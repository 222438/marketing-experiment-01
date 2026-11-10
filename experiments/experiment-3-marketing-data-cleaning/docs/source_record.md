# 来源与日期记录

## 一手来源

- 发布者：Julian McAuley（UCSD）；托管：Stanford SNAP。
- [Amazon product data 官方说明](https://snap.stanford.edu/data/amazon/productGraph/)：评论、评分、有用票及商品元数据；价格单位为采集时美元。总体数据覆盖 1996 年 5 月至 2014 年 7 月。
- [Musical Instruments 评论压缩包](https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Musical_Instruments_5.json.gz)：10,261 条评论。
- [同类商品元数据压缩包](https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/meta_Musical_Instruments.json.gz)：84,901 条商品记录。
- 本次获取日期：2026-11-10，精确 UTC 时间见 acquisition_record.json。
- 两个原始压缩包的 SHA-256、抽样配置和 raw CSV 哈希见 source_manifest.json。已用原始压缩包复核快照，不只比对脚本自己的输出。

## 采集步骤与口径

1. HTTPS 下载两个公开压缩包，不访问 Amazon 登录页面，不绕过访问限制。
2. 核对 SHA-256。原文件不变时可重现；变更时停止，不能静默换数据。
3. 从全部 10,261 条评论中用种子 20261110 固定抽取 450 条，按原始文件行号排序。不预先过滤评分、品牌、价格或评论长短。
4. 先保存抽样前 50 条进行字段预检；再导入完整 450 条。
5. 按 ASIN 与商品元数据进行多对一连接；验证每个所需 ASIN 只出现一个元数据记录，避免连接膨胀。450 条评论对应 316 个商品，全部匹配成功。
6. 投影到 13 个实验字段，删除身份列，不改写评论内容；记录评论和元数据的原始行号。
7. 原始 CSV 指“采集后、清洗前的隐私最小化样本”，不是完整压缩包的逐字节副本。JSONL 投影保存所用原值，压缩包在本地缓存且不提交 Git。
8. 清洗只处理规范化和有明确依据的无效记录；保留全部原始行，以便检查被排除的样本。

## 三种获取方式比较

| 方式 | 能力 | 本实验判断 |
|---|---|---|
| 静态 HTML | 小规模可直接解析，但页面结构变动且可能缺价格/日期 | 不抓电商页面；仅阅读官方数据说明 |
| 公开 API | 字段稳定、可能有配额、认证和分页限制 | 未发现任务所需的免认证历史评论 API；本次不用 API 获取评论 |
| 教师/公开研究数据集导入 | 可固定快照并复算，时间可能较旧 | 图片未附教师 CSV；选用一手发布的公开研究数据集，用 HTTPS 导入 |

## 来源与使用边界

数据具有真实的公开评论来源，但无法独立确认每一位评论者的购买真实性；不要把“来源真实”写成“所有观点均属客观事实”。本批评论时间为 2004-09-29 至 2014-07-20，不能描述为当年新采集的市场评价。

官方页面要求使用时引用以下研究。本仓库保留该引用与来源，不把数据套用软件 Skill 的 Apache 许可证，也不声称原始评论为本项目原创：

Julian McAuley, Christopher Targett, Qinfeng Shi, Anton van den Hengel.
**Image-based recommendations on styles and substitutes.** SIGIR, 2015.
[官方论文链接](https://snap.stanford.edu/data/amazon/productGraph/sigir_draft.pdf)。
