"""Model versions and lifecycle: upgrade policy, 18/12-month clocks, the Nov 2026 retirement cliff, migration, notifications and benchmarks."""
from __future__ import annotations

from generator.xd import *
from generator.xd import Note as _KitNote
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="model-router-lifecycle-part-2", title="Model versions, lifecycle and the retirement cliff", section="2", group="Models", order=23.5,
    description="How model versions age in Foundry: versionUpgradeOption, who is auto-upgraded, the 18- and 12-month lifecycle clocks, "
                "preview rules, the Nov 2026 retirement cliff, migration phases, notifications, the Models API and benchmarks.",
    tags=["model lifecycle", "retirement", "versions", "migration", "models api", "benchmarks"],
)

W, G, C = 3000, 48, 460          # canvas width, standard gap, one-column card width (6-column grid)
MUTED_ = "#495057"


def span(n: int) -> float:
    return n * C + (n - 1) * G


def colx(i: int) -> float:
    return i * (C + G)


def L(label: str, path: str, base: str = "azure/foundry"):
    return (label, learn(path, base=base))


S_VERS = L("Model versions", "foundry-models/concepts/model-versions")
S_WORK = L("Working with models (upgrade configuration)", "openai/how-to/working-with-models")
S_RET = L("Foundry Models lifecycle and support policy", "openai/concepts/model-retirements")
S_SCHED = L("Model retirement schedule", "openai/concepts/model-retirement-schedule")
S_MIG = L("Model migration process", "foundry-models/concepts/model-migration")
S_BENCH = L("Model leaderboards and benchmarks", "concepts/model-benchmarks")
S_BENCH2 = L("Benchmark a model in the catalog", "how-to/benchmark-model-in-catalog")
S_BEVAL = L("Benchmark evaluations (preview)", "observability/how-to/benchmark-evaluations")
S_CHOICE = L("Model choice guide", "foundry-models/how-to/model-choice-guide")
S_ROUTER = L("Model router concepts", "openai/concepts/model-router")
S_MODELSAPI = ("Models - List (REST API)", learn("rest/api/aiservices/accountmanagement/models", base=""))
S_HEALTH = ("Service Health alerts", learn("azure/service-health/alerts-activity-log-service-notifications-portal", base=""))


# ---------------------------------------------------------------------------------------------- helpers
def Note(w, text, **kw):
    """Kit Note plus bottom breathing room when it carries a Learn: link (the kit draws that link flush with the border)."""
    n = _KitNote(w, text, **kw)
    if kw.get("src") and "min_h" not in kw:
        n = _KitNote(w, text, min_h=n.h + 14, **kw)
    return n


def banner(cv, y, n, title, sub=None, theme="grape"):
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


def code_box(cv, x, y, w, title, lines, th_name="blue", size=15, h=None, src=None):
    """Monospace code panel with a coloured title; returns its height."""
    th = get_theme(th_name)
    lh = size * metrics.line_ratio(metrics.MONO)
    need = 12 + 26 + 8 + len(lines) * lh + 14 + (18 if src else 0)
    H = max(need, h or 0)
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 16, y + 10, title, size=18, color=th.deep)
    cv.text(x + 16, y + 44, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    if src:
        cv.text(x + 16, y + H - 26, "Learn: " + src[0], size=12, color=LINK, link=src[1])
    cv.register("code:" + title, x, y, w, H)
    return H


def two_pass(fn, cv, y):
    """Run a section twice: measure the side-by-side panels on a scratch canvas, then draw them all at the tallest height."""
    _, hs = fn(Canvas("scratch"), y, 0)
    return fn(cv, y, max(hs))[0]


def seg(cv, x0, x1, y, h, th_name, text="", fill="hatch", dash="solid", size=15, sw=2, round_=False, align="center"):
    """A coloured lifecycle segment with centred (or left-aligned) text."""
    th = get_theme(th_name)
    bg, fs = (th.fill, "hachure") if fill == "hatch" else (th.fill, "solid")
    cv.rect(x0, y, x1 - x0, h, stroke=th.stroke, fill=bg, style=fs, sw=sw, dash=dash, round_=round_)
    if text:
        tw, thh = text_size(text, size)
        tx = x0 + 14 if align == "left" else x0 + (x1 - x0 - tw) / 2
        cv.text(tx, y + (h - thh) / 2, text, size=size, color=th.deep)


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Model versions, lifecycle and the retirement cliff",
        "How a model version ages in Foundry: upgrade policy, lifecycle clocks, what retires when, how to migrate "
        "(facts as of 2026-11-03; part 1 covers the model router)", w=W)
    y = bottom + 36
    y = summary_tiles(cv, y)
    y = section_versions(cv, y + 56)[0]
    y = section_clocks(cv, y + 56)[0]
    y = two_pass(section_hand, cv, y + 56)
    y = two_pass(section_cliff, cv, y + 56)
    y = section_migration(cv, y + 56)
    y = section_check(cv, y + 56)[0]
    y = section_bench(cv, y + 56)
    section_sources(cv, y + 56)


# ---------------------------------------------------------------------------------------------- summary
def summary_tiles(cv, y):
    tiles = [
        ("18", "months: standard GA lifecycle", "Retirement date is set at launch; Deprecated at month 12", "grape", 60),
        ("12", "months: Anthropic, DeepSeek, Fireworks, Mistral GA", "SpaceXAI Grok from 4.7: minimum six months", "grape", 60),
        ("90-120", "days before retirement: replacement named", "Testable in Global Standard about 90 days out, in provisioned regions about 30", "grape", 36),
        ("60", "days: minimum GA retirement notice", "Email to subscription owners plus Azure Service Health", "grape", 60),
        ("410", "Gone: what retired models return", "Provisioned and Batch are never auto-upgraded", "red", 60),
        ("Nov 19", "2026 retirement cliff", "o1, o3, o4-mini families and Llama-4-Maverick (as of 2026-11-03)", "red", 36),
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
                      ("Fine-tuning: from data to a deployed model", "blue"), ("Model router: one deployment, many models (part 1)", "blue")):
        c = Chip(label, theme=th, size=15, fill="soft").place(cv, cx, y - 2)
        cx += c.w + 14
    return y + 38


