"""Microsoft 365 / Teams, Work IQ, SharePoint, Agent 365, Fabric IQ and event-driven integration: three islands and a bridge,
with the identity used on every hop and what stays private versus goes public. Part 2 covers autopilots, routines, Functions,
Logic Apps, network-isolation support, design decisions and gotchas."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme
from generator.xd.blocks import draw_mark

META = dict(
    id="ra-m365-fabric-integration",
    title="Microsoft 365, Fabric and event-driven integration",
    section="3", group="Reference architectures", order=6,
    description="Three islands and a bridge: publish a Foundry agent to Microsoft 365 Copilot and Teams (public, source-IP-filtered route for a private Foundry), "
                "Work IQ, SharePoint, Agent 365, Fabric IQ and the Fabric data agent deprecation - with the identity used on every hop and what stays private.",
    tags=["microsoft-365", "teams", "work-iq", "fabric-iq", "agent-365", "identity"],
)

W = 3300
ASOF = "as of 2026-11-03"
GRN, RED, GRY, INKC, IND, ORG = "#2f9e44", "#e03131", "#868e96", "#1e1e1e", "#3b5bdb", "#e8590c"

# ----------------------------------------------------------------------------------------------------- citations
S_PUB = ("Publish an agent to Microsoft 365 Copilot and Teams", learn("agents/how-to/publish-copilot"))
S_PUBVNET = ("Publish from a network-isolated project", learn("agents/how-to/publish-copilot-virtual-network"))
S_WORKIQ = ("Work IQ tool", learn("agents/how-to/tools/work-iq"))
S_SP = ("SharePoint tool", learn("agents/how-to/tools/sharepoint"))
S_A365 = ("Agent 365 integration", learn("agents/concepts/agent-365-integration"))
S_A365PERM = ("Grant Agent 365 permissions", learn("agents/how-to/grant-agent-365-permissions"))
S_AUTO = ("Autopilot overview", learn("agents/concepts/autopilot-overview"))
S_AUTOLC = ("Autopilot lifecycle", learn("agents/concepts/autopilot-lifecycle"))
S_AUTOQS = ("Build your first autopilot", learn("agents/how-to/agent-365"))
S_ROUT = ("Routines", learn("agents/concepts/routines"))
S_FIQ = ("Fabric IQ tool", learn("agents/how-to/tools/fabric-iq"))
S_FDA = ("Fabric data agent tool", learn("agents/how-to/tools/fabric"))
S_FUNC = ("Azure Functions tool", learn("agents/how-to/tools/azure-functions"))
S_AUTHZ = ("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))
S_TOOLAUTH = ("Tool authentication", learn("agents/how-to/tools/tool-authentication"))
S_LA1 = ("Automate Foundry agents with Logic Apps workflows", learn("azure/logic-apps/automate-foundry-agents-with-workflows", base=""))
S_LA2 = ("Add agent tools: connector actions in Logic Apps", learn("azure/logic-apps/add-agent-tools-connector-actions", base=""))
S_ALZ = ("Baseline Foundry chat in an Azure landing zone",
         learn("ai-ml/architecture/baseline-microsoft-foundry-landing-zone", base="azure/architecture"))


# ----------------------------------------------------------------------------------------------------- helpers
def chapter(cv, y, text, sub=None):
    _, b = section_header(cv, 0, y, text, sub=sub, size=34, w=W, sub_size=17)
    return b + 30


def zone(cv, x, y, w, h, title=None, *, theme="indigo", sub=None, style="dotted", fill="none", icon=None, title_size=22,
         sub_size=15, pad=16, sw=2, icon_size=30):
    """Explicit-size boundary drawn BEFORE its children."""
    th = get_theme(theme)
    bg, fs = "transparent", "solid"
    if fill == "hatch":
        bg, fs = th.fill, "hachure"
    elif fill == "solid":
        bg, fs = th.fill, "solid"
    elif fill == "soft":
        bg, fs = th.soft, "solid"
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=bg, style=fs, sw=sw, dash=style)
        tx = x + pad
        if icon:
            place_icon(cv, icon, x + pad, y + pad * 0.5, icon_size)
            tx += icon_size + 10
        if title:
            t = cv.text(tx, y + pad * 0.7, title, size=title_size, color=th.deep)
            if sub:
                cv.text(tx, t.bottom + 2, sub, size=sub_size, color=MUTED)


def pill(cv, x, y, text, th="indigo", size=12, right=False, pad=7, solid=True):
    t = get_theme(th)
    tw, hh = metrics.text_size(text, size)
    w, h = tw + 2 * pad, hh + 6
    if right:
        x -= w
    with cv.group():
        cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill if solid else "transparent", style="solid", sw=1.5, rough=0)
        cv.text(x + pad, y + 3, text, size=size, color=t.deep)
    return w, h


ID_TH, NET_PRIV, NET_PUB, NET_FILT, ST_PRE, ST_DEP, ST_GA = "red", "indigo", "orange", "yellow", "violet", "red", "green"


def chips_row(cv, cx, y, items, max_w, size=13, gap=8):
    """Centered rows of (label, theme) pills; returns bottom y."""
    rows, cur, cw = [], [], 0.0
    for lab, th in items:
        w = metrics.text_size(lab, size)[0] + 14
        if cur and cw + gap + w > max_w:
            rows.append((cur, cw))
            cur, cw = [], 0.0
        cw += (gap if cur else 0) + w
        cur.append((lab, th, w))
    if cur:
        rows.append((cur, cw))
    yy = y
    for r, rw in rows:
        x = cx - rw / 2
        for lab, th, w in r:
            pill(cv, x, yy, lab, th, size)
            x += w + gap
        yy += metrics.text_size("Ag", size)[1] + 6 + 5
    return yy


def hop(cv, y, x1, x2, n, label, chips, *, dash="solid", color=INKC, num_theme="blue", lab_w=None, sw=3, lab_dy=0):
    """Horizontal hop arrow x1 -> x2 at y: number circle in the middle, label above, identity / network / status chips below."""
    arrow(cv, [(x1, y), (x2, y)], color=color, sw=sw, dash=dash, end_head="arrow")
    xm = (x1 + x2) / 2
    numbered(cv, xm, y, n, theme=num_theme, d=30, size=17)
    lw = lab_w or abs(x2 - x1) - 20
    lines = wrap_text(label, lw, 14)
    th_ = len(lines) * 14 * metrics.line_ratio()
    cv.text(xm - lw / 2, y - 22 - th_ + lab_dy, "\n".join(lines), size=14, color=INKC, align="center", w=lw)
    return chips_row(cv, xm, y + 22, chips, lw + 20)


class Steps(Rect2):
    """Card whose rows are round numbered markers + wrapped text."""

    def __init__(self, w, title, steps, *, theme_name="blue", icon=None, src=(), size=15, title_size=22, pad=16, gap=10, d=30, badge=None):
        self.th = get_theme(theme_name)
        self.w, self.title, self.icon, self.src, self.badge = w, title, icon, list(src), badge
        self.size, self.title_size, self.pad, self.gap, self.d = size, title_size, pad, gap, d
        self.steps = []
        text_w = (w - 2 * pad - d - 12) * 0.965
        y = pad + max(title_size * metrics.line_ratio(), 36 if icon else 0) + 8
        for st in steps:
            n, text = st[0], st[1]
            th = st[2] if len(st) > 2 else theme_name
            lines = wrap_text(text, text_w, size)
            hh = max(len(lines) * size * metrics.line_ratio(), d)
            self.steps.append((n, th, lines, y, hh))
            y += hh + gap
        y -= gap
        self.src_lines = []
        if self.src:
            y += 8
            for label, url in self.src:
                ls = wrap_text(f"Learn: {label}", (w - 2 * pad) * 0.965, 12)
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
            tx = x + pad
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad - 2, 34)
                tx += 44
            cv.text(tx, y + pad, self.title, size=self.title_size, color=th.deep)
            if self.badge:
                draw_badge(cv, x + self.w - pad - metrics.line_width(self.badge, 13) - 18, y + pad - 1, self.badge)
            for n, sth, lines, sy, hh in self.steps:
                numbered(cv, x + pad + self.d / 2, y + sy + self.d / 2, n, theme=sth, d=self.d, size=17)
                ty = y + sy + ((self.d - self.size * metrics.line_ratio()) / 2 + 1 if len(lines) == 1 else 0)
                cv.text(x + pad + self.d + 12, ty, "\n".join(lines), size=self.size, color=INKC)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self


# ----------------------------------------------------------------------------------------------------- 0 title + headlines
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Microsoft 365, Fabric and event-driven integration",
        "Three islands and a bridge: which identity is used on every hop, and what stays private versus goes public - "
        f"{ASOF}. Part 2: autopilots, routines, Functions, Logic Apps, network support and gotchas", w=W)
    y = bottom + 34
    gap = 30
    cw = (W - 4 * gap) / 5
    c1 = Card(cw, "1  Microsoft 365 can't reach a private Foundry privately", [
        "Publishing from a network-isolated project needs a manually enabled, source-IP-filtered PUBLIC Activity Protocol route",
        "Responses, A2A and MCP stay private",
    ], theme="red", icon="globe", src=[S_PUBVNET])
    c2 = Card(cw, "2  Work IQ and the SharePoint tool", [
        "Preview, delegated-only (on behalf of the user) and public endpoints",
        "The SharePoint tool does not work once the agent is published to Teams",
    ], theme="orange", icon="sharepoint", badge="preview", src=[S_WORKIQ, S_SP])
    c3 = Card(cw, "3  Fabric data agent tool: deprecation scheduled 2026-11-06", [
        "Migrate to the Fabric IQ tool (preview)",
        "The data agent tool is unsupported under network isolation",
    ], theme="red", icon="fabric", badge="retiring", src=[S_FDA, S_FIQ])
    c4 = Card(cw, "4  An autopilot is an agent identity plus an Entra agent user", [
        "You publish a blueprint; managers hire instances, one licence each",
        "Identity defines it, not capabilities",
    ], theme="green", icon="agent", badge="preview", src=[S_AUTO])
    c5 = Card(cw, "5  Routines run as the agent identity", [
        "One trigger + one action",
        "Creator identity is an explicit opt-in at create time and can't be changed afterwards",
    ], theme="violet", icon="scheduler", src=[S_ROUT])
    r, b = row(cv, 0, y, [c1, c2, c3, c4, c5], gap=gap)
    return b + 50


# ----------------------------------------------------------------------------------------------------- 1 the map
def _map(cv, y):
    y = chapter(cv, y, "1  Three islands and a bridge: Microsoft 365, Foundry and Fabric",
                "Every arrow carries a number, the identity it runs as (red chips) and the network path it takes (blue private, orange public, yellow public but "
                "IP-filtered). Hops 1-10 are tabulated in section 2")
    FY = y
    IL_W, CL_W, C_W, CR_W = 700, 540, 1060, 480
    C_X = IL_W + CL_W
    F_X = C_X + C_W + CR_W
    F_W = W - F_X
    ROWH = 124
    ISY = FY + 214
    HDR = 92
    n_rows = 6
    ISH = HDR + 14 + n_rows * ROWH + 14

    def yc(j):
        return ISY + HDR + 14 + j * ROWH + ROWH / 2

    # ---- islands
    zone(cv, 0, ISY, IL_W, ISH, "Microsoft 365", theme="blue", style="solid", fill="soft", sw=2.5, title_size=26, icon="m365", icon_size=36, pad=18,
         sub="where users, admins and the work graph live")
    zone(cv, C_X, ISY, C_W, ISH, "Microsoft Foundry", theme="green", style="solid", fill="soft", sw=2.5, title_size=26, icon="foundry", icon_size=36, pad=18,
         sub="the agent, its endpoint, tools and routines")
    zone(cv, F_X, ISY, F_W, ISH, "Microsoft Fabric", theme="cyan", style="solid", fill="soft", sw=2.5, title_size=26, icon="fabric", icon_size=36, pad=18,
         sub="OneLake, data agents, ontologies")
    # identities live in the Foundry header
    cx0 = C_X + 560
    pill(cv, cx0, ISY + 20, "project managed identity", "red", 13)
    pill(cv, cx0, ISY + 52, "agent identity (Entra)", "red", 13)

    # ---- left island boxes
    lx, lw = 30, IL_W - 60
    bh = 104

    def lbox(j, label, sub, icon, th="blue"):
        return Box(lw, label, sub=sub, icon=icon, icon_pos="left", theme=th, h=bh, size=18, sub_size=13, icon_size=40).place(cv, lx, yc(j) - bh / 2)

    L0 = lbox(0, "Teams and Microsoft 365 Copilot", "the chat surfaces; agents appear under 'Your agents', 'Built by your org' or 'Agents for your team'", "teams")
    L1 = lbox(1, "Microsoft 365 admin center", "approves 'organization' publishes; Agents registry: Pending activate -> Available", "m365")
    L2 = lbox(2, "Agent 365", "registry, access control, visualization, interoperability, security", "m365", "indigo")
    L3 = lbox(3, "Entra agent user (autopilot)", "mailbox, calendar, Teams, org chart; one per hired instance", "users", "teal")
    L4 = lbox(4, "Work IQ service", "workiq.svc.cloud.microsoft - mail, meetings, files, Teams, people", "iq", "blue")
    L5 = lbox(5, "SharePoint", "Microsoft Copilot Retrieval API (text; semantic retrieval for doc, pptx, pdf, aspx, one)", "sharepoint", "teal")

    # ---- centre island boxes
    ix = C_X + 22
    iw = C_W - 44
    tall = 2 * ROWH - 12
    ep = Card(620, "Agent endpoint", [
        "Stable URL serves the active version (version_selector; 'Always use latest' is the default)",
        "Auth: AzureRbac / Entra; BotServiceRbac or BotServiceTenant for Teams and M365",
        "Responses, Invocations, A2A, MCP; Activity is added when you publish",
        "! Private project: portal publish is unsupported; REST with enable_m365_public_endpoint: true opens a public, source-IP-filtered Activity route",
    ], theme="green", icon="foundry", fill="soft", title_size=19, body_size=14, pad=14, icon_size=30, min_h=tall)
    ep.place(cv, ix, yc(0) - ROWH / 2 + 6)
    rt = Card(iw - 620 - 22, "Routines", [
        "One trigger + one action: invokes a prompt or hosted agent (Responses or Invocations API)",
        "Timer, recurring (min 5 min) or event: github_issue, Teams channel message",
        "Runs as the agent identity; creator identity is an irreversible opt-in; the endpoint must keep AzureRbac / Entra",
        "5 delivery attempts, 30 s timeout",
    ], theme="violet", icon="scheduler", fill="soft", title_size=19, body_size=14, pad=14, icon_size=30, min_h=tall)
    rt.place(cv, ix + 620 + 22, yc(0) - ROWH / 2 + 6)
    hs = Card(500, "Hosted agent (blueprint)", [
        "Your container on Foundry-managed compute",
        "Only hosted agents can be published as autopilot blueprints (part 2)",
        "Own Entra agent identity; Agent 365 telemetry needs the Agent 365 SDK and the OtelWrite role",
    ], theme="green", icon="container-apps", fill="soft", title_size=19, body_size=14, pad=14, icon_size=30, min_h=tall)
    hs.place(cv, ix, yc(2) - ROWH / 2 + 6)
    pa = Card(iw - 500 - 22, "Prompt agent", [
        "Codeless, platform-managed",
        "Reaches Teams and Microsoft 365 Copilot through the Activity protocol on its endpoint",
        "Agent 365: registry sync and activity data",
        "! The SharePoint tool stops working once the agent is published to Teams",
    ], theme="green", icon="agent", fill="soft", title_size=19, body_size=14, pad=14, icon_size=30, min_h=tall)
    pa.place(cv, ix + 500 + 22, yc(2) - ROWH / 2 + 6)
    tb = Box(iw, "Toolbox", sub="work_iq_preview and fabric_iq_preview as native tools, MCP servers; SharePoint, Azure Functions and Fabric data agent tools can't go in a toolbox",
             icon="toolbox", icon_pos="left", theme="orange", h=bh, size=18, sub_size=13, icon_size=34).place(cv, ix, yc(4) - bh / 2)
    dt = Box(iw, "Direct tools", sub="SharePoint tool, Azure Functions tool, Logic Apps workflow as a tool, Fabric data agent tool (deprecating)",
             icon="gear", icon_pos="left", theme="orange", h=bh, size=18, sub_size=13, icon_size=34).place(cv, ix, yc(5) - bh / 2)

    # ---- right island boxes
    rx, rw = F_X + 22, F_W - 44
    onel = Box(rw, "OneLake", sub="the data layer under Fabric items; also a Foundry IQ indexed knowledge source (no private sync)", icon="onelake", icon_pos="top",
               theme="cyan", h=tall, size=18, sub_size=13, icon_size=36).place(cv, rx, yc(0) - ROWH / 2 + 6)
    fiq_h = 3 * ROWH - 12
    fx0, fy0 = rx, yc(2) - ROWH / 2 + 6
    zone(cv, fx0, fy0, rw, fiq_h, "Fabric IQ tool", theme="cyan", style="solid", fill="hatch", sw=2.5, title_size=20, icon="fabric", icon_size=30, pad=14)
    draw_badge(cv, fx0 + rw - 14 - 78, fy0 + 12, "preview")
    sub_y = fy0 + 56
    for nm, net, th in (("Ontology", "tenant-level private link", "indigo"), ("Data agent", "tenant + workspace private link", "indigo"),
                        ("Power BI semantic model", "public access only", "orange")):
        Box(rw - 28, nm, sub=net, theme="cyan", h=84, size=16, sub_size=13, fill="solid").place(cv, fx0 + 14, sub_y)
        sub_y += 96
    fda = Box(rw, "Fabric data agent tool", sub="deprecation scheduled for 2026-11-06 (as of 2026-11-03): migrate to Fabric IQ", icon="fabric", icon_pos="left",
              theme="red", fill="soft", dash="dashed", h=bh, size=17, sub_size=13, icon_size=30).place(cv, rx, yc(5) - bh / 2)

    # ---- bridge arrows (left corridor)
    xl, xr = IL_W + 8, C_X - 8
    gate_w = 230
    gx = IL_W + (CL_W - gate_w) / 2
    y0 = yc(0) - 22
    gate = Box(gate_w, "Azure Bot Service", sub="Activity protocol channel + signed channel token", icon="bot", icon_pos="top", theme="gray", h=112, size=17,
               sub_size=12, icon_size=32).place(cv, gx, y0 - 56)
    arrow(cv, [(xl, y0), (gate.x - 4, y0)], sw=3, color=INKC)
    arrow(cv, [(gate.right + 4, y0), (xr, y0)], sw=3.5, color=ORG)
    numbered(cv, xl + 40, y0, 1, theme="blue", d=30, size=17)
    cv.text(gate.right + 8, y0 - 46, "Activity protocol", size=13, color=INKC)
    chips_row(cv, IL_W + CL_W / 2, y0 + 64, [("M365 user (Bot token)", ID_TH), ("public, IP-filtered", NET_FILT)], CL_W - 16)

    hop(cv, yc(1), xr, xl, 10, "publish and approve: Bot Service + Teams manifest, admin approval", [("Azure Bot Service Contributor + Foundry User", ID_TH)], dash="dashed",
        num_theme="gray", lab_w=CL_W - 40)
    hop(cv, yc(2), xr, xl, 8, "hosted agent telemetry to Agent 365", [("agent identity + OtelWrite", ID_TH), ("public :443", NET_PUB)], num_theme="indigo", lab_w=CL_W - 40)
    hop(cv, yc(3), xr, xl, 9, "autopilot acts as itself in M365", [("agent user + agent identity", ID_TH), ("M365", "gray"), ("preview", ST_PRE)], num_theme="teal", lab_w=CL_W - 40)
    hop(cv, yc(4), xr, xl, 2, "Work IQ over A2A", [("user (OBO)", ID_TH), ("public", NET_PUB), ("preview", ST_PRE)], num_theme="blue", lab_w=CL_W - 40)
    hop(cv, yc(5), xr, xl, 3, "SharePoint grounding", [("user (delegated)", ID_TH), ("public", NET_PUB), ("preview", ST_PRE)], num_theme="teal", lab_w=CL_W - 40)

    # ---- right corridor: Fabric
    xa, xb = C_X + C_W + 8, F_X - 8
    hop(cv, yc(4), xa, xb, 4, "Fabric IQ over MCP", [("user token / OAuth", ID_TH), ("private link (semantic model: public)", NET_PRIV), ("preview", ST_PRE)],
        num_theme="cyan", lab_w=CR_W - 30)
    hop(cv, yc(5), xa, xb, "x", "migrate to Fabric IQ", [("deprecating 2026-11-06", ST_DEP), ("unsupported under isolation", "gray")], dash="dashed", color=RED,
        num_theme="red", lab_w=CR_W - 30)

    # ---- routines <- event sources (top)
    ev_w = 400
    ev = Box(ev_w, "Event sources", sub="timer, recurring, GitHub issue, Teams channel message (connector-namespace connection)", icon="github", icon_pos="left",
             theme="orange", h=94, size=18, sub_size=13, icon_size=34).place(cv, rt.x + (rt.w - ev_w) / 2, FY + 18)
    xa5 = ev.cx
    y5 = FY + 160
    arrow(cv, [(xa5, ev.bottom + 4), (xa5, rt.y - 6)], sw=3, color=ORG)
    numbered(cv, xa5, y5, 5, theme="violet", d=30, size=17)
    chips_row(cv, xa5 + 270, y5 - 22, [("agent identity (creator = opt-in)", ID_TH), ("VNet projects supported", NET_PRIV)], 280)
    arrow(cv, [(rt.x - 4, rt.y + 60), (ep.right + 6, ep.y + 60)], sw=2.5, color=GRY, dash="dashed")

    # ---- legend (top left)
    lg = Card(1120, "How to read it", [
        "Red chips: the identity the hop runs as; blue chip: private path; orange: public; yellow: public but source-IP-filtered",
        "Violet chip: preview; red chip with a date: deprecation. Everything is delegated (on behalf of the user) unless the chip says agent identity",
    ], theme="gray", fill="soft", title_size=18, body_size=14)
    legend_y = FY + 12
    lg.place(cv, 0, legend_y)

    # ---- bottom band: Azure integration
    BY = ISY + ISH + 190
    band_x = C_X
    band_w = W - C_X
    BH = 300
    zone(cv, band_x, BY, band_w, BH, "Azure integration", theme="orange", style="dashed", fill="none", sw=2.5, title_size=24, icon="logic-apps", icon_size=34,
         pad=18)
    bw1 = 760
    fn = Card(bw1, "Azure Functions tool (queue pattern)", [
        "The agent writes a message to an input Storage queue; a queue-triggered function processes it and writes to an output queue",
        "Flex Consumption recommended (scale-to-zero, VNet identity-based)",
        "Standard agent setup only; not available in a toolbox",
    ], theme="orange", icon="functions", fill="soft", title_size=19, body_size=14, pad=14, icon_size=32, src=[S_FUNC])
    fn.place(cv, band_x + 22, BY + 76)
    la = Card(bw1 + 140, "Azure Logic Apps (Standard)", [
        "Agent action: the agent model source is a Foundry project; autonomous agents run on events or schedules across 1,400+ connectors",
        "A workflow becomes an agent tool: it must start with a Request trigger and end with a Response action",
        "Connector actions as tools through an MCP server (managed connectors without OAuth2, a single connector)",
    ], theme="orange", icon="logic-apps", badge="preview", fill="soft", title_size=19, body_size=14, pad=14, icon_size=32, src=[S_LA1, S_LA2])
    la.place(cv, fn.right + 22, BY + 76)
    note = Note(band_w - 22 - bw1 - 22 - (bw1 + 140) - 22 - 22, "As of 2026-11-03, Foundry names Logic Apps as the low-code migration target for the retiring Foundry Workflows (preview), which retire 2026-12-01.",
                kind="warn", title="Workflows retire", size=14, src=[S_LA1])
    note.place(cv, la.right + 22, BY + 76)
    # arrows 6 and 7
    ax6 = fn.x + 520
    arrow(cv, [(ax6, dt.bottom + 6), (ax6, fn.y - 6)], sw=3, color=ORG, start_head="arrow")
    numbered(cv, ax6, (dt.bottom + fn.y) / 2, 6, theme="orange", d=30, size=17)
    chips_row(cv, ax6 + 215, (dt.bottom + fn.y) / 2 - 22, [("project MI + function MI", ID_TH), ("Storage Queue Data Contributor", ID_TH), ("VNet supported", NET_PRIV)], 390)
    ax7 = la.x + 380
    arrow(cv, [(ax7, dt.bottom + 6), (ax7, la.y - 6)], sw=3, color=ORG, start_head="arrow")
    numbered(cv, ax7, (dt.bottom + la.y) / 2, 7, theme="orange", d=30, size=17)
    chips_row(cv, ax7 + 215, (dt.bottom + la.y) / 2 - 22, [("Foundry project = model source", ID_TH), ("unsupported under isolation", NET_PUB), ("preview", ST_PRE)], 390)

    # contrast note under the left island
    cs = Note(IL_W + CL_W - 40, "Copilot Studio is the contrast: the landing-zone article says it reaches a private Foundry over a delegated Power Platform private-network path "
                                "and needs no Activity exception. If public agent ingress is prohibited, don't use the public Activity route.", kind="info",
              title="Copilot Studio contrast", size=14, src=[S_ALZ])
    cs.place(cv, 0, BY + 24)
    return max(BY + BH, cs.bottom) + 56


# ----------------------------------------------------------------------------------------------------- 2 hop table
def _hops(cv, y):
    y = chapter(cv, y, "2  The identity and network path of every hop",
                f"The table behind the numbered arrows ({ASOF}); hops 1-9 are runtime calls, hop 10 is the publish-time setup")
    rows = [
        [("1", "blue"), "M365 / Teams user -> Azure Bot Service -> Foundry agent endpoint (Activity protocol)",
         "Signed-in M365 user via the Bot Service signed channel token; BotServiceRbac (the user needs an Azure role on the agent or project) or BotServiceTenant (a tenant user)",
         ("Public HTTPS, source-IP-filtered (when the project is private)", "yellow")],
        [("2", "blue"), "Agent -> Work IQ (preview)", "User (OBO); oauth2 connection with the Work IQ service principal / app registration (WorkIQAgent.Ask consent)",
         ("Public workiq.svc.cloud.microsoft; passes through the data proxy in a BYO VNet but is not private", "orange")],
        [("3", "teal"), "Agent -> SharePoint tool (preview)", "User (delegated), same tenant", ("Public, even in an isolated Foundry", "orange")],
        [("4", "cyan"), "Agent -> Fabric IQ / data agent (preview)", "User (UserEntraToken / AgentOnBehalfOfUser) or OAuth through a managed or custom app",
         ("Tenant / workspace private link (ontology: tenant only; semantic model: public only)", "indigo")],
        [("5", "violet"), "Routine -> agent", "Agent identity (default) or creator identity (opt-in at create time, permanent)", ("Foundry audience token; VNet projects supported", "indigo")],
        [("6", "orange"), "Agent -> Azure Function", "Project MI (writes the input queue) and the function's MI (writes the output queue): both Storage Queue Data Contributor",
         ("VNet supported", "indigo")],
        [("7", "orange"), "Logic Apps <-> agent (preview)", "Foundry project as the agent model source / workflow exposed as a tool (authentication details not captured in the sources read)",
         ("Logic Apps not supported under Foundry isolation; built-in actions can VNet-integrate", "orange")],
        [("8", "indigo"), "Hosted agent -> Agent 365 telemetry", "Agent identity holding the Agent365.Observability.OtelWrite app role", ("Public agent365.svc.cloud.microsoft :443", "orange")],
        [("9", "teal"), "Autopilot -> M365 workloads (preview)", "Agent user account (mailbox, calendar, Teams) + agent identity; admin consent governs the token", ("M365", "gray")],
        [("10", "gray"), "Foundry -> Azure Bot Service + M365 admin center (publish)", "Azure Bot Service Contributor (Foundry roles are insufficient) + Foundry User on the project; admin approval for the organization scheme",
         "Portal publish is unsupported for a private Foundry: REST with enable_m365_public_endpoint"],
    ]
    t = Table([("#", 60), ("Hop", 700), ("Identity / credential", 1300), ("Network path", 0)], rows, w=W, theme="blue", size=14, head_size=15,
              title="Identity used on each hop", title_size=22, align=["center", "left", "left", "left"])
    t.place(cv, 0, y)
    return t.bottom + 60


# ----------------------------------------------------------------------------------------------------- 3 publish
def _publish(cv, y):
    y = chapter(cv, y, "3  Publish a Foundry agent to Microsoft 365 Copilot and Teams",
                f"What publishing does, the two audience schemes, and the runtime path when the Foundry project is private ({ASOF})")
    seq = Sequence(cv, 0, y, [("M365 user", "gray", "user"), ("Teams / M365 Copilot", "blue", "teams"), ("Azure Bot Service", "gray", "bot"),
                              ("Foundry Activity route", "indigo", "foundry"), ("Active agent version", "green", "agent")],
                   spacing=345, head_w=200, step=62, size=15, label_size=14)
    seq.msg(0, 1, "User chats in Teams or Microsoft 365 Copilot", num=1)
    seq.msg(1, 2, "Microsoft 365 forwards the activity to Azure Bot Service", num=2)
    seq.msg(2, 3, "Public HTTPS to the Foundry Activity Protocol route", num=3, color=ORG)
    seq.note(2, 3, "A manually enabled, source-IP-filtered public route: Foundry checks the caller against the Bot Service / Microsoft 365 source IP ranges and fails closed",
             kind="warn")
    seq.note(3, 4, "Foundry validates the signed channel token and the BotServiceRbac / BotServiceTenant rule", kind="info")
    seq.msg(3, 4, "Route to the active agent version: models, tools and data stay private per the baseline", num=4)
    seq.msg(4, 3, "Agent response", dash="dashed", num=5)
    seq.msg(3, 2, "Response goes back through Azure Bot Service", dash="dashed", num=6)
    seq.msg(2, 1, "Reply appears in Teams / Copilot: no streaming, no citations", dash="dashed", num=7)
    yb = seq.end()
    n_priv = Note(1580, "Responses, A2A and MCP protocols stay private; outbound rules are unchanged. Microsoft 365 itself does not support private connectivity: "
                        "don't publish this way if public agent ingress is prohibited.", kind="gotcha", title="Only the Activity route is public", size=14,
                  src=[S_PUBVNET])
    n_priv.place(cv, 0, yb + 24)

    rx = 1640
    rw = W - rx
    st = Steps(rw, "Publish setup (portal, or REST for a private project)", [
        (1, "Prerequisites: the Microsoft.BotService resource provider is registered; you hold Azure Bot Service Contributor (Foundry roles are insufficient) and Foundry User on the project", "gray"),
        (2, "Publish: Foundry creates the Azure Bot Service resource, builds the Teams manifest, submits it to the catalogs and enables the activity protocol and an authorization scheme on the agent endpoint", "blue"),
        (3, "'Just you' = BotServiceRbac, no approval, under 'Your agents'. 'People in your organization' = BotServiceTenant: request to the M365 admin center, admin approves, under 'Built by your org'", "blue"),
        (4, "The stable endpoint serves the active version through version_selector (FixedRatio); 'Always use latest' is the default", "green"),
        (5, "Private project (public network access disabled): portal publish is unsupported; call the REST API with enable_m365_public_endpoint: true", "red"),
    ], theme_name="blue", icon="bot", size=14, gap=9, d=28, src=[S_PUB, S_PUBVNET])
    st.place(cv, rx, y)
    t = Table([("Aspect", 230), ("Just you", 0), ("People in your organization", 0)], [
        ["Authorization scheme", "BotServiceRbac", "BotServiceTenant"],
        ["publishScope", "Shared", "Tenant"],
        ["Admin approval", "none", "M365 admin center approval required"],
        ["Appears under", "Your agents", "Built by your org"],
        ["Who can use it", "each user needs the applicable Azure permission", "tenant users need no per-user Foundry RBAC"],
    ], w=rw, theme="blue", size=14, head_size=15, title="Two audience schemes", title_size=20, first_col_theme="blue")
    t.place(cv, rx, st.bottom + 24)
    nlim = Note(rw, "No streaming and no citations; file uploads and image generation don't work in Microsoft 365 (they work in Teams). The usual cause of a failed publish is "
                    "missing Azure Bot Service Contributor: it is separate from the Foundry roles.", kind="warn", title="Limits and the usual failure", size=14, src=[S_PUB])
    nlim.place(cv, rx, t.bottom + 24)
    return max(n_priv.bottom, nlim.bottom) + 60


# ----------------------------------------------------------------------------------------------------- 4 knowledge and governance surfaces
def _surfaces(cv, y):
    y = chapter(cv, y, "4  Work IQ, SharePoint, Agent 365 and Fabric: what each one needs",
                f"All delegated, all preview unless noted ({ASOF}); the full Work IQ handshake is in the canvas 'Microsoft IQ: the enterprise-context layer'")
    gap = 40
    cw = (W - 3 * gap) / 4
    wi = Card(cw, "Work IQ tool", [
        "A2A tool work_iq_preview; delegated only (OBO), no app-only; UserEntraToken is unsupported: use AgentOnBehalfOfUser or OAuth passthrough",
        "Endpoint workiq.svc.cloud.microsoft passes through the data proxy in a BYO VNet but is NOT private; not supported in network-isolated toolbox projects",
        "One-time: a Global Administrator (via PIM) provisions the Work IQ service principal (appId fdcc1f02-fc51-4226-8753-f668596af7f7), a single-tenant app registration and admin consent for WorkIQAgent.Ask; keep the secret in Key Vault",
        "Billing: Copilot Credits for the Work IQ API path; connector-backed tools may need M365 Copilot licences",
        "Connection fields can't be edited after creation",
    ], theme="orange", icon="iq", badge="preview", src=[S_WORKIQ])
    sp = Card(cw, "SharePoint tool", [
        "Delegated only, same tenant, ONE SharePoint tool per agent",
        "Uses the Microsoft Copilot Retrieval API: text only; .doc, .docx, .pptx, .pdf, .aspx and .one for semantic retrieval",
        "Needs a Microsoft 365 Copilot licence or pay-as-you-go",
        "! Does NOT work when the agent is published to Teams",
        "! Public endpoint even in an isolated Foundry; can't be placed in a toolbox",
        "Governed alternative: the Foundry IQ SharePoint knowledge source (indexed and ACL-aware, or remote through the same API): see the canvas 'Enterprise RAG / knowledge-grounded agent'",
    ], theme="teal", icon="sharepoint", badge="preview", src=[S_SP])
    a3 = Card(cw, "Agent 365 integration", [
        "Pillars: registry, access control, visualization, interoperability, security",
        "Foundry integration: registry sync (prompt and hosted agents) and autopilots (hosted agents only)",
        "Prerequisites: at least one M365 Copilot licence, Frontier preview enrolment, a Global Administrator enables Agent 365 and accepts the terms",
        "Controlled per Foundry resource through agent365Config; opt out with a365LoggingEnabled=false",
        "Hosted-agent telemetry: Agent 365 SDK + explicit telemetry config to agent365.svc.cloud.microsoft (or the AzureFrontDoor.Frontend tag), TCP 443",
        "Needs the Agent365.Observability.OtelWrite app role (appRoleId 8f71190c-00c8-461d-a63b-f74abde9ba52) on the Agent365Observability service principal, granted to the agent identity by a Global or Application Administrator; 2-5 min to propagate; 409 = already assigned",
        "Data residency: Foundry = Azure region; Agent 365 = Entra tenant geography",
    ], theme="indigo", icon="m365", badge="preview", src=[S_A365, S_A365PERM])
    fb = Card(cw, "Fabric IQ and the data agent", [
        "Fabric IQ tool fabric_iq_preview (OneLake catalog) replaces the Fabric data agent tool fabric_dataagent_preview, deprecated 2026-11-06 (as of 2026-11-03)",
        "Needs published items; F2+ capacity (or P1+ with Fabric enabled); data agent and its sources in the same region; same tenant; not where Power BI is the only Fabric workload",
        "Background mode only for data agents (models gpt-5.4 / gpt-5.5); results cross regions if the Foundry project and the Fabric workspace differ",
        "Auth: the incoming Entra user context (UserEntraToken / AgentOnBehalfOfUser) or OAuth through a managed or custom app; audience https://analysis.windows.net/powerbi/api, scope DataAgent.Execute.All (admin consent)",
        "user-entra-token is the toolbox authType for workspace-private data agent endpoints",
    ], theme="cyan", icon="fabric", badge="preview", src=[S_FIQ, S_FDA])
    r, b = row(cv, 0, y, [wi, sp, a3, fb], gap=gap)
    y2 = b + 36
    t = Table([("Fabric IQ item", 260), ("MCP URL pattern", 0), ("Network / VNet support", 440)], [
        [("Ontology", "cyan"), "https://{host}/v1/mcp/dataPlane/workspaces/{workspaceId}/items/{itemId}/ontologyEndpoint", ("tenant-level private link", "indigo")],
        [("Data agent", "cyan"), "https://{host}/v1/mcp/workspaces/{workspaceId}/dataagents/{dataAgentId}/agent", ("tenant- and workspace-level private link", "indigo")],
        [("Power BI semantic model", "cyan"), "https://{host}/v1/mcp/fabricaihub/integrations/m365", ("public access only", "orange")],
    ], w=2100, theme="cyan", size=14, head_size=15, title="Fabric IQ items and their MCP endpoints", title_size=22)
    t.place(cv, 0, y2)
    n = Note(W - 2100 - 40, "A workspace-private-link host looks like {workspaceId-without-dashes}.z{first2chars}.w.api.fabric.microsoft.com; otherwise the host is "
                            "usually api.fabric.microsoft.com. A direct data-agent MCP client may use a user or service-principal token (scope https://api.fabric.microsoft.com/.default).",
             kind="info", title="Hosts and direct clients", size=14, src=[S_FIQ])
    n.place(cv, 2140, y2)
    return max(t.bottom, n.bottom) + 60


# ----------------------------------------------------------------------------------------------------- sources
def _sources(cv, y):
    sources(cv, 0, y, [S_PUB, S_PUBVNET, S_WORKIQ, S_SP, S_A365, S_A365PERM, S_AUTO, S_ROUT, S_FIQ, S_FDA, S_FUNC, S_LA1, S_LA2, S_ALZ], w=W, cols=3)


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _map(cv, y)
    y = _hops(cv, y)
    y = _publish(cv, y)
    y = _surfaces(cv, y)
    _sources(cv, y)

