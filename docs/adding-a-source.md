# Adding a source

Two paths — pick the data-driven one whenever the source is a plain RSS/Atom
feed:

## Path A — data-driven (preferred for feeds)

Drop a line into any `scripts/feeds_*.json` file:

```json
"example": ["Example Blog", "https://example.com/feed", "https://example.com"]
```

`{key: [label, feed_url, home]}`. `_extra_feed_fetchers()` globs
`scripts/feeds_*.json` and registers each entry through
`_make_feed_fetcher` — no Python code needed. `gen_sources_md.py` and
`gen_opml.py` read the same files. Check for key AND feed-URL duplicates
against existing pools first (a source may already exist under another lane).

## Path B — custom fetcher (non-feed endpoints)

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
| `scripts/collect.py` | add fetcher to `fetchers` dict in `main()` — **careful**: defs go before `def main()`, never between its lines; then smoke-run `python3 -u scripts/collect.py` and confirm the first `Fetching …` lines appear |
| `index.html` | add tab to `TABS` (only for sources that deserve their own tab) |
| `docs/data-dictionary.md` | add source to the `source` enum |
| `data/sources.json` | regenerate (`scripts/gen_sources_md.py` emits it) — about.html's directory reads it |
| `docs/SOURCES.md` | regenerate — it's the canonical registry |

## 3. Test

```bash
python3 -c "import sys; sys.path.insert(0,'scripts')
import collect; print(len(collect.fetch_example()))"
python3 scripts/collect.py   # full run — writes data/ locally
```

Then open `index.html` (served from the repo root) and check the tab, rows,
Δ badges, and the topics classifier (`TOPIC_RULES` in collect.py) still
bucket sensibly.

## 4. Feed probe pitfalls (batch harvesting)

When probing pools of candidate feeds, check the failure mode before writing
a source off (see `docs/methodology.md` 19-21, 25-26, 29-32):

- **HTTP status semantics vary by site** — a blanket 404 on `feeds/videos.xml`
  is YouTube's IP rate-limit (self-heals ~hours), not a dead channel; 429 is
  transient everywhere; 000 (connect timeout) may be *your* egress blocking an
  AS range (whole DreamHost subnets went dark from one of our VMs while GitHub
  Actions fetched the same hosts fine — compare against the previous Actions
  snapshot before declaring death).
- **308s must be followed** — urllib's default redirect handler ignores 308;
  our global `_Redirect308` covers `urlopen`, but standalone probes should
  also chase it (`curl -L`). If a stored URL answers 308, prefer updating the
  stored URL to the final location.
- **Subscribe landing pages are not feeds** — a 200 on a newsletter's SPA
  subscribe page says nothing; sniff `<link rel="alternate">` or well-known
  paths (`/feed`, `/rss`, `/atom.xml`) for the real endpoint. For Substack,
  `{slug}.substack.com/feed` ≠ `substack.com/@handle` — resolve the handle
  page's link-alternate instead of guessing.
- **Truncated / zero-entry / malformed XML all have separate diagnoses** —
  >300KB CDN truncation breaks mid-document (take the head or flag manual);
  200 + zero entries → look for `<link rel="self">` / meta-refresh / moved
  paths; parse failures → BOM-whitespace → entity-escape → regex extraction,
  in that order.

## 5. Entity audit (RSS/Atom sources)

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

Merging a source automatically re-runs the collection workflow on push, so the
first snapshot lands within minutes — no need to wait for the cron.
