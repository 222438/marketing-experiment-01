# 实验三：真实营销数据获取与清洗 · v0.3

数据来自 [Julian McAuley 发布、Stanford 托管的 Amazon product data](https://snap.stanford.edu/data/amazon/productGraph/)，类别为 Musical Instruments。下载真实评论及商品元数据后，先抽样检查 50 条，再保留固定抽样的 450 条原始记录。清洗后得到 385 条评论、271 个商品、101 个品牌。没有生成评论或补造品牌、价格、评分、日期和互动数字。

调用的现成 Skill 是 Anthropic 官方仓库的 **explore-data** 与 **validate-data**，原文件保持不变，见 [来源及执行记录](docs/skill_usage.md)。本实验没有自行编写 Skill。

## 运行

在仓库根目录，安装实验一已有依赖并启动：

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

在左侧选择 **营销数据清洗**。上传本实验的 `data/raw/raw_data.csv`，查看清洗结果、原始数据和逐行日志，下载清洗 CSV。未上传时显示同一真实数据样本。页面中的品牌筛选不会改动原始文件。

仅清洗和校验只需要 Python 3.11+ 标准库，在仓库根目录执行：

```powershell
python experiments/experiment-3-marketing-data-cleaning/scripts/clean_data.py
python experiments/experiment-3-marketing-data-cleaning/scripts/profile_data.py
python experiments/experiment-3-marketing-data-cleaning/scripts/validate_data.py
python -m unittest discover -s experiments/experiment-3-marketing-data-cleaning/tests -v
```

重新从公开源下载并验证（约 33 MB；文件会保存在被 Git 忽略的 .cache）：

```powershell
python experiments/experiment-3-marketing-data-cleaning/scripts/import_public_source.py --preview
python experiments/experiment-3-marketing-data-cleaning/scripts/import_public_source.py
python experiments/experiment-3-marketing-data-cleaning/scripts/validate_data.py --cache experiments/experiment-3-marketing-data-cleaning/.cache
```

固定抽样种子只控制选择哪些真实记录，不生成数据。来源内容有变化或本地原始文件内容不一致时，脚本报错，拒绝覆盖。断网时仍可用已提交的原始 CSV 重跑清洗及验证。

## 结果与边界

- 原始 450 条，清洗后 385 条；排除 64 条品牌缺失/Unknown、1 条评论为空的记录。
- 原始品牌完整率 85.78%；清洗后全部 13 个字段完整率为 100%。这是对完整记录的筛选，保留率为 85.56%，不能说原始数据本来就完整。
- 日期范围为 2004-09-29 至 2014-07-20。价格是历史商品元数据采集时的 **USD** 价格，并非当前售价或消费者成交价。
- 一行代表一条评论。有用票数不是销量；0 票不等于差评。不同评论可能指向同一商品，比较商品价格时应先按 ASIN 去重。
- 移除上游 reviewerID/reviewerName 列后才创建公开样本；不上传包含这些列的完整压缩包。保留的评论原文未改写，完整来源可用 URL、SHA-256 和原始行号追溯。
- 数据为公开研究历史样本，不代表当前市场或全部消费者。没有虚构重复、异常值来制造清洗效果。

## 交付物索引

| 要求 | 文件 |
|---|---|
| 原始数据 | [data/raw/raw_data.csv](data/raw/raw_data.csv) |
| 清洗数据 | [data/processed/clean_data.csv](data/processed/clean_data.csv) |
| 来源公共字段快照 | data/source/*_projection.jsonl |
| 采集与清洗脚本 | scripts/import_public_source.py、scripts/clean_data.py |
| 数据字典 | [docs/data_dictionary.md](docs/data_dictionary.md) |
| 来源与日期、哈希 | [docs/source_record.md](docs/source_record.md)、source_manifest.json、acquisition_record.json |
| 50 条预检、10 条抽查 | docs/sample_50.csv、docs/sample_10_audit.csv、[docs/sample_review.md](docs/sample_review.md) |
| 伦理检查 | [docs/ethics_checklist.md](docs/ethics_checklist.md) |
| 清洗规则与逐行日志 | [docs/cleaning_rules.md](docs/cleaning_rules.md)、docs/cleaning_log.csv |
| 质量统计与画像 | reports/quality_stats.csv、quality_summary.json、[data_profile.md](reports/data_profile.md)、data_profile.json |
| Skill 来源、校验报告 | docs/skill_usage.md、[reports/validation_report.md](reports/validation_report.md) |
| 证据校验与测试 | reports/verification.json、reports/test_results.txt、tests/test_pipeline.py |
| 页面截图 | [screenshots/experiment03.png](screenshots/experiment03.png) |

GitHub 版本标签：`v0.3`。前序实验保留 `v0.1`、`v0.2`。
