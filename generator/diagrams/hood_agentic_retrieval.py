"""Under the hood: agentic retrieval / Foundry IQ pipeline - one knowledge_base_retrieve call, stage by stage.

Evidence convention (same as the other 'under the hood' canvases):
  solid border + hatch  = documented on Microsoft Learn
  dashed border + soft  = only a video / blog says it (labelled "(video/blog)")
  dotted grey + "?"     = not documented anywhere checked
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="hood-agentic-retrieval",
    title="Agentic retrieval and Foundry IQ: the pipeline under the hood",
    section="8", order=5,
    description="One knowledge_base_retrieve call stage by stage - LLM query planning, parallel keyword/vector/hybrid subqueries, "
                "semantic reranking, merge, citations and answer synthesis - with reasoning-effort levels, knowledge-source "
                "types and ingestion, limits, and the GA (2026-04-01) vs preview (2026-08-01-preview) split.",
    tags=["agentic retrieval", "foundry iq", "azure ai search", "knowledge base", "reasoning effort", "rag"],
)

W = 3160
GREY = "#868e96"


def S(path: str) -> str:
    """Azure AI Search Learn page."""
    return learn("azure/search/" + path, base="")


# ---------------------------------------------------------------- citations (label, url)
L_OVERVIEW = ("Agentic retrieval overview", S("agentic-retrieval-overview"))
L_EFFORT = ("Set the retrieval reasoning effort", S("agentic-retrieval-how-to-set-retrieval-reasoning-effort"))
L_KS = ("What is a knowledge source?", S("agentic-knowledge-source-overview"))
L_RETRIEVE = ("Call the retrieve action", S("agentic-retrieval-how-to-retrieve"))
L_SYNTH = ("Use answer synthesis", S("agentic-retrieval-how-to-answer-synthesis"))
L_LIMITS = ("Azure AI Search limits: agentic retrieval", S("search-limits-quotas-capacity"))
L_MIGRATE = ("Migrate agentic retrieval code", S("agentic-retrieval-how-to-migrate"))
L_IQ = ("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq"))
L_IQ_CONNECT = ("Connect a Foundry IQ knowledge base", learn("agents/how-to/foundry-iq-connect"))
L_DELEG = ("User delegation (Foundry IQ source authorization)", learn("agents/concepts/user-delegation"))

U_BRK246 = "https://www.youtube.com/watch?v=FRptM_WiBRg"
U_BRK196 = "https://www.youtube.com/watch?v=slDdNIQCJBQ"
U_SAVILL = "https://www.youtube.com/watch?v=uDVkcZwB0EU"
U_MECH = "https://www.youtube.com/watch?v=bHL1jbWjJUc"
U_BLOG_BUILD = "https://devblogs.microsoft.com/foundry/agent-service-build2026/"


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
            cv.rect(cx, cy, 64, 32, stroke="#1971c2", fill="#a5d8ff", style="hachure", sw=2)
        elif dash == "dashed":
            cv.rect(cx, cy, 64, 32, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, cy, 64, 32, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            mw, mh = text_size(mark, 20)
            cv.text(cx + (64 - mw) / 2, cy + (32 - mh) / 2, mark, size=20, color=GREY)
        cv.text(cx + 78, cy + 5, label, size=15, color=INK)
        cx += w + 36


def banner(cv: Canvas, y: float, letter: str, title: str, sub: str, theme: str = "teal") -> float:
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


# ====================================================================== build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "Agentic retrieval and Foundry IQ: the pipeline under the hood",
        "How one agent question becomes a grounded, cited, permission-filtered answer - what runs where, what is GA, what is preview (as of 2026-11-03)",
        w=W)
    evidence_key(cv, W, 6)

    y = strip(cv, bottom + 40)
    y = section_a(cv, y + 56)
    y = plan_demo(cv, y + 56)
    y = section_b(cv, y + 60)
    y = section_c(cv, y + 60)
    y = section_d(cv, y + 60)
    y = section_e(cv, y + 60)
    y = section_f(cv, y + 60)
    y = section_g(cv, y + 60)
    y = section_sources(cv, y + 60)


# ---------------------------------------------------------------- summary strip
def strip(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Seven things to hold in your head", size=30, w=W)
    see_also(cv, W, y + 2, ["Azure AI Search: the knowledge layer", "Enterprise RAG / knowledge-grounded agent",
                            "Microsoft IQ: the enterprise-context layer"])
    y += 62
    tiles = [
        ("3 layers", "(video/blog) Foundry integration, agentic retrieval, core retrieval engine on Azure AI Search", "teal", "vb"),
        ("4 stages", "Initiate, plan queries, execute subqueries in parallel, synthesize the results: Learn's four-step workflow", "teal", "doc"),
        ("4 efforts", "minimal, low (default), medium, auto (preview) decide how much LLM work happens", "blue", "doc"),
        ("12 sources", "6 indexed (ingested before query time) and 6 remote (fetched live) knowledge-source kinds", "teal", "doc"),
        ("2 API versions", "2026-04-01 is the GA subset; 2026-08-01-preview adds planning, synthesis and the rest", "orange", "doc"),
        ("2 meters", "Azure AI Search retrieval tokens, plus Azure OpenAI tokens for planning and synthesis", "yellow", "doc"),
        ("? ranker", "L2 / L3 ranker models, the planner prompt and the merge algorithm are not documented", "gray", "nd"),
    ]
    gap = 28
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + gap), y, tw, 140, big, cap, th, kind)
    return y + 140


# ---------------------------------------------------------------- A: the swimlane pipeline
CW = 300          # box width
LH, LG = 176, 14  # lane height / gap
BOX_PAD = 18      # lane top -> box top
BH = 136          # standard box height


def colx(c: int) -> float:
    """x of pipeline column c (0..6); the gutter after column 2 hosts the fan-out bus, the one after 5 gets labels."""
    return 238 + c * 392 + (110 if c >= 3 else 0) + (60 if c >= 6 else 0)


def lane_band(cv: Canvas, y: float, title: str, sub: str, theme: str, icon: str, h: float = LH) -> None:
    th = THEMES[theme]
    cv.rect(0, y, W, h, stroke=th.stroke, fill=th.soft, style="solid", sw=1.5, dash="dotted", rough=0)
    place_icon(cv, icon, 16, y + 16, 34)
    cv.text(16, y + 60, "\n".join(wrap_text(title, 196, 21)), size=21, color=th.deep)
    t_h = len(wrap_text(title, 196, 21)) * 21 * 1.25
    cv.text(16, y + 66 + t_h, "\n".join(wrap_text(sub, 196, 14)), size=14, color=MUTED)


def step_box(cv: Canvas, c: int, lane_y: float, n, label: str, sub: str, theme: str, *, h=BH, badge=None, shape="rect",
             w=CW) -> Box:
    b = Box(w, label, sub=sub, theme=theme, size=18, sub_size=14, h=h, fill="hatch", shape=shape)
    b.place(cv, colx(c), lane_y + BOX_PAD)
    if b.h > LH - BOX_PAD - 8:
        cv.warn(f"hero box {label!r} is {b.h:.0f}px tall; lane inner height is {LH - BOX_PAD - 8}")
    if shape == "diamond":
        numbered(cv, b.x + b.w * 0.25, b.y + b.h * 0.25, n, theme=theme, d=32, size=18)
    else:
        numbered(cv, b.x + 22, b.y + 4, n, theme=theme, d=34 if len(str(n)) > 1 else 32, size=18)
    if badge:
        draw_badge(cv, b.right - 12 - text_size("Preview", 13)[0] - 18, b.y - 12, badge)
    return b


GA_C = "#2f9e44"      # arrow colour: path that exists in the GA 2026-04-01 API (minimal, extractive)
PV_C = "#e8590c"      # arrow colour: stages that need the 2026-08-01-preview API


def arrow_key(cv: Canvas, x: float, y: float) -> None:
    """Small legend for the two arrow colours used in the pipeline."""
    for color, label in ((GA_C, "green arrow: exists in the GA 2026-04-01 API (minimal, extractive)"),
                         (PV_C, "orange arrow: needs the 2026-08-01-preview API")):
        arrow(cv, [(x, y + 11), (x + 64, y + 11)], color=color, sw=3)
        t = cv.text(x + 76, y, label, size=15, color=INK)
        x += 76 + t.w + 34


def section_a(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "A", "One knowledge_base_retrieve call, stage by stage: what runs where",
               "Five swim-lanes show the runtime that does each step. Solid arrows are the main path, dashed arrows are conditional. "
               "Numbers match the text in each box.")
    arrow_key(cv, W - 1190, y0 + 12)
    heights = [LH, LH + 24, LH, LH, LH]           # the LLM lane is taller: its top channel carries the medium-effort retry loop
    ly = []
    cur = y
    for h_ in heights:
        ly.append(cur)
        cur += h_ + LG
    l2 = ly[1] + 24                                  # top of the LLM lane's box row
    lanes = [
        ("Agent + Agent Service", "your agent loop, running in Foundry", "green", "agent"),
        ("LLM", "an Azure OpenAI deployment named in the knowledge base's model configuration", "blue", "openai"),
        ("Knowledge base", "the orchestrator: a resource on your Azure AI Search service", "teal", "ai-search"),
        ("Indexes + ranker", "indexed content, keyword / vector / hybrid queries and the semantic ranker, on your search service",
         "teal", "storage"),
        ("Remote sources", "content fetched at query time through each platform's API", "teal", "api-connections"),
    ]
    for i, (t, s, th, icon) in enumerate(lanes):
        lane_band(cv, ly[i], t, s, th, icon, h=heights[i])

    # ---- boxes
    a1 = step_box(cv, 0, ly[0], 1, "Agent calls the MCP tool",
                  "knowledge_base_retrieve is the only knowledge-base tool Agent Service supports; instructions should force its use",
                  "green")
    a2 = step_box(cv, 1, ly[0], 2, "Agent Service calls the KB",
                  "Project managed identity over a RemoteTool connection, plus the user's token in x-ms-query-source-authorization",
                  "green")
    b1 = step_box(cv, 1, ly[2], 3, "KB receives the retrieve call",
                  "Query + chat history at /knowledgebases/{kb}/mcp. Effort: the request's value, else the KB's, else low",
                  "teal")
    dm = step_box(cv, 2, ly[2], 4, "Effort = minimal?", "", "teal", shape="diamond", h=BH)
    c1 = step_box(cv, 2, l2, 5, "Plan the queries (LLM)",
                  "Split the question + history into focused subqueries; choose sources from name, description and retrievalInstructions",
                  "blue", badge="preview")
    d1 = step_box(cv, 3, ly[3], "6a", "Indexed subqueries",
                  "Keyword, vector or hybrid on each source's index, run locally. ACL and label filters come from the user token",
                  "teal")
    e1 = step_box(cv, 3, ly[4], "6b", "Remote subqueries",
                  "SharePoint, Fabric, MCP server, Work IQ, Bing: fetched live, never ingested. The source enforces permissions",
                  "teal")
    d2 = step_box(cv, 4, ly[3], 7, "Semantic ranker (L2)",
                  "Reranks every subquery's matches. Medium adds an L3 classifier that rescores (0 to 4.0) and can trigger one retry",
                  "teal")
    b3 = step_box(cv, 5, ly[2], 8, "Merge + unified ranking",
                  "Indexed and remote results are merged across subqueries and reranked. Extractive output keeps 200 chunks at most, "
                  "none under a 2.5 reranker score",
                  "teal")
    c3 = step_box(cv, 5, l2, "9a", "Answer synthesis (LLM)",
                  "answerSynthesis only: a grounded answer citing [ref_id:n]. Not allowed at minimal effort",
                  "blue", badge="preview")
    b4 = step_box(cv, 6, ly[2], "9b", "Build the response",
                  "extractiveData (default): the merged chunks, plus references and an activity log if requested. Or the synthesized answer",
                  "teal")
    a3 = step_box(cv, 6, ly[0], 10, "Result back to the agent",
                  "The agent answers with citations; the portal trace shows an execute_tool span for the call",
                  "green")

    # ---- arrows (green = GA 2026-04-01 path, orange = preview-only stages)
    connect(cv, a1, a2, sw=2, color=GA_C)
    connect(cv, a2, b1, a_side="bottom", b_side="top", label="MCP tool call", label_size=14, sw=2, color=GA_C)
    connect(cv, b1, dm, sw=2, color=GA_C)
    connect(cv, dm, c1, a_side="top", b_side="bottom", label="low or medium\n(auto: if its first\npass is weak)", label_size=14,
            label_pos="right", sw=2, color=PV_C)

    bx = colx(2) + CW + 101                      # fan-out bus in the gutter after column 2
    arrow(cv, [(dm.right + 4, dm.cy), (bx, dm.cy)], dash="dashed", label="minimal: skip\nplanning", label_size=14, label_dx=-14,
          sw=2, color=GA_C)
    chip = Chip("fan-out, all in parallel", theme="teal", size=14)
    chip.place(cv, bx - chip.w / 2, ly[3] - 26)
    arrow(cv, [(c1.right + 6, c1.cy), (bx, c1.cy), (bx, chip.y - 2)], end_head=None, sw=2, color=PV_C)
    arrow(cv, [(bx, chip.bottom + 2), (bx, e1.cy), (e1.x - 6, e1.cy)], sw=2, color=GA_C)
    arrow(cv, [(bx, d1.cy), (d1.x - 6, d1.cy)], sw=2, color=GA_C)
    connect(cv, d1, d2, sw=2, color=GA_C)
    arrow(cv, [(e1.right + 6, e1.cy), (d2.cx, e1.cy), (d2.cx, d2.bottom + 6)], sw=2, color=GA_C)
    connect(cv, d2, b3, a_side="right", b_side="left", route="elbow", sw=2, color=GA_C)
    # medium-only retry loop back to the planner, routed over the top channel of the LLM lane
    chan = ly[1] + 14
    arrow(cv, [(d2.cx + 40, d2.y - 6), (d2.cx + 40, chan), (c1.cx, chan), (c1.cx, c1.y - 6)], dash="dashed", sw=2, color=PV_C)
    cv.text(c1.right + 70, chan + 10, "medium only: if the L3 classifier finds the results too weak, ONE retry with a revised "
                                      "plan (it may pick other sources)", size=14, wrap=520)
    connect(cv, b3, b4, label="extractiveData\n(default)", label_size=14, sw=2, color=GA_C)
    connect(cv, b3, c3, a_side="top", b_side="bottom", label="answerSynthesis", label_size=14, sw=2, color=PV_C)
    connect(cv, c3, b4, a_side="right", b_side="top", tb=0.3, route="elbow", label="answer + citations", label_size=14, sw=2,
            color=PV_C)
    connect(cv, b4, a3, a_side="top", b_side="bottom", ta=0.7, tb=0.7, label="tool result", label_size=14, sw=2, color=GA_C)

    # ---- annotations that explain each lane (empty cells of the grid)
    Note(770, "Foundry IQ is not a separate runtime. The same retrieve call works from Foundry Agent Service, Microsoft Agent "
              "Framework or any app through REST or an SDK, and several agents can share one knowledge base.",
         kind="key", title="A knowledge base is one MCP tool to the agent", size=14, title_size=16, pad=10,
         src=[L_IQ]).place(cv, colx(2), ly[0] + BOX_PAD + 8)
    retag(Note(770, "Learn gives no latency numbers. A Build 2026 speaker said a retrieval can take 'a few seconds or sometimes "
                    "maybe 10s' when it iterates. Treat that as a speaker claim, not a documented figure.",
               kind="quote", dash="dashed", title="(video/blog) How long does it take?", size=14, title_size=16, pad=10,
               src=[("BRK246 at 0:33:35", U_BRK246)]), "Video").place(cv, colx(2) + 800, ly[0] + BOX_PAD + 8)
    nd_box(CW, "Planner prompt and loop", "Learn names the planner's inputs, not the prompt or the loop", h=116).place(
        cv, colx(0), l2 + BOX_PAD + 10)
    Note(610, "All the LLM stages use the model configured on the knowledge base. The search service reaches it with its own "
              "managed identity (Cognitive Services User on the Foundry resource).",
         kind="info", title="Whose identity calls the LLM?", size=14, title_size=16, pad=10,
         src=[L_IQ_CONNECT]).place(cv, colx(3) - 50, ly[1] + 68)
    Card(1000, "Indexed sources", [
        "Ingested before query time: your own index, a direct file upload, or an auto-generated indexer pipeline",
        "Queries run locally on the search service: keyword, vector or hybrid. Vector fields need a valid vectorizer or they are ignored",
        "References can carry service-generated citation URLs (preview)",
    ], theme="teal", fill="soft", title_size=18, body_size=15, gap=4, pad=12, src=[L_KS]).place(
        cv, colx(0), ly[3] + BOX_PAD + 6)
    Card(1000, "Remote sources", [
        "Nothing is copied into Search: the engine calls each platform's API at query time",
        "Bing travels over the public internet; SharePoint and Fabric stay inside your Microsoft tenant",
        "Remote results carry no citation URLs; permissions are enforced at the source with the user's token",
    ], theme="teal", fill="soft", title_size=18, body_size=15, gap=4, pad=12, src=[L_KS]).place(
        cv, colx(0), ly[4] + BOX_PAD + 6)
    nd_box(CW + 40, "Ranker models and merge", "L2 / L3 internals and the fusion method are not described", h=116).place(
        cv, colx(5) + 20, ly[3] + BOX_PAD + 10)
    Note(760, "For indexed sources the engine filters with the user identity you pass, and returns UNFILTERED results if it is "
              "omitted. Remote sources enforce permissions at the source.", kind="gotcha",
         title="Permissions ride on the user token", size=14, title_size=16, pad=10,
         src=[L_RETRIEVE]).place(cv, colx(4) + 200, ly[4] + BOX_PAD + 10)
    return ly[4] + LH


def plan_demo(cv: Canvas, y: float) -> float:
    """Illustration of subquery decomposition, using Learn's own multi-part example question."""
    section_header(cv, 0, y, "What planning does to a multi-part question (illustration)", size=24, w=W,
                   sub="The question is Learn's own multi-part example; the three subqueries are invented to show the idea. The real "
                       "plan is model-generated and appears in the activity log",
                   sub_size=15)
    top = y + 78
    cv.text(0, top, "Question and chat history", size=14, color=MUTED)
    q = Bubble(620, "Find me a hotel near the beach, with airport transportation, and that is within walking distance of vegetarian "
                    "restaurants", theme="blue", size=16, tail=None)
    pl = Box(260, "Planner (LLM)", sub="low, medium or auto effort", theme="blue", fill="hatch", size=19, sub_size=14, h=120)
    sqs = ["hotels near the beach", "airport transportation for those hotels", "vegetarian restaurants within walking distance"]
    sh = 3 * 46 + 2 * 12
    mid = top + 26 + sh / 2
    q.place(cv, 0, mid - q.h / 2)
    pl.place(cv, 710, mid - pl.h / 2)
    connect(cv, q, pl, sw=2)
    sx = 710 + 260 + 110
    cv.text(sx, top, "Subqueries (illustrative)", size=14, color=MUTED)
    for i, s in enumerate(sqs):
        b = Box(600, s, theme="teal", fill="soft", size=17, h=46).place(cv, sx, top + 26 + i * 58)
        connect(cv, pl, b, a_side="right", b_side="left", sw=2)
    nx = sx + 600 + 70
    nw = (W - nx - 40) / 2
    n1 = Note(nw, "Each subquery is reranked on its own, then results merge. The activity log keeps the plan: a modelQueryPlanning "
                  "record (tokens, elapsed time, model name) and, per source, the search text it ran (searchIndexArguments.search).",
              kind="info", title="Where to see the real plan", size=14, title_size=16, pad=10, src=[L_RETRIEVE])
    n2 = Note(nw, "Multi-part asks, questions that depend on earlier turns, rewriting (synonym maps plus LLM paraphrasing) and "
                  "spelling mistakes. It costs extra latency compared with a single query.", kind="key",
              title="What a single query cannot do", size=14, title_size=16, pad=10, src=[L_OVERVIEW])
    n1.place(cv, nx, top + 26)
    n2.place(cv, nx + nw + 40, top + 26)
    return max(top + 26 + sh, n1.bottom, n2.bottom)


