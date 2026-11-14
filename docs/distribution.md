# Distribution playbook

Launch assets for trendscope. Everything below is copy-paste ready; the owner
posts from their own accounts (Devin sessions can't create accounts).

## Show HN draft

**Title:** Show HN: trendscope – a daily open dataset of what developers are
reading and building

**Body:**
> I wanted yesterday's HN, GitHub trending, Lobsters, dev.to and package
> download charts in one place — and, more importantly, *downloadable*. Every
> day a GitHub Action snapshots all seven sources into a normalized dataset
> (CC0) committed back to the repo. The dashboard is just the storefront;
> `data/latest.json` and `data/history.csv` are the product.
>
> No signup, no tracking, no accounts — stdlib-only Python, ~150 lines of JS.
> Velocity board ("biggest movers") lights up once two days of history exist.
>
> Feedback wanted on: schema (data-dictionary.md), which sources to add, and
> whether a weekly digest is worth email-subscribing to.

Post Tuesday–Thursday ~14:00 UTC for best visibility. First comment: link to
the dashboard + `data/history.csv`.

## Badge

```markdown
[![trendscope snapshot](https://img.shields.io/badge/trendscope-daily%20snapshot-58a6ff)](https://zalize-com.github.io/trendscope/)
```

## Submission targets (in order of fit)

| Target | What to submit | Effort |
|---|---|---|
| `awesome-public-datasets` (wookat maintains related lists) | the dataset (`data/` layout + dictionary) | PR, 10 min |
| `awesome-json-datasets` | `latest.json` endpoint | PR, 10 min |
| r/datasets (owner's account) | dataset + dashboard | post |
| Lobste.rs | project link, tagged `data`/`show` | post |
| dev.to | short write-up "we built an open dev-attention dataset" | article |
| HN daily thread / Show HN | draft above | post |
| Product Hunt | after 1 week of history + weekly digest live | launch |
| Kaggle datasets | weekly CSV mirror of history.csv | upload (owner acct) |

## Site cross-links (owner's existing properties)

- `data.zalize.com` dataset card → trendscope (free tier showcase)
- zalize tool sites' footers → "more free tools" ring (snapmark/shelfmark/
  prompter/namechart/seatmark pattern)

## Metrics to watch (no analytics needed)

- GitHub stars/forks/traffic graph on the repo
- `data/index.json` growth (self-verifying freshness)
- Referrer mentions via GitHub "Used by" and inbound links
