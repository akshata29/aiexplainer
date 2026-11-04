"""Foundry Toolbox - one governed, versioned MCP endpoint in front of every tool an agent needs."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import THEMES

META = dict(
    id="toolbox", title="Foundry Toolbox", section="2", group="Tools and MCP", order=30,
    description="Toolbox: one versioned, governed MCP endpoint in front of 13 tool types - architecture, versions and promotion, tool search, private catalogs, guardrails, identity, network isolation and the end-to-end flow.",
    tags=["toolbox", "mcp", "tools", "versioning", "tool-search", "governance"],
)

W = 3000          # canvas content width
COL = 968         # two-column card width (3 per row with 48 gaps)
GAP = 48


# ====================================================================== local helpers
class Code(Rect2):
    """Monospace code panel (kit has no code block)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=14, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title = w, size, pad, title
        self.src = list(src)
        inner = (w - 2 * pad) * 0.965
        self.lines = []
        for ln in lines:
            ind = len(ln) - len(ln.lstrip(" "))
            wrapped = metrics.wrap_text(ln.strip(), inner - ind * size * 0.55, size, metrics.MONO) if ln.strip() else [""]
            for i, part in enumerate(wrapped):
                self.lines.append(" " * (ind + (2 if i else 0)) + part)
        lh = size * metrics.line_ratio(metrics.MONO)
        self.lh = lh
        self.title_h = (18 * metrics.line_ratio() + 6) if title else 0
        self.src_lines = [(f"Learn: {lbl}", url) for lbl, url in self.src]
        self.h = pad * 2 + self.title_h + len(self.lines) * lh + (len(self.src_lines) * 15 + 6 if self.src_lines else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill="#f8f9fa", style="solid", sw=2, dash="solid")
            ty = y + self.pad
            if self.title:
                cv.text(x + self.pad, ty, self.title, size=18, color=th.deep)
                ty += self.title_h
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color="#1e1e1e", font=metrics.MONO)
            ty += len(self.lines) * self.lh + 6
            for txt, url in self.src_lines:
                cv.text(x + self.pad, ty, txt, size=12, color=LINK, link=url)
                ty += 15
        cv.register("code", x, y, self.w, H)
        return self


def chevron(cv, x, y, w, h, label, theme, *, first=False, size=26):
    th = THEMES[theme]
    d = h * 0.42
    if first:
        pts = [(x, y), (x + w - d, y), (x + w, y + h / 2), (x + w - d, y + h), (x, y + h), (x, y)]
        cx = x + (w - d) / 2
    else:
        pts = [(x, y), (x + w - d, y), (x + w, y + h / 2), (x + w - d, y + h), (x, y + h), (x + d, y + h / 2), (x, y)]
        cx = x + w / 2
    cv.poly(pts, kind="line", stroke=th.stroke, fill=th.fill, fill_style="hachure", sw=2)
    tw, tth = metrics.text_size(label, size)
    cv.text(cx - tw / 2, y + (h - tth) / 2, label, size=size, color=th.deep)


def endpoint_box(cv, x, y, w, heading, url, foot, theme):
    """Rounded box with a heading, a monospace endpoint URL and a footnote."""
    th = THEMES[theme]
    pad = 14
    hl = metrics.wrap_text(heading, (w - 2 * pad) * 0.965, 17)
    ul = metrics.wrap_text(url, (w - 2 * pad) * 0.965, 15, metrics.MONO)
    fl = metrics.wrap_text(foot, (w - 2 * pad) * 0.965, 15)
    lh, lm = metrics.line_ratio(), metrics.line_ratio(metrics.MONO)
    H = pad * 2 + len(hl) * 17 * lh + len(ul) * 15 * lm + len(fl) * 15 * lh + 10
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
        ty = y + pad
        cv.text(x + pad, ty, "\n".join(hl), size=17, color=th.deep)
        ty += len(hl) * 17 * lh + 4
        cv.text(x + pad, ty, "\n".join(ul), size=15, color="#1e1e1e", font=metrics.MONO)
        ty += len(ul) * 15 * lm + 4
        cv.text(x + pad, ty, "\n".join(fl), size=15, color="#495057")
    cv.register("endpoint:" + heading, x, y, w, H)
    r = Rect2()
    r.x, r.y, r.w, r.h = x, y, w, H
    return r


def small_label(cv, x, y, text, *, size=16, color="#495057", w=None, align="left"):
    return cv.text(x, y, text, size=size, color=color, w=w, align=align)


def numbered_step(cv, card, n, theme):
    numbered(cv, card.x + 26, card.y + 2, n, theme=theme, d=34, size=18)


# ====================================================================== band 1: definition, status, before/after, pillars
def band_intro(cv, y):
    quote = Note(1984, "Toolbox provides a centralized way to manage and share tools in Microsoft Foundry. With Toolbox, you define a "
                       "curated set of tools once and expose them through a single MCP-compatible endpoint that agents can consume "
                       "across frameworks and runtimes.", kind="quote", title="What is Toolbox? (Learn wording)",
                 src=[("What is Toolbox in Foundry?", learn("agents/concepts/toolbox-overview"))])
    status = Note(COL, "Learn pages carry no GA or preview label for the Toolbox itself. Preview sub-features: skills, Work IQ, Fabric IQ, "
                       "Reminder tool, managed MCP connectors, AI-gateway governance. .NET toolbox types are prerelease "
                       "(2.1.0-beta.4). The Foundry Blog announced Toolboxes in public preview on 2026-04-22 (blog, not Learn).",
                  kind="preview", title="Status as of 2026-11-03")
    row(cv, 0, y, [quote, status], gap=GAP)
    y = max(quote.bottom, status.bottom) + 44

    # --- before / after
    with cv.panel(0, y, title="Why a toolbox: N agents x M tools x own auth", theme="gray", style="dotted", w=COL, pad=22,
                  title_size=22) as ba:
        bx = ba.ix
        by = ba.iy + 6
        half = 424
        names = ["Agent A", "Agent B", "Agent C"]
        tools = ["MCP server", "REST API", "Skills"]
        # before
        ag = [Box(120, n, h=44, theme="green", size=15).place(cv, bx, by + i * 64) for i, n in enumerate(names)]
        tl = [Box(130, t, h=44, theme="orange", size=15).place(cv, bx + half - 130, by + i * 64) for i, t in enumerate(tools)]
        for a in ag:
            for t in tl:
                cv.line((a.right + 4, a.cy), (t.x - 4, t.cy), stroke="#e03131", sw=1.5, opacity=55)
        cv.text(bx, by - 2 - 0, "", size=1)
        small_label(cv, bx, by + 3 * 64 + 2, "Before", size=20, color="#c92a2a")
        t1 = cv.text(bx, by + 3 * 64 + 30, "", size=1)
        txt1 = metrics.wrap_text("Every agent keeps its own tool definitions, secrets and token refresh; governance is inconsistent.", half * 0.96, 15)
        cv.text(bx, by + 3 * 64 + 28, "\n".join(txt1), size=15, color="#1e1e1e")
        # after
        ax = bx + half + 56
        ag2 = [Box(120, n, h=44, theme="green", size=15).place(cv, ax, by + i * 64) for i, n in enumerate(names)]
        hub = Box(110, "Toolbox", h=172, theme="orange", size=17, icon="toolbox-icon", icon_size=40).place(cv, ax + 150, by + 8)
        tl2 = [Box(130, t, h=44, theme="orange", size=15, fill="soft").place(cv, ax + half - 130, by + i * 64) for i, t in enumerate(tools)]
        for a in ag2:
            connect(cv, a, hub, a_side="right", b_side="left", gap=4, sw=1.5, tb=0.5)
        for t in tl2:
            connect(cv, hub, t, a_side="right", b_side="left", gap=4, sw=1.5, ta=0.5)
        small_label(cv, ax, by + 3 * 64 + 2, "After", size=20, color="#2b8a3e")
        txt2 = metrics.wrap_text("N agents -> 1 toolbox endpoint -> M tools. Define once; credentials, guardrails and versions live in one place.", half * 0.96, 15)
        cv.text(ax, by + 3 * 64 + 28, "\n".join(txt2), size=15, color="#1e1e1e")
        # dummy elements keep panel bbox honest
        cv.rect(bx, by + 3 * 64 + 28 + 3 * 19 + 6, 2, 2, stroke="transparent", fill="transparent")

    # --- four pillars
    px = COL + GAP
    d_w, step = 515, 489
    pillars = [
        ("BUILD", "orange", [
            "Create reusable collections of tools and skills (preview) and publish once",
            "Configure authentication centrally - no per-agent credentials",
            "Versioning: create and test a new version, then promote it to default",
        ]),
        ("DISCOVER", "teal", [
            "Tool search finds the most relevant tools at runtime",
            "Tools are hidden by default; two meta-tools are exposed: tool_search and call_tool",
            "One toolbox can hold hundreds of tools without flooding the model's context",
        ]),
        ("CONSUME", "green", [
            "Agents connect to a single MCP-compatible endpoint",
            "Add, remove or reconfigure tools without changing agent code or redeploying",
            "Works across protocols, authentication models, frameworks and runtimes",
        ]),
        ("GOVERN", "grape", [
            "Authentication, authorization, guardrails, observability and version management at toolbox level",
            "Credential injection, token refresh and policy enforcement via Microsoft Entra ID and OAuth passthrough",
            "Guardrails (Responsible AI policies) on tool inputs and outputs",
        ]),
    ]
    ch_h = 70
    for i, (lab, th, _) in enumerate(pillars):
        chevron(cv, px + i * step, y, d_w, ch_h, lab, th, first=(i == 0))
    cards = [Card(478, None, body, theme=th, fill="soft", body_size=16) for _, th, body in pillars]
    cw = 478
    cgap = (1984 - 4 * cw) / 3
    r, b = row(cv, px, y + ch_h + 20, cards, gap=cgap)
    # key-capability strip
    src = Note(1984, "Key capabilities: Single endpoint - Centralized authentication - Governance by default - Versioning. Created and managed in Foundry, "
                     "but any MCP-compatible runtime or client can use a toolbox, including Microsoft Agent Framework, LangGraph or your own code.",
               kind="key", title="Foundry-homed, not Foundry-bound", src=[("What is Toolbox in Foundry?", learn("agents/concepts/toolbox-overview"))])
    src.place(cv, px, b + 20)
    return max(ba.bottom, src.bottom)


