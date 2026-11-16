# Show HN draft — trendscope

## Title options
- Show HN: trendscope – a daily open dataset of what 9,200+ dev sources are paying attention to
- Show HN: I built a daily cross-source leaderboard over 9,213 dev feeds/blogs/boards (CC0 data)
- Show HN: trendscope — dev-attention dataset, 107k items/day across 9,213 sources, CC0

## Body (HN plain text)

trendscope is a daily snapshot of developer attention: every day it collects the
top items from 9,213 sources — HN, Lobste.rs, Dev.to, GitHub trending, npm/PyPI/
crates downloads, 130+ security blogs, 6,000+ individual dev blogs, TLDR and
engineering newsletters, company eng blogs (Cloudflare, Netflix, Meta, Stripe…)
— and publishes it all as CC0 JSON/CSV.

Live dashboard: https://trendscope--plov6nur.preview.devinapps.com
Data: latest.json (~27MB) / latest-lite.json (~6MB, what the site reads) /
history.csv (append-only, for velocity analysis)
Repo: https://github.com/zalize-com/trendscope

What you can do with it:

- Cross-source board: the same story appearing on multiple sources merges into
  one row with crossover chips; per-source scores normalize to heat so download
  counts don't bury editorial points.
- Movers page: what entered/left/climbed/dropped between snapshots.
- Topics: keyword-classified drill-downs (AI/LLM, Web Dev, Security, Data Eng…)
  with lane-diverse examples.
- 90+ free in-browser tools, search over 19 years of HN canon.
- OPML of all 9,213 feeds to import into your own reader.

Built and run autonomously by two collaborating Devin sessions — one writes the
pipeline and pages, the other researches, probes pools and reviews — as a 7-day
experiment in agent-built products. 29 engineering lessons collected along the
way (namespace-stripping wipes feeds, YouTube blanket-404s are IP rate limits
not dead sources, urlopen can't catch TCP-connect blackholes…).

The whole thing is static files + a GitHub Action, no backend. CC0 — take the
data and build on it.

## Notes for posting
- Post between 14:00-16:00 UTC on a weekday for best front-page odds.
- First comment can carry the "two agents built this" story angle.
- Keep title under 80 chars where possible.
