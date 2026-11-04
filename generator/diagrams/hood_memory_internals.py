"""Foundry Memory internals (preview) - under the hood: debounced write path, scoped managed store, static and contextual retrieval.

Evidence convention used on this canvas (keep it honest):
  solid border + hatch  = documented on Microsoft Learn
  dashed border + soft  = only a video / blog says it (labelled "(video/blog)")
  dotted grey + "?"     = not documented anywhere checked (inferences are written as such inside these boxes)
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-memory-internals",
    title="Foundry Memory internals (preview)",
    section="8", order=9,
    description="Under the hood of Foundry Memory (preview): the debounced write path (extract, consolidate), the scoped managed store, "
                "static and contextual retrieval, scopes and quotas, no VNet support and how prompt and hosted agents use it - with "
                "documented, video/blog-only and not-documented facts drawn differently.",
    tags=["memory", "memory store", "scope", "consolidation", "retrieval", "preview"],
)

W = 3250
GREY = "#868e96"
AMBER = "#f08c00"
INK_GRAY = "#495057"

# --------------------------------------------------------------------------- sources
L_WHAT = learn("agents/concepts/what-is-memory")
L_USAGE = learn("agents/how-to/memory-usage")
L_QSHOST = learn("agents/quickstarts/quickstart-memory-hosted-agent")
L_RUNTIME = learn("agents/concepts/runtime-components")
L_TRACE = learn("observability/concepts/trace-agent-concept")
L_LIMITS = learn("agents/concepts/limits-quotas-regions")
L_IQ = learn("agents/concepts/what-is-foundry-iq")
L_FILE = learn("agents/how-to/tools/file-search")
L_CS = learn("ai-services/content-safety/concepts/jailbreak-detection", base="azure")
U_BLOG1 = "https://devblogs.microsoft.com/foundry/introducing-memory-in-foundry-agent-service/"
U_BLOG2 = "https://devblogs.microsoft.com/foundry/memory-build2026/"
U_VID = "https://www.youtube.com/watch?v=DZn9bNDEs4U"
U_BRK241 = "https://www.youtube.com/watch?v=_8UKz197JuM"
U_BRK252 = "https://www.youtube.com/watch?v=a7FELS8hQAE"
U_STATE = "https://github.com/microsoft/STATE-Bench"

S_WHAT = ("Memory in Foundry Agent Service (preview)", L_WHAT)
S_USAGE = ("Create and use memory in Foundry Agent Service", L_USAGE)
S_QSHOST = ("Quickstart: give a hosted agent persistent memory", L_QSHOST)
S_RUNTIME = ("Build with agents, conversations and responses", L_RUNTIME)
S_TRACE = ("Agent tracing overview", L_TRACE)
S_LIMITS = ("Agent Service limits, quotas and regions", L_LIMITS)


# =========================================================================== evidence-styled blocks
def _retag(card: Card, prefix) -> Card:
    """Card.src lines always read 'Learn: ...'; relabel them for video / blog evidence (one prefix, or one per line)."""
    prefixes = [prefix] * len(card.src_lines) if isinstance(prefix, str) else list(prefix)
    card.src_lines = [(t.replace("Learn: ", f"{p}: ", 1), u, y) for (t, u, y), p in zip(card.src_lines, prefixes)]
    return card


def doc(w, title, body, *, theme="teal", src=(), **kw) -> Card:
    """Documented on Learn: solid border, hatch fill."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    return Card(w, title, body, theme=theme, src=src, **kw)


def vb(w, title, body, *, theme="yellow", src=(), prefix="Blog", **kw) -> Card:
    """Video / blog only: dashed border, soft fill, '(video/blog)' in the title."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    c = Card(w, "(video/blog) " + title, body, theme=theme, dash="dashed", fill="soft", src=src, **kw)
    return _retag(c, prefix)


def nd(w, title, body, **kw) -> Card:
    """Not documented: dotted grey, no fill, '?' in the title."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("title_color", GREY)
    return Card(w, "? " + title, body, theme="gray", dash="dotted", fill="none", body_color=MUTED, **kw)


def vb_box(w, label, sub, *, h=None, size=17, sub_size=14) -> Box:
    return Box(w, "(video/blog) " + label, sub=sub, theme="yellow", dash="dashed", fill="soft", size=size, sub_size=sub_size, h=h)


def nd_box(w, label, sub="not documented", *, h=None, size=17, sub_size=14) -> Box:
    return Box(w, "? " + label, sub=sub, theme="gray", dash="dotted", fill="none", size=size, sub_size=sub_size, h=h, color=GREY)


def tile(cv: Canvas, x, y, w, h, big, caption, theme, kind="doc") -> None:
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


def evidence_key(cv: Canvas, right: float, y: float) -> None:
    """Legend for the three evidence styles (solid / dashed / dotted grey), right aligned."""
    specs = [("solid", INK_GRAY, "Documented on Learn", ""),
             ("dashed", INK_GRAY, "Video or blog only (video/blog)", ""),
             ("dotted", GREY, "Not documented", "?")]
    widths = [64 + 14 + text_size(s[2], 15)[0] for s in specs]
    total = sum(widths) + 36 * (len(specs) - 1)
    x = right - total
    cv.text(x, y, "Evidence key", size=15, color=MUTED)
    cx, cy = x, y + 26
    for (dash, stroke, label, mark), w in zip(specs, widths):
        cv.rect(cx, cy, 64, 32, stroke=stroke, fill="#f1f3f5", style="solid", sw=2, dash=dash)
        if mark:
            mw, mh = text_size(mark, 20)
            cv.text(cx + (64 - mw) / 2, cy + (32 - mh) / 2, mark, size=20, color=GREY)
        cv.text(cx + 78, cy + 5, label, size=15, color=INK)
        cx += w + 36


def banner(cv: Canvas, y: float, letter, title: str, sub: str, theme: str = "teal") -> float:
    """Section banner with a lettered marker; returns the y where content can start."""
    numbered(cv, 24, y + 30, letter, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 62, y, title, sub, size=34, sub_size=17, w=W - 62)
    return bottom + 26


# =========================================================================== summary strip
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        ("3", "memory types: user profile, chat summary and procedural", "teal", "doc"),
        ("2 models", "a chat and an embedding deployment 'process your memory content'", "blue", "doc"),
        ("100 / 10,000", "maximum scopes per store / memories per scope", "yellow", "doc"),
        ("1,000 / min", "search requests, and separately update requests, per minute", "yellow", "doc"),
        ("No VNet", "VNet integration isn't supported for memory stores", "red", "doc"),
        ("19", "regions (as of 2026-11-03); the feature is in preview", "teal", "doc"),
        ("~5%", "vendor claim: procedural memory gain on STATE-Bench and Tau-Bench, unverified", "yellow", "vb"),
        ("?", "storage engine, index, encryption and BYO storage are not documented", "gray", "nd"),
    ]
    gap = 30
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    x = 0
    for big, cap, th, kind in tiles:
        tile(cv, x, y, tw, 132, big, cap, th, kind)
        x += tw + gap
    return y + 132


# =========================================================================== hero: lifecycle
BW, BG, LP = 430, 80, 24                 # lane box width, gap between boxes, lane panel padding
OX = 62                                  # lanes are indented so the loop arrow can run down the left margin
LW = 2 * LP + 4 * BW + 3 * BG            # lane panel width
SX = OX + LW + 100                       # store panel x
SW = W - SX                              # store panel width


