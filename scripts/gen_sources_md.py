#!/usr/bin/env python3
"""Regenerate docs/SOURCES.md — the canonical full registry table.

Parses every fetch_* def in collect.py for its docstring blurb and first
feed/API URL, then emits a markdown table in registry order. Run after any
source wave:  python3 scripts/gen_sources_md.py
"""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "collect.py"
OUT = ROOT / "docs" / "SOURCES.md"

src = SRC.read_text()

# function name -> (blurb, url) for every fetch_* def, any signature
info = {}
for m in re.finditer(r'def (fetch_\w+)\([^)]*\):\s*\n\s*"""(.*?)"""(.*?)(?=\ndef |\Z)', src, re.S):
    name, doc, body = m.groups()
    blurb = doc.strip().split("\n")[0].rstrip(".")
    blurb = re.sub(r"\s+—.*$", "", blurb)
    um = re.search(r'["\'](https?://[^"\']+)["\']', body)
    url = um.group(1) if um else ""
    host = re.sub(r"^https?://", "", url)
    host = re.sub(r"[/?].*$", "", host)
    info[name] = (blurb, host)

# fallback for docstring-less fetchers: use print("Fetching X ...") + first URL
for m in re.finditer(r'def (fetch_\w+)\([^)]*\):(.*?)(?=\ndef |\Z)', src, re.S):
    name, body = m.groups()
    if name in info:
        continue
    pm = re.search(r'print\(["\']Fetching ([^"\'.]+)', body)
    um = re.search(r'["\'](https?://[^"\']+)["\']', body)
    blurb = pm.group(1).strip() if pm else name[6:]
    url = um.group(1) if um else ""
    host = re.sub(r"^https?://", "", url)
    host = re.sub(r"[/?].*$", "", host)
    info[name] = (blurb, host)

# registry order: "key": fetch_name,
rows = []
missing = []
for k, fn in re.findall(r'"(\w+)": (fetch_\w+),', src):
    if fn in info:
        b, h = info[fn]
        rows.append((k, b, h))
    else:
        missing.append(k)

# data-driven feeds from scripts/feeds_*.json ({key: [label, feed, home]})
for path in sorted((ROOT / "scripts").glob("feeds_*.json")):
    import json
    for key, (label, feed, home) in json.load(open(path)).items():
        host = re.sub(r"^https?://", "", feed)
        host = re.sub(r"[/?].*$", "", host)
        if key in {r[0] for r in rows}:
            continue
        rows.append((key, label, host))

out = [
    "# Source registry",
    "",
    f"{len(rows)} fetchers, generated from `scripts/collect.py` by `scripts/gen_sources_md.py`.",
    "",
    "| Key | Description | Host |",
    "|---|---|---|",
]
for k, b, h in rows:
    out.append(f"| `{k}` | {b} | `{h}` |")
out.append("")
OUT.write_text("\n".join(out))
print(f"{OUT}: {len(rows)} rows; unmatched: {missing}")
