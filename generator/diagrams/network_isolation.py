"""Network isolation - inbound, outbound and perimeter controls for Foundry and Agent Service: public vs private endpoints
(+ private DNS), BYO VNet container injection vs managed VNet, Network Security Perimeter, on-premises access, tool
support, subnet sizing and order of operations."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="network-isolation", title="Network isolation", section="5", order=4,
    description="Inbound (public network access, private endpoints, private DNS), outbound (BYO VNet container injection vs managed VNet), Network Security Perimeter, on-premises access, tool support, subnet sizing and build order.",
    tags=["network", "private-endpoint", "vnet", "managed-vnet", "nsp", "dns"],
)

W = 3398          # canvas width: 6 columns of 533 px with 40 px gaps
GAP = 40
COL = 533
IND = THEMES["indigo"]
NET = IND.stroke   # network arrows
GRN = THEMES["green"].stroke
RED = THEMES["red"].stroke
MUT = "#868e96"


def cx(i: float) -> float:
    return i * (COL + GAP)


def sp(n: float) -> float:
    return n * COL + (n - 1) * GAP


# ---------------------------------------------------------------------------------------------------- helpers
def chapter(cv: Canvas, y: float, num: str, text: str, sub: str | None = None) -> float:
    """Full-width chapter heading; returns the y where content can start."""
    _, bottom = section_header(cv, 0, y, f"{num}  {text}", sub=sub, size=38, w=W, sub_size=18)
    return bottom + 30


def zone(cv: Canvas, x: float, y: float, w: float, h: float, title: str | None = None, *, theme="indigo",
         sub: str | None = None, style="dotted", fill="none", icon: str | None = None, title_size=22, sub_size=15,
         pad=16, sw=2, icon_size=30, title_w: float | None = None) -> El:
    """Explicit-size boundary (VNet, subnet, tenant, perimeter) with a title; draw it BEFORE its children."""
    th = THEMES[theme]
    bg, fs = "transparent", "solid"
    if fill == "hatch":
        bg, fs = th.fill, "hachure"
    elif fill == "solid":
        bg, fs = th.fill, "solid"
    elif fill == "soft":
        bg, fs = th.soft, "solid"
    with cv.group():
        el = cv.rect(x, y, w, h, stroke=th.stroke, fill=bg, style=fs, sw=sw, dash=style)
        tx = x + pad
        if icon:
            place_icon(cv, icon, x + pad, y + pad * 0.55, icon_size)
            tx += icon_size + 10
        if title:
            t = cv.text(tx, y + pad * 0.7, title, size=title_size, color=th.deep, wrap=title_w)
            if sub:
                cv.text(tx, t.bottom + 2, sub, size=sub_size, color=MUTED, wrap=title_w)
    return el


def nb(w: float, label: str, theme="indigo", *, sub: str | None = None, icon: str | None = None, h: float | None = None,
       shape="rect", fill="solid", dash="solid", size=16, sub_size=14, icon_pos="left", icon_size=30) -> Box:
    """Diagram node: centred label (+ optional sub line and icon)."""
    return Box(w, label, h=h, theme=theme, sub=sub, icon=icon, icon_pos=icon_pos, shape=shape, fill=fill, dash=dash,
               size=size, sub_size=sub_size, icon_size=icon_size)


def flow(cv: Canvas, a, b, *, color=NET, **kw) -> El:
    kw.setdefault("sw", 3)
    return connect(cv, a, b, color=color, **kw)


def cap(cv: Canvas, x: float, y: float, s: str, w: float, *, size=14, color=MUTED, align="left") -> El:
    """Wrapped caption of width w."""
    return cv.text(x, y, s, size=size, color=color, wrap=w, align=align, w=w)


def ink(cv: Canvas, x: float, y: float, s: str, *, size=16, color=INK, w: float | None = None, align="left",
        wrap: float | None = None) -> El:
    return cv.text(x, y, s, size=size, color=color, w=w, align=align, wrap=wrap)


def disc(cv: Canvas, cxx: float, cyy: float, label: str, *, d=40, theme="indigo", size=16) -> El:
    th = THEMES[theme]
    with cv.group():
        e = cv.ellipse(cxx - d / 2, cyy - d / 2, d, d, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        tw, thh = text_size(label, size)
        cv.text(cxx - tw / 2, cyy - thh / 2 + 1, label, size=size, color=th.deep)
    return e


def stub(cv: Canvas, label: str, url: str, x: float, y: float, w: float) -> float:
    """Clickable 'Learn:' line under a free-standing diagram; returns bottom y."""
    t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url, wrap=w)
    return t.bottom


# ---------------------------------------------------------------------------------------------------- 0 title + strip
def sec_title(cv: Canvas, y: float) -> float:
    _, bottom = title_block(cv, 0, 0, "Network isolation",
                            "Inbound, outbound and perimeter controls for Microsoft Foundry and Agent Service - as of 2026-11-03",
                            w=W)
    y = bottom + 34
    cards = [
        Card(COL, "Default: public in, public out", [
            "Inbound: any caller with a valid credential and the endpoint URL",
            "Egress: internet-accessible endpoints only; agent state in Microsoft-managed storage",
            "Nothing is private until you choose an option",
        ], theme="gray", icon="public-ip", src=[("Networking options", learn("agents/concepts/networking-options"))]),
        Card(COL, "Inbound controls", [
            "Public network access flag: Enabled, Enabled from selected IPs, Disabled",
            "Private endpoint (target 'account') plus 3 private DNS zones",
            "Optional NSP ring around the account",
        ], theme="indigo", icon="private-endpoint",
            src=[("Configure network isolation", learn("how-to/configure-private-link"))]),
        Card(COL, "Outbound: BYO VNet", [
            "Container injection into a subnet you delegate to Microsoft.App/environments",
            "You own IP ranges, peering, firewall and UDRs",
            "Covers hosted and prompt agents",
        ], theme="indigo", icon="vnet", src=[("Private networking for Agent Service", learn("agents/how-to/virtual-networks"))]),
        Card(COL, "Outbound: managed VNet", [
            "Microsoft-managed network in the Microsoft tenant; no NIC or subnet to run",
            "Isolation mode + outbound rules (fqdn, servicetag, privateendpoint)",
            "FQDN rules create a billed managed Azure Firewall",
        ], theme="indigo", icon="private-link", src=[("Managed virtual network", learn("how-to/managed-virtual-network"))]),
        Card(COL, "Perimeter: NSP", [
            "Network Security Perimeter restricts data-plane access",
            "Start in Transition (logs only), then switch to Enforced",
            "Control-plane operations may still succeed",
        ], theme="indigo", icon="nsp", badge="preview",
            src=[("Foundry in a network security perimeter", learn("how-to/add-foundry-to-network-security-perimeter"))]),
        Note(COL, "Network injection (BYO or managed) must be set when the Foundry account is created. It can't be added to an existing account or changed afterwards, so decide before you create.\nThere is no upgrade path from BYO VNet to managed VNet: redeploy.",
             kind="gotcha", title="Create-time only"),
    ]
    _, b = row(cv, 0, y, cards, gap=GAP)
    return b + 80


# ---------------------------------------------------------------------------------------------------- 1 big picture
def sec_big_picture(cv: Canvas, y: float) -> float:
    y = chapter(cv, y, "1", "The big picture - castle and moat",
                "Inbound drawbridge, platform keep, outbound moat. Choose controls per direction; the two outbound models are alternatives.")
    y0 = y
    XC, WC = 0, 400
    XG, WG = 520, 540
    PADR = 28
    XR, WK = 1220, 680
    XK = XR + PADR
    XO = XK + WK + PADR + 170
    WO = W - XO

    # ---- measure -----------------------------------------------------------------------------------------------
    inner = WG - 44
    seg_w = (inner - 20) / 3
    segs = [nb(seg_w, "Enabled", "gray", sub="any caller", h=84),
            nb(seg_w, "Selected IPs", "gray", sub="IPs + VNets", h=84),
            nb(seg_w, "Disabled", "indigo", sub="private endpoint only", h=84)]
    pe = nb(inner, "Private endpoint", "indigo", icon="private-endpoint", h=100,
            sub="sub-resource 'account'; same region and subscription as the VNet; only Approved carries traffic")
    dns = nb(inner, "3 private DNS zones, linked to the VNet", "indigo", icon="dns", h=100,
             sub="privatelink.cognitiveservices.azure.com, privatelink.openai.azure.com, privatelink.services.ai.azure.com")
    trust = nb(inner, "Trusted Azure services exception", "gray", icon="managed-identity", dash="dashed", fill="soft", h=100,
               sub="Microsoft.CognitiveServices, Microsoft.Search, Microsoft.MachineLearningServices - managed identity plus a role")

    kin = WK - 44
    kw2 = (kin - 16) / 2
    k_proj = nb(kw2, "Projects", "blue", icon="foundry", sub="isolation applies at account + project level", h=96)
    k_agent = nb(kw2, "Agent Service", "green", icon="agent", sub="prompt, hosted and workflow agents", h=96)
    k_cap = nb(kw2, "Capability hosts", "green", icon="gear", sub="account level, then project level; no inheritance", h=96)
    k_dp = nb(kw2, "Single-tenant data proxy", "indigo", icon="private-link", sub="one per project; every tool call routes through it", h=96)
    k_note = Note(kin, "Network injection is set at account creation and is immutable.", kind="gotcha", title="Create-time only", size=15)
    keep_h = 22 + 70 + k_proj.h + 16 + k_cap.h + 16 + k_note.h + 22
    ring_h = 52 + keep_h + PADR

    TITLE_H = 80
    a_agent = nb(290, "Agent subnet", "indigo", icon="subnet", h=130,
                 sub="delegated to Microsoft.App/environments; hosted-agent Micro VMs and the data proxy take IPs here")
    a_pe = nb(270, "PE subnet", "indigo", icon="private-endpoint", h=130, sub="private endpoints, one per resource; a separate subnet")
    res_defs = [("Azure Storage (blob)", "storage", "cyan"), ("Azure Cosmos DB (Sql)", "cosmos", "cyan"),
                ("Azure AI Search", "ai-search", "teal"), ("Key Vault (optional)", "key-vault", "red"),
                ("ACR (optional)", "acr", "gray"), ("App Insights via AMPLS (optional)", "app-insights", "violet")]
    RW = 230
    res = [nb(RW, n, th, icon=ic, h=64, size=15, icon_size=26) for n, ic, th in res_defs]
    res_block_h = 3 * 64 + 2 * 14
    A_h = TITLE_H + 14 + max(a_agent.h, res_block_h + 40) + 22

    mode1 = nb(300, "Allow internet outbound", "gray", sub="all internet egress allowed", h=84)
    mode2 = nb(300, "Allow only approved outbound", "indigo", sub="service tags + PEs + FQDN rules (ports 80 and 443)", h=96)
    rules = nb(250, "Outbound rules", "indigo", icon="policy", h=84, sub="fqdn | servicetag | privateendpoint")
    TW = 500
    t_pe = nb(TW, "Managed private endpoints", "indigo", icon="private-endpoint", h=80,
              sub="to your Cosmos DB, Storage and AI Search (auto-created in approved-only mode)")
    t_fw = nb(TW, "Managed Azure Firewall", "yellow", icon="firewall", h=80,
              sub="created with the first FQDN rule; you pay for it; ports 80 and 443 only")
    t_ag = nb(TW, "Application Gateway in your VNet", "indigo", icon="app-gateway", h=80,
              sub="private endpoint to the gateway, then on-premises (JFrog, Snowflake, private APIs)")
    mode_zone_h = 34 + mode1.h + 14 + mode2.h + 22
    B_h = TITLE_H + 14 + max(mode_zone_h, 3 * 80 + 2 * 14) + 22
    out_h = A_h + 50 + B_h

    # ---- inbound gate -----------------------------------------------------------------------------------------
    with cv.panel(XG, y0, title="Inbound controls", sub="who may reach the Foundry endpoint", theme="indigo",
                  style="dotted", fill="none", pad=22, title_size=24, sub_size=15, w=WG) as gate:
        t = cv.text(gate.ix, gate.iy, "Public network access (PNA) flag", size=17, color=IND.deep)
        seg_y = t.bottom + 8
        row(cv, gate.ix, seg_y, segs, gap=10)
        c = cap(cv, gate.ix, seg_y + segs[0].h + 8, "Disabled is the default for network-secured accounts and projects; it covers REST and WebSocket.", inner, size=14)
        pe.place(cv, gate.ix, c.bottom + 18)
        dns.place(cv, gate.ix, pe.bottom + 22)
        trust.place(cv, gate.ix, dns.bottom + 22)

    # ---- NSP ring + keep --------------------------------------------------------------------------------------
    ry = y0
    zone(cv, XR, ry, WK + 2 * PADR, ring_h, "Network Security Perimeter (optional)", theme="grape", style="dashed",
         icon="nsp", title_size=20, pad=14, icon_size=26)
    ky = ry + 52
    zone(cv, XK, ky, WK, keep_h, "Foundry account", sub="Microsoft.CognitiveServices/accounts (kind AIServices)", theme="blue",
         style="solid", fill="soft", icon="foundry", title_size=26, sub_size=15, pad=20)
    iy = ky + 22 + 70
    k_proj.place(cv, XK + 22, iy)
    k_agent.place(cv, XK + 22 + kw2 + 16, iy)
    k_cap.place(cv, XK + 22, iy + k_proj.h + 16)
    k_dp.place(cv, XK + 22 + kw2 + 16, iy + k_proj.h + 16)
    k_note.place(cv, XK + 22, iy + k_proj.h + 16 + k_cap.h + 16)

    # ---- outbound A / B ---------------------------------------------------------------------------------------
    zA = zone(cv, XO, y0, WO, A_h, "A. BYO VNet - container injection", sub="you run the network: IP ranges, peering, firewall, UDRs",
              theme="indigo", style="solid", fill="soft", icon="vnet", title_size=26, sub_size=15, pad=20)
    ay = y0 + TITLE_H + 14
    a_agent.place(cv, XO + 22, ay)
    a_pe.place(cv, a_agent.right + 80, ay)
    rx = a_pe.right + 70
    zone(cv, rx - 12, ay - 6, 2 * RW + 14 + 24, res_block_h + 46, "Your resources (PNA Disabled)", theme="cyan", style="dotted", title_size=17, pad=10)
    for i, r in enumerate(res):
        r.place(cv, rx + (i % 2) * (RW + 14), ay + 34 + (i // 2) * (64 + 14))
    flow(cv, a_agent, a_pe, label="Private Link", label_size=14, a_side="right", b_side="left")
    arrow(cv, [(a_pe.right + 6, a_pe.cy), (rx - 18, a_pe.cy)], color=NET, sw=3)

    by = y0 + A_h + 50
    zB = zone(cv, XO, by, WO, B_h, "B. Managed VNet - Microsoft-managed", sub="Microsoft tenant; no NIC or subnet visible in your subscription",
              theme="indigo", style="solid", fill="soft", icon="private-link", title_size=26, sub_size=15, pad=20)
    bty = by + TITLE_H + 14
    zone(cv, XO + 14, bty - 6, 300 + 16, mode_zone_h, "Isolation mode", theme="indigo", style="dotted", title_size=17, pad=10)
    mode1.place(cv, XO + 22, bty + 34)
    mode2.place(cv, XO + 22, mode1.bottom + 14)
    rules.place(cv, mode1.right + 90, bty + 34 + (mode1.h + 14 + mode2.h - rules.h) / 2)
    for i, tb in enumerate((t_pe, t_fw, t_ag)):
        tb.place(cv, XO + WO - 22 - TW, bty + i * (80 + 14))
    flow(cv, mode2, rules, a_side="right", b_side="left")
    for tb in (t_pe, t_fw, t_ag):
        flow(cv, rules, tb, a_side="right", b_side="left", route="elbow")

    # ---- callers ----------------------------------------------------------------------------------------------
    c_net = nb(WC, "Internet", "gray", icon="public-ip", sub="any caller with a credential and the URL", h=96)
    c_vpn = nb(WC, "On-prem, VPN, ExpressRoute, Bastion jump host", "gray", icon="vpn-gateway", sub="private routing to the private endpoint", h=110)
    c_ci = nb(WC, "CI runner in the VNet", "gray", icon="devops", sub="azd needs data-plane and ACR push from inside", h=110)
    c_net.place(cv, XC, segs[0].cy - c_net.h / 2)
    c_vpn.place(cv, XC, pe.y + 0.3 * pe.h - c_vpn.h / 2)
    c_ci.place(cv, XC, c_vpn.bottom + 34)
    flow(cv, c_net, segs[0], a_side="right", b_side="left", label="public path", label_size=14)
    flow(cv, c_vpn, pe, a_side="right", b_side="left", route="elbow", tb=0.3, label="private path", label_size=14, label_t=0.25)
    flow(cv, c_ci, pe, a_side="right", b_side="left", route="elbow", tb=0.7)
    arrow(cv, [(gate.right + 6, pe.cy), (XK - 6, pe.cy)], color=NET, sw=3, label="to the account endpoint", label_size=14,
          label_wrap=130, label_pos="above")

    # Teams / M365 reaches the account through the source-IP-filtered public route, not through the private endpoint
    c_m365 = nb(WC, "Teams and Microsoft 365", "violet", icon="teams", sub="through Azure Bot Service", h=96, dash="dashed")
    yt = max(ry + ring_h + 170, gate.y + gate.h + 84)
    c_m365.place(cv, XC, yt - c_m365.h / 2)
    xt = XK + WK / 2
    arrow(cv, [(c_m365.right + 6, yt), (xt, yt), (xt, ky + keep_h + 6)], color=NET, sw=3, dash="dashed")
    cap(cv, c_m365.right + 24, yt - 54, "Source-IP-filtered public route to the Activity Protocol route only; everything else stays private", 600, size=14, color=INK)

    # legend
    ly = yt + 60
    arrow(cv, [(XG, ly + 10), (XG + 70, ly + 10)], color=NET, sw=3)
    ink(cv, XG + 84, ly, "request or data path", size=14)
    arrow(cv, [(XG + 330, ly + 10), (XG + 400, ly + 10)], color=NET, sw=3, dash="dashed")
    ink(cv, XG + 414, ly, "alternative, optional or exception path", size=14)

    # ---- egress fork ------------------------------------------------------------------------------------------
    a_mid, b_mid = zA.cy, zB.cy
    xj = XK + WK + PADR + 70
    yj = (a_mid + b_mid) / 2
    arrow(cv, [(XK + WK + 6, yj), (xj - 20, yj)], color=NET, sw=3, end_head=None)
    arrow(cv, [(xj, yj - 20), (xj, a_mid), (XO - 6, a_mid)], color=NET, sw=3, dash="dashed")
    arrow(cv, [(xj, yj + 20), (xj, b_mid), (XO - 6, b_mid)], color=NET, sw=3, dash="dashed")
    disc(cv, xj, yj, "or", d=40, theme="indigo")
    disc(cv, xj + 36, a_mid, "A", d=30, theme="indigo", size=15)
    disc(cv, xj + 36, b_mid, "B", d=30, theme="indigo", size=15)

    bottom = max(y0 + out_h, ly + 40)
    return bottom + 50


# ---------------------------------------------------------------------------------------------------- 2 decide
def sec_decide(cv: Canvas, y: float) -> float:
    y = chapter(cv, y, "2", "Which model do I need?",
                "Egress decides the isolation story and inbound follows. Decision tree on the left, scenario-to-template map on the right.")
    y0 = y
    CY = 300
    d1 = nb(280, "Isolate egress?", "indigo", shape="diamond", h=170, size=18)
    d2 = nb(360, "Manage own IPs, firewall, UDR?", "indigo", shape="diamond", h=190, size=18)
    d3 = nb(360, "Internet outbound or approved-only?", "indigo", shape="diamond", h=200, size=18)
    no_box = nb(280, "Public egress + optional private endpoint", "gray", h=120,
                sub="the PE secures only the inbound path; templates 41 and 10")
    byo = nb(360, "BYO VNet (container injection)", "indigo", icon="vnet", h=110,
             sub="you control IPs, firewall and UDRs; templates 15, 11, 16")
    mvn = nb(330, "Managed VNet", "indigo", icon="private-link", h=110, sub="Microsoft-managed; template 18; no portal UI")
    m1 = nb(280, "Allow internet outbound", "gray", h=104, sub="unrestricted egress is acceptable")
    m2 = nb(280, "Allow only approved outbound", "indigo", h=104, sub="curated destinations; limits data exfiltration")
    d1.place(cv, 0, y0 + CY - d1.h / 2)
    d2.place(cv, 420, y0 + CY - d2.h / 2)
    byo.place(cv, 420, y0 + 20)
    mvn.place(cv, 920, y0 + CY - mvn.h / 2)
    d3.place(cv, 1340, y0 + CY - d3.h / 2)
    no_box.place(cv, 0, y0 + CY + 150)
    m1.place(cv, 1200, y0 + CY + 170)
    m2.place(cv, 1520, y0 + CY + 170)
    flow(cv, d1, d2, a_side="right", b_side="left", label="yes", label_size=16)
    flow(cv, d1, no_box, a_side="bottom", b_side="top", label="no", label_size=16, label_pos="right")
    flow(cv, d2, byo, a_side="top", b_side="bottom", label="yes", label_size=16, label_pos="right")
    flow(cv, d2, mvn, a_side="right", b_side="left", label="no, or IP ranges overlap", label_size=14, label_wrap=110)
    flow(cv, mvn, d3, a_side="right", b_side="left")
    ym = d3.bottom + 30
    arrow(cv, [(d3.cx, d3.bottom + 4), (d3.cx, ym)], color=NET, sw=3, end_head=None)
    arrow(cv, [(m1.cx, ym), (m1.cx, m1.y - 6)], color=NET, sw=3, start_head=None)
    arrow(cv, [(m2.cx, ym), (m2.cx, m2.y - 6)], color=NET, sw=3, start_head=None)
    arrow(cv, [(m1.cx, ym), (m2.cx, ym)], color=NET, sw=3, end_head=None)
    ink(cv, m1.cx - 8 - text_size("broad connectivity", 14)[0], ym + 6, "broad connectivity", size=14)
    ink(cv, m2.cx + 8, ym + 6, "curated list", size=14)
    stub(cv, "Networking options by scenario", learn("agents/concepts/networking-options"), 0, no_box.bottom + 24, 500)
    tree_bottom = m2.bottom

    # ---- scenario -> template table (right) ------------------------------------------------------------------
    tx = 1860
    t_goal = Table(
        [("Your goal", 470), ("Recommended option", 400), ("Deploy with", 428)],
        [
            ["Fastest path to a working agent, no isolation", "Public, Microsoft-managed storage", "Deploy your first hosted agent quickstart (azd or VS Code)"],
            ["Keep agent data in your own Azure resources, no isolation", "Public, bring-your-own storage (standard)", "41-standard-agent-setup"],
            ["Restrict who can call the endpoint; public egress is acceptable", "Public egress with a private endpoint", "10-private-network-basic"],
            ["Full isolation, no public egress; you control the network and bring your own data resources", "BYO VNet + BYO data resources (network-secured standard)", "15-private-network-standard-agent-setup"],
            ["Full isolation; you control the network but don't want to manage data resources", "BYO VNet + platform-managed data resources", "11-private-network-basic-vnet"],
            ["Full isolation, but you can't manage IP ranges or your IP space overlaps", ("Managed VNet", "indigo"), "18-managed-virtual-network"],
            ["Full isolation behind an API gateway", "BYO VNet with Azure API Management", "16-private-network-standard-agent-apim-setup"],
            ["Reach on-premises resources from agents", "BYO VNet plus VPN or ExpressRoute", "15-private-network-standard-agent-setup + Access on-premises resources"],
        ], w=W - tx, theme="indigo", size=14, head_size=15, title="Pick by goal: scenario, option and Bicep template", title_size=22)
    t_goal.place(cv, tx, y0)
    stub(cv, "Networking options for Agent Service", learn("agents/concepts/networking-options"), tx, t_goal.bottom + 8, 700)
    chips = ChipFlow(["15a-private-network-evaluation-only-setup", "19-private-network-agent-tools (private MCP, OpenAPI, Functions, A2A)",
                      "30-customer-managed-keys", "32-customer-managed-keys-user-assigned-identity", "42/43-*-agent-setup-with-customization",
                      "05-custom-policy-definitions", "01-connections"], W - tx, theme="gray", size=14, gap=8)
    ink(cv, tx, t_goal.bottom + 40, "More templates (microsoft-foundry/foundry-samples/infrastructure/infrastructure-setup-bicep, Terraform mirror)", size=14, color=MUTED)
    chips.place(cv, tx, t_goal.bottom + 66)

    # ---- egress model comparison --------------------------------------------------------------------------------
    cy0 = max(tree_bottom + 70, chips.y + chips.h + 50)
    t_cmp = Table(
        [("Aspect", 170), ("Public egress", 330), ("BYO VNet (container injection)", 450), ("Managed VNet", 450)],
        [
            ["Inbound choices", "Public (optionally selected IPs) or a private endpoint", "Private endpoint in your VNet", "Private endpoint in your VNet"],
            ["Best for", "Prototyping; a PE secures only the inbound path", "Full isolation; you control IP ranges, peering, firewall and UDR",
             "Full isolation without managing IP ranges, or when your IP space overlaps"],
            ["Who runs the network", "No isolated network: agents reach internet-accessible endpoints", "You: subnets, IPs, delegation", "Microsoft: subnets, IPs, delegation"],
            ["Control", "-", "Own firewall, UDRs, peering, delegation", "Fixed: no own firewall or UDR; no outbound logging yet; Application Gateway for on-prem"],
            ["Complexity", "-", "Subnet delegation to ACA, capability hosts, IP class limits, /27 or larger subnet", "Low; the Azure portal can't create it"],
            ["IP overlap", "-", "Non-overlapping ranges required", "Not a concern"],
            ["Cost", "-", "Your own network and firewall", "Private Link + managed Azure Firewall (when you use FQDN rules)"],
        ], w=1400, theme="indigo", size=14, head_size=15, title="Egress models compared (as of 2026-11-03)", title_size=22,
        first_col_theme="indigo")
    t_cmp.place(cv, 0, cy0)
    stub(cv, "Managed vs custom network", learn("how-to/managed-virtual-network"), 0, t_cmp.bottom + 8, 600)
    n1 = Note(sp(2.3), "Network isolation applies at Foundry account + project level: hosted agents, prompt agents and the other resources in the account. With BYO VNet you pick platform-managed data resources (multitenant, no capacity planning) or BYO data resources (Storage, AI Search, Cosmos DB in your tenant).",
              kind="info", title="Scope of isolation", src=[("Networking options", learn("agents/concepts/networking-options"))])
    n2 = Note(sp(2.3), "With public egress, adding a private endpoint secures only the inbound path: callers reach the endpoint privately, but agent egress is not isolated. When egress is isolated in a VNet, inbound access also goes through a private endpoint.",
              kind="warn", title="Private endpoint is not egress isolation")
    nx = 1400 + 40
    n1.place(cv, nx, cy0)
    n2.place(cv, nx, n1.bottom + 24)
    return max(t_cmp.bottom + 40, n2.bottom) + 40


# ---------------------------------------------------------------------------------------------------- 3 inbound
def _bar(cv: Canvas, x: float, y: float, h: float, w: float = 16, theme="indigo") -> None:
    th = THEMES[theme]
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2, round_=False)


def _pna_states(cv: Canvas, y: float) -> float:
    """Three mini diagrams for the public network access flag; returns bottom y of the zones."""
    ZH, ZW = 214, COL
    # --- 1: Enabled
    x = cx(0)
    zone(cv, x, y, ZW, ZH, "PNA = Enabled", theme="gray", style="dotted", title_size=20, icon="public-ip", icon_size=26)
    a = nb(150, "Internet", "gray", icon="public-ip", h=70, size=15, icon_size=24).place(cv, x + 22, y + 100)
    f = nb(160, "Foundry endpoint", "blue", icon="foundry", h=70, size=15, icon_size=24).place(cv, x + ZW - 22 - 160, y + 100)
    flow(cv, a, f, label="allowed", label_size=14)
    # --- 2: Enabled from selected IP addresses
    x = cx(1)
    zone(cv, x, y, ZW, ZH, "PNA = Enabled from selected IPs", theme="indigo", style="dotted", title_size=20, icon="nsg", icon_size=26)
    al = nb(150, "Allowed IPs and VNets", "indigo", h=62, size=15).place(cv, x + 22, y + 62)
    ot = nb(150, "Other callers", "gray", h=62, size=15).place(cv, x + 22, y + 142)
    f = nb(160, "Foundry endpoint", "blue", icon="foundry", h=142, size=15, icon_size=24).place(cv, x + ZW - 22 - 160, y + 62)
    gx = x + 236
    _bar(cv, gx, y + 56, 18)
    _bar(cv, gx, y + 112, 96)
    arrow(cv, [(al.right + 6, al.cy), (f.x - 6, al.cy)], color=NET, sw=3)
    arrow(cv, [(ot.right + 6, ot.cy), (gx - 4, ot.cy)], color=RED, sw=3, end_head="bar")
    ink(cv, ot.right + 10, ot.cy - 24, "blocked", size=14, color=RED)
    # --- 3: Disabled + private endpoint
    x = cx(2)
    zone(cv, x, y, ZW, ZH, "PNA = Disabled + private endpoint", theme="indigo", style="dotted", fill="soft", title_size=20, icon="private-endpoint", icon_size=26)
    net = nb(150, "Internet", "gray", icon="public-ip", h=60, size=15, icon_size=24).place(cv, x + 22, y + 60)
    cl = nb(150, "Client in a VNet or on-prem", "gray", h=64, size=15).place(cv, x + 22, y + 138)
    gx = x + 258
    _bar(cv, gx, y + 56, 150)
    pe = nb(104, "PE", "indigo", icon="private-endpoint", h=64, size=15, icon_size=24).place(cv, gx + 8 - 52, y + 138)
    f = nb(120, "Foundry endpoint", "blue", icon="foundry", icon_pos="top", h=146, size=14, icon_size=26).place(cv, x + ZW - 22 - 120, y + 58)
    arrow(cv, [(net.right + 6, net.cy), (gx - 4, net.cy)], color=RED, sw=3, end_head="bar")
    ink(cv, net.right + 14, net.cy - 26, "blocked", size=14, color=RED)
    arrow(cv, [(cl.right + 4, cl.cy), (pe.x - 6, pe.cy)], color=NET, sw=3)
    arrow(cv, [(pe.right + 6, pe.cy), (f.x - 6, pe.cy)], color=NET, sw=3)
    return y + ZH


def sec_inbound(cv: Canvas, y: float) -> float:
    y = chapter(cv, y, "3", "Inbound: who can reach the endpoint",
                "The public network access (PNA) flag decides whether a private endpoint is required; applies to REST and WebSocket.")
    y0 = y
    zb = _pna_states(cv, y0)
    cy1 = zb + 16
    c1 = Card(COL, "Enabled", [
        "Any caller with a valid credential and the endpoint URL reaches the account",
        "The default for a Foundry resource created without any networking configuration",
    ], theme="gray", icon="public-ip", src=[("Networking options", learn("agents/concepts/networking-options"))])
    c2 = Card(COL, "Enabled from selected IP addresses", [
        "Also called Selected networks: you list the IP addresses and VNets that may connect",
        "A middle setting between public and private; other callers are blocked",
    ], theme="indigo", icon="nsg", src=[("Configure network isolation", learn("how-to/configure-private-link"))])
    c3 = Card(COL, "Disabled + private endpoint", [
        "Callers must come through an approved private endpoint",
        "The default for network-secured accounts and projects; covers REST and WebSocket",
    ], theme="indigo", icon="private-endpoint", src=[("Configure network isolation", learn("how-to/configure-private-link"))])
    hh = max(c.h for c in (c1, c2, c3))
    for i, c in enumerate((c1, c2, c3)):
        c.place(cv, cx(i), cy1, h=hh)

    pe_card = Card(COL, "Private endpoint rules", [
        "Target resource type is labeled 'account' in the portal; select your Foundry resource",
        "Create it in the same region and subscription as the VNet",
        "Only Approved endpoints send traffic; approving needs Contributor or Owner on the Foundry resource, else it stays Pending",
        "Creating needs Network Contributor on the VNet and subnet; Private DNS Zone Contributor for the zones",
        "Don't use 172.17.0.0/16 for the VNet (Docker bridge)",
        "Removing a PE does not make the resource public; enabling public access does not remove PEs",
    ], theme="indigo", icon="private-endpoint", src=[("Configure network isolation", learn("how-to/configure-private-link"))])
    reach = Card(COL, "Ways in to a private Foundry", [
        "# Trusted Azure services (network rule exception)",
        "Microsoft.CognitiveServices, Microsoft.Search and Microsoft.MachineLearningServices can reach a restricted resource when their managed identity has a role",
        "# From people and pipelines",
        "VPN gateway (point-to-site or site-to-site) or ExpressRoute",
        "Azure Bastion to a jump box VM inside the VNet (RDP or SSH from the browser)",
        "Self-hosted GitHub or Azure DevOps runners in the VNet: azd needs data-plane and ACR push from inside",
        "Local dev: VPN or Bastion (azd ai agent run, ports 8088 and 8087)",
    ], theme="indigo", icon="vpn-gateway", src=[("Configure network isolation", learn("how-to/configure-private-link")),
                                               ("Private networking for Agent Service", learn("agents/how-to/virtual-networks"))])
    pol = Table([("Azure Policy built-in (Foundry Tools)", 330), ("Effect", 203)], [
        ["Azure AI Services resources should use Azure Private Link", "Audit, Disabled"],
        ["Configure Cognitive Services accounts with private endpoints", "DeployIfNotExists, Disabled"],
        ["Configure Cognitive Services accounts to disable public network access", "Disabled, Modify"],
        ["Azure AI Services resources should restrict network access", "Audit, Deny, Disabled"],
    ], w=COL, theme="indigo", size=14, head_size=15, title="Policies to enforce it", title_size=20)
    n_portal = Note(COL, "Some portal flows can't configure PE-only accounts; use the SDK, the CLI or the Bicep/Terraform templates.",
                    kind="warn", title="Portal limits")
    pe_card.place(cv, cx(3), y0)
    reach.place(cv, cx(4), y0)
    pol.place(cv, cx(5), y0)
    stub(cv, "Policy reference for Foundry Tools", learn("azure/ai-services/policy-reference", base=""), cx(5), pol.bottom + 6, COL)
    n_portal.place(cv, cx(5), pol.bottom + 34)
    return max(cy1 + hh, pe_card.bottom, reach.bottom, n_portal.bottom) + 60


# ---------------------------------------------------------------------------------------------------- 4 dns + required PEs
def _dns_sequence(cv: Canvas, x: float, y: float) -> float:
    seq = Sequence(cv, x, y, [("Client (VNet or on-prem)", "gray", "users"), ("DNS resolver", "indigo", "dns-resolver"),
                              ("Azure DNS 168.63.129.16", "indigo", "dns"), ("Private endpoint", "indigo", "private-endpoint"),
                              ("Foundry account", "blue", "foundry")], spacing=345, head_w=225, head_h=64, step=64, size=15, label_size=14)
    seq.msg(0, 1, "resolve the account FQDN", num=1)
    seq.msg(1, 2, "the name is a CNAME to the privatelink alias; ask the zone", num=2)
    seq.msg(2, 1, "A record = private IP of the PE", dash="dashed", num=3, note="from the private DNS zone linked to the VNet")
    seq.msg(1, 0, "private IP, not the public one", dash="dashed", num=4)
    seq.msg(0, 3, "HTTPS to the private IP on port 443", num=5)
    seq.msg(3, 4, "Private Link to the account", num=6)
    seq.note(0, 4, "Same connection string inside and outside the VNet: from outside it resolves to the public endpoint, from the VNet that hosts the private endpoint it resolves to the PE's private IP.", kind="info", size=14)
    return seq.end()


def _pe_map(cv: Canvas, x: float, y: float, w: float) -> float:
    rows = [
        ("Foundry account PE", "sub-resource: account", "Foundry account", "projects and Agent Service", "foundry", "blue",
         ["privatelink.cognitiveservices.azure.com", "privatelink.openai.azure.com", "privatelink.services.ai.azure.com"]),
        ("Azure Storage PE", "sub-resource: blob", "Azure Storage", "files and vector store files", "storage", "cyan",
         ["privatelink.blob.core.windows.net"]),
        ("Azure Cosmos DB PE", "sub-resource: Sql", "Azure Cosmos DB for NoSQL", "conversation and agent state", "cosmos", "cyan",
         ["privatelink.documents.azure.com"]),
        ("Azure AI Search PE", "sub-resource: searchService", "Azure AI Search", "knowledge and vector indexes", "ai-search", "teal",
         ["privatelink.search.windows.net"]),
    ]
    heights = [190, 112, 112, 112]
    H = 100 + sum(heights) + 24
    zone(cv, x, y, w, H, "Required private endpoints: standard (BYO data) network-isolated agent setup",
         sub="all four live in the PE subnet; each private DNS zone is linked to the VNet", theme="indigo", style="dotted",
         icon="private-endpoint", title_size=24, sub_size=15, pad=20)
    pw, tw = 400, 400
    xp, xt = x + 30, x + w - 30 - tw
    ink(cv, xp, y + 86, "Private endpoint", size=16, color=IND.deep)
    ink(cv, xp + pw + 110, y + 86, "Private DNS zone(s) linked to the VNet", size=16, color=IND.deep)
    ink(cv, xt, y + 86, "Target resource", size=16, color=IND.deep)
    ry = y + 116
    for (pl, ps, tl, ts, ti, tt, zones), hh in zip(rows, heights):
        pe = nb(pw, pl, "indigo", icon="private-endpoint", sub=ps, h=84).place(cv, xp, ry)
        tg = nb(tw, tl, tt, icon=ti, sub=ts, h=84).place(cv, xt, ry)
        flow(cv, pe, tg, a_side="right", b_side="left", label="Private Link", label_size=14)
        mid = (pe.right + tg.x) / 2
        cy = ry + 58
        for z in zones:
            ch = Chip(z, theme="indigo", size=14, icon="dns", icon_size=20, fill="soft")
            ch.place(cv, mid - ch.w / 2, cy)
            cy += ch.h + 6
        ry += hh
    return y + H


def sec_dns(cv: Canvas, y: float) -> float:
    y = chapter(cv, y, "4", "Private DNS and the required private endpoints",
                "A private endpoint only helps once the name resolves to it. Link the private DNS zones to the VNet and create the four PEs.")
    y0 = y
    ink(cv, 0, y0, "What happens when a client resolves a private Foundry name", size=22, color=IND.deep)
    sb = _dns_sequence(cv, 0, y0 + 44)
    stub(cv, "Configure network isolation (DNS configuration)", learn("how-to/configure-private-link"), 0, sb + 10, 800)

    tx = cx(3)
    t_dns = Table(
        [("Private link resource", 230), ("Sub-resource", 150), ("Private DNS zone(s)", 640), ("Public forwarder zone(s)", sp(3) - 1020)],
        [
            [("Foundry", "indigo"), "account", "privatelink.cognitiveservices.azure.com\nprivatelink.openai.azure.com\nprivatelink.services.ai.azure.com",
             "cognitiveservices.azure.com\nopenai.azure.com\nservices.ai.azure.com"],
            [("Azure AI Search", "indigo"), "searchService", "privatelink.search.windows.net", "search.windows.net"],
            [("Azure Cosmos DB (NoSQL)", "indigo"), "Sql", "privatelink.documents.azure.com", "documents.azure.com"],
            [("Azure Storage", "indigo"), "blob", "privatelink.blob.core.windows.net", "blob.core.windows.net"],
            [("Key Vault (if used)", "gray"), "vault", "privatelink.vaultcore.azure.net (named as an example in the deep dive)", "-"],
            [("Azure SQL (example)", "gray"), "-", "privatelink.database.windows.net (named in the deep dive)", "-"],
            [("ACR, Application Insights (via Azure Monitor Private Link Scope)", "gray"), "-", "zone names not stated in the Learn pages used here - check docs", "-"],
        ], w=sp(3), theme="indigo", size=14, head_size=15, title="Private DNS zones as documented", title_size=22)
    t_dns.place(cv, tx, y0)
    stub(cv, "Set up private networking for Foundry Agent Service", learn("agents/how-to/virtual-networks"), tx, t_dns.bottom + 8, 900)
    n1 = Note(sp(1.5) - 20, "Private endpoints for Storage, Cosmos DB and AI Search are NOT created when you deploy the Foundry resource in the portal. Create them on each resource, and link every private DNS zone to the VNet.",
              kind="gotcha", title="Not auto-created")
    n2 = Note(sp(1.5) - 20, "Delegate the privatelink subdomain to the VNet's private DNS zone (or add the A records) and forward to Azure DNS 168.63.129.16. A custom DNS server overrides linked private zones: use an Azure DNS Private Resolver (centralized DNS architecture) or, when the DNS server is an Azure VM, a conditional forwarder to 168.63.129.16.",
              kind="info", title="Custom or on-premises DNS", src=[("Evaluations in a VNet", learn("concepts/evaluation-virtual-network"))])
    ny = t_dns.bottom + 40
    nh = max(n1.h, n2.h)
    n1.place(cv, tx, ny, h=nh)
    n2.place(cv, tx + n1.w + 40, ny, h=nh)
    top2 = max(sb + 50, ny + nh + 40)

    zb = _pe_map(cv, 0, top2, sp(3))
    validate = Card(COL, "Validate the endpoints", [
        "+ PE connection status is Approved",
        "+ nslookup <endpoint> returns the private IP (10.x in the Foundry IQ tutorial)",
        "+ Test-NetConnection <pe-ip> -Port 443 succeeds",
        "403 after the PE works? The network path is fine: check RBAC on the project",
    ], theme="green", icon="monitor", src=[("Configure network isolation", learn("how-to/configure-private-link"))])
    optional = Card(COL, "Add only if you use them", [
        "Key Vault: sub-resource vault",
        "ACR for hosted-agent images, and Application Insights through an Azure Monitor Private Link Scope",
        "Any resource that a tool (MCP, OpenAPI, Functions, A2A) touches",
        "Hosted-agent ACR can be private for projects created after 2026-06-25 (as of 2026-11-03)",
    ], theme="gray", icon="key-vault", dash="dashed", src=[("Private networking for Agent Service", learn("agents/how-to/virtual-networks"))])
    byo = Card(COL, "BYO data is part of the deal", [
        "Standard setups require all three BYO resources (Storage, AI Search, Cosmos DB) for end-to-end isolation",
        "All data processed by Agent Service is stored at rest in them, in your Azure tenant",
        "Basic setup: platform-managed storage; inbound isolation can still be applied to every setup",
    ], theme="cyan", icon="storage", src=[("Foundry Agent environment setup", learn("agents/environment-setup"))])
    for i, c in enumerate((validate, optional, byo)):
        c.place(cv, cx(3 + i), top2, h=max(validate.h, optional.h, byo.h))
    r1b = top2 + max(validate.h, optional.h, byo.h)
    caph = Card(COL, "Capability hosts", [
        "Account-level capability host first, then project-level; the project reads the BYO connections (no inheritance)",
        "One per scope; a second name returns 409; no update - delete and recreate",
        "Connection properties: authType (for example AAD), category, target, metadata.ResourceId",
        "Project properties: threadStorageConnections (Cosmos DB), vectorStoreConnections (AI Search), storageConnections (Storage), optional aiServicesConnections",
        "! Calls to tool endpoints outside Foundry through your VNet need a project-level capability host, else 'name or host unknown'",
        "Capability settings API (2026-07-15-preview): the caller needs Storage Blob Data Contributor + Cosmos DB Operator; settings can't be updated on an existing project",
        "Portal and the legacy capability-host API provision with the project managed identity",
    ], theme="green", icon="gear", badge="preview", src=[("Capability hosts", learn("agents/concepts/capability-hosts")),
                                                         ("Private networking for Agent Service", learn("agents/how-to/virtual-networks"))])
    cosmos = Card(COL, "Cosmos DB for NoSQL sizing", [
        "Account throughput limit >= 3,000 RU/s (provisioned or serverless)",
        "Each project gets 3 to 5 containers at 1,000 RU/s each",
        "# At provisioning (Classic)",
        "thread-message-store, system-thread-message-store, agent-entity-store",
        "# First Responses-API agent runs (New, up to 2 more)",
        "agent-definitions-v1, run-state-v1",
        "Classic and New runtimes use different containers; 2 projects with Responses-API agents = 10,000 RU/s, classic-only = 6,000 RU/s",
        "Names are prefixed with the project ID in 'use your own resources'; too few RU/s fails provisioning",
        "! Docs disagree: standard-agent-setup also says 'five containers each 1,000 RU/s' next to 'at least 3,000'",
    ], theme="cyan", icon="cosmos", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
                                         ("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
    roles = Card(COL, "Providers and roles to line up", [
        "# Register resource providers",
        "Microsoft.KeyVault, Microsoft.CognitiveServices, Microsoft.Storage, Microsoft.MachineLearningServices, Microsoft.Search, Microsoft.Network, Microsoft.App, Microsoft.ContainerService",
        "Add Microsoft.Bing for Bing grounding; the IQ tutorial also lists Microsoft.ContainerRegistry and Microsoft.DocumentDB",
        "# Roles per the environment setup page",
        "Create account + project: Foundry Account Owner",
        "RBAC on Cosmos DB, Search, Storage: Role Based Access Control Administrator or Owner (roleAssignments/write)",
        "Create or edit agents: Foundry User; call endpoints only: Foundry Agent Consumer",
        "Autodeploy templates use Managed Identity and a Microsoft-managed Key Vault by default",
    ], theme="red", icon="managed-identity", src=[("Foundry Agent environment setup", learn("agents/environment-setup"))])
    r2y = r1b + 40
    hh2 = max(caph.h, cosmos.h, roles.h)
    for i, c in enumerate((caph, cosmos, roles)):
        c.place(cv, cx(3 + i), r2y, h=hh2)
    return max(zb, r2y + hh2) + 60


# ---------------------------------------------------------------------------------------------------- 5 hub and spoke
def sec_hubspoke(cv: Canvas, y: float) -> float:
    y = chapter(cv, y, "5", "Reference topology: hub and spoke",
                "A shared firewall in a hub VNet, peered to a spoke VNet that holds the delegated agent subnet and the private endpoints. A standalone project without a hub differs: adapt peering and firewall.")
    y0 = y
    XA, WA = 0, 380
    XH, WH = 470, 860
    XS, WS = 1530, 1040
    XV = 2720
    WV = W - XV

    # ---- hub -----------------------------------------------------------------------------------------------------
    bw = (WH - 44 - 20) / 2
    gw = nb(bw, "VPN or ExpressRoute gateway", "indigo", icon="vpn-gateway", h=104, sub="point-to-site, site-to-site or ExpressRoute from on-prem and developers")
    dnsr = nb(bw, "Azure DNS Private Resolver", "indigo", icon="dns-resolver", h=104, sub="centralized DNS: resolves the privatelink zones and forwards to 168.63.129.16")
    bast = nb(bw, "Azure Bastion", "indigo", icon="bastion", h=104, sub="AzureBastionSubnet; RDP or SSH to a jump box VM inside the VNet")
    fw = nb(bw, "Azure Firewall or another NVA", "yellow", icon="firewall", h=104, sub="inspects and controls egress from the injected subnet")
    dns6 = nb(WH - 44, "Private DNS zones, linked to the hub and the spoke", "indigo", icon="dns", h=70,
              sub="Foundry (3 zones), AI Search, Cosmos DB, Storage")
    hub_h = 78 + 104 + 18 + 104 + 18 + dns6.h + 22
    zone(cv, XH, y0, WH, hub_h, "Hub VNet - shared services", sub="firewall, gateway, DNS and Bastion are shared by every spoke", theme="indigo",
         style="dotted", icon="vnet", title_size=26, sub_size=15, pad=20)
    gw.place(cv, XH + 22, y0 + 78)
    dnsr.place(cv, XH + 22 + bw + 20, y0 + 78)
    bast.place(cv, XH + 22, y0 + 78 + 104 + 18)
    fw.place(cv, XH + 22 + bw + 20, y0 + 78 + 104 + 18)
    dns6.place(cv, XH + 22, y0 + 78 + 2 * 104 + 2 * 18)

    # ---- spoke -----------------------------------------------------------------------------------------------------
    ag_w = WS - 44
    vm = nb(300, "Hosted-agent Micro VM", "green", icon="vm", h=100, sub="own NIC in this subnet: 1 IP per concurrent session")
    dp = nb(300, "Single-tenant data proxy", "indigo", icon="private-link", h=100, sub="one per project; every tool call routes through it")
    ch_nsg = Chip("NSGs: allow Entra ID dependencies", theme="gray", size=14, icon="nsg", icon_size=22)
    ch_udr = Chip("UDRs and peering are yours", theme="gray", size=14)
    ag_h = 78 + 100 + 22
    pe_h = 78 + 4 * 64 + 3 * 14 + 22
    bot_h = 78 + 100 + 22
    spoke_h = 84 + ag_h + 24 + pe_h + 24 + bot_h + 22
    zone(cv, XS, y0, WS, spoke_h, "Spoke VNet - Foundry", sub="template default 192.168.0.0/16; any private range with room for both subnets", theme="indigo",
         style="solid", fill="soft", icon="vnet", title_size=26, sub_size=15, pad=20)
    ay = y0 + 84
    zone(cv, XS + 22, ay, ag_w, ag_h, "Agent subnet 192.168.0.0/24", sub="delegated to Microsoft.App/environments; /24 recommended", theme="indigo",
         style="dotted", fill="soft", icon="subnet", title_size=20, sub_size=14, pad=14, icon_size=26)
    vm.place(cv, XS + 22 + 20, ay + 78)
    dp.place(cv, vm.right + 20, ay + 78)
    ch_nsg.place(cv, dp.right + 24, ay + 92)
    ch_udr.place(cv, dp.right + 24, ay + 92 + ch_nsg.h + 12)

    py = ay + ag_h + 24
    zone(cv, XS + 22, py, ag_w, pe_h, "PE subnet 192.168.1.0/24", sub="private endpoints for the Foundry account and each BYO resource", theme="indigo",
         style="dotted", fill="soft", icon="private-endpoint", title_size=20, sub_size=14, pad=14, icon_size=26)
    pes = []
    pe_defs = [("PE: Foundry account", "sub-resource: account"), ("PE: Azure Storage", "sub-resource: blob"),
               ("PE: Azure Cosmos DB", "sub-resource: Sql"), ("PE: Azure AI Search", "sub-resource: searchService")]
    for i, (lab, sb_) in enumerate(pe_defs):
        b = nb(440, lab, "indigo", icon="private-endpoint", sub=sb_, h=64, icon_size=26)
        b.place(cv, XS + 22 + ag_w - 20 - 440, py + 78 + i * (64 + 14))
        pes.append(b)
    opt = Card(470, "Only if you use them", [
        "Key Vault (vault)",
        "ACR and Application Insights (via an Azure Monitor Private Link Scope)",
        "Resources your tools touch (MCP, OpenAPI, Functions, A2A)",
    ], theme="gray", dash="dashed", fill="soft", body_size=15, title_size=18)
    opt.place(cv, XS + 22 + 20, py + 78)

    by = py + pe_h + 24
    half = (ag_w - 20) / 2
    zone(cv, XS + 22, by, half, bot_h, "Runner and jump-box subnet", sub="CI and Bastion access from inside the VNet", theme="indigo", style="dotted",
         fill="soft", icon="subnet", title_size=20, sub_size=14, pad=14, icon_size=26)
    runner = nb((half - 60) / 2, "Self-hosted runner", "gray", icon="vm", h=100, size=15, sub="GitHub or Azure DevOps", icon_size=26)
    jump = nb((half - 60) / 2, "Jump box VM", "gray", icon="vm", h=100, size=15, sub="reached through Bastion", icon_size=26)
    runner.place(cv, XS + 22 + 20, by + 78)
    jump.place(cv, runner.right + 20, by + 78)
    zone(cv, XS + 22 + half + 20, by, half, bot_h, "MCP subnet (optional)", sub="template 19: private MCP", theme="orange", style="dashed",
         fill="soft", icon="subnet", title_size=20, sub_size=14, pad=14, icon_size=26)
    mcp = nb(half - 40, "Private MCP server", "orange", icon="container-apps", h=100, size=15,
             sub="Azure Container Apps, internal-only ingress; subnet delegated to Microsoft.App/environments", icon_size=26)
    mcp.place(cv, XS + 22 + half + 20 + 20, by + 78)

    # ---- services behind the private endpoints -----------------------------------------------------------------------
    zone(cv, XV, py, WV, pe_h, "Reached over Private Link", sub="public network access Disabled on each", theme="cyan", style="dotted",
         icon="private-link", title_size=22, sub_size=15, pad=16)
    svc_defs = [("Foundry account", "projects, Agent Service, capability hosts", "foundry", "blue"),
                ("Azure Storage", "files and vector store files", "storage", "cyan"),
                ("Azure Cosmos DB for NoSQL", "conversation and agent state", "cosmos", "cyan"),
                ("Azure AI Search", "knowledge and vector indexes", "ai-search", "teal")]
    for pe, (lab, sb_, ic, th) in zip(pes, svc_defs):
        s = nb(WV - 44 - 40, lab, th, icon=ic, sub=sb_, h=64, icon_size=26)
        s.place(cv, XV + 22 + 40, pe.y)
        flow(cv, pe, s, a_side="right", b_side="left", label="Private Link", label_size=14)

    # ---- callers --------------------------------------------------------------------------------------------------
    c_on = nb(WA, "On-prem network and developers", "gray", icon="users", sub="point-to-site or site-to-site VPN, or ExpressRoute", h=100)
    c_br = nb(WA, "Admin or developer browser", "gray", icon="browser", sub="RDP or SSH through Azure Bastion", h=100)
    c_on.place(cv, XA, gw.cy - c_on.h / 2)
    c_br.place(cv, XA, bast.cy - c_br.h / 2)
    flow(cv, c_on, gw, a_side="right", b_side="left", label="VPN or ExpressRoute", label_size=14, label_wrap=100)
    flow(cv, c_br, bast, a_side="right", b_side="left", label="RDP or SSH", label_size=14, label_wrap=100)

    # ---- peering, egress, internet ----------------------------------------------------------------------------------
    arrow(cv, [(XH + WH + 6, y0 + 150), (XS - 6, y0 + 150)], color=NET, sw=3, start_head="arrow", end_head="arrow",
          label="VNet peering", label_size=14, dash="dotted")
    arrow(cv, [(XS + 22 - 4, fw.cy), (fw.right + 6, fw.cy)], color=THEMES["yellow"].stroke, sw=3, label="egress through your firewall",
          label_size=14, label_wrap=150, label_pos="above")
    inet = nb(400, "Internet and non-Azure APIs", "gray", icon="public-ip", h=100,
              sub="allow outbound HTTPS in the firewall, or add a NAT gateway for controlled egress")
    inet.place(cv, fw.x + (bw - 400) / 2 if False else XH + WH - 22 - 400, y0 + hub_h + 70)
    arrow(cv, [(fw.cx, fw.bottom + 4), (fw.cx, inet.y - 6)], color=THEMES["yellow"].stroke, sw=3, label="allow-listed", label_size=14,
          label_pos="right")
    n_fw = Note(WH, "Allow control-{region}.identity.azure.net, {region}.login.microsoft.com and login.microsoftonline.com (plus the Managed Identity FQDNs from the Azure Container Apps firewall article, or the AzureActiveDirectory service tag). Add matching NSG outbound rules for Entra ID. Verify that the firewall does no TLS inspection: a self-signed certificate breaks provisioning and runtime.",
                kind="warn", title="Firewall and NSG rules for the agent subnet", size=14,
                src=[("Private networking for Agent Service", learn("agents/how-to/virtual-networks"))])
    n_fw.place(cv, XH, inet.bottom + 28)

    # CI runner reaches the self-hosted runner in the spoke
    c_ci = nb(WA, "GitHub Actions or Azure DevOps", "gray", icon="devops", h=100, sub="runs-on: self-hosted, inside the VNet")
    c_ci.place(cv, XA, runner.cy - c_ci.h / 2)
    arrow(cv, [(c_ci.right + 6, runner.cy), (runner.x - 6, runner.cy)], color=NET, sw=3, label="pipeline jobs", label_size=14, label_pos="above")

    # ---- notes (top right) ------------------------------------------------------------------------------------------
    n1 = Note(WV, "Hub-and-spoke with a shared firewall is the common topology. A standalone Foundry project has no hub, so its layout differs: adapt peering and firewall to your own VNet design.",
              kind="info", title="Adapt it to your network", src=[("Configure network isolation", learn("how-to/configure-private-link"))])
    n2 = Note(WV, "Local development against a private endpoint: point-to-site VPN, or Bastion to a dev VM in the VNet (azd ai agent run, forward ports 8088 and 8087). Peered VNets must not overlap; if overlap is unavoidable use a managed VNet.",
              kind="tip", title="Reaching it", src=[("Deep dive: Agent Service networking", learn("agents/concepts/agents-networking-deep-dive"))])
    n1.place(cv, XV, y0)
    n2.place(cv, XV, n1.bottom + 24)

    # legend
    ly = by + 6
    arrow(cv, [(XV, ly + 10), (XV + 70, ly + 10)], color=NET, sw=3)
    ink(cv, XV + 84, ly, "request or data path", size=14)
    arrow(cv, [(XV, ly + 46), (XV + 70, ly + 46)], color=THEMES["yellow"].stroke, sw=3)
    ink(cv, XV + 84, ly + 36, "egress to the internet", size=14)
    arrow(cv, [(XV, ly + 82), (XV + 70, ly + 82)], color=NET, sw=3, dash="dotted", start_head="arrow")
    ink(cv, XV + 84, ly + 72, "peering", size=14)
    return max(y0 + spoke_h, n_fw.bottom, c_ci.bottom) + 60


# @@NEXT@@


def build(cv: Canvas) -> None:
    y = sec_title(cv, 0)
    y = sec_big_picture(cv, y)
    y = sec_decide(cv, y)
    y = sec_inbound(cv, y)
    y = sec_dns(cv, y)
    y = sec_hubspoke(cv, y)
    sources(cv, 0, y + 40, [("Networking options for Agent Service", learn("agents/concepts/networking-options"))], w=W, cols=3)
