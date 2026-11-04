"""MCP in Foundry, part 2 - build it, connect it, govern it.

Private tools catalog (Azure API Center, preview) -> build your own MCP server (Azure Functions) and where to host a local one
-> the Foundry MCP Server for coding agents (79 tools in 17 categories, preview) -> governing MCP with an AI gateway and the other
levers -> transport details -> gotchas. Part 1 covers the hub, the MCP tool, the public catalog and managed MCP servers.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="mcp-catalog-and-servers-part-2", title="MCP in Foundry: build, connect and govern", section="2", group="Tools and MCP", order=32.5,
    description="MCP in Foundry, part 2: the private API Center catalog (preview), building your own MCP server on Azure Functions or Container Apps, the Foundry MCP Server for coding agents (79 tools in 17 categories, preview), governing MCP with an AI gateway, other levers and transport details.",
    tags=["mcp", "api-center", "azure-functions", "foundry-mcp-server", "ai-gateway", "governance"],
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


def flow(cv, x, y, boxes, gap, *, dashes=None, labels=None, sw=2.5):
    """Place boxes left to right and connect consecutive ones; returns (placed, bottom)."""
    placed, cx = [], x
    for b in boxes:
        b.place(cv, cx, y)
        placed.append(b)
        cx += b.w + gap
    for i, (a, b) in enumerate(zip(placed, placed[1:])):
        connect(cv, a, b, a_side="right", b_side="left", sw=sw, dash=(dashes[i] if dashes else "solid"),
                label=(labels[i] if labels and i < len(labels) else None), label_size=14)
    return placed, y + max(b.h for b in placed)


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


class Tile(Rect2):
    """Count + name tile for the tool wall."""

    def __init__(self, w, count, name, theme, h=112):
        self.th = get_theme(theme)
        self.w, self.h, self.count = w, h, str(count)
        self.lines = metrics.wrap_text(name, (w - 84) * 0.965, 16)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, self.h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + 14, y + self.h / 2 - 22, self.count, size=40, color=th.deep)
            nh = len(self.lines) * 16 * LR
            cv.text(x + 72, y + (self.h - nh) / 2, "\n".join(self.lines), size=16, color=INK)
        cv.register(f"tile:{self.lines[0]}", x, y, self.w, self.h)
        return self


def step_list(cv, x, y, w, steps, *, theme="orange", size=15):
    for i, s in enumerate(steps, 1):
        lines = metrics.wrap_text(s, (w - 46) * 0.965, size)
        h = max(len(lines) * size * LR, 28)
        numbered(cv, x + 15, y + 14, i, theme=theme, d=28, size=15)
        cv.text(x + 40, y + (h - len(lines) * size * LR) / 2, "\n".join(lines), size=size, color=INK)
        y += h + 10
    return y - 10


# ---------------------------------------------------------------------------------------------- 1. private catalog
def private_catalog(cv, y):
    y = sec(cv, y, "1  The private tools catalog (Azure API Center, preview)",
            sub="Your own registry of approved MCP servers: admins publish in API Center, developers find them in the Foundry portal.") + 40
    bw, gap = 560, 110
    rows = [
        ("API Center admin", "grape", [
            ("1  Register the server", "Inventory > Assets > Register an asset > MCP server; add environments and deployments"),
            ("2  Add an auth scheme (optional)", "Governance > Authorization > Add configuration: API Key, OAuth or HTTP bearer"),
            ("3  Manage access (preview)", "Server Details > Versions > Manage access"),
        ]),
        ("Developer in Foundry", "orange", [
            ("4  Get the role", "Azure API Center Data Reader; it can take up to 24 hours to propagate"),
            ("5  Find the catalog", "Build > Tools: filter by a registry named after the API Center"),
            ("6  Connect and test", "Add the server to an agent or a toolbox; approvals apply as for any MCP tool"),
        ]),
    ]
    cy = y
    last = []
    for label, th, items in rows:
        with cv.panel(0, cy, w=3 * bw + 2 * gap + 44, title=label, theme=th, style="dotted", pad=22, title_size=22) as p:
            boxes = [Box(bw, t, sub=s, theme=th, h=118, size=19, sub_size=14, dash="dashed" if "preview" in t else "solid") for t, s in items]
            flow(cv, p.ix, p.iy, boxes, gap)
        last.append(p)
        cy = p.bottom + 30
    rx = 3 * bw + 2 * gap + 44 + GUT
    rw = W - rx
    n1 = Note(rw, "With the API Key scheme, the key you store in Azure Key Vault is not used automatically in Foundry: developers must provide the API key when they configure the MCP server connection.",
              kind="warn", title="API Key scheme", size=15, src=src("priv"))
    n1.place(cv, rx, y)
    n2 = Note(rw, "The catalog name in Foundry is the API Center name, shown as a registry filter in Build > Tools. A Foundry project role alone is not enough: the Data Reader role is needed on the API Center.",
              kind="info", title="Where it shows up", size=15, src=src("priv"))
    n2.place(cv, rx, n1.bottom + 22)
    return max(cy - 30, n2.bottom) + 10


# ---------------------------------------------------------------------------------------------- 2. build your own
def build_own(cv, y):
    y = sec(cv, y, "2  Build your own MCP server",
            sub="Any HTTP server can speak MCP. The Foundry guide uses Azure Functions; local servers need a remote home on Azure Container Apps or Azure Functions.") + 40
    bw, gap = 520, 120
    steps = [
        Box(bw, "1  Deploy the MCP server", sub="Azure Functions, from the remote-mcp-functions-python template", theme="orange", h=130, size=19, sub_size=14, icon="functions", icon_pos="top"),
        Box(bw, "2  Register it (optional)", sub="Publish it in your API Center private catalog", theme="orange", h=130, size=19, sub_size=14, dash="dashed", icon="apim", icon_pos="top"),
        Box(bw, "3  Connect it in Foundry", sub="Build > Tools > Connect a tool > Custom > MCP", theme="orange", h=130, size=19, sub_size=14, icon="foundry", icon_pos="top"),
        Box(bw, "4  The agent calls it", sub="when the model needs one of your tools", theme="green", h=130, size=19, sub_size=14, icon="agent", icon_pos="top"),
        Box(bw, "5  Your server answers", sub="validates the call, uses the internal API, returns the result", theme="orange", h=130, size=19, sub_size=14, icon="mcp", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, steps, gap, dashes=["dashed", "solid", "solid", "solid"])
    cy = b + 40
    code = CodeCard(SPAN(2), "Build and deploy (Azure Functions)", [
        "azd init --template remote-mcp-functions-python -e mcpserver-python",
        "func start        # run locally",
        "azd up            # deploy",
        "azd down --purge  # clean up",
    ], theme="orange", note="Needs Python 3.13 or later, Azure Functions Core Tools 4.8.0 or later and azd 1.23.0 or later. The template ships sample MCP tools, resources and prompts. "
                            "Endpoint: https://{function_app_name}.azurewebsites.net/runtime/webhooks/mcp. Key: the mcp_extension system key, sent as x-functions-key.",
        src=src("build"))
    code.place(cv, 0, cy)
    at = Table([("Function app auth", 230), ("Foundry connection auth", 300), "What you configure"], [
        [("Function keys", "orange"), "Key-based", "Credential \"x-functions-key\": the mcp_extension system key"],
        [("Microsoft Entra", "red"), "Microsoft Entra authentication", "Project managed identity plus the Audience (Application ID URI); turn on Function App Authentication"],
        [("OAuth identity passthrough", "red"), "Custom OAuth with an Entra app registration", "Client ID and secret, auth URL, token URL, refresh URL and scopes; add Foundry's redirect URL to the app registration"],
        [("Unauthenticated", "gray"), "None", "Limited use; not for production"],
    ], w=SPAN(2) + GUT + 40, theme="orange", size=15, head_size=16, title="Auth mapping: from the Function app to the Foundry connection", title_size=20)
    at.place(cv, SPAN(2) + GUT, cy)
    sb = Card(SPAN(2) - 120, "Security baseline", [
        "Require authentication",
        "Keep secrets in Key Vault",
        "Least privilege on downstream calls",
        "Log and monitor tool calls",
    ], theme="red", icon="key-vault", src=src("build"))
    sb.place(cv, at.right + GUT, cy)
    ly = learn_line(cv, at.x, at.bottom + 8, src("build", "auth"))
    y2 = max(code.bottom, at.bottom, sb.bottom) + 50
    hosting = Table([("Aspect", 200), ("Azure Container Apps", 460), ("Azure Functions", 460)], [
        [("Transport", "orange"), "HTTP POST and GET endpoints", "HTTP streamable"],
        [("Code changes", "orange"), "Container rebuild", "Functions-specific configuration files in the root"],
        [("Auth", "red"), "Custom auth implementation", "Key-based only; OAuth needs API Management"],
        [("Languages", "orange"), "Any (Linux containers: Python, Node.js, .NET, TypeScript, Go)", "Python, Node.js, Java, .NET"],
        [("Container requirements", "orange"), "linux/amd64 only; no privileged containers", "Containerized servers are not supported"],
        [("Dependencies", "orange"), "All in the image", "OS-level dependencies (for example Playwright) are unsupported"],
        [("State", "orange"), "Stateless only", "Stateless only"],
        [("UVX and NPX", "orange"), "Supported", "Not supported"],
    ], w=SPAN(3) + 40, theme="orange", size=15, head_size=16, title="Hosting a local MCP server to get a remote endpoint: Container Apps or Functions", title_size=20)
    hosting.place(cv, 0, y2)
    ly2 = learn_line(cv, 0, hosting.bottom + 8, src("tool"))
    rx = hosting.right + GUT
    c1 = Card(W - rx, "Custom code interpreter", [
        "An Azure Container Apps dynamic sessions pool exposes an MCP server",
        "Point the tool at it with mcpServerEndpoint",
    ], theme="orange", icon="container-apps", src=src("tool"))
    c1.place(cv, rx, y2)
    c2 = Card(W - rx, "Private hosting", [
        "Private MCP needs Standard Agent Setup with private networking (BYO VNet)",
        "Tested host: Container Apps with internal-only ingress on a subnet delegated to Microsoft.App/environments",
        "Templates: 19-private-network-agent-tools (Bicep), 19-private-network-agent-setup-with-tools (Terraform) or 11-private-network-basic-vnet",
    ], theme="indigo", icon="vnet", src=src("tool", "plink"))
    c2.place(cv, rx, c1.bottom + 22)
    return max(ly2, c2.bottom) + 10


# ---------------------------------------------------------------------------------------------- 3. Foundry MCP Server
CATS = [
    ("Agent management", 7, "green"), ("Hosted agent sessions and files", 11, "green"), ("Toolbox management", 6, "orange"),
    ("Dataset management", 4, "cyan"), ("Data generation jobs", 4, "cyan"), ("Evaluation operations", 5, "violet"),
    ("Trace evaluation", 2, "violet"), ("Evaluation suites", 9, "violet"), ("Evaluator catalog", 4, "violet"),
    ("Evaluator generation jobs", 3, "violet"), ("Model catalog and details", 2, "blue"), ("Model deployment management", 5, "blue"),
    ("Model analytics and recommendations", 4, "blue"), ("Model monitoring and operations", 3, "blue"), ("Project connections", 6, "cyan"),
    ("Prompt optimization", 1, "green"), ("Continuous evaluation", 3, "violet"),
]


def foundry_server(cv, y):
    y = sec(cv, y, "3  The Foundry MCP Server for coding agents (preview)",
            sub="A cloud-hosted MCP server at https://mcp.ai.azure.com. It is developer tooling for VS Code, GitHub Copilot and other MCP clients - not an Agent Service tool.") + 40
    LW = 1500
    boxes = [
        Box(400, "Coding agent", sub="VS Code 1.99 or later with GitHub Copilot, Agent Mode", theme="gray", h=150, size=20, sub_size=14, icon="vscode", icon_pos="top"),
        Box(460, "Foundry MCP Server", sub="https://mcp.ai.azure.com: a global stateless proxy on a public endpoint", theme="gray", h=150, size=20, sub_size=14, icon="foundry", icon_pos="top", dash="dashed"),
        Box(360, "Your Foundry resources", sub="read and write operations as the signed-in user", theme="blue", h=150, size=20, sub_size=14, icon="openai", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, boxes, 140, labels=["Entra token", "On-Behalf-Of"])
    cy = b + 36
    with cv.panel(0, cy, w=LW, title="Connect VS Code in five steps", theme="gray", style="solid", fill="soft", pad=22, title_size=21) as st:
        sb = step_list(cv, st.ix, st.iy, LW - 44, [
            "In VS Code with GitHub Copilot, switch to Agent Mode.",
            "Command Palette > MCP: Add Server > HTTP (HTTP or Server-Sent Events).",
            "Enter the URL https://mcp.ai.azure.com and a name such as foundry-mcp-remote, or add it to .vscode/mcp.json.",
            "MCP: List Servers > Start the server > sign in with Microsoft Entra.",
            "Answer the permission prompts: Current session, Current workspace or Always allow.",
        ], theme="gray")
    code = CodeCard(LW, ".vscode/mcp.json", [
        "{ \"servers\": { \"foundry-mcp-remote\": {",
        "    \"type\": \"http\",",
        "    \"url\": \"https://mcp.ai.azure.com\" } } }",
    ], theme="gray", src=src("start"))
    code.place(cv, 0, st.bottom + 24)
    n_net = Note(LW, "No network isolation: the endpoint is public and Private Link resources are unreachable. It is a global stateless proxy: data is processed in EU or US data centers, encrypted in transit and not stored; cross-region processing is possible. "
                     "There is no SLA and the tool set can change. For private connectivity build your own MCP server and use Agent Service private MCP.",
                 kind="gotcha", title="Public only, no SLA", size=15, src=src("sec"))
    n_net.place(cv, 0, code.bottom + 24)
    # right: the wall
    rx = LW + GUT
    rw = W - rx
    cv.text(rx, y - 6, "79 tools in 17 categories", size=24, color=get_theme("gray").deep)
    tw = (rw - 5 * 14) / 6
    tiles = [Tile(tw, n, name, th) for name, n, th in CATS]
    total = Tile(tw, 79, "tools in total", "gray")
    for i, t in enumerate(tiles + [total]):
        t.place(cv, rx + (i % 6) * (tw + 14), y + 36 + (i // 6) * (t.h + 14))
    wy = y + 36 + 3 * (112 + 14)
    cv.text(rx, wy - 2, "Colour = area: green agents and prompts, orange toolbox, cyan data and connections, violet evaluation, blue models.", size=14, color=MUTED)
    names = Table([("Category", 280), "Tools named in the docs"], [
        ["Agent management (7)", "agent_get, agent_update, agent_invoke, agent_delete, agent_container_control, agent_container_status_get, agent_definition_schema_get"],
        ["Hosted agent sessions and files (11)", "session_create/get/list/delete/logstream; session_file_list/stat/mkdir/upload/download/delete"],
        ["Model catalog and details (2)", "model_catalog_list, model_details_get"],
        ["Model deployment management (5)", "model_deploy_azure_direct_model, model_deploy (deprecated alias), model_deploy_managed_compute, model_deployment_get, model_deployment_delete"],
        ["Model monitoring and operations (3)", "model_monitoring_metrics_get, model_deprecation_info_get, model_quota_list"],
        ["Project connections (6)", "list, get, list_metadata, create, update, delete"],
        ["Prompt optimization (1)", "prompt_optimize"],
    ], w=rw, theme="gray", size=14, head_size=15, title="Tool names the docs spell out (the other categories give counts only)", title_size=19)
    names.place(cv, rx, wy + 32)
    ly = learn_line(cv, rx, names.bottom + 8, src("avail"))
    rbac = Table([("Operation", 330), "Azure role needed"], [
        ["Read", "Reader"], ["Write and delete", "Contributor"], ["Manage access", "Owner or User Access Administrator"],
        ["Configure tenant Conditional Access", "Conditional Access Administrator"],
    ], w=(LW - GUT) / 2, theme="red", size=15, head_size=16, title="RBAC for the operations", title_size=19)
    rbac.place(cv, 0, n_net.bottom + 36)
    ca = CodeCard((LW - GUT) / 2, "Conditional Access", [
        "az ad sp create --id fcdfa2de-b65b-4b54-9a1c-81c8a18282d9",
    ], theme="red", note="That is the Foundry MCP Server application ID. Then: Enterprise applications > Conditional Access > block selected users or groups.", src=src("sec"))
    ca.place(cv, rbac.right + GUT, n_net.bottom + 36)
    bp = Card(rw, "Best practices for write operations", [
        "Verify each tool and its parameters (resource IDs, project endpoint formats); test in non-production first",
        "Make incremental changes, verify read-only first, back up configurations and use Activity Logs",
        "! Writes are live: deployments bill immediately, deletions break apps, evaluations consume quota and datasets can be overwritten",
        "A project needs Contributor or higher for the get-started path",
    ], theme="red", icon="compliance", src=src("sec", "start"))
    bp.place(cv, rx, ly + 28)
    return max(rbac.bottom, ca.bottom, bp.bottom) + 10


# ---------------------------------------------------------------------------------------------- 4. governance
def governance(cv, y):
    y = sec(cv, y, "4  Governing MCP: the AI gateway and the other levers",
            sub="The gateway (Azure API Management, preview) adds auth, rate limits, IP restrictions and audit logging without touching the MCP server or the agent code.") + 40
    agent = Box(420, "Agent Service agent", sub="MCP tool whose server_url is the gateway URL", theme="green", h=150, size=20, sub_size=14, icon="agent", icon_pos="top")
    gw = Box(560, "AI gateway (Azure API Management)", sub="https://<your-API-Management-instance>.azure-api.net/mcp/...", theme="grape", h=150, size=20, sub_size=14, icon="apim", icon_pos="top")
    srv = Box(420, "Your MCP server", sub="managed identity, key, custom OAuth passthrough or no auth", theme="orange", h=150, size=20, sub_size=14, icon="mcp", icon_pos="top")
    placed, b = flow(cv, 0, y, [agent, gw, srv], 150, labels=["calls", "forwards"])
    pol = Table([("APIM policy", 250), "What it does"], [
        ["rate-limit-by-key", "Example: calls = 60 per renewal-period = 60, keyed per IP"],
        ["ip-filter", "Allow list of client IP addresses"],
        ["Correlation header", "X-Correlation-Id = context.RequestId"],
        ["Delete headers", "Remove Cookie and Referer; never strip Authorization unless you are sure"],
        ["choose / when + set-backend-service", "Route by the X-Region header (geo routing)"],
    ], w=1100, theme="grape", size=15, head_size=16, title="Policies the docs show (applied in the Azure portal only)", title_size=19)
    pol.place(cv, 1900, y - 10)
    steps_y = b + 40
    with cv.panel(0, steps_y, w=1860, title="Set it up", theme="grape", style="solid", fill="soft", pad=22, title_size=21) as sp:
        step_list(cv, sp.ix, sp.iy, 1860 - 44, [
            "Connect an AI gateway to the Foundry resource (it is activated at resource level); you need API Management Service Contributor or Owner on the APIM instance.",
            "Create a NEW MCP tool in the Foundry portal that does not use managed OAuth; the tool config then shows the APIM gateway URL.",
            "Apply the policies in the Azure portal (they are not editable in Foundry).",
            "Test in an agent, then check APIM metrics: 2xx versus 429 (rate limit) and 403 (IP filter); X-RateLimit-Remaining; diagnostic settings to Azure Monitor Logs.",
        ], theme="grape")
    lim = Card(1100, "Limitations", [
        "Gateways support only MCP tools: not SharePoint, code-first MCP tools, managed-OAuth tools or OpenAPI tools",
        "Gateway routing is applied only at tool creation: existing tools are not retrofitted",
        "! They do not log tool traces",
        "! A gateway created from the new portal for a private Foundry is public by default - isolate it in the Azure portal",
    ], theme="red", icon="preview-features", src=src("gov", "gw"))
    lim.place(cv, 1900, pol.bottom + 24)
    y2 = max(sp.bottom, lim.bottom) + 50
    levers = Table([("Lever", 300), ("What it controls", 1000), "Where it lives"], [
        [("AI gateway (APIM, preview)", "grape"), "Auth, rate limits, IP restrictions and audit logging for new portal-created MCP tools without managed OAuth", "Foundry portal + Azure portal (policies)"],
        [("allowed_tools", "orange"), "Which tools the agent may call; an empty list allows ALL tools; names are case-sensitive", "MCP tool config"],
        [("require_approval", "orange"), "Human approval per call; default always. The toolbox endpoint does not block calls: the agent runtime must enforce it", "MCP tool config, agent runtime"],
        [("Toolbox guardrails (preview)", "pink"), "Checks on the tool call and the tool response", "Toolbox"],
        [("API Center RBAC and allowed tools", "grape"), "Who can see and use the servers in a private catalog", "Azure API Center"],
        [("Conditional Access", "red"), "Who can use the Foundry MCP Server", "Microsoft Entra enterprise application"],
        [("Azure Policy", "grape"), "For example block Bing resources", "Azure Policy"],
        [("Private networking", "indigo"), "Private MCP servers through Standard Agent Setup with BYO VNet", "Network (Container Apps subnet)"],
    ], w=W, theme="grape", size=15, head_size=16, title="Governance levers at a glance", title_size=21)
    levers.place(cv, 0, y2)
    ly = learn_line(cv, 0, levers.bottom + 8, src("gov", "gw", "tool", "sec"))
    n = Note(W, "A different feature, not the MCP tools gateway above: when you bring your own gateway for model traffic, the docs list the agent tools that can sit behind it - Code Interpreter, Functions, File Search, OpenAPI, Foundry IQ, SharePoint Grounding, Fabric Data Agent, MCP and Browser Automation.",
             kind="info", title="Do not confuse it with the model gateway", size=15)
    n.place(cv, 0, ly + 24)
    return n.bottom + 10


# ---------------------------------------------------------------------------------------------- 5. transport + notes
def transport(cv, y):
    y = sec(cv, y, "5  Transport and protocol details", sub="What each surface speaks, as documented.") + 36
    t = Table([("Surface", 300), ("Transport", 420), "Documented details"], [
        [("Agent Service MCP tool", "orange"), "Remote MCP server endpoint", "Non-streaming calls time out at 100 s; long-running operations use the MCP tasks capability (preview)"],
        [("Toolbox endpoint", "orange"), "MCP over streamable HTTP", "initialize uses protocolVersion 2025-03-26; no ping and no prompts/list; no non-streaming tools/call; supports MCP resources (skills) and tasks (preview, spec 2025-11-25); JSON-RPC error -32006 means OAuth consent is required"],
        [("Foundry MCP Server", "gray"), "HTTP (VS Code type http)", "Entra bearer token for https://mcp.ai.azure.com; delegated scope https://mcp.ai.azure.com/Foundry.Mcp.Tools when used through a connection"],
        [("Azure Functions-hosted server", "orange"), "HTTP streamable", "Endpoint path /runtime/webhooks/mcp"],
        [("Azure Container Apps-hosted server", "orange"), "HTTP POST and GET", "Use internal-only ingress for private MCP"],
        [("Custom code interpreter", "orange"), "ACA dynamic sessions pool exposes an MCP server", "Use mcpServerEndpoint"],
        [("Foundry IQ knowledge base", "teal"), "MCP tool knowledge_base_retrieve", "At the Azure AI Search knowledge base endpoint (API 2026-08-01-preview)"],
        [("Fabric IQ and Work IQ", "teal"), "MCP or A2A endpoints", "See the Tool catalog canvas"],
    ], w=W, theme="orange", size=15, head_size=16, title="Transport by surface", title_size=21)
    t.place(cv, 0, y)
    return learn_line(cv, 0, t.bottom + 8, src("tool", "build", "start"))


def notes(cv, y):
    y = sec(cv, y, "6  Gotchas to remember", sub="Preview status follows each feature's Learn page as of 2026-11-03: the private catalog, managed MCP servers, AI-gateway governance and the Foundry MCP Server are preview.") + 36
    n = lambda kind, title, text, *keys: Note(COL, text, kind=kind, title=title, size=15, src=src(*keys))
    items = [
        n("gotcha", "Foundry MCP Server is developer tooling", "It is for VS Code, GitHub Copilot and similar clients, and it cannot reach private-link Foundry resources. Its write tools are live.", "sec", "start"),
        n("warn", "The gateway skips some tools", "AI gateways exclude managed-OAuth tools and any tool created before the gateway was connected. A gateway made from the new portal for a private Foundry is public by default.", "gov"),
        n("warn", "Private MCP needs Standard setup", "A dedicated MCP subnet and Standard Agent Setup with private networking are required; Basic setup is unsupported.", "tool", "plink"),
        n("warn", "API Key schemes need the key twice", "The key stored in Azure Key Vault for an API Center API Key scheme is not used automatically: developers enter it in the connection.", "priv"),
        n("info", "Functions: keys only", "An Azure Functions MCP server uses key-based auth only; for OAuth put API Management in front. Containerized servers and OS-level dependencies are not supported there.", "tool", "build"),
        n("info", "Tool set can change", "The Foundry MCP Server offers no SLA and its tool list may change: re-check the available-tools page before you rely on a tool.", "avail"),
    ]
    _, b = row(cv, 0, y, items, gap=GUT)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, b = title_block(cv, 0, 0, "MCP in Foundry: build, connect and govern",
                       "Private catalogs, servers you build, the Foundry MCP Server for coding agents and governance through an AI gateway - part 2 of 2 (as of 2026-11-03)",
                       icon="mcp", w=W)
    y = b + 26
    legend(cv, 0, y, [("MCP servers and tools", "orange"), ("Agents and Agent Service", "green"), ("Auth and identity", "red"),
                      ("Governance and gateway", "grape"), ("Networking", "indigo"), ("Foundry MCP Server and coding agents", "gray")])
    cv.text(2400, y, "Dashed border = preview. Part 1 covers the hub and the MCP tool.", size=15, color=MUTED)
    y = private_catalog(cv, y + 60)
    y = build_own(cv, y + SEC)
    y = foundry_server(cv, y + SEC)
    y = governance(cv, y + SEC)
    y = transport(cv, y + SEC)
    y = notes(cv, y + SEC)
    sources(cv, 0, y + SEC, [L["priv"], L["build"], L["start"], L["avail"], L["sec"], L["gov"], L["gw"], L["tool"], L["auth"], L["plink"], L["conn"], L["ref"]], w=W, cols=3)
