#!/usr/bin/env python3
"""TrendScope weekly digest — summarizes history.csv into a markdown report.

Usage: python3 scripts/digest.py [days]   (default 7)
Writes docs/digest/YYYY-Www.md and prints it to stdout.
"""

import csv
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "digest")


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    history = os.path.join(DATA_DIR, "history.csv")
    if not os.path.exists(history):
        print("no history.csv yet", file=sys.stderr)
        sys.exit(1)

    rows = list(csv.DictReader(open(history, newline="")))
    if not rows:
        print("history.csv has no rows yet", file=sys.stderr)
        sys.exit(1)
    dates = sorted({r["date"] for r in rows})[-days:]
    rows = [r for r in rows if r["date"] in dates]

    by_source = defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r)

    # velocity: score delta between first and last appearance per url
    first, last = {}, {}
    for r in rows:
        key = (r["source"], r["url"])
        if key not in first:
            first[key] = r
        last[key] = r
    movers = []
    for key, f in first.items():
        l = last[key]
        if f["date"] != l["date"]:
            gain = int(l["score"]) - int(f["score"])
            if gain > 0:
                movers.append((gain, l))
    movers.sort(key=lambda x: -x[0])

    tags = Counter()
    for r in rows:
        for t in (r.get("tags") or "").split("|"):
            if t and not t.startswith(("author_", "story_", "poll_")):
                tags[t] += 1

    year, week = datetime.now(timezone.utc).isocalendar()[:2]
    title = f"trendscope weekly — {year}-W{week:02d}"
    out = [f"# {title}\n",
           f"Window: {dates[0]} → {dates[-1]} · {len(rows)} items · "
           f"{len(by_source)} sources\n"]

    out.append("## Top movers (score gained over window)\n")
    for gain, r in movers[:15]:
        out.append(f"- **+{int(r['score']) - int(first[(r['source'], r['url'])]['score']):,}** "
                   f"{r['metric']} — [{r['title']}]({r['url']})  `{r['source']}`")
    if not movers:
        out.append("- (needs ≥2 snapshots)")
    out.append("")

    out.append("## Top per source\n")
    for src, items in sorted(by_source.items()):
        latest_date = max(i["date"] for i in items)
        top = sorted((i for i in items if i["date"] == latest_date),
                     key=lambda x: -int(x["score"]))[:5]
        out.append(f"### {src}")
        for i in top:
            out.append(f"- {int(i['score']):,} {i['metric']} — [{i['title']}]({i['url']})")
        out.append("")

    out.append("## Hot tags\n")
    out.append(" · ".join(f"`{t}` ({c})" for t, c in tags.most_common(20)))
    out.append("")

    text = "\n".join(out)
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, f"{year}-W{week:02d}.md")
    with open(path, "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
