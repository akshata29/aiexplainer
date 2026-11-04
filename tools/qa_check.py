"""Static layout QA for generated diagrams - no browser, very cheap.

    python tools/qa_check.py                 # all diagrams, summary table
    python tools/qa_check.py ra-basic-chat   # one diagram, with details

Checks
  overflow  text whose box sticks out of the smallest rectangle/ellipse/diamond that contains its centre
  overlap   two text boxes that overlap by > 25 % of the smaller one
  crossed   arrow/line segments that pass through the middle of a text box
  tiny      text smaller than 11.5 px
  links     number of clickable citation links; sources panel present
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator.xd import metrics  # noqa: E402

DIAGRAMS = ROOT / "diagrams"


def bbox(e: dict) -> tuple[float, float, float, float]:
    if e["type"] in ("line", "arrow") and e.get("points"):
        xs = [e["x"] + p[0] for p in e["points"]]
        ys = [e["y"] + p[1] for p in e["points"]]
        return min(xs), min(ys), max(xs), max(ys)
    return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]


def ink_bbox(t: dict) -> tuple[float, float, float, float]:
    """Box around the glyphs actually drawn: element boxes can be wider than the text (alignment width)."""
    font = t.get("fontFamily", 5)
    text = t.get("text", "")
    w, h = metrics.text_size(text, t["fontSize"], font if font in (1, 3, 5, 6, 8) else 5)
    x0, x1 = t["x"], t["x"] + t["width"]
    align = t.get("textAlign", "left")
    if align == "center":
        cx = (x0 + x1) / 2
        return cx - w / 2, t["y"], cx + w / 2, t["y"] + h
    if align == "right":
        return x1 - w, t["y"], x1, t["y"] + h
    return x0, t["y"], x0 + w, t["y"] + h


def seg_hits_box(p1, p2, box, shrink=0.28) -> bool:
    """Does segment p1-p2 pass through the central part of box (box shrunk by `shrink` on each side)?"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    x0, x1 = x0 + w * shrink, x1 - w * shrink
    y0, y1 = y0 + h * shrink, y1 - h * shrink
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p1[0] - x0), (dx, x1 - p1[0]), (-dy, p1[1] - y0), (dy, y1 - p1[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def analyse(path: Path, detail: bool = False) -> dict:
    scene = json.loads(path.read_text(encoding="utf-8"))
    els = [e for e in scene["elements"] if not e.get("isDeleted")]
    texts = [e for e in els if e["type"] == "text" and e.get("text", "").strip()]
    shapes = [e for e in els if e["type"] in ("rectangle", "ellipse", "diamond") and e["width"] > 24 and e["height"] > 14
              and not (e["backgroundColor"] == "transparent" and e["strokeColor"] == "transparent")]
    shapes_sorted = sorted(shapes, key=lambda s: s["width"] * s["height"])

    overflow, overlap, crossed, tiny = [], [], [], []
    for t in texts:
        tb = ink_bbox(t)
        if t["fontSize"] < 11.5:
            tiny.append(t)
        cx, cy = (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2
        for s in shapes_sorted:
            sx0, sy0, sx1, sy1 = bbox(s)
            if sx0 <= cx <= sx1 and sy0 <= cy <= sy1:
                esc_x = max(sx0 - tb[0], tb[2] - sx1, 0)
                esc_y = max(sy0 - tb[1], tb[3] - sy1, 0)
                if esc_x > 3 or esc_y > 3:
                    overflow.append((t, s, esc_x, esc_y))
                break

    boxes = sorted(((ink_bbox(t), t) for t in texts), key=lambda b: b[0][0])
    for i, (a, ta) in enumerate(boxes):
        for j in range(i + 1, len(boxes)):
            b, tb_ = boxes[j]
            if b[0] > a[2]:
                break
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 2 and oy > 2:
                small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if small > 0 and ox * oy / small > 0.25:
                    overlap.append((ta, tb_, ox * oy / small))

    text_boxes = [(ink_bbox(t), t) for t in texts]
    for e in els:
        if e["type"] not in ("arrow", "line") or len(e.get("points", [])) < 2:
            continue
        if e.get("roundness") and len(e["points"]) > 2:
            continue  # smoothed curve: the control polygon is not the drawn path, so skip it
        pts = [(e["x"] + p[0], e["y"] + p[1]) for p in e["points"]]
        for p1, p2 in zip(pts, pts[1:]):
            if abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) < 30:
                continue
            minx, maxx = min(p1[0], p2[0]), max(p1[0], p2[0])
            miny, maxy = min(p1[1], p2[1]), max(p1[1], p2[1])
            for tbx, t in text_boxes:
                if tbx[2] < minx or tbx[0] > maxx or tbx[3] < miny or tbx[1] > maxy:
                    continue
                if seg_hits_box(p1, p2, tbx):
                    crossed.append((e, t))
                    break

    links = [e for e in els if e.get("link")]
    xs0 = min(bbox(e)[0] for e in els) if els else 0
    xs1 = max(bbox(e)[2] for e in els) if els else 0
    ys0 = min(bbox(e)[1] for e in els) if els else 0
    ys1 = max(bbox(e)[3] for e in els) if els else 0
    res = {
        "id": path.stem, "elements": len(els), "w": round(xs1 - xs0), "h": round(ys1 - ys0), "texts": len(texts),
        "overflow": len(overflow), "overlap": len(overlap), "crossed": len(crossed), "tiny": len(tiny),
        "links": len(links), "has_sources": any("Sources and further reading" in t["text"] for t in texts),
    }
    if detail:
        def snip(t):
            return f"({int(t['x'])},{int(t['y'])}) {t['text'][:50]!r}"
        res["overflow_d"] = [f"{snip(t)} escapes by x={ex:.0f} y={ey:.0f}" for t, s, ex, ey in overflow[:25]]
        res["overlap_d"] = [f"{snip(a)}  X  {snip(b)} ({r:.0%})" for a, b, r in overlap[:25]]
        res["crossed_d"] = [f"arrow@({int(e['x'])},{int(e['y'])}) through {snip(t)}" for e, t in crossed[:25]]
        res["tiny_d"] = [snip(t) + f" {t['fontSize']}px" for t in tiny[:10]]
    return res


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ids = [a for a in argv if not a.startswith("-")]
    files = [DIAGRAMS / f"{i}.excalidraw" for i in ids] if ids else sorted(
        p for p in DIAGRAMS.glob("*.excalidraw") if not p.name.startswith("_"))
    detail = bool(ids)
    rows = [analyse(f, detail) for f in files]
    if detail:
        for r in rows:
            print(f"== {r['id']}: {r['elements']} elements {r['w']}x{r['h']}  overflow={r['overflow']} "
                  f"overlap={r['overlap']} crossed={r['crossed']} tiny={r['tiny']} links={r['links']} "
                  f"sources={r['has_sources']}")
            for k in ("overflow_d", "overlap_d", "crossed_d", "tiny_d"):
                for line in r.get(k, []):
                    print(f"   [{k[:-2]}] {line}")
        return 0
    print(f"{'diagram':<36}{'elems':>6}{'w':>6}{'h':>7}{'ovfl':>6}{'ovlp':>6}{'xed':>5}{'tiny':>5}{'links':>6} src")
    for r in rows:
        flag = "  <-- check" if r["overflow"] + r["overlap"] > 8 else ""
        print(f"{r['id']:<36}{r['elements']:>6}{r['w']:>6}{r['h']:>7}{r['overflow']:>6}{r['overlap']:>6}{r['crossed']:>5}"
              f"{r['tiny']:>5}{r['links']:>6} {'Y' if r['has_sources'] else '-'}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
