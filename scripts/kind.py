#!/usr/bin/env python3
"""Rule-based `kind` classification for snapshot items — P0-1 first pass.

Freebie Radar lesson applied: classify cheaply with rules first; the LLM
pass (ai_score.py) can later refine only the ambiguous tail. Emits
data/kind.json: {"date", "kinds": {url: kind}, "counts": {kind: n}} so any
frontend page can join on item url without touching the pipeline schema.

Kinds: paper | release | tool | show | ask | job | video | podcast |
newsletter | post (default).
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "kind.json")

RE_RELEASE = re.compile(
    r"\b(release[sd]?|changelog|v\d+\.\d+(\.\d+)*\b.*(out|now)|"
    r"\d+\.\d+\.\d+ is|announcing .*\d+\.\d+)", re.I)
RE_SHOW = re.compile(r"^show hn\b|^show:(?!\s*hn)", re.I)
RE_ASK = re.compile(r"^(ask|tell) hn\b", re.I)
RE_JOB = re.compile(r"who (is |wants to be )?hiring|hiring thread|"
                    r"who wants to be hired|freelancer\?", re.I)


def classify(it):
    key = it.get("source") or ""
    title = it.get("title") or ""
    url = (it.get("url") or "").lower()
    if key == "arxiv" or "arxiv.org/abs" in url or "arxiv.org/pdf" in url:
        return "paper"
    if key.startswith("yt_") or key == "youtube":
        return "video"
    if key.startswith("pb_"):
        return "podcast"
    if key.startswith("nl_"):
        return "newsletter"
    if RE_JOB.search(title):
        return "job"
    if key == "ask_hn" or RE_ASK.search(title):
        return "ask"
    if key == "show_hn" or RE_SHOW.search(title):
        return "show"
    if RE_RELEASE.search(title) or "/releases/tag/" in url:
        return "release"
    if key == "github_trending" or re.match(
            r"https?://github\.com/[^/]+/[^/]+/?$", url):
        return "tool"
    return "post"


def main():
    lite = json.load(open(os.path.join(ROOT, "data", "latest-lite.json")))
    kinds = {}
    counts = {}
    for items in (lite.get("items") or {}).values():
        for it in items:
            k = classify(it)
            u = it.get("url")
            if u:
                kinds[u] = k
                counts[k] = counts.get(k, 0) + 1
    with open(OUT, "w") as f:
        json.dump({"date": lite.get("date"), "counts": counts,
                   "kinds": kinds}, f, ensure_ascii=False)
    print(f"kind.json: {len(kinds)} items -> {counts}")
    # Lite variant for lazy UI join: everything except the "post" default
    # (~3% of items, ~60KB vs ~2MB full file).
    notable = {u: k for u, k in kinds.items() if k != "post"}
    with open(os.path.join(ROOT, "data", "kind-lite.json"), "w") as f:
        json.dump({"date": lite.get("date"), "kinds": notable}, f,
                  ensure_ascii=False)
    print(f"kind-lite.json: {len(notable)} non-post items")


if __name__ == "__main__":
    sys.exit(main())
