"""Hub AI gateway (Azure API Management) reference architecture: the control-tower topology, the eight-step policy pipeline,
the four Architecture Center topologies, multi-region and per-boundary variants. Part 2 covers Foundry integration, MCP,
the Citadel Governance Hub, the policy catalogue and design decisions."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="ra-ai-gateway-pattern", title="Hub AI gateway reference architecture", section="3", group="Reference architectures",
    order=7,
    description="Azure API Management as the hub AI gateway in front of Foundry models, MCP tools and agents: the eight-step "
                "policy pipeline with a numbered request flow, the four Architecture Center topologies, multi-region and "
                "per-boundary variants.",
    tags=["ai-gateway", "api-management", "token-limits", "load-balancing", "multi-region", "circuit-breaker"],
)

W = 3200
AC = "azure/architecture"
S_GW = learn("ai-ml/guide/azure-openai-gateway-multi-backend", base=AC)
S_BASE = learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC)
S_CAP = learn("api-management/genai-gateway-capabilities", base="azure")
S_MR = learn("api-management/api-management-howto-deploy-multi-region", base="azure")
S_MCP = learn("api-management/mcp-server-overview", base="azure")
S_BACKENDS = learn("api-management/backends", base="azure")
S_APIM_REL = learn("reliability/reliability-api-management", base="azure")
S_F_GW = learn("configuration/enable-ai-api-management-gateway-portal")
S_F_LIM = learn("control-plane/how-to-enforce-limits-models")
S_F_MCP = learn("agents/how-to/tools/governance")
S_F_BYOM = learn("agents/how-to/ai-gateway")
S_F_HA = learn("how-to/high-availability-resiliency")
S_LZ_GW = "https://azure.github.io/AI-Landing-Zones/ai-gateway-landing-zone/"
S_LZ_L1 = "https://azure.github.io/AI-Landing-Zones/ai-gateway-landing-zone/blueprint/layer-1-governance-hub/"
S_LZ_NET = "https://azure.github.io/AI-Landing-Zones/ai-gateway-landing-zone/plan/network-approach/"
S_ACC = "https://github.com/Azure-Samples/ai-hub-gateway-solution-accelerator"
S_LABS = "https://github.com/Azure-Samples/ai-gateway"
S_AOAI_APIM = "https://github.com/Azure/aoai-apim/"

RED = "#e03131"
GREY = "#868e96"


# ====================================================================== helpers
def _src_fix(b):
    """Citations to pages that are not on Microsoft Learn read 'Source:' instead of 'Learn:'."""
    fixed = []
    for text, url, y in b.src_lines:
        if not url.startswith("https://learn.microsoft.com"):
            text = text.replace("Learn: ", "Source: ", 1)
        fixed.append((text, url, y))
    b.src_lines = fixed
    return b


def C(*a, **k):
    return _src_fix(Card(*a, **k))


def N(*a, **k):
    return _src_fix(Note(*a, **k))


def pill(cv, x, y, text, th_name, *, size=15, icon=None, fill="solid", dash="solid"):
    c = Chip(text, theme=th_name, size=size, icon=icon, fill=fill, dash=dash)
    c.place(cv, x, y)
    return c


class PipeBox(Rect2):
    """One step of the gateway policy pipeline: numbered marker, title, policy name and a few detail lines."""

    def __init__(self, w, n, title, policy, bullets, *, theme_name, icon=None, pad=14, d=34, size=14, title_size=19,
                 pol_size=15):
        self.th = get_theme(theme_name)
        self.w, self.n, self.icon, self.pad, self.d = w, n, icon, pad, d
        self.size, self.title_size, self.pol_size = size, title_size, pol_size
        lh = metrics.line_ratio()
        icon_w = 44 if icon else 0
        tw = (w - 2 * pad - d - 10 - icon_w) * 0.965
        self.t_lines = metrics.wrap_text(title, tw, title_size)
        self.head_h = max(d, len(self.t_lines) * title_size * lh)
        inner = (w - 2 * pad) * 0.965
        self.p_lines = metrics.wrap_text(policy, inner, pol_size) if policy else []
        y = pad + self.head_h + 8
        self.p_y = y
        y += len(self.p_lines) * pol_size * lh + (8 if self.p_lines else 0)
        self.items = []
        for b in bullets:
            lines = metrics.wrap_text(b, inner - 18, size)
            self.items.append((y, lines))
            y += len(lines) * size * lh + 5
        self.h = y - 5 + pad
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, lh = self.th, self.pad, metrics.line_ratio()
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            numbered(cv, x + pad + self.d / 2, y + pad + self.d / 2, self.n, theme=th.name, d=self.d, size=18)
            th_h = len(self.t_lines) * self.title_size * lh
            cv.text(x + pad + self.d + 10, y + pad + (self.head_h - th_h) / 2, "\n".join(self.t_lines),
                    size=self.title_size, color=th.deep)
            if self.icon:
                place_icon(cv, self.icon, x + self.w - pad - 36, y + pad - 1, 36)
            if self.p_lines:
                cv.text(x + pad, y + self.p_y, "\n".join(self.p_lines), size=self.pol_size, color=th.stroke)
            for iy, lines in self.items:
                cy = y + iy + self.size * lh / 2
                cv.ellipse(x + pad + 1, cy - 4, 9, 9, stroke=th.stroke, sw=2, rough=0)
                cv.text(x + pad + 18, y + iy, "\n".join(lines), size=self.size, color=INK)
        cv.register(f"pipe:{self.n}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


class StepsCard(Rect2):
    """Card whose rows are round numbered markers + wrapped text (flow legends)."""

    def __init__(self, w, title, steps, *, theme_name="blue", icon=None, src=(), size=16, title_size=20, pad=16, gap=11,
                 marker_d=30):
        self.th = get_theme(theme_name)
        self.w, self.title, self.icon, self.src = w, title, icon, list(src)
        self.size, self.title_size, self.pad, self.gap, self.d = size, title_size, pad, gap, marker_d
        self.steps = []
        text_w = (w - 2 * pad - marker_d - 12) * 0.965
        y = pad + max(title_size * metrics.line_ratio(), 36 if icon else 0) + 8
        for st in steps:
            n, text = st[0], st[1]
            sth = st[2] if len(st) > 2 else theme_name
            lines = metrics.wrap_text(text, text_w, size)
            hh = max(len(lines) * size * metrics.line_ratio(), marker_d)
            self.steps.append((n, sth, lines, y, hh))
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
                one = len(lines) == 1
                cv.text(x + pad + self.d + 12,
                        y + sy + ((self.d - self.size * metrics.line_ratio()) / 2 + 1 if one else 0),
                        "\n".join(lines), size=self.size, color=INK)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self


# ====================================================================== 0. title, key messages
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Hub AI gateway reference architecture",
        "Azure API Management in front of Foundry models, MCP tools and agents - a control tower that authenticates, throttles, "
        "routes and logs every call (facts as of 2026-11-03)", icon="apim", w=W)
    y = bottom + 36
    gap = 36
    cw = (W - 5 * gap) / 6
    cards = [
        C(cw, "A gateway is a choice", [
            "These topologies don't automatically require a gateway",
            "Add one for central routing control, reliability controls, security segmentation, observability and quota governance",
            "Design it so it doesn't become the new single point of failure",
        ], theme="gray", icon="apim", src=[("Use a gateway in front of multiple model deployments", S_GW)]),
        C(cw, "Foundry won't balance load for you", [
            "Foundry has no advanced load balancing or circuit breaking for model deployments",
            "Alternatives: data-zone provisioned + data-zone standard with spillover, or an API Management gateway",
        ], theme="blue", icon="openai", src=[("Baseline Foundry chat architecture", S_BASE)]),
        C(cw, "What API Management adds", [
            "Token limits, semantic caching, backend pools and a circuit breaker that honours Retry-After",
            "Managed identity to backends, credential manager, content safety",
            "Token metrics, MCP server exposure and an API Center registry",
        ], theme="grape", icon="apim", src=[("AI gateway in API Management", S_CAP)]),
        C(cw, "Foundry's own gateway link", [
            "Manage > AI Gateway puts API Management at the Foundry-resource level",
            "Per-project TPM limits (429) and a total token quota (403)",
            "MCP governance covers only new portal-created MCP tools that don't use managed OAuth",
        ], theme="orange", icon="foundry", badge="preview", src=[("Enable the AI gateway in Foundry", S_F_GW)]),
        C(cw, "Multi-region has limits", [
            "A single-region gateway is a global single point of failure",
            "Multi-region API Management: replicated gateways and a lowest-latency FQDN, but one control plane",
            "No unified gateway across geopolitical boundaries when data residency applies",
        ], theme="indigo", icon="regions", src=[("Multi-region deployment", S_MR)]),
        C(cw, "Citadel: contract-driven hub", [
            "Access, backend and publish contracts govern every call",
            "Deploy inside the hub VNet or as a dedicated spoke peered to the hub",
            "Community accelerator on GitHub, not a Learn page",
        ], theme="grape", icon="landing-zone", src=[("AI Gateway Landing Zone", S_LZ_GW)]),
    ]
    _, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    note = N(W, "This canvas is the reference topology: where the gateway sits, how a call flows through it and which topology to choose. "
                "The Foundry-side view (enable the gateway on a Foundry resource, per-project token limits, govern MCP tools, bring your own "
                "model, step by step) is the canvas 'AI gateway and token limits' in Control plane and cost. Failover behaviour is drawn in "
                "'Multi-region patterns' (BCDR and resiliency). Part 2 of this canvas covers the Foundry integration summary, MCP servers "
                "behind API Management, the Citadel Governance Hub, the policy catalogue and the design decisions.",
             kind="info", title="Where this canvas fits")
    note.place(cv, 0, y)
    y = note.bottom + 26
    legend(cv, 0, y, [("Callers", "gray"), ("Gateway and governance", "grape"), ("Models", "blue"), ("Tools and MCP", "orange"),
                      ("Agents", "green"), ("Identity", "red"), ("Throttling and capacity", "yellow"), ("Guardrails", "pink"),
                      ("Cache and data", "cyan"), ("Networking", "indigo"), ("Observability", "violet")], size=15, gap=26)
    return y + 56


# ====================================================================== 1. the control tower
def _tower(cv, y):
    _, hb = section_header(
        cv, 0, y, "1  The hub AI gateway: one control tower for every model, tool and agent call", size=32,
        sub="Solid arrows = request path (numbers match the steps card)  |  dashed = spillover, retry and the response  |  "
            "dotted = support services")
    y = hb + 40

    # ---- callers
    gap = 60
    cw = (W - 3 * gap) / 4
    callers = [
        Box(cw, "Foundry agents and apps (Agent Service)", sub="prompt and hosted agents calling models and tools", icon="agent",
            icon_pos="left", theme="green", h=112, size=19, sub_size=15),
        Box(cw, "Business apps and copilots", sub="applications that call a model deployment", icon="app", icon_pos="left",
            theme="gray", h=112, size=19, sub_size=15),
        Box(cw, "Other agents (A2A)", sub="agent-to-agent calls through the gateway", icon="a2a", icon_pos="left", theme="green",
            h=112, size=19, sub_size=15),
        Box(cw, "MCP clients (VS Code, Copilot Studio)", sub="remote MCP servers exposed by the gateway", icon="mcp",
            icon_pos="left", theme="orange", h=112, size=19, sub_size=15),
    ]
    row(cv, 0, y, callers, gap=gap, equalize=False)
    bus_y = y + 112 + 46
    for c in callers:
        arrow(cv, [(c.cx, c.bottom + 4), (c.cx, bus_y)], end_head=None, sw=3, color=GREY)
    arrow(cv, [(callers[0].cx, bus_y), (callers[-1].cx, bus_y)], end_head=None, sw=3, color=GREY)
    gw_y = bus_y + 150
    arrow(cv, [(W / 2, bus_y), (W / 2, gw_y - 6)], sw=3, num=1, num_theme="grape", label="OpenAI-compatible endpoint, MCP /mcp or A2A",
          label_pos="right", label_size=15)
    x_id = W / 2 - 40
    for text, th_name, icon in reversed([("APIM subscription key", "red", "apim"), ("Entra JWT", "red", "entra-connect"),
                                          ("managed identity", "red", "managed-identity")]):
        c = Chip(text, theme=th_name, size=15, icon=icon, fill="soft")
        c.place(cv, x_id - c.w, bus_y + 52)
        x_id -= c.w + 12
    cv.text(x_id - 250, bus_y + 56, "caller presents any of:", size=15, color=MUTED)
    arrow(cv, [(2700, gw_y - 6), (2700, bus_y + 4)], dash="dashed", sw=3, color="#2f9e44", num=10, num_theme="green",
          label="response; a cache hit returns here at once", label_pos="left", label_size=15)

    # ---- gateway panel with the pipeline
    n_steps, pgap, pad = 8, 44, 24
    PW = (W - 2 * pad - (n_steps - 1) * pgap) / n_steps
    steps = [
        (2, "Authenticate", "validate-azure-ad-token or subscription key", [
            "Resolve the product, access contract and Foundry project",
            "The client is authorised at the gateway; its credential ends here"], "red", "conditional-access"),
        (3, "Limit tokens", "llm-token-limit", [
            "TPM, or a quota per hour, day, week, month or year",
            "Counter key: subscription, IP or an expression",
            "429 when TPM is exceeded; 403 when the total quota is (Foundry-integrated gateway)"], "yellow", "quotas"),
        (4, "Safety and PII", "llm-content-safety (optional)", [
            "Screen prompts and responses against thresholds",
            "Citadel adds PII detect and anonymise; a failure returns a structured 502"], "pink", "content-safety"),
        (5, "Cache lookup", "llm-semantic-cache-lookup (optional)", [
            "Needs an embeddings API and Azure Managed Redis (or a RediSearch-compatible cache)",
            "A hit returns at once (step 10); a miss continues to routing"], "cyan", "redis"),
        (6, "Route", "backend pool", [
            "Priority, weighted, round-robin or session-aware",
            "PTU primary first, then standard or another region",
            "Same model and version in every pool member"], "indigo", "load-balancer"),
        (7, "Call the backend", "gateway managed identity", [
            "The gateway's own identity calls the model host",
            "Least-privilege Azure RBAC on every instance, equivalent on all failover targets"], "red", "managed-identity"),
        (8, "Trip and retry", "circuit breaker + Retry-After", [
            "429, 500 and 503 are circuit-break signals; Retry-After drives how long the breaker stays open",
            "The request is retried on the next backend before an error goes back"], "yellow", "service-health"),
        (9, "Emit and cache", "llm-emit-token-metric", [
            "Custom dimensions such as client, team and model",
            "Token, prompt and completion logs go to Azure Monitor",
            "llm-semantic-cache-store saves the response"], "violet", "metrics"),
    ]
    boxes = [PipeBox(PW, n, t, pol, bl, theme_name=th_name, icon=ic) for n, t, pol, bl, th_name, ic in steps]
    HB = max(b.h for b in boxes)
    with cv.panel(0, gw_y, w=W, title="AI gateway - Azure API Management", theme="grape", style="solid", fill="soft", pad=pad,
                  title_size=30, sub_size=16,
                  sub="one governed endpoint for models, MCP tools and A2A agents; credentials terminate here and the gateway's managed "
                      "identity calls the backends") as gw:
        chips_y = gw.iy + 8
        pipe_y = chips_y + 44 + 52
        xs = [gw.ix + i * (PW + pgap) for i in range(n_steps)]
        for b, x in zip(boxes, xs):
            b.place(cv, x, pipe_y, h=HB)
        for i in range(n_steps - 1):
            arrow(cv, [(xs[i] + PW + 5, pipe_y + 34 + 14), (xs[i + 1] - 5, pipe_y + 34 + 14)], sw=3)
        sup = [(1, "Microsoft Entra ID", "red", "entra-connect"), (3, "Content Safety / Language PII", "pink", "content-safety"),
               (4, "Managed Redis + embeddings", "cyan", "redis"), (6, "Key Vault / credential manager", "red", "key-vault"),
               (8, "Azure Monitor + App Insights", "violet", "monitor")]
        for idx, text, th_name, icon in sup:
            c = Chip(text, theme=th_name, size=15, icon=icon, fill="soft")
            cx = xs[idx - 1] + PW / 2
            c.place(cv, min(max(cx - c.w / 2, gw.ix), gw.ix + (W - 2 * pad) - c.w), chips_y)
            arrow(cv, [(cx, chips_y + c.h + 3), (cx, pipe_y - 5)], dash="dotted", sw=2, color=get_theme(th_name).stroke,
                  end_head=None)
        reg = Chip("Azure API Center: registry of models, MCP servers, A2A agents and skills", theme="grape", size=15,
                   icon="api-connections", fill="soft")
        reg.place(cv, gw.ix + (W - 2 * pad) - reg.w, gw.y + 28)
    # ---- backends
    by = gw.bottom + 150
    BH = 500
    # models
    MW, TW_, AW = 1560, 860, 680
    with cv.panel(0, by, w=MW, h=BH, title="Model backends", theme="blue", style="solid", fill="soft", pad=24, title_size=26,
                  sub_size=15, sub="same model and version on every pool member; deploy backends in the same regions as the gateways") as mp:
        with cv.panel(mp.ix, mp.iy, w=700, title="Foundry resource - region A", theme="blue", style="dotted", fill="none", pad=18,
                      title_size=20) as ra:
            ptu = Box(664, "Provisioned (PTU) deployment - primary", sub="priority 1: reserved capacity answers first",
                      icon="openai", icon_pos="left", theme="blue", h=100)
            ptu.place(cv, ra.ix, ra.iy)
            std = Box(664, "Standard (pay-as-you-go) deployment - spillover", sub="priority 2: same model and version, per-token overflow",
                      icon="openai", icon_pos="left", theme="blue", h=100, dash="dashed", fill="soft")
            std.place(cv, ra.ix, ptu.bottom + 82)
        rb = Box(692, "Foundry instance in region B", sub="another instance of the same model and version, reached through its own private endpoint",
                 icon="foundry", icon_pos="left", theme="blue", h=150)
        rb.place(cv, mp.ix + 800, mp.iy)
        oth = Box(692, "Non-Microsoft, self-hosted or Amazon Bedrock models", sub="OpenAI-compatible back ends behind one API; unified model API (preview)",
                      icon="ml", icon_pos="left", theme="blue", h=150, dash="dashed", fill="soft")
        oth.place(cv, mp.ix + 800, ra.bottom - 150)
    tx = MW + 50
    with cv.panel(tx, by, w=TW_, h=BH, title="Tool backends", theme="orange", style="solid", fill="soft", pad=24, title_size=26,
                  sub_size=15, sub="MCP tools only; policies apply to every operation exposed as a tool") as tp:
        m1 = Box(TW_ - 48, "MCP server from a REST API", sub="API operations become MCP tools", icon="mcp", icon_pos="left",
                 theme="orange", h=104)
        m1.place(cv, tp.ix, tp.iy)
        m2 = Box(TW_ - 48, "Existing MCP server", sub="for example LangChain / LangServe, Logic Apps or Functions", icon="mcp",
                 icon_pos="left", theme="orange", h=104)
        m2.place(cv, tp.ix, m1.bottom + 30)
        cx0 = tp.ix
        for text in ("Streamable HTTP /mcp", "SSE /sse + /messages (deprecated transport)"):
            c = Chip(text, theme="orange", size=15, fill="soft")
            c.place(cv, cx0, m2.bottom + 22)
            cx0 += c.w + 12
        N(TW_ - 48, "MCP tools only: no MCP resources or prompts, and not supported in API Management workspaces. Policies apply to "
                    "all operations exposed as tools (as of 2026-11-03).", kind="warn", size=14,
          src=[("MCP servers in API Management", S_MCP)]).place(cv, tp.ix, m2.bottom + 22 + 28 + 18)
    ax = tx + TW_ + 50
    with cv.panel(ax, by, w=AW, h=BH, title="Agent backends", theme="green", style="solid", fill="soft", pad=24, title_size=26,
                  sub_size=15, sub="A2A agent APIs managed in API Management") as ap:
        a1 = Box(AW - 48, "Foundry-hosted A2A agent", sub="exposed through the gateway; incoming A2A is preview (as of 2026-11-03)", icon="agent", icon_pos="left",
                 theme="green", h=104)
        a1.place(cv, ap.ix, ap.iy)
        a2 = Box(AW - 48, "Other A2A agent APIs", sub="governed with the same policies and subscriptions", icon="a2a", icon_pos="left",
                 theme="green", h=104, dash="dashed", fill="soft")
        a2.place(cv, ap.ix, a1.bottom + 30)
        N(AW - 48, "The Agent Landing Zone doesn't deploy the gateway for you: add one, then expose Foundry-hosted A2A agents through it.",
          kind="info", size=14, src=[("Agent Landing Zone configuration", "https://azure.github.io/AI-Landing-Zones/agent-landing-zone/configuration/")]
          ).place(cv, ap.ix, a2.bottom + 22)

    # ---- arrows gateway -> backends
    arrow(cv, [(MW / 2, gw.bottom + 4), (MW / 2, by - 6)], sw=3, num=6, num_theme="indigo", label_pos="right", label_size=15,
          label="route via the backend pool, then call with the managed identity (7)")
    arrow(cv, [(tx + TW_ / 2, gw.bottom + 4), (tx + TW_ / 2, by - 6)], sw=3, color="#e8590c", label_pos="right", label_size=15,
          label="MCP /mcp: REST API as MCP, or an existing server")
    arrow(cv, [(ax + AW / 2, gw.bottom + 4), (ax + AW / 2, by - 6)], sw=3, color="#2f9e44", label_pos="right", label_size=15,
          label="A2A agent APIs")
    connect(cv, ptu, std, a_side="bottom", b_side="top", dash="dashed", sw=3, color="#f08c00", num=8, num_theme="yellow",
            label="429 / 500 / 503: breaker trips, retry on the next backend", label_size=15, label_pos="right", label_wrap=270)
    connect(cv, ra, rb, a_side="right", b_side="left", ta=75 / ra.h, tb=0.5, dash="dashed", sw=3, color="#f08c00",
            label="cross-region", label_size=15)
    return by + BH + 70


# ====================================================================== 1b. observability, network, identity, steps
def _support(cv, y):
    wf = StepsCard(980, "Request path in ten steps (numbers match the diagram)", [
        (1, "Caller -> gateway: an OpenAI-compatible endpoint such as https://<apim>.azure-api.net/<api>/deployments/{name}/... "
            "(or the preview unified model API) with an APIM subscription key and/or an Entra JWT", "grape"),
        (2, "Authenticate (validate-azure-ad-token or key); resolve the product, access contract and Foundry project", "red"),
        (3, "Token limit (llm-token-limit, optional prompt-token precalculation): 429 on a TPM breach, 403 on a total-quota breach", "yellow"),
        (4, "Optional content-safety / PII screening (llm-content-safety; Citadel PII anonymisation)", "pink"),
        (5, "Optional semantic-cache lookup (embeddings + Azure Managed Redis): a hit returns immediately", "cyan"),
        (6, "Route through the backend pool (priority, weighted, round-robin or session-aware); the PTU primary goes first", "indigo"),
        (7, "Call the backend with the gateway's managed identity (least-privilege Azure RBAC on every instance)", "red"),
        (8, "On 429 / 500 / 503 the circuit breaker trips using Retry-After and the request is retried on the next backend "
            "(standard spillover, other region); same model + version required", "yellow"),
        (9, "Emit llm-emit-token-metric (custom dimensions) and token / prompt / completion logs to Azure Monitor; store in the cache", "violet"),
        (10, "Response to the caller; dashboards give chargeback / showback", "green"),
    ], theme_name="grape", icon="workflow", src=[("Gateway request flow and policies", S_CAP), ("Use a gateway in front of multiple model deployments", S_GW)])
    wf.place(cv, 0, y)

    px = wf.right + 40
    PWID = 740
    with cv.panel(px, y, w=PWID, title="Observability and chargeback", sub="one telemetry store for every consumed model", theme="violet",
                  style="solid", fill="soft", pad=20, title_size=24, sub_size=15) as ob:
        items = [
            ("Application Insights, Azure Monitor, Log Analytics", "gateway logs of tokens, prompts and completions; a built-in dashboard", "app-insights"),
            ("llm-emit-token-metric", "custom dimensions (client, team, model) are the chargeback key", "metrics"),
            ("Chargeback and showback", "usage per client across all deployments; instance logs can't tell clients apart without distinct Entra service principals", "cost-management"),
            ("Citadel usage pipeline", "Event Hub -> Logic App usage ingestion -> Cosmos DB analytics", "event-hubs"),
        ]
        cy = ob.iy + 2
        for lab, sub, ic in items:
            b = Box(PWID - 40, lab, sub=sub, icon=ic, icon_pos="left", theme="violet", h=88, size=17, sub_size=14)
            b.place(cv, ob.ix, cy)
            cy = b.bottom + 12
    nx = px + PWID + 40
    with cv.panel(nx, y, w=PWID, title="Network placement", sub="gateway in the hub VNet or a peered spoke", theme="indigo",
                  style="solid", fill="soft", pad=20, title_size=24, sub_size=15) as nw:
        items = [
            ("Hub VNet", "APIM subnet, private-endpoint subnet, agent subnet (delegated Microsoft.App/environments) and private DNS zones", "vnet"),
            ("Hub Azure Firewall", "inspects spoke-to-gateway traffic when the gateway is a dedicated spoke (part 2)", "firewall"),
            ("NSG on the private-endpoint subnet", "allows only the gateway; model endpoints are reachable only through it", "nsg"),
            ("Same region as the model host", "cross-region calls add latency and egress charges", "regions"),
        ]
        cy = nw.iy + 2
        for lab, sub, ic in items:
            b = Box(PWID - 40, lab, sub=sub, icon=ic, icon_pos="left", theme="indigo", h=88, size=17, sub_size=14)
            b.place(cv, nw.ix, cy)
            cy = b.bottom + 12
    ix = nx + PWID + 40
    idc = C(W - ix, "Identity and credentials", [
        "Terminate and re-establish credentials: the client is authorised at the gateway, the gateway is authorised to each instance by Azure RBAC",
        "Give the gateway's managed identity least-privilege RBAC on every instance, with equivalent permissions on all failover targets",
        "If you pass credentials through, make sure clients can't bypass the gateway or its model restrictions",
        "Credential manager (OAuth) handles outbound tokens for tool backends",
        "! The docs don't name the exact built-in role for the gateway identity (as of 2026-11-03)",
    ], theme="red", icon="managed-identity", src=[("Gateway service authorization", S_GW + "#service-authorization")])
    idc.place(cv, ix, y)
    ny = max(ob.bottom, nw.bottom, idc.bottom) + 24
    n1 = N(PWID, "Service faults, human configuration errors and complex routing logic all land on one component. Give API Management at "
                 "least 2 units across at least 2 availability zones (custom code: at least 3 instances).",
           kind="gotcha", title="The gateway can become the single point of failure", src=[("Gateway redundancy", S_GW + "#gateway-redundancy")])
    n1.place(cv, px, ny)
    n2 = N(PWID, "The default /status-0123456789abcdef mostly reflects the gateway instance, not your backends: add a dedicated health API. "
                 "Synthetic probes consume model capacity, so treat 429, 500 and 503 as circuit-break signals.",
           kind="gotcha", title="The status endpoint isn't backend health", src=[("Gateway health checks", S_GW + "#gateway-health-checks")])
    n2.place(cv, nx, ny)
    n3 = N(W - ix, "Honour Retry-After and don't keep hitting an endpoint that returns 429. Failover targets must run the same model and "
                   "version (never X -> X+1); use one deployment name everywhere to keep routes simple.",
           kind="warn", title="React to response codes, don't predict throttling", src=[("Gateway tips", S_GW + "#tips-for-the-multiple-instances-in-a-single-region-and-single-subscription-topology")])
    n3.place(cv, ix, ny)
    return max(wf.bottom, n1.bottom, n2.bottom, n3.bottom) + 70


# ====================================================================== 1c. policy and feature map
def _policy_map(cv, y):
    _, hb = section_header(cv, 0, y, "2  Policy and feature map: what the API Management AI gateway gives you", size=32,
                           sub="Capability by capability, with the policy or feature that delivers it (as of 2026-11-03)")
    y = hb + 36
    rows = [
        [("APIs managed", "gray"),
         "OpenAI Chat and Responses, Anthropic Messages (v2 tiers), Google Vertex; models in Foundry or Amazon Bedrock; remote MCP servers; A2A agent APIs; self-hosted models",
         "Unified model API (preview): one OpenAI-compatible endpoint with format translation"],
        [("Token governance", "yellow"),
         "llm-token-limit: TPM, or a quota over an hour, day, week, month or year. Counter key = subscription, IP or an expression; optional prompt-token precalculation (estimate-prompt-tokens)",
         "Foundry's UI exposes the same limits as TPM (429) and total quota (403). In a multi-region deployment each regional gateway counts tokens separately; counters are not aggregated"],
        [("Semantic caching", "cyan"),
         "llm-semantic-cache-lookup and llm-semantic-cache-store",
         "Needs Azure Managed Redis (or a RediSearch-compatible external cache) and an embeddings API. The docs give no savings figure; the benefit depends on repeated prompts"],
        [("Resilience", "indigo"),
         "Backend pool load balancer: round-robin, weighted, priority or session-aware. Circuit breaker with a Retry-After-driven trip duration",
         "A pool holds up to 30 backends; lower-priority groups are used only when every higher-priority backend has tripped. One breaker rule per backend; not in the Consumption tier. Same model and version across the pool"],
        [("Security", "red"),
         "Managed identity to backends; credential manager (OAuth); llm-content-safety; MCP security (inbound and outbound)",
         "Credentials terminate at the gateway; the gateway authenticates to each backend itself"],
        [("Observability", "violet"),
         "llm-emit-token-metric (custom dimensions); logging of tokens, prompts and completions to Azure Monitor; a built-in dashboard",
         "Supports chargeback and showback per client, team or model"],
        [("Developer experience", "grape"),
         "Azure API Center (registry for MCP servers and skills), developer portals, policy toolkit",
         "API Center also lists MCP servers hosted outside API Management"],
        [("Scaling", "blue"),
         "Scale units; multi-region gateways (Premium tier, classic)",
         "Deploy AI backends in the same regions as the gateways; autoscale applies to the primary region only, secondary regions scale manually"],
    ]
    t = Table([("Capability", 220), ("Feature or policy", 1280), "Notes"], rows, w=W, theme="grape", size=15, head_size=16,
              first_col_theme="grape")
    t.place(cv, 0, y)
    ly = t.bottom + 10
    x = 0
    for label, url in (("AI gateway capabilities in API Management", S_CAP), ("API Management backends (pools and circuit breaker)", S_BACKENDS),
                       ("Deploy API Management to multiple regions", S_MR), ("Reliability in API Management", S_APIM_REL)):
        tt = cv.text(x, ly, f"Learn: {label}", size=12, color=LINK, link=url)
        x += tt.w + 28
    return ly + 60


# ====================================================================== 2. topology gallery
def _mini_panel(cv, x, y, w, h, title, sub, th_name="gray", dash="dotted"):
    with cv.panel(x, y, w=w, h=h, title=title, sub=sub, theme=th_name, style=dash, fill="none", pad=18, title_size=22, sub_size=15):
        pass


def _node(cv, x, y, w, h, label, icon, th_name, *, sub=None, dash="solid", fill="solid", size=16, sub_size=13, icon_pos="top",
          icon_size=30):
    return Box(w, label, sub=sub, icon=icon, icon_pos=icon_pos, theme=th_name, h=h, dash=dash, fill=fill, size=size,
               sub_size=sub_size, icon_size=icon_size).place(cv, x, y)


def _frame(cv, x, y, w, h, title, th_name, *, icon=None, dash="dashed", fill="soft", title_size=17, center=False):
    th = get_theme(th_name)
    bg = "transparent" if fill == "none" else th.soft
    r = cv.rect(x, y, w, h, stroke=th.stroke, fill=bg, style="solid", sw=2, dash=dash)
    tx = x + 14
    if icon:
        place_icon(cv, icon, x + 10, y + 8, 28)
        tx = x + 46
    if center:
        tx = x + (w - metrics.text_size(title, title_size)[0]) / 2
    if title:
        cv.text(tx, y + 11, title, size=title_size, color=th.deep)
    return r


def _pe(cv, cx, cy, label="PE"):
    c = Chip(label, theme="indigo", size=14, icon="private-endpoint", fill="soft")
    c.place(cv, cx - c.w / 2, cy - c.h / 2)
    return c


def _wire(cv, a, b, *, passive=False, **kw):
    kw.setdefault("sw", 2.5)
    if passive:
        kw.setdefault("dash", "dashed")
        kw.setdefault("color", "#f08c00")
    return connect(cv, a, b, **kw)


MH = 420  # height of the T1-T3 mini diagrams


def _t1(cv, x, y):
    _mini_panel(cv, x, y, 1020, MH, "T1  Many deployments, one instance",
                "deployments: many  |  instances: 1  |  subscriptions: 1  |  regions: 1")
    ca = _node(cv, x + 24, y + 124, 150, 88, "Client A", "app", "gray")
    cb = _node(cv, x + 24, y + 248, 150, 88, "Client B", "app", "gray")
    g = _node(cv, x + 250, y + 160, 200, 130, "Gateway", "apim", "grape", sub="API Management")
    pe = _pe(cv, x + 540, y + 225)
    _frame(cv, x + 650, y + 100, 346, 280, "One Foundry instance", "blue", icon="foundry", dash="solid")
    deps = []
    for i, (lab, passive) in enumerate([("General-purpose model", False), ("Higher-capability model", False),
                                        ("Fine-tuned variant", False), ("New version (blue-green)", True)]):
        d = _node(cv, x + 674, y + 152 + i * 56, 298, 46, lab, None, "blue", dash="dashed" if passive else "solid",
                  fill="soft" if passive else "solid", size=15)
        deps.append((d, passive))
    _wire(cv, ca, g, a_side="right", b_side="left", tb=0.3)
    _wire(cv, cb, g, a_side="right", b_side="left", tb=0.7)
    _wire(cv, g, pe, a_side="right", b_side="left")
    for d, passive in deps:
        _wire(cv, pe, d, a_side="right", b_side="left", route="elbow", passive=passive)


def _t2(cv, x, y):
    _mini_panel(cv, x, y, 1020, MH, "T2  Many instances, one region, one subscription",
                "deployments: 1+  |  instances: many  |  subscriptions: 1  |  regions: 1")
    ca = _node(cv, x + 24, y + 136, 150, 88, "Client A", "app", "gray")
    cb = _node(cv, x + 24, y + 264, 150, 88, "Client B", "app", "gray")
    g = _node(cv, x + 250, y + 170, 200, 140, "Gateway", "apim", "grape", sub="retry + circuit breaker")
    _wire(cv, ca, g, a_side="right", b_side="left", tb=0.3)
    _wire(cv, cb, g, a_side="right", b_side="left", tb=0.7)
    for i, (lab, sub, passive) in enumerate([("Client A instance", "provisioned (PTU) - primary", False),
                                             ("Client A instance", "standard - spillover", True),
                                             ("Client B instance", "provisioned", False)]):
        yy = y + 104 + i * 104
        pe = _pe(cv, x + 540, yy + 42)
        inst = _node(cv, x + 640, yy, 356, 84, lab, "foundry", "blue", sub=sub, icon_pos="left", dash="dashed" if passive else "solid",
                     fill="soft" if passive else "solid")
        _wire(cv, g, pe, a_side="right", b_side="left", route="elbow", passive=passive)
        _wire(cv, pe, inst, a_side="right", b_side="left", passive=passive)


def _t3(cv, x, y):
    _mini_panel(cv, x, y, 1020, MH, "T3  Many instances, one region, many subscriptions",
                "deployments: 1+  |  instances: many  |  subscriptions: many  |  regions: 1")
    cl = _node(cv, x + 24, y + 196, 140, 88, "Client", "app", "gray")
    _frame(cv, x + 210, y + 104, 250, 250, "Gateway subscription", "grape")
    g = _node(cv, x + 232, y + 178, 206, 130, "Gateway", "apim", "grape", sub="own subscription")
    _wire(cv, cl, g, a_side="right", b_side="left")
    for i, s in enumerate("ABC"):
        yy = y + 100 + i * 104
        _frame(cv, x + 610, yy, 386, 94, f"Workload subscription {s}", "gray", title_size=16)
        inst = _node(cv, x + 628, yy + 32, 350, 54, "Foundry instance", "foundry", "blue", sub="own standard quota", icon_pos="left",
                     icon_size=26, size=15)
        pe = _pe(cv, x + 540, yy + 47)
        _wire(cv, g, pe, a_side="right", b_side="left", route="elbow")
        _wire(cv, pe, inst, a_side="right", b_side="left")
    cv.text(x + 210, y + 364, "private endpoints over cross-subscription Private Link (preferred) or hub transitive routing",
            size=14, color=MUTED, wrap=250)


def _t_col(cv, x, y, mini, why, adds, tips, notes, src):
    mini(cv, x, y)
    cy = y + MH + 20
    c1 = C(495, "Why you have it", why, theme="blue", src=src)
    c2 = C(495, "What the gateway adds", adds, theme="grape")
    _, b = row(cv, x, cy, [c1, c2], gap=30)
    c3 = C(1020, "Documented tips", tips, theme="gray")
    c3.place(cv, x, b + 20)
    cy = c3.bottom + 20
    for kind, title, text in notes:
        n = N(1020, text, kind=kind, title=title)
        n.place(cv, x, cy)
        cy = n.bottom + 16
    return cy


T4H = 700  # height of the T4 mini diagrams
PE_Y = 526  # private-endpoint row inside the T4 mini diagrams
FD_Y = 592  # foundry row inside the T4 mini diagrams


def _t4_panel(cv, x, y, title, sub, th_name):
    _mini_panel(cv, x, y, 740, T4H, title, sub, th_name)


def _cross_links(cv, g1, g2, pe1, pe2):
    """Own private endpoint solid, the other region's endpoint dashed (only two endpoints exist)."""
    _wire(cv, g1, pe1, a_side="bottom", b_side="top", ta=0.3, tb=0.3)
    _wire(cv, g2, pe2, a_side="bottom", b_side="top", ta=0.7, tb=0.3)
    _wire(cv, g1, pe2, a_side="bottom", b_side="top", ta=0.8, tb=0.78, passive=True)
    _wire(cv, g2, pe1, a_side="bottom", b_side="top", ta=0.2, tb=0.78, passive=True)


