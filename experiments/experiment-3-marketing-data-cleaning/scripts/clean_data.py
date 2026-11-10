"""Deterministic cleaning of real review data. Never generates or imputes values."""
from __future__ import annotations
import argparse
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from common import ROOT, FIELDS, csv_bytes, digest, read_csv, write_bytes, write_json

BRAND_ALIASES = {"Audio Technica": "Audio-Technica"}
UNKNOWN = {"", "unknown", "n/a", "null", "none"}
REQUIRED = ["record_id", "asin", "product", "brand", "price", "rating", "review", "review_date"]
NUMERIC = ["price", "rating", "unix_review_time", "helpful_votes", "total_votes",
           "source_review_line", "source_metadata_line"]

def number(value, integer=False, minimum=0, maximum=None):
    text = str(value).strip()
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        raise ValueError("not_numeric")
    if not parsed.is_finite() or parsed < minimum or (maximum is not None and parsed > maximum):
        raise ValueError("out_of_range")
    if integer and parsed != parsed.to_integral_value():
        raise ValueError("not_integer")
    return parsed

def normalize(row: dict[str, str]) -> tuple[dict[str, str], list[dict]]:
    clean = {f: row.get(f, "") for f in FIELDS}
    for f in ["record_id", "asin", "brand", "product"]:
        clean[f] = clean[f].strip()
    # Decode HTML entities in catalog labels only. Review evidence stays byte-for-byte as text.
    for f in ["brand", "product"]:
        clean[f] = html.unescape(clean[f])
    clean["brand"] = BRAND_ALIASES.get(clean["brand"], clean["brand"])
    if any(clean[f].strip().casefold() in UNKNOWN for f in REQUIRED):
        raise ValueError("missing_required:" + ",".join(f for f in REQUIRED if clean[f].strip().casefold() in UNKNOWN))
    if not re.fullmatch(r"[A-Z0-9]{10}", clean["asin"]):
        raise ValueError("invalid_asin")
    price = number(clean["price"], minimum=Decimal("0.01"))
    # No arbitrary price ceiling and no clipping. Two decimals must preserve value exactly.
    if price.quantize(Decimal(".01")) != price:
        raise ValueError("price_excess_precision")
    clean["price"] = format(price, ".2f")
    clean["rating"] = str(int(number(clean["rating"], integer=True, minimum=1, maximum=5)))
    date_text = clean["review_date"].strip()
    parsed = None
    for fmt in ("%m %d, %Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(date_text, fmt).date()
            break
        except ValueError:
            pass
    if parsed is None or not (datetime(1996, 1, 1).date() <= parsed <= datetime(2014, 7, 31).date()):
        raise ValueError("invalid_review_date")
    for f in NUMERIC[2:]:
        clean[f] = str(int(number(clean[f], integer=True, minimum=1 if "line" in f else 0)))
    timestamp_date = datetime.fromtimestamp(int(clean["unix_review_time"]), timezone.utc).date()
    if timestamp_date != parsed:
        raise ValueError("date_timestamp_conflict")
    clean["review_date"] = parsed.isoformat()
    if int(clean["helpful_votes"]) > int(clean["total_votes"]):
        raise ValueError("helpful_exceeds_total")
    changes = [{"field": f, "before": row.get(f, ""), "after": clean[f]}
               for f in FIELDS if clean[f] != row.get(f, "")]
    return clean, changes

def clean_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    output, log = [], []
    ids, fingerprints = set(), set()
    for index, row in enumerate(rows, 1):
        action, reason, changes = "keep", "", []
        try:
            clean, changes = normalize(row)
            fingerprint = (clean["asin"], clean["unix_review_time"], clean["review"],
                           clean["rating"], clean["helpful_votes"], clean["total_votes"])
            if clean["record_id"] in ids:
                raise ValueError("duplicate_record_id")
            if fingerprint in fingerprints:
                raise ValueError("duplicate_review")
            ids.add(clean["record_id"])
            fingerprints.add(fingerprint)
            output.append(clean)
        except (ValueError, OverflowError, OSError) as exc:
            action, reason = "drop", str(exc)
        log.append({"sample_row": index, "record_id": row.get("record_id", ""),
                    "source_review_line": row.get("source_review_line", ""),
                    "action": action, "reason": reason,
                    "changes": json.dumps(changes, ensure_ascii=False, separators=(",", ":"))})
    return output, log

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/raw_data.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/clean_data.csv")
    parser.add_argument("--artifact-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("Refusing to overwrite raw input")
    original_hash = digest(args.input.read_bytes())
    rows = read_csv(args.input)
    clean, log = clean_rows(rows)
    if not clean:
        raise SystemExit("No valid rows remain; inspect input instead of creating invented rows.")
    write_bytes(args.output, csv_bytes(clean))
    write_bytes(args.artifact_dir / "docs/cleaning_log.csv", csv_bytes(log, list(log[0])))
    stats = []
    for stage, data in [("raw", rows), ("clean", clean)]:
        for field in FIELDS:
            known = sum(str(r[field]).strip().casefold() not in UNKNOWN for r in data)
            stats.append({"stage": stage, "field": field, "row_count": len(data),
                          "known_count": known, "missing_count": len(data)-known,
                          "completeness_pct": round(known/len(data)*100, 4)})
    write_bytes(args.artifact_dir / "reports/quality_stats.csv", csv_bytes(stats, list(stats[0])))
    drop_reasons = Counter(r["reason"] for r in log if r["action"] == "drop")
    modifications = Counter(c["field"] for r in log for c in json.loads(r["changes"]) if r["action"] == "keep")
    summary = {"raw_rows": len(rows), "clean_rows": len(clean), "dropped_rows": len(rows)-len(clean),
               "retention_pct": round(len(clean)/len(rows)*100, 4),
               "drop_reasons": dict(drop_reasons), "field_changes": dict(modifications),
               "raw_sha256": original_hash, "clean_sha256": digest(args.output.read_bytes()),
               "all_clean_fields_at_least_90pct": all(s["completeness_pct"] >= 90 for s in stats if s["stage"] == "clean")}
    write_json(args.artifact_dir / "reports/quality_summary.json", summary)
    if digest(args.input.read_bytes()) != original_hash:
        raise RuntimeError("Raw input unexpectedly changed")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
