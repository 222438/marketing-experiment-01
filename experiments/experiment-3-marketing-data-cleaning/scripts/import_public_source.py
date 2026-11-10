"""Download real review archives, verify checksums, project public fields, sample."""
from __future__ import annotations
import argparse
import ast
import gzip
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from common import ROOT, FIELDS, SEED, SAMPLE_SIZE, SOURCES, csv_bytes, digest, write_bytes, write_json

REVIEW_FIELDS = ["asin", "reviewText", "overall", "reviewTime", "unixReviewTime", "helpful"]
META_FIELDS = ["asin", "title", "brand", "price"]

def acquire(cache: Path) -> dict[str, Path]:
    cache.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, spec in SOURCES.items():
        path = cache / name
        if not path.exists():
            request = Request(spec["url"], headers={"User-Agent": "MarketingLab-Experiment3/0.3"})
            with urlopen(request, timeout=90) as response:
                data = response.read()
            if digest(data) != spec["sha256"]:
                raise ValueError(f"Source checksum changed: {name}")
            write_bytes(path, data, immutable=True)
        if digest(path.read_bytes()) != spec["sha256"]:
            raise ValueError(f"Cached archive checksum mismatch: {name}")
        paths[name] = path
    return paths

def collect(cache: Path, preview=False):
    paths = acquire(cache)
    with gzip.open(paths["reviews_Musical_Instruments_5.json.gz"], "rt", encoding="utf-8") as handle:
        reviews = [(i, json.loads(line)) for i, line in enumerate(handle, 1)]
    # Sample before any quality filtering. The seed controls selection, not data generation.
    selected = sorted(random.Random(SEED).sample(reviews, SAMPLE_SIZE))
    if preview:
        selected = selected[:50]
    products = {row["asin"] for _, row in selected}
    metadata = {}
    meta_count = 0
    with gzip.open(paths["meta_Musical_Instruments.json.gz"], "rt", encoding="utf-8") as handle:
        for i, line in enumerate(handle, 1):
            meta_count = i
            item = ast.literal_eval(line)  # Upstream metadata uses Python-literal JSON.
            if item["asin"] in products:
                if item["asin"] in metadata:
                    raise ValueError("Ambiguous product metadata: " + item["asin"])
                metadata[item["asin"]] = (i, item)
    rows, review_snapshot, meta_snapshot = [], [], []
    for number, review in selected:
        meta_line, meta = metadata.get(review["asin"], ("", {}))
        helpful = review.get("helpful", ["", ""])
        row = {
            "record_id": f"MI-{number:05d}", "asin": review["asin"],
            "product": meta.get("title", ""), "brand": meta.get("brand", ""),
            "price": meta.get("price", ""), "rating": review.get("overall", ""),
            "review": review.get("reviewText", ""), "review_date": review.get("reviewTime", ""),
            "unix_review_time": review.get("unixReviewTime", ""),
            "helpful_votes": helpful[0], "total_votes": helpful[1],
            "source_review_line": number, "source_metadata_line": meta_line,
        }
        rows.append(row)
        # Exclude reviewerID and reviewerName BEFORE creating any public artifact.
        review_snapshot.append({"source_line": number, **{k: review.get(k, "") for k in REVIEW_FIELDS}})
    for asin, (number, meta) in sorted(metadata.items()):
        meta_snapshot.append({"source_line": number, **{k: meta.get(k, "") for k in META_FIELDS}})
    if preview:
        write_bytes(ROOT / "docs/sample_50.csv", csv_bytes(rows), immutable=True)
        write_json(ROOT / "reports/preview_50.json", {
            "rows": len(rows), "fields": len(FIELDS), "seed": SEED,
            "missing": {f: sum(r[f] == "" for r in rows) for f in FIELDS},
            "sample_rule": "First 50 in sorted 450-row sample; before cleaning"
        })
        print("PREVIEW: 50 actual source records inspected; docs/sample_50.csv")
        return
    raw = csv_bytes(rows)
    write_bytes(ROOT / "data/raw/raw_data.csv", raw, immutable=True)
    for name, snapshot in [("reviews", review_snapshot), ("metadata", meta_snapshot)]:
        content = "".join(json.dumps(r, ensure_ascii=False)+"\n" for r in snapshot).encode("utf-8")
        write_bytes(ROOT / f"data/source/{name}_projection.jsonl", content, immutable=True)
    manifest = {
        "dataset": "Amazon product data 2014 / Musical Instruments 5-core",
        "description_url": "https://snap.stanford.edu/data/amazon/productGraph/",
        "source_files": SOURCES, "review_population": len(reviews),
        "metadata_population": meta_count, "sample_size": len(rows),
        "seed": SEED, "selection": "random.sample of all review rows, sorted by original line; no quality prefilter",
        "matched_products": len(metadata), "sampled_products": len(products),
        "raw_sha256": digest(raw),
        "privacy_projection": "Excluded reviewerID, reviewerName and all unused metadata fields; review text unchanged.",
        "price_meaning": "USD at metadata crawl time; not transaction price or today's price",
    }
    write_json(ROOT / "docs/source_manifest.json", manifest, immutable=True)
    event = ROOT / "docs/acquisition_record.json"
    if not event.exists():
        write_json(event, {"acquired_at_utc": datetime.now(timezone.utc).isoformat(),
                          "sample_size": len(rows), "source_files_verified": list(SOURCES)}, immutable=True)
    print(f"ACQUIRED: {len(reviews)} source reviews -> {len(rows)} sampled; {len(metadata)} products; SHA256 {digest(raw)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    collect(args.cache, args.preview)

