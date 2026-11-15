#!/usr/bin/env python3
"""Track HN monthly hiring threads — a labor-demand signal nobody archives.

Finds the latest "Who is hiring? (Month Year)" and "Who wants to be hired?"
threads via Algolia search_by_date, records comment counts, appends to
data/hiring-history.csv and writes data/hiring.json for the dashboard card.
"""

import csv
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import get_json, DATA_DIR  # noqa: E402

THREADS = {
    "hiring": ("who is hiring", "who is hiring?"),
    "seeking": ("who wants to be hired", "who wants to be hired?"),
}
MONTH_RE = re.compile(r"\((January|February|March|April|May|June|July|August|"
                      r"September|October|November|December)\s+\d{4}\)", re.I)


def latest_thread(query, phrase):
    data = get_json(
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=ask_hn&query={urllib.request.quote(query)}&hitsPerPage=10")
    for h in (data or {}).get("hits", []):
        title = h.get("title", "")
        if phrase in title.lower() and MONTH_RE.search(title):
            return {
                "id": h["objectID"],
                "title": h["title"],
                "month": MONTH_RE.search(h["title"]).group(0).strip("()"),
                "created": h["created_at"][:10],
                "comments": h.get("num_comments", 0),
                "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
            }
    return None


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    found = {k: latest_thread(q, p) for k, (q, p) in THREADS.items()}

    hist = os.path.join(DATA_DIR, "hiring-history.csv")
    new = not os.path.exists(hist)
    with open(hist, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["captured_at", "kind", "thread_id", "month",
                        "comments", "url"])
        for kind, t in found.items():
            if t:
                w.writerow([now, kind, t["id"], t["month"],
                            t["comments"], t["url"]])

    out = {"generated_at": now, "threads": {
        k: t for k, t in found.items() if t}}
    with open(os.path.join(DATA_DIR, "hiring.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("hiring:", {k: (t["comments"] if t else None)
                    for k, t in found.items()})


if __name__ == "__main__":
    main()