# ---------------------------------------------------------------- B: reasoning effort
REGIONS_MEDIUM = ["East US 2", "East US", "South Central US", "West US 3", "West US 2", "West US", "Germany West Central",
                  "North Europe", "Switzerland North", "Sweden Central", "Spain Central", "UK South", "Korea Central",
                  "Japan East", "Southeast Asia"]


def section_b(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "B", "How much LLM work? The retrieval reasoning effort dial",
               "Set on the knowledge base and overridden per retrieve request; if neither is set the service uses low. "
               "Effort levels need the 2026-08-01-preview API.", "blue")
    top = y
    lw = 1540
    ty = top + 150
    arrow(cv, [(10, ty), (lw - 10, ty)], sw=4, end_head="arrow")
    cv.text(10, ty + 140, "cheapest, fastest, most predictable", size=14, color=MUTED)
    t = text_size("most LLM processing: deepest search, slowest, most tokens", 14)[0]
    cv.text(lw - t, ty + 140, "most LLM processing: deepest search, slowest, most tokens", size=14, color=MUTED)
    stops = [(190, "minimal", "teal", "No LLM planning. Every source in the knowledge base is searched directly."),
             (770, "low", "blue", "The default. One LLM pass plans the query and picks the sources."),
             (1350, "medium", "indigo", "Adds a semantic classifier that can trigger ONE retry.")]
    for sx, name, th, desc in stops:
        c = THEMES[th]
        cv.ellipse(sx - 20, ty - 20, 40, 40, stroke=c.stroke, fill=c.fill, style="solid", sw=3, rough=0)
        cv.text(sx - 200, ty + 30, name, size=26, color=c.deep, align="center", w=400)
        cv.text(sx - 200, ty + 66, "\n".join(wrap_text(desc, 380, 15)), size=15, color=INK, align="center", w=400)
    oc = THEMES["orange"]
    arrow(cv, [(300, ty - 30), (460, ty - 76), (770, ty - 94), (1080, ty - 76), (1240, ty - 30)], curved=True, sw=3,
          color=oc.stroke)
    cv.text(770 - 380, ty - 158, "auto (preview): a lightweight first pass; if grounding is weak it escalates through LLM "
                                 "planning, up to medium", size=16, color=oc.deep, align="center", w=760, wrap=740)

    cw = 745
    cy = ty + 168
    cards = [
        Card(cw, "minimal", [
            "No LLM planning: direct text and vector searches across ALL sources in the KB; the best-matching passages come back",
            "Predictable: no query expansion, and alwaysQuerySource is ignored",
            "! outputMode must be extractiveData. No answer synthesis, no web knowledge, at most 10 sources per KB",
            "+ The retrieval behaviour of the GA API: 2026-04-01 supports minimal, extractive retrieval only and has no effort setting",
            "Use it to migrate from the Search API or to manage query planning yourself",
        ], theme="teal", badge="GA (2026-04-01)", src=[L_EFFORT, L_OVERVIEW]),
        Card(cw, "low (default)", [
            "One pass of LLM query planning and source selection; subqueries fan out; results merge",
            "Answer synthesis (preview) can add a grounded answer with inline citations",
            "Limits: 5,000 answer tokens; 50 documents for semantic ranking (10 if the ranker uses L3 classification)",
            "Use it for a balance between minimal latency and deeper processing",
        ], theme="blue", badge="preview", src=[L_EFFORT]),
        Card(cw, "medium", [
            "Adds deeper search: a high-precision semantic classifier evaluates the first results",
            "If they are not relevant enough: ONE follow-up iteration with a revised plan; it may reuse or switch sources; "
            "rescored with L3 (0 to 4.0)",
            "Limits: 10,000 answer tokens; 50 documents (20 with L3); select regions only",
            "Each iteration adds latency and billable input tokens",
        ], theme="indigo", badge="preview", src=[L_EFFORT]),
        Card(cw, "auto", [
            "Starts with a lightweight retrieval pass and returns it if grounding is enough; otherwise continues with LLM "
            "planning, up to medium",
            "Needs the 2026-08-01-preview API and a model on the KB; earlier API versions return 400 Bad Request",
            "Available in every region that supports agentic retrieval",
        ], theme="orange", badge="preview", src=[L_EFFORT]),
    ]
    r1 = max(cards[0].h, cards[1].h)
    r2 = max(cards[2].h, cards[3].h)
    cards[0].place(cv, 0, cy, h=r1)
    cards[1].place(cv, cw + 50, cy, h=r1)
    cards[2].place(cv, 0, cy + r1 + 30, h=r2)
    cards[3].place(cv, cw + 50, cy + r1 + 30, h=r2)
    left_bottom = cy + r1 + 30 + r2

    rx, rw = lw + 80, W - lw - 80
    with cv.panel(rx, top, title="Medium effort: select regions only (as of 2026-11-03)", theme="indigo", style="dotted",
                  w=rw, pad=20, title_size=22) as pr:
        ChipFlow(REGIONS_MEDIUM, rw - 40, theme="indigo", size=15).place(cv, pr.ix, pr.iy)
    c2 = Card(rw, "Request-level controls (Learn)", [
        "retrievalReasoningEffort on the KB sets the default; a retrieve request overrides it; if neither is set, low",
        "maxRuntimeInSeconds: minimum 10, default 90, maximum 600. It applies to the Azure AI Search retrieve request only",
        "maxOutputSizeInTokens (maxOutputSize in 2026-05-01-preview and later) sets the length of the grounding string",
        "alwaysQuery on a source, or alwaysQuerySource on a request, forces a source into the query (ignored at minimal)",
        "retrievalInstructions steer which sources the LLM selects or skips, like a prompt",
        "resultsProcessing: rerank (default) or none per source; none skips reranking for that source (preview)",
    ], theme="blue", src=[L_EFFORT, L_RETRIEVE, L_LIMITS])
    c2.place(cv, rx, pr.bottom + 30)
    c3 = vb(rw, "What speakers add", [
        "Iteration: 'could be a few seconds or sometimes maybe 10s' (BRK246 at 0:33:35)",
        "Medium effort 'self-reflection' with a second pass (John Savill at 0:23:51)",
        "Quality gains come from better tool-calling models, a newly trained semantic ranker, better answer synthesis and MCP "
        "parameter binding tuned per model (BRK246 at 0:34:00)",
    ], src=[("BRK246 Foundry IQ (Build 2026)", U_BRK246), ("Deep Dive into Foundry IQ", U_SAVILL)], prefix="Video")
    c3.place(cv, rx, c2.bottom + 30)
    return max(left_bottom, c3.bottom)


