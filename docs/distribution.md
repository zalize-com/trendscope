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
pipeline that snapshots **eleven sources** every day — Hacker News (front
page, Show HN *and* Ask HN), GitHub trending, Lobsters, dev.to, npm, PyPI,
crates.io, Product Hunt and Techmeme — and commits the result back to the
repo as a normal file.

The interesting part isn't the dashboard — it's that **the data is the
product**:

- `data/daily/YYYY-MM-DD.json` — every edition, forever
- `data/history.csv` — append-only, built for "what's rising this week" queries
- `data/latest.json` — stable URL, embed it anywhere
- CC0 license. Do whatever you want with it.

The storefront page does more than a leaderboard: day-to-day diffs
(`compare.html`), staying-power streaks (`streaks.html`), and a demand lane
(`ideas.html`) that clusters Ask HN threads into "what devs keep asking for"
— with a built-vs-gap check against everything else on the radar.

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

If you want the same thing for *your own* feeds, we also made feedpaper
(link in the repo README once public): fork it, edit `feeds.yaml`, get your
own daily digest page. Same idea — your data lives in your repo, not our app.

Feedback we actually want: what source should be #12? And if you use the
dataset for something, we want to see it.

*[Publish note: replace the feedpaper mention with the real repo URL once
the repo is public; ask_hn/ideas angle works best after 2–3 days of data.]*

## dev.to article draft #2 (methodology — publish ~week 2)

**Title:** We let two AI agents mine HN, Lobsters, V2EX and Product Hunt for product gaps — here's what actually surfaced

**Tags:** showdev, ai, product, indiehackers

**Body:**

For a week we pointed two autonomous agents at every "what tool do you wish
existed" thread we could find — HN Ask threads, Lobsters, V2EX, dev.to,
Product Hunt comments. The goal: find what people keep asking for that
nobody shipped. Raw notes below, ranked by how often the same pain repeated.

**What repeated (≥3 independent threads):**

- *"Simple things that embed into an existing site"* — comments, voting,
  micro-forums, RSS→newsletter. Hosted versions all demand accounts and
  dashboards. (giscus/utterances prove the demand; the gap is breadth.)
- *"My own digest without signing up"* — RSS readers want logins; newsletters
  want your email. People just want a page that updates.
- *"Visualize branching decisions"* — docs and spreadsheets can't do trees;
  mermaid is code-first and intimidating.
- *The MV2 graveyard* — every utility extension Chrome killed left a
  "what's the alternative?" search stream behind. The ones needing no
  browser internals (formatters, encoders, color tools) map 1:1 to plain
  web pages.

**What looked juicy but isn't buildable without accounts/infra:** clipboard
sync across devices, unified favorites across apps, video auto-clipping.

**Method that worked:** don't ask "what would be cool" — count repetitions of
complaints, then check whether the fix needs a server. If it doesn't, it can
ship as a static page this week.

The first two outputs: [trendscope](https://github.com/zalize-com/trendscope)
(open daily dataset of dev attention) and
[feedpaper](https://github.com/zalize-com/feedpaper) (fork→feeds.yaml→your
own daily page). Both came straight out of the repetition ranking.
