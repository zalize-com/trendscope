#!/usr/bin/env python3
"""SimHash near-duplicate scan over the latest snapshot — P0-3 preview.

Computes 64-bit SimHash fingerprints over normalized item titles, finds
clusters at hamming distance <= 3 (the ai-news-brief two-stage approach's
cheap first pass), and writes data/dedup.json so the pipeline + frontend
can consume cross-source duplicate groups later.

Stdlib only; not yet wired into collect.yml — this is the feasibility
probe + parameter tuning artifact.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "dedup.json")
BITS = 64
MAX_DIST = 3

STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for",
        "is", "are", "was", "were", "be", "by", "with", "at", "as",
        "it", "its", "that", "this", "from", "how", "why", "what"}


def tokens(title):
    return [t for t in re.findall(r"[a-z0-9]+", (title or "").lower())
            if t not in STOP and len(t) > 2]


def fnv1a(s):
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def simhash(toks):
    vec = [0] * BITS
    for t in toks:
        h = fnv1a(t)
        for i in range(BITS):
            vec[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i, v in enumerate(vec) if v > 0)


def hamming(a, b):
    return bin(a ^ b).count("1")


def band_keys(h):
    # 4 bands of 16 bits — candidate pairs must share a band
    for band in range(4):
        yield band, (h >> (band * 16)) & 0xFFFF


def main():
    lite = json.load(open(os.path.join(ROOT, "data", "latest-lite.json")))
    items = [i for v in (lite.get("items") or {}).values() for i in v]
    sig = []
    for idx, it in enumerate(items):
        toks = tokens(it.get("title"))
        if len(toks) >= 4:
            sig.append((idx, simhash(toks)))

    # band index: (band, bandbits) -> [row...]
    bands = {}
    for row, (idx, h) in enumerate(sig):
        for bk in band_keys(h):
            bands.setdefault(bk, []).append(row)

    parent = list(range(len(sig)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    pairs = 0
    for rows in bands.values():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if find(a) == find(b):
                    continue
                if hamming(sig[a][1], sig[b][1]) <= MAX_DIST:
                    union(a, b)
                    pairs += 1

    clusters = {}
    for row in range(len(sig)):
        clusters.setdefault(find(row), []).append(row)
    groups = []
    for rows in clusters.values():
        if len(rows) < 2:
            continue
        members = []
        for r in rows:
            it = items[sig[r][0]]
            members.append({"source": it.get("source"), "title": it.get("title"),
                            "url": it.get("url"), "score": it.get("score")})
        if len({m["source"] for m in members}) < 2:
            continue  # same-source dup is not interesting
        members.sort(key=lambda m: -(m.get("score") or 0))
        groups.append({"size": len(members),
                       "sources": sorted({m["source"] for m in members}),
                       "canonical": members[0], "members": members})
    groups.sort(key=lambda g: -g["size"])

    out = {"date": lite.get("date"), "items_scanned": len(items),
           "fingerprinted": len(sig), "near_dup_pairs": pairs,
           "cross_source_clusters": len(groups), "clusters": groups[:200]}
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"scanned {len(items)} items, {len(sig)} fingerprinted, "
          f"{pairs} near-dup pairs, {len(groups)} cross-source clusters")
    for g in groups[:8]:
        print(f"  [{g['size']}] {' / '.join(g['sources'][:4])} :: "
              f"{g['canonical']['title'][:70]}")


if __name__ == "__main__":
    sys.exit(main())