# ---------------------------------------------------------------- C: knowledge sources and ingestion
def section_c(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "C", "Knowledge sources and ingestion: what is indexed, what stays remote",
               "12 kinds in Learn's table: six are ingested into an index on your search service, six are fetched live at query time",
               "teal")
    top = y
    PRE = ("preview", "orange")
    NOTAG = ("no preview tag", "green")
    IDX = ("Indexed", "teal")
    REM = ("Remote", "cyan")
    rows = [
        ["Search index", IDX, NOTAG, "Wraps an existing index"],
        ["Azure blob", IDX, NOTAG, "Generates an indexer pipeline from a blob container"],
        ["OneLake", IDX, NOTAG, "Generates an indexer pipeline from a lakehouse"],
        ["Azure SQL", IDX, PRE, "Generates an indexer pipeline from an Azure SQL table or view"],
        ["File", IDX, PRE, "Uploads files directly to Azure AI Search, with no external storage or indexer"],
        ["Indexed SharePoint", IDX, PRE, "Generates an indexer pipeline from a SharePoint site"],
        ["Remote SharePoint", REM, PRE, "Retrieves content from SharePoint"],
        ["Fabric Data Agent", REM, PRE, "Retrieves answers and embedded resources from a Fabric data agent"],
        ["Fabric Ontology", REM, PRE, "Retrieves entity and relationship answers from a Fabric ontology"],
        ["MCP server", REM, PRE, "Retrieves live, tool-backed results from an external MCP server"],
        ["Work IQ", REM, PRE, "Retrieves organizational intelligence from Work IQ"],
        ["Web", REM, NOTAG, "Retrieves real-time grounding data from Microsoft Bing; not supported at minimal effort"],
    ]
    t1 = Table([("Kind", 240), ("Mode", 120), ("Learn tag", 170), ("What it does (Learn's table)", 970)], rows, w=1500,
               theme="teal", size=14, head_size=15, title="12 knowledge-source kinds", title_size=22, first_col_theme="teal")
    t1.place(cv, 0, top)
    cv.text(0, t1.y + t1.h + 8, "'no preview tag' means Learn's table does not mark the kind as preview; the migration page has the "
                                "exact GA list. Docs disagree on Web: the effort page says web knowledge is not supported at minimal "
                                "effort, while the 2026-04-01 migration steps keep a model for a web source.", size=13, color=MUTED,
            link=L_MIGRATE[1], wrap=1500)
    t2 = Table([("Knowledge source", 250), ("Set ingestionPermissionOptions?", 250), ("How permissions are enforced at query time", 1000)], [
        ["Blob or ADLS Gen2", CHECK, "Ingested RBAC scopes, ACLs or Purview labels are matched against the user identity"],
        ["OneLake", CHECK, "Ingested Purview sensitivity labels are matched against the user identity"],
        ["Indexed SharePoint", CHECK, "Ingested SharePoint ACLs or Purview labels are matched against the user identity"],
        ["Remote SharePoint", CROSS, "The Copilot Retrieval API queries SharePoint directly with the user's token"],
        ["Fabric Data Agent / Ontology", CROSS, "The engine swaps the user's token for a Fabric-scoped token and queries on their behalf"],
        ["Work IQ", CROSS, "The engine swaps an app-audience user assertion (x-ms-query-work-iq-source-authorization) for a Work IQ-scoped token"],
    ], w=1500, theme="red", size=14, head_size=15, title="Who enforces permissions at query time (preview)", title_size=22,
        align=["left", "center", "left"])
    t2.place(cv, 0, t1.y + t1.h + 56)
    n1 = Note(1500, "No ingestion-time permission options means the index holds no permission metadata, and the system returns "
                    "results unfiltered regardless of the header. Most sources read x-ms-query-source-authorization; Work IQ is the "
                    "exception.", kind="gotcha", title="Unfiltered by default", size=14, title_size=16, pad=10, src=[L_RETRIEVE])
    n1.place(cv, 0, t2.y + t2.h + 24)
    left_bottom = n1.y + n1.h

    fx = 1550
    ca, cb, cc, cd, gap = 330, 450, 410, 250, 55
    rh, rg = 114, 20
    section_header(cv, fx, top, "How content reaches a knowledge source", size=22, w=W - fx, sub_size=15,
                   sub="Left to right: where it lives, what the search service sets up, how it is queried, how it is ranked")
    fy = top + 90
    xa, xb, xc, xd = fx, fx + ca + gap, fx + ca + cb + 2 * gap, fx + ca + cb + cc + 3 * gap
    for x, h in ((xa, "Where the content lives"), (xb, "What the search service sets up"), (xc, "How it is queried"),
                 (xd, "How it is ranked")):
        cv.text(x, fy - 26, h, size=15, color=MUTED)
    spec = [
        ("Your own search index", "an index you already run on the service", "Search index knowledge source",
         "wraps the existing index; no pipeline is created"),
        ("Files you upload (preview)", "PDFs, Office files and so on", "File knowledge source",
         "the service processes the files into a generated index: no external storage or indexer"),
        ("Blob, OneLake, SharePoint site, Azure SQL (preview)", "an external data store", "Auto-generated pipeline",
         "data source + skillset + indexer + chunked, vectorised index; schedule indexer runs for incremental refresh"),
        ("SharePoint, Fabric, MCP server, Work IQ, Bing", "an external platform", "Remote knowledge source",
         "nothing is ingested; the source object only holds how to call the platform"),
    ]
    a_boxes, b_boxes = [], []
    for i, (la, sa, lb, sb) in enumerate(spec):
        ry = fy + i * (rh + rg)
        a = Box(ca, la, sub=sa, theme="cyan", fill="soft", size=17, sub_size=14, h=rh).place(cv, xa, ry)
        b = Box(cb, lb, sub=sb, theme="teal", fill="hatch", size=17, sub_size=14, h=rh).place(cv, xb, ry)
        a_boxes.append(a)
        b_boxes.append(b)
        connect(cv, a, b, sw=2)
    ih = 3 * rh + 2 * rg
    idx = Box(cc, "Indexed: queried locally", sub="Full-text (keyword), vector or hybrid queries run on your search service. References "
                                                    "can carry service-generated citation URLs (preview).", theme="teal", fill="hatch",
              size=18, sub_size=14, h=ih).place(cv, xc, fy)
    rem = Box(cc, "Remote: queried live", sub="The engine calls the platform's API at query time: the public internet for Bing, "
                                              "your tenant for SharePoint and Fabric. No citation URLs.", theme="teal",
              fill="hatch", size=18, sub_size=14, h=rh).place(cv, xc, fy + 3 * (rh + rg))
    for i in range(3):
        connect(cv, b_boxes[i], idx, a_side="right", b_side="left", tb=((b_boxes[i].cy - idx.y) / idx.h), sw=2)
    connect(cv, b_boxes[3], rem, sw=2)
    uh = 4 * rh + 3 * rg
    uni = Box(cd, "Unified ranking", sub="All retrieved content, indexed or remote, flows through the same pipeline: scored for "
                                         "relevance, merged across queries and reranked before the response returns.",
              theme="teal", fill="solid", size=18, sub_size=14, h=uh).place(cv, xd, fy)
    connect(cv, idx, uni, a_side="right", b_side="left", ta=0.5, tb=((idx.cy - uni.y) / uni.h), sw=2)
    connect(cv, rem, uni, a_side="right", b_side="left", ta=0.5, tb=((rem.cy - uni.y) / uni.h), sw=2)

    ey = fy + uh + 36
    ex = Card(W - fx, "Ingestion extras (preview)", [
        "Purview sensitivity labels: set ingestionPermissionOptions to include sensitivityLabel (blob, indexed OneLake, indexed "
        "SharePoint). A chunked index also needs the label mapped onto each chunk through index projections",
        "Document-embedded images: configure an assetStore (same three kinds) and enable image serving on the KB; retrieve then "
        "injects images into the answer-synthesis prompt",
        "! Do not combine assetStore with ingestionPermissionOptions on the same knowledge source",
        "Private-network ingestion: blob, indexed SharePoint and Azure SQL support private indexer execution (shared private links "
        "for blob and SQL). SharePoint Online is not a shared private link target; private sync is not supported for indexed OneLake",
        "Automatic per-language analyzers (blob, indexed OneLake, indexed SharePoint): the service detects each document's language "
        "and applies a matching Microsoft analyzer",
    ], theme="orange", badge="preview", src=[L_KS])
    ex.place(cv, fx, ey)
    rl = Note(W - fx, "Create a knowledge source before the knowledge base. A source and its KB must live on the same search service. "
                      "To delete a source, first update or delete every KB that references it. Set alwaysQuery: true on a source to "
                      "include it in every query, whatever the effort.", kind="tip", title="Rules for knowledge sources", size=14,
              title_size=16, pad=10, src=[L_KS])
    rl.place(cv, fx, ex.bottom + 26)
    return max(left_bottom, rl.bottom)


