#!/usr/bin/env python3
"""Regenerate sitemap.xml daily: every URL gets today's lastmod (page content
is data-driven and refreshes with each snapshot). Enumerates site/src/pages
Astro files + dynamic daily-lane routes; emits extensionless URLs (CF Pages
canonical form — .html 308s to extensionless)."""
import datetime, glob, os, re

ROOT = os.path.join(os.path.dirname(__file__), "..")
PAGES = os.path.join(ROOT, "site", "src", "pages")
ORIGIN = "https://trendscope.zalize.com"
LANES = ["sec", "eb", "tb", "br", "nl", "pb", "yt", "tldr", "misc"]

locs = []
for f in sorted(glob.glob(os.path.join(PAGES, "**", "*.astro"), recursive=True)):
    rel = os.path.relpath(f, PAGES)[:-6]  # strip .astro
    if os.path.basename(rel).startswith("["):
        continue
    if os.path.basename(rel) == "index":
        rel = os.path.dirname(rel)
        loc = f"/{rel}/" if rel else "/"
    else:
        loc = f"/{rel}"
    locs.append(loc)
locs += [f"/daily/{lane}" for lane in LANES]
# asset endpoints worth indexing
locs += ["/feed.xml", "/llms.txt", "/trendscope.opml", "/data/latest.json"]

today = datetime.date.today().isoformat()
out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc in sorted(set(locs)):
    out.append(f"  <url><loc>{ORIGIN}{loc}</loc><lastmod>{today}</lastmod></url>")
out.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(out) + "\n")
print(f"sitemap.xml: {len(locs)} urls, lastmod={today}")
