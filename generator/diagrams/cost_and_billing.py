"""Microsoft Foundry Cost Structure - FLAGSHIP: every billing meter by area, billing options, metering, scopes, views and limits.

Layout idea (modelled on Dan Friedman's 'Microsoft Fabric Cost Structure' explainer): a tree.  Root = what you are billed
for -> six meter families (A-F) -> one card per meter.  Below the tree: how you pay, how usage becomes a bill, where cost
lands and how to see it, and a red 'limits' box with green dotted mitigations.  No currency amounts are drawn (none are
documented); only stated percentages, free allowances and caps appear.
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="cost-and-billing", title="Microsoft Foundry Cost Structure", section="2", group="Control plane and cost", order=53,
    description="Every Foundry billing meter by area - models, fine-tuning, agents and tools, safety, observability, data - plus billing options, metering, cost scopes, views and the limits that throttle you.",
    tags=["cost", "billing", "finops", "ptu", "meters", "budgets"],
)

# ---------------------------------------------------------------------------------------------- grid
P = 472            # panel / column width
CARD = 440         # card width inside a family panel (panel pad 16)
GUT = 40
STEP = P + GUT
W = 7 * P + 6 * GUT          # 3544
INK_BLUE = "#1864ab"


def X(i: int) -> float:
    return i * STEP


def SPAN(n: int) -> float:
    return n * P + (n - 1) * GUT


# ---------------------------------------------------------------------------------------------- sources
PR = "https://azure.microsoft.com/en-us/pricing/details/"
S = dict(
    cost=("Plan and manage costs for Foundry", learn("concepts/manage-costs")),
    deploy=("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
    reasoning=("Reasoning models (tokens)", learn("openai/how-to/reasoning")),
    cache=("Prompt caching", learn("openai/how-to/prompt-caching")),
    flex=("Flex processing (preview)", learn("openai/how-to/flex-processing")),
    priority=("Priority processing", learn("openai/concepts/priority-processing")),
    router=("Model router", learn("openai/concepts/model-router")),
    instant=("Instant access to models (preview)", learn("concepts/instant-models")),
    ptu=("Provisioned throughput", learn("openai/concepts/provisioned-throughput")),
    ptubill=("Provisioned throughput billing", learn("openai/concepts/provisioned-throughput-billing")),
    res=("Save costs with PTU reservations", learn("azure/cost-management-billing/reservations/microsoft-foundry", base="")),
    prepay=("Microsoft Agent prepurchase plan", learn("azure/cost-management-billing/reservations/agent-pre-purchase/", base="")),
    managed=("Managed compute (preview)", learn("concepts/managed-compute-overview")),
    claude=("Claude Consumption Units billing", learn("foundry-models/concepts/claude-models-billing")),
    partners=("Models from partners and community", learn("foundry-models/concepts/models-from-partners")),
    ft=("Fine-tuning cost management", learn("fine-tuning/cost-management")),
    plan=("Plan your Foundry rollout", learn("concepts/planning")),
    hosted=("Hosted agents", learn("agents/concepts/hosted-agents")),
    afaq=("Agent Service FAQ", learn("agents/faq")),
    alimits=("Agent Service limits and quotas", learn("agents/concepts/limits-quotas-regions")),
    voice=("Pricing for voice-based agents", learn("agents/concepts/voice-agent-pricing")),
    optcost=("Agent optimizer costs", learn("agents/concepts/agent-optimizer-costs")),
    obs=("Observability in Foundry", learn("concepts/observability")),
    mon=("Monitor agents dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard")),
    mvnet=("Managed virtual network", learn("how-to/managed-virtual-network")),
    gw=("Enable an AI gateway", learn("configuration/enable-ai-api-management-gateway-portal")),
    glimits=("Enforce token limits for models", learn("control-plane/how-to-enforce-limits-models")),
    quota=("Manage quota", learn("how-to/quota")),
    aquota=("Azure OpenAI quota and 429 errors", learn("openai/how-to/quota")),
    consol=("Consolidated view for Foundry Tools", learn("concepts/foundry-consolidated-view")),
    std=("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
    ga=("Feature status at GA", learn("concepts/general-availability")),
    trace=("Set up tracing", learn("observability/how-to/trace-agent-setup")),
    a365=("Overview of Microsoft Agent 365", learn("microsoft-agent-365/overview", base="")),
    policy=("Model deployment policy", learn("how-to/model-deployment-policy")),
    search_cost=("Plan and manage costs of Azure AI Search", learn("azure/search/search-sku-manage-costs", base="")),
    search_tier=("Choose an Azure AI Search tier", learn("azure/search/search-sku-tier", base="")),
    agentic=("Agentic retrieval billing", learn("azure/search/agentic-retrieval-overview", base="")),
    p_found=("Azure pricing: Microsoft Foundry (FAQ)", PR + "microsoft-foundry/"),
    p_agent=("Azure pricing: Foundry Agent Service", PR + "foundry-agent-service/"),
    p_obs=("Azure pricing: Observability in Foundry Control Plane", PR + "foundryobservability/"),
    p_cs=("Azure pricing: Content Safety in Foundry Control Plane", PR + "content-safety/"),
    p_def=("Azure pricing: Defender for Cloud (AI services)", PR + "defender-for-cloud/"),
    p_tools=("Azure pricing: Foundry Tools", PR + "foundry-tools/"),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


def mcard(title, body, *, sub=None, theme="blue", badge=None, icon=None, keys=(), fill="hatch", dash="solid", w=CARD, **kw):
    """One meter card: consistent type scale for the dense family columns."""
    return Card(w, title, body, theme=theme, subtitle=sub, badge=badge, icon=icon, src=src(*keys), fill=fill, dash=dash,
                title_size=19, body_size=15, sub_size=13, pad=14, gap=4, icon_size=30, **kw)


class Block(Rect2):
    """Placed rectangle (for connectors and overlap checks of hand-drawn shapes)."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


