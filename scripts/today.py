#!/usr/bin/env python3
"""docs/api/today.json — single-call 'what happened today' endpoint:
top items, topic mix, movers counts, hiring pulse, streaks count.
One URL a consumer or embed can read instead of joining five files."""

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = os.path.join(ROOT, "docs", "api")

TOPIC_RULES = [
    ("AI/LLM", ["llm", "gpt", "claude", "openai", "anthropic", "ai ", "ai-", "ai's", " ai", "gemini", "mistral", "deepseek", "neural", "ml ", "machine learning", "diffusion", "transformer", "agent"]),
    ("Security", ["security", "vulnerability", "cve", "exploit", "breach", "malware", "ransomware", "hack", "privacy", "encryption", "auth"]),
    ("DevTools", ["ide", "editor", "compiler", "debugger", "linter", "formatter", "ci/cd", "devops", "docker", "kubernetes", "git "]),
    ("Web Dev", ["javascript", "typescript", "react", "vue", "css", "html", "browser", "web ", "frontend", "backend", "api", "node"]),
    ("Programming", ["rust", "python", "golang", " go ", "java", "c++", "zig", "haskell", "language", "stdlib"]),
    ("Hardware", ["chip", "gpu", "cpu", "fpga", "raspberry", "esp32", "hardware", "silicon"]),
    ("Career", ["hiring", "job", "interview", "salary", "career", "fired", "laid off", "resign", "remote work"]),
    ("Open Source", ["open source", "open-source", "license", "gpl", "mit license", "foss"]),
]

def topic_of(title):
    t = (title or "").lower()
    return [name for name, kws in TOPIC_RULES if any(k in t for k in kws)]

def main():
    latest = json.load(open(os.path.join(DATA, "latest.json")))
    items = latest.get("items", [])
    date = latest.get("date") or datetime.now(timezone.utc).date().isoformat()

    rows = list(csv.DictReader(open(os.path.join(DATA, "history.csv"))))
    yday_rows = [r for r in rows if r["date"] != date]
    yday_urls = {r["url"] for r in yday_rows if r["date"] == yday_rows[-1]["date"]} if yday_rows else set()
    today = [r for r in rows if r["date"] == date]

    # topic mix
    mix = Counter()
    for r in today:
        for t in topic_of(r["title"]) or ["Other"]:
            mix[t] += 1

    # current streaks >= 2d ending today
    by_url = {}
    for r in rows:
        by_url.setdefault(r["url"], set()).add(r["date"])
    dates = sorted({r["date"] for r in rows})
    def prev(d):
        from datetime import timedelta
        return (datetime.fromisoformat(d).date() - timedelta(1)).isoformat()
    streaks = 0
    for u, ds in by_url.items():
        cur, d = 0, date
        while d in ds:
            cur += 1
            d = prev(d)
        if cur >= 2:
            streaks += 1

    movers = {}
    mf = os.path.join(API, "movers-latest.json")
    if os.path.exists(mf):
        m = json.load(open(mf))
        movers = {k: len(m.get(k, [])) for k in ("entered", "left", "gainers", "droppers")}

    hiring = {}
    hf = os.path.join(DATA, "hiring.json")
    if os.path.exists(hf):
        hiring = json.load(open(hf))

    top = sorted(today, key=lambda r: -(float(r["score"] or 0)))[:10]
    doc = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": len(today),
        "sources": len({r["source"] for r in today}),
        "new_entries": len([r for r in today if r["url"] not in yday_urls]),
        "active_streaks_2d_plus": streaks,
        "top10": [{"title": r["title"], "url": r["url"], "source": r["source"],
                   "score": int(float(r["score"] or 0)), "metric": r["metric"]} for r in top],
        "topic_mix": dict(mix.most_common(10)),
        "movers": movers,
        "hiring": hiring,
    }
    os.makedirs(API, exist_ok=True)
    with open(os.path.join(API, "today.json"), "w") as f:
        json.dump(doc, f, indent=1)
    print(f"today.json: {len(today)} items, {len(mix)} topics, {streaks} streaks")

if __name__ == "__main__":
    main()
