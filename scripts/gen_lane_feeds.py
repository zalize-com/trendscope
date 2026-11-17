#!/usr/bin/env python3
"""Per-lane RSS feeds — one RSS 2.0 feed per lane, from the latest snapshot.

Output:
  data/rss/<lane>.xml   top ~25 items of that lane, score-sorted
  data/rss/index.json   lane -> {count, xml}
  data/rss/index.opml   subscribe-to-all bundle

Lanes come from data/feeds.json (feed registry lanes) plus a small
platform-source map for the 11 non-feed keys (hackernews, npm, ...).
Stdlib only; run by collect.yml after the snapshot lands.
"""

import json
import os
from email.utils import format_datetime
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "rss")
BASE = "https://trendscope.zalize.com"
TOP_N = 25

PLATFORM_LANE = {
    "hackernews": "hn", "show_hn": "hn", "ask_hn": "hn",
    "github_trending": "github", "lobsters": "lobsters", "devto": "devto",
    "npm": "packages", "pypi": "packages", "crates": "packages",
    "arxiv": "arxiv", "lemmy": "lemmy",
}
LANE_TITLES = {
    "hn": "Hacker News", "github": "GitHub", "lobsters": "Lobsters",
    "devto": "Dev.to", "packages": "Packages", "arxiv": "arXiv",
    "lemmy": "Lemmy", "sec": "Security", "eb": "Engineering blogs",
    "tb": "Tech blogs", "br": "Blogroll", "nl": "Newsletters",
    "pb": "Pod blogs", "yt": "YouTube", "tldr": "TLDR", "aws": "AWS",
    "gitlab": "GitLab", "meta": "Meta", "slack": "Slack", "misc": "Misc",
}
LANE_PAGE = {l: f"{BASE}/daily/{l}" for l in
             ("sec", "eb", "tb", "br", "nl", "pb", "yt", "tldr", "misc")}


def lane_of(key, feed_lanes):
    if key in feed_lanes:
        return feed_lanes[key]
    if key in PLATFORM_LANE:
        return PLATFORM_LANE[key]
    if key.startswith("r") and "_" not in key:
        return "reddit"
    return "misc"


def main():
    lite = json.load(open(os.path.join(DATA, "latest-lite.json")))
    feeds = json.load(open(os.path.join(DATA, "feeds.json")))
    feed_lanes = {f["key"]: f.get("lane") or "misc" for f in feeds["feeds"]}
    date = lite.get("date", "")
    try:
        pub = format_datetime(datetime.strptime(date, "%Y-%m-%d")
                              .replace(hour=12, tzinfo=timezone.utc))
    except ValueError:
        pub = format_datetime(datetime.now(timezone.utc))

    lanes = {}
    for key, items in (lite.get("items") or {}).items():
        lanes.setdefault(lane_of(key, feed_lanes), []).extend(items)

    os.makedirs(OUT, exist_ok=True)
    index = {}
    for lane, items in sorted(lanes.items()):
        items.sort(key=lambda i: (-(i.get("score") or 0), i.get("rank") or 999))
        top = items[:TOP_N]
        if not top:
            continue
        title = f"trendscope · {LANE_TITLES.get(lane, lane)}"
        link = LANE_PAGE.get(lane, BASE + "/")
        body = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<rss version="2.0"><channel>',
                f"<title>{escape(title)}</title>",
                f"<link>{escape(link)}</link>",
                f"<description>Top {lane} items from today's cross-source snapshot ({date}). CC0.</description>",
                f"<pubDate>{pub}</pubDate>",
                f"<lastBuildDate>{pub}</lastBuildDate>"]
        for it in top:
            desc = (f"{it.get('source')} · score {it.get('score')}"
                    + (f" · {it.get('comments')} comments" if it.get("comments") else ""))
            body += ["<item>",
                     f"<title>{escape(it.get('title') or '(untitled)')}</title>",
                     f"<link>{escape(it.get('url') or link)}</link>",
                     f"<guid isPermaLink=\"true\">{escape(it.get('url') or link)}</guid>",
                     f"<description>{escape(desc)}</description>",
                     f"<pubDate>{pub}</pubDate>",
                     "</item>"]
        body += ["</channel></rss>"]
        xml = "\n".join(body)
        with open(os.path.join(OUT, f"{lane}.xml"), "w") as f:
            f.write(xml)
        index[lane] = {"title": title, "items": len(top),
                       "xml": f"{BASE}/data/rss/{lane}.xml"}

    with open(os.path.join(OUT, "index.json"), "w") as f:
        json.dump({"date": date, "lanes": index}, f, indent=1)

    opml = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<opml version="2.0"><head><title>trendscope lane feeds</title></head><body>']
    for lane, meta in index.items():
        opml.append(f'<outline type="rss" text="{escape(meta["title"])}" '
                    f'xmlUrl="{escape(meta["xml"])}" htmlUrl="{escape(LANE_PAGE.get(lane, BASE))}"/>')
    opml += ["</body></opml>"]
    with open(os.path.join(OUT, "index.opml"), "w") as f:
        f.write("\n".join(opml))

    print(f"data/rss/: {len(index)} lane feeds, "
          f"{sum(m['items'] for m in index.values())} items")


if __name__ == "__main__":
    main()
