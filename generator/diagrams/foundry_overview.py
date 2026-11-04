"""Microsoft Foundry platform overview - FLAGSHIP map: the AI factory (Build, Evaluate, Deploy, Operate, Govern).

Layout (in the spirit of Dan Friedman's Fabric overview): hero title + numbers -> ways in -> 1 BUILD (four colour-coded lanes of
icon tiles) -> the Foundry platform spine (core objects, hero, protocols) -> conveyor 2 Evaluate / 3 Deploy / 4 Operate /
5 Govern -> foundation rails -> runtime request path -> deprecation clock -> Why Foundry? and How to choose -> sources.
Tiles: no pill = GA (or no preview label in Learn); Preview / Part preview / Docs differ / Retiring pills mark the rest.
"""
from __future__ import annotations

from datetime import date
from math import ceil

from generator.xd import *
from generator.xd.icons import BADGES, ICON_DIR

META = dict(
    id="foundry-overview", title="Microsoft Foundry platform overview", section="1", group="Overview", order=1,
    description="The front-page map of Microsoft Foundry as an AI factory (Build, Evaluate, Deploy, Operate, Govern): every capability "
                "family as icon tiles with preview and retirement badges, the platform spine, foundation rails, a runtime request path, "
                "the deprecation clock, plus Why Foundry? and How to choose.",
    tags=["overview", "platform", "capabilities", "ai-factory", "agents", "models"],
)

# ------------------------------------------------------------------------------------------------ grid
W = 3560
GUT = 40
LW = 860                      # lane width: 4 lanes + 3 gutters = W
LPAD = 16
GAP = 14
LIN = LW - 2 * LPAD           # 828
LX = [i * (LW + GUT) for i in range(4)]
W2 = [760, 760, 800, 1120]    # conveyor lanes: Govern is double-width so all four finish at a similar height
LX2 = [sum(W2[:i]) + i * GUT for i in range(4)]
AS_OF = date(2026, 11, 3)


def L(label: str, path: str, base: str = "azure/foundry") -> tuple[str, str]:
    return (label, learn(path, base=base))


# ------------------------------------------------------------------------------------------------ icons
_SVG = {p.stem for p in ICON_DIR.glob("*.svg")} | {p.stem for p in ICON_DIR.glob("*.png")}


def _badge(cv, text, th_name, cx, y, size):
    """Text badge with a >= 12 px label (the kit's fallback shrinks below 12 px at small sizes)."""
    th = THEMES[th_name]
    fs = 0.42 * size
    while fs > 12 and metrics.line_width(text, fs) > size * 0.84:
        fs -= 1
    fs = max(fs, 12)
    tw, thh = metrics.text_size(text, fs)
    with cv.group():
        cv.rect(cx - size / 2, y, size, size, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        cv.text(cx - tw / 2, y + (size - thh) / 2, text, size=fs, color=th.deep)


def draw_icon(cv, spec, cx: float, y: float, size: float = 40) -> None:
    """spec: kit icon name | (text, theme) badge | list of specs drawn as a small strip centred on cx."""
    if spec is None:
        return
    if isinstance(spec, list):
        sz, gap = 30, 6
        total = len(spec) * sz + (len(spec) - 1) * gap
        x0 = cx - total / 2
        for i, nm in enumerate(spec):
            draw_icon(cv, nm, x0 + i * (sz + gap) + sz / 2, y + (size - sz) / 2, sz)
        return
    if isinstance(spec, tuple):
        _badge(cv, spec[0], spec[1], cx, y, size)
        return
    if spec in _SVG:
        place_icon(cv, spec, cx - size / 2, y, size)
    elif spec in BADGES:
        _badge(cv, BADGES[spec][0], BADGES[spec][1], cx, y, size)
    else:
        cv.warn(f"icon {spec!r} not found")


# ------------------------------------------------------------------------------------------------ status pills
ST = {
    "ga": dict(label="GA", pill="green", stroke=None, dash="solid"),
    "preview": dict(label="Preview", pill="orange", stroke="#e8590c", dash="dashed"),
    "limited": dict(label="Limited preview", pill="orange", stroke="#e8590c", dash="dashed"),
    "part": dict(label="Part preview", pill="yellow", stroke=None, dash="solid"),
    "differ": dict(label="Docs differ", pill="yellow", stroke="#f08c00", dash="dashed"),
    "retiring": dict(label="Retiring", pill="red", stroke="#e03131", dash="dashed"),
    "check": dict(label="Check docs", pill="gray", stroke="#868e96", dash="dashed"),
    "blog": dict(label="Blog only", pill="gray", stroke="#868e96", dash="dashed"),
}


def parse_status(st):
    if not st:
        return None
    key, text = (st if isinstance(st, tuple) else (st, None))
    d = dict(ST[key])
    if text:
        d["label"] = text
    return d


def pill_w(label: str, size: int = 12) -> float:
    return metrics.line_width(label, size) + 14


def draw_pill(cv, x, y, label, theme, *, size=12, dash="solid") -> tuple[float, float]:
    th = THEMES[theme]
    w, h = pill_w(label, size), size * 1.25 + 6
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0, dash=dash)
        cv.text(x + 7, y + 3, label, size=size, color=th.deep)
    return w, h


def dotted(cv, pts, *, color=INK, sw=3, head=None):
    """Dotted connector; a head is drawn as a short solid tip so it stays crisp."""
    if head is None:
        return arrow(cv, pts, dash="dotted", color=color, sw=sw, start_head=None, end_head=None)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    d = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1.0)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    tip = 18
    arrow(cv, list(pts[:-1]) + [(x2 - ux * tip, y2 - uy * tip)], dash="dotted", color=color, sw=sw, start_head=None,
          end_head=None)
    return arrow(cv, [(x2 - ux * tip, y2 - uy * tip), (x2, y2)], dash="solid", color=color, sw=sw, end_head="arrow")


def T(label, icon=None, sub=None, st=None, theme=None) -> dict:
    return dict(label=label, icon=icon, sub=sub, st=st, theme=theme)


# ------------------------------------------------------------------------------------------------ tiles and groups
class Tile(Rect2):
    """Icon tile: white card, icon, label, optional muted sub-label, status pill straddling the top edge."""

    def __init__(self, w, spec, theme, *, size=14, sub_size=12, icon_size=40):
        self.w, self.spec, self.size, self.sub_size, self.icon_size = w, spec, size, sub_size, icon_size
        self.th = THEMES[spec.get("theme") or theme]
        inner = (w - 12) * 0.965
        self.l_lines = metrics.wrap_text(metrics.sanitize(spec["label"])[0], inner, size)
        sub = spec.get("sub")
        self.s_lines = metrics.wrap_text(metrics.sanitize(sub)[0], inner, sub_size) if sub else []
        lh = metrics.line_ratio()
        self.h = (12 + icon_size + 6 + len(self.l_lines) * size * lh
                  + (len(self.s_lines) * sub_size * lh + 3 if self.s_lines else 0) + 9)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        st = parse_status(self.spec.get("st"))
        stroke = (st and st["stroke"]) or self.th.stroke
        dash = st["dash"] if st else "solid"
        lh = metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=stroke, fill="#ffffff", style="solid", sw=1.6, dash=dash)
            draw_icon(cv, self.spec.get("icon"), x + self.w / 2, y + 12, self.icon_size)
            ty = y + 12 + self.icon_size + 6
            cv.text(x + 6, ty, "\n".join(self.l_lines), size=self.size, color=INK, align="center", w=self.w - 12)
            ty += len(self.l_lines) * self.size * lh
            if self.s_lines:
                cv.text(x + 6, ty + 3, "\n".join(self.s_lines), size=self.sub_size, color=MUTED, align="center",
                        w=self.w - 12)
            if st:
                pw = pill_w(st["label"])
                draw_pill(cv, x + self.w - pw - 8, y - 11, st["label"], st["pill"])
        cv.register(f"tile:{self.spec['label']}", x, y, self.w, H)
        return self


class Group(Rect2):
    """Dotted panel with a title, a grid of Tiles (or a ChipFlow), optional bullets and Learn links."""

    def __init__(self, w, title, items, *, theme, cols=5, sub=None, src=(), pad=12, gap=10, title_size=19,
                 chips=False, foot=(), foot_size=15, fill="none", badge=None, tile_theme=None):
        self.w, self.title, self.sub, self.theme, self.pad, self.gap = w, title, sub, theme, pad, gap
        self.title_size, self.chips, self.fill, self.badge = title_size, chips, fill, badge
        self.src = list(src)
        lh = metrics.line_ratio()
        inner = w - 2 * pad
        self.inner = inner
        self.t_h = (title_size * lh + 6 + ((14 * lh + 2) if sub else 0) + 8) if title else 0
        if chips:
            self.flow = ChipFlow(items, inner, theme=theme, size=15, gap=8)
            self.body_h = self.flow.h
            self.tiles = []
        else:
            tw = (inner - (cols - 1) * gap) / cols
            self.tiles = [Tile(tw, spec, tile_theme or theme) for spec in items]
            self.th_ = max((t.h for t in self.tiles), default=0)
            self.cols = cols
            rows = ceil(len(self.tiles) / cols) if self.tiles else 0
            self.body_h = rows * self.th_ + max(rows - 1, 0) * gap
        self.foot = []
        fh = 0.0
        for t in foot:
            para = t.startswith("= ")
            txt = t[2:] if para else t
            lines = metrics.wrap_text(metrics.sanitize(txt)[0], (inner - (0 if para else 20)) * 0.965, foot_size)
            self.foot.append((para, lines))
            fh += len(lines) * foot_size * lh + 5
        self.foot_h = (fh + 12) if foot else 0
        self.src_lines = []
        sh = 0.0
        for label, url in self.src:
            lines = metrics.wrap_text(f"Learn: {label}", inner * 0.965, 12)
            self.src_lines.append(("\n".join(lines), url))
            sh += len(lines) * 12 * lh + 2
        self.src_h = (sh + 6) if self.src else 0
        self.foot_size = foot_size
        self.h = pad + self.t_h + self.body_h + self.foot_h + self.src_h + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        H = max(self.h, h or 0)
        lh = metrics.line_ratio()
        with cv.panel(x, y, title=self.title, sub=self.sub, theme=self.theme, style="dotted", fill=self.fill,
                      pad=self.pad, w=self.w, min_h=H, title_size=self.title_size, sub_size=14) as p:
            cy = p.iy
            if self.chips:
                self.flow.place(cv, p.ix, cy)
            else:
                tw = self.tiles[0].w if self.tiles else 0
                for i, t in enumerate(self.tiles):
                    r, c = divmod(i, self.cols)
                    t.place(cv, p.ix + c * (tw + self.gap), cy + r * (self.th_ + self.gap), h=self.th_)
            cy += self.body_h
            if self.foot:
                cy += 12
                for para, lines in self.foot:
                    if not para:
                        cv.ellipse(p.ix + 3, cy + self.foot_size * lh / 2 - 4, 9, 9, stroke=self.theme_stroke(), sw=2, rough=0)
                    cv.text(p.ix + (0 if para else 20), cy, "\n".join(lines), size=self.foot_size, color=INK)
                    cy += len(lines) * self.foot_size * lh + 5
            if self.src_lines:
                cy += 6
                for text, url in self.src_lines:
                    cv.text(p.ix, cy, text, size=12, color=LINK, link=url)
                    cy += (text.count("\n") + 1) * 12 * lh + 2
            if self.badge:
                st = parse_status(self.badge)
                draw_pill(cv, x + self.w - pill_w(st["label"]) - 12, y + 10, st["label"], st["pill"])
        self.x, self.y, self.w, self.h = p.x, p.y, p.w, p.h
        return self

    def theme_stroke(self) -> str:
        return THEMES[self.theme].stroke


