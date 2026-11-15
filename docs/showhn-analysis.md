# What 14 years of winning Show HN launches have in common

We backfilled every month's top-10 Show HN posts — 179 months, 1,790
launches, January 2012 through today. The dataset answers questions the
daily front page can't:

**Nobody wins twice.** The all-time top-40 has 40 different authors. Show
HN crowns a new person every time — unlike the front page, where repeat
players (dang-era regulars, big blogs) recur. It's the most meritocratic
leaderboard on HN.

**The winning formula is a playable artifact, not a product.** Top launches
are things you touch immediately: a strummable virtual guitar, a bowling
system rebuilt on $1,600 of ESP32s, an e-ink frame that draws birds in an
1800s illustration style, a single-file web server (Redbean). The genre is
"I made a thing" — not "I built a company."

**Hardware made a comeback.** Maker/hardware launches barely register in
the 2012–2015 slice; by 2022–2026 they're staples of the top-40 (open-source
laptop 3,237pts, ESP32 bowling 2,935, retro console 2,690). Cheap ESP32-class
silicon + LLM-assisted embedded coding shows up as a real attention shift.

**The score ceiling doubled.** Median monthly #1: ~650pts in the 2010s,
~990 in the 2020s. Same inflation the front-page canon shows — but Show HN
inflated *more evenly*: 2025/2026 hold 13 of 40 top spots vs 2023's front-page
monopoly.

**Dec 2025's #2 all-time was made by an AI.** "Gemini Pro 3 imagines the HN
front page 10 years from now" (3,346) — a model's output posted as a launch.
The dataset may already contain the first AI-authored monthly winner; we
haven't checked every row. A question for future analysis.

---

Method: `scripts/showhn_backfill.py` → `data/show-hn-monthly.csv` (CC0).
Computed 2026-11-15.

_Written by Devin sessions A+B as part of trendscope._
