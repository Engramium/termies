#!/usr/bin/env bash
# Capture a real Warp screenshot for each Warp theme (macOS only).
#
# For each theme the script tells you which one to pick in Warp. You pick it,
# come back to this terminal, press Enter, and then click the Warp window.
# The screenshot is saved to screenshots/warp/<theme>.png.
#
#   ./scripts/capture_warp_screenshots.sh                 all themes
#   ./scripts/capture_warp_screenshots.sh soft-chat quiet-ink
#
# Requires macOS and the Screen Recording permission for your terminal app
# (System Settings > Privacy & Security > Screen Recording).
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This script uses macOS screencapture and only runs on macOS." >&2
  exit 1
fi

here="$(cd "$(dirname "$0")/.." && pwd)"
out="$here/screenshots/warp"
mkdir -p "$out"

all_files=("$here"/themes/*.yaml)
files=()
if [ "$#" -eq 0 ]; then
  files=("${all_files[@]}")
else
  for slug in "$@"; do
    f="$here/themes/$slug.yaml"
    if [ ! -f "$f" ]; then
      echo "No theme named '$slug'." >&2
      exit 1
    fi
    files+=("$f")
  done
fi

total="${#files[@]}"
i=0
for f in "${files[@]}"; do
  i=$((i + 1))
  slug="$(basename "$f" .yaml)"
  name="$(sed -n 's/^name: *//p' "$f" | head -1 | tr -d '"')"
  echo
  echo "[$i/$total] Pick '$name' in Warp (Settings > Appearance > Themes)."
  read -r -p "Press Enter when it is selected, then click the Warp window: " _ < /dev/tty
  screencapture -o -w "$out/$slug.png"
  echo "Saved screenshots/warp/$slug.png"
done

echo
echo "Done. Screenshots are in $out"
