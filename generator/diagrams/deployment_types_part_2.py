"""Foundry deployment types, part 2 - the lanes in detail.

Part 1 (deployment-types) picks the lane. This sheet goes deep: Flex and Priority request-level tiers, Batch jobs and limits,
managed compute and LoRA adapters (preview), instant access (preview), partner serverless, model router, how model versions
move per deployment type, Azure Government, Azure Policy and how to create a deployment. No prices are drawn.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="deployment-types-part-2", title="Deployment types: the lanes in detail", section="2", group="Models", order=21.5,
    description="Part 2 of the deployment-types map: Flex and Priority request-level tiers, Batch jobs and limits, managed compute and LoRA adapters (preview), instant access (preview), partner serverless, model router, version upgrades per type, Azure Government, Azure Policy and how to create a deployment.",
    tags=["flex", "priority", "batch", "managed-compute", "instant-access", "azure-government", "lifecycle"],
)

W = 3080
COL, GUT = 480, 40
SEC = 72
LR = metrics.line_ratio()


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


def learn_line(cv, x, y, items, gap=34, size=12):
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * LR


class Sku(Rect2):
    """Card with an optional monospace code pill, bullets and chips (chips: (label, theme))."""

    def __init__(self, w, title, code=None, body=(), *, theme="blue", fill="hatch", dash="solid", chips=(), badge=None,
                 icon=None, title_size=21, body_size=15, pad=14, min_h=0, icon_size=34, code_size=14, src=(), chip_size=13,
                 subtitle=None):
        self.th = get_theme(theme)
        self.w, self.title, self.code, self.fill, self.dash = w, title, code, fill, dash
        self.title_size, self.body_size, self.pad, self.min_h = title_size, body_size, pad, min_h
        self.icon, self.icon_size, self.badge, self.code_size, self.chip_size = icon, icon_size, badge, code_size, chip_size
        inner = (w - 2 * pad) * 0.965
        self.bw = (metrics.line_width(STATUS.get(badge, ("gray", badge))[1], 13) + 18) if badge else 0
        self.icon_off = (icon_size + 10) if icon else 0
        t_w = inner - self.icon_off - ((self.bw + 8) if badge else 0)
        self.t_lines = metrics.wrap_text(title, t_w, title_size)
        y = pad + max(len(self.t_lines) * title_size * LR, icon_size if icon else 0)
        self.sub_lines = []
        if subtitle:
            self.sub_lines = metrics.wrap_text(subtitle, t_w, 14)
            y += 2 + len(self.sub_lines) * 14 * LR
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
            elif text.startswith("# "):
                kind, text = "head", text[2:]
            lines = metrics.wrap_text(text, inner - (0 if kind == "head" else 18), body_size + (1 if kind == "head" else 0))
            self.items.append((kind, y, lines))
            y += len(lines) * (body_size + (1 if kind == "head" else 0)) * LR + (7 if kind == "head" else 5)
        if self.items:
            y -= 5
        self.chip_rows = []
        if chips:
            y += 10
            cur, rw = [], 0.0
            for label, th_name in chips:
                cw = metrics.line_width(label, chip_size) + 20
                if cur and rw + cw > inner:
                    self.chip_rows.append((y, cur))
                    y += chip_size * LR + 12
                    cur, rw = [], 0.0
                cur.append((label, th_name, cw))
                rw += cw + 8
            self.chip_rows.append((y, cur))
            y += chip_size * LR + 8
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
            tt = cv.text(tx, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            if self.sub_lines:
                cv.text(tx, tt.bottom + 2, "\n".join(self.sub_lines), size=14, color=MUTED)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.bw, y + pad - 1, self.badge)
            if self.code_box:
                cy, cw, ch = self.code_box
                cv.rect(x + pad, y + cy, cw, ch, stroke=th.stroke, fill="#ffffff", style="solid", sw=1.5, rough=0)
                cv.text(x + pad + 9, y + cy + 4, self.code, size=self.code_size, color=INK, font=metrics.MONO)
            for kind, by, lines in self.items:
                ly = y + by
                if kind == "head":
                    cv.text(x + pad, ly, "\n".join(lines), size=self.body_size + 1, color=th.stroke)
                    continue
                color = {"bullet": INK, "warn": "#c92a2a", "good": "#2b8a3e"}[kind]
                cv.text(x + pad + 18, ly, "\n".join(lines), size=self.body_size, color=color)
                mc = {"bullet": th.stroke if th.name not in ("gray", "ink") else "#f08c00", "warn": "#e03131",
                      "good": "#2f9e44"}[kind]
                cv.ellipse(x + pad + 4, ly + self.body_size * LR / 2 - 4, 9, 9, stroke=mc, sw=2, rough=0)
            for cy, chips in self.chip_rows:
                cx = x + pad
                for label, th_name, cw in chips:
                    ct = get_theme(th_name)
                    cv.rect(cx, y + cy, cw, self.chip_size * LR + 6, stroke=ct.stroke, fill=ct.fill, style="solid", sw=1.5, rough=0)
                    cv.text(cx + 10, y + cy + 3, label, size=self.chip_size, color=ct.deep)
                    cx += cw + 8
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"sku:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


class CodeCard(Rect2):
    """Monospace snippet in a soft card (no syntax colouring: only documented text)."""

    def __init__(self, w, title, lines, *, theme="gray", size=14, pad=14, src=(), note=None):
        self.th = get_theme(theme)
        self.w, self.title, self.size, self.pad, self.src = w, title, size, pad, list(src)
        inner = (w - 2 * pad) * 0.965
        self.lines = []
        for ln in lines:
            if metrics.line_width(ln, size, metrics.MONO) <= inner:
                self.lines.append(ln)
            else:
                indent = ln[:len(ln) - len(ln.lstrip(" "))]
                parts = metrics.wrap_text(ln.strip(), inner - metrics.line_width(indent + "  ", size, metrics.MONO), size, metrics.MONO)
                self.lines.extend([indent + parts[0]] + ["  " + indent + p for p in parts[1:]])
        self.note_lines = metrics.wrap_text(note, inner, 14) if note else []
        lh = size * metrics.line_ratio(metrics.MONO)
        h = pad + 20 * LR + 8 + len(self.lines) * lh + 6
        if self.note_lines:
            h += 8 + len(self.note_lines) * 14 * LR
        self.src_lines = []
        if self.src:
            h += 8
            for label, url in self.src:
                self.src_lines.append((f"Learn: {label}", url, h))
                h += 12 * LR + 2
            h -= 2
        self.h = h + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        lh = self.size * metrics.line_ratio(metrics.MONO)
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
            cv.text(x + pad, y + pad, self.title, size=20, color=th.deep)
            ty = y + pad + 20 * LR + 8
            cv.text(x + pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            ty += len(self.lines) * lh + 14
            if self.note_lines:
                cv.text(x + pad, ty, "\n".join(self.note_lines), size=14, color=MUTED)
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"code:{self.title}", x, y, self.w, H)
        return self


def flow(cv, x, y, boxes, gap, *, labels=None, sw=2.5, dash="solid"):
    """Place boxes left to right and connect them with arrows (labels: optional list of strings per gap)."""
    placed, cx = [], x
    for b in boxes:
        b.place(cv, cx, y)
        placed.append(b)
        cx += b.w + gap
    hmax = max(b.h for b in placed)
    for i, (a, b) in enumerate(zip(placed, placed[1:])):
        lab = labels[i] if labels and i < len(labels) else None
        connect(cv, a, b, a_side="right", b_side="left", ta=0.5, tb=0.5, sw=sw, dash=dash, label=lab, label_size=14)
    return placed, y + hmax


# ---------------------------------------------------------------------------------------------- 1. Flex and Priority
def tiers(cv, y):
    y = sec(cv, y, "1  Flex and Priority: request-level tiers on Standard deployments",
            sub="Neither is a deployment type. Both ride on a Standard deployment and share its quota; the tier that served a request comes back in response.service_tier.") + 36
    PW, PH = 1720, 600
    with cv.panel(0, y, w=PW, h=PH, title="How a request picks its tier", theme="lime", style="dotted", pad=20, title_size=22):
        pass
    lx, lw, bh = 24, 560, 112
    y0 = y + 84
    ladder = [
        Box(lw, "1  Header x-ms-service-tier", sub="flex | priority | default (Standard) | auto (Priority). Wins when valid; an invalid value returns HTTP 400",
            theme="lime", h=bh, size=18, sub_size=14).place(cv, lx, y0),
        Box(lw, "2  Request body service_tier", sub="flex | priority | default | auto. auto, the default, follows the deployment setting",
            theme="lime", h=bh, size=18, sub_size=14).place(cv, lx, y0 + bh + 40),
        Box(lw, "3  Deployment setting", sub="Priority toggle: ARM properties.service_tier = priority | default (portal: Priority processing)",
            theme="lime", h=bh, size=18, sub_size=14).place(cv, lx, y0 + 2 * (bh + 40)),
    ]
    for a, b in zip(ladder, ladder[1:]):
        connect(cv, a, b, a_side="bottom", b_side="top", dash="dashed", label="if absent", label_size=14, sw=2)
    ymid = ladder[1].cy
    bx = lx + lw + 30
    brace(cv, bx, ladder[0].y, ladder[2].bottom, side="right", depth=22)
    dep = Box(360, "Standard deployment", sub="Global Standard (Flex and Priority) or Data Zone Standard, US (Priority)", theme="blue", h=170, size=20, sub_size=14,
              fill="hatch", icon="openai").place(cv, bx + 22 + 90, ymid - 85)
    arrow(cv, [(bx + 24, ymid), (dep.x - 6, ymid)], sw=2.5, label="chosen tier", label_size=14)
    lane_x, lane_w, lane_h, pitch = dep.right + 110, 500, 104, 154
    lane_y = ymid - lane_h / 2
    lanes = [
        Box(lane_w, "Flex lane (preview)", sub="50% off, preemptible capacity. HTTP 429 when busy: you retry with default", theme="lime", dash="dashed",
            h=lane_h, size=19, sub_size=14).place(cv, lane_x, lane_y - pitch),
        Box(lane_w, "Priority lane", sub="Lower, consistent latency with a target; pay-as-you-go", theme="lime", h=lane_h, size=19, sub_size=14).place(cv, lane_x, lane_y),
        Box(lane_w, "Standard lane", sub="Best-effort, pay per token (service_tier default)", theme="blue", h=lane_h, size=19, sub_size=14).place(cv, lane_x, lane_y + lane_h + 86),
    ]
    for ln in lanes:
        connect(cv, dep, ln, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, lanes[1], lanes[2], a_side="bottom", b_side="top", ta=0.78, tb=0.78, dash="dashed", color="#e03131", sw=2,
            label="re-routed to Standard: ramp limit, peak demand or long context (billed Standard)", label_size=14, label_wrap=330, label_pos="left")
    cv.text(lx, y + PH - 64, "Log response.service_tier: it names the tier that actually served the request.", size=16, color=MUTED, wrap=560)

    tx, tw = PW + 40, W - PW - 40
    t_opt = Table([("Option", 140), ("How you select it", 250), ("Latency and availability", 300), ("Cost model", 300), ("Best for", 330)], [
        [("Flex (preview)", "lime"), "Request service_tier = flex", "Variable latency; HTTP 429 when Flex capacity is unavailable", "50% off Standard token rates; cached-token discount also applies", "Evaluations, enrichment, offline analysis, delay-tolerant work"],
        [("Standard", "blue"), "service_tier = default, or the deployment's Standard tier", "Best-effort online processing", "Standard pay-per-token rate", "Development, testing and production with variable traffic"],
        [("Priority", "lime"), "Priority on the deployment, or service_tier = priority", "Lower, more consistent latency with a target for supported models", "Priority pay-per-token rate", "Latency-sensitive apps without a reserved-capacity commitment"],
        [("Batch", "cyan"), "Submit a batch job to a Batch deployment", "24-hour target, no real-time latency target", "Discounted batch rate", "Large offline jobs"],
        [("Provisioned", "yellow"), "Provisioned deployment plus PTUs", "Reserved capacity, predictable throughput and latency", "Hourly PTU billing or an Azure reservation", "High-volume, mission-critical production"],
    ], w=tw, theme="lime", size=14, head_size=15, title="Choose a processing option (the Flex page's own comparison)", title_size=20)
    t_opt.place(cv, tx, y)
    learn_line(cv, tx, t_opt.bottom + 8, src("flex"))
    n_hdr = Note(tw, "Flex and Standard requests go to the same Global Standard deployment, so Flex 429s are not necessarily quota: they can be preemptible capacity running short. "
                     "Flex and Priority both share the Standard deployment's quota.", kind="warn", title="Same deployment, shared quota", size=15)
    n_hdr.place(cv, tx, t_opt.bottom + 48)

    cy = y + PH + 44
    flex = Sku(SPAN(2), "Flex processing (preview)", None, [
        "Set service_tier = flex on a Responses or Chat Completions request; it runs on the same Global Standard deployment (no separate deployment)",
        "50% discount on input and output tokens, plus the cached-token discount; dedicated Flex meters appear in Cost Analysis",
        "Variable latency. HTTP 429 when preemptible Flex capacity is unavailable; a rejected request is not billed",
        "No automatic fallback: retry yourself with service_tier = default. Shares quota with the Global Standard deployment",
        "An unsupported model returns HTTP 400 invalid_request_error. No latency SLA and no service SLA",
        "Use a long client timeout (the docs example sets 900 s); errors to handle: 400, 408, 429, 5xx",
        "Monitor in Azure Monitor: Azure OpenAI Requests, filter ServiceTierRequest = flex",
        "# Supported models (all Global Standard, as of 2026-11-03)",
    ], theme="lime", dash="dashed", badge="preview", chips=[
        ("gpt-6.1-sol 2026-09-29", "lime"), ("gpt-6-sol 2026-09-22", "lime"), ("gpt-6-luna 2026-09-22", "lime"), ("gpt-6-astra 2026-09-03", "lime"),
        ("gpt-5.6-sol 2026-07-09", "lime"), ("gpt-5.6-luna 2026-07-09", "lime"), ("gpt-5.6-terra 2026-07-09", "lime")], src=src("flex"))
    prio = Sku(SPAN(2), "Priority processing", None, [
        "Pay-as-you-go lower latency with a target. Works on Global Standard and Data Zone Standard (US) only - not regional Standard or EU Data Zone",
        "Needs model versions 2025-12-01 or later; same quota as Standard",
        "Turn it on with the deployment toggle (portal: Priority processing; ARM properties.service_tier) and/or per request",
        "Deployment Standard + request priority = Priority. Deployment Priority + request default = Standard",
        "! Can be re-routed to Standard, billed at the Standard rate with service_tier = default, on: a ramp-rate limit (more than 50% tokens-per-minute increase in under 15 minutes), peak demand, or long context (over 128k prompt tokens on gpt-5.4 and gpt-4.1)",
        "Routinely hitting the ramp limit? Buy PTU instead. Monitor the ServiceTierRequest / ServiceTierResponse split",
    ], theme="lime", src=src("prio"))
    tt = Table([("Model", 300), ("Latency target, tokens/s", 340)], [
        ["gpt-6-sol", "80"], ["gpt-5.6-sol", "80"], ["gpt-5.6-terra", "70"], ["gpt-5.5", "50"], ["gpt-5.4-mini", "100"],
        ["gpt-5.4", "50"], ["gpt-5.2", "50"], ["gpt-5.1", "50"], ["gpt-4.1", "80"],
    ], w=700, theme="lime", size=15, head_size=15, title="Priority latency targets (docs: 99% > N tokens/second, p50 per 5 minutes)", title_size=18)
    rt = Table(["Deployment setting", "Request service_tier", "Served as"], [
        ["Standard", "priority", ("Priority", "lime")], ["Priority", "default", ("Standard", "blue")], ["Priority", "auto (the default)", ("Priority", "lime")],
    ], w=prio.w, theme="lime", size=15, head_size=15, title="Priority routing: deployment x request", title_size=18)
    flex.place(cv, 0, cy)
    prio.place(cv, flex.right + GUT, cy)
    rt.place(cv, prio.x, prio.bottom + 34)
    tt.place(cv, prio.right + GUT, cy)
    n_t = Note(700, "Only the models listed here have a published latency target in the docs read for this explainer (as of 2026-11-03); check the Priority page for additions.",
               kind="info", title="Targets are per model", size=15, src=src("prio"))
    n_t.place(cv, tt.x, tt.bottom + 26)
    bottom = max(flex.bottom, rt.bottom, n_t.bottom)
    return bottom + 20


# ---------------------------------------------------------------------------------------------- 2. Batch
def batch(cv, y):
    y = sec(cv, y, "2  Batch: Global Batch and Data Zone Batch",
            sub="Asynchronous JSONL jobs at 50% off Global Standard with a 24-hour target. Quota is enqueued tokens, not TPM. The portal shows the types as Global-Batch and Data Zone Batch.") + 40
    bw, gap = 680, 120
    steps = [
        Box(bw, "1  Upload the input", sub="JSONL file, purpose = batch; up to 100,000 requests and 200 MB per file", theme="cyan", h=150, size=20, sub_size=15, icon="file", icon_pos="top"),
        Box(bw, "2  Create the batch", sub="completion_window must be 24h; point it at a Batch deployment", theme="cyan", h=150, size=20, sub_size=15, icon="batch", icon_pos="top"),
        Box(bw, "3  Poll the status", sub="until the job reaches a final state; cancel any time, completed work is billed", theme="cyan", h=150, size=20, sub_size=15, icon="metrics", icon_pos="top"),
        Box(bw, "4  Download the results", sub="output_file_id for results, error_file_id for failed lines", theme="cyan", h=150, size=20, sub_size=15, icon="storage", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, steps, gap)
    cy = b + 28
    cv.text(0, cy, "Batch statuses:", size=17, color=get_theme("cyan").deep)
    sts = [("validating", "cyan"), ("in_progress", "cyan"), ("finalizing", "cyan"), ("completed", "green"), ("failed", "red"), ("expired", "red"),
           ("cancelling", "gray"), ("cancelled", "gray")]
    cx = 160
    for s, th in sts:
        c = Chip(s, theme=th, size=15)
        c.place(cv, cx, cy - 4)
        cx += c.w + 12
    cy += 56
    t_lim = Table([("Limit", 330), "Value"], [
        ["Input files per resource", "500 (no expiry) or 10,000 (with expiration)"],
        ["Input file size", "200 MB (1 GB with bring-your-own storage)"],
        ["Requests per input file", "100,000"],
        ["Output files", "Exempt from the input-file count limit"],
        ["Job records", "Kept up to 365 days after a final state"],
        ["Output and error files", "No default expiry; expires_after and output_expires_after accept 14 to 30 days"],
    ], w=SPAN(2) - 40, theme="cyan", size=15, head_size=16, title="Limits", title_size=20)
    t_q = Table([("Enqueued-token quota (examples)", 300), "Enterprise, MCA-E", "Default", "Credit card", "MSDN"], [
        ["Global Batch, gpt-5.5", "5B", "200M", "50M", "90K"],
        ["Global Batch, gpt-4.1-mini", "15B", "1B", "50M", "90K"],
        ["Data Zone Batch, gpt-5.5", "5B", "200M", "50M", "90K"],
    ], w=SPAN(2) + 60, theme="cyan", size=15, head_size=15, title="Quota is enqueued tokens (docs examples, as of 2026-11-03)", title_size=20)
    t_lim.place(cv, 0, cy)
    t_q.place(cv, t_lim.right + GUT, cy)
    nx = t_q.right + GUT
    n_q = Note(W - nx, "Enqueued tokens stay counted until the job reaches a final state. The docs tip is to enable dynamic quota on global batch deployments, but the dynamic-quota article exists only for Foundry (classic) - docs disagree. In some regions you can queue several jobs with exponential backoff.",
               kind="warn", title="Quota gotchas", size=15, src=src("batch"))
    n_q.place(cv, nx, cy)
    n_ns = Note(W - nx, "Not supported: Assistants integration, On Your Data and fine-tuned models. Content filters can be attached. The docs tables list gpt-5.4-mini, gpt-5.4, gpt-5.1, gpt-5, o3, o4-mini, the gpt-4.1 family, o3-mini and the gpt-4o family. A Batch deployment is never auto-upgraded to a new model version.",
                kind="info", title="What Batch does not do", size=15)
    n_ns.place(cv, nx, n_q.bottom + 22)
    bot = max(t_lim.bottom, t_q.bottom, n_ns.bottom)
    learn_line(cv, 0, bot + 8, src("batch", "types"))
    return bot + 30


# ---------------------------------------------------------------------------------------------- 3. managed compute + LoRA
def managed(cv, y):
    y = sec(cv, y, "3  Managed compute and LoRA adapters (preview)",
            sub="Dedicated GPUs for open-source and custom weights, in a Foundry project. Not a serverless type: the grid in part 1 does not apply.") + 40
    bw, gap = 520, 120
    chain = [
        Box(bw, "Model source", sub="Hugging Face collection in the azure-huggingface registry; weights pre-staged in Azure, no Hugging Face egress", theme="gray", h=180, size=19, sub_size=14, icon="hf", icon_pos="top"),
        Box(bw, "Deployment template", sub="Pins runtime, accelerator, count and context, e.g. qwen--qwen3-32b--40k-nvidia-a100 or ...--128k-nvidia-2xh100", theme="blue", h=180, size=19, sub_size=14, icon="cubes", icon_pos="top"),
        Box(bw, "Model instances", sub="The unit of scale: you set capacity. Accelerators: A100_80GB, H100_80GB, MI300_192GB", theme="blue", h=180, size=19, sub_size=14, icon="vm", icon_pos="top"),
        Box(bw, "Endpoint", sub="<endpoint>/managed-deployments/<name>/ and <endpoint>/openai/v1/ (404 if the runtime has no chat route, e.g. TEI)", theme="blue", h=180, size=19, sub_size=14, icon="api", icon_pos="top"),
        Box(bw, "Your app", sub="Entra bearer token (https://ai.azure.com/.default, Foundry User role) or the account key", theme="gray", h=180, size=19, sub_size=14, icon="app", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, chain, gap, labels=["pick", "scale", "serve", "call"])
    cy = b + 40
    c1 = Card(SPAN(2), "Billing and quota", [
        "Bill = accelerators per instance x instances x hours x the hourly rate; deleting the deployment stops billing immediately",
        "SKU GlobalManagedCompute: Global only; Data Zone and more regions are rolling out",
        "Quota is per accelerator family per region, requested in Manage > Quota > Managed compute > Request quota; about 15 minutes to propagate",
        "! Separate from Azure VM quota",
    ], theme="yellow", icon="quotas", badge="preview", src=src("mc", "mcdep"))
    c2 = Card(SPAN(2), "Runtimes and operations", [
        "Runtimes: vLLM, SGLang, TensorRT-LLM, NVIDIA NIM, TEI, llama.cpp, hf-serve - Microsoft builds, scans, signs and patches them; CVE patches apply automatically",
        "Metrics: request count by status code and latency p50, p90, p99; chat models add input and output tokens, time to first token and inter-token time",
        "Provisioning takes 10-15 minutes (investigate beyond 20)",
        "Create with Cognitive Services Contributor, Foundry Owner or Foundry Account Owner; read with Foundry User or Project Manager",
    ], theme="blue", icon="metrics", src=src("mcdep"))
    c3 = Card(SPAN(2), "Limitations while in preview", [
        "! No built-in content filtering",
        "Global scope only; no SLA",
        "Pricing and reserved-capacity options are still evolving - check the docs before publishing a deck",
        "Models come from the Hugging Face collection; weights are pre-staged in Azure",
        "versionUpgradeOption is exposed too (OnceNewDefaultVersionAvailable)",
    ], theme="red", icon="preview-features", src=src("mc"))
    _, b2 = row(cv, 0, cy, [c1, c2, c3], gap=GUT)
    ay = b2 + 44
    with cv.panel(0, ay, title="Adapter (LoRA) deployments (preview): many adapters, one base model", theme="violet", style="dotted", pad=22, title_size=22,
                  w=W) as ap:
        aw, ag = 700, 170
        ax = ap.ix
        ay2 = ap.iy + 8
        job = Box(aw, "Foundry fine-tuning job", sub="its output is a LoRA adapter; you cannot yet import your own", theme="violet", h=160, size=19, sub_size=14, icon="ml", icon_pos="top").place(cv, ax, ay2)
        adp = Box(aw, "Adapter deployment", sub="own deployment name, no extra compute and no separate price; adapter version is pinned (create a new deployment to change it)",
                  theme="violet", h=160, size=19, sub_size=14, dash="dashed", icon="cubes", icon_pos="top").place(cv, ax + aw + ag, ay2)
        tgt = Box(aw, "Target deployment", sub="compatible base model plus a LoRA-enabled template; several adapters can share it (multi-LoRA); scaling it scales all adapters",
                  theme="blue", h=160, size=19, sub_size=14, icon="vm", icon_pos="top").place(cv, ax + 2 * (aw + ag), ay2)
        connect(cv, job, adp, a_side="right", b_side="left", sw=2.5, label="register", label_size=14)
        connect(cv, adp, tgt, a_side="right", b_side="left", sw=2.5, label="attached to", label_size=14)
        cli = Chip("Client: POST /openai/v1/chat/completions with model = the adapter deployment name", theme="gray", size=16)
        cli.place(cv, adp.cx - cli.w / 2, ay2 + 160 + 44)
        connect(cv, cli, adp, a_side="top", b_side="bottom", dash="dashed", sw=2)
    learn_line(cv, 0, ap.bottom + 8, src("adapter", "mc"))
    return ap.bottom + 30


# ---------------------------------------------------------------------------------------------- 4. instant access
def instant(cv, y):
    y = sec(cv, y, "4  Instant access (preview): call a model by name, nothing to deploy",
            sub="Not a deployment option and not a deployment type: the quickest way to try a model today.") + 40
    bw, gap = 650, 160
    chain = [
        Box(bw, "Your app", sub='client.responses.create(model="gpt-5-mini", ...) - a model name, not a deployment name', theme="gray", h=170, size=20, sub_size=15, icon="app", icon_pos="top"),
        Box(bw, "Project endpoint", sub="https://<resource>.services.ai.azure.com/api/projects/<project>/openai/v1/responses - the project must be in West US 3", theme="blue", h=170, size=20, sub_size=15,
            icon="foundry", icon_pos="top", dash="dashed"),
        Box(bw, "Global quota pool", sub="One pool per model, shared automatically; Global Standard deployments reserve part of it; regional and provisioned types are separate", theme="yellow", h=170, size=20, sub_size=15, icon="quotas", icon_pos="top"),
        Box(bw, "Model", sub="The latest evergreen version by default; pin one with a dated name such as model-name-2025-04-01", theme="blue", h=170, size=20, sub_size=15, icon="openai", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, chain, gap, labels=["Foundry User", "draws from", "serves"])
    cy = b + 40
    c1 = Card(SPAN(2), "Find supported models", [
        "Model catalog: Deployment options = Instant",
        "REST: az rest on locations/westus3/models, filtered on capabilities.instant",
        "Names the docs use: chat-gpt-latest, gpt-5.6-sol, gpt-5.5, gpt-5-mini, gpt-5.3-codex",
        "Needs a project in West US 3 (the only supported region in preview) and the Foundry User role",
    ], theme="blue", icon="search", badge="preview", src=src("instant"))
    c2 = Card(SPAN(2), "Not available on instant access", [
        "Reserved capacity or PTU, and data-residency guarantees",
        "Per-model content filters or guardrails: every instant model uses the default guardrails (only an account-level default policy applies)",
        "Version locks per endpoint, fine-grained quota partitioning and fine-tuned models",
        "! A deployment with the same name shadows the instant model",
    ], theme="red", icon="compliance", src=src("instant"))
    c3 = Card(SPAN(2), "Admin controls", [
        "Azure Policy can block models or providers",
        "Switch the feature off by setting the account property instant to { raiPolicyName: Microsoft.DefaultV2, modelAllowList: [] } (API 2026-01-15-preview)",
    ], theme="grape", icon="policy", src=src("instant"))
    _, b2 = row(cv, 0, cy, [c1, c2, c3], gap=GUT)
    return b2 + 20


# ---------------------------------------------------------------------------------------------- 5. partner + router
def others(cv, y):
    y = sec(cv, y, "5  Serverless partner models and the model router deployment",
            sub="Two more things you deploy from the catalog that are not extra SKUs: a partner model hosted serverless, and the router that fronts many models.") + 40
    p = Card(SPAN(3), "Serverless pay-as-you-go partner models (MaaS)", [
        "The provider chooses managed compute or serverless. Serverless: Microsoft hosts it, the provider sets licence and price, and you pay through Azure Marketplace (SaaS)",
        "Region and billing-country eligibility applies ('Offer availability region')",
        "Examples: Claude (Global Standard; Data Zone Standard US for Azure-hosted), Fireworks (Global or Data Zone US, Standard or Provisioned), Cohere, Mistral and Meta partner models",
        "Third-party Global Standard availability tables exist per region; Data Zone Standard for partners is Americas only (Claude)",
        "Default content filtering is Azure AI Content Safety text moderation, billed separately; not for embedding or time-series models; can be toggled per endpoint. Claude has none built in",
        "Marketplace partner meters appear under the resource group; CCU-billed Claude appears under the Foundry resource",
    ], theme="orange", icon="marketplace", src=src("partners", "cost"))
    r = Card(SPAN(3), "Model router deployment", [
        "Deployed like any model: model-router, version 2025-11-18 (Active, latest GA); retirement 2027-05-20 per the schedule, as of 2026-11-03",
        "Global Standard and Data Zone Standard only; 32 regions (Data Zone Standard in a subset of them)",
        "One deployment, one rate limit and one content filter; the bill is the sum of the underlying models' costs - track it with the Cost Analysis tag deployment",
        "Routes among 35 models from six providers; you need no separate deployment for them, except Claude (deploy it first, same Foundry account, matching SKU)",
        "Images are accepted (the routing decision uses text only); no audio input. Prompt caching works only when the same underlying model serves consecutive requests with an overlapping prefix",
        "Modes, model subsets, failover and session affinity: see the Model router and lifecycle canvas",
    ], theme="blue", icon="branch", src=src("router"))
    _, b = row(cv, 0, y, [p, r], gap=GUT)
    return b + 20


# ---------------------------------------------------------------------------------------------- 6. version upgrades
def versions(cv, y):
    y = sec(cv, y, "6  Who upgrades the model version? It depends on the deployment type",
            sub="Standard types are upgraded for you; Provisioned and Batch never are. Dates as of 2026-11-03.") + 36
    rows = [
        [("Global Standard, Data Zone Standard, Standard", "blue"), "Yes: rolling, region by region, on a published schedule",
         "Set versionUpgradeOption: OnceNewDefaultVersionAvailable (upgrade within 2 weeks of the default changing; preview versions from 2 weeks after release), OnceCurrentVersionExpired (upgrade at retirement; null means this) or NoAutoUpgrade",
         "NoAutoUpgrade deployments stop working at retirement. The Azure CLI cannot update the option; REST, PowerShell and the portal can. A pinned version upgrades to the then-default at retirement"],
        [("Priority (a Standard tier)", "lime"), "Like Standard", "Migrate it like a Standard deployment", "-"],
        [("Provisioned: Global, Data Zone, Regional", "yellow"), "No: never auto-upgraded",
         "In place: same name and size; update the model version (portal, REST, CLI) or model family (REST, CLI); traffic moves over 20-30 minutes (updating, then succeeded). Or side by side: create a new PTU deployment, shift traffic, confirm no requests reach the old one for 5-10 minutes, delete it",
         "In place works only between provisioned deployments of the same type; check capacity first. A replacement is testable in provisioned regions about 30 days before retirement"],
        [("Batch: Global, Data Zone", "cyan"), "No: never auto-upgraded", "Side by side: deploy the replacement model next to the old deployment", "Retire the old deployment after the move"],
        [("Fine-tuned models", "gray"), "No", "Re-tune on the replacement model. Two clocks: training retirement (not earlier than the base model's) and deployment retirement",
         "Lifecycle page: gpt-4o and 4o-mini training no earlier than 2027-04-01, deployment 2027-10-01. Docs disagree on o4-mini: lifecycle page 2027-04-16 / 2027-10-16, schedule 2027-05-19 / 2027-11-19"],
        [("Managed compute (preview) and partner models", "gray"), "Managed compute exposes versionUpgradeOption (OnceNewDefaultVersionAvailable)",
         "A partner model's new version may get a new model ID (for example Meta-Llama-3 and 3.1 70B to Llama-3.3-70B-Instruct)", "The API contract may change with the new model"],
    ]
    t = Table([("Deployment type", 330), ("Auto-upgraded?", 300), ("How the move happens", 1250), "Watch out"], rows, w=W, theme="blue", size=14, head_size=15,
              title="Version upgrade policy by deployment type", title_size=22)
    t.place(cv, 0, y)
    ly = learn_line(cv, 0, t.bottom + 8, src("ver", "ret", "sched"))
    ty = ly + 40
    cv.text(0, ty, "The GA retirement clock (standard models)", size=24, color=get_theme("red").deep)
    end = timeline(cv, 0, ty + 44 + 130, W, [
        ("At launch", "Retirement date is set, about 18 months out", "Shown in the Models API; retirement dates are not extendable"),
        ("Month 12", "Deprecated", "Existing subscriptions keep deploying; new customers are blocked"),
        ("90-120 days before", "Replacement named", "Testable in Global Standard about 90 days before, in provisioned regions about 30 days"),
        ("60+ days before", "Retirement notice", "Email to subscription owners plus an Azure Service Health advisory (preview: 30 days)"),
        ("Month 18", "Retired: 410 Gone", "Anthropic, DeepSeek, Fireworks and Mistral GA models: 12-month lifecycle"),
    ], size=17, label_w=500, theme="red")
    return learn_line(cv, 0, end + 10, src("ret", "sched"))


# ---------------------------------------------------------------------------------------------- 7. Government, policy, create
def gov_policy(cv, y):
    y = sec(cv, y, "7  Azure Government, Azure Policy and creating a deployment",
            sub="Four types exist in Azure Government; Azure Policy can switch a type off; the CLI and Bicep take the SKU code.") + 40
    t = Table([("Deployment type", 260), ("SKU code", 330), ("Azure Government", 190)], [
        ["Global Standard, Provisioned, Batch", "GlobalStandard, GlobalProvisionedManaged, GlobalBatch", CROSS],
        ["Data Zone Standard", "DataZoneStandard", CHECK],
        ["Data Zone Provisioned", "DataZoneProvisionedManaged", CHECK],
        ["Data Zone Batch", "DataZoneBatch", CROSS],
        ["Standard (single region)", "Standard", CHECK],
        ["Regional Provisioned", "ProvisionedManaged", CHECK],
        ["Developer, Flex", "DeveloperTier, service_tier flex", CROSS],
    ], w=SPAN(2) - 40, theme="red", size=15, head_size=16, title="Azure Government: only four types", title_size=20)
    t.place(cv, 0, y)
    n_g = Note(SPAN(2) - 40, "USGov data-zone processing stays inside the Azure Government cloud. Regions: usgovarizona and usgovvirginia. PTU rules live on the Azure Government provisioned-throughput page.",
               kind="info", title="Azure Government facts", size=15, src=src("gov"))
    n_g.place(cv, 0, t.bottom + 24)
    pol = CodeCard(SPAN(2), "Azure Policy: switch a deployment type off", [
        "{ \"mode\": \"All\", \"policyRule\": { \"if\": { \"allOf\": [",
        "  { \"field\": \"type\",",
        "    \"equals\": \"Microsoft.CognitiveServices/accounts/deployments\" },",
        "  { \"field\": \"Microsoft.CognitiveServices/accounts/deployments/sku.name\",",
        "    \"equals\": \"GlobalStandard\" } ] } } }",
    ], theme="grape", note="Replace GlobalStandard with the SKU code of the type you want to restrict; pair the rule with the effect your governance team needs.",
        src=src("types"))
    pol.place(cv, SPAN(2) + GUT, y)
    cre = CodeCard(SPAN(2), "Create a deployment from the CLI", [
        "az cognitiveservices account deployment create",
        "  --sku-name <SKU> --sku-capacity N",
        "  --model-format <provider>",
        "az cognitiveservices account list-models",
    ], theme="blue", note="Portal dialog, CLI or Bicep (Microsoft.CognitiveServices/accounts/deployments; raiPolicyName defaults to Microsoft.DefaultV2). Needs Cognitive Services Contributor and CLI 2.60 or later. list-models shows model, format, version, SKU and default capacity.",
        src=src("create"))
    cre.place(cv, 2 * (SPAN(2) + GUT), y)
    bottom = max(n_g.bottom, pol.bottom, cre.bottom)
    return bottom + 20


# ---------------------------------------------------------------------------------------------- 8. notes
def notes(cv, y):
    y = sec(cv, y, "8  Re-check before you publish", sub="Preview features and a few places where the docs disagree (as of 2026-11-03).") + 36
    n = lambda kind, title, text, *keys: Note(COL * 1.0, text, kind=kind, title=title, size=15, src=src(*keys))
    items = [
        n("preview", "Preview items", "Managed compute, LoRA adapters, instant access and Flex are preview as of 2026-11-03. Re-check status, regions, limits and pricing before you publish.", "mc", "instant", "flex"),
        n("warn", "Docs disagree: model name", "The instant access page says chat-gpt-latest; the models page says gpt-chat-latest.", "instant"),
        n("warn", "Docs disagree: batch FAQ", "The Batch FAQ answer about embeddings repeats the fine-tuned-model sentence.", "batch"),
        n("warn", "Docs disagree: past dates", "Some retirement-schedule rows have dates in the past but still read Preview or GA (for example model-router 2025-05-19 and 2025-08-07, dated 2026-08-30). Treat the Models API as the source of truth.", "sched"),
        n("warn", "Docs disagree: dynamic quota", "The Batch page recommends dynamic quota; the dynamic-quota article exists only for Foundry (classic).", "batch"),
        n("info", "Pricing is not in the docs", "The deployment pages quote only percentages (Batch and Flex 50% off). For rates use the Azure pricing pages.", "types"),
    ]
    _, b = row(cv, 0, y, items, gap=GUT)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, b = title_block(cv, 0, 0, "Foundry deployment types, part 2: the lanes in detail",
                       "Flex and Priority, Batch, managed compute and LoRA adapters, instant access, partner serverless, router, version upgrades, Azure Government (as of 2026-11-03)",
                       w=W)
    y = b + 30
    legend(cv, 0, y, [("Standard: pay per token", "blue"), ("Provisioned: reserved PTU", "yellow"), ("Batch: async, 50% off", "cyan"),
                      ("Request-level tier: Flex, Priority", "lime"), ("Adapters and notes", "violet"), ("Other offers", "gray")])
    cv.text(2280, y, "Dashed border = preview offer. Part 1 picks the lane.", size=15, color=MUTED)
    y = tiers(cv, y + 60)
    y = batch(cv, y + SEC)
    y = managed(cv, y + SEC)
    y = instant(cv, y + SEC)
    y = others(cv, y + SEC)
    y = versions(cv, y + SEC)
    y = gov_policy(cv, y + SEC)
    y = notes(cv, y + SEC)
    sources(cv, 0, y + SEC, [
        L["types"], L["gov"], L["over"], L["flex"], L["prio"], L["batch"], L["mc"], L["mcdep"], L["adapter"], L["instant"], L["create"],
        L["ver"], L["ret"], L["sched"], L["router"], L["cost"],
    ], w=W, cols=3)

