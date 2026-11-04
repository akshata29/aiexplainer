"""Model APIs and capabilities (1/2): the capability map, endpoints, the Responses API loop and tool belt, Chat Completions, Decisions, reasoning."""
from __future__ import annotations

from generator.xd import *
from generator.xd import Note as _KitNote
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="model-apis-capabilities", title="Model APIs and capabilities: the surface map", section="2", group="Models", order=25,
    description="One Foundry endpoint, four districts: the Responses API and its tool belt, Chat Completions, the Decisions API, reasoning, "
                "structured outputs and caching - with an endpoint address book (media, voice, MAI and Claude continue in part 2).",
    tags=["responses api", "tools", "decisions api", "reasoning", "endpoints", "models"],
)

W, G, C = 3000, 48, 460          # canvas width, standard gap, one-column card width (6-column grid)
MUTED_ = "#495057"


def span(n: int) -> float:
    return n * C + (n - 1) * G


def colx(i: int) -> float:
    return i * (C + G)


def L(label: str, path: str, base: str = "azure/foundry"):
    return (label, learn(path, base=base))


S_ENDPOINTS = L("Endpoints for Foundry Models", "foundry-models/concepts/endpoints")
S_RESP = L("Responses API", "openai/how-to/responses")
S_FUNC = L("Function calling", "openai/how-to/function-calling")
S_PTC = L("Programmatic tool calling", "openai/concepts/programmatic-tool-calling")
S_TSEARCH = L("Tool search", "openai/how-to/tool-search")
S_WEB = L("Web search", "openai/how-to/web-search")
S_DEEP = L("Deep research", "openai/how-to/deep-research")
S_SHELL = L("Shell tool", "openai/how-to/shells")
S_SKILLS = L("Skills", "openai/how-to/skills")
S_MULTI = L("Multi-agent orchestration (preview)", "openai/how-to/responses-multi-agent")
S_WS = L("WebSocket mode", "openai/how-to/websockets")
S_CHAT = L("Chat Completions API", "openai/how-to/chatgpt")
S_DEC = L("Decisions API", "openai/how-to/decisions")
S_MSDEC = L("Microsoft-Decision-1", "foundry-models/how-to/use-foundry-models-microsoft-decision")
S_REASON = L("Reasoning models", "openai/how-to/reasoning")
S_STRUCT = L("Structured outputs", "openai/how-to/structured-outputs")
S_JSON = L("JSON mode", "openai/how-to/json-mode")
S_PRED = L("Predicted outputs", "openai/how-to/predicted-outputs")
S_CACHE = L("Prompt caching", "openai/how-to/prompt-caching")
S_ROUTER = L("Model router concepts", "openai/concepts/model-router")


# ---------------------------------------------------------------------------------------------- helpers
def Note(w, text, **kw):
    """Kit Note plus bottom breathing room when it carries a Learn: link (the kit draws that link flush with the border)."""
    n = _KitNote(w, text, **kw)
    if kw.get("src") and "min_h" not in kw:
        n = _KitNote(w, text, min_h=n.h + 14, **kw)
    return n


def banner(cv, y, n, title, sub=None, theme="blue"):
    """Numbered section banner across the canvas; returns the y where content can start."""
    numbered(cv, 24, y + 26, n, theme=theme, d=44, size=24)
    _, bottom = section_header(cv, 60, y, title, sub, size=32, sub_size=17, w=W - 60)
    return bottom + 26


def tile_h(num, label, sub, w, num_size=60):
    nw, nh = text_size(num, num_size)
    avail = (w - (26 + nw + 22) - 16) * 0.965
    lr = metrics.line_ratio()
    return max(nh + 24, len(wrap_text(label, avail, 21)) * 21 * lr + 4 + len(wrap_text(sub, avail, 15)) * 15 * lr + 28)


def tile(cv, x, y, w, h, num, label, sub, th_name, num_size=60):
    """Big-number summary tile."""
    th = get_theme(th_name)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    nw, nh = text_size(num, num_size)
    cv.text(x + 26, y + (h - nh) / 2, num, size=num_size, color=th.deep)
    tx = x + 26 + nw + 22
    avail = (w - (tx - x) - 16) * 0.965
    lab, sl = wrap_text(label, avail, 21), wrap_text(sub, avail, 15)
    lr = metrics.line_ratio()
    total = len(lab) * 21 * lr + 4 + len(sl) * 15 * lr
    ty = y + (h - total) / 2
    cv.text(tx, ty, "\n".join(lab), size=21, color=th.deep)
    cv.text(tx, ty + len(lab) * 21 * lr + 4, "\n".join(sl), size=15, color=INK)
    cv.register("tile:" + label, x, y, w, h)


def code_need(w, lines, size=15, notes=None, src=None):
    """Natural height of a code_box (code lines, optional bullet notes, optional Learn link)."""
    lh = size * metrics.line_ratio(metrics.MONO)
    need = 12 + 26 + 8 + len(lines) * lh + 14 + (18 if src else 0)
    if notes:
        need += 34 + sum(len(wrap_text(t, w - 56, 15)) * 15 * metrics.line_ratio() + 5 for t in notes)
    return need


