#!/usr/bin/env python3
"""Streaks → docs/api/streaks.json: items currently on the board for 2+
consecutive days, plus the all-time longest runs. Same semantics as
streaks.html. Updated daily by the collect workflow."""

import csv
import json
import os
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
OUT = os.path.join(ROOT, "docs", "api", "streaks.json")


def main():
    days = set()
    items = defaultdict(lambda: {"title": "", "source": "", "url": "",
                                 "days": set(), "top_score": 0, "top_rank": 99})
    for row in csv.DictReader(open(HIST, encoding="utf-8")):
        url = row.get("url")
        d = row.get("date")
        if not url or not d:
            continue
        days.add(d)
        it = items[url]
        it["title"] = row["title"]
        it["source"] = row["source"]
        it["url"] = url
        it["days"].add(d)
        try:
            sc = int(row.get("score") or 0)
            rk = int(row.get("rank") or 99)
        except ValueError:
            continue
        if sc > it["top_score"]:
            it["top_score"], it["top_rank"] = sc, rk

    latest = max(days) if days else None

    def streak_from(day_set, end):
        n, d = 0, end
        while d.isoformat() in day_set:
            n += 1
            d -= timedelta(days=1)
        return n

    active, longest = [], []
    end = date.fromisoformat(latest) if latest else None
    for it in items.values():
        if end:
            cur = streak_from(it["days"], end)
            if cur >= 2:
                active.append({**{k: it[k] for k in ("title", "source", "url", "top_score", "top_rank")},
                               "consecutive_days": cur})
        # longest run anywhere in its history
        run = best = 0
        ds = sorted(it["days"])
        prev = None
        for d in ds:
            cur_d = date.fromisoformat(d)
            run = run + 1 if prev and (cur_d - prev).days == 1 else 1
            best = max(best, run)
            prev = cur_d
        if best >= 2:
            longest.append({**{k: it[k] for k in ("title", "source", "url")},
                            "longest_streak": best})

    active.sort(key=lambda x: (-x["consecutive_days"], -x["top_score"]))
    longest.sort(key=lambda x: -x["longest_streak"])

    out = {
        "generated_at": date.today().isoformat(),
        "latest_snapshot": latest,
        "active": active[:50],
        "longest_all_time": longest[:50],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"streaks.json: {len(active)} active, {len(longest)} with 2d+ runs")


if __name__ == "__main__":
    main()
