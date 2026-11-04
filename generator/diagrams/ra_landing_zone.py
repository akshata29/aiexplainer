"""Microsoft Foundry in an Azure landing zone: management groups, platform vs workload landing zones, hub-spoke
topology with numbered flows, who owns what, private DNS and egress control, and the Agent Service gotchas.
Part 2 (ra_landing_zone_part_2.py) covers ownership models, policy guardrails, vending, AI Landing Zones and Well-Architected."""
from __future__ import annotations

import os

from generator.xd import *
from generator.xd import theme as get_theme

META = dict(
    id="ra-landing-zone", title="Foundry in an Azure landing zone", section="3", order=3,
    description="Platform vs workload landing zones for Microsoft Foundry: management groups, the hub-spoke topology with "
                "numbered flows, who owns what, private DNS and egress control, and the Agent Service gotchas.",
    tags=["landing-zone", "hub-spoke", "private-dns", "ownership", "egress", "agent-service"],
)

W = 3600
AC = "azure/architecture"
CAF = "azure/cloud-adoption-framework"

# ----------------------------------------------------------------------------------------------------- citations
S_ALZ = ("Baseline Foundry chat in an Azure landing zone (Architecture Center)",
         learn("ai-ml/architecture/baseline-microsoft-foundry-landing-zone", base=AC))
S_BASE = ("Baseline Microsoft Foundry chat reference architecture",
          learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC))
S_PLAN = ("Foundry rollout across my organization", learn("concepts/planning"))
S_CAF_LZ = ("What is an Azure landing zone? (CAF)", learn("ready/landing-zone", base=CAF))
S_CAF_AI = ("Architecture and governance for AI (CAF)", learn("ai/ready", base=CAF))
S_CAF_SHARE = ("AI platform sharing decision guidance (CAF)",
               learn("ai/platform/ai-platform-sharing-isolation-colocation", base=CAF))
S_VEND = ("Subscription vending (CAF)", learn("ready/landing-zone/design-area/subscription-vending", base=CAF))
S_PLDNS = ("Private Link and DNS integration at scale (CAF)",
           learn("ready/azure-best-practices/private-link-and-dns-integration-at-scale", base=CAF))
S_MODEL_POL = ("Built-in policies for model deployment", learn("how-to/model-deployment-policy"))
S_CUSTOM_POL = ("Custom policy definitions for Foundry", learn("how-to/custom-policy-definition"))
S_POL_REF = ("Azure Policy built-ins for Foundry Tools", learn("policy-reference", base="azure/ai-services"))
S_ARCH = ("Microsoft Foundry architecture", learn("concepts/architecture"))
S_SAS = ("Standard agent setup", learn("agents/concepts/standard-agent-setup"))
S_VNET = ("Network-secured agent setup (BYO VNet)", learn("agents/how-to/virtual-networks"))
S_NETOPT = ("Agent networking options", learn("agents/concepts/networking-options"))
S_PRIVLINK = ("Configure private link for Foundry", learn("how-to/configure-private-link"))
S_AILZ = ("AI Landing Zones (GitHub)", "https://github.com/Azure/AI-Landing-Zones")
S_AILZ_DOCS = ("AI Landing Zones documentation", "https://azure.github.io/AI-Landing-Zones/")
S_AILZ_NET = ("AI Landing Zones: network design",
              "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/network-isolation/")
S_AILZ_CFG = ("AI Landing Zones: deployment settings",
              "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/configuration/")
S_CAF_PLAN = ("Plan for AI adoption (CAF)", learn("ai/plan", base=CAF))
S_ZT = ("Zero Trust network for web applications with Azure Firewall and Application Gateway",
        learn("example-scenario/gateway/application-gateway-before-azure-firewall", base=AC))
S_AILZ_AGENT = ("AI Landing Zones: Agent Landing Zone", "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/")
S_AILZ_PLAN = ("AI Landing Zones: planning", "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/planning/")
S_AILZ_GW = ("AI Landing Zones: AI Gateway Landing Zone", "https://azure.github.io/AI-Landing-Zones/ai-gateway-landing-zone/")
S_AILZ_FAQ = ("AI Landing Zones: FAQ", "https://azure.github.io/AI-Landing-Zones/architecture/faq/")
S_AILZ_CHECK = ("AI Landing Zones: design checklist",
                "https://azure.github.io/AI-Landing-Zones/architecture/design-checklist/")


# ----------------------------------------------------------------------------------------------------- helpers
class Node(Rect2):
    """A hand-composed shape with a connector-friendly bounding box."""

    def __init__(self, x, y, w, h, el=None):
        self.x, self.y, self.w, self.h, self.el = x, y, w, h, el

    @property
    def bind_target(self):
        return self.el


def pill(cv, x, y, text, th="orange", size=12, right=False, pad=7, solid=True):
    """Small unregistered tag (does not take part in overlap checks). Returns (w, h)."""
    t = get_theme(th)
    tw, hh = text_size(text, size)
    w, h = tw + 2 * pad, hh + 6
    if right:
        x -= w
    with cv.group():
        cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill if solid else "transparent", style="solid", sw=1.5, rough=0)
        cv.text(x + pad, y + 3, text, size=size, color=t.deep)
    return w, h


def pills_row(cv, x, y, labels, th="gray", size=12, gap=8, max_w=None):
    """Left-to-right pills; wraps to a new row when max_w is exceeded. Returns bottom y."""
    cx, cy, rowh = x, y, 0
    for lab in labels:
        tw, _ = text_size(lab, size)
        if max_w and cx + tw + 14 > x + max_w and cx > x:
            cx, cy = x, cy + rowh + 6
        w, h = pill(cv, cx, cy, lab, th, size)
        cx += w + gap
        rowh = h
    return cy + rowh