def _t4a(cv, x, y):
    _t4_panel(cv, x, y, "T4a  One gateway region", "API Management in one region, backends in two", "red")
    cl = _node(cv, x + 295, y + 88, 150, 72, "Client", "app", "gray")
    _frame(cv, x + 170, y + 226, 400, 196, "", "red", fill="none")
    cv.text(x + 392, y + 190, "global single point of failure", size=16, color="#c92a2a")
    g = _node(cv, x + 220, y + 282, 300, 104, "API Management", "apim", "grape", sub="single region")
    f1 = _node(cv, x + 40, y + FD_Y, 300, 70, "Foundry - region 1", "foundry", "blue", sub="active, the gateway's own region", icon_pos="left")
    f2 = _node(cv, x + 400, y + FD_Y, 300, 70, "Foundry - region 2", "foundry", "blue", sub="active, or a standard passive host",
               icon_pos="left")
    _wire(cv, cl, g, a_side="bottom", b_side="top")
    _wire(cv, g, f1, a_side="bottom", b_side="top", route="elbow", ta=0.3)
    _wire(cv, g, f2, a_side="bottom", b_side="top", route="elbow", ta=0.7, passive=True,
          label="cross-region: latency + egress", label_size=14, label_wrap=200, label_pos="left", label_t=0.8)


