"""Build Excalidraw diagrams from generator/diagrams/*.py

    python -m generator.build                 # build everything + manifest
    python -m generator.build agent-service   # build one or more ids only (no manifest write)
    python -m generator.build --list

Each diagram module defines META (dict) and build(cv). See generator/README.md.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path

from .sections import SECTIONS
from .xd import Canvas, footer

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "generator" / "diagrams"
OUT = ROOT / "diagrams"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"gen_diagram_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def build_one(path: Path) -> dict:
    mod = _load(path)
    meta = dict(mod.META)
    meta.setdefault("id", path.stem)
    cv = Canvas(meta["id"])
    cv.meta = meta
    mod.build(cv)
    auto_links = 0
    if meta.get("auto_sources", True):
        try:
            from .autosrc import add_auto_sources
            auto_links = add_auto_sources(cv)
        except Exception as exc:  # never let the fallback break a build
            cv.warn(f"auto sources panel failed: {exc}")
    minx, miny, maxx, maxy = cv.bounds()
    if not getattr(cv, "footer_done", False) and meta.get("footer", True):
        footer(cv, minx, maxy + 50)
        minx, miny, maxx, maxy = cv.bounds()
    problems = cv.validate()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{meta['id']}.excalidraw"
    cv.save(out)
    n = len([e for e in cv._els if e])
    meta.update({"file": f"{meta['id']}.excalidraw", "width": round(maxx - minx), "height": round(maxy - miny),
                 "elements": n, "updated": cv.updated_label, "preview": f"previews/{meta['id']}.png",
                 "auto_sources": auto_links})
    return {"meta": meta, "problems": problems, "path": out}


def main(argv: list[str]) -> int:
    ids = [a for a in argv if not a.startswith("-")]
    files = sorted(SRC.glob("*.py"))
    if not ids:
        files = [p for p in files if not p.name.startswith("_")]
    if "--list" in argv:
        for p in files:
            print(p.stem)
        return 0
    if ids:
        want = {i.replace("-", "_") for i in ids}
        files = [p for p in files if p.stem.replace("-", "_") in want]
        if not files:
            print(f"no diagram module matches {ids} (module file must be generator/diagrams/<id with underscores>.py)",
                  file=sys.stderr)
            return 2
    failed = 0
    for p in files:
        t0 = time.time()
        try:
            res = build_one(p)
        except Exception:
            failed += 1
            print(f"[FAIL] {p.stem}")
            traceback.print_exc()
            continue
        meta = res["meta"]
        auto = f"  (auto sources panel: {meta['auto_sources']} links)" if meta.get("auto_sources") else ""
        print(f"[ok]   {meta['id']:<34} {meta['elements']:>5} elements  {meta['width']}x{meta['height']}  "
              f"({time.time() - t0:.1f}s){auto}")
        for prob in res["problems"]:
            print(f"       ! {prob}")
    if not ids or "--manifest" in argv:
        _write_manifest()
    return 1 if failed else 0


def _write_manifest() -> None:
    """Manifest is derived from the .excalidraw files + META of every module (not just the ones just built)."""
    entries = []
    for p in sorted(SRC.glob("*.py")):
        if p.name.startswith("_"):
            continue
        meta = dict(_load(p).META)
        meta.setdefault("id", p.stem)
        f = OUT / f"{meta['id']}.excalidraw"
        if not f.exists():
            continue
        scene = json.loads(f.read_text(encoding="utf-8"))
        xs0, ys0, xs1, ys1 = [], [], [], []
        for e in scene["elements"]:
            if e["type"] in ("line", "arrow"):
                px = [e["x"] + q[0] for q in e["points"]]
                py = [e["y"] + q[1] for q in e["points"]]
                xs0.append(min(px)), xs1.append(max(px)), ys0.append(min(py)), ys1.append(max(py))
            else:
                xs0.append(e["x"]), ys0.append(e["y"]), xs1.append(e["x"] + e["width"]), ys1.append(e["y"] + e["height"])
        meta.update({"file": f.name, "width": round(max(xs1) - min(xs0)), "height": round(max(ys1) - min(ys0)),
                     "elements": len(scene["elements"]), "preview": f"previews/{meta['id']}.png"})
        entries.append(meta)
    entries.sort(key=lambda m: (str(m.get("section", "9")), m.get("order", 999), m["id"]))
    manifest = {"generated": time.strftime("%Y-%m-%d"),
                "sections": {k: {"title": v[0], "blurb": v[1]} for k, v in SECTIONS.items()},
                "diagrams": entries}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"manifest: {len(entries)} diagrams")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