def code_box(cv, x, y, w, title, lines, th_name="blue", size=15, h=None, src=None, notes=None):
    """Monospace code panel with a coloured title (and optional 'reading the call' bullets); returns its height."""
    th = get_theme(th_name)
    lh = size * metrics.line_ratio(metrics.MONO)
    H = max(code_need(w, lines, size, notes, src), h or 0)
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 16, y + 10, title, size=18, color=th.deep)
    cv.text(x + 16, y + 44, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    if notes:
        ny = y + 44 + len(lines) * lh + 20
        cv.line((x + 16, ny - 8), (x + w - 16, ny - 8), stroke=th.stroke, sw=1, dash="dashed")
        cv.text(x + 16, ny, "Reading the call", size=16, color=th.deep)
        ny += 26
        for t in notes:
            tl = wrap_text(t, w - 56, 15)
            cv.ellipse(x + 18, ny + 6, 8, 8, stroke=th.stroke, sw=2, rough=0)
            cv.text(x + 38, ny, "\n".join(tl), size=15, color=INK)
            ny += len(tl) * 15 * metrics.line_ratio() + 5
    if src:
        cv.text(x + 16, y + H - 26, "Learn: " + src[0], size=12, color=LINK, link=src[1])
    cv.register("code:" + title, x, y, w, H)
    return H


def std(theme, title, body, **kw):
    """Standard dense card (consistent type scale)."""
    kw.setdefault("title_size", 20)
    kw.setdefault("body_size", 15)
    return Card(C, title, body, theme=theme, **kw)


def two_pass(fn, cv, y):
    """Run a section twice: measure the side-by-side panels on a scratch canvas, then draw them all at the tallest height."""
    _, hs = fn(Canvas("scratch"), y, 0)
    return fn(cv, y, max(hs))[0]


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Model APIs and capabilities: the surface map",
        "One Foundry endpoint, four districts: Responses and its tool belt, classic and decision APIs, reasoning and output shaping "
        "(facts as of 2026-11-03; media, voice, MAI and Claude: part 2)", w=W)
    y = bottom + 36
    y = summary_tiles(cv, y)
    y = section_map(cv, y + 56)
    y = section_endpoints(cv, y + 56)
    y = section_responses(cv, y + 56)
    y = section_text(cv, y + 56)
    section_sources(cv, y + 56)


# ---------------------------------------------------------------------------------------------- summary
def summary_tiles(cv, y):
    tiles = [
        ("32", "regions for the Responses API", "The region list on the Responses API page", "blue", 60),
        ("1", "model on the Decisions API", "gpt-6-luna only; East US 2 excluded while it rolls out", "blue", 60),
        ("60 min", "WebSocket mode connection cap", "One in-flight response per connection", "orange", 40),
        ("3", "Decisions question types", "predicate, choice and score; any can return a refusal", "blue", 60),
        ("29 min", "a reasoning call can take this long", "Set client timeouts accordingly", "violet", 40),
        ("100%", "off cached input at best", "Provisioned; Standard gets a discount on cache reads", "yellow", 60),
    ]
    hs = [tile_h(*t[:3], C, t[4]) for t in tiles]
    H = max(hs)
    for i, (num, label, sub, th, ns) in enumerate(tiles):
        tile(cv, colx(i), y, C, H, num, label, sub, th, ns)
    y += H + 22
    cx = 0.0
    cv.text(cx, y + 2, "Also in this series:", size=16, color=MUTED_)
    cx += text_size("Also in this series:", 16)[0] + 16
    for label, th in (("Foundry Models catalog", "blue"), ("Deployment types and offers", "blue"), ("PTU and quota", "yellow"),
                      ("Model router: one deployment, many models", "blue"), ("Fine-tuning: from data to a deployed model", "blue"),
                      ("Part 2: Media, voice, MAI models and Claude on Foundry", "lime")):
        c = Chip(label, theme=th, size=15, fill="soft").place(cv, cx, y - 2)
        cx += c.w + 14
    return y + 38


# ---------------------------------------------------------------------------------------------- 1 map
D1 = [
    ("Tool belt", "orange", ["Function calling", "Programmatic tool calling", "Tool search", "Web search", "Deep research", "Shell + skills", "MCP",
                             "Computer use", "Multi-agent (preview)"]),
    ("Run it", "green", ["Stateful: previous_response_id", "Background mode", "WebSocket mode", "service_tier", "Auto or direct model routing"]),
    ("Shape the answer", "blue", ["Structured outputs", "Reasoning effort", "Prompt caching"]),
]
D2 = [
    ("Text APIs", "blue", ["Chat Completions", "JSON mode", "Predicted outputs"]),
    ("Typed decisions", "blue", ["Decisions API (gpt-6-luna)", "Microsoft-Decision-1"]),
    ("Vectors", "teal", ["Embeddings"]),
]
D3 = [
    ("Pictures and video", "lime", ["Image generation", "MAI-Image", "FLUX", "Sora 2 (preview)", "Vision input"]),
    ("Voice", "lime", ["Audio models", "Realtime 2.1", "GPT-Live", "Realtime Translate", "Realtime Transcribe", "MAI-Voice", "MAI-Transcribe"]),
]
D4 = [
    ("Coding agents", "gray", ["Codex CLI", "Codex VS Code extension", "Claude Code", "Claude Desktop"]),
    ("Events", "gray", ["Webhooks"]),
]


def district(cv, x, y, w, num, title, sub, th_name, groups, footer, min_h=0):
    """One colour-coded district of the capability map: titled panel with grouped chips."""
    th = get_theme(th_name)
    with cv.panel(x, y, title=title, sub=sub, theme=th_name, style="solid", fill="soft", pad=20, title_size=26, sub_size=16, w=w, sw=3,
                  min_h=min_h) as p:
        cy = p.iy + 4
        for gname, chip_theme, items in groups:
            cv.text(p.ix, cy, gname, size=17, color=get_theme(chip_theme).deep)
            cy += 26
            fl = ChipFlow([Chip(i, theme=chip_theme, size=15, fill="solid", pad_x=10, pad_y=5) for i in items], w - 40, gap=8)
            fl.place(cv, p.ix, cy)
            cy += fl.h + 16
        cv.text(p.ix, cy, footer, size=14, color=MUTED_)
    numbered(cv, x + w - 30, y + 30, num, theme=th_name, d=38, size=22)
    return p


