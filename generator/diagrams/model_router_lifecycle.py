"""Model router: one deployment that picks the model per request - modes, subsets, failover, affinity, agents, governance, observability."""
from __future__ import annotations

import math

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="model-router-lifecycle", title="Model router: one deployment, many models", section="2", group="Models", order=23,
    description="How the model router works - trained router, Cost / Balanced / Quality modes, model subset, failover, session affinity, "
                "agents and Responses API, policy governance, monitoring and evaluation (versions and lifecycle continue in part 2).",
    tags=["model router", "routing", "failover", "subset", "policy", "models"],
)

W, G, C = 3000, 48, 460          # canvas width, standard gap, one-column card width (6-column grid)
MUTED_ = "#495057"

from generator.xd import Note as _KitNote  # noqa: E402


def Note(w, text, **kw):
    """Kit Note plus bottom breathing room when it carries a Learn: link (the kit draws that link flush with the border)."""
    n = _KitNote(w, text, **kw)
    if kw.get("src") and "min_h" not in kw:
        n = _KitNote(w, text, min_h=n.h + 14, **kw)
    return n


def span(n: int) -> float:
    return n * C + (n - 1) * G


def colx(i: int) -> float:
    return i * (C + G)


def L(label: str, path: str):
    return (label, learn(path))


S_ROUTER = L("Model router concepts", "openai/concepts/model-router")
S_HOW = L("How model router works", "openai/concepts/model-router-how-it-works")
S_HOWTO = L("Use model router", "openai/how-to/model-router")
S_NEW = L("What's new in model router", "foundry-models/whats-new-model-router")
S_MON = L("Monitor model router", "openai/how-to/monitor-model-router")
S_EVAL = L("Evaluate model router", "openai/how-to/evaluate-model-router")
S_POL = L("Govern model router with Azure Policy", "how-to/model-router-policy")
S_AGENTS = L("Model router with agents", "openai/how-to/model-router-agents")
S_RESP = L("Responses API: automatic vs direct routing", "openai/how-to/responses-model-routing")
S_CACHE = L("Prompt caching", "openai/how-to/prompt-caching")
S_QUOTAS = L("Azure OpenAI quotas and limits", "openai/quotas-limits")
S_WORK = L("Working with models (auto-update)", "openai/how-to/working-with-models")
S_SCHED = L("Model retirement schedule", "openai/concepts/model-retirement-schedule")


# ---------------------------------------------------------------------------------------------- helpers
def banner(cv, y, n, title, sub=None, theme="blue"):
    """Numbered section banner across the canvas; returns the y where content can start."""
    numbered(cv, 24, y + 26, n, theme=theme, d=44, size=24)
    _, bottom = section_header(cv, 60, y, title, sub, size=32, sub_size=17, w=W - 60)
    return bottom + 26


def tile_h(num, label, sub, w, num_size=60):
    nw, nh = text_size(num, num_size)
    avail = (w - (26 + nw + 22) - 16) * 0.965
    lr = metrics.line_ratio()
    return max(nh + 24, len(wrap_text(label, avail, 21)) * 21 * lr + 4 + len(wrap_text(sub, avail, 15)) * 15 * lr + 28)


def tile(cv, x, y, w, h, num, label, sub, th_name, num_size=60):
    """Big-number summary tile."""
    th = get_theme(th_name)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    nw, nh = text_size(num, num_size)
    cv.text(x + 26, y + (h - nh) / 2, num, size=num_size, color=th.deep)
    tx = x + 26 + nw + 22
    avail = (w - (tx - x) - 16) * 0.965
    lab, sl = wrap_text(label, avail, 21), wrap_text(sub, avail, 15)
    lr = metrics.line_ratio()
    total = len(lab) * 21 * lr + 4 + len(sl) * 15 * lr
    ty = y + (h - total) / 2
    cv.text(tx, ty, "\n".join(lab), size=21, color=th.deep)
    cv.text(tx, ty + len(lab) * 21 * lr + 4, "\n".join(sl), size=15, color=INK)
    cv.register("tile:" + label, x, y, w, h)


def code_need(w, lines, size=15, notes=None, src=None):
    """Natural height of a code_box (code lines, optional bullet notes, optional Learn link)."""
    lh = size * metrics.line_ratio(metrics.MONO)
    need = 12 + 26 + 8 + len(lines) * lh + 14 + (18 if src else 0)
    if notes:
        need += 34 + sum(len(wrap_text(t, w - 56, 15)) * 15 * metrics.line_ratio() + 5 for t in notes)
    return need


