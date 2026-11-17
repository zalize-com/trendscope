# Competitive learning plan — 竞品解剖与升级方案

> 方法论：先把「我们是什么」说清 → 再逐产品解剖「它强在哪/弱在哪」→ 按四个维度
> （代码质量 / 想法与思路 / 设计与流程 / 架构）提取可学项 → 汇总成升级方案。
> 所有竞品均已本地部署实测或源码解剖（11/17–11/18），非纸上谈兵。

## 0. 我们是什么（自我解剖）

**trendscope**：唯一一个「开发者注意力开放数据集」——9,213 源每日快照、
109k+ items、CC0、可下载、带 provenance。本质是**数据产品**而非仪表盘：
git 即数据库、Actions 即采集器、CF Pages+raw 即分发。用户心智 = 「要历史数据
和可下载资产来这，别的站只给当下一屏」。

**feedpaper**：fork 式自托管日报模板——「你的数据归你」对抗托管订阅。
用户心智 = 「不想注册 usedigest/TLDR，fork 就走」。

**我们的既有优势**（学习中不能丢的）：
- 零注册/零后端/零运维——竞品里只有 ai-news-radar 同级轻
- 数据资产可下载 + 版本化 + 健康标注（dormant/moved/zerowatch）——无人对标
- stdlib-only 管线——十年后仍能跑
- 方法论沉淀（methodology.md 47 条实战教训）

**我们已知的短板**（竞品反衬出的）：
- 采集层只取不判——无 AI 质量层（freebie-radar 有三层降噪）
- 站点信息密度高但「首屏故事」弱——WorldMonitor 一屏即战场
- 无推送/订阅出口（Telegram/邮件路由）——读者只能主动来
- 去重指纹弱——同题跨源重复靠 crossover 事后关联，非管线内去重
- tools 页数量取胜但单件深度浅（vs CyberChef/DevToys 的工艺感）

## 1. 竞品逐项解剖（源码级）

### 1.1 WorldMonitor（koala73/worldmonitor，2026-01 建，90.8k★）⭐ 最强学习对象
- **形态**：TS SPA + Vercel Edge + Railway seeders + Upstash Redis + Tauri 桌面。
- **架构精华**：**registry 驱动**——图层/服务/proto/locale/CI 全由注册表定义，
  `npm run docs:check` 验证注册表与文档契约同步；每个 seeder 写 `seed-meta:<key>`
  （freshness 元数据），health 端点把 BOOTSTRAP/STANDALONE/ON_DEMAND key 分类报告。
  → **我们的 zerowatch 是它的 health-keys 思想的雏形，但没到 registry 契约层**。
- **工程纪律**：AGENTS.md 规定 PR 必须附 UI 截图证据、import 方向 lint 强制、
  ownership rule「改拓扑必须同 PR 改文档」。
- **变现**：站内 Pro 分层（高级工作区/告警）——证明仪表盘可收费。
- **不学**：Vercel+Railway+Upstash 三供应商绑死、SPA 对 SEO 负资产。

### 1.2 BettaFish 微舆（42.7k★）⭐ 多 Agent 范式
- **形态**：6 引擎分工——MindSpider（话题抽取爬虫）、InsightEngine（深度搜索 agent：
  FirstSearch→FirstSummary→Reflection→ReflectionSummary→ReportStructure→Formatting
  的 node 图）、MediaEngine、QueryEngine、ReportEngine、ForumEngine（LLM 主持的多
  智能体辩论）。
- **精华**：**分析不是一次 LLM 调用而是一个 node pipeline**，每节点单一职责、
  聚类采样（MAX_CLUSTERED_RESULTS=50、每簇5条）控制上下文；多引擎各司其职
  由一个 ForumHost 汇总。
- **证明**：「AI 分析消费形态」需求巨大且被付费验证。
- **不学**：90+ Python 依赖+MySQL+6 个 LLM key 的重配置——违反零运维。

### 1.3 Freebie Radar（4 天 1.4k★）⭐ 降噪管线+设计语言
- **形态**：Node+SQLite+React 自托管工作台，docker compose 一键。
- **管线精华（最值得借）**：**三层成本递增降噪**——规则初筛（正则提兑换码/价格/
  去重指纹）→ 统一屏蔽词（命中即跳，**连 AI 额度都省**）→ AI 语义二审
  （keep/形态/类目/获取方式/质量分1-5）。先便宜的判，贵的留给难的。
- **设计精华**：DESIGN.md 是一份完整 design token 清单（canvas/ink/brand/accent
  色阶+语义色 deal/code/alert），目标是「Linear/Things 3 精密工作台感」。
- **正交分类学**：形态×领域×获取方式三维，而不是我们的单维 lane。
- **推送路由**：按频道/类目/价格/分数配 Telegram 路由。
- **不学**：React SPA 工作台形态（我们是静态站）。

### 1.4 Horizon（Thysrael/Horizon，14.5k★，2026 新）⭐ AI 分层+配置体验
- **AI 层分工**：analyzer（重要性）/classifier（分类）/enricher（补充）/summarizer
  （摘要）四层独立类 + 独立 prompting 目录；tenacity 重试 + Pydantic 校验 +
  `gather_ai_tasks` 并发控制。