class FlowGroup(Rect2):
    """Dotted panel holding a row of boxes joined by arrows. nodes = (label, sub, theme[, weight])."""

    def __init__(self, w, title, nodes, *, theme, sub=None, badge=None, src=(), pad=12, gap=34, size=16, sub_size=12,
                 foot=None, fill="none", title_size=19):
        self.w, self.title, self.sub, self.theme, self.pad, self.badge, self.fill = w, title, sub, theme, pad, badge, fill
        self.title_size, self.gap, self.src = title_size, gap, list(src)
        lh = metrics.line_ratio()
        inner = w - 2 * pad
        weights = [n[3] if len(n) > 3 else 1 for n in nodes]
        free = inner - gap * (len(nodes) - 1)
        self.boxes = [Box(free * wt / sum(weights), n[0], sub=n[1], theme=n[2], size=size, sub_size=sub_size, fill="hatch",
                          pad=8) for n, wt in zip(nodes, weights)]
        self.bh = max(b.h for b in self.boxes)
        self.t_h = title_size * lh + 6 + ((14 * lh + 2) if sub else 0) + 8
        self.foot_lines = metrics.wrap_text(metrics.sanitize(foot)[0], inner * 0.965, 14) if foot else []
        self.foot_h = (len(self.foot_lines) * 14 * lh + 8) if foot else 0
        self.src_lines = []
        sh = 0.0
        for label, url in self.src:
            lines = metrics.wrap_text(f"Learn: {label}", inner * 0.965, 12)
            self.src_lines.append(("\n".join(lines), url))
            sh += len(lines) * 12 * lh + 2
        self.src_h = (sh + 6) if self.src else 0
        self.h = pad + self.t_h + self.bh + self.foot_h + self.src_h + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        H = max(self.h, h or 0)
        lh = metrics.line_ratio()
        with cv.panel(x, y, title=self.title, sub=self.sub, theme=self.theme, style="dotted", fill=self.fill, pad=self.pad,
                      w=self.w, min_h=H, title_size=self.title_size, sub_size=14) as p:
            cx = p.ix
            for b in self.boxes:
                b.place(cv, cx, p.iy, h=self.bh)
                cx += b.w + self.gap
            for a, b in zip(self.boxes, self.boxes[1:]):
                connect(cv, a, b, a_side="right", b_side="left", end_head="arrow", sw=2, gap=3)
            cy = p.iy + self.bh
            if self.foot_lines:
                cv.text(p.ix, cy + 8, "\n".join(self.foot_lines), size=14, color=MUTED)
                cy += self.foot_h
            if self.src_lines:
                cy += 6
                for text, url in self.src_lines:
                    cv.text(p.ix, cy, text, size=12, color=LINK, link=url)
                    cy += (text.count("\n") + 1) * 12 * lh + 2
            if self.badge:
                st = parse_status(self.badge)
                draw_pill(cv, x + self.w - pill_w(st["label"]) - 12, y + 10, st["label"], st["pill"])
        self.x, self.y, self.w, self.h = p.x, p.y, p.w, p.h
        return self


class Stack(Rect2):
    """Blocks stacked vertically (used as one cell of a side-by-side row)."""

    def __init__(self, blocks, gap=GAP):
        self.blocks, self.gap = blocks, gap
        self.w = max(b.w for b in blocks)
        self.h = sum(b.h for b in blocks) + gap * (len(blocks) - 1)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        extra = max(0.0, (h or 0) - self.h)
        cy = y
        for i, b in enumerate(self.blocks):
            b.place(cv, x, cy, h=(b.h + extra) if i == len(self.blocks) - 1 else None)
            cy += b.h + self.gap
        self.x, self.y = x, y
        self.h = cy - self.gap - y
        return self


class Lane:
    """One colour-coded lane: solid head card + stacked blocks (a tuple/list in `blocks` = side-by-side row)."""

    def __init__(self, x, theme, marker, title, sub, icon, blocks, *, w=LW):
        self.x, self.w, self.theme, self.marker, self.blocks = x, w, theme, marker, blocks
        self.head = Card(w - 2 * LPAD, title, [], theme=theme, subtitle=sub, icon=icon, fill="solid", title_size=27,
                         sub_size=18, pad=14, icon_size=46)
        self.panel = None

    def rows(self):
        return [list(b) if isinstance(b, (list, tuple)) else [b] for b in self.blocks]

    def height(self) -> float:
        h = LPAD + self.head.h
        for r in self.rows():
            h += GAP + max(b.h for b in r)
        return h + LPAD

    def place(self, cv, y, H):
        spare = max(0.0, H - self.height())
        rows = self.rows()
        with cv.panel(self.x, y, theme=self.theme, style="dotted", fill="soft", pad=LPAD, w=self.w, min_h=H, sw=2.5) as p:
            self.head.place(cv, p.ix, p.iy)
            numbered(cv, self.head.right - 34, self.head.y + 34, self.marker, theme=self.theme, d=46, size=22)
            cy = p.iy + self.head.h + GAP
            for i, r in enumerate(rows):
                rh = max(b.h for b in r) + (spare if i == len(rows) - 1 else 0)
                cx = p.ix
                for b in r:
                    b.place(cv, cx, cy, h=rh)
                    cx += b.w + GAP
                cy += rh + GAP
        self.panel = p
        return p


class Ladder(Rect2):
    """Staircase from a single model call to a hosted agent."""

    def __init__(self, w, title, steps, *, theme="green", pad=12, gap=38, rise=24, src=()):
        self.w, self.title, self.theme, self.pad, self.rise, self.gap, self.src = w, title, theme, pad, rise, gap, list(src)
        inner = w - 2 * pad
        n = len(steps)
        bw = (inner - (n - 1) * gap) / n
        self.boxes = [Box(bw, lab, sub=sub, theme=th, size=16, sub_size=12, fill="hatch", pad=8) for lab, sub, th in steps]
        self.bh = max(b.h for b in self.boxes)
        lh = metrics.line_ratio()
        self.t_h = 19 * lh + 6 + 8
        sh = 0.0
        self.src_lines = []
        for label, url in self.src:
            lines = metrics.wrap_text(f"Learn: {label}", inner * 0.965, 12)
            self.src_lines.append(("\n".join(lines), url))
            sh += len(lines) * 12 * lh + 2
        self.src_h = (sh + 6) if self.src else 0
        self.h = pad + self.t_h + (n - 1) * rise + self.bh + 34 + self.src_h + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        H = max(self.h, h or 0)
        n = len(self.boxes)
        lh = metrics.line_ratio()
        with cv.panel(x, y, title=self.title, theme=self.theme, style="dotted", fill="none", pad=self.pad, w=self.w,
                      min_h=H, title_size=19) as p:
            base = p.iy + (n - 1) * self.rise
            bw = self.boxes[0].w
            for i, b in enumerate(self.boxes):
                b.place(cv, p.ix + i * (bw + self.gap), base - i * self.rise, h=self.bh)
            for a, b in zip(self.boxes, self.boxes[1:]):
                connect(cv, a, b, a_side="right", b_side="left", end_head="arrow", sw=2, gap=3)
            ly = base + self.bh + 8
            cv.text(p.ix, ly, "least to manage", size=14, color=MUTED)
            t = "most control"
            cv.text(p.ix + self.w - 2 * self.pad - metrics.line_width(t, 14), ly, t, size=14, color=MUTED)
            mid = "start declarative, move to code as needs grow"
            cv.text(p.ix + (self.w - 2 * self.pad - metrics.line_width(mid, 14)) / 2, ly, mid, size=14, color=THEMES[self.theme].deep)
            cy = ly + 22
            if self.src_lines:
                for text, url in self.src_lines:
                    cv.text(p.ix, cy, text, size=12, color=LINK, link=url)
                    cy += (text.count("\n") + 1) * 12 * lh + 2
        self.x, self.y, self.w, self.h = p.x, p.y, p.w, p.h
        return self


# ------------------------------------------------------------------------------------------------ stage chevrons
def chevron(cv, x, y, w, h, title, sub, theme, *, notch=True, tsize=34, ssize=17, left=False, marker=None):
    th = THEMES[theme]
    d = h * 0.42
    if notch:
        pts = [(x, y), (x + w - d, y), (x + w, y + h / 2), (x + w - d, y + h), (x, y + h), (x + d, y + h / 2), (x, y)]
        cx = x + w / 2
    else:
        pts = [(x, y), (x + w - d, y), (x + w, y + h / 2), (x + w - d, y + h), (x, y + h), (x, y)]
        cx = x + (w - d) / 2
    cv.poly(pts, kind="line", stroke=th.stroke, fill=th.fill, fill_style="hachure", sw=3)
    lh = metrics.line_ratio()
    block_h = tsize * lh + ssize * lh
    ty = y + (h - block_h) / 2
    if left:
        tx = x + 110
        numbered(cv, x + 62, y + h / 2, marker, theme=theme, d=62, size=32)
        cv.text(tx, ty, title, size=tsize, color=th.deep)
        cv.text(tx + 2, ty + tsize * lh, sub, size=ssize, color=INK)
    else:
        cv.text(cx - metrics.line_width(title, tsize) / 2, ty, title, size=tsize, color=th.deep)
        cv.text(cx - metrics.line_width(sub, ssize) / 2, ty + tsize * lh, sub, size=ssize, color=INK)


# ============================================================================================== 0. title, key, numbers
SUBTITLE = ("Models + Agents + Tools, under one Azure resource - every capability family on one AI-factory map: "
            "Build, Evaluate, Deploy, Operate, Govern  |  as of 2026-11-03")


def legend_panel(cv, x, y, w, h):
    with cv.panel(x, y, title="How to read this map", theme="gray", style="dotted", fill="none", pad=18, w=w, min_h=h,
                  title_size=22) as p:
        cy = p.iy - 2
        legend(cv, p.ix, cy, [("Models", "blue"), ("Agents", "green"), ("Tools", "orange"), ("Knowledge + memory", "teal"),
                              ("Evaluation + observability", "violet"), ("Guardrails", "pink")], size=14, gap=16)
        legend(cv, p.ix, cy + 28, [("Identity + security", "red"), ("Network", "indigo"), ("Governance", "grape"),
                                   ("Data", "cyan"), ("Cost + capacity", "yellow"), ("Neutral", "gray")], size=14, gap=16)
        cy += 68
        cx = p.ix
        for kind, text in (("ga", "stated GA (headline items)"), ("preview", "preview (dashed tile)"),
                           ("part", "GA core, parts preview")):
            st = ST[kind]
            pw, _ = draw_pill(cv, cx, cy, st["label"], st["pill"])
            t = cv.text(cx + pw + 8, cy + 2, text, size=14, color=INK)
            cx += pw + 8 + t.w + 26
        cy += 32
        cx = p.ix
        for kind, text in (("differ", "Learn pages disagree"), ("retiring", "retirement date set"), ("check", "status not stated")):
            st = ST[kind]
            pw, _ = draw_pill(cv, cx, cy, st["label"], st["pill"])
            t = cv.text(cx + pw + 8, cy + 2, text, size=14, color=INK)
            cx += pw + 8 + t.w + 26
        cv.text(cx, cy + 2, "no pill = no preview label in Learn", size=14, color=INK)
        cy += 34
        foot = ("Build > Evaluate > Deploy > Operate > Govern is our diagram, not a Learn term (Learn says Discover - Build - "
                "Operate; the Build 2025 blog says AI factory). Preview and GA labels drift weekly: always follow the Learn links.")
        t = cv.text(p.ix, cy, "\n".join(metrics.wrap_text(foot, (w - 36) * 0.965, 14)), size=14, color=MUTED)
        cv.text(p.ix, t.bottom + 4, "Blog: Build recap, new Azure AI Foundry resource, developer APIs and tools (AI factory wording)", size=12,
                color=LINK, link="https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/build-recap-new-azure-ai-foundry-resource-developer-apis-and-tools/4427241")
    return p


