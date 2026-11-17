#!/usr/bin/env python3
"""Consistency check — registry ↔ generated docs/assets.

Four-way reconciliation so generated surfaces can never silently drift from
the source registry (WorldMonitor-style contract check, stdlib only):

  1. Registry keys (collect.py literal fetchers + feeds_*.json overrides,
     last-wins) == data/feeds.json keys == docs/SOURCES.md keys.
  2. OPML outlines (xmlUrl set) == registry feed URLs, and the per-lane
     data/opml/*.opml subsets sum to the same set.
  3. sitemap.xml page locs ⊆ llms.txt link targets (every public page is
     indexed for LLM crawlers).

Exit 1 on any violation. Run: python3 scripts/consistency.py
"""
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://trendscope.zalize.com"
fails = []


def report(name, problems):
    if problems:
        fails.append(name)
        print(f"FAIL {name}: {len(problems)} issue(s)")
        for p in problems[:12]:
            print(f"   - {p}")
        if len(problems) > 12:
            print(f"   ... +{len(problems) - 12} more")
    else:
        print(f"ok   {name}")


def registry():
    """All source keys from collect.py literal + feeds_*.json (SOURCES.md scope)."""
    src = (ROOT / "scripts" / "collect.py").read_text()
    keys = {k for k, _fn in re.findall(r'"(\w+)": (fetch_\w+),', src)}
    for p in sorted((ROOT / "scripts").glob("feeds_*.json")):
        keys |= set(json.load(open(p)))
    return keys


def feed_registry():
    """key -> feed url for the OPML/feeds.json scope (feed-type sources only).

    Mirrors gen_opml.py exactly: a literal fetcher qualifies when its body has
    a Request("url") or a feed/rss/atom/xml-ish URL; API sources (HN/npm/...)
    are excluded by design. feeds_*.json rows override same-key literals.
    """
    src = (ROOT / "scripts" / "collect.py").read_text()
    feeds = {}
    for m in re.finditer(r'def (fetch_\w+)\([^)]*\):\s*\n\s*"""(.*?)"""(.*?)(?=\ndef |\Z)', src, re.S):
        name, body = m.group(1), m.group(3)
        um = (re.search(r'Request\(\s*\n?\s*"(https?://[^"]+)"', body)
              or re.search(r'["\'](https?://[^"\']*(?:feed|rss|atom|xml)[^"\']*)["\']', body))
        if um:
            feeds[name] = um.group(1)
    reg = {k: feeds[fn] for k, fn in re.findall(r'"(\w+)": (fetch_\w+),', src) if fn in feeds}
    for p in sorted((ROOT / "scripts").glob("feeds_*.json")):
        for key, row in json.load(open(p)).items():
            reg[key] = row[1]
    return reg


def check_registry_parity(all_keys, feed_reg):
    problems = []
    src_md = (ROOT / "docs" / "SOURCES.md").read_text()
    md_keys = set(re.findall(r"^\| `(\w+)` \|", src_md, re.M))
    if md_keys != all_keys:
        problems.append(f"SOURCES.md {len(md_keys)} vs registry {len(all_keys)}; "
                        f"missing: {sorted(all_keys - md_keys)[:8]}; extra: {sorted(md_keys - all_keys)[:8]}")

    feeds_doc = json.load(open(ROOT / "data" / "feeds.json"))
    doc = {f["key"]: f["feed"] for f in feeds_doc["feeds"]}
    if set(doc) != set(feed_reg):
        problems.append(f"feeds.json {len(doc)} vs feed registry {len(feed_reg)}; "
                        f"missing: {sorted(set(feed_reg) - set(doc))[:8]}; extra: {sorted(set(doc) - set(feed_reg))[:8]}")
    mismatched = [k for k in set(feed_reg) & set(doc) if doc[k] != feed_reg[k]]
    if mismatched:
        problems.append(f"feed url mismatch registry vs feeds.json: {mismatched[:10]}")
    report("registry parity (SOURCES.md + feeds.json)", problems)


def opml_urls(path):
    return {o.get("xmlUrl") for o in ET.parse(path).iter("outline")
            if o.get("type") == "rss" and o.get("xmlUrl")}


def check_opml(reg):
    problems = []
    urls = opml_urls(ROOT / "trendscope.opml")
    reg_urls = {u for u in reg.values() if u}
    if urls != reg_urls:
        problems.append(f"xmlUrl set differs from registry ({len(urls)} vs {len(reg_urls)})")
    lane_total = set()
    for p in sorted((ROOT / "data" / "opml").glob("*.opml")):
        lane_total |= opml_urls(p)
    if lane_total != urls:
        problems.append(f"per-lane subsets sum {len(lane_total)} != full OPML {len(urls)}")
    report("OPML parity (full + per-lane subsets)", problems)


def check_llms_coverage():
    problems = []
    llms = (ROOT / "llms.txt").read_text()
    links = set(re.findall(r"\]\(([^)]+)\)", llms))
    links = {re.sub(r"\.html$", "", l).strip("/") or "/" for l in links}
    links = {"/" if l == "index" else l for l in links}
    sm = (ROOT / "sitemap.xml").read_text()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    missing = []
    for loc in locs:
        path = loc.replace(SITE, "").strip("/") or "/"
        if path not in links:
            missing.append(path)
    if missing:
        problems.append(f"sitemap pages missing from llms.txt: {missing[:15]}")
    report("llms.txt ↔ sitemap coverage", problems)


if __name__ == "__main__":
    all_keys = registry()
    feed_reg = feed_registry()
    print(f"registry: {len(all_keys)} sources, {len(feed_reg)} feeds")
    check_registry_parity(all_keys, feed_reg)
    check_opml(feed_reg)
    check_llms_coverage()
    if fails:
        sys.exit(f"{len(fails)} consistency check(s) failed: {fails}")
    print("all consistency checks passed")
