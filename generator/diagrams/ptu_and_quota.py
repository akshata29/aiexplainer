"""PTU and quota - granted rate limits (quota) versus reserved capacity (provisioned throughput units)."""
from __future__ import annotations

import math

from generator.xd import *

META = dict(
    id="ptu-and-quota", title="PTU and quota", section="2", group="Models", order=22,
    description="Quota (granted TPM/RPM pools, subscription-level since May 2026, Free and Tier 1-6) versus provisioned throughput (reserved PTUs): sizing, billing and reservations, 429s, spillover, operations and monitoring.",
    tags=["ptu", "quota", "provisioned-throughput", "spillover", "capacity"],
)

W = 3250            # canvas content width
COL, GAP = 500, 50  # 6-column grid
HDR = 92            # space under a section header
SEC = 64            # space between sections
Y_ = theme("yellow")
B_ = theme("blue")
RED = "#e03131"


def cx(i: int) -> float:
    """Left edge of grid column i."""
    return i * (COL + GAP)


def span(n: int) -> float:
    """Width of n grid columns."""
    return n * COL + (n - 1) * GAP


def lbl(cv, x, y, s, size=15, color=INK, align="left", w=None, wrap=None):
    return cv.text(x, y, s, size=size, color=color, align=align, w=w, wrap=wrap)


def _lh(size):
    return text_size("A", size)[1]


