"""Extract per-glyph advance widths from the Excalidraw font files.

The Python diagram kit lays text out *before* Excalidraw ever sees it, so it needs the same glyph
widths the browser will use. This script reads the woff2 chunks shipped in
`node_modules/@excalidraw/excalidraw/dist/prod/fonts` and writes `generator/xd/font_metrics.json`.

Run once after `npm install`:  python tools/build_font_metrics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "node_modules" / "@excalidraw" / "excalidraw" / "dist" / "prod" / "fonts"
OUT = ROOT / "generator" / "xd" / "font_metrics.json"

# Excalidraw fontFamily ids -> (folder, display name, line-height ratio used by Excalidraw)
FAMILIES = {
    1: ("Virgil", "Virgil", 1.25),
    3: ("Cascadia", "Cascadia", 1.2),
    5: ("Excalifont", "Excalifont", 1.25),
    6: ("Nunito", "Nunito", 1.35),
    8: ("ComicShanns", "Comic Shanns", 1.25),
}


def main() -> int:
    if not FONT_DIR.exists():
        print(f"font dir not found: {FONT_DIR} (run npm install first)", file=sys.stderr)
        return 1
    result: dict[str, dict] = {}
    for fid, (folder, name, line_height) in FAMILIES.items():
        advances: dict[int, int] = {}
        units = None
        for path in sorted((FONT_DIR / folder).glob("*.woff2")):
            font = TTFont(path)
            units = units or font["head"].unitsPerEm
            cmap = font.getBestCmap() or {}
            hmtx = font["hmtx"].metrics
            for cp, glyph in cmap.items():
                if glyph in hmtx:
                    advances[cp] = hmtx[glyph][0]
        if not advances or not units:
            print(f"no glyphs for {name}", file=sys.stderr)
            continue
        # average advance of lowercase ascii = fallback for unknown glyphs
        sample = [advances[c] for c in range(ord("a"), ord("z") + 1) if c in advances]
        avg = sum(sample) / len(sample)
        result[str(fid)] = {
            "name": name,
            "unitsPerEm": units,
            "lineHeight": line_height,
            "avg": avg,
            "advance": {str(k): v for k, v in sorted(advances.items())},
        }
        print(f"{name:12s} glyphs={len(advances):5d} unitsPerEm={units} avg={avg / units:.3f}em")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
