#!/usr/bin/env python3
"""Export the Warp palettes for Windows Terminal, iTerm2, Ghostty, kitty, WezTerm and Alacritty.

Writes:
  dist/windows-terminal/termies-<slug>.json   a color scheme object
  dist/iterm2/termies-<slug>.itermcolors      an iTerm2 color preset (XML plist)
  dist/ghostty/termies-<slug>                 a Ghostty theme file (key = value)
  dist/kitty/termies-<slug>.conf              a kitty color snippet (use: include ...)
  dist/wezterm/termies-<slug>.toml            a WezTerm color scheme (TOML)
  dist/alacritty/termies-<slug>.toml          an Alacritty theme (import it in alacritty.toml)

Usage:
  python3 scripts/build_terminal_exports.py           write the files
  python3 scripts/build_terminal_exports.py --check   fail if committed files are out of date

Requires PyYAML.
"""
import argparse
import json
import pathlib
import plistlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from palette import mix  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
DIST = ROOT / "dist"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Windows Terminal scheme keys, and the Termies palette key each one comes from.
WT_ANSI = [
    ("black", "black"), ("red", "red"), ("green", "green"), ("yellow", "yellow"),
    ("blue", "blue"), ("purple", "magenta"), ("cyan", "cyan"), ("white", "white"),
]
WT_BRIGHT = [
    ("brightBlack", "black"), ("brightRed", "red"), ("brightGreen", "green"),
    ("brightYellow", "yellow"), ("brightBlue", "blue"), ("brightPurple", "magenta"),
    ("brightCyan", "cyan"), ("brightWhite", "white"),
]

# iTerm2 preset keys for the 16 ANSI colors, in order.
ITERM_ORDER = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
]


def slug_of(name):
    return "termies-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def palette(theme):
    """Every color one export needs, taken from one theme."""
    bg, fg, accent = theme["background"], theme["foreground"], theme["accent"]
    normal = theme["terminal_colors"]["normal"]
    bright = theme["terminal_colors"]["bright"]
    return {
        "background": bg,
        "foreground": fg,
        "cursor": accent,
        "selection": mix(bg, accent, 0.30),
        "normal": normal,
        "bright": bright,
    }


def windows_terminal(theme):
    p = palette(theme)
    scheme = {
        "name": f"Termies {theme['name']}",
        "background": p["background"],
        "foreground": p["foreground"],
        "cursorColor": p["cursor"],
        "selectionBackground": p["selection"],
    }
    for key, source in WT_ANSI:
        scheme[key] = p["normal"][source]
    for key, source in WT_BRIGHT:
        scheme[key] = p["bright"][source]
    return scheme


def rgb_component(hex_color):
    h = hex_color.lstrip("#")
    return {
        "Red Component": int(h[0:2], 16) / 255,
        "Green Component": int(h[2:4], 16) / 255,
        "Blue Component": int(h[4:6], 16) / 255,
        "Alpha Component": 1.0,
        "Color Space": "sRGB",
    }


def iterm2(theme):
    p = palette(theme)
    preset = {
        "Background Color": rgb_component(p["background"]),
        "Foreground Color": rgb_component(p["foreground"]),
        "Cursor Color": rgb_component(p["cursor"]),
        "Cursor Text Color": rgb_component(p["background"]),
        "Selection Color": rgb_component(p["selection"]),
        "Selected Text Color": rgb_component(p["foreground"]),
        "Bold Color": rgb_component(p["foreground"]),
    }
    for i, name in enumerate(ITERM_ORDER):
        preset[f"Ansi {i} Color"] = rgb_component(p["normal"][name])
    for i, name in enumerate(ITERM_ORDER):
        preset[f"Ansi {i + 8} Color"] = rgb_component(p["bright"][name])
    return preset


def ghostty(theme, slug):
    """A Ghostty theme file: plain key = value lines, saved without an extension."""
    p = palette(theme)
    lines = [
        f"# {theme['name']} (Termies)",
        f"background = {p['background']}",
        f"foreground = {p['foreground']}",
        f"cursor-color = {p['cursor']}",
        f"selection-background = {p['selection']}",
        f"selection-foreground = {p['foreground']}",
    ]
    for i, name in enumerate(ITERM_ORDER):
        lines.append(f"palette = {i}={p['normal'][name]}")
    for i, name in enumerate(ITERM_ORDER):
        lines.append(f"palette = {i + 8}={p['bright'][name]}")
    text = "\n".join(lines) + "\n"
    for line in lines[1:]:
        value = line.split("=")[-1].strip()
        assert HEX.match(value), f"{slug}: bad color in line {line!r}"
    return text