# ---------------------------------------------------------------------------------------------- 1 versions
def lanes_upgrade(cv, x, y, w):
    """versionUpgradeOption: when does a Standard deployment move to the new version? Returns bottom y."""
    LW = 440
    bx0, BW = x + LW + 20, w - LW - 20
    f1, f2, f3 = 0.20, 0.34, 0.86
    lanes = [
        ("OnceNewDefaultVersionAvailable", 'Portal: "Upgrade once new default version becomes available"', f2, "blue", "new default version"),
        ("OnceCurrentVersionExpired", 'Portal: "Once the current version expires". null means this one', f3, "blue", "new default"),
        ("NoAutoUpgrade", 'Portal: "Opt out of automatic model version upgrades"', f3, "red", "stops working"),
    ]
    top, lh, lg = y + 36, 72, 18
    for n, f in ((1, f1), (2, f2), (3, f3)):
        mx = bx0 + BW * f
        cv.line((mx, top - 6), (mx, top + 3 * lh + 2 * lg + 4), stroke="#868e96", sw=2, dash="dashed")
        numbered(cv, mx, top - 22, n, theme="grape", d=28, size=16)
    for i, (name, sub, f, th_new, new_txt) in enumerate(lanes):
        ly = top + i * (lh + lg)
        cv.text(x, ly + 4, name, size=18, color=get_theme("grape").deep)
        cv.text(x, ly + 4 + 18 * metrics.line_ratio() + 2, "\n".join(wrap_text(sub, LW - 10, 14)), size=14, color=MUTED_)
        by = ly + 12
        sx = bx0 + BW * f
        seg(cv, bx0, sx, by, 48, "gray", "current version", size=15, align="left")
        seg(cv, sx, bx0 + BW, by, 48, th_new, new_txt, size=15)
    ly = top + 3 * lh + 2 * lg + 18
    tw = (w - 2 * 36) / 3
    for i, (n, t) in enumerate((
            (1, "A new version becomes the default; Azure tells you at least 2 weeks before"),
            (2, "Auto-update moves the deployment within 2 weeks of the default changing (preview versions: starting 2 weeks after release)"),
            (3, "The current version retires; without an upgrade, inference returns 410 Gone"))):
        numbered(cv, x + i * (tw + 36) + 14, ly + 12, n, theme="grape", d=28, size=16)
        cv.text(x + i * (tw + 36) + 38, ly, "\n".join(wrap_text(t, tw - 42, 15)), size=15, color=INK)
    return ly + 3 * 15 * metrics.line_ratio() + 8


def section_versions(cv, y, mh=0):
    y = banner(cv, y, 1, "Versions and the upgrade policy: who moves, and when",
               "Standard deployment types follow versionUpgradeOption; Provisioned, Batch and fine-tuned models are never auto-upgraded")
    top = y
    with cv.panel(colx(0), top, title="When does my Standard deployment move to a new version?",
                  sub="versionUpgradeOption - Global Standard, Data Zone Standard and Standard deployments", theme="grape", style="dotted",
                  pad=22, title_size=24, sub_size=16, w=span(3), min_h=mh) as pa:
        lanes_upgrade(cv, pa.ix, pa.iy + 4, span(3) - 44)
    tbl = Table([("Deployment type", 330), ("Auto-upgraded?", 120), "What happens at retirement"], [
        ["Global Standard, Data Zone Standard, Standard", CHECK,
         "Rolling, region by region, on a schedule published in advance; follows versionUpgradeOption. Quota is handled for you."],
        ["Priority processing", CHECK, "Same process as Standard"],
        ["Provisioned (Global, Data Zone, Regional)", CROSS,
         "Never auto-upgraded: migrate by hand, in place or side by side (section 3). Make sure quota exists for the target model first."],
        ["Batch", CROSS, "Side by side: deploy the new model, resubmit jobs, retire the old deployment. A shared retirement date does not mean auto-upgrade for Global Batch."],
        ["Fine-tuned models", CROSS, "Not auto-upgraded: re-tune on the replacement. Training and deployment retire on separate clocks."],
    ], w=span(3), theme="grape", size=14, head_size=15, title="Who is auto-upgraded?", title_size=20, first_col_theme="grape")
    tbl.place(cv, colx(3), top)
    n1 = Note(span(3), "Pinning a version does not stop the upgrade: a pinned version moves to the then-default at retirement, unless you chose NoAutoUpgrade, "
              "in which case the deployment stops working.", kind="gotcha", title="Pinned does not mean safe", size=15, src=[S_VERS, S_WORK])
    n1.place(cv, colx(3), max(tbl.bottom + 20, pa.bottom - n1.h))
    bottom = max(pa.bottom, n1.bottom)
    y2 = bottom + 36
    c1 = Card(span(2), "Two versions to track", [
        "Model version: a dated release inside a family (for example gpt-4o 2024-05-13 vs 2024-08-06). A variant is a size tier (GPT-5, -mini, -nano).",
        "API version: the api-version query parameter. The v1 route /openai/v1/ needs none.",
        "Azure keeps the previous major version until its retirement date and tells you at least 2 weeks before a new version becomes the default.",
        "The upgrade happens even where the new version is not yet deployed (rolling, region by region).",
    ], theme="grape", icon="versions", title_size=20, body_size=15, src=[S_VERS])
    c2 = Card(span(2), "Setting the policy", [
        "Property versionUpgradeOption on the deployment; Standard deployment types only",
        "Read it with REST, PowerShell or CLI; update it with REST, PowerShell or the portal",
        "! Azure CLI cannot update it",
        "Managed compute deployments also expose versionUpgradeOption: OnceNewDefaultVersionAvailable",
    ], theme="grape", icon="gear", title_size=20, body_size=15, src=[S_WORK])
    c3 = Card(span(2), "Partner models and quota", [
        "Partner models: a new version may get a new model ID (for example Meta-Llama-3 and 3.1 70B became Llama-3.3-70B-Instruct), and the API contract may change",
        "Standard auto-upgrades: quota is handled automatically",
        "Provisioned: you must have quota for the target model before migrating (section 3)",
    ], theme="grape", icon="quotas", title_size=20, body_size=15, src=[S_RET])
    _, b = row(cv, 0, y2, [c1, c2, c3], gap=G)
    return b, [pa.h]


