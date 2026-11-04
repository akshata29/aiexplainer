"""High level, self-measuring blocks.  Construct (measures text) -> place(cv, x, y) (draws).

    card = Card(420, "Prompt agents", ["Declarative: instructions + model + tools", "  sub bullet", "! gotcha"],
                theme="green", badge="ga", src=[("Prompt agents", learn("agents/concepts/prompt-agents"))])
    card.place(cv, 100, 200)           # card.x/y/w/h are now set -> use card.pt("right") for connectors

Bullet markup (strings in `body`): plain = bullet, two leading spaces = sub-bullet, '# ' = sub-heading,
'= ' = paragraph (no marker), '! ' = warning bullet (red), '+ ' = positive bullet (green).
"""
from __future__ import annotations

from typing import Optional, Sequence

from . import metrics
from .canvas import Canvas, El, Rect2
from .icons import place_icon
from .palette import INK, LINK, MUTED, STATUS, Theme, theme as get_theme

SAFETY = 0.965  # shrink wrap widths slightly so kerning/hinting differences never overflow


def learn(path: str, base: str = "azure/foundry") -> str:
    """Canonical Microsoft Learn URL. learn('agents/overview') -> .../en-us/azure/foundry/agents/overview.
    Use learn('azure/search/agentic-retrieval-overview', base='') for other Learn areas."""
    path = path.strip("/")
    root = "https://learn.microsoft.com/en-us/"
    return root + (f"{base.strip('/')}/{path}" if base else path)


def short_url(url: str) -> str:
    u = url.replace("https://", "").replace("http://", "")
    u = u.replace("learn.microsoft.com/en-us/", "learn.microsoft.com/")
    return u.split("?")[0].rstrip("/")


# ====================================================================== bullets / cards
def _parse_body(body: Sequence) -> list[tuple[str, int, str]]:
    items: list[tuple[str, int, str]] = []
    for it in body:
        if isinstance(it, tuple):
            kind, text = it[0], it[1]
            level = it[2] if len(it) > 2 else 0
        else:
            s = str(it)
            level = (len(s) - len(s.lstrip(" "))) // 2
            text = s.strip()
            kind = "bullet"
            for pfx, k in (("# ", "head"), ("= ", "para"), ("! ", "warn"), ("+ ", "good")):
                if text.startswith(pfx):
                    kind, text = k, text[2:]
                    break
        items.append((kind, level, text))
    return items


