#!/usr/bin/env python3
"""Aggregates → docs/api/{domains,authors,discussed}.json: leaderboards the
site computes client-side, published as endpoints.
Same semantics as the matching pages. Daily via collect workflow."""

import csv
import json
import os
from collections import defaultdict
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.csv")
API = os.path.join(ROOT, "docs", "api")

ROLLING = {"npm", "pypi", "crates"}
SKIP = {"news.ycombinator.com", "github.com", "www.npmjs.com", "pypi.org",
        "crates.io", "dev.to", "lobste.rs"}
LIMIT = 50


def host_of(url):
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def main():
    days = set()
    doms = defaultdict(lambda: {"hits": 0, "days": set(), "srcs": set(), "top": None})
    authors = defaultdict(lambda: {"hits": 0, "days": set(), "srcs": set(), "top": None})
    items = {}  # url -> best comment-bearing row
    series = {}  # url -> {"title","source","metric","days": {date: score}}
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        url = r.get("url") or ""
        d = r.get("date") or ""
        if not url or not d:
            continue
        days.add(d)
        score = int(float(r.get("score") or 0))
        hit = {"title": r["title"], "url": url, "score": score,
               "metric": r.get("metric") or "", "date": d}
        se = series.setdefault(url, {"title": r["title"], "source": r["source"],
                                     "metric": r.get("metric") or "", "days": {}})
        se["days"][d] = max(score, se["days"].get(d, 0))

        h = host_of(url)
        if h:
            h = h[4:] if h.startswith("www.") else h
            if h not in SKIP:
                dm = doms[h]
                dm["hits"] += 1
                dm["days"].add(d)
                dm["srcs"].add(r["source"])
                if not dm["top"] or score > dm["top"]["score"]:
                    dm["top"] = hit

        comments = int(float(r.get("comments") or 0))
        if comments:
            cur = items.get(url)
            if not cur or comments > cur["comments"]:
                items[url] = {"title": r["title"], "url": url,
                              "score": score, "comments": comments,
                              "metric": r.get("metric") or "",
                              "source": r["source"], "date": d,
                              "author": r.get("author") or ""}

        who = (r.get("author") or "").strip()
        if who:
            a = authors[who]
            a["hits"] += 1
            a["days"].add(d)
            a["srcs"].add(r["source"])
            if not a["top"] or score > a["top"]["score"]:
                a["top"] = hit

    def pack(rows, key):
        return [{
            key: k,
            "days_on_board": len(v["days"]),
            "items": v["hits"],
            "sources": sorted(v["srcs"]),
            "top_hit": v["top"],
        } for k, v in sorted(rows.items(),
                            key=lambda kv: (-len(kv[1]["days"]), -kv[1]["hits"]))[:LIMIT]]

    now = datetime.now(timezone.utc).isoformat()
    for name, data in (("domains", pack(doms, "hostname")),
                       ("authors", pack(authors, "author"))):
        out = {"generated_at": now, "latest_snapshot": max(days),
               "total": len(doms if name == "domains" else authors),
               name: data}
        with open(os.path.join(API, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"{name}.json: {len(data)} rows / {out['total']} total")

    # crossovers: same normalized URL on ≥2 different sources
    xo = defaultdict(lambda: {"title": "", "sources": set(), "days": set(),
                             "best": {"score": 0, "metric": "", "source": "", "date": ""}})
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        url = (r.get("url") or "").strip()
        if not url:
            continue
        p = urlparse(url.lower())
        h = p.hostname or ""
        h = h[4:] if h.startswith("www.") else h
        if h in SKIP:
            continue
        qs = urlencode([(k, v) for k, v in parse_qsl(p.query)
                        if not k.startswith("utm_")])
        key = urlunparse((p.scheme or "https", p.netloc, p.path.rstrip("/"),
                          "", qs, ""))
        score = int(float(r.get("score") or 0))
        e = xo[key]
        e["title"] = r["title"]
        e["sources"].add(r["source"])
        e["days"].add(r.get("date") or "")
        if score > e["best"]["score"]:
            e["best"] = {"score": score, "metric": r.get("metric") or "",
                         "source": r["source"], "date": r.get("date") or ""}
    cross = sorted(({"url": k, "title": v["title"], "sources": sorted(v["sources"]),
                     "days": len(v["days"]), "best": v["best"]}
                    for k, v in xo.items() if len(v["sources"]) >= 2),
                   key=lambda x: (-len(x["sources"]), -x["days"], -x["best"]["score"]))[:LIMIT]
    with open(os.path.join(API, "crossovers.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": max(days),
                   "crossovers": cross}, f, ensure_ascii=False, indent=1)
    print(f"crossovers.json: {len(cross)} rows")

    # new today: latest-date rows whose (source,url) never appeared on an earlier date
    first_seen = set()
    latest_rows = []
    maxday = max(days)
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        d, src, url = r.get("date") or "", r.get("source") or "", r.get("url") or ""
        if not url:
            continue
        if d < maxday:
            first_seen.add((src, url))
        elif d == maxday:
            latest_rows.append(r)
    new_items = sorted(
        ({"title": r["title"], "url": r["url"], "source": r["source"],
          "rank": int(float(r.get("rank") or 0)),
          "score": int(float(r.get("score") or 0)),
          "metric": r.get("metric") or ""}
         for r in latest_rows if (r["source"], r["url"]) not in first_seen),
        key=lambda x: (x["source"], x["rank"]))
    by_src = {}
    for i in new_items:
        by_src[i["source"]] = by_src.get(i["source"], 0) + 1
    with open(os.path.join(API, "new.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": maxday,
                   "total_items": len(latest_rows), "new_items": len(new_items),
                   "by_source": dict(sorted(by_src.items(), key=lambda x: -x[1])),
                   "items": new_items}, f, ensure_ascii=False, indent=1)
    print(f"new.json: {len(new_items)}/{len(latest_rows)} first-seen")

    # velocity: score growth per day for urls seen on 2+ dates
    vel = []
    for url, o in series.items():
        if o["source"] in ROLLING:
            continue
        ds = sorted(o["days"])
        if len(ds) < 2:
            continue
        first, last = o["days"][ds[0]], o["days"][ds[-1]]
        span = max(1, (datetime.fromisoformat(ds[-1]) - datetime.fromisoformat(ds[0])).days)
        vel.append({"url": url, "title": o["title"], "source": o["source"],
                    "metric": o["metric"], "days": len(ds),
                    "delta": last - first,
                    "per_day": round((last - first) / span, 1),
                    "latest": last})
    vel.sort(key=lambda x: -x["per_day"])
    with open(os.path.join(API, "velocity.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": max(days),
                   "total": len(vel), "items": vel[:LIMIT]},
                  f, ensure_ascii=False, indent=1)
    print(f"velocity.json: {len(vel)} multi-day items")

    # weekday: day-of-week x source item counts (UTC weekday of the snapshot date)
    grid = defaultdict(lambda: [0] * 7)
    totals = defaultdict(int)
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        d, src = r.get("date") or "", r.get("source") or ""
        if not d or not src:
            continue
        try:
            w = (datetime.fromisoformat(d).weekday())  # 0=Mon
        except ValueError:
            continue
        grid[src][w] += 1
        totals[src] += 1
    DOW = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    with open(os.path.join(API, "weekday.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": max(days),
                   "days_of_week": DOW,
                   "sources": {s: {"counts": grid[s], "total": totals[s]}
                               for s in sorted(totals, key=lambda k: -totals[k])}},
                  f, ensure_ascii=False, indent=1)
    print(f"weekday.json: {len(grid)} sources x 7 days")

    discussed = sorted(items.values(), key=lambda x: -x["comments"])[:LIMIT]
    heated = sorted((x for x in items.values() if x["score"] >= 50),
                    key=lambda x: -x["comments"] / max(1, x["score"]))[:LIMIT]
    out = {"generated_at": now, "latest_snapshot": max(days),
           "total": len(items),
           "discussed": discussed, "heated": heated}
    with open(os.path.join(API, "discussed.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"discussed.json: {len(discussed)}+{len(heated)} rows / {out['total']} total")


if __name__ == "__main__":
    main()
