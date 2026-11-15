#!/usr/bin/env python3
"""Aggregates → docs/api/{domains,authors,discussed}.json: leaderboards the
site computes client-side, published as endpoints.
Same semantics as the matching pages. Daily via collect workflow."""

import csv
import json
import os
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
API = os.path.join(ROOT, "docs", "api")

SKIP = {"news.ycombinator.com", "github.com", "www.npmjs.com", "pypi.org",
        "crates.io", "dev.to", "lobste.rs"}
LIMIT = 50


def host_of(url):
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def main():
    days = set()
    doms = defaultdict(lambda: {"hits": 0, "days": set(), "srcs": set(), "top": None})
    authors = defaultdict(lambda: {"hits": 0, "days": set(), "srcs": set(), "top": None})
    items = {}  # url -> best comment-bearing row
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        url = r.get("url") or ""
        d = r.get("date") or ""
        if not url or not d:
            continue
        days.add(d)
        score = int(float(r.get("score") or 0))
        hit = {"title": r["title"], "url": url, "score": score,
               "metric": r.get("metric") or "", "date": d}

        h = host_of(url)
        if h:
            h = h[4:] if h.startswith("www.") else h
            if h not in SKIP:
                dm = doms[h]
                dm["hits"] += 1
                dm["days"].add(d)
                dm["srcs"].add(r["source"])
                if not dm["top"] or score > dm["top"]["score"]:
                    dm["top"] = hit

        comments = int(float(r.get("comments") or 0))
        if comments:
            cur = items.get(url)
            if not cur or comments > cur["comments"]:
                items[url] = {"title": r["title"], "url": url,
                              "score": score, "comments": comments,
                              "metric": r.get("metric") or "",
                              "source": r["source"], "date": d,
                              "author": r.get("author") or ""}

        who = (r.get("author") or "").strip()
        if who:
            a = authors[who]
            a["hits"] += 1
            a["days"].add(d)
            a["srcs"].add(r["source"])
            if not a["top"] or score > a["top"]["score"]:
                a["top"] = hit

    def pack(rows, key):
        return [{
            key: k,
            "days_on_board": len(v["days"]),
            "items": v["hits"],
            "sources": sorted(v["srcs"]),
            "top_hit": v["top"],
        } for k, v in sorted(rows.items(),
                            key=lambda kv: (-len(kv[1]["days"]), -kv[1]["hits"]))[:LIMIT]]

    now = datetime.now(timezone.utc).isoformat()
    for name, data in (("domains", pack(doms, "hostname")),
                       ("authors", pack(authors, "author"))):
        out = {"generated_at": now, "latest_snapshot": max(days),
               "total": len(doms if name == "domains" else authors),
               name: data}
        with open(os.path.join(API, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"{name}.json: {len(data)} rows / {out['total']} total")

    discussed = sorted(items.values(), key=lambda x: -x["comments"])[:LIMIT]
    heated = sorted((x for x in items.values() if x["score"] >= 50),
                    key=lambda x: -x["comments"] / max(1, x["score"]))[:LIMIT]
    out = {"generated_at": now, "latest_snapshot": max(days),
           "total": len(items),
           "discussed": discussed, "heated": heated}
    with open(os.path.join(API, "discussed.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"discussed.json: {len(discussed)}+{len(heated)} rows / {out['total']} total")


if __name__ == "__main__":
    main()