# ---------------------------------------------------------------- D: output, citations and the response
def activity_chart(cv: Canvas, x: float, y: float, w: float) -> float:
    """Learn's own sample activity array (low effort) as a small bar chart of each record's elapsedMs."""
    th = THEMES["cyan"]
    rows = [("modelQueryPlanning", 2396, "2,302 in / 109 out tokens"),
            ("searchIndex: demo-financials-ks", 1137, "count 26"),
            ("searchIndex: demo-healthcare-ks", 494, "count 17"),
            ("agenticReasoning", None, "103,368 reasoning tokens"),
            ("modelAnswerSynthesis", 3837, "5,821 in / 344 out tokens")]
    with cv.panel(x, y, title="A real activity array (Learn's sample)", theme="cyan", style="dotted", w=w, pad=16, title_size=20,
                  sub="low effort, answer synthesis on. Bars are each record's own elapsedMs; records can overlap", sub_size=13) as p:
        lab_w, bar_max = 250, 200
        yy = p.iy + 2
        for name, ms, note in rows:
            cv.text(p.ix, yy + 2, name, size=14, color=INK)
            if ms:
                bw = ms / 3837 * bar_max
                cv.rect(p.ix + lab_w, yy, bw, 22, stroke=th.stroke, fill=th.fill, style="hachure", sw=1.5)
                cv.text(p.ix + lab_w + bw + 8, yy + 2, f"{ms:,} ms", size=14, color=th.deep)
            cv.text(p.ix + lab_w + bar_max + 100, yy + 3, note, size=13, color=MUTED)
            yy += 31
    return p.bottom


