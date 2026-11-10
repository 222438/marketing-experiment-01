# 数据字典

一行＝一条历史评论，商品字段通过 ASIN 从元数据表连接。空白与 Unknown 都按缺失计算；0 票是合法数值，不是缺失。

| 字段 | 类型/单位 | 上游来源 | 解释与规则 |
|---|---|---|---|
| record_id | string | 派生：MI-加评论原始行号 | 本实验追溯键，不是 Amazon 评论 ID；不得据此寻找评论者 |
| asin | string，10 位 | 两个源文件的 asin | 商品标识，多条评论可重复；连接时不扩增行数 |
| product | string | metadata.title | 商品名；清洗时仅解码 HTML 实体并去首尾空白 |
| brand | string | metadata.brand | 缺失/Unknown 的行不能用于品牌比较；不从商品名推断 |
| price | decimal，USD | metadata.price | 历史采集时商品价格；必须有限且为正，原数值不变，显示两位小数；不代表成交价 |
| rating | integer，1–5 | reviews.overall | 评论评分；5.0 规范为 5，数值不变 |
| review | string | reviews.reviewText | 保留原评论文本；空评论排除，不翻译、不改写、不由模型生成 |
| review_date | date | reviews.reviewTime | 原始 MM DD, YYYY → YYYY-MM-DD；与 UTC Unix 时间交叉校验 |
| unix_review_time | integer，秒 | reviews.unixReviewTime | Unix 秒数，清洗不改动含义 |
| helpful_votes | integer，≥0 | reviews.helpful[0] | 认为有用的票数；不是点赞量或销量 |
| total_votes | integer，≥helpful_votes | reviews.helpful[1] | 总投票数；0 时有用票比例不定义 |
| source_review_line | integer，≥1 | 评论解压文件物理行号 | 用于回到原始来源；不是用户 ID |
| source_metadata_line | integer，≥1 | 元数据解压文件物理行号 | 用于复核商品价格、品牌与名称 |

`reviewerID`、`reviewerName` 没有进入公开样本。源数据未提供该样本所需的销量、收藏数或实时价格，本项目不补造这些列。

全部 13 个字段都参与清洗后完整率检查。公式：非空且非未知的单元格数量 / 当前阶段行数；raw 分母为 450，clean 分母为 385。原始数据里的 Unknown 不计作完整值。

