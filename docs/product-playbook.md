# Product Playbook — our product workflow, researched & codified

Written 2026-11-17 after the user's critique: "你们是闭门造车，上网去学"。
This document maps our actual process onto named industry frameworks
(Solo-Founder lifecycle, JTBD, Lean BML loop, Mom Test, Shape Up,
structured-pull pain mining) and marks what we adopted vs. what we still
can't do as two autonomous agents. Every section has a **gap** note.

Sources consulted (11/17):
- Solo Founder lifecycle (Discovery→Validation→Build→Launch→Growth), oneperson.work
- Steve Blank, MVP tree (customer archetype → JTBD → execution)
- Eric Ries, Build-Measure-Learn; thrv.com on JTBD-before-build
- Rob Fitzpatrick, The Mom Test (ask about past behavior, not opinions)
- Basecamp, Shape Up (appetite, betting table, big/small batch, no backlog)
- IdeaTwister / SaaStash structured-pull Reddit pain-mining method

---

## Stage 1 — 需求分析 (Discovery & Validation)

**Framework**: pain-mining, not brainstorming. Structured pull:
pick a niche room → friction keywords ("wish existed", "hate", "workaround",
"is there a tool") → cluster by theme → pressure-test each cluster on
buyer / price / channel / wedge → validate via real dialogue.

**Our version (as agents)**:
- Community mining rounds: Ask HN "what tool do you wish existed" threads,
  Lobsters, dev.to, V2EX 需求帖, ProductHunt comments — scored each
  candidate 1-5 on value / feasibility / monetization before building.
- Competitor table before building (Sentinel Feed, ViralSlate, Hotfork,
  usedigest → found the empty slot: nobody ships a *versioned, downloadable*
  cross-source dataset).
- JTBD framing: "developers & data people hire us to know what the
  ecosystem paid attention to yesterday — without subscribing to 9,000 feeds."

**Gap (honest)**: we can't run Mom-Test interviews or collect pre-orders —
both need the user's identity/accounts. Our validation substitutes:
empty-slot analysis + keyword demand (search volume for "X alternative")
+ usage signals post-launch. **Weakness**: no money-evidence gate before
build. Mitigation: keep every product at ≤1 day skeleton cost so a failed
bet is cheap — Shape Up "appetite" applied to ourselves.

## Stage 2 — 设计 (frontend / backend / framework / deployment)

**Framework**: design the contract before the interface — schema/API/data
dictionary first, screens second. Deployment design = zero-ops first:
static site + GitHub Actions + edge redirects, no servers to babysit.

**Our version**: unified item schema written before the first fetcher
(`source/rank/title/url/score/comments/tags/author/captured_at`);
data-dictionary.md is the contract doc; pages are rendered views over it.
Deployment: GitHub Actions collect → commit → Cloudflare Pages static +
`_redirects` proxy of `/data/*` to repo raw = always-fresh, zero servers.

**Gap**: no user-flow diagrams or wireframe stage — we went data → page
directly. Acceptable for a data product; would not skip this for a product
with actual user journeys.

## Stage 3 — 技术选型 (tech selection)

**Criteria (in order)**: ① zero-ops / free-tier sustainable ② boring &
battle-tested ③ fewest dependencies (stdlib-first — a fork must run with
zero pip install) ④ user said: 对标主流但保持 indie 轻量.

**Actual picks**: Python stdlib collectors (urllib + xml.etree, custom
YAML-subset parser) · GitHub Actions as the cron · Astro + Tailwind +
daisyUI(prefixed, class-collision lesson) for the site · Cloudflare Pages
+ raw-proxy data layer · no backend, no database — git *is* the database.

**Gap**: we chose well but didn't benchmark alternatives formally
(e.g. SQLite-as-database option, Deno cron, Workers-side rendering).
Adding a one-line "also considered" table per future pick.

## Stage 4 — 实现 (framework first, then content)

**Framework**: walking skeleton — end-to-end thin slice first, flesh out
after. Never a big-bang build.

**Our version**: day 1 = collect.py + latest.json + one HTML page, live.
Then layered: more sources → daily snapshots → history/velocity → Astro
migration (62 pages, byte-level parity gate) → tools/ sub-site → datasets.
Same for feedpaper: fetch.py + index.html first, OPML/archive/weekly later.

**Gap**: none significant — this stage we did right by accident.

## Stage 5 — 验收与迭代 (acceptance & agile iteration)

**Framework**: independent verification + measurable gates + the
BML loop (build→measure→learn→iterate).

**Our version**:
- Two-agent QA: A ships, B independently pulls data and signs off — no
  self-certification. vdiff pixel-gate for the 62-page migration.
- Data contract validation in CI (validate.py), linkcheck gate,
  merge-base push assertion (silent-green CI lesson, methodology 33).
- Runtime telemetry = the dataset itself: zerowatch source-health endpoint
  (persistent-empty vs tide), degraded-source banner, mojibake audits.
- Methodology log: every incident becomes a numbered rule (42 entries).
- Iteration cadence = collect runs (~2×/day) + push-triggered CI; appetite
  ≈ anything shippable inside one stretch, no multi-day epics.

**Gap**: no external user feedback loop yet — needs launch + real traffic.
Analytics intentionally absent (no tracking); we'd add a privacy-respecting
counter once the user picks one.

---

## Collaboration protocol v3 (agent-to-agent)

1. Shared whiteboard async-first; direct messages only for: decision
   needed / keepalive / awaited handover. Every direct message ends with
   "→ 需要你做什么".
2. Division by pipeline stage: A owns the machine (collectors, CI, deploy,
   site plumbing); B owns judgment (QA sign-off, research, content, triage).
   Either may cross over — leave a whiteboard note first; on collision the
   better implementation wins, decided by evidence not seniority.
3. Every shipped batch gets independently verified before sign-off:
   numbers pulled from the artifact, not trusted from the report.
4. Incident → methodology entry; incident in shared schema → scan all
   consumers before shipping.

## 工具集 (work set)

collect.py + feeds_*.json registry · zerowatch.py source health ·
rss2json/feed2json fallback chain with quota budget · gen_opml/gen_sources_md ·
switch_domain.py · linkcheck.py + vdiff harness (pixel-diff gate) ·
deploy_cf.sh + _redirects raw-proxy · digest.py/feed.py generators ·
Astro site (64 pages) + shared design system.

## Next-product pipeline (how we pick the next one)

Repeatable, mined-not-brainstormed:
1. **Mine**: structured pull on new rooms (one niche per round, friction
   keywords, cluster ≥10 independent mentions = candidate).
2. **Score**: value / feasibility / monetization / ops-cost, 1-5 each,
   in the whiteboard — both agents score, disagreements = discussion point.
3. **Gate**: must name buyer + painful job + why incumbents fail +
   our wedge. No gate, no build.
4. **Skeleton**: walking skeleton ≤1 day; then either iterate or park.
5. **Portfolio rule**: a product graduates to "maintain-only" when its
   daily pipeline runs green unattended for 3+ days — then we may bet on
   the next product. trendscope/feedpaper qualify as of 11/17.
