#!/usr/bin/env python3
"""Show a Termies theme inside your terminal, before you install it.

The preview uses truecolor escape codes that color only this output. It never
changes your terminal's own palette, so it is safe to run in any terminal that
supports 24-bit color.

Usage:
  python3 scripts/preview_theme.py soft-chat
  python3 scripts/preview_theme.py soft-chat quiet-ink     several themes, one after another
  python3 scripts/preview_theme.py --list                  list the theme names

Standard library only. Reads the themes/*.yaml files directly.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
ANSI = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
RESET = "\x1b[0m"


def parse_theme(path):
    """Read the fixed layout of a Termies theme file. Returns name, colors, and the 16 ANSI colors."""
    name = accent = background = foreground = None
    normal, bright = {}, {}
    group = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or line.strip() == "---":
            continue
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("accent:"):
            accent = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("background:"):
            background = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("foreground:"):
            foreground = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("terminal_colors:"):
            group = None
        elif re.match(r"^  (normal|bright):\s*$", line):
            group = normal if "normal" in line else bright
        else:
            m = re.match(r'^    (\w+):\s*"?(#[0-9A-Fa-f]{6})"?\s*$', line)
            if m and group is not None and m.group(1) in ANSI:
                group[m.group(1)] = m.group(2)
    missing = [k for k, v in (("name", name), ("accent", accent), ("background", background),
                              ("foreground", foreground)) if not v]
    if missing or set(normal) != set(ANSI) or set(bright) != set(ANSI):
        raise ValueError(f"{path.name}: could not read {', '.join(missing) or 'the 16 ANSI colors'}")
    return {"name": name, "accent": accent, "background": background,
            "foreground": foreground, "normal": normal, "bright": bright}


def fg(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[38;2;{r};{g};{b}m"


def bg(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[48;2;{r};{g};{b}m"


def render(theme):
    """Return the preview as one string of text with escape codes."""
    base_bg = bg(theme["background"])
    text = fg(theme["foreground"])
    accent = fg(theme["accent"])
    n, b = theme["normal"], theme["bright"]
    dim = fg(b["black"])
    lines = []
    lines.append(f"{base_bg}{accent}\x1b[1m  {theme['name']}  {RESET}{base_bg}{text}")
    lines.append(f"{base_bg}{dim}  Preview only. Your terminal colors are not changed.{RESET}{base_bg}")
    lines.append("")

    # Normal and bright ANSI swatches, labeled.
    for label, colors in (("normal", n), ("bright", b)):
        row = "".join(f"{bg(colors[c])}      {base_bg}" for c in ANSI)
        names = "".join(f"{text}{c[:5]:<6}" for c in ANSI)
        lines.append(f"{base_bg}{dim}  {label:<7}{base_bg}{row}")
        lines.append(f"{base_bg}{' ' * 9}{names}{RESET}")
    lines.append("")

    # Sample output: prompt, a directory listing, an error, and git status.
    lines.append(f"{base_bg}{text}  {accent}user@host{text}:{fg(n['blue'])}~/project{text}$ ls -la")
    lines.append(f"{base_bg}{text}  {fg(n['blue'])}src/{text}      {fg(n['green'])}build.sh*{text}      README.md")
    lines.append(f"{base_bg}{text}  {fg(n['red'])}error:{text} cannot find module 'config'")
    lines.append(f"{base_bg}{text}  {fg(n['yellow'])}warning:{text} deprecated option 'legacy'")
    lines.append(f"{base_bg}{text}  On branch main  {fg(n['green'])}modified:{text} src/app.py")
    lines.append(f"{base_bg}{text}  {fg(n['magenta'])}#{text} {fg(n['cyan'])}cyan{text} {fg(b['magenta'])}bright magenta{text} "
                 f"{accent}accent{text}{RESET}")
    lines.append("")
    return "\n".join(lines) + RESET + "\n"


def main():
    parser = argparse.ArgumentParser(description="Preview Termies themes in your terminal.")
    parser.add_argument("names", nargs="*", help="theme names, e.g. soft-chat")
    parser.add_argument("--list", action="store_true", help="list the theme names")
    args = parser.parse_args()

    files = sorted(THEMES.glob("*.yaml"))
    if args.list or not args.names:
        for f in files:
            print(f.stem)
        return 0

    status = 0
    for name in args.names:
        path = THEMES / f"{name}.yaml"
        if not path.exists():
            print(f"No theme named '{name}'. Use --list to see the names.", file=sys.stderr)
            status = 1
            continue
        try:
            theme = parse_theme(path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            status = 1
            continue
        sys.stdout.write(render(theme))
    return status


if __name__ == "__main__":
    sys.exit(main())
