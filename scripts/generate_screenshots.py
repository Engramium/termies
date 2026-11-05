#!/usr/bin/env python3
"""Generate a screenshot for every theme that has no real screenshot yet (feature 5).

Output goes to screenshots/generated/<theme>.png. These are mockups drawn from the
theme's own palette, not captures of the Warp app. Real captures from
scripts/capture_warp_screenshots.sh live in screenshots/warp/ and always take
priority in the README.

Needs Google Chrome (or set CHROME to another Chromium-based browser). Optional:
oxipng on your PATH, which compresses the PNGs further.

Usage:
  python3 scripts/generate_screenshots.py            generate missing screenshots
  python3 scripts/generate_screenshots.py --all      regenerate every screenshot
  python3 scripts/generate_screenshots.py soft-chat  one theme
"""
import argparse
import html
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from preview_theme import parse_theme  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
REAL = ROOT / "screenshots" / "warp"
OUT = ROOT / "screenshots" / "generated"
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]
WIDTH, HEIGHT = 1000, 620


def find_chrome():
    override = os.environ.get("CHROME")
    if override and shutil.which(override) or (override and pathlib.Path(override).exists()):
        return override
    for path in CHROME_PATHS:
        if pathlib.Path(path).exists():
            return path
    for name in ("google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def span(color, text, bold=False):
    weight = "font-weight:600;" if bold else ""
    return f'<span style="color:{color};{weight}">{html.escape(text)}</span>'


def page(theme):
    n, b = theme["normal"], theme["bright"]
    fg, accent, bg = theme["foreground"], theme["accent"], theme["background"]
    chip = "".join(f'<i style="background:{n[c]}"></i>' for c in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"))
    chip += "".join(f'<i style="background:{b[c]}"></i>' for c in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"))
    lines = [
        span(accent, "user@host", True) + span(fg, ":") + span(n["blue"], "~/project", True) + span(fg, "$ ls -la"),
        span(n["blue"], "src/") + span(fg, "        ") + span(n["green"], "build.sh*") + span(fg, "        README.md"),
        span(n["red"], "error:", True) + span(fg, " cannot find module 'config'"),
        span(n["yellow"], "warning:", True) + span(fg, " deprecated option 'legacy'"),
        span(fg, "On branch main  ") + span(n["green"], "modified:") + span(fg, " src/app.py"),
        span(n["magenta"], "#") + span(fg, " ") + span(n["cyan"], "cyan") + span(fg, " ") + span(b["magenta"], "bright magenta") + span(fg, " ") + span(accent, "accent"),
    ]
    body = "".join(f"<div>{line}</div>" for line in lines)
    return f"""<!doctype html>
<meta charset="utf-8">
<style>
  html, body {{ margin: 0; width: {WIDTH}px; height: {HEIGHT}px; background: {bg}; }}
  .window {{ width: 100%; height: 100%; display: flex; flex-direction: column; }}
  .bar {{ display: flex; justify-content: space-between; padding: 12px 16px;
    border-bottom: 1px solid {b['black']}; color: {b['black']};
    font: 14px ui-monospace, Menlo, monospace; }}
  .log {{ padding: 22px 26px; font: 17px/1.7 ui-monospace, Menlo, "IBM Plex Mono", monospace;
    color: {fg}; white-space: pre; flex: 1; }}
  .swatches {{ display: flex; gap: 4px; padding: 0 26px 18px; }}
  .swatches i {{ width: 26px; height: 26px; border-radius: 5px; display: block; }}
  .note {{ padding: 0 26px 16px; color: {b['black']}; font: 13px ui-monospace, Menlo, monospace; }}
</style>
<div class="window">
  <div class="bar"><span>Termies · {html.escape(theme['name'])}</span><span>generated mockup</span></div>
  <div class="log">{body}</div>
  <div class="swatches">{chip}</div>
  <div class="note">Drawn from the theme palette. Not a capture of the Warp app.</div>
</div>
"""


def render(chrome, html_text, out_png):
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "theme.html"
        src.write_text(html_text, encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={out_png}", src.as_uri()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not out_png.exists():
        raise RuntimeError(f"Chrome did not write {out_png.name}")


def compress(png):
    oxipng = shutil.which("oxipng")
    if oxipng:
        subprocess.run([oxipng, "-o", "4", "--quiet", str(png)], check=False)


def main():
    parser = argparse.ArgumentParser(description="Generate theme screenshots.")
    parser.add_argument("names", nargs="*", help="theme names (default: all)")
    parser.add_argument("--all", action="store_true", help="regenerate even if a screenshot exists")
    args = parser.parse_args()

    chrome = find_chrome()
    if not chrome:
        print("Google Chrome was not found. Install it, or set CHROME to a Chromium-based browser.", file=sys.stderr)
        return 1

    names = args.names or [f.stem for f in sorted(THEMES.glob("*.yaml"))]
    OUT.mkdir(parents=True, exist_ok=True)
    made = skipped = 0
    for name in names:
        path = THEMES / f"{name}.yaml"
        if not path.exists():
            print(f"No theme named '{name}'.", file=sys.stderr)
            return 1
        if (REAL / f"{name}.png").exists():
            skipped += 1
            continue
        out_png = OUT / f"{name}.png"
        if out_png.exists() and not args.all:
            skipped += 1
            continue
        theme = parse_theme(path)
        render(chrome, page(theme), out_png)
        compress(out_png)
        made += 1
        print(f"Wrote screenshots/generated/{name}.png")
    print(f"Done: {made} generated, {skipped} skipped (a real or existing screenshot is already there).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
