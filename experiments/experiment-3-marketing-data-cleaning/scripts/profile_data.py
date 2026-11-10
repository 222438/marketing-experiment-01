"""Execute explore-data's file profiling checks, retaining explicit denominators."""
from __future__ import annotations
from collections import Counter
from datetime import datetime
import json
import statistics
from common import ROOT, FIELDS, read_csv, write_json, write_bytes
from clean_data import UNKNOWN, NUMERIC

def percentile(values, p):
    values = sorted(values)
    position = (len(values)-1)*p
    low = int(position)
    return values[low] + (values[min(low+1,len(values)-1)]-values[low])*(position-low)

def profile(rows):
    report = {"rows": len(rows), "columns": len(FIELDS), "grain": "one source review joined many-to-one with its product metadata", "fields": {}}
    for f in FIELDS:
        known = [r[f] for r in rows if r[f].strip().casefold() not in UNKNOWN]
        counts = Counter(known)
        stat = {"missing":len(rows)-len(known), "known_pct":round(len(known)/len(rows)*100,4),
                "distinct":len(counts), "cardinality_ratio":round(len(counts)/len(rows),6),
                "whitespace_rows":sum(r[f] != r[f].strip() for r in rows)}
        # Avoid repeating long review text throughout the QA report.
        if f != "review":
            stat["top_values"] = counts.most_common(5)
            stat["least_common"] = sorted(counts.items(), key=lambda x:(x[1],x[0]))[:5]
        if f in NUMERIC:
            values = [float(v) for v in known]
            if values:
                stat.update({"min":min(values),"max":max(values),"mean":statistics.mean(values),
                             "median":statistics.median(values),"stddev":statistics.pstdev(values),
                             "zero":values.count(0),"negative":sum(v<0 for v in values),
                             "percentiles":{str(p):percentile(values,p/100) for p in [1,5,25,75,95,99]}})
        elif known:
            stat["length"] = {"min":min(map(len,known)), "max":max(map(len,known)), "mean":statistics.mean(map(len,known))}
        report["fields"][f] = stat
    dates=[]
    for row in rows:
        for fmt in ("%m %d, %Y","%Y-%m-%d"):
            try:
                dates.append(datetime.strptime(row["review_date"],fmt).date().isoformat())
                break
            except ValueError:
                pass
    report["dates"]={"min":min(dates),"max":max(dates),"by_month":dict(sorted(Counter(d[:7] for d in dates).items()))}
    report["unique_record_ids"] = len({r["record_id"] for r in rows})
    report["unique_products"] = len({r["asin"] for r in rows})
    report["unique_brands"] = len({r["brand"] for r in rows if r["brand"].casefold() not in UNKNOWN})
    return report

def main():
    profiles = {stage: profile(read_csv(ROOT / f"data/{folder}/{name}.csv"))
                for stage,folder,name in [("raw","raw","raw_data"),("clean","processed","clean_data")]}
    write_json(ROOT / "reports/data_profile.json",profiles)
    summary=json.loads((ROOT/"reports/quality_summary.json").read_text(encoding="utf8"))
    lines=["# 数据画像（调用 explore-data）","",
           "一行是一条历史评论；商品价格会随同一个 ASIN 重复，不能把评论行数当成销量，也不能把评论加权均价称为商品均价。","",
           "| 阶段 | 行数 | 商品数 | 已知品牌数 | 日期范围 |","|---|---:|---:|---:|---|"]
    for stage,p in profiles.items():
        lines.append(f"| {stage} | {p['rows']} | {p['unique_products']} | {p['unique_brands']} | {p['dates']['min']} — {p['dates']['max']} |")
    lines+=["","| 字段 | 原始完整率 | 清洗后完整率 | 清洗后不同值数 |","|---|---:|---:|---:|"]
    for f in FIELDS:
        a,b=profiles["raw"]["fields"][f],profiles["clean"]["fields"][f]
        lines.append(f"| {f} | {a['known_pct']:.2f}% | {b['known_pct']:.2f}% | {b['distinct']} |")
    lines+=["","## 质量发现","",
            f"- 删除 {summary['dropped_rows']} 行；原因及数量：{summary['drop_reasons']}。",
            "- 空品牌和 Unknown 视为不可用；不从商品标题猜品牌。所有原始行仍保留。",
            "- 通过删除无品牌行获得完整率，带来完整记录选择偏差，不能声称样本代表所有消费者。",
            "- 不人为加入重复、负价格或日期错误。未发现某类错误时，其处理数量记录为 0。",
            "- 各字段的数值分位数、极值、文本长度、频数、时间分布见 data_profile.json。价格只验证有限正数，不因高价而随意删行。",
            "","## 后续分析建议","",
            "1. 按品牌比较评分，始终同时给出评论数及商品数。",
            "2. 按 ASIN 去重商品价格后比较价格分布，避免热门商品评论多导致权重偏差。",
            "3. 分析有用票比例时分母使用 total_votes；0 票记录不计算比例。",
            "4. 比较删行前后的评分分布，检查品牌缺失是否关联评分。",
            "5. 若研究当下市场，先采集新的数据；本批数据截至 2014 年。"]
    write_bytes(ROOT / "reports/data_profile.md",("\n".join(lines)+"\n").encode("utf8"))
    print("PROFILE: raw and clean fields, distributions and date ranges recorded")

if __name__ == "__main__":
    main()
