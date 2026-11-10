# 实验二：Consumer Insight Skill

本实验将“消费者评论分析”整理成一个可重复调用的 Skill。实现采用 GitHub 高分 `marcosmodly/marketing-skill` 的证据纪律，并结合 ChatGPT 已提供的 `consumer-review-collector` Skill 的评论字段原则：先固定评论字段，再把语义编码与统计分开；事实与推断分开；证据必须能回到原评论文本。此次目录从零建立，没有复用电脑中已有的实验四成品。

## 输入与输出

- 输入：`data/reviews.csv`，至少包含 `review_id, brand, product, rating, review`。
- 输出：`outputs/encoded_reviews.json`，每条记录包含 `sentiment`、`need`、`pain_point`、`scenario`、`purchase_barrier`、`evidence`、`confidence`。
- Schema：`schema/consumer-insight.schema.json`。
- 规则：没有原文证据时使用 `unknown` 或 `[]`，不能根据品牌、评分或常识补写结论。

## 运行验证

项目只使用 Python 标准库：

```powershell
python scripts/validate_skill.py
```

验证脚本会检查 CSV/JSON 的 ID 一致性、字段枚举、证据片段是否为原文连续子串、空评论的未知处理，以及 10 条样例是否全部覆盖。

## 交付物

- `skills/consumer-insight-skill/SKILL.md`：可复用 Skill 的调用说明和边界
- `docs/label_dictionary.md`：标签字典、允许值和判定规则
- `schema/consumer-insight.schema.json`：结构化输出 Schema
- `data/reviews.csv`：10 条匿名试样输入
- `data/test_cases.json`：10 条预期输出试样
- `outputs/encoded_reviews.json`：按 Skill 规则生成的结构化结果
- `docs/blind_test_record.md`：盲测过程与一致性记录
- `docs/failure_cases_and_revision.md`：失败案例、修订前后规则
- `docs/external_skill_reference.md`：高分 GitHub Skill 来源、Stars、固定提交和复用边界

版本标签：`v0.2`。