def _t4_multi(cv, x, y, title, sub, passive_hosts):
    """Shared drawing for T4b (active-active gateways) and T4c (plus active-passive model hosts)."""
    _t4_panel(cv, x, y, title, sub, "green")
    cl = _node(cv, x + 295, y + 84, 150, 68, "Client", "app", "gray")
    fq = _node(cv, x + 190, y + 206, 360, 76, "Built-in global FQDN", "dns", "indigo", sub="performance-based (lowest-latency) routing",
               icon_pos="left")
    _frame(cv, x + 30, y + 350, 680, 134, "One API Management instance", "green", dash="solid", center=True)
    g1 = _node(cv, x + 56, y + 394, 300, 70, "Gateway - region 1", "apim", "grape", icon_pos="left")
    g2 = _node(cv, x + 384, y + 394, 300, 70, "Gateway - region 2", "apim", "grape", icon_pos="left")
    pe1 = _pe(cv, g1.cx, y + PE_Y, "private endpoint")
    pe2 = _pe(cv, g2.cx, y + PE_Y, "private endpoint")
    sub_f = "provisioned active + standard passive" if passive_hosts else None
    f1 = _node(cv, x + 56, y + FD_Y, 300, 70, "Foundry - region 1", "foundry", "blue", sub=sub_f, icon_pos="left")
    f2 = _node(cv, x + 384, y + FD_Y, 300, 70, "Foundry - region 2", "foundry", "blue", sub=sub_f, icon_pos="left")
    if passive_hosts:
        _wire(cv, cl, fq, a_side="bottom", b_side="top")
        _wire(cv, fq, g1, a_side="bottom", b_side="top", route="elbow", ta=0.3, bend=0.3)
        _wire(cv, fq, g2, a_side="bottom", b_side="top", route="elbow", ta=0.7, bend=0.3)
        _cross_links(cv, g1, g2, pe1, pe2)
    else:
        _wire(cv, cl, fq, a_side="bottom", b_side="top", num=1, num_theme="green")
        _wire(cv, fq, g1, a_side="bottom", b_side="top", route="elbow", ta=0.3, bend=0.3)
        _wire(cv, fq, g2, a_side="bottom", b_side="top", route="elbow", ta=0.7, bend=0.3, passive=True, num=3, num_theme="red")
        cv.text(x + 556, y + 286, "region 1 down:\nnew calls go here", size=14, color="#c92a2a")
        _wire(cv, g1, pe1, a_side="bottom", b_side="top", num=2, num_theme="green")
        _wire(cv, g2, pe2, a_side="bottom", b_side="top")
    _wire(cv, pe1, f1, a_side="bottom", b_side="top")
    _wire(cv, pe2, f2, a_side="bottom", b_side="top")


