# Marketing Experiments

营销数据分析系列实验仓库。实验一完成一个不调用大模型 API 的 CSV 分析工具；后续实验放入 `experiments/` 目录，并沿用同一 GitHub 仓库的版本记录。

## 实验一：营销数据分析工具

上传 CSV 后，程序会：

- 检查必需字段 `brand`、`price`、`rating`；
- 清理空值和非数字数据，并给出可读的提示；
- 按品牌计算平均价格和平均评分；若提供 `sales`、`product`，同时展示总销量和商品数；
- 绘制平均价格和平均评分柱状图；
- 支持品牌筛选、结果表格查看和筛选结果下载。

## 启动

需要 Python 3.11 或更高版本。依赖版本固定为已验证的 pandas 3.0.2 和 Streamlit 1.56.0。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

打开终端显示的本地地址，在侧边栏上传 `data/marketing_data.csv` 或自己的 CSV。分析需要 `brand`、`price`、`rating` 三个字段；`product` 和 `sales` 会保留在原始表格中，并在提供时计算扩展指标。未上传文件时，页面会自动展示内置示例数据。

## 项目结构

```text
.
├── app.py
├── data/                      # 演示数据和三类验收 CSV
├── docs/experiment01.md       # 实验记录、验收结果和 Debug 过程
├── logs/debug.log             # 运行与排错记录
├── prompts/requirement_prompt.md
├── screenshots/               # 运行截图
└── experiments/               # 后续实验
```

后续实验从 `experiments/README.md` 约定的结构开始，并在此 README 增加运行方式和实验入口。

## 验收

```powershell
python -m unittest discover -s tests -v
```

版本 `v0.1` 对应实验一的首个可运行版本。

## 实验二：Consumer Insight Skill

实验二把消费者评论分析整理为可复用 Skill。输入 `experiments/experiment-2-consumer-insight/data/reviews.csv`，按
`experiments/experiment-2-consumer-insight/skills/consumer-insight-skill/SKILL.md` 的边界规则输出结构化 JSON；
Schema、标签字典、10 条试样、盲测记录和失败案例均保存在同一目录中。

验证命令：

```powershell
python experiments/experiment-2-consumer-insight/scripts/validate_skill.py
```

版本 `v0.2` 对应实验二的可复用 Skill 版本。

## 实验三：营销数据获取与清洗

实验三使用 Stanford/UCSD 公开发布的真实 Amazon 乐器类历史评论，固定抽取 450 条，清洗后保留 385 条。原始文件保留；没有补造品牌、价格、评分、评论或日期。调用 Anthropic 官方现成 `explore-data` 和 `validate-data` Skill，原文件保存在实验目录中。

[实验三入口与交付物](experiments/experiment-3-marketing-data-cleaning/README.md) · [实验记录](docs/experiment03.md)

启动 `python -m streamlit run app.py` 后，在左侧选择 **营销数据清洗**，上传实验三 `raw_data.csv`，查看处理记录并下载清洗结果。价格为历史 USD 元数据价格，评论日期截至 2014 年。

验证命令：

```powershell
python experiments/experiment-3-marketing-data-cleaning/scripts/clean_data.py
python experiments/experiment-3-marketing-data-cleaning/scripts/profile_data.py
python experiments/experiment-3-marketing-data-cleaning/scripts/validate_data.py
python -m unittest discover -s experiments/experiment-3-marketing-data-cleaning/tests -v
```

版本 `v0.3` 对应实验三的数据获取与清洗版本。
