#!/usr/bin/env python3
"""TrendScope daily brief — rule-based prose summary of a day's snapshot.

Usage: python3 scripts/brief.py [YYYY-MM-DD]   (default: latest snapshot)
Writes docs/brief/YYYY-MM-DD.md and prints it to stdout.
"""

import csv
import glob
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DOCS_DIR = os.path.join(ROOT, "docs", "brief")
ROLLING = {"npm", "pypi", "crates"}


def load_history():
    path = os.path.join(DATA_DIR, "history.csv")
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, newline="")))


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "daily", "????-??-??.json")))
    date = sys.argv[1] if len(sys.argv) > 1 else (os.path.basename(files[-1])[:10] if files else None)
    if not date:
        print("no daily snapshots", file=sys.stderr)
        sys.exit(1)

    hist = load_history()
    today = [r for r in hist if r["date"] == date]
    if not today:
        print(f"no history rows for {date}", file=sys.stderr)
        sys.exit(1)
    dates = sorted({r["date"] for r in hist})
    i = dates.index(date)
    prev = dates[i - 1] if i else None
    yest = [r for r in hist if r["date"] == prev] if prev else []
    yurls = {r["url"] for r in yest}

    srcs = Counter(r["source"] for r in today)
    non_rolling = [r for r in today if r["source"] not in ROLLING]
    top = max(non_rolling, key=lambda r: int(r["score"] or 0)) if non_rolling else None
    new_items = [r for r in today if r["url"] not in yurls]
    new_items.sort(key=lambda r: -int(r["score"] or 0))

    # biggest gainers (non-rolling sources only)
    ymap = {r["url"]: int(r["score"] or 0) for r in yest}
    gains = []
    for r in today:
        if r["source"] in ROLLING:
            continue
        d = int(r["score"] or 0) - ymap.get(r["url"], 0)
        if d > 0 and r["url"] in yurls:
            gains.append((d, r))
    gains.sort(key=lambda x: -x[0])

    # streaks: urls on board 3+ consecutive days ending today
    streaks = []
    by_url = defaultdict(list)
    for r in hist:
        by_url[r["url"]].append(r["date"])
    def prevday(d):
        from datetime import date as dt, timedelta
        y, m, dd = map(int, d.split("-"))
        return str(dt(y, m, dd) - timedelta(days=1))
    for r in today:
        ds = sorted(by_url[r["url"]])
        n = 0
        d = date
        while d in ds:
            n += 1
            d = prevday(d)
        if n >= 3:
            streaks.append((n, r))
    streaks.sort(key=lambda x: -x[0])

    L = []
    L.append(f"# Daily brief — {date}\n")
    L.append(f"_{len(today)} items across {len(srcs)} sources · {len(new_items)} new entries vs {prev or 'n/a'}_\n")
    if top:
        L.append(f"**Top story:** [{top['title']}]({top['url']}) — {top['score']} {top['metric']} on {top['source']}.\n")
    if gains:
        g, r = gains[0]
        L.append(f"**Biggest climber:** [{r['title']}]({r['url']}) (+{g} {r['metric']} vs yesterday).\n")
    if new_items:
        L.append("**Notable new entries:** " + "; ".join(
            f"[{r['title'][:70]}]({r['url']}) ({r['source']}, {r['score']} {r['metric']})"
            for r in new_items[:5]) + ".\n")
    if streaks:
        L.append("**Staying power (3+ days on board):** " + "; ".join(
            f"[{r['title'][:60]}]({r['url']}) {n}d" for n, r in streaks[:5]) + ".\n")
    L.append("\n**Source mix:** " + " · ".join(f"{s} {n}" for s, n in srcs.most_common()) + "\n")
    L.append("\n---\nData: [history.csv](../../data/history.csv) · "
             "[dashboard](../../index.html?day=" + date + ") · "
             "[movers](../../docs/api/movers-" + date + ".json)\n")

    out = "\n".join(L)
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, f"{date}.md")
    open(path, "w").write(out)
    print(path)
    print(out)


if __name__ == "__main__":
    main()
