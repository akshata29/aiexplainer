"""Foundry Agent Service overview - the map: agent kinds + decision flow, request path, Responses-based object model vs
classic Assistants, what the service manages, key numbers and the dates that matter. Setup/limits/regions live in part 2."""
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS

META = dict(
    id="agent-service-overview", title="Foundry Agent Service: the map", section="2", group="Agent Service", order=10,
    description="What Foundry Agent Service is: the five REST agent kinds and a decision flow, the request path, the Responses-based object model vs classic Assistants, what the service manages for you, key numbers and the retirement dates.",
    tags=["agent-service", "agents", "responses-api", "object-model", "overview"],
)

W = 3000
OV = learn("agents/overview")
RC = learn("agents/concepts/runtime-components")
LQR = learn("agents/concepts/limits-quotas-regions")
REG_URL = learn("reference/rest/agents-patch-agent-object")


# ---------------------------------------------------------------------------------------------- helpers
def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def ypt(blk, y):
    """Fraction along blk's vertical edge that sits at absolute y (for straight horizontal connectors)."""
    return (y - blk.y) / blk.h


def hdr(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


class StepCard(Rect2):
    """Round numbered marker + title + wrapped text in a hatch card (request-flow legends)."""

    def __init__(self, w, n, title, text, *, theme_name="blue", src=(), size=15):
        self.th = theme(theme_name)
        self.w, self.n, self.title, self.size, self.theme_name = w, n, title, size, theme_name
        self.src = list(src)
        pad = 16
        self.pad, self.d = pad, 34
        inner = (w - 2 * pad - self.d - 12) * 0.965
        self.t_lines = metrics.wrap_text(title, inner, 19)
        self.lines = metrics.wrap_text(text, (w - 2 * pad) * 0.965, size)
        y = pad + max(len(self.t_lines) * 19 * metrics.line_ratio(), self.d) + 8
        self.body_y = y
        y += len(self.lines) * size * metrics.line_ratio()
        self.src_lines = []
        if self.src:
            y += 8
            for label, url in self.src:
                ls = metrics.wrap_text(f"Learn: {label}", (w - 2 * pad) * 0.965, 12)
                self.src_lines.append(("\n".join(ls), url, y))
                y += len(ls) * 12 * metrics.line_ratio() + 2
        self.h = y + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            numbered(cv, x + pad + self.d / 2, y + pad + self.d / 2, self.n, theme=self.theme_name, d=self.d, size=19)
            cv.text(x + pad + self.d + 12, y + pad + 2, "\n".join(self.t_lines), size=19, color=th.deep)
            cv.text(x + pad, y + self.body_y, "\n".join(self.lines), size=self.size, color=INK)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"step:{self.title}", x, y, self.w, H)
        return self


# ---------------------------------------------------------------------------------------------- section 0
def glance(cv, y):
    note = Note(W, "A managed platform for building, deploying and scaling AI agents: any framework, any supported model from the Foundry "
                   "catalog, one entry point for model inference and tools. Preview items carry a Preview badge; "
                   "time-sensitive statements are as of 2026-11-03.",
                kind="key", title="Agent Service is GA - some sub-features are in preview",
                src=[("What is Foundry Agent Service?", OV), ("Quotas and limits", LQR)])
    note.place(cv, 0, y)
    y = note.bottom + 26
    items = [
        ("Agent Runtime", "hosts and scales prompt and hosted agents; manages conversations, tool calls and lifecycle", "agent", "green", None),
        ("Toolboxes", "curate tools once; one managed MCP-compatible endpoint with central auth, governance and versioning", "toolbox", "orange", None),
        ("Models", "Foundry catalog; swap a model without changing agent code", "openai", "blue", None),
        ("Observability", "end-to-end tracing, metrics, evaluations, Application Insights", "app-insights", "violet", None),
        ("Optimization", "agent optimizer: better instructions, skills, tool descriptions and model picks for prompt and hosted agents", "gear", "violet", "preview"),
        ("Identity and security", "Entra identity, RBAC, content filters, virtual network isolation", "managed-identity", "red", None),
        ("Publishing", "versions, stable endpoints, Teams, Microsoft Copilot, Entra Agent Registry", "teams", "gray", None),
    ]
    gap = 28
    bw = (W - gap * (len(items) - 1)) / len(items)
    boxes = [Box(bw, lab, sub=sub, icon=ic, icon_pos="left", theme=th, size=18, sub_size=14, h=130) for lab, sub, ic, th, _ in items]
    r, b = row(cv, 0, y, boxes, gap=gap)
    for bx, it in zip(boxes, items):
        if it[4]:
            badge_on(cv, bx, it[4])
    y = b + 26
    lg = legend(cv, 0, y, [("agents / Agent Service", "green"), ("models", "blue"), ("tools / toolbox / MCP", "orange"),
                           ("knowledge / memory", "teal"), ("observability / evals", "violet"), ("guardrails", "pink"),
                           ("identity / security", "red"), ("networking", "indigo"), ("quota / limits", "yellow"),
                           ("state / data", "cyan"), ("neutral", "gray")], size=15, gap=22)
    bx = lg.right + 50
    for k in ("ga", "preview", "retiring"):
        draw_badge(cv, bx, y - 1, k)
        bx += metrics.line_width(STATUS[k][1], 13) + 18 + 16
    return y + 40


