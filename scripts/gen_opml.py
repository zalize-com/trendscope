#!/usr/bin/env python3
"""Regenerate trendscope.opml — every RSS/Atom feed in the registry as OPML
outlines, importable into Feedly/NetNewsWire/FreshRSS. API sources (HN/npm/
PyPI/reddit...) have no feed URL and are excluded. Run after any source wave."""
import re, json, glob, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "scripts", "collect.py")).read()

feeds = {}
for m in re.finditer(r'def (fetch_\w+)\([^)]*\):\s*\n\s*"""(.*?)"""(.*?)(?=\ndef |\Z)', src, re.S):
    name, doc, body = m.groups()
    label = re.sub(r"\s+—.*$", "", doc.strip().split("\n")[0].rstrip("."))
    um = (re.search(r'Request\(\s*\n?\s*"(https?://[^"]+)"', body)
          or re.search(r'["\'](https?://[^"\']*(?:feed|rss|atom|xml)[^"\']*)["\']', body))
    if um:
        feeds[name] = (label, um.group(1))

out = [(k,) + feeds[fn] for k, fn in re.findall(r'"(\w+)": (fetch_\w+),', src) if fn in feeds]
dormant_keys = set()
for p in sorted(glob.glob(os.path.join(ROOT, "scripts", "feeds_*.json"))):
    for k, row in json.load(open(p)).items():
        label, feed, home = row[:3]
        out.append((k, label, feed))
        if len(row) > 3 and "dormant" in row[3:]:
            dormant_keys.add(k)
# Data-driven feeds_*.json rows override literal fetchers for the same key
# (mirrors collect.py's fetchers.update()) — dedupe last-wins so OPML/JSON
# don't double-count moved sources.
out = list({k: (k, n, f) for k, n, f in out}.values())

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="2.0">', '<head>',
         f'<title>trendscope sources ({len(out)})</title>',
         f'<dateModified>{datetime.date.today()}</dateModified>', '</head>', '<body>',
         '<outline text="trendscope" title="trendscope sources">']
for k, n, f in out:
    lines.append(f'<outline type="rss" text="{esc(n)[:80]}" title="{esc(n)[:80]}" xmlUrl="{esc(f)}"/>')
lines += ['</outline>', '</body>', '</opml>']
open(os.path.join(ROOT, "trendscope.opml"), "w").write("\n".join(lines))
print(f"trendscope.opml: {len(out)} outlines")

# data/feeds.json — the same registry as JSON so the site can render a
# browsable feed directory (feeds.html) and API consumers can subscribe
# without parsing OPML.
feeds_json = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds").replace("+00:00", "Z"),
    "count": len(out),
    "feeds": [
        {"key": k, "label": n, "feed": f,
         "lane": k.split("_")[0] if "_" in k else "misc",
         "dormant": k in dormant_keys}
        for k, n, f in out],
}
with open(os.path.join(ROOT, "data", "feeds.json"), "w") as fh:
    json.dump(feeds_json, fh, indent=1, ensure_ascii=False)
print(f"data/feeds.json: {len(out)} feeds")

# data/opml/<lane>.opml — per-lane OPML so readers can subscribe to just
# security feeds, just YouTube channels, etc. without importing 9k+ outlines.
opml_dir = os.path.join(ROOT, "data", "opml")
os.makedirs(opml_dir, exist_ok=True)
for stale in glob.glob(os.path.join(opml_dir, "*.opml")):
    os.remove(stale)
lanes = {}
for k, n, f in out:
    lanes.setdefault(k.split("_")[0] if "_" in k else "misc", []).append((k, n, f))
for lane, rows in sorted(lanes.items()):
    ll = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="2.0">', '<head>',
          f'<title>trendscope {lane} feeds ({len(rows)})</title>',
          f'<dateModified>{datetime.date.today()}</dateModified>', '</head>', '<body>',
          f'<outline text="{esc(lane)}" title="trendscope {lane}">']
    for k, n, f in rows:
        ll.append(f'<outline type="rss" text="{esc(n)[:80]}" title="{esc(n)[:80]}" xmlUrl="{esc(f)}"/>')
    ll += ['</outline>', '</body>', '</opml>']
    open(os.path.join(opml_dir, f"{lane}.opml"), "w").write("\n".join(ll))
print(f"data/opml/: {len(lanes)} lane files")