def section_map(cv, y):
    y = banner(cv, y, 1, "The capability map: one endpoint, four districts",
               "Every model is called through a deployment name in the model field; what you can do with it depends on the API surface and the model")
    DW, HUB = 1090, 600
    specs = [
        (1, "Text and agents", "Responses API: stateful, tool-rich", "green", D1, "Details: section 3 (loop, tool belt, WebSocket mode)"),
        (2, "Classic and decision", "Messages in, text or typed answers out", "blue", D2, "Details: section 4 (embeddings: part 2)"),
        (3, "Media and voice", "Pictures, video, audio and live speech", "lime", D3, "Details: part 2 (images, video, Realtime, GPT-Live)"),
        (4, "Developer tools", "Coding agents and push events", "gray", D4, "Details: part 2 (Codex, Claude Code and Desktop, webhooks)"),
    ]
    scratch = Canvas("scratch")
    hs = [district(scratch, 0, 0, DW, *s).h for s in specs]
    ht, hb = max(hs[0], hs[1]), max(hs[2], hs[3])
    gap = 60
    xr = W - DW
    d1 = district(cv, 0, y, DW, *specs[0], min_h=ht)
    d2 = district(cv, xr, y, DW, *specs[1], min_h=ht)
    d3 = district(cv, 0, y + ht + gap, DW, *specs[2], min_h=hb)
    d4 = district(cv, xr, y + ht + gap, DW, *specs[3], min_h=hb)
    hy = y + (ht + gap + hb) / 2
    hub = Box(HUB, "One Foundry endpoint", sub="deployment name = the model value", theme="blue", shape="ellipse", h=300, icon="foundry",
              icon_pos="top", icon_size=44, size=26, sub_size=16, fill="hatch", sw=3)
    hub.place(cv, (W - HUB) / 2, hy - 150)
    cx = W / 2
    ty = hub.bottom + 14
    for s, mono in (("https://<resource>.openai.azure.com/openai/v1/", True), ("https://<resource>.services.ai.azure.com  (Claude: /anthropic/v1/messages)", True)):
        tw, _ = text_size(s, 13, metrics.MONO)
        cv.text(cx - tw / 2, ty, s, size=13, color=INK, font=metrics.MONO)
        ty += 20
    cv.text(cx - text_size("Learn: Endpoints for Foundry Models", 12)[0] / 2, ty + 2, "Learn: Endpoints for Foundry Models", size=12, color=LINK, link=S_ENDPOINTS[1])
    # bus connectors
    for side in (0, 1):
        xm = DW + 55 if side == 0 else xr - 55
        hx = hub.x - 6 if side == 0 else hub.right + 6
        y1, y3 = y + ht / 2, y + ht + gap + hb / 2
        arrow(cv, [(hx, hy), (xm, hy)], dash="dotted", color="#1971c2", sw=3, start_head=None, end_head=None)
        arrow(cv, [(xm, y1), (xm, y3)], dash="dotted", color="#1971c2", sw=3, start_head=None, end_head=None)
        arrow(cv, [(xm, y1), (DW + 8 if side == 0 else xr - 8, y1)], dash="dotted", color="#1971c2", sw=3, start_head=None, end_head="arrow")
        arrow(cv, [(xm, y3), (DW + 8 if side == 0 else xr - 8, y3)], dash="dotted", color="#1971c2", sw=3, start_head=None, end_head="arrow")
    ly = y + ht + gap + hb + 50
    lw = span(3)
    with cv.panel(0, ly, title="Anthropic Claude (Messages API)", sub="Not sold by Azure: Anthropic is the seller and data processor", theme="orange", style="dotted",
                  pad=20, title_size=24, sub_size=15, w=lw) as pc:
        fl = ChipFlow(["Hosted on Azure (v2, all GA)", "Hosted on Anthropic (v1)", "Messages + token counting", "CCU billing, MACC-eligible",
                       "No built-in content filter"], lw - 40, theme="orange", size=15, fill="solid", gap=8)
        fl.place(cv, pc.ix, pc.iy + 4)
        cv.text(pc.ix, pc.iy + 4 + fl.h + 12, "Details: part 2", size=14, color=MUTED_)
    with cv.panel(colx(3), ly, title="Microsoft AI (MAI) models", sub="Mostly preview; Microsoft-Decision-1 is v1", theme="violet", style="dotted", pad=20,
                  title_size=24, sub_size=15, w=lw, min_h=pc.h) as pm:
        fl = ChipFlow(["MAI-Thinking-1", "MAI-Image-2.5 and 2.6 families", "MAI-Voice-2.1", "MAI-Transcribe-2", "Microsoft-Decision-1", "MAI-Code-1.1-Flash"],
                      lw - 40, theme="violet", size=15, fill="solid", gap=8)
        fl.place(cv, pm.ix, pm.iy + 4)
        cv.text(pm.ix, pm.iy + 4 + fl.h + 12, "Details: part 2 (MAI table)", size=14, color=MUTED_)
    return max(pc.bottom, pm.bottom)


