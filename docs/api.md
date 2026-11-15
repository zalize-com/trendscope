# trendscope data API

Everything is static files in this repo — no key, no rate limit, CC0.
Fetch straight from GitHub raw or the Pages site (`/trendscope/…`).

| Endpoint | Format | Contents |
|---|---|---|
| `data/latest.json` | JSON | Most recent full snapshot: `items` per source, `topics`, `total_items` |
| `data/latest.csv` | CSV | Same snapshot as flat rows |
| `data/history.csv` | CSV | Append-only cumulative history — every item × every day (velocity analysis) |
| `data/index.json` | JSON | `{"snapshots": ["2026-11-07", …]}` — list of available daily archives |
| `data/daily/YYYY-MM-DD.json` | JSON | Per-day archive (full `items` + `topics`) |
| `data/daily/YYYY-MM-DD.csv` | CSV | Per-day archive, flat |
| `data/health.json` | JSON | Per-source run health `{ok, items, ms}` |
| `data/health-log.csv` | CSV | Daily `date,source,ok,items,ms` health history |
| `data/topics-history.csv` | CSV | Append-only per-day topic counts — time-series |
| `docs/api/movers-latest.json` | JSON | Entered/left/gainers/droppers + package rank movers for the latest day pair |
| `docs/api/movers-YYYY-MM-DD.json` | JSON | Same schema, archived per day — the movers history (from 2026-11-15) |
| `docs/api/week.json` | JSON | Rolling last-7-days top-50 by cumulative normalized heat + per-topic counts (same metric as `week.html`) |
| `docs/api/month.json` | JSON | Same aggregate over a rolling 30-day window |
| `docs/api/ideas-latest.json` | JSON | Ask-HN demand clusters + top asks + built/gap coverage |
| `docs/api/stats.json` | JSON | Dataset summary: days, rows, unique URLs, per-source totals |
| `docs/api/today.json` | JSON | One-call 'today' summary: top-10, topic mix, new entries, active streaks, movers counts, hiring pulse |
| `docs/api/risers.json` | JSON | Single-day spikes, package rank jumps, sustained climbers still on board |
| `docs/api/streaks.json` | JSON | Active on-board streaks (2+ consecutive days) + all-time longest runs |
| `docs/api/domains.json` | JSON | Most-linked hostnames leaderboard (days/items/sources/top hit) |
| `docs/api/authors.json` | JSON | Most-featured authors & orgs leaderboard (days/items/sources/top hit) |
| `docs/api/crossovers.json` | JSON | Same URL ranked on ≥2 sources — the breakout stories |
| `docs/api/new.json` | JSON | First-seen items on the latest snapshot — URL never in history before (per-source counts in `by_source`) |
| `docs/api/discussed.json` | JSON | Comment leaderboards: most-discussed + heated (comments/point ratio, score ≥ 50) |
| `docs/api/sources.json` | JSON | Per-source stats over the whole window: items, unique urls, median days-on-board, one-day %, top item |
| `docs/api/series.json` | JSON | Per-item daily series: `{title, source, metric, author, days: {date: [score, rank, comments]}}` for every tracked url — the canonical feed all analytic pages read |
| `docs/api/velocity.json` | JSON | Score growth rate for multi-day items: url/title/source/metric/days/delta/per_day/latest, sorted by +/day — rolling counters excluded |
| `docs/api/weekday.json` | JSON | Day-of-week x source item counts — `{sources:{name:{counts:[mon..sun],total}}}` |
| `docs/api/rhythm.json` | JSON | Hour-of-day (UTC) x source capture counts — `{sources:{name:{counts:[0..23],total}}}` |
| `data/hiring.json` | JSON | Latest HN monthly hiring/seeking thread comment counts |
| `data/hiring-history.csv` | CSV | Append-only daily log of those counts (labor-demand signal) |
| `data/hiring-monthly.csv` | CSV | All canonical monthly hiring/seeking threads, 2010 → today |
| `data/hn-canon-monthly.csv` | CSV | HN canon: top-10 stories per month, Feb 2007 → today |
| `data/show-hn-monthly.csv` | CSV | Show HN canon: top-10 launches per month, Jan 2012 → today |
| `data/ask-hn-monthly.csv` | CSV | Ask/Tell HN canon: top-10 questions per month, Feb 2007 → today |
| `docs/index.json` | JSON | Index of `docs/digest/` weekly digests, `docs/movers/` reports and `docs/brief/` daily briefs |
| `docs/brief/YYYY-MM-DD.md` | Markdown | Rule-based daily prose brief: top story, biggest climber, new entries, streaks, source mix |
| `feed.xml` | RSS | Daily snapshots + movers + digests as feed items |

Schema for item rows: `source, rank, title, url, score, metric, comments, author, tags, captured_at` — see [data-dictionary.md](data-dictionary.md).

Example (Python, stdlib):

```python
import json, urllib.request
snap = json.load(urllib.request.urlopen(
    "https://zalize-com.github.io/trendscope/data/latest.json"))
print(snap["date"], snap["total_items"])
```

Attribution is welcome but not required — CC0.

### `docs/api/badge.json`

shields.io endpoint badge carrying the dataset size (`items tracked: N rows · Nd`) —
embed `![trendscope](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/zalize-com/trendscope/main/docs/api/badge.json)`.

### `docs/api/badge-top.json` | `docs/api/badge-sources.json`
shields.io endpoint badge carrying today's #1 HN story — embed a live
"top story" widget in any README:

```markdown
![top](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/zalize-com/trendscope/main/docs/api/badge-top.json)
```