LH = 136                                 # lane box height


def lane_box(label, sub, theme, icon, *, h=LH, size=20) -> Box:
    return Box(BW, label, sub=sub, theme=theme, icon=icon, icon_pos="left", icon_size=38, size=size, sub_size=15, h=h,
               fill="hatch")


def drawer(cv: Canvas, x, y, w, h, label) -> None:
    """One scope: an isolated drawer with three shelves (the memory types) and items as dots."""
    th = THEMES["teal"]
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        cv.text(x + 16, y + 10, label, size=19, color=th.deep)
        sy = y + 52
        shelf_h = (h - 52 - 14 - 2 * 10) / 3
        for name in ("User profile", "Chat summary", "Procedural"):
            cv.rect(x + 14, sy, w - 28, shelf_h, stroke=th.stroke, fill="#ffffff", style="solid", sw=1.5)
            cv.text(x + 26, sy + (shelf_h - 20) / 2, name, size=16, color=INK)
            for k in range(4):
                cv.ellipse(x + w - 36 - k * 24, sy + shelf_h / 2 - 8, 16, 16, stroke=th.stroke,
                           fill=th.fill if k < 3 else "transparent", style="solid", sw=1.5, rough=0,
                           dash="solid" if k < 3 else "dotted")
            sy += shelf_h + 10
    cv.register("drawer", x, y, w, h)


