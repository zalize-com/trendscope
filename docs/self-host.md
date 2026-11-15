# Self-host your own trendscope

The whole pipeline is one stdlib-only Python script and a GitHub Actions
workflow. Fork this repo and you get your own cross-source attention
dataset in about two minutes:

1. **Fork** → Settings → Pages → Deploy from branch → `main` / root.
2. **The workflow is already enabled** — it runs twice daily at 06:05 and 18:05 UTC and
   commits `data/` back to your fork. First run: Actions → "Run workflow".
3. **Edit the watchlists** in `scripts/collect.py` — `NPM_WATCHLIST` and
   `PYPI_WATCHLIST` pick the packages, `TOPIC_RULES` re-labels the topic
   buckets, and the source functions at the bottom decide what you track
   (drop a source = delete its entry; ask_hn's 48h window is in
   `fetch_ask_hn`).

That's it. No secrets, no pip installs, no servers. Your data accumulates
in `data/history.csv` — the whole site runs off static files.

## Want your own analysis pages?

Every page under the repo root (`canon.html`, `hiring.html`, ...) is
plain HTML+JS reading the CSVs client-side. Copy a page, point it at
your data, commit. If you build something interesting, add yourself to
the README's "Built on this dataset" section.

## What you get for free

- `scripts/validate.py` — CI contract checks (schema, empty sources,
  title entity residue, duplicate history rows).
- `scripts/backfill.py` — refill HN history for arbitrary past days via
  Algolia `numericFilters`.
- `feed.xml` + `feed.json` — your dataset is subscribable out of the box.
- `llms.txt` + `robots.txt` — AI-search-ready by default.

## Fork etiquette

The upstream data is CC0 — do what you like. If your fork tracks a
different niche (games, design, biotech), tell us — we'd love to link it.