# ---------------------------------------------------------------------------------------------- 2 clocks
def ruler(cv, x, y, w):
    """Lifecycle length ruler (to scale) plus a zoom on the last six months. Returns bottom y."""
    LW = 330
    ax0 = x + LW + 10
    s = 80.0
    tail = w - LW - 10 - 18 * s
    lanes = [
        ("Standard GA", "OpenAI and most other models: 18 months"),
        ("Anthropic, DeepSeek, Fireworks, Mistral", "GA lifecycle: 12 months"),
        ("SpaceXAI Grok (from 4.7)", "GA: at least six months"),
        ("Preview", "not sooner than about 90 days"),
    ]
    top, lh, lg = y + 4, 50, 16
    for i, (name, sub) in enumerate(lanes):
        ly = top + i * (lh + lg)
        nl = wrap_text(name, LW - 10, 17)
        total = len(nl) * 17 * 1.25 + 15 * 1.25
        cv.text(x, ly + (lh - total) / 2, "\n".join(nl), size=17, color=get_theme("grape").deep)
        cv.text(x, ly + (lh - total) / 2 + len(nl) * 17 * 1.25, sub, size=14, color=MUTED_)
    # lane 1: standard GA
    y1 = top
    seg(cv, ax0, ax0 + 12 * s, y1, lh, "green", "GA: production-ready, retirement date already set", size=16)
    seg(cv, ax0 + 12 * s, ax0 + 18 * s, y1, lh, "yellow", "Deprecated: existing customers only", size=16)
    seg(cv, ax0 + 18 * s, ax0 + 18 * s + tail, y1, lh, "red", "410 Gone", fill="solid", size=16)
    # lane 2: 12 months
    y2 = top + (lh + lg)
    seg(cv, ax0, ax0 + 12 * s, y2, lh, "blue", "GA lifecycle: 12 months", size=16)
    seg(cv, ax0 + 12 * s, ax0 + 18 * s + tail, y2, lh, "red", "Retired: 410 Gone", size=16)
    # lane 3: grok
    y3 = top + 2 * (lh + lg)
    seg(cv, ax0, ax0 + 6 * s, y3, lh, "teal", "at least 6 months", size=16)
    arrow(cv, [(ax0 + 6 * s + 8, y3 + lh / 2), (ax0 + 9 * s, y3 + lh / 2)], dash="dashed", color="#099268", sw=3)
    cv.text(ax0 + 9 * s + 14, y3 + lh / 2 - 10, "the retirement date is on the schedule page", size=15, color=MUTED_)
    # lane 4: preview
    y4 = top + 3 * (lh + lg)
    seg(cv, ax0, ax0 + 3 * s, y4, lh, "orange", "not sooner than about 90 days", size=15)
    arrow(cv, [(ax0 + 3 * s + 8, y4 + lh / 2), (ax0 + 5 * s, y4 + lh / 2)], dash="dashed", color="#e8590c", sw=3)
    cv.text(ax0 + 5 * s + 14, y4 + lh / 2 - 22, "sometimes extended; then force-upgraded to a newer preview or GA\n(at least 30 days notice), or retired with no replacement (30 days notice)",
            size=15, color=MUTED_)
    # axis
    ay = y4 + lh + 14
    cv.line((ax0, ay), (ax0 + 18 * s + tail, ay), stroke=INK, sw=2)
    for m in range(0, 19, 3):
        cv.line((ax0 + m * s, ay - 5), (ax0 + m * s, ay + 7), stroke=INK, sw=2)
        t = str(m) if m < 18 else "18 months"
        cv.text(ax0 + m * s - text_size(t, 15)[0] / 2, ay + 10, t, size=15, color=INK)
    cv.text(x, ay + 8, "months from GA launch (preview: from launch)", size=14, color=MUTED_)
    # zoom funnel
    zy = ay + 78
    zx0, zx1 = ax0, ax0 + 18 * s
    cv.poly([(ax0 + 12 * s, ay + 38), (ax0 + 18 * s, ay + 38), (zx1, zy), (zx0, zy), (ax0 + 12 * s, ay + 38)], kind="line",
            stroke="#868e96", sw=2, dash="dashed", fill="#f1f3f5", fill_style="solid", rough=0)
    cv.text(x + 8, zy + 16, "Zoom: months 12 to 18\nof an 18-month GA\nlifecycle", size=16, color=get_theme("grape").deep)
    zs = (zx1 - zx0) / 6
    za = zy + 128                       # zoom axis y
    cv.rect(x - 4, zy + 4, w + 8, 266, stroke="#adb5bd", fill="transparent", style="solid", sw=1, dash="dotted", round_=True)
    cv.line((zx0, za), (zx1, za), stroke=INK, sw=3)
    for m in range(12, 19):
        cv.line((zx0 + (m - 12) * zs, za - 5), (zx0 + (m - 12) * zs, za + 7), stroke=INK, sw=2)
        cv.text(zx0 + (m - 12) * zs - text_size(str(m), 14)[0] / 2, za + 18, str(m), size=14, color=MUTED_)
    ev_above = [
        (12.0, 1, "Deprecated: existing customers only", "yellow"),
        (14.5, 2, "Official replacement named about 90-120 days out", "grape"),
        (16.0, 4, "GA retirement notice: at least 60 days (email + Service Health)", "grape"),
        (18.0, 6, "Retired: 410 Gone. Standard types auto-upgrade; Provisioned moves by hand", "red"),
    ]
    ev_below = [
        (15.0, 3, "Replacement testable in Global Standard (about 90 days out)", "blue"),
        (17.0, 5, "Replacement testable in provisioned regions (about 30 days out)", "blue"),
    ]
    LWD = 250
    for m, n, t, th in ev_above:
        ex = zx0 + (m - 12) * zs
        lines = wrap_text(t, LWD, 15)
        h_ = len(lines) * 15 * 1.25
        if n == 2:
            hbrace(cv, zx0 + 2 * zs + 8, zx0 + 3 * zs - 8, za - 22, side="bottom", depth=12, color=get_theme(th).stroke, sw=2)
        numbered(cv, ex, za, n, theme=th, d=28, size=16)
        cv.text(ex - LWD / 2 if n not in (1, 6) else (ex - 20 if n == 1 else ex - LWD + 40), za - 48 - h_,
                "\n".join(lines), size=15, color=INK, align="center" if n not in (1, 6) else "left", w=LWD)
    for m, n, t, th in ev_below:
        ex = zx0 + (m - 12) * zs
        lines = wrap_text(t, LWD, 15)
        numbered(cv, ex, za, n, theme=th, d=28, size=16)
        cv.text(ex - LWD / 2, za + 46, "\n".join(lines), size=15, color=INK, align="center", w=LWD)
    return zy + 270


