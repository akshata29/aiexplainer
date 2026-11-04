"""Reference architecture: multi-agent / agent platform (orchestration patterns, A2A, MCP, Toolbox, memory, identity, CI/CD)."""
from __future__ import annotations

from generator.xd import *
from generator.xd.flows import _poly_point

META = dict(
    id="ra-multi-agent-platform",
    title="Reference architecture: multi-agent platform",
    section="3",
    order=5,
    description="Orchestrator and specialist agents on Foundry: the five orchestration patterns, A2A, MCP, Toolbox, memory, Entra agent identity, observability and CI/CD - with the Workflows retirement and the gotchas.",
    tags=["multi-agent", "orchestration", "a2a", "mcp", "toolbox", "agent identity"],
)

W = 3400
GAP = 48
COLW = (W - 3 * GAP) / 4          # four-column grid for the lower sections
AC = "azure/architecture/ai-ml/guide/ai-agent-design-patterns"
AC_SRC = ("AI agent orchestration patterns", learn(AC, base=""))
ASOF = "as of 2026-11-03"


# ====================================================================== helpers
def seg(cv, pts, *, num=None, label=None, theme="blue", t=0.5, pos=None, size=14, dx=0, dy=0, wrap=None,
        dash="solid", color=INK, sw=2, start_head=None, end_head="arrow", label_color=None):
    """Arrow along explicit points with an optional step badge and label that never collide."""
    arrow(cv, pts, dash=dash, color=color, sw=sw, start_head=start_head, end_head=end_head)
    (mx, my), horiz = _poly_point(pts, t)
    if num is not None:
        numbered(cv, mx, my, num, theme=theme, d=28, size=16)
    if label:
        txt = "\n".join(wrap_text(label, wrap, size)) if wrap else label
        tw, th = text_size(txt, size)
        pos = pos or ("above" if horiz else "right")
        clear = 18 if num is not None else 6
        if pos == "above":
            lx, ly = mx - tw / 2, my - th - clear
        elif pos == "below":
            lx, ly = mx - tw / 2, my + clear
        elif pos == "right":
            lx, ly = mx + clear + 2, my - th / 2
        else:
            lx, ly = mx - tw - clear - 2, my - th / 2
        cv.text(lx + dx, ly + dy, txt, size=size, color=label_color or INK,
                align="center" if "\n" in txt else "left", w=tw)
    return mx, my


def tag(cv, x, y, text, theme="violet", size=13):
    """Small pill (identity hop tags etc.). Returns the placed Chip."""
    return Chip(text, theme=theme, size=size, pad_x=8, pad_y=2, sw=1.5).place(cv, x, y)


