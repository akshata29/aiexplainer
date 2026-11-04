"""Workflows, routines, A2A and multi-agent orchestration (part 1): the map of every way Foundry coordinates more than one agent,
declarative workflows (Preview, retiring 2026-12-01) with their migration paths, and the Microsoft Agent Framework orchestration patterns
exactly as the Agent Framework docs describe them.

Part 2 ('workflows-multi-agent-part-2') goes deep on the A2A tool, incoming A2A and A2A authentication, Responses API multi-agent
orchestration (Preview), routines (Preview), Microsoft Foundry Canvas and the doc conflicts.
Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="workflows-multi-agent", title="Workflows, routines, A2A and multi-agent orchestration", section="2", group="Agent Service", order=13,
    description="The orchestration map: declarative workflows (retiring 2026-12-01) and where they go, the five Microsoft Agent Framework "
                "patterns drawn as topologies, A2A, Responses multi-agent and routines side by side, plus human-in-the-loop.",
    tags=["workflows", "multi-agent", "agent-framework", "orchestration", "a2a", "routines"],
)

W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    workflow=("Build a workflow in Microsoft Foundry (retiring)", learn("agents/concepts/workflow")),
    lowcode=("Use and migrate declarative workflows (VS Code)", learn("how-to/develop/vs-code-agents-workflow-low-code")),
    procode=("Create hosted agents (VS Code, workflow sample)", learn("how-to/develop/vs-code-agents-workflow-pro-code")),
    fwhost=("Host agents built with frameworks", learn("how-to/develop/framework-hosted-agents")),
    maf=("Agent Framework: workflow orchestrations", learn("agent-framework/workflows/orchestrations", base="")),
    seq=("Agent Framework: sequential orchestration", learn("agent-framework/workflows/orchestrations/sequential", base="")),
    conc=("Agent Framework: concurrent orchestration", learn("agent-framework/workflows/orchestrations/concurrent", base="")),
    hand=("Agent Framework: handoff orchestration", learn("agent-framework/workflows/orchestrations/handoff", base="")),
    group=("Agent Framework: group chat orchestration", learn("agent-framework/workflows/orchestrations/group-chat", base="")),
    mag=("Agent Framework: Magentic orchestration", learn("agent-framework/workflows/orchestrations/magentic", base="")),
    hitl=("Agent Framework: human-in-the-loop", learn("agent-framework/workflows/human-in-the-loop", base="")),
    decl=("Agent Framework: declarative workflows", learn("agent-framework/workflows/declarative", base="")),
    mafhost=("Agent Framework: Foundry hosted agent", learn("agent-framework/hosting/foundry-hosted-agent", base="")),
    logic=("Automate Foundry agents with workflows in Azure Logic Apps", learn("azure/logic-apps/automate-foundry-agents-with-workflows", base="")),
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    a2atool=("Connect to an A2A agent endpoint", learn("agents/how-to/tools/agent-to-agent")),
    a2aauth=("Agent2Agent (A2A) authentication", learn("agents/concepts/agent-to-agent-authentication")),
    a2ain=("Enable an incoming A2A endpoint", learn("agents/how-to/enable-agent-to-agent-endpoint")),
    multi=("Multi-agent orchestration with the Responses API", learn("openai/how-to/responses-multi-agent")),
    routines=("Routines in Foundry Agent Service", learn("agents/concepts/routines")),
    useroutines=("Automate agents with routines", learn("agents/how-to/use-routines")),
    canvas=("Microsoft Foundry Canvas", learn("agents/concepts/foundry-agent-canvas")),
    overview=("Agent Service overview", learn("agents/overview")),
)


def src(*keys: str) -> list:
    return [U[k] for k in keys]


def card(w, title, body, theme="green", **kw) -> Card:
    """Dense-column card: one type scale for the whole canvas."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("sub_size", 13)
    kw.setdefault("pad", 14)
    kw.setdefault("gap", 4)
    kw.setdefault("icon_size", 30)
    return Card(w, title, body, theme=theme, **kw)


