#!/usr/bin/env python3
"""Create a Warp theme YAML from a few colors. Standard library only.

Example:
  python3 generator/make_theme.py --name "Dusk Chat" \
      --background "#1C1A24" --foreground "#DCD8E6" --accent "#B49BD9"

Add --mode light for light backgrounds. The output goes to themes/ by default.
The 16 ANSI colors are derived from a fixed set of muted hues; edit the
generated file if you want to tune any of them by hand.
"""
import argparse
import pathlib
import re
import sys

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Muted base hues, tuned separately for dark and light backgrounds.
HUES = {
    "dark": {
        "red": "#D9776F", "green": "#9CBF88", "yellow": "#D6B977",
        "blue": "#7F9FCB", "magenta": "#B392C9", "cyan": "#7DB8B5",
    },
    "light": {
        "red": "#B5534B", "green": "#5C7F4A", "yellow": "#9A7420",
        "blue": "#3D6B8C", "magenta": "#7D5A9A", "cyan": "#3E7F7B",
    },
}


def to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def mix(a, b, t):
    """Blend color a toward color b by fraction t (0 = a, 1 = b)."""
    ra, rb = to_rgb(a), to_rgb(b)
    return to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_yaml(name, mode, bg, fg, accent):
    hues = HUES[mode]
    normal = {
        "black": bg,
        "red": hues["red"],
        "green": hues["green"],
        "yellow": hues["yellow"],
        "blue": hues["blue"],
        "magenta": hues["magenta"],
        "cyan": hues["cyan"],
        "white": fg,
    }
    bright = {
        "black": mix(bg, fg, 0.35),
        **{k: mix(normal[k], "#FFFFFF", 0.2) for k in hues},
        "white": mix(fg, "#FFFFFF", 0.3),
    }
    escaped = name.replace('"', '\\"')
    lines = [
        "---",
        f'name: "{escaped}"',
        f'accent: "{accent}"',
        f'background: "{bg}"',
        f'foreground: "{fg}"',
        f"details: {'lighter' if mode == 'light' else 'darker'}",
        "terminal_colors:",
    ]
    for group, colors in (("normal", normal), ("bright", bright)):
        lines.append(f"  {group}:")
        for key in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            lines.append(f'    {key}: "{colors[key]}"')
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Create a Warp theme YAML.")
    parser.add_argument("--name", required=True, help="Theme name shown in Warp")
    parser.add_argument("--background", required=True, help="Background hex, e.g. #17181C")
    parser.add_argument("--foreground", required=True, help="Text hex, e.g. #D9DCE2")
    parser.add_argument("--accent", required=True, help="Accent hex, e.g. #8FA8C8")
    parser.add_argument("--mode", choices=["dark", "light"], default="dark")
    parser.add_argument("--out", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parent.parent / "themes",
                        help="Folder to write the file into (default: themes/)")
    args = parser.parse_args()

    for label, value in (("background", args.background),
                         ("foreground", args.foreground),
                         ("accent", args.accent)):
        if not HEX.match(value):
            sys.exit(f"--{label} must be a 6-digit hex color like #17181C, got {value!r}")

    slug = slugify(args.name)
    if not slug:
        sys.exit("--name must contain at least one letter or digit")

    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{slug}.yaml"
    target.write_text(build_yaml(args.name, args.mode, args.background,
                                 args.foreground, args.accent), encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