def steps(cv, x, y, w, items, *, cols=3, size=15, theme="blue", gap=40):
    """Numbered step legend: items = [(n, title, text)]. Returns bottom y."""
    colw = (w - gap * (cols - 1)) / cols
    per = -(-len(items) // cols)
    bottom = y
    for c in range(cols):
        cy = y
        cx = x + c * (colw + gap)
        for n, title, text in items[c * per:(c + 1) * per]:
            numbered(cv, cx + 17, cy + 17, n, theme=theme, d=34, size=19)
            lines = wrap_text(text, colw - 56, size)
            t = cv.text(cx + 48, cy, title, size=size + 2, color=INK)
            body = cv.text(cx + 48, t.bottom + 1, "\n".join(lines), size=size, color="#343a40")
            cy = max(body.bottom, cy + 36) + 20
        bottom = max(bottom, cy - 20)
    return bottom


# ====================================================================== 1. summary strip
LAD_CARD_W = 300
LAD_GAP = 74
LAD_W = 3 * LAD_CARD_W + 2 * LAD_GAP + 48          # panel width of the complexity ladder
SW = (W - LAD_W - 3 * GAP) / 3                       # width of the three cards to its right


def summary_strip(cv, y):
    with cv.panel(0, y, title="Climb the complexity ladder only as far as you must",
                  sub="Architecture Center - AI agent orchestration patterns", theme="blue", style="dotted",
                  pad=24, title_size=24, sub_size=15, w=LAD_W) as lad:
        r1 = Card(LAD_CARD_W, "Direct model call", [
            "One model call with a well-crafted prompt; no agent logic or tools",
            "Classification, summarisation, translation, single-step tasks",
            "If prompt engineering can solve it, you don't need an agent",
        ], theme="blue", fill="hatch")
        r2 = Card(LAD_CARD_W, "Single agent + tools", [
            "One agent reasons and picks tools, knowledge and APIs; may loop",
            "\"Often the right default for enterprise use cases\"",
            "Simpler to debug and test; set iteration limits to stop tool-call loops",
        ], theme="green", fill="hatch")
        r3 = Card(LAD_CARD_W, "Multi-agent orchestration", [
            "Specialised agents coordinated by an orchestrator or a peer protocol",
            "Justified by prompt complexity, tool overload or security requirements",
            "Adds coordination overhead, latency and failure modes",
        ], theme="green", fill="cross")
        tall = max(r1.h, r2.h, r3.h)
        base = lad.iy + tall + 70
        placed, x = [], lad.ix
        for c, extra in zip((r1, r2, r3), (0, 35, 70)):
            c.place(cv, x, base - tall - extra, h=tall + extra)
            placed.append(c)
            x += LAD_CARD_W + LAD_GAP
        for a, b in zip(placed, placed[1:]):
            seg(cv, [(a.right + 6, base - 46), (b.x - 6, base - 46)], color="#1971c2", sw=3)
        cv.text(lad.ix, base + 10, "more coordination overhead, latency and failure modes ->", size=14, color=MUTED)
    return lad


def summary_cards(cv, y, h):
    x = LAD_W + GAP
    with cv.panel(x, y, title="Foundry primitives you compose", sub="patterns are technology-agnostic; Agent Framework implements all five",
                  theme="green", style="solid", fill="soft", pad=24, title_size=24, sub_size=15, w=SW, min_h=h) as pp:
        chips = ChipFlow([
            Chip("Prompt agents", theme="green", icon="agent", size=16),
            Chip("Hosted agents", theme="green", icon="container-apps", size=16),
            Chip("Toolbox", theme="orange", icon="toolbox", size=16),
            Chip("MCP", theme="orange", icon="mcp", size=16),
            Chip("A2A", theme="orange", icon="a2a", size=16),
            Chip("Memory (preview)", theme="teal", icon="cosmos", size=16),
            Chip("Control Plane", theme="grape", icon="dashboard", size=16),
            Chip("Entra Agent ID", theme="red", icon="conditional-access", size=16),
        ], SW - 48, gap=12)
        chips.place(cv, pp.ix, pp.iy + 4)
        n = Note(SW - 48, "Agent Service building blocks: Agent Runtime (prompt + hosted agents), Toolboxes, Models, Observability, Optimization (preview), Identity and security, Publishing.",
                 kind="info", size=15, src=[("Agent Service overview", learn("agents/overview"))])
        n.place(cv, pp.ix, chips.y + chips.h + 22)
    x += SW + GAP
    Card(SW, f"Foundry Workflows retire 2026-12-01 ({ASOF})", [
        "Preview. After that date the visual designer and in-portal workflow execution are unsupported",
        "YAML workflow definitions keep running only when deployed as a hosted agent; workflows are no longer a separate agent type",
        "Hosted agents aren't supported in the workflow designer",
        "Export the YAML first; migrate to Agent Framework (recommended), Logic Apps (low-code) or A2A (lightweight hand-offs)",
        "Connected Agents isn't in the new Foundry service: use A2A, Agent Framework or Logic Apps",
    ], theme="red", badge="retiring", icon="workflow", fill="cross",
        src=[("Workflows", learn("agents/concepts/workflow")), ("A2A tool", learn("agents/how-to/tools/agent-to-agent"))]).place(cv, x, y, h=h)
    x += SW + GAP
    Card(SW, "Every agent gets its own identity", [
        "New agents get an Entra agent identity under an agent identity blueprint; legacy agents share the project identity",
        "A new identity has NO permissions until granted; migrating changes the identity and role assignments do not transfer",
        "Hosted-agent sandboxes hold no blueprint credential: tokens come from a service outside the sandbox",
        "Entra applies: Conditional Access, sponsors/owners/expiry, sign-in and audit logs; no API keys on agent endpoints",
    ], theme="red", icon="managed-identity", fill="hatch",
        src=[("Entra agent identity", learn("agents/concepts/agent-identity")), ("Identity overview", learn("agents/concepts/identity-access-overview"))]).place(cv, x, y, h=h)


# ====================================================================== 2. main architecture diagram
def main_diagram(cv, y0):
    CH_W = 290
    P1_W = CH_W + 44
    P2_X = P1_W + 150
    ORCH_W, ARW, SPB_W = 520, 210, 420
    SP_W = SPB_W + 40
    P2_W = ORCH_W + ARW + SP_W + 44
    P3_X = P2_X + P2_W + 130
    P3_W = 930
    P7_X = P3_X + P3_W + 70
    P7_W = W - P7_X

    # ---------------------------------------------------------------- P2: agent layer
    with cv.panel(P2_X, y0, title="Agent layer", sub="orchestration code runs in the orchestrator: Agent Framework, A2A calls or Workflows (retiring)",
                  theme="green", style="dotted", pad=22, title_size=26, sub_size=14, w=P2_W) as p2:
        orch = Card(ORCH_W, "Orchestrator agent", [
            "A prompt agent, or a hosted agent running Microsoft Agent Framework",
            "Loads memory, calls the model to plan and route",
            "Invokes specialists and tools; validates and aggregates their output",
            "Persists state and task progress in a durable store",
        ], theme="green", icon="agent", fill="hatch", src=[AC_SRC])
        orch.place(cv, p2.ix, p2.iy)
        sx = p2.ix + ORCH_W + ARW
        with cv.panel(sx, p2.iy, title="Specialist agents", sub="narrow prompt, own tools, own identity", theme="green", style="dashed",
                      fill="soft", pad=20, title_size=22, sub_size=14, w=SP_W) as sp:
            sp1 = Box(SPB_W, "Prompt agents", sub="declarative: instructions + model + tools", theme="green", fill="hatch",
                      icon="agent", icon_pos="left", h=84)
            sp1.place(cv, sp.ix, sp.iy)
            sp2 = Box(SPB_W, "Hosted agents", sub="your code: Agent Framework, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK or custom",
                      theme="green", fill="hatch", icon="container-apps", icon_pos="left")
            sp2.place(cv, sp.ix, sp1.bottom + 16)
        with cv.panel(sx, sp.bottom + 24, title="Direct-only tools", sub="cannot be added to a toolbox", theme="orange", style="dashed",
                      fill="none", pad=18, title_size=20, sub_size=14, w=SP_W) as dt:
            ChipFlow(["Function calling", "Bing grounding", "Computer use", "Image generation", "SharePoint", "Fabric data agent",
                      "Azure Functions"], SP_W - 36, theme="orange", size=14, fill="soft", dash="dashed", gap=8).place(cv, dt.ix, dt.iy)
        by = orch.bottom + 112
        models = Box(250, "Models", sub="Foundry deployments; every agent calls them, optionally behind the AI gateway", theme="blue",
                     fill="hatch", icon="openai", icon_pos="left")
        memory = Box(250, "Memory stores (preview)", sub="user profile, chat summary, procedural; no VNet support", theme="teal", fill="hatch")
        hh = max(models.h, memory.h)
        models.place(cv, p2.ix, by, h=hh)
        memory.place(cv, p2.ix + 270, by, h=hh)
        conv = Box(ORCH_W, "Conversations / sessions", sub="conversation state and hosted-agent sessions", theme="cyan", fill="hatch")
        conv.place(cv, p2.ix, by + hh + 20)
        cv.text(p2.ix, conv.bottom + 26, "Hosted-agent endpoint protocols", size=16, color="#2b8a3e")
        ChipFlow(["Responses", "Invocations", "Invocations (WebSocket)", "Activity (Teams / M365)", "A2A"], ORCH_W, theme="green",
                 size=14, fill="soft", gap=8).place(cv, p2.ix, conv.bottom + 54)
        Note(SP_W, "Hosted agents run in a per-session VM-isolated sandbox with persistent $HOME and /files, scale to zero and resume with state.",
             kind="info", size=14).place(cv, sx, dt.bottom + 24)

    # ---------------------------------------------------------------- P3: tool layer
    with cv.panel(P3_X, y0, title="Tool layer", sub="one governed MCP endpoint in front of the tools", theme="orange", style="dotted",
                  pad=22, title_size=26, sub_size=14, w=P3_W) as p3:
        iw = P3_W - 44
        with cv.panel(p3.ix, p3.iy, title="Toolbox", sub="{project_endpoint}/toolboxes/{name}/mcp?api-version=v1  -  always serves the default version",
                      theme="orange", style="solid", fill="soft", pad=20, title_size=24, sub_size=14, w=iw) as tbx:
            items = [Chip(t, theme="orange", size=15) for t in (
                "MCP", "Web search", "Azure AI Search", "Code interpreter", "File search", "OpenAPI", "A2A", "Browser automation",
                "Fabric IQ (preview)", "Work IQ (preview)", "Skills (preview)", "Reminder")]
            items += [Chip("tool_search", theme="gray", size=15, fill="soft"), Chip("call_tool", theme="gray", size=15, fill="soft")]
            cf = ChipFlow(items, iw - 40, gap=10)
            cf.place(cv, tbx.ix, tbx.iy + 2)
            cf2 = ChipFlow([
                Chip("Guardrails screen every tool input and output", theme="pink", size=14, fill="soft"),
                Chip("Auth lives on the project connection, not in agent code", theme="red", size=14, fill="soft"),
                Chip("Versions: promote to default, no agent redeploy", theme="violet", size=14, fill="soft"),
            ], iw - 40, gap=10)
            cf2.place(cv, tbx.ix, cf.y + cf.h + 16)
        my = tbx.bottom + 92
        with cv.panel(p3.ix, my, title="MCP servers behind the Toolbox", theme="orange", style="dashed", fill="none", pad=18,
                      title_size=22, w=570) as mcp:
            m1 = Box(534, "Public MCP server", sub="remote endpoint; descriptions and results are untrusted input", theme="orange",
                     fill="hatch", icon="mcp", icon_pos="left", h=74)
            m1.place(cv, mcp.ix, mcp.iy)
            m2 = Box(534, "Private MCP server", sub="Container Apps, internal-only ingress, dedicated MCP subnet",
                     theme="orange", fill="hatch", icon="container-apps", icon_pos="left", h=74)
            m2.place(cv, mcp.ix, m1.bottom + 12)
            m3 = Box(534, "Managed MCP servers (preview)", sub="connector namespaces: 1,000+ connectors, OAuth2 only",
                     theme="orange", fill="hatch", icon="api-connections", icon_pos="left", h=74)
            m3.place(cv, mcp.ix, m2.bottom + 12)
            m4 = Box(534, "Private tool catalog (preview)", sub="Azure API Center; found at Build > Tools", theme="orange", fill="hatch",
                     icon="apim", icon_pos="left", h=74)
            m4.place(cv, mcp.ix, m3.bottom + 12)
        kb = Box(iw - 570 - 28, "Knowledge and data backends", sub="Foundry IQ knowledge base, AI Search, Fabric IQ, Work IQ - per-user permissions kept when the tool is delegated",
                 theme="teal", fill="hatch", icon="ai-search", icon_pos="top")
        kb.place(cv, mcp.right + 28, my, h=mcp.h)
        seg(cv, [(mcp.cx - 140, tbx.bottom + 6), (mcp.cx - 140, mcp.y - 6)], num=6, theme="orange")
        seg(cv, [(kb.cx, tbx.bottom + 6), (kb.cx, kb.y - 6)])

    rowA = max(p2.bottom, p3.bottom)

    # ---------------------------------------------------------------- guardrails band + foundation
    gy = rowA + 30
    gr = Box(P3_X + P3_W - P2_X, "Guardrails screen model input and output, and every toolbox tool input and output (Architecture Center: also at user input and final output)",
             theme="pink", fill="hatch", h=70, size=18, icon="content-safety", icon_pos="left")
    gr.place(cv, P2_X, gy)
    numbered(cv, P2_X - 22, gy + 35, 7, theme="pink", d=34, size=19)

    fy = gr.bottom + 30
    with cv.panel(0, fy, title="Foundation", sub="what every agent runs on", theme="gray", style="dotted", pad=22, title_size=26,
                  sub_size=14, w=P3_X + P3_W) as fd:
        fw = (P3_X + P3_W - 44 - 5 * 16) / 6
        cells = [
            Box(fw, "Foundry resource + project", sub="governance boundary; deployments live on the resource", theme="blue", fill="hatch", icon="foundry", icon_pos="top"),
            Box(fw, "Project managed identity", sub="platform infra operations, e.g. ACR Container Registry Repository Reader", theme="red", fill="hatch", icon="managed-identity", icon_pos="top"),
            Box(fw, "Agent identity", sub="blueprint + identity per agent; no permissions until granted", theme="red", fill="hatch", icon="identity-governance", icon_pos="top"),
            Box(fw, "Application Insights + Log Analytics", sub="spans, traces and logs", theme="violet", fill="hatch", icon="app-insights", icon_pos="top"),
            Box(fw, "Azure Container Registry", sub="hosted-agent container images", theme="cyan", fill="hatch", icon="acr", icon_pos="top"),
            Box(fw, "VNet / private endpoints", sub="network isolation for the project", theme="indigo", fill="hatch", icon="vnet", icon_pos="top"),
        ]
        row(cv, fd.ix, fd.iy, cells, gap=16)
    total_bottom = fd.bottom

    # ---------------------------------------------------------------- P1: channels (placed last so it can match the row height)
    with cv.panel(0, y0, title="Channels", sub="how callers reach an agent", theme="gray", style="dotted", pad=22, title_size=26,
                  sub_size=14, w=P1_W, min_h=rowA - y0) as p1:
        cy = p1.iy
        for lab, sub, ic in (("Web / app", "Responses API", "app"), ("Teams / M365", "Activity protocol", "teams"),
                             ("Other agents", "A2A protocol", "a2a"), ("MCP clients", "any MCP runtime -> Toolbox", "mcp"),
                             ("Routines / triggers", "timer, recurring, event", "scheduler")):
            b = Box(CH_W, lab, sub=sub, theme="gray", fill="hatch", icon=ic, icon_pos="left", h=88)
            b.place(cv, p1.ix, cy)
            cy += b.h + 14
        Note(CH_W, "Callers present an Entra token (audience https://ai.azure.com) and need Foundry Agent Consumer or Foundry User. No API keys on agent endpoints.",
             kind="key", size=14, src=[("Endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))]).place(cv, p1.ix, cy + 8)

    # ---------------------------------------------------------------- P7: govern and operate
    with cv.panel(P7_X, y0, title="Govern and operate", sub="platform controls shared by every agent", theme="grape", style="dotted",
                  pad=22, title_size=26, sub_size=14, w=P7_W, min_h=total_bottom - y0) as p7:
        gw = P7_W - 44
        gov = [
            ("Control Plane", "Operate panes: Overview, Assets, Compliance; Quota under Manage", "grape", "dashboard"),
            ("AI gateway (API Management)", "prerequisite for advanced Control Plane governance", "grape", "apim"),
            ("Entra Agent ID", "Conditional Access, sponsors, expiry, sign-in and audit logs", "red", "conditional-access"),
            ("Defender, Purview, Entra", "security, compliance and identity integrations", "red", "defender"),
            ("Tracing + continuous evaluation", "spans to Application Insights; AI Red Teaming", "violet", "monitor"),
            ("CI/CD pipeline (azd)", "azd provision then deploy, with an eval gate", "gray", "azd"),
        ]
        bh_ = (total_bottom - p7.iy - 22 - 5 * 16) / 6
        gy2 = p7.iy
        for lab, sub, th, ic in gov:
            b = Box(gw, lab, sub=sub, theme=th, fill="hatch", icon=ic, icon_pos="left", h=bh_)
            b.place(cv, p7.ix, gy2)
            gy2 += b.h + 16

    # ---------------------------------------------------------------- flow arrows
    # 1 channels -> orchestrator
    seg(cv, [(p1.right + 6, orch.y + 52), (orch.x - 6, orch.y + 52)], num=1, theme="blue")
    tag(cv, p1.right + 22, orch.y + 20, "H1")
    # 9 response back to channels
    seg(cv, [(orch.x - 6, orch.bottom - 44), (p1.right + 6, orch.bottom - 44)], num=9, theme="blue", dash="dashed",
        label="response", pos="below")
    # 4 orchestrator -> specialists (three ways) + 8 return
    x1, x2 = orch.right + 6, sp.x - 6
    ys = [orch.y + 0.16 * orch.h, orch.y + 0.36 * orch.h, orch.y + 0.56 * orch.h]
    seg(cv, [(x1, ys[0]), (x2, ys[0])], num=4, theme="green", label="in-process")
    seg(cv, [(x1, ys[1]), (x2, ys[1])], label="A2A tool")
    seg(cv, [(x1, ys[2]), (x2, ys[2])], label="Workflow (retiring)", dash="dashed", color="#e03131", label_color="#c92a2a")
    seg(cv, [(x2, orch.y + 0.86 * orch.h), (x1, orch.y + 0.86 * orch.h)], num=8, theme="green", dash="dashed", label="results up", pos="below")
    # 2 / 3 orchestrator -> memory / models
    seg(cv, [(models.cx, orch.bottom + 6), (models.cx, models.y - 6)], num=3, theme="blue", label="plan / route", pos="right", wrap=None)
    seg(cv, [(memory.cx, orch.bottom + 6), (memory.cx, memory.y - 6)], num=2, theme="teal", label="memory search", pos="right")
    # 5 specialists -> toolbox
    yy = y0 + 150
    seg(cv, [(sp.right + 6, yy), (p3.x + 14, yy)], num=5, theme="orange", label="Toolbox endpoint", dash="solid", wrap=None)
    tag(cv, sp.right + 20, yy + 20, "H2")
    tag(cv, mcp.cx - 110, tbx.bottom + 24, "H3")
    tag(cv, kb.cx - 70, tbx.bottom + 24, "H4")
    return p2, p3, total_bottom, (P2_X, P3_X + P3_W)


# ====================================================================== 3. orchestration patterns
PGAP = 40
PW = (W - 4 * PGAP) / 5          # width of one pattern panel
DH = 318                         # height reserved for each mini-diagram


def _cap(cv, x, y, w, text, size=14, color=MUTED, align="center"):
    return cv.text(x, y, "\n".join(wrap_text(text, w, size)), size=size, color=color, align=align, w=w)


def d_sequential(cv, x, y, w):
    io, bw, bh = 88, 104, 58
    gap = (w - 2 * io - 3 * bw) / 4
    cy = y + 62
    _cap(cv, x, y, w, "order is predefined - \"isn't a choice given to agents\"")
    chain = [Box(io, "Input", theme="gray", h=bh, size=16, fill="hatch").place(cv, x, cy)]
    px = x + io + gap
    for i in range(3):
        chain.append(Box(bw, f"Agent {i + 1}", theme="green", h=bh, size=17, fill="hatch").place(cv, px, cy))
        px += bw + gap
    chain.append(Box(io, "Output", theme="gray", h=bh, size=16, fill="hatch").place(cv, px, cy))
    for a, b in zip(chain, chain[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=2.5)
    ag = chain[1:4]
    bar = Box(ag[2].right - ag[0].x, "common state spans the agents", theme="teal", h=48, size=16, fill="hatch")
    bar.place(cv, ag[0].x, cy + bh + 52)
    for a in ag:
        connect(cv, a, bar, a_side="bottom", b_side="top", ta=0.5, tb=(a.cx - bar.x) / bar.w, dash="dotted", end_head=None, gap=2)
    _cap(cv, x, bar.bottom + 24, w, "agents see the previous agent's output; resembles Pipes and Filters")


def d_concurrent(cv, x, y, w):
    aw, ah = 136, 52
    stack = 3 * ah + 2 * 16
    top = y + 40
    _cap(cv, x, y, w, "same input to every agent, results gathered")
    init = Box(116, "Initiator", theme="grape", h=64, size=17, fill="hatch").place(cv, x, top + (stack - 64) / 2)
    coll = Box(116, "Collector", theme="grape", h=64, size=17, fill="hatch").place(cv, x + w - 116, top + (stack - 64) / 2)
    ags = [Box(aw, f"Agent {c}", theme="green", h=ah, size=17, fill="hatch").place(cv, x + (w - aw) / 2, top + i * (ah + 16))
           for i, c in enumerate("ABC")]
    for a in ags:
        connect(cv, init, a, a_side="right", b_side="left", route="elbow", sw=2.5)
        connect(cv, a, coll, a_side="right", b_side="left", route="elbow", sw=2.5)
    _cap(cv, x, top + stack + 22, w, "aggregation: vote or majority, weighted merge, LLM-synthesised summary - or none")


def d_group_chat(cv, x, y, w):
    mgr = Box(170, "Chat manager", theme="grape", h=50, size=17, fill="hatch").place(cv, x + 30, y)
    hum = Box(210, "Human", sub="participant, observer or manager", theme="gray", h=60, size=16, sub_size=13, fill="hatch", dash="dashed").place(cv, x + w - 210, y - 4)
    bar = Box(w, "shared, accumulating thread", theme="teal", h=44, size=17, fill="hatch").place(cv, x, y + 96)
    connect(cv, mgr, bar, a_side="bottom", b_side="top", ta=0.5, tb=(mgr.cx - bar.x) / bar.w, label="turn order", label_size=14, label_pos="right", gap=2)
    connect(cv, hum, bar, a_side="bottom", b_side="top", ta=0.5, tb=(hum.cx - bar.x) / bar.w, dash="dashed", gap=2)
    aw = 128
    gap = (w - 3 * aw) / 2
    for i in range(3):
        a = Box(aw, f"Agent {'ABC'[i]}", theme="green", h=48, size=17, fill="hatch").place(cv, x + i * (aw + gap), bar.bottom + 62)
        connect(cv, bar, a, a_side="bottom", b_side="top", ta=(a.cx - bar.x) / bar.w, tb=0.5, start_head="arrow", end_head="arrow", gap=2)
    my = bar.bottom + 62 + 48 + 30
    mk = Box(120, "Maker", theme="green", h=44, size=16, fill="hatch").place(cv, x, my)
    ck = Box(120, "Checker", theme="green", h=44, size=16, fill="hatch").place(cv, x + 120 + 120, my)
    connect(cv, mk, ck, a_side="right", b_side="left", label="proposal", label_size=13, gap=3, ta=0.3, tb=0.3)
    connect(cv, ck, mk, a_side="left", b_side="right", dash="dashed", label="feedback", label_size=13, label_pos="below", gap=3, ta=0.7, tb=0.7)
    cv.text(x + 120 + 120 + 120 + 16, my - 2, "\n".join(wrap_text("maker-checker loop (a group-chat variant): cap the iterations and add a fallback", w - 392, 13)), size=13, color=MUTED)


def d_handoff(cv, x, y, w):
    _cap(cv, x, y, w, "one active agent at a time; full control transfers")
    top = y + 44
    tri = Box(140, "Triage agent", theme="green", h=70, size=17, fill="hatch").place(cv, x, top + 74)
    sw_, sh = 168, 54
    names = ["Technical infrastructure", "Financial resolution", "Account access"]
    spec = []
    for i, nme in enumerate(names):
        spec.append(Box(sw_, nme, theme="green", h=sh, size=15, fill="hatch").place(cv, x + 236, top + i * (sh + 20)))
    hum = Box(92, "Human", theme="gray", h=70, size=16, fill="hatch", dash="dashed").place(cv, x + w - 92, top + 74)
    for i, s in enumerate(spec):
        active = i == 1
        connect(cv, tri, s, a_side="right", b_side="left", route="elbow", dash="solid" if active else "dashed", sw=3 if active else 1.5)
        connect(cv, s, hum, a_side="right", b_side="left", route="elbow", dash="dashed", sw=1.5)
    _cap(cv, x + 140, top + 3 * (sh + 20) + 4, w - 140, "agents decide when to transfer - or escalate to a human", size=13)


def d_magentic(cv, x, y, w):
    mgr = Box(190, "Manager agent", theme="grape", h=58, size=17, fill="hatch").place(cv, x + 10, y + 12)
    led = Box(250, "Task ledger", sub="goals and subgoals, adapted as work proceeds", theme="teal", h=78, size=17, sub_size=13, fill="hatch").place(cv, x + w - 250, y)
    connect(cv, mgr, led, a_side="right", b_side="left", start_head="arrow", end_head="arrow", label="build / adapt", label_size=13, ta=0.5, tb=0.45)
    aw = 168
    gap = (w - 3 * aw) / 2
    ay = y + 176
    bus = ay - 34
    ags = []
    for i in range(3):
        ags.append(Box(aw, f"Agent {'ABC'[i]}", sub="tools that change systems", theme="green", h=62, size=17, sub_size=13, fill="hatch").place(cv, x + i * (aw + gap), ay))
    arrow(cv, [(mgr.cx, mgr.bottom + 4), (mgr.cx, bus)], end_head=None, sw=2)
    arrow(cv, [(ags[0].cx, bus), (ags[2].cx, bus)], end_head=None, sw=2)
    for a in ags:
        arrow(cv, [(a.cx, bus), (a.cx, a.y - 4)], sw=2)
    arrow(cv, [(led.cx + 60, ay - 4), (led.cx + 60, led.bottom + 4)], dash="dashed", sw=2, color="#2b8a3e")
    cv.text(led.cx + 60 - 150, y + 108, "evaluate goal loop", size=13, color=MUTED)
    _cap(cv, x, ay + 62 + 22, w, "human-reviewable plan before or after execution", size=13)


PATTERNS = [
    ("Sequential", "pipeline, prompt chaining, linear delegation", d_sequential,
     "Linear: each agent processes the previous agent's output. The order is deterministic and predefined; a common state spans the agents.",
     "Law-firm contract generation: template selection, clause customisation, regulatory compliance, risk assessment."),
    ("Concurrent", "parallel, fan-out / fan-in, scatter-gather, map-reduce", d_concurrent,
     "Parallel: agents work independently on the same input; an initiator and a collector. Agent selection is deterministic or dynamic.",
     "Stock analysis: fundamental, technical, sentiment and ESG agents."),
    ("Group chat", "roundtable, collaborative, multi-agent debate, council", d_group_chat,
     "Conversational: shared accumulating thread; the chat manager controls turn order; humans can take part. Agents are typically read-only (no tools that change systems).",
     "Park-proposal review: community engagement, environmental planning, budget and operations."),
    ("Handoff", "routing, triage, transfer, dispatch, delegation", d_handoff,
     "Dynamic delegation: one active agent at a time, full control transfers, and agents decide when to transfer.",
     "Telecom support: triage, then technical infrastructure, financial resolution or account access, then a human."),
    ("Magentic", "dynamic orchestration, task-ledger-based, adaptive planning", d_magentic,
     "Plan, build, execute: a manager agent builds and adapts a task ledger, invokes agents and runs an \"evaluate goal loop\". Agents typically have tools that change external systems. Extension of group chat.",
     "SRE incident response: manager plus diagnostics, infrastructure, rollback and communication agents."),
]


def _para_h(w, text, size=15):
    return len(wrap_text(text, w, size)) * size * 1.25


def patterns_section(cv, y):
    section_header(cv, 0, y, "Five orchestration patterns - drawn from the documented structure",
                   sub=f"Architecture Center names five; Microsoft Agent Framework implements all five, with human-in-the-loop via tool approval and request info  |  {ASOF}", size=34, w=W)
    legend(cv, W - 1480, y + 12, [("worker agent", "green"), ("coordinator / manager", "grape"), ("shared state, thread, ledger", "teal"), ("human, input, output", "gray")])
    y += 110
    inner = PW - 40
    need = 0
    for _, _, _, coord, ex in PATTERNS:
        need = max(need, _para_h(inner, coord) + _para_h(inner, ex) + 2 * 22 + 26)
    ph = 24 + 44 + 28 + DH + 16 + need + 20
    for i, (name, aka, drawer, coord, ex) in enumerate(PATTERNS):
        px = i * (PW + PGAP)
        with cv.panel(px, y, title=name, sub=aka, theme="green", style="dashed", fill="soft", pad=20, title_size=30, sub_size=14, w=PW, min_h=ph) as pnl:
            drawer(cv, pnl.ix, pnl.iy + 6, inner)
            ty = pnl.iy + 6 + DH + 14
            cv.text(pnl.ix, ty, "How it coordinates", size=16, color="#2b8a3e")
            t1 = cv.text(pnl.ix, ty + 22, "\n".join(wrap_text(coord, inner, 15)), size=15, color=INK)
            cv.text(pnl.ix, t1.bottom + 12, "Architecture Center example", size=16, color="#2b8a3e")
            cv.text(pnl.ix, t1.bottom + 34, "\n".join(wrap_text(ex, inner, 15)), size=15, color="#343a40")
    y += ph + 50
    return y


QUICK = [
    ("Can a direct model call, or one agent with tools, do the job?", "Stop here: don't go multi-agent", "blue"),
    ("Is the right agent obvious from the initial input?", "Deterministic routing or a simple dispatcher - not handoff", "gray"),
    ("Do the stages have fixed, linear dependencies?", "Sequential", "green"),
    ("Can independent agents work the same input in parallel?", "Concurrent", "green"),
    ("Open-ended, no predetermined path, and you want a human-reviewable plan?", "Magentic", "green"),
    ("Is the specialist unknown upfront, handled one at a time?", "Handoff", "green"),
    ("Debate, consensus or review - with an objective completion test?", "Group chat: 3 agents or fewer; maker-checker for pass/fail criteria", "green"),
]

USE_AVOID = [
    [("Sequential", "green"),
     "Multistage processes with clear linear dependencies; data-transformation pipelines; stages that can't be parallelised; progressive refinement (draft, review, polish); you know each agent's availability and performance and tolerate delays",
     "Stages are embarrassingly parallel; only a few stages a single agent could do; agents must collaborate or backtrack; dynamic routing is needed; early-stage failures can't be stopped from polluting later steps",
     "Early failures propagate; no parallelism. Cost accumulates step by step"],
    [("Concurrent", "green"),
     "Parallelisable tasks (fixed set or dynamically chosen agents); multiple independent perspectives (brainstorming, ensemble reasoning, quorum or voting); time-sensitive scenarios",
     "Agents must build on each other or need cumulative context; strict order or reproducible results; quota makes parallelism inefficient; shared-state changes can't be coordinated; no conflict-resolution strategy; aggregation is too complex or lowers quality",
     "Needs conflict resolution when results contradict; resource-intensive. Cost spikes consumption"],
    [("Group chat", "green"),
     "Collaborative ideation, consensus or debate, iterative refinement, multidisciplinary dialogue; QA, compliance or editorial review; transparency and auditability",
     "Basic delegation or a linear pipeline suffices; real-time needs make discussion overhead unacceptable; a clear hierarchical or deterministic flow is better; the chat manager has no objective completion test",
     "Conversation loops; hard to control with many agents - limit to 3 or fewer"],
    [("Maker-checker (group-chat variant)", "green"),
     "Clear pass/fail acceptance criteria (also called evaluator-optimizer, generator-verifier, critic or reflection loops): the maker proposes, the checker evaluates against criteria and sends feedback",
     "-",
     "Set an iteration cap and a fallback: escalate to a human, or return the best result with a quality warning"],
    [("Handoff", "green"),
     "The specialist needed isn't known upfront; expertise emerges during processing; multi-domain problems handled one specialist at a time; predetermined signals show when an agent hits its limit",
     "The right agent is identifiable from the initial input (use deterministic routing or a simple dispatcher); rule-based routing; concurrent operations are needed; handoff loops can't be prevented",
     "Infinite handoff loops; unpredictable routing paths; bad routing means poor UX. Cost accumulates step by step"],
    [("Magentic", "green"),
     "Open-ended problems with no predetermined path; input from multiple specialists; you want a human-reviewable plan before or after execution; tool-equipped agents that change systems",
     "A deterministic solution path exists; no ledger needed; low complexity; time-sensitive work; stalls or loops with no resolution are expected",
     "Slow to converge; stalls on ambiguous goals. Most variable, least predictable cost"],
]

WHERE = [
    [("Microsoft Agent Framework", "green"),
     "Code, optionally hosted as a Foundry hosted agent. Built-in sequential, concurrent, group chat, handoff and magentic orchestrations; human-in-the-loop supported; you control deterministic routing; checkpoints for recovery. Foundry's recommended migration target \"for most teams\"; Semantic Kernel users should migrate to it",
     ("Recommended by the Foundry docs", "green")],
    [("Foundry Workflows", "red"),
     "Visual designer or YAML. Templates: Human in the loop, Sequential, Group chat. Hosted agents aren't supported in the designer. After 2026-12-01 the visual designer and in-portal execution are unsupported, but YAML definitions keep running when deployed as a hosted agent. Export the YAML first",
     ("Preview - retiring 2026-12-01", "red")],
    [("A2A between independent agents", "orange"),
     "Agent-to-agent protocol as an outbound tool and as an incoming endpoint on a Foundry agent. Lightweight hand-offs between two agents; keeps the calling agent in control",
     ("a2a v1.0: GA. a2a_preview v0.3: preview. Incoming A2A: preview doc", "orange")],
    [("Azure Logic Apps (Standard)", "orange"),
     "Foundry's low-code migration target for Workflows: a fully visual designer; the Agent action uses a Foundry project as the agent model source; 1,400+ connectors. Not supported under Foundry network isolation",
     ("Preview", "orange")],
    [("Connected agents (classic)", "gray"),
     "The Connected Agents tool from the classic Agents API isn't available in the new Foundry Agent Service; use A2A, Agent Framework or Logic Apps. The Architecture Center page still links the classic feature",
     ("Classic only - docs disagree", "gray")],
]


def decision_section(cv, y):
    left_w = 1100
    qw, ow, bh, gap = 560, 380, 66, 30
    with cv.panel(0, y, title="Quick pick: which pattern?", sub="derived from the documented use / avoid lists - not an official flowchart",
                  theme="gray", style="dotted", pad=24, title_size=26, sub_size=14, w=left_w) as qp:
        cy = qp.iy + 6
        prev = None
        for q, out, th in QUICK:
            qb = Box(qw, q, theme="gray", h=bh, size=16, fill="soft").place(cv, qp.ix, cy)
            ob = Box(ow, out, theme=th, h=bh, size=16, fill="hatch").place(cv, qp.ix + qw + 112, cy)
            connect(cv, qb, ob, a_side="right", b_side="left", label="yes", label_size=14, gap=3)
            if prev is not None:
                connect(cv, prev, qb, a_side="bottom", b_side="top", label="no", label_size=14, label_pos="right", gap=2)
            prev = qb
            cy += bh + gap
        last = Box(qw, "Combine patterns: don't force one pattern onto the whole workflow", theme="yellow", h=bh, size=16, fill="hatch").place(cv, qp.ix, cy)
        connect(cv, prev, last, a_side="bottom", b_side="top", label="no", label_size=14, label_pos="right", gap=2)
    tx = left_w + GAP
    tw = W - tx
    tb = Table([("Pattern", 190), ("Use when (documented)", 800), ("Avoid when (documented)", 800), ("Watch out for / cost profile", tw - 1790)],
               USE_AVOID, w=tw, theme="green", size=14, head_size=16, title="Choosing a pattern: use when / avoid when, as documented",
               title_size=24, first_col_theme="green")
    tb.place(cv, tx, y)
    ny = max(tb.bottom, qp.bottom - 130) + 26
    nw = (tw - GAP) / 2
    n1 = Note(nw, "Combining patterns is explicitly allowed (for example sequential first stages, then a concurrent analysis). Antipatterns: unnecessary coordination complexity; agents without real specialisation; ignoring multi-hop latency; sharing mutable state between concurrent agents; a deterministic pattern for non-deterministic work (and vice versa); ignoring resource limits when going concurrent; context windows growing unchecked.",
              kind="tip", title="Combine patterns, avoid the antipatterns", src=[AC_SRC])
    n1.place(cv, tx, ny)
    n2 = Note(nw, "Microsoft Agent Framework ships all five orchestrations. Human-in-the-loop works through tool approval and request info (approval-required tools pause the workflow for review); you control deterministic routing; checkpoints help recover from interruptions and deployments.",
              kind="key", title="Where the patterns are implemented",
              src=[("Agent Framework orchestrations", learn("agent-framework/workflows/orchestrations", base=""))])
    n2.place(cv, tx + nw + GAP, ny)
    return max(qp.bottom, n1.bottom, n2.bottom) + 70


def where_section(cv, y):
    section_header(cv, 0, y, "Where the orchestration runs, and what is changing",
                   sub=f"Agent Framework code in a hosted agent, Foundry Workflows (retiring), A2A between agents, or Logic Apps  |  {ASOF}", size=34, w=W)
    y += 110
    tw = W - 1100 - GAP
    t = Table([("Option", 300), ("What the docs say", tw - 300 - 380), ("Status", 380)], WHERE, w=tw, theme="green", size=14, head_size=16,
              first_col_theme="green")
    t.place(cv, 0, y)
    nx = tw + GAP
    n1 = Note(1100, "The Workflows designer's \"Group chat\" template is described as \"dynamically passes control between agents based on context or rules\" (typical use: escalation, fallback or expert handoff). That reads like the Architecture Center's handoff pattern, not its group chat (a shared accumulating thread run by a chat manager). Check which semantics you actually get.",
              kind="warn", title="Naming mismatch: the designer's \"Group chat\" reads like handoff", src=[("Workflows", learn("agents/concepts/workflow"))])
    n1.place(cv, nx, y)
    n2 = Note(1100, "The Architecture Center orchestration page still links the classic managed, no-code connected-agents feature, while the Foundry docs say the Connected Agents tool is not available in the new Foundry Agent Service. The A2A how-to still lists Workflows as an alternative, while the Workflows page says they retire on 2026-12-01. Verify before designing around either.",
              kind="gotcha", title="Docs disagree: connected agents and Workflows", src=[("A2A tool", learn("agents/how-to/tools/agent-to-agent")), AC_SRC])
    n2.place(cv, nx, n1.bottom + 22)
    return max(t.bottom, n2.bottom) + 70


STEPS = [
    (1, "Client calls the orchestrator endpoint", "Web/app via the Responses API, Teams via the Activity protocol, another agent via A2A. Token audience https://ai.azure.com; caller needs Foundry Agent Consumer (or Foundry User) - or a Bot Service scheme for Teams/M365."),
    (2, "Memory is loaded (preview)", "The orchestrator (a hosted agent running Agent Framework, or a prompt agent) loads memory through the memory search tool; scope such as {{$userId}}."),
    (3, "Model plans and routes", "A Foundry deployment, optionally through the AI gateway. Routing depends on the pattern: fixed order, fan-out, chat manager picks the speaker, agent hands off, or manager updates a task ledger."),
    (4, "Specialists are invoked", "In-process (Agent Framework), over A2A (a2a v1.0 tool / agent card) or through a workflow (retiring)."),
    (5, "Specialists call tools via the Toolbox", "Consumer endpoint .../toolboxes/{name}/mcp?api-version=v1 with the agent's own identity; the connection authType decides whose credentials reach the tool."),
    (6, "Tools reach their backends", "MCP servers (public, private Container Apps, managed connectors, API Center catalog), Foundry IQ knowledge base, AI Search, Fabric IQ, Work IQ."),
    (7, "Guardrails screen the traffic", "Toolbox tool inputs and outputs and model I/O; the Architecture Center also screens user input and the final output."),
    (8, "Results flow up", "The orchestrator validates and aggregates (conflict resolution, maker-checker, context compaction) and persists state and memory (extract, then consolidate)."),
    (9, "Response + telemetry", "Reply to the client; spans (invoke_agent, plan, invoke_workflow, execute_tool, memory operations) go to Application Insights; assets, metrics and compliance surface in the Control Plane."),
]


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Multi-agent platform reference architecture",
        f"Orchestrator + specialist agents, A2A, MCP, Toolbox, memory, Entra agent identity, observability and CI/CD on Microsoft Foundry  |  facts {ASOF}",
        icon="foundry", w=W)
    y = bottom + 50
    lad = summary_strip(cv, y)
    summary_cards(cv, y, lad.h)
    y = lad.bottom + 70

    section_header(cv, 0, y, "The reference architecture: an agent city",
                   sub="channels at the gate, agents downtown, tools next door, shared utilities underneath, city hall on the right - numbers 1-9 follow one request", size=34, w=W)
    y += 110
    p2, p3, dbottom, span = main_diagram(cv, y)
    y = dbottom + 50
    sb = steps(cv, 0, y, W, STEPS, cols=3, size=15)
    y = sb + 60
    y = patterns_section(cv, y)
    y = decision_section(cv, y)
    y = where_section(cv, y)
    y = agents_tools_section(cv, y)
    y = identity_state_section(cv, y)
    y = operate_section(cv, y)
    gotcha_sources(cv, y)


# ====================================================================== 4. agents, tools, A2A
def learn_line(cv, x, y, label, url, size=12):
    return cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)


def hdr(cv, y, text, sub):
    section_header(cv, 0, y, text, sub=sub, size=34, w=W)
    return y + 108


def agents_tools_section(cv, y):
    y = hdr(cv, y, "Agents, tools and agent-to-agent calls: the detail behind the diagram",
            f"hosted agents, Toolbox, MCP and A2A - preview items are marked  |  {ASOF}")
    host = Card(COLW, "Agents on the platform", [
        "Prompt agents: declarative (instructions, model, tools); voice-based prompt agents are preview",
        "Hosted agents: your code (Agent Framework, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK or custom), from a container or .zip source",
        "Per-session VM-isolated sandbox with persistent $HOME and /files; scale-to-zero with stateful resume",
        "Deploy creates a dedicated agent identity and endpoint; the project managed identity does platform work, e.g. ACR Container Registry Repository Reader",
        "User-invoked runs can use on-behalf-of; autonomous runs use the agent identity",
        "! Hosted agents aren't supported in the Workflows designer; they consume toolboxes via FoundryToolbox (Python) / AddFoundryToolboxes (.NET)",
    ], theme="green", icon="agent", src=[("Agent Service overview", learn("agents/overview")), ("Hosted agents", learn("agents/concepts/hosted-agents"))])
    tbx = Card(COLW, "Toolbox: what you get", [
        "One MCP-compatible endpoint per toolbox; pillars: Build, Discover, Consume, Govern",
        "Consumer URL {project_endpoint}/toolboxes/{name}/mcp?api-version=v1 always serves the default version",
        "Create and test a new version, then promote it to default - no agent redeploy",
        "Guardrails screen every tool input and output, so untrusted MCP responses can't smuggle prompt injection back",
        "Meta-tools tool_search and call_tool help with big catalogs; Skills are preview",
        "Any MCP runtime can consume it; Agent Framework hosted agents use FoundryToolbox / AddFoundryToolboxes",
    ], theme="orange", icon="toolbox", src=[("Toolbox overview", learn("agents/concepts/toolbox-overview"))])
    cal = Card(COLW, "Toolbox: who is the caller?", [
        "Auth lives on the project connection, never in agent code",
        "authType: none, custom-keys, project-managed-identity, agentic-identity, oauth2 (identity passthrough), user-entra-token",
        "Two identities per call: agent -> toolbox is the agent's own identity; tool -> data is the user's credentials (oauth2, user-entra-token) or a service identity, by authType",
        "Per-user tokens are isolated by Foundry; first use returns a consent link",
        "Consumers need at least Foundry Agent Consumer; the user's tenant must equal the project tenant",
        "! Direct (non-agent) toolbox clients can't use AgentOnBehalfOfUser",
    ], theme="red", icon="managed-identity", src=[("Tool authentication", learn("agents/how-to/tools/tool-authentication"))])
    proto = Table([("Protocol", 150), ("Endpoint", COLW - 150)], [
        ["Responses", "{project_endpoint}/agents/{name}/endpoint/protocols/openai/responses"],
        ["Invocations", "{project_endpoint}/agents/{name}/endpoint/protocols/invocations"],
        ["Invocations (WebSocket)", "wss://{account}.services.ai.azure.com/api/projects/{project}/agents/{name}/endpoint/protocols/invocations_ws?api-version=v1"],
        ["Activity", "bridged automatically when you publish to Microsoft 365 / Teams"],
        ["A2A", "{project_endpoint}/agents/{name}/endpoint/protocols/a2a (incoming A2A is a preview doc; enabled by REST PATCH)"],
    ], w=COLW, theme="green", size=14, head_size=15, title="Hosted-agent protocols and endpoints", title_size=20)
    right, bottom = row(cv, 0, y, [host, tbx, cal], gap=GAP, equalize=True)
    proto.place(cv, right + GAP, y)
    learn_line(cv, right + GAP, proto.bottom + 8, "Hosted agents", learn("agents/concepts/hosted-agents"))
    y = max(bottom, proto.bottom + 30) + 48

    mcp = Card(COLW, "MCP servers: public, private, managed, catalog", [
        "# Public vs private",
        "Private MCP = Azure Container Apps with internal-only ingress on a dedicated MCP subnet delegated to Microsoft.App/environments",
        "# Managed MCP servers",
        "Powered by Connector Namespaces: 1,000+ connectors, OAuth2 only, per project; connector triggers unsupported",
        "14 regions: australiaeast, brazilsouth, canadacentral, eastus2, francecentral, germanywestcentral, japaneast, norwayeast, southafricanorth, southcentralus, spaincentral, swedencentral, switzerlandnorth, westus3",
        "# Private tool catalog",
        "Azure API Center; needs the Azure API Center Data Reader role (propagation up to 24 h); found at Build > Tools",
        "MCP long-running operations (MCP tasks, background mode): preview",
    ], theme="orange", icon="mcp", badge="preview",
        src=[("MCP servers", learn("agents/how-to/tools/model-context-protocol")), ("Managed MCP (preview)", learn("agents/how-to/tools/connectors")), ("Private tool catalog", learn("agents/how-to/private-tool-catalog"))])
    mcp.place(cv, 0, y)
    nx = COLW + GAP
    n1 = Note(COLW, "On an MCP tool, allowed_tools must be a non-empty list. An empty list - or omitting it - allows EVERY tool the server exposes, not zero. Always list the tools explicitly.",
              kind="gotcha", title="allowed_tools: [] allows ALL tools", size=16, title_size=19, src=[("MCP servers", learn("agents/how-to/tools/model-context-protocol"))])
    n1.place(cv, nx, y)
    n2 = Note(COLW, "require_approval defaults to always (never must be explicit). Treat tool descriptions, annotations and results from remote MCP servers as untrusted (indirect prompt injection). Require approval for write or change operations; review allowed_tools, approvals and connection permissions when the operator or tools change; log approvals and tool calls.",
              kind="warn", title="MCP hygiene", src=[("MCP servers", learn("agents/how-to/tools/model-context-protocol"))])
    n2.place(cv, nx, n1.bottom + 22)
    n3 = Note(COLW, "A toolbox has no networking of its own: the project's network governs, and a project-level capability host is required. Work IQ and Browser automation are not supported in network-isolated projects.",
              kind="gotcha", title="Toolbox in private projects", src=[("Toolbox network isolation", learn("agents/how-to/tools/toolbox-network-isolation"))])
    n3.place(cv, nx, n2.bottom + 22)

    a2a = Card(COLW, "A2A: two directions", [
        "Outbound: the A2A tool - a2a (A2A v1.0, GA) or a2a_preview (v0.3, preview); it can sit in a toolbox",
        "Inbound: enable incoming A2A on the target by REST PATCH (agent_card + agent_endpoint.protocol_configuration.a2a); not available in the portal; preview doc",
        "Base .../agents/{agent}/endpoint/protocols/a2a; agent cards at .../agentCard/v1.0 and .../agentCard/v0.3",
        "! Default is v0.3 when no A2A-Version header / a2a-version query is sent; mismatched selectors return 400 version-ambiguous",
        "v1.0 = JSON-RPC only; v0.3 = JSON-RPC + HTTP+JSON; no gRPC; text modality only; no streaming; tasks and contexts kept 60 days",
    ], theme="orange", icon="a2a", badge="preview",
        src=[("A2A tool", learn("agents/how-to/tools/agent-to-agent")), ("Enable incoming A2A", learn("agents/how-to/enable-agent-to-agent-endpoint"))])
    a2a.place(cv, 2 * (COLW + GAP), y)
    a2b = Card(COLW, "A2A authentication", [
        "Incoming: Entra only - no anonymous, no keys; caller needs Foundry Agent Consumer (eed3b665-ab3a-47b6-8f48-c9382fb1dad6) at project or agent scope; token scope https://ai.azure.com/.default",
        "Outbound tool connection: key-based, Entra agent identity, Entra project managed identity, client user delegation (UserEntraToken or AgentOnBehalfOfUser), OAuth identity passthrough, or unauthenticated",
        "! Treat connected agents, especially non-Foundry agents, as external trust boundaries: validate exchanged data, apply least privilege, assess prompt-injection risk",
    ], theme="red", icon="managed-identity",
        src=[("A2A authentication", learn("agents/concepts/agent-to-agent-authentication")), ("Transparency note", learn("responsible-ai/agents/transparency-note"))])
    a2b.place(cv, 3 * (COLW + GAP), y)
    y = max(mcp.bottom, n3.bottom, a2a.bottom, a2b.bottom) + 48

    seq_w = 2 * COLW + GAP
    with cv.panel(0, y, title="A2A call, step by step", sub="enable, discover, authenticate, call", theme="orange", style="dotted", pad=24,
                  title_size=24, sub_size=15, w=seq_w) as sp:
        s = Sequence(cv, sp.ix, sp.iy + 4, [("Target agent owner", "gray", "users"), ("Caller agent", "green", "agent"),
                                           ("Microsoft Entra ID", "red", "managed-identity"), ("Target agent endpoint", "orange", "a2a")],
                     spacing=(seq_w - 48 - 200) / 3, head_w=200, size=15, label_size=14)
        s.msg(0, 3, "REST PATCH: enable incoming A2A (agent_card + protocol_configuration.a2a)", num=1)
        s.msg(1, 3, "GET the agent card at .../agentCard/v1.0 or .../v0.3; the A2A-Version header or a2a-version query picks the version", num=2,
              note="no selector = v0.3; conflicting selectors = 400 version-ambiguous")
        s.msg(1, 2, "request a token for https://ai.azure.com/.default", num=3, note="caller holds Foundry Agent Consumer")
        s.msg(2, 1, "access token", dash="dashed")
        s.msg(1, 3, "JSON-RPC call to .../agents/{agent}/endpoint/protocols/a2a", num=4, note="text only, no streaming, no gRPC; tasks and contexts kept 60 days")
        s.msg(3, 1, "task result", dash="dashed")
        s.note(1, 3, "Inside Foundry the calling agent uses the A2A tool plus a project connection: key, agent identity, project managed identity, user delegation, OAuth passthrough or none.", kind="info", size=14)
        s.end()
    px = seq_w + GAP
    with cv.panel(px, y, title="Toolbox with per-user auth", sub="oauth2 / user-entra-token connections", theme="orange", style="dotted", pad=24,
                  title_size=24, sub_size=15, w=W - px) as up:
        steps(cv, up.ix, up.iy + 6, W - px - 48, [
            (1, "Admin creates the connection", "e.g. azd ai connection create ... --auth-type oauth2. Auth is a property of the connection, never agent code."),
            (2, "Add tools to a toolbox version, promote it", "Promote to default: every agent on the consumer endpoint picks it up."),
            (3, "Hosted agent connects", "FoundryToolbox / AddFoundryToolboxes forwards x-agent-foundry-call-id so the proxy resolves the caller; don't hard-code or reuse it."),
            (4, "First use returns a consent link", "Foundry stores and refreshes the per-user credentials; re-consent if the refresh token expires or is revoked."),
            (5, "Later calls run as that user", "The downstream service returns only what the user may see (labels honoured)."),
        ], cols=2, size=14, theme="orange", gap=30)
    return max(sp.bottom, up.bottom) + 70


# ====================================================================== 5. identity, memory, observability
def identity_state_section(cv, y):
    y = hdr(cv, y, "Identity, memory and observability", f"who is calling whom at every hop; what the agents remember; what you can see  |  {ASOF}")
    seq_w = 2 * COLW + GAP
    with cv.panel(0, y, title="Identity hops: which credential is used where", sub="H1-H4 match the tags on the architecture diagram", theme="red",
                  style="dotted", pad=24, title_size=24, sub_size=15, w=seq_w) as hp:
        n0 = Note(seq_w - 48, "Three identity boundaries: (1) developer or admin -> Foundry: management plane, Azure RBAC; (2) caller -> agent endpoint: the authorization schemes (H1); (3) agent -> downstream tool or resource: the connection authType (H2-H4).",
                  kind="key", size=15)
        n0.place(cv, hp.ix, hp.iy + 4)
        s = Sequence(cv, hp.ix, n0.bottom + 22, [("Caller", "gray", "users"), ("Agent endpoint", "green", "agent"), ("Agent (own identity)", "red", "managed-identity"),
                                                ("Toolbox", "orange", "toolbox"), ("Tool or data", "teal", "ai-search")],
                     spacing=(seq_w - 48 - 190) / 4, head_w=190, size=15, label_size=14)
        s.msg(0, 1, "Entra token (audience https://ai.azure.com) checked against Azure RBAC (AzureRbac); or AgentBlueprint (preview); or Bot Service for Teams / M365", num="H1",
              note="no API keys on agent endpoints")
        s.msg(1, 2, "the request runs as the agent's own Entra identity")
        s.msg(2, 3, "agent identity: blueprint authentication, then an agent-identity token, then a token for the toolbox audience", num="H2")
        s.msg(3, 4, "the connection authType decides: none, custom-keys, project-managed-identity, agentic-identity, oauth2, user-entra-token", num="H3")
        s.msg(2, 4, "delegated tools (Foundry IQ, Work IQ, Fabric IQ, Dataverse ...): AgentOnBehalfOfUser or UserEntraToken keeps per-user permissions", num="H4")
        s.note(0, 4, "Platform-only hop: the project managed identity does infra work for hosted agents (for example it pulls the image from ACR with Container Registry Repository Reader). The exact role a hosted agent's identity needs to call model deployments is not documented on the pages read - do not assume one.", kind="warn", size=14)
        s.end()
    ident = Card(COLW, "Entra agent identity", [
        "Each new agent gets an agent identity blueprint plus an agent identity (a service principal under the blueprint)",
        "A federated credential on the blueprint trusts the first-party Azure Machine Learning app (appId 0736f41a-0425-4b46-bdb5-1563eff02385)",
        "Runtime token exchange in four stages: blueprint authentication, agent-identity token, token scoped to the downstream audience, tool call",
        "Hosted sandboxes hold no blueprint credential - the token service sits outside the sandbox",
        "Legacy agents share the project identity; migrating changes the identity and role assignments do not transfer",
        "! A new identity has NO permissions until granted",
        "Entra features apply: Conditional Access, identity protection, governance (sponsors, owners, expiry), sign-in and audit logs",
    ], theme="red", icon="identity-governance", src=[("Entra agent identity", learn("agents/concepts/agent-identity")), ("Identity overview", learn("agents/concepts/identity-access-overview"))])
    ident.place(cv, seq_w + GAP, y)
    auth = Card(COLW, "Who may call an agent endpoint", [
        "AzureRbac (alias Entra): audience https://ai.azure.com; needs Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action",
        "AgentBlueprint (preview): audience = the agent blueprint; delegated scope defaults to api://<blueprint-client-id>/access_agent; app-only needs a non-empty token_validation_rules.allowed_clients",
        "BotServiceRbac, BotServiceTenant, BotService (legacy): Teams / Microsoft 365 publishing schemes",
        "Delegated tools: agent-on-behalf-of-user is preview and needs agent-blueprint endpoint access",
        "! API keys are not supported on agent endpoints",
        "Routine dispatch needs AzureRbac / Entra kept on the endpoint",
    ], theme="red", icon="key-vault", src=[("Endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")), ("User delegation", learn("agents/concepts/user-delegation"))])
    auth.place(cv, seq_w + GAP + COLW + GAP, y)
    y = max(hp.bottom, ident.bottom, auth.bottom) + 50

    mem = Table([("Memory (preview)", 190), ("Detail", seq_w - 190)], [
        ["Memory types", "User profile, chat summary, procedural"],
        ["Operations", "Extract, consolidate, retrieve; item CRUD; store-level default TTL; direct remember / forget; memory search tool with a scope such as {{$userId}}"],
        ["Two ways to use it", "Memory search tool on a prompt agent (reads and writes during conversations; the only path with automatic scope resolution) or the Memory Store APIs (direct item control; scope must be set explicitly on every request)"],
        ["Limits", "100 scopes per store; 10,000 memories per scope; 1,000 requests/min each for search and update"],
        ["Dependencies", "Azure OpenAI chat + embedding deployments; 19 regions: Australia East, Brazil South, Canada East, East US 2, France Central, Italy North, Japan East, Korea Central, North Central US, Norway East, South Africa North, South India, Sweden Central, Switzerland North, UAE North, UK South, West US, West US 2, West US 3"],
        [("Network", "red"), ("VNet integration is NOT supported for memory stores", "red")],
        ["When to use what", "Memory = user-specific or agent context learned over time; Foundry IQ knowledge base = curated organisational content; file search = documents the user provides during an interaction"],
        ["Caveats", "Some defaults (enabling procedural memory, default TTL) are set at store creation - verify post-create update support for your API version. Retrieve user-profile memory early, chat-summary memory per turn. LLM-extracted memories can be poisoned: validate prompts in and out with Azure AI Content Safety and prompt-injection detection, and run adversarial tests. Preview: you pay for the chat and embedding model usage, and price can change"],
    ], w=seq_w, theme="teal", size=14, head_size=16, first_col_theme="teal", title="Memory stores: what the docs say", title_size=22)
    mem.place(cv, 0, y)
    learn_line(cv, 0, mem.bottom + 8, "What is memory", learn("agents/concepts/what-is-memory"))
    obs = Card(COLW, "Observability", [
        "Tracing is GA for prompt and hosted agents; workflow and external agents are preview",
        "Traces are stored in Application Insights",
        "OpenTelemetry GenAI semantic conventions (status: Development), with multi-agent conventions co-developed with Cisco Outshift",
        "Spans: invoke_agent, plan, invoke_workflow, execute_tool and memory operations; attributes gen_ai.tool.*",
        "Instrument every agent operation and handoff; keep per-agent baselines",
    ], theme="violet", icon="app-insights", src=[("Agent tracing", learn("observability/concepts/trace-agent-concept"))])
    cp = Card(COLW, "Control Plane and AI gateway", [
        "Operate panes: Overview, Assets, Compliance; Quota under Manage",
        "Integrations: Defender, Purview, Entra; AI Red Teaming; continuous evaluation",
        "The AI gateway (API Management) is a prerequisite for advanced governance - see the AI gateway canvas",
        "Models, MCP tools and agents can sit behind it; MCP governance and bring-your-own-model gateways are preview",
    ], theme="grape", icon="apim", src=[("Control Plane", learn("control-plane/overview")), ("AI gateway", learn("agents/how-to/ai-gateway"))])
    obs_h = max(obs.h, cp.h, (mem.h - 22) / 2)
    obs.place(cv, seq_w + GAP, y, h=obs_h)
    cp.place(cv, seq_w + GAP + COLW + GAP, y, h=obs_h)
    return max(mem.bottom + 30, obs.bottom, cp.bottom) + 70


# ====================================================================== 6. operate: lifecycle, CI/CD, decisions
LIFECYCLE = [
    ("Choose a type", "prompt, voice (preview) or hosted", "green"),
    ("Create", "instructions, model, code", "green"),
    ("Add tools", "Toolbox, MCP, A2A", "orange"),
    ("Version", "versions are immutable", "gray"),
    ("Trace", "Application Insights", "violet"),
    ("Evaluate", "eval runs and gates", "violet"),
    ("Optimize", "agent optimizer (preview)", "violet"),
    ("Publish", "stable endpoint, Teams / M365, Agent 365", "blue"),
    ("Monitor", "Control Plane, continuous evaluation", "grape"),
]

DECISIONS = [
    ["Single vs multi-agent", "Single agent + tools (the default)", "Multi-agent", "Go multi only for prompt complexity, tool overload or security-boundary needs; each extra agent adds latency, cost and failure modes"],
    ["Where orchestration runs", "Agent Framework (code, hosted agent)", "Workflows (retiring), Logic Apps (low-code) or A2A", "Foundry recommends Agent Framework for most teams and Logic Apps for low-code; don't start new designs on Workflows"],
    ["Agent-to-agent transport", "In-process calls (shared runtime)", "A2A (independent deployment and boundaries)", "A2A limits: text only, no streaming, no gRPC, default v0.3, REST-only enablement"],
    ["Tool exposure", "Toolbox (central auth, guardrails, versions)", "Direct tools", "Function calling, Bing grounding, Computer use, Image generation, SharePoint, Fabric data agent and Azure Functions can't go in a toolbox"],
    ["MCP hosting", "Public MCP or managed connectors (preview, OAuth2 only, 14 regions)", "Private MCP on Container Apps (internal ingress)", "Private needs an MCP subnet delegated to Microsoft.App/environments"],
    ["Tool-call identity", "Agent identity (per-agent audit, least privilege)", "User delegation (OBO / oauth2)", "Pick per tool; Work IQ needs AgentOnBehalfOfUser"],
    ["Memory", "Foundry memory stores (preview, no VNet)", "Your own store", "Memory stores aren't available to VNet-integrated designs today"],
    ["Model per agent", "Small model (classification, extraction, formatting)", "Capable model (planning)", "Match the model to the task complexity"],
    ["Context passing", "Full raw context", "Compacted summaries or fresh instructions only", "Monitor context size, compact between agents, persist shared state externally"],
    ["Group chat size", "3 agents or fewer", "More", "Beyond 3 is hard to control; set iteration caps"],
]

WAF = [
    [("Reliability", "blue"), "Timeouts and retries; degrade gracefully when agents fault; surface errors, don't hide them; validate agent output before passing it on; circuit breakers for agent dependencies; isolate agents (one shared model endpoint or knowledge store can rate-limit parallel agents); use SDK checkpoints to recover from interruptions and deployments; persist task progress, intermediate results and history in a durable store"],
    [("Security", "red"), "Authenticate and secure the network between agents; review inter-agent messages for data privacy; audit trails; least privilege; security trimming in EVERY agent; content-safety guardrails at user input, tool calls, tool responses and final output; Foundry: an identity per agent, Conditional Access, sponsors and expiry, no API keys on endpoints"],
    [("Cost", "yellow"), "Right-size the model per agent; monitor tokens per agent and per orchestration run; compact context between agents. Sequential and handoff accumulate cost step by step, concurrent spikes consumption, magentic is the most variable"],
    [("Operations", "violet"), "Instrument all agent operations and handoffs; per-agent baselines; testable agent interfaces; integration tests with scoring rubrics or LLM-as-judge (outputs are non-deterministic); HITL gates (observer, reviewer, escalation target) with state persisted at mandatory gates; scope approvals to sensitive tool calls; CI/CD with eval gates"],
    [("Performance", "indigo"), "Multi-hop latency; context windows grow with every agent; concurrent patterns need quota headroom; use deterministic routing or a dispatcher when the right agent is obvious; magentic is not for time-sensitive work"],
]


def operate_section(cv, y):
    y = hdr(cv, y, "Operate: lifecycle, CI/CD and the decision tables",
            f"agent lifecycle, a hosted-agent pipeline with an eval gate, design decisions and Well-Architected-style guidance  |  {ASOF}")
    bw = (W - 8 * 44) / 9
    bx = 0
    prev = None
    for i, (lab, sub, th) in enumerate(LIFECYCLE):
        b = Box(bw, lab, sub=sub, theme=th, h=96, size=18, sub_size=14, fill="hatch").place(cv, bx, y)
        numbered(cv, bx + 16, y - 6, i + 1, theme=th, d=30, size=16)
        if prev is not None:
            connect(cv, prev, b, a_side="right", b_side="left", sw=2.5, gap=3)
        prev = b
        bx += bw + 44
    learn_line(cv, 0, y + 106, "Agent development lifecycle", learn("agents/concepts/development-lifecycle"))
    y += 150

    pw = 3 * COLW + 2 * GAP
    with cv.panel(0, y, title="CI/CD for hosted agents with azd", sub="GitHub Actions or Azure DevOps; OIDC federated login", theme="gray", style="dotted", pad=24,
                  title_size=24, sub_size=15, w=pw) as pp:
        sw_ = (pw - 48 - 5 * 52) / 6
        stages = [
            ("Install", "azd ext install microsoft.foundry", "gray"),
            ("Configure", "azd pipeline config generates the workflow", "gray"),
            ("Provision", "azd provision", "blue"),
            ("Deploy", "azd deploy", "green"),
            ("Quality gate", "azd ai agent eval run; azd ai eval run start --fail-on pass-rate=0.8", "violet"),
            ("Promote", "after the gate passes", "grape"),
        ]
        sx, prev = pp.ix, None
        hh = 130
        for lab, sub, th in stages:
            b = Box(sw_, lab, sub=sub, theme=th, h=hh, size=19, sub_size=14, fill="hatch").place(cv, sx, pp.iy + 6)
            if prev is not None:
                connect(cv, prev, b, a_side="right", b_side="left", sw=2.5, gap=3)
            prev = b
            sx += sw_ + 52
        cf = ChipFlow([
            Chip("Concurrency group serialises runs", theme="gray", size=15, fill="soft"),
            Chip("Terraform remote state via an RS_* backend", theme="gray", size=15, fill="soft"),
            Chip("Self-hosted runners inside the VNet for private projects", theme="indigo", size=15, fill="soft"),
            Chip("Gate needs the azure.ai.evaluations extension", theme="violet", size=15, fill="soft"),
            Chip("CI identity: Foundry Owner + Contributor", theme="red", size=15, fill="soft"),
        ], pw - 48, gap=12)
        cf.place(cv, pp.ix, pp.iy + 6 + hh + 22)
    n = Note(COLW, "Pin production to its existing version before the deploy step, then promote only after the eval gate passes. The pipeline provisions and deploys; it does not decide for you which version serves traffic.",
             kind="tip", title="Pin production, then promote", src=[("Set up CI/CD", learn("agents/how-to/set-up-ci-cd-cli"))])
    n.place(cv, pw + GAP, y)
    y = max(pp.bottom, n.bottom) + 50

    dw = 2252
    dec = Table([("Decision", 220), ("Option A", 430), ("Option B", 460), ("Documented guidance", dw - 1110)], DECISIONS, w=dw, theme="grape", size=14, head_size=16,
                first_col_theme="grape", title="Design decisions and trade-offs", title_size=24)
    dec.place(cv, 0, y)
    ww = W - dw - GAP
    waf = Table([("Pillar", 130), ("Documented guidance (Architecture Center implementation considerations)", ww - 130)], WAF, w=ww, theme="blue", size=14, head_size=15,
                first_col_theme="blue", title="Well-Architected-style guidance", title_size=24)
    waf.place(cv, dw + GAP, y)
    learn_line(cv, dw + GAP, waf.bottom + 8, "AI agent orchestration patterns", learn(AC, base=""))
    return max(dec.bottom, waf.bottom + 30) + 70


# ====================================================================== 7. gotchas and sources
GOTCHAS = [
    ["Foundry Workflows (preview) retire 2026-12-01: the designer and in-portal execution end; YAML keeps running only as a hosted agent",
     "Connected Agents isn't available in the new Foundry service - use A2A, Agent Framework or Logic Apps",
     "MCP allowed_tools: [] (or omitted) allows ALL tools - always list them explicitly",
     "MCP require_approval defaults to always; never must be set explicitly",
     "A2A defaults to v0.3 when no version selector is sent; v1.0 is the GA a2a tool; incoming A2A can't be enabled in the portal"],
    ["Moving a legacy agent to its own identity doesn't carry role assignments; a new identity has no permissions",
     "Hosted sandboxes hold no blueprint credential; tokens come from a service outside the sandbox",
     "Per-user tool auth needs the project's tenant and at least Foundry Agent Consumer; direct toolbox clients can't use AgentOnBehalfOfUser",
     "Agent-on-behalf-of-user and the AgentBlueprint endpoint scheme are preview",
     "Security trimming must be implemented in EVERY agent of a multi-agent flow: agents have broad access, users must not"],
    ["Memory has no VNet support; limits 100 scopes/store, 10,000 memories/scope, 1,000 requests/min each for search and update",
     "Toolbox in private projects: no networking of its own; Work IQ and Browser automation unsupported; project-level capability host required",
     "Private tool catalog: the Azure API Center Data Reader role can take up to 24 h to propagate",
     "Tracing for workflow and external agents is preview (prompt and hosted agents are GA)",
     "Magentic is the slowest to converge and the most variable in cost; group chat beyond 3 agents is hard to control"],
]


def gotcha_sources(cv, y):
    y = hdr(cv, y, "Gotchas checklist", f"the things that bite in production - all items as documented {ASOF}")
    cw = (W - 2 * GAP) / 3
    cards = [Card(cw, t, ["! " + g for g in col], theme="red", fill="soft", body_size=15)
             for t, col in zip(("Retirement, MCP and A2A", "Identity and delegation", "State, network and operations"), GOTCHAS)]
    right, bottom = row(cv, 0, y, cards, gap=GAP)
    y = bottom + 60
    sources(cv, 0, y, [
        ("AI agent orchestration patterns (Architecture Center)", learn(AC, base="")),
        ("Agent Framework: workflow orchestrations", learn("agent-framework/workflows/orchestrations", base="")),
        ("Foundry Agent Service overview", learn("agents/overview")),
        ("Build a workflow (retiring 2026-12-01)", learn("agents/concepts/workflow")),
        ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
        ("Toolbox: tool authentication", learn("agents/how-to/tools/tool-authentication")),
        ("Connect to an MCP server", learn("agents/how-to/tools/model-context-protocol")),
        ("Connect to an A2A agent endpoint", learn("agents/how-to/tools/agent-to-agent")),
        ("Enable an incoming A2A endpoint", learn("agents/how-to/enable-agent-to-agent-endpoint")),
        ("Entra agent identity", learn("agents/concepts/agent-identity")),
        ("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
        ("What is memory in Agent Service", learn("agents/concepts/what-is-memory")),
        ("Hosted agents", learn("agents/concepts/hosted-agents")),
        ("Set up CI/CD for agents", learn("agents/how-to/set-up-ci-cd-cli")),
    ], w=W, cols=4)

