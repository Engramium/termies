#!/usr/bin/env python3
"""Build the preview pages from the palette files in themes/.

Writes:
  preview/theme-picker.html    interactive picker, with a card for every theme
  preview/theme-overview.html  one static grid of every theme, for the README image

Take the screenshots afterwards (see README.md); this script only
writes the HTML, so it runs without a browser.

Usage:
  python3 scripts/build_preview.py           write both pages
  python3 scripts/build_preview.py --check   fail if the committed pages are out of date

Requires PyYAML.
"""
import argparse
import html
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from palette import contrast, neutrals  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
PREVIEW = ROOT / "preview"
PICKER = PREVIEW / "theme-picker.html"
OVERVIEW = PREVIEW / "theme-overview.html"

# Family order and display: (family key, dark slug, light slug, dusk slug, note, card style).
# Card style: "bubbles" (chat bubbles), "thread" (role labels), "prompt" (one prompt line).
FAMILIES = [
    ("Soft Chat", "soft-chat", "soft-chat-light", "soft-chat-dusk",
     "Chat-style, closest to Claude and ChatGPT. Steel-blue accent.", "bubbles"),
    ("Ember Chat", "ember-chat", "ember-chat-light", "ember-chat-dusk",
     "Warm dark with an ember accent.", "bubbles"),
    ("Quiet Ink", "quiet-ink", "quiet-ink-light", "quiet-ink-dusk",
     "Terminal first. One amber accent on near black.", "prompt"),
    ("Calm Focus", "calm-focus", "calm-focus-light", "calm-focus-dusk",
     "Quiet slate, the all-day default.", "prompt"),
    ("Ink Mono", "ink-mono", "ink-mono-light", "ink-mono-dusk",
     "Almost grayscale, one amber accent.", "prompt"),
    ("Forest Dim", "forest-dim", "forest-dim-light", "forest-dim-dusk",
     "Dark green with sage accents, for long sessions.", "bubbles"),
    ("Violet", "violet-night", "violet-day", "violet-dusk",
     "Purple-accented, with a palette inspired by Dracula.", "bubbles"),
    ("Paper", "paper-dark", "paper-light", "paper-dusk",
     "Warm off-white and warm dark.", "thread"),
    ("Thread", "thread-dark", "paper-thread", "thread-dusk",
     "Document-like, with a role label on each turn.", "thread"),
    ("Sunrise", "sunrise", "sunrise-day", None,
     "Energizing: warm orange accent for focus and comfort.", "bubbles"),
    ("Contrast", "contrast-night", "contrast-day", None,
     "High Contrast, at least 7:1 text contrast.", "prompt"),
    ("Safe Harbor", "safe-harbor", "safe-harbor-light", None,
     "Colorblind-safe: errors and diffs stay distinct for color vision differences.", "bubbles"),
    ("Atlas", "atlas-dark", "atlas-light", None,
     "Classic, in the style of the One Dark and One Light palettes.", "prompt"),
    ("Agent", "agent-night", None, None,
     "Dark teal-green, with an accent color for prompts and output.", "prompt"),
    ("Agent Navy", "agent-navy", None, None,
     "Deep navy with a green prompt, measured from a terminal screenshot.", "prompt"),
    ("Plum Night", "plum-night", None, None,
     "Plum purple with an orange cursor, measured from a terminal screenshot.", "prompt"),
    ("Plum Deep", "plum-deep", None, None,
     "Deep plum with a light text color, measured from a terminal screenshot.", "prompt"),
]


# Mood tags per family (feature 2). Dark themes also get "low light" and light themes
# get "bright", based on their mode. Dusk versions inherit their family's tags.
FAMILY_MOODS = {
    "Soft Chat": ["calm"], "Ember Chat": ["calm", "warm"], "Quiet Ink": ["minimal"],
    "Calm Focus": ["calm", "minimal"], "Ink Mono": ["minimal"], "Forest Dim": ["calm"],
    "Violet": ["calm"], "Paper": ["calm", "warm"], "Thread": ["calm"],
    "Sunrise": ["energizing", "warm"], "Contrast": ["minimal"], "Safe Harbor": ["calm"],
    "Atlas": ["minimal"], "Agent": ["calm"], "Agent Navy": ["calm"],
    "Plum Night": ["calm", "warm"], "Plum Deep": ["calm"],
}


def load(slug):
    return yaml.safe_load((THEMES / f"{slug}.yaml").read_text(encoding="utf-8"))


COLORED_ANSI = ["red", "green", "yellow", "blue", "magenta", "cyan"]


def contrast_report(theme):
    """Text contrast and the weakest colored ANSI color, for the accessibility report (feature 3)."""
    bg, fg = theme["background"], theme["foreground"]
    worst_name, worst = None, None
    for group in ("normal", "bright"):
        for color in COLORED_ANSI:
            ratio = contrast(theme["terminal_colors"][group][color], bg)
            if worst is None or ratio < worst:
                worst, worst_name = ratio, f"{group} {color}"
    return {
        "text": round(contrast(fg, bg), 2),
        "ansi_min": round(worst, 2),
        "ansi_min_name": worst_name,
    }