# ---------------------------------------------------------------------------------------------- section 1
def kinds(cv, y):
    y = hdr(cv, y, "1  Pick your agent kind",
            "REST AgentVersion.definition is a union of five kinds (discriminator `kind`): hosted | prompt | workflow | external | voice. "
            "The overview page itself says 'three agent types' (prompt, voice-based prompt, hosted).") + 40
    Y = y
    FW = 1540
    PX, PW = 640, 900
    # --- grouping panels (drawn first so shapes sit on top)
    with cv.panel(PX, Y, w=PW, h=392, title="You run the agent - Foundry runs nothing, or only models and tools", theme="gray",
                  style="dotted", pad=20, title_size=21):
        pass
    with cv.panel(PX, Y + 432, w=PW, h=660, title="Foundry runs the agent - managed endpoint, Entra identity, scaling", theme="green",
                  style="dotted", pad=20, title_size=21):
        pass
    with cv.panel(0, Y + 730, w=570, h=362, title="Legacy", theme="red", style="dashed", pad=20, title_size=21):
        pass

    LX, LW, LH = 1140, 380, 132
    # vertical centres of the decision rows
    c_ext, c_resp = Y + 120, Y + 284
    c_host = Y + 582
    c_voice = c_host + 250
    c_prompt = c_voice + 172

    start = Box(200, "New agent on Foundry", sub="what are you building?", theme="gray", h=92, size=18)
    q1 = Box(330, "Will Foundry run the agent?", shape="diamond", theme="gray", h=176, size=17)
    q2 = Box(300, "What do you want from Foundry?", shape="diamond", theme="gray", h=170, size=17)
    q3 = Box(300, "Need your own code, framework or protocol?", shape="diamond", theme="gray", h=170, size=17)
    q4 = Box(300, "Real-time spoken conversation?", shape="diamond", theme="gray", h=170, size=17)
    qx = PX + 40
    q2.place(cv, qx, c_resp - q2.h / 2)
    q3.place(cv, qx, c_host - q3.h / 2)
    q4.place(cv, qx, c_voice - q4.h / 2)
    cy1 = (c_resp + c_host) / 2
    q1.place(cv, 262, cy1 - q1.h / 2)
    start.place(cv, 0, cy1 - start.h / 2)

    leaf_specs = [
        (c_ext, "External agent", "register only: it runs anywhere; Foundry keeps metadata for the trace view and evals", "agent", "gray", "dashed", "preview"),
        (c_resp, "Responses API (ephemeral agent)", "definition lives in your app, nothing persisted; Foundry models, tools, identity", "openai", "blue", "solid", None),
        (c_host, "Hosted agent", "your code as a container or zip; per-session VM sandbox; managed endpoint and identity", "container-apps", "green", "solid", None),
        (c_voice, "Voice-based prompt agent", "model + audio + tools over Voice Live (WebSocket); kind: voice", "speech", "green", "solid", "preview"),
        (c_prompt, "Prompt agent", "config only: model + instructions + tools; Foundry runs it; kind: prompt", "agent", "green", "solid", None),
    ]
    leaves = []
    for cy, lab, sub, ic, th, dash, badge in leaf_specs:
        bx = Box(LW, lab, sub=sub, icon=ic, icon_pos="left", theme=th, dash=dash, h=LH, size=18, sub_size=14).place(cv, LX, cy - LH / 2)
        if badge:
            badge_on(cv, bx, badge)
        leaves.append(bx)
    ext, resp, host, voice, prompt = leaves

    wf = Box(530, "Workflow agent (kind: workflow)", sub="CSDL YAML. Visual designer and in-portal run retire on 2026-12-01; YAML keeps running as a hosted agent",
             icon="workflow", icon_pos="left", theme="red", dash="dashed", h=150, size=18, sub_size=14).place(cv, 20, Y + 800)
    badge_on(cv, wf, "retiring")
    mig = Box(530, "Migrate to", sub="Microsoft Agent Framework (recommended) | Azure Logic Apps | A2A direct", icon="logic-apps",
              icon_pos="left", theme="gray", h=84, size=17, sub_size=14).place(cv, 20, Y + 985)

    # --- arrows
    connect(cv, start, q1, a_side="right", b_side="left", sw=2.5)
    connect(cv, q1, q2, a_side="top", b_side="left", route="elbow", label="no - it runs elsewhere", label_size=15, label_t=0.6, sw=2.5)
    connect(cv, q1, q3, a_side="bottom", b_side="left", route="elbow", label="yes", label_size=15, label_t=0.6, sw=2.5)
    connect(cv, q2, resp, a_side="right", b_side="left", label="models + tools", label_size=14, sw=2.5)
    connect(cv, q2, ext, a_side="top", b_side="left", route="elbow", label="traces + evals", label_size=14, label_t=0.62, sw=2.5)
    connect(cv, q3, host, a_side="right", b_side="left", label="yes", label_size=15, sw=2.5)
    connect(cv, q3, q4, a_side="bottom", b_side="top", label="no", label_size=15, sw=2.5)
    connect(cv, q4, voice, a_side="right", b_side="left", label="yes", label_size=15, sw=2.5)
    connect(cv, q4, prompt, a_side="bottom", b_side="left", route="elbow", label="no", label_size=15, label_t=0.62, sw=2.5)
    connect(cv, wf, mig, a_side="bottom", b_side="top", dash="dashed", color="#e03131", sw=2.5)

    # --- compare table (right)
    TX, TW = FW + 60, W - FW - 60
    t_cmp = Table(
        [("", 150), "Prompt agents", "Voice-based prompt agents (preview)", "Hosted agents"],
        [
            ["Authoring surface", "Portal, Azure Developer CLI, SDK or REST", "Agent definition through the portal, SDK or REST",
             "Agent Framework, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK, custom code"],
            ["Foundry models + platform tools", "Yes", "Yes, through Voice Live and configured agent tools", "Yes (via the Responses API on the project endpoint)"],
            ["Skill support", "Yes", "Yes", "Yes"],
            ["Runtime code to maintain", "None", "None for the managed voice orchestration", "Yes - your agent logic"],
            ["Compute to manage", "None, fully managed", "None, fully managed", "Container compute, Foundry-managed"],
            ["Managed endpoint", "Yes", "Yes - real-time WebSocket", "Yes"],
            ["Autoscale", "Automatic, Foundry-managed; scales with request volume", "Managed by Foundry and Voice Live",
             "Automatic, Foundry-managed; scales container instances per session and request volume"],
            ["Agent identity (Entra)", "Yes", "Yes", "Automatic, dedicated per agent"],
            ["Cost model", "Per-call inference + tool usage", "Voice Live and model usage; see service pricing", "Per-call inference + tool usage + container compute"],
            ["Best for", "Fast start; production agents without custom orchestration", "Real-time spoken interactions without hosting voice orchestration code",
             "Agents that call into custom code; secondarily custom orchestration logic"],
        ], w=TW, theme="green", size=14, head_size=15, first_col_theme="green", title="Compare the three kinds Foundry runs (overview page)",
        title_size=22)
    t_cmp.place(cv, TX, Y)
    src = cv.text(TX, t_cmp.bottom + 8, "Learn: What is Foundry Agent Service? - Compare agent types", size=12, color=LINK, link=OV)

    # --- dates that matter (fills the right column under the compare table)
    ty = src.bottom + 56
    cv.text(TX, ty, "Dates that matter (as of 2026-11-03)", size=24, color=theme("red").deep)
    t_end = timeline(cv, TX, ty + 44 + 170, TW, [
        ("2026-11-03", "Today", "Agent Service is GA; voice-based agents, the Copilot harness, routines, external agents and the optimizer are preview"),
        ("2026-12-01", "Workflows retire", "Visual designer and in-portal run end; YAML workflows deployed as a hosted agent keep running. Move to Microsoft Agent Framework (recommended), Logic Apps or A2A"),
        ("2027-04-30", "Custom agent registration: deprecation scheduled", "Foundry Control Plane custom agents (traffic through an AI Gateway): no new ones can be added. Register External agents and keep the OpenTelemetry agent ID"),
    ], size=17, label_w=400, theme="red")
    l1 = cv.text(TX, t_end + 8, "Learn: Workflows", size=12, color=LINK, link=learn("agents/concepts/workflow"))
    cv.text(TX + 150, t_end + 8, "Learn: Register external agents", size=12, color=LINK, link=learn("agents/how-to/register-external-agent"))
    bottom = max(Y + 1092, l1.bottom)

    # --- details table (full width)
    y2 = bottom + 50
    cv.text(0, y2, "The six ways to build an agent, in detail", size=24, color=theme("green").deep)
    y2 += 40
    t_kinds = Table(
        [("Kind", 330), ("Defined by", 520), ("Who runs it", 520), ("Status and notes (as of 2026-11-03)", 800), ("Choose it when", 830)],
        [
            [("Prompt agent\nkind: prompt", "green"), "Config only: model + instructions + tools (+ skills, toolbox)",
             "Foundry: default runtime, or the optional Microsoft Copilot harness (preview)", "Core service", "You want the least to manage; no code or containers"],
            [("Voice-based prompt agent\nkind: voice ('voice-first' alias)", "green"), "Model + instructions + audio + greeting + tools",
             "Foundry + the Voice Live runtime over WebSocket",
             "Preview on the Learn voice pages. The Build-2026 blog lists 'Voice Live prompt agents: GA' - the docs do not say whether these are the same product",
             "Real-time spoken conversations without hosting a speech pipeline"],
            [("Hosted agent\nkind: hosted", "green"), "Your code (Agent Framework, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK, custom) as a container image or a zip of source",
             "Foundry: per-session VM-isolated sandbox, managed endpoint and identity",
             "The concept page carries no preview banner (inferred GA); the Build-2026 blog said GA was expected by early July 2026 (blog-sourced)",
             "You own the orchestration code, need custom protocols (webhooks, WebSocket voice, AG-UI) or runtime control"],
            [("Responses API 'ephemeral agent'\n(no REST kind)", "blue"), "The definition lives in your app; nothing is persisted in Foundry",
             "You, on any host", "No Copilot harness and no prompt-agent optimizer - both need a saved version",
             "You already run the agent elsewhere but want Foundry models, tools and identity"],
            [("External agent\nkind: external", "gray"), "Registration metadata only (otel_agent_id)", "Not Foundry - runs anywhere",
             "Preview. The recommended path for observability, evaluation and optimization of non-Foundry agents",
             "You want the trace view and trace-based evals for an agent that runs outside Foundry"],
            [("Workflow agent\nkind: workflow", "red"), "CSDL YAML definition", "Foundry workflow engine",
             "RETIRING Dec 1, 2026: 'no longer a separate agent type'. Azure Government lists Workflows = Preview",
             "Migrate to Microsoft Agent Framework (recommended), Azure Logic Apps or A2A"],
        ], w=W, theme="green", size=14, head_size=15)
    t_kinds.place(cv, 0, y2)
    cv.text(0, t_kinds.bottom + 8, "Learn: What is Foundry Agent Service?", size=12, color=LINK, link=OV)
    cv.text(260, t_kinds.bottom + 8, "Learn: Agent object schema (REST)", size=12, color=LINK, link=REG_URL)
    cv.text(560, t_kinds.bottom + 8, "Learn: Register external agents", size=12, color=LINK, link=learn("agents/how-to/register-external-agent"))
    return t_kinds.bottom + 60


