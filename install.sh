#!/usr/bin/env bash
# Install Termies themes into Warp's themes folder.
#
# Run from a clone:
#   ./install.sh                 interactive menu (or all themes when not run in a terminal)
#   ./install.sh soft-chat       install one theme (file name without .yaml)
#   ./install.sh soft-chat quiet-ink
#
# Run without a clone (downloads the themes from GitHub first):
#   bash <(curl -fsSL https://raw.githubusercontent.com/Engramium/termies/main/install.sh)
#
# Environment overrides:
#   WARP_THEMES_DIR   destination folder
#   TERMIES_API_URL   GitHub API folder listing (used when there is no clone)
#   TERMIES_RAW_URL   raw file base URL (used when there is no clone)
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

# Download the theme files when this script is not running from a clone.
fetch_remote_themes() {
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to download the themes." >&2
    exit 1
  fi
  local api="${TERMIES_API_URL:-https://api.github.com/repos/Engramium/termies/contents/themes}"
  local raw="${TERMIES_RAW_URL:-https://raw.githubusercontent.com/Engramium/termies/main/themes}"

  WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/termies.XXXXXX")"
  trap 'rm -rf "$WORK_DIR"' EXIT
  mkdir -p "$WORK_DIR/themes"

  local names
  if ! names="$(curl -fsSL "$api" | grep -o '"name": *"[^"]*\.yaml"' | sed 's/.*"\([^"]*\)"$/\1/')"; then
    echo "Could not list the themes from GitHub. Check your connection and try again." >&2
    exit 1
  fi
  if [ -z "$names" ]; then
    echo "No themes found at $api" >&2
    exit 1
  fi
  while IFS= read -r name; do
    if ! curl -fsSL "$raw/$name" -o "$WORK_DIR/themes/$name"; then
      echo "Download failed for $name" >&2
      exit 1
    fi
  done <<< "$names"
  themes_dir="$WORK_DIR/themes"
}

if [ -d "$here/themes" ] && compgen -G "$here/themes/*.yaml" >/dev/null; then
  themes_dir="$here/themes"
else
  fetch_remote_themes
fi

# All theme files, sorted.
all_files=("$themes_dir"/*.yaml)
files=()

if [ "$#" -gt 0 ]; then
  for name in "$@"; do
    f="$themes_dir/$name.yaml"
    if [ ! -f "$f" ]; then
      echo "No theme named '$name'. Available themes:" >&2
      for t in "${all_files[@]}"; do basename "$t" .yaml >&2; done
      exit 1
    fi
    files+=("$f")
  done
elif [ -t 0 ]; then
  echo "Termies themes:"
  i=1
  for t in "${all_files[@]}"; do
    printf "  %2d) %s\n" "$i" "$(basename "$t" .yaml)"
    i=$((i + 1))
  done
  echo
  echo "Enter the numbers to install, separated by spaces, or 'a' for all."
  read -r -p "> " choice
  if [ "$choice" = "a" ] || [ "$choice" = "all" ]; then
    files=("${all_files[@]}")
  else
    for n in $choice; do
      if ! [[ "$n" =~ ^[0-9]+$ ]] || [ "$n" -lt 1 ] || [ "$n" -gt "${#all_files[@]}" ]; then
        echo "Invalid choice: '$n'. Run the script again and pick numbers from the list." >&2
        exit 1
      fi
      files+=("${all_files[$((n - 1))]}")
    done
  fi
  if [ "${#files[@]}" -eq 0 ]; then
    echo "Nothing selected."
    exit 0
  fi
else
  # Not running in a terminal (for example, in CI): install everything.
  files=("${all_files[@]}")
fi

mkdir -p "$dest"
for f in "${files[@]}"; do
  cp "$f" "$dest/"
  echo "Installed $(basename "$f" .yaml) -> $dest"
done

echo "Done. In Warp, open Settings > Appearance > Themes and pick a theme."
