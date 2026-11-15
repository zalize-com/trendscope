# Adding a source

A source = one function in `scripts/collect.py` + wiring in four places.

## 1. Write the fetcher

```python
def fetch_example() -> list[dict]:
    """Return up to ~20 items."""
    data = get_json("https://example.com/api/hot")   # or fetch() for HTML
    items = []
    for i, hit in enumerate(data["hits"][:20]):
        items.append(item(
            source="example",
            rank=i + 1,
            title=hit["title"],
            url=hit["url"],
            score=hit.get("points", 0),
            metric="points",            # human label shown on the board
            comments=hit.get("num_comments"),
            author=hit.get("author"),
            tags=hit.get("tags") or [],
        ))
    return items
```

Rules we follow:

- **Keyless public endpoints only** — no auth, no cookies.
- Polite: `UA` header is already set in `fetch()`; stay ≤ ~1 req/s.
- If the source gives no votes, use **position scoring**
  (`score = len(entries) - i`, `metric="feed rank"`) — see `fetch_techmeme`.
- If the score is a rolling window (weekly/monthly downloads), add the source
  to `ROLLING` in `scripts/movers.py` so rank deltas are used instead.
- Prefer provenance: keep the canonical `url`; strip tracking params.

## 2. Wire it in

| File | Change |
|---|---|
| `scripts/collect.py` | add fetcher to `fetchers` dict in `main()` |
| `index.html` | add tab to `TABS` |
| `docs/data-dictionary.md` | add source to the `source` enum |
| `about.html` | add row to the sources table |
| `README.md` | update the sources list |

## 3. Test

```bash
python3 -c "import sys; sys.path.insert(0,'scripts')
import collect; print(len(collect.fetch_example()))"
python3 scripts/collect.py   # full run — writes data/ locally
```

Then open `index.html` (served from the repo root) and check the tab, rows,
Δ badges, and the topics classifier (`TOPIC_RULES` in collect.py) still
bucket sensibly.

## 4. Entity audit (RSS/Atom sources)

Every new feed source has produced one real encoding bug — check before
calling it done:

- **double-encoded entities** in titles/summaries (`&#8217;`, `&amp;lt;`)
  — run `html.unescape()` on the raw text, not the stripped text
- **HTML truncation mid-entity** — unescape first, then `[:200]` slice
- **junk entries** — feeds may keep deleted/housekeeping items
  (Product Hunt ships `-deleted-NNNN` slugs); filter by URL pattern
- **nested CDATA** — `findtext` returns it verbatim; strip tags after
- **author hidden in description prefix** — some feeds prefix the author in
  the summary (`X / Y :`), not a field (Techmeme); extract it or
  `authors.html` can't see the source's writers

Merging a source automatically re-runs the daily workflow on push, so the
first snapshot lands within minutes — no need to wait for the cron.
