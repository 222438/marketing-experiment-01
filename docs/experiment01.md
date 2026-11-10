# 实验一记录：Codex 协作开发与 Debug

## 目标

完成一个不调用大模型 API 的营销数据分析小工具，掌握需求拆解、项目目录、程序运行、错误定位、修复和验收的完整流程。

## 需求拆解

1. 使用 Streamlit 提供 CSV 上传页面。
2. 检查 `brand`、`price`、`rating` 字段，缺少字段时阻止分析并提示字段名；`product` 和 `sales` 为可选字段。
3. 清理空值和非法数字，提示被移除的行数。
4. 按品牌计算平均价格和平均评分，补充总销量与商品数。
5. 使用柱状图展示平均价格和平均评分，支持品牌筛选。
6. 提供 README、需求 Prompt、三类测试 CSV、Debug 日志、运行截图和 `v0.1` 标签。

## 目录设计

```text
marketing-experiments/
├── app.py
├── data/
├── docs/
├── logs/
├── prompts/
├── screenshots/
└── experiments/
```

根目录保留实验一的可运行入口。后续实验放在 `experiments/experiment-02-*` 等目录中，避免新实验覆盖已有成果。

## 测试与验收

| 测试文件 | 预期结果 | 结果 |
| --- | --- | --- |
| `data/test_normal.csv` | 正常加载并按品牌统计 | 通过 |
| `data/test_missing_fields.csv` | 明确提示缺少 `rating` | 通过 |
| `data/test_empty_values.csv` | 排除含必要字段空值的行并提示数量 | 通过 |
| `data/test_empty.csv` | 无数据行时提示没有可分析数据 | 通过 |

此外，单元测试覆盖品牌汇总、缺少字段、空数据和非法数字清理。
验证结果：`python -m unittest discover -s tests -v` 共 6 项测试通过。

## Debug 记录

第一次运行时需要确认空 CSV 的行为不能依赖 pandas 自动推断。修复后在 `clean_data` 中先统一转换数值字段，再删除无法参与统计的行；当所有行都被删除时，页面展示明确的错误提示并停止后续计算。

完整运行记录见 [`logs/debug.log`](../logs/debug.log)。

## 验收结论

- README 启动命令可运行；
- 正常数据可以查看指标、柱状图、统计表和下载结果；
- 缺少 `product`、`sales` 时仍可按三个必需字段完成分析；
- 缺少字段和空数据会给出明确提示；
- 筛选只影响汇总和下载结果，原始数据表仍显示全量记录；
- 实验一首个可运行版本标记为 `v0.1`。

页面集成检查通过：正常样例显示 4 项指标、2 张图表和 2 张数据表；上传缺少 `rating` 的 CSV 显示字段错误；上传空值样例保留 2 行并提示排除 3 行；筛选单一品牌后汇总表为 1 行，原始表仍为 9 行。浏览器页面无 JavaScript 异常。