class Tile(Rect2):
    """Big-number summary tile: headline + one caption."""

    def __init__(self, w, big, cap, theme="green", big_size=34, cap_size=15, pad=14):
        self.th = THEMES[theme]
        self.w, self.big_size, self.cap_size, self.pad = w, big_size, cap_size, pad
        inner = (w - 2 * pad) * 0.965
        self.big_lines = wrap_text(big, inner, big_size)
        self.cap_lines = wrap_text(cap, inner, cap_size)
        lr = metrics.line_ratio()
        self.h = pad * 2 + len(self.big_lines) * big_size * lr + 8 + len(self.cap_lines) * cap_size * lr
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            ty = y + self.pad
            inner = self.w - 2 * self.pad
            cv.text(x + self.pad, ty, "\n".join(self.big_lines), size=self.big_size, color=th.deep, align="center", w=inner)
            ty += len(self.big_lines) * self.big_size * lr + 8
            cv.text(x + self.pad, ty, "\n".join(self.cap_lines), size=self.cap_size, color=INK, align="center", w=inner)
        cv.register("tile", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class Steps(Rect2):
    """Numbered walk-through card: the circles match the numbered arrows of the diagram next to it."""

    def __init__(self, w, title, steps, theme="yellow", num_theme="blue", size=14, pad=14, src=(), title_size=19):
        self.th = THEMES[theme]
        self.w, self.title, self.steps, self.num_theme, self.size, self.pad, self.title_size = w, title, steps, num_theme, size, pad, title_size
        self.tw = (w - 2 * pad - 38) * 0.965
        lr = metrics.line_ratio()
        self.lines = [wrap_text(t, self.tw, size) for t in steps]
        self.row_h = [max(len(ln) * size * lr, 26) + 9 for ln in self.lines]
        self.src = list(src)
        h = pad + title_size * lr + 8 + sum(self.row_h) + 4
        self.src_lines = []
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * lr + 2
        self.h = h + pad - (2 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=th.deep)
            cy = y + self.pad + self.title_size * lr + 8
            for i, (ln, rh) in enumerate(zip(self.lines, self.row_h)):
                numbered(cv, x + self.pad + 13, cy + 13, i + 1, theme=self.num_theme, d=26, size=15)
                cv.text(x + self.pad + 38, cy + 4, "\n".join(ln), size=self.size, color=INK)
                cy += rh
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("steps", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def label(cv, x, y, text, theme="green", size=22) -> float:
    t = cv.text(x, y, text, size=size, color=THEMES[theme].deep)
    return t.bottom + 12


def badge_on(cv, blk, kind, dx=-10, dy=-12):
    """Status pill straddling the top-right corner of a placed block."""
    _, lab = STATUS_LABELS.get(kind, ("gray", kind))
    bw = metrics.line_width(lab, 13) + 18
    draw_badge(cv, blk.right - bw + dx + 10, blk.y + dy, kind)


STATUS_LABELS = {"ga": ("green", "GA"), "preview": ("orange", "Preview"), "retiring": ("red", "Retiring"), "new": ("violet", "New"),
                 "classic": ("gray", "Classic")}


# ================================================================================================ band 0: banner + tiles
def band_banner(cv: Canvas, y: float) -> float:
    th = THEMES["red"]
    H = 200
    cv.rect(0, y, W, H, stroke=th.stroke, fill=th.soft, style="solid", sw=3)
    draw_badge(cv, 28, y + 26, "retiring")
    cv.text(130, y + 18, "Declarative Workflows retire on 2026-12-01", size=34, color=th.deep)
    cv.text(30, y + 80, "The visual workflow designer and in-portal workflow execution are no longer supported after that date. Foundry keeps running "
                        "YAML-based workflow definitions that you deploy as a hosted agent - workflows are no longer a separate agent type. "
                        "For new orchestration work the docs say: use Microsoft Agent Framework.", size=17, wrap=1680)
    cv.text(30, y + H - 34, "Learn: Build a workflow in Microsoft Foundry (the page is still titled Preview)", size=12, color=LINK, link=U["workflow"][1])
    # mini timeline
    x0, x1 = 1960, W - 50
    ly = y + 70
    cv.poly([(x0, ly), (x1, ly)], kind="arrow", stroke=INK, sw=3, end_head="arrow")
    ev = [("2026-11-03", "Today: workflows still run in the portal (Preview)", "gray"),
          ("2026-12-01", "Retirement: designer and in-portal execution unsupported", "red"),
          ("After 2026-12-01", "YAML workflow definitions deployed as a hosted agent keep running", "green")]
    seg = (x1 - x0 - 20) / 3
    for i, (when, detail, tn) in enumerate(ev):
        cx = x0 + seg * (i + 0.5)
        t2 = THEMES[tn]
        cv.ellipse(cx - 11, ly - 11, 22, 22, stroke=t2.stroke, fill=t2.fill, style="solid", sw=2, rough=0)
        cv.text(cx - seg / 2 + 10, ly + 24, when, size=19, color=t2.deep, align="center", w=seg - 20)
        cv.text(cx - seg / 2 + 10, ly + 52, detail, size=15, align="center", w=seg - 20, wrap=seg - 24)
    cv.register("banner", 0, y, W, H)
    return y + H


def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "Migrate, do not build", "Do not start new work on Foundry workflows (Preview). Move to Agent Framework, Azure Logic Apps or direct A2A.", "red"),
        Tile(C, "5 code-first patterns", "Microsoft Agent Framework: Sequential, Concurrent, Handoff, Group Chat, Magentic - deployed as a hosted agent.", "green"),
        Tile(C, "A2A tool: 1.0 GA", "The a2a tool is GA (a2a_preview = 0.3, preview). Incoming A2A on a Foundry agent is preview and defaults to v0.3.", "pink"),
        Tile(C, "GPT-5.6 only", "Responses API multi-agent (Preview): the model spawns subagents in parallel inside ONE request; 3 concurrent by default.", "blue"),
        Tile(C, "1 trigger + 1 action", "Routines (Preview): timer, cron schedule (min 5 min), GitHub issue or Teams message -> invoke one agent.", "violet"),
        Tile(C, "Humans stay in the loop", "Tool approval, request info, plan review, ask-the-user nodes, and your own approval of client-run function calls.", "yellow"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: the five lanes
LX = 560  # left edge of the diagram area inside a lane
CA = (560, 340)    # lane column A: x, w   (source)
CB = (990, 940)    # column B (middle panel)
CCOL = (2190, 560)  # column C (options)
CD = (2920, 610)   # column D (result)


def lane_frame(cv, y, h, n, title, sub, theme, badge=None, src_=()):
    th = THEMES[theme]
    cv.rect(0, y, W, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    numbered(cv, 44, y + 44, n, theme=theme, d=44, size=24)
    t = cv.text(84, y + 20, title, size=25, color=th.deep, wrap=410)
    s = cv.text(86, t.bottom + 6, sub, size=15, color="#495057", wrap=410)
    by = s.bottom + 12
    if badge:
        draw_badge(cv, 86, by, badge)
        by += 34
    for lab, url in src_:
        cv.text(86, by, f"Learn: {lab}", size=12, color=LINK, link=url, wrap=410)
        by += 17
    cv.line((520, y + 18), (520, y + h - 18), stroke=th.stroke, sw=1.5, dash="dotted", opacity=60)


def lane_workflows(cv, y):
    H = 268
    lane_frame(cv, y, H, 1, "Visual and declarative: Workflows", "Predefined sequences of agents and logic in a visual builder, stored as YAML", "red",
               badge="retiring", src_=[src("workflow")[0]])
    cy = y + H / 2
    des = Box(CA[1], "Workflow designer", sub="Foundry portal, YAML view, Power Fx", icon="workflow", icon_pos="left", theme="red", h=112, size=20,
              sub_size=14, fill="hatch")
    des.place(cv, CA[0], cy - 56)
    with cv.panel(CB[0], y + 26, title="Designer palette", theme="red", style="dotted", pad=18, title_size=20, min_w=CB[1], min_h=H - 52) as pal:
        cv.text(pal.ix, pal.iy + 2, "Node types", size=15, color=MUTED)
        n1 = ChipFlow(["Agent", "Logic", "Data transformation", "Basic chat"], w=CB[1] - 40, theme="red", size=16)
        n1.place(cv, pal.ix, pal.iy + 26)
        cv.text(pal.ix, n1.bottom + 14, "Starter templates", size=15, color=MUTED)
        n2 = ChipFlow(["Human in the loop", "Sequential", "Group chat"], w=CB[1] - 40, theme="red", size=16, fill="soft")
        n2.place(cv, pal.ix, n1.bottom + 40)
    tg = [
        Box(CCOL[1], "Microsoft Agent Framework", sub="recommended - declarative YAML or code-first", icon="agent", icon_pos="left", theme="green", h=74, size=19,
            sub_size=14, fill="hatch"),
        Box(CCOL[1], "Azure Logic Apps", sub="fully visual, low-code; can call Foundry agents as steps", icon="logic-apps", icon_pos="left", theme="gray", h=74,
            size=19, sub_size=14, fill="hatch"),
        Box(CCOL[1], "A2A direct", sub="one agent calls another, no formal workflow", icon="a2a", icon_pos="left", theme="pink", h=74, size=19, sub_size=14,
            fill="hatch"),
    ]
    ty = cy - (3 * 74 + 2 * 16) / 2
    for b in tg:
        b.place(cv, CCOL[0], ty)
        ty += 74 + 16
    hosted = Box(CD[1], "Hosted agent", sub="runs YAML or code workflows - the only home for YAML workflows after 2026-12-01", icon="container-apps", icon_pos="left",
                 theme="green", h=112, size=21, sub_size=14, fill="hatch")
    hosted.place(cv, CD[0], tg[0].cy - 56)
    connect(cv, pal, tg[0], a_side="right", b_side="left", route="elbow", sw=3, color="#e03131", dash="dashed")
    cv.text(pal.right + 16, tg[1].cy - 50, "export the YAML,\nthen migrate", size=15, color="#c92a2a")
    connect(cv, pal, tg[1], a_side="right", b_side="left", route="elbow", sw=2.5, color="#e03131", dash="dashed")
    connect(cv, pal, tg[2], a_side="right", b_side="left", route="elbow", sw=2.5, color="#e03131", dash="dashed")
    connect(cv, tg[0], hosted, a_side="right", b_side="left", sw=3, label="deploy", label_size=15)
    return y + H


def lane_maf(cv, y):
    H = 240
    lane_frame(cv, y, H, 2, "Code-first: Microsoft Agent Framework", "Built-in multi-agent orchestration patterns in Python or C#, hosted on Foundry", "green",
               badge=None, src_=[src("maf")[0]])
    cy = y + H / 2
    code = Box(CA[1], "Your Agent Framework code", sub="Python or C#; workflow YAML or code", icon="code", icon_pos="left", theme="green", h=112, size=19,
               sub_size=14, fill="hatch")
    code.place(cv, CA[0], cy - 56)
    with cv.panel(CB[0], y + 26, title="Orchestration patterns, as documented", theme="green", style="dotted", pad=18, title_size=20, min_w=CB[1],
                  min_h=H - 52) as pal:
        cf = ChipFlow(["Sequential", "Concurrent", "Handoff", "Group Chat", "Magentic"], w=CB[1] - 40, theme="green", size=17)
        cf.place(cv, pal.ix, pal.iy + 6)
        cf2 = ChipFlow(["Human-in-the-loop: tool approval + request info"], w=CB[1] - 40, theme="yellow", size=16, fill="soft")
        cf2.place(cv, pal.ix, cf.bottom + 16)
    insp = Box(CCOL[1], "Test locally with Agent Inspector", sub="port 8088; workflow visualization and source navigation", icon="vscode", icon_pos="left",
               theme="violet", h=112, size=19, sub_size=14, fill="hatch")
    insp.place(cv, CCOL[0], cy - 56)
    hosted = Box(CD[1], "Hosted agent on Foundry", sub="agent-framework-foundry-hosting; Code + Remote or container; dedicated endpoint and agent identity",
                 icon="container-apps", icon_pos="left", theme="green", h=112, size=21, sub_size=14, fill="hatch")
    hosted.place(cv, CD[0], cy - 56)
    connect(cv, code, pal, a_side="right", b_side="left", sw=3, label="pick one", label_size=15)
    connect(cv, pal, insp, a_side="right", b_side="left", sw=3, label="build", label_size=15)
    connect(cv, insp, hosted, a_side="right", b_side="left", sw=3, label="deploy", label_size=15)
    return y + H


def lane_a2a(cv, y):
    H = 312
    lane_frame(cv, y, H, 3, "Agent to agent: A2A", "A prompt agent (or a hosted agent through a toolbox) calls any A2A endpoint through a project connection", "pink",
               badge="ga", src_=[src("a2atool")[0], src("a2ain")[0]])
    cy = y + H / 2
    caller = Box(CA[1], "Caller agent", sub="prompt agent, or hosted agent via its toolbox MCP endpoint", icon="agent", icon_pos="left", theme="green", h=112,
                 size=20, sub_size=14, fill="hatch")
    caller.place(cv, CA[0], cy - 56)
    with cv.panel(CB[0], y + 26, title="A2A tool + project connection", theme="pink", style="dotted", pad=18, title_size=20, min_w=CB[1], min_h=H - 52) as pal:
        cv.text(pal.ix, pal.iy + 2, "Tool type, by A2A protocol version", size=15, color=MUTED)
        r1 = ChipFlow(["a2a = A2A 1.0 (GA)", "a2a_preview = A2A 0.3 (Preview)"], w=CB[1] - 40, theme="pink", size=16)
        r1.place(cv, pal.ix, pal.iy + 26)
        cv.text(pal.ix, r1.bottom + 14, "The connection stores the endpoint, auth method and credentials", size=15, color=MUTED)
        r2 = ChipFlow(["key-based", "agent identity", "project managed identity", "Entra user delegation", "OAuth passthrough", "unauthenticated"],
                      w=CB[1] - 40, theme="red", size=15, fill="soft")
        r2.place(cv, pal.ix, r1.bottom + 40)
    tg = [
        Box(CCOL[1], "Any A2A-compatible endpoint", sub="third-party or your own (public, valid TLS)", icon="globe", icon_pos="left", theme="gray", h=76, size=18,
            sub_size=14, fill="hatch"),
        Box(CCOL[1], "Foundry agent with incoming A2A", sub="PATCH agent_card + a2a protocol; Entra only", icon="foundry", icon_pos="left", theme="green", h=76, size=18,
            sub_size=14, fill="hatch"),
        Box(CCOL[1], "Agent registered in Control Plane", sub="proxy URL; AI gateway access control and monitoring", icon="a2a", icon_pos="left", theme="grape", h=76, size=18,
            sub_size=14, fill="hatch"),
    ]
    ty = cy - (3 * 76 + 2 * 16) / 2
    for b in tg:
        b.place(cv, CCOL[0], ty)
        ty += 76 + 16
    badge_on(cv, tg[1], "preview")
    note = Note(CD[1], "Foundry agent targets: text only, no streaming, tasks and contexts kept 60 days. The Connected Agents tool of classic agents is gone - A2A or "
                       "Agent Framework replace it. Details on part 2.", kind="info", title="A2A at a glance", size=15)
    note.place(cv, CD[0], cy - note.h / 2)
    connect(cv, caller, pal, a_side="right", b_side="left", sw=3, label="uses", label_size=15)
    for b in tg:
        connect(cv, pal, b, a_side="right", b_side="left", route="elbow", sw=2.5)
    return y + H


def lane_responses(cv, y):
    H = 264
    lane_frame(cv, y, H, 4, "Model-driven: Responses API multi-agent", "One request; a GPT-5.6 model creates and coordinates subagents in parallel", "blue",
               badge="preview", src_=[src("multi")[0]])
    cy = y + H / 2
    app = Box(CA[1], "Your app", sub="POST /responses with multi_agent.enabled = true", icon="app", icon_pos="left", theme="gray", h=112, size=20, sub_size=14,
              fill="hatch")
    app.place(cv, CA[0], cy - 56)
    # agent tree
    root = Box(190, "/root", sub="receives the request", theme="blue", h=84, size=20, sub_size=13, fill="hatch")
    root.place(cv, CB[0], cy - 42)
    kids = []
    kx = CB[0] + 190 + 190
    ky = cy - (3 * 62 + 2 * 14) / 2
    for nm in ("/root/researcher", "/root/reviewer", "/root/writer"):
        b = Box(290, nm, theme="blue", h=62, size=18, fill="hatch")
        b.place(cv, kx, ky)
        kids.append(b)
        ky += 62 + 14
    tester = Box(300, "/root/reviewer/tester", theme="blue", h=62, size=18, fill="hatch", dash="dashed")
    tester.place(cv, kx + 290 + 90, kids[1].y)
    connect(cv, root, kids[0], a_side="right", b_side="left", route="elbow", sw=2.5)
    cv.text(root.right + 104, kids[0].cy - 26, "spawn_agent", size=14)
    connect(cv, root, kids[1], a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, root, kids[2], a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, kids[1], tester, a_side="right", b_side="left", sw=2.5)
    app2 = Box(CCOL[1], "Your app runs every function_call", sub="from any agent; returns function_call_output (HTTP continuation, or response.inject over WebSocket)",
               icon="app", icon_pos="left", theme="gray", h=130, size=19, sub_size=14, fill="hatch")
    app2.place(cv, CCOL[0], cy - 65)
    note = Note(CD[1], "Azure OpenAI Responses API (api-version=preview), not a Foundry agent resource. Hosted actions (spawn_agent, send_message, followup_task, "
                       "wait_agent, interrupt_agent, list_agents) run inside the service - your app never executes them.", kind="warn", title="Preview, GPT-5.6 only", size=15)
    note.place(cv, CD[0], cy - note.h / 2)
    connect(cv, app, root, a_side="right", b_side="left", sw=3, label="1 request", label_size=15)
    connect(cv, tester, app2, a_side="right", b_side="left", sw=2.5, dash="dashed", label="client tools", label_size=14, label_wrap=90)
    return y + H


def lane_routines(cv, y):
    H = 252
    lane_frame(cv, y, H, 5, "Triggers: Routines", "When a time or an event occurs, invoke this agent - exactly one trigger and one action", "violet",
               badge="preview", src_=[src("routines")[0]])
    cy = y + H / 2
    with cv.panel(CA[0], y + 22, title="Trigger", theme="violet", style="dotted", pad=16, title_size=20, min_w=CA[1], min_h=H - 44) as tp:
        cy0 = tp.iy + 4
        for lab, ic in (("timer (one-shot)", None), ("schedule (cron, min 5 min)", None), ("github_issue", "github"), ("custom: teams message", "teams")):
            ch = Chip(lab, theme="violet", size=16, icon=ic, w=CA[1] - 40, icon_size=28)
            ch.place(cv, tp.ix, cy0)
            cy0 += ch.h + 10
    rt = Box(CB[1] - 560, "Routine", sub="trigger + action + input; enable or disable; run history with trace links", icon="scheduler", icon_pos="left", theme="violet",
             h=130, size=22, sub_size=14, fill="hatch")
    rt.place(cv, CB[0], cy - 65)
    act = Box(560, "Action: invoke the agent", sub="Responses API or Invocations API; static input; 5 delivery attempts, 30 s per request", icon="api-connections",
              icon_pos="left", theme="green", h=130, size=19, sub_size=14, fill="hatch")
    act.place(cv, rt.right + 100, cy - 65)
    ag = Box(CCOL[1], "Prompt agent or hosted agent", sub="runs as the agent identity by default (creator identity is a create-time opt-in)", icon="agent", icon_pos="left",
             theme="green", h=130, size=19, sub_size=14, fill="hatch")
    ag.place(cv, CCOL[0], cy - 65)
    note = Note(CD[1], "No branching, no multiple agents, no approval steps inside a routine. Not in UK West, Switzerland West, Japan West, UAE North or Norway East. "
                       "No customer-managed keys.", kind="warn", title="Routines are only a trigger", size=15)
    note.place(cv, CD[0], cy - note.h / 2)
    connect(cv, tp, rt, a_side="right", b_side="left", sw=3, label="fires", label_size=15)
    connect(cv, rt, act, a_side="right", b_side="left", sw=3)
    connect(cv, act, ag, a_side="right", b_side="left", sw=3)
    return y + H


def band_lanes(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  The orchestration map - five ways to coordinate agents or start one",
             "Read each lane left to right. Status badges are the docs' own labels as of 2026-11-03; every lane has a deep dive further down or on part 2.")
    for fn, gap in ((lane_workflows, 26), (lane_maf, 26), (lane_a2a, 26), (lane_responses, 26), (lane_routines, 0)):
        y = fn(cv, y) + gap
    return y


# ================================================================================================ band 2: decision table
def band_decide(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Which one when - pick by the question you are answering",
             "Statuses are the docs' labels as of 2026-11-03. The routines page still points to workflows for multi-agent logic; with workflows retiring, "
             "read that as code-first orchestration inside the agent.")
    t = Table(
        [("You need", 640), ("Pick", 520), ("Status", 330), "Watch out"],
        [
            ["Run an agent when a time or an event occurs (summaries, reminders, issue triage)", ("Routines", "violet"), ("Preview", "yellow"),
             "One trigger + one action only: no branching, no second agent, no approvals"],
            ["A fixed multi-agent pipeline you control: ordered, parallel, handoff, shared chat or planned", ("Microsoft Agent Framework -> hosted agent", "green"),
             "Pattern pages show no preview banner; .NET Magentic types are experimental",
             "Pattern docs live on the Agent Framework site, not in the Foundry table of contents"],
            ["Call an agent someone else runs, or expose yours to other agents", ("A2A tool (outbound) / incoming A2A endpoint", "pink"),
             "a2a = 1.0 GA; incoming endpoint = Preview", "Incoming A2A defaults to v0.3 when no version is chosen; text only, no streaming"],
            ["Let the model split one task into parallel subagents", ("Responses API multi-agent", "blue"), ("Preview, GPT-5.6 only", "yellow"),
             "Not a Foundry agent resource; every agent shares the tools; subagents raise token use"],
            ["A drag-and-drop designer with deterministic steps", ("Azure Logic Apps (the docs' visual path)", "gray"), ("Workflows: Retiring 2026-12-01", "red"),
             "Do not start new work on Foundry workflows"],
            ["One agent simply hands a subtask to another, no workflow", ("A2A direct", "pink"), "a2a = 1.0 GA", "You keep the calling agent in control; the target must speak A2A"],
        ], w=S(4), theme="green", size=14, head_size=16, first_col_theme="green", title="Decision table", title_size=22)
    t.place(cv, 0, y)
    n1 = Note(S(2), "Routines answer 'when should my agent run?'; orchestration answers 'how do agents connect?'. A routine can invoke a hosted agent whose own "
                    "code runs an Agent Framework orchestration - the two compose.", kind="key", title="Trigger vs orchestration", src=src("routines"))
    n1.place(cv, X(4), y)
    n2 = Note(S(2), "Docs-lag flag: the routines page says to 'use a workflow instead' for branching, multiple agents or approvals, while the workflow page says "
                    "workflows retire on 2026-12-01 and new work should use Microsoft Agent Framework.", kind="warn", title="Docs disagree", src=src("routines", "workflow"))
    n2.place(cv, X(4), n1.bottom + 22)
    return max(t.bottom, n2.bottom)


def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(wrap_text(s, w, size))


# ================================================================================================ band 3: declarative workflows
def band_workflows(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Declarative workflows (Preview, retiring) - templates, nodes and what carries over",
             "Read this as migration context, not a new-build option: the patterns it offered (sequential, group chat, branching, human approval) are expressible "
             "in code or YAML on a supported runtime.")
    top = y
    PW, PG, MIN_H = 560, 32, 262
    inner = PW - 32
    bw, bh, gp = 142, 86, 40
    # --- template 1: human in the loop
    with cv.panel(0, top, title="Human in the loop", sub=wrap("Asks the user a question and awaits user input to proceed", inner, 14), theme="red",
                  style="dotted", pad=16, title_size=22, sub_size=14, min_w=PW, min_h=MIN_H) as p1:
        by = p1.iy + 16
        bs = [Box(bw, t, theme=th, h=bh, size=16, fill="hatch") for t, th in (("Ask the user a question", "red"), ("Wait for the user's input", "yellow"),
                                                                              ("Continue the workflow", "green"))]
        for i, b in enumerate(bs):
            b.place(cv, p1.ix + i * (bw + gp), by)
        connect(cv, bs[0], bs[1], a_side="right", b_side="left", sw=2.5, gap=3)
        connect(cv, bs[1], bs[2], a_side="right", b_side="left", sw=2.5, gap=3)
        cv.text(p1.ix, by + bh + 26, "Typical use: an approval request that waits for a human decision, or collecting information from the user.", size=14,
                color=MUTED, wrap=inner)
    # --- template 2: sequential
    with cv.panel(PW + PG, top, title="Sequential", sub=wrap("Passes the result from one agent to the next in a defined order", inner, 14), theme="red",
                  style="dotted", pad=16, title_size=22, sub_size=14, min_w=PW, min_h=MIN_H) as p2:
        by = p2.iy + 16
        bs = [Box(bw, f"Agent {n}", theme="green", h=bh, size=17, fill="hatch") for n in "123"]
        for i, b in enumerate(bs):
            b.place(cv, p2.ix + i * (bw + gp), by)
        connect(cv, bs[0], bs[1], a_side="right", b_side="left", sw=2.5, gap=3)
        connect(cv, bs[1], bs[2], a_side="right", b_side="left", sw=2.5, gap=3)
        cv.text(p2.ix, by + bh + 26, "Typical use: step-by-step workflows, pipelines or multiple-stage processing.", size=14, color=MUTED, wrap=inner)
    # --- template 3: group chat
    with cv.panel(2 * (PW + PG), top, title="Group chat", sub=wrap("Dynamically passes control between agents based on context or rules", inner, 14), theme="red",
                  style="dotted", pad=16, title_size=22, sub_size=14, min_w=PW, min_h=MIN_H) as p3:
        aw, ah = 128, 54
        a = Box(aw, "Agent A", theme="green", h=ah, size=17, fill="hatch").place(cv, p3.ix + 28, p3.iy + 6)
        b2 = Box(aw, "Agent B", theme="green", h=ah, size=17, fill="hatch").place(cv, p3.ix + inner - aw - 28, p3.iy + 6)
        c3 = Box(aw, "Agent C", theme="green", h=ah, size=17, fill="hatch").place(cv, p3.ix + (inner - aw) / 2, p3.iy + 6 + 104)
        connect(cv, a, b2, a_side="right", b_side="left", sw=2.5, gap=3, start_head="arrow")
        connect(cv, a, c3, a_side="bottom", b_side="left", route="elbow", sw=2.5, gap=3, start_head="arrow")
        connect(cv, b2, c3, a_side="bottom", b_side="right", route="elbow", sw=2.5, gap=3, start_head="arrow")
        cv.text(p3.ix, p3.iy + 6 + 104 + ah + 18, "Typical use: dynamic workflows, escalation, fallback or expert handoff.", size=14, color=MUTED, wrap=inner)
    # --- node types table + note (right)
    nodes = Table(
        [("Node type", 230), "What it does in the designer"],
        [
            [("Agent", "red"), "Invoke an agent: pick an existing Foundry agent or create one. Structured output: Details > parameter icon > Text format = JSON Schema, "
                                "saved to a variable"],
            [("Logic", "red"), "if/else, go to, for each"],
            [("Data transformation", "red"), "Set a variable or parse a value"],
            [("Basic chat", "red"), "Send a message or ask a question (an ask-a-question node saves the reply to a variable)"],
        ], w=S(3), theme="red", size=14, head_size=15, title="Four node types", title_size=22)
    nodes.place(cv, X(3), top)
    n1 = Note(S(3), "Hosted agents are not supported in the workflow designer. To coordinate agents inside a hosted agent, run Microsoft Agent Framework workflows "
                    "(or another framework with workflow support) in your hosted-agent code. Routines also do not support workflow agents.", kind="gotcha",
              title="Where workflows never reached", src=src("workflow", "routines"))
    n1.place(cv, X(3), nodes.bottom + 22)
    y1 = max(p1.bottom, p2.bottom, p3.bottom, n1.bottom) + 44
    # --- row 2: authoring + Power Fx cards, migration diagram
    feat = card(C, "Authoring features", [
        "Build > Create new workflow > a template; add nodes with the + icon; run in the chat window",
        "Not saved automatically: select Save after every change",
        "Each save is a new, unchangeable version; the Version list shows history",
        "YAML visualizer toggle: edit the graph or the YAML, both stay in sync",
        "Notes can be added on the canvas",
        "Needs Contributor or higher on the project",
    ], theme="red", icon="workflow", badge="retiring", src=src("workflow"))
    fx = card(C, "Power Fx expressions", [
        "Excel-like formulas set variables, parse values and drive if/else conditions",
        "Prefix variables: System. for system variables, Local. for your own",
        "System variables: Activity, Bot, Conversation (Id, LocalTimeZone, LocalTimeZoneOffset, InTestMode), LastMessage, User.Language",
        "Literals: String, Boolean, Number, Record and table, Date and time, Blank; Choice is not supported",
    ], theme="red", icon="gear", src=src("workflow"))
    _, rb = row(cv, 0, y1, [feat, fx], gap=G)
    st = Steps(S(2), "Migration flow", [
        "Open the workflow in the designer, switch to the YAML view and copy or export the YAML",
        "Pick a path: Agent Framework (recommended), Azure Logic Apps or A2A",
        "Agent Framework: Generate Code in VS Code (GitHub Copilot converts YAML to code), then review it",
        "Test locally with Agent Inspector; replay the requests you used on the old workflow",
        "Deploy as a hosted agent; keep the original definition until dependent apps use the replacement",
    ], theme="yellow", num_theme="red", src=src("workflow"))
    st.place(cv, 0, rb + 24)
    rb = st.bottom
    mx0 = X(2)
    o1 = card(960, "Option 1: Microsoft Agent Framework (recommended)", [
        "Same patterns through declarative YAML or code-first authoring",
        "Often you can bring the exported YAML into an Agent Framework project with minimal changes",
        "Keep iterating in VS Code instead of the portal",
        "Run the result by deploying it as a hosted agent - the same managed runtime as your other code-based agents",
    ], theme="green", icon="agent", src=src("workflow", "decl"))
    o2 = card(960, "Option 2: Azure Logic Apps", [
        "A fully featured low-code canvas that can call Foundry agents as steps",
        "Combine deterministic steps (built-in actions, APIs, MCP servers) with agent reasoning in one run",
        "Adopt agents incrementally in processes you already have",
    ], theme="gray", icon="logic-apps", src=src("logic"))
    o3 = card(960, "Option 3: A2A direct", [
        "For lightweight cases: one agent just calls another, no formal multistep workflow",
        "Expose an agent as an A2A endpoint and call it directly; the calling agent stays in control",
    ], theme="pink", icon="a2a", icon_size=40, src=src("workflow", "a2ain"))
    oy = y1
    for c in (o1, o2, o3):
        c.place(cv, mx0 + 410, oy)
        oy += c.h + 18
    total = oy - 18 - y1
    ex = Box(300, "Your workflow", sub="designer YAML view: copy or export the YAML before the designer retires", icon="workflow", icon_pos="top", theme="red", h=190,
             size=21, sub_size=14, fill="hatch")
    ex.place(cv, mx0, y1 + (total - ex.h) / 2)
    res = [
        Box(S(4) - 1480, "Hosted agent", sub="runs the YAML or code workflow on Foundry; endpoint + agent identity", icon="container-apps", icon_pos="left", theme="green",
            h=84, size=20, sub_size=14, fill="hatch"),
        Box(S(4) - 1480, "Logic Apps workflow", sub="Foundry agents as steps", icon="logic-apps", icon_pos="left", theme="gray", h=84, size=20, sub_size=14, fill="hatch"),
        Box(S(4) - 1480, "Caller agent + A2A tool", sub="calls a Foundry agent that has incoming A2A enabled (Preview)", icon="a2a", icon_pos="left", theme="pink", h=84,
            size=20, sub_size=14, fill="hatch"),
    ]
    for c, r in zip((o1, o2, o3), res):
        r.place(cv, mx0 + 1480, c.cy - 42)
        connect(cv, ex, c, a_side="right", b_side="left", route="elbow", sw=2.5, color="#e03131", dash="dashed")
        connect(cv, c, r, a_side="right", b_side="left", sw=2.5)
    y2 = max(rb, oy - 18) + 44
    # --- row 3: VS Code routes
    low = card(S(2), "VS Code, existing workflows (low-code route)", [
        "Foundry Toolkit > Agents > Workflow tab opens the playground: the graph is read-only, with a version selector",
        "Edit exported YAML locally in *.workflow.yaml - local changes do not sync to Foundry",
        "Deploy with the existing workflow name = a new version (before retirement); a different name creates a separate workflow",
        "The playground runs only the saved Foundry version, not your local YAML or generated code",
        "Generate Code (Python or C#) asks GitHub Copilot to convert the YAML to Agent Framework code - review required, it does not deploy",
    ], theme="indigo", icon="vscode", src=src("lowcode"))
    pro = card(S(2), "VS Code, hosted-agent workflow (pro-code route)", [
        "Create from an Agent Framework sample that uses the Responses protocol (Foundry Toolkit > Create Agent > Browse all samples)",
        "Python: Multi-Agent Workflow chains a writer, a reviewer and a formatter; C#: Translation Workflow chains EN -> FR -> ES -> EN",
        "Run locally and inspect with Agent Inspector (workflow visualization)",
        "Deploy source code (Code + Remote package mode, no local Docker build) or as a container; Foundry Project Manager at project scope",
        "These hosted workflows are code - different from the retiring declarative workflow service",
    ], theme="indigo", icon="vscode", src=src("procode"))
    insp = card(S(2), "Agent Inspector and tracing (validate a migration)", [
        "Agent Inspector in Foundry Toolkit tests a local Agent Framework workflow while you validate a migration",
        "Supported Agent Framework development servers provide the diagnostics for workflow visualization and source navigation",
        "Configure local tracing to compare recorded spans across runs; Tracing in Foundry Toolkit also covers a deployed hosted agent",
        "! These local steps do not replace the remote playground for a declarative workflow, and they run only supported local workflows",
    ], theme="violet", icon="monitor", src=src("workflow", "lowcode"))
    _, b3 = row(cv, 0, y2, [low, pro, insp], gap=G)
    return b3


# ================================================================================================ band 4: Agent Framework patterns
PW5, PG5 = 680, 50


def pattern_panel(cv, i, y, title, doc, theme, fn, min_h):
    with cv.panel(i * (PW5 + PG5), y, title=title, sub=wrap(doc, PW5 - 40, 15), theme=theme, style="solid", fill="soft", pad=18, title_size=26, sub_size=15,
                  min_w=PW5, min_h=min_h) as p:
        fn(cv, p)
    return p


def d_sequential(cv, p):
    iw = PW5 - 36
    y0 = p.iy + 56
    bw, bh = 120, 64
    xs = [p.ix + 62, p.ix + 62 + 200, p.ix + 62 + 400]
    bs = [Box(bw, f"Agent {n}", theme="green", h=bh, size=18, fill="hatch").place(cv, x, y0) for n, x in zip("ABC", xs)]
    cy = y0 + bh / 2
    arrow(cv, [(p.ix, cy), (xs[0] - 6, cy)], sw=2.5, label="input", label_size=14, label_dy=-6)
    connect(cv, bs[0], bs[1], a_side="right", b_side="left", sw=2.5, gap=3)
    connect(cv, bs[1], bs[2], a_side="right", b_side="left", sw=2.5, gap=3)
    arrow(cv, [(bs[2].right + 6, cy), (p.ix + iw, cy)], sw=2.5, label="output", label_size=14, label_dy=-6)
    cv.text(p.ix, y0 + bh + 34, "Each agent takes the previous agent's output as its turn: a pipeline.", size=15, color=MUTED, wrap=iw)
    ChipFlow(["pipeline", "default: previous agent's full conversation", "chain_only_agent_responses=True (Python): responses only",
              "mix agents with custom executors"], w=iw, theme="green", size=15, fill="soft").place(cv, p.ix, y0 + bh + 82)


def d_concurrent(cv, p):
    iw = PW5 - 36
    cy = p.iy + 130
    inp = Box(104, "Input", theme="gray", h=64, size=17, fill="hatch").place(cv, p.ix, cy - 32)
    ags = []
    for k in range(3):
        ags.append(Box(160, f"Agent {k + 1}", theme="green", h=52, size=17, fill="hatch").place(cv, p.ix + 176, cy - 90 + k * 64))
    agg = Box(140, "Aggregator", sub="merges the results", theme="teal", h=70, size=17, sub_size=13, fill="hatch").place(cv, p.ix + 176 + 160 + 100, cy - 35)
    for a in ags:
        connect(cv, inp, a, a_side="right", b_side="left", sw=2.5, gap=3, route="elbow")
        connect(cv, a, agg, a_side="right", b_side="left", sw=2.5, gap=3, route="elbow")
    arrow(cv, [(agg.right + 6, cy), (p.ix + iw, cy)], sw=2.5, label="result", label_size=14, label_dy=-8)
    cv.text(p.ix, cy + 112, "All agents work on the same task at once and independently.", size=15, color=MUTED, wrap=iw)
    ChipFlow(["parallel, then aggregate", "custom aggregator callback", "agents or custom executors"], w=iw, theme="green", size=15, fill="soft").place(
        cv, p.ix, cy + 150)


def d_handoff(cv, p):
    iw = PW5 - 36
    aw, ah = 132, 56
    top = p.iy + 30
    usr = Box(86, "User", theme="gray", h=56, size=16, fill="hatch").place(cv, p.ix, top)
    A = Box(aw, "Agent A", sub="start agent", theme="green", h=ah + 8, size=17, sub_size=13, fill="hatch").place(cv, p.ix + 120, top - 4)
    B = Box(aw, "Agent B", theme="green", h=ah, size=17, fill="hatch").place(cv, p.ix + iw - aw - 6, top)
    Cc = Box(aw, "Agent C", theme="green", h=ah, size=17, fill="hatch").place(cv, p.ix + 120, top + 118)
    D = Box(aw, "Agent D", theme="green", h=ah, size=17, fill="hatch").place(cv, p.ix + iw - aw - 6, top + 118)
    connect(cv, usr, A, a_side="right", b_side="left", sw=2.5, gap=3)
    connect(cv, A, B, a_side="right", b_side="left", sw=2.5, gap=3, start_head="arrow")
    connect(cv, Cc, D, a_side="right", b_side="left", sw=2.5, gap=3, start_head="arrow")
    connect(cv, A, Cc, a_side="bottom", b_side="top", sw=2.5, gap=3, start_head="arrow")
    connect(cv, B, D, a_side="bottom", b_side="top", sw=2.5, gap=3, start_head="arrow")
    cv.text(p.ix, top + 118 + ah + 20, "No orchestrator: the agent holding the task decides whether to hand the whole task to another agent.", size=15, color=MUTED, wrap=iw)
    Chip("mesh topology", theme="green", size=15, fill="soft").place(cv, p.ix, top + 118 + ah + 74)


def d_group(cv, p):
    iw = PW5 - 36
    cx = p.ix + iw / 2
    cy = p.iy + 108
    orch = Box(196, "Orchestrator", sub="decides who speaks next", theme="teal", h=80, size=18, sub_size=13, fill="hatch").place(cv, cx - 98, cy - 40)
    pw_, ph = 128, 50
    ps = [Box(pw_, "Agent 1", theme="green", h=ph, size=16, fill="hatch").place(cv, p.ix + 4, p.iy + 2),
          Box(pw_, "Agent 2", theme="green", h=ph, size=16, fill="hatch").place(cv, p.ix + iw - pw_ - 4, p.iy + 2),
          Box(pw_, "Agent 3", theme="green", h=ph, size=16, fill="hatch").place(cv, p.ix + 4, p.iy + 164),
          Box(pw_, "Agent 4", theme="green", h=ph, size=16, fill="hatch").place(cv, p.ix + iw - pw_ - 4, p.iy + 164)]
    for q in ps:
        connect(cv, orch, q, sw=2.5, gap=3, start_head="arrow")
    cv.text(p.ix, p.iy + 232, "Every agent sees the shared conversation; the orchestrator syncs sessions and broadcasts each reply.", size=15, color=MUTED, wrap=iw)
    ChipFlow(["star topology", "round-robin", "prompt-based", "custom logic"], w=iw, theme="green", size=15, fill="soft").place(cv, p.ix, p.iy + 288)


def d_magentic(cv, p):
    iw = PW5 - 36
    cx = p.ix + 250
    mgr = Box(250, "Magentic manager", sub="plans, tracks progress, replans", theme="teal", h=84, size=18, sub_size=13, fill="hatch").place(cv, p.ix + 20, p.iy + 4)
    rev = Box(214, "Optional plan review", sub="approve or revise the plan", theme="yellow", h=84, size=17, sub_size=13, fill="soft", dash="dashed").place(
        cv, p.ix + iw - 214, p.iy + 4)
    ags = [Box(150, f"Agent {n}", theme="green", h=54, size=17, fill="hatch").place(cv, p.ix + 8 + k * 196, p.iy + 160) for k, n in enumerate("123")]
    for a in ags:
        connect(cv, mgr, a, a_side="bottom", b_side="top", sw=2.5, gap=3, start_head="arrow")
    connect(cv, mgr, rev, a_side="right", b_side="left", sw=2, gap=3, dash="dashed", start_head="arrow")
    cv.text(p.ix, p.iy + 230, "Agents are picked per subtask, in any order and as often as needed; a progress ledger flags loops and stalls.", size=15, color=MUTED, wrap=iw)
    ChipFlow(["star topology", "planning manager", "stall detection + replan"], w=iw, theme="green", size=15, fill="soft").place(cv, p.ix, p.iy + 290)


def band_maf(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Microsoft Agent Framework orchestration patterns - drawn as the docs describe them",
             "Five built-in patterns documented on the Agent Framework site (not in the Foundry table of contents). Run them on Foundry by deploying the code as a hosted agent.")
    MH = 424
    ps = [
        pattern_panel(cv, 0, y, "1  Sequential", "Agents execute one after another in a defined order", "green", d_sequential, MH),
        pattern_panel(cv, 1, y, "2  Concurrent", "Agents execute in parallel on the same task", "green", d_concurrent, MH),
        pattern_panel(cv, 2, y, "3  Handoff", "Agents transfer control to each other based on context", "green", d_handoff, MH),
        pattern_panel(cv, 3, y, "4  Group Chat", "Agents collaborate in a shared conversation", "green", d_group, MH),
        pattern_panel(cv, 4, y, "5  Magentic", "A manager agent dynamically coordinates specialized agents", "green", d_magentic, MH),
    ]
    by = max(p.bottom for p in ps) + 22
    bl = [
        card(PW5, "Sequential: facts", [
            "Pipeline: each agent processes the task in turn and passes its output on; order is the participants list",
            "Default: each agent consumes the previous agent's full conversation (input + response)",
            "Python chain_only_agent_responses=True passes only the previous agent's response messages",
            "Mix agents with custom executors; terminal output is the last agent's response",
            "Good for document review, data pipelines, multi-stage reasoning",
        ], theme="green", src=src("seq")),
        card(PW5, "Concurrent: facts", [
            "Several agents work on the same task in parallel, each independently",
            "Default aggregation: one AgentResponse with one assistant message per participant",
            "Custom aggregator callback (sync or async) can post-process, for example summarize",
            "Participants can be agents or custom executors",
            "Good for brainstorming, ensemble reasoning and voting",
        ], theme="green", src=src("conc")),
        card(PW5, "Handoff: facts", [
            "Mesh topology, no orchestrator; the receiving agent takes full ownership of the task",
            "Handoff tools are registered from your handoff rules; the agent calls one to transfer control",
            "Interactive by default; autonomous mode keeps agents going (50 turns per agent by default in the .NET docs)",
            "Agents do not share a session: user and agent messages are broadcast, tool calls (including handoffs) are not",
            "Only Agent participants that support local tool execution; checkpointing for durable workflows",
        ], theme="green", src=src("hand")),
        card(PW5, "Group chat: facts", [
            "Star topology: the orchestrator picks the next speaker - round-robin, prompt-based (an agent) or custom logic",
            "All agents see the full history: the orchestrator syncs each session before a turn and broadcasts each reply",
            "Iterative refinement over rounds; .NET MaximumIterationCount bounds the turns",
            "Python parameters: selection_func, orchestrator_agent or orchestrator",
            "Good for writer-reviewer loops, multi-perspective analysis, quality assurance",
        ], theme="green", src=src("group")),
        card(PW5, "Magentic: facts", [
            "Based on Magentic-One (AutoGen); same architecture as group chat with a planning manager",
            "Loop: plan, optional plan review, pick agent, execute, assess, stall detection and replan, final synthesis",
            "Limits: max rounds, max consecutive stalls before replanning, max plan resets",
            "Plan review: off by default in Python, on by default in .NET (RequirePlanSignoff)",
            "! Untested outside the original Magentic-One design; the .NET sample marks the types experimental (MAAIW001)",
        ], theme="green", src=src("mag")),
    ]
    r, b = row(cv, 0, by, bl, gap=PG5)
    y2 = b + 40
    t = Table(
        [("Pattern", 190), ("Topology", 230), ("Who chooses the next step", 340), ("Context between agents", 470), ("Documented use cases", 560)],
        [
            [("Sequential", "green"), "Pipeline", "The defined order", "Previous agent's full conversation by default, or only its responses (Python option)",
             "Document review, data processing pipelines, multi-stage reasoning"],
            [("Concurrent", "green"), "Parallel fan-out, aggregate", "Nobody: all run at once", "Each agent works independently on the input; results aggregated",
             "Brainstorming, ensemble reasoning, voting"],
            [("Handoff", "green"), "Mesh, no orchestrator", "The agent that holds the task, by rules or message content", "User and agent messages broadcast to all; tool calls are not",
             "Customer support, expert systems, dynamic delegation"],
            [("Group Chat", "green"), "Star, orchestrator in the middle", "The orchestrator: round-robin, prompt-based or custom", "Full shared history, synced before each turn",
             "Iterative refinement, collaborative problem-solving, writer-reviewer, QA"],
            [("Magentic", "green"), "Star, planning manager", "The manager, from its plan and progress ledger", "The manager keeps the shared context and adapts the plan",
             "Complex, open-ended tasks where the solution path is not known in advance"],
        ], w=S(4), theme="green", size=14, head_size=15, first_col_theme="green", title="Pattern comparison (as documented)", title_size=22)
    t.place(cv, 0, y2)
    hv = Table(
        [("", 150), ("Handoff", 280), ("Agent-as-tools", 280)],
        [
            ["Control flow", "Control is passed explicitly between agents; no central authority", "A primary agent delegates subtasks and gets control back"],
            ["Task ownership", "The receiving agent takes full ownership", "The primary agent keeps overall responsibility"],
            ["Context", "The receiving agent has full context so far", "The primary agent passes only the relevant information"],
        ], w=S(2), theme="green", size=14, head_size=15, first_col_theme="green", title="Handoff vs agent-as-tools", title_size=22)
    hv.place(cv, X(4), y2)
    n1 = Note(S(2), "Choose another pattern when: you need strict order (Sequential), agents should work fully independently (Concurrent), direct agent-to-agent transfer "
                    "is needed (Handoff), or complex dynamic planning is required (Magentic) - the group chat page's own guidance.", kind="tip", title="Choosing between patterns",
              src=src("group"))
    n1.place(cv, X(4), hv.bottom + 22)
    y3 = max(t.bottom, n1.bottom) + 36
    host = card(S(2), "Run them on Foundry: hosted agents", [
        "Orchestrations are Agent Framework code (Python or C#); to run on Foundry, deploy the code as a hosted agent",
        "Python package agent-framework-foundry-hosting exposes the agent or workflow on the hosted-agent protocols",
        "Hosted agents get a dedicated endpoint and Entra agent identity; one VM-isolated sandbox per session",
        "Hosted-agent runtime, sessions and state are drawn on 'Hosted agents: your code on Foundry's runtime'",
    ], theme="green", icon="container-apps", src=src("fwhost", "mafhost"))
    host.place(cv, 0, y3)
    ctx = card(S(2), "Context and sessions in group patterns", [
        "Agents rely on agent sessions for context; in Handoff and Group Chat they do NOT share one session instance",
        "Participants (Handoff) or the orchestrator (Group Chat) synchronize each agent's context by broadcasting messages",
        "Python keeps user text, inline data, URIs, hosted files and vector stores; other messages keep text only; tool-control content is filtered before broadcast",
        "To redact text before it enters shared history, filter in a custom GroupChatOrchestrator response handler",
    ], theme="gray", icon="gear", src=src("hand", "group"))
    ctx.place(cv, X(2), y3)
    n2 = Note(S(2), "In the docs, human-in-the-loop for orchestrations means tool approval and request info; each pattern's page shows the details (section 5 collects them).",
              kind="key", title="Human in the loop", src=src("maf", "hitl"))
    n2.place(cv, X(4), y3)
    return max(host.bottom, ctx.bottom, n2.bottom)


# ================================================================================================ band 5: human in the loop
def band_hitl(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Human in the loop - where a person can step in",
             "Every surface that coordinates agents has its own pause-for-a-human mechanism. As documented, as of 2026-11-03.")
    def lk(label, key):
        return {"text": label, "link": U[key][1], "color": LINK}

    def ct(text, th):
        return {"text": text, "theme": th, "color": THEMES[th].deep}

    t = Table(
        [("Surface", 330), ("Mechanism", 1900), ("Status", 330), ("Learn", 432)],
        [
            [ct("Foundry workflows", "red"), "Human in the loop template and the Basic chat ask-a-question node: the workflow asks the user and waits for input before continuing",
             ("Retiring 2026-12-01", "red"), lk("Build a workflow", "workflow")],
            [ct("Agent Framework orchestrations", "green"), "Tool approval (approval-required tools pause the workflow for human review before execution) and request info "
                                                          "(pause after chosen agents for feedback; Python with_request_info)", "Agent Framework docs", lk("Human-in-the-loop", "hitl")],
            [ct("Sequential (.NET)", "green"), "Tool approval only; for free-form back-and-forth use Handoff (interactive by default) or a custom workflow with a RequestPort",
             "Agent Framework docs", lk("Sequential orchestration", "seq")],
            [ct("Handoff", "green"), "Control returns to the user when an agent answers without handing off; tool approval; checkpointing pauses and resumes across restarts; "
                                  "autonomous mode removes the pause", "Agent Framework docs", lk("Handoff orchestration", "hand")],
            [ct("Magentic", "green"), "Plan review: approve the manager's plan or revise it; also on stall-triggered replans (default off in Python, on in .NET)",
             "Agent Framework docs", lk("Magentic orchestration", "mag")],
            [ct("Responses multi-agent", "blue"), "Your app is the gate: require user approval before write, destructive, financial or other high-impact actions, and log agent, "
                                               "tool, arguments, decision and result", ("Preview", "yellow"), lk("Responses multi-agent", "multi")],
            [ct("Routines", "violet"), "None inside a routine: it only starts an agent (one trigger, one action). The invoked agent can implement its own approvals",
             ("Preview", "yellow"), lk("Routines", "routines")],
        ], w=S(5), theme="yellow", size=14, head_size=15, title="Pause-for-a-human map", title_size=22)
    t.place(cv, 0, y)
    n = Note(C, "Hosted agents add their own long-running and suspended-turn mechanisms - see the hosted-agent canvases.", kind="info", title="Hosted agents",
             src=src("hosted"))
    n.place(cv, X(5), y)
    return max(t.bottom, n.bottom)


# ================================================================================================ band 6: gotchas
def band_gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Docs disagree, gaps and gotchas - as of 2026-11-03",
             "Where two sources give different answers both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 860), ("Another source says", 860), "How to read it"], [
        [("Multi-agent in workflows", "orange"), "The A2A tool page and the routines page still point to workflows for multi-agent, branching and approval patterns",
         "The workflow page: Foundry retires workflows on 2026-12-01 and new workflows should use Microsoft Agent Framework",
         "Treat the older pointers as lagging; plan on Agent Framework"],
        [("Which patterns exist", "orange"), "The Foundry workflow page lists three designer templates: Human in the loop, Sequential, Group chat",
         "The Agent Framework docs list five patterns: Sequential, Concurrent, Handoff, Group Chat, Magentic",
         "Different surfaces: designer templates vs framework patterns"],
        [("Magentic maturity", "orange"), "A Build-2026 recap (blog-sourced, not Learn) calls Agent Framework multi-agent orchestration, including Magentic-One, stable",
         "The Magentic page: .NET sample suppresses warning MAAIW001 ('Magentic types are experimental') and says performance outside the original design is untested",
         "Check the package status before production"],
        [("Workflow agent type", "orange"), "The workflow page: workflows are no longer a separate agent type after the retirement",
         "REST still lists kind: workflow (CSDL YAML) with the same retirement notice; Azure Government lists Workflows as Preview",
         "Same conclusion: do not build new on it"],
    ], w=S(6), theme="orange", size=14, head_size=15, first_col_theme="orange", title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    ny = t.bottom + 30
    g1 = Note(S(2), "The Agent Framework pattern docs sit outside the Foundry table of contents. Handoff supports only Agent participants that can run tools locally, and "
                    "agents in Handoff and Group Chat do not share a session.", kind="gotcha", title="Pattern gotchas", src=src("maf", "hand"))
    g1.place(cv, 0, ny)
    g2 = Note(S(2), "Plan review defaults differ by language: Python off, .NET on. Sequential 'chain_only_agent_responses' and 'ensure_trailing_user_turn' are Python options; "
                    "the .NET page uses different builders.", kind="warn", title="Language differences", src=src("seq", "mag"))
    g2.place(cv, X(2), ny)
    g3 = Note(S(2), "Not documented for orchestrations as read here: latency or cost guidance per pattern, and a maximum participant count. Nothing on this canvas fills "
                    "those gaps.", kind="quote", title="What the docs do not say")
    g3.place(cv, X(4), ny)
    return max(g1.bottom, g2.bottom, g3.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Workflows, routines, A2A and multi-agent orchestration",
        "Five ways Foundry coordinates several agents or starts one on a trigger  |  part 1: the map, declarative workflows (retiring) and Agent Framework patterns  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Tools and A2A", "pink"), ("Identity and security", "red"),
                           ("Observability", "violet"), ("Cost and capacity", "yellow"), ("State and data", "cyan"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature", size=15)
    draw_badge(cv, bx + 260, y - 1, "retiring")
    cv.text(bx + 360, y, "retiring (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Prompt agents in depth", "Prompt agents: harness, A2A, routines and migration",
                "Hosted agents: your code on Foundry's runtime", "Foundry Toolbox", "Agent identity and delegation",
                "Workflows part 2: A2A, Responses and routines"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_banner(cv, y) + 34
    y = band_tiles(cv, y) + 56
    y = band_lanes(cv, y) + 56
    y = band_decide(cv, y) + 56
    y = band_workflows(cv, y) + 56
    y = band_maf(cv, y) + 56
    y = band_hitl(cv, y) + 56
    y = band_gotchas(cv, y) + 56
    sources(cv, 0, y, [
        ("Build a workflow in Microsoft Foundry (retiring)", U["workflow"][1]), ("Use and migrate declarative workflows (VS Code)", U["lowcode"][1]),
        ("Create hosted agents with Foundry Toolkit for VS Code", U["procode"][1]), ("Host agents built with frameworks", U["fwhost"][1]),
        ("Agent Framework: workflow orchestrations", U["maf"][1]), ("Agent Framework: sequential orchestration", U["seq"][1]),
        ("Agent Framework: concurrent orchestration", U["conc"][1]), ("Agent Framework: handoff orchestration", U["hand"][1]),
        ("Agent Framework: group chat orchestration", U["group"][1]), ("Agent Framework: Magentic orchestration", U["mag"][1]),
        ("Agent Framework: human-in-the-loop", U["hitl"][1]), ("Agent Framework: declarative workflows", U["decl"][1]),
        ("Agent Framework: Foundry hosted agent", U["mafhost"][1]), ("Automate Foundry agents with Azure Logic Apps workflows", U["logic"][1]),
        ("Routines in Foundry Agent Service", U["routines"][1]), ("Hosted agents (concepts)", U["hosted"][1]),
    ], w=W, cols=4)
