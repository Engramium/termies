"""Shared color helpers and the layered neutral system (feature F1).

Used by the exporters and the validator. Standard library only.

Layered neutrals give every theme the same tiers, so UI pieces (chat bubbles,
borders, selections, dim text) get consistent levels in every export:

  mantle, base, crust          the page layers, darkest to lightest on dark themes
  surface0..2                  raised areas: bubbles, selections, hovers
  overlay0..2                  borders and quiet UI, moving from bg toward text
  subtext0..1, text            secondary text, then main text
"""
import re

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def to_rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def mix(a, b, t):
    """Blend a toward b by fraction t. A negative t moves a away from b."""
    ra, rb = to_rgb(a), to_rgb(b)
    return to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def luminance(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def is_dark(hex_color):
    return luminance(hex_color) < 0.18


def neutrals(theme):
    """The 12 layered neutrals for one theme, from its background and text colors.

    Tiers move toward the text color, so a dark theme's surfaces get lighter as they
    rise, and a light theme's surfaces get darker. Mantle and crust sit below the
    base on dark themes and below it on light themes too, so the page layers stay
    in order.
    """
    bg, fg = theme["background"], theme["foreground"]
    if is_dark(bg):
        mantle, crust = mix(bg, fg, -0.04), mix(bg, fg, -0.08)
    else:
        mantle, crust = mix(bg, fg, 0.02), mix(bg, fg, 0.05)
    return {
        "crust": crust,
        "mantle": mantle,
        "base": bg,
        "surface0": mix(bg, fg, 0.08),
        "surface1": mix(bg, fg, 0.14),
        "surface2": mix(bg, fg, 0.20),
        "overlay0": mix(bg, fg, 0.30),
        "overlay1": mix(bg, fg, 0.42),
        "overlay2": mix(bg, fg, 0.54),
        "subtext0": mix(fg, bg, 0.25),
        "subtext1": mix(fg, bg, 0.12),
        "text": fg,
    }
