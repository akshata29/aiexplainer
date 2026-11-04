"""Baseline Microsoft Foundry chat, network-isolated: Application Gateway + WAF, private endpoints, standard agent setup
(BYO Cosmos DB / Storage / AI Search), agent subnet injection and Azure Firewall egress - a VNet map with numbered flows,
the private endpoint + DNS zone table, identity wiring, subnet matrices, design decisions and the flagged doc conflicts."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="ra-baseline-network-isolated",
    title="Baseline chat: network-isolated (private endpoints, WAF, standard setup)",
    section="3", group="Reference architectures", order=2,
    description="The production baseline for Foundry chat redrawn as a VNet map: Application Gateway + WAF, private endpoints, standard "
                "agent setup with your own Cosmos DB, Storage and AI Search, agent subnet injection, Azure Firewall egress, DNS zones, RBAC wiring and trade-offs.",
    tags=["reference-architecture", "network-isolation", "private-endpoint", "standard-agent-setup", "waf", "azure-firewall"],
)

W = 3200
AC = "azure/architecture"
ASOF = "as of 2026-11-03"
IND, GRN, RED, GRY, INKC, VIO = "#3b5bdb", "#2f9e44", "#e03131", "#868e96", "#1e1e1e", "#6741d9"

# ----------------------------------------------------------------------------------------------------- citations
S_BASE = ("Baseline Microsoft Foundry chat reference architecture",
          learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC))
S_SAS = ("Standard agent setup", learn("agents/concepts/standard-agent-setup"))
S_OWN = ("Use your own resources with Agent Service", learn("agents/how-to/use-your-own-resources"))
S_VNET = ("Network-secured agent setup (BYO VNet)", learn("agents/how-to/virtual-networks"))
S_NETOPT = ("Agent networking options", learn("agents/concepts/networking-options"))
S_DEEP = ("Agent Service networking deep dive", learn("agents/concepts/agents-networking-deep-dive"))
S_PRIV = ("Configure private link for Foundry", learn("how-to/configure-private-link"))
S_MANVNET = ("Managed virtual network for Foundry", learn("how-to/managed-virtual-network"))
S_CAPH = ("Capability hosts", learn("agents/concepts/capability-hosts"))
S_RBAC = ("Role-based access control for Foundry", learn("concepts/rbac-foundry"))
S_ENV = ("Foundry Agent environment setup", learn("agents/environment-setup"))
S_ARCH = ("Microsoft Foundry architecture", learn("concepts/architecture"))
S_NSP = ("Foundry in a network security perimeter", learn("how-to/add-foundry-to-network-security-perimeter"))
S_PATTERNS = ("AI agent design patterns (Architecture Center)", learn("ai-ml/guide/ai-agent-design-patterns", base=AC))
S_REPO = ("Reference implementation: microsoft-foundry-baseline (GitHub)", "https://github.com/Azure-Samples/microsoft-foundry-baseline")
S_TEMPL = ("Foundry sample Bicep templates (GitHub)",
           "https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep")
S_BLOG = ("Foundry agents and custom engine agents through the corporate firewall (blog)",
          "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-agents-and-custom-engine-agents-through-the-corporate-firewall/4502218")


# ----------------------------------------------------------------------------------------------------- helpers
class Node(Rect2):
    """Hand-composed shape with a connector-friendly bounding box."""

    def __init__(self, x, y, w, h, el=None):
        self.x, self.y, self.w, self.h, self.el = x, y, w, h, el

    @property
    def bind_target(self):
        return self.el


def pill(cv, x, y, text, th="indigo", size=12, right=False, pad=7, solid=True):
    """Small unregistered tag. Returns (w, h)."""
    t = get_theme(th)
    tw, hh = metrics.text_size(text, size)
    w, h = tw + 2 * pad, hh + 6
    if right:
        x -= w
    with cv.group():
        cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill if solid else "transparent", style="solid", sw=1.5, rough=0)
        cv.text(x + pad, y + 3, text, size=size, color=t.deep)
    return w, h


def pill_rows(pills, max_w, size=12, gap=6):
    """Greedy rows of (label, theme) pills; returns (rows, height)."""
    rows, cur, cw = [], [], 0.0
    for lab, th in pills:
        w = metrics.text_size(lab, size)[0] + 14
        if cur and cw + gap + w > max_w:
            rows.append(cur)
            cur, cw = [], 0.0
        cw += (gap if cur else 0) + w
        cur.append((lab, th, w))
    if cur:
        rows.append(cur)
    hh = metrics.text_size("Ag", size)[1] + 6
    return rows, len(rows) * hh + max(0, len(rows) - 1) * 5


class Tile(Rect2):
    """Subnet tile: icon + name + wrapped description + pills; measured on construction (extra_h reserves room)."""

    def __init__(self, w, name, text, icon, theme="indigo", pills=(), *, name_size=17, size=14, pad=12, dash="solid",
                 min_h=0, extra_h=0, text_w=None, fill="hatch"):
        self.th = get_theme(theme)
        self.w, self.name, self.icon, self.pad, self.size, self.name_size = w, name, icon, pad, size, name_size
        self.dash, self.extra_h, self.fill = dash, extra_h, fill
        self.name_lines = wrap_text(name, w - 2 * pad - 42, name_size)
        self.lines = wrap_text(text, (text_w or (w - 2 * pad)) * 0.965, size) if text else []
        self.pill_rows, ph = pill_rows(pills, w - 2 * pad)
        lh = metrics.line_ratio()
        head = max(len(self.name_lines) * name_size * lh, 30)
        body = len(self.lines) * size * lh
        self.h = max(pad + head + 4 + body + (8 if self.pill_rows else 0) + ph + extra_h + pad, min_h)
        self.pills_h = ph
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        bg, fs = (th.fill, "hachure") if self.fill == "hatch" else (th.soft, "solid")
        lh = metrics.line_ratio()
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=2, dash=self.dash)
            place_icon(cv, self.icon, x + pad, y + pad - 2, 30)
            cv.text(x + pad + 40, y + pad, "\n".join(self.name_lines), size=self.name_size, color=th.deep)
            ty = y + pad + max(len(self.name_lines) * self.name_size * lh, 30) + 4
            if self.lines:
                cv.text(x + pad, ty, "\n".join(self.lines), size=self.size, color=INKC)
            py = y + H - pad - self.extra_h - self.pills_h
            for row_ in self.pill_rows:
                px = x + pad
                for lab, pth, pw in row_:
                    pill(cv, px, py, lab, pth, 12)
                    px += pw + 6
                py += metrics.text_size("Ag", 12)[1] + 6 + 5
        cv.register(f"tile:{self.name}", x, y, self.w, H - self.extra_h)
        return self

    @property
    def bind_target(self):
        return self.rect_el


class PEChip(Rect2):
    """Private-endpoint chip: icon + target name + sub-resource line."""

    def __init__(self, w, label, sub, theme, h=66):
        self.th = get_theme(theme)
        self.w, self.h, self.label, self.sub = w, h, label, sub
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, self.h, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
            place_icon(cv, "private-endpoint", x + 6, y + (self.h - 28) / 2, 28)
            tw = self.w - 44
            ll = wrap_text(self.label, tw, 15)
            sl = wrap_text(self.sub, tw, 12)
            total = len(ll) * 15 * 1.25 + len(sl) * 12 * 1.25
            ty = y + (self.h - total) / 2
            cv.text(x + 38, ty, "\n".join(ll), size=15, color=th.deep)
            cv.text(x + 38, ty + len(ll) * 15 * 1.25, "\n".join(sl), size=12, color="#495057")
        cv.register(f"pe:{self.label}", x, y, self.w, self.h)
        return self


def zone(cv, x, y, w, h, title=None, *, theme="indigo", sub=None, style="dotted", fill="none", icon=None, title_size=22,
         sub_size=15, pad=16, sw=2, icon_size=30, title_pos="top", sub_wrap=None):
    """Explicit-size boundary drawn BEFORE its children. title_pos 'top' (left) or 'bottom' (left)."""
    th = get_theme(theme)
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
        if icon and title_pos == "top":
            place_icon(cv, icon, x + pad, y + pad * 0.5, icon_size)
            tx += icon_size + 10
        if title:
            sl = wrap_text(sub, sub_wrap, sub_size) if (sub and sub_wrap) else ([sub] if sub else [])
            th_h = title_size * metrics.line_ratio() + (2 + len(sl) * sub_size * metrics.line_ratio() if sl else 0)
            ty = y + pad * 0.7 if title_pos == "top" else y + h - pad * 0.7 - th_h
            if icon and title_pos == "bottom":
                place_icon(cv, icon, x + pad, ty - 2, icon_size)
                tx += icon_size + 10
            t = cv.text(tx, ty, title, size=title_size, color=th.deep)
            if sl:
                cv.text(tx, t.bottom + 2, "\n".join(sl), size=sub_size, color=MUTED)
    return Node(x, y, w, h, el)


def letter(cv, cx, cy, ch, theme="indigo", d=28, size=16):
    """Rounded-square letter badge (network flow A/B/C)."""
    th = get_theme(theme)
    tw, thh = metrics.text_size(ch, size)
    with cv.group():
        cv.rect(cx - d / 2, cy - d / 2, d, d, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        cv.text(cx - tw / 2, cy - thh / 2 + 1, ch, size=size, color=th.deep)


def varrow(cv, x, y1, y2, *, color=INKC, sw=3, dash="solid", num=None, num_theme="blue", let=None, let_theme="indigo",
           label=None, label_pos="right", label_size=14, label_t=0.5, label_dx=0.0, label_dy=0.0, start_head=None,
           end_head="arrow", label_wrap=None):
    """Vertical arrow from y1 to y2 with an optional number circle (+ letter badge) at the middle."""
    el = arrow(cv, [(x, y1), (x, y2)], color=color, sw=sw, dash=dash, num=num, num_theme=num_theme, label=label,
               label_pos=label_pos, label_size=label_size, label_t=label_t, label_dx=label_dx, label_dy=label_dy,
               start_head=start_head, end_head=end_head, label_wrap=label_wrap)
    if let:
        my = y1 + (y2 - y1) * label_t
        letter(cv, x - 32 if num is not None else x, my, let, let_theme)
    return el


def harrow(cv, y, x1, x2, **kw):
    return arrow(cv, [(x1, y), (x2, y)], **kw)


class Steps(Rect2):
    """Card whose rows are round numbered markers + wrapped text."""

    def __init__(self, w, title, steps, *, theme_name="blue", icon=None, src=(), size=15, title_size=22, pad=16, gap=10,
                 d=30, marker="num"):
        self.th = get_theme(theme_name)
        self.marker = marker
        self.w, self.title, self.icon, self.src = w, title, icon, list(src)
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
            for n, sth, lines, sy, hh in self.steps:
                if self.marker == "letter":
                    letter(cv, x + pad + self.d / 2, y + sy + self.d / 2, n, theme=sth, d=self.d, size=17)
                else:
                    numbered(cv, x + pad + self.d / 2, y + sy + self.d / 2, n, theme=sth, d=self.d, size=17)
                ty = y + sy + ((self.d - self.size * metrics.line_ratio()) / 2 + 1 if len(lines) == 1 else 0)
                cv.text(x + pad + self.d + 12, ty, "\n".join(lines), size=self.size, color=INKC)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self


def chapter(cv, y, text, sub=None):
    _, b = section_header(cv, 0, y, text, sub=sub, size=34, w=W, sub_size=17)
    return b + 30


# ----------------------------------------------------------------------------------------------------- 0 title + glance
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Baseline Microsoft Foundry chat - network-isolated",
        "Production reference architecture: one public door (Application Gateway + WAF), private endpoints for everything else, "
        f"standard agent setup in your VNet and Azure Firewall egress - {ASOF}", w=W)
    y = bottom + 34
    gw, gap = 502, 38
    items = [
        ("Only one public door", "Application Gateway + WAF; DDoS Protection plan on its public IP", "app-gateway", "indigo"),
        ("Private endpoints for the rest", "Foundry, AI Search, Cosmos DB, Storage, Key Vault, App Service; public access disabled", "private-endpoint", "indigo"),
        ("Standard agent setup", "BYO VNet + BYO Cosmos DB, Storage and AI Search: all agent state in your subscription", "agent", "green"),
        ("Agents injected into your subnet", "snet-agentsEgress, delegated to Microsoft.App/environments (set at account creation)", "subnet", "green"),
        ("Egress only through Azure Firewall", "UDR 0.0.0.0/0; FQDN allow-list; no TLS inspection of agent traffic", "firewall", "red"),
        ("One resource per production workload", "dedicated Foundry resource = the fully isolated workload topology; single region", "foundry", "blue"),
    ]
    boxes = [Box(gw, a, sub=b, icon=ic, icon_pos="left", theme=t, h=112, size=18, sub_size=13) for a, b, ic, t in items]
    row(cv, 0, y, boxes, gap=gap)
    y += 112 + 22
    n = Note(W, "This is the baseline chat article's production design. The chat UI follows the baseline App Service web app guidance "
                "(zone-redundant, VNet integration + private endpoints); this canvas draws only the Foundry-specific parts. It uses a prompt agent "
                "persisted in Agent Service (hosted agents are also supported). Reference implementation: Azure-Samples/microsoft-foundry-baseline. "
                "The topology is redrawn from the article's text and diagram descriptions: check exact boxes and arrows against the live page.",
             kind="info", title="Scope of this canvas", size=15, src=[S_BASE, S_REPO])
    n.place(cv, 0, y)
    return n.bottom + 46


# ----------------------------------------------------------------------------------------------------- 1 topology
def _topology(cv, y):
    y = chapter(cv, y, "1  The walled campus: one public door, everything else private",
                "Numbers 1-7 are the request flow (listed under the VNet). Letters A, B, C are the three network flows: "
                "A = into the Foundry endpoint, B = agent to your Azure PaaS dependencies, C = agent to the internet through the firewall.")
    FY = y

    # ---- geometry
    VX, VPAD = 420, 32
    c1x, c1w = VX + VPAD, 380
    c2x, c2w = c1x + c1w + 32, 400
    c3x, c3w = c2x + c2w + 32, 960
    c4x, c4w = c3x + c3w + 80, 380
    c5x, c5w = c4x + c4w + 32, 380
    V_RIGHT = c5x + c5w + VPAD
    VY = FY + 236
    R0Y = VY + 96

    # ---- tiles (measured first so each row shares one height)
    t_build = Tile(c1w, "snet-buildAgents", "CI/CD build agents: deploy agents as code from inside the network.", "builds", "gray",
                   [("NSG in: Bastion subnet", "gray"), ("out: PEs + internet", "gray"), ("UDR -> FW", "red")])
    t_fw = Tile(c2w + c3w + 80 + c4w + 64, "AzureFirewallSubnet + AzureFirewallManagementSubnet",
                "Azure Firewall inspects and restricts all agent egress with FQDN rules. Deploy across all availability zones, use multiple public IPs "
                "against SNAT exhaustion, Basic tier unless you need more. No TLS inspection on agent traffic.", "firewall", "indigo",
                [("no NSG, no UDR on these subnets", "indigo"), ("allow: Entra ID tag, platform FQDNs, your public FQDNs", "red")],
                text_w=1100)
    t_bast = Tile(c5w, "AzureBastionSubnet", "Azure Bastion: the only way in to the jump box when there is no peered VNet, ExpressRoute or VPN.", "bastion", "gray",
                  [("NSG per Bastion docs", "gray"), ("no UDR", "gray")])
    r0h = max(t_build.h, t_fw.h, t_bast.h)

    t_gw = Tile(c1w, "snet-appGateway", "Application Gateway + WAF: the only internet-exposed resource. TLS termination, path-based routing, zone distribution; "
                "TLS certificate stored in Key Vault. The back end is the App Service private endpoint.", "app-gateway", "indigo",
                [("public IP + DDoS plan", "red"), ("NSG: internet users", "indigo"), ("no UDR", "gray")])
    t_app = Tile(c2w, "snet-appServicePlan", "App Service VNet integration for the chat UI (zone-redundant, 3 zones). It calls Foundry through the private endpoint with "
                 "the app's managed identity; the code ZIP comes from a Storage account.", "app-service", "gray",
                 [("NSG in: none", "gray"), ("out: PEs + Azure Monitor", "gray"), ("UDR -> FW", "red")])
    t_ae = Tile(c3w, "snet-agentsEgress",
                "Foundry Agent Service runtime injected here: a dedicated subnet delegated to Microsoft.App/environments, not shared with another "
                "Foundry resource. Minimum /27, recommended /24. NSG blocks all inbound; outbound only to PE subnets and TCP 443 to the internet.",
                "foundry", "green", [("injection set at account creation", "orange"), ("UDR -> FW: only the public FQDNs you allow", "red")],
                extra_h=118)
    t_mcp = Tile(c4w, "snet-mcpServers", "Private MCP servers on Container Apps (internal): a /24 delegated to Microsoft.App/environments. Private DNS must resolve the "
                 "environment's default or custom domain to its static IP, and the NSG must also allow the Container Apps traffic.", "container-apps", "orange",
                 [("NSG in: TCP 443 + 31443 from agent subnet", "orange"), ("UDR -> FW", "red")])
    t_jump = Tile(c5w, "snet-jumpBoxes", "Jump box VMs: portal and data-plane access from inside the network. Highly privileged: log who and what.", "vm", "gray",
                  [("NSG in: Bastion subnet", "gray"), ("out: PEs + internet", "gray"), ("UDR -> FW", "red")])
    r1h = max(t_gw.h, t_app.h, t_ae.h, t_mcp.h, t_jump.h)

    L0 = 120                                   # egress lane (R0 -> R1)
    R1Y = R0Y + r0h + L0
    BANDY = R1Y + r1h + 78
    BANDH = 152
    VBOT = BANDY + BANDH + VPAD
    PY = VBOT + 78                             # PaaS / platform row

    # ---- VNet zone + header
    zone(cv, VX, VY, V_RIGHT - VX, VBOT - VY, "Virtual network (single region)", theme="indigo", style="dashed", sw=3, title_size=26,
         sub="NSG on every subnet that supports one; UDR 0.0.0.0/0 to Azure Firewall on every subnet that supports one - even when no egress is expected",
         sub_size=15, icon="vnet", icon_size=34, pad=22, fill="none")

    T = {}
    T["build"] = t_build.place(cv, c1x, R0Y, h=r0h)
    T["fw"] = t_fw.place(cv, c2x, R0Y, h=r0h)
    T["bast"] = t_bast.place(cv, c5x, R0Y, h=r0h)
    T["gw"] = t_gw.place(cv, c1x, R1Y, h=r1h)
    T["app"] = t_app.place(cv, c2x, R1Y, h=r1h)
    T["ae"] = t_ae.place(cv, c3x, R1Y, h=r1h)
    T["mcp"] = t_mcp.place(cv, c4x, R1Y, h=r1h)
    T["jump"] = t_jump.place(cv, c5x, R1Y, h=r1h)

    # ---- inner boxes of the agent subnet
    ix = c3x + 12
    iy = R1Y + r1h - 12 - 118
    mvm = Box(430, "Micro VMs (hosted agents)", sub="2 NICs, own outbound NIC; each concurrent agent session uses one subnet IP",
              icon="vm", icon_pos="left", theme="green", h=100, size=16, sub_size=13, icon_size=30).place(cv, ix, iy + 9)
    dpx = Box(c3w - 24 - 430 - 16, "Single-tenant data proxy", sub="Azure Container Apps, one per project, shared by all prompt agents; "
              "every tool call goes through it to your private endpoints", icon="container-apps", icon_pos="left", theme="green",
              h=100, size=16, sub_size=13, icon_size=30).place(cv, ix + 430 + 16, iy + 9)

    # ---- PE band
    zone(cv, c1x, BANDY, V_RIGHT - VPAD - c1x, BANDH, theme="indigo", style="solid", fill="soft", sw=2)
    cv.text(c1x + 14, BANDY + BANDH - 52, "snet-privateEndpoints", size=17, color=get_theme("indigo").deep)
    cv.text(c1x + 14, BANDY + BANDH - 29, "NSG in: virtual network; out: none. UDR -> FW.", size=13, color=MUTED)
    cyp = BANDY + 14
    chip_w = 210
    chips = {}

    def chip(key, x, label, sub, th):
        chips[key] = PEChip(chip_w, label, sub, th).place(cv, x, cyp)

    chip("app", 612, "App Service", "inbound from AppGw", "gray")
    f_x = 1052 - chip_w / 2
    chip("fnd", f_x, "Foundry", "sub-resource: account", "blue")
    s_x = c3x + c3w - (3 * chip_w + 2 * 24)
    chip("srch", s_x, "AI Search", "searchService", "teal")
    chip("cos", s_x + chip_w + 24, "Cosmos DB", "Sql", "cyan")
    chip("sto", s_x + 2 * (chip_w + 24), "Storage", "blob (agent files)", "cyan")
    chip("web", c4x + 84, "Storage", "blob (web app code)", "cyan")
    chip("kv", c5x + 82, "Key Vault", "vault", "red")

    # ---- Foundry platform + PaaS row
    FPX, FPW = 876, 680
    FPH = 566
    zone(cv, FPX, PY, FPW, FPH, "Microsoft-managed Foundry platform", theme="blue", style="solid", fill="soft", sw=2.5, title_size=22,
         sub="Foundry resource + project: outside your VNet, public network access disabled, PEs defined at resource level",
         sub_size=14, title_pos="bottom", icon="foundry", icon_size=32, pad=18, sub_wrap=FPW - 90)
    bw = (FPW - 44 - 20) / 2
    ex, tx_ = FPX + 22, FPX + 22 + bw + 20
    b_end = Box(bw, "Foundry endpoint", sub="<resource>.services.ai.azure.com - data plane, reached over the PE", icon="foundry", icon_pos="left",
                theme="blue", h=104, size=17, sub_size=13, icon_size=30).place(cv, ex, PY + 22)
    b_tool = Box(bw, "Tools Service", sub="routes tool calls to the data proxy in your subnet", icon="toolbox", icon_pos="left",
                 theme="orange", h=104, size=17, sub_size=13, icon_size=30).place(cv, tx_, PY + 22)
    b_agent = Box(FPW - 44, "Agent Service - standard setup",
                  sub="prompt agent (hosted agents also supported); project-level capability host binds your Cosmos DB, Storage and AI Search; "
                      "every prompt agent in a project shares one managed identity",
                  icon="agent", icon_pos="left", theme="green", h=128, size=18, sub_size=13, icon_size=34).place(cv, ex, PY + 22 + 104 + 52)
    b_model = Box(bw, "Model deployment", sub="Azure OpenAI in the same Foundry resource; content filter bound per deployment", icon="openai",
                  icon_pos="left", theme="blue", h=118, size=17, sub_size=13, icon_size=30).place(cv, ex, b_agent.bottom + 52)
    b_conn = Box(bw, "Connections", sub="project level, Entra ID auth; API-key connections keep secrets in your Key Vault", icon="api-connections",
                 icon_pos="left", theme="cyan", h=118, size=17, sub_size=13, icon_size=30).place(cv, tx_, b_agent.bottom + 52)

    pw = chip_w
    paas = {}
    paas_specs = [
        ("srch", "Azure AI Search", "agent dependency: Agent Service owns the index, schema and chunking", "ai-search", "teal"),
        ("cos", "Azure Cosmos DB for NoSQL", "database enterprise_memory: conversations and agent definitions", "cosmos", "cyan"),
        ("sto", "Azure Storage", "agent files uploaded in chat; containers + lifecycle managed by Agent Service", "storage", "cyan"),
        ("web", "Azure Storage", "chat UI code ZIP (separate account)", "storage", "cyan"),
        ("kv", "Azure Key Vault", "Application Gateway TLS certificates + Foundry connection secrets", "key-vault", "red"),
    ]
    pbs = {k: Box(pw, label, sub=sub, icon=icon, icon_pos="top", theme=th, h=200, size=16, sub_size=13, icon_size=32)
           for k, label, sub, icon, th in paas_specs}
    ph_ = max(b.h for b in pbs.values())
    for k, b in pbs.items():
        paas[k] = b.place(cv, chips[k].x, PY, h=ph_)
    cv.text(s_x, PY + ph_ + 10, "All PaaS targets: public network access = Disabled. Create the PEs yourself; link every private DNS zone to the VNet.",
            size=13, color=MUTED, wrap=c5x + c5w - s_x)

    # ---- outside actors
    LW = 300
    users = Box(LW, "Application users", sub="browser over HTTPS from the internet", icon="users", icon_pos="top", theme="gray", h=124,
                size=17, sub_size=13).place(cv, 0, R1Y + (r1h - 124) / 2)
    entra = Box(LW, "Microsoft Entra ID", sub="signs users in; managed identities; RBAC", icon="app-registrations", icon_pos="top", theme="red",
                h=124, size=17, sub_size=13).place(cv, 0, R0Y + (r0h - 124) / 2)
    inet = Box(340, "Public internet", sub="only the FQDNs the firewall allows", icon="globe", icon_pos="left", theme="gray", h=84, size=17,
               sub_size=13).place(cv, c3x + c3w / 2 - 170, FY + 10)
    oper = Box(300, "Agent author / operator", sub="portal and data-plane access", icon="user", icon_pos="left", theme="gray", h=84,
               size=16, sub_size=13).place(cv, c5x + (c5w - 300) / 2, FY + 10)
    how = Card(900, "How to read it", [
        "Numbers 1-7 = request flow; letters A / B / C = network flows (indigo / green / red arrows)",
        "Dashed red = egress through Azure Firewall; dashed green = agent runtime injected into your subnet",
        "Lock chips = private endpoints in snet-privateEndpoints; each one points at its PaaS target",
    ], theme="gray", fill="soft", title_size=18, body_size=15)
    how.place(cv, VX + 40, FY + 4)

    # ---- arrows
    gwx = T["gw"].cx
    # 1 users -> appgw
    arrow(cv, [(users.right + 6, users.cy), (c1x - 4, users.cy)], sw=3, num=1, num_theme="blue", label="HTTPS", label_size=14, label_dx=-34,
          label_dy=-6)
    # sign-in
    arrow(cv, [(users.cx, users.y - 6), (entra.cx, entra.bottom + 6)], dash="dotted", color=GRY, sw=2.5, label="sign-in", label_size=14,
          label_pos="right")
    # 1 appgw -> PE app service -> app service (U path through the PE)
    pe_a = chips["app"]
    varrow(cv, 700, T["gw"].bottom + 6, pe_a.y - 6, num=1, num_theme="blue", sw=3, label="WAF inspects; forwards via the App Service PE",
           label_pos="left", label_size=13, label_wrap=190)
    arrow(cv, [(pe_a.right + 4, pe_a.cy), (890, pe_a.cy), (890, T["app"].bottom + 6)], sw=3)
    # 2 / A app service -> Foundry PE -> endpoint
    ex_c = b_end.cx
    varrow(cv, ex_c, T["app"].bottom + 6, chips["fnd"].y - 6, color=IND, sw=3, num=2, num_theme="indigo", let="A", let_theme="indigo")
    varrow(cv, ex_c, chips["fnd"].bottom + 4, b_end.y - 6, color=IND, sw=3)
    cv.text(ex_c + 40, T["app"].bottom + 36, "Responses API over HTTPS via the PE, managed identity", size=13, color=INKC, wrap=215)
    # 3 inside the platform
    varrow(cv, b_end.cx, b_end.bottom + 6, b_agent.y - 6, color=INKC, sw=3, num=3, num_theme="green")
    varrow(cv, b_tool.cx, b_agent.y - 6, b_tool.bottom + 6, color=INKC, sw=3, label="tool calls", label_pos="right", label_size=14)
    varrow(cv, b_model.cx, b_agent.bottom + 6, b_model.y - 6, color=INKC, sw=3, num=6, num_theme="blue")
    varrow(cv, b_conn.cx, b_agent.bottom + 6, b_conn.y - 6, color=GRY, sw=2, dash="dotted")
    # injection: tools service -> agent subnet
    inj_x = b_tool.cx
    varrow(cv, inj_x, b_tool.y - 6, R1Y + r1h + 6, color=GRN, sw=3.5, dash="dashed")
    cv.text(inj_x + 16, PY - 52, "VNet injection:\nthe runtime lives in your subnet", size=14, color="#2b8a3e")
    # B flows: agent subnet -> PEs -> PaaS
    for key, n, th in (("srch", 4, "teal"), ("cos", 7, "cyan"), ("sto", None, "cyan")):
        c = chips[key]
        col = GRN
        varrow(cv, c.cx, R1Y + r1h + 6, c.y - 6, color=col, sw=3, num=n, num_theme=th, let="B" if n == 4 else None, let_theme="green")
        varrow(cv, c.cx, c.bottom + 4, PY - 6, color=get_theme(th).stroke, sw=2, dash="dashed")
    for key in ("fnd", "web", "kv"):
        c = chips[key]
        if key == "fnd":
            continue
        varrow(cv, c.cx, c.bottom + 4, PY - 6, color=get_theme("cyan" if key == "web" else "red").stroke, sw=2, dash="dashed")
    # Foundry platform keeps connection secrets in Key Vault: stated on the Connections box and the Key Vault box (no extra line)
    # C: egress through the firewall
    for tl, dsh, sw_ in ((T["app"], "dashed", 2), (T["mcp"], "dashed", 2)):
        arrow(cv, [(tl.cx, tl.y - 4), (tl.cx, T["fw"].bottom + 6)], dash=dsh, color=RED, sw=sw_)
    cv.text(T["app"].cx + 12, R0Y + r0h + 18, "Azure Monitor only", size=13, color="#c92a2a")
    cv.text(T["mcp"].cx + 12, R0Y + r0h + 18, "MCP egress", size=13, color="#c92a2a")
    ae_c = T["ae"].cx
    varrow(cv, ae_c, T["ae"].y - 4, T["fw"].bottom + 6, color=RED, sw=3.5, num=5, num_theme="red", let="C", let_theme="red")
    cv.text(ae_c + 40, R0Y + r0h + 16, "UDR 0.0.0.0/0: public FQDNs only", size=13, color="#c92a2a")
    arrow(cv, [(ae_c, T["fw"].y - 4), (ae_c, inet.bottom + 6)], color=RED, sw=3.5, label="external tools: public MCP, OpenAPI", label_size=13,
          label_pos="right", label_dx=10)
    # 5 private MCP stays in the VNet
    arrow(cv, [(T["ae"].right + 4, T["ae"].cy), (T["mcp"].x - 4, T["mcp"].cy)], color=GRN, sw=3, num=5, num_theme="green")
    cv.text(T["ae"].right + 6, T["ae"].cy + 30, "private MCP:\n443 + 31443", size=12, color="#2b8a3e", wrap=76)
    # ops
    arrow(cv, [(oper.cx, oper.bottom + 6), (T["bast"].cx, T["bast"].y - 4)], dash="dashed", color=GRY, sw=2.5, label="portal access", label_size=13,
          label_pos="left")
    arrow(cv, [(T["bast"].cx, T["bast"].bottom + 4), (T["jump"].cx, T["jump"].y - 4)], dash="dashed", color=GRY, sw=2.5)

    # ---- request flow card + A-C card + developer path
    steps = Steps(FPX - 60, "Request flow (numbers match the diagram)", [
        (1, "User -> chat UI over Application Gateway; the WAF inspects and forwards to the App Service back end.", "blue"),
        (2, "The web app calls its agent through Microsoft Agent Framework: OpenAI-compatible Responses API over the Foundry PE; auth is the web app's managed identity.", "indigo"),
        (3, "The agent runs per its system prompt with its configured model and tools: Azure AI Search for grounding, web search for public data.", "green"),
        (4, "Agent -> AI Search tool over the private network, through the AI Search PE.", "teal"),
        (5, "Public MCP servers and custom OpenAPI tools traverse Azure Firewall; private MCP servers and APIs stay in the VNet.", "red"),
        (6, "The agent calls its language model and passes the relevant context.", "blue"),
        (7, "Before returning to the UI, the agent persists request, response and tool invocations as conversation items in Cosmos DB, so a chat can resume.", "cyan"),
    ], theme_name="blue", icon="workflow", src=[("Baseline chat: workflow", S_BASE[1] + "#workflow")], size=14, gap=8, d=28)
    steps.place(cv, 0, PY)
    flows = Steps(FPX - 60, "Three network flows", [
        ("A", "App Service chat UI -> HTTPS over the PE -> Foundry data-plane endpoint.", "indigo"),
        ("B", "Agent -> single-tenant data proxy in the delegated subnet -> HTTPS to the PEs of AI Search, Cosmos DB, Storage and your custom tools.", "green"),
        ("C", "Agent -> resources outside the VNet: the data proxy routes from the delegated subnet through Azure Firewall.", "red"),
    ], theme_name="indigo", icon="private-link", marker="letter", size=14, gap=8, d=28,
        src=[("Baseline chat: network flows", S_BASE[1] + "#network-flows")])
    flows.place(cv, 0, steps.bottom + 22)

    # ---- developer path (right-bottom)
    dx0 = s_x
    dw = c5x + c5w - dx0
    cv.text(dx0, PY + 262, "Reaching the portal and the data plane (developer path)", size=20, color=get_theme("gray").deep)
    n_dev, gap_d = 6, 46
    bw_d = (dw - (n_dev - 1) * gap_d) / n_dev
    dev = [
        ("Agent author", "works from a laptop", "user", "gray"),
        ("Azure Bastion", "AzureBastionSubnet", "bastion", "gray"),
        ("Jump box VM", "snet-jumpBoxes", "vm", "gray"),
        ("Foundry portal PE", "Foundry account private endpoint", "private-endpoint", "blue"),
        ("Foundry project + Agent Service", "virtual interface in the agent subnet", "foundry", "green"),
        ("PEs of the 3 dependencies", "AI Search, Cosmos DB, Storage", "private-endpoint", "cyan"),
    ]
    dbs = [Box(bw_d, a, sub=b, icon=ic, icon_pos="top", theme=th, h=122, size=15, sub_size=12, icon_size=28) for a, b, ic, th in dev]
    dh = max(b.h for b in dbs)
    dboxes = [b.place(cv, dx0 + i * (bw_d + gap_d), PY + 296, h=dh) for i, b in enumerate(dbs)]
    for a_, b_ in zip(dboxes, dboxes[1:]):
        connect(cv, a_, b_, a_side="right", b_side="left", sw=2.5, color=GRY)
    nd = Note(dw, "Alternatives to Bastion + jump box: a peered VNet, ExpressRoute, or a site-to-site / point-to-site VPN. The portal website ai.azure.com "
                  "is reachable, but all project-level functionality needs network access to the data-plane private endpoints.",
              kind="info", title="Portal access", size=14, src=[("Network-secured agent setup", S_VNET[1])])
    nd.place(cv, dx0, PY + 296 + dh + 18)
    return max(PY + FPH, flows.bottom, nd.bottom) + 44


# ----------------------------------------------------------------------------------------------------- ops lane
def _ops(cv, y):
    cw, gap = (W - 44 - 4 * 22) / 5, 22
    zone(cv, 0, y, W, 270, "Operations and governance lane (workload-wide)", theme="violet", style="dashed", fill="none", sw=2, title_size=24,
         sub="Applies to every box above: diagnostics on all resources, alerts, Defender plans, policy, and portal-side governance", sub_size=15,
         icon="monitor", pad=20)
    bx = 22
    items = [
        ("Log Analytics + Application Insights", "all log categories on all services; App Insights connected to the Foundry project for traces, tokens and latency",
         "log-analytics", "violet"),
        ("Azure Monitor baseline alerts", "AI Search, AI services, Web Apps; also watch Azure Firewall SNAT + health and the jump boxes", "alerts", "violet"),
        ("Defender for Cloud plans", "Servers, App Service, Cosmos DB and AI services plans", "defender", "red"),
        ("Microsoft Purview (Control Plane)", "enable at subscription scope: audit log, DSPM classification, collection policy; Insider Risk 'Risky Agents' template is preview; "
         "interaction-data flow doesn't support network isolation", "compliance", "grape"),
        ("Azure Policy", "disable key / local auth; require PEs and NSGs; customer-managed keys; restrict regions and types", "policy", "grape"),
    ]
    boxes = [Box(cw, a, sub=b, icon=ic, icon_pos="top", theme=th, h=176, size=17, sub_size=13, icon_size=32) for a, b, ic, th in items]
    row(cv, bx, y + 84, boxes, gap=gap)
    return y + 270 + 48


# ----------------------------------------------------------------------------------------------------- sources
def _sources(cv, y):
    sources(cv, 0, y, [
        S_BASE, S_SAS, S_OWN, S_VNET, S_NETOPT, S_DEEP, S_PRIV, S_MANVNET, S_NSP, S_CAPH, S_RBAC, S_ENV, S_ARCH,
        ("Baseline chat in an Azure landing zone", learn("ai-ml/architecture/baseline-microsoft-foundry-landing-zone", base=AC)),
        S_REPO, S_TEMPL,
    ], w=W, cols=3)


# ----------------------------------------------------------------------------------------------------- 2 dns
def _dns(cv, y):
    y = chapter(cv, y, "2  Private endpoints and private DNS: what to create and what must resolve",
                "Seven private endpoints in snet-privateEndpoints (two of them for Storage accounts); every private DNS zone linked to the VNet; public network access "
                f"disabled on Foundry, AI Search, Storage and Cosmos DB ({ASOF})")
    rows = [
        [("Foundry (account)", "blue"), "account",
         "privatelink.cognitiveservices.azure.com\nprivatelink.openai.azure.com\nprivatelink.services.ai.azure.com",
         "Chat UI -> Foundry data plane; portal; evaluations"],
        [("Azure AI Search", "teal"), "searchService", "privatelink.search.windows.net", "Agent Service dependency + knowledge store"],
        [("Azure Cosmos DB (NoSQL)", "cyan"), "Sql", "privatelink.documents.azure.com", "Agent state (enterprise_memory)"],
        [("Azure Storage", "cyan"), "blob", "privatelink.blob.core.windows.net", "Agent files + web app code"],
        [("Key Vault", "red"), "vault", "privatelink.vaultcore.azure.net", "App Gateway certs, Foundry connection secrets"],
        [("App Service (inbound from AppGw)", "gray"), "sites", "privatelink.azurewebsites.net", "AppGw -> App Service"],
    ]
    t = Table([("Private Link resource", 250), ("Sub-resource (group)", 170), ("Private DNS zone(s)", 480), ("Used by", 380)], rows,
              theme="indigo", size=14, head_size=15, title="Private endpoints and the private DNS zones they need", title_size=22)
    t.place(cv, 0, y)
    cw = (W - t.w - 40 - 40) / 2
    c1 = Card(cw, "Create them yourself", [
        "PEs for AI Search, Storage and Cosmos DB are NOT created when you deploy the Foundry resource: create one on each resource",
        "Link every private DNS zone to the VNet",
        "A PE connection must be Approved: Contributor or Owner on the Foundry resource, otherwise it stays Pending",
        "Network Contributor on the VNet to create a PE; Private DNS Zone Contributor for the zones",
    ], theme="red", icon="private-endpoint", src=[S_VNET, S_PRIV])
    c2 = Card(cw, "DNS must resolve first", [
        "Create the capability host only after the dependency FQDNs resolve to the PEs, otherwise the deployment fails",
        "Custom DNS: conditional forwarders to Azure DNS 168.63.129.16",
        "Test: nslookup <fqdn>, then Test-NetConnection <pe-ip> -Port 443",
    ], theme="indigo", icon="dns", src=[("Baseline chat in a landing zone", learn("ai-ml/architecture/baseline-microsoft-foundry-landing-zone", base=AC)), S_VNET])
    c3 = Card(cw, "Verify the deployment", [
        "Subnet delegation shows Microsoft.App/environments",
        "Public network access = Disabled on Foundry, AI Search, Storage and Cosmos DB",
        "nslookup each endpoint, then create and run a test agent",
    ], theme="green", icon="diagnostics", src=[S_VNET])
    c4 = Card(cw, "Good to know", [
        "PEs live in the same region and subscription as the VNet",
        "Trusted Azure services exception list: Foundry Tools (Microsoft.CognitiveServices), AI Search (Microsoft.Search), Azure Machine Learning (Microsoft.MachineLearningServices)",
        "Template default when you bring no VNet: 192.168.0.0/16 with agent subnet 192.168.0.0/24 and PE subnet 192.168.1.0/24",
    ], theme="gray", icon="info-protection", src=[S_PRIV, S_VNET])
    x2 = t.right + 40
    r1, b1 = row(cv, x2, y, [c1, c2], gap=40)
    r2, b2 = row(cv, x2, b1 + 28, [c3, c4], gap=40)
    y2 = t.bottom + 40
    cv.text(0, y2, "How a name becomes a private IP", size=22, color=get_theme("indigo").deep)
    y2 += 44
    gp = 46
    bw = (t.w - 3 * gp) / 4
    items = [
        ("Caller in the VNet", "app, jump box, build agent, agent data proxy", "vm", "gray"),
        ("Azure DNS 168.63.129.16", "custom DNS: conditional forwarder to it", "dns", "indigo"),
        ("Private DNS zone", "privatelink.* zone linked to the VNet", "dns", "indigo"),
        ("PE NIC private IP", "A record -> the PE in snet-privateEndpoints", "private-endpoint", "blue"),
    ]
    bxs = [Box(bw, a, sub=b, icon=ic, icon_pos="top", theme=th, h=130, size=16, sub_size=13, icon_size=32) for a, b, ic, th in items]
    bh = max(b.h for b in bxs)
    bxs = [b.place(cv, i * (bw + gp), y2, h=bh) for i, b in enumerate(bxs)]
    for a_, b_ in zip(bxs, bxs[1:]):
        connect(cv, a_, b_, a_side="right", b_side="left", sw=3, color=IND)
    return max(y2 + bh, b2) + 56


# ----------------------------------------------------------------------------------------------------- 3 identity
def _rbac(cv, y):
    y = chapter(cv, y, "3  Identity wiring: one project identity, seven role assignments on your BYO resources",
                "Standard agent setup: the project managed identity is the runtime principal. Arrows point at the scope; numbers match the seven assignments "
                f"({ASOF}; roles use the new Foundry names, GUIDs unchanged)")
    ROW = 70
    mi_w = 340
    zx = 860
    zw = 740
    sw_ = 470
    specs = [
        ("Azure Cosmos DB account (BYO)", "cosmos", "cyan", [
            (1, "Cosmos DB Operator", "Cosmos DB account", "runtime provisioning", "System-assigned"),
            (2, "Cosmos DB Built-in Data Contributor", "database enterprise_memory", "scope covers all its containers: conversations, agent definitions", "System- or user-assigned"),
        ]),
        ("Azure Storage account (BYO)", "storage", "cyan", [
            (3, "Storage Account Contributor", "Storage account", "runtime", "System-assigned"),
            (4, "Storage Blob Data Contributor", "container <workspaceId>-azureml-blobstore", "agent files", "System- or user-assigned"),
            (5, "Storage Blob Data Owner", "container <workspaceId>-azureml-agent", "agent system data: chunks, embeddings", "System- or user-assigned"),
        ]),
        ("Azure AI Search service (BYO)", "ai-search", "teal", [
            (6, "Search Index Data Contributor", "AI Search service", "create and query vector stores", "System- or user-assigned"),
            (7, "Search Service Contributor", "AI Search service", "create and query vector stores", "System- or user-assigned"),
        ]),
    ]
    ztop = y
    zy = ztop
    row_pos = []
    for title, icon, th, rws in specs:
        zh = 54 + len(rws) * ROW + 6
        zone(cv, zx, zy, zw, zh, title, theme=th, style="solid", fill="soft", icon=icon, title_size=20, pad=14, icon_size=28)
        for k, rw in enumerate(rws):
            ry = zy + 50 + k * ROW
            sc = Box(sw_, rw[2], sub=rw[3], theme=th, h=ROW - 10, size=15, sub_size=12, fill="solid").place(cv, zx + 14, ry)
            pill(cv, sc.right + 12, ry + (ROW - 10) / 2 - 11, rw[4], "red", 12, solid=False)
            row_pos.append((rw, ry + (ROW - 10) / 2))
        zy += zh + 16
    total_h = zy - 16 - ztop
    mi = Card(mi_w, "Project managed identity", [
        "System-assigned and user-assigned (SMI + UMI) are both granted",
        "Prefer a user-assigned identity: a re-created project or capability host then reuses the role assignments",
        "All prompt agents in a project share this one identity; hosted agents get their own Entra agent identity",
        "! These assignments sit on your resources: whoever deploys needs Microsoft.Authorization/roleAssignments/write to create them",
    ], theme="red", icon="managed-identity", src=[S_SAS, S_OWN])
    mi.place(cv, 0, ztop, h=total_h)
    for rw, ay in row_pos:
        n, role = rw[0], rw[1]
        arrow(cv, [(mi.right + 6, ay), (zx + 8, ay)], color=RED, sw=2.5, dash="dashed")
        ch = Chip(role, theme="red", size=15, fill="solid")
        ch.place(cv, (mi.right + zx) / 2 - ch.w / 2 + 14, ay - ch.h - 4)
        numbered(cv, mi.right + 26, ay, n, theme="red", d=28, size=16)
    # who else
    tx = zx + zw + 40
    tw_ = W - tx
    who = Table(
        [("Who", 330), ("Role", 440), ("Scope", 260), ("Why", 0)],
        [
            ["Deploying identity (user, CI service principal or workload identity)", ("Storage Blob Data Contributor", "red"), "each BYO Storage account", "provision the required containers"],
            ["same", ("Cosmos DB Operator", "red"), "each BYO Cosmos DB account", "provision Cosmos resources (AI Search: no caller role needed)"],
            ["Person creating account + project", ("Foundry Account Owner + Role Based Access Control Administrator (or Owner)", "red"), "subscription", "create and assign roles (roleAssignments/write)"],
            ["Developers (agent authors)", ("Foundry User (min agents/*/read, /action, /delete) + Reader on the Foundry resource", "red"), "Foundry project", "create and edit agents"],
            ["Foundry resource manager", ("Foundry Account Owner", "red"), "Foundry resource", "manage the resource"],
            ["Agent consumers (callers only), for example the web app's identity", ("Foundry Agent Consumer", "red"), "project or agent scope", "invoke endpoints only: the least-privilege option on the RBAC page"],
        ], w=tw_, theme="red", size=14, head_size=15, title="Who else needs a role", title_size=22)
    who.place(cv, tx, ztop)
    n_ren = Note(tw_, "Old Azure AI User / Owner / Account Owner / Project Manager names can still appear in the portal; the role IDs are unchanged. Developers need Foundry User "
                      "(at minimum the agents/*/read, agents/*/action and agents/*/delete data actions); a principal that only calls agents needs Foundry Agent Consumer.",
                 kind="tip", title="Renamed roles, same permissions", size=14, src=[S_RBAC])
    n_ren.place(cv, tx, who.bottom + 24)
    yb = max(ztop + total_h, n_ren.bottom) + 40
    cw = (W - 40) / 2
    c_id = Card(cw, "Identity design choices", [
        "Separate managed identities per resource and function: Foundry resource, each project, web app, Application Gateway, custom orchestrator",
        "Assignment restrictions (preview): allow identity assignment only to Microsoft.CognitiveServices/accounts/projects, Microsoft.Web/sites and Microsoft.Network/applicationGateways; isolation scope Regional",
        "Prefer workload identities and agent identities; Entra ID auth on connections, secrets in a dedicated Key Vault",
        "Separate projects per access pattern, because prompt agents in one project share an identity",
    ], theme="red", icon="managed-identity", badge="preview", src=[S_BASE, S_RBAC])
    t_ids = Table(
        [("Role", 560), ("Role ID", 0)],
        [
            ["Foundry User", "53ca6127-db72-4b80-b1b0-d745d6d5456d"],
            ["Foundry Owner", "c883944f-8b7b-4483-af10-35834be79c4a"],
            ["Foundry Account Owner", "e47c6f54-e4a2-4754-9501-8e0985b135e1"],
            ["Foundry Project Manager", "eadc314b-1a2d-4efa-be10-5d325db5065e"],
            ["Foundry Agent Consumer", "eed3b665-ab3a-47b6-8f48-c9382fb1dad6"],
            ["Azure AI Enterprise Network Connection Approver (managed VNet only)", "b556d68e-0be0-4f35-a333-ad7ee1ce17ea"],
        ], w=cw, theme="red", size=14, head_size=15, title="Role IDs (unchanged by the rename)", title_size=20)
    row(cv, 0, yb, [c_id], gap=0, equalize=False)
    t_ids.place(cv, cw + 40, yb)
    return max(c_id.bottom, t_ids.bottom) + 60


# ----------------------------------------------------------------------------------------------------- 4 network matrices
def _netmatrix(cv, y):
    y = chapter(cv, y, "4  Subnet, NSG, UDR and firewall rules, subnet sizing and the two agent network paths",
                f"Nine subnets; NSG on every subnet that supports one; UDR to the firewall on every subnet that supports it ({ASOF})")
    t = Table(
        [("Subnet", 290), ("NSG inbound", 330), ("NSG outbound", 290), ("UDR -> FW", 110), ("Firewall egress", 380)],
        [
            [("snet-privateEndpoints", "indigo"), "Virtual network", "No traffic", CHECK, "None"],
            [("snet-appGateway", "indigo"), "Chat-UI user sources (internet) + service-required", "PE subnet + service-required", CROSS, DASH],
            [("snet-appServicePlan", "gray"), "None", "PEs + Azure Monitor", CHECK, "To Azure Monitor"],
            [("snet-agentsEgress (Foundry Agent Service)", "green"), "None", "PEs, MCP subnet, internet", CHECK, "Only the public FQDNs you allow agents to use"],
            [("snet-mcpServers", "orange"), "TCP 443 and 31443 from the agent subnet + host-required", "host-required", CHECK, "Platform FQDNs + public FQDNs the MCP servers need"],
            [("snet-jumpBoxes", "gray"), "Bastion subnet", "PEs + internet", CHECK, "As needed by the VM"],
            [("snet-buildAgents", "gray"), "Bastion subnet", "PEs + internet", CHECK, "As needed by the VM"],
            [("AzureBastionSubnet", "gray"), "per the Bastion NSG docs", "per the Bastion NSG docs", CROSS, DASH],
            [("AzureFirewallSubnet / AzureFirewallManagementSubnet", "indigo"), "no NSG", "no NSG", CROSS, DASH],
        ], w=1720, theme="indigo", size=14, head_size=15, title="Subnet / NSG / UDR / firewall matrix", title_size=22,
        align=["left", "left", "left", "center", "left"])
    t.place(cv, 0, y)
    allow = Table(
        [("Scenario", 210), ("Allow through the firewall", 0)],
        [
            ["Agents (identity)", "*.identity.azure.net, login.microsoftonline.com, *.login.microsoftonline.com, *.login.microsoft.com - or the AzureActiveDirectory service tag. "
                                  "Template list: control-{region}.identity.azure.net, {region}.login.microsoft.com, login.microsoftonline.com"],
            ["Evaluations and traces", "settings.sdk.monitor.azure.com, *.livediagnostics.monitor.azure.com, *.in.applicationinsights.azure.com + AzureMachineLearning tag "
                                       "(alternative: *.dataproxy.{region}.api.azureml.ms, {region}.api.azureml.ms)"],
            ["Fine-tuning", "raw.githubusercontent.com"],
            ["Hosted agents: Agent 365 telemetry", "agent365.svc.cloud.microsoft (or AzureFrontDoor.Frontend tag), TCP 443; opt out with a365LoggingEnabled=false on the Foundry resource"],
            ["Hosted agents: source-code deploy", "deployment endpoints listed under 'firewall requirements for private virtual networks' in the deploy-hosted-agent-code page"],
        ], w=W - 1720 - 40, theme="red", size=14, head_size=15, title="Firewall allow-list by scenario", title_size=22)
    allow.place(cv, t.right + 40, y)
    nt = Note(allow.w, "Do not TLS-inspect agent traffic: a self-signed certificate breaks provisioning and runtime. Add matching NSG outbound rules for Entra ID.",
              kind="warn", title="Firewall and NSG for the agent subnet", size=14, src=[S_VNET, S_PRIV])
    nt.place(cv, allow.x, allow.bottom + 20)
    y2 = max(t.bottom, nt.bottom) + 44

    # ---- ladder (custom bars)
    lx = 0
    lw = 1500
    cv.text(lx, y2, "Subnet size ladder for the agent subnet", size=22, color=get_theme("green").deep)
    cv.text(lx, y2 + 30, "One IP per concurrent agent session by default (support can raise it to 1 IP : 10 sessions); keep utilisation at or under 80%",
            size=14, color=MUTED, wrap=lw)
    ladder = [("/27", 27, "~20", False), ("/26", 59, "~50", False), ("/25", 123, "~100", False), ("/24", 251, "~250", True),
              ("/23", 507, "~500", False), ("/22", 1019, "~1,000", False), ("/21", 2043, "~2,000", False)]
    ly = y2 + 84
    maxw = 760
    import math
    for i, (cidr, ips, sess, rec) in enumerate(ladder):
        bar = 60 + (math.log2(ips) - math.log2(27)) / (math.log2(2043) - math.log2(27)) * (maxw - 60)
        th = get_theme("green" if rec else "indigo")
        yy = ly + i * 50
        cv.text(lx, yy + 6, cidr, size=20, color=th.deep)
        cv.rect(lx + 70, yy, bar, 38, stroke=th.stroke, fill=th.fill, style="hachure" if rec else "solid", sw=2.5 if rec else 2)
        cv.text(lx + 70 + bar + 14, yy + 3, f"~{ips:,} usable IPs  ->  {sess} sessions" + ("   recommended for production" if rec else ""),
                size=15, color=th.deep if rec else INKC)
    ln = Note(lw, "The Azure subnet reserves 5 IPs. The region's session quota caps real concurrency (a /22 or larger doesn't lift a 1,000-session quota). "
                  "One Foundry resource can't share its agent subnet with another. Roughly 250 projects per Foundry instance at low traffic, as few as 25 under heavy traffic.",
              kind="info", title="Sizing rules", size=14, src=[S_DEEP])
    ln.place(cv, 0, ly + 7 * 50 + 14)
    ln2 = Note(lw, "Exhaustion shows up as HTTP 5xx from the data proxy, HTTP 429 subnet_exhausted on hosted agents, or failed provisioning of new projects. "
                   "There is no portal metric for delegated-subnet IP usage and no proactive warning: track it yourself.",
               kind="gotcha", title="No early warning", size=14, src=[S_DEEP])
    ln2.place(cv, 0, ln.bottom + 16)

    # ---- prompt vs hosted path
    px = lw + 60
    pw_ = W - px
    cv.text(px, y2, "Two agent paths through the network", size=22, color=get_theme("green").deep)
    cv.text(px, y2 + 30, "Both end at the single-tenant data proxy; all tool calls go through it. Neither calls your resources from the Foundry side", size=14,
            color=MUTED, wrap=pw_)
    prompt = ["Client", "Foundry endpoint", "Tools Service", "Data proxy (your subnet)", "Your PEs"]
    hosted = ["Client", "Foundry endpoint", "Micro VM (your subnet)", "Tools Service", "Data proxy", "Your PEs"]

    def chain(cy, labels, theme_, title, sub):
        cv.text(px, cy, title, size=18, color=get_theme(theme_).deep)
        cv.text(px + 220, cy + 2, sub, size=14, color=MUTED, wrap=pw_ - 230)
        n = len(labels)
        gap = 34
        bw = (pw_ - (n - 1) * gap) / n
        bxs = []
        for i, lab in enumerate(labels):
            th = "gray" if i == 0 else ("blue" if i == 1 else ("orange" if "Tools" in lab else ("cyan" if "PEs" in lab else "green")))
            bxs.append(Box(bw, lab, theme=th, h=64, size=15).place(cv, px + i * (bw + gap), cy + 52))
        for a_, b_ in zip(bxs, bxs[1:]):
            connect(cv, a_, b_, a_side="right", b_side="left", sw=2.5, color=GRN)
        return cy + 52 + 64

    e1 = chain(y2 + 84, prompt, "green", "Prompt agent",
               "no Micro VM; versions don't consume IPs: a small static pool (up to ~10 IPs per project) serves all prompt agents")
    e2 = chain(e1 + 36, hosted, "green", "Hosted agent",
               "Micro VM (/invoke) with 2 NICs and its own outbound NIC; each concurrent session uses 1 IP, a new revision briefly doubles it")
    pn = Note(pw_, "As of 2026-11-03, hosted agents with a private ACR are supported for projects created after June 25 2026; earlier projects need a public ACR. "
                   "Source-code deploy of a hosted agent needs the extra firewall endpoints listed above.", kind="info", title="Hosted agent notes", size=14,
              src=[S_DEEP, S_VNET])
    pn.place(cv, px, e2 + 26)

    # ---- BYO VNet requirements (right column) + alternatives (left column)
    cw2 = (pw_ - 40) / 2
    req = Card(cw2, "BYO VNet requirements for the agent subnet", [
        "Dedicated subnet delegated to Microsoft.App/environments; several Foundry resources may share the VNet but not the subnet",
        "Minimum /27, recommended /24; subnet name up to 63 UTF-8 bytes",
        "RFC 1918 ranges (10/8, 172.16/12, 192.168/16); RFC 6598 100.64.0.0/10 is disputed between pages (see 'Docs disagree' below)",
        "Foundry resource in the same region as the VNet; PEs in the same region and subscription; peered VNets must not overlap",
        "Must be set at account creation: can't be added later, and the subnet can't be changed (new projects or redeploy); takes effect with the first hosted agent",
    ], theme="indigo", icon="subnet", src=[S_NETOPT, S_VNET])
    res = Card(cw2, "Ranges that must not overlap", [
        "169.254.0.0/16, 172.30.0.0/16, 172.31.0.0/16, 192.0.2.0/24",
        "0.0.0.0/8, 127.0.0.0/8",
        "100.100.0.0/17, 100.100.192.0/19, 100.100.224.0/19",
        "Don't use 172.17.0.0/16 (Docker bridge)",
        "! Docs disagree on 100.64.0.0/10 (CGNAT) - verify before you pick it",
    ], theme="indigo", icon="route-table", src=[S_NETOPT, S_VNET])
    r_, b_ = row(cv, px, pn.bottom + 30, [req, res], gap=40)
    alt = Card(lw, "Why BYO VNet here - and what the alternatives lose", [
        "Public egress + private endpoint secures only the inbound path; egress stays public",
        "Managed virtual network: Microsoft-managed VNet; FQDN rules create a billed managed Azure Firewall; no BYO firewall; portal can't create it; 18 regions as of 2026-11-03",
        "Network security perimeter: works for basic and evaluation setups, not when you use private endpoints + UDRs (this baseline)",
        "Full comparison: see the canvas 'Network isolation'",
    ], theme="gray", icon="nsp", src=[S_MANVNET, S_NSP, S_NETOPT])
    alt.place(cv, 0, ln2.bottom + 30)
    return max(b_, alt.bottom) + 60


# ----------------------------------------------------------------------------------------------------- 5 docs disagree
def _disagree(cv, y):
    y = chapter(cv, y, "5  Decision points that depend on the page you read",
                f"Where the documentation pages contradict each other ({ASOF}), both views are drawn: check the live pages before you commit")
    nw = (W - 40) / 2
    d1 = Note(nw, "The landing-zone article lists only the three RFC 1918 ranges for the agent subnet: 10.0.0.0/8, 172.16.0.0/12 and 192.168.0.0/16. The networking-options "
                  "and virtual-networks pages also allow RFC 6598 100.64.0.0/10 (excluding 100.100.0.0/17, 100.100.192.0/19 and 100.100.224.0/19). The agents-networking-deep-dive "
                  "page says CGNAT 100.64.0.0/10 is not supported because it causes routing failures.", kind="warn",
              title="Docs disagree: is RFC 6598 (CGNAT 100.64.0.0/10) allowed for the agent subnet?", size=15,
              src=[S_NETOPT, S_VNET, S_DEEP])
    d2 = Note(nw, "One passage says five containers; another says three containers and 3,000 RU/s. The use-your-own-resources page says 3 to 5 containers per project at "
                  "1,000 RU/s each, depending on the runtime (classic: thread-message-store, system-thread-message-store, agent-entity-store; Responses API adds "
                  "agent-definitions-v1 and run-state-v1). The account needs at least 3,000 RU/s; too little RU/s fails provisioning.", kind="warn",
              title="Docs disagree: how many Cosmos DB containers and how much RU/s does Agent Service need?", size=15, src=[S_OWN, S_SAS])
    hh = max(d1.h, d2.h)
    d1.place(cv, 0, y, h=hh)
    d2.place(cv, nw + 40, y, h=hh)
    nx = Note(W, "Part 2 of this canvas ('Baseline chat: decisions, operations and gotchas') covers the design forks (prompt vs hosted agent, app tier, chat history), "
                 "which tools still work behind the VNet, the zone-redundancy and recovery map, security, cost and operations guidance, and four production traps "
                 "(WAF tuning, portal access, conversation isolation, cost surprises).", kind="key", title="Continue with part 2", size=15)
    nx.place(cv, 0, y + hh + 26)
    return nx.bottom + 50


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _topology(cv, y)
    y = _ops(cv, y)
    y = _dns(cv, y)
    y = _rbac(cv, y)
    y = _netmatrix(cv, y)
    y = _disagree(cv, y)
    _sources(cv, y)
