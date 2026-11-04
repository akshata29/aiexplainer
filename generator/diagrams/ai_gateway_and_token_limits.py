"""AI gateway (Azure API Management) in Foundry: request flow, token limits, MCP governance, bring-your-own-model."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="ai-gateway-and-token-limits", title="AI gateway and token limits", section="2", group="Control plane and cost",
    order=51,
    description="The Foundry AI gateway (Azure API Management): how it is enabled and billed, the request flow, 429/403 token limits per project and deployment, MCP governance and bring-your-own-model.",
    tags=["ai gateway", "api management", "token limits", "mcp governance", "byom", "quota"],
)

W = 3100
GAP = 44
COL = 480


def cw(n: int) -> int:
    """Width of n grid columns (480 px each, 44 px gaps)."""
    return n * COL + (n - 1) * GAP


# ====================================================================== local blocks
class Sticker(Rect2):
    """Status-code sticker: big code on the left, caption on the right."""

    def __init__(self, w, code, title, sub=None, *, theme="yellow", code_size=34, title_size=17, sub_size=14,
                 pad=12, code_w=96):
        self.th = get_theme(theme)
        self.w, self.code, self.code_size, self.pad, self.code_w = w, code, code_size, pad, code_w
        self.title_size, self.sub_size = title_size, sub_size
        inner = (w - code_w - 2 * pad) * 0.965
        self.t_lines = metrics.wrap_text(title, inner, title_size)
        self.s_lines = metrics.wrap_text(sub, inner, sub_size) if sub else []
        lh = metrics.line_ratio()
        self.text_h = len(self.t_lines) * title_size * lh + (len(self.s_lines) * sub_size * lh + 3 if sub else 0)
        self.h = max(2 * pad + self.text_h, 2 * pad + code_size * lh)
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="solid", sw=2)
            cw_, ch_ = metrics.text_size(self.code, self.code_size)
            cv.text(x, y + (H - ch_) / 2, self.code, size=self.code_size, color=th.deep, align="center", w=self.code_w)
            cv.line((x + self.code_w, y + 10), (x + self.code_w, y + H - 10), stroke=th.stroke, sw=1.5, dash="dashed")
            tx = x + self.code_w + self.pad
            ty = y + (H - self.text_h) / 2
            cv.text(tx, ty, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            if self.s_lines:
                ty += len(self.t_lines) * self.title_size * metrics.line_ratio() + 3
                cv.text(tx, ty, "\n".join(self.s_lines), size=self.sub_size, color=MUTED)
        cv.register(f"sticker:{self.code}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


class StepsCard(Rect2):
    """Card with numbered steps. steps: str or (heading, detail)."""

    def __init__(self, w, title, steps, *, theme="grape", icon=None, badge=None, src=(), size=15, pad=16, d=28,
                 gap=11, title_size=20, fill="hatch", start=1, sub=None):
        self.th = get_theme(theme)
        self.w, self.title, self.icon, self.badge, self.src = w, title, icon, badge, list(src)
        self.size, self.pad, self.d, self.gap, self.title_size, self.fill, self.start = size, pad, d, gap, title_size, fill, start
        self.sub = sub
        lh = metrics.line_ratio()
        inner = w - 2 * pad
        icon_off = 46 if icon else 0
        self.badge_w = 0.0
        if badge:
            from generator.xd.palette import STATUS
            self.badge_w = metrics.line_width(STATUS.get(badge, ("gray", badge))[1], 13) + 18
        self.icon_off = icon_off
        self.t_lines = metrics.wrap_text(title, (inner - icon_off - (self.badge_w + 8 if badge else 0)) * 0.965, title_size)
        h = pad + max(len(self.t_lines) * title_size * lh, 36 if icon else 0)
        self.sub_lines = []
        if sub:
            self.sub_lines = metrics.wrap_text(sub, (inner - icon_off) * 0.965, 14)
            h += 2 + len(self.sub_lines) * 14 * lh
        h += 12
        tw = (inner - d - 12) * 0.965
        self.items = []
        for s in steps:
            head, detail = (s if isinstance(s, tuple) else (None, s))
            hl = metrics.wrap_text(head, tw, size + 1) if head else []
            dl = metrics.wrap_text(detail, tw, size) if detail else []
            ih = max(len(hl) * (size + 1) * lh + len(dl) * size * lh, d)
            self.items.append((hl, dl, h, ih))
            h += ih + gap
        h -= gap
        self.src_lines = []
        if self.src:
            h += 10
            for label, url in self.src:
                lines = metrics.wrap_text(f"Learn: {label}", inner * 0.965, 12)
                self.src_lines.append(("\n".join(lines), url, h))
                h += len(lines) * 12 * lh + 2
            h -= 2
        self.h = h + pad
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        from generator.xd.blocks import draw_badge
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, lh = self.th, self.pad, metrics.line_ratio()
        bg, fs = (th.fill, "hachure") if self.fill == "hatch" else (th.soft, "solid")
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=2)
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, 36)
            cv.text(x + pad + self.icon_off, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            if self.sub_lines:
                cv.text(x + pad + self.icon_off, y + pad + len(self.t_lines) * self.title_size * lh + 2,
                        "\n".join(self.sub_lines), size=14, color=MUTED)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.badge_w, y + pad - 1, self.badge)
            for i, (hl, dl, oy, ih) in enumerate(self.items):
                numbered(cv, x + pad + self.d / 2, y + oy + self.d / 2, self.start + i, theme=th.name, d=self.d, size=16)
                tx, ty = x + pad + self.d + 12, y + oy
                if hl:
                    cv.text(tx, ty, "\n".join(hl), size=self.size + 1, color=th.deep)
                    ty += len(hl) * (self.size + 1) * lh
                if dl:
                    cv.text(tx, ty, "\n".join(dl), size=self.size, color=INK)
            for txt, url, oy in self.src_lines:
                cv.text(x + pad, y + oy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


def L(path: str) -> str:
    return learn(path)


def A(path: str) -> str:
    """Learn pages outside /azure/foundry (API Management etc.)."""
    return learn(path, base="")


def hconn(cv, a, b, y, *, rtl=False, **kw):
    """Horizontal connector at absolute height y between the facing sides of a and b."""
    ta, tb = (y - a.y) / a.h, (y - b.y) / b.h
    if rtl:
        return connect(cv, a, b, a_side="left", b_side="right", ta=ta, tb=tb, **kw)
    return connect(cv, a, b, a_side="right", b_side="left", ta=ta, tb=tb, **kw)


# ====================================================================== canvas
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "AI gateway and token limits",
        "Azure API Management as the governed front door to Foundry models and tools - limits per project and deployment (Preview, as of 2026-11-03)",
        w=W)
    y = bottom + 40

    # ------------------------------------------------------------------ summary strip
    en_src = ("Configure AI Gateway", learn("configuration/enable-ai-api-management-gateway-portal"))
    tw = (W - 4 * 45) // 5
    tiles = [
        Card(tw, "What it is", [
            "= An Azure API Management (APIM) v2 instance linked to your Foundry resource. Once a project is added, its calls to models and tools flow through it."],
             theme="grape", icon="apim", icon_size=44, src=[en_src]),
        Card(tw, "What it enforces", [
            "= Per project and deployment: a tokens-per-minute (TPM) limit answers 429; a total token quota per hour, day, week, month or year answers 403."],
             theme="yellow", icon="quotas", icon_size=44,
             src=[("Enforce token limits", learn("control-plane/how-to-enforce-limits-models"))]),
        Card(tw, "How it is scoped", [
            "= One gateway per Foundry resource, shared by every project in it. Each project keeps its own limits. Need strict isolation? Use separate Foundry resources."],
             theme="grape", icon="foundry", icon_size=44, src=[en_src]),
        Card(tw, "What it costs", [
            "= It is a real APIM instance, billed until you delete it. Removing a project from the gateway does not stop the charges."],
             theme="yellow", icon="cost-management", icon_size=44, src=[en_src]),
        Card(tw, "Status (as of 2026-11-03)", [
            "= Manage > AI Gateway is Preview. MCP tools governance is Preview. Legacy custom-agent registration through an APIM proxy is deprecated, scheduled Apr 30, 2027."],
             theme="orange", icon="preview-features", icon_size=44, badge="preview",
             src=[("General availability", learn("concepts/general-availability"))]),
    ]
    s_right, s_bottom = row(cv, 0, y, tiles, gap=45)

    # ------------------------------------------------------------------ 1. inbound flow
    y1 = s_bottom + 64
    _, hb = section_header(cv, 0, y1, "1  Inbound: the AI gateway sits in front of Foundry models and tools",
                           sub="Foundry (new) portal > Manage > AI Gateway. The numbered steps are explained in the card on the right.", size=32)
    legend(cv, 1700, y1 + 20, [("Request path", "grape"), ("Response", "blue"), ("At a limit (429 / 403)", "yellow"),
                               ("Bypass: no gateway", "red")], size=16)
    ptop = hb + 120

    with cv.panel(0, ptop, w=380, title="Callers", sub="use the project's gateway URL and key", theme="gray",
                  style="dotted", pad=22, title_size=24, sub_size=14) as pc:
        b_app = Box(336, "Applications and SDK clients", sub="call a model deployment", theme="gray", icon="app",
                    icon_pos="left", h=84)
        b_ag = Box(336, "Agents with a governed MCP tool", sub="tool calls go to the gateway URL", theme="gray",
                   icon="agent", icon_pos="left", h=84)
        b_app.place(cv, pc.ix, pc.iy)
        b_ag.place(cv, pc.ix, b_app.bottom + 22)
        lab_y = b_ag.bottom + 40
        cv.text(pc.ix, lab_y, "At a limit the gateway answers itself:", size=15, color=MUTED)
        s429 = Sticker(336, "429", "Too Many Requests", "tokens-per-minute (TPM) limit exceeded", theme="yellow")
        s403 = Sticker(336, "403", "Forbidden", "token quota for the period exceeded", theme="yellow")
        s429.place(cv, pc.ix, lab_y + 30)
        s403.place(cv, pc.ix, s429.bottom + 16)

    GX, GW = 490, 1440
    with cv.panel(GX, ptop, w=GW, title="AI gateway = one Azure API Management (v2) instance per Foundry resource",
                  sub="every project added to it shares the instance; each project has its own limits",
                  theme="grape", style="solid", fill="soft", pad=26, title_size=26, sub_size=15) as gw:
        iw = GW - 52
        py = gw.iy + 4
        cv.text(gw.ix, py, "What the gateway does to each request", size=17, color=get_theme("grape").deep)
        py += 30
        bw = (iw - 3 * 40) / 4
        stages = [
            Box(bw, "Identify the caller", sub="project gateway URL + project key", theme="grape", h=96),
            Box(bw, "Apply token limits", sub="TPM limit -> 429 | token quota -> 403", theme="yellow", h=96),
            Box(bw, "Forward to the backend", sub="model deployment or governed MCP tool", theme="grape", h=96),
            Box(bw, "Count tokens and log", sub="prompt + completion tokens; APIM metrics and logs", theme="violet", h=96),
        ]
        for i, s in enumerate(stages):
            s.place(cv, gw.ix + i * (bw + 40), py)
        for a, b in zip(stages, stages[1:]):
            connect(cv, a, b, gap=4)
        ly = py + 96 + 34
        cv.text(gw.ix, ly, "Projects in the gateway (illustrative; you choose the values)", size=17,
                color=get_theme("green").deep)
        ly += 30

        def lane(y_, title, sub, chips, theme="green", style="dashed"):
            with cv.panel(gw.ix, y_, w=iw, title=title, sub=sub, theme=theme, style=style, fill="none", pad=16,
                          title_size=22, sub_size=14) as ln:
                cx = ln.ix
                for ch in chips:
                    ch.place(cv, cx, ln.iy + 2)
                    cx += ch.w + 12
            return ln

        la = lane(ly, "Project A", "its own TPM limit and token quota for each deployment", [
            Chip("Gateway status: Enabled", theme="green", size=15),
            Chip("Gateway URL + key for this project", theme="grape", size=15),
            Chip("TPM limit per deployment -> 429", theme="yellow", size=15),
            Chip("Token quota per period -> 403", theme="yellow", size=15)])
        lb = lane(la.bottom + 16, "Project B", "same gateway, different limits: one project cannot monopolise capacity", [
            Chip("Gateway status: Enabled", theme="green", size=15),
            Chip("Gateway URL + key for this project", theme="grape", size=15),
            Chip("TPM limit per deployment -> 429", theme="yellow", size=15),
            Chip("Token quota per period -> 403", theme="yellow", size=15)])
        lc = lane(lb.bottom + 16, "Project C (existing project, not added yet)",
                  "new projects are enabled by default; older ones need Add project to gateway", [
                      Chip("Gateway status: Disabled", theme="gray", size=15, dash="dashed"),
                      Chip("No gateway limits apply", theme="red", size=15),
                      Chip("Its calls bypass the gateway", theme="red", size=15)], theme="gray", style="dashed")
    numbered(cv, stages[1].x + 6, stages[1].y + 6, 2, theme="yellow")

    BX = GX + GW + 110
    with cv.panel(BX, ptop, w=400, title="What it fronts", theme="gray", style="dotted", pad=22, title_size=24) as pb:
        k_model = Card(356, "Model deployments", ["Each project's deployments; limits are set per project x deployment"],
                       theme="blue", icon="openai")
        k_mcp = Card(356, "MCP servers", ["New MCP tools created in the Foundry portal, without managed OAuth"],
                     theme="orange", icon="mcp", badge="preview")
        k_cust = Card(356, "Custom agents (legacy)", ["APIM proxy gives Block / Unblock",
                                                      "Deprecated: scheduled Apr 30, 2027 (as of 2026-11-03); no new adds"],
                      theme="gray", icon="agent", badge="retiring", dash="dashed")
        col(cv, pb.ix, pb.iy, [k_model, k_mcp, k_cust], gap=20)

    logs = Box(820, "APIM metrics and gateway logs", theme="violet", icon="log-analytics", icon_pos="left", h=92,
               sub="Monitoring > Metrics > Requests; diagnostic setting -> Log Analytics (ApiManagementGatewayLogs)")
    logs.place(cv, GX + (GW - 820) / 2, gw.bottom + 70)

    # arrows ---------------------------------------------------------
    hconn(cv, b_app, gw, b_app.cy, num=1, num_theme="grape", color="#862e9c", sw=3)
    hconn(cv, b_ag, gw, b_ag.cy, color="#862e9c", sw=3)
    hconn(cv, gw, s429, s429.cy, rtl=True, dash="dashed", color="#e67700", sw=3, num=5, num_theme="yellow")
    hconn(cv, gw, s403, s403.cy, rtl=True, dash="dashed", color="#e67700", sw=3)
    hconn(cv, gw, k_model, k_model.cy - 26, num=3, num_theme="grape", color="#862e9c", sw=3)
    hconn(cv, k_model, gw, k_model.cy + 26, rtl=True, dash="dashed", num=4, num_theme="blue", color="#1971c2", sw=3)
    hconn(cv, gw, k_mcp, k_mcp.cy, color="#862e9c", sw=3)
    hconn(cv, gw, k_cust, k_cust.cy, color="#868e96", sw=2, dash="dashed")
    connect(cv, gw, logs, a_side="bottom", b_side="top", num=6, num_theme="violet", color="#5f3dc4", sw=3)
    arrow(cv, [(pc.cx, ptop - 4), (pc.cx, ptop - 56), (pb.cx, ptop - 56), (pb.cx, ptop - 4)], dash="dashed",
          color="#e03131", sw=3, label="Project C was never added, so its calls bypass the gateway: no limits and no gateway logs",
          label_size=16, label_color="#c92a2a", label_t=0.5)

    steps = StepsCard(600, "Request path, step by step", [
        ("Call", "The caller sends the request to the project's gateway URL with the project's gateway key."),
        ("Check", "The gateway applies that project's TPM limit and token quota for the deployment."),
        ("Forward", "Within limits, the request goes on to the model deployment (or governed MCP tool)."),
        ("Return", "The response comes back through the gateway; prompt + completion tokens are counted."),
        ("At a limit", "The gateway answers itself: 429 over the TPM limit, 403 over the token quota."),
        ("Observe", "Requests show in APIM Monitoring > Metrics and, with a diagnostic setting, in Log Analytics."),
    ], theme="grape", icon="apim",
        src=[("Configure AI Gateway", learn("configuration/enable-ai-api-management-gateway-portal")),
             ("Enforce token limits", learn("control-plane/how-to-enforce-limits-models"))])
    steps.place(cv, BX + 400 + 60, ptop)
    n_conc = Note(600, "If many requests arrive at once, token use can briefly exceed the configured limits until the responses are processed. New limits apply immediately to later requests.",
                  kind="gotcha", title="Concurrency overshoot")
    n_conc.place(cv, steps.x, steps.bottom + 24)

    y_end = max(logs.bottom, steps.bottom, n_conc.bottom, pc.bottom)

    # ------------------------------------------------------------------ 2. what is enforced, where it is set
    y2 = y_end + 70
    _, hb2 = section_header(cv, 0, y2, "2  What the gateway enforces - and where you set each control",
                            sub="Only tier 1 is configured in the Foundry portal; the rest is Azure API Management, set in the Azure portal",
                            size=32)
    ty = hb2 + 36

    def src_cell(label, url):
        return dict(text="Learn: " + label, link=url, color=LINK)

    t_pol = Table(
        [("Tier of evidence", 250), ("What it can do", 940), ("Where you set it", 430), ("Source", 432)],
        [
            [("1  Foundry portal", "grape"),
             "Per-project TPM limit and total token quota for each deployment; add or remove a project; create a gateway or pick an APIM instance.",
             "Foundry (new) > Manage > AI Gateway",
             src_cell("Enforce token limits", L("control-plane/how-to-enforce-limits-models"))],
            [("2  Foundry docs: policies for MCP tools (Preview)", "orange"),
             "rate-limit-by-key (doc example: 60 calls per 60 s keyed by caller IP); ip-filter allow-list; X-Correlation-Id set from context.RequestId; delete Cookie and Referer headers (never Authorization); route by header with set-backend-service.",
             "Azure portal > API Management > policies - not the Foundry portal",
             src_cell("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))],
            [("3  Foundry docs: identity for bring-your-own-model", "blue"),
             "validate-azure-ad-token with the connection's Audience and the managed identity's client ID, so your APIM accepts the Foundry project's identity.",
             "Azure portal > APIM inbound policy",
             src_cell("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))],
            [("4  Foundry resilience guidance", "indigo"),
             "'Generative AI Gateway' reverse proxy in front of model endpoints: load balancing, circuit breaker, rate limiting and throttling, central logging, priority routing for mission-critical apps; multi-region APIM with Azure Front Door; an enterprise PTU pool behind APIM.",
             "APIM - you design and run it",
             src_cell("High availability and resiliency", L("how-to/high-availability-resiliency"))],
            [("5  APIM docs (generic) - not configurable from the Foundry portal", "gray"),
             "llm-token-limit (rate and/or quota on any counter key); semantic caching (llm-semantic-cache-lookup and -store with Azure Managed Redis or a RediSearch-compatible cache); backend load balancer (round-robin, weighted, priority-based, session-aware); circuit breaker (trip duration from Retry-After); llm-content-safety; llm-emit-token-metric; log prompts and completions to Azure Monitor; managed identity to backends; OAuth credential manager; REST APIs as MCP servers; A2A agent APIs; unified model API (preview); API Center catalog.",
             "APIM only",
             src_cell("AI gateway capabilities in API Management", A("azure/api-management/genai-gateway-capabilities"))],
        ], w=cw(4), theme="grape", size=14, head_size=15, title="Four tiers of evidence: what is wired into Foundry and what is plain APIM", title_size=22)
    t_pol.place(cv, 0, ty)

    rules = Card(cw(2), "Token counting rules (APIM llm-token-limit policy)", [
        "= Foundry's page links to this policy for details but does not spell out the portal's internals - read these as APIM-documented behaviour.",
        "Counts prompt + completion tokens only",
        "Over the rate limit: 429. Over the quota: 403",
        "Quota windows are fixed: the window starts at the UTC timestamp truncated to the period",
        "estimate-prompt-tokens true: pre-counts the prompt (fewer wasted backend calls, may cost performance). False: uses actual usage from the response, so a prompt can still be sent when over the limit",
        "Streaming: prompt tokens are always estimated, completion tokens too",
        "Images are over-counted as up to 1,200 tokens each when estimating or streaming",
        "Counters are per gateway: regional and workspace gateways do not aggregate",
        "v2 tiers use a token bucket (classic: sliding window) - keep tokens-per-minute consistent when one key is used at several scopes",
    ], theme="yellow", icon="quotas", src=[("llm-token-limit policy", A("azure/api-management/llm-token-limit-policy"))])
    rules.place(cv, t_pol.right + GAP, ty)

    ys = max(t_pol.bottom, rules.bottom) + 50
    with cv.panel(0, ys, w=cw(4), title="Limit stack: how the layers compose", theme="gray", style="dashed", pad=22,
                  title_size=24, sub="our synthesis from the pages cited - the docs do not draw one combined stack",
                  sub_size=15) as ls:
        t_stack = Table(
            [("Layer", 340), ("Scope", 530), ("Unit", 380), ("Over the limit", 260), ("Set in", 498)],
            [
                [("Foundry quota (deployment rate limits)", "yellow"), "subscription x region x model, split across deployments",
                 "TPM per deployment (RPM is proportional)", "429", "Manage > Quota (GA)"],
                [("Gateway TPM limit", "yellow"), "project x deployment", "tokens per minute", "429",
                 "Manage > AI Gateway > Token management"],
                [("Gateway token quota", "yellow"), "project x deployment", "tokens per hour, day, week, month or year",
                 "403", "Manage > AI Gateway > Token management"],
                [("APIM llm-token-limit (your own policy)", "yellow"), "any counter key x policy scope",
                 "prompt + completion tokens", "429 / 403", "APIM, in the Azure portal"],
                [("Budget", "yellow"), "subscription, resource group or filter", "currency",
                 "alert only - no hard stop", "Cost Management"],
            ], w=cw(4) - 44, theme="yellow", size=14, head_size=15)
        t_stack.place(cv, ls.ix, ls.iy)
        lx_ = ls.ix
        for lab, url in (("Foundry quota", L("how-to/quota")), ("Enforce token limits", L("control-plane/how-to-enforce-limits-models")),
                         ("Plan and manage costs", L("concepts/manage-costs"))):
            t_ = cv.text(lx_, t_stack.bottom + 10, "Learn: " + lab, size=12, color=LINK, link=url)
            lx_ += t_.w + 26
    n_agent = Note(cw(2), "Learn defines limits per project x deployment only. An Ignite 2025 speaker (BRK202) said limits can be set 'either per project or per agents' - video-sourced, unverified, so the diagram draws per project. 'Per team' is our reading: model a team as a project, or give it its own Foundry resource.",
                   kind="warn", title="Per agent or per team? Not in Learn")
    n_agent.place(cv, ls.right + GAP, ys)
    n_tool = Note(cw(2), "TPM limits and token quotas are the only limits set in the Foundry portal. Rate limits, IP filters and header rules for MCP tools are APIM policies, applied in the Azure portal.",
                  kind="info", title="Two places to configure")
    n_tool.place(cv, ls.right + GAP, n_agent.bottom + 22)
    y_end = max(ls.bottom, n_tool.bottom)

    # ------------------------------------------------------------------ 3. turn it on, set limits, turn it off
    y3 = y_end + 70
    _, hb3 = section_header(cv, 0, y3, "3  Turn it on, set limits, turn it off",
                            sub="Foundry (new) portal > Manage > AI Gateway - the click path first, then roles, eligibility and what 'off' really means",
                            size=32)
    cy0 = hb3 + 46
    chain = [
        ("Add AI Gateway", "Manage > AI Gateway > Add AI Gateway, then pick the Foundry resource", "grape"),
        ("Create new or use existing", "Create new = Basic v2 (dev/test, with SLA). Use existing = a v2 instance in the same tenant and subscription", "grape"),
        ("Name it, then Add", "Status shows Provisioning, then Enabled. Basic v2 typically provisions in 5-10 minutes", "grape"),
        ("Add existing projects", "New projects are enabled by default. Older ones: open the gateway > Add project to gateway", "grape"),
        ("Set token limits", "Gateway > Token management > + Set limit > project + deployment > Limit (tokens per minute) > Create", "yellow"),
        ("Verify", "Call through the project's gateway URL + key: 429 at the TPM limit, 403 at the quota. APIM > Monitoring > Metrics > Requests", "violet"),
    ]
    bw3 = 440
    gap3 = (W - 6 * bw3) / 5
    cboxes = [Box(bw3, t, sub=s, theme=th, h=124, size=18, sub_size=15) for t, s, th in chain]
    for i, b in enumerate(cboxes):
        b.place(cv, i * (bw3 + gap3), cy0)
    for a, b in zip(cboxes, cboxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=5)
    for i, (b, c) in enumerate(zip(cboxes, chain)):
        numbered(cv, b.x + 24, b.y + 2, i + 1, theme=c[2])
    r3 = cboxes[0].bottom + 54

    t_roles = Table(
        [("You want to", 400), ("Role needed", 380), ("On", 224)],
        [
            ["Create the APIM instance (Create new)", "Contributor or Owner", "Target resource group (or subscription)"],
            ["Use an existing APIM, add a project, set limits, apply policies", "API Management Service Contributor (or Owner)", "The APIM instance"],
            ["Open Manage > AI Gateway for a Foundry resource", "Foundry Account Owner or Foundry Owner (the doc's example)", "The Foundry resource"],
        ], w=cw(2), theme="red", size=14, head_size=15, title="Roles you need", title_size=22)
    t_roles.place(cv, 0, r3)
    n_roles = Note(cw(2), "Foundry roles were renamed (Azure AI User / Owner / Account Owner / Project Manager became Foundry User / Owner / Account Owner / Project Manager). Old names can still show up in places; role IDs are unchanged.",
                   kind="info", title="Role names")
    n_roles.place(cv, 0, t_roles.bottom + 22)
    ver = Card(cw(2), "Verify it is working", [
        "APIM > Monitoring > Metrics > Requests: the count rises after a test call to a model deployment in an enabled project",
        "APIM > Monitoring > Diagnostic settings > Add: Logs related to ApiManagement Gateway -> Log Analytics, Resource specific table",
        "Query ApiManagementGatewayLogs | where TimeGenerated > ago(1h) and look for 200s with your gateway's API name",
        "Exceed the TPM limit to see 429; exhaust the quota to see 403",
    ], theme="violet", icon="log-analytics", src=[("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal"))])
    ver.place(cv, 0, n_roles.bottom + 22)

    elig = Card(cw(2), "Which APIM instance can you use?", [
        "Create new: a Basic v2 instance - dev/test with SLA support",
        "Use existing: same Entra tenant AND same subscription as the Foundry resource, a v2 tier, visible to the portal, and you hold API Management Service Contributor or Owner",
        "Classic tiers (Developer, Basic, Standard, Premium) are not listed - the instance must be a v2 tier",
        "Production or higher throughput: consider an existing Standard v2 or Premium v2 instance",
        "Private Foundry resource (public access disabled): APIM must be private too - Standard v2 or Premium v2 with a private endpoint, or Premium v2 injected in a virtual network",
        "! A gateway created in the Foundry portal for a private Foundry resource is automatically public; to complete data-plane actions, network-isolate it in the Azure portal",
    ], theme="grape", icon="apim", src=[("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal")),
                                         ("Configure network isolation", L("how-to/configure-private-link"))])
    elig.place(cv, cw(2) + GAP, r3)

    lx = 2 * (cw(2) + GAP)
    with cv.panel(lx, r3, w=cw(2), title="Disable is not delete", sub="and only deleting the APIM instance stops the charges", theme="yellow",
                  style="dashed", fill="none", pad=22, title_size=24, sub_size=15) as lp:
        s1 = Box(470, "Project routes through the gateway", sub="Gateway status: Enabled", theme="green", h=78)
        s2 = Box(470, "Project disabled", sub="Gateway status: Disabled. The gateway and its APIM instance keep running for other projects - and keep billing",
                 theme="yellow", h=104)
        s3 = Box(470, "APIM instance deleted", sub="Charges stop. Check that no other workload uses the instance first", theme="green", h=92)
        s1.place(cv, lp.ix, lp.iy + 4)
        s2.place(cv, lp.ix, s1.bottom + 62)
        s3.place(cv, lp.ix, s2.bottom + 86)
        connect(cv, s1, s2, a_side="bottom", b_side="top", sw=3, label="Remove project from gateway", label_size=15,
                label_wrap=400, gap=4)
        connect(cv, s2, s3, a_side="bottom", b_side="top", sw=3, gap=4,
                label="Disable every project, delete the gateway in the Foundry resource, then delete the APIM instance with the same name in the Azure portal",
                label_size=15, label_wrap=400)
    y_end = max(ver.bottom, elig.bottom, lp.bottom)

    # ------------------------------------------------------------------ 4. MCP tools governance
    y4 = y_end + 70
    _, hb4 = section_header(cv, 0, y4, "4  Govern MCP tools through the gateway (Preview)",
                            sub="Route MCP traffic through the gateway to enforce authentication, rate limits, IP restrictions and audit logging - without changing MCP servers or agent code",
                            size=32)
    my = hb4 + 40
    mw = cw(4)
    lim = Card(cw(2), "Limitations (as of 2026-11-03)", [
        "! Only MCP tools: SharePoint, code-first MCP, managed-OAuth and OpenAPI tools are not supported",
        "! Routing is applied only when a tool is created - existing tools are not mediated; re-create them after connecting the gateway",
        "! Only new MCP tools created in the Foundry portal that do not use managed OAuth are routed",
        "! The gateway does not log tool traces - use APIM logs and metrics plus your MCP server's own logs",
        "! Policies can be applied in the Azure portal only, not in the Foundry portal",
    ], theme="red", icon="mcp", badge="preview", src=[("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))])
    ben = Card(cw(2), "Key benefits (per the doc)", [
        "Secure routing for all new MCP tools through a gateway endpoint",
        "Consistent access control and authentication enforcement",
        "Centralised observability for gateway traffic (logs and metrics)",
        "Unified policies for throttling, IP restrictions and routing",
        "Reuse of tools through public and private catalogs",
    ], theme="orange", icon="toolbox-icon", src=[("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))])
    with cv.panel(0, my, w=mw, title="MCP traffic through the gateway", sub="applies to new MCP tools created in the Foundry portal that do not use managed OAuth",
                  theme="orange", style="dotted", fill="none", pad=24, title_size=24, sub_size=15,
                  min_h=lim.h + ben.h + 22) as mp:
        nw = 520
        gap_n = (mw - 48 - 3 * nw) / 2
        ny = mp.iy + 84
        n1 = Box(nw, "Agent", sub="adds an MCP tool: Tools > Catalog, or Build > Tools > Custom > Model Context Protocol (paste endpoint + auth type)",
                 theme="green", icon="agent", icon_pos="left", h=124)
        n2 = Box(nw, "AI gateway (APIM)", sub="the tool's endpoint shows https://<your-apim>.azure-api.net/mcp/... instead of the MCP server URL",
                 theme="grape", icon="apim", icon_pos="left", h=124)
        n3 = Box(nw, "MCP server", sub="auth: managed identity (Entra), key-based, custom OAuth identity passthrough, or unauthenticated",
                 theme="orange", icon="mcp", icon_pos="left", h=124)
        for i, n in enumerate((n1, n2, n3)):
            n.place(cv, mp.ix + i * (nw + gap_n), ny)
        connect(cv, n1, n2, a_side="right", b_side="left", sw=3, label="tool call", label_size=15, gap=5)
        connect(cv, n2, n3, a_side="right", b_side="left", sw=3, label="forwarded after policies", label_size=15,
                label_wrap=150, gap=5)
        arrow(cv, [(n1.cx, ny - 4), (n1.cx, ny - 40), (n3.cx, ny - 40), (n3.cx, ny - 4)], dash="dashed", color="#e03131",
              sw=3, label="Existing tools and managed-OAuth tools call the MCP server directly - not governed",
              label_size=15, label_color="#c92a2a")
        with cv.panel(mp.ix, n2.bottom + 62, w=mw - 48, title="Policies you apply in the Azure portal (APIM)",
                      sub="the Foundry portal cannot edit them; the doc's examples", theme="grape", style="dashed", fill="soft",
                      pad=18, title_size=20, sub_size=14) as sh:
            cf = ChipFlow(["rate-limit-by-key (example: 60 calls per 60 s per caller IP)", "ip-filter allow-list",
                           "X-Correlation-Id header from context.RequestId", "delete Cookie and Referer (keep Authorization)",
                           "route by header with set-backend-service"], w=mw - 48 - 36, theme="orange", size=15)
            cf.place(cv, sh.ix, sh.iy)
        connect(cv, sh, n2, a_side="top", b_side="bottom", dash="dashed", sw=3, color="#862e9c", gap=5,
                label="applied here", label_size=15)
    lim.place(cv, mw + GAP, my)
    ben.place(cv, mw + GAP, lim.bottom + 22)

    r4 = max(mp.bottom, ben.bottom) + 44
    gsteps = StepsCard(cw(2), "Govern a tool, step by step", [
        ("Connect the gateway", "Link the AI gateway to the Foundry resource; governance is activated at the resource level."),
        ("Add the MCP tool", "Tools > Catalog, or Build > Tools > Custom > Model Context Protocol; pick the auth type."),
        ("Confirm routing", "The tool's endpoint must show the gateway URL, not the MCP server. Note which agents use the tool."),
        ("Apply policies", "Azure portal > API Management > policies: rate limit, IP filter, correlation ID, header cleanup, routing."),
        ("Test and verify", "Call the tool from an agent, then check APIM metrics and logs."),
    ], theme="orange", icon="mcp", src=[("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))])
    pre = Card(cw(2), "Prerequisites and security", [
        "Gateway connected to the Foundry resource",
        "API Management Service Contributor or Owner on the connected APIM instance",
        "MCP server auth: managed identity (Entra), key-based (API key or token), custom OAuth identity passthrough, or unauthenticated",
        "Treat keys, tokens and OAuth secrets as secrets: keep shared credentials in a project connection and limit project access",
        "Use least privilege for managed identity and Entra access",
        "! Never strip Authorization unless the MCP server does not need it",
    ], theme="orange", icon="key", src=[("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))])
    vf = Card(cw(2), "Verify that governance works", [
        "Open the tool in the Foundry portal: the endpoint points to the gateway, not the MCP server",
        "In APIM metrics look for requests named after your MCP tool; response codes: 2xx = allowed, 429 = rate limit, 403 = IP filter",
        "With rate limiting on, X-RateLimit-Remaining decreases with each call",
        "Enable Diagnostic settings on the APIM instance and query Azure Monitor Logs for detail",
        "! Calls failing after a new policy? Disable policies temporarily to isolate the cause, then refine",
    ], theme="violet", icon="log-analytics", src=[("Govern MCP tools by using an AI gateway", L("agents/how-to/tools/governance"))])
    h4 = max(gsteps.h, pre.h, vf.h)
    gsteps.place(cv, 0, r4, h=h4)
    pre.place(cv, cw(2) + GAP, r4, h=h4)
    vf.place(cv, 2 * (cw(2) + GAP), r4, h=h4)
    y_end = r4 + h4

    # ------------------------------------------------------------------ 5. outbound: bring your own model
    y5 = y_end + 70
    _, hb5 = section_header(cv, 0, y5, "5  Outbound: bring your own model (BYOM) behind your gateway",
                            sub="The mirror image of section 1 - here Foundry Agent Service calls out to models that sit behind YOUR gateway", size=32)
    by = hb5 + 40
    with cv.panel(0, by, w=W, title="Agent Service -> your gateway -> your models", sub="outbound; nothing here is governed by the Foundry AI gateway",
                  theme="blue", style="dashed", fill="none", pad=24, title_size=24, sub_size=15) as bp:
        bw5 = 560
        gap5 = (W - 48 - 4 * bw5) / 3
        bny = bp.iy + 8
        m1 = Box(bw5, "Prompt agent", sub="Foundry Agent Service. Model = <connection-name>/<model-name>, for example my-apim-connection/gpt-4o",
                 theme="green", icon="agent", icon_pos="left", h=124)
        m2 = Box(bw5, "Admin-connected model", sub="Manage > Resource details > Admin-connected models > Add. Each model you add becomes a deployment in Foundry",
                 theme="blue", icon="api-connections", icon_pos="left", h=124)
        m3 = Box(bw5, "Your AI gateway", sub="Azure API Management, or a non-Azure managed AI model gateway",
                 theme="grape", icon="apim", icon_pos="left", h=124)
        m4 = Box(bw5, "Your models", sub="must implement the OpenAI-compatible chat completions API; third-party models are Non-Microsoft Products",
                 theme="blue", icon="cubes", icon_pos="left", h=124, dash="dashed")
        for i, m in enumerate((m1, m2, m3, m4)):
            m.place(cv, bp.ix + i * (bw5 + gap5), bny)
        connect(cv, m1, m2, a_side="right", b_side="left", sw=3, label="agent picks the admin-connected deployment",
                label_size=15, label_wrap=gap5 - 40, gap=5)
        connect(cv, m2, m3, a_side="right", b_side="left", sw=3, label="base URL = gateway base path only; Foundry appends the route",
                label_size=15, label_wrap=gap5 - 40, gap=5)
        connect(cv, m3, m4, a_side="right", b_side="left", sw=3, label="your routing, auth and policies", label_size=15,
                label_wrap=gap5 - 40, gap=5)
    r5 = bp.bottom + 44

    wiz = StepsCard(cw(2), "Add model connection wizard", [
        ("Connection type", "Azure API Management (pick the APIM resource + Base URL) or Other source (connection name + Base URL)."),
        ("Authentication", "API key (key field, header name, header value scheme such as {api_key}), Managed Identity (APIM only; set the Audience) or OAuth 2.0 (Other source: client ID, secret, token URL, default scope)."),
        ("Model configuration", "Name as used in API calls (for Foundry models, the deployment name), Display name, optional Version."),
        ("Advanced", "API version, Include deployment name in URL path (for /deployments/{name}/chat/completions style gateways), static headers."),
    ], theme="blue", icon="api-connections", src=[("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))])
    wiz.place(cv, 0, r5)

    t_key = Table(
        [("Connection pattern", 300), ("Key to provide", 380), ("Header name", 280)],
        [
            ["Direct Foundry project endpoint (no gateway)", "The project API key", "api-key"],
            ["Azure API Management gateway", "The subscription key (APIM > APIs > Subscriptions)", "The header your APIM policy or API definition expects"],
            ["Other gateway (non-Azure)", "The key that gateway issues", "The header its documentation requires"],
        ], w=cw(2), theme="blue", size=14, head_size=15, title="Which key, which header?", title_size=22)
    t_key.place(cv, cw(2) + GAP, r5)
    n_url = Note(cw(2), "Enter the gateway's base path only. Base URL https://<account>.services.ai.azure.com/openai/v1 makes Foundry call .../openai/v1/chat/completions. For Azure OpenAI-style deployment paths use .../openai and turn on Include deployment name in URL path.",
                 kind="tip", title="Base URL rule", src=[("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))])
    n_url.place(cv, cw(2) + GAP, t_key.bottom + 22)

    sup = Card(cw(2), "Supported configuration (as of 2026-11-03)", [
        "Only prompt agents in the Agent SDK support this feature",
        "Tools: Code Interpreter, Functions, File Search, OpenAPI, Foundry IQ, SharePoint Grounding, Fabric Data Agent, MCP, Browser Automation",
        "Public networking works for APIM and self-hosted gateways",
        "# Full network isolation",
        "APIM: deploy Foundry and APIM together with the 16-private-network-standard-agent-apim-setup Bicep template",
        "Self-hosted gateway: make its endpoints reachable inside the virtual network used by Agent Service",
        "! Not supported with the Microsoft Copilot harness",
    ], theme="green", icon="agent", src=[("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))])
    sup.place(cv, 2 * (cw(2) + GAP), r5)

    r5b = max(wiz.bottom, n_url.bottom, sup.bottom) + 44
    conn = Card(cw(2), "Two connection types for CLI and Bicep", [
        "# API Management connection",
        "Defaults: list /deployments, get /deployments/{deploymentName}, provider AzureOpenAI",
        "Auth: API key (subscription key) or Microsoft Entra ID",
        "# Model Gateway connection",
        "For OpenAI, MuleSoft or a custom gateway; static or dynamic model discovery",
        "Auth: API key or OAuth 2.0",
        "Templates: microsoft-foundry/foundry-samples > infrastructure/infrastructure-setup-bicep/01-connections",
    ], theme="blue", icon="code", src=[("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))])
    conn.place(cv, 0, r5b)
    gl = Card(cw(2), "Check the gateway side", [
        "APIM > Monitoring > Application Insights > Add, then APIs > All APIs > Settings > Diagnostic Logs: sampling 100% for tests, Always log errors = Yes, verbosity Information",
        "Query requests, dependencies, exceptions and traces in Application Insights",
        "Or send gateway diagnostics to Log Analytics and query ApiManagementGatewayLogs",
        "You should see incoming requests from the Agent Service endpoint",
    ], theme="violet", icon="app-insights", src=[("Bring your own model to Agent Service", L("agents/how-to/ai-gateway"))])
    gl.place(cv, cw(2) + GAP, r5b, h=conn.h)
    n_risk = Note(cw(2), "BYOM models are third-party 'Non-Microsoft Products' (this excludes Foundry Models sold by Azure). You implement the responsible-AI mitigations (metaprompt, content filters) and you own data handling, retention and location. Prerequisites: Foundry User on the project, Contributor on the resource group for connection deployment.",
                  kind="gotcha", title="You own the risk")
    n_risk.place(cv, 2 * (cw(2) + GAP), r5b)
    n_dis = Note(cw(2), "The page says 'The Response API isn't supported at present', yet its own sample calls responses.create() with an agent_reference. It also carries no GA or Preview label, while the MCP governance page still links to it as 'preview'. Test your pattern and check the docs.",
                 kind="warn", title="Docs disagree")
    n_dis.place(cv, 2 * (cw(2) + GAP), n_risk.bottom + 20)
    y_end = max(conn.bottom, gl.bottom, n_dis.bottom)

    # ------------------------------------------------------------------ 6. control plane, tiers, troubleshooting
    y6 = y_end + 70
    _, hb6 = section_header(cv, 0, y6, "6  Where it sits in the Control Plane, which APIM tier, and what to check when it breaks",
                            size=32)
    c6 = hb6 + 40
    with cv.panel(0, c6, w=cw(3), title="Where it sits in the Control Plane", sub="Foundry (new) portal toolbar", theme="grape",
                  style="dotted", fill="none", pad=22, title_size=24, sub_size=15) as cp:
        nx = cp.ix
        for lab in ("Discover", "Build", "Operate", "Manage"):
            on = lab == "Manage"
            ch = Chip(lab, theme="grape" if on else "gray", fill="solid" if on else "soft", size=18, pad_x=20, pad_y=8,
                      sw=3 if on else 1.5)
            ch.place(cv, nx, cp.iy + 4)
            nx += ch.w + 14
        ny6 = cp.iy + 66
        op = Card(250, "Operate", ["Overview, Assets, Compliance", "subscription-wide; Preview"], theme="gray", fill="soft")
        mg = Card(270, "Manage", ["Quota: GA", "AI Gateway: Preview", "Project and Resource details: GA"], theme="grape", fill="soft")
        hh = max(op.h, mg.h)
        op.place(cv, cp.ix, ny6, h=hh)
        mg.place(cv, cp.ix + 270, ny6, h=hh)
        n_mg = Note(520, "Manage is scoped to your current project and its parent resource. Switch projects first to act on another one.",
                    kind="info")
        n_mg.place(cv, cp.ix, ny6 + hh + 18)
        bl = Card(cw(3) - 44 - 580, "What the gateway powers", [
            "Token limits for models: the Control Plane enforces TPM limits and token quotas at project scope through the AI gateway",
            "MCP tools governance (Preview)",
            "The APIM proxy behind legacy custom-agent registration (Block / Unblock) - deprecated, scheduled Apr 30, 2027, no new adds",
            "! External agents (Preview) use no gateway: Foundry keeps registration metadata only and cannot block them",
            "Control Plane prerequisite on Learn: 'an AI gateway configured for advanced governance features'",
        ], theme="grape", icon="apim", src=[("Control Plane overview", L("control-plane/overview")),
                                            ("Register a custom agent", L("control-plane/register-custom-agent"))])
        bl.place(cv, cp.ix + 580, cp.iy + 4)

    t_tier = Table(
        [("Tier", 140), ("Role in Foundry", 380), ("Network options", 600), ("Scale", 408)],
        [
            [("Basic v2", "grape"), "What Create new provisions: development and testing, with SLA support", "No VNet integration, private endpoint or injection listed on the overview", "Up to 10 units"],
            [("Standard v2", "grape"), "Production-ready; can be picked with Use existing", "VNet integration (outbound to isolated backends; gateway and management plane stay public) + inbound private endpoint", "Up to 10 units"],
            [("Premium v2", "grape"), "Enterprise; for a private Foundry resource", "VNet injection with no public IP (full isolation) or private endpoint; availability zones", "Up to 30 units; gateway on a dedicated App Service Environment"],
            [("Classic tiers", "gray"), "Not listed for Use existing: must be a v2 tier", "-", "-"],
        ], w=cw(3), theme="grape", size=14, head_size=15, title="Which API Management v2 tier?", title_size=22)
    t_tier.place(cv, cw(3) + GAP, c6)
    n_v2 = Note(cw(3), "The v2 tiers currently list multi-region deployment, backup and restore, and upgrade from the classic tiers as unavailable (APIM docs, as of 2026-11-03). Plan resilience around that.",
                kind="warn", title="v2 tier limits", src=[("API Management v2 tiers", A("azure/api-management/v2-service-tiers-overview"))])
    n_v2.place(cv, cw(3) + GAP, t_tier.bottom + 22)

    r6 = max(cp.bottom, n_v2.bottom) + 50
    t_tr = Table(
        [("Symptom", 520), ("Likely cause", 760), ("Try", 1100), ("Where documented", 720)],
        [
            ["Requests bypass the gateway", "The project was not enabled before the calls, or the gateway is not fully provisioned", "Check that the gateway status is Enabled for both the resource and the project",
             src_cell("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal"))],
            ["Project shows Gateway status: Disabled", "Existing projects are not added automatically", "Open the gateway, find the project, select Add project to gateway",
             src_cell("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal"))],
            ["Token limits don't apply", "Limits are not configured, or the project is not using the gateway", "Enable the project, set limits in Manage > AI Gateway, confirm the enforcement toggle is on",
             src_cell("Enforce token limits", L("control-plane/how-to-enforce-limits-models"))],
            ["500 errors on model calls after setup", "Auto-created APIM endpoints not fully provisioned, or the deployment is not mapped through the gateway", "Wait several minutes, test the model without the gateway, check APIM Monitoring > Logs, remove and re-add the project",
             src_cell("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal"))],
            ["High latency after enabling", "APIM cold start, or APIM and the Foundry resource are in different regions", "Compare the two regions; call the model directly and through the gateway and compare",
             src_cell("Enforce token limits", L("control-plane/how-to-enforce-limits-models"))],
            ["Use existing does not list your APIM", "Not a v2 tier, another tenant or subscription, or a missing role", "Check tier, tenant, subscription and your API Management Service Contributor or Owner role",
             src_cell("Configure AI Gateway", L("configuration/enable-ai-api-management-gateway-portal"))],
            ["MCP tool still calls the server directly", "Tool created before the gateway was connected, or it uses managed OAuth", "Re-create the tool after connecting the gateway; confirm it is an MCP tool without managed OAuth",
             src_cell("Govern MCP tools", L("agents/how-to/tools/governance"))],
            ["BYOM: model not found", "Deployment name is not in the <connection-name>/<model-name> format", "Fix the model value, for example my-apim-connection/gpt-4o",
             src_cell("Bring your own model", L("agents/how-to/ai-gateway"))],
            ["BYOM: connection Inactive, or timeouts", "Gateway URL unreachable, bad credentials, or the gateway is not reachable from the Agent Service network", "Verify the URL and credentials; for private networks follow the network isolation guidance",
             src_cell("Bring your own model", L("agents/how-to/ai-gateway"))],
        ], w=W, theme="red", size=14, head_size=15, title="Troubleshooting (from the docs)", title_size=22)
    t_tr.place(cv, 0, r6)
    y_end = t_tr.bottom
    cv.meta["_y"] = y_end
    # @@NEXT@@
    sources(cv, 0, cv.meta["_y"] + 60, [
        ("Configure AI Gateway in your Foundry resources", L("configuration/enable-ai-api-management-gateway-portal")),
        ("Enforce token limits for models", L("control-plane/how-to-enforce-limits-models")),
        ("Govern MCP tools by using an AI gateway (preview)", L("agents/how-to/tools/governance")),
        ("Bring your own model to Foundry Agent Service", L("agents/how-to/ai-gateway")),
        ("Microsoft Foundry Control Plane overview", L("control-plane/overview")),
        ("High availability and resiliency", L("how-to/high-availability-resiliency")),
        ("Configure network isolation (private link)", L("how-to/configure-private-link")),
        ("Foundry quota", L("how-to/quota")),
        ("Plan and manage costs", L("concepts/manage-costs")),
        ("AI gateway capabilities in Azure API Management", A("azure/api-management/genai-gateway-capabilities")),
        ("llm-token-limit policy (API Management)", A("azure/api-management/llm-token-limit-policy")),
        ("API Management v2 tiers", A("azure/api-management/v2-service-tiers-overview")),
        ("Foundry samples: connections (GitHub)",
         "https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/01-connections"),
        ("Ignite 2025 BRK202 (video-sourced: only the 'per agents' remark)", "https://www.youtube.com/watch?v=XjVj_qRwzVg"),
    ], w=W, cols=3, title="Sources and further reading (Microsoft Learn, plus the samples repo and one video)")
