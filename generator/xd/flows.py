"""Connectors, markers, braces, labelled boxes, sequence diagrams and timelines."""
from __future__ import annotations

import math
from typing import Optional, Sequence

from . import metrics
from .blocks import SAFETY
from .canvas import Canvas, El, Point, Rect2
from .icons import place_icon
from .palette import INK, MUTED, Theme, theme as get_theme


# ====================================================================== markers
def numbered(cv: Canvas, cx: float, cy: float, n, *, theme="blue", d=30, size=17) -> El:
    """Filled circle with a step number, centred on (cx, cy)."""
    th = get_theme(theme)
    s = str(n)
    tw, thh = metrics.text_size(s, size)
    with cv.group():
        c = cv.ellipse(cx - d / 2, cy - d / 2, d, d, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        cv.text(cx - tw / 2, cy - thh / 2 + 1, s, size=size, color=th.deep)
    return c


# ====================================================================== boxes
class Box(Rect2):
    """Centered-label shape (rect | ellipse | diamond) for architecture/flow diagrams."""

    def __init__(self, w: float, label: str, *, h: Optional[float] = None, theme="blue", sub: Optional[str] = None,
                 size=17, sub_size=14, icon: Optional[str] = None, shape="rect", fill="solid", dash="solid", pad=10,
                 sw=2, link=None, icon_size=34, icon_pos="top", color: Optional[str] = None, min_h=0, rough=None):
        self.th = get_theme(theme)
        self.w, self.shape, self.fill, self.dash, self.sw, self.link = w, shape, fill, dash, sw, link
        self.icon, self.icon_size, self.icon_pos, self.pad, self.rough = icon, icon_size, icon_pos, pad, rough
        self.size, self.sub_size = size, sub_size
        self.color = color or self.th.deep
        shrink = 0.62 if shape in ("ellipse", "diamond") else 1.0
        left_icon = (icon_size + 8) if (icon and icon_pos == "left") else 0
        inner = (w * shrink - 2 * pad - left_icon) * SAFETY
        self.lines = metrics.wrap_text(label, inner, size)
        self.sub_lines = metrics.wrap_text(sub, inner, sub_size) if sub else []
        lh = metrics.line_ratio()
        text_h = len(self.lines) * size * lh + (len(self.sub_lines) * sub_size * lh + 3 if sub else 0)
        top_icon = (icon_size + 6) if (icon and icon_pos == "top") else 0
        need = text_h + top_icon + 2 * pad
        if icon and icon_pos == "left":
            need = max(text_h, icon_size) + 2 * pad
        if shape != "rect":
            need = need / shrink
        self.text_h, self.top_icon, self.left_icon = text_h, top_icon, left_icon
        self.h = max(h or 0, need, min_h)
        self.x = self.y = 0.0
        self.shape_el: Optional[El] = None

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Box":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        bg, fs = "transparent", "solid"
        if self.fill == "solid":
            bg, fs = th.fill, "solid"
        elif self.fill == "hatch":
            bg, fs = th.fill, "hachure"
        elif self.fill == "soft":
            bg, fs = th.soft, "solid"
        with cv.group():
            if self.shape == "ellipse":
                self.shape_el = cv.ellipse(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=self.sw,
                                           dash=self.dash, link=self.link, rough=self.rough)
            elif self.shape == "diamond":
                self.shape_el = cv.diamond(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=self.sw,
                                           dash=self.dash, link=self.link, rough=self.rough)
            else:
                self.shape_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=self.sw,
                                        dash=self.dash, link=self.link, rough=self.rough)
            total = self.text_h + self.top_icon
            ty = y + (H - total) / 2
            if self.icon and self.icon_pos == "top":
                place_icon(cv, self.icon, x + (self.w - self.icon_size) / 2, ty, self.icon_size)
                ty += self.icon_size + 6
            tx0, tw_box = x, self.w
            if self.icon and self.icon_pos == "left":
                place_icon(cv, self.icon, x + self.pad, y + (H - self.icon_size) / 2, self.icon_size)
                tx0, tw_box = x + self.left_icon, self.w - self.left_icon
                ty = y + (H - self.text_h) / 2
            cv.text(tx0, ty, "\n".join(self.lines), size=self.size, color=self.color, align="center", w=tw_box)
            if self.sub_lines:
                ty += len(self.lines) * self.size * metrics.line_ratio() + 3
                cv.text(tx0, ty, "\n".join(self.sub_lines), size=self.sub_size, color=MUTED, align="center", w=tw_box)
        cv.register(f"box:{self.lines[0] if self.lines else ''}", x, y, self.w, H)
        return self

    @property
    def bind_target(self) -> Optional[El]:
        return self.shape_el