def section_clocks(cv, y, mh=0):
    y = banner(cv, y, 2, "Lifecycle clocks: how long a version lives", "Standard GA = 18 months with the retirement date set at launch; other publishers and previews run shorter clocks")
    top = y
    # ---- right column first, so the ruler panel can match its height
    st = Table([("Stage", 128), "What it means", ("New deployments", 118), ("Existing ones", 96)], [
        [("Preview", "orange"), "Experimental: weights, runtime and API schema may change; not guaranteed to reach GA", CHECK, CHECK],
        [("GA", "green"), "Production-ready: weights and APIs fixed; security patches do not change outputs", CHECK, CHECK],
        [("Legacy (optional)", "yellow"), "Newer, more capable models exist: plan to migrate. A model may skip this stage", "Until deprecation", CHECK],
        [("Deprecated", "yellow"), "Existing customers keep creating and managing; new customers are blocked. Existing = the subscription has ever deployed that version; "
         "a new subscription in the same tenant does not inherit access", "Existing customers only", CHECK],
        [("Retired", "red"), "Removed from service: all inference returns 410 Gone", CROSS, CROSS],
    ], w=span(2), theme="grape", size=14, head_size=14, title="Five lifecycle stages", title_size=20)
    st.place(cv, colx(4), top)
    with cv.panel(colx(4), st.bottom + 24, title="Where a new model shows up first", sub="Launch order by deployment type", theme="blue",
                  style="dotted", pad=20, title_size=22, sub_size=15, w=span(2)) as pl:
        iw = span(2) - 40
        bw = (iw - 3 * 26) / 4
        bxs = []
        for i, (t, s) in enumerate((("Global Standard", "At launch: broadest availability, lowest latency"),
                                    ("Global Provisioned", "Right behind it: reserved throughput"),
                                    ("Data Zone Standard + Provisioned", "Processing stays in a data zone"),
                                    ("Standard + Provisioned", "Last: regional-only"))):
            b = Box(bw, t, sub=s, theme="blue", size=17, sub_size=13, fill="hatch", h=132)
            b.place(cv, pl.ix + i * (bw + 26), pl.iy)
            numbered(cv, b.x + 16, b.y + 2, i + 1, theme="blue", d=26, size=15)
            bxs.append(b)
        for a, b in zip(bxs, bxs[1:]):
            connect(cv, a, b, sw=2)
    n_az = Note(span(2), "Every model launches in Global Standard but is not guaranteed in the other types. Specialised models (audio, image, video) are often "
                "Global or Data Zone only. Azure Government has no Global Standard and usually one version at a time, with a 30-day overlap.",
                kind="info", title="Availability varies", size=14, src=[S_RET])
    n_az.place(cv, colx(4), pl.bottom + 20)
    rb = n_az.bottom
    with cv.panel(colx(0), top, title="Lifecycle clocks on one scale", sub="Retirement dates cannot be extended; emergency retirement is possible for security or compliance issues",
                  theme="grape", style="dotted", pad=22, title_size=24, sub_size=16, w=span(4), min_h=rb - top) as pr:
        ruler(cv, pr.ix, pr.iy + 6, span(4) - 44)
    return max(pr.bottom, rb), [pr.h]


# ---------------------------------------------------------------------------------------------- 3 by hand
def flow_steps(cv, x, y, w, steps, th_name):
    """Vertical numbered steps joined by arrows; returns bottom y."""
    bxs = []
    cy = y
    for i, (t, s) in enumerate(steps):
        b = Box(w - 44, t, sub=s, theme=th_name, size=18, sub_size=14, fill="hatch", pad=12)
        b.place(cv, x + 44, cy)
        numbered(cv, x + 18, b.cy, i + 1, theme=th_name, d=32, size=18)
        bxs.append(b)
        cy = b.bottom + 30
    for a, b in zip(bxs, bxs[1:]):
        connect(cv, a, b, a_side="bottom", b_side="top", sw=2)
    return bxs[-1].bottom