def band_hero(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "1", "The life of a memory: write path on top, read path below, the store on the right",
                "Numbers 1-5 follow a write; A and B are the two ways to read; F is the fast lane. Solid = Learn, dashed = video/blog only, dotted grey = not documented")
    # ------------------------------------------------------------------ write lane
    with cv.panel(OX, y0, title="Write path: the back office",
                  sub="Runs after the answer has been sent: a debounce clock, then two LLM jobs, then the store",
                  theme="gray", style="solid", fill="soft", pad=LP, title_size=26, sub_size=15, w=LW) as wp:
        ry = wp.iy
        w1 = lane_box("Agent responds", "Short-term context stays in the session. With the memory search tool the service calls update_memories after every response",
                      "green", "agent")
        w2 = lane_box("Debounce: update_delay", "Completes only after a period of inactivity; update_delay=0 on the update API processes at once",
                      "teal", "scheduler")
        w3 = lane_box("Extract (LLM)", "Pulls preferences, facts, context and summaries of recent activity out of the conversation",
                      "teal", "gpt")
        w4 = lane_box("Consolidate (LLM)", "Merges similar or duplicate topics, resolves conflicting facts, resets the last-updated time",
                      "teal", "gpt")
        wb = [w1, w2, w3, w4]
        for i, b in enumerate(wb):
            b.place(cv, wp.ix + i * (BW + BG), ry)
            numbered(cv, b.x + 18, b.y + 4, i + 1, theme=b.th.name, d=34, size=20)
        for a, b in zip(wb, wb[1:]):
            connect(cv, a, b, a_side="right", b_side="left", sw=3)
        r2 = ry + w1.h + 50
        n2 = nd_box(BW, "New turn restarts the timer?", "Learn says 'a period of inactivity'; a restart is our inference", h=88)
        n2.place(cv, w2.x, r2)
        v3 = vb_box(BW, "Procedural memory", "Trajectories are ingested and audited into 'when to use' and 'what to do' items", h=88)
        v3.place(cv, w3.x, r2)
        n4 = nd_box(BW, "Consolidation algorithm", "Prompts, model and merge rules are not described", h=88)
        n4.place(cv, w4.x, r2)
        connect(cv, v3, w3, a_side="top", b_side="bottom", dash="dashed", color=AMBER, sw=2)
        connect(cv, n2, w2, a_side="top", b_side="bottom", dash="dotted", color=GREY, sw=2, end_head=None)
        connect(cv, n4, w4, a_side="top", b_side="bottom", dash="dotted", color=GREY, sw=2, end_head=None)
    # ------------------------------------------------------------------ read lane
    with cv.panel(OX, wp.bottom + 44, title="Read path: the front desk",
                  sub="Static memories at the start of a conversation, contextual memories on every turn, both injected into the prompt",
                  theme="gray", style="solid", fill="soft", pad=LP, title_size=26, sub_size=15, w=LW) as rp:
        ry = rp.iy
        col4, col3, col2 = rp.ix + 3 * (BW + BG), rp.ix + 2 * (BW + BG), rp.ix + (BW + BG)
        ra = lane_box("Static fetch at conversation start",
                      "search_memories(scope) with no items returns the user-profile memories", "teal", "search")
        rb = lane_box("Contextual search on every turn",
                      "search_memories(scope, items = latest messages): the profile and chat-summary memories most relevant; max_memories caps the count",
                      "teal", "search")
        ra.place(cv, col4, ry)
        rb.place(cv, col4, ry + ra.h + 28)
        mid = ry + (ra.h + 28 + rb.h - LH) / 2
        rc = lane_box("Inject into the model prompt", "Static memories become persistent context; contextual hits inform each response",
                      "blue", "openai")
        rd = lane_box("Model answers", "A personalised reply; memory operations appear as child spans in the trace tree", "green", "agent")
        rc.place(cv, col3, mid)
        rd.place(cv, col2, mid)
        numbered(cv, ra.x + 18, ra.y + 4, "A", theme="teal", d=34, size=20)
        numbered(cv, rb.x + 18, rb.y + 4, "B", theme="teal", d=34, size=20)
        connect(cv, ra, rc, a_side="left", b_side="right", route="elbow", sw=3)
        connect(cv, rb, rc, a_side="left", b_side="right", route="elbow", sw=3)
        connect(cv, rc, rd, a_side="left", b_side="right", sw=3)
        # loop back to the next write, down the left margin (outside the panels, so it crosses no text)
        lx = OX / 2
        arrow(cv, [(rd.x - 6, rd.cy), (lx, rd.cy), (lx, w1.cy), (w1.x - 6, w1.cy)], sw=3, dash="dashed", end_head="arrow")
        cv.text(rp.ix + 40, rd.cy + 12, "the agent now knows you:\nnext turn or next session", size=15, color=INK_GRAY)
        why = Note(BW, "User-profile memories often can't be found by similarity to a message, so Learn has you inject them at the start and search by context on each turn.",
                   kind="tip", title="Why two read modes?", size=14, title_size=16, src=[S_USAGE])
        why.place(cv, rp.ix, ry)
    # ------------------------------------------------------------------ fast lane
    with cv.panel(OX, rp.bottom + 44, title="Fast lane: direct remember or forget",
                  sub="Latest preview: the memory search tool applies the change immediately",
                  theme="gray", style="solid", fill="soft", pad=LP, title_size=26, sub_size=15, w=LW) as fp:
        ry = fp.iy
        f1 = lane_box("User asks to remember or forget", "For example 'remember my seat is aisle' or 'forget ...'", "gray", "user")
        f2 = lane_box("Memory search tool applies it now", "Applied immediately; no additional tool configuration is required", "teal", "iq")
        f3 = lane_box("Memory command items returned", "Listed in the response output (memory_command_call); the item is still subject to TTL",
                      "teal", "api")
        for i, b in enumerate((f1, f2, f3)):
            b.place(cv, fp.ix + (i + 1) * (BW + BG), ry)
        connect(cv, f1, f2, a_side="right", b_side="left", sw=3)
        connect(cv, f2, f3, a_side="right", b_side="left", sw=3)
        numbered(cv, f1.x + 18, f1.y + 4, "F", theme="gray", d=34, size=20)
        fn = Note(BW, "Direct remember commands do not override the store's TTL: the item can still expire.", kind="warn",
                  title="TTL still applies", size=15)
        fn.place(cv, fp.ix, ry)
    # ------------------------------------------------------------------ the store
    H = fp.bottom - y0
    with cv.panel(SX, y0, title="Memory store", sub="'items in a managed memory store', partitioned by scope",
                  theme="teal", style="solid", fill="soft", pad=24, title_size=30, sub_size=16, w=SW, h=H) as sp:
        ix, iw = sp.ix, SW - 48
        yy = sp.iy
        cv.text(ix, yy, "Created with (Learn)", size=15, color=MUTED)
        ChipFlow([Chip("chat model deployment", theme="blue", size=15), Chip("embedding model deployment", theme="blue", size=15),
                  Chip("options: user profile, chat summary, procedural, TTL", theme="teal", size=15)],
                 iw, gap=10).place(cv, ix, yy + 24)
        yy += 78
        cv.text(ix, yy, "Scopes: each one is an isolated collection of memory items", size=15, color=MUTED)
        yy += 26
        dw = (iw - 2 * 22) / 3
        dh = 300
        for i, lab in enumerate(("scope: user_123", "scope: {tid}_{oid}", "scope: any stable ID")):
            drawer(cv, ix + i * (dw + 22), yy, dw, dh, lab)
        yy += dh + 6
        cv.text(ix, yy, "Each dot is one memory item; a dotted dot has expired by TTL (illustration)", size=13, color=MUTED)
        yy += 30
        ChipFlow([Chip("max 100 scopes per store", theme="yellow", size=15), Chip("max 10,000 memories per scope", theme="yellow", size=15),
                  Chip("default_ttl_seconds: 0 = never expires", theme="yellow", size=15)], iw, gap=10).place(cv, ix, yy)
        yy += 48
        ChipFlow([Chip("item CRUD", theme="teal", size=15), Chip("delete by scope", theme="teal", size=15),
                  Chip("delete store", theme="teal", size=15),
                  Chip("(video/blog) portal memory UI", theme="yellow", size=15, dash="dashed", fill="soft")], iw, gap=10).place(cv, ix, yy)
        yy += 56
        nv = Box(iw, "No VNet integration for memory stores", sub="Documented limitation of the preview", theme="red", icon="vnet",
                 icon_pos="left", icon_size=36, size=19, sub_size=14, h=84, fill="hatch")
        nv.place(cv, ix, yy)
        yy += 84 + 16
        cv.text(ix, yy, "Not documented anywhere I could find:", size=15, color=MUTED)
        yy += 28
        rem = sp.y + H - 24 - yy
        bh = (rem - 14) / 2
        nw = (iw - 14) / 2
        grid_boxes = [("Backing storage engine", "Learn says only 'a managed memory store'"),
                      ("Index behind search", "the hosted quickstart mentions 'indexing'; nothing describes the index"),
                      ("Encryption at rest and CMK", "not covered on the memory pages"),
                      ("Raw conversation text", "whether it is kept after extraction is not documented")]
        for k, (lab, sub) in enumerate(grid_boxes):
            nd_box(nw, lab, sub, h=bh, size=19, sub_size=15).place(cv, ix + (k % 2) * (nw + 14), yy + (k // 2) * (bh + 14))
    # ------------------------------------------------------------------ arrows to and from the store
    draw_badge(cv, SX + 24 + text_size("Memory store", 30)[0] + 20, y0 + 22, "preview")
    connect(cv, w4, sp, a_side="right", b_side="left", ta=0.5, tb=(w4.cy - sp.y) / sp.h, sw=3, num=5, num_theme="teal")
    connect(cv, sp, ra, a_side="left", b_side="right", ta=(ra.cy - sp.y) / sp.h, tb=0.5, sw=3, num="A", num_theme="teal")
    connect(cv, sp, rb, a_side="left", b_side="right", ta=(rb.cy - sp.y) / sp.h, tb=0.5, sw=3, num="B", num_theme="teal")
    connect(cv, f3, sp, a_side="right", b_side="left", ta=0.5, tb=(f3.cy - sp.y) / sp.h, sw=3, num="F", num_theme="gray")
    return sp.bottom


# =========================================================================== 2: four phases x three evidence levels
C4, G4 = 775, 50


def row_label(cv: Canvas, x: float, y: float, kind: str, title: str, sub: str) -> float:
    """Evidence-row heading: a swatch in the row's border style plus what the style means."""
    if kind == "doc":
        cv.rect(x, y + 2, 64, 34, stroke="#099268", fill="#96f2d7", style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y + 2, 64, 34, stroke=AMBER, fill="#fff9db", style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y + 2, 64, 34, stroke=GREY, fill="transparent", sw=2, dash="dotted")
        cv.text(x + 24, y + 5, "?", size=26, color=GREY)
    t = cv.text(x + 82, y, title, size=26, color=INK)
    cv.text(x + 82 + t.w + 20, y + 8, sub, size=17, color=MUTED)
    return y + 54


def nd_paras(*items) -> list:
    return [("para", i) for i in items]


def band_matrix(cv: Canvas, y: float) -> float:
    y = banner(cv, y, "2", "Four phases, three levels of evidence",
               "Each column is one phase of the lifecycle; each row says how well that phase is documented. Read down a column to see where the knowledge ends")
    heads = [("Extraction", "what is pulled out of a conversation, and when", "gpt"),
             ("Consolidation", "how new facts meet the ones already stored", "gpt"),
             ("Storage", "where items live and what bounds them", "storage"),
             ("Retrieval", "how memories come back into a prompt", "search")]
    hb = []
    for i, (t, s, ic) in enumerate(heads):
        b = Box(C4, t, sub=s, theme="teal", icon=ic, icon_pos="left", icon_size=40, size=26, sub_size=16, h=100, fill="solid")
        b.place(cv, i * (C4 + G4), y)
        numbered(cv, b.x + 18, b.y + 4, i + 1, theme="teal", d=34, size=20)
        hb.append(b)
    for a, b in zip(hb, hb[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3)
    y += 100 + 46

    # ---------------------------------------------------------------- row 1: documented on Learn
    y = row_label(cv, 0, y, "doc", "Documented on Learn", "solid border, hatch fill (as of 2026-11-03)")
    d_ext = doc(C4, "Extraction: what Learn says", [
        "The system actively extracts key information from the conversation: user preferences, facts and relevant context (for example 'allergic to dairy') and summaries of recent activities",
        "Memory search tool: after each agent response the service internally calls update_memories; the write is debounced by update_delay",
        "Memory Store APIs: begin_update_memories(items) is a long-running operation of about one minute; chain updates with previous_update_id; update_delay=0 starts at once",
        "The system 'preprocesses and postprocesses' the data, including extraction and consolidation; the stages are not described",
        "You name a chat and an embedding deployment at store creation: they 'process your memory content'",
        "user_profile_details steers what to extract, summarize and commit, and what to leave out (age, financials, precise location, credentials)",
        "An update returns memory_operations[]: each has a kind and a memory_item (memory_id, content)",
    ], src=[S_WHAT, S_USAGE])
    d_con = doc(C4, "Consolidation: what Learn says", [
        "Extracted memories are consolidated 'to keep the memory store efficient and relevant'",
        "The system uses LLMs to merge similar or duplicate topics, so the agent does not store redundant information",
        "Conflicting facts, such as a new allergy, are resolved to keep memory accurate",
        "Logic is applied 'where applicable', for example to merge duplicate or overlapping user-profile information",
        "Behaviour 'can vary by memory type and might change during the preview'",
        "Updating and consolidating an item resets its last-updated time (Learn states this in the TTL section)",
        "Three types, all 'enabled by default' in the types table; in the latest preview, enabling procedural memory and a default TTL are set at store creation",
    ], src=[S_WHAT, S_USAGE])
    d_sto = doc(C4, "Storage: what Learn says", [
        "'memories are stored as items in a managed memory store'",
        "scope partitions the store: each scope keeps an isolated collection of memory items",
        "Documented maximums: 100 scopes per store and 10,000 memories per scope (as of 2026-11-03)",
        "default_ttl_seconds sets store-level retention (0 = no expiry) for memories from commands, extraction or item CRUD",
        "Item-level create, get, list, update and delete; delete by scope; delete the whole store",
        "Hosted quickstart: the store 'finishes indexing' a new memory, so wait a few seconds before you query",
        "VNet integration isn't supported for memory stores; available in 19 regions",
        "No separate meter: you pay for the chat and embedding models you configure (can change during preview)",
    ], src=[S_WHAT, S_USAGE, S_QSHOST])
    d_ret = doc(C4, "Retrieval: what Learn says", [
        "Searches the memory store for the most relevant memories; retrieve stable user-profile information early in the conversation",
        "Why two modes: 'Often, you can't retrieve user profile memories based on semantic similarity to a user's message'",
        "Static: search_memories with a scope but no items and no previous_search_id returns user-profile memories",
        "Contextual: items = the latest messages returns the user-profile and chat-summary memories most relevant to them",
        "options.max_memories limits the result count",
        "Memory search tool: static memories are injected at conversation start, contextual ones are retrieved per turn",
        "Tool output uses a memories collection instead of the legacy results field",
        "Needs an embedding deployment; search is limited to 1,000 requests per minute",
    ], src=[S_WHAT, S_USAGE])
    _, b1 = row(cv, 0, y, [d_ext, d_con, d_sto, d_ret], gap=G4)

    # ---------------------------------------------------------------- row 2: video or blog only
    y = row_label(cv, 0, b1 + 56, "vb", "Video or blog only", "dashed border, soft fill, tagged (video/blog): claims, not specifications")
    SB1 = ("Introducing Memory in Foundry Agent Service, 2025-11-25", U_BLOG1)
    SB2 = ("Making agent memory more reliable, transparent, and production-ready, 2026-06-03", U_BLOG2)
    SV = ("Using Microsoft Agent Framework with Foundry managed memory, 2026-04-16", U_VID)
    SK = ("From prototype to production (BRK241), procedural memory at 0:39:39", U_BRK241)
    v_ext = vb(C4, "Steering, procedural extraction, debounce cost", [
        "Blog 2025-11-25: user_profile_details is 'translated into instructions for the underlying model, shaping how memory extraction, consolidation, and retrieval are performed'",
        "Blog 2026-06-03: procedural memory ingests agent trajectories and audits them for successful patterns, inefficient routes and missing steps",
        "Output: structured items with 'when to use' (task context, preconditions, signals) and 'what to do' (ordered actions, required checks, tool usage)",
        "Blog 2026-06-03 also announces multimodal memory (images); the Learn pages read here do not cover it",
        "Video 0:17:55-0:18:21: repeated writes cost more and early statements may be superseded; 'a lot of the long-term memory really happens after the current session stopped'",
        "BRK241 at 0:39:39 announces procedural memory in public preview",
    ], src=[SB1, SB2, SV, SK], prefix=["Blog", "Blog", "Video", "Video"])
    v_con = vb(C4, "The conflict-resolution example", [
        "Video 0:11:13-0:11:41: a 'dairy' allergy the user later qualifies ('cooking for my kids'); 'the memory has a consolidation layer that detects this conflict and automatically evolves what is inside the memory store'",
        "Video 0:02:55-0:03:18: memory is a tool the agent calls to extract and consolidate, and to fetch at inference time",
        "Video 0:12:39: TTL is described for facts that decay",
        "The video is concept-level: it does not open up the consolidation algorithm or any storage internals",
    ], src=[SV], prefix="Video")
    v_sto = vb(C4, "Portal UI, shared scopes, scale claim, roadmap", [
        "Blog 2026-06-03: a portal memory-management UI to view stores and work with individual items",
        "Video 0:07:31-0:09:21: 'memory scope as a data container': several agents can share a store and scope, or one agent can use several stores",
        "Blog 2025-11-25: memory 'scales to millions of users and memories' - the documented quota is 100 scopes per store (see section 3)",
        "Roadmap statements, not commitments: bring-your-own storage 'in the future' (blog 2025-11-25); governance and lineage, 'which agent changed that data' (video 0:14:33-0:16:14)",
        "Blog 2026-06-03: file-based (markdown) memory in Microsoft Agent Framework as a local-first path",
    ], src=[SB1, SB2, SV], prefix=["Blog", "Blog", "Video"])
    v_ret = vb(C4, "Hybrid search, early retrieval, procedural retrieval", [
        "Blog 2025-11-25: retrieval 'uses hybrid search techniques'",
        "Blog 2025-11-25: core memories (allergies, favourite products, recurring requests) are retrieved at the beginning of a conversation",
        "Blog 2026-06-03: for similar tasks, relevant procedures are retrieved and injected into the agent's context as step-level constraints (validations, tool parameters, policy)",
        "Vendor claim, unverified: about 5% improvement on STATE-Bench and Tau-Bench with procedural memory enabled (pass^5 metric)",
    ], src=[SB1, SB2, ("STATE-Bench (open-source benchmark)", U_STATE)], prefix=["Blog", "Blog", "Repo"])
    _, b2 = row(cv, 0, y, [v_ext, v_con, v_sto, v_ret], gap=G4)

    # ---------------------------------------------------------------- row 3: not documented
    y = row_label(cv, 0, b2 + 56, "nd", "Not documented", "dotted grey, tagged with ?: nobody has published it (inferences are labelled as ours)")
    n_ext = nd(C4, "Extraction internals", nd_paras(
        "Extraction prompts, and which model call does which job.",
        "Whether a new turn restarts the debounce timer: Learn says only 'a period of inactivity'; a restart is our inference.",
        "Which identity calls the chat and embedding deployments: Learn states the role requirement (Foundry User for the project managed identity), not the hop; the project identity is our inference."),
        gap=9)
    n_con = nd(C4, "Consolidation internals", nd_paras(
        "The consolidation algorithm, its prompts and the model it uses.",
        "How a conflict is settled when two facts disagree.",
        "What 'can vary by memory type' means in practice."), gap=9)
    n_sto = nd(C4, "Storage internals", nd_paras(
        "The backing store and index engine.",
        "Encryption at rest and customer-managed keys: not covered on the two memory pages.",
        "Bring-your-own storage and a write lineage or audit trail: roadmap statements only.",
        "Whether raw conversation text is kept after extraction.",
        "Why VNet integration is not supported."), gap=9)
    n_ret = nd(C4, "Retrieval internals", nd_paras(
        "What 'hybrid search' means: vector plus keyword, a re-ranker?",
        "How the top max_memories are ranked and chosen.",
        "The index behind it: Learn implies semantic similarity for contextual search and requires an embedding deployment, but does not describe the index."),
        gap=9)
    _, b3 = row(cv, 0, y, [n_ext, n_con, n_sto, n_ret], gap=G4)
    return b3


# =========================================================================== 3: scope
def band_scopes(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "3", "Scope: the partition key you own, and the scale conflict it exposes",
                "The scope is how memory is isolated: one collection of items per scope. How it gets resolved depends on which API path you use")
    # ---------------------------------------------------------------- left: resolution flow
    root = Box(250, "A call needs a scope", sub="two API paths", theme="gray", size=20, sub_size=15, h=110, fill="hatch")
    root.place(cv, 0, y0 + 190)
    top = Box(380, "Memory search tool", sub="scope: {{$userId}} in the tool definition", theme="teal", icon="iq", icon_pos="left",
              icon_size=36, size=20, sub_size=15, h=120, fill="hatch")
    top.place(cv, 320, y0 + 60)
    bot = Box(380, "Low-level Memory Store APIs", sub="update, search, item CRUD, delete scope", theme="teal", icon="api",
              icon_pos="left", icon_size=36, size=20, sub_size=15, h=120, fill="hatch")
    bot.place(cv, 320, y0 + 420)
    dia = Box(360, "x-memory-user-id header present?", shape="diamond", theme="yellow", size=18, h=240, fill="hatch")
    dia.place(cv, 780, y0)
    yes = Box(380, "scope = the header value", sub="proxy or backend pattern: your service calls on behalf of an end user",
              theme="teal", size=19, sub_size=14, h=120, fill="hatch")
    yes.place(cv, 1260, y0)
    no = Box(380, "scope = {tid}_{oid}", sub="frontend pattern: the caller's Entra token (tenant ID and object ID)",
             theme="teal", size=19, sub_size=14, h=120, fill="hatch")
    no.place(cv, 1260, y0 + 140)
    stat = Box(360, "scope = a static value", sub="when you do not need per-user isolation", theme="teal", size=19, sub_size=14, h=100,
               fill="hatch")
    stat.place(cv, 780, y0 + 290)
    low = Box(860, "scope must be passed explicitly on every call",
              sub="a UUID or another stable identifier from your system; automatic identity extraction is not supported", theme="teal",
              size=19, sub_size=14, h=120, fill="hatch")
    low.place(cv, 780, y0 + 420)
    connect(cv, root, top, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, root, bot, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, top, dia, a_side="right", b_side="left", sw=3)
    connect(cv, top, stat, a_side="bottom", b_side="left", route="elbow", sw=3)
    connect(cv, bot, low, a_side="right", b_side="left", sw=3)
    for leaf, lab in ((yes, "yes"), (no, "no")):
        arrow(cv, [(dia.right + 4, dia.cy), (dia.right + 56, dia.cy), (dia.right + 56, leaf.cy), (leaf.x - 6, leaf.cy)], sw=3,
              end_head="arrow")
        cv.text(dia.right + 70, leaf.cy - 32, lab, size=17, color=INK)
    cv.text(0, y0 + 372, "Same rule for both paths: write\nand read must use the same\nscope, otherwise search returns\nno results.",
            size=15, color=INK)
    # ---------------------------------------------------------------- right: conflict, rules, claims
    rx, rw = 1700, W - 1700
    n = Note(rw, "Learn lists a maximum of 100 scopes per memory store and 10,000 memories per scope. The 2025-11-25 launch blog (video/blog) says memory "
                 "'scales to millions of users and memories'. The two statements do not line up in the preview: treat the quota page as the contract "
                 "(as of 2026-11-03) and the blog line as marketing.", kind="warn", title="Docs disagree: how many users fit in one store?",
             size=16, src=[S_WHAT])
    n.place(cv, rx, y0)
    cw2 = (rw - 50) / 2
    r1 = doc(cw2, "Scope rules from Learn", [
        "Each scope keeps an isolated collection of memory items, for example one per customer",
        "Do not share a scope across users; if you must, use user_profile_details to tell memory not to store personal information",
        "Tool path: {{$userId}} resolves per response call, from the header if present, else from the Entra token",
        "Low-level APIs: scope on every call; no automatic resolution",
        "Learn recommends one dedicated memory store per agent, for clear boundaries of access and optimization",
    ], src=[S_USAGE], title_size=19)
    r2 = nd(cw2, "What Learn does not say about scale", nd_paras(
        "What happens when a store needs a 101st scope.",
        "Whether 100 scopes per store is a preview limit that will rise.",
        "If scope = end user, 100 is tiny: plan several stores or a coarser scope. That is our inference, not guidance from Learn."),
        gap=9)
    r3 = vb(rw, "Scope as a data container", [
        "Video 0:07:31-0:09:21: 'memory scope as a data container': several agents can share a store and scope, or one agent can talk to several stores",
        "Blog 2025-11-25: memory 'scales to millions of users and memories' (see the note above)",
    ], src=[("Using Microsoft Agent Framework with Foundry managed memory, 2026-04-16", U_VID),
            ("Introducing Memory in Foundry Agent Service, 2025-11-25", U_BLOG1)], prefix=["Video", "Blog"])
    ry = n.bottom + 30
    _, rb_ = row(cv, rx, ry, [r1, r2], gap=50)
    r3.place(cv, rx, rb_ + 30)
    return max(r3.bottom, low.bottom)


# =========================================================================== 4: how agents use it
def code_block(cv: Canvas, x: float, y: float, w: float, title: str, lines: list, *, size=14) -> float:
    """Small monospaced snippet panel (text copied from Learn samples); returns its height."""
    lh = size * metrics.line_ratio(metrics.MONO)
    h = 40 + len(lines) * lh + 14
    with cv.group():
        cv.rect(x, y, w, h, stroke=INK_GRAY, fill="#f8f9fa", style="solid", sw=1.5)
        cv.text(x + 14, y + 10, title, size=13, color=MUTED)
        cv.text(x + 14, y + 36, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    cv.register("code", x, y, w, h)
    return h


def lane_chain(cv: Canvas, x: float, y: float, items) -> list:
    """Three boxes joined by arrows: (label, sub, theme, icon)."""
    out = []
    for i, (label, sub, th, icon) in enumerate(items):
        b = Box(400, label, sub=sub, theme=th, icon=icon, icon_pos="left", icon_size=36, size=19, sub_size=14, h=124, fill="hatch")
        b.place(cv, x + i * 480, y)
        out.append(b)
    for a, b in zip(out, out[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3)
    return out


def band_agents(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "4", "How agents reach memory: three ways in, one store behind them",
                "A prompt agent gets a tool; a hosted agent calls the store from its own code; anything else can use the low-level APIs")
    CHAIN_W = 3 * 400 + 2 * 80
    KW = (W - 48 - CHAIN_W - 2 * 40) / 2          # width of each of the two text cards beside the chain
    KX1 = 24 + CHAIN_W + 40
    KX2 = KX1 + KW + 40

    def lane(top, title, sub, chain, cards, below):
        """One lane: chain (+ a block under it) on the left, two text cards on the right; returns the panel."""
        with cv.panel(0, top, title=title, sub=sub, theme="gray", style="solid", fill="soft", pad=24, title_size=26, sub_size=15, w=W) as p:
            by = p.iy + 14
            lane_chain(cv, p.ix, by, chain)
            left_h = 124 + 24 + below(p.ix, by + 124 + 24)
            H = max(left_h, max(c.h for c in cards))
            for i, c in enumerate(cards):
                c.place(cv, KX1 + i * (KW + 40), by, h=H)
        draw_badge(cv, 24 + text_size(title, 26)[0] + 20, p.y + 18, "preview")
        return p

    # ---------------------------------------------------------------- lane 1: prompt agent
    def below1(x, yy):
        return code_block(cv, x, yy, CHAIN_W, "Tool definition, REST sample from Learn (a static scope; {{$userId}} resolves one per end user)", [
            '"tools": [{ "type": "memory_search_preview",',
            '            "memory_store_name": "my_memory_store",',
            '            "scope": "user_123",',
            '            "update_delay": 1 }]'])

    p1 = lane(y0, "Prompt agent: the memory search tool", "the simple path: attach one tool and the service does the work", [
        ("Prompt agent", "declarative: model, instructions and tools", "green", "agent"),
        ("memory_search_preview", "tool fields: memory_store_name, scope, update_delay", "teal", "iq"),
        ("Memory store", "one dedicated store per agent is recommended", "teal", "storage")], [
        doc(KW, "Reads: what the service injects", [
            "At the start of each conversation, static memories are injected so the agent has immediate, persistent context",
            "Contextual memories are retrieved on each turn from the latest messages",
            "Remember or forget requests are applied immediately and returned as memory command items; they do not override TTL",
        ], src=[S_WHAT, S_USAGE], title_size=19, body_size=15),
        doc(KW, "Writes, scope and identity", [
            "After each agent response the service internally calls update_memories; the actual write is debounced by update_delay",
            "scope {{$userId}} resolves per response call from the x-memory-user-id header, else from the caller's Entra token",
            "Prerequisite: the project's system-assigned managed identity with Foundry User on the Foundry resource (or key-based auth if roles are not feasible)",
        ], src=[S_USAGE], title_size=19, body_size=15)], below1)

    # ---------------------------------------------------------------- lane 2: hosted agent
    def below2(x, yy):
        c = vb(CHAIN_W, "Agent Framework wiring and file memory", [
            "Video 0:17:04-0:17:50: a Foundry memory provider is configured with name, scope and update_delay; 0 writes immediately, otherwise the provider accumulates messages before writing",
            "Blog 2026-06-03: file-based (markdown) memory in Microsoft Agent Framework is a local-first path",
        ], src=[("Using Microsoft Agent Framework with Foundry managed memory, 2026-04-16", U_VID),
                ("Making agent memory more reliable, transparent, and production-ready, 2026-06-03", U_BLOG2)],
               prefix=["Video", "Blog"])
        c.place(cv, x, yy)
        return c.h

    p2 = lane(p1.bottom + 40, "Hosted agent: a memory provider in your own code",
              "your container calls the store itself; the Learn quickstart uses FoundryMemoryProvider from the Agent Framework sample", [
        ("Hosted agent", "your container code, one Micro VM sandbox per session", "green", "container-apps"),
        ("FoundryMemoryProvider", "retrieves before each model call, updates after each turn", "teal", "iq"),
        ("Memory store", "created by an azd hook or by the SDK", "teal", "storage")], [
        doc(KW, "How it is wired", [
            "Learn's tool steps say to attach the memory search tool to a prompt agent; the hosted-agent quickstart wires memory through the provider in the agent code",
            "The store comes from an azd postprovision hook (top level of azure.yaml) or the Python or .NET SDK; MEMORY_STORE_NAME names it (hook default: agent_framework_memory)",
        ], src=[S_QSHOST, S_RUNTIME], title_size=19, body_size=15),
        doc(KW, "Roles and timing", [
            "Your identity needs Foundry User on the project scope; Cognitive Services OpenAI User on the same scope goes to your identity and to the deployed agent's runtime identity, otherwise writes fail with 401 and the store stays empty",
            "After storing a fact, wait a few seconds before you query: the store finishes indexing the memory",
        ], src=[S_QSHOST], title_size=19, body_size=15)], below2)

    # ---------------------------------------------------------------- lane 3: low-level APIs
    def below3(x, yy):
        return code_block(cv, x, yy, CHAIN_W, "Update call, Python sample from Learn (long-running: about one minute)", [
            "update_poller = project_client.beta.memory_stores.begin_update_memories(",
            "    name=memory_store_name, scope=scope,",
            "    items=[user_message], update_delay=0)",
            "update_result = update_poller.result()"])

    p3 = lane(p2.bottom + 40, "Low-level Memory Store APIs: any app or custom orchestration",
              "full control over when to write, what to search and which records to keep", [
        ("Your app or agent code", "decides when to update and when to search", "gray", "app"),
        ("project.beta.memory_stores", "update, search, item CRUD, delete scope, delete store", "teal", "sdk"),
        ("Memory store", "scope is explicit on every request", "teal", "storage")], [
        doc(KW, "Update and search", [
            "begin_update_memories(name, scope, items, previous_update_id?, update_delay?) is a long-running operation of about one minute; chain updates with previous_update_id",
            "search_memories(name, scope, items?, previous_search_id?, options.max_memories) returns static or contextual memories that you inject yourself",
        ], src=[S_USAGE], title_size=19, body_size=15),
        doc(KW, "Items, deletion and API versions", [
            "Item-level create, get, list, update and delete, plus delete by scope, support user-facing controls and data-rights requests",
            "REST: memory stores use api-version 2025-11-15-preview, while attaching the tool to an agent uses /agents?api-version=v1 (Learn calls the difference out)",
        ], src=[S_USAGE], title_size=19, body_size=15)], below3)
    return p3.bottom


# =========================================================================== 5: one item over time
def band_item_life(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "5", "One memory item over time: how it is born, kept, expired or deleted",
                "Learn: TTL applies to every memory however it was created, and updating plus consolidating an item resets its last-updated time")
    ew = 520
    e1 = Box(ew, "Write path", sub="extraction, then consolidation: merge duplicates, resolve conflicts", theme="teal", icon="gpt",
             icon_pos="left", icon_size=36, size=20, sub_size=15, h=100, fill="hatch")
    e2 = Box(ew, "Direct remember command", sub="applied immediately by the memory search tool", theme="teal", icon="iq",
             icon_pos="left", icon_size=36, size=20, sub_size=15, h=100, fill="hatch")
    e3 = Box(ew, "Item create (CRUD)", sub="you create the record yourself with the item APIs", theme="teal", icon="api",
             icon_pos="left", icon_size=36, size=20, sub_size=15, h=100, fill="hatch")
    st = doc(880, "A stored memory item", [
        "Lives in one scope and counts toward the 10,000 memories per scope",
        "User-profile items are fetched statically at conversation start; chat-summary items come back by relevance, per turn",
        "Procedural items are retrieved when the user asks for a recurring workflow the agent handled before",
        "Carries a last-updated time: if the memory is updated and consolidated, the service resets it",
        "Reachable by item get, list, update and delete, and by the memory search itself",
    ], src=[S_WHAT, S_USAGE], title_size=22, body_size=16, badge="preview")
    sx = ew + 150
    st.place(cv, sx, y0 + 120)
    gap = 28
    total = 3 * 100 + 2 * gap
    mid = st.y + st.h / 2
    for i, b in enumerate((e1, e2, e3)):
        b.place(cv, 0, mid - total / 2 + i * (100 + gap))
    cv.text(0, e1.y - 44, "Born", size=24, color=INK)
    x1 = Box(ew, "Expired", sub="the store's default TTL, set in seconds, applies to every memory; 0 means no expiration", theme="yellow", icon="scheduler",
             icon_pos="left", icon_size=36, size=22, sub_size=15, h=110, fill="hatch")
    x2 = Box(ew, "Deleted", sub="forget command, item delete, delete by scope or delete the store", theme="red", icon="storage",
             icon_pos="left", icon_size=36, size=22, sub_size=15, h=110, fill="hatch")
    xx = W - ew
    y1, y2 = st.y + 0.2 * st.h, st.y + 0.8 * st.h
    x1.place(cv, xx, y1 - 55)
    x2.place(cv, xx, y2 - 55)
    cv.text(xx, x1.y - 44, "Gone", size=24, color=INK)
    for b in (e1, e2, e3):
        connect(cv, b, st, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, st, x1, a_side="right", b_side="left", ta=0.2, tb=0.5, sw=3)
    connect(cv, st, x2, a_side="right", b_side="left", ta=0.8, tb=0.5, sw=3)
    cv.text(st.right + 40, y1 - 30, "TTL runs out", size=16, color=INK)
    cv.text(st.right + 40, y2 - 30, "explicit delete", size=16, color=INK)
    loop_x1, loop_x2 = st.x + 230, st.x + 650
    arrow(cv, [(loop_x1, st.y - 6), (loop_x1, st.y - 56), (loop_x2, st.y - 56), (loop_x2, st.y - 6)], sw=3, dash="dashed", end_head="arrow")
    cv.text(loop_x1 + 20, st.y - 92, "updated or consolidated again: last-updated resets", size=16, color=INK)
    # ---------------------------------------------------------------- TTL rules
    ty = max(e3.bottom, st.bottom, x2.bottom) + 50
    w4 = (W - 150) / 4
    n1 = Note(w4, "TTL applies to all memories, whether they come from direct memory commands, extraction and consolidation, or item-level CRUD.",
              kind="info", title="TTL covers every origin", src=[S_USAGE])
    n2 = Note(w4, "TTL applies only to memory stores created after TTL support was introduced. Updating a store changes only its description or metadata; in the latest "
                  "preview, enabling procedural memory and setting a default TTL happen at store creation (verify post-create updates in your API version).", kind="warn",
              title="Create-time defaults", src=[S_USAGE, S_WHAT])
    n3 = Note(w4, "Direct remember commands do not override TTL: an item added by a remember command can still expire.", kind="gotcha",
              title="Remember does not beat TTL", src=[S_USAGE])
    n4 = nd(w4, "How exactly is expiry computed?", nd_paras(
        "Learn ties TTL to the memory and says the last-updated time resets on update and consolidation. The precise expiry rule (for example whether it is "
        "measured from that time) is not spelled out."), gap=9, title_size=17, body_size=15, pad=12)
    _, rb4 = row(cv, 0, ty, [n1, n2, n3, n4], gap=50)
    return rb4


# =========================================================================== 6: limits, network, cost
def band_limits(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "6", "Limits, network and cost: what bounds a memory store (as of 2026-11-03)",
                "Quotas and regions change often in preview: re-check the Learn pages before you size anything")
    w3 = (W - 100) / 3
    t = Table([("Limit or fact", 330), ("Documented value", w3 - 330)], [
        ["Scopes per memory store", "100 (maximum)"],
        ["Memories per scope", "10,000 (maximum)"],
        ["Search memories", "1,000 requests per minute"],
        ["Update memories", "1,000 requests per minute"],
        ["Models", "compatible Azure OpenAI chat and embedding deployments"],
        ["Low-level update", "long-running, about one minute"],
        ["Memory-store API version", "2025-11-15-preview (agents use v1)"],
        [("Network", "red"), ("VNet integration isn't supported for memory stores", "red")],
        ["Pricing", "no separate meter: the chat and embedding models you configure are billed; can change during preview"],
    ], w=w3, theme="yellow", size=15, head_size=16, title="Quotas and facts", title_size=22, first_col_theme="yellow")
    t.place(cv, 0, y0)
    regions = ["Australia East", "Brazil South", "Canada East", "East US 2", "France Central", "Italy North", "Japan East", "Korea Central",
               "North Central US", "Norway East", "South Africa North", "South India", "Sweden Central", "Switzerland North", "UAE North",
               "UK South", "West US", "West US 2", "West US 3"]
    cx = w3 + 50
    cv.text(cx, y0, "19 regions (as of 2026-11-03)", size=22, color=THEMES["teal"].deep)
    cf = ChipFlow([Chip(r, theme="teal", size=15) for r in regions], w3, gap=8)
    cf.place(cv, cx, y0 + 40)
    cv.text(cx, y0 + 40 + cf.h + 14, "Learn: Memory in Foundry Agent Service (preview)", size=12, color=LINK, link=L_WHAT)
    bp = doc(w3, "Operating checklist (Learn best practices)", [
        "Map scope to the end user and never share a scope across users",
        "Minimize and protect sensitive data; redact what could trace back to a person",
        "Give users item-level edit and delete, and record deletions in a tamper-evident audit trail",
        "Set explicit TTL defaults that match your retention policy, and say so in your UX",
        "Track token usage and memory operations to understand cost",
    ], src=[S_USAGE], title_size=20, body_size=15)
    bp.place(cv, cx, y0 + 40 + cf.h + 14 + 20 + 24)
    # ---------------------------------------------------------------- no VNet sketch
    nx = 2 * (w3 + 50)
    with cv.panel(nx, y0, title="No VNet integration", sub="what the documented limitation means for a network-isolated project",
                  theme="red", style="solid", fill="soft", pad=22, title_size=24, sub_size=15, w=w3) as vp:
        a = Box(300, "Your private network", sub="VNet, private endpoints, delegated subnet", theme="indigo", icon="vnet",
                icon_pos="left", icon_size=34, size=18, sub_size=14, h=120, fill="hatch")
        a.place(cv, vp.ix, vp.iy + 10)
        m = Box(300, "Memory store", sub="a managed store", theme="teal", icon="storage", icon_pos="left", icon_size=34, size=18,
                sub_size=14, h=120, fill="hatch")
        m.place(cv, vp.ix + w3 - 44 - 300, vp.iy + 10)
        arrow(cv, [(a.right + 8, a.cy), (m.x - 8, m.cy)], sw=3, dash="dashed", color="#e03131", start_head=None, end_head="arrow",
              label="not supported", label_size=15, label_color="#c92a2a", label_pos="above")
        q = nd_box(w3 - 44, "How a network-isolated project reaches memory", "not documented; see the networking canvas 'Networking internals: container injection and private paths'",
                   h=104)
        q.place(cv, vp.ix, a.bottom + 28)
    return max(t.bottom, vp.bottom, bp.bottom)


# =========================================================================== 7: gotchas and telemetry
def band_gotchas(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "7", "Gotchas, risks and the trace spans you can watch",
                "Most 'memory does not work' reports come from the debounce, the scope or a create-time default")
    w3 = (W - 100) / 3
    n1 = Note(w3, "Memory and the Memory Store API are preview features under the Azure preview terms. Pricing and behaviour can change, and consolidation "
                  "'might change during the preview'. The store API version is 2025-11-15-preview while agents use v1, and the tool output moved from results to "
                  "memories. Check Learn before you rely on a detail (as of 2026-11-03).", kind="preview", title="Preview: contracts can change", src=[S_WHAT, S_USAGE])
    n2 = Note(w3, "'Memories don't appear after a conversation' is normal while an update is debounced or still processing: wait longer, or call the update API "
                  "with update_delay set to 0. The hosted quickstart adds: allow a few seconds so the store finishes indexing.", kind="info",
              title="Debounce is by design", src=[S_USAGE, S_QSHOST])
    n3 = Note(w3, "Search returns no results when the scope differs from the one used on write. Use the same stable identifier for update and search; with "
                  "{{$userId}} remember the header-or-Entra rule.", kind="gotcha", title="Scope mismatch = empty search", src=[S_USAGE])
    n4 = Note(w3, "Learn's types table lists procedural memory as 'enabled by default', yet the Learn how-to sample and the 2026-06-03 blog sample both set "
                  "procedural_memory_enabled explicitly. In the latest preview it is a create-time option: check the toggle when you create the store.",
              kind="warn", title="Docs disagree: procedural default", src=[S_WHAT, S_USAGE])
    n5 = Note(w3, "There is no memory meter: you pay for the chat and embedding models you configure, so extraction, consolidation and embeddings all show up as model "
                  "tokens. That the cost grows with update frequency is our inference; Learn advises tracking token usage and memory operations.", kind="info",
              title="Cost shows up as model tokens", src=[S_USAGE, S_WHAT])
    n6 = Note(w3, "An LLM extracts and consolidates memories, so incorrect or harmful content can be stored and steer later answers (prompt injection, memory "
                  "corruption). Learn recommends Azure AI Content Safety prompt-injection detection on all prompts entering or leaving the memory system, plus "
                  "adversarial testing.", kind="gotcha", title="Memory poisoning is a documented threat",
              src=[S_WHAT, ("Prompt injection detection (Content Safety)", L_CS)])
    _, b1 = row(cv, 0, y0, [n1, n2, n3], gap=50)
    _, b2 = row(cv, 0, b1 + 36, [n4, n5, n6], gap=50)
    # ---------------------------------------------------------------- spans + decision tip
    sy = b2 + 56
    with cv.panel(0, sy, title="Trace spans: memory operations in the trace tree",
                  sub="child spans of invoke_agent or invoke_workflow; each records 'a memory operation' (Learn does not map the names to the steps above)",
                  theme="violet", style="solid", fill="soft", pad=22, title_size=24, sub_size=15, w=2 * w3 + 50) as sp2:
        ChipFlow([Chip(n, theme="violet", size=17)
                  for n in ("create_memory", "search_memory", "update_memory", "upsert_memory", "delete_memory")], 1400, gap=12).place(cv, sp2.ix, sp2.iy)
        cv.text(sp2.ix, sp2.iy + 52, "Tracing is generally available for prompt and hosted agents; workflow and external agents are in preview.", size=15, color=INK)
        cv.text(sp2.ix, sp2.iy + 78, "Learn: Agent tracing overview", size=12, color=LINK, link=L_TRACE)
        vsp = vb(560, "Semantic conventions for memory", [
            "BRK252 at 0:32:05-0:32:21: Microsoft is contributing OpenTelemetry semantic conventions for memory",
        ], src=[("From observability to ROI for AI agents (BRK252)", U_BRK252)], prefix="Video", title_size=17, body_size=15)
        vsp.place(cv, sp2.ix + 1440, sp2.iy)
    n_guard = nd(w3, "Do guardrails cover memory reads and writes?", nd_paras(
        "The guardrail intervention-point pages do not list memory reads or writes (our inference). Treat memory as an untrusted input channel: the checks on it are yours to add."),
        gap=9)
    n_guard.place(cv, 2 * (w3 + 50), sy)
    ty = max(sp2.bottom, n_guard.bottom) + 40
    w2 = (W - 50) / 2
    tip = Note(w2, "Memory is for user-specific or agent context that is learned and persists through interactions over time. Use a Foundry IQ knowledge base to "
                   "ground the agent on curated organizational content, and the file search tool to search user-provided documents during an interaction.",
               kind="tip", title="Memory, Foundry IQ or file search?", src=[S_WHAT, ("What is Foundry IQ?", L_IQ), ("File search tool", L_FILE)])
    sib = Note(w2, "Feature-level view of memory (stores, types, scopes, short-term state vs the durable state store, privacy and doc conflicts): the canvas "
                   "'Foundry Memory (Preview): long-term memory for agents'. Sandbox and network context: 'Hosted agent runtime: how a container becomes "
                   "an agent endpoint' and 'Networking internals: container injection and private paths'.", kind="key", title="Related canvases")
    _, rb3 = row(cv, 0, ty, [tip, sib], gap=50)
    return rb3


# =========================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Foundry Memory internals",
                                "Extract, consolidate, store, retrieve - what Learn documents, what only a video or blog says, "
                                "and what nobody has published (as of 2026-11-03)", w=W)
    tx = 84 + 22 + text_size("Foundry Memory internals", 48)[0] + 24
    draw_badge(cv, tx, 14, "preview", size=18)
    evidence_key(cv, W, 6)
    y = bottom + 40
    y = band_tiles(cv, y)
    y = band_hero(cv, y + 48)
    y = band_matrix(cv, y + 50)
    y = band_scopes(cv, y + 50)
    y = band_agents(cv, y + 50)
    y = band_item_life(cv, y + 50)
    y = band_limits(cv, y + 50)
    y = band_gotchas(cv, y + 50)
    y += 44
    sources(cv, 0, y, [
        ("Memory in Foundry Agent Service (preview)", L_WHAT),
        ("Create and use memory in Foundry Agent Service", L_USAGE),
        ("Quickstart: give a hosted agent persistent memory", L_QSHOST),
        ("Build with agents, conversations and responses", L_RUNTIME),
        ("Agent tracing overview (memory spans)", L_TRACE),
        ("Agent Service limits, quotas and regions", L_LIMITS),
        ("What is Foundry IQ? (memory vs knowledge bases)", L_IQ),
        ("File search tool", L_FILE),
        ("Prompt injection detection in Azure AI Content Safety", L_CS),
        ("Introducing Memory in Foundry Agent Service (blog, 2025-11-25)", U_BLOG1),
        ("Making agent memory more reliable, transparent, and production-ready (blog, 2026-06-03)", U_BLOG2),
        ("Using Microsoft Agent Framework with Foundry managed memory (video DZn9bNDEs4U, 2026-04-16)", U_VID),
        ("From prototype to production, BRK241 (video _8UKz197JuM, procedural memory at 0:39:39)", U_BRK241),
        ("From observability to ROI for AI agents, BRK252 (video a7FELS8hQAE, memory conventions at 0:32:05)", U_BRK252),
    ], w=W, cols=4, title="Sources and further reading (Microsoft Learn, blogs and videos)")
