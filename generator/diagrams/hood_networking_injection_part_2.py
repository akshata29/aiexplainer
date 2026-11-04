"""Under the hood, networking part 2: the operator's sheet for a bring-your-own VNet - subnet rules and IP economics,
which wire each tool uses when the project is isolated, the firewall allow-list, and the places where the documentation
disagrees or is silent.

Evidence convention (same as part 1): solid border = documented on Microsoft Learn, dashed amber = video/blog only,
dotted grey ('?') = not documented or inferred."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-networking-injection-part-2",
    title="Networking internals, part 2: subnet sizing, tool wires, firewall and gotchas",
    section="8", order=6.5,
    description="Operator's sheet for a bring-your-own VNet: subnet rules and IP economics, which wire each tool uses when the project is isolated, "
                "the firewall allow-list by scenario, and where the sources disagree or stay silent.",
    tags=["networking", "subnet sizing", "firewall", "tool support", "gotchas"],
)

W = 3300            # canvas width
MAIN = 2260         # main column
SIDE_X = MAIN + 80
SIDE_W = W - SIDE_X
GREY = "#868e96"

LD = learn
YT = "https://www.youtube.com/watch?v="


# ---------------------------------------------------------------------------------------------- helpers
def vb_card(w, title, body, theme="yellow", **kw):
    """Video / blog-only claim: dashed amber border."""
    return Card(w, f"(video/blog) {title}", body, theme=theme, fill="soft", dash="dashed", **kw)


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


def steps_card(cv, x, y, w, title, steps, theme="yellow", src=()):
    """Card whose rows carry numbered circles; returns the bottom y."""
    th = THEMES[theme]
    pad, d, size = 16, 28, 15
    lr = metrics.line_ratio()
    tw = (w - 2 * pad - d - 12) * 0.965
    ty = pad + 20 * lr + 10
    rows = []
    for n, text in enumerate(steps, 1):
        lines = wrap_text(text, tw, size)
        h = max(len(lines) * size * lr, d)
        rows.append((n, lines, ty, h))
        ty += h + 10
    ty -= 10
    srcs = []
    if src:
        ty += 8
        for label, url in src:
            srcs.append((f"Learn: {label}", url, ty))
            ty += 12 * lr + 2
        ty -= 2
    H = ty + pad
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        cv.text(x + pad, y + pad, title, size=20, color=th.deep)
        for n, lines, ry, rh in rows:
            numbered(cv, x + pad + d / 2, y + ry + d / 2, n, theme=theme, d=d, size=15)
            cv.text(x + pad + d + 12, y + ry + (rh - len(lines) * size * lr) / 2, "\n".join(lines), size=size)
        for txt, url, sy in srcs:
            cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
    cv.register(f"steps:{title}", x, y, w, H)
    return y + H


def evidence_legend(cv, x, y):
    cx = x
    for kind, label in (("doc", "Solid + hatch: documented on Microsoft Learn"),
                        ("vb", "Dashed + soft, tagged (video/blog): only a video or blog says so"),
                        ("nd", "Dotted grey ?: not documented")):
        if kind == "doc":
            cv.rect(cx, y, 64, 34, stroke="#2f9e44", fill="#b2f2bb", style="hachure", sw=2)
        elif kind == "vb":
            cv.rect(cx, y, 64, 34, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, y, 64, 34, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            cv.text(cx + 24, y + 3, "?", size=26, color=GREY)
        t = cv.text(cx + 78, y + 5, label, size=17)
        cx += 78 + t.w + 56
    draw_badge(cv, cx, y + 4, "preview")
    t = cv.text(cx + 82, y + 5, "Preview feature (check Learn before relying on it)", size=17)
    cx += 82 + t.w + 56
    cv.text(cx, y + 5, "Time-sensitive facts carry: as of 2026-11-03", size=17, color="#c92a2a")
    return y + 46


# ---------------------------------------------------------------------------------------------- 6  subnet / IP economics
def subnet_section(cv, y):
    section_header(cv, 0, y, "6  Subnet rules and IP economics (BYO VNet)", w=W)
    y0 = y + 76
    cw = (MAIN - 100) / 3
    c1 = Card(cw, "Delegated subnet rules", [
        "Delegate to Microsoft.App/environments; dedicated to ONE Foundry resource (the VNet can be shared, the subnet can't)",
        "/27 is the supported minimum; /24 is recommended for production with hosted agents",
        "Size can't be changed after assignment; Azure reserves 5 IPs per subnet; subnet name at most 63 UTF-8 bytes",
        "The Foundry resource must be in the same region as the VNet; other resources may be elsewhere",
        "Register providers: KeyVault, CognitiveServices, Storage, MachineLearningServices, Search, Network, App, ContainerService (+ Bing for Bing grounding)",
    ], theme="indigo", icon="subnet", src=[("Set up private networking", LD("agents/how-to/virtual-networks")),
                                           ("Networking options", LD("agents/concepts/networking-options"))])
    c2 = Card(cw, "Address space (as of 2026-11-03)", [
        "RFC 1918: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16; public ranges are unsupported",
        "Avoid overlap with peered VNets and with 169.254.0.0/16, 172.30.0.0/16, 172.31.0.0/16, 192.0.2.0/24, 0.0.0.0/8, 127.0.0.0/8",
        "Don't use 172.17.0.0/16 (Docker bridge)",
        "Peering works (non-overlapping ranges, extra data-transfer cost); if overlap is unavoidable, use a managed VNet",
    ], theme="indigo", icon="vnet", src=[("Set up private networking", LD("agents/how-to/virtual-networks")),
                                         ("Deep dive", LD("agents/concepts/agents-networking-deep-dive"))])
    c3 = Card(cw, "Lifecycle and immutability", [
        "Set when the Foundry account is created; it can't be added to an existing account or changed later",
        "Takes effect when the first hosted agent is created; to change, create new projects or redeploy",
        "Deleting: delete AND purge the Foundry resource before the VNet - the service association link legionservicelink blocks subnet deletion",
        "Private ACR for hosted agents only for projects created after 2026-06-25",
    ], theme="indigo", icon="landing-zone", src=[("Networking options", LD("agents/concepts/networking-options")),
                                                 ("Configure network isolation", LD("how-to/configure-private-link"))])
    r, b = row(cv, 0, y0, [c1, c2, c3], gap=50)
    w1 = Note(cw, "networking-options and virtual-networks list RFC 6598 (CGNAT) 100.64.0.0/10 as supported, excluding 100.100.0.0/17, "
                  "100.100.192.0/19 and 100.100.224.0/19; the networking deep dive says CGNAT is not supported and causes routing failures. "
                  "Plan with RFC 1918 until the pages agree.", kind="warn", title="Docs disagree: CGNAT 100.64.0.0/10",
              src=[("Networking options", LD("agents/concepts/networking-options")), ("Deep dive", LD("agents/concepts/agents-networking-deep-dive"))])
    w3 = Note(cw, "networking-options calls /27 the supported minimum that 'works for production when you run prompt agents, or for smaller hosted-agent "
                  "deployments'; the deep dive says 'Don't use a /27 subnet for production workloads'. Size for your peak, with /24 as the starting point.",
              kind="warn", title="Docs disagree: is /27 fine for production?",
              src=[("Networking options", LD("agents/concepts/networking-options")), ("Deep dive", LD("agents/concepts/agents-networking-deep-dive"))])
    w2 = Note(cw, "Learn's deep-dive diagram labels the hosted hop /invoke; the public agent routes are /responses and /invocations.",
              kind="warn", title="Docs disagree: path label",
              src=[("Deep dive", LD("agents/concepts/agents-networking-deep-dive"))])
    hh = max(w1.h, w2.h, w3.h)
    w1.place(cv, 0, b + 30, h=hh)
    w3.place(cv, cw + 50, b + 30, h=hh)
    w2.place(cv, 2 * (cw + 50), b + 30, h=hh)

    # side: capacity + exhaustion
    cap = Card(SIDE_W, "Capacity and exhaustion (as of 2026-11-03)", [
        "About 250 projects at low traffic; as few as about 25 under heavy traffic - IP-bound; IP exhaustion fails new project provisioning",
        "Upgrades run old and new infrastructure in parallel, so plan below 80% utilisation",
        "Signals: Data Proxy HTTP 5xx; hosted session create or resume HTTP 429 subnet_exhausted",
        "The portal doesn't show delegated-subnet IP utilisation, and the platform doesn't warn you proactively",
        "Default mapping is 1 IP : 1 session; Azure support can raise it to 1:10",
    ], theme="yellow", icon="quotas", src=[("Deep dive", LD("agents/concepts/agents-networking-deep-dive")),
                                           ("Quotas and limits", LD("agents/concepts/limits-quotas-regions"))])
    cap.place(cv, SIDE_X, y0, h=b - y0)

    # sizing ladder (table + bars drawn together)
    ty = max(w1.bottom, w2.bottom) + 50
    cv.text(0, ty, "Subnet size vs concurrent hosted sessions (default 1:1 mapping, as of 2026-11-03)", size=22, color="#e67700")
    sb = steps_card(cv, SIDE_X, ty, SIDE_W, "Plan capacity in this order", [
        "Estimate peak concurrent hosted sessions across all projects in the account, for the region",
        "Check the region's default concurrent session quota",
        "Size the subnet so usable IPs meet or exceed that target, keeping the planned peak below 80% of usable IPs",
        "If the target exceeds the regional default, request a limit increase (subscription, region, expected concurrency)",
        "If you need more sessions than the usable IPs allow and the subnet can't grow, ask for a higher IP-to-session mapping in the same support request",
    ], theme="yellow", src=[("Deep dive: subnet sizing and IP allocation", LD("agents/concepts/agents-networking-deep-dive"))])
    Note(SIDE_W, "A session is hosted-agent compute plus persisted file state, not conversation history, so session capacity doesn't cap how many "
                 "conversations your application can keep.", kind="tip", title="Sessions are not conversations",
         src=[("Deep dive", LD("agents/concepts/agents-networking-deep-dive"))]).place(cv, SIDE_X, sb + 30)
    ty += 40
    sizes = [("/27", "32", "~27", 20), ("/26", "64", "~59", 50), ("/25", "128", "~123", 100), ("/24", "256", "~251", 250),
             ("/23", "512", "~507", 500), ("/22", "1,024", "~1,019", 1000), ("/21", "2,048", "~2,043", 2000)]
    x_lab, x_tot, x_use, x_bar = 0, 150, 330, 520
    scale = 1500 / 2100.0
    cv.text(x_lab, ty, "Subnet", size=16, color="#495057")
    cv.text(x_tot, ty, "Total IPs", size=16, color="#495057")
    cv.text(x_use, ty, "Usable IPs", size=16, color="#495057")
    cv.text(x_bar, ty, "Approximate concurrent sessions: planning share (80%) and headroom (20%)", size=16, color="#495057")
    cy = ty + 34
    for name, tot, use, sess in sizes:
        cv.text(x_lab, cy + 6, name, size=20, color="#364fc7")
        cv.text(x_tot, cy + 8, tot, size=16)
        cv.text(x_use, cy + 8, use, size=16)
        bw = sess * scale
        cv.rect(x_bar, cy, bw * 0.8, 34, stroke="#2f9e44", fill="#b2f2bb", style="solid", sw=2, rough=0, round_=False)
        cv.rect(x_bar + bw * 0.8, cy, bw * 0.2, 34, stroke="#f08c00", fill="#ffec99", style="hachure", sw=2, rough=0, round_=False)
        cv.text(x_bar + bw + 14, cy + 6, f"~{sess:,}", size=17)
        cy += 50
    for q, lab in ((1000, "default regional session quota 1,000"), (2000, "2,000 in seven regions")):
        qx = x_bar + q * scale
        cv.line((qx, ty + 30), (qx, cy + 4), stroke="#e03131", sw=2)
        cv.text(qx + 8, cy + 6, lab, size=14, color="#c92a2a")
    cv.text(0, cy + 40, "Green = 80% of the approximate sessions, the share to plan for; orange = the 20% headroom for upgrades, rollouts and scale events. A subnet larger than /22 adds IP headroom "
                        "but not concurrency while your regional quota is 1,000 - raise the quota separately.", size=15, color="#495057")
    link_lines(cv, 0, cy + 90, [("Deep dive: subnet size and concurrent sessions", LD("agents/concepts/agents-networking-deep-dive")),
                                ("Quotas and limits", LD("agents/concepts/limits-quotas-regions"))])
    return cy + 150


# ---------------------------------------------------------------------------------------------- 7  tools
def tools_section(cv, y):
    section_header(cv, 0, y, "7  Which wire does each tool use when the project is network-isolated?", w=W)
    y0 = y + 76
    lanes = [
        ("Through your VNet subnet", "indigo", "subnet", ["MCP tool (private MCP)", "OpenAPI tool", "Agent-to-Agent (A2A)", "Azure Functions"],
         "Reaches whatever the delegated subnet can reach, subject to your network security rules. Foundry IQ (preview) is listed as supported 'via MCP'; Learn doesn't break that path down further"),
        ("Through a private endpoint", "teal", "private-endpoint", ["Azure AI Search", "File search"],
         "Azure Blob files with File Search aren't supported; recreate vector stores after enabling the VNet unless you bring your own resources"),
        ("Microsoft backbone network", "blue", "vwan", ["Code Interpreter", "Function calling"],
         "No extra networking. In a BYO VNet Code Interpreter works only without file upload or download (workaround: SDK-created container plus container_id). Function calling runs in your app - check what actually crosses your network."),
        ("Public endpoints", "orange", "public-ip", ["Bing grounding", "Web search", "SharePoint grounding"],
         "Work in isolated setups but cross the public internet; block them with Azure Policy if that isn't acceptable"),
        ("Partial or not supported", "gray", None, ["Fabric IQ (partial, by item type)", "Fabric data agent", "Work IQ", "Logic Apps", "Browser automation",
                                                    "Computer use", "Image generation", "Workflow agents: no outbound injection",
                                                    "AI Gateway (APIM) made in the portal is public"],
         "Fabric data agent needs public access; Logic Apps, Browser automation, Computer use and Image generation are under development; Work IQ isn't supported in network-isolated projects; Workflow agents and AI Gateway are only partly supported"),
    ]
    lw = MAIN - 380
    cy = y0
    for title, th_name, ic, chips, note in lanes:
        th = THEMES[th_name]
        flow = ChipFlow(chips, lw - 20, theme=th_name, size=15, fill="soft")
        nl = wrap_text(note, lw - 20, 14) if note else []
        h = max(86, 20 + flow.h + (len(nl) * 14 * 1.25 + 12 if nl else 0) + 16)
        cv.rect(0, cy, MAIN, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
        tx = 20
        if ic:
            place_icon(cv, ic, 18, cy + 16, 36)
            tx = 66
        cv.text(tx, cy + 20, "\n".join(wrap_text(title, 360 - tx, 20)), size=20, color=th.deep)
        flow.place(cv, 380, cy + 14)
        if nl:
            cv.text(380, cy + 14 + flow.h + 8, "\n".join(nl), size=14, color="#495057")
        cy += h + 16
    link_lines(cv, 0, cy, [("Agent tools with network isolation", LD("how-to/configure-private-link#agent-tools-with-network-isolation")),
                           ("Network isolation for a toolbox", LD("agents/how-to/tools/toolbox-network-isolation"))])
    cy += 60

    # side: capability host + toolbox + scope of the matrix
    n1 = Note(SIDE_W, "Before calling tool endpoints outside Foundry through your VNet, provision a capability host at the PROJECT level. "
                      "An account-level capability host alone fails with network errors such as 'name or host unknown'.",
              kind="gotcha", title="Project-level capability host is mandatory",
              src=[("Capability hosts", LD("agents/concepts/capability-hosts")), ("Configure network isolation", LD("how-to/configure-private-link"))])
    n1.place(cv, SIDE_X, y0)
    n2 = Note(SIDE_W, "A toolbox is a logical container and deploys no networking of its own. Agents reach its MCP endpoint through the project's private "
                      "endpoint, and each downstream tool then follows its own wire.", kind="info", title="Toolbox networking",
              src=[("Network isolation for a toolbox", LD("agents/how-to/tools/toolbox-network-isolation"))])
    n2.place(cv, SIDE_X, n1.bottom + 24)
    n3 = Note(SIDE_W, "The matrix applies to network-isolated deployments created with the Standard template 15-private-network-standard-agent-setup "
                      "or the Basic template 11-private-network-basic-vnet (as of 2026-11-03).", kind="info", title="Scope of the matrix",
              src=[("Configure network isolation", LD("how-to/configure-private-link#agent-tools-with-network-isolation"))])
    n3.place(cv, SIDE_X, n2.bottom + 24)
    return max(cy, n3.bottom)


# ---------------------------------------------------------------------------------------------- 8  firewall allow-list
def firewall_section(cv, y):
    _, hb = section_header(cv, 0, y, "8  Firewall allow-list when you control egress (BYO VNet)", w=W,
                           sub="You run the firewall, so you allow-list what the platform needs. With a managed VNet, Microsoft's managed Azure Firewall does this job")
    y0 = hb + 30
    rows = [
        [("Agents", "red"), "*.identity.azure.net\nlogin.microsoftonline.com\n*.login.microsoftonline.com\n*.login.microsoft.com\nor the AzureActiveDirectory service tag",
         "Required for the Azure Container Apps delegation that Agent Service uses"],
        [("Agent subnet behind Azure Firewall", "red"), "control-{region}.identity.azure.net\n{region}.login.microsoft.com\nlogin.microsoftonline.com\n"
         "+ the Managed Identity FQDNs from the Azure Container Apps firewall article, or the AzureActiveDirectory tag",
         "Replace {region} with the agent's region. NSGs on the agent subnet need matching outbound rules (AzureActiveDirectory tag). Blocked dependencies break provisioning and runtime"],
        [("Source-code deploy of a hosted agent", "orange"), "mcr.microsoft.com\n*.login.microsoft.com", "Needed during provisioning of a code-based hosted agent in a private VNet"],
        [("Evaluations and traces (Application Insights)", "violet"), "settings.sdk.monitor.azure.com\n*.livediagnostics.monitor.azure.com\n*.in.applicationinsights.azure.com\nAzureMachineLearning service tag",
         "Alternative to the tag: *.dataproxy.{region}.api.azureml.ms and {region}.api.azureml.ms for the region where the evaluation runs"],
        [("Hosted agents to Agent 365", "violet"), "agent365.svc.cloud.microsoft (TCP 443)\nor the AzureFrontDoor.Frontend service tag",
         "Optional. If blocked, agents keep working but traces aren't exported to Agent 365 and the firewall logs repeated denies. Set a365LoggingEnabled to false (new sessions only)"],
        [("Fine-tuning with curated datasets", "gray"), "raw.githubusercontent.com", "Only when you pick a curated sample dataset in the portal; your own training data doesn't use it"],
        [("Agent calls to non-Azure APIs", "gray"), "outbound HTTPS to those destinations", "Allow it in the firewall, or deploy a NAT gateway for controlled egress"],
    ]
    t = Table([("Scenario", 250), ("FQDNs and service tags to allow", 760), "Why, and what happens if you block it"], rows, w=MAIN, theme="red",
              size=14, head_size=15, title="Allow-list by scenario (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, y0)
    ly = link_lines(cv, 0, t.bottom + 8, [("Firewall allowlisting", LD("how-to/configure-private-link")),
                                          ("Agent subnet egress firewall allow list", LD("agents/how-to/virtual-networks")),
                                          ("Firewall requirements for source-code deploys", LD("agents/how-to/deploy-hosted-agent-code"))])
    n1 = Note(MAIN, "Service tags cover the IP ranges of a whole Azure service and can't be scoped to a tenant, subscription or resource "
                    "(AzureFrontDoor.Frontend covers all of Front Door). When you need a narrower rule, allow the FQDN instead.",
              kind="tip", title="Tag or FQDN?", src=[("Firewall allowlisting", LD("how-to/configure-private-link"))])
    n1.place(cv, 0, ly + 20)

    layers = Table([("Egress control layer", 210), ("Who and where", 330), "Notes"], [
        [("Egress proxy in the sandbox (preview)", "pink"), "Foundry platform, inside the hosted agent's Micro VM sandbox",
         "Hosted agents only; ordered host rules; complements your firewall, isn't enforced through Azure Policy"],
        [("NSG on the agent subnet", "indigo"), "You, BYO VNet", "Mirror the firewall rules, including the AzureActiveDirectory tag"],
        [("Azure Firewall or other NVA", "indigo"), "You, often a shared hub VNet peered to the Foundry spoke",
         "No TLS inspection on the agent-subnet path; NAT gateway for controlled egress to non-Azure APIs"],
        [("Managed Azure Firewall", "violet"), "Microsoft, managed VNet",
         "Created at the first FQDN rule, FQDN rules on ports 80 and 443; you can't bring your own"],
    ], w=SIDE_W, theme="pink", size=14, head_size=15, title="Which layer controls egress?", title_size=22)
    layers.place(cv, SIDE_X, y0)
    n2 = Note(SIDE_W, "Learn's hub-and-spoke diagram: a hub VNet holds a shared firewall and is peered to a spoke VNet for Foundry networking. "
                      "A standalone project without a hub looks different - adapt the firewall and peering to your own design.",
              kind="info", title="Common topology", src=[("Hub-and-spoke and firewall configuration", LD("how-to/configure-private-link"))])
    n2.place(cv, SIDE_X, layers.bottom + 30)
    return max(n1.bottom, n2.bottom)


# ---------------------------------------------------------------------------------------------- 9  gotchas
def gotchas_section(cv, y):
    _, hb = section_header(cv, 0, y, "9  Gotchas, and where the sources disagree", w=W)
    y0 = hb + 30
    cw = (W - 3 * 40) / 4
    r1 = [
        Note(cw, "BYO VNet injection and the managed VNet are both fixed at account creation. Neither can be added later, there is no upgrade path "
                 "from BYO to managed, a delegated subnet can't be swapped, and capability hosts can't be updated (delete and recreate).",
             kind="gotcha", title="Decide before you create",
             src=[("Networking options", LD("agents/concepts/networking-options")), ("Managed virtual network", LD("how-to/managed-virtual-network"))]),
        Note(cw, "Learn tells you to verify that no TLS inspection happens in the firewall on the agent subnet, because it could add a self-signed certificate. "
                 "The egress proxy's CA, injected inside the sandbox (preview), is a different thing: the platform manages it and rotates it about every 30 days.",
             kind="warn", title="No TLS inspection on the agent subnet",
             src=[("Set up private networking", LD("agents/how-to/virtual-networks")), ("Add guardrails to a hosted agent", LD("agents/how-to/add-hosted-agent-guardrails"))]),
        Note(cw, "Bing grounding, Web search and SharePoint grounding keep working in an isolated project - over the public internet. "
                 "If your organization needs all traffic to stay private, block them with Azure Policy.",
             kind="warn", title="Public-endpoint tools",
             src=[("Agent tools with network isolation", LD("how-to/configure-private-link#agent-tools-with-network-isolation"))]),
        Note(cw, "Learn lists Function calling under the Microsoft backbone, but the function itself runs in your application (client-side). "
                 "Check what actually crosses your network before you call it private.",
             kind="warn", title="Docs disagree: function calling as a network path",
             src=[("Agent tools with network isolation", LD("how-to/configure-private-link#agent-tools-with-network-isolation"))]),
    ]
    r, b1 = row(cv, 0, y0, r1, gap=40)
    r2 = [
        Note(cw, "When public network access is disabled, Teams and Microsoft 365 can't use the project's private endpoint. The REST path sets enable_m365_public_endpoint "
                 "to true: a source-IP-filtered public route to the Activity Protocol only; Responses, Invocations, A2A and MCP stay private. Bot Service authorization still applies.",
             kind="info", title="Teams and Microsoft 365 with a private Foundry",
             src=[("Publish agents by using the REST API", LD("agents/how-to/publish-copilot-virtual-network"))]),
        Note(cw, "Learn's networking diagram labels the Micro VMs and Data Proxy 'on Azure Container Apps' and the subnet delegation is Microsoft.App/environments. "
                 "A Reactor presenter (2026-04-27) called the new hosted-agent platform a different 'fast micro VM platform'. Unresolved; the hypervisor isn't named.",
             kind="warn", title="Docs and video disagree: what is under the Micro VM?", dash="dashed"),
        Note(cw, "The network isolation page still says 'hosted (preview) agents' in one place, while blogs announced hosted agents GA on 2026-07-09 "
                 "(video/blog, as of 2026-11-03). Network egress controls remain preview, so read each hosted-agent page's own banner.",
             kind="warn", title="Docs disagree: is hosted-agent networking GA?",
             src=[("Configure network isolation", LD("how-to/configure-private-link"))]),
        Note(cw, "Projects created after 2026-06-25 can use a private (network-secured) Azure Container Registry for hosted agents. Older projects need the registry "
                 "reachable on its public endpoint. Existing projects aren't affected.",
             kind="info", title="Private ACR date",
             src=[("Configure network isolation", LD("how-to/configure-private-link"))]),
    ]
    r, b2 = row(cv, 0, b1 + 40, r2, gap=40)
    return b2


# ---------------------------------------------------------------------------------------------- sources
def sources_block(cv, y):
    learn_items = [
        ("Deep dive into Foundry Agent Service networking", LD("agents/concepts/agents-networking-deep-dive")),
        ("Networking options for Agent Service", LD("agents/concepts/networking-options")),
        ("Set up private networking for Foundry Agent Service", LD("agents/how-to/virtual-networks")),
        ("Configure network isolation for Microsoft Foundry", LD("how-to/configure-private-link")),
        ("Managed virtual network", LD("how-to/managed-virtual-network")),
        ("Network isolation for a toolbox", LD("agents/how-to/tools/toolbox-network-isolation")),
        ("Capability hosts", LD("agents/concepts/capability-hosts")),
        ("Foundry Agent Service quotas, limits and regions", LD("agents/concepts/limits-quotas-regions")),
        ("Deploy a hosted agent from source code", LD("agents/how-to/deploy-hosted-agent-code")),
        ("Add guardrails to a hosted agent (network egress controls, preview)", LD("agents/how-to/add-hosted-agent-guardrails")),
        ("Publish agents to Copilot and Teams by using the REST API", LD("agents/how-to/publish-copilot-virtual-network")),
    ]
    vb_items = [
        ("Reactor: Host your agents on Foundry (about 0:40): 'fast micro VM platform'", YT + "8N7q0Ucr3rw"),
        ("Tech Community: Foundry agents and custom engine agents through the corporate firewall",
         "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-agents-and-custom-engine-agents-through-the-corporate-firewall/4502218"),
        ("Azure blog: GPT-5.6 now available in Microsoft Foundry (2026-07-09, hosted agents GA announcement)",
         "https://azure.microsoft.com/en-us/blog/gpt-5-6-now-available-in-microsoft-foundry/"),
    ]
    b1 = src_panel(cv, 0, y, learn_items, MAIN, 2, "Sources and further reading (Microsoft Learn)")
    b2 = src_panel(cv, SIDE_X, y, vb_items, SIDE_W, 1, "Sources: video and blog (not Learn)", theme="yellow", dash="dashed")
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "Networking internals, part 2: subnet sizing, tool wires, firewall and gotchas",
        "Under the hood - the operator's sheet for a bring-your-own VNet. Part 1 follows the packets; this part says how many IPs they burn, which wire each tool uses, what the firewall must allow",
        icon="foundry", w=W)
    y = bottom + 34
    tiles = [
        ("/24", "recommended agent subnet for production; /27 is the supported minimum and the size is fixed once assigned", "indigo", "doc"),
        ("1 : 1", "default usable IPs to concurrent hosted sessions; Azure support can raise it to 1:10", "indigo", "doc"),
        ("80 %", "plan peak sessions below this share of usable IPs: upgrades run old and new infrastructure together", "yellow", "doc"),
        ("250 | 25", "projects per account at low traffic | under heavy traffic; IP-bound", "yellow", "doc"),
        ("1,000 | 2,000", "regional concurrent hosted sessions per subscription: default | seven regions", "yellow", "doc"),
        ("429", "hosted session create or resume error subnet_exhausted when the subnet runs dry", "red", "doc"),
        ("5", "IPs Azure reserves in every subnet - hence about 27 usable in a /27", "indigo", "doc"),
        ("? IPs", "whether an idle or stopped session releases its delegated-subnet IP is not stated", "gray", "nd"),
    ]
    tw = (W - 7 * 24) / 8
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + 24), y, tw, 150, big, cap, th, kind)
    y = evidence_legend(cv, 0, y + 150 + 24)
    y = subnet_section(cv, y + 50) + 40
    y = tools_section(cv, y) + 60
    y = firewall_section(cv, y) + 60
    y = gotchas_section(cv, y) + 60
    sources_block(cv, y)
