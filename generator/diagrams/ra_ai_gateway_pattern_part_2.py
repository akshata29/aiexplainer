"""Hub AI gateway reference architecture, part 2: how Foundry plugs into the gateway (token limits, MCP governance, bring
your own model), MCP servers behind API Management, the Citadel Governance Hub, design decisions and Well-Architected notes."""
from __future__ import annotations

from generator.diagrams.ra_ai_gateway_pattern import (
    W, C, N, StepsCard, pill, _node, _frame, _pe, _wire, _mini_panel, S_GW, S_BASE, S_CAP, S_MR, S_BACKENDS, S_APIM_REL,
    S_F_GW, S_F_LIM, S_F_MCP, S_F_BYOM, S_F_HA, S_LZ_GW, S_LZ_L1, S_LZ_NET, S_ACC, S_LABS, S_AOAI_APIM, S_MCP, RED, GREY)
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="ra-ai-gateway-pattern-part-2", title="Hub AI gateway reference architecture, part 2", section="3",
    group="Reference architectures", order=7.5,
    description="How Foundry plugs into the gateway (per-project token limits, MCP governance, bring your own model), MCP servers "
                "behind API Management, the Citadel Governance Hub with its contracts and network options, and the design decisions.",
    tags=["ai-gateway", "mcp-governance", "byom", "citadel", "contracts", "design-decisions"],
)

S_MCP_SEC = learn("api-management/secure-mcp-servers", base="azure")
S_F_TOOLAUTH = learn("agents/how-to/tools/tool-authentication")
S_LZ_AGENT = "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/configuration/"
S_TF = "https://github.com/Azure/terraform-ai-gateway-landing-zone"
S_SNIPPETS = "https://github.com/Azure/api-management-policy-snippets"


# ====================================================================== 0. title and summary
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Hub AI gateway reference architecture, part 2",
        "Foundry integration (token limits, MCP governance, bring your own model), MCP servers behind API Management, the Citadel "
        "Governance Hub and the design decisions (facts as of 2026-11-03)", icon="apim", w=W)
    y = bottom + 36
    gap = 40
    cw = (W - 4 * gap) / 5
    cards = [
        C(cw, "Foundry's link is per resource", [
            "Manage > AI Gateway is enabled on the Foundry resource: all its projects share one gateway",
            "Per project and deployment: TPM -> 429, total token quota -> 403",
            "Create new = Basic v2; use existing = same tenant and subscription, a v2 tier",
        ], theme="orange", icon="foundry", badge="preview", src=[("Enable the AI gateway in Foundry", S_F_GW)]),
        C(cw, "MCP governance has edges", [
            "Only new MCP tools created in the portal that don't use managed OAuth are routed through the gateway",
            "Policies are applied in the Azure portal, not in Foundry",
            "The gateway logs no tool traces",
        ], theme="orange", icon="mcp", badge="preview", src=[("Govern MCP tools through the gateway", S_F_MCP)]),
        C(cw, "Bring your own model: prompt agents only", [
            "Connection type Azure API Management or Model Gateway",
            "Prompt agents in the Agent SDK; the Responses API is not supported",
            "Non-Microsoft models are your responsibility",
        ], theme="blue", icon="ml", badge="preview", src=[("Bring your own model with a gateway", S_F_BYOM)]),
        C(cw, "Citadel = contracts", [
            "Access, backend and publish contracts in infrastructure as code (.bicepparam)",
            "Default-deny allow-lists, content safety and PII handling per contract",
            "Usage streams through Event Hub and a Logic App into Cosmos DB",
        ], theme="grape", icon="landing-zone", src=[("Governance Hub layer", S_LZ_L1)]),
        C(cw, "Hub or dedicated spoke", [
            "Hub-based: simplest, the gateway lives in the existing hub VNet",
            "Hub-spoke-hub: a gateway spoke peered to the hub, dual firewall inspection",
            "Hub-spoke-hub needs post-deploy VNet peering, DNS servers and route tables",
        ], theme="indigo", icon="vnet", src=[("Network approach", S_LZ_NET)]),
    ]
    _, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    note = N(W, "Part 1 draws the control tower, the policy map and the topologies. The step-by-step portal flows for the Foundry-side gateway "
                "(enable it, set limits, govern MCP tools, bring your own model) are in the canvas 'AI gateway and token limits' in Control "
                "plane and cost: here is the reference-architecture view of those three integrations, then MCP servers behind API Management and the Citadel hub.",
             kind="info", title="Where this part fits")
    note.place(cv, 0, y)
    return note.bottom + 70


