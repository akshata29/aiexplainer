"""Foundry tracing, part 2 - client-side tracing, replay, traces to datasets, annotations, privacy, retention and VS Code.

Part 1 (tracing) is the pipeline, the spans, setup per agent kind and Entra ingestion. This sheet follows a trace after it exists:
add client-side spans (preview), replay a conversation (preview), turn traces into evaluation datasets, annotate with human feedback
(preview), restrict sensitive content (AppGenAIContent, the 2026-09-30 cut-over has passed), data handling and retention, and the
VS Code Foundry Toolkit.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="tracing-part-2", title="Tracing: client-side, replay, datasets and privacy", section="2", group="Observability and safety", order=41.5,
    description="Tracing in Foundry, part 2: client-side tracing (preview), Trace Replay, traces to evaluation datasets, human annotations, restricting sensitive content in AppGenAIContent (the 2026-09-30 cut-over has passed), data handling and retention, and VS Code tracing.",
    tags=["tracing", "trace-replay", "datasets", "annotations", "sensitive-content", "vs-code"],
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
    evalregions=("Evaluation regions, limits and virtual network", learn("concepts/evaluation-regions-limits-virtual-network")),
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
    for i, s in enumerate(steps, 1):
        lines = metrics.wrap_text(s, (w - 46) * 0.965, size)
        h = max(len(lines) * size * LR, 28)
        numbered(cv, x + 15, y + 14, i, theme=theme, d=28, size=15)
        cv.text(x + 40, y + (h - len(lines) * size * LR) / 2, "\n".join(lines), size=size, color=INK)
        y += h + 10
    return y - 10


def flow(cv, x, y, boxes, gap, *, dashes=None, labels=None, sw=2.5):
    placed, cx = [], x
    for b in boxes:
        b.place(cv, cx, y)
        placed.append(b)
        cx += b.w + gap
    for i, (a, b) in enumerate(zip(placed, placed[1:])):
        connect(cv, a, b, a_side="right", b_side="left", sw=sw, dash=(dashes[i] if dashes else "solid"),
                label=(labels[i] if labels and i < len(labels) else None), label_size=14)
    return placed, y + max(b.h for b in placed)


# ---------------------------------------------------------------------------------------------- 1. client-side tracing
def client_side(cv, y):
    y = sec(cv, y, "1  Client-side tracing (preview): add your own app logic to the trace",
            sub="Server-side spans need no code. Client-side spans wrap the code around the agent call and correlate with the server-side ones through W3C trace context.") + 40
    LW = 1700
    top = y
    app = Box(520, "Your app", sub="AIProjectInstrumentor().instrument() after the experimental opt-in; custom spans with @trace_function (Python) or an ActivitySource (C#)", theme="gray",
              h=190, size=21, sub_size=14, icon="python", icon_pos="top")
    sdk = Box(460, "OpenTelemetry SDK + exporter", sub="azure-monitor-opentelemetry with configure_azure_monitor(connection_string=...), or OTLP", theme="violet", h=190, size=20, sub_size=14, icon="otel", icon_pos="top")
    svc = Box(520, "Foundry Agent Service", sub="server-side spans for the same agent run; responses.create() carries agent_reference (name + id) and traceparent", theme="green", h=190, size=20, sub_size=14, icon="agent", icon_pos="top")
    ai = Box(520, "Application Insights", sub="client and server spans join in one trace; see them in Agents > Traces", theme="cyan", h=190, size=20, sub_size=14, icon="app-insights", icon_pos="top")
    app.place(cv, 0, top)
    sdk.place(cv, 640, top)
    svc.place(cv, 0, top + 190 + 110)
    ai.place(cv, 1180, top + 150)
    connect(cv, app, sdk, a_side="right", b_side="left", sw=2.5, label="spans", label_size=14)
    connect(cv, sdk, ai, a_side="right", b_side="top", route="elbow", sw=2.5, label="export", label_size=14)
    connect(cv, app, svc, a_side="bottom", b_side="top", sw=2.5, dash="dashed", label="traceparent, tracestate", label_size=14, label_pos="right")
    connect(cv, svc, ai, a_side="right", b_side="bottom", route="elbow", sw=2.5, label="server-side export", label_size=14)
    cb = Note(LW, "Content recording is for development only. Baggage can leak personal data, and trace-context propagation sends trace IDs to Azure services. "
                  "Keep content recording off in production; the @trace_function decorator always records its parameters and return value and ignores the content-recording flag.",
              kind="warn", title="Privacy", size=15, src=src("client"))
    cb.place(cv, 0, top + 190 + 110 + 190 + 40)
    rx = LW + GUT
    rw = W - rx
    pk = Table([("Language", 110), ("Packages", 480), "Opt in (experimental)"], [
        [("Python", "violet"), "azure-ai-projects, opentelemetry-sdk, azure-core-tracing-opentelemetry, azure-monitor-opentelemetry (+ opentelemetry-exporter-otlp for OTLP or Aspire)",
         "Environment variable AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true, set before AIProjectInstrumentor().instrument()"],
        [("C#", "violet"), "Azure.AI.Projects, Azure.AI.Projects.Agents, Azure.Identity, Azure.Monitor.OpenTelemetry.Exporter",
         "AppContext.SetSwitch(\"Azure.Experimental.EnableGenAITracing\", true)"],
        [("JavaScript", "violet"), "@azure/ai-projects 2.4.0 or later, @azure/monitor-opentelemetry", "tracingOptions: { experimental: true }"],
    ], w=rw, theme="violet", size=14, head_size=15, title="Install and enable, per language", title_size=20)
    pk.place(cv, rx, top - 6)
    ly = learn_line(cv, rx, pk.bottom + 8, src("client"))
    code = CodeCard(rw, "Connection string from the project (Python)", [
        "cs = project.telemetry.get_application_insights_connection_string()",
        "configure_azure_monitor(connection_string=cs)",
    ], theme="violet", note="Include agent_reference (name and id) in responses.create() to correlate traces with a specific agent in the portal.", src=src("client"))
    code.place(cv, rx, ly + 20)
    y2 = max(cb.bottom, code.bottom) + 44
    env = Table([("Environment variable", 560), ("Default", 130), "What it does"], [
        ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING", "false", "Turns the GenAI tracing instrumentation on"],
        ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false", "Content recording of prompts and responses"],
        ["AZURE_TRACING_GEN_AI_ENABLE_TRACE_CONTEXT_PROPAGATION", "true when tracing is on", "W3C trace-context propagation (Python)"],
        ["AZURE_TRACING_GEN_AI_TRACE_CONTEXT_PROPAGATION_INCLUDE_BAGGAGE", "false", "Also propagate baggage"],
        ["AZURE_TRACING_GEN_AI_INSTRUMENT_RESPONSES_API", "true", "Instrument the Responses API"],
        ["AZURE_TRACING_GEN_AI_INCLUDE_BINARY_DATA", "false", "Base64 or image URLs inflate the payload"],
    ], w=SPAN(3) + 40, theme="violet", size=14, head_size=15, first_col_theme=None, title="Environment variables the docs list", title_size=20)
    env.place(cv, 0, y2)
    ly2 = learn_line(cv, 0, env.bottom + 8, src("client"))
    c1 = Card(SPAN(2) + 60, "Custom spans and attributes", [
        "Python: the @trace_function decorator (from azure.ai.projects.telemetry import trace_function); it writes code.function.parameter.<name> and code.function.return.value",
        "C#: an ActivitySource",
        "Custom attributes through a SpanProcessor, for example session.id",
        "Backends: Azure Monitor, console, or any OTLP backend such as Datadog, Grafana Tempo, Jaeger or Honeycomb",
    ], theme="violet", icon="code", src=src("client"))
    c1.place(cv, env.right + GUT, y2)
    return max(ly2, c1.bottom) + 10


# ---------------------------------------------------------------------------------------------- 2. replay
def replay(cv, y):
    y = sec(cv, y, "2  Trace Replay (preview): step through a conversation",
            sub="Open it from any page that references a Conversation ID or Trace ID (Agents > Traces). Two tabs: Trajectories and User.") + 40
    PW = 1700
    with cv.panel(0, y, w=PW, h=560, title="Trace Replay, sketched from the docs", theme="violet", style="dotted", pad=22, title_size=22) as p:
        pass
    t1 = Chip("Trajectories (default)", theme="violet", size=17, fill="solid")
    t2 = Chip("User", theme="gray", size=17, fill="soft")
    t1.place(cv, 24, y + 64)
    t2.place(cv, 24 + t1.w + 14, y + 64)
    note = cv.text(24 + t1.w + t2.w + 40, y + 70, "Trajectories: span tree + waterfall bar by duration or token cost.  User: chat-style view + collapsible span tree.", size=14, color=MUTED, wrap=PW - t1.w - t2.w - 100)
    rows = [(0, "invoke_agent", 0.00, 1.00, "green"), (1, "chat", 0.04, 0.30, "blue"), (1, "execute_tool", 0.32, 0.50, "orange"),
            (1, "chat", 0.52, 0.92, "blue"), (1, "create_memory", 0.93, 0.99, "cyan")]
    bx0, bx1 = 300, PW - 60
    ry = y + 130
    for i, (ind, lab, a, b, th) in enumerate(rows):
        t = get_theme(th)
        cv.text(44 + ind * 34, ry + i * 50, lab, size=18, color=t.deep)
        cv.rect(bx0 + (bx1 - bx0) * a, ry + i * 50 + 3, (bx1 - bx0) * (b - a), 26, stroke=t.stroke, fill=t.fill, style="hachure", sw=2)
    sy = ry + len(rows) * 50 + 24
    cv.text(24, sy, "Playthrough", size=19, color=get_theme("violet").deep)
    cv.line((220, sy + 14), (PW - 330, sy + 14), stroke="#495057", sw=3)
    cv.ellipse(220 + (PW - 550) * 0.42 - 10, sy + 4, 20, 20, stroke="#5f3dc4", fill="#d0bfff", style="solid", sw=2, rough=0)
    cx = PW - 300
    for s in ("1x", "2x", "4x"):
        c = Chip(s, theme="violet", size=16, fill="solid" if s == "1x" else "soft")
        c.place(cv, cx, sy)
        cx += c.w + 10
    cv.text(24, sy + 44, "Sequential replay, skip spans, speed 1x, 2x or 4x and a scrubber. It needs at least 2 spans.", size=15, color=INK)
    fy = sy + 90
    cv.text(24, fy, "Filters:", size=17, color=get_theme("violet").deep)
    fx = 120
    for s, th in (("Chat", "blue"), ("Agent", "green"), ("Tool", "orange"), ("Conversation", "gray")):
        c = Chip(s, theme=th, size=15)
        c.place(cv, fx, fy - 4)
        fx += c.w + 10
    fx += 20
    cv.text(fx, fy, "token level:", size=15, color=MUTED)
    fx += 120
    for s, th in (("Low  under 500", "green"), ("Medium  500-2k", "yellow"), ("High  over 2k", "red")):
        c = Chip(s, theme=th, size=15)
        c.place(cv, fx, fy - 4)
        fx += c.w + 10
    cv.text(24, fy + 40, "Also: Find in trace (text search) and a raw metadata JSON view for any selected span.", size=15, color=INK)
    rx = PW + GUT
    rw = W - rx
    c1 = Card(rw, "What a selected span shows", [
        "LLM invocations, tool execution, user prompts and sub-agent orchestration",
        "Raw metadata JSON",
        "Results of evaluations that ran on the conversation",
    ], theme="violet", icon="otel", badge="preview", src=src("replay"))
    c1.place(cv, rx, y)
    c2 = Card(rw, "Use it for", [
        "Root-cause analysis and debugging",
        "Token usage optimisation: switch the waterfall to token cost",
        "Conversation reconstruction and audit",
    ], theme="violet", icon="advisor", src=src("replay"))
    c2.place(cv, rx, c1.bottom + 24)
    c3 = Card(rw, "Opening replay", [
        "From any page that references a Conversation ID or Trace ID, for example Agent > Traces",
        "Conversation view: search by Response ID or Trace ID, then pick a Conversation ID",
    ], theme="violet", icon="search", src=src("replay", "setup"))
    c3.place(cv, rx, c2.bottom + 24)
    return max(p.bottom, c3.bottom) + 10


# ---------------------------------------------------------------------------------------------- 3. traces -> dataset
def to_dataset(cv, y):
    y = sec(cv, y, "3  Traces to datasets: close the improvement loop",
            sub="Turn real production conversations into versioned evaluation datasets, then evaluate and optimise.") + 40
    bw, gap = 500, 100
    boxes = [
        Box(bw, "Traces", sub="in the connected Application Insights; pick an agent, a date range and (optionally) an agent version", theme="cyan", h=170, size=20, sub_size=14, icon="app-insights", icon_pos="top"),
        Box(bw, "Intelligent sampling", sub="when max_samples is set: drops low-intent traces (for example single-character messages), keeps a diverse sample using MinHash", theme="violet", h=170, size=20, sub_size=14, icon="gear", icon_pos="top"),
        Box(bw, "Generation job", sub="runs in the background; redact_private_content defaults to true", theme="violet", h=170, size=20, sub_size=14, icon="scheduler", icon_pos="top"),
        Box(bw, "Versioned dataset", sub="standard query-response schema; OVERWRITE (default) or MERGE; a version is never modified in place", theme="cyan", h=170, size=20, sub_size=14, icon="files", icon_pos="top"),
        Box(bw, "Evaluate", sub="start an evaluation from the dataset; optimise and redeploy", theme="violet", h=170, size=20, sub_size=14, icon="ml", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, boxes, gap)
    cy = b + 40
    c1 = Card(SPAN(2), "In the portal", [
        "Data Generation tab > Create dataset > From traces",
        "Choose the agent, the dataset, Create dataset for = Evaluation, a date range, sampling and Maximum samples (1 to 1,000)",
        "Check the Data tab to preview, download or delete; then start an evaluation",
        "Or: in the Traces table select traces and choose Add to dataset",
    ], theme="violet", icon="foundry", src=src("todata"))
    c2 = Card(SPAN(2), "In the SDK", [
        "azure-ai-projects 2.8.0 or later (JavaScript: @azure/ai-projects 2.8.0 or later)",
        "project_client.datasets.begin_create_generation_job(...) with TracesDataGenerationJobSource (agent_name, start_time, end_time, optional agent_version or trace_ids) and TracesDataGenerationJobConfiguration (max_samples, redact_private_content)",
        "Manage jobs: list, get, cancel, delete. Output write_mode: OVERWRITE or MERGE",
    ], theme="violet", icon="python", src=src("todata"))
    c3 = Card(SPAN(2), "Roles and limits", [
        "Foundry User or higher; the project managed identity needs Reader on Application Insights (plus Privileged Monitoring Data Reader if the tables are protected)",
        "! Application Insights must allow public network access, even behind a private link scope; bring-your-own storage also needs public access for dataset creation",
        "! Not supported for external agents",
        "Tip: pin agent_version; max_samples is a ceiling, and trace_ids selects exact traces",
    ], theme="red", icon="managed-identity", src=src("todata", "evalregions"))
    _, b2 = row(cv, 0, cy, [c1, c2, c3], gap=GUT)
    return b2 + 10


# ---------------------------------------------------------------------------------------------- 4. annotations
def annotations(cv, y):
    y = sec(cv, y, "4  Human annotations (preview): thumbs on a trace become evaluation events",
            sub="Annotations are appended as gen_ai.evaluation.result events in the same trace; they never overwrite earlier feedback.") + 40
    bw, gap = 560, 110
    boxes = [
        Box(bw, "Builder or end user", sub="Annotate button on the trace detail (source = builder), or your app (source = end_user)", theme="gray", h=160, size=20, sub_size=14, icon="user", icon_pos="top"),
        Box(bw, "Thumbs up or down", sub="up = score 1.0, label pass; down = 0.0, fail; optional explanation. Default template task_completion is preseeded in every project", theme="violet", h=160, size=20, sub_size=14, icon="workbooks", icon_pos="top"),
        Box(bw, "gen_ai.evaluation.result event", sub="same trace and span context: operation_Id = trace ID, operation_ParentId = span ID, gen_ai.response.id, gen_ai.agent.id, .name, .version", theme="violet", h=160, size=20, sub_size=14, icon="otel", icon_pos="top"),
        Box(bw, "customEvents in Application Insights", sub="query with KQL; shown in the trace's Annotation history; list shows the latest plus '+X more'", theme="cyan", h=160, size=20, sub_size=14, icon="app-insights", icon_pos="top"),
    ]
    placed, b = flow(cv, 0, y, boxes, gap)
    cy = b + 40
    c1 = Card(SPAN(2), "Tags and filters", [
        "microsoft.gen_ai.human_evaluation.source = builder (portal) or end_user (app)",
        "microsoft.gen_ai.evaluation.actor.type = human",
        "Filter the trace list by evaluation name, score or label, and source",
    ], theme="violet", icon="tag", badge="preview", src=src("annot"))
    c2 = Card(SPAN(2), "Writing needs telemetry-write rights", [
        "With Entra ingestion the identity needs Monitoring Metrics Publisher",
        "Another trace-reader role does not grant telemetry-write access",
        "! External agents cannot use human evaluation",
    ], theme="red", icon="managed-identity", src=src("annot", "entra"))
    c3 = Card(SPAN(2), "Programmatic feedback", [
        "Emit the gen_ai.evaluation.result event inside the same trace and span context, with gen_ai.evaluation.name, score.value and score.label",
        "Correlate with gen_ai.response.id and the agent attributes",
        "Read it back with KQL on customEvents",
    ], theme="violet", icon="code", src=src("annot"))
    _, b2 = row(cv, 0, cy, [c1, c2, c3], gap=GUT)
    return b2 + 10


# ---------------------------------------------------------------------------------------------- 5. sensitive content
def sensitive(cv, y):
    y = sec(cv, y, "5  Restrict who can read prompts and responses (preview)",
            sub="Seven GenAI attributes are written to a dedicated table, AppGenAIContent, which you can protect with RBAC. The 2026-09-30 cut-over has passed as of 2026-11-03.") + 40
    LW = 1500
    kinds = Table([("Attribute", 560), "Why it is sensitive"], [
        [("gen_ai.input.messages", "red"), "Prompt and input messages sent to the model"],
        [("gen_ai.output.messages", "red"), "Model responses and output messages"],
        [("gen_ai.system_instructions", "red"), "System instructions provided to the model"],
        [("gen_ai.tool.definitions", "red"), "Definitions of tools available to the model"],
        [("gen_ai.tool.call.arguments", "red"), "Arguments passed to a tool call"],
        [("gen_ai.tool.call.result", "red"), "Result returned from a tool call"],
        [("gen_ai.evaluation.explanation", "red"), "Explanation produced during model evaluation"],
    ], w=LW, theme="red", size=15, head_size=16, title="The seven sensitive attributes", title_size=20)
    kinds.place(cv, 0, y)
    ly = learn_line(cv, 0, kinds.bottom + 8, src("sens"))
    with cv.panel(0, ly + 26, w=LW, title="Protect it in four steps", theme="red", style="solid", fill="soft", pad=22, title_size=21) as st:
        step_list(cv, st.ix, st.iy, LW - 44, [
            "Register the feature flag for early opt-in: az feature register --namespace Microsoft.Insights --name protectGenAISensitiveData (needs Subscription Owner or Microsoft.Features/* actions).",
            "Set the AppGenAIContent table's protection level to Protected: deny by default, immediate effect for standard read and custom roles (needs Log Analytics Contributor).",
            "Grant Privileged Monitoring Data Reader on the Application Insights resource linked to the project: enough for both Application Insights and Foundry views. Add it on the Log Analytics workspace only for workspace-centric KQL. PIM and just-in-time access work.",
            "Verify: a user with only Log Analytics Reader sees the trace but not the content; a Privileged Monitoring Data Reader sees both.",
        ], theme="red")
    rx = LW + GUT
    rw = W - rx
    tl_y = y
    cv.text(rx, tl_y, "Where the seven attributes are written", size=22, color=get_theme("red").deep)
    t = Table([("When", 330), ("Existing tables", 480), "AppGenAIContent"], [
        [("Before 2026-09-30", "gray"), "Values written to AppDependencies, AppTraces and AppEvents", "Values also written here"],
        [("From 2026-09-30 (has passed as of 2026-11-03)", "red"), "Newly ingested data keeps the attribute keys, but the values become a short pointer", "Read the values here"],
        [("2027-09-30", "yellow"), "The temporary opt-out flag optOutProtectGenAISensitiveData is discontinued", "Only destination, whatever the flag says"],
    ], w=rw, theme="red", size=14, head_size=15, title=None)
    t.place(cv, rx, tl_y + 36)
    n1 = Note(rw, "Data ingested before 2026-09-30 stays where it was and stays queryable. Built-in Application Insights and Foundry experiences keep working. Update custom queries, alert rules, dashboards and workbooks that read these values from AppDependencies, AppTraces or AppEvents.",
              kind="warn", title="Update your KQL", size=15, src=src("sens"))
    n1.place(cv, rx, t.bottom + 24)
    n2 = Note(rw, "The page still uses future tense for the 2026-09-30 change, so whether the early-opt-in flag is still needed on your account is unverified: check your own Application Insights.",
              kind="warn", title="Docs disagree with the calendar", size=15)
    n2.place(cv, rx, n1.bottom + 22)
    n3 = Note(rw, "If a custom role has one of two AzMon DataActions that allow access to protected tables, anyone with that role gets the access.",
              kind="info", title="Custom roles", size=15)
    n3.place(cv, rx, n2.bottom + 22)
    return max(st.bottom, n3.bottom) + 10


# ---------------------------------------------------------------------------------------------- 6. data handling + retention
def data_handling(cv, y):
    y = sec(cv, y, "6  Data handling and retention",
            sub="Traces can hold customer data. Tracing is off until an owner turns it on, and your Application Insights settings decide how long data stays.") + 40
    c1 = Card(SPAN(2), "What tracing captures", [
        "User inputs and prompts, agent and model inputs and outputs",
        "Tool calls and intermediate steps, execution metadata",
        "Customer Data that might contain personal data",
    ], theme="violet", icon="otel", src=src("data"))
    c2 = Card(SPAN(2), "On, off and who sees it", [
        "Off by default: only a Foundry Account Owner or Foundry Owner can enable it by connecting Application Insights, at project creation or later",
        "Disable by disconnecting or removing Application Insights; existing data stays for its retention period",
        "Viewers need project access plus read on Application Insights or the Log Analytics workspace (Log Analytics Reader, Monitoring Reader or Reader)",
    ], theme="red", icon="managed-identity", src=src("data"))
    c3 = Card(SPAN(2), "Controls and your responsibilities", [
        "Controls: PII redaction, restrict Log Analytics Reader and Privileged Monitoring Data Reader, configurable capture policies",
        "You: inform end users, comply with the rules that apply to you, and configure access and retention",
    ], theme="gray", icon="compliance", src=src("data"))
    _, b = row(cv, 0, y, [c1, c2, c3], gap=GUT)
    cy = b + 40
    ret = Table([("Window", 360), ("What it is", 640), "Where it comes from"], [
        [("Out-of-the-box traces: 90 days", "violet"), "What the Foundry Traces UI shows for server-side traces", "Setup and concepts pages"],
        [("Retention and sampling", "cyan"), "How long spans stay in Application Insights and Log Analytics, and what is sampled", "Your Application Insights and Log Analytics configuration"],
        [("VS Code cloud query: 7 days", "gray"), "The cloud trace-detail query window in the Foundry Toolkit - not retention", "VS Code tracing page"],
        [("Ingestion delay: 2-5 minutes", "yellow"), "Typical time for a new trace to appear (Application Insights ingests spans in 30-90 seconds for dataset jobs)", "Setup page"],
    ], w=SPAN(4), theme="violet", size=15, head_size=16, title="Retention and time windows", title_size=20)
    ret.place(cv, 0, cy)
    ly = learn_line(cv, 0, ret.bottom + 8, src("setup", "data", "vsc"))
    n = Note(SPAN(2), "Both statements appear in the docs - the Foundry UI shows the last 90 days, and retention follows your Application Insights or Log Analytics configuration - and the docs do not explain how they interact. "
                      "Do not assume 90 days is your retention: check the Application Insights and workspace settings.",
             kind="warn", title="Docs disagree: 90 days versus retention", size=15, src=src("concept"))
    n.place(cv, SPAN(4) + GUT, cy)
    return max(ly, n.bottom) + 10


# ---------------------------------------------------------------------------------------------- 7. VS Code
def vscode(cv, y):
    y = sec(cv, y, "7  Tracing in VS Code with the Foundry Toolkit",
            sub="Three approaches, from a live local view to the traces of a hosted agent.") + 40
    a = Card(SPAN(2), "Agent Inspector", [
        "Live local view of request and tool events, with breakpoints",
        "No OTLP needed",
    ], theme="gray", icon="vscode", src=src("vsc"))
    b = Card(SPAN(2), "Local tracing", [
        "Foundry Toolkit > Developer Tools > Monitor > Tracing > Start Collector",
        "Collector endpoints: OTLP gRPC http://localhost:4317; OTLP HTTP http://localhost:4318/v1/traces and /v1/logs",
        "Local store: SQLite traces.db under .aitk\\tracing in the user home",
    ], theme="violet", icon="otel", src=src("vsc"))
    c = Card(SPAN(2), "Hosted-agent tracing", [
        "Queries the connected Application Insights",
        "The cloud trace-detail query covers the last 7 days (a query window, not retention)",
    ], theme="green", icon="agent", src=src("vsc"))
    _, b2 = row(cv, 0, y, [a, b, c], gap=GUT)
    n = Note(W, "Supported instrumentation examples: Agent Framework (built in), Azure AI Inference SDK (preview), Foundry Projects SDK (client instrumentor, preview), Anthropic, LangChain and OpenAI SDKs through OpenLLMetry / Traceloop (non-Microsoft), Google GenAI and the OpenAI Agents SDK.",
             kind="info", title="What can be instrumented", size=15, src=src("vsc"))
    n.place(cv, 0, b2 + 28)
    return n.bottom + 10


# ---------------------------------------------------------------------------------------------- 8. gotchas
def notes(cv, y):
    y = sec(cv, y, "8  Gotchas to remember", sub="Preview status follows each feature's Learn page as of 2026-11-03.") + 36
    n = lambda kind, title, text, *keys: Note(COL, text, kind=kind, title=title, size=15, src=src(*keys))
    items = [
        n("preview", "Preview in this sheet", "Client-side tracing, framework integrations, Trace Replay, human annotations and sensitive-content restriction are preview. Re-check before you publish.", "client", "replay"),
        n("gotcha", "External agents: no datasets, no human evaluation", "Traces to dataset, human evaluation and red teaming do not work for external agents (preview kind).", "todata", "annot"),
        n("warn", "Public network access needed", "Traces to dataset needs Application Insights with public query access, even behind a private link scope; there is no private-only path.", "todata"),
        n("warn", "Update custom KQL after 2026-09-30", "Values of the seven attributes are now pointers in AppDependencies, AppTraces and AppEvents for new data; read AppGenAIContent instead.", "sens"),
        n("info", "Python-only features", "Trace-context propagation, @trace_function and the LangChain integration are Python only.", "client", "fw"),
        n("warn", "Content recording is dev-only", "Recommended off in production; @trace_function ignores the flag, baggage can leak personal data and context propagation sends trace IDs to Azure services.", "client"),
    ]
    _, b = row(cv, 0, y, items, gap=GUT)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, b = title_block(cv, 0, 0, "Tracing: client-side, replay, datasets and privacy",
                       "What happens after a trace exists: add client spans, replay, turn traces into datasets, annotate, protect content - part 2 of 2 (as of 2026-11-03)",
                       icon="otel", w=W)
    y = b + 26
    legend(cv, 0, y, [("Agents", "green"), ("Spans, replay and datasets", "violet"), ("Application Insights and data", "cyan"),
                      ("Identity and access", "red"), ("Neutral", "gray")])
    cv.text(2400, y, "Dashed border = preview. Part 1 covers the pipeline and setup.", size=15, color=MUTED)
    y = client_side(cv, y + 60)
    y = replay(cv, y + SEC)
    y = to_dataset(cv, y + SEC)
    y = annotations(cv, y + SEC)
    y = sensitive(cv, y + SEC)
    y = data_handling(cv, y + SEC)
    y = vscode(cv, y + SEC)
    y = notes(cv, y + SEC)
    sources(cv, 0, y + SEC, [L["client"], L["fw"], L["replay"], L["todata"], L["annot"], L["sens"], L["data"], L["setup"], L["entra"], L["vsc"], L["concept"], L["ext"], L["evalregions"]],
            w=W, cols=3)
