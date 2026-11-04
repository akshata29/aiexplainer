"""Under the hood: one Responses call, part 2 - four variants of the call (client-side function, MCP approval,
background and reconnect, Foundry IQ), the time and limit markers along the path, what nobody documents, and the
places where the documentation disagrees.

Evidence convention (same as part 1): solid = documented on Microsoft Learn, dashed amber = video/blog only,
dotted grey '?' = not documented."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-request-lifecycle-part-2", title="One Responses call, part 2: variants, limits and what nobody documents",
    section="8", order=3.5,
    description="Four variants of the Responses call (client-side function, MCP approval, background and reconnect, Foundry IQ), the time and limit "
                "markers along the path, the things nobody documents and the docs that disagree.",
    tags=["responses api", "approvals", "limits", "background mode", "docs disagree"],
)

W = 3300
MAIN = 2260
SIDE_X = MAIN + 80
SIDE_W = W - SIDE_X
GREY = "#868e96"
RED = "#c92a2a"
LR = metrics.line_ratio()
LD = learn
YT = "https://www.youtube.com/watch?v="


# ---------------------------------------------------------------------------------------------- helpers
def retag(card, prefix):
    """Card.src lines always read 'Learn: ...'; relabel them for video / blog evidence."""
    card.src_lines = [(t.replace("Learn: ", f"{prefix}: ", 1), u, y) for (t, u, y) in card.src_lines]
    return card


def vb_card(w, title, body, theme="yellow", **kw):
    """Video / blog-only claim: dashed amber border."""
    return Card(w, f"(video/blog) {title}", body, theme=theme, fill="soft", dash="dashed", **kw)


def nd_box(w, label, sub=None, h=None, **kw):
    """Not documented: dotted grey '?' box."""
    return Box(w, f"? {label}", sub=sub, h=h, theme="gray", fill="soft", dash="dotted", **kw)


def link_lines(cv, x, y, items, size=12, prefix="Learn: "):
    for label, url in items:
        t = cv.text(x, y, f"{prefix}{label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def src_panel(cv, x, y, items, w, cols, title, theme="gray", dash="solid", size=14):
    """Citation panel (own version so Learn sources keep a solid border and video/blog sources a dashed one)."""
    th = THEMES[theme]
    colw = (w - 40 - 24 * (cols - 1)) / cols
    entries = []
    for label, url in items:
        l1 = wrap_text(label, colw * 0.965, size)
        l2 = wrap_text(short_url(url), colw * 0.965, size - 2, MONO)
        h = len(l1) * size * LR + len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
        entries.append((l1, l2, url, h))
    per_col = -(-len(entries) // cols)
    heights = [sum(e[3] for e in entries[c * per_col:(c + 1) * per_col]) for c in range(cols)]
    H = 30 + max(heights) + 36
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash=dash)
        cv.text(x + 20, y + 14, title, size=size + 4, color=th.deep)
        for c in range(cols):
            cx = x + 20 + c * (colw + 24)
            cy = y + 14 + 30 + 6
            for l1, l2, url, h in entries[c * per_col:(c + 1) * per_col]:
                cv.text(cx, cy, "\n".join(l1), size=size, color=INK)
                cy += len(l1) * size * LR
                cv.text(cx, cy, "\n".join(l2), size=size - 2, color=LINK, font=MONO, link=url)
                cy += len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
    cv.register("sources", x, y, w, H)
    return y + H


def tile(cv, x, y, w, h, big, caption, theme, kind="doc"):
    """Big-number tile: solid hatch = Learn, dashed soft = video/blog, dotted grey = not documented."""
    th = THEMES[theme]
    if kind == "doc":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y, w, h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
    cv.text(x, y + 10, big, size=36, color=th.deep if kind != "nd" else GREY, align="center", w=w)
    lines = wrap_text(caption, (w - 30) * 0.96, 15)
    cv.text(x + 15, y + 10 + 36 * 1.25 + 2, "\n".join(lines), size=15, color=INK if kind != "nd" else MUTED,
            align="center", w=w - 30)
    cv.register("tile", x, y, w, h)


def evidence_legend(cv, x, y):
    cx = x
    for kind, label in (("doc", "Solid + hatch: documented on Microsoft Learn"),
                        ("vb", "Dashed + soft, tagged (video/blog): only a video or blog says so"),
                        ("nd", "Dotted grey ?: not documented")):
        if kind == "doc":
            cv.rect(cx, y, 64, 34, stroke="#2f9e44", fill="#b2f2bb", style="hachure", sw=2)
        elif kind == "vb":
            cv.rect(cx, y, 64, 34, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, y, 64, 34, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            cv.text(cx + 24, y + 3, "?", size=26, color=GREY)
        t = cv.text(cx + 78, y + 5, label, size=17)
        cx += 78 + t.w + 56
    draw_badge(cv, cx, y + 4, "preview")
    t = cv.text(cx + 82, y + 5, "Preview feature (check Learn before relying on it)", size=17)
    cx += 82 + t.w + 56
    cv.text(cx, y + 5, "Time-sensitive facts carry: as of 2026-11-03", size=17, color=RED)
    return y + 46


def strip(cv, x, y, w, title, sub, steps, cut=None, cut_label="response ends: your app acts"):
    """Horizontal chain of step boxes joined by arrows. steps: [(label, theme, icon)]. Returns the bottom y."""
    cv.text(x, y, title, size=22, color=INK)
    if sub:
        cv.text(x + metrics.text_size(title, 22)[0] + 22, y + 5, sub, size=16, color=MUTED)
    gap = 38
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    boxes = [Box(bw, label, theme=theme, fill="soft", icon=icon, icon_pos="left", icon_size=28, size=15, pad=8)
             for (label, theme, icon) in steps]
    H = max(b.h for b in boxes)
    ty = y + 52
    for i, b in enumerate(boxes):
        b.place(cv, x + i * (bw + gap), ty, h=H)
        if i:
            arrow(cv, [(b.x - gap + 6, ty + H / 2), (b.x - 6, ty + H / 2)], color=INK, sw=2.5)
    if cut is not None:
        cx = boxes[cut].x - gap / 2
        cv.line((cx, ty - 16), (cx, ty + H + 16), stroke=RED, sw=2, dash="dotted")
        tw = metrics.text_size(cut_label, 14)[0]
        cv.text(cx - tw / 2, ty - 38, cut_label, size=14, color=RED)
    return ty + H


# ---------------------------------------------------------------------------------------------- variants
def variants_section(cv, y):
    _, hb = section_header(cv, 0, y, "Four variants of the same call", w=W,
                           sub="Same gates and the same identities as part 1; what changes is where the response ends and who acts next")
    y = hb + 34
    y = strip(cv, 0, y, W, "A  Client-side function call", "two round trips; the function runs in your app, not in the service", [
        ("Call 1: POST /responses", "gray", "users"), ("Gate 1: user input", "pink", "content-safety"), ("Model call", "blue", "openai"),
        ("function_call item", "blue", "openai"), ("Response completes", "green", "foundry"),
        ("Your code runs the function", "gray", "users"), ("Call 2: function_call_output, same conversation", "gray", "users"),
        ("Model call", "blue", "openai"), ("Gate 4: output", "pink", "content-safety"), ("Answer streams back", "green", "foundry"),
    ], cut=5) + 56
    y = strip(cv, 0, y, W, "B  MCP tool with approval", "two round trips; the approval must come back in the same conversation", [
        ("Call 1: POST /responses", "gray", "users"), ("Model call", "blue", "openai"), ("Gate 2: tool call (preview)", "pink", "content-safety"),
        ("mcp_approval_request: the response ends", "green", "foundry"), ("A human approves", "gray", "users"),
        ("Call 2: mcp_approval_response, same conversation", "gray", "users"), ("Tools Service runs the MCP tool", "orange", "toolbox-icon"),
        ("Gate 3: tool response (preview)", "pink", "content-safety"), ("Model call", "blue", "openai"), ("Gate 4: output", "pink", "content-safety"),
    ], cut=4, cut_label="response ends: a human acts") + 56
    y = strip(cv, 0, y, W, "C  Background mode and reconnect", "background needs store=true; streaming can resume only if the first call used stream=true", [
        ("background=true (needs store=true)", "gray", "users"), ("queued", "green", "foundry"), ("in_progress", "green", "foundry"),
        ("Poll, or stream with starting_after", "gray", "users"),
        ("Reconnect: GET /responses/{id}?stream=true&starting_after=seq", "gray", "users"),
        ("completed, failed or cancelled; cancel is idempotent", "green", "foundry"),
        ("Hosted agents: resilient background tasks survive container loss (preview)", "green", "vm"),
    ]) + 56
    y = strip(cv, 0, y, W, "D  Foundry IQ tool call", "an MCP tool call that crosses two identities; the retrieval itself is in the Foundry IQ canvas", [
        ("Model emits an MCP tool call: knowledge_base_retrieve", "orange", "toolbox-icon"),
        ("Agent Service calls the knowledge base MCP endpoint", "green", "foundry"),
        ("RemoteTool connection, as the project MI", "teal", "managed-identity"),
        ("x-ms-query-source-authorization carries the user (OBO, preview)", "violet", "users"),
        ("AI Search knowledge base: see 'Agentic retrieval and Foundry IQ'", "teal", "ai-search"),
        ("Results join the tool loop, then Gate 3", "pink", "content-safety"),
    ])
    ly = link_lines(cv, 0, y + 14, [("Function calling", LD("agents/how-to/tools/function-calling")),
                                    ("Model Context Protocol tool: approvals", LD("agents/how-to/tools/model-context-protocol")),
                                    ("Stream with reconnect", LD("agents/how-to/stream-with-reconnect")),
                                    ("Add human-in-the-loop", LD("agents/how-to/add-human-in-the-loop"))])
    return ly


# ---------------------------------------------------------------------------------------------- limits
def limits_section(cv, y):
    _, hb = section_header(cv, 0, y, "Time and limit markers along the path (as of 2026-11-03)", w=W,
                           sub="Only numbers that a Learn page states; speaker figures are labelled and kept apart")
    y0 = hb + 30
    rows = [
        [("Each guardrail intervention point", "pink"), "About +50 to 100 ms", ("Learn", "green")],
        [("Model router", "blue"), "'Negligible overhead' (Learn). A speaker's '~50 ms' is a video figure", ("Learn; speaker figure (video)", "yellow")],
        [("PTU deployment full", "blue"), "Immediate HTTP 429 with retry-after-ms; no queue. Spillover can retry on a pay-as-you-go deployment", ("Learn", "green")],
        [("Non-streaming MCP tool call", "orange"), "100 s timeout: use background mode for slow tools", ("Learn", "green")],
        [("Background response", "violet"), "Needs store=true; higher time to first token; streaming resumes only if the original call had stream=true", ("Learn", "green")],
        [("Stored response retention", "cyan"), "30 days by default (Azure OpenAI Responses page) versus 'persists until you delete it' (Agent Service pages)", ("Learn, docs disagree", "orange")],
        [("Hosted session idle and retention", "green"), "Idle timeout 900 s by default (120 to 14,400 s); the session is deleted after 30 days of inactivity", ("Learn", "green")],
        [("Code interpreter session", "orange"), "1 h active and 30 min idle (Agent Service tool page); the raw Responses API page says a container expires after 20 min unused", ("Learn, docs disagree", "orange")],
        [("Hosted guardrail limits", "pink"), "A request over 2 MB is unscreened; a buffered response over 1 MB returns 502; each check is truncated at 10,000 characters", ("Learn", "green")],
    ]
    t = Table([("Where on the path", 320), ("Marker", 1480), "Evidence"], rows, w=MAIN, theme="yellow", size=14, head_size=15,
              title="What the documentation actually says", title_size=22)
    t.place(cv, 0, y0)
    ly = link_lines(cv, 0, t.bottom + 8, [("Guardrail intervention points", LD("guardrails/intervention-points")),
                                          ("Responses API", LD("openai/how-to/responses")),
                                          ("Hosted agent guardrails", LD("agents/concepts/hosted-agent-guardrails")),
                                          ("Manage hosted sessions", LD("agents/how-to/manage-hosted-sessions"))])
    vb = vb_card(SIDE_W, "Figures that only a speaker gave", [
        "Model router: '~50 ms' overhead (Model Mondays, about 0:03 to 0:04)",
        "Hosted cold start: 'seconds, low variance' (launch blog); Learn says 'predictable' and gives no number",
        "Idle shutdown: 'about 15 minutes' in the BRK243 demo - consistent with the 900 s default, but the default is the documented number",
    ], src=[("Model Mondays: Spotlight on Model router", YT + "od_WTpE2nH4"), ("Build 2026 BRK243", YT + "e_ZJy3RsNkg")])
    retag(vb, "Video")
    vb.place(cv, SIDE_X, y0)
    return max(ly, vb.bottom)


# ---------------------------------------------------------------------------------------------- not documented
def unknown_section(cv, y):
    _, hb = section_header(cv, 0, y, "What nobody documents", w=W,
                           sub="Searched on 2026-11-03: Learn, 19 videos, blogs and repos. Grey boxes stay grey until a source says more")
    y0 = hb + 30
    items = [
        ("Orchestrator internals", "scheduler and queue, loop-iteration cap, whole-run timeout, retry policy"),
        ("Prompt-agent identity on the model hop", "hosted agents use the project MI proxy; the prompt-agent runtime isn't documented"),
        ("Gate 1 and hydrated history", "whether the guardrail re-scans the history loaded in step 5"),
        ("Default version", "which version runs when agent_reference carries only a name"),
        ("Persistence commit order", "when items are committed relative to streaming"),
        ("Gates 2 and 3 in hosted containers", "for tools your container runs; the egress policy is the documented analogue"),
        ("Hosted compute", "hypervisor or VMM, guest OS, snapshot restore, warm pool, a numeric cold start"),
        ("Guardrail classifier hosting", "where the classifiers run and their latency beyond '+50 to 100 ms'"),
    ]
    gap = 30
    bw = (W - 3 * gap) / 4
    boxes = [nd_box(bw, label, sub=sub, size=17, sub_size=14, pad=12) for label, sub in items]
    h = max(b.h for b in boxes)
    for i, b in enumerate(boxes):
        r, c = divmod(i, 4)
        b.place(cv, c * (bw + gap), y0 + r * (h + gap), h=h)
    return y0 + 2 * h + gap


# ---------------------------------------------------------------------------------------------- docs disagree + gotchas
def notes_section(cv, y):
    _, hb = section_header(cv, 0, y, "Where the docs disagree, and what to remember", w=W)
    y0 = hb + 30
    cw = (W - 2 * 40) / 3
    r1 = [
        Note(cw, "The hosted-agents concept page says traffic splitting between versions isn't supported. The rollout guide and REST samples show versionSelector "
                 "with FixedRatio percentages, and the launch blog mentions weighted rollouts (video/blog). Treat percentage rollouts as unconfirmed.",
             kind="warn", title="Docs disagree: hosted-agent version traffic splitting",
             src=[("Hosted agents", LD("agents/concepts/hosted-agents"))]),
        Note(cw, "The Azure OpenAI Responses page says stored responses are retained 30 days by default and can be deleted by id. The Agent Service pages say data "
                 "persists until you delete it. This canvas shows both and draws no single number.",
             kind="warn", title="Docs disagree: how long is a stored response kept?",
             src=[("Responses API", LD("openai/how-to/responses")), ("Agent Service runtime components", LD("agents/concepts/runtime-components"))]),
        Note(cw, "The Agent Service tool page says 1 hour active and 30 minutes idle; the raw Responses API page says a container expires after 20 minutes unused. "
                 "Different surfaces: cite the Agent Service number for agents.",
             kind="warn", title="Docs disagree: code interpreter session lifetime",
             src=[("Code interpreter tool", LD("agents/how-to/tools/code-interpreter"))]),
    ]
    r, b1 = row(cv, 0, y0, r1, gap=40)
    r2 = [
        Note(cw, "runtime-components addresses an agent by name and version, with no GUID. The hosted contract injects FOUNDRY_AGENT_ID, which is a GUID. "
                 "Read name plus version as the key and the GUID as an environment variable only.",
             kind="info", title="Docs differ: what identifies an agent?",
             src=[("Hosted agent runtime contract", LD("agents/concepts/hosted-agent-contract"))]),
        Note(cw, "Blogs announced hosted agents GA on 2026-07-09 (video/blog). Learn's hosted pages carry no GA banner, and long-running resilience, AgentBlueprint audiences "
                 "and hosted guardrails are still preview. Colour per feature, not per product.",
             kind="warn", title="Docs disagree: is hosted-agent GA?", dash="dashed"),
        Note(cw, "The function-calling page still says 'Runs expire 10 minutes after creation', which is legacy Assistants wording. The Responses-era flow has no run "
                 "object, so no 10-minute number is drawn here.",
             kind="info", title="Legacy wording not drawn: run expiry",
             src=[("Function calling", LD("agents/how-to/tools/function-calling"))]),
    ]
    r, b2 = row(cv, 0, b1 + 40, r2, gap=40)
    cw4 = (W - 3 * 40) / 4
    r3 = [
        Note(cw4, "The caller (gateway), the project MI (state, model proxy, service spans), the agent identity (tools, in-sandbox calls) and the user (delegated tools) "
                  "touch different things. Never draw one 'Foundry' identity.", kind="key", title="Which identity touches what"),
        Note(cw4, "Approvals and client-side functions each cost an extra Responses round trip and must stay in the same conversation "
                  "(or previous_response_id for non-harness agents).", kind="gotcha", title="Extra round trips"),
        Note(cw4, "Default output filtering buffers (higher time to first token); the async filter retracts after the fact; a hosted blocked stream is HTTP 200 "
                  "plus a terminal SSE error.", kind="gotcha", title="Streaming versus filtering"),
        Note(cw4, "100 s for a non-streaming MCP call; PTU 429s are immediate; cold start isn't quantified on Learn. Plan retries and background mode accordingly.",
             kind="tip", title="Timeouts to plan for"),
    ]
    r, b3 = row(cv, 0, b2 + 40, r3, gap=40)
    return b3


# ---------------------------------------------------------------------------------------------- sources
def sources_block(cv, y):
    learn_items = [
        ("Agent Service runtime components (agent, conversation, response lifecycle)", LD("agents/concepts/runtime-components")),
        ("Responses API: retention, background mode, starting_after", LD("openai/how-to/responses")),
        ("Model Context Protocol tool: approvals, allowed_tools, timeouts", LD("agents/how-to/tools/model-context-protocol")),
        ("Function calling", LD("agents/how-to/tools/function-calling")),
        ("Code interpreter tool", LD("agents/how-to/tools/code-interpreter")),
        ("Stream with reconnect", LD("agents/how-to/stream-with-reconnect")),
        ("Add human-in-the-loop", LD("agents/how-to/add-human-in-the-loop")),
        ("Guardrail intervention points", LD("guardrails/intervention-points")),
        ("Hosted agent guardrails", LD("agents/concepts/hosted-agent-guardrails")),
        ("Hosted agents", LD("agents/concepts/hosted-agents")),
        ("Hosted agent runtime contract", LD("agents/concepts/hosted-agent-contract")),
        ("Manage hosted sessions", LD("agents/how-to/manage-hosted-sessions")),
    ]
    vb_items = [
        ("Model Mondays: Spotlight on Model router (about 0:03)", YT + "od_WTpE2nH4"),
        ("Build 2026 BRK243 (about 0:14 to 0:20)", YT + "e_ZJy3RsNkg"),
        ("Foundry blog: Introducing the new hosted agents (2026-04-22)",
         "https://devblogs.microsoft.com/foundry/introducing-the-new-hosted-agents-in-foundry-agent-service-secure-scalable-compute-built-for-agents/"),
        ("Azure blog: GPT-5.6 now available in Microsoft Foundry (2026-07-09, hosted agents GA)",
         "https://azure.microsoft.com/en-us/blog/gpt-5-6-now-available-in-microsoft-foundry/"),
    ]
    b1 = src_panel(cv, 0, y, learn_items, MAIN, 2, "Sources and further reading (Microsoft Learn)")
    b2 = src_panel(cv, SIDE_X, y, vb_items, SIDE_W, 1, "Sources: video and blog (not Learn)", theme="yellow", dash="dashed")
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "One Responses call, part 2: variants, limits and what nobody documents",
        "Under the hood - the other shapes a call can take, the numbers along the path, and the grey areas. Part 1 follows one call hop by hop",
        icon="foundry", w=W)
    y = bottom + 34
    tiles = [
        ("+50-100 ms", "added by each guardrail intervention point", "pink", "doc"),
        ("429", "PTU deployment full: immediate, with retry-after-ms, no queue", "blue", "doc"),
        ("100 s", "timeout for a non-streaming MCP tool call; use background mode", "orange", "doc"),
        ("900 s", "default hosted-session idle timeout (120 to 14,400 s)", "green", "doc"),
        ("30 d", "hosted session kept after its last activity", "green", "doc"),
        ("1 h | 30 min", "code interpreter session: active | idle (Agent Service tool page)", "orange", "doc"),
        ("2 MB | 1 MB", "hosted guardrails: request unscreened | buffered response returns 502", "pink", "doc"),
        ("? s", "orchestrator loop cap, whole-run timeout and retry policy are not documented", "gray", "nd"),
    ]
    tw = (W - 7 * 24) / 8
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + 24), y, tw, 150, big, cap, th, kind)
    y = evidence_legend(cv, 0, y + 150 + 24) + 50
    y = variants_section(cv, y) + 50
    y = limits_section(cv, y) + 50
    y = unknown_section(cv, y) + 60
    y = notes_section(cv, y) + 60
    sources_block(cv, y)
