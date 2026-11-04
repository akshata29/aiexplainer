"""Ways to build on Microsoft Foundry (part 2 of 2): each surface in detail - portal and playgrounds, VS Code Foundry Toolkit, Foundry Canvas,
azd ai extensions and the DevPack, REST v1 and ARM, coding agents with the Foundry Skill and the Foundry MCP Server tool list, LangChain,
templates and samples (as of 2026-11-03)."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="developer-surfaces-part-2", title="Developer surfaces in detail", section="1", group="Overview", order=6.5,
    description="Each way in, in detail: portal and playgrounds, VS Code Foundry Toolkit, Canvas, azd ai extensions and the DevPack, REST v1 and ARM, the Foundry "
                "Skill and all 79 Foundry MCP Server tools, LangChain, templates and samples.",
    tags=["azd", "mcp-server", "rest", "vscode", "templates", "devpack"],
)

W = 3000

# ------------------------------------------------------------------------------------------------ sources
SDK = learn("how-to/develop/sdk-overview")
INSTALL = learn("how-to/develop/install-cli-sdk")
AZD = learn("agents/concepts/cli-agent-development")
AZD_EXT = learn("agents/how-to/install-cli-foundry-extensions")
AZD_CODING = learn("agents/how-to/use-cli-with-coding-agents")
VSCODE = learn("how-to/develop/get-started-projects-visual-studio-code")
VSCODE_INSTALL = learn("how-to/develop/install-foundry-toolkit-visual-studio-code")
INSPECTOR = learn("how-to/develop/vs-code-agent-inspector")
VSTRACE = learn("how-to/develop/vs-code-tracing")
SKILL = learn("how-to/develop/use-microsoft-foundry-skill")
MCP = learn("mcp/get-started")
MCP_TOOLS = learn("mcp/available-tools")
MCP_SEC = learn("mcp/security-best-practices")
CANVAS = learn("agents/concepts/foundry-canvas")
LANGCHAIN = learn("how-to/develop/langchain")
PLAYGROUNDS = learn("concepts/concept-playgrounds")
NAV = learn("how-to/navigate-from-classic")
AUTH = learn("concepts/authentication-authorization-foundry")
ENDPOINTS = learn("foundry-models/concepts/endpoints")
CONFIGURE_AGENT = learn("agents/how-to/configure-agent")
HOSTED = learn("agents/concepts/hosted-agents")
TEMPLATE = learn("how-to/develop/ai-template-get-started")
HOSTED_QS = learn("agents/quickstarts/quickstart-hosted-agent")
REST_REF = learn("rest/api/microsoft-foundry/?view=rest-microsoft-foundry-v1", base="")
ARM = learn("azure/templates/microsoft.cognitiveservices/accounts", base="")
SAMPLES = "https://github.com/microsoft-foundry/foundry-samples"
DEVPACK_BLOG = "https://devblogs.microsoft.com/foundry/foundry-devpack-announcement/"
JULAUG_BLOG = "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-july-august-2026/"


# ================================================================================================ local helpers
def sticker(cv, x, y, text, th="red", size=14):
    """Small solid pill drawn on a card edge (not registered, so it does not trigger overlap warnings)."""
    t = theme(th)
    tw = metrics.line_width(text, size) + 20
    with cv.group():
        cv.rect(x, y, tw, size * 1.25 + 8, stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0)
        cv.text(x + 10, y + 4, text, size=size, color=t.deep)
    return tw


def block_arrow(cv, x, y, w, h, text, *, th="blue", size=17, tip=30, notch=False, sub=None, sub_size=14, sub_font=None):
    """Chevron-style block arrow with centred text; notch=True gives the 'follows another chevron' shape."""
    t = theme(th)
    pts = [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h)]
    if notch:
        pts.append((x + tip, y + h / 2))
    pts.append(pts[0])
    pad_l = (tip + 12) if notch else 16
    tw = w - tip - pad_l - 12
    lines = metrics.wrap_text(text, tw, size, sub_font or metrics.HAND)
    sub_lines = metrics.wrap_text(sub, tw, sub_size) if sub else []
    lh = metrics.line_ratio()
    th_h = len(lines) * size * lh + (len(sub_lines) * sub_size * lh + 3 if sub_lines else 0)
    with cv.group():
        cv.poly(pts, kind="line", stroke=t.stroke, fill=t.fill, fill_style="hachure", sw=2)
        ty = y + (h - th_h) / 2
        cv.text(x + pad_l, ty, "\n".join(lines), size=size, color=t.deep, align="center", w=tw, font=sub_font or metrics.HAND)
        if sub_lines:
            cv.text(x + pad_l, ty + len(lines) * size * lh + 3, "\n".join(sub_lines), size=sub_size, color=MUTED, align="center", w=tw)
    cv.register("chevron", x, y, w, h)


class CodeBox(Rect2):
    """Monospace command box: optional title, lines of str or (str, kind) where kind in cmd|note|out."""

    def __init__(self, w, lines, *, title=None, size=14, pad=14, th="gray", title_size=17, bg="#f8f9fa"):
        self.th = theme(th)
        self.w, self.size, self.pad, self.title_size, self.bg = w, size, pad, title_size, bg
        inner = (w - 2 * pad) * 0.965
        lm = metrics.line_ratio(metrics.MONO)
        y = pad
        self.t_lines = metrics.wrap_text(title, inner, title_size) if title else []
        if self.t_lines:
            y += len(self.t_lines) * title_size * metrics.line_ratio() + 6
        self.rows = []
        for ln in lines:
            text, kind = (ln, "cmd") if isinstance(ln, str) else ln
            size_ = size if kind != "note" else size - 1
            wrapped = metrics.wrap_text(text, inner, size_, metrics.MONO)
            self.rows.append((wrapped, kind, size_, y))
            y += len(wrapped) * size_ * lm + 5
        self.h = y - 5 + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        colors = {"cmd": "#1864ab", "note": "#868e96", "out": "#2b8a3e"}
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=self.bg, style="solid", sw=2)
            if self.t_lines:
                cv.text(x + pad, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            for wrapped, kind, size_, ry in self.rows:
                cv.text(x + pad, y + ry, "\n".join(wrapped), size=size_, color=colors[kind], font=metrics.MONO)
        cv.register("codebox", x, y, self.w, H)
        return self


def flow_row(cv, x, y, w, steps, th, *, h=110, size=16, tip=28, sub_size=14, mono_titles=False):
    """Horizontal chevron process: steps = [(title, sub)]; returns bottom y."""
    n, gap = len(steps), 6
    sw = (w - (n - 1) * gap) / n
    for i, (t, s) in enumerate(steps):
        block_arrow(cv, x + i * (sw + gap), y, sw, h, t, th=th, size=size, tip=tip, notch=i > 0, sub=s, sub_size=sub_size,
                    sub_font=metrics.MONO if mono_titles else None)
    return y + h


def learn_line(cv, x, y, items, size=12, gap=24):
    """Row of clickable 'Learn: ...' links; returns the bottom y."""
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * metrics.line_ratio()


def masonry(cv, x, y, cards, ncols, gap_x=24, gap_y=22):
    """Place cards in `ncols` equal columns, each next card going to the currently shortest column; returns bottom y."""
    heights = [0.0] * ncols
    cw = cards[0].w
    for c in cards:
        k = heights.index(min(heights))
        c.place(cv, x + k * (cw + gap_x), y + heights[k])
        heights[k] += c.h + gap_y
    return y + max(heights) - gap_y


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Developer surfaces in detail",
                                "Portal and playgrounds, VS Code, Canvas, azd and the DevPack, REST and ARM, coding agents with the Foundry MCP Server, LangChain, templates  |  "
                                "part 2 of 2  |  as of 2026-11-03", w=W)
    y = bottom + 26
    legend(cv, 0, y, [("Human surfaces", "green"), ("Code and frameworks", "indigo"), ("Terminal and infrastructure", "grape"), ("AI-assisted", "orange"),
                      ("Foundry resource", "blue"), ("Read tool (MCP)", "green"), ("Write tool (MCP)", "red"), ("Reference", "gray")])
    y += 54
    H = s_human(Canvas("measure"), 0, 0) - 100
    y = s_human(cv, y, H) + 90
    y = s_terminal(cv, y) + 90
    y = s_rest(cv, y) + 90
    y = s_assist(cv, y) + 90
    y = s_code(cv, y) + 70
    sources(cv, 0, y, [
        ("Playgrounds and quick evaluation", PLAYGROUNDS),
        ("Foundry Toolkit for VS Code overview", VSCODE),
        ("Install Foundry Toolkit for VS Code", VSCODE_INSTALL),
        ("Debug agents with Agent Inspector", INSPECTOR),
        ("Collect and inspect traces in VS Code", VSTRACE),
        ("What is Microsoft Foundry Canvas?", CANVAS),
        ("Develop agents with the Azure Developer CLI", AZD),
        ("Install the azd Foundry extensions", AZD_EXT),
        ("Use the azd CLI with coding agents", AZD_CODING),
        ("Prepare your development environment (DevPack)", INSTALL),
        ("Foundry SDKs and endpoints", SDK),
        ("Foundry REST API reference (v1)", REST_REF),
        ("Configure an agent endpoint (protocols, authorization)", CONFIGURE_AGENT),
        ("Use the Microsoft Foundry Skill in coding agents", SKILL),
        ("Foundry MCP Server: get started", MCP),
        ("Foundry MCP Server: available tools", MCP_TOOLS),
        ("Foundry MCP Server: security best practices", MCP_SEC),
        ("LangChain and LangGraph with Foundry", LANGCHAIN),
        ("Get started with an AI template", TEMPLATE),
        ("Microsoft.CognitiveServices/accounts template reference", ARM),
    ], w=W, cols=3)


# ================================================================================================ 1. human surfaces
def s_human(cv: Canvas, y: float, H: float = 0) -> float:
    section_header(cv, 0, y, "Human surfaces: portal and playgrounds, VS Code Foundry Toolkit, Foundry Canvas", w=W,
                   sub="Learn: Playgrounds and quick evaluation; Foundry Toolkit for VS Code; What is Microsoft Foundry Canvas?  |  'preview' as labelled on Learn, as of 2026-11-03")
    top = y + 100
    WA, WB, WC, G = 990, 990, 880, 70
    XA, XB, XC = 0, WA + G, WA + G + WB + G
    pad = 22

    # ---------------------------------------------------------------- A: portal
    with cv.panel(XA, top, w=WA, min_h=H, title="Foundry portal and playgrounds", sub="ai.azure.com  |  no code needed", theme="green", style="dashed", fill="soft", pad=pad,
                  title_size=26, sub_size=15) as pa:
        iw = WA - 2 * pad
        c1 = Card(iw, "Explore, prototype, build prompt agents", [
            "The New Foundry toggle in the banner switches between the new and classic portals",
            "Six top-level sections: Home, Discover, Build, Operate, Manage and Docs",
            "Discover: model catalog, benchmarks, solution templates, agent templates and tools",
            "Build > Create: Agents, Models, Services, Tools, Knowledge, Memory, Guardrails, Data; Optimize: Evaluations, Fine-tune",
            "'Open in VS Code (for the Web)' in a playground imports the endpoint and key into a workspace",
        ], theme="green", icon="foundry", body_size=15, title_size=20, pad=14, src=[("Migrate from the classic portal (portal map)", NAV), ("Playgrounds", PLAYGROUNDS)])
        c1.place(cv, pa.ix, pa.iy)
        ST = lambda t, th: dict(text=t, theme=th, align="center")
        tbl = Table([("Playground", 210), ("What you can do", 560), ("Status", 120)], [
            ["Model playground", "Compare up to 3 models, system prompts, tools (web search, file search, code interpreter), safety guardrails, code export", ST("GA", "green")],
            ["Agents playground", "Tools, knowledge, memory, tracing and evaluation for an agent", ST("GA", "green")],
            ["Images playground 2.0", "gpt-image-1, gpt-image-2, FLUX.1-Kontext-pro: text-to-image, inpainting", ST("GA", "green")],
            ["Video playground", "Sora-2", ST("Preview", "orange")],
            ["Audio playground", "Not in the new portal", ST("Classic", "gray")],
            ["AI services (Speech ...)", "Playgrounds for Foundry Tools", ST("GA", "green")],
        ], w=iw, theme="green", size=14, head_size=15, pad_y=6, title="Playgrounds", title_size=20, align=["left", "left", "center"])
        tbl.place(cv, pa.ix, c1.bottom + 24)
        roles = Table([("Role in the portal", 280), "What it lets you do"], [
            [("Foundry User", "green"), "Build with pre-deployed models on the project (day-to-day development)"],
            [("Foundry Project Manager", "green"), "Publish or deploy hosted agents and create connections"],
            [("Foundry Account Owner", "green"), "Create the Foundry resource and projects"],
        ], w=iw, theme="green", size=14, head_size=15, pad_y=6, title="Roles (formerly Azure AI User, Project Manager, Account Owner)", title_size=18)
        roles.place(cv, pa.ix, tbl.bottom + 22)
        learn_line(cv, pa.ix, roles.bottom + 8, [("Foundry SDKs (prerequisite roles)", SDK)])

    # ---------------------------------------------------------------- B: VS Code
    with cv.panel(XB, top, w=WB, min_h=H, title="VS Code: Microsoft Foundry Toolkit", sub="the new name for AI Toolkit  |  some experiences are preview", theme="green", style="dashed",
                  fill="soft", pad=pad, title_size=26, sub_size=15) as pb:
        iw = WB - 2 * pad
        c1 = Card(iw, "One extension for local and Foundry resources", [
            "Also includes the capabilities of the separate Microsoft Foundry extension; install from aka.ms/foundrytk (needs VS Code and the .NET Runtime)",
            "Models: Model Catalog (Foundry, external, local ONNX, Ollama, Foundry Local), Model Playground, convert, quantize, optimize, evaluate and fine-tune "
            "(local GPU or Azure Container Apps)",
            "Declarative workflows: inspect and migrate only; Workflows retire on 2026-12-01",
        ], theme="green", icon="vscode", body_size=15, title_size=20, pad=14, src=[("Foundry Toolkit overview", VSCODE), ("Install Foundry Toolkit", VSCODE_INSTALL)])
        c1.place(cv, pb.ix, pb.iy)
        bw = (iw - 2 * 14) / 3
        secs = [Box(bw, "My Resources", sub="models, agents, tools, knowledge, evaluations, local and project resources", theme="green", fill="solid", size=17, sub_size=13, min_h=108),
                Box(bw, "Developer Tools", sub="discover, build, debug, deploy, test, evaluate, monitor", theme="green", fill="solid", size=17, sub_size=13, min_h=108),
                Box(bw, "Help And Feedback", sub="ask Copilot, docs, release notes, issues, community", theme="green", fill="solid", size=17, sub_size=13, min_h=108)]
        row(cv, pb.ix, c1.bottom + 20, secs, gap=14)
        fy = c1.bottom + 20 + secs[0].h + 22
        cv.text(pb.ix, fy, "Build and run an agent in the editor", size=19, color=theme("green").deep)
        fy += 30
        steps = [
            ("Agent Builder", "Prompt agents: test conversations, save versions, generate client code; the Tool Catalog adds Foundry tools, MCP servers and toolboxes", "agent"),
            ("Agent Inspector", "Debug local agents: streaming responses, tool calls, workflow execution (the Responses protocol is the main path)", "bug"),
            ("Deploy hosted agents", "To Foundry Agent Service from source code or a container image", "container-apps"),
            ("Hosted Agent Playground", "Test the deployed agent, inspect logs and traces, manage versions", "browser"),
            ("Evaluate and trace", "Datasets and built-in evaluators; local OpenTelemetry collector; hosted-agent telemetry from Application Insights", "app-insights"),
        ]
        bx = []
        sy = fy
        for i, (t, sub, ic) in enumerate(steps):
            b = Box(iw - 50, t, sub=sub, theme="green", fill="hatch", icon=ic, icon_pos="left", icon_size=30, size=17, sub_size=13, min_h=70, pad=8)
            b.place(cv, pb.ix + 50, sy)
            numbered(cv, pb.ix + 20, b.cy, i + 1, theme="green", d=30, size=16)
            bx.append(b)
            sy += b.h + 22
        for a, b in zip(bx, bx[1:]):
            arrow(cv, [(a.cx, a.bottom + 3), (b.cx, b.y - 3)], sw=3, end_head="arrow", color=theme("green").stroke)
        learn_line(cv, pb.ix, sy - 8, [("Agent Inspector", INSPECTOR), ("Traces", VSTRACE)])

    # ---------------------------------------------------------------- C: Canvas
    with cv.panel(XC, top, w=WC, min_h=H, title="Foundry Canvas", sub="a GitHub Copilot App extension  |  PREVIEW", theme="green", style="dashed", fill="soft", pad=pad, title_size=26,
                  sub_size=15) as pc:
        iw = WC - 2 * pad
        c1 = Card(iw, "Design, configure, test and deploy hosted agents from a side panel", [
            "Install: GitHub Copilot App > Settings > Plugins > search microsoft-foundry",
            "It opens in the right-hand panel when you ask Copilot to create a Foundry hosted agent, signs you in to Azure and remembers the subscription and project",
        ], theme="green", icon="copilot", badge="preview", body_size=15, title_size=19, pad=14, src=[("What is Microsoft Foundry Canvas?", CANVAS)])
        c1.place(cv, pc.ix, pc.iy)
        py = c1.bottom + 24
        cw_, sw_ = 250, 500
        with cv.panel(pc.ix, py, w=iw, title="GitHub Copilot App", theme="gray", style="dotted", fill="none", pad=14, title_size=19) as gp:
            stg = [("Create new hosted agents", "Inspire me, Help me decide or Hello world", "green"),
                   ("Build current hosted agent", "Wire a deployed model; add Toolboxes, skills and guardrails from your project", "green"),
                   ("Deploy and test", "Inspect Locally (embedded Agent Inspector) or Deploy to Foundry", "green")]
            sb = []
            yy = gp.iy
            for i, (t, sub, th) in enumerate(stg):
                b = Box(sw_ - 60, t, sub=sub, theme=th, fill="hatch", size=17, sub_size=13, min_h=92, pad=8)
                b.place(cv, gp.ix + cw_ + 90, yy)
                numbered(cv, b.x + 2, b.y + 2, i + 1, theme=th, d=28, size=15)
                sb.append(b)
                yy += b.h + 18
            for a, b in zip(sb, sb[1:]):
                arrow(cv, [(a.cx, a.bottom + 2), (b.cx, b.y - 14)], sw=2.5, end_head="arrow", color=theme("green").stroke)
            chat = Box(cw_ - 20, "Copilot conversation", sub="scaffolds and edits your agent code, runs commands", theme="gray", fill="soft", icon="copilot", icon_pos="top", icon_size=34,
                       size=17, sub_size=13, h=yy - 18 - gp.iy)
            chat.place(cv, gp.ix, gp.iy)
            arrow(cv, [(sb[0].x - 6, sb[0].cy + 14), (chat.right + 6, sb[0].cy + 14)], sw=3, end_head="arrow", color="#495057", dash="dashed", label="ready-to-run prompt",
                  label_size=13, label_wrap=96)
        ny = gp.bottom + 20
        n1 = Note(iw, "Each choice in the canvas becomes a ready-to-run prompt with the project, subscription and endpoint attached; Copilot does the file edits. Inspect Locally "
                       "and Deploy to Foundry run the underlying azd commands, so you can drop to the terminal at any point.", kind="info", title="Canvas shows, Copilot edits",
                  size=14, title_size=16, pad=11)
        n1.place(cv, pc.ix, ny)
        n2 = Note(iw, "The capability reference calls it a generic 'visual surface for composing and inspecting agents'; the Canvas page scopes it to hosted agents in GitHub Copilot App. "
                      "This canvas follows the page.", kind="warn", title="Docs disagree: what Canvas is", size=14, title_size=16, pad=11)
        n2.place(cv, pc.ix, n1.bottom + 16)
    return max(pa.bottom, pb.bottom, pc.bottom)


# ================================================================================================ 2. terminal
EXT_CORE = [
    ("azure.ai.agents", "azd ai agent", "Ship agents from your terminal; also installs its dependencies, including the inspector, project, connection and toolbox support"),
    ("azure.ai.connections", "azd ai connection", "Manage Foundry project connections"),
    ("azure.ai.inspector", "azd ai inspector", "Browser-based inspector UI for locally running agents"),
    ("azure.ai.projects", "azd ai project", "Configure project resources and model deployments; manage the endpoint context"),
    ("azure.ai.routines", "azd ai routine", "Manage routines: timers, schedules, event triggers"),
    ("azure.ai.skills", "azd ai skill", "Manage skills: reusable agent behavioural guidelines"),
    ("azure.ai.toolboxes", "azd ai toolbox", "Manage toolboxes: versioned tool collections"),
]
EXT_OPT = [
    ("azure.ai.evaluations", "azd ai eval", "Scaffold project evaluations, manage evaluators, inspect results, gate builds"),
    ("azure.ai.dataset", "azd ai dataset", "Register, version, download and delete datasets"),
    ("azure.ai.finetune", "azd ai finetuning", "Submit and manage fine-tuning jobs and deploy their models"),
    ("azure.ai.models", "azd ai models", "Upload, register, inspect and maintain custom model weights"),
]


def s_terminal(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Terminal: azd ai extensions and the Foundry DevPack", w=W,
                   sub="Learn: Develop agents with azd; Install the azd Foundry extensions; Prepare your development environment  |  azd extensions are preview-labelled (see the note below)")
    top = y + 100
    LW = 1780
    RW = W - LW - 70
    RX = LW + 70

    # ---- left: loop, extensions table
    cv.text(0, top, "The developer loop", size=24, color=theme("grape").deep)
    steps = [
        ("azd ai agent init", "scaffold a hosted, prompt or voice agent project"),
        ("azd ai agent run", "run the agent locally; azd ai agent invoke --local calls it"),
        ("azd up", "provision and deploy"),
        ("azd ai agent eval", "generate a test suite, then run the evaluation"),
        ("azd ai agent optimize", "agent optimizer: improve the agent (preview)"),
        ("azd down", "tear it down"),
    ]
    by = flow_row(cv, 0, top + 40, LW, steps, "grape", h=132, size=15, tip=26, sub_size=13, mono_titles=True)
    ex = ChipFlow([Chip("azd ai agent sessions", theme="grape", size=14, fill="soft"), Chip("files", theme="grape", size=14, fill="soft"), Chip("monitor", theme="grape", size=14, fill="soft"),
                   Chip("doctor", theme="grape", size=14, fill="soft"), Chip("state-stores", theme="grape", size=14, fill="soft"), Chip("pack", theme="grape", size=14, fill="soft"),
                   Chip("publish: Teams and M365 Activity agents", theme="grape", size=14, fill="soft")], LW, gap=8)
    cv.text(0, by + 18, "Also under azd ai agent:", size=15, color=MUTED)
    ex.place(cv, 0, by + 44)
    cb = CodeBox(LW, [("# a routine that fires every morning at 07:00", "note"), 'azd ai routine create --trigger recurring --cron "0 7 * * *"'], size=15, th="grape")
    cb.place(cv, 0, ex.y + ex.h + 20)

    rows = []
    for eid, grp, what in EXT_CORE:
        rows.append([dict(text=eid, color="#862e9c"), dict(text=grp, color="#862e9c"), what, ("Bundled", "grape")])
    for eid, grp, what in EXT_OPT:
        rows.append([dict(text=eid, color="#495057"), dict(text=grp, color="#495057"), what, ("Install separately", "gray")])
    t = Table([("Extension ID", 210), ("Command group", 190), ("What it does", 1080), ("Packaging", 190)], rows, w=LW, theme="grape", size=14, head_size=15, pad_y=6,
              title="Seven core extensions in the microsoft.foundry bundle, four more on their own", title_size=20)
    t.place(cv, 0, cb.bottom + 36)
    cv.text(0, t.bottom + 8, "Learn: Install the Azure Developer CLI Foundry extensions", size=12, color=LINK, link=AZD_EXT)
    left_bottom = t.bottom + 28

    # ---- right: azure.yaml, install, automation
    c1 = Card(RW, "azure.yaml: one file for the whole project", [
        "host values: azure.ai.project, azure.ai.agent, azure.ai.connection, azure.ai.toolbox, azure.ai.skill, azure.ai.routine",
        "${VAR} substitution from .azure/<env>/.env",
        "Agent types: hosted (source or container), prompt, voice (declarative kind: prompt-voice, or a hosted voice wrapper)",
        "The agent container listens on port 8088; protocols: responses (POST /responses) and invocations (POST /invocations)",
    ], theme="grape", icon="azd", body_size=15, title_size=19, pad=14, src=[("Develop agents with azd", AZD)])
    c1.place(cv, RX, top)
    cb2 = CodeBox(RW, [("# install (azd 1.37.0 or later; Python 3.10+ or .NET 8+)", "note"), "azd ext install microsoft.foundry", "azd ext upgrade microsoft.foundry",
                       ("# optional extensions", "note"), "azd ext install azure.ai.evaluations", "azd ext install azure.ai.dataset", "azd ext install azure.ai.finetune",
                       "azd ext install azure.ai.models", ("# verify and sign in", "note"), "azd ext list", "azd ai --help", "azd auth login"],
                  title="Install, verify, sign in", size=14, th="grape")
    cb2.place(cv, RX, c1.bottom + 20)
    c2 = Card(RW, "Automation hygiene for CI and coding agents", [
        "--no-prompt and --output json on commands",
        "Point at a project with azd ai project set <endpoint>, or the FOUNDRY_PROJECT_ENDPOINT environment variable",
    ], theme="grape", body_size=15, title_size=19, pad=14, src=[("Use azd with coding agents", AZD_CODING)])
    c2.place(cv, RX, cb2.bottom + 20)
    right_bottom = c2.bottom

    # ---- DevPack band
    dy = max(left_bottom, right_bottom) + 44
    with cv.panel(0, dy, w=W, title="Foundry DevPack: one command for the whole toolchain (preview)", sub="winget, Homebrew or a shell installer  |  Learn: Prepare your development environment; "
                                                                                                            "blog: Introducing Foundry Dev Pack (2026-09-15)",
                  theme="grape", style="dashed", fill="soft", pad=22, title_size=26, sub_size=15) as dp:
        os_box = CodeBox(980, [("# Windows", "note"), "winget install Microsoft.FoundryDevPack", ("# macOS", "note"),
                               "brew install --cask microsoft/foundry/devpack && foundry-devpack install", ("# Linux", "note"),
                               "curl -fsSL https://aka.ms/foundry-devpack-install.sh | bash"], title="Install", size=15, th="grape")
        os_box.place(cv, dp.ix, dp.iy)
        inst = Table([("Installs", 330), ("What you can do", 660)], [
            [("azd and azd ai", "grape"), "Scaffold, deploy, evaluate and automate from the terminal"],
            [("Microsoft Foundry Skill", "orange"), "Gives coding agents reusable guidance for Foundry workflows"],
            [("Foundry Toolkit for VS Code", "green"), "Installed only when VS Code is present: build, test, evaluate and deploy from the editor"],
            [("Foundry Canvas (preview)", "green"), "Installed only when GitHub Copilot App is present: design and deploy hosted agents from a guided canvas"],
        ], w=1000, theme="grape", size=14, head_size=15, pad_y=6, title="DevPack installs its core tools and adds host extensions only when their apps exist", title_size=18)
        inst.place(cv, os_box.right + 40, dp.iy)
        n1 = Note(W - 44 - 980 - 1000 - 80, "It does not install VS Code or GitHub Copilot App. The July-August 2026 round-up described DevPack 0.1.3 as preview installers for "
                                               "Windows, macOS and Linux (x64 and Arm64).", kind="preview", title="Scope and status", size=14, title_size=16, pad=11,
                  src=[("Prepare your development environment", INSTALL)])
        n1.place(cv, inst.right + 40, dp.iy)
    ny = dp.bottom + 30
    notes = [
        Note(973, "The azd overview and install pages carry the generic preview banner and the August 2026 blog called the agents extension 1.0.0-beta.13 (preview), yet the capability "
                  "map and capability reference list azd without a preview label and the GA matrix does not mention it. Draw azd as preview-labelled extensions.", kind="warn",
             title="Docs disagree: is azd GA?", src=[("Install the azd Foundry extensions", AZD_EXT), ("Develop agents with azd", AZD)]),
        Note(973, "To use the Microsoft Copilot harness with prompt agents, install azure.ai.agents 1.0.0-beta.22 or later and set AZD_ALPHA_ENABLE_AGENTS_MANAGED_HARNESS=true in the "
                  "shell (or each CI job) that runs azd. The opt-in does not grant service access or change your Azure permissions.", kind="preview",
             title="Copilot harness opt-in (preview)", src=[("Install the azd Foundry extensions", AZD_EXT)]),
        Note(973, "Foundry User on the project to create and invoke agents and reuse a project and deployment. To create resources and assign roles during provisioning: Contributor and "
                  "Role Based Access Control Administrator together. Foundry Project Manager to create project connections, including a Toolbox connection created by azd.",
             kind="info", title="Roles azd needs", src=[("Install the azd Foundry extensions", AZD_EXT)]),
    ]
    row(cv, 0, ny, notes, gap=40)
    return ny + max(n.h for n in notes)


# ================================================================================================ 3. REST + ARM
def s_rest(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "REST v1, preview gating, ARM and infrastructure as code", w=W,
                   sub="Learn: Foundry REST API reference (v1); Configure an agent endpoint; Foundry SDKs; Microsoft.CognitiveServices/accounts template reference  |  as of 2026-11-03")
    top = y + 100
    LW, MW = 1480, 760
    GAPX = 60
    RW = W - LW - MW - 2 * GAPX
    mono = lambda t, c="#1864ab": dict(text=t, color=c)
    routes = [
        [mono("/openai/v1/"), "The Learn 'v1 API' group: Chat, Embeddings, Evals, Files, Fine-tuning, Models, Responses, Vector stores. Image, audio and video reference pages are preview"],
        [mono("/openai/v1/decisions"), "Decisions API: typed, non-generative decisions; gpt-6-luna is the only supported model (as of 2026-11-03)"],
        [mono("{project_endpoint}/openai/v1/responses"), "Responses API through the project endpoint (agents, conversations, platform tools)"],
        [mono("{project_endpoint}/agents/{name}/endpoint/protocols/..."), "Each agent's stable endpoint. Suffixes: openai/responses, openai/conversations, invocations, activityprotocol, a2a (v1.0 GA, v0.3 preview), "
                                                                            "mcp (preview); invocations_ws is a wss:// route"],
        [mono(".../applications/<app>/protocols/openai/responses"), "Legacy Agent Application route (existing applications keep working)"],
        [mono("<resource>.services.ai.azure.com/managed-deployments/<deployment>/"), "Managed-compute model deployments"],
        [mono("<resource>.api.cognitive.microsoft.com/providers/blackforestlabs/v1/<model>?api-version=preview"), "FLUX image models"],
    ]
    t1 = Table([("Route", 560), "What it serves"], routes, w=LW, theme="indigo", size=14, head_size=15, pad_y=6, title="Data plane: stable v1 routes", title_size=20)
    t1.place(cv, 0, top)
    n1 = Note(LW, "No api-version on the /openai/v1 routes. The agent-endpoint examples on Learn still pass ?api-version=v1, and the invocations_ws route is "
                  "wss://<account>.services.ai.azure.com/api/projects/<project>/agents/<name>/endpoint/protocols/invocations_ws?api-version=v1. The project endpoint "
                  "does not currently route embeddings: use /openai/v1.", kind="gotcha", title="Versioning is not uniform", size=14, title_size=16, pad=11,
              src=[("Configure an agent endpoint", CONFIGURE_AGENT), ("Hosted agents", HOSTED)])
    n1.place(cv, 0, t1.bottom + 24)
    n2 = Note(LW, "Calling an agent's endpoint authenticates with Microsoft Entra: the AzureRbac (alias Entra) scheme needs the Foundry Agent Consumer role or another role with the "
                  "endpoint permission; AgentBlueprint is preview; BotServiceRbac and BotServiceTenant are set automatically when you publish to Teams or Microsoft 365. "
                  "API key authentication is not supported on agent endpoints.", kind="key", title="Inbound authorization on an agent endpoint", size=14, title_size=16, pad=11,
              src=[("Configure an agent endpoint", CONFIGURE_AGENT)])
    n2.place(cv, 0, n1.bottom + 20)
    left_bottom = n2.bottom

    # ---- middle: preview gating
    gate = Table([("Foundry-Features header", 400), "Surface"], [
        [mono("Toolboxes=V1Preview"), "Toolboxes"], [mono("Skills=V1Preview"), "Skills"], [mono("AgentEndpoints=V1Preview"), "Agent endpoints"],
        [mono("ExternalAgents=V1Preview"), "External agents"], [mono("VoiceAgents=V1Preview"), "Voice agents"], [mono("AgentsOptimization=V2Preview"), "Agent optimization"],
    ], w=MW, theme="orange", size=14, head_size=15, pad_y=6, title="Preview REST surfaces need a gate header", title_size=20)
    MX = LW + GAPX
    gate.place(cv, MX, top)
    cb = CodeBox(MW, [("# header on each preview REST call", "note"), "Foundry-Features: Toolboxes=V1Preview", ("# Python SDK", "note"), "AIProjectClient(..., allow_preview=True)",
                      ("# C# pipeline policy", "note"), 'new FoundryFeaturesPolicy("AgentsOptimization=V2Preview")'], title="Opting in", size=14, th="orange")
    cb.place(cv, MX, gate.bottom + 24)
    cv.text(MX, cb.bottom + 8, "Learn: Foundry SDKs; Foundry REST API reference", size=12, color=LINK, link=SDK)

    # ---- right: ARM
    RX = MX + MW + GAPX
    c1 = Card(RW, "Control plane: Azure Resource Manager", [
        "Microsoft.CognitiveServices/accounts: kind AIServices, allowProjectManagement: true",
        "Child types: accounts/projects, deployments, connections, capability settings",
        "GA API versions: 2026-09-01, 2026-07-01, 2026-05-01, 2026-03-01",
        "Preview: 2026-09-15-preview, 2026-07-15-preview, 2026-05-15-preview, 2026-03-15-preview, 2026-01-15-preview",
        "Authorised by Azure RBAC actions; the data plane uses dataActions",
    ], theme="grape", icon="management-group", body_size=15, title_size=19, pad=14, src=[("Microsoft.CognitiveServices/accounts reference", ARM)])
    c1.place(cv, RX, top)
    tools = Table([("Tool", 150), "Notes"], [
        [("Bicep / ARM", "grape"), "Template reference above; the samples repo has numbered scenario folders"],
        [("Terraform", "grape"), "AzureRM 4.56.0 or later (non-destructive OpenAI to AIServices change), or AzAPI"],
        [("Azure CLI", "grape"), "az cognitiveservices account create, az cognitiveservices account project create (CLI 2.80.0 or later for projects)"],
        [("Python", "grape"), "azure-mgmt-cognitiveservices 13.7.0 or later"],
    ], w=RW, theme="grape", size=14, head_size=15, pad_y=6, title="Provision with", title_size=20)
    tools.place(cv, RX, c1.bottom + 22)
    right_bottom = tools.bottom

    # ---- 48 REST groups
    gy = max(left_bottom, gate.bottom, cb.bottom, right_bottom) + 50
    groups = {
        "green": ["Agent Conversations", "Agent Insight Monitors", "Agent Invocations", "Agent Invocations WebSocket", "Agent Microsoft 365 Publishing", "Agent Session Files",
                  "Agent Sessions", "Agent Telephony", "Agent Versions", "Agents", "Voice Agent WebSocket", "Routines", "Schedules", "Skills", "Toolboxes", "Containers"],
        "teal": ["Memory Stores"],
        "blue": ["Audio", "Batch", "Chat", "Completions", "Conversations", "Embeddings", "Files", "Fine-tuning", "Images", "Models", "Moderations", "Realtime", "Responses",
                 "Uploads", "Vector stores", "Videos"],
        "violet": ["AgentOptimizationJobs", "DataGenerationJobs", "Evals", "Evaluation Rules", "Evaluation Taxonomies", "EvaluatorGenerationJobs", "Evaluators", "Insights", "Redteams"],
        "cyan": ["Connections", "Datasets", "Deployments", "Indexes"],
        "gray": ["Assistants", "Threads"],
    }
    chips = []
    n_total = 0
    for th, names in groups.items():
        for n in names:
            n_total += 1
            chips.append(Chip(n, theme=th, size=14, fill="soft", pad_x=10, pad_y=5, dash="dashed" if th == "gray" else "solid"))
    assert n_total == 48, n_total
    cf = ChipFlow(chips, W - 60, gap=8)
    with cv.panel(0, gy, w=W, title="The 48 REST reference groups on Learn (v1)", sub="our colouring: agents and runtime (green), memory (teal), OpenAI-compatible (blue), evaluation and optimization (violet), "
                                                                                     "project resources (cyan), Assistants-era (gray, dashed: the Assistants API sunset on 2026-08-26)",
                  theme="gray", style="dotted", fill="none", pad=22, title_size=24, sub_size=15) as p:
        cf.place(cv, p.ix, p.iy)
        learn_line(cv, p.ix, cf.y + cf.h + 14, [("Foundry REST API reference (v1)", REST_REF), ("interactive reference: ai.azure.com/api-reference", "https://ai.azure.com/api-reference/")])
    return p.bottom


# ================================================================================================ 4. AI-assisted
TOOL_CATS = [
    ("Agent management", [("agent_get", "r"), ("agent_update", "w"), ("agent_invoke", "w"), ("agent_delete", "w"), ("agent_container_control", "w"),
                          ("agent_container_status_get", "r"), ("agent_definition_schema_get", "r")], "green"),
    ("Hosted agent sessions and files", [("session_create", "w"), ("session_get", "r"), ("session_list", "r"), ("session_delete", "w"), ("session_logstream", "r"),
                                         ("session_file_list", "r"), ("session_file_stat", "r"), ("session_file_mkdir", "w"), ("session_file_upload", "w"),
                                         ("session_file_download", "r"), ("session_file_delete", "w")], "green"),
    ("Toolbox management", [("toolbox_get", "r"), ("toolbox_version_get", "r"), ("toolbox_version_create", "w"), ("toolbox_update", "w"), ("toolbox_delete", "w"),
                            ("toolbox_version_delete", "w")], "orange"),
    ("Dataset management", [("evaluation_dataset_create", "w"), ("evaluation_dataset_get", "r"), ("evaluation_dataset_versions_get", "r"),
                            ("evaluation_dataset_sas_url_get", "r")], "violet"),
    ("Data generation jobs", [("data_generation_job_create", "w"), ("data_generation_job_get", "r"), ("data_generation_job_cancel", "w"), ("data_generation_job_delete", "w")], "violet"),
    ("Evaluation operations", [("evaluation_agent_batch_eval_create", "w"), ("evaluation_dataset_batch_eval_create", "w"), ("evaluation_get", "r"),
                               ("evaluation_comparison_create", "w"), ("evaluation_comparison_get", "r")], "violet"),
    ("Trace evaluation", [("evaluation_agent_traces_batch_eval_create", "w"), ("evaluation_traces_batch_eval_create", "w")], "violet"),
    ("Evaluation suites", [("evaluation_suite_create", "w"), ("evaluation_suite_get", "r"), ("evaluation_suite_update", "w"), ("evaluation_suite_run", "w"),
                           ("evaluation_suite_delete", "w"), ("evaluation_suite_generation_job_create", "w"), ("evaluation_suite_generation_job_get", "r"),
                           ("evaluation_suite_generation_job_cancel", "w"), ("evaluation_suite_generation_job_delete", "w")], "violet"),
    ("Evaluator catalog", [("evaluator_catalog_get", "r"), ("evaluator_catalog_create", "w"), ("evaluator_catalog_update", "w"), ("evaluator_catalog_delete", "w")], "violet"),
    ("Evaluator generation jobs", [("evaluator_generation_job_create", "w"), ("evaluator_generation_job_get", "r"), ("evaluator_generation_job_cancel", "w")], "violet"),
    ("Model catalog and details", [("model_catalog_list", "r"), ("model_details_get", "r")], "blue"),
    ("Model deployment management", [("model_deploy_azure_direct_model", "w"), ("model_deploy (deprecated alias)", "w"), ("model_deploy_managed_compute", "w"),
                                     ("model_deployment_get", "r"), ("model_deployment_delete", "w")], "blue"),
    ("Model analytics and recommendations", [("model_benchmark_get", "r"), ("model_benchmark_subset_get", "r"), ("model_similar_models_get", "r"),
                                             ("model_switch_recommendations_get", "r")], "blue"),
    ("Model monitoring and operations", [("model_monitoring_metrics_get", "r"), ("model_deprecation_info_get", "r"), ("model_quota_list", "r")], "blue"),
    ("Project connections", [("project_connection_list", "r"), ("project_connection_get", "r"), ("project_connection_list_metadata", "r"), ("project_connection_create", "w"),
                             ("project_connection_update", "w"), ("project_connection_delete", "w")], "cyan"),
    ("Prompt optimization", [("prompt_optimize", "w")], "violet"),
    ("Continuous evaluation", [("continuous_eval_create", "w"), ("continuous_eval_get", "r"), ("continuous_eval_delete", "w")], "violet"),
]


def s_assist(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "AI-assisted: coding agents, the Foundry Skill and the Foundry MCP Server (preview)", w=W,
                   sub="Learn: Use the Microsoft Foundry Skill in coding agents; Foundry MCP Server: get started, available tools, security best practices  |  tool names as listed on Learn")
    top = y + 100
    LW, MW = 960, 1130
    G = 55
    RW = W - LW - MW - 2 * G

    # ---- left: the Foundry Skill
    sk = Card(LW, "Microsoft Foundry Skill", [
        "A 'microsoft-foundry' meta-skill with sub-skills that give a coding agent Foundry know-how",
        "Prerequisites: Node.js 18 or later (the plugin starts MCP servers with npx), Git, az login and azd auth login",
        "Workspace files it reads: azure.yaml, .azure/<env>/.env, .foundry/agent-metadata.yaml (and .<env>.yaml), eval.yaml",
        "The VS Code Foundry Toolkit ships its own skills (vscode-microsoft-foundry, foundrytk-quick-start)",
    ], theme="orange", icon="github", body_size=15, title_size=20, pad=14, src=[("Use the Microsoft Foundry Skill", SKILL)])
    sk.place(cv, 0, top)
    subs = ChipFlow([Chip(t, theme="orange", size=14, fill="soft") for t in (
        "Onboarding", "Access and capacity (RBAC, quota)", "Model deployment", "Model customization (SFT, DPO, RFT)", "Agent creation", "Agent deployment (ACR push, hosted agent)",
        "Invocation and testing", "Evaluation and optimization", "Trace and dataset work", "Troubleshooting")], LW - 28, gap=8)
    cv.text(0, sk.bottom + 18, "What the skill covers", size=18, color=theme("orange").deep)
    subs.place(cv, 0, sk.bottom + 48)
    cb = CodeBox(LW, [("# just the skill", "note"), "npx skills add https://github.com/microsoft/azure-skills --skill microsoft-foundry",
                      ("# Azure Skills Plugin (skill + Azure MCP + Foundry MCP): Copilot CLI", "note"), "/plugin marketplace add microsoft/azure-skills", "/plugin install azure@azure-skills",
                      ("# Claude Code", "note"), "/plugin install azure@claude-plugins-official"], title="Install", size=14, th="orange")
    cb.place(cv, 0, subs.y + subs.h + 22)
    left_bottom = cb.bottom

    # ---- middle: sequence
    sq = Sequence(cv, LW + G, top, [("You", "gray", "user"), ("Coding agent", "orange", "github"), ("azd + Foundry MCP Server", "orange", "mcp"), ("Foundry project", "blue", "foundry")],
                  spacing=300, head_w=190, head_h=58, step=62, size=15, label_size=14)
    sq.msg(0, 1, "1  'Use the Foundry Skill to create a project, deploy a model and scaffold a hosted agent'")
    sq.msg(1, 1, "2  load the Foundry Skill")
    sq.msg(1, 0, "3  proposes a plan", dash="dashed")
    sq.note(0, 1, "You review it first: write tools and azd steps create live, billable resources immediately.", kind="gotcha", size=14)
    sq.msg(0, 1, "4  approve")
    sq.msg(1, 2, "5  runs azd commands or MCP write tools")
    sq.msg(2, 3, "6  calls the project as you (Entra on-behalf-of)")
    sq.msg(3, 2, "7  result: project, deployment, agent", dash="dashed")
    sq.msg(2, 1, "8  result", dash="dashed")
    sb = sq.end()
    cv.text(LW + G, sb + 8, "Learn: Use the Microsoft Foundry Skill; Foundry MCP Server security best practices", size=12, color=LINK, link=SKILL)
    mid_bottom = sb + 30

    # ---- right: server facts
    RX = LW + G + MW + G
    cf = Card(RW, "Foundry MCP Server (preview)", [
        "Cloud-hosted Model Context Protocol server: no infrastructure to deploy",
        "Endpoint: https://mcp.ai.azure.com over HTTP; connect from any MCP client, for example GitHub Copilot Agent Mode in VS Code 1.99 or later",
        "79 tools in 17 categories; each is read or write",
        "Auth: Microsoft Entra on-behalf-of; token scope https://mcp.ai.azure.com",
        "Reader for read tools, Contributor for write tools; Conditional Access Administrator only to set tenant policies",
    ], theme="orange", icon="mcp", badge="preview", body_size=15, title_size=20, pad=14, src=[("Foundry MCP Server: get started", MCP)])
    cf.place(cv, RX, top)
    jc = CodeBox(RW, ['{ "servers": {', '  "foundry-mcp-remote": {', '    "type": "http",', '    "url": "https://mcp.ai.azure.com"', "  } } }"],
                 title=".vscode/mcp.json", size=14, th="orange")
    jc.place(cv, RX, cf.bottom + 20)
    right_bottom = jc.bottom

    # ---- tool catalogue
    ty = max(left_bottom, mid_bottom, right_bottom) + 50
    n_read = sum(1 for _, tools, _ in TOOL_CATS for _, rw in tools if rw == "r")
    n_write = sum(1 for _, tools, _ in TOOL_CATS for _, rw in tools if rw == "w")
    cv.text(0, ty, "All 79 Foundry MCP Server tools by category", size=26, color=theme("orange").deep)
    legend_y = ty + 40
    cv.rect(0, legend_y + 2, 22, 16, stroke="#2f9e44", fill="#b2f2bb", style="solid", sw=2)
    cv.text(30, legend_y, f"green = read tool: retrieves information ({n_read} tools)", size=15)
    cv.rect(520, legend_y + 2, 22, 16, stroke="#e03131", fill="#ffc9c9", style="solid", sw=2)
    cv.text(550, legend_y, f"red = write tool: creates, updates or deletes; affects live resources and billing immediately ({n_write} tools)", size=15)
    cv.text(2300, legend_y, "Learn: Foundry MCP Server available tools", size=13, color=LINK, link=MCP_TOOLS)
    cw, gx = 576, 30
    cards = []
    n_tools = 0
    for name, tools, th in TOOL_CATS:
        body = []
        for tn, rw in tools:
            body.append(("good", tn) if rw == "r" else ("warn", tn))
            n_tools += 1
        cards.append(Card(cw, f"{name} ({len(tools)})", body, theme=th, body_size=14, title_size=17, pad=13, gap=4))
    assert n_tools == 79 and len(TOOL_CATS) == 17 and n_read + n_write == 79, (n_tools, len(TOOL_CATS))
    columns = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9], [10, 11, 12, 13], [14, 16, 15]]
    cb_bottom = 0.0
    for k, idxs in enumerate(columns):
        yy = legend_y + 44
        for i in idxs:
            cards[i].place(cv, k * (cw + gx), yy)
            yy += cards[i].h + 22
        cb_bottom = max(cb_bottom, yy - 22)

    # ---- notes
    ny = cb_bottom + 40
    notes = [
        Note(973, "Preview, no SLA, and the tool set may change. The server is a global stateless proxy: requests and responses might be processed in EU or US data centres, and it does not "
                  "store data. It exposes a public endpoint and cannot reach Foundry resources behind Azure Private Link: use the SDKs or REST, or a custom MCP server with Agent Service "
                  "private networking.", kind="gotcha", title="Limits of the hosted server", src=[("Foundry MCP Server: security best practices", MCP_SEC), ("Available tools", MCP_TOOLS)]),
        Note(973, "Tenant admins can grant or block the server for selected users or workload identities with Conditional Access: create the service principal for the Foundry MCP Server "
                  "application, then add a policy to that enterprise application (the application ID is on the security page). The Conditional Access Administrator role is needed.",
             kind="info", title="Govern it with Conditional Access", src=[("Foundry MCP Server: security best practices", MCP_SEC)]),
        Note(973, "Write tools change live resources and billing immediately. Model deployment: use model_deploy_azure_direct_model, not the deprecated model_deploy alias, and model_deploy_managed_compute "
                  "only when model details report isFoundryManagedCompute. Toolbox versions are immutable: toolbox_version_create creates the toolbox if needed; promote a version with "
                  "toolbox_update.", kind="tip", title="Use the write tools carefully", src=[("Available tools", MCP_TOOLS)]),
    ]
    row(cv, 0, ny, notes, gap=40)
    return ny + max(n.h for n in notes)


# ================================================================================================ 5. LangChain, templates, samples
def s_code(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Frameworks and starting points: LangChain and LangGraph, templates, samples", w=W,
                   sub="Learn: LangChain and LangGraph with Foundry; Get started with an AI template  |  GitHub: microsoft-foundry/foundry-samples (folders read 2026-11-03)")
    top = y + 100
    LW = 1480
    RX = LW + 60
    RW = W - RX
    mono = lambda t: dict(text=t, color="#364fc7")
    ns = Table([("Namespace (langchain_azure_ai.)", 380), "Typical use"], [
        [mono("agents"), "Managed Foundry Agent Service nodes for LangGraph and LangChain graphs and flows"],
        [mono("agents.hosting"), "Host a compiled LangGraph agent on Agent Service with the Responses or Invocations protocol"],
        [mono("agents.middleware"), "Foundry Content Safety and moderation as guardrails"],
        [mono("chat_models"), "Azure OpenAI and model-catalog chat models"],
        [mono("embeddings"), "Embedding models from the catalog for search, retrieval and ranking"],
        [mono("vectorstores"), "Azure AI Search and Cosmos DB vector integrations"],
        [mono("retrievers"), "Retrieval over Azure-backed indexes and stores"],
        [mono("chat_history"), "Persist and replay chat history across sessions; memory-powered histories"],
        [mono("tools"), "Document Intelligence, Vision, health text analytics, Logic Apps; load a whole Foundry Toolbox through one MCP endpoint"],
        [mono("callbacks"), "Capture run events and emit OpenTelemetry traces"],
        [mono("query_constructors"), "Backend-specific query filters for retrieval"],
        [mono("document_loaders"), "Load documents and media with Content Understanding"],
    ], w=LW, theme="indigo", size=14, head_size=15, pad_y=6, title="langchain-azure-ai: the namespace map", title_size=20)
    ns.place(cv, 0, top)
    cb = CodeBox(LW, [("# base package; extras: [tools] for the tools namespace, [opentelemetry] for tracing, [v1] for Foundry classic", "note"),
                      "pip install -U langchain-azure-ai azure-identity", 'pip install -U "langchain-azure-ai[tools]"', 'pip install -U "langchain-azure-ai[opentelemetry]"',
                      ("# one environment variable; Entra authentication and Azure RBAC apply", "note"),
                      'export AZURE_AI_PROJECT_ENDPOINT="https://<resource>.services.ai.azure.com/api/projects/<project>"'],
                 title="Python 3.11 or later; az login so DefaultAzureCredential can sign in", size=14, th="indigo")
    cb.place(cv, 0, ns.bottom + 24)
    n1 = Note(LW, "Through project_endpoint, authentication is Microsoft Entra ID and Azure RBAC on the project (Foundry User is the least-privilege development role). API keys are for direct "
                  "service endpoints such as /openai/v1.", kind="info", title="Auth for LangChain", size=14, title_size=16, pad=11, src=[("LangChain and LangGraph with Foundry", LANGCHAIN)])
    n1.place(cv, 0, cb.bottom + 20)
    left_bottom = n1.bottom

    # ---- right: templates
    GH = lambda repo: dict(text=repo, link=f"https://github.com/{repo}", color=LINK)
    tt = Table([("Solution template", 300), "GitHub repo"], [
        ["AI chat", GH("Azure-Samples/get-started-with-ai-chat")],
        ["AI agents", GH("Azure-Samples/get-started-with-ai-agents")],
        ["Conversation insights", GH("microsoft/Conversation-Knowledge-Mining-Solution-Accelerator")],
        ["Multi-agent workflow automation", GH("microsoft/Multi-Agent-Custom-Automation-Engine-Solution-Accelerator")],
        ["Multi-modal content processing", GH("microsoft/content-processing-solution-accelerator")],
        ["Document generation", GH("microsoft/document-generation-solution-accelerator")],
        ["Client meeting enhancement", GH("microsoft/Build-your-own-copilot-Solution-Accelerator")],
        ["Code modernization", GH("microsoft/Modernize-your-code-solution-accelerator")],
        ["Conversational agent", GH("Azure-Samples/Azure-Language-OpenAI-Conversational-Agent-Accelerator")],
    ], w=RW, theme="gray", size=14, head_size=15, pad_y=5, title="Portal: Discover > Solution templates (GA per the GA matrix)", title_size=20)
    tt.place(cv, RX, top)
    cv.text(RX, tt.bottom + 8, "Learn: Get started with an AI template. Each repo has a README with setup and deployment. Agent templates (Discover > Agents) are starter manifests you deploy from the portal.",
            size=12, color=LINK, link=TEMPLATE, wrap=RW)
    sy = tt.bottom + 52
    sc = Card(RW, "microsoft-foundry/foundry-samples (GitHub)", [
        "# samples/",
        "REST, cli, cpp, csharp, java, javascript, python, rust, typescript",
        "samples/python: autopilot-agents, black-forest-labs, enterprise-agent-tutorial, external-agents, finetuning, foundry-autopilot-agent, foundry-local, foundry-models, hosted-agents, "
        "prompt-agents, quickstart, voice-agents",
        "# infrastructure/ (Bicep and Terraform)",
        "00 basic, 01 connections, 02 storage + speech + language, 03 custom DNS, 04 disable local auth, 05 custom policy definitions",
        "10-11 private network (basic, with VNet); 15-19 private-network variants of the standard agent setup (APIM, user-assigned identity, managed virtual network, agent tools)",
        "20 user-assigned identity, 25 Entra ID passthrough, 30-32 customer-managed keys, 40-43 basic and standard agent setup (with customization), 45 basic agent with Bing; "
        "Terraform adds 46-47 bring-your-own models",
        "# also: samples-classic/, samples-mistral/, migration/ (Assistants to agents tool)",
    ], theme="gray", icon="github", body_size=14, title_size=19, pad=14, link=SAMPLES)
    sc.place(cv, RX, sy)
    return max(left_bottom, sc.bottom)
