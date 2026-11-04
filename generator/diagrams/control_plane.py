"""Foundry Control Plane - four pillars in one role-aware console, how it plugs into Defender / Purview / Entra / Agent 365,
fleet lifecycle, custom vs external agents, Entra admin governance, token limits, guardrail policies, roles, personas."""
from generator.xd import *
from generator.xd import metrics as M
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="control-plane", title="Foundry Control Plane", section="2", group="Control plane and cost", order=50,
    description="One role-aware console for the agent fleet: four pillars, Operate and Manage panes, integrations with Defender, "
                "Purview, Entra Agent ID and Agent 365, lifecycle controls, token limits, guardrail policies, roles and who sees what.",
    tags=["control-plane", "governance", "agent-fleet", "compliance", "entra-agent-id", "agent-365"],
)

W = 3200
GX = 170                      # left gutter of the hero (layer labels)
AS_OF = "as of 2026-11-03"

# ---------------------------------------------------------------------------------------------- citations
S_OVERVIEW = ("What is Foundry Control Plane?", learn("control-plane/overview"))
S_MONITOR = ("Monitor agent health across your fleet", learn("control-plane/monitoring-across-fleet"))
S_MANAGE = ("Manage agents at scale", learn("control-plane/how-to-manage-agents"))
S_CUSTOM = ("Register and manage custom agents", learn("control-plane/register-custom-agent"))
S_MIGRATE = ("Migrate custom agents to external agents", learn("control-plane/migrate-custom-to-external-agent"))
S_EXTERNAL = ("Register external agents (preview)", learn("agents/how-to/register-external-agent"))
S_ENTRA = ("Manage agent availability as an administrator", learn("control-plane/govern-agent-infrastructure-entra-admin"))
S_COMPL = ("Manage compliance and security", learn("control-plane/how-to-manage-compliance-security"))
S_QS = ("Quickstart: create a guardrail policy", learn("control-plane/quickstart-create-guardrail-policy"))
S_LIMITS = ("Enforce token limits for models", learn("control-plane/how-to-enforce-limits-models"))
S_GATEWAY = ("Configure an AI gateway", learn("configuration/enable-ai-api-management-gateway-portal"))
S_MCPGOV = ("Govern MCP tools with an AI gateway", learn("agents/how-to/tools/governance"))
S_IDENT = ("Agent identity concepts", learn("agents/concepts/agent-identity"))
S_A365 = ("Agent 365 integration with Foundry", learn("agents/concepts/agent-365-integration"))
S_A365D = ("Configure Agent 365 data collection", learn("agents/how-to/configure-agent-365-data-collection"))
S_GA = ("Feature readiness at GA", learn("concepts/general-availability"))
S_GUARD = ("Guardrails and controls overview", learn("guardrails/guardrails-overview"))
S_A365OV = ("Overview of Microsoft Agent 365", learn("microsoft-agent-365/overview", base=""))
S_DEFENDER = ("Threat protection for Foundry Tools (Defender for Cloud)", learn("azure/defender-for-cloud/ai-onboarding", base=""))
S_DASH = ("Monitor agents with the monitoring dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard"))
S_COSTS = ("Plan and manage costs", learn("concepts/manage-costs"))

# arrow colours (match the theme strokes)
C_VIOLET, C_GRAPE, C_RED, C_INDIGO, C_GREEN, C_BLUE, C_GRAY = ("#6741d9", "#9c36b5", "#e03131", "#3b5bdb", "#2f9e44", "#1971c2",
                                                                "#495057")


# ---------------------------------------------------------------------------------------------- small helpers
def _bullets_h(items, w, size, gap=5):
    lh = size * M.line_ratio()
    return sum(len(wrap_text(t, (w - 18) * 0.965, size)) * lh + gap for t in items) - (gap if items else 0)


def _draw_bullets(cv, x, y, w, items, theme, size=15, gap=5):
    th = get_theme(theme)
    lh = size * M.line_ratio()
    cy = y
    for t in items:
        lines = wrap_text(t, (w - 18) * 0.965, size)
        cv.text(x + 18, cy, "\n".join(lines), size=size, color=INK)
        cv.ellipse(x + 4, cy + lh / 2 - 4, 9, 9, stroke=th.stroke, sw=2, rough=0)
        cy += len(lines) * lh + gap
    return cy - gap


def _panel_head(title, sub, ts, ss, pad):
    """Height consumed above the inner content of cv.panel (mirror of Canvas.panel)."""
    if not title:
        return pad
    h = M.text_size(title, ts)[1] + 6
    if sub:
        h += M.text_size(sub, ss)[1] + 2
    return pad + h + 8


def _badge_w(kind, size=13):
    return M.line_width(STATUS.get(kind, ("gray", kind))[1], size) + 18


class Window(Rect2):
    """Console-style window: title bar with window dots + status badge, optional chip row, bullets."""
    BAR = 40

    def __init__(self, w, title, items=(), *, theme="gray", badge=None, chips=(), dashed=(), size=15, pad=14, min_h=0):
        self.th = get_theme(theme)
        self.theme_name = theme
        self.w, self.title, self.items, self.badge, self.size, self.pad = w, title, list(items), badge, size, pad
        self.chips = None
        if chips:
            cl = [Chip(c, theme=theme, size=13, fill="soft", dash="dashed" if c in dashed else "solid", pad_y=4) for c in chips]
            self.chips = ChipFlow(cl, w - 2 * pad, gap=8)
        self.body_h = _bullets_h(self.items, w - 2 * pad, size)
        self.h = max(self.BAR + 4 + pad + (self.chips.h + 12 if self.chips else 0) + self.body_h + pad, min_h)
        self.x = self.y = 0.0
        self.frame = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, BAR = self.th, self.pad, self.BAR
        with cv.group():
            self.frame = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, round_=False)
            cv.rect(x + 2, y + 2, self.w - 4, BAR, stroke="transparent", fill=th.fill, style="solid", sw=0, round_=False, rough=0)
            cv.line((x + 2, y + 2 + BAR), (x + self.w - 2, y + 2 + BAR), stroke=th.stroke, sw=2)
            for i, col in enumerate(("#fa5252", "#fab005", "#40c057")):
                cv.ellipse(x + 14 + i * 18, y + 2 + BAR / 2 - 5, 10, 10, stroke=col, fill=col, style="solid", sw=1, rough=0)
            cv.text(x + 14 + 3 * 18 + 10, y + 2 + (BAR - 19 * M.line_ratio()) / 2, self.title, size=19, color=th.deep)
            if self.badge:
                bw = _badge_w(self.badge)
                draw_badge(cv, x + self.w - 10 - bw, y + 2 + (BAR - 22) / 2, self.badge)
            cy = y + 2 + BAR + pad
            if self.chips:
                self.chips.place(cv, x + pad, cy)
                cy += self.chips.h + 12
            _draw_bullets(cv, x + pad, cy, self.w - 2 * pad, self.items, self.theme_name, self.size)
        return self

    @property
    def bind_target(self):
        return self.frame