# ====================================================================== 1. Foundry <-> gateway
def _foundry(cv, y):
    _, hb = section_header(
        cv, 0, y, "1  How Foundry plugs into the gateway: three integrations (all preview)", size=32,
        sub="Control-plane view of Manage > AI Gateway and bring your own model. Preview features can change; verify in the linked pages")
    y = hb + 36
    PH = 470
    xs = [0, 1090, 2180]

    # ---- lane A: per-project token limits
    px, py = xs[0], y
    _mini_panel(cv, px, py, 1020, PH, "A  Model calls with per-project limits", "Manage > AI Gateway > Token management (preview)", "grape")
    _frame(cv, px + 24, py + 112, 290, 290, "Foundry resource", "green", icon="foundry", dash="dashed")
    pa = _node(cv, px + 44, py + 172, 250, 80, "Project A", "agent", "green", sub="gateway enabled", icon_pos="left", size=17)
    pb = _node(cv, px + 44, py + 282, 250, 80, "Project B", "agent", "green", sub="new projects: on by default", icon_pos="left", size=17)
    gw = _node(cv, px + 400, py + 176, 250, 170, "AI gateway", "apim", "grape", sub="API Management: Basic v2 when created from the UI")
    md = _node(cv, px + 750, py + 196, 240, 130, "Model deployments", "openai", "blue", sub="limits per project x deployment")
    _wire(cv, pa, gw, a_side="right", b_side="left", tb=0.3)
    _wire(cv, pb, gw, a_side="right", b_side="left", tb=0.7)
    _wire(cv, gw, md, a_side="right", b_side="left")
    pill(cv, px + 388, py + 372, "TPM exceeded: 429", "yellow", fill="soft")
    pill(cv, px + 388 + 190, py + 372, "total quota exceeded: 403", "yellow", fill="soft")

    # ---- lane B: governed MCP tool
    px, py = xs[1], y
    _mini_panel(cv, px, py, 1020, PH, "B  A governed MCP tool", "Govern MCP tools through the gateway (preview)", "orange")
    ag = _node(cv, px + 24, py + 150, 210, 120, "Agent", "agent", "green", sub="uses a new MCP tool created in the portal")
    gb = _node(cv, px + 320, py + 130, 270, 160, "AI gateway", "apim", "grape", sub="tool endpoint becomes <apim>.azure-api.net/mcp/...")
    ms = _node(cv, px + 690, py + 150, 300, 120, "MCP server", "mcp", "orange", sub="called with its own auth method")
    _wire(cv, ag, gb, a_side="right", b_side="left")
    _wire(cv, gb, ms, a_side="right", b_side="left")
    cv.text(px + 24, py + 306, "policies you apply in the Azure portal (examples):", size=14, color=MUTED)
    ChipFlow(["rate limit", "IP filter", "correlation ID", "header cleanup", "regional routing"], 560, theme="grape", size=14,
             fill="soft").place(cv, px + 24, py + 330)
    cv.text(px + 690, py + 306, "MCP auth methods:", size=14, color=MUTED)
    ChipFlow(["managed identity", "key-based", "custom OAuth passthrough", "unauthenticated"], 310, theme="orange", size=14,
             fill="soft").place(cv, px + 690, py + 330)
    pill(cv, px + 24, py + 414, "no tool traces in the gateway: use API Management and MCP server logs", "red", size=14, fill="soft")

    # ---- lane C: bring your own model
    px, py = xs[2], y
    _mini_panel(cv, px, py, 1020, PH, "C  Bring your own model (BYOM)", "Admin-connected models behind a gateway (preview)", "blue")
    pr = _node(cv, px + 24, py + 150, 190, 120, "Prompt agent", "agent", "green", sub="built with the Agent SDK")
    cn = _node(cv, px + 266, py + 150, 210, 120, "Connection", "api-connections", "blue", sub="type: API Management or Model Gateway")
    gc = _node(cv, px + 528, py + 140, 200, 140, "Gateway", "apim", "grape", sub="your API Management or a model gateway")
    mo = _node(cv, px + 780, py + 150, 210, 120, "Your model", "ml", "blue", sub="a non-Microsoft product", dash="dashed", fill="soft")
    _wire(cv, pr, cn, a_side="right", b_side="left")
    _wire(cv, cn, gc, a_side="right", b_side="left")
    _wire(cv, gc, mo, a_side="right", b_side="left")
    ChipFlow(["model reference: <connection-name>/<model-name>", "base URL = gateway base path only",
              "auth: APIM subscription key or managed identity"], 960, theme="blue", size=14, fill="soft").place(cv, px + 24, py + 312)
    pill(cv, px + 24, py + 390, "Responses API not supported", "red", size=14, fill="soft")
    pill(cv, px + 290, py + 390, "not with the Copilot harness", "red", size=14, fill="soft")
    y += PH + 24

    # ---- fact cards
    ca = C(1020, "Enable it and set limits", [
        "Create new = a Basic v2 API Management instance. The gateway created from the UI is public: network-isolate it in the Azure portal",
        "Use existing: same Entra tenant and subscription, a v2 tier, and the API Management Service Contributor role",
        "A private Foundry needs Standard v2 or Premium v2 with a private endpoint, or Premium v2 VNet-injected",
        "Enabled on the Foundry resource, so all projects share it; new projects are enabled by default, existing ones use Add project to gateway",
        "Separate gateways need separate Foundry resources",
        "Limits per project + deployment: TPM -> 429; a total token quota per hour, day, week, month or year -> 403. They apply immediately; concurrent requests can briefly overshoot",
    ], theme="grape", badge="preview", src=[("Enable the AI gateway in Foundry", S_F_GW), ("Enforce token limits on model deployments", S_F_LIM)])
    cb = C(1020, "Govern MCP tools", [
        "Only new MCP tools created in the Foundry portal that don't use managed OAuth go through the gateway; their endpoint becomes https://<apim>.azure-api.net/mcp/...",
        "Existing tools are not re-routed",
        "Policies are applied in the Azure portal, not in Foundry",
        "! Not supported: SharePoint, code-first MCP tools, managed-OAuth tools and OpenAPI tools",
        "! The gateway doesn't log tool traces: use API Management logs and the MCP server's own logs",
        "MCP auth methods: managed identity, key-based, custom OAuth identity passthrough, unauthenticated",
        "Verify with APIM metrics and logs: 429 from a rate limit, 403 from an IP filter",
    ], theme="orange", badge="preview", src=[("Govern MCP tools through the gateway", S_F_MCP), ("Tool authentication", S_F_TOOLAUTH)])
    cc = C(1020, "Bring your own model", [
        "An admin connects the model under Manage > Resource details; connection type Azure API Management or Model Gateway",
        "Base URL = the gateway base path only (API Management defaults: /deployments, /deployments/{name}, provider AzureOpenAI)",
        "Auth: an APIM subscription key or a managed identity (audience such as https://cognitiveservices.azure.com/, validated with validate-azure-ad-token). Model Gateway: static or dynamic discovery with an API key or OAuth 2.0",
        "! Prompt agents in the Agent SDK only; the Responses API is not supported; not with the Copilot harness",
        "Tools that work: Code Interpreter, Functions, File Search, OpenAPI, Foundry IQ, SharePoint (preview), Fabric data agent (tool deprecation Nov 6, 2026, as of 2026-11-03), MCP, Browser Automation",
        "Full isolation: the template 16-private-network-standard-agent-apim-setup, or a self-hosted gateway reachable inside the Agent Service VNet",
        "! BYOM models are non-Microsoft products: they are your responsibility",
    ], theme="blue", badge="preview", src=[("Bring your own model with a gateway", S_F_BYOM)])
    _, b = row(cv, 0, y, [ca, cb, cc], gap=70)
    return b + 70


