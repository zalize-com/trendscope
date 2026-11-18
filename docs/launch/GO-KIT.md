# GO kit — everything paste-ready (owner posts, Devin monitors)

Baseline @ 2026-11-18 14:17 UTC: trendscope 0★/0 forks · feedpaper private ·
sites 200 · latest.json 09:12Z · persistent-empty 148 · IndexNow 81 urls 202'd.

---

## 1. Show HN — news.ycombinator.com/submit (account: yours)

**Title** (79 chars):
```
Show HN: trendscope – daily open dataset of what 9,200+ dev sources are reading
```

**Text** (paste into `text` field):
```
trendscope is a daily snapshot of developer attention: every day it collects the top items from 9,213 sources — HN, Lobste.rs, Dev.to, GitHub trending, npm/PyPI/crates downloads, 130+ security blogs, ~6,000 individual dev blogs, TLDR and engineering newsletters, company eng blogs (Cloudflare, Netflix, Meta, Stripe) — and publishes it all as CC0 JSON/CSV.

Live dashboard: https://trendscope.zalize.com
Data: latest.json (~27MB) / latest-lite.json (~6MB, what the site reads) / history.csv (append-only, for velocity analysis)
Repo: https://github.com/zalize-com/trendscope

What you can do with it:

- Cross-source board: the same story appearing on multiple sources merges into one row with crossover chips; per-source scores normalize to heat so download counts don't bury editorial points.
- Movers page: what entered/left/climbed/dropped between snapshots.
- Topics: keyword-classified drill-downs (AI/LLM, Web Dev, Security, Data Eng…) with lane-diverse examples.
- 90+ free in-browser tools, search over 19 years of HN canon.
- OPML of all 9,202 feeds to import into your own reader.

Built and run autonomously by two collaborating Devin sessions — one writes the pipeline and pages, the other researches, probes pools and reviews — as a 7-day experiment in agent-built products. 41 engineering lessons collected along the way (namespace-stripping wipes feeds, YouTube blanket-404s are IP rate limits not dead sources, urllib silently misses 308s that CDNs love, urlopen can't catch TCP-connect blackholes…).

The dataset already proved itself on its own data: today's front page ran "Old Bitly links are being hijacked" and "Preserving 30 years of Salon journalism" side by side — the dataset caught that link-rot cluster from 5 independent sources before anyone called it a trend. Cross-source corroboration is the point.

The whole thing is static files + a GitHub Action, no backend. CC0 — take the data and build on it.
```

**First comment** (post it yourself right after submitting):
```
Two-agent build report: session A owns the fetch pipeline + pages, session B researches source pools (9,213 sources were screened from ~40k candidates), reviews every change, and writes the docs. Every claim in the post is reproducible from the repo — data/, docs/methodology.md has all 41 lessons.

Dataset entry points:
- https://github.com/zalize-com/trendscope/blob/main/data/latest.json
- https://github.com/zalize-com/trendscope/blob/main/data/history.csv
- OPML: https://github.com/zalize-com/trendscope/blob/main/trendscope.opml (9,202 feeds)

Honest caveat: ~150 sources are currently flagged persistent-empty — we publish the health telemetry itself (data/zerowatch.json) rather than hide it. Most are rate-limit waves, not dead sites; we only call a source dead after 3 consecutive empty snapshots.

Feedback wanted: schema shape, missing source lanes, and whether a weekly digest email is worth building.
```

---

## 2. dev.to — new post (draft #1, the product intro)

Dashboard → Write a post → paste `docs/launch/devto-draft.md` body (front-matter
already has title/tags; set `published: true`). Canonical is already the repo —
fine as-is.

**First comment** (post after publish):
```
Data-first links: the cross-source health census → https://trendscope.zalize.com/state-of-rss · append-only history.csv for your own velocity analysis → https://github.com/zalize-com/trendscope/blob/main/data/history.csv · full OPML (9,202 feeds) → https://github.com/zalize-com/trendscope/blob/main/trendscope.opml
```

---

## 3. Lobste.rs — lobste.rs/stories/new (account: yours)

```
URL: https://trendscope.zalize.com
Title: trendscope — daily open dataset of developer attention (9,213 sources, CC0)
Tags: data show
Description: Daily snapshot of the top items across 9,213 dev sources — HN, Lobste.rs, Dev.to, GitHub trending, package registries, ~6,000 blogs — published as CC0 JSON/CSV with per-source health telemetry. Static site + one GitHub Action.
```

## 4. r/datasets — reddit.com/r/datasets/submit

```
Title: [Data] trendscope — daily snapshots of what 9,200+ developer sources are paying attention to (CC0, JSON+CSV)
Link: https://github.com/zalize-com/trendscope
Body (text post):
Daily cross-source snapshot of developer attention — 9,213 sources (HN, Lobste.rs, Dev.to, GitHub Trending, npm/PyPI/crates, 130+ security blogs, ~6,000 dev blogs, newsletters). Every record carries source, rank, title, canonical URL, normalized score, comments, tags, author, capture timestamp.

- latest.json — full snapshot (~27MB, regenerated daily)
- history.csv — append-only cumulative history for velocity analysis
- data/daily/*.json.gz — daily archives
- feeds.json + zerowatch.json — the 9,202-feed registry with per-source health telemetry
- dedup.json — SimHash near-duplicate story clusters across sources

License: CC0. No auth, no rate limits — it's a GitHub repo. Dashboard: https://trendscope.zalize.com
```

## 5. awesome-public-datasets — contributes via awesomedata/apd-core

Their README is generated; entries are YAML in apd-core. I can't fork external
repos with my integration, so this one needs your GitHub:

1. Open https://github.com/awesomedata/apd-core → Fork.
2. In YOUR fork, create file `core/Software/trendscope-developer-attention-dataset.yml`
   — content ready at our repo: `docs/launch/apd-entry.yml` (copy it).
3. Open PR to `awesomedata/apd-core`, title: `Add trendscope developer attention dataset (Software)`.

---

## After you post — tell me the URLs

I monitor HN rank/points every ~15min, draft suggested replies to comments,
backfill URLs into distribution.md, and snapshot day-1 metrics vs this baseline.
