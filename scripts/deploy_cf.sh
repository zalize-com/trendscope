#!/usr/bin/env bash
# Deploy trendscope to Cloudflare Pages (project: trendscope → trendscope.pages.dev).
#
# Auth (either):
#   CLOUDFLARE_API_TOKEN                    — scoped API token with Pages edit
#   CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL   — Global API Key pair
#
# Assets >25 MiB (data/latest.json, data/history.csv) cannot be stored on
# Pages — site/public/_redirects 302s those paths to GitHub raw, so they are
# excluded from the upload here.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/opt/node24/bin:$PATH"
ORIGIN="${SITE_ORIGIN:-https://trendscope.zalize.com}"
OUT="$ROOT/.deploy-cf"

cd "$ROOT/site"
SITE_ORIGIN="$ORIGIN" SITE_BASE="" npm run build

rm -rf "$OUT"
mkdir -p "$OUT"
cp -rL "$ROOT/site/dist/." "$OUT/"

rm -f "$OUT/data/latest.json" "$OUT/data/history.csv" "$OUT/docs/api/series.json"

# repo-level generated files (sitemap.xml, feed.xml, llms.txt, ...) still name
# the preview origin — repoint the deploy copy only; repo files switch via
# scripts/switch_domain.py once the public domain is final.
OLD="https://trendscope--plov6nur.preview.devinapps.com"
if [ "$ORIGIN" != "$OLD" ]; then
  grep -rl "$OLD" "$OUT" | xargs sed -i "s|$OLD|$ORIGIN|g"
fi

npx -y wrangler@latest pages deploy "$OUT" \
  --project-name "${CF_PROJECT:-trendscope}" --branch main --commit-dirty=true
echo "deployed → $ORIGIN"