class StepCard(Rect2):
    """Hatched card whose body is a numbered list. steps: str or (heading, text)."""

    def __init__(self, w, title, steps, *, color="blue", icon=None, src=(), size=16, title_size=20, d=28,
                 fill="hatch", pad=16, gap=10):
        self.th = theme(color)
        self.color, self.w, self.icon, self.src = color, w, icon, list(src)
        self.size, self.title_size, self.d, self.fill, self.pad = size, title_size, d, fill, pad
        inner = (w - 2 * pad) * 0.965
        self.icon_off = 46 if icon else 0
        self.t_lines = wrap_text(title, inner - self.icon_off, title_size)
        y = pad + max(len(self.t_lines) * _lh(title_size), 36 if icon else 0) + 10
        tw = (w - 2 * pad - d - 12) * 0.965
        self.rows = []
        for st in steps:
            head, text = st if isinstance(st, tuple) else (None, st)
            hl = wrap_text(head, tw, size + 1) if head else []
            tl = wrap_text(text, tw, size) if text else []
            h = max(len(hl) * _lh(size + 1) + len(tl) * _lh(size), d)
            self.rows.append((y, hl, tl))
            y += h + gap
        y -= gap
        self.src_lines = []
        if self.src:
            y += 8
            for label, url in self.src:
                lines = wrap_text(f"Learn: {label}", inner, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * _lh(12) + 2
            y -= 2
        self.h = y + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        bg, fs = (th.fill, "hachure") if self.fill == "hatch" else (th.soft, "solid")
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=2)
            if self.icon:
                place_icon(cv, self.icon, x + self.pad, y + self.pad, 36)
            cv.text(x + self.pad + self.icon_off, y + self.pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            for i, (ry, hl, tl) in enumerate(self.rows, 1):
                numbered(cv, x + self.pad + self.d / 2, y + ry + self.d / 2, i, theme=self.color, d=self.d, size=16)
                tx, ty = x + self.pad + self.d + 12, y + ry
                if hl:
                    cv.text(tx, ty, "\n".join(hl), size=self.size + 1, color=th.deep)
                    ty += len(hl) * _lh(self.size + 1)
                if tl:
                    cv.text(tx, ty, "\n".join(tl), size=self.size, color=INK)
            for text, url, sy in self.src_lines:
                cv.text(x + self.pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"stepcard:{self.t_lines[0]}", x, y, self.w, H)
        return self


# ====================================================================== drawing helpers (illustrations)
def staircase(cv, x, y, tiers, values, *, bar_w=50, gap=8, th=Y_):
    """Bars growing left to right (ordinal steps, not to scale). Returns (right, bottom)."""
    n = len(tiers)
    heights = [10] + [14 + 30 * i for i in range(1, n)]
    base_y = y + 26 + max(heights)
    for i, (t, v, h) in enumerate(zip(tiers, values, heights)):
        bx = x + i * (bar_w + gap)
        cv.rect(bx, base_y - h, bar_w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2, round_=False)
        vw, _ = text_size(v, 14)
        lbl(cv, bx + (bar_w - vw) / 2, base_y - h - 22, v, size=14, color=th.deep)
        tw, _ = text_size(t, 15)
        lbl(cv, bx + (bar_w - tw) / 2, base_y + 6, t, size=15, color=INK)
    right = x + n * bar_w + (n - 1) * gap
    cv.line((x - 6, base_y), (right + 6, base_y), stroke=th.stroke, sw=3)
    return right, base_y + 28


def tank(cv, x, y, w, h, level, *, th=B_):
    """Open-top tank with hatched water at `level` (0..1). Returns the water-top y."""
    water_top = y + h * (1 - level)
    cv.rect(x + 3, water_top, w - 6, y + h - water_top - 3, stroke="transparent", fill=th.fill, style="hachure",
            sw=2, round_=False, rough=1)
    cv.poly([(x, y), (x, y + h), (x + w, y + h), (x + w, y)], kind="line", stroke=th.stroke, sw=4)
    pts = [(x + 3 + (w - 6) * i / 20, water_top + 4 * math.sin(i * math.pi / 2.5)) for i in range(21)]
    cv.poly(pts, kind="line", stroke=th.stroke, sw=2, curved=True)
    return water_top


def gauge(cv, gx, gy, r, pct, *, red_from=0.8):
    """Half-circle dial 0..100 %, needle at pct, last stretch in red."""
    def pt(frac, rad):
        a = math.pi * (1 - frac)
        return gx + rad * math.cos(a), gy - rad * math.sin(a)
    n = 24
    cv.poly([pt(i / n, r) for i in range(0, int(n * red_from) + 1)], kind="line", stroke=INK, sw=3, curved=True)
    cv.poly([pt(i / n, r) for i in range(int(n * red_from), n + 1)], kind="line", stroke=RED, sw=7, curved=True)
    for frac, txt in ((0.0, "0%"), (0.5, "50%"), (1.0, "100%")):
        cv.line(pt(frac, r - 10), pt(frac, r + 8), stroke=INK, sw=2)
        tx, ty = pt(frac, r + 26)
        tw, thh = text_size(txt, 14)
        lbl(cv, tx - tw / 2, ty - thh / 2, txt, size=14)
    nx, ny = pt(pct, r - 16)
    cv.line((gx, gy), (nx, ny), stroke=RED, sw=4)
    cv.ellipse(gx - 8, gy - 8, 16, 16, stroke=INK, fill=RED, style="solid", sw=2, rough=0)


# ====================================================================== glance strip
def glance_strip(cv, y):
    items = [
        ("yellow", "quotas", "Quota = a granted rate limit",
         "TPM with a proportional RPM on shared capacity. You pay per token and nothing is reserved."),
        ("blue", "reservations", "PTU = reserved capacity",
         "Fixed capacity held for you around the clock, billed per PTU per hour, used or not."),
        ("red", None, "PTU quota is not capacity",
         "Quota is only a ceiling. Capacity is checked at deploy time and can be missing."),
        ("yellow", "subscription", "Quota pools are per subscription",
         "Global Standard: one pool across all regions. Free Tier and Tier 1-6. Rollout began after May 7, 2026."),
        ("blue", None, "At 100% utilization: instant 429",
         "A provisioned deployment never queues. Retry after retry-after-ms, or spill over."),
        ("green", None, "Spillover to a standard deployment",
         "Same model and version in the same resource. Spilled requests carry x-ms-spillover-from-deployment."),
    ]
    boxes = [Box(COL, label, sub=sub, theme=th_name, icon=icon, icon_pos="left", icon_size=40, size=20, sub_size=16,
                 fill="soft", sw=2, pad=14) for th_name, icon, label, sub in items]
    return row(cv, 0, y, boxes, gap=GAP)[1]


# ====================================================================== S1 / the two lanes
def quota_lane(cv, x, y, w, min_h):
    with cv.panel(x, y, title="Quota: a granted rate limit",
                  sub="Permission to use shared capacity - Standard, Global Standard and Data Zone Standard deployments",
                  theme="yellow", style="solid", fill="soft", pad=26, title_size=30, sub_size=16, w=w, min_h=min_h) as p:
        ox, oy = p.ix, p.iy + 4
        lbl(cv, ox, oy, "1. Your tier sets the pool size", size=19, color=Y_.deep)
        right, bot = staircase(cv, ox + 8, oy + 40, ["Free", "T1", "T2", "T3", "T4", "T5", "T6"],
                               ["0", "80K", "315K", "1M", "2M", "10M", "15M"])
        lbl(cv, ox, bot + 2, "Example: Grok 4.7, Global Standard, TPM by tier. Steps are not to scale.", size=14, color=MUTED, wrap=400)
        px = ox + 520
        lbl(cv, px, oy, "2. One shared pool per model + version", size=19, color=Y_.deep)
        yy = oy + 40
        for b in (Box(430, "Global Standard pool", sub="one pool for every region in the subscription (Standard and Flex requests)",
                      theme="yellow", fill="solid", size=18, sub_size=14),
                  Box(430, "Data Zone Standard pool", sub="one pool per data zone, for example US or EU", theme="yellow",
                      fill="solid", size=18, sub_size=14),
                  Box(430, "Legacy scope", sub="models not yet onboarded: per region, per subscription", theme="gray",
                      fill="soft", dash="dashed", size=18, sub_size=14)):
            b.place(cv, px, yy)
            yy += b.h + 16
        dx = ox + 1050
        lbl(cv, dx, oy, "3. You assign TPM to deployments", size=19, color=Y_.deep)
        yy2 = oy + 40
        for b in (Box(470, "Deployment A", sub="x TPM, with a proportional RPM", theme="blue", icon="openai",
                      icon_pos="left", fill="solid", size=18, sub_size=14, icon_size=30),
                  Box(470, "Deployment B", sub="y TPM, with a proportional RPM", theme="blue", icon="openai",
                      icon_pos="left", fill="solid", size=18, sub_size=14, icon_size=30),
                  Box(470, "Unallocated", sub="pool - (x + y): still available to assign", theme="gray", fill="soft",
                      dash="dashed", size=18, sub_size=14)):
            b.place(cv, dx, yy2)
            yy2 += b.h + 16
        arrow(cv, [(right + 24, oy + 180), (px - 14, oy + 180)], end_head="arrow", sw=3, color=Y_.stroke,
              label="tier sets the limit", label_size=14, label_wrap=100, label_pos="above")
        arrow(cv, [(px + 430 + 14, oy + 180), (dx - 14, oy + 180)], end_head="arrow", sw=3, color=Y_.stroke,
              label="assign TPM", label_size=14, label_wrap=100, label_pos="above")
        by = max(yy, yy2, bot + 40) + 2
        lbl(cv, ox, by, "Other quota systems (details in section 4)", size=18, color=Y_.deep)
        ChipFlow(["Claude: RPM, ITPM, OTPM", "Batch: enqueued tokens", "Managed compute (preview): GPU quota",
                  "Instant access (preview): global pool", "Fireworks: 10M TPM pools", "Foundry shared quota: test endpoints only"],
                 960, theme="yellow", size=15, fill="soft").place(cv, ox, by + 34)
        Note(470, "Over TPM or RPM the deployment returns HTTP 429. Limits count actual input plus generated tokens, not max_tokens.",
             kind="gotcha", title="At the limit", size=15).place(cv, dx, by - 2)
        gy = by + 150
        lbl(cv, ox, gy, "Getting more quota", size=18, color=Y_.deep)
        steps = [Box(430, "Tier auto-upgrade", sub="consumption trend, payment history and Microsoft relationship", theme="yellow",
                     fill="soft", size=17, sub_size=14),
                 Box(430, "Rebalance", sub="move TPM between deployments on the Quota page", theme="yellow", fill="soft",
                     size=17, sub_size=14),
                 Box(430, "Request form", sub="reviewed individually. Approval adds quota but keeps your tier", theme="yellow",
                     fill="soft", size=17, sub_size=14)]
        row(cv, ox, gy + 32, steps, gap=70)
        for a, b in zip(steps, steps[1:]):
            connect(cv, a, b, color=Y_.stroke, sw=3, dash="dashed")
    return p


def ptu_lane(cv, x, y, w, min_h):
    with cv.panel(x, y, title="PTU: reserved capacity",
                  sub="Provisioned throughput units - fixed capacity held for your deployment, whether or not you send requests",
                  theme="blue", style="solid", fill="soft", pad=26, title_size=30, sub_size=16, w=w, min_h=min_h) as p:
        ox, oy = p.ix, p.iy + 4
        tx, ty, tw, th_ = ox + 330, oy + 100, 270, 290
        req = Box(200, "Requests", sub="each adds an estimated cost", theme="gray", icon="users", icon_pos="left",
                  icon_size=30, fill="solid", size=18, sub_size=14).place(cv, ox, oy + 6)
        wt = tank(cv, tx, ty, tw, th_, 0.68)
        lbl(cv, tx + 16, wt + 36, "PTUs in use", size=17, color=B_.deep)
        lbl(cv, tx + 16, wt + 60, "= PTUs consumed", size=14, color=MUTED)
        lbl(cv, tx, ty + th_ + 8, "Tank size = deployed PTUs", size=16, color=B_.deep, w=tw, align="center")
        cv.line((tx + 4, ty + 16), (tx + tw - 4, ty + 16), stroke=RED, sw=3, dash="dashed")
        lbl(cv, tx + tw + 12, ty + 4, "100%", size=16, color="#c92a2a")
        arrow(cv, [(ox + 206, oy + 6 + req.h / 2), (tx + tw / 2, oy + 6 + req.h / 2), (tx + tw / 2, ty + 70)],
              end_head="arrow", sw=3, color=INK)
        arrow(cv, [(tx + tw + 4, ty + th_ - 24), (tx + tw + 100, ty + th_ - 24)], end_head="arrow", sw=3, color=B_.stroke)
        lbl(cv, tx + tw + 8, ty + th_ - 18, "drains in proportion to deployed PTUs", size=14, color=B_.deep, wrap=170)
        v429 = Box(330, "At 100%: HTTP 429 now", sub="retry-after-ms and retry-after headers. No queueing.", theme="red",
                   fill="solid", size=18, sub_size=14).place(cv, tx + tw + 90, oy + 0)
        arrow(cv, [(tx + tw + 60, ty + 4), (tx + tw + 86, oy + v429.h / 2 + 4)], end_head="arrow", sw=2, color=RED, dash="dashed")
        gx, gy = tx + tw + 270, oy + 306
        gauge(cv, gx, gy, 100, 0.93)
        lbl(cv, gx - 170, gy + 28, "Provisioned-managed utilization V2", size=15, color=B_.deep, w=340, align="center")
        lbl(cv, gx - 170, gy + 50, "= PTUs consumed / PTUs deployed", size=14, color=MUTED, w=340, align="center")
        sx, sy, sw_, sh = ox + 1190, oy + 214, 300, 176
        tank(cv, sx, sy, sw_, sh, 0.35, th=Y_)
        lbl(cv, sx, sy + sh + 8, "Standard deployment", size=17, color=Y_.deep, w=sw_, align="center")
        lbl(cv, sx, sy + sh + 32, "same model + version, same resource", size=14, color=MUTED, w=sw_, align="center")
        lbl(cv, sx, sy + sh + 52, "pay per token, uses quota", size=14, color=Y_.deep, w=sw_, align="center")
        arrow(cv, [(tx + tw + 8, ty + 40), (sx + sw_ / 2, ty + 40), (sx + sw_ / 2, sy - 12)], end_head="arrow", sw=3,
              color=Y_.stroke, label="optional spillover", label_size=15, label_pos="above", label_t=0.6)
        yy = ty + th_ + 82
        lbl(cv, ox, yy, "Three provisioned deployment types, each with its own PTU quota pool", size=18, color=B_.deep)
        row(cv, ox, yy + 34, [
            Box(470, "Global Provisioned", sub="sku GlobalProvisionedManaged", theme="blue", fill="solid", size=18, sub_size=14),
            Box(470, "Data Zone Provisioned", sub="sku DataZoneProvisionedManaged", theme="blue", fill="solid", size=18, sub_size=14),
            Box(470, "Regional Provisioned", sub="sku ProvisionedManaged", theme="blue", fill="solid", size=18, sub_size=14),
        ], gap=40)
    return p


def versus_block(cv, y):
    def q(t):
        return {"text": t, "theme": "yellow"}

    def pp(t):
        return {"text": t, "theme": "blue"}

    rows = [
        ["What you get", q("A granted rate limit (TPM, with a proportional RPM) on shared Azure capacity. Nothing is reserved."),
         pp("Fixed processing capacity held exclusively for your deployment, whether or not requests are being made.")],
        ["Unit", q("TPM per subscription, model and deployment type. 1 capacity unit = 1,000 TPM and a model-specific RPM."),
         pp("PTU: model-independent, region-specific. TPM per PTU varies by model; each model has a minimum PTU deployment.")],
        ["Billing", q("Pay per token (Standard, Global Standard, Data Zone Standard). Priority bills at a priority rate."),
         pp("Per PTU per hour, or an Azure Reservation (1 month or 1 year), regardless of the tokens you send.")],
        ["Latency", q("Standard: no latency SLA. Above a monthly token volume per model, latency can vary more (usage tiers)."),
         pp("Defined latency target per model: p50 request latency per 5 minutes, for example 99% > 50 tokens/s.")],
        ["At the limit", q("HTTP 429: rate limit exceeded, system capacity throttling, or a temporary rate-limit adjustment."),
         pp("HTTP 429 right away at 100% utilization, with retry-after-ms. No queueing, so accepted calls stay predictable.")],
        ["Getting more", q("Tier auto-upgrade, moving TPM between deployments (up to 15 minutes to apply), or the request form."),
         pp("Request PTU quota (can take several days), then pass the capacity check at deploy time.")],
        ["Best for", q("Dev and test, low volume, highly variable traffic."),
         pp("Predictable, latency-sensitive, production-scale and real-time traffic.")],
    ]
    t = Table([("Dimension", 170), "Quota - granted rate limit (pay-per-token deployments)", "PTU - reserved capacity (provisioned deployments)"],
              rows, w=span(4), theme="gray", size=16, head_size=18, first_col_theme="gray", title="Quota versus PTU at a glance",
              title_size=24)
    t.place(cv, 0, y)
    ut = Note(span(4), "Usage tiers (Standard, Global Standard and Data Zone Standard only - not Batch or PTU): above a per-model monthly token volume across your whole tenant, latency can become more than 2x worse. It is not a hard cap. Remedy: a quota increase, or move steady volume to PTU.",
              kind="tip", title="Why steady, high-volume workloads graduate to PTU", size=16,
              src=[("Azure OpenAI quotas and limits", learn("openai/quotas-limits"))])
    ut.place(cv, 0, t.bottom + 26)

    rx = cx(4)
    t4 = Table(["Option", "Billing", "Latency target"], [
        [("Standard", "yellow"), "Pay per token", "None (no latency SLA)"],
        [("Priority", "yellow"), "Pay per token, priority rate", "Defined per model"],
        [("Provisioned (PTU)", "blue"), "Per PTU per hour, or a reservation", "Defined per model"],
        [("Batch", "yellow"), "Discounted per token", "None (no latency SLA)"],
    ], w=span(2), theme="gray", size=16, head_size=17, title="Four ways to pay for tokens", title_size=22)
    t4.place(cv, rx, y)
    c = Card(span(2), "PTU quota is not capacity", [
        "# PTU quota",
        "The maximum PTUs you may deploy per subscription, region and deployment type. A policy limit that costs nothing",
        "# Capacity",
        "PTUs actually available for a model version. Allocated at deploy time and held for the deployment's life",
        "! A deployment fails if the region lacks capacity. Capacity changes through the day, and capacity you release by scaling down or deleting may not come back",
    ], theme="red", icon="quotas", src=[("PTU concepts", learn("openai/concepts/provisioned-throughput"))])
    c.place(cv, rx, t4.bottom + 26)
    return max(ut.bottom, c.bottom)


# ====================================================================== S2 / request path with spillover
def request_path(cv, y):
    with cv.panel(0, y, title="A request hitting a PTU deployment, with optional spillover",
                  sub="What the client observes depends on utilization and on whether spillover is configured",
                  theme="blue", style="dotted", pad=30, title_size=26, sub_size=16, w=span(4)) as p:
        ox, oy = p.ix, p.iy + 56
        vA, vB, vC = oy + 70, oy + 360, oy + 590
        client = Box(240, "Client app", sub="OpenAI SDK, model = the deployment name", theme="gray", icon="app", icon_pos="left",
                     icon_size=30, h=110, size=19, sub_size=14).place(cv, ox, vA - 55)
        ptu = Box(330, "PTU deployment", sub="Global, Data Zone or Regional Provisioned", theme="blue", icon="openai",
                  icon_pos="left", icon_size=30, h=110, size=19, sub_size=14).place(cv, ox + 350, vA - 55)
        d1 = Box(340, "Utilization at 100%?", shape="diamond", theme="blue", h=200, size=18, fill="soft").place(cv, ox + 800, vA - 100)
        ok = Box(360, "Served on reserved PTUs", sub="no queueing: accepted calls keep predictable latency", theme="blue", h=110,
                 size=18, sub_size=14).place(cv, ox + 1280, vA - 55)
        r200 = Box(300, "200 response", sub="served by the PTU deployment", theme="green", h=110, size=19, sub_size=14).place(
            cv, ox + 1790, vA - 55)
        d2 = Box(340, "Spillover configured?", shape="diamond", theme="yellow", h=200, size=18, fill="soft").place(
            cv, ox + 800, vB - 100)
        std = Box(360, "Standard deployment", sub="same model + version, same resource. Billed per token, uses quota",
                  theme="yellow", h=130, size=19, sub_size=14).place(cv, ox + 1280, vB - 65)
        rsp = Box(300, "200 + spillover headers", sub="x-ms-spillover-from-deployment, x-ms-deployment-name, x-ms-spillover-error",
                  theme="green", h=130, size=18, sub_size=13).place(cv, ox + 1790, vB - 65)
        e429 = Box(360, "HTTP 429 + retry-after-ms", sub="and retry-after: a traffic-management signal, not a service error",
                   theme="red", h=130, size=19, sub_size=14).place(cv, ox + 1280, vC - 65)
        dec = Box(300, "Client decides", sub="redirect to another deployment, or wait retry-after-ms and retry", theme="gray",
                  h=130, size=19, sub_size=14).place(cv, ox + 1790, vC - 65)
        lbl(cv, ox + 1790, vA - 55 - 38, "What the client sees", size=20, color=B_.deep)
        connect(cv, client, ptu, label="call", label_size=15, sw=3)
        connect(cv, ptu, d1, label="check", label_size=15, sw=3)
        connect(cv, d1, ok, label="no", label_size=16, sw=3)
        connect(cv, ok, r200, sw=3)
        connect(cv, d1, d2, a_side="bottom", b_side="top", label="yes", label_size=16, sw=3)
        connect(cv, d2, std, label="yes", label_size=16, sw=3, color=Y_.stroke)
        connect(cv, std, rsp, sw=3, color=Y_.stroke)
        arrow(cv, [(ox + 970, vB + 106), (ox + 970, vC), (ox + 1274, vC)], end_head="arrow", sw=3, label="no", label_size=16,
              label_t=0.2)
        connect(cv, e429, dec, sw=3, color=RED)
        Note(640, "A non-200 answer from the PTU deployment starts spillover: 429 (PTUs exhausted), 400 for long context (over 128K on the gpt-4.1 series), 500 or 503.",
             kind="info", title="What triggers spillover", size=15).place(cv, ox + 70, vB - 150)
        Note(640, "Per deployment: the portal option Traffic spillover or the property spilloverDeploymentName. Per request: the header x-ms-spillover-deployment. If both are set, the property wins.",
             kind="tip", title="How spillover is switched on", size=15).place(cv, ox + 70, vB + 10)
    return p


def flow_side(cv, x, y):
    PG = [("Operate provisioned deployments", learn("openai/how-to/provisioned-get-started"))]
    c1 = StepCard(span(2), "How utilization works: a leaky bucket", [
        ("Throttle at 100%", "At 100% utilization the service returns HTTP 429 immediately, with retry-after-ms and retry-after headers. Short bursts slightly above 100% may be allowed."),
        ("Estimate each request", "Cost = prompt tokens (minus cached tokens) + max_tokens. If max_tokens is unset the service guesses, which lowers concurrency: set it close to the real generation size."),
        ("Correct after completion", "The estimate is replaced by actual token counts, and the difference is added to or subtracted from utilization."),
        ("Drain continuously", "Utilization drains at a rate proportional to the PTUs deployed, so a bigger deployment drains faster."),
    ], color="blue", icon="metrics", src=PG)
    c1.place(cv, x, y)
    n1 = Note(span(2), "Accepted requests keep predictable latency because 429s return immediately instead of queueing. A provisioned 429 is a traffic-management signal, not a service error.",
              kind="key", title="No queue, no surprise latency", size=16)
    n1.place(cv, x, c1.bottom + 24)
    c2 = Card(span(2), "What to do on a 429", [
        "Redirect to another deployment or model: the lowest added latency. Spillover automates this",
        "Or wait the time in retry-after-ms and retry, if you need this deployment and can accept the delay",
        "OpenAI SDKs retry 429s by default (max_retries is 2) and honour retry-after; tune or disable it",
        "How many calls fit depends on call shape (prompt size, max_tokens): the calculator on the Quota page estimates it",
    ], theme="blue", src=PG)
    c2.place(cv, x, n1.bottom + 24)
    return c2.bottom


def spillover_row(cv, y):
    SP = [("Spillover for provisioned deployments", learn("openai/how-to/spillover-traffic-management"))]
    a = Card(span(2), "Turn spillover on", [
        "Prerequisite: a provisioned deployment and an active standard (pay-as-you-go) deployment of the same model and version, in the same Foundry resource",
        "Per deployment: the portal option Traffic spillover, or the property spilloverDeploymentName (at creation or added later)",
        "Per request: the header x-ms-spillover-deployment set to the standard deployment name",
        "If both are set the deployment property wins. For per-request control only, leave the property unset",
        "Role: Cognitive Services Contributor or higher on the Foundry resource",
        "Recommended for all Global and Data Zone provisioned deployments. Also works with Foundry Agent Service",
    ], theme="blue", icon="openai", src=SP)
    b = Card(span(2), "What spills, and what it costs", [
        "A non-200 answer from the PTU deployment: 429 (PTUs used up), 400 for long context, 500 or 503",
        "The service tries the PTU deployment first, so spilled requests can carry extra latency",
        "Supported for all Azure OpenAI models that support PTU. Not for Azure DeepSeek or Meta Llama",
        "Requests served by PTU cost only the hourly PTU charge. Spilled requests bill at the standard input, cached and output token rates",
        "If the standard deployment also fails, its status and body come back and the spillover headers are still present",
    ], theme="yellow", icon="cost-management", src=SP)
    t = Table(["Signal", "What it tells you"], [
        ["x-ms-spillover-from-deployment", "Name of the PTU deployment. Its presence marks a spilled request"],
        ["x-ms-deployment-name", "The deployment that served the request: the standard one when it spilled"],
        ["x-ms-spillover-error", "Status code from the PTU deployment that triggered it (429, 500, 503). Present even if the attempt fails"],
        ["Metric: Azure OpenAI Requests", "Split by ModelDeploymentName, StatusCode and IsSpillover. Spilled requests are not counted as 429s on the PTU deployment"],
    ], w=span(2), theme="blue", size=15, head_size=16, title="Spot a spilled request", title_size=22)
    return row(cv, 0, y, [a, b, t], gap=GAP)[1]


# ====================================================================== S3 / sizing
def sizing_section(cv, y):
    SZ = [("Determine PTU sizing for a workload", learn("openai/how-to/provisioned-throughput-sizing"))]
    s1 = Card(690, "1. Collect the inputs", [
        "Model and deployment type: global, data zone or regional",
        "Peak requests per minute (RPM)",
        "Average prompt tokens and average response tokens per call",
        "Cache rate: the share of prompt tokens served from the prompt cache",
        "The capacity calculator on the Foundry Quota page does the arithmetic and also estimates the maximum concurrent calls",
    ], theme="blue", src=SZ)
    s2 = Card(690, "2. Normalize to TPM", [
        "Input TPM = RPM x average prompt tokens",
        "Output TPM = RPM x average response tokens",
        "Normalized TPM = Input TPM x (1 - cache rate) + output-to-input ratio x Output TPM",
        "The ratio is the model's Global Standard price ratio: gpt-5 is 8, gpt-4.1 is 4, Llama-3.3-70B-Instruct is 4 (a non-standard case)",
    ], theme="blue", src=SZ)
    s3 = Card(690, "3. Divide, then round up", [
        "PTUs = Normalized TPM / input TPM per PTU (see the table below)",
        "Round up to the model's scale increment, and never below its minimum deployment size",
        "Most GPT models in the table start at 15 PTUs and grow in steps of 5 on Global and Data Zone",
        "Then benchmark before you commit: azure-openai-benchmark, at least 10 minutes of steady state",
    ], theme="blue", src=[("Operate provisioned deployments", learn("openai/how-to/provisioned-get-started"))])
    r_, b_ = row(cv, 0, y, [s1, s2, s3], gap=40)
    for a, c in zip((s1, s2), (s2, s3)):
        arrow(cv, [(a.right + 6, a.y + 36), (c.x - 6, c.y + 36)], end_head="arrow", sw=3, color=B_.stroke)

    ey = b_ + 44
    lbl(cv, 0, ey, "Worked example from the docs: gpt-5.2, Data Zone, 1,000 RPM, 200 prompt tokens, 20 response tokens, 3,400 input TPM per PTU, ratio 8",
        size=19, color=B_.deep)
    xs = [i * 442 for i in range(5)]
    r1 = ey + 38
    ex1 = [
        Box(380, "Input TPM", sub="1,000 RPM x 200 tokens = 200,000", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "Output TPM", sub="1,000 RPM x 20 tokens = 20,000", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "Normalized TPM", sub="200,000 + 8 x 20,000 = 360,000", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "Divide", sub="360,000 / 3,400 TPM per PTU = 105.88", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "110 PTUs", sub="rounded up to the increment of 5", theme="green", fill="solid", h=96, size=22, sub_size=15),
    ]
    for b, x in zip(ex1, xs):
        b.place(cv, x, r1)
    for a, c in zip(ex1, ex1[1:]):
        connect(cv, a, c, sw=3)
    r2 = r1 + 96 + 36
    lbl(cv, 0, r2 + 8, "Same workload with 50% of prompt tokens served from cache:", size=17, color=MUTED, wrap=380)
    ex2 = [
        Box(380, "Normalized TPM", sub="200,000 x 0.5 + 8 x 20,000 = 260,000", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "Divide", sub="260,000 / 3,400 TPM per PTU = 76.47", theme="blue", fill="soft", h=96, size=19, sub_size=15),
        Box(380, "80 PTUs", sub="rounded up to the increment of 5", theme="green", fill="solid", h=96, size=22, sub_size=15),
    ]
    for b, x in zip(ex2, xs[2:]):
        b.place(cv, x, r2)
    for a, c in zip(ex2, ex2[1:]):
        connect(cv, a, c, sw=3)
    left_bottom = r2 + 96

    rx = cx(4)
    g = Card(span(2), "GPT-6 models count normalized tokens", [
        "Applies to GPT-6 Astra, GPT-6 Sol and GPT-6.1 Sol",
        "Short-context input = 1.0, output = 5.0",
        "Cached input = 0.1 (GPT-6.1 Sol: 0.05), cache write = 1.25",
        "Long-context input = 2.0, output = 7.5 (the docs list more rates)",
        "So cached tokens still consume PTU capacity, unlike classic accounting where cached tokens are deducted 100% from utilization",
    ], theme="blue", icon="foundry", src=SZ)
    n1 = Note(span(2), "gpt-5.4 and the gpt-4.1 series provisioned deployments do not support prompts over 128K tokens. The call fails with HTTP 400, or spills over if spillover is configured.",
              kind="warn", title="Long context", size=15)
    n2 = Note(span(2), "Normalized tokens per request = text in + image in x 1.6 + image out x 3.75 x 1.6. PTUs = normalized TPM / 1,200. Azure Monitor reports no latency metrics for image models, and request counts show twice.",
              kind="info", title="Image models", size=15)
    _, right_bottom = col(cv, rx, y, [g, n1, n2], gap=22)

    # per-model parameters (left) + Fireworks (right)
    ty = max(left_bottom, right_bottom) + 56
    mt = Table(
        ["Model (version)", "Global / Data Zone: min - increment", "Regional: min - increment", "Input TPM per PTU",
         "Output : input ratio", "Latency target"],
        [
            ["gpt-6.1-sol (2026-09-29)", "15 - 5", "50 - 50", "3,000", "normalized tokens", "99% > 50 TPS"],
            ["gpt-6-sol (2026-09-22)", "15 - 5", "50 - 50", "3,000", "normalized tokens", "99% > 80 TPS"],
            ["gpt-6-astra (2026-09-03)", "15 - 5", "50 - 50", "600", "normalized tokens", "99% > 40 TPS"],
            ["gpt-5.6-luna / -terra / -sol", "15 - 5", "50 - 50", "30,000 / 3,000 / 1,200", "6", "> 100 / > 70 / > 80 TPS"],
            ["gpt-5.5", "15 - 5", "50 - 50", "1,200", "6", "> 50 TPS"],
            ["gpt-5.4 / gpt-5.4-mini", "15 - 5", "50 - 50 / 25 - 25", "2,400 / 7,900", "6", "> 50 / > 100 TPS"],
            ["gpt-5.3-codex, gpt-5.2, gpt-5.2-codex", "15 - 5", "50 - 50", "3,400", "8", "> 50 TPS"],
            ["gpt-5.1, gpt-5.1-codex, gpt-5", "15 - 5", "50 - 50", "4,750", "8", "> 50 TPS"],
            ["gpt-5-mini", "15 - 5", "25 - 25", "23,750", "8", "> 80 TPS"],
            ["gpt-4.1 / -mini / -nano", "15 - 5", "50 / 25 / 25", "3,000 / 14,900 / 59,400", "4", "> 80 / > 90 / > 100 TPS"],
            ["o3 / o4-mini", "15 - 5", "50 / 25", "3,000 / 5,400", "4", "> 80 / > 90 TPS"],
            ["gpt-4o / gpt-4o-mini / o3-mini / o1", "15 - 5", "50 / 25 / 25 / 25 (o1: increment 50)", "2,500 / 37,000 / 2,500 / 230", "4", "> 25 / > 33 / > 66 / > 25 TPS"],
            ["gpt-image-2 / gpt-image-2.5-flare", "100 - 100", "100 - 100", "1,200 text in (750 image in)", "image out weight 3.75 x 1.6", "N/A"],
            ["Llama-3.3-70B-Instruct", "100 - 100", "not available", "8,450", "4", "> 50 TPS"],
        ], w=span(4), theme="blue", size=16, head_size=16, first_col_theme="blue", max_col=520,
        title="PTU sizing parameters by model (docs table, as of 2026-11-03)", title_size=22)
    mt.place(cv, 0, ty)
    lbl(cv, 0, mt.bottom + 8, "Latency target = p50 request latency per 5 minutes, written as '99% > N tokens per second' (TPS).",
        size=14, color=MUTED, wrap=span(4))
    lbl(cv, 0, mt.bottom + 32, "Learn: Determine PTU sizing for a workload", size=12, color=LINK,
        ).el["link"] = learn("openai/how-to/provisioned-throughput-sizing")

    ft = Table(["Fireworks model", "Min - increment", "Input TPM per PTU"], [
        ["FW-Kimi-K3", "5 - 1", "985 (Global only)"],
        ["FW-DeepSeek-V4.1-Flash", "5 - 1", "11,000 (Global only)"],
        ["FW-GLM-5.3", "5 - 1 Global, 320 - 160 Data Zone", "1,645 Global, 1,050 Data Zone"],
        ["FW-GPT-OSS-120B", "50 - 25", "10,800"],
        ["FW-DeepSeek-V4-Pro", "800 - 400", "100"],
        ["FW-Llama-v3.1-8B-Instruct", "50 - 25", "46,240"],
    ], w=span(2), theme="blue", size=15, head_size=16, first_col_theme="blue", title="Fireworks PTU examples (all Global, most also Data Zone US)",
        title_size=20)
    n3 = Note(span(2), "Latency target for every Fireworks PTU model is 99% > 50 TPS. A Fireworks PTU offering gets 12 months' notice before retirement (Fireworks pay-per-token: 15 days).",
              kind="info", size=15, src=[("Fireworks model catalog", learn("how-to/fireworks/fireworks-model-catalog"))])
    _, fb = col(cv, rx, ty, [ft, n3], gap=22)
    return max(mt.bottom + 56, fb)


# ====================================================================== S4 / quota in detail
def quota_detail(cv, y):
    QL = [("Foundry Models quotas and limits", learn("foundry-models/quotas-limits"))]
    OQ = [("Azure OpenAI quotas and limits", learn("openai/quotas-limits"))]
    MQ = [("Manage Azure OpenAI quota", learn("openai/how-to/quota"))]
    tt = Table(["Tier", "gpt-5.5", "gpt-5.6-sol, gpt-6-sol, gpt-6.1-sol", "Grok 4.7", "Microsoft-Decision-1"], [
        [("Free Tier", "yellow"), DASH, DASH, "0 / 0", DASH],
        [("Tier 1", "yellow"), "1,000 / 1M", "250 / 250K", "80 / 80K", "2,160 / 2.16M"],
        [("Tier 2", "yellow"), "2,000 / 2M", "1,000 / 1M", "315 / 315K", "4,500 / 4.5M"],
        [("Tier 3", "yellow"), "4,000 / 4M", "2,500 / 2.5M", "1,000 / 1M", "6,000 / 6M"],
        [("Tier 4", "yellow"), "7,000 / 7M", "7,000 / 7M", "2,000 / 2M", "9,000 / 9M"],
        [("Tier 5", "yellow"), "10,000 / 10M", "10,000 / 10M", "10,000 / 10M", "10,200 / 10.2M"],
        [("Tier 6", "yellow"), "15,000 / 15M", "15,000 / 15M", "15,000 / 15M", "15,000 / 15M"],
    ], w=span(4), theme="yellow", size=16, head_size=16, title="Quota tiers, examples: RPM / TPM per tier, Global Standard", title_size=22,
        align=["left", "center", "center", "center", "center"])
    tt.place(cv, 0, y)
    lbl(cv, 0, tt.bottom + 8,
        "A grey dash = no value listed. Data Zone Standard example: gpt-5.5 Tier 1 = 333 RPM / 333K TPM. Tier 0 tab examples: gpt-4.1-mini 200 / 200K, gpt-5-mini 500 / 500K, o4-mini 100 / 100K. 1 capacity unit = 1,000 TPM and 1 RPM for Grok 4.7.",
        size=14, color=MUTED, wrap=span(4))
    ht = Card(span(2), "How tiers work", [
        "Seven tiers: Free Tier and Tiers 1-6; Tier 6 has the highest quota",
        "The first tier reflects your usage and your Microsoft relationship (EA, MCA-E)",
        "Auto-upgrade follows consumption trend, payment history and offer, evaluated per subscription",
        "Some models and deployment types have offer-specific limits",
        "For GPT-5.5, GPT-5.6 and the GPT-6 family, Tier 5 and 6 have quota by default; other tiers must request it",
        "A quota increase adds quota but does not change your tier",
        "Opt out of auto-upgrade (preview): tierUpgradePolicy NoAutoUpgrade, PATCH on quotaTiers/default (api-version 2025-10-01-preview)",
        "Read the tier with GET on the same URL: currentTierName and tierUpgradePolicy (for example OnceUpgradeIsAvailable)",
    ], theme="yellow", icon="quotas", src=QL)
    ht.place(cv, cx(4), y)

    # three masonry columns
    sc = Card(span(2), "Subscription-level scope", [
        "Rolling out model by model: it started after May 7, 2026 and the docs say 'soon all models'",
        "Tracked per subscription, not per resource or region. Quota is never enforced at tenant level",
        "Global Standard: deployments of one model and version share a single pool across all regions (Standard and Flex requests)",
        "Data Zone Standard: one pool per data zone, for example US or EU",
        "Quota page, Scope column: Global or Data Zone = subscription-level; a region name = legacy per-region management",
        "Existing approved quota is retained and applies at subscription level, no action needed",
        "When an existing model is upgraded, its new limit = the greater of the tier limit and the total quota of its existing deployments",
    ], theme="yellow", icon="subscription", src=QL)
    r429 = Card(span(2), "Three kinds of 429", [
        "Rate limit exceeded: raise the deployment's TPM, rebalance, or request quota",
        "System capacity throttling: retry, and consider PTU",
        "Temporary rate-limit adjustment (shared-pool protection): x-ratelimit-limit-tokens sits below your TPM, usually clearing in hours",
        "Can happen below quota: HTTP 400 rejects count; RPM is judged in 1-10 second windows (600 RPM = 10 requests per second); enforcement is distributed",
        "Escalate sustained 429s below approved quota to support",
        "Headers: x-ratelimit-limit, -remaining and -reset for requests and tokens, plus retry-after-ms",
    ], theme="yellow", icon="alerts", src=MQ)
    us = Card(span(2), "Usage tiers and client timeouts", [
        "# Usage tiers (latency, not a cap)",
        "Standard, Global Standard, Data Zone Standard only. Above a monthly volume per model, latency can be over 2x worse: gpt-5 32B tokens, gpt-5-mini 160B, gpt-4.1 30B, gpt-4o 12B, gpt-5.1 86B, gpt-5.2 60B, gpt-5.4 50B, gpt-5.5 25B, gpt-5.6-sol 25B",
        "Counted per model across all deployments, subscriptions and regions of your tenant",
        "# Client timeouts: set them explicitly",
        "Reasoning models: up to 29 minutes. Non-reasoning: streaming up to 60 seconds, non-streaming up to 29 minutes",
    ], theme="yellow", icon="monitor", src=OQ)

    st = StepCard(span(2), "Assign TPM to deployments", [
        ("Open Manage > Quota", "Tabs: Token per minute, Provisioned throughput unit, Managed compute. Pick the subscription and the model."),
        ("Edit the allocation", "Details pane 'Affiliated deployments using shared quota', then the pencil. Available quota drops as you assign TPM (1 capacity unit = 1,000 TPM)."),
        ("Or automate it", "Deployments PUT with sku.capacity (10 = 10K TPM). az cognitiveservices account deployment create --sku-name Standard --sku-capacity 10 (CLI 2.51 or later), PowerShell, ARM, Bicep, Terraform via AzAPI."),
        ("Wait up to 15 minutes", "Changes propagate in up to 15 minutes. Example: 240,000 TPM of gpt-4o in East US = one 240K deployment, or 2 x 120K across resources."),
    ], color="yellow", icon="gear", src=[("Manage Foundry quota", learn("how-to/quota")), ("Automate quota and deployments", learn("openai/how-to/automate-quota-deployments"))])
    cl = Table(["Claude models", "Pay-as-you-go", "Enterprise and MCA-E", "Free trial"], [
        ["haiku-5-5, opus-5-5, opus-5, opus-4-8, 4-7, 4-6, 4-5, sonnet-5-5, sonnet-5", "40 / 40,000 / 8,000", "10,000 / 10M / 2M", "0"],
        ["opus-5-5-fast", "16 / 16,000 / 3,200", "4,000 / 4M / 800K", "0"],
        ["sonnet-4-6, sonnet-4-5, haiku-4-5", "80 / 80,000 / 16,000", "10,000 / 10M / 2M", "0"],
        ["fable-5, fable-5-1", "0 / 0 / 0", "4,000 / 4M / 800K", "0"],
    ], w=span(2), theme="yellow", size=15, head_size=16, first_col_theme="yellow", max_col=420,
        title="Claude defaults: RPM / ITPM / OTPM", title_size=22)
    cln = Note(span(2), "Subscription-level pools. Cache reads do not count toward ITPM (input after the last breakpoint and cache-creation tokens do). Free-trial subscriptions are unsupported.",
               kind="info", size=15, src=[("Claude quotas and limits", learn("foundry-models/concepts/claude-models-quotas-limits"))])
    ot = Table(["Other quota system", "How it works"], [
        ["Batch", "Enqueued-token quotas per model and subscription type"],
        ["Managed compute (preview)", "GPU quota per accelerator family and region (Manage > Quota > Managed compute), not VM quota"],
        ["Instant access (preview)", "A per-model global pool; Global Standard deployments reserve part of it"],
        ["Priority and Flex (preview)", "Share the Standard deployment quota. Flex 429s are not necessarily quota"],
        ["Fireworks", "Separate Global Standard and Data Zone Standard pools, default 10M TPM per region, subscription and pool"],
        ["Dynamic quota (preview)", "Lets a standard deployment exceed its TPM when capacity is spare; extra usage bills at normal rates. Documented only for Foundry (classic)"],
    ], w=span(2), theme="yellow", size=15, head_size=16, first_col_theme="yellow", title="Other quota systems", title_size=22)

    rq = Card(span(2), "Raise quota, and who can do what", [
        "Request form: aka.ms/oai/stuquotarequest, or Manage > Quota > Request quota. Covers sold-by-Azure, Azure OpenAI and Anthropic models",
        "Other partner models do not support increases. Requests are evaluated one by one, in order, and customers actively using their quota come first",
        "Roles: Cognitive Services Usages Reader (view, subscription scope); Owner or Contributor (request increases); Cognitive Services Contributor + Usages Reader (edit allocations)",
        "Read usage: Usages API, az cognitiveservices usage list -l eastus, Get-AzCognitiveServicesUsage. Read capacity: Model Capacities API",
        "Foundry shared quota: a temporary pool for test endpoints only (not production), usage-based billing, no ticket needed",
    ], theme="yellow", icon="users", src=MQ)
    la = Table(["Resource and deployment limits", "Value"], [
        ["Foundry resources per region per subscription", "100"],
        ["Projects per Foundry resource", "250"],
        ["Model deployments per Foundry resource", "32"],
        ["Azure OpenAI resources per region per subscription", "30"],
        ["Fine-tuned model deployments", "10"],
        ["Provisioned throughput units per deployment", "100,000"],
        ["Custom headers per request (more gives HTTP 431)", "10"],
    ], w=span(2), theme="yellow", size=15, head_size=16, title="Limits cheat sheet", title_size=22)
    lb = Table(["Request limits and defaults", "Value"], [
        ["Embeddings array / tokens per request", "2,048 inputs / 300,000"],
        ["Chat completions tools or functions", "128"],
        ["Message character limit", "1,048,576"],
        ["Images per request (gpt-4o, gpt-4.1)", "50"],
        ["Models not yet onboarded ('rest of models')", "400,000 TPM, 1,000 RPM, 300 concurrent"],
        ["gpt-oss-120b", "5M TPM, 5K RPM"],
        ["Flux.2-Pro (low default / medium / high)", "15 / 30 / 100 RPM"],
        ["GPT-Live concurrent sessions", "10 default; T1 25, T2 50, T3 200, T4 300, T5 500"],
    ], w=span(2), theme="yellow", size=15, head_size=16, title="Defaults and per-request limits", title_size=22)

    y2 = max(tt.bottom + 56, ht.bottom + 40)
    _, ba = col(cv, 0, y2, [sc, r429, us], gap=34)
    _, bb = col(cv, cx(2), y2, [st, cl, cln, ot], gap=30)
    _, bc = col(cv, cx(4), y2, [rq, la, lb], gap=34)
    return max(ba, bb, bc)


# ====================================================================== S5 / billing
def billing_section(cv, y):
    BL = [("PTU billing and cost management", learn("openai/concepts/provisioned-throughput-billing"))]
    h = Card(span(2), "Hourly: billed as long as it exists", [
        "Rate x PTUs deployed, per hour, regardless of tokens. Prorated: 15 minutes = 1/4 of an hour",
        "Starts when the deployment is created. Resizing adjusts billing immediately",
        "It cannot be paused: only deleting the deployment stops it",
        "Charges on a deleted resource continue until it is purged, so delete deployments first, then purge",
        "Good for benchmarking and events. Not for tracking traffic up and down: capacity risk, and reservations are cheaper",
        "Legacy commitment model: only customers onboarded before the August 2024 self-service update",
    ], theme="blue", icon="cost-management", src=BL)
    ex = Note(span(2), "3,000 normalized TPM per PTU x 60 x 24 x 30 = 129.6M normalized tokens per month. At the docs' example price of $260 per PTU per month that is about $2.01 per 1M tokens, against $2.00 pay-as-you-go at 100% utilization. A doc illustration for GPT-6 Sol, not a quote.",
              kind="quote", title="Doc example: reservation versus pay-as-you-go", size=15, src=BL)
    r = Card(span(2), "Azure Reservations: 1 month or 1 year", [
        "A discount on the PTU meter, not on deployments. Bought per deployment type: Global, Data Zone and Regional are not interchangeable",
        "A Global reservation is not tied to a region and is model-independent, so it can cover the sum (for example 50 + 100 + 200 = 350)",
        "Match rule: same type, same region (Data Zone and Regional) and a scope that includes the subscription or resource group",
        "Scopes: resource group, subscription, management group, billing account. Change scope without penalty. Overlapping is allowed",
        "No capacity guarantee: create deployments first, then buy. PTUs above the reservation bill hourly",
        "Cancel or exchange may incur fees; exchange across types is not supported. Deleting a deployment does not cancel the reservation",
        "Purchasing needs its own Azure role permissions",
    ], theme="blue", icon="reservations", src=BL)
    _, b1 = col(cv, 0, y, [h, ex], gap=30)
    r.place(cv, cx(2), y)
    with cv.panel(cx(4), y, title="Reservation coverage, doc example", sub="Global reservation of 500 PTUs, deployments of 300 + 300 PTUs",
                  theme="blue", style="dotted", pad=22, title_size=22, sub_size=15, w=span(2)) as p:
        ox, oy = p.ix, p.iy + 4
        scale = 1.5
        lbl(cv, ox, oy, "Reservation", size=16, color=B_.deep)
        cv.rect(ox, oy + 26, 500 * scale, 46, stroke=B_.stroke, fill=B_.fill, style="hachure", sw=2, round_=False)
        lbl(cv, ox + 8, oy + 36, "Global reservation: 500 PTUs", size=17, color=B_.deep)
        lbl(cv, ox, oy + 96, "Deployed", size=16, color=B_.deep)
        cv.rect(ox, oy + 122, 300 * scale, 46, stroke=B_.stroke, fill=B_.fill, style="solid", sw=2, round_=False)
        lbl(cv, ox + 8, oy + 132, "300 PTUs, first model", size=17, color=B_.deep)
        cv.rect(ox + 300 * scale, oy + 122, 200 * scale, 46, stroke=B_.stroke, fill=B_.fill, style="solid", sw=2, round_=False)
        lbl(cv, ox + 300 * scale + 8, oy + 132, "200 of 300 PTUs", size=17, color=B_.deep)
        cv.rect(ox + 500 * scale, oy + 122, 100 * scale, 46, stroke=Y_.stroke, fill=Y_.fill, style="hachure", sw=2, round_=False)
        lbl(cv, ox + 500 * scale + 6, oy + 132, "100 hourly", size=17, color=Y_.deep)
        lbl(cv, ox + 300 * scale + 20, oy + 176, "the new DeepSeek deployment: 300 PTUs", size=14, color=MUTED)
        cv.line((ox + 500 * scale, oy + 74), (ox + 500 * scale, oy + 120), stroke=INK, sw=2, dash="dashed")
        hbrace(cv, ox + 300 * scale + 4, ox + 600 * scale - 4, oy + 208, side="bottom", depth=14, color=B_.stroke)
        lbl(cv, ox, oy + 236,
            "500 covers the first 300 plus 200 of the new 300. The remaining 100 PTUs are billed at the hourly rate. A Global reservation is model-independent, so it can cover any model's Global Provisioned PTUs.",
            size=15, color=INK, wrap=span(2) - 60)
    return max(b1, r.bottom, p.bottom)


# ====================================================================== S6 / operating
def ops_section(cv, y):
    OP = [("Operate provisioned deployments", learn("openai/how-to/provisioned-get-started"))]
    steps = [
        ("blue", "Estimate", ["Capacity calculator or the formula", "Inputs: model, type, peak RPM, prompt and response tokens, cache rate"]),
        ("yellow", "Request quota", ["Manage > Quota > Provisioned throughput unit > Request Quota, or the form", "Approval can take several days; you get an email", "Quota is shared by all PTU deployments of a type in a region"]),
        ("yellow", "Check capacity", ["Portal deployment dialog lists alternative regions", "Or the Model Capacities API", "Quota does not guarantee capacity"]),
        ("blue", "Deploy", ["sku.name GlobalProvisionedManaged, DataZoneProvisionedManaged or ProvisionedManaged", "sku.capacity = PTUs", "Use the deployment name as the model"]),
        ("yellow", "Reserve", ["Only after the deployment works", "Match type, region (Data Zone, Regional) and scope"]),
        ("violet", "Benchmark", ["azure-openai-benchmark", "At least 10 minutes of steady state", "Test your own traffic shape and retry logic"]),
        ("violet", "Monitor", ["Provisioned-managed utilization V2, split by deployment", "Azure OpenAI Requests split by ModelDeploymentName, StatusCode, IsSpillover"]),
        ("blue", "Scale and spill over", ["Scale PTUs up or down in the portal or CLI, in increments", "Enable spillover for bursts", "Scale-down is a one-way door for capacity"]),
        ("gray", "Clean up", ["Delete the deployment: the only way to stop hourly billing", "Purge a deleted resource", "Reservations are not cancelled by deleting"]),
    ]
    cw, cgap = 330, 35
    line_y = y + 24
    cv.line((0, line_y), (W, line_y), stroke=INK, sw=3)
    cards = [Card(cw, title, bullets, theme=th_name, body_size=15, title_size=21) for th_name, title, bullets in steps]
    hmax = max(c.h for c in cards)
    for i, ((th_name, _, _), c) in enumerate(zip(steps, cards)):
        x = i * (cw + cgap)
        c.place(cv, x, y + 66, h=hmax)
        numbered(cv, x + cw / 2, line_y, i + 1, theme=th_name, d=40, size=22)
        cv.line((x + cw / 2, line_y + 20), (x + cw / 2, y + 66), stroke=INK, sw=2)
    y2 = y + 66 + hmax + 56
    mon = Card(span(2), "Monitoring a PTU deployment", [
        "Provisioned-managed utilization V2 in Azure Monitor: PTUs consumed / PTUs deployed in the period. Use Apply splitting to see each deployment",
        "Azure OpenAI Requests split by ModelDeploymentName, StatusCode and IsSpillover: what PTU served and what spilled",
        "Utilization near 100% with 429s: spill over, retry, or add PTUs in increments",
        "Image models: no latency metrics, and request counts are doubled (divide by 2)",
    ], theme="violet", icon="metrics", src=OP)
    ops = Card(span(2), "Roles and client settings", [
        "Create deployments with Azure Contributor or Cognitive Services Contributor on the subscription or resource group",
        "Inference code is the same as for any deployment type: pass the deployment name as the model",
        "Set max_tokens close to the real generation size to raise concurrency",
        "OpenAI SDKs retry 429s (max_retries default 2). Redirect to a standard deployment for the lowest added latency",
        "Check capacity before scaling up; capacity you release may not come back",
    ], theme="blue", icon="users", src=OP)
    reg = Card(span(2), "Where can I deploy it?", [
        "Region availability tables have three pivots: Standard, Provisioned and Batch",
        "Sections: Global Standard, Data Zone Standard, Standard (regional), Global, Data Zone and Regional Provisioned Managed, Global Batch, Data Zone Batch",
        "Each has four geography tabs: Americas, Europe, Asia Pacific, Middle East and Africa; one table for Azure OpenAI models and one for other models sold by Azure",
        "Partner tables: Claude on Global Standard, and Data Zone Standard (US only)",
    ], theme="gray", icon="regions", src=[("Region availability", learn("foundry-models/concepts/models-sold-directly-by-azure-region-availability"))])
    return row(cv, 0, y2, [mon, ops, reg], gap=GAP)[1]


# ====================================================================== S7 / gotchas
def gotchas(cv, y):
    notes = [
        ("gotcha", "Quota is not capacity", "You can hold PTU quota and still fail to deploy. Capacity is allocated at deploy time and held for the deployment's life."),
        ("gotcha", "PTUs bill while idle", "Billing covers deployed capacity even at zero traffic. No pause: only deleting stops it. Delete a resource without purging and charges continue."),
        ("warn", "Scale-down is a one-way door", "Released capacity may not be available again. Do not autoscale PTUs hourly: hourly billing suits benchmarks and events, reservations suit steady use."),
        ("warn", "Deploy first, then reserve", "Reservations are per deployment type and do not guarantee capacity. Deleting a deployment does not cancel its reservation."),
        ("gotcha", "429 arrives instantly", "A PTU deployment never queues. Design for spillover or a client retry. OpenAI SDKs retry 429s by default."),
        ("info", "Pools moved up a level", "Global Standard quota for a model is now shared across all regions of the subscription (after May 7, 2026). Legacy models keep per-region quota."),
        ("warn", "Priority and Flex share Standard quota", "Flex (preview) 429s are not necessarily quota."),
        ("warn", "Partner models rarely raise quota", "Most non-Anthropic partner models cannot get quota increases."),
        ("warn", "Claude needs a paid agreement", "Free-trial subscriptions get 0 Claude quota, and increases are never guaranteed."),
        ("info", "Quota is not a budget", "The docs say quota is not the recommended tool for controlling spend. Use Cost Management."),
        ("key", "Always benchmark", "The calculator gives an estimate. Run azure-openai-benchmark for at least 10 minutes with your own traffic shape."),
        ("preview", "Preview items", "Opting out of automatic tier upgrades (NoAutoUpgrade) is preview. Dynamic quota is preview and documented only for Foundry (classic)."),
    ]
    blocks = [Note(COL, text, kind=k, title=t, size=16) for k, t, text in notes]
    b1 = row(cv, 0, y, blocks[:6], gap=GAP)[1]
    b2 = row(cv, 0, b1 + 26, blocks[6:], gap=GAP)[1]
    dd = [
        Note(span(2), "The PTU concepts page says Data Zone covers 'US or EU'; the deployment types page lists US, EU and APAC zones.", kind="warn",
             title="Docs disagree: data zones", size=15),
        Note(span(2), "The quota tier tables list Tier 1-4 limits for gpt-5.5, gpt-5.6 and the GPT-6 family, while the model notes say only Tier 5 and 6 have quota by default. Trust the Quota page in your portal.", kind="warn",
             title="Docs disagree: tiers", size=15),
        Note(span(2), "The Global Batch page still recommends dynamic quota, but the dynamic-quota article exists only for Foundry (classic).", kind="warn",
             title="Docs disagree: dynamic quota", size=15),
    ]
    return row(cv, 0, b2 + 36, dd, gap=GAP)[1]


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "PTU and quota",
                                "Two ways to get model capacity - granted rate limits versus reserved throughput (as of 2026-11-03)",
                                icon="quotas", w=W)
    y = glance_strip(cv, bottom + 44) + 50

    section_header(cv, 0, y, "1. Two engines, side by side",
                   sub="Quota is permission to use shared capacity. PTU is capacity you reserve. Both end in an HTTP 429 when you hit the limit.",
                   size=32)
    y += HDR
    LH = 700
    ql = quota_lane(cv, 0, y, span(3), LH)
    pl = ptu_lane(cv, span(3) + GAP, y, span(3), LH)
    y = max(ql.bottom, pl.bottom) + 46
    y = versus_block(cv, y) + SEC

    section_header(cv, 0, y, "2. Utilization, 429 and spillover",
                   sub="A provisioned deployment fills like a leaky bucket. At 100% it answers 429 immediately; spillover can send the overflow to a standard deployment.",
                   size=32)
    y += HDR
    rp = request_path(cv, y)
    side_bottom = flow_side(cv, cx(4), y)
    y = max(rp.bottom, side_bottom) + 46
    y = spillover_row(cv, y) + SEC

    section_header(cv, 0, y, "3. Sizing a PTU deployment",
                   sub="Turn peak traffic into normalized tokens per minute, divide by what one PTU delivers for your model, round up - then benchmark.",
                   size=32)
    y += HDR
    y = sizing_section(cv, y) + SEC

    section_header(cv, 0, y, "4. Quota in detail",
                   sub="Tiers, subscription-level pools, assigning TPM to deployments, raising quota, 429 anatomy and the other quota systems.",
                   size=32)
    y += HDR
    y = quota_detail(cv, y) + SEC

    section_header(cv, 0, y, "5. Billing and reservations", sub="Hourly by default; an Azure Reservation discounts the PTU meter for steady workloads.", size=32)
    y += HDR
    y = billing_section(cv, y) + SEC

    section_header(cv, 0, y, "6. Operating in production", sub="From estimate to clean-up, with monitoring along the way.", size=32)
    y += HDR
    y = ops_section(cv, y) + SEC

    section_header(cv, 0, y, "Gotchas to remember", size=32)
    y += 64
    y = gotchas(cv, y) + 60

    sources(cv, 0, y, [
        ("PTU concepts", learn("openai/concepts/provisioned-throughput")),
        ("Determine PTU sizing for a workload", learn("openai/how-to/provisioned-throughput-sizing")),
        ("PTU billing and cost management", learn("openai/concepts/provisioned-throughput-billing")),
        ("Operate provisioned throughput deployments in production", learn("openai/how-to/provisioned-get-started")),
        ("Manage traffic with spillover for provisioned deployments", learn("openai/how-to/spillover-traffic-management")),
        ("Manage Foundry quota", learn("how-to/quota")),
        ("Manage Azure OpenAI quota", learn("openai/how-to/quota")),
        ("Automate quota and deployments", learn("openai/how-to/automate-quota-deployments")),
        ("Foundry Models quotas and limits", learn("foundry-models/quotas-limits")),
        ("Azure OpenAI quotas and limits", learn("openai/quotas-limits")),
        ("Claude quotas and limits", learn("foundry-models/concepts/claude-models-quotas-limits")),
        ("Region availability for models sold by Azure", learn("foundry-models/concepts/models-sold-directly-by-azure-region-availability")),
        ("Fireworks model catalog (PTU)", learn("how-to/fireworks/fireworks-model-catalog")),
        ("Dynamic quota (Foundry classic)", learn("openai/how-to/dynamic-quota", base="azure/foundry-classic")),
    ], w=W, cols=3)