def section_hand(cv, y, mh=0):
    y = banner(cv, y, 3, "Moving by hand: Provisioned, Batch and fine-tuned models",
               "Standard types auto-upgrade; everything else is your migration. Worked examples first, then the two migration patterns")
    e1 = Card(span(2), "Example: gpt-4o 2024-05-13 retires 2027-01-14", [
        "Replacement: gpt-5.1 version 2025-11-13",
        "Global Standard and Data Zone Standard deployments are upgraded automatically at retirement",
        "Provisioned deployments are not: create gpt-5.1 deployments and move traffic before the date",
        "A shared retirement date does not mean auto-upgrade for Global Batch offers",
        "Regional Standard deployments already retired on 2026-03-31",
    ], theme="grape", icon="versions", title_size=20, body_size=15, src=[S_RET])
    e2 = Card(span(2), "Example: four model versions retire 2027-04-14", [
        "gpt-4o 2024-08-06 and 2024-11-20, gpt-4o-mini 2024-07-18 and gpt-4.1-mini 2025-04-14",
        "All active customer-facing base-model inference offers in Azure public cloud, in all applicable regions",
        "Regional Standard deployments that already retired stay retired",
        "Fine-tuned models have their own, later schedules",
    ], theme="grape", icon="versions", title_size=20, body_size=15, src=[S_RET])
    e3 = Card(span(2), "Embeddings run on extended clocks", [
        "text-embedding-3-large, text-embedding-3-small and text-embedding-ada-002 are handled differently from inference models",
        "The schedule shows 2028-02-09 for embeddings",
        "You cannot upgrade between embedding models in place: switching means re-embedding your data",
    ], theme="grape", icon="versions", title_size=20, body_size=15, src=[S_SCHED])
    _, eb = row(cv, 0, y, [e1, e2, e3], gap=G)
    top = eb + 34
    with cv.panel(colx(0), top, title="Provisioned: in-place migration", sub="Same deployment name and size", theme="yellow", style="dotted", pad=22,
                  title_size=24, sub_size=16, w=span(2), min_h=mh) as pa:
        iw = span(2) - 44
        bb = flow_steps(cv, pa.ix, pa.iy, iw, [
            ("Check capacity and quota", "for the target model, before you start"),
            ("Update the deployment", "Model version update: portal, REST or CLI. Model family change: REST or CLI"),
            ("Azure migrates the traffic", "Over 20-30 minutes with no downtime; the state goes from updating to succeeded"),
        ], "yellow")
        n_a = Note(iw, "Only between provisioned deployments of the same type.", kind="warn", size=15)
        n_a.place(cv, pa.ix, bb + 24)
        Note(iw, "Make sure quota exists for the target model before you migrate. PTU capacity is model-agnostic and fungible across provisioned managed deployments.",
             kind="info", title="Quota first", size=15, src=[S_RET]).place(cv, pa.ix, n_a.bottom + 16)
    with cv.panel(colx(2), top, title="Provisioned and Batch: side by side", sub="Multi-deployment migration", theme="yellow", style="dotted", pad=22,
                  title_size=24, sub_size=16, w=span(2), min_h=mh) as pb:
        iw = span(2) - 44
        bb = flow_steps(cv, pb.ix, pb.iy, iw, [
            ("Create a new deployment", "of the replacement model: a new PTU deployment, or a new batch deployment"),
            ("Test, then shift traffic", "Weighted routing is your gateway's job"),
            ("Confirm the old one is idle", "No requests for 5-10 minutes (Azure OpenAI Requests metric)"),
            ("Delete the old deployment", "Batch: resubmit the jobs to the new deployment first"),
        ], "yellow")
        Note(iw, "Priority processing is the exception: it follows the same upgrade process as Standard, and auto-upgrade is supported.", kind="tip",
             size=15, src=[S_WORK]).place(cv, pb.ix, bb + 24)
    ft = Table([("Model", 160), ("Version", 130), ("Training retires", 330), "Deployment retires"], [
        ["gpt-4o", "2024-08-06", "no earlier than 2027-04-01", "2027-10-01"],
        ["gpt-4o-mini", "2024-07-18", "no earlier than 2027-04-01", "2027-10-01"],
        ["gpt-4.1, -mini, -nano", "2025-04-14", "no earlier than 2027-04-14", "2027-10-14"],
        ["o4-mini", "2025-04-16", "no earlier than 2027-04-16", "2027-10-16"],
    ], w=span(2) - 44, theme="grape", size=14, head_size=14, title="Two clocks: training and deployment", title_size=20)
    with cv.panel(colx(4), top, title="Fine-tuned models: re-tune, do not wait", sub="Never auto-upgraded", theme="grape", style="dotted", pad=22,
                  title_size=24, sub_size=16, w=span(2), min_h=mh) as pc:
        ft.place(cv, pc.ix, pc.iy)
        n1 = Note(span(2) - 44, "Training retires no earlier than the base model, for existing customers only; otherwise it retires with the base model. "
                  "After training retires you can still deploy models you already trained, until the deployment date.", kind="info", size=14, src=[S_RET])
        n1.place(cv, pc.ix, ft.bottom + 18)
        n2 = Note(span(2) - 44, "The schedule page lists o4-mini fine-tuning at 2027-05-19 (training) and 2027-11-19 (deployment), unlike the lifecycle page above.",
                  kind="warn", title="Docs disagree", size=14, src=[S_SCHED])
        n2.place(cv, pc.ix, n1.bottom + 14)
    return max(pa.bottom, pb.bottom, pc.bottom), [pa.h, pb.h, pc.h]


# ---------------------------------------------------------------------------------------------- 4 cliff
def cliff(cv, x, y, w):
    """To-scale 37-day axis from today (2026-11-03) with a fan of date cards. Returns bottom y."""
    ax0, dpx, days = x + 70, 75.0, 37
    ay = y + 84
    cv.line((ax0, ay), (ax0 + days * dpx, ay), stroke=INK, sw=4)
    for d in range(days + 1):
        big = d % 7 == 0
        cv.line((ax0 + d * dpx, ay - (9 if big else 4)), (ax0 + d * dpx, ay + (9 if big else 4)), stroke=INK, sw=2 if big else 1)
    cv.ellipse(ax0 - 12, ay - 12, 24, 24, stroke="#2f9e44", fill="#b2f2bb", style="solid", sw=3, rough=0)
    cv.text(ax0 - 30, ay - 62, "Today", size=18, color=get_theme("green").deep)
    cv.text(ax0 - 30, ay - 40, "2026-11-03", size=14, color=MUTED_)
    scale_txt = "1 tick = 1 day, to scale; taller tick = 1 week"
    cv.text(ax0 + days * dpx - text_size(scale_txt, 14)[0], ay - 84, scale_txt, size=14, color=MUTED_)
    cards_def = [
        (12, "Nov 15", "in 12 days", "red", [
            "claude-haiku-4-5 retires (in the router pool)",
            "codex-mini retires",
            "Cohere-embed-v3-* is deprecated from this day; it retires 2027-02-15 (replacement Cohere-embed-v5-fast or -pro)"]),
        (14, "Nov 17", "in 14 days", "orange", [
            "gpt-chat-latest preview versions retire (two dates: 2026-11-17 and 2026-12-08)"]),
        (16, "Nov 19", "in 16 days: the cliff", "red", [
            "o1, o1-pro, o3, o3-deep-research, o3-pro: replacement gpt-5.6-sol",
            "o3-mini, o4-mini: replacement gpt-5.6-terra",
            "Llama-4-Maverick-17B-128E-Instruct-FP8 retires",
            "! o4-mini and Llama-4-Maverick are also in the router pool (part 1)"]),
        (21, "Nov 24", "in 21 days", "red", ["claude-opus-4-5 retires", "Replacement: see the schedule page"]),
        (27, "Nov 30", "in 27 days", "red", ["claude-sonnet-4-5 retires (it is in the router pool); replacement claude-sonnet-5-5"]),
        (35, "Dec 8", "in 35 days", "orange", ["gpt-chat-latest preview versions: the second retirement date"]),
    ]
    n = len(cards_def)
    wc = (w - (n - 1) * 30) / n
    cards = []
    for i, (d, date, when, th, body) in enumerate(cards_def):
        cliff_card = d == 16
        c = Card(wc, date, body, theme=th, subtitle=when, title_size=24 if cliff_card else 21, body_size=15,
                 fill="solid" if cliff_card else "hatch", sw=4 if cliff_card else 2, sub_size=15,
                 badge="preview" if th == "orange" else None)
        cards.append(c)
    H = max(c.h for c in cards)
    cy = ay + 112
    ymids = [ay + 40, ay + 54, ay + 68, ay + 68, ay + 54, ay + 40]
    for i, ((d, date, when, th, body), c) in enumerate(zip(cards_def, cards)):
        c.place(cv, x + i * (wc + 30), cy, h=H)
        mx = ax0 + d * dpx
        thm = get_theme(th)
        big = d == 16
        r = 15 if big else 11
        cv.ellipse(mx - r, ay - r, 2 * r, 2 * r, stroke=thm.stroke, fill=thm.fill, style="solid", sw=3, rough=0)
        tw, _ = text_size(date, 19 if big else 17)
        cv.text(mx - tw / 2, ay - 44 - (6 if big else 0), date, size=19 if big else 17, color=thm.deep)
        arrow(cv, [(mx, ay + r + 2), (mx, ymids[i]), (c.cx, ymids[i]), (c.cx, c.y - 4)], color=thm.stroke, sw=2 if not big else 3,
              dash="solid" if not big else "solid")
    return cy + H


