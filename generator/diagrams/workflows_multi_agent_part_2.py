"""Workflows, routines, A2A and multi-agent orchestration (part 2): the A2A tool (outbound) and incoming A2A endpoint, A2A authentication,
Responses API multi-agent orchestration (Preview), routines (Preview), Microsoft Foundry Canvas (Preview) and the doc conflicts.

Part 1 ('workflows-multi-agent') holds the orchestration map, declarative workflows (retiring 2026-12-01), the Microsoft Agent Framework patterns
and the human-in-the-loop map.  Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="workflows-multi-agent-part-2", title="Multi-agent orchestration in depth: A2A, Responses and routines", section="2", group="Agent Service", order=13.5,
    description="A2A in depth (outbound tool call sequence, incoming endpoint, six authentication methods), Responses API multi-agent orchestration "
                "(Preview), routines (Preview) and Microsoft Foundry Canvas.",
    tags=["a2a", "multi-agent", "responses-api", "routines", "authentication", "canvas"],
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
    a2atool=("Connect to an A2A agent endpoint", learn("agents/how-to/tools/agent-to-agent")),
    a2aauth=("Agent2Agent (A2A) authentication", learn("agents/concepts/agent-to-agent-authentication")),
    a2ain=("Enable an incoming A2A endpoint", learn("agents/how-to/enable-agent-to-agent-endpoint")),
    userdeleg=("Configure user delegation for tools", learn("agents/how-to/configure-user-delegation")),
    register=("Register a custom agent in Foundry Control Plane", learn("control-plane/register-custom-agent")),
    toolbox=("What is a toolbox?", learn("agents/concepts/toolbox-overview")),
    multi=("Multi-agent orchestration with the Responses API", learn("openai/how-to/responses-multi-agent")),
    routines=("Routines in Foundry Agent Service", learn("agents/concepts/routines")),
    useroutines=("Automate agents with routines", learn("agents/how-to/use-routines")),
    routrest=("Create or update a routine (REST)", learn("reference/rest/create-or-update-routine")),
    reminder=("Reminder tool for self-scheduling agents", learn("agents/how-to/tools/reminder-tool")),
    canvas=("Microsoft Foundry Canvas", learn("agents/concepts/foundry-agent-canvas")),
    canvasqs=("Quickstart: deploy your first hosted agent", learn("agents/quickstarts/quickstart-hosted-agent")),
    workflow=("Build a workflow in Microsoft Foundry (retiring)", learn("agents/concepts/workflow")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    lowcode=("Use and migrate declarative workflows (VS Code)", learn("how-to/develop/vs-code-agents-workflow-low-code")),
    procode=("Create hosted agents (VS Code, workflow sample)", learn("how-to/develop/vs-code-agents-workflow-pro-code")),
    maf=("Agent Framework: workflow orchestrations", learn("agent-framework/workflows/orchestrations", base="")),
    rbac=("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
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


def lk(label, key):
    return {"text": label, "link": U[key][1], "color": LINK}


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


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
    lab = {"ga": "GA", "preview": "Preview", "retiring": "Retiring", "new": "New", "classic": "Classic"}.get(kind, kind)
    bw = metrics.line_width(lab, 13) + 18
    draw_badge(cv, blk.right - bw + dx + 10, blk.y + dy, kind)


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "a2a = 1.0 GA", "Use the a2a tool type for new integrations; a2a_preview (A2A 0.3) stays Preview for existing ones. Incoming A2A defaults to v0.3.", "pink"),
        Tile(C, "6 auth methods", "Key-based, agent identity, project managed identity, Entra user delegation, OAuth passthrough, or none.", "red"),
        Tile(C, "60 days", "Tasks and contexts on a Foundry A2A target are kept 60 days from the last write. Text only, no streaming.", "cyan"),
        Tile(C, "3 concurrent", "Responses multi-agent (Preview): max_concurrent_subagents defaults to 3 across the whole tree; GPT-5.6 models only.", "blue"),
        Tile(C, ">= 5 min", "Routine schedule minimum. Up to 5 delivery attempts per run, 30 s per downstream request; Preview.", "violet"),
        Tile(C, "Canvas in Copilot", "Microsoft Foundry Canvas (Preview): build, inspect and deploy hosted agents from the GitHub Copilot App.", "gray"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: A2A
def band_a2a(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  A2A - call another agent through the tool, or expose yours as an endpoint",
             "The A2A tool lets a Foundry agent exchange context with any endpoint that speaks the A2A protocol. The remote agent answers; your agent composes the reply.")
    top = y
    seq = Sequence(cv, 0, top, [("User or app", "gray", "user"), ("Foundry caller agent", "green", "agent"), ("Remote A2A agent", "pink", "a2a")],
                   spacing=690, head_w=250, head_h=62, size=16, label_size=15)
    seq.msg(0, 1, "Prompt: the user asks for something the remote agent is good at", num=1)
    yy = seq.msg(1, 1, "Model decides to use the A2A tool")
    numbered(cv, seq.actors[1][0] - 26, yy + 14, 2, theme="green", d=26, size=15)
    yy = seq.msg(1, 1, "Read the project connection: endpoint, auth type, credentials")
    numbered(cv, seq.actors[1][0] - 26, yy + 14, 3, theme="green", d=26, size=15)
    seq.msg(1, 2, "GET the agent card - anonymous by default; credentials only if send_credentials_for_agent_card = true", num=4)
    seq.msg(2, 1, "Agent card: description and skills", dash="dashed", note="Descriptions may reach the model context - treat them as untrusted input")
    seq.msg(1, 2, "Send the task over A2A (1.0 = JSON-RPC) with the connection's auth", num=5)
    seq.msg(2, 1, "Result as text", dash="dashed", num=6, note="Foundry targets: text only, no streaming; task and context kept 60 days")
    seq.msg(1, 0, "Caller composes the answer and keeps managing the conversation", dash="dashed", num=7)
    sb = seq.end()
    # right column
    tt = Table(
        [("Tool type", 190), ("SDK class", 330), ("A2A version", 150), ("Status", 120)],
        [
            [ct("a2a", "pink"), "A2ATool / A2AToolboxTool", "1.0", ("GA", "green")],
            [ct("a2a_preview", "pink"), "A2APreviewTool / A2APreviewToolboxTool", "0.3", ("Preview", "yellow")],
        ], w=S(3) - 400, theme="pink", size=14, head_size=15, title="Two tool types (as of 2026-11-03)", title_size=22)
    tt.place(cv, X(3), top)
    n0 = Note(380, "Use the GA a2a type for new integrations. The Connected Agents tool of classic agents is not in the new Agent Service.", kind="tip",
              title="Which one", size=14, src=src("a2atool"))
    n0.place(cv, tt.right + 24, top)
    c1 = card(S(3) // 2 - 12, "How to attach it", [
        "Create a project connection first (portal Tools > Connect tool > Custom > Agent2Agent, azd, or REST); the tool references it by project_connection_id",
        "Prompt agents attach the tool directly; hosted agents reach it through a toolbox MCP endpoint",
        "A toolbox is the recommended home: reuse across agents and runtimes, central credentials, versioning, policy",
        "SDKs: Python azure-ai-projects >= 2.5.0, C#, TypeScript @azure/ai-projects >= 2.6.0, Java azure-ai-agents 2.0.0",
    ], theme="pink", icon="a2a", icon_size=40, src=src("a2atool", "toolbox"))
    c2 = card(S(3) // 2 - 12, "Roles and the Foundry-agent target", [
        "Foundry Project Manager creates the A2A project connection; Foundry User creates and tests the agent",
        "Target is a Foundry agent: set the connection target to .../agents/{agent}/endpoint/protocols/a2a with audience https://ai.azure.com",
        "Do not set an agent card path: Foundry resolves it and negotiates the A2A version",
        "The caller needs Foundry Agent Consumer (or higher) on the target; incoming A2A must be enabled there",
    ], theme="red", icon="managed-identity", src=src("a2atool", "rbac"))
    ry = max(tt.bottom, n0.bottom) + 24
    c1.place(cv, X(3), ry)
    c2.place(cv, X(3) + c1.w + 24, ry)
    y1 = max(sb, c1.bottom, c2.bottom) + 44
    # incoming + hosting elsewhere + caution
    a = card(C * 2 + G, "Incoming A2A endpoint on a Foundry agent", [
        "Expose an agent as an A2A server: one PATCH adds agent_card (description, version, skills) and protocol_configuration.a2a next to responses",
        "A2A v1.0 (GA, JSON-RPC) or v0.3; if no version is chosen Foundry serves v0.3, so pin v1.0 for production",
        "Entra only (no API keys, no anonymous card); callers need Foundry Agent Consumer at project or agent scope",
        "Text modality only, no streaming; tasks and contexts retained 60 days from the last write",
        "The how-to describes prompt agents; the full PATCH walk-through is on 'Prompt agents: harness, A2A, routines and migration'",
    ], theme="pink", icon="a2a", icon_size=40, badge="preview", src=src("a2ain"))
    b = card(C * 2 + G, "Agents that live outside Agent Service", [
        "# Option 1: register in Foundry Control Plane",
        "Pick A2A as the protocol; Foundry generates a proxy URL and discovers the card at /.well-known/agent-card.json",
        "Access control and monitoring come through the AI gateway",
        "# Option 2: wrap a Foundry agent in your own A2A server",
        "Use an A2A SDK (Python, .NET or JavaScript), call the agent through the Responses API, serve the card, deploy, then register it",
    ], theme="grape", icon="a2a", icon_size=40, src=src("a2atool", "register"))
    d = Note(C * 2 + G, "Third parties, not Microsoft, run most A2A endpoints and Microsoft did not test them. The tool can pass custom headers; review everything you share, "
                        "log it for audit, prefer endpoints hosted by trusted providers over proxies, and enforce permissions and approvals independently of model-generated decisions. "
                        "The endpoint must be reachable with a valid TLS certificate. Azure Government: the A2A tool is not available.", kind="gotcha",
             title="Trust and reach", size=15, src=src("a2atool", "gov"))
    a.place(cv, 0, y1)
    b.place(cv, C * 2 + G + G, y1)
    d.place(cv, 2 * (C * 2 + G) + 2 * G, y1)
    return max(a.bottom, b.bottom, d.bottom)


# ================================================================================================ band 2: authentication
def band_auth(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  A2A authentication - choose the identity the remote agent sees",
             "Two scenarios: shared authentication (every user has the same identity, no user context) and individual authentication (the user's own context persists).")
    top = y
    # decision tree (left, S(3))
    sx = 0
    start = Box(210, "Call a remote A2A agent", theme="gray", h=96, size=18, fill="hatch", icon="a2a", icon_pos="top", icon_size=34)
    start.place(cv, sx, top + 200)
    q1 = Box(270, "Must each user keep their own identity?", theme="yellow", shape="diamond", h=190, size=17, fill="hatch")
    q1.place(cv, sx + 290, top + 153)
    q2 = Box(270, "Does the endpoint accept Entra tokens?", theme="yellow", shape="diamond", h=170, size=16, fill="hatch")
    q2.place(cv, sx + 650, top + 36)
    q3 = Box(270, "Is the remote agent another Foundry agent?", theme="yellow", shape="diamond", h=170, size=16, fill="hatch")
    q3.place(cv, sx + 650, top + 307)
    LXX, LW_ = 1060, 716
    leaves = [
        ("Entra: agent identity", "App-only call to another Foundry agent or an Azure service; roles go to the agent identity", "red", top - 2),
        ("Entra: project managed identity", "All agents in the project share one identity; roles go to the project identity", "red", top + 78),
        ("Key-based", "Header name + value from the project connection; shared secret only", "orange", top + 158),
        ("Unauthenticated", "Only public or network-protected endpoints", "gray", top + 238),
        ("Entra client user delegation", "UserEntraToken (compatibility) or AgentOnBehalfOfUser (Preview)", "red", top + 318),
        ("OAuth identity passthrough", "Per-user consent; managed or custom OAuth", "pink", top + 398),
    ]
    lb = []
    for t_, s_, th, ly in leaves:
        b_ = Box(LW_, t_, sub=s_, theme=th, h=68, size=18, sub_size=14, fill="hatch")
        b_.place(cv, LXX, ly)
        lb.append(b_)
    connect(cv, start, q1, a_side="right", b_side="left", sw=2.5)
    connect(cv, q1, q2, a_side="top", b_side="left", route="elbow", sw=2.5, label="no: shared", label_size=14, label_dy=-4)
    connect(cv, q1, q3, a_side="bottom", b_side="left", route="elbow", sw=2.5, label="yes: individual", label_size=14, label_dx=60, label_dy=4)
    connect(cv, q2, lb[0], a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, q2, lb[1], a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, q2, lb[2], a_side="right", b_side="left", route="elbow", sw=2.5, dash="dashed")
    connect(cv, q2, lb[3], a_side="right", b_side="left", route="elbow", sw=2.5, dash="dashed")
    connect(cv, q3, lb[4], a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, q3, lb[5], a_side="right", b_side="left", route="elbow", sw=2.5, dash="dashed")
    xm = (q2.right + 6 + LXX - 6) / 2
    for txt, ty in (("yes", top + 38), ("no", top + 198), ("yes", top + 358), ("no", top + 438)):
        cv.text(xm + 10, ty, txt, size=14, color="#c92a2a")
    cv.text(0, top + 482, "Decision guide derived from the docs' 'Choose an authentication method' table. Learn: Agent2Agent (A2A) authentication", size=12, color=LINK, link=U["a2aauth"][1])
    # OAuth passthrough flow (right S(3))
    st = Steps(S(3) // 2 - 12, "OAuth identity passthrough: how it works", [
        "First interaction: Agent Service generates a consent link for the user",
        "The user opens it, signs in to the remote service and authorizes the agent",
        "Agent Service stores the user's access and refresh tokens, scoped to that user and agent",
        "Later calls carry the user's access token; an expired one is renewed with the refresh token",
    ], theme="pink", num_theme="pink", src=src("a2aauth"))
    st.place(cv, X(3), top)
    c1 = card(S(3) // 2 - 12, "Tokens and OAuth options", [
        "Access token: short-lived (typically 1 hour). Refresh token: hours to weeks, or until revoked",
        "Managed OAuth: Microsoft or the endpoint publisher owns the app registration - use it when available",
        "Custom OAuth: you supply client ID, secret if required, authorization URL, token URL, refresh URL and scopes",
        "Add the redirect URL that Agent Service gives you to your app registration's allowed redirect URIs",
        "Users need Foundry Agent Consumer on the project or agent hosting the caller (Foundry User also works but is meant for builders)",
    ], theme="pink", icon="oauth", icon_size=40, src=src("a2aauth"))
    c1.place(cv, X(3) + st.w + 24, top)
    y1 = top + 530
    t = Table(
        [("Method", 250), ("What Agent Service does", 840), ("User context", 150), ("What you configure", 1112)],
        [
            [ct("Key-based", "orange"), "Reads the credential (header name + value) from the project connection and adds it to every request",
             ("No", "red"), "API key, PAT or secret from the publisher; formats: Authorization, x-api-key or a custom header. Anyone with project access can read the secret"],
            [ct("Entra: agent identity", "red"), "Requests a token for the agent's own identity from Entra and sends it (connection auth type agentic-identity + audience)",
             ("No", "red"), "Assign the needed roles on the underlying service (for example Cosmos DB Data Reader) to the agent identity"],
            [ct("Entra: project managed identity", "red"), "Requests a token with the project's managed identity (project-managed-identity + audience)",
             ("No", "red"), "Assign roles to the project identity; every agent in the project shares it"],
            [ct("Entra: client user delegation", "red"), "Keeps the incoming Entra user's context when calling another Foundry agent. UserEntraToken is the compatibility path; "
                                                           "AgentOnBehalfOfUser (Preview) needs the AgentBlueprint scheme on the source endpoint", ("Yes", "green"),
             "Target must support the chosen type, audience and permissions; consent and migration steps are in 'Configure user delegation'"],
            [ct("OAuth identity passthrough", "pink"), "Consent link, then stores per-user tokens and refreshes them", ("Yes", "green"),
             "Managed or custom OAuth; works with Microsoft and non-Microsoft endpoints that support OAuth 2.0"],
            [ct("Unauthenticated", "gray"), "Sends no credentials", ("No", "red"), "Use only for public endpoints, dev endpoints or endpoints protected at the network level"],
        ], w=S(4), theme="red", size=14, head_size=15, title="The six methods side by side", title_size=22)
    t.place(cv, 0, y1)
    n1 = Note(S(2), "The agent card fetch is anonymous by default - none of the methods above apply to it. Set send_credentials_for_agent_card = true only when the publisher "
                    "confirms the card path needs auth; credentials then go only to the host in base_url and only over HTTPS (HTTP, or an agent_card_path on another host, is ignored).",
              kind="warn", title="Agent card credentials", size=15, src=src("a2aauth"))
    n1.place(cv, X(4), y1)
    n2 = Note(S(2), "Anyone with access to the project can read secrets stored in a project connection. Store only shared secrets there; for per-user access use "
                    "Entra user delegation or OAuth passthrough. Rotate tokens, use least-privilege credentials and audit connection access.", kind="gotcha",
              title="Key-based secrets are project-wide", size=15, src=src("a2aauth"))
    n2.place(cv, X(4), n1.bottom + 22)
    return max(t.bottom, n2.bottom)


# ================================================================================================ band 3: Responses multi-agent
def band_responses(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Responses API multi-agent orchestration (Preview) - one request, a tree of subagents",
             "Azure OpenAI Responses API with api-version=preview and GPT-5.6 models. The model decides whether delegation helps; your app still runs every developer function.")
    top = y
    # --- tree panel (left S(2))
    PWd = S(2)
    with cv.panel(0, top, title="The agent tree", sub=wrap("The agent that receives the request is /root; subagents get hierarchical names", PWd - 50, 15), theme="blue",
                  style="solid", fill="soft", pad=22, title_size=26, sub_size=15, min_w=PWd, min_h=660) as p:
        root = Box(240, "/root", sub="delegates, waits, reconciles and writes the final answer", theme="blue", h=118, size=22, sub_size=14, fill="hatch")
        root.place(cv, p.ix, p.iy + 125)
        kids = []
        ky = p.iy + 36
        for nm, sb_ in (("/root/researcher", "own context, same model and tools"), ("/root/reviewer", "can spawn its own subagents"), ("/root/writer", "runs in parallel")):
            b = Box(330, nm, sub=sb_, theme="blue", h=84, size=19, sub_size=13, fill="hatch")
            b.place(cv, root.right + 110, ky)
            kids.append(b)
            ky += 84 + 22
        tester = Box(300, "/root/reviewer/tester", theme="blue", h=84, size=18, fill="hatch", dash="dashed")
        tester.place(cv, kids[1].right + 80, kids[1].y)
        for k in kids:
            connect(cv, root, k, a_side="right", b_side="left", route="elbow", sw=2.5)
        cv.text(root.right + 14, kids[0].y - 26, "spawn_agent", size=14)
        connect(cv, kids[1], tester, a_side="right", b_side="left", sw=2.5)
        cv.text(p.ix, p.iy + 362, "Hosted collaboration actions (service-run; your app must not execute them or return outputs for them)", size=15, color=THEMES["blue"].deep)
        ChipFlow(["spawn_agent", "send_message", "followup_task", "wait_agent", "interrupt_agent", "list_agents"], w=PWd - 50, theme="blue", size=15).place(cv, p.ix, p.iy + 388)
        cv.text(p.ix, p.iy + 446, "Extra output items in the response", size=15, color=THEMES["blue"].deep)
        ChipFlow(["multi_agent_call", "multi_agent_call_output", "agent_message (encrypted)"], w=PWd - 50, theme="violet", size=15, fill="soft").place(cv, p.ix, p.iy + 472)
        cv.text(p.ix, p.iy + 524, "Preserve these items when you replay state or collect traces; never show encrypted agent messages to users.", size=14, color=MUTED, wrap=PWd - 50)
    # --- sequence (middle S(2))
    seq = Sequence(cv, X(2), top, [("Your app", "gray", "app"), ("Responses API: /root", "blue", "openai"), ("Subagents", "blue", "agent")], spacing=474, head_w=220, head_h=62,
                   size=16, label_size=15)
    seq.msg(0, 1, "POST /responses?api-version=preview with multi_agent { enabled, max_concurrent_subagents: 3 } and your function tools", num=1)
    seq.msg(1, 2, "/root spawns subagents with spawn_agent (a hosted action)", num=2)
    seq.msg(2, 1, "A subagent calls a developer function: function_call", dash="dashed", num=3)
    seq.msg(1, 0, "Response completes or pauses with the pending function_call items", dash="dashed", num=4)
    seq.msg(0, 1, "Your app runs EVERY function_call and returns function_call_output", num=5,
            note="HTTP: send them in the next request. WebSocket: response.inject")
    seq.msg(2, 1, "Subagents finish; findings reach /root (agent_message, encrypted)", dash="dashed", num=6)
    seq.msg(1, 0, "Final answer from /root (message item, phase final_answer)", dash="dashed", num=7)
    sb = seq.end()
    # --- when to use (right S(2))
    t = Table(
        [("Use multi-agent when", 560), ("Prefer one agent when", 560)],
        [
            ["Work splits into independent, bounded tasks", "Each step depends directly on the previous step"],
            ["Separate context improves focus", "The task is small enough for one short run"],
            ["Parallel exploration cuts wall-clock time", "Agents would contend over the same mutable resource"],
            ["Comparing independent findings improves coverage", "You need a fixed, deterministic execution graph"],
        ], w=S(2), theme="blue", size=14, head_size=15, title="Choose when to use it", title_size=22)
    t.place(cv, X(4), top)
    n1 = Note(S(2), "Subagents can raise token use and may not help tasks that need an ordered chain of reasoning, frequent writes to shared state, or one slow external "
                    "operation. The model decides whether to delegate; make the workstreams explicit in the input, or add developer instructions such as 'Do not create "
                    "subagents unless the user explicitly asks'.", kind="tip", title="Control delegation", size=15, src=src("multi"))
    n1.place(cv, X(4), t.bottom + 22)
    n2 = Note(S(2), "This is the Azure OpenAI Responses API with api-version=preview, not a Foundry agent resource. It is Preview and works with GPT-5.6 models only "
                    "(check model availability for your region).", kind="warn", title="Not a Foundry agent", size=15, src=src("multi"))
    n2.place(cv, X(4), n1.bottom + 22)
    y1 = max(top + 660, sb, n2.bottom) + 44
    # --- detail cards
    req = card(C, "The request", [
        "POST https://<resource>.openai.azure.com/openai/v1/responses?api-version=preview (beta Responses client)",
        "model = your deployment name; multi_agent.enabled = true; max_concurrent_subagents default 3, counted across the whole tree (root excluded)",
        "Entra ID: scope https://ai.azure.com/.default and the Cognitive Services OpenAI User role; or an api-key",
        "Every agent has the tools of the original request: apply the same controls to subagent calls",
    ], theme="blue", icon="openai", badge="preview", src=src("multi"))
    tr = Table(
        [("Transport", 130), ("Behavior", 520), ("Use for", 420)],
        [
            [ct("HTTP", "blue"), "Waits until active agents finish or pause for function output; you submit pending outputs in a continuation request", "Hosted-tool workflows or few developer function calls"],
            [ct("WebSocket", "blue"), "You inject each function output into the active response (response.inject) as soon as it is ready; each injection returns response.inject.created "
                                      "or response.inject.failed", "Tool-heavy or long-running workflows where coordination latency matters"],
        ], w=S(2) - C - G, theme="blue", size=14, head_size=15, title="HTTP or WebSocket", title_size=22)
    sec = card(C, "Security controls", [
        "Grant tools and calling identities only what the task needs",
        "Validate function arguments and authorize each action in application code",
        "Require user approval before write, destructive, financial or other high-impact actions",
        "Treat content from external tools as untrusted input and guard against prompt injection",
        "Log agent name, tool, arguments, approval decision and result",
        "Bound delegated work and monitor token usage",
    ], theme="pink", icon="content-safety", src=src("multi"))
    lim = card(C, "Limitations (as of 2026-11-03)", [
        "/responses/compact is not supported when multi-agent is on",
        "Automatic server-side compaction is on, run separately for the root and each subagent; override with context_management.compact_threshold",
        "reasoning.summary and max_tool_calls are not supported",
        "No fixed limit on tree depth or total subagents - bound concurrency and work yourself",
    ], theme="gray", icon="quotas", src=src("multi"))
    req.place(cv, 0, y1)
    tr.place(cv, X(1), y1)
    sec.place(cv, X(4), y1)
    lim.place(cv, X(5), y1)
    ts = Table(
        [("Symptom", 280), ("Resolution", 840)],
        [
            ["HTTP 401 or 403", "Entra: token scope https://ai.azure.com/.default and the Cognitive Services OpenAI User role; API key: it must belong to the endpoint's resource"],
            ["HTTP 404", "model must be the Azure OpenAI deployment name, available on that resource"],
            ["Unknown request parameter", "Upgrade the OpenAI SDK, use the beta Responses client, target the v1 endpoint with api-version=preview"],
            ["No subagents created", "State the workstreams in the prompt and check multi_agent.enabled; the model decides whether to delegate"],
            ["Unexpected function-call pauses", "Execute every developer function_call - including subagents' - and return a matching function_call_output per call ID"],
        ], w=S(2), theme="gray", size=14, head_size=15, title="Troubleshooting", title_size=22)
    ts.place(cv, X(1), tr.bottom + 28)
    return max(req.bottom, ts.bottom, sec.bottom, lim.bottom)


# ================================================================================================ band 4: routines
def band_routines(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Routines (Preview) - the trigger layer that lives with the agent",
             "A routine answers 'when should my agent run?' with exactly one trigger and one action. It reuses the normal agent invocation path, so no separate runtime is added.")
    top = y
    bw, bh = 330, 150
    gap = 90
    labels = [
        ("1  Trigger fires", "timer, recurring schedule, GitHub issue opened or closed, Teams channel message", "violet", "scheduler"),
        ("2  Run record created", "Foundry records the run in the project", "violet", "folder"),
        ("3  Agent endpoint invoked", "with the routine input (text or JSON) via the Responses or Invocations API", "green", "api-connections"),
        ("4  Agent runs", "its own model, instructions, tools and dispatch identity", "green", "agent"),
        ("5  Status stored", "run status linked to the agent response and trace details", "violet", "monitor"),
    ]
    boxes = []
    for i, (t_, s_, th, ic) in enumerate(labels):
        b = Box(bw, t_, sub=s_, theme=th, h=bh, size=19, sub_size=14, icon=ic, icon_pos="top", icon_size=32, fill="hatch")
        b.place(cv, i * (bw + gap), top)
        boxes.append(b)
    for i in range(4):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", sw=3)
    ry = top + bh + 26
    rh = Note(5 * bw + 4 * gap, "Run history shows each trigger run with its inputs, outputs, status and a link to the related agent response and trace. You can enable, disable, update, "
                                "dispatch manually (POST .../routines/{name}:dispatch_async?api-version=v1 is the only public manual route) or delete a routine without recreating the agent.",
              kind="info", title="Operate and observe", size=15, src=src("routines", "useroutines"))
    rh.place(cv, 0, ry)
    # routines vs workflows (right)
    t = Table(
        [("", 170), ("Routines", 300), ("Workflows (retiring)", 320)],
        [
            ["Question", "When should my agent run?", "How should steps or agents connect?"],
            ["Model", "Trigger to agent", "Graph of nodes, edges, branching, state"],
            ["Multi-agent", "No: one agent per routine", "Yes"],
            ["Best for", "Timers, schedules, lightweight automation", "Branching, approvals, multi-step processes"],
        ], w=S(1) + G + 410 - 20, theme="violet", size=14, head_size=15, first_col_theme="violet", title="Routines vs workflows (the routines page)", title_size=22)
    t.place(cv, 5 * bw + 4 * gap + 60, top)
    y1 = max(rh.bottom, t.bottom) + 36
    tg = Table(
        [("Trigger", 170), ("Key fields", 780)],
        [
            [ct("schedule", "violet"), "cron_expression (5 fields, minimum interval 5 minutes) and time_zone (IANA or Windows id) - both required"],
            [ct("timer", "violet"), "at: a future ISO 8601 time with an explicit UTC offset; one-shot, inactive after it fires"],
            [ct("github_issue", "violet"), "connection_id, owner, repository, issue_event (opened or closed)"],
            [ct("custom (teams)", "violet"), "provider teams, event_name on_new_channel_message, parameters: connection_id, thread_type channel, group_id, channel_id"],
        ], w=S(2) - 100, theme="violet", size=14, head_size=15, title="Trigger fields", title_size=22)
    tg.place(cv, 0, y1)
    dp = Table(
        [("Downstream result", 270), ("Run behavior", 560)],
        [
            ["2xx", "Run completed; downstream identifiers recorded"],
            ["408, 429, 5xx, timeout or transient failure", "Retryable while attempts remain"],
            ["Other 4xx", "Terminal: run failed"],
        ], w=S(2) - 100, theme="violet", size=14, head_size=15, title="Delivery policy", title_size=22)
    dp.place(cv, X(2) + 90, y1)
    cx = X(4)
    c1 = card(S(2), "Dispatch facts", [
        "Five total attempts, exponential backoff from 5 s capped at 60 s; 30 s timeout per downstream request",
        "Responses actions run in background mode: the timeout covers acceptance, not completion of the agent's work",
        "An acknowledged dispatch means 'enqueued', not 'finished'; success does not prove the agent's async work completed",
    ], theme="yellow", icon="quotas", src=src("useroutines"))
    c1.place(cv, cx, y1)
    y2 = max(tg.bottom, dp.bottom, c1.bottom) + 28
    id_ = card(C, "Identity", [
        "Default: the agent identity, for every trigger type",
        "Creator identity is a create-time opt-in (authorization.identity = creator) for tools that need delegated access; it is only the creating principal",
        "Fixed at creation: delete and recreate to switch",
        "! The agent endpoint must keep AzureRbac (Entra); AgentBlueprint is not supported for routine dispatch",
    ], theme="red", icon="managed-identity", src=src("routines"))
    gv = card(C, "Governance and connections", [
        "Routines are project-scoped, governed like agents, tools and connections (Foundry User or higher)",
        "GitHub and Teams triggers use project connections created through connector namespaces",
        "Do not put secrets, credentials or tokens in routine input or prompts",
    ], theme="grape", icon="policy", src=src("routines"))
    lm = card(C, "Limits (as of 2026-11-03)", [
        "One trigger and one action; prompt and hosted agents only, not workflow agents",
        "Works with VNet-secured projects; no customer-managed keys",
        "! Not in UK West, Switzerland West, Japan West, UAE North or Norway East",
        "SDKs: Python azure-ai-projects >= 2.4.0; stable C# 2.0.1 packages do not include routines",
    ], theme="gray", icon="regions", src=src("routines", "useroutines"))
    rm = card(C, "Agent-scheduled reminders", [
        "A hosted agent can schedule itself with the reminder_preview toolbox tool (not for prompt agents)",
        "The agent chooses a delay in minutes; Foundry re-invokes the same agent on the same conversation",
        "Different from routines: the agent decides, not an external trigger",
    ], theme="orange", icon="toolbox-icon", src=src("reminder"))
    nn = Note(S(2), "The routines page says to 'use a workflow instead' when you need branching, multiple agents or human approval. With workflows retiring on 2026-12-01, the "
                    "documented migration target is code-first orchestration (Microsoft Agent Framework) inside the invoked agent - see part 1.", kind="warn",
              title="Docs lag", size=15, src=src("routines", "workflow"))
    r_, b_ = row(cv, 0, y2, [id_, gv, lm, rm], gap=G)
    nn.place(cv, X(4), y2)
    return max(b_, nn.bottom)


# ================================================================================================ band 5: Canvas and tools
def band_canvas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Build and inspect - Microsoft Foundry Canvas (Preview), Foundry Toolkit and Agent Inspector",
             "Foundry Canvas is a GitHub Copilot App extension: a side-panel canvas for hosted agents. The canvas surfaces choices; Copilot writes the code in your workspace.")
    top = y
    stages = [
        ("1  Start", "Ask Copilot to create a Foundry hosted agent; the canvas opens in the right panel", "gray"),
        ("2  Choose a project", "Sign in to Azure, pick the subscription and Foundry project; it is remembered", "gray"),
        ("3  Scaffold", "Inspire me, Help me decide or Hello world sample prompt", "green"),
        ("4  Configure", "Wire a deployed model; add toolboxes, tools, skills and guardrails from your project", "orange"),
        ("5  Inspect Locally", "Runs azd under the hood and opens the embedded Agent Inspector; errors go back to Copilot as fix requests", "violet"),
        ("6  Deploy to Foundry", "Publishes the finished agent to Foundry Agent Service (azd)", "green"),
    ]
    bw = 330
    gp = (S(4) - 6 * bw) / 5
    sb = []
    for i, (t_, s_, th) in enumerate(stages):
        b = Box(bw, t_, sub=s_, theme=th, h=170, size=20, sub_size=14, fill="hatch")
        b.place(cv, i * (bw + gp), top + 34)
        sb.append(b)
    cv.text(0, top, "Canvas side panel (stages)", size=18, color=THEMES["green"].deep)
    for i in range(5):
        connect(cv, sb[i], sb[i + 1], a_side="right", b_side="left", sw=3, gap=3)
    cp = Box(S(4), "Copilot session in your workspace", sub="Every choice becomes a ready-to-run prompt with the project, subscription and endpoint attached; "
                                                          "Copilot scaffolds and edits the agent code and runs the commands - you keep control of the generated code",
             icon="copilot", icon_pos="left", theme="indigo", h=120, size=22, sub_size=15, fill="hatch")
    cp.place(cv, 0, top + 34 + 170 + 100)
    for b in sb[2:]:
        connect(cv, b, cp, a_side="bottom", b_side="top", tb=(b.cx - cp.x) / cp.w, sw=2.5, gap=4, color="#3b5bdb")
    cv.text(sb[2].x + 6, sb[2].bottom + 36, "ready-to-run prompts", size=14, color="#364fc7")
    badge_on(cv, cp, "preview")
    side = card(S(2), "Install and scope", [
        "In the GitHub Copilot App open Settings > Plugins, search microsoft-foundry and select Install",
        "Targets Foundry hosted agents; follow the full walkthrough in the hosted-agent quickstart (canvas pivot)",
        "Inspect Locally and Deploy to Foundry run the azd commands, so you can drop to the terminal at any time",
        "The page is titled Microsoft Foundry Canvas; its URL slug says foundry-agent-canvas",
    ], theme="gray", icon="github", src=src("canvas", "canvasqs"))
    side.place(cv, X(4), top)
    y1 = max(cp.bottom, side.bottom) + 40
    t = Table(
        [("Tool", 330), ("Status (as of 2026-11-03)", 360), ("Use it to", 1080), ("Not for", 540)],
        [
            [ct("Workflow designer (Foundry portal)", "red"), ("Preview, retiring 2026-12-01", "red"), "Maintain existing declarative workflows; export YAML before retirement",
             "New orchestration work"],
            [ct("Foundry Toolkit for VS Code", "indigo"), "No status banner on the pages read", "Open a read-only workflow graph, export and re-deploy existing workflow YAML, Generate Code (Python or C#) "
                                                                                                       "with GitHub Copilot, create hosted-agent workflows from samples, tracing",
             "Authoring declarative workflows (the graph is read-only)"],
            [ct("Agent Inspector", "violet"), "Part of the Toolkit and the Canvas", "Test a local Agent Framework workflow: workflow visualization and source navigation on supported dev servers",
             "Replacing the remote playground for a declarative workflow"],
            [ct("Microsoft Foundry Canvas", "gray"), ("Preview", "yellow"), "Guided, visual creation of hosted agents inside the GitHub Copilot App", "Prompt agents or workflows"],
            [ct("Azure Logic Apps", "gray"), "Not a Foundry feature", "Visual low-code orchestration that calls Foundry agents as steps", "Code-first agent orchestration"],
        ], w=S(4), theme="indigo", size=14, head_size=15, title="Which tool for which job", title_size=22)
    t.place(cv, 0, y1)
    nn = Note(S(2), "Docs name the Copilot harness differently: 'Microsoft Copilot harness' (microsoft_copilot_preview) in the docs and azd, 'GitHub Copilot managed harness' "
                    "(github_copilot_preview) in the REST schema. The Canvas page is a separate GitHub Copilot App extension.", kind="info", title="Do not confuse", size=15,
              src=src("canvas"))
    nn.place(cv, X(4), y1)
    return max(t.bottom, nn.bottom)


# ================================================================================================ band 6: gotchas
def band_gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Docs disagree, gaps and gotchas - as of 2026-11-03",
             "Where two sources give different answers both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 860), ("Another source says", 860), "How to read it"], [
        [ct("Incoming A2A on hosted agents", "orange"), "The enable-an-A2A-endpoint how-to describes prompt agents only and requires the responses protocol",
         "The hosted-agents concept page and the azure.yaml reference list a2a as a hosted-agent protocol", "Verify before you rely on a hosted agent serving A2A"],
        [ct("Which A2A version", "orange"), "The A2A tool page: use the GA a2a type (A2A 1.0) for new integrations",
         "The incoming endpoint serves v0.3 (preview) when no version is selected", "Pin v1.0 explicitly on both sides"],
        [ct("Multi-agent in workflows", "orange"), "The routines page and the A2A tool page point to workflows for multi-agent, branching and approvals",
         "The workflow page: retiring 2026-12-01, use Microsoft Agent Framework", "Treat the older pointers as lagging"],
        [ct("Preview vs GA across the set", "orange"), "The a2a tool is GA; routines, incoming A2A, Responses multi-agent and the Canvas are Preview",
         "A single customer scenario can mix them", "Check each hop's status; previews carry no SLA"],
    ], w=S(6), theme="orange", size=14, head_size=15, title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    ny = t.bottom + 30
    g1 = Note(S(2), "A2A on Foundry targets is text only and non-streaming. Task and context retention is 60 days from the last write. Azure Government has no A2A tool, and the "
                    "Connected Agents tool is not in the new Agent Service.", kind="gotcha", title="A2A limits", src=src("a2atool", "a2ain", "gov"))
    g1.place(cv, 0, ny)
    g2 = Note(S(2), "Responses multi-agent: GPT-5.6 only, Preview, no /responses/compact, no reasoning.summary or max_tool_calls. Routines: only GitHub issue and Teams channel "
                    "triggers, minimum 5 minutes, not in five regions, no CMK.", kind="warn", title="Preview limits", src=src("multi", "routines"))
    g2.place(cv, X(2), ny)
    g3 = Note(S(2), "Not documented in the pages read: a maximum number of A2A tools per agent, A2A latency or cost guidance, price rates for routines or multi-agent runs, "
                    "and per-pattern guidance for combining a routine with an orchestration. Nothing on this canvas fills those gaps.", kind="quote", title="What the docs do not say")
    g3.place(cv, X(4), ny)
    return max(g1.bottom, g2.bottom, g3.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "A2A, Responses multi-agent and routines in depth",
        "Part 2 of 'Workflows, routines, A2A and multi-agent orchestration'  |  A2A tool and endpoint, A2A authentication, Responses API subagents (Preview), routines (Preview), Foundry Canvas  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Tools and A2A", "pink"), ("Identity and security", "red"),
                           ("Observability and triggers", "violet"), ("Cost and capacity", "yellow"), ("State and data", "cyan"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    draw_badge(cv, bx + 420, y - 1, "ga")
    cv.text(bx + 470, y, "generally available", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Workflows, routines, A2A and multi-agent orchestration", "Prompt agents: harness, A2A, routines and migration", "Hosted agents: your code on Foundry's runtime",
                "Foundry Toolbox", "MCP and tool authentication", "Agent identity and delegation"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_a2a(cv, y) + 56
    y = band_auth(cv, y) + 56
    y = band_responses(cv, y) + 56
    y = band_routines(cv, y) + 56
    y = band_canvas(cv, y) + 56
    y = band_gotchas(cv, y) + 56
    sources(cv, 0, y, [
        ("Connect to an A2A agent endpoint", U["a2atool"][1]), ("Agent2Agent (A2A) authentication", U["a2aauth"][1]),
        ("Enable an incoming A2A endpoint", U["a2ain"][1]), ("Configure user delegation for tools", U["userdeleg"][1]),
        ("Register a custom agent in Foundry Control Plane", U["register"][1]), ("What is a toolbox?", U["toolbox"][1]),
        ("Multi-agent orchestration with the Responses API", U["multi"][1]), ("Routines in Foundry Agent Service", U["routines"][1]),
        ("Automate agents with routines", U["useroutines"][1]), ("Create or update a routine (REST)", U["routrest"][1]),
        ("Reminder tool for self-scheduling agents", U["reminder"][1]), ("Microsoft Foundry Canvas", U["canvas"][1]),
        ("Quickstart: deploy your first hosted agent", U["canvasqs"][1]), ("Build a workflow in Microsoft Foundry (retiring)", U["workflow"][1]),
        ("Use and migrate declarative workflows (VS Code)", U["lowcode"][1]), ("Agent Service in Azure Government", U["gov"][1]),
    ], w=W, cols=4)