# ---------------------------------------------------------------------------------------------- 2 endpoints
def section_endpoints(cv, y):
    y = banner(cv, y, 2, "Address book: where each surface lives", "The v1 route needs no api-version; the deployment name is the model value (as documented on the pages cited)")
    t = Table([("Surface", 250), ("Route or address", 1100), "How you call it (as documented)"], [
        [("Responses API (v1)", "green"), "https://<resource>.openai.azure.com/openai/v1/responses   or the project route  .../api/projects/<proj>/openai/v1/responses",
         "Foundry SDK: AIProjectClient(...).get_openai_client(), then client.responses.create(model=<deployment>, input=...). Also works with non-OpenAI sold-by-Azure models that support it (for example DeepSeek, Llama, Grok); otherwise 400 Model not supported."],
        [("Responses WebSocket mode", "green"), "wss://<resource>.openai.azure.com/openai/v1/responses", "response.create events; API key or Entra ID (scope https://ai.azure.com/.default)."],
        [("Chat Completions", "blue"), "Messages-based interface: see the Chat Completions page for the route and api-version", "Entra ID needs the Cognitive Services User role. Still the API for many partner models; new apps are pointed to the Responses API."],
        [("Decisions API", "blue"), "POST /openai/v1/decisions", "openai.decisions.create (Python openai>=3.26.0, JavaScript openai>=7.30.0) or REST; API key or Entra ID; gpt-6-luna only."],
        [("Microsoft-Decision-1", "blue"), "<foundry-resource-endpoint>/providers/microsoft/v1/systemone", "model = your deployment name; body = state plus questions. Entra token scope https://cognitiveservices.azure.com."],
        [("Realtime API", "lime"), "wss://<resource>.openai.azure.com/openai/v1/realtime?model=<deployment>", "No api-version. WebRTC, WebSocket or SIP transports (part 2)."],
        [("GPT-Live", "lime"), "wss://<resource>.openai.azure.com/openai/v1/live/sessions", "WebSocket; for WebRTC your backend POSTs the browser's SDP offer to /openai/v1/live/sessions (part 2)."],
        [("Claude Messages API", "orange"), "POST https://<resource>.services.ai.azure.com/anthropic/v1/messages   (+ /v1/messages/count_tokens)", "Header anthropic-version: 2023-06-01; anthropic Python or @anthropic-ai/foundry-sdk (part 2)."],
        [("Webhook registration", "gray"), "POST https://<resource>.openai.azure.com/openai/v1/dashboard/webhook_endpoints", "REST only; the signing secret is shown once (part 2)."],
    ], w=W, theme="blue", size=15, head_size=16, title="Surfaces, routes and how to call them", title_size=22)
    t.place(cv, 0, y)
    n1 = Note(span(3), "Two Entra token scopes appear in the examples: https://ai.azure.com/.default (WebSocket mode) and https://cognitiveservices.azure.com/.default "
              "(Microsoft-Decision-1). Use the scope on the page for the API you call.", kind="warn", title="Docs disagree", size=15, src=[S_ENDPOINTS])
    n1.place(cv, 0, t.bottom + 24)
    n2 = Note(span(3), "Roles named on the pages: Cognitive Services User (Chat Completions with Entra, SIP), Cognitive Services OpenAI User (embeddings, multi-agent). "
              "Check the page for the role your API needs.", kind="info", title="Roles", size=15)
    n2.place(cv, colx(3), t.bottom + 24, h=n1.h)
    return t.bottom + 24 + max(n1.h, n2.h)


