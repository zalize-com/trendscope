#!/usr/bin/env python3
"""zerowatch — report sources empty in the LAST TWO consecutive snapshots.

Single-round zero = rate-limit tide (YouTube wave / Reddit per-IP cap /
substack ASN block rotating through the egress), NOT a dead source — see
methodology 35-37. Only sources empty in two consecutive daily snapshots
are worth human attention.

Usage: python3 scripts/zerowatch.py [--rounds N]
Prints: still-empty sources grouped by lane prefix, and the tide count
(empty this round but with data in a previous one).
"""
import gzip
import json
import os
import sys
from collections import Counter

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _snap(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)["items"]


def main():
    rounds = 3
    if "--rounds" in sys.argv:
        rounds = int(sys.argv[sys.argv.index("--rounds") + 1])
    daily = sorted(f for f in os.listdir(os.path.join(DATA, "daily")) if f.endswith(".json.gz"))
    if len(daily) < rounds:
        # fall back to latest.json for the newest round
        snaps = [_snap(os.path.join(DATA, "daily", f)) for f in daily[-(rounds - 1):]]
        with open(os.path.join(DATA, "latest.json")) as f:
            snaps.append(json.load(f)["items"])
        names = daily[-(rounds - 1):] + ["latest.json"]
    else:
        snaps = [_snap(os.path.join(DATA, "daily", f)) for f in daily[-rounds:]]
        names = daily[-rounds:]
    print(f"window: {' / '.join(names)}")
    keys = set().union(*snaps)
    persistent = sorted(k for k in keys if all(not s.get(k) for s in snaps))
    tide = sorted(k for k in keys if not snaps[-1].get(k) and any(s.get(k) for s in snaps[:-1]))
    print(f"persistent empty ({rounds} rounds): {len(persistent)}")
    print("  by lane:", dict(Counter(k.split("_")[0] for k in persistent).most_common(10)))
    print(f"tide (empty now, had data before): {len(tide)}")
    for k in persistent[:40]:
        print("  -", k)
    return 1 if persistent else 0


if __name__ == "__main__":
    sys.exit(main())
