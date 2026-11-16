#!/usr/bin/env python3
"""to_astro.py <page.html> — mechanical HTML->Astro transcription helper.

Splits a legacy page into: frontmatter props (title/description), page-local
<style> block, and the body subtree minus shared chrome (topbar/footer/
skiplink), then emits a draft .astro file importing BaseLayout. The draft is
a starting point for review, never committed unreviewed.

Usage: to_astro.py index.html > site/src/pages/index.astro
"""
import re, sys, html.parser, pathlib

def extract(page_path):
    t = pathlib.Path(page_path).read_text(encoding='utf-8')
    title = (re.search(r'<title>(.*?)</title>', t, re.S) or [None,''])[1].strip()
    desc = ''
    m = re.search(r'name="description"\s+content="([^"]+)"', t) or \
        re.search(r'content="([^"]+)"\s+name="description"', t)
    if m: desc = m.group(1)
    styles = '\n\n'.join(m.group(1) for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S))
    scripts = '\n\n'.join(m.group(1) for m in re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', t, re.S))
    body = re.search(r'<body[^>]*>(.*)</body>', t, re.S)
    body = body.group(1) if body else ''
    # strip shared chrome — keep page content only. The site's topbar is a
    # <header> element (with or without class="topbar"); pages never use
    # <header> for content in this repo.
    body = re.sub(r'<a[^>]*class="skiplink"[^>]*>.*?</a>', '', body, flags=re.S)
    body = re.sub(r'<header[^>]*>.*?</header>', '', body, flags=re.S)
    body = re.sub(r'<nav[^>]*class="[^"]*topbar[^"]*"[^>]*>.*?</nav>', '', body, flags=re.S)
    body = re.sub(r'<footer[^>]*>.*?</footer>', '', body, flags=re.S)
    return title, desc, styles.strip(), body.strip(), scripts.strip()

def main():
    p = sys.argv[1]
    title, desc, styles, body, scripts = extract(p)
    name = pathlib.Path(p).stem
    out = ['---', 'import Base from "../layouts/Base.astro";',
           f'const title = {title!r};', f'const description = {desc!r};', '---',
           '<Base title={title} description={description}>', '', body, '', '</Base>']
    if styles:
        out += ['', '<style>', styles, '</style>']
    if scripts:
        out += ['', '<script is:inline>', scripts, '</script>']
    print('\n'.join(out))

if __name__ == '__main__':
    main()
