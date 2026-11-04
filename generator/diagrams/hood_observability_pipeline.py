"""Under the hood: the telemetry pipeline - emitters, two identities, ingestion, protected table, and the views built on top.

Evidence convention (same as the other 'under the hood' canvases):
  solid border + hatch  = documented on Microsoft Learn
  dashed border + soft  = only a video / blog says it (labelled "(video/blog)")
  dotted grey + "?"     = not documented anywhere checked
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-observability-pipeline",
    title="Observability pipeline: telemetry under the hood",
    section="8", order=8,
    description="How one agent run becomes a trace: who emits which spans (the Agent Service with the project managed identity, "
                "your sandbox code with the agent identity), Application Insights ingestion with Entra auth, the protected "
                "AppGenAIContent table, retention and data handling, and how the portal builds Traces, Monitor and evaluations.",
    tags=["observability", "opentelemetry", "application insights", "tracing", "hosted agents", "appgenaicontent"],
)

W = 3160
GREY = "#868e96"
GA_C = "#2f9e44"      # data path
ID_C = "#e03131"      # identity / credential on a hop

# ---------------------------------------------------------------- citations (label, url)
L_CONCEPT = ("Agent tracing overview", learn("observability/concepts/trace-agent-concept"))
L_DATA = ("Trace data: collection, storage and access", learn("observability/concepts/trace-data"))
L_SETUP = ("Set up tracing in Foundry", learn("observability/how-to/trace-agent-setup"))
L_ENTRA = ("Entra authentication for trace ingestion (preview)", learn("observability/how-to/trace-ingestion-entra-authentication"))
L_SENS = ("Restrict access to sensitive trace content (preview)", learn("observability/how-to/traces-sensitive-content"))
L_DASH = ("Monitor agents with the Agent Monitoring Dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard"))
L_OBS = ("Observability in generative AI", learn("concepts/observability"))
L_HOSTED_OTEL = ("Configure hosted agent telemetry", learn("agents/how-to/configure-hosted-agent-telemetry"))
L_PERMS = ("Hosted agent permissions reference", learn("agents/concepts/hosted-agent-permissions"))
L_NETISO = ("Configure network isolation (firewall allow-listing)", learn("how-to/configure-private-link"))
L_MVNET = ("Configure managed virtual network", learn("how-to/managed-virtual-network"))
L_ARCH = ("Foundry architecture", learn("concepts/architecture"))

U_DEM341 = "https://www.youtube.com/watch?v=WprbDyANqy0"
U_BRK252 = "https://www.youtube.com/watch?v=a7FELS8hQAE"
U_BRK205 = "https://www.youtube.com/watch?v=oOO6OG4biEY"
U_MECH = "https://www.youtube.com/watch?v=iR7_57lJOz8"
U_REACTOR = "https://www.youtube.com/watch?v=8N7q0Ucr3rw"


# ---------------------------------------------------------------- evidence-styled blocks
def retag(card, prefix):
    """Card.src lines always read 'Learn: ...'; relabel them for video / blog evidence."""
    card.src_lines = [(t.replace("Learn: ", f"{prefix}: ", 1), u, y) for (t, u, y) in card.src_lines]
    return card


def vb(w, title, body, *, theme="yellow", src=(), prefix="Video", **kw) -> Card:
    """Video / blog only: dashed border, soft fill, '(video/blog)' in the title."""
    return retag(Card(w, "(video/blog) " + title, body, theme=theme, dash="dashed", fill="soft", src=src, **kw), prefix)


def nd(w, title, body, **kw) -> Card:
    """Not documented: dotted grey, empty fill, '?' in the title."""
    body = [("para", b) for b in ([body] if isinstance(body, str) else body)]
    kw.setdefault("title_color", GREY)
    return Card(w, "? " + title, body, theme="gray", dash="dotted", fill="none", body_color=MUTED, **kw)


def nd_box(w, label, sub, h=None) -> Box:
    return Box(w, "? " + label, sub=sub, theme="gray", dash="dotted", fill="none", size=17, sub_size=14, h=h)


def evidence_key(cv: Canvas, right: float, y: float) -> None:
    specs = [("solid", "Documented on Learn", ""), ("dashed", "Video or blog only (video/blog)", ""),
             ("dotted", "Not documented", "?")]
    widths = [64 + 14 + text_size(s[1], 15)[0] for s in specs]
    total = sum(widths) + 36 * (len(specs) - 1)
    x = right - total
    cv.text(x, y, "Evidence key", size=15, color=MUTED)
    cx, cy = x, y + 26
    for (dash, label, mark), w in zip(specs, widths):
        if dash == "solid":
            cv.rect(cx, cy, 64, 32, stroke="#6741d9", fill="#d0bfff", style="hachure", sw=2)
        elif dash == "dashed":
            cv.rect(cx, cy, 64, 32, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, cy, 64, 32, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            mw, mh = text_size(mark, 20)
            cv.text(cx + (64 - mw) / 2, cy + (32 - mh) / 2, mark, size=20, color=GREY)
        cv.text(cx + 78, cy + 5, label, size=15, color=INK)
        cx += w + 36


def banner(cv: Canvas, y: float, letter: str, title: str, sub: str, theme: str = "violet") -> float:
    """Section banner with a lettered marker; returns the y where content can start."""
    numbered(cv, 24, y + 30, letter, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 62, y, title, sub, size=34, sub_size=17, w=W - 62)
    return bottom + 20


def tile(cv: Canvas, x, y, w, h, big, caption, theme, kind="doc") -> None:
    th = THEMES[theme]
    if kind == "doc":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y, w, h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
    cv.text(x, y + 10, big, size=36, color=th.deep if kind != "nd" else GREY, align="center", w=w)
    lines = wrap_text(caption, (w - 34) * 0.96, 15)
    cv.text(x + 17, y + 10 + 36 * 1.25 + 2, "\n".join(lines), size=15, color=INK if kind != "nd" else MUTED,
            align="center", w=w - 34)
    cv.register("tile", x, y, w, h)


def see_also(cv: Canvas, right: float, y: float, labels) -> None:
    """Right-aligned 'See also' chips that name sibling canvases by their gallery titles."""
    chips = [Chip(lab, theme="gray", size=14, pad_x=10, pad_y=4) for lab in labels]
    head = "See also (other canvases):"
    hw = text_size(head, 14)[0]
    total = hw + 12 + sum(c.w for c in chips) + 10 * (len(chips) - 1)
    x = right - total
    cv.text(x, y + 6, head, size=14, color=MUTED)
    cx = x + hw + 12
    for c in chips:
        c.place(cv, cx, y)
        cx += c.w + 10


def arrow_key(cv: Canvas, x: float, y: float, entries) -> None:
    for color, label, dash in entries:
        arrow(cv, [(x, y + 11), (x + 64, y + 11)], color=color, sw=3, dash=dash)
        t = cv.text(x + 76, y, label, size=15, color=INK)
        x += 76 + t.w + 34


class Steps(Rect2):
    """A card whose rows carry the same numbered circles used on the diagram (the legend for the markers)."""

    def __init__(self, w, title, steps, *, theme="violet", size=15, pad=16, d=30, src=(), title_size=20, min_h=0):
        self.th = THEMES[theme]
        self.theme, self.w, self.title, self.size, self.pad, self.d, self.title_size = (
            theme, w, title, size, pad, d, title_size)
        lr = metrics.line_ratio()
        tw = (w - 2 * pad - d - 12) * 0.965
        y = pad + title_size * lr + 10
        self.rows = []
        for n, text in steps:
            lines = wrap_text(text, tw, size)
            h = max(len(lines) * size * lr, d)
            self.rows.append((n, lines, y, h))
            y += h + 9
        y -= 9
        self.src_lines = []
        if src:
            y += 8
            for label, url in src:
                lines = wrap_text(f"Learn: {label}", w - 2 * pad, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * 12 * lr + 2
            y -= 2
        self.h = max(y + pad, min_h)
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "Steps":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        lr = metrics.line_ratio()
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=self.th.deep)
            for n, lines, ry, rh in self.rows:
                numbered(cv, x + self.pad + self.d / 2, y + ry + self.d / 2, n, theme=self.theme, d=self.d, size=15)
                th_ = len(lines) * self.size * lr
                cv.text(x + self.pad + self.d + 12, y + ry + (rh - th_) / 2, "\n".join(lines), size=self.size)
            for txt, url, sy in self.src_lines:
                cv.text(x + self.pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


# ====================================================================== build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "Observability pipeline: telemetry under the hood",
        "Who emits which spans, under which identity, how they reach Application Insights, and how the portal builds its views - as documented on Learn (as of 2026-11-03)",
        w=W)
    evidence_key(cv, W, 6)

    y = strip(cv, bottom + 40)
    y = section_a(cv, y + 56)
    y = section_b(cv, y + 60)
    y = section_c(cv, y + 60)
    y = section_d(cv, y + 60)
    y = section_e(cv, y + 60)
    y = section_f(cv, y + 60)
    y = section_sources(cv, y + 60)


# ---------------------------------------------------------------- summary strip
def strip(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Seven things to hold in your head", size=30, w=W)
    see_also(cv, W, y + 2, ["Tracing: from agent run to the Traces UI", "Foundry Observability: one data model"])
    y += 62
    tiles = [
        ("2 emitters", "A hosted agent's spans come from the Agent Service (project managed identity) and from your sandbox code (agent identity)",
         "green", "doc"),
        ("Off by default", "Nothing is collected until an Account Owner or Owner connects Application Insights; then every agent in the project is traced",
         "violet", "doc"),
        ("1 connection", "Only one Application Insights connection per project: update the existing one instead of adding another",
         "violet", "doc"),
        ("7 attributes", "Prompts, responses, system instructions and tool data go to the protected AppGenAIContent table (preview)",
         "red", "doc"),
        ("2026-09-30", "Routing change date, already past: old tables now keep a pointer, not the content, for newly ingested data",
         "red", "doc"),
        ("Foundry roles", "Foundry User and the other Foundry roles cannot read traces: you need Monitoring or Log Analytics access too",
         "red", "doc"),
        ("? rebuild", "How the portal reconstructs a trace from the spans is not documented, only the access it needs",
         "gray", "nd"),
    ]
    gap = 28
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + gap), y, tw, 150, big, cap, th, kind)
    return y + 150


# ---------------------------------------------------------------- A: the pipeline
LABW = 232
EX, EW = 258, 420          # emit column
XX, XW = 748, 390          # export column
IX, IW = 1308, 420         # ingest column (170 px gutter before it carries the credential labels)
SX, SW = 1828, 540         # store column
BUSX = 2458                # bus that fans out to the readers
RX = 2528
RW = W - RX                # read column
LH = 238                   # lane height
LG = 14


def lane_band(cv: Canvas, y: float, title: str, sub: str, theme: str, icon: str, h: float = LH, dash="dotted", w: float = W) -> None:
    th = THEMES[theme]
    cv.rect(0, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=1.5, dash=dash, rough=0)
    place_icon(cv, icon, 16, y + 14, 34)
    lines = wrap_text(title, LABW - 24, 20)
    cv.text(16, y + 56, "\n".join(lines), size=20, color=th.deep)
    cv.text(16, y + 62 + len(lines) * 25, "\n".join(wrap_text(sub, LABW - 24, 14)), size=14, color=MUTED)


def col_head(cv: Canvas, x: float, y: float, w: float, title: str, sub: str, theme: str = "violet") -> None:
    th = THEMES[theme]
    cv.text(x, y, title, size=22, color=th.deep)
    cv.text(x, y + 28, "\n".join(wrap_text(sub, w, 14)), size=14, color=MUTED)
    cv.line((x, y + 25), (x + w, y + 25), stroke=th.stroke, sw=2)


def section_a(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "A", "One agent run, hop by hop: from a span to a trace in the portal",
               "Read left to right: who emits, how it is exported and authenticated, where it lands, who can read it. Numbers match the "
               "steps card under the diagram.")
    arrow_key(cv, W - 1030, y0 + 14, [(GA_C, "green: telemetry data path", "solid"), (ID_C, "red: the credential on that hop", "solid"),
                                       (GREY, "grey dashed: optional or video/blog", "dashed")])

    # ---- hop 0: switch it on (control plane), four small cards
    cw = (W - 3 * 36) / 4
    zero = [
        Card(cw, "Connect Application Insights", [
            "A Foundry Account Owner or Owner connects it to the project. Until then tracing is OFF and nothing is collected",
            "Then data is collected for ALL agents in the project. One connection per project",
        ], theme="violet", title_size=18, body_size=14, gap=4, pad=12, src=[L_DATA]),
        Card(cw, "Auth type: project managed identity", [
            "Preview. The portal assigns Monitoring Metrics Publisher to the project's managed identity on the App Insights resource",
            "Disable local (key) authentication to enforce Entra-only ingestion",
        ], theme="red", badge="preview", title_size=18, body_size=14, gap=4, pad=12, src=[L_ENTRA]),
        Card(cw, "Hosted agents: grant the agent identity too", [
            "Assign Monitoring Metrics Publisher to the Agent Identity on the same App Insights resource, in the portal or with "
            "az role assignment create",
            "Without it, spans from your sandbox code are rejected (Forbidden)",
        ], theme="red", badge="preview", title_size=18, body_size=14, gap=4, pad=12, src=[L_ENTRA]),
        Card(cw, "The platform injects the connection string", [
            "APPLICATIONINSIGHTS_CONNECTION_STRING goes into every hosted agent container, only while project monitoring is on",
            "It is reserved: you cannot set or override it in agent.yaml",
        ], theme="green", title_size=18, body_size=14, gap=4, pad=12, src=[L_HOSTED_OTEL]),
    ]
    zh = max(c.h for c in zero)
    numbered(cv, 18, y + 12, 0, theme="violet", d=30, size=17)
    cv.text(42, y, "Switch it on (control plane, once per project)", size=20, color=THEMES["violet"].deep)
    zy = y + 34
    for i, c in enumerate(zero):
        c.place(cv, i * (cw + 36), zy, h=zh)
    y = zy + zh + 40

    # ---- column headings of the conveyor
    heads = [(EX, EW, "1  Emit", "who creates spans"), (XX, XW, "2  Export", "OpenTelemetry exporters"),
             (IX, IW, "3  Ingest", "Application Insights endpoint"), (SX, SW, "4  Store", "your Azure Monitor resources"),
             (RX, RW, "5  Read", "who builds views from it")]
    for hx, hw, ht, hs in heads:
        col_head(cv, hx, y, hw, ht, hs)
    y += 66

    # ---- lanes (left part only: emitters and exporters)
    heights = [LH, LH, LH, 214]
    ly, cur = [], y
    for h_ in heights:
        ly.append(cur)
        cur += h_ + LG
    lanes = [
        ("External agent", "your app, any framework or cloud (preview)", "gray", "api", "dashed"),
        ("Foundry Agent Service", "server side, inside the platform", "green", "agent", "dotted"),
        ("Hosted agent sandbox", "your code in the per-session sandbox", "green", "container-apps", "dotted"),
        ("Optional 2nd destination", "any OpenTelemetry-compliant endpoint or collector", "gray", "monitor", "dashed"),
    ]
    lane_w = IX - 62
    for i, (t, s, th, icon, dsh) in enumerate(lanes):
        lane_band(cv, ly[i], t, s, th, icon, h=heights[i], dash=dsh, w=lane_w if i < 3 else IX + IW + 30)

    BH = 176
    def at(i):  # top y of a box row inside lane i
        return ly[i] + (heights[i] - BH) / 2

    # external lane (video / blog)
    e0 = Box(EW, "(video/blog) OpenTelemetry distro in your app",
             sub="A few lines: enable Azure Monitor, set the connection string and framework, and register an agent ID so the traces "
                 "correlate in Foundry. Learn: external agents are in preview",
             theme="yellow", fill="soft", dash="dashed", size=18, sub_size=14, h=BH).place(cv, EX, at(0))
    x0 = Box(XW, "(video/blog) Azure Monitor export", sub="Traces go to Application Insights, which stores Foundry's traces in Azure Monitor",
             theme="yellow", fill="soft", dash="dashed", size=18, sub_size=14, h=BH).place(cv, XX, at(0))
    # Agent Service lane
    e1 = Box(EW, "Agent Service emits server-side spans",
             sub="Prompt agents, hosted agents and workflows are traced with no code changes once App Insights is connected. "
                 "Root span: invoke_agent", theme="green", fill="hatch", size=18, sub_size=14, h=BH).place(cv, EX, at(1))
    x1 = Box(XW, "Exported with the project managed identity",
             sub="Learn: the service emits server-side traces 'by using project managed identity'", theme="violet", fill="hatch", size=18,
             sub_size=14, h=BH).place(cv, XX, at(1))
    # hosted sandbox lane
    e2 = Box(EW, "Protocol library and your code emit spans",
             sub="The Responses and Invocations libraries bundle the OpenTelemetry distro: traces, logs and metrics with no setup in "
                 "your code. service.name is forced to the agent's name (cloud_RoleName)",
             theme="green", fill="hatch", size=18, sub_size=14, h=BH).place(cv, EX, at(2))
    x2 = Box(XW, "Application Insights exporter, batched",
             sub="On when the platform-injected connection string exists; auth is the agent identity. Allow a few seconds. "
                 "OTEL_TRACES_SAMPLER samples spans only: logs are always exported",
             theme="violet", fill="hatch", size=18, sub_size=14, h=BH).place(cv, XX, at(2))
    # optional OTLP lane
    x3 = Box(XW, "OTLP exporter (optional)",
             sub="Set OTEL_EXPORTER_OTLP_ENDPOINT (+ _PROTOCOL, _HEADERS) on the agent version. It runs next to the App Insights exporter",
             theme="gray", fill="soft", dash="dashed", size=18, sub_size=14, h=BH - 20).place(cv, XX, ly[3] + (heights[3] - (BH - 20)) / 2)
    ox = Box(IW, "Any OTLP endpoint or collector", sub="A third party receives prompt, tool and response content, depending on your "
                                                     "instrumentation: review its data handling",
             theme="gray", fill="soft", dash="dashed", size=18, sub_size=14, h=BH - 20).place(cv, IX, ly[3] + (heights[3] - (BH - 20)) / 2)

    # ---- ingestion, storage and readers: three tall columns beside lanes 0-2
    top3, bot3 = ly[0], ly[2] + heights[2]
    ing = Box(IW, "Application Insights ingestion", theme="violet", fill="hatch", size=22, h=bot3 - top3, icon="app-insights",
              icon_pos="top", icon_size=40)
    ing.place(cv, IX, top3)
    ix = IX + 22
    iy = top3 + 96
    ing_lines = [
        ("Entra token (preview)", "Each sending identity needs Monitoring Metrics Publisher. With local auth disabled, ingestion is Entra-only", "#c92a2a"),
        ("Key-based", "The connection string authenticates while local authentication is still on", MUTED),
        ("After a role change", "Wait 2 to 5 minutes. A 'Forbidden' from the exporter points at a missing role or a local-auth mismatch", MUTED),
    ]
    for head, body, col in ing_lines:
        cv.text(ix, iy, head, size=16, color=col)
        iy += 22
        lines = wrap_text(body, IW - 44, 14)
        cv.text(ix, iy, "\n".join(lines), size=14, color=INK)
        iy += len(lines) * 17.5 + 14

    with cv.panel(SX, top3, title="Your Application Insights + Log Analytics", sub="retention, sampling and billing follow YOUR configuration",
                  theme="violet", style="dotted", fill="none", w=SW, h=bot3 - top3, pad=18, title_size=20, sub_size=14) as ps:
        std = Box(SW - 36, "AppDependencies, AppTraces, AppEvents", sub="The standard telemetry tables. For newly ingested data the seven "
                                                                       "sensitive attribute KEYS stay here, with a short pointer as the value",
                  theme="violet", fill="hatch", size=18, sub_size=14, h=130).place(cv, ps.ix, ps.iy + 4)
        sec = Box(SW - 36, "AppGenAIContent (set it to Protected)",
                  sub="Dedicated table for gen_ai.input.messages, output.messages, system_instructions, tool.definitions, tool.call.arguments, "
                      "tool.call.result and evaluation.explanation",
                  theme="red", fill="hatch", size=18, sub_size=14, h=166).place(cv, ps.ix, ps.iy + 4 + 130 + 56)
        who = Card(SW - 36, "Who reads what", [
            "Standard tables: Log Analytics Reader, Monitoring Reader or Reader",
            "Protected table: also Privileged Monitoring Data Reader",
            "Foundry roles cannot read traces",
        ], theme="gray", title_size=16, body_size=13, pad=10, gap=3, bullet=None, src=[L_DATA])
        who.place(cv, ps.ix, sec.bottom + 18)

    # ---- readers: six boxes
    rd = [
        ("Foundry Traces and Trajectories", "The trace tree under one invoke_agent root. Out-of-the-box traces for the past 90 days (as of 2026-11-03)",
         "violet", "doc", None),
        ("Monitor tab (preview)", "Token usage, latency (flagged above 10 s), run success rate (flagged below 95%), evaluation scores, red-team results",
         "violet", "doc", None),
        ("Evaluations", "Continuous evaluation samples live traffic; recurring evaluations (preview) run on a schedule; red-team scans (preview)",
         "violet", "doc", 6),
        ("Alerts (preview)", "On latency, token usage, evaluation scores or red-team findings", "violet", "doc", 7),
        ("Azure portal: Application Insights", "Investigate > Transaction search or Performance, plus your own KQL", "violet", "doc", None),
        ("(video/blog) Control Plane fleet views", "Aggregate the same telemetry across agents: cost, health and success rates", "yellow", "vb", None),
    ]
    rh = (bot3 - top3 - 5 * 14) / 6
    rboxes = []
    for i, (lab, sub, th, kind, n) in enumerate(rd):
        if kind == "vb":
            b = Box(RW, lab, sub=sub, theme=th, fill="soft", dash="dashed", size=18, sub_size=14, h=rh)
        else:
            b = Box(RW, lab, sub=sub, theme=th, fill="hatch", size=18, sub_size=14, h=rh)
        b.place(cv, RX, top3 + i * (rh + 14))
        if n is not None:
            numbered(cv, b.x + 22, b.y + 4, n, theme="violet", d=32, size=18)
        rboxes.append(b)

    # ---- arrows
    gc = GA_C
    bus_i = IX - 44
    # exporters -> bus -> ingestion; the credential used on each hop is written in red above its arrow
    for xb, lab, idc in ((x0, "connection\nstring", GREY), (x1, "project\nmanaged\nidentity", ID_C), (x2, "agent\nidentity", ID_C)):
        arrow(cv, [(xb.right + 6, xb.cy), (bus_i, xb.cy)], color=gc, sw=2, end_head=None, dash="dashed" if xb is x0 else "solid")
        tw, th_ = text_size(lab, 14)
        cv.text((xb.right + bus_i) / 2 - tw / 2, xb.cy - th_ - 6, lab, size=14, color=idc, align="center", w=tw)
    c3y = (x0.cy + x1.cy) / 2
    arrow(cv, [(bus_i, x0.cy), (bus_i, c3y - 17)], color=gc, sw=2, end_head=None, dash="dashed")
    arrow(cv, [(bus_i, c3y + 17), (bus_i, x2.cy), (ing.x - 6, x2.cy)], color=gc, sw=2)
    arrow(cv, [(bus_i, x1.cy), (ing.x - 6, x1.cy)], color=gc, sw=2)
    numbered(cv, bus_i, c3y, 3, theme="violet", d=32, size=18)
    # emit -> export
    for a, b in ((e0, x0), (e1, x1), (e2, x2)):
        connect(cv, a, b, sw=2, color=gc, dash="dashed" if a is e0 else "solid")
    # optional OTLP branch: hosted exporter -> OTLP exporter -> endpoint
    connect(cv, x2, x3, a_side="bottom", b_side="top", dash="dashed", sw=2, color=GREY, label="also", label_size=14)
    connect(cv, x3, ox, dash="dashed", sw=2, color=GREY)
    # ingestion -> storage (the split into two tables)
    arrow(cv, [(ing.right + 6, std.cy), (SX - 6, std.cy)], color=gc, sw=2)
    c4x = (ing.right + SX) / 2
    arrow(cv, [(ing.right + 6, sec.cy), (c4x - 17, sec.cy)], color=ID_C, sw=2, end_head=None)
    arrow(cv, [(c4x + 17, sec.cy), (SX - 6, sec.cy)], color=ID_C, sw=2)
    numbered(cv, c4x, sec.cy, 4, theme="red", d=32, size=18)
    cv.text(c4x - 40, sec.cy + 24, "the 7\nattributes", size=14, color="#c92a2a", align="center", w=80)
    # storage -> readers bus
    bx = BUSX
    ym = (std.cy + sec.cy) / 2
    c5x = (SX + SW + bx) / 2
    arrow(cv, [(SX + SW + 6, ym), (c5x - 17, ym)], color=gc, sw=2, end_head=None)
    arrow(cv, [(c5x + 17, ym), (bx, ym)], color=gc, sw=2, end_head=None)
    numbered(cv, c5x, ym, 5, theme="violet", d=32, size=18)
    arrow(cv, [(bx, rboxes[0].cy), (bx, rboxes[-1].cy)], color=gc, sw=2, end_head=None)
    for rb in rboxes:
        arrow(cv, [(bx, rb.cy), (rb.x - 6, rb.cy)], color=gc, sw=2, dash="dashed" if rb is rboxes[-1] else "solid")

    # beside lane 4: the OTLP caution
    Note(W - SX, "Exporting over OTLP in addition to Application Insights sends the same telemetry to that provider. Telemetry can "
                 "include prompt, tool and response content, so check the provider's retention and location policies. Environment "
                 "variables are fixed per agent version: change them by creating a new version.", kind="warn",
         title="A second destination is a second data flow", size=14, title_size=16, pad=10, src=[L_HOSTED_OTEL]).place(
        cv, SX, ly[3] + 22)

    # ---- numbered steps card under the lanes
    sy = ly[3] + heights[3] + 36
    st1 = Steps(1020, "The numbers on the diagram (1 to 3)", [
        (1, "A run starts. The Agent Service emits the server-side spans (invoke_agent root) with the project managed identity"),
        (2, "Hosted agents: the container handler runs; the protocol library and your code emit more spans with the agent identity"),
        (3, "Exporters batch the spans to Application Insights; each identity needs Monitoring Metrics Publisher, or the key still works while local auth is on"),
    ], theme="violet", src=[L_ENTRA, L_CONCEPT], size=14)
    st2 = Steps(1020, "The numbers on the diagram (4 to 7)", [
        (4, "Application Insights routes the seven sensitive GenAI attributes to AppGenAIContent (set it to Protected)"),
        (5, "Foundry queries the Application Insights APIs for the viewer, who needs read access on App Insights or Log Analytics"),
        (6, "Evaluators score sampled live traffic; scores show on the Monitor tab"),
        (7, "Alerts (preview) fire on latency, token use, evaluation scores or red-team findings"),
    ], theme="violet", src=[L_DASH, L_DATA], size=14)
    h = max(st1.h, st2.h)
    st1.place(cv, 0, sy, h=h)
    st2.place(cv, 1060, sy, h=h)
    nw = W - 2120 - 40
    n5 = Note(nw, "Learn says users need access to the Foundry project plus read permission on the connected App Insights or Log "
                  "Analytics. The exact query path, and how spans are stitched into the trace tree, is not described.",
              kind="info", title="Step 5 is only partly documented", size=14, title_size=16, pad=10, src=[L_DATA])
    n5.place(cv, 2120 + 40, sy)
    return sy + h


# ---------------------------------------------------------------- B: identities and roles
def section_b(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "B", "Who may do what: identities that write, identities that read",
               "Writing and reading telemetry are two separate permission problems. Foundry's own roles solve neither.", "red")
    top = y
    # left: writers (who needs Monitoring Metrics Publisher) as a small relationship diagram
    wx = 0
    ai = Box(360, "Application Insights resource", sub="the one connected to the project", theme="violet", fill="hatch", size=19,
             sub_size=14, h=150, icon="app-insights", icon_pos="left", icon_size=36)
    pm = Box(380, "Project managed identity", sub="emits the Agent Service's server-side spans", theme="red", fill="hatch", size=19,
             sub_size=14, h=130).place(cv, wx, top + 24)
    ag = Box(380, "Agent identity", sub="emits the spans from code in the hosted agent sandbox", theme="red", fill="hatch", size=19,
             sub_size=14, h=130).place(cv, wx, top + 24 + 130 + 50)
    ai.place(cv, 1000, (pm.cy + ag.cy) / 2 - 75)
    for src_, ty_ in ((pm, 0.28), (ag, 0.72)):
        connect(cv, src_, ai, a_side="right", b_side="left", tb=ty_, route="elbow", bend=0.8, sw=2, color=ID_C)
    for src_ in (pm, ag):
        lab = "Monitoring Metrics Publisher"
        tw, th_ = text_size(lab, 14)
        cv.text(src_.right + 30, src_.cy - th_ - 6, lab, size=14, color="#c92a2a")
    pm_note = Note(1360, "The portal assigns the role to the project managed identity when you create the connection with Auth type = "
                         "Project managed identity. For hosted agents YOU assign it to the Agent Identity as well. Disable local "
                         "authentication to enforce Entra-only ingestion.", kind="key", title="Two writers, one role", size=14,
                   title_size=16, pad=10, src=[L_ENTRA])
    pm_note.place(cv, 0, top + 24 + 130 + 50 + 130 + 30)
    cm = Card(1360, "Who can connect and disconnect", [
        "Only a Foundry Account Owner or Foundry Owner enables tracing (it is off by default)",
        "Disable tracing by disconnecting or removing the Application Insights resource: no new data is collected, and history stays "
        "under the Application Insights retention policy",
        "Permission to assign roles on the App Insights resource (at least User Access Administrator) is needed to set up Entra ingestion",
    ], theme="violet", src=[L_DATA, L_ENTRA])
    cm.place(cv, 0, pm_note.bottom + 24)
    left_bottom = cm.bottom

    # right: readers matrix
    tx = 1460
    tw = W - tx
    CHECKS = CHECK
    t = Table([("Role", 400), ("Scope", 310), ("Can read the agent's telemetry?", 320), ("Note", tw - 1030)], [
        ["Owner", "Application Insights", CHECKS, ""],
        ["Contributor", "Application Insights", CHECKS, ""],
        ["Monitoring Reader", "Application Insights", CHECKS, "Its */read access reaches the underlying workspace without a workspace assignment"],
        ["Log Analytics Reader", "Log Analytics workspace", CHECKS, "From the workspace directly; Learn's setup pages also give it as the starting role on the App Insights resource"],
        ["Privileged Monitoring Data Reader", "Log Analytics workspace", CHECKS, "Required to read PROTECTED tables such as AppGenAIContent"],
        ["Foundry User", "Application Insights", CROSS, "Sees metrics, but not traces"],
        ["Foundry Account Owner", "Application Insights", CROSS, "Sees metrics, but not traces"],
        ["Foundry Project Manager", "Application Insights", CROSS, ""],
        ["Foundry Owner", "Application Insights", CROSS, ""],
    ], w=tw, theme="red", size=14, head_size=15, title="Reading telemetry: built-in roles (Learn)", title_size=22, first_col_theme="red",
        align=["left", "left", "center", "left"])
    t.place(cv, tx, top)
    w1 = Note(tw, "The sensitive-content page says to assign Privileged Monitoring Data Reader on the Application Insights resource "
                  "linked to the project, and that this is enough to view sensitive content in both App Insights and Foundry (Foundry "
                  "queries through the Application Insights APIs). The permissions table lists the same role at the workspace scope. "
                  "Assign it where your own query path needs it.", kind="warn", title="Docs differ on the scope of Privileged Monitoring Data Reader",
              size=14, title_size=16, pad=10, src=[L_SENS, L_PERMS])
    w1.place(cv, tx, t.y + t.h + 24)
    ce = Card(tw, "Continuous evaluation needs an identity too", [
        "To enable continuous evaluation rules, assign the project managed identity the Foundry User role",
        "The Learn page points to 'Set up permissions for evaluation workflows' for the full list of evaluation roles",
    ], theme="violet", src=[L_DASH])
    ce.place(cv, tx, w1.bottom + 24)
    return max(left_bottom, ce.bottom)


# ---------------------------------------------------------------- C: sensitive content and the protected table
def section_c(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "C", "Prompts and tool data: the protected table and the 2026-09-30 routing change",
               "Preview. Sensitive GenAI content leaves the standard telemetry tables and lands in a table you can lock down with RBAC.", "red")
    top = y
    LWD = 1504                       # width of the before/after column; the steps card sits to its right

    def flow(x, fy, heading, hcolor, left_sub, upper, lower, dashed_upper=False):
        """One before/after row: the 7 attributes on the left, two tables on the right."""
        cv.text(x, fy, heading, size=20, color=hcolor)
        by_ = fy + 36
        src_ = Box(330, "7 sensitive GenAI attributes", sub=left_sub, theme="red", fill="hatch", size=18, sub_size=14, h=166).place(
            cv, x, by_)
        t1_ = Box(760, upper[0], sub=upper[1], theme="violet", fill="soft" if dashed_upper else "hatch", size=18, sub_size=14,
                  h=76).place(cv, x + 450, by_)
        t2_ = Box(760, lower[0], sub=lower[1], theme="red", fill="hatch", size=18, sub_size=14, h=76).place(cv, x + 450, by_ + 90)
        connect(cv, src_, t1_, a_side="right", b_side="left", route="elbow", sw=2, color=GA_C, dash="dashed" if dashed_upper else "solid")
        connect(cv, src_, t2_, a_side="right", b_side="left", route="elbow", sw=2, color=ID_C)
        return t2_, by_ + 166

    t2b, bb = flow(0, top, "Before 2026-09-30", MUTED, "prompts, responses, system instructions, tool data, evaluation explanations",
                   ("AppDependencies, AppTraces, AppEvents", "the full values, as before"),
                   ("AppGenAIContent", "the full values as well (both copies)"))
    t2a, ba = flow(0, bb + 44, "From 2026-09-30 (already past as of 2026-11-03), newly ingested data", "#c92a2a",
                   "the same attributes from the same agents",
                   ("AppDependencies, AppTraces, AppEvents", "the attribute KEYS stay; each value is replaced by a short pointer to AppGenAIContent"),
                   ("AppGenAIContent", "the only place the values live (unless you opted out)"), dashed_upper=True)
    Box(190, "Protected", sub="deny by default", theme="red", fill="solid", size=17, sub_size=13, h=66).place(
        cv, t2a.right + 24, t2a.y + 5)

    # steps to protect, to the right of the before/after diagram
    sx = LWD
    st = Steps(W - sx, "Protect it: four steps", [
        (1, "Register the protectGenAISensitiveData feature flag (namespace Microsoft.Insights) to route content only to AppGenAIContent early"),
        (2, "Set the AppGenAIContent table's protection level to Protected: standard read and custom roles are cut off at once"),
        (3, "Grant Privileged Monitoring Data Reader to the identities that may read prompts and tool data; PIM can make it time-bound"),
        (4, "Verify: a Log Analytics Reader-only user sees the trace without its sensitive content; a Privileged Monitoring Data Reader sees it"),
    ], theme="red", size=14, src=[L_SENS])
    st.place(cv, sx, top)
    nn = Note(W - sx, "To keep the old routing a little longer, register optOutProtectGenAISensitiveData. It is temporary: after "
                      "2027-09-30 Application Insights routes the content only to AppGenAIContent regardless of the flag. Registering "
                      "flags needs a subscription Owner (or Microsoft.Features/* actions); setting protection needs Log Analytics Contributor.",
              kind="warn", title="The opt-out is temporary", size=14, title_size=16, pad=10, src=[L_SENS])
    nn.place(cv, sx, st.bottom + 22)

    # the timeline spans the full width under both
    ty = max(ba, nn.bottom) + 44
    cv.text(0, ty, "Timeline of the change (Learn)", size=20, color=THEMES["red"].deep)
    tl_bottom = timeline(cv, 40, ty + 156, W - 80, [
        ("Before 2026-09-30", "Both copies", "The seven attributes go to the old tables AND to AppGenAIContent; opt in early with protectGenAISensitiveData"),
        ("2026-09-30", "Routing change", "New data: old tables keep keys with pointers; content only in AppGenAIContent"),
        ("Now (2026-11-03)", "Today", "Update any custom KQL, alert rules and workbooks that read these attributes from the old tables"),
        ("2027-09-30", "Opt-out ends", "optOutProtectGenAISensitiveData is discontinued; content goes only to AppGenAIContent"),
    ], color=INK, size=16, label_w=680, theme="red")
    return tl_bottom


# ---------------------------------------------------------------- D: hosted agent configuration
def section_d(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "D", "Configuring the hosted-agent emitter: environment variables, not code",
               "The protocol runtime detects its exporters at startup from environment variables set on the agent version.", "green")
    top = y
    cw = 760
    c1 = Card(cw, "Which exporters run", [
        "APPLICATIONINSIGHTS_CONNECTION_STRING present: export to Application Insights (injected by the platform when monitoring is on)",
        "OTEL_EXPORTER_OTLP_ENDPOINT present: also export over OTLP; the two exporters are independent, so both can run at once",
        "To send ONLY to OTLP, disable monitoring at the project level; you cannot remove the injected setting",
    ], theme="green", src=[L_HOSTED_OTEL])
    c2 = Card(cw, "OTLP settings", [
        "OTEL_EXPORTER_OTLP_PROTOCOL: http/protobuf is the widely supported default; grpc depends on your backend",
        "OTEL_EXPORTER_OTLP_HEADERS: key=value pairs for authentication; per-signal variants exist for traces, logs and metrics",
        "Keep the secret out of agent.yaml: store it in a Custom keys project connection and reference it with a placeholder",
        "! Create the connection BEFORE you deploy the version, or the placeholder resolves to an empty value",
    ], theme="orange", src=[L_HOSTED_OTEL])
    c3 = Card(cw, "Things the platform decides", [
        "service.name is fixed to the agent's name (cloud_RoleName in App Insights); OTEL_SERVICE_NAME has no effect",
        "Environment variables are immutable once the version exists: change the destination by creating a new version",
        "OTEL_TRACES_SAMPLER and the other standard variables tune exporter behaviour; sampling affects spans only, never logs",
        "Export is batched: allow a few seconds before data appears",
    ], theme="gray", src=[L_HOSTED_OTEL])
    c4 = Card(cw, "Where to look", [
        "Application Insights: Investigate > Transaction search or Performance",
        "Foundry portal: the Traces tab and the playground's Trajectories tab",
        "Learn: tracing is generally available for prompt and hosted agents; workflow and external agents are in preview",
    ], theme="violet", src=[L_HOSTED_OTEL, L_CONCEPT])
    h = max(c.h for c in (c1, c2, c3, c4))
    for i, c in enumerate((c1, c2, c3, c4)):
        c.place(cv, i * (cw + 40), top, h=h)
    y2 = top + h + 40
    # allow-listing table
    t = Table([("Scenario", 380), ("FQDNs and service tags", 1010), ("What it is for", 760)], [
        ["Evaluations and Traces with an Application Insights resource",
         "settings.sdk.monitor.azure.com, *.livediagnostics.monitor.azure.com, *.in.applicationinsights.azure.com, AzureMachineLearning service tag",
         "Sending results to the linked Application Insights resource and the Evaluators Catalog"],
        ["Hosted agents to Agent 365 (A365)", "agent365.svc.cloud.microsoft, or the AzureFrontDoor.Frontend service tag (TCP 443)",
         "The hosted agent's A365 observability and tracing endpoint. Block it and the agent keeps running, but its traces are not exported to Agent 365"],
    ], w=2150, theme="indigo", size=14, head_size=15, title="Behind a firewall or managed network: allow-list for telemetry (Learn, as of 2026-11-03)",
        title_size=20, first_col_theme="indigo")
    t.place(cv, 0, y2)
    nt = Note(W - 2150 - 40, "To stop firewall noise from blocked A365 attempts, set a365LoggingEnabled to false on the Foundry resource. "
                             "Sessions that started earlier keep trying until they end.", kind="gotcha", title="Silent denied connections",
              size=14, title_size=16, pad=10, src=[L_NETISO])
    nt.place(cv, 2190, y2)
    return max(t.y + t.h, nt.bottom)


# ---------------------------------------------------------------- E: how the portal builds its views
def section_e(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "E", "What the spans look like, and how the portal builds its views",
               "The vocabulary is documented. Which emitter produces which span is not, so the tree below is deliberately neutral.", "violet")
    top = y
    # span tree
    tw_ = 1340
    with cv.panel(0, top, title="Span vocabulary (OpenTelemetry GenAI conventions, status: Development)", theme="violet", style="dotted",
                  w=tw_, pad=18, title_size=22, sub="parents shown are common examples: actual nesting depends on the agent or framework",
                  sub_size=14) as p:
        x0, y0_ = p.ix + 10, p.iy + 8
        root = Box(420, "invoke_agent", sub="root: invokes an agent through a remote service or in process", theme="violet", fill="hatch",
                   size=18, sub_size=14, h=96).place(cv, x0, y0_)
        kids = [("invoke_agent (child)", "an invocation of another agent: parent-child relationship"), ("plan", "a planning or task-decomposition phase"),
                ("execute_tool", "a tool execution"), ("create / search / update / upsert / delete _memory", "a memory operation")]
        ky = y0_ + 110
        last = None
        for i, (lab, sub) in enumerate(kids):
            kb = Box(520, lab, sub=sub, theme="violet", fill="soft", size=17, sub_size=14, h=76).place(cv, x0 + 90, ky + i * 90)
            line_between(cv, root, kb, dash="solid", color=THEMES["violet"].stroke, a_side="bottom", b_side="left", route="elbow", sw=2,
                         ta=0.1)
            last = kb
        wf = Box(420, "invoke_workflow", sub="a coordinated workflow of agents or other GenAI operations: a root span; execute_tool and "
                                              "memory spans can sit under it", theme="violet", fill="hatch", size=18, sub_size=14,
                 h=130).place(cv, x0 + 700 - 10, y0_)
        at = Card(450, "Attribute names on Learn", [
            "gen_ai.tool.definitions on invoke_agent",
            "gen_ai.tool.call.arguments on execute_tool",
            "gen_ai.tool.call.result on execute_tool",
            "Network egress decision: a span for hosted-agent egress controls",
        ], theme="gray", title_size=17, body_size=14, pad=12, gap=4)
        at.place(cv, x0 + 700 - 10, y0_ + 150)
    q = nd_box(tw_, "Which emitter makes which span",
               "Learn names two emitters for a hosted agent (the Agent Service and your sandbox code) but not which span each one produces",
               h=96).place(cv, 0, p.bottom + 24)
    left_bottom = q.bottom

    # views: two balanced columns of cards under a small heading
    vx = tw_ + 60
    cgap = 36
    cw2 = (W - vx - cgap) / 2
    cv.text(vx, top, "Portal views built on the stored telemetry", size=20, color=THEMES["violet"].deep)
    vtop = top + 44
    rows = [
        ("Traces and Trajectories", "Per-conversation trace tree: each run's inputs and outputs in the order they were invoked (tool calls, retries, latency, cost).",
         "doc"),
        ("Monitor tab (preview)", "Reads the connected Application Insights. Cards for token usage, latency (above 10 s warrants a look), run success rate (below 95% does), "
                                  "evaluation scores and red-team results; settings for recurring evaluations, red-team scans and alerts.", "doc"),
        ("Continuous evaluation", "Samples live traffic as it occurs and scores it with evaluators; needs the project managed identity to hold Foundry User. "
                                  "Recurring evaluations run on a fixed schedule instead.", "doc"),
    ]
    cards = [Card(cw2, lab, [("para", sub)], theme="violet", title_size=19, body_size=14, pad=14) for lab, sub, _ in rows]
    cards.append(vb(cw2, "More on the same data", [
        "DEM341 shows the portal tree: a per-conversation list with token cost, input, output and estimated cost, sortable and filterable; trace "
        "metrics are the number of spans, chat calls, tool calls, latency and tokens",
        "BRK252: continuous evaluation pulls production traces from Application Insights and scores them (0:07:57)",
        "Control Plane fleet views aggregate cost and health across agents (Mechanics 0:12:54, BRK205 0:22:46)",
    ], src=[("DEM341 at 0:06:47", U_DEM341), ("BRK252 at 0:07:57", U_BRK252), ("BRK205 at 0:22:46", U_BRK205)], prefix="Video"))
    cols = [vtop, vtop]
    for c in cards:
        i = 0 if cols[0] <= cols[1] else 1
        c.place(cv, vx + i * (cw2 + cgap), cols[i])
        cols[i] = c.bottom + 18
    return max(left_bottom, max(cols) - 18)


# ---------------------------------------------------------------- F: data handling + not documented
def section_f(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "F", "Retention, data handling and what nobody documents",
               "The data sits in your own Azure Monitor resources, so your policies decide how long it lives and who can see it", "gray")
    top = y
    cw = 1000
    gap = 80
    c1 = Card(cw, "Where the data lives and for how long", [
        "Stored in the Application Insights and Log Analytics resources YOU connect: their retention, sampling and billing settings apply",
        "Application Insights costs apply; tracing is off by default so data collection starts only when you connect it",
        "Disabling tracing stops new data; history stays until your retention policy removes it",
        "Learn: out-of-the-box traces for the past 90 days once tracing is enabled (as of 2026-11-03)",
    ], theme="violet", src=[L_DATA, L_SETUP])
    c2 = Card(cw, "Your responsibilities", [
        "Tell end users what is collected, why and who can see it",
        "Redact or minimise personal data and never log secrets, credentials or tokens in prompts, tool arguments or span attributes",
        "Control who holds Log Analytics Reader, and who holds Privileged Monitoring Data Reader on protected tables",
        "Trace data may be visible to users with access to the connected resource, within the project or tenant",
    ], theme="red", src=[L_DATA, L_CONCEPT])
    c3 = Card(cw, "Status and caveats (as of 2026-11-03)", [
        "Tracing is generally available for prompt and hosted agents; workflow and external agents are in preview",
        "Entra-authenticated ingestion and the protected AppGenAIContent routing are preview",
        "The OpenTelemetry GenAI semantic conventions are in Development status: attribute names may change",
        "Microsoft and Cisco Outshift contribute multi-agent conventions, integrated in Foundry, Microsoft Agent Framework, LangChain, "
        "LangGraph and the OpenAI Agents SDK",
    ], theme="orange", src=[L_CONCEPT, L_ENTRA])
    h = max(c1.h, c2.h, c3.h)
    c1.place(cv, 0, top, h=h)
    c2.place(cv, cw + gap, top, h=h)
    c3.place(cv, 2 * (cw + gap), top, h=h)
    y2 = top + h + 40
    nds = nd(cw, "Not documented", [
        "How the portal reconstructs a trace tree, trends and trajectories from the stored spans",
        "Which span each emitter produces, and how the two identities' spans are joined",
        "Where evaluation scores are stored, and how the Control Plane aggregates across agents",
        "Per-tenant retention beyond the Application Insights and Log Analytics policies",
    ], title_size=20, body_size=15, pad=16)
    nds.place(cv, 0, y2)
    ev = vb(cw, "From the Build 2026 hosted-agent tracing walk-through", [
        "Reactor stream (2026-04-27, 0:42:09 to 0:46:24): a tracing walk-through for a hosted Microsoft Agent Framework agent",
        "Mechanics (2026-04-22): actions are traceable to the agent identity (0:03:45, 0:05:01)",
    ], src=[("Reactor: host your agents on Foundry", U_REACTOR), ("Mechanics: Agent Service explained", U_MECH)], prefix="Video")
    ev.place(cv, cw + gap, y2)
    pf = Note(cw, "Preview terms apply: no service-level agreement and not recommended for production workloads. Re-check the "
                  "protected-table dates and the preview markers before you rely on them.", kind="preview", title="Preview features",
              size=14, title_size=16, pad=10, src=[L_ENTRA, L_SENS])
    pf.place(cv, 2 * (cw + gap), y2)
    return max(nds.bottom, ev.bottom, pf.bottom)


# ---------------------------------------------------------------- sources
def section_sources(cv: Canvas, y: float) -> float:
    items = [L_CONCEPT, L_DATA, L_SETUP, L_ENTRA, L_SENS, L_DASH, L_OBS, L_HOSTED_OTEL, L_PERMS, L_NETISO, L_MVNET, L_ARCH,
             ("(video) DEM341: Any agent, any cloud: tracing with OpenTelemetry, v=WprbDyANqy0", U_DEM341),
             ("(video) BRK252: From observability to ROI, v=a7FELS8hQAE", U_BRK252),
             ("(video) BRK205: AI Operations to own the fleet, v=oOO6OG4biEY", U_BRK205)]
    r = sources(cv, 0, y, items, w=W, cols=4)
    return r.y + r.h