# ====================================================================== connectors
def _auto_sides(a: Rect2, b: Rect2) -> tuple[str, str]:
    dx, dy = b.cx - a.cx, b.cy - a.cy
    if abs(dx) >= abs(dy):
        return ("right", "left") if dx >= 0 else ("left", "right")
    return ("bottom", "top") if dy >= 0 else ("top", "bottom")


_OFFSET = {"left": (-1, 0), "right": (1, 0), "top": (0, -1), "bottom": (0, 1), "center": (0, 0)}


def _poly_point(pts: Sequence[Point], t: float) -> tuple[Point, bool]:
    """Point at fraction t of the polyline length; also whether that segment is mostly horizontal."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    target = t * total
    acc = 0.0
    for i, s in enumerate(seg):
        if acc + s >= target or i == len(seg) - 1:
            f = (target - acc) / s if s else 0
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            horizontal = abs(pts[i + 1][0] - pts[i][0]) >= abs(pts[i + 1][1] - pts[i][1])
            return (x, y), horizontal
        acc += s
    return pts[-1], True


def arrow(cv: Canvas, pts: Sequence[Point], *, label: Optional[str] = None, label_size=14, label_t=0.5,
          label_pos="auto", label_dx=0.0, label_dy=0.0, label_bg=False, label_color: Optional[str] = None,
          label_wrap: Optional[float] = None, dash="solid", color=INK, sw=2, start_head=None, end_head="arrow",
          curved=False, num=None, num_theme="blue", rough=None, opacity=100, link=None) -> El:
    """Arrow (or plain line when no heads) through absolute points, with optional label / step number."""
    kind = "arrow" if (start_head or end_head) else "line"
    el = cv.poly(list(pts), kind=kind, stroke=color, sw=sw, dash=dash, start_head=start_head, end_head=end_head,
                 curved=curved, rough=rough, opacity=opacity, link=link)
    if label or num is not None:
        (mx, my), horiz = _poly_point(pts, label_t)
        if num is not None:
            numbered(cv, mx, my, num, theme=num_theme)
        if label:
            txt = label
            if label_wrap:
                txt = "\n".join(metrics.wrap_text(label, label_wrap, label_size))
            tw, th_ = metrics.text_size(txt, label_size)
            pos = label_pos
            if pos == "auto":
                pos = "above" if horiz else "right"
            off = 20 if num is not None else 0
            if pos == "above":
                lx, ly = mx - tw / 2, my - th_ - 5
                lx += off if num is not None else 0
            elif pos == "below":
                lx, ly = mx - tw / 2, my + 6
            elif pos == "left":
                lx, ly = mx - tw - 10 - off, my - th_ / 2
            elif pos == "right":
                lx, ly = mx + 10 + off, my - th_ / 2
            else:  # center
                lx, ly = mx - tw / 2, my - th_ / 2
            lx, ly = lx + label_dx, ly + label_dy
            if label_bg or pos == "center":
                cv.rect(lx - 4, ly - 1, tw + 8, th_ + 2, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                        rough=0, opacity=92, round_=False)
            cv.text(lx, ly, txt, size=label_size, color=label_color or INK, align="center" if "\n" in txt else "left",
                    w=tw)
    return el


def connect(cv: Canvas, a: Rect2, b: Rect2, *, a_side: Optional[str] = None, b_side: Optional[str] = None,
            ta=0.5, tb=0.5, gap=6, route="straight", bend=0.5, via: Sequence[Point] = (), bind=True, **kw) -> El:
    """Arrow from shape a to shape b (any placed block / El / Panel).

    route: 'straight' | 'elbow' (orthogonal, bends at `bend` fraction) | 'curve' (gentle arc).
    kw -> arrow(): label, num, dash, color, sw, start_head, end_head ('arrow'|'triangle'|'dot'|'bar'|None), ...
    """
    sa, sb = _auto_sides(a, b)
    a_side, b_side = a_side or sa, b_side or sb
    p1, p2 = a.pt(a_side, ta), b.pt(b_side, tb)
    oa, ob = _OFFSET[a_side], _OFFSET[b_side]
    p1 = (p1[0] + oa[0] * gap, p1[1] + oa[1] * gap)
    p2 = (p2[0] + ob[0] * gap, p2[1] + ob[1] * gap)
    pts: list[Point]
    if via:
        pts = [p1, *via, p2]
    elif route == "elbow":
        pts = elbow_points(p1, p2, a_side, b_side, bend)
    elif route == "curve":
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        horiz = a_side in ("left", "right")
        k = 0.25 * (abs(p2[1] - p1[1]) if horiz else abs(p2[0] - p1[0]))
        pts = [p1, (mx + (0 if horiz else k), my + (k if horiz else 0)), p2]
        kw.setdefault("curved", True)
    else:
        pts = [p1, p2]
    el = arrow(cv, pts, **kw)
    if bind:
        ta_, tb_ = a.bind_target, b.bind_target
        if ta_ is not None and tb_ is not None:
            el.el["startBinding"] = {"elementId": ta_.id, "focus": 0, "gap": gap}
            el.el["endBinding"] = {"elementId": tb_.id, "focus": 0, "gap": gap}
            for tgt in (ta_, tb_):
                tgt.el["boundElements"] = (tgt.el.get("boundElements") or []) + [{"id": el.id, "type": "arrow"}]
    return el


def elbow_points(p1: Point, p2: Point, a_side: str, b_side: str, bend=0.5) -> list[Point]:
    (x1, y1), (x2, y2) = p1, p2
    ha, hb = a_side in ("left", "right"), b_side in ("left", "right")
    if ha and hb:
        if abs(y1 - y2) < 2:
            return [p1, p2]
        xm = x1 + (x2 - x1) * bend
        return [p1, (xm, y1), (xm, y2), p2]
    if not ha and not hb:
        if abs(x1 - x2) < 2:
            return [p1, p2]
        ym = y1 + (y2 - y1) * bend
        return [p1, (x1, ym), (x2, ym), p2]
    if ha and not hb:
        return [p1, (x2, y1), p2]
    return [p1, (x1, y2), p2]


def line_between(cv: Canvas, a: Rect2, b: Rect2, *, dash="dotted", color=INK, sw=2, **kw) -> El:
    """Plain (no head) dotted connector like the reference Fabric diagrams."""
    return connect(cv, a, b, dash=dash, color=color, sw=sw, end_head=None, start_head=None, gap=0, **kw)


# ====================================================================== braces
def _densify(pts: list[Point], max_seg: float = 120.0) -> list[Point]:
    """Insert points along long straight runs so a smoothed (curved) polyline cannot overshoot between control points."""
    out: list[Point] = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = int(d // max_seg)
        for i in range(1, n + 1):
            t = i / (n + 1)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        out.append(b)
    return out


def brace(cv: Canvas, x: float, y1: float, y2: float, *, side="left", depth=20, color=INK, sw=2) -> El:
    """Vertical curly brace. side='left' draws '{' (tip points left) with its spine at x."""
    d = depth if side == "left" else -depth
    ym = (y1 + y2) / 2
    k = min(depth, (y2 - y1) / 5)
    pts = [(x + d, y1), (x + d * 0.3, y1 + k * 0.3), (x, y1 + k), (x, ym - k), (x - d * 0.3, ym - k * 0.3),
           (x - d, ym), (x - d * 0.3, ym + k * 0.3), (x, ym + k), (x, y2 - k), (x + d * 0.3, y2 - k * 0.3),
           (x + d, y2)]
    return cv.poly(_densify(pts), kind="line", stroke=color, sw=sw, curved=True)


def hbrace(cv: Canvas, x1: float, x2: float, y: float, *, side="top", depth=18, color=INK, sw=2) -> El:
    """Horizontal curly brace. side='top' draws the tip pointing up."""
    d = -depth if side == "top" else depth
    xm = (x1 + x2) / 2
    k = min(depth, (x2 - x1) / 5)
    pts = [(x1, y + d), (x1 + k * 0.3, y + d * 0.3), (x1 + k, y), (xm - k, y), (xm - k * 0.3, y - d * 0.3),
           (xm, y - d), (xm + k * 0.3, y - d * 0.3), (xm + k, y), (x2 - k, y), (x2 - k * 0.3, y + d * 0.3),
           (x2, y + d)]
    return cv.poly(_densify(pts), kind="line", stroke=color, sw=sw, curved=True)


# ====================================================================== sequence diagrams
class Sequence:
    """Swimlane/sequence diagram.  actors = [(label, theme, icon_or_None), ...]

        seq = Sequence(cv, x, y, [("Client", "gray", "user"), ("Foundry endpoint", "blue", "foundry")], spacing=280)
        seq.msg(0, 1, "POST /responses", num=1)
        seq.msg(1, 0, "200 + stream", dash="dashed")
        seq.note(0, 1, "token is validated here", kind="warn")
        seq.end()          # draws lifelines behind everything and returns bottom y
    """

    def __init__(self, cv: Canvas, x: float, y: float, actors: Sequence[tuple], *, spacing=260, head_w=190,
                 head_h=56, step=62, size=15, label_size=14):
        self.cv, self.x, self.y0 = cv, x, y
        self.spacing, self.head_w, self.head_h, self.step, self.size, self.label_size = (
            spacing, head_w, head_h, step, size, label_size)
        self.actors = []
        self.mark = cv.mark()
        for i, a in enumerate(actors):
            label, th_name = a[0], a[1]
            icon = a[2] if len(a) > 2 else None
            cx = x + head_w / 2 + i * spacing
            b = Box(head_w, label, h=head_h, theme=th_name, icon=icon, icon_pos="left", icon_size=30, size=size + 1,
                    min_h=head_h).place(cv, cx - head_w / 2, y)
            self.actors.append((cx, get_theme(th_name), b))
        self.cur = y + head_h + 30

    def _cx(self, i: int) -> float:
        return self.actors[i][0]

    def msg(self, src: int, dst: int, text: str, *, dash="solid", num=None, note: Optional[str] = None,
            color=INK, gap_after=0, end_head="arrow") -> float:
        """One message row; returns the arrow's y. Vertical space adapts to the wrapped label height."""
        cv = self.cv
        x1, x2 = self._cx(src), self._cx(dst)
        th = self.actors[src][1]
        if src == dst:
            w = 70
            lines = metrics.wrap_text(text, self.spacing * 0.9, self.label_size)
            lh = len(lines) * self.label_size * metrics.line_ratio()
            y = self.cur + 6
            pts = [(x1, y), (x1 + w, y), (x1 + w, y + 30), (x1 + 4, y + 30)]
            cv.poly(pts, kind="arrow", stroke=color, sw=2, dash=dash, end_head=end_head)
            cv.text(x1 + w + 10, y - 4, "\n".join(lines), size=self.label_size, color=INK)
            self.cur = y + max(30, lh) + 26 + gap_after
            return y
        lo, hi = sorted((x1, x2))
        span = hi - lo
        lw = max(span - 50 - (30 if num is not None else 0), 120)
        lines = metrics.wrap_text(text, lw, self.label_size)
        txt = "\n".join(lines)
        tw, th_ = metrics.text_size(txt, self.label_size)
        y = self.cur + th_ + 14
        cv.poly([(x1 + (4 if x2 > x1 else -4), y), (x2 - (4 if x2 > x1 else -4), y)], kind="arrow", stroke=color,
                sw=2, dash=dash, end_head=end_head)
        tx = lo + (span - tw) / 2
        if num is not None:
            numbered(cv, lo + 22 if x2 > x1 else hi - 22, y - 16, num, theme=th.name, d=26, size=15)
            tx += 12
        cv.text(tx, y - th_ - 5, txt, size=self.label_size, color=INK, align="center", w=tw)
        if note:
            nl = metrics.wrap_text(note, max(span - 30, 120), self.label_size - 2)
            cv.text(lo + 14, y + 6, "\n".join(nl), size=self.label_size - 2, color=MUTED)
            self.cur = y + 12 + len(nl) * (self.label_size - 2) * 1.25 + gap_after
        else:
            self.cur = y + 20 + gap_after
        return y

    def note(self, a: int, b: int, text: str, *, kind="info", size: Optional[int] = None) -> None:
        from .blocks import Note
        lo, hi = sorted((self._cx(a), self._cx(b)))
        w = max(hi - lo + self.head_w - 20, 260)
        n = Note(w, text, kind=kind, size=size or self.size)
        n.place(self.cv, lo - (self.head_w - 20) / 2, self.cur)
        self.cur += n.h + 20

    def end(self) -> float:
        cv = self.cv
        bottom = self.cur + 6
        for cx, th, box in self.actors:
            ln = cv.line((cx, box.y + box.h), (cx, bottom), stroke=th.stroke, sw=2, dash="dashed", opacity=70)
            cv.move_to(ln, self.mark)
        return bottom


