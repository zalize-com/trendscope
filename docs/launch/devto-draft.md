---
title: trendscope — a daily open dataset of what 9,213 dev sources are paying attention to
published: false
tags: webdev, opensource, data, news
---

Every day, thousands of dev sources publish — HN frontpage, Lobste.rs, Dev.to,
GitHub trending, npm/PyPI downloads, 130+ security blogs, ~6,000 individual dev
blogs, newsletters like TLDR and company eng blogs (Cloudflare, Netflix, Meta,
Stripe). Nobody aggregates the signal across all of them.

trendscope does. Every day it snapshots the top items from 9,213 sources and
publishes everything as CC0 JSON/CSV.

## What you get

- **Cross-source board** — the same story across sources merges into one row
  with crossover chips; per-source scores normalize to heat so npm download
  counts don't bury editorial points.
- **Movers** — what entered, left, climbed or dropped between snapshots.
- **Topics** — keyword-classified drill-downs (AI/LLM, Web Dev, Security…).
- **90+ free in-browser tools**, search over 19 years of HN canon, OPML export.

## The data

| file | size | what |
|---|---|---|
| `data/latest.json` | ~27MB | full snapshot, all items |
| `data/latest-lite.json` | ~6MB | top-3 per source (what the site reads) |
| `data/history.csv` | append-only | for velocity analysis |
| `data/daily/*.json.gz` | ~8MB/day | daily archives |

All under CC0 — take it, remix it, no attribution needed.

## Built by two agents

The whole project was built and run by two collaborating Devin sessions as a
7-day experiment in agent-built products: one writes the pipeline and the
pages, the other researches source pools, reviews changes and writes content.
35 engineering lessons collected along the way — namespace-stripping wipes
feeds, YouTube's blanket-404 is an IP rate limit not a dead source, `urlopen`
timeouts can't catch TCP-connect blackholes.

Static files + one GitHub Action, no backend.

- Live: https://trendscope--plov6nur.preview.devinapps.com
- Repo: https://github.com/zalize-com/trendscope