def code_box(cv, x, y, w, title, lines, th_name="blue", size=15, h=None, src=None, notes=None):
    """Monospace code panel with a coloured title (and optional 'reading the call' bullets); returns its height."""
    th = get_theme(th_name)
    lh = size * metrics.line_ratio(metrics.MONO)
    H = max(code_need(w, lines, size, notes, src), h or 0)
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 16, y + 10, title, size=18, color=th.deep)
    cv.text(x + 16, y + 44, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    if notes:
        ny = y + 44 + len(lines) * lh + 20
        cv.line((x + 16, ny - 8), (x + w - 16, ny - 8), stroke=th.stroke, sw=1, dash="dashed")
        cv.text(x + 16, ny, "Reading the call", size=16, color=th.deep)
        ny += 26
        for t in notes:
            tl = wrap_text(t, w - 56, 15)
            cv.ellipse(x + 18, ny + 6, 8, 8, stroke=th.stroke, sw=2, rough=0)
            cv.text(x + 38, ny, "\n".join(tl), size=15, color=INK)
            ny += len(tl) * 15 * metrics.line_ratio() + 5
    if src:
        cv.text(x + 16, y + H - 26, "Learn: " + src[0], size=12, color=LINK, link=src[1])
    cv.register("code:" + title, x, y, w, H)
    return H


def std(theme, title, body, **kw):
    """Standard dense card (consistent type scale)."""
    kw.setdefault("title_size", 20)
    kw.setdefault("body_size", 15)
    return Card(C, title, body, theme=theme, **kw)


def two_pass(fn, cv, y):
    """Run a section twice: measure the side-by-side panels on a scratch canvas, then draw them all at the tallest height."""
    _, hs = fn(Canvas("scratch"), y, 0)
    return fn(cv, y, max(hs))[0]


def funnel(cv, x, y, w, h, theme="blue"):
    """Funnel graphic: many models in at the top, a smaller eligible subset out of the neck."""
    th = get_theme(theme)
    n0, n1, ny = x + w * 0.36, x + w * 0.64, y + h * 0.55
    cv.poly([(x, y), (x + w, y), (n1, ny), (n1, y + h), (n0, y + h), (n0, ny), (x, y)], kind="line", stroke=th.stroke,
            sw=2, fill=th.soft, fill_style="solid", rough=0)
    cols = ["blue", "orange", "gray", "violet", "teal", "pink", "blue", "orange"]
    for i, cn in enumerate(cols):
        t2 = get_theme(cn)
        cx = x + 22 + (i % 4) * (w - 44) / 3
        cy = y + 20 + (i // 4) * 22
        cv.ellipse(cx - 8, cy - 8, 16, 16, stroke=t2.stroke, fill=t2.fill, style="solid", sw=2, rough=0)
    for i in range(2):
        t2 = get_theme(["blue", "orange"][i])
        cv.ellipse(x + w / 2 - 20 + i * 24, y + h * 0.78 - 8, 16, 16, stroke=t2.stroke, fill=t2.fill, style="solid", sw=2,
                   rough=0)


def gauge(cv, cx, cy, r):
    """Three-position dial (Cost | Balanced | Quality) with the needle on Balanced (the default)."""
    for th_name, a0, a1 in (("yellow", 180, 122), ("blue", 118, 62), ("violet", 58, 0)):
        th = get_theme(th_name)
        pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / 10)),
                cy - r * math.sin(math.radians(a0 + (a1 - a0) * i / 10))) for i in range(11)]
        cv.poly(pts, kind="line", stroke=th.stroke, sw=12, curved=True, rough=0)
    ang = math.radians(90)
    cv.poly([(cx, cy), (cx + (r - 22) * math.cos(ang), cy - (r - 22) * math.sin(ang))], kind="line", stroke=INK, sw=4, rough=0)
    cv.ellipse(cx - 8, cy - 8, 16, 16, stroke=INK, fill=INK, style="solid", sw=2, rough=0)
    for label, ex, th_name in (("Cost", cx - r + 4, "yellow"), ("Quality", cx + r - 4, "violet")):
        tw, _ = text_size(label, 18)
        cv.text(ex - tw / 2, cy + 16, label, size=18, color=get_theme(th_name).deep)
    tw, _ = text_size("Balanced (default)", 18)
    cv.text(cx - tw / 2, cy - r - 36, "Balanced (default)", size=18, color=get_theme("blue").deep)


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Model router: one deployment, many models",
        "A trained router picks the best-fit model for every request: modes, subsets, failover, agents, policy and monitoring "
        "(facts as of 2026-11-03; versions and lifecycle: part 2)", w=W)
    y = bottom + 36
    y = summary_tiles(cv, y)
    y = section_flow(cv, y + 56)
    y = section_modes(cv, y + 56)
    y = section_switches(cv, y + 56)
    y = two_pass(section_use, cv, y + 56)
    y = section_deploy(cv, y + 56)
    y = two_pass(section_run, cv, y + 56)
    section_sources(cv, y + 56)


# ---------------------------------------------------------------------------------------------- summary
def summary_tiles(cv, y):
    tiles = [
        ("35", "models in the pool", "6 providers - router version 2025-11-18 (GA)", "blue", 60),
        ("3", "routing modes", "Cost, Balanced (the default) and Quality", "blue", 60),
        ("32", "regions", "Global Standard in all, Data Zone Standard in a subset", "blue", 60),
        ("1", "deployment to manage", "One endpoint, one rate limit, one content filter", "blue", 60),
        ("30 min", "session affinity (preview)", "Chat Completions only; best-effort same model across turns", "violet", 40),
        ("5 min", "to apply a mode or subset change", "Up to 5 minutes: edit the settings, wait, re-test", "yellow", 40),
    ]
    hs = [tile_h(*t[:3], C, t[4]) for t in tiles]
    H = max(hs)
    for i, (num, label, sub, th, ns) in enumerate(tiles):
        tile(cv, colx(i), y, C, H, num, label, sub, th, ns)
    y += H + 22
    cx = 0.0
    cv.text(cx, y + 2, "Also in this series:", size=16, color=MUTED_)
    cx += text_size("Also in this series:", 16)[0] + 16
    for label, th in (("Foundry Models catalog", "blue"), ("Deployment types and offers", "blue"), ("PTU and quota", "yellow"),
                      ("Fine-tuning: from data to a deployed model", "blue"), ("Part 2: Model versions, lifecycle and the retirement cliff", "grape")):
        c = Chip(label, theme=th, size=15, fill="soft").place(cv, cx, y - 2)
        cx += c.w + 14
    return y + 38


# ---------------------------------------------------------------------------------------------- 1 flow
POOL = [
    ("OpenAI", "blue", ["gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5", "gpt-5.4", "gpt-5.4-mini",
                        "gpt-5.4-nano", "gpt-5.2", "gpt-5", "gpt-5-mini", "gpt-5-nano", "o4-mini", "gpt-4.1", "gpt-4.1-mini",
                        "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini", "gpt-oss-120b"]),
    ("Anthropic", "orange", ["claude-fable-5-1", "claude-opus-5", "claude-sonnet-5", "claude-opus-4-8", "claude-opus-4-7",
                             "claude-opus-4-6", "claude-sonnet-4-5", "claude-haiku-4-5"]),
    ("xAI", "gray", ["grok-4.6", "grok-4-1-fast-reasoning", "grok-4"]),
    ("Fireworks", "violet", ["FW-GLM-5.3", "FW-GLM-5.3-Flash", "FW-Kimi-K3"]),
    ("DeepSeek", "teal", ["DeepSeek-V3.2"]),
    ("Meta", "pink", ["Llama-4-Maverick-17B-128E-Instruct-FP8"]),
]
RETIRING = {"o4-mini", "claude-haiku-4-5", "claude-sonnet-4-5", "Llama-4-Maverick-17B-128E-Instruct-FP8"}


