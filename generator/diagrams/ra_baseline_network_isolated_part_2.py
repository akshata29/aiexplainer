"""Baseline Microsoft Foundry chat, network-isolated - part 2: the design decisions, what works behind the VNet,
reliability and disaster recovery, the Well-Architected guidance and the production gotchas."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme
from generator.xd.blocks import draw_mark

META = dict(
    id="ra-baseline-network-isolated-part-2",
    title="Baseline chat: decisions, operations and gotchas",
    section="3", group="Reference architectures", order=2.5,
    description="Part 2 of the network-isolated baseline: design decisions and trade-offs, which tools work behind the VNet, zone redundancy and "
                "disaster recovery, Well-Architected guidance and the production gotchas (WAF tuning, portal access, conversation isolation).",
    tags=["reference-architecture", "well-architected", "disaster-recovery", "design-decisions", "tools", "gotchas"],
)

W = 3200
AC = "azure/architecture"
ASOF = "as of 2026-11-03"
GRN, RED, GRY, INKC, IND = "#2f9e44", "#e03131", "#868e96", "#1e1e1e", "#3b5bdb"

# ----------------------------------------------------------------------------------------------------- citations
S_BASE = ("Baseline Microsoft Foundry chat reference architecture",
          learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC))
S_SAS = ("Standard agent setup", learn("agents/concepts/standard-agent-setup"))
S_OWN = ("Use your own resources with Agent Service", learn("agents/how-to/use-your-own-resources"))
S_VNET = ("Network-secured agent setup (BYO VNet)", learn("agents/how-to/virtual-networks"))
S_PRIV = ("Configure private link for Foundry", learn("how-to/configure-private-link"))
S_NETOPT = ("Agent networking options", learn("agents/concepts/networking-options"))
S_ARCH = ("Microsoft Foundry architecture", learn("concepts/architecture"))
S_RBAC = ("Role-based access control for Foundry", learn("concepts/rbac-foundry"))
S_PATTERNS = ("AI agent design patterns (Architecture Center)", learn("ai-ml/guide/ai-agent-design-patterns", base=AC))
S_LIMITS = ("Limits, quotas and regions: tool support by region and model", learn("agents/concepts/limits-quotas-regions"))
S_REPO = ("Reference implementation: microsoft-foundry-baseline (GitHub)", "https://github.com/Azure-Samples/microsoft-foundry-baseline")
S_BLOG = ("Foundry agents and custom engine agents through the corporate firewall (blog)",
          "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-agents-and-custom-engine-agents-through-the-corporate-firewall/4502218")
S_GW = ("Generative AI gateway for multiple models (Architecture Center)", learn("ai-ml/guide/generative-ai-gateway-multiple-models", base=AC))


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


# ----------------------------------------------------------------------------------------------------- 0 title + glance
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Baseline Microsoft Foundry chat - decisions, operations and gotchas",
        "Part 2 of the network-isolated baseline: the forks in the road, what still works behind the VNet, zones and recovery, and the production traps "
        f"- {ASOF}. Part 1 has the topology, private endpoints, identity wiring and network rules", w=W)
    y = bottom + 34
    gap = 38
    gw = (W - 4 * gap) / 5
    items = [
        ("Prompt agent by default", "hosted agent when you need control, code audit or per-agent identity", "agent", "green"),
        ("Not everything stays private", "Bing, web search and SharePoint grounding use public endpoints; Fabric data agent and Logic Apps are unsupported", "globe", "red"),
        ("Zones, not regions", "single region: zone-redundant dependencies, and no built-in disaster recovery for Agent Service", "regions", "orange"),
        ("Three line items dominate cost", "Cosmos DB, AI Search and DDoS Protection", "cost-management", "yellow"),
        ("Authorization on chats is yours", "Agent Service doesn't enforce per-user authorization on conversations", "conditional-access", "red"),
    ]
    boxes = [Box(gw, a, sub=b, icon=ic, icon_pos="left", theme=t, h=128, size=18, sub_size=13) for a, b, ic, t in items]
    row(cv, 0, y, boxes, gap=gap)
    return y + 128 + 56


# ----------------------------------------------------------------------------------------------------- 1 decisions
def _decisions(cv, y):
    y = chapter(cv, y, "1  Design decisions and trade-offs the article documents",
                f"Each row is a fork in the road; the right-hand column is what the Architecture Center page recommends ({ASOF})")
    rows = [
        [("Foundry topology", "blue"), "Dedicated Foundry resource per production workload (fully isolated workload topology; CAF: one AI platform instance per production workload)",
         "Shared resource with several projects", "Accept the segmentation overhead for independent access, quota and cost"],
        [("Chat orchestration", "green"), "Prompt agent: codeless, nondeterministic, platform-managed",
         "Hosted agent: your container on Foundry-managed compute (Responses protocol = platform keeps history and session lifecycle; Invocations protocol = your code keeps session state); or self-hosted orchestration, where you run everything",
         "Prompt agent unless one of the triggers on the right applies"],
        [("App tier", "gray"), "App Service (preferred for simplicity)", "Container Apps or AKS", "Choose by how much platform you want to run"],
        [("Grounding store", "teal"), "Azure AI Search (vector search is typical, not required)", "Cosmos DB, SQL or another OLTP store", "Pick the store your data already lives in"],
        [("Chat history", "cyan"), "Service-managed conversations in your Cosmos DB", "Client-managed: zero data retention, custom context control and compaction, several UX channels",
         "Client-managed shifts persistence, governance and backup and restore to you"],
        [("Agents", "green"), "Predefined, as code: reproducible", "Dynamic, per user", "Dynamic agents add a lifecycle burden"],
        [("Single vs multi-agent", "green"), "Single agent", "Multi-agent: several expertise areas, different permission levels, different models for cost or latency, or sequential and parallel business steps",
         "Multi-agent costs coordination and latency; private MCP needs the standard setup and a dedicated subnet; MCP and A2A connect external tools and agents"],
        [("Outbound isolation", "indigo"), "BYO VNet (part 1): you own ranges, peering, firewall and UDRs", "Managed virtual network: Microsoft-managed, billed managed Azure Firewall, no BYO firewall",
         "Compare in the canvas 'Network isolation'"],
    ]
    t = Table([("Decision", 190), ("Option A", 440), ("Option B", 560), ("Documented guidance", 0)], rows, w=1990, theme="grape", size=14, head_size=15,
              title="Decisions, options and guidance", title_size=22)
    t.place(cv, 0, y)

    # ---- fan-in: when a prompt agent isn't enough
    fx = t.right + 40
    fw = W - fx
    cv.text(fx, y, "When do you outgrow a prompt agent?", size=22, color=get_theme("green").deep)
    cv.text(fx, y + 30, "Choose a hosted agent when any of these applies", size=14, color=MUTED)
    conds = ["Models or tools Agent Service doesn't support", "Deterministic control, human-in-the-loop or multi-agent", "Reuse of existing code",
             "Code audit or certification", "Per-agent identity and endpoint isolation", "CPU and memory tuning per session",
             "Extended memory in a separate database"]
    cw_ = fw - 360 - 70
    cy0 = y + 70
    chips = []
    for i, c in enumerate(conds):
        chips.append(Chip(c, theme="green", size=15, fill="solid", w=cw_).place(cv, fx, cy0 + i * 52))
    top, bot = chips[0].y, chips[-1].bottom
    brace(cv, fx + cw_ + 12, top, bot, side="right", depth=22, color=GRN, sw=2.5)
    hb = Box(300, "Hosted agent", sub="your container on Foundry-managed compute; own Entra agent identity and endpoint path", icon="container-apps",
             icon_pos="top", theme="green", h=170, size=20, sub_size=13, icon_size=40).place(cv, fx + fw - 300, (top + bot) / 2 - 85)
    arrow(cv, [(fx + cw_ + 40, (top + bot) / 2), (hb.x - 6, (top + bot) / 2)], color=GRN, sw=3)
    pa = Box(fw, "Otherwise: the prompt agent", sub="codeless, platform-managed and nondeterministic - the baseline's default", icon="agent",
             icon_pos="left", theme="green", fill="soft", dash="dashed", h=76, size=18, sub_size=13).place(cv, fx, bot + 22)
    n1 = Note(fw, "Agent Service supports only a subset of the catalog (filter ai.azure.com catalog capabilities=agentsv2, or az cognitiveservices model list "
                  "--query \"[?model.capabilities.agentsV2=='true']\"). Tool availability depends on model and region, and REST agent creation can accept an unsupported "
                  "model and tool combination and fail only at runtime.", kind="gotcha", title="Model and tool selection gotcha", size=14,
              src=[S_LIMITS, S_BASE])
    n1.place(cv, fx, pa.bottom + 22)
    n2 = Note(t.w, "Multi-agent patterns: sequential, concurrent, group chat, handoff and magentic. Use multi-agent only when one agent can't do the job; "
                   "dedicated resource + standard setup + BYO VNet + prompt agent is the documented default.", kind="tip", title="Defaults and patterns", size=14,
              src=[S_PATTERNS])
    n2.place(cv, 0, t.bottom + 22)
    return max(n1.bottom, n2.bottom) + 56


# ----------------------------------------------------------------------------------------------------- 2 tools behind the VNet
def _tools(cv, y):
    y = chapter(cv, y, "2  What still works behind the VNet - and what leaves it",
                f"Tool support under network isolation by traffic path, as documented for a private Foundry ({ASOF})")
    lanes = [
        ("Through your VNet subnet", "supported", "green", [("MCP (private servers)", "orange"), ("OpenAPI tool", "orange"), ("Azure Functions", "orange"), ("A2A", "pink")], ""),
        ("Through a private endpoint", "supported", "indigo", [("Azure AI Search", "teal"), ("File Search", "teal")],
         "Azure Blob Storage files with File Search are not supported in a BYO setup"),
        ("Microsoft backbone", "supported", "blue", [("Code Interpreter", "orange"), ("Function calling", "orange")],
         "Code Interpreter in a BYO network works only without file upload or download"),
        ("Via MCP", "partial", "cyan", [("Foundry IQ (preview)", "teal"), ("Fabric IQ", "cyan")],
         "Fabric IQ: data agents tenant + workspace private link, ontologies tenant-level, Power BI semantic models public only"),
        ("Public endpoint", "public", "red", [("Bing grounding", "orange"), ("Web search", "orange"), ("SharePoint grounding", "teal")],
         "supported, but traffic leaves over a public endpoint; can be blocked with Azure Policy"),
        ("Not supported", "no", "gray", [("Fabric data agent", "cyan"), ("Logic Apps", "orange"), ("Browser Automation", "orange"), ("Computer Use", "orange"),
                                           ("Image Generation", "orange")],
         "Fabric data agent needs public network access on Fabric; the others are 'under development'"),
    ]
    LH, LG = 108, 14
    n = len(lanes)
    total = n * LH + (n - 1) * LG
    ax, aw = 0, 300
    lx = ax + aw + 90
    lw = 2020
    agent = Box(aw, "Agent Service", sub="tool call from a prompt or hosted agent; the data proxy in your agent subnet carries the VNet-bound ones",
                icon="agent", icon_pos="top", theme="green", h=total, size=22, sub_size=14, icon_size=44).place(cv, ax, y)
    for i, (title, status, th, tools, note) in enumerate(lanes):
        ly = y + i * (LH + LG)
        t_ = get_theme(th)
        zone(cv, lx, ly, lw, LH, theme=th, style="solid", fill="soft", sw=2)
        lab = Box(360, title, theme=th, h=LH - 20, size=19, fill="solid").place(cv, lx + 10, ly + 10)
        mk = {"supported": CHECK, "partial": PARTIAL, "public": PARTIAL, "no": CROSS}[status]
        draw_mark(cv, mk, lx + lw - 34, ly + 30, 28)
        cx = lx + 390
        for tname, tth in tools:
            c = Chip(tname, theme=tth, size=16, fill="solid").place(cv, cx, ly + 12)
            cx += c.w + 14
        if note:
            cv.text(lx + 390, ly + 58, note, size=14, color=MUTED, wrap=lw - 390 - 70)
        arrow(cv, [(agent.right + 6, ly + LH / 2), (lx - 6, ly + LH / 2)], color=t_.stroke, sw=2.5, dash="dashed" if status in ("public", "no") else "solid")
    px = lx + lw + 40
    pw = W - px
    n1 = Note(pw, "Workflow agents: inbound works, outbound VNet injection is not supported. An AI gateway (API Management) created from the Foundry UI is public: "
                  "network-isolate it in the Azure portal. Indexers into a private Search service must set executionEnvironment to Private; indexed knowledge sources and "
                  "auto-generated indexers don't support it.", kind="warn", title="Other limits to know", size=14, src=[S_PRIV, S_VNET])
    n1.place(cv, px, y)
    n2 = Note(pw, "Publishing to Teams or Microsoft 365 works with public network access disabled but needs extra setup and a public, source-IP-filtered Activity route: "
                  "see the canvas 'Microsoft 365, Fabric and event-driven integration'. As of 2026-11-03, hosted agents with a private ACR are supported for projects "
                  "created after June 25 2026; earlier projects need a public ACR.",
              kind="info", title="Teams and Microsoft 365", size=14, src=[S_BLOG])
    n2.place(cv, px, n1.bottom + 18)
    n3 = Note(pw, "Don't read 'supported' as 'private': Bing grounding, web search and SharePoint grounding are supported but use public endpoints.",
              kind="key", title="Supported is not private", size=14)
    n3.place(cv, px, n2.bottom + 18)
    return max(y + total, n3.bottom) + 56


# ----------------------------------------------------------------------------------------------------- 3 reliability + DR
def _resilience(cv, y):
    y = chapter(cv, y, "3  Zone redundancy and disaster recovery: what you control and what has no switch",
                f"Single region only; Agent Service has no built-in disaster recovery ({ASOF})")
    rows = [
        [("Application Gateway + WAF", "indigo"), CHECK, "zone distribution", "-"],
        [("App Service (chat UI)", "gray"), CHECK, "zone-redundant, 3 zones (baseline App Service guidance)", "code ZIP in Storage; redeploy from CI/CD"],
        [("Azure Firewall", "indigo"), CHECK, "deploy across all zones; several public IPs or prefixes against SNAT exhaustion; monitor SNAT and health", "-"],
        [("Model deployment", "blue"), CHECK, "Standard is single-region with no zones: use global or data-zone; enterprise chat: Data Zone Provisioned + Data Zone Standard with spillover",
         "n/a; no round-robin or circuit-breaker in Foundry: build an API Management gateway if you need it"],
        [("Cosmos DB (enterprise_memory)", "cyan"), CHECK, "zone-redundant; consider multi-region", "continuous backup: point-in-time restore within 7 days, into the same account and database"],
        [("Storage (agent files)", "cyan"), CHECK, "ZRS or GZRS", "customer-managed failover if the account is GRS, otherwise Support"],
        [("AI Search (agent dependency)", "teal"), CHECK, "3+ replicas; Standard or higher in a zone-enabled region", "no built-in restore: contact Support; keep a separate source of truth to rebuild the index"],
        [("Foundry portal, data plane, Agent Service", "green"), CROSS, "no direct zone-redundancy controls", "none: no replication, backup or point-in-time restore"],
    ]
    t = Table([("Component", 300), ("You control it", 150), ("Zone redundancy / availability", 640), ("Backup and restore", 0)], rows, w=2060, theme="orange",
              size=14, head_size=15, title="Resilience map of the baseline", title_size=22, align=["left", "center", "left", "left"])
    t.place(cv, 0, y)
    dx = t.right + 40
    dw = W - dx
    dr = Card(dw, "Recovery recipe for Agent Service", [
        "Agents as code, so they can be re-created",
        "Use a user-assigned identity for the project: a re-created project or capability host then reuses the role assignments",
        "Delete locks on the three dependencies; never touch the system-managed collections or indexes directly (use data-plane APIs, for example for right-to-be-forgotten)",
        "Coordinate transactional consistency across the stores: conversation and agent IDs must still line up after a restore",
        "Write the runbook: failover and fail-back",
        "! Single region only: no global ingress, DNS failover, replication, active / passive designation or failover runbooks",
    ], theme="red", icon="recovery-vault", src=[S_BASE, S_ARCH])
    dr.place(cv, dx, y)
    n = Note(t.w, "Multi-region: deploy separate Foundry resources per region and handle synchronisation and routing in your application layer. Isolate the Agent Service "
                  "dependencies: don't share the Cosmos DB, Storage or AI Search accounts with other parts of the workload (blast radius). Co-locate them in the same region "
                  "as Agent Service.", kind="info", title="Blast radius and regions", size=14, src=[S_BASE, S_OWN])
    n.place(cv, 0, t.bottom + 22)
    return max(dr.bottom, n.bottom) + 56


# ----------------------------------------------------------------------------------------------------- 4 pillars
def _pillars(cv, y):
    y = chapter(cv, y, "4  Security, cost, operations and performance - what the baseline documents",
                f"The remaining Well-Architected guidance, condensed ({ASOF})")
    gap = 40
    cw = (W - 3 * gap) / 4
    sec = Card(cw, "Security", [
        "Separate identities per resource and function; Entra ID on connections; secrets in a dedicated Key Vault (API-key connections here: App Insights and the web search tool)",
        "MCP: restrict allowed_tools; require and log approval for write or change tools",
        "One content-filter policy per model deployment, authored as code",
        "Defender plans: Servers, App Service, Cosmos DB, AI services",
        "Purview via the Foundry Control Plane at subscription scope (audit log, DSPM); the Insider Risk 'Risky Agents' template is preview; Purview's interaction-data flow doesn't support network isolation",
        "Policy ideas: disable key / local auth, require PEs and NSGs, customer-managed keys, restrict regions and types",
    ], theme="red", icon="defender", src=[S_BASE])
    cost = Card(cw, "Cost optimization", [
        "Top costs: Cosmos DB, AI Search and DDoS Protection; then chat UI compute and Application Gateway",
        "Agent Service manages Cosmos RU allocation: buy reserved capacity",
        "No file upload? LRS storage and 1 search replica; delete stale agents and conversations",
        "Disable what you don't need (semantic ranker, Cosmos gateway, multi-region writes); co-locate dependencies with Agent Service",
        "Model levers: max_output_tokens, truncation, cheapest adequate model, budgets and alerts, PAYG to PTU when stable, restrict the playground in production",
        "Azure Firewall Basic unless you need more; in a landing zone share the firewall and DDoS plan",
    ], theme="yellow", icon="cost-management", src=[S_BASE])
    ops = Card(cw, "Operational excellence", [
        "Separate Foundry resources and dependencies per environment; agent compute is Microsoft-managed serverless",
        "Agent Framework (C#, Python) for the runtime, Foundry SDK for platform operations",
        "Pin the agent version and the model version (disable auto-upgrade); agent versions are immutable",
        "Agents as code + CI/CD from network-connected build agents; hosted agents roll back by re-pointing the endpoint's version selector",
        "No native blue-green or canary: add a routing layer such as an API gateway",
        "Use structured inputs only for instruction text: don't template MCP URLs",
        "Monitor the jump boxes; Azure Monitor baseline alerts",
    ], theme="violet", icon="monitor", src=[S_BASE])
    perf = Card(cw, "Performance efficiency", [
        "A codeless agent gives you no control over AI Search queries: tune the index, replace the connection with your own API, or run the orchestration yourself",
        "Model capacity: PTU versus shared; keep the number of tools small",
        "Watch HTTP 429 and 503",
        "Plan a /24 agent subnet and a /24 MCP subnet",
    ], theme="blue", icon="metrics", src=[S_BASE, S_GW])
    r, b = row(cv, 0, y, [sec, cost, ops, perf], gap=gap)
    return b + 56


# ----------------------------------------------------------------------------------------------------- 5 gotchas
def _gotchas(cv, y):
    y = chapter(cv, y, "5  Four production traps",
                f"None of these shows up in a quick proof of concept ({ASOF})")
    gap = 40
    cw = (W - 3 * gap) / 4
    n1 = Note(cw, "Chat content (code, SQL, HTML) triggers false positives, and the OWASP anomaly score accumulates across turns, so a long chat can suddenly return HTTP 403. "
                  "Add exclusions scoped to the chat-message body field and to specific rule groups, and check the request-body size limits.",
              kind="gotcha", title="WAF tuning for chat", src=[S_BASE])
    n2 = Note(cw, "The portal runs many actions with the service's identity, so a user with limited RBAC may still see conversations and agent definitions: restrict the portal in production. "
                  "A project created in the portal doesn't inherit your PEs or NSGs: treat project creation as privileged and use IaC only.",
              kind="gotcha", title="Portal access is wider than RBAC suggests", src=[S_BASE, S_RBAC])
    n3 = Note(cw, "Agent Service doesn't enforce per-user authorization on conversations (broken object-level authorization): your app server must verify that the authenticated user "
                  "owns the conversation ID. Hosted-agent per-user session isolation applies only if the request carries the end-user identity (isolate-sessions-per-user, "
                  "multiplex-session-users).", kind="gotcha", title="Conversation isolation is your job", src=[S_BASE])
    n4 = Note(cw, "Tool invocation is non-deterministic, so cost is unpredictable: limit the connected tools, tune the prompt and monitor. REST agent creation can accept a model and tool "
                  "pair that fails at runtime. Pay-as-you-go is best-effort: decide early whether you need provisioned throughput.",
              kind="warn", title="Cost and runtime surprises", src=[S_BASE, S_LIMITS])
    hh = max(n.h for n in (n1, n2, n3, n4))
    for i, n in enumerate((n1, n2, n3, n4)):
        n.place(cv, i * (cw + gap), y, h=hh)
    return y + hh + 60


def _sources(cv, y):
    sources(cv, 0, y, [S_BASE, S_SAS, S_OWN, S_VNET, S_PRIV, S_NETOPT, S_ARCH, S_RBAC, S_LIMITS, S_PATTERNS, S_REPO, S_BLOG], w=W, cols=3)


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _decisions(cv, y)
    y = _tools(cv, y)
    y = _resilience(cv, y)
    y = _pillars(cv, y)
    y = _gotchas(cv, y)
    _sources(cv, y)
