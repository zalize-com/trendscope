# Activation checklist — every manual step to go live

Everything below needs a human click (account or repo permissions we don't
have). Ordered by impact-per-click. Estimated total time: **~10 minutes**.

## 1. ~~Publish both sites~~ ✅ DONE 2026-11-17 (Cloudflare Pages)

- **https://trendscope.zalize.com** — live, 74 pages, data proxied fresh from repo
- **https://feedpaper.zalize.com** — live
- Backup URLs: trendscope-660.pages.dev / feedpaper.pages.dev
- `trendscope.pages.dev` is taken by an unrelated project — canonical is the zalize domain.

### Remaining clicks here

| Item | Why | Steps |
|---|---|---|
| feedpaper repo → public | fork-template product needs it; also re-enables live-data proxying (private raw 404s) | [Settings → Danger Zone → Change visibility](https://github.com/zalize-com/feedpaper/settings) → public |
| (optional) auto-redeploy secrets | lets Actions redeploy the static layer after pushes — data already stays fresh via raw proxy | repo Settings → Secrets → `CLOUDFLARE_API_KEY`, `CLOUDFLARE_EMAIL`, `CLOUDFLARE_ACCOUNT_ID` + variable `CF_DEPLOY_ENABLED=1` |

## 2. Say the word and we ship the submissions

These are ready-to-paste in `docs/distribution.md`; tell us "go" and we open
the PRs as you:

- **awesome-public-datasets** PR (trendscope row)
- **awesome-selfhosted** PR (feedpaper row)
- **Show HN** posts for both (drafts ready; needs your HN account to post —
  we can write, you paste)
- **dev.to articles** ×2 (drafts ready; needs your dev.to account or API key)

## 3. Money hooks (optional, ~5 min each)

- **GitHub Sponsors**: [github.com/sponsors/accounts](https://github.com/sponsors/accounts) →
  enable → tell us and we add `.github/FUNDING.yml` (one commit).
- **Paid full-history dataset** (your existing zalize pattern): put a
  data.zalize.com or Gumroad link in README — placeholders already marked.
- **Kaggle dataset mirror**: upload `data/history.csv` + `data/latest.json`
  (CC0) — instructions in distribution.md. Drives dataset SEO traffic back.

## 4. Repo metadata (~2 min — Devin's token can't set it)

Topics and homepage feed GitHub topic pages and search snippets — free
discovery traffic. Easiest: repo page → ⚙ next to "About". Or CLI:

```bash
gh repo edit zalize-com/trendscope --add-topic dataset,open-data,hacker-news,github-trending,daily-digest,developer-tools,github-actions,cc0,dashboard --homepage https://trendscope.zalize.com
gh repo edit zalize-com/feedpaper --add-topic rss,digest,github-actions,github-pages,self-hosted,news-reader --homepage https://feedpaper.zalize.com
```

## Already done for you

- ✅ trendscope: ~9,200 sources / ~109k items per snapshot — blogs,
  newsletters, podcasts, YouTube channels, zh lane; 63-page site (Astro build) with
  MiniSearch full-text search, feed.xml (subscribable), sitemap.xml,
  compare/streaks/movers pages, canon-history datasets 2007→today,
  embed widget, API docs + OpenAPI, llms.txt, 35-lesson methodology
- ✅ feedpaper: 30 curated feeds, production-verified (Actions bot already
  committing daily digests), RSS+Atom+OPML in/out, own feed.xml, tag chips,
  archive, weekly, tests, hardened parser
- ✅ All monetization/distribution copy written and reviewed
- ✅ Two Devin sessions relay-running until 11/22 — ask us for anything

_Nothing else is blocked on you — we're building continuously._