def pool_flow(models, th, w):
    chips = [Chip(m, theme="red", size=15, pad_x=9, pad_y=5, dash="dashed", fill="soft") if m in RETIRING
             else Chip(m, theme=th, size=15, pad_x=9, pad_y=5) for m in models]
    return ChipFlow(chips, w, gap=8)


def section_flow(cv, y):
    y = banner(cv, y, 1, "One deployment, many models: the request path",
               "You call a single deployment named model-router; a small trained model chooses which underlying model answers each request")
    RW, PW, AW, SW_, GAP = 780, 1140, 240, 450, 90
    with cv.panel(0, y, title="model-router deployment  (Global Standard or Data Zone Standard)",
                  sub="Single deployment, single rate limit, single content filter - the content filter and TPM limit apply to the router as a whole",
                  theme="blue", style="dotted", pad=26, title_size=26, sub_size=16, w=W) as flow:
        fx, fy = flow.ix, flow.iy + 8
        rx = fx + AW + GAP
        # ---------------- router panel
        with cv.panel(rx, fy, title="Router model", sub="trained ML model - not an LLM", theme="blue", style="solid", fill="none",
                      pad=20, title_size=24, sub_size=16, w=RW, sw=3) as rp:
            ml = Box(RW - 40, "Analyses the full request", sub="System + user messages, tool definitions and conversation history. "
                     "A small model trained on hundreds of thousands of examples (QA, code, math, summarisation, conversation, agentic tool calling). "
                     "Negligible overhead; it does not store your prompts.", theme="blue", icon="traffic-manager", icon_pos="left",
                     icon_size=40, size=18, sub_size=14, fill="hatch")
            ml.place(cv, rp.ix, rp.iy)
            ry = ml.bottom + 22
            gauge(cv, rp.ix + 140, ry + 120, 96)
            mode = Card(RW - 40 - 300, "Routing mode", ["Default is Balanced; set it in Custom settings (routing mode)",
                                                        "Cost, Balanced or Quality (see section 2)",
                                                        "A change takes up to 5 minutes to apply"],
                        theme="blue", title_size=19, body_size=15, src=[S_ROUTER])
            mode.place(cv, rp.ix + 300, ry, h=190)
            fy2 = ry + 190 + 20
            funnel(cv, rp.ix + 36, fy2 + 6, 230, 140)
            sub = Card(RW - 40 - 300, "Model subset", ["Choose which pool models are eligible (default: all of them)",
                                                       "New models are never added to your subset automatically",
                                                       "Pick at least 2: the subset is also the failover set",
                                                       "Effective context window = the smallest underlying model: pick a subset for long contexts"],
                       theme="blue", title_size=19, body_size=15, src=[S_HOW])
            sub.place(cv, rp.ix + 300, fy2)
        # ---------------- pool panel
        px = rp.right + GAP
        rows = []
        for name, th, models in POOL:
            rows.append((name, th, models))
        with cv.panel(px, fy, title="Eligible pool: 35 models (version 2025-11-18, updated in place)",
                      sub="Only models you may use and that exist in the deployment's region are eligible; data-zone boundaries are honored",
                      theme="blue", style="solid", fill="none", pad=20, title_size=24, sub_size=16, w=PW, sw=3,
                      min_h=rp.h) as pp:
            cx0, cy0 = pp.ix, pp.iy + 4
            tagw = 138
            for name, th, models in rows[:2]:
                tag = Chip(f"{name}  {len(models)}", theme=th, size=16, fill="solid", sw=2, w=tagw)
                tag.place(cv, cx0, cy0)
                fl = pool_flow(models, th, PW - 40 - tagw - 14)
                fl.place(cv, cx0 + tagw + 14, cy0)
                cy0 += max(fl.h, tag.h) + 14
                if name == "Anthropic":
                    cv.text(cx0 + tagw + 14, cy0 - 6, "Every other pool model needs no separate deployment. Claude must be deployed from the catalog first\n"
                            "(same Foundry account, matching SKU) - otherwise InvalidResourceProperties", size=14, color="#c92a2a")
                    cy0 += 46
            pair_w = (PW - 40 - 40) / 2
            for pair in (rows[2:4], rows[4:6]):
                xx = cx0
                rh = 0
                for name, th, models in pair:
                    tag = Chip(f"{name}  {len(models)}", theme=th, size=16, fill="solid", sw=2, w=tagw)
                    tag.place(cv, xx, cy0)
                    fl = pool_flow(models, th, pair_w - tagw - 14)
                    fl.place(cv, xx + tagw + 14, cy0)
                    rh = max(rh, fl.h, tag.h)
                    xx += pair_w + 40
                cy0 += rh + 14
            # legend for retiring models
            lg = Chip("retiring Nov 2026", theme="red", size=15, dash="dashed", fill="soft").place(cv, cx0, cy0)
            cv.text(lg.right + 14, cy0 + 4, "o4-mini, claude-haiku-4-5, claude-sonnet-4-5 and Llama-4-Maverick are on the 2026-11 retirement list "
                    "(as of 2026-11-03) - see part 2", size=14, color=MUTED_)
            # pool growth chain
            cy0 += 54
            cv.text(cx0, cy0, "How the pool grew (what's new)", size=17, color=get_theme("blue").deep)
            cy0 += 28
            steps = [("Nov 2025", "GA: routing modes, subsets, Global + Data Zone Standard"), ("Mar 2026", "Automatic failover"),
                     ("May 2026", "+7 models (28)"), ("Aug 2026", "GPT-5.6 + Opus 4.8 added; 5 retired models removed (27)"),
                     ("Oct 2026", "+8 models (35)")]
            bw = (PW - 40 - 4 * 30) / 5
            bxs = []
            for i, (when, what) in enumerate(steps):
                b = Box(bw, when, sub=what, theme="blue", size=17, sub_size=13, fill="soft", h=100)
                b.place(cv, cx0 + i * (bw + 30), cy0)
                bxs.append(b)
            for a, b in zip(bxs, bxs[1:]):
                connect(cv, a, b, sw=2)
            cv.text(cx0, bxs[0].bottom + 8, "Source: What's new in model router. Counts as documented; the Models page and Azure Policy decide what you can deploy.",
                    size=13, color=MUTED_, link=S_NEW[1])
        # ---------------- app + response
        cyc = fy + max(rp.h, pp.h) / 2
        app = Box(AW, "Your app or agent", sub='model = "model-router"  (Responses API or Chat Completions)', theme="gray",
                  icon="app", icon_pos="top", icon_size=40, size=20, sub_size=14, h=190, fill="hatch")
        app.place(cv, fx, cyc - app.h / 2)
        resp = Card(SW_, "Response", [
            "Top-level model field names the model that answered (response.model in the Responses API)",
            "Log it: it is the primary observability signal",
            "Preview: opt-in model_selection_details shows the mode and the ordered attempts",
            "Billing: input prompts are charged at the pricing-page rate (section 5)",
        ], theme="violet", icon="metrics", title_size=20, body_size=15, src=[S_MON])
        resp.place(cv, pp.right + GAP, cyc - resp.h / 2)
        connect(cv, app, rp, a_side="right", b_side="left", num=1, sw=3)
        connect(cv, rp, pp, a_side="right", b_side="left", num=2, sw=3)
        connect(cv, pp, resp, a_side="right", b_side="left", num=3, sw=3)
        # failover loop below the panels
        by = max(rp.bottom, pp.bottom)
        arrow(cv, [(pp.x + 300, by + 6), (pp.x + 300, by + 40), (rp.x + 330, by + 40), (rp.x + 330, by + 8)], dash="dashed",
              color="#e8590c", sw=3, label="Automatic failover on a transient error: next most appropriate model (your mode still applies)",
              label_pos="below", label_size=15, label_color="#d9480f")
        # step legend
        sy = by + 84
        txts = [
            (1, "Your app calls the deployment name. Nothing else changes in your code."),
            (2, "The router analyses the request, estimates which eligible model does best, then applies the mode inside your subset."),
            (3, "The chosen model answers and the response says which model it was. Cached tokens work when the same model serves consecutive requests."),
        ]
        sx = fx
        stw = (W - 52 - 2 * 40) / 3
        for n, t in txts:
            numbered(cv, sx + 16, sy + 14, n, theme="blue", d=30)
            cv.text(sx + 44, sy, "\n".join(wrap_text(t, stw - 50, 16)), size=16, color=INK)
            sx += stw + 40
    return flow.bottom