def vlink(cv, upper, lower, x, direction="up", **kw):
    """Straight vertical arrow at absolute x between two blocks (upper above lower)."""
    ta = (x - upper.x) / upper.w
    tb = (x - lower.x) / lower.w
    assert 0 < ta < 1 and 0 < tb < 1, (upper.x, upper.w, lower.x, lower.w, x)
    if direction == "down":
        return connect(cv, upper, lower, a_side="bottom", b_side="top", ta=ta, tb=tb, **kw)
    if direction == "up":
        return connect(cv, lower, upper, a_side="top", b_side="bottom", ta=tb, tb=ta, **kw)
    return connect(cv, upper, lower, a_side="bottom", b_side="top", ta=ta, tb=tb, start_head="arrow", end_head="arrow", **kw)


def hlink(cv, left, right, y, direction="right", **kw):
    """Straight horizontal arrow at absolute y between two blocks (left of right)."""
    ta = (y - left.y) / left.h
    tb = (y - right.y) / right.h
    assert 0 < ta < 1 and 0 < tb < 1, (left.y, left.h, right.y, right.h, y)
    if direction == "right":
        return connect(cv, left, right, a_side="right", b_side="left", ta=ta, tb=tb, **kw)
    if direction == "left":
        return connect(cv, right, left, a_side="left", b_side="right", ta=tb, tb=ta, **kw)
    return connect(cv, left, right, a_side="right", b_side="left", ta=ta, tb=tb, start_head="arrow", end_head="arrow", **kw)


def _layer_label(cv, y, n, title, sub, theme="gray"):
    th = get_theme(theme)
    numbered(cv, 32, y + 28, n, theme=theme, d=44, size=22)
    cv.text(62, y + 18, title, size=18, color=th.deep)
    cv.text(8, y + 64, sub, size=14, color="#495057", wrap=148)


def _sec(cv, y, title, sub):
    """Section header used by every zone; returns the y where content can start."""
    _, b = section_header(cv, 0, y, title, sub=sub, size=34, w=W)
    return b + 36


# ---------------------------------------------------------------------------------------------- 1. pillars ("temple")
def _pillars(cv, y0):
    """Roof + entablature + four pillars + foundation (left) and when-to-use / status notes (right)."""
    TW = 2230
    grape = get_theme("grape")
    roof_h = 120
    cv.poly([(0, y0 + roof_h), (TW / 2, y0), (TW, y0 + roof_h), (0, y0 + roof_h)], kind="line", stroke=grape.stroke, sw=2,
            fill=grape.fill, fill_style="hachure")
    t = "Microsoft Foundry Control Plane"
    tw, th_ = M.text_size(t, 36)
    cv.rect(TW / 2 - tw / 2 - 14, y0 + roof_h - th_ - 22, tw + 28, th_ + 14, stroke="transparent", fill="#ffffff", style="solid", sw=0,
            rough=0, opacity=92, round_=False)
    cv.text(TW / 2 - tw / 2, y0 + roof_h - th_ - 15, t, size=36, color=grape.deep)
    by = y0 + roof_h + 8
    beam = Box(TW, "Visibility + governance + control for agents, models and tools - from build to production, in one role-aware interface",
               h=64, theme="grape", fill="soft", size=19, sw=2).place(cv, 0, by)
    pw, pg = 520, 36
    px = (TW - (4 * pw + 3 * pg)) / 2
    py = by + beam.h + 26
    cols = [
        Card(pw, "Inventory", [
            "Every agent, model and tool across the projects of a subscription in one searchable table",
            "Discovers Foundry agents (prompt, workflow, hosted), Azure SRE Agent, Logic Apps agent loops, custom agents",
            "Discovery is RBAC-trimmed: different users see different agents",
            "# In the console: Operate > Assets",
        ], theme="green", icon="all-resources", src=[S_MANAGE]),
        Card(pw, "Observability", [
            "Fleet health, run completion, error trends, token usage and cost",
            "Alerts, evaluation results and traces correlated; deep links to Evaluation and Monitoring",
            "Continuous evaluation, AI Red Teaming Agent, cluster analysis",
            "# In the console: Operate > Overview and Assets",
        ], theme="violet", icon="app-insights", src=[S_MONITOR]),
        Card(pw, "Compliance", [
            "Enterprise-wide guardrail policies for model deployments",
            "Azure Policy under the hood: versioned policies, assignment tracking",
            "Real-time posture; noncompliant assets surfaced; bulk remediation",
            "# In the console: Operate > Compliance",
        ], theme="grape", icon="policy", src=[S_COMPL]),
        Card(pw, "Security", [
            "Defender recommendations and jailbreak / prompt-attack alerts on the dashboard",
            "Purview: audit, sensitive-info classification, DSPM for AI",
            "Entra Agent ID: one identity per agent; admin Block / Delete",
            "Scheduled red-teaming and drift monitoring; rate-limit, token and cost anomalies",
            "# In the console: Compliance > Security posture, plus Entra and Purview",
        ], theme="red", icon="defender", src=[S_OVERVIEW]),
    ]
    _, pb = row(cv, px, py, cols, gap=pg)
    for i, c in enumerate(cols):
        numbered(cv, c.x + c.w - 26, c.y + 26, i + 1, theme=["green", "violet", "grape", "red"][i], d=34, size=19)
    fy = pb + 14
    base = Box(TW, "Built on: OpenTelemetry in Application Insights  |  Azure Policy  |  Microsoft Defender  |  Microsoft Purview  |  "
                   "Microsoft Entra (Agent ID)  |  Agent 365  |  AI gateway (Azure API Management)",
               h=54, theme="gray", fill="soft", size=17, sw=2).place(cv, 0, fy)
    rx = TW + 50
    rw = W - rx
    when = Card(rw, "When to use it", [
        "Many agents across different projects or teams",
        "Central compliance visibility and policy enforcement across the AI fleet",
        "Defender and Purview integration for AI governance and threat protection",
        "Agents from several platforms: Foundry, Microsoft and non-Microsoft",
        "Track cost, token usage and resource consumption across the whole environment",
        "= Without it: individual Azure portal blades and separate per-project views.",
    ], theme="gray", icon="learn", src=[S_OVERVIEW])
    when.place(cv, rx, y0)
    n1 = Note(rw, "Foundry (new) portal only - look for the New Foundry toggle. Operate (subscription-wide) and Manage (current project + parent "
                  "resource) toolbar buttons. Learn documents no API surface for the dashboards.", kind="info", title="Where it lives",
              src=[S_OVERVIEW])
    n1.place(cv, rx, when.bottom + 22)
    n2 = Note(rw, f"Status {AS_OF}: Operate > Overview, Assets and Compliance = Preview. Manage > AI Gateway = Preview. Manage > Quota and "
                  "Project / Resource details = GA. Preview features carry no SLA.", kind="preview", title="Preview vs GA", src=[S_GA])
    n2.place(cv, rx, n1.bottom + 22)
    return max(fy + base.h, n2.bottom)


