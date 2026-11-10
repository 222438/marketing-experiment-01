"""Validate the experiment 2 skill output without third-party dependencies."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "reviews.csv"
EXPECTED_PATH = ROOT / "data" / "test_cases.json"
OUTPUT_PATH = ROOT / "outputs" / "encoded_reviews.json"

ENUMS = {
    "sentiment": {"positive", "negative", "mixed", "neutral", "unknown"},
    "need": {"quality", "value", "convenience", "service", "information", "fit", "durability", "safety", "none", "unknown"},
    "pain_point": {"price", "quality", "taste", "delivery", "packaging", "service", "usability", "fit", "availability", "none", "unknown"},
    "scenario": {"home", "commute", "work", "travel", "gift", "outdoor", "exercise", "family", "unknown"},
    "purchase_barrier": {"price", "trust", "quality", "availability", "delivery", "fit", "complexity", "none", "unknown"},
    "confidence": {"high", "medium", "low"},
}
REQUIRED_FIELDS = {"review_id", "sentiment", "need", "pain_point", "scenario", "purchase_barrier", "evidence", "confidence"}


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with EXPECTED_PATH.open(encoding="utf-8") as handle:
        expected = json.load(handle)
    with OUTPUT_PATH.open(encoding="utf-8") as handle:
        output = json.load(handle)

    if len(rows) != 10 or len(expected) != 10 or len(output) != 10:
        fail("CSV、预期试样和输出都必须各有 10 条记录")
    source = {row["review_id"]: row for row in rows}
    actual_ids = [item.get("review_id") for item in output]
    if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != set(source):
        fail("输入与输出的 review_id 必须一一对应且唯一")

    for item in output:
        if set(item) != REQUIRED_FIELDS:
            fail(f"{item.get('review_id')}: 输出字段不完整或包含额外字段")
        review = source[item["review_id"]]["review"]
        for field, allowed in ENUMS.items():
            value = item[field]
            if field in {"sentiment", "confidence"}:
                if value not in allowed:
                    fail(f"{item['review_id']}: {field} 非法值 {value!r}")
            else:
                if not isinstance(value, list) or not value or len(set(value)) != len(value) or not set(value) <= allowed:
                    fail(f"{item['review_id']}: {field} 必须是唯一且属于字典的非空数组")
        if not isinstance(item["evidence"], list):
            fail(f"{item['review_id']}: evidence 必须为数组")
        for evidence in item["evidence"]:
            if set(evidence) != {"field", "quote"} or evidence["field"] not in {"sentiment", "need", "pain_point", "scenario", "purchase_barrier"}:
                fail(f"{item['review_id']}: evidence 结构非法")
            if not evidence["quote"] or evidence["quote"] not in review:
                fail(f"{item['review_id']}: evidence.quote 不在原评论中")
        if not review and item["evidence"]:
            fail(f"{item['review_id']}: 空评论不能有证据")

    if output != expected:
        fail("输出与 10 条试样的预期编码不一致")
    print(f"PASS: {len(output)} 条评论通过字段、枚举、ID、证据子串和盲测一致性校验")
    print("PASS: 空评论 R009 使用 unknown/[]/low，没有伪造证据")
    print("PASS: 输出可通过 review_id 回到 reviews.csv 原文")


if __name__ == "__main__":
    main()
