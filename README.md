# trendscope

> The developer attention dataset — what developers are reading, building and
> downloading, snapshotted daily. Open data (CC0), updated by GitHub Actions.

![snapshots](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzalize-com%2Ftrendscope%2Fmain%2Fdata%2Findex.json&query=%24.snapshots%5B%23%5D&label=snapshots&color=58a6ff)
![items today](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzalize-com%2Ftrendscope%2Fmain%2Fdata%2Flatest.json&query=%24.total_items&label=items%20today&color=3fb950)
![license](https://img.shields.io/badge/data-CC0-green)

**Live dashboard:** `https://zalize-com.github.io/trendscope/` *(enable Pages: Settings → Pages → Deploy from branch → `main` / root)*
**Latest data:** [`data/latest.json`](data/latest.json)

![dashboard demo](docs/demo.webp)

## What's inside

A daily cross-source snapshot of developer attention:

| Source | Signal | Endpoint |
|---|---|---|
| Hacker News | front-page points & comments | `hn.algolia.com` |
| Show HN | launches — points & comments | `hn.algolia.com` |
| Ask HN | community questions — demand signals | `hn.algolia.com` |
| GitHub | new repos trending this week | `api.github.com/search` |
| Lobste.rs | hottest stories | `lobste.rs/hottest.json` |
| Dev.to | top articles (7d) | `dev.to/api` |
| Product Hunt | daily launch feed | `producthunt.com/feed` |
| Techmeme | editorial tech news | `techmeme.com/feed.xml` |
| npm | weekly downloads (watchlist) | `api.npmjs.org` |
| PyPI | monthly downloads (watchlist) | `pypistats.org` |
| crates.io | recent downloads | `crates.io/api` |

Every run also writes `data/health.json` — per-source item count and latency —
shown as the health line on the dashboard.

Every record carries `url` + `captured_at` for provenance, plus a per-source
`rank`. Scores are source-native (points / stars / reactions / downloads) —
compare within a source, not across.

## Files

| File | Description |
|---|---|
| `data/latest.json` | Most recent full snapshot (stable URL for consumers) |
| `data/latest.csv` | Same items, flat CSV |
| `data/daily/YYYY-MM-DD.json` / `.csv` | Full snapshot for that day |
| `data/history.csv` | Append-only cumulative history — velocity analysis |
| `data/index.json` | List of all snapshot dates |
| `feed.xml` | RSS feed of every snapshot + weekly digest |

## Site

- **Dashboard** (`index.html`): cross-source board, topic trends, rising items,
  and a day picker to browse any past snapshot.
- **Tools** (`tools/`): 18 free in-browser dev utilities — JSON formatter,
  regex tester, cron explainer, timestamp converter, Base64/URL, JWT decoder,
  chmod calculator, UUID/hash, text diff, markdown preview, color converter,
  text inspector, YAML↔JSON, outline→tree, URL query editor.
- **Weekly digests** (`docs/digest/`): machine-generated summaries plus
  narrative notes.
- **Topics** (`topics.html?t=AI%2FLLM`): per-topic drill-down — every story,
  repo and package matching a topic, grouped by source.
- **Compare** (`compare.html?a=…&b=…`): diff two daily snapshots — entries,
  exits and biggest gainers/droppers. The same diff is auto-published daily
  as markdown in `docs/movers/` and shipped in `feed.xml`.
- **Streaks** (`streaks.html`): staying-power leaderboard — items ranked by
  consecutive days on the board, computed client-side from `history.csv`.
- **Domains** (`domains.html`): most-linked sites across all snapshots,
  grouped by hostname from `history.csv`.
- **Digests** (`digest.html`): weekly markdown digests rendered in-site.
- **Embed widget** (`embed.html`): the top-10 board as a drop-in iframe for
  blogs/docs (no signup, updates daily):

  The Packages tab also supports a personal npm watchlist
  (`?pkgs=hono,zod` — saved in the browser, shareable).

```html
<iframe src="https://zalize-com.github.io/trendscope/embed.html" width="400" height="520" frameborder="0"></iframe>
```

## Quick start

```bash
curl -s https://raw.githubusercontent.com/zalize-com/trendscope/main/data/latest.json | jq .
```

## Use cases

- Trend research: what is the dev community paying attention to this week?
- Velocity signals: which repos/packages are gaining attention *fastest*?
- Benchmarks & journalism: a citable, timestamped record of dev attention.

## Data dictionary

See [`docs/data-dictionary.md`](docs/data-dictionary.md). Schema:
`source, rank, title, url, score, metric, comments, author, tags, captured_at`.

## Provenance & compliance

- Only public, login-free endpoints; ~1 req/s or less per source; no anti-bot circumvention.
- Titles/links/scores only — no personal data beyond public author handles.
- CC0 for our compilation; upstream content rights remain with their owners.

## Run it yourself

```bash
python3 scripts/collect.py            # stdlib only, no dependencies
GITHUB_TOKEN=... python3 scripts/collect.py   # optional: higher GitHub API limits
```

Then serve the dashboard statically from the repo root (e.g. `python3 -m http.server`)
and open `index.html`.

## Attribution

Free to use, share and build on — including commercially. When you publish or
redistribute, please credit **trendscope** with a link back to
<https://github.com/zalize-com/trendscope> or the dashboard:

```text
trendscope developer attention dataset, https://zalize-com.github.io/trendscope/
```

## Roadmap & paid tier (owner activates)

- Cleaned long-range history + per-topic slices → dataset listing on
  [data.zalize.com](https://data.zalize.com) (link TBD)
- Weekly digest archives under `docs/digest/` → subscription-ready content
- GitHub Sponsors → enable on the account and this repo
- README sponsor slot below → TBD
