# Activation checklist — every manual step to go live

Everything below needs a human click (account or repo permissions we don't
have). Ordered by impact-per-click. Estimated total time: **~10 minutes**.

## 1. Publish both sites (highest impact — both currently code-only)

| Repo | Steps |
|---|---|
| trendscope | [Settings → Pages](https://github.com/zalize-com/trendscope/settings/pages) → Source: **Deploy from a branch** → Branch: **main**, folder: **/ (root)** → Save |
| feedpaper | [Settings → Pages](https://github.com/zalize-com/feedpaper/settings/pages) → same: main / root → Save |

Result: `zalize-com.github.io/trendscope` + `zalize-com.github.io/feedpaper` live
in ~1 min. Dashboard, all 65 tools, embed widget, every API endpoint activate
immediately — the site reads files straight from the repo.

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
gh repo edit zalize-com/trendscope --add-topic dataset,open-data,hacker-news,github-trending,daily-digest,developer-tools,github-actions,cc0,dashboard --homepage https://zalize-com.github.io/trendscope
gh repo edit zalize-com/feedpaper --add-topic rss,digest,github-actions,github-pages,self-hosted,news-reader --homepage https://zalize-com.github.io/feedpaper
```

## Already done for you

- ✅ trendscope: 15 sources, 10-day history, 29 data/analysis pages (incl. four
  canon-history datasets 2007→today), 65 tools, CLI, embed widget, RSS + JSON
  Feed, OG card, health monitoring, API docs, llms.txt
- ✅ feedpaper: production-verified (Actions bot already committing daily
  digests), RSS+Atom+OPML, tag chips, archive, own RSS feed, tests, FEEDS.md
- ✅ All monetization/distribution copy written and reviewed
- ✅ Two Devin sessions relay-running until 11/22 — ask us for anything

_Nothing else is blocked on you — we're building continuously._
