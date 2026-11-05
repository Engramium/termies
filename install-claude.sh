#!/usr/bin/env bash
# Install Termies themes into Claude Code's themes folder (~/.claude/themes).
#
#   ./install-claude.sh                  install every Claude Code theme
#   ./install-claude.sh termies-soft-chat   install one theme (file name without .json)
#
# Set CLAUDE_THEMES_DIR to override the destination folder.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_THEMES_DIR:-$HOME/.claude/themes}"

all_files=("$here"/claude-code/themes/*.json)
files=()

if [ "$#" -eq 0 ]; then
  files=("${all_files[@]}")
else
  for name in "$@"; do
    f="$here/claude-code/themes/$name.json"
    if [ ! -f "$f" ]; then
      echo "No Claude Code theme named '$name'. Available themes:" >&2
      for t in "${all_files[@]}"; do basename "$t" .json >&2; done
      exit 1
    fi
    files+=("$f")
  done
fi

mkdir -p "$dest"
for f in "${files[@]}"; do
  cp "$f" "$dest/"
  echo "Installed $(basename "$f" .json) -> $dest"
done

echo "Done. In Claude Code, run /theme and pick a Termies theme."