def rail(cv, x, y, w, entries, th_name="grape"):
    """Vertical dated rail; returns bottom y."""
    th = get_theme(th_name)
    hs = []
    for date, text, hl in entries:
        lines = wrap_text(text, w - 170, 15)
        hs.append(max(len(lines) * 15 * metrics.line_ratio(), 22) + 14)
    cv.line((x + 9, y + 12), (x + 9, y + sum(hs[:-1]) + 12), stroke=th.stroke, sw=3)
    cy = y
    for (date, text, hl), h in zip(entries, hs):
        t2 = get_theme("blue" if hl else th_name)
        cv.ellipse(x + 1, cy + 4, 16, 16, stroke=t2.stroke, fill=t2.fill, style="solid", sw=2, rough=0)
        cv.text(x + 30, cy, date, size=17, color=t2.deep)
        cv.text(x + 150, cy + 1, "\n".join(wrap_text(text, w - 170, 15)), size=15, color=INK)
        cy += h
    return cy


def section_cliff(cv, y, mh=0):
    y = banner(cv, y, 4, "The retirement cliff (as of 2026-11-03)", "Six dates in the next five weeks, drawn to scale; dates cannot be extended", "red")
    with cv.panel(0, y, title="Next five weeks: what retires, and what replaces it", sub="Source: the retirement schedule page, read 2026-11-03; the Models API is the source of truth",
                  theme="red", style="dotted", pad=22, title_size=26, sub_size=16, w=W) as pc:
        cliff(cv, pc.ix, pc.iy + 6, W - 44)
    top = pc.bottom + 40
    later = [
        ("2027-01-14", "gpt-4o 2024-05-13 (replacement gpt-5.1 2025-11-13)", False),
        ("2027-01-17", "Phi-4 family (replacement microsoft--phi-4 on Foundry Managed Compute)", False),
        ("2027-01-31", "Grok-4, grok-code-fast-1 and Llama-3.3-70B", False),
        ("2027-02-09", "gpt-5 and gpt-5-nano", False),
        ("2027-02-15", "Cohere-embed-v3-* (replacement Cohere-embed-v5-fast or -pro)", False),
        ("2027-04-14", "gpt-4.1 family, gpt-4o-mini and later gpt-4o versions", False),
        ("2027-05-20", "model-router 2025-11-18 (GA)", True),
        ("2027-07-13", "gpt-5.1", False),
        ("2027-09-02", "gpt-5.4", False),
        ("2027-10-26", "gpt-5.5", False),
        ("2028-01-11", "gpt-5.6 family", False),
        ("2028-02-09", "embedding models (extended timeline)", False),
        ("2028-02-20", "DeepSeek-V4 GA", False),
    ]
    with cv.panel(colx(0), top, title="Later retirements on the schedule (selected)", sub="Blue dot = the model router version from part 1", theme="grape",
                  style="dotted", pad=22, title_size=24, sub_size=16, w=span(4), min_h=mh) as pl:
        half = (span(4) - 44 - 60) / 2
        b1 = rail(cv, pl.ix, pl.iy + 4, half, later[:7])
        b2 = rail(cv, pl.ix + half + 60, pl.iy + 4, half, later[7:])
    rules = Card(span(2), "Rules that do not bend", [
        "Retirement dates are not extendable: there is no exception process",
        "Emergency retirement with shortened notice is possible for security or compliance reasons",
        "Provisioned and Batch deployments are never auto-upgraded; NoAutoUpgrade deployments stop working at retirement",
        "Fireworks pay-per-token retirement notice is 15 days (PTU: 12 months)",
        "! Some schedule rows still read Preview or GA after their date has passed (for example MAI-Image-2.5 on 2026-10-01): trust the Models API",
    ], theme="red", icon="service-health", title_size=20, body_size=15, src=[S_RET, S_SCHED])
    rules.place(cv, colx(4), top, h=max(pl.h, mh))
    return max(pl.bottom, rules.bottom), [pl.h, rules.h]


