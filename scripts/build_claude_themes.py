#!/usr/bin/env python3
"""Build Claude Code themes from the Warp palettes in themes/.

Writes claude-code/themes/<slug>.json. Claude Code reads these from
~/.claude/themes/ and lists them under /theme. Each file has the shape:

  {"name": "...", "base": "dark" | "light", "overrides": {token: color}}

Only the tokens listed in MAPPING are overridden; Claude Code fills in the rest
from the base theme. Text-like colors are pushed toward the foreground until
they reach 4.5:1 contrast on the background.

Usage:
  python3 scripts/build_claude_themes.py           write the files
  python3 scripts/build_claude_themes.py --check   fail if committed files are out of date

Requires PyYAML.
"""
import argparse
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from palette import HEX, contrast, mix, neutrals  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
OUT = ROOT / "claude-code" / "themes"
MIN_TEXT_CONTRAST = 4.5

# Colorblind-friendly Claude Code bases (feature F3), keyed by theme slug.
DALTONIZED_BASE = {
    "termies-safe-harbor": "dark-daltonized",
    "termies-safe-harbor-light": "light-daltonized",
}


def readable(color, bg, fg, target=MIN_TEXT_CONTRAST):
    """Move color toward the foreground until it reaches the target contrast."""
    for step in range(0, 21):
        candidate = mix(color, fg, step / 20)
        if contrast(candidate, bg) >= target:
            return candidate
    return fg


def overrides_for(theme):
    fg, bg, accent = theme["foreground"], theme["background"], theme["accent"]
    normal = theme["terminal_colors"]["normal"]
    bright = theme["terminal_colors"]["bright"]
    layers = neutrals(theme)
    green, red = normal["green"], normal["red"]

    # Foreground roles: must read clearly on the background.
    text_roles = {
        "claude": accent,
        "claudeShimmer": mix(accent, "#FFFFFF", 0.25),
        "bashBorder": accent,
        "clawd_body": accent,
        "permission": normal["blue"],
        "permissionShimmer": bright["blue"],
        "suggestion": normal["blue"],
        "remember": normal["blue"],
        "ide": normal["cyan"],
        "planMode": normal["cyan"],
        "success": green,
        "error": red,
        "warning": normal["yellow"],
        "warningShimmer": bright["yellow"],
        "merged": normal["magenta"],
        "inactive": layers["subtext0"],
        "inactiveShimmer": layers["subtext1"],
        "subtle": layers["overlay0"],
        "promptBorder": layers["overlay0"],
        "promptBorderShimmer": layers["overlay1"],
    }
    out = {"text": fg, "inverseText": bg}
    for token, color in text_roles.items():
        out[token] = readable(color, bg, fg)

    # Background tints from the layered neutrals (feature F1): raised surfaces behind text.
    out.update({
        "userMessageBackground": layers["surface0"],
        "userMessageBackgroundHover": layers["surface1"],
        "selectionBg": layers["surface2"],
        "diffAdded": mix(green, bg, 0.75),
        "diffAddedDimmed": mix(green, bg, 0.85),
        "diffAddedWord": mix(green, bg, 0.55),
        "diffRemoved": mix(red, bg, 0.75),
        "diffRemovedDimmed": mix(red, bg, 0.85),
        "diffRemovedWord": mix(red, bg, 0.55),
    })
    return out


def build(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    name = f"Termies {data['name']}"
    slug = "termies-" + re.sub(r"[^a-z0-9]+", "-", data["name"].lower()).strip("-")
    doc = {
        "name": name,
        "base": DALTONIZED_BASE.get(slug, "dark" if data["details"] == "darker" else "light"),
        "overrides": overrides_for(data),
    }
    for token, color in doc["overrides"].items():
        assert HEX.match(color), f"{slug}: {token} produced invalid color {color!r}"
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    return slug, text


def main():
    parser = argparse.ArgumentParser(description="Build Claude Code themes.")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if committed files differ from what would be built")
    args = parser.parse_args()

    built = dict(build(p) for p in sorted(THEMES.glob("*.yaml")))

    if args.check:
        stale = []
        for slug, text in built.items():
            target = OUT / f"{slug}.json"
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(target.relative_to(ROOT).as_posix())
        if stale:
            print("Out of date (run scripts/build_claude_themes.py):")
            for s in stale:
                print(f"  {s}")
            return 1
        print(f"All {len(built)} Claude Code themes are up to date.")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for slug, text in built.items():
        (OUT / f"{slug}.json").write_text(text, encoding="utf-8")
        print(f"Wrote claude-code/themes/{slug}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