# ====================================================================== band 2: architecture
def band_arch(cv, y):
    r, b = section_header(cv, 0, y, "Architecture: one governed endpoint between agents and tools",
                          sub="Consumers connect with MCP over streamable HTTP and a Microsoft Entra token; the toolbox calls the tools", size=32)
    y = b + 30
    c1 = Card(COL, "Prompt agents", [
        "Agent Service prompt agents attach the toolbox as an mcp tool: server_label, server_url = toolbox endpoint, require_approval",
        "project_connection_id points to a remote-tool connection to the toolbox endpoint (user Entra token, audience https://ai.azure.com)",
        "Agent identity needs Foundry User on the project; skills only through the shell tool",
    ], theme="green", icon="agent", subtitle="Foundry Agent Service", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    c2 = Card(COL, "Hosted agents", [
        "Python: Microsoft Agent Framework FoundryToolbox",
        ".NET: AddFoundryToolboxes(credential, toolboxName)",
        "LangGraph: AzureAIProjectToolbox(toolbox_name=...)",
        "GitHub Copilot SDK: custom McpBridge ('.' in tool names becomes '_')",
        "x-agent-foundry-call-id header is forwarded so the toolbox proxy resolves caller context",
        "Env: TOOLBOX_ENDPOINT, or FOUNDRY_PROJECT_ENDPOINT + TOOLBOX_NAME",
    ], theme="green", icon="container-apps", subtitle="your code running in Agent Service",
        src=[("Use a toolbox in a hosted agent", learn("agents/how-to/tools/use-toolbox-hosted-agent"))])
    c3 = Card(COL, "Any MCP client", [
        "Streamable HTTP MCP: initialize (protocolVersion 2025-03-26) -> notifications/initialized -> tools/list -> tools/call",
        "MCP SDKs: mcp (Python), @modelcontextprotocol/sdk (JS), ModelContextProtocol.Client (.NET)",
        "Custom Agent Framework / LangGraph agents, IDEs and coding agents",
        "No agent-blueprint sign-in or AgentOnBehalfOfUser; handle per-tool OAuth consent yourself",
    ], theme="gray", icon="mcp", subtitle="Foundry-homed, not Foundry-bound", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    cons = [c1, c2, c3]
    row(cv, 0, y, cons, gap=GAP)
    cb = max(c.bottom for c in cons)

    # ---- hub
    hub_y = cb + 130
    with cv.panel(0, hub_y, title="Toolbox", sub="a logical container for tools - the hosting Foundry project's networking, RBAC and connections govern it",
                  theme="orange", style="solid", fill="soft", w=W, pad=26, title_size=34, sub_size=17) as hub:
        iy = hub.iy
        ix = hub.ix
        e1 = endpoint_box(cv, ix, iy, 1000, "Consumer endpoint - agents connect here",
                          "{project_endpoint}/toolboxes/{name}/mcp?api-version=v1", "always serves default_version", "green")
        e2 = endpoint_box(cv, ix, e1.bottom + 16, 1000, "Developer endpoint - test a version before promoting",
                          "{project_endpoint}/toolboxes/{name}/versions/{v}/mcp?api-version=v1", "pinned to version {v}", "blue")
        # version stack
        vx = ix + 1040
        cv.text(vx, iy, "Versions: immutable snapshots", size=18, color=THEMES["orange"].deep)
        chip = Chip("default_version", theme="green", size=15).place(cv, vx, iy + 36)
        v_y = iy + 106
        v1 = Box(170, "v1", sub="auto-default", h=76, theme="orange", size=22, fill="solid").place(cv, vx, v_y)
        v2 = Box(170, "v2", sub="staged", h=76, theme="orange", size=22, fill="soft").place(cv, vx + 250, v_y)
        v3 = Box(170, "v3", sub="staged", h=76, theme="orange", size=22, fill="soft", dash="dashed").place(cv, vx + 500, v_y)
        connect(cv, chip, v1, a_side="bottom", b_side="top", gap=3)
        connect(cv, v1, v2, label="new version", label_size=13, gap=4)
        connect(cv, v2, v3, label="new version", label_size=13, gap=4)
        cv.text(vx, v_y + 90, "later versions are not auto-promoted", size=15, color="#495057")
        # capability rows: chip + one-line explanation
        kx = ix + 1040 + 700 + 24
        kw = W - 26 - kx
        cv.text(kx, iy, "Built into the endpoint", size=18, color=THEMES["orange"].deep)
        caps = [
            ("Tool search (BM25)", "teal", "exposes tool_search + call_tool instead of every tool definition"),
            ("Guardrails", "pink", "Responsible AI policy on tool inputs and outputs, separate from model filters"),
            ("Credential injection", "red", "token refresh and OAuth consent; the auth type lives on the project connection"),
            ("Skills as MCP resources", "orange", "preview: skill://{name} via resources/list and resources/read"),
            ("MCP tasks", "orange", "preview: long-running tool calls (MCP spec 2025-11-25)"),
            ("Version promotion", "grape", "stage, test on the developer endpoint, promote, roll back"),
        ]
        cy = iy + 34
        for lab, th, txt in caps:
            c = Chip(lab, theme=th, size=15, w=250, pad_y=4).place(cv, kx, cy)
            cv.text(kx + 266, cy + (c.h - 15 * metrics.line_ratio()) / 2, txt, size=15, color="#1e1e1e")
            cy += c.h + 8
    # consumers -> hub arrows
    labels = ["mcp tool + connection", "FoundryToolbox / AddFoundryToolboxes", "MCP SDK"]
    for i, c in enumerate(cons):
        connect(cv, c, hub, a_side="bottom", b_side="top", ta=0.5, tb=c.cx / W, label=labels[i], label_size=15, sw=3, gap=4,
                color="#1e1e1e")
    mid = Chip("MCP over streamable HTTP + Microsoft Entra token, scope https://ai.azure.com/.default", theme="gray", size=15, fill="soft")
    mid.place(cv, (cons[0].cx + cons[1].cx) / 2 - mid.w / 2 + 120, cb + 60)

    # ---- tools panel
    ty = hub.bottom + 130
    with cv.panel(0, ty, title="13 tool types can sit behind the endpoint (as of 2026-11-03)",
                  sub="Add a description to every tool - it drives model tool selection and tool-search ranking",
                  theme="orange", style="dotted", w=W, pad=26, title_size=28, sub_size=16) as tp:
        tiles = [
            ("MCP server", "mcp", "mcp", "orange", None),
            ("Web search", "web_search", "globe", "orange", None),
            ("Azure AI Search", "azure_ai_search", "ai-search", "teal", None),
            ("Code interpreter", "code_interpreter", "code", "orange", None),
            ("File search", "file_search", "files", "teal", None),
            ("OpenAPI", "openapi", "api", "orange", None),
            ("Agent-to-agent (A2A)", "a2a (v1.0) or a2a_preview (v0.3)", "a2a", "green", None),
            ("Browser automation", "browser_automation", "browser", "orange", "ga"),
            ("Fabric IQ", "fabric_iq_preview", "fabric", "teal", "preview"),
            ("Work IQ", "work_iq_preview", "m365", "teal", "preview"),
            ("Tool search", "toolbox_search (toolbox only)", "search", "orange", None),
            ("Skills", "skill_reference + shell", "folder", "orange", "preview"),
            ("Reminder", "reminder_preview (hosted only)", "scheduler", "orange", "preview"),
        ]
        tw, th_, tg = 400, 78, 24
        for i, (lab, typ, ic, th, bd) in enumerate(tiles):
            rr, cc = divmod(i, 7)
            bx = tp.ix + cc * (tw + tg)
            by = tp.iy + 10 + rr * (th_ + 26)
            Box(tw, lab, sub=typ, h=th_, theme=th, icon=ic, icon_pos="left", icon_size=38, fill="hatch", size=18, sub_size=14).place(cv, bx, by)
            if bd:
                lab_txt = "GA" if bd == "ga" else "Preview"
                bw = metrics.line_width(lab_txt, 12) + 18
                draw_badge(cv, bx + tw - bw - 10, by - 11, bd, size=12)
        # legend in the 14th slot
        lx = tp.ix + 6 * (tw + tg)
        ly = tp.iy + 10 + (th_ + 26)
        legend(cv, lx, ly + 4, [("tools and actions", "orange")], size=14)
        legend(cv, lx, ly + 28, [("knowledge and IQ", "teal")], size=14)
        legend(cv, lx, ly + 52, [("agents", "green")], size=14)
    connect(cv, hub, tp, a_side="bottom", b_side="top", ta=0.5, tb=0.5, label="calls the downstream tool; credentials injected from the project connection; guardrails on inputs and outputs",
            label_size=15, sw=3, gap=4, color="#1e1e1e")

    # ---- direct-only
    dy = tp.bottom + 40
    with cv.panel(0, dy, title="Direct-only: attach these to the agent, not to a toolbox (7)", theme="gray", style="dashed", w=1984,
                  pad=24, title_size=24) as dp:
        flow = ChipFlow([
            Chip("Function calling (client-side execution)", theme="gray", size=15),
            Chip("Grounding with Bing", theme="gray", size=15),
            Chip("Computer use", theme="gray", size=15),
            Chip("Image generation", theme="gray", size=15),
            Chip("SharePoint", theme="gray", size=15),
            Chip("Fabric data agent", theme="gray", size=15),
            Chip("Azure Functions", theme="gray", size=15),
        ], 1984 - 48, gap=12)
        flow.place(cv, dp.ix, dp.iy)
    nt = Note(COL, "The Fabric data agent tool is scheduled for deprecation on 2026-11-06 (3 days from 2026-11-03). Use Fabric IQ instead - Fabric IQ can be added to a toolbox.",
              kind="gotcha", title="Date-sensitive (as of 2026-11-03)", src=[("What is Toolbox in Foundry?", learn("agents/concepts/toolbox-overview"))])
    nt.place(cv, 1984 + GAP, dy)
    return max(dp.bottom, nt.bottom)


# ====================================================================== band 3: end-to-end flow
def band_flow(cv, y):
    r, b = section_header(cv, 0, y, "End to end: from first tool to governed production",
                          sub="Eight steps; the numbers repeat on the cards. Steps 1-5 build and promote, steps 6-8 run and govern", size=32)
    y = b + 34
    steps = [
        ("Get access", "red", ["Developer gets Foundry User on the project", "Pick the project endpoint https://<account>.services.ai.azure.com/api/projects/<project>"]),
        ("Create project connections", "red", ["For authenticated tools: azd ai connection create ... or the portal", "The auth type is chosen here - never in agent code"]),
        ("Create a toolbox version", "orange", ["POST /toolboxes/{name}/versions with tools, optional skills, policies.rai_config and toolbox_search", "The first version becomes default automatically"]),
        ("Verify on the version endpoint", "orange", ["/toolboxes/{name}/versions/{v}/mcp?api-version=v1", "initialize, notifications/initialized, tools/list (non-empty), tools/call (no error; -32006 = consent needed)"]),
        ("Promote", "grape", ["PATCH /toolboxes/{name} with {\"default_version\": \"<v>\"}", "or azd ai toolbox publish <name> <version>"]),
        ("Attach the agent", "green", ["Connect to the consumer endpoint /toolboxes/{name}/mcp?api-version=v1", "Hosted: FoundryToolbox or AddFoundryToolboxes. Prompt agent: an mcp tool"]),
        ("Runtime call", "pink", ["Agent calls with its Entra token (+ x-agent-foundry-call-id)", "Toolbox applies guardrails to inputs and outputs, injects credentials (first OAuth use: -32006 + consent URL), calls the tool, returns the MCP result"]),
        ("Enforce and observe", "violet", ["The agent runtime enforces require_approval", "Traces and APIM logs show calls; new versions are staged, promoted or rolled back without touching agent code"]),
    ]
    cw, gx = 700, 66
    cards = [Card(cw, t, b_, theme=th, pad=20, fill="hatch", title_size=21) for t, th, b_ in steps]
    xs = [i * (cw + gx) for i in range(4)]
    r1 = cards[:4]
    r2 = cards[4:]
    h1 = max(c.h for c in r1)
    h2 = max(c.h for c in r2)
    for c, x in zip(r1, xs):
        c.place(cv, x, y + 20, h=h1)
    y2 = y + 20 + h1 + 90
    for c, x in zip(r2, xs):
        c.place(cv, x, y2, h=h2)
    for i, c in enumerate(cards):
        numbered_step(cv, c, i + 1, steps[i][1])
    for i in range(3):
        connect(cv, r1[i], r1[i + 1], a_side="right", b_side="left", gap=3, sw=3)
        connect(cv, r2[i], r2[i + 1], a_side="right", b_side="left", gap=3, sw=3)
    connect(cv, r1[3], r2[0], a_side="bottom", b_side="top", route="elbow", gap=4, sw=3, dash="dashed", bend=0.5)
    return y2 + h2


# ====================================================================== band 4: support matrix
def band_matrix(cv, y):
    r, b = section_header(cv, 0, y, "What goes in: the toolbox support matrix and the naming rules",
                          sub="Toolbox column = can be added to a toolbox; Direct = can be attached straight to an agent (as of 2026-11-03)", size=32)
    y = b + 30
    rows = [
        ["MCP (remote server)", CHECK, CHECK, CHECK, "Every surface; MCP tools need a unique server_label"],
        ["Web search", CHECK, CHECK, CHECK, "Bing Custom Search via custom_search_configuration {project_connection_id, instance_name}"],
        ["Azure AI Search", CHECK, CHECK, CHECK, "azure_ai_search.indexes[{index_name, project_connection_id}]"],
        ["Code interpreter", CHECK, CHECK, CHECK, "container: {type: auto}"],
        ["File search", CHECK, CHECK, CHECK, "vector_store_ids pinned, or omitted for dynamic (the portal requires them)"],
        ["OpenAPI", CHECK, CHECK, CROSS, "Spec inline; auth.type: project_connection"],
        ["Agent-to-agent (A2A)", CHECK, CHECK, CROSS, "a2a (a2a_version 1.0) or a2a_preview (v0.3 - what azd emits today)"],
        ["Browser automation", CHECK, CHECK, CROSS, "Not supported in network-isolated projects"],
        [("Fabric IQ (preview)", "teal"), CHECK, CHECK, CHECK, "Partial network support; see the network section"],
        [("Work IQ (preview)", "teal"), CHECK, CHECK, CHECK, "Not supported in network-isolated projects (toolbox page)"],
        ["Tool search", CHECK, CROSS, CHECK, "Toolbox only: toolbox_search directive"],
        [("Skills (preview)", "orange"), CHECK, PARTIAL, PARTIAL, "Direct only for prompt agents on the Microsoft Copilot harness; VS Code: docs disagree"],
        [("Reminder (preview)", "orange"), CHECK, CROSS, DASH, "Hosted agents only"],
        ["Function calling", CROSS, CHECK, DASH, "Client-side execution"],
        ["Grounding with Bing", CROSS, CHECK, DASH, "Web search with Bing custom config is the toolbox route"],
        ["Computer use", CROSS, CHECK, DASH, ""],
        ["Image generation", CROSS, CHECK, DASH, ""],
        ["SharePoint", CROSS, CHECK, DASH, ""],
        [("Fabric data agent", "yellow"), CROSS, CHECK, DASH, "Deprecation scheduled 2026-11-06 (as of 2026-11-03); use Fabric IQ"],
        ["Azure Functions", CROSS, CHECK, DASH, ""],
    ]
    t = Table([("Tool", 250), ("In toolbox", 100), ("Direct", 90), ("VS Code Foundry Toolkit", 150), ("Notes", 900)], rows,
              theme="orange", size=14, head_size=15, first_col_theme="orange", title="Toolbox support matrix (Learn: toolbox overview + create and manage)",
              title_size=22, align=["left", "center", "center", "center", "left"])
    t.place(cv, 0, y)

    rx = t.right + GAP
    rw = W - rx
    a = Card(rw, "One instance per type, unless named", [
        "At most one tool without a name field per built-in type: Web Search, Azure AI Search, Code Interpreter, File Search",
        "More instances need a unique name each; otherwise 400 invalid_payload: Multiple tools without identifiers found",
        "MCP tools need a unique server_label; toolbox_search does not count toward the limit",
        "Add a description to every tool - it drives model selection and tool-search ranking",
    ], theme="orange", icon="toolbox-icon", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    a.place(cv, rx, y)
    b2 = Card(rw, "Tool names on tools/list", [
        "MCP: {server_label}.{tool_name}      OpenAPI: {openapi_name}.{operationId}",
        "A2A: the agent name (or connection name)      Others: name, or a default such as web_search",
        "Each MCP tool carries _meta.tool_configuration, including require_approval",
    ], theme="orange", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    b2.place(cv, rx, a.bottom + 22)
    args = Table([("Tool", 150), ("tools/call arguments", 330), ("Citations in the result", 330)], [
        ["Azure AI Search", "{\"query\"}", "structuredContent.documents[] (title, url, id, score)"],
        ["File search", "{\"queries\":[...], \"vector_store_ids\":[...]?}", "content[].resource._meta (title, file_id, document_chunk_id, score)"],
        ["Code interpreter", "{\"code\"}", ""],
        ["Web search", "{\"search_query\"}", "resource._meta.annotations[] (type, url, title, start_index, end_index)"],
        ["A2A", "{\"message\":{\"parts\":[{\"kind\":\"text\",\"text\":...}]}}", ""],
        ["Work IQ", "{\"message\":{\"parts\":[{\"type\":\"text\",...}]}}", ""],
        ["Fabric IQ", "varies (typically {\"query\"})", "structuredContent.documents[]"],
        ["MCP", "tool-specific", ""],
    ], w=rw, theme="orange", size=13, head_size=14, title="tools/call shapes (verification table)", title_size=20)
    args.place(cv, rx, b2.bottom + 22)
    return max(t.bottom, args.bottom)


# ====================================================================== band 5: versions + tool search
def band_versions_search(cv, y):
    lw = 1476
    rx = lw + GAP
    # ---------------- versions
    with cv.panel(0, y, title="Versions and promotion", sub="Versions are immutable snapshots; the consumer endpoint follows default_version",
                  theme="orange", style="dotted", w=lw, pad=24, title_size=30, sub_size=16) as vp:
        fw = 320
        fgap = (lw - 48 - 4 * fw) / 3
        frames = [
            ("Create v1", ["v1"], "v1", False, "The first version becomes default_version automatically."),
            ("Create v2", ["v1", "v2"], "v1", True, "NOT auto-promoted. Consumers stay on v1; test v2 on /versions/2/mcp."),
            ("Promote v2", ["v1", "v2"], "v2", False, "PATCH default_version = 2 (or azd ai toolbox publish). Consumer-endpoint agents pick it up with no code change."),
            ("Roll back", ["v1", "v2"], "v1", False, "Promote an older version again: PATCH default_version = 1."),
        ]
        fy = vp.iy + 14
        caps = [f[4] for f in frames]
        cap_lines = [metrics.wrap_text(c, (fw - 36) * 0.965, 15) for c in caps]
        fh = 54 + 40 + 60 + 52 + max(len(cl) for cl in cap_lines) * 15 * metrics.line_ratio() + 24
        placed = []
        for i, (ttl, vers, dflt, dev, cap) in enumerate(frames):
            fx = vp.ix + i * (fw + fgap)
            cap_l = cap_lines[i]
            with cv.panel(fx, fy, title=f"{ttl}", theme="orange", style="solid", fill="soft", w=fw, h=fh, pad=16, title_size=22) as fp:
                bx = fp.ix + 8
                by = fp.iy + 40
                bxs = {}
                for j, v in enumerate(vers):
                    is_def = v == dflt
                    bb = Box(112, v, h=56, theme="orange", size=22, fill="solid" if is_def else "soft").place(cv, bx + j * 150, by)
                    bxs[v] = bb
                    if is_def:
                        Chip("default", theme="green", size=14, pad_y=3).place(cv, bb.x + (112 - 74) / 2, by - 36)
                if dev:
                    Chip("dev endpoint", theme="blue", size=14, pad_y=3).place(cv, bxs["v2"].x - 6, by + 66)
                cv.text(fp.ix, by + 112, "\n".join(cap_l), size=15, color="#1e1e1e")
            placed.append(fp)
            numbered(cv, fx, fy, i + 1, theme="orange", d=34, size=18)
        for i in range(3):
            connect(cv, placed[i], placed[i + 1], a_side="right", b_side="left", gap=2, sw=3)
        ry = max(p.bottom for p in placed) + 28
        rules = Card((lw - 48 - 24) / 2, "Rules", [
            "Every call to the create endpoint produces a new, immutable version",
            "Cannot delete the default version while other versions exist - promote another first",
            "Deleting the only remaining version removes the toolbox (azd needs --force)",
            "default_version cannot be empty; rollback = promote an older version",
            "azd ai toolbox add/skill/connection commands branch a NEW version from the latest (not the default) and never promote; use --from-version to branch",
        ], theme="orange", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
        tips = Card((lw - 48 - 24) / 2, "Tips and limits", [
            "Connect agents to the consumer endpoint; keep the version-specific endpoint for testing",
            "Keep server_label unique per agent even when switching versions",
            "The hosted-agent quickstart uses the versioned endpoint (TOOLBOX_ENDPOINT), so it needs no promotion",
            "Agent-side limits: 128 tools registered per agent, 1,000 versions per agent",
            "Learn documents no numeric limit for tools or versions per toolbox (as of 2026-11-03)",
        ], theme="orange", src=[("Limits, quotas and regions", learn("agents/concepts/limits-quotas-regions"))])
        row(cv, vp.ix, ry, [rules, tips], gap=24)
        dn = Note(lw - 48, "REST reference says POST /toolboxes/{name}:invoke_mcp invokes the latest version; the how-to pages say the /mcp consumer endpoint "
                           "always serves default_version. This canvas draws the how-to behaviour. The reminder-tool page also shows a different URL shape "
                           "(.../agents/toolboxes/<name>/mcp?version=1).", kind="warn", title="Docs disagree")
        dn.place(cv, vp.ix, max(rules.bottom, tips.bottom) + 22)

    # ---------------- tool search
    with cv.panel(rx, y, title="Tool search: hide the long tail, discover on demand", sub="Add {\"type\": \"toolbox_search\"} to a toolbox version; ranking is BM25",
                  theme="teal", style="dotted", w=lw, pad=24, title_size=30, sub_size=16) as tp:
        seq = Sequence(cv, tp.ix, tp.iy + 4, [("Agent / model", "green", "agent"), ("Toolbox endpoint", "orange", "toolbox-icon"),
                                              ("Downstream tool", "gray", "mcp")],
                       spacing=580, head_w=260, head_h=60, size=16, label_size=15)
        seq.msg(0, 1, "tools/list", num=1, note="returns only tool_search + call_tool (+ pinned and auto-pinned tools); all other toolbox tools are hidden")
        seq.msg(0, 1, "tool_search { query, limit }", num=2, note="limit defaults to 5, max 10; the model may call it several times per turn")
        y3 = seq.msg(1, 1, "rank every toolbox tool with BM25 over name + description + parameter info (+ additional_search_text)")
        numbered(cv, seq.actors[1][0] + 40, y3 - 16, 3, theme="orange", d=26, size=15)
        seq.msg(1, 0, "top matches - they stay callable for the rest of the turn", dash="dashed", num=4)
        seq.msg(0, 1, "call_tool { name, ... }", num=5)
        seq.msg(1, 2, "invoke the discovered tool", num=6)
        seq.msg(2, 1, "tool result", dash="dashed", num=7)
        seq.msg(1, 0, "MCP result", dash="dashed")
        sb = seq.end()
        cw = (lw - 48 - 2 * 24) / 3
        pin = Card(cw, "Pin", ["tool_configs.<tool>.pin: true keeps a tool in tools/list; \"*\" pins every tool of that entry", "Use for tools called on nearly every turn"], theme="teal")
        ctx = Card(cw, "Add context", ["additional_search_text adds your team's vocabulary to the ranking index", "Never shown to the model"], theme="teal")
        auto = Card(cw, "Auto-pin", ["Foundry tracks per-user call frequency and surfaces hot tools after a short warm-up", "Per-user; stale entries age out"], theme="teal")
        r_, b_ = row(cv, tp.ix, sb + 24, [pin, ctx, auto], gap=24)
        g = Card(lw - 48, "When and how", [
            "Use it when a toolbox has more than 10-15 tools or tasks need different subsets; add a description to every tool",
            "Mention tool_search in the system prompt; test on the version endpoint before promoting",
            "Tools added directly to the agent are unaffected. toolbox_search is a directive: not listed in tools/list, not counted in the unnamed-tool-per-type limit",
            "Troubleshoot: tool_search missing -> add toolbox_search and create a new version; no results -> improve descriptions; model never calls it -> add a system-prompt instruction",
        ], theme="teal", src=[("Tool search", learn("agents/how-to/tools/tool-search"))])
        g.place(cv, tp.ix, b_ + 22)
    return max(vp.bottom, tp.bottom)


# ====================================================================== band 6: create and manage
def band_manage(cv, y):
    r, b = section_header(cv, 0, y, "Create and manage: portal, SDKs, REST, azd and VS Code",
                          sub="Every surface can create versions and set the guardrail; promotion is a separate step on every surface", size=32)
    y = b + 30
    x1, x2, x3 = 0, COL + GAP, 2 * (COL + GAP)

    # ---- column 1: surfaces table, docs-disagree note, python
    ops = Table([("Operation", 330), ("Python", 100), ("REST", 90), (".NET", 90), ("JS", 80), ("azd", 90), ("Foundry Toolkit", 188)], [
        ["Toolbox update, list, get, delete", CHECK, CHECK, CHECK, CHECK, PARTIAL, CHECK],
        ["Toolbox version create", CHECK, CHECK, CHECK, CHECK, CHECK, CHECK],
        ["Version list, get, delete", CHECK, CHECK, CHECK, CHECK, PARTIAL, CROSS],
        ["Guardrail (RAI policy)", CHECK, CHECK, CHECK, CHECK, CHECK, PARTIAL],
    ], w=COL, theme="orange", size=14, head_size=15, first_col_theme="orange", title="Operations by surface", title_size=22,
        align=["left", "center", "center", "center", "center", "center", "center"])
    ops.place(cv, x1, y)
    n1 = Note(COL, "Learn's feature table lists azd as N/A for toolbox and version list, get and delete, yet azd ai toolbox list, show, versions list, delete and publish exist. "
                   "For Foundry Toolkit it says version list/get/delete = No (the UI shows the latest version only) and guardrails = yes, while the prose says guardrail "
                   "configuration is not yet available in the VS Code extension.", kind="warn", title="Docs disagree (partial marks)",
              src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    n1.place(cv, x1, ops.bottom + 24)
    py = Code(COL, [
        "pip install azure-ai-projects      # 2.3.0 or later for the toolbox + connection samples",
        "",
        "from azure.ai.projects import AIProjectClient",
        "from azure.ai.projects.models import (MCPToolboxTool, ToolSearchToolboxTool,",
        "                                      WebSearchToolboxTool)",
        "",
        "project.toolboxes.create_version(",
        "    name=..., description=...,",
        "    tools=[WebSearchToolboxTool(),",
        "           MCPToolboxTool(server_label=..., server_url=...,",
        "                          require_approval=\"never\",",
        "                          project_connection_id=...),",
        "           ToolSearchToolboxTool()])",
        "",
        "project.toolboxes.update(toolbox_name=..., default_version=...)   # promote",
        "# also: list_toolbox_versions, get_toolbox_version, delete_version",
    ], title="Python SDK (azure-ai-projects)", theme="orange", size=14,
        src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    py.place(cv, x1, n1.bottom + 24)
    sdk = Card(COL, "Other SDKs", [
        ".NET: Azure.AI.Projects 2.1.0-beta.4 (prerelease) + Azure.AI.Projects.Agents + Azure.AI.Extensions.OpenAI; projectClient.AgentAdministrationClient.GetAgentToolboxes()",
        "JavaScript: npm install @azure/ai-projects @azure/identity; project.toolboxes.createVersion(...)",
        "Java: no toolbox-creation API yet (MCP page: an API for creating toolboxes is not yet available)",
    ], theme="orange", icon="sdk", src=[("MCP tool", learn("agents/how-to/tools/model-context-protocol"))])
    sdk.place(cv, x1, py.bottom + 24)

    # ---- column 2: REST, azd, yaml
    rest = Table([("Method", 120), ("Route", 380), ("What it does", 468)], [
        ["GET", "/toolboxes", "List: limit 1-100 (default 20), order asc or desc by created_at, after/before cursors"],
        ["GET", "/toolboxes/{name}", "Get a toolbox"],
        ["PATCH", "/toolboxes/{name}", "Promote: body {\"default_version\": \"<id>\"} - required, cannot be empty"],
        ["DELETE", "/toolboxes/{name}", "Delete a toolbox"],
        ["GET", "/toolboxes/{name}/versions", "List versions"],
        ["POST", "/toolboxes/{name}/versions", "Create a version; provisions the toolbox if it does not exist yet"],
        ["GET, DELETE", "/toolboxes/{name}/versions/{version}", "Get or delete one version"],
        ["POST", "/toolboxes/{name}:invoke_mcp", "Invoke the latest version through its MCP endpoint (raw MCP request body)"],
    ], w=COL, theme="orange", size=14, head_size=15, first_col_theme="orange", title="REST: the Toolboxes reference group", title_size=22)
    rest.place(cv, x2, y)
    n2 = Note(COL, "All routes take ?api-version=v1 and a bearer token for scope https://ai.azure.com/.default.", kind="info", title="REST basics",
              src=[("REST: create toolbox version", learn("reference/rest/create-toolbox-version"))])
    n2.place(cv, x2, rest.bottom + 24)
    azd = Code(COL, [
        "azd ext install microsoft.foundry",
        "azd ai project set <endpoint>",
        "azd ai connection create <name> --kind <kind> --target <url> --auth-type <type>",
        "azd ai toolbox create <name> --from-file toolbox.yaml",
        "azd ai toolbox list | show | versions list | delete --force",
        "azd ai toolbox publish <name> <version>     # the only CLI path that promotes",
        "azd ai toolbox add connection | skill       # new version, never promoted",
    ], title="azd (Azure Developer CLI)", theme="orange", size=14, src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    azd.place(cv, x2, n2.bottom + 24)
    yml = Code(COL, [
        "description: ...",
        "connections:",
        "  - name: ...",
        "tools:",
        "  - type: web_search        # or code_interpreter, toolbox_search, azure_ai_search ...",
        "skills:",
        "  - name: ...               # version is optional",
        "policies:",
        "  raiConfig:",
        "    raiPolicyName: ...",
    ], title="toolbox.yaml (azd --from-file)", theme="orange", size=14)
    yml.place(cv, x2, azd.bottom + 24)
    azn = Card(COL, "azd notes", [
        "--kind: remote-tool, remote-a2a, cognitive-search, GroundingWithCustomSearch",
        "--auth-type: none, custom-keys, api-key, oauth2, user-entra-token, project-managed-identity, agentic-identity",
        "At least one of connections, skills or tools must be non-empty; the YAML never embeds credentials",
        "Declarative: an azure.ai.toolbox service in azure.yaml, deployed with azd deploy or azd up; the sample emits TOOLBOX_AGENT_TOOLS_MCP_ENDPOINT (a versioned endpoint)",
        "Minimum azd: 1.27.1 on the toolbox page (other pages say 1.25 and 1.36.0)",
    ], theme="orange", icon="azd", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    azn.place(cv, x2, yml.bottom + 24)

    # ---- column 3: data model, portal, VS Code, MCP server
    dm = Card(COL, "Data model", [
        "ToolboxObject: id, name, default_version (REST reference adds updated_at and versions.latest)",
        "ToolboxVersionObject: id, name, version, description, created_at (unix seconds), tools[], skills[], policies, metadata",
        "metadata: up to 16 key/value pairs; key up to 64 chars, value up to 512 chars",
        "policies.rai_config.rai_policy_name = the guardrail",
        "policies.invocations_moderation declares where request and response text lives (input/output content type json or text, response_mode non_streaming, streaming or both, input_paths, output_paths, stream_selectors) so content-safety guardrails can extract it for the invocations protocol",
    ], theme="orange", icon="cubes", src=[("REST: create toolbox version", learn("reference/rest/create-toolbox-version"))])
    dm.place(cv, x3, y)
    po = Card(COL, "Foundry portal", [
        "Browser-automation page: project -> Build > Tools > Create a toolbox -> name + description -> Tools > Add -> pick a tool -> Add tool -> connection details -> Connect -> Publish",
        "Reminder page: Build & customize > Toolboxes > + New -> + Add tool -> Built-in tools -> e.g. Reminder (preview) -> Add -> Save",
        "The toolbox details page shows the MCP endpoint to copy; a tool's details page shows its Project connection ID",
        "Guardrail selection lives under Guardrails (RAI policies)",
        "Portal File Search requires vector_store_ids; the dynamic override is API, SDK or azd only",
        "! Menu labels differ between pages - treat Build > Tools and Build & customize > Toolboxes as the same area",
    ], theme="orange", icon="foundry", src=[("Browser automation", learn("agents/how-to/tools/browser-automation")),
                                            ("Reminder tool", learn("agents/how-to/tools/reminder-tool"))])
    po.place(cv, x3, dm.bottom + 24)
    vs = Card(COL, "VS Code: Foundry Toolkit", [
        "Activity Bar -> Foundry Toolkit -> My Resources -> project -> Tools -> + Add Toolbox -> Build a Custom Toolbox (name, description, tools, Tool search checkbox) -> Publish; the first version is the default",
        "Toolboxes tab: Endpoint URL column (the consumer endpoint) and Scaffold code template (a hosted-agent sample wired to the toolbox)",
        "Developer Tools -> Agent Dev Tools -> Tool Catalog adds prebuilt skills",
    ], theme="blue", icon="vscode", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    vs.place(cv, x3, po.bottom + 24)
    mc = Card(COL, "Conversationally: Foundry MCP Server (preview)", [
        "Hosted at https://mcp.ai.azure.com; toolbox tools: toolbox_get, toolbox_version_get, toolbox_version_create, toolbox_update, toolbox_delete, toolbox_version_delete",
        "Read tools need Reader; write tools need Contributor",
    ], theme="orange", badge="preview", icon="mcp", src=[("Foundry MCP Server tools", learn("mcp/available-tools"))])
    mc.place(cv, x3, vs.bottom + 24)
    return max(sdk.bottom, azn.bottom, mc.bottom)


# ====================================================================== band 7: skills and private catalogs
def band_skills_catalogs(cv, y):
    r, b = section_header(cv, 0, y, "Skills and private catalogs",
                          sub="Skills (preview) ride the toolbox as MCP resources; both private catalogs (preview) are backed by Azure API Center", size=32)
    y = b + 30
    sk = Card(COL, "Skills in a toolbox (preview)", [
        "Tools define what an agent can do; skills define how it performs a task",
        "A skill is a folder with a required SKILL.md (front matter: name up to 64 chars, description up to 1,024 chars) plus optional scripts and assets; open Agent Skills format",
        "Versioned through the Skills API (header Foundry-Features: Skills=V1Preview); versions are immutable",
        "Attach: skills: [{type: skill_reference, name, version?}]; omit version to follow the skill's default_version; same Foundry project only",
        "Exposed as MCP resources skill://{name}; the client must support resources/list and resources/read",
        "Agent Framework .NET: AgentSkillsProviderBuilder().UseMcpSkills(mcpClient) - progressive disclosure",
    ], theme="orange", badge="preview", icon="folder", src=[("Skills", learn("agents/how-to/tools/skills"))])
    sh = Card(COL, "Skills through the shell tool", [
        "A prompt agent can use skills only through the shell tool",
        "{type: shell, name, environment: {type: container_auto, skills: [{type: skill_reference, skill_id, version: latest or N}], file_ids: [...]}}",
        "container_auto is recommended; container_reference expires after 20 min idle and is deleted 1 h after creation",
        "Up to 200 skills and up to 50 file_ids (mounted under /mnt/data)",
        "Runtimes: Python 3.11, Node.js 22.16.0, Java 17, PHP 8.2, Ruby 3.1, Go 1.23.2; non-interactive, no sudo, no outbound network",
        "! azd ai toolbox skill add does not populate environment.skills",
    ], theme="orange", badge="preview", icon="code", src=[("Skills with the shell tool", learn("agents/how-to/tools/skills-shell-tool"))])
    pc = Card(COL, "Two catalogs, one backing store", [
        "Private tools catalog (preview): register MCP servers as Azure API Center assets",
        "Private skill catalog (preview): register skills as API Center assets (title, summary, description, lifecycle, Git source URL)",
        "The API Center name becomes the catalog name in the Foundry registry filter",
        "Public side: the Foundry Tools Catalog (Add tool) lists more than 1,000 connectors and catalog MCP servers - see the MCP in Foundry canvas",
    ], theme="grape", badge="preview", icon="api-connections", src=[("Private tool catalog", learn("agents/how-to/private-tool-catalog")),
                                                                     ("Private skill catalog", learn("agents/how-to/private-skill-catalog"))])
    row(cv, 0, y, [sk, sh, pc], gap=GAP)
    ty = max(sk.bottom, sh.bottom, pc.bottom) + 34
    t = Table([("", 170), ("Private tool catalog (preview)", 915), ("Private skill catalog (preview)", 915)], [
        ["Backing store", "Azure API Center: register MCP servers as assets",
         "Azure API Center: register Skills as assets (title, summary, description, lifecycle, Source URL of a Git repo)"],
        ["Admin does", "Create the API Center; register the MCP server (Inventory > Assets > Register an asset > MCP server); optionally Governance > Authorization > Add configuration (API Key, OAuth or HTTP bearer), then server Details > Versions > Manage access (preview)",
         "Create the API Center; Inventory > Assets > + Register an asset > Skill; define Allowed tools (the APIs or MCP servers the skill may reach - the governance boundary for a skill); optionally Governance > AI Assessment > Skills tab (criteria: name, score range, pass threshold, weight); optionally sync from a Git repo"],
        ["Developer access", "RBAC: Azure API Center Data Reader (or an equivalent custom role)",
         "The same role, at the API Center resource or its parent resource group or subscription - a Foundry project role alone is not enough"],
        ["Shows in Foundry", "Portal Build > Tools; search or filter by the API Center name (catalog name = API Center name)",
         "Build > Tools > Skills > Browse skills > Registry filter = API Center name (not a separate list item)"],
        ["Gotchas", "Role assignments can take up to 24 hours to propagate; OAuth prompts repeat if the token expires; with the API Key scheme the key stored in Key Vault is not used automatically - developers provide the key when configuring the connection",
         "The same 24 h propagation; the wrong scope (project instead of API Center) hides the catalog; a private repo gives 'skill source can't be opened'"],
    ], w=W, theme="grape", size=14, head_size=16, first_col_theme="grape", title="Private tool catalog vs private skill catalog", title_size=22)
    t.place(cv, 0, ty)
    return t.bottom


# ====================================================================== band 8: governance
def self_msg(seq, cv, actor, text, n, theme):
    y = seq.msg(actor, actor, text)
    numbered(cv, seq.actors[actor][0] + 40, y - 16, n, theme=theme, d=26, size=15)
    return y


def band_governance(cv, y):
    r, b = section_header(cv, 0, y, "Governance: guardrails, the AI gateway and approvals",
                          sub="The toolbox applies guardrails and injects credentials; the agent runtime owns require_approval", size=32)
    y = b + 30
    sw = 1984
    with cv.panel(0, y, title="Anatomy of a governed tool call", sub="who does what between the agent runtime, the toolbox and the tool", theme="grape",
                  style="dotted", w=sw, pad=24, title_size=28, sub_size=16) as gp:
        seq = Sequence(cv, gp.ix + 80, gp.iy + 4, [("Agent runtime", "green", "agent"), ("Toolbox endpoint", "orange", "toolbox-icon"),
                                                   ("MCP server / tool", "gray", "mcp")], spacing=700, head_w=280, head_h=60, size=16, label_size=15)
        self_msg(seq, cv, 0, "enforces require_approval: mcp_approval_request -> user -> mcp_approval_response (same conversation)", 1, "green")
        seq.msg(0, 1, "tools/call - Entra token (scope https://ai.azure.com/.default); hosted agents add x-agent-foundry-call-id", num=2)
        self_msg(seq, cv, 1, "guardrail on the tool call (intervention point: Tool call, preview)", 3, "pink")
        self_msg(seq, cv, 1, "inject connection credentials, refresh tokens; first OAuth use returns -32006 + consent URL", 4, "red")
        seq.note(1, 2, "Optional: MCP tools created in the portal without managed OAuth are routed through the AI gateway (Azure API Management, preview): rate limits, IP restrictions, audit logging.", kind="info")
        seq.msg(1, 2, "call the downstream tool", num=5)
        seq.msg(2, 1, "tool result", dash="dashed")
        self_msg(seq, cv, 1, "guardrail on the tool response (intervention point: Tool response, preview)", 6, "pink")
        seq.msg(1, 0, "MCP result", dash="dashed", num=7)
        seq.note(0, 1, "The MCP endpoint does not block tools/call. Enforcement of require_approval is entirely the agent runtime's responsibility - a system-prompt instruction does not enforce approval.", kind="gotcha")
        sb = seq.end()
    rx = sw + GAP
    rw = W - rx
    g = Card(rw, "Guardrails on tool calls", [
        "Set policies.rai_config.rai_policy_name on a toolbox version (the policy name from Guardrails in the portal)",
        "Runs at the toolbox layer, independently of any model-level content filter",
        "Four intervention points: User input, Tool call (preview, agents only), Tool response (preview, agents only), Output",
        "An agent guardrail fully overrides the model's guardrail; default policy Microsoft.DefaultV2; agents block rather than only annotate",
        "Spotlighting and Groundedness do not apply to agents; Groundedness (preview) retires 2027-04-30 (as of 2026-11-03)",
        "Hosted agents also support network egress controls (preview) in the same RAI policy",
    ], theme="pink", icon="content-safety", src=[("Guardrails overview", learn("guardrails/guardrails-overview"))])
    g.place(cv, rx, y)
    ag = Card(rw, "AI gateway (Azure API Management)", [
        "Single governed entry for MCP tools: auth, rate limits, IP restrictions, audit logging - no change to MCP servers or agent code",
        "Only new MCP tools created in the portal that do not use managed OAuth are routed through it, at tool creation",
        "Policies are applied in the Azure portal: rate-limit-by-key, ip-filter, X-Correlation-Id, header removal, routing",
        "! Gateways support only MCP tools; they do not log tool traces; existing tools are not retrofitted",
    ], theme="grape", badge="preview", icon="apim", src=[("Govern tools with an AI gateway", learn("agents/how-to/tools/governance"))])
    ag.place(cv, rx, g.bottom + 24)
    ot = Card(rw, "Also governing", [
        "Versions give staged rollout and rollback; trace tool calls (trace-agent-setup); APIM logs show gateway traffic",
        "Connecting non-Foundry tools might incur costs, and data might be sent outside Foundry's compliance boundary",
    ], theme="gray", src=[("Tool best practices", learn("agents/concepts/tool-best-practice"))])
    ot.place(cv, rx, ag.bottom + 24)
    return max(gp.bottom, ot.bottom)


# ====================================================================== band 9: identity and network
def band_identity_network(cv, y):
    r, b = section_header(cv, 0, y, "Identity, authentication and network isolation",
                          sub="Auth is a property of the connection, never of agent code; the project's networking governs every toolbox call", size=32)
    y = b + 30
    x1, x2, x3 = 0, COL + GAP, 2 * (COL + GAP)
    # ---- column 1: two identities diagram + boundary cards
    with cv.panel(x1, y, title="Two identities in every tool call", theme="red", style="dotted", w=COL, pad=22, title_size=26) as ip:
        ag = Box(210, "Agent or MCP client", sub="agent identity", h=96, theme="green", icon="agent", icon_pos="left", icon_size=32, size=17).place(cv, ip.ix, ip.iy + 20)
        tb = Box(210, "Toolbox", sub="endpoint + connections", h=96, theme="orange", icon="toolbox-icon", icon_pos="left", icon_size=32, size=17).place(cv, ip.ix + 250, ip.iy + 20)
        td = Box(210, "Tool / data", sub="MCP, API, Fabric...", h=96, theme="gray", icon="globe", icon_pos="left", icon_size=32, size=17).place(cv, ip.ix + 500, ip.iy + 20)
        connect(cv, ag, tb, a_side="right", b_side="left", gap=3, sw=3, num=1, num_theme="red")
        connect(cv, tb, td, a_side="right", b_side="left", gap=3, sw=3, num=2, num_theme="red")
        bc = Card(COL - 44, None, [
            "# 1 Agent to toolbox",
            "Entra token, scope https://ai.azure.com/.default; the agent identity needs Foundry User on the project",
            "# 2 Tool to data",
            "Credentials come from the project connection: shared (key, project or agent identity) or per user (OAuth, user Entra token)",
        ], theme="red", fill="soft")
        bc.place(cv, ip.ix, ag.bottom + 24)
    rb = Table([("Principal", 290), ("Role on the Foundry project", 330), ("When", 348)], [
        ["Developer", "Foundry User", "always (creates and manages toolbox versions)"],
        ["Agent identity", "Foundry User", "required if you use a prompt agent"],
        ["End user", "Foundry User", "only for OAuth or UserEntraToken flows"],
        ["Creating a project connection", "Foundry Project Manager", "MCP page"],
        ["Consumers of OAuth-passthrough agents", "at least Foundry Agent Consumer", "user tenant must equal the project tenant"],
    ], w=COL, theme="red", size=14, head_size=15, first_col_theme="red", title="Who needs which role", title_size=22)
    rb.place(cv, x1, ip.bottom + 28)
    # ---- column 2: authType table
    at = Table([("authType on the connection", 250), ("Whose identity reaches the tool", 345), ("Typical use", 373)], [
        ["none", "nobody (anonymous)", "public servers; private servers relying on network isolation"],
        ["custom-keys", "the principal tied to the stored key", "key-based SaaS; secret stays in the connection - the agent never sees it"],
        ["project-managed-identity", "the Foundry project's managed identity", "shared project-level access; grant RBAC to the project identity"],
        ["agentic-identity", "the agent's own Entra agent identity", "per-agent audit and least privilege; a user token is rejected on purpose"],
        ["oauth2", "the user who completes OAuth consent", "per-user access; managed or custom OAuth; tokens stored and refreshed by the service"],
        ["user-entra-token", "the signed-in user, on-behalf-of", "limited Microsoft-owned tools (Fabric IQ, Foundry MCP, Azure DevOps MCP...)"],
    ], w=COL, theme="red", size=14, head_size=15, first_col_theme="red", title="Six auth types (the connection decides)", title_size=22)
    at.place(cv, x2, y)
    nn = Note(COL, "Verify per-user delegation with two users of different permissions - a successful call alone doesn't prove correct user delegation. "
                   "Direct MCP clients cannot use agent-blueprint sign-in or AgentOnBehalfOfUser; per-tool OAuth consent must be handled by the client.",
              kind="tip", title="Check delegation", src=[("Tool authentication", learn("agents/how-to/tools/tool-authentication"))])
    nn.place(cv, x2, at.bottom + 24)
    # ---- column 3: network rules
    nr = Card(COL, "Network rules", [
        "A toolbox is a logical container for tools and has no networking of its own; the hosting project's networking governs all access",
        "Agents reach the toolbox through the project's private endpoint; a project-level capability host is required (account level alone is insufficient: 'name or host unknown')",
        "Recreate file-search vector stores when a VNet is enabled (unless BYO) and again after disabling it",
        "Public-endpoint tools can be blocked with Azure Policy",
        "AI Search indexing through private endpoints: set the indexer executionEnvironment to Private, or the index stays silently empty",
        "! An AI gateway created from the portal for a private Foundry is automatically public - isolate it in the Azure portal",
    ], theme="indigo", icon="vnet", src=[("Network isolation for a toolbox", learn("agents/how-to/tools/toolbox-network-isolation")),
                                         ("Configure private link", learn("how-to/configure-private-link"))])
    nr.place(cv, x3, y)
    ny = max(rb.bottom, nn.bottom, nr.bottom) + 40
    t1 = Table([("Tool", 220), ("", 70), ("Network path (toolbox network page)", 678)], [
        ["MCP", CHECK, "through your VNet subnet"],
        ["Azure AI Search", CHECK, "through a private endpoint"],
        ["File search", CHECK, "through a private endpoint"],
        ["OpenAPI", CHECK, "through your VNet subnet"],
        ["A2A", CHECK, "through your VNet subnet"],
        ["Web search", CHECK, "relies on Microsoft-managed public endpoints"],
        ["Code interpreter", CHECK, "Microsoft backbone network"],
        ["Skills", CHECK, "depends on the tools the skill uses"],
        ["Fabric IQ", PARTIAL, "depends on the Fabric item and its networking configuration"],
        ["Work IQ", CROSS, "not supported in network-isolated projects (the Work IQ page describes a public HTTPS endpoint, so docs disagree)"],
        ["Browser automation", CROSS, "not supported"],
        ["Tool search", DASH, "not applicable"],
    ], w=COL, theme="indigo", size=14, head_size=15, first_col_theme="indigo", title="Network isolation by tool", title_size=22, align=["left", "center", "left"])
    t1.place(cv, x1, ny)
    t2 = Table([("Added by the authoritative matrix", 250), ("", 70), ("Path (configure-private-link)", 648)], [
        ["Function calling", CHECK, "Microsoft backbone network"],
        ["Bing Grounding", CHECK, "public endpoint"],
        ["SharePoint Grounding", CHECK, "public endpoint"],
        ["Foundry IQ (preview)", CHECK, "via MCP"],
        ["Azure Functions", CHECK, "through your VNet subnet"],
        ["Fabric IQ", PARTIAL, "partial via MCP: data agents need tenant- and workspace-level private link, ontologies tenant-level, Power BI semantic models are public access only"],
        ["Fabric data agent", CROSS, "the Fabric resource must have public network access; workspace-level private link unsupported"],
        ["Logic Apps", CROSS, "under development"],
        ["Browser automation", CROSS, "under development"],
        ["Computer use", CROSS, ""],
        ["Image generation", CROSS, ""],
    ], w=COL, theme="indigo", size=14, head_size=15, first_col_theme="indigo", title="Authoritative per-tool matrix: the extras", title_size=22, align=["left", "center", "left"])
    t2.place(cv, x2, ny)
    nt = Note(COL, "The authoritative matrix lives in configure-private-link (agent tools with network isolation) and applies to new Responses-API agents. "
                   "Templates in foundry-samples: Bicep 10-private-network-basic, 11-private-network-basic-vnet, 15-private-network-standard-agent-setup, 19-private-network-agent-tools; "
                   "Terraform 10-, 11-, 15a-, 15b-...-byovnet and 19-private-network-agent-setup-with-tools.",
              kind="info", title="Where the truth lives", src=[("Configure private link", learn("how-to/configure-private-link"))])
    nt.place(cv, x3, ny)
    n3 = Note(COL, "Work IQ: the toolbox page says not supported; the Work IQ page says public HTTPS https://workiq.svc.cloud.microsoft, with BYO-VNet traffic routed through the "
                   "project's single-tenant data proxy (not private).", kind="warn", title="Docs disagree", src=[("Work IQ tool", learn("agents/how-to/tools/work-iq"))])
    n3.place(cv, x3, nt.bottom + 24)
    return max(t1.bottom, t2.bottom, n3.bottom)


# ====================================================================== band 10: best practices and gotchas
def band_practices(cv, y):
    r, b = section_header(cv, 0, y, "Best practices and gotchas", sub="Assembled from the tool best-practice and troubleshooting pages", size=32)
    y = b + 30
    lw = 1476
    items = [
        "Connect agents to the consumer endpoint; test on the version endpoint; promote when ready.",
        "Give every tool a description; set a unique name or server_label for duplicates.",
        "Use tool search beyond about 10-15 tools; pin always-needed tools; add additional_search_text for your vocabulary; mention tool_search in the system prompt.",
        "Set require_approval: never unless the runtime can pause, collect and resume an approval; otherwise implement approval in the runtime.",
        "Keep credentials on the connection, never in agent code or prompts; use least-privilege tokens and rotate them.",
        "Treat MCP tool outputs and descriptions as untrusted (indirect prompt injection); validate structured outputs; require user approval for consequential actions; log approvals and tool calls.",
        "Describe each tool's purpose in the agent instructions; add decision rules for overlapping tools; use tool_choice (auto, required, none) for determinism.",
        "Check region and model support for each tool - both must say yes.",
        "Verify per-user delegation with two users of different permissions.",
        "A failing source can break enumeration for the whole toolbox (startup or readiness fails): fix or remove it, create a new version, promote it.",
    ]
    with cv.panel(0, y, title="Ten best practices", theme="green", style="dotted", w=lw, pad=24, title_size=28) as bp:
        cy = bp.iy
        for i, txt in enumerate(items, 1):
            lines = metrics.wrap_text(txt, (lw - 48 - 56) * 0.965, 17)
            h = len(lines) * 17 * metrics.line_ratio()
            numbered(cv, bp.ix + 18, cy + 13, i, theme="green", d=32, size=17)
            cv.text(bp.ix + 52, cy, "\n".join(lines), size=17, color="#1e1e1e")
            cy += max(h, 32) + 14
        cv.text(bp.ix, cy + 2, "Learn: Tool best practices", size=12, color=LINK, link=learn("agents/concepts/tool-best-practice"))
    rx = lw + GAP
    nw = (W - rx - 24) / 2
    g1 = Note(nw, "No ping (500) and no prompts/list (500; pass load_prompts=False). Non-streaming tools/call is unsupported (500) - always stream. "
                  "A newly created toolbox may return 404 'while enumerating tools' for a few seconds - retry after about 10 seconds.",
              kind="warn", title="Endpoint quirks", src=[("Create and manage a toolbox", learn("agents/how-to/tools/toolbox"))])
    g2 = Note(nw, "inputSchema must have properties (some MCP servers omit it, which breaks OpenAI). Definitions with anyOf, allOf or multi-type parameters trigger 'Invalid tool schema'.",
              kind="warn", title="Schemas")
    g3 = Note(nw, "An empty allowed_tools list means ALL tools, not zero. Names are case-sensitive; a misspelled name silently yields fewer tools.",
              kind="gotcha", title="allowed_tools")
    g4 = Note(nw, "Listing MCP or A2A tools returns zero tools if the connection credentials are invalid, because the toolbox must fetch manifests from the remote endpoint.",
              kind="gotcha", title="Invalid credentials")
    g5 = Note(nw, "A tool needs both region and model support. Docs disagree on code interpreter: the best-practice page says southcentralus and spaincentral are unsupported, the region table says yes. File search is unavailable in Italy North and Brazil South.",
              kind="info", title="Region and model gating", src=[("Limits, quotas and regions", learn("agents/concepts/limits-quotas-regions"))])
    g6 = Note(nw, "The platform reserves environment variables prefixed FOUNDRY_ and may overwrite them: use TOOLBOX_MCP_ENDPOINT, not FOUNDRY_TOOLBOX_ENDPOINT. Python hosted agents also set PYTHONNOUSERSITE=1.",
              kind="info", title="Env var gotcha")
    ya = y
    ra, ba = col(cv, rx, ya, [g1, g3, g5], gap=22)
    rb_, bb = col(cv, rx + nw + 24, ya, [g2, g4, g6], gap=22)
    return max(bp.bottom, ba, bb)


def band_sources(cv, y):
    sources(cv, 0, y, [
        ("What is Toolbox in Foundry?", learn("agents/concepts/toolbox-overview")),
        ("Create and manage a toolbox in Foundry", learn("agents/how-to/tools/toolbox")),
        ("Enable tool search in a toolbox", learn("agents/how-to/tools/tool-search")),
        ("Use a toolbox in a hosted agent", learn("agents/how-to/tools/use-toolbox-hosted-agent")),
        ("Toolbox quickstart", learn("agents/quickstarts/quickstart-toolbox-agent")),
        ("Network isolation for a toolbox", learn("agents/how-to/tools/toolbox-network-isolation")),
        ("Configure private link (agent tools with network isolation)", learn("how-to/configure-private-link")),
        ("Tool authentication", learn("agents/how-to/tools/tool-authentication")),
        ("Govern tools with an AI gateway", learn("agents/how-to/tools/governance")),
        ("Guardrails overview", learn("guardrails/guardrails-overview")),
        ("Skills (preview)", learn("agents/how-to/tools/skills")),
        ("Private tool catalog / private skill catalog", learn("agents/how-to/private-tool-catalog")),
        ("Tool best practices", learn("agents/concepts/tool-best-practice")),
        ("Foundry Blog: Introducing Toolboxes in Foundry (2026-04-22, not Learn)", "https://devblogs.microsoft.com/foundry/introducing-toolboxes-in-foundry/"),
    ], w=W, cols=3, title="Sources and further reading (Microsoft Learn, plus one Foundry Blog post)")


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Foundry Toolbox",
                                "One governed, versioned MCP endpoint for every tool an agent needs - build, discover, consume, govern",
                                icon="toolbox-icon", w=W)
    y = band_intro(cv, bottom + 50)
    y = band_arch(cv, y + 70)
    y = band_flow(cv, y + 80)
    y = band_matrix(cv, y + 80)
    y = band_versions_search(cv, y + 80)
    y = band_manage(cv, y + 80)
    y = band_skills_catalogs(cv, y + 80)
    y = band_governance(cv, y + 80)
    y = band_identity_network(cv, y + 80)
    y = band_practices(cv, y + 80)
    band_sources(cv, y + 70)