def dotted(cv, pts, *, color=INK, sw=2, head=None):
    """Dotted connector; a head is drawn as a short solid tip so it stays crisp."""
    if head is None:
        return arrow(cv, pts, dash="dotted", color=color, sw=sw, start_head=None, end_head=None)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    d = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1.0)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    tip = 18
    arrow(cv, list(pts[:-1]) + [(x2 - ux * tip, y2 - uy * tip)], dash="dotted", color=color, sw=sw, start_head=None,
          end_head=None)
    return arrow(cv, [(x2 - ux * tip, y2 - uy * tip), (x2, y2)], dash="solid", color=color, sw=sw, end_head="arrow")


class Receipt(Rect2):
    """Receipt-style ledger: label ........ unit, with an optional total line. Draws no prices - only units or symbols."""

    def __init__(self, w, title, rows, total=None, note=None, *, theme="blue", size=15, pad=14):
        self.th = THEMES[theme]
        self.w, self.title, self.rows, self.total, self.note, self.size, self.pad = w, title, rows, total, note, size, pad
        inner = (w - 2 * pad) * 0.965
        self.t_lines = wrap_text(title, inner, 18)
        self.n_lines = wrap_text(note, inner, 14) if note else []
        self.lh = text_size("Ag", size)[1]
        self.h = (pad + len(self.t_lines) * text_size("Ag", 18)[1] + 8 + len(rows) * (self.lh + 7)
                  + ((self.lh + 16) if total else 0) + ((len(self.n_lines) * text_size("Ag", 14)[1] + 10) if note else 0) + pad)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed", round_=False)
            cy = y + pad
            cv.text(x + pad, cy, "\n".join(self.t_lines), size=18, color=th.deep)
            cy += len(self.t_lines) * text_size("Ag", 18)[1] + 8
            right = x + self.w - pad
            for label, value in self.rows:
                lw = text_size(label, self.size)[0]
                vw = text_size(value, self.size)[0]
                cv.text(x + pad, cy, label, size=self.size)
                cv.text(right - vw, cy, value, size=self.size, color=th.deep)
                ly = cy + self.lh * 0.78
                cv.line((x + pad + lw + 8, ly), (right - vw - 8, ly), stroke="#868e96", sw=1, dash="dotted")
                cy += self.lh + 7
            if self.total:
                label, value = self.total
                cv.line((x + pad, cy + 2), (right, cy + 2), stroke=INK, sw=2)
                cv.text(x + pad, cy + 8, label, size=self.size + 1, color=th.deep)
                vw = text_size(value, self.size + 1)[0]
                cv.text(right - vw, cy + 8, value, size=self.size + 1, color=th.deep)
                cy += self.lh + 16
            if self.n_lines:
                cv.text(x + pad, cy + 2, "\n".join(self.n_lines), size=14, color=MUTED)
        cv.register("receipt", x, y, self.w, H)
        return self


