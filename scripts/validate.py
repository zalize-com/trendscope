#!/usr/bin/env python3
"""Dataset contract checks — runs after collect.py in CI.

Fails (exit 1) if the public data files violate the documented schema,
so a broken snapshot never ships silently to consumers.
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEM_FIELDS = {"source", "rank", "title", "url", "score", "metric"}
HIST_HEADER = ["date", "source", "rank", "title", "url", "score",
               "metric", "comments", "author", "tags", "captured_at"]

errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    # latest.json: required keys + item shape
    latest = json.load(open(os.path.join(ROOT, "data", "latest.json")))
    for k in ("date", "generated_at", "sources", "items"):
        check(k in latest, f"latest.json missing key {k!r}")
    check(len(latest.get("items", {})) >= 5,
          f"latest.json has {len(latest.get('items', {}))} sources (<5)")
    for src, items in latest.get("items", {}).items():
        check(len(items) > 0, f"source {src!r} is empty")
        for it in items:
            missing = ITEM_FIELDS - set(it)
            check(not missing, f"{src} item missing fields {missing}: {it.get('title','?')[:50]}")
            check(isinstance(it.get("score"), (int, float)),
                  f"{src} score not numeric: {it.get('title','?')[:50]}")

    # data/daily/<today>.json exists
    day = latest["date"]
    check(os.path.exists(os.path.join(ROOT, "data", "daily", f"{day}.json")),
          f"daily/{day}.json missing")

    # history.csv: header + today's rows present
    with open(os.path.join(ROOT, "data", "history.csv")) as f:
        rd = csv.reader(f)
        header = next(rd)
        check(header == HIST_HEADER, f"history.csv header drifted: {header}")
        today = sum(1 for r in rd if r and r[0] == day)
        check(today > 0, f"history.csv has no rows for {day}")

    # health.json: every collected source reported ok
    health = json.load(open(os.path.join(ROOT, "data", "health.json")))
    for src, h in health.get("sources", {}).items():
        check(h.get("ok"), f"health.json: {src} not ok")
        check(h.get("items", 0) > 0, f"health.json: {src} reports 0 items")

    # docs/api JSON endpoints parse
    for p in ("docs/api/stats.json", "docs/api/movers-latest.json",
              "docs/api/ideas-latest.json", "docs/api/badge.json",
              "feed.xml", "feed.json"):
        fp = os.path.join(ROOT, p)
        check(os.path.exists(fp), f"{p} missing")
    json.load(open(os.path.join(ROOT, "docs/api/stats.json")))

    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors[:20]:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK — {len(latest['items'])} sources, "
          f"{sum(len(v) for v in latest['items'].values())} items, "
          f"{today} history rows for {day}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
