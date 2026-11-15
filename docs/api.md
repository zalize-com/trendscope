# trendscope data API

Everything is static files in this repo — no key, no rate limit, CC0.
Fetch straight from GitHub raw or the Pages site (`/trendscope/…`).

| Endpoint | Format | Contents |
|---|---|---|
| `data/latest.json` | JSON | Most recent full snapshot: `items` per source, `topics`, `total_items` |
| `data/latest.csv` | CSV | Same snapshot as flat rows |
| `data/history.csv` | CSV | Append-only cumulative history — every item × every day (velocity analysis) |
| `data/index.json` | JSON | `{"snapshots": ["2026-11-07", …]}` — list of available daily archives |
| `data/daily/YYYY-MM-DD.json` | JSON | Per-day archive (full `items` + `topics`) |
| `data/daily/YYYY-MM-DD.csv` | CSV | Per-day archive, flat |
| `data/health.json` | JSON | Per-source run health `{ok, items, ms}` |
| `data/health-log.csv` | CSV | Daily `date,source,ok,items,ms` health history |
| `data/topics-history.csv` | CSV | Append-only per-day topic counts — time-series |
| `docs/api/movers-latest.json` | JSON | Entered/left/gainers/droppers + package rank movers for the latest day pair |
| `docs/index.json` | JSON | Index of `docs/digest/` weekly digests and `docs/movers/` reports |
| `feed.xml` | RSS | Daily snapshots + movers + digests as feed items |

Schema for item rows: `source, rank, title, url, score, metric, comments, author, tags, captured_at` — see [data-dictionary.md](data-dictionary.md).

Example (Python, stdlib):

```python
import json, urllib.request
snap = json.load(urllib.request.urlopen(
    "https://zalize-com.github.io/trendscope/data/latest.json"))
print(snap["date"], snap["total_items"])
```

Attribution is welcome but not required — CC0.