def top_strip(cv, y) -> float:
    leg_w, stat_w, q_w = 1000, 1520, 960
    x_stat = leg_w + 40
    x_q = x_stat + stat_w + 40
    cv.text(x_stat, y, "Foundry by the numbers  (Learn, as of 2026-11-03)", size=22, color="#343a40")
    stats = [
        ("10,000+", "models in the catalog, about 50 new a month", "blue", None, L("Foundry Models", "concepts/foundry-models-overview")),
        ("1,400+", "tools in the portal tool catalog", "orange", None, L("Navigate from classic", "how-to/navigate-from-classic")),
        ("30 + 2", "regions for projects: commercial + Azure Government", "gray", None, L("Region support", "reference/region-support")),
        ("31", "regions list hosted agents", "green", None, L("Hosted agents", "agents/concepts/hosted-agents")),
        ("5", "Foundry RBAC roles, incl. Agent Consumer", "red", None, L("RBAC for Foundry", "concepts/rbac-foundry")),
        ("9", "model deployment types", "blue", None, L("Deployment types", "foundry-models/concepts/deployment-types")),
        ("79", "tools in the Foundry MCP Server", "orange", "preview", L("MCP available tools", "mcp/available-tools")),
    ]
    cards = [Card(200, big, [f"= {cap}"], theme=th, align="center", title_size=40, body_size=14, pad=12, fill="hatch", gap=4,
                  para_gap=4, src=[s]) for big, cap, th, bd, s in stats]
    _, sb = row(cv, x_stat, y + 38, cards, gap=20)
    pw = pill_w("Preview")
    draw_pill(cv, cards[-1].right - pw - 10, cards[-1].y - 11, "Preview", "orange")
    quote = Note(q_w, "Microsoft Foundry unifies agents, models and tools under a single management grouping with tracing, "
                      "monitoring, evaluations and customizable enterprise setup; unified RBAC, networking and policies under one "
                      "Azure resource provider namespace.", kind="quote", title="What is Foundry? (Learn wording)", size=16,
                 src=[L("What is Microsoft Foundry?", "what-is-foundry")])
    names = Note(q_w, "Microsoft Foundry was Azure AI Foundry, before that Azure AI Studio. Foundry Tools was Azure AI Services. "
                      "Foundry (classic) is the previous portal with hub-based projects. The Azure resource type did not change: "
                      "Microsoft.CognitiveServices/accounts, kind AIServices.", kind="info", title="Names to use", size=15,
                 src=[L("Navigate from Foundry classic", "how-to/navigate-from-classic")])
    stack = Stack([quote, names], gap=14)
    h = max(sb - y, stack.h, 262)
    stack.place(cv, x_q, y, h=h)
    legend_panel(cv, 0, y, leg_w, h)
    return y + h


# ============================================================================================== 0b. one-glance factory strip
def factory_strip(cv, y) -> float:
    stages = [("1  BUILD", "Raw materials to assembly line: models, agents, tools, knowledge", "gray"),
              ("2  EVALUATE", "QA line: measure quality, probe risk, optimize", "violet"),
              ("3  DEPLOY", "Dispatch dock: version, publish, ship", "green"),
              ("4  OPERATE", "Control tower: trace, monitor, keep improving", "violet"),
              ("5  GOVERN", "Compliance office: guardrails, policy, fleet view", "grape")]
    h = 104
    d = h * 0.42
    gap = 8
    wc = (W + 4 * (d - gap)) / 5
    for i, (t, s, th) in enumerate(stages):
        chevron(cv, i * (wc - d + gap), y, wc, h, t, s, th, notch=i > 0, tsize=36, ssize=18)
    by = y + h + 16
    with cv.panel(0, by, theme="gray", style="dotted", fill="none", pad=11, w=W) as p:
        t = cv.text(p.ix + 6, p.iy + 2, "Rails under every stage:", size=19, color="#343a40")
        cx = p.ix + 6 + t.w + 18
        for lab, th in (("Identity and access", "red"), ("Network", "indigo"), ("Data and keys", "cyan"),
                        ("Resource model and cost", "yellow")):
            c = Chip(lab, theme=th, size=17)
            c.place(cv, cx, p.iy - 2)
            cx += c.w + 12
        t2 = cv.text(cx + 40, p.iy + 2, "Protocols on the wire:", size=19, color="#343a40")
        cx = cx + 40 + t2.w + 18
        for lab in ("Responses", "Invocations", "Activity", "A2A", "MCP", "OpenAPI"):
            c = Chip(lab, theme="gray", size=17)
            c.place(cv, cx, p.iy - 2)
            cx += c.w + 12
        t3 = cv.text(cx + 40, p.iy + 2, "Foundry Tools shelf:", size=19, color="#343a40")
        cx = cx + 40 + t3.w + 18
        for lab in ("Speech", "Language", "Translator", "Vision", "Document Intelligence", "Content Understanding", "Content Safety"):
            c = Chip(lab, theme="orange" if lab != "Content Safety" else "pink", size=17)
            c.place(cv, cx, p.iy - 2)
            cx += c.w + 12
    return p.bottom


# ============================================================================================== 1. ways in
def ways_in(cv, y):
    avail = W - 2 * 18 - 2 * 20
    tw = int((avail - 202) / 16)
    th_ = dict(theme="gray", gap=10)

    def g(title, tiles, src):
        n = len(tiles)
        return Group(n * tw + (n - 1) * 10 + 24, title, tiles, cols=n, src=src, **th_)

    human = g("Human surfaces", [
        T("Foundry portal", "foundry", "ai.azure.com, New Foundry toggle", st="ga"),
        T("Playgrounds", "browser", "model, agents, images; video is preview"),
        T("VS Code Foundry Toolkit", "vscode", "Agent Builder, Inspector, evals, traces", st="part"),
        T("Foundry Canvas", "copilot", "GitHub Copilot App side panel", st="preview"),
        T("Templates and samples", "template-specs", "solution + agent templates, GitHub samples"),
    ], [L("Playgrounds", "concepts/concept-playgrounds"), L("Foundry Toolkit for VS Code", "how-to/develop/get-started-projects-visual-studio-code"),
        L("Foundry Canvas", "agents/concepts/foundry-canvas")])
    code = g("Code surfaces: one project endpoint", [
        T("Foundry SDKs 2.x", ["python", "dotnet", "js", "java"], "azure-ai-projects: project client + OpenAI client"),
        T("OpenAI + Anthropic SDKs", ["openai", "claude"], "/openai/v1 and the /anthropic Messages route"),
        T("Foundry Tools SDKs", "ai-services", "Vision, Speech, Language, Translator"),
        T("LangChain / LangGraph", "langgraph", "langchain-azure-ai"),
        T("REST v1", "rest", "/openai/v1 routes, no api-version"),
        T("ARM, Bicep, Terraform", "code", "Microsoft.CognitiveServices/accounts"),
    ], [L("Foundry SDK overview", "how-to/develop/sdk-overview"), L("Foundry Models endpoints", "foundry-models/concepts/endpoints"),
        L("LangChain and LangGraph", "how-to/develop/langchain"),
        L("Foundry REST API reference (v1)", "rest/api/microsoft-foundry/?view=rest-microsoft-foundry-v1", base="")])
    auto = g("Automation and AI-assisted", [
        T("azd + azd ai", "azd", "scaffold, run, test, deploy agents", st="preview"),
        T("Foundry DevPack", ("Pack", "blue"), "one-command installer", st="preview"),
        T("Foundry Skill + coding agents", "github", "GitHub Copilot, Claude Code"),
        T("Foundry MCP Server", "mcp", "79 tools at mcp.ai.azure.com", st="preview"),
        T("Claude Code and Desktop", "claude", "point Anthropic tooling at Foundry"),
    ], [L("azd for agents", "agents/concepts/cli-agent-development"), L("Install the CLI and SDK (DevPack)", "how-to/develop/install-cli-sdk"),
        L("Foundry MCP Server", "mcp/get-started")])
    h = max(human.h, code.h, auto.h)
    with cv.panel(0, y, title="Ways in: the build surfaces", sub="portal, editors, SDKs, CLI and AI-assisted - all talk to the same Foundry project",
                  theme="gray", style="dotted", fill="soft", pad=18, w=W, title_size=28, sub_size=16) as p:
        x = p.ix
        for blk in (human, code, auto):
            blk.place(cv, x, p.iy, h=h)
            x += blk.w + 20
    return p


# ============================================================================================== 2. BUILD lanes
def lane_models(x) -> Lane:
    disc = Group(LIN, "Discover and compare", [
        T("Model catalog", "cubes", "10,000+ models, ~50 new a month", st="ga"),
        T("Sold by Azure", "openai", "Microsoft terms, support and SLAs"),
        T("Partners and community", "marketplace", "Marketplace, provider support"),
        T("Leaderboards", "metrics", "compare quality, cost, performance", st="preview"),
        T("Instant access", "globe", "no deployment, West US 3 only", st="preview"),
    ], theme="blue", src=[L("Foundry Models overview", "concepts/foundry-models-overview"),
                          L("Benchmarks and leaderboards", "concepts/model-benchmarks")])
    fam = Group(LIN, "Model families (sold by Azure, partners and community)", [
        Chip("OpenAI GPT-6.1, GPT-6, GPT-5.x", theme="blue", size=15, icon="openai"),
        Chip("gpt-oss", theme="blue", size=15), Chip("Claude", theme="blue", size=15), Chip("Llama", theme="blue", size=15),
        Chip("DeepSeek", theme="blue", size=15), Chip("Mistral", theme="blue", size=15), Chip("Cohere", theme="blue", size=15),
        Chip("Grok (SpaceXAI)", theme="blue", size=15), Chip("MAI", theme="blue", size=15), Chip("FLUX", theme="blue", size=15),
        Chip("Fireworks", theme="blue", size=15),
        Chip("Hugging Face (preview)", theme="orange", size=15, dash="dashed"),
        Chip("Healthcare AI (limited preview)", theme="orange", size=15, dash="dashed"),
        Chip("Foundry Local (blog only)", theme="gray", size=15, dash="dashed"),
    ], theme="blue", chips=True, src=[L("Models sold by Azure", "foundry-models/concepts/models-sold-directly-by-azure"),
                                      L("Models from partners and community", "foundry-models/concepts/models-from-partners")])
    dep = Group(LIN, "Deploy and capacity", [
        T("Deployment types", "deployment-environments", "9 types: Global, Data Zone, regional"),
        T("Model router", "traffic-manager", "best-fit model per request; session affinity preview", st="part"),
        T("Provisioned (PTU)", "reservations", "reserved throughput, spillover"),
        T("Batch and Flex", "batch", "50% off; Flex is preview"),
        T("Managed compute", "vm", "A100, H100, MI300X for open models", st="preview"),
        T("Quota and regions", "quotas", "per subscription, region, model"),
        T("Model lifecycle", "versions", "versions, upgrades, retirements"),
    ], theme="blue", cols=4, src=[L("Deployment types", "foundry-models/concepts/deployment-types"), L("Model router", "openai/concepts/model-router")])
    tw = 146
    cust = Group(2 * tw + 10 + 24, "Customize", [
        T("Fine-tuning", "ml", "SFT, DPO, RFT, vision, tools", st="ga"),
        T("Programmed training", "code", "code-driven; access approval", st="preview"),
    ], theme="blue", cols=2, src=[L("Fine-tuning overview", "fine-tuning/overview")])
    voice = Group(3 * tw + 20 + 24, "Voice and realtime", [
        T("GPT-Live", "speech", "full-duplex voice, delegation"),
        T("Realtime 2.1", "openai", "WebRTC, WebSocket, SIP"),
        T("Voice Live API", "speech", "managed STT + LLM + TTS + avatar"),
    ], theme="blue", cols=3, src=[L("GPT-Live", "openai/concepts/gpt-live"), L("Realtime 2.1", "openai/concepts/realtime-2")])
    note = Note(LIN, "Call a deployment by name on one endpoint. The Responses API works with Azure OpenAI models and the Foundry "
                     "Models sold by Azure that support it (else 400 Model not supported: use Chat Completions). Claude uses the "
                     "separate /anthropic Messages route. Decisions API (/openai/v1/decisions): typed, non-generative decisions; "
                     "gpt-6-luna only, rolling out.",
                kind="info", title="One endpoint, a deployment name as model", size=15,
                src=[L("Foundry Models endpoints", "foundry-models/concepts/endpoints")])
    return Lane(x, "blue", "1a", "Foundry Models", "Choose, deploy and tune models", "openai",
                [disc, fam, dep, (cust, voice), note])


