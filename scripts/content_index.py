#!/usr/bin/env python3
"""TrendScope content index — lists generated digests and movers for the site.

Writes docs/index.json so digest.html can enumerate markdown files without
directory listing. Run after digest.py/movers.py in the daily workflow.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

DIGEST_RE = re.compile(r"^\d{4}-W\d{2}(-notes)?\.md$")
MOVERS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def main():
    digests = sorted(
        (f for f in os.listdir(os.path.join(DOCS, "digest")) if DIGEST_RE.match(f)),
        reverse=True,
    ) if os.path.isdir(os.path.join(DOCS, "digest")) else []
    movers = sorted(
        (f[:-3] for f in os.listdir(os.path.join(DOCS, "movers")) if MOVERS_RE.match(f)),
        reverse=True,
    ) if os.path.isdir(os.path.join(DOCS, "movers")) else []

    analysis = sorted(
        (f for f in os.listdir(DOCS) if f.endswith("-analysis.md")),
        reverse=True,
    )

    out = {"digests": digests, "movers": movers, "analysis": analysis}
    with open(os.path.join(DOCS, "index.json"), "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"docs/index.json: {len(digests)} digests, {len(movers)} movers")


if __name__ == "__main__":
    main()
