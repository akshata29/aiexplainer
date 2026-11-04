"""Foundry tracing, part 1 - from an agent run to the Foundry Traces UI.

Hero: a five-stage pipeline (agent run -> OpenTelemetry GenAI spans -> exporter -> Application Insights / Log Analytics ->
Foundry Traces UI and Azure Monitor) with a setup marker, an identity rail and a numbered legend. Then the span hierarchy and the
attributes the docs name, setup per agent kind and per framework, and Entra authentication for trace ingestion (preview).
Part 2 covers client-side tracing, replay, traces to datasets, annotations, sensitive content, retention and the VS Code toolkit.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="tracing", title="Tracing: from agent run to the Traces UI", section="2", group="Observability and safety", order=41,
    description="Tracing in Foundry, part 1: the pipeline from an agent run through OpenTelemetry GenAI spans and Application Insights to the Foundry Traces UI, the span hierarchy and attributes, setup per agent kind and framework, and Entra authentication for trace ingestion.",
    tags=["tracing", "opentelemetry", "application-insights", "spans", "genai", "entra"],
)

W = 3080
COL, GUT = 480, 40
SEC = 72
LR = metrics.line_ratio()


def SPAN(n: int) -> float:
    return n * COL + (n - 1) * GUT


L = dict(
    concept=("Trace agents: concepts", learn("observability/concepts/trace-agent-concept")),
    setup=("Set up tracing", learn("observability/how-to/trace-agent-setup")),
    hosted=("Quickstart: tracing a hosted agent", learn("observability/quickstarts/quickstart-tracing-hosted-agent")),
    entra=("Entra authentication for trace ingestion (preview)", learn("observability/how-to/trace-ingestion-entra-authentication")),
    client=("Client-side tracing (preview)", learn("observability/how-to/trace-agent-client-side")),
    fw=("Trace agent frameworks (preview)", learn("observability/how-to/trace-agent-framework")),
    replay=("Trace Replay (preview)", learn("observability/how-to/trace-agent-replay")),
    todata=("Convert traces to a dataset", learn("observability/how-to/traces-to-dataset")),
    annot=("Annotate traces (preview)", learn("observability/how-to/trace-annotations")),
    sens=("Restrict access to sensitive content (preview)", learn("observability/how-to/traces-sensitive-content")),
    data=("Tracing and data handling", learn("observability/concepts/trace-data")),
    vsc=("Foundry Toolkit tracing in VS Code", learn("how-to/develop/vs-code-tracing")),
    ext=("Register external agents", learn("agents/how-to/register-external-agent")),
    otel=("OTel GenAI agent spans (GitHub, not Learn)", "https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md"),
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


def badge_on(cv, blk, kind, inset=14, up=13):
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


class Stat(Rect2):
    """Big word + caption tile."""

    def __init__(self, w, big, label, *, theme="violet", big_size=44, size=15, pad=14, badge=None):
        self.th = get_theme(theme)
        self.w, self.big, self.big_size, self.size, self.pad, self.badge = w, big, big_size, size, pad, badge
        self.lines = metrics.wrap_text(label, (w - 2 * pad) * 0.965, size)
        self.h = pad + big_size * LR + 4 + len(self.lines) * size * LR + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
            cv.text(x + pad, y + pad, self.big, size=self.big_size, color=th.deep)
            cv.text(x + pad, y + pad + self.big_size * LR + 4, "\n".join(self.lines), size=self.size, color=INK)
            if self.badge:
                _, label = STATUS.get(self.badge, ("gray", self.badge))
                bw = metrics.line_width(label, 13) + 18
                draw_badge(cv, x + self.w - pad - bw, y + pad - 1, self.badge)
        cv.register(f"stat:{self.big}", x, y, self.w, H)
        return self


class CodeCard(Rect2):
    """Monospace snippet in a soft card (only documented text; indentation is preserved)."""

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


def step_list(cv, x, y, w, steps, *, theme="violet", size=15):
    """Numbered vertical step list; returns the bottom y."""
    for i, s in enumerate(steps, 1):
        lines = metrics.wrap_text(s, (w - 46) * 0.965, size)
        h = max(len(lines) * size * LR, 28)
        numbered(cv, x + 15, y + 14, i, theme=theme, d=28, size=15)
        cv.text(x + 40, y + (h - len(lines) * size * LR) / 2, "\n".join(lines), size=size, color=INK)
        y += h + 10
    return y - 10


# ---------------------------------------------------------------------------------------------- 0. title + strip
def top_block(cv):
    _, b = title_block(cv, 0, 0, "Tracing: from agent run to the Foundry Traces UI",
                       "OpenTelemetry GenAI spans, Application Insights and Azure Monitor - part 1 of 2: the pipeline, the spans, setup and Entra ingestion (as of 2026-11-03)",
                       icon="otel", w=W)
    y = b + 26
    legend(cv, 0, y, [("Agents", "green"), ("Spans, export and the Traces UI", "violet"), ("Application Insights and data", "cyan"),
                      ("Identity and access", "red"), ("Neutral", "gray")])
    cv.text(2400, y, "Dashed border = preview. Part 2 covers client-side tracing, replay, datasets and privacy.", size=15, color=MUTED)
    y += 52
    stats = [
        Stat(COL, "GA", "for prompt and hosted agents; workflow and external agents are preview", theme="green"),
        Stat(COL, "OFF", "by default: no trace data is collected until a Foundry Account Owner or Owner connects Application Insights", theme="red"),
        Stat(COL, "2-5 min", "typical delay before a new trace shows up in the Traces tab", theme="violet"),
        Stat(COL, "90 days", "of traces the Foundry Traces UI shows out of the box; retention follows Application Insights", theme="violet"),
        Stat(COL, "1", "Application Insights connection per project", theme="cyan"),
        Stat(COL, "7", "sensitive attributes routed to the AppGenAIContent table", theme="red"),
    ]
    _, b2 = row(cv, 0, y, stats, gap=GUT)
    return b2


# ---------------------------------------------------------------------------------------------- 1. pipeline
def pipeline(cv, y):
    y = sec(cv, y, "1  The pipeline: five stages from a run to the Traces UI",
            sub="Foundry captures inputs, outputs, tool usage, retries, latencies and costs as OpenTelemetry spans; the traces are stored in Azure Monitor Application Insights.") + 40
    SW, SG = 520, 120
    sx = [i * (SW + SG) for i in range(5)]
    stages = [
        ("AGENT RUN", "who emits the work", "green", [
            ("Prompt agent", "server-side spans, no code", "ga"),
            ("Hosted agent", "server-side plus hosting libraries in your code", "ga"),
            ("Workflow agent", "server-side spans", "preview"),
            ("External agent", "you emit spans that carry gen_ai.agent.id", "preview"),
            ("Your app + framework", "client-side instrumentation", None),
        ]),
        ("OpenTelemetry spans", "GenAI semantic conventions (Development status)", "violet", [
            ("Server-side: automatic, no code", "Foundry enables it after you connect Application Insights", None),
            ("Hosting libraries + Microsoft OTel distro", "azure-ai-agentserver-responses and -invocations; microsoft-opentelemetry", None),
            ("Client-side SDK or framework instrumentation", "your own app logic around the agent call", "preview"),
        ]),
        ("Exporter", "where the spans are sent", "violet", [
            ("Azure Monitor exporter", "into the project's Application Insights", None),
            ("OTLP to Datadog, Grafana Tempo, Jaeger or Honeycomb", "any OTLP-capable backend", None),
            ("Console or Aspire Dashboard", "local development", None),
            ("VS Code local OTLP collector", "port 4317 (gRPC) and 4318 (HTTP)", None),
        ]),
        ("Application Insights", "connected to the project; data lands in Log Analytics", "cyan", [
            ("AppDependencies, AppTraces, AppEvents", "span and log tables", None),
            ("AppGenAIContent", "sensitive content; a protectable table", None),
            ("customEvents", "gen_ai.evaluation.result: evaluation results and feedback", None),
            ("Retention and sampling", "follow your Application Insights configuration", None),
        ]),
        ("Foundry (new) + Azure Monitor", "the consumption surfaces", "violet", [
            ("Agents > Traces", "search, filter, sort; last 90 days", None),
            ("Conversation view", "by Response ID, Trace ID or Conversation ID", None),
            ("Trace Replay", "trajectories and playthrough", "preview"),
            ("Monitor dashboard", "reads the same Application Insights", None),
            ("Insights", "recurring behaviours found in production traces", "preview"),
            ("Trace-based evaluations", "sample production traces, then score them", None),
            ("Traces to dataset", "versioned evaluation datasets", None),
        ]),
    ]
    # measure, then equalise heights
    gap_b = 14
    built = []
    for title, sub, th, items in stages:
        boxes = [Box(SW - 40, lab, sub=s, theme=th, fill="soft", size=17, sub_size=14, pad=9) for lab, s, _ in items]
        built.append(boxes)
    head = 96
    need = [head + sum(b.h for b in bx) + gap_b * (len(bx) - 1) + 24 for bx in built]
    H = max(need)
    # setup strip above the stages
    sy = y
    note = Note(SW * 3 + SG * 2, "Tracing is off by default. No trace data is collected or stored unless a Foundry Account Owner or Foundry Owner enables it by connecting Application Insights, "
                                 "at project creation or later. Disconnecting stops collection; data already in Application Insights stays for its retention period.",
                kind="gotcha", title="Off until you connect Application Insights", size=15, src=src("data"))
    note.place(cv, 0, sy)
    setup = Box(SW, "1  Setup, once", sub="Project > Agents > Traces > Connect (or Manage > Project details > Connected resources > Add connection > Application Insights)",
                theme="violet", h=note.h, size=19, sub_size=13, fill="hatch")
    setup.place(cv, sx[3], sy)
    top = sy + note.h + 70
    panels = []
    for i, (title, sub, th, items) in enumerate(stages):
        with cv.panel(sx[i], top, w=SW, h=H, title=title, sub=sub, theme=th, style="solid", fill="hatch" if i == 3 else "none", pad=20, title_size=24, sub_size=15) as p:
            pass
        extra = (H - need[i]) / len(built[i])
        cy = p.iy
        for b, (lab, s, badge) in zip(built[i], items):
            b.h += extra
            b.place(cv, sx[i] + 20, cy)
            if badge:
                badge_on(cv, b, badge)
            cy += b.h + gap_b
        panels.append(p)
    connect(cv, setup, panels[3], a_side="bottom", b_side="top", dash="dashed", sw=2.5, label="tracing ON", label_size=14, label_pos="right")
    arrows = [("run emits\nspans", 2), ("export", 3), ("ingest\n2-5 min", 3), ("query", 4)]
    for i, (lab, n) in enumerate(arrows):
        ay = top + 150
        x1, x2 = panels[i].right + 6, panels[i + 1].x - 6
        arrow(cv, [(x1, ay), (x2, ay)], sw=3, label=lab, label_size=14, label_wrap=104, label_pos="below")
        numbered(cv, (x1 + x2) / 2, ay - 26, n, theme="violet")
    # numbered legend directly under the pipeline, then the identity rail that elaborates step 5
    ly = top + H + 60
    cards = [
        ("1  Setup, once", "Project > Agents > Traces > Connect Application Insights (auth: key or Project managed identity). Tracing is now ON.", "violet"),
        ("2  Run", "A call reaches Foundry Agent Service, which emits server-side spans (project managed identity). Hosted agent code adds spans (Agent Identity); Agent Framework and LangChain spans nest under the hosting spans. Model calls show as chat, tools as execute_tool.", "green"),
        ("3  Export", "The exporter sends spans to Application Insights (about 2-5 minutes) and they land in Log Analytics tables. Sensitive content goes to AppGenAIContent.", "cyan"),
        ("4  Consume", "Traces tab (last 90 days), Conversation view and Trace Replay -> annotate -> add to a dataset -> evaluate -> optimize -> redeploy.", "violet"),
        ("5  Secure", "Protect AppGenAIContent and grant Privileged Monitoring Data Reader to a few identities. Use Entra instead of keys for ingestion.", "red"),
    ]
    w5 = (W - 4 * GUT) / 5
    cs = [Card(w5, t, ["= " + b], theme=th, title_size=19, body_size=15, pad=14) for t, b, th in cards]
    _, lbot = row(cv, 0, ly, cs, gap=GUT)
    ry = lbot + 44
    ingest = Card(SW * 3 + SG * 2, "5  Secure: who can write spans (ingestion)", [
        "Key-based ingestion, or - preview - Microsoft Entra: set the connection's auth to Project managed identity and disable local authentication on Application Insights",
        "A connection created in the portal gets Monitoring Metrics Publisher assigned to the project managed identity",
        "Hosted agents write with two identities: Foundry Agent Service (project managed identity) and your agent code in the sandbox (Agent Identity) - grant the Agent Identity the same role",
        "Another trace-reader role does not grant telemetry-write access",
    ], theme="red", icon="managed-identity", badge="preview", src=src("entra"))
    store = Card(SW, "Who can read protected content", [
        "Set AppGenAIContent to Protected: deny by default",
        "Grant Privileged Monitoring Data Reader on the App Insights resource linked to the project",
    ], theme="red", icon="key-vault", badge="preview", src=src("sens"))
    read = Card(SW, "Who can read traces", [
        "Log Analytics Reader on the Application Insights resource",
        "Plus Privileged Monitoring Data Reader if the tables are protected",
        "Manage at scale with Entra groups",
    ], theme="red", icon="users", src=src("setup"))
    h = max(ingest.h, store.h, read.h)
    ingest.place(cv, 0, ry, h=h)
    store.place(cv, sx[3], ry, h=h)
    read.place(cv, sx[4], ry, h=h)
    return ry + h


# ---------------------------------------------------------------------------------------------- 2. span hierarchy
SPAN_ROWS = [
    # indent, label, detail, bar start, bar end, theme
    (0, "invoke_workflow", "a coordinated workflow that contains agents or GenAI operations", 0.00, 1.00, "grape"),
    (1, "invoke_agent", "an agent invoked remotely or in-process; carries gen_ai.tool.definitions", 0.03, 0.97, "green"),
    (2, "plan", "child span: planning or task decomposition", 0.06, 0.18, "gray"),
    (2, "chat ...", "the model call; the docs screenshot shows invoke_agent, chat completions, token requests", 0.20, 0.42, "blue"),
    (2, "execute_tool", "gen_ai.tool.call.arguments and gen_ai.tool.call.result", 0.44, 0.58, "orange"),
    (2, "invoke_agent", "child span: another agent - a parent/child pair is a sub-agent call", 0.60, 0.84, "green"),
    (2, "create_memory | search_memory | update_memory | upsert_memory | delete_memory", "memory operations", 0.86, 0.95, "cyan"),
]


def span_tree(cv, x, y, w):
    """Illustrative waterfall of the span hierarchy (bar positions are not real timings)."""
    pitch, lab_w = 66, 760
    h = 96 + len(SPAN_ROWS) * pitch + 70
    with cv.panel(x, y, w=w, h=h, title="Span hierarchy: a trace as a waterfall", sub="illustrative layout, not real timings; parent spans are common examples - actual nesting depends on the instrumented agent or framework",
                  theme="violet", style="dotted", pad=22, title_size=24, sub_size=15) as p:
        pass
    bx0, bx1 = x + 22 + lab_w + 20, x + w - 30
    ry0 = p.iy + 10
    cv.text(bx0, ry0 - 20, "time ->", size=14, color=MUTED)
    cv.line((bx0, ry0 - 2), (bx1, ry0 - 2), stroke="#868e96", sw=1)
    ys, bottoms = [], []
    for i, (ind, lab, det, a, b, th) in enumerate(SPAN_ROWS):
        ry = ry0 + 8 + i * pitch
        ys.append(ry)
        t = get_theme(th)
        lx = x + 22 + ind * 34
        lines = metrics.wrap_text(lab, lab_w - ind * 34 - 6, 18)
        cv.text(lx, ry, "\n".join(lines), size=18, color=t.deep)
        d_lines = metrics.wrap_text(det, lab_w - ind * 34 - 6, 13)
        cv.text(lx, ry + len(lines) * 18 * LR, "\n".join(d_lines), size=13, color=MUTED)
        bottoms.append(ry + len(lines) * 18 * LR + len(d_lines) * 13 * LR)
        bh = 26
        cv.rect(bx0 + (bx1 - bx0) * a, ry + 6, (bx1 - bx0) * (b - a), bh, stroke=t.stroke, fill=t.fill, style="hachure", sw=2)
    # tree connectors run in the gutter left of each child label, below the parent's text block
    for i, (ind, *_r) in enumerate(SPAN_ROWS):
        if ind == 0:
            continue
        parent = max(j for j in range(i) if SPAN_ROWS[j][0] == ind - 1)
        px = x + 22 + (ind - 1) * 34 + 10
        cv.line((px, bottoms[parent] + 2), (px, ys[i] + 12), stroke="#868e96", sw=1.5)
        cv.line((px, ys[i] + 12), (px + 18, ys[i] + 12), stroke="#868e96", sw=1.5)
    cv.text(x + 22, y + h - 40, "Trace Replay filters by span type: Chat, Agent, Tool, Conversation. The waterfall bar can be measured by duration or by token cost.", size=15, color=INK)
    return p


ATTRS = [
    ("gen_ai.operation.name", "Operation type. The evaluation service reads only spans where it equals invoke_agent"),
    ("gen_ai.agent.id, .name, .version", "Agent identity. External agents are matched to the registration by gen_ai.agent.id = otel_agent_id"),
    ("gen_ai.conversation.id", "Needed for conversation-level evaluation of external agents"),
    ("gen_ai.response.id", "Correlates annotations to a traced response"),
    ("gen_ai.input.messages, gen_ai.output.messages", "Prompt and response content, needed by quality evaluators - sensitive"),
    ("gen_ai.system_instructions, gen_ai.tool.definitions, gen_ai.tool.call.arguments, gen_ai.tool.call.result, gen_ai.evaluation.explanation", "Sensitive: with the two message attributes these are the 7 attributes routed to AppGenAIContent"),
    ("gen_ai.evaluation.result (event) + gen_ai.evaluation.name, .score.value, .score.label", "Human and automated evaluation results and feedback"),
    ("code.function.parameter.<name>, code.function.return.value", "Written by the Python @trace_function decorator; always recorded, ignores the content-recording flag"),
]


def spans(cv, y):
    y = sec(cv, y, "2  What a trace contains: spans and attributes",
            sub="A trace is the journey of one request; spans are single operations with start and end, attributes and nesting; semantic conventions standardise the names.") + 36
    LW = 1700
    p = span_tree(cv, 0, y, LW)
    rx = LW + GUT
    rw = W - rx
    t = Table([("Attribute", 540), "Meaning and where it is used"], [[(a, "violet"), m] for a, m in ATTRS], w=rw, theme="violet", size=14, head_size=15,
              title="Attributes the Foundry docs name", title_size=20)
    t.place(cv, rx, y)
    ly = learn_line(cv, rx, t.bottom + 8, src("concept", "setup", "annot", "sens"))
    below = max(p.bottom, ly) + 36
    LW3 = SPAN(3)
    n1 = Note(LW3, "Microsoft and Cisco Outshift contribute multi-agent conventions that build on the OpenTelemetry GenAI agent and framework spans plus W3C Trace Context. "
                   "They are integrated into Foundry, Microsoft Agent Framework, LangChain, LangGraph and the OpenAI Agents SDK. The OTel GenAI conventions have Development status and might change.",
              kind="info", title="Conventions in motion", size=15, src=src("concept"))
    n2 = Note(LW3, "The OTel GenAI agent spec on GitHub (not Learn, Development status) also defines create_agent {gen_ai.agent.name} (a client span), invoke-agent client and internal spans, "
                   "plus skill spans: load skill, read skill resource and command execution. Foundry's server-side tracing does not enumerate its exact span names in Learn.",
              kind="warn", title="More spans exist in the spec", size=15, src=src("otel"))
    hosted = Card(W - LW3 - GUT, "Hosted agent: one tree from HTTP to the model", [
        "Agent Framework spans appear as children of the hosting-layer spans: a complete tree from the HTTP request through orchestration to tool calls and LLM interactions",
        "The server package configures Azure Monitor export and enriches every span with project, agent name, agent version and agent ID",
        "Two trace-emitting identities: Agent Service (project managed identity) and your agent code (Agent Identity)",
    ], theme="green", icon="container-apps", src=src("hosted"))
    n1.place(cv, 0, below)
    n2.place(cv, 0, n1.bottom + 22)
    hosted.place(cv, LW3 + GUT, below, h=max(hosted.h, n2.bottom - below))
    return max(n2.bottom, hosted.bottom) + 6


# ---------------------------------------------------------------------------------------------- 3. setup
def setup(cv, y):
    y = sec(cv, y, "3  Set it up: per agent kind, per framework",
            sub="Start server-side (no code). Add client-side instrumentation when you need your own app logic in the trace.") + 36
    kinds = [
        [("Prompt agent", "green"), ("GA", "green"), "Server-side and automatic after you connect Application Insights: no code",
         "Foundry Agent Service, with the project managed identity", "Connect Application Insights, run the agent once, open Agents > Traces"],
        [("Hosted agent", "green"), ("GA", "green"),
         "Server-side invocation telemetry from Agent Service, plus your code: the hosting libraries azure-ai-agentserver-responses and azure-ai-agentserver-invocations integrate the Microsoft OpenTelemetry distro (microsoft-opentelemetry on PyPI), auto-instrument Microsoft Agent Framework and LangChain, and export to Application Insights",
         "Two identities: Agent Service (project managed identity) and the agent code in the sandbox (Agent Identity)",
         "Python Agent Server SDK: pip install \"azure-ai-agentserver-core[tracing]\" emits spans automatically. With Entra-only ingestion, grant the Agent Identity Monitoring Metrics Publisher too"],
        [("Workflow agent", "green"), ("Preview", "yellow"), "Server-side and automatic, like prompt agents", "Foundry Agent Service, with the project managed identity", "Connect Application Insights"],
        [("External agent", "gray"), ("Preview", "yellow"),
         "You instrument the agent wherever it runs. Every span must carry gen_ai.agent.id; it is matched to the registration's otel_agent_id by (project, agent_id). Add gen_ai.conversation.id for conversation-level evaluation",
         "Your app's exporter writes to the project's Application Insights", "Register the agent (see Register external agents). Not supported for traces to dataset, human evaluation or red teaming"],
        [("Your app + framework", "gray"), ("Preview", "yellow"), "Client-side: OpenTelemetry plus the azure-ai-projects instrumentor, or a framework's own instrumentation (matrix below, part 2 for the SDK details)",
         "Your exporter", "Install the packages, opt in, set the connection string and pass agent_reference in responses.create()"],
    ]
    t = Table([("Agent kind", 220), ("Status", 100), ("How spans are emitted", 980), ("Who writes to Application Insights", 540), "What you do"], kinds, w=W,
              theme="violet", size=14, head_size=15, title="What emits spans for each kind of agent", title_size=21)
    t.place(cv, 0, y)
    ly = learn_line(cv, 0, t.bottom + 8, src("concept", "hosted", "ext"))
    y2 = ly + 44
    cmp_ = Table([("", 150), ("Server-side (recommended start)", 480), ("Client-side (preview)", 480)], [
        [("Code change", "violet"), "None: Foundry enables it automatically after you connect Application Insights", "Yes: OpenTelemetry plus the azure-ai-projects instrumentor or framework instrumentation"],
        [("Covers", "violet"), "Prompt agents, hosted agents and workflows: out-of-the-box traces for the past 90 days", "Your own app logic around the agent call, and model or tool calls made from your code"],
        [("Notes", "violet"), "Works for any agent hosted in Foundry", "Needed to see custom logic. Python can propagate W3C traceparent and tracestate to correlate with server-side spans"],
    ], w=SPAN(3), theme="violet", size=15, head_size=16, title="Server-side versus client-side", title_size=20)
    cmp_.place(cv, 0, y2)
    with cv.panel(0, cmp_.bottom + 30, w=SPAN(3), title="Verify in four steps", theme="violet", style="solid", fill="soft", pad=22, title_size=21) as st:
        step_list(cv, st.ix, st.iy, SPAN(3) - 44, [
            "In Foundry (new): project > Agents > Traces > Connect (an existing resource, or Create new); or Manage > Project details > Connected resources > Add connection > Application Insights.",
            "Run the agent once: the Traces list shows a new trace with timestamps, durations and status. It typically takes 2-5 minutes.",
            "View it in the Foundry Traces tab (search, filter, sort; last 90 days) or in Azure Monitor Application Insights.",
            "Conversation view: search by Response ID or Trace ID, select a Conversation ID to see the history, tokens per run, ordered actions, run steps and tool calls.",
        ])
    n_err = Note(SPAN(3), "A project can hold only one Application Insights connection. The error 'Multiple connection with same category (AppInsights) created, we only allow to have 1 connection for category' means: edit the existing connection instead. "
                          "To query you need Log Analytics Reader on the Application Insights resource, plus Privileged Monitoring Data Reader if the tables are protected; ingestion needs Contributor or higher on Application Insights for frameworks.",
                 kind="warn", title="One connection, a few roles", size=15, src=src("setup"))
    n_err.place(cv, 0, st.bottom + 24)
    rx = SPAN(3) + GUT
    fw = Table([("Framework", 190), ("How", 500), "Notes"], [
        [("Microsoft Agent Framework", "violet"), "Native: emits automatically when project tracing is on, no extra code or packages. Outside Foundry hosting: use_microsoft_opentelemetry(enable_azure_monitor=True, ..., instrumentation_options={\"agent-framework\": {...}})", "Pass agent_id and agent_name in the options"],
        [("Semantic Kernel", "violet"), "Native: same as Agent Framework", ""],
        [("LangChain / LangGraph", "violet"), "pip install microsoft-opentelemetry; use_microsoft_opentelemetry(... instrumentation_options={\"langchain\": {\"enabled\": True, agent_id, agent_name}})", "Python only. Dev content capture needs OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_AND_EVENT, OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental and AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true"],
        [("OpenAI Agents SDK", "violet"), "pip install opentelemetry-sdk opentelemetry-instrumentation-openai-agents azure-monitor-opentelemetry-exporter; OpenAIAgentsInstrumentor().instrument(...)", "Falls back to the console exporter if APPLICATION_INSIGHTS_CONNECTION_STRING is not set"],
        [("OpenInference (openinference-* packages)", "violet"), "Auto-instruments many frameworks; works for hosted and non-Foundry agents", "Hosted: correlation is automatic. External: set the agent id through the distro"],
    ], w=SPAN(3), theme="violet", size=14, head_size=15, title="Agent frameworks (preview)", title_size=20)
    fw.place(cv, rx, y2)
    ly2 = learn_line(cv, rx, fw.bottom + 8, src("fw"))
    n_fw = Note(SPAN(3), "The distro repositories: Python microsoft/opentelemetry-distro-python; .NET and JavaScript distros exist too (linked from the Register external agents page). "
                         "The portal path to check traces is worded Agents > Traces on the setup page and Observability > Traces on the frameworks page - the same place.",
                kind="info", title="Distros and portal wording", size=15, src=src("ext"))
    n_fw.place(cv, rx, ly2 + 24)
    return max(n_err.bottom, n_fw.bottom) + 10


# ---------------------------------------------------------------------------------------------- 4. Entra
def entra(cv, y):
    y = sec(cv, y, "4  Entra authentication for trace ingestion (preview)",
            sub="Replaces key-based ingestion: the identities that emit spans get a role on Application Insights and local authentication is turned off.") + 40
    bw = 560
    agent_svc = Box(bw, "Foundry Agent Service", sub="server-side spans, written with the project managed identity", theme="green", h=130, size=20, sub_size=14, icon="agent", icon_pos="top")
    code = Box(bw, "Hosted agent code", sub="spans from your code in the sandbox, written with the Agent Identity", theme="green", h=130, size=20, sub_size=14, icon="container-apps", icon_pos="top")
    ai = Box(640, "Application Insights", sub="connected to the project; local authentication disabled, so only Entra identities can write", theme="cyan", h=300, size=22, sub_size=15, icon="app-insights", icon_pos="top")
    agent_svc.place(cv, 0, y)
    code.place(cv, 0, y + 130 + 40)
    ai.place(cv, bw + 330, y - 20)
    connect(cv, agent_svc, ai, a_side="right", b_side="left", tb=0.25, sw=2.5, label="Monitoring Metrics Publisher", label_size=14, label_wrap=250)
    connect(cv, code, ai, a_side="right", b_side="left", tb=0.75, sw=2.5, label="Monitoring Metrics Publisher", label_size=14, label_wrap=250)
    reader = Box(520, "Log Analytics Reader", sub="what you need to view the traces", theme="red", h=100, size=19, sub_size=14, icon="user", icon_pos="left")
    reader.place(cv, ai.right + 130, ai.cy - 50)
    connect(cv, reader, ai, a_side="left", b_side="right", dash="dashed", sw=2.5, label="reads", label_size=14, start_head=None, end_head="arrow")
    px = ai.right + 130 + 520 + 60
    n1 = Note(W - px, "Forbidden: 'Your application might be configured with a token credential, but your Application Insights resource might be configured incorrectly' - local authentication is not disabled, or an identity is missing the role. Wait 2-5 minutes after role changes.",
              kind="gotcha", title="The usual error", size=15, src=src("entra"))
    n1.place(cv, px, y - 20)
    y2 = y + 300 + 50
    with cv.panel(0, y2, w=SPAN(3), title="Switch to Entra in five steps", theme="red", style="solid", fill="soft", pad=22, title_size=21) as st:
        step_list(cv, st.ix, st.iy, SPAN(3) - 44, [
            "Prerequisites: local authentication disabled on the connected Application Insights (this enforces Entra-only), User Access Administrator or equivalent to assign roles, Log Analytics Reader to view.",
            "Update the connection: Manage > Project details > the connection > Edit authentication > Project managed identity > Save. Or create a new connection with Auth type = Project Managed Identity.",
            "A connection created from the portal gets Monitoring Metrics Publisher assigned to the project managed identity automatically.",
            "Hosted agents: also grant Monitoring Metrics Publisher to the Agent Identity on the Application Insights resource, in portal IAM or with the CLI.",
            "Wait 2-5 minutes after role changes, then run the agent and check the Traces tab.",
        ], theme="red")
    code = CodeCard(SPAN(3), "Grant the Agent Identity (hosted agents)", [
        "az role assignment create",
        "  --assignee-object-id $AGENT_IDENTITY_OBJECT_ID",
        "  --assignee-principal-type ServicePrincipal",
        "  --role \"Monitoring Metrics Publisher\"",
        "  --scope $APP_INSIGHTS_RESOURCE_ID",
    ], theme="red", note="Writing annotations and evaluation events needs the same telemetry-write right: with Entra ingestion the writing identity needs Monitoring Metrics Publisher.",
        src=src("entra"))
    code.place(cv, SPAN(3) + GUT, y2)
    return max(st.bottom, code.bottom) + 10


# ---------------------------------------------------------------------------------------------- 5. notes
def notes(cv, y):
    y = sec(cv, y, "5  Gotchas to remember", sub="Preview status follows each feature's Learn page as of 2026-11-03.") + 36
    n = lambda kind, title, text, *keys: Note(COL, text, kind=kind, title=title, size=15, src=src(*keys))
    items = [
        n("preview", "GA versus preview", "Tracing is GA for prompt and hosted agents. Workflow and external agents are preview, as are client-side tracing, the framework integrations, Entra ingestion, Trace Replay, annotations and sensitive-content restriction.", "concept"),
        n("info", "Tracing is available in every Foundry region", "Retention and sampling follow your Application Insights configuration. Telemetry may incur costs based on data volume and retention.", "concept"),
        n("warn", "Two names for the UI path", "The setup page says Agents > Traces; the frameworks page says Observability > Traces. Both appear in the docs.", "setup", "fw"),
        n("warn", "Python-only features", "Trace-context propagation, the @trace_function decorator and the LangChain / LangGraph integration are Python only.", "client", "fw"),
        n("gotcha", "Entra-only needs two role assignments for hosted agents", "Disable local authentication on Application Insights, then give both the project managed identity and the Agent Identity Monitoring Metrics Publisher.", "entra"),
        n("warn", "Attribute names may change", "The OTel GenAI semantic conventions are in Development status: attribute and span names can change.", "concept"),
    ]
    _, b = row(cv, 0, y, items, gap=GUT)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    y = top_block(cv)
    y = pipeline(cv, y + SEC)
    y = spans(cv, y + SEC)
    y = setup(cv, y + SEC)
    y = entra(cv, y + SEC)
    y = notes(cv, y + SEC)
    sources(cv, 0, y + SEC, [L["concept"], L["setup"], L["hosted"], L["entra"], L["client"], L["fw"], L["replay"], L["todata"], L["annot"], L["sens"], L["data"], L["vsc"], L["ext"], L["otel"]],
            w=W, cols=3)