def lane_agents(x) -> Lane:
    types = Group(LIN, "Agent types", [
        T("Prompt agent", "agent", "declarative: instructions, model, tools", st="ga"),
        T("Hosted agent", "container-apps", "your code in a sandbox per session", st="ga"),
        T("Voice prompt agent", "speech", "Voice Live, WebSocket, telephony", st="preview"),
        T("Autopilot", "m365", "own M365 identity, Frontier program", st="preview"),
        T("Workflows", "workflow", "preview; use Microsoft Agent Framework", st=("retiring", "Retires 2026-12-01")),
        T("Copilot harness", "copilot", "file, shell, web-fetch, subagents", st="preview"),
        T("Long-running agents", "scheduler", "durable, steerable, human approval", st="preview"),
    ], theme="green", cols=4, src=[L("Agent Service overview", "agents/overview"), L("Prompt agents", "agents/concepts/prompt-agents"),
                                   L("Autopilots", "agents/concepts/autopilot-overview")])
    run = Group(LIN, "Run, trigger and connect", [
        T("Responses API", "api", "stateful: conversations, items, background"),
        T("Routines", "scheduler", "timer, schedule, GitHub, Teams triggers", st="ga"),
        T("A2A", "a2a", "call or expose agents, v1.0", st="ga"),
        T("Agent identity", "managed-identity", "Entra Agent ID per agent; OBO preview", st="part"),
        T("Agent Framework", ("MAF", "green"), "open source, for hosted agents"),
    ], theme="green", src=[L("Routines", "agents/concepts/routines"), L("Agent identity", "agents/concepts/agent-identity")])
    ladder = Ladder(LIN, "From one model call to your own code", [
        ("Model call", "send a prompt to a deployment", "blue"),
        ("Ephemeral agent", "definition lives in your app code", "teal"),
        ("Prompt agent", "Foundry runs it, nothing to host", "green"),
        ("Hosted agent", "your code in Foundry's runtime", "green"),
    ], src=[L("Start with your goal", "concepts/capabilities")])
    hosted = Group(LIN, "Hosted agents in brief", [], theme="green", cols=1, fill="soft", foot=[
        "Protocols: Responses, Invocations, Invocations (WebSocket), Activity; an agent can expose several",
        "Per-session VM-isolated sandbox, Entra agent identity, 0.5, 1 or 2 vCPU, idle timeout 2-240 min (default 15)",
        "Ship a container image or a .zip of source (Foundry builds the image); private ACR for projects created after 2026-06-25",
    ], src=[L("Hosted agents", "agents/concepts/hosted-agents")])
    limits = Note(LIN, "Concurrent hosted-agent sessions per subscription per region: 2,000 in Canada Central, East US 2, Japan East, "
                       "North Central US, South Africa North, Southeast Asia and Sweden Central, otherwise 1,000 (idle or stopped "
                       "sessions do not count). Up to 128 tools and 1,000 versions per agent.", kind="info",
                  title="Default limits (as of 2026-11-03)", size=15,
                  src=[L("Agent Service limits, quotas and regions", "agents/concepts/limits-quotas-regions")])
    return Lane(x, "green", "1b", "Foundry Agent Service", "Build agents: declarative to full code", "agent",
                [types, run, ladder, hosted, limits])


def lane_tools(x) -> Lane:
    flow = FlowGroup(LIN, "Toolbox: define tools once, serve one MCP endpoint", [
        ("Agents and MCP clients", "prompt and hosted agents, Agent Framework, LangGraph, GitHub Copilot", "green", 1),
        ("Toolbox", "central auth, guardrails, immutable versions (promote a default), tool search", "orange", 1.25),
        ("Tools and skills", "MCP servers, OpenAPI, built-in tools, skills", "orange", 1),
    ], theme="orange", gap=34, badge=("part", "GA hosted, preview prompt"), src=[L("Toolbox overview", "agents/concepts/toolbox-overview")])
    tools = Group(LIN, "Tools an agent can call", [
        T("MCP servers", "mcp", "remote, managed, bring your own", st="part"),
        T("Tool search", "search", "tool_search + call_tool meta-tools", st="ga"),
        T("Function calling", "code", "your functions, run client-side"),
        T("OpenAPI", "api", "any REST API from a spec"),
        T("Code interpreter", "python", "sandbox; custom runtime is preview"),
        T("File search", "files", "managed vector stores"),
        T("Web search", "bing", "Web Search, Bing grounding"),
        T("Azure AI Search", "ai-search", "index as agent knowledge"),
        T("Browser automation", "browser", "Playwright Workspaces, live view", st="differ"),
        T("Computer use", "dev-box", "operate a virtual computer UI", st="preview"),
        T("Image generation", "image", "from inside an agent", st="preview"),
        T("SharePoint", "sharepoint", "ground answers in SharePoint", st="preview"),
        T("Skills", ("Skill", "orange"), "reusable, versioned behavior", st="preview"),
        T("Azure Functions", "functions", "queue-based tool", st="differ"),
    ], theme="orange", src=[L("MCP tool", "agents/how-to/tools/model-context-protocol"), L("Web search overview", "agents/how-to/tools/web-overview"),
                            L("Tool search", "agents/how-to/tools/tool-search")])
    cat = Group(LIN, "Catalogs and governance", [
        T("Tool catalog", "cubes", "1,400+ tools; check each label"),
        T("Private catalogs", "marketplace", "private tool and skill catalogs", st="preview"),
        T("MCP governance", "apim", "route MCP tools via AI gateway", st="preview"),
        T("Reminder tool", "scheduler", "a hosted agent schedules itself", st="preview"),
    ], theme="orange", cols=4, src=[L("Tool best practices", "agents/concepts/tool-best-practice")])
    note = Note(LIN, "MCP authentication: key, Entra agent or project identity, OAuth identity passthrough or OBO, or "
                     "unauthenticated. API keys are not accepted for agents, evaluations or Toolbox (auth matrix). Web Search and "
                     "Grounding with Bing are first-party consumption services: the DPA does not apply and data leaves your "
                     "compliance and geography boundary.",
                kind="info", title="Credentials and data boundaries", size=15,
                src=[L("Tool authentication", "agents/how-to/tools/tool-authentication")])
    drift = Note(LIN, "Toolboxes are GA for hosted agents; for prompt agents they are preview per the Sept 2026 blog, and the "
                      "REST examples still send Toolboxes=V1Preview. Browser automation and Azure Functions show conflicting "
                      "labels across Learn pages (see the Docs differ card below).", kind="warn", title="Docs disagree on tool status", size=15)
    return Lane(x, "orange", "1c", "Toolbox, tools and MCP", "Equip agents: define once, use everywhere", "toolbox",
                [flow, tools, cat, note, drift])


def lane_knowledge(x) -> Lane:
    iq = Group(LIN, "Microsoft IQ: a unified intelligence layer for enterprise AI", [
        T("Foundry IQ", "iq", "curated knowledge: knowledge bases + agentic retrieval", st=("part", "Partial GA")),
        T("Fabric IQ", "fabric", "live state of the business: ontology over OneLake", st="preview"),
        T("Work IQ", "m365", "how people work: mail, meetings, files, chats via A2A", st="preview"),
        T("Web IQ", ("Web", "cyan"), "fresh web, news, images, video: REST, MCP, SDK", st=("part", "Some APIs beta")),
    ], theme="teal", cols=4, src=[L("Foundry IQ", "agents/concepts/what-is-foundry-iq"), L("Microsoft IQ documentation", "microsoft-iq/", base=""),
                                  L("Web IQ overview", "web-iq/overview", base="")])
    blocks = Group(LIN, "Retrieval building blocks", [
        T("Vector stores", "files", "managed: parse, chunk, embed, search"),
        T("Azure AI Search", "ai-search", "index as agent knowledge: keyword, vector, hybrid"),
        T("Agentic retrieval", "search", "LLM plans queries, parallel searches"),
        T("RAG patterns", "learn", "ground responses in your content"),
    ], theme="teal", cols=4, src=[L("Vector stores", "agents/concepts/vector-stores"),
                                  L("Retrieval-augmented generation", "concepts/retrieval-augmented-generation")])
    detail = Group(LIN, "Foundry IQ in brief", [], theme="teal", cols=1, fill="soft", foot=[
        "Knowledge base = knowledge sources (Blob, SharePoint, OneLake, public web) + agentic retrieval: an LLM plans queries, runs parallel searches, returns citations",
        "Honors ACLs and Purview labels; runs under the caller's Entra identity",
        "Retrieval reasoning effort: minimal, low or medium; connects to Copilot Studio",
        "Only a few uploaded files? File search is the lighter option",
        "Web IQ is its own Azure resource (paid subscription, Azure credits do not work); your app calls it directly",
        "Microsoft IQ hub on Learn: Work IQ, Fabric IQ, Foundry IQ, Web IQ",
    ])
    mem = FlowGroup(LIN, "Memory: managed long-term memory", [
        ("Conversation", "turns and items", "gray", 1),
        ("Extraction", "key facts and preferences", "teal", 1),
        ("Consolidation", "merge duplicates, resolve conflicts", "teal", 1.1),
        ("Memory store", "user profile, chat summary, procedural", "teal", 1.1),
        ("Retrieval", "relevant memories per turn", "green", 1),
    ], theme="teal", gap=26, badge="preview", size=15,
        foot="Types: user profile, chat summary, procedural; item CRUD, default TTL, remember and forget commands.",
        src=[L("Memory", "agents/concepts/what-is-memory")])
    ft = Group(LIN, "Foundry Tools: prebuilt AI APIs (formerly Azure AI Services)", [
        T("Speech", "speech", "STT, TTS, avatar, Voice Live"),
        T("Language", "language", "PII, health, NER; parts retiring"),
        T("Translator", "translator", "text + documents; resource-level only"),
        T("Vision", "vision", "image analysis, OCR, Face"),
        T("Document Intelligence", "doc-intelligence", "documents to structured data"),
        T("Content Understanding", "applied-ai", "multimodal to structured; BYO storage", st="differ"),
        T("Content Safety", "content-safety", "harm detection, Prompt Shields", theme="pink"),
    ], theme="orange", cols=4, foot=["= On the same Foundry resource (kind AIServices) or as single-service kinds."],
        src=[L("What are Foundry Tools?", "azure/ai-services/what-are-ai-services", base="")])
    return Lane(x, "teal", "1d", "Knowledge, memory and Foundry Tools", "Ground agents in data, users and the web", "ai-search",
                [iq, detail, blocks, mem, ft])