class Card(Rect2):
    def __init__(self, w: float, title: Optional[str] = None, body: Sequence = (), *, theme="blue",
                 subtitle: Optional[str] = None, badge: Optional[str] = None, icon: Optional[str] = None,
                 link: Optional[str] = None, src: Sequence[tuple[str, str]] = (), fill="hatch", dash="solid",
                 title_size=20, body_size=16, sub_size=14, pad=16, gap=5, para_gap=8, min_h=0, align="left",
                 title_color: Optional[str] = None, sw=2, rough=None, opacity=100, round_=True, icon_size=36,
                 body_color=INK, bullet="ring", src_size=12):
        self.th: Theme = get_theme(theme)
        self.w = w
        self.title, self.subtitle, self.badge, self.icon, self.link = title, subtitle, badge, icon, link
        self.src = list(src)
        self.fill, self.dash, self.sw, self.rough, self.opacity, self.round_ = fill, dash, sw, rough, opacity, round_
        self.title_size, self.body_size, self.sub_size, self.pad = title_size, body_size, sub_size, pad
        self.gap, self.para_gap, self.min_h, self.align = gap, para_gap, min_h, align
        self.title_color, self.body_color, self.bullet, self.icon_size, self.src_size = (
            title_color or self.th.deep, body_color, bullet, icon_size, src_size)
        self.items = _parse_body(body)
        self.x = self.y = 0.0
        self.rect_el: Optional[El] = None
        self._layout()

    # ---- measuring
    def _layout(self) -> None:
        pad, w = self.pad, self.w
        inner = (w - 2 * pad) * SAFETY
        self.badge_w = 0.0
        if self.badge:
            _, label = STATUS.get(self.badge, ("gray", self.badge))
            self.badge_w = metrics.line_width(label, 13) + 18
        icon_off = (self.icon_size + 10) if self.icon else 0
        t_w = inner - icon_off - (self.badge_w + 8 if self.badge else 0)
        y = pad
        self.title_lines: list[str] = []
        self.sub_lines: list[str] = []
        head_h = 0.0
        if self.title:
            self.title_lines = metrics.wrap_text(self.title, t_w, self.title_size)
            head_h = len(self.title_lines) * self.title_size * metrics.line_ratio()
        if self.subtitle:
            self.sub_lines = metrics.wrap_text(self.subtitle, t_w, self.sub_size)
            head_h += 2 + len(self.sub_lines) * self.sub_size * metrics.line_ratio()
        if self.icon:
            head_h = max(head_h, self.icon_size)
        self.icon_off = icon_off
        y += head_h
        if self.title or self.subtitle or self.icon:
            y += self.gap + 3
        self.layout: list[dict] = []
        first = True
        for kind, level, text in self.items:
            if kind == "head":
                size, x0, tx, tw = self.body_size + 1, pad, pad, inner
                if not first:
                    y += self.para_gap - self.gap
            elif kind == "para":
                size, x0, tx, tw = self.body_size, pad, pad, inner
            else:
                size = self.body_size - (1 if level else 0)
                x0 = pad + level * 20
                tx = x0 + 18
                tw = inner - level * 20 - 18
            lines = metrics.wrap_text(text, tw, size)
            lh = size * metrics.line_ratio()
            self.layout.append({"kind": kind, "level": level, "x0": x0, "tx": tx, "y": y, "lines": lines,
                                "size": size, "lh": lh})
            y += len(lines) * lh + self.gap
            first = False
        if self.items:
            y -= self.gap
        self.src_lines: list[tuple[str, str, float]] = []
        if self.src:
            y += 8
            for label, url in self.src:
                txt = f"Learn: {label}"
                lines = metrics.wrap_text(txt, inner, self.src_size)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * self.src_size * metrics.line_ratio() + 2
            y -= 2
        self.h = max(y + pad, self.min_h)
        self.content_h = y + pad

    # ---- drawing
    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Card":
        self.x, self.y = x, y
        H = max(self.content_h, h or 0, self.min_h)
        self.h = H
        th, pad = self.th, self.pad
        bg, fs = "transparent", "solid"
        if self.fill == "hatch":
            bg, fs = th.fill, "hachure"
        elif self.fill == "solid":
            bg, fs = th.fill, "solid"
        elif self.fill == "soft":
            bg, fs = th.soft, "solid"
        elif self.fill == "cross":
            bg, fs = th.fill, "cross-hatch"
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=self.sw, dash=self.dash,
                                   link=self.link, rough=self.rough, opacity=self.opacity, round_=self.round_)
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, self.icon_size)
            ty = y + pad
            tx = x + pad + self.icon_off
            inner_w = self.w - 2 * pad
            if self.title_lines:
                tw = inner_w - self.icon_off
                if self.align == "center":
                    cv.text(x + pad, ty, "\n".join(self.title_lines), size=self.title_size, color=self.title_color,
                            align="center", w=inner_w)
                else:
                    cv.text(tx, ty, "\n".join(self.title_lines), size=self.title_size, color=self.title_color)
                ty += len(self.title_lines) * self.title_size * metrics.line_ratio()
            if self.sub_lines:
                cv.text(tx, ty + 2, "\n".join(self.sub_lines), size=self.sub_size, color=MUTED)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.badge_w, y + pad - 1, self.badge)
            for it in self.layout:
                kind, ly = it["kind"], y + it["y"]
                text = "\n".join(it["lines"])
                color = self.body_color
                if kind == "head":
                    color = th.stroke
                elif kind == "warn":
                    color = "#c92a2a"
                elif kind == "good":
                    color = "#2b8a3e"
                if self.align == "center" and kind in ("para", "head"):
                    cv.text(x + pad, ly, text, size=it["size"], color=color, align="center", w=inner_w)
                else:
                    cv.text(x + it["tx"], ly, text, size=it["size"], color=color)
                if kind in ("bullet", "warn", "good") and self.bullet:
                    mc = {"bullet": th.stroke if th.name not in ("gray", "ink") else "#f08c00",
                          "warn": "#e03131", "good": "#2f9e44"}[kind]
                    cy = ly + it["size"] * metrics.line_ratio() / 2
                    mx = x + it["x0"] + 4
                    if it["level"]:
                        cv.ellipse(mx + 1, cy - 2.5, 5, 5, stroke=mc, fill=mc, style="solid", sw=1, rough=0)
                    else:
                        cv.ellipse(mx, cy - 4, 9, 9, stroke=mc, sw=2, rough=0)
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=self.src_size, color=LINK, link=url)
        cv.register(f"card:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self) -> Optional[El]:
        return self.rect_el


# ====================================================================== badges / chips / notes
def draw_badge(cv: Canvas, x: float, y: float, kind: str, size: int = 13) -> El:
    """Small status pill. kind: ga | preview | retiring | new | classic or any custom label."""
    theme_name, label = STATUS.get(kind, ("gray", kind))
    th = get_theme(theme_name)
    tw = metrics.line_width(label, size)
    w, h = tw + 18, size * 1.25 + 6
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0)
        cv.text(x + 9, y + 3, label, size=size, color=th.deep)
    return r