def _t4b(cv, x, y):
    _t4_multi(cv, x, y, "T4b  Multi-region API Management", "replicated gateways, one control plane", False)


def _t4c(cv, x, y):
    _t4_multi(cv, x, y, "T4c  Multi-region + active-passive hosts", "each gateway can reach the other region", True)


def _t4d(cv, x, y):
    _t4_panel(cv, x, y, "T4d  Custom-coded gateway", "routing too complex for API Management policy", "gray")
    cl = _node(cv, x + 295, y + 88, 150, 72, "Client", "app", "gray")
    fr = _frame(cv, x + 30, y + 190, 680, 112, "Global router - choose one", "indigo", dash="dashed")
    _node(cv, x + 56, y + 232, 300, 62, "Azure Front Door", "front-door", "indigo", sub="WAF, public internet", icon_pos="left", icon_size=28)
    _node(cv, x + 384, y + 232, 300, 62, "Traffic Manager", "traffic-manager", "indigo", sub="no WAF, DNS TTL is enough", icon_pos="left",
          icon_size=28)
    g1 = _node(cv, x + 56, y + 372, 300, 100, "Custom gateway - region 1", "container-apps", "gray", sub="one highly available scale unit per region",
               icon_pos="left")
    g2 = _node(cv, x + 384, y + 372, 300, 100, "Custom gateway - region 2", "container-apps", "gray", sub="one highly available scale unit per region",
               icon_pos="left")
    pe1 = _pe(cv, g1.cx, y + PE_Y, "private endpoint")
    pe2 = _pe(cv, g2.cx, y + PE_Y, "private endpoint")
    f1 = _node(cv, x + 56, y + FD_Y, 300, 70, "Foundry - region 1", "foundry", "blue", sub="active + passive", icon_pos="left")
    f2 = _node(cv, x + 384, y + FD_Y, 300, 70, "Foundry - region 2", "foundry", "blue", sub="active + passive", icon_pos="left")
    _wire(cv, cl, fr, a_side="bottom", b_side="top")
    _wire(cv, fr, g1, a_side="bottom", b_side="top", ta=(g1.cx - fr.x) / fr.w)
    _wire(cv, fr, g2, a_side="bottom", b_side="top", ta=(g2.cx - fr.x) / fr.w)
    _cross_links(cv, g1, g2, pe1, pe2)
    _wire(cv, pe1, f1, a_side="bottom", b_side="top")
    _wire(cv, pe2, f2, a_side="bottom", b_side="top")


