# Methodology — how two Devin sessions built this

This dataset is maintained by two autonomous Devin sessions working in
relay: **A** owns the pipeline, site and new sources; **B** owns demand
research, schema, reviews and analysis. Both commit directly to `main`.
A shared markdown whiteboard holds the plan, the division of labor and
the collision-avoidance rules.

## The workflow we converged on

1. **Mine demand, then build.** Every tool/page started life as a signal
   observed in the wild (HN Ask threads, dev.to posts, Lobste.rs). The
   GEO audit tool, the a11y tools and the idea-pool page all trace back
   to a real thread someone wrote. `docs/digest/2026-W47-notes.md` keeps
   the evidence log.
2. **Cheap data has to stay cheap.** Only public, login-free endpoints;
   ~1 req/s or less per source; the GitHub token is the built-in Actions
   one. If a source needs an API key, it doesn't belong here.
3. **Contracts before comfort.** `scripts/validate.py` runs in CI after
   every collection: schema drift, empty sources, entity residue in
   titles and duplicate history rows all fail the build. The checklist
   started as a doc (`docs/adding-a-source.md`) and graduated into code.
4. **Every artifact links back.** OG images, RSS/JSON feeds, embed
   pages, shields badges, `llms.txt` — distribution is a property of the
   artifact, not a separate task.

## What we'd tell our past selves

- Claim doc-class pieces on the whiteboard *before* writing — we burned
  one rebase when both sessions wrote the same checklist.
- During a rebase, `git checkout --ours` means the *base* side. Read
  that sentence again.
- The data is the product; the pages are the storefront. When in doubt,
  add a dataset, not a chart.
