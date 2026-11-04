"""Dump the text of a diagram in rough reading order (for proofreading / fact-checking).

    python tools/dump_text.py resource-model            # one diagram
    python tools/dump_text.py --all > all-text.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "diagrams"


def dump(path: Path) -> str:
    scene = json.loads(path.read_text(encoding="utf-8"))
    texts = [e for e in scene["elements"] if e["type"] == "text" and e.get("text", "").strip()]
    # rows of ~40px so left-to-right text on the same visual line stays together
    texts.sort(key=lambda e: (round(e["y"] / 40), e["x"]))
    out = [f"=== {path.stem}  ({len(texts)} text elements)"]
    last_row = None
    for e in texts:
        row = round(e["y"] / 40)
        if last_row is not None and row != last_row:
            out.append("")
        last_row = row
        t = e["text"].replace("\n", " ")
        link = f"  <{e['link']}>" if e.get("link") else ""
        out.append(f"[{int(e['x'])},{int(e['y'])} {e['fontSize']:g}px] {t}{link}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if "--all" in argv:
        files = sorted(p for p in DIAGRAMS.glob("*.excalidraw") if not p.name.startswith("_"))
    else:
        files = [DIAGRAMS / f"{a}.excalidraw" for a in argv if not a.startswith("-")]
    sys.stdout.reconfigure(encoding="utf-8")
    for f in files:
        print(dump(f))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