def card_data(theme_id, name, mode, note, style, theme, tags):
    n = neutrals(theme)
    normal = theme["terminal_colors"]["normal"]
    return {
        "id": theme_id,
        "tags": tags + (["low light"] if mode == "dark" else ["bright"]),
        "contrast": contrast_report(theme),
        "name": name,
        "mode": mode,
        "style": style,
        "note": note,
        "bg": theme["background"],
        "fg": theme["foreground"],
        "muted": n["subtext0"],
        "line": n["overlay0"],
        "accent": theme["accent"],
        "userBg": n["surface0"],
        "codeBg": n["mantle"],
        "ok": normal["green"],
        "inputBg": n["surface0"] if mode == "dark" else "#FFFFFF",
        "inputRadius": "4px" if style == "prompt" else "999px",
        "swatches": [theme["background"], n["surface0"], theme["foreground"],
                     theme["accent"], normal["green"]],
    }


def all_cards():
    """Every theme as a card, grouped by family: dark, then Dusk, then light."""
    cards = []
    for family, dark_slug, light_slug, dusk_slug, note, style in FAMILIES:
        dark = load(dark_slug)
        cards.append(card_data(dark_slug, dark["name"], "dark", note, style, dark, FAMILY_MOODS[family]))
        if dusk_slug:
            dusk = load(dusk_slug)
            cards.append(card_data(dusk_slug, dusk["name"], "dark",
                                   f"Middle mood between {family} dark and light.", style, dusk, FAMILY_MOODS[family]))
        if light_slug:
            light = load(light_slug)
            cards.append(card_data(light_slug, light["name"], "light", note, style, light, FAMILY_MOODS[family]))
    return cards


def replace_once(text, pattern, replacement):
    new, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"could not find the expected block in preview/theme-picker.html: {pattern[:40]}")
    return new


def build_picker(cards):
    template = PICKER.read_text(encoding="utf-8")
    block = "const THEMES = " + json.dumps(cards, indent=2, ensure_ascii=False) + ";"
    return replace_once(template, r"const THEMES = \[.*?\n\];", block)


def build_overview(cards):
    """A compact static grid: one row per family (dark, dusk, light)."""
    rows = []
    by_id = {c["id"]: c for c in cards}
    for family, dark_slug, light_slug, dusk_slug, note, _style in FAMILIES:
        cells = [dark_slug] + ([dusk_slug] if dusk_slug else [None]) + [light_slug]
        tds = []
        for slug in cells:
            if slug is None:
                tds.append('<div class="cell empty">no version here</div>')
                continue
            c = by_id[slug]
            strip = "".join(f'<i style="background:{s}"></i>' for s in c["swatches"])
            tds.append(
                f'<div class="cell" style="background:{c["bg"]};color:{c["fg"]};border-color:{c["line"]}">'
                f'<div class="cname">{html.escape(c["name"])}</div>'
                f'<div class="sample"><span style="color:{c["accent"]}">›</span> '
                f'Why does order 956 still show a payout?</div>'
                f'<div class="strip">{strip}</div></div>'
            )
        rows.append(
            f'<div class="row"><div class="fam"><b>{html.escape(family)}</b>'
            f'<span>{html.escape(note)}</span></div>{"".join(tds)}</div>'
        )
    return f"""<!doctype html>
<meta name="claude:viewport-fit-sides" content="cover">
<title>Termies Theme Overview</title>
<style>
  body {{ margin: 0; background: #F4F2ED; color: #23262D;
    font: 14px/1.4 "Newsreader", Georgia, serif; padding: 32px; }}
  h1 {{ font-weight: 500; font-size: 28px; margin: 0 0 4px; }}
  .sub {{ color: #6B707B; margin: 0 0 20px; }}
  .head, .row {{ display: grid; grid-template-columns: 240px repeat(3, 1fr); gap: 12px; }}
  .head div {{ font: 12px "IBM Plex Mono", ui-monospace, Menlo, monospace; color: #6B707B;
    text-transform: uppercase; letter-spacing: .06em; padding: 0 0 6px; }}
  .row {{ margin-bottom: 14px; align-items: stretch; }}
  .fam b {{ display: block; font-size: 17px; font-weight: 500; }}
  .fam span {{ color: #6B707B; font-size: 13px; }}
  .cell {{ border: 1px solid; border-radius: 10px; padding: 12px; min-height: 120px;
    display: flex; flex-direction: column; gap: 8px; }}
  .cell.empty {{ background: transparent; border: 1px dashed #C9C5BB; color: #8A8E98;
    align-items: center; justify-content: center; font-style: italic; }}
  .cname {{ font: 12px "IBM Plex Mono", ui-monospace, Menlo, monospace; opacity: .8; }}
  .sample {{ font: 13px/1.4 "IBM Plex Mono", ui-monospace, Menlo, monospace; }}
  .strip {{ display: flex; gap: 4px; margin-top: auto; }}
  .strip i {{ width: 16px; height: 16px; border-radius: 4px; display: block; }}
</style>
<h1>Termies Warp themes</h1>
<p class="sub">{len(cards)} themes in {len(FAMILIES)} families. Dark, middle (Dusk), and light.</p>
<div class="head"><div>Family</div><div>Dark</div><div>Dusk (middle)</div><div>Light</div></div>
{"".join(rows)}
"""


def main():
    parser = argparse.ArgumentParser(description="Build the theme preview pages.")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the committed pages differ from what would be built")
    args = parser.parse_args()

    cards = all_cards()
    outputs = {PICKER: build_picker(cards), OVERVIEW: build_overview(cards)}

    if args.check:
        stale = [p.relative_to(ROOT).as_posix() for p, text in outputs.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("Out of date (run scripts/build_preview.py):")
            for s in stale:
                print(f"  {s}")
            return 1
        print(f"Preview pages are up to date ({len(cards)} themes).")
        return 0

    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)} ({len(cards)} themes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