def section_d(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "D", "What comes back: output modes, citations and the response shape",
               "Grounding chunks or a synthesized answer, plus an activity log and references, over REST, an SDK, an SSE stream or MCP",
               "teal")
    top = y
    cw = 560
    c1 = Card(cw, "extractiveData (default)", [
        "Raw grounding chunks as ONE JSON string in a chat-message response (content type text)",
        "At most 200 chunks; chunks below a 2.5 reranker score are excluded",
        "Length is capped by maxOutputSizeInTokens; an oversized best document can be omitted and the activity log warns",
        "Your app or agent passes the string to an LLM as grounding data",
        "+ The only mode in the GA 2026-04-01 API",
    ], theme="teal", badge="GA (2026-04-01)", src=[L_RETRIEVE])
    c2 = Card(cw, "answerSynthesis", [
        "Set outputMode: answerSynthesis (optional answerInstructions); the KB's LLM writes a natural-language answer",
        "Citations are formatted [ref_id:n] and map to the references array",
        "Not available at minimal effort; billed as Azure OpenAI pay-as-you-go tokens",
        "Needs the search service's managed identity with Cognitive Services User on the Foundry resource",
        "Answer-token caps: 5,000 at low, 10,000 at medium",
    ], theme="blue", badge="preview", src=[L_SYNTH, L_EFFORT])
    h12 = max(c1.h, c2.h)
    c1.place(cv, 0, top, h=h12)
    c2.place(cv, cw + 50, top, h=h12)

    ax = 2 * cw + 50 + 60
    aw = 1000
    with cv.panel(ax, top, title="Response anatomy of the retrieve action", theme="teal", style="dotted", w=aw, pad=18,
                  title_size=22, sub="chat-message style body; fields below as documented for 2026-08-01-preview", sub_size=14) as pa:
        r1 = Card(aw - 36, "response", [
            "The extracted grounding string, or the synthesized answer message, depending on the output mode",
        ], theme="teal", title_size=18, body_size=15)
        r2 = Card(aw - 36, "activity (the query plan and its bill)", [
            "One record per step. Source records (searchIndex, azureBlob, ...) report elapsed time and arguments, including the "
            "semantic ranker",
            "agenticReasoning: reasoning tokens. modelQueryPlanning, modelAnswerSynthesis, modelWebSummarization: input and output "
            "tokens plus the public model name. imageServing: image counts",
        ], theme="cyan", title_size=18, body_size=15)
        r3 = Card(aw - 36, "references (the citation list)", [
            "type, id (the citation key, not the document key), activitySource (links back to the activity), docKey, sourceData",
            "citationUrl (preview): a read-only URL to the document in the backing index; indexed sources only",
        ], theme="gray", title_size=18, body_size=15)
        _, yy = col(cv, pa.ix, pa.iy, [r1, r2, r3], gap=14)
    sx = ax + aw + 50
    mc = Card(W - sx, "The KB as an MCP server", [
        "Endpoint: {search_endpoint}/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview",
        "One tool, knowledge_base_retrieve: the only tool Agent Service supports",
        "! The MCP tool result currently differs from the REST and SDK response shape",
        "Agent instructions should force tool use and render the tool's annotation markers as citations",
    ], theme="orange", icon="mcp", badge="preview", src=[L_RETRIEVE, L_IQ_CONNECT])
    mc.place(cv, sx, top)
    ac_bottom = activity_chart(cv, sx, mc.bottom + 30, W - sx)
    row1_bottom = max(top + h12, pa.bottom, ac_bottom)

    y2 = row1_bottom + 50
    section_header(cv, 0, y2, "Streaming the retrieve call (preview, 2026-08-01-preview)", size=24, w=W,
                   sub="Send Accept: text/event-stream; one HTTP connection stays open and events arrive in order", sub_size=15)
    y2 += 76
    bw, gp = 560, 90
    evs = [
        ("retrieval.started", "First event: request ID, KB name, output mode and the effective effort. If the effort is auto it "
                              "reports auto and does not predict escalation"),
        ("activity.started / .completed", "Query planning, each source and each model call. Several can start before an earlier one "
                                          "completes; match them by id"),
        ("answer.completed", "Once, only for answerSynthesis: the complete synthesized message. There is no token-by-token delta"),
        ("references.completed", "The full references array, sent after every reference is resolved"),
        ("response.completed", "The terminal event: status 200 or 206 plus the complete retrieve response body"),
    ]
    boxes = []
    for i, (lab, sub) in enumerate(evs):
        b = Box(bw, lab, sub=sub, theme="teal", fill="hatch", size=18, sub_size=14, h=150).place(cv, i * (bw + gp), y2)
        numbered(cv, b.x + 20, b.y + 4, i + 1, theme="teal", d=30, size=17)
        boxes.append(b)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=2)
    err = Box(2 * bw + gp, "error: replaces references.completed and response.completed",
              sub="If retrieval fails after the stream opens. The HTTP status stays 200, so check the terminal event, not the status",
              theme="red", fill="soft", dash="dashed", size=17, sub_size=14, h=110).place(cv, boxes[3].x, y2 + 150 + 44)
    connect(cv, boxes[2], err, a_side="bottom", b_side="left", ta=0.5, route="elbow", dash="dashed", color=THEMES["red"].stroke, sw=2)
    sn = Card(2 * bw + gp, "Stream details", [
        "A heartbeat comment arrives about every 15 seconds while the stream is idle; a disconnect cancels the retrieval",
        "No Accept header, or application/json: normal JSON response. An earlier API version returns 406 Not Acceptable",
        "A 206 means some knowledge sources failed: their errors are in the activity array",
    ], theme="teal", fill="soft", title_size=18, body_size=15, gap=4, pad=14, src=[L_RETRIEVE])
    sn.place(cv, 0, y2 + 150 + 44, h=110)
    return max(sn.bottom, err.bottom)


