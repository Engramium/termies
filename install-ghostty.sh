#!/usr/bin/env bash
# Install Termies themes into Ghostty's themes folder.
#
#   ./install-ghostty.sh                  install every Ghostty theme
#   ./install-ghostty.sh termies-soft-chat   install one theme
#
# Set GHOSTTY_THEMES_DIR to override the destination folder.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="${GHOSTTY_THEMES_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/ghostty/themes}"

all_files=("$here"/dist/ghostty/*)
files=()

if [ "$#" -eq 0 ]; then
  files=("${all_files[@]}")
else
  for name in "$@"; do
    f="$here/dist/ghostty/$name"
    if [ ! -f "$f" ]; then
      echo "No Ghostty theme named '$name'. Available themes:" >&2
      for t in "${all_files[@]}"; do basename "$t" >&2; done
      exit 1
    fi
    files+=("$f")
  done
fi

mkdir -p "$dest"
for f in "${files[@]}"; do
  cp "$f" "$dest/"
  echo "Installed $(basename "$f") -> $dest"
done

echo "Done. Add this line to your Ghostty config, using the theme name you want:"
echo "  theme = termies-soft-chat"
