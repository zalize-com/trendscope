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
