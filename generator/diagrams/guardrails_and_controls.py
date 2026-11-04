"""Guardrails and controls end-to-end: where each safety check runs (4 intervention points), layers that attach a policy,
risk catalogue, hosted-agent / toolbox / egress / third-party / control-plane layers and the Responsible AI wrapper."""
from generator.xd import *
from generator.xd import metrics
from generator.xd.blocks import draw_mark
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="guardrails-and-controls", title="Guardrails and controls", section="2", group="Observability and safety", order=44,
    description="Guardrails end to end: the four intervention points and which risk checks run where, layers that attach a policy, "
                "risk catalogue, hosted-agent, toolbox and control-plane guardrails, plus the Responsible AI wrapper.",
    tags=["guardrails", "content-safety", "prompt-shields", "responsible-ai", "hosted-agents"],
)

W = 3500                      # content width of the canvas
AS_OF = "as of 2026-11-03"
LH = metrics.line_ratio()

# risk family -> theme (chip colour)
FAM = dict(harm="pink", attack="red", pm="lime", pii="cyan", ground="teal", task="orange", custom="gray")


# ====================================================================== small helpers
def src_line(cv: Canvas, x: float, y: float, items, size=12) -> float:
    """Clickable 'Learn: ...' lines for hand-drawn diagrams; returns bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def txt(cv: Canvas, x, y, s, *, size=15, color=INK, wrap=None, align="left", w=None, link=None):
    """Text helper that returns the El (use .bottom / .right)."""
    return cv.text(x, y, s, size=size, color=color, wrap=wrap, align=align, w=w, link=link)


def badge_w(kind: str, size=13) -> float:
    return metrics.line_width(STATUS.get(kind, ("gray", kind))[1], size) + 18


class CChip(Rect2):
    """Control chip: rounded rect, risk-family colour, optional sub-line and right-aligned badges."""

    def __init__(self, w, label, *, theme="pink", sub=None, badges=(), dashed=False, size=15, sub_size=13, pad=10):
        self.th = get_theme(theme)
        self.w, self.size, self.sub_size, self.pad, self.dashed, self.badges = w, size, sub_size, pad, dashed, list(badges)
        self.label = label
        bws = [badge_w(b) for b in self.badges]
        self.bw_total = sum(bws) + 6 * max(len(bws) - 1, 0)
        avail = w - 2 * pad - (self.bw_total + 8 if self.badges else 0)
        self.lines = metrics.wrap_text(label, avail * 0.97, size)
        self.sub_lines = metrics.wrap_text(sub, (w - 2 * pad) * 0.97, sub_size) if sub else []
        head_h = max(len(self.lines) * size * LH, 22 if self.badges else 0)
        self.head_h = head_h
        self.h = pad * 0.8 * 2 + head_h + (3 + len(self.sub_lines) * sub_size * LH if sub else 0)
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        cv.rect(x, y, self.w, H, stroke=th.stroke, fill=("transparent" if self.dashed else th.fill),
                style="solid" if self.dashed else "hachure", sw=2, dash="dashed" if self.dashed else "solid")
        ty = y + pad * 0.8
        cv.text(x + pad, ty, "\n".join(self.lines), size=self.size, color=th.deep)
        bx = x + self.w - pad
        for b in reversed(self.badges):
            bwid = badge_w(b)
            bx -= bwid
            draw_badge(cv, bx, ty - 1, b)
            bx -= 6
        if self.sub_lines:
            cv.text(x + pad, ty + self.head_h + 3, "\n".join(self.sub_lines), size=self.sub_size, color=MUTED)
        cv.register(f"cchip:{self.label}", x, y, self.w, H)
        return self


def lane_bar(cv: Canvas, x, y, w, h, text, tone, *, size=15, dash="solid", badge=None, fill="hachure"):
    """Coverage bar for the 'layers' lanes: hatch-filled rounded rect with wrapped text and optional badge."""
    th = get_theme(tone)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style=fill, sw=2, dash=dash)
    bwid = badge_w(badge) if badge else 0
    avail = w - 24 - (bwid + 10 if badge else 0)
    lines = metrics.wrap_text(text, avail * 0.97, size)
    th_h = len(lines) * size * LH
    cv.text(x + 12, y + (h - th_h) / 2, "\n".join(lines), size=size, color=INK)
    if badge:
        draw_badge(cv, x + w - bwid - 10, y + (h - 24) / 2, badge)


def dotted_rect(cv: Canvas, x, y, w, h, tone="pink", dash="dotted", sw=2):
    th = get_theme(tone)
    return cv.rect(x, y, w, h, stroke=th.stroke, fill="transparent", sw=sw, dash=dash)


def swatch_legend(cv: Canvas, x, y, w, title, entries, size=14) -> float:
    """Vertical colour key inside a dotted panel; returns bottom y."""
    cy = y + 14
    t = cv.text(x + 14, cy, title, size=16, color=INK)
    cy = t.bottom + 8
    for label, tone, dashed in entries:
        th = get_theme(tone)
        cv.rect(x + 14, cy + 2, 26, 17, stroke=th.stroke, fill=("transparent" if dashed else th.fill),
                style="solid" if dashed else "hachure", sw=2, dash="dashed" if dashed else "solid")
        lt = cv.text(x + 50, cy, label, size=size, color=INK)
        cy += max(lt.h, 20) + 5
    h = cy - y + 8
    dotted_rect(cv, x, y, w, h, "gray")
    return y + h


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Guardrails and controls",
        f"Which safety check runs where - four intervention points, the risks scanned at each, who attaches the policy, and the Responsible AI wrapper ({AS_OF})",
        icon="content-safety", w=W)
    y = bottom + 40

    y = glance_strip(cv, y)
    y = hero(cv, y + 56)
    y = anatomy(cv, y + 56)
    y = catalogue(cv, y + 56)
    y = deep_dives(cv, y + 56)
    y = consume(cv, y + 56)
    # <<NEXT-SECTIONS>>


# ====================================================================== 0. glance strip
def glance_strip(cv: Canvas, y: float) -> float:
    tiles = [
        Box(556, "4 intervention points", sub="User input · Tool call (preview) · Tool response (preview) · Output",
            theme="pink", size=27, sub_size=15, h=132, fill="hatch"),
        Box(556, "Risk + point + action", sub="A control = one risk, where to scan and what to do. A guardrail = a named collection of controls (REST: RAI policy)",
            theme="pink", size=27, sub_size=15, h=132, fill="hatch"),
        Box(556, "Agent beats model", sub="An agent's guardrail fully overrides its model deployment's guardrail; with none assigned it inherits the model's",
            theme="green", size=27, sub_size=15, h=132, fill="hatch"),
        Box(556, "Microsoft.DefaultV2", sub="Default for models: core harms at Medium, user prompt attacks on, document attacks off. Can't be edited",
            theme="blue", size=27, sub_size=15, h=132, fill="hatch"),
        Box(556, "~50-100 ms", sub="added per intervention point; varies with content length and the number of controls",
            theme="gray", size=27, sub_size=15, h=132, fill="hatch"),
        Box(556, "Agent guardrails: preview", sub=f"Tool call and tool response points, PII, task adherence, spotlighting and groundedness are preview ({AS_OF})",
            theme="orange", size=27, sub_size=15, h=132, fill="hatch"),
    ]
    _, b = row(cv, 0, y, tiles, gap=32.8)
    return b


# ====================================================================== 1. hero
def hero(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "1  Where each check runs", sub="One request path, four intervention points (gates), the controls that can run at each, and the layers that can attach a guardrail",
                   size=32, w=W)
    y += 88

    X0, AW, GW, GP = 45, 250, 340, 100
    seq = [("user", AW), ("g1", GW), ("agent", AW), ("g2", GW), ("tool", AW), ("g3", GW), ("mem", AW), ("g4", GW), ("out", AW)]
    cx: dict[str, float] = {}
    x = X0
    for k, wd in seq:
        cx[k] = x
        x += wd + GP

    # ---------------------------------------------------------------- layers band
    lane_h, lane_gap = 62, 10
    with cv.panel(0, y, w=W, title="Layers that can attach a policy", theme="pink", style="dotted", pad=24, title_size=24,
                  sub="Bars show which intervention points each layer covers (documented scope only); colour = what the policy is attached to",
                  sub_size=15) as lp:
        ly = lp.iy
        lanes = [
            ("Control Plane Azure Policy", "minimum compliance", "grape"),
            ("Model deployment guardrail", "Microsoft.DefaultV2 by default", "blue"),
            ("Agent guardrail", "fully overrides the model's", "green"),
            ("Hosted-agent boundary", "rai_config on the agent", "green"),
            ("Toolbox version", "policies.rai_config", "orange"),
            ("Network egress controls", "hosted agents only", "indigo"),
        ]
        for i, (name, sub, tone) in enumerate(lanes):
            Box(AW, name, sub=sub, theme=tone, size=15, sub_size=13, h=lane_h, fill="soft", pad=6).place(cv, X0, ly + i * (lane_h + lane_gap))
        g1x, g4r = cx["g1"], cx["g4"] + GW
        r0 = ly
        lane_bar(cv, g1x, r0, cx["out"] + AW - g1x, lane_h,
                 "Mandates the minimum controls a model deployment needs to be compliant (content safety, prompt injection, protected materials) - "
                 "subscription or resource-group scope, with exceptions - evaluated by Azure Policy", "grape", dash="dashed")
        r1 = ly + (lane_h + lane_gap)
        lane_bar(cv, cx["g1"], r1, GW, lane_h, "scans the prompt (user input)", "blue")
        lane_bar(cv, cx["g4"], r1, GW, lane_h, "scans the completion (output)", "blue")
        t = txt(cv, cx["g1"] + GW + 24, r1 + 12, "Models have two intervention points only: user input and output. A request-time x-policy-id header can pick another guardrail for one call.",
                size=14, color=MUTED, wrap=cx["g4"] - cx["g1"] - GW - 48, align="left")
        r2 = ly + 2 * (lane_h + lane_gap)
        lane_bar(cv, g1x, r2, g4r - g1x, lane_h,
                 "The guardrail assigned to the agent decides what is scanned at all four points and fully overrides its model's guardrail "
                 "(no custom guardrail assigned: it inherits its model deployment's)", "green", badge="preview")
        r3 = ly + 3 * (lane_h + lane_gap)
        lane_bar(cv, g1x, r3, g4r - g1x, lane_h,
                 "Platform screens at the hosted-agent boundary, independent of any model deployment policy: blocked input returns "
                 "HTTP 400 content_filter before the agent runs; no rai_config = no guardrail", "green", badge="preview", fill="cross")
        r4 = ly + 4 * (lane_h + lane_gap)
        lane_bar(cv, cx["tool"] - 40, r4, AW + 80, lane_h, "filters tool inputs and outputs at the toolbox layer", "orange")
        r5 = ly + 5 * (lane_h + lane_gap)
        lane_bar(cv, cx["agent"], r5, cx["tool"] + AW - cx["agent"], lane_h,
                 "hosted agent outbound calls: ordered host rules (allow, deny, transform, rewrite); Audit, then Enforce", "indigo", badge="preview")
        txt(cv, cx["tool"] + AW + 24, r5 + 8, "Egress rules govern outbound connections, not content: they are not an intervention point.",
            size=14, color=MUTED, wrap=GW * 2 + 40)
        txt(cv, cx["tool"] + AW + 60, r4 + 8, "Toolbox docs word it as 'tool inputs and outputs' and do not map it to gates 2 and 3.",
            size=14, color=MUTED, wrap=GW * 2)
    y = lp.bottom + 44

    # ---------------------------------------------------------------- pipeline nodes
    nh = 130
    n_user = Box(AW, "USER", sub="sends a prompt (and documents)", theme="gray", icon="user", size=19, sub_size=14, h=nh).place(cv, cx["user"], y)
    n_g1 = Box(GW, "GATE 1: USER INPUT", sub="models + agents", theme="pink", icon="content-safety", size=19, sub_size=14, h=nh).place(cv, cx["g1"], y)
    n_agent = Box(AW, "MODEL / AGENT", sub="Responses API", theme="green", icon="agent", size=19, sub_size=14, h=nh).place(cv, cx["agent"], y)
    n_g2 = Box(GW, "GATE 2: TOOL CALL", sub="agents only", theme="pink", icon="content-safety", size=19, sub_size=14, h=nh).place(cv, cx["g2"], y)
    n_tool = Box(AW, "TOOL", sub="must support moderation", theme="orange", icon="toolbox", size=19, sub_size=14, h=nh).place(cv, cx["tool"], y)
    n_g3 = Box(GW, "GATE 3: TOOL RESPONSE", sub="agents only", theme="pink", icon="content-safety", size=19, sub_size=14, h=nh).place(cv, cx["g3"], y)
    n_mem = Box(AW, "AGENT MEMORY / CONTEXT", sub="what the agent keeps", theme="teal", icon="files", size=19, sub_size=14, h=nh).place(cv, cx["mem"], y)
    n_g4 = Box(GW, "GATE 4: OUTPUT", sub="models + agents", theme="pink", icon="content-safety", size=19, sub_size=14, h=nh).place(cv, cx["g4"], y)
    n_out = Box(AW, "USER", sub="receives the answer", theme="gray", icon="user", size=19, sub_size=14, h=nh).place(cv, cx["out"], y)
    for n, gx in ((1, cx["g1"]), (2, cx["g2"]), (3, cx["g3"]), (4, cx["g4"])):
        numbered(cv, gx + 24, y + 24, n, theme="pink", d=32, size=18)
    for gx in (cx["g2"], cx["g3"]):
        draw_badge(cv, gx + GW - badge_w("preview") - 10, y + 10, "preview")
    chain = [(n_user, n_g1, "prompt"), (n_g1, n_agent, "allowed"), (n_agent, n_g2, "proposed call"), (n_g2, n_tool, "allowed"),
             (n_tool, n_g3, "payload"), (n_g3, n_mem, "allowed"), (n_mem, n_g4, "completion"), (n_g4, n_out, "answer")]
    for a, b, lab in chain:
        connect(cv, a, b, label=lab, label_size=14, label_wrap=84, color=INK, sw=2.5)
    y += nh + 30

    # ---------------------------------------------------------------- stacks under the gates
    GP_PAD, CW = 14, GW - 28
    stacks = {
        "g1": dict(
            scan="Scans the prompt, plus documents embedded in it.",
            chips=[
                CChip(CW, "Hate · Sexual · Self-harm · Violence", theme=FAM["harm"], sub="DefaultV2 blocking level: Medium"),
                CChip(CW, "User prompt attack", theme=FAM["attack"], sub="Prompt Shields - on by default"),
                CChip(CW, "Document attack", theme=FAM["attack"], sub="Prompt Shields - off by default"),
                CChip(CW, "Spotlighting", theme=FAM["attack"], sub="tags documents as lower trust", badges=["preview", "models only"]),
                CChip(CW, "Blocklists (prompt)", theme=FAM["custom"], sub="Azure OpenAI models"),
            ],
            blocked="Input never reaches the model and the interaction halts. Hosted agent: HTTP 400 content_filter before the agent runs."),
        "g2": dict(
            scan="Scans the tool name, arguments and the data the agent proposes to send.",
            chips=[
                CChip(CW, "Hate · Sexual · Self-harm · Violence", theme=FAM["harm"], sub="docs example: Hate (High), annotate and block"),
                CChip(CW, "? Task adherence", theme=FAM["task"], sub="point not stated in the docs read; the API checks planned tool calls", badges=["preview"], dashed=True),
            ],
            blocked="The tool call is NOT executed; the agent stops until the next user input."),
        "g3": dict(
            scan="Scans the full tool payload before it enters agent memory or reaches the user.",
            chips=[
                CChip(CW, "Document attack", theme=FAM["attack"], sub="indirect prompt injection in tool output", badges=["preview"]),
                CChip(CW, "Hate · Sexual · Self-harm · Violence", theme=FAM["harm"], sub="implied by the override example; not listed explicitly", dashed=True),
            ],
            blocked="The agent stops and the payload is not saved to agent memory."),
        "g4": dict(
            scan="Scans the final completion returned to the user.",
            chips=[
                CChip(CW, "Hate · Sexual · Self-harm · Violence", theme=FAM["harm"], sub="DefaultV2 blocking level: Medium"),
                CChip(CW, "Protected material - text", theme=FAM["pm"], sub="English only"),
                CChip(CW, "Protected material - code", theme=FAM["pm"], sub="GitHub index current to 2023-04-06"),
                CChip(CW, "PII", theme=FAM["pii"], sub="completions; block removes the whole output", badges=["preview"]),
                CChip(CW, "Groundedness", theme=FAM["ground"], sub="models only; streaming; retires 2027-04-30", badges=["preview", "retiring"]),
                CChip(CW, "Blocklists (completion)", theme=FAM["custom"], sub="Azure OpenAI models"),
            ],
            blocked="Models: filtered completion (finish_reason content_filter). Hosted agent: HTTP 400, or HTTP 200 + terminal SSE error event when streamed."),
    }
    heights = {}
    for k, s in stacks.items():
        scan_l = metrics.wrap_text(s["scan"], CW * 0.97, 14)
        blk_l = metrics.wrap_text(s["blocked"], CW * 0.97, 14)
        s["scan_l"], s["blk_l"] = scan_l, blk_l
        heights[k] = (GP_PAD + len(scan_l) * 14 * LH + 8 + 18 + len(blk_l) * 14 * LH + 14 + sum(c.h + 8 for c in s["chips"]) + GP_PAD)
    SH = max(heights.values())
    for k, s in stacks.items():
        gx = cx[k]
        dotted_rect(cv, gx, y, GW, SH, "pink")
        cy = y + GP_PAD
        t = txt(cv, gx + GP_PAD, cy, "\n".join(s["scan_l"]), size=14, color=MUTED)
        cy = t.bottom + 8
        txt(cv, gx + GP_PAD, cy, "If blocked", size=14, color="#c92a2a")
        b = txt(cv, gx + GP_PAD, cy + 18, "\n".join(s["blk_l"]), size=14, color=INK)
        cy = b.bottom + 14
        for c in s["chips"]:
            c.place(cv, gx + GP_PAD, cy)
            cy += c.h + 8
        if k in ("g2", "g3"):
            txt(cv, gx + GP_PAD, cy + 6, "Only the controls named above appear in the docs for this point; there is no full per-point list (see the matrix in section 3).",
                size=13, color=MUTED, wrap=CW)

    # ---------------------------------------------------------------- notes under actor columns
    swatch_legend(cv, cx["user"], y, AW, "Chip colour = risk family", [
        ("Content harms", FAM["harm"], False), ("Prompt attacks", FAM["attack"], False), ("Protected material", FAM["pm"], False),
        ("PII", FAM["pii"], False), ("Groundedness", FAM["ground"], False), ("Task adherence", FAM["task"], False),
        ("Custom (blocklists)", FAM["custom"], False), ("Dashed = implied / unknown", "gray", True)])
    n1 = Note(AW, "Models can Annotate or Annotate and block. Agents can only Annotate and block.", kind="info", title="Actions", size=14, title_size=16, pad=10)
    n1.place(cv, cx["user"], y + 290)
    n2 = Note(AW, "The agent's own guardrail decides; it fully overrides the model's.", kind="key", title="Which guardrail", size=14, title_size=16, pad=10)
    n2.place(cv, cx["agent"], y)
    n2b = Note(AW, "Tool call and tool response controls need agents built in Foundry Agent Service; other Control Plane agents are not covered.",
               kind="warn", title="Scope", size=14, title_size=16, pad=10)
    n2b.place(cv, cx["agent"], n2.bottom + 16)
    tools = Card(AW, "Supported tools", ["Azure AI Search", "Azure Functions", "OpenAPI", "SharePoint Grounding", "Fabric Data Agent", "Bing Grounding",
                                         "Bing Custom Search", "Browser Automation", "! Other tools: the control silently has no effect"],
                 theme="orange", icon="toolbox", title_size=17, body_size=14, pad=12, icon_size=26, gap=4,
                 src=[("Intervention points", learn("guardrails/intervention-points#supported-tools"))])
    tools.place(cv, cx["tool"], y)
    n3 = Note(AW, "A blocked tool response is not saved to agent memory, so injected content cannot steer later steps.", kind="tip",
              title="Memory stays clean", size=14, title_size=16, pad=10)
    n3.place(cv, cx["mem"], y)
    n4 = Note(AW, "Streaming: default buffers output before release; the async filter returns tokens first (section 5).", kind="info",
              title="Output timing", size=14, title_size=16, pad=10)
    n4.place(cv, cx["out"], y)
    n5 = Note(AW, "Each intervention point adds about 50-100 ms.", kind="info", title="Latency", size=14, title_size=16, pad=10)
    n5.place(cv, cx["out"], n4.bottom + 16)
    return y + SH + 20


def marks_legend(cv: Canvas, x: float, y: float, entries, size=14, gap=26) -> float:
    cx_ = x
    for mark, label in entries:
        draw_mark(cv, mark, cx_ + 10, y + 11, 18)
        t = cv.text(cx_ + 26, y + 1, label, size=size, color=INK)
        cx_ = t.right + gap
    return y + 24


# ====================================================================== 2. anatomy
def anatomy(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2  Anatomy of a guardrail: controls, actions and which guardrail wins",
                   sub="How a control is built, how an agent's guardrail relates to its model's, and what annotate and block mean", size=32, w=W)
    y += 88
    PW = 1140
    b1 = control_anatomy(cv, 0, y, PW)
    b2 = precedence(cv, PW + 40, y, PW)
    b3 = actions_levels(cv, 2 * (PW + 40), y, PW)
    return max(b1, b2, b3)


def control_anatomy(cv: Canvas, x: float, y: float, w: float) -> float:
    with cv.panel(x, y, w=w, title="A control = risk + intervention point(s) + action", theme="pink", style="dotted", pad=24, title_size=24,
                  sub="A guardrail is a named collection of controls (REST: an RAI policy)", sub_size=15) as p:
        ix, iy = p.ix, p.iy
        bw, gap, bh = 230, 40, 118
        parts = [("RISK", "what to detect: harm categories, prompt attacks, PII, protected material", "hatch"),
                 ("INTERVENTION POINT(S)", "where to scan: user input, tool call, tool response, output", "hatch"),
                 ("ACTION", "annotate, or annotate and block", "hatch"),
                 ("CONTROL", "one risk + its point(s) + one action", "solid")]
        for i, (lab, sub, fl) in enumerate(parts):
            Box(bw, lab, sub=sub, theme="pink", size=17, sub_size=13, h=bh, fill=fl).place(cv, ix + i * (bw + gap), iy)
        for i, g in enumerate(["+", "+", "="]):
            gx = ix + (i + 1) * bw + i * gap + (gap - metrics.line_width(g, 30)) / 2
            cv.text(gx, iy + bh / 2 - 20, g, size=30, color="#a61e4d")
        y2 = iy + bh + 40
        with cv.panel(ix, y2, w=730, title="Example guardrail (examples taken from the docs)", theme="pink", style="solid", fill="soft", pad=16,
                      title_size=19) as gp:
            Table([("Risk", 200), ("Intervention point(s)", 250), ("Action", 240)], [
                ["Hate (core harm)", "User input, Output", "Annotate and block - level Medium"],
                ["Document attack", "User input; Tool response (preview, agents)", "Annotate and block"],
                ["Protected material - text", "Output", "Annotate (docs example: annotate only)"],
            ], w=698, theme="pink", size=14, head_size=15).place(cv, gp.ix, gp.iy)
        tx = ix + 730 + 100
        t1 = Box(232, "Model deployments", sub="many per guardrail", theme="blue", icon="openai", size=17, sub_size=13, h=96, icon_pos="left", fill="hatch").place(cv, tx, y2 + 20)
        t2 = Box(232, "Agents", sub="many per guardrail", theme="green", icon="agent", size=17, sub_size=13, h=96, icon_pos="left", fill="hatch").place(cv, tx, y2 + 150)
        draw_badge(cv, tx + 232 - badge_w("preview"), y2 + 150 - 28, "preview")
        connect(cv, gp, t1, a_side="right", b_side="left", ta=0.28, tb=0.5, label="assign", label_size=14, route="elbow", color="#a61e4d", sw=2.5)
        connect(cv, gp, t2, a_side="right", b_side="left", ta=0.78, tb=0.5, route="elbow", color="#a61e4d", sw=2.5)
        n = Note(w - 48, "Applies to all Foundry Models sold by Azure except audio-transcription models, and to agents built in Foundry Agent Service only - "
                         "not to other agents registered in the Control Plane. Creating a guardrail needs a project, at least one model deployment and the "
                         "Foundry Account Owner (or Owner) role. REST name: Microsoft.CognitiveServices/accounts/<acct>/raiPolicies/<name>, "
                         "assigned to a deployment with raiPolicyName.", kind="info", title="Scope and prerequisites", size=14, title_size=16, pad=10,
                 src=[("Guardrails overview", learn("guardrails/guardrails-overview"))])
        n.place(cv, ix, gp.bottom + 28)
    return p.bottom


def precedence(cv: Canvas, x: float, y: float, w: float) -> float:
    with cv.panel(x, y, w=w, title="Which guardrail wins for an agent?", theme="green", style="dotted", pad=24, title_size=24,
                  sub="Agent guardrails are preview; the agent's guardrail is used, it is not merged with the model's", sub_size=15) as p:
        ix, iy = p.ix, p.iy
        d = Box(300, "Custom guardrail assigned to the agent?", shape="diamond", theme="green", size=15, h=176, fill="hatch").place(cv, ix, iy)
        yes = Box(330, "The agent uses ITS guardrail, which fully overrides the model's", theme="green", size=15, h=84, fill="solid").place(cv, ix + 400, iy - 6)
        no = Box(330, "The agent inherits its model deployment's guardrail", theme="blue", size=15, h=84, fill="solid").place(cv, ix + 400, iy + 100)
        connect(cv, d, yes, a_side="right", b_side="left", label="yes", label_size=15, route="elbow", sw=2.5)
        connect(cv, d, no, a_side="right", b_side="left", label="no", label_size=15, route="elbow", sw=2.5, ta=0.62)
        txt(cv, ix + 402, iy + 196, "Microsoft.DefaultV2 applies to an agent only if its model deployment uses it, or you assign it explicitly.",
            size=14, color=MUTED, wrap=330)
        n1 = Note(w - 48 - 760, "Controls for risks not supported on agents (Spotlighting, Groundedness) do not take effect for the agent, but still apply to models using the same guardrail.",
                  kind="warn", title="Not every control carries over", size=14, title_size=16, pad=10)
        n1.place(cv, ix + 760, iy - 6)
        ty = iy + 246
        t = Table([("Violence control", 230), "1 User input", "2 Tool call", "3 Tool response", "4 Output"], [
            ["Model deployment guardrail", "High", "n/a for models", "n/a for models", "High"],
            ["Agent guardrail (assigned)", "Low", "no control", "no control", "Low"],
            [("Effective for the agent", "green"), ("scanned at Low", "green"), ("not scanned for Violence", "green"),
             ("not scanned for Violence", "green"), ("scanned at Low", "green")],
        ], w=w - 48, theme="green", size=14, head_size=15, title="Worked example from the docs", title_size=19)
        t.place(cv, ix, ty)
        src_line(cv, ix, t.bottom + 8, [("Guardrails overview: inheritance and override", learn("guardrails/guardrails-overview#guardrail-inheritance-and-override"))])
        n2 = Note(w - 48, "Risks are detected in an agent based on the guardrail it is assigned, not its model's. If the agent's guardrail has no Violence control at tool call "
                          "or tool response, those points are not scanned for Violence - even though the model's own guardrail is stricter.",
                  kind="gotcha", title="Gotcha: a weaker agent guardrail relaxes the model's", size=14, title_size=16, pad=10)
        n2.place(cv, ix, t.bottom + 40)
    return p.bottom


def actions_levels(cv: Canvas, x: float, y: float, w: float) -> float:
    with cv.panel(x, y, w=w, title="Actions, blocking levels and severity", theme="pink", style="dotted", pad=24, title_size=24,
                  sub="What a control does when it fires, and how strict the four core harms are", sub_size=15) as p:
        ix, iy = p.ix, p.iy
        iw = w - 48
        t1 = Table([("Action", 200), ("Models", 90), ("Agents (preview)", 140), "What happens"], [
            [("Annotate", "pink"), CHECK, CROSS, "Detection or severity is returned in the annotations; content is not filtered (filtered: false)"],
            [("Annotate and block", "pink"), CHECK, CHECK, "Blocked input returns an error (HTTP 400 content_filter); blocked output can return a filtered completion"],
        ], w=iw, theme="pink", size=14, head_size=15, title="Actions", title_size=19)
        t1.place(cv, ix, iy)
        t2 = Table([("Blocking level", 190), ("Blocks (Hate, Sexual, Self-harm, Violence)", 380), "Who can use it"], [
            [("Off", "pink"), "Nothing blocked; annotations can still be returned", "Inputs: all customers. Outputs: approved customers only (modified guardrails)"],
            [("Low", "pink"), "High severity only (least restrictive)", "All customers"],
            [("Medium", "pink"), "Medium + High (DefaultV2 level)", "All customers"],
            [("High", "pink"), "Low + Medium + High (most restrictive)", "All customers"],
        ], w=iw, theme="pink", size=14, head_size=15, title="Blocking levels for the four core harms", title_size=19)
        t2.place(cv, ix, t1.bottom + 28)
        n1 = Note(iw, "Safe is always annotated, never filtered. The blocking level changes what is blocked, not how content is classified. "
                      "Guardrails use four levels: Safe, Low, Medium, High. Azure AI Content Safety text uses 0-7 (optionally trimmed to 0, 2, 4, 6); images use 0, 2, 4, 6. "
                      "Text classifiers are trained and tested on Chinese, English, French, German, Italian, Japanese, Portuguese and Spanish.",
                  kind="info", title="Severity", size=14, title_size=16, pad=10,
                  src=[("Default guardrail policies", learn("guardrails/default-safety-policies")),
                       ("Harm categories and severity", learn("openai/concepts/content-filter-severity-levels"))])
        n1.place(cv, ix, t2.bottom + 24)
        n2 = Note(iw, "The overview says all customers can turn content harms off for inputs and only approved customers for outputs; the Limited Access page says "
                      "modified-guardrails approval is needed to turn guardrails partially or fully off. Annotation-only on outputs for the four core harms also needs approval.",
                  kind="warn", title="Docs disagree: who can turn guardrails off", size=14, title_size=16, pad=10,
                  src=[("Limited access", learn("responsible-ai/openai/limited-access"))])
        n2.place(cv, ix, n1.bottom + 20)
    return p.bottom


# ====================================================================== 3. risk catalogue
def catalogue(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3  Risk catalogue: what applies to models and agents, and what the docs do not say",
                   sub=f"Risk applicability, a risk x intervention-point matrix limited to what the docs state, and the DefaultV2 settings ({AS_OF})", size=32, w=W)
    y += 88
    # ---- C1 risk applicability
    rows = [
        [("Hate · Sexual · Self-harm · Violence", FAM["harm"]), CHECK, CHECK, CHECK, "The four core harms; text and image; severity Safe, Low, Medium, High; DefaultV2 level Medium"],
        [("User prompt attacks (Prompt Shields)", FAM["attack"]), CHECK, CHECK, CHECK, "Formerly Jailbreak; scanned at user input only; on by default"],
        [("Indirect attacks (document attacks)", FAM["attack"]), CHECK, CHECK, CROSS, "Off by default; user input for models, plus tool response for agents' supported tools"],
        [("Spotlighting (preview)", FAM["attack"]), CHECK, CROSS, CROSS, "Chat Completions only; off by default; base-64 tags documents as lower trust"],
        [("Protected material - code", FAM["pm"]), CHECK, CHECK, CHECK, "GitHub index current to 2023-04-06; the quickstart is titled preview, the risk table does not label it"],
        [("Protected material - text", FAM["pm"]), CHECK, CHECK, CHECK, "English only; recipes, web content, news, lyrics"],
        [("Groundedness (preview, retires 2027-04-30)", FAM["ground"]), CHECK, CROSS, DASH, "Models only; English only; guardrail annotations only in streaming scenarios"],
        [("PII (preview)", FAM["pii"]), CHECK, CHECK, DASH, "Needs API 2025-01-01-preview or later; scans completions"],
        [("Task adherence (preview)", FAM["task"]), CHECK, CHECK, DASH, "Agentic tool-use alignment; the intervention point is not stated"],
        [("Network egress (preview)", "indigo"), CROSS, PARTIAL, DASH, "Hosted agents, plus prompt agents that use the Microsoft Copilot harness; not other prompt agents or models"],
    ]
    t1 = Table([("Risk", 330), ("Models", 90), ("Agents (preview)", 120), ("In DefaultV2", 120), "Notes"], rows, w=1330, theme="pink", size=14,
               head_size=15, title="Risk applicability", title_size=22)
    t1.place(cv, 0, y)
    ly = marks_legend(cv, 0, t1.bottom + 14, [(CHECK, "applies / enabled"), (CROSS, "does not apply / explicitly off"),
                                               (PARTIAL, "only some agent types"), (DASH, "not listed in DefaultV2 / not stated")], size=13)
    src_line(cv, 0, ly + 6, [("Guardrails overview: risk applicability", learn("guardrails/guardrails-overview#risk-applicability"))])
    n1 = Note(1330, "If a guardrail has controls for risks not supported on agents (Spotlighting, Groundedness), they do not take effect for the agent but still apply to models using it. "
                    "The guided set-up page says agents that call external tools get 'tool response validation and spotlighting', while the risk table marks Spotlighting as not applicable to agents.",
              kind="warn", title="Docs disagree: spotlighting for agents", size=14, title_size=16, pad=10)
    n1.place(cv, 0, ly + 44)
    # ---- C2 matrix
    mx = 1380
    t2 = Table([("Risk", 250), ("1 User input", 92), ("2 Tool call (preview)", 112), ("3 Tool response (preview)", 124), ("4 Output", 80), "Basis in the docs"], [
        [("Hate · Sexual · Self-harm · Violence", FAM["harm"]), CHECK, CHECK, PARTIAL, CHECK, "Defaults cover prompts and completions; gate 2 = docs example Hate (High); gate 3 only implied by the override example"],
        [("User prompt attack", FAM["attack"]), CHECK, CROSS, CROSS, CROSS, "Scannable only at user input"],
        [("Document attack", FAM["attack"]), CHECK, DASH, CHECK, DASH, "Models: user input. Agents: also tool response, supported tools (preview)"],
        [("Spotlighting (preview)", FAM["attack"]), PARTIAL, CROSS, CROSS, DASH, "Toggle on the document attack control; models, Chat Completions"],
        [("Protected material (text, code)", FAM["pm"]), DASH, DASH, DASH, CHECK, "Documented as scanning model output"],
        [("PII (preview)", FAM["pii"]), DASH, DASH, DASH, CHECK, "Documented as scanning completions"],
        [("Groundedness (preview)", FAM["ground"]), DASH, CROSS, CROSS, CHECK, "Models only; completion annotations, streaming"],
        [("Task adherence (preview)", FAM["task"]), DASH, DASH, DASH, DASH, "Point not stated; the API analyses planned tool calls"],
        [("Blocklists", FAM["custom"]), CHECK, DASH, DASH, CHECK, "RAI policy promptBlocklists and completionBlocklists; Azure OpenAI models"],
    ], w=1150, theme="pink", size=14, head_size=14, title="Risk x intervention point: only what the docs state", title_size=22)
    t2.place(cv, mx, y)
    ly2 = marks_legend(cv, mx, t2.bottom + 14, [(CHECK, "stated"), (PARTIAL, "implied or conditional"), (CROSS, "stated as not possible"),
                                                 (DASH, "not stated")], size=13)
    src_line(cv, mx, ly2 + 6, [("Intervention points", learn("guardrails/intervention-points")),
                               ("Configure guardrails", learn("guardrails/how-to-create-guardrails")),
                               ("Prompt Shields", learn("openai/concepts/content-filter-prompt-shields"))])
    n2 = Note(1150, "The docs publish no full risk x intervention-point matrix - only examples and the controls the wizard recommends. The portal wizard hides a point when "
                    "a risk cannot apply there (user prompt attacks: user input only). Task adherence's intervention point is not stated in the pages read.",
              kind="gotcha", title="Docs gap", size=14, title_size=16, pad=10)
    n2.place(cv, mx, ly2 + 76)
    # ---- C3 defaults
    dx = 2580
    t3 = Table([("Model type", 150), "Prompts", "Completions"], [
        [("Text models", "blue"), "Hate, Violence, Sexual, Self-harm at Medium; user prompt injection (jailbreak)",
         "The four harms at Medium; protected material text; protected material code"],
        [("Vision-enabled chat", "blue"), "The four harms at Medium; identification of individuals and inference of sensitive attributes; user prompt injection (jailbreak)",
         "The four harms at Medium"],
        [("Image generation", "blue"), "The four harms at Medium; deceptive generation of political candidates; depictions of public figures; "
                                       "protected material - art and studio characters; profanity; user prompt injection (jailbreak)",
         "The four harms at Medium; content credentials"],
        [("Audio models", "blue"), "The four harms at Medium; user prompt injection (jailbreak)",
         "The four harms at Medium; protected material text; protected material code"],
    ], w=920, theme="blue", size=14, head_size=15, title="Microsoft.DefaultV2 settings by model type", title_size=22)
    t3.place(cv, dx, y)
    n3 = Note(920, "Applies to all Foundry Models sold by Azure except audio-transcription models. Core-harm filters and user prompt attack detection are on by default; "
                   "document attack detection is off. DefaultV2 can't be edited - create a custom guardrail. Blocked input returns an error; blocked output can return a filtered completion.",
              kind="info", title="Defaults", size=14, title_size=16, pad=10,
              src=[("Default guardrail policies", learn("guardrails/default-safety-policies"))])
    n3.place(cv, dx, t3.bottom + 18)
    return max(n1.bottom, n2.bottom, n3.bottom)


# ====================================================================== 4. deep dives
C4 = [0, 885, 1770, 2655]       # 4-column grid, 845 wide
CW4 = 845


def deep_dives(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Risk deep dives: attacks, sensitive data, copyright, grounding, task alignment and custom controls",
                   sub=f"What each control detects, where it runs, its limits and its status ({AS_OF})", size=32, w=W)
    y += 88
    # ---------------------------------------------------------------- row 1: Prompt Shields | PII | Protected material
    ps = Table([("", 150), ("User prompt attacks", 440), ("Document attacks (indirect)", 480)], [
        [("Risk name", "red"), "User prompt attacks - formerly Jailbreak risk detection", "Indirect attacks, also called document attacks"],
        [("Hides in", "red"), "What the user types or sends", "Documents, emails or web pages the model reads"],
        [("Scanned at", "red"), "User input only", "User input for model calls; also tool response for supported agent tools (preview)"],
        [("Default", "red"), "On", "Off - enable it in the guardrail"],
        [("Classes", "red"), "Attempt to change system rules · Embedding a conversation mockup · Role-play · Encoding attacks",
         "Manipulated content · Allowing a compromised LLM to access system infrastructure · Information gathering · Availability · Fraud · Malware · plus the four user-prompt classes"],
        [("Annotation", "red"), "detected + filtered (key: jailbreak)", "detected + filtered"],
        [("REST 2024-10-01-preview", "red"), "prompt_shield.user_prompt {enabled, action: annotate | block}", "prompt_shield.documents {enabled, action, spotlighting_enabled}"],
        [("Standalone API", "red"), "Content Safety: analyze userPrompt", "Analyze up to 5 documents; returns attackDetected"],
    ], w=1090, theme="red", size=14, head_size=15, title="Prompt Shields: user prompt attacks vs document attacks", title_size=22)
    ps.place(cv, 0, y)
    ps_notes = Card(620, "Spotlighting (preview) and tips", [
        "Spotlighting tags documents as lower trust by base-64 encoding them; off by default",
        "No direct cost, but more tokens; large documents can exceed input limits; Chat Completions only",
        "Side effect: the model may mention that content was base-64 encoded",
        "Core-harm blocking levels don't change Prompt Shields sensitivity - configure and evaluate it separately",
        "Chat Completions: wrap documents in the <documents> delimiter and JSON-escape them",
        "Primarily trained and evaluated on English; it doesn't verify provenance or judge harm, accuracy or grounding",
    ], theme="red", body_size=14, title_size=19, badge="preview",
        src=[("Prompt Shields", learn("openai/concepts/content-filter-prompt-shields")),
             ("Document embedding in prompts", learn("guardrails/how-to-create-guardrails#document-embedding-in-prompts"))])
    ps_notes.place(cv, 1130, y)
    pii = Card(CW4, "PII detection (sensitive data leakage)", [
        "Scans LLM completions for personal data; configurable per category",
        "Modes: Annotate, or Annotate and block (blocks the entire output)",
        "Personal: email, phone, address, person, IP address, date of birth, driver's licence, passport",
        "Financial: card, bank account, SWIFT, IBAN. Government IDs: SSN, national IDs (50+ countries), tax IDs",
        "Azure secrets (connection strings, storage account keys, authentication keys) and geolocation",
        "Annotation fields: detected, filtered, redacted",
        "Needs API 2025-01-01-preview or later; guided set-up turns it on when you answer yes to sensitive data / PII",
    ], theme=FAM["pii"], badge="preview", icon="content-safety", body_size=14, title_size=19,
        src=[("PII filter", learn("openai/concepts/content-filter-personal-information"))])
    pii.place(cv, C4[2], y)
    pm = Card(CW4, "Protected material (text and code)", [
        "Scans model output, not prompts; English only",
        "Text: all four categories always apply - Recipes (40+ characters of anecdotes, creative names or descriptions), Web Content (webmd.com, over 200 characters), News (over 200 characters), Lyrics (over 11 words)",
        "Code: matches known GitHub repositories; the index is current only through 2023-04-06",
        "Code annotation returns an example citation URL and licence - display it; licence compliance may be needed for Customer Copyright Commitment coverage",
        "Code API: POST <endpoint>/contentsafety/text:detectProtectedMaterialForCode (2024-09-15-preview)",
        "The code quickstart is titled preview; the guardrails risk table does not label it",
    ], theme=FAM["pm"], icon="content-safety", body_size=14, title_size=19,
        src=[("Protected material", learn("openai/concepts/content-filter-protected-material")),
             ("Protected material for code", learn("azure/ai-services/content-safety/quickstart-protected-material-code", base=""))])
    pm.place(cv, C4[3], y)
    y1 = max(ps.bottom, ps_notes.bottom, pii.bottom, pm.bottom) + 40

    # ---------------------------------------------------------------- row 2: custom controls | groundedness | task adherence
    cc = Table([("Control", 250), ("What it does", 520), ("Key limits", 560), "Status"], [
        [("Blocklists in guardrails (Foundry)", "gray"),
         "Terms or regex patterns applied to prompts (promptBlocklists) and/or completions (completionBlocklists) of a guardrail. Build > Guardrails > Blocklists; add terms or upload a .csv. Azure OpenAI models only",
         "10,000 terms per list; pattern up to 1,000 characters; case-sensitive by default; new terms take about 5 minutes. Blocked prompt: HTTP 400; blocked completion: finish_reason content_filter",
         "No retirement notice in the pages read"],
        [("Content Safety blocklist API", "gray"),
         "Exact term matching: analyze with blocklistNames and haltOnBlocklistHit; create the list, then POST addOrUpdateBlocklistItems (2024-09-01)",
         "10,000 terms across all lists; 100 items per request; item up to 128 characters",
         "No retirement notice in the pages read; custom blocklist is not in GA API 2024-02-01 annotations"],
        [("Custom categories (standard), preview", "gray"),
         "Train an ML model on your samples (up to several hours), then analyze with analyzeCustomCategory; text only",
         "English only; 3 categories per user; 3 versions per category; 1 concurrent build; 5 inference ops/s; 50-5K positive samples, 10K total; sample file 128,000 bytes; text sample 125K characters; definition 1,000 characters",
         ("Retirement date 2026-09-01 has passed (page still says retiring). Migrate to the Custom text API in Foundry Custom text classification", "red")],
        [("Custom categories (rapid), preview", "gray"),
         "Create an incident and add samples; an LLM with embeddings matches emerging content - no training; text and image",
         "Incident name 100 characters; 1,000 samples per incident; text sample 500 characters; image 4 MB (BMP, GIF, JPEG, PNG, TIF, WEBP); 100 incidents per resource",
         ("Retires 2027-04-30. Evaluate blocklists (exact matching) or custom text classification", "red")],
    ], w=1730, theme="gray", size=14, head_size=15, title=f"Custom controls: blocklists and custom categories ({AS_OF})", title_size=22)
    cc.place(cv, 0, y1)
    ly = src_line(cv, 0, cc.bottom + 8, [("Use blocklists in Foundry models", learn("openai/how-to/use-blocklists")),
                                         ("Use a blocklist (Content Safety)", learn("azure/ai-services/content-safety/how-to/use-blocklist", base="")),
                                         ("Custom categories", learn("azure/ai-services/content-safety/concepts/custom-categories", base=""))])
    gr = Card(CW4, "Groundedness detection", [
        "Retires 2027-04-30 in Azure AI Content Safety and Azure OpenAI; update affected workloads before then",
        "Docs name two alternatives: Foundry evaluation tooling, or your own grounding validation with an LLM or system prompt",
        "Flags LLM output not supported by your grounding sources (RAG); needs documents embedded and formatted in the prompt",
        "Modes: non-reasoning (fast, binary) or reasoning (explanations); domain Medical or Generic; task Summarization or QnA",
        "Optional correction (preview); English only",
        "Guardrail annotations only in streaming scenarios (API 2024-10-01-preview, 2025-01-01-preview)",
        "Models only - the control has no effect for agents",
    ], theme=FAM["ground"], badge="retiring", subtitle="preview feature", icon="content-safety", body_size=14, title_size=19,
        src=[("Groundedness detection", learn("openai/concepts/content-filter-groundedness"))])
    gr.place(cv, C4[2], y1)
    ta = Card(CW4, "Task adherence", [
        "Flags agent tool calls that don't match the user's intent - e.g. the user asks to view a leave balance and the agent plans apply_leave()",
        "Docs suggest blocking the tool call or escalating to human-in-the-loop review",
        "Applies to models and agents (risk table); the intervention point of the guardrail control is not stated in the pages read",
        "Standalone API: POST <endpoint>/contentsafety/agent:analyzeTaskAdherence?api-version=2024-12-15-preview",
        "Body: tools[] (function name + description) and messages[]; response: taskRiskDetected + details",
        "Up to 100,000 characters; tested on English; data may be processed in other US or EU regions outside the geo",
        "Portal: Guardrails + controls > Try it out > Agentic Workflow > Task Adherence",
    ], theme=FAM["task"], badge="preview", icon="content-safety", body_size=14, title_size=19,
        src=[("Task adherence", learn("guardrails/task-adherence"))])
    ta.place(cv, C4[3], y1)
    y2 = max(ly, gr.bottom, ta.bottom)
    return y2


# ====================================================================== 5. streaming, what the app sees, setup
def consume(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Streaming, what your app sees, and how to configure",
                   sub="Synchronous vs asynchronous filtering, the errors and annotations a client receives, and every way to attach a guardrail", size=32, w=W)
    y += 88
    st = Table([("", 150), ("Default (synchronous)", 560), ("Asynchronous Filter", 600)], [
        [("Status", "pink"), "GA", "GA"],
        [("Behaviour", "pink"), "Content is buffered and evaluated before it is returned, so it arrives in chunks", "Tokens are returned immediately; filters run asynchronously"],
        [("Signal", "pink"), "Immediate filtering signal", "Delayed; guaranteed within about 1,000 characters of the violating content"],
        [("Configure", "pink"), "On by default", "Streaming = Asynchronous Filter in the content-filter configuration (needs permission to modify content filters); API 2024-02-01 or later"],
        [("Watch out", "pink"), "The last 15-30 words may be returned before the policy is applied (test: blocklist on gpt-4o; blocked when stream was false)",
         "Retroactively flagged protected material is not eligible for the Customer Copyright Commitment"],
        [("Annotations", "pink"), "Standard annotation messages", "Annotation messages carry content_filter_offsets {check_offset, start_offset, end_offset}"],
        [("Billing", "pink"), "When a filter triggers: HTTP 400 (prompt filtered) is charged for the prompt; HTTP 200 with finish_reason content_filter is charged for prompt and completion tokens",
         "Same charging rules as default streaming"],
        [("Hosted agents", "pink"), "Default (synchronous prevention): output is held until approved",
         "Asynchronous filter (deferred detection): output streams, and the stream stops with a moderation signal if a violation is found later"],
    ], w=1730, theme="pink", size=14, head_size=15, title="Content streaming: default vs asynchronous filter", title_size=22)
    st.place(cv, 0, y)
    src_line(cv, 0, st.bottom + 8, [("Content streaming", learn("openai/concepts/content-streaming")),
                                    ("Hosted agent content safety overview", learn("agents/concepts/hosted-agent-guardrails#output-streaming-behavior"))])
    app = Table([("Where", 200), ("Blocked input", 400), ("Blocked output", 520), "Annotations"], [
        [("Chat Completions", "pink"), "HTTP 400 content_filter", "Filtered completion; finish_reason content_filter", "prompt_filter_results + content_filter_results"],
        [("Responses API", "pink"), "HTTP 400 content_filter", "Not stated in the pages read", "Top-level content_filters array: blocked, source_type (prompt or completion), content_filter_results"],
        [("Hosted agent", "pink"), "HTTP 400 content_filter before the agent runs (a streamed Responses request emits no events)",
         "Non-streaming or buffered: HTTP 400 naming the output stage. Streamed: HTTP 200 + terminal SSE error event, code content_filter", "Not stated"],
        [("Blocklist", "pink"), "HTTP 400 with custom_blocklists in the inner error", "HTTP 200 with finish_reason content_filter", "custom_blocklists: id, filtered"],
        [("Partner integration", "pink"), "HTTP 400 content_filter; innererror ResponsibleAIPolicyViolation", "Not stated", "content_filter_result.external_safety_provider: provider_name, detected, filtered"],
    ], w=1730, theme="pink", size=14, head_size=15, title="What your app sees when a control fires", title_size=22)
    app.place(cv, 1770, y)
    src_line(cv, 1770, app.bottom + 8, [("Handle guardrails in the Responses API", learn("openai/how-to/responses#handle-guardrails-and-content-filtering")),
                                        ("Third-party integrations", learn("guardrails/third-party-integrations"))])
    y1 = max(st.bottom, app.bottom) + 70
    setup = Table([("Path", 190), ("Where and how", 640), "Notes"], [
        [("Portal wizard", "pink"), "Build > Guardrails > Create guardrail: 1 add controls (risk, intervention points, one action), 2 assign agents and models, 3 review and name",
         "Takes effect immediately on assignment; test in the playground with a non-production model or agent"],
        [("Guided guardrail (preview)", "pink"), "Agent playground > Guardrails > Manage guardrail > Guided guardrails setup", "Answers become recommended controls per intervention point (section 6)"],
        [("REST", "pink"), "A guardrail is an RAI policy: Microsoft.CognitiveServices/accounts/<acct>/raiPolicies/<name>; assign it with raiPolicyName on the deployment",
         "RAI Policies and Deployments create-or-update operations"],
        [("Per request", "pink"), "x-policy-id header names a guardrail for one call and overrides the deployment-level guardrail", "Not for chat with image input (default guardrail is used); unknown name gives InvalidContentFilterPolicy"],
        [("Hosted agent", "pink"), "rai_config.rai_policy_name = full ARM resource ID of the policy; azd: a policies list in azure.yaml (mapped to rai_config); azure-ai-projects 2.2.0 or later", "Section 6"],
        [("Toolbox version", "pink"), "policies.rai_config.rai_policy_name on the toolbox version", "Section 6"],
        [("Control Plane", "pink"), "Operate > Compliance > Create policy (Azure Policy)", "Section 7"],
    ], w=1730, theme="pink", size=14, head_size=15, title="Every way to attach a guardrail", title_size=22)
    setup.place(cv, 0, y1)
    src_line(cv, 0, setup.bottom + 8, [("Configure guardrails and controls", learn("guardrails/how-to-create-guardrails"))])
    an = Card(CW4, "Annotations and API versions", [
        "Standard annotations: risk category, severity (safe, low, medium, high), filtered",
        "Optional: user prompt attack, indirect attack, protected material text, protected material code (+ citation URL and licence), PII (detected, filtered, redacted), groundedness (+ offsets)",
        "API availability: indirect attack 2024-04-01-preview or later; PII and groundedness 2025-01-01-preview or later; GA 2024-02-01 recommended for production",
        "Annotation-only on outputs for the four core harms needs modified-guardrails approval; prompt and document attack toggles do not",
        "Showing generated code? Also show the citation from the annotation",
    ], theme="pink", icon="content-safety", body_size=14, title_size=19,
        src=[("Work with annotations", learn("guardrails/how-to-create-guardrails#work-with-annotations"))])
    an.place(cv, C4[2], y1)
    ed = Card(CW4, "Editing and testing rules", [
        "Core-harm controls on user input and output can't be deleted, only overridden",
        "Microsoft Default guardrails such as Default.V2 can't be edited - create a custom guardrail",
        "To delete a guardrail, first reassign or remove its models and agents",
        "'Try in playground' needs the guardrail assigned: assigning changes behaviour immediately, so use a non-production model or agent",
        "Document embedding: guardrails perform better when the prompt separates system, user and assistant roles",
    ], theme="pink", icon="content-safety", body_size=14, title_size=19,
        src=[("Configure guardrails and controls", learn("guardrails/how-to-create-guardrails#edit-controls-in-a-guardrail"))])
    ed.place(cv, C4[3], y1)
    return max(setup.bottom + 30, an.bottom, ed.bottom)
