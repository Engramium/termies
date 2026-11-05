#!/usr/bin/env bash
# Install Termies themes for kitty, WezTerm or Alacritty.
#
#   ./install-terminals.sh kitty                  install every kitty theme
#   ./install-terminals.sh wezterm termies-soft-chat   install one WezTerm theme
#   ./install-terminals.sh alacritty              install every Alacritty theme
#
# Override the destination with KITTY_CONFIG_DIR, WEZTERM_COLORS_DIR or ALACRITTY_THEMES_DIR.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 kitty|wezterm|alacritty [theme-name ...]" >&2
  exit 1
fi

app="$1"
shift

case "$app" in
  kitty)
    src="$here/dist/kitty"
    dest="${KITTY_CONFIG_DIR:-$config_home/kitty}"
    ext="conf"
    ;;
  wezterm)
    src="$here/dist/wezterm"
    dest="${WEZTERM_COLORS_DIR:-$config_home/wezterm/colors}"
    ext="toml"
    ;;
  alacritty)
    src="$here/dist/alacritty"
    dest="${ALACRITTY_THEMES_DIR:-$config_home/alacritty/themes}"
    ext="toml"
    ;;
  *)
    echo "Unknown app '$app'. Use kitty, wezterm or alacritty." >&2
    exit 1
    ;;
esac

all_files=("$src"/*.$ext)
files=()

if [ "$#" -eq 0 ]; then
  files=("${all_files[@]}")
else
  for name in "$@"; do
    f="$src/$name.$ext"
    if [ ! -f "$f" ]; then
      echo "No $app theme named '$name'. Available themes:" >&2
      for t in "${all_files[@]}"; do basename "$t" ".$ext" >&2; done
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

case "$app" in
  kitty)
    echo "Done. Add a line like this to $config_home/kitty/kitty.conf, then reload kitty:"
    echo "  include termies-soft-chat.conf"
    ;;
  wezterm)
    echo "Done. Add this to your WezTerm config (wezterm.lua), then reload:"
    echo "  config.color_scheme = 'termies-soft-chat'"
    echo "  config.color_scheme_dirs = { '$config_home/wezterm/colors' }"
    ;;
  alacritty)
    echo "Done. Add this to $config_home/alacritty/alacritty.toml:"
    echo "  [general]"
    echo "  import = [\"~/.config/alacritty/themes/termies-soft-chat.toml\"]"
    ;;
esac
