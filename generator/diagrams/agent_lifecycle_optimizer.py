"""Agent lifecycle and the optimizer (Agent Service), part 1: the nine-step build -> test -> ship -> improve loop, the local toolbelt
(azd, Agent Inspector, agent doctor, Foundry Toolkit), evaluation hooks, the agent optimizer at a glance, the release pipeline at a glance
and a 'what to use when' table.

Part 2 ('agent-lifecycle-optimizer-part-2') covers the optimizer in depth (optimizer-ready, datasets, run, REST, costs), the Prompt Optimizer
and the hosted-agent CI/CD template.  The full AgentOps loop and CI/CD pipelines live on the AgentOps canvases; this one stays agent-specific.
Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import Note as _KitNote
from generator.xd.palette import STATUS

META = dict(
    id="agent-lifecycle-optimizer", title="Agent lifecycle and the optimizer: build, test, ship, improve", section="2", group="Agent Service", order=17,
    description="The agent development lifecycle as a loop (build, test, trace, evaluate, optimize, publish, monitor), the local toolbelt (azd, Agent Inspector, agent doctor), "
                "evaluation hooks, the agent optimizer (Preview) at a glance, release promotion and a what-to-use-when table.",
    tags=["agent-lifecycle", "azd", "agent-inspector", "evaluation", "agent-optimizer", "ci-cd"],
)

class Note(_KitNote):
    """Kit Note plus 10 px of bottom padding when it carries Learn: lines (the kit lets the last link touch the border)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if self.src_lines:
            self.h += 10


