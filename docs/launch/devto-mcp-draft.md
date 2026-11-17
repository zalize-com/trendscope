# Draft #8 — dev.to: "We gave our open dataset an MCP server"

**slug suggestion:** trendscope-mcp-server
**tags:** mcp, ai, opensource, datasets
**canonical:** https://trendscope.zalize.com/docs/mcp.md → use GitHub docs/mcp.md URL
**position:** run AFTER the dataset intro post (#1); this is the agent-angle follow-up.

---

## Title options

1. We gave our open dataset an MCP server — 170 lines, zero dependencies
2. Your agent can now query 100k+ daily developer signals (no API key)
3. MCP in 170 lines of stdlib Python: exposing an open dataset to agents

## Body

Every morning our pipeline snapshots what ~9,200 developer sources are
publishing — Hacker News, GitHub trending, security blogs, newsletters,
YouTube channels, subreddits — and commits it to a public repo as CC0 data.

Dashboards are nice for humans. But the interesting consumers of a daily
dataset are *agents*: your Claude Code session, your research assistant,
your "what did I miss this week" bot. Agents shouldn't scrape HTML — they
should call tools.

So we wrote the smallest honest MCP server we could:
[`scripts/mcp_server.py`](https://github.com/zalize-com/trendscope/blob/main/scripts/mcp_server.py)
— ~170 lines, Python stdlib only, no `pip install` anything.

### What it exposes

Six read-only tools over the live dataset:

```
trendscope_latest   today's snapshot: date, totals, top-ranked items
trendscope_items    all items from one source key
trendscope_search   substring search over 100k+ titles/urls
trendscope_feeds    the 9,200-feed directory with health flags
trendscope_health   suspected-dead sources + rate-limit tide
trendscope_topics   topic clusters over today
trendscope_day      time travel — replay any past date
```

### Install (30 seconds)

```bash
git clone https://github.com/zalize-com/trendscope
claude mcp add trendscope -- \
  python3 trendscope/scripts/mcp_server.py
```

`.mcp.json` is in the repo root, so MCP-aware clients pick it up
automatically when the repo is on disk.

### What we learned writing it

- **The stdio transport is just newline-delimited JSON-RPC.** No SDK
  needed for a read-only server: `initialize`, `tools/list`,
  `tools/call`, ignore the rest.
- **Design for the agent's context window.** `latest` returns the top 20
  items, not 100k. `day` returns a summary + top items, never the raw
  40MB file. Every tool has a `limit`.
- **Data files are gzip on disk** — the fetch helper transparently
  retries `*.json` → `*.json.gz` + decompress, so tool code stays boring.
- **`TRENDSCOPE_BASE` makes it mirror-friendly.** Fork the dataset, point
  the env var at your mirror, and your agent queries *your* pipeline.

### Why bother when the JSON is public anyway?

Because agents think in tools, not in `curl`. "What are the top stories
today?" becomes one typed call with structured output instead of a
6.5MB blob the model has to grep through. And because an MCP server is
also documentation that executes itself — the tool list *is* the API
contract.

The dataset updates daily via GitHub Actions. The server has no state,
no key, and nothing to rate-limit — it's just a friendly front door to
files that were already free.

Repo: https://github.com/zalize-com/trendscope ·
Site: https://trendscope.zalize.com ·
MCP docs: `docs/mcp.md`

---

## First comment (seed)

> Happy to answer questions about the MCP protocol bits — the stdio
> framing turned out way simpler than the docs suggest. Also: if there's
> a tool you'd want added (e.g. `trendscope_movers` for week-over-week
> risers), tell me and I'll wire it.