# ---------------------------------------------------------------------------------------------- 2 modes
BAR_H = [150, 146, 142, 134, 128, 104, 80, 56]
PRICE = [4, 3, 2, 3, 1, 2, 1, 1]


def mode_panel(cv, x, y, w, h, name, th_name, band, in_band, pick):
    th = get_theme(th_name)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 18, y + 12, name, size=26, color=th.deep)
    bl = wrap_text(band, w - 36, 15)
    cv.text(x + 18, y + 46, "\n".join(bl), size=15, color=INK)
    base = y + 74 + len(bl) * 19 + 176
    bw, gap = 34, 14
    x0 = x + (w - (8 * bw + 7 * gap)) / 2
    for i in range(8):
        bx = x0 + i * (bw + gap)
        top = base - BAR_H[i]
        inb = i < in_band
        cv.rect(bx, top, bw, BAR_H[i], stroke=th.stroke if inb else "#adb5bd", fill=th.fill if inb else "#e9ecef",
                style="hachure" if inb else "solid", sw=4 if i == pick else 2, rough=0 if i == pick else None, round_=False)
        if i == pick:
            tag = Chip("pick", theme=th_name, size=14, pad_x=8, pad_y=3, fill="solid", sw=2).place(cv, bx + bw / 2 - 24, top - 32)
        cv.text(bx + (bw - text_size("ABCDEFGH"[i], 15)[0]) / 2, base + 4, "ABCDEFGH"[i], size=15, color=MUTED_)
        for d in range(PRICE[i]):
            cv.ellipse(bx + 1 + d * 8.5, base + 28, 7, 7, stroke="#f08c00", fill="#ffec99", style="solid", sw=1, rough=0)
    # band line
    thr = base - BAR_H[max(in_band - 1, 0)]
    cv.line((x0 - 10, thr - 1), (x0 + 8 * bw + 7 * gap + 10, thr - 1), stroke=th.stroke, sw=2, dash="dashed")
    cv.register("mode:" + name, x, y, w, h, container=True)


def section_modes(cv, y):
    y = banner(cv, y, 2, "How the three modes choose", "Same prompt, same pool: the mode decides how wide a quality band the router may shop in (band widths are the docs' examples)")
    key = Card(C, "How to read the three charts", [
        "Each bar = one pool model (A to H); height = estimated quality for this one prompt",
        "Orange dots = relative price (more dots, more expensive)",
        "Coloured bars are inside the mode's band; the dashed line is the band edge",
        "'pick' = the router's choice: the cheapest bar inside the band",
        "! Illustration only: not real scores, prices or band widths",
    ], theme="gray", title_size=19, body_size=15)
    best = Card(span(2), "Choosing a mode and a subset", [
        "# What real traffic looks like (docs experiment, a point in time)",
        "Cost mode sends most traffic to smaller, cheaper models and escalates only when the prompt needs it; Balanced spreads across cheap and mid-tier models; Quality favors frontier and reasoning models",
        "# Rules of thumb",
        "Start with Balanced and watch the distribution of serving models in Azure Monitor for a few weeks before tuning",
        "Cost mode for latency-insensitive or batch pipelines; Quality mode for the critical path",
        "Change one lever at a time (mode or subset) and re-run your evaluation",
        "Use the model subset as a compliance gate: only models you approve; it is also your fallback set",
        "Design for the smallest context window in the subset, and always log the model field of each response",
        "Keep a direct deployment for traffic that must be deterministic (hybrid pattern, section 4)",
    ], theme="blue", icon="traffic-manager", title_size=20, body_size=15, src=[S_HOW, S_HOWTO])
    h = max(372, best.h, key.h)
    mode_panel(cv, colx(0), y, C, h, "Cost", "yellow", "Wider band (for example about 5-6% below the best). Picks the most cost-effective model inside it.", 5, 4)
    mode_panel(cv, colx(1), y, C, h, "Balanced (default)", "blue", "Small band (for example about 1-2% below the best). Picks the most cost-effective model inside it.", 3, 2)
    mode_panel(cv, colx(2), y, C, h, "Quality", "violet", "No band: the highest-rated model for this prompt wins and cost is ignored.", 1, 0)
    key.place(cv, colx(3), y, h=h)
    best.place(cv, colx(4), y, h=h)
    return y + h


