#!/usr/bin/env python3
"""Daily movers — writes docs/movers/YYYY-MM-DD.md: what entered the board,
what left, and the biggest score movers vs the previous snapshot."""

import json
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "daily")
OUT = os.path.join(ROOT, "docs", "movers")


def fmt(n):
    a = abs(n)
    s = "-" if n < 0 else ""
    if a >= 1e9:
        return f"{s}{a/1e9:.1f}B"
    if a >= 1e6:
        return f"{s}{a/1e6:.1f}M"
    if a >= 1e3:
        return f"{s}{a/1e3:.1f}k"
    return str(n)


def load(day):
    p = os.path.join(DAILY, f"{day}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def flat(snap):
    return {i["url"]: i for its in (snap.get("items") or {}).values() for i in its}


def rows(items, badge, fmt_score, limit=15):
    out = []
    for it, extra in items[:limit]:
        out.append(f"- {badge} [{it['title']}]({it['url']}) "
                   f"`{it['source']}` — {fmt_score(it, extra)}")
    return "\n".join(out) or "- _(none)_"


def main():
    os.makedirs(OUT, exist_ok=True)
    days = sorted(f[:-5] for f in os.listdir(DAILY) if f.endswith(".json"))
    if len(days) < 2:
        print("need 2+ snapshots; skipping")
        return
    day_b, day_a = days[-1], days[-2]
    sa, sb = load(day_a), load(day_b)
    A, B = flat(sa), flat(sb)

    enter = [i for u, i in B.items() if u not in A]
    exit_ = [i for u, i in A.items() if u not in B]
    movers = [(i, i["score"] - A[u]["score"]) for u, i in B.items() if u in A]
    enter.sort(key=lambda i: -i["score"])
    exit_.sort(key=lambda i: -i["score"])
    gainers = sorted(movers, key=lambda m: -m[1])
    droppers = sorted(movers, key=lambda m: m[1])

    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# Movers — {day_b}",
          f"",
          f"_{day_a} → {day_b} · {len(A)} → {len(B)} tracked URLs · "
          f"generated {gen}_",
          f"",
          f"**+{len(enter)}** entered · **−{len(exit_)}** left · "
          f"**{len(movers)}** persisted",
          f"",
          f"## Biggest gainers",
          rows(gainers, "", lambda i, d: f"{fmt(A[i['url']]['score'])} → "
                                       f"**+{fmt(d)}** {i['metric']}" if d > 0
                                       else f"{fmt(d)} {i['metric']}"),
          f"",
          f"## New on the board",
          rows([(i, None) for i in enter], "🆕 ", lambda i, _: f"{fmt(i['score'])} {i['metric']}"),
          f"",
          f"## Biggest droppers",
          rows(droppers[:10], "", lambda i, d: f"{fmt(d)} {i['metric']}"),
          f"",
          f"## Left the board",
          rows([(i, None) for i in exit_], "", lambda i, _: f"{fmt(i['score'])} {i['metric']} (was)"),
          f"",
          f"---",
          f"[interactive view](https://zalize-com.github.io/trendscope/compare.html"
          f"?a={day_a}&b={day_b}) · data: `data/daily/{day_b}.json` (CC0)",
          f""]
    path = os.path.join(OUT, f"{day_b}.md")
    with open(path, "w") as f:
        f.write("\n".join(md))
    print(f"wrote docs/movers/{day_b}.md (+{len(enter)}/-{len(exit_)}/{len(movers)})")


if __name__ == "__main__":
    main()