def leaf(cv, x, y, w, h, title, lines=(), th="gray", icon=None, chips=(), dashed=False, bold=False, chip_th=None):
    """Subscription / resource tile used in the management-group tree and platform panels."""
    t = get_theme(th)
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=t.stroke, fill=t.soft, style="solid", sw=3 if bold else 2,
                    dash="dashed" if dashed else "solid")
        tx = x + 12
        if icon:
            place_icon(cv, icon, x + 10, y + 10, 30)
            tx = x + 48
        tl = wrap_text(title, w - (tx - x) - 10, 16)
        cv.text(tx, y + 9, "\n".join(tl), size=16, color=t.deep)
        cy = max(y + 9 + len(tl) * 20 + 3, y + 46 if icon else 0)
        for ln in lines:
            ll = wrap_text(ln, w - 24, 13)
            cv.text(x + 12, cy, "\n".join(ll), size=13, color="#343a40")
            cy += len(ll) * 16.3 + 2
        if chips:
            cy = pills_row(cv, x + 12, max(cy + 3, y + h - 6 - 26 * max(1, len(chips) // 3)), chips, chip_th or th, 12,
                           max_w=w - 24)
    cv.register(f"leaf:{title}", x, y, w, h)
    return Node(x, y, w, h, r)


def tree_edges(cv, parent, children, gap=30, color="#868e96"):
    px, py = parent.cx, parent.bottom
    yb = py + gap
    cv.line((px, py), (px, yb), stroke=color, sw=2)
    xs = [c.cx for c in children] + [px]
    if max(xs) - min(xs) > 1:
        cv.line((min(xs), yb), (max(xs), yb), stroke=color, sw=2)
    for c in children:
        cv.line((c.cx, yb), (c.cx, c.y), stroke=color, sw=2)


def flow_card(cv, x, y, w, n, title, text, th="gray", num_th="ink", size=14, min_h=0):
    """Numbered explanation card (legend for the numbered flows in the diagram)."""
    t = get_theme(th)
    tl = wrap_text(title, w - 70, 18)
    bl = wrap_text(text, w - 28, size)
    h = max(14 + len(tl) * 22.5 + 8 + len(bl) * size * 1.25 + 14, min_h)
    with cv.group():
        cv.rect(x, y, w, h, stroke=t.stroke, fill=t.soft, style="solid", sw=2)
        numbered(cv, x + 28, y + 28, n, theme=num_th, d=34, size=19)
        cv.text(x + 54, y + 12, "\n".join(tl), size=18, color=t.deep)
        cv.text(x + 14, y + 14 + max(len(tl) * 22.5, 34) + 6, "\n".join(bl), size=size, color="#1e1e1e")
    cv.register(f"flow:{n}", x, y, w, h)
    return Node(x, y, w, h)


def panel_offset(*specs):
    """Where do nested panels start their content? specs: dicts of cv.panel kwargs (outermost first)."""
    probe = Canvas("probe")
    x = y = 0.0
    stack = []
    ps = []
    for sp in specs:
        cm = probe.panel(x, y, **sp)
        p = cm.__enter__()
        stack.append(cm)
        ps.append(p)
        x, y = p.ix, p.iy
    for cm in reversed(stack):
        cm.__exit__(None, None, None)
    return ps


# ----------------------------------------------------------------------------------------------------- sections
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Microsoft Foundry in an Azure landing zone",
        "The platform team owns the plumbing, the workload team owns Foundry: management groups, hub-spoke network, ownership, "
        "private DNS, egress and Agent Service gotchas. Policy, rollout and AI Landing Zones are in part 2 (facts as of 2026-11-03)",
        icon="foundry", w=W)
    y = bottom + 46
    cw, gap = 688, 40
    cards = [
        Card(cw, "AI needs no special landing zone", [
            "CAF: AI workloads don't require a different Azure landing zone architecture or governance model",
            "No AI-specific management groups: internet-facing AI workloads go under Online, internal ones under Corp",
            "Extend the baseline policies with AI-service policies (Foundry models, Foundry Tools, AI Search, VMs) "
            "through the MG hierarchy",
        ], theme="grape", icon="landing-zone", src=[("Architecture and governance for AI (CAF)", S_CAF_AI[1])]),
        Card(cw, "Workload team owns Foundry", [
            "Recommended: the workload owns the Foundry resource, its projects, Agent Service and the BYO dependencies",
            "Not recommended: one Foundry resource per business group with delegated projects per workload "
            "(resource-organization and cost-allocation limits)",
            "Production default: one Foundry resource per workload boundary",
        ], theme="blue", icon="foundry", src=[("Foundry in a landing zone (Architecture Center)", S_ALZ[1])]),
        Card(cw, "Platform team owns the plumbing", [
            "Hub Azure Firewall and Bastion, the spoke VNet (creation, peering, DNS settings), UDRs, private DNS zones, "
            "DDoS Protection",
            "Azure Policy constraints and DeployIfNotExists (DINE) policies on the workload subscription",
            "Most of these were workload-owned in the baseline architecture",
        ], theme="yellow", icon="firewall", src=[("Foundry in a landing zone (Architecture Center)", S_ALZ[1])]),
        Card(cw, "DNS is the gotcha", [
            "Agent Service doesn't use the spoke VNet's DNS settings: link a DNS Private Resolver ruleset to the spoke",
            "Deploy the capability host only after the dependency FQDNs resolve to their private endpoints, "
            "otherwise the deployment fails",
            "DINE policies that fill private DNS zones are best-effort, with no SLA",
        ], theme="indigo", icon="dns-resolver", src=[("Foundry in a landing zone (Architecture Center)", S_ALZ[1])]),
        Card(cw, "Keep the dependencies local", [
            "Cosmos DB, Storage and AI Search for Agent Service remain workload resources",
            "Don't consolidate them as platform resources to optimise cost",
            "Agent Service manages them exclusively: no other component or workload should use them",
        ], theme="cyan", icon="cosmos", src=[("Foundry in a landing zone (Architecture Center)", S_ALZ[1])]),
    ]
    r, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    legend(cv, 0, y, [("Platform team (yellow)", "yellow"), ("Workload team (blue)", "blue"),
                      ("Management group / policy (grape)", "grape"), ("Networking (indigo)", "indigo"),
                      ("Identity and security (red)", "red"), ("Agents (green)", "green"), ("Data (cyan)", "cyan"),
                      ("Observability (violet)", "violet")], size=16, gap=30)
    cv.text(0, y + 30, "In the topology diagram, panel colour shows who owns the resource. Orange MOVED tag = workload-owned "
                       "in the baseline architecture, platform-owned in a landing zone. Green SHARED tag = created by one "
                       "team, used by the other.", size=14, color="#495057")
    return y + 72


def _mg(cv, y):
    r, b = section_header(cv, 0, y, "1  Tenant, management groups and subscriptions",
                          sub="An Azure landing zone = one platform landing zone + one workload landing zone per workload. "
                              "Azure Policy and RBAC are assigned on management groups and inherited downwards.",
                          size=34, w=W)
    y = b + 30
    # banner: unified identity, security and governance
    with cv.panel(0, y, title="Unified identity, security and governance", theme="gray", style="dashed", fill="soft",
                  pad=16, title_size=20, w=W) as ban:
        chips = [Chip("Microsoft Entra", theme="red", size=16), Chip("Microsoft Defender", theme="red", size=16, icon="defender"),
                 Chip("Microsoft Purview", theme="red", size=16, icon="compliance"),
                 Chip("Microsoft Agent 365", theme="red", size=16)]
        cx = ban.ix + 590
        for c in chips:
            c.place(cv, cx, ban.iy - 40)
            cx += c.w + 14
        cv.text(cx + 10, ban.iy - 36, "across Azure, Microsoft, multicloud and on-premises (CAF conceptual diagram)",
                size=14, color="#495057")
    y = ban.bottom + 36

    # --- tree
    yr, y1, y2, y3 = y, y + 112, y + 230, y + 362
    root = Box(420, "Tenant root group", h=70, theme="grape", icon="management-group", icon_pos="left", size=20).place(
        cv, 1590, yr)
    pill(cv, root.x - 10, root.y + 22, "Azure Policy", "grape", 14, right=True)
    pill(cv, root.right + 10, root.y + 22, "Azure RBAC", "red", 14)
    plat = Box(330, "Platform", h=64, theme="grape", icon="management-group", icon_pos="left").place(cv, 345, y1)
    wlz = Box(480, "Workload landing zones", h=64, theme="grape", icon="management-group", icon_pos="left").place(
        cv, 1880, y1)
    sbx = Box(300, "Sandbox", h=64, theme="grape", icon="management-group", icon_pos="left").place(cv, 2950, y1)
    dec = Box(310, "Decommissioned", h=64, theme="grape", icon="management-group", icon_pos="left").place(cv, 3290, y1)
    tree_edges(cv, root, [plat, wlz, sbx, dec], gap=34)

    names = ["Security", "Management", "Identity", "Connectivity"]
    pch = []
    for i, n in enumerate(names):
        pch.append(Box(240, n, h=60, theme="grape", icon="management-group", icon_pos="left", size=18).place(
            cv, i * 260, y2))
    tree_edges(cv, plat, pch, gap=34)
    wch = []
    for x, w, n in ((1350, 520, "Corp (Internal)"), (1910, 520, "Online"), (2470, 420, "Local")):
        wch.append(Box(w, n, h=60, theme="grape", icon="management-group", icon_pos="left", size=18).place(cv, x, y2))
    tree_edges(cv, wlz, wch, gap=34)

    lh = 134
    leaf(cv, 0, y3, 240, lh, "Security subscription", ["Microsoft Sentinel, Log Analytics workspaces, dashboards"],
         "yellow", "subscription")
    leaf(cv, 260, y3, 240, lh, "Management subscription",
         ["Central Log Analytics workspaces and dashboards; baseline alerts by policy"], "yellow", "subscription")
    leaf(cv, 520, y3, 240, lh, "Identity subscription", ["VNets with domain services, Recovery Services vaults"],
         "yellow", "subscription")
    leaf(cv, 780, y3, 240, lh, "Connectivity subscription",
         ["DDoS Protection, Azure DNS, VPN / ExpressRoute gateways, Azure Firewall, peered hubs"], "yellow",
         "subscription", bold=True)
    for c, lf in zip(pch, (0, 260, 520, 780)):
        cv.line((c.cx, c.bottom), (c.cx, y3), stroke="#868e96", sw=2)
    leaf(cv, 1350, y3, 520, lh, "Workload landing zone subscriptions", ["From the CAF reference diagram:"],
         "blue", "subscription", chips=["A1", "P1", "A2"])
    leaf(cv, 1910, y3, 520, lh, "This chat workload (example placement)",
         ["Internet-facing: public Application Gateway IP. Each environment = 1+ subscriptions"], "blue", "subscription",
         chips=["Dev", "Test", "Prod"], dashed=True, bold=True)
    leaf(cv, 2470, y3, 420, lh, "Local workloads", ["C1: Azure Local clusters", "A1: applications"], "blue",
         "subscription")
    leaf(cv, 2950, y3, 300, lh, "Sandbox subscriptions", ["Sandbox subscription 1", "Sandbox subscription 2"], "gray",
         "subscription")
    leaf(cv, 3290, y3, 310, lh, "Decommissioned subscription", ["Retired subscriptions wait here"], "gray",
         "subscription")
    for c in wch:
        cv.line((c.cx, c.bottom), (c.cx, y3), stroke="#868e96", sw=2)
    cv.line((sbx.cx, sbx.bottom), (sbx.cx, y3), stroke="#868e96", sw=2)
    cv.line((dec.cx, dec.bottom), (dec.cx, y3), stroke="#868e96", sw=2)

    # common toolset
    yt = y3 + lh + 24
    lbl = "Every subscription repeats a common toolset (CAF reference diagram):"
    cv.text(0, yt, lbl, size=15, color="#495057")
    pills_row(cv, text_size(lbl, 15)[0] + 24, yt - 3, ["Action Groups", "Alerts", "Cost Management", "Role assignment",
                                                       "Policy assignment", "Network Watcher", "Defender for Cloud",
                                                       "Azure Update Manager"], "gray", 14, gap=10)
    yn = yt + 52
    ws, gap = [600, 600, 1140, 1140], 40
    cards = [
        Card(ws[0], "Platform landing zone", [
            "Management-group hierarchy + centralized resources (connectivity, security monitoring, identity, "
            "management) + a repeatable way to hand out workload landing zones (subscription vending)",
            "Most organizations should have only one platform landing zone per Microsoft Entra tenant",
        ], theme="yellow", icon="management-group", src=[("What is an Azure landing zone?", S_CAF_LZ[1])]),
        Card(ws[1], "Workload landing zone", [
            "One per workload: it holds all environments (dev, test, prod); each environment = one or more subscriptions",
            "The platform team places each subscription under Online, Internal (\"Corp\") or Local, below the "
            "Workload landing zones MG",
            "Each subscription inherits Azure Policy from the MG hierarchy",
        ], theme="blue", icon="subscription", src=[("What is an Azure landing zone?", S_CAF_LZ[1])]),
        Card(ws[2], "Where does an AI workload go?", [
            "Internet-facing AI workloads: Online MG. Internal AI workloads: Corp MG",
            "Use these existing boundaries instead of creating MGs just for AI",
            "Subscriptions are the boundary for quota, cost, governance and security",
            "Internet-facing AI workloads should use DDoS Protection: the platform team can provide it as shared networking",
            "Microsoft Fabric can prepare and provide governed organizational data to AI workloads",
        ], theme="grape", icon="landing-zone", src=[("Architecture and governance for AI", S_CAF_AI[1])]),
        Card(ws[3], "How the platform gets built", [
            "Microsoft accelerators (infrastructure as code) or a custom build",
            "Connectivity subscription: hub-spoke (peered hubs in 2 regions) or Virtual WAN hubs",
            "Hybrid access to on-premises data: ExpressRoute for predictable private connectivity, VPN Gateway for encrypted "
            "connectivity over the public internet",
            "Platform teams should prepare for multi-region workload landing zones; failover must include model "
            "deployments and retrieval data",
        ], theme="gray", icon="vwan", src=[("What is an Azure landing zone?", S_CAF_LZ[1]),
                                          ("Architecture and governance for AI", S_CAF_AI[1])]),
    ]
    r, b = row(cv, 0, yn, cards, gap=gap)
    return _ai_tree(cv, b + 50)


def _ai_tree(cv, y):
    """CAF AI decision tree: pick the AI platform from the use case before anything lands in a workload landing zone."""
    GR = get_theme("grape")
    cv.text(0, y, "Before the landing zone: which AI platform fits the use case? The CAF AI decision tree", size=24, color=GR.deep)
    cv.text(0, y + 32, "Foundry is one branch. Wherever an AI workload lands on Azure it uses the same management groups and platform "
                       "capabilities as any other workload; Foundry is added to selected workload landing zones as an optional capability.",
            size=15, color="#495057")
    y += 70
    gap = 24
    cw = (W - 7 * gap) / 8
    items = [
        ("Enhance individual productivity", "Microsoft 365 Copilot", "gray", "m365",
         "For Microsoft 365 apps. In-product Copilots (Azure, GitHub, Fabric, Dynamics 365, Power Platform), role-aligned "
         "Copilots (security, sales, service, finance), Microsoft Copilot for general use"),
        ("You use Microsoft 365 Copilot and need custom agents with domain-specific skills", "Extensibility tools", "gray",
         "copilot", "Extensibility tools for Microsoft 365 Copilot"),
        ("Automate business functionality", "Copilot Studio", "green", "agent",
         "A SaaS tool: create and deploy agents through natural language, with integrated pricing"),
        ("A development platform with API access to Foundry Tools", "Microsoft Foundry", "blue", "foundry",
         "The branch this canvas follows"),
        ("Prebuilt non-generative models, or Azure AI Search for agent support", "Foundry Tools", "blue", "ai-services",
         "Use Foundry Tools"),
        ("Train and deploy ML models with your own data", "Fabric or Azure ML", "cyan", "ml",
         "Microsoft Fabric if you already work in it; otherwise Azure Machine Learning"),
        ("Lightweight AI inferencing without managing GPU infrastructure", "Azure Container Apps", "orange", "container-apps",
         "Regional availability and feature status vary: verify current serverless GPU support"),
        ("Bring your own models", "VMs or AKS", "gray", "aks",
         "Azure VMs (optionally with Azure CycleCloud or Azure Batch), or AKS for containerized workloads"),
    ]
    cards = []
    for goal, product, th, ic, text in items:
        hero = product == "Microsoft Foundry"
        cards.append(Card(cw, product, [("para", text)], theme=th, icon=ic, subtitle=goal, title_size=19, body_size=14,
                          sub_size=13, icon_size=36, pad=14, sw=5 if hero else 2, fill="solid" if hero else "hatch"))
    r, b = row(cv, 0, y, cards, gap=gap)
    yb = learn_line(cv, 0, b + 8, S_CAF_AI)
    return yb + 40

# ----------------------------------------------------------------------------------------------------- sections

def subnet_tile(cv, x, y, w, h, name, text, icon, th="indigo", udr=True):
    t = get_theme(th)
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill, style="hachure", sw=2)
        place_icon(cv, icon, x + 10, y + 9, 30)
        nl = wrap_text(name, w - 56, 15)
        cv.text(x + 48, y + 12, "\n".join(nl), size=15, color=t.deep)
        bl = wrap_text(text, w - 22, 13)
        cv.text(x + 11, y + 48 + (len(nl) - 1) * 18.75, "\n".join(bl), size=13, color="#1e1e1e")
        pw, _ = pill(cv, x + 11, y + h - 30, "NSG", th, 12)
        pill(cv, x + 11 + pw + 8, y + h - 30, "UDR to hub FW" if udr else "no UDR", th if udr else "red", 12)
    cv.register(f"snet:{name}", x, y, w, h)
    return Node(x, y, w, h, r)