def _federated(cv, x, y):
    PWD, PHT = 2060, 470
    _mini_panel(cv, x, y, PWD, PHT, "Federated stamps - one isolated gateway per geopolitical boundary",
                "regions as in the Architecture Center residency example (East US, Germany West Central); a gateway per stamp follows its data-sovereignty guidance", "indigo",
                dash="dashed")
    for i, (name, who, region) in enumerate([("US stamp", "US clients", "East US"), ("Germany stamp", "German clients", "Germany West Central")]):
        sx = x + 36 + i * 1088
        _frame(cv, sx, y + 112, 900, 322, name + " - active-active or active-passive only inside the stamp", "grape", dash="solid")
        c = _node(cv, sx + 24, y + 214, 170, 100, who, "app", "gray")
        g = _node(cv, sx + 250, y + 204, 220, 120, "Gateway", "apim", "grape", sub="its own highly available instance")
        pe = _pe(cv, sx + 540, y + 264)
        f = _node(cv, sx + 610, y + 214, 270, 100, "Provisioned model", "foundry", "blue", icon_pos="left", sub="in " + region)
        _wire(cv, c, g, a_side="right", b_side="left")
        _wire(cv, g, pe, a_side="right", b_side="left")
        _wire(cv, pe, f, a_side="right", b_side="left")
    xx = x + PWD / 2
    cv.line((xx - 14, y + 238), (xx + 14, y + 278), stroke=RED, sw=6)
    cv.line((xx - 14, y + 278), (xx + 14, y + 238), stroke=RED, sw=6)
    cv.text(xx - 70, y + 296, "no cross-\nboundary calls", size=15, color="#c92a2a", align="center", w=140)
    return PWD, PHT


