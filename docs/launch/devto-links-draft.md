---
title: "Bitly is quietly auctioning off your old links — own your feed chain instead"
published: false
tags: webdev, opensource, rss, selfhosted
---

Yesterday's HN front page carried the story: old Bitly links are being
hijacked and redirected. Millions of short URLs people baked into blog posts,
tweet threads, PDFs and slides now point wherever the highest bidder wants.

It's the third act of a play we've watched before: a free convenience layer
becomes the landlord of your distribution, and eventually the rent comes due
— in redirects, in dead profiles, in lost archives.

Your reading list has the same problem, and nobody talks about it.

## The subscription you don't control

If your daily information diet runs through a hosted reader or a
digest-by-email startup, your subscription graph lives on *their* disk, in
*their* format, behind *their* login. When they pivot, get acquired, or
start charging for the export feature, you start over — same as every
Bitly user did this week.

The fix isn't a different landlord. It's a file you own.

## The dumbest possible architecture (that's the point)

We built feedpaper on a premise that sounds too simple to work:

1. `fork` the repo
2. edit `feeds.yaml` (or drop in an OPML export from whatever reader you
   use today)
3. Settings → Pages → your own daily digest site regenerates itself every
   morning via GitHub Actions

No account anywhere. No server. No third party between you and your feed
list. The YAML file *is* the subscription — plain text, diffable, in your
git history forever. Move it, fork it, diff it, revert it.

The whole pipeline is ~200 lines of Python stdlib: a hand-rolled YAML-subset
parser (so forks never need `pip install`), `xml.etree` for RSS 2.0 and Atom,
and GitHub's own free runners doing the daily fetch. When a feed host
rate-limits the Actions egress IP, the fetcher falls back through a free
server-side proxy lane and marks the failure on the page instead of dying.

It's not a product you sign up for. It's a product you *have*.

## What the dataset half looks like

The same plumbing runs trendscope, our other repo — it snapshots ~9,200
developer sources daily and publishes the whole registry as open data
(CC0): a browsable/searchable directory of every feed, per-lane OPML files
if you only want the security feeds or just the YouTube channels, and the
full 9,202-feed `trendscope.opml` if you want everything.

An OPML file is an odd thing to call an asset, but it is: it's a curated
map of where the good writing lives, in a format every feed reader since
2005 can import. If your reader dies next year, the file doesn't care.

## The pattern worth stealing

- **Data in files you own beats data in accounts you rent.** YAML, OPML,
  JSON exports — boring formats are durable formats.
- **Cron you can read beats infrastructure you can't.** A GitHub Action
  that runs `python3 fetch.py` daily is understandable in one sitting.
  If it breaks, the fix is in your repo, not in someone's status page.
- **A fork is a better account.** Growth shows up as forks and stars, not
  DAU dashboards. Nobody can deplatform your daily digest.

Links rot because someone else controls the middle. Feeds don't have to.

*feedpaper and trendscope are open source (MIT / CC0 data). Links in the
comments.*
