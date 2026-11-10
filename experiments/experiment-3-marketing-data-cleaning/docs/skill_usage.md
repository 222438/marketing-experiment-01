# 已有 Skill 来源与实际执行记录

本实验直接下载并读取 Anthropic 官方仓库中的现成 Skill，没有编写新的 SKILL.md，也没有使用本机旧项目的模拟数据或自建 Skill。

- 上游仓库：[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
- 查询日期：2026-11-10；查询时仓库 Stars：35,295。Stars 是仓库关注量，不是该 Skill 的质量评分。
- 固定提交：`e605d8ddbfb688da57dfaaceebd93f12a64ef1d3`
- [explore-data 原文件](https://github.com/anthropics/knowledge-work-plugins/blob/e605d8ddbfb688da57dfaaceebd93f12a64ef1d3/data/skills/explore-data/SKILL.md)
- [validate-data 原文件](https://github.com/anthropics/knowledge-work-plugins/blob/e605d8ddbfb688da57dfaaceebd93f12a64ef1d3/data/skills/validate-data/SKILL.md)
- 仓库内原样副本：vendor/anthropic-data/skills/，另保留 data/LICENSE 和 CONNECTORS.md。
- 文件哈希及逐字节核验见 upstream_manifest.json。

## 调用方式

这是指令型 Skill，不是一个 Python 包。Codex 读取上游 SKILL.md 后，按照其中的文件输入工作流执行脚本和复核任务；没有调用不存在的“Skill API”，也没有宣称运行了 Slash 命令服务。无需数据仓库连接器，使用上游明确支持的 CSV 文件分支。

| 现成 Skill 步骤 | 本次执行 | 产物 |
|---|---|---|
| explore-data：读取数据，确认粒度/主键 | 获取官方数据、按源行号抽样、ASIN 多对一连接 | source_manifest.json、raw_data.csv |
| explore-data：全列空值、基数、分布 | 对 raw/clean 两个阶段执行 profile_data.py | reports/data_profile.json/md |
| explore-data：数值、字符串、日期异常 | 价格/评分/票数统计、文本长度/实体、日期范围及月份分布 | data_profile.json、cleaning_log.csv |
| explore-data：数据关系与后续方向 | 区分评论粒度/商品粒度；有用票分母明确；提出后续分析 | reports/data_profile.md |
| validate-data：方法与偏差 | 记录历史时间、完整记录筛选、商品重复权重问题 | validation_report.md |
| validate-data：独立复算 | 重新计算完整率、核对压缩包源值、10 条样本对照 | verification.json、sample_10_audit.csv |
| validate-data：重复与回归 | 两次临时目录清洗字节一致、13 项单元/页面测试、实际浏览器上传下载 | test_results.txt、browser_check.json |
| validate-data：结论等级 | Share with noted caveats：适合课堂流程验收，须注明历史数据和选择偏差 | reports/validation_report.md |

原样 Skill 指导工作流程；为当前数据编写的导入/清洗/校验 Python 是实验实现代码，不是另写 Skill。