# ---------------------------------------------------------------------------------------------- section 2
def request_path(cv, y):
    y = hdr(cv, y, "2  How a request flows through the service",
            "Client -> project endpoint -> the runtime for that agent kind -> model and tools -> state and traces. "
            "The numbers match the five step cards underneath.") + 40
    Y = y
    CW_ = 330
    PX, PW = 450, 1470
    RX = 2050
    RW = W - RX
    TOP = Y + 78          # inner top of the project panel

    model = Card(RW, "Model", [
        "Catalog model deployed in the Foundry resource",
        "Connected model: another Foundry resource (Other source) or an Azure API Management gateway",
        "Model router: auto or direct routing",
    ], theme="blue", icon="openai", src=[("Connected models", learn("agents/how-to/connected-models"))])
    tools = Card(RW, "Tools", [
        "Toolbox: one managed MCP-compatible endpoint (central auth and governance)",
        "Built-in: web search, file search, code interpreter, memory",
        "Custom: functions (run in your app), OpenAPI, MCP servers",
        "A2A: call other agents",
    ], theme="orange", icon="toolbox", src=[("Toolbox overview", learn("agents/concepts/toolbox-overview"))])
    state = Card(RW, "State", [
        "Conversations and items, files, vector stores, memory stores, hosted session files",
        "Basic setup: Microsoft-managed storage, logically separated",
        "Standard setup: your Cosmos DB, Azure Storage and AI Search (see part 2)",
    ], theme="cyan", icon="cosmos", src=[("Runtime components", RC)])
    obs = Card(RW, "Traces and evaluation", [
        "OpenTelemetry tracing to Application Insights",
        "Monitoring dashboard and evaluations",
    ], theme="violet", icon="app-insights", src=[("Trace agents", learn("observability/concepts/trace-agent-concept"))])
    rcards = [model, tools, state, obs]

    ENDW = 500
    endpoint = Card(ENDW, "Agent endpoint", [
        "One stable endpoint per agent: live at creation, never changes",
        "Protocols, several at once: Responses, Activity, Invocations, A2A, MCP (preview)",
        "Entra auth only, no API keys: AzureRbac (Foundry Agent Consumer), AgentBlueprint (preview), Bot Service schemes",
    ], theme="green", icon="api", icon_size=44, src=[("Configure an agent", learn("agents/how-to/configure-agent"))])
    ver = Card(ENDW, "Version resolution", [
        "version_selector: always latest (default) or pinned to one version",
        "Every edit creates a new immutable version",
    ], theme="green", icon="versions")
    ident = Card(ENDW, "Agent identity (Entra)", [
        "Dedicated per agent: blueprint + instance identity",
        "Starts with NO permissions - grant RBAC for models, tools and the toolbox",
        "Used for the downstream model and tool calls",
    ], theme="red", icon="managed-identity", src=[("Agent identity", learn("agents/concepts/agent-identity"))])
    lcards = [endpoint, ver, ident]

    gap_l = 26
    left_h = sum(c.h for c in lcards) + gap_l * (len(lcards) - 1)
    right_min = sum(c.h for c in rcards) + 26 * (len(rcards) - 1)
    inner_h = max(left_h, right_min)
    gap_r = (inner_h - sum(c.h for c in rcards)) / (len(rcards) - 1)

    # project panel + callers panel (drawn first, so everything sits on top)
    with cv.panel(PX, Y, w=PW, h=inner_h + 78 + 26, title="Foundry project", sub="https://{account}.services.ai.azure.com/api/projects/{project}",
                  theme="green", style="dashed", fill="none", pad=24, title_size=26, sub_size=16):
        pass
    with cv.panel(0, TOP, w=CW_, h=inner_h, title="Callers", theme="gray", style="dotted", pad=18, title_size=22):
        pass
    callers = [
        Box(CW_ - 40, "App, SDK or REST", sub="Responses API via azure-ai-projects and the OpenAI client", icon="app", icon_pos="left", icon_size=42, theme="gray", h=104),
        Box(CW_ - 40, "Teams and Microsoft 365 Copilot", sub="Activity protocol", icon="teams", icon_pos="left", theme="gray", h=104),
        Box(CW_ - 40, "Other agents and routines", sub="A2A (v1.0 GA, v0.3 preview); routines (preview)", icon="a2a", icon_pos="left", icon_size=42, theme="gray", h=104),
        Box(CW_ - 40, "Custom apps and voice clients", sub="Invocations protocol; WebSocket for voice-based agents", icon="api", icon_pos="left", icon_size=42, theme="gray", h=104),
    ]
    free = inner_h - 70 - sum(b.h for b in callers)
    cg = free / (len(callers) + 0)
    cy_ = TOP + 70
    for b in callers:
        b.place(cv, 20, cy_)
        cy_ += b.h + cg

    # left stack inside the project panel (stretched so it fills the panel)
    lx = PX + 24
    ly = TOP
    extra = (inner_h - left_h) / len(lcards)
    for c in lcards:
        c.place(cv, lx, ly, h=c.h + extra)
        ly += c.h + gap_l
    # runtime panel
    RTX = lx + ENDW + 140
    RTW = PX + PW - 24 - RTX
    with cv.panel(RTX, TOP, w=RTW, h=inner_h, title="Agent runtime", sub="picked by the agent kind", theme="green", style="solid", fill="soft",
                  pad=20, title_size=24, sub_size=15):
        pass
    rboxes = [
        Box(RTW - 40, "Prompt agent runtime", sub="default runtime, or the Microsoft Copilot harness (preview); loops model <-> tools; function calls go back to the client",
            icon="agent", icon_pos="left", theme="green", h=128),
        Box(RTW - 40, "Voice runtime (preview)", sub="Voice Live: speech recognition, turn taking, model and speech synthesis over a WebSocket",
            icon="speech", icon_pos="left", theme="green", h=128),
        Box(RTW - 40, "Hosted agent sandbox", sub="your code (container or zip) in a per-session VM-isolated sandbox; calls the project endpoint for models and tools",
            icon="container-apps", icon_pos="left", theme="green", h=128),
    ]
    avail = inner_h - 84
    rg = (avail - sum(b.h for b in rboxes)) / (len(rboxes) + 1)
    ry = TOP + 84 + rg
    for b in rboxes:
        b.place(cv, RTX + 20, ry)
        ry += b.h + rg
    badge_on(cv, rboxes[1], "preview")

    # right column
    ry = TOP
    for c in rcards:
        c.place(cv, RX, ry)
        ry += c.h + gap_r

    # arrows -------------------------------------------------------------------------------
    callers_panel = Rect2()
    callers_panel.x, callers_panel.y, callers_panel.w, callers_panel.h = 0, TOP, CW_, inner_h
    y1 = endpoint.y + 70
    connect(cv, callers_panel, endpoint, a_side="right", b_side="left", ta=ypt(callers_panel, y1), tb=ypt(endpoint, y1), num=1,
            num_theme="red", label="Entra token", label_size=14, label_dx=-12, label_dy=-6, sw=3, bind=False)
    rt_blk = Rect2()
    rt_blk.x, rt_blk.y, rt_blk.w, rt_blk.h = RTX, TOP, RTW, inner_h
    connect(cv, endpoint, rt_blk, a_side="right", b_side="left", ta=ypt(endpoint, y1), tb=ypt(rt_blk, y1), num=2, num_theme="green",
            label="resolve name + version", label_size=14, label_wrap=120, label_dx=-22, label_dy=-6, sw=3, bind=False)
    plan = [(model, 3, "blue", "inference"), (tools, 3, "orange", "tool calls"), (state, 4, "cyan", "items written"), (obs, 4, "violet", "traces")]
    for c, n, th, lab in plan:
        connect(cv, rt_blk, c, a_side="right", b_side="left", ta=ypt(rt_blk, c.cy), tb=0.5, num=n, num_theme=th, label=lab, label_size=14,
                label_dy=-6, sw=3, bind=False)
    y5 = endpoint.bottom - 40
    connect(cv, endpoint, callers_panel, a_side="left", b_side="right", ta=ypt(endpoint, y5), tb=ypt(callers_panel, y5), num=5, num_theme="gray",
            dash="dashed", label="response", label_size=14, label_dx=-24, label_dy=-12, sw=3, bind=False)

    # step cards ---------------------------------------------------------------------------
    sy = Y + inner_h + 78 + 26 + 44
    sw_ = (W - 4 * 36) / 5
    steps = [
        StepCard(sw_, 1, "Authenticate and call", "The client gets an Entra token for https://ai.azure.com/ and calls the project endpoint "
                 "(Azure Government: https://ai.azure.us/.default).", theme_name="red", src=[("Configure an agent", learn("agents/how-to/configure-agent"))]),
        StepCard(sw_, 2, "Resolve and route", "Foundry resolves the agent and version (stable endpoint -> version_selector) and routes to the runtime for that kind: "
                 "prompt, voice or hosted.", theme_name="green"),
        StepCard(sw_, 3, "Call model and tools", "The runtime calls the model (catalog, connected or router) and any tools - direct or through the toolbox "
                 "MCP endpoint - using the agent identity.", theme_name="blue"),
        StepCard(sw_, 4, "Persist and trace", "Response items are written to the conversation (Cosmos DB in Standard setup) and traces go to Application Insights.",
                 theme_name="cyan"),
        StepCard(sw_, 5, "Read the response", "The client reads it synchronously, as a stream (SSE), or polls a background response (background: true).",
                 theme_name="gray", src=[("Runtime components", RC)]),
    ]
    r, b = row(cv, 0, sy, steps, gap=36)
    return b + 60


