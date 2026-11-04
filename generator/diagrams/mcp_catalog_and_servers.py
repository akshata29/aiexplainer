"""MCP in Foundry, part 1 - one MCP tool, five kinds of MCP server.

Hub: a Foundry agent's MCP tool (server_url, server_label, allowed_tools, require_approval, project_connection_id, headers)
talks to four kinds of remote server (public Tools Catalog, managed servers on connector namespaces, private API Center catalog,
servers you build); the fifth kind, the Foundry MCP Server, serves coding agents. Then: the MCP tool's fields, the approval flow,
long-running calls and limits; the public Tools Catalog; managed MCP servers (connector namespaces, preview). Part 2 covers
build-your-own, the Foundry MCP Server, governance and transport.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="mcp-catalog-and-servers", title="MCP in Foundry: catalogs and servers", section="2", group="Tools and MCP", order=32,
    description="MCP in Foundry, part 1: one MCP tool and five kinds of MCP server (public Tools Catalog, managed servers on connector namespaces, private API Center catalog, servers you build, the Foundry MCP Server for coding agents), the tool's fields, approval flow and limits, the public catalog and managed MCP servers (preview).",
    tags=["mcp", "tools-catalog", "connector-namespace", "approvals", "allowed-tools", "managed-mcp"],
)

W = 3080
COL, GUT = 480, 40
SEC = 72
LR = metrics.line_ratio()


def SPAN(n: int) -> float:
    return n * COL + (n - 1) * GUT


L = dict(
    tool=("Connect agents to MCP servers (MCP tool)", learn("agents/how-to/tools/model-context-protocol")),
    conn=("Managed MCP servers from connectors (preview)", learn("agents/how-to/tools/connectors")),
    auth=("MCP authentication", learn("agents/how-to/mcp-authentication")),
    build=("Build your own MCP server", learn("mcp/build-your-own-mcp-server")),
    start=("Get started with the Foundry MCP Server", learn("mcp/get-started")),
    avail=("Foundry MCP Server available tools", learn("mcp/available-tools")),
    sec=("Foundry MCP Server security best practices", learn("mcp/security-best-practices")),
    priv=("Private tool catalog (API Center)", learn("agents/how-to/private-tool-catalog")),
    gov=("Governance for MCP tools (preview)", learn("agents/how-to/tools/governance")),
    gw=("AI gateway", learn("agents/how-to/ai-gateway")),
    plink=("Configure private link (agent tools)", learn("how-to/configure-private-link")),
    ref=("Power Platform: all MCP server connectors", learn("connectors/connector-reference/connector-reference-mcpserver-connectors", base="")),
)


def src(*keys: str) -> list:
    return [L[k] for k in keys]


# ---------------------------------------------------------------------------------------------- helpers
def sec(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


def learn_line(cv, x, y, items, gap=34, size=12):
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * LR


class Stat(Rect2):
    """Big number + caption tile."""

    def __init__(self, w, big, label, *, theme="orange", big_size=46, size=15, pad=14, badge=None):
        self.th = get_theme(theme)
        self.w, self.big, self.big_size, self.size, self.pad, self.badge = w, big, big_size, size, pad, badge
        self.lines = metrics.wrap_text(label, (w - 2 * pad) * 0.965, size)
        self.h = pad + big_size * LR + 4 + len(self.lines) * size * LR + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
            cv.text(x + pad, y + pad, self.big, size=self.big_size, color=th.deep)
            cv.text(x + pad, y + pad + self.big_size * LR + 4, "\n".join(self.lines), size=self.size, color=INK)
            if self.badge:
                _, label = STATUS.get(self.badge, ("gray", self.badge))
                bw = metrics.line_width(label, 13) + 18
                draw_badge(cv, x + self.w - pad - bw, y + pad - 1, self.badge)
        cv.register(f"stat:{self.big}", x, y, self.w, H)
        return self


class CodeCard(Rect2):
    """Monospace snippet in a soft card (only documented text; indentation is preserved)."""

    def __init__(self, w, title, lines, *, theme="gray", size=14, pad=14, src=(), note=None):
        self.th = get_theme(theme)
        self.w, self.title, self.size, self.pad, self.src = w, title, size, pad, list(src)
        inner = (w - 2 * pad) * 0.965
        self.lines = []
        for ln in lines:
            if metrics.line_width(ln, size, metrics.MONO) <= inner:
                self.lines.append(ln)
            else:
                indent = ln[:len(ln) - len(ln.lstrip(" "))]
                parts = metrics.wrap_text(ln.strip(), inner - metrics.line_width(indent + "  ", size, metrics.MONO), size, metrics.MONO)
                self.lines.extend([indent + parts[0]] + ["  " + indent + p for p in parts[1:]])
        self.note_lines = metrics.wrap_text(note, inner, 14) if note else []
        lh = size * metrics.line_ratio(metrics.MONO)
        h = pad + 20 * LR + 8 + len(self.lines) * lh + 6
        if self.note_lines:
            h += 8 + len(self.note_lines) * 14 * LR
        self.src_lines = []
        if self.src:
            h += 8
            for label, url in self.src:
                self.src_lines.append((f"Learn: {label}", url, h))
                h += 12 * LR + 2
            h -= 2
        self.h = h + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        lh = self.size * metrics.line_ratio(metrics.MONO)
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
            cv.text(x + pad, y + pad, self.title, size=20, color=th.deep)
            ty = y + pad + 20 * LR + 8
            cv.text(x + pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            ty += len(self.lines) * lh + 14
            if self.note_lines:
                cv.text(x + pad, ty, "\n".join(self.note_lines), size=14, color=MUTED)
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"code:{self.title}", x, y, self.w, H)
        return self


def step_list(cv, x, y, w, steps, *, theme="orange", size=15):
    """Numbered vertical step list; returns the bottom y."""
    for i, s in enumerate(steps, 1):
        lines = metrics.wrap_text(s, (w - 46) * 0.965, size)
        h = max(len(lines) * size * LR, 28)
        numbered(cv, x + 15, y + 14, i, theme=theme, d=28, size=15)
        cv.text(x + 40, y + (h - len(lines) * size * LR) / 2, "\n".join(lines), size=size, color=INK)
        y += h + 10
    return y - 10


def badge_on(cv, blk, kind, inset=14, up=13):
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


# ---------------------------------------------------------------------------------------------- 0. title + strip
def top_block(cv):
    _, b = title_block(cv, 0, 0, "MCP in Foundry: catalogs and servers",
                       "One MCP tool on the agent, five kinds of MCP server behind it, and the controls around them - part 1 of 2 (as of 2026-11-03)",
                       icon="mcp", w=W)
    y = b + 26
    legend(cv, 0, y, [("MCP servers and tools", "orange"), ("Agents and Agent Service", "green"), ("Auth and identity", "red"),
                      ("Governance and gateway", "grape"), ("Networking", "indigo"), ("Foundry MCP Server and coding agents", "gray")])
    cv.text(2400, y, "Dashed border = preview. Part 2 builds, connects and governs.", size=15, color=MUTED)
    y += 52
    stats = [
        Stat(COL, ">1,000", "connectors in the Foundry Tools Catalog that can surface as managed MCP servers", theme="orange"),
        Stat(COL, "10", "MCP servers with a Foundry-managed OAuth app", theme="red"),
        Stat(COL, "14", "regions for managed MCP servers (preview)", theme="orange", badge="preview"),
        Stat(COL, "79", "tools in 17 categories on the Foundry MCP Server (preview)", theme="gray", badge="preview"),
        Stat(COL, "100 s", "timeout for a non-streaming MCP tool call", theme="yellow"),
        Stat(COL, "128", "tools per agent (agent-level limit)", theme="green"),
    ]
    _, b2 = row(cv, 0, y, stats, gap=GUT)
    return b2


# ---------------------------------------------------------------------------------------------- 1. hub
def hub(cv, y):
    y = sec(cv, y, "1  One MCP tool, five kinds of MCP server",
            sub="The agent runtime accepts only a remote MCP endpoint. Four kinds of server plug into the same tool config; the fifth serves coding agents, not Agent Service agents.") + 40
    servers = [
        Card(1560, "Public Tools Catalog", [
            "Portal: Build > Tools > Catalog (or + Add tool). Catalog MCP servers include Azure DevOps (hosted by Azure DevOps, streamable HTTP), GitHub, Azure Speech and Azure Language",
            "Also listed: Work IQ and Fabric IQ (OneLake Catalog) options; the Foundry Tools Catalog adds more than 1,000 connectors",
            "Auth is chosen when you create the server: a project connection holds the endpoint and credentials",
        ], theme="orange", icon="mcp", src=src("tool", "conn")),
        Card(1560, "Managed MCP servers on connector namespaces", [
            "Add a connector and Foundry provisions an MCP server in your account's Connector Namespace; each project maps to an environment inside it",
            "Actions only (no triggers); OAuth2 connectors; 14 regions; role: Foundry Project Manager",
        ], theme="orange", icon="logic-apps", dash="dashed", badge="preview", src=src("conn")),
        Card(1560, "Private tools catalog (Azure API Center)", [
            "Admins register MCP servers as API Center assets; Foundry lists them under Build > Tools as a registry filter named after the API Center",
            "Developers need Azure API Center Data Reader; access can take up to 24 hours to propagate",
        ], theme="orange", icon="apim", dash="dashed", badge="preview", src=src("priv")),
        Card(1560, "Build your own remote MCP server", [
            "Host it as a remote endpoint: Azure Functions (https://{app}.azurewebsites.net/runtime/webhooks/mcp) or Azure Container Apps. A local server must be self-hosted to get a remote endpoint",
            "Connect with Build > Tools > Connect a tool > Custom > MCP; auth by key, Microsoft Entra (project managed identity) or custom OAuth",
            "A custom code interpreter also exposes an MCP server (ACA dynamic sessions pool, mcpServerEndpoint)",
        ], theme="orange", icon="functions", src=src("build")),
    ]
    gap = 22
    sx = W - 1560
    H4 = sum(c.h for c in servers) + gap * 3
    cfg = Card(660, "MCP tool in the agent definition", [
        "server_url: the remote MCP endpoint",
        "server_label: unique per agent",
        "allowed_tools: empty list = all tools, otherwise an allow-list",
        "require_approval: always (default), never, or per-tool lists",
        "project_connection_id: endpoint and credentials; a connection's endpoint overrides server_url",
        "headers: custom headers, {{placeholder}} values from structured inputs",
    ], theme="orange", icon="mcp", src=src("tool"))
    tb = Box(660, "Toolbox (optional)", sub="One MCP endpoint that bundles many tools; attach it as a normal mcp tool (server_url + server_label)", theme="orange", dash="dashed",
             h=112, size=19, sub_size=14, icon="toolbox", icon_pos="left")
    gw = Box(660, "AI gateway (optional, preview)", sub="New MCP tools created in the portal without managed OAuth are routed through Azure API Management: rate limits, IP restrictions, audit logging",
             theme="grape", dash="dashed", h=128, size=19, sub_size=14, icon="apim", icon_pos="left")
    appr = Note(660, "With require_approval = always the model's tool call comes back as an mcp_approval_request (tool + arguments). Answer with an mcp_approval_response in the same conversation.",
                kind="key", title="Approvals", size=15, src=src("tool"))
    PW = 700
    content = 76 + cfg.h + 22 + tb.h + 22 + gw.h + 22 + appr.h + 24
    H = max(H4, content)
    extra = (H - H4) / 4
    px = 600
    with cv.panel(px, y, w=PW, h=H, title="MCP tool config and optional layers", theme="orange", style="dotted", pad=20, title_size=21) as P:
        pass
    cfg.place(cv, px + 20, y + 62)
    tb.place(cv, px + 20, cfg.bottom + 22)
    gw.place(cv, px + 20, tb.bottom + 22)
    appr.place(cv, px + 20, gw.bottom + 22)
    cy = y
    placed = []
    for c in servers:
        c.place(cv, sx, cy, h=c.h + extra)
        placed.append(c)
        cy += c.h + gap
    agent = Card(500, "Agent Service agent", [
        "A prompt or hosted agent whose Foundry model calls MCP tools",
        "The runtime accepts a remote MCP server endpoint only",
        "Foundry User role to create and test; Foundry Project Manager to create a project connection",
    ], theme="green", icon="agent", src=src("tool"))
    agent.place(cv, 0, y + 70)
    net = Card(500, "Public or private endpoint?", [
        "Public: any publicly reachable remote server, Basic or Standard setup",
        "Private: Standard Agent Setup with private networking (BYO VNet); Basic setup is unsupported",
        "Tested private host: Azure Container Apps with internal-only ingress on a dedicated MCP subnet delegated to Microsoft.App/environments; Functions and App Service might work but are not internally validated",
    ], theme="indigo", icon="vnet", src=src("tool", "plink"))
    net.place(cv, 0, agent.bottom + 28)
    connect(cv, agent, P, a_side="right", b_side="left", ta=0.5, tb=(agent.cy - y) / H, start_head="arrow", end_head="arrow", sw=2.5,
            label="tool calls", label_size=14)
    for c in placed:
        connect(cv, P, c, a_side="right", b_side="left", ta=(c.cy - y) / H, tb=0.5, start_head="arrow", end_head="arrow", sw=2.5)
    # fifth kind: the Foundry MCP Server, for coding agents
    y5 = y + H + 90
    with cv.panel(0, y5 - 60, w=W, h=240, title="Not an Agent Service tool: coding agents", theme="gray", style="dotted", pad=20, title_size=21):
        pass
    coder = Box(500, "Coding agent", sub="VS Code with GitHub Copilot in agent mode: developer tooling", theme="gray", h=120, size=20, sub_size=14, icon="vscode", icon_pos="left").place(cv, 20, y5 + 10)
    fm = Card(1560, "Foundry MCP Server", [
        "A cloud-hosted MCP server at https://mcp.ai.azure.com: 79 tools in 17 categories that read and write Foundry resources, with nothing to deploy",
        "Entra token scoped to https://mcp.ai.azure.com; the server calls on behalf of the signed-in user (On-Behalf-Of)",
        "Public endpoint only: no network isolation and no SLA",
    ], theme="gray", icon="foundry", badge="preview", src=src("start", "avail")).place(cv, sx, y5 - 20)
    connect(cv, coder, fm, a_side="right", b_side="left", ta=0.5, tb=(coder.cy - fm.y) / fm.h, start_head="arrow", end_head="arrow", sw=2.5,
            label="Entra token for https://mcp.ai.azure.com", label_size=15)
    return max(fm.bottom, coder.bottom, P.bottom) + 40


# ---------------------------------------------------------------------------------------------- 2. the MCP tool
def tool_section(cv, y):
    y = sec(cv, y, "2  The MCP tool: fields, approvals and long-running calls",
            sub="What you configure on the agent, what happens when a call needs approval, and where the limits bite.") + 36
    t = Table([("Field", 200), ("What it does", 620), "Default or gotcha"], [
        ["server_url", "The remote MCP server endpoint, for example https://api.githubcopilot.com/mcp/", "The Agent Service runtime only accepts a remote MCP server endpoint"],
        ["server_label", "Name of the server, unique per agent", "Keep it unique even when you switch toolbox versions; toolbox tool names read {server_label}.{tool}"],
        ["allowed_tools", "Allow-list of the tool names the agent may call", "An empty list allows ALL tools; names are case-sensitive"],
        ["require_approval", "Which calls need a human approval: always, never, {\"never\": [tools]} or {\"always\": [tools]}", "Default is always"],
        ["project_connection_id", "The project connection that holds the endpoint and credentials", "If the connection's endpoint differs from server_url, the connection's endpoint is used"],
        ["headers", "Custom request headers", "Can use {{placeholder}} values from structured inputs"],
    ], w=SPAN(3), theme="orange", size=15, head_size=16, first_col_theme="orange", title="MCP tool fields", title_size=21)
    tx = SPAN(3) + GUT
    t.place(cv, tx, y)
    ly = learn_line(cv, tx, t.bottom + 8, src("tool"))
    n = Note(SPAN(3), "Third parties, not Microsoft, create remote MCP servers, and Microsoft does not test or verify them. Prefer servers hosted by trusted providers over proxies, "
                      "treat tool descriptions, annotations and results as untrusted (indirect prompt injection), require approval for writes, log tool calls and re-review when a server or its tools change.",
             kind="warn", title="Third-party servers: caution", size=15, src=src("tool"))
    n.place(cv, tx, ly + 28)
    seq = Sequence(cv, 0, y, [("Your app", "gray", "app"), ("Agent Service", "green", "agent"), ("MCP server", "orange", "mcp")], spacing=650, head_w=220)
    seq.msg(0, 1, "user message to the agent", num=1)
    seq.msg(1, 1, "the model picks an MCP tool; require_approval = always")
    seq.msg(1, 0, "output item mcp_approval_request: tool + arguments", num=2, dash="dashed")
    seq.msg(0, 1, "mcp_approval_response: approve = true + request ID, same conversation", num=3)
    seq.msg(1, 2, "call the tool", num=4)
    seq.msg(2, 1, "tool result", num=5, dash="dashed")
    seq.msg(1, 0, "final answer", num=6, dash="dashed")
    sb = seq.end()
    cy = max(n.bottom, sb) + 44
    c1 = Card(SPAN(2), "Approval flow details", [
        "Submit the approval in the same conversation; Copilot-harness agents must pass a conversation, and previous_response_id is unsupported",
        "Learn's first-success route: connect with require_approval = always, approve one call, verify, then clean up",
        "Agent never continues after approval? Send a follow-up in the same conversation using the approval request item ID as approval_request_id",
    ], theme="green", icon="agent", src=src("tool"))
    c2 = Card(SPAN(2), "Long-running operations", [
        "Run the response in background mode (models such as gpt-5.4 and gpt-5.5)",
        "The MCP server must implement the MCP tasks capability, return io.modelcontextprotocol/related-task metadata with a taskId and be pollable",
        "The response comes back queued; poll until completed",
        "! Without tasks, non-streaming MCP tool calls time out at 100 s",
    ], theme="orange", icon="metrics", badge="preview", src=src("tool"))
    c3 = Card(SPAN(2), "Known limits and errors", [
        "Remote endpoints only: host a local server in Azure Container Apps or Azure Functions to get one",
        "! Invalid tool schema when the server uses anyOf, allOf or multi-type parameters",
        "Private MCP needs Standard Agent Setup with private networking (BYO VNet); Basic setup is unsupported",
        "SDKs: Python, C#, JavaScript, Java and REST; Basic and Standard agent setup",
    ], theme="red", icon="preview-features", src=src("tool", "plink"))
    _, b = row(cv, 0, cy, [c1, c2, c3], gap=GUT)
    return b + 10


# ---------------------------------------------------------------------------------------------- 3. public catalog
def catalog(cv, y):
    y = sec(cv, y, "3  The public Tools Catalog",
            sub="Portal: project > Build > Tools > Catalog (labels vary: Tools, + Add tool, Browse all tools - the same catalog). Private catalogs appear as registry filters named after the API Center.") + 36
    LW = SPAN(4)
    with cv.panel(0, y, title="What is on the shelves (documented examples, not an exhaustive list)", theme="orange", style="dotted", pad=22, title_size=22, w=LW) as shelf:
        cx, cy = shelf.ix, shelf.iy
        inner = LW - 44

        def shelf_row(title, items, theme, size=15, sub=None):
            nonlocal cy
            t = cv.text(cx, cy, title, size=18, color=get_theme(theme).deep)
            cy = t.bottom + 6
            if sub:
                s = cv.text(cx, cy, sub, size=14, color=MUTED)
                cy = s.bottom + 4
            f = ChipFlow(items, inner, theme=theme, size=size)
            f.place(cv, cx, cy)
            cy += f.h + 22

        shelf_row("Catalog MCP servers", ["Azure DevOps MCP Server (hosted by Azure DevOps, streamable HTTP)", "GitHub", "Azure Speech MCP Server", "Azure Language MCP",
                                           "Work IQ options", "Fabric IQ (OneLake Catalog) options"], "orange")
        shelf_row("10 servers with a Foundry-managed OAuth app", ["Azure Databricks Genie", "GitHub", "Infobip WhatsApp", "Infobip RCS", "Infobip SMS",
                                                                  "LSEG Data and Analytics", "Morningstar", "Neon", "Pipedream", "Vercel"], "red",
                  sub="Other OAuth-enabled MCP servers need your own app registration; connector names and auth details are in the MCP and tool authentication canvas.")
        shelf_row("Foundry Tools Catalog: more than 1,000 connectors", ["Pre-built integrations to SaaS, data and line-of-business systems",
                                                                         "Add one and Foundry can publish it as a managed MCP server (section 4, preview)"], "blue")
        shelf_row("Power Platform connector reference, 'List of all MCP servers' (81 entries when read) - examples",
                  ["Azure DevOps MCP", "Box MCP Server", "Docusign MCP", "Dun and Bradstreet MCP Server", "Dynamics 365 MCP", "Dynamics 365 Sales", "Dynamics 365 ERP",
                   "Dynamics 365 Business Central", "GitHub", "Gong", "LSEG", "Microsoft Dataverse", "Microsoft Learn Docs MCP", "Microsoft Sentinel MCP", "monday.com",
                   "Morningstar", "Smartsheet", "Tavily MCP", "Work IQ MCP", "Work IQ OneDrive", "Work IQ SharePoint", "Zapier MCP", "ZoomInfo GTM MCP", "Azure - Foundry IQ"],
                  "gray", size=14)
    ly = learn_line(cv, 0, shelf.bottom + 8, src("conn", "ref"))
    n = Note(LW, "The Skills catalog in the VS Code Foundry Toolkit (Developer Tools > Agent Dev Tools > Tool Catalog) is separate from MCP: prebuilt skills grouped as Office documents (docx, pptx, xlsx, pdf), "
                 "Design and creative (canvas-design, algorithmic-art, brand-guidelines, theme-factory) and Writing and comms (doc-coauthoring, internal-comms, slack-gif-creator).",
             kind="info", title="Skills are not MCP servers", size=15)
    n.place(cv, 0, ly + 24)
    rx = LW + GUT
    rw = W - rx
    with cv.panel(rx, y, title="Add a catalog MCP server in the portal", theme="orange", style="solid", fill="soft", pad=22, title_size=22, w=rw) as st:
        step_list(cv, st.ix, st.iy, rw - 44, [
            "Open Build > Tools > Catalog and search or filter",
            "Pick the server",
            "Create or configure it and choose the auth type; this creates a project connection",
            "Optionally choose a subset of its tools: that becomes allowed_tools",
            "The portal checks gateway routing: with an AI gateway connected and no managed OAuth, the URL becomes the API Management URL",
            "Attach it to the agent or to a toolbox",
            "Run it; approve any mcp_approval_request in the same conversation",
        ])
    ado = Card(rw, "Azure DevOps through the catalog", [
        "Add Tools > Catalog > Azure DevOps > Create > enter your organization name > Connect > choose a subset of tools",
        "The organization must be backed by a Microsoft Entra tenant; standalone Microsoft-account organizations are unsupported",
        "Supports client user delegation: target pattern https://mcp.dev.azure.com/{orgName} with the delegated scope Ado.Mcp.Tools",
    ], theme="orange", icon="devops", src=src("tool", "auth"))
    ado.place(cv, rx, st.bottom + 28)
    return max(n.bottom, ado.bottom) + 10


# ---------------------------------------------------------------------------------------------- 4. managed MCP servers
def managed(cv, y):
    y = sec(cv, y, "4  Managed MCP servers on connector namespaces (preview)",
            sub="Add a connector and Foundry hosts a project-scoped MCP server for you: hosting, tool definitions, authentication, credentials and lifecycle are managed.") + 40
    top = y
    AX, AW = 470, 1700
    with cv.panel(AX, top, w=AW, h=540, title="Your Foundry account", theme="blue", style="dotted", pad=20, title_size=22):
        pass
    with cv.panel(AX + 24, top + 66, w=AW - 48, h=450, title="Connector Namespace (one per account, fully managed)", sub="hosts connector runtimes and MCP servers; the namespace acts as a proxy to the service",
                  theme="orange", style="dashed", fill="soft", pad=20, title_size=21, sub_size=15) as ns:
        pass
    ew = (AW - 48 - 40 - 24) / 2
    envs = []
    for i, name in enumerate(("Project A environment", "Project B environment")):
        ex = AX + 24 + 20 + i * (ew + 24)
        with cv.panel(ex, top + 176, w=ew, h=284, title=name, sub="one environment per project; servers are scoped to the project", theme="orange", style="solid", pad=18, title_size=20, sub_size=14) as ep:
            pass
        envs.append(ep)
    bw = (ew - 36 - 20) / 2
    labels = [("Managed MCP server", "GitHub"), ("Managed MCP server", "SharePoint"), ("Managed MCP server", "Docusign"), ("more connectors", "actions only, no triggers")]
    for i, (t, s) in enumerate(labels):
        ep = envs[i // 2]
        Box(bw, t, sub=s, theme="orange", fill="hatch", h=110, size=18, sub_size=15, dash="dashed" if i == 3 else "solid",
            icon="mcp" if i < 3 else None, icon_pos="top").place(cv, ep.x + 18 + (i % 2) * (bw + 20), ep.y + 108)
    agent = Box(380, "Agent or toolbox", sub="in the same Foundry project; add the managed server URL", theme="green", h=150, size=20, sub_size=15, icon="agent", icon_pos="top").place(cv, 0, top + 195)
    saas = Box(780, "The SaaS or business system", sub="GitHub, SharePoint, Docusign, Box ...; reached with OAuth2 per-user consent", theme="gray", h=150, size=20, sub_size=15, icon="globe", icon_pos="top").place(cv, W - 780, top + 195)
    connect(cv, agent, ns, a_side="right", b_side="left", ta=0.5, tb=(agent.cy - ns.y) / ns.h, sw=2.5, start_head="arrow", end_head="arrow", label="MCP tool calls", label_size=14)
    connect(cv, ns, saas, a_side="right", b_side="left", ta=(saas.cy - ns.y) / ns.h, tb=0.5, sw=2.5, start_head="arrow", end_head="arrow", label="OAuth2", label_size=14)
    y2 = top + 540 + 50
    flow_boxes = [
        Box(480, "1  Browse", sub="the connector catalog; only validated connectors get the managed-MCP portal experience", theme="orange", h=140, size=19, sub_size=14),
        Box(480, "2  Connect", sub="authenticate with OAuth2 (consent per user)", theme="orange", h=140, size=19, sub_size=14),
        Box(480, "3  Select actions", sub="pick only the actions you need; change them later from the Tools view", theme="orange", h=140, size=19, sub_size=14),
        Box(480, "4  Add tool", sub="Foundry publishes the MCP server in the project's environment; the agent calls its tools", theme="orange", h=140, size=19, sub_size=14),
    ]
    cx = 0
    prev = None
    for b in flow_boxes:
        b.place(cv, cx, y2)
        if prev:
            connect(cv, prev, b, a_side="right", b_side="left", sw=2.5)
        prev = b
        cx += b.w + GUT
    tiers = Table([("Publisher tier", 220), ("Examples", 290), "Where your data goes"], [
        [("Microsoft, internal services", "blue"), "SharePoint, Teams, Dynamics 365", "Stays on Microsoft infrastructure"],
        [("Microsoft, external services", "blue"), "GitHub", "Transits Microsoft infrastructure; the destination's policies apply"],
        [("Verified third party", "gray"), "Docusign, Databricks, Box", "Same as external services"],
        [("Independent publisher", "gray"), "Community connectors", "Lower certification bar: review the terms"],
    ], w=SPAN(2), theme="orange", size=15, head_size=16, title="Publisher tiers and data responsibility", title_size=20)
    tiers.place(cv, SPAN(4) + GUT, y2 - 30)
    y3 = max(flow_boxes[0].bottom, tiers.bottom) + 44
    facts = Card(SPAN(2), "What to know", [
        "Each Foundry account has one Connector Namespace; each project maps to an environment inside it",
        "Servers are scoped to the project; connector triggers are not supported, only actions",
        "Code-first (REST, SDK, azd) has no gating: any catalog connector works. The portal experience covers validated connectors only",
        "Only OAuth2 connectors today; for others use Logic Apps 'Add connector actions as agent tools'",
        "Role: Foundry Project Manager",
    ], theme="orange", icon="logic-apps", badge="preview", src=src("conn"))
    regions = ["australiaeast", "brazilsouth", "canadacentral", "eastus2", "francecentral", "germanywestcentral", "japaneast", "norwayeast",
               "southafricanorth", "southcentralus", "spaincentral", "swedencentral", "switzerlandnorth", "westus3"]
    facts.place(cv, 0, y3)
    with cv.panel(SPAN(2) + GUT, y3, title="14 regions", sub="managed MCP servers (preview); the connector catalog itself is always served from eastus", theme="indigo", style="dotted", pad=20, title_size=22, w=SPAN(2)) as rg:
        ChipFlow(regions, SPAN(2) - 40, theme="indigo", size=15).place(cv, rg.ix, rg.iy)
    code = CodeCard(SPAN(2), "azd: create the connection", [
        "azd ai connection create <name>",
        "  --kind remote-tool",
        "  --connector-name <catalog connector name>",
        "  --metadata mcpserverConfigProperties=<json>",
    ], theme="orange", note="The CLI cannot complete the browser OAuth consent. The microsoft.foundry azd extension is preview. The connectors page cites azd 1.36.0 or later, while other tool pages name 1.25 and 1.27.1 - docs disagree.",
        src=src("conn"))
    code.place(cv, 2 * (SPAN(2) + GUT), y3)
    y4 = max(facts.bottom, rg.bottom, code.bottom) + 44
    with cv.panel(0, y4, w=W, title="Code-first: the REST flow in seven steps", theme="orange", style="solid", fill="soft", pad=22, title_size=22) as rest:
        step_list(cv, rest.ix, rest.iy, W - 44, [
            "Get two tokens: a catalog token (resource https://ai.azure.com) and an ARM token.",
            "Discover the connector with POST https://eastus.api.azureml.ms/asset-gallery/v1.0/tools - the catalog is always served from eastus. Filters: entityContainerId=connectors-registry-prod-bl, type=tools, kind=Versioned, labels=latest; page with skip and pageSize 100. A connector is OAuth2 when x-ms-connection-parameters has type oauthSetting.",
            "Create the project connection with an ARM PUT on .../accounts/{acct}/projects/{proj}/connections/{name} (api-version 2025-04-01-preview): authType OAuth2, category RemoteTool, connectorName, target https://placeholder, metadata.type gateway_connector, toolEntityId, connectionproperties. Status: Unauthenticated.",
            "Get the per-user consent link with listConsentLinks: it is short-lived (about 1 hour) and redirects to https://ai.azure.com/nextgen/authConsentPopup.",
            "List the connector's operations (Microsoft.Web/locations/eastus/managedApis/{connector}/apiOperations, api-version 2016-06-01); skip webhook and notification triggers.",
            "Send a second PUT that adds metadata.mcpserverConfigProperties (state and connectors[].operations[] with userParameters and agentParameters schemas). The target is rewritten to https://app-XX.<region>.logic.azure.com/api/connectorGateways/<envId>/mcpServerConfigs/<connectionName>/mcp and the status becomes Connected after consent and registration. A PUT replaces the whole operations list.",
            "Add the managed server URL to a toolbox or to an agent.",
        ])
    learn_line(cv, 0, rest.bottom + 8, src("conn"))
    return rest.bottom + 30


# ---------------------------------------------------------------------------------------------- 5. gotchas
def gotchas(cv, y):
    y = sec(cv, y, "5  Gotchas to remember", sub="Status labels follow each feature's own Learn page: managed MCP servers, the private catalog, AI-gateway governance and the Foundry MCP Server are preview as of 2026-11-03.") + 36
    n = lambda kind, title, text, *keys: Note(COL, text, kind=kind, title=title, size=15, src=src(*keys))
    items = [
        n("gotcha", "allowed_tools: [] means ALL tools", "An empty allow-list does not block everything - it allows every tool the server offers. Tool names are case-sensitive.", "tool"),
        n("warn", "Approval defaults to always", "require_approval defaults to always on the MCP tool. A toolbox endpoint does not block tool calls itself: the agent runtime has to enforce approval.", "tool"),
        n("warn", "Microsoft tokens are not forwarded", "With managed OAuth, a token for a known Microsoft audience is never sent to a custom or third-party server: 'Cannot pass Microsoft token to untrusted MCP endpoint.'", "auth"),
        n("info", "Catalog in eastus, servers in 14 regions", "The managed-MCP connector catalog is always served from eastus; the managed servers themselves run in 14 regions.", "conn"),
        n("warn", "100 seconds without tasks", "Non-streaming MCP tool calls time out at 100 s unless the server implements the MCP tasks capability and you use background mode (preview).", "tool"),
        n("info", "Labels moved", "The portal calls the same catalog Build > Tools, Tools > Catalog, + Add tool or Add Tools > Catalog. Treat them as one place.", "tool"),
    ]
    _, b = row(cv, 0, y, items, gap=GUT)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    y = top_block(cv)
    y = hub(cv, y + SEC)
    y = tool_section(cv, y + SEC)
    y = catalog(cv, y + SEC)
    y = managed(cv, y + SEC)
    y = gotchas(cv, y + SEC)
    sources(cv, 0, y + SEC, [L["tool"], L["conn"], L["auth"], L["ref"], L["priv"], L["build"], L["start"], L["avail"], L["gov"], L["plink"]], w=W, cols=3)
