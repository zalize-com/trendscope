#!/usr/bin/env python3
"""trendscope — today's developer board, in your terminal.

    curl -sL https://zalize-com.github.io/trendscope/trendscope.py | python3 -
    python3 trendscope.py --source hackernews -n 5
    python3 trendscope.py --movers     # what entered/left the board today
    python3 trendscope.py --week       # top of the last 7 days

Zero dependencies (stdlib only). Reads the open dataset directly from
GitHub Pages. Data is CC0 — do whatever you want with it.
"""

import argparse
import csv
import io
import json
import os
import sys
import urllib.request

# TRENDSCOPE_BASE lets forks/mirrors serve their own copy of the dataset.
BASE = os.environ.get("TRENDSCOPE_BASE", "https://zalize-com.github.io/trendscope").rstrip("/")
UA = "trendscope-cli/1.0"


def fetch(path, binary=False):
    try:
        req = urllib.request.Request(f"{BASE}/{path}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        return data if binary else data.decode("utf-8")
    except Exception:
        # fall back to the local dataset when running inside the repo
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if os.path.exists(local):
            with open(local, "rb") as f:
                data = f.read()
            return data if binary else data.decode("utf-8")
        raise


def fmt(n):
    n = float(n)
    for u in (1e9, 1e6, 1e3):
        if n >= u:
            return f"{n/u:.1f}{'BMK'[(u == 1e6) + 2 * (u == 1e3)]}"
    return str(int(n))


def board(args):
    snap = json.loads(fetch("data/latest.json"))
    print(f"trendscope — {snap['date']} snapshot")
    rows = []
    maxs = {s: (its[0]["score"] or 1) for s, its in snap["items"].items()}
    for s, its in snap["items"].items():
        if args.source and s != args.source:
            continue
        for it in its:
            rows.append((it["score"] / (maxs[s] or 1), s, it))
    rows.sort(key=lambda x: -x[0])
    for i, (heat, s, it) in enumerate(rows[:args.n], 1):
        print(f"{i:>3}. [{s}] {it['title'][:72]}")
        print(f"      {fmt(it['score'])} {it['metric']}  {it['url']}")
    return 0


def movers(_args):
    m = json.loads(fetch("docs/api/movers-latest.json"))
    print(f"trendscope movers — {m['a']} → {m['b']}")
    for key, label in (("entered", "ENTERED"), ("left", "LEFT"),
                       ("gainers", "GAINERS"), ("droppers", "DROPPERS")):
        rows = m.get(key) or []
        if not rows:
            continue
        print(f"\n== {label} ==")
        for it in rows[:10]:
            delta = f" (+{it.get('delta')})" if it.get("delta") else ""
            print(f"  [{it['source']}] {it['title'][:72]}{delta}")
    return 0


def week(_args):
    data = fetch("data/history.csv", binary=True).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(data)))
    days = sorted({r["date"] for r in rows})[-7:]
    wk = [r for r in rows if r["date"] in set(days)]
    mx = {}
    for r in wk:
        k = (r["date"], r["source"])
        mx[k] = max(mx.get(k, 0), float(r["score"] or 0))
    by_url = {}
    for r in wk:
        e = by_url.setdefault(r["url"], {"title": r["title"], "source": r["source"],
                                         "total": 0, "days": set(), "metric": r["metric"]})
        e["total"] += float(r["score"] or 0) / (mx.get((r["date"], r["source"])) or 1)
        e["days"].add(r["date"])
    print(f"trendscope week — {days[0]} → {days[-1]}")
    for i, e in enumerate(
            sorted(by_url.values(), key=lambda x: -x["total"])[:20], 1):
        print(f"{i:>3}. [{e['source']}] {e['title'][:68]} "
              f"({e['total']:.1f} heat, {len(e['days'])}d)")
    return 0


def canon(_args):
    data = fetch("data/hn-canon-monthly.csv", binary=True).decode("utf-8")
    rows = [r for r in csv.DictReader(io.StringIO(data)) if r.get("points")]
    top = sorted(rows, key=lambda r: -int(r["points"]))[:20]
    print(f"trendscope canon — HN all-time top (of {len(rows)} stories, 2007→today)")
    for i, r in enumerate(top, 1):
        print(f"{i:>3}. {r['title'][:72]}")
        print(f"      {fmt(int(r['points']))} pts · {r['month']}  {r['hn_url']}")
    return 0


def hiring(_args):
    h = json.loads(fetch("data/hiring.json"))
    t = h.get("threads", {})
    hire, seek, free = t.get("hiring"), t.get("seeking"), t.get("freelancer")
    month = (hire or seek or free or {}).get("month", "")
    print(f"trendscope hiring pulse — {month}")
    for label, th in (("hiring", hire), ("seeking", seek), ("freelancer", free)):
        if th:
            print(f"  {label:<10} {fmt(th['comments']):>6} comments   {th['url']}")
    if hire and seek:
        print(f"  ratio      {hire['comments']/seek['comments']:.2f} positions per seeker")
    return 0


def main():
    p = argparse.ArgumentParser(description="trendscope — the developer attention dataset, in your terminal")
    p.add_argument("-n", type=int, default=15, help="rows to show (board mode)")
    p.add_argument("--source", help="one source only, e.g. hackernews")
    p.add_argument("--movers", action="store_true", help="today's board changes")
    p.add_argument("--week", action="store_true", help="last-7-day cumulative top")
    p.add_argument("--canon", action="store_true", help="HN all-time top stories")
    p.add_argument("--hiring", action="store_true", help="HN who-is-hiring pulse")
    args = p.parse_args()
    try:
        if args.movers:
            return movers(args)
        if args.week:
            return week(args)
        if args.canon:
            return canon(args)
        if args.hiring:
            return hiring(args)
        return board(args)
    except Exception as e:
        print(f"trendscope: fetch failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
