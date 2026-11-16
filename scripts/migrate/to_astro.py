#!/usr/bin/env python3
"""to_astro.py <page.html> — mechanical HTML->Astro transcription helper.

Splits a legacy page into: frontmatter props (title/description), page-local
<style> block, and the body subtree minus shared chrome (topbar/footer/
skiplink), then emits a draft .astro file importing BaseLayout. The draft is
a starting point for review, never committed unreviewed.

Usage: to_astro.py index.html > site/src/pages/index.astro
"""
import re, sys, json, html.parser, pathlib

def extract(page_path):
    t = pathlib.Path(page_path).read_text(encoding='utf-8')
    title = (re.search(r'<title>(.*?)</title>', t, re.S) or [None,''])[1].strip()
    desc = ''
    m = re.search(r'name="description"\s+content="([^"]+)"', t) or \
        re.search(r'content="([^"]+)"\s+name="description"', t)
    if m: desc = m.group(1)
    styles = '\n\n'.join(m.group(1) for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S))
    # keep the tag attrs too — type="module" matters (top-level await etc.)
    scripts = [(m.group(1), m.group(2)) for m in
               re.finditer(r'<script((?![^>]*src=)[^>]*)>(.*?)</script>', t, re.S)]
    body = re.search(r'<body[^>]*>(.*)</body>', t, re.S)
    body = body.group(1) if body else ''
    # strip shared chrome only: the sticky topbar header + skiplink +
    # shared footer. `<header class="hero">` IS page content — keep it.
    body = re.sub(r'<a[^>]*class="skiplink"[^>]*>.*?</a>', '', body, flags=re.S)
    body = re.sub(r'<header[^>]*class="topbar"[^>]*>.*?</header>', '', body, flags=re.S)
    body = re.sub(r'<nav[^>]*class="[^"]*topbar[^"]*"[^>]*>.*?</nav>', '', body, flags=re.S)
    body = re.sub(r'<footer[^>]*>.*?</footer>', '', body, flags=re.S)
    # lift scripts/styles out of body — they're re-emitted at the end as
    # is:inline / is:global. Left in place, Astro would try to bundle the
    # <script> tags (and scope the <style> tags).
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.S)
    body = re.sub(r'<script(?![^>]*src=)[^>]*>.*?</script>', '', body, flags=re.S)
    # Astro template parses {} as expressions — entity-encode them. Entities
    # decode back to the same chars in both text nodes and attribute values.
    body = body.replace('{', '&#123;').replace('}', '&#125;')
    return title, desc, styles.strip(), body.strip(), scripts

# topbar nav keys — best-effort guess; reviewer may correct.
NAV = {'movers': 'movers', 'topics': 'topics', 'digest': 'digests',
       'week': 'digests', 'about': 'about', 'why': 'about', 'faq': 'about',
       'source': 'board', 'sources': 'board', 'domain': 'board',
       'domains': 'board', 'author': 'board', 'authors': 'board'}

def main():
    p = sys.argv[1]
    title, desc, styles, body, scripts = extract(p)
    name = pathlib.Path(p).stem
    nav = NAV.get(name, 'none')
    # JSON-quoted strings are valid JS — repr() is not (\x/unicode escapes differ).
    out = ['---', 'import Base from "../layouts/Base.astro";',
           f'const title = {json.dumps(title)};', f'const description = {json.dumps(desc)};',
           f'const path = \'/{name}.html\';', '---',
           f'<Base title={{title}} description={{description}} path={{path}} nav="{nav}">',
           '', body, '', '</Base>']
    if styles:
        # is:global — Astro scopes <style> by default; legacy selectors
        # target the verbatim body markup and must not get hashed.
        out += ['', '<style is:global>', styles, '</style>']
    # Astro parses {} inside inline <script> text as expressions — arrow fns
    # like e=>{ break the build. Only reliable verbatim path: external file.
    outdir = pathlib.Path('site/public/js/pages')
    for kind in ('classic', 'module'):
        blocks = [c.strip() for a, c in scripts
                  if c.strip() and ('module' in a) == (kind == 'module')]
        if not blocks:
            continue
        outdir.mkdir(parents=True, exist_ok=True)
        suffix = '.mjs' if kind == 'module' else '.js'
        fname = f'{name}{suffix}'
        (outdir / fname).write_text('\n\n'.join(blocks) + '\n',
                                    encoding='utf-8')
        mod = ' type="module"' if kind == 'module' else ''
        out += ['', f'<script is:inline src="/js/pages/{fname}"{mod}></script>']
    print('\n'.join(out))

if __name__ == '__main__':
    main()