# ---------------------------------------------------------------------------------------------- 3 switches
def section_switches(cv, y):
    y = banner(cv, y, 3, "Switches, limits and where it runs", "Failover is on by default; the preview controls (session affinity, routing trace) are opt-in")
    cards = [
        std("blue", "Automatic failover", [
            "On by default since Mar 2026; no setup",
            "A transient failure of the selected model redirects the request to the next most appropriate model",
            "Your mode keeps applying during failover",
            "Your subset is the fallback set, so prompts never reach models you did not approve",
            "! A single-model subset has nothing to fail over to: pick at least two",
        ], icon="traffic-manager", src=[S_ROUTER]),
        std("blue", "Session affinity", [
            "Chat Completions only; not Agent Service",
            "Body: routing_config.session_affinity = { mode: sticky | none, session_id }; or header x-ms-session-id (the body wins)",
            "Session ID: 1-256 Unicode code points, opaque, no secrets or PII",
            "Association expires after 30 minutes without a successful create or update",
            "Response model_router_details.session_affinity: mode, source (payload or header) and decision: initialize, retain or switch",
            "Best effort: never overrides policy, safety, capability, quota, availability or fallback. Helps prompt-cache reuse; no guarantee",
            "No valid ID, or lookup unavailable: normal routing, and no session_affinity object in the response",
        ], badge="preview", icon="traffic-manager", src=[S_HOWTO, S_MON]),
        std("violet", "Per-request routing trace", [
            "Opt in with header Foundry-Features: ModelRouterControls=V1Preview (Chat Completions, api-version 2024-10-21)",
            "Response gains model_selection_details.model_router_details",
            "mode, plus routing_trace[]: latency_ms and an ordered attempts[] list (model, result.status, optional error code and message)",
            "More than one attempt means a fallback happened",
            "! Preview shape: every field is optional, so parse defensively and do not infer details that are absent",
        ], badge="preview", icon="metrics", src=[S_MON]),
        std("grape", "Azure Policy gate", [
            "The built-in 'Foundry model deployments should only use approved models' policy applies to the model subset",
            "Allowed publishers must include Microsoft (the router) and every provider in the subset",
            "Deny or Audit; one non-compliant model rejects the whole deployment",
            "Step-by-step flow in section 6",
        ], icon="policy", src=[S_POL]),
        std("blue", "Regions and deployment types", [
            "Global Standard and Data Zone Standard only",
            "32 regions: Global Standard in all of them, Data Zone Standard in a subset",
            "No Data Zone Standard in Brazil South, Canada Central and East, South Africa North, Switzerland West, UAE North, UK South and West, West Central US",
            "Only models that exist in the region are usable there",
        ], icon="regions", src=[S_ROUTER]),
        std("blue", "Inputs, reasoning and caching", [
            "Images accepted, but the routing decision uses text only; no audio input",
            "Reasoning model chosen: temperature and top_p are ignored; reasoning_effort supported from 2025-11-18",
            "Prompt caching works only when the same model serves consecutive requests with an overlapping prefix",
            "Content filter and TPM limit apply to the router deployment as a whole",
        ], icon="openai", src=[S_ROUTER, S_CACHE]),
    ]
    _, b = row(cv, 0, y, cards, gap=G)
    return b