# ---------------------------------------------------------------- E: identities on the knowledge-base path
def halo(cv: Canvas, seq: Sequence, src: int, dst: int, ay: float, text: str, num) -> None:
    """White backing for a sequence label that straddles another actor's lifeline (mirrors Sequence.msg's geometry)."""
    lo, hi = sorted((seq._cx(src), seq._cx(dst)))
    span = hi - lo
    lw = max(span - 50 - (30 if num is not None else 0), 120)
    txt = "\n".join(wrap_text(text, lw, seq.label_size))
    tw, th_ = text_size(txt, seq.label_size)
    tx = lo + (span - tw) / 2 + (12 if num is not None else 0)
    r = cv.rect(tx - 6, ay - th_ - 7, tw + 12, th_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0, rough=0,
                round_=False)
    cv.move_to(r, seq.mark + len(seq.actors))


def section_e(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "E", "Who calls whom: identities and roles on the knowledge-base path",
               "Three different credentials are in play: the project managed identity, the search service's own managed identity, "
               "and the signed-in user's token", "red")
    top = y
    seq = Sequence(cv, 0, top, [
        ("Signed-in user", "gray", "user"),
        ("Agent Service", "green", "agent"),
        ("KB MCP endpoint", "teal", "ai-search"),
        ("LLM deployment", "blue", "openai"),
        ("Knowledge sources", "teal", "storage"),
    ], spacing=410, head_w=240, head_h=70, label_size=15)
    seq.msg(0, 1, "Asks; the agent calls the KB tool", num=1)
    seq.msg(1, 2, "MCP call over the RemoteTool connection", num=2,
            note="Auth: the project managed identity (Search Index Data Reader on the search service). Header "
                 "x-ms-query-source-authorization: the signed-in user's Search token, set by Agent Service")
    seq.msg(2, 3, "LLM: plan the queries, later write the answer", num=3,
            note="Auth: the search service's own system-assigned managed identity, with Cognitive Services User on the Foundry "
                 "resource. Only needed when the KB names an LLM")
    seq.msg(3, 2, "Subqueries and chosen sources", dash="dashed", num=4)
    lifeline_cross = []
    t5 = "Parallel subqueries to every selected source"
    ay = seq.msg(2, 4, t5, num=5,
                 note="Indexed: filtered by the ACLs or labels matched to\nthe user token. Remote: the source enforces permissions")
    lifeline_cross.append((2, 4, ay, t5, 5))
    t6 = "Ranked results"
    ay = seq.msg(4, 2, t6, dash="dashed", num=6)
    lifeline_cross.append((4, 2, ay, t6, 6))
    seq.msg(2, 1, "Chunks or answer + references + activity", dash="dashed", num=7)
    seq.msg(1, 0, "Answer with citations", dash="dashed", num=8)
    sb = seq.end()
    # the two long messages cross the LLM lifeline: put a white halo behind their labels (above the lifelines, below the text)
    for src_, dst_, ay, text_, num_ in lifeline_cross:
        halo(cv, seq, src_, dst_, ay, text_, num_)

    rx = 1990
    rw = W - rx
    t = Table([("Principal", 270), ("Role (Learn)", 400), ("Where and why", rw - 670)], [
        ["Developer", "Foundry Project Manager", "On the project's parent resource: create the RemoteTool project connection"],
        ["Agent users", "Foundry User or Foundry Project Manager", "Same resource: use the MCP tool in agents"],
        ["Project managed identity", "Search Index Data Reader (plus Search Index Data Contributor only if the agent writes)",
         "On the search service"],
        ["Search service system-assigned MI", "Cognitive Services User", "On the Foundry resource; only if the KB specifies an LLM"],
        ["End user (query-time token)", "No search service role needed", "The token only represents the user whose access is evaluated"],
    ], w=rw, theme="red", size=14, head_size=15, title="Roles on the path (Learn)", title_size=22, first_col_theme="red")
    t.place(cv, rx, top)
    n1 = Note(rw, "Create the connection with category RemoteTool (preview), authType ProjectManagedIdentity and the KB's MCP URL as "
                  "target. The agent's MCPTool then lists allowed_tools: knowledge_base_retrieve. Hub-based projects are not "
                  "supported. The documented SDK paths are Python and REST.", kind="info", title="The project connection",
              size=14, title_size=16, pad=10, src=[L_IQ_CONNECT])
    n1.place(cv, rx, t.y + t.h + 26)
    n2 = Note(rw, "Agent Service dynamically sets x-ms-query-source-authorization with the signed-in user's Azure AI Search token. When the "
                  "request targets the agent blueprint it gets that token on the user's behalf (search.azure.com/user_impersonation); "
                  "missing consent can surface as an oauth_consent_request. Omit the token and indexed sources return unfiltered results.",
              kind="gotcha", title="User token, not service token", size=14, title_size=16, pad=10, src=[L_DELEG, L_RETRIEVE])
    n2.place(cv, rx, n1.y + n1.h + 20)
    return max(sb, n2.bottom)


