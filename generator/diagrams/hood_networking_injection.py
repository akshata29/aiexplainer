"""Under the hood: Agent Service networking - container injection, delegated subnet, private endpoints, DNS,
managed VNet and the hosted-agent egress proxy, drawn as three packet paths.

Evidence convention on this canvas: solid border = documented on Microsoft Learn, dashed amber = video/blog only,
dotted grey ('?') = not documented or inferred."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-networking-injection", title="Networking internals: container injection and private paths",
    section="8", order=6,
    description="Packet paths through Agent Service networking: container injection into your delegated subnet, private endpoints and DNS, managed VNet, and the hosted-agent egress proxy.",
    tags=["networking", "vnet injection", "private endpoint", "dns", "egress"],
)

W = 3300            # canvas width
MAIN = 2260         # main column
SIDE_X = MAIN + 80
SIDE_W = W - SIDE_X
HALF = (W - 60) // 2

# arrow colours (evidence: solid = Learn, dashed amber = video/blog, dotted grey = not documented)
C_HOSTED, C_PROMPT, C_OWN, C_SHARED, C_FRONT = "#1971c2", "#2f9e44", "#e03131", "#3b5bdb", "#343a40"

LD = learn
YT = "https://www.youtube.com/watch?v="


# ---------------------------------------------------------------------------------------------- helpers
def vb_card(w, title, body, theme="yellow", **kw):
    """Video / blog-only claim: dashed amber border."""
    return Card(w, f"(video/blog) {title}", body, theme=theme, fill="soft", dash="dashed", **kw)


def nd_card(w, title, body, **kw):
    """Not documented or inferred: dotted grey border, '?' in the title."""
    return Card(w, f"? {title}", body, theme="gray", fill="soft", dash="dotted", **kw)


def nd_box(w, label, sub=None, h=None, **kw):
    """Not documented: dotted grey '?' box."""
    return Box(w, f"? {label}", sub=sub, h=h, theme="gray", fill="soft", dash="dotted", **kw)


def vb_place(cv, card, x, y, label, url, h=None):
    """Place a card and add a clickable video/blog citation line in its bottom padding."""
    base = card.h
    card.place(cv, x, y, h=max(h or 0, base + 20))
    cv.text(x + card.pad, y + base - card.pad + 6, f"Video/blog: {label}", size=12, color=LINK, link=url)
    return card


def rect_of(x, y, w, h):
    r = Rect2()
    r.x, r.y, r.w, r.h = x, y, w, h
    return r


GREY = "#868e96"


def tile(cv, x, y, w, h, big, caption, theme, kind="doc"):
    """Big-number tile: solid hatch = Learn, dashed soft = video/blog, dotted grey = not documented."""
    th = THEMES[theme]
    if kind == "doc":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y, w, h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
    cv.text(x, y + 10, big, size=36, color=th.deep if kind != "nd" else GREY, align="center", w=w)
    lines = wrap_text(caption, (w - 30) * 0.96, 15)
    cv.text(x + 15, y + 10 + 36 * 1.25 + 2, "\n".join(lines), size=15, color=INK if kind != "nd" else MUTED,
            align="center", w=w - 30)
    cv.register("tile", x, y, w, h)


def numbers_grid(cv, x, y, w):
    """Six big-number tiles (3 x 2) for the side column; returns the bottom y."""
    cv.text(x, y, "Numbers to remember (as of 2026-11-03)", size=22, color=INK)
    tiles = [
        ("1 : 1", "default hosted sessions per usable subnet IP; Azure support can raise it to 1:10", "indigo", "doc"),
        ("2 NICs", "per Micro VM; Learn describes only the dedicated one in your subnet", "indigo", "doc"),
        ("~10 IPs", "static pool per project for prompt agents; their versions use none", "green", "doc"),
        ("18", "regions with a managed VNet for prompt and hosted agents", "violet", "doc"),
        ("~30 d", "egress-proxy CA rotation inside the sandbox (preview)", "pink", "doc"),
        ("HTTP 403", "what the agent's client gets when the egress proxy denies a call (preview)", "pink", "doc"),
    ]
    gap = 24
    tw = (w - 2 * gap) / 3
    th = 134
    top = y + 40
    for i, (big, cap, theme, kind) in enumerate(tiles):
        r, c = divmod(i, 3)
        tile(cv, x + c * (tw + gap), top + r * (th + gap), tw, th, big, cap, theme, kind)
    return top + 2 * th + gap


def link_lines(cv, x, y, items, size=12, prefix="Learn: "):
    for label, url in items:
        t = cv.text(x, y, f"{prefix}{label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def src_panel(cv, x, y, items, w, cols, title, theme="gray", dash="solid", size=14):
    """Citation panel (own version so Learn sources keep a solid border and video/blog sources a dashed one)."""
    th = THEMES[theme]
    colw = (w - 40 - 24 * (cols - 1)) / cols
    entries = []
    for label, url in items:
        l1 = wrap_text(label, colw * 0.965, size)
        l2 = wrap_text(short_url(url), colw * 0.965, size - 2, MONO)
        h = len(l1) * size * metrics.line_ratio() + len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
        entries.append((l1, l2, url, h))
    per_col = -(-len(entries) // cols)
    heights = [sum(e[3] for e in entries[c * per_col:(c + 1) * per_col]) for c in range(cols)]
    H = 30 + max(heights) + 36
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash=dash)
        cv.text(x + 20, y + 14, title, size=size + 4, color=th.deep)
        for c in range(cols):
            cx = x + 20 + c * (colw + 24)
            cy = y + 14 + 30 + 6
            for l1, l2, url, h in entries[c * per_col:(c + 1) * per_col]:
                cv.text(cx, cy, "\n".join(l1), size=size, color=INK)
                cy += len(l1) * size * metrics.line_ratio()
                cv.text(cx, cy, "\n".join(l2), size=size - 2, color=LINK, font=MONO, link=url)
                cy += len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
    cv.register("sources", x, y, w, H)
    return y + H


# ---------------------------------------------------------------------------------------------- top band
def legend_panel(cv, x, y, w):
    with cv.panel(x, y, title="How to read this canvas", theme="gray", style="solid", fill="soft", pad=20,
                  title_size=22, w=w) as lg:
        cx, cy = lg.ix, lg.iy
        s_w = (w - 40 - 2 * 24) / 3
        Box(s_w, "Solid border: documented on Microsoft Learn", theme="green", fill="soft", h=62, size=15).place(cv, cx, cy)
        Box(s_w, "Dashed amber: video / blog only (video/blog)", theme="yellow", fill="soft", dash="dashed", h=62,
            size=15).place(cv, cx + s_w + 24, cy)
        Box(s_w, "Dotted grey ?: not documented or inferred", theme="gray", fill="soft", dash="dotted", h=62,
            size=15).place(cv, cx + 2 * (s_w + 24), cy)
        by = cy + 80
        draw_badge(cv, cx, by, "preview")
        cv.text(cx + 80, by + 3, "preview feature; 'as of 2026-11-03' marks time-sensitive facts", size=15)
        ay = by + 52
        items = [(C_HOSTED, "hosted-agent request"), (C_PROMPT, "prompt-agent request"),
                 (C_OWN, "agent's own outbound"), (C_SHARED, "tool path: Data Proxy to private endpoints"),
                 (C_FRONT, "client to gateway")]
        ax = cx
        for i, (color, label) in enumerate(items):
            if i == 3:
                ax, ay = cx, ay + 34
            arrow(cv, [(ax, ay), (ax + 50, ay)], color=color, sw=3)
            t = cv.text(ax + 60, ay - 10, label, size=15)
            ax += 60 + t.w + 30
    return lg


def at_a_glance(w):
    return Card(w, "At a glance", [
        "Inject: Micro VMs and the Data Proxy take IPs from YOUR delegated subnet (Microsoft.App/environments)",
        "Size: /27 minimum, /24 recommended; default 1 IP per concurrent hosted session",
        "Resolve: private DNS zones keep names inside your VNet (Azure DNS virtual server 168.63.129.16)",
        "Lock-in: BYO VNet injection is set when the account is created - it can't be added or changed later",
        "Tool calls always go through the single-tenant Data Proxy, even from a Micro VM that has its own NIC",
    ], theme="indigo", icon="vnet", src=[("Networking deep dive", LD("agents/concepts/agents-networking-deep-dive")),
                                           ("Networking options", LD("agents/concepts/networking-options"))])


def model_cards(w):
    gap = 50
    cw = (w - 2 * gap) / 3
    pub = Card(cw, "Public egress", [
        "No config = fully public baseline; nothing is private until you choose",
        "Inbound: public (optionally selected IPs) or a private endpoint",
        "Public network access flag: Enabled, Enabled from selected IP addresses, or Disabled",
        "A private endpoint here secures only the inbound path - agent egress stays public",
        "Best for prototyping and tests",
    ], theme="blue", icon="public-ip", subtitle="egress model 1", src=[("Networking options", LD("agents/concepts/networking-options"))])
    byo = Card(cw, "BYO virtual network = container injection", [
        "Agents are injected into a subnet you delegate and manage",
        "Inbound: private endpoint in your VNet",
        "You own IP ranges, peering, UDRs and firewall",
        "Needs ACA delegation, project capability host, IP class range, /27 minimum",
        "Full isolation",
    ], theme="indigo", icon="vnet", subtitle="egress model 2", src=[("Set up private networking", LD("agents/how-to/virtual-networks"))])
    mng = Card(cw, "Managed virtual network", [
        "Microsoft-managed VNet created in the Microsoft tenant for your account",
        "Inbound: private endpoint; no IP ranges to manage, overlapping IP space is fine",
        "Prompt and hosted agents (new Responses API, new portal) in 18 regions as of 2026-11-03",
        "Full isolation without running a network",
    ], theme="violet", icon="private-access", subtitle="egress model 3",
        src=[("Managed virtual network", LD("how-to/managed-virtual-network"))])
    return [pub, byo, mng]


# ---------------------------------------------------------------------------------------------- Case 1: BYO VNet
def hero_byo(cv, x0, y0):
    """BYO VNet standard agent setup. Two zones, container injection boundary, numbered hops. Returns bottom y."""
    ZL, GAP, ZR, H = 760, 80, 1420, 1510
    xl, xr = x0, x0 + ZL + GAP

    with cv.panel(xl, y0, title="Microsoft-managed Foundry platform network", sub="Microsoft tenant: you never see these hosts",
                  theme="gray", style="solid", fill="soft", w=ZL, h=H, pad=24, title_size=24, sub_size=15):
        pass
    with cv.panel(xr, y0, title="Your customer VNet", sub="template reference topology: VNet 192.168.0.0/16, agent subnet /24, PE subnet /24",
                  theme="indigo", style="solid", fill="soft", w=ZR, h=H, pad=24, title_size=24, sub_size=15):
        pass
    sx = xl + ZL + GAP / 2 - 20
    cv.rect(sx, y0 + 20, 40, H - 40, stroke="#3b5bdb", fill="#dbe4ff", style="solid", sw=2, rough=0)
    lbl = cv.text(0, 0, "container injection boundary", size=18, color="#364fc7")
    lbl.el["x"], lbl.el["y"] = sx + 20 - lbl.w / 2, y0 + 20 + 40 + lbl.w / 2 - lbl.h / 2
    lbl.el["angle"] = -1.5708

    # ---- customer VNet contents
    K = Box(300, "Client", sub="in your VNet, or via VPN / ExpressRoute / Bastion", theme="gray", fill="solid", icon="users",
            icon_pos="left", h=104).place(cv, xr + 24, y0 + 96)
    Note(790, "Your resolver (Azure DNS virtual server 168.63.129.16, or your DNS server forwarding to it) answers "
              "<acct>.services.ai.azure.com through the privatelink alias with the private endpoint's IP. "
              "From outside the VNet the same name resolves to a public IP.",
         kind="info", title="1  who resolves what", size=15).place(cv, xr + 24 + 300 + 40, y0 + 96, h=104)

    band_y, band_h = y0 + 256, 206
    cv.rect(xr + 24, band_y, ZR - 48, band_h, stroke="#3b5bdb", fill="#edf2ff", style="solid", sw=2)
    cv.text(xr + 330, band_y + 12, "Private-endpoint subnet", size=20, color="#364fc7")
    cv.text(xr + 330, band_y + 40, "PEs to Search, Storage and Cosmos DB are NOT auto-created with the Foundry resource", size=14,
            color="#495057")
    numbered(cv, xr + 640, band_y + 23, 8, theme="gray", d=26, size=15)
    cv.text(xr + 662, band_y + 14, "platform persistence also lands here (writer not named)", size=14, color="#495057")
    tile_w, tile_gap = 256, 14
    tiles = []
    for i, (lab, sub, th, ic) in enumerate([("PE: Foundry account", "sub-resource: account", "blue", "private-endpoint"),
                                            ("PE: Cosmos DB", "sub-resource: Sql", "cyan", "cosmos"),
                                            ("PE: Storage", "sub-resource: blob", "cyan", "storage"),
                                            ("PE: AI Search", "sub-resource: searchService", "teal", "ai-search"),
                                            ("PE: Key Vault", "named in the deep dive", "red", "key-vault")]):
        t = Box(tile_w, lab, sub=sub, theme=th, fill="solid", icon=ic, icon_pos="left", icon_size=30, h=96, size=16,
                sub_size=13).place(cv, xr + 42 + i * (tile_w + tile_gap), band_y + 92)
        tiles.append(t)
    A = tiles[0]

    sub_y, sub_h = y0 + 540, 730
    with cv.panel(xr + 24, sub_y, title="Delegated subnet: Microsoft.App/environments",
                  sub="dedicated to one Foundry resource | /27 minimum, /24 recommended | size fixed after assignment",
                  theme="indigo", style="solid", fill="none", w=1036, h=sub_h, pad=24, title_size=22, sub_size=14):
        pass
    mx, my, mw, mh = xr + 54, y0 + 650, 430, 230
    for off in (28, 14):
        cv.rect(mx + off, my + off, mw, mh, stroke="#2f9e44", fill="#ebfbee", style="solid", sw=2)
    with cv.panel(mx, my, title="Micro VM", sub="one per session; 1 IP from this subnet",
                  theme="green", style="solid", fill="soft", w=mw, h=mh, pad=18, title_size=22, sub_size=14) as M:
        cy = M.iy + 4
        Chip("NIC 1: delegated subnet", theme="indigo", size=14, fill="solid").place(cv, M.ix, cy)
        Chip("NIC 2: role not described", theme="gray", size=14, fill="soft", dash="dotted").place(cv, M.ix, cy + 40)
        Chip("egress proxy (preview)", theme="pink", size=14, fill="solid").place(cv, M.ix, cy + 80)
        Chip("your agent container", theme="green", size=14, fill="solid").place(cv, M.ix + 215, cy)
    Card(430, "IP budget", [
        "1 IP per concurrent hosted session (default 1:1)",
        "plus project-level parts such as the Data Proxy",
        "prompt-agent versions consume no IPs",
    ], theme="indigo", fill="soft", title_size=18, body_size=15).place(cv, mx, my + mh + 70)
    nd_box(230, "Not documented", sub="Which DNS resolver the Micro VM uses for its own lookups", h=120,
           size=15, sub_size=14).place(cv, xr + 520, my + mh + 30)
    P = Box(420, "Single-tenant Data Proxy", sub="one isolated instance per project; IPs come from this subnet", theme="indigo",
            fill="solid", icon="private-link", icon_pos="left", h=120, size=18).place(cv, xr + 560, y0 + 1100)
    C = Box(300, "Your network controls", sub="NSG, UDRs, optional Azure Firewall in a hub VNet, peering", theme="red",
            fill="soft", icon="firewall", icon_pos="left", h=150, size=17).place(cv, xr + 1100, my + 40)

    dy = y0 + 1340
    with cv.panel(xr + 24, dy, title="Private DNS zones linked to your VNet", theme="indigo", style="solid", fill="none",
                  w=ZR - 48, h=150, pad=20, title_size=20) as dz:
        zones = ["privatelink.services.ai.azure.com", "privatelink.cognitiveservices.azure.com", "privatelink.openai.azure.com",
                 "privatelink.search.windows.net", "privatelink.documents.azure.com", "privatelink.blob.core.windows.net",
                 "privatelink.vaultcore.azure.net"]
        ChipFlow(zones, ZR - 48 - 40, theme="cyan", size=14, fill="soft").place(cv, dz.ix, dz.iy - 2)

    # ---- platform network contents
    ex = xl + 370
    Ebox = Box(366, "Foundry endpoint (API gateway)", sub="authenticates, then routes by target agent type", theme="blue",
               fill="solid", icon="foundry", icon_pos="left", h=130, size=18).place(cv, ex, A.y + A.h / 2 - 65)
    Hbox = Box(366, "Micro VM host layer", sub="runs Hosted agents", theme="green", fill="solid", icon="vm", icon_pos="left",
               h=130, size=18).place(cv, ex, my + mh / 2 - 65)
    Tbox = Box(366, "Tools Service", sub="runs service-side tools", theme="orange", fill="solid", icon="toolbox-icon",
               icon_pos="left", h=120, size=18).place(cv, ex, y0 + 905)
    Dbox = Box(366, "Data Proxy host layer", sub="hosts the single-tenant proxy", theme="indigo", fill="solid",
               icon="private-link", icon_pos="left", h=120, size=18).place(cv, ex, P.y + P.h / 2 - 60)
    PR = Box(300, "Prompt-agent runtime", sub="Microsoft-managed compute (Learn: on Azure Container Apps)", theme="green",
             fill="hatch", icon="container-apps", icon_pos="left", h=130, size=17).place(cv, xl + 24, Hbox.y)
    Card(300, "Prompt agents", [
        "No Micro VM on this path",
        "Versions consume no IPs; a small static pool per project (up to about 10)",
    ], theme="green", fill="soft", title_size=18, body_size=15,
        src=[("Networking options", LD("agents/concepts/networking-options"))]).place(cv, xl + 24, Tbox.y + 90)
    ci = Note(ZL - 48, "The platform places Micro VMs and the Data Proxy INTO your delegated subnet, so they consume your IPs, "
                       "while their control layers stay in the platform network.", kind="key", title="Container injection", size=15)
    ci.place(cv, xl + 24, y0 + 1236)
    av = Note(ZL - 48, "Learn's diagram annotates the Micro VMs and the Data Proxy as 'on Azure Container Apps'. A Reactor presenter (2026-04-27) described "
                       "the new hosted-agent platform as a different 'fast micro VM platform'. No ACA is drawn inside the Micro VM here; the hypervisor isn't named anywhere.",
              kind="warn", title="Docs and video disagree: what is under the Micro VM?", size=15, dash="dashed",
              src=[("Reactor: Host your agents on Foundry (about 0:40)", YT + "8N7q0Ucr3rw")])
    av.src_lines = [(t.replace("Learn: ", "Video: ", 1), u, off) for (t, u, off) in av.src_lines]
    av.place(cv, xl + 24, ci.bottom + 16)
    Card(ZL - 48, "Front door (ingress)", [
        "Clients send HTTPS to <resource>.services.ai.azure.com",
        "The API gateway authenticates the request and routes it by target agent type",
        "Hosted agents: only an allow-list of caller headers is forwarded (x-client-*, content negotiation, tracing); never Authorization, Host, Cookie or x-forwarded-*",
    ], theme="blue", fill="soft", title_size=18, body_size=15, icon="foundry", icon_size=30,
        src=[("Networking deep dive", LD("agents/concepts/agents-networking-deep-dive")),
             ("Hosted agent contract", LD("agents/concepts/hosted-agent-contract"))]).place(cv, xl + 24, y0 + 96)

    # ---- arrows (hops)
    connect(cv, K, A, a_side="bottom", b_side="top", num=1, color=C_FRONT, sw=3, gap=4)
    connect(cv, A, Ebox, a_side="left", b_side="right", num=2, color=C_FRONT, sw=3)
    connect(cv, Ebox, Hbox, a_side="bottom", b_side="top", num=3, color=C_HOSTED, sw=3, label="hosted agent", label_size=14)
    connect(cv, Ebox, PR, a_side="left", b_side="top", route="elbow", color=C_PROMPT, sw=3, label="prompt agent", label_size=14,
            label_t=0.3)
    connect(cv, Hbox, M, a_side="right", b_side="left", tb=0.3, ta=0.3, num=4, color=C_HOSTED, sw=3)
    connect(cv, M, C, a_side="right", b_side="left", ta=0.5, num=5, color=C_OWN, sw=3, label="own outbound via NIC 1",
            label_size=14, label_wrap=130, label_t=0.2, label_dy=-16)
    connect(cv, M, Tbox, a_side="left", b_side="right", ta=0.85, num=6, color=C_HOSTED, sw=3)
    connect(cv, PR, Tbox, a_side="bottom", b_side="left", route="elbow", color=C_PROMPT, sw=3)
    connect(cv, Tbox, Dbox, a_side="bottom", b_side="top", color=C_SHARED, sw=3, label="calls the proxy", label_size=14)
    connect(cv, Dbox, P, a_side="right", b_side="left", color=C_SHARED, sw=3, label="injected into your subnet", label_size=14,
            label_t=0.5)
    connect(cv, P, rect_of(xr + 24, band_y, ZR - 48, band_h), a_side="top", b_side="bottom", tb=(P.cx - (xr + 24)) / (ZR - 48),
            num=7, color=C_SHARED, sw=3, label="via private endpoints", label_size=14, label_t=0.8, bind=False)
    return y0 + H


def hero_side(cv, x, y):
    rows = [
        [("1", "gray"), "Client to PE", "Resolver (Azure DNS 168.63.129.16, or your DNS server) maps <acct>.services.ai.azure.com to the PE IP through the privatelink alias. The PE must be Approved."],
        [("2", "gray"), "PE to Foundry endpoint", "The API gateway authenticates the request, then routes it by target agent type."],
        [("3", "blue"), "Gateway to Micro VM host layer", "Hosted agent: the Micro VM path. Prompt agent: Microsoft-managed compute, no Micro VM."],
        [("4", "blue"), "Host layer to your subnet", "The platform provisions or resumes the Micro VM and takes 1 IP; none free means HTTP 429 subnet_exhausted. The request is forwarded into the container (Learn's diagram labels this hop /invoke; the public routes are /responses and /invocations)."],
        [("5", "red"), "Agent's own outbound", "Dedicated NIC in your subnet, so your NSG, UDRs and firewall apply. Which resolver it uses: not documented."],
        [("5a", "gray"), "Model call from your code", "The code calls its project endpoint, and the platform proxies the call to the account-level deployment with the project managed identity. Learn's networking page doesn't draw this hop, so how it crosses your VNet isn't shown here."],
        [("6", "blue"), "Tool calls", "Micro VM (or prompt compute) to Tools Service to Data Proxy - never straight out of the VM, even with its own NIC."],
        [("7", "indigo"), "Data Proxy to private endpoints", "Reaches Storage, Cosmos DB, Search and Key Vault through PEs; the privatelink zones keep name resolution inside the VNet."],
        [("8", "yellow"), "Platform persistence", "The project managed identity uses your Cosmos DB, Storage and AI Search over PEs. Which component writes: not named on Learn. (video/blog): 'transitive VNet injection'."],
    ]
    t = Table([("#", 46), ("Hop", 230), "Who resolves or decides what"], rows, w=SIDE_W, theme="indigo", size=14, head_size=15,
              title="Packet path, hop by hop (BYO VNet)", title_size=22).place(cv, x, y)
    yy = link_lines(cv, x, t.bottom + 10, [("Networking deep dive", LD("agents/concepts/agents-networking-deep-dive")),
                                           ("Set up private networking for Agent Service", LD("agents/how-to/virtual-networks"))])
    c1 = Card(SIDE_W, "Capacity check before go-live (as of 2026-11-03)", [
        "Planned peak sessions <= 80% of usable IPs AND <= your regional session quota (default 1,000; 2,000 in seven regions)",
        "Over either limit? Ask Azure support for the 1:10 IP-to-session mapping or a bigger quota in one request",
        "Watch HTTP 429 subnet_exhausted and Data Proxy 5xx - the portal shows no IP utilisation for the subnet",
    ], theme="yellow", icon="quotas", src=[("Networking deep dive", LD("agents/concepts/agents-networking-deep-dive")),
                                           ("Quotas and limits", LD("agents/concepts/limits-quotas-regions"))]).place(cv, x, yy + 24)
    c2 = vb_card(SIDE_W, "Transitive VNet injection", [
        "Ignite 2025 BRK201 (about 0:37): even with private network access, 'we can use transitive VNET injection' to reach your Cosmos DB and Search and persist data into them",
        "Learn says the project managed identity does the runtime access over private endpoints; it doesn't use the term",
    ])
    vb_place(cv, c2, x, c1.bottom + 30, "Ignite 2025 BRK201", YT + "7faSLQS501E")
    c3 = nd_card(SIDE_W, "Not documented", [
        "Whether idle or stopped sessions release their delegated-subnet IP (the concurrency quota excludes idle sessions; IP behaviour at idle is not stated)",
        "The Micro VM's second NIC: Learn says two NICs and describes only the dedicated one in the delegated subnet",
    ])
    c3.place(cv, x, c2.bottom + 30)
    c4 = Note(SIDE_W, "Network isolation (section 5) has the decision tree, the Bicep templates and the policies. Baseline chat: network-isolated "
                      "(section 3) is the full reference architecture. Hosted agent runtime (this section) goes inside the Micro VM.",
              kind="key", title="See also in this gallery")
    c4.place(cv, x, c3.bottom + 30)
    return c4.bottom


# ---------------------------------------------------------------------------------------------- DNS section
def dns_section(cv, y):
    _, hb = section_header(cv, 0, y, "3  Private endpoints and DNS: one name, different answers depending on who asks", w=W,
                           sub="The connection string never changes: the name resolves through a privatelink alias, and only the final answer differs - a public IP from outside, the private endpoint IP from inside")
    y0 = hb + 34
    colw = 340
    X = [i * (colw + 140) for i in range(5)]

    def node(col, yy, label, sub=None, theme="gray", icon=None):
        return Box(colw, label, sub=sub, theme=theme, fill="solid", icon=icon, icon_pos="left", icon_size=30, h=92,
                   size=16, sub_size=13).place(cv, X[col], yy)

    ly = y0
    cv.text(0, ly, "A  From outside the VNet (internet client)", size=18, color="#495057")
    a1 = node(0, ly + 32, "Client on the internet", theme="gray", icon="users")
    a2 = node(1, ly + 32, "Public DNS", sub="returns the privatelink alias, then a public IP", theme="gray", icon="dns")
    a5 = node(4, ly + 32, "Public IP of the Foundry endpoint", sub="not the private endpoint", theme="blue", icon="foundry")
    connect(cv, a1, a2, label="query", color=C_FRONT, sw=3)
    connect(cv, a2, a5, label="alias, then a public A record", color=C_FRONT, sw=3)

    ly += 170
    cv.text(0, ly, "B  From inside the VNet, or connected to it (VM, VPN, ExpressRoute, Bastion)", size=18, color="#495057")
    b1 = node(0, ly + 32, "Client in or connected to the VNet", theme="gray", icon="users")
    b3 = node(2, ly + 32, "Azure DNS virtual server", sub="IP 168.63.129.16", theme="indigo", icon="dns-resolver")
    b4 = node(3, ly + 32, "Private DNS zone", sub="privatelink.services.ai.azure.com, linked to the VNet", theme="cyan", icon="dns")
    b5 = node(4, ly + 32, "Private endpoint IP", sub="the A record in the zone", theme="indigo", icon="private-endpoint")
    connect(cv, b1, b3, label="query", color=C_FRONT, sw=3)
    connect(cv, b3, b4, label="zone link", color=C_FRONT, sw=3)
    connect(cv, b4, b5, label="A record", color=C_FRONT, sw=3)

    ly += 170
    cv.text(0, ly, "C  From a custom or on-premises DNS server", size=18, color="#495057")
    c1 = node(0, ly + 32, "Client on-premises or in another network", theme="gray", icon="users")
    c2 = node(1, ly + 32, "Your DNS server", sub="custom or on-premises", theme="gray", icon="dns")
    c3 = node(2, ly + 32, "Azure DNS virtual server", sub="IP 168.63.129.16", theme="indigo", icon="dns-resolver")
    c4 = node(3, ly + 32, "Private DNS zone", sub="one zone per privatelink name", theme="cyan", icon="dns")
    c5 = node(4, ly + 32, "Private endpoint IP", sub="the A record in the zone", theme="indigo", icon="private-endpoint")
    connect(cv, c1, c2, label="query", color=C_FRONT, sw=3)
    connect(cv, c2, c3, label="forwarder", color=C_FRONT, sw=3)
    connect(cv, c3, c4, label="zone link", color=C_FRONT, sw=3)
    connect(cv, c4, c5, label="A record", color=C_FRONT, sw=3)
    cv.text(0, ly + 140, "Custom DNS: create a conditional forwarder to 168.63.129.16 for each zone in the table below - or delegate the privatelink "
                        "subdomain to the VNet's private zone, or add the A records on your own server.", size=15, color="#495057")

    ty = ly + 190
    rows = [
        [("Foundry account", "blue"), "account", "privatelink.cognitiveservices.azure.com\nprivatelink.openai.azure.com\nprivatelink.services.ai.azure.com",
         "cognitiveservices.azure.com\nopenai.azure.com\nservices.ai.azure.com"],
        [("Azure AI Search", "teal"), "searchService", "privatelink.search.windows.net", "search.windows.net"],
        [("Azure Cosmos DB", "cyan"), "Sql", "privatelink.documents.azure.com", "documents.azure.com"],
        [("Azure Storage", "cyan"), "blob", "privatelink.blob.core.windows.net", "blob.core.windows.net"],
        [("Key Vault", "red"), "vault", "privatelink.vaultcore.azure.net", "zone named in the deep dive"],
        [("Azure SQL Database", "gray"), "not listed", "privatelink.database.windows.net", "zone named as an example"],
    ]
    t = Table([("Private Link resource", 250), ("Sub-resource", 170), ("Private DNS zone(s)", 700), "Public DNS zone forwarder(s)"], rows,
              w=MAIN, theme="cyan", size=14, head_size=15, title="Private DNS zones to create and link to the VNet", title_size=22)
    t.place(cv, 0, ty)
    link_lines(cv, 0, t.bottom + 8, [("Set up private networking for Agent Service", LD("agents/how-to/virtual-networks")),
                                     ("Configure network isolation", LD("how-to/configure-private-link"))])

    # side column
    c_pe = Card(SIDE_W, "Private endpoint rules", [
        "The PE must be in the same region and subscription as the VNet; only PEs in Approved state carry traffic",
        "PEs to Search, Storage and Cosmos DB are NOT auto-created with the Foundry resource - create them yourself",
        "Under the template, accounts and projects default to Public network access Disabled, for REST and WebSocket",
        "Trusted-service exception: Foundry Tools, AI Search and Azure ML (Microsoft.CognitiveServices, Search, MachineLearningServices) via managed identity",
        "Search indexers over PEs: set executionEnvironment to Private; indexed knowledge sources' auto-generated indexers don't support it (silent failures, empty index)",
    ], theme="indigo", icon="private-link", src=[("Set up private networking", LD("agents/how-to/virtual-networks")),
                                                 ("Configure network isolation", LD("how-to/configure-private-link"))])
    c_pe.place(cv, SIDE_X, y0)
    n = Note(SIDE_W, "Same connection string everywhere: the FQDN doesn't change, only the answer does. If DNS returns a public IP "
                     "inside the VNet, check that the privatelink zone exists and is linked to the VNet; if it times out on 443, check NSG and firewall rules to the PE IP.",
             kind="tip", title="Debugging name resolution", src=[("Configure network isolation", LD("how-to/configure-private-link"))])
    n.place(cv, SIDE_X, c_pe.bottom + 30)
    n2 = Note(SIDE_W, "A custom DNS server overrides the private zones linked to the VNet. Use an Azure DNS Private Resolver (centralized DNS architecture) or, "
                      "if your DNS server runs on an Azure VM, a conditional forwarder to 168.63.129.16. Intermittent failures often mean the DNS server is "
                      "unreachable from some subnets.", kind="warn", title="Custom DNS: don't lose the private zones",
              src=[("Evaluations in a VNet", LD("concepts/evaluation-virtual-network")), ("Configure network isolation", LD("how-to/configure-private-link"))])
    n2.place(cv, SIDE_X, n.bottom + 30)
    return max(t.bottom + 40, n2.bottom)


# ---------------------------------------------------------------------------------------------- Case 2: managed VNet
def case_managed(cv, x0, y0):
    H = 1060
    with cv.panel(x0, y0, title="Your VNet", theme="indigo", style="solid", fill="soft", w=400, h=H, pad=22, title_size=22):
        pass
    with cv.panel(x0 + 450, y0, title="Foundry platform", sub="Microsoft tenant", theme="gray", style="solid", fill="soft", w=780,
                  h=H, pad=22, title_size=22, sub_size=14):
        pass
    with cv.panel(x0 + 1280, y0, title="Outside the managed VNet", theme="gray", style="solid", fill="soft", w=340, h=H, pad=22,
                  title_size=22):
        pass
    K = Box(300, "Client", sub="in your VNet, or via VPN, ExpressRoute or Bastion", theme="gray", fill="solid", icon="users",
            icon_pos="left", h=100).place(cv, x0 + 50, y0 + 90)
    A = Box(300, "PE: Foundry account", sub="inbound is still a private endpoint", theme="blue", fill="solid",
            icon="private-endpoint", icon_pos="left", h=100).place(cv, x0 + 50, y0 + 300)
    with cv.panel(x0 + 24, y0 + 470, title="Private DNS zones", sub="same zones as the BYO setup", theme="cyan", style="solid",
                  fill="none", w=352, pad=14, title_size=18, sub_size=13) as dz:
        cy = dz.iy
        for z in ("privatelink.services.ai.azure.com", "privatelink.cognitiveservices.azure.com", "privatelink.openai.azure.com"):
            Chip(z, theme="cyan", size=13, fill="soft").place(cv, dz.ix, cy)
            cy += 38
    nd_box(300, "Not documented", sub="DNS resolution inside the managed VNet isn't described on the managed-VNet page", h=140,
           size=15, sub_size=14).place(cv, x0 + 50, y0 + 740)

    E = Box(360, "Foundry endpoint (API gateway)", sub="authenticates, routes by agent type", theme="blue", fill="solid",
            icon="foundry", icon_pos="left", h=110).place(cv, x0 + 660, y0 + 90)
    with cv.panel(x0 + 470, y0 + 290, title="Managed virtual network", theme="violet",
                  style="solid", fill="none", w=740, h=730, pad=20, title_size=22):
        pass
    cv.text(x0 + 490, y0 + 972, "Created in the Microsoft tenant for your account; no customer-visible NICs or subnets", size=14,
            color="#495057")
    AG = Box(330, "Agent compute", sub="prompt and hosted agents; no delegated subnet, no IPs from your ranges", theme="green",
             fill="solid", icon="container-apps", icon_pos="left", h=130).place(cv, x0 + 490, y0 + 400)
    with cv.panel(x0 + 880, y0 + 390, title="Managed private endpoints", sub="created with the CLI only", theme="violet",
                  style="solid", fill="soft", w=310, pad=14, title_size=18, sub_size=13) as MPE:
        ChipFlow(["Cosmos DB", "Storage", "AI Search", "Key Vault", "Container Registry", "Application Gateway"], 280,
                 theme="violet", size=14, fill="solid").place(cv, MPE.ix, MPE.iy)
    Dia = Box(270, "Outbound mode?", shape="diamond", theme="violet", fill="soft", h=170).place(cv, x0 + 520, y0 + 640)
    FW = Box(330, "Managed Azure Firewall", sub="created at the first FQDN rule; FQDN rules on ports 80 and 443; Standard by default, Basic selectable",
             theme="red", fill="solid", icon="firewall", icon_pos="left", h=150).place(cv, x0 + 870, y0 + 650)
    D1 = Box(300, "Your Azure resources", sub="Cosmos DB, Storage, AI Search", theme="cyan", fill="solid", icon="cosmos",
             icon_pos="left", h=120).place(cv, x0 + 1300, y0 + 420)
    OP = Box(300, "On-premises", sub="through Application Gateway (L4 or L7)", theme="gray", fill="solid", icon="app-gateway",
             icon_pos="left", h=110).place(cv, x0 + 1300, y0 + 590)
    INT = Box(300, "Internet", sub="FQDN and service-tag destinations", theme="gray", fill="solid", icon="public-ip",
              icon_pos="left", h=110).place(cv, x0 + 1300, y0 + 850)

    connect(cv, K, A, a_side="bottom", b_side="top", num=1, color=C_FRONT, sw=3, gap=4)
    connect(cv, A, E, a_side="right", b_side="left", route="elbow", num=2, color=C_FRONT, sw=3, bend=0.23)
    connect(cv, E, AG, a_side="bottom", b_side="top", ta=0.33, tb=0.875, num=3, color=C_FRONT, sw=3)
    connect(cv, AG, MPE, a_side="right", b_side="left", ta=0.35, tb=0.3, num=4, color=C_SHARED, sw=3)
    connect(cv, MPE, D1, a_side="right", b_side="left", ta=0.3, tb=0.5, color=C_SHARED, sw=3, label="private link", label_size=14,
            label_dy=-4)
    connect(cv, MPE, OP, a_side="right", b_side="left", ta=0.85, tb=0.5, num=7, color=C_SHARED, sw=3)
    connect(cv, AG, Dia, a_side="bottom", b_side="top", num=5, color=C_OWN, sw=3)
    connect(cv, Dia, FW, a_side="right", b_side="left", color=C_OWN, sw=3, label="approved only", label_size=14, label_wrap=70)
    connect(cv, Dia, INT, a_side="bottom", b_side="left", route="elbow", color=C_OWN, sw=3, label="internet outbound", label_size=14,
            label_t=0.62)
    connect(cv, FW, INT, a_side="right", b_side="top", route="elbow", num=6, color=C_OWN, sw=3)
    return y0 + H


def managed_below(cv, x0, y):
    hw = (HALF - 50) / 2
    modes = Table([("Mode", 220), "What it does"], [
        [("Allow internet outbound", "violet"), "All outbound internet traffic is allowed. Can't be reconfigured back to Disabled."],
        [("Allow only approved outbound", "violet"), "Service tags, private endpoints and optional FQDN rules (ports 80 and 443) enforced by a managed Azure Firewall. Can't be loosened to internet outbound."],
        [("Disabled", "gray"), "Managed network isolation isn't enabled (unless a custom VNet is used)."],
    ], w=hw, theme="violet", size=14, head_size=15, title="Three outbound modes", title_size=22).place(cv, x0, y)
    yy = link_lines(cv, x0, modes.bottom + 8, [("Managed virtual network", LD("how-to/managed-virtual-network"))])
    appr = Card(hw, "Approving the managed private endpoints", [
        "The Foundry account's managed identity needs Azure AI Enterprise Network Connection Approver (role ID b556d68e-0be0-4f35-a333-ad7ee1ce17ea) on the target",
        "Azure SQL also needs Reader on the target's resource group; Container Registry needs Reader",
        "In approved-only mode the platform auto-creates PEs to your Cosmos DB, Storage and AI Search, plus the AzureActiveDirectory service tag",
        "Managed PEs show no NIC or subnet in your subscription",
    ], theme="violet", icon="managed-identity", src=[("Managed virtual network", LD("how-to/managed-virtual-network"))])
    appr.place(cv, x0 + hw + 50, y)
    lim = Card(hw, "Limits and lifecycle (as of 2026-11-03)", [
        "Can't be disabled once enabled; no upgrade path from BYO VNet (redeploy); deleting the Foundry resource deletes it",
        "Create with Bicep, Terraform, az rest or the CLI - the portal UI can't create the managed network",
        "Free feature, but Private Link and the managed firewall are charged; one firewall per account, no bring-your-own",
        "No outbound traffic logging yet; on-premises access goes through Application Gateway",
    ], theme="violet", badge="preview", src=[("Managed virtual network", LD("how-to/managed-virtual-network"))])
    lim.place(cv, x0, yy + 24)
    vb = vb_card(hw, "Hosted-agent managed VNet", [
        "The Build blog (2026-06-02) listed 'Managed virtual network for Hosted agents' as a road-to-GA item",
        "The Learn page now says managed VNet supports Prompt and Hosted agents",
    ])
    vb_place(cv, vb, x0 + hw + 50, appr.bottom + 30, "Foundry blog, What's new in hosted agents", "https://devblogs.microsoft.com/foundry/hosted-agents-build26/")
    y2 = max(lim.bottom, vb.bottom) + 36
    p1 = ChipFlow(["Foundry (AI Services)", "Application Gateway", "API Management (Classic, Standard v2)", "AI Search", "Container Registry",
                   "Cosmos DB", "Data Factory", "MariaDB, MySQL, PostgreSQL", "Databricks", "Event Hubs", "Key Vault",
                   "Azure ML", "Redis", "SQL Server", "Storage", "Application Insights (via AMPLS)"], HALF - 40, theme="violet", size=14, fill="soft")
    with cv.panel(x0, y2, title="Private-endpoint targets supported from the managed network (CLI only)", theme="violet", style="solid",
                  fill="none", w=HALF, pad=18, title_size=20) as pp:
        p1.place(cv, pp.ix, pp.iy)
    y3 = pp.bottom + 24
    p2 = ChipFlow(["*.identity.azure.net", "login.microsoftonline.com", "*.login.microsoftonline.com", "*.login.microsoft.com",
                   "mcr.microsoft.com", "or the AzureActiveDirectory service tag"], HALF - 40, theme="red", size=14, fill="soft")
    with cv.panel(x0, y3, title="Agent FQDN rules you may need in approved-only mode", theme="red", style="solid", fill="none",
                  w=HALF, pad=18, title_size=20) as pf:
        p2.place(cv, pf.ix, pf.iy)
    y4 = pf.bottom + 24
    p3 = ChipFlow(["East US", "East US 2", "Japan East", "France Central", "UAE North", "Brazil South", "Spain Central",
                   "Germany West Central", "Italy North", "South Central US", "Australia East", "Sweden Central", "Canada East",
                   "South Africa North", "West US", "West US 3", "South India", "UK South"], HALF - 40, theme="gray", size=14, fill="soft")
    with cv.panel(x0, y4, title="18 supported regions (as of 2026-11-03)", theme="gray", style="solid", fill="none", w=HALF, pad=18,
                  title_size=20) as pr:
        p3.place(cv, pr.ix, pr.iy)
    return pr.bottom


# ---------------------------------------------------------------------------------------------- Case 3: egress proxy
def case_egress(cv, x0, y0):
    H = 1060
    SW = 1140
    ox = x0 + SW + 50
    with cv.panel(x0, y0, title="Micro VM sandbox (Foundry-managed)", sub="your code runs here; the egress proxy lives inside it",
                  theme="green", style="solid", fill="soft", w=SW, h=H, pad=22, title_size=22, sub_size=14):
        pass
    with cv.panel(ox, y0, title="Outside the sandbox", theme="gray", style="solid", fill="soft", w=HALF - SW - 50, h=H, pad=22,
                  title_size=22):
        pass
    a1 = Box(250, "Agent code", sub="your HTTP client: requests, gRPC, Node.js", theme="green", fill="solid", icon="code",
             icon_pos="left", h=120).place(cv, x0 + 30, y0 + 150)
    a2 = Box(270, "TLS client", sub="trusts the proxy CA the runtime injected", theme="pink", fill="soft", icon="security",
             icon_pos="left", h=120).place(cv, x0 + 380, y0 + 150)
    a3 = Box(280, "Egress proxy (preview)", sub="ordered host rules; fail-closed", theme="pink", fill="solid",
             icon="content-safety", icon_pos="left", h=120).place(cv, x0 + 740, y0 + 150)
    a4 = Box(300, "First matching rule?", shape="diamond", theme="pink", fill="soft", h=200).place(cv, x0 + 730, y0 + 390)
    deny = Box(330, "Deny", sub="Enforced: HTTP 403 goes to the agent's HTTP client. Audit: the request still flows and the would-deny is logged",
               theme="red", fill="solid", icon="nsg", icon_pos="left", h=160).place(cv, x0 + 300, y0 + 410)
    span = Box(300, "Network egress decision", sub="span: decision, reason, matched rule, rule source, enforcement, destination, default action",
               theme="violet", fill="solid", icon="app-insights", icon_pos="left", h=150).place(cv, x0 + 730, y0 + 680)
    nd_box(320, "Not documented", sub="Where the proxy sits relative to the VM's two NICs and your subnet controls isn't drawn on Learn. Dashed arrows 4 and 7 are inferred from "
                                       "'enforced inside the sandbox before traffic leaves the runtime'",
           h=190, size=15, sub_size=14).place(cv, x0 + 30, y0 + 690)
    nd_box(320, "Not documented", sub="Whether service-side tool traffic (Tools Service to Data Proxy) is subject to egress rules",
           h=190, size=15, sub_size=14).place(cv, x0 + 370, y0 + 690)
    O1 = Box(380, "Network path out", sub="BYO VNet: your NSG, UDRs, Azure Firewall. Managed VNet: the managed firewall rules", theme="indigo",
             fill="solid", icon="firewall", icon_pos="left", h=170).place(cv, ox + 24, y0 + 405)
    O2 = Box(380, "Destination", sub="internet, private endpoint or on-premises host", theme="gray", fill="solid", icon="public-ip",
             icon_pos="left", h=110).place(cv, ox + 24, y0 + 640)
    O3 = Box(380, "Application Insights and the Trajectories tab", sub="traces | where message == 'Network egress decision'",
             theme="violet", fill="solid", icon="app-insights", icon_pos="left", h=130).place(cv, ox + 24, y0 + 850)

    connect(cv, a1, a2, num=1, color=C_OWN, sw=3, label="HTTPS call", label_size=14, label_dy=-14, label_dx=-18)
    connect(cv, a2, a3, num=2, color=C_OWN, sw=3, label="via the proxy", label_size=14, label_dy=-14)
    connect(cv, a3, a4, a_side="bottom", b_side="top", num=3, color=C_OWN, sw=3, label="evaluate", label_size=14)
    connect(cv, a4, O1, a_side="right", b_side="left", num=4, color=C_OWN, sw=3, dash="dashed", label="Allow, Transform or Rewrite",
            label_size=14, label_wrap=150, label_dy=-22)
    connect(cv, a4, deny, a_side="left", b_side="right", num=5, color=C_OWN, sw=3, label="Deny", label_size=14, label_dy=-14)
    connect(cv, deny, a1, a_side="left", b_side="bottom", route="elbow", color=C_OWN, sw=3, label="403", label_size=14, label_t=0.8)
    connect(cv, a4, span, a_side="bottom", b_side="top", num=6, color=C_FRONT, sw=3, label="every decision", label_size=14)
    connect(cv, span, O3, a_side="right", b_side="left", route="elbow", color=C_FRONT, sw=3)
    connect(cv, O1, O2, a_side="bottom", b_side="top", num=7, color=C_OWN, sw=3, dash="dashed")
    return y0 + H


def egress_below(cv, x0, y):
    hw = (HALF - 50) / 2
    rules = Table([("Rule model", 190), "How it works"], [
        [("Order", "pink"), "Rules are evaluated top to bottom; the first match wins"],
        [("Default", "pink"), "No match: the policy's default action - Deny for an allow list (recommended) or Allow for a deny list"],
        [("Match", "pink"), "Request host, wildcards such as *.contoso.com (ruleType Fqdn)"],
        [("Actions", "pink"), "Allow, Deny, Transform (allow and Set, Insert or Remove headers), Rewrite (redirect to another destination)"],
        [("Mode", "pink"), "Audit logs would-denies only; Enforced blocks. Transform and Rewrite apply in both modes"],
        [("Limits", "pink"), "Up to 480 rules per policy (support can raise it); fail-closed if the policy can't be evaluated; foundational platform domains are auto-allowed"],
    ], w=hw, theme="pink", size=14, head_size=15, title="Egress policy in one table", title_size=22).place(cv, x0, y)
    yy = link_lines(cv, x0, rules.bottom + 8, [("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))])
    ca = Card(hw, "CA bundle: what the runtime injects", [
        "To inspect HTTPS, the proxy's CA is added to the sandbox trust bundle via SSL_CERT_FILE, REQUESTS_CA_BUNDLE, GRPC_DEFAULT_SSL_ROOTS_FILE_PATH and NODE_EXTRA_CA_CERTS",
        "The CA differs across hosted-agent clusters and regions and rotates about every 30 days (as of 2026-11-03)",
        "Don't pin, copy or persist it; long-running processes may need to reload TLS config",
    ], theme="pink", badge="preview", src=[("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))])
    ca.place(cv, x0 + hw + 50, y)
    ops = Card(hw, "Operating notes", [
        "Hosted agents only - not prompt agents or model deployments; API version 2026-05-15-preview on the RAI policy",
        "Complements Azure Firewall; it doesn't delegate to your firewall and isn't enforced through Azure Policy",
        "Running sandboxes don't reload policy changes: deploy a new version, then start or resume a session",
        "Start in Audit with a Deny default, review the decisions, then switch to Enforced",
    ], theme="pink", badge="preview", src=[("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))])
    ops.place(cv, x0, yy + 24)
    pats = Card(hw, "Common patterns", [
        "Restrict a coding agent to approved package and source-control hosts; deny everything else",
        "Limit an integration agent to the API hosts of the SaaS services it uses",
        "Transform adds a workload or correlation header (never a secret in a static value); Rewrite redirects a matched host to an approved gateway - test rewrites outside production",
        "Package managers and SDKs follow redirects and use separate download hosts: the registry host is rarely the only one, so audit a representative workload first",
    ], theme="pink", badge="preview", src=[("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))])
    pats.place(cv, x0 + hw + 50, ca.bottom + 30)
    notyet = Card(hw, "Not available yet", [
        "Secret header values", "Azure service tag and IP address rules", "MCP tool policies",
        "PII and data-loss-prevention inspection", "Custom webhook hooks",
    ], theme="gray", fill="soft", src=[("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))])
    notyet.place(cv, x0 + hw + 50, pats.bottom + 30)
    adj = nd_card(hw, "Adjacent technology, not documented as the same thing", [
        "Azure Container Apps dynamic sessions are described on Learn as Hyper-V-isolated sandboxes with pre-warmed pools and sub-second start",
        "Foundry's networking page labels hosted-agent Micro VMs 'on Azure Container Apps', but no page says hosted agents are dynamic sessions: treat any such link as inferred",
    ], src=[("Dynamic sessions in Azure Container Apps", LD("azure/container-apps/sessions", base=""))])
    adj.place(cv, x0, ops.bottom + 30)
    return max(adj.bottom, notyet.bottom)


# ---------------------------------------------------------------------------------------------- sources
def sources_block(cv, y):
    learn_items = [
        ("Deep dive into Foundry Agent Service networking", LD("agents/concepts/agents-networking-deep-dive")),
        ("Networking options for Agent Service", LD("agents/concepts/networking-options")),
        ("Set up private networking for Foundry Agent Service", LD("agents/how-to/virtual-networks")),
        ("Configure network isolation for Microsoft Foundry", LD("how-to/configure-private-link")),
        ("Managed virtual network", LD("how-to/managed-virtual-network")),
        ("Access on-premises resources from a managed network", LD("how-to/access-on-premises-resources")),
        ("Add guardrails to a hosted agent (network egress controls, preview)", LD("agents/how-to/add-hosted-agent-guardrails")),
        ("Hosted agent runtime contract", LD("agents/concepts/hosted-agent-contract")),
        ("Foundry Agent Service quotas, limits and regions", LD("agents/concepts/limits-quotas-regions")),
        ("Dynamic sessions in Azure Container Apps (adjacent technology)", LD("azure/container-apps/sessions", base="")),
    ]
    vb_items = [
        ("Ignite 2025 BRK201 (about 0:37): transitive VNET injection", YT + "7faSLQS501E"),
        ("Foundry blog: What's new in hosted agents (2026-06-02)", "https://devblogs.microsoft.com/foundry/hosted-agents-build26/"),
        ("Reactor: Host your agents on Foundry (about 0:40): 'fast micro VM platform'", YT + "8N7q0Ucr3rw"),
    ]
    b1 = src_panel(cv, 0, y, learn_items, MAIN, 2, "Sources and further reading (Microsoft Learn)")
    b2 = src_panel(cv, SIDE_X, y, vb_items, SIDE_W, 1, "Sources: video and blog (not Learn)", theme="yellow", dash="dashed")
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "Networking internals: container injection and private paths",
        "Under the hood - how an Agent Service request physically reaches your VNet, what DNS must answer, and where egress is controlled",
        icon="foundry", w=W)
    y = bottom + 34

    # top band: legend + at a glance
    ag = at_a_glance(SIDE_W)
    lg = legend_panel(cv, 0, y, MAIN)
    ag.place(cv, SIDE_X, y, h=max(ag.h, lg.h))
    y = max(ag.bottom, lg.bottom) + 50

    # 1  three models
    _, hb = section_header(cv, 0, y, "1  Three network models: decide before you create the account", w=W,
                           sub="Three isolation areas: inbound to Foundry, outbound from the Foundry resource (Private Link) and outbound from the agent client (VNet injection). "
                               "Isolation applies at account and project level, to prompt agents, hosted agents and the other resources")
    cards = model_cards(MAIN)
    top = hb + 30
    nb = numbers_grid(cv, SIDE_X, top, SIDE_W)
    ch = max(max(c.h for c in cards), nb - top)
    cx = 0
    for c in cards:
        c.place(cv, cx, top, h=ch)
        cx += c.w + 50
    y = top + ch + 60

    # 2  case 1
    _, hb = section_header(cv, 0, y, "2  Case 1 - BYO virtual network: one request, hop by hop", w=W,
                           sub="Standard agent setup. Blue = hosted-agent path, green = prompt-agent path, red = the agent's own outbound, indigo = tool path, dark grey = front door")
    y0 = hb + 30
    bottom1 = hero_byo(cv, 0, y0)
    bottom2 = hero_side(cv, SIDE_X, y0)
    y = max(bottom1, bottom2) + 60

    # 3  DNS
    y = dns_section(cv, y) + 60

    # 4 + 5  managed VNet | egress proxy, side by side
    x2 = HALF + 60
    _, hb = section_header(cv, 0, y, "4  Case 2 - Managed virtual network: Microsoft runs the network", w=HALF,
                           sub="Created in the Microsoft tenant; no subnet or IPs on your side")
    section_header(cv, x2, y, "5  Case 3 - Hosted-agent egress through the sandbox proxy (preview)", w=HALF,
                   sub="A second, platform-side egress layer inside the Micro VM sandbox")
    y0 = hb + 30
    yb = max(case_managed(cv, 0, y0), case_egress(cv, x2, y0)) + 40
    y = max(managed_below(cv, 0, yb), egress_below(cv, x2, yb)) + 60

    # 6, 7, 8, 9 live in part 2
    n_next = Note(MAIN, "Part 2 continues with the operator's sheet for a BYO VNet: 6 subnet rules and IP economics (sizing ladder), 7 which wire each tool uses "
                        "when the project is isolated, 8 the firewall allow-list by scenario, 9 gotchas and the places where the sources disagree.",
                  kind="key", title="Continue with part 2 (hood-networking-injection-part-2)")
    n_next.place(cv, 0, y)
    sources_block(cv, n_next.bottom + 50)