# ---------------------------------------------------------------------------------------------- 4 use it
def section_use(cv, y, mh=0):
    y = banner(cv, y, 4, "Use it from your code, from agents, and next to direct deployments",
               "Only the model string changes: the router is just another deployment name")
    top = y
    # (a) responses api
    with cv.panel(colx(0), top, title="Responses API: automatic vs direct", theme="blue", style="dotted", pad=22, title_size=24,
                  w=span(2), min_h=mh) as pa:
        iw = span(2) - 44
        cw = (iw - 20) / 2
        h1 = code_box(cv, pa.ix, pa.iy, cw, "Automatic selection", [
            "response = client.responses.create(", '    model="model-router",', '    input="Summarise this ticket",', ")",
            "print(response.model)   # who answered"], "blue", size=15)
        code_box(cv, pa.ix + cw + 20, pa.iy, cw, "Deterministic (direct)", [
            "response = client.responses.create(", '    model="gpt-5.2",', '    input="Summarise this ticket",', ")",
            "print(response.model)   # always the same"], "gray", size=15, h=h1)
        c1 = Card(iw, "Only the model string changes", [
            "response.model returns who answered; for the router, for example gpt-4.1-nano",
            "reasoning_effort is supported from router version 2025-11-18",
        ], theme="blue", title_size=19, body_size=15, src=[S_RESP])
        c1.place(cv, pa.ix, pa.iy + h1 + 20)
        cy = c1.bottom + 22
        cv.text(pa.ix, cy, "Platform features on every call, router or direct", size=18, color=get_theme("blue").deep)
        fl = ChipFlow(["failover (router)", "prompt caching", "content filtering", "RBAC", "model identification", "data residency",
                       "per-deployment TPM limits"], iw, theme="blue", size=15, fill="soft")
        fl.place(cv, pa.ix, cy + 30)
        n0 = Note(iw, "Session affinity and the per-request routing trace are documented for Chat Completions only, and both are preview. "
                  "Agent Service does not support session affinity.", kind="preview", title="Preview controls and the API", size=15, src=[S_HOWTO])
        n0.place(cv, pa.ix, fl.y + fl.h + 22)
    # (b) agents
    with cv.panel(colx(2), top, title="Foundry agents: a router deployment as the agent's model", theme="green", style="dotted",
                  pad=22, title_size=24, w=span(2), min_h=mh) as pb:
        iw = span(2) - 44
        ag = Box(iw, "Your agents", sub='model = the router deployment name (portal dropdown, create_agent, or agents.createVersion with kind "prompt")',
                 theme="green", icon="agent", icon_pos="left", icon_size=36, size=19, sub_size=14, fill="hatch")
        ag.place(cv, pb.ix, pb.iy)
        cw3 = (iw - 2 * 20) / 3
        dep = []
        for i, (nm, mode_, th, subset) in enumerate((
                ("router-frontier", "Quality mode", "violet", "gpt-5.6-sol, gpt-5, o4-mini"),
                ("router-balanced", "Balanced mode", "blue", "gpt-5-mini, gpt-4.1, gpt-4.1-mini"),
                ("router-efficient", "Cost mode", "yellow", "gpt-5-nano, gpt-4.1-nano"))):
            c = Card(cw3, nm, ["Subset: " + subset], theme=th, subtitle=mode_, title_size=19, body_size=15, icon="traffic-manager",
                     icon_size=30)
            c.place(cv, pb.ix + i * (cw3 + 20), ag.bottom + 56)
            dep.append(c)
            connect(cv, ag, c, a_side="bottom", b_side="top", ta=(cw3 / 2 + i * (cw3 + 20)) / iw, tb=0.5, route="elbow", sw=2)
        cv.text(pb.ix, dep[0].bottom + 8, "Docs example: three router deployments, tailored per agent", size=14, color=MUTED_)
        c2 = Card(iw, "How routing behaves with agents", [
            "Routing is per request: a 5-turn conversation may use 3 different models",
            "Tool-aware: strict mechanistic tool calls go to mid-tier models; RAG synthesis and multi-step MCP or Toolbox work go to frontier models",
            "Documented estimate: typically 50-60% of agent traffic is 'simple'",
            "Eligible models: OpenAI, open-source and Anthropic models that support the requested tool (see Agent Service tool support by region and model)",
            "! The docs example subsets include o4-mini, which retires 2026-11-19 (as of 2026-11-03): adjust before copying",
        ], theme="green", title_size=19, body_size=15, src=[S_AGENTS])
        c2.place(cv, pb.ix, dep[0].bottom + 36)
    # (c) hybrid
    with cv.panel(colx(4), top, title="Hybrid pattern: router plus direct", theme="blue", style="dotted", pad=22, title_size=24,
                  w=span(2), min_h=mh) as pc:
        iw = span(2) - 44
        app = Box(230, "Your app or gateway", sub="classifies the traffic", theme="gray", icon="app", icon_pos="top", icon_size=34,
                  size=18, sub_size=14, fill="hatch", h=190)
        app.place(cv, pc.ix, pc.iy + 6)
        tw_ = iw - 230 - 110
        t1 = Box(tw_, "model-router deployment", sub="General traffic: diverse prompts, cost and latency matter", theme="blue",
                 icon="traffic-manager", icon_pos="left", icon_size=34, size=19, sub_size=14, fill="hatch", h=84)
        t1.place(cv, pc.ix + 230 + 110, pc.iy + 6)
        t2 = Box(tw_, "Direct deployment (for example gpt-5.2)", sub="Compliance- or parameter-sensitive traffic: the same model every request",
                 theme="gray", icon="openai", icon_pos="left", icon_size=34, size=19, sub_size=14, fill="hatch", h=84)
        t2.place(cv, pc.ix + 230 + 110, pc.iy + 6 + 190 - 84)
        connect(cv, app, t1, a_side="right", b_side="left", ta=0.2, tb=0.5, route="elbow", num=1, sw=2)
        connect(cv, app, t2, a_side="right", b_side="left", ta=0.8, tb=0.5, route="elbow", num=2, sw=2)
        yy = app.bottom + 28
        cw2 = (iw - 20) / 2
        r1 = Card(cw2, "Router fits when", ["The workload is diverse", "Cost and latency matter", "You want one endpoint, agents and automatic failover",
                                          "You want a simpler lifecycle: one deployment to manage"], theme="blue", title_size=19, body_size=15,
                  src=[S_HOWTO])
        r2 = Card(cw2, "Direct fits when", ["You need the same model on every request (determinism)",
                                          "The traffic is compliance- or parameter-sensitive"],
                  theme="gray", title_size=19, body_size=15, src=[S_RESP])
        _, rb = row(cv, pc.ix, yy, [r1, r2], gap=20)
        n1 = Note(iw, "Best of both: send general traffic to model-router and keep a direct deployment for anything that needs one fixed model. "
                  "Both are just deployment names in the same call.", kind="tip", title="Hybrid is the recommended shape", size=15)
        n1.place(cv, pc.ix, rb + 20)
    return max(pa.bottom, pb.bottom, pc.bottom), [pa.h, pb.h, pc.h]


