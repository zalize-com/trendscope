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
                                     "metric": r.get("metric") or "", "days": {},
                                     "ranks": {}, "comments": {}, "author": ""})
        se["days"][d] = max(score, se["days"].get(d, 0))
        rk = int(float(r.get("rank") or 99))
        se["ranks"][d] = min(rk, se["ranks"].get(d, 99))
        cm = int(float(r.get("comments") or 0))
        se["comments"][d] = max(cm, se["comments"].get(d, 0))
        se["author"] = r.get("author") or se["author"]

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

    ser_items = {}
    for url, o in series.items():
        ser_items[url] = {"title": o["title"], "source": o["source"],
                          "metric": o["metric"], "author": o["author"],
                          "days": {d: [o["days"][d], o["ranks"].get(d, 99),
                                       o["comments"].get(d, 0)]
                                   for d in sorted(o["days"])}}
    with open(os.path.join(API, "series.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": max(days),
                   "days_tracked": len(days), "total_items": len(ser_items),
                   "items": ser_items}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"series.json: {len(ser_items)} items")
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
                   "days_tracked": len(days),
                   "days_of_week": DOW,
                   "sources": {s: {"counts": grid[s], "total": totals[s]}
                               for s in sorted(totals, key=lambda k: -totals[k])}},
                  f, ensure_ascii=False, indent=1)
    print(f"weekday.json: {len(grid)} sources x 7 days")

    # rhythm: hour-of-day (UTC captured_at) x source capture counts
    hgrid = defaultdict(lambda: [0] * 24)
    htotals = defaultdict(int)
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        ts, src = r.get("captured_at") or "", r.get("source") or ""
        m = ts[11:13] if len(ts) >= 13 and ts[10] == "T" else ""
        if not m.isdigit() or not src:
            continue
        hgrid[src][int(m)] += 1
        htotals[src] += 1
    with open(os.path.join(API, "rhythm.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "latest_snapshot": max(days),
                   "days_tracked": len(days), "utc": True,
                   "sources": {s: {"counts": hgrid[s], "total": htotals[s]}
                               for s in sorted(htotals, key=lambda k: -htotals[k])}},
                  f, ensure_ascii=False, indent=1)
    print(f"rhythm.json: {len(hgrid)} sources x 24 hours")

    discussed = sorted(items.values(), key=lambda x: -x["comments"])[:LIMIT]
    heated = sorted((x for x in items.values() if x["score"] >= 50),
                    key=lambda x: -x["comments"] / max(1, x["score"]))[:LIMIT]
    out = {"generated_at": now, "latest_snapshot": max(days),
           "total": len(items),
           "discussed": discussed, "heated": heated}
    with open(os.path.join(API, "discussed.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"discussed.json: {len(discussed)}+{len(heated)} rows / {out['total']} total")


def emit_history_apis(now):
    """topics-history.csv + hiring-history.csv → docs/api/*.json"""
    tpath = os.path.join(ROOT, "data", "topics-history.csv")
    if os.path.exists(tpath):
        rows = list(csv.DictReader(open(tpath, encoding="utf-8")))
        days = sorted({r["date"] for r in rows})
        topics = {}
        for r in rows:
            t = topics.setdefault(r["topic"], {"counts": {}, "scores": {}})
            t["counts"][r["date"]] = int(r["count"])
            t["scores"][r["date"]] = int(r.get("total_score") or 0)
        with open(os.path.join(API, "topics.json"), "w", encoding="utf-8") as f:
            json.dump({"generated_at": now, "days": days,
                       "topics": {k: {"counts": v["counts"], "scores": v["scores"]}
                                  for k, v in sorted(topics.items())}},
                      f, ensure_ascii=False, separators=(",", ":"))
        print(f"topics.json: {len(topics)} topics x {len(days)} days")
    # sparkline.svg — items-per-day trend, embeddable in READMEs
    per_day = {}
    for r in csv.DictReader(open(HIST, encoding="utf-8")):
        per_day.setdefault(r["date"], set()).add(r["url"])
    days = sorted(per_day)
    if days:
        vals = [len(per_day[d]) for d in days]
        W, Hh, P = 200, 36, 2
        mx = max(vals)
        pts = " ".join(
            f"{P + (W - 2 * P) * (i / max(1, len(vals) - 1)):.1f},{Hh - P - (Hh - 2 * P) * (v / mx):.1f}"
            for i, v in enumerate(vals))
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh + 14}" '
            f'viewBox="0 0 {W} {Hh + 14}" font-family="monospace">'
            f'<rect width="{W}" height="{Hh + 14}" fill="#0d1117" rx="4"/>'
            f'<polyline points="{pts}" fill="none" stroke="#58a6ff" stroke-width="1.5"/>')
        for i, v in enumerate(vals):
            x = P + (W - 2 * P) * (i / max(1, len(vals) - 1))
            y = Hh - P - (Hh - 2 * P) * (v / mx)
            svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="#58a6ff"/>'
        svg += (f'<text x="{P}" y="{Hh + 11}" font-size="8" fill="#8b949e">{days[0]}</text>'
                f'<text x="{W - P}" y="{Hh + 11}" font-size="8" fill="#8b949e" text-anchor="end">'
                f'{days[-1]} · {vals[-1]} items</text></svg>')
        with open(os.path.join(API, "sparkline.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"sparkline.svg: {len(days)} days, latest {vals[-1]}")

        # per-source sparklines → docs/api/sparkline/<source>.svg
        sdir = os.path.join(API, "sparkline")
        os.makedirs(sdir, exist_ok=True)
        per_src = {}
        for r in csv.DictReader(open(HIST, encoding="utf-8")):
            per_src.setdefault(r["source"], {}).setdefault(r["date"], set()).add(r["url"])
        def mk_svg(days2, vals2, label):
            W2, H2, P2 = 200, 36, 2
            mx2 = max(vals2) or 1
            pts2 = " ".join(
                f"{P2 + (W2 - 2 * P2) * (i / max(1, len(vals2) - 1)):.1f},{H2 - P2 - (H2 - 2 * P2) * (v / mx2):.1f}"
                for i, v in enumerate(vals2))
            o = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2 + 14}" '
                 f'viewBox="0 0 {W2} {H2 + 14}" font-family="monospace">'
                 f'<rect width="{W2}" height="{H2 + 14}" fill="#0d1117" rx="4"/>'
                 f'<polyline points="{pts2}" fill="none" stroke="#58a6ff" stroke-width="1.5"/>')
            o += (f'<text x="{P2}" y="{H2 + 11}" font-size="8" fill="#8b949e">{days2[0]}</text>'
                  f'<text x="{W2 - P2}" y="{H2 + 11}" font-size="8" fill="#8b949e" text-anchor="end">'
                  f'{label} · {vals2[-1]}</text></svg>')
            return o
        for src, dm in sorted(per_src.items()):
            vals2 = [len(dm.get(d, ())) for d in days]
            with open(os.path.join(sdir, f"{src}.svg"), "w", encoding="utf-8") as f:
                f.write(mk_svg(days, vals2, src))
        print(f"sparkline/: {len(per_src)} source svgs")
        print(f"sparkline.svg: {len(days)} days, latest {vals[-1]}")

    hpath = os.path.join(ROOT, "data", "hiring-history.csv")
    if os.path.exists(hpath):
        rows = list(csv.DictReader(open(hpath, encoding="utf-8")))
        with open(os.path.join(API, "hiring-history.json"), "w", encoding="utf-8") as f:
            json.dump({"generated_at": now, "rows": rows},
                      f, ensure_ascii=False, indent=1)
        print(f"hiring-history.json: {len(rows)} rows")



