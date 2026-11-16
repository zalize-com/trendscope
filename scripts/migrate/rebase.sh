#!/usr/bin/env bash
# Rebase root-absolute URLs in dist/ for a subpath deployment (GitHub project Pages).
# Run from site/ after `astro build`. No-op when SITE_BASE is unset/empty.
#   SITE_BASE=/trendscope bash ../scripts/migrate/rebase.sh
# Page-body JS fetches stay relative ("data/...", "docs/...") so they resolve
# against the page URL correctly under any base; only html attributes are rewritten.
# XML manifests (sitemap/opensearch) carry the build-time origin verbatim —
# rewrite it to SITE_ORIGIN when that is set.
set -euo pipefail
BASE="${SITE_BASE:-}"
BASE="${BASE%/}"
ORIGIN="${SITE_ORIGIN:-}"
PREVIEW='https://trendscope--plov6nur.preview.devinapps.com'
[ -z "$BASE" ] && [ -z "$ORIGIN" ] && { echo "SITE_BASE/SITE_ORIGIN unset - nothing to rebase"; exit 0; }
[ -d dist ] || { echo "dist/ not found - run from site/" >&2; exit 1; }
if [ -n "$BASE" ]; then
  find dist -name '*.html' -print0 | xargs -0 sed -i -E \
    's#(href|src|action|poster)="/#\1="'"$BASE"'/#g'
  echo "rebased root-absolute refs -> $BASE"
fi
if [ -n "$ORIGIN" ] && [ "$ORIGIN" != "$PREVIEW" ]; then
  find dist \( -name '*.xml' -o -name '*.html' -o -name '*.txt' \) -print0 \
    | xargs -0 sed -i "s#${PREVIEW}#${ORIGIN%/}#g"
  echo "rewrote origin $PREVIEW -> ${ORIGIN%/}"
fi