# ---------------------------------------------------------------- F: GA vs preview, limits, billing
def section_f(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "F", "GA vs preview, limits and billing",
               "Status follows the Search REST API version you call, not the product name (as of 2026-11-03)", "orange")
    top = y
    ga = Card(1020, "2026-04-01: the generally available subset", [
        "Input is intents (type semantic, search). There is no running messages transcript: send a new intent for every follow-up",
        "Minimal, extractive retrieval only: no LLM query planning, no answer synthesis, no effort setting",
        "Knowledge sources with no preview tag in Learn's table: search index, Azure blob, OneLake and web (see the web caveat in C)",
        "Response: extracted content, activity (source records, agenticReasoning) and references",
        "Billing consent: a dedicated knowledgeRetrieval property on the search service (management plane)",
        "+ Use it for production workloads that fit this subset",
    ], theme="green", badge="ga", src=[L_OVERVIEW, L_MIGRATE])
    pv = Card(1120, "2026-08-01-preview: everything else", [
        "LLM query planning, answer synthesis, low / medium / auto effort, multi-turn messages",
        "Preview kinds: Azure SQL, File, indexed SharePoint, remote SharePoint, Fabric Data Agent, Fabric Ontology, MCP server, Work IQ",
        "Streaming over SSE, citationUrl, resultsProcessing none, query hints, query-time permissions, sensitivity labels, "
        "embedded images, private ingestion, per-language analyzers",
        "Freshness-aware retrieval, document caps and persisted retrieve defaults arrive in 2026-05-01-preview and later",
        "! No SLA and not recommended for production (Azure AI Search preview terms)",
    ], theme="orange", badge="preview", src=[L_OVERVIEW, L_MIGRATE])
    h = max(ga.h, pv.h)
    ga.place(cv, 0, top, h=h)
    pv.place(cv, 1070, top, h=h)
    nx = 1070 + 1120 + 50
    nw = W - nx
    n1 = Note(nw, "The Azure portal and the Foundry portal give preview-only access to every agentic retrieval capability. Objects "
                  "they create can use preview schemas and need migration when you move to the GA REST version.", kind="preview",
              title="Portals are preview-only", size=14, title_size=16, pad=10, src=[L_OVERVIEW])
    n1.place(cv, nx, top)
    n2 = retag(Note(nw, "A Build 2026 blog calls Foundry IQ generally available, with a serverless tier in preview. Learn's Search "
                        "pages say only a 2026-04-01 subset is GA. This canvas colours each feature by API version, not the product.",
                    kind="warn", title="Docs disagree: is Foundry IQ GA?", size=14, title_size=16, pad=10,
                    src=[("Build 2026: agent-service-build2026 blog", U_BLOG_BUILD)]), "Blog")
    n2.place(cv, nx, n1.y + n1.h + 20)
    y2 = top + h + 50

    lim = Table([("Resource", 290), ("Free", 90), ("Basic", 140), ("S1", 90), ("S2", 90), ("S3", 90), ("S3 HD", 250), ("L1", 90),
                 ("L2", 90), ("Serverless Developer", 280)], [
        ["Knowledge sources per service", "3", "5 or 15", "50", "200", "200", "1000 per partition or 3000 per service", "10", "10", "30"],
        ["Knowledge bases per service", "3", "5 or 15", "50", "200", "200", "1000 per partition or 3000 per service", "10", "10", "30"],
        ["Knowledge sources per knowledge base", "3", "5 or 10", "10", "10", "10", "10", "10", "10", "10"],
    ], w=1500, theme="orange", size=14, head_size=15, title="Per-tier limits (Learn, as of 2026-11-03)", title_size=22,
        first_col_theme="orange")
    lim.place(cv, 0, y2)
    cv.text(0, lim.y + lim.h + 6, "Basic services created before 2024-04-03 have lower limits (5). Some older S3 HD services do not "
                                  "support knowledge bases or sources.", size=13, color=MUTED, link=L_LIMITS[1])
    sel = Table([("API version", 420), ("Effort", 380), ("Free", 130), ("Basic", 280), ("S1 and above", 290)], [
        ["2026-05-01-preview and later", "minimal, low, medium", "3", "5 or 10", "10"],
        ["2026-04-01, 2025-11-01-preview", "minimal (uses every source in the KB)", "3", "5 or 10", "10"],
        ["2025-11-01-preview", "low", "3", "3", "3"],
        ["2025-11-01-preview", "medium", "3", "5", "5"],
    ], w=1500, theme="orange", size=14, head_size=15, title="How many sources one retrieval can select", title_size=22,
        first_col_theme="orange")
    sel.place(cv, 0, lim.y + lim.h + 60)
    left_bottom = sel.y + sel.h

    bx, bw = 1560, W - 1560
    b1 = Card(bw, "Two meters on one call", [
        "Azure AI Search bills retrieval tokens consumed by subquery execution and semantic ranking. The free plan (default) gives "
        "a monthly token allowance; the standard plan adds pay-as-you-go after it",
        "Azure OpenAI bills input and output tokens for query planning and answer synthesis, always pay-as-you-go, on the model "
        "assigned to the KB. Web summarization uses the model too",
        "Cost levers: fewer sources, lower effort, curated content; read the activity log to see what each call spent",
    ], theme="yellow", src=[L_OVERVIEW])
    b1.place(cv, bx, y2)
    bt = Table([("Aspect", 260), ("Classic pipeline", 540), ("Agentic retrieval", bw - 800)], [
        ["Unit", "Query based", "Token based"],
        ["Cost per unit", "Uniform cost per query", "Variable cost per token (depends on reasoning effort)"],
        ["Estimating", "Count queries", "Estimate token usage"],
        ["Free allowance", "Monthly free query allowance", "Monthly free token allowance"],
    ], w=bw, theme="yellow", size=14, head_size=15, title="Classic vs agentic billing", title_size=20, first_col_theme="yellow")
    bt.place(cv, bx, b1.bottom + 26)
    ex = Note(bw, "2,000 retrievals x 3 subqueries x 50 reranked chunks x 500 tokens = 150 million rerank tokens. A plan is about "
                  "2,000 input and 350 output tokens per retrieval on a small model. Rates in Learn's example are illustrative: "
                  "check current pricing.", kind="quote", title="Learn's worked example", size=14, title_size=16, pad=10,
              src=[L_OVERVIEW])
    ex.place(cv, bx, bt.y + bt.h + 24)
    return max(left_bottom, ex.bottom)


