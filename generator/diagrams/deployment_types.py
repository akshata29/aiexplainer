"""Foundry deployment types and offers - 'pick your lane'.

Layout: title + one-glance strip -> offers hub (serverless / managed compute / instant access) -> the 3x3 serverless grid
(Global / Data Zone / geography x Standard / Provisioned / Batch) with a nested 'where is it processed' diagram -> reference
tables for every type and offer -> decision tree -> Flex and Priority -> Batch -> islands -> lifecycle and gotchas -> sources.
No prices are drawn (the docs defer to the pricing pages); only documented percentages, limits and dates appear.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="deployment-types", title="Deployment types and offers", section="2", group="Models", order=21,
    description="Every way to run a Foundry model: the 3x3 serverless grid (Global, Data Zone, geography x Standard, Provisioned, Batch), Developer, Flex and Priority request-level tiers, managed compute, instant access, partner serverless and model router - with data-processing location, billing meter, SLA, limits and a 'which lane?' decision tree.",
    tags=["deployment-types", "global-standard", "provisioned", "batch", "flex", "priority", "data-zone"],
)

W = 3080
COL, GUT = 480, 40
SEC = 72
LR = metrics.line_ratio()


def X(i: int) -> float:
    return i * (COL + GUT)


def SPAN(n: int) -> float:
    return n * COL + (n - 1) * GUT


L = dict(
    types=("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
    gov=("Deployment types for Azure Government", learn("foundry-models/concepts/deployment-types-gov")),
    over=("Deployment overview for Foundry Models", learn("concepts/deployments-overview")),
    batch=("Batch deployments", learn("openai/how-to/batch")),
    flex=("Flex processing (preview)", learn("openai/how-to/flex-processing")),
    prio=("Priority processing", learn("openai/concepts/priority-processing")),
    mc=("Managed compute (preview)", learn("concepts/managed-compute-overview")),
    mcdep=("Deploy models on managed compute", learn("how-to/deploy-models-managed")),
    adapter=("Adapter (LoRA) deployments (preview)", learn("concepts/adapter-deployment-overview")),
    instant=("Instant access to models (preview)", learn("concepts/instant-models")),
    create=("Create model deployments", learn("foundry-models/how-to/create-model-deployments")),
    cost=("Plan and manage costs", learn("concepts/manage-costs")),
    ret=("Model retirements and lifecycle", learn("openai/concepts/model-retirements")),
    sched=("Model retirement schedule", learn("openai/concepts/model-retirement-schedule")),
    ver=("Model versions", learn("foundry-models/concepts/model-versions")),
    ptu=("Provisioned throughput", learn("openai/concepts/provisioned-throughput")),
    router=("Model router", learn("openai/concepts/model-router")),
    partners=("Models from partners and community", learn("foundry-models/concepts/models-from-partners")),
)


def src(*keys: str) -> list:
    return [L[k] for k in keys]


# ---------------------------------------------------------------------------------------------- helpers
def sec(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def learn_line(cv, x, y, items, gap=34, size=12):
    """Row of clickable 'Learn: ...' citations under a table or diagram."""
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * LR


class Sku(Rect2):
    """Grid cell / island card: title, optional monospace SKU pill, bullets and optional chips (chips: (label, theme))."""

    def __init__(self, w, title, code=None, body=(), *, theme="blue", fill="hatch", dash="solid", chips=(), badge=None,
                 icon=None, title_size=21, body_size=15, pad=14, min_h=0, icon_size=34, code_size=14, src=()):
        self.th = get_theme(theme)
        self.w, self.title, self.code, self.fill, self.dash = w, title, code, fill, dash
        self.title_size, self.body_size, self.pad, self.min_h = title_size, body_size, pad, min_h
        self.icon, self.icon_size, self.badge, self.code_size = icon, icon_size, badge, code_size
        inner = (w - 2 * pad) * 0.965
        self.bw = (metrics.line_width(STATUS.get(badge, ("gray", badge))[1], 13) + 18) if badge else 0
        self.icon_off = (icon_size + 10) if icon else 0
        t_w = inner - self.icon_off - ((self.bw + 8) if badge else 0)
        self.t_lines = metrics.wrap_text(title, t_w, title_size)
        y = pad + max(len(self.t_lines) * title_size * LR, icon_size if icon else 0)
        self.code_box = None
        if code:
            cw = metrics.line_width(code, code_size, metrics.MONO) + 18
            ch = code_size * metrics.line_ratio(metrics.MONO) + 8
            self.code_box = (y + 6, cw, ch)
            y += 6 + ch
        y += 8
        self.items = []
        for b in body:
            kind, text = "bullet", str(b)
            if text.startswith("! "):
                kind, text = "warn", text[2:]
            elif text.startswith("+ "):
                kind, text = "good", text[2:]
            lines = metrics.wrap_text(text, inner - 18, body_size)
            self.items.append((kind, y, lines))
            y += len(lines) * body_size * LR + 5
        if self.items:
            y -= 5
        self.chip_rows = []
        if chips:
            y += 10
            cur, rw = [], 0.0
            for label, th_name in chips:
                cw = metrics.line_width(label, 13) + 20
                if cur and rw + cw > inner:
                    self.chip_rows.append((y, cur))
                    y += 13 * LR + 12
                    cur, rw = [], 0.0
                cur.append((label, th_name, cw))
                rw += cw + 8
            self.chip_rows.append((y, cur))
            y += 13 * LR + 8
        self.src_lines = []
        if src:
            y += 8
            for label, url in src:
                lines = metrics.wrap_text(f"Learn: {label}", inner, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * 12 * LR + 2
            y -= 2
        self.h0 = y + pad
        self.h = max(self.h0, min_h)
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h0, h or 0, self.min_h)
        self.h = H
        th, pad = self.th, self.pad
        bg, fs = {"hatch": (th.fill, "hachure"), "soft": (th.soft, "solid"), "solid": (th.fill, "solid"),
                  "cross": (th.fill, "cross-hatch"), "none": ("transparent", "solid")}[self.fill]
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=2, dash=self.dash)
            tx = x + pad
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, self.icon_size)
                tx += self.icon_off
            cv.text(tx, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.bw, y + pad - 1, self.badge)
            if self.code_box:
                cy, cw, ch = self.code_box
                cv.rect(x + pad, y + cy, cw, ch, stroke=th.stroke, fill="#ffffff", style="solid", sw=1.5, rough=0)
                cv.text(x + pad + 9, y + cy + 4, self.code, size=self.code_size, color=INK, font=metrics.MONO)
            for kind, by, lines in self.items:
                ly = y + by
                color = {"bullet": INK, "warn": "#c92a2a", "good": "#2b8a3e"}[kind]
                cv.text(x + pad + 18, ly, "\n".join(lines), size=self.body_size, color=color)
                mc = {"bullet": th.stroke if th.name not in ("gray", "ink") else "#f08c00", "warn": "#e03131",
                      "good": "#2f9e44"}[kind]
                cv.ellipse(x + pad + 4, ly + self.body_size * LR / 2 - 4, 9, 9, stroke=mc, sw=2, rough=0)
            for cy, chips in self.chip_rows:
                cx = x + pad
                for label, th_name, cw in chips:
                    ct = get_theme(th_name)
                    cv.rect(cx, y + cy, cw, 13 * LR + 6, stroke=ct.stroke, fill=ct.fill, style="solid", sw=1.5, rough=0)
                    cv.text(cx + 10, y + cy + 3, label, size=13, color=ct.deep)
                    cx += cw + 8
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"sku:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


# ---------------------------------------------------------------------------------------------- 0. title + glance strip
def top_block(cv):
    _, b = title_block(cv, 0, 0, "Foundry deployment types: pick your lane",
                       "Every way to run a Foundry model - where the prompt is processed, how you pay and what is guaranteed (as of 2026-11-03)",
                       w=W)
    y = b + 26
    legend(cv, 0, y, [("Standard: pay per token", "blue"), ("Provisioned: reserved PTU", "yellow"),
                      ("Batch: async, 50% off", "cyan"), ("Request-level tier: Flex, Priority", "lime"),
                      ("Developer and other offers", "gray")])
    cv.text(2280, y, "Dashed border = preview offer. Dates and limits as of 2026-11-03.", size=15, color=MUTED)
    y += 50
    cards = [
        Card(SPAN(2), "1. Where is the prompt processed?", [
            "Global: any Azure region - highest quota, newest models first",
            "Data Zone: only inside the US, EU or APAC zone",
            "Standard and Regional Provisioned: inside the Azure geography you pick",
            "Data at rest always stays in the designated Azure geography",
        ], theme="blue", icon="regions", src=src("types")),
        Card(SPAN(2), "2. How do I pay?", [
            "Pay per token: Standard; Flex is 50% off (preview), Priority has its own rate",
            "Reserved PTUs: Provisioned, billed hourly or through an Azure reservation",
            "Batch: 50% off Global Standard with a 24-hour target",
            "Managed compute: hourly per accelerator (preview)",
        ], theme="yellow", icon="cost-management", src=src("types", "cost")),
        Card(SPAN(2), "3. What is guaranteed?", [
            "Provisioned: guaranteed throughput, lower latency variance",
            "Standard types: best-effort; Priority adds a latency target",
            "Batch and Flex: no real-time or latency SLA",
            "Developer, managed compute and instant access: no SLA (the last two are preview)",
        ], theme="gray", icon="service-health", src=src("types")),
    ]
    _, b2 = row(cv, 0, y, cards, gap=GUT)
    n = Note(W, "For most workloads start with Global Standard: it launches first when a new model ships, has the lowest price, the broadest region coverage and the highest default quota. "
                "Move only for a reason: data residency, reserved throughput or asynchronous batch work.",
             kind="key", title="Not sure? Start with Global Standard", size=16, src=src("types"))
    n.place(cv, 0, b2 + 28)
    return n.bottom


# ---------------------------------------------------------------------------------------------- 1. three offers
def offers(cv, y):
    y = sec(cv, y, "1  Three offers: serverless API, managed compute, instant access",
            sub="The nine deployment types apply to the serverless API only. Open-source and custom weights on managed compute do not use them.") + 40
    app = Box(420, "Your app or agent", sub="OpenAI-compatible SDK or REST", theme="gray", icon="app", icon_pos="left", h=100, size=20)
    ax = (W - app.w) / 2
    app.place(cv, ax, y)
    n1 = Note(1180, "Azure OpenAI resources show only Azure OpenAI models in the catalog. Upgrade to a Foundry resource to deploy the full catalog.",
              kind="info", title="Resource type matters", size=15, src=src("over"))
    n1.place(cv, 0, y)
    n2 = Note(1180, "A partner provider decides whether its model runs on managed compute or serverless. Serverless means Microsoft hosts it; the provider sets licence and price and you pay through Azure Marketplace.",
              kind="info", title="Partner models: two hosting choices", size=15, src=src("partners"))
    n2.place(cv, W - 1180, y)
    cy = y + max(app.h, n1.h, n2.h) + 130
    a = Card(SPAN(2), "Serverless API", [
        "Models: all Foundry Models, sold by Azure plus select partner models; lives in a Foundry resource (no AI hub)",
        "Types: Standard, Provisioned, Batch and Developer, scoped Global, Data Zone or geography where offered (the grid in section 2)",
        "Billing in tokens, or reserved PTUs for Provisioned",
        "Where the prompt is processed is set by the deployment type: Global, Data Zone or geography",
        "Quota: TPM and RPM pools for pay-per-token types, PTUs for Provisioned (see the PTU and quota canvas)",
        "Content filtering, Entra keyless auth and private networking are available",
        "Call it with model = your deployment name",
    ], theme="blue", icon="openai", subtitle="Preferred, most capable option", src=src("over"))
    b = Card(SPAN(2), "Managed compute", [
        "Open-source, partner, industry and custom weights on dedicated GPUs, in a Foundry project",
        "Unit of scale is a model instance; a deployment template pins runtime, accelerator, count and context length",
        "Billed hourly per accelerator; quota is per accelerator family per region, separate from Azure VM quota",
        "Global only; no built-in content filtering; no SLA while in preview",
        "Call <endpoint>/managed-deployments/<name>/ (or /openai/v1/ for OpenAI-compatible runtimes)",
    ], theme="blue", icon="vm", dash="dashed", badge="preview", subtitle="Open weights on your own GPUs", src=src("mc"))
    c = Card(SPAN(2), "Instant access", [
        "Call a supported model by name with no deployment - it is not a deployment option",
        "Default is the latest evergreen model; pin one with a dated suffix such as model-name-2025-04-01",
        "Billed per token against a per-model global quota pool",
        "West US 3 is the only supported project region; Foundry User role",
        "Not for reserved capacity, PTU, data residency or per-model filters",
        "Admins can block models with Azure Policy or switch the feature off on the account",
    ], theme="blue", icon="functions", dash="dashed", badge="preview", subtitle="Call by name, nothing to deploy", src=src("instant"))
    cards = [a, b, c]
    _, bottom = row(cv, 0, cy, cards, gap=GUT)
    labels = ["model = deployment name", "managed-deployments/<name>", "model = model name"]
    for card, lab in zip(cards, labels):
        connect(cv, app, card, a_side="bottom", b_side="top", route="elbow", label=lab, label_size=15, sw=2.5, label_t=0.78,
                label_pos="above" if card is not b else "right")
    return bottom


# ---------------------------------------------------------------------------------------------- 2. grid
GX0, CW, GG = 226, 470, 16


def gx(i):
    return GX0 + i * (CW + GG)


def grid_section(cv, y):
    y = sec(cv, y, "2  The serverless grid: three scopes x three billing meters",
            sub="Nine SKU codes. Flex and Priority are not rows or columns: they are request-level tiers on Standard deployments.") + 36
    top = y
    corner = Box(210, "Scope", sub="where it is processed", theme="gray", fill="soft", h=72, size=22)
    corner.place(cv, 0, y)
    heads = [("Standard", "pay per token", "blue"), ("Provisioned", "reserved PTU, hourly or reservation", "yellow"),
             ("Batch", "50% off, 24-hour target", "cyan")]
    for i, (t, s, th) in enumerate(heads):
        Box(CW, t, sub=s, theme=th, h=72, size=24, fill="solid").place(cv, gx(i), y)
    y += 72 + 16

    def S(*a, **k):
        return Sku(CW, *a, **k)

    rows = [
        ("Global", "any Azure region", [
            S("Global Standard", "GlobalStandard", ["Any Azure region, pay per token", "Newest models first, lowest price, broadest regions, highest default quota",
                                                    "Best-effort latency"],
              theme="blue", chips=[("DEFAULT START", "yellow"), ("Flex (preview)", "lime"), ("Priority", "lime")]),
            S("Global Provisioned", "GlobalProvisionedManaged", ["Any Azure region, reserved PTUs", "Predictable high throughput; lower, more consistent latency than Global Standard",
                                                                  "Hourly PTU billing or an Azure reservation"], theme="yellow"),
            S("Global Batch", "GlobalBatch", ["Any Azure region, 50% off Global Standard", "24-hour target with a separate enqueued-token quota",
                                              "Large asynchronous jobs"], theme="cyan"),
        ]),
        ("Data Zone", "inside US, EU or APAC", [
            S("Data Zone Standard", "DataZoneStandard", ["Processed only inside the data zone: US, EU or APAC", "Higher default quota than geography types",
                                                         "Pay per token"], theme="blue", chips=[("Priority (US zone only)", "lime")]),
            S("Data Zone Provisioned", "DataZoneProvisionedManaged", ["Reserved PTUs, processed inside the data zone", "Zone compliance plus predictable throughput"],
              theme="yellow"),
            S("Data Zone Batch", "DataZoneBatch", ["Same as Global Batch: 50% off, 24-hour target", "Traffic routed only to datacenters inside the zone"],
              theme="cyan"),
        ]),
        ("Regional", "inside one Azure geography", [
            S("Standard (regional)", "Standard", ["Pay per token, processed inside the geography you pick", "Low-to-medium volume with bursts",
                                                  "Model and throughput availability can be limited; launches last"], theme="blue"),
            S("Regional Provisioned", "ProvisionedManaged", ["Reserved PTUs inside one Azure geography", "Geography compliance plus throughput, where supported"],
              theme="yellow"),
            S("Regional Batch: n/a", None, ["No regional batch type exists - the Batch types are Global and Data Zone"], theme="gray", fill="cross", dash="dashed"),
        ]),
    ]
    for label, sub, cells in rows:
        rh = max(c.h for c in cells)
        Box(210, label, sub=sub, theme="gray", fill="soft", h=rh, size=24).place(cv, 0, y)
        for i, c in enumerate(cells):
            c.place(cv, gx(i), y, h=rh)
        y += rh + GG
    left_bottom = y - GG
    n = Note(gx(2) + CW, "Flex is a per-request tier and Priority a deployment toggle or request tier on Standard deployments, so both share the Standard quota. "
                         "Not every model supports every type: check the model's availability table.",
             kind="gotcha", title="Flex and Priority are not deployment types", size=15, src=src("flex", "prio"))
    n.place(cv, 0, left_bottom + 22)
    left_bottom = n.bottom

    # ---- right column: nested scopes, launch order, Developer
    rx, rw = gx(2) + CW + 62, W - (gx(2) + CW + 62)
    oy = top
    OH = 440
    th = get_theme("blue")
    cv.rect(rx, oy, rw, OH, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dotted")
    cv.text(rx + 22, oy + 14, "Global: any Azure region where the model is deployed", size=22, color=th.deep)
    cv.text(rx + 22, oy + 44, "GlobalStandard | GlobalProvisionedManaged | GlobalBatch (DeveloperTier also runs in any region)", size=14, color=INK, font=metrics.MONO)
    mx, my, mw, mh = rx + 36, oy + 84, rw - 72, OH - 84 - 28
    cv.rect(mx, my, mw, mh, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    cv.text(mx + 22, my + 12, "Data Zone: only inside the Microsoft-specified zone", size=22, color=th.deep)
    cv.text(mx + 22, my + 42, "DataZoneStandard | DataZoneProvisionedManaged | DataZoneBatch", size=14, color=INK, font=metrics.MONO)
    zw = (mw - 44 - 2 * 18) / 3
    zx = mx + 22
    zones = [("US", "anywhere in the US; the docs tables show centralus, eastus, eastus2, northcentralus, southcentralus, westus, westus3"),
             ("EU", "Azure EU Data Boundary; may include EFTA countries such as Norway and Switzerland"),
             ("APAC", "multiple Asia Pacific regions")]
    for i, (t, s) in enumerate(zones):
        Box(zw, t, sub=s, theme="blue", fill="soft", h=122, size=22, sub_size=14).place(cv, zx + i * (zw + 18), my + 74)
    ix, iy, iw, ih = mx + 40, my + 74 + 122 + 20, mw - 80, mh - (74 + 122 + 20) - 20
    cv.rect(ix, iy, iw, ih, stroke=th.stroke, fill="#ffffff", style="solid", sw=2)
    cv.text(ix + 20, iy + 12, "Geography: inside the Azure geography you pick", size=21, color=th.deep)
    cv.text(ix + 20, iy + 42, "Standard | ProvisionedManaged - may move between regions inside the geography for operational purposes", size=14, color=INK)
    rn = Note(rw, "Data at rest always stays in the designated Azure geography. Only the inference processing differs by type. Microsoft can add regions to a data zone without prior notice.",
              kind="key", title="Residency rule", size=15, src=src("types"))
    rn.place(cv, rx, oy + OH + 22)
    ly = rn.bottom + 26
    cv.text(rx, ly, "Launch order for a new model", size=20, color=th.deep)
    ly += 34
    bw = (rw - 2 * 90) / 3
    steps = [("1  Global", "Standard, Provisioned and Batch first", "blue"), ("2  Data Zone", "next", "blue"),
             ("3  Geography", "last: no guaranteed date, depends on capacity freed by retiring models", "blue")]
    boxes = []
    for i, (t, s, tc) in enumerate(steps):
        bx = Box(bw, t, sub=s, theme=tc, fill="soft", size=19, sub_size=13, h=96).place(cv, rx + i * (bw + 90), ly)
        boxes.append(bx)
    for a_, b_ in zip(boxes, boxes[1:]):
        connect(cv, a_, b_, a_side="right", b_side="left", sw=2.5)
    ly = boxes[0].bottom + 26
    dev = Sku(rw, "Developer", "DeveloperTier", [
        "Fine-tuned model evaluation only: fixed 24-hour lifetime, then the deployment is auto-deleted",
        "Pay per token, any Azure region, no SLA and no data-residency guarantee",
        "Not for latency-sensitive work. To host a fine-tune for real use a Standard, Global or Data Zone fine-tune deployment",
    ], theme="gray", icon="dev-box", src=src("types"))
    dev.place(cv, rx, ly)
    return max(left_bottom, dev.bottom)


# ---------------------------------------------------------------------------------------------- 3. reference tables
def tables(cv, y):
    y = sec(cv, y, "3  Every type and offer side by side",
            sub="Data-processing location, billing meter, SLA and the limits that matter. Quotas and PTU sizing live in the PTU and quota canvas.") + 36
    cols = [("Type or offer", 250), ("SKU or how you select it", 340), ("Data processing", 340), ("Billing meter", 330),
            ("SLA and latency", 380), "Limits, notes and gotchas"]
    tb = lambda t, th: (t, th)
    rows_a = [
        [tb("Global Standard", "blue"), "GlobalStandard", "Any Azure region", "Pay per token",
         "Best-effort; latency can vary at high consistent volume",
         "Launches first, lowest price, broadest regions, highest default quota. Supports Flex (preview) and Priority. If the primary region is interrupted, traffic routed to it is affected"],
        [tb("Global Provisioned", "yellow"), "GlobalProvisionedManaged", "Any Azure region", "Reserved PTUs: hourly or an Azure reservation",
         "Guaranteed throughput, lower and more consistent latency",
         "Minimum PTUs and capacity vary by model. Never auto-upgraded to a new model version (manual migration)"],
        [tb("Global Batch", "cyan"), "GlobalBatch", "Any Azure region", "50% discount vs Global Standard",
         "No real-time SLA; 24-hour target - jobs are not expired, cancel anytime, completed work is billed",
         "Separate enqueued-token quota; 200 MB and 100,000 requests per input file; no fine-tuned models. Never auto-upgraded"],
        [tb("Data Zone Standard", "blue"), "DataZoneStandard", "Inside the data zone (US, EU or APAC)", "Pay per token", "Best-effort",
         "Higher default quota than geography types; supports Priority in the US zone only; same primary-region interruption caveat as Global Standard"],
        [tb("Data Zone Provisioned", "yellow"), "DataZoneProvisionedManaged", "Inside the data zone", "Reserved PTUs",
         "Guaranteed throughput, lower latency variance", "Data-zone compliance plus predictable throughput. Never auto-upgraded"],
        [tb("Data Zone Batch", "cyan"), "DataZoneBatch", "Inside the data zone", "50% discount", "No real-time SLA; 24-hour target",
         "Same functionality as Global Batch, traffic stays inside the zone"],
        [tb("Standard (regional)", "blue"), "Standard", "Inside the Azure geography you pick; may move between its regions for operational purposes",
         "Pay per token", "Best-effort",
         "Low-to-medium volume with bursts; models and throughput can be limited; geography types launch last with no guaranteed date"],
        [tb("Regional Provisioned", "yellow"), "ProvisionedManaged", "Inside one Azure geography", "Reserved PTUs", "Guaranteed throughput",
         "Geography compliance plus throughput, where supported; minimum PTUs vary by model"],
        [tb("Developer", "gray"), "DeveloperTier", "Any Azure region, no residency guarantee", "Pay per token", "No SLA",
         "Fine-tuned model evaluation only; fixed 24-hour lifetime, then auto-deleted"],
    ]
    ta = Table(cols, rows_a, w=W, theme="blue", size=14, head_size=15, title="A. The nine serverless deployment types (SKU codes as used in CLI, ARM and Bicep)", title_size=22)
    ta.place(cv, 0, y)
    ly = learn_line(cv, 0, ta.bottom + 8, src("types", "ptu"))
    rows_b = [
        [tb("Flex (preview)", "lime"), "Request service_tier = flex (or header x-ms-service-tier: flex) on a Global Standard deployment", "As the Global Standard deployment",
         "50% off input and output tokens; cached-token discount applies; dedicated Flex meters", "Variable latency; no latency SLA and no service SLA",
         "HTTP 429 when preemptible Flex capacity is unavailable (not billed); no automatic fallback; unsupported model = HTTP 400; shares Standard quota"],
        [tb("Priority", "lime"), "Deployment toggle (ARM properties.service_tier) and/or request service_tier = priority", "Global Standard and Data Zone Standard (US) only",
         "Priority pay-per-token rate", "Latency target per model, for example 80 tokens/s for gpt-6-sol; can be re-routed to Standard",
         "Model versions 2025-12-01 or later; not on regional Standard or EU Data Zone; same quota as Standard"],
        [tb("Serverless partner models (MaaS)", "gray"), "Partner model deployed from the catalog", "Mostly Global Standard; Claude: Global Standard, plus Data Zone Standard (US) for Azure-hosted; Fireworks: Global or Data Zone (US), Standard or Provisioned",
         "Provider sets price; billed through Azure Marketplace (CCU-billed Claude differs)", "Best-effort unless Provisioned",
         "Marketplace region and billing-country eligibility applies; default filter is Content Safety text moderation, billed separately (Claude has none built in)"],
        [tb("Managed compute (preview)", "gray"), "SKU GlobalManagedCompute; endpoint .../managed-deployments/<name>/", "Global only (Data Zone and more regions rolling out)",
         "Accelerators per instance x instances x hours x hourly rate; deleting stops billing", "Preview, no SLA",
         "Quota per accelerator family per region, separate from VM quota; no built-in content filtering; 10-15 min to provision"],
        [tb("Instant access (preview)", "gray"), "Call by model name on the project endpoint, e.g. model = gpt-5-mini", "Project in West US 3 only; per-model global quota pool",
         "Pay per token", "Preview, no SLA",
         "No PTU, data residency, per-model filters, version locks or fine-tunes; a same-named deployment shadows the instant model"],
        [tb("Model router", "gray"), "Deploy model-router (version 2025-11-18) like any model", "Global Standard and Data Zone Standard only",
         "Sum of the underlying models' token costs", "Follows the underlying Standard types",
         "32 regions; one rate limit and one content filter for the whole deployment; see the Model router canvas"],
        [tb("LoRA adapter (preview)", "gray"), "Adapter deployment attached to a target deployment", "Same as its target (managed compute)",
         "No extra compute and no separate price", "Preview, no SLA",
         "Adapters come from Foundry fine-tuning jobs only (no import yet); adapter version is pinned; scaling the target scales all adapters"],
    ]
    tb2 = Table(cols, rows_b, w=W, theme="lime", size=14, head_size=15, title="B. Request-level tiers and the other offers", title_size=22)
    tb2.place(cv, 0, ly + 40)
    ly = learn_line(cv, 0, tb2.bottom + 8, src("flex", "prio", "mc", "instant", "adapter", "router"))
    return ly


# ---------------------------------------------------------------------------------------------- 4. decision tree
def decide(cv, y):
    y = sec(cv, y, "4  Which lane? A decision tree",
            sub="Answer from the top; the first yes wins. Part A can skip the serverless grid. Part B ends in one cell of the grid.") + 36
    PW, PH = 1500, 800
    BX = W - PW
    with cv.panel(0, y, w=PW, h=PH, title="A. Do you even need a serverless deployment?", theme="gray", style="dotted", pad=20, title_size=22):
        pass
    with cv.panel(BX, y, w=PW, h=PH, title="B. Pick a cell of the grid", theme="blue", style="dotted", pad=20, title_size=22):
        pass
    DW, DH, PITCH = 380, 140, 186
    r0 = y + 96

    def dia(x, i, text, th):
        return Box(DW, text, shape="diamond", theme=th, h=DH, size=17, fill="soft").place(cv, x, r0 + i * PITCH)

    def leaf(x, w, dq, label, sub, th, icon=None, dash="solid", badge=None, h=124):
        c = Card(w, label, ["= " + sub], theme=th, icon=icon, dash=dash, badge=badge, title_size=20, body_size=15, min_h=h)
        return c.place(cv, x, dq.cy - c.h / 2)

    ax = 24
    q1 = dia(ax, 0, "Just trying a model or need the newest today?", "gray")
    q2 = dia(ax, 1, "Open weights on dedicated GPUs?", "gray")
    q3 = dia(ax, 2, "Evaluating a fine-tune briefly?", "gray")
    lx, lw = ax + DW + 110, PW - 48 - DW - 110
    l1 = leaf(lx, lw, q1, "Instant access", "Call the model by name, no deployment: project in West US 3, Foundry User role. No PTU, data residency or per-model filters",
              "blue", icon="functions", dash="dashed", badge="preview")
    l2 = leaf(lx, lw, q2, "Managed compute", "Open or custom weights on dedicated GPUs, billed per accelerator-hour; Global only, no content filter. Or Hugging Face / Fireworks bring-your-own-model with PTU",
              "blue", icon="vm", dash="dashed", badge="preview")
    l3 = leaf(lx, lw, q3, "Developer tier", "Evaluate a fine-tuned model for up to 24 hours: pay per token, no SLA, auto-deleted. Hosting it for real needs a Standard, Global or Data Zone fine-tune deployment",
              "gray", icon="dev-box")
    connect(cv, q1, q2, a_side="bottom", b_side="top", label="no", label_size=15, sw=2.5)
    connect(cv, q2, q3, a_side="bottom", b_side="top", label="no", label_size=15, sw=2.5)
    for q, lf in ((q1, l1), (q2, l2), (q3, l3)):
        connect(cv, q, lf, a_side="right", b_side="left", label="yes", label_size=15, sw=2.5)
    crown = Note(PW - 48, "Default when you are unsure: Global Standard. Flex and Priority are request-level choices on top of it, not separate deployments.",
                 kind="key", title="Default lane", size=16)
    crown.place(cv, ax, r0 + 3 * PITCH + 10)

    bx0 = BX + 24
    q4 = dia(bx0, 0, "Can it wait up to 24 hours?", "blue")
    q5 = dia(bx0, 1, "How local must processing be?", "blue")
    q6 = dia(bx0, 2, "Need guaranteed throughput and stable latency?", "yellow")
    blx = bx0 + DW + 110
    blw = BX + PW - 24 - blx
    l4 = leaf(blx, blw, q4, "Global Batch or Data Zone Batch", "50% off Global Standard: JSONL jobs, 24-hour target, separate enqueued-token quota, no real-time SLA. Data Zone Batch keeps data inside the zone",
              "cyan", icon="batch")
    gw = (blw - 2 * 22 - 28) / 3
    scope = [("Global", "no residency need", "blue"), ("Data Zone", "inside US, EU or APAC", "blue"),
             ("Geography", "Standard or Regional Provisioned; arrive last, limited", "blue")]
    with cv.panel(blx, q5.cy - 98, w=blw, h=196, title="Pick one row of the grid", theme="blue", style="dashed", pad=14, title_size=18) as sp:
        pass
    sbx = []
    for i, (t, s, th) in enumerate(scope):
        sbx.append(Box(gw, t, sub=s, theme=th, h=124, size=20, sub_size=14, fill="hatch").place(cv, blx + 14 + i * (gw + 22), sp.y + 44))
    l6 = leaf(blx, blw, q6, "Provisioned (PTU) in the same scope", "Reserved capacity, lower and more consistent latency. Add spillover to Standard for peaks (see the PTU and quota canvas)",
              "yellow", icon="quotas")
    fin = Box(PW - 48, "Standard (pay per token): the default for variable, bursty traffic", theme="blue", h=110, size=20, sub_size=15,
              sub="Latency-sensitive without a commitment: add Priority (Global Standard or Data Zone Standard, US). Delay-tolerant and cheap: add Flex (preview, Global Standard)",
              fill="hatch").place(cv, bx0, r0 + 3 * PITCH + 10)
    connect(cv, q4, q5, a_side="bottom", b_side="top", label="no", label_size=15, sw=2.5)
    connect(cv, q5, q6, a_side="bottom", b_side="top", label="then", label_size=15, sw=2.5)
    connect(cv, q6, fin, a_side="bottom", b_side="top", tb=(q6.cx - fin.x) / fin.w, label="no", label_size=15, sw=2.5)
    connect(cv, q4, l4, a_side="right", b_side="left", label="yes", label_size=15, sw=2.5)
    connect(cv, q5, sp, a_side="right", b_side="left", label="answer", label_size=15, sw=2.5)
    connect(cv, q6, l6, a_side="right", b_side="left", label="yes", label_size=15, sw=2.5)
    gutter = (PW + BX) / 2
    yb = q3.bottom + 30
    connect(cv, q3, q4, a_side="bottom", b_side="left", via=[(q3.cx, yb), (gutter, yb), (gutter, q4.cy)], label="no: go to B", label_size=15,
            label_t=0.2, label_pos="above", sw=2.5)
    return y + PH


# ---------------------------------------------------------------------------------------------- 5. gotchas and dates
def gotchas(cv, y):
    y = sec(cv, y, "5  Gotchas and dates to remember",
            sub="The lane details (Flex, Priority, Batch, managed compute, instant access, Azure Government) continue in part 2 of this explainer.") + 36
    n = lambda kind, title, text, *keys: Note(COL, text, kind=kind, title=title, size=15, src=src(*keys))
    r1 = [
        n("gotcha", "Provisioned and Batch never auto-upgrade",
          "Standard types move to a new model version automatically (unless you opt out), region by region. Provisioned and Batch deployments are never auto-upgraded: migrate them yourself. A NoAutoUpgrade deployment stops working at retirement (inference then returns 410 Gone).", "ver", "ret"),
        n("warn", "Flex: expect 429s, no fallback",
          "Flex capacity is preemptible, so HTTP 429 is normal and rejected requests are not billed. Nothing falls back for you: retry with service_tier default. An unsupported model returns HTTP 400.", "flex"),
        n("warn", "Priority can silently downgrade",
          "Priority is not on regional Standard or the EU Data Zone. A request can be re-routed to Standard (billed at the Standard rate, response shows service_tier default) on a ramp-rate limit, peak demand or long context.", "prio"),
        n("info", "Batch quota is enqueued tokens",
          "Batch does not use TPM. Enqueued tokens stay counted until the job reaches a final state, and a submission can fail when enqueued quota is insufficient.", "batch"),
        n("gotcha", "Developer deployments vanish",
          "A Developer deployment has a fixed 24-hour lifetime and is auto-deleted. It is for evaluating a fine-tune, never for serving traffic.", "types"),
        n("warn", "Instant access is narrow (preview)",
          "No custom filters, PTU or fine-tunes, and only West US 3 during preview. A deployment with the same name shadows the instant model.", "instant"),
    ]
    _, b1 = row(cv, 0, y, r1, gap=GUT)
    r2 = [
        n("warn", "Managed compute quota is not VM quota (preview)",
          "Quota is requested per accelerator family per region through the Foundry quota process. Global scope only and no built-in content filter.", "mc"),
        n("info", "Partner models offer fewer types",
          "Anthropic and Fireworks models are mostly Global plus US Data Zone Standard; check each model's availability table.", "partners"),
        n("info", "Where the cost shows up",
          "Group Cost Management by Meter. Marketplace partner meters appear under the resource group (CCU-billed Claude under the Foundry resource). Project-level attribution (preview) covers sold-by-Azure models only.", "cost"),
        n("warn", "Docs disagree: data zones",
          "The provisioned-throughput page says Data Zone means US or EU; the deployment-types page lists US, EU and APAC. Check your model's region table.", "types", "ptu"),
        n("warn", "Docs disagree: Flex models",
          "The Flex page says gpt-5.6-sol is the first supported model, yet its table lists seven models (all Global Standard).", "flex"),
        n("warn", "Docs disagree: SKU codes",
          "The deployment-types Bicep sample still uses GlobalProvisioned, Provisioned and publisher xAI, older than the ...ProvisionedManaged codes in its own table.", "types"),
    ]
    _, b2 = row(cv, 0, b1 + 26, r2, gap=GUT)
    ty = b2 + 60
    cv.text(0, ty, "Dates that matter (as of 2026-11-03, from the retirement schedule)", size=24, color=get_theme("red").deep)
    t_end = timeline(cv, 0, ty + 44 + 150, W, [
        ("2026-11-19", "o1, o3, o3-mini, o4-mini and Llama-4-Maverick retire", "named replacements: gpt-5.6-sol for the o1 and o3 families, gpt-5.6-terra for o3-mini and o4-mini"),
        ("2027-01-14", "gpt-4o 2024-05-13 retires", "Standard types auto-upgrade it to gpt-5.1 (2025-11-13)"),
        ("2027-04-14", "gpt-4.1 family and later gpt-4o versions retire", "Provisioned and Batch deployments need manual migration"),
        ("2027-05-20", "model-router 2025-11-18 (GA) retires", "retirement dates are not extendable"),
        ("2028-02-09", "Embedding models retire", "extended timeline compared with other models"),
    ], size=17, label_w=520, theme="red")
    return learn_line(cv, 0, t_end + 10, src("sched", "ret"))


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    y = top_block(cv)
    y = offers(cv, y + SEC)
    y = grid_section(cv, y + SEC)
    y = tables(cv, y + SEC)
    y = decide(cv, y + SEC)
    y = gotchas(cv, y + SEC)
    sources(cv, 0, y + SEC, [
        L["types"], L["gov"], L["over"], L["batch"], L["flex"], L["prio"], L["mc"], L["mcdep"], L["adapter"], L["instant"],
        L["create"], L["cost"], L["ret"], L["ver"],
    ], w=W, cols=3)