# ============================================================================================== 3. stage lanes
def lane_evaluate(x, w=LW) -> Lane:
    inner = w - 2 * LPAD
    measure = Group(inner, "Measure", [
        T("Built-in evaluators", "metrics", "general, RAG, safety, agent, rubric", st="ga"),
        T("Custom evaluators", "code", "prompt- or code-based", st="preview"),
        T("Datasets", "files", "bring, synthetic, from traces"),
        T("Agent evaluation", "agent", "trajectory, tool calls, task completion"),
        T("Human evaluation", "users", "structured human judgments", st="preview"),
        T("Cluster analysis", "cubes", "group failures by root cause", st="preview"),
    ], theme="violet", cols=3, src=[L("Evaluation overview", "concepts/evaluation-overview"),
                                    L("Built-in evaluators", "concepts/built-in-evaluators")])
    probe = Group(inner, "Probe and improve", [
        T("AI red teaming", "pyrit", "cloud GA, local preview", theme="pink", st="ga"),
        T("Prompt optimizer", "gear", "improve instructions"),
        T("Agent optimizer", "gear", "instructions, skills, tools", st="limited"),
        T("CI/CD gates", "github", "GitHub, Azure DevOps", st="preview"),
        T("azd eval", "azd", "azd ai eval commands", st="preview"),
    ], theme="violet", cols=5, src=[L("AI red teaming", "concepts/ai-red-teaming-agent"),
                                    L("Agent optimizer", "agents/concepts/agent-optimizer-overview")])
    note = Note(inner, "Score your agent before you change anything, so later changes are measurable, not anecdotal. Need adversarial "
                       "coverage? Add AI red teaming. Evaluation outcomes and results stay in the project scope.",
                kind="tip", title="Baseline first", size=15, src=[L("Evaluate generative AI apps", "how-to/evaluate-generative-ai-app")])
    return Lane(x, "violet", "2", "Evaluate", "Measure quality, probe risk, optimize", "metrics", [measure, probe, note], w=w)


def lane_deploy(x, w=LW) -> Lane:
    inner = w - 2 * LPAD
    ship = Group(inner, "Ship", [
        T("Agent versions", "versions", "versioned agent, stable endpoint"),
        T("Publish to Copilot + Teams", "teams", "portal or REST/VNet, Microsoft 365", st="ga"),
        T("A2A + Agent Registry", "a2a", "A2A endpoint, Entra Agent Registry"),
        T("Hosted runtime", "container-apps", "sessions, state, scale-to-zero"),
        T("CI/CD + IaC", "devops", "azd, Bicep, Terraform, Actions"),
        T("Capacity", "quotas", "quota, PTU, batch"),
        T("Voice channels", "speech", "Teams Phone, Twilio, SIP", st="preview"),
    ], theme="green", cols=4, src=[L("Publish to Copilot and Teams", "agents/how-to/publish-copilot"),
                                   L("Hosted agents", "agents/concepts/hosted-agents")])
    loop = FlowGroup(inner, "The azd developer loop", [
        ("Scaffold", "azd ai agent init", "gray", 1), ("Run locally", "azd ai agent run, invoke --local", "gray", 1.15),
        ("Provision + deploy", "azd up", "green", 1), ("Evaluate", "azd ai agent eval generate or run", "violet", 1.15),
        ("Optimize", "azd ai agent optimize", "violet", 1),
    ], theme="green", gap=26, size=15, badge="preview", src=[L("azd for agents", "agents/concepts/cli-agent-development")])
    note = Note(inner, "Publishing now only means distributing to Microsoft 365 and Teams: creating an agent already gives it a stable "
                       "endpoint and its own Entra Agent Blueprint and identity. The agent object absorbs endpoint, identity and "
                       "deployment, so Agent Applications are replaced (preview REST flag AgentEndpoints=V1Preview).",
                kind="info", title="Agent Applications are replaced", size=15,
                src=[L("Migrate Agent Applications", "agents/how-to/migrate-agent-applications")])
    return Lane(x, "green", "3", "Deploy", "Ship a versioned agent to its channels", "container-apps", [ship, loop, note], w=w)


def lane_operate(x, w=LW) -> Lane:
    inner = w - 2 * LPAD
    observe = Group(inner, "Observe", [
        T("Tracing", "otel", "OpenTelemetry to Application Insights", st="part"),
        T("Monitoring dashboard", "dashboard", "health, usage, quality, cost", st="preview"),
        T("Insights", "advisor", "trace-backed findings and fixes", st="preview"),
        T("Continuous evaluation", "metrics", "sampled production traffic", st="preview"),
        T("Model + router monitoring", "monitor", "latency, throughput, errors"),
        T("Diagnostic logs", "log-analytics", "audit and request logs to Azure Monitor"),
        T("End-user feedback", "users", "feedback signals from your app", st="preview"),
        T("External agents", "agent", "register agents running elsewhere", st="preview"),
        T("Notification Center", "alerts", "service and resource notices"),
        T("Cost analysis", "cost-management", "meters, budgets, consolidated view"),
        T("Service Health", "service-health", "alerts and known issues"),
    ], theme="violet", cols=4, src=[L("Foundry Observability", "concepts/observability"),
                                    L("Monitor agents dashboard", "observability/how-to/how-to-monitor-agents-dashboard"),
                                    L("Agent insights", "observability/how-to/agent-insights"),
                                    L("Diagnostic logging", "how-to/diagnostic-logging")])
    loop = FlowGroup(inner, "The improve loop", [
        ("Issue flagged", "Insights or continuous evaluation", "violet", 1.1), ("Traces to dataset", "turn real runs into tests", "violet", 1.1),
        ("Evaluate", "baseline vs change", "violet", 1), ("Optimize", "instructions, skills, tools, model", "violet", 1.1),
        ("New version", "redeploy", "green", 1),
    ], theme="violet", gap=26, size=15, badge="preview", src=[L("Convert traces to datasets", "observability/how-to/traces-to-dataset")])
    return Lane(x, "violet", "4", "Operate", "Trace, monitor and keep improving", "monitor", [observe, loop], w=w)


def lane_govern(x, w=LW) -> Lane:
    inner = w - 2 * LPAD
    half = (inner - GAP) / 2
    cp = Group(half, "Foundry Control Plane: the fleet view", [
        T("Control plane", "management-group", "Overview, Assets, Compliance", st="preview"),
        T("Fleet monitoring", "dashboard", "health, performance, cost across agents", st="preview"),
        T("AI gateway", "apim", "API Management routing + policy", st="preview"),
        T("Token limits", "token", "cap use per agent, project, team", st="preview"),
        T("Guardrail policy", "policy", "org-level policies, bulk fixes", st="preview"),
        T("Quota", "quotas", "Manage > Quota"),
    ], theme="grape", cols=3, src=[L("Control plane overview", "control-plane/overview"),
                                   L("Enforce token limits", "control-plane/how-to-enforce-limits-models")])
    gr = Group(half, "Guardrails and safety", [
        T("Guardrails + controls", "content-safety", "risks + intervention points + actions", st="part"),
        T("Risk detectors", "security", "harm, Prompt Shields, PII, groundedness"),
        T("Task adherence", "gear", "detect agents straying from task", st="preview"),
        T("Guided guardrail", "learn", "guided setup for agents", st="preview"),
        T("Egress controls", "firewall", "hosted-agent network egress", st="preview"),
    ], theme="pink", cols=3, src=[L("Guardrails overview", "guardrails/guardrails-overview")])
    pol = Group(half, "Policy, agents and compliance", [
        T("Azure Policy", "policy", "approved models, block preview features"),
        T("Agent 365", "m365", "registry sync, autopilots, telemetry"),
        T("Responsible AI", "compliance", "transparency notes, data privacy"),
        T("Custom-agent registration", "agent", "use external agents instead", st=("retiring", "Retires 2027-04-30")),
    ], theme="grape", cols=2, src=[L("Model deployment policy", "how-to/model-deployment-policy"),
                                   L("Agent 365 integration", "agents/concepts/agent-365-integration")])
    ip = FlowGroup(half, "Guardrail intervention points", [
        ("User input", "", "pink", 1), ("Tool call", "preview", "pink", 1), ("Tool response", "preview", "pink", 1.2), ("Output", "", "pink", 1),
    ], theme="pink", gap=20, size=15, src=[L("Intervention points", "guardrails/intervention-points")])
    note = Note(half, "The control plane discovers Foundry agents (prompt, workflow, hosted), Azure SRE Agent and Logic Apps agent "
                      "loops, and integrates Defender, Purview, Entra and Azure Policy. Custom-agent registration is closed to new "
                      "registrations: register external agents instead.",
                kind="info", title="What the fleet view sees", size=15, src=[L("Control plane overview", "control-plane/overview")])
    return Lane(x, "grape", "5", "Govern", "Control, secure and prove compliance", "policy", [(cp, gr), (pol, Stack([ip, note]))], w=w)


# ============================================================================================== 4. platform spine
def hero(cv, x, y, w, h):
    th = THEMES["blue"]
    lh = metrics.line_ratio()
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=3.5)
        place_icon(cv, "foundry", x + 40, y + 34, 118)
        cv.text(x + 190, y + 26, "Microsoft Foundry", size=66, color=INK)
        cv.text(x + 194, y + 112, "Models + Agents + Tools, under one Azure resource", size=27, color=th.deep)
        cx, cy = x + 40, y + 174
        for i, (lab, tn) in enumerate((("Foundry resource (kind AIServices)", "blue"), ("Projects", "green"),
                                       ("Agents, models, tools, connections", "orange"))):
            c = Chip(lab, theme=tn, size=18)
            c.place(cv, cx, cy)
            cx += c.w
            if i < 2:
                arrow(cv, [(cx + 6, cy + c.h / 2), (cx + 34, cy + c.h / 2)], end_head="arrow", sw=2.5)
                cx += 40
        cv.text(x + 40, y + 236, "https://<resource>.services.ai.azure.com/api/projects/<project>", size=18, color=INK, font=metrics.MONO)
        foot = ("One governance boundary: unified RBAC, networking and policies under Microsoft.CognitiveServices/accounts.")
        cv.text(x + 40, y + 268, "\n".join(metrics.wrap_text(foot, (w - 80) * 0.965, 16)), size=16, color=INK)
        cv.text(x + 40, y + h - 28, "Learn: What is Microsoft Foundry?", size=12, color=LINK, link=learn("what-is-foundry"))


class Pair(Rect2):
    """Blocks side by side, equalised to the tallest (used as one cell of a Stack)."""

    def __init__(self, blocks, gap=GAP):
        self.blocks, self.gap = blocks, gap
        self.w = sum(b.w for b in blocks) + gap * (len(blocks) - 1)
        self.h = max(b.h for b in blocks)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        H = max(self.h, h or 0)
        cx = x
        for b in self.blocks:
            b.place(cv, cx, y, h=H)
            cx += b.w + self.gap
        self.x, self.y, self.h = x, y, H
        return self


