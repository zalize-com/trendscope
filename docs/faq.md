# FAQ — the developer attention dataset

## Where does the data come from?
Public, login-free endpoints only: HN Algolia API, GitHub Trending (HTML),
Lobste.rs/dev.to/ProductHunt/Ars/Verge/Slashdot feeds, npm/PyPI/crates
download APIs, arXiv listings. ~1 request/sec or less per source, once a
day via GitHub Actions. No API keys, no scraping of gated content.

## Can I use it commercially?
The compilation is CC0 — do anything. Upstream titles/links/scores remain
with their owners. If you cite it, a link back to the repo or the dataset
page is appreciated but not required.

## How fresh is the data?
`data/latest.json` regenerates twice daily (06:05 and 18:05 UTC). `data/history.csv`
is append-only and never rewritten — safe to build on.

## What's the difference between daily/, history.csv and the long-history CSVs?
- `daily/YYYY-MM-DD.json` — full snapshot for one day, all 22 sources.
- `history.csv` — the same rows, append-only, for velocity analysis.
- `hn-canon-monthly.csv` / `show-hn-monthly.csv` / `ask-hn-monthly.csv` —
  monthly top-10 canon backfills (2007-02 / 2012-01 / 2007-02 → today).
- `hiring-monthly.csv` — 15 years of monthly HN hiring threads
  (hiring / seeking / freelancer kinds).

## Something looks wrong — who do I tell?
[Open an issue](https://github.com/zalize-com/trendscope/issues/new).
Every new source goes through the entity audit in
`docs/adding-a-source.md`; CI checks schema drift, empty sources and
title entity residue on every run.

## Who maintains it?
Two autonomous Devin sessions in relay — `docs/methodology.md` explains
the split. A human maintains the repos.

## Can I run my own copy of this pipeline?

Yes — the whole collector + dashboard is forkable. See [docs/self-host.md](self-host.md): fork, enable Pages, edit the watchlists.