- **extractor registry**：trafilatura→firecrawl→outcrawl→specstream 可插拔降级链
  ——与我们直连→worker→rss2json→feed2json 同构，但它是**注册表模式**，我们是
  写死在函数里。
- **配置体验**：`horizon-wizard` 交互式问兴趣自动生成 config.json——**降低
  首次使用门槛的样板**（fork 产品最缺这个）。
- **MCP server**：管线各阶段暴露为 MCP 工具，AI 助手可逐段调用——把管线当
  工具箱而非黑盒。
- **profiles/**：ai-creator/finance-news/tech-blog/tech-news 预设档——订阅 preset
  而非自己写 config。

### 1.5 ClawFeed（2.4k★）⭐ 单文件防御性编程样本
- 870 行 server.mjs 一个文件装下全部后端：SSRF 防护（assertSafeFetchUrl +
  isPrivateOrSpecialIp 拦内网地址）、OAuth state HMAC 签名/验证、session cookie
  签名、SQLite 零配置。**小而硬**——证明工具不必大，但要防御完备。
- 不学：Google OAuth 多用户（我们零账号）。

### 1.6 ai-news-brief（frankzch，inbrief.info 引擎）
- **两级去重**：SimHash 快速粗筛 → pgvector 语义精判。我们目前只有 URL/标题
  指纹，同题换源换标题会漏。
- **内容抓取降级链**：trafilatura→curl_cffi→DrissionPage（真浏览器）三级。
- 370+ 源含 ~310 个 X 账号——X 靠用户自带 token，证实 X 无免登录路径。

### 1.7 FreshRSS / changedetection.io / Huginn（成熟自托管）
- FreshRSS：**先装后配**的安装流程（do-install→create-user→导入 OPML）是
  自托管产品的标准 onboarding；feedpaper 的两步（fork+Pages）比它还简。
- changedetection：**任务+频道通知+diff 高亮**的监控范式，"盯网页变化"这个
  动词极强——我们的 zerowatch 是它的数据版（盯 feed 死活）。
- 不学：都需服务器部署，形态不同。

### 1.8 ai-news-radar / DailyHot / HotList / mo.fish
- ai-news-radar：和我们同构（静态站+数据 JSON+Actions），但只做 AI 单域、
  无历史资产——**验证了我们模式的可行性，也证明「无数据集=无壁垒」**。
- DailyHot 系：60+ 平台 tab 切换的热榜形态是「board tab 墙」的成熟参照。

### 1.9 非开源对照：it-tools / CyberChef / mo.fish / usedigest / inbrief.info
- it-tools：左栏搜索+工具卡网格+收藏置顶=工具站交互标杆（tools/all 已学）。
- CyberChef：单工具即「操作流编辑器」（拖拽 recipe）——深度单件的天花板。
- usedigest/inbrief.info：成品形态证明「每日摘要」可独立成产品+可收费。

## 2. 四维学习方案

### 维度一：代码质量与规范
| 学谁 | 学什么 | 落地动作 |
|---|---|---|
| WorldMonitor | registry 驱动 + docs 契约同步 + seed-meta freshness | collect.py 的 feeds_*.json 已是 registry 雏形 → 加 `npm run check`-式**一致性校验脚本**（registry↔SOURCES.md↔llms.txt↔sitemap 四方对账，进 CI） |
| WorldMonitor | 「改拓扑必须同 PR 改文档」ownership rule | 写进 product-playbook + AGENTS.md |
| Horizon | tenacity 重试 + Pydantic 响应校验 | collect.py stdlib 约束下用 dataclass+轻校验替代；AI 层（将来）抄它的分层 |
| ClawFeed | SSRF 防御清单（私网 IP 拦截） | opml-doctor Worker 已有拦截，对表补齐 IPv6/link-local |
| BettaFish | node pipeline 单职责拆分 | collect.py 的 _make_feed_fetcher 已太长 → 拆 fetch/classify/persist 三阶段 |

### 维度二：好想法（Idea）与思路
| 学谁 | 学什么 | 落地动作 |
|---|---|---|
| Freebie Radar | **成本递增三层降噪**（规则→屏蔽→AI） | 我们采集层加第 1.5 层：源内 blocklist/重复指纹（同题跨源同小时 dedup），为将来 AI 层留插槽 |
| Freebie Radar | 正交分类（形态×领域×获取方式） | items 加 `kind` 维度（news/tool/paper/release/discussion），board/搜索可按 kind 切 |
| BettaFish | 聚类采样控制上下文 + Reflection 节点 | digest.py 将来上 LLM 时：先聚类选代表再摘要，二次反思提升质量 |
| Horizon | wizard 交互式配置 + profiles 预设 | feedpaper 加 `feeds-presets/`（ai/dev/cn-tech 三档 starter），README 改「选一档即可」 |
| Horizon | 管线暴露为 MCP 工具 | trendscope 数据面本来就开放——补一个 `.mcp.json`/tools 描述文件，让 agent 能直接调 latest/zerowatch/feeds |
| changedetection | 「盯变化」的动词心智 | zerowatch 已是数据版；给 sources 页加「watch this source」邮件/RSS 订阅钩子（先用现有 feed.xml 按源切片） |
| FreshRSS | OPML 导入式 onboarding | feedpaper 已有 OPML 导入；补「从 OPML 生成 feeds.yaml」向导页 |

### 维度三：设计与流程
| 学谁 | 学什么 | 落地动作 |
|---|---|---|
| Freebie Radar | 完整 design token 清单（语义色阶） | trendscope.css 已成型 → 补 semantic tokens（deal/dead/moved/dormant 语义色），全站状态色统一 |
| WorldMonitor | 一屏即战场的信息密度组织 | index 首屏：stamp→board→不过三屏看到数据集入口；现在 hero 文案已 OK，可加「live 数据证明条」（今日 items/源数/最新条目滚动） |
| it-tools | 工具站三件套（搜索/网格/收藏） | tools/all 已学；剩余差距=工具内「最近使用」+键盘快捷 |
| CyberChef | 单件深度：输入→操作链→输出 的可组合性 | 选 1-2 个工具做深（如 URL 工具加「chain」多步操作），不必全做 |
| 全部 | 移动首屏体验 | 逐页过一遍 375px 宽度截图检查（目前基本没验过移动） |

### 维度四：架构
| 学谁 | 学什么 | 落地动作 |
|---|---|---|
| WorldMonitor | 分层数据契约：bootstrap（首屏必载）/standalone/on-demand | 我们已有 latest/latest-lite/series 三级 → 正式命名分层并文档化，health 端点按层报告 |
| Horizon | extractor/fetcher **注册表模式**而非写死函数 | collect.py fetcher 表已是数据驱动，把兜底链也注册表化（fallback_chain: [direct, worker, rss2json, feed2json] 声明式） |
| ai-news-brief | SimHash 粗筛 + 向量精判 两级去重 | SimHash 纯 Python 可 stdlib 实现 → items 加 simhash 字段，同题去重进管线 |
| BettaFish | 引擎间消息总线（ForumHost 汇总） | 远期：digest/agent 分析层独立进程消费 data/，不耦合采集 |
| ClawFeed | SQLite 作本地读模型 | 不需要——git+JSON 已覆盖；但 widgets/embed 可考虑单文件 sqlite 导出供重度用户 |

## 3. 总体升级方案（按 ROI 排序）

> 原则：只做强化「开放数据集」差异化的升级，不抄竞品的重形态。

### P0 — 本周内（强化差异化护城河）
1. **kind 正交维度**（idea②）：items 加 kind 字段（规则可判 80%：paper=arxiv/nature、tool=github、release=tag、news/discussion 兜底）→ board 加 kind 过滤。成本 ~0.5 天，立刻让数据集多一维。
2. **registry↔文档一致性校验脚本**（code①）：四方对账进 CI，防 SOURCES.md/llms/sitemap 漂移。成本 ~0.5 天。
3. **SimHash 同题去重**（arch③）：stdlib 实现 ~80 行，管线内 dedup + history.csv 减噪。成本 ~1 天。
4. **语义色 tokens 统一**（design①）：dead/moved/dormant/deal 状态色全站统一。

### P1 — 两周内（消费形态升级）
5. **MCP 工具描述文件**：让 AI agent 能把 trendscope 当数据源直接调（mcp.json + tools 文档）——蹭 MCP 生态流量。
6. **feedpaper profiles 预设 + wizard 式 README**：fork 用户选档即用。
7. **按源/按 lane 的 RSS 切片订阅**：feed.xml 已全量，补 per-lane feed 让每个 lane 可订阅（等于免费版"推送路由"）。
8. **移动端首屏体验 audit + 修复**。

### P2 — 需要 LLM key 后启动（用户给 key 即解锁）
9. **AI 质量层**（freebie-radar 三层模式）：规则初筛（已有）→ 屏蔽词 → LLM 评分 keep/quality 1-5，只给 top N 跑省额度。先接 OpenRouter 最便宜模型。
10. **LLM digest 升级**：聚类采样→摘要→reflection 二次（BettaFish node 模式精简版）。
11. **推送路由**：Telegram/邮件按 lane+分数路由（freebie-radar 模式，用户自配 bot token）。

### 不做清单（学到的反面）
- ❌ SPA 化/多供应商后端（WorldMonitor 架构太重，且我们是数据产品）
- ❌ 账号系统/OAuth（违反零注册定位）
- ❌ 90+ 依赖的 Python 重框架（违反 stdlib 约束）
- ❌ 自建爬虫打 X/微信（无免登录路径，做了就死）

## 4. 执行分工
- A：P0-1/3（kind 维度+SimHash 入管线）、P1-7（per-lane feed 生成）
- B：P0-2/4（一致性校验+语义色）、P1-5/6/8（MCP 描述、presets、移动 audit）
- P2 全部等用户提供 LLM key 后启动
