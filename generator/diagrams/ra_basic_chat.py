"""Basic Microsoft Foundry chat reference architecture (learning / POC) - redrawn as a topology with numbered flow,
RBAC wiring and the five Well-Architected pillars' deliberate omissions."""
from generator.xd import *
from generator.xd import metrics

META = dict(
    id="ra-basic-chat", title="Basic chat reference architecture (learning / POC)", section="3", order=1,
    description="The basic Foundry chat architecture redrawn: App Service + Easy Auth, a prompt agent with AI Search and web search grounding, numbered flow, RBAC wiring and what each Well-Architected pillar deliberately leaves out.",
    tags=["reference-architecture", "chat", "prompt-agent", "app-service", "well-architected"],
)

W = 2640
AC = "azure/architecture"
BASIC = learn("ai-ml/architecture/basic-microsoft-foundry-chat", base=AC)
BASELINE = learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC)
RED = "#e03131"
VIOLET = "#6741d9"


class StepsCard(Rect2):
    """Card whose rows are round numbered markers + wrapped text (workflow / flow legends)."""

    def __init__(self, w, title, steps, *, theme_name="blue", icon=None, src=(), size=16, title_size=20, pad=16, gap=12,
                 marker_d=30):
        self.th = theme(theme_name)
        self.w, self.title, self.icon, self.src = w, title, icon, list(src)
        self.size, self.title_size, self.pad, self.gap, self.d = size, title_size, pad, gap, marker_d
        self.steps = []
        text_w = (w - 2 * pad - marker_d - 12) * 0.965
        y = pad + max(title_size * metrics.line_ratio(), 36 if icon else 0) + 8
        for st in steps:
            n, text = st[0], st[1]
            th = st[2] if len(st) > 2 else theme_name
            lines = metrics.wrap_text(text, text_w, size)
            hh = max(len(lines) * size * metrics.line_ratio(), marker_d)
            self.steps.append((n, th, lines, y, hh))
            y += hh + gap
        y -= gap
        self.src_lines = []
        if self.src:
            y += 8
            for label, url in self.src:
                ls = metrics.wrap_text(f"Learn: {label}", (w - 2 * pad) * 0.965, 12)
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
                numbered(cv, x + pad + self.d / 2, y + sy + self.d / 2, n, theme=sth, d=self.d, size=17)
                cv.text(x + pad + self.d + 12, y + sy + (self.d - self.size * metrics.line_ratio()) / 2 + 1 if len(lines) == 1 else y + sy,
                        "\n".join(lines), size=self.size, color=INK)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Basic Microsoft Foundry chat",
        "Reference architecture for learning and proof of concept - a one-room cottage: one region, public endpoints, identity is the only wall",
        w=W)
    y = bottom + 34

    # ------------------------------------------------------------------ banner + glance strip
    banner = Note(W, "It is an introductory architecture for learning and proof of concept (POC). It favours simplicity and cost "
                     "efficiency over functionality; every omission is deliberate to minimise setup time and each omission increases "
                     "risk. For production chat use the baseline reference architecture (next canvas).",
                  kind="gotcha", title="This architecture is not for production (as of 2026-11-03)",
                  src=[("Basic Microsoft Foundry chat reference architecture", BASIC)])
    banner.place(cv, 0, y)
    y = banner.bottom + 26

    glance = [
        Box(412, "Runs in one region", sub="no multi-region design", icon="regions", icon_pos="left", theme="gray", h=92),
        Box(412, "App Service Basic tier", sub="1 instance - no zones - no autoscale", icon="app-service", icon_pos="left",
            theme="gray", h=92),
        Box(412, "Prompt agent", sub="declarative, built in the Foundry portal", icon="agent", icon_pos="left", theme="green", h=92),
        Box(412, "Global Standard model", sub="pay-as-you-go, fixed quota", icon="openai", icon_pos="left", theme="blue", h=92),
        Box(412, "AI Search Basic tier", sub="no replicas, no zones", icon="ai-search", icon_pos="left", theme="teal", h=92),
        Box(412, "Public endpoints", sub="no network security, egress not restricted", icon="security", icon_pos="left",
            theme="red", h=92),
    ]
    row(cv, 0, y, glance, gap=33, equalize=True)
    y += 92 + 44

    # ------------------------------------------------------------------ main diagram
    section_header(cv, 0, y, "The architecture - six numbered steps, three role assignments", size=32,
                   sub="Solid arrows = request flow (numbers match the workflow card)  |  dashed red = role assignments (arrow points at the scope)  |  dotted = telemetry")
    FY = y + 96
    AX, AW = 430, 500
    FX, FW = 1130, 640
    TX, TW = 2030, 570
    AY = FY + 180
    PH = 730
    MY = AY + PH + 74
    FH = MY + 222 + 36 - FY
    with cv.panel(0, FY, w=W, h=FH, title="Single region  |  public endpoints  |  identity is the only perimeter", theme="gray",
                  style="dashed", sw=3, title_size=26, pad=24):
        pass

    portal = Box(250, "Portal user", sub="builds and tests agents in the Foundry portal", icon="users", icon_pos="top", theme="gray", h=118)
    portal.place(cv, 44, FY + 62)

    # --- web tier
    with cv.panel(AX, AY, w=AW, h=PH, title="Azure App Service", sub="Basic tier - 1 instance - built-in public IP", theme="gray",
                  style="solid", fill="soft", pad=20, title_size=26, sub_size=16) as asp:
        auth = Box(AW - 40, "Easy Auth", sub="App Service Authentication with Microsoft Entra ID", icon="conditional-access",
                   icon_pos="left", theme="red", h=104)
        auth.place(cv, asp.ix, asp.iy + 6)
        ui = Box(AW - 40, "Chat UI + API code", sub="same instance; *.azurewebsites.net resolves to the built-in public IP; TLS certificate fully managed by Azure",
                 icon="app-service", icon_pos="left", theme="gray", h=150)
        ui.place(cv, asp.ix, auth.bottom + 56)
        maf = Box(AW - 40, "Microsoft Agent Framework", sub="Azure.Identity authenticates with the App Service managed identity",
                  icon="agent", icon_pos="left", theme="green", h=124)
        maf.place(cv, asp.ix, ui.bottom + 56)
        Chip("Basic tier: no availability zones, no autoscale", theme="red", size=14, fill="soft").place(cv, asp.ix, maf.bottom + 28)
    arrow(cv, [(auth.cx, auth.bottom + 4), (auth.cx, ui.y - 4)], color="#868e96", sw=2.5)
    arrow(cv, [(ui.cx, ui.bottom + 4), (ui.cx, maf.y - 4)], color="#868e96", sw=2.5)

    entra = Box(250, "Microsoft Entra ID", sub="signs the user in", icon="entra-connect", icon_pos="top", theme="red", h=124)
    entra.place(cv, 44, auth.cy - 62)
    users = Box(250, "Application user", sub="browser, HTTPS", icon="users", icon_pos="top", theme="gray", h=124)
    users.place(cv, 44, ui.cy - 62)

    # --- Foundry resource > project
    with cv.panel(FX, AY, w=FW, h=PH, title="Microsoft Foundry resource", sub="one resource containing one project", theme="blue",
                  style="solid", fill="soft", pad=20, title_size=26, sub_size=16) as fr:
        with cv.panel(fr.ix, fr.iy + 4, w=FW - 40, title="Foundry project",
                      sub="agents, model deployments and connections; exposes the endpoint clients call",
                      theme="green", style="dashed", fill="none", pad=16, title_size=22, sub_size=15) as pr:
            agent = Box(FW - 72, "Agent Service - prompt agent",
                        sub="system prompt + temperature + top_p + constrained knowledge connections define the behaviour for every request",
                        icon="agent", icon_pos="left", theme="green", h=150)
            agent.place(cv, pr.ix, pr.iy + 4)
            model = Box(FW - 72, "Azure OpenAI model", sub="Foundry Models, Global Standard deployment (fixed quota); DefaultV2 content filter bound at deployment",
                        icon="openai", icon_pos="left", theme="blue", h=130)
            model.place(cv, pr.ix, agent.bottom + 64)
            mi = Chip("Project managed identity", theme="red", icon="managed-identity", size=15)
            mi.place(cv, pr.ix, model.bottom + 14)
        ghost = Box(FW - 40, "Microsoft-hosted agent dependencies",
                    sub="Cosmos DB, Storage and AI Search run for you ('basic' agent setup) - not visible in your subscription",
                    icon="cosmos", icon_pos="left", theme="gray", fill="none", dash="dashed", h=96)
        ghost.place(cv, fr.ix, pr.bottom + 16)

    # --- tools outside the Foundry resource
    search = Box(TW, "Azure AI Search", sub="Basic tier, no replicas - your grounding index (RAG knowledge store)", icon="ai-search",
                 icon_pos="left", theme="teal", h=118)
    search.place(cv, TX, AY + 100)
    web = Box(TW, "Web search tool", sub="up-to-date public knowledge; has its own pricing", icon="globe", icon_pos="left",
              theme="orange", h=118)
    web.place(cv, TX, AY + 290)
    how = Card(TW, "How to read it", [
        "Numbered circles = the workflow steps 1-6",
        "Solid arrows = request flow; dotted violet = telemetry",
        "Dashed red arrows = role assignments, pointing at the scope",
    ], theme="gray", fill="soft", title_size=18, body_size=15)
    how.place(cv, TX, FY + 64)
    egress = Note(TW, "AI Search, Foundry and App Service are reachable from the internet. Egress is not restricted either: an agent can be "
                      "configured to call any public endpoint named in an OpenAPI spec, so exfiltration of private grounding data can't be "
                      "prevented through network controls.",
                  kind="gotcha", title="No network perimeter", src=[("Network security - basic chat", BASIC + "#network-security")])
    egress.place(cv, TX, web.bottom + 44)

    # --- monitoring
    with cv.panel(AX, MY, w=TX + TW - AX, h=222, title="Monitoring", sub="diagnostics on all services; connect Application Insights to the Foundry project",
                  theme="violet", style="dashed", fill="soft", pad=18, title_size=24, sub_size=15) as mon:
        ai = Box(420, "Application Insights", sub="token usage, latency, exceptions, response quality; OpenTelemetry tracing",
                 icon="app-insights", icon_pos="left", theme="violet", h=108)
        ai.place(cv, mon.ix, mon.iy + 6)
        am = Box(420, "Azure Monitor", sub="App Service logs and Foundry RequestResponse logs", icon="monitor", icon_pos="left",
                 theme="violet", h=108)
        am.place(cv, ai.right + 24, mon.iy + 6)
        logs = Note(840, "App Service: AppServiceHTTPLogs, AppServiceConsoleLogs, AppServiceAppLogs, AppServicePlatformLogs. Foundry: RequestResponse. "
                         "Inventory the logs during the POC and remove sources that add no value before production.",
                    kind="info", size=14, title="Log categories captured", title_size=16, src=[("Monitoring - basic chat", BASIC + "#monitoring")])
        logs.place(cv, am.right + 24, mon.iy + 2)
    numbered(cv, AX + 18, MY - 2, 6, theme="violet", d=36, size=20)

    # --- flow arrows
    connect(cv, users, ui, a_side="right", b_side="left", num=1, num_theme="blue", label="HTTPS", label_size=15, label_dx=-72, sw=3)
    connect(cv, auth, entra, a_side="left", b_side="right", num=2, num_theme="red", dash="dashed", color=RED, sw=2.5,
            start_head="arrow", label="sign-in", label_size=15, label_dx=-72)
    connect(cv, maf, agent, a_side="right", b_side="left", ta=0.5, tb=0.5, num=3, num_theme="green", sw=3, route="elbow", bend=0.5,
            label="agent call", label_size=15, label_pos="left")
    a4 = connect(cv, agent, search, a_side="right", b_side="left", ta=0.3, tb=0.72, num=4, num_theme="teal", sw=3, route="elbow",
                 bend=0.62, label_t=0.9)
    connect(cv, agent, web, a_side="right", b_side="left", ta=0.75, tb=0.5, num=4, num_theme="orange", sw=3, route="elbow", bend=0.62,
            label_t=0.9)
    cv.text(FX + FW + 18, agent.y + 0.3 * agent.h - 26, "grounding data", size=15, color=INK)
    connect(cv, agent, model, a_side="bottom", b_side="top", num=5, num_theme="blue", sw=3, label="prompt + grounding + chat context",
            label_size=15)
    arrow(cv, [(AX + AW / 2, AY + PH + 4), (AX + AW / 2, MY - 4)], dash="dotted", color=VIOLET, sw=2.5)
    arrow(cv, [(FX + FW / 2, AY + PH + 4), (FX + FW / 2, MY - 4)], dash="dotted", color=VIOLET, sw=2.5)

    # --- role assignments (dashed red, pointing at the scope)
    gap1 = FX - (AX + AW)
    arrow(cv, [(AX + AW + 6, AY + 74), (FX - 6, AY + 74)], dash="dashed", color=RED, sw=2.5, end_head="arrow")
    c1 = Chip("Foundry User", theme="red", size=14, fill="soft")
    c1.place(cv, AX + AW + (gap1 - c1.w) / 2, AY + 74 - c1.h - 6)
    arrow(cv, [(portal.right + 6, portal.cy), (FX + FW * 0.62, portal.cy), (FX + FW * 0.62, AY - 6)], dash="dashed", color=RED, sw=2.5,
          end_head="arrow")
    c3 = Chip("Foundry User", theme="red", size=14, fill="soft")
    c3.place(cv, FX + FW * 0.62 - c3.w - 24, portal.cy - c3.h - 6)
    arrow(cv, [(FX + FW - 2, search.y + 28), (TX - 6, search.y + 28)], dash="dashed", color=RED, sw=2.5, end_head="arrow")
    c2 = Chip("Search Index Data Reader", theme="red", size=14, fill="soft")
    c2.place(cv, (FX + FW + TX) / 2 - c2.w / 2, search.y + 28 - c2.h - 6)
    who1, who2 = "App Service MI", "project managed identity"
    cv.text(AX + AW + (gap1 - metrics.line_width(who1, 13)) / 2, AY + 74 + 6, who1, size=13, color="#c92a2a")
    cv.text((FX + FW + TX) / 2 - metrics.line_width(who2, 13) / 2, search.y + 28 + 6, who2, size=13, color="#c92a2a")

    y = FY + FH + 54

    # ------------------------------------------------------------------ pillars
    section_header(cv, 0, y, "What the basic architecture leaves out - the five Well-Architected pillars", size=32,
                   sub="Each omission is deliberate to minimise setup time; the 'Before production' lines say how to close it")
    y += 100
    pw = 500
    p_rel = Card(pw, "Reliability", [
        "# Omitted",
        "App Service Basic has no availability-zone support: the instance is lost if the instance, rack or datacenter fails",
        "No autoscale on the chat UI: over-provision while learning",
        "Agent Service dependencies (Cosmos DB, Storage, AI Search) are Microsoft-hosted: you don't control their reliability",
        "AI Search Basic has no availability zones",
        "# Before production",
        "Zone-redundant App Service and autoscale",
        "AI Search Standard or higher in a zone-enabled region, 3+ replicas",
        "Reserved throughput: Data Zone Provisioned (explicit residency) or Global Provisioned",
    ], theme="orange", icon="service-health", src=[("Reliability considerations", BASIC + "#reliability")])
    p_sec = Card(pw, "Security", [
        "# Omitted",
        "No network security: identity is the perimeter; AI Search, Foundry and App Service are reachable from the internet",
        "Egress is not restricted: an agent can call any public endpoint named in an OpenAPI spec, so exfiltration of grounding data can't be stopped by network controls",
        "No Defender for Cloud plans; no Azure Policy",
        "# In place",
        "Guardrails detect and block hate, sexual, self-harm, violence, profanity and jailbreak content; low / medium / high per category; DefaultV2 filter",
        "# Interim option",
        "Network security perimeter (NSP) on the Foundry project: ingress + egress control; replaced by Private Link in the standard private setup",
    ], theme="red", icon="defender", src=[("Security considerations", BASIC + "#security"),
                                          ("Add Foundry to an NSP", learn("how-to/add-foundry-to-network-security-perimeter"))])
    p_cost = Card(pw, "Cost optimization", [
        "# Omitted",
        "Assumes limited model calls: Global Standard pay-as-you-go, not provisioned throughput",
        "Agent Service bills for files uploaded in chat: don't expose upload if you don't need it",
        "Agent Service is no-code: you can't deterministically control which tools run per request - model cost at maximum usage of every connection",
        "Extra knowledge connections, such as the Web Search tool, have their own pricing",
        "No cost governance or containment controls",
        "# Do now",
        "Set Azure budgets and alerts early; adapt the pricing-calculator estimate",
    ], theme="yellow", icon="cost-management", src=[("Cost considerations", BASIC + "#cost-optimization")])
    p_ops = Card(pw, "Operational excellence", [
        "# Monitoring",
        "Diagnostics on all services; inventory the logs in the POC, drop noisy ones before production",
        "Connect Application Insights to the Foundry project (tokens, latency, exceptions, quality); trace with OpenTelemetry",
        "# Model and agent operations",
        "Plan model lifecycle and retirement before promoting",
        "Agents are built in the browser portal (basic only): delete agents you no longer need, and the connection if it was the last user",
        "Evaluate model, prompt and data quality with Foundry evaluators",
    ], theme="violet", icon="monitor", src=[("Operational excellence", BASIC + "#operational-excellence"),
                                            ("Trace agents", learn("observability/how-to/trace-agent-setup"))])
    p_perf = Card(pw, "Performance efficiency", [
        "# Omitted",
        "Production-grade scaling: pick the App Service SKU from POC results",
        "Scale out (instance count); avoid designs that need a tier change to meet routine demand",
        "# Decide",
        "Pay-as-you-go is best-effort allocation and can show noisy-neighbour effects",
        "Decide whether you need provisioned throughput to reserve capacity and get predictable performance",
        "# Also",
        "Design AI workloads with the Well-Architected AI workloads guidance",
    ], theme="blue", icon="metrics", src=[("Performance efficiency", BASIC + "#performance-efficiency"),
                                          ("AI workloads on Azure", learn("well-architected/ai/get-started", base="azure"))])
    r_right, r_bottom = row(cv, 0, y, [p_rel, p_sec, p_cost, p_ops, p_perf], gap=35)
    y = r_bottom + 64

    # ------------------------------------------------------------------ workflow + components
    section_header(cv, 0, y, "Workflow, components and who needs which role", size=32)
    y += 70
    wf = StepsCard(900, "Workflow (numbers match the diagram)", [
        (1, "User sends HTTPS to the App Service default domain on azurewebsites.net (its built-in public IP). TLS is established from the client straight to App Service; Azure fully manages the certificate", "blue"),
        (2, "Easy Auth makes sure the user is authenticated through Microsoft Entra ID", "red"),
        (3, "App code renders the chat UI; the API code in the same instance calls the agent in Agent Service through Microsoft Agent Framework", "green"),
        (4, "Agent Service uses its configured tools to fetch grounding data: an Azure AI Search index and a web search capability. The grounding data is added to the prompt", "teal"),
        (5, "Agent Service calls the Azure OpenAI model deployed in Foundry with the prompt, grounding data and chat context", "blue"),
        (6, "Application Insights logs the original App Service request and the agent interactions", "violet"),
    ], icon="workflow", src=[("Workflow - basic chat", BASIC + "#workflow")])
    wf.place(cv, 0, y)

    comp = Table(
        [("Component", 230), "Configuration in this reference", ("Role", 330)],
        [
            [("Azure App Service", "gray"), "Basic tier, 1 instance, no zones, no autoscale; default domain *.azurewebsites.net -> built-in public IP; Azure-managed TLS certificate; Easy Auth + Entra ID; managed identity",
             "Hosts the chat UI and API code in the same instance"],
            [("Microsoft Agent Framework", "green"), "In the app code; Azure.Identity authenticates with the App Service managed identity",
             "Client SDK that calls the agent"],
            [("Foundry resource + 1 project", "blue"), "Project = container for agents, model deployments and connections; exposes the endpoint clients use",
             "Platform"],
            [("Agent Service prompt agent", "green"), "System prompt + temperature + top_p + constrained knowledge connections define behaviour for all requests; created in the portal",
             "Keeps conversation history, orchestrates tool calls, enforces content safety, integrates identity / network / observability"],
            [("Azure OpenAI model", "blue"), "Foundry Models, Global Standard deployment (fixed quota); DefaultV2 content filter", "Inference as a service"],
            [("Azure AI Search", "teal"), "Basic tier, no replicas; full-text, semantic, vector and hybrid search; reached through a project connection",
             "Your grounding index (RAG knowledge store)"],
            [("Web search tool", "orange"), "Public-web grounding capability of Agent Service; own pricing structure", "Fresh public knowledge"],
            [("Application Insights + Azure Monitor", "violet"), "Diagnostics on all services; optional App Insights connection to the Foundry project", "Monitoring (step 6)"],
            [("Hidden dependencies", "gray"), "Cosmos DB, Storage and AI Search fully hosted by Microsoft ('basic' agent setup); not in your subscription",
             "Chat state and real-time file chunking"],
        ], w=W - 900 - 40, theme="blue", size=14, head_size=15, title="Component inventory", title_size=22)
    comp.place(cv, wf.right + 40, y)
    y = max(wf.bottom, comp.bottom) + 44

    rbac = Table(
        [("Principal", 250), ("Role", 190), ("Scope", 190), ("Why", 380)],
        [
            ["App Service (managed identity)", ("Foundry User", "red"), "Foundry resource", "Chat UI authenticates to Agent Service with its managed identity (Azure.Identity)"],
            ["Foundry project (managed identity)", ("Search Index Data Reader", "red"), "Azure AI Search", "Project authenticates to AI Search through connection definitions"],
            ["Portal user (each individual)", ("Foundry User", "red"), "Foundry resource", "Individuals who use the Foundry portal"],
        ], w=1010, theme="red", size=14, head_size=15, title="Role assignments you must create", title_size=22)
    rbac.place(cv, 0, y)
    ident = Card(760, "Identity guidance", [
        "You are responsible for creating the role assignments for the managed identities",
        "A Foundry resource can hold several projects, each with its own managed identity",
        "Need isolated access to connected data sources? Use separate projects in one resource and don't share connections across them; otherwise use one project",
    ], theme="red", icon="managed-identity", src=[("Role-based access roles", BASIC + "#role-based-access-roles")])
    ident.place(cv, rbac.right + 40, y)
    n_cons = Note(W - rbac.right - 40 - 760 - 40, "For a principal that only calls agents (for example through the Responses API) without creating or editing them, "
                  "the Foundry RBAC page recommends Foundry Agent Consumer (role ID eed3b665-ab3a-47b6-8f48-c9382fb1dad6). "
                  "This architecture page lists Foundry User for the App Service identity.",
                  kind="tip", title="Least privilege for callers", src=[("RBAC for Foundry", learn("concepts/rbac-foundry"))])
    n_cons.place(cv, ident.right + 40, y)
    y = max(rbac.bottom, ident.bottom, n_cons.bottom) + 44

    # ------------------------------------------------------------------ basic vs baseline + gotchas
    t_up = Table(
        [("Concern", 210), "Basic (this canvas)", "Baseline (next canvas)"],
        [
            [("Network", "indigo"), "Public endpoints; identity is the perimeter; egress not restricted",
             "BYO virtual network, private endpoints, public network access disabled, egress forced through Azure Firewall"],
            [("Ingress", "indigo"), "App Service default domain on azurewebsites.net, built-in public IP",
             "Application Gateway + WAF is the only internet-exposed resource; DDoS Protection plan on its public IP"],
            [("Chat UI hosting", "gray"), "App Service Basic, 1 instance, no zones, no autoscale",
             "Zone-redundant App Service following the baseline App Service guidance (Premium plan, 3+ workers)"],
            [("Agent state", "cyan"), "Basic agent setup: Microsoft-hosted Cosmos DB, Storage, AI Search",
             "Standard agent setup: your own Cosmos DB, Storage and AI Search in your subscription"],
            [("Grounding search", "teal"), "AI Search Basic, no replicas", "AI Search Standard or higher in a zone-enabled region, 3+ replicas"],
            [("Model deployment", "blue"), "Global Standard, pay-as-you-go", "Enterprise chat: Data Zone Provisioned + Data Zone Standard with spillover"],
            [("Security services", "red"), "No Defender plans, no Azure Policy",
             "Defender plans (Servers, App Service, Cosmos DB, AI services), Azure Policy, optional Purview"],
            [("Portal access", "gray"), "Over the internet", "Only through a jump box, peered network, ExpressRoute or VPN"],
        ], w=1700, theme="grape", size=14, head_size=15, title="Moving from basic to baseline (as of 2026-11-03)", title_size=22)
    t_up.place(cv, 0, y)
    nw = W - 1700 - 40
    g1 = Note(nw, "The AI Search in the diagram holds your grounding data. It is different from the AI Search that is a hidden dependency "
                  "of Agent Service, which does real-time chunking of files uploaded in a chat session or as part of an agent definition.",
              kind="gotcha", title="Two different AI Search instances", src=[("Reliability considerations", BASIC + "#reliability")])
    g1.place(cv, t_up.right + 40, y)
    g2 = Note(nw, "Agent Service is a no-code solution: you can't deterministically control which tools or knowledge sources each request invokes. "
                  "In cost modeling, assume maximum usage of each connection.",
              kind="warn", title="Non-deterministic tool use", src=[("Cost considerations", BASIC + "#cost-optimization")])
    g2.place(cv, t_up.right + 40, g1.bottom + 22)
    g3 = Note(nw, "Both architectures keep the chat UI on App Service and use a prompt agent in Agent Service. The baseline adds private "
                  "networking, zone redundancy, standard agent setup with your own data stores, and cost and security governance.",
              kind="info", title="Where to go next", src=[("Baseline Foundry chat reference architecture", BASELINE)])
    g3.place(cv, t_up.right + 40, g2.bottom + 22)
    y = max(t_up.bottom, g3.bottom) + 60

    sources(cv, 0, y, [
        ("Basic Microsoft Foundry chat reference architecture", BASIC),
        ("Baseline Microsoft Foundry chat reference architecture", BASELINE),
        ("Reference implementation (GitHub)", "https://github.com/Azure-Samples/microsoft-foundry-basic"),
        ("Role-based access control for Microsoft Foundry", learn("concepts/rbac-foundry")),
        ("Foundry Agent Service overview (agent types)", learn("agents/overview")),
        ("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
        ("Guardrails and content filtering", learn("guardrails/guardrails-overview")),
        ("Add Foundry to a network security perimeter", learn("how-to/add-foundry-to-network-security-perimeter")),
        ("Trace agents (Application Insights, OpenTelemetry)", learn("observability/how-to/trace-agent-setup")),
        ("Well-Architected: AI workloads on Azure", learn("well-architected/ai/get-started", base="azure")),
        ("Pricing calculator estimate for this architecture", "https://azure.com/e/d43fd2e27fdc4766a125818efd56294e"),
    ], w=W, cols=3)