def emit_gone(now):
    """latest.json vs previous daily snapshot → docs/api/gone.json:
    items that were on yesterday's board but not today's (the drop side
    of new.json). Each entry: item fields + yesterday's rank/score."""
    import datetime, glob
    lpath = os.path.join(ROOT, "data", "latest.json")
    if not os.path.exists(lpath):
        return
    latest = json.load(open(lpath, encoding="utf-8"))
    today_urls = set()
    lit = latest.get("items", {})
    if isinstance(lit, dict):
        lit = [it for v in lit.values() for it in v]
    for it in lit:
        u = (it.get("url") or "").split("?")[0].rstrip("/")
        if u:
            today_urls.add(u)
    snaps = sorted(glob.glob(os.path.join(ROOT, "data", "daily", "*.json")))
    today_date = latest.get("latest_snapshot", latest.get("date", ""))
    prev = None
    for p in reversed(snaps):
        d = os.path.basename(p)[:10]
        if d != today_date:
            prev = p
            break
    gone = []
    if prev:
        pd = json.load(open(prev, encoding="utf-8"))
        pit = pd.get("items", {})
        if isinstance(pit, dict):
            pit = [it for v in pit.values() for it in v]
        for it in pit:
            u = (it.get("url") or "").split("?")[0].rstrip("/")
            if u and u not in today_urls:
                gone.append({"title": it.get("title"), "url": it.get("url"),
                             "source": it.get("source"), "metric": it.get("metric"),
                             "score": it.get("score"), "rank": it.get("rank")})
    gone.sort(key=lambda x: x.get("score") or 0, reverse=True)
    out = {"generated_at": now, "latest_snapshot": today_date,
           "previous_snapshot": os.path.basename(prev)[:10] if prev else None,
           "items": gone}
    op = os.path.join(ROOT, "docs", "api", "gone.json")
    json.dump(out, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"gone.json: {len(gone)} dropped items")


def emit_rss(now):
    """latest.json → docs/api/latest.rss: today's top items as RSS 2.0,
    so RSS readers can subscribe to the cross-source board."""
    import html as _html
    lpath = os.path.join(ROOT, "data", "latest.json")
    if not os.path.exists(lpath):
        return
    latest = json.load(open(lpath, encoding="utf-8"))
    items = latest.get("items", {})
    if isinstance(items, dict):
        items = [it for v in items.values() for it in v]
    # package counters are rolling download numbers, not news — exclude
    items = [it for it in items
             if it.get("source") not in ("npm", "pypi", "crates")]
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    items = items[:25]
    esc = lambda t: _html.escape(str(t or ""), quote=True)
    body = "\n".join(
        "  <item><title>{}</title><link>{}</link>"
        "<description>{} · {} · score {}</description>"
        "<guid isPermaLink=\"true\">{}</guid></item>".format(
            esc(it.get("title")), esc(it.get("url")),
            esc(it.get("source")), esc(it.get("metric")),
            it.get("score", 0), esc(it.get("url")))
        for it in items)
    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0"><channel>'
           '<title>trendscope — today\'s top</title>'
           '<link>https://zalize-com.github.io/trendscope/</link>'
           '<description>Top items across 18 tracked sources, refreshed daily.</description>'
           '<lastBuildDate>{}</lastBuildDate>\n{}\n</channel></rss>\n').format(now, body)
    with open(os.path.join(API, "latest.rss"), "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"latest.rss: {len(items)} items")


if __name__ == "__main__":
    main()
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    emit_history_apis(now)
    emit_rss(now)
    emit_gone(now)
