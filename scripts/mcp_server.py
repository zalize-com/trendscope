#!/usr/bin/env python3
"""trendscope MCP server (stdio, zero-deps).

Exposes the dataset to any MCP-capable agent as tools over plain JSON-RPC.
Self-hostable: point BASE at any mirror of the repo's data/ + docs/api/.

    {"jsonrpc":"2.0","id":1,"method":"tools/list"}
    {"jsonrpc":"2.0","id":2,"method":"tools/call",
     "params":{"name":"ts_latest","arguments":{"n":5}}}

Claude Desktop / any MCP client config:

    {"mcpServers":{"trendscope":{
      "command":"python3",
      "args":["/path/to/trendscope/scripts/mcp_server.py"]}}}
"""
import json
import os
import sys
import urllib.request
import urllib.parse

BASE = os.environ.get("TRENDSCOPE_BASE",
                      "https://zalize-com.github.io/trendscope")
UA = "trendscope-mcp/0.1"


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def flat_items(d):
    items = d.get("items", {})
    if isinstance(items, dict):
        return [it for v in items.values() for it in v]
    return items or []


def clip(items, n):
    return [{"title": i.get("title"), "url": i.get("url"),
             "source": i.get("source"), "score": i.get("score"),
             "metric": i.get("metric")} for i in items[:n]]


def ts_latest(n=10, source=None):
    its = flat_items(fetch("/data/latest.json"))
    if source:
        its = [i for i in its if i.get("source") == source]
    its.sort(key=lambda x: x.get("score") or 0, reverse=True)
    return clip(its, n)


def ts_new(n=10):
    return clip(fetch("/docs/api/new.json").get("items", []), n)


def ts_risers(n=10):
    d = fetch("/docs/api/risers.json")
    spikes = [s.get("item", s) for s in d.get("single_day_spikes", [])]
    return clip(spikes, n)


def ts_search(q, n=10):
    q = q.lower()
    its = flat_items(fetch("/data/latest.json"))
    hits = [i for i in its if q in (i.get("title") or "").lower()]
    hits.sort(key=lambda x: x.get("score") or 0, reverse=True)
    return clip(hits, n)


def ts_streaks(n=10):
    d = fetch("/docs/api/streaks.json")
    return clip([s.get("item", s) for s in d.get("active", [])], n)


def ts_topics():
    d = fetch("/docs/api/topics.json")
    days = d.get("days", [])
    last = days[-1] if days else None
    return {t: v["counts"].get(last, 0)
            for t, v in d.get("topics", {}).items()} if last else {}


def ts_sources():
    return fetch("/docs/api/sources.json")


TOOLS = [
    {"name": "ts_latest",
     "description": "Today's top items across 20 tracked sources (points/stars/etc.).",
     "inputSchema": {"type": "object", "properties": {
         "n": {"type": "integer", "default": 10},
         "source": {"type": "string", "description": "optional filter e.g. hackernews, github_trending"}}}},
    {"name": "ts_new",
     "description": "Items that first appeared on the board today.",
     "inputSchema": {"type": "object", "properties": {"n": {"type": "integer", "default": 10}}}},
    {"name": "ts_risers",
     "description": "Single-day spikes — items that jumped onto the board today.",
     "inputSchema": {"type": "object", "properties": {"n": {"type": "integer", "default": 10}}}},
    {"name": "ts_search",
     "description": "Search today's board by title substring.",
     "inputSchema": {"type": "object", "properties": {
         "q": {"type": "string"}, "n": {"type": "integer", "default": 10}},
         "required": ["q"]}},
    {"name": "ts_streaks",
     "description": "Items on the board 3+ consecutive days.",
     "inputSchema": {"type": "object", "properties": {"n": {"type": "integer", "default": 10}}}},
    {"name": "ts_topics",
     "description": "Topic counts for the latest day (AI/LLM, Web Dev, ...).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ts_sources",
     "description": "Per-source stats across all tracked days.",
     "inputSchema": {"type": "object", "properties": {}}},
]

HANDLERS = {
    "ts_latest": lambda a: ts_latest(a.get("n", 10), a.get("source")),
    "ts_new": lambda a: ts_new(a.get("n", 10)),
    "ts_risers": lambda a: ts_risers(a.get("n", 10)),
    "ts_search": lambda a: ts_search(a["q"], a.get("n", 10)),
    "ts_streaks": lambda a: ts_streaks(a.get("n", 10)),
    "ts_topics": lambda a: ts_topics(),
    "ts_sources": lambda a: ts_sources(),
}


def reply(rid, result):
    sys.stdout.write(json.dumps(
        {"jsonrpc": "2.0", "id": rid, "result": result},
        ensure_ascii=False) + "\n")
    sys.stdout.flush()


def err(rid, msg):
    sys.stdout.write(json.dumps(
        {"jsonrpc": "2.0", "id": rid,
         "error": {"code": -32603, "message": msg}},
        ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = req.get("id")
        method = req.get("method", "")
        if method == "initialize":
            reply(rid, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "trendscope", "version": "0.1.0"}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            reply(rid, {"tools": TOOLS})
        elif method == "tools/call":
            p = req.get("params", {})
            name, args = p.get("name"), p.get("arguments", {})
            if name not in HANDLERS:
                err(rid, f"unknown tool {name}")
                continue
            try:
                out = HANDLERS[name](args)
                reply(rid, {"content": [{
                    "type": "text",
                    "text": json.dumps(out, ensure_ascii=False)}]})
            except Exception as e:
                err(rid, f"{name} failed: {e}")
        elif rid is not None:
            reply(rid, {})


if __name__ == "__main__":
    main()
