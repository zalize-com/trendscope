# trendscope data dictionary

One row per captured item. Present in `data/latest.json`, `data/daily/*.json/.csv`
and `data/history.csv` (CSV joins `tags` with `|`).

`data/daily/YYYY-MM-DD.json` is the complete daily archive:
`{date, generated_at, sources, items, top_scores, topics}` where `items` is the
full per-source item lists and `top_scores` is a compact top-10 summary kept for
backward compatibility.

| Field | Type | Description |
|---|---|---|
| `source` | string | `hackernews`, `show_hn`, `ask_hn`, `github_trending`, `lobsters`, `devto`, `producthunt`, `techmeme`, `slashdot`, `arstechnica`, `theverge`, `arxiv`, `npm`, `pypi`, `crates`, `lemmy`, `krebs`, `changelog`, `freecodecamp`, `echojs`, `infoq`, `theregister`, `lwn`, `hackaday`, `thenewstack`, `opensourcecom`, `soblog`, `codinghorror`, `martinfowler`, `pragmatic`, `bendersky`, `cheney`, `lucumr`, `hynek`, `susam`, `haxx`, `jvns`, `wingolog`, `philopp`, `sanglard`, `antirez`, `beesbuzz`, `gargron`, `overreacted`, `swizec`, `kentcdodds`, `cloudflare`, `netflix`, `github_eng`, `slack_eng`, `aws_blog`, `dropbox`, `lyft`, `pinterest`, `etsy`, `discord`, `stripe`, `vercel`, `meta_eng`, `airbnb`, `mongodb`, `elastic`, `gitlab_blog`, `aphyr`, `thisweek`, `pythonblog`, `rands`, `catonmat`, `dabeaz`, `mitchw`, `birklund`, `simonw`, `daringfireball`, `marco`, `danluu`, `stratechery`, `baeldung`, `troyhunt`, `tonsky`, `joelonsoftware`, `raphlinus`, `xeiaso`, `jetbrains`, `tedinski`, `drmaciver`, `matklad`, `grumpyg`, `chriskiehl`, `dimitri`, `hillel`, `ridiculousfish`, `nadia`, `henrikwarne`, `charity`, `surfingcomplexity`, `lorinhochstein`, `geshan`, `mtlynch`, `nelhage`, `schneems`, `lcamtuf`, `copyconstruct`, `verdagon`, `bitbashing`, `ntietz`, `murat`, `begriffs`, `gds`, `bitslog`, `roytang`, `tbray`, `bertrand`, `bret`, `codemadness` |
| `rank` | int | Rank within that source for that day (1-based) |
| `title` | string | Story title, or `owner/name` for repos, package name for registries |
| `url` | string | Canonical link (provenance) |
| `score` | int | Source-native score: HN points, GitHub stars, Lobsters score, Dev.to reactions, npm weekly downloads, PyPI monthly downloads, crates recent downloads |
| `metric` | string | Human-readable unit of `score` (`points`, `stars`, `reactions`, `weekly downloads`, `monthly downloads`, `recent downloads`, `score`) |
| `comments` | int | Comment count (0 when the source doesn't expose one) |
| `author` | string \| null | Public author handle / repo owner |
| `tags` | list&lt;string&gt; | Source tags, repo language, or crate keywords |
| `captured_at` | string | ISO 8601 UTC timestamp of the collection run |

Extra fields per source (JSON only): `description`, `forks`, `created_at` for
GitHub; `author` for others.

## Topics

`latest.json → topics` counts keyword-classified items across all sources
(`AI/LLM`, `Web Dev`, `DevOps/Infra`, `Security`, `Data Eng`, `Languages`,
`Tools/OSS`, `Career/Business`). `total_score` mixes units — use `count` for
ranking.

## Caveats

- Scores are **not comparable across sources** (points ≠ downloads).
- npm/PyPI entries cover a fixed watchlist (see `scripts/collect.py`), not the
  whole registry.
- GitHub section = repos **created in the last 7 days** sorted by total stars
  (via the Search API), not the official trending page — it's "hot new repos".
- Hacker News `tags` exclude Algolia bookkeeping tokens (`author_*`, `story_*`).

## Auxiliary files

- `data/health.json` — per-source run health `{ok, items, ms}` for the latest
  collection; `data/health-log.csv` appends `date,source,ok,items,ms` twice daily.
- `data/topics-history.csv` — append-only `date,topic,count,total_score` per day.
- `docs/api/movers-latest.json` — structured entered/left/gainers/droppers and
  package rank movers for the latest snapshot pair (same computation as
  `docs/movers/*.md`).
- `data/hiring.json` / `data/hiring-history.csv` — monthly HN "Who is hiring?"
  and "Who wants to be hired?" thread comment counts, tracked twice daily
  (`captured_at,kind,thread_id,month,comments,url`); a labor-demand signal.
- `data/hiring-monthly.csv` — full backfill: every canonical monthly thread
  Algolia indexes (2010 → today), `month,kind,comments,thread_id,url,created`;
  regenerate with `scripts/hiring_backfill.py`.
- `data/hn-canon-monthly.csv` — the HN canon: top-10 front-page stories per
  month, Feb 2007 (launch) → today
  (`month,rank,title,url,points,comments,author,id,hn_url`);
  regenerate with `scripts/canon_backfill.py`.
- `data/show-hn-monthly.csv` — the Show HN canon: top-10 product launches per
  month, Jan 2012 → today (same schema); regenerate with
  `scripts/showhn_backfill.py`.
- `data/ask-hn-monthly.csv` — the Ask/Tell HN canon: top-10 questions per
  month, Feb 2007 → today (same schema); regenerate with
  `scripts/askhn_backfill.py`.
