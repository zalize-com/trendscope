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

## dev.to article draft

**Title:** We open-sourced the "what are developers reading" question — a dataset updated daily by a GitHub Action

**Tags:** showdev, data, opensource, webdev

**Body:**

Most of us check the same five places every morning: Hacker News, GitHub
trending, Lobsters, dev.to, and the package charts. The numbers are all
public — but nobody keeps them. Every "trending" page is ephemeral: yesterday
is gone.

So we built [trendscope](https://github.com/zalize-com/trendscope): a tiny
pipeline that snapshots all seven sources every day and commits the result
back to the repo as a normal file.

The interesting part isn't the dashboard — it's that **the data is the
product**:

- `data/daily/YYYY-MM-DD.json` — every edition, forever
- `data/history.csv` — append-only, built for "what's rising this week" queries
- `data/latest.json` — stable URL, embed it anywhere
- CC0 license. Do whatever you want with it.

### What's in it already

Three things we noticed in week one (full notes in
`docs/digest/2026-W46-notes.md`):

1. **The privacy backlash is compounding** — EFF's "shifting the concept of
   privacy" post and the Lovable leak exposé hit HN's top-4 the same week.
2. **MCP fatigue has started** — dev.to's most-discussed post was "MCP Is
   Dead Simple. And That's Exactly the Problem." Expect MCP *tooling* to be
   the next wave of hot repos, not more servers.
3. **The attention economy runs on build tooling** — npm's top-4 (zod,
   typescript, esbuild, vite) and crates' top-5 (hashbrown, syn, …) are all
   plumbing. Apps come and go; toolchains compound.

### How it works (boring on purpose)

- One stdlib-only Python script (`scripts/collect.py`) — no dependencies to
  rot.
- One GitHub Action on a cron — the runner commits data back to main.
- A static page that fetches `latest.json` — no backend, no build step.

If you want the same thing for *your own* feeds, we also made
[feedpaper](https://github.com/zalize-com/feedpaper): fork it, edit
`feeds.yaml`, get your own daily digest page. Same idea — your data lives in
your repo, not our app.

Feedback we actually want: what source should be #8? And if you use the
dataset for something, we want to see it.
