#!/bin/bash
# Full-site visual parity: old tree (:8899) vs astro dist (:8898).
# Usage: ./scripts/migrate/vdiff_all.sh [port_old] [port_new]
OLD=${1:-8899}; NEW=${2:-8898}
cd "$(dirname "$0")/../.." || exit 1
ok=0; warn=0; fail=0
for f in $(ls *.html tools/*.html 2>/dev/null); do
  name=${f%.html}; name=${name//\//_}
  out=$(./scripts/migrate/visual_diff.sh "http://localhost:$OLD/$f" "http://localhost:$NEW/$f" "$name" 2>/dev/null | tail -1)
  pct=$(echo "$out" | grep -o '[0-9.]*%' | tr -d '%')
  printf '%-22s %s\n' "$f" "${pct:-N/A}%"
  case "$pct" in
    "" ) fail=$((fail+1));;
    *) if (( $(echo "$pct < 3" | bc -l) )); then ok=$((ok+1)); elif (( $(echo "$pct < 15" | bc -l) )); then warn=$((warn+1)); else fail=$((fail+1)); fi;;
  esac
done
echo "== $ok tight (<3%) | $warn delta (3-15%) | $fail broken (>=15% or missing) ==" 1>&2
