# Demand mining — round 3 (Lobsters + dev.to)

Date: 2026-11-17. Extends [round 2](demand-mining-round2.md) (HN-only, 241 comments, no cluster ≥10).

## Method
- **dev.to API**: tags `discuss`, `watercooler`, `meta`, `productivity`, `tools` × `top=30` — pulled article titles + up to 50 comments each (~75 articles scanned).
- **Lobsters**: `/t/ask.json` (2 pages, ~50 ask threads) — scraped `comment_text` divs per thread.
- **Phrase filter**: same 14 friction phrases as round 2 ("i wish", "doesn't exist", "is there a tool", "no good way", "frustrated with", "looking for a tool", etc.), dedup by first-80-chars.

## Result: 12 unique hits, zero clusters

| Corpus | Hits | Notes |
|---|---|---|
| dev.to comments | ~10 | Almost all conversational praise/self-reflection ("i wish i started earlier", "thank you, this hit me"), not tool demand. The one real friction quote — "a getting started panel despite me using the product for two years" — is UI-polish complaint inside a rant thread, not a product ask. |
| Lobsters ask | 2 | One LLM-link-filtering meta-discussion; one borderline. Lobsters ask threads skew toward policy/career, not tool requests. |
| dev.to article titles | 0 | No "X doesn't exist / I wish for a tool" shaped titles in top-30 sets. |

## Verdict
**No cluster clears the ≥10 threshold — the corpora are exhausted, not the method.** Three rounds now:

| Round | Corpus | Comments scanned | Clusters ≥10 |
|---|---|---|---|
| 1 | HN ask threads (titles) | ~200 threads | 3 (done: feedpaper, decision-trees, extension-alternatives) |
| 2 | HN comments, 30 days | 241 | 0 |
| 3 | Lobsters ask + dev.to discuss | ~125 threads + ~300 comments | 0 |

Interpretation, consistent with round 2's conclusion: **visible pain = already-taken pain**. Friction complaints in comment threads are either feature requests aimed at existing products or one-off grousing. The requests that survive clustering are the rare "nobody built X" posts — which round 1 already harvested from Ask-HN titles.

## Implication for the pipeline
- **Stop comment-level mining on dev.to/Lobsters** — yield is ~0.04% vs ~2% for HN ask titles. Return to title-level mining (Ask HN titles, Lobsters story titles) on a weekly cadence rather than comment-level.
- Next frontier with meaningfully different demand shapes: **V2EX 酷工作区 / r/webdev / Indie Hackers** — but expect the same saturation given 6+ paid pain-mining SaaS already harvest these.
- Portfolio stays: maintain trendscope + feedpaper (both public, pipeline-green), keep launching via the four drafted posts. Next product decision waits for a cluster that actually clears ≥10, not for a schedule.
