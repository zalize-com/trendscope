#!/usr/bin/env python3
"""Per-source stats → docs/api/sources.json: how each tracked source performs
over the whole history.csv window (items, days, median days-on-board,
one-day %, top item). Updated daily by the collect workflow."""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
OUT = os.path.join(ROOT, "docs", "api", "sources.json")


def main():
    urls = defaultdict(lambda: {"title": "", "source": "", "score": 0,
                                "rank": 99, "days": set()})
    for row in csv.DictReader(open(HIST, encoding="utf-8")):
        url = row.get("url")
        if not url:
            continue
        e = urls[url]
        e["title"] = row["title"]
        e["source"] = row["source"]
        try:
            sc = int(row.get("score") or 0)
        except ValueError:
            sc = 0
        if sc > e["score"]:
            e["score"] = sc
            e["rank"] = int(row.get("rank") or 99)
        e["days"].add(row["date"])

    sources = defaultdict(lambda: {"items": 0, "urls": 0, "day_spans": [],
                                   "top": None, "score_total": 0})
    all_days = sorted({d for e in urls.values() for d in e["days"]})
    for url, e in urls.items():
        s = sources[e["source"]]
        s["items"] += len(e["days"])
        s["urls"] += 1
        s["day_spans"].append(len(e["days"]))
        s["score_total"] += e["score"]
        if s["top"] is None or e["score"] > s["top"]["score"]:
            s["top"] = {"title": e["title"], "url": url,
                        "score": e["score"], "rank": e["rank"]}

    out = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "days_tracked": len(all_days),
           "sources": {}}
    for name, s in sorted(sources.items(),
                          key=lambda kv: -kv[1]["items"]):
        spans = sorted(s["day_spans"])
        med = spans[len(spans) // 2] if spans else 0
        one_day = sum(1 for x in spans if x == 1)
        out["sources"][name] = {
            "items": s["items"],
            "unique_urls": s["urls"],
            "median_days_on_board": med,
            "one_day_pct": round(100 * one_day / len(spans)) if spans else 0,
            "top_item": s["top"],
        }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"sources.json: {len(out['sources'])} sources over {len(all_days)} days")


if __name__ == "__main__":
    main()
