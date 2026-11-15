#!/usr/bin/env python3
"""Backfill data/hn-canon-monthly.csv — the HN canon: top-10 front-page
stories per month, February 2007 (site launch) → current month.

Algolia's default ranking for tags=story surfaces highest-point items, so a
query-less search over a created_at_i window returns the month's top stories.
One request per month (~236 total, well inside the 1000/hr free limit).
Idempotent: rewrite the file each run.
"""
import csv
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import DATA_DIR  # noqa: E402

OUT = os.path.join(DATA_DIR, "hn-canon-monthly.csv")
TOP_N = 10
START = (2007, 2)  # HN launched Feb 2007


def gj(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trendscope-canon/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def months():
    y, m = START
    now = datetime.now(timezone.utc)
    while (y, m) <= (now.year, now.month):
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def main():
    rows = []
    for y, m in months():
        t0 = int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp())
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        t1 = int(datetime(ny, nm, 1, tzinfo=timezone.utc).timestamp())
        d = gj("https://hn.algolia.com/api/v1/search?tags=story"
               f"&hitsPerPage={TOP_N}"
               f"&numericFilters=created_at_i>={t0},created_at_i<{t1}")
        for rank, h in enumerate(d.get("hits", []), 1):
            rows.append({
                "month": f"{y:04d}-{m:02d}", "rank": rank,
                "title": h.get("title", ""), "url": h.get("url", ""),
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "author": h.get("author", ""),
                "id": h["objectID"],
                "hn_url": f"https://news.ycombinator.com/item?id={h['objectID']}"})
        print(f"{y}-{m:02d}: {len(d.get('hits', []))} stories", flush=True)
        time.sleep(0.4)

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["month", "rank", "title", "url",
                                          "points", "comments", "author",
                                          "id", "hn_url"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}: {len(rows)} rows")


if __name__ == "__main__":
    main()