class Chip(Rect2):
    def __init__(self, label: str, *, theme="blue", size=16, pad_x=12, pad_y=6, icon: Optional[str] = None,
                 fill="solid", sw=1.5, link=None, dash="solid", w: Optional[float] = None, color: Optional[str] = None,
                 round_=True, icon_size=22):
        self.th = get_theme(theme)
        self.label, self.size, self.pad_x, self.pad_y, self.icon = label, size, pad_x, pad_y, icon
        self.fill, self.sw, self.link, self.dash, self.round_, self.icon_size = fill, sw, link, dash, round_, icon_size
        self.color = color or self.th.deep
        label, _ = metrics.sanitize(label)
        self.label = label
        tw, th_ = metrics.text_size(label, size)
        self.icon_w = (icon_size + 6) if icon else 0
        self.w = max(w or 0, tw + 2 * pad_x + self.icon_w)
        self.h = max(th_ + 2 * pad_y, icon_size + 6 if icon else 0)
        self.tw, self.th_ = tw, th_
        self.x = self.y = 0.0
        self.rect_el: Optional[El] = None

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Chip":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        bg, fs = "transparent", "solid"
        if self.fill == "solid":
            bg, fs = self.th.fill, "solid"
        elif self.fill == "soft":
            bg, fs = self.th.soft, "solid"
        elif self.fill == "hatch":
            bg, fs = self.th.fill, "hachure"
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=bg, style=fs, sw=self.sw,
                                   dash=self.dash, link=self.link, round_=self.round_)
            tx = x + self.pad_x
            if self.icon:
                place_icon(cv, self.icon, tx - 2, y + (H - self.icon_size) / 2, self.icon_size)
                tx += self.icon_w
            cv.text(tx, y + (H - self.th_) / 2, self.label, size=self.size, color=self.color)
        cv.register(f"chip:{self.label}", x, y, self.w, H)
        return self

    @property
    def bind_target(self) -> Optional[El]:
        return self.rect_el


