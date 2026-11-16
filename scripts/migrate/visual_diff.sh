#!/usr/bin/env bash
# visual_diff.sh <old-url> <new-url> <name> — headless-Chrome screenshot both,
# pixel-diff with PIL, save triple (old/new/diff) under /tmp/vdiff/<name>/.
# Exit 0 always; prints a coarse diff % for the caller to eyeball.
set -e
OLD="$1"; NEW="$2"; NAME="${3:-page}"
OUT="/tmp/vdiff/$NAME"; mkdir -p "$OUT"
CHROME=${CHROME:-google-chrome}
for which in old new; do
  url=$OLD; [ "$which" = new ] && url=$NEW
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --window-size=1280,2400 --screenshot="$OUT/$which.png" "$url" >/dev/null 2>&1
done
python3 - "$OUT" << 'PY'
import sys
from PIL import Image, ImageChops
old, new = Image.open(f"{sys.argv[1]}/old.png"), Image.open(f"{sys.argv[1]}/new.png")
w = min(old.width, new.width); h = min(old.height, new.height)
old, new = old.crop((0,0,w,h)).convert("RGB"), new.crop((0,0,w,h)).convert("RGB")
diff = ImageChops.difference(old, new)
bbox = diff.getbbox()
import math
px = list(diff.getdata()); n = len(px)
changed = sum(1 for p in px if max(p) > 24)
diff.save(f"{sys.argv[1]}/diff.png")
print(f"diff: {changed/n*100:.2f}% pixels differ (>24 channel delta); bbox={bbox}")
PY
