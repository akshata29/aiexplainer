"""Core canvas: builds Excalidraw scene JSON (version 2 files) with deterministic ids/seeds.

Everything here is intentionally low level. Authors normally use the higher level blocks in `blocks.py`
(Card, Table, Chip, Note ...) and the connectors / sequence helpers in `flows.py`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional, Sequence

from . import metrics
from .palette import INK, WHITE, Theme, theme as get_theme

Point = tuple[float, float]
ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _r(v: float) -> float:
    return round(float(v), 2)


def _frac_keys(n: int) -> list[str]:
    """n ascending valid fractional-index keys (what Excalidraw stores in element.index)."""
    keys: list[str] = []
    length = 1  # digits after head
    head = ord("a")
    while len(keys) < n:
        count = 62 ** length
        for i in range(min(count, n - len(keys))):
            digits, v = [], i
            for _ in range(length):
                digits.append(BASE62[v % 62])
                v //= 62
            keys.append(chr(head) + "".join(reversed(digits)))
        length += 1
        head += 1
    return keys


class Rect2:
    """Anything with a bounding box; provides anchors for connectors."""

    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def pt(self, side: str, t: float = 0.5) -> Point:
        """Anchor on an edge: side in left/right/top/bottom/center; t = fraction along that edge."""
        if side == "left":
            return (self.x, self.y + self.h * t)
        if side == "right":
            return (self.x + self.w, self.y + self.h * t)
        if side == "top":
            return (self.x + self.w * t, self.y)
        if side == "bottom":
            return (self.x + self.w * t, self.y + self.h)
        if side == "center":
            return (self.cx, self.cy)
        raise ValueError(f"bad side {side!r}")

    @property
    def bind_target(self) -> Optional["El"]:
        return None


class El(Rect2):
    """Handle for one created Excalidraw element."""

    def __init__(self, cv: "Canvas", el: dict, x: float, y: float, w: float, h: float):
        self.cv, self.el, self.x, self.y, self.w, self.h = cv, el, x, y, w, h

    @property
    def id(self) -> str:
        return self.el["id"]

    @property
    def bind_target(self) -> Optional["El"]:
        return self if self.el["type"] in ("rectangle", "ellipse", "diamond", "image", "text") else None


class Canvas:
    def __init__(self, slug: str, *, bg: str = "#ffffff"):
        self.slug = slug
        self.bg = bg
        self.meta: dict = {}
        self.warnings: list[str] = []
        self.updated_label = time.strftime("%m/%d/%Y").lstrip("0").replace("/0", "/")
        self._els: list[Optional[dict]] = []
        self.files: dict[str, dict] = {}
        self._groups: list[str] = []
        self._rng = random.Random(f"foundry-explainers:{slug}")
        self._ids: set[str] = set()
        self._blocks: list[tuple[str, float, float, float, float]] = []
        self._now = int(time.time() // 86400) * 86400 * 1000  # midnight UTC: same-day rebuilds are byte-identical
        self.rough = 1  # default roughness (0 architect, 1 artist, 2 cartoonist)

    # ------------------------------------------------------------------ ids / base
    def _new_id(self) -> str:
        while True:
            i = "".join(self._rng.choice(ALNUM) for _ in range(21))
            if i not in self._ids:
                self._ids.add(i)
                return i

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def _base(self, typ: str, x: float, y: float, w: float, h: float, *, stroke=INK, bg="transparent",
              fill="solid", sw=2, dash="solid", rough=None, opacity=100, roundness=None, link=None) -> dict:
        return {
            "id": self._new_id(), "type": typ, "x": _r(x), "y": _r(y), "width": _r(w), "height": _r(h),
            "angle": 0, "strokeColor": stroke, "backgroundColor": bg, "fillStyle": fill, "strokeWidth": sw,
            "strokeStyle": dash, "roughness": self.rough if rough is None else rough, "opacity": opacity,
            "groupIds": list(reversed(self._groups)), "frameId": None, "index": None, "roundness": roundness,
            "seed": self._rng.randrange(1, 2 ** 31 - 1), "version": 2,
            "versionNonce": self._rng.randrange(1, 2 ** 31 - 1), "isDeleted": False, "boundElements": None,
            "updated": self._now, "link": link, "locked": False,
        }

    def _add(self, el: dict, x: float, y: float, w: float, h: float) -> El:
        self._els.append(el)
        return El(self, el, x, y, w, h)

    # ------------------------------------------------------------------ groups / z-order
    @contextmanager
    def group(self):
        """Elements created inside the `with` block move together in Excalidraw."""
        gid = self._new_id()
        self._groups.append(gid)
        try:
            yield gid
        finally:
            self._groups.pop()

    def mark(self) -> int:
        return len(self._els)

    def move_to(self, handle: El, index: int) -> None:
        """Move an already created element to z-position `index` (e.g. behind things drawn since mark())."""
        self._els.remove(handle.el)
        self._els.insert(index, handle.el)

    def bbox_since(self, mark: int) -> Optional[tuple[float, float, float, float]]:
        xs0, ys0, xs1, ys1 = [], [], [], []
        for e in self._els[mark:]:
            if e is None:
                continue
            x0, y0, x1, y1 = _el_bbox(e)
            xs0.append(x0), ys0.append(y0), xs1.append(x1), ys1.append(y1)
        if not xs0:
            return None
        return min(xs0), min(ys0), max(xs1), max(ys1)

    def bounds(self) -> tuple[float, float, float, float]:
        return self.bbox_since(0) or (0, 0, 0, 0)

    # ------------------------------------------------------------------ primitives
    def rect(self, x, y, w, h, *, stroke=INK, fill="transparent", style="hachure", sw=2, dash="solid",
             rough=None, opacity=100, round_=True, link=None) -> El:
        fs = "solid" if fill == "transparent" else style
        el = self._base("rectangle", x, y, w, h, stroke=stroke, bg=fill, fill=fs, sw=sw, dash=dash, rough=rough,
                        opacity=opacity, roundness={"type": 3} if round_ else None, link=link)
        return self._add(el, x, y, w, h)

    def ellipse(self, x, y, w, h, *, stroke=INK, fill="transparent", style="hachure", sw=2, dash="solid",
                rough=None, opacity=100, link=None) -> El:
        fs = "solid" if fill == "transparent" else style
        el = self._base("ellipse", x, y, w, h, stroke=stroke, bg=fill, fill=fs, sw=sw, dash=dash, rough=rough,
                        opacity=opacity, roundness={"type": 2}, link=link)
        return self._add(el, x, y, w, h)

    def diamond(self, x, y, w, h, *, stroke=INK, fill="transparent", style="hachure", sw=2, dash="solid",
                rough=None, opacity=100, link=None) -> El:
        fs = "solid" if fill == "transparent" else style
        el = self._base("diamond", x, y, w, h, stroke=stroke, bg=fill, fill=fs, sw=sw, dash=dash, rough=rough,
                        opacity=opacity, roundness={"type": 2}, link=link)
        return self._add(el, x, y, w, h)

    def text(self, x, y, s: str, *, size=16, color=INK, align="left", font=metrics.HAND, link=None, w=None,
             wrap: Optional[float] = None, opacity=100) -> El:
        """Free text. `x,y` is the top-left of the text box. With `w` set and align='center'/'right' the text is
        aligned inside that box width (handy for centring). `wrap` word-wraps to that pixel width."""
        s, bad = metrics.sanitize(str(s), font)
        if bad:
            self.warn(f"unsupported glyphs {sorted(bad)!r} in text {s[:40]!r} (will fall back to a system font)")
        if wrap:
            s = "\n".join(metrics.wrap_text(s, wrap, size, font))
        tw, th = metrics.text_size(s, size, font)
        bw = max(tw, w) if w is not None else tw
        el = self._base("text", x, y, bw, th, stroke=color, opacity=opacity, link=link)
        el.update({
            "fontSize": size, "fontFamily": font, "text": s, "textAlign": align, "verticalAlign": "top",
            "containerId": None, "originalText": s, "autoResize": True, "lineHeight": metrics.line_ratio(font),
        })
        return self._add(el, x, y, bw, th)

    def poly(self, pts: Sequence[Point], *, kind="line", stroke=INK, sw=2, dash="solid", rough=None, opacity=100,
             start_head=None, end_head=None, curved=False, fill="transparent", fill_style="hachure",
             link=None) -> El:
        """Polyline / arrow through absolute points. kind='arrow' adds heads; curved=True smooths the path."""
        x0, y0 = pts[0]
        rel = [[_r(px - x0), _r(py - y0)] for px, py in pts]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        closed = kind == "line" and len(pts) > 2 and pts[0] == pts[-1]
        fs = "solid" if fill == "transparent" else fill_style
        el = self._base(kind, x0, y0, w, h, stroke=stroke, bg=fill if closed else "transparent",
                        fill=fs if closed else "solid", sw=sw, dash=dash, rough=rough, opacity=opacity,
                        roundness={"type": 2} if curved else None, link=link)
        el.update({"points": rel, "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
                   "startArrowhead": start_head if kind == "arrow" else None,
                   "endArrowhead": end_head if kind == "arrow" else None})
        if kind == "arrow":
            el["elbowed"] = False
        else:
            el["polygon"] = bool(closed)
        handle = self._add(el, min(xs), min(ys), w, h)
        return handle

    def line(self, p1: Point, p2: Point, **kw) -> El:
        return self.poly([p1, p2], kind="line", **kw)

    def image(self, x, y, w, h, file_id: str, *, link=None) -> El:
        el = self._base("image", x, y, w, h, stroke="transparent", link=link)
        el.update({"status": "saved", "fileId": file_id, "scale": [1, 1], "crop": None})
        return self._add(el, x, y, w, h)

    def add_file(self, data: bytes, mime: str) -> str:
        fid = hashlib.sha1(data).hexdigest()
        if fid not in self.files:
            b64 = base64.b64encode(data).decode("ascii")
            self.files[fid] = {"mimeType": mime, "id": fid, "dataURL": f"data:{mime};base64,{b64}",
                               "created": self._now, "lastRetrieved": self._now}
        return fid

    # ------------------------------------------------------------------ panels
    @contextmanager
    def panel(self, x: float, y: float, *, title: Optional[str] = None, theme="gray", pad=24, title_size=24,
              style="dotted", fill="none", w: Optional[float] = None, h: Optional[float] = None, sub: str = None,
              link=None, sw=2, title_color: Optional[str] = None, title_pos="inside", min_w=0, min_h=0,
              rough=None, opacity=100, round_=True, sub_size=15):
        """Auto-sizing container. Place children at p.ix / p.iy (inner content origin) inside the `with` block.

        fill: 'none' | 'hatch' | 'solid' | 'soft'.  After the block, p.x/y/w/h give the final box (use for arrows).
        title_pos: 'inside' (default, top-left in the panel) or 'above' (outside, above the border).
        """
        th = get_theme(theme)
        p = Panel(x, y, pad)
        t_h = 0.0
        if title and title_pos == "inside":
            tw, t_h0 = metrics.text_size(title, title_size)
            t_h = t_h0 + 6
            if sub:
                _, sh = metrics.text_size(sub, sub_size)
                t_h += sh + 2
            t_h += 8
        p.ix, p.iy = x + pad, y + pad + t_h
        mark = self.mark()
        with self.group():
            yield p
            box = self.bbox_since(mark)
            if box is None:
                box = (x, y, x + pad * 2, y + pad * 2)
            right = max(box[2] + pad, x + min_w)
            bottom = max(box[3] + pad, y + min_h)
            pw = w if w is not None else right - x
            ph = h if h is not None else bottom - y
            if title and title_pos == "inside":
                need = metrics.text_size(title, title_size)[0] + pad * 2
                pw = max(pw, need)
            p.x, p.y, p.w, p.h = x, y, pw, ph
            bg, fs = "transparent", "solid"
            if fill == "hatch":
                bg, fs = th.fill, "hachure"
            elif fill == "solid":
                bg, fs = th.fill, "solid"
            elif fill == "soft":
                bg, fs = th.soft, "solid"
            box_el = self.rect(x, y, pw, ph, stroke=th.stroke, fill=bg, style=fs, sw=sw, dash=style, link=link,
                               rough=rough, opacity=opacity, round_=round_)
            self.move_to(box_el, mark)
            p.el = box_el
            if title:
                tcol = title_color or th.deep
                if title_pos == "inside":
                    t = self.text(x + pad, y + pad * 0.7, title, size=title_size, color=tcol)
                    if sub:
                        self.text(x + pad, t.bottom + 2, sub, size=sub_size, color="#495057")
                else:
                    self.text(x + pad, y - title_size * 1.25 - 6, title, size=title_size, color=tcol)
                    if sub:
                        self.text(x + pad + metrics.text_size(title, title_size)[0] + 14,
                                  y - sub_size * 1.25 - 8, sub, size=sub_size, color="#495057")
        self.register(f"panel:{title}", x, y, pw, ph, container=True)

    # ------------------------------------------------------------------ validation / output
    def register(self, name: str, x: float, y: float, w: float, h: float, container=False) -> None:
        if not container:
            self._blocks.append((name, x, y, w, h))

    def validate(self) -> list[str]:
        out = list(self.warnings)
        b = self._blocks
        for i in range(len(b)):
            for j in range(i + 1, len(b)):
                n1, x1, y1, w1, h1 = b[i]
                n2, x2, y2, w2, h2 = b[j]
                ox = min(x1 + w1, x2 + w2) - max(x1, x2)
                oy = min(y1 + h1, y2 + h2) - max(y1, y2)
                if ox > 4 and oy > 4:
                    out.append(f"OVERLAP {n1!r} <-> {n2!r} ({ox:.0f}x{oy:.0f}px)")
        return out

    def to_scene(self) -> dict:
        els = [e for e in self._els if e is not None]
        for e, key in zip(els, _frac_keys(len(els))):
            e["index"] = key
        used = {e.get("fileId") for e in els if e["type"] == "image"}
        files = {k: v for k, v in self.files.items() if k in used}
        return {"type": "excalidraw", "version": 2, "source": "foundry-explainers", "elements": els,
                "appState": {"gridSize": None, "viewBackgroundColor": self.bg}, "files": files}

    def save(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_scene(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return path


class Panel(Rect2):
    def __init__(self, x: float, y: float, pad: float):
        self.x, self.y, self.w, self.h = x, y, 0.0, 0.0
        self.pad = pad
        self.ix = x + pad
        self.iy = y + pad
        self.el: Optional[El] = None

    @property
    def bind_target(self) -> Optional[El]:
        return self.el


def _el_bbox(e: dict) -> tuple[float, float, float, float]:
    if e["type"] in ("line", "arrow"):
        pts = e["points"]
        xs = [e["x"] + p[0] for p in pts]
        ys = [e["y"] + p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)
    return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]