def pe_chip(cv, x, y, w, h, label, th):
    t = get_theme(th)
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill, style="solid", sw=1.5, rough=0)
        place_icon(cv, "private-endpoint", x + 6, y + (h - 24) / 2, 24)
        ll = wrap_text(label, w - 42, 13)
        cv.text(x + 36, y + (h - len(ll) * 16.25) / 2, "\n".join(ll), size=13, color=t.deep)
    cv.register(f"pe:{label}", x, y, w, h)
    return Node(x, y, w, h, r)


def _topology(cv, y):
    r, b = section_header(cv, 0, y, "2  Landing zone topology: hub, spoke and Foundry",
                          sub="Flows 1 to 8 are explained under the diagram. Yellow = platform team, blue = workload team, "
                              "grape dotted = management group.", size=34, w=W)
    y0 = b + 34
    XP, WP = 350, 670       # platform management-group panel
    XW, WW = 1350, 2250     # workload management-group panel
    BW = WP - 44 - 44 - 40  # hub box width (542)
    IND = get_theme("indigo")
    INK = "#1e1e1e"

    # ============================================================ platform column
    hubs = {}
    Y_P = y0 + 110
    with cv.panel(XP, Y_P, title="Platform management group", sub="Connectivity, Management, Identity and Security MGs",
                  theme="grape", style="dotted", pad=22, title_size=24, sub_size=14, w=WP) as pmg:
        with cv.panel(pmg.ix, pmg.iy, title="Connectivity subscription", sub="platform team (connectivity)",
                      theme="yellow", style="solid", fill="soft", pad=22, title_size=22, sub_size=14, w=WP - 44) as con:
            with cv.panel(con.ix, con.iy, title="Hub virtual network", sub="regional hub with shared services",
                          theme="indigo", style="dashed", pad=20, title_size=20, sub_size=14, w=WP - 88) as hub:
                specs = [
                    ("gw", "ExpressRoute / VPN gateway", "cross-premises access (greyed out: outside the article's scope)",
                     "expressroute", "gray", 70, None),
                    ("zones", "Azure private DNS zones", "A records for the private endpoints: 8 zones (listed in section 4)",
                     "dns", "indigo", 86, "MOVED"),
                    ("bastion", "Azure Bastion", "shared regional resource for operational access", "bastion", "indigo", 74,
                     "MOVED"),
                    ("dns", "DNS Private Resolver + rulesets",
                     "Recommended for Agent Service: a ruleset for the workload's private DNS zones, linked to the spoke. "
                     "Alternative: Azure Firewall as DNS proxy", "dns-resolver", "indigo", 120, None),
                    ("ddos", "Azure DDoS Protection", "covers the Application Gateway public IP", "ddos", "indigo", 78,
                     "MOVED"),
                    ("fw", "Azure Firewall", "inspects and restricts workload egress, agent traffic included",
                     "firewall", "indigo", 82, "MOVED"),
                ]
                cy = hub.iy
                for key, label, sub, icon, th, h, tagtxt in specs:
                    bx = Box(BW, label, sub=sub, icon=icon, icon_pos="left", theme=th, fill="soft" if key == "gw" else "solid",
                             dash="dashed" if key == "gw" else "solid", h=h, size=18, sub_size=13).place(cv, hub.ix, cy)
                    if tagtxt:
                        pill(cv, bx.right - 10, bx.y - 11, tagtxt, "orange", 12, right=True)
                    hubs[key] = bx
                    cy += bx.h + 14
        # --- optional AI Gateway landing zone (where APIM sits)
        with cv.panel(pmg.ix, con.bottom + 40, title="AI Gateway Landing Zone (optional)",
                      sub=_wrapped("Platform / AI CoE-run shared service: a dedicated spoke VNet peered to the hub, or "
                                   "deployed inside the hub VNet", 560, 13),
                      theme="grape", style="dashed", pad=18, title_size=20, sub_size=13, w=WP - 44) as aig:
            draw_badge(cv, aig.ix + (WP - 44 - 36) - 84, aig.y + 14, "preview")
            ax = aig.ix
            b1 = Box(176, "API Management", sub="AI gateway", icon="apim", icon_pos="left", theme="grape", h=84, size=16,
                     sub_size=13).place(cv, ax, aig.iy)
            b2 = Box(176, "Foundry", sub="central model host", icon="foundry", icon_pos="left", theme="blue", h=84,
                     size=16, sub_size=13).place(cv, ax + 188, aig.iy)
            b3 = Box(214, "Event Hub, Cosmos DB, Logic App", sub="usage streaming and analytics", icon="event-hubs",
                     icon_pos="left", theme="cyan", h=84, size=15, sub_size=13).place(cv, ax + 376, aig.iy)
        yc = aig.bottom + 30
        cw3 = (WP - 44 - 28) / 3
        leaf(cv, pmg.ix, yc, cw3, 158, "Security subscription", ["Microsoft Sentinel, Log Analytics workspaces, dashboards"],
             "yellow", "sentinel")
        leaf(cv, pmg.ix + cw3 + 14, yc, cw3, 158, "Identity subscription",
             ["VNets with domain services, Recovery Services vaults"], "yellow", "subscription")
        leaf(cv, pmg.ix + 2 * (cw3 + 14), yc, cw3, 158, "Management subscription",
             ["Central Log Analytics workspace; Azure Monitor baseline alerts by policy"], "yellow", "log-analytics")
    mgmt_leaf = Node(pmg.ix + 2 * (cw3 + 14), yc, cw3, 158)

    # external strip
    gw, zones, bast, dnsb, ddos, fw = (hubs[k] for k in ("gw", "zones", "bastion", "dns", "ddos", "fw"))
    onprem = Box(290, "On-premises / corporate network", sub="data scientists and developers on authorised workstations",
                 icon="users", theme="gray", h=124, size=17, sub_size=13).place(cv, 0, gw.cy - 62)
    pubnet = Box(290, "Public internet", sub="grounding sources, public MCP servers, tools, OS patches", icon="globe",
                 theme="gray", h=124, size=17, sub_size=13).place(cv, 0, fw.cy - 62)

    # ============================================================ workload column
    V = bast.cy - 125
    VW = 1590
    wmg_spec = dict(title="Workload landing zones management group",
                    sub="Online MG (public Application Gateway IP) or Corp MG (internal)", theme="grape", style="dotted",
                    pad=22, title_size=24, sub_size=14, w=WW)
    wsub_spec = dict(title="Workload landing zone subscription",
                     sub=_wrapped("Prod shown; Dev and Test are separate subscriptions. Azure Policy is inherited from the MGs",
                                  600, 14),
                     theme="blue", style="solid", fill="soft", pad=22, title_size=22, sub_size=14, w=WW - 44)
    vnet_spec = dict(title="Spoke virtual network", sub="platform: creates, peers, sets DNS   |   workload: subnets, NSGs, resources",
                     theme="indigo", style="dashed", pad=26, title_size=22, sub_size=14, w=VW)
    ps = panel_offset(wmg_spec, wsub_spec, vnet_spec)
    Y_W = V - ps[2].y
    TW, TH, LANE, BARH = 245, 190, 84, 112
    TG = (VW - 52 - 6 * TW) / 5
    PAAS_H = 108

    with cv.panel(XW, Y_W, **wmg_spec) as wmg:
        with cv.panel(wmg.ix, wmg.iy, **wsub_spec) as wsub:
            vh = (ps[2].iy - ps[2].y) + TH + LANE + BARH + 26
            with cv.panel(wsub.ix, wsub.iy, h=vh, **vnet_spec) as vnet:
                tx0, ty0 = vnet.ix, vnet.iy
                colx = lambda i: tx0 + i * (TW + TG)
                tiles = [
                    ("snet-jumpBoxes", "Jump box for operational support: DNS and routing troubleshooting", "vm", "indigo", True),
                    ("snet-buildAgents", "CI/CD build agents: platform-approved image, patching, authentication", "builds", "indigo", True),
                    ("snet-appGateway", "Application Gateway + WAF + public IP. Ingress stays in the spoke", "app-gateway", "indigo", False),
                    ("snet-mcpServers", "Private MCP servers on Container Apps; a /24 delegated to Microsoft.App/environments. "
                                        "Agent traffic: TCP 443 and 31443",
                     "container-apps", "indigo", True),
                    ("snet-agentsEgress", "Agent Service data proxy; subnet within a /24, delegated to Microsoft.App/environments",
                     "foundry", "green", True),
                    ("snet-appServicePlan", "App Service VNet integration for the chat UI (vnetRouteAllEnabled)", "app-service",
                     "indigo", True),
                ]
                T = [subnet_tile(cv, colx(i), ty0, TW, TH, *tiles[i][:3], th=tiles[i][3], udr=tiles[i][4]) for i in range(6)]
                jump, build, appgw, mcp, agents, appsvc = T
                # --- private endpoint bar
                by = ty0 + TH + LANE
                cv.rect(tx0, by, VW - 52, BARH, stroke=IND.stroke, fill=IND.soft, style="solid", sw=2)
                lab = "snet-privateEndpoints"
                cv.text(tx0 + 14, by + 8, lab, size=16, color=IND.deep)
                cv.text(tx0 + 200, by + 11, "8 private endpoints, network policies enabled", size=13, color="#495057")
                cv.text(tx0 + 690, by + 11, "NSG + UDR", size=13, color="#495057")
                cw_, ch_ = 156, 62
                cyp = by + 38
                dep0 = colx(3) + (2 * TW + TG - (3 * cw_ + 24)) / 2 + 24
                chip_specs = [
                    ("Storage (web code)", "cyan", colx(0)), ("Key Vault", "red", colx(0) + 168),
                    ("AI Search (knowledge)", "teal", colx(0) + 336),
                    ("App Service", "gray", colx(2) + (TW - cw_) / 2),
                    ("AI Search (agent)", "teal", dep0), ("Cosmos DB (agent)", "cyan", dep0 + 168),
                    ("Storage (agent)", "cyan", dep0 + 336),
                    ("Foundry", "blue", colx(5) + (TW - cw_) / 2),
                ]
                chips = [pe_chip(cv, x, cyp, cw_, ch_, lab_, th) for lab_, th, x in chip_specs]
            # ---- below the VNet: PaaS targets
            paas_y = vnet.bottom + 84
            paas_specs = [
                (0, "Storage account", "web app code (ZIP)", "storage", "cyan"),
                (1, "Key Vault", "Application Gateway TLS certificate", "key-vault", "red"),
                (2, "AI Search", "Foundry IQ knowledge store", "ai-search", "teal"),
                (3, "App Service", "chat UI, zone-redundant", "app-service", "gray"),
                (4, "AI Search", "Agent Service dependency", "ai-search", "teal"),
                (5, "Cosmos DB", "Agent Service dependency", "cosmos", "cyan"),
                (6, "Storage", "Agent Service dependency", "storage", "cyan"),
            ]
            paas = []
            for idx, lab_, sub_, icon_, th_ in paas_specs:
                c = chips[idx]
                bx = Box(cw_, lab_, sub=sub_, icon=icon_, icon_pos="top", theme=th_, h=PAAS_H, size=15, sub_size=12,
                         icon_size=30).place(cv, c.x, paas_y)
                paas.append(bx)
                arrow(cv, [(c.cx, c.bottom + 2), (c.cx, paas_y - 6)], dash="dashed", sw=2, color=get_theme(th_).stroke,
                      end_head="arrow")
            mon = Box(cw_ + 30, "Log Analytics + Application Insights", sub="workload's own monitoring", icon="log-analytics",
                      icon_pos="top", theme="violet", h=PAAS_H, size=14, sub_size=12, icon_size=30).place(
                cv, chips[7].cx - (cw_ + 30) / 2, paas_y)
            # dependency group outline
            dx0 = chips[4].x - 10
            cv.rect(dx0, paas_y - 14, 3 * cw_ + 24 + 20, PAAS_H + 14 + 34, stroke=get_theme("cyan").stroke, fill="transparent",
                    style="solid", sw=2, dash="dashed")
            cv.text(dx0 + 12, paas_y + PAAS_H + 6, "Agent Service dependencies: BYO, workload-owned", size=13,
                    color=get_theme("cyan").deep)
            # ---- Foundry resource panel (right)
            fx = vnet.right + 170
            fw_ = WW - 44 - 44 - VW - 170
            with cv.panel(fx, vnet.y, title="Foundry resource", sub="workload-owned (recommended topology)", theme="blue",
                          style="solid", fill="soft", pad=22, title_size=22, sub_size=14, w=fw_,
                          h=paas_y + PAAS_H + 52 - vnet.y) as fp:
                inner = fw_ - 44
                boxA = Box(inner, "Agent Service (standard setup)",
                           sub="Microsoft-managed runtime; its single-tenant data proxy runs in your delegated subnet",
                           icon="agent", icon_pos="left", theme="green", h=96, size=17, sub_size=13).place(cv, fp.ix, fp.iy)
                boxB = Box(inner, "Project", sub="prompt agents (hosted agents also supported) with workload-specific "
                                                 "connections to tools", icon="foundry", icon_pos="left", theme="green",
                           h=90, size=17, sub_size=13).place(cv, fp.ix, boxA.bottom + 14)
                boxD = Box(inner, "Model deployments + content safety", sub="models hosted as a service (MaaS) in the "
                                                                          "workload's own resource", icon="openai",
                           icon_pos="left", theme="blue", h=84, size=16, sub_size=13).place(cv, fp.ix, boxB.bottom + 14)
                cy_c = chips[7].cy
                boxC = Box(inner, "Foundry endpoint (data plane)", sub="public network access disabled; reached through "
                                                                    "the Foundry private endpoint", icon="foundry",
                           icon_pos="left", theme="blue", h=86, size=16, sub_size=13).place(
                    cv, fp.ix, max(cy_c - 43, boxD.bottom + 14))
                note = Note(inner, "Deploy the capability host only after the Foundry, AI Search, Cosmos DB and Storage "
                                   "FQDNs resolve to their private endpoints from inside the spoke.", kind="gotcha",
                            title="DNS gate", size=14, title_size=16)
                note.place(cv, fp.ix, boxC.bottom + 14)
    pill(cv, vnet.right - 12, vnet.y - 11, "MOVED", "orange", 12, right=True)
    pill(cv, vnet.right - 100, vnet.y - 11, "SHARED", "green", 12, right=True)

    # ============================================================ arrows, numbered flows
    def mk(n):
        return dict(num=n, num_theme="ink")

    # 1 ingress
    inet = Box(300, "Internet users", sub="chat UI visitors", icon="users", icon_pos="left", theme="gray", h=76, size=17,
               sub_size=13).place(cv, appgw.cx - 150, Y_W - 122)
    tot = (appgw.y - 6) - (inet.bottom + 4)
    arrow(cv, [(appgw.cx, inet.bottom + 4), (appgw.cx, appgw.y - 6)], sw=3, label_t=22 / tot, **mk(1))
    cv.text(inet.right + 16, inet.y + 10, "HTTPS to Application Gateway + WAF.\nPublic IP covered by DDoS Protection", size=14,
            color="#1e1e1e")
    # 2 AppGw -> App Service PE, 3 App Service -> Foundry PE, 4 data proxy -> dependencies
    arrow(cv, [(appgw.cx, appgw.bottom + 4), (chips[3].cx, chips[3].y - 4)], sw=3, **mk(2))
    cv.text(appgw.cx + 24, appgw.bottom + 8, "via the App Service PE", size=13, color="#1e1e1e")
    arrow(cv, [(appsvc.cx, appsvc.bottom + 4), (chips[7].cx, chips[7].y - 4)], sw=3, **mk(3))
    lbl3 = "TCP 443,\nmanaged identity"
    cv.text(appsvc.cx - 22 - text_size(lbl3, 13)[0], appsvc.bottom + 8, lbl3, size=13, color="#1e1e1e", align="right")
    arrow(cv, [(chips[7].right + 4, chips[7].cy), (boxC.x - 6, boxC.cy)], sw=3, end_head="arrow")
    ddx0, ddx1 = chips[4].x, chips[6].right
    hbrace(cv, ddx0, ddx1, chips[4].y - 6, side="top", depth=13, color="#2f9e44", sw=2)
    bxm = (ddx0 + ddx1) / 2
    arrow(cv, [(bxm, agents.bottom + 4), (bxm, chips[4].y - 22)], sw=3, color="#2f9e44", **dict(num=4, num_theme="green"))
    cv.text(bxm + 22, agents.bottom + 6, "east-west to the PEs\n(not through the hub)", size=13, color="#1e1e1e")
    # injection: Foundry Agent Service -> snet-agentsEgress
    yi = ty0 - 30
    gx = vnet.right + 85
    arrow(cv, [(agents.cx, agents.y - 4), (agents.cx, yi), (gx, yi), (gx, boxA.cy), (boxA.x - 6, boxA.cy)], sw=3,
          color="#2f9e44", dash="dashed", start_head="arrow", end_head=None)
    lbli = "VNet injection: the data proxy runs in your delegated subnet"
    cv.text(agents.cx - 14 - text_size(lbli, 13)[0], yi - 24, lbli, size=13, color="#2b8a3e")

    # hub <-> spoke
    xa = lambda bx: bx.right + 6
    xv = vnet.x - 6
    lab14 = dict(label_size=14)
    arrow(cv, [(xa(zones), zones.cy - 2), (xv, zones.cy - 2)], sw=5, color=IND.stroke, start_head="arrow",
          end_head="arrow", label="VNet peering, created by the platform. No spoke-to-spoke peering unless the workload "
                                  "needs it", label_wrap=300, label_pos="above", **lab14)
    arrow(cv, [(xa(bast), bast.cy), (jump.x - 6, bast.cy)], sw=2, dash="dashed", color=IND.stroke,
          label="Bastion to jump box and build agents", label_wrap=300, label_pos="above", **lab14)
    arrow(cv, [(xa(dnsb), dnsb.cy - 36), (xv, dnsb.cy - 36)], sw=3, color=IND.stroke, label_dy=-12,
          label="hub DNS, inherited by AppGw, App Service, MCP servers, jump box, build agents", label_wrap=300,
          label_pos="above", **dict(num=6, num_theme="ink", **lab14))
    arrow(cv, [(xa(dnsb), dnsb.cy + 36), (xv, dnsb.cy + 36)], sw=3, color="#e03131", dash="dashed", label_dy=14,
          label="ruleset link: Agent Service, Foundry, AI Search and Cosmos DB use Azure DNS and ignore VNet DNS",
          label_wrap=300, label_pos="below", **dict(num=6, num_theme="red", **lab14))
    arrow(cv, [(xv, fw.cy), (xa(fw), fw.cy)], sw=3, color=IND.stroke, dash="dashed", label_dy=-12,
          label="UDR 0.0.0.0/0 on all subnets except snet-appGateway", label_wrap=300, label_pos="above",
          **dict(num=5, num_theme="ink", **lab14))
    pill(cv, xv - 4, fw.cy + 8, "MOVED", "orange", 12, right=True)
    # external endpoints
    arrow(cv, [(onprem.right + 6, gw.cy), (gw.x - 6, gw.cy)], sw=3, start_head="arrow", end_head="arrow", **mk(7))
    arrow(cv, [(fw.x - 6, fw.cy), (pubnet.right + 6, fw.cy)], sw=3, dash="dashed", color=IND.stroke, end_head="arrow",
          label="egress", label_pos="above", label_dx=-30, **lab14)
    # AI gateway path
    arrow(cv, [(fw.cx, fw.bottom + 8), (fw.cx, aig.y - 6)], sw=2, dash="dashed", color="#9c36b5", end_head="arrow",
          label="models, MCP and agents via the AI gateway", label_pos="left", label_t=0.72, label_wrap=520, **lab14)
    # policy inheritance
    gx2 = (pmg.right + wmg.x) / 2
    arrow(cv, [(pmg.right + 6, Y_P + 40), (gx2, Y_P + 40), (gx2, wmg.y + 40), (wmg.x - 6, wmg.y + 40)], sw=3,
          dash="dashed", color="#9c36b5", end_head="arrow")
    place_icon(cv, "policy", gx2 - 17, (Y_P + wmg.y) / 2 + 40 - 17, 34)
    pill(cv, gx2 + 24, (Y_P + wmg.y) / 2 + 28, "NEW", "violet", 12)
    cv.text(pmg.right + 14, Y_P - 46, "Azure Policy and RBAC from the MG hierarchy\n(Deny, Audit, Modify, DINE) apply to the "
                                      "workload subscription", size=14, color="#862e9c")
    # 8 diagnostics
    yd = wmg.bottom + 26
    gx3 = (pmg.right + wmg.x) / 2 + 40
    arrow(cv, [(mgmt_leaf.right + 6, mgmt_leaf.cy), (gx3, mgmt_leaf.cy), (gx3, yd), (mon.cx, yd), (mon.cx, mon.bottom + 6)],
          sw=2, dash="dotted", color="#6741d9", start_head="arrow", end_head=None)
    numbered(cv, mon.cx, yd + 0, 8, theme="ink")
    cv.text(gx3 + 80, yd + 8, _wrapped("diagnostics: workload logs stay in the workload's own workspace; the platform may also "
                                        "copy them to the central one with a DINE policy", 760, 13), size=13, color="#5f3dc4")

    # ============================================================ numbered flow legend
    yl = wmg.bottom + 76
    lw = (WW - 3 * 30) / 4
    flows = [
        (1, "Ingress stays in the spoke", "Application Gateway + WAF and its public IP live in the spoke, not the hub. Azure "
            "Firewall does not inspect this inbound traffic. Optional: platform-supported inbound inspection with extra UDRs."),
        (2, "AppGw to the chat UI", "Application Gateway forwards to the App Service chat UI over the App Service private "
            "endpoint (zone privatelink.azurewebsites.net)."),
        (3, "Chat UI to Foundry", "App Service uses regional VNet integration and calls the Foundry data plane through the "
            "Foundry private endpoint: TCP 443 with the app's managed identity."),
        (4, "Agent to its dependencies", "Agent Service's single-tenant data proxy in snet-agentsEgress reaches Cosmos DB, "
            "Storage and AI Search over their private endpoints. East-west traffic is not routed through the hub."),
        (5, "Egress through the hub firewall", "UDR 0.0.0.0/0 sends internet-bound traffic (public MCP servers, grounding, tools) "
            "to the hub Azure Firewall. Can't be forced: Application Gateway and AI Search traffic."),
        (6, "DNS", "Components that inherit VNet DNS use the hub. Agent Service, Foundry, AI Search and Cosmos DB use Azure DNS "
            "and can't be overridden: link a DNS Private Resolver ruleset to the spoke."),
        (7, "Developer and data-scientist access", "Workstation over ExpressRoute or VPN, hub, peering, then the Foundry portal "
            "through its PE: needs transitive routing + cross-premises DNS. Fallback: Bastion and a jump box."),
        (8, "Diagnostics and alerts", "Workload resources log to their own Log Analytics workspace + Application Insights. The "
            "platform may add central log copies and baseline alerts through policy: don't block them."),
    ]
    heights = []
    row1 = [flow_card(cv, XW + i * (lw + 30), yl, lw, *flows[i][:2], flows[i][2], size=14, min_h=170) for i in range(4)]
    h1 = max(c.h for c in row1)
    row2 = [flow_card(cv, XW + i * (lw + 30), yl + h1 + 24, lw, *flows[4 + i][:2], flows[4 + i][2], size=14, min_h=170)
            for i in range(4)]
    yl_end = yl + h1 + 24 + max(c.h for c in row2)
    return max(pmg.bottom, yl_end) + 60


