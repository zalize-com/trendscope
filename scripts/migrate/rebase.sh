#!/usr/bin/env bash
# Rebase root-absolute URLs in dist/ for a subpath deployment (GitHub project Pages).
# Run from site/ after `astro build`. No-op when SITE_BASE is unset/empty.
#   SITE_BASE=/trendscope bash ../scripts/migrate/rebase.sh
# Page-body JS fetches stay relative ("data/...", "docs/...") so they resolve
# against the page URL correctly under any base; only html attributes are rewritten.
set -euo pipefail
BASE="${SITE_BASE:-}"
BASE="${BASE%/}"
[ -z "$BASE" ] && { echo "SITE_BASE unset - nothing to rebase"; exit 0; }
[ -d dist ] || { echo "dist/ not found - run from site/" >&2; exit 1; }
find dist -name '*.html' -print0 | xargs -0 sed -i -E \
  's#(href|src|action|poster)="/#\1="'"$BASE"'/#g'
echo "rebased root-absolute refs -> $BASE"
