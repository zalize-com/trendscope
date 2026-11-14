#!/usr/bin/env python3
"""TrendScope collector — aggregates daily developer trend signals from free APIs.

Sources (all keyless or token-optional):
  - Hacker News front page      (hn.algolia.com)
  - Lobsters hottest            (lobste.rs)
  - dev.to top articles         (dev.to/api)
  - GitHub new trending repos   (api.github.com search, token optional)
  - npm weekly downloads        (api.npmjs.org) for a package watchlist
  - PyPI monthly downloads      (pypistats.org) for a package watchlist
  - crates.io recent downloads  (crates.io/api, needs User-Agent)

Outputs (the accumulating CC0 dataset):
  data/latest.json              full snapshot consumed by the dashboard
  data/latest.csv               today's items, flat CSV
  data/daily/YYYY-MM-DD.json    daily snapshot archive (json + csv)
  data/daily/YYYY-MM-DD.csv
  data/history.csv              cumulative flat rows for velocity analysis
  data/index.json               snapshot index
"""

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "trendscope/0.1 (+https://github.com/zalize-com/trendscope)"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

NPM_WATCHLIST = [
    "react", "vue", "@angular/core", "svelte", "next", "nuxt", "vite",
    "typescript", "express", "fastify", "nestjs", "lodash", "axios",
    "tailwindcss", "webpack", "esbuild", "jest", "vitest", "prisma",
    "zod", "react-query", "graphql", "electron", "react-native",
]

PYPI_WATCHLIST = [
    "requests", "numpy", "pandas", "django", "flask", "fastapi",
    "sqlalchemy", "boto3", "pytest", "pydantic", "scipy",
    "scikit-learn", "matplotlib", "tensorflow", "torch", "transformers",
    "openai", "langchain", "click", "rich", "httpx", "celery",
]

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


def get_json(url, headers=None, retries=2):
    """Fetch JSON with retries. Returns parsed JSON or None on failure."""
    req_headers = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [warn] GET {url} attempt {attempt + 1} failed: {e}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    return None


def item(source, title, url, score, metric, tags=None, comments=0,
         author=None, extra=None):
    d = {
        "source": source,
        "title": title,
        "url": url,
        "score": score,
        "metric": metric,
        "comments": comments,
        "author": author,
        "tags": tags or [],
    }
    if extra:
        d.update(extra)
    return d


def fetch_hackernews(limit=20):
    print("Fetching Hacker News front page...")
    data = get_json(
        f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={limit}"
    )
    out = []
    for h in (data or {}).get("hits", []):
        out.append(item(
            "hackernews",
            h.get("title", ""),
            h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            h.get("points", 0),
            "points",
            tags=[t for t in (h.get("_tags") or [])
                  if not (t.startswith(("author_", "story_", "poll_"))
                          or t in ("front_page", "story", "poll", "comment"))],
            comments=h.get("num_comments", 0),
            author=h.get("author"),
        ))
    return out


def fetch_lobsters(limit=15):
    print("Fetching Lobsters hottest...")
    data = get_json("https://lobste.rs/hottest.json")
    out = []
    for s in (data or [])[:limit]:
        out.append(item(
            "lobsters",
            s.get("title", ""),
            s.get("url") or s.get("short_id_url", ""),
            s.get("score", 0),
            "score",
            tags=s.get("tags", []),
            comments=s.get("comment_count", 0),
        ))
    return sorted(out, key=lambda x: -x["score"])


def fetch_devto(limit=15):
    print("Fetching dev.to top articles...")
    data = get_json("https://dev.to/api/articles?top=7&per_page=25")
    out = []
    for a in (data or [])[:limit]:
        out.append(item(
            "devto",
            a.get("title", ""),
            a.get("url", ""),
            a.get("positive_reactions_count", 0),
            "reactions",
            tags=a.get("tag_list", []),
            comments=a.get("comments_count", 0),
            author=(a.get("user") or {}).get("username"),
        ))
    return sorted(out, key=lambda x: -x["score"])


def fetch_github_trending(limit=15):
    print("Fetching GitHub trending repos...")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    week_ago = datetime.fromtimestamp(
        time.time() - 7 * 86400, tz=timezone.utc).strftime("%Y-%m-%d")
    q = urllib.parse.quote(f"created:>{week_ago} stars:>20")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    data = get_json(url, headers=headers)
    if data is None and not token:
        print("  [warn] GitHub search failed without token; skipping", file=sys.stderr)
        return []
    out = []
    for r in (data or {}).get("items", []):
        out.append(item(
            "github_trending",
            r.get("full_name", ""),
            r.get("html_url", ""),
            r.get("stargazers_count", 0),
            "stars",
            tags=[r.get("language")] if r.get("language") else [],
            author=(r.get("owner") or {}).get("login"),
            extra={
                "description": r.get("description") or "",
                "created_at": r.get("created_at"),
                "forks": r.get("forks_count", 0),
            },
        ))
    return out


def fetch_npm_downloads():
    print("Fetching npm weekly downloads...")
    out = []
    for pkg in NPM_WATCHLIST:
        enc = urllib.parse.quote(pkg, safe="@/")
        data = get_json(f"https://api.npmjs.org/downloads/point/last-week/{enc}")
        if data and "downloads" in data:
            out.append(item(
                "npm", pkg,
                f"https://www.npmjs.com/package/{pkg}",
                data["downloads"], "weekly downloads",
                tags=["npm"],
            ))
        time.sleep(0.25)
    return sorted(out, key=lambda x: -x["score"])