class ChipFlow(Rect2):
    """Chips wrapped into rows within width w."""

    def __init__(self, items: Sequence, w: float, *, gap=10, theme="blue", size=15, **chip_kw):
        self.w = w
        self.gap = gap
        self.chips: list[Chip] = [i if isinstance(i, Chip) else Chip(i, theme=theme, size=size, **chip_kw)
                                  for i in items]
        self.rows: list[list[Chip]] = []
        cur: list[Chip] = []
        cw = 0.0
        for c in self.chips:
            need = c.w + (gap if cur else 0)
            if cur and cw + need > w:
                self.rows.append(cur)
                cur, cw = [], 0.0
                need = c.w
            cur.append(c)
            cw += need
        if cur:
            self.rows.append(cur)
        self.row_h = [max(c.h for c in r) for r in self.rows]
        self.h = sum(self.row_h) + gap * max(0, len(self.rows) - 1)
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "ChipFlow":
        self.x, self.y = x, y
        cy = y
        for row, rh in zip(self.rows, self.row_h):
            cx = x
            for c in row:
                c.place(cv, cx, cy, h=rh)
                cx += c.w + self.gap
            cy += rh + self.gap
        return self


NOTE_KINDS = {
    "info": ("blue", "i"), "tip": ("green", "+"), "warn": ("orange", "!"), "gotcha": ("red", "!"),
    "preview": ("violet", "P"), "quote": ("yellow", '"'), "key": ("teal", "*"),
}


