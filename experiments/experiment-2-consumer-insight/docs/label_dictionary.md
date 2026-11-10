# 标签字典

所有标签都是评论文本中的可观察编码。没有文字证据时不使用推断标签。

## sentiment

| 值 | 含义 |
| --- | --- |
| `positive` | 明确表达满意、喜欢、推荐或效果好 |
| `negative` | 明确表达不满、失望、拒绝或效果差 |
| `mixed` | 同一评论同时出现明确正向和负向表达 |
| `neutral` | 只有事实描述、询问或无法判断倾向 |
| `unknown` | 评论为空或证据不足以判断 |

## need

允许值：`quality`、`value`、`convenience`、`service`、`information`、`fit`、`durability`、`safety`、`none`、`unknown`。

只在评论明确提出“需要、希望、想要、应该”等需求时标记。没有明确需求使用 `none`；评论为空或语义不可读使用 `unknown`。

## pain_point

允许值：`price`、`quality`、`taste`、`delivery`、`packaging`、`service`、`usability`、`fit`、`availability`、`none`、`unknown`。

只记录明确的负面问题或改进意见。一个评论可以有多个痛点，但同一痛点只计一次。

## scenario

允许值：`home`、`commute`、`work`、`travel`、`gift`、`outdoor`、`exercise`、`family`、`unknown`。

只有原文直接提到使用地点、活动或对象时才标记；不能因为产品类别推测场景。

## purchase_barrier

允许值：`price`、`trust`、`quality`、`availability`、`delivery`、`fit`、`complexity`、`none`、`unknown`。

“没买、犹豫、不会再买、因为……所以放弃”等表达才构成购买障碍。已购买但不满意只标记痛点，除非原文明示影响下一次购买。

## evidence 与 confidence

`evidence` 中的 `quote` 必须是 `review` 的连续子串，`field` 指向被支持的输出字段。`high` 表示直接明确，`medium` 表示有一定语境但不完整，`low` 表示空文本、模糊表达或只能保守地输出未知。