def _gallery(cv, y):
    _, hb = section_header(
        cv, 0, y, "3  Where does the gateway sit? The four Architecture Center topologies", size=32,
        sub="Add a gateway only when it earns its place. Solid arrows = active path, dashed orange = passive or spillover path, PE = private endpoint")
    y = hb + 36
    SRC1 = [("Multiple model deployments in a single instance", S_GW + "#multiple-model-deployments-in-a-single-instance")]
    SRC2 = [("Multiple instances in a single region and subscription", S_GW + "#multiple-instances-in-a-single-region-and-a-single-subscription")]
    SRC3 = [("Multiple instances across multiple subscriptions", S_GW + "#multiple-instances-in-a-single-region-across-multiple-subscriptions")]
    col_x = [0, 1090, 2180]
    ends = []
    ends.append(_t_col(cv, col_x[0], y, _t1, [
        "Different capabilities or fine-tuned variants behind one host",
        "Different versions for regression tests or blue-green rollouts",
        "Different TPM per deployment to throttle each client",
    ], [
        "Server-side routing: change the model without redeploying clients",
        "One entry point that identifies the client and picks the deployment, for example one per tenant",
        "Keys and Azure RBAC apply per instance, not per deployment: the gateway adds per-model segmentation",
        "Per-client usage for chargeback and showback; instance logs can't tell clients apart without distinct Entra service principals",
    ], [
        "Changing the model behind the gateway is a breaking change for clients: keep safe-deployment discipline",
        "API Management policy is usually enough, no custom code; keep OpenAI-style API and SDK compatibility",
        "Terminate and re-establish credentials: the client is authorised at the gateway, the gateway by Azure RBAC. If you pass credentials through, make sure clients can't bypass the gateway",
        "Same region as the model host; a subnet for the instance's private endpoint with an NSG that allows only the gateway",
    ], [("warn", "Reasons to avoid a gateway", "Skip it when controlling client configuration is as easy as gateway routing, or when separate host instances "
                                              "give stronger identity, network and billing segmentation.")], SRC1))
    ends.append(_t_col(cv, col_x[1], y, _t2, [
        "Security segmentation: keys or Azure RBAC per client",
        "Easy chargeback: a dedicated instance per client",
        "Failover for an instance outage, a network misconfiguration or a deleted deployment",
        "Quota failover: pair a provisioned instance with a standard instance for spillover",
    ], [
        "Retry and circuit breaking in one place, not in every client",
        "All backends treated as active-active: the same PTU model on several instances, load-balanced",
        "One telemetry store for every consumed model: unified dashboards and alerts",
        "Cost pattern: slightly under-provision the PTU instance and add a standard instance, so clients drain reserved throughput first and then spill over",
    ], [
        "Honour Retry-After: the built-in circuit breaker does on 429; don't keep hitting an endpoint that returns 429",
        "Don't predict throttling; react to HTTP response codes",
        "Same model and same version on every failover or round-robin target (never X -> X+1)",
        "Gateway in the same region, in a dedicated resource group (APIOps); all instance private endpoints in one subnet of the gateway VNet with an NSG for the gateway only",
        "Use the same deployment name on every instance to keep routes simple",
    ], [("gotcha", "Standard quota is per subscription", "Standard quotas are subscription level, not instance level: load balancing standard instances in one "
                                                           "subscription adds no throughput."),
        ("warn", "Reasons to avoid a gateway", "It doesn't improve chargeback here (a dedicated instance per client already does) and isn't needed with few "
                                              "clients you control. If the aim is capacity, evaluate data-zone capacity first.")], SRC2))
    ends.append(_t_col(cv, col_x[2], y, _t3, [
        "More standard quota while the models stay in one region (standard quota is per subscription)",
        "A central AI-as-a-service team",
    ], [
        "Everything from T2",
        "Hides the subscription boundary from clients while routing on availability or capacity",
    ], [
        "Same Microsoft Entra tenant everywhere",
        "Gateway in the same region, in its own subscription",
        "Reach the private endpoints through hub transitive routing or, preferred, cross-subscription Private Link connections",
    ], [("tip", "Global and Data Zone alternatives", "If you don't need to pin models to one region, use Global or Data Zone deployments instead. Global: processing in any "
                                                    "region with capacity, data at rest stays in the deployment's region. Data Zone: processing stays in a zone such as the EU."),
        ("warn", "Reasons to avoid a gateway", "Same as T2. Strict no-cross-border processing rules out one global gateway: use separate gateways per region or geography.")],
        SRC3))
    y = max(ends) + 56

    # ---- T4: across regions
    _, hb = section_header(
        cv, 0, y, "T4  Multiple instances across multiple regions: four ways to build the gateway", size=30,
        sub="Availability across paired regions, data residency and mixed-model availability. A single gateway region is a global single point of failure; "
            "treat each region as fully up or fully down")
    y = hb + 36
    xs = [0, 820, 1640, 2460]
    for fn, x in zip((_t4a, _t4b, _t4c, _t4d), xs):
        fn(cv, x, y)
    SRC4 = [("Multiple instances across multiple regions", S_GW + "#multiple-instances-across-multiple-regions")]
    cy = y + T4H + 20
    cols = [
        (["Simple; protects against a regional model-endpoint outage",
          "Active-active pool, or active-passive: traffic stays in the gateway's region unless that region's model host fails"],
         ["Global single point of failure: any gateway outage makes every region unreachable. Not for business-critical workloads",
          "Needs network line of sight across regions (peering or private endpoints); cross-region latency and egress charges",
          "Can't be used for data residency if a region spans a geopolitical boundary"], SRC4),
        (["No global traffic-handling single point of failure",
          "Policies are replicated; the built-in FQDN routes on lowest latency and around a failed region",
          "Supports DR drills: disable an individual regional gateway"],
         ["Control plane and developer portal stay in the primary region: a partial single point of failure",
          "Policies need conditional logic so each gateway calls same-region backends",
          "Survivors must absorb 100% of the traffic: over-provision PTU or add active-passive",
          "Clients must honour the DNS TTL and retry",
          "Premium tier (classic) per the multi-region page (as of 2026-11-03)"],
         [("Multi-region deployment", S_MR)]),
        (["Fails over from provisioned to standard, or across regions, without exposing errors to clients",
          "Keeps the performance-based FQDN",
          "Only two private endpoints: each region's endpoint is also the other gateway's passive target"],
         ["Same data-residency restriction across geopolitical boundaries",
          "Region status and routing logic live in policy: test failover regularly"],
         [("Active-active plus active-passive variant", S_GW + "#active-active-gateway-plus-active-passive-variant")]),
        (["Use when routing rules are too complex for API Management policy",
          "One highly available scale unit per region (at least 3 instances across zones)",
          "Can still be fronted by API Management for TLS, authentication, health and round-robin"],
         ["Behind Front Door make the gateway private-endpoint only and validate the X_AZURE_FDID header so it can't be bypassed",
          "Traffic Manager has no WAF; DNS TTL applies",
          "Per-region resource groups; for residency run an isolated stamp per geopolitical boundary"],
         [("Custom-coded gateway", S_GW + "#use-a-custom-coded-gateway")]),
    ]
    bottoms = []
    for (good, watch, src), x in zip(cols, xs):
        c1 = C(740, "Good for", ["+ " + g for g in good], theme="green", src=src)
        c1.place(cv, x, cy)
        c2 = C(740, "Watch out", ["! " + w for w in watch], theme="red")
        c2.place(cv, x, c1.bottom + 18)
        bottoms.append(c2.bottom)
    y = max(bottoms) + 50

    # ---- flow B + federated
    pw, ph = _federated(cv, 0, y)
    fl = StepsCard(W - pw - 40, "Multi-region request flow (T4b)", [
        (1, "The client resolves the built-in global FQDN and lands on the lowest-latency regional gateway", "green"),
        (2, "Policy conditional logic picks the same-region backend, through that region's private endpoint to its Foundry instance", "green"),
        (3, "On a regional failure FQDN routing steers new calls to a surviving region (honour the DNS TTL, retry on the client); "
            "survivors must absorb 100% of the traffic", "red"),
    ], theme_name="green", icon="regions", size=15,
        src=[("Multi-region API Management topology", S_GW + "#use-api-management-multi-region-deployment"), ("Deploy API Management to multiple regions", S_MR)])
    fl.place(cv, pw + 40, y)
    nr = N(W - pw - 40, "Treat each geopolitical boundary as an isolated stamp and apply active-active or active-passive only inside it. Block clients from other "
                        "geographies' endpoints; the gateway itself must never make a cross-geopolitical request. The most reliable way is a fully independent, "
                        "highly available gateway per geopolitical region.", kind="gotcha", title="Data residency", src=[("Data sovereignty", S_GW + "#data-sovereignty")])
    nr.place(cv, pw + 40, fl.bottom + 20)
    ng = N(pw, "Global deployments: data at rest stays in the deployment's region but inference may run in any hosting location. Data Zone deployments: inference stays "
               "inside the Microsoft-specified zone. Performance-based routing therefore needs scrutiny for sovereignty: for strict no-cross-border processing keep a separate "
               "gateway per region or geography.", kind="warn", title="Global and Data Zone do not change that", src=[("Data sovereignty", S_GW + "#data-sovereignty")])
    ng.place(cv, 0, y + ph + 20)
    return max(ng.bottom, nr.bottom) + 70