# ---------------------------------------------------------------------------------------------- section 3
def object_model(cv, y):
    y = hdr(cv, y, "3  The object model: Responses-based Agent Service vs classic Assistants",
            "Agents are identified by name + version; conversations hold items; a response is one unit of execution. Sessions exist for hosted agents only.") + 40
    Y = y
    CLW, GAPX, NW = 290, 150, 800
    NX = CLW + GAPX
    cv.text(0, Y, "Classic (Assistants-style)", size=22, color=theme("gray").deep)
    cv.text(NX, Y, "New: Agent Service on the Responses API", size=22, color=theme("green").deep)
    ry = Y + 44
    rows_ = [
        (("Assistant", "GUID AgentID"), Card(NW, "Agent", [
            "Named, versioned, persisted definition - identified by name + version, no GUID AgentID",
            "Every update creates a new immutable version",
            "POST {project}/agents?api-version=v1",
        ], theme="green", icon="agent", src=[("Runtime components", RC)])),
        (None, Card(NW, "Agent version", [
            "Up to 1,000 per agent; the 1,001st create fails with 400 UserError - delete old versions first",
            "REST: a draft flag; status creating | active | failed | deleting | deleted",
        ], theme="green", icon="versions")),
        (("Thread", None), Card(NW, "Conversation", [
            "Durable object with a unique ID that stores items; reusable across sessions",
            "Model input is auto-truncated; the conversation itself is not",
            "POST {project}/openai/v1/conversations",
        ], theme="cyan", icon="cosmos")),
        (("Message", None), Card(NW, "Item", [
            "Message, tool call, tool output and output items",
        ], theme="cyan", icon="files")),
        (("Run", None), Card(NW, "Response", [
            "One unit of execution; chain turns with previous_response_id",
            "store: false = zero retention; stream (SSE) or background: true",
            "POST {project}/openai/v1/responses",
        ], theme="blue", icon="openai")),
        (None, Card(NW, "Session (hosted agents only)", [
            "A sandbox plus its persisted files - sessions are NOT conversations (see the hosted-agents canvas)",
        ], theme="green", icon="container-apps", dash="dashed")),
    ]
    boxes = []
    for classic, card in rows_:
        card.place(cv, NX, ry)
        if classic:
            bh = min(card.h, 104)
            b = Box(CLW, classic[0], sub=classic[1], theme="gray", dash="dashed", fill="hatch", h=bh, size=20, sub_size=15).place(cv, 0, ry + (card.h - bh) / 2)
            connect(cv, b, card, a_side="right", b_side="left", label="replaced by", label_size=14, label_dy=-4, sw=2.5, dash="dashed")
        else:
            bh = min(card.h, 64)
            b = Box(CLW, "no classic equivalent", theme="gray", dash="dotted", fill="none", h=bh, size=16).place(cv, 0, ry + (card.h - bh) / 2)
        boxes.append(b)
        ry += card.h + 20
    left_bottom = ry - 20

    # --- relationship sketch (right)
    RX = NX + NW + 100
    RW = W - RX
    cv.text(RX, Y, "How the objects relate at run time", size=22, color=theme("green").deep)
    bw = (RW - 2 * 130) / 3
    ay = Y + 60
    hmax = 176

    def chip_card(x, title, lines, chips, th_name, icon, dash="solid"):
        with cv.panel(x, ay, w=bw, h=hmax, title=title, theme=th_name, style=dash, fill="hatch", pad=16, title_size=20) as p:
            place_icon(cv, icon, x + bw - 16 - 36, ay + 14, 36)
            cv.text(p.ix, p.iy, "\n".join(metrics.wrap_text("\n".join(lines), (bw - 32) * 0.96, 15)), size=15, color=INK)
            ChipFlow(chips, bw - 32, theme=th_name, size=14, gap=8).place(cv, p.ix, ay + hmax - 56)
        return p

    a_card = chip_card(RX, "Agent (name)", ["name <= 63 characters, immutable", "every edit adds an immutable version"], ["v1", "v2", "v3", "...", "vN"], "green", "agent")
    r_card = Card(bw, "Response", ["Runs against an agent name + version", "Sync, stream (SSE) or background: true", "store: false = zero retention"],
                  theme="blue", icon="openai", icon_size=36)
    r_card.place(cv, RX + bw + 130, ay, h=hmax)
    c_card = chip_card(RX + 2 * (bw + 130), "Conversation", ["Items accumulate here", "Reusable across sessions"], ["message", "tool call", "tool output"], "cyan", "cosmos")
    connect(cv, a_card, r_card, a_side="right", b_side="left", label="runs against name + version", label_size=14, label_wrap=118,
            label_dy=-4, sw=3)
    connect(cv, c_card, r_card, a_side="left", b_side="right", start_head="arrow", label="reads + appends items", label_size=14, label_wrap=118,
            label_dy=-4, sw=3)
    prev = Card(bw, "Previous response", ["Chained with previous_response_id"], theme="blue", icon="openai", dash="dashed")
    prev.place(cv, r_card.x, r_card.bottom + 70)
    connect(cv, r_card, prev, a_side="bottom", b_side="top", dash="dashed", label="previous_response_id", label_size=14, sw=2.5)
    sess = Card(bw, "Session (hosted)", ["Sandbox + persisted files", "Not a conversation"], theme="green", icon="container-apps", dash="dashed")
    sess.place(cv, a_card.x, prev.y, h=prev.h)
    connect(cv, a_card, sess, a_side="bottom", b_side="top", dash="dashed", label="hosted agents only", label_size=14, sw=2.5)
    routes = Card(bw, "Where it lives", [
        "Project endpoint, API version v1",
        "Basic: Microsoft-managed; Standard: your Cosmos DB",
    ], theme="gray", icon="regions", fill="soft", dash="dashed")
    routes.place(cv, c_card.x, prev.y, h=prev.h)
    right_bottom = max(sess.bottom, prev.bottom, routes.bottom)

    # --- notes (stacked under the sketch)
    ny = right_bottom + 50
    nw2 = (RW - 40) / 2
    n1 = Note(nw2, "Agents have no GUID ID any more - always address them by name + version. A hosted container still receives FOUNDRY_AGENT_ID as an "
                   "environment variable, but treat name + version as the key.", kind="key", title="Name + version is the key")
    n2 = Note(nw2, "The classic Connected Agents tool is not available in the new service: use the A2A tool or Workflows (retiring, see section 1).",
              kind="warn", title="Connected Agents is gone", src=[("Agent-to-agent tool", learn("agents/how-to/tools/agent-to-agent"))])
    r1, b1 = row(cv, RX, ny, [n1, n2], gap=40)
    n3 = Note(RW, "There is no upgrade path from hub-based projects or Azure OpenAI Assistants: files, conversations and vector stores are not migrated "
                  "(model deployments and quota are reusable). Classic and new runtimes use different Cosmos DB containers.",
              kind="gotcha", title="Classic data does not move", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
    n3.place(cv, RX, b1 + 24)
    base = Card(RW, "Shared REST base and token audience", [
        "https://{account}.services.ai.azure.com/api/projects/{project}",
        "Token resource https://ai.azure.com/ (Azure Government: https://ai.azure.us/.default, host *.services.ai.azure.us)",
        "Agents, conversations and responses are all project-scoped routes under that base",
    ], theme="gray", icon="api", icon_size=44, fill="soft", src=[("Runtime components", RC)])
    base.place(cv, RX, n3.bottom + 24)
    return max(left_bottom, base.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 4
def managed(cv, y):
    y = hdr(cv, y, "4  What the service manages for you",
            "Eight things you do not build or operate yourself - each one is a setting or a surface, not infrastructure.") + 40
    cw = (W - 3 * 60) / 4
    cards = [
        Card(cw, "Hosting and scaling", [
            "Prompt agents run on Microsoft-managed compute - nothing to deploy or patch",
            "Hosted agents run in per-session, VM-isolated sandboxes (container image or zip of source)",
            "Autoscale: Foundry-managed (prompt), Foundry + Voice Live (voice), per session and request volume (hosted)",
        ], theme="green", icon="container-apps", src=[("What is Foundry Agent Service?", OV)]),
        Card(cw, "State", [
            "Conversations and items, files, vector stores, memory stores, hosted session files",
            "Basic setup: Microsoft-managed storage, logically separated",
            "Standard setup: your Cosmos DB, Azure Storage and AI Search",
        ], theme="cyan", icon="cosmos", src=[("Runtime components", RC)]),
        Card(cw, "Identity", [
            "A dedicated Entra agent identity per agent: blueprint + instance identity",
            "It starts with NO permissions - grant RBAC for models, tools and the toolbox",
            "Foundry User builds agents; Foundry Agent Consumer only calls endpoints",
        ], theme="red", icon="managed-identity", src=[("Agent identity", learn("agents/concepts/agent-identity"))]),
        Card(cw, "Tools and Toolbox", [
            "Built-in: web search, file search, code interpreter, memory",
            "Custom: functions, OpenAPI specs, MCP servers",
            "Toolbox: build, discover (tool search), consume (one MCP endpoint), govern",
        ], theme="orange", icon="toolbox", src=[("Toolbox overview", learn("agents/concepts/toolbox-overview"))]),
        Card(cw, "Observability", [
            "OpenTelemetry tracing to Application Insights",
            "Monitoring dashboard and evaluations",
            "Agent optimizer (preview) improves instructions, skills, tool descriptions and model picks",
        ], theme="violet", icon="app-insights", src=[("Trace agents", learn("observability/concepts/trace-agent-concept"))]),
        Card(cw, "Guardrails", [
            "Content filters, XPIA protections and RAI policies",
            "Network egress rules for the Copilot harness (preview) - see the prompt-agents canvas",
        ], theme="pink", icon="content-safety", src=[("Data, privacy and security", learn("responsible-ai/agents/data-privacy-security"))]),
        Card(cw, "Publishing", [
            "A stable endpoint per agent; versions with a version_selector",
            "Microsoft Teams and Microsoft 365 Copilot (Activity protocol), A2A and the Entra Agent Registry",
        ], theme="gray", icon="teams", src=[("Configure an agent", learn("agents/how-to/configure-agent"))]),
        Card(cw, "Protocols", [
            "OpenResponses + Activity (Microsoft 365 publishing)",
            "Invocations (custom apps)",
            "A2A: v1.0 GA, v0.3 preview",
            "MCP: preview",
        ], theme="green", icon="api", icon_size=40, src=[("Configure an agent", learn("agents/how-to/configure-agent"))]),
    ]
    r, b = grid(cv, 0, y, cards, 4, gap_x=60, gap_y=40)

    # --- toolbox in / out
    ty = b + 50
    tw = (W - 60) / 2
    cf_in = ChipFlow(["MCP", "web search", "AI Search", "code interpreter", "file search", "OpenAPI", "A2A", "browser automation", "Fabric IQ", "Work IQ"],
                     tw - 48, theme="orange", size=16)
    cf_out = ChipFlow(["function calling", "Grounding with Bing", "computer use", "image generation", "SharePoint", "Fabric data agent",
                       "Azure Functions (direct only)"], tw - 48, theme="gray", size=16)
    ph = max(cf_in.h, cf_out.h) + 100
    with cv.panel(0, ty, w=tw, h=ph, title="Can be curated in a Toolbox", sub="one managed MCP-compatible endpoint, versioned, governed", theme="orange",
                  style="dotted", pad=24, title_size=24, sub_size=15) as p1:
        cf_in.place(cv, p1.ix, p1.iy + 4)
    with cv.panel(tw + 60, ty, w=tw, h=ph, title="Cannot go in a Toolbox - attach to the agent directly", sub="as of 2026-11-03", theme="gray",
                  style="dotted", pad=24, title_size=24, sub_size=15) as p2:
        cf_out.place(cv, p2.ix, p2.iy + 4)
    cv.text(0, ty + ph + 6, "Learn: What is Toolbox in Foundry?", size=12, color=LINK, link=learn("agents/concepts/toolbox-overview"))

    # --- lifecycle strip
    ly = ty + ph + 70
    cv.text(0, ly, "The lifecycle the platform supports", size=24, color=theme("green").deep)
    ly += 44
    gap = 66
    bw = (W - 6 * gap) / 7
    steps = [
        ("Create", "portal, SDK, REST or azd", "green", None), ("Test", "agent playground", "green", None),
        ("Trace", "OpenTelemetry to Application Insights", "violet", None), ("Evaluate", "evaluations", "violet", None),
        ("Optimize", "agent optimizer", "violet", "preview"), ("Publish", "stable endpoint, Teams, Microsoft Copilot", "gray", None),
        ("Monitor", "monitoring dashboard", "violet", None),
    ]
    boxes = [Box(bw, lab, sub=sub, theme=th, h=104, size=20, sub_size=14) for lab, sub, th, _ in steps]
    row(cv, 0, ly, boxes, gap=gap)
    for i in range(len(boxes) - 1):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", sw=3)
    for bx, st in zip(boxes, steps):
        if st[3]:
            badge_on(cv, bx, st[3])
    return ly + 104 + 70


# ---------------------------------------------------------------------------------------------- section 5
def numbers(cv, y):
    y = hdr(cv, y, "5  Setup modes, key numbers and Azure Government (as of 2026-11-03)",
            "The short version. The next canvas ('Agent Service: setup, limits, regions and Azure Government') has the full setup guide, capability hosts and settings, every limit and error code, all 30 regions and the whole Azure Government matrix.") + 40
    # --- three setup modes
    GX = 150
    mw = (W - 2 * GX) / 3
    m1 = Card(mw, "Basic setup", [
        "Agent state in Microsoft-managed, logically separated storage; Microsoft-managed keys only",
        "Compatible with OpenAI Assistants tools, plus non-OpenAI models and tools such as AI Search and Bing",
        "Quickest start: a Foundry account, a project and a model deployment",
    ], theme="blue", icon="foundry", src=[("Set up your environment", learn("agents/environment-setup"))])
    m2 = Card(mw, "Standard setup", [
        "All files, conversations and vector stores live in YOUR single-tenant resources: Azure Storage, Azure AI Search and Azure Cosmos DB for NoSQL (at least 3,000 RU/s)",
        "Customer-managed keys are supported",
        "Capability hosts or capability settings point Agent Service at those resources",
    ], theme="cyan", icon="cosmos", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))])
    m3 = Card(mw, "Standard + BYO virtual network", [
        "Everything in Standard, plus private network isolation of agent OUTBOUND traffic (Standard only)",
        "Containers are injected into a delegated subnet (Microsoft.App/environments); /24 recommended",
        "Inbound: private endpoint + public access disabled - this works with every setup",
    ], theme="indigo", icon="vnet", src=[("Use a virtual network with Agent Service", learn("agents/how-to/virtual-networks"))])
    hm = max(m1.h, m2.h, m3.h)
    m1.place(cv, 0, y, h=hm)
    m2.place(cv, mw + GX, y, h=hm)
    m3.place(cv, 2 * (mw + GX), y, h=hm)
    connect(cv, m1, m2, a_side="right", b_side="left", label="+ your data", label_size=15, sw=3, color="#0c8599", bind=False)
    connect(cv, m2, m3, a_side="right", b_side="left", label="+ your network", label_size=15, sw=3, color="#3b5bdb", bind=False)
    y = y + hm + 56

    # --- the numbers
    cv.text(0, y, "Defaults enforced by Agent Service - fixed for every subscription type; only the hosted-session quota can be raised with a support request", size=18,
            color=theme("yellow").deep)
    y += 38
    gap = 24
    tw = (W - 7 * gap) / 8
    tiles = [
        ("1,000", "agent versions per agent (400 UserError beyond)"), ("128", "tools registered per agent"),
        ("512 MB", "max file upload for prompt agents"), ("300 GB", "total uploaded file size for agents"),
        ("100,000", "messages per thread"), ("2,000 | 1,000", "concurrent hosted sessions per subscription and region"),
        ("30", "regions for the Responses API and Agents"), ("60 min", "max voice session; stored voice data kept 60 days"),
    ]
    boxes = [Box(tw, v, sub=s, theme="yellow", fill="hatch", h=150, size=30, sub_size=14) for v, s in tiles]
    r, b = row(cv, 0, y, boxes, gap=gap)
    t = cv.text(0, b + 14, "Hosted sessions: 2,000 in Canada Central, East US 2, Japan East, North Central US, South Africa North, Southeast Asia and Sweden Central; "
                           "1,000 in every other region where hosted agents are available.", size=15, color=MUTED, wrap=W)
    cv.text(0, t.bottom + 6, "Learn: Quotas and limits for Foundry Agent Service", size=12, color=LINK, link=LQR)
    y = t.bottom + 56

    # --- Azure Government (short version)
    cv.text(0, y, "Azure Government (US Gov Virginia and US Gov Arizona): a subset of agent types and tools", size=24, color=theme("gray").deep)
    y += 44
    tg = Table(
        [("Agent type", 360), ("In Azure Government", 360)],
        [
            ["Prompt agents", ("Yes", "green")],
            ["Voice-based prompt agents", ("No", "red")],
            ["Workflows", ("Preview", "yellow")],
            ["Hosted agents", ("No", "red")],
        ], w=720, theme="gray", size=15, head_size=16, first_col_theme="gray")
    tg.place(cv, 0, y)
    gcard = Card(W - 720 - 60, "Tools in Azure Government", [
        "Yes: Code Interpreter, File Search, Azure AI Search, Azure Functions, Function calling, MCP, OpenAPI",
        "Preview: Custom Code Interpreter",
        "No: Web search, Grounding with Bing, Image generation, Browser automation, Computer use, Fabric, SharePoint, A2A",
        "Workflows are listed as Preview here, while the global workflows page announces the 2026-12-01 retirement - confirm which applies to your cloud. Preview features may lack FedRAMP, DoD IL5 and CJIS commitments. Token resource https://ai.azure.us/.default; endpoints under *.services.ai.azure.us",
    ], theme="gray", icon="regions", src=[("Feature availability in Azure Government", learn("agents/concepts/azure-government"))])
    gcard.place(cv, 780, y, h=max(gcard.h, tg.h))
    return max(tg.bottom, gcard.bottom) + 60