class Note(Rect2):
    """Callout box with a round glyph on the left: kind in info|tip|warn|gotcha|preview|quote|key."""

    def __init__(self, w: float, text: str, *, kind="info", title: Optional[str] = None, size=15, pad=12,
                 theme: Optional[str] = None, link: Optional[str] = None, src: Sequence[tuple[str, str]] = (),
                 dash="solid", min_h=0, title_size=17):
        th_name, self.glyph = NOTE_KINDS.get(kind, ("blue", "i"))
        self.th = get_theme(theme or th_name)
        self.w, self.size, self.pad, self.title, self.link, self.dash, self.title_size = (
            w, size, pad, title, link, dash, title_size)
        self.src = list(src)
        self.g_w = 30
        inner = (w - 2 * pad - self.g_w) * SAFETY
        self.t_lines = metrics.wrap_text(title, inner, title_size) if title else []
        self.lines = metrics.wrap_text(text, inner, size)
        h = pad * 2
        if self.t_lines:
            h += len(self.t_lines) * title_size * metrics.line_ratio() + 3
        h += len(self.lines) * size * metrics.line_ratio()
        self.src_lines = []
        if self.src:
            h += 6
            for label, url in self.src:
                lines = metrics.wrap_text(f"Learn: {label}", inner, 12)
                self.src_lines.append(("\n".join(lines), url, h))
                h += len(lines) * 12 * metrics.line_ratio() + 2
            h -= 2 + 0
            h -= 0
        self.h = max(h, min_h, 44)
        self.x = self.y = 0.0
        self.rect_el: Optional[El] = None

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Note":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2,
                                   dash=self.dash, link=self.link)
            cv.ellipse(x + pad - 2, y + pad - 1, 24, 24, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
            gw = metrics.line_width(self.glyph, 16)
            cv.text(x + pad - 2 + (24 - gw) / 2, y + pad + 1, self.glyph, size=16, color=th.deep)
            tx, ty = x + pad + self.g_w, y + pad
            if self.t_lines:
                cv.text(tx, ty, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
                ty += len(self.t_lines) * self.title_size * metrics.line_ratio() + 3
            cv.text(tx, ty, "\n".join(self.lines), size=self.size, color=INK)
            for txt, url, off in self.src_lines:
                cv.text(tx, y + off, txt, size=12, color=LINK, link=url)
        cv.register("note", x, y, self.w, H)
        return self

    @property
    def bind_target(self) -> Optional[El]:
        return self.rect_el


class Bubble(Rect2):
    """Speech-bubble (sample prompts / quotes) with a small tail: tail in left|right|top|bottom|None."""

    def __init__(self, w: float, text: str, *, theme="violet", size=15, pad=12, tail="left", fill="solid"):
        self.th = get_theme(theme)
        self.w, self.size, self.pad, self.tail, self.fill = w, size, pad, tail, fill
        inner = (w - 2 * pad) * SAFETY
        self.lines = metrics.wrap_text(text, inner, size)
        self.h = len(self.lines) * size * metrics.line_ratio() + 2 * pad
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Bubble":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style=self.fill if self.fill != "hatch" else "hachure", sw=2)
            ty = y + self.pad
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK)
            cy = y + min(26, H / 2)
            if self.tail == "left":
                cv.poly([(x + 1, cy - 9), (x - 15, cy), (x + 1, cy + 9), (x + 1, cy - 9)], stroke=th.stroke,
                        fill=th.fill, fill_style="solid", sw=2, rough=0)
            elif self.tail == "right":
                xr = x + self.w
                cv.poly([(xr - 1, cy - 9), (xr + 15, cy), (xr - 1, cy + 9), (xr - 1, cy - 9)], stroke=th.stroke,
                        fill=th.fill, fill_style="solid", sw=2, rough=0)
        cv.register("bubble", x - (15 if self.tail == "left" else 0), y, self.w + 15, H)
        return self


# ====================================================================== tables
CHECK = "[v]"
CROSS = "[x]"
PARTIAL = "[~]"
DASH = "[-]"


def draw_mark(cv: Canvas, kind: str, cx: float, cy: float, size: float = 18) -> None:
    """Vector tick / cross / partial / dash (Excalifont has no check glyphs)."""
    s = size / 2
    if kind == CHECK:
        cv.poly([(cx - s * 0.7, cy + s * 0.05), (cx - s * 0.2, cy + s * 0.6), (cx + s * 0.8, cy - s * 0.7)],
                stroke="#2f9e44", sw=3, rough=1)
    elif kind == CROSS:
        cv.line((cx - s * 0.6, cy - s * 0.6), (cx + s * 0.6, cy + s * 0.6), stroke="#e03131", sw=3)
        cv.line((cx - s * 0.6, cy + s * 0.6), (cx + s * 0.6, cy - s * 0.6), stroke="#e03131", sw=3)
    elif kind == PARTIAL:
        cv.ellipse(cx - s * 0.7, cy - s * 0.7, s * 1.4, s * 1.4, stroke="#f08c00", fill="#ffec99", style="solid",
                   sw=2, rough=0)
    else:
        cv.line((cx - s * 0.5, cy), (cx + s * 0.5, cy), stroke="#868e96", sw=3)


class Table(Rect2):
    """cols: ['Name', ('Other', 180), ...] (width optional). rows: list of lists; a cell is str, (text, theme) or
    dict(text=, theme=, align=). Cell text '[v]' '[x]' '[~]' '[-]' draw vector marks."""

    def __init__(self, cols: Sequence, rows: Sequence[Sequence], *, w: Optional[float] = None, theme="blue",
                 size=15, head_size=16, pad_x=10, pad_y=7, zebra=True, first_col_theme: Optional[str] = None,
                 max_col=380, min_col=70, align: Optional[Sequence[str]] = None, link: Optional[str] = None,
                 head_fill="solid", title: Optional[str] = None, title_size=20, round_=False):
        self.th = get_theme(theme)
        self.size, self.head_size, self.pad_x, self.pad_y = size, head_size, pad_x, pad_y
        self.zebra, self.link, self.head_fill, self.round_ = zebra, link, head_fill, round_
        self.first_col_theme = get_theme(first_col_theme) if first_col_theme else None
        self.title, self.title_size = title, title_size
        self.heads = [c if isinstance(c, str) else c[0] for c in cols]
        fixed = [None if isinstance(c, str) else c[1] for c in cols]
        n = len(cols)
        self.align = list(align) if align else ["left"] * n
        self.cells: list[list[dict]] = []
        for r in rows:
            row = []
            for i in range(n):
                c = r[i] if i < len(r) else ""
                if isinstance(c, dict):
                    d = dict(c)
                elif isinstance(c, tuple):
                    d = {"text": c[0], "theme": c[1]}
                else:
                    d = {"text": c}
                d["text"], _ = metrics.sanitize(str(d.get("text", "")))
                row.append(d)
            self.cells.append(row)
        # natural/min widths
        nat, mn = [], []
        for i in range(n):
            texts = [self.heads[i]] + [row[i]["text"] for row in self.cells]
            sizes = [head_size] + [size] * len(self.cells)
            nat_w = max(max((metrics.line_width(l, s) for l in t.split("\n")), default=0) for t, s in zip(texts, sizes))
            min_w = max(max((metrics.line_width(wd, s) for wd in l.split(" ")), default=0)
                        for t, s in zip(texts, sizes) for l in t.split("\n"))
            nat.append(nat_w + 2 * pad_x + 4)
            mn.append(min(min_w + 2 * pad_x + 4, max_col))
        widths = [f if f else min(max(nat[i], min_col), max_col) for i, f in enumerate(fixed)]
        if w is not None:
            free = [i for i, f in enumerate(fixed) if not f]
            total = sum(widths)
            if total > w and free:
                # shrink free columns toward their minimum width proportionally
                slack = sum(max(widths[i] - mn[i], 0) for i in free)
                need = total - w
                for i in free:
                    s = max(widths[i] - mn[i], 0)
                    widths[i] -= min(s, need * (s / slack if slack else 0))
            elif total < w and free:
                extra = w - total
                base = sum(widths[i] for i in free)
                for i in free:
                    widths[i] += extra * widths[i] / base
        self.col_w = widths
        self.w = sum(widths)
        # wrap + row heights
        lh = metrics.line_ratio()
        self.head_lines = [metrics.wrap_text(self.heads[i], (widths[i] - 2 * pad_x) * SAFETY, head_size) for i in range(n)]
        self.head_h = max(len(l) for l in self.head_lines) * head_size * lh + 2 * pad_y
        self.row_lines: list[list[list[str]]] = []
        self.row_h: list[float] = []
        for row in self.cells:
            lines = []
            for i, d in enumerate(row):
                if d["text"] in (CHECK, CROSS, PARTIAL, DASH):
                    lines.append([d["text"]])
                else:
                    lines.append(metrics.wrap_text(d["text"], (widths[i] - 2 * pad_x) * SAFETY, size))
            self.row_lines.append(lines)
            self.row_h.append(max(max(len(l) for l in lines) * size * lh, size * lh) + 2 * pad_y)
        self.title_h = (title_size * lh + 10) if title else 0
        self.h = self.title_h + self.head_h + sum(self.row_h)
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "Table":
        self.x, self.y = x, y
        th, lh = self.th, metrics.line_ratio()
        with cv.group():
            if self.title:
                cv.text(x, y, self.title, size=self.title_size, color=th.deep)
            y0 = y + self.title_h
            tbl_h = self.head_h + sum(self.row_h)
            # zebra / custom cell fills first (behind)
            cy = y0 + self.head_h
            for ri, row in enumerate(self.cells):
                rh = self.row_h[ri]
                if self.zebra and ri % 2 == 1:
                    cv.rect(x + 1, cy, self.w - 2, rh, stroke="transparent", fill=th.soft, style="solid", sw=0,
                            round_=False, rough=0)
                cx = x
                for ci, d in enumerate(row):
                    cth = d.get("theme") or (self.first_col_theme.name if (ci == 0 and self.first_col_theme) else None)
                    if cth:
                        t2 = get_theme(cth)
                        cv.rect(cx + 1, cy + 1, self.col_w[ci] - 2, rh - 2, stroke="transparent", fill=t2.fill,
                                style="solid", sw=0, round_=False, rough=0, opacity=85)
                    cx += self.col_w[ci]
                cy += rh
            # header band
            hb = cv.rect(x, y0, self.w, self.head_h, stroke=th.stroke, fill=th.fill, style="solid", sw=2,
                         round_=False, rough=1)
            # outer border
            cv.rect(x, y0, self.w, tbl_h, stroke=th.stroke, fill="transparent", sw=2, round_=self.round_, rough=1,
                    link=self.link)
            # separators
            cx = x
            for i in range(len(self.col_w) - 1):
                cx += self.col_w[i]
                cv.line((cx, y0), (cx, y0 + tbl_h), stroke=th.stroke, sw=1, rough=1, opacity=70)
            cy = y0 + self.head_h
            for ri in range(len(self.row_h) - 1):
                cy += self.row_h[ri]
                cv.line((x, cy), (x + self.w, cy), stroke="#adb5bd", sw=1, rough=1, opacity=90)
            # text
            cx = x
            for ci, lines in enumerate(self.head_lines):
                cv.text(cx + self.pad_x, y0 + self.pad_y, "\n".join(lines), size=self.head_size, color=th.deep,
                        align=self.align[ci], w=self.col_w[ci] - 2 * self.pad_x)
                cx += self.col_w[ci]
            cy = y0 + self.head_h
            for ri, row in enumerate(self.cells):
                cx = x
                for ci, d in enumerate(row):
                    lines = self.row_lines[ri][ci]
                    if d["text"] in (CHECK, CROSS, PARTIAL, DASH):
                        draw_mark(cv, d["text"], cx + self.col_w[ci] / 2, cy + self.row_h[ri] / 2)
                    elif d["text"]:
                        color = d.get("color") or (self.first_col_theme.deep if (ci == 0 and self.first_col_theme) else INK)
                        cv.text(cx + self.pad_x, cy + self.pad_y, "\n".join(lines), size=self.size, color=color,
                                align=d.get("align", self.align[ci]), w=self.col_w[ci] - 2 * self.pad_x,
                                link=d.get("link"))
                    cx += self.col_w[ci]
                cy += self.row_h[ri]
        cv.register("table", x, y, self.w, self.h)
        return self


# ====================================================================== headings, sources, footer
def title_block(cv: Canvas, x: float, y: float, title: str, subtitle: Optional[str] = None, *, icon="foundry",
                w: Optional[float] = None, title_size=48, sub_size=22, icon_size=84) -> tuple[float, float]:
    """Big canvas title with logo; returns (right, bottom)."""
    with cv.group():
        tx = x
        if icon:
            place_icon(cv, icon, x, y, icon_size)
            tx = x + icon_size + 22
        tt = cv.text(tx, y - 2, title, size=title_size, color=INK)
        bottom = tt.bottom
        if subtitle:
            st = cv.text(tx + 2, tt.bottom + 2, subtitle, size=sub_size, color=MUTED)
            bottom = st.bottom
        bottom = max(bottom, y + (icon_size if icon else 0))
        right = max(tx + metrics.text_size(title, title_size)[0], x + (w or 0))
        cv.line((x, bottom + 14), (right, bottom + 14), stroke=INK, sw=2)
    return right, bottom + 14


def section_header(cv: Canvas, x: float, y: float, text: str, sub: Optional[str] = None, *, size=30,
                   color: str = INK, w: Optional[float] = None, underline=True, sub_size=16) -> tuple[float, float]:
    t = cv.text(x, y, text, size=size, color=color)
    bottom = t.bottom
    width = t.w
    if sub:
        s = cv.text(x + 2, t.bottom + 1, sub, size=sub_size, color=MUTED)
        bottom, width = s.bottom, max(width, s.w)
    if underline:
        cv.line((x, bottom + 6), (x + (w or width + 24), bottom + 6), stroke=color, sw=2)
        bottom += 8
    return x + (w or width), bottom


def sources(cv: Canvas, x: float, y: float, items: Sequence[tuple[str, str]], *, w: float = 1500, cols: int = 2,
            title: str = "Sources and further reading (Microsoft Learn)", size=14, theme="gray") -> Rect2:
    """Clickable citation list at the bottom of a canvas. items: (label, url)."""
    th = get_theme(theme)
    colw = (w - 40 - 24 * (cols - 1)) / cols
    entries = []
    for label, url in items:
        label, _ = metrics.sanitize(label)
        l1 = metrics.wrap_text(label, colw * SAFETY, size)
        l2 = metrics.wrap_text(short_url(url), colw * SAFETY, size - 2, metrics.MONO)
        h = len(l1) * size * metrics.line_ratio() + len(l2) * (size - 2) * metrics.line_ratio(metrics.MONO) + 8
        entries.append((l1, l2, url, h))
    per_col = -(-len(entries) // cols)
    col_heights = [sum(e[3] for e in entries[c * per_col:(c + 1) * per_col]) for c in range(cols)]
    title_h = 30
    H = title_h + max(col_heights, default=0) + 36
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
        cv.text(x + 20, y + 14, title, size=size + 4, color=th.deep)
        for c in range(cols):
            cx = x + 20 + c * (colw + 24)
            cy = y + 14 + title_h + 6
            for l1, l2, url, h in entries[c * per_col:(c + 1) * per_col]:
                cv.text(cx, cy, "\n".join(l1), size=size, color=INK)
                cy += len(l1) * size * metrics.line_ratio()
                cv.text(cx, cy, "\n".join(l2), size=size - 2, color=LINK, font=metrics.MONO, link=url)
                cy += len(l2) * (size - 2) * metrics.line_ratio(metrics.MONO) + 8
    r = Rect2()
    r.x, r.y, r.w, r.h = x, y, w, H
    cv.register("sources", x, y, w, H)
    return r


def footer(cv: Canvas, x: float, y: float, *, size=14) -> float:
    """Update stamp + disclaimer (call last; x,y = top-left)."""
    a = cv.text(x, y, f"Microsoft Foundry explainers  |  Updated {cv.updated_label}", size=size + 2, color=INK)
    b = cv.text(x, a.bottom + 2, "Unofficial community explainer - verify details against the linked Microsoft Learn pages.",
                size=size - 1, color=MUTED)
    return b.bottom


def legend(cv: Canvas, x: float, y: float, entries: Sequence[tuple[str, str]], *, size=15, gap=24) -> Rect2:
    """Row of (label, theme) colour swatches."""
    cx = x
    for label, th_name in entries:
        th = get_theme(th_name)
        cv.rect(cx, y + 2, 22, 16, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        t = cv.text(cx + 30, y, label, size=size)
        cx += 30 + t.w + gap
    r = Rect2()
    r.x, r.y, r.w, r.h = x, y, cx - x, 22
    return r


# ====================================================================== layout helpers
def row(cv: Canvas, x: float, y: float, blocks: Sequence, *, gap=28, equalize=True) -> tuple[float, float]:
    """Place blocks left->right; returns (right_edge, bottom_edge). equalize stretches all to the tallest."""
    hmax = max((b.h for b in blocks), default=0) if equalize else 0
    cx = x
    bottom = y
    for b in blocks:
        b.place(cv, cx, y, h=hmax) if equalize else b.place(cv, cx, y)
        cx += b.w + gap
        bottom = max(bottom, b.y + b.h)
    return cx - gap, bottom


def col(cv: Canvas, x: float, y: float, blocks: Sequence, *, gap=22) -> tuple[float, float]:
    """Place blocks top->bottom; returns (right_edge, bottom_edge)."""
    cy = y
    right = x
    for b in blocks:
        b.place(cv, x, cy)
        cy += b.h + gap
        right = max(right, b.x + b.w)
    return right, cy - gap


def grid(cv: Canvas, x: float, y: float, blocks: Sequence, cols: int, *, gap_x=28, gap_y=28,
         equalize=True) -> tuple[float, float]:
    """Place blocks in a grid (row-major); each row is stretched to its tallest block."""
    cy = y
    right = x
    for i in range(0, len(blocks), cols):
        chunk = blocks[i:i + cols]
        r, b = row(cv, x, cy, chunk, gap=gap_x, equalize=equalize)
        right = max(right, r)
        cy = b + gap_y
    return right, cy - gap_y
