# Free feed-proxy survey — 2026-11-16

Why: both rescue lanes (rss2json, feed2json) are rate-limited *by caller IP*,
so when Actions egress burns the daily quota the whole rescue layer goes dark.
Surveyed candidates for a third channel. Tested against three sample feeds:
reddit `.rss` (hostile endpoint), a Substack feed, a normal blog.

## Verdict first

**No free, keyless, burst-friendly third channel exists.** The viable spare
is `api.cors.lol` (raw-proxy, returns untouched feed bytes we parse ourselves)
— but it rate-limits hard (~429 after 1–2 rapid calls), so it's a trickle
lane at ~1 req / several seconds, not a rescue lane. The architecture that
already shipped (persistent-gating + per-run budget + priority scheduling)
remains the right answer: free proxies are a budget, not a pipe.

## Results

| endpoint | format | reddit | substack | blog | yt atom | limit observed | score |
|---|---|---|---|---|---|---|---|
| `api.rss2json.com/v1/api.json?rss_url=` | JSON items | ✓ (proxy-verified) | ✓ | ✓ | ✓ | daily quota (~150+ calls/day), 429 all at once | **primary** |
| `feed2json.org/convert?url=` | JSON Feed | ✓ 25 items | — | ✓ 20 | ✓ 15 | 429 after ~5–15 calls; some feeds 500 | secondary (shipped) |
| `api.cors.lol/?url=` | **raw bytes** | ✓ 62KB XML | 429 | 429 | — | ~1 fast call then 429; unknown window | trickle spare |
| `api.allorigins.win/raw?url=` | **raw bytes** | ✓ 62KB XML | timeout | timeout | ✓ XML | flaky (intermittent 000) | flaky spare |
| `feedrapp.info/?q=` | JSON | 400 can't parse .rss | — | — | — | parses only simple feeds | unusable |
| `openrss.org/<site>` | feed generator | 503 | — | — | — | overloaded + wrong tool (site→feed, not proxy) | unusable |
| `rss-to-json-serverless-api.vercel.app` | JSON | 402 quota | — | — | — | quota dead | dead |
| `api.factmaven.com/xml-to-json` | JSON | 000 | — | — | — | unreachable | dead |
| `rss.as`, `morphss.com`, `proxy.cors.sh`, `api.codetabs.com/v1/proxy` | — | 000/000/000/000 | — | — | — | all dead | dead |
| `corsproxy.io`, `cors.eu.org`, `test.cors.workers.dev` | raw | 401/429/429 | — | — | — | key or insta-limit | unusable |
| `rsshub.app` + public mirrors | feed generator | 403/503/404 | — | — | — | public instances abused | unusable |

## Field-mapping notes (if ever wired)

- `api.cors.lol/?url=<quoted>` returns the raw upstream response — pass through
  the existing `_feed_root` parser, no new schema. Throttle to ~1 req/5s.
- `api.allorigins.win/raw?url=<quoted>` same shape, but ~30% timeouts observed.
- `feedrapp` uses `?q=` not `?url=` and fails on Reddit's `.rss` anyway.

## Lesson (methodology 42 candidate)

Free proxies share one pool: caller-IP quota. Adding channels multiplies
complexity, not capacity — capacity comes from spending the quota only on
sources that cannot self-heal (persistent_empty gating).
