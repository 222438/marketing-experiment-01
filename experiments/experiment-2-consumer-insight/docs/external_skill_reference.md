# 外部高分 Skill 参考记录

## 选用来源

- 仓库：[marcosmodly/marketing-skill](https://github.com/marcosmodly/marketing-skill)
- Skill：[`skills/competitor-research/SKILL.md`](https://github.com/marcosmodly/marketing-skill/blob/28456ea34da08b3344ea86721792755e320c9e21/skills/competitor-research/SKILL.md)
- GitHub Stars：134（2026-11-10 查询）
- 固定提交：`28456ea34da08b3344ea86721792755e320c9e21`
- 选择理由：这是检索结果中与营销/消费者洞察任务直接相关且关注度较高的可复用 Skill。它要求事实有来源、未知信息明确标注、事实和推断分开，并保持中性表达。

## 本实验复用的原则

1. **证据优先**：每个输出标签都必须连接到评论中的连续原文片段。
2. **未知不编造**：评论没有说明的场景、需求或购买障碍使用 `unknown`，不能用产品常识填空。
3. **事实与推断分开**：Skill 只做逐条语义编码，不输出总体排名、百分比或经营建议。
4. **中性表达**：保留 mixed、neutral 和 low confidence，避免把模糊评论包装成确定结论。

## 复用边界

没有复制该仓库的竞品研究模板、网页检索工具、营销文案流程或代码。实验二只迁移上述质量控制思想，并使用本实验自己的 `reviews.csv`、标签字典和 JSON Schema。评论字段和评论采集边界参考 ChatGPT 已提供的 `consumer-review-collector` Skill；本实验不抓取网站，也不调用大模型 API。