# ---------------------------------------------------------------------------------------------- section 6
def dates(cv, y):
    y = hdr(cv, y, "6  Gotchas and where the docs disagree",
            "Cautious wording on purpose: the sources contradict each other here, so both readings are shown.") + 40
    nw = (W - 3 * 40) / 4
    nx = 0
    n1 = Note(nw, "The overview page says Agent Service has three agent types (prompt, voice-based prompt, hosted); the REST AgentVersion.definition union "
                  "lists five kinds (hosted, prompt, workflow, external, voice). Workflows are retiring, so they are drawn as legacy rather than a peer kind.",
              kind="warn", title="Docs disagree: three kinds or five?", src=[("Agent object schema (REST)", REG_URL)])
    n2 = Note(nw, "Learn's voice pages (Oct 2026) mark voice-based prompt agents, telephony and SIP as preview, while the Build-2026 blog recap lists 'Voice Live prompt agents: "
                  "generally available'. They are probably different products, but the docs do not say so. Hosted agents: the concept page has no preview banner; no GA announcement page was read.",
              kind="warn", title="Docs disagree: preview or GA?")
    n3 = Note(nw, "The autopilot docs describe Assistive, Background service and Autopilot agents. That is an identity model, not a runtime kind - see the "
                  "publish-and-channels canvas.", kind="info", title="Not a runtime kind")
    n4 = Note(nw, "The external-agent how-to still contains two TODO(verify) authoring markers. Treat its finer details as provisional and re-check them against the page; "
                  "the preview status and the 2027-04-30 deprecation date are stated plainly.", kind="warn", title="Docs quality: provisional details",
              src=[("Register external agents", learn("agents/how-to/register-external-agent"))])
    row(cv, nx, y, [n1, n2, n3, n4], gap=40)
    return y + max(n1.h, n2.h, n3.h, n4.h) + 70