def kitty(theme, slug):
    """A kitty config snippet, loaded with 'include termies-<name>.conf' in kitty.conf."""
    p = palette(theme)
    lines = [
        f"# {theme['name']} (Termies)",
        f"foreground {p['foreground']}",
        f"background {p['background']}",
        f"cursor {p['cursor']}",
        f"selection_foreground {p['foreground']}",
        f"selection_background {p['selection']}",
    ]
    for i, name in enumerate(ITERM_ORDER):
        lines.append(f"color{i} {p['normal'][name]}")
    for i, name in enumerate(ITERM_ORDER):
        lines.append(f"color{i + 8} {p['bright'][name]}")
    return "\n".join(lines) + "\n"


def wezterm(theme, slug):
    """A WezTerm color scheme file, saved as ~/.config/wezterm/colors/<name>.toml."""
    p = palette(theme)
    ansi = [p["normal"][name] for name in ITERM_ORDER]
    brights = [p["bright"][name] for name in ITERM_ORDER]
    lines = [
        "[colors]",
        f'foreground = "{p["foreground"]}"',
        f'background = "{p["background"]}"',
        f'cursor_bg = "{p["cursor"]}"',
        f'cursor_fg = "{p["background"]}"',
        f'cursor_border = "{p["cursor"]}"',
        f'selection_fg = "{p["foreground"]}"',
        f'selection_bg = "{p["selection"]}"',
        "ansi = [" + ", ".join(f'"{c}"' for c in ansi) + "]",
        "brights = [" + ", ".join(f'"{c}"' for c in brights) + "]",
        "",
        "[metadata]",
        f'name = "Termies {theme["name"]}"',
        'author = "Termies"',
    ]
    return "\n".join(lines) + "\n"


def alacritty(theme, slug):
    """An Alacritty theme file, loaded with [general] import in alacritty.toml."""
    p = palette(theme)
    lines = [
        "[colors.primary]",
        f'background = "{p["background"]}"',
        f'foreground = "{p["foreground"]}"',
        "",
        "[colors.cursor]",
        f'text = "{p["background"]}"',
        f'cursor = "{p["cursor"]}"',
        "",
        "[colors.selection]",
        f'text = "{p["foreground"]}"',
        f'background = "{p["selection"]}"',
        "",
        "[colors.normal]",
    ]
    lines += [f'{name} = "{p["normal"][name]}"' for name in ITERM_ORDER]
    lines += ["", "[colors.bright]"]
    lines += [f'{name} = "{p["bright"][name]}"' for name in ITERM_ORDER]
    return "\n".join(lines) + "\n"


def build_all():
    """Return {relative path: text or bytes} for every export."""
    out = {}
    for path in sorted(THEMES.glob("*.yaml")):
        theme = yaml.safe_load(path.read_text(encoding="utf-8"))
        slug = slug_of(theme["name"])
        scheme = windows_terminal(theme)
        for key, value in scheme.items():
            if key != "name":
                assert HEX.match(value), f"{slug}: {key} is not hex: {value!r}"
        out[f"dist/windows-terminal/{slug}.json"] = json.dumps(scheme, indent=2, ensure_ascii=False) + "\n"
        out[f"dist/iterm2/{slug}.itermcolors"] = plistlib.dumps(iterm2(theme), fmt=plistlib.FMT_XML)
        out[f"dist/ghostty/{slug}"] = ghostty(theme, slug)
        out[f"dist/kitty/{slug}.conf"] = kitty(theme, slug)
        out[f"dist/wezterm/{slug}.toml"] = wezterm(theme, slug)
        out[f"dist/alacritty/{slug}.toml"] = alacritty(theme, slug)
        for rel in (f"dist/kitty/{slug}.conf", f"dist/wezterm/{slug}.toml", f"dist/alacritty/{slug}.toml"):
            for value in re.findall(r'#[0-9A-Fa-f]{3,8}\b', out[rel]):
                assert HEX.match(value), f"{rel}: bad color {value!r}"
    return out


def main():
    parser = argparse.ArgumentParser(description="Export Windows Terminal and iTerm2 themes.")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if committed files differ from what would be built")
    args = parser.parse_args()

    built = build_all()

    if args.check:
        stale = []
        for rel, content in built.items():
            target = ROOT / rel
            if not target.exists():
                stale.append(rel)
                continue
            current = target.read_bytes()
            expected = content.encode("utf-8") if isinstance(content, str) else content
            if current != expected:
                stale.append(rel)
        if stale:
            print("Out of date (run scripts/build_terminal_exports.py):")
            for s in stale:
                print(f"  {s}")
            return 1
        print(f"All {len(built)} terminal exports are up to date.")
        return 0

    for rel, content in built.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)
        print(f"Wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