# ====================================================================== 2. MCP behind API Management
def _mcp(cv, y):
    _, hb = section_header(
        cv, 0, y, "2  MCP servers behind API Management", size=32,
        sub="The API Management-native path: expose a REST API as an MCP server or front an existing one, then secure, govern, observe and publish it")
    y = hb + 36
    PH = 560
    with cv.panel(0, y, w=W, h=PH, title="API Management as the MCP gateway", theme="grape", style="dashed", fill="none", pad=24,
                  title_size=26, sub_size=15, sub="MCP tools only; policies currently apply to every operation exposed as a tool") as pn:
        # clients
        with cv.panel(pn.ix, pn.iy, w=420, title="MCP clients", theme="gray", style="solid", fill="soft", pad=18, title_size=22) as cl:
            c1 = _node(cv, cl.ix, cl.iy, 384, 84, "VS Code", "vscode", "gray", icon_pos="left", size=18)
            c2 = _node(cv, cl.ix, cl.iy + 108, 384, 84, "Copilot Studio", "copilot", "gray", icon_pos="left", size=18)
            c3 = _node(cv, cl.ix, cl.iy + 216, 384, 84, "Any MCP client", "mcp", "gray", icon_pos="left", size=18,
                       sub="Streamable HTTP /mcp")
        # gateway stages
        gx = pn.ix + 420 + 90
        sw = 440
        stages = [
            Card(sw, "Inbound security", [
                "Subscription key header Ocp-Apim-Subscription-Key",
                "OAuth 2.1 / Entra token validated by validate-azure-ad-token; protected resource metadata (PRM) samples exist",
                "To forward a token: declare Authorization a required header and forward it in the outbound policy",
            ], theme="red", icon="conditional-access", src=[("Secure MCP servers", S_MCP_SEC)]),
            Card(sw, "Governance policies", [
                "Rate limiting and quota",
                "Authentication and authorization: JWT from Entra or another identity provider",
                "IP filtering and caching",
                "They apply to all operations exposed as tools",
            ], theme="grape", icon="policy", src=[("MCP servers in API Management", S_MCP)]),
            Card(sw, "Outbound security", [
                "Credential manager: register the app in the IdP, create a credential provider, then connections",
                "Policies get-authorization-context + set-header add the token to the backend call",
            ], theme="red", icon="key-vault", src=[("Secure MCP servers", S_MCP_SEC)]),
        ]
        xs_ = [gx + i * (sw + 80) for i in range(3)]
        hh = max(c.h for c in stages)
        for c, x in zip(stages, xs_):
            c.place(cv, x, pn.iy, h=hh)
        for i in range(2):
            arrow(cv, [(xs_[i] + sw + 6, pn.iy + hh / 2), (xs_[i + 1] - 6, pn.iy + hh / 2)], sw=3)
        for c in (c1, c2, c3):
            arrow(cv, [(cl.right + 6, c.cy), (gx - 8, pn.iy + hh / 2)], sw=2.5, color=GREY)
        # backends
        bx = xs_[2] + sw + 90
        bw = W - 24 - bx
        with cv.panel(bx, pn.iy, w=bw, title="Backends", theme="orange", style="solid", fill="soft", pad=18, title_size=22) as bk:
            b1 = _node(cv, bk.ix, bk.iy, bw - 36, 100, "REST API as an MCP server", "api", "orange", icon_pos="left", size=18,
                       sub="API operations become MCP tools")
            b2 = _node(cv, bk.ix, bk.iy + 128, bw - 36, 100, "Existing MCP server", "mcp", "orange", icon_pos="left", size=18,
                       sub="for example LangChain / LangServe, Logic Apps, Functions")
        arrow(cv, [(xs_[2] + sw + 6, pn.iy + hh / 2), (bx - 8, pn.iy + hh / 2)], sw=3)
        # discovery and monitoring
        by = pn.iy + hh + 46
        d1 = _node(cv, xs_[0], by, 560, 96, "Azure API Center", "api-connections", "grape", icon_pos="left", size=18,
                   sub="registry and portal; also lists MCP servers hosted outside API Management")
        d2 = _node(cv, xs_[0] + 640, by, 560, 96, "Application Insights and Azure Monitor", "app-insights", "violet", icon_pos="left", size=18,
                   sub="correlation IDs and the trace policy for MCP traffic")
        d3 = _node(cv, xs_[0] + 1280, by, 640, 96, "Tiers", "apim", "gray", icon_pos="left", size=18,
                   sub="classic Developer, Basic, Standard, Premium; v2 Basic, Standard, Premium; self-hosted gateway")
        for d in (d1, d2):
            arrow(cv, [(d.cx, by - 4), (d.cx, pn.iy + hh + 6)], dash="dotted", sw=2, color=get_theme("grape").stroke, end_head=None)
    y = pn.bottom + 28
    n1 = N(1020, "MCP tools only: no MCP resources or prompts. MCP servers are not supported in API Management workspaces. Early access is "
                 "through the 'AI Gateway' release channel (as of 2026-11-03).", kind="warn", title="Limits of MCP in API Management",
           src=[("MCP servers in API Management", S_MCP)])
    n1.place(cv, 0, y)
    n2 = N(1020, "Transports: Streamable HTTP at /mcp (it replaces HTTP+SSE) and SSE at /sse and /messages (the deprecated 2024-11-05 transport). "
                 "Two ways to expose a server: a REST API as an MCP server, or an existing MCP server.", kind="info",
           title="Transports and two ways to expose", src=[("MCP servers in API Management", S_MCP)])
    n2.place(cv, 0, n1.bottom + 20)
    sn = C(1020, "Foundry's sample policy snippets", [
        "rate-limit-by-key: for example 60 calls per 60 seconds keyed by IP",
        "ip-filter: allow the internal range and a trusted app",
        "set-header X-Correlation-Id = context.RequestId",
        "Delete the Cookie and Referer headers; don't delete Authorization",
        "choose / when on an X-Region header with set-backend-service for regional routing",
        "More snippets: github.com/Azure/api-management-policy-snippets",
    ], theme="grape", icon="policy", src=[("Govern MCP tools through the gateway", S_F_MCP)])
    sn.place(cv, 1090, y)
    tw = C(1020, "Two MCP governance paths", [
        "# Foundry-integrated gateway (preview)",
        "New MCP tools created in the Foundry portal that don't use managed OAuth are routed through the gateway; policies are set in the Azure portal; the gateway keeps no tool traces",
        "# API Management-native",
        "Expose a REST API as an MCP server or front an existing MCP server; secure it with Entra tokens or subscription keys and the credential manager; discover it in API Center",
    ], theme="orange", icon="mcp", src=[("Govern MCP tools through the gateway", S_F_MCP), ("MCP servers in API Management", S_MCP)])
    tw.place(cv, 2180, y)
    return max(n2.bottom, sn.bottom, tw.bottom) + 70


