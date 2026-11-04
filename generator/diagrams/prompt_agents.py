"""Prompt agents in depth (part 1): anatomy of a saved version, the request flow, models, structured inputs, every
configure-agent setting (endpoint, protocols, authorization), tool best practices. Part 2 covers the Copilot harness,
incoming A2A, routines, legacy applications, the optimizer and migration from classic."""
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS

META = dict(
    id="prompt-agents", title="Prompt agents in depth", section="2", group="Agent Service", order=11,
    description="Prompt agents: what is inside an immutable version, the request flow with numbered steps, connected models and the router, structured inputs, the stable agent endpoint, protocols and Entra-only authorization.",
    tags=["prompt-agents", "agent-endpoint", "versions", "structured-inputs", "authorization"],
)

W = 3000
PA = learn("agents/concepts/prompt-agents")
CA = learn("agents/how-to/configure-agent")
CM = learn("agents/how-to/connected-models")
SI = learn("agents/how-to/structured-inputs")
TBP = learn("agents/concepts/tool-best-practice")
AEA = learn("agents/concepts/agent-endpoint-authorization")
REST = learn("reference/rest/agents-patch-agent-object")
LQR = learn("agents/concepts/limits-quotas-regions")
OV = learn("agents/overview")


# ---------------------------------------------------------------------------------------------- helpers
def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def ypt(blk, y):
    return (y - blk.y) / blk.h


def hdr(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


def link(cv, x, y, label, url):
    return cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)


def pill(cv, x, y, label, theme_name, size=15, fill="solid"):
    """Rounded label drawn with raw shapes (not a registered block), for use inside cards."""
    th = theme(theme_name)
    tw, thh = metrics.text_size(label, size)
    w, h = tw + 24, thh + 12
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill if fill == "solid" else th.soft, style="solid", sw=1.5)
        cv.text(x + 12, y + 6, label, size=size, color=th.deep)
    return r


class StepCard(Rect2):
    """Round numbered marker + title + wrapped text in a hatch card."""

    def __init__(self, w, n, title, text, *, theme_name="blue", size=15):
        self.th = theme(theme_name)
        self.w, self.n, self.title, self.size, self.theme_name = w, n, title, size, theme_name
        pad = 16
        self.pad, self.d = pad, 34
        inner = (w - 2 * pad - self.d - 12) * 0.965
        self.t_lines = metrics.wrap_text(title, inner, 19)
        self.lines = metrics.wrap_text(text, (w - 2 * pad) * 0.965, size)
        y = pad + max(len(self.t_lines) * 19 * metrics.line_ratio(), self.d) + 8
        self.body_y = y
        y += len(self.lines) * size * metrics.line_ratio()
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
        cv.register(f"step:{self.title}", x, y, self.w, H)
        return self


# ---------------------------------------------------------------------------------------------- section 0
def glance(cv, y):
    note = Note(W, "You declare a model, instructions and tools; Foundry runs the agent - no orchestration code, no container, no compute to manage. "
                   "Saving a change creates a new immutable version; the agent keeps one stable endpoint and its own Entra identity. "
                   "Preview items are badged; time-sensitive facts are as of 2026-11-03.",
                kind="key", title="A prompt agent is configuration, not code",
                src=[("Prompt agents", PA), ("Configure an agent", CA)])
    note.place(cv, 0, y)
    y = note.bottom + 26
    items = [
        ("Declarative", "model + instructions + tools; Foundry runs it", "agent", "green"),
        ("Versioned", "every save is a new immutable version; up to 1,000 per agent", "versions", "green"),
        ("Stable endpoint", "live at creation, never changes; serves the latest or a pinned version", "api", "green"),
        ("Own Entra identity", "blueprint + instance identity; no API keys on any scheme", "managed-identity", "red"),
        ("Five protocols", "Responses, Activity, Invocations, A2A (v1.0 GA, v0.3 preview), MCP (preview)", "api-connections", "indigo"),
        ("Four ways to author", "portal, SDK, REST or the Azure Developer CLI (azd)", "azd", "blue"),
    ]
    gap = 28
    bw = (W - gap * (len(items) - 1)) / len(items)
    boxes = [Box(bw, lab, sub=sub, icon=ic, icon_pos="left", icon_size=44 if ic in ("api", "azd") else 36, theme=th, size=19, sub_size=14, h=128)
             for lab, sub, ic, th in items]
    r, b = row(cv, 0, y, boxes, gap=gap)
    return b + 56