# ---------------------------------------------------------------------------------------------- 5 deploy
def section_deploy(cv, y):
    y = banner(cv, y, 5, "Deploy and size it", "Portal or REST; Global Standard or Data Zone Standard; quota scales with your subscription's usage tier")
    steps = Card(span(2), "Deploy it", [
        "# Portal",
        "Model catalog, model-router, then Default settings (Balanced, all models) or Custom settings (routing mode, Route to a subset of models)",
        "Choose Global Standard or Data Zone Standard",
        "# REST or CLI",
        "routing.mode and routing.models carry the mode and the subset (call on the right)",
        "# Watch out",
        "! Claude in your subset: deploy it first, same Foundry account and matching SKU, or the call fails with InvalidResourceProperties",
        "Auto-update moves the deployment to new router versions, which changes the model pool and the cost",
    ], theme="blue", icon="foundry", title_size=20, body_size=15, src=[S_HOWTO, S_WORK])
    vt = Table([("Version", 130), ("Status", 150), "Notes"], [
        ["2025-11-18", ("Active (latest)", "green"), "GA. Updated in place with new models and features; the schedule retires it 2027-05-20"],
        ["2025-08-07", ("Frozen", "gray"), "Fixed model set; no new additions"],
        ["2025-05-19", ("Frozen", "gray"), "Fixed model set; no new additions"],
    ], w=span(2), theme="blue", size=15, head_size=15, title="Router versions (version stays 2025-11-18 as models are added)", title_size=20)
    nt = Note(span(2), "The schedule page still lists the two frozen versions as Preview with a 2026-08-30 retirement date that has already passed. "
              "Check the Models API for their real status.", kind="warn", title="Docs disagree", size=14, src=[S_SCHED, S_ROUTER])
    code = ["PUT .../accounts/{acct}/deployments/{name}?api-version=2025-10-01-preview",
            "{",
            '  "sku": { "name": "GlobalStandard", "capacity": 10 },',
            '  "properties": {',
            '    "model": { "format": "OpenAI", "name": "model-router", "version": "2025-11-18" },',
            '    "routing": {',
            '      "mode": "balanced",              // balanced | cost | quality',
            '      "models": [ { "format": "OpenAI", "name": "gpt-4.1", "version": "2025-04-14" }, ... ]',
            "    }",
            "  }",
            "}"]
    notes_ = ["routing.mode: balanced (the default), cost or quality",
              "routing.models: your subset; each entry needs format, name and version from the supported-models table (format Meta for Llama-4-Maverick, for example)",
              "Name at least one model; leave the list out and the default set for the mode applies",
              "Claude models in the list must already be deployed (same account, matching SKU)"]
    H1 = max(steps.h, vt.h + 20 + nt.h, code_need(span(2), code, 14, notes_, S_HOWTO))
    steps.place(cv, colx(0), y, h=H1)
    code_box(cv, colx(2), y, span(2), "REST: create a router deployment (api-version 2025-10-01-preview)", code, "blue", size=14, h=H1,
             src=S_HOWTO, notes=notes_)
    vt.place(cv, colx(4), y)
    nt.place(cv, colx(4), vt.bottom + 20)
    y2 = y + H1 + 36
    qt = Table([("Tier", 120), "Global Standard RPM", "Global Standard TPM", "Data Zone Standard RPM", "Data Zone Standard TPM"], [
        ["Tier 1", "1,000", "1M", "300", "300K"], ["Tier 2", "2,000", "2M", "670", "670K"], ["Tier 3", "4,000", "4M", "1,000", "1M"],
        ["Tier 4", "7,000", "7M", "2,000", "2M"], ["Tier 5", "10,000", "10M", "3,000", "3M"], ["Tier 6", "15,000", "15M", "4,000", "4M"],
    ], w=span(3), theme="yellow", size=15, head_size=15, title="Router quota by usage tier (as of 2026-11-03)", title_size=20,
        first_col_theme="yellow", align=["left", "right", "right", "right", "right"])
    qt.place(cv, colx(0), y2)
    cv.text(colx(0), qt.bottom + 8, "Learn: Azure OpenAI quotas and limits (quota tiers)", size=12, color=LINK, link=S_QUOTAS[1])
    sz = Card(span(3), "Sizing, limits and cost", [
        "One deployment, one limit: the TPM limit and the content filter belong to the router deployment as a whole, not to each underlying model",
        "Quota scales with your subscription's usage tier; Global Standard and Data Zone Standard have separate limits",
        "Billing: router usage is charged for input prompts at the rate on the pricing page",
        "Monitor cost in the Azure portal; Cost Analysis can filter by the tag deployment = your router deployment name",
    ], theme="yellow", icon="cost-management", title_size=20, body_size=15, src=[S_ROUTER])
    sz.place(cv, colx(3), y2 + qt.title_h, h=qt.h - qt.title_h)
    return max(y + H1, nt.bottom, qt.bottom + 26, sz.bottom)


