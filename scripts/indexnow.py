#!/usr/bin/env python3
"""Submit sitemap URLs to IndexNow (Bing/Yandex instant indexing, no account needed).

The key file <KEY>.txt must be deployed at the site root (see site/public/).
Usage: python3 scripts/indexnow.py [--host HOST] [--key KEY]
"""
import json, sys, urllib.request, xml.etree.ElementTree as ET

HOST = "trendscope.zalize.com"
KEY = "f24ed6af513c4c46b65fd4302bc30283"  # matches site/public/<KEY>.txt
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls(path="sitemap.xml"):
    root = ET.parse(path).getroot()
    return [loc.text for loc in root.iter() if loc.tag.endswith("loc")]


def main():
    host, key = HOST, KEY
    argv = sys.argv[1:]
    if "--host" in argv:
        host = argv[argv.index("--host") + 1]
    if "--key" in argv:
        key = argv[argv.index("--key") + 1]
    urls = sitemap_urls()
    # verify key file is live before submitting
    key_url = f"https://{host}/{key}.txt"
    req0 = urllib.request.Request(key_url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req0, timeout=20) as r:
        assert r.read().decode().strip() == key, "key file mismatch"
    body = json.dumps({
        "host": host,
        "key": key,
        "keyLocation": key_url,
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("indexnow", r.status, f"submitted {len(urls)} urls")
    except urllib.error.HTTPError as e:
        print("indexnow", e.code, e.read()[:300])


if __name__ == "__main__":
    main()