# ---------------------------------------------------------------------------------------------- section 1
def anatomy(cv, y):
    y = hdr(cv, y, "1  Anatomy: what is inside a saved version",
            "Eight compartments make up the definition (REST kind: prompt; SDK: PromptAgentDefinition). Any edit - even one prompt line - saves the next version.") + 40
    FW = 2080
    cw = (FW - 2 * 26 - 3 * 24) / 4
    cards = [
        Card(cw, "Model / deployment", [
            "A deployment from the Foundry catalog, chosen in the model picker",
            "Or a connected Foundry model: <connection>/<model>",
            "Or the model router (auto or direct routing)",
            "Swap models without changing agent code",
        ], theme="blue", icon="openai", subtitle="REST: model", src=[("Connected models", CM)]),
        Card(cw, "Instructions", [
            "The system prompt for every request",
            "May hold {{structured_inputs}} placeholders",
            "The Prompt Optimizer (pencil-sparkle icon) works on this text only - see part 2",
        ], theme="green", icon="files", subtitle="REST: instructions"),
        Card(cw, "Tools", [
            "Built-in: web search, file search, code interpreter",
            "Custom: function calling, MCP, A2A, OpenAPI",
            "Up to 128 per agent",
            "tool_choice: auto | required | none",
        ], theme="orange", icon="toolbox", subtitle="REST: tools[], tool_choice", src=[("Tool best practices", TBP)]),
        Card(cw, "Skills", [
            "Reusable instructions, scripts and resources",
            "Version pinned at creation",
            "Supported by prompt, voice-based and hosted agents",
        ], theme="orange", icon="learn", subtitle="REST: skills[]"),
        Card(cw, "Toolbox", [
            "A managed MCP-compatible endpoint that curates tools once",
            "Central auth, governance and versioning",
            "Function calling is not curated in a toolbox",
        ], theme="orange", icon="toolbox", icon_size=40, subtitle="attach as a tool", src=[("Toolbox overview", learn("agents/concepts/toolbox-overview"))]),
        Card(cw, "Sampling and reasoning", [
            "temperature 0-2, top_p",
            "reasoning: mode standard | pro",
            "effort none, minimal, low, medium, high, xhigh, max",
            "summary; context auto | current_turn | all_turns",
        ], theme="blue", icon="gear", subtitle="REST: temperature, top_p, reasoning"),
        Card(cw, "Structured inputs", [
            "Handlebars {{var}} placeholders declared with a description, type and default",
            "Values arrive per request - no new version",
        ], theme="violet", icon="code", subtitle="REST: structured_inputs", src=[("Structured inputs", SI)]),
        Card(cw, "Harness choice", [
            "Default prompt-agent runtime - the simplest",
            "Or the Microsoft Copilot harness (preview) for multi-step tool, skill, file and command workflows",
            "Chosen at creation; cannot be changed later",
        ], theme="green", icon="agent", subtitle="REST: harness", src=[("Copilot harness", learn("agents/how-to/use-tools-skills-copilot-harness"))]),
    ]
    with cv.panel(0, y, w=FW, title="Agent version vN - an immutable snapshot", sub="kind: prompt  |  saved in the project  |  create_version(agent_name, definition=PromptAgentDefinition(...))",
                  theme="green", style="solid", fill="soft", pad=26, title_size=28, sub_size=16) as fr:
        r, b = grid(cv, fr.ix, fr.iy + 6, cards, 4, gap_x=24, gap_y=24)
    badge_on(cv, cards[7], "preview")
    FH = fr.h

    # side column: the agent around the version
    SX, SW = FW + 50, W - FW - 50
    c_agent = Card(SW, "The agent: a stable identity", [
        "name up to 63 characters, immutable",
        "One endpoint, live at creation, never changes",
        "Own Entra identity: blueprint + instance identity (instance_identity.principal_id)",
        "status Enabled | Disabled - REST also has disable and enable operations",
    ], theme="green", icon="agent", src=[("Configure an agent", CA)])
    c_vers = Card(SW, "Versions", [
        "Up to 1,000 per agent; the next create then fails with 400 UserError",
        "version_selector: always latest (default) or pinned to one version",
        "Latest auto-updates Teams and Microsoft 365 Copilot",
        "No traffic splitting per this page - docs disagree, see section 7",
    ], theme="green", icon="versions", src=[("Prompt agents", PA)])
    c_agent.place(cv, SX, y)
    c_vers.place(cv, SX, c_agent.bottom + 26, h=y + FH - (c_agent.bottom + 26))
    # version strip drawn with raw pills (not registered blocks) inside the Versions card
    by_ = c_vers.y + c_vers.content_h + 6
    pills = []
    vx = SX + 36
    for lab, th_, fl in (("v1", "gray", "soft"), ("v2", "gray", "soft"), ("v3", "gray", "soft"), ("v4 = latest", "green", "solid")):
        pills.append(pill(cv, vx, by_, lab, th_, size=16, fill=fl))
        vx += pills[-1].w + 64
    for a_, b_ in zip(pills, pills[1:]):
        arrow(cv, [(a_.right + 6, a_.cy), (b_.x - 6, b_.cy)], color="#868e96", sw=2, dash="dashed")
    sel_y = by_ + pills[0].h + 44
    s_pin = pill(cv, pills[1].cx - 55, sel_y, "pinned: v2", "indigo", size=15, fill="soft")
    s_lat = pill(cv, pills[3].cx - 120, sel_y, "always latest (default)", "green", size=15, fill="soft")
    arrow(cv, [(s_pin.cx, s_pin.y - 4), (pills[1].cx, pills[1].bottom + 6)], color="#3b5bdb", sw=2)
    arrow(cv, [(s_lat.cx, s_lat.y - 4), (pills[3].cx, pills[3].bottom + 6)], color="#2f9e44", sw=2)
    y2 = y + FH + 40

    # when to use what
    cw3 = (W - 2 * 40) / 3
    u1 = Card(cw3, "Use a prompt agent when", [
        "You do not want app code or infrastructure",
        "Behavior comes from instructions + model + tools",
        "You author in the portal, SDK, REST or azd",
        "You want a stable endpoint with Foundry managing versions, conversations, identity, tracing and scaling",
        "Spoken, real-time conversations are a separate kind (kind: voice) - see the voice-agents canvas",
    ], theme="green", icon="agent", src=[("Prompt agents", PA)])
    u2 = Card(cw3, "Use a hosted agent when", [
        "You bring your own framework or orchestration code",
        "You need custom middleware or protocols",
        "You need runtime dependencies, compute control or a process model",
        "See the hosted-agents canvas",
    ], theme="green", icon="container-apps")
    u3 = Card(cw3, "Use the Responses API directly when", [
        "Your app owns the definition (an ephemeral agent)",
        "Nothing is saved in Foundry - so no Copilot harness and no agent optimizer",
        "You still get catalog models, platform tools and project governance",
    ], theme="blue", icon="openai", src=[("What is Foundry Agent Service?", OV)])
    r, b = row(cv, 0, y2, [u1, u2, u3], gap=40)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 2
