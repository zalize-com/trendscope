#!/usr/bin/env python3
"""Emit trendscope.opml — every feed source as an OPML outline, importable
into any RSS reader (Feedly, NetNewsWire, Miniflux, ...)."""
import re

src = open('scripts/collect.py').read()
defs = re.findall(
    r'def fetch_([a-z0-9_]+)\(limit=\d+\):\s*\n\s*"""([^"\n]+)"""\s*\n'
    r'.*?Request\(\s*\n?\s*"([^"]+)"', src, re.S)

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<opml version="2.0">', '<head>',
       f'<title>trendscope sources ({len(defs)})</title>',
       '</head>', '<body>',
       '<outline text="trendscope" title="trendscope sources">']
for key, doc, url in sorted(defs, key=lambda t: t[0]):
    label = doc.split(' — ')[0].strip().replace('"', '&quot;')
    out.append(f'<outline type="rss" text="{label}" title="{label}" xmlUrl="{url}"/>')
out += ['</outline>', '</body>', '</opml>']
open('trendscope.opml', 'w').write('\n'.join(out) + '\n')
print(f'wrote trendscope.opml with {len(defs)} outlines')
