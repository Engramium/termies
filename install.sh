#!/usr/bin/env bash
# Install Termies themes into Warp's themes folder.
#
#   ./install.sh                 install every theme in themes/
#   ./install.sh soft-chat       install one theme (file name without .yaml)
#
# Set WARP_THEMES_DIR to override the destination folder.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"

dest="${WARP_THEMES_DIR:-}"
if [ -z "$dest" ]; then
  case "$(uname -s)" in
    Darwin) dest="$HOME/.warp/themes" ;;
    Linux)  dest="${XDG_DATA_HOME:-$HOME/.local/share}/warp-terminal/themes" ;;
    MINGW*|MSYS*|CYGWIN*) dest="$(cygpath -u "$APPDATA")/warp/Warp/data/themes" ;;
    *) echo "Unsupported system: $(uname -s). Set WARP_THEMES_DIR to install manually." >&2; exit 1 ;;
  esac
fi

if [ "$#" -eq 0 ]; then
  files=("$here"/themes/*.yaml)
else
  files=()
  for name in "$@"; do
    f="$here/themes/$name.yaml"
    if [ ! -f "$f" ]; then
      echo "No theme named '$name'. Available themes:" >&2
      for t in "$here"/themes/*.yaml; do basename "$t" .yaml >&2; done
      exit 1
    fi
    files+=("$f")
  done
fi

mkdir -p "$dest"
for f in "${files[@]}"; do
  cp "$f" "$dest/"
  echo "Installed $(basename "$f" .yaml) -> $dest"
done

echo "Done. In Warp, open Settings > Appearance > Themes and pick a theme."
