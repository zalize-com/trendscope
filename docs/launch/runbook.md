# Launch-day runbook — what happens the moment the owner says "go"

Owner says GO → we execute this top to bottom. Every step lists who does it
(Devin can / owner must) and what gets backfilled after. Target: everything
below inside ~2 hours, posts spread for maximum window coverage.

> Hard rule: **owner posts from their own accounts.** Devin preps, stages,
> verifies, monitors — never posts as the owner.

## T-0: pre-flight (Devin, 10 min)

- [ ] `latest.json` generated_at < 26h ago (fresh snapshot — today's edition
      must look alive when visitors land)
- [ ] `curl -sI https://trendscope.zalize.com` → 200; same for
      feedpaper.zalize.com, /movers, /state-of-rss, /tools/doctor, /daily/sec
- [ ] og.jpg loads (share card), feed.xml validates, sitemap.xml < 90 locs
- [ ] Empty-source banner honest (persistent < ~150; if a wave is mid-crash,
      say so in the Show HN comment instead of hiding it)
- [ ] `python3 scripts/indexnow.py` — resubmit all sitemap URLs
- [ ] feedpaper: latest digest visible on homepage (private repo → snapshot
      data; if >2 days stale, run `bash scripts/deploy_cf.sh` there first)

## T+0: Show HN (owner posts — the anchor)

Window: **Tue–Thu 14:00 UTC** (9am ET) if "go" lands in a weekday window;
otherwise post when told — a mediocre slot beats a delayed launch.

- Owner posts `docs/launch/show-hn-draft.md` verbatim (title + body).
- Devin immediately after it appears:
  - [ ] Confirm post is live: `hn.algolia.com/api/v1/search?tags=show_hn&query=trendscope`
  - [ ] Owner posts first comment (pre-staged): dashboard link +
        `data/history.csv` + "feedback wanted: schema, missing sources,
        weekly digest yes/no"
  - [ ] If it doesn't hit `tags=front_page` in ~30 min, no panic — log the
        rank, keep going; dev.to/lobste.rs are still ahead.

## T+15: dev.to first article (owner posts)

- Publish draft #1 (`devto-draft.md` — the "open-sourced the question" piece;
  it's the product intro, not the war story).
- Backfill after publish:
  - [ ] `canonical_url` → set to the dev.to URL inside the article front-matter
        via dashboard edit (or leave — canonical already points at the repo)
  - [ ] Add the dev.to URL into `docs/distribution.md` next to the draft
  - [ ] Seed first comment (pre-staged): link to /state-of-rss + history.csv
  - [ ] Update repo README badge row with the article link (Devin commit)

## T+30: secondary venues (owner posts, Devin preps text)

In order of fit (drafts live in distribution.md / launch/):

| # | Venue | Asset | Backfill |
|---|-------|-------|----------|
| 1 | Lobste.rs | project link, tags `data` `show` | URL into distribution.md |
| 2 | r/datasets | dataset + dashboard post | URL into distribution.md |
| 3 | HN daily/Show HN thread | covered by T+0 | — |

## T+45: Devin-driven submissions (no owner needed)

These are PRs Devin opens directly:

- [ ] `awesome-public-datasets` — dataset section, one-line description +
      repo link
- [ ] `awesome-json-datasets` — `latest.json` endpoint entry
- [ ] (Optional) `awesome-selfhosted` — feedpaper, once its repo is public

Each PR: title = repo convention, body = 1-line "what/where/license".
Links backfilled into distribution.md.

## T+60: metrics baseline (Devin)

Snapshot starting state so day-1 delta is measurable:

- [ ] GitHub: stars/forks count (`gh api repos/zalize-com/trendscope`)
- [ ] CF Web Analytics (zalize.com zone): baseline requests/visitors today
- [ ] HN post: points/comments count + rank
- [ ] dev.to: public_reactions_count on the article
- [ ] Write the baseline block into distribution.md §launch-metrics

## T+90 → T+120: watch + respond

- [ ] Re-check HN rank/points every ~15 min for 2h; draft suggested replies
      for substantive comments (owner posts them — flag questions about
      data schema, source coverage, privacy/compliance with pre-drafted answers)
- [ ] Watch referrers in CF analytics — any surprise inbound → log it
- [ ] If Show HN dies quietly: still fine — the dataset compounds daily and
      dev.to/PH are the long game. Log, move on, do NOT repost same-day.

## Not today (scheduled, don't touch)

- **Product Hunt**: week 2, after a real week of history + weekly digest
- **Kaggle dataset**: owner account, `kaggle datasets create -p data/kaggle`
- **dev.to drafts #2–7**: staggered 1/day after launch (order in
  distribution.md); each gets canonical + first-comment treatment
- **feedpaper repo → public**: owner click; until then it stays off
  all public posts' asset lists

## If something breaks mid-launch

- Site down → `bash scripts/deploy_cf.sh` redeploys in ~90s; data endpoints
  never die (raw.githubusercontent)
- A wave of "your data is wrong" comments → honest answer template:
  "empty-set rotates daily on rate-limit tides — see zerowatch.json; we only
  call a source dead after 3 consecutive empty snapshots"
- Wrong domain somewhere → `scripts/switch_domain.py` exists and is proven