# ---------------------------------------------------------------- G: layers, IQ family and gotchas
def section_g(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "G", "Where this sits: three layers, three IQs and the traps",
               "The layering is a speaker's framing (dashed); the components next to it are what Learn documents (solid)", "gray")
    top = y
    layers = [
        ("Foundry integration layer", "Portal and agent productivity: create knowledge bases, connect agents, test in the playground",
         "Foundry portal: Build, Knowledge tab; connect the KB to an agent as an MCP tool", "green"),
        ("Knowledge retrieval system with agentic retrieval", "Iterative query planning across many sources; connects to the other "
                                                              "Microsoft IQ workloads",
         "Knowledge base + knowledge sources + agentic retrieval: LLM planning, parallel subqueries, semantic rerank", "teal"),
        ("Core retrieval engine", "Vector, lexical and hybrid retrieval plus ranking models, with enterprise security and scale",
         "Azure AI Search: the indexing and retrieval infrastructure underneath", "cyan"),
    ]
    lh, lg = 100, 32
    ly0 = top + 40
    cv.text(0, top, "(video/blog) BRK246: three layers", size=17, color=THEMES["yellow"].deep)
    cv.text(1180, top, "Learn: what documents the same stack", size=17, color=THEMES["blue"].deep)
    prev_v = prev_d = None
    for i, (name, sub, doc, th) in enumerate(layers):
        yy = ly0 + i * (lh + lg)
        v = Box(1060, name, sub=sub, theme="yellow", fill="soft", dash="dashed", size=18, sub_size=14, h=lh).place(cv, 0, yy)
        d = Box(1000, doc, theme=th, fill="hatch", size=17, h=lh).place(cv, 1180, yy)
        line_between(cv, v, d, dash="dotted", color=THEMES[th].stroke)
        if prev_v is not None:
            connect(cv, v, prev_v, a_side="top", b_side="bottom", sw=2, color=THEMES["yellow"].stroke)
            connect(cv, d, prev_d, a_side="top", b_side="bottom", sw=2)
        prev_v, prev_d = v, d
    layers_bottom = ly0 + 3 * lh + 2 * lg
    cv.text(0, layers_bottom + 12, "'Foundry IQ doesn't hide options': you can use any layer on its own (BRK246 at 0:07:07).",
            size=14, color=MUTED, link=U_BRK246)

    ix = 2290
    iw = W - ix
    c1 = Card(iw, "Three IQ workloads", [
        "Fabric IQ: a semantic intelligence layer for Fabric: ontologies, semantic models, graphs, data agents",
        "Work IQ: a contextual layer for Microsoft 365: documents, meetings, chats, workflows",
        "Foundry IQ: managed knowledge over Azure, SharePoint, OneLake and the web",
        "Each is standalone; use them together for richer context",
    ], theme="indigo", src=[L_IQ])
    c1.place(cv, ix, top)
    c2 = vb(iw, "Serverless vs dedicated", [
        "Serverless Foundry IQ: 'ten, 20 seconds to create a service', no cost until used, scales to zero (you pay for index storage)",
        "Learn's limits page lists a Serverless Developer tier; the speed claim is the speaker's",
    ], src=[("BRK246 at 0:09:07", U_BRK246)], prefix="Video")
    c2.place(cv, ix, c1.bottom + 24)

    gy = max(layers_bottom + 50, c2.bottom + 40)
    section_header(cv, 0, gy, "Traps worth a call-out", size=26, w=W)
    gy += 56
    nw = (W - 3 * 40) / 4
    notes = [
        Note(nw, "Agentic retrieval ignores scoringProfile and scoringParameters, and uses the knowledge source's semantic "
                 "configuration. For recency bias use freshness-aware retrieval (preview).", kind="info",
             title="Scoring profiles do not apply", size=14, title_size=16, pad=10, src=[L_RETRIEVE]),
        Note(nw, "The reference id is a citation key for this response, not the index document key. Use docKey (or the preview "
                 "citationUrl) to find the document, and activitySource to find the query that produced it.", kind="warn",
             title="reference id is not the doc key", size=14, title_size=16, pad=10, src=[L_RETRIEVE]),
        Note(nw, "A document larger than the output budget can be left out of the response, and the activity array warns when "
                 "the most relevant document exceeds it. Raise maxOutputSizeInTokens to keep more content.", kind="gotcha",
             title="Output budget can drop the best document", size=14, title_size=16, pad=10, src=[L_RETRIEVE]),
        Note(nw, "Migrating to 2026-04-01 means dropping outputMode, answerInstructions, retrievalInstructions, "
                 "retrievalReasoningEffort and alwaysQuerySource, and sending intents instead of messages.", kind="warn",
             title="Going back to GA removes properties", size=14, title_size=16, pad=10, src=[L_MIGRATE]),
    ]
    right, bottom = row(cv, 0, gy, notes, gap=40)
    return bottom


def section_sources(cv: Canvas, y: float) -> float:
    items = [L_OVERVIEW, L_EFFORT, L_KS, L_RETRIEVE, L_SYNTH, L_LIMITS, L_MIGRATE, L_IQ, L_IQ_CONNECT, L_DELEG,
             ("(video) BRK246: Foundry IQ (Build 2026), v=FRptM_WiBRg", U_BRK246),
             ("(video) Deep Dive into Foundry IQ (John Savill), v=uDVkcZwB0EU", U_SAVILL)]
    r = sources(cv, 0, y, items, w=W, cols=4)
    return r.y + r.h
