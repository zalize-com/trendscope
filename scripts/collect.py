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

import concurrent.futures
import csv
import html
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


def fetch_show_hn(limit=12):
    print("Fetching Show HN launches...")
    since = int(time.time()) - 48 * 3600
    data = get_json(
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=show_hn&hitsPerPage=40&numericFilters=created_at_i>{since}"
    )
    hits = sorted((data or {}).get("hits", []),
                  key=lambda h: h.get("points", 0), reverse=True)
    out = []
    for h in hits[:limit]:
        out.append(item(
            "show_hn",
            h.get("title", ""),
            h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            h.get("points", 0),
            "points",
            tags=[t for t in (h.get("_tags") or [])
                  if not t.startswith(("author_", "story_", "poll_", "show_hn"))],
            comments=h.get("num_comments", 0),
            author=h.get("author"),
        ))
    return out


def fetch_ask_hn(limit=12):
    print("Fetching Ask HN...")
    since = int(time.time()) - 48 * 3600
    data = get_json(
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=ask_hn&hitsPerPage=40&numericFilters=created_at_i>{since}"
    )
    hits = sorted((data or {}).get("hits", []),
                  key=lambda h: h.get("points", 0), reverse=True)
    out = []
    for h in hits[:limit]:
        out.append(item(
            "ask_hn",
            h.get("title", ""),
            f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            h.get("points", 0),
            "points",
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


def fetch_lemmy(limit=15):
    """programming.dev (Lemmy) hot posts — fediverse programming community signal."""
    print("Fetching lemmy programming.dev hot...")
    data = get_json(
        "https://programming.dev/api/v3/post/list?community_name=programming&sort=Hot&limit=%d" % limit,
        headers={"User-Agent": UA})
    out = []
    for p in (data or {}).get("posts", [])[:limit]:
        po, co, cr = p.get("post", {}), p.get("counts", {}), p.get("creator", {})
        out.append(item(
            "lemmy",
            po.get("name", ""),
            po.get("url") or po.get("ap_id", ""),
            co.get("score", 0),
            "score",
            tags=[po.get("community_name") or p.get("community", {}).get("name", "")],
            comments=co.get("comments", 0),
            author=cr.get("name"),
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


def fetch_producthunt(limit=20):
    """Product Hunt daily feed — Atom XML, no vote counts, so items are
    scored by feed position (top entry gets the highest score)."""
    print("Fetching Product Hunt feed...")
    import re
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.producthunt.com/feed",
                headers={"User-Agent": UA, "Accept": "application/atom+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] producthunt attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = root.findall("a:entry", ns)
    # PH keeps deleted launches in the feed with a "-deleted-NNNN" slug;
    # note Elements are falsy when childless — compare with None explicitly
    def _href(e):
        l = e.find("a:link", ns)
        return l.get("href") if l is not None else ""
    entries = [e for e in entries if "-deleted-" not in _href(e)]
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        link = e.find("a:link", ns)
        url = link.get("href") if link is not None else "https://www.producthunt.com/"
        tagline = (e.findtext("a:summary", default="", namespaces=ns) or "").strip()
        if not tagline:
            content = (e.findtext("a:content", default="", namespaces=ns) or "")
            tagline = " ".join(re.sub(r"<[^>]+>", " ", content).split())
            tagline = html.unescape(tagline)[:200]
            tagline = re.sub(r"\s*Discussion\s*\|\s*Link\s*$", "", tagline)
        out.append(item(
            "producthunt", title, url or "https://www.producthunt.com/",
            len(entries) - i, "feed rank",
            extra={"description": tagline},
        ))
    return out


def fetch_techmeme(limit=20):
    """Techmeme RSS — editorial tech news, position-scored like producthunt."""
    print("Fetching Techmeme feed...")
    import re
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.techmeme.com/feed.xml",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] techmeme attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall("channel/item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://www.techmeme.com/"
        desc = " ".join(re.sub(r"<[^>]+>", " ", e.findtext("description", default="") or "").split())
        desc = html.unescape(desc)[:200]
        # descriptions lead with "Author / Outlet : body" — lift it into author
        m = re.match(r"^([^:]{1,80}) : ", desc)
        author = m.group(1).strip() if m else None
        out.append(item(
            "techmeme", title, url, len(entries) - i, "feed rank",
            extra={"description": desc, "author": author},
        ))
    return out


def fetch_krebs(limit=15):
    """Krebs on Security RSS — security journalism lane, position-scored."""
    print("Fetching Krebs on Security feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://krebsonsecurity.com/feed/",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] krebs attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://krebsonsecurity.com/"
        author = (e.findtext("{http://purl.org/dc/elements/1.1/}creator", default="") or "").strip() or None
        out.append(item(
            "krebs", title, url, len(entries) - i, "feed rank",
            extra={"author": author},
        ))
    return out


def fetch_changelog(limit=15):
    """Changelog News RSS — dev news/podcast lane, position-scored."""
    print("Fetching Changelog News feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://changelog.com/news/feed",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] changelog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://changelog.com/news"
        out.append(item(
            "changelog", title, url, len(entries) - i, "feed rank",
        ))
    return out


def fetch_freecodecamp(limit=15):
    """freeCodeCamp News RSS — tutorials/dev-content lane, position-scored."""
    print("Fetching freeCodeCamp News feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.freecodecamp.org/news/rss/",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] freecodecamp attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://www.freecodecamp.org/news/"
        out.append(item(
            "freecodecamp", title, url, len(entries) - i, "feed rank",
        ))
    return out


def fetch_echojs(limit=15):
    """Echo JS RSS — JavaScript community news, position-scored."""
    print("Fetching Echo JS feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.echojs.com/rss",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            # echojs emits whitespace inside tag text — tolerant parse
            root = ET.fromstring(raw)
            break
        except Exception as e:
            print(f"  [warn] echojs attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title", default="") or "").split())
        url = " ".join((e.findtext("link", default="") or "").split()) or "https://www.echojs.com/"
        out.append(item(
            "echojs", title, url, len(entries) - i, "feed rank",
        ))
    return out


def fetch_infoq(limit=15):
    """InfoQ RSS — enterprise dev news/presentations, position-scored."""
    print("Fetching InfoQ feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://feed.infoq.com/",
                headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] infoq attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://www.infoq.com/"
        out.append(item(
            "infoq", title, url, len(entries) - i, "feed rank",
        ))
    return out


def fetch_theregister(limit=15):
    """The Register — software headlines (Atom), position-scored."""
    print("Fetching The Register feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://feeds.feedburner.com/TheRegister",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] theregister attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    # despite the .atom URL the body is RSS 2.0 — parse <item>s
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "theregister", title, link.strip() or "https://www.theregister.com/software/",
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_lwn(limit=15):
    """LWN.net headlines RSS — Linux/kernel news, position-scored."""
    print("Fetching LWN feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://lwn.net/headlines/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] lwn attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://lwn.net/"
        out.append(item(
            "lwn", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_hackaday(limit=15):
    """Hackaday — hardware/maker feed, position-scored."""
    print("Fetching Hackaday feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://hackaday.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] hackaday attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://hackaday.com/"
        out.append(item(
            "hackaday", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_thenewstack(limit=15):
    """The New Stack — cloud-native/devops feed, position-scored."""
    print("Fetching The New Stack feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://thenewstack.io/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] thenewstack attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://thenewstack.io/"
        out.append(item(
            "thenewstack", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_opensourcecom(limit=15):
    """Opensource.com — Red Hat OSS community feed, position-scored."""
    print("Fetching Opensource.com feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://opensource.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] opensourcecom attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://opensource.com/"
        out.append(item(
            "opensourcecom", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_soblog(limit=15):
    """Stack Overflow Blog — dev culture RSS, position-scored."""
    print("Fetching Stack Overflow Blog feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://stackoverflow.blog/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] soblog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://stackoverflow.blog/"
        out.append(item(
            "soblog", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_codinghorror(limit=15):
    """Coding Horror — classic dev blog RSS, position-scored."""
    print("Fetching Coding Horror feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.codinghorror.com/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] codinghorror attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://blog.codinghorror.com/"
        out.append(item(
            "codinghorror", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_martinfowler(limit=15):
    """Martin Fowler — classic software engineering blog (Atom), position-scored."""
    print("Fetching Martin Fowler feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://martinfowler.com/feed.atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] martinfowler attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "martinfowler", title, link.strip() or "https://martinfowler.com/",
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_pragmatic(limit=15):
    """The Pragmatic Engineer — big SWE newsletter/blog RSS, position-scored."""
    print("Fetching Pragmatic Engineer feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.pragmaticengineer.com/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] pragmatic attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://blog.pragmaticengineer.com/"
        out.append(item(
            "pragmatic", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_bendersky(limit=15):
    """Eli Bendersky — deep-dive dev blog (Atom), position-scored."""
    print("Fetching Eli Bendersky feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://eli.thegreenplace.net/feeds/all.atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bendersky attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bendersky", title, link.strip() or "https://eli.thegreenplace.net/",
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_cheney(limit=15):
    """Dave Cheney — practical Go/engineering blog RSS, position-scored."""
    print("Fetching Dave Cheney feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://dave.cheney.net/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] cheney attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://dave.cheney.net/"
        out.append(item(
            "cheney", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_lucumr(limit=15):
    """Lucumr / Armin Ronacher — systems blog (Atom), position-scored."""
    print("Fetching Lucumr feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://lucumr.pocoo.org/feed.atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] lucumr attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "lucumr", title, link.strip() or "https://lucumr.pocoo.org/",
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_hynek(limit=15):
    """Hynek Schlawack — Python/ecosystem blog RSS, position-scored."""
    print("Fetching Hynek feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://hynek.me/articles/index.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] hynek attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or "").split())
        link = (e.findtext("link") or "").strip() or "https://hynek.me/"
        out.append(item(
            "hynek", title, link,
            len(entries) - i, "feed rank",
        ))
    return out



def fetch_susam(limit=15):
    """Susam Pal — long-form hacker blog (Atom), position-scored."""
    print("Fetching Susam feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://susam.net/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] susam attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "susam", title, link.strip() or "https://susam.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_haxx(limit=15):
    """Daniel Stenberg (curl author) — blog RSS, position-scored."""
    print("Fetching Daniel Haxx blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://daniel.haxx.se/blog/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] haxx attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "haxx", title, link.strip() or "https://daniel.haxx.se/blog/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_jvns(limit=15):
    """Julia Evans (jvns.ca) — zines/dev teaching blog (Atom), position-scored."""
    print("Fetching Julia Evans blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://jvns.ca/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] jvns attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "jvns", title, link.strip() or "https://jvns.ca/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_wingolog(limit=15):
    """Andy Wingo (wingolog) — compilers/GC deep dives (Atom), position-scored."""
    print("Fetching wingolog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://wingolog.org/feed/atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] wingolog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "wingolog", title, link.strip() or "https://wingolog.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_philopp(limit=15):
    """Phil Oppermann (os.phil-opp.com) — Writing an OS in Rust (feed), position-scored."""
    print("Fetching phil-opp blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://os.phil-opp.com/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] phil-opp attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "philopp", title, link.strip() or "https://os.phil-opp.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_sanglard(limit=15):
    """Fabien Sanglard — game-engine deep dives (RSS), position-scored."""
    print("Fetching Fabien Sanglard feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://fabiensanglard.net/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] sanglard attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "sanglard", title, link.strip() or "https://fabiensanglard.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_antirez(limit=15):
    """antirez (Salvatore Sanfilippo) — Redis author blog (RSS), position-scored."""
    print("Fetching antirez feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://antirez.com/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] antirez attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "antirez", title, link.strip() or "https://antirez.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_beesbuzz(limit=15):
    """Beesbuzz — dev longform blog (feed), position-scored."""
    print("Fetching Beesbuzz feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://beesbuzz.biz/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] beesbuzz attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "beesbuzz", title, link.strip() or "https://beesbuzz.biz/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_gargron(limit=15):
    """Gargron (Eugen Rochko) — Mastodon creator blog (RSS), position-scored."""
    print("Fetching Gargron feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://mastodon.social/@Gargron.rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] gargron attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "gargron", title, link.strip() or "https://mastodon.social/@Gargron",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_overreacted(limit=15):
    """Dan Abramov (overreacted.io) — React/longform dev blog (RSS), position-scored."""
    print("Fetching overreacted.io feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://overreacted.io/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] overreacted attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "overreacted", title, link.strip() or "https://overreacted.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_swizec(limit=15):
    """Swizec Teller — indie hacker/dev blog (RSS), position-scored."""
    print("Fetching Swizec feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://swizec.com/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] swizec attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "swizec", title, link.strip() or "https://swizec.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_kentcdodds(limit=15):
    """Kent C. Dodds — React/testing blog (RSS), position-scored."""
    print("Fetching Kent C. Dodds feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://kentcdodds.com/blog/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] kentcdodds attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "kentcdodds", title, link.strip() or "https://kentcdodds.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_cloudflare(limit=15):
    """Cloudflare Blog — infra/network engineering (RSS), position-scored."""
    print("Fetching Cloudflare Blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.cloudflare.com/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] cloudflare attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "cloudflare", title, link.strip() or "https://blog.cloudflare.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_netflix(limit=15):
    """Netflix Tech Blog — streaming platform engineering (RSS), position-scored."""
    print("Fetching Netflix Tech Blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://netflixtechblog.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] netflix attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "netflix", title, link.strip() or "https://netflixtechblog.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_github_eng(limit=15):
    """GitHub Engineering blog — platform engineering (Atom), position-scored."""
    print("Fetching GitHub Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://github.blog/engineering.atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] github_eng attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "github_eng", title, link.strip() or "https://github.blog/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_slack_eng(limit=15):
    """Slack Engineering — messaging platform engineering (RSS), position-scored."""
    print("Fetching Slack Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://slack.engineering/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] slack_eng attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "slack_eng", title, link.strip() or "https://slack.engineering/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_aws_blog(limit=15):
    """AWS News Blog — cloud announcements from Amazon (RSS), position-scored."""
    print("Fetching AWS blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://aws.amazon.com/blogs/aws/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] aws_blog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "aws_blog", title, link.strip() or "https://aws.amazon.com/blogs/aws/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_dropbox(limit=15):
    """Dropbox Tech — storage infrastructure engineering (RSS), position-scored."""
    print("Fetching Dropbox Tech feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://dropbox.tech/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] dropbox attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "dropbox", title, link.strip() or "https://dropbox.tech/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_lyft(limit=15):
    """Lyft Engineering — rideshare platform engineering (RSS), position-scored."""
    print("Fetching Lyft Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://eng.lyft.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] lyft attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "lyft", title, link.strip() or "https://eng.lyft.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_pinterest(limit=15):
    """Pinterest Engineering — visual discovery platform engineering (RSS), position-scored."""
    print("Fetching Pinterest Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://medium.com/feed/@Pinterest_Engineering",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] pinterest attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "pinterest", title, link.strip() or "https://medium.com/@Pinterest_Engineering",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_etsy(limit=15):
    """Etsy Code as Craft — marketplace engineering (RSS), position-scored."""
    print("Fetching Etsy Code as Craft feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.etsy.com/codeascraft/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] etsy attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "etsy", title, link.strip() or "https://www.etsy.com/codeascraft",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_discord(limit=15):
    """Discord Blog — chat platform engineering (RSS), position-scored."""
    print("Fetching Discord blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://discord.com/blog/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] discord attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "discord", title, link.strip() or "https://discord.com/blog",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_stripe(limit=15):
    """Stripe Blog — payments infrastructure engineering (RSS), position-scored."""
    print("Fetching Stripe blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://stripe.com/blog/feed.rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] stripe attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "stripe", title, link.strip() or "https://stripe.com/blog",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_vercel(limit=15):
    """Vercel Blog — frontend cloud platform engineering (Atom), position-scored."""
    print("Fetching Vercel blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://vercel.com/atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] vercel attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "vercel", title, link.strip() or "https://vercel.com/blog",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_meta_eng(limit=15):
    """Meta Engineering — facebook-scale infrastructure (RSS), position-scored."""
    print("Fetching Meta Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://engineering.fb.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] meta_eng attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "meta_eng", title, link.strip() or "https://engineering.fb.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_airbnb(limit=15):
    """Airbnb Engineering — marketplace infrastructure (RSS via Medium), position-scored."""
    print("Fetching Airbnb Engineering feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://medium.com/feed/airbnb-engineering",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] airbnb attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "airbnb", title, link.strip() or "https://medium.com/airbnb-engineering",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_mongodb(limit=15):
    """MongoDB Blog — database engineering (RSS), position-scored."""
    print("Fetching MongoDB blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.mongodb.com/blog/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] mongodb attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "mongodb", title, link.strip() or "https://www.mongodb.com/blog",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_elastic(limit=15):
    """Elastic Blog — search engine engineering (RSS), position-scored."""
    print("Fetching Elastic blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.elastic.co/blog/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] elastic attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "elastic", title, link.strip() or "https://www.elastic.co/blog",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_gitlab_blog(limit=15):
    """GitLab Blog — DevOps platform news (Atom), position-scored."""
    print("Fetching GitLab blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://about.gitlab.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] gitlab_blog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "gitlab_blog", title, link.strip() or "https://about.gitlab.com/blog/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_aphyr(limit=15):
    """Aphyr (Kyle Kingsbury) — Jepsen distributed-systems analyses (Atom), position-scored."""
    print("Fetching aphyr.com feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://aphyr.com/posts.atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] aphyr attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "aphyr", title, link.strip() or "https://aphyr.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_thisweek(limit=15):
    """This Week in Rust — Rust community newsletter (RSS), position-scored."""
    print("Fetching This Week in Rust feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://this-week-in-rust.org/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] thisweek attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "thisweek", title, link.strip() or "https://this-week-in-rust.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_pythonblog(limit=15):
    """Python Blog — official Python releases and announcements (RSS), position-scored."""
    print("Fetching Python blog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.python.org/feeds/posts/default",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] pythonblog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "pythonblog", title, link.strip() or "https://blog.python.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_rands(limit=15):
    """Rands in Repose — engineering management essays (RSS), position-scored."""
    print("Fetching Rands in Repose feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://randsinrepose.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] rands attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "rands", title, link.strip() or "https://randsinrepose.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_catonmat(limit=15):
    """catonmat (Peter Krumins) — unix tools and programming essays (RSS), position-scored."""
    print("Fetching catonmat feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://catonmat.net/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] catonmat attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "catonmat", title, link.strip() or "https://catonmat.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_dabeaz(limit=15):
    """David Beazley — Python wizardry and language design (Atom), position-scored."""
    print("Fetching dabeaz feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://dabeaz.blogspot.com/feeds/posts/default",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] dabeaz attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "dabeaz", title, link.strip() or "https://dabeaz.blogspot.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_mitchw(limit=15):
    """Mitchell Hashimoto — infra tooling creator (Vagrant/Terraform/Ghostty) (RSS), position-scored."""
    print("Fetching mitchellh.com feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://mitchellh.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] mitchw attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "mitchw", title, link.strip() or "https://mitchellh.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_birklund(limit=15):
    """Two-Bit History — computing history essays (Atom), position-scored."""
    print("Fetching Two-Bit History feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://twobithistory.org/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] birklund attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "birklund", title, link.strip() or "https://twobithistory.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_simonw(limit=15):
    """Simon Willison — LLM tooling and web dev essays (Atom), position-scored."""
    print("Fetching Simon Willison feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://simonwillison.net/atom/everything/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] simonw attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "simonw", title, link.strip() or "https://simonwillison.net/",
            len(entries) - i, "feed rank",
        ))
    return out





def fetch_daringfireball(limit=15):
    """Daring Fireball (John Gruber) — Apple/tech commentary (Atom), position-scored."""
    print("Fetching Daring Fireball feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://daringfireball.net/feeds/main",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] daringfireball attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "daringfireball", title, link.strip() or "https://daringfireball.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_marco(limit=15):
    """Marco Arment — indie dev and Apple ecosystem (RSS), position-scored."""
    print("Fetching Marco Arment feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://marco.org/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] marco attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "marco", title, link.strip() or "https://marco.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_danluu(limit=15):
    """Dan Luu — systems performance and career essays (RSS), position-scored."""
    print("Fetching Dan Luu feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://danluu.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] danluu attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "danluu", title, link.strip() or "https://danluu.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_stratechery(limit=15):
    """Stratechery (Ben Thompson) — tech strategy analysis (RSS), position-scored."""
    print("Fetching Stratechery feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://stratechery.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] stratechery attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "stratechery", title, link.strip() or "https://stratechery.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_baeldung(limit=15):
    """Baeldung — Java/Spring/backend tutorials (RSS mirror), position-scored."""
    print("Fetching Baeldung feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://feeds.feedburner.com/Baeldung",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] baeldung attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "baeldung", title, link.strip() or "https://www.baeldung.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_troyhunt(limit=15):
    """Troy Hunt — web security and HaveIBeenPwned (RSS), position-scored."""
    print("Fetching Troy Hunt feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.troyhunt.com/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] troyhunt attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "troyhunt", title, link.strip() or "https://www.troyhunt.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_tonsky(limit=15):
    """Nikita Tonsky Prokopov — UI design, fonts and Clojure (Atom), position-scored."""
    print("Fetching Tonsky feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://tonsky.me/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] tonsky attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "tonsky", title, link.strip() or "https://tonsky.me/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_joelonsoftware(limit=15):
    """Joel on Software (Joel Spolsky) — classic software industry essays (RSS), position-scored."""
    print("Fetching Joel on Software feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.joelonsoftware.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] joelonsoftware attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "joelonsoftware", title, link.strip() or "https://www.joelonsoftware.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_raphlinus(limit=15):
    """Raph Levien — GUI/text rendering and Rust UI (Atom) (Atom), position-scored."""
    print("Fetching Raph Levien feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://raphlinus.github.io/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] raphlinus attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "raphlinus", title, link.strip() or "https://raphlinus.github.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_xeiaso(limit=15):
    """Xe Iaso — tech essays and homelab lore (RSS) (RSS), position-scored."""
    print("Fetching Xe Iaso feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://xeiaso.net/blog.rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] xeiaso attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "xeiaso", title, link.strip() or "https://xeiaso.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_jetbrains(limit=15):
    """JetBrains Blog — IDE and tooling news (RSS) (RSS), position-scored."""
    print("Fetching JetBrains feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.jetbrains.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] jetbrains attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "jetbrains", title, link.strip() or "https://blog.jetbrains.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_tedinski(limit=15):
    """Ted Kaminski — programming language theory (Atom) (Atom), position-scored."""
    print("Fetching Tedinski feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.tedinski.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] tedinski attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "tedinski", title, link.strip() or "https://www.tedinski.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_drmaciver(limit=15):
    """David R. MacIver — Hypothesis/property testing (RSS) (RSS), position-scored."""
    print("Fetching DRMacIver feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://drmaciver.substack.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] drmaciver attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "drmaciver", title, link.strip() or "https://drmaciver.substack.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_matklad(limit=15):
    """matklad (Alex Kladov) — Rust-analyzer and compilers (Atom) (Atom), position-scored."""
    print("Fetching matklad feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://matklad.github.io/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] matklad attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "matklad", title, link.strip() or "https://matklad.github.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_grumpyg(limit=15):
    """Grumpy Old Geek — veteran engineer commentary (RSS) (RSS), position-scored."""
    print("Fetching GrumpyOldGeek feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://grumpyoldgeek.tumblr.com/rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] grumpyg attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "grumpyg", title, link.strip() or "https://grumpyoldgeek.tumblr.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_chriskiehl(limit=15):
    """Chris Kiehl — Gooey author, dev tooling (RSS) (RSS), position-scored."""
    print("Fetching Chris Kiehl feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://chriskiehl.com/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] chriskiehl attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "chriskiehl", title, link.strip() or "https://chriskiehl.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_dimitri(limit=15):
    """Dimitri Fontaine — PostgreSQL and Emacs (RSS) (RSS), position-scored."""
    print("Fetching Dimitri Fontaine feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://tapoueh.org/index.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] dimitri attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "dimitri", title, link.strip() or "https://tapoueh.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_hillel(limit=15):
    """Hillel Wayne — formal methods and TLA+ (RSS) (RSS), position-scored."""
    print("Fetching Hillel Wayne feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.hillelwayne.com/post/index.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] hillel attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "hillel", title, link.strip() or "https://www.hillelwayne.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_ridiculousfish(limit=15):
    """Ridiculous Fish — fish shell author, low-level dev (Atom) (Atom), position-scored."""
    print("Fetching Ridiculous Fish feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://ridiculousfish.com/blog/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] ridiculousfish attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "ridiculousfish", title, link.strip() or "https://ridiculousfish.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_nadia(limit=15):
    """Nadia Eghbal — open source economics (Atom) (Atom), position-scored."""
    print("Fetching Nadia Eghbal feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://nadia.xyz/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] nadia attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "nadia", title, link.strip() or "https://nadia.xyz/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_henrikwarne(limit=15):
    """Henrik Warne — programming practice essays (RSS) (RSS), position-scored."""
    print("Fetching Henrik Warne feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://henrikwarne.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] henrikwarne attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "henrikwarne", title, link.strip() or "https://henrikwarne.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_charity(limit=15):
    """Charity Majors — observability and eng leadership (RSS) (RSS), position-scored."""
    print("Fetching Charity Majors feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://charity.wtf/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] charity attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "charity", title, link.strip() or "https://charity.wtf/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_surfingcomplexity(limit=15):
    """Surfing Complexity — resilience engineering (RSS) (RSS), position-scored."""
    print("Fetching Surfing Complexity feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://surfingcomplexity.blog/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] surfingcomplexity attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "surfingcomplexity", title, link.strip() or "https://surfingcomplexity.blog/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_lorinhochstein(limit=15):
    """Lorin Hochstein — software essays and book notes (RSS) (RSS), position-scored."""
    print("Fetching Lorin Hochstein feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://lorinhochstein.wordpress.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] lorinhochstein attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "lorinhochstein", title, link.strip() or "https://lorinhochstein.wordpress.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_geshan(limit=15):
    """Geshan Manandhar — software engineering tutorials (Atom) (Atom), position-scored."""
    print("Fetching Geshan feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://geshan.com.np/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] geshan attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "geshan", title, link.strip() or "https://geshan.com.np/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_mtlynch(limit=15):
    """Michael Lynch — indie hacking and SRE retros (RSS) (RSS), position-scored."""
    print("Fetching mtlynch feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://mtlynch.io/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] mtlynch attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "mtlynch", title, link.strip() or "https://mtlynch.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_nelhage(limit=15):
    """Nelson Elhage — systems and tooling deep dives (RSS) (RSS), position-scored."""
    print("Fetching Nelson Elhage feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.nelhage.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] nelhage attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "nelhage", title, link.strip() or "https://blog.nelhage.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_schneems(limit=15):
    """Richard Schneeman — Ruby performance and open source (Atom), position-scored."""
    print("Fetching Schneems feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.schneems.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
            break
        except Exception as e:
            print(f"  [warn] schneems attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    # schneems.com emits non-well-formed Atom (raw & and " inside attributes)
    # -> regex extraction fallback instead of ET
    import re as _re
    blocks = _re.findall(r"<entry>(.*?)</entry>", body, _re.S)[:limit]
    out = []
    for i, b in enumerate(blocks):
        mt = _re.search(r"<title[^>]*>(.*?)</title>", b, _re.S)
        ml = _re.search(r"<link[^>]+href=\"([^\"]+)\"", b)
        title = " ".join((html.unescape(mt.group(1)) if mt else "").split())
        link = ml.group(1) if ml else ""
        out.append(item(
            "schneems", title, link.strip() or "https://www.schneems.com/",
            len(blocks) - i, "feed rank",
        ))
    return out


def fetch_lcamtuf(limit=15):
    """Michal Zalewski — security research and essays (RSS) (RSS), position-scored."""
    print("Fetching lcamtuf feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://lcamtuf.substack.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] lcamtuf attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "lcamtuf", title, link.strip() or "https://lcamtuf.substack.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_copyconstruct(limit=15):
    """Cindy Sridharan — distributed systems essays (RSS) (RSS), position-scored."""
    print("Fetching Copy Construct feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://copyconstruct.medium.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] copyconstruct attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "copyconstruct", title, link.strip() or "https://copyconstruct.medium.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_verdagon(limit=15):
    """Verdagon — Vale language design (RSS) (RSS), position-scored."""
    print("Fetching Verdagon feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://verdagon.dev/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] verdagon attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "verdagon", title, link.strip() or "https://verdagon.dev/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bitbashing(limit=15):
    """BitBashing — low-level systems essays (RSS) (RSS), position-scored."""
    print("Fetching BitBashing feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://bitbashing.io/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bitbashing attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bitbashing", title, link.strip() or "https://bitbashing.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_ntietz(limit=15):
    """Nicholas Tietz — distributed systems essays (Atom) (Atom), position-scored."""
    print("Fetching ntietz feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://ntietz.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] ntietz attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "ntietz", title, link.strip() or "https://ntietz.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_murat(limit=15):
    """Murat Demirbas — distributed systems papers blog (Atom) (Atom), position-scored."""
    print("Fetching Murat Demirbas feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://muratbuffalo.blogspot.com/feeds/posts/default",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] murat attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "murat", title, link.strip() or "https://muratbuffalo.blogspot.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_begriffs(limit=15):
    """Joe Nelson — API design and Postgres (Atom) (Atom), position-scored."""
    print("Fetching Begriffs feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://begriffs.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] begriffs attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "begriffs", title, link.strip() or "https://begriffs.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_gds(limit=15):
    """UK Government Digital Service blog (Atom) (Atom), position-scored."""
    print("Fetching GDS feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://gds.blog.gov.uk/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] gds attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "gds", title, link.strip() or "https://gds.blog.gov.uk/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bitslog(limit=15):
    """Sergio Schvezov — security research (RSS) (RSS), position-scored."""
    print("Fetching BitsLog feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://bitslog.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bitslog attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bitslog", title, link.strip() or "https://bitslog.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_roytang(limit=15):
    """Roy Tang — dev notes and links (RSS) (RSS), position-scored."""
    print("Fetching Roy Tang feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://roytang.net/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] roytang attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "roytang", title, link.strip() or "https://roytang.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_tbray(limit=15):
    """Tim Bray — XML inventor, tech commentary (Atom) (Atom), position-scored."""
    print("Fetching Tim Bray feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.tbray.org/ongoing/ongoing.atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] tbray attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "tbray", title, link.strip() or "https://www.tbray.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bertrand(limit=15):
    """Bertrand Meyer — Eiffel creator, SE methodology (RSS) (RSS), position-scored."""
    print("Fetching Bertrand Meyer feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://bertrandmeyer.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bertrand attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bertrand", title, link.strip() or "https://bertrandmeyer.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bret(limit=15):
    """Bret Victor — dynamic media and computing essays (Atom) (Atom), position-scored."""
    print("Fetching Bret Victor feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "http://worrydream.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bret attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bret", title, link.strip() or "http://worrydream.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_codemadness(limit=15):
    """codemadness — suckless-style minimal Unix tooling (Atom), position-scored."""
    print("Fetching codemadness feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://codemadness.org/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] codemadness attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "codemadness", title, link.strip() or "https://codemadness.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_jacobian(limit=15):
    """Jacob Kaplan-Moss — Django co-creator, eng leadership (RSS) (RSS), position-scored."""
    print("Fetching Jacob Kaplan-Moss feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://jacobian.org/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] jacobian attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "jacobian", title, link.strip() or "https://jacobian.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_karl(limit=15):
    """Karl Voit — Org mode and PIM (Atom) (Atom), position-scored."""
    print("Fetching Karl Voit feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://karl-voit.at/feeds/lazyblorg-all.atom_1.0.links-and-content.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] karl attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "karl", title, link.strip() or "https://karl-voit.at/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_gwern(limit=15):
    """Gwern Branwen — longform research essays (RSS) (RSS), position-scored."""
    print("Fetching Gwern feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://gwern.net/index.rss",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] gwern attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "gwern", title, link.strip() or "https://gwern.net/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_andrewkelley(limit=15):
    """Andrew Kelley — Zig creator (RSS) (RSS), position-scored."""
    print("Fetching Andrew Kelley feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://andrewkelley.me/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] andrewkelley attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "andrewkelley", title, link.strip() or "https://andrewkelley.me/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_joeduffy(limit=15):
    """Joe Duffy — Midori/systems essays (RSS) (RSS), position-scored."""
    print("Fetching Joe Duffy feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "http://joeduffyblog.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] joeduffy attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "joeduffy", title, link.strip() or "http://joeduffyblog.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bravenewgeek(limit=15):
    """Tyler Treat — distributed systems essays (RSS) (RSS), position-scored."""
    print("Fetching Brave New Geek feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://bravenewgeek.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bravenewgeek attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bravenewgeek", title, link.strip() or "https://bravenewgeek.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_ciechanow(limit=15):
    """Bartosz Ciechanowski — interactive visual essays (RSS) (RSS), position-scored."""
    print("Fetching Ciechanowski feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://ciechanow.ski/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] ciechanow attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "ciechanow", title, link.strip() or "https://ciechanow.ski/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_mikeash(limit=15):
    """Mike Ash — Friday Q&A systems blog (RSS) (RSS), position-scored."""
    print("Fetching mikeash feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://mikeash.com/pyblog/rss.py",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] mikeash attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "mikeash", title, link.strip() or "https://mikeash.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_fogus(limit=15):
    """Fogus — Clojure and programming languages (RSS) (RSS), position-scored."""
    print("Fetching fogus feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.fogus.me/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] fogus attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "fogus", title, link.strip() or "https://blog.fogus.me/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_ncase(limit=15):
    """Nicky Case — explorable explanations and interactive essays (Atom), position-scored."""
    print("Fetching ncase feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://blog.ncase.me/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] ncase attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "ncase", title, link.strip() or "https://ncase.me/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_jwz(limit=15):
    """Jamie Zawinski — Netscape co-founder, jwz blog (RSS) (RSS), position-scored."""
    print("Fetching jwz feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.jwz.org/blog/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] jwz attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "jwz", title, link.strip() or "https://www.jwz.org/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_steveblank(limit=15):
    """Steve Blank — startup methodology (RSS) (RSS), position-scored."""
    print("Fetching Steve Blank feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://steveblank.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] steveblank attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "steveblank", title, link.strip() or "https://steveblank.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_zackkanter(limit=15):
    """Zack Kanter — startups and strategy (RSS) (RSS), position-scored."""
    print("Fetching Zack Kanter feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://zackkanter.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] zackkanter attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "zackkanter", title, link.strip() or "https://zackkanter.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_robinrendle(limit=15):
    """Robin Rendle — front-end craft essays (Atom) (Atom), position-scored."""
    print("Fetching Robin Rendle feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://robinrendle.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] robinrendle attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "robinrendle", title, link.strip() or "https://robinrendle.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_terrytao(limit=15):
    """Terence Tao — math research notes (RSS) (RSS), position-scored."""
    print("Fetching Terence Tao feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://terrytao.wordpress.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] terrytao attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "terrytao", title, link.strip() or "https://terrytao.wordpress.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_norvig(limit=15):
    """Peter Norvig — AI classic essays (RSS) (RSS), position-scored."""
    print("Fetching Peter Norvig feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "http://norvig.com/rss-feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] norvig attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "norvig", title, link.strip() or "http://norvig.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_gamasutra(limit=15):
    """GameDeveloper.com — game industry news (RSS) (RSS), position-scored."""
    print("Fetching GameDeveloper feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.gamedeveloper.com/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] gamasutra attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "gamasutra", title, link.strip() or "https://www.gamedeveloper.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_thisdavej(limit=15):
    """ThisDaveJ — Node.js and maker tutorials (RSS) (RSS), position-scored."""
    print("Fetching ThisDaveJ feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://thisdavej.com/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] thisdavej attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "thisdavej", title, link.strip() or "https://thisdavej.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_x065(limit=15):
    """0x65 — low-level systems research (Atom) (Atom), position-scored."""
    print("Fetching 0x65 feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://0x65.dev/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] x065 attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "x065", title, link.strip() or "https://0x65.dev/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_shkspr(limit=15):
    """Terence Eden — open tech and government digital (RSS) (RSS), position-scored."""
    print("Fetching Terence Eden feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://shkspr.mobi/blog/feed/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] shkspr attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "shkspr", title, link.strip() or "https://shkspr.mobi/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_daverupert(limit=15):
    """Dave Rupert — front-end and web components (RSS) (RSS), position-scored."""
    print("Fetching Dave Rupert feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://daverupert.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] daverupert attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "daverupert", title, link.strip() or "https://daverupert.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_bobmonsour(limit=15):
    """Bob Monsour — personal tech essays (Atom) (Atom), position-scored."""
    print("Fetching Bob Monsour feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.bobmonsour.com/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] bobmonsour attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "bobmonsour", title, link.strip() or "https://www.bobmonsour.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_justinpot(limit=15):
    """Justin Pot — productivity and software writing (RSS) (RSS), position-scored."""
    print("Fetching Justin Pot feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://justinpot.com/rss/",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] justinpot attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "justinpot", title, link.strip() or "https://justinpot.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_jakelazaroff(limit=15):
    """Jake Lazaroff — web tech deep-dives (RSS) (RSS), position-scored."""
    print("Fetching Jake Lazaroff feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://jakelazaroff.com/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] jakelazaroff attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "jakelazaroff", title, link.strip() or "https://jakelazaroff.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_wcedmisten(limit=15):
    """William Edmisten — geospatial and data notes (RSS) (RSS), position-scored."""
    print("Fetching William Edmisten feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://wcedmisten.fyi/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] wcedmisten attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "wcedmisten", title, link.strip() or "https://wcedmisten.fyi/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_prog21(limit=15):
    """prog21 — James Hague programming essays (Atom) (Atom), position-scored."""
    print("Fetching Programming in the 21st Century feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://prog21.dadgum.com/atom.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] prog21 attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "prog21", title, link.strip() or "https://prog21.dadgum.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_danielmiessler(limit=15):
    """Daniel Miessler — security and AI analysis (RSS) (RSS), position-scored."""
    print("Fetching Daniel Miessler feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://danielmiessler.com/feed",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] danielmiessler attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "danielmiessler", title, link.strip() or "https://danielmiessler.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_swyx(limit=15):
    """swyx — AI engineering and learning in public (RSS) (RSS), position-scored."""
    print("Fetching swyx feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.swyx.io/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] swyx attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "swyx", title, link.strip() or "https://www.swyx.io/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_samwho(limit=15):
    """Sam Rose — visual systems essays, samwho (Atom) (Atom), position-scored."""
    print("Fetching Sam Rose feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://samwho.dev/rss.xml",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] samwho attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "samwho", title, link.strip() or "https://samwho.dev/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_rauchg(limit=15):
    """Guillermo Rauch — Vercel CEO writing (Atom) (Atom), position-scored."""
    print("Fetching Guillermo Rauch feed...")
    import xml.etree.ElementTree as ET
    ATOM = "{http://www.w3.org/2005/Atom}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://rauchg.com/atom",
                headers={"User-Agent": "Mozilla/5.0 trendscope"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] rauchg attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    entries = root.findall(".//item") or root.findall(f"{ATOM}entry")
    entries = entries[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext("title") or e.findtext(f"{ATOM}title", default="") or "").split())
        link = e.findtext("link") or ""
        if not link:
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        out.append(item(
            "rauchg", title, link.strip() or "https://rauchg.com/",
            len(entries) - i, "feed rank",
        ))
    return out


def fetch_slashdot(limit=15):
    """Slashdot RSS 1.0 (RDF) — nerd news, position-scored like techmeme."""
    print("Fetching Slashdot feed...")
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://rss.slashdot.org/Slashdot/slashdotMain",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] slashdot attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    R = "{http://purl.org/rss/1.0/}"
    entries = root.findall(f"{R}item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext(f"{R}title", default="") or "").strip()
        url = (e.findtext(f"{R}link", default="") or "").strip() or "https://slashdot.org/"
        author = (e.findtext("{http://purl.org/dc/elements/1.1/}creator", default="") or "").strip() or None
        out.append(item(
            "slashdot", title, url, len(entries) - i, "feed rank",
            extra={"author": author},
        ))
    return out


def fetch_arstechnica(limit=15):
    """Ars Technica RSS — long-form tech editorial, position-scored like techmeme."""
    print("Fetching Ars Technica feed...")
    import re
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://feeds.arstechnica.com/arstechnica/index",
                headers={"User-Agent": UA, "Accept": "application/rss+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] arstechnica attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    DC = "{http://purl.org/dc/elements/1.1/}"
    entries = root.findall("channel/item")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = (e.findtext("title", default="") or "").strip()
        url = (e.findtext("link", default="") or "").strip() or "https://arstechnica.com/"
        desc = " ".join(re.sub(r"<[^>]+>", " ", e.findtext("description", default="") or "").split())
        desc = html.unescape(desc)[:200]
        author = (e.findtext(f"{DC}creator", default="") or "").strip() or None
        out.append(item(
            "arstechnica", title, url, len(entries) - i, "feed rank",
            extra={"description": desc, "author": author},
        ))
    return out


def fetch_theverge(limit=15):
    """The Verge Atom feed — mainstream tech news, position-scored like techmeme."""
    print("Fetching The Verge feed...")
    import re
    import xml.etree.ElementTree as ET
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://www.theverge.com/rss/index.xml",
                headers={"User-Agent": UA, "Accept": "application/atom+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] theverge attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = root.findall("a:entry", ns)[:limit]
    out = []
    for i, e in enumerate(entries):
        title = html.unescape(
            (e.findtext("a:title", default="", namespaces=ns) or "").strip())
        url = ""
        for l in e.findall("a:link", ns):
            if l.get("rel", "alternate") == "alternate" and l.get("href"):
                url = l.get("href")
                break
        url = url or "https://www.theverge.com/"
        desc = " ".join(re.sub(r"<[^>]+>", " ",
            e.findtext("a:summary", default="", namespaces=ns) or "").split())
        desc = html.unescape(desc)[:200]
        author = (e.findtext("a:author/a:name", default="", namespaces=ns) or "").strip() or None
        tags = [c.get("term") for c in e.findall("a:category", ns) if c.get("term")][:4]
        out.append(item(
            "theverge", title, url, len(entries) - i, "feed rank",
            tags=tags or None,
            extra={"description": desc, "author": author},
        ))
    return out


def fetch_arxiv(limit=15):
    """arXiv recent CS submissions — research attention signal, position-scored."""
    print("Fetching arXiv recent...")
    import xml.etree.ElementTree as ET
    url = ("https://export.arxiv.org/api/query?search_query="
           "cat:cs.AI%20OR%20cat:cs.CL%20OR%20cat:cs.SE%20OR%20cat:cs.LG"
           "&sortBy=submittedDate&sortOrder=descending&max_results=" + str(limit))
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/atom+xml"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"  [warn] arxiv attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return []
    A = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(f"{A}entry")[:limit]
    out = []
    for i, e in enumerate(entries):
        title = " ".join((e.findtext(f"{A}title", default="") or "").split())
        link = e.findtext(f"{A}id", default="") or ""
        cats = [c.get("term") for c in e.findall(f"{A}category") if c.get("term")]
        authors = [a.findtext(f"{A}name", default="") for a in e.findall(f"{A}author")]
        out.append(item(
            "arxiv", title, link or "https://arxiv.org/",
            len(entries) - i, "arxiv recent",
            tags=cats[:4],
            author=authors[0] if authors else None,
            extra={"authors_count": len(authors)},
        ))
    return out


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
        data = get_json(f"https://pypistats.org/api/packages/{pkg}/recent",
                        retries=4)
        if data and "data" in data:
            out.append(item(
                "pypi", pkg,
                f"https://pypi.org/project/{pkg}/",
                data["data"].get("last_month", 0), "monthly downloads",
                tags=["pypi"],
            ))
        # pypistats 429s on bursts — keep well under 1 req/s
        time.sleep(2.0)
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

    fetchers = {
        "hackernews": fetch_hackernews,
        "show_hn": fetch_show_hn,
        "ask_hn": fetch_ask_hn,
        "lobsters": fetch_lobsters,
        "devto": fetch_devto,
        "lemmy": fetch_lemmy,
        "producthunt": fetch_producthunt,
        "techmeme": fetch_techmeme,
        "slashdot": fetch_slashdot,
        "krebs": fetch_krebs,
        "changelog": fetch_changelog,
        "freecodecamp": fetch_freecodecamp,
        "echojs": fetch_echojs,
        "infoq": fetch_infoq,
        "theregister": fetch_theregister,
        "lwn": fetch_lwn,
        "hackaday": fetch_hackaday,
        "thenewstack": fetch_thenewstack,
        "opensourcecom": fetch_opensourcecom,
        "soblog": fetch_soblog,
        "codinghorror": fetch_codinghorror,
        "martinfowler": fetch_martinfowler,
        "pragmatic": fetch_pragmatic,
        "bendersky": fetch_bendersky,
        "cheney": fetch_cheney,
        "lucumr": fetch_lucumr,
        "simonw": fetch_simonw,
        "daringfireball": fetch_daringfireball,
        "marco": fetch_marco,
        "danluu": fetch_danluu,
        "stratechery": fetch_stratechery,
        "baeldung": fetch_baeldung,
        "troyhunt": fetch_troyhunt,
        "tonsky": fetch_tonsky,
        "joelonsoftware": fetch_joelonsoftware,
        "raphlinus": fetch_raphlinus,
        "xeiaso": fetch_xeiaso,
        "jetbrains": fetch_jetbrains,
        "tedinski": fetch_tedinski,
        "drmaciver": fetch_drmaciver,
        "matklad": fetch_matklad,
        "grumpyg": fetch_grumpyg,
        "chriskiehl": fetch_chriskiehl,
        "dimitri": fetch_dimitri,
        "hillel": fetch_hillel,
        "ridiculousfish": fetch_ridiculousfish,
        "nadia": fetch_nadia,
        "henrikwarne": fetch_henrikwarne,
        "charity": fetch_charity,
        "surfingcomplexity": fetch_surfingcomplexity,
        "lorinhochstein": fetch_lorinhochstein,
        "geshan": fetch_geshan,
        "mtlynch": fetch_mtlynch,
        "nelhage": fetch_nelhage,
        "schneems": fetch_schneems,
        "lcamtuf": fetch_lcamtuf,
        "copyconstruct": fetch_copyconstruct,
        "verdagon": fetch_verdagon,
        "bitbashing": fetch_bitbashing,
        "ntietz": fetch_ntietz,
        "murat": fetch_murat,
        "begriffs": fetch_begriffs,
        "gds": fetch_gds,
        "bitslog": fetch_bitslog,
        "roytang": fetch_roytang,
        "tbray": fetch_tbray,
        "bertrand": fetch_bertrand,
        "bret": fetch_bret,
        "codemadness": fetch_codemadness,
        "jacobian": fetch_jacobian,
        "karl": fetch_karl,
        "gwern": fetch_gwern,
        "andrewkelley": fetch_andrewkelley,
        "joeduffy": fetch_joeduffy,
        "bravenewgeek": fetch_bravenewgeek,
        "ciechanow": fetch_ciechanow,
        "mikeash": fetch_mikeash,
        "fogus": fetch_fogus,
        "ncase": fetch_ncase,
        "jwz": fetch_jwz,
        "steveblank": fetch_steveblank,
        "zackkanter": fetch_zackkanter,
        "robinrendle": fetch_robinrendle,
        "terrytao": fetch_terrytao,
        "norvig": fetch_norvig,
        "gamasutra": fetch_gamasutra,
        "thisdavej": fetch_thisdavej,
        "x065": fetch_x065,
        "shkspr": fetch_shkspr,
        "daverupert": fetch_daverupert,
        "bobmonsour": fetch_bobmonsour,
        "justinpot": fetch_justinpot,
        "jakelazaroff": fetch_jakelazaroff,
        "wcedmisten": fetch_wcedmisten,
        "prog21": fetch_prog21,
        "danielmiessler": fetch_danielmiessler,
        "swyx": fetch_swyx,
        "samwho": fetch_samwho,
        "rauchg": fetch_rauchg,
        "hynek": fetch_hynek,
        "susam": fetch_susam,
        "haxx": fetch_haxx,
        "jvns": fetch_jvns,
        "wingolog": fetch_wingolog,
        "philopp": fetch_philopp,
        "sanglard": fetch_sanglard,
        "antirez": fetch_antirez,
        "beesbuzz": fetch_beesbuzz,
        "gargron": fetch_gargron,
        "overreacted": fetch_overreacted,
        "swizec": fetch_swizec,
        "kentcdodds": fetch_kentcdodds,
        "cloudflare": fetch_cloudflare,
        "netflix": fetch_netflix,
        "github_eng": fetch_github_eng,
        "slack_eng": fetch_slack_eng,
        "aws_blog": fetch_aws_blog,
        "dropbox": fetch_dropbox,
        "lyft": fetch_lyft,
        "pinterest": fetch_pinterest,
        "etsy": fetch_etsy,
        "discord": fetch_discord,
        "stripe": fetch_stripe,
        "vercel": fetch_vercel,
        "meta_eng": fetch_meta_eng,
        "airbnb": fetch_airbnb,
        "mongodb": fetch_mongodb,
        "elastic": fetch_elastic,
        "gitlab_blog": fetch_gitlab_blog,
        "aphyr": fetch_aphyr,
        "thisweek": fetch_thisweek,
        "pythonblog": fetch_pythonblog,
        "rands": fetch_rands,
        "catonmat": fetch_catonmat,
        "dabeaz": fetch_dabeaz,
        "mitchw": fetch_mitchw,
        "birklund": fetch_birklund,
        "arstechnica": fetch_arstechnica,
        "theverge": fetch_theverge,
        "arxiv": fetch_arxiv,
        "github_trending": fetch_github_trending,
        "npm": fetch_npm_downloads,
        "pypi": fetch_pypi_downloads,
        "crates": fetch_crates,
    }
    # Fetchers are independent — run them concurrently (slowest source bounds
    # the run instead of the sum of all sources).
    sections, health = {}, {}

    def run_one(item):
        name, fn = item
        t0 = time.time()
        try:
            items = fn()
        except Exception as e:
            items = []
            print(f"  {name}: FAILED {e}")
        return name, items, int((time.time() - t0) * 1000)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for name, items, ms in pool.map(run_one, fetchers.items()):
            sections[name] = items
            health[name] = {"ok": bool(items), "items": len(items), "ms": ms}
    with open(os.path.join(DATA_DIR, "health.json"), "w") as f:
        json.dump({"generated_at": now.isoformat(), "sources": health}, f, indent=2)

    # Append-only per-source health log — powers the "N consecutive green days"
    # badge on the dashboard.
    hlog = os.path.join(DATA_DIR, "health-log.csv")
    new_file = not os.path.exists(hlog)
    with open(hlog, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "source", "ok", "items", "ms"])
        for name, h in health.items():
            w.writerow([today, name, int(h["ok"]), h["items"], h["ms"]])

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

    # Per-day topic counts, append-only (time-series for analysts).
    tcsv = os.path.join(DATA_DIR, "topics-history.csv")
    tnew = not os.path.exists(tcsv)
    tdone = set()
    if not tnew:
        with open(tcsv, newline="") as f:
            tdone = {(r["date"], r["topic"]) for r in csv.DictReader(f)}
    with open(tcsv, "a", newline="") as f:
        w = csv.writer(f)
        if tnew:
            w.writerow(["date", "topic", "count", "total_score"])
        for t in topics:
            if (today, t["topic"]) not in tdone:
                w.writerow([today, t["topic"], t["count"], t["total_score"]])

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
