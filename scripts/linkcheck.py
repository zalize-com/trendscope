#!/usr/bin/env python3
"""Internal link integrity check — every local href/src in every HTML page
must resolve to a file that exists, and every root HTML page must be in the
sitemap. Fails the build on dead links or orphaned pages."""
import html.parser
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_SCHEMES = ("http://", "https://", "mailto:", "data:", "tel:", "javascript:")
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print(f"  ✗ {msg}")


class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, val in attrs:
            if name in ("href", "src") and val:
                self.refs.append(val)


pages = []
for dirpath, _dirs, files in os.walk(ROOT):
    if ".git" in dirpath or "node_modules" in dirpath:
        continue
    for f in files:
        if f.endswith(".html"):
            pages.append(os.path.join(dirpath, f))

for page in sorted(pages):
    rel = os.path.relpath(page, ROOT)
    p = LinkParser()
    p.feed(open(page, encoding="utf-8").read())
    for ref in p.refs:
        if ref.startswith(SKIP_SCHEMES) or ref.startswith("#"):
            continue
        path = ref.split("#")[0].split("?")[0]
        if not path:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(page), path))
        check(os.path.exists(target), f"{rel}: dead link → {ref}")

# every root-level html page must appear in the sitemap
sitemap = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
for page in sorted(pages):
    rel = os.path.relpath(page, ROOT)
    if os.sep in rel:
        continue
    check(f"trendscope/{rel}" in sitemap, f"{rel}: missing from sitemap.xml")

# every sitemap entry must resolve to a real page
for loc in re.findall(r"<loc>https://zalize-com\.github\.io/trendscope/([^<]+)</loc>", sitemap):
    check(os.path.exists(os.path.join(ROOT, loc)), f"sitemap.xml: dead entry → {loc}")

if fails:
    print(f"\nLINKCHECK FAILED — {len(fails)} problem(s)", file=sys.stderr)
    sys.exit(1)
print(f"OK — {len(pages)} pages, all internal links resolve, sitemap complete")