W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    life=("Agent development lifecycle", learn("agents/concepts/development-lifecycle")),
    cli=("Agent development with the Azure Developer CLI", learn("agents/concepts/cli-agent-development")),
    insp=("Agent Inspector", learn("agents/how-to/agent-inspector")),
    doc=("azd ai agent doctor", learn("agents/how-to/agent-doctor")),
    ovo=("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
    costs=("Agent optimizer costs and token usage", learn("agents/concepts/agent-optimizer-costs")),
    ready=("Make your agent optimizer-ready", learn("agents/how-to/make-agent-optimizer-ready")),
    ds=("Create an optimizer dataset", learn("agents/how-to/create-optimizer-dataset")),
    tg=("Optimize agent instructions, skills, tools and models", learn("agents/how-to/optimize-agent-targets")),
    qh=("Quickstart: optimize a hosted agent", learn("agents/quickstarts/quickstart-optimize-hosted-agent")),
    qp=("Quickstart: optimize a prompt agent", learn("agents/quickstarts/quickstart-optimize-prompt-agent")),
    po=("Optimize agent prompts with Prompt Optimizer", learn("observability/how-to/prompt-optimizer")),
    cicd=("Set up CI/CD for hosted agents with azd", learn("agents/how-to/set-up-ci-cd-cli")),
    cdq=("Quickstart: set up CI/CD for a hosted agent", learn("agents/quickstarts/set-up-cicd-hosted-agent")),
    prod=("Promote hosted agents to production with azd", learn("agents/how-to/deploy-hosted-agent-production")),
    canvas=("Microsoft Foundry Canvas", learn("agents/concepts/foundry-agent-canvas")),
    rest=("REST: create an agent optimization job", learn("reference/rest/agent-optimization-jobs-create")),
    aeval=("Agent evaluators", learn("concepts/evaluation-evaluators/agent-evaluators")),
    ov=("Foundry Agent Service overview", learn("agents/overview")),
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


def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(wrap_text(s, w, size))


def bullets(cv, x, y, w, items, theme_name="violet", size=15, gap=6) -> float:
    """Ring-bullet list drawn straight on the canvas (same look as Card bullets, no border); returns the bottom y."""
    th = THEMES[theme_name]
    cy, lh = y, size * metrics.line_ratio()
    for it in items:
        warn = it.startswith("! ")
        txt = it[2:] if warn else it
        lines = wrap_text(txt, (w - 22) * 0.965, size)
        mc = "#e03131" if warn else th.stroke
        cv.ellipse(x + 2, cy + lh / 2 - 4, 9, 9, stroke=mc, sw=2, rough=0)
        cv.text(x + 22, cy, "\n".join(lines), size=size, color="#c92a2a" if warn else INK)
        cy += len(lines) * lh + gap
    return cy - gap


def cite(cv, x, y, items) -> float:
    """Clickable 'Learn:' lines; returns the bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 2
    return y


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


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
    """Numbered walk-through card."""

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


class CodeBlock(Rect2):
    """Monospace snippet in a soft rounded box (Excalifont has no code face, so Comic Shanns is used)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=14, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title = w, size, pad, title
        inner = (w - 2 * pad) * 0.965
        self.lines: list[str] = []
        for ln in lines:
            if metrics.line_width(ln, size, MONO) <= inner:
                self.lines.append(ln)
            else:
                self.lines += wrap_text(ln, inner, size, MONO)
        self.lh = size * metrics.line_ratio(MONO)
        self.t_h = (17 * 1.25 + 6) if title else 0
        self.src = list(src)
        self.src_h = (8 + len(self.src) * 15) if self.src else 0
        self.h = pad * 2 + self.t_h + len(self.lines) * self.lh + self.src_h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=2)
            ty = y + self.pad
            if self.title:
                cv.text(x + self.pad, ty, self.title, size=17, color=self.th.deep)
                ty += self.t_h
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=MONO)
            sy = ty + len(self.lines) * self.lh + 8
            for label, url in self.src:
                cv.text(x + self.pad, sy, f"Learn: {label}", size=12, color=LINK, link=url)
                sy += 15
        cv.register("code", x, y, self.w, H)
        return self


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "9 steps", "The lifecycle page lists nine steps from choosing the agent type to monitoring; the overview page lists seven (create, test, trace, evaluate, optimize, publish, monitor).", "green"),
        Tile(C, "4 targets", "The agent optimizer improves instructions, skills (hosted only), tool descriptions and the model; each activates from files you provide.", "violet"),
        Tile(C, "0.0 - 1.0", "Candidates are ranked by a composite score. A gain under 0.03 is noise, 0.03 to 0.10 is worth deploying, above 0.20 is major.", "violet"),
        Tile(C, "Mostly Preview", "Agent optimizer, Agent Inspector, agent doctor, tracing and evaluation are Preview (as of 2026-11-03). Foundry Toolkit for VS Code is GA per a Build blog.", "orange"),
        Tile(C, "2 optimizers", "The agent optimizer (dataset, evaluators, candidates) and the Prompt Optimizer (an instructions-only rewrite) are different tools.", "gray"),
        Tile(C, "Real tool calls", "The optimizer invokes your agent for every task, so external tools run for real: point it at test endpoints or mocks.", "red"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: the loop
def band_loop(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  The loop: build, test, ship, improve - the nine documented steps",
             "Two lanes make one loop: build and debug on the way out, then evaluate, optimize and ship, then monitor and feed the next version back in. Every step names the tool that does it.")
    top = y
    LW = S(4)
    NW, NH = 400, 160
    GX = (LW - 5 * NW) / 4

    def cx_(i):
        return i * (NW + GX)

    ya = top + 66
    yb = ya + NH + 180
    for yy, label, th_name in ((top, "BUILD AND DEBUG: the inner loop on your machine and in the playground", "green"),
                               (yb + NH + 18, "EVALUATE, OPTIMIZE AND SHIP: gate every change, then watch it run", "violet")):
        th = THEMES[th_name]
        cv.rect(0, yy, LW, 46, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        tw, thh = text_size(label, 19)
        cv.text((LW - tw) / 2, yy + (46 - thh) / 2, label, size=19, color=th.deep)
    spec = [  # n, col, row, title, sub, icon, theme, preview
        (1, 0, 0, "Choose the agent type", "prompt, voice-based prompt or hosted", "agent", "green", False),
        (2, 1, 0, "Create and test", "playground or code; locally azd ai agent run with the Agent Inspector", "code", "green", False),
        (3, 2, 0, "Add tools and data", "a tool must be configured successfully before the agent can be saved with it", "toolbox", "orange", False),
        (4, 3, 0, "Save changes as versions", "immutable; compare setup, chat output and YAML across versions", "versions", "green", False),
        (5, 4, 0, "Debug with tracing", "tool calls, inputs and outputs, latency", "app-insights", "violet", True),
        (6, 4, 1, "Evaluate quality and safety", "run before publishing and after any meaningful change", "metrics", "violet", True),
        (7, 3, 1, "Optimize", "agent optimizer: better instructions, skills, tool descriptions, model", "gear", "violet", True),
        (8, 2, 1, "Publish and deploy", "stable endpoint; azd deploy; choose the version it serves", "builds", "green", False),
        (9, 1, 1, "Monitor and iterate", "azd ai agent monitor and Application Insights; ship the next version", "dashboard", "violet", False),
    ]
    nodes = {}
    for n, col, rw_, title, sub, icon, th_name, prev in spec:
        b = Box(NW, title, sub=sub, theme=th_name, h=NH, size=20, sub_size=14, fill="hatch", icon=icon, icon_pos="left", icon_size=34)
        b.place(cv, cx_(col), ya if rw_ == 0 else yb)
        numbered(cv, b.x + 22, b.y + 22, n, theme=th_name, d=32, size=18)
        if prev:
            badge_on(cv, b, "preview")
        nodes[n] = b
    k = "#343a40"
    for a, b in ((1, 2), (2, 3), (3, 4), (4, 5)):
        connect(cv, nodes[a], nodes[b], a_side="right", b_side="left", sw=3, color=k)
    connect(cv, nodes[5], nodes[6], a_side="bottom", b_side="top", sw=3, color=k, label="gate", label_size=15)
    for a, b in ((6, 7), (7, 8), (8, 9)):
        connect(cv, nodes[a], nodes[b], a_side="left", b_side="right", sw=3, color=k)
    connect(cv, nodes[9], nodes[2], a_side="top", b_side="bottom", sw=3, color="#2b8a3e", dash="dashed", label="iterate: the next version", label_size=14, label_wrap=190)
    connect(cv, nodes[7], nodes[4], a_side="top", b_side="bottom", sw=3, color="#6741d9", dash="dashed", label="apply the winning candidate: a new version", label_size=14, label_wrap=190)
    # key for the three arrow styles, in the empty bottom-left cell of the loop
    ky = yb + 14
    for i, (col_, dash_, lab) in enumerate(((k, "solid", "next step"), ("#2b8a3e", "dashed", "iterate with the next version"), ("#6741d9", "dashed", "optimizer candidate becomes a version"))):
        yy = ky + i * 40
        arrow(cv, [(cx_(0) + 10, yy + 12), (cx_(0) + 90, yy + 12)], color=col_, sw=3, dash=dash_, end_head="arrow")
        cv.text(cx_(0) + 106, yy, lab, size=15, color=INK)
    left_bottom = yb + NH + 18 + 46

    rx, rw = LW + G, S(2)
    c1 = card(rw, "Save changes as versions", [
        "Versions are immutable; unsaved playground edits are lost if you leave the portal",
        "Compare the setup, the chat output and the YAML across versions",
        "Saving is required for conversation history, monitoring and full evaluations",
        "In code, reference an agent as <agent_name>:<version>",
    ], theme="green", icon="versions", src=src("life"))
    c1.place(cv, rx, top)
    c2 = card(rw, "Code habits the page recommends", [
        "Agent names cannot change after creation",
        "Create the agent once and reuse it: prefer get-or-create over blind create",
        "Treat a 404 as terminal: the agent was deleted",
        "A tool must be configured successfully before the agent can be saved with it",
    ], theme="gray", icon="learn", src=src("life"))
    c2.place(cv, rx, c1.bottom + 24)
    ny = max(left_bottom, c2.bottom) + 30
    n1 = Note(S(2), "The overview lists a 7-step lifecycle (Create, Test, Trace, Evaluate, Optimize, Publish, Monitor); the lifecycle page lists the 9 drawn here. Same loop, finer grain.",
              kind="key", title="Seven steps or nine?", src=src("ov", "life"))
    n2 = Note(S(2), "The lifecycle page says the agent optimizer is for hosted agents; the overview and the prompt-agent quickstart cover prompt agents too. The lifecycle page also still says "
                    "'agent applications' for publishing - read that as the stable agent endpoint.", kind="warn", title="Docs disagree: optimizer scope and wording", src=src("life", "ovo"))
    n3 = Note(S(2), "A separate AgentOps canvas covers the whole loop across environments, CI/CD gates, RACI and FinOps. This canvas stays on what is specific to building and improving one agent.",
              kind="info", title="Where the wider story lives")
    row(cv, 0, ny, [n1, n2, n3], gap=G)
    return ny + max(n1.h, n2.h, n3.h)


# ================================================================================================ band 2: local toolbelt
def band_toolbelt(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  The local toolbelt: run, inspect and debug before the cloud",
             "The Azure Developer CLI (azd) with the Foundry extension drives the whole workflow from scaffold to evaluation; the Inspector, doctor and VS Code Toolkit make local runs visible.")
    top = y
    GP = 64
    bw = (W - 6 * GP) / 7
    flow = [
        ("1  Install", "azd 1.36.0 or later for the current extension set; azd ext install microsoft.foundry", "azd", "gray"),
        ("2  Scaffold", "azd ai agent init - prompt, hosted or voice agents", "agent", "green"),
        ("3  Define", "azure.yaml describes the agent and its resources", "files", "gray"),
        ("4  Develop", "azd ai agent run; azd ai agent invoke --local", "code", "green"),
        ("5  Deploy", "azd up or azd deploy", "builds", "green"),
        ("6  Operate", "azd ai agent monitor, versions, automation", "dashboard", "violet"),
        ("7  Evaluate", "azd ai agent eval (quick) and azd ai eval (project)", "metrics", "violet"),
    ]
    boxes = [Box(bw, lab, sub=sub, theme=th, h=170, size=19, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=32) for lab, sub, ic, th in flow]
    row(cv, 0, top, boxes, gap=GP)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#343a40")
    cy = boxes[0].bottom + 24
    cv.text(0, cy, "Resource groups:", size=16, color=MUTED)
    cf = ChipFlow([Chip(t, theme="gray", size=15, fill="soft") for t in ("azd ai connection", "azd ai toolbox", "azd ai skill", "azd ai routine", "azd ai project", "azd ai agent add")],
                  1500, gap=10)
    cf.place(cv, 170, cy - 6)
    cv.text(1750, cy, "Learn: Agent development with the Azure Developer CLI", size=12, color=LINK, link=U["cli"][1])
    y2 = max(cf.y + cf.h, cy + 24) + 36

    # ---- local-run topology: what each local command touches
    MW = 1760
    with cv.panel(0, y2, title="Your machine: run, inspect, debug", sub="what azd ai agent run, invoke --local and doctor touch", theme="gray", style="dotted", pad=20,
                  title_size=22, sub_size=14, w=MW, min_h=380) as pm:
        r1y = pm.iy + 4
        r2y = r1y + 120 + 96
        run = Box(360, "azd ai agent run", sub="starts the agent locally and opens the Agent Inspector", theme="green", h=120, size=19, sub_size=13, fill="hatch", icon="azd",
                  icon_pos="left", icon_size=30)
        ag = Box(340, "Your agent", sub="listens on port 8088", theme="green", h=120, size=19, sub_size=13, fill="hatch", icon="agent", icon_pos="left", icon_size=30)
        ins = Box(380, "Agent Inspector", sub="UI on port 8087: replay requests; in VS Code, debugger and workflow visualization", theme="violet", h=120, size=19, sub_size=13,
                  fill="hatch", icon="browser", icon_pos="left", icon_size=30)
        inv = Box(340, "azd ai agent invoke --local", sub="send one request from your shell", theme="green", h=120, size=18, sub_size=13, fill="hatch", icon="code",
                  icon_pos="left", icon_size=30)
        doc = Box(380, "azd ai agent doctor", sub="read-only checks, local and remote; exit codes 0, 1 and 2", theme="green", h=120, size=19, sub_size=13, fill="hatch",
                  icon="diagnostics", icon_pos="left", icon_size=30)
        run.place(cv, pm.ix, r1y)
        ag.place(cv, pm.ix + 550, r1y)
        ins.place(cv, pm.ix + 1080, r1y)
        inv.place(cv, ag.x, r2y)
        doc.place(cv, ins.x, r2y)
        connect(cv, run, ag, sw=3, color="#2b8a3e", label="starts it", label_size=14)
        connect(cv, ins, ag, sw=3, color="#6741d9", label="replay requests", label_size=14)
        connect(cv, inv, ag, a_side="top", b_side="bottom", sw=3, color="#2b8a3e", label="one request", label_size=14)
    badge_on(cv, ins, "preview")
    badge_on(cv, doc, "preview")
    RX_ = MW + 150
    with cv.panel(RX_, y2, title="Foundry project", sub="remote", theme="green", style="dotted", pad=20, title_size=22, sub_size=14, w=S(4) - RX_, min_h=pm.h) as pr_:
        rb = Box(S(4) - RX_ - 40, "Deployed agent and project settings", sub="what doctor inspects remotely", theme="green", h=120, size=18, sub_size=13, fill="hatch", icon="foundry",
                 icon_pos="left", icon_size=30)
        rb.place(cv, pr_.ix, r2y)
    connect(cv, doc, rb, sw=3, color="#2b8a3e", dash="dashed", label="remote checks", label_size=14)
    cite(cv, 0, pm.bottom + 6, src("insp", "doc"))
    y2 = pm.bottom + 56
    cs = [
        card(C, "Agent Inspector", [
            "Runs locally only: azd ai agent run opens it (UI on port 8087, your agent on 8088)",
            "Replay requests against the running agent",
            "In VS Code the Foundry Toolkit adds debugger integration and workflow visualization",
        ], theme="violet", icon="browser", badge="preview", src=src("insp")),
        card(C, "azd ai agent doctor", [
            "Read-only checks of your local setup and the remote project",
            "Exit codes 0, 1 and 2, so it is CI-friendly",
            "Preview: use it as a pre-deploy health check",
        ], theme="green", icon="diagnostics", badge="preview", src=src("doc")),
        card(C, "Foundry Toolkit for VS Code", [
            "Create from templates or with Copilot",
            "Debug with trace visualization; connect Toolboxes; deploy",
            "Agent Optimization scaffolds the optimizer integration for you",
            "GA per the Build 2026 blog (not on the Learn pages read)",
        ], theme="gray", icon="vscode", badge="GA (blog)", src=src("cli")),
        card(C, "Foundry Agent Canvas", [
            "A GitHub Copilot App extension: a side panel for creating, inspecting and deploying hosted agents",
            "The canvas surfaces choices; Copilot writes the code in your workspace",
            "See the 'Workflows, routines, A2A and multi-agent orchestration' canvases",
        ], theme="gray", icon="github", badge="preview", src=src("canvas")),
        card(C, "Coding-agent skill and chat command", [
            "A Microsoft Foundry skill for coding agents is linked from the CI/CD and memory quickstarts (the skill page itself was not read)",
            "VS Code Copilot Chat: /validate-microsoft-foundry-hosted-agent",
        ], theme="gray", icon="code", src=src("cdq")),
        card(C, "Debug a running agent", [
            "azd ai agent monitor, the log stream API, latency debug headers and Application Insights",
            "Tracing (Preview) shows tool calls, inputs, outputs and latency",
            "Details: 'Hosted agents: deploy and operate' and 'Tracing' canvases",
        ], theme="violet", icon="monitor", src=src("life")),
    ]
    _, b = row(cv, 0, y2, cs, gap=G)
    return b


# ================================================================================================ band 3: evaluation hooks
def band_eval(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Evaluation hooks: two CLI surfaces that look alike and are not interchangeable",
             "Run an evaluation before you publish and after any meaningful change. Evaluation is Preview; the optimizer reuses the quick-evaluation config.")
    top = y
    PW = S(3)
    with cv.panel(0, top, title="Quick evaluation", sub="azd ai agent eval ...  +  a local eval.yaml", theme="violet", style="solid", fill="soft", pad=22, title_size=26, sub_size=16,
                  w=PW) as pq:
        cf = ChipFlow([Chip(t, theme="violet", size=15) for t in ("eval generate", "eval init", "eval update", "eval run")], PW - 44, gap=10)
        cf.place(cv, pq.ix, pq.iy + 4)
        by_ = bullets(cv, pq.ix, cf.y + cf.h + 18, PW - 44, [
            "Config: eval.yaml in the agent project - the same file also feeds the agent optimizer",
            "eval generate produces a dataset and evaluators from the agent's instructions",
            "Edit rubric_dimensions.json, then run eval update",
            "Best for fast checks while you develop",
        ], "violet")
        cite(cv, pq.ix, by_ + 10, src("cli"))
    with cv.panel(PW + G, top, title="Project evaluation", sub="azd ai eval (separate extension)  +  evals/azure.eval.yaml", theme="grape", style="solid", fill="soft", pad=22, title_size=26,
                  sub_size=16, w=PW, min_h=pq.h) as pp:
        cf2 = ChipFlow([Chip(t, theme="grape", size=15) for t in ("azd ai eval run start", "--fail-on pass-rate=0.8", "trace sources", "dataset sources")], PW - 44, gap=10)
        cf2.place(cv, pp.ix, pp.iy + 4)
        by2 = bullets(cv, pp.ix, cf2.y + cf2.h + 18, PW - 44, [
            "Config: evals/azure.eval.yaml - trace and dataset sources plus CI quality gates",
            "azd ai eval run start --fail-on pass-rate=0.8 fails the pipeline below the bar",
            "The extension is installed separately from the core Foundry extension",
            "Best for CI gates and project-level evaluation",
        ], "grape")
        cite(cv, pp.ix, by2 + 10, src("cli", "cicd"))
    nn = Note(W, "eval.yaml (quick evaluation, also used by the optimizer) and evals/azure.eval.yaml (project evaluation) are different formats read by different extensions: "
                 "the config files are not interchangeable. Pick the surface first, then write its file.", kind="gotcha", title="The two config files are not interchangeable",
              src=src("cli", "cicd"))
    nn.place(cv, 0, max(pq.bottom, pp.bottom) + 26)
    y2 = nn.bottom + 26
    nw = (W - 3 * G) / 4
    cs = [
        Note(nw, "Run before publishing and after any meaningful change. Saving versions is required for monitoring and full evaluations.", kind="key", title="When to run", src=src("life")),
        Note(nw, "Trace-based evaluation of an external agent requires registering it with gen_ai.agent.id (see the 'Tracing' and 'Foundry Agent Service: the map' canvases).", kind="info",
             title="External agents"),
        Note(nw, "Voice agents are evaluated with transcript-only evaluators (see the 'Voice agents' canvases).", kind="info", title="Voice agents"),
        Note(nw, "Agent evaluators include intent resolution, task adherence and tool-call accuracy (see 'Evaluation in depth').", kind="info", title="Agent evaluators", src=src("aeval")),
    ]
    _, b = row(cv, 0, y2, cs, gap=G)
    return b


# ================================================================================================ band 4: optimizer at a glance
def band_optimizer(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  The agent optimizer (Preview) at a glance",
             "It automatically improves prompt agents and hosted agents: evaluate the baseline, generate candidates, evaluate them, rank by a 0.0 to 1.0 score. Part 2 has the commands, files, datasets, costs, REST, the Prompt Optimizer (with its 15 regions) and the CI/CD template.")
    top = y
    FW = S(3)
    fb = (FW - 3 * 70) / 4
    steps = [
        Box(fb, "1  Evaluate the baseline", sub="invoke your agent on every task in a dataset and score each response", theme="violet", h=150, size=18, sub_size=13, fill="hatch", icon="metrics",
            icon_pos="top", icon_size=30),
        Box(fb, "2  Generate candidates", sub="rewritten instructions, discovered skills, better tool descriptions, other models - guided by failures", theme="violet", h=150, size=18, sub_size=13,
            fill="hatch", icon="gear", icon_pos="top", icon_size=30),
        Box(fb, "3  Evaluate candidates", sub="test each candidate against the same dataset", theme="violet", h=150, size=18, sub_size=13, fill="hatch", icon="metrics", icon_pos="top", icon_size=30),
        Box(fb, "4  Rank and recommend", sub="composite score 0.0 to 1.0; the best candidate gets a star", theme="green", h=150, size=18, sub_size=13, fill="hatch", icon="agent", icon_pos="top", icon_size=30),
    ]
    row(cv, 0, top, steps, gap=70)
    for a, b in zip(steps, steps[1:]):
        connect(cv, a, b, sw=3, color="#6741d9")
    wy = steps[0].bottom + 22
    n1 = Note(FW, "The whole run happens in the cloud, and its length depends on dataset size, number of candidates and models. The optimizer proposes: you apply and deploy the winner "
                   "(hosted) or promote it to a new version (prompt agents).", kind="info", title="Closed loop, cloud job", src=src("ovo"))
    n1.place(cv, 0, wy)
    n2 = Note(FW, "During evaluation the optimizer invokes your agent for every task. If the agent calls APIs, databases or third-party services, those calls execute each time: charges, state changes "
                  "and rate limits are real. Use test endpoints or mocks.", kind="gotcha", title="Tool calls are real", src=src("ovo"))
    n2.place(cv, 0, n1.bottom + 20)

    rx = FW + G
    tg = [
        card((FW - G) / 2, "Instruction tuning", [
            "Rewrites and refines the system prompt to score higher",
            "Hosted: activates when the baseline has instructions.md; prompt agents: the selected version is the baseline",
        ], theme="violet", icon="files"),
        card((FW - G) / 2, "Skill improvement (hosted only)", [
            "Refines the body of each reusable skill while keeping its purpose",
            "Activates with skills/<name>/SKILL.md (the open Agent Skills format); the optimizer can also discover and create skills",
        ], theme="violet", icon="toolbox"),
        card((FW - G) / 2, "Tool optimization", [
            "Improves function-calling tool and parameter descriptions - not names, types, defaults or required fields",
            "Hosted: needs tools.json. Prompt agents: client-side tools, so execution is not evaluated",
        ], theme="orange", icon="toolbox"),
        card((FW - G) / 2, "Model selection", [
            "Evaluates the agent across several deployments for the best quality-to-cost trade-off",
            "Hosted: model_search_space in eval.yaml (the current model is removed automatically); prompt agents: Compare across models in the wizard",
        ], theme="blue", icon="openai"),
    ]
    _, b = row(cv, rx, top, tg[:2], gap=G)
    _, b2 = row(cv, rx, b + 24, tg[2:], gap=G)
    cv.text(rx, b2 + 12, "Targets activate automatically from the baseline files you provide.  Learn: Agent optimizer overview", size=12, color=LINK, link=U["ovo"][1])
    y2 = max(n2.bottom, b2 + 36) + 36

    t1 = Table([("", 220), ("Prompt agent", 780), ("Hosted agent", 776)], [
        [ct("Start a run", "violet"), "Portal Optimize tab wizard; no code changes. Not for agents that use the Microsoft Copilot harness", "Foundry Toolkit (scaffolds the integration) or azd after making the agent optimizer-ready"],
        [ct("Targets", "violet"), "Instructions, function-tool descriptions, model", "Instructions, skills, function-tool descriptions, model"],
        [ct("Cost view", "yellow"), "Pre-run estimate in the portal (minimum, estimated, maximum), then measured token usage", "Measured token usage after the run; no pre-run estimate"],
        [ct("Needs", "red"), "A dataset: generate from traces, pick a registered one or upload JSONL", "Responses protocol; all hosted regions except Norway East; JSONL or a registered dataset"],
        [ct("Apply", "green"), "Promote a candidate: it becomes a new prompt-agent version", "optimize apply, review, then azd deploy (or optimize deploy)"],
    ], w=FW, theme="violet", size=14, head_size=15, title="Prompt agents vs hosted agents (as of 2026-11-03)", title_size=20)
    t1.place(cv, 0, y2)
    t2 = Table([("Model", 230), ("Role", 640), ("Allowed", 856)], [
        [ct("Eval model", "violet"), "Scores each response against the criteria: a binary score per evaluator, task and candidate (--eval-model)",
         "Any chat-completion deployment, for example gpt-4.1-mini"],
        [ct("Optimization model", "violet"), "Required. Generates candidates across the targets (--optimize-model); a stronger model usually proposes better ones",
         "gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, DeepSeek-V4-Pro, DeepSeek-V-3.2"],
    ], w=FW, theme="violet", size=14, head_size=15, title="Two models, both deployed in the project", title_size=20)
    t2.place(cv, FW + G, y2)
    y3 = max(t1.bottom, t2.bottom) + 36
    cv.text(0, y3, "How to read the score: each evaluator is rescaled to 0-1 (flipped if lower is better), then averaged. If every candidate scores below the baseline, keep the baseline.", size=17, color=INK)
    by = y3 + 40
    segs = [("below 0.03: noise", 0.22, "gray"), ("0.03 to 0.10: moderate, worth deploying", 0.26, "green"), ("0.10 to 0.20: significant", 0.26, "teal"), ("above 0.20: major, likely a weak baseline", 0.26, "orange")]
    cx = 0.0
    for lab, frac, th_name in segs:
        th = THEMES[th_name]
        sw_ = W * frac
        cv.rect(cx, by, sw_, 54, stroke=th.stroke, fill=th.fill, style="solid", sw=2, round_=False, rough=0)
        tw, thh = text_size(lab, 17)
        cv.text(cx + (sw_ - tw) / 2, by + (54 - thh) / 2, lab, size=17, color=th.deep)
        cx += sw_
    wy2 = by + 54 + 22
    cv.text(0, wy2, "Six steps for both kinds:", size=16, color=MUTED)
    cf = ChipFlow([Chip(t, theme="violet", size=16) for t in ("1 Select the baseline", "2 Dataset", "3 Evaluation criteria", "4 Run", "5 Review", "6 Apply")], 2400, gap=12)
    cf.place(cv, 240, wy2 - 6)
    cv.text(2700, wy2, "Learn: Agent optimizer overview", size=12, color=LINK, link=U["ovo"][1])
    return cf.y + cf.h


# ================================================================================================ band 5: release pipeline
def band_release(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Releasing a new version: from commit to production and back",
             "Agent-specific view of the release path. The environment strategy, gates, RACI and FinOps are on the AgentOps canvases; the deploy mechanics are on 'Hosted agents: deploy and operate'.")
    top = y
    GP = 64
    bw = (W - 6 * GP) / 7
    flow = [
        ("Branch push", "a push triggers the pipeline azd pipeline config set up; the branch maps to an environment", "branch", "gray"),
        ("Pin production", "the endpoint follows the latest version by default: pin production before you deploy", "versions", "green"),
        ("Deploy the candidate", "a new version is created; pinned production traffic does not change", "builds", "green"),
        ("Test session", "a version-pinned session against the candidate", "browser", "green"),
        ("Evaluation gate", "azd ai eval run start --fail-on pass-rate=0.8", "metrics", "violet"),
        ("Promote", "move the version selector to the candidate; promote separately from deploy", "agent", "green"),
        ("Monitor and roll back", "watch the promoted version; rollback restores the previous selector", "dashboard", "violet"),
    ]
    boxes = [Box(bw, f"{i + 1}  {lab}", sub=sub, theme=th, h=180, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for i, (lab, sub, ic, th) in enumerate(flow)]
    row(cv, 0, top, boxes, gap=GP)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#343a40")
    connect(cv, boxes[6], boxes[5], a_side="bottom", b_side="bottom", route="elbow", sw=2, color="#c92a2a", dash="dashed",
            via=[(boxes[6].cx, boxes[6].bottom + 40), (boxes[5].cx, boxes[5].bottom + 40)], label="rollback", label_size=14, label_pos="below")
    y2 = boxes[0].bottom + 80
    c1 = card(S(2), "Pipeline set-up in one card", [
        "azd pipeline config wires GitHub Actions or Azure DevOps, with Bicep or Terraform (--infra); Terraform keeps remote state",
        "Secrets and variables: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_ENV_NAME, AZURE_LOCATION",
        "The workflow identity needs Foundry User and Contributor on the target project (container deploy needs more ACR permissions)",
    ], theme="yellow", icon="devops", badge="preview", src=src("cicd", "cdq"))
    c2 = card(S(2), "The optimizer joins the same path", [
        "optimize apply downloads the winning candidate to .agent_configs/<id>/ for a hosted agent",
        "Review the diff, then azd deploy - or feed the change into the same pipeline: evaluation gate, deploy, test session, promote",
        "optimize deploy skips local files: fine to try, but use apply then deploy for production",
    ], theme="violet", icon="gear", badge="preview", src=src("tg"))
    n = Note(S(2), "The configure, manage and hosted-agents pages say there is no traffic splitting: one version at 100%. The production-deploy page documents 90/10, 50/50 and 100/0 canary steps, and "
                   "REST exposes FixedRatio rules with traffic_percentage. Treat splitting as unconfirmed.", kind="warn", title="Docs disagree: traffic splitting", src=src("prod"))
    row(cv, 0, y2, [c1, c2, n], gap=G)
    return y2 + max(c1.h, c2.h, n.h)


# ================================================================================================ band 6: what to use when
def band_use(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  What to use when", "Pick the tool by the job. Status is as of 2026-11-03; 'GA (blog)' means the status comes from a Foundry blog post, not from a Learn page.")
    PRE, GAB = ("Preview", "orange"), ("GA (blog)", "green")
    t = Table([("The job", 760), ("Use", 1240), ("Where it runs", 440), ("Status", 240), ("Watch out for", 920)], [
        ["Run an agent locally and replay requests", "azd ai agent run, then the Agent Inspector (UI on port 8087, agent on 8088)", "Your machine", PRE, "Local only"],
        ["Call the local agent once from a script", "azd ai agent invoke --local", "Your machine", "", "Part of the develop step"],
        ["Check the setup before a deploy or in CI", "azd ai agent doctor", "Local and remote, read-only", PRE, "Exit codes 0, 1 and 2"],
        ["Build, debug with traces, deploy and optimize from VS Code", "Foundry Toolkit for VS Code", "Your machine", GAB, "Status from the Build 2026 blog"],
        ["Create a hosted agent with Copilot in a side panel", "Foundry Agent Canvas (GitHub Copilot App extension)", "GitHub Copilot App", PRE, "Hosted agents; separate from the harness"],
        ["A fast quality check of one agent", "azd ai agent eval with a local eval.yaml", "CLI", PRE, "The same eval.yaml feeds the optimizer"],
        ["Quality gates in CI", "azd ai eval run start --fail-on pass-rate=0.8 with evals/azure.eval.yaml", "CI pipeline", PRE, "A different extension and file format"],
        ["Automatically improve a hosted agent", "azd ai agent optimize, or the Toolkit, after making the agent optimizer-ready", "Cloud job you start", PRE, "Responses protocol; not in Norway East; tools run for real"],
        ["Improve a prompt agent without code", "Portal: agent, Optimize tab, wizard", "Portal", PRE, "Not for Copilot-harness agents; tool execution not evaluated"],
        ["Rewrite instruction text only", "Prompt Optimizer: the pencil-and-sparkle icon on Instructions", "Portal playground", "", "Ephemeral: select Use prompt before you close; 15 regions (listed in part 2)"],
        ["Ship from a branch with checks", "azd pipeline config with GitHub Actions or Azure DevOps", "CI pipeline", PRE, "Pin production before you deploy"],
        ["Roll out a version safely and roll back", "Pin, deploy a candidate, test in a version-pinned session, promote the selector", "Agent endpoint", PRE, "Docs disagree on traffic splitting"],
        ["Debug a running agent", "azd ai agent monitor, log stream, latency debug headers, Application Insights", "Cloud", "", "See 'Hosted agents: deploy and operate'"],
    ], w=W, theme="gray", size=14, head_size=15, first_col_theme="gray", title="Job to tool", title_size=22)
    t.place(cv, 0, y)
    return t.bottom


# ================================================================================================ band 7: docs disagree
def band_disagree(cv: Canvas, y: float) -> float:
    y = head(cv, y, "7  Docs disagree and what to double-check - as of 2026-11-03",
             "Where two Learn pages (or Learn and a blog) give different answers, both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 1100), ("Another source says", 1100), ("How to read it", 1100)], [
        [ct("Optimizer scope", "orange"), "Lifecycle page: optimize hosted agents", "Optimizer overview and the prompt-agent quickstart: prompt agents and hosted agents", "Read the overview as current: both kinds, different setups"],
        [ct("max_candidates default", "orange"), "eval.yaml documentation: the default is 5", "REST schema: candidate_search_configuration.max_candidates defaults to 1", "Set it explicitly in whichever surface you use"],
        [ct("Optimization goal", "orange"), "The REST agent_optimization goal lists only improve_quality", "The overview lists four targets: instructions, skills, tool descriptions and model selection",
         "In REST, goal and target_attributes are separate fields; only one goal is documented"],
        [ct("Publish wording", "orange"), "The lifecycle page says publish an 'agent application'", "Agent Service now gives every agent a stable endpoint and identity at creation", "Use stable-endpoint language; see 'Publishing and channels'"],
        [ct("Toolkit status", "orange"), "A Build 2026 blog (not Learn) says the Foundry Toolkit for VS Code is generally available", "Most Learn Toolkit pages were not read for this canvas, so a Learn GA statement is unconfirmed",
         "Treat GA as blog-sourced; check the live Toolkit page"],
        [ct("Traffic splitting", "orange"), "Configure, manage and hosted-agents pages: no splitting, one version at 100%", "Production-deploy page: 90/10, 50/50, 100/0 canary with azd ai agent endpoint update", "Treat splitting as unconfirmed"],
    ], w=W, theme="orange", size=14, head_size=15, title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    q = Note(W, "Not stated on the pages read for this canvas: Agent Inspector and doctor behaviors beyond what is drawn, how the Foundry skill for coding agents works (its page was not read), "
                "and any price for optimizer runs beyond the token estimates in part 2. Nothing on this canvas fills those gaps.", kind="quote", title="What the docs do not say",
             src=src("insp", "doc", "costs"))
    q.place(cv, 0, t.bottom + 30)
    return q.bottom


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Agent lifecycle and the optimizer",
        "Build -> test -> trace -> evaluate -> optimize -> ship -> monitor: local tools, evaluation hooks, the agent optimizer (Preview) and release promotion  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Tools and MCP", "orange"), ("Evaluation and optimizer", "violet"), ("Models", "blue"), ("Identity and security", "red"),
                           ("CI/CD and cost", "yellow"), ("Governance", "grape"), ("Local tooling and neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Hosted agents: deploy and operate", "AgentOps lifecycle", "Evaluation in depth", "Tracing: from agent run to the Traces UI",
                "Prompt agents: harness, A2A, routines and migration", "Publishing and channels: endpoint, Microsoft 365, Teams and identity"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_loop(cv, y) + 56
    y = band_toolbelt(cv, y) + 56
    y = band_eval(cv, y) + 56
    y = band_optimizer(cv, y) + 56
    y = band_release(cv, y) + 56
    y = band_use(cv, y) + 56
    y = band_disagree(cv, y) + 56
    sources(cv, 0, y, [
        ("Agent development lifecycle", U["life"][1]), ("Agent development with the Azure Developer CLI", U["cli"][1]), ("Agent Inspector", U["insp"][1]), ("azd ai agent doctor", U["doc"][1]),
        ("Agent optimizer overview", U["ovo"][1]), ("Make your agent optimizer-ready", U["ready"][1]),
        ("Optimize agent instructions, skills, tools and models", U["tg"][1]), ("Quickstart: optimize a hosted agent", U["qh"][1]),
        ("Quickstart: optimize a prompt agent", U["qp"][1]), ("Optimize agent prompts with Prompt Optimizer", U["po"][1]), ("Set up CI/CD for hosted agents with azd", U["cicd"][1]),
        ("Promote hosted agents to production with azd", U["prod"][1]), ("Microsoft Foundry Canvas", U["canvas"][1]),
        ("REST: create an agent optimization job", U["rest"][1]),
    ], w=W, cols=4)