def fetch_crates(limit=15):
    print("Fetching crates.io recent downloads...")
    data = get_json(
        f"https://crates.io/api/v1/crates?sort=recent-downloads&per_page={limit}")
    out = []
    for c in (data or {}).get("crates", []):
        out.append(item(
            "crates",
            c.get("id") or c.get("name", ""),
            f"https://crates.io/crates/{c.get('id') or c.get('name', '')}",
            c.get("recent_downloads") or c.get("downloads", 0),
            "recent downloads",
            tags=(c.get("keywords") or [])[:5],
            extra={"description": c.get("description") or ""},
        ))
    return out


def fetch_pypi_downloads():
    print("Fetching PyPI monthly downloads...")
    out = []
    for pkg in PYPI_WATCHLIST:
        data = get_json(f"https://pypistats.org/api/packages/{pkg}/recent")
        if data and "data" in data:
            out.append(item(
                "pypi", pkg,
                f"https://pypi.org/project/{pkg}/",
                data["data"].get("last_month", 0), "monthly downloads",
                tags=["pypi"],
            ))
        time.sleep(0.25)
    return sorted(out, key=lambda x: -x["score"])


def classify_topics(items):
    """Keyword-based topic counts over all titles/descriptions."""
    topics = {k: {"count": 0, "total_score": 0, "examples": []} for k in TOPIC_RULES}
    for it in items:
        text = f"{it.get('title', '')} {' '.join(it.get('tags', []))} {it.get('description', '')}".lower()
        for topic, keywords in TOPIC_RULES.items():
            if any(k in text for k in keywords):
                t = topics[topic]
                t["count"] += 1
                t["total_score"] += it.get("score", 0)
                if len(t["examples"]) < 3:
                    t["examples"].append({"title": it["title"], "url": it["url"], "source": it["source"]})
    # Rank by item count — raw scores mix incomparable units (points vs downloads).
    return [{"topic": k, **v} for k, v in sorted(
        topics.items(), key=lambda kv: (-kv[1]["count"], -kv[1]["total_score"]))
        if v["count"] > 0]


def load_history_index():
    path = os.path.join(DATA_DIR, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"snapshots": []}


def write_csvs(items, today, now_iso):
    """latest.csv = today flat; history.csv = cumulative (dedup on date+source+url)."""
    latest_csv = os.path.join(DATA_DIR, "latest.csv")
    history_csv = os.path.join(DATA_DIR, "history.csv")
    fields = ["date", "source", "rank", "title", "url", "score", "metric",
              "comments", "author", "tags", "captured_at"]

    rows = [{
        "date": today,
        "source": i["source"],
        "rank": i.get("rank", 0),
        "title": i["title"],
        "url": i["url"],
        "score": i["score"],
        "metric": i["metric"],
        "comments": i.get("comments", 0),
        "author": i.get("author") or "",
        "tags": "|".join(i.get("tags", [])),
        "captured_at": now_iso,
    } for i in items]

    with open(latest_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    existing = set()
    write_header = not os.path.exists(history_csv)
    if not write_header:
        with open(history_csv, newline="") as f:
            for r in csv.DictReader(f):
                existing.add((r["date"], r["source"], r["url"]))
    with open(history_csv, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        for r in rows:
            if (r["date"], r["source"], r["url"]) not in existing:
                w.writerow(r)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    sections = {
        "hackernews": fetch_hackernews(),
        "lobsters": fetch_lobsters(),
        "devto": fetch_devto(),
        "github_trending": fetch_github_trending(),
        "npm": fetch_npm_downloads(),
        "pypi": fetch_pypi_downloads(),
        "crates": fetch_crates(),
    }

    all_items = []
    for items in sections.values():
        for rank, it in enumerate(items, start=1):
            it["rank"] = rank
            it["captured_at"] = now.isoformat()
        all_items.extend(items)
    topics = classify_topics(all_items)

    snapshot = {
        "generated_at": now.isoformat(),
        "date": today,
        "sources": {k: len(v) for k, v in sections.items()},
        "total_items": len(all_items),
        "topics": topics,
        "items": sections,
    }

    latest_path = os.path.join(DATA_DIR, "latest.json")
    with open(latest_path, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    daily_dir = os.path.join(DATA_DIR, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    history_path = os.path.join(daily_dir, f"{today}.json")
    history_record = {
        "date": today,
        "generated_at": now.isoformat(),
        "sources": {k: len(v) for k, v in sections.items()},
        "items": sections,
        "top_scores": {
            k: [{"title": i["title"], "url": i["url"], "score": i["score"],
                 "metric": i["metric"]} for i in v[:10]]
            for k, v in sections.items()
        },
        "topics": [{"topic": t["topic"], "count": t["count"],
                    "total_score": t["total_score"]} for t in topics],
    }
    with open(history_path, "w") as f:
        json.dump(history_record, f, indent=2, ensure_ascii=False)

    with open(os.path.join(daily_dir, f"{today}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date", "source", "rank", "title", "url", "score", "metric",
            "comments", "author", "tags", "captured_at"])
        w.writeheader()
        for i in all_items:
            w.writerow({
                "date": today, "source": i["source"], "rank": i["rank"],
                "title": i["title"], "url": i["url"], "score": i["score"],
                "metric": i["metric"], "comments": i.get("comments", 0),
                "author": i.get("author") or "",
                "tags": "|".join(i.get("tags", [])),
                "captured_at": i["captured_at"],
            })

    idx = load_history_index()
    if today not in idx["snapshots"]:
        idx["snapshots"].append(today)
        idx["snapshots"].sort()
    with open(os.path.join(DATA_DIR, "index.json"), "w") as f:
        json.dump(idx, f, indent=2)

    write_csvs(all_items, today, now.isoformat())

    print(f"\nDone. {len(all_items)} items across {len(sections)} sources.")
    print(f"  latest:   {latest_path}")
    print(f"  snapshot: {history_path}")
    print(f"  topics:   {[t['topic'] for t in topics]}")


if __name__ == "__main__":
    main()
