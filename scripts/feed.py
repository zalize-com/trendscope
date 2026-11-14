#!/usr/bin/env python3
"""TrendScope RSS feed — generates feed.xml at repo root.

Items: one per daily snapshot (data/daily/*.json) and one per weekly digest
(docs/digest/*.md). Most recent first, capped at 30 items.
"""

import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "daily")
DIGEST = os.path.join(ROOT, "docs", "digest")
BASE = "https://zalize-com.github.io/trendscope"
REPO = "https://github.com/zalize-com/trendscope"


def items():
    out = []
    for name in sorted(os.listdir(DAILY), reverse=True):
        if not name.endswith(".json"):
            continue
        day = name[:-5]
        try:
            doc = json.load(open(os.path.join(DAILY, name)))
            items = doc.get("items", {})
            n = sum(len(v) for v in items.values())
            src = len(items)
            tops = []
            for src_items in (doc.get("top_scores") or {}).values():
                tops += [i["title"][:80] for i in src_items[:1]]
            desc = f"{n} items across {src} sources. " + (
                "Top: " + "; ".join(tops[:3]) if tops else "")
        except Exception:
            desc = "Daily snapshot."
        out.append((day, f"Snapshot {day}",
                    f"{BASE}/", f"{REPO}/blob/main/data/daily/{name}", desc))
    for name in sorted(os.listdir(DIGEST), reverse=True):
        if not name.endswith(".md"):
            continue
        week = name[:-3]
        out.append((week, f"Weekly digest {week}",
                    f"{REPO}/blob/main/docs/digest/{name}", f"{REPO}/blob/main/docs/digest/{name}",
                    "Weekly digest: top movers, per-source leaders, hot tags."))
    out.sort(key=lambda t: t[0], reverse=True)
    return out[:30]


def main():
    now = format_datetime(datetime.now(timezone.utc))
    body = []
    for _, title, link, guid, desc in items():
        body.append(
            f"  <item>\n    <title>{escape(title)}</title>\n    <link>{escape(link)}</link>\n"
            f"    <guid isPermaLink=\"true\">{escape(guid)}</guid>\n"
            f"    <pubDate>{now}</pubDate>\n    <description>{escape(desc)}</description>\n  </item>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n<channel>\n'
        "  <title>trendscope — developer attention dataset</title>\n"
        f"  <link>{BASE}/</link>\n"
        "  <description>Daily cross-source snapshot of what developers are reading, building and downloading.</description>\n"
        f"  <lastBuildDate>{now}</lastBuildDate>\n" + "\n".join(body) + "\n</channel>\n</rss>\n")
    with open(os.path.join(ROOT, "feed.xml"), "w") as f:
        f.write(xml)
    print(f"feed.xml: {len(body)} items")


if __name__ == "__main__":
    main()
