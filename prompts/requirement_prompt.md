# 实验一需求 Prompt

请完成一个不调用大模型 API 的营销数据分析小工具。使用 Streamlit 提供页面，支持上传 `marketing_data.csv`，字段包括 `brand`、`product`、`price`、`rating`、`sales`，其中 `brand`、`price`、`rating` 为必需字段。程序需要检查必需字段，在字段缺失时给出明确错误提示；按品牌计算平均价格和平均评分，展示柱状图，支持按品牌筛选，并提供结果下载。

交付物包括：`app.py`、`README.md`、正常/缺少字段/空数据三类测试 CSV、Debug 日志、运行截图、`docs/experiment01.md` 和版本标签 `v0.1`。项目应能在 README 的启动命令下运行，实验结果保留在同一个仓库中，方便后续实验继续追加。
