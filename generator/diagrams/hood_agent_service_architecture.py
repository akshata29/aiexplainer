"""Agent Service architecture - a cut-away blueprint of Foundry Agent Service (Under the hood).

Evidence convention for every 'under the hood' canvas: solid border = documented on Microsoft Learn,
dashed border = video / blog only, dotted grey with a '?' = not documented (or only inferred).
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-agent-service-architecture",
    title="Agent Service architecture (the blueprint)",
    section="8", order=1,
    description="Cut-away map of Foundry Agent Service: front door, control vs data plane, registry and versions, "
                "the runtime (prompt vs hosted path), state stores, tools, model gateway and the identity, guardrail "
                "and tracing hooks - with what the docs do not say drawn as grey question marks.",
    tags=["agent-service", "architecture", "control-plane", "runtime", "identity", "state"],
)

# ---------------------------------------------------------------------------------------------- geometry
W = 3330
CP_W = 320                       # control-plane strip
BX, BW = 360, 2190               # band panels (data plane)
PAD = 26
COLW, GAP = 500, 45              # 4 columns inside a band
GUT = (2600, 2652, 2704)         # utility lines: identity, guardrails, tracing
RAIL_X, RAIL_W = 2770, 560
EVD = {"L": "solid", "V": "dashed", "N": "dotted"}
HOOK_THEME = {"I": "red", "G": "pink", "T": "violet"}
ND_STROKE, ND_FILL, ND_TEXT = "#868e96", "#f8f9fa", "#495057"


def colx(k: int) -> float:
    return BX + PAD + k * (COLW + GAP)


def colc(k: int) -> float:
    return colx(k) + COLW / 2


# ---------------------------------------------------------------------------------------------- local helpers
def K(w, title, body, theme, ev="L", **kw) -> Card:
    """Component card that honours the evidence convention (solid / dashed / dotted)."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    if ev == "V":
        title = f"{title} (video/blog)"
        kw["fill"] = "soft"
    return Card(w, title, body, theme=theme, dash=EVD[ev], **kw)


