#!/usr/bin/env python3
"""Check every theme in themes/ before it reaches users.

Requires PyYAML (pip install pyyaml). Exits with status 1 if any file fails.

Checks:
  - required top-level keys and the 16 terminal colors are present
  - every color is a 6-digit hex value
  - details matches the background: "darker" needs a dark background,
    "lighter" needs a light one
  - text on the background meets WCAG AA contrast (4.5:1)
  - the file name is a lowercase slug
"""
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from palette import HEX, contrast, luminance  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED = {"name", "accent", "background", "foreground", "details", "terminal_colors"}
ANSI = {"black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"}
MIN_CONTRAST = 4.5
# High Contrast themes (feature F3) must clear a stricter text contrast bar.
HIGH_CONTRAST_FILES = {"contrast-night", "contrast-day"}
HIGH_CONTRAST_MIN = 7.0
# Colored ANSI colors (red, green, yellow, blue, magenta, cyan) must reach this contrast
# against the background. 3:1 is the WCAG floor for graphics and UI components.
ANSI_COLORED = ["red", "green", "yellow", "blue", "magenta", "cyan"]
ANSI_MIN_CONTRAST = 3.0
# Themes that already fail the ANSI check. They are reported as warnings, not errors,
# until they are fixed. A new or edited theme that fails is an error.
ANSI_GRANDFATHERED = {
    'agent-night',  # blue path measured from a screenshot; kept as measured
    'paper-light', 'paper-thread',  # original Warp themes; kept until the owner decides
}


def check(path):
    errors = []
    warnings = []
    if not SLUG.match(path.stem):
        errors.append(f"file name '{path.stem}' should be a lowercase slug like 'soft-chat'")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"invalid YAML: {exc}"], []
    if not isinstance(data, dict):
        return ["file must contain a YAML mapping"], [], []

    missing = REQUIRED - set(data)
    if missing:
        errors.append(f"missing keys: {', '.join(sorted(missing))}")
        return errors, warnings

    if not isinstance(data["name"], str) or not data["name"].strip():
        errors.append("name must be a non-empty string")

    for key in ("accent", "background", "foreground"):
        if not isinstance(data[key], str) or not HEX.match(data[key]):
            errors.append(f"{key} must be a 6-digit hex color, got {data[key]!r}")

    colors = data["terminal_colors"]
    if not isinstance(colors, dict) or set(colors) != {"normal", "bright"}:
        errors.append("terminal_colors must have exactly 'normal' and 'bright'")
    else:
        for group in ("normal", "bright"):
            if not isinstance(colors[group], dict) or set(colors[group]) != ANSI:
                errors.append(f"terminal_colors.{group} must have exactly the 8 ANSI colors")
                continue
            for key, value in colors[group].items():
                if not isinstance(value, str) or not HEX.match(value):
                    errors.append(f"terminal_colors.{group}.{key} must be hex, got {value!r}")

    # The checks below need valid background and foreground colors.
    if not (HEX.match(str(data["background"])) and HEX.match(str(data["foreground"]))):
        return errors, warnings

    bg, fg = data["background"], data["foreground"]
    is_dark_bg = luminance(bg) < 0.18
    if data["details"] not in ("darker", "lighter"):
        errors.append(f"details must be 'darker' or 'lighter', got {data['details']!r}")
    elif data["details"] == "darker" and not is_dark_bg:
        errors.append("details is 'darker' but the background is light")
    elif data["details"] == "lighter" and is_dark_bg:
        errors.append("details is 'lighter' but the background is dark")

    ratio = contrast(fg, bg)
    required = HIGH_CONTRAST_MIN if path.stem in HIGH_CONTRAST_FILES else MIN_CONTRAST
    if ratio < required:
        errors.append(f"text contrast is {ratio:.2f}:1, below {required}:1")

    weak = []
    for group in ("normal", "bright"):
        for color in ANSI_COLORED:
            value = data["terminal_colors"][group][color]
            ratio_ansi = contrast(value, bg)
            if ratio_ansi < ANSI_MIN_CONTRAST:
                weak.append(f"{group}.{color} is {ratio_ansi:.2f}:1 on the background")
    if weak:
        if path.stem in ANSI_GRANDFATHERED:
            warnings.append(f"{len(weak)} colored ANSI colors below {ANSI_MIN_CONTRAST}:1 (grandfathered)")
        else:
            errors.extend(weak)

    return errors, warnings


def main():
    files = sorted(THEMES.glob("*.yaml"))
    if not files:
        print(f"No theme files found in {THEMES}")
        return 1

    failed = 0
    for path in files:
        problems, notes = check(path)
        if problems:
            failed += 1
            print(f"FAIL {path.relative_to(ROOT)}")
            for problem in problems:
                print(f"     - {problem}")
        else:
            print(f"ok   {path.relative_to(ROOT)}")
        for note in notes:
            print(f"warn {path.relative_to(ROOT)}: {note}")

    print(f"\n{len(files) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