# ====================================================================== timeline
def timeline(cv: Canvas, x: float, y: float, w: float, events: Sequence[tuple], *, color=INK, size=16,
             label_w=190, theme="blue") -> float:
    """Horizontal timeline. events: (when, title, optional detail); alternates above/below. Returns bottom y."""
    th = get_theme(theme)
    n = len(events)
    cv.line((x, y), (x + w, y), stroke=color, sw=3)
    cv.poly([(x + w - 12, y - 8), (x + w, y), (x + w - 12, y + 8)], kind="line", stroke=color, sw=3)
    step = w / max(n, 1)
    bottom = y
    for i, ev in enumerate(events):
        when, title = ev[0], ev[1]
        detail = ev[2] if len(ev) > 2 else None
        cx = x + step * (i + 0.5)
        cv.ellipse(cx - 9, y - 9, 18, 18, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        above = i % 2 == 0
        tl = metrics.wrap_text(title, label_w * SAFETY, size)
        dl = metrics.wrap_text(detail, label_w * SAFETY, size - 2) if detail else []
        block_h = (size * 1.25 * (len(tl) + 1)) + (len(dl) * (size - 2) * 1.25 + 4)
        if above:
            ty = y - 26 - block_h
            cv.line((cx, y - 10), (cx, y - 24), stroke=th.stroke, sw=2)
        else:
            ty = y + 26
            cv.line((cx, y + 10), (cx, y + 24), stroke=th.stroke, sw=2)
        cv.text(cx - label_w / 2, ty, when, size=size, color=th.deep, align="center", w=label_w)
        ty2 = ty + size * 1.25
        cv.text(cx - label_w / 2, ty2, "\n".join(tl), size=size, color=INK, align="center", w=label_w)
        ty3 = ty2 + len(tl) * size * 1.25 + 4
        if dl:
            cv.text(cx - label_w / 2, ty3, "\n".join(dl), size=size - 2, color=MUTED, align="center", w=label_w)
        bottom = max(bottom, ty + block_h)
    return bottom
