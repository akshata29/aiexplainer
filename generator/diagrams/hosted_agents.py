"""Hosted agents - concepts: what they are, framework choice, runtime contract and protocols, sessions and isolation keys,
agent identity and the token service, calling models and the Toolbox, scale, sizes and regions.

Deploy paths, versions and rollout, CI/CD, logs and debugging, guardrails and long-running agents live on the companion
canvas 'hosted-agents-operations'.  Developer / operator view only: Micro VM internals are on 'hood-hosted-agent-runtime'.
Preview items carry a Preview badge; every doc conflict is listed in section K ("Docs disagree") and flagged in place.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hosted-agents", title="Hosted agents: your code on Foundry's runtime", section="2", group="Agent Service", order=12,
    description="Hosted agents in depth (concepts): when to pick them over prompt agents, framework choice, the port-8088 runtime contract and "
                "protocols, per-session sandboxes, isolation keys, agent identity and the token service, models and Toolbox, scale and regions.",
    tags=["hosted-agents", "sessions", "protocols", "identity", "sandbox", "scale"],
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
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    contract=("Hosted agent runtime contract", learn("agents/concepts/hosted-agent-contract")),
    perms=("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions")),
    token=("Hosted agent token service", learn("agents/concepts/hosted-agent-token-service")),
    ident=("Agent identity", learn("agents/concepts/agent-identity")),
    state=("Durable state store", learn("agents/concepts/agent-state-store")),
    limits=("Limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    sessions=("Manage hosted agent sessions", learn("agents/how-to/manage-hosted-sessions")),
    isolate=("Isolate sessions per user", learn("agents/how-to/isolate-sessions-per-user")),
    mux=("Multiplex users on a session", learn("agents/how-to/multiplex-session-users")),
    keys=("Pass isolation keys", learn("agents/how-to/pass-isolation-keys")),
    obo=("Use the on-behalf-of flow", learn("agents/how-to/use-on-behalf-of-flow")),
    env=("Hosted agent environment variables", learn("agents/how-to/configure-hosted-agent-env-variables")),
    toolbox=("Use a toolbox in a hosted agent", learn("agents/how-to/tools/use-toolbox-hosted-agent")),
    fw=("Host agents built with frameworks", learn("how-to/develop/framework-hosted-agents")),
    lc=("Host LangChain / LangGraph agents", learn("how-to/develop/langchain-hosted-agents")),
    maf=("Agent Framework: Foundry hosted agent", learn("agent-framework/hosting/foundry-hosted-agent", base="")),
    azyaml=("azure.yaml reference", learn("agents/concepts/azure-yaml-reference")),
    prompt=("Prompt agents", learn("agents/concepts/prompt-agents")),
    overview=("Agent Service overview", learn("agents/overview")),
    workflow=("Build a workflow (workflow designer)", learn("agents/concepts/workflow")),
    migrate=("Migrate from the initial hosted-agent preview", learn("agents/how-to/migrate-hosted-agent-preview")),
    deploy=("Deploy a hosted agent", learn("agents/how-to/deploy-hosted-agent")),
    manage=("Manage hosted agents", learn("agents/how-to/manage-hosted-agent")),
    prod=("Deploy hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production")),
    pricing=("Azure pricing: Foundry Agent Service", "https://azure.microsoft.com/pricing/details/foundry-agent-service/"),
    snap=("Enable memory snapshots for hosted agents", learn("agents/how-to/use-hosted-agent-memory-snapshots")),
    vnet=("Configure virtual networks for agents", learn("agents/how-to/virtual-networks")),
    netdeep=("Agents networking deep dive", learn("agents/concepts/agents-networking-deep-dive")),
    faq=("Agent Service FAQ", learn("agents/faq")),
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


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


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


def label(cv, x, y, text, theme="green", size=22) -> float:
    t = cv.text(x, y, text, size=size, color=THEMES[theme].deep)
    return t.bottom + 12


def bracket(cv, x1, x2, y, up=12, color=INK) -> None:
    """Flat bracket under a group of boxes: end ticks point up at the boxes, a centre tick points down at the caption."""
    cv.poly([(x1, y - up), (x1, y), (x2, y), (x2, y - up)], kind="line", stroke=color, sw=2)
    xm = (x1 + x2) / 2
    cv.line((xm, y), (xm, y + 12), stroke=color, sw=2)


# ================================================================================================ bands
def band_hero(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "Python + C#", "Any framework. Ship a linux/amd64 container image or a zip of source (python_3_13, python_3_14, dotnet_10).", "green"),
        Tile(C, "1 identity + 1 endpoint", "Created per agent at deploy time: a dedicated Entra agent identity and a dedicated endpoint, live right after deploy.", "red"),
        Tile(C, "Scale per session", "One VM-isolated sandbox per session, scale to zero. No replica count to set and no warm pool to size.", "green"),
        Tile(C, "15 min idle", "Default idle timeout, set per version. Compute is deprovisioned, $HOME and /files are kept; deleted after 30 days idle.", "cyan"),
        Tile(C, "Port 8088", "Plain HTTP: GET /readiness plus POST /responses and/or /invocations (WebSocket /invocations_ws). Container protocol 2.0.0.", "gray"),
        Tile(C, "Pay while active", "Billing follows CPU + memory consumed across active sessions - no compute charge while a session is deprovisioned.", "yellow"),
    ]
    _, bottom = row(cv, 0, y, tiles, gap=G)
    # one-glance pipeline: code -> image -> registry -> version -> endpoint
    ry = label(cv, 0, bottom + 40, "From code to endpoint: the deployment pipeline in five steps", size=24)
    steps = [("1  Your code", "Python or C#, any framework", "green", "code"),
             ("2  Image or source zip", "linux/amd64 image, or a zip up to 250 MB", "gray", "container-apps"),
             ("3  Registry", "ACR, private ACR or BYO (a zip needs none)", "gray", "acr"),
             ("4  Agent version", "immutable: image/code, cpu/memory, env, protocols", "green", "versions"),
             ("5  Endpoint + identity", "dedicated, live right after deploy", "red", "foundry")]
    bw = 470
    gap = (W - 5 * bw) / 4
    boxes = []
    for i, (t, s_, th, ic) in enumerate(steps):
        b = Box(bw, t, sub=s_, theme=th, icon=ic, icon_pos="left", size=19, sub_size=14, h=84, fill="hatch")
        b.place(cv, i * (bw + gap), ry)
        boxes.append(b)
    for i, lab in enumerate(["package", "push or remote build", "pull + create version", "route + serve"]):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", label=lab, label_wrap=gap - 40, label_size=14, sw=3, gap=6)
    cap = cv.text(0, ry + 84 + 16, "Seven deploy paths - azd, source zip, container image to ACR, private ACR, BYO registry, Terraform, REST or SDK - all end in a new immutable agent version "
                                    "behind a dedicated endpoint. Every path in detail: 'Hosted agents: deploy and operate'.", size=15, color=MUTED, wrap=2600)
    cap2 = cv.text(0, cap.bottom + 4, "Status (as of 2026-11-03): the hosted-agents concept page carries no preview banner; capabilities marked Preview on these canvases "
                                      "(draft versions, guardrails, long-running resilience, memory) are preview in the docs.", size=15, color=MUTED, wrap=2600)
    return cap2.bottom


def band_what(cv: Canvas, y: float) -> float:
    y = head(cv, y, "A  What a hosted agent is - and who owns what",
             "Your own containerized agentic app on Agent Service. Models from the catalog do the reasoning; your code does the orchestration.")
    you = card(C, "You own: the code in the sandbox", [
        "Agent logic and orchestration, in Python or C#",
        "Framework: Microsoft Agent Framework, LangGraph, Semantic Kernel or custom",
        "The container image, or the zip of source, and its dependencies",
        "cpu and memory, env vars and protocols - all fixed per version",
        "What you persist: $HOME files, state-store items, memory",
    ], theme="green", icon="code", src=src("hosted"))
    contract = card(C, "Runtime contract: the handshake", [
        "Listen on port 8088 (plain HTTP)",
        "GET /readiness returns 200",
        "POST /responses and/or POST /invocations; WebSocket /invocations_ws",
        "Shut down gracefully on SIGTERM; container protocol 2.0.0",
        "The AgentServer SDK implements all of it for you",
    ], theme="ink", icon="api-connections", src=src("contract"))
    plat = card(C, "Foundry owns: everything around it", [
        "Dedicated endpoint, and routing to the version you select",
        "Dedicated Entra agent identity plus the token service",
        "Sandbox provisioning, scale per session, scale to zero",
        "Session state ($HOME, /files) kept across idle; conversation history (Responses)",
        "Telemetry plumbing, immutable versions, rollbacks",
    ], theme="gray", icon="foundry", src=src("hosted"))
    _, b1 = row(cv, 0, y, [you, contract, plat], gap=G)
    connect(cv, you, contract, a_side="right", b_side="left", start_head="arrow", end_head="arrow", sw=3, gap=4)
    connect(cv, contract, plat, a_side="right", b_side="left", start_head="arrow", end_head="arrow", sw=3, gap=4)
    note = Note(S(3), "Python and C# only. Source runtimes: python_3_13, python_3_14, dotnet_10. Container images must be linux/amd64. "
                      "There is no Node.js runtime - the JS SDK can still upload Python or .NET zips.", kind="info",
                title="Languages and packaging", src=src("hosted", "fw"))
    note.place(cv, 0, b1 + 22)
    fw = Table(
        [("Framework", 190), ("Hosting package and entry point", 760), "Toolbox client"],
        [
            [("Microsoft Agent Framework", "green"),
             "agent-framework-foundry-hosting: ResponsesHostServer, InvocationsHostServer. .NET: AddFoundryResponses / MapFoundryResponses, AddInvocationsServer",
             "FoundryToolbox (Python), AddFoundryToolboxes (.NET)"],
            [("LangGraph", "green"),
             "langchain-azure-ai[hosting] >= 1.2.9; python -m langchain_azure_ai.agents.hosting.run --protocol responses|invocations. A checkpointer keys state "
             "by conversation; production needs a durable one such as FoundryStateStore",
             "AzureAIProjectToolbox"],
            [("Semantic Kernel, CrewAI, custom", "green"),
             "Use the protocol libraries directly: azure-ai-agentserver-responses / -invocations (Python), Azure.AI.AgentServer.* (.NET)",
             "A standard MCP Streamable-HTTP client"],
            [("Also named in the docs", "green"), "OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK", "A standard MCP client"],
        ], w=S(3), theme="green", size=14, head_size=15, title="Framework choice", title_size=22)
    fw.place(cv, X(3), y)
    return max(note.bottom, fw.bottom, b1)


def band_compare(cv: Canvas, y: float) -> float:
    y = head(cv, y, "B  Hosted vs prompt agents - pick by what you must control",
             "Same agent-endpoint model and immutable versions; what differs is who writes and runs the logic.")
    t = Table(
        [("", 200), ("Prompt agent", 820), "Hosted agent"],
        [
            ["Defined by", "Configuration only: model + instructions + tools (+ skills, toolbox). Saving a change creates a new version",
             "Your code as a container image or a zip of source. A version snapshots image/code, cpu/memory, env vars and protocols"],
            ["Who runs the logic", "Foundry's default prompt-agent runtime (or the Microsoft Copilot harness - preview). You maintain no code",
             "Your code, inside a per-session VM-isolated sandbox that Foundry provisions. You maintain the orchestration plus an AgentServer protocol library"],
            ["Compute you control", "None", "cpu and memory per version (one session's sandbox); $HOME and /files storage"],
            ["Endpoint routes", "Responses, Activity, Invocations, A2A (v1.0 GA, v0.3 preview), MCP (preview)",
             "Responses, Invocations, Invocations (WebSocket), Activity (bridged from Responses), A2A (docs disagree - see section K)"],
            ["State", "Conversations (Responses model) managed by the platform",
             "Sessions ($HOME, /files) + conversations (Responses) + a durable state store - you choose where state lives"],
            ["Scaling and cost", "Foundry-managed; inference + tool charges",
             "Per session, scale to zero; inference + tool charges + container compute (CPU + memory of active sessions)"],
            ["Agent identity", "Yes - Entra agent identity", "Yes - dedicated Entra agent identity created at deploy; your code gets tokens through the token service"],
            ["Versions and routing", "Immutable versions; version_selector latest or pinned; docs say no traffic splitting",
             "Immutable versions; the same selector; docs disagree on traffic splitting (see section K)"],
            ["Azure Government", "Available", "Not available"],
            ["Choose it when", "You want the least to manage: no code, containers or compute",
             "You need your own code or framework, custom protocols (webhooks, non-OpenAI payloads), compute control, stateful work or resilient long-running work (preview)"],
        ], w=S(4), theme="green", size=14, head_size=16, first_col_theme="green")
    t.place(cv, 0, y)
    n1 = Note(C, "Prompt agent: behaviour from instructions + model + tools, no app code or infrastructure. Hosted agent: your own framework or "
                 "orchestration code, custom middleware or protocols, runtime dependencies and compute. Responses API directly: your app owns the "
                 "definition (no Copilot harness, no prompt-agent optimizer). The prompt-agent side is drawn on 'Prompt agents in depth'.", kind="tip",
              title="Rule of thumb", src=src("prompt", "overview"))
    n1.place(cv, X(4), y)
    n2 = Note(C, "Hosted agents are not available in Azure Government (prompt agents are) and are not supported in the workflow designer. "
                 "Agents on the initial hosted-agent preview backend were not auto-migrated; support for it ended on 2026-08-20.",
              kind="gotcha", title="Where hosted agents do not go", src=src("gov", "workflow", "migrate"))
    n2.place(cv, X(5), y)
    return max(t.bottom, n1.bottom, n2.bottom)


def band_arch(cv: Canvas, y: float) -> float:
    y = head(cv, y, "C  Runtime and session architecture - what runs where when a request arrives",
             "Numbers 1-6 follow one Responses request through the platform; 7 and 8 (idle, resume) are drawn in section D.")
    top = y + 4
    LEFT_W, CP_X, DEP_W = 470, 600, 640
    DEP_X = W - DEP_W
    CP_W = DEP_X - 170 - CP_X
    PAD, DOORS_W = 26, 640

    # ---------------------------------------------------------------- control plane (grey) with doors + sandbox
    with cv.panel(CP_X, top, title="Foundry Agent Service: the platform-owned side",
                  sub="endpoint, versions, identity, conversations and session storage - everything around your container",
                  theme="gray", style="dotted", pad=PAD, title_size=26, sub_size=15, w=CP_W) as cp:
        with cv.panel(cp.ix, cp.iy, title="Agent endpoint", sub="dedicated per agent, live right after deploy", theme="green",
                      style="solid", fill="soft", pad=18, title_size=22, sub_size=14, w=DOORS_W) as dp:
            dw = DOORS_W - 36

            def door(t, b):
                return card(dw, t, b, theme="green", title_size=18, body_size=14, pad=12, gap=3)
            doors = [
                door("Responses", ["POST .../agents/{name}/endpoint/protocols/openai/responses", "Chat apps: Foundry keeps the history by conversation ID"]),
                door("Invocations", ["POST .../endpoint/protocols/invocations", "Arbitrary JSON in and out; you keep state; session only via ?agent_session_id="]),
                door("Invocations (WebSocket)", ["wss://.../endpoint/protocols/invocations_ws?api-version=v1", "Full duplex streaming, for example real-time voice"]),
                door("Activity", ["Teams and Microsoft 365 channels", "The platform bridges Responses to Activity when you publish"]),
                door("A2A", [".../endpoint/protocols/a2a", "Agent-to-agent delegation; v1.0 GA, v0.3 preview"]),
            ]
            col(cv, dp.ix, dp.iy, doors, gap=12)
        mx = dp.x + dp.w + 110
        mw = (CP_X + CP_W - PAD) - mx
        cw = (mw - 50) / 3
        c_conv = card(cw, "Conversations and session storage", [
            "Conversation history lives in Foundry and outlives compute",
            "$HOME and /files persist and are restored onto new compute",
        ], theme="cyan", icon="storage", src=src("hosted"))
        c_id = card(cw, "Agent identity and token service", [
            "Dedicated Entra identity: blueprint + instance",
            "The token service sits outside the sandbox and hands tokens to your code",
            "No blueprint credential in the sandbox",
        ], theme="red", icon="managed-identity", src=src("token"))
        c_ver = card(cw, "Agent versions (immutable)", [
            "Snapshot: image or code, cpu/memory, env vars, protocols",
            "Sessions stay on the version they were created with",
        ], theme="green", icon="versions", src=src("hosted"))
        _, rb = row(cv, mx, cp.iy, [c_conv, c_id, c_ver], gap=25)
        with cv.panel(mx, rb + 78, title="Per-session sandbox (VM-isolated)", sub="one per session; the cpu and memory set on the version describe ONE session",
                      theme="green", style="solid", fill="soft", pad=20, title_size=24, sub_size=14, w=mw) as sb:
            sw_ = (mw - 40 - 44) / 3
            s1 = card(sw_, "Your container", [
                "Agent code + framework (Agent Framework, LangGraph, Semantic Kernel, custom)",
                "Listens on :8088; GET /readiness must return 200",
                "Receives x-agent-user-id and x-agent-foundry-call-id",
            ], theme="green", icon="container-apps")
            s2 = card(sw_, "AgentServer SDK", [
                "Responses, Invocations and Core adapters",
                "HTTP server, SSE, history hydration, OpenTelemetry, SIGTERM handling",
            ], theme="green", icon="code")
            s3 = card(sw_, "Session filesystem", [
                "$HOME (default /home/session) plus /files uploads",
                "Disk up to 20 GiB at 1 vCPU or more; about 20% is reserved",
            ], theme="cyan", icon="storage", src=src("hosted"))
            row(cv, sb.ix, sb.iy, [s1, s2, s3], gap=22)

    # ---------------------------------------------------------------- left column: callers, Entra gate, steps
    callers = card(LEFT_W, "Callers", [
        "Your app or SDK: any OpenAI-compatible client for Responses",
        "Teams and Microsoft 365 (Activity)",
        "Other agents (A2A) and voice clients (WebSocket)",
    ], theme="gray", icon="user")
    callers.place(cv, 0, cp.y + 4)
    gate = card(LEFT_W, "Microsoft Entra ID token", [
        "Audience: https://ai.azure.com/",
        "Invoke with Foundry Agent Consumer (least privilege) or Foundry User",
        "Apps with their own auth add x-ms-user-identity (section F)",
    ], theme="red", icon="managed-identity", src=src("perms"))
    gate.place(cv, 0, dp.y + dp.h / 2 - gate.h / 2)
    steps = Steps(LEFT_W, "Request walk-through", [
        "Client calls the endpoint with an Entra token and a conversation or agent_session_id",
        "The endpoint authenticates, then resolves the session: a new sandbox or the bound one",
        "Compute is provisioned (cold, warm or resume); the platform waits for GET /readiness = 200",
        "The request reaches your container: POST /responses or /invocations",
        "Your code calls models, the Toolbox and Azure services as the agent identity",
        "The response or SSE stream returns; every request resets the idle timer",
        "No request for the idle timeout: compute is deprovisioned, files stay",
        "Same session ID again: new compute, state restored",
    ], theme="yellow", src=src("hosted"))
    steps.place(cv, 0, gate.bottom + 40)

    # ---------------------------------------------------------------- right column: dependencies
    with cv.panel(DEP_X, top, title="Dependencies", sub="what your container and the platform reach - you secure each one",
                  theme="gray", style="dotted", pad=20, title_size=24, sub_size=15, w=DEP_W) as dep:
        dwid = DEP_W - 40
        c_acr = card(dwid, "Container registry (image source)", [
            "At deploy the platform pulls the image from ACR with the project managed identity; or from a non-Azure registry through a connection",
        ], theme="gray", icon="acr", src=src("deploy"))
        c_mod = card(dwid, "Foundry models", [
            "Project endpoint (FOUNDRY_PROJECT_ENDPOINT)",
            "The agent identity can call model inference by default",
        ], theme="blue", icon="openai", src=src("hosted"))
        c_tool = card(dwid, "Toolbox MCP endpoint", [
            "Code Interpreter, Web Search, AI Search, OpenAPI, MCP, A2A, Skills behind one URL",
            "Auth consolidated: OAuth passthrough, agent identity, keys; tool calls leave the sandbox through a single-tenant data proxy",
        ], theme="orange", icon="toolbox", src=src("toolbox"))
        c_az = card(dwid, "Your Azure services", [
            "Storage, databases, internal APIs: assign RBAC to the agent identity - it starts with none",
        ], theme="gray", icon="storage", src=src("perms"))
        c_mem = card(dwid, "Memory store", [
            "Attach a Foundry memory store for long-term agent memory (see the Memory canvas)",
        ], theme="teal", icon="ai-search", badge="preview")
        c_st = card(dwid, "FoundryStateStore", [
            "Durable key-value store for app state and framework checkpoints; survives crashes, restarts and idle eviction",
        ], theme="cyan", icon="cosmos", src=src("state"))
        c_ai = card(dwid, "Application Insights / OTLP", [
            "Connection string injected as an env var; protocol libraries emit OpenTelemetry traces",
        ], theme="violet", icon="app-insights", src=src("hosted"))
        col(cv, dep.ix, dep.iy, [c_acr, c_mod, c_tool, c_az, c_mem, c_st, c_ai], gap=16)

    # ---------------------------------------------------------------- arrows
    connect(cv, callers, gate, a_side="bottom", b_side="top", num=1, label="request + token", label_size=14, sw=3, gap=6)
    connect(cv, gate, dp, a_side="right", b_side="left", num=2, label="authenticated", label_size=14, label_dy=-14, label_t=0.3, sw=3, gap=6)
    connect(cv, c_ver, sb, a_side="bottom", b_side="top", tb=(c_ver.cx - sb.x) / sb.w, num=3, label="provision", label_size=14, sw=3, gap=6)
    connect(cv, c_id, sb, a_side="bottom", b_side="top", tb=(c_id.cx - sb.x) / sb.w, dash="dashed", label="tokens", label_size=14, sw=2, gap=6)
    y4 = sb.y + sb.h * 0.38
    arrow(cv, [(dp.x + dp.w + 6, y4), (sb.x - 6, y4)], num=4, label="route", label_size=14, label_dy=-14, sw=3, end_head="arrow")
    y6 = sb.y + sb.h * 0.74
    arrow(cv, [(sb.x - 6, y6), (dp.x + dp.w + 6, y6)], dash="dashed", num=6, label="reply", label_size=14, label_dy=-14, sw=2, end_head="arrow")
    xbus = DEP_X - 44
    ys = [c.y + c.h / 2 for c in (c_mod, c_tool, c_az, c_mem, c_st)]
    ysb = sb.y + sb.h / 2
    arrow(cv, [(sb.x + sb.w + 6, ysb), (xbus, ysb)], num=5, sw=3, end_head=None)
    arrow(cv, [(xbus, min(ys + [ysb])), (xbus, max(ys + [ysb]))], sw=3, end_head=None)
    for yy in ys:
        arrow(cv, [(xbus, yy), (c_mod.x - 5, yy)], sw=3, end_head="arrow")
    ai_y = c_ai.y + c_ai.h / 2
    xt = xbus - 74
    arrow(cv, [(sb.x + sb.w + 6, sb.y + sb.h * 0.9), (xt, sb.y + sb.h * 0.9), (xt, ai_y), (c_ai.x - 5, ai_y)], dash="dashed", sw=2,
          end_head="arrow", label="OTel traces", label_size=14, label_t=0.93, label_pos="above", label_dx=-30)
    arrow(cv, [(c_acr.x - 5, c_acr.y + c_acr.h / 2), (c_ver.x + c_ver.w + 6, c_acr.y + c_acr.h / 2)], dash="dashed", sw=2,
          label="image pull", label_size=14, label_dx=20)
    return max(cp.y + cp.h, dep.y + dep.h, steps.bottom)


def band_lifecycle(cv: Canvas, y: float) -> float:
    y = head(cv, y, "D  Session lifecycle - compute follows the session, not the request",
             "Idle sessions hold no compute; their files survive until 30 days of inactivity. Steps 7 and 8 continue the walk-through above.")
    ty = y + 56
    BW, gap = 540, 210
    a = card(BW, "Active", ["Compute is running and requests are routed to it", "$HOME and /files are available; every request resets the idle timer"], theme="green")
    i = card(BW, "Idle", ["No request for the idle timeout (default 15 min)", "Compute deprovisioned; $HOME and /files persisted; no compute billed"], theme="cyan")
    r = card(BW, "Resumed", ["The same session ID is referenced again", "New compute provisioned, state restored: the code finds its files"], theme="green")
    hmax = max(a.h, i.h, r.h)
    a.place(cv, 0, ty, h=hmax)
    i.place(cv, BW + gap, ty, h=hmax)
    r.place(cv, 2 * (BW + gap), ty, h=hmax)
    d = card(BW, "Deleted", ["30 days of inactivity: the session is permanently deleted (REST expires_at: rolling 30 days)"], theme="red")
    d.place(cv, BW + gap, ty + hmax + 84)
    connect(cv, a, i, a_side="right", b_side="left", num=7, label="no request for the idle timeout", label_wrap=gap - 40, label_size=14, label_dy=-14, sw=3, gap=6)
    connect(cv, i, r, a_side="right", b_side="left", num=8, label="same session ID", label_wrap=gap - 40, label_size=14, label_dy=-14, sw=3, gap=6)
    connect(cv, r, a, a_side="top", b_side="top", via=[(r.cx, ty - 40), (a.cx, ty - 40)], label="resumed: active again", label_size=14, sw=2, dash="dashed", gap=6)
    connect(cv, i, d, a_side="bottom", b_side="top", label="30 days idle", label_size=14, sw=3, gap=6)
    tx = 3 * BW + 2 * gap + 100
    tbl = Table([("Topic", 190), "Detail"], [
        ["Idle timeout", "Set per version, default 15 min (900 s); a change creates a new version. azd: sessionConfiguration.idleTimeoutSeconds; over 3,600 s needs azure.ai.agents >= 1.0.0-beta.19"],
        ["Stop vs delete", "Stop kills compute and keeps the files (resumable). Delete also deletes the volume"],
        ["Status values", "creating, active, idle, updating, failed, deleting, deleted, expired"],
        ["Version binding", "Each session is bound to ONE agent version at creation and stays on it"],
    ], w=W - tx, theme="cyan", size=14, head_size=15, first_col_theme="cyan", title="Timers and states", title_size=22)
    tbl.place(cv, tx, ty - 44)
    half = (W - tx - G) / 2
    n_idle = Note(half, "Hosted pages: 2-240 min (120-14,400 s). REST schema for session_configuration.idle_timeout_seconds: 120-3,600 s. Both agree on the 15 min (900 s) default. "
                        "Test any value above 1 hour before you rely on it.", kind="warn", title="Docs disagree: idle-timeout range", src=src("hosted", "sessions"))
    n_idle.place(cv, tx, tbl.bottom + 22)
    n_snap = Note(half, "A version created with enableMemorySnapshot: true (cold-start optimization, enabled through an azd alpha feature switch) restores a startup baseline after idle: "
                        "$HOME, local files and process memory are not preserved. Use it only if your agent does not need $HOME to persist. Details: 'Hosted agents: deploy and operate'.",
                  kind="gotcha", title="Exception: memory snapshots", src=src("snap"))
    n_snap.place(cv, tx + half + G, tbl.bottom + 22)
    return max(d.bottom, tbl.bottom, n_idle.bottom, n_snap.bottom)


def band_contract(cv: Canvas, y: float) -> float:
    y = head(cv, y, "E  Runtime contract and protocols - what your container must do, and which door to expose",
             "Platform-injected variables use the reserved FOUNDRY_ and AGENT_ prefixes. Start with Responses; one agent can expose several protocols.")
    t1 = Table([("Requirement", 215), "Detail"], [
        ["Port", "8088, plain HTTP/1.1 on 0.0.0.0 (the platform terminates TLS; PORT overrides)"],
        ["Health", "GET /readiness returns 200 (non-200 means restart). A readiness timeout surfaces as 424 session_not_ready"],
        ["Protocol routes", "At least one of POST /responses or POST /invocations; WebSocket GET /invocations_ws"],
        ["Shutdown", "Graceful on SIGTERM: stop taking new work, finish in-flight work, flush $HOME"],
        ["Container protocol", "2.0.0 is required (1.0.0 is blocked): set every protocol_versions[].version to 2.0.0"],
        ["Request headers (2.0.0)", "x-agent-user-id: global per-user ID, the primary key for per-user data. x-agent-foundry-call-id: forward unchanged on outbound Foundry calls (the SDKs do)"],
        ["Caller headers", "Forwarded: x-client-*, content negotiation, tracing and correlation, user-agent. Never forwarded: Authorization, Host, Cookie, x-forwarded-*"],
        ["Response headers", "x-agent-session-id, x-platform-server, x-platform-error-source"],
        ["Env vars (injected)", "FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_PROJECT_ARM_ID, FOUNDRY_AGENT_ID, FOUNDRY_AGENT_NAME, FOUNDRY_AGENT_VERSION, FOUNDRY_AGENT_SESSION_ID, "
                                "APPLICATIONINSIGHTS_CONNECTION_STRING, HOME. You set PYTHONNOUSERSITE=1 (Python)"],
    ], w=S(3), theme="green", size=14, head_size=15, first_col_theme="green", title="The container contract", title_size=22)
    t1.place(cv, 0, y)
    t2 = Table([("Protocol", 190), ("Route", 290), ("History and state", 300), "Best for"], [
        [("Responses", "green"), "POST /responses", "Platform manages history by conversation ID; streaming and background", "Most agents; any OpenAI-compatible SDK works as the client. Start here"],
        [("Invocations", "green"), "POST /invocations", "You manage state; session only via the ?agent_session_id= query", "Webhooks, batch and extraction, custom streaming (AG-UI), protocol bridges"],
        [("Invocations (WebSocket)", "green"), "GET /invocations_ws (wss://...?api-version=v1)", "You manage state", "Real-time voice and two-way streaming; text and binary frames, 1 MB frame cap, about 30 min connection cap"],
        [("Activity", "green"), "Platform bridge", "-", "Teams and Microsoft 365: Responses runs the logic, the platform bridges it to Activity"],
        [("A2A", "green"), ".../protocols/a2a", "-", "Agent-to-agent delegation; v1.0 GA, v0.3 preview"],
    ], w=S(3), theme="green", size=14, head_size=15, title="Protocol comparison", title_size=22)
    t2.place(cv, X(3), y)
    yy = max(t1.bottom, t2.bottom) + 50

    # ---- decision tree (horizontal)
    ty = label(cv, 0, yy, "Which protocol?")
    d1 = Box(330, "Chat-style conversation?", shape="diamond", theme="green", size=16, h=120)
    d1.place(cv, 0, ty)
    d2 = Box(330, "Real-time voice or two-way streaming?", shape="diamond", theme="green", size=16, h=120)
    d2.place(cv, 330 + 140, ty)
    r3 = card(560, "Invocations", ["Arbitrary JSON in and out: webhooks, batch, custom streams such as AG-UI, protocol bridges"], theme="green", title_size=18, body_size=14)
    r3.place(cv, 2 * (330 + 140), ty + 60 - r3.h / 2)
    r1 = card(440, "Responses", ["The platform keeps the history and the streaming lifecycle", "Crash recovery is a separate opt-in (see 'Hosted agents: deploy and operate')"], theme="green", title_size=18, body_size=14)
    r1.place(cv, 0, ty + 120 + 80)
    r2 = card(440, "Invocations (WebSocket)", ["Full duplex; pair with Pipecat, LiveKit or Voice Live in your container"], theme="green", title_size=18, body_size=14)
    r2.place(cv, 470, ty + 120 + 80)
    connect(cv, d1, d2, a_side="right", b_side="left", label="no", label_size=15, sw=3, gap=4)
    connect(cv, d2, r3, a_side="right", b_side="left", label="no", label_size=15, sw=3, gap=4)
    connect(cv, d1, r1, a_side="bottom", b_side="top", tb=(d1.cx - r1.x) / r1.w, label="yes", label_size=15, sw=3, gap=4)
    connect(cv, d2, r2, a_side="bottom", b_side="top", tb=(d2.cx - r2.x) / r2.w, label="yes", label_size=15, sw=3, gap=4)
    n_tree = Note(S(3) - 940 - G, "Teams or Microsoft 365 publish: Responses + Activity, bridged automatically. Not sure? Start with Responses - an agent can add Invocations later.",
                  kind="tip", title="Rule of thumb", src=src("hosted"))
    n_tree.place(cv, 940 + G, r1.y)

    # ---- adapters + notes
    t3 = Table([("Library", 130), ("Python", 560), ".NET"], [
        [("Responses", "green"), "azure-ai-agentserver-responses", "Azure.AI.AgentServer.Responses"],
        [("Invocations", "green"), "azure-ai-agentserver-invocations (also serves /invocations_ws)", "Azure.AI.AgentServer.Invocations"],
        [("Core", "green"), "azure-ai-agentserver-core: tasks, streams, FoundryStateStore", "Azure.AI.AgentServer.Core"],
    ], w=S(3), theme="green", size=14, head_size=15, title="AgentServer SDK adapter packages", title_size=22)
    t3.place(cv, X(3), yy)
    n_ad = Note(S(3), "The adapters give you the HTTP server, /readiness, SSE, history hydration (context.get_history()), OpenTelemetry and graceful shutdown - no web-server code of your own. "
                      "Routes are live right after deploy; which ones are active follows protocol_versions on the version (azure.ai.agent service in azure.yaml, or the SDK).",
                kind="info", title="What the libraries add", src=src("contract", "hosted"))
    n_ad.place(cv, X(3), t3.bottom + 22)
    return max(r1.bottom, n_tree.bottom, n_ad.bottom, r2.bottom)


def band_sessions(cv: Canvas, y: float) -> float:
    y = head(cv, y, "F  Sessions, state and isolation keys - who is the user, and where does state live",
             "A session is compute plus files, a conversation is history, the state store is durable key-value. Do not mix them up.")
    sess = card(C, "Session: compute + files", [
        "ID: agent_session_id; a sandbox with $HOME and /files",
        "Created on first use; isolated from every other session; bound to ONE agent version",
        "Responses without agent_session_id lands in a NEW sandbox; a conversation auto-associates a stable session",
        "Invocations: you carry the ID, only as the ?agent_session_id= query parameter",
    ], theme="green", icon="container-apps", src=src("hosted", "sessions"))
    conv = card(C, "Conversation: history", [
        "ID: conversation or previous_response_id",
        "Durable record of messages, tool calls and responses, stored in Foundry; outlives compute",
        "Reachable from the playground, the API, Teams and other channels",
        "Responses: platform-managed. Invocations: yours to manage (memory, Cosmos DB, ...)",
    ], theme="cyan", icon="cosmos", src=src("hosted"))
    store = card(C, "State store: durable key-value", [
        "FoundryStateStore.get_or_create(name, user_isolation=True)",
        "JSON items; survive crashes, restarts and idle eviction",
        "Items age out after a 30-day idle window; writes renew it",
        "Limits, CLI and long-running patterns: 'Hosted agents: deploy and operate'",
    ], theme="cyan", icon="storage", src=src("state"))
    _, rb = row(cv, 0, y, [sess, conv, store], gap=G)
    t = Table([("Operation", 200), "How"], [
        [("Sessions", "green"), "List, create, get, delete and stop sessions. An explicit create can pin version_indicator to a concrete version"],
        [("Files", "green"), "Upload with PUT .../files/content?path= (up to 50 MB); azd ai agent files upload | list | download | delete | mkdir | stat. Files land in $HOME"],
        [("Picking the session", "green"), "Responses: no agent_session_id means a new sandbox; a conversation ties to one session. Invocations: pass ?agent_session_id= (query only)"],
        [("Version pinning", "green"), "A session stays on the version it was created with, even after the endpoint moves on"],
    ], w=S(3), theme="green", size=14, head_size=15, first_col_theme="green", title="Session management APIs", title_size=22)
    t.place(cv, X(3), y)
    yy = max(rb, t.bottom) + 50

    ty = label(cv, 0, yy, "Isolation keys - telling the platform who the user is", theme="red", size=24)
    k1 = card(C, "Entra token (default)", ["isolation_key_source.kind = Entra", "The caller identity comes from the Entra token"],
              theme="red", icon="managed-identity", src=src("isolate"))
    k2 = card(C, "Header key", ["isolation_key_source.kind = Header", "The caller sends x-ms-user-isolation-key"],
              theme="red", icon="key-vault", src=src("keys"))
    k3 = card(C, "Delegated identity", ["An app with its own auth sends x-ms-user-identity (1-256 chars: letters, digits . _ : - @)",
                                          "Needs the custom data action ...UserIdentityImpersonation/action - in no built-in role"],
              theme="red", icon="users", src=src("isolate"))
    _, kb = row(cv, 0, ty, [k1, k2, k3], gap=G)
    pl = card(S(3), "What the platform isolates", [
        "Response chains: previous_response_id cannot cross users",
        "User-isolated state stores (user_isolation=True); x-agent-user-id reaches your container as the key for per-user data",
    ], theme="green", icon="foundry", src=src("isolate", "contract"))
    pl.place(cv, 0, kb + 80)
    for k in (k1, k2, k3):
        connect(cv, k, pl, a_side="bottom", b_side="top", ta=0.5, tb=(k.cx - pl.x) / pl.w, sw=3, gap=5)
    mxc = card(S(3), "Multiplexing: many users on a pool of sessions", [
        "Your middle tier keeps the user-to-session map and partitions your data by (session, user); the platform still isolates response chains per user",
        "! The platform does NOT fence one delegated user from another inside a session: two users routed to one session can see each other's data",
    ], theme="orange", icon="groups", src=src("mux"))
    mxc.place(cv, X(3), ty)
    n1 = Note(S(3), "--isolation-key, --user-isolation-key and --chat-isolation-key were retired from azd; use --user-identity. "
                    "Local runs do not enforce isolation or user-isolated state stores.", kind="gotcha", title="CLI and local runs", src=src("isolate", "keys"))
    n1.place(cv, X(3), mxc.bottom + 22)
    n2 = Note(S(3), "The default caller identity comes from the Entra token. Send x-ms-user-identity only from an app backend that authenticates its users itself, "
                    "and keep any user token out of logs.", kind="tip", title="Choose the narrowest option", src=src("isolate", "obo"))
    n2.place(cv, X(3), n1.bottom + 22)
    return max(pl.bottom, n2.bottom)


def band_identity(cv: Canvas, y: float) -> float:
    y = head(cv, y, "G  Identity, token service and roles - how your code gets tokens and who needs which role",
             "Agent identity = the container's runtime identity. Project managed identity = platform operations such as the ACR pull. Hosted code never holds a blueprint credential.")
    seq = Sequence(cv, 0, y, [("Token service (platform, outside the sandbox)", "red", "managed-identity"),
                              ("Your code in the sandbox", "green", "container-apps"),
                              ("Foundry model, tool or Azure service", "blue", "foundry")],
                   spacing=700, head_w=360, head_h=68, step=62, size=16, label_size=15)
    seq.msg(1, 0, "ManagedIdentityCredential, or a REST GET to IDENTITY_ENDPOINT ?resource=<uri>&api-version=2019-08-01 with the X-IDENTITY-HEADER header", num=1)
    seq.msg(0, 1, "Access token for the agent identity", dash="dashed", num=2,
            note="Optional client_id: other client IDs are rejected (except the blueprint, for the autopilot exchange)")
    seq.msg(1, 2, "Call the service with Authorization: Bearer <token>", num=3)
    seq.msg(2, 1, "Response - RBAC is checked against the agent identity", dash="dashed", num=4)
    seq.note(0, 2, "The sandbox holds no blueprint credential. ManagedIdentityCredential is only the SDK entry point: it talks to the platform token service, "
                   "not to the project managed identity.", kind="gotcha")
    sb_ = seq.end()
    oy = sb_ + 30
    ob1 = card(C, "Delegation through a toolbox", [
        "User delegation for MCP and other tools goes through a Foundry toolbox - the default route",
        "In Microsoft Agent Framework use FoundryToolbox (Python) or AddFoundryToolboxes (.NET)",
    ], theme="red", icon="toolbox", src=src("obo", "hosted"))
    ob2 = card(C, "Microsoft 365 channels: two modes", [
        "User-invoked (interactive): when a user token is present the platform supports OAuth 2.0 on-behalf-of (OBO) with the user's delegated permissions, within Entra tenant policy",
        "Autonomous or background: no user token, so the agent authenticates as its own agent identity",
        "In both cases the agent keeps its dedicated Entra identity for authentication, authorization and audit",
    ], theme="red", icon="mfa", src=src("hosted"))
    ob3 = card(C, "Direct downstream calls with OBO", [
        "Your app backend performs the Entra OBO exchange and forwards the user token in an x-client-* header, together with x-ms-user-identity",
        "! Never combine that user token with the agent identity, and keep tokens out of logs",
    ], theme="red", icon="users", src=src("obo"))
    _, ob_b = row(cv, 0, oy, [ob1, ob2, ob3], gap=G)
    t = Table([("", 150), ("Agent identity", 470), "Project managed identity"], [
        [("Scope", "red"), "Per agent; created automatically at deploy (blueprint + instance)", "Project-wide; system-assigned on the Foundry project"],
        [("Used for", "red"), "The container's runtime auth: model inference, tool access, downstream Azure services", "Platform operations, for example the ACR image pull"],
        [("Your code can use it", "red"), "Yes, through the token service", "No - not the agent's runtime identity"],
        [("Starts with", "red"), "No RBAC except model inference through the project endpoint and session storage", "Needs Foundry User at account scope; Container Registry Repository Reader on ACR"],
    ], w=S(3), theme="red", size=14, head_size=15, first_col_theme="red", title="Two identities, two jobs", title_size=22)
    t.place(cv, X(3), y)
    roles = Table([("Who", 215), ("Does what", 250), ("Role and scope", 520), "Notes"], [
        [("Deployer (person or CI)", "red"), "Create or update the agent and its versions", "Foundry Project Manager at project scope",
         "ARM roles (Owner, Contributor) carry no data-plane rights; the legacy Azure AI Developer role is insufficient"],
        [("Caller", "red"), "Invoke the agent endpoint", "Foundry Agent Consumer (least privilege) or Foundry User", "Entra token for https://ai.azure.com/"],
        [("Agent identity", "red"), "Reach other Foundry resources", "OpenAI endpoint: Cognitive Services OpenAI User or Foundry User. Speech, Content Safety, Vision, Document Intelligence, Language, "
                                                                     "Translator: Cognitive Services User or Foundry User (account scope)", "Assign them yourself"],
        [("Teams publisher", "red"), "Publish through Azure Bot Service", "Microsoft.BotService/* permissions (Owner or Contributor)", ""],
    ], w=S(3), theme="red", size=14, head_size=15, first_col_theme="red", title="Who needs which role (registry and telemetry roles: see 'deploy and operate')", title_size=20)
    roles.place(cv, X(3), t.bottom + 28)
    return max(ob_b, roles.bottom)


def band_calls(cv: Canvas, y: float) -> float:
    y = head(cv, y, "H  Calling models and tools from your container",
             "The agent identity can reach models by default; everything else is granted explicitly, or reached through the Toolbox.")
    t = Table([("Target", 200), ("How your code calls it", 640), "Credential and permission"], [
        [("Foundry models", "blue"), "The project endpoint (FOUNDRY_PROJECT_ENDPOINT) with the Foundry SDK or any OpenAI-compatible client",
         "Agent identity - model inference through the project endpoint works by default"],
        [("Toolbox tools", "orange"), "One Toolbox MCP endpoint: Agent Framework FoundryToolbox / AddFoundryToolboxes, LangGraph AzureAIProjectToolbox, or any MCP Streamable-HTTP client",
         "The toolbox consolidates auth: OAuth identity passthrough, agent identity, key-based and more; user delegation for MCP and other tools goes through it"],
        [("Your Azure services", "gray"), "The service's own SDK with ManagedIdentityCredential (it calls the token service)",
         "You assign RBAC to the agent identity - it starts with none beyond model inference and session storage"],
        [("Other Foundry resources", "blue"), "Account-level endpoints such as OpenAI, Speech, Content Safety, Vision, Document Intelligence, Language, Translator",
         "OpenAI: Cognitive Services OpenAI User or Foundry User; the others: Cognitive Services User or Foundry User (account scope)"],
    ], w=S(4), theme="orange", size=14, head_size=15, first_col_theme="orange", title="Outbound calls and what each one needs", title_size=22)
    t.place(cv, 0, y)
    tb = card(S(2), "Toolbox in a hosted agent", [
        "Hosted agents reach Foundry-managed tools - Code Interpreter, Web Search (Grounding with Bing Custom Search), Azure AI Search, OpenAPI, MCP, A2A, Skills and more - "
        "through a Toolbox MCP endpoint in your project, not through the agent definition",
        "Agent Framework agents use FoundryToolbox (Python) or AddFoundryToolboxes (.NET); other runtimes use standard MCP client libraries. Details: 'Foundry Toolbox'",
    ], theme="orange", icon="toolbox", src=src("hosted", "toolbox"))
    tb.place(cv, X(4), y)
    return max(t.bottom, tb.bottom)


def band_scale(cv: Canvas, y: float) -> float:
    y = head(cv, y, "I  Scale, size and quotas - scale per session, not per replica",
             "No replica count, no warm pool; --min-replicas and --max-replicas were removed. Each request resets the idle timer; idle sessions cost no compute.")
    ty = label(cv, 0, y, "One sandbox per active session; idle sessions hold none")
    bw, bg_ = 340, 21
    names = [("Session A", True), ("Session B", True), ("Session C", True), ("Session D", False), ("Session E", False)]
    by = ty + 8
    for i, (nm, act) in enumerate(names):
        b_ = Box(bw, nm, sub="active: its own sandbox with the cpu + memory of ONE session" if act else "idle: compute deprovisioned, $HOME and /files kept",
                 theme="green" if act else "gray", fill="hatch" if act else "none", dash="solid" if act else "dashed", size=18, sub_size=14, h=130)
        b_.place(cv, i * (bw + bg_), by)
    hb = by + 130 + 26
    bracket(cv, 0, 3 * bw + 2 * bg_, hb)
    cv.text(0, hb + 22, "Billed: CPU + memory consumed across all active sessions - oversizing multiplies cost by concurrency", size=15,
            color=THEMES["yellow"].deep, w=3 * bw + 2 * bg_, align="center")
    bracket(cv, 3 * (bw + bg_), 5 * bw + 4 * bg_, hb)
    cv.text(3 * (bw + bg_), hb + 22, "No compute billed while deprovisioned", size=15, color=MUTED, w=2 * bw + bg_, align="center")
    chips = ["no replica count", "no warm pool", "--min/--max-replicas removed", "new sandbox per session on demand", "scale to zero when idle"]
    ch = ChipFlow(chips, S(3), gap=10, theme="green", size=15, fill="soft")
    ch.place(cv, 0, hb + 70)
    RW = (S(3) - G) // 2
    st = Table([("Source", 200), ("CPU", 330), "Memory"], [
        ["Concept page", "0.5 / 1 / 2 vCPU", "1 / 2 / 4 GiB"],
        ["azure.yaml reference", "0.25 to 4.0", "0.5Gi to 8.0Gi"],
        ["API error text", "400: CPU and Memory must be specified as a valid resource tier", ""],
    ], w=RW, theme="yellow", size=14, head_size=15, title="Sandbox sizes - docs disagree", title_size=22, first_col_theme="yellow")
    st.place(cv, X(3), y)
    sn = Note(RW, "Disk: up to 20 GiB per session at 1 vCPU or more (less for smaller tiers; about 20% is reserved), shared by image, $HOME and other writable paths. "
                  "Right-size with App Insights > Investigate > Performance: if sustained peaks exceed about 70% of the allocation raise the next version, if far below lower it - "
                  "and retest, because versions are immutable.", kind="tip", title="Disk and right-sizing", src=src("hosted", "azyaml"))
    sn.place(cv, X(3), st.bottom + 22)
    q = card(RW, "Quotas and pricing", [
        "Concurrent sessions per subscription per region: 2,000 in 7 regions, 1,000 elsewhere; only provisioning and running sessions count",
        "429: session_quota_exceeded, regional_session_quota_exceeded, subnet_exhausted",
        "Hosted-session quota can be raised through support",
        "Billing: CPU + memory of active sessions; rates are on the Agent Service pricing page - no price is drawn here",
    ], theme="yellow", icon="reservations", src=src("limits", "pricing"))
    q.place(cv, X(3) + RW + G, y)
    return max(ch.bottom, sn.bottom, q.bottom)


REGIONS = ["Australia East", "Brazil South", "Canada Central", "Canada East", "Central US", "East US", "East US 2", "France Central",
           "Germany West Central", "Italy North", "Japan East", "Japan West", "Korea Central", "North Central US", "Norway East",
           "Poland Central", "South Africa North", "South Central US", "South India", "Southeast Asia", "Spain Central",
           "Sweden Central", "Switzerland North", "Switzerland West", "UAE North", "UK South", "UK West", "West Central US",
           "West Europe", "West US", "West US 3"]
HIGH_QUOTA = {"Canada Central", "East US 2", "Japan East", "North Central US", "South Africa North", "Southeast Asia", "Sweden Central"}


def band_regions(cv: Canvas, y: float) -> float:
    y = head(cv, y, "J  Regions - where hosted agents run",
             "Responses, Invocations and Invocations (WebSocket) are available in every hosted-agent region. Hosted agents are not available in Azure Government.")
    with cv.panel(0, y, title="Hosted-agent regions listed on the hosted-agents page (31, as of 2026-11-03)", theme="gray", style="dotted", pad=22,
                  title_size=22, w=S(4)) as pn:
        lg = [Chip("2,000 concurrent sessions per subscription per region", theme="yellow", size=14, fill="soft"),
              Chip("1,000 concurrent sessions", theme="gray", size=14, fill="soft"),
              Chip("UK West: only on the hosted page", theme="orange", size=14, fill="soft", dash="dashed")]
        lx = pn.ix
        for c_ in lg:
            c_.place(cv, lx, pn.iy)
            lx += c_.w + 14
        items = [Chip(r_, theme="yellow" if r_ in HIGH_QUOTA else ("orange" if r_ == "UK West" else "gray"), size=15, fill="soft",
                      dash="dashed" if r_ == "UK West" else "solid") for r_ in REGIONS]
        flow = ChipFlow(items, S(4) - 44, gap=10)
        flow.place(cv, pn.ix, pn.iy + 46)
    n1 = Note(S(2), "The hosted-agents page lists 31 regions (it adds UK West); the Agent Service limits page lists 30 for Agents; a June 2026 Build blog said 20 regions "
                    "during the preview. Routines are unavailable in UK West. Check the live pages for your region before you plan around it.", kind="warn",
              title="Docs disagree: region count", src=src("hosted", "limits"))
    n1.place(cv, X(4), y)
    n2 = Note(S(2), "Azure Government (US Gov Virginia, US Gov Arizona): prompt agents are available, hosted agents are not.", kind="gotcha",
              title="Not in Azure Government", src=src("gov"))
    n2.place(cv, X(4), n1.bottom + 22)
    return max(pn.y + pn.h, n2.bottom)


def band_disagree(cv: Canvas, y: float) -> float:
    y = head(cv, y, "K  Docs disagree and gotchas - as of 2026-11-03",
             "Where two Learn pages (or Learn and the REST schema) give different answers, both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 240), ("One page says", 640), ("Another page says", 700), "How to read it"], [
        [("Traffic splitting across versions", "orange"), "Concept and manage pages: the endpoint serves one version at 100%; traffic splitting is not supported",
         "The production guide documents a canary 90/10 -> 50/50 -> 100/0 with azd ai agent endpoint update; the REST/SDK model has traffic_percentage; a blog says weighted rollouts",
         "Plan for one version at 100% unless you verify weighted routing yourself (details: 'Hosted agents: deploy and operate')"],
        [("Idle-timeout range", "orange"), "Hosted pages: 2-240 min (120-14,400 s), default 15 min", "REST schema: 120-3,600 s, default 900 s",
         "The 15 min default is common ground; test values above 1 hour"],
        [("Sandbox sizes", "orange"), "Concept page: three tiers (0.5 vCPU / 1 GiB, 1 / 2, 2 / 4)", "azure.yaml reference: cpu 0.25-4.0, memory 0.5Gi-8.0Gi; the API says valid resource tier",
         "Stick to the three documented tiers unless you test others"],
        [("Region count", "orange"), "Hosted-agents page: 31 regions (adds UK West)", "Limits page: 30 for Agents; a June 2026 blog said 20 during preview", "Check the live hosted-agents page"],
        [("Version provisioning time", "orange"), "Deploy page: typically under 1 minute", "Manage page: 2-5 minutes", "Poll status until active"],
        [("Subnet ranges for VNet injection", "orange"), "The virtual-networks how-to allows RFC 6598 100.64.0.0/10 (minus three reserved sub-ranges)",
         "The networking deep dive and the FAQ say private RFC 1918 ranges only", "Prefer RFC 1918 ranges"],
        [("A2A on hosted agents", "orange"), "The how-to that enables an A2A endpoint describes prompt agents only",
         "The hosted-agents concept page and the azure.yaml reference list a2a as a hosted protocol", "Verify before you rely on incoming A2A"],
    ], w=S(4), theme="orange", size=14, head_size=15, first_col_theme="orange", title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    fn = cv.text(0, t.bottom + 12, "Also: manage-hosted-agent still shows a [TO VERIFY] marker and register-external-agent has TODO(verify) twice - treat those passages as unconfirmed.",
                 size=14, color=MUTED)
    nd = Note(S(4), "Not published as of 2026-11-03: a cold-start latency figure or SLA, how a warm pool behaves, hosted-agent prices (rates live only on the Agent Service pricing page), "
                    "a Foundry Agent Service SLA, and what the session field stopped_at 'idle-billing reconciliation' means (also why a session is 'stopped' rather than 'idle'). "
                    "Nothing on this canvas fills those gaps.", kind="quote", title="What the docs do not say",
              src=src("hosted", "pricing", "sessions"))
    nd.place(cv, 0, fn.bottom + 18)
    g1 = Note(S(2), "Invocations binds a session only through the ?agent_session_id= query parameter. Container protocol 1.0.0 is blocked - set every protocol_versions[].version to 2.0.0. "
                    "Local runs do not enforce isolation or user-isolated state.", kind="gotcha", title="Contract gotchas", src=src("contract", "sessions"))
    g1.place(cv, X(4), y)
    g2 = Note(S(2), "Do not put secrets in container images or environment variables - use managed identities and connections, with secrets in a managed store such as Key Vault. "
                    "Treat $HOME uploads as untrusted: keep session data apart from application files (Python: PYTHONNOUSERSITE=1).", kind="gotcha",
              title="Secrets and uploads", src=src("hosted", "env"))
    g2.place(cv, X(4), g1.bottom + 22)
    g3 = Note(S(2), "This canvas stays on the developer and operator view. For the per-session Micro VM cut-away, networking hops and what nobody has documented, see "
                    "'Hosted agent runtime: how a container becomes an agent endpoint' under Under the hood.", kind="info", title="Looking for the internals?")
    g3.place(cv, X(4), g2.bottom + 22)
    return max(nd.bottom, g3.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Hosted agents: your code on Foundry's runtime",
        "Containerized or zip-deployed agents on Foundry Agent Service - one VM-isolated sandbox per session  |  concepts, runtime contract, sessions, identity, scale  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Tools and toolbox", "orange"), ("Identity and security", "red"),
                           ("Memory and knowledge", "teal"), ("Observability", "violet"), ("Guardrails", "pink"), ("Networking", "indigo"),
                           ("State and data", "cyan"), ("Cost and capacity", "yellow")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Prompt agents in depth", "Hosted agents: deploy and operate",
                "Hosted agent runtime: how a container becomes an agent endpoint", "Foundry Toolbox", "Agent identity and delegation",
                "Agent Service disaster recovery"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    GAPB = 50
    y = band_hero(cv, y) + 56
    y = band_what(cv, y) + GAPB
    y = band_compare(cv, y) + GAPB
    y = band_arch(cv, y) + GAPB
    y = band_lifecycle(cv, y) + GAPB
    y = band_contract(cv, y) + GAPB
    y = band_sessions(cv, y) + GAPB
    y = band_identity(cv, y) + GAPB
    y = band_calls(cv, y) + GAPB
    y = band_scale(cv, y) + GAPB
    y = band_regions(cv, y) + GAPB
    y = band_disagree(cv, y) + GAPB
    sources(cv, 0, y, [
        ("What are hosted agents?", U["hosted"][1]), ("Hosted agent runtime contract", U["contract"][1]),
        ("Hosted agent token service", U["token"][1]), ("Hosted agent permissions", U["perms"][1]),
        ("Agent identity", U["ident"][1]), ("Manage hosted agent sessions", U["sessions"][1]),
        ("Isolate sessions per user", U["isolate"][1]), ("Pass isolation keys", U["keys"][1]),
        ("Use the on-behalf-of flow", U["obo"][1]), ("Use a toolbox in a hosted agent", U["toolbox"][1]),
        ("Host agents built with frameworks", U["fw"][1]), ("Agent Framework: Foundry hosted agent", U["maf"][1]),
        ("Agent Service limits, quotas and regions", U["limits"][1]), ("Azure pricing: Foundry Agent Service", U["pricing"][1]),
        ("Configure virtual networks for agents", U["vnet"][1]), ("Agents networking deep dive", U["netdeep"][1]),
    ], w=W, cols=4)
