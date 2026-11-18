# trendscope 数据集盘点与类型分析（2026-11-18）

## 三层资产结构

| 层 | 文件 | 体量 | 作用 |
|---|---|---|---|
| 原始快照 | latest.json / latest-lite / latest.csv / data/daily/* / history.csv | 42MB / 17天 / 37万行 | 每日全量 9,213 源 × ~108k 条；provenance=url+captured_at |
| 衍生语义 | kind.json / dedup.json / feeds.json / dormant.json / zerowatch.json / health*.csv | ~4MB | 类型标注、同题去重、feed 注册表+健康度 |
| 产品面 | docs/api/* (45) / data/rss (20) / data/opml (14) | — | 页面/订阅/外部消费的稳定端点 |

## 内容类型分布（2026-11-18 全量 108,038 条，规则分类）

| 类型 | 条数 | 占比 | 典型 lane |
|---|---|---|---|
| 未分类正文 (other) | 83,630 | 77.4% | 全 lane |
| AI/ML | 7,275 | 6.7% | tldr 43% / bytebytego 60% / aheadofai 93% |
| 教程 | 4,175 | 3.9% | freecodecamp 60% / flaviocopes 47% |
| 提问/求助 | 3,474 | 3.2% | ask 67% / briefs 67% / wellkeptwallet 50% |
| 版本发布 | 2,236 | 2.1% | simonw 47% / w4github 100% / thenewstack 27% |
| 深度分析 | 1,938 | 1.8% | lorinhochstein 40% / surfingcomplexity 40% |
| 安全事件 | 1,829 | 1.7% | sec 27% / techmeme 33% / krebs 30% |
| 开源工具 | 1,564 | 1.4% | echojs 13% / w4feeds7 36% |
| Show/发布 | 982 | 0.9% | show 92% / spotify 20% |
| 招聘 | 670 | 0.6% | developingdev 20% / moneyunder30 10% |
| self-hosted | 265 | 0.2% | codeinwp 12% / ddadaal 7% / miaotony 27% |

## 结构特征（关键事实）

- **br lane = 66% 体量**（71,018/108,038）：数据集本质是「开发者博客长尾」普查，不是新闻聚合——这是跟 Techmeme/HN 的结构性差异
- 每源 top15 截断：71k br 条目 ≈ 4,700 活源 × 15，覆盖面=广度非深度
- AI/ML 是无可争议的当代主导主题（显式 6.7%，且 other 里还藏着大量）——top30 词频 code/review/agent/claude/agents 全在前排
- 类型有 lane 指纹：sec 是事件驱动、nl/tldr 是 AI 重型、pb 是长尾杂项、yt 是教程+AI

## 每个类型的作用判定

| 数据 | 类型 | 已验证用途 | 待开发用途 |
|---|---|---|---|
| latest/daily/history | 时间序列快照 | movers/digest/时间旅行页 | 主题趋势线（weekly wave）、预测面 |
| feeds.json + 健康度 | feed 注册表 | feeds 目录/state-of-rss/opml-doctor | awesome 列表体检 SaaS、feed 迁移图谱 |
| kind.json | 内容类型标注 | kind chips（10 页） | 类型筛选订阅（只看 release/paper）|
| dedup.json | 同题簇 | item 页 near-dup 行 | 跨源热度=去重后真实传播度 |
| zerowatch/dormant | 健康信号 | sources 页 chip | 死源目录、RSS 生态年报 |
| need-signal 提取 | 需求雷达 | self-hosted 波发现→产品页 | 每日自动跑 theme 聚类出「今日需求榜」 |

## 结论

数据集的真正形态：**开发者注意力长尾普查**。br lane 占 2/3 意味着我们对主流新闻是镜像，对「中长尾开发者在写/在读什么」是独家覆盖。价值排序：feed 健康资产（独家）> 需求雷达（今日已兑现）> 历史纵深（30 天后才显威）> 类型标注（稀疏但诚实）。
