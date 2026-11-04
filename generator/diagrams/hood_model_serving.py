"""Under the hood: model serving internals - routing scope, quota gate, PTU leaky bucket, spillover, tiers, caching, router."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="hood-model-serving", title="Model serving internals", section="8", order=4,
    description="How a model request is served as documented: Global / Data Zone / Regional routing, Standard TPM/RPM gate vs PTU leaky bucket, spillover, service tiers, prompt caching, model router and managed compute.",
    tags=["model serving", "ptu", "quota", "spillover", "model router"],
)

W = 2950
INK_GRAY = "#495057"

# ---------------------------------------------------------------- citations
L_DEPLOY = ("Deployment types", learn("foundry-models/concepts/deployment-types"))
L_PTU = ("Provisioned throughput", learn("openai/concepts/provisioned-throughput"))
L_PTU_OPS = ("Operate provisioned deployments", learn("openai/how-to/provisioned-get-started"))
L_SPILL = ("Spillover traffic management", learn("openai/how-to/spillover-traffic-management"))
L_QUOTA = ("Manage quota and rate limits", learn("openai/how-to/quota"))
L_CACHE = ("Prompt caching", learn("openai/how-to/prompt-caching"))
L_PRIO = ("Priority processing", learn("openai/concepts/priority-processing"))
L_FLEX = ("Flex processing", learn("openai/how-to/flex-processing"))
L_BATCH = ("Batch deployments", learn("openai/how-to/batch"))
L_ROUTER = ("Model router", learn("openai/concepts/model-router"))
L_ROUTER_HOW = ("How model router works", learn("openai/concepts/model-router-how-it-works"))
L_MANAGED = ("Managed compute", learn("concepts/managed-compute-overview"))
L_INSTANT = ("Instant models", learn("concepts/instant-models"))
L_ARCH = ("Foundry architecture", learn("concepts/architecture"))


# ---------------------------------------------------------------- small helpers
def evidence_key(cv: Canvas, right: float, y: float) -> None:
    """Legend for the three evidence styles (solid / dashed / dotted grey)."""
    specs = [("solid", INK_GRAY, "Documented on Learn", ""),
             ("dashed", INK_GRAY, "Video or blog only (video/blog)", ""),
             ("dotted", "#868e96", "Not documented", "?")]
    widths = [64 + 14 + text_size(s[2], 15)[0] for s in specs]
    total = sum(widths) + 36 * (len(specs) - 1)
    x = right - total
    cv.text(x, y, "Evidence key", size=15, color=MUTED)
    cx, cy = x, y + 26
    for (dash, stroke, label, mark), w in zip(specs, widths):
        cv.rect(cx, cy, 64, 32, stroke=stroke, fill="#f1f3f5", style="solid", sw=2, dash=dash)
        if mark:
            mw, mh = text_size(mark, 20)
            cv.text(cx + (64 - mw) / 2, cy + (32 - mh) / 2, mark, size=20, color="#868e96")
        cv.text(cx + 78, cy + 5, label, size=15, color=INK)
        cx += w + 36


def banner(cv: Canvas, y: float, letter: str, title: str, sub: str, theme: str = "blue") -> float:
    """Section banner with a lettered marker; returns the y where content can start."""
    numbered(cv, 24, y + 30, letter, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 62, y, title, sub, size=34, sub_size=17, w=W - 62)
    return bottom + 26


def nd_box(w: float, label: str, sub: str = "not documented", h=None) -> Box:
    """Dotted grey 'not documented' placeholder."""
    return Box(w, "? " + label, sub=sub, theme="gray", dash="dotted", fill="none", size=16, sub_size=14, h=h)


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Model serving internals",
                                "From 'your request hits a deployment' to 'tokens come back' - as documented on Learn (as of 2026-11-03)",
                                w=W)
    evidence_key(cv, W, 6)

    y = bottom + 44
    y = knobs_strip(cv, y)
    y = hero_chain(cv, y + 40)
    y = section_a(cv, y + 70)
    y = section_b(cv, y + 70)


def knobs_strip(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Five knobs decide where it runs, how it is throttled, what it costs and which model answers", size=30)
    y += 64
    knobs = [
        ("A", "Where is it processed?", "Deployment type: Global, Data Zone or Regional", "blue", "regions"),
        ("B", "Which throttle applies?", "Standard: TPM and RPM windows. Provisioned: a leaky bucket on PTU utilization", "yellow", "quotas"),
        ("C", "Which tier?", "Standard, Priority, Flex (preview), Batch or Provisioned", "yellow", "reservations"),
        ("D", "What is cached?", "An identical prompt prefix of at least 1,024 tokens", "cyan", None),
        ("E", "Which model answers?", "Your deployment, or model router picks per request", "blue", "traffic-manager"),
    ]
    boxes = []
    x = 0
    for letter, label, sub, th, icon in knobs:
        b = Box(550, label, sub=sub, theme=th, icon=icon, icon_pos="left", icon_size=40, size=21, sub_size=15, h=118, fill="hatch")
        b.place(cv, x, y)
        numbered(cv, x + 22, y + 4, letter, theme=th, d=34, size=20)
        boxes.append(b)
        x += 550 + 50
    return y + 118


def hero_chain(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "One inference request through the serving path", size=30,
                   sub="Each stage is documented on Learn; the exact internal order between them is not (see the grey box)", sub_size=16)
    y += 84
    stages = [
        ("Call the deployment", "Deployment name, model-router or an instant model at .../openai/v1/responses", "gray", "api"),
        ("Authn + RBAC", "Entra ID token or key, then Azure RBAC on the account or project", "red", "managed-identity"),
        ("Input content filter", "Runs inline with the request; policy configured per deployment", "pink", "content-safety"),
        ("Quota gate", "Standard: TPM / RPM check. Provisioned: utilization check", "yellow", "quotas"),
        ("Model router", "Only if you called model-router: analyse prompt, pick a model, fail over", "blue", "traffic-manager"),
        ("Prompt-cache lookup", "Identical first 1,024 tokens -> cached tokens", "cyan", None),
        ("Inference", "Runs in the region, zone or global pool your SKU defines", "blue", "openai"),
        ("Output content filter", "Inline on the output; configurable per deployment", "pink", "content-safety"),
        ("Response", "model, service_tier and cached_tokens are reported back", "gray", "api"),
        ("Metrics", "Utilization V2, requests (IsSpillover), ServiceTierRequest / Response", "violet", "monitor"),
    ]
    bw, gap, bh = 250, 50, 188
    boxes = []
    x = 0
    for i, (label, sub, th, icon) in enumerate(stages):
        b = Box(bw, label, sub=sub, theme=th, icon=icon, icon_pos="top", icon_size=34, size=18, sub_size=14, h=bh, fill="hatch",
                dash="solid")
        b.place(cv, x, y)
        numbered(cv, x + 22, y + 2, i + 1, theme=th, d=32, size=18)
        boxes.append(b)
        x += bw + gap
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=2)
    # exits: where a request can leave the happy path (and which section explains it)
    ey = y + bh + 56
    exits = [
        (3, "HTTP 429", "retry-after-ms. Provisioned: immediate, nothing queued. Spillover can redirect", "red", "B"),
        (4, "Fail over", "To another model; needs at least 2 models in the subset", "blue", "E"),
        (6, "Tier outcomes", "Priority can fall back to Standard; Flex 429s when it has no capacity", "yellow", "C"),
        (8, "Rate-limit headers", "x-ratelimit-* on every call, retry-after-ms on a 429", "yellow", "B"),
    ]
    for idx, label, sub, th, letter in exits:
        src = boxes[idx]
        eb = Box(bw, label, sub=sub, theme=th, size=17, sub_size=14, h=134, fill="soft")
        eb.place(cv, src.x, ey)
        connect(cv, src, eb, dash="dashed", color=THEMES[th].stroke, a_side="bottom", b_side="top")
        numbered(cv, eb.right - 20, eb.y + 4, letter, theme=th, d=28, size=16)
    nd = nd_box(550, "Exact order of stages 2 to 8", sub="Learn documents each mechanism, not the sequence in which they run", h=134)
    nd.place(cv, 0, ey)
    return ey + 134


def section_b(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "B", "Which throttle applies? Standard TPM and RPM gate vs Provisioned leaky bucket",
               "The same deployment name can sit behind two very different admission controls. Both answer with HTTP 429, for different reasons.",
               "yellow")
    top = y
    with cv.panel(0, top, title="Standard (pay as you go): a TPM and RPM gate", theme="yellow", style="dotted", pad=26,
                  title_size=26, sub="Quota is TPM per subscription, per region, per model and per deployment type", sub_size=16,
                  w=1420) as p1:
        std_panel(cv, p1.ix, p1.iy)
    with cv.panel(1470, top, title="Provisioned (PTU): a leaky bucket on utilization", theme="yellow", style="dotted", pad=26,
                  title_size=26, sub="PTU quota (policy) and PTU capacity (real GPUs) are two different things", sub_size=16,
                  w=1480, min_h=p1.h) as p2:
        ptu_panel(cv, p2.ix, p2.iy)
    return spillover(cv, max(p1.bottom, p2.bottom) + 60)


def std_panel(cv: Canvas, x: float, y: float) -> None:
    th = THEMES["yellow"]
    red = THEMES["red"]
    # --- quota -> deployments
    cv.text(x, y, "Assign quota to deployments", size=19, color=th.deep)
    cv.text(x, y + 28, "Quota: 240,000 TPM for GPT-4o in East US (Learn's example)", size=15, color=INK)
    by = y + 66
    cv.poly([(x, by + 10), (x, by), (x + 660, by), (x + 660, by + 10)], kind="line", stroke=INK, sw=2)
    for i, name in enumerate(["Deployment A", "Deployment B"]):
        rx = x + i * 336
        cv.rect(rx, by + 22, 324, 62, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        cv.text(rx, by + 30, name, size=17, color=th.deep, align="center", w=324)
        cv.text(rx, by + 54, "120K TPM", size=17, color=INK, align="center", w=324)
    cv.text(x, by + 98, "The TPM you assign becomes that deployment's TPM limit; RPM is set proportionally. Up to 30 resources per "
                        "region, and more than one deployment of a model per resource is allowed.", size=15, color=INK, wrap=660)
    t = Table([("Model class", 360), ("1 capacity unit =", 310)], [
        ["Older chat models", "1,000 TPM + 6 RPM"],
        ["o1 and o1-preview", "6,000 TPM + 1 RPM"],
        ["o3 and o4-mini", "1,000 TPM + 1 RPM"],
        ["o3-mini, o1-mini and o3-pro", "10,000 TPM + 1 RPM"],
    ], w=670, theme="yellow", size=14, head_size=15, title="RPM follows TPM by a per-model ratio", title_size=19)
    t.place(cv, x + 698, y)
    # --- gate chain
    gy = y + 262
    req = Box(190, "Request", sub="to a Standard deployment", theme="gray", icon="users", icon_pos="top", icon_size=30, h=150,
              fill="hatch").place(cv, x, gy)
    rx0 = x + 240
    rpm = Slot(rx0, gy, 520, 318)
    cv.rect(rpm.x, rpm.y, rpm.w, rpm.h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    cv.text(rpm.x + 18, rpm.y + 12, "RPM gate", size=21, color=th.deep)
    cv.text(rpm.x + 18, rpm.y + 42, "Requests are judged over small windows, typically 1 s or 10 s. Spikes get a 429 even when the "
                                      "per-minute total is within the limit.", size=15, color=INK, wrap=486)
    base = rpm.y + 262
    vals = [6, 8, 9, 10, 7, 14, 9, 8]
    cx0 = rpm.x + 30
    for i, v in enumerate(vals):
        bx_ = cx0 + i * 50
        over = v > 10
        cv.rect(bx_, base - v * 10, 34, v * 10, stroke="#e03131" if over else th.stroke, fill="#ffc9c9" if over else "#ffec99",
                style="solid", sw=2, rough=0, round_=False)
        if over:
            cv.text(bx_ - 4, base - v * 10 - 24, "429", size=17, color="#e03131")
    cv.line((cx0 - 10, base), (cx0 + 8 * 50, base), stroke=INK, sw=2)
    cv.line((cx0 - 10, base - 100), (cx0 + 8 * 50 + 2, base - 100), stroke="#e03131", sw=2, dash="dashed")
    cv.text(cx0 + 8 * 50 + 6, base - 112, "limit", size=14, color="#e03131")
    cv.text(rpm.x + 18, base + 8, "Illustration of the documented example: 600 RPM = 10 requests per 1-second window.",
            size=14, color=MUTED, wrap=486)
    tpm = Box(290, "TPM gate", sub="Counts actual input and generated tokens, not the max output setting (current Learn page)",
              theme="yellow", size=21, sub_size=15, h=150, fill="hatch").place(cv, rpm.right + 50, gy)
    adm = Box(218, "Admitted", sub="Goes on to the cache lookup and inference", theme="blue", size=21, sub_size=15, h=150,
              fill="hatch").place(cv, tpm.right + 50, gy)
    r429 = Box(tpm.w + 50 + adm.w, "HTTP 429 + retry-after-ms",
               sub="Retry after the wait, back off with jitter. The SDK retries twice by default.", theme="red", size=20,
               sub_size=15, h=118, fill="hatch").place(cv, tpm.x, gy + 200)
    ya = gy + 75
    connect(cv, req, rpm, a_side="right", b_side="left", tb=75 / rpm.h)
    connect(cv, rpm, tpm, a_side="right", b_side="left", ta=75 / rpm.h)
    connect(cv, tpm, adm)
    connect(cv, tpm, r429, a_side="bottom", b_side="top", dash="dashed", color=red.stroke)
    connect(cv, rpm, r429, a_side="right", b_side="left", ta=(gy + 259 - rpm.y) / rpm.h, tb=0.5, dash="dashed", color=red.stroke)
    # --- three kinds of 429
    ky = gy + 318 + 44
    cv.text(x, ky, "Three different 429s on Standard", size=20, color=th.deep)
    cw = 436
    k1 = Card(cw, "1  Rate limit exceeded", [
        "Your TPM or RPM limit was hit",
        "Fix: raise or rebalance quota, spread requests, shorten prompts",
        "! Unsuccessful requests, including 400s for input length, still count toward the limit",
    ], theme="red", icon="quotas", src=[L_QUOTA])
    k2 = Card(cw, "2  System capacity throttling", [
        "The message says the service is temporarily unable to serve, or demand is high",
        "! Raising your quota will not help",
        "Fix: back off and retry",
    ], theme="red", icon="service-health", src=[L_QUOTA])
    k3 = Card(cw, "3  Temporary limit reduction", [
        "Shared Standard pools can lower a deployment's effective limit; it usually clears within hours",
        "Tell-tale: x-ratelimit-limit-tokens is below your configured TPM",
        "Fix: back off, spread traffic, ramp gradually, or move to PTU",
    ], theme="red", icon="alerts", src=[L_QUOTA])
    kb = row(cv, x, ky + 34, [k1, k2, k3], gap=30)[1]
    # --- headers + docs-disagree
    hy = kb + 28
    hc = Card(cw + 60, "Headers on every response", [
        "x-ratelimit-limit-requests and -tokens: the limits",
        "x-ratelimit-remaining-requests and -tokens: what is left",
        "x-ratelimit-reset-requests and -tokens: time until reset",
        "retry-after-ms: added on a 429",
    ], theme="yellow", icon="diagnostics", src=[L_QUOTA])
    hc.place(cv, x, hy)
    nn = Note(1368 - hc.w - 30, "The current quota page says rate-limit math uses actual input and generated tokens, and a higher max output "
                                "setting does not reserve tokens. Older Learn text and the Dev Proxy docs say the Standard check estimates "
                                "prompt + max_tokens. This canvas follows the current page for Standard. PTU does estimate with max_tokens "
                                "and then corrects (right).", kind="warn", title="Docs disagree: how does the TPM check count?",
              src=[L_QUOTA, L_PTU_OPS], min_h=hc.h)
    nn.place(cv, hc.right + 30, hy)


def ptu_panel(cv: Canvas, x: float, y: float) -> None:
    th = THEMES["yellow"]
    red = "#e03131"
    tx, tw_, ty, tht = x + 585, 250, y + 14, 320
    level = 0.64
    wh = tht * level
    sy_ = ty + tht - wh
    y100 = ty + 24
    cv.rect(tx + 5, sy_, tw_ - 10, wh - 3, stroke="transparent", fill=th.fill, style="hachure", sw=0, round_=False)
    cv.poly([(tx, ty - 8), (tx, ty + tht), (tx + tw_, ty + tht), (tx + tw_, ty - 8)], kind="line", stroke=th.stroke, sw=4)
    cv.poly([(tx + 5, sy_), (tx + tw_ * 0.25, sy_ - 7), (tx + tw_ * 0.5, sy_ + 2), (tx + tw_ * 0.75, sy_ - 6), (tx + tw_ - 5, sy_)],
            kind="line", stroke=th.stroke, sw=2, curved=True)
    cv.text(tx + 40, sy_ + 40, "utilization", size=18, color=th.deep)
    cv.text(tx + 40, sy_ + 64, "(illustrative level)", size=14, color=MUTED)
    cv.line((tx - 52, y100), (tx + tw_, y100), stroke=red, sw=2, dash="dashed")
    cv.text(tx - 112, y100 - 11, "100%", size=17, color=red)
    # (1) overflow, (2) inflow, (3) correction, (4) drain
    arrow(cv, [(tx + tw_ + 2, y100), (tx + tw_ + 90, y100)], color=red, sw=3, num=1, num_theme="red")
    arrow(cv, [(x + 548, ty + 70), (tx + 120, ty + 70)], color=INK, sw=3, num=2, num_theme="yellow")
    arrow(cv, [(tx + 190, sy_ - 42), (tx + 190, sy_ + 42)], color=INK, sw=2, start_head="arrow", end_head="arrow", num=3,
          num_theme="yellow", label_pos="left")
    arrow(cv, [(tx + tw_ / 2, ty + tht + 4), (tx + tw_ / 2, ty + tht + 66)], color=th.stroke, sw=3, num=4, num_theme="yellow")
    rcol = tx + tw_ + 108
    label_block(cv, rcol, y100 - 14, x + 1428 - rcol, "At 100%: immediate 429",
                "HTTP 429 comes back at once with retry-after-ms and retry-after headers. Nothing is queued, so accepted requests keep "
                "predictable latency. Bursts just over 100% may be admitted briefly.", red, num=1, theme="red")
    label_block(cv, x, ty + 36, 540, "Estimate on admission",
                "Cost = prompt tokens (minus cached tokens) + max_tokens. If max_tokens is unset the service guesses, which can lower "
                "concurrency. Set it close to the real generation size.", th.deep, num=2)
    label_block(cv, x, ty + 176, 540, "Correct when it finishes",
                "The actual cost is now known. If actual > estimate the difference is added to utilization; if less, it is subtracted.",
                th.deep, num=3)
    label_block(cv, rcol, ty + tht - 60, x + 1428 - rcol, "Continuous drain",
                "Utilization drains at a rate proportional to the PTUs deployed, so a bigger deployment drains faster.", th.deep, num=4)
    ny = ty + tht + 96
    n = Note(1428, "PTU utilization = PTUs consumed / PTUs deployed (metric: Provisioned-managed utilization V2). A 429 here is a "
                   "traffic-management signal, not a service error: redirect the request (spillover below) or retry after retry-after-ms.",
             kind="key", title="Reading the bucket", src=[L_PTU_OPS])
    n.place(cv, x, ny)
    cy = n.bottom + 26
    cw = 460
    c1 = Card(cw, "Quota is not capacity", [
        "PTU quota is a free policy limit per subscription, region and deployment type; Global, Data Zone and Regional are separate pools",
        "Capacity is the real PTUs per model version; allocated at deployment time and held for its life",
        "! Quota does not guarantee capacity: the deployment fails if the region lacks it",
        "Deleting or scaling down releases capacity with no guarantee you get it back",
    ], theme="yellow", icon="quotas", src=[L_PTU])
    c2 = Card(cw, "Sizing inputs", [
        "Request shape: RPM, input tokens, output tokens",
        "Output:input ratio: output tokens cost more capacity; for GPT-4.1 and later it equals the global standard price ratio",
        "Cache rate: cached tokens do not consume PTU capacity",
        "PTUs are model-independent; TPM per PTU and the minimum deployment size vary by model",
    ], theme="yellow", icon="metrics", src=[L_PTU])
    c3 = Card(cw, "Billing", [
        "Hourly $/PTU/hr from create to delete, whether or not requests arrive",
        "Azure Reservations: 1 month or 1 year, per deployment type; loosely coupled to deployments",
        "! Reservations do not guarantee capacity: create the deployment first, then buy the reservation",
    ], theme="yellow", icon="reservations", src=[L_PTU])
    row(cv, x, cy, [c1, c2, c3], gap=24)


def spillover(cv: Canvas, y: float) -> float:
    th = THEMES["yellow"]
    red = THEMES["red"]
    _, hb = section_header(cv, 0, y, "Spillover: when the PTU deployment cannot serve, the request retries on a pay-as-you-go deployment",
                           size=28, w=W)
    sy = hb + 40
    client = Box(250, "Client or agent", sub="may send x-ms-spillover-deployment", theme="gray", icon="users", icon_pos="top",
                 icon_size=30, h=130, fill="hatch").place(cv, 0, sy)
    ptu = Box(400, "Provisioned deployment (PTU)", sub="Tried first, always. This can add latency before any spill.", theme="yellow",
              size=20, sub_size=15, h=130, fill="hatch").place(cv, 340, sy)
    ok1 = Box(380, "200 served by PTU", sub="Only the hourly PTU cost applies", theme="blue", size=20, sub_size=15, h=130,
              fill="hatch").place(cv, 850, sy)
    std = Box(400, "Standard deployment", sub="Same Foundry resource, same model and version. Needs an active pay-go deployment.",
              theme="blue", size=20, sub_size=15, h=150, fill="hatch").place(cv, 340, sy + 270)
    ok2 = Box(380, "200 served by Standard", sub="Billed at input, cached and output token rates", theme="blue", size=20, sub_size=15,
              h=150, fill="hatch").place(cv, 850, sy + 270)
    connect(cv, client, ptu, num=1, num_theme="yellow")
    connect(cv, ptu, ok1, label="200", label_size=15)
    connect(cv, ptu, std, a_side="bottom", b_side="top", color=red.stroke, sw=3, num=2, num_theme="red")
    cv.text(ptu.cx + 40, sy + 160, "Any non-200 from the PTU deployment:", size=15, color=red.deep)
    cv.text(ptu.cx + 40, sy + 182, "429 (PTUs exhausted), 400 (long context: GPT-4.1 series PTU supports under 128K), 500 or 503",
            size=15, color=INK, wrap=420)
    connect(cv, std, ok2, label="200", label_size=15)
    cv.text(std.x, std.bottom + 14, "If Standard also fails, its status and body go back to the caller; the spill headers are still present.",
            size=14, color=MUTED, wrap=400)
    cx0 = 1330
    c1 = Card(520, "Response headers", [
        "x-ms-spillover-from-deployment: the PTU deployment name; present means it spilled",
        "x-ms-deployment-name: the deployment that served the request",
        "x-ms-spillover-error: the PTU response code that triggered it; present even if the spill fails",
    ], theme="yellow", icon="diagnostics", src=[L_SPILL])
    c2 = Card(510, "Enable it", [
        "Per deployment: set spilloverDeploymentName (ARM 2024-10-01) to a standard deployment in the same resource",
        "Per request: send the x-ms-spillover-deployment header; without it nothing spills",
        "If both are set, the deployment property wins",
        "Learn recommends it for all global and data zone provisioned deployments",
    ], theme="yellow", icon="gear", src=[L_SPILL])
    c3 = Card(510, "Observe it, know the limits", [
        "Split Azure OpenAI Requests by ModelDeploymentName, StatusCode and IsSpillover",
        "Spilled requests are not counted as 429s on the PTU deployment",
        "Azure OpenAI models only (not DeepSeek or Llama); works with Foundry Agent Service",
    ], theme="yellow", icon="monitor", src=[L_SPILL])
    hmax = max(c1.h, c2.h, c3.h)
    c1.place(cv, cx0, sy - 6, h=hmax)
    c2.place(cv, cx0 + 550, sy - 6, h=hmax)
    c3.place(cv, cx0 + 1090, sy - 6, h=hmax)
    return max(std.bottom + 70, c1.bottom)


# ====================================================================== small drawing helpers (continued)
class Slot(Rect2):
    """Placeholder rectangle so connectors can attach to custom-drawn shapes."""

    def __init__(self, x: float, y: float, w: float, h: float):
        self.x, self.y, self.w, self.h = x, y, w, h


def label_block(cv: Canvas, x: float, y: float, w: float, head: str, body: str, color: str, *, num=None,
                theme="yellow", head_size=17, body_size=15) -> float:
    """Numbered heading + wrapped body text; returns the bottom y."""
    cx, cw = x, w
    if num is not None:
        numbered(cv, x + 15, y + 14, num, theme=theme, d=30, size=17)
        cx, cw = x + 42, w - 42
    t = cv.text(cx, y, head, size=head_size, color=color, wrap=cw)
    b = cv.text(cx, t.bottom + 3, body, size=body_size, color=INK, wrap=cw)
    return b.bottom


def dot(cv: Canvas, cx: float, cy: float, theme="blue", hi=False) -> None:
    th = THEMES[theme]
    r = 13 if hi else 9
    cv.ellipse(cx - r, cy - r, 2 * r, 2 * r, stroke=th.stroke, fill=th.stroke if hi else th.fill, style="solid", sw=2, rough=0)


# ====================================================================== A: routing scope
def section_a(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "A", "Where is it processed? Global, Data Zone or Regional routing",
               "The deployment type decides where inference runs. Data at rest stays in the designated geography for every type.", "blue")
    top = y
    th = THEMES["blue"]
    bx, bw, bh, bgap = 250, 1200, 158, 22
    total_h = 3 * bh + 2 * bgap
    mid = top + total_h / 2
    client = Box(170, "Client or agent", sub="calls a deployment", theme="gray", icon="users", icon_pos="top", icon_size=34, h=150,
                 fill="hatch")
    client.place(cv, 0, mid - 75)
    bands = [
        ("Global", ["GlobalStandard", "GlobalProvisionedManaged", "GlobalBatch"],
         "Any Azure region: Azure's global infrastructure dynamically routes traffic to available datacenters"),
        ("Data Zone", ["DataZoneStandard", "DataZoneProvisionedManaged", "DataZoneBatch"],
         "Only inside the data zone you chose: US, EU (Azure EU Data Boundary) or APAC*"),
        ("Regional / geography", ["Standard", "ProvisionedManaged"],
         "Standard stays in the Azure geography (may move between regions inside it for operations). Regional Provisioned stays in the deployment's region."),
    ]
    for i, (name, codes, desc) in enumerate(bands):
        by = top + i * (bh + bgap)
        cv.rect(bx, by, bw, bh, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        cv.text(bx + 20, by + 14, name, size=26, color=th.deep)
        for j, c in enumerate(codes):
            cv.text(bx + 22, by + 54 + j * 22, c, size=14, color=INK, font=MONO)
        x0 = bx + 340
        cv.text(x0, by + 14, desc, size=15, color=INK, wrap=bw - 360)
        cy = by + 112
        if i == 0:
            for k in range(15):
                dot(cv, x0 + 10 + k * 58, cy, hi=(k == 8))
            cv.text(x0 + 10 + 8 * 58 - 60, cy + 20, "serving datacenter", size=13, color=th.deep)
        elif i == 1:
            for k, zone in enumerate(["US", "EU", "APAC*"]):
                zx = x0 + k * 290
                cv.rect(zx, by + 76, 262, 70, stroke=th.stroke, fill="transparent", sw=2, dash="dotted")
                cv.text(zx + 12, by + 80, zone, size=15, color=th.deep)
                for m in range(4):
                    dot(cv, zx + 32 + m * 62, by + 120, hi=(k == 0 and m == 2))
        else:
            cv.rect(x0, by + 76, 380, 70, stroke=th.stroke, fill="transparent", sw=2, dash="dotted")
            cv.text(x0 + 12, by + 80, "Azure geography", size=15, color=th.deep)
            for m in range(4):
                dot(cv, x0 + 40 + m * 90, by + 120, hi=(m == 1))
        # request arrow into the band
        by_mid = by + bh / 2
        arrow(cv, [(client.right + 6, mid), (bx - 40, mid), (bx - 40, by_mid), (bx - 6, by_mid)], sw=2,
              end_head="arrow", color=th.stroke)
    ly = top + total_h + 30
    n1 = Note(1450, "The PTU page says Data Zone Provisioned stays within 'US or EU'. The deployment-types page says 'US, EU or APAC'. "
                    "This canvas shows the broader list (*): check both pages for your model and region.",
              kind="warn", title="Docs disagree: which zones does Data Zone cover?", src=[L_PTU, L_DEPLOY])
    n1.place(cv, 0, ly)
    nd = nd_box(1450, "Global and Data Zone placement algorithm",
                sub="Learn says traffic is dynamically routed to available datacenters; how a datacenter is chosen is not documented", h=96)
    nd.place(cv, 0, n1.bottom + 24)
    left_bottom = nd.bottom

    # ---------------- right: deployment type table + cards
    rx = 1500
    t = Table([("Deployment type", 210), ("SKU code", 330), ("Inference processed", 560), ("Billing", 350)], [
        ["Global Standard", "GlobalStandard", "Any Azure region (dynamic routing to available datacenters)", "Pay per token"],
        ["Global Provisioned", "GlobalProvisionedManaged", "Any Azure region", "Hourly PTU"],
        ["Global Batch", "GlobalBatch", "Any Azure region", "50% discount, 24 h target"],
        ["Data Zone Standard", "DataZoneStandard", "Inside the data zone: US, EU (Azure EU Data Boundary, incl. EFTA) or APAC*", "Pay per token"],
        ["Data Zone Provisioned", "DataZoneProvisionedManaged", "Inside the data zone", "Hourly PTU"],
        ["Data Zone Batch", "DataZoneBatch", "Inside the data zone", "50% discount"],
        ["Standard", "Standard", "Inside the Azure geography (may move between regions in it for operations)", "Pay per token"],
        ["Regional Provisioned", "ProvisionedManaged", "Inside the geography / region", "Hourly PTU"],
        [("Developer", "yellow"), "DeveloperTier", "Any region", "Fine-tuned model evaluation only; 24 h lifetime, no SLA"],
    ], w=1450, theme="blue", size=14, head_size=15, first_col_theme="blue", title="Deployment types and where inference runs",
        title_size=22)
    t.place(cv, rx, top - 6)
    c1 = Card(710, "Rollout and guardrails", [
        "New models launch Global first, then Data Zone, then geography (no date guarantee)",
        "Not every model supports every type; Azure Policy can deny a SKU (deployments/sku.name)",
        "Data at rest stays in the designated geography for all types",
        "! Global and Data Zone Standard have no automatic cross-region failover guarantee: if the primary region has an interruption, traffic routed there is affected",
    ], theme="blue", icon="policy", src=[L_DEPLOY, ("High availability", learn("how-to/high-availability-resiliency"))])
    c2 = Card(710, "Instant access", [
        "Call a model by name with no deployment; West US 3 only during the preview",
        "Draws on a per-model global quota pool, separate from regional quota",
        "Default account RAI policy only: no per-model guardrails",
        "Pin a version with model-name-YYYY-MM-DD; if a deployment has the same name, the deployment wins",
    ], theme="blue", icon="openai", badge="preview", src=[L_INSTANT])
    r_bottom = row(cv, rx, t.bottom + 28, [c1, c2], gap=30)[1]
    return max(left_bottom, r_bottom)