def request_flow(cv, y):
    y = hdr(cv, y, "2  A request through a prompt agent",
            "Top lane = run time (solid = request, dashed = response). Bottom lane = build time. The numbers match the step cards underneath.") + 40
    Y = y
    C1W = 330
    C2X, C2W = 470, 560
    C3X, C3W = 1170, 640
    C4X = 1990
    C4W = W - C4X

    model = Card(C4W, "Model", [
        "Catalog deployment, connected model (<connection>/<model>) or the model router",
        "Sampling and reasoning settings come from the version",
    ], theme="blue", icon="openai")
    tools = Card(C4W, "Server-side tools", [
        "Toolbox MCP endpoint, MCP servers and A2A agents run server-side with the agent identity - grant it RBAC on what they reach",
        "Built-in tools such as web search, file search and code interpreter are served by the platform",
    ], theme="orange", icon="toolbox", src=[("Tool best practices", TBP)])
    state = Card(C4W, "Conversation items and trace", [
        "Items appended to the conversation (Cosmos DB in Standard setup)",
        "OpenTelemetry trace to Application Insights",
    ], theme="cyan", icon="cosmos")
    rcards = [model, tools, state]
    run_h = sum(c.h for c in rcards) + 28 * 2 + 40

    ver = Card(C2W, "Agent version vN", [
        "Immutable snapshot: model, instructions, tools, skills, toolbox, structured inputs, harness",
    ], theme="green", icon="versions")
    dev = Box(C1W, "You or your pipeline", sub="portal, SDK create_version, REST or azd", icon="user", icon_pos="left", icon_size=44, theme="gray", h=124)

    # --- run lane --------------------------------------------------------------------------
    cbox = [
        ("Client app, SDK or REST", "app"),
        ("Routine (preview)", "scheduler"),
        ("Incoming A2A (preview)", "a2a"),
        ("Teams, Microsoft 365 (Activity)", "teams"),
        ("Custom app (Invocations)", "api"),
        ("MCP client (preview)", "mcp"),
    ]
    boxes = [Box(C1W - 36, lab, icon=ic, icon_pos="left", icon_size=42 if ic in ("app", "a2a", "api", "mcp") else 34, theme="gray", h=60, size=16)
             for lab, ic in cbox]
    run_h = max(run_h, 90 + sum(b.h for b in boxes) + 14 * (len(boxes) - 1) + 28)
    gap_r = (run_h - sum(c.h for c in rcards)) / 2
    with cv.panel(0, Y, w=C1W, h=run_h, title="Callers", sub="no API keys on any scheme", theme="gray", style="dotted", pad=18, title_size=22, sub_size=14):
        pass
    free = run_h - 90 - sum(b.h for b in boxes) - 28
    cg = free / (len(boxes) - 1)
    cy_ = Y + 90
    for b_ in boxes:
        b_.place(cv, 18, cy_)
        cy_ += b_.h + cg

    with cv.panel(C2X, Y, w=C2W, h=run_h, title="Agent endpoint", sub=".../agents/{agent}/endpoint", theme="green", style="solid", fill="soft", pad=20,
                  title_size=24, sub_size=15):
        pass
    eb = [
        Box(C2W - 40, "Route by protocol", sub="Responses (.../protocols/openai/responses), Activity, Invocations, A2A (v1.0 GA, v0.3 preview), MCP (preview)",
            icon="api-connections", icon_pos="left", theme="indigo", h=110, size=17, sub_size=14),
        Box(C2W - 40, "Authorize", sub="Entra token checked against the scheme: AzureRbac needs Foundry Agent Consumer; AgentBlueprint (preview); Bot Service. No API keys",
            icon="conditional-access", icon_pos="left", theme="red", h=110, size=17, sub_size=14),
        Box(C2W - 40, "Select the version", sub="version_selector: always the latest (default) or a pinned version", icon="versions", icon_pos="left", theme="green", h=96, size=17, sub_size=14),
    ]
    free = run_h - 92 - sum(b.h for b in eb)
    eg = free / (len(eb) + 1)
    ey = Y + 92 + eg
    for b_ in eb:
        b_.place(cv, C2X + 20, ey)
        ey += b_.h + eg
    for i in range(len(eb) - 1):
        connect(cv, eb[i], eb[i + 1], a_side="bottom", b_side="top", sw=2.5)

    with cv.panel(C3X, Y, w=C3W, h=run_h, title="Agent runtime", sub="operated by Foundry - nothing to deploy", theme="green", style="solid", fill="soft", pad=20,
                  title_size=24, sub_size=15):
        pass
    rb = [
        Box(C3W - 40, "Load the saved definition", sub="model, instructions, tools, skills, toolbox, structured inputs, harness", icon="versions", icon_pos="left", theme="green", h=96, size=17, sub_size=14),
        Box(C3W - 40, "Pick the runtime", sub="the default prompt-agent runtime, or the Microsoft Copilot harness (preview)", icon="agent", icon_pos="left", theme="green", h=96, size=17, sub_size=14),
        Box(C3W - 40, "Loop: model <-> tools", sub="until the answer is ready. Function calls return to your app; toolbox, MCP and A2A calls run server-side with the agent identity",
            icon="gear", icon_pos="left", theme="green", h=118, size=17, sub_size=14),
    ]
    free = run_h - 92 - sum(b.h for b in rb)
    rg = free / (len(rb) + 1)
    ry = Y + 92 + rg
    for b_ in rb:
        b_.place(cv, C3X + 20, ry)
        ry += b_.h + rg
    badge_on(cv, rb[1], "preview")
    for i in range(len(rb) - 1):
        connect(cv, rb[i], rb[i + 1], a_side="bottom", b_side="top", sw=2.5)
    ry = Y
    for c in rcards:
        c.place(cv, C4X, ry)
        ry += c.h + gap_r

    # --- build lane ------------------------------------------------------------------------
    by = Y + run_h + 90
    top_row_h = max(ver.h, dev.h)
    dev.place(cv, 0, by + (top_row_h - dev.h) / 2)
    ver.place(cv, C2X, by + (top_row_h - ver.h) / 2)
    bn = Note(W - C3X, "Every edit saves a new immutable version. The endpoint's version_selector decides which one serves traffic - always the latest (default) or a pinned version. "
                       "Nothing in the run lane above changes when you edit: the next request simply loads the version the selector points at.",
              kind="info", title="Build time vs run time", src=[("Configure an agent", CA)])
    bn.place(cv, C3X, by + (top_row_h - bn.h) / 2)

    # arrows -------------------------------------------------------------------------------
    cb = Rect2()
    cb.x, cb.y, cb.w, cb.h = 0, Y, C1W, run_h
    ep = Rect2()
    ep.x, ep.y, ep.w, ep.h = C2X, Y, C2W, run_h
    rt = Rect2()
    rt.x, rt.y, rt.w, rt.h = C3X, Y, C3W, run_h
    connect(cv, cb, ep, a_side="right", b_side="left", ta=0.5, tb=0.5, num=2, num_theme="red", label="POST + Entra token", label_size=14, label_wrap=110, label_dx=-22, label_dy=-6, sw=3, bind=False)
    connect(cv, ep, rt, a_side="right", b_side="left", ta=0.5, tb=0.5, num=3, num_theme="green", label="route + load definition", label_size=14, label_wrap=110, label_dx=-22, label_dy=-6,
            sw=3, bind=False)
    plan = [(model, 4, "blue", "model call"), (tools, 4, "orange", "tool calls"), (state, 5, "cyan", "items + trace")]
    for c, n, th, lab in plan:
        connect(cv, rt, c, a_side="right", b_side="left", ta=ypt(rt, c.cy), tb=0.5, num=n, num_theme=th, label=lab, label_size=14, label_dy=-6, sw=3, bind=False)
    connect(cv, dev, ver, a_side="right", b_side="left", num=1, num_theme="gray", label="create or edit", label_size=14, label_dy=-6, sw=3)
    connect(cv, ver, ep, a_side="top", b_side="bottom", dash="dotted", label="version_selector: latest | pinned", label_size=14, sw=2.5, label_pos="right", bind=False)
    connect(cv, ep, cb, a_side="left", b_side="right", ta=0.92, tb=0.92, dash="dashed", label="response", label_size=14, label_dy=-6, sw=2.5, bind=False)

    # step cards ---------------------------------------------------------------------------
    sy = by + top_row_h + 60
    sw_ = (W - 5 * 30) / 6
    steps = [
        StepCard(sw_, 1, "Create or edit", "Portal, SDK create_version, REST or azd saves a new immutable version; the endpoint serves the latest (or the pinned) one.", theme_name="gray"),
        StepCard(sw_, 2, "Call the endpoint", "The client sends input to .../agents/{agent}/endpoint/protocols/openai/responses with an Entra token for https://ai.azure.com.", theme_name="red"),
        StepCard(sw_, 3, "Load the definition", "Foundry loads the saved definition and routes to the selected runtime: the default one or the Copilot harness (preview).", theme_name="green"),
        StepCard(sw_, 4, "Model <-> tools loop", "The runtime loops between model and tools. Function calls return to your app; toolbox, MCP and A2A tools run server-side with the agent identity.", theme_name="blue"),
        StepCard(sw_, 5, "Respond and record", "Foundry returns the response, records the trace and appends the items to the conversation.", theme_name="cyan"),
        StepCard(sw_, 6, "Other ways in", "A routine, an incoming A2A caller or a Microsoft 365 channel enters through another protocol route on the same endpoint (see the Callers panel).", theme_name="indigo"),
    ]
    r, b = row(cv, 0, sy, steps, gap=30)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 3
