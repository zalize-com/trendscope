# Dataset changelog

Pipeline and dataset milestones, newest first. Data consumers: subscribe
via [feed.xml](../feed.xml) or watch this file.

## 2026-11-15 (day one — everything)

### Sources (15 total)
- Core 8 at launch: hackernews, show_hn, ask_hn, lobsters, devto,
  github_trending, npm, pypi (+ crates watchlist)
- Added same-day: producthunt, techmeme, slashdot, arstechnica,
  theverge, arxiv (Atom/RSS feed-rank sources)

### Long-history datasets
- `data/hn-canon-monthly.csv` — top-10 front-page stories/month,
  Feb 2007 → today (2,380 rows)
- `data/show-hn-monthly.csv` — top-10 launches/month, Jan 2012 →
  today (1,790 rows)
- `data/ask-hn-monthly.csv` — top-10 questions/month, Feb 2007 →
  today (2,378 rows)
- `data/hiring-monthly.csv` — who-is-hiring / seeking / freelancer
  threads, 2010 → today (528 rows, 3 kinds)
- `data/hiring-history.csv` — per-day comment counts for the
  current month's hiring threads
- `data/topics-history.csv` — per-day topic counts (deduped)

### API surface (`docs/api/`, refreshed daily)
- `movers-latest.json`, `week.json`, `ideas-latest.json`,
  `stats.json`, `health.json` + `history.csv`, `latest.json`

### Quality gates in CI
- `validate.py` — schema contracts for all CSVs, history.csv
  dedup, **HTML-entity residue audit on every title column**
  (born from 3 real double-encoding bugs: PH, Techmeme, The Verge)
- `linkcheck.py` — every page's internal links + sitemap coverage
- `stats.py` — regenerates badge endpoints

### Schema
- v1 record fields (unchanged since launch):
  source, rank, title, url, score, comments, tags, author,
  captured_at
