# Demand mining — round 2 (2026-11-17)

Method: structured-pull over HN Algolia comments, last ~30 days, 10 friction
phrases ("i wish", "wish there was", "doesn't exist", "no good way",
"frustrated with", "tired of", "hate that", "why is there no",
"someone should build", "can't believe there's no"). 241 unique comments,
keyword-bucketed by hand.

## Verdict: no cluster clears the ≥10 buildable threshold

| bucket | hits | assessment |
|---|---|---|
| ai/ml tooling | 50 | mostly feature wishes for existing AI products, not standalone opportunities |
| social/community | 9 | meta-complaints about HN itself, not product asks |
| auth/identity | 6 | incidental mentions, no coherent ask |
| files/sync | 6 | dead-horse wishes (GPU pricing, car batteries), unbuildable |
| self-host/deploy | 6 | already-solved (Caddy/Tailscale covers the homelab path) |
| browser ext | 6 | scattered; the MV2-orphan traffic already routed to tools/extensions.html |
| mobile/app | 5 | out of scope (app stores) |
| markdown/notes | 5 | call-notes niche is crowded NOW: Granola, Retranscript, Noted — three indie builders in this thread alone |
| privacy | 4 | GDPR/VPN talk, no wedge |
| calendar/scheduling | 3 | thin |
| docs/search | 2 | thin |
| rss/feed/digest | 1 | validates our position — nobody else asks for it |

## Read

- The "wish existed" vein on HN is thin this month (only 2 Ask-HN posts in 3d).
- Call-notes is the cautionary tale: by the time a pain cluster is visible in
  comments, 2–3 indie builders are already shipping. Speed matters more than
  novelty in this pipeline.
- Pain-mining SaaS field confirmed saturated (PainKillerIdeas, PainSpotter,
  HurryMind, DemandRadar, SaaSHunt — all gated AI-scored idea lists).
- Standing recommendation: keep feeding traffic surface on the two validated
  positions (open dataset + fork template) rather than force a #3 product
  through a weak gate. Next mining round in ~1 week, or widen to
  Lobsters/dev.to/V2EX corpora next time.
