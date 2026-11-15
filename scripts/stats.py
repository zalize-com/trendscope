#!/usr/bin/env python3
"""docs/api/stats.json — dataset-level summary stats (days, rows, sources,
fresh counts). Consumable metadata for integrators and the site footer."""

import csv
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = os.path.join(ROOT, "docs", "api")


def main():
    os.makedirs(API, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(DATA, "history.csv"))))
    days = sorted({r["date"] for r in rows})
    per_src, src_days, urls = {}, {}, set()
    for r in rows:
        per_src[r["source"]] = per_src.get(r["source"], 0) + 1
        src_days.setdefault(r["source"], set()).add(r["date"])
        urls.add(r["url"])

    green = 0
    hlog = os.path.join(DATA, "health-log.csv")
    if os.path.exists(hlog):
        by_day = {}
        for r in csv.DictReader(open(hlog)):
            by_day.setdefault(r["date"], True)
            by_day[r["date"]] = by_day[r["date"]] and r["ok"] == "1"
        for d in sorted(by_day, reverse=True):
            if not by_day[d]:
                break
            green += 1

    latest = json.load(open(os.path.join(DATA, "latest.json")))
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days_tracked": len(days),
        "first_day": days[0] if days else None,
        "latest_day": days[-1] if days else None,
        "total_rows": len(rows),
        "unique_urls": len(urls),
        "items_in_latest": latest.get("total_items"),
        "sources": {s: {"rows": per_src[s], "days_active": len(src_days[s])}
                    for s in sorted(per_src)},
        "all_green_days": green,
    }
    out = os.path.join(API, "stats.json")
    with open(out, "w") as f:
        json.dump(doc, f, indent=1)
    print(f"wrote {os.path.relpath(out, ROOT)} "
          f"({doc['days_tracked']}d, {doc['total_rows']} rows, "
          f"{doc['unique_urls']} urls)")


if __name__ == "__main__":
    main()