def explore(cv, y):
    cv.text(0, y, "Explore next", size=24, color=theme("green").deep)
    cf = ChipFlow(["Agent Service: setup, limits, regions and Azure Government", "Prompt agents in depth", "Prompt agents: harness, A2A, routines and migration",
                   "Hosted agents in depth", "Workflows, routines, A2A and multi-agent", "Memory (preview)", "Voice-based agents",
                   "Publishing, endpoints and channels", "Agent lifecycle and optimizer"], W, theme="green", size=17, gap=14)
    cf.place(cv, 0, y + 42)
    return y + 42 + cf.h + 60


def sources_block(cv, y):
    sources(cv, 0, y, [
        ("What is Foundry Agent Service?", OV),
        ("Agent runtime components (object model)", RC),
        ("Quotas, limits and regions", LQR),
        ("Prompt agents", learn("agents/concepts/prompt-agents")),
        ("Hosted agents", learn("agents/concepts/hosted-agents")),
        ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
        ("Agent identity", learn("agents/concepts/agent-identity")),
        ("Register external agents", learn("agents/how-to/register-external-agent")),
        ("Workflows (retiring)", learn("agents/concepts/workflow")),
        ("Agent object schema (REST reference)", REG_URL),
        ("Migrate from classic agents", learn("agents/how-to/migrate")),
        ("Data, privacy and security for agents", learn("responsible-ai/agents/data-privacy-security")),
    ], w=W, cols=3)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry Agent Service",
                                "The map: five kinds of agent, the Responses-based object model, the request path and what Foundry manages for you  |  as of 2026-11-03",
                                icon="foundry", w=W)
    y = glance(cv, bottom + 34)
    y = kinds(cv, y + 30)
    y = request_path(cv, y)
    y = object_model(cv, y)
    y = managed(cv, y)
    y = numbers(cv, y)
    y = dates(cv, y)
    y = explore(cv, y)
    sources_block(cv, y)
