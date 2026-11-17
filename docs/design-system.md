# Design system notes

Adopted rules (borrowed from openstatus DESIGN.md and dub themes.css — read those
sources before inventing anything new):

## Principles
- **Hierarchy over decoration.** One loud level per page (item titles), everything
  else quiet. Emphasis = weight + color first, size last.
- **Quiet by default.** Start muted (`var(--dim)`), lift only the word that
  matters. Accent color is earned, not ambient.
- **Compose, don't invent.** New screens = existing shared classes in a new
  arrangement. A new primitive is a decision, not a side effect.
- **Content left, properties right.** Index is a dashboard: main column (board)
  + rail of labeled cards (Snapshot / Signals / By topic). Not a centered stack.

## Type
- Sans (Inter) for prose; **Space Grotesk** for display headings/wordmark only.
- **Mono + `tabular-nums` for values**: counts, dates, ranks, scores — anything
  compared or copied. Applied via `.stamp/.topic-chip b/.row .rank,.score,.heat/.num/code`.
- Sentence case. Section title carries its muted count: `Signals · 3`.

## Color
- Tokens only (`--bg/--panel/--border/--fg/--dim/--accent/--green/--orange/--red/--st-*`),
  never raw hex in page CSS. Dark + light themes both come from tokens.
- Status color sits on the smallest element that can carry it (dot, one word,
  chip). Chrome stays neutral.

## Spacing & layout
- `.wrap` 1080px; `.dash` grid `1fr | 296px` rail, collapses to single column
  ≤940px and ≤620px.
- Cards: `padding 12px 16px 14px`, `border-radius 10px`, labeled by
  `railcard > h3` (11px uppercase dim).

## Motion (CSS only, no animation lib)
- Named properties in transitions, never `transition-all`.
- Press feedback `transform: scale(.97)` on `.btn/.tab/.topic-chip/.chip`.
- One authored motion moment: the `.radar` sweep (disabled under
  `prefers-reduced-motion`).
- Nothing moves that is seen 100×/day except hover/press feedback.

## Links
- Quiet links use dashed muted underline
  (`.status-item a`, `.board-actions a`, `.pagesub a`), not color change.

## Wheels we use (don't hand-roll these)
- **daisyUI 5 (`d-` prefix)**: `d-input`, `d-select`, `d-btn`, `d-btn-outline`,
  `d-badge`, `d-tabs`, `d-dropdown`, `d-join`, `d-card`, `d-table`, `d-tooltip`.
  Colors are bridged to our tokens via the palette-bridge block in global.css —
  d-* components follow our theme automatically (default light + dark themes
  already match our `data-theme`/`prefers-color-scheme` semantics).
- **Astro compound kit** (`src/components/`): `RailCard`, `Section`, `Card` —
  the repeated page furniture. New pages compose these, never copy markup.
- **JS libs (CDN, always `is:inline`)**: MiniSearch (search), dayjs, cronstrue,
  diff, marked, papaparse, lucide icons, swagger-ui, js-yaml, compare-versions.
- **Layout wheels**: `.wrap` container, `.dash` two-column grid, `.cards` grid,
  `.board/.row` list primitive — compose, don't invent.

## Theme
- `html[data-theme]` + `localStorage.tsTheme` + `?theme=` param; OS
  `prefers-color-scheme` as default. FOUC script runs before first paint in
  `Base.astro`. Page-local token overrides must target
  `:root:not([data-theme])` inside the media block **and**
  `html[data-theme="light"|"dark"]` — transform all new pages accordingly.

## Type tokens (2026-11-18)

| token | value | role |
|---|---|---|
| `--font-sans` | IBM Plex Sans (+ CJK stack) | body/UI text — one token, every page consumes |
| `--font-display` | Bricolage Grotesque | h1/h2/brand/tagline |
| `--font-mono` | IBM Plex Mono | tabular numbers, code, stamps |

Page `body{font:...}` rules must reference `var(--font-sans)` — no inline stacks
(53 pages were converged to the token when it was introduced).

## Impeccable detector — accepted exceptions

- `radial-halo` on the `.radar` dial: the radar instrument is the brand motif
  (concentric rings + conic sweep), not a decorative page wash. Documented,
  not a defect.
- `em-dash-overuse` advisories: long-form copy pages; trimmed where cheap.
- `tools/web.js font-family:arial`: intentional — Facebook OG-card mock.
- Modeled contrast warnings that pair a light-theme token with a dark-theme
  surface (e.g. `#0969da on #161b22`) — verified visually as false pairings.
