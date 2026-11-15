#!/usr/bin/env python3
"""Weekly aggregate API — writes docs/api/week.json: the rolling last-N-days
top board by cumulative daily-normalized heat (same metric as week.html) plus
per-topic counts over the window. Runs after collect in the daily workflow."""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(ROOT, "data", "history.csv")
TOPICS_HIST = os.path.join(ROOT, "data", "topics-history.csv")
def out_file(name):
    return os.path.join(ROOT, "docs", "api", name)


def build(recs, days, window, name):
    win = set(days[-window:])
    wk = [r for r in recs if r["date"] in win]

    mx = {}
    for r in wk:
        k = (r["date"], r["source"])
        try:
            mx[k] = max(mx.get(k, 0), float(r["score"] or 0))
        except ValueError:
            mx[k] = mx.get(k, 0)

    by_url = {}
    for r in wk:
        key = r["url"] or r["title"]
        e = by_url.setdefault(key, {
            "title": r["title"], "url": r["url"], "source": r["source"],
            "metric": r["metric"], "heat": 0.0, "days": set(), "best_rank": 99,
        })
        try:
            score = float(r["score"] or 0)
        except ValueError:
            score = 0.0
        e["heat"] += score / (mx.get((r["date"], r["source"])) or 1)
        e["days"].add(r["date"])
        try:
            e["best_rank"] = min(e["best_rank"], int(r["rank"] or 99))
        except ValueError:
            pass

    top = sorted(by_url.values(), key=lambda e: -e["heat"])[:50]
    for e in top:
        e["days_on_board"] = len(e.pop("days"))
        e["heat"] = round(e["heat"], 2)

    topics = []
    if os.path.exists(TOPICS_HIST):
        with open(TOPICS_HIST, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["date"] in win:
                    topics.append({"topic": r["topic"], "count": int(r["count"])})
    tacc = {}
    for t in topics:
        tacc[t["topic"]] = tacc.get(t["topic"], 0) + t["count"]

    doc = {
        "generated": days[-1] if days else None,
        "window_days": len(win),
        "from": min(win) if win else None,
        "to": max(win) if win else None,
        "items_in_window": len(wk),
        "unique_urls": len(by_url),
        "top": top,
        "topics": [{"topic": k, "count": v} for k, v in
                   sorted(tacc.items(), key=lambda x: -x[1])],
    }
    os.makedirs(os.path.dirname(out_file("x")), exist_ok=True)
    with open(out_file(name), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"{name}: {len(top)} top / {len(tacc)} topics / {len(wk)} items over {len(win)}d")


def main():
    with open(HISTORY, newline="", encoding="utf-8") as f:
        recs = list(csv.DictReader(f))
    days = sorted({r["date"] for r in recs})
    for window, name in ((7, "week.json"), (30, "month.json")):
        build(recs, days, window, name)


if __name__ == "__main__":
    main()
