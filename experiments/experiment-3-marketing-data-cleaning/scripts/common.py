"""Shared CSV contract for real Amazon review acquisition and cleaning."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["record_id", "asin", "product", "brand", "price", "rating", "review",
          "review_date", "unix_review_time", "helpful_votes", "total_votes",
          "source_review_line", "source_metadata_line"]
SEED = 20261110
SAMPLE_SIZE = 450
SOURCES = {
    "reviews_Musical_Instruments_5.json.gz": {
        "url": "https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Musical_Instruments_5.json.gz",
        "sha256": "03f9cc27ae13a454cb4ea6cb620fb10546cc1194ef921441d1c5f34addff2748"},
    "meta_Musical_Instruments.json.gz": {
        "url": "https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/meta_Musical_Instruments.json.gz",
        "sha256": "9ef838f5d971d3a7f52f0bbc1cc971082cddd8d6b1049ec3c4940e28293bfd85"},
}
def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def csv_bytes(rows: list[dict], fields: list[str] = FIELDS) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")

def read_csv(source) -> list[dict[str, str]]:
    if isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    else:
        data = source.read()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    missing = set(FIELDS) - set(reader.fieldnames or [])
    if missing:
        raise ValueError("缺少字段：" + ", ".join(sorted(missing)))
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV 存在重复列名")
    rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV 列数与表头不一致")
    return rows

def write_bytes(path: Path, data: bytes, immutable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite original evidence: {path}")
        return
    path.write_bytes(data)

def write_json(path: Path, data, immutable=False):
    write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2)+"\n").encode("utf-8"), immutable)