# ---------------------------------------------------------------------------------------------- 2. hero: the console wall
def _hero(cv, y0):
    right, bottom = section_header(cv, 0, y0, "The console wall: who looks, what they see, what feeds it, what it controls",
                                   sub="Layered architecture - solid arrows carry signals up (observe), dashed arrows carry controls down (act)",
                                   size=34, w=W)
    y = bottom + 26
    # ------------------------------------------------------------- column grid shared by every layer so arrows run straight
    gx = 22
    ow = (480, 740, 680)
    op_x = GX + 24
    OX = op_x + 22
    xs = [OX, OX + ow[0] + gx, OX + ow[0] + gx + ow[1] + gx]
    op_w = sum(ow) + 2 * gx + 44
    MX = op_x + op_w + 28
    MW = W - 24 - MX

    w_over = Window(ow[0], "Overview", [
        "Trend-based health scores and alert summaries",
        "Drill from an anomaly or cost spike to inventory, observability or policy",
        "Scope: whole subscription by default (all discovered agents), project dropdown, date range",
    ], theme="violet", badge="preview", chips=["active agents", "cost trends", "run-completion rate", "prevented behaviors"])
    w_assets = Window(ow[1], "Assets", [
        "One searchable table of every agent, model and tool across the projects of a subscription",
        "Drill into Evaluation, Monitoring and Traces; inline recommendations",
        "Drift, latency and error clusters; AI Red Teaming Agent hooks",
        "Observe and modify model and agent guardrails",
        "Update status: Start / Stop / Block / Unblock",
    ], theme="green", badge="preview", chips=["version", "tags", "health score %", "cost", "alerts", "token usage"])
    w_comp = Window(ow[2], "Compliance", [
        "Guardrail policies for model deployments = Azure Policy assignments",
        "Scope: one subscription or one resource group, with exceptions",
        "Versioned policies, assignment tracking, real-time posture",
        "Noncompliant assets surfaced: Fix now, bulk remediation",
        "Defender recommendations and the Purview toggle live here",
    ], theme="grape", badge="preview", chips=["Policies", "Assets", "Guardrails", "Security posture", "Data security and governance"],
        dashed=["Data security and governance"])
    mw = (MW - 44 - 22) / 2
    m_quota = Window(mw, "Quota", ["Deployments and quota consumed", "Show all: every model and region, even undeployed"],
                     theme="yellow", badge="ga")
    m_gw = Window(mw, "AI Gateway", ["APIM-based gateway for the Foundry resource", "Per-project token limits; MCP tools governance"],
                  theme="indigo", badge="preview")
    m_proj = Window(mw, "Project details", ["Resource ID, endpoint, subscription, location",
                                            "Users tab; Connected resources tab (Application Insights, storage)"], theme="gray", badge="ga")
    m_res = Window(mw, "Resource details", ["Parent resource config; open in the Azure portal", "Projects tab: add and review projects"],
                   theme="gray", badge="ga")
    op_h = max(w.h for w in (w_over, w_assets, w_comp))
    mg_h = max(m_quota.h, m_gw.h) + 18 + max(m_proj.h, m_res.h)
    inner_h = max(op_h, mg_h)

    # ------------------------------------------------------------- layer 1: personas
    _layer_label(cv, y + 30, 1, "WHO", "opens the console; RBAC trims what each persona sees", "gray")
    py = y + 6
    ph = 104
    pers = [
        Box(ow[0], "Platform admin", h=ph, theme="grape", sub="fleet health, cost, policy, quota, gateway", icon="gear", icon_pos="left",
            icon_size=40, size=20, sub_size=14),
        Box((ow[1] - 20) / 2, "Developer", h=ph, theme="green", sub="own agents: versions, traces, error rate", icon="code",
            icon_pos="left", icon_size=40, size=20, sub_size=14),
        Box((ow[1] - 20) / 2, "AI quality engineer", h=ph, theme="violet", sub="evaluation, drift, red teaming", icon="metrics",
            icon_pos="left", icon_size=40, size=20, sub_size=14),
        Box(ow[2], "Security admin", h=ph, theme="red", sub="Defender + Purview signals, agent identity, Block / Delete", icon="security",
            icon_pos="left", icon_size=40, size=20, sub_size=14),
        Box(MW - 44, "Administrators and power users", h=ph, theme="gray", sub="project and resource setup: quota, AI gateway, users, connections",
            icon="users", icon_pos="left", icon_size=40, size=20, sub_size=14),
    ]
    pxs = [xs[0], xs[1], xs[1] + (ow[1] - 20) / 2 + 20, xs[2], MX + 22]
    for b, bx in zip(pers, pxs):
        b.place(cv, bx, py)
    cb_y = py + ph + 78

    # ------------------------------------------------------------- layer 2: console
    head = _panel_head("OPERATE", None, 22, 15, 22)
    with cv.panel(GX, cb_y, title=None, theme="grape", style="dotted", pad=24, w=W - GX, min_h=24 + head + inner_h + 24 + 22) as cb:
        with cv.panel(op_x, cb.iy, title="OPERATE", theme="grape", style="solid", fill="soft", pad=22, title_size=22, w=op_w,
                      min_h=head + inner_h + 22) as op:
            for wdw, x in zip((w_over, w_assets, w_comp), xs):
                wdw.place(cv, x, op.iy, h=inner_h)
        with cv.panel(MX, cb.iy, title="MANAGE", theme="indigo", style="solid", fill="soft", pad=22, title_size=22, w=MW,
                      min_h=head + inner_h + 22) as mg:
            rh1 = max(m_quota.h, m_gw.h)
            rh2 = inner_h - rh1 - 18
            m_quota.place(cv, mg.ix, mg.iy, h=rh1)
            m_gw.place(cv, mg.ix + mw + 22, mg.iy, h=rh1)
            m_proj.place(cv, mg.ix, mg.iy + rh1 + 18, h=rh2)
            m_res.place(cv, mg.ix + mw + 22, mg.iy + rh1 + 18, h=rh2)
    _layer_label(cv, cb_y + 6, 2, "CONSOLE", "Foundry (new) portal. Operate = subscription-wide. Manage = current project + parent resource", "grape")
    for b, tgt in ((pers[0], w_over), (pers[1], w_assets), (pers[2], w_assets), (pers[3], w_comp)):
        vlink(cv, b, tgt, b.cx, "down", color=C_GRAY, sw=3)
    vlink(cv, pers[4], mg, pers[4].cx, "down", color=C_GRAY, sw=3)

    # ------------------------------------------------------------- layer 3: integrated services
    c_y = cb.bottom + 112
    T = 20
    ai_x, ai_w = op_x, 620
    ent_x, ent_w = ai_x + ai_w + 30, 240
    a365_w = 240
    a365_x = ent_x + ent_w + 130
    tw3 = (ow[2] - 2 * T) / 3
    t_ai = Card(ai_w, "Application Insights", [
        "Agents emit OpenTelemetry spans (GenAI semantic conventions)",
        "Per project: Manage > Project details > Connected resources > AppInsights",
        "Viewers need Log Analytics Reader (or higher) plus Cost Management Reader for cost columns",
        "! No Application Insights = no health metrics, cost tracking or drill-down traces",
    ], theme="violet", icon="app-insights", body_size=15, src=[S_MONITOR])
    t_ent = Card(ent_w, "Entra Agent ID", [
        "One identity per Foundry agent (Entra ID column)",
        "Tenant-wide inventory in Entra admin center",
        "Admin Block / Delete",
    ], theme="red", icon="managed-identity", body_size=14, title_size=19, src=[S_IDENT])
    t_a365 = Card(a365_w, "Agent 365", [
        "Registry sync of published agents",
        "Autopilots from hosted agents",
        "Admin Block / Delete in Microsoft 365 admin center",
    ], theme="red", icon="m365", body_size=14, title_size=19, src=[S_A365])
    t_pol = Card(tw3, "Azure Policy", [
        "Guardrail policy = Azure Policy assignment",
        "Compliance %, versions, bulk fix",
    ], theme="grape", icon="policy", body_size=14, title_size=19, src=[S_QS])
    t_def = Card(tw3, "Defender for Cloud", [
        "Posture recommendations",
        "Jailbreak and prompt-attack alerts",
    ], theme="red", icon="defender", body_size=14, title_size=19, src=[S_COMPL])
    t_pur = Card(tw3, "Microsoft Purview", [
        "Audit, SIT, DSPM for AI",
        "Toggle per subscription",
    ], theme="red", icon="info-protection", body_size=14, title_size=19, src=[S_COMPL])
    t_apim = Card(MW, "AI gateway (Azure API Management)", [
        "Token limits per project x deployment: TPM -> 429, token quota -> 403",
        "MCP tools governance: policies applied in the Azure portal",
        "Legacy custom-agent proxy: Block / Unblock",
        "= Control Plane prerequisite: an AI gateway configured for advanced governance features.",
    ], theme="indigo", icon="apim", badge="preview", body_size=15, src=[S_LIMITS, S_GATEWAY])
    tiles3 = [(t_ai, ai_x), (t_ent, ent_x), (t_a365, a365_x), (t_pol, xs[2]), (t_def, xs[2] + tw3 + T), (t_pur, xs[2] + 2 * (tw3 + T)),
              (t_apim, MX)]
    h3 = max(t.h for t, _ in tiles3)
    with cv.panel(GX, c_y, title=None, theme="gray", style="dotted", pad=24, w=W - GX, min_h=24 + h3 + 24) as cc:
        for t, x in tiles3:
            t.place(cv, x, cc.iy, h=h3)
    _layer_label(cv, c_y + 6, 3, "SERVICES", "integrated with the console: signals up, controls down", "gray")

    # ------------------------------------------------------------- layer 4: fleet + governed resources
    d_y = cc.bottom + 112
    f_ext = Card(256, "External agents", ["Registered by name + OpenTelemetry ID", "Telemetry only: no proxy, no block"],
                 theme="green", badge="preview", body_size=14, title_size=19, fill="soft", dash="dashed", src=[S_EXTERNAL])
    f_found = Card(934, "Foundry agents", [
        "Discovered automatically across all projects in the subscription",
        "Start / Stop when published or hosted; unpublished prompt and workflow agents have no Stop action (delete)",
        "Classic agents and Azure OpenAI assistants are not supported",
    ], theme="green", icon="agent", body_size=15, src=[S_MANAGE])
    f_model = Card(ow[2], "Model deployments", [
        "Guardrail policies set minimum controls per deployment (subscription or resource-group scope)",
        "Defender threat protection covers managed inference endpoints",
        "Token limits per project x deployment through the AI gateway",
    ], theme="blue", icon="openai", body_size=15, src=[S_GUARD])
    sw4 = (MW - 3 * 18) / 4
    f_sre = Card(sw4, "Azure SRE Agent", ["Start / Stop"], theme="green", body_size=14, title_size=18, fill="soft")
    f_logic = Card(sw4, "Logic Apps agent loops", ["Start / Stop (stops ALL workflows of the resource)", "No traces or metrics"], theme="green",
                   body_size=14, title_size=18, fill="soft")
    f_cust = Card(sw4, "Custom agents", ["Clients call the APIM gateway URL", "Block / Unblock only", "Ends 2027-04-30"], theme="green", badge="retiring",
                  body_size=14, title_size=18, fill="soft", dash="dashed", src=[S_CUSTOM])
    f_mcp = Card(sw4, "MCP tools", ["New tools made in the Foundry portal (no managed OAuth) are routed through the gateway", "(preview)"], theme="orange",
                 body_size=14, title_size=18, fill="soft", icon="mcp", icon_size=30, src=[S_MCPGOV])
    tiles4 = [(f_ext, op_x), (f_found, op_x + 256 + 30), (f_model, xs[2]), (f_sre, MX), (f_logic, MX + sw4 + 18),
              (f_cust, MX + 2 * (sw4 + 18)), (f_mcp, MX + 3 * (sw4 + 18))]
    h4 = max(t.h for t, _ in tiles4)
    with cv.panel(GX, d_y, title=None, theme="green", style="dotted", pad=24, w=W - GX, min_h=24 + h4 + 24) as dd:
        for t, x in tiles4:
            t.place(cv, x, dd.iy, h=h4)
    _layer_label(cv, d_y + 6, 4, "FLEET", "agents on several platforms, plus the model deployments and tools around them", "green")

    # ------------------------------------------------------------- arrows: console <-> integrations
    vlink(cv, w_over, t_ai, 450, "up", color=C_VIOLET, sw=3, label="fleet health, cost trends", label_size=13, label_wrap=130)
    vlink(cv, w_assets, t_ai, 750, "up", color=C_VIOLET, sw=3, label="error rate, tokens, traces", label_size=13, label_wrap=130)
    vlink(cv, w_assets, t_ent, t_ent.cx, "up", color=C_RED, sw=3, label="Entra ID column", label_size=13, label_wrap=120)
    vlink(cv, w_comp, t_pol, t_pol.cx, "both", color=C_GRAPE, sw=3, label="policy and compliance state", label_size=13, label_wrap=116)
    vlink(cv, w_comp, t_def, t_def.cx, "up", color=C_RED, sw=3, label="posture, alerts", label_size=13, label_wrap=116)
    vlink(cv, w_comp, t_pur, t_pur.cx, "both", color=C_RED, sw=3, label="toggle, audit, DSPM", label_size=13, label_wrap=116)
    vlink(cv, mg, t_apim, MX + 440, "both", color=C_INDIGO, sw=3, label="configure gateway and token limits", label_size=13, label_wrap=190)
    act_x = (ent_x + ent_w + a365_x) / 2
    connect(cv, w_assets, f_found, a_side="bottom", b_side="top", ta=(act_x - w_assets.x) / w_assets.w, tb=(act_x - f_found.x) / f_found.w,
            dash="dashed", color=C_GRAPE, sw=4, label="Update status: Start / Stop / Block", label_size=13, label_wrap=130, label_pos="center")
    # ------------------------------------------------------------- arrows: integrations <-> fleet
    vlink(cv, t_ai, f_ext, 300, "up", color=C_VIOLET, sw=3, label="OTel only, no proxy", label_size=13, label_wrap=100)
    vlink(cv, t_ai, f_found, 640, "up", color=C_VIOLET, sw=3, label="OpenTelemetry spans", label_size=13, label_wrap=116)
    vlink(cv, t_ent, f_found, t_ent.cx, "both", color=C_RED, sw=3, label="identity, Block / Delete", label_size=13, label_wrap=116)
    vlink(cv, t_a365, f_found, t_a365.cx, "both", color=C_RED, sw=3, label="registry sync, Block / Delete", label_size=13, label_wrap=116)
    vlink(cv, t_pol, f_model, t_pol.cx, "down", color=C_GRAPE, sw=3, label="evaluates guardrails", label_size=13, label_wrap=116)
    vlink(cv, t_def, f_model, t_def.cx, "up", color=C_RED, sw=3, label="threat signals", label_size=13, label_wrap=116)
    vlink(cv, t_pur, f_model, t_pur.cx - 10, "up", color=C_RED, sw=3, label="AI interaction data", label_size=13, label_wrap=116, label_pos="left")
    vlink(cv, t_apim, f_cust, f_cust.cx, "down", color=C_INDIGO, sw=3, label="proxy + Block", label_size=13, label_wrap=100)
    vlink(cv, t_apim, f_mcp, f_mcp.cx, "down", color=C_INDIGO, sw=3, label="governs new tools", label_size=13, label_wrap=100)
    gy = (cc.bottom + dd.y) / 2 + 6
    arrow(cv, [(MX + 40, t_apim.bottom + 8), (MX + 40, gy), (f_model.right - 36, gy), (f_model.right - 36, f_model.y - 8)],
          color=C_INDIGO, sw=3, label="token limits: TPM 429, quota 403", label_size=13, label_t=0.04, label_pos="right", label_wrap=170)
    ky = dd.bottom + 26
    cv.text(GX, ky, "Key:", size=16, color=C_GRAY)
    arrow(cv, [(GX + 56, ky + 11), (GX + 136, ky + 11)], color=INK, sw=3)
    cv.text(GX + 146, ky, "signal or data (read)", size=15)
    arrow(cv, [(GX + 376, ky + 11), (GX + 456, ky + 11)], color=C_GRAPE, sw=4, dash="dashed")
    cv.text(GX + 466, ky, "control (write / act)", size=15)
    arrow(cv, [(GX + 676, ky + 11), (GX + 756, ky + 11)], color=INK, sw=3, start_head="arrow")
    cv.text(GX + 766, ky, "both directions", size=15)
    cv.text(GX + 976, ky, f"Badges show status {AS_OF}. Dashed outline = preview or retiring.", size=15, color=C_GRAY)
    return ky + 26


