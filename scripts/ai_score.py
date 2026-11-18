#!/usr/bin/env python3
"""AI quality layer for trendscope — P2 scaffold, stdlib only.

Scores top items of the latest snapshot with an OpenAI-compatible
chat-completion endpoint and writes data/ai_quality.json.

Design (from docs/competitive-learning-plan.md, Freebie Radar pattern):
cost-escalating filter — cheap rules first (this script only sends the
top-K per lane), then ONE batched LLM call returns kind/quality/dedup
hints per item. No LLM key → clean no-op so CI never hard-depends on it.

Env:
  TRENDSCOPE_LLM_KEY   OpenAI-compatible API key (required; else no-op)
  TRENDSCOPE_LLM_BASE  default https://api.openai.com/v1
  TRENDSCOPE_LLM_MODEL default gpt-4o-mini (any chat model)
"""
import json
import os
import sys
import urllib.request

KEY = os.environ.get("TRENDSCOPE_LLM_KEY")
# Auto-detect provider from the key shape so "paste any key" just works:
# Gemini keys start with AIza → Google's OpenAI-compatible endpoint.
if KEY and KEY.startswith("AIza"):
    _def_base, _def_model = ("https://generativelanguage.googleapis.com/v1beta/openai",
                             "gemini-2.0-flash")
else:
    _def_base, _def_model = ("https://api.openai.com/v1", "gpt-4o-mini")
BASE = os.environ.get("TRENDSCOPE_LLM_BASE", _def_base).rstrip("/")
MODEL = os.environ.get("TRENDSCOPE_LLM_MODEL", _def_model)
PER_LANE = 25          # top-N items per lane sent to the model
OUT = "data/ai_quality.json"

# Horizon-style profiles: what "worth reading" means differs per lane.
# A news story wants "why it matters"; an engineering post wants
# "what I can use". One rubric line per lane, picked by `lane(source)`.
RUBRICS = {
    "security": "novel vulnerabilities, exploitable techniques, major breaches, actionable defense",
    "eng-blog": "reusable engineering practice, real production lessons, architecture decisions",
    "tech-blog": "clear technical explanations, usable tools/libraries, non-trivial how-tos",
    "blogroll": "distinctive personal insight or experience, not generic listicles",
    "newsletter": "the issue's standout link, not newsletter meta-content",
    "pod-blog": "high-signal talks/interviews worth the watch time",
    "youtube": "high-signal tutorials/talks/demos worth the watch time",
    "tldr": "stories a busy senior dev must not miss today",
    "misc": "broad developer relevance, novel or consequential",
}
DEFAULT_RUBRIC = RUBRICS["misc"]

PROMPT = """You classify developer-attention items. For each item return:
kind (paper|release|tool|news|discussion|question|show|job|other),
quality 1-5 (5 = must-read for a developer today, judged by the per-source rubric given in `rubric`),
dup_key (short slug; identical stories across sources share it),
note (one line, <=12 words: why it matters OR what a dev can use — whichever fits the rubric).
Reply ONLY with a JSON array aligned to the input order:
[{"i":0,"kind":"...","quality":3,"dup_key":"...","note":"..."}, ...]
Items (JSON array of {i, source, rubric, title, url, score}):
"""

LANE_OF = {
    "sec": "security", "eb": "eng-blog", "tb": "tech-blog", "br": "blogroll",
    "nl": "newsletter", "pb": "pod-blog", "yt": "youtube", "tldr": "tldr",
    "aws": "aws", "github": "github", "gitlab": "gitlab", "meta": "meta",
    "slack": "slack", "misc": "misc",
}


def lane(key):
    p = key.split("_", 1)[0]
    return LANE_OF.get(p, p)


def chat(messages):
    body = json.dumps({
        "model": MODEL, "messages": messages, "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read())
    return out["choices"][0]["message"]["content"]


def main():
    if not KEY:
        print("TRENDSCOPE_LLM_KEY unset — ai_quality skipped (no-op).")
        return 0
    d = json.load(open("data/latest-lite.json"))
    items = [i for v in (d.get("items") or {}).values() for i in v]
    # cheap layer: top-N per lane by score — model only sees signal-dense head
    lanes = {}
    for it in items:
        lanes.setdefault(lane(it.get("source", "")), []).append(it)
    batch = []
    for ln, rows in lanes.items():
        rows.sort(key=lambda x: -(x.get("score") or 0))
        for it in rows[:PER_LANE]:
            batch.append({"i": len(batch), "source": it.get("source"),
                          "rubric": RUBRICS.get(ln, DEFAULT_RUBRIC),
                          "title": it.get("title"), "url": it.get("url"),
                          "score": it.get("score")})
    print(f"scoring {len(batch)} items across {len(lanes)} lanes …")
    raw = chat([
        {"role": "system", "content": "You are a precise classifier. JSON only."},
        {"role": "user", "content": PROMPT + json.dumps(batch, ensure_ascii=False)},
    ])
    try:
        scored = json.loads(raw)
        if isinstance(scored, dict):  # tolerate {"items":[...]} wrapping
            scored = scored.get("items") or scored.get("results") or []
    except json.JSONDecodeError:
        print("model returned non-JSON; aborting without writes.")
        return 1
    by_i = {s.get("i"): s for s in scored if isinstance(s, dict)}
    out = {"generated_at": d.get("generated_at"), "model": MODEL,
           "scored": len(by_i), "items": []}
    for b in batch:
        s = by_i.get(b["i"]) or {}
        out["items"].append({**b, "kind": s.get("kind"),
                             "quality": s.get("quality"),
                             "dup_key": s.get("dup_key"),
                             "note": s.get("note")})
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"wrote {OUT} ({len(out['items'])} items, model={MODEL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
