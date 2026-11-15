#!/usr/bin/env python3
"""Risers → docs/api/risers.json: biggest single-day score spikes (non-rolling
sources), package rank jumps (rolling sources) and sustained climbers still on
the board. Same semantics as risers.html. Updated daily by the collect
workflow."""

import csv
import json
import os
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
OUT = os.path.join(ROOT, "docs", "api", "risers.json")
ROLLING = {"npm", "pypi", "crates"}


def main():
    items = defaultdict(lambda: {"title": "", "source": "", "url": "", "obs": []})
    days = set()
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
        try:
            it["obs"].append({"date": d, "score": int(row.get("score") or 0),
                              "rank": int(row.get("rank") or 99)})
        except ValueError:
            continue

    latest = max(days) if days else None

    def prev_day(d):
        return (date.fromisoformat(d) - timedelta(days=1)).isoformat()

    spikes, jumps, climbers = [], [], []
    for it in items.values():
        it["obs"].sort(key=lambda o: o["date"])
        obs = it["obs"]
        base = {k: it[k] for k in ("title", "source", "url")}
        for i in range(1, len(obs)):
            p, c = obs[i - 1], obs[i]
            if prev_day(c["date"]) != p["date"]:
                continue
            if it["source"] in ROLLING:
                j = p["rank"] - c["rank"]
                if j > 0:
                    jumps.append({**base, "date": c["date"], "jump": j,
                                  "from_rank": p["rank"], "to_rank": c["rank"]})
            else:
                d = c["score"] - p["score"]
                if d > 0:
                    spikes.append({**base, "date": c["date"], "delta": d,
                                   "from_score": p["score"], "to_score": c["score"]})
        if (it["source"] not in ROLLING and len(obs) >= 2
                and latest and obs[-1]["date"] == latest):
            gain = obs[-1]["score"] - obs[0]["score"]
            if gain > 0:
                climbers.append({**base, "gain": gain, "days_tracked": len(obs)})

    spikes.sort(key=lambda x: -x["delta"])
    jumps.sort(key=lambda x: -x["jump"])
    climbers.sort(key=lambda x: -x["gain"])

    out = {
        "generated_at": date.today().isoformat(),
        "latest_snapshot": latest,
        "single_day_spikes": spikes[:50],
        "package_rank_jumps": jumps[:50],
        "sustained_climbers": climbers[:50],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"risers.json: {len(spikes)} spikes, {len(jumps)} jumps, {len(climbers)} climbers")


if __name__ == "__main__":
    main()