# ---------------------------------------------------------------------------------------------- 3 responses
def section_responses(cv, y):
    y = banner(cv, y, 3, "Responses API: the agentic loop and its tool belt",
               "Stateful, multi-turn, tool-rich; unifies Chat Completions and Assistants capabilities. Check model, api-version and SDK support for each tool", "green")
    top = y
    with cv.panel(0, top, title="One turn of the loop", sub="Hosted tools stay on the service side; function calls and local shell come back to your code", theme="green",
                  style="dotted", pad=22, title_size=24, sub_size=16, w=span(3)) as pl:
        seq = Sequence(cv, pl.ix + 40, pl.iy + 6, [("Your app", "gray", "app"), ("Responses API + model", "blue", "openai"), ("Hosted tools", "orange", "toolbox")],
                       spacing=470, head_w=250, head_h=60, step=62, label_size=15)
        seq.msg(0, 1, "responses.create(model, input, tools)", num=1)
        seq.msg(1, 2, "hosted tool call: web search, hosted shell, MCP, deep research", num=2)
        seq.msg(2, 1, "tool output, no round trip to you", dash="dashed", num=3)
        seq.msg(1, 0, "function call or local shell call: your code runs it", num=4)
        seq.msg(0, 1, "create(previous_response_id, tool output)", num=5)
        seq.msg(1, 0, "final message (with inline citations when web search ran), plus the response id", dash="dashed", num=6)
        seq.note(0, 1, "Over WebSocket mode only the new input items are sent on each turn (see the WebSocket panel below).", kind="tip")
        seq.end()
    tb = Table([("Tool", 200), ("Hosted by the service", 560), "Run by your code"], [
        ["Function calling", DASH, CHECK],
        ["Shell", "container_auto: Azure provisions a sandboxed container", "local shell: you execute shell_call actions"],
        ["Tool search", "hosted: the service searches the deferred tools you declared", "client-executed: you answer tool_search_call with tool_search_output"],
        ["Web search", CHECK, DASH],
        ["Deep research (background)", CHECK, DASH],
    ], w=span(3), theme="orange", size=14, head_size=15, title="Who runs which tool", title_size=20, first_col_theme="orange")
    tb.place(cv, colx(3), top)
    st = Card(span(3), "Stateful by design", [
        "Responses are stored and chained with previous_response_id, so each turn sends only new input",
        "Background mode runs long jobs and completes through a response.completed webhook",
        "Request-level service_tier (flex, priority, default or auto) and header x-ms-service-tier: see the deployment types canvas",
        "model = model-router chooses a model per request: see the model router canvas",
    ], theme="green", icon="agent", title_size=20, body_size=15, src=[S_RESP])
    st.place(cv, colx(3), tb.bottom + 24)
    y2 = max(pl.bottom, st.bottom) + 40
    # ---- tool belt cards
    cards1 = [
        std("orange", "Function calling", [
            "Chat Completions flavour in 3 steps: call with tools and user input; the model returns JSON arguments; your app runs the function and calls again with the result",
            "The Responses API uses a different request and response shape",
            "! GPT-5.6 models: Chat Completions and function tools only combine when reasoning_effort is none; use Responses for tool calling",
        ], icon="functions", src=[S_FUNC]),
        std("orange", "Programmatic tool calling", [
            "The model writes a program that orchestrates tools, with branching and iteration, so one request replaces many model turns",
            "Flow: model, generated program, tool operations, program result, model",
            "SDK needs output_schema, allowed_callers and caller info",
            "! Per model and SDK: do not assume Responses API support implies it",
        ], icon="code", src=[S_PTC]),
        std("orange", "Tool search", [
            "gpt-5.4 and later: add tool_search to tools and mark tools, namespaces or MCP servers defer_loading: true",
            "Definitions load on demand and are appended at the end of context, which preserves the cache",
            "Prefer namespaces (fewer than 10 functions each) or MCP servers; the model still sees each name and description",
            "Different from Toolbox tool search in Agent Service",
        ], icon="toolbox", src=[S_TSEARCH]),
        std("orange", "Web search", [
            "Tool {\"type\": \"web_search\"} works with GPT-4 models and later; web_search_preview is supported but not recommended",
            "Modes: fast lookup without reasoning, agentic search with reasoning models, deep research",
            "! Uses Grounding with Bing Search or Custom Search (First Party Consumption Services): the Microsoft DPA does not apply, data flows outside your compliance and geo boundary, and it costs extra",
        ], icon="bing", src=[S_WEB]),
        std("orange", "Deep research", [
            "o3-deep-research, or gpt-5.5 with high or xhigh reasoning through web search",
            "background: true plus at least one data source: web_search_preview and/or a remote MCP server (optional code_interpreter)",
            "Runs for minutes: use background mode and a response.completed webhook",
            "Output lists web_search_call, code_interpreter_call, mcp_tool_call and a final message with inline citations",
            "! o3-deep-research retires 2026-11-19 (replacement gpt-5.6-sol), as of 2026-11-03",
        ], icon="search", src=[S_DEEP]),
        std("orange", "Shell tool and skills", [
            "Responses API only, not Chat Completions",
            "Hosted shell: environment.type container_auto, Azure provisions a sandboxed container. Local shell: you execute shell_call actions",
            "Skills: versioned bundles (SKILL.md front matter plus files, the Agent Skills standard) uploaded as a directory or zip, giving a skill_id",
            "Attach through the shell environment skills array ({\"type\": \"skill_reference\", \"skill_id\": ...})",
            "! Treat skills as privileged code",
        ], icon="gear", src=[S_SHELL, S_SKILLS]),
    ]
    cards2 = [
        std("green", "Multi-agent orchestration", [
            "GPT-5.6 models only; api-version=preview",
            "multi_agent.enabled: true, plus max_concurrent_subagents",
            "A root agent spawns parallel subagents and /root consolidates",
            "Role: Cognitive Services OpenAI User",
            "Best for independent, bounded workstreams; it uses more tokens",
        ], badge="preview", icon="agent", src=[S_MULTI]),
        std("orange", "Computer use, MCP and background mode", [
            "computer-use-preview needs limited-access registration; the GPT-5.x docs list Computer use",
            "Remote MCP servers are a data source for deep research and appear in the examples",
            "Background mode with a response.completed webhook suits long runs",
        ], icon="mcp", src=[S_RESP]),
        std("blue", "Structured outputs and reasoning", [
            "Responses takes the JSON Schema in text.format; Chat Completions in response_format",
            "reasoning_effort is set on the request",
            "Details in section 4",
        ], icon="openai", src=[S_STRUCT]),
        std("blue", "Prompt caching", [
            "Identical prompt prefixes are reused; GPT-5.6 and later add prompt_cache_key and explicit cache breakpoints",
            "Details in section 4",
        ], icon="openai", src=[S_CACHE]),
    ]
    _, b1 = row(cv, 0, y2, cards1, gap=G)
    y3 = b1 + G
    # row 2: four cards + WebSocket panel gets its own band
    _, b2 = row(cv, 0, y3, cards2, gap=G)
    # websocket mode band
    wy = b2 + 40
    with cv.panel(0, wy, title="WebSocket mode: a persistent connection for long, tool-heavy chains", sub="wss://<resource>.openai.azure.com/openai/v1/responses driven by response.create events",
                  theme="orange", style="dotted", pad=22, title_size=24, sub_size=16, w=W) as pw:
        seq = Sequence(cv, pw.ix + 40, pw.iy + 6, [("Client", "gray", "app"), ("Responses service", "blue", "openai")], spacing=640, head_w=250, head_h=60, step=60,
                       label_size=15)
        seq.msg(0, 1, "response.create: mirrors the HTTP create body (no stream or background)", num=1)
        seq.msg(1, 0, "response events, streamed", dash="dashed", num=2)
        seq.msg(0, 1, "response.create: previous_response_id plus only the new input items", num=3)
        seq.msg(1, 0, "response events, streamed", dash="dashed", num=4)
        seq.note(0, 1, "The service caches only the most recent response in connection-local memory.", kind="info")
        sb = seq.end()
        lt = Table([("Limit or behaviour", 330), "What happens"], [
            ["One in-flight response per connection", "No multiplexing: open more sockets for parallel runs"],
            ["60-minute connection cap", "websocket_connection_limit_reached: reconnect"],
            ["store=false and an uncached previous_response_id", "Fails with previous_response_not_found"],
            ["store=true", "Can hydrate older ids, but loses the latency gain"],
            ["Warm-up", "Optional: send generate: false first"],
            ["Compaction", "Works with server-side compaction (context_management + compact_threshold) and /responses/compact"],
        ], w=span(3) - 20, theme="orange", size=14, head_size=15, title="Limits (as documented)", title_size=20)
        lt.place(cv, pw.ix + 1120, pw.iy + 4)
        cv.text(pw.ix + 1120, lt.bottom + 8, "Auth: API key or Entra ID. Worth it for agentic coding and orchestration loops; not for single-shot or short chats.", size=14, color=MUTED_)
    # supported models
    my = max(pw.bottom, lt.bottom + 40) + 36
    with cv.panel(0, my, title="Responses API supported models (page list, as of 2026-11-03)",
                  sub="Plus non-OpenAI sold-by-Azure models that support it (DeepSeek, Llama, Grok); the Models page differs slightly", theme="blue", style="dotted", pad=22,
                  title_size=24, sub_size=16, w=W) as pm:
        models = ["gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-luna", "gpt-6-sol", "gpt-6-astra", "gpt-5.6-sol / -terra / -luna", "gpt-chat-latest", "gpt-5.5", "gpt-5.4 family",
                  "gpt-5.3-codex / -chat", "gpt-5.2 / -codex / -chat", "gpt-5.1 family", "gpt-5 family (incl. -pro, -codex, -chat)", "gpt-4o / gpt-4o-mini", "gpt-4.1 family",
                  "computer-use-preview", "gpt-image-1 / -1-mini / -1.5", "gpt-image-2.5-flare / -sunburst", "o1", "o3", "o3-mini", "o4-mini"]
        fl = ChipFlow(models, W - 44, theme="blue", size=15, fill="soft", gap=8)
        fl.place(cv, pm.ix, pm.iy + 4)
        cv.text(pm.ix, pm.iy + 4 + fl.h + 10, "Learn: Responses API", size=12, color=LINK, link=S_RESP[1])
    return pm.bottom