def platform_band(cv, y):
    left_w, hero_w, right_w, gap = 1120, 1160, 1120, 60
    core = Group(left_w, "Core objects you will meet", [
        Chip("Deployment", theme="blue", size=16, icon="openai"), Chip("Agent + versions", theme="green", size=16),
        Chip("Conversation + items", theme="green", size=16), Chip("Response", theme="green", size=16),
        Chip("Toolbox + versions", theme="orange", size=16), Chip("Memory store", theme="teal", size=16),
        Chip("Connection", theme="cyan", size=16), Chip("Routine", theme="green", size=16), Chip("Skill", theme="orange", size=16),
        Chip("Project", theme="gray", size=16), Chip("Evaluation + dataset", theme="violet", size=16),
    ], theme="blue", chips=True, foot=["= An agent is a named, versioned asset; a conversation holds persisted items; a response is the unit of execution."],
        fill="none", src=[L("Agent runtime components", "agents/concepts/runtime-components")])
    cw = (left_w - GAP) / 2
    res = Card(cw, "Resource scope: the governance boundary", [
        "Model deployments: created once, reused by every project",
        "Connections to Storage, Key Vault and AI Search",
        "RBAC, managed identities, private networking, customer-managed keys",
        "Guardrails per deployment; Azure Monitor metrics",
    ], theme="blue", fill="soft", title_size=18, body_size=15, pad=14, gap=4, icon="foundry", icon_size=32,
        src=[L("Foundry architecture", "concepts/architecture")])
    prj = Card(cw, "Project scope: the development boundary", [
        "Agents, prompt and hosted, built against the project endpoint",
        "Evaluations, traces and datasets",
        "Files and vector stores: Microsoft-managed (basic) or your own accounts (standard)",
        "A project managed identity reaches connected resources",
    ], theme="green", fill="soft", title_size=18, body_size=15, pad=14, gap=4, icon="folder", icon_size=32,
        src=[L("Standard agent setup", "agents/concepts/standard-agent-setup")])
    left = Stack([core, Pair([res, prj])], gap=14)
    proto = Group(right_w, "Protocols on the wire", [
        T("Responses", "api", "OpenAI-compatible, stateful"),
        T("Invocations (+ WebSocket)", "rest", "custom payloads, webhooks, voice"),
        T("Activity", "teams", "Teams and Microsoft 365"),
        T("A2A", "a2a", "agent to agent, v1.0 GA"),
        T("MCP", "mcp", "Toolbox endpoint, remote servers"),
        T("OpenAPI", "api", "call any REST API as a tool"),
    ], theme="gray", cols=6, foot=[
        "= Chat: Responses. Voice or two-way streaming: Invocations (WebSocket). Webhooks, batch, custom payloads: Invocations. Teams or M365: Responses + Activity.",
        "Per-agent A2A endpoint: {project_endpoint}/agents/{name}/endpoint/protocols/a2a (v1.0 GA, v0.3 preview)",
        "Preview REST surfaces need a Foundry-Features: <Feature>=V1Preview header, for example Toolboxes, Skills or AgentEndpoints",
    ], src=[L("Hosted agents", "agents/concepts/hosted-agents"), L("Agent Service overview", "agents/overview")])
    hero_h = 330
    H = max(hero_h, left.h, proto.h)
    with cv.panel(0, y, theme="blue", style="solid", fill="soft", pad=20, w=W, sw=3) as p:
        left.place(cv, p.ix, p.iy, h=H)
        hero(cv, p.ix + left_w + gap, p.iy + (H - hero_h) / 2, hero_w, hero_h)
        proto.place(cv, p.ix + left_w + gap + hero_w + gap, p.iy, h=H)
    return p


# ============================================================================================== 5. foundation rails
def rails(cv, y) -> float:
    r, b = section_header(cv, 0, y, "Foundation rails: power and plumbing under every stage",
                          sub="identity, network, data and keys, resource model and cost run beneath the whole line", size=32)
    gy = b + 26
    groups = [
        Group(LW, "Identity and access", [
            T("Entra ID tokens", "app-registrations", "keyless; scope ai.azure.com/.default"),
            T("5 Foundry roles", "groups", "User, Project Manager, Account Owner, Owner, Agent Consumer"),
            T("Managed identities", "managed-identity", "resource and project scope"),
            T("Entra Agent ID", ("AID", "red"), "blueprint + identity per agent"),
            T("API keys", "key", "not accepted for agents, evals, Toolbox"),
        ], theme="red", cols=5, fill="soft", foot=["Starter least privilege: Foundry User for each developer and each project identity at resource scope",
                                                     "A custom subdomain is required for token auth"],
              src=[L("RBAC for Foundry", "concepts/rbac-foundry"), L("Authentication and authorization", "concepts/authentication-authorization-foundry")]),
        Group(LW, "Network", [
            T("Private endpoints", "private-endpoint", "inbound access"),
            T("Managed VNet", "vnet", "Foundry manages outbound"),
            T("BYO VNet", "subnet", "delegated subnet, outbound injection"),
            T("Network perimeter", "nsp", "network security perimeter"),
            T("On-premises access", "vpn-gateway", "reach on-prem resources"),
        ], theme="indigo", cols=5, fill="soft", foot=["A Foundry resource answers on three hostnames: openai.azure.com, services.ai.azure.com and cognitiveservices.azure.com",
                                                        "Some network-isolated scenarios need the SDK or CLI, not the portal"],
              src=[L("Networking options", "agents/concepts/networking-options"), L("Managed virtual network", "how-to/managed-virtual-network")]),
        Group(LW, "Data and keys", [
            T("Managed storage", "storage", "Microsoft-managed (basic setup)"),
            T("Bring your own", "cosmos", "Storage, Cosmos DB, AI Search"),
            T("Customer-managed keys", "key-vault", "CMK for Foundry data"),
            T("BYO Key Vault", "key", "connection secrets"),
            T("Data residency", "regions", "follows the deployment type"),
        ], theme="cyan", cols=5, fill="soft", foot=["Standard agent setup: your Storage, Cosmos DB and AI Search hold files, conversations and vector stores, isolated by project"],
              src=[L("Customer-managed keys", "concepts/customer-managed-keys"), L("Standard agent setup", "agents/concepts/standard-agent-setup")]),
        Group(LW, "Resource model and cost", [
            T("Foundry resource", "foundry", "kind AIServices: governance boundary"),
            T("Projects", "folder", "development boundary, own endpoint"),
            T("Connections", "api-connections", "Storage, Key Vault, AI Search"),
            T("Meters + budgets", "cost-management", "per-feature meters"),
            T("Chargeback", "tag", "project-level cost view", st="preview"),
        ], theme="yellow", cols=5, fill="soft", foot=["Microsoft.CognitiveServices/accounts, kind AIServices; deploy with ARM, Bicep or Terraform"],
              src=[L("Foundry architecture", "concepts/architecture"), L("Plan and manage costs", "concepts/manage-costs")]),
    ]
    h = max(g.h for g in groups)
    for i, g in enumerate(groups):
        g.place(cv, LX[i], gy, h=h)
    nw = (W - 2 * GUT) / 3
    n_res = Note(nw, "No automatic cross-region failover. For multi-region availability deploy separate Foundry resources per region "
                     "and handle data synchronization and routing in your application layer.", kind="gotcha", title="Resilience",
                 size=15, src=[L("High availability and resiliency", "how-to/high-availability-resiliency")])
    n_reg = Note(nw, "Foundry projects: 30 commercial regions plus US Gov Virginia and Arizona. Hosted agents list 31 regions. "
                     "Model availability depends on the provider and the deployment type; Learn gives no single real-time matrix, so "
                     "check the per-feature region pages before you deploy.", kind="warn", title="Region and feature availability varies",
                 size=15, src=[L("Feature availability across regions", "reference/region-support")])
    n_gov = Note(nw, "US Gov Virginia and Arizona, portal at ai.azure.us. Available: Responses API, Entra agent identity, private "
                     "networking, RBAC, network security perimeter, guardrails and prompt-agent tracing. Listed as not available: "
                     "model router, evaluations and optimization. Agent Service has a subset of agent types and tools.", kind="info",
                 title="Azure Government (Learn page of 2026-09-04)", size=15,
                 src=[L("Foundry in Azure Government", "concepts/foundry-azure-government"), L("Agent Service in Azure Government", "agents/concepts/azure-government")])
    _, nb = row(cv, 0, gy + h + 34, [n_res, n_reg, n_gov], gap=GUT)
    return nb


# ============================================================================================== 6. runtime path
def runtime(cv, y):
    bw, gap, H = 350, 96, 250
    with cv.panel(0, y, title="What happens at runtime: one request, end to end", theme="gray", style="dotted", fill="none",
                  pad=22, w=W, title_size=30, sub="the same path for a prompt agent or a hosted agent; guardrail intervention points for agents are preview",
                  sub_size=16) as p:
        top = p.iy + 4
        x = p.ix
        nodes = [
            ("Client app", "sends an Entra token (scope https://ai.azure.com/.default)", "gray", "user"),
            ("Project endpoint", ".../api/projects/<project> or a per-agent endpoint", "blue", "foundry"),
            ("RBAC check", "Foundry User on the project (Agent Consumer to only call agents)", "red", "managed-identity"),
            ("Guardrails", "screen user input, tool call, tool response and output", "pink", "content-safety"),
            ("Agent runtime", "prompt runtime or hosted sandbox", "green", "agent"),
            None,
            ("Response items", "appended to the conversation", "green", "files"),
            ("Telemetry", "traces and metrics to Application Insights and Azure Monitor", "violet", "app-insights"),
        ]
        verbs = ["HTTPS", "authorize", "screen", "run", "use", "return", "emit"]
        placed = []
        for i, n in enumerate(nodes):
            bx = x + i * (bw + gap)
            if n is None:
                with cv.panel(bx, top, theme="orange", style="dotted", fill="soft", pad=12, w=bw, min_h=H) as sp:
                    sy = sp.iy
                    for lab, sub, th, ic in (("Model deployment", "called by name", "blue", "openai"),
                                             ("Toolbox MCP endpoint", "tools and skills", "orange", "toolbox"),
                                             ("Knowledge + memory", "Foundry IQ, memory", "teal", "iq")):
                        b = Box(bw - 24, lab, sub=sub, theme=th, icon=ic, icon_pos="left", icon_size=30, size=17, sub_size=13,
                                fill="hatch", pad=8, min_h=68)
                        b.place(cv, sp.ix, sy)
                        sy += b.h + 12
                numbered(cv, bx + 8, top + 8, i + 1, theme="orange", d=34, size=19)
                placed.append(sp)
                continue
            lab, sub, th, ic = n
            b = Box(bw, lab, sub=sub, theme=th, icon=ic, icon_pos="top", icon_size=40, size=21, sub_size=14, fill="hatch",
                    pad=12, min_h=170)
            b.place(cv, bx, top + (H - max(b.h, 170)) / 2)
            numbered(cv, bx + 8, b.y + 8, i + 1, theme=th, d=34, size=19)
            placed.append(b)
        for i, (a, b) in enumerate(zip(placed, placed[1:])):
            connect(cv, a, b, a_side="right", b_side="left", end_head="arrow", sw=2.5, label=verbs[i], label_size=15, gap=4)
        by = top + H + 26
        spans = [(0, 2, "Identity and access: Entra token, RBAC", "red"), (3, 3, "Safety", "pink"),
                 (4, 5, "Run: compute, models, tools, knowledge", "green"), (6, 7, "Observe", "violet")]
        for a, b, label, th in spans:
            x1 = x + a * (bw + gap)
            x2 = x + b * (bw + gap) + bw
            hbrace(cv, x1 + 6, x2 - 6, by, side="top", depth=18, color=THEMES[th].stroke, sw=3)
            tw = metrics.line_width(label, 18)
            cv.text((x1 + x2) / 2 - tw / 2, by + 24, label, size=18, color=THEMES[th].deep)
    return p


