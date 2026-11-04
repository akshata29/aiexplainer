"""Text measurement with the real Excalidraw font advance widths.

Diagrams are laid out in Python *before* Excalidraw sees them, so we must predict how wide the browser will
render a string. `font_metrics.json` (built by tools/build_font_metrics.py) holds glyph advances for the fonts
Excalidraw ships. Excalifont (id 5) is the default hand-drawn face and has NO arrow/check/inequality glyphs, so
`sanitize()` rewrites those to ASCII and reports anything else that would fall back to a system font.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = json.loads(Path(__file__).with_name("font_metrics.json").read_text(encoding="utf-8"))
_ADV: dict[int, dict[int, int]] = {
    int(fid): {int(cp): adv for cp, adv in d["advance"].items()} for fid, d in _DATA.items()
}

HAND = 5   # Excalifont  - default hand-drawn font (proportional)
MONO = 8   # Comic Shanns - monospaced hand-drawn (good for identifiers/URLs/code)
CODE = 3   # Cascadia Code - monospaced
VIRGIL = 1
NUNITO = 6

# unsupported glyph -> ASCII replacement
REPLACEMENTS = {
    "\u2192": "->", "\u2190": "<-", "\u2194": "<->", "\u21d2": "=>", "\u27f6": "->", "\u2191": "^", "\u2193": "v",
    "\u2265": ">=", "\u2264": "<=", "\u2248": "~", "\u2260": "!=", "\u2713": "+", "\u2714": "+", "\u2717": "x",
    "\u2718": "x", "\u26a0": "(!)", "\u2605": "*", "\u2606": "*", "\u25cf": "*", "\u25cb": "o", "\u25a0": "#",
    "\u25a1": "[ ]", "\u25b6": ">", "\u25c0": "<", "\u2192": "->", "\u00a7": "S", "\u2021": "+", "\u00b9": "1",
    "\u00b2": "2", "\u00b3": "3", "\u00b5": "u", "\u2011": "-", "\u2212": "-", "\u00a0": " ", "\u200b": "",
    "\u2192": "->", "\u21c4": "<->", "\u2194": "<->", "\u2022": "\u2022",
}


def _adv_table(font: int) -> dict[int, int]:
    return _ADV.get(font) or _ADV[HAND]


def sanitize(text: str, font: int = HAND) -> tuple[str, set[str]]:
    """Replace glyphs the font lacks with ASCII; return (clean_text, still_unsupported_chars)."""
    table = _adv_table(font)
    out: list[str] = []
    bad: set[str] = set()
    for ch in text:
        if ch == "\n" or ord(ch) in table:
            out.append(ch)
        elif ch in REPLACEMENTS:
            out.append(REPLACEMENTS[ch])
        else:
            bad.add(ch)
            out.append(ch)
    return "".join(out), bad


@lru_cache(maxsize=None)
def _info(font: int) -> tuple[float, float, float]:
    d = _DATA.get(str(font)) or _DATA[str(HAND)]
    return d["unitsPerEm"], d["avg"], d["lineHeight"]


def line_ratio(font: int = HAND) -> float:
    return _info(font)[2]


def char_em(ch: str, font: int = HAND) -> float:
    units, avg, _ = _info(font)
    return _adv_table(font).get(ord(ch), avg) / units


def line_width(line: str, size: float, font: int = HAND) -> float:
    return sum(char_em(ch, font) for ch in line) * size


def text_size(text: str, size: float, font: int = HAND) -> tuple[float, float]:
    """(width, height) of a possibly multi-line string as Excalidraw would size it."""
    lines = text.split("\n")
    w = max((line_width(l, size, font) for l in lines), default=0.0)
    h = len(lines) * size * line_ratio(font)
    return w, h


def _hard_break(token: str, max_w: float, size: float, font: int) -> list[str]:
    """Split an over-long token, preferring to break after / . - _ : (identifiers, URLs) over mid-word."""
    pieces: list[str] = []
    rest = token
    while line_width(rest, size, font) > max_w and len(rest) > 1:
        cut = 0
        width = 0.0
        last_soft = 0
        for i, ch in enumerate(rest):
            width += char_em(ch, font) * size
            if width > max_w:
                break
            cut = i + 1
            if ch in "/.-_:,":
                last_soft = i + 1
        if last_soft >= max(3, cut * 0.45):
            cut = last_soft
        cut = max(cut, 1)
        pieces.append(rest[:cut])
        rest = rest[cut:]
    pieces.append(rest)
    return pieces


def wrap_text(text: str, max_w: float, size: float, font: int = HAND) -> list[str]:
    """Greedy word wrap. Honors explicit newlines; breaks words wider than max_w at / . - _ when possible."""
    out: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if line_width(trial, size, font) <= max_w:
                cur = trial
                continue
            if cur:
                out.append(cur)
            if line_width(word, size, font) > max_w:
                parts = _hard_break(word, max_w, size, font)
                out.extend(parts[:-1])
                cur = parts[-1]
            else:
                cur = word
        out.append(cur)
    return out
