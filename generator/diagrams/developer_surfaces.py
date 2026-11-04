"""Ways to build on Microsoft Foundry (part 1): the layered picture (surface -> SDK or API -> endpoint -> Foundry), the surface x persona
matrix, SDKs and endpoints, authentication per surface, four paths to a first working agent and the gotchas (as of 2026-11-03).
Part 2 holds the per-surface detail: portal, REST/ARM, azd, VS Code, Canvas, coding agents + MCP server tools, LangChain, templates."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="developer-surfaces", title="Ways to build on Microsoft Foundry", section="1", group="Overview", order=6,
    description="Every way in: portal and playgrounds, SDKs, REST, azd, VS Code, Canvas, coding agents and MCP, LangChain and IaC drawn as one layered "
                "picture (surface -> SDK or API -> endpoint -> Foundry), with a surface x persona matrix, endpoints and authentication per surface.",
    tags=["sdk", "endpoints", "azd", "mcp", "authentication", "personas"],
)

W = 3000

# ------------------------------------------------------------------------------------------------ sources
WHAT = learn("what-is-foundry")
SDK = learn("how-to/develop/sdk-overview")
INSTALL = learn("how-to/develop/install-cli-sdk")
AZD = learn("agents/concepts/cli-agent-development")
AZD_EXT = learn("agents/how-to/install-cli-foundry-extensions")
VSCODE = learn("how-to/develop/get-started-projects-visual-studio-code")
SKILL = learn("how-to/develop/use-microsoft-foundry-skill")
MCP = learn("mcp/get-started")
MCP_TOOLS = learn("mcp/available-tools")
MCP_SEC = learn("mcp/security-best-practices")
CANVAS = learn("agents/concepts/foundry-canvas")
LANGCHAIN = learn("how-to/develop/langchain")
PLAYGROUNDS = learn("concepts/concept-playgrounds")
AUTH = learn("concepts/authentication-authorization-foundry")
ENDPOINTS = learn("foundry-models/concepts/endpoints")
RBAC = learn("concepts/rbac-foundry")
GA = learn("concepts/general-availability")
NAV = learn("how-to/navigate-from-classic")
CAP = learn("concepts/capabilities")
TEMPLATE = learn("how-to/develop/ai-template-get-started")
HOSTED_QS = learn("agents/quickstarts/quickstart-hosted-agent")
CLI_CODING = learn("agents/how-to/use-cli-with-coding-agents")
ARM = learn("templates/microsoft.cognitiveservices/accounts", base="azure")
DEVPACK_BLOG = "https://devblogs.microsoft.com/foundry/foundry-devpack-announcement/"


# ================================================================================================ local helpers
def sticker(cv, x, y, text, th="red", size=14):
    """Small solid pill drawn on a card edge (not registered, so it does not trigger overlap warnings)."""
    t = theme(th)
    tw = metrics.line_width(text, size) + 20
    with cv.group():
        cv.rect(x, y, tw, size * 1.25 + 8, stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0)
        cv.text(x + 10, y + 4, text, size=size, color=t.deep)
    return tw


def block_arrow(cv, x, y, w, h, text, *, th="blue", size=17, tip=34, notch=False, sub=None, sub_size=14, reg=True):
    """Chevron-style block arrow with centred text; notch=True gives the 'follows another chevron' shape."""
    t = theme(th)
    pts = [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h)]
    if notch:
        pts.append((x + tip, y + h / 2))
    pts.append(pts[0])
    pad_l = (tip + 12) if notch else 16
    tw = w - tip - pad_l - 12
    lines = metrics.wrap_text(text, tw, size)
    sub_lines = metrics.wrap_text(sub, tw, sub_size) if sub else []
    lh = metrics.line_ratio()
    th_h = len(lines) * size * lh + (len(sub_lines) * sub_size * lh + 3 if sub_lines else 0)
    with cv.group():
        cv.poly(pts, kind="line", stroke=t.stroke, fill=t.fill, fill_style="hachure", sw=2)
        ty = y + (h - th_h) / 2
        cv.text(x + pad_l, ty, "\n".join(lines), size=size, color=t.deep, align="center", w=tw)
        if sub_lines:
            cv.text(x + pad_l, ty + len(lines) * size * lh + 3, "\n".join(sub_lines), size=sub_size, color=MUTED, align="center", w=tw)
    if reg:
        cv.register("chevron", x, y, w, h)


class UrlBox(Rect2):
    """Rounded box: title + rows of (label, monospace url). URLs are placeholders (<resource>), so they are not linked."""

    def __init__(self, w, title, rows, *, th="gray", fill="soft", size=13, title_size=17, label_size=14, pad=12, dash="solid", sw=2, note=None):
        self.th = theme(th)
        self.w, self.fill, self.size, self.title_size, self.label_size, self.pad, self.dash, self.sw = w, fill, size, title_size, label_size, pad, dash, sw
        inner = (w - 2 * pad) * 0.965
        lr, lm = metrics.line_ratio(), metrics.line_ratio(metrics.MONO)
        self.t_lines = metrics.wrap_text(title, inner, title_size) if title else []
        y = pad + (len(self.t_lines) * title_size * lr + 4 if self.t_lines else 0)
        self.rows = []
        for label, url in rows:
            ll = metrics.wrap_text(label, inner, label_size) if label else []
            ul = metrics.wrap_text(url, inner, size, metrics.MONO)
            self.rows.append((ll, ul, y))
            y += len(ll) * label_size * lr + len(ul) * size * lm + 7
        self.n_lines = metrics.wrap_text(note, inner, label_size) if note else []
        if self.n_lines:
            self.n_y = y
            y += len(self.n_lines) * label_size * lr + 3
        self.h = y + pad - 4
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        bg, fs = (th.soft, "solid") if self.fill == "soft" else (th.fill, "hachure")
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=self.sw, dash=self.dash)
            if self.t_lines:
                cv.text(x + pad, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            for ll, ul, ry in self.rows:
                yy = y + ry
                if ll:
                    cv.text(x + pad, yy, "\n".join(ll), size=self.label_size, color=MUTED)
                    yy += len(ll) * self.label_size * metrics.line_ratio()
                cv.text(x + pad, yy, "\n".join(ul), size=self.size, color=th.deep, font=metrics.MONO)
            if self.n_lines:
                cv.text(x + pad, y + self.n_y, "\n".join(self.n_lines), size=self.label_size, color=MUTED)
        cv.register("urlbox", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


def flow_row(cv, x, y, w, steps, th, *, h=96, size=16, tip=28, sub_size=14):
    """Horizontal chevron process: steps = [(title, sub)]; returns bottom y."""
    n, gap = len(steps), 6
    sw = (w - (n - 1) * gap) / n
    for i, (t, s) in enumerate(steps):
        block_arrow(cv, x + i * (sw + gap), y, sw, h, t, th=th, size=size, tip=tip, notch=i > 0, sub=s, sub_size=sub_size)
    return y + h


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Ways to build on Microsoft Foundry",
                                "Portal, SDKs, REST, azd, VS Code, Canvas, coding agents, LangChain and IaC - one layered picture  |  part 1 of 2  |  as of 2026-11-03",
                                w=W)
    y = bottom + 26
    legend(cv, 0, y, [("Human surfaces", "green"), ("Code surfaces", "indigo"), ("Automation and infrastructure", "grape"), ("AI-assisted", "orange"),
                      ("Foundry resource and project", "blue"), ("Endpoints", "gray"), ("Identity and auth", "red")])
    y += 54
    y = s_glance(cv, y) + 60
    y = s_hero(cv, y) + 80
    y = s_matrix(cv, y) + 80
    y = s_sdk(cv, y) + 80
    y = s_auth(cv, y) + 80
    y = s_flows(cv, y) + 70
    y = s_notes(cv, y) + 60
    sources(cv, 0, y, [
        ("What is Microsoft Foundry? (Choose your developer surface)", WHAT),
        ("Microsoft Foundry SDKs and endpoints", SDK),
        ("Set up your developer environment (CLI, SDK, Dev Pack)", INSTALL),
        ("Develop agents with the Azure Developer CLI", AZD),
        ("Install the azd Foundry extensions", AZD_EXT),
        ("Work in VS Code: Microsoft Foundry Toolkit", VSCODE),
        ("Use the Microsoft Foundry Skill in coding agents", SKILL),
        ("Foundry MCP Server (preview): get started", MCP),
        ("Foundry MCP Server: available tools", MCP_TOOLS),
        ("Foundry Canvas (GitHub Copilot App, preview)", CANVAS),
        ("LangChain and LangGraph with Foundry", LANGCHAIN),
        ("Playgrounds and quick evaluation", PLAYGROUNDS),
        ("Authentication and authorization in Foundry", AUTH),
        ("Foundry Models endpoints", ENDPOINTS),
        ("Role-based access control for Microsoft Foundry", RBAC),
        ("Configure an agent endpoint (protocols, authorization)", learn("agents/how-to/configure-agent")),
        ("Microsoft Foundry product and capability map", CAP),
    ], w=W, cols=3)


# ================================================================================================ 0. glance strip
def s_glance(cv: Canvas, y: float) -> float:
    items = [
        ("One project endpoint", "https://<resource>.services.ai.azure.com/api/projects/<project>", "foundry", "indigo", True),
        ("SDK 2.x in four languages", "Python, C#, JavaScript, Java: a project client plus an OpenAI-compatible client", "sdk", "indigo", False),
        ("Entra first", "API keys are not accepted for agents, evaluations or the Toolbox", "key", "red", False),
        ("azd ai: seven core extensions", "microsoft.foundry bundle, preview-labelled; four more install separately", "azd", "grape", False),
        ("79 tools, 17 categories", "Foundry MCP Server at mcp.ai.azure.com (preview)", "mcp", "orange", False),
        ("2.x = new portal", "match the SDK major to the portal; 1.x = classic", "versions", "gray", False),
    ]
    w, gap = 470, 36
    boxes = []
    for lab, sub, ic, th, mono in items:
        b = Box(w, lab, sub=sub, theme=th, fill="hatch", icon=ic, icon_pos="left", icon_size=36, size=20, sub_size=14, min_h=112, sw=2.5)
        boxes.append(b)
    hh = max(b.h for b in boxes)
    for i, b in enumerate(boxes):
        b.place(cv, i * (w + gap), y, h=hh)
    return y + hh


# ================================================================================================ 1. hero: layered picture
def s_hero(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "The layered picture: surface -> SDK or API -> endpoint -> Foundry", w=W,
                   sub="Each row is one family of surfaces and what it talks to. Dashed arrows reach the control plane. Learn: Choose your developer surface; Foundry SDKs and endpoints; Authentication and authorization")
    top = y + 128
    LW = 2300
    PAD = 16
    TAGW, SW, APIW, EPW, G1 = 230, 700, 520, 690, 56
    X_TAG = PAD
    X_S = X_TAG + TAGW + 24
    X_API = X_S + SW + G1
    X_EP = X_API + APIW + G1
    FX, FWID = 2430, 570

    # ---- column headers
    for lab, x0, w0, th in (("Surface: where you work", X_S, SW, "gray"), ("SDK, API or protocol", X_API, APIW, "gray"), ("Endpoint", X_EP, EPW, "gray")):
        c = Chip(lab, theme=th, size=18, fill="solid")
        c.place(cv, x0 + (w0 - c.w) / 2, top - 48)
    c = Chip("Microsoft Foundry", theme="blue", size=18, fill="solid")
    c.place(cv, FX + (FWID - c.w) / 2, top - 48)

    def tag(name, sub, icon, th):
        return Box(TAGW, name, sub=sub, theme=th, fill="hatch", icon=icon, icon_pos="top", icon_size=34, size=20, sub_size=14, sw=3)

    def surf_row(specs, th, *, w_total=SW, gap=14):
        n = len(specs)
        bw = (w_total - (n - 1) * gap) / n
        out = []
        for lab, sub, ic, badge in specs:
            out.append((Box(bw, lab, sub=sub, theme=th, fill="solid", icon=ic, icon_pos="top", icon_size=32, size=17, sub_size=13, sw=2), badge))
        return out

    def plain(w, lab, sub, th="gray", fill="soft", dash="solid", size=17, sub_size=14, icon=None):
        return Box(w, lab, sub=sub, theme=th, fill=fill, dash=dash, size=size, sub_size=sub_size, icon=icon, icon_pos="left" if icon else "top", icon_size=30)

    lanes = []

    # ---- lane 1 human
    lanes.append(dict(
        th="green", plane="data plane",
        tag=tag("Human surfaces", "you click, type and watch", "users", "green"),
        surf=surf_row([("Foundry portal + playgrounds", "ai.azure.com; New Foundry toggle", "foundry", None),
                       ("Foundry Toolkit for VS Code", "Agent Builder, Agent Inspector, evals, traces", "vscode", None),
                       ("Foundry Canvas", "side panel in GitHub Copilot App", "copilot", "preview")], "green"),
        api=plain(APIW, "UI first, code when you are ready", "playgrounds export code; Agent Builder generates client code"),
        ep=plain(EPW, "Your Foundry project", "the playground's 'Open in VS Code (for the Web)' imports the endpoint and key into a workspace"),
    ))
    # ---- lane 2 code
    chips = ChipFlow([Chip("Foundry SDK 2.x", theme="indigo", size=16, icon="sdk", icon_size=30), Chip("OpenAI SDK", theme="indigo", size=16, icon="openai", icon_size=30),
                      Chip("Anthropic SDK", theme="indigo", size=16, icon="claude", icon_size=30),
                      Chip("Foundry Tools SDKs", theme="indigo", size=16, icon="ai-services", icon_size=30),
                      Chip("REST v1 (no api-version)", theme="indigo", size=16, icon="api", icon_size=30)], APIW - 32, gap=8)
    lanes.append(dict(
        th="indigo", plane="data plane",
        tag=tag("Code surfaces", "you write application code", "code", "indigo"),
        surf=[(Box(SW, "Your application, service or notebook", sub="the SDK major must match the portal: 2.x = new, 1.x = classic", theme="indigo", fill="solid", icon="app",
                   icon_pos="left", icon_size=34, size=18, sub_size=14, sw=2), None)],
        surf_chips=[Chip("Python", theme="indigo", size=15, icon="python", fill="soft", icon_size=36), Chip("C#", theme="indigo", size=15, icon="dotnet", fill="soft", icon_size=36),
                    Chip("JavaScript", theme="indigo", size=15, icon="js", fill="soft", icon_size=36), Chip("Java", theme="indigo", size=15, icon="java", fill="soft", icon_size=36)],
        api=("panel", "Pick the client for the job", chips),
        ep=UrlBox(EPW, None, [("Project endpoint (agents, evals, tools, Responses)", "https://<resource>.services.ai.azure.com/api/projects/<project>"),
                              ("OpenAI v1 (embeddings, Chat Completions, lowest latency)", "https://<resource>.openai.azure.com/openai/v1"),
                              ("Anthropic Messages route (Claude)", "https://<resource>.services.ai.azure.com/anthropic"),
                              ("Foundry Tools (Vision, Speech, Language ...)", "https://<resource>.cognitiveservices.azure.com/")], th="gray", size=13, title_size=17),
    ))
    # ---- lane 3 frameworks
    lanes.append(dict(
        th="indigo", plane="data plane",
        tag=tag("Frameworks", "you orchestrate with a library", "workflow", "indigo"),
        surf=surf_row([("LangChain / LangGraph", "langchain-azure-ai (Python 3.11+)", "langgraph", None),
                       ("Microsoft Agent Framework", "open source: C#/.NET and Python", "agent", None)], "indigo"),
        api=plain(APIW, "Responses API through the project endpoint", "Agent Framework: FoundryChatClient; LangChain: agents, chat_models, tools, callbacks"),
        ep=plain(EPW, "Project endpoint", "AZURE_AI_PROJECT_ENDPOINT; Responses at {project_endpoint}/openai/v1/responses"),
    ))
    # ---- lane 4 terminal
    lanes.append(dict(
        th="grape", plane="data plane",
        tag=tag("Terminal and CI", "you script, test and deploy", "devops", "grape"),
        surf=surf_row([("Azure Developer CLI", "azd ai extensions: the microsoft.foundry bundle", "azd", "preview"),
                       ("Foundry DevPack", "one command installs azd, the Skill and the Toolkit", "gear", "preview")], "grape"),
        api=plain(APIW, "azd ai agent | project | toolbox | skill ...", "one azure.yaml describes project, agents, toolbox, skills and routines"),
        ep=plain(EPW, "Project endpoint", "azd ai project set <endpoint>, or the FOUNDRY_PROJECT_ENDPOINT environment variable"),
    ))
    # ---- lane 5 AI-assisted
    lanes.append(dict(
        th="orange", plane="data plane + deploy",
        tag=tag("AI-assisted", "your coding agent drives Foundry", "github", "orange"),
        surf=surf_row([("GitHub Copilot, Claude Code", "coding agents with the Microsoft Foundry Skill", "github", None),
                       ("Azure Skills Plugin", "bundles the skill, Azure MCP and Foundry MCP", "mcp", None)], "orange"),
        api=plain(APIW, "Foundry Skill + MCP tools", "the agent runs azd and the Foundry MCP Server's read and write tools; review cost-bearing steps first"),
        ep=plain(EPW, "Foundry MCP Server (preview): https://mcp.ai.azure.com", "cloud-hosted MCP over HTTP; Entra on-behalf-of; no private link"),
    ))
    # ---- lane 6 infrastructure
    chips6 = ChipFlow([Chip("Bicep / ARM", theme="grape", size=16, icon="template-specs", icon_size=30), Chip("Terraform", theme="grape", size=16, icon="code", icon_size=30),
                       Chip("Azure CLI: az cognitiveservices", theme="grape", size=16, icon="gear", icon_size=30),
                       Chip("azure-mgmt-cognitiveservices", theme="grape", size=16, icon="python", icon_size=30)], SW - 20, gap=8)
    lanes.append(dict(
        th="grape", plane="control plane", dashed=True,
        tag=tag("Infrastructure", "you provision and govern", "management-group", "grape"),
        surf=[("panel", "Infrastructure as code and CLI", chips6)],
        api=plain(APIW, "Azure Resource Manager", "Microsoft.CognitiveServices/accounts: kind AIServices, projects, deployments, connections"),
        ep=plain(EPW, "Control plane", "Azure RBAC actions; the data plane is authorised separately (dataActions)"),
    ))

    # ---- measure lane heights
    def panel_h(spec):
        kind, title, ch = spec
        tw, th_ = metrics.text_size(title, 17)
        return 14 + th_ + 10 + ch.h + 14

    heights = []
    for ln in lanes:
        sh = max(b.h for b, _ in ln["surf"]) if isinstance(ln["surf"][0][0], Rect2) else panel_h(ln["surf"][0])
        if ln.get("surf_chips"):
            sh += 12 + max(c.h for c in ln["surf_chips"])
        ah = panel_h(ln["api"]) if isinstance(ln["api"], tuple) else ln["api"].h
        h = max(sh, ah, ln["ep"].h, ln["tag"].h, 134)
        heights.append(h)

    ly = top
    mids = []
    spans = []
    for ln, hh in zip(lanes, heights):
        th = ln["th"]
        with cv.panel(0, ly, w=LW, h=hh + 2 * PAD, title=None, theme=th, style="dotted", fill="soft", pad=PAD, sw=2.5):
            pass
        spans.append((ly, ly + hh + 2 * PAD))
        iy = ly + PAD
        ln["tag"].place(cv, X_TAG, iy, h=hh)
        # surfaces
        if isinstance(ln["surf"][0][0], str):
            kind, title, ch = ln["surf"][0]
            with cv.group():
                cv.rect(X_S, iy, SW, hh, stroke=theme(th).stroke, fill="#ffffff", style="solid", sw=2, dash="dashed")
                cv.text(X_S + 14, iy + 12, title, size=17, color=theme(th).deep)
                ch.place(cv, X_S + 14, iy + 12 + 17 * metrics.line_ratio() + 10)
        else:
            sx = X_S
            extra = 0
            if ln.get("surf_chips"):
                extra = 12 + max(c.h for c in ln["surf_chips"])
            for b, badge in ln["surf"]:
                b.place(cv, sx, iy, h=hh - extra)
                if badge:
                    draw_badge(cv, b.right - 82, b.y - 12, badge)
                sx += b.w + 14
            if ln.get("surf_chips"):
                cx = X_S
                for c in ln["surf_chips"]:
                    c.place(cv, cx, iy + hh - max(cc.h for cc in ln["surf_chips"]))
                    cx += c.w + 12
        # api
        if isinstance(ln["api"], tuple):
            kind, title, ch = ln["api"]
            with cv.group():
                cv.rect(X_API, iy, APIW, hh, stroke=theme(th).stroke, fill=theme("gray").soft, style="solid", sw=2)
                cv.text(X_API + 16, iy + 14, title, size=17, color=theme(th).deep)
                ch.place(cv, X_API + 16, iy + 14 + 17 * metrics.line_ratio() + 10)
        else:
            ln["api"].place(cv, X_API, iy, h=hh)
        ln["ep"].place(cv, X_EP, iy, h=hh)
        mid = iy + hh / 2
        mids.append(mid)
        arrow(cv, [(X_S + SW + 6, mid), (X_API - 6, mid)], sw=3, end_head="arrow", color=theme(th).stroke)
        arrow(cv, [(X_API + APIW + 6, mid), (X_EP - 6, mid)], sw=3, end_head="arrow", color=theme(th).stroke)
        ly += hh + 2 * PAD + 14
    bottom = ly - 14

    # ---- Foundry panel
    with cv.panel(FX, top, w=FWID, h=bottom - top, title="Foundry resource", sub="Microsoft.CognitiveServices/accounts, kind AIServices", theme="blue", style="solid",
                  fill="soft", pad=18, title_size=26, sub_size=14, sw=3):
        pass
    cards_top = top + 92
    p_bottom = spans[4][1]
    with cv.panel(FX + 18, cards_top, w=FWID - 36, h=p_bottom - cards_top, title="Foundry project (data plane)", theme="green", style="dashed", fill="none", pad=14,
                  title_size=20, sw=2.5):
        pass
    cw_ = FWID - 36 - 28
    specs = [
        ("Foundry Models", "blue", "openai", ["Call a deployment by name: model = the deployment name", "Responses and more on the project endpoint; embeddings go to /openai/v1"]),
        ("Agents", "green", "agent", ["Prompt and hosted agents, versioned, on the Responses API", "Every agent also gets its own stable endpoint under {project_endpoint}/agents/{name}"]),
        ("Platform tools and Toolbox", "orange", "toolbox-icon", ["File search, code interpreter, web search, memory, SharePoint, WorkIQ, Fabric IQ, MCP",
                                                                  "Toolbox: one managed MCP endpoint (Entra only)"]),
        ("Knowledge, files and data", "teal", "ai-search", ["Foundry IQ knowledge bases, vector stores, indexes, datasets, files", "Memory stores (memory is preview)"]),
        ("Evaluations, tracing and tuning", "violet", "app-insights", ["Cloud evaluations, tracing with Application Insights", "Fine-tuning jobs; connections and deployments are project resources too"]),
    ]
    avail = p_bottom - cards_top - 14 - 52
    for bs in (16, 15, 14):
        pcards = [Card(cw_, t, b, theme=th, icon=ic, body_size=bs, title_size=bs + 3, pad=11, icon_size=28) for t, th, ic, b in specs]
        tot = sum(c.h for c in pcards) + 10 * (len(pcards) - 1)
        if tot <= avail:
            break
    extra = max(0.0, (avail - tot) / len(pcards))
    yy = cards_top + 52
    for c in pcards:
        c.place(cv, FX + 32, yy, h=c.h + extra)
        yy += c.h + 10
    cp_top, cp_bot = spans[5]
    cp = Card(FWID - 36, "Resource (control plane)", ["Projects, deployments, connections, RBAC and networking: set through ARM, Bicep, Terraform and the CLI",
                                                     "Azure RBAC actions here; the data plane is authorised separately (dataActions)"],
              theme="grape", icon="management-group", body_size=15, title_size=18, pad=12, icon_size=30, dash="dashed")
    cp.place(cv, FX + 18, cp_top + 2, h=cp_bot - cp_top - 20)

    # ---- arrows into Foundry
    for ln, mid in zip(lanes, mids):
        th = theme(ln["th"])
        ctrl = ln.get("dashed")
        arrow(cv, [(LW + 8, mid), (FX - 6, mid)], sw=3, end_head="arrow", color=th.stroke, dash="dashed" if ctrl else "solid", label=ln["plane"], label_size=13,
              label_color=th.deep, label_wrap=100)
    return bottom


# ================================================================================================ 2. surface x persona matrix
def s_matrix(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Which surface for which persona", w=W,
                   sub="Learn: 'Choose your developer surface' (what-is-foundry) and the 'Who it's for' column of the product and capability map  |  [v] = listed by Learn, [~] = our reading")
    top = y + 100
    L = lambda text, url: dict(text=text, link=url, color=LINK)
    V, H = CHECK, PARTIAL
    rows = [
        [("Foundry portal + playgrounds", "green"), V, "", "", "", "Exploring models, prototyping prompts, building prompt agents without code", "GA; Video playground preview; Audio playground is classic-only",
         L("Playgrounds and quick evaluation", PLAYGROUNDS)],
        [("SDKs: Python, C#, JavaScript, Java", "indigo"), "", V, "", "", "Building applications", "2.x targets the new portal; 1.x is classic",
         L("Foundry SDKs and endpoints", SDK)],
        [("Azure Developer CLI + azd ai", "grape"), "", "", "", V, "Scaffolding, running, testing and deploying hosted-agent projects from the terminal",
         "Preview-labelled extensions (docs disagree on GA)", L("Develop agents with azd", AZD)],
        [("VS Code: Foundry Toolkit", "green"), "", V, "", "", "Building and debugging agents in the editor", "Some experiences preview",
         L("Work in VS Code", VSCODE)],
        [("Coding agents + MCP", "orange"), "", V, "", "", "Driving Foundry from GitHub Copilot or Claude Code with the Foundry Skill and the MCP server",
         "Foundry MCP Server is preview", L("Use the Foundry Skill in coding agents", SKILL)],
        [("LangChain / LangGraph", "indigo"), "", "", V, "", "Teams already on LangChain or LangGraph: models, tools, memory and tracing", "langchain-azure-ai",
         L("LangChain and LangGraph with Foundry", LANGCHAIN)],
        [("Foundry Canvas", "green"), "", "", H, "", "Guided visual build and deploy of hosted agents inside GitHub Copilot App", "Preview",
         L("Foundry Canvas", CANVAS)],
    ]
    cols = [("Surface", 410), ("Anyone evaluating", 130), ("Application developer", 150), ("Agent developer", 130), ("Platform engineer", 130),
            ("Best for (Learn)", 780), ("Status", 560), "Start page"]
    t = Table(cols, rows, w=W, theme="gray", size=15, head_size=16, pad_y=9, align=["left", "center", "center", "center", "center", "left", "left", "left"],
              first_col_theme=None)
    t.place(cv, 0, top)
    cv.text(0, t.bottom + 10, "The capability map lists one persona per product; Canvas is not in that table, so [~] is our reading of 'hosted agents'. "
                              "Many developers combine surfaces, for example prototyping in the portal and then moving to code.", size=14, color=MUTED)
    return t.bottom + 34


# ================================================================================================ 3. SDKs and endpoints
def s_sdk(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "SDKs and endpoints: one project endpoint, a few deliberate exceptions", w=W,
                   sub="Learn: Microsoft Foundry SDKs and endpoints (how-to/develop/sdk-overview) and Foundry Models endpoints  |  versions as shown on Learn, as of 2026-11-03")
    top = y + 100
    LW_ = 1900
    sdk_rows = [
        [("Foundry SDK", "indigo"), "Thin client over all Foundry project APIs: Foundry Models plus platform tools (file search, code interpreter, web search, memory, SharePoint, WorkIQ, Fabric IQ, MCP), "
                                    "agents, evaluations, tracing, fine-tuning",
         "https://<resource>.services.ai.azure.com/api/projects/<project>"],
        [("Agent Framework", "indigo"), "Unified multi-agent orchestration for hosted agents; C#/.NET and Python; the foundry package depends on the Foundry SDK",
         "Responses API in the project endpoint, via FoundryChatClient"],
        [("OpenAI SDK", "indigo"), "Full OpenAI surface, best latency, embeddings, Chat Completions for models sold by Azure. No agents, evaluations or Foundry-only platform tools",
         "https://<resource>.openai.azure.com/openai/v1  (also accepted: <resource>.services.ai.azure.com/openai/v1/)"],
        [("Anthropic SDK", "indigo"), "Claude models deployed in Foundry through the Messages API (not OpenAI-compatible); no native C# client, use REST",
         "https://<resource>.services.ai.azure.com/anthropic"],
        [("Foundry Tools SDKs", "indigo"), "Prebuilt Vision, Speech, Language, Translator, Document Intelligence and Content Safety",
         "https://<resource>.cognitiveservices.azure.com/ (Speech and Translator have regional or global hosts)"],
    ]
    mono_rows = []
    for name, what, ep in sdk_rows:
        mono_rows.append([name, what, dict(text=ep, color="#1864ab")])
    t1 = Table([("SDK", 210), ("What it is for", 880), "Endpoint"], mono_rows, w=LW_, theme="indigo", size=14, head_size=16, pad_y=7, title="Five SDK families",
               title_size=20)
    t1.place(cv, 0, top)
    lang_rows = [
        [("Python", "yellow"), "azure-ai-projects>=2.3.0 + openai>=3.0.0", "Python 3.10+", "1.x = classic (1.0.0)"],
        [("JavaScript", "yellow"), "@azure/ai-projects 2.8.0 + @azure/identity", "Node.js 22+", "1.0.1 = classic"],
        [("C# / .NET", "violet"), "Azure.AI.Projects + Azure.AI.Projects.Agents + Azure.AI.Extensions.OpenAI (2.0.0 GA)", ".NET 8+",
         "1.1.0 = classic; do not mix in the preview Azure.AI.Projects.OpenAI"],
        [("Java", "orange"), "com.azure:azure-ai-projects 2.3.0 + azure-ai-agents 2.3.0", "JDK 17+", "-"],
    ]
    t2 = Table([("Language", 130), ("Packages (Foundry SDK 2.x)", 760), ("Runtime", 130), "Classic portal (1.x)"], lang_rows, w=LW_, theme="indigo", size=14, head_size=16,
               pad_y=7, title="Foundry SDK 2.x by language", title_size=20)
    t2.place(cv, 0, t1.bottom + 34)
    n = Note(LW_, "Versions move quickly: Learn shows these numbers as of 2026-11-03, while the Foundry DevBlog (August 2026) quoted slightly different ones. Treat '2.x' as the "
                  "contract and check the SDK page for the exact version. azure-ai-inference retired on 2026-08-26 (migrate to the openai package).",
             kind="warn", title="Version numbers are a moving target", src=[("Microsoft Foundry SDKs", SDK), ("Migrate from the classic portal", NAV)])
    n.place(cv, 0, t2.bottom + 24)
    left_bottom = n.bottom

    # ---- right: two clients
    RX = LW_ + 60
    RW = W - RX
    with cv.panel(RX, top, w=RW, title="Two clients, one SDK", sub="Most apps use both", theme="indigo", style="dashed", fill="soft", pad=20, title_size=24, sub_size=15) as rp:
        pc = Box(RW - 40, "Project client", sub="Foundry-native: connections, project properties, tracing, create and version agents", theme="blue", fill="hatch", icon="foundry",
                 icon_pos="left", icon_size=32, size=19, sub_size=14)
        pc.place(cv, rp.ix, rp.iy + 4)
        oc = Box(RW - 40, "OpenAI-compatible client", sub="Responses, conversations, agent runs, evaluations, fine-tuning; served on the project endpoint's /openai route", theme="green",
                 fill="hatch", icon="openai", icon_pos="left", icon_size=32, size=19, sub_size=14)
        oc.place(cv, rp.ix, pc.bottom + 84)
        connect(cv, pc, oc, a_side="bottom", b_side="top", label="project.get_openai_client()", label_size=15, sw=3, gap=6)
        code = [("Python", "project.get_openai_client()"), ("JavaScript", "project.getOpenAIClient()"),
                ("C#", "projectClient.ProjectOpenAIClient"), ("", "  .GetProjectResponsesClientForAgent()"), ("Java", "AgentsClientBuilder -> ResponsesClient")]
        cy = oc.bottom + 22
        fs = 15
        lh = fs * metrics.line_ratio(metrics.MONO)
        bh = 16 + len(code) * (lh + 4) + 14
        with cv.group():
            cv.rect(rp.ix, cy, RW - 40, bh, stroke="#495057", fill="#f8f9fa", style="solid", sw=2)
            ly = cy + 14
            for lang, call in code:
                if lang:
                    cv.text(rp.ix + 14, ly, lang, size=14, color=MUTED)
                cv.text(rp.ix + 120, ly, call, size=fs, font=metrics.MONO, color="#2b8a3e")
                ly += lh + 4
        cv.register("clientcode", rp.ix, cy, RW - 40, bh)
        cv.text(rp.ix, cy + bh + 8, "Learn: Foundry SDKs and endpoints; Migrate to the new agents experience", size=12, color=LINK, link=SDK)
    ex_y = rp.bottom + 26
    ex = Note(RW, "The project endpoint does not currently route embeddings: use the OpenAI endpoint (/openai/v1) for them. An Azure OpenAI resource provides only /openai/v1; "
                  "a Foundry resource provides all the endpoints on this page.", kind="gotcha", title="Exceptions to 'one endpoint'", src=[("Microsoft Foundry SDKs", SDK)])
    ex.place(cv, RX, ex_y)
    return max(left_bottom, ex.bottom)


# ================================================================================================ 4. authentication per surface
def s_auth(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Authentication per surface", w=W,
                   sub="Learn: Authentication and authorization in Foundry; Foundry SDKs; Foundry MCP Server security  |  Foundry User on the project is the day-to-day role; roles as renamed (formerly Azure AI ...)")
    top = y + 100
    # ---- left: token flow
    SPAC, HW = 330, 240
    sq = Sequence(cv, 0, top, [("Microsoft Entra ID", "red", "entra-connect"), ("Your app (SDK or REST)", "indigo", "app"), ("Foundry project endpoint", "blue", "foundry")],
                  spacing=SPAC, head_w=HW, head_h=60, step=64, size=16, label_size=15)
    sq.msg(1, 0, "1  DefaultAzureCredential (or any TokenCredential) asks for a token")
    sq.msg(0, 1, "2  access token for scope https://ai.azure.com/.default", dash="dashed")
    sq.msg(1, 2, "3  request with Authorization: Bearer <token>")
    sq.note(1, 2, "The caller needs the Foundry User role on the project. API keys are not accepted for agents, evaluations or the Toolbox.", kind="gotcha", size=14)
    sq.msg(2, 1, "4  response", dash="dashed")
    sb = sq.end()
    LWID = HW + 2 * SPAC
    cv.text(0, sb + 8, "Learn: Authentication and authorization in Foundry", size=12, color=LINK, link=AUTH)
    left_bottom = sb + 30

    # ---- right: table
    TX = LWID + 70
    TW = W - TX
    rows = [
        [("Foundry portal", "green"), "Signed-in Entra user; the playground uses project connection mode", "n/a",
         "Foundry User on the project to build; Foundry Project Manager to publish or deploy hosted agents and create connections; Foundry Account Owner to create the resource and projects"],
        [("Foundry SDK / REST: project endpoint", "indigo"), "DefaultAzureCredential or any TokenCredential", "https://ai.azure.com/.default",
         "Foundry User on the project. Keys are not accepted for agents, evaluations or the Toolbox"],
        [("OpenAI SDK: /openai/v1", "indigo"), "Entra bearer token or an API key (api_key=, api-key or Bearer)", "https://ai.azure.com/.default",
         "Foundry User on the account to call deployments (also for managed compute)"],
        [("Anthropic SDK", "indigo"), "Entra token provider", "https://ai.azure.com/.default", "Foundry User"],
        [("A published agent's own endpoint", "indigo"), "Entra token for the Foundry resource: the AzureRbac scheme (alias Entra); Bot Service schemes when published to Teams or M365", "-",
         "Foundry Agent Consumer, or another role with the endpoint permission. API key authentication is not supported"],
        [("azd and Azure CLI", "grape"), "azd auth login; az login", "-",
         "Foundry User to reuse a project; Contributor + Role Based Access Control Administrator to provision and assign roles; Foundry Project Manager to create connections, incl. a Toolbox"],
        [("VS Code Toolkit and Canvas", "green"), "See the Toolkit page; Canvas runs azd underneath", "-", "Not stated on the pages read: follow the Toolkit and Canvas pages"],
        [("LangChain / LangGraph", "indigo"), "Project endpoint: Entra + RBAC; API keys only for direct /openai/v1 endpoints", "-", "Foundry User on the project (project endpoint)"],
        [("Foundry MCP Server (preview)", "orange"), "Entra on-behalf-of (OBO)", "https://mcp.ai.azure.com",
         "Reader for read tools; Contributor for write and delete tools; Owner or User Access Administrator to manage access"],
        [("ARM, Bicep, Terraform, az", "grape"), "Azure RBAC actions (control plane)", "Azure Resource Manager",
         "Foundry Account Owner, Owner or Contributor; Role Based Access Control Administrator (or Owner) for role assignments"],
    ]
    rows = [[r[0], r[1], dict(text=r[2], color="#1864ab"), r[3]] for r in rows]
    t = Table([("Surface", 250), ("Credential", 360), ("Token scope or audience", 310), "Minimum role (as documented)"], rows, w=TW, theme="red", size=14, head_size=16, pad_y=7)
    t.place(cv, TX, top)
    cv.text(TX, t.bottom + 8, "Learn: Authentication and authorization in Foundry; Microsoft Foundry SDKs; Foundry MCP Server security best practices", size=12, color=LINK, link=AUTH)
    ny = max(left_bottom, t.bottom + 34)
    nw = 973
    notes = [
        Note(nw, "API keys are the exception: the auth matrix shows no key support for the Agents service, evaluations or the Toolbox, and the portal GA overview adds the dataset tab "
                 "and Content Understanding as Entra-only, while the matrix shows Content Understanding batch jobs accepting keys. Check the page for your feature.",
             kind="warn", title="Docs disagree: where keys work", src=[("Authentication and authorization", AUTH), ("Portal GA overview", GA)]),
        Note(nw, "Nearly every page uses https://ai.azure.com/.default. One sample on the classic-migration page shows https://cognitiveservices.azure.com/.default for the OpenAI v1 "
                 "client, and the Foundry MCP Server uses https://mcp.ai.azure.com. When a 401 appears, check the scope first.",
             kind="warn", title="Docs disagree: the token scope", src=[("Migrate from the classic portal", NAV), ("Authentication and authorization", AUTH)]),
        Note(nw, "Entra (token) authentication needs a custom subdomain on the resource (customSubDomainName). The Foundry MCP Server cannot reach private-link resources, may process in "
                 "EU or US data centres and has no SLA; Conditional Access applies through a service principal for the MCP app.",
             kind="info", title="Prerequisites and limits", src=[("Foundry MCP Server security", MCP_SEC)]),
    ]
    row(cv, 0, ny, notes, gap=40)
    return ny + max(n.h for n in notes)


# ================================================================================================ 5. flows
def s_flows(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Four paths to a first working agent", w=W,
                   sub="Learn: Set up your developer environment; Foundry SDKs; Use the Foundry Skill; Foundry Canvas  |  tools marked preview are preview as of 2026-11-03")
    y += 100
    paths = [
        ("Fastest: terminal (preview tools)", "grape", [
            ("winget install Microsoft.FoundryDevPack", "macOS and Linux have their own commands"), ("az login / azd auth login", "sign in"),
            ("azd ai agent init", "scaffold the project"), ("azd ai agent run", "run locally"), ("azd up", "provision and deploy")]),
        ("Code path", "indigo", [
            ("AIProjectClient(endpoint, DefaultAzureCredential())", "the project client"), ("project.get_openai_client()", "the OpenAI-compatible client"),
            ("openai.responses.create(model=<deployment>, input=...)", "call a model or an agent")]),
        ("AI-assisted (cost-bearing steps need your review)", "orange", [
            ("Install the Azure Skills Plugin", "skill + Azure MCP + Foundry MCP"), ("The agent loads the Foundry Skill", "plus MCP discovery"), ("It proposes a plan", ""),
            ("You review it", "before anything costs money"), ("It runs azd or MCP write tools", "")]),
        ("Canvas path (preview)", "green", [
            ("GitHub Copilot App", "plugin microsoft-foundry"), ("Choose a project", ""), ("Inspire me", "or Help me decide, Hello world"), ("Inspect Locally", "embedded Agent Inspector"),
            ("Deploy to Foundry", "azd runs underneath")]),
    ]
    for title, th, steps in paths:
        t = cv.text(0, y, title, size=22, color=theme(th).deep)
        by = flow_row(cv, 0, y + 34, W, steps, th, h=104, size=17, sub_size=14)
        y = by + 34
    cv.text(0, y - 14, "Learn: Set up your developer environment, Foundry SDKs, Use the Foundry Skill, Foundry Canvas (see Sources below)", size=12, color=LINK, link=INSTALL)
    return y + 4


# ================================================================================================ 6. notes
def s_notes(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Preview status, caveats and where the docs disagree", w=W)
    y += 64
    nw = 973
    notes = [
        Note(nw, "Preview as labelled on Learn (as of 2026-11-03): the Foundry DevPack, Foundry Canvas, the Foundry MCP Server and the azd Foundry extensions (the Learn "
                 "capability pages list azd without a label, the install pages carry the generic preview banner: draw it as preview-labelled).", kind="preview",
             title="Preview and 'GA?' surfaces", src=[("Install the azd Foundry extensions", AZD_EXT), ("Foundry MCP Server", MCP)]),
        Note(nw, "The capability reference calls Canvas a 'visual surface for composing and inspecting agents'; the Canvas page itself scopes it to hosted agents inside "
                 "the GitHub Copilot App. This canvas follows the page.", kind="warn", title="Docs disagree: what Canvas is", src=[("Foundry Canvas", CANVAS)]),
        Note(nw, "The OpenAI SDK sample uses <resource>.openai.azure.com/openai/v1, the LangChain page uses <resource>.services.ai.azure.com/openai/v1, and the endpoints page says both "
                 "are accepted. Pick one per app and keep the token scope consistent.", kind="warn", title="Docs disagree: OpenAI v1 hostnames", src=[("Foundry Models endpoints", ENDPOINTS)]),
        Note(nw, "Part 2 of this canvas, 'Developer surfaces in detail', covers each surface: portal and playgrounds, REST v1 and ARM, azd extensions, the Dev Pack, "
                 "VS Code Toolkit, Canvas, coding agents with the full MCP tool list, LangChain, and templates and samples.", kind="key", title="Next: the detail"),
        Note(nw, "Prerequisites quoted by the docs: Python 3.10+, .NET 8+ (the hosting examples need the .NET 10 SDK), Node.js 22 (SDK page) or 20+ (install page), JDK 17+, "
                 "Node 18+ and Git for the Foundry Skill. Run az login and azd auth login before the first call.", kind="tip", title="Runtimes",
             src=[("Set up your developer environment", INSTALL)]),
        Note(nw, "Foundry User on the project is enough to build. Creating the Foundry resource or projects needs Foundry Account Owner (just in time through PIM, per Learn), and "
                 "provisioning with azd needs Contributor plus Role Based Access Control Administrator.", kind="info", title="Least privilege first",
             src=[("RBAC for Foundry", RBAC)]),
    ]
    bottom = y
    for i in range(0, len(notes), 3):
        r = notes[i:i + 3]
        hmax = max(n.h for n in r)
        for j, n in enumerate(r):
            n.place(cv, j * (nw + 40), bottom, h=hmax)
        bottom += hmax + 30
    return bottom - 30
