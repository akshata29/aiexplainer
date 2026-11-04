"""Operate: monitor, alert, respond, learn - signal map, alert catalogue, on-call flow, trace-to-dataset loop."""
import math

from generator.xd import *

META = dict(
    id="monitoring-alerting-incident", title="Monitoring, alerting and incident response", section="6", order=3,
    description="The five-ring signal map (resource vs project scope), model and agent metrics, alert catalogue, on-call flow "
                "and the trace-to-dataset feedback loop for operating Foundry workloads.",
    tags=["monitoring", "alerting", "incident", "observability", "app-insights", "on-call"],
)

W = 3000


# ---------------------------------------------------------------------------------------------- helpers
def stack_panel(cv, x, w, cy, items, theme, *, size=15, fill="soft", pad=12, gap=8, dash="dotted", min_h=0):
    """Dotted panel with one pill per row, vertically centred on cy. items = [(label, icon_or_None), ...]."""
    chips = [Chip(lbl, theme=theme, size=size, icon=ic, w=w - 2 * pad, fill=fill) for lbl, ic in items]
    for c in chips:
        if c.w > w - 2 * pad + 1:
            cv.warn(f"chip too wide for its panel: {c.label!r} ({c.w:.0f} > {w - 2 * pad})")
    H = max(2 * pad + sum(c.h for c in chips) + gap * (len(chips) - 1), min_h)
    top = cy - H / 2
    with cv.panel(x, top, theme=theme, style=dash, fill="none", pad=pad, w=w, h=H) as p:
        yy = p.iy
        for c in chips:
            c.place(cv, p.ix, yy)
            yy += c.h + gap
    return p


def stack_height(items, w, size=15, pad=12, gap=8):
    chips = [Chip(lbl, size=size, icon=ic, w=w - 2 * pad) for lbl, ic in items]
    return 2 * pad + sum(c.h for c in chips) + gap * (len(chips) - 1)


def col_label(cv, x, w, y, text, color="#495057"):
    cv.text(x, y, text, size=18, color=color, align="center", w=w)


def tile(cv, x, y, w, h, title, note, theme, pts, warn=None):
    """Dashboard tile: title, tiny illustrative sparkline, optional red threshold line."""
    th = THEMES[theme]
    with cv.group():
        r = cv.rect(x, y, w, h, stroke=th.stroke, fill="#ffffff", style="solid", sw=2)
        cv.text(x + 14, y + 10, title, size=18, color=th.deep)
        sx0, sx1, sy0, sy1 = x + 16, x + w - 16, y + 44, y + h - 62
        n = len(pts) - 1
        cv.poly([(sx0 + (sx1 - sx0) * i / n, sy1 - (sy1 - sy0) * v) for i, v in enumerate(pts)], kind="line",
                stroke=th.stroke, sw=2, curved=True)
        cv.line((sx0, sy1 + 4), (sx1, sy1 + 4), stroke="#adb5bd", sw=1)
        cv.text(x + 14, y + h - 54, note, size=14, color="#c92a2a" if warn else "#495057", wrap=w - 28)
    cv.register(f"tile:{title}", x, y, w, h)
    return r


def onion(cv, cx, cy, themes):
    """Flattened 'signal onion': concentric rings, outer = ring 1."""
    rx, ry = [230, 190, 150, 110, 70], [50, 42, 34, 26, 18]
    for i, th in enumerate(themes):
        t = THEMES[th]
        cv.ellipse(cx - rx[i], cy - ry[i], 2 * rx[i], 2 * ry[i], stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0)
    for i, th in enumerate(themes):
        nx = cx + ((rx[i] + rx[i + 1]) / 2 if i + 1 < len(rx) else 0)
        numbered(cv, nx, cy, i + 1, theme=th, d=30, size=17)


