#!/usr/bin/env python3
"""Backfill past days' Hacker News top stories via Algolia numeric filters.

Only HN supports real time-travel (stories carry their day-1 scores in Algolia's
index for a while). Other sources are day-0 only, so backfilled daily files
contain just the hackernews section with `partial: true`.

Usage: python3 scripts/backfill.py [days]   (default 7, skips today and existing days)
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

UA = "trendscope/0.1 (+https://github.com/zalize-com/trendscope)"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def hn_top_for_day(day, limit=20):
    start = int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())
    end = start + 86400
    url = (f"https://hn.algolia.com/api/v1/search?tags=story"
           f"&numericFilters=created_at_i>={start},created_at_i<{end},points>=15"
           f"&hitsPerPage=100")
    data = get_json(url) or {}
    hits = sorted(data.get("hits", []), key=lambda h: -h.get("points", 0))[:limit]
    out = []
    for rank, h in enumerate(hits, 1):
        out.append({
            "source": "hackernews",
            "rank": rank,
            "title": h.get("title", ""),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "score": h.get("points", 0),
            "metric": "points",
            "comments": h.get("num_comments", 0),
            "author": h.get("author"),
            "tags": [],
            "captured_at": f"{day.isoformat()}T23:59:00+00:00",
            "backfilled": True,
        })
    return out


TOPIC_RULES = {
    "AI/LLM": ["ai", "llm", "gpt", "claude", "gemini", "openai", "anthropic",
               "machine learning", "ml ", "neural", "diffusion", "agent",
               "rag", "transformer", "model", "inference", "fine-tun",
               "copilot", "mcp", "prompt"],
    "Web Dev": ["react", "vue", "svelte", "angular", "next.js", "nextjs",
                "typescript", "javascript", "css", "html", "web", "vite",
                "tailwind", "frontend", "browser", "dom"],
    "DevOps/Infra": ["kubernetes", "k8s", "docker", "terraform", "ci/cd",
                     "deploy", "aws", "cloud", "serverless", "infra",
                     "observability", "monitor", "devops"],
    "Security": ["security", "vuln", "cve", "exploit", "breach", "malware",
                 "ransomware", "phishing", "zero-day", "0day", "auth",
                 "encryption", "privacy"],
    "Data Eng": ["data", "postgres", "sql", "database", "duckdb",
                 "pipeline", "etl", "spark", "kafka", "analytics",
                 "warehouse", "dbt"],
    "Languages": ["rust", "golang", "go ", "python", "java", "kotlin",
                  "swift", "zig", "c++", "compiler", "lua"],
    "Tools/OSS": ["open source", "cli", "tool", "github", "git ",
                  "editor", "vscode", "neovim", "terminal", "framework",
                  "library", "release", "v1.0"],
    "Career/Business": ["startup", "hiring", "salary", "remote", "career",
                        "interview", "acquisition", "ipo", "funding",
                        "layoff", "business", "saas"],
}


def classify_topics(items):
    topics = {k: {"count": 0, "total_score": 0, "examples": []} for k in TOPIC_RULES}
    for it in items:
        text = it.get("title", "").lower()
        for topic, keywords in TOPIC_RULES.items():
            if any(k in text for k in keywords):
                t = topics[topic]
                t["count"] += 1
                t["total_score"] += it.get("score", 0)
                if len(t["examples"]) < 3:
                    t["examples"].append({"title": it["title"], "url": it["url"], "source": it["source"]})
    return [{"topic": k, **v} for k, v in sorted(
        topics.items(), key=lambda kv: (-kv[1]["count"], -kv[1]["total_score"]))
        if v["count"] > 0]


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    today = datetime.now(timezone.utc).date()
    daily_dir = os.path.join(DATA_DIR, "daily")
    os.makedirs(daily_dir, exist_ok=True)

    idx_path = os.path.join(DATA_DIR, "index.json")
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {"snapshots": []}

    for i in range(1, days + 1):
        day = today - timedelta(days=i)
        ds = day.isoformat()
        path = os.path.join(daily_dir, f"{ds}.json")
        if os.path.exists(path):
            print(f"skip {ds} (exists)")
            continue
        items = hn_top_for_day(day)
        if not items:
            print(f"skip {ds} (no hits)")
            continue
        snap = {
            "date": ds,
            "generated_at": f"{ds}T23:59:00+00:00",
            "partial": True,
            "backfilled": True,
            "sources": {"hackernews": len(items)},
            "items": {"hackernews": items},
            "top_scores": {"hackernews": [
                {"title": x["title"], "url": x["url"], "score": x["score"],
                 "metric": x["metric"]} for x in items[:10]]},
            "topics": classify_topics(items),
        }
        with open(path, "w") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False)
        print(f"wrote {ds}: {len(items)} HN items")
        if ds not in idx["snapshots"]:
            idx["snapshots"].append(ds)
        time.sleep(1)

    idx["snapshots"].sort()
    with open(idx_path, "w") as f:
        json.dump(idx, f, indent=2)
    print("index.json updated")


if __name__ == "__main__":
    main()