# ---------------------------------------------------------------------------------------------- 6 run it
def section_run(cv, y, mh=0):
    y = banner(cv, y, 6, "Run it well: observe, evaluate, govern", "Which model answered, did routing beat the baseline, and may the subset be used at all", "violet")
    top = y
    # ---- observe
    with cv.panel(colx(0), top, title="Observe: which model answered?", theme="violet", style="dotted", pad=22, title_size=24, w=span(2),
                  min_h=mh) as po:
        iw = span(2) - 44
        cw = 440
        x2 = po.ix + cw + 24
        cards = [
            Card(iw - cw - 24, "Per response", [
                "Top-level model (response.model in the Responses API) names the serving model: log it with every request",
                "Several attempts in routing_trace mean a fallback happened (preview, Chat Completions)",
            ], theme="violet", title_size=19, body_size=15, src=[S_MON]),
            Card(iw - cw - 24, "Aggregate", [
                "Azure Monitor metrics: filter by deployment and split by underlying model to see the routing distribution",
                "Cost Analysis: filter by tag deployment = the router deployment name",
            ], theme="violet", title_size=19, body_size=15, icon="monitor", src=[S_MON]),
        ]
        stack_h = cards[0].h + cards[1].h + 18
        h1 = code_box(cv, po.ix, po.iy, cw, "Response fields (outline, not literal JSON)", [
            'model: "gpt-4.1-nano"      <- who answered',
            "model_selection_details:  <- preview, opt in",
            "  model_router_details:",
            '    mode: "balanced"',
            "    routing_trace[]:",
            "      latency_ms",
            "      attempts[]  (ordered)",
            "        model",
            "        result.status",
            "        error.code, error.message  (optional)",
            "    session_affinity:      <- if you sent an ID",
            "      mode, source, decision",
        ], "violet", size=14, h=stack_h)
        col(cv, x2, po.iy, cards, gap=18)
        n = Note(iw, "Router is not a fixed model: consecutive turns can hit different models. Use session affinity (preview, Chat Completions only) "
                 "or a direct deployment when a conversation must stay on one model.", kind="gotcha", title="Different turns, different models", size=15)
        n.place(cv, po.ix, po.iy + max(h1, stack_h) + 24)
    # ---- evaluate
    with cv.panel(colx(2), top, title="Evaluate: hill-climb against a baseline", theme="violet", style="dotted", pad=22, title_size=24,
                  w=span(2), min_h=mh) as pe:
        iw = span(2) - 44
        bw = (iw - 3 * 40) / 4
        loop = []
        for i, (t, s, th) in enumerate((("Baseline", "your current model or a direct deployment", "gray"),
                                        ("Change ONE lever", "routing mode or model subset, never both at once", "violet"),
                                        ("Re-run", "representative prompts by category, judge model, app config fixed", "violet"),
                                        ("Compare", "quality, cost, latency (median, p90, p95), policy", "violet"))):
            b = Box(bw, t, sub=s, theme=th, size=18, sub_size=13, fill="hatch", h=150)
            b.place(cv, pe.ix + i * (bw + 40), pe.iy + 4)
            numbered(cv, b.x + 18, b.y + 2, i + 1, theme=th, d=28, size=16)
            loop.append(b)
        for a, b in zip(loop, loop[1:]):
            connect(cv, a, b, sw=2)
        ly = loop[0].bottom + 6
        arrow(cv, [(loop[3].cx, ly), (loop[3].cx, ly + 34), (loop[1].cx, ly + 34), (loop[1].cx, ly + 4)], dash="dashed", color="#6741d9", sw=2,
              label="iterate", label_pos="below", label_size=14)
        c3 = Card(iw, "Before you rely on it", [
            "Write acceptance criteria first, across quality, cost, latency and policy",
            "Use the Model Router Auto Evaluation toolkit (GitHub microsoft-foundry/Model-Router-Auto-Evaluation) with a judge model",
            "Human review for high-impact decisions; then a limited production test",
            "Keep a direct deployment where determinism is needed",
            "More samples: ModelRouter-Distribution, a Model Router demo app and On-Call Copilot",
        ], theme="violet", title_size=19, body_size=15, icon="ml", src=[S_EVAL])
        c3.place(cv, pe.ix, ly + 74)
    # ---- govern
    with cv.panel(colx(4), top, title="Govern: Azure Policy on the subset", theme="grape", style="dotted", pad=22, title_size=24,
                  w=span(2), min_h=mh) as pg:
        iw = span(2) - 44
        st = [
            ("An admin assigns the built-in policy", "'Foundry model deployments should only use approved models' (formerly 'Cognitive Services Deployments should only use approved Registry Models'). Owner or Resource Policy Contributor; takes up to 15 min to propagate."),
            ("It is evaluated against the model subset", "Allowed publishers must include Microsoft (the router itself) and each provider in the subset, for example Anthropic."),
            ("Developers feel it at deploy time", "Portal greys out unapproved models and offers View blocked. ARM, CLI and REST reject the whole deployment if any model is non-compliant."),
            ("Effects and reporting", "Deny or Audit. Existing deployments show in the Compliance dashboard within 24 h or after an on-demand scan."),
        ]
        yy = pg.iy
        bxs = []
        for i, (t, s) in enumerate(st):
            b = Box(iw - 40, t, sub=s, theme="grape", size=18, sub_size=14, fill="hatch")
            b.place(cv, pg.ix + 40, yy)
            numbered(cv, pg.ix + 14, b.cy, i + 1, theme="grape", d=30)
            bxs.append(b)
            yy = b.bottom + 34
        for a, b in zip(bxs, bxs[1:]):
            connect(cv, a, b, a_side="bottom", b_side="top", sw=2)
        n2 = Note(iw, "Extra built-in policy definitions for allowed regions, required routing rules and logging are in preview.", kind="preview",
                  size=14, src=[S_POL])
        n2.place(cv, pg.ix, yy - 6)
    return max(po.bottom, pe.bottom, pg.bottom), [po.h, pe.h, pg.h]


# ---------------------------------------------------------------------------------------------- notes + sources
def section_sources(cv, y):
    y = banner(cv, y, 7, "Gotchas and sources", None, "gray")
    nw = (W - 3 * G) / 4
    notes = [
        Note(nw, "Claude models must be deployed from the catalog before they go in a subset, and the policy must allow the publisher Microsoft and every provider in it. "
             "Single-model subsets disable failover. New models never join a subset on their own.", kind="gotcha", title="Subsets are explicit", size=15),
        Note(nw, "Context window = the smallest model in the pool. A large prompt succeeds only if it happens to be routed to a big-context model: use a subset, "
             "summarise, truncate or retrieve only the relevant sections.", kind="warn", title="Long prompts", size=15),
        Note(nw, "Router nature: the concepts page calls it a trained language model, the how-it-works page a lightweight ML model that is not an LLM itself. "
             "Provider naming: the router page and the Bicep sample say xAI, the Models page lists SpaceXAI. This canvas follows the router page.",
             kind="warn", title="Docs disagree", size=15, src=[S_ROUTER, S_HOW]),
        Note(nw, "Retirement dates cannot be extended, and the router pool and the retirement schedule are separate pages: re-check your subset against the schedule (part 2).",
             kind="info", title="Pool vs schedule", size=15),
    ]
    _, nb = row(cv, 0, y, notes, gap=G)
    y = nb + 40
    sources(cv, 0, y, [
        ("Model router concepts", learn("openai/concepts/model-router")),
        ("How model router works", learn("openai/concepts/model-router-how-it-works")),
        ("Use model router", learn("openai/how-to/model-router")),
        ("What's new in model router", learn("foundry-models/whats-new-model-router")),
        ("Monitor model router", learn("openai/how-to/monitor-model-router")),
        ("Evaluate model router", learn("openai/how-to/evaluate-model-router")),
        ("Govern model router with Azure Policy", learn("how-to/model-router-policy")),
        ("Model router with agents", learn("openai/how-to/model-router-agents")),
        ("Responses API: automatic vs direct routing", learn("openai/how-to/responses-model-routing")),
        ("Prompt caching", learn("openai/how-to/prompt-caching")),
        ("Azure OpenAI quotas and limits", learn("openai/quotas-limits")),
        ("Working with models (auto-update)", learn("openai/how-to/working-with-models")),
        ("Model retirement schedule", learn("openai/concepts/model-retirement-schedule")),
    ], w=W, cols=3)
