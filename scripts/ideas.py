#!/usr/bin/env python3
"""Ideas API — clusters ask_hn demand threads from history.csv into
docs/api/ideas-latest.json. Mirrors the client-side logic in ideas.html so
consumers get the same demand signals as structured data."""

import csv
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
OUT = os.path.join(ROOT, "docs", "api", "ideas-latest.json")

STOP = set(("a an the is are was were be been what which who whom how when where why do does did "
            "can could should would will shall may might must i you he she it we they me him her us them my your its our their "
            "this that these those there here to of in on at for with about as by from or and but if not no so too very just "
            "any some all one two get got have has had hn ask tell show self best new more much most now today use used using "
            "name something anything everything nothing someone anyone everyone like make made take look people really also "
            "start started down done doing run running want wanted stuff thing things way ways good great big small old "
            "advice ideas idea question questions anyone build builds built state future 2026").split())
SKIP = re.compile(r"^(ask hn|tell hn|show hn|hn)[:?]?\s*", re.I)


def tokens(title):
    words = [w for w in re.split(r"[^a-z0-9]+", SKIP.sub("", title).lower())
             if len(w) > 2 and w not in STOP and not w.isdigit()]
    return words + [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]


def main():
    if not os.path.exists(HIST):
        print("no history.csv; skipping")
        return
    rows = list(csv.DictReader(open(HIST)))
    asks, others = {}, []
    for r in rows:
        if r["source"] == "ask_hn":
            it = asks.setdefault(r["url"], {"title": r["title"], "days": set(), "max_score": 0})
            it["days"].add(r["date"])
            it["max_score"] = max(it["max_score"], int(float(r["score"] or 0)))
        elif r["url"]:
            others.append({"title": r["title"], "url": r["url"], "source": r["source"],
                           "score": int(float(r["score"] or 0))})

    threads = [{"url": u, "title": it["title"], "days_on_board": len(it["days"]),
                "max_score": it["max_score"]} for u, it in asks.items()]

    tok_map = {}
    for t in threads:
        for tok in set(tokens(t["title"])):
            tok_map.setdefault(tok, set()).add(t["url"])

    by_url = {t["url"]: t for t in threads}
    themes = []
    for name, urls in tok_map.items():
        if len(urls) < (2 if " " in name else 3):
            continue
        cov = [o for o in others
               if all(w in o["title"].lower() for w in name.split())]
        cov.sort(key=lambda o: -o["score"])
        themes.append({
            "theme": name,
            "threads": [by_url[u] for u in urls],
            "score": sum(by_url[u]["max_score"] for u in urls),
            "coverage": {"built": bool(cov), "top_hit": cov[0] if cov else None},
        })
    themes.sort(key=lambda th: -th["score"])

    seen = set()
    deduped = []
    for th in themes:
        fresh = [t for t in th["threads"] if t["url"] not in seen]
        if not fresh:
            continue
        th["threads"] = fresh
        deduped.append(th)
        seen.update(t["url"] for t in fresh)
    deduped = deduped[:10]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "unique_threads": len(threads),
        "themes": deduped,
        "top_asks": sorted(threads, key=lambda t: -t["max_score"])[:15],
    }, open(OUT, "w"), indent=2)
    print(f"wrote {OUT} ({len(threads)} threads, {len(deduped)} themes)")


if __name__ == "__main__":
    main()