def _wrapped(s, w, size):
    return "\n".join(wrap_text(s, w, size))


SRC_ALZ = [("Foundry in a landing zone (Architecture Center)", S_ALZ[1])]
TAG_MOVED = ("MOVED from the workload", "orange")
TAG_NEW = ("NEW in a landing zone", "violet")
TAG_SAME = ("unchanged", "gray")


def learn_line(cv, x, y, src, size=12):
    """Clickable 'Learn: ...' citation under a table or diagram. Returns its bottom y."""
    return cv.text(x, y, f"Learn: {src[0]}", size=size, color=LINK, link=src[1]).bottom


def _owners(cv, y):
    r, b = section_header(
        cv, 0, y, "3  Who owns what: platform team and workload team",
        sub="Responsibility table from the landing-zone article: the workload keeps Foundry and everything Agent Service needs; "
            "the platform team takes the shared network and guardrail resources (as of 2026-11-03)", size=34, w=W)
    y = b + 26
    legend(cv, 0, y, [("Platform team owns", "yellow"), ("Workload team owns", "blue"), ("Moved from the workload", "orange"),
                      ("New in a landing zone", "violet"), ("Unchanged", "gray")], size=16, gap=34)
    y += 44
    cols = [("Resource", 560), ("Platform team", 680), ("Workload team", 680), ("Versus the baseline", 380)]
    P = lambda t: (t, "yellow")
    Wk = lambda t: (t, "blue")
    plat = [
        ["Azure Firewall (hub)", P("Owns it, in the connectivity subscription. App rules for the approved FQDNs: external knowledge, "
                                   "tools, public MCP servers"),
         "NSG and UDR on the agent subnet; supplies the FQDNs it needs", TAG_MOVED],
        ["Azure Bastion (hub, shared regional resource)", P("Owns it"),
         "Jump-box and build-agent NSGs allow remote access only from the platform's Bastion subnet", TAG_MOVED],
        ["Spoke virtual network", P("Creates it, peers it to the hub and sets its DNS settings. No spoke-to-spoke peering unless "
                                    "the workload needs it"),
         "Owns the subnets, NSGs and resources inside it", TAG_MOVED],
        ["UDRs: 0.0.0.0/0 to the hub firewall", P("Owns them, on every subnet except snet-appGateway"), "-", TAG_MOVED],
        ["Azure Policy constraints and DeployIfNotExists (DINE)", P("Owns them, at the platform MG or on the workload "
                                                                    "subscription. DINE is best-effort: no SLA"),
         "Expects pre-existing MG policies; owns only workload-specific policy", TAG_NEW],
        ["Private DNS zones (A records for the private endpoints)", P("Owns them, in the connectivity subscription"),
         "Agrees who manages zone records, resolver ruleset links and VNet DNS settings", TAG_MOVED],
        ["DNS resolution service", P("Owns it: DNS Private Resolver with linked rulesets for Agent Service (or hub-based DNS). "
                                     "Alternative: Azure Firewall DNS proxy"), "-", ("platform service", "gray")],
        ["DDoS Protection", P("Owns the plan: IP protection plans, or VNet protection plans enforced through Azure Policy"),
         "Still needs coverage for the Application Gateway public IP", TAG_MOVED],
        ["ExpressRoute / VPN gateway", P("Owns it, in the connectivity subscription"),
         "Private portal access for data scientists via transitive routing: ask for it in the vending request",
         ("out of scope of the article", "gray")],
    ]
    work = [
        ["Foundry resource and projects", "-", Wk("Owns it: models as a service, content safety, agents with workload-specific connections"),
         ("unchanged. A shared resource per business group is not recommended", "gray")],
        ["Agent Service (standard setup)", "-", Wk("Owns it: agent subnet in the spoke, egress through the connectivity "
                                                  "subscription, data proxy in its dedicated subnet"), TAG_SAME],
        ["Agent Service dependencies: Cosmos DB, Storage, AI Search (BYO)",
         "Don't consolidate them as platform resources to optimise cost",
         Wk("Owns them: they must remain workload resources"), TAG_SAME],
        ["App Service chat UI, Application Gateway + WAF, Key Vault, AI Search knowledge store",
         "Decides the MG placement (Online or Corp) from the ingress profile",
         Wk("Owns them. Procures the TLS certificate, aligned with the platform"), TAG_SAME],
        ["Spoke subnets, NSGs and private endpoints", "-", Wk("Owns them (the VNet itself is created by the platform)"),
         ("unchanged: subnets stay workload-owned", "gray")],
        ["Private MCP servers and their Container Apps host", "Allocates spoke address space for the MCP subnet; supports DNS "
                                                              "and firewall", Wk("Deploys and operates them"), ("-", "gray")],
        ["Build agents and jump boxes", "-", Wk("Deploys and operates them: platform-approved OS image, patching, compliance, "
                                                "authentication"), TAG_SAME],
        ["Log Analytics workspace and Application Insights", "May also copy logs to the central workspace (DINE) and add "
                                                             "baseline alerts: don't block them",
         Wk("Owns its own workspace: all diagnostics go here"), TAG_SAME],
        ["Exfiltration mitigation where egress can't be forced", "-",
         Wk("Owns compensating controls, a redesign or a formal exception (Application Gateway, AI Search)"), ("-", "gray")],
        ["Workload-specific Azure Policy", "-", Wk("Owns it"), TAG_SAME],
    ]
    t1 = Table(cols, plat, theme="yellow", size=14, head_size=15, title="Platform team owns", title_size=22).place(cv, 0, y)
    t2 = Table(cols, work, theme="blue", size=14, head_size=15, title="Workload team owns", title_size=22).place(
        cv, 0, t1.bottom + 34)
    yb = learn_line(cv, 0, t2.bottom + 8, S_ALZ)

    X2 = 2350
    W2 = W - X2
    a = Card(W2, "Platform changes that can hurt the workload", [
        "Azure Policy changes and management-group moves: they surface at the workload's next deployment",
        "Firewall rule changes: a blocked Bing API makes agent tool calls fail",
        "Hub routing changes: agents lose the route to another team's vector store, data scientists lose portal access",
        "Bastion changes",
    ], theme="yellow", icon="chaos", src=SRC_ALZ)
    bcard = Card(W2, "Workload changes the platform has to hear about", [
        "Egress growth: the noisy-neighbour effect",
        "Public-access changes: removing the Application Gateway public IP means a different MG",
        "Business-criticality or SLA changes",
        "Data-sovereignty changes: the region where logs, Purview data or SIEM data are replicated",
    ], theme="blue", icon="subscription", src=SRC_ALZ)
    ccard = Card(W2, "Monitoring across the boundary", [
        "The workload provisions its own Application Insights and Log Analytics workspace and sends all diagnostics there",
        "The platform may also push logs to the central workspace (management subscription) with DINE and apply Azure Monitor "
        "baseline alerts with policy: don't block them",
        "Correlating workload and platform logs (Firewall, DNS Private Resolver, Bastion) is hard: write a triage runbook and "
        "have the platform grant RBAC to read the relevant logs",
        "Enable firewall logs for network rules, application rules and the DNS proxy",
    ], theme="violet", icon="monitor", src=SRC_ALZ)
    dnote = Card(W2, "Critical dependencies for the failure mode analysis", [
        "Egress firewall: it is shared by several workloads and changes for reasons unrelated to yours",
        "DNS resolution: the workload depends on timely DNS records for its private endpoints and on the DNS services staying "
        "available",
        "DINE policies: best-effort with no SLA, so a DNS delay can keep the chat UI from becoming traffic-ready or block agents",
        "Management-group policies: keep pre-production matching production so tests stay accurate",
    ], theme="red", icon="service-health", src=SRC_ALZ)
    ecard = Card(W2, "When the models come from the platform", [
        "The article assumes the workload owns its model deployments",
        "If the AI Center of Excellence restricts model deployments, the workload may have to consume models through centralized "
        "AI resources (an AI hub)",
        "All model consumption then usually flows through an AI gateway that the AI platform team provides: the model host "
        "becomes a workload dependency",
        "The platform keeps the network connectivity to it, or provides a private endpoint",
    ], theme="grape", icon="apim", src=SRC_ALZ)
    gap = 22
    ya = y
    a.place(cv, X2, ya)
    bcard.place(cv, X2, a.bottom + gap)
    ccard.place(cv, X2, bcard.bottom + gap)
    dnote.place(cv, X2, ccard.bottom + gap)
    ecard.place(cv, X2, dnote.bottom + gap, h=max(ecard.h, yb - (dnote.bottom + gap)))
    return max(yb, ecard.bottom) + 50