# ====================================================================== 3. cross-cutting recommendations
def _cross(cv, y):
    _, hb = section_header(cv, 0, y, "4  Cross-cutting recommendations for every topology", size=32,
                           sub="From the Architecture Center gateway guidance (as of 2026-11-03)")
    y = hb + 36
    gap = 40
    cw = (W - 3 * gap) / 4
    GEN = "#general-recommendations"
    cards = [
        C(cw, "Health checks", [
            "Assume instances are available; treat 429, 500 and 503 as circuit-break signals and honour Retry-After",
            "The default status endpoint reflects the gateway, not the backends: add a dedicated health API",
            "Synthetic probes consume model capacity",
        ], theme="yellow", icon="service-health", src=[("Gateway health checks", S_GW + "#gateway-health-checks")]),
        C(cw, "Safe deployment", [
            "Use the gateway to run blue-green or incremental rollouts of model versions and fine-tunes",
            "Define APIOps automation that matches how often backends and deployments change",
        ], theme="green", icon="devops", src=[("Safe deployment practices", S_GW + "#safe-deployment-practices")]),
        C(cw, "Just enough implementation", [
            "Don't add a new single point of failure or expose more models than intended through complex routing",
            "Human configuration mistakes in the gateway are a failure mode too",
        ], theme="gray", icon="gear", src=[("Just enough implementation", S_GW + "#just-enough-implementation")]),
        C(cw, "Data sovereignty", [
            "Treat geopolitical boundaries as isolated stamps",
            "Scrutinise performance-based routing; block clients from other geographies' endpoints",
        ], theme="indigo", icon="regions", src=[("Data sovereignty", S_GW + "#data-sovereignty")]),
        C(cw, "Service authorization", [
            "The gateway uses a managed identity with least-privilege Azure RBAC on every instance",
            "Give it equivalent permissions on all failover targets",
        ], theme="red", icon="managed-identity", src=[("Service authorization", S_GW + "#service-authorization")]),
        C(cw, "Azure Policy", [
            "Enforce consistency between instances and deployments with built-in AI-services policies",
            "Community custom policies exist for gaps the built-ins leave",
        ], theme="grape", icon="policy", src=[("Azure Policy", S_GW + "#azure-policy")]),
        C(cw, "Gateway redundancy", [
            "Choose regions with availability zones and spread the gateway across them",
            "API Management: at least 2 units across at least 2 zones",
            "Custom code: at least 3 instances, best-effort zone spread",
        ], theme="blue", icon="subnet", src=[("Gateway redundancy", S_GW + "#gateway-redundancy")]),
        C(cw, "Stateful chat and priority processing", [
            "Pin a stateful session (Assistants-style) to one backend with a cookie or session affinity",
            "When the pinned backend throttles, return 429 rather than silently re-routing to a backend with no history",
            "Priority processing lowers latency inside one deployment but adds no quota",
        ], theme="teal", icon="agent", src=[("Stateful interactions", S_GW + "#stateful-interactions")]),
    ]
    _, b = grid(cv, 0, y, cards, 4, gap_x=gap, gap_y=30)
    return b + 70


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _tower(cv, y)
    y = _support(cv, y)
    y = _policy_map(cv, y)
    y = _gallery(cv, y)
    y = _cross(cv, y)
    sources(cv, 0, y, [
        ("Use a gateway in front of multiple model deployments or instances", S_GW),
        ("Baseline Foundry chat reference architecture", S_BASE),
        ("AI gateway capabilities in API Management", S_CAP),
        ("MCP servers in API Management", S_MCP),
        ("Deploy API Management to multiple regions", S_MR),
        ("API Management backends: pools and circuit breaker", S_BACKENDS),
        ("Reliability in API Management", S_APIM_REL),
        ("Enable the AI gateway in Foundry", S_F_GW),
        ("Enforce token limits on model deployments", S_F_LIM),
        ("High availability and resiliency for Foundry", S_F_HA),
        ("AI Gateway Landing Zone (GitHub Pages, not Learn)", S_LZ_GW),
        ("Citadel Governance Hub, layer 1 (GitHub Pages, not Learn)", S_LZ_L1),
        ("Scaling with API Management: provisioned + standard spillover (GitHub)", S_AOAI_APIM),
        ("AI Gateway labs (GitHub)", S_LABS),
    ], w=W, cols=3)
