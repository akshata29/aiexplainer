"""Foundry Observability overview - trace, monitor, evaluate and optimize on one OpenTelemetry + Application Insights data spine."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, THEMES

META = dict(
    id="observability-overview", title="Foundry Observability: one data model", section="2",
    group="Observability and safety", order=40,
    description="Trace, monitor, evaluate and optimize as one closed loop on an OpenTelemetry + Application Insights data spine - control-room surfaces, setup, roles and where every artifact is stored.",
    tags=["observability", "monitoring", "application insights", "opentelemetry", "evaluation"],
)

W = 3000
VIOLET, CYAN, BLUE, RED = (THEMES[n].stroke for n in ("violet", "cyan", "blue", "red"))


def L(label, path, base="azure/foundry"):
    return (label, learn(path, base=base))


def tc(text, theme):
    """Table cell with coloured text and no fill."""
    return {"text": text, "color": THEMES[theme].deep}


# ====================================================================== local helper blocks
class Bullets(Rect2):
    """Card bullet markup without the card frame (for use inside a Shell)."""

    def __init__(self, w, body, *, theme="violet", size=16, src=(), gap=5):
        self.card = Card(w, None, body, theme=theme, body_size=size, pad=0, gap=gap, src=src)
        self.w, self.h = w, self.card.h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        c, th = self.card, self.card.th
        self.x, self.y = x, y
        for it in c.layout:
            kind, ly = it["kind"], y + it["y"]
            color = {"head": th.stroke, "warn": "#c92a2a", "good": "#2b8a3e"}.get(kind, c.body_color)
            cv.text(x + it["tx"], ly, "\n".join(it["lines"]), size=it["size"], color=color)
            if kind in ("bullet", "warn", "good"):
                mc = {"bullet": th.stroke, "warn": "#e03131", "good": "#2f9e44"}[kind]
                cy = ly + it["size"] * metrics.line_ratio() / 2
                mx = x + it["x0"] + 4
                if it["level"]:
                    cv.ellipse(mx + 1, cy - 2.5, 5, 5, stroke=mc, fill=mc, style="solid", sw=1, rough=0)
                else:
                    cv.ellipse(mx, cy - 4, 9, 9, stroke=mc, sw=2, rough=0)
        for text, url, sy in c.src_lines:
            cv.text(x, y + sy, text, size=c.src_size, color=LINK, link=url)
        cv.register("bullets", x, y, self.w, self.h)
        return self


class Shell(Rect2):
    """Card-look container (hatch fill, icon, title, badge) that stacks arbitrary child blocks under its header."""

    def __init__(self, w, title, blocks, *, theme="violet", icon=None, badge=None, subtitle=None, pad=16,
                 title_size=20, sub_size=14, src=(), gap=10):
        self.w, self.title, self.blocks, self.theme = w, title, list(blocks), theme
        self.icon, self.badge, self.subtitle, self.pad = icon, badge, subtitle, pad
        self.title_size, self.sub_size, self.src, self.gap = title_size, sub_size, list(src), gap
        self.x = self.y = 0.0
        self.el = None
        self.h = self._draw(Canvas("measure"), 0, 0, None).h

    @property
    def bind_target(self):
        return self.el

    def _draw(self, cv, x, y, h):
        th, pad, w = THEMES[self.theme], self.pad, self.w
        icon_off = 46 if self.icon else 0
        badge_w = (text_size(STATUS.get(self.badge, ("gray", self.badge))[1], 13)[0] + 18) if self.badge else 0
        tw = (w - 2 * pad) * 0.965 - icon_off - (badge_w + 8 if self.badge else 0)
        t_lines = wrap_text(self.title, tw, self.title_size)
        s_lines = wrap_text(self.subtitle, tw, self.sub_size) if self.subtitle else []
        lh = metrics.line_ratio()
        head_h = len(t_lines) * self.title_size * lh + ((2 + len(s_lines) * self.sub_size * lh) if s_lines else 0)
        head_h = max(head_h, 36 if self.icon else 0)
        with cv.panel(x, y, theme=self.theme, style="solid", fill="hatch", pad=pad, w=w, h=h) as p:
            if self.icon:
                place_icon(cv, self.icon, p.ix, p.iy, 36)
            cv.text(p.ix + icon_off, p.iy, "\n".join(t_lines), size=self.title_size, color=th.deep)
            if s_lines:
                cv.text(p.ix + icon_off, p.iy + len(t_lines) * self.title_size * lh + 2, "\n".join(s_lines),
                        size=self.sub_size, color=MUTED)
            if self.badge:
                draw_badge(cv, p.ix + (w - 2 * pad) - badge_w, p.iy - 1, self.badge)
            cy = p.iy + head_h + 10
            for blk in self.blocks:
                blk.place(cv, p.ix, cy)
                cy += blk.h + self.gap
            cy -= self.gap
            if self.src:
                cy += 8
                for label, url in self.src:
                    cv.text(p.ix, cy, f"Learn: {label}", size=12, color=LINK, link=url)
                    cy += 16
        return p

    def place(self, cv, x, y, h=None):
        p = self._draw(cv, x, y, h)
        self.x, self.y, self.h, self.el = x, y, p.h, p.el
        return self


class Stop(Card):
    """Card whose icon slot holds a step marker (number or letter); optional small icon at the top-right."""

    def __init__(self, n, w, title, body, *, icon_name=None, **kw):
        kw["icon"] = "foundry"  # reserves the icon slot; replaced by the marker when drawing
        super().__init__(w, title, body, **kw)
        self.n, self.icon_name = n, icon_name

    def place(self, cv, x, y, h=None):
        saved, self.icon = self.icon, None
        super().place(cv, x, y, h)
        self.icon = saved
        numbered(cv, x + self.pad + self.icon_size / 2, y + self.pad + self.icon_size / 2, self.n,
                 theme=self.th.name, d=34, size=19)
        if self.icon_name:
            place_icon(cv, self.icon_name, x + self.w - self.pad - 30, y + self.pad, 30)
        return self


def stack(cv, x, y, blocks, gap=24, h=None):
    """Stack blocks vertically; stretch the last one so the column ends at y + h."""
    cy = y
    for i, b in enumerate(blocks):
        extra = max(0, (y + h) - (cy + b.h)) if (h is not None and i == len(blocks) - 1) else 0
        b.place(cv, x, cy, h=b.h + extra)
        cy += b.h + gap
    return cy - gap


def stack_h(blocks, gap=24):
    return sum(b.h for b in blocks) + gap * (len(blocks) - 1)


def balance_cols(builders, total_w, gap=60, lo=560, hi=1000, step=20, vgap=24):
    """Choose column widths so the stacked columns come out (almost) the same height.

    builders: list of f(width) -> [blocks]. Returns (widths, blocks per column, heights)."""
    n = len(builders)
    avail = total_w - gap * (n - 1)
    cache: dict = {}

    def get(i, w):
        if (i, w) not in cache:
            bl = builders[i](w)
            cache[(i, w)] = (bl, stack_h(bl, vgap))
        return cache[(i, w)]

    best: list = [None]

    def rec(i, remaining, ws):
        if i == n - 1:
            if lo <= remaining <= hi:
                allw = ws + [remaining]
                hs = [get(j, allw[j])[1] for j in range(n)]
                score = (round(max(hs) - min(hs)), round(max(hs)))
                if best[0] is None or score < best[0][0]:
                    best[0] = (score, allw, hs)
            return
        top = min(hi, remaining - lo * (n - 1 - i))
        for w in range(lo, top + 1, step):
            rec(i + 1, remaining - w, ws + [w])

    rec(0, avail, [])
    _, widths, hs = best[0]
    return widths, [get(i, w)[0] for i, w in enumerate(widths)], hs


def hdr(cv, y, text, sub=None):
    _, bottom = section_header(cv, 0, y, text, sub, w=W)
    return bottom + 30


# ====================================================================== 1. top: title, quote, pillars, lifecycle
def top(cv):
    _, bottom = title_block(cv, 0, 0, "Foundry Observability",
                            "One data model - trace, monitor, evaluate, optimize - on an OpenTelemetry + Application Insights spine",
                            icon="foundry", w=W)
    y = bottom + 20
    x = 0
    for kind, cap in (("ga", "generally available"), ("preview", "preview (no SLA, not recommended for production)"),
                      ("Foundry (new) only", "needs the Foundry (new) portal"), ("as of 2026-11-03", "status date for every stamp")):
        b = draw_badge(cv, x, y, kind)
        x += b.w + 10
        t = cv.text(x, y + 2, cap, size=14, color=MUTED)
        x += t.w + 44
    y += 50

    q = Note(W, "AI observability is the ability to monitor, understand and troubleshoot AI systems across their lifecycle: "
                "trace, evaluate, add automated quality gates to CI/CD, and collect evaluation metrics, logs, traces and model outputs.",
             kind="quote", title="The idea in one sentence", src=[L("Observability in Foundry", "concepts/observability")])
    q.place(cv, 0, y)
    y = q.bottom + 36

    pill = [
        Card(705, "Tracing", [
            "Captures LLM calls, tool invocations and agent decisions",
            "Works with Microsoft Agent Framework, LangChain, LangGraph and the OpenAI Agents SDK",
            "Off by default; starts when Application Insights is connected",
        ], theme="violet", icon="otel", subtitle="distributed tracing on OpenTelemetry",
            src=[L("Observability in Foundry", "concepts/observability")]),
        Card(705, "Monitoring", [
            "Dashboards for operational metrics, token consumption, latency, error rates and quality scores",
            "Alerts on quality-threshold failures and harmful content",
            "Data lives in the connected Application Insights",
        ], theme="violet", icon="monitor", subtitle="Azure Monitor Application Insights",
            src=[L("Observability in Foundry", "concepts/observability")]),
        Card(705, "Evaluation", [
            "Measures quality, safety and reliability",
            "Runs on datasets, generated responses, production traces or simulated conversations",
            "Built-in and custom evaluators; automated quality gates in CI/CD",
        ], theme="violet", icon="ml", subtitle="quality, safety, reliability",
            src=[L("Observability in Foundry", "concepts/observability")]),
        Card(705, "Optimization", [
            "Prompt Optimizer: quick instruction rewrites in the playground",
            "Agent optimizer: evaluation-driven search over instructions, tool descriptions, skills and model choice",
            "Promotes the winning candidate back to the agent",
        ], theme="violet", icon="gear", subtitle="evaluation-driven improvement",
            src=[L("Agent optimizer overview", "agents/concepts/agent-optimizer-overview")]),
    ]
    _, b = row(cv, 0, y, pill, gap=60)
    cap = cv.text(0, b + 12, "Learn documents three core capabilities - evaluation, monitoring, tracing - plus the optimizers. "
                  "The four-pillar framing comes from Build 2026 session BRK252 (video, not on Learn).", size=14, color=MUTED)
    y = cap.bottom + 50

    y = hdr(cv, y, "Where it applies across the lifecycle", "model selection, pre-production evaluation, post-production monitoring")
    s1 = Card(690, "Stage 1: Base model selection", [
        "Foundry benchmarks (model benchmarks) on public data or your own data",
        "Azure AI Evaluation SDK against model endpoints",
    ], theme="blue", icon="openai", src=[L("Observability in Foundry", "concepts/observability")])
    s2 = Card(690, "Stage 2: Pre-production evaluation", [
        "Evaluation datasets, edge cases, robustness",
        "Metrics: task adherence, groundedness, relevance, safety",
        "Bring your own data: portal wizard, SDK or custom evaluators",
        "AI red teaming agent (PyRIT) - best used with a human in the loop",
    ], theme="violet", icon="ml", src=[L("Observability in Foundry", "concepts/observability")])
    s3 = Card(690, "Stage 3: Post-production monitoring", [
        "Operational metrics (tokens, latency, errors)",
        "Continuous evaluation on sampled production traffic",
        "Scheduled evaluation on test datasets to detect drift; scheduled red teaming",
        "Azure Monitor alerts",
    ], theme="violet", icon="monitor", src=[L("Observability in Foundry", "concepts/observability")])
    _, b = row(cv, 0, y, [s1, s2, s3], gap=80)
    connect(cv, s1, s2, sw=4, color=VIOLET)
    connect(cv, s2, s3, sw=4, color=VIOLET)
    qr = Table([("Question", 290), ("Where to look", 420)], [
        [tc("How do I set up tracing?", "violet"), "Trace overview + setup"],
        [tc("What do I evaluate for?", "violet"), "Built-in and custom evaluators"],
        [tc("What data do I use?", "violet"), "Dataset selection"],
        [tc("How do I run it?", "violet"), "Overview, portal or SDK"],
        [tc("How did it perform?", "violet"), "Evaluation results + cluster analysis"],
        [tc("How do I improve?", "violet"), "Cluster analysis; optimize agents and re-evaluate"],
    ], w=710, theme="violet", size=14, head_size=15, title="Evaluation quick reference (docs table)", title_size=19)
    qr.place(cv, W - 710, y)
    return max(b, qr.bottom) + 60


# ====================================================================== 2. hero: the closed loop + setup
def hero(cv, y):
    bottom = hdr(cv, y, "The closed loop", "eight stations around one data spine - every turn of the loop makes the agent better")
    legend(cv, W - 1000, y + 14, [("Observability loop", "violet"), ("Data spine and storage", "cyan"), ("Roles and identity", "red")])
    ry = bottom + 20

    SW, GX, GY = 450, 110, 100
    xs = [0, SW + GX, 2 * (SW + GX)]
    s2 = Stop(2, SW, "Run + trace", ["= Spans and events flow to Application Insights (typically 2-5 min) -> Traces UI and Trace Replay"],
              theme="violet", subtitle="TRACING", icon_name="otel", body_size=15)
    s3 = Stop(3, SW, "Monitor", ["= Monitor tab (tokens, latency, success, evals, red team), model metrics, fleet view; "
                                "Azure Monitor alerts; Notification Center"],
              theme="violet", subtitle="MONITORING", icon_name="monitor", body_size=15)
    s4 = Stop(4, SW, "Evaluate continuously", ["= Sampled live traffic + scheduled evals + scheduled red-team scans; "
                                              "human and end-user feedback attach to traces"],
              theme="violet", subtitle="EVALUATION", icon_name="scheduler", body_size=15)
    s5 = Stop(5, SW, "Discover", ["= Insights clusters recurring behaviour, with evidence and a proposed fix"],
              theme="violet", subtitle="MONITORING", icon_name="advisor", body_size=15)
    s6 = Stop(6, SW, "Curate", ["= Traces -> evaluation dataset (intelligent sampling) or synthetic seeds; new evaluator or rubric"],
              theme="violet", subtitle="EVALUATION", icon_name="files", body_size=15)
    s7 = Stop(7, SW, "Evaluate candidate", ["= Cloud evaluation: compare runs (t-test) and cluster analysis"],
              theme="violet", subtitle="EVALUATION", icon_name="ml", body_size=15)
    s8 = Stop(8, SW, "Optimize", ["= Prompt Optimizer or Agent optimizer -> promote the candidate or apply it, then redeploy"],
              theme="violet", subtitle="OPTIMIZATION", icon_name="gear", body_size=15)
    s9 = Stop(9, SW, "Gate + ship", ["= GitHub Action or Azure DevOps evaluation gate (confidence intervals, pairwise stats) "
                                    "-> deploy -> back to 2"],
              theme="violet", subtitle="EVALUATION + CI/CD", icon_name="devops", body_size=15)
    top_h = max(s.h for s in (s2, s3, s4))
    for s, x in zip((s2, s3, s4), xs):
        s.place(cv, x, ry, h=top_h)

    # ---- the spine (centre column)
    nw = SW - 48
    na = Box(nw, "Instrument: OpenTelemetry GenAI spans + events", sub="Foundry servers, hosting libraries, frameworks and your code emit them; connect Application Insights (Entra auth optional)",
             theme="violet", icon="otel", icon_pos="left", fill="solid", size=17, sub_size=14)
    nb = Box(nw, "Application Insights", sub="Connected to the project - one connection per project",
             theme="cyan", icon="app-insights", icon_pos="left", fill="solid", size=17, sub_size=14)
    nc = Box(nw, "Log Analytics workspace", sub="AppDependencies, AppTraces, AppEvents; AppGenAIContent for sensitive content",
             theme="cyan", icon="log-analytics", icon_pos="left", fill="solid", size=17, sub_size=14)
    sp_y = ry + top_h + GY
    with cv.panel(xs[1], sp_y, title="The data spine", sub="one store behind every surface", theme="cyan", style="dotted",
                  fill="soft", pad=24, title_size=24, sub_size=15) as sp:
        na.place(cv, sp.ix, sp.iy)
        nb.place(cv, sp.ix, na.bottom + 56)
        nc.place(cv, sp.ix, nb.bottom + 56)
        connect(cv, na, nb, a_side="bottom", b_side="top", sw=4, color=CYAN)
        connect(cv, nb, nc, a_side="bottom", b_side="top", sw=4, color=CYAN)
    numbered(cv, na.x + 2, na.y + 2, 1, theme="violet", d=34, size=19)
    mid_y = sp.y + (sp.h - s9.h) / 2
    s9.place(cv, xs[0], mid_y)
    s5.place(cv, xs[2], mid_y, h=s9.h)
    bot_y = sp.bottom + GY
    bot_h = max(s.h for s in (s6, s7, s8))
    for s, x in zip((s8, s7, s6), xs):
        s.place(cv, x, bot_y, h=bot_h)

    # ring arrows (clockwise) + taps into the spine
    kw = dict(sw=3, color=VIOLET)
    connect(cv, s2, s3, a_side="right", b_side="left", **kw)
    connect(cv, s3, s4, a_side="right", b_side="left", **kw)
    connect(cv, s4, s5, a_side="bottom", b_side="top", **kw)
    connect(cv, s5, s6, a_side="bottom", b_side="top", **kw)
    connect(cv, s6, s7, a_side="left", b_side="right", **kw)
    connect(cv, s7, s8, a_side="left", b_side="right", **kw)
    connect(cv, s8, s9, a_side="top", b_side="bottom", **kw)
    connect(cv, s9, s2, a_side="top", b_side="bottom", **kw)
    tap = dict(dash="dotted", color=CYAN, sw=3, start_head="arrow", end_head="arrow")
    connect(cv, s3, sp, a_side="bottom", b_side="top", **tap)
    connect(cv, sp, s7, a_side="bottom", b_side="top", **tap)
    connect(cv, s9, sp, a_side="right", b_side="left", **tap)
    connect(cv, sp, s5, a_side="right", b_side="left", **tap)
    ring_bottom = bot_y + bot_h
    guide = Note(2 * (SW + GX) + SW, "Solid violet arrows are the loop and the numbers are its stations. Dotted cyan arrows mean a station reads from or writes to the data spine. "
                 "Application Insights is the common store: the Monitor tab, Insights, trace-based evaluation and trace-to-dataset curation all read it.",
                 kind="key", title="How to read the loop", size=15)
    guide.place(cv, 0, ring_bottom + 40)
    ring_bottom = guide.bottom

    # ---- right: turn it on + roles
    sx = 2 * (SW + GX) + SW + 70
    cw = (W - sx - 48 - 30) / 2
    A = Stop("A", cw, "Connect Application Insights", [
        "Agents -> Traces -> Connect, or Manage -> Project details -> Connected resources -> Add connection -> Application Insights",
        "One App Insights connection per project; optional auth: project managed identity (Entra ingestion)",
        "A Foundry Account Owner or Owner turns tracing on",
    ], theme="cyan", icon_name="app-insights", body_size=15, src=[L("Set up tracing", "observability/how-to/trace-agent-setup")])
    B = Stop("B", cw, "Open the Monitor tab", [
        "Build -> your agent -> Monitor tab",
        "The Foundry (new) toggle must be on; charts read the connected Application Insights",
    ], theme="violet", icon_name="monitor", body_size=15, src=[L("Monitor agents dashboard", "observability/how-to/how-to-monitor-agents-dashboard")])
    C = Stop("C", cw, "Link evaluation storage", [
        "Add an Azure Blob Storage connection to the project (key or Entra ID; bring-your-own supported)",
        "Evaluations fail without it",
    ], theme="cyan", icon_name="storage", body_size=15, src=[L("Troubleshooting evaluations", "observability/how-to/troubleshooting")])
    D = Stop("D", cw, "Turn on continuous evaluation", [
        "Give the project managed identity the Foundry User role",
        "Create the rule: Build -> Evaluations -> Recurring Configs -> Create, or use the SDK",
    ], theme="violet", icon_name="scheduler", body_size=15, src=[L("Monitor agents dashboard", "observability/how-to/how-to-monitor-agents-dashboard")])
    roles = Table([("Role or permission", 340), ("Granted to", 400), ("Needed for", 572)], [
        [tc("Foundry Account Owner / Owner", "red"), "People who enable tracing", "Connect Application Insights - nothing is collected until they do"],
        [tc("Log Analytics Reader", "red"), "People viewing traces", "View traces in Foundry; fleet monitoring (with Cost Management Reader)"],
        [tc("Privileged Monitoring Data Reader", "red"), "People, project MI", "Only when tables are Protected (AppGenAIContent)"],
        [tc("Monitoring Reader", "red"), "User and project MI", "Insights (reads App Insights); model deployment metrics (view)"],
        [tc("Monitoring Contributor", "red"), "Admins", "Create diagnostic settings for model resource logs"],
        [tc("Monitoring Metrics Publisher", "red"), "Project MI (+ Agent Identity for hosted agents)", "Entra-authenticated trace ingestion; writing annotations and feedback events"],
        [tc("Reader on App Insights", "red"), "Project MI", "Trace-based evaluation and traces -> dataset"],
        [tc("Foundry User", "red"), "Project MI, reviewers, prompt-agent Insights users", "Continuous evaluation, human evaluation, Insights"],
        [tc("Foundry Project Manager", "red"), "Users", "Insights on hosted agents"],
        [tc("Storage Blob Data Contributor", "red"), "Project MI", "Evaluation storage (one docs page says Data Owner - see Gotchas)"],
        [tc("Agent365.Observability.OtelWrite", "red"), "Entra Agent Identity", "Hosted-agent export to Agent 365 (granted by a Global or Application Admin)"],
    ], w=W - sx - 48, theme="red", size=14, head_size=15, title="Roles at a glance", title_size=21)
    with cv.panel(sx, ry, title="Turn it on", sub="four setup steps, then who needs which role", theme="gray", style="dotted",
                  pad=24, title_size=26, sub_size=15) as su:
        _, gb = grid(cv, su.ix, su.iy, [A, B, C, D], 2, gap_x=30, gap_y=24)
        roles.place(cv, su.ix, gb + 34)
    return max(ring_bottom, su.bottom) + 80


# ====================================================================== 3. control room
def _tile(w, label, sub, theme="violet"):
    return Box(w, label, sub=sub, theme=theme, fill="soft", size=17, sub_size=14, pad=8)


def _col_health(CW):
    iw = CW - 32
    t3 = (iw - 24) / 3
    r1 = [_tile(t3, "Token usage", "high = verbose prompts"),
          _tile(t3, "Latency", "over 10 s may mean throttling, complex tool calls or network"),
          _tile(t3, "Run success rate", "below 95% warrants investigation")]
    t2 = (iw - 12) / 2
    r2 = [_tile(t2, "Evaluation metrics", "from evaluators on sampled outputs"),
          _tile(t2, "Red teaming results", "scheduled scans; failed scans = potential security risk", "pink")]
    h1, h2 = max(t.h for t in r1), max(t.h for t in r2)

    class Wire(Rect2):
        def __init__(self):
            self.w, self.h = iw, h1 + h2 + 12

        def place(self, cv, x, y, h=None):
            self.x, self.y = x, y
            cx = x
            for t in r1:
                t.place(cv, cx, y, h=h1)
                cx += t3 + 12
            cx = x
            for t in r2:
                t.place(cv, cx, y + h1 + 12, h=h2)
                cx += t2 + 12
            return self

    c1 = Shell(CW, "Agent Monitoring Dashboard", [
        Wire(),
        Bullets(iw, ["# Gear -> Monitor settings",
                     "Recurring evaluations (preview): wizard, scheduled",
                     "Red team scans (preview): enable or disable, choose the eval template and run, set the schedule",
                     "Alerts (preview): latency, token usage, evaluation scores, red-team findings",
                     "Continuous evaluation tab (+ Add evaluator(s) for custom evaluators); Insights tab"], theme="violet", size=15),
    ], theme="violet", icon="monitor", badge="preview", subtitle="Build -> agent -> Monitor tab | Foundry (new) | reads connected App Insights",
        src=[L("Monitor agents dashboard", "observability/how-to/how-to-monitor-agents-dashboard")])
    c1b = Card(CW, "Continuous and scheduled evaluation", [
        "Continuous samples live traffic as it occurs; Scheduled runs on a fixed schedule",
        "Wizard: agents -> turn-level evaluation -> type -> data source: Live traffic (Random or Intelligent sampling + max traces/runs) or Dataset (golden dataset)",
        "SDK azure-ai-projects >= 2.0.0 (Python 3.10+; JS Node 22+; C# Azure.AI.Projects)",
        "# Continuous rule (SDK)",
        "evaluation_rules.create_or_update(EvaluationRule(...))",
        "  action: ContinuousEvaluationRuleAction(eval_id, max_hourly_runs=100)",
        "  event_type RESPONSE_COMPLETED; filter on agent_name; enabled",
        "# Scheduled evaluation (SDK)",
        "beta.schedules.create_or_update(Schedule(...))",
        "  trigger: RecurrenceTrigger (e.g. daily at 09:00)",
        "  task: EvaluationScheduleTask over agent-filtered trace data",
        "! Default max_hourly_runs = 100 - runs are skipped when exceeded. The JS SDK supports continuous rules only; schedule from the portal",
    ], theme="violet", icon="scheduler", badge="preview", body_size=15, subtitle="rules and schedules live in the Foundry project",
        src=[L("Monitor agents dashboard", "observability/how-to/how-to-monitor-agents-dashboard")])
    n_trouble = Note(CW, "Empty charts = no traffic, time range or ingestion delay. Auth errors = RBAC on App Insights or Log Analytics. "
                     "No continuous results = rule disabled or project MI lacks Foundry User. Runs skipped = hourly limit.",
                     kind="tip", title="Dashboard troubleshooting", size=15)
    c4 = Card(CW, "Notification Center", [
        "Bell icon in the Foundry portal header: in-app feed with unread badge, Dismiss all, and a View all page (sort / filter by type, project, severity)",
        "Categories listed: Security alerts (Defender), Policy and compliance (Azure Policy / guardrail issues), Run completion and other events (eval runs, training jobs)",
        "Delivery: portal only; deep-links to the Operate page, Azure portal security and policy",
    ], theme="grape", icon="alerts", body_size=15, subtitle="in-app feed - delivery is portal only",
        src=[L("Notification Center", "concepts/concept-notification-center")])
    return [c1, c1b, n_trouble, c4]


def _col_learn(CW):
    iw = CW - 32
    cats = ["Context and memory", "Cost and tokens", "Hallucinations", "Latency", "Output quality", "Reliability errors",
            "Security and risk", "Tool call failures"]
    c2a = Shell(CW, "Insights in Foundry", [
        Bullets(iw, ["Analyzes production traces from App Insights; recurring behaviours become Insights with evidence, likely cause and a recommended action",
                     "Fields: Title, Category, Severity (High / Medium / Low), Status (Active / Resolved / Dismissed), agent version + recency, AI-generated description, linked and highlighted traces (summary, duration, tokens)",
                     "Proposed fix = prompt-agent instruction diff, hosted-agent source diff, or general advice"], theme="violet", size=15),
        ChipFlow(cats, iw, theme="violet", size=14, gap=8),
    ], theme="violet", icon="advisor", badge="preview", subtitle="eight built-in categories | reads connected App Insights",
        src=[L("Insights in Foundry", "observability/how-to/agent-insights")])
    c2b = Card(CW, "Insights: prerequisites and roles", [
        "A project with GPT-5 or a newer GPT model as the judge (mini / nano ok, larger is better) + connected App Insights",
        "Foundry User (prompt agent) or Foundry Project Manager (hosted agent)",
        "Monitoring Reader on App Insights for the user AND the project MI",
        "Privileged Monitoring Data Reader if AppGenAIContent is protected; project MI access to the judge deployment",
        "! 404 = not enabled for the subscription; 403 = unauthorized",
    ], theme="violet", icon="advisor", badge="preview", body_size=15, src=[L("Insights in Foundry", "observability/how-to/agent-insights")])
    c2c = Card(CW, "Insights: run, schedule, SDK", [
        "First analysis looks back 7 days; Run now (async) or schedule it (portal toggle; SDK run_interval_hours, e.g. 6)",
        "Metrics view: active / total insights, traces and runs analyzed, token usage + estimated cost, trends; History window",
        "Custom priorities (built-in categories on / off), + Custom category, free-text Instructions",
        "SDK azure-ai-projects >= 2.6.1 (allow_preview=True): beta.agent_insight_monitors with create, begin_create_run, list_insights, update_insight, update, cancel_run",
        "Read-only pull into a coding agent: Foundry MCP Server or the Microsoft Foundry Skill tool agent_insights_get",
        "! Deleting a monitor deletes its runs, insights and state",
    ], theme="violet", icon="advisor", badge="preview", body_size=15, src=[L("Insights in Foundry", "observability/how-to/agent-insights")])
    c3 = Card(CW, "End-user feedback logging", [
        "Emit the OTel gen_ai.evaluation.result event, correlated to the trace and span",
        "Types: Binary (0.0 / 1.0, label fail / pass; thumbs) or Likert 5-point (1.0-5.0; pass if >= threshold 3.0)",
        "Source: builder or end_user (microsoft.gen_ai.human_evaluation.source)",
        "Extra attributes in internal_properties.gen_ai.evaluation: type, min_value, max_value, threshold, desirable_direction",
        "KQL: customEvents | where name == \"gen_ai.evaluation.result\"; sample sample_human_evaluations.py",
    ], theme="violet", icon="users", badge="preview", body_size=15, subtitle="stored in App Insights customEvents",
        src=[L("Log end-user feedback", "observability/how-to/log-end-user-feedback")])
    return [c2a, c2b, c2c, c3]


def _col_models(CW):
    iw = CW - 32
    metrics_list = ["ModelAvailabilityRate", "ModelRequests", "TimeToResponse", "NormalizedTimeBetweenTokens", "InputTokens", "OutputTokens",
                    "TotalTokens", "TokensCacheMatchRate", "ProvisionedUtilization", "ProvisionedConsumedTokens", "AudioInputTokens", "AudioOutputTokens"]
    c5 = Shell(CW, "Model deployment monitoring", [
        Bullets(iw, ["Azure Monitor metrics are automatic - no configuration (time-series metrics database, near-real-time alerting)",
                     "Portal: My assets -> Models + endpoints -> deployment -> Metrics tab (+ Azure Cost Management link; cost data lags ~5 h), or Azure Monitor Metrics explorer (resource type Foundry Tools)",
                     "Prefer the Models metric category over the legacy Azure OpenAI category; also Workbooks, Grafana, Power BI"], theme="blue", size=15),
        ChipFlow(metrics_list, iw, theme="blue", size=14, gap=8),
        Bullets(iw, ["ModelAvailabilityRate = (calls - server errors >= 500) / calls; ProvisionedUtilization >= 100% -> 429; TimeToResponse (PTU streaming) and TokensCacheMatchRate (PTU)",
                     "Dimensions: ApiName, OperationName, Region, StreamType, ModelDeploymentName, ModelName, ModelVersion, StatusCode",
                     "Logs: diagnostic settings -> Log Analytics (RequestResponse, Trace, Audit; AllMetrics), KQL on AzureMetrics, up to 15 min delay, ingestion costs"], theme="blue", size=15),
    ], theme="blue", icon="metrics", subtitle="reads the Azure Monitor metrics database",
        src=[L("Monitor model deployments", "foundry-models/how-to/monitor-models")])
    c6 = Card(CW, "Model router monitoring", [
        "Send header Foundry-Features: ModelRouterControls=V1Preview (Chat Completions, api-version 2024-10-21, openai >= 1.75.0)",
        "Response adds optional model_selection_details.model_router_details: mode; routing_trace[] (latency_ms, ordered attempts[] each with model + result status / error -> reveals fallback); session_affinity (sticky; source session_id_payload or session_id_header; decision initialize / retain / switch)",
        "Enable stickiness with routing_config.session_affinity {mode: sticky, session_id}; best-effort, does not block fallback",
        "Fields are optional - parse defensively; the metadata exists only in the API response, so log it yourself",
    ], theme="blue", icon="openai", badge="preview", body_size=15, subtitle="metadata exists only in the API response",
        src=[L("Monitor model router", "openai/how-to/monitor-model-router")])
    c7 = Card(CW, "Fleet monitoring (Control Plane)", [
        "Operate -> Overview: fleet health scores, alerts, active agents, error rates, compliance, trends",
        "Operate -> Assets -> Agents: inventory; per-agent pane with Active alerts (policy / security / evaluation) + Activity (error rate, runs, tokens)",
        "Discovers Foundry agents (prompt, workflows, hosted), Azure SRE Agent, Azure Logic Apps agent loops and custom agents",
        "Aggregates logs and metrics from each connected App Insights; requires OTel GenAI semantic conventions",
        "Roles: read on project / subscription, Log Analytics Reader, Cost Management Reader",
        "! Agents without App Insights get no health, cost or drill-down; different users see different agents",
    ], theme="grape", icon="dashboard", badge="Foundry (new) only", body_size=15, subtitle="reads each connected App Insights + Cost Management",
        src=[L("Monitoring across the fleet", "control-plane/monitoring-across-fleet")])
    return [c5, c6, c7]


def _col_beyond(CW):
    n_custom = Note(CW, "Custom (non-Foundry) agents: onboard via AI Gateway, emit OTel GenAI spans to the same App Insights, then use the Control Plane Asset page -> agent -> Monitor tab. "
                    "Custom-agent registration is scheduled for deprecation on April 30, 2027 (as of 2026-11-03) - use external agents instead.",
                    kind="warn", title="Custom agents are being replaced", size=15)
    c9 = Card(CW, "External agents", [
        "Register agents that run anywhere (other cloud, on-prem) so the trace view and trace-based evaluation work; Foundry stores registration metadata only - it does not host, proxy or invoke",
        "Portal: Build -> Agents -> New agent -> Link external agent (name, description, OpenTelemetry ID)",
        "SDK: project.agents.create_version(agent_name, definition=ExternalAgentDefinition(otel_agent_id=...)); allow_preview=True, header Foundry-Features: ExternalAgents=V1Preview, azure-ai-projects >= 2.3.0, Python 3.11+",
        "otel_agent_id defaults to the name and must equal gen_ai.agent.id on spans (the microsoft-opentelemetry distro sets it)",
        "Traces appear in 2-5 min; evaluate via the OpenAI-compatible evals API (multi-turn by gen_ai.conversation.id); agents.delete(force=True) leaves spans in App Insights",
        "! Not supported for external agents: human evaluation, traces -> dataset, AI red teaming",
    ], theme="green", icon="globe", badge="preview", body_size=15, subtitle="registration in the project; spans stay in your App Insights",
        src=[L("Register an external agent", "agents/how-to/register-external-agent")])
    c8 = Card(CW, "Agent 365 observability", [
        "Two ways in: Registry sync (published Foundry agents appear automatically) and Autopilots (hosted-agent blueprints)",
        "Activity data: prompt agents collected; hosted agents through the Agent 365 SDK - agents built with the Foundry hosting libraries export automatically when enabled",
        "Needs ALL of: a tenant licence, a global admin who enables Agent 365 and accepts the terms, and resource property a365LoggingEnabled = true",
        "a365LoggingEnabled defaults to true once Agent 365 is enabled for the tenant; read-only a365Status = Enabled | Disabled | NotLicensed (ARM api 2026-03-15-preview)",
        "Set per Foundry resource - no per-project or per-agent override; opt-out and an Azure Policy deny are supported",
        "! Residency differs: Foundry data follows the Azure region; Agent 365 follows the Entra tenant storage geography",
    ], theme="grape", icon="m365", body_size=15, subtitle="Agent 365 control plane - Entra tenant geography",
        src=[L("Agent 365 integration", "agents/concepts/agent-365-integration"),
             L("Configure data collection", "agents/how-to/configure-agent-365-data-collection")])
    c8b = Card(CW, "Agent 365: hosted export and transport", [
        "Hosted-agent export: the Entra Agent Identity needs app role Agent365.Observability.OtelWrite on the Agent365Observability service principal (Graph appRoleAssignments; Global or Application Admin)",
        "Firewall: allow agent365.svc.cloud.microsoft on TCP 443, or set a365LoggingEnabled = false",
        "Agent 365 docs: recommended path is the Microsoft OpenTelemetry Distro (unified across Agent 365, Foundry, Azure Monitor); direct OTLP/HTTP+JSON is the exception",
        "! Ingestion can return 200 OK while rejecting spans if the tenant or licence is not set up",
    ], theme="grape", icon="m365", body_size=15, src=[L("Grant Agent 365 permissions", "agents/how-to/grant-agent-365-permissions"),
                                                    ("Direct OpenTelemetry integration", learn("microsoft-agent-365/developer/direct-open-telemetry-integration", base=""))])
    return [n_custom, c9, c8, c8b]


def control_room(cv, y):
    y = hdr(cv, y, "The control room: nine surfaces, each reading a different store",
            "most read your connected Application Insights; model metrics come from Azure Monitor; routing detail is only in the API response")
    builders = [_col_health, _col_learn, _col_models, _col_beyond]
    heads = [("Agent health and alerts", "dashboard, evaluation rules, Notification Center", "violet"),
             ("Learn from production", "Insights and feedback", "violet"),
             ("Models, routing and fleet", "Azure Monitor + Control Plane", "blue"),
             ("Beyond Foundry-hosted agents", "external agents and Agent 365", "grape")]
    widths, cols, hs = balance_cols(builders, W, gap=60, lo=640, hi=780, step=10)
    target = max(hs)
    x = 0
    for (title, sub, th), w, blocks in zip(heads, widths, cols):
        Box(w, title, sub=sub, theme=th, h=64, fill="solid", size=21, sub_size=15).place(cv, x, y)
        stretch = target if (target - stack_h(blocks)) < 90 else None
        stack(cv, x, y + 64 + 22, blocks, gap=24, h=stretch)
        x += w + 60
    return y + 64 + 22 + target + 80


# ====================================================================== 4. optimization
class Gauge(Rect2):
    """Score-delta scale for the optimizer improvement guide (segment widths proportional to the ranges)."""

    def __init__(self, w):
        self.w, self.h = w, 110
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        total = 0.30
        segs = [(0.0, 0.03, "gray", "under 0.03", "noise"), (0.03, 0.10, "yellow", "0.03 - 0.10", "moderate"),
                (0.10, 0.20, "lime", "0.10 - 0.20", "significant"), (0.20, 0.30, "green", "over 0.20", "major")]
        by = y + 30
        for lo, hi, th, rng, word in segs:
            sx, sw = x + self.w * lo / total, self.w * (hi - lo) / total
            t = THEMES[th]
            cv.rect(sx, by, sw, 34, stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0, round_=False)
            tw, thh = text_size(word, 15)
            cv.text(sx + (sw - tw) / 2 if tw < sw else sx + 2, by + 7, word, size=15, color=t.deep)
            rw, _ = text_size(rng, 14)
            cv.text(sx + (sw - rw) / 2, by + 42, rng, size=14, color=MUTED)
        cv.text(x, y, "Change in composite score (0-1) versus the baseline", size=15, color=INK)
        cv.register("gauge", x, y, self.w, self.h)
        return self


def optimization(cv, y):
    y = hdr(cv, y, "Optimization closes the loop", "Prompt Optimizer for quick instruction rewrites; Agent optimizer for evaluation-driven search on prompt and hosted agents")
    fw, fg = 400, 120
    nodes = [
        ("Dataset", "agent traces, a registered dataset or an upload"),
        ("Baseline evaluation", "score the current agent with the eval model"),
        ("Generate candidates", "improved instructions, tool descriptions, skills or model choice (optimization model)"),
        ("Evaluate candidates", "run each candidate against the dataset"),
        ("Rank", "composite score 0-1; the best candidate is marked with a star"),
        ("Promote or apply", "new prompt-agent version, or apply to the hosted agent; then redeploy"),
    ]
    boxes = [Box(fw, a, sub=b, theme="violet", fill="solid", size=18, sub_size=14, icon_pos="left") for a, b in nodes]
    hmax = max(b.h for b in boxes)
    for i, b in enumerate(boxes):
        b.place(cv, i * (fw + fg), y, h=hmax)
    for i in range(5):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", sw=3, color=VIOLET, num=i + 1, num_theme="violet")
    y = y + hmax + 50
    CW, G = 960, 60
    po = Card(CW, "Prompt Optimizer", [
        "Playground: pencil-sparkle icon next to Instructions",
        "Text-only instructions; paragraph-level reasoning; iterate with suggestions",
        "Results are ephemeral - click Use prompt to keep them",
        "Available in 15 regions (as of 2026-11-03)",
    ], theme="violet", icon="gear", body_size=15, subtitle="quick instruction rewrites in the playground",
        src=[L("Prompt Optimizer", "observability/how-to/prompt-optimizer")])
    ao = Card(CW, "Agent optimizer: prompt agents", [
        "Improves instructions, function-tool descriptions and model selection; agents without the Microsoft Copilot harness",
        "Portal Optimize tab -> wizard: Target -> Dataset -> Criteria -> Review",
        "Pre-run cost estimate (prompt agents only): Minimum / Estimated / Maximum - not a spending limit",
        "Static assumptions: agent 2,000 in + 400 out tokens per call; judge 3,000 + 120; reflection 6,000 + 2,000",
        "Post-run token usage by phase: Running your agent, Scoring responses, Generating improvements",
        "Promote a candidate -> new prompt-agent version (if the agent is pinned to a version, set the active one manually)",
    ], theme="violet", icon="gear", body_size=15, subtitle="evaluation-driven, runs in the cloud",
        src=[L("Agent optimizer overview", "agents/concepts/agent-optimizer-overview"), L("Agent optimizer costs", "agents/concepts/agent-optimizer-costs")])
    ah = Card(CW, "Agent optimizer: hosted agents", [
        "Improves instructions, skills, tool descriptions and model selection",
        "Run from the Foundry Toolkit or azd ai agent optimize --config eval.yaml",
        "Make the agent optimizer-ready first: load_config(), instructions.md, skills/*/SKILL.md, tools.json, model_search_space in eval.yaml",
        "Needs the Responses protocol; available where hosted agents are, except Norway East (as of 2026-11-03)",
        "Results come back through azd - the Optimize tab covers prompt agents",
    ], theme="violet", icon="container-apps", body_size=15, subtitle="Foundry Toolkit or azd",
        src=[L("Agent optimizer overview", "agents/concepts/agent-optimizer-overview"), L("Evaluate with azd", "observability/how-to/azure-developer-cli-evaluation")])
    _, b = row(cv, 0, y, [po, ao, ah], gap=G)
    y = b + 30
    models = Card(CW, "Models and datasets", [
        "Eval model: any chat-completion model",
        "Optimization model (as of 2026-11-03): gpt-5, 5.1, 5.2, 5.4, 5.5, DeepSeek-V4-Pro or DeepSeek-V-3.2",
        "Dataset sources: agent traces, a registered dataset, or an upload",
    ], theme="violet", icon="openai", body_size=15, src=[L("Agent optimizer overview", "agents/concepts/agent-optimizer-overview")])
    guide = Shell(CW, "Improvement guide", [Gauge(CW - 32)], theme="violet", icon="metrics",
                  src=[L("Agent optimizer overview", "agents/concepts/agent-optimizer-overview")])
    warn = Note(CW, "The optimizer invokes the agent on every dataset row, so tool calls really execute. Point the agent at test endpoints before you optimize.",
                kind="gotcha", title="Side effects", size=15)
    _, b = row(cv, 0, y, [models, guide, warn], gap=G)
    return b + 80


# ====================================================================== 5. storage + troubleshooting
def storage(cv, y):
    y = hdr(cv, y, "Where is each artifact stored?", "color = the store: cyan is the data spine, green the Foundry project, blue Azure Monitor metrics, red = not stored")
    TW = 1930

    def c(text, th):
        return (text, th)

    st = Table([("Artifact", 520), ("Stored in", 800), ("Notes", 610)], [
        ["Traces, spans, logs", c("Application Insights -> Log Analytics (AppDependencies, AppTraces, AppEvents; AppGenAIContent for sensitive content)", "cyan"),
         "Foundry UI shows the last 90 days; retention follows App Insights / Log Analytics; off until connected"],
        ["End-user and builder feedback, human-evaluation answers", c("App Insights customEvents (gen_ai.evaluation.result)", "cyan"), "retention per App Insights; download CSV for long-term"],
        ["Dashboard, Insights inputs, fleet metrics", c("Read from the connected App Insights (+ Cost Management for cost)", "cyan"), ""],
        ["Model deployment metrics", c("Azure Monitor metrics database (automatic)", "blue"), ""],
        ["Resource logs (RequestResponse, Trace, Audit)", c("Log Analytics (or another destination) only after a diagnostic setting", "cyan"), "cost per GB"],
        ["Cloud evaluation definitions, runs, results", c("Foundry project (Evals API; report_url); optional copy to App Insights; datasets and results read-write in the linked Blob storage account", "green"),
         "storage connection required; bring-your-own storage supported"],
        ["Datasets (uploaded, synthetic, from traces, simulated conversations)", c("Versioned Foundry datasets in the project", "green"), ""],
        ["Custom evaluators and rubrics", c("Evaluator catalog (versioned) in the project", "green"), ""],
        ["Continuous eval rules and schedules", c("Foundry project (evaluation_rules, beta.schedules)", "green"), ""],
        ["Insight monitors, runs, insights", c("Foundry (preview API)", "green"), "deleting a monitor deletes its insights; physical store not documented"],
        ["Optimization runs", c("Foundry Optimize tab (prompt agents) / azd results (hosted)", "green"), "Prompt Optimizer output is not stored"],
        ["Cluster analysis, compare view", c("Not stored", "red"), "download CSV before leaving"],
        ["Model-router request metadata", c("Only in the API response", "red"), "log it yourself"],
        ["External-agent registration", c("Foundry project (metadata only)", "green"), "spans stay in your App Insights"],
        ["Notification Center", c("Foundry portal (in-app)", "gray"), ""],
        ["Agent 365 activity data", c("Agent 365 control plane (Entra tenant geography)", "grape"), "opt-out per Foundry resource"],
        ["Local traces (VS Code)", c("Local SQLite traces.db (.aitk\\tracing)", "gray"), ""],
    ], w=TW, theme="cyan", size=14, head_size=16)
    st.place(cv, 0, y)

    trouble = Table([("Symptom", 350), ("What to do", 670)], [
        [tc("Storage not linked", "red"), "Create the Blob connection (Build -> Tools to check)"],
        [tc("403 AuthorizationPermissionMismatch", "red"), "Project MI needs Storage Blob Data Contributor (az role assignment create; propagation up to 10 min)"],
        [tc("Slow or stuck run, or 429", "red"), "Judge deployment TPM quota: shrink the dataset, fewer turns, cancel via evals.runs.cancel; honour retry-after + backoff"],
        [tc("401 / 403", "red"), "az login or azd auth login; Foundry User on the project (and at account scope for model inference)"],
        [tc("Data mapping or schema errors", "red"), "JSONL, one object per line; case-sensitive field names; item_schema must match; conversation-level needs messages"],
        [tc("Zero or missing scores", "red"), "Evaluator not selected; safety zero = category disabled or unsupported; low groundedness = incomplete retrieval context"],
        [tc("Agent evaluator tool errors", "red"), "Unsupported tool: wrap it as a function tool"],
        [tc("azd eval issues", "red"), "azd ext list (>= 0.1.40-preview per the evaluation page; the tracing quickstart names a different extension - docs differ), azd ai agent show, check the deployment name"],
        [tc("Trace evaluation score = None", "red"), "Project MI needs Reader on App Insights (+ Privileged Monitoring Data Reader / Log Analytics Reader); invoke_agent spans need gen_ai.input.messages and output.messages - pip install \"azure-ai-agentserver-core[tracing]\""],
        [tc("Human evaluation", "red"), "Feedback button missing = no active template; results missing = App Insights not configured or up to 5 min ingestion; reviewer needs Foundry User"],
    ], w=W - TW - 50, theme="gray", size=14, head_size=16, title="Troubleshooting strip", title_size=21)
    trouble.place(cv, TW + 50, y)
    return max(st.bottom, trouble.bottom) + 80


# ====================================================================== 6. gotchas + sources
def gotchas(cv, y):
    y = hdr(cv, y, "Gotchas and docs that disagree", "what to double-check before you rely on a behaviour")
    NW = 705
    notes = [
        Note(NW, "Tracing is GA only for prompt and hosted agents. Dashboard Monitor settings (recurring evals, red-team scans, alerts), Insights, end-user feedback logging, model-router metadata, external agents and parts of the Notification Center are preview or newly documented; agent guardrails are preview (as of 2026-11-03).",
             kind="preview", title="GA vs preview"),
        Note(NW, "The Monitor tab and fleet monitoring exist only in the Foundry (new) portal; the Insights and dashboard steps assume the New Foundry toggle is on.",
             kind="warn", title="Foundry (new) only"),
        Note(NW, "Nothing is collected until a Foundry Account Owner or Owner connects Application Insights. Disconnecting stops collection; existing data stays per retention.",
             kind="info", title="Tracing is off by default"),
        Note(NW, "Evaluations fail without a Blob storage connection; a missing role returns 403 AuthorizationPermissionMismatch. Docs disagree on the role: Storage Blob Data Contributor (permissions + troubleshooting pages) vs Storage Blob Data Owner on the account and the project resource (regions + limits page).",
             kind="gotcha", title="Storage connection is mandatory"),
        Note(NW, "Insights needs a GPT-5 or newer judge; composite evaluators need the GPT-5.6 family; rubric evaluators need gpt-5.x, gpt-4.1 or gpt-4o.",
             kind="info", title="Model requirements"),
        Note(NW, "Risk and safety evaluations and agent-playground evaluations are consumption-billed. Playground evaluations are ON by default for every project - turn them off by unselecting all evaluators under Metrics.",
             kind="warn", title="Playground evaluations are on and billed"),
        Note(NW, "Foundry data follows the Azure region; Agent 365 activity data follows the Entra tenant storage geography. Opt out per Foundry resource with a365LoggingEnabled = false.",
             kind="gotcha", title="Agent 365 changes residency"),
        Note(NW, "Foundry page: at least one Microsoft 365 Copilot licence + Frontier preview. Agent 365 page: Microsoft 365 E7 or an Agent 365 licence assigned to at least one user. The Foundry page also calls the setting agent365Config in prose, but a365LoggingEnabled / a365Status in the how-to.",
             kind="warn", title="Docs disagree: Agent 365 licence"),
        Note(NW, "The page says four main notification types but lists three: Security alerts (Defender), Policy and compliance, Run completion and other events.",
             kind="warn", title="Docs disagree: Notification Center"),
        Note(NW, "In Metrics explorer prefer the Models metric category over the legacy Azure OpenAI category.",
             kind="tip", title="Metrics category"),
        Note(NW, "Foundry shows the last 90 days of traces, while retention follows your Application Insights / Log Analytics configuration - the docs do not explain how the two interact.",
             kind="warn", title="Docs unclear: retention"),
        Note(NW, "Optimizer model lists, rubric and composite-evaluator requirements, SDK minimum versions and preview API shapes move quickly; re-check the linked pages (SDK minimums here range from azure-ai-projects 2.0.0 to 2.8.0).",
             kind="info", title="Fast-moving surface"),
    ]
    _, b = grid(cv, 0, y, notes, 4, gap_x=60, gap_y=28)
    return b + 70


def build(cv: Canvas) -> None:
    y = top(cv)
    y = hero(cv, y)
    y = control_room(cv, y)
    y = optimization(cv, y)
    y = storage(cv, y)
    y = gotchas(cv, y)
    sources(cv, 0, y, [
        ("Observability in Foundry (concepts)", learn("concepts/observability")),
        ("Monitor agents with the dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard")),
        ("Insights in Foundry", learn("observability/how-to/agent-insights")),
        ("Log end-user feedback", learn("observability/how-to/log-end-user-feedback")),
        ("Notification Center", learn("concepts/concept-notification-center")),
        ("Monitor model deployments", learn("foundry-models/how-to/monitor-models")),
        ("Monitor model router", learn("openai/how-to/monitor-model-router")),
        ("Monitoring across the fleet (Control Plane)", learn("control-plane/monitoring-across-fleet")),
        ("Agent 365 integration", learn("agents/concepts/agent-365-integration")),
        ("Configure Agent 365 data collection", learn("agents/how-to/configure-agent-365-data-collection")),
        ("Register an external agent", learn("agents/how-to/register-external-agent")),
        ("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
        ("Prompt Optimizer", learn("observability/how-to/prompt-optimizer")),
        ("Troubleshoot evaluations", learn("observability/how-to/troubleshooting")),
        ("Foundry Observability pricing (azure.microsoft.com)", "https://azure.microsoft.com/pricing/details/foundryobservability/"),
        ("Video: From observability to ROI for AI agents (BRK252, Build 2026)", "https://build.microsoft.com/en-US/sessions/BRK252"),
    ], w=W, cols=4, title="Sources and further reading (Microsoft Learn; pricing page and video are not Learn)")
