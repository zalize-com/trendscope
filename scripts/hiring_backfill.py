#!/usr/bin/env python3
"""Backfill data/hiring-monthly.csv — every monthly HN hiring/seeking thread
Algolia can see (2010 → today). Run manually when needed; idempotent.

Output schema: month,kind,comments,thread_id,url,created
Dedupe: per (kind,month) the highest-comment thread wins — monthly "canonical"
threads beat occasional reposts/typos.
"""
import csv
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import DATA_DIR  # noqa: E402

MONTH_RE = re.compile(
    r"\((January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4}\)", re.I)
QUERIES = [("hiring", "who is hiring"), ("seeking", "who wants to be hired"),
            ("freelancer", "seeking freelancer")]
OUT = os.path.join(DATA_DIR, "hiring-monthly.csv")


def gj(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trendscope-backfill/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    rows = []
    for kind, query in QUERIES:
        seen = set()
        for page in range(7):
            d = gj("https://hn.algolia.com/api/v1/search?tags=ask_hn"
                   f"&query={urllib.request.quote(query)}&hitsPerPage=100&page={page}")
            for h in d.get("hits", []):
                oid = h["objectID"]
                title = h.get("title", "")
                if oid in seen or query not in title.lower():
                    continue
                m = MONTH_RE.search(title)
                if not m:
                    continue
                seen.add(oid)
                rows.append({"kind": kind, "month": m.group(0).strip("()"),
                             "thread_id": oid, "comments": h.get("num_comments", 0),
                             "url": f"https://news.ycombinator.com/item?id={oid}",
                             "created": h["created_at"][:10]})
            if page >= d.get("nbPages", 1) - 1:
                break
            time.sleep(1)

    best = {}
    for r in rows:
        k = (r["kind"], r["month"])
        if k not in best or r["comments"] > best[k]["comments"]:
            best[k] = r
    out = sorted(best.values(), key=lambda r: r["created"])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["month", "kind", "comments",
                                        "thread_id", "url", "created"])
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT}: {len(out)} monthly rows "
          f"({out[0]['month']} → {out[-1]['month']})")


if __name__ == "__main__":
    main()