# ---------------------------------------------------------------------------------------------- 3. integration map
def _integration(cv, y0):
    y = _sec(cv, y0, "How it plugs into Defender, Purview, Entra Agent ID and Agent 365",
             "Four Microsoft security and identity systems around one console: what each shows in Foundry, what it needs, and which way the data flows")
    LW, CW, RW, G = 880, 1100, 880, 170
    cx0 = LW + G
    rx0 = cx0 + CW + G
    c_def = Card(LW, "Microsoft Defender for Cloud", [
        "Security posture tab: Defender recommendations with the affected resource, risk level and remediation links",
        "Jailbreak and user-prompt attack detections appear as Defender alerts; Defender and Purview alerts show on the Control Plane dashboard",
        "Correlate the alerts with Purview Audit records of the AI interactions",
        "Needs: Defender for Cloud on the subscription (Security Admin or Owner) + threat protection for Foundry Tools",
        "Scope: AI workloads on Foundry managed inference endpoints",
    ], theme="red", icon="defender", src=[S_COMPL, S_DEFENDER])
    c_pur = Card(LW, "Microsoft Purview", [
        "Compliance > Data security and governance: pick a subscription, turn on Powered by Microsoft Purview (Foundry Account Owner)",
        "Interaction data feeds Purview Audit, SIT classification, DSPM for AI, Insider Risk, Communication Compliance, Data Lifecycle Management and eDiscovery",
        "Data Security Policies apply to Entra user-context auth on /chat/completions (AzureUserSecurityContext); other auth shows only in Audit and the DSPM activity explorer",
        "Needs a Purview licence; billing is Purview pay-as-you-go meters or an Agent 365 subscription, else Audit only",
        "! No network-isolation support yet",
    ], theme="pink", icon="info-protection", src=[S_COMPL])
    c_ent = Card(RW, "Microsoft Entra Agent ID", [
        "Each Foundry agent gets its own agent identity blueprint + agent identity (a special service principal) with no permissions at first",
        "Assets > Agents > Entra ID column: agent identity application + object ID",
        "Entra admin center: tenant-wide inventory, Conditional Access, Identity Protection, network access, governance (expiry, owners, sponsors), sign-in and audit logs",
        "Admin Block / Delete reaches the runtime: effective state = developer configuration AND admin state",
        "Legacy agents share a project identity; migrating changes the identity and role assignments do not transfer",
    ], theme="red", icon="managed-identity", src=[S_IDENT, S_ENTRA])
    c_a365 = Card(RW, "Microsoft Agent 365", [
        "Microsoft's enterprise control plane for AI agents; pillars: Registry, Access control, Visualization, Interoperability, Security",
        "Registry sync: every published Foundry agent appears automatically",
        "Autopilots: a blueprint from a hosted agent appears in the registry after admin approval; people hire instances in Teams",
        "Activity data needs licence + tenant consent + a365LoggingEnabled on the Foundry resource (default true once A365 is on; no per-project override)",
        "Residency: Foundry = the resource's Azure region; Agent 365 = Entra tenant storage location. Opt out per resource",
        "Hosted agents using Foundry hosting libraries export automatically; others need the Agent 365 SDK; allow agent365.svc.cloud.microsoft:443",
    ], theme="red", icon="m365", src=[S_A365, S_A365D])

    # ---- centre geometry (relative to y) driven by the cards so every arrow lands inside both blocks
    BH, b2_h = 96, 190
    oc_y = 112
    oa_y = oc_y + BH + 16
    sub1_y = 62
    sub1_h = oa_y + BH + 16 - sub1_y
    sub2_y = sub1_y + sub1_h + 18
    b2_y = sub2_y + 46
    b3_y = b2_y + b2_h + 16
    b1_y = b3_y + BH + 16
    sub2_h = b1_y + BH + 16 - sub2_y
    center_h = sub2_y + sub2_h + 22
    hD = c_def.h
    hE = max(c_ent.h, b2_y + 34 + 30)
    pur_y = hD + 40
    hP = max(c_pur.h, b1_y + BH / 2 + 34 - pur_y)
    a365_y = hE + 40
    hA = max(c_a365.h, b3_y + BH / 2 + 34 - a365_y)
    total_h = max(center_h, pur_y + hP, a365_y + hA)

    c_def.place(cv, 0, y)
    c_pur.place(cv, 0, y + pur_y, h=hP)
    c_ent.place(cv, rx0, y, h=hE)
    c_a365.place(cv, rx0, y + a365_y, h=hA)
    bx, bw = cx0 + 44, CW - 88
    with cv.panel(cx0, y, title="Microsoft Foundry", theme="gray", style="dotted", pad=16, title_size=24, w=CW, h=total_h):
        with cv.panel(cx0 + 22, y + sub1_y, title="Control Plane console (Foundry (new) portal)", theme="grape", style="solid", fill="soft",
                      pad=14, title_size=18, w=CW - 44, h=sub1_h):
            oc = Box(bw, "Operate > Compliance", h=BH, theme="grape", sub="Guardrail policies | Security posture tab | Data security and governance tab",
                     icon="policy", icon_pos="left", size=19, sub_size=14).place(cv, bx, y + oc_y)
            oa = Box(bw, "Operate > Assets > Agents", h=BH, theme="green", sub="Entra ID column | per-agent alerts: policy, security, evaluation",
                     icon="all-resources", icon_pos="left", size=19, sub_size=14).place(cv, bx, y + oa_y)
        with cv.panel(cx0 + 22, y + sub2_y, title="Your Foundry estate (subscription scope)", theme="blue", style="dotted", pad=14, title_size=18,
                      w=CW - 44, h=sub2_h):
            b2 = Box(bw, "Foundry agents", h=b2_h, theme="green", sub="prompt, workflow and hosted agents; published ones are agent applications; "
                     "each agent has its own blueprint + agent identity", icon="agent", icon_pos="left", size=19, sub_size=14).place(cv, bx, y + b2_y)
            b3 = Box(bw, "Foundry resource (Microsoft.CognitiveServices/accounts)", h=BH, theme="gray",
                     sub="a365LoggingEnabled + a365Status; the subscription is the scope of the Purview toggle", icon="resource-group", icon_pos="left",
                     size=19, sub_size=14).place(cv, bx, y + b3_y)
            b1 = Box(bw, "Model deployments", h=BH, theme="blue", sub="Foundry managed inference endpoints (/chat/completions); guardrail policies apply here",
                     icon="openai", icon_pos="left", size=19, sub_size=14).place(cv, bx, y + b1_y)
    lab = dict(label_size=13, label_wrap=140, label_pos="above")
    hlink(cv, c_def, oc, y + oc_y + BH / 2, "right", color=C_RED, sw=3, label="posture recommendations, jailbreak and prompt-attack alerts", label_dx=-12, **lab)
    hlink(cv, c_pur, b1, y + b1_y + BH / 2, "both", color="#c2255c", sw=3, label="AI interaction data out, data security policies in", label_dx=-12, **lab)
    hlink(cv, oa, c_ent, y + oa_y + BH / 2, "left", color=C_RED, sw=3, label="agent identity in the Entra ID column", label_dx=12, **lab)
    hlink(cv, b2, c_ent, y + b2_y + 34, "both", color=C_RED, sw=3, label="identity; Block / Delete state", label_dx=12, **lab)
    hlink(cv, b2, c_a365, y + b2_y + b2_h - 34, "both", color=C_RED, sw=3, label="registry sync, autopilots, activity data", label_dx=12, **lab)
    hlink(cv, b3, c_a365, y + b3_y + BH / 2, "both", color=C_RED, sw=3, label="licence + consent + logging flag", label_dx=12, **lab)

    # ---- positioning row
    y2 = y + total_h + 56
    p1 = Card(1000, "Foundry Control Plane", [
        "Designed for developers and AI engineers",
        "Deep observability, runtime controls, evaluation and fleet operations across AI applications and agents, from build to production",
        "Where: Foundry (new) portal, Operate + Manage",
    ], theme="grape", icon="foundry", src=[S_OVERVIEW])
    p2 = Card(1000, "Agent 365", [
        "Designed for IT and security administrators",
        "Registry, access control, identity governance and organization-wide policy enforcement across all agents in the tenant",
        "Where: Microsoft 365 admin center (Agent 365 registry) and Microsoft Entra",
        "= Both lean on the same Microsoft Entra, Defender and Purview foundations (azure.com product page, not Learn).",
    ], theme="red", icon="m365", src=[S_A365OV])
    t_sup = Table([("Foundry agent type", 200), ("Registry sync", 150), ("Autopilot publishing", 190), ("Activity data", 240)], [
        [("Prompt agent", "green"), CHECK, CROSS, CHECK],
        [("Hosted agent", "green"), CHECK, CHECK, "Using the Agent 365 SDK"],
    ], w=780, theme="red", size=15, title="Agent 365 support by Foundry agent type", title_size=20, align=["left", "center", "center", "left"])
    p1.place(cv, 0, y2)
    p2.place(cv, 1050, y2)
    t_sup.place(cv, 2100, y2)
    n_lic = Note(1100, "The Foundry integration page asks for at least one Microsoft 365 Copilot licence and Frontier programme enrolment. The Agent 365 "
                       "overview says: generally available for the Commercial segment since 2026-05-01, per-user licensing, at least one user with a qualifying "
                       "Agent 365 licence, works best with Microsoft E5. Check both before planning a rollout.", kind="warn",
                 title="Docs disagree: Agent 365 prerequisites", src=[S_A365, S_A365OV])
    n_lic.place(cv, 2100, y2 + t_sup.h + 20)
    return max(p1.bottom, p2.bottom, n_lic.bottom)


