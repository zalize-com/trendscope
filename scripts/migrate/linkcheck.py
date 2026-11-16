#!/usr/bin/env python3
"""Internal link check for the Astro build output (site/dist).

Walks every .html in dist/, resolves relative href/src/action/poster
targets against the page URL, and reports references that don't exist
in dist. Directory URLs resolve to <dir>/index.html (build.format=file
also emits x.html for /x, so bare `foo` tries foo.html too).
Run from site/ (expects dist/). Exit 1 on any broken ref.
"""
import os, re, sys, glob, urllib.parse

DIST = 'dist'
broken = []
for f in glob.glob(os.path.join(DIST, '*.html')) + glob.glob(os.path.join(DIST, '**/*.html'), recursive=True):
    html = open(f, encoding='utf8', errors='replace').read()
    page_dir = os.path.dirname(f)
    for m in re.finditer(r'(?:href|src|action|poster)="([^"#]+)"', html):
        u = m.group(1)
        if u.startswith(('http', 'data:', 'mailto:', 'javascript:', '//')) or u.startswith('${'):
            continue
        path = urllib.parse.unquote(u.split('?')[0])
        t = path.lstrip('/') if path.startswith('/') else os.path.normpath(os.path.join(page_dir, path))
        t = os.path.join(DIST, t) if not t.startswith(DIST) else t
        if (os.path.exists(t) or os.path.exists(t + '.html')
                or os.path.exists(os.path.join(t, 'index.html')) or os.path.isdir(t)):
            continue
        broken.append((os.path.relpath(f, DIST), u))

if broken:
    print(f'{len(broken)} broken internal refs:')
    for f, u in broken[:50]:
        print(f'  {f} -> {u}')
    sys.exit(1)
print('linkcheck: all internal refs resolve')