# ====================================================================== 3. Citadel Governance Hub
def _flow_arrow(cv, x1, x2, y, n, label, *, back=False, color=INK, num_theme="grape"):
    """Horizontal step arrow with its number on the line and the label above (forward) or below (return)."""
    arrow(cv, [(x1, y), (x2, y)], sw=2.5, dash="dashed" if back else "solid", color=color)
    mx = (x1 + x2) / 2
    numbered(cv, mx, y, n, theme=num_theme, d=28, size=16)
    tw, th_ = metrics.text_size(label, 14)
    cv.text(mx - tw / 2, (y + 20) if back else (y - 20 - th_), label, size=14, color=INK)


def _citadel(cv, y):
    _, hb = section_header(
        cv, 0, y, "3  The Citadel Governance Hub (AI Gateway Landing Zone)", size=32,
        sub="Contract-driven governance hub from the AI Landing Zones project: a community accelerator on GitHub Pages, not a Microsoft Learn page (as of 2026-11-03)")
    y = hb + 36
    SRC_L1 = [("Governance Hub (layer 1)", S_LZ_L1)]

    # ---- 3a blueprint | components | dimensions
    with cv.panel(0, y, w=700, title="AI Citadel Blueprint", sub="four layers; this canvas is layer 1", theme="grape", style="solid",
                  fill="soft", pad=20, title_size=24, sub_size=15) as bp:
        l1 = _node(cv, bp.ix, bp.iy, 660, 150, "L1  Governance Hub", "apim", "grape", icon_pos="left", size=20,
                   sub="owned by the AI CoE and platform team; every AI call flows through this layer and nothing bypasses it")
        cy = l1.bottom + 14
        for lab in ("L2  Agent Operations", "L3  Agent Management", "L4  Security Foundation"):
            b = _node(cv, bp.ix, cy, 660, 64, lab, None, "gray", dash="dashed", fill="soft", size=18)
            cy = b.bottom + 12
        cv.text(bp.ix, cy + 2, "Layers 2-4 are not detailed here.", size=14, color=MUTED)
    comp = C(1060, "Core components", [
        "# Required",
        "API Management: the unified AI gateway",
        "Foundry, and Microsoft Entra",
        "# Recommended",
        "API Center: the universal AI registry",
        "Defender for AI and Purview",
        "# Usage and telemetry",
        "Log Analytics and Application Insights",
        "Event Hub (usage streaming), a Logic App (usage ingestion, private mode opt-in) and Cosmos DB (usage analytics)",
        "# Network and optional",
        "A VNet; Azure Managed Redis for semantic caching (optional)",
        "Content Safety and Language PII are served from the primary Foundry account",
    ], theme="grape", icon="landing-zone", src=SRC_L1, min_h=bp.h, body_size=17)
    comp.place(cv, 770, y)
    dims = [
        C(635, "Governance", ["Resiliency, observability and capacity management", "Universal AI routing", "Universal AI catalog"], theme="grape"),
        C(635, "Security", ["Authentication and authorization", "Content safety", "PII processing and audit logs"], theme="red"),
        C(635, "Operations", ["Access contracts", "Publish contracts", "Backend contracts"], theme="blue"),
        C(635, "Cloud and hybrid", ["A hybrid data plane", "Any model, tool or agent"], theme="indigo"),
    ]
    cv.text(1900, y, "Four dimensions", size=22, color=get_theme("grape").deep)
    grid(cv, 1900, y + 36, dims, 2, gap_x=30, gap_y=24)
    y = max(bp.bottom, comp.bottom) + 40

    # ---- 3b resiliency layers | security
    with cv.panel(0, y, w=1900, title="Resiliency layers", sub="a request meets them in this order", theme="indigo", style="solid", fill="soft",
                  pad=22, title_size=24, sub_size=15) as rz:
        steps = [("Affinity", "session affinity pins stateful conversations", "link"), ("Load balance", "pools and aliases with priority and weight", "load-balancer"),
                 ("Retry and failover", "cross-model and cross-provider fallback; typed errors", "regions"),
                 ("Circuit breaker", "parks unhealthy backends, then probes them back", "service-health")]
        bw_ = 392
        nodes = []
        for i, (t, s, ic) in enumerate(steps):
            nodes.append(_node(cv, rz.ix + i * (bw_ + 60), rz.iy + 10, bw_, 150, t, "gear" if ic == "link" else ic, "indigo", sub=s, size=19, sub_size=14))
        for a, b in zip(nodes, nodes[1:]):
            _wire(cv, a, b, a_side="right", b_side="left", sw=3)
        cv.text(rz.ix, nodes[0].bottom + 22, "Backends are grouped into pools with aliases; each backend carries a priority and a weight.",
                size=15, color=INK)
    sec = C(W - 1900 - 70, "Security in the hub", [
        "API key and/or an identity-provider JWT; per-contract allow-lists, default-deny",
        "Content safety (prompt shields, thresholds tuned per contract) on requests and responses",
        "PII detect and anonymise before the model is called; a failure returns a structured 502",
        "Audit logs: metadata always, bodies optional, streamed to Defender and Sentinel",
    ], theme="red", icon="defender", src=SRC_L1, min_h=rz.h)
    sec.place(cv, 1970, y)
    y = max(rz.bottom, sec.bottom) + 40

    # ---- 3c contracts
    CH = None
    with cv.panel(0, y, w=W, title="Contract-driven governance", sub="contracts are infrastructure as code (.bicepparam): demand on the left, supply on the right",
                  theme="grape", style="dashed", fill="none", pad=24, title_size=26, sub_size=15) as ct:
        cx0, top = ct.ix, ct.iy + 4
        with cv.panel(cx0, top, w=380, title="Consumers", theme="gray", style="solid", fill="soft", pad=18, title_size=22) as cs:
            u1 = _node(cv, cs.ix, cs.iy, 344, 96, "Business unit", "groups", "gray", icon_pos="left", size=18)
            u2 = _node(cv, cs.ix, cs.iy + 124, 344, 96, "Use case", "app", "gray", icon_pos="left", size=18)
            u3 = _node(cv, cs.ix, cs.iy + 248, 344, 96, "Environment", "deployment-environments", "gray", icon_pos="left", size=18)
        acc = C(640, "Access contracts (demand, northbound)", [
            "One per business unit, use case and environment",
            "Becomes an API Management product, subscription and policies",
            "Asset allow-list, token and request limits, content safety, PII handling",
            "Credentials delivered through Key Vault, a Foundry connection, or directly",
        ], theme="grape", icon="policy", src=SRC_L1)
        acc.place(cv, cx0 + 380 + 80, top + 70)
        hub = _node(cv, acc.right + 90, top + 20, 420, 440, "Governance Hub", "apim", "grape", sub="API Management: every AI call flows through it",
                    size=24, sub_size=16, icon_size=48)
        bk = C(660, "Backend contracts (supply, southbound)", [
            "LLM backends and model aliases",
            "Load balancing and failover",
            "GET /deployments discovery",
            "Multi-provider, including Amazon Bedrock",
        ], theme="blue", icon="openai", src=SRC_L1)
        bk.place(cv, hub.right + 90, top)
        pb = C(660, "Publish contracts", [
            "Tools / MCP and Agents / A2A",
            "Optional API Center registration",
            "Foundry A2A publishing",
        ], theme="orange", icon="mcp", badge="preview", src=[("Governance Hub (layer 1), version 1.0.0-preview", S_LZ_L1)])
        pb.place(cv, hub.right + 90, bk.bottom + 36)
        sx = bk.right + 90
        s1 = _node(cv, sx, bk.y + 10, W - 24 - sx, 110, "LLM backends and providers", "openai", "blue", icon_pos="left", size=18, sub="Foundry, Amazon Bedrock and others")
        s2 = _node(cv, sx, pb.y + 4, W - 24 - sx, 96, "Tools and MCP servers", "mcp", "orange", icon_pos="left", size=18)
        s3 = _node(cv, sx, s2.bottom + 24, W - 24 - sx, 96, "Agents (A2A)", "a2a", "green", icon_pos="left", size=18)
        for u, ty in ((u1, 0.2), (u2, 0.5), (u3, 0.8)):
            connect(cv, u, acc, a_side="right", b_side="left", tb=ty, sw=2.5, route="elbow")
        connect(cv, acc, hub, a_side="right", b_side="left", sw=3)
        connect(cv, hub, bk, a_side="right", b_side="left", ta=0.25, tb=0.5, sw=3, route="elbow")
        connect(cv, hub, pb, a_side="right", b_side="left", ta=0.75, tb=0.5, sw=3, route="elbow")
        connect(cv, bk, s1, a_side="right", b_side="left", ta=0.5, tb=0.5, sw=2.5, route="elbow")
        connect(cv, pb, s2, a_side="right", b_side="left", ta=0.35, tb=0.5, sw=2.5, route="elbow")
        connect(cv, pb, s3, a_side="right", b_side="left", ta=0.7, tb=0.5, sw=2.5, route="elbow")
    y = ct.bottom + 50

    # ---- 3d network options
    PWD, PH = 1560, 450
    for i, (title, sub) in enumerate([("Network option 1: hub-based", "the gateway lives inside the existing hub VNet; a 4-step flow"),
                                      ("Network option 2: hub-spoke-hub", "a dedicated gateway spoke peered to the hub; a 6-step flow with dual inspection")]):
        _mini_panel(cv, i * (PWD + 80), y, PWD, PH, title, sub, "indigo", dash="dashed")
    # option 1
    x0 = 0
    _frame(cv, x0 + 24, y + 110, 400, 300, "Agent spoke VNet", "gray")
    ag = _node(cv, x0 + 54, y + 190, 340, 140, "Spoke agent", "agent", "green", sub="calls the gateway directly", icon_pos="left")
    _frame(cv, x0 + 560, y + 110, 430, 300, "Hub VNet", "indigo")
    gw = _node(cv, x0 + 590, y + 190, 370, 140, "AI gateway", "apim", "grape", sub="Governance Hub", icon_pos="left")
    bkn = _node(cv, x0 + 1130, y + 150, 400, 220, "Backends", "cubes", "gray", sub="LLMs, agents and tools; backends in other spokes must be forced through the hub firewall",
                icon_pos="top")
    _flow_arrow(cv, ag.right + 6, gw.x - 6, y + 235, 1, "auth token")
    _flow_arrow(cv, gw.right + 6, bkn.x - 6, y + 235, 2, "governed request")
    _flow_arrow(cv, bkn.x - 6, gw.right + 6, y + 295, 3, "response + telemetry", back=True)
    _flow_arrow(cv, gw.x - 6, ag.right + 6, y + 295, 4, "validated, logged response", back=True)
    # option 2
    x0 = PWD + 80
    bw2, gp = 230, 190
    sx_ = [x0 + 34 + i * (bw2 + gp) for i in range(4)]
    n_ag = _node(cv, sx_[0], y + 170, bw2, 170, "Agent spoke", "agent", "green", sub="calls through the hub firewall")
    n_fw = _node(cv, sx_[1], y + 170, bw2, 170, "Hub firewall", "firewall", "indigo", sub="inspects the call in and out")
    _frame(cv, sx_[2] - 18, y + 130, bw2 + 36, 250, "", "grape", dash="dashed")
    cv.text(sx_[2] - 4, y + 138, "Gateway spoke VNet", size=15, color=get_theme("grape").deep)
    n_gw = _node(cv, sx_[2], y + 170, bw2, 170, "AI gateway", "apim", "grape", sub="governance", fill="solid")
    n_bk = _node(cv, sx_[3], y + 170, bw2, 170, "Backends", "cubes", "gray", sub="LLMs, agents and tools")
    yf, yr = y + 226, y + 292
    _flow_arrow(cv, n_ag.right + 6, n_fw.x - 6, yf, 1, "inspection")
    _flow_arrow(cv, n_fw.right + 6, n_gw.x - 24, yf, 2, "governed call")
    _flow_arrow(cv, n_gw.right + 6, n_bk.x - 6, yf, 3, "backend call")
    _flow_arrow(cv, n_bk.x - 6, n_gw.right + 6, yr, 4, "response + telemetry", back=True)
    _flow_arrow(cv, n_gw.x - 24, n_fw.right + 6, yr, 5, "validation, egress check", back=True)
    _flow_arrow(cv, n_fw.x - 6, n_ag.right + 6, yr, 6, "to the agent", back=True)
    y += PH + 20
    o1 = C(PWD, "Hub-based: when it fits", [
        "+ Deploy inside the existing hub VNet; spoke agents call the gateway directly. The simplest topology",
        "! Backends in other spokes must be forced through the hub firewall",
    ], theme="indigo", icon="vnet", src=[("Network approach", S_LZ_NET)])
    o1.place(cv, 0, y)
    o2 = C(PWD, "Hub-spoke-hub: when it fits", [
        "+ A dedicated spoke VNet peered to the hub: recommended for strict segmentation or a separate cost centre or subscription; dual inspection through the hub firewall",
        "! After deployment you must configure VNet peering, DNS servers and route tables",
    ], theme="indigo", icon="vnet", src=[("Network approach", S_LZ_NET)])
    o2.place(cv, PWD + 80, y)
    y = max(o1.bottom, o2.bottom) + 44

    # ---- 3e defaults and prerequisites
    cw4 = (W - 3 * 40) / 4
    g1 = C(cw4, "Greenfield defaults", [
        "VNet 10.170.0.0/24",
        "APIM subnet 10.170.0.0/26; private-endpoint subnet 10.170.0.64/26; Function App subnet 10.170.0.128/26",
        "Agent subnet 10.170.0.192/26, delegated to Microsoft.App/environments; foundryNetworkInjectionEnabled = true by default",
        "apimNetworkType = 'External', or 'Internal' for production; apimV2UsePrivateEndpoint = true",
        "Creates an NSG per subnet, private DNS zones, private endpoints (the Logic App endpoint is opt-in) and a route table (needed for APIM Developer and Premium)",
    ], theme="indigo", src=[("Network approach", S_LZ_NET)])
    g2 = C(cw4, "Brownfield prerequisites", [
        "An existing VNet with subnets: APIM /26 or larger, Function App /26+, private endpoint /26+, and Agent /26+ (only when network injection is on)",
        "Private DNS zones created and linked; NSG rules on the APIM subnet; agent subnet delegation",
        "Parameters: useExistingVnet = true, existingVnetRG, apimSubnetName, privateEndpointSubnetName, agentSubnetName, dnsZoneRG and dnsSubscriptionId (the hub subscription)",
    ], theme="indigo", src=[("Network approach", S_LZ_NET)])
    g3 = Table(["Dir", "Port", "From / to", "Why"], [
        ["In", "443", "Internet -> VNet", "gateway access (public)"],
        ["In", "3443", "ApiManagement -> VNet", "control plane"],
        ["In", "6390", "AzureLoadBalancer -> VNet", "health probes"],
        ["In", "443", "AzureTrafficManager -> VNet", "routing"],
        ["Out", "443", "-> Storage", "dependency"],
        ["Out", "1433", "-> Sql", "dependency"],
    ], w=cw4, theme="indigo", size=14, head_size=15, title="APIM subnet NSG (Developer / Premium VNet injection)", title_size=17)
    g4 = C(cw4, "Agent Landing Zone gateway (not Citadel)", [
        "Default ai-gateway-subnet 192.168.5.0/24",
        "API Management Standard v2 or Premium v2 with outbound VNet integration: at least /27, delegated to Microsoft.Web/serverFarms, with an NSG and outbound HTTPS to Key Vault",
        "! Don't put APIM private endpoints in the integration subnet",
        "! The Agent Landing Zone does not deploy the gateway for you",
        "One Agent Execution Plane per business unit or use case",
    ], theme="green", src=[("Agent Landing Zone configuration", S_LZ_AGENT)])
    xs4 = [i * (cw4 + 40) for i in range(4)]
    g1.place(cv, xs4[0], y)
    g2.place(cv, xs4[1], y)
    g3.place(cv, xs4[2], y)
    g4.place(cv, xs4[3], y)
    cv.text(xs4[2], g3.bottom + 6, "Only the rows captured from the page are shown; check it for the rest.", size=13, color=MUTED, wrap=cw4)
    y = max(g1.bottom, g2.bottom, g3.bottom + 40, g4.bottom) + 44

    # ---- 3f onboarding and deployment
    wf = StepsCard(PWD, "Onboard a use case through contracts", [
        (1, "The platform team deploys the Governance Hub (azd with Bicep, or Terraform)", "grape"),
        (2, "Backend contract: register the model backend (endpoint, auth, pool, priority and weight, circuit breaker, alias)", "blue"),
        (3, "Publish contract (preview): publish MCP tools or A2A agents; optionally register them in API Center", "orange"),
        (4, "Access contract per business unit, use case and environment: product, subscription and policies (asset allow-list, token and request limits, content safety, PII); credential via Key Vault, a Foundry connection or directly", "grape"),
        (5, "The use case goes live: governance is injected into every call; usage flows to Event Hub, then Cosmos DB analytics; dashboards and chargeback", "violet"),
    ], theme_name="grape", icon="workflow", src=SRC_L1)
    wf.place(cv, 0, y)
    dp = C(PWD, "Deploy it", [
        "Bicep: Azure-Samples/ai-hub-gateway-solution-accelerator, branch citadel-v1. Terraform: Azure/terraform-ai-gateway-landing-zone",
        "Quick deploy with azd; you need Owner, or Contributor plus User Access Administrator",
        "Publish contracts are preview (1.0.0-preview); layers 2-4 of the blueprint are not covered here",
        "Source: community accelerators on GitHub, not Microsoft Learn: review them before use",
    ], theme="teal", icon="github", src=[("AI Gateway Landing Zone", S_LZ_GW), ("Governance Hub accelerator (GitHub)", S_ACC), ("Terraform module (GitHub)", S_TF)],
          min_h=wf.h)
    dp.place(cv, PWD + 80, y)
    return max(wf.bottom, dp.bottom) + 70