# ---------------------------------------------------------------------------------------------- 4. fleet monitoring and health
def _monitoring(cv, y0):
    y = _sec(cv, y0, "Fleet monitoring and health: how the console lights up",
             "The Control Plane reads the Application Insights resources that receive agent telemetry - no telemetry, no health scores")
    sw, g = 540, 125
    steps = [
        Card(sw, "Connect Application Insights", [
            "Manage > Project details > Connected resources",
            "Check for the AppInsights category; if missing: Add connection > Application Insights",
            "Per project; projects may share one resource or use separate ones (a governance choice)",
        ], theme="violet", icon="app-insights", src=[S_MONITOR]),
        Card(sw, "Emit OpenTelemetry", [
            "Agents log with OpenTelemetry GenAI semantic conventions",
            "Custom-code agents: instrument and send to the project's App Insights",
            "Platforms without App Insights support: OTel collector + Azure Monitor exporter",
        ], theme="orange", icon="otel", src=[S_CUSTOM]),
        Card(sw, "Run the agent", [
            "Only runs after the configuration are captured",
            "Past runs are not backfilled",
        ], theme="green", icon="agent", src=[S_MANAGE]),
        Card(sw, "Wait", [
            "Metrics appear after a few minutes",
            "Allow up to 15 minutes after the first post-configuration run",
        ], theme="gray", icon="scheduler", src=[S_MANAGE]),
        Card(sw, "Read the console", [
            "Operate > Overview: subscription-wide metrics; pick a project to scope",
            "Operate > Assets > Agents: error rate, estimated cost, token usage, runs",
            "Cost columns also need Cost Management Reader",
        ], theme="grape", icon="dashboard", src=[S_MONITOR]),
    ]
    _, sb = row(cv, 0, y, steps, gap=g)
    for i, c in enumerate(steps):
        numbered(cv, c.x + c.w - 26, c.y + 26, i + 1, theme=["violet", "orange", "green", "gray", "grape"][i], d=34, size=19)
        if i:
            connect(cv, steps[i - 1], c, a_side="right", b_side="left", sw=3, color=C_GRAY)
    y2 = sb + 50
    cw = (W - 3 * 40) / 4
    k1 = Card(cw, "What the console computes", [
        "Fleet health metrics: active agents, run completion rates, error trends",
        "Cost and performance tracking: token usage, budget consumption, resource efficiency",
        "Anomaly detection: cost spikes, performance degradation, emerging issues",
        "Drill-down: from fleet metrics to a single agent's traces and logs",
        "! Resources without Application Insights have no health metrics, cost tracking or drill-down traces",
    ], theme="violet", icon="metrics", src=[S_MONITOR])
    k2 = Card(cw, "Roles needed to view", [
        "Read access to the project and the subscription you view",
        "Log Analytics Reader (or higher) on the agent's Application Insights resource",
        "Cost Management Reader - without it cost data is missing",
        "Protected Log Analytics tables also need Privileged Monitoring Data Reader (monitoring dashboard how-to)",
    ], theme="red", icon="managed-identity", src=[S_MONITOR, S_DASH])
    k3 = Card(cw, "Monitor and improve", [
        "Correlate alerts, evaluation results and traces to find problems quickly",
        "Continuous evaluation covers quality and risk dimensions (chips below); default cap max_hourly_runs = 100",
        "AI Red Teaming Agent and cluster analysis: automated vulnerability probing, error root-cause discovery",
        "Recommendations: prompt refinements, model version upgrades, configuration changes",
    ], theme="violet", icon="bug", src=[S_OVERVIEW, S_DASH])
    k4 = Note(cw, "No metrics: is App Insights connected to the project, did the agent run after setup, wait up to 15 minutes. "
                  "Agent missing from Assets: supported platform? RBAC on the hosting resource? right subscription? custom agent registered? "
                  "Cost missing: Cost Management Reader on the subscription. Different users see different agents depending on their access.",
              kind="tip", title="If something is missing", src=[S_MANAGE, S_MONITOR])
    _, kb = row(cv, 0, y2, [k1, k2, k3], gap=40)
    k4.place(cv, k3.right + 40, y2)
    chips = ChipFlow(["task adherence", "intent resolution", "tool call success", "groundedness", "sensitive data leakage", "jailbreak",
                      "cross-domain prompt injection (XPIA)"], 2 * cw + 40, gap=10, theme="violet", size=15)
    cv.text(k1.x, kb + 22, "Risk dimensions continuous evaluation can cover:", size=16, color=C_GRAY)
    chips.place(cv, k1.x, kb + 52)
    return max(kb + 52 + chips.h, k4.bottom)


