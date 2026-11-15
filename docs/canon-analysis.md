# What 19 years of HN front pages are actually made of

We backfilled every month's top-10 stories on Hacker News — 238 months,
2,380 stories, February 2007 (launch month: `pg` asking what features the
site needed) through today. Some things only visible at this resolution:

**Half of all monthly #1s clear 2,000 points.** Of 238 monthly leaders,
118 crossed 2k — the community's ceiling moved from ~300 (2007) to ~6,000
(2018+), but "big month" has meant roughly the same thing for a decade.

**The all-time top-40 is four genres.** Deaths and memorials (Hawking 6,015,
Wirth, "In loving memory of square checkbox"), Big-Tech drama (the FBI–Apple
letter, OpenAI's board firing Sam Altman — the single biggest company
story ever on HN at 5,710), infrastructure catastrophes (xz backdoor 4,549,
CrowdStrike's global bluescreen 4,489), and outages. What *isn't* there:
product launches, funding rounds, "why I use X" essays.

**The canon skews young.** 8 of the top-40 all-time stories are from 2023
alone; 29 of 40 are from 2020 onward. Either attention compounds with the
user base, or recent decades were genuinely more dramatic. Probably both —
but a dataset should note it.

**History rhymes by the month.** Every November is a storyline: 2023's
OpenAI succession crisis, 2022's Meta layoffs, 2025's Steam Machine reveal.
The `canon.html` page's this-month-in-history view surfaces this in one glance.

**The freelancer thread didn't exist until 2013.** HN's labor board grew
organically — Who's Hiring (2010), Who Wants to Be Hired (2010), Freelancer
(2013). The shape of the monthly ritual itself is history.

---

Method: `scripts/canon_backfill.py` → `data/hn-canon-monthly.csv` (CC0,
regenerate any time — Algolia indexes everything back to launch).
Numbers computed 2026-11-15.

_Written by Devin sessions A+B as part of trendscope._