# ============================================================================================== 7. deprecation clock + docs drift
EVENTS = [
    (date(2026, 7, 30), "GitHub Models retired", "move to Foundry Models", "past", L("GitHub Models to Foundry", "foundry-models/how-to/quickstart-github-models")),
    (date(2026, 8, 26), "azure-ai-inference retired; Assistants API sunset", "use the openai SDK and the Responses API", "past", L("Navigate from classic", "how-to/navigate-from-classic")),
    (AS_OF, "Today", "as of this canvas", "now", None),
    (date(2026, 11, 6), "Fabric data agent tool: deprecation scheduled", "use the Fabric IQ tool", "soon", L("Fabric tools", "agents/how-to/tools/fabric")),
    (date(2026, 12, 1), "Workflows retire", "use Microsoft Agent Framework", "soon", L("Workflows", "agents/concepts/workflow")),
    (date(2027, 3, 20), "Azure Language Studio retires", "moves to Foundry", "later", L("Foundry SDK overview", "how-to/develop/sdk-overview")),
    (date(2027, 4, 30), "Custom-agent registration retires", "register external agents instead", "later", L("Register a custom agent", "control-plane/register-custom-agent")),
    (date(2029, 3, 31), "Azure Language features retire", "key phrases, sentiment, summarization, entity linking, CLU, CQA, custom text classification, orchestration workflow",
     "later", L("Azure Language overview", "azure/ai-services/language-service/overview", base="")),
]


def clock(cv, x, y, w, min_h=0):
    kinds = {"past": ("#868e96", "gray"), "now": ("#1971c2", "blue"), "soon": ("#e03131", "red"), "later": ("#e8590c", "orange")}
    lh = metrics.line_ratio()
    with cv.panel(x, y, title="Deprecation clock (as of 2026-11-03)", sub="retirements and deprecations named in Learn; day counts run from 2026-11-03",
                  theme="red", style="dotted", fill="none", pad=22, w=w, min_h=min_h, title_size=30, sub_size=16) as p:
        n = len(EVENTS)
        inner = w - 44
        slot = inner / n
        ay = p.iy + 128
        cv.line((p.ix, ay), (p.ix + inner - 8, ay), stroke=INK, sw=3)
        cv.poly([(p.ix + inner - 22, ay - 10), (p.ix + inner - 6, ay), (p.ix + inner - 22, ay + 10)], kind="line", stroke=INK, sw=3)
        bottom = ay
        for i, (d, title, detail, kind, src) in enumerate(EVENTS):
            cx = p.ix + slot * (i + 0.5)
            col, th = kinds[kind]
            days = (d - AS_OF).days
            when = "today" if days == 0 else (f"in {days} days" if days > 0 else f"{-days} days ago")
            ds = d.isoformat()
            r = 17 if kind == "now" else 11
            tw = metrics.line_width(ds, 24)
            cv.text(cx - tw / 2, ay - 80, ds, size=24, color=col)
            tw2 = metrics.line_width(when, 16)
            cv.text(cx - tw2 / 2, ay - 50, when, size=16, color=MUTED)
            cv.ellipse(cx - r, ay - r, 2 * r, 2 * r, stroke=col, fill=THEMES[th].fill, style="solid", sw=3, rough=0)
            ty = ay + r + 14
            tl = metrics.wrap_text(title, (slot - 22) * 0.965, 18)
            cv.text(cx - slot / 2 + 11, ty, "\n".join(tl), size=18, color=INK, align="center", w=slot - 22)
            ty += len(tl) * 18 * lh + 4
            if detail:
                dl = metrics.wrap_text(detail, (slot - 22) * 0.965, 15)
                cv.text(cx - slot / 2 + 11, ty, "\n".join(dl), size=15, color=MUTED, align="center", w=slot - 22)
                ty += len(dl) * 15 * lh + 4
            if src:
                sl = metrics.wrap_text(f"Learn: {src[0]}", (slot - 22) * 0.965, 12)
                cv.text(cx - slot / 2 + 11, ty, "\n".join(sl), size=12, color=LINK, link=src[1], align="center", w=slot - 22)
                ty += len(sl) * 12 * lh
            bottom = max(bottom, ty)
        # retired services sit on the panel floor so the panel can stretch to match its neighbours
        chips = [Chip(n, theme="gray", size=15, dash="dashed") for n in
                 ("Anomaly Detector", "Content Moderator", "LUIS", "Metrics Advisor", "Personalizer", "QnA Maker")]
        cy = max(bottom + 26, y + min_h - 22 - chips[0].h - 8)
        cv.text(p.ix, cy - 28, "Already retired Foundry-adjacent services (Learn: What are Foundry Tools?)", size=16, color="#343a40",
                link=learn("azure/ai-services/what-are-ai-services", base=""))
        cx = p.ix
        for c in chips:
            c.place(cv, cx, cy)
            cx += c.w + 10
        # dot colour key, right-aligned on the same row
        items = (("#868e96", "gray", "already passed"), ("#1971c2", "blue", "today"), ("#e03131", "red", "within a month"),
                 ("#e8590c", "orange", "later"))
        kx = p.ix + inner - sum(metrics.line_width(t, 15) + 44 for _, _, t in items)
        cv.text(kx - 100, cy + 4, "Dot colour:", size=15, color="#343a40")
        for col, th, t in items:
            cv.ellipse(kx, cy + 8, 14, 14, stroke=col, fill=THEMES[th].fill, style="solid", sw=2, rough=0)
            cv.text(kx + 22, cy + 4, t, size=15, color=INK)
            kx += metrics.line_width(t, 15) + 44
    return p


def drift_cards(w) -> list:
    status = Card(w, "Docs disagree on status (as of 2026-11-03)", [
        "Browser automation: GA per the tool page and the 2026-10-19 blog; preview in the capability reference",
        "Agent optimizer: limited preview in the GA matrix; REST calls still need a preview header",
        "Long-running hosted agents: preview per the Sept blog; Learn pages updated 2026-11-02 show no label",
        "azd Foundry extensions: preview banner on Learn; the capability reference lists them without a label",
        "Foundry IQ: partial GA (API-level GA, portal preview) vs preview on the classic-to-new page",
        "Azure Functions tool: a tool page exists, the migration table says No for new agents",
        "Managed compute: new-portal preview pages vs older pages that still say hub-based and classic",
        "Voice: voice-based prompt agents are preview, while Voice Live with hosted agents is GA per the blog",
    ], theme="yellow", fill="soft", title_size=20, body_size=15, icon="preview-features", icon_size=36,
        src=[L("Feature status at GA", "concepts/general-availability"), L("Capability reference", "concepts/capability-reference")])
    dates = Card(w, "Docs disagree on dates, auth and wording", [
        "Learn's GA overview is dated 2026-09-23 and What's new covers August 2026: newer page labels win",
        "Assistants API sunset 2026-08-26 has passed, yet the GA page says classic assistants continue until an upgrade exists",
        "Entra scope: almost every page uses https://ai.azure.com/.default; one sample shows cognitiveservices.azure.com",
        "API keys: the GA page says Content Understanding needs Entra, the auth matrix says its batch jobs accept keys",
        "Vector-store file size: 2,000,000 tokens on the limits page, 5,000,000 on the file-search page",
        "The private-link page still says hosted (preview) agents, while hosted agents are GA elsewhere",
        "SDK versions move weekly: read them as 2.x and check the SDK page",
    ], theme="yellow", fill="soft", title_size=20, body_size=15, icon="info-protection", icon_size=36,
        src=[L("Navigate from classic", "how-to/navigate-from-classic"), L("Agent Service limits", "agents/concepts/limits-quotas-regions"),
             L("Authentication and authorization", "concepts/authentication-authorization-foundry")])
    return [status, dates]


# ============================================================================================== 8. why Foundry / how to choose
WHY = [
    ("Many resources, endpoints and SDK packages: Azure OpenAI + hub + AI Services, five or more endpoints",
     "One Foundry resource with projects, one project endpoint, unified RBAC, networking and policies; the 2.x SDK plus the OpenAI client",
     [L("Navigate from classic", "how-to/navigate-from-classic"), L("What is Foundry?", "what-is-foundry")]),
    ("Locked into one model provider",
     "10,000+ models in one catalog (about 50 new a month): sold by Azure with Microsoft terms and SLAs, plus partners and community; a model router and nine deployment types",
     [L("Foundry Models", "concepts/foundry-models-overview")]),
    ("Agents need servers, containers and glue code",
     "Prompt agents have nothing to host; hosted agents run your code in per-session VM-isolated sandboxes with a managed endpoint, scale-to-zero and an Entra agent identity",
     [L("Agent Service", "agents/overview"), L("Hosted agents", "agents/concepts/hosted-agents")]),
    ("Tool definitions and credentials copied into every agent",
     "Toolbox: define tools once, expose one MCP endpoint with central auth, guardrails and immutable versions; tool search; 1,400+ tools in the catalog",
     [L("Toolbox", "agents/concepts/toolbox-overview")]),
    ("Agents that know nothing about your data, your users or the web",
     "Foundry IQ knowledge bases with agentic retrieval that honor ACLs and Purview labels, plus Fabric IQ, Work IQ and Web IQ; Memory (preview) for long-term context",
     [L("Foundry IQ", "agents/concepts/what-is-foundry-iq"), L("Microsoft IQ", "microsoft-iq/", base="")]),
    ("No proof that a change made things better",
     "Evaluations with a baseline first, agent evaluators, datasets from traces, AI red teaming, optimizers (preview) and CI/CD gates (preview)",
     [L("Evaluations", "concepts/evaluation-overview")]),
    ("Black-box agents in production",
     "OpenTelemetry tracing into Application Insights; monitoring dashboard, insights and continuous evaluation (preview); diagnostic logs to Azure Monitor",
     [L("Observability", "concepts/observability")]),
    ("Safety and compliance bolted on at the end",
     "Guardrails (risks + intervention points + actions) on models (GA) and agents (preview); Azure Policy to approve models and block preview features",
     [L("Guardrails", "guardrails/guardrails-overview"), L("Model deployment policy", "how-to/model-deployment-policy")]),
    ("Security and platform teams cannot see or govern agents",
     "Keyless Entra auth, five RBAC roles, Entra Agent ID per agent, private networking, customer-managed keys; a control plane fleet view (preview)",
     [L("Control plane", "control-plane/overview"), L("RBAC for Foundry", "concepts/rbac-foundry")]),
    ("Surprise bills",
     "Per-feature meters, deployment types (provisioned, batch), quota and budgets; project-level chargeback (preview)",
     [L("Plan and manage costs", "concepts/manage-costs")]),
]


