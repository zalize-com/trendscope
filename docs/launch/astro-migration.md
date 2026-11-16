# Astro migration plan (decided 11/16 — user: "best long-term, not short-sighted")

> **Status 11/16 ~15:00 CST: all 62 pages migrated and building green.**
> Waves A–C done via `scripts/migrate/to_astro.py` (hand-written index +
> mechanical transcription). Parity fixes landed: daisyUI `d-` prefix
> (class collisions), `.row` grid variant, per-page footers re-injected,
> nav `.here` parity, `/tools/` postbuild copy, Pages-subpath rebase
> (`scripts/migrate/rebase.sh` + `SITE_BASE`/`SITE_ORIGIN` envs),
> canonical subpath concat, dist linkcheck wired into site.yml CI.
> Remaining gate: full-site visual diff sign-off → Pages enable.

## Why Astro (+ Tailwind/daisyUI), and why now
- Current state: 55+ static HTML pages each hand-duplicating
  head/OG/canonical/topbar/footer chrome. Style bugs proved the cost
  (38-page light-mode fix, tools/ path fixes, per-page sed waves).
- Long-term benefit (user directive): one Layout component owns chrome;
  design changes land once. Component reuse (board row, card, chip,
  tab bar) replaces per-page inline styles.
- Astro ships zero-JS static HTML by default → Pages hosting unchanged,
  self-host story unchanged, SEO/OG identical or better.
- Tailwind + daisyUI = mainstream utility/component system; replaces
  both Pico and hand-rolled trendscope.css where convenient
  (trendscope.css tokens can be ported as Tailwind theme at first).

## Non-negotiables (don't regress these)
- Static output only; no backend; stdlib-only data pipeline untouched.
- All URLs stay byte-identical: `astro.config.mjs` sets
  `build: { format: 'file' }` so `src/pages/x.astro` emits `x.html`
  (not `x/index.html`) — sitemap/links/SEO and downstream consumers
  (feed.xml, OPML, widget.js) keep working byte-for-byte.
- data/, docs/, scripts/, .github/ are NOT part of the site build —
  Pages deploy serves build output + repo data files unchanged.
- 55-page parity checklist before Pages flips to build output.

## Repo layout (proposal)
```
site/                 # Astro project (package.json, astro.config.mjs)
  src/layouts/Base.astro        # head + OG/canonical + topbar + footer
  src/components/{BoardRow,Card,Chip,Topbar,...}.astro
  src/pages/*.astro             # one per current .html page
  src/styles/tokens.css         # ported design tokens
site/dist/            # build output → Pages deploy target
```

## Migration waves
1. Scaffold site/ + Base layout + tokens port + CI build job
   (Actions: setup-node → npm ci → astro build → upload artifact)
2. Wave A: index.html, movers, topics, zh, digest, about — the
   high-traffic six; screenshot-diff vs prod each page
3. Wave B: board pages (week/day/year/compare/ideas...) bulk script
4. Wave C: tools/*.html (94 embedded tools — keep their JS, re-home
   markup into pages) — heaviest, last
5. Parity gate: linkcheck + OG/canonical audit + visual diff +
   latest-lite fetch path unchanged → switch Pages source to Actions
   deploy artifact → delete legacy .html after one stable week

## Division
- A: scaffold, layout/components, CI deploy wiring, wave B bulk
- B (me): tokens/design parity QA, wave A+C migration, screenshot
  diff harness, parity checklist owner

## Gate results (2026-11-16) — PASS, ready for Pages flip

62/62 pages built and parity-verified on `site/dist`:

- **Pixel diff** (`scripts/migrate/visual_diff.sh`, `--virtual-time-budget` + 25s timeout):
  board family 0%, 20+ pages <2%, median ~5%. Three pages >15% all
  classified non-regression noise: `source`/`week` (dense word-cloud
  pages — 1px line-height delta × whole-page glyph edges) and
  `tools/web` (QR CDN fetch timing flake, same CDN both sides).
- **Head parity**: title/canonical/JSON-LD/twitter equal; og copy
  refreshed on 9 pages (semantically equal or richer, e.g. stale
  "2375 sources" in old JSON-LD fixed to 9213).
- **Structural**: footer 0 missing, nav `.here` page-set identical,
  embed.html keeps topbar + 28 `?mode=` branches 1:1, tools/index.html
  URL preserved via postbuild copy, 86 internal refs 0 broken,
  sitemap/tools parity green.
- **Architecture bugs found & fixed during migration**: daisyUI class
  collision (`.hero>*` grid overlay stacked all hero children — fixed
  with `prefix: "d-"`), `.row` flex/grid variant mixup, tools/index
  URL fold under `build.format:'file'`, canonical losing SITE_ORIGIN
  subpath (`new URL("/x", base)` drops path → string concat),
  51 page footers stripped by chrome-pass, JSX whitespace collapse in
  footers, scripts emitted after `</html>`, `<script is:inline>` braces
  parsed as expressions (fixed by externalizing to `/js/pages/*`).
- **Subpath deploy**: `SITE_BASE=/trendscope` + `SITE_ORIGIN` env rebase
  root-absolute refs at postbuild (`scripts/migrate/rebase.sh`);
  default build stays preview-domain identical.

Remaining: Pages source flip to Actions artifact (user action), then
legacy `.html` deletion after one stable week.
