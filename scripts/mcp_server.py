#!/usr/bin/env python3
"""trendscope MCP server — stdio JSON-RPC, stdlib only.

Exposes the open dataset (raw.githubusercontent.com/zalize-com/trendscope)
as read-only MCP tools so AI agents can query it without scraping.

Usage (e.g. Claude Code / any MCP client):
    python3 scripts/mcp_server.py
or add the repo-root .mcp.json to your client config.
"""
import gzip
import json
import os
import sys
import urllib.request

RAW = os.environ.get(
    "TRENDSCOPE_BASE",
    "https://raw.githubusercontent.com/zalize-com/trendscope/main/",
).rstrip("/") + "/"
PROTOCOL_VERSION = "2024-11-05"
UA = {"User-Agent": "trendscope-mcp/1.0 (+https://trendscope.zalize.com)"}


def fetch(path):
    req = urllib.request.Request(RAW + path, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError:
        if not path.endswith(".gz"):
            req = urllib.request.Request(RAW + path + ".gz", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(gzip.decompress(r.read()))
        raise


def _item_row(it):
    if not isinstance(it, dict):
        return str(it)
    keep = ("source", "rank", "title", "url", "score", "comments", "author")
    return {k: it[k] for k in keep if it.get(k) is not None}


def _all_items(d):
    """Flatten latest-lite items {source_key: [item, ...]} into one list."""
    out = []
    for v in (d.get("items") or {}).values():
        out.extend(v)
    return out


def tool_latest(args):
    d = fetch("data/latest-lite.json")
    items = _all_items(d)
    items.sort(key=lambda i: (-(i.get("score") or 0), i.get("rank") or 999))
    top = [_item_row(i) for i in items[: int(args.get("limit", 20))]]
    return {"date": d.get("date"), "generated_at": d.get("generated_at"),
            "total_items": d.get("total_items"), "live_sources":
            sum(1 for v in (d.get("sources") or {}).values() if v), "top_items": top}


def tool_items(args):
    src = (args.get("source") or "").strip()
    if not src:
        return {"error": "source is required"}
    d = fetch("data/latest-lite.json")
    rows = [_item_row(i) for i in (d.get("items") or {}).get(src) or []]
    return {"source": src, "count": len(rows),
            "items": rows[: int(args.get("limit", 50))]}


def tool_search(args):
    q = (args.get("query") or "").strip().lower()
    if not q:
        return {"error": "query is required"}
    d = fetch("data/latest-lite.json")
    hits = [i for i in _all_items(d)
            if q in (i.get("title") or "").lower() or q in (i.get("url") or "").lower()]
    return {"query": q, "count": len(hits),
            "items": [_item_row(i) for i in hits[: int(args.get("limit", 50))]]}


def tool_feeds(args):
    d = fetch("data/feeds.json")
    feeds = d.get("feeds") or []
    lane = (args.get("lane") or "").strip()
    if lane:
        feeds = [f for f in feeds if f.get("lane") == lane or str(f.get("key", "")).startswith(lane)]
    slim = [{k: f.get(k) for k in ("key", "label", "feed", "lane", "dormant") if f.get(k) is not None}
            for f in feeds]
    return {"count": len(slim), "feeds": slim[: int(args.get("limit", 200))]}


def tool_health(_args):
    d = fetch("data/zerowatch.json")
    return {"rounds": d.get("rounds"),
            "persistent_empty": len(d.get("persistent_empty") or []),
            "tide": len(d.get("tide") or []),
            "persistent_empty_sources": (d.get("persistent_empty") or [])[:100]}


def tool_topics(_args):
    d = fetch("data/latest-lite.json")
    return {"date": d.get("date"), "topics": d.get("topics")}


def tool_day(args):
    """Historical daily snapshot — the dataset's time-travel endpoint."""
    date = (args.get("date") or "").strip()
    if not date:
        return {"error": "date is required (YYYY-MM-DD)"}
    d = fetch(f"data/daily/{date}.json")
    items = d.get("items") or []
    if isinstance(items, dict):
        items = [i for v in items.values() for i in v]
    return {"date": date,
            "sources": len(d.get("sources") or {}),
            "total_items": len(items),
            "top_items": [_item_row(i) for i in items[: int(args.get("limit", 20))]]}


TOOLS = {
    "trendscope_latest": {
        "fn": tool_latest,
        "description": "Latest daily snapshot: date, item count and top-ranked items across 9,200+ developer sources (HN, GitHub, blogs, newsletters, YouTube, Reddit, security...).",
        "inputSchema": {"type": "object",
                        "properties": {"limit": {"type": "integer", "default": 20}},
                        "additionalProperties": False},
    },
    "trendscope_items": {
        "fn": tool_items,
        "description": "Items captured for one source key (e.g. 'hackernews', 'github_trending', 'sec_krebs').",
        "inputSchema": {"type": "object",
                        "properties": {"source": {"type": "string"},
                                       "limit": {"type": "integer", "default": 50}},
                        "required": ["source"], "additionalProperties": False},
    },
    "trendscope_search": {
        "fn": tool_search,
        "description": "Substring search over today's item titles and URLs.",
        "inputSchema": {"type": "object",
                        "properties": {"query": {"type": "string"},
                                       "limit": {"type": "integer", "default": 50}},
                        "required": ["query"], "additionalProperties": False},
    },
    "trendscope_feeds": {
        "fn": tool_feeds,
        "description": "RSS/Atom feed directory (9,200+ feeds) with health flags; optional lane filter.",
        "inputSchema": {"type": "object",
                        "properties": {"lane": {"type": "string"},
                                       "limit": {"type": "integer", "default": 200}},
                        "additionalProperties": False},
    },
    "trendscope_health": {
        "fn": tool_health,
        "description": "Source-health telemetry: sources empty for several consecutive snapshots (suspected dead) and current rate-limit tide.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "trendscope_topics": {
        "fn": tool_topics,
        "description": "Topic clusters computed over today's snapshot.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "trendscope_day": {
        "fn": tool_day,
        "description": "Historical daily snapshot (time travel): pass a past date YYYY-MM-DD to replay that day.",
        "inputSchema": {"type": "object",
                        "properties": {"date": {"type": "string"},
                                       "limit": {"type": "integer", "default": 20}},
                        "required": ["date"], "additionalProperties": False},
    },
}


def reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle(msg):
    method = msg.get("method")
    rid = msg.get("id")
    if method == "initialize":
        return reply(rid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "trendscope", "version": "1.0.0"},
        })
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return reply(rid, {})
    if method == "tools/list":
        return reply(rid, {"tools": [
            {"name": n, "description": t["description"], "inputSchema": t["inputSchema"]}
            for n, t in TOOLS.items()]})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        tool = TOOLS.get(name)
        if not tool:
            return reply(rid, error={"code": -32602, "message": f"unknown tool {name!r}"})
        try:
            out = tool["fn"](params.get("arguments") or {})
        except Exception as e:  # network/json errors surface as tool errors
            return reply(rid, {"content": [{"type": "text", "text": f"error: {e}"}],
                               "isError": True})
        return reply(rid, {"content": [{"type": "text",
                                        "text": json.dumps(out, ensure_ascii=False)}]})
    # unknown notifications get no reply; unknown requests get method-not-found
    if rid is None:
        return None
    return reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