# ---------------------------------------------------------------------------------------------- 4 text side
def section_text(cv, y):
    y = banner(cv, y, 4, "Classic and decision APIs, reasoning and shaping the answer",
               "Chat Completions for existing code, typed Decisions for classification and gating, plus the knobs every text call shares", "blue")
    top = y
    # which API
    wt = Table([("I need ...", 330), "Use", ("Why", 540)], [
        ["Stateful turns, tools, agents", ("Responses API", "green"), "Stateful, tool-rich; the recommended base for new apps"],
        ["To keep existing messages-based code", ("Chat Completions", "blue"), "Classic messages interface; still the API for many partner models"],
        ["Typed answers: classify, route, rank, gate", ("Decisions API or Microsoft-Decision-1", "blue"), "Probabilities and choices instead of generated text"],
        ["Free-form JSON that follows a schema", ("Structured outputs", "blue"), "Schema adherence; JSON mode only guarantees valid JSON"],
        ["Typed arguments for a tool call", ("Function calling", "orange"), "The model returns arguments; your code runs the tool"],
        ["Claude models", ("Messages API", "orange"), "/anthropic/v1/messages (part 2)"],
    ], w=span(3), theme="blue", size=14, head_size=15, title="Which API for which job?", title_size=20)
    wt.place(cv, 0, top)
    cc = Card(span(3), "Chat Completions in a few lines", [
        "Classic messages interface (multi-turn, you manage the token budget); the doc tip: for new apps consider the Responses API (migration guide: azure-openai-to-responses)",
        "Reasoning models: use max_completion_tokens; temperature, top_p and penalties are rejected or ignored; use developer role messages",
        "! GPT-5.6 models: function tools only with reasoning_effort none; use Responses for tool calling",
        "Standard quota only governs admission, it does not guarantee throughput; estimate TPM from Azure Monitor processed prompt and generated completion tokens",
    ], theme="blue", icon="api", title_size=20, body_size=15, src=[S_CHAT])
    cc.place(cv, colx(3), top, h=wt.h)
    y1 = top + max(wt.h, cc.h) + 40
    # ---- decisions
    with cv.panel(0, y1, title="Decisions API: typed answers instead of generated text", sub="POST /openai/v1/decisions with gpt-6-luna: text, images or both in; answers[] out", theme="blue",
                  style="dotted", pad=22, title_size=24, sub_size=16, w=span(4)) as pd:
        iw = span(4) - 44
        req = [
            "POST /openai/v1/decisions",
            "{",
            '  "model": "<gpt-6-luna deployment name>",',
            '  "input": "text, or user messages with input_text / input_image parts",',
            '  "questions": [',
            '    { "type": "predicate", "name": "<unique name>", "instructions": "..." },',
            '    { "type": "choice", "name": "<unique name>", "instructions": "...", "choices": [ ... ] },',
            '    { "type": "score", "name": "<unique name>", "instructions": "...", "levels": [ ... ] }',
            "  ]",
            "}",
        ]
        rh = code_box(cv, pd.ix, pd.iy + 4, 760, "Request outline: model + input + questions[]", req, "blue", size=14)
        bx = pd.ix + 760 + 70
        cv.text(bx, pd.iy + 4, "Response: answers[] in order, plus token usage", size=18, color=get_theme("blue").deep)
        ay = pd.iy + 4 + 34
        for a in (
            Card(1110, "predicate", ["Returns a probability from 0 to 1"], theme="blue", title_size=18, body_size=15, fill="soft"),
            Card(1110, "choice", ["One of the options you supply, a probability per option and a confidence"], theme="blue", title_size=18, body_size=15, fill="soft"),
            Card(1110, "score", ["Probability-weighted average of the ordered level indices, a probability per level and a confidence"], theme="blue", title_size=18,
                 body_size=15, fill="soft"),
            Card(1110, "refusal", ["Any question can return type refusal with its name while the others still answer: handle it apart from a low probability"], theme="red",
                 title_size=18, body_size=15, fill="soft"),
        ):
            a.place(cv, bx, ay)
            ay += a.h + 12
        ah = ay - 12 - (pd.iy + 4)
        arrow(cv, [(pd.ix + 760 + 8, pd.iy + 4 + max(rh, ah) / 2), (bx - 8, pd.iy + 4 + max(rh, ah) / 2)], color=INK, sw=3)
        n_th = Note(iw, "Your app applies thresholds calibrated on labelled data. Use the Decisions API for classification, routing, prioritisation and gating; "
                    "structured outputs for free-form JSON; function calling for tool arguments.", kind="tip", title="Calibrate, then gate", size=15, src=[S_DEC])
        n_th.place(cv, pd.ix, pd.iy + 4 + max(rh, ah) + 24)
    dt = Table([("", 140), "Decisions API", "Microsoft-Decision-1"], [
        ["Model", "gpt-6-luna only (deployment name in model)", "Microsoft-Decision-1, version 1, sold by Azure"],
        ["Route", "POST /openai/v1/decisions", "<resource endpoint>/providers/microsoft/v1/systemone"],
        ["Input", "input: text and/or images", "state: text or JSON; up to 32K tokens; text only"],
        ["Questions", "predicate, choice, score", "noul (probability 0-1), choice, score; optional criteria"],
        ["Output", "answers[] with probabilities, confidence, refusals", "Typed answers; no free-form text or rationale"],
        ["Availability", "Rolling out to regions where gpt-6-luna is available; East US 2 excluded", "GlobalStandard and DataZoneStandard in selected regions"],
        ["Quota", "-", "Tier 1: 2.16M TPM, 2,160 RPM; up to Tier 6: 15M TPM, 15,000 RPM"],
    ], w=span(2), theme="blue", size=14, head_size=15, title="Decisions API vs Microsoft-Decision-1", title_size=20, first_col_theme="blue")
    dt.place(cv, colx(4), y1)
    nq = Note(span(2), "The two use different vocabulary: predicate vs noul, input vs state.", kind="warn", title="Docs quirk", size=14, src=[S_MSDEC])
    nq.place(cv, colx(4), dt.bottom + 20)
    y2 = max(pd.bottom, nq.bottom) + 40
    # ---- reasoning ladder
    with cv.panel(0, y2, title="Reasoning models: effort, parameters and time", sub="Page title: GPT-6 Astra and GPT-5; non-OpenAI reasoning models have their own page", theme="violet", style="dotted", pad=22,
                  title_size=24, sub_size=16, w=W) as pr:
        iw = W - 44
        rungs = [("none", "gpt-5.1 default; the only level that mixes GPT-5.6 with Chat Completions tools"), ("minimal", "GPT-5 family; parallel tool calls are not supported here"),
                 ("low", "GPT-5 family"), ("medium", "GPT-5 family default"), ("high", "GPT-5 family"), ("xhigh", "gpt-5.1-codex-max adds it and does not support none")]
        rw = (iw - 5 * 40) / 6
        boxes = []
        for i, (t, s) in enumerate(rungs):
            th = "violet"
            b = Box(rw, t, sub=s, theme=th, size=22, sub_size=14, fill="hatch" if i != 3 else "solid", h=150)
            b.place(cv, pr.ix + i * (rw + 40), pr.iy + 30)
            boxes.append(b)
        for a, b in zip(boxes, boxes[1:]):
            connect(cv, a, b, sw=3)
        cv.text(pr.ix, pr.iy + 2, "less reasoning", size=15, color=MUTED_)
        tw_, _ = text_size("more reasoning", 15)
        cv.text(pr.ix + iw - tw_, pr.iy + 2, "more reasoning", size=15, color=MUTED_)
        cy = boxes[0].bottom + 24
        rc = [
            Card(span(2), "Parameters and roles", [
                "Different parameter set from classic chat models: max_completion_tokens; temperature and top_p are ignored; developer role messages",
                "gpt-chat-latest has a fixed non-zero effort that you cannot set",
                "GPT-6 family pages list reasoning effort and verbosity",
            ], theme="violet", title_size=19, body_size=15, src=[S_REASON]),
            Card(span(2), "Time and other reasoning models", [
                "Reasoning models can take up to 29 minutes: set client timeouts",
                "Non-OpenAI catalog models expose chat-completion with reasoning content (DeepSeek-V4, Kimi, Cohere-command-a-plus)",
                "MAI-Thinking-1 offers encrypted chain-of-thought (part 2)",
            ], theme="violet", title_size=19, body_size=15, src=[S_REASON]),
            Card(span(2), "Where else effort appears", [
                "Responses and Chat Completions: reasoning_effort on the request",
                "Realtime 2.1 uses reasoning.effort minimal, low, medium or high (part 2)",
                "Model router: reasoning_effort is supported from router version 2025-11-18",
            ], theme="violet", title_size=19, body_size=15, src=[S_ROUTER]),
        ]
        row(cv, pr.ix, cy, rc, gap=24)
    y3 = pr.bottom + 40
    # ---- shaping the answer
    st = Table([("Feature", 190), ("What it does", 560), ("Where", 300), "Watch out"], [
        [("Structured outputs", "blue"), "The model follows your JSON Schema; the Pydantic helper client.beta.chat.completions.parse parses it", "Chat Completions response_format; Responses text.format",
         "Use for free-form objects; for typed scores use the Decisions API"],
        [("JSON mode", "gray"), "Guarantees valid JSON only, not adherence to a schema", "Chat Completions; added in api-version 2023-12-01-preview",
         "The page itself prefers structured outputs; its supported-model list did not render when read"],
        [("Predicted outputs", "blue"), "Pass known text in prediction to cut latency on small edits (code autocomplete, refactors)", "Chat Completions only; gpt-4o-mini 2024-07-18, gpt-4o 2024-08-06 and 2024-11-20, gpt-4.1, -mini, -nano; since 2025-01-01-preview",
         "Not with tools or function calling, audio, n greater than 1, logprobs, penalties above 0 or max_completion_tokens; unavailable in Southeast Asia"],
        [("Prompt caching", "yellow"), "Identical prompt prefixes are reused: lower latency and cost; cache reads are discounted on Standard and up to 100% off input on Provisioned", "All text APIs; router and Fireworks have their own hints (x-session-affinity, user, prompt_cache_key)",
         "GPT-5.6 and later: prompt_cache_key (above about 15 requests a minute per prefix and key may miss: spread across keys), explicit cache breakpoints (Standard yes, PTU-M no), and cache writes can be charged. Claude: automatic, 5-minute and 1-hour breakpoints"],
    ], w=W, theme="blue", size=14, head_size=15, title="Shaping the answer: structured outputs, JSON mode, predicted outputs and caching", title_size=22)
    st.place(cv, 0, y3)
    lx = 0.0
    cv.text(0, st.bottom + 10, "Learn:", size=12, color=MUTED_)
    lx += 48
    for lab, url in (S_STRUCT, S_JSON, S_PRED, S_CACHE):
        cv.text(lx, st.bottom + 10, lab, size=12, color=LINK, link=url)
        lx += text_size(lab, 12)[0] + 28
    return st.bottom + 30