def _dns_egress(cv, y):
    r, b = section_header(
        cv, 0, y, "4  DNS, egress and traffic control",
        sub="Which resolver each component uses, which private DNS zones the platform hosts, how internet-bound traffic reaches the "
            "hub firewall, and who controls each ingress and egress path (as of 2026-11-03)", size=34, w=W)
    y0 = b + 34
    IND, RED = get_theme("indigo"), get_theme("red")
    DW = 2330
    LW = 1010
    with cv.panel(0, y0, title="Who resolves what", sub="Two resolution paths meet in the same private DNS zones", theme="indigo",
                  style="dotted", pad=20, title_size=24, sub_size=14, w=DW) as pd:
        with cv.panel(pd.ix, pd.iy, title="Inherit the VNet DNS setting (hub DNS)", theme="indigo", style="dashed", fill="soft",
                      pad=14, title_size=18, w=LW) as la:
            items = [("Application Gateway", "app-gateway"), ("App Service", "app-service"),
                     ("Private MCP servers", "container-apps"), ("Jump box", "vm"), ("Build agents", "builds")]
            bw = (LW - 28 - 4 * 10) / 5
            for i, (lab, ic) in enumerate(items):
                Box(bw, lab, h=66, theme="indigo", icon=ic, icon_pos="left", size=14, icon_size=26).place(
                    cv, la.ix + i * (bw + 10), la.iy)
        with cv.panel(pd.ix, la.bottom + 40, title="Use Azure DNS: the VNet setting can't be overridden", theme="red",
                      style="dashed", fill="soft", pad=14, title_size=18, w=LW) as lb:
            items = [("AI Search", "ai-search"), ("Foundry", "foundry"), ("Agent Service", "agent"), ("Cosmos DB", "cosmos")]
            bw = (LW - 28 - 3 * 10) / 4
            for i, (lab, ic) in enumerate(items):
                Box(bw, lab, h=66, theme="red", icon=ic, icon_pos="left", size=14, icon_size=32).place(
                    cv, lb.ix + i * (bw + 10), lb.iy)
        xr = pd.ix + LW + 140
        r1 = Box(440, "Hub DNS", sub="Azure Firewall DNS proxy or DNS Private Resolver", icon="dns-resolver", icon_pos="left",
                 theme="indigo", h=100, size=18, sub_size=13).place(cv, xr, la.y + la.h / 2 - 50)
        r2 = Box(440, "DNS Private Resolver ruleset", sub="linked to the spoke VNet: it forwards the privatelink zones",
                 icon="dns-resolver", icon_pos="left", theme="indigo", h=100, size=18, sub_size=13).place(
            cv, xr, lb.y + lb.h / 2 - 50)
        xz = xr + 440 + 140
        z = Box(DW - 40 - (xz - pd.ix), "Azure private DNS zones", sub="connectivity subscription: 8 zones hold the A records of "
                "the private endpoints (table on the right)", icon="dns", icon_pos="top", theme="indigo",
                h=lb.bottom - la.y, size=19, sub_size=14, icon_size=44).place(cv, xz, la.y)
        py = z.bottom - 98
        for i, (lab, th_) in enumerate((("3 zones: Foundry", "blue"), ("3 zones: Agent Service dependencies", "cyan"),
                                        ("2 zones: Key Vault and App Service", "gray"))):
            tw_, _ = text_size(lab, 13)
            pill(cv, z.cx - (tw_ + 14) / 2, py + i * 30, lab, th_, 13)
        arrow(cv, [(la.right + 6, r1.cy), (r1.x - 6, r1.cy)], sw=3, color=IND.stroke, label="VNet DNS", label_size=14,
              label_pos="above")
        arrow(cv, [(lb.right + 6, r2.cy), (r2.x - 6, r2.cy)], sw=3, color=RED.stroke, dash="dashed", label="ruleset link",
              label_size=14, label_pos="above")
        arrow(cv, [(r1.right + 6, r1.cy), (z.x - 6, r1.cy)], sw=3, color=IND.stroke)
        arrow(cv, [(r2.right + 6, r2.cy), (z.x - 6, r2.cy)], sw=3, color=IND.stroke)
        cv.text(pd.ix, lb.bottom + 14, "Where hub-based DNS isn't possible, the platform can't log DNS requests, and resolving Private Link "
                                       "services in your landing zone or other landing zones might be impossible.", size=14,
                color="#495057")
    learn_line(cv, pd.ix, pd.bottom + 6, ("Private Link and DNS integration at scale (CAF)", S_PLDNS[1]))

    zcols = [("Private DNS zone", 500), ("Private endpoint for", 300), ("Used for", 420)]
    F, D, O = "blue", "cyan", "gray"
    zrows = [
        [("privatelink.services.ai.azure.com", F), "Foundry (sub-resource account)", "Chat UI to the Foundry data plane, portal, evaluations"],
        [("privatelink.openai.azure.com", F), "Foundry (same endpoint)", "Foundry data plane"],
        [("privatelink.cognitiveservices.azure.com", F), "Foundry (same endpoint)", "Foundry data plane"],
        [("privatelink.search.windows.net", D), "AI Search (searchService)", "Agent Service dependency and the knowledge store"],
        [("privatelink.blob.core.windows.net", D), "Storage (blob)", "Agent files and the web app code"],
        [("privatelink.documents.azure.com", D), "Cosmos DB (Sql)", "Agent state: database enterprise_memory"],
        [("privatelink.vaultcore.azure.net", O), "Key Vault", "Application Gateway certificates, Foundry connection secrets"],
        [("privatelink.azurewebsites.net", O), "App Service (sites)", "Application Gateway to the chat UI"],
    ]
    tz = Table(zcols, zrows, theme="indigo", size=14, head_size=15, title="Private DNS zones the platform hosts (8)",
               title_size=20).place(cv, DW + 50, y0)
    learn_line(cv, DW + 50, tz.bottom + 6, S_ALZ)
    y1 = max(pd.bottom + 30, tz.bottom + 30) + 20

    # ---- egress: how internet-bound traffic is forced to the hub firewall
    cv.text(0, y1, "How internet-bound traffic is forced to the hub firewall, per component", size=24, color=IND.deep)
    y1 += 40
    cw = (W - 5 * 30) / 6
    cards = []
    for lab, ic, ok, how in [
        ("Application Gateway", "app-gateway", False, "None: it can't be forced through the platform firewall"),
        ("App Service", "app-service", True, "Regional VNet integration with vnetRouteAllEnabled"),
        ("AI Search", "ai-search", False, "None: it can't be forced (not an issue here: no skills are used)"),
        ("Agent Service", "agent", True, "UDR on snet-agentsEgress"),
        ("Private MCP servers", "container-apps", True, "UDR on snet-mcpServers"),
        ("Jump boxes and build agents", "vm", True, "UDR on their subnets"),
    ]:
        cards.append(Card(cw, lab, [("para", how)], theme="green" if ok else "red", icon=ic, title_size=18, body_size=15,
                          icon_size=32, min_h=118, fill="soft" if ok else "hatch"))
    r_, b_ = row(cv, 0, y1, cards, gap=30)
    for c, ok in zip(cards, (False, True, False, True, True, True)):
        pill(cv, c.right - 12, c.bottom - 36, "forced to the hub" if ok else "can't be forced", "green" if ok else "red", 13,
             right=True)
    yn = b_ + 24
    nw2 = (W - 60) / 2
    tip = Note(nw2, "Where a component can't be forced, use compensating controls, redesign, or record a formal exception: the "
                    "workload owns the exfiltration mitigation. East-west traffic to private endpoints isn't routed through the "
                    "hub either.", kind="tip", title="No force-tunnelling for Application Gateway and AI Search", size=15)
    ing = Note(nw2, "Inbound traffic stays in the spoke: Application Gateway + WAF + public IP. Azure Firewall does not inspect it "
                    "(option: platform-supported inbound inspection with extra UDRs). Some organisations place ingress in a "
                    "central perimeter network: out of scope for this architecture.", kind="info",
               title="Ingress is not tunnelled through the hub", size=15, src=[S_ZT])
    hh = max(tip.h, ing.h)
    tip.place(cv, 0, yn, h=hh)
    ing.place(cv, nw2 + 60, yn, h=hh)
    y2 = yn + hh + 44

    # ---- control matrices
    cv.text(0, y2, "Who controls each path: workload control versus platform control", size=24, color=IND.deep)
    y2 += 40
    wk = lambda t: (t, "blue")
    pf = lambda t: (t, "yellow")
    none = ("none", "gray")
    icols = [("Ingress source", 270), ("Purpose", 330), ("Workload control", 600), ("Platform control", 580)]
    irows = [
        ["Internet", "App traffic", wk("NSG + WAF + routing before public-to-private for the chat UI"), none],
        ["Internet", "Foundry portal and data-plane REST", wk("Deny with service-level configuration"), none],
        ["Internet", "Data plane of every service except Application Gateway", wk("Deny with NSG + service configuration"), none],
        ["Azure Bastion", "Jump box and build agents", wk("NSG blocks remote-access ports unless the source is the platform's "
                                                          "Bastion subnet"), none],
        ["Cross-premises", "Foundry portal and REST", wk("Deny all, or allow only authorised workstation subnets if there's no "
                                                         "jump box"), pf("Enforce non-transitive routing, or Azure Firewall in a "
                                                                        "Virtual WAN secured hub")],
        ["Other spokes", "-", wk("Blocked with NSGs"), pf("Non-transitive routing, or the Virtual WAN secured-hub firewall")],
    ]
    ecols = [("Egress endpoint", 290), ("Purpose", 290), ("Workload control", 600), ("Platform control", 600)]
    erows = [
        ["Public internet sources", "Internet grounding", wk("NSG on the agent subnet"),
         pf("Firewall app rules for external knowledge and tools")],
        ["Public MCP servers", "Approved tools", wk("NSG + UDR on the agent subnet"), pf("Firewall app rules for the approved FQDNs")],
        ["Private MCP servers", "Workload tools", wk("Allow 443 and 31443 from the agent subnet, plus inbound on the MCP subnet"),
         none],
        ["Foundry data plane", "Chat UI to the agent", wk("Allow TCP 443 from the App Service integration subnet to the Foundry PE "
                                                          "subnet"), none],
        ["Cosmos DB", "Agent memory database", wk("Allow TCP on every port to the Cosmos DB PE subnet"), none],
    ]
    ti = Table(icols, irows, theme="indigo", size=14, head_size=15, title="Ingress", title_size=20).place(cv, 0, y2)
    te = Table(ecols, erows, theme="indigo", size=14, head_size=15, title="Egress", title_size=20).place(cv, ti.right + 40, y2)
    yb = max(ti.bottom, te.bottom)
    learn_line(cv, 0, yb + 8, S_ALZ)
    return yb + 50