def ring_arrow(cv, cx, cy, rx, ry, a0, a1, boxes, *, label=None, label_size=17, label_off=30, color=INK, sw=3, margin=10):
    """Arrow that follows an ellipse from angle a0 to a1 (degrees, 0 = right, 90 = down), trimmed where it meets the boxes."""
    n = max(2, int(abs(a1 - a0) / 3))
    pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
           for i in range(n + 1)]

    def inside(p):
        return any(b.x - margin <= p[0] <= b.x + b.w + margin and b.y - margin <= p[1] <= b.y + b.h + margin for b in boxes)

    keep = [p for p in pts if not inside(p)]
    cv.poly(keep, kind="arrow", stroke=color, sw=sw, end_head="arrow", curved=True)
    if label:
        mx, my = keep[len(keep) // 2]
        gx, gy = (mx - cx) / rx ** 2, (my - cy) / ry ** 2
        gl = math.hypot(gx, gy) or 1
        nx, ny = gx / gl, gy / gl
        tw, th_ = text_size(label, label_size)
        lx = mx + nx * label_off - (tw / 2 if abs(nx) < 0.35 else (0 if nx > 0 else tw))
        ly = my + ny * label_off - th_ / 2
        cv.text(lx, ly, label, size=label_size, color="#495057")


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Operate: monitor, alert, respond, learn",
                                "Where every Foundry signal lives, what to alert on, how an incident flows - and how production traces feed the next evaluation",
                                w=W)
    # key for stickers
    kx = 1700
    cv.text(kx, 8, "Key:", size=16, color="#495057")
    draw_badge(cv, kx + 50, 8, "preview")
    cv.text(kx + 135, 8, "preview as documented", size=15)
    draw_badge(cv, kx + 360, 8, "suggested")
    cv.text(kx + 465, 8, "our synthesis, not in the docs", size=15)
    draw_badge(cv, kx + 800, 8, "docs disagree")
    cv.text(kx + 955, 8, "conflicting Learn pages", size=15)
    cv.text(kx + 50, 42, "Time-sensitive facts are as of 2026-11-03", size=15, color="#495057")

    y = bottom + 56

    # ================================================================== 1. SIGNAL MAP
    section_header(cv, 0, y, "1   The signal map: five rings, from what Microsoft tells you to what your users feel", size=32,
                   sub="Read each lane left to right: what to watch -> where it is collected -> where you look -> which alert (#) in the catalogue catches it")
    onion(cv, 2740, y + 26, ["gray", "blue", "green", "cyan", "violet"])
    cv.text(2330, y + 8, "outer ring: what Microsoft tells you\ninner ring: what your users feel", size=14, color="#495057", align="right", w=270)
    y += 100
    C_HEAD, C_SIG, C_STORE, C_VIEW, C_ALERT = (0, 300), (350, 960), (1380, 430), (1880, 600), (2540, 460)
    col_label(cv, C_SIG[0], C_SIG[1], y, "What to watch", "#1864ab")
    col_label(cv, C_STORE[0], C_STORE[1], y, "Collected in", "#1864ab")
    col_label(cv, C_VIEW[0], C_VIEW[1], y, "Look here", "#1864ab")
    col_label(cv, C_ALERT[0], C_ALERT[1], y, "Alerts (# = catalogue row)", "#1864ab")
    y += 34

    lanes = [
        dict(n=1, theme="gray", icon="service-health", title="Platform health", sub="what Microsoft tells you",
             bullets=[
                 "Azure Service Health: service issues, planned maintenance, health and security advisories",
                 "Service Health alert scoped to subscriptions + regions + services: Azure OpenAI, Foundry Models, Foundry Agent Service",
                 "Resource Health on Foundry, Cosmos DB, Storage, AI Search - wire alerts: Microsoft does not notify you when a zone is down",
                 "status.azure.com + the Foundry Known issues page (Agent Service: none active when read, 2026-11-03)",
                 "Notification Center: Defender for Cloud high-severity alerts, Azure Policy and guardrail compliance, evaluation and training job results",
                 "Retirement notices arrive as Service Health advisories + email (see the FinOps canvas)",
             ],
             stores=[("Azure Service Health", "service-health"), ("Azure Resource Health", "service-health"),
                     ("Defender for Cloud + Azure Policy", "defender")],
             views=[("Azure portal > Service Health > Health alerts", "service-health"),
                    ("Foundry Notification Center (bell icon)", "alerts"),
                    ("status.azure.com + Known issues page", "learn")],
             alerts=["#1 Platform incident", "#14 Config / policy"]),
        dict(n=2, theme="blue", icon="openai", title="Model deployments", sub="resource scope - auto-collected, no setup",
             bullets=[
                 "ModelRequests split by StatusCode, deployment, model, version, region and API - where 429s and 5xx show up",
                 "ModelAvailabilityRate = (calls - server errors) / calls, where an error is HTTP 500 or higher",
                 "TimeToResponse and NormalizedTimeBetweenTokens: streaming latency and speed (PTU, PTU-managed)",
                 "InputTokens, OutputTokens, TotalTokens, TokensCacheMatchRate, ProvisionedConsumedTokens",
                 "ProvisionedUtilization = PTUs consumed / PTUs deployed x 100 - at 100% or more, requests get 429",
                 "Spillover: Azure OpenAI Requests split by IsSpillover; opt-in diagnostic logs RequestResponse, Trace, Audit",
             ],
             stores=[("Azure Monitor platform metrics ('Models')", "monitor"),
                     ("Diagnostic settings (opt-in logs)", "log-analytics")],
             views=[("Foundry: Models + endpoints > deployment > Metrics", "foundry"),
                    ("Metrics explorer, Workbooks, Grafana, Power BI", "workbooks"),
                    ("Log Analytics (KQL on AzureDiagnostics)", "log-analytics")],
             alerts=["#2 Model errors (5xx)", "#3 Availability", "#4 Throttling (429)", "#5 PTU saturation", "#6 Latency"]),
        dict(n=3, theme="green", icon="agent", title="Agent runtime", sub="project scope - needs Application Insights",
             bullets=[
                 "Agent Monitor dashboard (Build > agent > Monitor): token usage, latency, run success rate, evaluation scores",
                 "OpenTelemetry tracing of LLM calls, tool invocations and agent decisions - off until App Insights is connected",
                 "Continuous evaluation on sampled live responses + scheduled evaluation on a dataset",
                 "Control Plane > Operate: fleet health, alerts, cost, anomaly detection (new portal)",
                 "Hosted agents: console and system logs with azd ai agent monitor (crash loops, auth errors, timeouts)",
                 "Insights (preview): an LLM judge scans production traces for recurring problems",
             ],
             stores=[("Application Insights (OTel traces)", "app-insights"), ("Hosted-agent log stream (azd)", "azd")],
             views=[("Agent Monitor dashboard", "dashboard"),
                    ("Control Plane > Operate (Overview, Assets > Agents)", "foundry"),
                    ("Trace drill-down + Insights (preview)", "app-insights"),
                    ("azd ai agent monitor", "azd")],
             alerts=["#7 Agent success", "#8 Agent latency", "#11 Hosted capacity"]),
        dict(n=4, theme="cyan", icon="apim", title="Dependencies and gateway", sub="your Azure resources + APIM",
             bullets=[
                 "Cosmos DB, AI Search, Storage: Azure Monitor metrics and Resource Health alerts",
                 "Azure Monitor baseline alerts for AI services and AI Search; Defender for Azure Cosmos DB and Defender for AI services",
                 "APIM AI gateway: llm-emit-token-metric (custom dimensions), prompt + completion + token logging, analytics workbook",
                 "Application Insights availability tests on agent endpoints from several geographies",
                 "Quota headroom: Usages API (consumption vs limit) and Model Capacities API (PTU capacity)",
                 "Azure Firewall SNAT and firewall health",
             ],
             stores=[("Azure Monitor + Resource Health", "monitor"), ("APIM -> App Insights / Azure Monitor", "apim"),
                     ("Usages + Model Capacities APIs", "quotas")],
             views=[("Azure Monitor alerts + Resource Health", "alerts"),
                    ("APIM built-in dashboard / analytics workbook", "apim"),
                    ("Foundry: Manage > Quota", "quotas")],
             alerts=["#12 Dependency health", "#13 Cost / budget"]),
        dict(n=5, theme="violet", icon="content-safety", title="Quality, safety and feedback", sub="project scope + your users",
             bullets=[
                 "Continuous evaluation (sampled) and scheduled evaluation on test datasets to detect drift",
                 "Scheduled red teaming; recurring evaluations and red-team scans are preview items",
                 "Azure Monitor alerts when outputs fail quality thresholds or produce harmful content",
                 "End-user and builder feedback (preview): OTel event gen_ai.evaluation.result - binary 0/1 or Likert 1-5",
                 "Query it in App Insights: customEvents where name == gen_ai.evaluation.result",
             ],
             stores=[("Foundry project: evaluation runs", "foundry"), ("Application Insights: customEvents", "app-insights")],
             views=[("Agent Monitor: evaluation + red-team tiles", "dashboard"),
                    ("Build > Evaluations > Recurring Configs", "foundry"),
                    ("App Insights KQL / Workbooks", "workbooks")],
             alerts=["#9 Quality drift", "#10 Safety"]),
    ]
    for ln in lanes:
        card = Card(C_SIG[1], None, ln["bullets"], theme=ln["theme"], fill="hatch")
        hs = max(card.h, stack_height(ln["stores"], C_STORE[1]), stack_height(ln["views"], C_VIEW[1]),
                 stack_height([(a, None) for a in ln["alerts"]], C_ALERT[1]), 150)
        card.place(cv, C_SIG[0], y, h=hs)
        hdr = Box(C_HEAD[1], ln["title"], h=hs, theme=ln["theme"], sub=ln["sub"], icon=ln["icon"], icon_pos="top",
                  fill="solid", size=22, sub_size=15, icon_size=44).place(cv, C_HEAD[0], y)
        numbered(cv, 24, y + 24, ln["n"], theme=ln["theme"], d=34, size=20)
        cy = y + hs / 2
        p_store = stack_panel(cv, C_STORE[0], C_STORE[1], cy, ln["stores"], ln["theme"])
        p_view = stack_panel(cv, C_VIEW[0], C_VIEW[1], cy, ln["views"], ln["theme"])
        p_alert = stack_panel(cv, C_ALERT[0], C_ALERT[1], cy, [(a, None) for a in ln["alerts"]], ln["theme"], fill="solid",
                              dash="dashed")
        connect(cv, card, p_store, a_side="right", b_side="left", gap=4)
        connect(cv, p_store, p_view, a_side="right", b_side="left", gap=4)
        connect(cv, p_view, p_alert, a_side="right", b_side="left", gap=4)
        y += hs + 34

    cv.text(0, y + 2, "Two scopes, two kinds of SLO - pick the scope that matches what you are measuring", size=22, color="#364fc7")
    sc1 = Card(1480, "Resource scope: the Foundry resource", [
        "Token consumption, model latency, request counts and error rates across all projects",
        "Azure Monitor platform metrics + diagnostic settings (logs to Log Analytics, Storage or Event Hubs)",
        "Use it for model SLOs: availability, 429 rate, latency, PTU utilization",
    ], theme="blue", icon="foundry", src=[("Foundry architecture - monitoring scopes", learn("concepts/architecture"))])
    sc2 = Card(1480, "Project scope: each Foundry project", [
        "Evaluation run outcomes, agent invocation counts and file-operation activity",
        "Agent health, cost and quality come from the project's connected Application Insights",
        "Use it for agent SLOs: run success rate, agent latency, evaluation scores, tool failures",
    ], theme="green", icon="agent", src=[("Foundry architecture - monitoring scopes", learn("concepts/architecture"))])
    sr, sb = row(cv, 0, y + 40, [sc1, sc2], gap=40)
    y = sb + 70

    # ================================================================== 2. MODEL METRICS DETAIL
    section_header(cv, 0, y, "2   Ring 2 in detail: model deployment metrics and logs (resource scope)", size=32,
                   sub="Auto-collected per deployment. In Metrics explorer set Resource types = Foundry Tools.")
    y += 100
    t_metrics = Table(
        [("Metric (REST name)", 330), ("Meaning", 650), ("Dimensions and notes", 520)],
        [
            [("ModelRequests", "blue"), "Calls to the inference API",
             "StatusCode, ModelDeploymentName, ModelName, ModelVersion, Region, ApiName, OperationName, StreamType"],
            [("ModelAvailabilityRate", "blue"), "(total calls - server errors) / total calls; an error is HTTP 500 or higher", "Aggregations: min, avg, max"],
            [("TimeToResponse", "blue"), "Time to first response for streaming calls, measured at the API gateway - an approximation that excludes client latency",
             "PTU and PTU-managed deployments"],
            [("NormalizedTimeBetweenTokens", "blue"), "Token generation speed for streaming calls", "PTU and PTU-managed deployments"],
            [("InputTokens / OutputTokens / TotalTokens", "blue"), "Token counts", "Per deployment and region; PTU, PTU-managed and standard"],
            [("TokensCacheMatchRate", "blue"), "Percentage of prompt tokens served from cache", "PTU deployments"],
            [("ProvisionedUtilization", "blue"), "(PTUs consumed / PTUs deployed) x 100; at 100% or more requests get 429",
             "Also shown as 'Provisioned-managed utilization V2' in the Azure OpenAI metric category"],
            [("ProvisionedConsumedTokens", "blue"), "Total tokens minus cached tokens", "PTU deployments"],
            [("Audio input / output tokens", "blue"), "Audio token counts", "PTU-managed deployments"],
            [("Spillover view", "blue"), "Azure OpenAI Requests split by ModelDeploymentName + StatusCode + IsSpillover", "Use IsSpillover to see requests that spilled over"],
        ], w=1500, theme="blue", size=14, head_size=15, title="Metrics collected with no configuration", title_size=22)
    t_metrics.place(cv, 0, y)

    dl = Card(700, "Diagnostic logs (opt-in, per resource)", [
        "Categories: RequestResponse, Trace, Audit; the diagnostic-logging page also lists Azure OpenAI Request Usage and AllMetrics",
        "Destinations: Log Analytics (KQL), Azure Storage (insights-logs-<category> containers, PT1H.json blobs), Event Hubs",
        "KQL: AzureDiagnostics where ResourceProvider == MICROSOFT.COGNITIVESERVICES; Category == RequestResponse for percentiles by ResultSignature",
        "Log Analytics ingestion costs money - collect only the categories you need",
        "Portal views: Models + endpoints > deployment > Metrics, link to Cost analysis; Azure Monitor Workbooks, Grafana, Power BI",
    ], theme="violet", icon="log-analytics", src=[("Diagnostic logging", learn("how-to/diagnostic-logging"))])
    dl.place(cv, 1560, y)
    lag = Table([("Signal", 300), ("Typical delay", 340)], [
        ["Cost data (Cost Management)", "about 5 hours"],
        ["Diagnostic logs", ("15 minutes to 2 hours", "yellow")],
        ["App Insights spans (traces)", "30 to 90 seconds"],
        ["Notification Center", "in-app only, not a paging channel"],
    ], w=640, theme="gray", size=14, head_size=15, title="How fresh is each signal?", title_size=20)
    lag.place(cv, 1560 + 700 + 40, y)
    n_lag = Note(640, "monitor-models says logs can take up to 15 minutes; diagnostic-logging says up to two hours.",
                 kind="warn", title="Docs disagree")
    n_lag.place(cv, lag.x, lag.bottom + 20)
    n_cat = Note(1500, "Two metric categories exist: 'Azure OpenAI' (legacy, Azure OpenAI models only) and 'Models' (all models, including DeepSeek and Phi). The docs recommend switching to the new 'Models' set. "
                       "The model router has its own monitoring page.",
                 kind="info", title="Pick the 'Models' category",
                 src=[("Monitor Foundry Models", learn("foundry-models/how-to/monitor-models")),
                      ("Monitor model router", learn("openai/how-to/monitor-model-router"))])
    n_cat.place(cv, 0, t_metrics.bottom + 24)
    rt = Table([("You need to", 700), ("Role", 740)], [
        ["View metrics", "Monitoring Reader"],
        ["Create diagnostic settings / alert rules", "Monitoring Contributor"],
        ["Connect App Insights to the project", "Foundry Account Owner or Foundry Owner"],
        ["View traces", "Log Analytics Reader, Monitoring Reader or Reader"],
        ["Read protected trace tables", "Privileged Monitoring Data Reader"],
        ["Control Plane cost + App Insights views", "Cost Management Reader + Log Analytics Reader"],
        ["Insights: user and project identity", "Monitoring Reader on App Insights"],
        ["View quota", "Cognitive Services Usages Reader"],
    ], w=1440, theme="red", size=14, head_size=15, title="Roles for monitoring", title_size=20)
    rt.place(cv, 1560, max(dl.bottom, n_lag.bottom) + 30)
    y = max(n_cat.bottom, rt.bottom) + 70

    # ================================================================== 3. AGENT RUNTIME
    section_header(cv, 0, y, "3   Ring 3 in detail: the agent runtime (project scope)", size=32,
                   sub="Agent health, cost and quality live in the project's connected Application Insights - no App Insights, no health metrics or drill-down in Control Plane")
    y += 100
    with cv.panel(0, y, title="Agent Monitor dashboard", sub="Build > select the agent > Monitor   |   illustrative layout, not real data", theme="violet",
                  style="solid", fill="soft", pad=22, title_size=26, sub_size=15, w=900) as dash:
        tw_, th_ = 400, 190
        tx0, ty0 = dash.ix, dash.iy + 4
        tile(cv, tx0, ty0, tw_, th_, "Token usage", "Tokens per run and over time", "violet", [0.2, 0.35, 0.3, 0.5, 0.45, 0.7, 0.65, 0.8])
        tile(cv, tx0 + tw_ + 24, ty0, tw_, th_, "Latency", "Over 10 s may mean throttling, complex tool calls or network", "violet",
             [0.3, 0.25, 0.4, 0.35, 0.8, 0.9, 0.5, 0.4], warn=True)
        tile(cv, tx0, ty0 + th_ + 24, tw_, th_, "Run success rate", "Below 95% warrants investigation", "violet",
             [0.9, 0.92, 0.88, 0.9, 0.6, 0.55, 0.85, 0.9], warn=True)
        tile(cv, tx0 + tw_ + 24, ty0 + th_ + 24, tw_, th_, "Evaluation scores + red team", "Scores on sampled outputs and red-team results", "violet",
             [0.6, 0.65, 0.62, 0.7, 0.68, 0.72, 0.7, 0.74])
        yy = ty0 + 2 * th_ + 48
        c1 = Chip("Recurring evaluations (preview)", theme="orange", size=15).place(cv, tx0, yy)
        c2 = Chip("Red team scans (preview)", theme="orange", size=15).place(cv, tx0 + c1.w + 12, yy)
        c3 = Chip("Alerts (preview): latency, token usage, evaluation scores, red-team findings", theme="orange", size=15).place(cv, tx0, yy + c1.h + 10)
    dash_bottom = dash.bottom
    dash_src = cv.text(0, dash_bottom + 8, "Learn: Monitor agents dashboard", size=12, color=LINK,
                       link=learn("observability/how-to/how-to-monitor-agents-dashboard"))

    gx, gw, gg = 960, 640, 40
    ev = Card(gw, "Continuous and scheduled evaluation", [
        "Continuous: EvaluationRule + ContinuousEvaluationRuleAction(eval_id, max_hourly_runs=100) on RESPONSE_COMPLETED, filtered by agent name",
        "Samples live traffic: Random or Intelligent sampling",
        "Scheduled: fixed schedule on a dataset (portal); the JS/TS SDK supports continuous only",
        "Project managed identity needs Foundry User",
        "Portal: Build > Evaluations > Recurring Configs; verify in the charts and the runs list ('Completed')",
    ], theme="violet", icon="foundry", badge="preview", src=[("Monitor agents dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard"))])
    cp = Card(gw, "Control Plane > Operate (new portal only)", [
        "Overview: fleet health scores, alert summaries, active agents, error rates, compliance",
        "Assets > Agents: inventory, per-agent Active alerts + Activity (error rate, runs, tokens)",
        "Cost and performance tracking, anomaly detection (cost spikes, degradation), drill-down to traces",
        "Watches Foundry agents (prompt, workflow, hosted), Azure SRE Agent, Logic Apps agent loops and registered custom agents",
        "Needs OTel GenAI semantic conventions + App Insights per project",
    ], theme="grape", icon="foundry", src=[("Monitoring across the fleet", learn("control-plane/monitoring-across-fleet"))])
    tr = Card(gw, "Tracing", [
        "OpenTelemetry traces to App Insights: LLM calls, tool invocations, agent decisions",
        "Frameworks: LangChain, LangGraph, OpenAI Agents SDK, Microsoft Agent Framework",
        "Off by default - connect App Insights (Foundry Account Owner or Foundry Owner)",
        "Stored per App Insights retention; ingestion lag 30 to 90 s",
        "! Traces may contain personal data; Log Analytics Reader exposes it",
    ], theme="violet", icon="app-insights", src=[("Trace data", learn("observability/concepts/trace-data"))])
    hl = Card((3 * gw + 2 * gg - gg) / 2, "Hosted-agent logs", [
        "azd ai agent monitor: console stdout/stderr; --follow; --tail 1-300 (default 50); --session-id; --user-identity",
        "--type system shows container lifecycle, crashes and restart loops",
        "Listening on 0.0.0.0:8088 = healthy; AuthenticationError = RBAC of the Entra Agent Identity",
        "ModelNotFound; ResourceNotFound (check FOUNDRY_PROJECT_ENDPOINT); TimeoutError; repeated restarts = crash loop",
    ], theme="green", icon="azd", src=[("Monitor hosted-agent logs", learn("agents/how-to/monitor-hosted-agent-logs"))])
    ins = Card((3 * gw + 2 * gg - gg) / 2, "Insights in Foundry", [
        "LLM judge (GPT-5 or newer; mini or nano allowed) scans production traces; first scan looks back 7 days; on demand or scheduled",
        "Each Insight: title, category, severity High / Medium / Low, agent version, likely cause, linked traces, proposed fix",
        "Categories: Context and memory, Cost and tokens, Hallucinations, Latency, Output quality, Reliability errors, Security and risk, Tool call failures",
        "Actions: investigate, add evaluation coverage, review the fix, route dependency or platform issues to the owner, resolve / dismiss / monitor",
        "Read-only retrieval: Foundry MCP agent_insights_get or Foundry Skill",
    ], theme="violet", icon="foundry", badge="preview", src=[("Agent insights", learn("observability/how-to/agent-insights"))])
    r1r, r1b = row(cv, gx, y, [ev, cp, tr], gap=gg)
    r2r, r2b = row(cv, gx, r1b + gg, [hl, ins], gap=gg)
    y = max(r2b, dash_bottom + 30) + 70

    # ================================================================== 4. ALERT CATALOGUE
    section_header(cv, 0, y, "4   Alert catalogue: a suggested starter set", size=32,
                   sub="Assembled by us from documented signals. Green cells are thresholds the docs give; the rest are yours to set from a baseline of normal traffic.")
    draw_badge(cv, text_size("4   Alert catalogue: a suggested starter set", 32)[0] + 24, y + 14, "suggested")
    y += 100
    D, Y_ = "green", "gray"
    t_alert = Table(
        [("#", 56), ("Alert", 220), ("Signal", 520), ("Threshold", 340), ("Action", 360)],
        [
            [("1", "gray"), "Platform incident", "Service Health: service issue, maintenance, advisory, security", "n/a", "Page on-call; evaluate failover"],
            [("2", "blue"), "Model errors", "ModelRequests with StatusCode 5xx (count)", ("yours: your tolerance", Y_), "Gateway circuit breaker or failover"],
            [("3", "blue"), "Availability", "ModelAvailabilityRate", ("yours: below target %", Y_), "Same as 2"],
            [("4", "blue"), "Throttling", "ModelRequests with 429, by deployment", ("docs: sustained 429s while under quota -> support", D), "Back off, raise quota, add PTU"],
            [("5", "blue"), "PTU saturation", "ProvisionedUtilization", ("docs: 100% or more = 429", D), "Spillover or scale"],
            [("6", "blue"), "Latency", "TimeToResponse, NormalizedTimeBetweenTokens", ("yours: vs your baseline", Y_), "PTU or regional change"],
            [("7", "green"), "Agent success", "Agent Monitor run success rate", ("docs: below 95%", D), "Investigate runs"],
            [("8", "green"), "Agent latency", "Agent Monitor latency", ("docs: above 10 s", D), "Check model, tool, network"],
            [("9", "violet"), "Quality drift", "Continuous / scheduled evaluation scores", ("yours: per evaluator", Y_), "Roll back or optimise"],
            [("10", "violet"), "Safety", "Red-team findings; Defender and guardrail alerts (Notification Center)", "n/a", "SOC runbook"],
            [("11", "green"), "Hosted-agent capacity", "429 session_quota_exceeded, regional_session_quota_exceeded or subnet_exhausted", "n/a", "Raise limits or fix the subnet"],
            [("12", "cyan"), "Dependency health", "Cosmos DB, AI Search, Storage Resource Health + metrics", ("yours: per service", Y_), "Disaster-recovery playbook"],
            [("13", "cyan"), "Cost", "Cost Management budgets and anomaly alerts (see the FinOps canvas)", ("yours: budget %", Y_), "FinOps owner"],
            [("14", "gray"), "Config / policy", "Azure Policy non-compliance (Notification Center)", "n/a", "Platform team"],
        ], w=1496, theme="yellow", size=14, head_size=15, title="Starter alert rules (numbers match the lanes above)", title_size=22)
    t_alert.place(cv, 0, y)
    ax = 1496 + 50
    aw = (W - ax - 40) / 2
    n_sh = Note(aw, "Azure portal > Service Health > Health alerts > Add service health alert. Scope: subscriptions + regions + services (Azure OpenAI, Foundry Models, Foundry Agent Service). "
                    "CLI: az monitor activity-log alert create --condition category=ServiceHealth. The action group can send email, SMS, webhook or ITSM, and trigger Azure Automation runbooks or Logic Apps that run a failover script.",
                kind="tip", title="Create the platform alert (#1)", src=[("Stay informed with Service Health", learn("how-to/stay-informed-service-health"))])
    n_sh.place(cv, ax, y)
    n_th = Note(aw, "Set thresholds from a baseline of normal traffic - use Metrics explorer to review historical values.", kind="info", title="Docs tip")
    n_th.place(cv, ax, n_sh.bottom + 20)
    n_known = Note(aw, "Notification Center is in-app only (the Foundry portal bell). It aggregates security alerts, policy and compliance events and run results for long-running evaluation and training jobs. "
                       "The page says 'four main types' but lists three.",
                   kind="warn", title="Docs disagree - and not a paging channel", src=[("Notification Center", learn("concepts/concept-notification-center"))])
    n_known.place(cv, ax + aw + 40, y)
    chain_y = n_known.bottom + 30
    with cv.panel(ax + aw + 40, chain_y, title="Documented automation hook", sub="from the disaster-recovery page", theme="gray", style="dotted", pad=18,
                  title_size=20, sub_size=14, w=aw) as ch:
        bw_ = (aw - 36 - 3 * 34) / 4
        b1 = Box(bw_, "Service Health alert", h=96, theme="gray", icon="service-health", icon_pos="top", icon_size=28, size=14).place(cv, ch.ix, ch.iy)
        b2 = Box(bw_, "Action group", h=96, theme="gray", icon="alerts", icon_pos="top", icon_size=28, size=14).place(cv, b1.right + 34, ch.iy)
        b3 = Box(bw_, "Runbook or Logic App", h=96, theme="gray", icon="logic-apps", icon_pos="top", icon_size=28, size=14).place(cv, b2.right + 34, ch.iy)
        b4 = Box(bw_, "Failover script", h=96, theme="gray", icon="automation", icon_pos="top", icon_size=28, size=14).place(cv, b3.right + 34, ch.iy)
        connect(cv, b1, b2, gap=2)
        connect(cv, b2, b3, gap=2)
        connect(cv, b3, b4, gap=2)
    y = max(t_alert.bottom, n_th.bottom, ch.bottom) + 70

    # ================================================================== 5. ON-CALL FLOW
    section_header(cv, 0, y, "5   On-call flow: detect, triage, classify and mitigate, communicate, learn", size=32,
                   sub="A suggested flow synthesised from the Foundry disaster-recovery pages and the Cloud Adoption Framework operate guidance")
    draw_badge(cv, text_size("5   On-call flow: detect, triage, classify and mitigate, communicate, learn", 32)[0] + 24, y + 14, "suggested")
    y += 112
    flow_top = y
    BH = 86
    branches = [
        ("Platform outage", "Fail over: gateway or warm standby", "red", "service-health"),
        ("Throttling", "Back off, raise TPM, spillover, add PTU", "yellow", "quotas"),
        ("Bad release", "Roll back the agent version or selector", "green", "versions"),
        ("Tool, MCP or dependency issue", "Disable it or route to its owner (CAF: pause / resume for external agents and tools)", "orange", "toolbox"),
        ("Security finding", "SOC runbook", "pink", "defender"),
    ]
    stack_h = len(branches) * BH + (len(branches) - 1) * 16
    cyf = flow_top + stack_h / 2
    det = Card(350, "Detect", [
        "Service Health alert",
        "Metric alert: errors, 429s, PTU utilization",
        "Agent Monitor alert (preview)",
        "Insights (preview) or evaluation drift",
    ], theme="gray", icon="alerts")
    tri = Card(440, "Triage (under 15 min)", [
        "Platform or workload? Check Service Health + Resource Health",
        "Split ModelRequests by StatusCode, deployment and region",
        "Check the latest release: agent version, model version, routing config",
    ], theme="blue", icon="monitor")
    det.place(cv, 0, cyf - det.h / 2)
    tri.place(cv, det.right + 90, cyf - tri.h / 2)
    dia = Box(250, "What kind of incident?", h=190, shape="diamond", theme="yellow", size=17).place(cv, tri.right + 90, cyf - 95)
    bx = dia.right + 120
    bws = 640
    cv.text(bx, flow_top - 44, "Classify, then mitigate by type", size=24, color="#e67700")
    brs = []
    for i, (t, d, th, ic) in enumerate(branches):
        b = Box(bws, t, h=BH, theme=th, sub=d, icon=ic, icon_pos="left", icon_size=34, size=18, sub_size=14, fill="soft")
        b.place(cv, bx, flow_top + i * (BH + 16))
        brs.append(b)
    brace(cv, bx - 36, flow_top, flow_top + stack_h, side="left", depth=22)
    arrow(cv, [(dia.right + 6, cyf), (bx - 62, cyf)])
    brace(cv, bx + bws + 36, flow_top, flow_top + stack_h, side="right", depth=22)
    com = Card(350, "Communicate", [
        "Tell users the app is in standby mode",
        "Update stakeholders",
    ], theme="indigo", icon="users")
    lrn = Card(500, "Learn", [
        "Convert incident traces into a regression dataset (trace_ids or a narrow time window)",
        "Add an evaluator for the failure",
        "Update alert thresholds, the runbook and the IaC",
        "Schedule a failover drill",
    ], theme="violet", icon="foundry")
    com.place(cv, bx + bws + 100, cyf - com.h / 2)
    lrn.place(cv, com.right + 70, cyf - lrn.h / 2)
    connect(cv, det, tri, a_side="right", b_side="left")
    connect(cv, tri, dia, a_side="right", b_side="left")
    arrow(cv, [(bx + bws + 64, cyf), (com.x - 6, cyf)])
    connect(cv, com, lrn, a_side="right", b_side="left")
    for n_, blk, th_ in ((1, det, "gray"), (2, tri, "blue"), (3, dia, "yellow"), (4, com, "indigo"), (5, lrn, "violet")):
        numbered(cv, blk.x + (blk.w / 2 if n_ == 3 else 6), blk.y + (4 if n_ == 3 else 6), n_, theme=th_, d=36, size=21)
    # loop-back: what you learn feeds detection
    lby = flow_top + stack_h + 46
    arrow(cv, [(lrn.cx, lrn.bottom + 6), (lrn.cx, lby), (det.cx, lby), (det.cx, det.bottom + 6)], dash="dashed", color="#6741d9", sw=3,
          label="what you learn tunes the alerts, runbooks and datasets that detect the next incident", label_size=17, label_pos="above")
    y = lby + 70

    # ================================================================== 6. FEEDBACK LOOP
    section_header(cv, 0, y, "6   The feedback loop: production traces become the next evaluation dataset", size=32,
                   sub="Trace -> dataset -> evaluate -> optimize -> release -> monitor, then around again")
    y += 100
    cx0, cy0 = 790, y + 450
    rxl, ryl = 560, 370
    nw, nh = 390, 128
    ang = {"trace": -90, "dataset": -30, "eval": 30, "opt": 90, "rel": 150, "mon": 210}
    spec = [
        ("trace", "1  Trace", "OTel spans in App Insights; 30-90 s lag; may hold personal data", "violet", "app-insights"),
        ("dataset", "2  Dataset", "Traces-to-dataset job: max_samples 1-1,000 with intelligent sampling", "cyan", "storage"),
        ("eval", "3  Evaluate", "Run evaluators on the dataset; cluster analysis and Insights (preview)", "violet", "foundry"),
        ("opt", "4  Optimize", "Agent or prompt optimizer proposes; you apply and redeploy", "green", "agent"),
        ("rel", "5  Release", "New agent version, release gates, then promote", "grape", "devops"),
        ("mon", "6  Monitor", "Continuous + scheduled evaluation, alerts, Control Plane", "violet", "monitor"),
    ]
    nodes = {}
    for key, title, sub, th, ic in spec:
        a = math.radians(ang[key])
        px, py = cx0 + rxl * math.cos(a), cy0 + ryl * math.sin(a)
        nodes[key] = Box(nw, title, h=nh, theme=th, sub=sub, icon=ic, icon_pos="left", icon_size=38, size=24, sub_size=15,
                         fill="solid").place(cv, px - nw / 2, py - nh / 2)
    boxes_ = list(nodes.values())
    order_ = ["trace", "dataset", "eval", "opt", "rel", "mon", "trace"]
    labels_ = ["convert", "run evaluators", "improve", "new version", "ship", "observe"]
    for i in range(6):
        ring_arrow(cv, cx0, cy0, rxl, ryl, ang[order_[i]], ang[order_[i]] + 60, boxes_, label=labels_[i], label_size=18,
                   label_off=34)
    cv.text(cx0 - 250, cy0 - 70, "Production traffic\nbecomes tomorrow's\ntest set", size=30, color="#5f3dc4", align="center", w=500)
    cv.text(cx0 - 250, cy0 + 60, "every incident and drift alert can add cases\nto the regression dataset (suggested practice)", size=16,
            color="#495057", align="center", w=500)

    fx = 1560
    fw = W - fx
    t2d = Card(fw, "Convert agent traces into evaluation datasets", [
        "A datasets generation job from project_client.datasets; SDK 2.8.0 or later (Python and JS); supported-region list applies",
        "max_samples 1-1,000; intelligent sampling drops low-intent traffic and keeps diversity (MinHash)",
        "trace_ids selects exact traces; pinning agent_version is recommended",
        "redact_private_content defaults to true",
        "Write mode overwrite (new version from the new rows only) or merge (dedupe with the latest); it never edits a version in place",
    ], theme="cyan", icon="storage", src=[("Convert traces to datasets", learn("observability/how-to/traces-to-dataset"))])
    t2d.place(cv, fx, y)
    lim = Card((fw - 40) / 2, "Limitations", [
        "The connected App Insights must allow public network access for dataset generation (behind an Azure Monitor Private Link Scope, enable public network query access)",
        "Bring-your-own storage needs public network access for dataset creation",
    ], theme="red", icon="private-link", src=[("Convert traces to datasets", learn("observability/how-to/traces-to-dataset"))])
    lim.place(cv, fx, t2d.bottom + 24)
    fb = Card((fw - 40) / 2, "Human feedback (preview)", [
        "OTel event gen_ai.evaluation.result, correlated to the trace and span",
        "Binary (0.0 or 1.0, label fail / pass) or Likert 5-point (1-5, default threshold 3.0)",
        "Source: builder or end_user",
        "Query: customEvents where name == gen_ai.evaluation.result",
    ], theme="violet", icon="app-insights", badge="preview", src=[("Log end-user feedback", learn("observability/how-to/log-end-user-feedback"))])
    fb.place(cv, fx + lim.w + 40, t2d.bottom + 24)
    y = max(cy0 + ryl + nh / 2, fb.bottom, lim.bottom) + 70

    # ================================================================== 7. GOTCHAS
    section_header(cv, 0, y, "Watch out", size=32)
    y += 62
    nw3 = (W - 2 * 40) / 3
    g1 = Note(nw3, "Agent monitoring data lives in the connected Application Insights. Without it there are no health metrics, cost or drill-down in Control Plane.",
              kind="gotcha", title="No App Insights, no agent signals")
    g2 = Note(nw3, "Dashboard alerts, recurring evaluations, red-team scans, Insights and end-user feedback logging are all preview as documented on 2026-11-03.",
              kind="preview", title="Several operate features are preview")
    g3 = Note(nw3, "Trace content can include personal data. Log Analytics Reader exposes it; use Privileged Monitoring Data Reader for protected tables.",
              kind="gotcha", title="Traces can contain PII")
    g4 = Note(nw3, "The classic Agent Service metrics (Agents, IndexedFiles, Messages, Runs, Threads, Tokens, ToolCalls) are reference only: Agents (classic) is deprecated and retires March 31, 2027 (as of 2026-11-03). Plan alerts on the new agent runtime signals.",
              kind="warn", title="Agents (classic) is retiring",
              src=[("Classic monitor reference", learn("agents/reference/monitor-service", base="azure/foundry-classic"))])
    g5 = Note(nw3, "Foundry cannot fail over for you: Service Health, Resource Health and your own alerts are how you find out. Build the response into runbooks, the gateway and IaC.",
              kind="warn", title="Detection is yours")
    g6 = Note(nw3, "Cost lags about 5 hours, diagnostic logs 15 minutes to 2 hours, App Insights spans 30 to 90 seconds - do not use cost data for fast paging.",
              kind="tip", title="Match the alert to the lag")
    row(cv, 0, y, [g1, g2, g3], gap=40)
    row(cv, 0, g1.bottom + 24, [g4, g5, g6], gap=40)
    y = g4.bottom + 70

    # ================================================================== SOURCES
    sources(cv, 0, y, [
        ("Stay informed with Azure Service Health", learn("how-to/stay-informed-service-health")),
        ("Monitor Foundry Models (metrics)", learn("foundry-models/how-to/monitor-models")),
        ("Diagnostic logging", learn("how-to/diagnostic-logging")),
        ("Monitor agents with the dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard")),
        ("Observability concepts", learn("concepts/observability")),
        ("Trace data", learn("observability/concepts/trace-data")),
        ("Agent insights", learn("observability/how-to/agent-insights")),
        ("Convert traces to evaluation datasets", learn("observability/how-to/traces-to-dataset")),
        ("Log end-user feedback", learn("observability/how-to/log-end-user-feedback")),
        ("Monitoring across the fleet (Control Plane)", learn("control-plane/monitoring-across-fleet")),
        ("Notification Center", learn("concepts/concept-notification-center")),
        ("Monitor hosted-agent logs", learn("agents/how-to/monitor-hosted-agent-logs")),
        ("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
        ("Foundry architecture (monitoring scopes)", learn("concepts/architecture")),
    ], w=W, cols=3)
