"""Independent evidence checks and deterministic replay for validate-data skill."""
from __future__ import annotations
import argparse
import ast
import gzip
import html
import json
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from common import ROOT, FIELDS, SEED, SOURCES, csv_bytes, digest, read_csv, write_bytes, write_json

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def validate(cache=None):
    raw_path=ROOT/"data/raw/raw_data.csv"
    original=raw_path.read_bytes()
    raw=read_csv(raw_path)
    clean=read_csv(ROOT/"data/processed/clean_data.csv")
    manifest=json.loads((ROOT/"docs/source_manifest.json").read_text(encoding="utf8"))
    require(len(raw)==450 and 300<=len(clean)<=500, "sample size")
    require(digest(original)==manifest["raw_sha256"],"raw checksum")
    require(len({r["record_id"] for r in raw})==len(raw),"raw unique record IDs")
    raw_by_id={r["record_id"]:r for r in raw}
    source_reviews=[json.loads(s) for s in (ROOT/"data/source/reviews_projection.jsonl").read_text(encoding="utf8").splitlines()]
    source_metadata=[json.loads(s) for s in (ROOT/"data/source/metadata_projection.jsonl").read_text(encoding="utf8").splitlines()]
    rev={r["source_line"]:r for r in source_reviews}
    meta={r["source_line"]:r for r in source_metadata}
    private_fields={"reviewerID","reviewerName","email","phone","address"}
    require(all(not (private_fields & set(r)) for r in source_reviews+source_metadata),"private source columns excluded")
    for row in raw:
        review=rev[int(row["source_review_line"])]
        product=meta[int(row["source_metadata_line"])]
        require(row["asin"]==review["asin"]==product["asin"],"join keys match")
        for field,key in [("product","title"),("brand","brand"),("price","price")]:
            require(row[field]==str(product.get(key,"")),"raw metadata value changed")
        for field,key in [("review","reviewText"),("rating","overall"),("review_date","reviewTime"),("unix_review_time","unixReviewTime")]:
            require(row[field]==str(review[key]),"raw review value changed")
        require(row["helpful_votes"]==str(review["helpful"][0]) and row["total_votes"]==str(review["helpful"][1]),"votes changed")
        require(row["record_id"]==f"MI-{int(row['source_review_line']):05d}","derived ID trace")
    expected_lines=sorted(random.Random(SEED).sample(range(1,manifest["review_population"]+1),450))
    require([int(r["source_review_line"]) for r in raw]==expected_lines,"unfiltered deterministic sampling")
    require(read_csv(ROOT/"docs/sample_50.csv")==raw[:50],"50-row preview matches raw")
    require(len({r["record_id"] for r in clean})==len(clean),"clean unique IDs")
    for row in clean:
        before=raw_by_id[row["record_id"]]
        require(row["review"]==before["review"],"review evidence unchanged")
        require(row["asin"]==before["asin"],"product identity unchanged")
        require(Decimal(row["price"])==Decimal(before["price"])>0,"price not imputed")
        require(Decimal(row["rating"])==Decimal(before["rating"]) and 1<=int(row["rating"])<=5,"rating not imputed")
        require(row["review_date"]==datetime.fromtimestamp(int(before["unix_review_time"]),timezone.utc).date().isoformat(),"date matches source UTC")
        expected_brand=html.unescape(before["brand"].strip())
        if expected_brand=="Audio Technica":
            expected_brand="Audio-Technica"
        require(row["brand"]==expected_brand,"brand only documented normalization")
        require(row["product"]==html.unescape(before["product"].strip()),"title only decoded")
        require(0<=int(row["helpful_votes"])<=int(row["total_votes"]),"vote consistency")
        for f in ["source_review_line","source_metadata_line","unix_review_time","helpful_votes","total_votes"]:
            require(row[f]==str(int(Decimal(before[f]))),"numeric source trace")
    # Calculate completeness independently from report producer.
    import csv
    stats=list(csv.DictReader((ROOT/"reports/quality_stats.csv").open(encoding="utf-8-sig",newline="")))
    for s in stats:
        rows=raw if s["stage"]=="raw" else clean
        known=sum(r[s["field"]].strip().casefold() not in {"","unknown","n/a","null","none"} for r in rows)
        require(int(s["row_count"])==len(rows) and int(s["known_count"])==known,"reported denominator/count mismatch")
        require(abs(float(s["completeness_pct"])-known/len(rows)*100)<.0001,"completeness rate mismatch")
        if s["stage"]=="clean":
            require(known/len(rows)>=.9,"clean completeness below 90%")
    logs=list(csv.DictReader((ROOT/"docs/cleaning_log.csv").open(encoding="utf-8-sig",newline="")))
    require(len(logs)==len(raw),"one log decision per raw row")
    require({r["record_id"] for r in logs if r["action"]=="keep"}=={r["record_id"] for r in clean},"log/clean alignment")
    # Full upstream check is optional for CI; it was run with the downloaded original archives.
    upstream_verified=False
    if cache is not None:
        for name,spec in SOURCES.items():
            require(digest((cache/name).read_bytes())==spec["sha256"],"archive hash mismatch")
        for name, projected, keys, parse in [
            ("reviews_Musical_Instruments_5.json.gz",rev,["asin","reviewText","overall","reviewTime","unixReviewTime","helpful"],json.loads),
            ("meta_Musical_Instruments.json.gz",meta,["asin","title","brand","price"],ast.literal_eval)]:
            with gzip.open(cache/name,"rt",encoding="utf8") as handle:
                for i,line in enumerate(handle,1):
                    if i in projected:
                        actual=parse(line)
                        require(all(projected[i][k]==actual.get(k,"") for k in keys),"projection differs from original archive")
        upstream_verified=True
    with tempfile.TemporaryDirectory() as temp:
        outputs=[]
        for run in [1,2]:
            dest=Path(temp)/str(run)
            command=[sys.executable,str(ROOT/"scripts/clean_data.py"),"--input",str(raw_path),
                     "--output",str(dest/"clean_data.csv"),"--artifact-dir",str(dest)]
            subprocess.run(command,check=True,capture_output=True)
            outputs.append({name:(dest/name).read_bytes() for name in ["clean_data.csv","docs/cleaning_log.csv","reports/quality_stats.csv","reports/quality_summary.json"]})
        require(outputs[0]==outputs[1],"two clean runs differ")
        require(outputs[0]["clean_data.csv"]==(ROOT/"data/processed/clean_data.csv").read_bytes(),"checked-in clean data stale")
    require(original==raw_path.read_bytes(),"raw modified")
    # Email and common phone patterns. Calendar dates are not phone numbers.
    pii=re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)(?:\+1[ -]?)?\(?\d{3}\)?[ -]\d{3}[ -]\d{4}(?!\d)")
    flagged=[r["record_id"] for r in raw if pii.search(r["review"])]
    require(not flagged,"contact-like text requires manual privacy review: "+str(flagged))
    checks={"sample_rows":len(raw),"clean_rows":len(clean),"source_projection_matches":True,
            "original_archives_verified_this_run":upstream_verified,
            "raw_hash":digest(original),"raw_unchanged":True,"repeat_runs_identical":True,
            "all_fields_completeness_at_least_90pct":True,"contact_pattern_flags":flagged}
    write_json(ROOT/"reports/verification.json",checks)
    clean_by_id={r["record_id"]:r for r in clean}
    log_by_id={r["record_id"]:r for r in logs}
    audit=[]
    for row in sorted(random.Random(SEED+1).sample(raw,10),key=lambda r:r["record_id"]):
        rid=row["record_id"]; after=clean_by_id.get(rid)
        audit.append({"record_id":rid,"source_review_line":row["source_review_line"],
                      "action":log_by_id[rid]["action"],"reason":log_by_id[rid]["reason"],
                      "raw_brand":row["brand"],"clean_brand":after["brand"] if after else "",
                      "raw_price":row["price"],"clean_price":after["price"] if after else "",
                      "raw_date":row["review_date"],"clean_date":after["review_date"] if after else "",
                      "review_unchanged": str(after is None or after["review"]==row["review"]),
                      "source_projection_match":"True"})
    write_bytes(ROOT/"docs/sample_10_audit.csv",csv_bytes(audit,list(audit[0])))
    print(json.dumps(checks,ensure_ascii=False,indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path)
    args=parser.parse_args()
    validate(args.cache)