class VFlow(Rect2):
    """Small vertical flow of boxes joined by arrows: steps = (label, sub, theme, icon)."""

    def __init__(self, w, title, steps, *, gap=30, box_size=17):
        self.w, self.title, self.gap = w, title, gap
        self.t_lines = wrap_text(title, w * 0.965, 18) if title else []
        self.boxes = [Box(w, lab, theme=th, sub=sub, icon=icon, icon_pos="left", icon_size=30, size=box_size, sub_size=13,
                          fill="hatch", pad=9, min_h=60) for lab, sub, th, icon in steps]
        self.t_h = (len(self.t_lines) * text_size("Ag", 18)[1] + 10) if title else 0
        self.h = self.t_h + sum(b.h for b in self.boxes) + gap * (len(self.boxes) - 1)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        if self.t_lines:
            cv.text(x, y, "\n".join(self.t_lines), size=18, color="#343a40")
        cy = y + self.t_h
        for b in self.boxes:
            b.place(cv, x, cy)
            cy += b.h + self.gap
        for a, b in zip(self.boxes, self.boxes[1:]):
            connect(cv, a, b, a_side="bottom", b_side="top", end_head="arrow", sw=2)
        return self


# ============================================================================================== 0. title + key
def title_and_key(cv) -> float:
    _, bottom = title_block(
        cv, 0, 0, "Microsoft Foundry Cost Structure",
        "You pay for what Foundry calls, not for Foundry itself: every billing meter by area, what bills while idle, where it lands, where to see it  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    with cv.panel(0, y, theme="gray", style="dotted", pad=16, w=W) as k:
        t = cv.text(k.ix, k.iy - 2, "Colour = area", size=16, color="#343a40")
        legend(cv, k.ix + 150, k.iy - 2, [
            ("Models", "blue"), ("Agents", "green"), ("Tools and Foundry Tools", "orange"), ("Knowledge and memory", "teal"),
            ("Observability and evaluation", "violet"), ("Guardrails", "pink"), ("Security", "red"), ("Networking", "indigo"),
            ("Governance and control plane", "grape"), ("Data", "cyan"), ("Cost mechanics", "yellow"),
            ("Free or not billed", "lime")], size=15, gap=24)
        y2 = k.iy + 34
        cv.text(k.ix, y2, "Markers", size=16, color="#343a40")
        cx = k.ix + 150
        for kind, label in (("idle", "bills while idle"), ("ok", "nothing billed while idle")):
            col_ = "#e03131" if kind == "idle" else "#2f9e44"
            cv.ellipse(cx, y2 + 4, 11, 11, stroke=col_, sw=2, rough=0)
            tt = cv.text(cx + 20, y2, label, size=15)
            cx += 20 + tt.w + 36
        draw_badge(cv, cx, y2 - 1, "preview")
        tt = cv.text(cx + 80, y2, "preview feature (as of 2026-11-03)", size=15)
        cx += 80 + tt.w + 36
        cv.rect(cx, y2 + 1, 28, 18, stroke=THEMES["blue"].stroke, fill=THEMES["blue"].fill, style="cross-hatch", sw=2)
        tt = cv.text(cx + 38, y2, "billed through Azure Marketplace", size=15)
        cx += 38 + tt.w + 36
        cv.rect(cx, y2 + 1, 28, 18, stroke="#495057", sw=2, dash="dashed")
        tt = cv.text(cx + 38, y2, "our reading: not stated in the docs", size=15)
        cx += 38 + tt.w + 36
        cv.rect(cx, y2 + 1, 28, 18, stroke=THEMES["green"].stroke, fill=THEMES["green"].fill, style="hachure", sw=2, dash="dotted")
        cv.text(cx + 38, y2, "mitigation", size=15)
    return k.bottom


# ============================================================================================== 1. root + tree heads
def tree_top(cv, y: float):
    root = Card(
        SPAN(3), "What you are billed for", [
            "= The Foundry platform is free to use and explore. Individual features you access and consume are billed at their normal rates.",
            "= Each service and product available in Foundry has its own billing model and price - so the cost structure is a set of meters, in six families.",
        ], theme="yellow", align="center", fill="hatch", title_size=32, body_size=18, icon="cost-management", icon_size=46,
        pad=22, src=src("p_found"))
    root.place(cv, X(2), y)

    n_left = Note(940, "Foundry is composed of several optional Azure services, so the Azure pricing calculator has no dedicated Foundry "
                  "page. Add each service you use (for example Azure Speech in Foundry or Azure AI Search) and estimate them one by one.",
                  kind="info", title="No Foundry page in the pricing calculator", src=src("cost"))
    n_left.place(cv, 0, y + (root.h - n_left.h) / 2)
    n_right = Note(940, "Rates vary by model, region, agreement and currency, so no prices are drawn. Only documented percentages, free "
                   "allowances, caps and tiers appear (as of 2026-11-03). Use the pricing pages and the calculator for rates.",
                   kind="warn", title="No currency prices on this canvas", src=src("p_found"))
    n_right.place(cv, W - 940, y + (root.h - n_right.h) / 2)
    dotted(cv, [(n_left.right + 6, root.cy), (root.x - 8, root.cy)], color="#868e96", sw=2)
    dotted(cv, [(n_right.x - 6, root.cy), (root.right + 8, root.cy)], color="#868e96", sw=2)
    return root


FAMILIES = [
    # (first column, columns spanned, theme, icon, title, subtitle, body)
    (0, 2, "blue", "openai", "A  Model deployments",
     "input / cached / output tokens  -  PTU-hours  -  GPU-hours  -  CCU",
     ["! Bills while idle: provisioned (PTU) and managed compute",
      "+ Nothing while idle: Standard family, Batch, Flex, Priority, Developer, Claude, partner models"]),
    (2, 1, "blue", "ml", "B  Fine-tuning", "training tokens or hours  -  hosting hours",
     ["! Hosting bills even when the model is unused"]),
    (3, 1, "green", "agent", "C  Agents and tools", "model tokens  -  vCPU and GiB hours  -  sessions  -  GB-days  -  1,000 transactions",
     ["+ Prompt agents and workflows: no additional charge"]),
    (4, 1, "pink", "content-safety", "D  Safety, evaluation, security", "records  -  evaluation tokens  -  1K tokens a month  -  licences",
     ["+ Free tier: 5,000 text records and 5,000 images a month"]),
    (5, 1, "violet", "app-insights", "E  Observability and gateway", "log ingestion  -  APIM instance  -  managed firewall",
     ["+ Monitoring dashboards: no charge"]),
    (6, 1, "teal", "ai-search", "F  Knowledge, data, Foundry Tools", "Search units  -  RU/s  -  GB  -  per-service meters",
     ["+ Quota is a policy limit with no cost"]),
]


def heads(cv, y: float, root) -> list:
    cards = []
    for c0, span, theme, icon, title, sub, body in FAMILIES:
        cards.append(Card(SPAN(span), title, body, theme=theme, subtitle=sub, icon=icon, fill="solid", title_size=24, body_size=15,
                          sub_size=14, pad=16, gap=4, icon_size=40))
    hmax = max(c.h for c in cards)
    bus_y = y - 42
    xs = []
    for (c0, span, *_), c in zip(FAMILIES, cards):
        c.place(cv, X(c0), y, h=hmax)
        xs.append(c.cx)
    dotted(cv, [(root.cx, root.bottom + 4), (root.cx, bus_y)], sw=3)
    dotted(cv, [(min(xs), bus_y), (max(xs), bus_y)], sw=3)
    for (c0, span, theme, *_), c in zip(FAMILIES, cards):
        numbered(cv, c.x + 6, c.y + 6, "ABCDEF"[[f[0] for f in FAMILIES].index(c0)], theme=theme, d=34, size=19)
        if abs(c.cx - root.cx) > 1:
            dotted(cv, [(c.cx, bus_y), (c.cx, c.y - 6)], sw=3, head="arrow")
    dotted(cv, [(root.cx, bus_y), (root.cx, cards[2].y - 6)], sw=3, head="arrow")
    return cards


# ============================================================================================== 2. meter families
def family_panel(cv, x, y, w, cards, theme, h, label=None):
    with cv.panel(x, y, theme=theme, style="dotted", fill="soft", pad=16, w=w, min_h=h) as p:
        cy = p.iy
        if label:
            t = cv.text(p.ix, cy - 4, label, size=20, color=THEMES[theme].deep)
            cy += t.h + 6
        col(cv, p.ix, cy, cards, gap=18)
    return p


def need_h(cards, label=False) -> float:
    return 32 + sum(c.h for c in cards) + 18 * (len(cards) - 1) + (34 if label else 0)


def families(cv, y: float, head_cards) -> float:
    # ---------------------------------------------------------------- A1: pay per token
    a1 = [
        mcard("Standard family tokens", [
            "Unit: input tokens, cached input tokens (discounted) and output tokens",
            "Reasoning tokens bill as output tokens; cached tokens are part of input",
            "Global Standard: lowest price, broadest regions, first for new models; Learn gives no Data Zone or regional ratios",
            "+ Nothing billed while idle",
        ], sub="GlobalStandard  -  DataZoneStandard  -  Standard", icon="openai", keys=("deploy", "reasoning")),
        mcard("Prompt-cache meters", [
            "Cache read: discounted input price (Standard) or up to a 100% discount (Provisioned)",
            "Cache write: no extra charge before GPT-5.6; GPT-5.6 and later can add a charge on top of discounted reads",
            "Same price for in-memory and extended retention; usage shows cached_tokens and cache_write_tokens",
        ], sub="identical prompt prefix of 1,024+ tokens", icon="redis", keys=("cache",)),
        mcard("Batch", [
            "Tokens at 50% less than Global Standard; 24-hour target, no real-time SLA",
            "Separate enqueued-token quota, so online traffic is not disrupted",
            "+ Nothing billed while idle",
        ], sub="GlobalBatch  -  DataZoneBatch", icon="batch", keys=("deploy",)),
        mcard("Flex", [
            "Tokens at 50% of Standard rates on dedicated Flex meters; cached-token discount still applies",
            "No latency or service SLA; supported models only; shares quota with the Global Standard deployment",
            "429 when Flex capacity is unavailable - those requests are not billed",
            "+ Nothing billed while idle",
        ], sub="service_tier = flex on a Global Standard deployment", badge="preview", icon="scheduler", keys=("flex",)),
        mcard("Priority", [
            "Tokens at the Priority rate, pay-as-you-go; same quota as Standard; Global Standard or Data Zone Standard (US)",
            "Re-routed to Standard and billed at Standard rates on a ramp-rate breach (+50% TPM in under 15 min), at peak, or for >128k-token prompts on some models",
            "+ Nothing billed while idle",
        ], sub="service_tier = priority (deployment or request)", icon="metrics", keys=("priority",)),
        mcard("Developer tier", [
            "Fine-tuned model evaluation only; tokens at Global Standard rates",
            "No hosting fee: the deployment is deleted automatically after 24 hours",
            "No SLA and no data-residency guarantee",
        ], sub="DeveloperTier", icon="code", keys=("deploy", "ft")),
        mcard("Model router", [
            "Learn: charged for input prompts at the rate on the pricing page (a router input-token meter)",
            "Mode (Balanced default, Cost, Quality), model subset and Auto-update change which models serve you, and the spend",
            "Global and Data Zone Standard only",
        ], sub="one deployment, per-request model choice", icon="branch", keys=("router",)),
        mcard("Instant access", [
            "Call by model name, no deployment; draws from a per-model global quota pool",
            "The Learn page does not name the billing meter: check the pricing page",
        ], sub="West US 3 only during preview", badge="preview", icon="preview-features", keys=("instant",)),
    ]
    # ---------------------------------------------------------------- A2: capacity + marketplace
    a2 = [
        mcard("Provisioned throughput (PTU)", [
            "Unit: $/PTU/hour x deployed PTUs (300 PTUs = rate x 300); 15 minutes = 1/4 hour; resizing bills immediately",
            "! Bills while idle: can't be paused; billing stops only when the deployment is deleted",
            "PTU quota has no cost, but quota is not capacity; minimum PTUs apply per model",
            "Model-independent pool per region and deployment type",
        ], sub="GlobalProvisionedManaged  -  DataZoneProvisionedManaged  -  ProvisionedManaged", icon="cubes", keys=("ptubill", "ptu")),
        mcard("PTU Reservation", [
            "Discounted effective $/PTU/hour for a 1-month or 1-year term; the % varies by model family and term (none in Learn)",
            "Matches deployment type + region (Data Zone, Regional) + scope - not the model; PTUs above the reservation bill hourly",
            "! Deleting a deployment does not cancel the reservation; unused reserved PTUs are lost, not carried over",
            "Create deployments first, then buy; a reservation does not guarantee capacity",
        ], sub="Azure Reservations", icon="reservations", keys=("ptubill", "res")),
        mcard("Managed compute", [
            "Unit: GPUs per instance x instances x hours x $/GPU-hour, by accelerator family",
            "! Bills while the deployment runs, with or without requests; delete it to stop",
            "Learn lists A100 80GB, H100 80GB and MI300X 192GB; quota per family and region, separate from VM quota; Global only",
            "Reserved capacity and commitment discounts are still evolving in preview",
        ], sub="GlobalManagedCompute", badge="preview", icon="vm", keys=("managed",)),
        mcard("Claude (CCU)", [
            "Unit: Claude Consumption Unit - tokens x Anthropic per-model rates, after discounts, divided by a fixed CCU price",
            "Metered hourly, invoiced monthly in arrears; MACC-eligible; no prepaid CCU",
            "Lands on the Foundry resource; its tags flow to cost records; no project-level attribution",
            "Estimated-cost chart only for CCU-based deployments; older ones keep per-model billing",
            "+ Nothing billed while idle",
        ], sub="billed through Azure Marketplace", icon="claude", fill="cross", keys=("claude",)),
        mcard("Partner and community models", [
            "Provider-set price through Azure Marketplace (Cohere, Mistral, Meta and others)",
            "Meters named model-name-GUID show under the resource group, as 'Global' resources - not under the Foundry resource",
            "! Azure Prepayment can't pay for them; no project-level attribution",
            "Student, Visual Studio Enterprise and free-credit subscriptions can't buy the SaaS offer",
            "+ Nothing billed while idle",
        ], sub="serverless, billed through Azure Marketplace", icon="marketplace", fill="cross", keys=("partners", "cost")),
        mcard("Free or not billed", [
            "+ PTU quota and quota requests: no cost",
            "+ Flex requests rejected for lack of capacity: not billed",
            "+ Exploring the Foundry platform: free (an Azure subscription is needed to build agents)",
        ], theme="lime", icon="quotas", keys=("ptu", "flex", "p_found")),
    ]
    # ---------------------------------------------------------------- B: fine-tuning
    b = [
        mcard("Training: SFT and DPO", [
            "Unit: training tokens x epochs x price per training token (not elapsed time)",
            "Regional Standard, Global Standard and Developer training rates differ; Global and Developer give no residency guarantee",
            "Developer training is preemptible; paused jobs resume free",
        ], sub="Managed Training", icon="ml", keys=("ft",)),
        mcard("Training: RFT", [
            "Unit: hours (2 decimals) x hourly rate, plus grader tokens billed separately",
            "A per-job spending limit pauses the job and creates a checkpoint; resuming removes the cost limit",
            "Cancel = pay for work done; work lost to a service error is not billed",
        ], sub="reinforcement fine-tuning", icon="gear", keys=("ft",)),
        mcard("Programmed Training", [
            "Four token buckets: prefill, cached prefill, sampling and training",
            "Cumulative across the whole run - not the dataset size",
        ], sub="token-based, not the hourly RFT formula", badge="preview", icon="code", keys=("ft",)),
        mcard("Hosting a fine-tuned model", [
            "Standard and Global Standard: hourly hosting fee per deployment plus base-model token rates",
            "! The hosting fee runs even when the model is unused (30 days = 720 x the hourly rate)",
            "Regional Provisioned: PTU-hours, no per-token charge; Developer: no hosting fee, 24 hours",
        ], sub="inference + hosting", icon="vm", keys=("ft", "cost")),
        mcard("Other ways to host", [
            "Fireworks on Foundry: token offers for catalog models, PTU-hours for imported custom models",
            "Managed compute (preview): GPU-hours; delete to release accelerators",
        ], sub="same training bill, different serving meter", icon="cubes", keys=("ft",)),
        mcard("Never billed", [
            "+ Time in the queue",
            "+ Failed jobs and jobs cancelled before training begins",
            "+ Data safety checks",
        ], theme="lime", icon="quotas", keys=("ft",)),
        Note(CARD, "Fine-tuning needs Foundry Owner because jobs consume compute and storage; training is not project-isolated, so use "
             "separate Foundry resources for independent teams.", kind="warn", title="Role and isolation", src=src("plan")),
    ]
    # ---------------------------------------------------------------- C: agents and tools
    c = [
        mcard("Agent Service: prompt agents and workflows", [
            "+ No additional charge for creating or running Foundry-native agents with prompts and workflows",
            "You pay model tokens for each agent's base model, plus the tools and knowledge it uses",
            "Workflows are in preview and retire on Dec 1, 2026 (as of 2026-11-03)",
        ], theme="lime", icon="agent", keys=("p_agent", "afaq")),
        mcard("Hosted agents", [
            "Billed on underlying container compute per hour: vCPU-hours + memory GiB-hours across all active sessions",
            "Sandboxes: 0.5 vCPU / 1 GiB, 1 / 2 or 2 / 4 - oversizing multiplies cost by concurrency",
            "Idle timeout 2-240 min (default 15) deprovisions compute; a session is deleted after 30 days idle",
            "Concurrent sessions per subscription and region: 2,000 in seven named regions, else 1,000",
            "! Persisted-session storage billing is not stated in Learn",
        ], sub="vCPU-hours + GiB-hours", icon="container-apps", keys=("hosted", "alimits", "p_agent")),
        mcard("File search", [
            "Billed per GB of vector storage per day, 1 GB free",
            "Charges come on top of the model tokens",
        ], sub="vector storage", theme="orange", icon="files", keys=("afaq", "p_agent")),
        mcard("Code Interpreter", [
            "Billed per session; each concurrent conversation starts its own session",
            "A session is active for one hour by default - requests in the same hour pay once",
            "Charges come on top of the model tokens",
        ], sub="per session", theme="orange", icon="code", keys=("afaq", "p_agent")),
        mcard("Web Search and Custom Search", [
            "Billed per 1,000 transactions; Grounding with Bing Search is priced separately",
            "Search data leaves the Azure compliance boundary",
        ], sub="per 1,000 transactions", theme="orange", icon="bing", keys=("p_agent",)),
        mcard("Voice agents", [
            "Audio tokens for caller and agent, session length, tool calls, avatar video and stored recordings (store = true)",
            "Model hosting: managed (billed through the voice agent) or self_deployed (your deployment's meter)",
            "Trace cost attributes are estimates, not invoice records",
        ], sub="Voice Live", badge="preview", theme="green", icon="speech", keys=("voice",)),
        mcard("Toolbox, MCP and other tools", [
            "You might incur costs: Logic Apps connectors, Fabric data agent, SharePoint, Foundry IQ, Speech, Language and Translator bill on their own meters",
            "Server-side tools such as toolboxes and MCP servers bill through their own resources",
        ], sub="not billed by Agent Service", theme="orange", icon="toolbox", keys=("p_agent", "voice")),
    ]
    # ---------------------------------------------------------------- D: safety, evaluation, security
    d = [
        mcard("Control Plane: no separate meter", [
            "Pricing is based on observability, guardrails and Microsoft Security usage: AI evaluations per input / output token; monitoring and tracing as Azure logs; guardrails per text or image record",
            "Indirect costs: the APIM gateway, App Insights, Content Safety records, Defender tokens, Purview and Agent 365",
            "The 'Foundry Control Plane' pricing link opens the Content Safety page",
        ], theme="grape", icon="management-group", keys=("p_obs", "p_found")),
        mcard("Guardrails (Content Safety)", [
            "Billed per text record (1,000 characters = 1 record) and per image; Prompt Shields and groundedness listed",
            "+ Free tier: 5,000 text records and 5,000 images a month; it stops at the limit, no overage",
        ], sub="per record", theme="pink", icon="content-safety", keys=("p_cs",)),
        mcard("AI evaluations meter", [
            "Input and output tokens per million - only for safety evaluations, red teaming and agent-playground evaluations",
            "! Playground evaluations are on by default in every project and billed: unselect all evaluators to turn off",
        ], sub="safety  -  red teaming  -  playground", theme="violet", icon="metrics", keys=("p_obs", "obs")),
        mcard("Quality and continuous evaluations", [
            "Tokens on your own judge-model deployment, with no surcharge - and they use that deployment's quota",
            "Continuous runs: max_hourly_runs default 100 an hour; Random or Intelligent sampling caps volume",
        ], sub="your judge model", theme="violet", icon="metrics", keys=("p_obs", "mon")),
        mcard("Agent optimizer", [
            "Modelled in three layers: agent runs (2,000 prompt / 400 completion tokens a call), judge (3,000 / 120), reflection (6,000 / 2,000)",
            "Review shows Minimum, Estimated and Maximum - the Maximum is not a spending limit; excludes external tools",
        ], sub="prompt agents show a pre-run estimate", badge="Limited preview", theme="violet", icon="gear", keys=("optcost", "ga")),
        mcard("Defender for AI services", [
            "Billed per 1K tokens a month; the trial is capped at 30 days or 75 billion tokens, whichever comes first",
            "Threat protection for jailbreak and prompt attacks",
        ], sub="Microsoft Defender for Cloud plan", theme="red", icon="defender", keys=("p_def",)),
        mcard("Purview and Agent 365", [
            "Purview: pay-as-you-go meters or an Agent 365 subscription; without either you get Audit only",
            "Agent 365: per-user licence, GA for Commercial since May 1, 2026 (as of 2026-11-03)",
        ], sub="data security and governance for AI", theme="red", icon="info-protection", keys=("ga",)),
    ]
    # ---------------------------------------------------------------- E: observability + gateway
    e = [
        mcard("Monitoring", [
            "+ No charge for the Foundry monitoring dashboards",
            "Data lives in your Application Insights: retention and billing follow its configuration",
        ], sub="agent dashboard", badge="preview", theme="lime", icon="dashboard", keys=("mon", "p_obs")),
        mcard("Tracing", [
            "Application Insights / Log Analytics ingestion and retention (Azure Monitor logs pricing); Foundry adds no charge",
            "Sampling and retention follow your App Insights setup; the portal shows the last 90 days",
        ], sub="GA for prompt and hosted agents", theme="violet", icon="app-insights", keys=("p_obs", "obs")),
        mcard("Diagnostic settings", [
            "Log Analytics ingestion, Storage or Event Hubs - each billed as its own Azure service",
            "Logs can arrive up to two hours late",
        ], sub="resource logs and metrics", theme="violet", icon="diagnostics", keys=("cost",)),
        mcard("AI gateway", [
            "The API Management instance: Basic v2 by default, Standard v2 or Premium v2 optional",
            "! Billed until the APIM resource is deleted - disabling a project does not delete it",
            "Learn says the gateway includes a free API Management tier, without eligibility details",
        ], sub="Manage > AI Gateway", badge="preview", theme="grape", icon="apim", keys=("gw", "ga")),
        mcard("Managed virtual network", [
            "The feature itself is free; you pay for Private Link and, with FQDN outbound rules, a managed Azure Firewall",
            "One firewall per Foundry account (Standard by default, Basic optional); you can't bring your own",
        ], sub="isolation mode: allow only approved outbound", theme="indigo", icon="firewall", keys=("mvnet",)),
        mcard("Peered VNets for agents", [
            "Data transfer charges apply - Learn says it is costly and not recommended",
            "Customer-VNet private endpoints bill as ordinary Azure networking resources",
        ], sub="agents with a customer VNet", theme="indigo", icon="vnet", keys=("afaq",)),
        mcard("Azure Policy and RBAC", [
            "+ No meter is mentioned for policy, RBAC or role assignments",
        ], theme="lime", icon="policy", keys=("policy",)),
    ]
    # ---------------------------------------------------------------- F: knowledge, data, tools
    f = [
        mcard("Foundry IQ (knowledge bases)", [
            "Azure AI Search bills retrieval tokens (subquery execution + semantic ranking); the free plan has a monthly allowance, standard is pay-as-you-go after it",
            "Azure OpenAI bills the query-planning and answer-synthesis tokens; the cost depends on reasoning effort",
        ], sub="agentic retrieval: two meters", theme="teal", icon="iq", keys=("agentic", "search_cost")),
        mcard("Azure AI Search service", [
            "Dedicated: hourly per Search Unit (replicas x partitions) by tier - Free, Basic, S1-S3, L1-L2",
            "Serverless (preview): Compute Units per hour + indexed GB a month; billing began Sept 13, 2026",
            "Free tier: one per subscription, no private endpoint or CMK",
        ], sub="Foundry IQ and vector stores", theme="teal", icon="ai-search", keys=("search_tier", "search_cost")),
        mcard("Memory", [
            "Billed as the chat and embedding models you configure",
            "Pricing can change while memory is in preview",
        ], sub="agent memory", badge="preview", theme="teal", icon="iq", keys=("ga",)),
        mcard("Cosmos DB, Storage, Key Vault, ACR", [
            "Standard agent setup runs in your accounts: Cosmos DB needs at least 3,000 RU/s in total (provisioned or serverless)",
            "Storage, Key Vault, ACR (hosted agents), App Insights and Log Analytics bill as normal Azure resources",
            "Basic setup uses Microsoft-managed storage",
        ], sub="bring your own", theme="cyan", icon="cosmos", keys=("std", "afaq")),
        mcard("Foundry Tools", [
            "Speech, Language, Translator, Vision, Document Intelligence, Content Understanding: each service's own meters",
            "Commitment tiers: a fixed fee for service features; extra usage is billed at the overage amount",
        ], sub="prebuilt AI services", theme="orange", icon="ai-services", keys=("cost", "p_tools")),
    ]

    cols = [(a1, "blue", "Pay per token (serverless)"), (a2, "blue", "Reserved capacity, GPUs, Marketplace"), (b, "blue", None),
            (c, "green", None), (d, "pink", None), (e, "violet", None), (f, "teal", None)]
    target = max(need_h(cs, lab is not None) for cs, _, lab in cols)
    panels = []
    for i, (cs, th, lab) in enumerate(cols):
        panels.append(family_panel(cv, X(i), y, P, cs, th, target, label=lab))
    # connect the heads to their panels
    for hc, i in zip(head_cards, (0, 2, 3, 4, 5, 6)):
        th = THEMES[FAMILIES[(0, 2, 3, 4, 5, 6).index(i)][2]]
        if i == 0:
            for j in (0, 1):
                dotted(cv, [(panels[j].cx, hc.bottom + 4), (panels[j].cx, panels[j].y - 4)], sw=3, head="arrow")
        else:
            dotted(cv, [(hc.cx, hc.bottom + 4), (panels[i].cx, panels[i].y - 4)], sw=3, head="arrow")
    return max(p.bottom for p in panels)


# ============================================================================================== build
def build(cv: Canvas) -> None:
    y = title_and_key(cv) + 50
    root = tree_top(cv, y)
    y = root.bottom + 110
    hc = heads(cv, y, root)
    y = max(c.bottom for c in hc) + 44
    y = families(cv, y, hc)