# ---------------------------------------------------------------------------------------------- 5 migration
def section_migration(cv, y):
    y = banner(cv, y, 5, "Migration: six phases from schedule to switch-off",
               "Do not wait for the named replacement: start evaluating newer models now. Keep the old deployment warm for about 30 days as a rollback")
    phases = [
        ("Discover", "What retires, and when?", ["Retirement schedule page", "Azure Service Health advisories", "Models API: lifecycleStatus and deprecation dates"]),
        ("Assess", "Which replacement fits?", ["Leaderboards, compare and trade-off charts (section 7)",
                                              "Confirm API compatibility, feature support, deployment type and region, capacity and quota"]),
        ("Adapt", "Change prompts, schemas, settings", ["Prompt Optimizer and Agent optimization (Foundry only)", "Simulator"]),
        ("Validate", "Does it hold up?", ["Azure AI Evaluation SDK (30+ evaluators) or portal evaluation",
                                         "Compare quality, latency and cost together, on your own prompts and data"]),
        ("Roll out", "Move traffic safely", ["versionUpgradeOption; PTU in place or side by side", "Continuous evaluation and Azure Monitor alerts",
                                            "Weighted routing is your gateway's job"]),
        ("Retire", "Switch the old model off", ["Models API and the observability dashboard show what is still in use",
                                               "Keep the old deployment warm for about 30 days as a rollback"]),
    ]
    heads, cards = [], []
    for i, (name, q, body) in enumerate(phases):
        hb = Box(C, name, sub=q, theme="grape", size=24, sub_size=15, fill="hatch", h=92)
        hb.place(cv, colx(i), y)
        numbered(cv, hb.x + 24, hb.y + 4, i + 1, theme="grape", d=34, size=20)
        heads.append(hb)
        cards.append(Card(C, None, body, theme="grape", body_size=15, fill="soft"))
    ch = max(c.h for c in cards)
    cy = y + 92 + 34
    for hb, c in zip(heads, cards):
        c.place(cv, hb.x, cy, h=ch)
        connect(cv, hb, c, a_side="bottom", b_side="top", sw=2, dash="dotted")
    for a, b in zip(heads, heads[1:]):
        connect(cv, a, b, sw=3)
    nt = Note(W, "The replacement named 90-120 days before retirement is Microsoft's recommended target and, where supported, the model used for automatic upgrades - "
              "it does not limit your manual choices. Compare candidates on your own prompts and data, not on public benchmarks alone.",
              kind="tip", title="Name your own replacement early", size=16, src=[S_RET, S_MIG])
    nt.place(cv, 0, cy + ch + 24)
    return nt.bottom


# ---------------------------------------------------------------------------------------------- 6 find out
def section_check(cv, y, mh=0):
    y = banner(cv, y, 6, "How you find out, and how to check in code", "Notices are pushed (email, Service Health); the Models API is pull and always current")
    top = y
    with cv.panel(colx(0), top, title="Push and pull", sub="Standard GA has no separate announcement: its retirement date is set at launch", theme="grape",
                  style="dotted", pad=22, title_size=24, sub_size=16, w=span(3), min_h=mh) as pa:
        iw = span(3) - 44
        pw = (iw - 24) * 2 / 3
        qw = iw - 24 - pw
        bw = (pw - 20) / 2
        g = Box(bw, "GA retirement notice", sub="at least 60 days before retirement; to subscription owners with active deployments", theme="grape",
                size=19, sub_size=14, fill="hatch", h=100)
        g.place(cv, pa.ix, pa.iy)
        p = Box(bw, "Preview retirement notice", sub="at least 30 days before; the deployment may be auto-upgraded when a replacement applies", theme="orange",
                size=19, sub_size=14, fill="hatch", h=100)
        p.place(cv, pa.ix + bw + 20, pa.iy)
        gy = g.bottom + 46
        cw = (pw - 32 - 20) / 2
        with cv.panel(pa.ix, gy, title="Push: you are told", theme="blue", style="dashed", pad=16, title_size=20, w=pw) as pu:
            c1 = Card(cw, "Email", ["Sent automatically to subscription owners with active deployments"], theme="blue", badge="push", icon="info-protection",
                      title_size=20, body_size=15, src=[S_RET])
            c2 = Card(cw, "Azure Service Health", ["Health advisory for affected subscriptions",
                                                   "Filter service: Azure OpenAI Service (there is no separate Microsoft Foundry entry)",
                                                   "Create an alert rule for email, text message or webhook"],
                      theme="violet", badge="push", icon="service-health", title_size=20, body_size=15, src=[S_HEALTH])
            row(cv, pu.ix, pu.iy, [c1, c2], gap=20)
        with cv.panel(pa.ix + pw + 24, gy, title="Pull: you ask", theme="teal", style="dashed", pad=16, title_size=20, w=qw, min_h=pu.h) as pl:
            c3 = Card(qw - 32, "Models API", ["Per subscription and location, always current",
                                              "Fields: lifecycleStatus, deprecation.inference, deprecation.fineTune and per-SKU deprecationDate",
                                              "Legacy and Deprecated transitions are visible here in real time"],
                      theme="teal", badge="pull", icon="api-connections", title_size=20, body_size=15, src=[S_MODELSAPI])
            c3.place(cv, pl.ix, pl.iy)
        connect(cv, g, pu, a_side="bottom", b_side="top", ta=0.5, tb=(bw / 2) / pw, sw=2)
        connect(cv, p, pu, a_side="bottom", b_side="top", ta=0.5, tb=(bw + 20 + bw / 2) / pw, sw=2, dash="dashed")
    vt = Table([("Stage in docs and portal", 190), ("API lifecycleStatus", 170), ("API deprecation.inference", 200), "Meaning"], [
        ["Preview", "Preview", "future date or not set", "Experimental; may change or be removed"],
        ["Generally Available", "GenerallyAvailable", "future date, set at launch", "Production-ready; fixed weights and API"],
        [("Deprecated", "yellow"), ("Deprecating", "yellow"), "future date", "Still serves inference; blocked for new customers"],
        [("Retired", "red"), ("Deprecated", "red"), "past date", "Fully retired: inference returns 410 Gone"],
    ], w=span(3), theme="grape", size=14, head_size=14, title="Same stages, different words: docs and portal vs the API", title_size=20)
    vt.place(cv, colx(3), top)
    code = ["GET https://management.azure.com/subscriptions/{sub}/providers/Microsoft.CognitiveServices/locations/{location}/models?api-version=2024-10-01",
            "",
            'if lifecycleStatus == "Deprecated"          -> Retired (410 Gone)',
            'if lifecycleStatus == "Deprecating"         -> Deprecated (existing customers only)',
            "if deprecation.inference < today            -> Retired, even if lifecycleStatus lags",
            'if lifecycleStatus == "GenerallyAvailable"  -> GA',
            'if lifecycleStatus == "Preview"             -> Preview']
    code_h = 12 + 26 + 8 + len(code) * 14 * metrics.line_ratio(metrics.MONO) + 14 + 18
    nt = Note(span(3), "A model the docs call Deprecated (still works, blocked for new customers) shows up in the API as lifecycleStatus Deprecating. "
              "The API value Deprecated means retired.", kind="gotcha", title="Deprecated means retired in the API", size=15, src=[S_RET])
    cy = max(vt.bottom + 24, pa.bottom - code_h - 24 - nt.h)
    code_box(cv, colx(3), cy, span(3), "Decide a model's stage in code (checks in this order)", code, "grape", size=14, h=code_h, src=S_MODELSAPI)
    nt.place(cv, colx(3), cy + code_h + 24)
    return max(pa.bottom, nt.bottom), [pa.h]