# ====================================================================== 4. decisions and Well-Architected
def _decisions(cv, y):
    _, hb = section_header(cv, 0, y, "4  Design decisions and trade-offs", size=32,
                           sub="Documented guidance for each choice (Architecture Center gateway article, API Management docs, Citadel pages)")
    y = hb + 36
    rows = [
        [("Gateway at all?", "grape"), "No gateway: client-side logic, or Foundry data-zone provisioned + data-zone standard with spillover", "API Management gateway",
         "Skip it if clients are easy to change. Add it when you don't own client code or need segmentation, central telemetry or server-side routing"],
        [("Credential model", "red"), "Pass-through client credentials", "Terminate at the gateway; managed identity to the backend",
         "'Strongly consider' termination and re-establishment; with pass-through, prevent bypass"],
        [("Gateway technology", "grape"), "API Management: policies, pools, circuit breaker", "Custom code: Container Apps behind Front Door or Traffic Manager",
         "API Management is preferred; custom only when the routing is too complex for policy"],
        [("Gateway footprint", "indigo"), "Single-region API Management: a global single point of failure", "Multi-region API Management: replicated gateways, one control plane",
         "A single region isn't for business-critical workloads"],
        [("Model-host posture", "blue"), "Active-active with the same model and version", "PTU primary plus standard passive spillover",
         "Slightly under-provision PTU and add standard overage; standard quota is per subscription"],
        [("Residency", "indigo"), "One unified gateway", "An independent gateway stamp per geopolitical boundary", "Never unify across boundaries when residency applies"],
        [("Landing-zone placement", "indigo"), "Hub VNet: direct and simple", "Dedicated spoke peered to the hub: dual inspection, own cost centre",
         "Citadel: a spoke is recommended for strict segmentation"],
        [("Gateway provisioning", "orange"), "Created from the Foundry UI: Basic v2, public", "An existing v2 API Management: Standard v2 or Premium v2 with a private endpoint, or Premium v2 VNet-injected",
         "A private Foundry needs the second"],
        [("MCP governance", "orange"), "Foundry-integrated: new portal tools only; policies in the Azure portal", "API Management-native MCP: REST to MCP, existing servers, Entra and credential manager",
         "API Management governs MCP tools only (no resources or prompts)"],
        [("Caching", "cyan"), "None", "Semantic caching with Managed Redis and an embeddings API", "Adds components and cost; the benefit depends on repeated prompts and is not quantified in the docs"],
    ]
    t = Table([("Decision", 240), ("Option A", 760), ("Option B", 800), "Documented guidance"], rows, w=W, theme="grape", size=15, head_size=16,
              first_col_theme="grape")
    t.place(cv, 0, y)
    ly = t.bottom + 10
    x = 0
    for label, url in (("Use a gateway in front of multiple model deployments", S_GW), ("AI gateway capabilities in API Management", S_CAP),
                       ("Enable the AI gateway in Foundry", S_F_GW), ("Network approach (AI Landing Zones)", S_LZ_NET)):
        tt = cv.text(x, ly, f"Learn: {label}" if url.startswith("https://learn") else f"Source: {label}", size=12, color=LINK, link=url)
        x += tt.w + 28
    y = ly + 60

    _, hb = section_header(cv, 0, y, "Well-Architected view of the gateway", size=30,
                           sub="As documented across the multi-backend article, API Management and the Citadel pages")
    y = hb + 30
    cw = (W - 4 * 36) / 5
    pillars = [
        C(cw, "Reliability", [
            "Retry and circuit breaker (Retry-After), active-active pools, PTU + standard spillover",
            "API Management: at least 2 units across at least 2 zones (custom code: at least 3 instances)",
            "Multi-region API Management with the performance-based FQDN; treat regions as fully up or down and over-provision survivors",
            "A dedicated health API; synthetic probes consume capacity",
            "A regional model failure and a gateway failure are different single points of failure",
        ], theme="orange", icon="service-health", src=[("Gateway recommendations", S_GW + "#general-recommendations")]),
        C(cw, "Security", [
            "Credential termination plus a managed identity with least-privilege RBAC",
            "Private-endpoint-only backends; an NSG that allows only the gateway; block bypass (X_AZURE_FDID check behind Front Door)",
            "Per-client segmentation at the gateway: keys and RBAC are per instance otherwise",
            "Content safety, PII handling, audit logs to Defender and Sentinel",
            "Azure Policy for consistency; default-deny access contracts (Citadel)",
        ], theme="red", icon="defender", src=[("Gateway recommendations", S_GW + "#general-recommendations")]),
        C(cw, "Cost optimization", [
            "Under-provisioned PTU plus standard overage",
            "Token quotas per client or project; chargeback and showback metrics",
            "Semantic caching (the docs give no savings figure)",
            "Don't add a unified gateway just for quota: use Global Standard, and evaluate data-zone capacity first",
            "Fewer, right-sized instances",
        ], theme="yellow", icon="cost-management", src=[("Gateway recommendations", S_GW)]),
        C(cw, "Operational excellence", [
            "APIOps for gateway configuration; blue-green model rollouts through routing",
            "One telemetry store, unified dashboards and alerts",
            "Infrastructure-as-code contracts (Bicep or Terraform) for onboarding; API Center registry",
            "The gateway in its own resource group or subscription (separation of duties)",
        ], theme="violet", icon="monitor", src=[("Safe deployment practices", S_GW + "#safe-deployment-practices")]),
        C(cw, "Performance efficiency", [
            "Colocate the gateway and the model host in one region",
            "Performance-based routing and a semantic cache",
            "Session affinity for stateful chats",
            "Priority processing lowers latency but adds no quota",
            "Scale units",
        ], theme="blue", icon="metrics", src=[("AI gateway capabilities", S_CAP)]),
    ]
    _, b = row(cv, 0, y, pillars, gap=36)
    return b + 70


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _foundry(cv, y)
    y = _mcp(cv, y)
    y = _citadel(cv, y)
    y = _decisions(cv, y)
    sources(cv, 0, y, [
        ("Use a gateway in front of multiple model deployments or instances", S_GW),
        ("AI gateway capabilities in API Management", S_CAP),
        ("MCP servers in API Management", S_MCP),
        ("Secure access to MCP servers in API Management", S_MCP_SEC),
        ("Deploy API Management to multiple regions", S_MR),
        ("API Management backends: pools and circuit breaker", S_BACKENDS),
        ("Enable the AI gateway in Foundry", S_F_GW),
        ("Enforce token limits on model deployments", S_F_LIM),
        ("Govern MCP tools through the gateway (preview)", S_F_MCP),
        ("Bring your own model with a gateway (preview)", S_F_BYOM),
        ("Tool authentication in Foundry", S_F_TOOLAUTH),
        ("AI Gateway Landing Zone (GitHub Pages, not Learn)", S_LZ_GW),
        ("Citadel Governance Hub, layer 1 (GitHub Pages, not Learn)", S_LZ_L1),
        ("Network approach for the AI Gateway Landing Zone (GitHub Pages, not Learn)", S_LZ_NET),
        ("Agent Landing Zone configuration (GitHub Pages, not Learn)", S_LZ_AGENT),
        ("Governance Hub accelerator (GitHub)", S_ACC),
        ("Terraform AI Gateway Landing Zone (GitHub)", S_TF),
        ("API Management policy snippets (GitHub)", S_SNIPPETS),
    ], w=W, cols=3)
