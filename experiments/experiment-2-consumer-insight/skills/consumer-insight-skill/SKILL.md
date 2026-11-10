---
name: consumer-insight-skill
description: 将消费者评论逐条编码为有证据约束的结构化洞察 JSON，不替原文补写未知信息。
metadata:
  short-description: Evidence-grounded consumer review coding
---

# Consumer Insight Skill

本 Skill 采用 GitHub 高分 `marcosmodly/marketing-skill` 在固定提交
`28456ea34da08b3344ea86721792755e320c9e21` 中体现的证据优先、未知不编造和事实/推断分离原则；来源与复用边界见 `docs/external_skill_reference.md`。

## 目标

把 `reviews.csv` 中的每条消费者评论编码成一条稳定 JSON。Skill 只做逐条识别，不做品牌排名、总体比例、经营建议或因果推断；统计应由后续程序基于 JSON 计算。

## 输入

CSV 至少包含：

| 字段 | 要求 |
| --- | --- |
| `review_id` | 稳定且唯一的评论 ID |
| `brand` | 品牌名；未知时保留 `unknown` |
| `product` | 产品名；未知时保留 `unknown` |
| `rating` | 1–5 的整数；空值可以保留并标记为未知 |
| `review` | 原始评论文本；空文本不能伪造证据 |

`review_id` 必须原样写入输出，不能重新编号。评论文本必须作为唯一语义依据；品牌、商品、评分和外部知识不能替代评论中的证据。

## 输出

每条输入对应一条 JSON 对象，字段必须符合 `schema/consumer-insight.schema.json`：

- `review_id`
- `sentiment`
- `need`
- `pain_point`
- `scenario`
- `purchase_barrier`
- `evidence`
- `confidence`

数组字段允许多个标签。无明确证据时返回 `[]`；当一个字段无法判断时返回 `['unknown']`。`evidence` 是对象数组，每项包含 `field` 和 `quote`，其中 `quote` 必须是原评论中的连续原文片段。

## 编码步骤

1. 先读取原文，不根据评分直接推断情绪或痛点。
2. 标记评论明确表达的情绪、需求、痛点、使用场景和购买障碍。
3. 每个标签都寻找最短、足以支持它的原文片段；找不到就删除该标签并改为 `unknown` 或空数组。
4. 复核 `evidence.quote in review`，复核每个 `review_id` 只出现一次。
5. 根据证据完整度给出置信度：明确直接表达为 `high`；语义可解释但不完整为 `medium`；空评论、模糊短语或仅凭上下文猜测为 `low`。
6. 输出 JSON，不输出排名、百分比、推荐或评论之外的事实。

## 边界规则

- “价格有点贵”“因为太贵没买”可以标记 `pain_point: price` 或 `purchase_barrier: price`，必须引用原句。
- “希望包装更好”表示改进需求和包装痛点；“包装很好”只能支持正向证据，不能标记痛点。
- 一条评论可以有多个标签；同一标签在一条评论中只保留一次。
- “还行”“不知道”“没用过”和空评论不能强行归类，使用 `neutral`/`unknown` 和低置信度。
- 场景只有在评论明确出现“通勤、出差、送礼、家里”等表达时才标记。
- 评分不是情绪证据。评分与文字冲突时标记 `mixed` 或 `unknown`，并在证据中只引用文字。
- 原文没有说明的购买障碍、需求和场景必须保持未知；禁止使用常识填空。
- 任何由多条评论汇总出的比例、排名或建议都必须交给后续统计程序，并保留样本量和原文索引。

## 自检

在仓库根目录运行：

```powershell
python experiments/experiment-2-consumer-insight/scripts/validate_skill.py
```

自检失败时先报告缺失字段、非法枚举、ID 不一致或证据不在原文中的具体记录，再修订规则或输出。
