"""Capacity, cost and model-lifecycle operations - operating cadence, quota/PTU/reservation ops, cost controls, retirement machinery."""
from generator.xd import *

META = dict(
    id="finops-capacity-ops", title="FinOps, capacity and model-lifecycle operations", section="6", order=4,
    description="The operating cadence for quota, PTU and reservations, token budgets, chargeback and cleanup - plus model "
                "retirement ops: the schedule watch, NoAutoUpgrade pitfalls and regression testing on upgrade.",
    tags=["finops", "capacity", "quota", "ptu", "cost", "model-retirement"],
)

W = 3000
ASOF = "as of 2026-11-03"


# ---------------------------------------------------------------------------------------------- helpers
def tag(cv, x, y, label):
    """Small grey pill for 'suggested' / 'docs disagree' style stickers."""
    draw_badge(cv, x, y, label)


def head(cv, y, text, sub=None, sticker=None):
    section_header(cv, 0, y, text, size=32, sub=sub)
    if sticker:
        draw_badge(cv, text_size(text, 32)[0] + 24, y + 14, sticker)
    return y + (100 if sub else 70)


def bar(cv, x, y, w, h, theme, label=None, hatch=True, size=15, dash="solid"):
    th = THEMES[theme]
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure" if hatch else "solid", sw=2, round_=False, rough=1, dash=dash)
    if label:
        tw, thh = text_size(label, size)
        cv.text(x + (w - tw) / 2, y + (h - thh) / 2, label, size=size, color=th.deep)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Capacity, cost and model-lifecycle operations",
                                "The cadence that keeps quota, PTUs, token spend and model versions under control - week after week", w=W)
    kx = 1700
    cv.text(kx, 8, "Key:", size=16, color="#495057")
    draw_badge(cv, kx + 50, 8, "preview")
    cv.text(kx + 135, 8, "preview as documented", size=15)
    draw_badge(cv, kx + 360, 8, "suggested")
    cv.text(kx + 465, 8, "our synthesis, not in the docs", size=15)
    draw_badge(cv, kx + 800, 8, "docs disagree")
    cv.text(kx + 955, 8, "conflicting Learn pages", size=15)
    cv.text(kx + 50, 42, f"Time-sensitive facts are {ASOF}. Cost meters themselves are on the governance and cost canvas.", size=15, color="#495057")
    y = bottom + 56

    # ================================================================== 1. CADENCE
    y = head(cv, y, "1   The operating cadence", "Daily pulse, weekly review, monthly FinOps, quarterly planning - and the events that interrupt all of them",
             sticker="suggested")
    cv.text(text_size("1   The operating cadence", 32)[0] + 170, y - 82, "task lists are our synthesis, anchored to the Learn pages cited on each card", size=15, color="#495057")
    colw, cgap = 560, 50
    cad = [
        ("Daily", "check the pulse", "scheduler", "yellow", [
            "Service Health and the Foundry known-issues page",
            "429 and 5xx by deployment (ModelRequests)",
            "ProvisionedUtilization and the spillover share (IsSpillover)",
            "Gateway token-limit hits: 429 (TPM) and 403 (period quota)",
            "Cost anomaly alert inbox",
            "Hosted-agent session-quota errors",
        ], [("Stay informed with Service Health", learn("how-to/stay-informed-service-health")),
            ("Provisioned: get started", learn("openai/how-to/provisioned-get-started")),
            ("Enforce token limits", learn("control-plane/how-to-enforce-limits-models"))]),
        ("Weekly", "review and root-cause", "advisor", "yellow", [
            "429 root-cause review: rate limit, capacity or a temporary adjustment",
            "PTU utilization vs deployed PTUs",
            "Idle deployments, stale agents and conversations",
            "Budget burn vs plan",
            "Pending retirement notices: Service Health advisories, Models API lifecycleStatus",
            "Insights review, category Cost and tokens",
        ], [("Quota", learn("openai/how-to/quota")), ("Agent insights", learn("observability/how-to/agent-insights")),
            ("Model lifecycle and retirements", learn("openai/concepts/model-retirements"))]),
        ("Monthly", "FinOps review", "cost-management", "yellow", [
            "CAF: review consumption trends monthly",
            "Adjust quotas by business priority",
            "Benchmark smaller models for routine tasks",
            "Reservation Utilization % check",
            "Chargeback report by the project tag",
            "Cost analysis grouped by Meter and Resource; scheduled cost export",
        ], [("CAF: integrate, manage and operate", learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base="")),
            ("Plan and manage costs", learn("concepts/manage-costs")),
            ("PTU billing and reservations", learn("openai/concepts/provisioned-throughput-billing"))]),
        ("Quarterly", "plan and rehearse", "reservations", "yellow", [
            "CAF: audit the agent estate and retire unused agents",
            "Align high-availability settings to workload criticality",
            "Model migration cadence: 'roughly quarterly'",
            "Reservation sizing and renewal",
            "Failover drill: 'for example, quarterly'",
            "Capacity plan for the next quarter",
        ], [("CAF: integrate, manage and operate", learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base="")),
            ("Model migration", learn("foundry-models/concepts/model-migration")),
            ("High availability and resiliency", learn("how-to/high-availability-resiliency"))]),
        ("Event-driven", "interrupts the calendar", "alerts", "gray", [
            "Retirement notice (GA at least 60 days, preview at least 30 days): start the migration",
            "New model launch",
            "Quota or capacity request (approval 'might take several days')",
            "Budget breach",
            "Incident: see the monitoring canvas",
        ], [("Model lifecycle and retirements", learn("openai/concepts/model-retirements")),
            ("Provisioned throughput", learn("openai/concepts/provisioned-throughput"))]),
    ]
    cx = 0
    cad_cards = []
    for name, sub, ic, th, bullets, srcs in cad:
        hb = Box(colw, name, h=92, theme=th, sub=sub, icon=ic, icon_pos="left", icon_size=40, size=30, sub_size=17, fill="solid")
        cd = Card(colw, None, bullets, theme=th, fill="hatch", src=srcs)
        cad_cards.append((hb, cd))
    hmax = max(c.h for _, c in cad_cards)
    for i, (hb, cd) in enumerate(cad_cards):
        hb.place(cv, cx, y)
        cd.place(cv, cx, y + hb.h + 14, h=hmax)
        if i:
            arrow(cv, [(cx - cgap + 6, y + hb.h / 2), (cx - 6, y + hb.h / 2)], sw=3)
        cx += colw + cgap
    y = y + 92 + 14 + hmax + 70

    # ================================================================== 2. COCKPIT + COST STACK
    y = head(cv, y, "2   Two control stacks: the capacity cockpit and the cost-control stack",
             "Left: from quota to the spillover that absorbs peaks. Right: from the gateway limit to cleanup. Read top to bottom.")
    lw = 1470
    rx0 = lw + 60
    cv.text(0, y - 2, "Capacity cockpit", size=26, color="#e67700")
    cv.text(rx0, y - 2, "Cost-control stack", size=26, color="#e67700")
    y += 44
    fun = [
        ("1  Quota", "Do I have the right to deploy?", "quotas", 1470, [
            "Quota is TPM per subscription x region x model x deployment type; RPM is derived by a model-specific capacity unit",
            "Assigning TPM to a deployment reduces the quota still available; up to 30 resources per region",
            "Portal: Manage > Quota (Token per minute and Provisioned throughput unit tabs); Request quota; changes propagate in up to 15 min",
            "Alert on headroom with the Usages API or az cognitiveservices usage list -l <region>; view role: Cognitive Services Usages Reader",
            "Increases favour customers who actively use their existing quota; partner and community models generally cannot get increases (Anthropic can)",
        ], [("Quota", learn("openai/how-to/quota"))]),
        ("2  Capacity", "Is there room right now?", "regions", 1370, [
            "Capacity is dynamic and changes through the day; unused quota does not guarantee capacity",
            "Scale-up needs free capacity; scale-down releases capacity permanently",
            "Check in the portal (it lists alternative regions) or with the Model Capacities API",
            "No capacity? Request it via the form, try fewer PTUs, try later, or use Global Provisioned for broader availability",
        ], [("Provisioned billing and capacity", learn("openai/concepts/provisioned-throughput-billing")),
            ("Deployment types", learn("foundry-models/concepts/deployment-types"))]),
        ("3  Deployment", "How big, and which type?", "openai", 1270, [
            "Size from RPM, average input and output tokens, output-to-input ratio and cache rate (section 3)",
            "The deployment type - Global, Data Zone or Regional - decides the reservation you can buy",
            "Create the deployment first, then purchase the reservation",
        ], [("Determine PTU sizing", learn("openai/how-to/provisioned-throughput-sizing"))]),
        ("4  Reservation", "How do I pay less?", "reservations", 1170, [
            "One-month or one-year term; the discount applies to PTU hourly meters, not to deployment creation",
            "Matches on deployment type + region (Data Zone and Regional only) + scope; model-independent",
            "Does not guarantee capacity",
        ], [("PTU billing and reservations", learn("openai/concepts/provisioned-throughput-billing"))]),
        ("5  Spillover", "What absorbs the peaks?", "apim", 1070, [
            "PTU -> Standard inside one Foundry resource; enable it on all Global and Data Zone provisioned deployments",
            "Cost = PTU hourly + standard token rates for the spilled requests",
            "Triggers and response headers: see the multi-region patterns canvas",
        ], [("Spillover traffic management", learn("openai/how-to/spillover-traffic-management"))]),
    ]
    cards_l = []
    for title, sub, ic, w, bl, srcs in fun:
        cards_l.append(Card(w, title, bl, theme="yellow", subtitle=sub, icon=ic, src=srcs, title_size=22, sub_size=15))
    yy = y
    for c in cards_l:
        c.place(cv, (lw - c.w) / 2, yy)
        yy += c.h + 48
    for a, b in zip(cards_l, cards_l[1:]):
        connect(cv, a, b, a_side="bottom", b_side="top", sw=3)
    left_bottom = cards_l[-1].bottom

    stack = [
        ("1  Gateway token limits", "Stop runaway use before it bills", "apim", "preview", [
            "Foundry Control Plane + AI Gateway (APIM): per-project TPM rate limit (429) and a total token quota per period - hourly, daily, weekly, monthly or yearly (403 when exhausted)",
            "Manage > AI Gateway > gateway > Token management > + Set limit; needs API Management Service Contributor (or Owner); applies immediately; concurrent calls can briefly overshoot",
            "APIM policies: llm-token-limit / azure-openai-token-limit (counter key: subscription key, IP or expression; regional counters are not aggregated), llm-emit-token-metric, semantic caching with Azure Managed Redis",
            "Application levers: max_output_tokens, truncation (not with Agent Service managed orchestration), shorter system prompts, summarised history, cached answers",
        ], [("Enforce token limits", learn("control-plane/how-to-enforce-limits-models")),
            ("AI gateway capabilities in APIM", learn("azure/api-management/genai-gateway-capabilities", base=""))]),
        ("2  Budgets", "Know when spend crosses a line", "cost-management", None, [
            "Create budgets and alerts at subscription or resource-group scope, with filters for services or resources",
            "! No hard spend cap exists: Azure OpenAI does not currently provide hard limits - start automation from budget action groups (needs custom development)",
        ], [("Plan and manage costs", learn("concepts/manage-costs"))]),
        ("3  Anomaly alerts", "Catch the spike nobody budgeted", "alerts", None, [
            "Cost Management > Cost alerts > + Add > Anomaly; needs Cost Management Contributor or Microsoft.CostManagement/scheduledActions/write",
            "Emails once at detection; summarises resource-group count and cost changes and the top changes vs the previous 60 days",
        ], [("Analyze unexpected charges", learn("azure/cost-management-billing/understand/analyze-unexpected-charges", base=""))]),
        ("4  Chargeback tags", "Who spent it?", "tag", "preview", [
            "Project-level cost attribution (preview): usage is auto-tagged project - no manual tags - for Models sold by Azure incl. Azure OpenAI (not Marketplace models, not Claude); filter Cost analysis by Tag project",
            "CAF: cost-allocation tags by department or use case; gateway per-consumer token metrics; reservation costs can be charged back",
        ], [("Plan and manage costs", learn("concepts/manage-costs"))]),
        ("5  Cleanup", "Stop paying for what nobody uses", "automation", None, [
            "Idle deployments, zombie model versions, unused agents, old trace retention - see section 6",
        ], []),
    ]
    cards_r = []
    for title, sub, ic, bdg, bl, srcs in stack:
        cards_r.append(Card(1470, title, bl, theme="yellow", subtitle=sub, icon=ic, badge=bdg, src=srcs, title_size=22, sub_size=15, fill="soft"))
    # equalise the total height of both stacks by stretching the gaps
    tot_r = sum(c.h for c in cards_r)
    tot_l = left_bottom - y
    gap_r = max(48, (tot_l - tot_r) / (len(cards_r) - 1))
    yy = y
    for c in cards_r:
        c.place(cv, rx0, yy)
        yy += c.h + gap_r
    for a, b in zip(cards_r, cards_r[1:]):
        connect(cv, a, b, a_side="bottom", b_side="top", sw=3)
    y = max(left_bottom, cards_r[-1].bottom) + 70

    # ================================================================== 3. PTU PLANNING
    y = head(cv, y, "3   PTU planning, hourly billing and reservations", "Provisioned throughput is billed on deployed PTUs, not tokens - size it, deploy it, then commit")
    # --- sizing flow
    with cv.panel(0, y, title="From traffic to PTUs", sub="sizing inputs -> calculator -> benchmark", theme="blue", style="dotted", pad=22, title_size=24, w=1010) as ps:
        ins = ["RPM", "Average input tokens", "Average output tokens", "Output-to-input ratio (model-specific)", "Cache rate (cached tokens use no PTU)"]
        ch = [Chip(t, theme="blue", size=15, w=330, fill="soft") for t in ins]
        yy = ps.iy
        for c in ch:
            c.place(cv, ps.ix, yy)
            yy += c.h + 12
        calc = Box(210, "Capacity calculator in the portal", h=110, theme="blue", icon="quotas", icon_size=32, size=16).place(cv, ps.ix + 410, ps.iy + 56)
        ptu = Box(150, "PTUs to deploy", h=110, theme="yellow", size=17).place(cv, calc.right + 60, calc.y)
        for c in ch:
            connect(cv, c, calc, a_side="right", b_side="left", gap=3, sw=1.5, route="elbow")
        connect(cv, calc, ptu, sw=2.5)
        bench = Chip("azure-openai-benchmark: at least 10 min steady state", theme="violet", size=14).place(cv, ps.ix + 410, calc.bottom + 24)
        bench2 = Chip("then your own traffic shape and retry logic", theme="violet", size=14).place(cv, ps.ix + 410, bench.bottom + 8)
    sz_note = Card(1010, "Sizing notes", [
        "Normalized TPM (the model's Input TPM per PTU) converts the inputs to a PTU count; for GPT-4.1 and later the output-to-input ratio equals the global standard price ratio",
        "Set max_tokens near the true generation size for the best concurrency",
        "The PTU quota is shared across supported models in a region and deployment type - you buy PTUs, not a model",
    ], theme="blue", icon="openai", src=[("Determine PTU sizing", learn("openai/how-to/provisioned-throughput-sizing"))])
    sz_note.place(cv, 0, ps.bottom + 24)
    bill = Card(1010, "Hourly billing", [
        "$/PTU/hr on the PTUs deployed, whatever the tokens; prorated (15 minutes = 1/4 hour); a resize bills the new PTU count immediately",
        "Cannot be paused: only deleting the deployment stops billing, and charges on a deleted resource continue until it is purged (delete deployments first)",
        "Use hourly for benchmarking and events - not for scaling production up and down with traffic (cost and capacity risk)",
        "Pre-August-2024 customers can keep the legacy Commitment model alongside hourly and reservation billing",
    ], theme="yellow", icon="cost-management", src=[("PTU billing", learn("openai/concepts/provisioned-throughput-billing"))])
    bill.place(cv, 0, sz_note.bottom + 24)
    left_b = bill.bottom

    t_res = Table([("Reservation fact", 250), ("Detail", 700)], [
        ["Term and purchase", "One month or one year; bought in the Azure portal; a separate purchase per deployment type (Global, Data Zone, Regional)"],
        ["Global is region-agnostic", "50 PTU East US + 100 West Europe + 200 Australia East = one 350-unit Global reservation"],
        ["Matching", "Deployment type + region (Data Zone and Regional only) + scope; never by model or deployment ID"],
        ["Scope", "Resource group, subscription, management group or billing account; scope updates are free at any time"],
        ["Active immediately", "The discount applies as soon as the reservation is Active"],
        ["Excess is billed hourly", "Deployed PTUs above the reservation quantity pay the standard hourly rate"],
        ["No capacity guarantee", "Deploy first to confirm capacity, then purchase the reservation"],
        ["Exchange and cancel", "May incur fees; no exchange across deployment types; exchanges reset the term; auto-renew can be toggled"],
        ["Different roles", "Roles to purchase a reservation differ from deployment roles - verify early"],
        ["Utilization below 100%", "Over-purchase, or a deployment was deleted without cancelling its reservation"],
    ], w=1000, theme="yellow", size=14, head_size=15, title="Azure Reservations for PTUs: key facts", title_size=22, first_col_theme="yellow")
    t_res.place(cv, 1050, y)
    res_src = cv.text(1050, t_res.bottom + 6, "Learn: PTU billing and reservations", size=12, color=LINK, link=learn("openai/concepts/provisioned-throughput-billing"))

    # --- overage diagram
    ox = 2090
    ow = W - ox
    with cv.panel(ox, y, title="Reservation overage, worked example", sub="a 500-PTU Global reservation covers 300 existing PTUs", theme="yellow", style="dotted",
                  pad=22, title_size=24, w=ow) as po:
        u = 1.12
        x0 = po.ix
        by = po.iy + 70
        res_x = x0 + 500 * u
        cv.text(x0, by - 30, "Add a 200-PTU deployment", size=17, color="#495057")
        bar(cv, x0, by, 300 * u, 56, "gray", "300 existing")
        bar(cv, x0 + 300 * u, by, 200 * u, 56, "green", "200 new")
        cv.text(x0, by + 62, "All 500 PTUs covered: no hourly overage", size=15, color="#2b8a3e")
        by2 = by + 150
        cv.text(x0, by2 - 30, "Add a 300-PTU deployment", size=17, color="#495057")
        bar(cv, x0, by2, 300 * u, 56, "gray", "300 existing")
        bar(cv, x0 + 300 * u, by2, 200 * u, 56, "green", "200 covered")
        bar(cv, x0 + 500 * u, by2, 100 * u, 56, "red", "100", dash="dashed")
        cv.text(x0, by2 + 62, "100 PTUs billed hourly until you resize or buy more", size=15, color="#c92a2a")
        cv.line((res_x, by - 40), (res_x, by2 + 100), stroke="#e67700", sw=2, dash="dashed")
        cv.text(res_x + 8, by - 38, "500 PTU\nreserved", size=14, color="#e67700")
    n_dep = Note(ow, "Reservations and deployments are loosely coupled: deleting a deployment does not cancel its reservation, and resizing a deployment does not change the reservation quantity.",
                 kind="gotcha", title="Reservations do not follow deployments")
    n_dep.place(cv, ox, po.bottom + 24)
    y = max(left_b, t_res.bottom + 24, n_dep.bottom) + 70

    # ================================================================== 4. REGIONAL CAPACITY + LIMITS
    y = head(cv, y, "4   Regional capacity strategy, and the quota ceilings you can hit", f"Where new models land first - and the limits to watch ({ASOF})")
    cw3 = (W - 2 * 50) / 3
    # model rollout chain
    with cv.panel(0, y, title="Where a new model shows up", sub="deployment types, in order of availability", theme="blue", style="dotted", pad=20, title_size=22, w=cw3) as pr:
        order = [("Global Standard", "at launch: broadest availability", "blue"), ("Global Provisioned", "follows closely", "blue"),
                 ("Data Zone Standard + Provisioned", "after Global Provisioned", "indigo"), ("Standard + Provisioned (regional)", "last; no guaranteed date", "gray")]
        bxs = []
        yy = pr.iy
        for i, (t, s, th) in enumerate(order):
            b = Box(cw3 - 40, t, h=64, theme=th, sub=s, size=16, sub_size=13, fill="solid").place(cv, pr.ix, yy)
            bxs.append(b)
            yy += 64 + 30
        for a, b in zip(bxs, bxs[1:]):
            connect(cv, a, b, a_side="bottom", b_side="top", gap=2, sw=2.5)
    rc = Card(cw3, "Plan per workload", [
        "Specialised models (audio, image, video) are often only Data Zone or Global",
        "Successive versions may not land in the same regions; Microsoft can limit new customers in specific regions",
        "Plan model families, deployment types, data-processing limits, throughput and latency targets, and quota plus provisioned capacity for steady state and peak",
        "Set cost controls and budget alerts for shared and isolated environments (Foundry rollout guide)",
        "Check hosted-agent regions (31 at read time) and per-region tool and model support before choosing capacity or DR regions",
    ], theme="blue", icon="regions", src=[("Model lifecycle and availability", learn("openai/concepts/model-retirements")),
                                           ("Plan your Foundry rollout", learn("concepts/planning"))])
    rc.place(cv, 0, pr.bottom + 24)
    hs = Card(cw3, "Hosted agents: concurrent-session cap", [
        "Cap per subscription per region: 2,000 in Canada Central, East US 2, Japan East, North Central US, South Africa North, Southeast Asia and Sweden Central; 1,000 elsewhere",
        "Raise it with a support ticket naming the subscription, region and expected concurrency",
        "Idle and stopped sessions do not count; billing is CPU + memory across active sessions",
        "Right-size per version: raise the allocation if sustained peaks exceed about 70%, lower it if far below",
        "Alert on 429 session_quota_exceeded, regional_session_quota_exceeded, subnet_exhausted",
    ], theme="green", icon="agent", src=[("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
                                          ("Hosted agents", learn("agents/concepts/hosted-agents"))])
    hs.place(cv, cw3 + 50, y)
    t_lim = Table([("Agent Service fixed limit", 250), ("Value", 130)], [
        ["Files per agent / thread", "10,000"], ["Size per file (prompt agents)", "512 MB"], ["Total uploads", "300 GB"],
        ["Tokens per vector-store file", "2M"], ["Messages per thread", "100,000"], ["Characters per message", "1.5M"],
        ["Tools per agent", "128"], [("Versions per agent", "yellow"), ("1,000", "yellow")],
    ], w=cw3 - 20, theme="green", size=14, head_size=15, title="Agent Service fixed limits", title_size=20)
    t_lim.place(cv, cw3 + 50, hs.bottom + 24)
    cv.text(cw3 + 50, t_lim.bottom + 6, "Learn: Agent Service limits, quotas and regions", size=12, color=LINK, link=learn("agents/concepts/limits-quotas-regions"))
    n_q = Note(cw3, "Standard quota is scoped to the subscription: load-balancing across Foundry resources in one subscription adds no throughput. Quota increases may take days, and priority goes to customers using what they already have.",
               kind="gotcha", title="Quota is per subscription, per region")
    n_q.place(cv, 2 * (cw3 + 50), y)
    n_pr = Note(cw3, "Unused PTU quota does not guarantee capacity when you want to scale back up. Do not scale production PTUs down and up with traffic - keep the deployment sized, cover it with a reservation, and let spillover absorb peaks.",
                kind="warn", title="Do not play yo-yo with PTUs")
    n_pr.place(cv, 2 * (cw3 + 50), n_q.bottom + 24)
    n_pn = Note(cw3, "Data Zone Provisioned is described as 'US or EU' on the PTU page but lists US, EU and APAC on the deployment-types page - check the current zone list for your region.",
                kind="warn", title="Docs disagree: data zones")
    n_pn.place(cv, 2 * (cw3 + 50), n_pr.bottom + 24)
    y = max(rc.bottom, t_lim.bottom + 30, n_pn.bottom) + 70

    # ================================================================== 5. VISIBILITY
    y = head(cv, y, "5   Where to see the money: estimates for monitoring, Cost Management for reconciliation",
             "Foundry estimates are near-real-time but incomplete; the invoice truth lives in Azure Cost Management and lags by about 5 hours")
    t_vis = Table([("Need", 290), ("Mechanism", 1150)], [
        [("Near-real-time view", "blue"), "Foundry portal: Operate > Overview 'Estimated cost' tile (excludes prompt-agent and non-Foundry agent costs, and provisioned throughput); Operate > Assets > Agents 'Estimated costs' column; "
                                          "the agent Monitor tab token cost; Build > Models > model > Monitor cost chart (Claude / CCU caveat). Use estimates for monitoring."],
        [("Authoritative cost", "yellow"), "Azure Cost Management: Cost analysis at resource-group or subscription scope (Service tier: Azure OpenAI), grouped by Meter or Resource; "
                                           "meters per model per Foundry resource are named model-name-GUID; about 5 hours of delay; the HTTP status alone does not decide billing."],
        [("Other costs", "gray"), "Log Analytics and Azure Monitor alerting costs show under those services, not the Foundry resource scope. Export cost data to storage (daily, weekly or monthly) - the recommended way to retrieve cost datasets."],
        [("Reservation view", "yellow"), "Reservation Utilization, purchase and refund transactions, amortized cost view, and chargeback of reservation costs - all in Cost Management."],
    ], w=1440, theme="yellow", size=14, head_size=15, title="Cost visibility, from fast to authoritative", title_size=22)
    t_vis.place(cv, 0, y)
    cv.text(0, t_vis.bottom + 6, "Learn: Plan and manage costs", size=12, color=LINK, link=learn("concepts/manage-costs"))
    dep = Card(700, "Agent dependency costs (Standard setup)", [
        "Costliest: Cosmos DB and AI Search (plus DDoS protection)",
        "Foundry manages the Cosmos RU allocation: buy Cosmos reserved capacity",
        "No file uploads? Use LRS storage and a single AI Search replica",
        "Delete unused agents and conversations; keep dependencies in the Agent Service region (egress)",
        "Avoid sharing Cosmos or Search except after a risk assessment",
    ], theme="cyan", icon="cosmos", src=[("Baseline Foundry chat architecture - cost", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base=""))])
    dep.place(cv, 1480, y)
    n_est = Note(W - 2240, "Playground evaluations are on by default and billed - turn them off if you do not need them.", kind="tip", title="Quick win")
    n_est.place(cv, 2220, y)
    n_est2 = Note(W - 2240, "Project-level cost attribution, the AI Gateway integration, the agent optimizer and Insights are preview as of 2026-11-03.", kind="preview",
                  title="Preview ahead")
    n_est2.place(cv, 2220, n_est.bottom + 20)
    y = max(t_vis.bottom + 30, dep.bottom, n_est2.bottom) + 70

    # ================================================================== 6. CLEANUP
    y = head(cv, y, "6   Cleanup: find the idle and the zombie", "A monthly sweep - each item either costs money or hits a cap", sticker="suggested")
    cw4 = (W - 3 * 40) / 4
    cl = [
        Card(cw4, "Capacity and PTUs", [
            "Delete idle PTU deployments - billing stops only on deletion",
            "Deleting a deployment does not cancel its reservation: cancel or exchange it separately",
            "Delete deployments before deleting the resource, then purge it - charges continue until purged",
        ], theme="yellow", icon="quotas"),
        Card(cw4, "Models and agents", [
            "Old model deployments after a migration (zombie deployments)",
            "Developer-tier deployments auto-delete after 24 hours",
            "Unused agents (CAF quarterly audit); old agent versions (1,000-version cap)",
            "Idle sessions are auto-deleted after 30 days of inactivity",
        ], theme="green", icon="agent"),
        Card(cw4, "Data and telemetry", [
            "Stale threads and conversations grow Storage, Cosmos DB and AI Search",
            "Old trace and log retention in Application Insights and Log Analytics",
            "Diagnostic categories you never query",
        ], theme="cyan", icon="log-analytics"),
        Card(cw4, "Defaults to switch off", [
            "Playground evaluations are on by default and billed",
            "Restrict playground use to pre-production; approve every model consumer (CAF)",
            "Route deterministic tasks to rules, not a model (CAF)",
        ], theme="gray", icon="gear"),
    ]
    r_, b_ = row(cv, 0, y, cl, gap=40)
    cv.text(0, b_ + 8, "Learn: CAF integrate, manage and operate", size=12, color=LINK,
            link=learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base=""))
    y = b_ + 70

    # ================================================================== 7. MODEL LIFECYCLE
    y = head(cv, y, "7   Model lifecycle operations: watch the schedule, pick the upgrade policy, test before you move",
             f"Retirement dates are not extendable and there is no exception process ({ASOF})")
    tl_b = timeline(cv, 100, y + 150, W - 200, [
        ("GA launch", "Retirement date is set 18 months out", "visible in the Models API"),
        ("12 months", "Deprecated", "existing customers only; new customers cannot deploy"),
        ("About T-90 days", "Replacement testable in Global Standard", "official replacement named 90-120 days out"),
        ("At least T-60 days", "GA retirement notice", "email to subscription owners + Service Health advisory"),
        ("About T-30 days", "Replacement testable in provisioned regions", "a manual migration window"),
        ("18 months", "Retired: 410 Gone", "all inference requests fail"),
    ], label_w=430, theme="red", size=17)
    cv.text(W - 330, y + 150 - 64, "schematic - not to scale", size=14, color="#495057")
    cv.text(0, y - 4, "Standard 18-month GA lifecycle", size=22, color="#c92a2a")
    y = tl_b + 40
    t_stage = Table([("Stage", 300), ("Create new deployments?", 300), ("Existing deployments", 330)], [
        [("Preview", "orange"), "Yes", "Work; may be force-upgraded (at least 30 days notice)"],
        [("GA", "green"), "Yes", "Work"],
        [("Legacy (optional)", "yellow"), "Yes, until deprecation", "Work"],
        [("Deprecated  (API: lifecycleStatus Deprecating)", "yellow"), "Existing subscriptions only: the subscription must have deployed that version", "Work"],
        [("Retired  (API: Deprecated + a past date)", "red"), "No", "All inference returns 410 Gone"],
    ], w=1000, theme="red", size=14, head_size=15, title="Five lifecycle stages", title_size=22)
    t_stage.place(cv, 0, y)
    cv.text(0, t_stage.bottom + 6, "Learn: Foundry Models lifecycle and support policy", size=12, color=LINK, link=learn("openai/concepts/model-retirements"))
    lens = Card(560, "How long a version lives", [
        "Standard GA: 18 months; Deprecated at 12 months",
        "Anthropic, DeepSeek, Fireworks and Mistral GA: 12 months",
        "SpaceXAI Grok from 4.7: at least 6 months",
        "Preview: force-upgraded or retired with at least 30 days notice",
        "Government clouds: one version at a time, 30-day overlap",
        "Emergency retirement is possible for compliance or security issues",
        "Fine-tuned models retire on a separate clock",
    ], theme="red", icon="versions", src=[("Model lifecycle", learn("openai/concepts/model-retirements"))])
    lens.place(cv, 1040, y)
    # auto-update policy decision
    ax0 = 1640
    with cv.panel(ax0, y, title="Auto-update policy on a Standard deployment", sub="versionUpgradeOption - which one is on your production deployment?", theme="grape",
                  style="dotted", pad=20, title_size=22, w=W - ax0) as pa:
        dm = Box(260, "versionUpgradeOption", h=150, shape="diamond", theme="grape", size=16).place(cv, pa.ix, pa.iy + 40)
        o1 = Box(780, "OnceNewDefaultVersionAvailable", h=70, theme="green", sub="upgraded within 2 weeks of a new default version", size=17, sub_size=14, fill="soft").place(cv, dm.right + 90, pa.iy)
        o2 = Box(780, "OnceCurrentVersionExpired  (null = this)", h=70, theme="yellow", sub="upgraded when the current version retires", size=17, sub_size=14, fill="soft").place(cv, dm.right + 90, o1.bottom + 20)
        o3 = Box(780, "NoAutoUpgrade", h=70, theme="red", sub="the deployment STOPS WORKING at retirement", size=17, sub_size=14, fill="soft").place(cv, dm.right + 90, o2.bottom + 20)
        for o in (o1, o2, o3):
            connect(cv, dm, o, a_side="right", b_side="left", gap=4, sw=2.5, route="elbow")
    pol = Card(W - ax0, "Policy facts and pitfalls", [
        "Applies to Standard deployment types; read it via REST, PowerShell, CLI or portal; update it via REST, PowerShell or portal - Azure CLI cannot update it",
        "Architecture Center: production agents should not auto-upgrade; early testing can auto-update to the default",
        "! Pinned production + a missed retirement date = an outage: put the retirement date in your calendar and alert on Service Health advisories",
        "! Provisioned deployments are never auto-upgraded - you migrate them by hand before retirement",
    ], theme="grape", icon="policy", src=[("Working with models", learn("openai/how-to/working-with-models")),
                                          ("Baseline Foundry chat architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base=""))])
    pol.place(cv, ax0, pa.bottom + 24)
    y = max(t_stage.bottom + 30, lens.bottom, pol.bottom) + 40

    # API terminology + schedule
    t_api = Table([("Stage in docs and portal", 300), ("API lifecycleStatus", 230), ("deprecation.inference", 270), ("Meaning", 250)], [
        ["Preview", "Preview", "future date or unset", "May change or be removed"],
        ["Generally Available", "GenerallyAvailable", "future date, set at launch", "Fixed weights and API"],
        ["Deprecated", "Deprecating", "future date", "Still serves; blocked for new customers"],
        [("Retired", "red"), ("Deprecated", "red"), ("past date", "red"), ("Fully retired: 410 Gone", "red")],
    ], w=1090, theme="blue", size=14, head_size=15, title="Check it in code: the Models API wording differs from the docs", title_size=20)
    t_api.place(cv, 0, y)
    cv.text(0, t_api.bottom + 6, "Learn: Models API; GET .../providers/Microsoft.CognitiveServices/locations/{location}/models?api-version=2024-10-01",
            size=12, color=LINK, link=learn("openai/concepts/model-retirements"))
    n_api = Note(1090, "In the API, lifecycleStatus Deprecated means RETIRED - a model the docs call Deprecated appears as Deprecating. Check lifecycleStatus and deprecation.inference together; also read deprecation.fineTune and the per-SKU deprecationDate.",
                 kind="gotcha", title="'Deprecated' means different things")
    n_api.place(cv, 0, t_api.bottom + 36)
    t_sched = Table([("Model and version", 330), ("Retires", 170), ("Replacement and notes", 620)], [
        ["gpt-4o 2024-05-13", ("Jan 14, 2027", "red"), "gpt-5.1 2025-11-13. Global Standard and Data Zone Standard auto-upgrade; Provisioned does not; the shared date does not imply auto-upgrade for Global Batch"],
        ["gpt-4o 2024-08-06 and 2024-11-20; gpt-4o-mini 2024-07-18; gpt-4.1-mini 2025-04-14", ("Apr 14, 2027", "red"), "All active base-model inference offers in Azure public cloud; see the schedule for each replacement"],
        ["gpt-4o (Regional Standard)", "Retired Mar 31, 2026", "That date is unchanged"],
        ["codex-mini 2025-05-16", ("Nov 15, 2026", "red"), "No replacement listed"],
        ["o1, o1-pro, o3, o3-deep-research", ("Nov 19, 2026", "red"), "gpt-5.6-sol is the listed replacement"],
        ["Fine-tuned gpt-4o 2024-08-06", "Deployment: Oct 1, 2027", "Training retires no earlier than 2027-04-01 for existing customers; no auto-upgrade - re-tune early on the replacement base model"],
    ], w=1120, theme="red", size=14, head_size=15, title=f"Examples from the schedule ({ASOF}; verify the live page)", title_size=20)
    t_sched.place(cv, 1130, y)
    cv.text(1130, t_sched.bottom + 6, "Learn: Model retirement schedule", size=12, color=LINK, link=learn("openai/concepts/model-retirement-schedule"))
    # provisioned migration paths
    px0 = 2290
    pw = W - px0
    prov = Card(pw, "Provisioned: migrate by hand", [
        "# In place",
        "Same name and size; change the version in portal, REST or CLI (family change via REST or CLI)",
        "A 20-30 minute 'updating' window, no downtime",
        "# Side by side",
        "Create the new deployment, shift traffic, confirm Azure OpenAI Requests shows no calls for 5-10 minutes, delete the old one",
        "Needs quota and capacity for both during the overlap; same deployment type only",
    ], theme="yellow", icon="versions", src=[("Model lifecycle", learn("openai/concepts/model-retirements"))])
    prov.place(cv, px0, y)
    y = max(t_api.bottom, n_api.bottom, t_sched.bottom + 30, prov.bottom) + 60

    # ---- 6-phase migration ribbon
    cv.text(0, y, "Regression-test on upgrade: the six-phase migration", size=26, color="#1864ab")
    cv.text(560, y + 8, "Build and freeze the test dataset FIRST, so every model is scored on the same ruler", size=16, color="#495057")
    y += 50
    phases = [
        ("1  Discover", "Find affected deployments: Models API lifecycleStatus and dates, Service Health advisories", "blue"),
        ("2  Assess", "Freeze the test dataset; baseline the source model, then score the target on the same set", "blue"),
        ("3  Adapt", "Adapt prompts and schemas with Prompt Optimizer, the agent optimizer or the simulator", "violet"),
        ("4  Validate", "Compare quality, latency (TTFT, throughput) and cost per request against the baseline", "violet"),
        ("5  Roll out", "Canary, weighted or shadow with your own gateway weights; keep a rollback corridor (about 30 days typical)", "green"),
        ("6  Retire", "Delete the old deployment, archive the evaluations, update the docs; fold new traces into the golden dataset", "gray"),
    ]
    pw6 = (W - 5 * 56) / 6
    pb = []
    for i, (t, d, th) in enumerate(phases):
        b = Box(pw6, t, h=176, theme=th, sub=d, size=22, sub_size=15, fill="solid")
        b.place(cv, i * (pw6 + 56), y)
        pb.append(b)
    for a, b in zip(pb, pb[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=3)
    cv.text(0, pb[0].bottom + 8, "Learn: Model migration process", size=12, color=LINK, link=learn("foundry-models/concepts/model-migration"))
    y = pb[0].bottom + 40
    opt = Card(980, "Agent optimizer for quality-to-cost trade-offs", [
        "Targets instruction tuning, skill improvement, tool-description optimization and model selection (quality-to-cost)",
        "Needs an evaluation model and an optimization model deployed in the project; tool calls execute during runs - use test endpoints",
        "Hosted-agent optimization requires the Responses protocol and hosted-agent regions (not Norway East)",
        "Proposes only: azd ai agent optimize apply --candidate <id>, then azd deploy, is explicit",
    ], theme="green", icon="agent", badge="preview", src=[("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
                                                        ("Optimize cost and performance", learn("control-plane/how-to-optimize-cost-performance"))])
    opt.place(cv, 0, y)
    with cv.panel(1020, y, title="Composite score (0 to 1): how much did it move?", sub="improvement bands from the optimizer docs", theme="green", style="dotted", pad=20,
                  title_size=22, w=980) as sc:
        bw = 215
        bands = [("under 0.03", "noise", "gray"), ("0.03 to 0.10", "moderate", "yellow"), ("0.10 to 0.20", "significant", "green"), ("over 0.20", "major", "blue")]
        for i, (r, l, th) in enumerate(bands):
            Box(bw, l, h=84, theme=th, sub=r, size=18, sub_size=15, fill="solid").place(cv, sc.ix + i * (bw + 22), sc.iy + 4)
    fnote = Note(W - 2040, "Production content capture is opt-in and never retroactive: turn on trace capture before the next migration, not during it.", kind="tip",
                 title="Golden dataset", src=[("Model migration", learn("foundry-models/concepts/model-migration"))])
    fnote.place(cv, 2040, y)
    agcl = Note(W - 2040, "Agents (classic) is deprecated and retires March 31, 2027 (as of 2026-11-03): migrate to the GA Agent Service.", kind="warn", title="Platform lifecycle",
                src=[("Classic monitor reference", learn("agents/reference/monitor-service", base="azure/foundry-classic"))])
    agcl.place(cv, 2040, fnote.bottom + 20)
    y = max(opt.bottom, sc.bottom, agcl.bottom) + 70

    # ================================================================== 8. GOTCHAS
    section_header(cv, 0, y, "Watch out", size=32)
    y += 62
    nw3 = (W - 2 * 40) / 3
    gs = [
        Note(nw3, "PTU billing continues for deleted resources until they are purged, and reservations do not follow deletions.", kind="gotcha", title="Deleted is not stopped"),
        Note(nw3, "Standard quota is subscription-scoped: load balancing across instances in one subscription adds no throughput.", kind="warn", title="More instances, same quota"),
        Note(nw3, "Hard spend caps do not exist. Build automation off budget action groups, and put token limits at the gateway.", kind="gotcha", title="No kill switch"),
        Note(nw3, "Retirement dates cannot be extended and Provisioned has no auto-upgrade safety net.", kind="gotcha", title="The date is the date"),
        Note(nw3, "NoAutoUpgrade plus a missed date means the deployment stops working. Track retirement dates like certificates.", kind="gotcha", title="NoAutoUpgrade = outage risk"),
        Note(nw3, "Foundry cost estimates exclude PTU and some agent types - reconcile in Cost Management before you act on them.", kind="warn", title="Estimates are not the invoice"),
    ]
    row(cv, 0, y, gs[:3], gap=40)
    r2b = row(cv, 0, gs[0].bottom + 24, gs[3:], gap=40)[1]
    y = r2b + 70

    # ================================================================== SOURCES
    sources(cv, 0, y, [
        ("Provisioned throughput", learn("openai/concepts/provisioned-throughput")),
        ("Provisioned throughput billing and reservations", learn("openai/concepts/provisioned-throughput-billing")),
        ("Get started with provisioned deployments", learn("openai/how-to/provisioned-get-started")),
        ("Spillover traffic management", learn("openai/how-to/spillover-traffic-management")),
        ("Manage quota", learn("openai/how-to/quota")),
        ("Working with models (upgrade policy)", learn("openai/how-to/working-with-models")),
        ("Plan and manage costs", learn("concepts/manage-costs")),
        ("Enforce token limits (Control Plane + AI Gateway)", learn("control-plane/how-to-enforce-limits-models")),
        ("Foundry Models lifecycle and support policy", learn("openai/concepts/model-retirements")),
        ("Model retirement schedule", learn("openai/concepts/model-retirement-schedule")),
        ("Model migration process", learn("foundry-models/concepts/model-migration")),
        ("Deployment types", learn("foundry-models/concepts/deployment-types")),
        ("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
        ("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
        ("CAF: integrate, manage and operate AI agents", learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base="")),
        ("Baseline Foundry chat architecture (cost)", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")),
        ("AI gateway capabilities in Azure API Management", learn("azure/api-management/genai-gateway-capabilities", base="")),
        ("Analyze unexpected charges (anomaly alerts)", learn("azure/cost-management-billing/understand/analyze-unexpected-charges", base="")),
    ], w=W, cols=3)
