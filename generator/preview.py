"""Quick visual check for one diagram: build -> render the overview PNG (and optionally a few detail tiles).

    python -m generator.preview resource-model                      # overview PNG -> diagrams/previews/work/<id>.png + tile-grid hint
    python -m generator.preview resource-model --tiles r1c1,r2c2    # also write just those full-resolution tiles
    python -m generator.preview resource-model --max-side 2600      # larger overview

Renders are serialized machine-wide (one browser at a time). View the PNGs with an image viewer (agents: `view` tool).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from . import build

ROOT = Path(__file__).resolve().parents[1]
VALUE_OPTIONS = {"--tiles", "--max-side", "--scale", "--tile", "--out"}


def main(argv: list[str]) -> int:
    ids: list[str] = []
    extra: list[str] = []
    it = iter(argv)
    for a in it:
        if a in VALUE_OPTIONS:
            extra += [a, next(it, "")]
        elif a.startswith("-"):
            extra.append(a)
        else:
            ids.append(a)
    if not ids:
        print(__doc__)
        return 2
    rc = build.main(ids)
    if rc:
        return rc
    ids_to_render = []
    want = {i.replace("-", "_") for i in ids}
    for p in sorted((ROOT / "generator" / "diagrams").glob("*.py")):
        if p.stem.replace("-", "_") in want:
            mod = build._load(p)
            ids_to_render.append(dict(mod.META).get("id", p.stem))
    cmd = ["node", str(ROOT / "tools" / "render.mjs"), "--only", ",".join(ids_to_render), *extra]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
