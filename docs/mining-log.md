# Demand-signal mining log

Every two hours we sweep public communities for repeated demand
signals. A signal becomes a *cluster* when it recurs with different
wording within ~48h. Clusters feed tools, pages and weekly notes.

## Clusters (recurring)

| Cluster | First seen | Rounds | Product response |
|---|---|---|---|
| AI career anxiety (hollowed skills + code ownership) | 11/14 | 7, 9, 11, 16 | W47 notes section; geo.html |
| MCP ecosystem — fatigue → mature diversification | 11/14 | 6, 11, 14 | W46+W47 narrative correction |
| Own-your-data / self-hosting demand | 11/15 | 10, 13 | feedpaper positioning + dev.to #4 hook |
| GEO / AI-referral visibility | 11/15 | 9, 15 | tools/geo.html; llms.txt ×2 |
| Blog-impersonation anxiety | 11/15 | 10 | tools/web.html typosquat checker |
| Blind-SWE / a11y tooling | 11/15 | 9 | utils contrast checker + a11y.html suite |
| AI cost accounting (enterprise) | 11/15 | 12 | logged for future billing-observability tool |

## One-off signals worth noting

- "Ask HN: what tool do you wish existed" (46345827): simple embeddable
  widgets (comments/polls) — giscus occupies comments; polls open.
- IndexFast (Show HN) — "which of my pages do search engines index" —
  same family as GEO.
- Google search login-wall rumor (44pt) — SERP-scraping pipes break;
  machine-readability self-checks survive.
- V2EX: Claude Team resold-accounts discussion — gray market, not a
  product opportunity.
- lobste.rs /t/ai: weight-space programming 50pt — frontier research
  attention, not a demand.

## Method

Sources swept: HN front/ask/show (Algolia), lobste.rs hottest+newest+
tags, dev.to top7, V2EX hot, PH feed, StackExchange (quota-bound).
Rule: ≥2 independent phrasings of the same demand within 48h → cluster;
otherwise one-off. Every product-shaped response is annotated above.
