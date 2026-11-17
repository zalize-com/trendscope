# Landscape scan — 2026-11-17

User asked for a wide sweep: domestic + international, open + closed source,
big + small + obscure. Four categories relevant to our two products.

## A. Tech-news aggregators & trend radars

### Big / established
| Product | Model | Gap for us |
|---|---|---|
| Techmeme (US, since 2005) | Human-curated live page, no account | Ephemeral; no data export |
| daily.dev | Browser ext + feed, freemium, **account required** | No dataset, walled |
| Feedly / Inoreader | Hosted RSS, freemium, account | No trend data |
| Hatena Bookmark (JP) | Social bookmarking hot-entry (b.hatena.ne.jp/hotentry/it) | Japan-only lane, no export |
| tophub.today + TopList/mo.fish (CN, Go, 4.7k★) | Chinese consumer-platform hot lists (Weibo/Zhihu/Bilibili) | Different market entirely — not dev-source data |
| Lobste.rs | Community | Single source |

### Mid / indie
| Product | Model | Gap |
|---|---|---|
| **OrangeBot.AI** — closest US analog | 8-source morning digest, no account, AI summaries | Real-time only, no downloadable dataset |
| Hackertab.dev | New-tab extension | No persistence |
| theinternetrightnow / ViralSlate / Hotfork | Real-time dashboards | No history, no dataset |
| deadstack.net | LLM-clustered hourly tech news (Show HN 188pts) | Dashboard only |
| PulseTech.news, multimodal-scout | Small scrapers | Same |
| Sentinel Feed (OSS, Next.js) | 7-source radar, 15min refresh | No data retention |

### Open-source same-pattern repos (closest to feedpaper)
| Repo | Pattern | Note |
|---|---|---|
| **keep-up-daily** (LuizMacedo) | Python scraper + GH Actions + Pages dashboard, 6 sources, 30-day nav, commits daily JSON | Validates our pattern; personal dashboard, not marketed as dataset |
| **News-Agent** (zskfree) | GH Actions + Gemini filter + RSS out + GH Pages | AI-curated feeds |
| **daily-digest** (sjoerdbeentjes) | Bun + GH Actions → email + hosted digest + RSS | Needs SMTP + OpenRouter key |

**Verdict:** every aggregator is ephemeral or account-walled. Nobody persists a
normalized cross-source dataset. Our slot confirmed.

## B. Open datasets
| Dataset | Content | Gap |
|---|---|---|
| BigQuery HN (YC official) | stories+comments since 2006 | Single source, needs BigQuery |
| GH Archive | hourly event stream since 2011 | Events not attention/trends |
| HF open-index/hacker-news | monthly parquet | Single source |
| Launch-Day-Diffusion (academic) | 138-repo HN→star study | One-off research artifact |
| dev.to tutorial author's 17.9k HN→GH set | **paywalled download** | Proof paid niche datasets exist |

**Verdict:** datasets exist but are all single-source. Zero competition for
cross-source daily-normalized-CC0. Paywalled niche datasets prove the market.

## C. RSS infrastructure (feedpaper's landscape)
| Product | What | Scale |
|---|---|---|
| **RSSHub** (DIYgod, 47k★ AGPL) | Generates RSS for anything; 5,000+ public instances | The giant — complementary not competitor (we cite its routes) |
| Folo | AI RSS reader by RSSHub author | Reader side |
| FreshRSS / Miniflux / TT-RSS-fork / CommaFeed / yarr | Self-hosted readers (PHP/Go+PG) | Need a VPS — our zero-ops wedge |
| Kill-the-newsletter | newsletter→RSS | Inverse tool |
| **OPML starter packs**: plenaryapp/awesome-rss-feeds (~500 by country), Tidings bundles (Top 200, >150 feeds = paywall!), lqdev.me packs, SlashFeed packs (962 tech feeds) | Curated OPML bundles | **None carry health signals** — dead/moved/dormant labels are our unique wedge (zerowatch) |

**Verdict:** feedpaper's "your data in your repo, zero server" position is
uncontested. Reader apps do starter packs but none are health-annotated —
C1/feedstarter wedge still valid.

## D. Developer tool collections
| Product | Notes |
|---|---|
| IT-Tools (it-tools.tech, MIT, Vue) | ~100 tools, self-hostable — the reference we benchmarked |
| CyberChef (GCHQ) | Recipe chaining, heavy |
| DevToys (desktop) / DevUtils (paid macOS) / Boop | Native apps |
| DataEngUtils | Data-eng niche, Parquet in-browser |

**Verdict:** crowded category. Our 88 tools are SEO-traffic assets, not the
product. Correctly deprioritized as a differentiator.

## Positioning summary (what the sweep confirms)

1. **Dataset moat intact**: aggregators are ephemeral, datasets are
   single-source — cross-source daily normalized CC0 is still only us.
2. **Health-annotated OPML is unique**: starter packs exist everywhere but
   nobody labels dead/moved/dormant — zerowatch data is defensible.
3. **CN market is a different game** (consumer hot lists); JP/KR have their
   own aggregators — English dev-source niche is our lane.
4. **RSSHub is infrastructure, not competition** — potential source/citation.
5. Watch closest analogs: OrangeBot.AI (digest UX), keep-up-daily (same
   GH-Actions pattern), Tidings/SlashFeed (OPML UX).

## 补扫：聚合雷达/监控族（2026-11-17，GitHub 关键词扫描）

### 福利/线报族
- ZiChuanLan/freebie-radar 1.4k★（4 天爆红，本报告触发源）
- 中国「线报」生态真身：青龙面板+脚本——6dylan6/jdm 337、lo1kda/M_UTOPIA 33、mgmg22/QinglongMy 164
- 结论：线报=羊毛脚本形态，freebie-radar 把它产品化成工作台=爆红原因

### 热榜聚合族
- tophubs/TopList 4.7k（mo.fish）、imsyy/DailyHotApi 4.1k、uxiaohan/HotList-Web 456、huqi-pr/trending-in-one 465（唯一带归档思想的）、iiecho1/api-for-hot-search-golang 48
- 结论：全员实时，仅 trending-in-one 有小时级归档（单源微博热搜）

### 多平台爬虫基建族（小红书/X/FB 线）
- NanmiCoder/MediaCrawler **71k**——小红书/抖音/快手/B站/微博/贴吧/知乎逆向签名爬虫事实标准，垄断生态位
- 666ghj/MindSpider 429（BettaFish 配套爬虫）、XHS_Crawler 系全部个位数星
- **X/Facebook：无活的免登录开源方案**——X 断 API+登墙、FB Graph 锁死，所有爬虫要带 cookie/开发者账号；这个空位是真但没人能做，包括我们（零账号哲学同样受限）

### 舆情/监控族（企业 FOMO）
- 666ghj/BettaFish 微舆 **42.7k**——多 Agent 舆情分析（微博/小红书/抖音/知乎），近期爆红
- 思通舆情 627、hmmnxkl/LLM舆情助手 714
- 借：AI 二审/Agent 分析的消费形态

### 通用变更监控族（西人社区）
- huginn 50.6k、changedetection.io 35.9k——监控+触发器万能体，不同族不同客户

### 垂直监控
- cooderl/wewe-rss 9.6k：微信公众号→RSS（微信读书接口），私域订阅痛点已占
- 微博监控：全是个位数小项目无大一统

### 本轮结论
1. trendscope「沉淀成数据集」差异化仍稳——所有聚合器都是看现在
2. 社媒爬虫生态位被 MediaCrawler 垄断，不碰
3. X/FB 空位真但无免登录路径，不属于我们
