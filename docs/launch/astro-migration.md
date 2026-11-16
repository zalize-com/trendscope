# Astro migration plan (decided 11/16 — user: "best long-term, not short-sighted")

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
