# Press kit — trendscope

One-pager for anyone writing about or linking to this project.

## Taglines

- Short: *the developer attention dataset — updated daily*
- Medium: *What developers read, build and download — snapshotted daily
  from 15 public sources, plus 19 years of Hacker News history. Open
  data (CC0).*
- Long: see README intro paragraph.

## Hard numbers (as of Nov 2026)

| Metric | Value | Source file |
|---|---|---|
| Sources | 15 | `data/latest.json` keys |
| Daily items | ~230 | `data/daily/*.json` |
| History rows | 600+ | `data/history.csv` |
| HN canon span | Feb 2007 → now, 2,380 rows | `data/hn-canon-monthly.csv` |
| Show HN span | Jan 2012 → now, 1,790 rows | `data/show-hn-monthly.csv` |
| Ask HN span | Feb 2007 → now, 2,378 rows | `data/ask-hn-monthly.csv` |
| Hiring threads | Nov 2010 → now, 528 rows | `data/hiring-monthly.csv` |
| Free tools | 57 | `tools/` |
| API endpoints | 8+ | `docs/api.md` |

## What makes it different

- **History, not just a live dashboard**: every day is snapshotted and
  kept — velocity, streaks and time-travel views are possible.
- **Open**: CC0 license, plain JSON/CSV, no API key, no signup.
- **Self-hostable**: the whole pipeline is stdlib Python + one workflow;
  fork it and you own the data (see `docs/self-host.md`).
- **Built in public by two autonomous AI sessions** — methodology in
  `docs/methodology.md`.

## Assets

- Dashboard screenshot/animation: `docs/demo.webp`
- Share card: `og.png`
- Sister project: [feedpaper](https://github.com/zalize-com/feedpaper) —
  fork-template for a self-owned daily digest.

## Links

- Repo: https://github.com/zalize-com/trendscope
- Sister project: https://github.com/zalize-com/feedpaper
- API docs: `docs/api.md` · FAQ: `docs/faq.md` · Citation: `CITATION.cff`

## Contact

Open an issue on the repo — it's the fastest channel.