def _gotchas(cv, y):
    r, b = section_header(
        cv, 0, y, "5  Agent Service gotchas in a landing zone",
        sub="What surprises teams the first time a Foundry workload meets platform-owned DNS, firewall and policy "
            "(as of 2026-11-03)", size=34, w=W)
    y = b + 30
    RED = get_theme("red")
    cw = (W - 2 * 60) / 3
    g1 = Card(cw, "1  Agent Service ignores the spoke's DNS", [
        "The Agent Service capability doesn't use your spoke VNet's DNS configuration: it uses Azure DNS, and that can't be "
        "overridden. Foundry, AI Search and Cosmos DB behave the same way",
        "Application Gateway, App Service, private MCP servers, the jump box and build agents inherit the VNet DNS, so they "
        "follow the hub",
        "Platform fix: link DNS Private Resolver rulesets to the spoke VNet (or use hub-based resolution) so the private "
        "endpoint records resolve",
        "Without hub DNS the platform can't log DNS requests, and resolving Private Link services in your landing zone or "
        "other landing zones might be impossible",
    ], theme="indigo", icon="dns-resolver", src=SRC_ALZ)
    g2 = Card(cw, "2  Capability host fails if the PE DNS doesn't resolve", [
        "DNS resolution must work from inside the spoke before you deploy the capability host for Agent Service",
        "Wait until the dependency FQDNs (Foundry, AI Search, Cosmos DB, Storage) resolve to their private endpoints, "
        "especially when DINE policies populate the private DNS zones",
        "DINE policies are best-effort with no SLA: DNS lag can block the chat UI or the agents",
        "Network injection must be set when the Foundry resource is created: it can't be added later. The capability-host page "
        "(kept for reference) says a capability host can't be updated: delete and recreate",
    ], theme="red", icon="private-endpoint",
        src=SRC_ALZ + [S_SAS, ("Capability hosts", learn("agents/concepts/capability-hosts"))])
    g3 = Card(cw, "3  Its dependencies stay workload resources", [
        "Cosmos DB, Storage and AI Search for Agent Service remain workload resources: don't consolidate them as platform "
        "resources to optimise cost",
        "Agent Service manages them exclusively: don't share them with other parts of the workload (blast radius) and never "
        "touch the system-managed collections or indexes directly",
        "Keep your app storage separate from the Agent Service backing storage, and plan quota for the backing resources "
        "separately",
        "Two AI Search services appear in the topology: the knowledge store you query, and the Agent Service dependency",
    ], theme="cyan", icon="cosmos", src=SRC_ALZ)
    r_, b_ = row(cv, 0, y, [g1, g2, g3], gap=60)

    # ---- deployment order that avoids gotcha 2
    y = b_ + 38
    cv.text(0, y, "Deployment order that avoids gotcha 2", size=24, color=RED.deep)
    y += 42
    bw, gp, h = 780, 160, 104
    s1 = Box(bw, "1  Platform: zones and resolver ruleset", sub="Create the private DNS zones and link a DNS Private Resolver "
             "ruleset (or hub DNS) to the spoke VNet", icon="dns-resolver", icon_pos="left", theme="yellow", h=h, size=18,
             sub_size=14).place(cv, 0, y)
    s2 = Box(bw, "2  Workload: private endpoints", sub="Create the private endpoints on Foundry, AI Search, Cosmos DB and "
             "Storage, approve the connections and link every zone to the VNet", icon="private-endpoint", icon_pos="left",
             theme="blue", h=h, size=18, sub_size=14).place(cv, bw + gp, y)
    s3 = Box(bw, "3  Test from inside the spoke", sub="nslookup each FQDN: it must return the private endpoint IP. Then "
             "Test-NetConnection <PE IP> -Port 443", icon="vm", icon_pos="left", theme="indigo", h=h, size=18,
             sub_size=14).place(cv, 2 * (bw + gp), y)
    s4 = Box(bw, "4  Deploy the capability host", sub="Then create and run a test agent", icon="foundry", icon_pos="left",
             theme="green", h=h, size=18, sub_size=14).place(cv, 3 * (bw + gp), y)
    for a_, b2 in ((s1, s2), (s2, s3), (s3, s4)):
        connect(cv, a_, b2, a_side="right", b_side="left", sw=3)
    fail = Box(bw, "Capability host deployment fails", sub="The FQDNs don't resolve to the private endpoints yet, for example "
               "because DINE policies are still filling the zones", icon="chaos", icon_pos="left", theme="red",
               fill="soft", dash="dashed", h=92, size=18, sub_size=14).place(cv, s3.x, s3.bottom + 36)
    connect(cv, s3, fail, a_side="bottom", b_side="top", dash="dashed", color=RED.stroke, sw=3, label="not resolving",
            label_pos="right", label_size=14)
    Note(2 * bw + gp - 120, "The test commands and the 'verify the deployment' checklist come from the Agent Service private "
                            "networking guide. Private endpoint connections must be Approved: that needs Contributor or Owner "
                            "on the Foundry resource, otherwise they stay Pending.", kind="tip", title="Before step 4", size=15,
         src=[("Network-secured agent setup (BYO VNet)", S_VNET[1])]).place(cv, 0, fail.y - 4)

    # ---- identity + DR
    y = fail.bottom + 40
    rcols = [("Role", 620), ("Scope", 1100), ("Identity", 520)]
    SA, SU = "System-assigned", "System- or user-assigned"
    rrows = [
        ["Cosmos DB Operator", "The Cosmos DB account", SA],
        ["Storage Account Contributor", "The Storage account", SA],
        ["Search Index Data Contributor", "The AI Search service", SU],
        ["Search Service Contributor", "The AI Search service", SU],
        ["Storage Blob Data Contributor", "Container <workspaceId>-azureml-blobstore: agent files", SU],
        ["Storage Blob Data Owner", "Container <workspaceId>-azureml-agent: agent system data (chunks, embeddings)", SU],
        ["Cosmos DB Built-in Data Contributor", "Database enterprise_memory (database scope covers all its containers)", SU],
    ]
    tr = Table(rcols, rrows, theme="red", size=15, head_size=16, first_col_theme="red",
               title="4  The project's managed identity needs 7 role assignments on your BYO resources",
               title_size=22).place(cv, 0, y)
    nt = Note(tr.w, "Also needed: the deploying identity (user, CI service principal or workload identity) needs Storage Blob Data "
                    "Contributor on each BYO Storage account and Cosmos DB Operator on each BYO Cosmos DB account. The person "
                    "who creates the account and project needs Foundry Account Owner at subscription scope plus Role Based "
                    "Access Control Administrator (or Owner).", kind="info", title="Who else needs a role", size=15,
              src=[S_SAS]).place(cv, 0, tr.bottom + 24)
    dr = Card(W - tr.w - 60, "5  No built-in disaster recovery for Agent Service", [
        "Agent Service has no built-in DR: no replication, no backup, no point-in-time restore. Foundry has no automatic "
        "cross-region failover either",
        "Cosmos DB: turn on continuous backup for the enterprise_memory database (point-in-time restore within a 7-day "
        "window, into the same account and database)",
        "AI Search: no built-in restore, contact Support. Keep a separate source of truth so you can rebuild the index",
        "Storage: customer-managed failover if the account is GRS, otherwise Support",
        "Keep the three stores consistent with each other: conversation and agent IDs must still line up after a restore",
        "Agents as code; a user-assigned managed identity for the project (a re-created project or capability host reuses "
        "the role assignments); delete locks on the three dependencies; a written runbook",
        "Multi-region: deploy separate Foundry resources per region and handle sync and routing in the app layer. The "
        "platform should support multi-region workload landing zones",
    ], theme="orange", icon="service-health", src=SRC_ALZ + [("Microsoft Foundry architecture", S_ARCH[1])])
    dr.place(cv, tr.right + 60, y, h=max(dr.h, nt.bottom - y))
    y = max(nt.bottom, dr.bottom) + 40

    # ---- docs disagree
    section_header(cv, 0, y, "Docs disagree: verify before you design", size=28, color="#d9480f",
                   sub="The documentation pages below give different answers (as of 2026-11-03). Both views are shown; check the "
                       "live pages before you commit to a design.", w=W)
    y += 90
    nw = (W - 60) / 2
    n1 = Note(nw, "The landing-zone article lists only the three RFC 1918 ranges for the agent subnet: 10.0.0.0/8, 172.16.0.0/12 "
                  "and 192.168.0.0/16. The networking-options and virtual-networks pages also allow RFC 6598 100.64.0.0/10 "
                  "(excluding 100.100.0.0/17, 100.100.192.0/19 and 100.100.224.0/19). The agents-networking-deep-dive page says "
                  "CGNAT 100.64.0.0/10 is not supported because it causes routing failures.", kind="warn",
              title="Docs disagree: is RFC 6598 (CGNAT 100.64.0.0/10) allowed for the agent subnet?", size=15,
              src=[S_NETOPT, S_VNET, ("Agent networking deep dive",
                                      learn("agents/concepts/agents-networking-deep-dive"))])
    n2 = Note(nw, "One passage says five containers; another says three containers and 3,000 RU/s. The use-your-own-resources page "
                  "says 3 to 5 containers per project at 1,000 RU/s each, depending on the runtime (classic containers: "
                  "thread-message-store, system-thread-message-store, agent-entity-store; Responses API adds agent-definitions-v1 "
                  "and run-state-v1). The account needs at least 3,000 RU/s; too little RU/s causes provisioning failures.",
              kind="warn", title="Docs disagree: how many Cosmos DB containers and how much RU/s does Agent Service need?",
              size=15, src=[("Use your own resources", learn("agents/how-to/use-your-own-resources")), S_SAS])
    hh = max(n1.h, n2.h)
    n1.place(cv, 0, y, h=hh)
    n2.place(cv, nw + 60, y, h=hh)
    return y + hh + 50


