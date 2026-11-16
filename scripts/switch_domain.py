#!/usr/bin/env python3
"""switch_domain.py — rewrite the canonical site domain across the repo.

Usage:
    python3 scripts/switch_domain.py <new-origin> [--apply]

<new-origin> is an origin without trailing slash, e.g.
    https://zalize-com.github.io/trendscope
    https://trendscope.example.com

Without --apply it only prints the files that would change.

Rewrites every literal occurrence of the CURRENT canonical origin
(`https://trendscope--plov6nur.preview.devinapps.com`) in tracked text files:
HTML (canonical/og:url/og:image), sitemap.xml, robots.txt, llms.txt,
feed generators' SITE_URL constants, scripts/collect.py SITE_URL,
docs and README links.

It does NOT touch docs that intentionally describe the migration itself.
After switching, run scripts/gen_opml.py and linkcheck.py, then commit.
"""
import os
import re
import sys

OLD = "https://trendscope--plov6nur.preview.devinapps.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".html", ".xml", ".txt", ".md", ".yaml", ".yml", ".py",
            ".js", ".json", ".csv", ".opml", ".cff"}
SKIP = {os.path.join("docs", "launch", "pages-verification-drill.md")}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    if len(args) != 1:
        print(__doc__.strip())
        return 2
    new = args[0].rstrip("/")
    if not new.startswith("https://"):
        print("error: new origin must start with https://")
        return 2

    changed = []
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__",
                                              "node_modules"}]
        for fn in files:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT)
            if rel in SKIP or os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            try:
                s = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if OLD not in s:
                continue
            n = s.count(OLD)
            if apply:
                open(p, "w", encoding="utf-8",
                     newline="").write(s.replace(OLD, new))
            changed.append((rel, n))

    for rel, n in sorted(changed):
        print(f"{'rewrote' if apply else 'would rewrite'} {rel} ({n}x)")
    print(f"{len(changed)} files, {sum(n for _, n in changed)} occurrences")
    if not apply:
        print("dry run — pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