# ---------------------------------------------------------------------------------------------- 5. managing agents at scale
def _manage(cv, y0):
    y = _sec(cv, y0, "Managing agents at scale: inventory, status and the ladder for taking an agent offline",
             "Operate > Assets > Agents lists what you can reach in the selected subscription; Start / Stop / Block live under Update status")
    # ---- inventory table + side pane
    t_inv = Table([("Column", 200), ("What it shows", 700), ("Platforms", 150), ("Needs observability", 160)], [
        ["Name", "Name of the agent or agentic resource", "All", ""],
        ["Source", "Platform where it was discovered", "All", ""],
        ["Project", "Foundry project; for custom agents the project where it was registered", "FoundryCustom", ""],
        ["Status", "Running, Stopped, Blocked or Unknown", "All", ""],
        ["Version", "Version of the agent asset", "Foundry", ""],
        ["Published as", "Whether it was published as an agent application (own invocation endpoint)", "Foundry", ""],
        ["Error rate", "Failed versus successful runs, last month", "All", CHECK],
        ["Estimated cost", "Token-based estimate of agent executions, last month", "Foundry", CHECK],
        ["Token usage", "Estimated tokens consumed by runs, last month", "Foundry", CHECK],
        ["Runs", "Number of executions, last month", "All", CHECK],
        ["Monitoring features", "Number of monitoring features enabled on the agent", "Foundry", ""],
        ["Entra ID", "Entra Agent ID application + object ID of the agent identity", "Foundry", ""],
    ], w=1210, theme="green", size=15, title="Operate > Assets > Agents: inventory columns", title_size=22, first_col_theme="green",
        align=["left", "left", "left", "center"])
    t_inv.place(cv, 0, y)
    rx = t_inv.right + 50
    rw = W - rx
    side = Card(rw, "Select an agent: side pane and Traces", [
        "Active alerts: policy, security and evaluation alerts grouped by severity",
        "Activity: error rate over time, total runs, token usage",
        "Traces tab: one entry per call, with Trace ID and Conversation ID",
        "Traces live in Application Insights; conversations live in the Foundry service",
        "Custom agents need extra instrumentation to show tool and LLM spans",
    ], theme="violet", icon="monitor", src=[S_MANAGE, S_MONITOR])
    side.place(cv, rx, y)
    t_perm = Table([("Role", 150), ("Scope", 430), ("What you can do", 560)], [
        [("Reader", "green"), "Resource, resource group or subscription", "View agent inventory and traces"],
        [("Contributor", "yellow"), "Resource, resource group or subscription", "View and perform lifecycle operations (start, stop, block)"],
        [("Owner", "red"), "Resource, resource group or subscription", "Full management, including permissions"],
    ], w=rw, theme="red", size=15, title="Permission model (minimum roles)", title_size=20)
    t_perm.place(cv, rx, side.bottom + 28)
    n_cust = Note(rw, "Custom roles with equivalent permissions also work. Discovery follows your role assignments across the resources of the "
                      "selected subscription, so two people can see different agents. Estimated cost is token-based, not an invoice.", kind="info",
                  title="Good to know", src=[S_MANAGE])
    n_cust.place(cv, rx, t_perm.bottom + 24)
    y2 = max(t_inv.bottom, n_cust.bottom) + 60

    # ---- lifecycle matrix
    t_life = Table([("Platform", 150), ("Agent type", 190), ("Published", 100), ("Action", 150), ("What happens", 560)], [
        ["Foundry", "PromptWorkflow", "No", ("None", "red"), "No dedicated deployment (uses the project endpoint); lifecycle tied to the project - to stop it you must delete it"],
        ["Foundry", "Hosted", "No", ("Start / Stop", "green"), "Stopping stops the deployment; attached compute is deallocated"],
        ["Foundry", "PromptWorkflowHosted", "Yes", ("Start / Stop", "green"), "Stopping a published agent stops its deployment and deallocates compute"],
        ["Azure SRE Agent", "n/a", "n/a", ("Start / Stop", "green"), "Supported"],
        ["Azure Logic Apps", "n/a", "n/a", ("Start / Stop", "green"), "Stopping the Logic Apps resource stops ALL workflows associated with it"],
        ["Custom (legacy)", "n/a", "n/a", ("Block / Unblock", "indigo"), "No access to the infrastructure, so no start / stop; requests are blocked at the gateway while the agent keeps running"],
    ], w=1150, theme="green", size=15, title="Lifecycle operations by platform", title_size=22, first_col_theme="green")
    t_life.place(cv, 0, y2)
    sem = Card(1150, "What Stop and Block really do", [
        "Stop deprovisions the agent's infrastructure and prevents new runs; it does not terminate runs already in progress",
        "Stop and Block can take a few minutes: refresh the Assets pane to verify the new Status",
        "Blocked agents keep running in their own infrastructure but cannot take incoming requests",
        "Unknown status: the source platform is unavailable or the agent is not reporting - check the platform, a custom agent's infrastructure and "
        "its Application Insights logs, then try stopping and restarting",
    ], theme="gray", icon="gear", src=[S_MANAGE])
    sem.place(cv, 0, t_life.bottom + 26)
    n_q = Note(1150, "Learn documents Stop, Block (custom agents), Entra / Agent 365 Block and Delete, and disabling the agent endpoint. "
                     "'Quarantine' is only mentioned aloud in a conference session (video-sourced, not Learn), so do not expect a Quarantine button.",
               kind="gotcha", title="'Quarantine' is not a documented Control Plane action")
    n_q.place(cv, 0, sem.bottom + 22)
    n_ext = Note(1150, "Block only works for custom agents because their traffic crosses the gateway. External agents are never proxied, so Foundry cannot "
                       "block them; unpublished prompt and workflow agents have no Stop action either.", kind="warn", title="Where the Control Plane cannot reach",
                 src=[S_EXTERNAL, S_MANAGE])
    n_ext.place(cv, 0, n_q.bottom + 22)

    # ---- escalation ladder
    lx = t_life.right + 60
    lw = W - lx
    cv.text(lx, y2, "Take an agent offline: start with the lightest control that works", size=22, color="#364fc7")
    rungs = [
        ("green", "Stop it", "Operate > Assets > select the agent > Update status > Stop", [
            "Foundry published or hosted agents, Azure SRE Agent, Logic Apps agent loops; minimum role Contributor",
            "Deprovisions the infrastructure and prevents new runs; existing runs are not terminated",
        ]),
        ("indigo", "Block it (custom agents only)", "Update status > Block", [
            "Requests are blocked at the APIM gateway while the agent keeps running; minimum role Contributor",
            "Works only because custom-agent traffic crosses the gateway; registration is deprecated (ends 2027-04-30)",
        ]),
        ("red", "Block it in Entra or Agent 365 (identity level)", "Entra: Disable in this tenant  |  Agent 365: Block", [
            "Entra AI Administrator or Global Administrator; agent owners and sponsors for their own identities; activate via PIM if used",
            "Takes up to 10 minutes; Foundry enforces it only for agents created on or after 2026-10-23 16:00 UTC; Unblock reverses it",
        ]),
        ("orange", "Emergency: intervene on the Azure resource", "disable the agent endpoint, or stop the application's deployments", [
            "Foundry agent: disable / enable endpoint (Foundry User); agent application: stop / start deployments (Foundry Owner)",
            "Via Microsoft 365 admin center, Foundry portal or REST / CLI; affects every consumer of the resource, even in other tenants",
        ]),
        ("gray", "Last resort: delete", "Foundry agent delete, or governance Delete / Permanently delete", [
            "Delete a Foundry agent with Foundry User; governance Delete is reversible (Restore), Permanently delete is unrecoverable",
            "Prefer reversible disablement; governance deletion does not delete the Azure resources",
        ]),
    ]
    cy = y2 + 52
    prev = None
    for i, (th, title, sub, items) in enumerate(rungs):
        c = Card(lw - 70, title, items, theme=th, subtitle=sub, src=[S_ENTRA] if i in (2, 3, 4) else [S_MANAGE] if i == 0 else [S_CUSTOM] if i == 1 else [])
        c.place(cv, lx + 70, cy)
        numbered(cv, lx + 28, c.y + 34, i + 1, theme=th, d=42, size=22)
        if prev is not None:
            arrow(cv, [(lx + 28, prev.y + 34 + 25), (lx + 28, c.y + 34 - 25)], color=C_GRAY, sw=3, dash="dashed")
        prev = c
        cy = c.bottom + 30
    cv.text(lx, cy - 8, "Lightest -> most drastic. Reverse the identity-level and endpoint actions before you expect an agent to run again.", size=15, color=C_GRAY)
    return max(n_ext.bottom, cy + 20)


# @@ZONES@@

# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry Control Plane",
                                f"One role-aware console to see, govern and secure the agent fleet - inventory, observability, compliance, security  |  Foundry (new) portal only  |  facts {AS_OF}",
                                icon="foundry", w=W)
    y = _pillars(cv, bottom + 50)
    y = _hero(cv, y + 70)
    y = _integration(cv, y + 90)
    y = _monitoring(cv, y + 90)
    y = _manage(cv, y + 90)
    sources(cv, 0, y + 60, [S_OVERVIEW, S_MONITOR, S_MANAGE, S_CUSTOM], w=W, cols=4)
