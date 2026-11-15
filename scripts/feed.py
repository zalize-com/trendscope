#!/usr/bin/env python3
"""TrendScope RSS feed — generates feed.xml at repo root.

Items: one per daily snapshot (data/daily/*.json) and one per weekly digest
(docs/digest/*.md). Most recent first, capped at 30 items.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "daily")
DIGEST = os.path.join(ROOT, "docs", "digest")
MOVERS = os.path.join(ROOT, "docs", "movers")
BASE = "https://zalize-com.github.io/trendscope"
REPO = "https://github.com/zalize-com/trendscope"


def item_date(name):
    """Edition date for a daily snapshot (YYYY-MM-DD) or digest (YYYY-Www)."""
    if "-W" in name:
        y, w = name.split("-W")
        return datetime.strptime(f"{y}-W{w}-7", "%G-W%V-%u").replace(tzinfo=timezone.utc)
    try:
        return datetime.strptime(name, "%Y-%m-%d").replace(
            hour=6, minute=10, tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def items():
    out = []
    for name in sorted(os.listdir(DAILY), reverse=True):
        if not name.endswith(".json"):
            continue
        day = name[:-5]
        try:
            doc = json.load(open(os.path.join(DAILY, name)))
            n = sum(len(v) for v in doc.get("items", {}).values())
            src = len(doc.get("items", {}))
            tops = []
            for src_items in (doc.get("top_scores") or {}).values():
                tops += [i["title"][:80] for i in src_items[:1]]
            desc = f"{n} items across {src} sources. " + (
                "Top: " + "; ".join(tops[:3]) if tops else "")
        except Exception:
            desc = "Daily snapshot."
        out.append((item_date(day), f"Snapshot {day}",
                    f"{BASE}/", f"{REPO}/blob/main/data/daily/{name}", desc))
    for name in sorted(os.listdir(DIGEST), reverse=True):
        if not re.fullmatch(r"\d{4}-W\d{2}\.md", name):
            continue
        week = name[:-3]
        out.append((item_date(week), f"Weekly digest {week}",
                    f"{REPO}/blob/main/docs/digest/{name}", f"{REPO}/blob/main/docs/digest/{name}",
                    "Weekly digest: top movers, per-source leaders, hot tags."))
    if os.path.isdir(MOVERS):
        for name in sorted(os.listdir(MOVERS), reverse=True):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", name):
                continue
            day = name[:-3]
            out.append((item_date(day) + timedelta(minutes=10), f"Movers {day}",
                        f"{REPO}/blob/main/docs/movers/{name}", f"{REPO}/blob/main/docs/movers/{name}",
                        "Daily movers: what entered the board, what left, biggest gainers."))
    out.sort(key=lambda t: t[0], reverse=True)
    return out[:30]


def main():
    now = format_datetime(datetime.now(timezone.utc))
    body = []
    for pub, title, link, guid, desc in items():
        body.append(
            f"  <item>\n    <title>{escape(title)}</title>\n    <link>{escape(link)}</link>\n"
            f"    <guid isPermaLink=\"true\">{escape(guid)}</guid>\n"
            f"    <pubDate>{format_datetime(pub)}</pubDate>\n    <description>{escape(desc)}</description>\n  </item>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n<channel>\n'
        "  <title>trendscope — developer attention dataset</title>\n"
        f"  <link>{BASE}/</link>\n"
        "  <description>Daily cross-source snapshot of what developers are reading, building and downloading.</description>\n"
        f"  <lastBuildDate>{now}</lastBuildDate>\n" + "\n".join(body) + "\n</channel>\n</rss>\n")
    with open(os.path.join(ROOT, "feed.xml"), "w") as f:
        f.write(xml)

    # JSON Feed v1.1 (feed.json) — same items, modern format.
    jfeed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "trendscope — developer attention dataset",
        "home_page_url": f"{BASE}/",
        "feed_url": f"{BASE}/feed.json",
        "description": "Daily cross-source snapshot of what developers are "
                       "reading, building and downloading.",
        "items": [{
            "id": guid,
            "url": link,
            "title": title,
            "summary": desc,
            "date_published": pub.isoformat(),
        } for pub, title, link, guid, desc in items()],
    }
    with open(os.path.join(ROOT, "feed.json"), "w") as f:
        json.dump(jfeed, f, indent=1, ensure_ascii=False)
    print(f"feed.xml + feed.json: {len(body)} items")


if __name__ == "__main__":
    main()