def why_panel(cv, x, y, w, min_h):
    th = THEMES["green"]
    lh = metrics.line_ratio()
    pw, aw, sw_, gapx = 700, 980, 300, 20
    with cv.panel(x, y, title="Why Foundry?", sub="From scattered building blocks to one governed platform for models, agents and tools (every answer links to Learn)",
                  theme="green", style="dotted", fill="soft", pad=22, w=w, min_h=min_h, title_size=36, sub_size=18) as p:
        cx0 = p.ix
        cv.text(cx0, p.iy, "Today's problem", size=18, color="#c92a2a")
        cv.text(cx0 + pw + gapx + 70 + gapx, p.iy, "The Foundry answer", size=18, color=th.deep)
        cv.text(cx0 + pw + gapx + 70 + gapx + aw + gapx, p.iy, "Where in Learn", size=18, color=MUTED)
        cy = p.iy + 30
        for i, (prob, ans, srcs) in enumerate(WHY):
            pl = metrics.wrap_text(prob, pw * 0.965, 16)
            al = metrics.wrap_text(ans, aw * 0.965, 16)
            sl = [metrics.wrap_text(f"Learn: {s[0]}", sw_ * 0.965, 12) for s in srcs]
            rh = max(len(pl) * 16 * lh, len(al) * 16 * lh, sum(len(s) for s in sl) * 12 * lh + 4 * len(sl)) + 20
            if i % 2 == 0:
                cv.rect(cx0 - 8, cy - 4, w - 2 * 22 + 16, rh, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                        round_=False, rough=0, opacity=65)
            cv.text(cx0, cy + 6, "\n".join(pl), size=16, color="#c92a2a")
            ax = cx0 + pw + gapx
            arrow(cv, [(ax + 4, cy + rh / 2 - 4), (ax + 58, cy + rh / 2 - 4)], color="#2f9e44", sw=4, end_head="arrow")
            cv.text(cx0 + pw + gapx + 70 + gapx, cy + 6, "\n".join(al), size=16, color=INK)
            sx = cx0 + pw + gapx + 70 + gapx + aw + gapx
            sy = cy + 6
            for (label, url), lines in zip(srcs, sl):
                cv.text(sx, sy, "\n".join(lines), size=12, color=LINK, link=url)
                sy += len(lines) * 12 * lh + 4
            cy += rh
        q = Note(w - 44, "Start with a model call, add a prompt agent, and repackage it as a hosted agent when you need your own code: the "
                         "Toolbox, knowledge and identity stay the same. Learn's advice: start declarative and move to code as your needs grow.",
                 kind="key", title="The through-line", size=16, src=[L("What is Microsoft Foundry? (choose how to build)", "what-is-foundry")])
        q.place(cv, p.ix, cy + 16)
    return p


def how_panel(cv, x, y, w, min_h):
    th = THEMES["yellow"]
    rows = [
        ["Send a prompt to a model, no tools", "Foundry Models + Responses API", "shortest path to a working call; add an agent later only if you need tools or orchestration"],
        ["Build my first agent", "Prompt agent (+ Toolbox)", "nothing to run; instructions, model and tools, versioned in the project"],
        ["Host an agent I already wrote", "Hosted agent", "your code or container behind a managed endpoint, with a sandbox per session, scaling and identity"],
        ["Use LangGraph, Agent Framework or Semantic Kernel", "Hosted agents + frameworks page", "shows how each framework maps onto Foundry hosting"],
        ["Talk to users in real time", "Voice prompt agent (preview) or Voice Live", "Foundry manages voice orchestration; connect over WebSocket"],
        ["Ground answers in company data", "Foundry IQ (file search for a few files)", "knowledge bases with agentic retrieval; file search is the lighter option"],
        ["Know whether quality is good", "Evaluations, baseline first (+ red teaming)", "a baseline makes later changes measurable"],
        ["See what happens in production", "Tracing + monitoring", "tracing, monitoring and evaluation share one data model"],
        ["Ship repeatably", "CI/CD for agents", "a repeatable release path before you scale"],
        ["Govern many agents", "Control plane (preview) + guardrails + Azure Policy", "for a single project, project settings are enough"],
    ]
    with cv.panel(x, y, title="How to choose: start with your goal", sub="rows condensed from Learn's capability map (concepts/capabilities)",
                  theme="yellow", style="dotted", fill="soft", pad=22, w=w, min_h=min_h, title_size=34, sub_size=16) as p:
        t = Table([("I want to...", 300), ("Start with", 320), ("Why", 0)], rows, w=w - 44, theme="yellow", size=14, head_size=16,
                  pad_y=6, first_col_theme="yellow")
        t.place(cv, p.ix, p.iy)
        cy = t.bottom + 18
        cv.text(p.ix, cy, "First path for a new developer", size=20, color=th.deep)
        cy += 32
        steps = ["Make a model call", "Set up your environment", "Choose a model", "Build a prompt agent (hosted if you bring code)",
                 "Add Toolbox tools, then knowledge and memory"]
        sw = (w - 44 - 4 * 26) / 5
        boxes = []
        for i, s in enumerate(steps):
            b = Box(sw, s, theme="yellow", size=15, fill="hatch", pad=8, min_h=74)
            b.place(cv, p.ix + i * (sw + 26), cy)
            numbered(cv, b.x + 6, b.y + 6, i + 1, theme="yellow", d=30, size=17)
            boxes.append(b)
        for a, b in zip(boxes, boxes[1:]):
            connect(cv, a, b, a_side="right", b_side="left", end_head="arrow", sw=2, gap=2)
        cy = boxes[0].bottom + 10
        cv.text(p.ix, cy, "Learn: Start with your goal", size=12, color=LINK, link=learn("concepts/capabilities"))
        cv.text(p.ix + 230, cy, "Learn: Choose how to build", size=12, color=LINK, link=learn("what-is-foundry"))
        who = Note(w - 44, "Anyone evaluating: the portal. Application developer: Foundry Models, SDKs, VS Code, coding agents + MCP. Agent developer: "
                           "prompt and hosted agents, Toolbox, Foundry IQ, Memory (preview), LangChain/LangGraph. ML engineer: fine-tuning. "
                           "Platform engineer: azd, the control plane. AI quality engineer: observability and evaluations. "
                           "Security administrator: AI red teaming, guardrails and controls.", kind="info", title="Who it is for (Learn capability map)",
                   size=15, src=[L("Capabilities and who they are for", "concepts/capabilities")])
        who.place(cv, p.ix, cy + 30)
    return p


# ============================================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry platform overview", SUBTITLE, icon="foundry", w=W)
    y = top_strip(cv, bottom + 40)
    y = factory_strip(cv, y + 40)
    rail = ways_in(cv, y + 44)

    # ---- 1 BUILD banner + four lanes
    by = rail.bottom + 48
    dotted(cv, [(rail.cx, rail.bottom + 4), (rail.cx, by - 6)], head="arrow")
    chevron(cv, 0, by, W, 92, "BUILD", "The assembly line: discover raw materials, then assemble models, agents, tools and knowledge", "gray", notch=False,
            left=True, marker="1", tsize=40, ssize=19)
    ly = by + 92 + 24
    # Station 0 "Discover" (raw materials) sits in the right half of the BUILD banner
    disc_chips = [Chip("Model catalog (10,000+)", theme="blue", size=17), Chip("Leaderboards", theme="orange", size=17, dash="dashed"),
                  Chip("Instant access", theme="orange", size=17, dash="dashed"), Chip("Solution templates", theme="gray", size=17),
                  Chip("Agent templates", theme="green", size=17), Chip("Tool catalog (1,400+)", theme="orange", size=17)]
    dw = sum(c.w for c in disc_chips) + 12 * (len(disc_chips) - 1)
    dx = W - 80 - dw
    lab = "Discover: raw materials"
    cv.text(dx - 24 - metrics.line_width(lab, 22), by + 33, lab, size=22, color="#343a40")
    for c in disc_chips:
        c.place(cv, dx, by + (92 - c.h) / 2)
        dx += c.w + 12
    lanes1 = [lane_models(LX[0]), lane_agents(LX[1]), lane_tools(LX[2]), lane_knowledge(LX[3])]
    H1 = max(l.height() for l in lanes1)
    for l in lanes1:
        l.place(cv, ly, H1)

    # ---- platform spine
    band = platform_band(cv, ly + H1 + 84)
    for l in lanes1:
        dotted(cv, [(l.panel.cx, l.panel.bottom + 4), (l.panel.cx, band.y - 8)], head="arrow")

    # ---- 2-5 conveyor
    cy_ = band.bottom + 68
    stage = [("2  EVALUATE", "QA line: prove it works", "violet"), ("3  DEPLOY", "Dispatch dock: ship and publish", "green"),
             ("4  OPERATE", "Control tower: watch and improve", "violet"), ("5  GOVERN", "Compliance office: control and prove", "grape")]
    lanes2 = [lane_evaluate(LX2[0], W2[0]), lane_deploy(LX2[1], W2[1]), lane_operate(LX2[2], W2[2]), lane_govern(LX2[3], W2[3])]
    for i, (t, s, th) in enumerate(stage):
        w_ = W2[i] + (64 if i < 3 else 0)
        chevron(cv, LX2[i], cy_, w_, 92, t, s, th)
        dotted(cv, [(LX2[i] + W2[i] / 2, band.bottom + 4), (LX2[i] + W2[i] / 2, cy_ - 8)], head="arrow")
    ly2 = cy_ + 92 + 24
    H2 = max(l.height() for l in lanes2)
    for l in lanes2:
        l.place(cv, ly2, H2)
    # improve-loop arrow: Operate -> Evaluate, under the lanes
    lb = ly2 + H2
    arrow(cv, [(lanes2[2].panel.cx, lb + 6), (lanes2[2].panel.cx, lb + 54), (lanes2[0].panel.cx, lb + 54), (lanes2[0].panel.cx, lb + 8)],
          dash="dashed", color=THEMES["violet"].stroke, sw=3.5, end_head="arrow",
          label="the improve loop: traces become datasets, evaluations drive optimizer changes, a new agent version ships",
          label_size=17, label_pos="above", label_color=THEMES["violet"].deep)

    # ---- foundation rails, runtime, clock, why / how, sources
    ry = rails(cv, lb + 84)
    rt = runtime(cv, ry + 50)
    cw = 2300
    rside = Stack(drift_cards(W - cw - 60), gap=14)
    c = clock(cv, 0, rt.bottom + 50, cw, min_h=rside.h)
    rside.place(cv, cw + 60, rt.bottom + 50, h=c.h)
    wy = max(c.bottom, rside.y + rside.h) + 50
    why_w = 2150
    hp = how_panel(cv, why_w + 60, wy, W - why_w - 60, 0)
    wp = why_panel(cv, 0, wy, why_w, hp.h)
    ph = max(wp.h, hp.h)
    for pnl in (wp, hp):
        if pnl.h < ph:
            pnl.el.el["height"] = round(ph, 2)
            pnl.h = ph
    sy = wy + ph + 50
    sources(cv, 0, sy, [
        L("What is Microsoft Foundry?", "what-is-foundry"),
        L("Capability map: start with your goal", "concepts/capabilities"),
        L("Feature status at GA", "concepts/general-availability"),
        L("Microsoft Foundry architecture", "concepts/architecture"),
        L("Agent Service overview", "agents/overview"),
        L("Hosted agents", "agents/concepts/hosted-agents"),
        L("Toolbox overview", "agents/concepts/toolbox-overview"),
        L("Foundry IQ", "agents/concepts/what-is-foundry-iq"),
        L("Microsoft IQ documentation", "microsoft-iq/", base=""),
        L("Foundry Observability", "concepts/observability"),
        L("Guardrails overview", "guardrails/guardrails-overview"),
        L("Foundry control plane overview", "control-plane/overview"),
        L("RBAC for Microsoft Foundry", "concepts/rbac-foundry"),
        L("Navigate from Foundry classic (migration dates)", "how-to/navigate-from-classic"),
    ], w=W, cols=3)