class NDBox(Rect2):
    """Dotted grey '?' box - what the documentation does not say."""

    def __init__(self, w, title, lines=(), *, size=15, title_size=17, pad=14, glyph=44):
        self.w, self.size, self.title_size, self.pad, self.glyph = w, size, title_size, pad, glyph
        self.gl_w = 36
        inner = (w - 2 * pad - self.gl_w) * 0.965
        self.t_lines = metrics.wrap_text(title, inner, title_size)
        self.b_lines: list[str] = []
        for ln in lines:
            self.b_lines += metrics.wrap_text(ln, inner, size)
        lh = metrics.line_ratio()
        body = len(self.b_lines) * size * lh + (4 if self.b_lines else 0)
        self.h = max(2 * pad + len(self.t_lines) * title_size * lh + body, 2 * pad + glyph - 8)
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=ND_STROKE, fill=ND_FILL, style="solid", sw=2,
                                   dash="dotted")
            cv.text(x + self.pad - 2, y + self.pad - 8, "?", size=self.glyph, color="#adb5bd")
            tx, ty = x + self.pad + self.gl_w, y + self.pad
            cv.text(tx, ty, "\n".join(self.t_lines), size=self.title_size, color=ND_TEXT)
            ty += len(self.t_lines) * self.title_size * metrics.line_ratio() + 4
            if self.b_lines:
                cv.text(tx, ty, "\n".join(self.b_lines), size=self.size, color=ND_TEXT)
        cv.register(f"nd:{self.t_lines[0] if self.t_lines else ''}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


def hook(cv, cx, cy, code, d=32):
    numbered(cv, cx, cy, code, theme=HOOK_THEME[code[0]], d=d, size=14)


def tap(cv, blk, codes, taps, *, dx=0, y_ref=None):
    """Draw hook badges straddling the top-right border of a block; remember them for the utility lines."""
    for i, c in enumerate(codes):
        hook(cv, blk.right - 26 - dx - i * 36, blk.y + 1, c)
        taps.append((c, y_ref if y_ref is not None else blk.y + min(blk.h / 2, 60)))


def idchip(cv, x, y, letter, label, *, nd=False, size=13):
    """Identity chip: letter circle + label on white. Returns width."""
    th = THEMES["red"]
    stroke = ND_STROKE if nd else th.stroke
    tw = metrics.line_width(label, size)
    w, h = tw + 44, 26
    cv.rect(x, y, w, h, stroke=stroke, fill="#ffffff", style="solid", sw=1.5, rough=0, dash="dotted" if nd else "solid")
    cv.ellipse(x + 4, y + 3, 20, 20, stroke=stroke, fill="#e9ecef" if nd else th.fill, style="solid", sw=1.5, rough=0)
    lw, lh = metrics.text_size(letter, 13)
    cv.text(x + 14 - lw / 2, y + 13 - lh / 2, letter, size=13, color="#495057" if nd else th.deep)
    cv.text(x + 30, y + (h - metrics.text_size(label, size)[1]) / 2, label, size=size, color=INK)
    return w


def panel_title_h(title, size, sub=None, sub_size=15):
    h = metrics.text_size(title, size)[1] + 6
    if sub:
        h += metrics.text_size(sub, sub_size)[1] + 2
    return h + 8


def legend_strip(cv, x, y, w) -> float:
    """One-glance key: evidence styles, preview pill, hooks, paths."""
    g, a = THEMES["green"], THEMES["yellow"]
    cx, cy = x, y
    rowh = 40

    def advance(need):
        nonlocal cx, cy
        if cx + need > x + w:
            cx, cy = x, cy + rowh

    def label(txt, off):
        nonlocal cx
        t = cv.text(cx + off, cy + 5, txt, size=16, color=INK)
        cx += off + t.w + 44

    advance(520)
    cv.rect(cx, cy, 58, 32, stroke=g.stroke, fill=g.fill, style="hachure", sw=2)
    label("Solid border = documented on Microsoft Learn", 72)
    advance(640)
    cv.rect(cx, cy, 58, 32, stroke=a.stroke, fill=a.fill, style="hachure", sw=2, dash="dashed")
    label("Dashed border = from a video or blog only, labelled (video/blog)", 72)
    advance(640)
    cv.rect(cx, cy, 58, 32, stroke=ND_STROKE, fill=ND_FILL, style="solid", sw=2, dash="dotted")
    cv.text(cx + 21, cy + 1, "?", size=26, color="#adb5bd")
    label("Dotted grey ? = not documented, or only inferred", 72)
    advance(420)
    draw_badge(cv, cx, cy + 4, "preview")
    label("Preview feature (as of 2026-11-03)", 86)
    advance(560)
    for i, c in enumerate(("I", "G", "T")):
        numbered(cv, cx + 15 + i * 36, cy + 16, c, theme=HOOK_THEME[c], d=30, size=15)
    label("Hooks: identity, guardrails, tracing (key on the right)", 116)
    advance(520)
    numbered(cv, cx + 15, cy + 16, "P", theme="green", d=30, size=15)
    numbered(cv, cx + 51, cy + 16, "H", theme="lime", d=30, size=15)
    label("Prompt-agent path and hosted-agent path", 82)
    return cy + rowh


def vline(cv, x, y1, y2, **kw):
    return arrow(cv, [(x, y1), (x, y2)], **kw)


# ---------------------------------------------------------------------------------------------- the canvas
def build(cv: Canvas) -> None:
    taps: list[tuple[str, float]] = []
    right, bottom = title_block(
        cv, 0, 0, "Foundry Agent Service: under the hood",
        "Cut-away blueprint - front door, control vs data plane, runtime, state, tools, models and the identity / guardrail / "
        "tracing hooks   (as of 2026-11-03)", icon="foundry", w=W)
    y = legend_strip(cv, 0, bottom + 26, W) + 56

    # ================================================================== A. callers
    yA = y
    with cv.panel(BX, yA, title="A. Callers and channels", sub="every data-plane caller arrives at the same front door",
                  theme="gray", style="solid", sw=1, fill="soft", pad=PAD, w=BW, title_size=22, sub_size=15) as pa:
        specs = [
            ("SDK / REST client", "azure-ai-projects + OpenAI client; also runs function calls and approves MCP requests", "sdk", "L"),
            ("Foundry portal playground", "build and try agents against the project endpoint", "foundry", "L"),
            ("Teams / M365 Copilot", "Bot Service / Activity protocol", "teams", "L"),
            ("Other agents (A2A)", "A2A v1.0 GA, v0.3 preview", "a2a", "L"),
            ("Routines (video/blog)", "preview; wake an idle hosted session", "scheduler", "V"),
        ]
        callers = [Box(398, t, sub=s, icon=ic, icon_pos="left", theme="gray", fill="soft" if ev == "L" else "none",
                       dash=EVD[ev], h=96, size=17, sub_size=13) for t, s, ic, ev in specs]
        row(cv, pa.ix, pa.iy, callers, gap=36)

    admin = Box(CP_W, "Admins / IaC", sub="portal, CLI, Bicep, Terraform", icon="gear", icon_pos="left", theme="gray",
                fill="soft", h=96, size=17, sub_size=13).place(cv, 0, pa.iy)

    # ================================================================== B. front door
    yB = pa.bottom + 74
    with cv.panel(BX, yB, title="B. Front door: Foundry endpoint = API gateway",
                  sub="platform network - authenticates the request, then routes it by target agent type",
                  theme="green", style="solid", sw=2, fill="soft", pad=PAD, w=BW, title_size=22, sub_size=15) as pb:
        b1 = K(2 * COLW + GAP, "Project endpoint and agent endpoints", [
            "Project endpoint: https://<account>.services.ai.azure.com/api/projects/<project>  (token audience https://ai.azure.com)",
            "Agent endpoint, a stable URL per agent: {project_endpoint}/agents/{name}/endpoint/protocols/openai/responses",
            "Same base, other protocols: .../invocations, wss://.../invocations_ws and .../a2a",
            "Create an agent with POST {project_endpoint}/agents?api-version=v1 (definition.kind = prompt or hosted); call it with POST {project_endpoint}/openai/v1/responses and an agent_reference",
            "The platform's API gateway authenticates the request and routes it based on the target agent type",
        ], "green", icon="foundry",
            src=[("Agents networking deep dive", learn("agents/concepts/agents-networking-deep-dive")),
                 ("Hosted agents", learn("agents/concepts/hosted-agents"))])
        b2 = K(COLW, "Endpoint authorization", [
            "AzureRbac (alias Entra): token for https://ai.azure.com; data action interact/action at project or agent scope",
            "Least-privilege caller role: Foundry Agent Consumer",
            "AgentBlueprint (preview): token for the agent's blueprint audience",
            "BotServiceRbac, BotServiceTenant, BotService (legacy)",
            "! API keys are not supported for agent endpoints",
        ], "red", icon="managed-identity",
            src=[("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))])
        b3 = K(COLW, "Header allow-list (hosted agents)", [
            "Gateway forwards only an allow-list: x-client-*, content negotiation, tracing and correlation headers, user-agent",
            "Never forwards Authorization, Host, Cookie or x-forwarded-*",
            "Platform adds x-agent-user-id and x-agent-foundry-call-id (container protocol 2.0.0)",
        ], "green", icon="api-connections",
            src=[("Hosted agent contract", learn("agents/concepts/hosted-agent-contract"))])
        row(cv, colx(0), pb.iy + 2, [b1, b2, b3], gap=GAP)
    tap(cv, pb, ["I1", "G1"], taps, dx=10, y_ref=yB + 120)

    # ================================================================== C. runtime plane
    yC = pb.bottom + 84
    RT_W, RT_PAD, LANE_GAP, LANE_PAD = 3 * COLW + 2 * GAP, 22, 26, 20
    LANE_W = (RT_W - 2 * RT_PAD - LANE_GAP) / 2
    LANE_IN = LANE_W - 2 * LANE_PAD
    with cv.panel(BX, yC, title="C. Agent Service runtime plane",
                  sub="first the registry and the Agent Runtime, then the shared services both agent paths use",
                  theme="green", style="solid", sw=1, fill="none", pad=PAD, w=BW, title_size=22, sub_size=15) as pc:
        row1_y = pc.iy

        # ---- column 0: registry + version routing
        reg = K(COLW, "Agent registry", [
            "A saved prompt agent is a versioned resource in a project; every change creates a new immutable version",
            "Addressed by name + version - the new model has no GUID AgentID",
            "Limits (as of 2026-11-03): 1,000 versions per agent, 128 tools per agent",
            "Each agent gets its own Entra blueprint and default-instance identity at creation",
            "Agent Applications, the older publishing construct, are being migrated to the agent endpoint model",
        ], "green", icon="versions",
            src=[("Prompt agents", learn("agents/concepts/prompt-agents")),
                 ("Limits and quotas", learn("agents/concepts/limits-quotas-regions"))])
        ver = K(COLW, "Version routing on hosted endpoints", [
            "versionSelector rules: FixedRatio {agentVersion, trafficPercentage}, summing to 100 - for canary rollouts",
            "Each hosted session is bound to one version when it is created",
        ], "green", icon="workflow",
            src=[("Production hosted agents", learn("agents/how-to/deploy-hosted-agent-production"))])
        vnote = Note(COLW, "The hosted-agents concept page says traffic splitting between versions is not supported; the rollout guide and REST samples show FixedRatio percentages.",
                     kind="warn", title="Docs disagree", size=14, title_size=16)
        vnd = NDBox(COLW, "Default version", ["Which version runs when agent_reference carries only a name: not documented (samples pass the name only)"],
                    size=14, title_size=16)
        col(cv, colx(0), row1_y, [reg, ver, vnote, vnd], gap=18)

        # ---- columns 1-3: Agent Runtime with the two paths
        rt_t = "Agent Runtime (orchestrator)"
        rt_s = "hosts and scales prompt agents and hosted agents; manages conversations, tool calls and the agent lifecycle"
        lane_t_h = panel_title_h("Prompt agent path", 21, "definition from the registry; compute managed by Microsoft", 14)

        # prompt lane content
        p1 = K(LANE_IN, "Prompt-agent runtime", [
            "Microsoft-managed compute - you supply the saved definition, there is no container to run",
            "Coordinates the model and the configured tools; several model and tool calls can happen in one response",
            "Returns the response, records traces and appends the response items to the conversation",
        ], "green", icon="agent", src=[("Prompt agents", learn("agents/concepts/prompt-agents"))])
        p2 = K(LANE_IN, "Copilot harness runtime", [
            "Alternative runtime for prompt agents with built-ins: file system, shell, web fetch and sub-agents",
            "Chosen at creation only; needs a first-class conversation per response",
        ], "green", badge="preview", src=[("Prompt agents", learn("agents/concepts/prompt-agents"))])
        p3 = NDBox(LANE_IN, "Orchestrator internals", [
            "Scheduler, queue and placement; loop-iteration cap; whole-run timeout; retry policy; which identity the runtime uses on the model hop - not documented"],
            size=14, title_size=16)
        p4 = Note(LANE_IN, "Call the Responses API with the definition in your code - no saved agent resource - and still get catalog models, platform tools, project-scoped data, on-behalf-of auth and project-level observability.",
                  kind="info", title="Ephemeral pattern", size=14, title_size=16,
                  src=[("Agent Service overview", learn("agents/overview"))])
        # hosted lane content
        half = (LANE_IN - 18) / 2
        h1 = K(half, "Micro VM host layer", [
            "Platform-network layer that provisions or resumes one Micro VM per session",
            "Session quota (as of 2026-11-03): 1,000 or 2,000 concurrent sessions per subscription per region",
        ], "green", icon="vm", src=[("Networking deep dive", learn("agents/concepts/agents-networking-deep-dive"))])
        h2 = K(half, "Token service + tool server", [
            "Run outside the sandbox and identify the calling session",
            "Issue tokens only for the associated agent; the code never sees the blueprint credential",
        ], "red", icon="managed-identity", src=[("Agent identity", learn("agents/concepts/agent-identity"))])
        sb_in = LANE_IN - 36
        sh = (sb_in - 18) / 2
        s1 = K(sh, "Your container", ["Port 8088; POST /responses or /invocations", "A protocol library implements the contract",
                                      "Image from ACR, or a source zip"], "green", icon="container-apps", title_size=18, body_size=14)
        s2 = K(sh, "Persistent files", ["$HOME and /files survive idle", "Up to 20 GiB at >= 1 vCPU", "Files only: memory state is lost"],
               "cyan", icon="storage", title_size=18, body_size=14)
        s3 = K(sh, "Egress proxy", ["Ordered host rules: Allow, Deny, Transform, Rewrite", "HTTP 403 on deny; audit or enforce"],
               "pink", badge="preview", icon="firewall", title_size=18, body_size=14)
        s4 = K(sh, "Own NIC", ["Dedicated NIC for the agent's own outbound traffic (BYO VNet)", "Tool calls still go through the data proxy"],
               "indigo", icon="vnet", title_size=18, body_size=14)
        h3 = K(half, "Isolation wording", ['"Production-proven hypervisor isolation" - launch blog', '"microVM" - Microsoft Mechanics video'],
               "green", ev="V", title_size=18, body_size=14)
        h4 = NDBox(half, "Compute internals", ["Hypervisor / VMM, guest OS, snapshot-restore, warm pool and a numeric cold-start time: not documented"],
                   size=14, title_size=16)

        with cv.panel(colx(1), row1_y, title=rt_t, sub=rt_s, theme="green", style="solid", sw=2, fill="soft",
                      pad=RT_PAD, w=RT_W, title_size=24, sub_size=15) as rt:
            with cv.panel(rt.ix + LANE_W + LANE_GAP, rt.iy, title="Hosted agent path (your code)",
                          sub="one VM-isolated sandbox per session", theme="lime", style="solid", sw=2, fill="none",
                          pad=LANE_PAD, w=LANE_W, title_size=21, sub_size=14) as lh:
                row(cv, lh.ix, lh.iy + 6, [h1, h2], gap=18)
                sy = lh.iy + 6 + max(h1.h, h2.h) + 16
                with cv.panel(lh.ix, sy, title="Micro VM sandbox (one per session)", theme="lime", style="solid", sw=2,
                              fill="soft", pad=18, w=LANE_IN, title_size=19) as sb:
                    row(cv, sb.ix, sb.iy, [s1, s2], gap=18)
                    row(cv, sb.ix, sb.iy + max(s1.h, s2.h) + 18, [s3, s4], gap=18)
                row(cv, lh.ix, sb.bottom + 16, [h3, h4], gap=18)
            with cv.panel(rt.ix, rt.iy, title="Prompt agent path", sub="definition from the registry; compute managed by Microsoft",
                          theme="green", style="solid", sw=2, fill="none", pad=LANE_PAD, w=LANE_W, min_h=lh.h,
                          title_size=21, sub_size=14) as lp:
                col(cv, lp.ix, lp.iy + 6, [p1, p2, p3, p4], gap=16)
            lane_h = max(lh.h, lp.h)
            for lane in (lh, lp):
                lane.el.el["height"] = lane_h
                lane.h = lane_h
        c1_bottom = max(rt.bottom, vnd.bottom)

        # ---- shared services row
        svc_y = c1_bottom + 112
        s_state = K(COLW, "State service", [
            "Objects: agent (reusable model + instructions + tools), conversation (durable items), response (one execution)",
            "store=false: nothing is persisted and you carry the context",
            "Past the context window the model input is truncated; the conversation is not",
            "Hosted agents also get a durable key-value state store (explicit writes)",
        ], "cyan", icon="storage", src=[("Runtime components", learn("agents/concepts/runtime-components")),
                                        ("Agent state store", learn("agents/concepts/agent-state-store"))])
        s_tools = K(COLW, "Tools Service (both paths)", [
            "Runs service-side tools: Code Interpreter, File search, Web search / Bing, AI Search, MCP, OpenAPI, A2A, Azure Functions, Browser automation, Computer use, Image generation, SharePoint, Fabric and Work / Foundry IQ",
            "Toolbox: one managed MCP-compatible endpoint with central auth and guardrails on tool input and output",
            "! Function calling is client-side - your app executes it",
        ], "orange", icon="toolbox", src=[("Toolbox overview", learn("agents/concepts/toolbox-overview"))])
        s_proxy = K(COLW, "Data proxy (single tenant per project)", [
            "Platform-managed network component dedicated to your project",
            "All tool calls route through it",
            "BYO VNet: consumes IPs from your delegated subnet (Microsoft.App/environments)",
        ], "indigo", icon="private-link", src=[("Networking deep dive", learn("agents/concepts/agents-networking-deep-dive"))])
        s_model = K(COLW, "Model gateway = project endpoint", [
            "The project proxies inference calls to the account-level deployment using its own managed identity",
            "Agent identity has implicit access to inference through the project endpoint",
            "! Speech, Content Safety, Vision, Document Intelligence, Language and Translator are not proxied",
        ], "blue", icon="openai", src=[("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions"))])
        row(cv, colx(0), svc_y, [s_state, s_tools, s_proxy, s_model], gap=GAP)

    # ================================================================== D. state, tools targets, deployments
    yD = pc.bottom + 108
    with cv.panel(BX, yD, title="D. Data stores and models", sub="where the data actually lives",
                  theme="cyan", style="solid", sw=1, fill="none", pad=PAD, w=BW, title_size=22, sub_size=15) as pd:
        d1 = K(COLW, "Basic setup (default)", [
            "Microsoft-managed multitenant storage, logically separated",
            "Holds conversations, responses, agent definitions, files and vector stores",
            "No capability host needed",
        ], "cyan", icon="storage", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
        d2 = K(COLW, "Standard setup (your resources)", [
            "Cosmos DB for NoSQL: conversations, responses, agent definitions (containers agent-definitions-v1 and run-state-v1)",
            "Storage for files; AI Search for vector stores",
            "Roles go to the project managed identity; data is isolated by project and stays in the endpoint's region",
            "Minimum 3,000 RU/s; customer-managed keys only in this setup",
        ], "cyan", icon="cosmos", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))])
        d3 = K(COLW, "What tools reach", [
            "MCP servers, OpenAPI endpoints, A2A agents, Azure Functions",
            "Azure AI Search and file-search vector stores",
            "Bing, web search and SharePoint grounding use public endpoints",
            "Network-isolated paths differ per tool - see the networking canvas",
        ], "orange", fill="soft", icon="api-connections", src=[("Private link for Foundry", learn("how-to/configure-private-link"))])
        d4 = K(COLW, "Model deployments (account level)", [
            "Created once on the Foundry resource and shared by every project",
            "Deployment type sets where prompts are processed: Global, Data Zone or Regional",
            "Optional: your own Azure OpenAI resource through aiServicesConnections (standard setup)",
        ], "blue", icon="openai", src=[("Deployment types", learn("foundry-models/concepts/deployment-types"))])
        row(cv, colx(0), pd.iy + 2, [d1, d2, d3, d4], gap=GAP)
    tap(cv, d2, ["I2"], taps)
    tap(cv, s_state, ["I2"], taps)

    # ================================================================== E. utility sources
    yE = pd.bottom + 70
    e0 = K(COLW, "Supporting resources", [
        "Azure Container Registry: hosted-agent images, pulled with the project managed identity (Container Registry Repository Reader)",
        "Key Vault: connection secrets - managed by default, or bring your own",
    ], "gray", icon="acr", src=[("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions"))])
    e1 = K(COLW, "Application Insights", [
        "Tracing is off until an App Insights resource is connected to the project (one connection per project)",
        "Spans: invoke_agent with execute_tool, plan and memory children",
        "Sensitive GenAI content goes to the protected AppGenAIContent table",
    ], "violet", icon="app-insights", src=[("Trace data", learn("observability/concepts/trace-data"))])
    e2 = K(COLW, "Guardrails (Content Safety classifiers)", [
        "A guardrail = risks + intervention points + action, assigned to models and agents",
        "Intervention points: user input, output, tool call (preview), tool response (preview)",
        "The agent's guardrail fully overrides the model's",
    ], "pink", icon="content-safety", src=[("Guardrails overview", learn("guardrails/guardrails-overview"))])
    e3 = K(COLW, "Microsoft Entra ID", [
        "Agent identity blueprint + agent identity (Entra Agent ID); the blueprint credential never reaches your code or the project",
        "Issues the caller tokens and the exchanged agent-identity tokens",
        "A new agent identity starts with no permissions",
    ], "red", icon="app-registrations", src=[("Agent identity", learn("agents/concepts/agent-identity"))])
    e_row_h = max(c.h for c in (e0, e1, e2, e3))
    e_title_h = panel_title_h("E. Utility sources", 22, "x", 15)
    with cv.panel(BX, yE, title="E. Utility sources", sub="the three lines that run up through every layer: identity, guardrails, tracing",
                  theme="gray", style="solid", sw=1, fill="soft", pad=PAD, w=BW, title_size=22, sub_size=15,
                  min_h=PAD * 2 + e_title_h + e_row_h + 120) as pe:
        row(cv, colx(0), pe.iy + 2, [e0, e1, e2, e3], gap=GAP, equalize=True)
    e_boxes_bottom = e0.bottom
    tap(cv, e3, ["I6"], taps)
    tap(cv, e2, ["G2"], taps)
    tap(cv, e1, ["T3"], taps)

    # ------------------------------------------------------------------ hook badges on the middle components
    tap(cv, p1, ["T1", "G2"], taps)
    tap(cv, h2, ["I5"], taps)
    tap(cv, s3, ["G4"], taps)
    tap(cv, s_tools, ["I4", "G2"], taps, dx=0)
    tap(cv, s_model, ["I3", "G3"], taps)
    tap(cv, lh, ["T2"], taps, dx=14)

    # ------------------------------------------------------------------ arrows
    # A -> B
    for b in callers:
        vline(cv, b.cx, b.bottom + 6, yB - 5, color="#1e1e1e", sw=2.5)
    idchip(cv, callers[0].cx + 16, (pa.bottom + yB) / 2 - 13, "C", "Caller token (Entra)")
    # admin -> control plane strip (drawn once the strip exists)

    # B -> runtime panel (P and H)
    xp, xh = lp.x + lp.w / 2, lh.x + lh.w / 2
    vline(cv, xp, pb.bottom + 5, rt.y - 5, color="#2f9e44", sw=3)
    vline(cv, xh, pb.bottom + 5, rt.y - 5, color="#66a80f", sw=3)
    numbered(cv, xp, pb.bottom + 24, "P", theme="green", d=28, size=14)
    numbered(cv, xh, pb.bottom + 24, "H", theme="lime", d=28, size=14)
    cv.text(xp + 22, pb.bottom + 10, "route: prompt agent", size=14, color=INK)
    cv.text(xh + 22, pb.bottom + 10, "route: hosted agent", size=14, color=INK)
    idchip(cv, xp + 22, pb.bottom + 36, "?", "service-internal hop", nd=True)
    idchip(cv, xh + 22, pb.bottom + 36, "?", "service-internal hop", nd=True)

    # registry -> runtime (horizontal)
    y_rr = reg.y + 70
    arrow(cv, [(reg.right + 6, y_rr), (rt.x - 6, y_rr)], color="#2f9e44", sw=2.5)

    # runtime -> bus -> services
    bus_y = rt.bottom + 52
    riser_x = rt.x + rt.w / 2
    vline(cv, riser_x, rt.bottom + 3, bus_y, color="#495057", sw=3, end_head=None)
    arrow(cv, [(colc(0), bus_y), (colc(3), bus_y)], color="#495057", sw=3, end_head=None)
    for k, blk in enumerate((s_state, s_tools, s_proxy, s_model)):
        vline(cv, colc(k), bus_y, blk.y - 5, color="#495057", sw=3)
    cv.text(colx(0) + 8, bus_y - 24, "model calls, tool calls and state reads / writes from either path", size=14, color=INK)
    # tools -> proxy
    connect(cv, s_tools, s_proxy, a_side="right", b_side="left", ta=0.2, tb=0.2, color="#e8590c", sw=2.5)

    # state service -> basic / standard
    gap_mid = (s_state.bottom + yD) / 2
    x_b = s_state.x + 330
    arrow(cv, [(x_b, s_state.bottom + 5), (x_b, d1.y - 5)], color="#0c8599", sw=2.5)
    cv.text(x_b - 150, s_state.bottom + 30, "no capability host", size=14, color=INK)
    x_s = s_state.x + 440
    arrow(cv, [(x_s, s_state.bottom + 5), (x_s, gap_mid + 8), (colc(1), gap_mid + 8), (colc(1), d2.y - 5)], color="#0c8599", sw=2.5)
    cv.text(x_s + 10, gap_mid + 14, "capability host present", size=14, color=INK)
    idchip(cv, colc(1) + 12, gap_mid - 9, "P", "Project MI")
    # data proxy -> tool targets, model gateway -> deployments
    vline(cv, colc(2), s_proxy.bottom + 5, d3.y - 5, color="#e8590c", sw=2.5)
    idchip(cv, colc(2) + 14, (s_proxy.bottom + d3.y) / 2 - 13, "A", "agent identity or connection auth")
    vline(cv, colc(3), s_model.bottom + 5, d4.y - 5, color="#1971c2", sw=2.5)
    idchip(cv, colc(3) + 14, (s_model.bottom + d4.y) / 2 - 13, "P", "Project MI (proxy)")

    # ------------------------------------------------------------------ utility lines (identity, guardrails, tracing)
    y_cap = yA - 6
    runs = [(e3, GUT[0], "I", 0), (e2, GUT[1], "G", 1), (e1, GUT[2], "T", 2)]
    th_of = {"I": THEMES["red"], "G": THEMES["pink"], "T": THEMES["violet"]}
    for blk, gx, letter, rank in runs:
        y_run = e_boxes_bottom + 30 + rank * 28
        col_ = th_of[letter].stroke
        arrow(cv, [(blk.cx, blk.bottom + 4), (blk.cx, y_run), (gx, y_run), (gx, y_cap + 18)], color=col_, sw=3,
              end_head=None)
        numbered(cv, gx, y_cap, letter, theme=HOOK_THEME[letter], d=34, size=17)
        # junction dots
        ys = sorted(t[1] for t in taps if t[0][0] == letter)
        prev = -1e9
        for t_code, t_y in sorted((t for t in taps if t[0][0] == letter), key=lambda t: t[1]):
            yy = max(t_y, prev + 38)
            hook(cv, gx, yy, t_code, d=30)
            prev = yy

    # ------------------------------------------------------------------ rail: tokens, hook key, status
    r_tok = K(RAIL_W, "Identity tokens at a glance", [
        "C  Caller: user, app, managed identity or channel - Entra token for https://ai.azure.com",
        "P  Project managed identity: platform work - ACR pull, Cosmos / Storage / Search access, the model proxy, service-side traces",
        "A  Agent identity: what the agent acts as toward tools and Azure; its credential never leaves the platform",
        "U  User on-behalf-of (preview): delegated user token for IQ, Fabric, Dataverse, Azure DevOps and other delegated tools",
    ], "red", icon="managed-identity", src=[("Agent identity", learn("agents/concepts/agent-identity")),
                                           ("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions"))])
    r_i = K(RAIL_W, "Identity hooks (red)", [
        "I1  Front door: caller token validated; interact/action data action",
        "I2  State: the project MI reaches your Cosmos DB, Storage and AI Search",
        "I3  Model gateway: the project MI proxies inference to the account deployment",
        "I4  Tools: a 4-stage blueprint exchange yields an agent-identity token for the downstream audience (or the connection's own auth)",
        "I5  Hosted code gets tokens only from the token service outside the sandbox",
        "I6  Entra: blueprint + agent identity, no secret in code, project or sandbox",
    ], "red", src=[("Agent identity", learn("agents/concepts/agent-identity"))])
    r_g = K(RAIL_W, "Guardrail hooks (pink)", [
        "G1  Hosted boundary: the rai_config policy screens request and response before the container sees them (preview)",
        "G2  Intervention points: user input and output; tool call and tool response (preview, supported tools only)",
        "G3  Model deployment: content filters run inline with model requests; the agent's guardrail overrides them",
        "G4  Hosted egress policy: a proxy inside the sandbox, HTTP 403 on deny (preview)",
    ], "pink", src=[("Guardrails overview", learn("guardrails/guardrails-overview")),
                    ("Hosted agent guardrails", learn("agents/concepts/hosted-agent-guardrails"))])
    r_t = K(RAIL_W, "Tracing hooks (violet)", [
        "T1  Service-side spans (invoke_agent root, execute_tool, plan, memory) emitted by Agent Service with the project MI",
        "T2  Hosted: protocol libraries emit OpenTelemetry from the sandbox with the agent identity",
        "T3  Spans land in your Application Insights; the platform injects APPLICATIONINSIGHTS_CONNECTION_STRING",
    ], "violet", src=[("Trace agent concepts", learn("observability/concepts/trace-agent-concept")),
                      ("Hosted agent telemetry", learn("agents/how-to/configure-hosted-agent-telemetry"))])
    nd_g = NDBox(RAIL_W, "Guardrail classifier hosting", [
        "Where the classifiers run, and their latency beyond ~50-100 ms per intervention point: not documented"], size=14, title_size=16)
    col(cv, RAIL_X, yA, [r_tok, r_i, r_g, nd_g, r_t], gap=24)
    r_bottom = r_t.bottom

    # ------------------------------------------------------------------ control plane strip
    cp_inner = CP_W - 44
    c1 = K(cp_inner, "What it manages", [
        "Foundry resource: Microsoft.CognitiveServices/accounts, kind AIServices",
        "Projects: .../accounts/projects",
        "Model deployments and connections",
        "Networking, security, customer-managed keys",
        "Capability hosts / settings",
    ], "grape", icon="policy", src=[("Architecture", learn("concepts/architecture"))])
    c2 = K(cp_inner, "Control vs data plane", [
        "# Control plane (ARM)",
        "Create deployments and projects; configure networking, security, connections",
        "# Data plane",
        "Build agents, run evaluations, upload files",
        "Roles at resource, project or agent scope",
        "! Owner and Contributor carry no data-plane rights",
    ], "grape", icon="gear", src=[("RBAC for Foundry", learn("concepts/rbac-foundry"))])
    steps = [
        "Create the Foundry resource (+ optional network injection)",
        "Deploy a model",
        "Standard: create your Cosmos DB, Storage, AI Search and the connections",
        "Account capability host / settings",
        "Create the project (project MI)",
        "Grant the project MI its runtime roles",
        "Foundry User to developers, Foundry Agent Consumer to callers",
    ]
    cap = K(cp_inner, "Capability host / settings", [
        "Sub-resources at account and project scope: where conversations, files and vector stores live",
        "None = Microsoft-managed (Basic); project capability host = your resources (Standard)",
        "One per scope; no updates; account host before project host; no inheritance",
        "Newer 'capability settings' (API 2026-07-15-preview): thinly documented",
    ], "cyan", icon="gear", src=[("Capability hosts", learn("agents/concepts/capability-hosts"))])
    roles = K(cp_inner, "Runtime roles for the project MI", [
        "Account: Cosmos DB Operator, Storage Account Contributor",
        "Cosmos DB (database level): Built-in Data Contributor",
        "Blob containers: Storage Blob Data Contributor and Data Owner",
        "AI Search: Search Index Data Contributor + Search Service Contributor",
    ], "red", icon="key-vault", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))])
    # provisioning steps drawn as a numbered list
    prov_title_h = 40
    prov_lines = [metrics.wrap_text(s, (cp_inner - 70) * 0.965, 15) for s in steps]
    prov_h = 16 + prov_title_h + sum(len(l) * 15 * metrics.line_ratio() + 12 for l in prov_lines) + 30

    strip_y = yB
    cp_mark = cv.mark()
    cy = strip_y + 22 + panel_title_h("Control plane (ARM)", 22, "manages the Foundry resource", 14)
    c1.place(cv, 22, cy)
    c2.place(cv, 22, c1.bottom + 20)
    py = c2.bottom + 20
    # provisioning list
    with cv.group():
        pr = cv.rect(22, py, cp_inner, prov_h, stroke=THEMES["grape"].stroke, fill=THEMES["grape"].fill, style="hachure", sw=2)
        cv.text(22 + 16, py + 14, "Provisioning order (30-45 min by hand for Standard)", size=17, color=THEMES["grape"].deep, wrap=cp_inner - 32)
        yy = py + 16 + prov_title_h + 12
        for i, (s, ls) in enumerate(zip(steps, prov_lines), 1):
            numbered(cv, 22 + 30, yy + 8, i, theme="grape", d=26, size=15)
            cv.text(22 + 54, yy, "\n".join(ls), size=15, color=INK)
            yy += len(ls) * 15 * metrics.line_ratio() + 12
    cv.register("prov", 22, py, cp_inner, prov_h)
    cap_y = max(s_state.y, py + prov_h + 24)
    cap.place(cv, 22, cap_y)
    roles_y = max(yD + 8, cap_y + cap.h + 20)
    roles.place(cv, 22, roles_y)
    strip_bottom = max(pd.bottom, roles.bottom + 22)
    with cv.panel(0, strip_y, title="Control plane (ARM)", sub="manages the Foundry resource",
                  theme="grape", style="solid", sw=2, fill="soft", pad=22, w=CP_W, h=strip_bottom - strip_y,
                  title_size=22, sub_size=14) as cps:
        pass
    cv.move_to(cps.el, cp_mark)
    vline(cv, CP_W / 2, admin.bottom + 6, strip_y - 5, color="#9c36b5", sw=2.5)
    # capability host -> state service
    arrow(cv, [(cap.right + 4, cap.y + 70), (colx(0) - 6, cap.y + 70), (colx(0) - 6, s_state.y + 70), (colx(0) - 1, s_state.y + 70)],
          color="#0c8599", sw=2.5, end_head="arrow")

    # ------------------------------------------------------------------ status table + gotchas in the rail
    t_status = Table(
        [("Item", 290), ("Status", 270)],
        [
            ["Agent Service", "GA; some sub-features preview"],
            ["Hosted agents", "GA on 2026-07-09 (video/blog); Learn pages show no GA banner"],
            ["Copilot harness runtime", ("preview", "orange")],
            ["AgentBlueprint endpoint scheme", ("preview", "orange")],
            ["Tool-call / tool-response guardrails", ("preview", "orange")],
            ["Hosted guardrails + egress policy", ("preview", "orange")],
            ["Agent identity on behalf of user", ("preview", "orange")],
            ["Long-running resilient execution", ("preview", "orange")],
            ["Capability settings (2026-07-15-preview)", ("preview", "orange")],
        ], w=RAIL_W, theme="orange", size=14, head_size=15, title="Status at a glance (as of 2026-11-03)", title_size=20)
    t_status.place(cv, RAIL_X, r_bottom + 40)
    notes = [
        Note(RAIL_W, "Classic (threads and runs) and the new runtime use different Cosmos containers - thread-message-store, system-thread-message-store and agent-entity-store vs agent-definitions-v1 and run-state-v1. Do not mix Basic and Standard in one Foundry account.",
             kind="gotcha", title="Basic vs Standard", size=14, title_size=16,
             src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))]),
        Note(RAIL_W, "Legacy agents share a project-level identity. Migrating to the new model changes the identity, so role assignments do not transfer. A new agent identity starts with no permissions.",
             kind="gotcha", title="Identity migration", size=14, title_size=16,
             src=[("Agent identity", learn("agents/concepts/agent-identity"))]),
        Note(RAIL_W, "Owner and Contributor carry no data-plane rights, and the Azure AI Developer role is not enough for hosted agents.",
             kind="gotcha", title="Roles", size=14, title_size=16,
             src=[("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions"))]),
        Note(RAIL_W, "Foundry does not support automatic cross-region failover: deploy per-region resources and route in your application layer.",
             kind="gotcha", title="Resilience", size=14, title_size=16,
             src=[("Architecture", learn("concepts/architecture"))]),
        Note(RAIL_W, "The networking deep-dive diagram labels the Micro VMs and the data proxy 'on Azure Container Apps' and names the hosted path /invoke; the public routes are /responses and /invocations. A presenter (video/blog, 2026-04-27) said the new hosted platform replaced the Container Apps one. We draw the subnet delegation only - no Container Apps box.",
             kind="warn", title="Docs disagree: what hosted runs on", size=14, title_size=16),
        Note(RAIL_W, "runtime-components identifies agents by name + version (no GUID AgentID), while the hosted contract injects FOUNDRY_AGENT_ID, a GUID, as an environment variable. Treat name + version as the API key.",
             kind="warn", title="Docs disagree: agent identifier", size=14, title_size=16),
        Note(RAIL_W, "Blogs say hosted agents went GA on 2026-07-09; the Learn pages read carry no GA banner, and long-running resilience, AgentBlueprint and the guardrails are still preview. We show GA core + preview sub-features.",
             kind="warn", title="Docs disagree: hosted GA", size=14, title_size=16),
    ]
    _, notes_bottom = col(cv, RAIL_X, t_status.bottom + 36, notes, gap=18)

    # ================================================================== zoom-in section
    blue_bottom = max(pe.bottom, strip_bottom, notes_bottom)
    y0 = blue_bottom + 90
    section_header(cv, 0, y0, "Zoom in: identity, state, tools and models",
                   sub="the details behind the blueprint, with the Learn pages they come from", size=36, sub_size=18,
                   w=W)
    y1 = y0 + 120

    # ---------------- row 1: identity
    red = THEMES["red"]
    cv.text(0, y1, "Runtime token exchange for service-managed tool calls", size=22, color=red.deep)
    cv.text(0, y1 + 28, "Agent Service handles the exchange - no secret in your code, the project or a sandbox", size=15, color=MUTED)
    seq = Sequence(cv, 0, y1 + 66, [("Agent Service", "green", "foundry"), ("Microsoft Entra ID", "red", "app-registrations"),
                                   ("MCP server / A2A endpoint", "orange", "mcp")], spacing=470, head_w=210, head_h=76, label_size=15)
    seq.msg(0, 1, "Present the blueprint's OAuth credential", num=1)
    seq.msg(1, 0, "Agent-identity token: identifies the agent as an independent actor", num=2, dash="dashed")
    seq.msg(0, 1, "Present that token; request one for the downstream audience, e.g. https://storage.azure.com", num=3)
    seq.msg(1, 0, "Scoped access token", dash="dashed")
    seq.msg(0, 2, "Authenticated tool call with the scoped token", num=4)
    seq.note(1, 2, "The downstream resource validates the token and checks the agent identity's RBAC role assignments", kind="info")
    seq_bottom = seq.end()
    cv.text(0, seq_bottom + 10, "Learn: Agent identity", size=12, color=LINK, link=learn("agents/concepts/agent-identity"))
    seq_bottom += 30

    tx = 1215
    cv.text(tx, y1, "Which identity do I get?", size=22, color=red.deep)
    cv.text(tx, y1 + 28, "Ask the questions in order", size=15, color=MUTED)
    tree = [
        ("Model inference through the project endpoint?", "Implicit access",
         "The project proxies the call to the account deployment with its own managed identity; the agent identity needs no role on the deployment.",
         "blue", "P", "Project MI"),
        ("A tool with service-managed auth?", "Blueprint exchange or connection auth",
         "The 4-stage exchange gives an agent-identity token for the tool's audience - or the connection's own auth: project MI, key, OAuth passthrough.",
         "orange", "A", "Agent identity"),
        ("Hosted code calling Azure itself?", "Hosted-agent token service",
         "ManagedIdentityCredential reaches IDENTITY_ENDPOINT outside the sandbox: the agent identity - never the project MI, never IMDS.",
         "lime", "A", "Agent identity"),
        ("Acting for the signed-in user?", "On-behalf-of (preview)",
         "Delegated access needs AgentBlueprint endpoint access; used by Foundry IQ, Work IQ, Fabric IQ, Dataverse and Azure DevOps MCP.",
         "violet", "U", "User OBO"),
    ]
    q_w, a_w, ty = 380, 600, y1 + 66
    prev_q = None
    tree_bottom = ty
    for i, (q, at, ab, th, letter, who) in enumerate(tree):
        ac = K(a_w, at, [f"= {ab}"], th, title_size=18, body_size=15)
        qb = Box(q_w, q, theme="gray", fill="soft", h=max(ac.h, 88), size=17, sub=None, icon=None)
        qb.place(cv, tx, ty)
        ac.place(cv, tx + q_w + 90, ty, h=qb.h)
        connect(cv, qb, ac, a_side="right", b_side="left", color="#495057", sw=2.5, label="yes", label_size=15)
        iw = idchip(cv, ac.right - 24 - (metrics.line_width(who, 13) + 44), ac.y + 11, letter, who)
        if prev_q is not None:
            connect(cv, prev_q, qb, a_side="bottom", b_side="top", color="#868e96", sw=2, label="no", label_size=15, label_pos="right")
        prev_q = qb
        ty = qb.bottom + 48
        tree_bottom = qb.bottom
    cv.text(tx, tree_bottom + 12, "Learn: Agent identity, Hosted agent permissions", size=12, color=LINK, link=learn("agents/concepts/hosted-agent-permissions"))

    t_who = Table(
        [("Hop", 560), ("Identity on the wire", 480)],
        [
            ["Caller -> front door", ("Caller token (Entra, aud https://ai.azure.com); no API keys", "red")],
            ["Definitions, conversations, responses in your Cosmos DB", ("Project managed identity", "red")],
            ["Hosted image pull from ACR", ("Project managed identity", "red")],
            ["Hosted code -> model through the project endpoint", ("Project MI proxies; the code itself holds the agent identity", "red")],
            ["Prompt-agent runtime -> model", ("not documented", "gray")],
            ["Service-managed tool call", ("Agent identity (4-stage) or the connection's own auth", "red")],
            ["Hosted code -> Azure resources", ("Agent identity through the token service", "red")],
            ["Delegated tools (preview)", ("User on-behalf-of", "red")],
            ["Traces: service spans / in-sandbox spans", ("Project MI / agent identity", "red")],
        ], w=1040, theme="red", size=14, head_size=15, title="Who acts as whom, hop by hop", title_size=22)
    t_who.place(cv, 2290, y1)
    row1_bottom = max(seq_bottom, tree_bottom + 40, t_who.bottom)
    cv.text(2290, t_who.bottom + 8, "Learn: Hosted agent permissions, Agent endpoint authorization", size=12, color=LINK,
            link=learn("agents/concepts/hosted-agent-permissions"))

    # ---------------- row 2: state and capability hosts
    y2 = row1_bottom + 90
    section_header(cv, 0, y2, "State and capability hosts", sub="where the conversation, files and vectors live and who decides", size=30, sub_size=16, w=W)
    y2c = y2 + 90
    t_state = Table(
        [("Aspect", 230), ("Basic (default)", 400), ("Standard (bring your own)", 610)],
        [
            ["Who owns the storage", "Microsoft-managed, multitenant, logically separated", "Your Azure resources, isolated by project"],
            ["Conversations, responses, agent definitions", "Managed store", "Cosmos DB for NoSQL: the new runtime uses agent-definitions-v1 and run-state-v1; minimum 3,000 RU/s"],
            ["Files", "Managed storage", "Storage account with two blob containers: <workspaceId>-azureml-blobstore (files) and <workspaceId>-azureml-agent (chunks and embeddings)"],
            ["Vector stores", "Managed vector search", "Azure AI Search"],
            ["Roles go to", "-", "The project managed identity (system- and user-assigned)"],
            ["Customer-managed keys", CROSS, CHECK],
            ["Capability host", "none needed", "account host first, then the project host"],
            ["Data residency", "Stays in the endpoint's region", "Stays in the endpoint's region"],
            ["Retention", "Persists until you delete it", "Persists until you delete it"],
        ], w=1240, theme="cyan", size=14, head_size=15, title="Basic vs Standard agent setup", title_size=22, first_col_theme="cyan")
    t_state.place(cv, 0, y2c)
    cv.text(0, t_state.bottom + 8, "Learn: Standard agent setup, Use your own resources, Agent Service FAQ", size=12, color=LINK,
            link=learn("agents/concepts/standard-agent-setup"))
    cap_card = K(620, "Capability host rules", [
        "# Project capability host properties",
        "threadStorageConnections: Cosmos DB; vectorStoreConnections: AI Search; storageConnections: Storage",
        "Optional aiServicesConnections: your own Azure OpenAI resource",
        "capabilityHostKind = Agents; connections need authType, category, target and metadata.ResourceId",
        "# Rules",
        "One per scope (a second name gives 409); no updates - delete and recreate",
        "Account host must exist before the project host",
        "No inheritance: Agent Service reads the project capability host",
        "Same name + same config is idempotent (200); same name + different config is 400",
        "! The 'capability settings' page redirects to environment setup in this review - details are thin (docs disagree on status)",
    ], "cyan", icon="gear", src=[("Capability hosts", learn("agents/concepts/capability-hosts")),
                                  ("Environment setup", learn("agents/environment-setup"))])
    cap_card.place(cv, 1296, y2c)
    lim = K(650, "State objects and limits (as of 2026-11-03)", [
        "Agent: reusable model + instructions + tools",
        "Conversation: durable object of items (message, tool call, tool output, output items)",
        "Response: one execution, with or without an agent or conversation",
        "10,000 files per agent or thread; 512 MB per file (prompt agents); 300 GB total uploads",
        "2,000,000 tokens per file in a vector store",
        "100,000 messages per thread; 1,500,000 characters per message text",
        "! Over the context window the model input is truncated - the conversation is not",
    ], "cyan", icon="files", src=[("Runtime components", learn("agents/concepts/runtime-components")),
                                    ("Limits and quotas", learn("agents/concepts/limits-quotas-regions"))])
    lim.place(cv, 1296 + 620 + 60, y2c)
    cos = Note(650, "The standard-setup page says five containers at 1,000 RU/s each in one place and 3,000 RU/s = 1,000 x 3 containers in troubleshooting. Quote the 3,000 RU/s account minimum only.",
               kind="warn", title="Docs disagree: Cosmos RU/s", size=14, title_size=16)
    cos.place(cv, 1296 + 620 + 60, lim.bottom + 20)
    row2_bottom = max(t_state.bottom + 30, cap_card.bottom, cos.bottom)

    # ---------------- row 3: tools and models
    y3 = row2_bottom + 90
    section_header(cv, 0, y3, "Tools and the model gateway", sub="what runs in the service, what runs in your app, and how inference is authorised", size=30, sub_size=16, w=W)
    y3c = y3 + 90
    t_tools = Table(
        [("Where it runs", 250), ("What", 640), ("Notes", 440)],
        [
            [("Service-side: the Tools Service", "orange"),
             "Code Interpreter, File search, Web search / Grounding with Bing, Azure AI Search, MCP, OpenAPI, A2A, Azure Functions, Browser automation, Computer use, Image generation, SharePoint, Fabric data agent, Fabric IQ / Work IQ / Foundry IQ, Skills",
             "Executed by the service; every tool-server call routes through the single-tenant data proxy"],
            [("Client-side: your app", "gray"), "Function calling",
             "The model requests a call; your app executes it and returns function_call_output"],
            [("Toolbox: one managed endpoint", "orange"),
             "MCP-compatible endpoint with central auth (Entra, OAuth identity passthrough), guardrails on tool input and output, versioning (promote a default version), optional tool search, skills (preview)",
             "Not supported through a toolbox: Function calling, Grounding with Bing, Computer use, Image generation, SharePoint, Fabric data agent. Azure Functions: direct only"],
        ], w=1330, theme="orange", size=14, head_size=15, title="Service-side vs client-side tools", title_size=22)
    t_tools.place(cv, 0, y3c)
    cv.text(0, t_tools.bottom + 8, "Learn: Toolbox overview, Function calling, Code Interpreter", size=12, color=LINK,
            link=learn("agents/concepts/toolbox-overview"))
    ci = K(600, "Code Interpreter sandbox", [
        "Python sandbox run by the service",
        "Each concurrent conversation gets its own session",
        "Default active 1 h, idle timeout 30 min (as of 2026-11-03)",
        "Extra charges beyond tokens",
    ], "orange", icon="code", src=[("Code Interpreter", learn("agents/how-to/tools/code-interpreter"))])
    ci.place(cv, 1386, y3c)
    ci_note = Note(600, "The raw Responses API page says the container expires after 20 minutes unused - a different surface. The function-calling page still carries legacy 'run expiry' wording; the Responses flow has no run object, so no expiry is drawn.",
                   kind="warn", title="Docs disagree", size=14, title_size=16)
    ci_note.place(cv, 1386, ci.bottom + 20)
    mg = K(690, "Model gateway and identity", [
        "\"When you use the Foundry SDK and the project endpoint for model inference, the project proxies inference calls to the account-level deployment using its own managed identity.\"",
        "The agent identity has implicit access to inference through the project endpoint, plus session storage",
        "Bypass the project endpoint and call https://{account}.cognitiveservices.azure.com directly, and the identity needs Cognitive Services OpenAI User or Foundry User at account scope",
        "Without implicit access it would need responses/* plus agents/*/read and agents/*/write data actions at project scope",
        "Speech, Content Safety, Vision, Document Intelligence, Language and Translator are not proxied",
    ], "blue", icon="openai", src=[("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions"))])
    mg.place(cv, 1386 + 600 + 54, y3c)
    row3_bottom = max(t_tools.bottom + 30, ci_note.bottom, mg.bottom)

    # ---------------- row 4: agent object flow + product-team wording
    y4 = row3_bottom + 90
    section_header(cv, 0, y4, "Agent object flow and what the product team said", size=30, w=W)
    y4c = y4 + 80
    steps5 = [
        ("Create the agent", "POST {project_endpoint}/agents?api-version=v1 with definition.kind = prompt or hosted", "green"),
        ("New immutable version", "Saved in the registry; every change makes another version", "green"),
        ("Identities created", "Entra blueprint + agent identity for the agent - no permissions yet", "red"),
        ("Endpoint routes versions", "versionSelector decides which version a hosted session binds to", "green"),
        ("Invoke", "POST {project_endpoint}/openai/v1/responses with an agent_reference", "blue"),
    ]
    bw5, g5 = 440, 98
    fl = []
    for i, (t, s, th) in enumerate(steps5):
        b = Box(bw5, t, sub=s, theme=th, fill="soft", h=130, size=19, sub_size=14)
        b.place(cv, i * (bw5 + g5), y4c)
        fl.append(b)
    for i in range(4):
        connect(cv, fl[i], fl[i + 1], color="#1e1e1e", sw=2.5, num=i + 1, num_theme="green", gap=8)
    cv.text(0, fl[0].bottom + 10, "Learn: Agent Service overview, Prompt agents, Agent identity", size=12, color=LINK,
            link=learn("agents/overview"))
    v_w = 3330 - (5 * bw5 + 4 * g5) - 0
    bq = K(1060, "Product-team wording", [
        "Built to start on multi-tenant infrastructure and move to single-tenant 'with no code changes'",
        "Versions are first-class because evaluations and observability need them",
        "Responses is a stateful API that persists conversation history and agent definitions; with your own Cosmos DB and AI Search, 'transitive VNET injection' lets the service persist into private resources",
    ], "gray", ev="V", title_size=19, body_size=15)
    bq.place(cv, 0, fl[0].bottom + 50)
    cv.text(20, bq.bottom + 8, "Video: Ignite 2025 BRK201 (youtube.com/watch?v=7faSLQS501E), 0:03:39-0:03:56 and 0:36:00-0:37:26 - not Learn",
            size=12, color=LINK, link="https://www.youtube.com/watch?v=7faSLQS501E")
    row4_bottom = bq.bottom + 30

    # ---------------- sources
    yS = row4_bottom + 70
    sources(cv, 0, yS, [
        ("Agent Service overview", learn("agents/overview")),
        ("Build with runtime components", learn("agents/concepts/runtime-components")),
        ("Prompt agents", learn("agents/concepts/prompt-agents")),
        ("Hosted agents", learn("agents/concepts/hosted-agents")),
        ("Deep dive into Agent Service networking", learn("agents/concepts/agents-networking-deep-dive")),
        ("Agent identity concepts", learn("agents/concepts/agent-identity")),
        ("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
        ("Hosted agent permissions reference", learn("agents/concepts/hosted-agent-permissions")),
        ("Capability hosts", learn("agents/concepts/capability-hosts")),
        ("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
        ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
        ("Microsoft Foundry architecture", learn("concepts/architecture")),
        ("Guardrails overview", learn("guardrails/guardrails-overview")),
        ("Ignite 2025 BRK201 (video, not Learn)", "https://www.youtube.com/watch?v=7faSLQS501E"),
    ], w=W, cols=3)
