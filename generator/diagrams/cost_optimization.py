"""Foundry cost optimization - levers, guardrails and a 'pick your lane' decision flow (documented guidance first)."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="cost-optimization", title="Cost optimization: levers and decision flow", section="2",
    group="Control plane and cost", order=54,
    description="Pick your lane (router, Batch, Flex, Priority, PTU), set the guardrails, then pull the levers - caching, limits, hosting, evaluation, commitments - with savings, trade-offs and where to set each one.",
    tags=["cost", "finops", "ptu", "prompt-caching", "quota", "decision-flow"],
)

W = 3600
ASOF = "as of 2026-11-03"
DASH_GRAY = "#495057"
BILLING = "Meters and billing units: see the 'Cost and billing' canvas"


# ====================================================================== top: title, key, lever strip
def _top(cv: Canvas) -> float:
    _, bottom = title_block(
        cv, 0, 0, "Cost optimization in Microsoft Foundry",
        "Levers, guardrails and a decision flow: spend less per good answer without breaking quality, latency or residency",
        w=W)
    y = bottom + 30
    with cv.panel(0, y, title="How to read this canvas", theme="gray", style="dotted", pad=24, title_size=22, w=W) as key:
        chips = [
            Chip("Documented on Microsoft Learn", theme="blue", size=16),
            Chip("Documented on the Azure.com pricing page", theme="cyan", size=16),
            Chip("General FinOps practice - not Foundry-specific guidance", theme="gray", size=16, dash="dashed", fill="none"),
            Chip("Synthesis - inferred, not stated verbatim in a doc", theme="gray", size=16, dash="dashed", fill="soft"),
            Chip("Preview feature", theme="orange", size=16),
            Chip("Facts " + ASOF, theme="yellow", size=16),
        ]
        flow = ChipFlow(chips, 2330, gap=12)
        flow.place(cv, key.ix, key.iy)
        cv.text(key.ix, flow.y + flow.h + 14,
                "Lever tables: the Basis column says where each claim comes from; a dashed outline marks anything that is not "
                "documented as Foundry guidance. No currency prices are quoted - the pricing pages load them dynamically.",
                size=15, color=MUTED, wrap=2330)
        n = Note(1130, "This canvas is about the levers. The meters and billing units - what each setting is actually charged on - "
                       "are drawn on the separate 'Cost and billing' canvas (id: cost-and-billing).",
                 kind="key", title="Where are the meters?")
        n.place(cv, key.ix + 2330 + 70, key.iy - 4)
    return key.bottom


def _strip(cv: Canvas, y: float) -> float:
    _, b = section_header(cv, 0, y, "Eight lever groups", "The same numbers head the lever tables further down", size=32)
    levers = [
        (1, "Model choice", "blue", "openai",
         ["Smaller model where quality allows", "Model router: Balanced, Cost or Quality", "Policy: approved models, no previews"]),
        (2, "Deployment type and tier", "blue", "regions",
         ["Global Standard first: lowest price", "Batch and Flex: 50% discount", "Priority or PTU when latency matters"]),
        (3, "Prompt and cache", "blue", "redis",
         ["Stable prefix first, >= 1,024 tokens", "prompt_cache_key + breakpoints (GPT-5.6+)", "Watch cached vs cache-write tokens"]),
        (4, "Output and tool discipline", "orange", "toolbox-icon",
         ["Cap output tokens, short instructions", "Scope tools: each adds tokens per turn", "Rate-limit tool calls at the gateway"]),
        (5, "Limits and quotas", "yellow", "quotas",
         ["Split quota across projects", "Gateway TPM + token quota per project", "Budgets alert but never stop spend"]),
        (6, "Agents and hosting", "green", "agent",
         ["Hosted agents: idle timeout 2-240 min", "Right-size 0.5 / 1 / 2 vCPU sandboxes", "Stop idle agents; free AI Search tier"]),
        (7, "Evaluation and observability", "violet", "app-insights",
         ["Playground evaluations are on and billed", "Sample continuous eval; cap runs per hour", "Sample traces; set retention"]),
        (8, "Fine-tuning and commitments", "yellow", "reservations",
         ["Prompt first: fine-tune hosting is hourly", "PTU right-size + spillover", "Reservation after capacity is deployed"]),
    ]
    gap = 36
    cw = (W - 7 * gap) / 8
    cards = [Card(cw, t, body, theme=th, icon=ic) for _, t, th, ic, body in levers]
    row(cv, 0, b + 40, cards, gap=gap)
    for c, (n, _, th, _, _) in zip(cards, levers):
        numbered(cv, c.x + 2, c.y + 2, n, theme=th, d=36, size=20)
    return max(c.bottom for c in cards)


# ====================================================================== decision flow
def _bus(cv: Canvas, q: Box, cards: list, bus_x: float, label: str | None = None) -> None:
    """Tree connector from a decision diamond to several outcome cards stacked below it."""
    x0, y0 = q.pt("bottom")
    ytrunk = cards[0].y - 34
    arrow(cv, [(x0, y0 + 5), (x0, ytrunk), (bus_x, ytrunk), (bus_x, cards[-1].cy)], end_head=None, sw=2)
    for c in cards:
        arrow(cv, [(bus_x, c.cy), (c.x - 5, c.cy)], sw=2)
    if label:
        cv.text(x0 + 10, y0 + 8, label, size=16)


def _decision(cv: Canvas, y: float) -> float:
    CW, GAP = 620, 110           # column width / gap
    BUS, CL, CWID = 20, 56, 560  # bus-lane offset, card offset and card width inside a column
    DW, DH = 450, 170            # question diamond
    with cv.panel(0, y, title="Pick your lane: how should this workload be served?",
                  sub="Decision flow assembled from the deployment-type, instant-access, managed-compute, Flex, Priority and "
                      "provisioned-throughput pages (" + ASOF + ")",
                  theme="yellow", style="dotted", pad=30, title_size=30, sub_size=16, w=W) as p:
        col = [p.ix + i * (CW + GAP) for i in range(5)]
        cx = [c + CL + CWID / 2 for c in col]
        start = Box(320, "A workload needs a model", h=54, theme="gray", fill="solid", size=18).place(cv, cx[0] - 160, p.iy)
        yq = start.bottom + 56
        qs = []
        for i, label in enumerate([
                "Just trying or prototyping a model?",
                "Open-source or custom weights that need dedicated GPUs?",
                "Any data-residency constraint?",
                "Is a user waiting for the answer?",
                "Need consistent low latency or guaranteed throughput?"]):
            qs.append(Box(DW, label, h=DH, shape="diamond", theme="yellow", fill="solid", size=18, color=INK)
                      .place(cv, cx[i] - DW / 2, yq))
        connect(cv, start, qs[0], a_side="bottom", b_side="top")
        connect(cv, qs[0], qs[1], a_side="right", b_side="left", label="no", label_size=17)
        connect(cv, qs[1], qs[2], a_side="right", b_side="left", label="no: serverless models", label_size=16)
        connect(cv, qs[2], qs[3], a_side="right", b_side="left", label="then pick the tier", label_size=16)
        connect(cv, qs[3], qs[4], a_side="right", b_side="left", label="yes", label_size=17)
        yo = yq + DH + 84

        instant = Card(CWID, "Instant access", [
            "Call a supported model by name - no deployment",
            "Projects in West US 3 only (preview)",
            "Draws from a global quota pool; no custom guardrails per model",
            "! Billing meter is not stated on the Learn page",
        ], theme="blue", badge="preview", icon="preview-features", subtitle="Yes: just trying or prototyping",
            src=[("Instant access to models", learn("concepts/instant-models"))])
        instant.place(cv, col[0] + CL, yo)
        managed = Card(CWID, "Managed compute", [
            "Open-source models on dedicated GPUs; billed hourly per accelerator",
            "Global deployment only for now (" + ASOF + ")",
            "! Bills while deployed, even with no traffic - delete when idle",
        ], theme="blue", badge="preview", icon="vm", subtitle="Yes: open-source or custom weights",
            src=[("Managed compute", learn("concepts/managed-compute-overview"))])
        managed.place(cv, col[1] + CL, yo)
        connect(cv, qs[0], instant, a_side="bottom", b_side="top", label="yes", label_size=17)
        connect(cv, qs[1], managed, a_side="bottom", b_side="top", label="yes", label_size=17)

        dt = [("Deployment types", learn("foundry-models/concepts/deployment-types"))]
        scope = [
            Card(CWID, "Global", ["Lowest price, launches first, broadest regions", "Processed in any region; more latency variance at high volume"],
                 theme="blue", icon="globe", subtitle="No residency constraint", src=dt),
            Card(CWID, "Data Zone", ["Processed inside the US, EU or APAC data zone", "Data Zone Standard, Provisioned or Batch"],
                 theme="blue", icon="regions", subtitle="A zone", src=dt),
            Card(CWID, "Standard / Regional Provisioned", ["Processed in your Azure geography", "Arrive last, with no guaranteed availability date"],
                 theme="blue", icon="regions", subtitle="A geography", src=dt),
        ]
        sy = yo
        for c in scope:
            c.place(cv, col[2] + CL, sy)
            sy += c.h + 18
        _bus(cv, qs[2], scope, col[2] + BUS)
        Note(CWID, "Scope + tier = deployment type, for example Global Batch, Data Zone Provisioned or Regional Provisioned. "
                   "Not every model supports every type.", kind="info", title="Scope sets the prefix").place(cv, col[2] + CL, sy + 6)

        batch = Card(CWID, "Batch", [
            "Global Batch or Data Zone Batch: 50% discount",
            "24-hour target, separate quota, no real-time SLA",
        ], theme="blue", icon="batch", subtitle="No: a huge file of independent requests", src=dt)
        flex = Card(CWID, "Flex processing", [
            "50% off tokens on a Global Standard deployment: service_tier = flex per request",
            "429 when capacity is short - you retry, or fall back with service_tier = default",
            "Documented uses: evaluations, data enrichment, document analysis, async workflows",
        ], theme="blue", badge="preview", icon="scheduler", subtitle="No, but you want a synchronous API and can retry",
            src=[("Flex processing", learn("openai/how-to/flex-processing"))])
        by = yo
        for c in (batch, flex):
            c.place(cv, col[3] + CL, by)
            by += c.h + 18
        _bus(cv, qs[3], [batch, flex], col[3] + BUS, label="no")
        Note(CWID, "Supported on Global Standard (" + ASOF + "): gpt-6.1-sol, gpt-6-sol, gpt-6-luna, gpt-6-astra, "
                   "gpt-5.6-sol, gpt-5.6-luna, gpt-5.6-terra. An unsupported model returns HTTP 400 - check the table first.",
             kind="warn", title="Flex model list is short").place(cv, col[3] + CL, by + 6)

        std = Card(CWID, "Standard or Global Standard", [
            "Best effort, pay per token - the default for most workloads",
            "Global Standard: lowest price and highest quota",
        ], theme="blue", icon="openai", subtitle="No: best effort is fine", src=dt)
        ptu = Card(CWID, "Provisioned throughput (PTU)", [
            "Billed hourly per deployed PTU, used or not",
            "Add a Reservation once deployed and stable",
            "Add spillover to a Standard deployment for bursts",
        ], theme="yellow", icon="reservations", subtitle="Yes: steady, predictable, high volume (mission-critical)",
            src=[("Provisioned throughput billing", learn("openai/concepts/provisioned-throughput-billing"))])
        prio = Card(CWID, "Priority processing", [
            "Pay-as-you-go on Global Standard or Data Zone Standard (US)",
            "Downgraded to Standard if TPM ramps >50% in <15 min",
            "Routinely hitting ramp limits? Consider PTU",
        ], theme="blue", icon="metrics", subtitle="Yes: bursty or business-hours traffic, no commitment",
            src=[("Priority processing", learn("openai/concepts/priority-processing"))])
        cy5 = yo
        for c in (std, ptu, prio):
            c.place(cv, col[4] + CL, cy5)
            cy5 += c.h + 18
        _bus(cv, qs[4], [std, ptu, prio], col[4] + BUS)

        yb = max(instant.bottom, managed.bottom) + 60
        with cv.panel(col[0], yb, title="Side branch: fine-tuned models", sub="a separate question - ask it after the lane is chosen",
                      theme="gray", style="dashed", pad=24, title_size=22, sub_size=15) as sb:
            q6 = Box(330, "Fine-tuned model?", h=130, shape="diamond", theme="yellow", fill="solid", size=18, color=INK)
            dev = Card(390, "Developer tier", [
                "No hourly hosting fee; token rates = Global Standard",
                "Removed after 24 h; no SLA or residency guarantee",
            ], theme="blue", icon="foundry", subtitle="Yes: evaluate it here first",
                src=[("Fine-tuning cost management", learn("fine-tuning/cost-management"))])
            host = Card(430, "Then host it", [
                "Standard or Global Standard: hourly hosting fee (30 days = 720 x rate)",
                "Regional Provisioned: PTU-hours",
                "! The fee runs even at zero traffic - delete unused deployments",
            ], theme="blue", icon="cubes", subtitle="Production serving")
            top = sb.iy
            q6.place(cv, sb.ix, top + 10)
            dev.place(cv, q6.right + 90, top)
            host.place(cv, dev.right + 90, top, h=dev.h)
            connect(cv, q6, dev, a_side="right", b_side="left", label="yes", label_size=17)
            connect(cv, dev, host, a_side="right", b_side="left", label="then", label_size=16)
    return p.bottom


# ====================================================================== guardrail stack + cost-control loop
def _guardrails(cv: Canvas, y: float) -> float:
    _, b = section_header(cv, 0, y, "Guardrail stack: prevent, cap, alert, observe, commit",
                          "Budgets only alert. The AI gateway token quota is a hard cap on tokens, not on currency.", size=32)
    gap = 40.8
    cw = (W - 5 * gap) / 6
    pc = [("Plan and manage costs", learn("concepts/manage-costs"))]
    cards = [
        Card(cw, "Azure Policy", [
            "Approved-models and eligibility policies (GA) gate every model deployment",
            "Deny previews, or allow only Direct-from-Azure models",
            "A custom policy can target a deployment type (docs show the condition only)",
            "Instant access can be switched off per subscription",
        ], theme="grape", icon="policy", subtitle="1  Prevent costly setups",
            src=[("Policies for model deployment", learn("how-to/model-deployment-policy"))]),
        Card(cw, "Foundry quota", [
            "TPM quota per subscription, region and model; PTU quota has no cost",
            "Split it across projects in Manage > Quota",
            "Shared quota pool: test endpoints only, usage-billed",
            "! Quota never guarantees PTU capacity",
        ], theme="yellow", icon="quotas", badge="ga", subtitle="2  Cap capacity per project",
            src=[("Manage and increase quotas", learn("how-to/quota"))]),
        Card(cw, "AI gateway token limits", [
            "TPM rate limit per project and deployment: 429 above it",
            "Total token quota per period (hourly to yearly): 403 above it",
            "Concurrent requests can briefly overshoot",
            "Needs an API Management instance - delete it when you retire projects",
        ], theme="grape", icon="apim", badge="preview", subtitle="3  Cap usage per project",
            src=[("Enforce token limits", learn("control-plane/how-to-enforce-limits-models"))]),
        Card(cw, "Budgets and alerts", [
            "Budgets on subscriptions or resource groups, filtered to resources or services",
            "! No hard stop for Azure OpenAI; action groups can start custom automation",
            "Tune thresholds only after a full billing-cycle trend",
        ], theme="yellow", icon="cost-management", subtitle="4  Alert before the invoice", src=pc),
        Card(cw, "Monitor and attribute", [
            "Operate > Overview: Estimated cost tile (agents; prompt agents excluded)",
            "Build > Models > Monitor: deployment cost chart (standard, not PTU)",
            "Cost analysis: group by Resource, then Meter; filter by the project tag (preview)",
            "Estimates skip discounts - the invoice is the source of truth",
        ], theme="violet", icon="monitor", subtitle="5  Observe and allocate", src=pc),
        Card(cw, "Reservation utilization", [
            "Watch Utilization % on PTU reservations",
            "Deploy first, then reserve exactly the deployed PTUs",
            "Deleting a deployment does not cancel a reservation",
            "Agent pre-purchase plans apply after PTU reservations",
        ], theme="yellow", icon="reservations", subtitle="6  Commit and keep it used",
            src=[("PTU billing and reservations", learn("openai/concepts/provisioned-throughput-billing"))]),
    ]
    y0 = b + 40
    row(cv, 0, y0, cards, gap=gap)
    for a, c in zip(cards, cards[1:]):
        connect(cv, a, c, a_side="right", b_side="left", sw=3)
    cv.text(0, max(c.bottom for c in cards) + 10, BILLING + ".  Estimates and charts are near-real-time aids; reconcile against Cost Management and the invoice.",
            size=15, color=MUTED)

    ly = max(c.bottom for c in cards) + 56
    with cv.panel(0, ly, title="The cost-control loop", sub="Setup order assembled from the Foundry cost pages; the monthly review is general FinOps practice",
                  theme="gray", style="dotted", pad=26, title_size=24, sub_size=15, w=W) as lp:
        steps = [
            ("Pick a lane", "decision flow above", "yellow", False),
            ("Pick the tier and model", "router, Batch, Flex, Priority or PTU", "blue", False),
            ("Set quota and gateway limits", "per project and deployment", "yellow", False),
            ("Add Policy guardrails", "approved models, previews, deployment type", "grape", False),
            ("Tag and attribute", "project, deployment and user tags; cost exports", "gray", False),
            ("Budget and alert", "no built-in hard stop", "yellow", False),
            ("Monitor and reconcile", "Estimated cost, reservation utilization; Resource, then Meter", "violet", False),
            ("Revisit monthly", "general FinOps: idle deployments, orphaned APIM instances, thresholds", "gray", True),
        ]
        sg = 50
        bw = (W - 2 * 26 - 7 * sg) / 8
        boxes = []
        bx = lp.ix
        for i, (t, sub, th, dashed) in enumerate(steps):
            bx_ = Box(bw, t, sub=sub, theme=th, fill="none" if dashed else "solid", dash="dashed" if dashed else "solid",
                      h=126, size=17, sub_size=14, color=INK if not dashed else DASH_GRAY)
            bx_.place(cv, bx, lp.iy + 14)
            boxes.append(bx_)
            bx += bw + sg
        for a, c in zip(boxes, boxes[1:]):
            connect(cv, a, c, a_side="right", b_side="left", sw=3)
        for i, bx_ in enumerate(boxes):
            numbered(cv, bx_.x + 4, bx_.y + 4, i + 1, theme=steps[i][2], d=32, size=18)
        yb = boxes[0].bottom + 40
        arrow(cv, [(boxes[-1].cx, boxes[-1].bottom + 6), (boxes[-1].cx, yb), (boxes[0].cx, yb), (boxes[0].cx, boxes[0].bottom + 6)],
              dash="dashed", sw=2, label="repeat every month: estimate, test, reconcile, adjust", label_size=16, label_pos="below")
    return lp.bottom


# ====================================================================== lever tables
COLS = [("Lever", 330), ("Savings mechanism", 430), ("Trade-off / watch-out", 500), ("Where to set it", 390), ("Basis", 130)]
BASIS = {
    "docs": ("Docs", None, False),
    "voice": ("Docs (voice)", None, False),
    "preview": ("Docs, preview", "orange", False),
    "limited": ("Docs, limited preview", "orange", False),
    "price": ("Pricing page", "cyan", False),
    "finops": ("General FinOps", "gray", True),
    "synth": ("Synthesis", "gray", True),
}


def _lever_table(cv: Canvas, x: float, y: float, title: str, theme: str, rows: list) -> Table:
    body, flags = [], []
    for lever, save, trade, where, basis in rows:
        text, th, dashed = BASIS[basis]
        body.append([lever, save, trade, where, {"text": text, "theme": th} if th else text])
        flags.append(dashed)
    t = Table(COLS, body, theme=theme, size=14, head_size=15, pad_y=6, title=title, title_size=24, first_col_theme=theme)
    t.place(cv, x, y)
    ry = t.y + t.title_h + t.head_h
    for h, dashed in zip(t.row_h, flags):
        if dashed:
            cv.rect(t.x + 2, ry + 2, t.w - 4, h - 4, stroke=DASH_GRAY, fill="transparent", sw=2, dash="dashed", round_=False, rough=0)
        ry += h
    return t


def _tables(cv: Canvas, y: float) -> float:
    _, b = section_header(cv, 0, y, "Lever table: lever x savings mechanism x trade-off x where to set it",
                          "Group numbers match the strip above. Dashed rows are general FinOps practice or synthesis; every other row is documented (" + ASOF + ").",
                          size=32)
    left = [
        ("1  Model choice", "blue", [
            ("Smaller or cheaper model where quality allows", "Lower per-token price",
             "Evaluate first: evaluation runs use quota and tokens", "Model deployment chosen for the agent or app", "docs"),
            ("Model router: one deployment, per-request model choice",
             "Cheaper models take simpler prompts. Balanced (default) picks the cheapest model within ~1-2% of the best quality; Cost mode within ~5-6%",
             "Router input-token meter (see Docs disagree); Auto-update changes the model set and cost; benchmark against your baseline; Global and Data Zone Standard only",
             "Custom deploy: routing mode + model subset (>= 2 models for fallback)", "docs"),
            ("Limit which models and previews can be deployed", "Stops costly or unvetted deployments before they exist",
             "Checked at deploy time; Deny does not remove existing deployments; the router honours the same policy",
             "Azure Policy: approved models + eligibility (denyPreviewModels, onlyAllowDirectFromAzure) at management group, subscription or resource group", "docs"),
        ]),
        ("2  Deployment type and tier", "blue", [
            ("Default to Global Standard", "Lowest price, highest quota, launches first, broadest regions",
             "Processed in any region; more latency variance at high volume", "Deployment type when you create the deployment", "docs"),
            ("Batch (Global or Data Zone Batch)", "50% discount for non-urgent bulk work",
             "24-hour target; separate enqueued-token quota; no real-time SLA", "Deployment type: Global Batch or Data Zone Batch (model support varies)", "docs"),
            ("Flex processing", "50% off input and output tokens, plus the cached-token discount",
             "No SLA; 429 when capacity is short (not billed); shares Global Standard quota; unsupported model = HTTP 400; no automatic fallback",
             "Request: service_tier = flex on a Global Standard deployment", "preview"),
            ("Priority instead of over-buying PTU for bursty traffic", "Consistent low latency, pay-as-you-go, no commitment",
             "Priority rate (premium not stated on Learn); downgraded requests bill at Standard; ramp-rate limit: TPM up >50% in <15 min",
             "Deployment toggle or properties.service_tier = priority; per-request service_tier", "docs"),
            ("Provisioned throughput (PTU) for steady high volume", "Predictable hourly cost; PTU quota is free; cached tokens count less toward PTU",
             "Billed hourly while deployed, even when idle; quota does not guarantee capacity",
             "Deployment type: Global, Data Zone or Regional Provisioned; capacity calculator on the Quota page", "docs"),
            ("Developer tier for fine-tuned model evaluation", "No hourly hosting fee; token rates = Global Standard",
             "Evaluation only: removed after 24 h, no SLA, no residency guarantee", "Deployment type: Developer", "docs"),
        ]),
        ("3  Prompt and cache", "blue", [
            ("Stable content first; append-only history; >= 1,024 identical leading tokens",
             "Cache reads are discounted (Standard) or up to 100% off (Provisioned); lower latency",
             "One changed character in the first 1,024 tokens = a miss; the in-memory cache clears after ~5-10 min idle and always within 1 h",
             "Prompt and message structure in your app", "docs"),
            ("prompt_cache_key with a stable key-to-prefix mapping (GPT-5.6+)", "Better cache matching for related requests",
             "Above ~15 requests/min per prefix + key some requests may miss: spread across keys", "Request parameter prompt_cache_key", "docs"),
            ("Explicit breakpoints after stable blocks (GPT-5.6+, Standard)", "Control cache-write spend: favour reads over writes",
             "GPT-5.6+ cache writes can cost extra; max 4 new writes per request; PTU-M has no breakpoints",
             "prompt_cache_options.mode (implicit default or explicit), ttl 30m, prompt_cache_breakpoint on a content block", "docs"),
            ("Switch caching off deliberately", "mode explicit + no breakpoints = no caching and no cache-write charges",
             "Gives up read discounts; earlier models and PTU-M cannot turn caching off", "prompt_cache_options.mode = explicit (Standard, GPT-5.6+)", "docs"),
            ("Extended retention (up to 24 h)", "More hits across idle gaps; same cache pricing",
             "Listed models only (default on gpt-5.5); GPT-5.6+ uses ttl instead", "prompt_cache_retention = 24h (models before GPT-5.6)", "docs"),
            ("Router session affinity", "Better chance of cache reuse across related turns",
             "Chat Completions only; best effort - no guaranteed hit", "routing_config.session_affinity or x-ms-session-id header", "preview"),
            ("Cache rate in PTU sizing", "Learn example: 0% cache = 110 PTUs, 50% cache = 80 PTUs",
             "The 100% deduction does not apply to GPT-6 Astra, GPT-6 Sol or GPT-6.1 Sol: cached input and cache writes still use PTU",
             "Sizing formula or capacity calculator", "docs"),
            ("Monitor cached_tokens and cache_write_tokens", "Confirms the savings are real",
             "cache_write_tokens is reported on Standard with GPT-5.6+ only", "Response usage.prompt_tokens_details", "docs"),
        ]),
        ("4  Output and tool discipline", "orange", [
            ("Cap output, keep instructions short, scope tools",
             "Fewer tokens every turn: instructions are resent each turn; each attached tool adds tokens even if never called",
             "Documented on the voice-agent pricing page; applying it to text agents is our extension", "Agent definition: max_output_tokens, instructions, attached tools", "voice"),
            ("Static interim responses, end_conversation, store off (voice agents)", "Avoids extra model calls and storage",
             "llm_interim_response adds a model call on every trigger; store = true adds transcript and audio storage", "Voice agent definition", "docs"),
            ("Reuse a Code Interpreter session inside its 1-hour window", "One session charge instead of several",
             "Parallel conversations each create a session; 30-minute idle timeout", "App logic: keep related work in one conversation", "docs"),
            ("Rate-limit tool calls at the gateway", "Caps tool spend and abuse, e.g. rate-limit-by-key 60 calls/min per IP",
             "Only new MCP tools made in the Foundry portal without managed OAuth are routed; blocked calls return 429",
             "API Management policy on the AI gateway (Azure portal, not the Foundry portal)", "preview"),
            ("max_tool_calls (Responses API parameter)", "Could bound tool loops",
             "Semantics are not documented on the pages read: verify in the API reference first", "Responses API request", "synth"),
            ("Watch vector-store growth", "File search is billed per GB-day of vector storage; the first GB is free",
             "Pricing-page fact (" + ASOF + ")", "Vector stores and files in the project", "price"),
        ]),
    ]
    right = [
        ("5  Limits and quotas as guardrails", "yellow", [
            ("Split Foundry quota across projects", "Caps what each project can burn; quota itself is free",
             "TPM per subscription, region and model; changes take up to 15 min; the shared pool is for test endpoints only",
             "Manage > Quota (Token per minute and Provisioned throughput unit tabs)", "docs"),
            ("AI gateway: TPM limit + total token quota per project and deployment",
             "Hard cap on aggregate usage: 429 over the TPM limit, 403 over the quota (hourly to yearly)",
             "Needs an API Management instance; concurrent requests can briefly overshoot; delete the instance when you retire the projects",
             "Manage > AI Gateway > Token management > + Set limit", "preview"),
            ("Budgets and alerts with action-group automation", "Early warning before the invoice",
             "No built-in hard stop for Azure OpenAI; automation needs custom development; tune thresholds after a full billing-cycle trend",
             "Azure Cost Management > Budgets", "docs"),
            ("Policy: block a deployment type or instant access", "Prevents cost-leaking configurations",
             "A deployment-type ban is a custom policy on deployments/sku.name (docs show the condition only)",
             "Azure Policy at management group, subscription or resource group", "docs"),
            ("Separate Foundry resources for prod and exploration", "Independent quota and cost boundaries; exploration instance with limited capacity",
             "A shared resource shares its blast radius: incidents, quota exhaustion, misconfiguration", "Resource topology (planning phase)", "docs"),
        ]),
        ("6  Agents and hosting", "green", [
            ("Hosted agents: tune the idle timeout", "Compute is deprovisioned when idle (scale to zero, stateful resume): pay for active sessions only",
             "2-240 min, default 15; a session is deleted after 30 days idle; billing = CPU + memory across active sessions", "Idle timeout per agent version", "docs"),
            ("Right-size the sandbox (0.5, 1 or 2 vCPU)", "Oversizing multiplies cost by your concurrency",
             "Raise if sustained peaks > ~70% of allocation; lower if far below; each version is immutable, so retest", "cpu and memory on a new agent version", "docs"),
            ("Stop unneeded hosted or published agents", "Attached compute is deallocated",
             "Stopping prevents new runs (existing runs continue); an unpublished prompt agent must be deleted to stop",
             "Operate > Assets > Agents > Update status > Stop", "docs"),
            ("Stop or delete idle sessions", "Stay under the concurrent-session quota",
             "Otherwise creating or resuming a session fails with session_quota_exceeded", "Hosted-agent sessions; limits page", "docs"),
            ("Foundry IQ: start on the free AI Search tier", "Free tier plus a free allocation of agentic-retrieval tokens; lower retrieval reasoning effort",
             "Cost per token depends on reasoning effort; Dedicated suits steady load, Serverless (preview) suits bursty", "Knowledge base settings and the AI Search service tier", "preview"),
            ("Memory: choose smaller chat and embedding models", "Memory bills the chat and embedding models you configure",
             "Pricing and billing can change during the preview", "Memory store configuration", "preview"),
        ]),
        ("7  Evaluation and observability", "violet", [
            ("Turn off playground evaluations when not needed", "Removes the playground evaluation meter: on by default for every project and billed on consumption",
             "You lose the automatic quality scores in the playground", "Agents playground > metrics (upper right) > unselect all evaluators", "docs"),
            ("Smaller judge model, pre-computed outputs, smaller datasets", "Fewer tokens and less quota per evaluation run",
             "Smaller datasets mean less coverage; the judge model counts against your quota", "Evaluation setup: judge deployment and dataset", "docs"),
            ("Continuous evaluation: Random or Intelligent sampling, max traces or runs, max_hourly_runs",
             "Caps the judge tokens spent on production traffic",
             "Default cap is 100 runs/hour; sampling means not every trace is scored", "Monitor dashboard evaluation rule", "preview"),
            ("Schedule evaluations and red teaming instead of running them continuously", "Bounded, predictable evaluation spend",
             "Slower drift detection between runs", "Scheduled evaluation and scheduled red teaming in monitoring", "synth"),
            ("Trace sampling and retention", "Lower Application Insights and Log Analytics ingestion",
             "Fewer traces to debug with. Documented: retention and billing follow your Application Insights and Log Analytics configuration",
             "OTel setup (sampling_ratio appears in the docs sample) + App Insights retention and Log Analytics tier", "finops"),
            ("Agent optimizer: read Minimum, Estimated and Maximum before you submit",
             "Bounds optimization spend: fewer candidates, rows and evaluators; smaller evaluation and optimization models; early stopping can cut usage",
             "Maximum is not a spending limit; the portal estimate covers prompt agents only; runs call your tools too; excludes external services",
             "Optimization wizard Review step; post-run Token usage view", "limited"),
        ]),
        ("8  Fine-tuning and commitments", "yellow", [
            ("Prompt, caching and router first; fine-tune only if needed",
             "Avoids a standing floor: a fine-tuned deployment bills hourly hosting even at zero traffic (30 days = 720 x the hourly rate)",
             "'Prompt first' is our advice; the hosting floor is documented", "Fine-tuning deployment choice", "synth"),
            ("Cheaper training runs", "Global training is discounted; Developer training is preemptible and paused jobs are not charged",
             "No data-residency guarantee; Developer jobs can take longer", "Fine-tuning job: training type", "docs"),
            ("Reinforcement fine-tuning (RFT): start small",
             "reasoning_effort Low, fewer validation examples and eval_samples, smallest grader, tune compute_multiplier; cancel any time",
             "A per-job spending limit pauses the run; resuming continues billing without another cost-based limit", "RFT job settings; monitor in the Foundry portal", "docs"),
            ("Delete unused deployments", "Stops hourly meters: fine-tuned hosting, managed-compute GPUs, PTUs, APIM gateways",
             "Deleting a PTU deployment does not cancel its reservation", "Deployments list; Azure portal for the APIM instance", "docs"),
            ("PTU right-sizing", "Avoids over-buying: PTUs = [input TPM x (1 - cache rate) + ratio x output TPM] / input TPM per PTU, rounded up to the scale increment",
             "Benchmark representative traffic; an estimate is not a load test", "Manage > Quota > capacity calculator", "docs"),
            ("PTU baseline + Standard spillover for spikes", "No need to size PTU to peak; overflow runs on a Standard deployment at token rates",
             "Azure OpenAI models only; PTU is tried first (can add latency); no automatic PTU-to-PTU failover",
             "spilloverDeploymentName on the deployment, or the x-ms-spillover-deployment header", "docs"),
            ("Enterprise PTU pool behind APIM", "One shared Data Zone PTU deployment smooths traffic for higher utilization",
             "Your gateway or app owns the failover chain", "AI gateway or API Management routing", "docs"),
            ("Reservations: deploy first, then buy", "Discounted $/PTU/hr for 1-month or 1-year terms; one Global reservation can cover many regions",
             "No capacity guarantee; size to deployed PTUs; excess billed hourly; cancel or exchange has limits; never scale PTU hourly with traffic",
             "Azure portal > Reservations", "docs"),
            ("Microsoft Agent Pre-Purchase Plan", "1-year commitment for Foundry + Copilot spend: 5% / 10% / 15% tiers (20,000 / 100,000 / 500,000 ACU, pricing page)",
             "Applied after PTU reservations; no cancel or exchange; does not combine with other discounts", "Azure portal > Reservations", "docs"),
            ("Route spend to the right commitment", "Claude CCU is MACC-eligible; Foundry Tools commitment tiers give a fixed fee",
             "Azure Prepayment cannot pay Marketplace models; usage above a commitment tier is billed as overage", "Commercial agreement and Cost Management", "docs"),
        ]),
    ]
    ty = b + 46
    tw = sum(c[1] for c in COLS)
    x2 = W - tw
    bottoms = []
    for x0, group in ((0, left), (x2, right)):
        yy = ty
        for title, theme, rows in group:
            t = _lever_table(cv, x0, yy, title, theme, rows)
            yy = t.bottom + 36
        bottoms.append(yy - 36)
    return max(bottoms)


# ====================================================================== worked loops
def _loops(cv: Canvas, y: float) -> float:
    _, b = section_header(cv, 0, y, "Three worked loops", "PTU right-size and commit, prompt-cache tuning, evaluation spend control", size=32)
    gap = 50
    pw = (W - 2 * gap) / 3
    y0 = b + 40
    inner = pw - 52

    # ---- A: PTU right-size and commit
    with cv.panel(0, y0, title="PTU right-size and commit", sub="Create deployments first, then buy the reservation", theme="yellow",
                  style="dotted", pad=26, title_size=26, sub_size=15, w=pw) as pa:
        sg = 36
        bw = (inner - 3 * sg) / 4
        labels = ["Collect peak RPM, prompt and reply size, cache rate", "Size it: formula or capacity calculator",
                  "Deploy - this confirms capacity is there", "Run production traffic",
                  "Check utilization", "Buy a Reservation = the deployed PTUs",
                  "Add spillover to a Standard deployment", "Consider an enterprise PTU pool behind APIM"]
        bs = []
        for i, lab in enumerate(labels):
            r, c = divmod(i, 4)
            bs.append(Box(bw, lab, h=104, theme="yellow", size=15, color=INK).place(cv, pa.ix + c * (bw + sg), pa.iy + 14 + r * (104 + 74)))
        for i in range(7):
            if i == 3:
                connect(cv, bs[3], bs[4], a_side="bottom", b_side="top", route="elbow", sw=3)
            else:
                connect(cv, bs[i], bs[i + 1], a_side="right", b_side="left", sw=3)
        for i, bx in enumerate(bs):
            numbered(cv, bx.x + 4, bx.y + 4, i + 1, theme="yellow", d=30, size=17)
        fc = Card(inner, "Worked example from the sizing page (gpt-5.2, Data Zone Provisioned)", [
            "= PTUs = [input TPM x (1 - cache rate) + output-to-input ratio x output TPM] / input TPM per PTU, rounded up to the scale increment",
            "1,000 RPM, 200-token prompt, 20-token reply; 3,400 input TPM per PTU; ratio 8",
            "0% cache: (200,000 + 8 x 20,000) / 3,400 = 105.88 -> 110 PTUs",
            "50% cache: (100,000 + 8 x 20,000) / 3,400 = 76.47 -> 80 PTUs (rounded to the nearest 5)",
            "! GPT-6 Astra, GPT-6 Sol and GPT-6.1 Sol and newer use normalized tokens: cached input and cache writes still consume PTU",
        ], theme="yellow", icon="metrics", title_size=18, src=[("Estimate PTUs", learn("openai/how-to/provisioned-throughput-sizing"))])
        fc.place(cv, pa.ix, bs[-1].bottom + 34)
        sc = Card(inner, "Spillover and pooling", [
            "Spillover: set spilloverDeploymentName (or the x-ms-spillover-deployment header) to a Standard deployment in the same resource",
            "Response headers x-ms-spillover-from-deployment and x-ms-spillover-error show a spilled request",
            "Billing: PTU requests = hourly cost only; spilled requests = Standard token rates",
        ], theme="yellow", icon="apim", title_size=18,
            src=[("Spillover traffic management", learn("openai/how-to/spillover-traffic-management")),
                 ("High availability and resiliency", learn("how-to/high-availability-resiliency"))])
        sc.place(cv, pa.ix, fc.bottom + 24)

    # ---- B: prompt-cache tuning loop
    bx0 = pw + gap
    with cv.panel(bx0, y0, title="Prompt-cache tuning loop", sub="Reads are discounted; writes can cost extra on GPT-5.6 and later",
                  theme="blue", style="dotted", pad=26, title_size=26, sub_size=15, w=pw) as pb:
        bw2 = (inner - 150) / 2
        c1 = Box(bw2, "Restructure the prompt: static content first, append-only, >= 1,024 identical leading tokens", h=118, theme="blue", size=15, color=INK).place(cv, pb.ix, pb.iy + 14)
        c2 = Box(bw2, "Add prompt_cache_key and breakpoints (GPT-5.6+)", h=118, theme="blue", size=15, color=INK).place(cv, pb.ix + bw2 + 150, pb.iy + 14)
        c3 = Box(bw2, "Watch cached_tokens against cache_write_tokens", h=118, theme="blue", size=15, color=INK).place(cv, pb.ix + bw2 + 150, c1.bottom + 90)
        c4 = Box(bw2, "Keep requests steady, then adjust", h=118, theme="blue", size=15, color=INK).place(cv, pb.ix, c1.bottom + 90)
        connect(cv, c1, c2, a_side="right", b_side="left", sw=3, label="stable key", label_size=14)
        connect(cv, c2, c3, a_side="bottom", b_side="top", sw=3)
        connect(cv, c3, c4, a_side="left", b_side="right", sw=3, label="steady stream", label_size=14)
        connect(cv, c4, c1, a_side="top", b_side="bottom", sw=3)
        for i, bx in enumerate((c1, c2, c3, c4)):
            numbered(cv, bx.x + 4, bx.y + 4, i + 1, theme="blue", d=30, size=17)
        n1 = Note(inner, "Models before GPT-5.6 do not charge extra to write to the cache. On GPT-5.6 and later, cache writes can incur charges "
                         "in addition to discounted reads (" + ASOF + "). Keep reused content identical across requests, place explicit "
                         "breakpoints only after stable blocks, and compare write volume with later cache reads. "
                         "mode explicit with no breakpoints = no caching and no write charges (Standard, GPT-5.6+).",
                  kind="gotcha", title="The cache-write note", src=[("Prompt caching", learn("openai/how-to/prompt-caching"))])
        n1.place(cv, pb.ix, c3.bottom + 34)
        Note(inner, "Router sessions: with a model router, cached tokens are used automatically when the same model serves consecutive "
                    "requests with overlapping prefixes. Session affinity (Chat Completions, preview) asks the router to try the same model, "
                    "but it never guarantees a cache hit.",
             kind="info", title="Router and caching", src=[("Model router", learn("openai/concepts/model-router"))]).place(cv, pb.ix, n1.bottom + 24)

    # ---- C: evaluation spend control and agent optimizer
    cx0 = 2 * (pw + gap)
    with cv.panel(cx0, y0, title="Evaluation spend control", sub="Playground evaluations are on by default and billed", theme="violet",
                  style="dotted", pad=26, title_size=26, sub_size=15, w=pw) as pc:
        sg = 22
        bw = (inner - 4 * sg) / 5
        labels = ["Playground evaluations off unless you need them", "Sample live traffic; cap max_hourly_runs (default 100)",
                  "Smaller judge model; pre-computed outputs; smaller datasets", "Schedule red teaming, do not run it continuously",
                  "Read the optimizer estimate before every run"]
        eb = [Box(bw, lab, h=158, theme="violet", size=15, color=INK).place(cv, pc.ix + i * (bw + sg), pc.iy + 14) for i, lab in enumerate(labels)]
        for a, c in zip(eb, eb[1:]):
            connect(cv, a, c, a_side="right", b_side="left", sw=3)
        for i, bx in enumerate(eb):
            numbered(cv, bx.x + 4, bx.y + 4, i + 1, theme="violet", d=30, size=17)
        ty = eb[0].bottom + 34
        t = Table([("Portal value", 150), ("Meaning", inner - 150)], [
            [("Minimum", "violet"), "Modeled cost of the required full-dataset evaluations for the baseline and the requested candidates"],
            [("Estimated", "violet"), "Expected modeled cost, including runs that finish before the full call budget"],
            [("Maximum", "violet"), "Conservative modeled upper bound - not an enforced spending limit"],
        ], theme="violet", size=14, head_size=15, pad_y=6, title="Agent optimizer pre-run estimate (prompt agents, portal)", title_size=20)
        t.place(cv, pc.ix, ty)
        oc = Card(inner, "Agent optimizer: cost vs quality", [
            "Limited preview. Candidates are ranked by a composite quality score (0.0 to 1.0); a gain under 0.03 is noise",
            "Its model-selection target compares model deployments to find the best quality-to-cost trade-off",
            "Optimized instructions are often longer: check the token increase against the score gain",
            "Cost layers: running your agent, scoring responses, generating improvements (the largest share in the docs' 2-candidate example)",
            "! Every run invokes your agent on each dataset row - external tool calls execute too; use test endpoints or mocks",
            "Hosted agents get post-run token usage, not the pre-run estimate, in the portal",
        ], theme="violet", icon="app-insights", title_size=18,
            src=[("Agent optimizer cost and token usage", learn("agents/concepts/agent-optimizer-costs")),
                 ("What is the agent optimizer?", learn("agents/concepts/agent-optimizer-overview"))])
        oc.place(cv, pc.ix, t.bottom + 30)
    return max(pa.bottom, pb.bottom, pc.bottom)


# ====================================================================== facts, anti-patterns, caveats
def _bottom(cv: Canvas, y: float) -> float:
    with cv.panel(0, y, title="Savings facts the docs actually state", sub="Percentages, allowances and caps only (" + ASOF + "); blue = Learn, cyan = Azure.com pricing page",
                  theme="green", style="dotted", pad=26, title_size=28, sub_size=16, w=W) as fp:
        learn_facts = [
            "Batch: 50% discount", "Flex (preview): 50% off tokens + cached-token discount",
            "Cache reads: discounted on Standard, up to 100% off on Provisioned", "Global Standard: lowest price",
            "PTU quota: no cost", "Hosted-agent idle timeout: 15 min default (2-240)", "Code Interpreter session: 1 h",
            "Continuous evaluation cap: 100 runs/hour by default", "AI Search free tier + free agentic-retrieval tokens",
        ]
        price_facts = [
            "Agent Pre-Purchase: 5% / 10% / 15% (20,000 / 100,000 / 500,000 ACU)", "File search: 1 GB free",
            "Content Safety: 5,000 text records + 5,000 images free per month", "Defender for AI Services trial: 30 days or 75 B tokens",
        ]
        items = [Chip(t, theme="blue", size=16) for t in learn_facts] + [Chip(t, theme="cyan", size=16) for t in price_facts]
        ChipFlow(items, W - 52, gap=12).place(cv, fp.ix, fp.iy)

    y1 = fp.bottom + 50
    with cv.panel(0, y1, title="Anti-patterns the docs warn about", sub="Each one is a documented warning, not a guess",
                  theme="red", style="dotted", pad=26, title_size=28, sub_size=16, w=W) as ap:
        aw = (W - 52 - 3 * 26) / 4
        cards = [
            Card(aw, "Commitments", [
                "! Scaling PTU up and down with hourly traffic (cost and capacity risk)",
                "! Buying a reservation before confirming deployable capacity",
            ], theme="red", icon="reservations", src=[("PTU billing", learn("openai/concepts/provisioned-throughput-billing"))]),
            Card(aw, "Meters that keep running", [
                "! Leaving fine-tuned or managed-compute deployments running",
                "! Leaving an APIM gateway after disabling projects - delete the instance",
                "! Oversized hosted-agent sandboxes",
            ], theme="red", icon="vm", src=[("Fine-tuning cost management", learn("fine-tuning/cost-management")),
                                             ("Hosted agents", learn("agents/concepts/hosted-agents"))]),
            Card(aw, "Requests and prompts", [
                "! Concurrent requests overshooting gateway limits",
                "! Flex without retry or fallback logic",
                "! One changed character in the first 1,024 tokens (cache miss)",
            ], theme="red", icon="api-connections", src=[("Flex processing", learn("openai/how-to/flex-processing")),
                                                          ("Prompt caching", learn("openai/how-to/prompt-caching"))]),
            Card(aw, "Evaluation and budgets", [
                "! Playground evaluations left on",
                "! Treating the optimizer's Maximum estimate as a limit",
                "! Expecting budgets to stop spend",
            ], theme="red", icon="alerts", src=[("Observability", learn("concepts/observability")),
                                                 ("Plan and manage costs", learn("concepts/manage-costs"))]),
        ]
        row(cv, ap.ix, ap.iy, cards, gap=26)

    y2 = ap.bottom + 50
    gap = 50
    cw = (W - 2 * gap) / 3
    # ---- column A: docs disagree
    ny = y2
    notes = [
        Note(cw, "The prerequisites say model versions 2025-12-01 or later, yet the page's own supported list includes gpt-4.1 2025-04-14 "
                 "and gpt-5.1 2025-11-13. The premium over Standard pricing is not stated on Learn. Check the page and the pricing page "
                 "before you plan (" + ASOF + ").", kind="warn", title="Docs disagree: Priority processing",
             src=[("Priority processing", learn("openai/concepts/priority-processing"))]),
        Note(cw, "The concept page says router usage is charged for input prompts at the pricing-page rate; the how-to page says the router's "
                 "cost is the sum of the costs incurred by the underlying models. Whether router tokens are billed on top of the underlying "
                 "models is not stated unambiguously - confirm on the pricing page and compare against your baseline.",
             kind="warn", title="Docs disagree: model router billing",
             src=[("Model router", learn("openai/concepts/model-router")), ("Use model router", learn("openai/how-to/model-router"))]),
        Note(cw, "Prompt-caching text says Provisioned deployments get up to 100% off cached input. The sizing page deducts cached tokens "
                 "fully only for models without normalized token accounting; GPT-6 Astra, GPT-6 Sol and GPT-6.1 Sol and newer count cached "
                 "input and cache writes at model-specific weights. Check your model before relying on a cache rate in PTU sizing.",
             kind="warn", title="Model-dependent: cached tokens on PTU",
             src=[("Estimate PTUs", learn("openai/how-to/provisioned-throughput-sizing"))]),
    ]
    for n in notes:
        n.place(cv, 0, ny)
        ny += n.h + 24
    col_a_bottom = ny - 24

    # ---- column B: not stated + preview board
    nb = Card(cw, "Not stated in the docs (" + ASOF + ")", [
        "Currency prices: none are quoted here - see the pricing pages and the 'Cost and billing' canvas",
        "The Priority-processing premium over Standard",
        "Which meter instant access uses",
        "Whether router tokens bill on top of the underlying models",
        "Hosted-agent per-vCPU and per-GiB rates, and whether persisted $HOME and /files storage is billed",
        "The PTU reservation discount % (varies by model family and term)",
        "max_tool_calls semantics (check the API reference)",
    ], theme="gray", dash="dashed", fill="none", icon="info-protection", title_size=20)
    nb.place(cv, cw + gap, y2)
    with cv.panel(cw + gap, nb.bottom + 24, title="Status board", sub=ASOF, theme="orange", style="dotted", pad=22, title_size=22, sub_size=15, w=cw) as sbd:
        prev = ["Flex processing", "Instant access (West US 3 only)", "Managed compute", "AI gateway token limits (Manage > AI Gateway)",
                "MCP tool governance via the AI gateway", "Project-level cost attribution (project tag)", "Router session affinity",
                "Memory", "Monitor dashboard evaluations", "Serverless AI Search"]
        cs = [Chip(t, theme="orange", size=15) for t in prev] + [Chip("Agent optimizer (limited preview)", theme="orange", size=15, dash="dashed")]
        cs += [Chip(t, theme="green", size=15) for t in ("GA: Manage > Quota", "GA: Policy approved models + eligibility", "GA: tracing for prompt and hosted agents")]
        ChipFlow(cs, cw - 44, gap=10).place(cv, sbd.ix, sbd.iy)

    # ---- column C: general FinOps practice
    with cv.panel(2 * (cw + gap), y2, title="General FinOps practice", sub="Not Foundry-specific guidance - useful habits that the docs support only in part",
                  theme="gray", style="dashed", pad=22, title_size=24, sub_size=15, w=cw) as fo:
        inner_w = cw - 44
        f1 = Card(inner_w, "Showback, then allocation, then chargeback", [
            "FinOps maturity order: start with showback, then cost allocation, then chargeback",
            "Foundry gives the inputs: project, deployment and user tags, and cost exports (Learn)",
        ], theme="gray", dash="dashed", fill="none", icon="tag", title_size=18,
            src=[("Plan and manage costs", learn("concepts/manage-costs")),
                 ("FinOps: invoicing and chargeback", learn("cloud-computing/finops/framework/manage/invoicing-chargeback", base=""))])
        f2 = Card(inner_w, "Monthly review checklist", [
            "Reservation utilization, idle deployments, orphaned APIM instances",
            "Estimate, test, then reconcile by Resource and Meter; adjust budgets after a full billing cycle (Learn)",
        ], theme="gray", dash="dashed", fill="none", icon="scheduler", title_size=18)
        f3 = Card(inner_w, "Tag everything consistently", [
            "Tag filters return incomplete results when tags are missing on participating resources (Learn troubleshooting)",
        ], theme="gray", dash="dashed", fill="none", icon="tag", title_size=18)
        col(cv, fo.ix, fo.iy, [f1, f2, f3], gap=18)
    return max(col_a_bottom, sbd.bottom, fo.bottom)


def _sources(cv: Canvas, y: float) -> None:
    sources(cv, 0, y, [
        ("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
        ("Prompt caching", learn("openai/how-to/prompt-caching")),
        ("Flex processing (preview)", learn("openai/how-to/flex-processing")),
        ("Priority processing", learn("openai/concepts/priority-processing")),
        ("Model router for Foundry", learn("openai/concepts/model-router")),
        ("Provisioned throughput billing and reservations", learn("openai/concepts/provisioned-throughput-billing")),
        ("Estimate PTUs (sizing formulas)", learn("openai/how-to/provisioned-throughput-sizing")),
        ("Spillover traffic management", learn("openai/how-to/spillover-traffic-management")),
        ("Plan and manage costs for Microsoft Foundry", learn("concepts/manage-costs")),
        ("Manage and increase quotas", learn("how-to/quota")),
        ("Enforce token limits for models (AI gateway)", learn("control-plane/how-to-enforce-limits-models")),
        ("Hosted agents", learn("agents/concepts/hosted-agents")),
        ("Agent optimizer cost and token usage", learn("agents/concepts/agent-optimizer-costs")),
        ("Observability in generative AI", learn("concepts/observability")),
        ("Fine-tuning cost management", learn("fine-tuning/cost-management")),
        ("Save costs with Foundry Provisioned Throughput reservations", learn("azure/cost-management-billing/reservations/microsoft-foundry", base="")),
        ("Microsoft Agent prepurchase plan", learn("azure/cost-management-billing/reservations/agent-pre-purchase/", base="")),
        ("Microsoft Foundry pricing (Azure.com, pricing-page facts)", "https://azure.microsoft.com/en-us/pricing/details/microsoft-foundry/"),
    ], w=W, cols=3, title="Sources and further reading (Microsoft Learn and the Azure.com pricing page)")


def build(cv: Canvas) -> None:
    y = _top(cv)
    y = _strip(cv, y + 50)
    y = _decision(cv, y + 60)
    y = _guardrails(cv, y + 70)
    y = _tables(cv, y + 70)
    y = _loops(cv, y + 70)
    y = _bottom(cv, y + 70)
    _sources(cv, y + 70)