# ---------------------------------------------------------------------------------------------- sources
def section_sources(cv, y):
    y = banner(cv, y, 5, "Gotchas and sources", None, "gray")
    nw = (W - 3 * G) / 4
    notes = [
        Note(nw, "Web search and Bing grounding send data outside your compliance and geo boundary, and the Microsoft DPA does not apply. Plan data classification before you enable it.",
             kind="gotcha", title="Web search leaves your boundary", size=15, src=[S_WEB]),
        Note(nw, "The Decisions API supports only gpt-6-luna and is rolling out (East US 2 excluded). Microsoft-Decision-1 is a different model on a different route with different vocabulary.",
             kind="gotcha", title="Two decision APIs", size=15, src=[S_DEC, S_MSDEC]),
        Note(nw, "Programmatic tool calling, multi-agent (GPT-5.6, api-version=preview), skills and shell, and WebSocket mode all need a supporting model, api-version and SDK. Check support first.",
             kind="warn", title="Check support first", size=15, src=[S_RESP]),
        Note(nw, "The deep research how-to calls o3-deep-research through the Responses API on an Azure OpenAI deployment, while the models page says it is available only with "
             "Foundry Agent Service. The Responses supported-models list and the Models page also differ slightly.", kind="warn", title="Docs disagree", size=15, src=[S_DEEP]),
    ]
    _, nb = row(cv, 0, y, notes, gap=G)
    y = nb + 40
    sources(cv, 0, y, [
        ("Endpoints for Foundry Models", learn("foundry-models/concepts/endpoints")),
        ("Responses API", learn("openai/how-to/responses")),
        ("Function calling", learn("openai/how-to/function-calling")),
        ("Programmatic tool calling", learn("openai/concepts/programmatic-tool-calling")),
        ("Tool search", learn("openai/how-to/tool-search")),
        ("Web search", learn("openai/how-to/web-search")),
        ("Deep research", learn("openai/how-to/deep-research")),
        ("Shell tool", learn("openai/how-to/shells")),
        ("Multi-agent orchestration (preview)", learn("openai/how-to/responses-multi-agent")),
        ("WebSocket mode", learn("openai/how-to/websockets")),
        ("Chat Completions API", learn("openai/how-to/chatgpt")),
        ("Decisions API", learn("openai/how-to/decisions")),
        ("Microsoft-Decision-1", learn("foundry-models/how-to/use-foundry-models-microsoft-decision")),
        ("Reasoning models", learn("openai/how-to/reasoning")),
    ], w=W, cols=3)