def _sources(cv, y):
    items = [
        ("Baseline Foundry chat in an Azure landing zone (Architecture Center)", S_ALZ[1]),
        ("Baseline Microsoft Foundry chat reference architecture", S_BASE[1]),
        ("Foundry rollout across my organization", S_PLAN[1]),
        ("Microsoft Foundry architecture", S_ARCH[1]),
        ("AI platform sharing, isolation and colocation (CAF)", S_CAF_SHARE[1]),
        ("Architecture and governance for AI (CAF)", S_CAF_AI[1]),
        ("What is an Azure landing zone? (CAF)", S_CAF_LZ[1]),
        ("Plan for AI adoption (CAF)", S_CAF_PLAN[1]),
        ("Subscription vending (CAF)", S_VEND[1]),
        ("Private Link and DNS integration at scale (CAF)", S_PLDNS[1]),
        ("Built-in policies for model deployment", S_MODEL_POL[1]),
        ("Custom policy definitions for Foundry", S_CUSTOM_POL[1]),
        ("Azure Policy built-ins for Foundry Tools", S_POL_REF[1]),
        ("Standard agent setup", S_SAS[1]),
        ("Network-secured agent setup (BYO VNet)", S_VNET[1]),
        ("Agent networking options", S_NETOPT[1]),
        ("Configure private link for Foundry", S_PRIVLINK[1]),
        ("Zero Trust network for web apps with Azure Firewall and Application Gateway", S_ZT[1]),
        ("AI Landing Zones (GitHub: Azure/AI-Landing-Zones)", S_AILZ[1]),
        ("AI Landing Zones documentation", S_AILZ_DOCS[1]),
        ("AI Landing Zones: Agent Landing Zone", S_AILZ_AGENT[1]),
        ("AI Landing Zones: planning", S_AILZ_PLAN[1]),
        ("AI Landing Zones: network design", S_AILZ_NET[1]),
        ("AI Landing Zones: deployment settings", S_AILZ_CFG[1]),
        ("AI Landing Zones: AI Gateway Landing Zone", S_AILZ_GW[1]),
        ("AI Landing Zones: FAQ", S_AILZ_FAQ[1]),
        ("AI Landing Zones: design checklist", S_AILZ_CHECK[1]),
    ]
    t = cv.text(0, y, "Continue in part 2 (Foundry in an Azure landing zone, part 2): Foundry resource ownership models, Azure Policy "
                      "guardrails, subscription vending and CI/CD, the AI Landing Zones repo and Well-Architected notes.",
                size=18, color="#0b7285")
    s = sources(cv, 0, t.bottom + 24, items, w=W, cols=4, title="Sources and further reading (links are clickable)")
    return s.bottom + 20


# (new sections are wired into build() below)


def build(cv: Canvas) -> None:
    only = os.environ.get("LZ_SECTIONS")  # dev aid: e.g. "mg,topology"
    steps = [("mg", _mg), ("topology", _topology), ("owners", _owners), ("dns", _dns_egress), ("gotchas", _gotchas),
             ("sources", _sources)]
    y = _head(cv)
    for name, fn in steps:
        if only and name not in only.split(","):
            continue
        y = fn(cv, y)
