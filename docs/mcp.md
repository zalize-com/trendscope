# trendscope MCP server

Query the open dataset directly from any MCP-compatible agent
(Claude Code, Cursor, OpenClaw, …). No API key, no scraping — the tools
read the public JSON artifacts straight from this repo's `main` branch.

## Install

```bash
git clone https://github.com/zalize-com/trendscope
```

then add the repo-root `.mcp.json` to your client's MCP config, or register it:

```bash
claude mcp add trendscope -- python3 /path/to/trendscope/scripts/mcp_server.py
```

Stdlib-only Python 3 — there is nothing else to install.

## Tools

| Tool | What it returns |
|---|---|
| `trendscope_latest` | Today's snapshot: date, total items, live-source count, top-ranked items |
| `trendscope_items` | All items captured for one source key (`hackernews`, `github_trending`, `sec_krebs`, …) |
| `trendscope_search` | Substring search over today's item titles/URLs |
| `trendscope_feeds` | The 9,200+-feed directory with health flags; optional lane filter |
| `trendscope_health` | Telemetry: persistent-empty (suspected dead) sources + rate-limit tide |
| `trendscope_topics` | Topic clusters computed over today's snapshot |
| `trendscope_day` | Historical snapshot replay — pass `date` (YYYY-MM-DD) to time-travel |

## What the agent sees

- Data refreshes with every daily GitHub Actions snapshot; `generated_at`
  tells you how fresh it is.
- Every item carries `source`, `rank`, `title`, `url`, `score`,
  `comments`, `author` — enough for provenance-aware answers.
- Bulk consumers don't need these tools; download
  `data/latest.json` / `data/history.csv` directly. The MCP surface is
  for interactive agents, not ETL.

## Example prompts

- "What are the top 10 developer stories today?" → `trendscope_latest`
- "What did Krebs publish this snapshot?" → `trendscope_items` `sec_krebs`
- "Any items about MCP today?" → `trendscope_search` `mcp`
- "Which feeds look dead?" → `trendscope_health`