# ---------------------------------------------------------------------------------------------- 7 benchmarks
def section_bench(cv, y):
    y = banner(cv, y, 7, "Benchmarks and choosing: pick, or replace, a model", "From a public leaderboard to your own data - the steps before you commit to a migration", "violet")
    cards = [
        Card(C, "Leaderboards", [
            "Quality index: average of exact_match, pass@1 or arena_hard over bigbench_hard (1,000), chembench, frontierscience, gpqa, mbppplus, mmlu_pro (1,000), musr, tau2_telecom",
            "Safety: attack success rate (HarmBench standard, contextual, copyright), WMDP, ToxiGen F1",
            "Performance: 14 days x 24 trials, 800 input and 200 output tokens; latency mean, P50, P90, P95, P99; GTPS, TTPS, TTFT, time between tokens",
            "Cost, scenario and embeddings leaderboards (accuracy, F1, MAP, NDCG@10, Spearman, V-measure)",
        ], theme="violet", badge="preview", icon="metrics", title_size=20, body_size=14, src=[S_BENCH]),
        Card(C, "Compare and trade-offs", [
            "Compare up to 3 models side by side",
            "Trade-off charts sit next to the leaderboards in the catalog and help you weigh the dimensions against each other",
            "Used in the Assess phase of a migration (section 5)",
        ], theme="violet", icon="dashboard", title_size=20, body_size=15, src=[S_BENCH2]),
        Card(C, "Benchmark evaluations", [
            "Built-in datasets run against your own deployments or agents",
            "Optional judge model scores the answers",
            "Use it to confirm a leaderboard winner on your workload",
        ], theme="violet", badge="preview", icon="ml", title_size=20, body_size=15, src=[S_BEVAL]),
        Card(C, "Model choice guide", [
            "GPT-5: reasoning effort minimal, low, medium (default) or high",
            "Parallel tool calls are unsupported at minimal effort",
            "GPT-4.1: low latency and high throughput",
            "PTU when you need a latency SLA",
        ], theme="blue", icon="openai", title_size=20, body_size=15, src=[S_CHOICE]),
        Card(C, "Or let the router choose", [
            "The guide suggests model router, citing up to 60% lower inference cost at comparable quality",
            "! A docs claim: no measurement method is stated. Evaluate it against your baseline (part 1)",
        ], theme="blue", icon="traffic-manager", title_size=20, body_size=15, src=[S_CHOICE, S_ROUTER]),
    ]
    nt = Note(C, "The leaderboards cost method is described two ways: actual USD per run on one page, a 3:1 input-to-output token estimate on another.",
              kind="warn", title="Docs disagree", size=14, src=[S_BENCH])
    hh = max(c.h for c in cards)
    xs = []
    for i, c in enumerate(cards):
        c.place(cv, colx(i), y, h=hh)
    nt.place(cv, colx(5), y)
    for a, b in zip(cards[:4], cards[1:4]):
        connect(cv, a, b, sw=2)
    return y + hh


# ---------------------------------------------------------------------------------------------- sources
def section_sources(cv, y):
    y = banner(cv, y, 8, "Gotchas and sources", None, "gray")
    nw = (W - 2 * G) / 3
    notes = [
        Note(nw, "Preview models are force-upgraded or retired, with at least 30 days notice and no option to stay. Never pin production to a preview model.",
             kind="gotcha", title="Preview is a moving target", size=15, src=[S_RET]),
        Note(nw, "Some schedule rows still read Preview or GA after their date passed. Docs 'Deprecated' is API 'Deprecating'. The o4-mini fine-tuning dates differ between "
             "the lifecycle and schedule pages. Check the Models API.", kind="warn", title="Docs disagree", size=15, src=[S_SCHED]),
        Note(nw, "Name your own replacement, test it on your own data, and migrate Provisioned and Batch by hand. The Models API is the source of truth for dates.",
             kind="tip", title="Plan from the Models API", size=15, src=[S_MODELSAPI]),
    ]
    _, nb = row(cv, 0, y, notes, gap=G)
    y = nb + 40
    sources(cv, 0, y, [
        ("Foundry Models lifecycle and support policy", learn("openai/concepts/model-retirements")),
        ("Model retirement schedule", learn("openai/concepts/model-retirement-schedule")),
        ("Model versions", learn("foundry-models/concepts/model-versions")),
        ("Working with models (upgrade configuration)", learn("openai/how-to/working-with-models")),
        ("Model migration process", learn("foundry-models/concepts/model-migration")),
        ("Models - List (REST API)", learn("rest/api/aiservices/accountmanagement/models", base="")),
        ("Service Health alerts", learn("azure/service-health/alerts-activity-log-service-notifications-portal", base="")),
        ("Model leaderboards and benchmarks", learn("concepts/model-benchmarks")),
        ("Benchmark a model in the catalog", learn("how-to/benchmark-model-in-catalog")),
        ("Benchmark evaluations (preview)", learn("observability/how-to/benchmark-evaluations")),
        ("Model choice guide", learn("foundry-models/how-to/model-choice-guide")),
        ("Model router concepts", learn("openai/concepts/model-router")),
    ], w=W, cols=3)
