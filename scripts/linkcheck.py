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

def js_string_scan(src):
    """Stack-based JS scanner — catches unclosed ', ", ` literals, /* comments
    and /regex/ literals that would kill the whole script block (blank page).
    Handles ${...} interpolation inside template literals by pushing a brace
    depth tracker; nested template literals push another ` state."""
    stack = []          # states: "tmpl" (in `...`) or {"brace":depth} for ${}
    state, esc, i, n = None, False, 0, len(src)
    prev = ""           # last non-space char seen in normal/code state
    REGEX_OK = set("([{=,:;!&|?+-*~^%<>\n")
    while i < n:
        c = src[i]
        top = stack[-1] if stack else None
        if state == "line":
            if c == "\n":
                state = None
        elif state == "block":
            if c == "*" and i + 1 < n and src[i + 1] == "/":
                state = None
                i += 1
        elif state == "regex":
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "[":
                state = "regexclass"
            elif c == "/":
                state = None
        elif state == "regexclass":
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "]":
                state = "regex"
        elif state in ("'", '"'):
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == state:
                state = None
        elif state == "`":
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "`":
                state = None
                stack.pop()          # close this template literal
            elif c == "$" and i + 1 < n and src[i + 1] == "{":
                stack.append(0)      # brace depth tracker for ${ }
                state = None         # parse ${...} as normal code
                i += 1
        else:
            if isinstance(top, int) and top is not None:
                # inside ${...} of a template literal: normal code, but track braces
                if c == "{":
                    stack[-1] += 1
                elif c == "}":
                    if stack[-1] == 0:
                        stack.pop()
                        state = "`"    # resume template literal
                        i += 1
                        continue
                    stack[-1] -= 1
            if c == "/" and i + 1 < n and src[i + 1] == "/":
                state = "line"
                i += 1
            elif c == "/" and i + 1 < n and src[i + 1] == "*":
                state = "block"
                i += 1
            elif c == "/" and (not prev or prev in REGEX_OK):
                state = "regex"
            elif c in ("'", '"', "`"):
                if c == "`":
                    stack.append("tmpl")
                state = c
            if not c.isspace():
                prev = c
        i += 1
    return state if state else ("tmpl" if stack else None)


for page in sorted(pages):
    rel = os.path.relpath(page, ROOT)
    text = open(page, encoding="utf-8").read()
    for idx, m in enumerate(re.finditer(r"<script(?![^>]*src)[^>]*>(.*?)</script>", text, re.S)):
        if 'type="application/ld+json"' in m.group(0)[:200]:
            continue
        end_state = js_string_scan(m.group(1))
        check(end_state is None,
              f"{rel}: inline script #{idx} ends inside {end_state} literal (syntax break → blank page)")

# every sitemap entry must resolve to a real page; ?t= entries must name a
# tool tab that actually exists on that page
for loc in re.findall(r"<loc>https://zalize-com\.github\.io/trendscope/([^<]+)</loc>", sitemap):
    base = loc.split("?")[0].split("#")[0]
    target = os.path.join(ROOT, base)
    check(os.path.exists(target), f"sitemap.xml: dead entry → {loc}")
    if not os.path.exists(target):
        continue
    m = re.search(r"[?&]t=([A-Za-z0-9_-]+)", loc)
    if m and base.startswith("tools/"):
        src = open(target, encoding="utf-8").read()
        check(f'data-tool="{m.group(1)}"' in src, f"sitemap.xml: unknown tool tab → {loc}")

if fails:
    print(f"\nLINKCHECK FAILED — {len(fails)} problem(s)", file=sys.stderr)
    sys.exit(1)
print(f"OK — {len(pages)} pages, all internal links resolve, sitemap complete")