def models(cv, y):
    y = hdr(cv, y, "3  Models: catalog, connected and router",
            "Which model a version calls - and which tools that choice unlocks.") + 40
    cw3 = (W - 2 * 40) / 3
    m1 = Card(cw3, "Catalog models", [
        "Chosen with the model picker; the version's model field names the deployment",
        "A deployment in the project's Foundry resource; Agent Service supports Azure OpenAI models and several Foundry models sold by Azure",
        "Availability varies by region and changes over time - check the portal model picker",
        "Swap the model without changing agent code",
    ], theme="blue", icon="openai", src=[("Quotas, limits and regions", LQR)])
    m2 = Card(cw3, "Connected Foundry models", [
        "Call models hosted in another Foundry resource without copying them",
        "Connection type Other source: Base URL of the other resource; API key or OAuth 2.0 (scope https://ai.azure.com/.default); add each model with deployment name + display name",
        "Connection type Azure API Management gateway: load balancing, throttling, guardrails",
        "Reference it as <connection-name>/<model-name>",
        "Connections are resource-scoped: every project in the resource can use them",
        "Replaces the classic capability-host model hookups",
    ], theme="blue", icon="apim", src=[("Connected models", CM)])
    m3 = Card(cw3, "Model router", [
        "Auto or direct routing",
        "Per the tool-by-model table: Yes for Grounding with Bing, Browser Automation, Code Interpreter, Fabric data agent, File Search, Functions, MCP, OpenAPI, SharePoint and Work IQ (preview)",
        "No for web search, A2A, Azure AI Search, Azure Functions, Computer Use and image generation",
    ], theme="blue", icon="openai", src=[("Quotas, limits and regions - tool support by model", LQR)])
    r, b = row(cv, 0, y, [m1, m2, m3], gap=40)

    # sample of the tool-by-model matrix
    ty = b + 50
    heads = [("Model", 250), "A2A", "Azure AI Search", "Azure Functions", "Bing Search", "Code Interpreter", "File Search", "Functions", "MCP", "Web search"]
    Y_, N_ = CHECK, CROSS
    rows = [
        ["gpt-4.1", Y_, Y_, N_, Y_, Y_, Y_, Y_, Y_, Y_],
        ["gpt-5", Y_, Y_, N_, Y_, Y_, Y_, Y_, Y_, Y_],
        ["gpt-5.1", N_, Y_, Y_, Y_, Y_, Y_, Y_, Y_, Y_],
        ["o3", Y_, Y_, N_, N_, Y_, Y_, Y_, Y_, Y_],
        ["model-router", N_, N_, N_, Y_, Y_, Y_, Y_, Y_, N_],
        ["Llama-3.3-70B-Instruct", N_, Y_, N_, Y_, Y_, Y_, Y_, Y_, Y_],
        ["gpt-oss-120b", N_, N_, N_, N_, Y_, Y_, Y_, Y_, N_],
        ["DeepSeek-R1-0528", N_, N_, N_, N_, Y_, Y_, N_, N_, N_],
    ]
    TW_ = 1880
    t = Table(heads, rows, w=TW_, theme="blue", size=15, head_size=14, first_col_theme="blue", align=["left"] + ["center"] * 9,
              title="Tool support depends on the model - sample rows (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, ty)
    cv.text(0, t.bottom + 8, "The full table on the limits page has 17 tool columns and many more models; it only accounts for the model, so check the region table too.",
            size=14, color=MUTED)
    link(cv, 0, t.bottom + 34, "Quotas, limits and regions - tool support by model", LQR)
    NX = TW_ + 50
    NW = W - NX
    n1 = Note(NW, "Browser Automation, Grounding with Bing, SharePoint, Memory Search and Microsoft Fabric are NOT supported when the agent uses a connected model.",
              kind="gotcha", title="Connected models: unsupported tools", src=[("Connected models", CM)])
    n1.place(cv, NX, ty)
    n2 = Note(NW, "A tool needs both model and region support. For example file search is not available in Italy North or Brazil South, and the Function tool is not available in "
                  "Brazil South, North Central US, South Central US or West US.", kind="warn", title="Region matters too", src=[("Quotas, limits and regions", LQR)])
    n2.place(cv, NX, n1.bottom + 22)
    return max(t.bottom + 60, n2.bottom) + 70

# ---------------------------------------------------------------------------------------------- section 4
def structured(cv, y):
    y = hdr(cv, y, "4  Structured inputs: one version, many behaviours",
            "Declare placeholders once; supply the values on each request - no new version, no prompt string-building in your app.") + 40
    Y = y
    left = Card(860, "Declare", [
        "Handlebars {{var}} placeholders",
        "Declared under structured_inputs with a description, a type and a default",
        "Helpers: #if / else, #unless, #each",
        "Values are supplied per request - the agent version does not change",
        "! No secrets in structured inputs",
    ], theme="violet", icon="code", src=[("Structured inputs", SI)])
    left.place(cv, 0, Y)
    EX, EW = 960, 980
    tpl = Bubble(EW, "Template - an illustrative example, not taken from the docs: You are the support agent for {{company}}. "
                     "{{#if premium}}Offer priority escalation.{{/if}} Answer in {{language}}.", theme="violet", size=16, tail="left")
    tpl.place(cv, EX, Y + 10)
    arrow(cv, [(left.right + 8, Y + 50), (tpl.x - 18, Y + 50)], color="#6741d9", sw=3, label="same version", label_size=14, label_dy=-4)
    cw2 = (EW - 30) / 2
    q1 = Card(cw2, "Request 1", ["company = Contoso", "premium = true", "language = English",
                                 "= Becomes: You are the support agent for Contoso. Offer priority escalation. Answer in English."],
              theme="green", icon="user", icon_size=36)
    q2 = Card(cw2, "Request 2", ["company = Fabrikam", "premium = false", "language = French",
                                 "= Becomes: You are the support agent for Fabrikam. Answer in French."],
              theme="green", icon="user", icon_size=36)
    qy = tpl.bottom + 60
    hq = max(q1.h, q2.h)
    q1.place(cv, EX, qy, h=hq)
    q2.place(cv, EX + cw2 + 30, qy, h=hq)
    connect(cv, tpl, q1, a_side="bottom", b_side="top", ta=0.25, tb=0.5, label="values per request", label_size=14, label_pos="right", sw=2.5, color="#6741d9", bind=False)
    connect(cv, tpl, q2, a_side="bottom", b_side="top", ta=0.75, tb=0.5, sw=2.5, color="#6741d9", bind=False)
    t = Table(
        [("Where {{placeholders}} work", 380), ("Fields", 540)],
        [
            ["Agent or response instructions", "instructions"],
            ["Message content", "content"],
            ["File Search", "vector_store_ids"],
            ["Code Interpreter", "container, file_ids"],
            ["MCP tool", "server_label, server_url, headers"],
            ["Azure AI Search tool", "filter"],
        ], w=920, theme="violet", size=15, head_size=16, title="Templatable fields", title_size=22)
    t.place(cv, W - 920, Y)
    link(cv, W - 920, t.bottom + 8, "Structured inputs", SI)
    return max(left.bottom, q1.bottom, t.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 5
def configure(cv, y):
    y = hdr(cv, y, "5  Configure the agent: every setting",
            "The Configure page of a prompt agent: object model, routing, protocols, authorization schemes and properties. Portal-capable: the version selector; REST or SDK only: protocols, schemes, agent card.") + 40
    Y = y
    LW_ = 1230
    # --- object model (left)
    with cv.panel(0, Y, w=LW_, title="Object model", sub="Project > Agent > Agent version / Agent endpoint", theme="gray", style="dotted", pad=22,
                  title_size=24, sub_size=15) as proj:
        with cv.panel(proj.ix, proj.iy, w=LW_ - 44, title="Agent", sub="stable consumer-facing identity + endpoint + authorization", theme="green",
                      style="solid", fill="soft", pad=18, title_size=22, sub_size=15) as ag:
            iw = (LW_ - 44 - 36 - 30) / 2
            e = Card(iw, "Agent endpoint", [
                "URL live at creation, never changes",
                "Protocols + authorization schemes",
                "version_selector: latest | pinned",
            ], theme="green", icon="api", icon_size=40, fill="hatch")
            v = Card(iw, "Agent versions", [
                "Immutable snapshot of the definition",
                "Any edit, even one prompt line, adds one",
                "v1, v2 ... vN (max 1,000)",
            ], theme="green", icon="versions", fill="hatch")
            hh = max(e.h, v.h)
            e.place(cv, ag.ix, ag.iy, h=hh)
            v.place(cv, ag.ix + iw + 30, ag.iy, h=hh)
            cf = ChipFlow(["id", "name", "versions.latest", "agent_endpoint", "instance_identity", "blueprint", "blueprint_reference", "agent_card", "status"],
                          LW_ - 44 - 36, theme="green", size=15, gap=8, fill="soft")
            cf.place(cv, ag.ix, ag.iy + hh + 18)
    link(cv, 0, proj.bottom + 6, "Configure an agent", CA)

    t_prop = Table(
        [("Property", 250), ("Detail", 980)],
        [
            ["name", "At most 63 characters; immutable"],
            ["versions.latest", "The newest version; the version selector decides what the endpoint serves"],
            ["agent_endpoint", "URL, protocol_configuration, authorization_schemes and version_selector"],
            ["instance_identity", "{principal_id, client_id} - the agent's own Entra identity. null means a legacy agent: shared project identity, cannot publish to Teams or Microsoft 365 through the stable endpoint"],
            ["blueprint, blueprint_reference", "The agent blueprint behind the identity"],
            ["agent_card", "description, version and skills[] - needed to expose the agent over A2A"],
            ["status", "Enabled or Disabled (REST also has disable and enable operations)"],
        ], w=LW_, theme="green", size=14, head_size=15, title="Agent properties", title_size=22, first_col_theme="green")
    t_prop.place(cv, 0, proj.bottom + 56)
    cv.text(0, t_prop.bottom + 10, "Read: GET {endpoint}/agents/{name}?api-version=v1   |   update: PATCH ... Content-Type application/merge-patch+json", size=14, color=MUTED, font=MONO)
    n1 = Note(LW_, "The portal cannot yet configure protocols, authorization schemes or the agent card - use REST or the SDK. The version selector works in the portal.",
              kind="info", title="Portal limits", src=[("Configure an agent", CA)])
    n1.place(cv, 0, t_prop.bottom + 60)
    left_bottom = n1.bottom

    # --- right column: protocols, schemes, notes
    RX = LW_ + 60
    RW = W - RX
    t_proto = Table(
        [("Protocol", 190), ("Route under .../agents/{agent}/endpoint", 640), "Serves", ("Status", 230)],
        [
            ["Responses", "/protocols/openai/responses", "apps and SDKs (Responses API)", ""],
            ["Activity", "/protocols/activityprotocol", "Microsoft Teams and Microsoft 365", ""],
            ["Invocations", "/protocols/invocations", "custom apps", ""],
            ["A2A", "/protocols/a2a", "other agents (incoming A2A)", ("v1.0 GA, v0.3 preview", "yellow")],
            ["MCP", "/protocols/mcp", "MCP-protocol callers", ("Preview", "yellow")],
        ], w=RW, theme="indigo", size=14, head_size=15, title="Protocols - several can be enabled at once", title_size=22, first_col_theme="indigo")
    t_proto.place(cv, RX, Y)
    link(cv, RX, t_proto.bottom + 8, "Configure an agent", CA)
    t_auth = Table(
        [("Authorization scheme", 300), "What it checks", ("Notes", 520)],
        [
            [("AzureRbac (alias Entra)", "red"), "A token for the Foundry resource; the caller needs Foundry Agent Consumer, or any role with Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action",
             "Isolation-key source: Entra (from the token) or Header (user_isolation_key, chat_isolation_key)"],
            [("AgentBlueprint (preview)", "yellow"), "A token issued for the agent blueprint. Delegated scope api://<blueprint-client-id>/access_agent; app-only /.default needs a non-empty token_validation_rules.allowed_clients",
             "Preauthorized: Foundry portal, CLI and VS Code"],
            [("BotServiceRbac, BotServiceTenant, BotService (legacy)", "red"), "Microsoft 365 and Teams channel authentication", "Only ONE Bot Service scheme at a time; configured automatically on publish"],
            [("API keys", "gray"), "Not available - none of the schemes use API keys", "Entra identities only"],
        ], w=RW, theme="red", size=14, head_size=15, title="Authorization schemes", title_size=22)
    t_auth.place(cv, RX, t_proto.bottom + 56)
    link(cv, RX, t_auth.bottom + 8, "Agent endpoint authorization", AEA)
    nw2 = (RW - 40) / 2
    n2 = Note(nw2, "With a private network, set agent_endpoint.protocol_configuration.activity.enable_m365_public_endpoint = true for source-IP-filtered public access to the "
                   "Activity route only. A PATCH replaces protocol_configuration and authorization_schemes wholesale - send the full block.",
              kind="warn", title="Private network + Microsoft 365", src=[("Configure an agent", CA)])
    n3 = Note(nw2, "Assign client roles at project scope. A new agent identity starts with NO permissions; the project managed identity is not the agent identity.",
              kind="key", title="Roles and identity", src=[("Agent identity", learn("agents/concepts/agent-identity"))])
    r, b = row(cv, RX, t_auth.bottom + 56, [n2, n3], gap=40)
    t_tr = Table(
        [("Symptom", 260), "Fix"],
        [
            ["403", "Grant Foundry User on the project"],
            ["401", "The token must be issued for https://ai.azure.com"],
            ["Tool calls fail", "Grant RBAC to the agent identity - it starts with no permissions"],
            ["Teams publish fails", "agent.identity is null: a legacy agent (no in-place identity upgrade yet)"],
        ], w=RW, theme="gray", size=14, head_size=15, title="Troubleshooting", title_size=22)
    t_tr.place(cv, RX, b + 56)
    return max(left_bottom, t_tr.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 6
def best_practices(cv, y):
    y = hdr(cv, y, "6  Tool best practices", "Habits that keep a tool-using prompt agent predictable and safe.") + 40
    cw = (W - 3 * 40) / 4
    cards = [
        Card(cw, "Describe each tool", [
            "State each tool's purpose clearly",
            "Add decision rules where tools overlap",
            "Set tool_choice: auto, required or none",
        ], theme="orange", icon="toolbox"),
        Card(cw, "Treat output as untrusted", [
            "Treat all tool output as untrusted",
            "Require approval for consequential actions",
        ], theme="red", icon="security"),
        Card(cw, "Minimum data, no secrets", [
            "Send tools only the data they need",
            "No secrets in prompts or traces",
        ], theme="pink", icon="content-safety"),
        Card(cw, "Check support, then verify", [
            "A tool needs BOTH model and region support",
            "Use the toolbox and traces to confirm calls happen",
            "MCP governance through the AI gateway (preview)",
        ], theme="violet", icon="app-insights"),
    ]
    r, b = row(cv, 0, y, cards, gap=40)
    link(cv, 0, b + 8, "Tool best practices", TBP)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 7
def gotchas(cv, y):
    y = hdr(cv, y, "7  Gotchas and where the docs disagree") + 36
    nw = (W - 2 * 40) / 3
    n1 = Note(nw, "configure-agent, manage-hosted-agent and the hosted-agents concept page say there is no traffic splitting: one version serves 100%. But the REST and SDK "
                  "schema expose FixedRatioVersionSelectionRule.traffic_percentage, and a Foundry blog claims 'weighted rollouts across versions'. Treat this as unresolved "
                  "and test before you rely on either.", kind="warn", title="Docs disagree: traffic splitting", src=[("Configure an agent", CA), ("Agent object schema", REST)])
    n2 = Note(nw, "Older pages still say Azure AI User, and one troubleshooting page calls the Azure AI Developer role 'insufficient'. The roles were renamed - Foundry User, "
                  "Foundry Owner, Foundry Account Owner, Foundry Project Manager - with the same role IDs.", kind="warn", title="Docs disagree: legacy role names")
    n3 = Note(nw, "Every new agent gets a stable endpoint, its own blueprint and an instance identity at creation. An agent whose instance_identity is null is a legacy agent: "
                  "shared project identity, no Teams or Microsoft 365 publishing through the stable endpoint, no in-place upgrade yet.", kind="gotcha", title="Legacy agents have no identity of their own")
    r, b = row(cv, 0, y, [n1, n2, n3], gap=40)
    return b + 70


def sources_block(cv, y):
    sources(cv, 0, y, [
        ("Prompt agents", PA),
        ("Configure an agent", CA),
        ("Connected models", CM),
        ("Structured inputs", SI),
        ("Tool best practices", TBP),
        ("Agent endpoint authorization", AEA),
        ("Agent object schema (REST reference)", REST),
        ("Use the Copilot harness with prompt agents", learn("agents/how-to/use-tools-skills-copilot-harness")),
        ("Quotas, limits and regions", LQR),
        ("What is Foundry Agent Service?", OV),
        ("Agent identity", learn("agents/concepts/agent-identity")),
        ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
    ], w=W, cols=3)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Prompt agents",
                                "Declarative agents that Foundry runs for you: what is in a version, the request flow, models, inputs, the stable endpoint and its Entra-only auth  |  as of 2026-11-03",
                                icon="foundry", w=W)
    y = glance(cv, bottom + 34)
    y = anatomy(cv, y + 20)
    y = request_flow(cv, y)
    y = models(cv, y)
    y = structured(cv, y)
    y = configure(cv, y)
    y = best_practices(cv, y)
    y = gotchas(cv, y)
    sources_block(cv, y)
