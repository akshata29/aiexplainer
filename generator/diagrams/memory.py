"""Foundry Memory (Preview): long-term memory for agents - what it is, memory stores and types, scopes, the extract / consolidate / retrieve
lifecycle, how prompt agents, hosted agents and LangChain use it, short-term state vs the durable state store, quotas, regions, privacy and
the doc conflicts.  Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="memory", title="Foundry Memory (Preview): long-term memory for agents", section="2", group="Agent Service", order=14,
    description="Foundry Memory (Preview): memory stores, scopes, the extract-consolidate-retrieve lifecycle, memory types, how prompt, hosted and "
                "LangChain agents use it, short-term state vs the durable state store, quotas, privacy and docs conflicts.",
    tags=["memory", "memory-store", "scope", "long-term-memory", "hosted-agents", "privacy"],
)

W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    what=("Memory in Foundry Agent Service (preview)", learn("agents/concepts/what-is-memory")),
    usage=("Create and use memory in Foundry Agent Service", learn("agents/how-to/memory-usage")),
    qshosted=("Quickstart: give a hosted agent persistent memory", learn("agents/quickstarts/quickstart-memory-hosted-agent")),
    langchain=("Use Foundry Memory with LangChain and LangGraph", learn("how-to/develop/langchain-memory")),
    runtime=("Build with agents, conversations and responses", learn("agents/concepts/runtime-components")),
    state=("Durable state store for hosted agents", learn("agents/concepts/agent-state-store")),
    azyaml=("azure.yaml reference", learn("agents/concepts/azure-yaml-reference")),
    privacy=("Data, privacy and security for Agent Service", learn("responsible-ai/agents/data-privacy-security")),
    rest=("Memory Stores REST: create memory store", learn("reference/rest/create-memory-store")),
    limits=("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    iq=("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
    filesearch=("File search tool", learn("agents/how-to/tools/file-search")),
    safety=("Prompt injection detection (Azure AI Content Safety)", learn("ai-services/content-safety/concepts/jailbreak-detection", base="azure")),
    pricing=("Foundry Agent Service pricing", "https://azure.microsoft.com/pricing/details/foundry-agent-service/"),
    rbac=("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
)


def src(*keys: str) -> list:
    return [U[k] for k in keys]


def card(w, title, body, theme="teal", **kw) -> Card:
    """Dense-column card: one type scale for the whole canvas."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("sub_size", 13)
    kw.setdefault("pad", 14)
    kw.setdefault("gap", 4)
    kw.setdefault("icon_size", 30)
    return Card(w, title, body, theme=theme, **kw)


def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(wrap_text(s, w, size))


def lk(label, key):
    return {"text": label, "link": U[key][1], "color": LINK}


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


class Tile(Rect2):
    """Big-number summary tile: headline + one caption."""

    def __init__(self, w, big, cap, theme="teal", big_size=34, cap_size=15, pad=14):
        self.th = THEMES[theme]
        self.w, self.big_size, self.cap_size, self.pad = w, big_size, cap_size, pad
        inner = (w - 2 * pad) * 0.965
        self.big_lines = wrap_text(big, inner, big_size)
        self.cap_lines = wrap_text(cap, inner, cap_size)
        lr = metrics.line_ratio()
        self.h = pad * 2 + len(self.big_lines) * big_size * lr + 8 + len(self.cap_lines) * cap_size * lr
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            ty = y + self.pad
            inner = self.w - 2 * self.pad
            cv.text(x + self.pad, ty, "\n".join(self.big_lines), size=self.big_size, color=th.deep, align="center", w=inner)
            ty += len(self.big_lines) * self.big_size * lr + 8
            cv.text(x + self.pad, ty, "\n".join(self.cap_lines), size=self.cap_size, color=INK, align="center", w=inner)
        cv.register("tile", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class Steps(Rect2):
    """Numbered walk-through card: the circles match the numbered arrows of the diagram next to it."""

    def __init__(self, w, title, steps, theme="yellow", num_theme="blue", size=14, pad=14, src=(), title_size=19):
        self.th = THEMES[theme]
        self.w, self.title, self.steps, self.num_theme, self.size, self.pad, self.title_size = w, title, steps, num_theme, size, pad, title_size
        self.tw = (w - 2 * pad - 38) * 0.965
        lr = metrics.line_ratio()
        self.lines = [wrap_text(t, self.tw, size) for t in steps]
        self.row_h = [max(len(ln) * size * lr, 26) + 9 for ln in self.lines]
        self.src = list(src)
        h = pad + title_size * lr + 8 + sum(self.row_h) + 4
        self.src_lines = []
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * lr + 2
        self.h = h + pad - (2 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=th.deep)
            cy = y + self.pad + self.title_size * lr + 8
            for i, (ln, rh) in enumerate(zip(self.lines, self.row_h)):
                numbered(cv, x + self.pad + 13, cy + 13, i + 1, theme=self.num_theme, d=26, size=15)
                cv.text(x + self.pad + 38, cy + 4, "\n".join(ln), size=self.size, color=INK)
                cy += rh
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("steps", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def badge_on(cv, blk, kind, dx=-10, dy=-12):
    """Status pill straddling the top-right corner of a placed block."""
    lab = {"ga": "GA", "preview": "Preview", "retiring": "Retiring", "new": "New", "classic": "Classic"}.get(kind, kind)
    bw = metrics.line_width(lab, 13) + 18
    draw_badge(cv, blk.right - bw + dx + 10, blk.y + dy, kind)


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "Public preview", "Memory and the Memory Store API are preview: pricing, consolidation behavior and API versions can change.", "yellow"),
        Tile(C, "3 memory types", "User profile, chat summary and procedural - all enabled by default and set when you create the store.", "teal"),
        Tile(C, "scope = the key", "Each scope is an isolated collection: 100 scopes per store, 10,000 memories per scope.", "teal"),
        Tile(C, "300 s debounce", "update_delay: writes wait for inactivity - default 300 s (5 min); samples use 1 s, 0 triggers processing at once.", "violet"),
        Tile(C, "No VNet", "Memory stores do not support VNet integration; they need chat and embedding model deployments.", "indigo"),
        Tile(C, "1,000 / min", "Search memories and update memories are each limited to 1,000 requests per minute.", "yellow"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: big picture
def band_big(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  The big picture - a memory pipeline over a vault",
             "Write path on top (conversation, debounce, extract, consolidate, store); read path below (search, inject, answer). The three phases are the docs' own words.")
    top = y
    bw, bh = 410, 170
    xs = [560, 1058, 1556]
    # left conversations
    with cv.panel(0, top + 20, title="Session A", sub="the user states something worth keeping", theme="gray", style="dotted", pad=18, title_size=22, sub_size=14,
                  min_w=470, min_h=210) as pa:
        Bubble(380, "I'm allergic to dairy.", theme="gray", tail="left", size=17).place(cv, pa.ix + 22, pa.iy + 20)
        cv.text(pa.ix, pa.iy + 94, "A preference like this is the docs' own extraction example.", size=14, color=MUTED, wrap=420)
    with cv.panel(0, top + 330, title="Session B", sub="a new conversation, same scope", theme="gray", style="dotted", pad=18, title_size=22, sub_size=14,
                  min_w=470, min_h=210) as pb:
        Bubble(380, "Suggest a dinner recipe.", theme="gray", tail="left", size=17).place(cv, pb.ix + 22, pb.iy + 20)
        Chip("recalled: allergic to dairy", theme="teal", size=15).place(cv, pb.ix + 22, pb.iy + 92)
    w1 = Box(bw, "After each response", sub="the service schedules update_memories; it runs after update_delay seconds of inactivity (debounce)", theme="green", h=bh, size=20,
             sub_size=14, fill="hatch", icon="agent", icon_pos="top", icon_size=30)
    w1.place(cv, xs[0], top + 40)
    w2 = Box(bw, "1  Extraction", sub="an LLM pulls key information from the conversation: preferences, facts, context", theme="teal", h=bh, size=21, sub_size=14, fill="hatch")
    w2.place(cv, xs[1], top + 40)
    w3 = Box(bw, "2  Consolidation", sub="LLMs merge similar or duplicate topics and resolve conflicting facts (a new allergy)", theme="teal", h=bh, size=21, sub_size=14,
             fill="hatch")
    w3.place(cv, xs[2], top + 40)
    r1 = Box(bw, "3  Retrieval", sub="search_memories: static (profile) memories early in a conversation, contextual ones each turn", theme="teal", h=bh, size=21, sub_size=14,
             fill="hatch")
    r1.place(cv, xs[2], top + 350)
    r2 = Box(bw, "Inject as context", sub="the memory search tool adds recalled memories to response generation", theme="green", h=bh, size=20, sub_size=14, fill="hatch")
    r2.place(cv, xs[1], top + 350)
    r3 = Box(bw, "Model answers", sub="personalized with what it remembers about this scope", theme="blue", h=bh, size=20, sub_size=14, fill="hatch", icon="openai",
             icon_pos="top", icon_size=30)
    r3.place(cv, xs[0], top + 350)
    # vault
    vx = 2090
    with cv.panel(vx, top, title="Memory store (create one per agent)", sub="a chat model deployment and an embedding model deployment process the content", theme="teal",
                  style="solid", fill="soft", pad=24, title_size=28, sub_size=16, min_w=W - vx, min_h=560) as vault:
        sy = vault.iy + 10
        shelves = [("scope A", "for example user_123", True), ("scope B", "another user: isolated", False), ("scope C", "shared, for example a resource id", False)]
        shelf_w = W - vx - 48
        for nm, sub, first in shelves:
            cv.rect(vault.ix, sy, shelf_w, 118, stroke=THEMES["teal"].stroke, fill="#ffffff", style="solid", sw=1.5, dash="dashed")
            Box(300, nm, sub=sub, theme="gray", h=84, size=20, sub_size=13, fill="hatch").place(cv, vault.ix + 16, sy + 17)
            kx = vault.ix + 16 + 300 + 40
            for kind in ("User profile", "Chat summary", "Procedural"):
                Box(300, kind, theme="teal", h=60, size=18, fill="hatch").place(cv, kx, sy + 12)
                kx += 300 + 20
            if first:
                cv.text(vault.ix + 16 + 300 + 40, sy + 82, "e.g. 'allergic to dairy'", size=14, color=MUTED)
            sy += 118 + 16
        cv.text(vault.ix, sy + 4, "Each scope keeps an isolated collection of memory items. Per store: up to 100 scopes; per scope: up to 10,000 memories.", size=15, color=INK,
                wrap=shelf_w)
    # arrows
    connect(cv, pa, w1, a_side="right", b_side="left", sw=3)
    connect(cv, w1, w2, a_side="right", b_side="left", sw=3, gap=3)
    connect(cv, w2, w3, a_side="right", b_side="left", sw=3, gap=3)
    arrow(cv, [(w3.right + 6, w3.cy), (vx - 6, w3.cy)], sw=3, label="write items", label_size=15, label_dy=-2)
    arrow(cv, [(vx - 6, r1.cy), (r1.right + 6, r1.cy)], sw=3, label="search", label_size=15, label_dy=-2)
    connect(cv, r1, r2, a_side="left", b_side="right", sw=3, gap=3)
    connect(cv, r2, r3, a_side="left", b_side="right", sw=3, gap=3)
    connect(cv, r3, pb, a_side="left", b_side="right", sw=3)
    cv.text(xs[0], top + 40 + bh + 18, "WRITE PATH: asynchronous, never blocks the reply", size=15, color=THEMES["teal"].deep)
    cv.text(xs[0], top + 350 + bh + 18, "READ PATH: per conversation start and per turn", size=15, color=THEMES["teal"].deep)
    y1 = max(vault.bottom, pb.bottom, top + 350 + bh + 40) + 36
    st = Steps(S(3), "Five-step flow (the docs' sequence)", [
        "Create the memory store (chat + embedding models, options) and attach the memory search tool (type memory_search_preview) with scope {{$userId}}",
        "Turn N: the client sends the response request (+ x-memory-user-id); the service injects static (profile) memories, retrieves contextual ones, the model answers",
        "After the response the service schedules update_memories; after update_delay of inactivity, extraction and consolidation write or merge items for that scope",
        "New conversation, same scope: the agent recalls the preference; an explicit 'remember ...' request is applied immediately as a memory command (memory_command_call)",
        "Erasure: delete_scope removes one user's memories, or delete the whole store (dependent agents lose that context)",
    ], theme="teal", num_theme="teal", src=src("usage"))
    st.place(cv, 0, y1)
    uc = card(S(3), "When memory is the right tool - and use cases from the docs", [
        "Use memory for user-specific or agent context that is learned and persists through interactions over time",
        "Use a Foundry IQ knowledge base to ground the agent on curated organizational content",
        "Use the file search tool to search user-provided documents during an interaction",
        "Support agent: remembers name, previous issues and resolutions, ticket numbers and the preferred contact method",
        "Shopping assistant: sizes in brands, preferred colors, past returns, recent purchases. Travel agent: seat, food and loyalty preferences",
        "Research agent: which compounds were tested and failed, key findings from different labs",
    ], theme="teal", icon="iq", src=src("what"))
    uc.place(cv, X(3), y1)
    return max(st.bottom, uc.bottom)


# ================================================================================================ band 2: four kinds of state
def band_kinds(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Short-term, long-term and durable state - four different boxes",
             "Memory is semantic and LLM-curated; session state is the live conversation; the state store is explicit key-value data you manage; a knowledge base is curated content.")
    cw = (W - 3 * G) / 4
    c1 = card(cw, "Short-term: session and conversation state", [
        "The current session's conversation: immediate context for ongoing turns",
        "Agent orchestration frameworks typically manage it as session context",
        "Agent Service: conversations and items persist history across turns (Responses model)",
        "Hosted agents: sessions with $HOME and /files that survive idle deprovisioning",
    ], theme="gray", icon="gear", src=src("what", "runtime"))
    c2 = card(cw, "Long-term: Foundry Memory", [
        "Distilled knowledge retained across sessions, devices and workflows",
        "A managed memory store holds the items; extraction and consolidation are done by LLMs",
        "Isolated per scope; TTL, delete_scope, item CRUD and direct remember/forget commands",
        "Works with prompt agents (tool), hosted agents (provider) and frameworks",
    ], theme="teal", icon="iq", badge="preview", src=src("what"))
    c3 = card(cw, "Durable state store (hosted agents only)", [
        "Server-backed key-value JSON that survives container crashes, restarts and idle eviction",
        "Your code writes and updates it explicitly - the platform does not populate it",
        "Typical contents: framework checkpoints, app-managed history, artifacts, preferences",
        "Item up to 1 MB; idle window removes items (default 30 days, or never); tags, ETags",
    ], theme="cyan", icon="storage", src=src("state"))
    c4 = card(cw, "Knowledge: Foundry IQ and file search", [
        "A Foundry IQ knowledge base grounds the agent on curated organizational content",
        "The file search tool searches documents the user provides during an interaction",
        "Neither learns from conversations: you curate or the user supplies the content",
    ], theme="indigo", icon="search", src=src("iq", "filesearch"))
    _, b = row(cv, 0, y, [c1, c2, c3, c4], gap=G)
    t = Table(
        [("", 200), ("Foundry Memory", 800), ("Session / conversation state", 700), ("FoundryStateStore", 1000), "Foundry IQ and file search"],
        [
            [ct("Holds", "gray"), "Distilled user profile facts, chat summaries and procedural how-to routines", "The live conversation; for hosted agents also session files in $HOME and /files",
             "Your own JSON: checkpoints, app-managed history, intermediate artifacts, per-user preferences", "Curated organizational content, or documents supplied by the user"],
            [ct("Who writes it", "gray"), "The service (extraction + consolidation after responses), or you through remember/forget commands and item CRUD",
             "The runtime or framework and the platform as turns happen", "Your agent code, explicitly", "You curate it or the user uploads it"],
            [ct("Isolation", "gray"), "Scope: per user, team, resource or any stable id; 100 scopes per store", "Per session or conversation",
             "Store name as the partition, plus optional per-user isolation resolved from the call ID (not in local runs)", ("Not stated in the pages read", "gray")],
            [ct("Lifetime and limits", "gray"), "Store default TTL (0 = never) on every memory; 10,000 memories per scope", "Hosted sessions: idle timeout deprovisions compute, files kept (see the hosted-agent canvases)",
             "Item <= 1 MB; tags <= 16; store idle window default 30 days or never (writes renew, reads do not)", ("Not stated in the pages read", "gray")],
            [ct("Use it when", "gray"), "The agent should learn context about a user or itself that must persist across sessions", "You need turn-by-turn context inside one session",
             "State must outlive the container: checkpoints, app-managed history, artifacts", "Grounding on curated content (IQ) or on user-provided documents (file search)"],
        ], w=W, theme="teal", size=14, head_size=15, title="Which one for which job", title_size=22)
    t.place(cv, 0, b + 40)
    return t.bottom


# ================================================================================================ band 3: lifecycle in detail
def band_lifecycle(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  The lifecycle in detail - extract, consolidate, retrieve",
             "One preference travels from session A to session B. Numbers follow the sequence; the cards on the right hold the documented behavior of each phase.")
    top = y
    seq = Sequence(cv, 0, top, [("User or app", "gray", "user"), ("Agent + memory search tool", "green", "agent"), ("Memory store service", "teal", "storage"),
                                ("Chat + embedding models", "blue", "openai")], spacing=515, head_w=230, head_h=62, size=16, label_size=15)
    seq.msg(0, 1, "Session A, turn N: response request, with x-memory-user-id for a backend caller", num=1)
    seq.msg(1, 2, "Conversation start: inject static (user profile) memories. Each turn: search contextual memories", num=2)
    seq.msg(2, 1, "memories (the field is memories, not the legacy results)", dash="dashed")
    seq.msg(1, 0, "Answer, personalized with the recalled context", dash="dashed", num=3)
    seq.msg(1, 2, "After the response: schedule update_memories", num=4, note="Debounced: the write finishes only after update_delay seconds of inactivity")
    seq.msg(2, 3, "Extract, consolidate and embed the new content", num=5, note="Chat model extracts and consolidates; embedding model indexes")
    seq.msg(0, 1, "Session B (new conversation), same scope: asks something related", num=6)
    seq.msg(1, 2, "search by scope", num=7)
    seq.msg(1, 0, "Recalled preference shapes the answer", dash="dashed", num=8)
    sb = seq.end()
    cw = (S(3) - 2 * 24) / 3
    c1 = card(cw, "1  Extraction", [
        "Pulls key information from the conversation: preferences, facts and context",
        "user_profile_details steers what to capture or avoid (for example age, financials, precise location, credentials)",
        "The service calls update_memories internally after each response; the write completes after update_delay of inactivity",
        "update_delay default 300 s; samples use 1 s; the low-level update can use 0",
        "Low-level add is long-running (about 1 minute): chain with previous_update_id and poll GET /memory_stores/{name}/updates/{update_id}",
    ], theme="teal", src=src("what", "usage"))
    c2 = card(cw, "2  Consolidation", [
        "LLMs merge similar or duplicate topics so the store does not keep redundant information",
        "Conflicting facts (for example a new allergy) are resolved to keep the memory accurate",
        "Behavior varies by memory type and may change during preview",
        "A memory that is updated and consolidated resets its TTL clock",
    ], theme="teal", src=src("what", "usage"))
    c3 = card(cw, "3  Retrieval", [
        "Retrieve stable user-profile information early: static = search_memories with a scope but no items",
        "Contextual = search_memories with items set to the latest messages; may return profile and chat-summary memories",
        "Chain searches with previous_search_id; options.max_memories caps the result",
        "The memory search tool does both for you: static at conversation start, contextual each turn",
        "Procedural memories: retrieve when the user asks for a recurring workflow",
    ], theme="teal", src=src("what", "usage"))
    cx = X(3)
    c1.place(cv, cx, top)
    c2.place(cv, cx + cw + 24, top)
    c3.place(cv, cx + 2 * (cw + 24), top)
    ty = max(c1.bottom, c2.bottom, c3.bottom) + 28
    # debounce mini timeline
    cv.text(cx, ty, "The debounced write path", size=22, color=THEMES["violet"].deep)
    bw, bh = 250, 100
    gap = (S(3) - 5 * bw) / 4
    ev = [("Turn 1 response", "update_memories scheduled", "green"), ("Turn 2 response", "timer restarts", "green"), ("Inactivity", "update_delay elapses (default 300 s)", "gray"),
          ("Extract + consolidate", "items written or merged", "teal"), ("Memories visible", "next search can return them", "teal")]
    bs = []
    for i, (t_, s_, th) in enumerate(ev):
        b = Box(bw, t_, sub=s_, theme=th, h=bh, size=17, sub_size=13, fill="hatch")
        b.place(cv, cx + i * (bw + gap), ty + 40)
        bs.append(b)
    for i in range(4):
        connect(cv, bs[i], bs[i + 1], a_side="right", b_side="left", sw=2.5, gap=3)
    hbrace(cv, bs[1].right - 20, bs[3].x + 20, ty + 40 - 10, side="top", depth=14)
    cv.text(bs[2].cx - 150, ty + 40 - 52, "update_delay", size=15, color=THEMES["violet"].deep, align="center", w=300)
    n = Note(S(3), "In the latest preview: memory item operations (create, read, update, list, delete), a store-level default TTL, and direct remember-or-forget commands. "
                   "Memory items live in a managed memory store; if memories do not appear after a conversation, the update is still debounced - raise the wait or call "
                   "the update API with update_delay set to 0.", kind="preview", title="Latest preview and the debounce gotcha", size=15, src=src("what", "usage"))
    n.place(cv, cx, ty + 40 + bh + 30)
    return max(sb, n.bottom)


# ================================================================================================ band 4: stores, types and options
def band_stores(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Memory stores, types and options",
             "Create one store per agent. All three memory types are on by default; options such as procedural memory and the default TTL are set at creation.")
    top = y
    t = Table(
        [("Memory type", 240), ("What it holds", 760), ("Retrieval guidance", 676), ("How the API retrieves it", 676)],
        [
            [ct("User profile memory", "teal"), "Durable preferences and personal context: language preference, product defaults, accessibility needs",
             "Retrieve near the beginning of each conversation to set stable personalization", "Static: search_memories with a scope and no items (item kind user_profile)"],
            [ct("Chat summary memory", "teal"), "Distilled summaries of prior conversation topics and threads", "Retrieve each turn using the current conversation messages",
             "Contextual: search_memories with items = the latest messages"],
            [ct("Procedural memory", "teal"), "Reusable how-to routines and operating patterns inferred from prior interactions",
             "Retrieve when the user asks for a recurring workflow or task the agent has handled before", "Enable with procedural_memory_enabled at store creation"],
        ], w=S(4), theme="teal", size=14, head_size=15, title="Three memory types (the concept page)", title_size=22)
    t.place(cv, 0, top)
    nd = Note(S(4), "Docs disagree on the count: the concept page lists three types (user profile, chat summary, procedural); the LangChain page lists two (user profile, chat summary); "
                    "the Build 2026 blog (not Learn) says 'procedural, user and session context'. The REST item kind values beyond user_profile were not enumerated in the pages read.",
              kind="warn", title="Docs disagree: how many memory types", size=15, src=src("what", "langchain"))
    nd.place(cv, 0, t.bottom + 22)
    cdef = card(S(2), "What you create: the store definition", [
        "POST {project}/memory_stores?api-version=2025-11-15-preview - the memory-store API version; the agents API uses api-version=v1",
        "definition { kind: default, chat_model, embedding_model, options {...} }",
        "options: chat_summary_enabled, user_profile_enabled, procedural_memory_enabled, default_ttl_seconds (0 = never), user_profile_details",
        "Needs a chat deployment (the docs use gpt-5.2) and an embedding deployment (text-embedding-3-small) in the project",
        "Some defaults, such as procedural memory and the default TTL, are fixed at creation - verify post-create updates for your API version",
    ], theme="teal", icon="storage", badge="preview", src=src("usage", "rest"))
    cdef.place(cv, X(4), top)
    y1 = max(nd.bottom, cdef.bottom) + 40
    ops = Table(
        [("Group", 190), ("Operation (as used in the how-to)", 980), ("Notes", 1182)],
        [
            [ct("Store admin", "teal"), "create, get, list, update (description, metadata), delete a memory store", "One store per agent; deleting a store removes every scope, so dependent agents lose their history"],
            [ct("Write path", "teal"), "POST /memory_stores/{name}:update_memories, then GET /memory_stores/{name}/updates/{update_id}", "Long-running (about 1 minute); chain with previous_update_id; poll the update id or fire and forget"],
            [ct("Read path", "teal"), "POST /memory_stores/{name}:search_memories", "scope required; optional items and previous_search_id; options.max_memories"],
            [ct("Items (preview)", "teal"), "create, get, list (items:list?scope=), update and delete a single memory item", "Item-level CRUD; for user-facing edit and delete controls"],
            [ct("Erase", "teal"), "POST /memory_stores/{name}:delete_scope", "Removes all memories of one scope: user data-deletion requests or resets"],
        ], w=S(4), theme="teal", size=14, head_size=15, title="Memory Store API surface (the REST group lists 14 operations)", title_size=22)
    ops.place(cv, 0, y1)
    ttl = card(S(2), "TTL and retention rules", [
        "default_ttl_seconds applies to all memories: extraction, commands and item CRUD; 0 means no expiration",
        "A memory that is updated and consolidated resets its last-updated time",
        "Direct remember commands do not override the TTL - such items can still expire",
        "TTL only affects stores created after TTL support was introduced",
    ], theme="yellow", icon="quotas", src=src("usage"))
    ttl.place(cv, X(4), y1)
    return max(ops.bottom, ttl.bottom)


# ================================================================================================ band 5: scope
def band_scope(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Scope - the isolation key",
             "Every request is partitioned by scope. The tool can resolve it from the caller's identity; the low-level APIs never can.")
    top = y
    # decision flow (left S(3))
    cyy = top + 120
    a = Box(270, "Memory search tool", sub="the scope setting in the tool definition", theme="green", h=104, size=19, sub_size=14, fill="hatch", icon="agent", icon_pos="left")
    a.place(cv, 0, cyy - 52)
    d1 = Box(330, "scope = {{$userId}}?", theme="yellow", shape="diamond", h=190, size=17, fill="hatch")
    d1.place(cv, 350, cyy - 95)
    d2 = Box(340, "x-memory-user-id header present?", theme="yellow", shape="diamond", h=190, size=16, fill="hatch")
    d2.place(cv, 770, cyy - 95)
    l1 = Box(560, "User id = the header value", sub="proxy and backend scenarios: your service calls on behalf of an end user", theme="teal", h=96, size=18, sub_size=14, fill="hatch")
    l1.place(cv, S(3) - 560, top + 10)
    l2 = Box(560, "User id = the caller's Entra token", sub="falls back to tenant ID and object ID ({tid}_{oid}); the default for frontend callers", theme="teal", h=96, size=18,
             sub_size=14, fill="hatch")
    l2.place(cv, S(3) - 560, top + 150)
    ls = Box(560, "Static scope value", sub="no per-user isolation needed: every caller shares that scope", theme="gray", h=96, size=18, sub_size=14, fill="hatch")
    ls.place(cv, 350 - 115, top + 270)
    connect(cv, a, d1, a_side="right", b_side="left", sw=2.5)
    connect(cv, d1, d2, a_side="right", b_side="left", sw=2.5)
    connect(cv, d2, l1, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, d2, l2, a_side="right", b_side="left", route="elbow", sw=2.5, dash="dashed")
    connect(cv, d1, ls, a_side="bottom", b_side="top", sw=2.5, dash="dashed")
    cv.text(d1.right + 14, cyy - 26, "yes", size=14, color="#c92a2a")
    xm = (d2.right + 6 + l1.x - 6) / 2
    cv.text(xm + 14, l1.cy - 26, "yes", size=14, color="#c92a2a")
    cv.text(xm + 14, l2.cy - 26, "no", size=14, color="#c92a2a")
    cv.text(d1.cx + 14, d1.bottom + 8, "no", size=14, color="#c92a2a")
    api = Box(S(3), "Low-level memory APIs (no tool)", sub="scope must be explicit on every request: a UUID or another stable id from your system - there is no automatic resolution "
                                                          "from the caller's identity", theme="orange", h=104, size=20, sub_size=15, fill="hatch", icon="api", icon_pos="left")
    api.place(cv, 0, top + 400)
    lc = Table(
        [("LangChain id", 220), ("Use it as", 644)],
        [
            [ct("user id", "teal"), "The stable identity for long-term memory (the scope); keep it the same across sessions"],
            [ct("session id / thread id", "gray"), "The short-term conversation identity; change it for each chat session"],
            [ct("resource id", "teal"), "A stable identifier for long-term memory shared across multiple users"],
        ], w=864, theme="teal", size=14, head_size=15, title="LangChain and LangGraph identity mapping", title_size=22)
    lc.place(cv, X(3), top)
    nn = Note(864, "Memory's tool path and the API path are different on purpose: only the memory search tool resolves {{$userId}}. A search that returns nothing usually means the "
                   "scope differs from the one used when the memories were stored.", kind="gotcha", title="Scope gotcha", size=15, src=src("usage", "what"))
    nn.place(cv, X(3), lc.bottom + 22)
    bp = card(864, "Best practices (the how-to)", [
        "Partition per user with scope; do not give agents memories shared across all users",
        "If a scope is shared, use user_profile_details to tell the system not to store personal information",
        "Store only what is necessary; redact content that could trace back to an individual",
        "Give users transparency, access and deletion; keep a tamper-evident audit trail of deletions",
        "Expose item-level edit and delete controls; set explicit TTL defaults; monitor token use and memory operations",
        "In multi-agent systems segment memory logically and operationally",
    ], theme="red", icon="managed-identity", src=src("usage"))
    bp.place(cv, X(3) + 864 + 48, top)
    return max(top + 520, lc.bottom, nn.bottom, bp.bottom)


# ================================================================================================ band 6: how agents use it
LX = 560


def lane_frame(cv, y, h, n, title, sub, theme, badge=None, src_=()):
    th = THEMES[theme]
    cv.rect(0, y, W, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    numbered(cv, 44, y + 44, n, theme=theme, d=44, size=24)
    t = cv.text(84, y + 20, title, size=25, color=th.deep, wrap=410)
    s = cv.text(86, t.bottom + 6, sub, size=15, color="#495057", wrap=410)
    by = s.bottom + 12
    if badge:
        draw_badge(cv, 86, by, badge)
        by += 34
    for lab, url in src_:
        cv.text(86, by, f"Learn: {lab}", size=12, color=LINK, link=url, wrap=410)
        by += 17
    cv.line((520, y + 18), (520, y + h - 18), stroke=th.stroke, sw=1.5, dash="dotted", opacity=60)


def lane(cv, y, min_h, n, title, sub, theme, badge, srcs, a, b, store_sub, facts, facts_title):
    """One 'way in' lane; its height follows the facts card. Returns the lane's bottom y."""
    c = card(W - (LX + 430 + 90 + 560 + 90 + 360 + 60) - 24, facts_title, facts, theme=theme, title_size=18)
    h = max(min_h, c.h + 44)
    lane_frame(cv, y, h, n, title, sub, theme, badge, srcs)
    cy = y + h / 2
    ba = Box(430, a[0], sub=a[1], theme=a[2], h=124, size=19, sub_size=14, fill="hatch", icon=a[3], icon_pos="left")
    ba.place(cv, LX, cy - 62)
    bb = Box(560, b[0], sub=b[1], theme=b[2], h=124, size=19, sub_size=14, fill="hatch", icon=b[3], icon_pos="left")
    bb.place(cv, ba.right + 90, cy - 62)
    bs = Box(360, "Memory store", sub=store_sub, theme="teal", h=124, size=20, sub_size=14, fill="hatch", icon="storage", icon_pos="left")
    bs.place(cv, bb.right + 90, cy - 62)
    connect(cv, ba, bb, a_side="right", b_side="left", sw=3, gap=4)
    connect(cv, bb, bs, a_side="right", b_side="left", sw=3, gap=4, start_head="arrow")
    c.place(cv, bs.right + 60, cy - c.h / 2)
    return y + h


def band_agents(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  How agents use it - four ways in",
             "The memory search tool is the simple path for prompt agents; hosted agents and frameworks wire a store through code; the low-level APIs give full control.")
    GP = 24
    y = lane(cv, y, 240, 1, "Prompt agents: the memory search tool", "Attach one tool; the service does retrieval and updates", "teal", "preview", src("usage"),
             ("Prompt agent", "definition: model, instructions, tools", "green", "agent"),
             ("Memory search tool", "type memory_search_preview: memory_store_name, scope, update_delay", "teal", "iq"), "chat + embedding models inside",
             [
                 "SDK: MemorySearchPreviewTool inside PromptAgentDefinition; scope {{$userId}} resolves per end user",
                 "Static memories are injected at conversation start; contextual memories are retrieved each turn",
                 "Remember/forget requests are applied immediately and returned as memory command items (memory_command_call)",
                 "Output uses the memories field (not the legacy results)",
                 "! Not supported with connected models or with the Copilot harness",
             ], "What to know") + GP
    y = lane(cv, y, 240, 2, "Hosted agents: a provider in your code", "Attach a store through code; the sample wires retrieval and updates", "green", "preview",
             src("qshosted", "azyaml"),
             ("Hosted agent code", "Microsoft Agent Framework sample, Python or C#", "green", "container-apps"),
             ("FoundryMemoryProvider", "retrieves memories before each model call and updates the store after each turn", "teal", "iq"), "created by a postprovision hook",
             [
                 "azd: a top-level postprovision hook creates the store; default name agent_framework_memory (env MEMORY_STORE_NAME); C#: AZURE_AI_MEMORY_STORE_ID, default foundry-memory-rag-store",
                 "Stores can also be declared in azure.yaml (chatModel, embeddingModel, options.*); quickstart paths: azd, Python SDK, C# SDK",
                 "Python path routes traffic with FixedRatioVersionSelectionRule(traffic_percentage=100) while testing",
                 "Roles: Foundry User plus Cognitive Services OpenAI User, otherwise writes fail with 401 and the store stays empty",
                 "Memory (semantic, LLM-curated) is separate from sessions ($HOME, /files), conversations and FoundryStateStore",
             ], "What to know") + GP
    y = lane(cv, y, 240, 3, "Frameworks: LangChain and LangGraph", "Keep short-term history in the runtime; long-term in Foundry Memory", "indigo", "preview",
             src("langchain"),
             ("LangChain or LangGraph app", "short-term chat history stays in the runtime", "indigo", "langgraph"),
             ("langchain-azure-ai", "AzureAIMemoryChatMessageHistory + AzureAIMemoryRetriever (retriever k=5 in the sample)", "teal", "python"), "scope = the stable user id",
             [
                 "Use a stable user id as the scope; a session id (or LangGraph thread id) as the short-term identity",
                 "Retrieve user profile memory early and chat-summary memory per turn; inject the text into the model input or a pre-model hook",
                 "update_delay=0 is test mode; the default is about 300 s",
                 "client.memory_stores.delete_scope cleans up test data; two memory types are shown on this page",
             ], "What to know") + GP
    return lane(cv, y, 240, 4, "Low-level APIs: any app or agent code", "Direct control over records, retention and the memory lifecycle", "orange", "preview",
                src("usage", "rest"),
                ("Your app or agent", "calls the memory_stores APIs directly", "gray", "app"),
                ("update_memories / search_memories", "plus item CRUD, delete_scope and store admin", "orange", "api"), "scope on every request",
                [
                    "scope is mandatory on every request; there is no automatic resolution from the caller identity",
                    "Add memories from conversation content; the update is a long-running operation (about 1 minute) you can poll or fire and forget",
                    "Search static (scope only) or contextual (items = latest messages) memories and inject them yourself",
                    "Item-level create, get, list, update and delete for user-facing controls and retention behavior",
                ], "What to know")


# ================================================================================================ band 7: quotas, privacy
def band_privacy(cv: Canvas, y: float) -> float:
    y = head(cv, y, "7  Quotas, regions and privacy - what to check before production",
             "Memory is preview: validate quotas, regions and the privacy controls below; the docs state the memory-specific limits and only general Agent Service data handling.")
    top = y
    qt = Table(
        [("Quota (as of 2026-11-03)", 640), ("Limit", 528)],
        [
            ["Scopes per memory store", "100"], ["Memories per scope", "10,000"], ["Search memories", "1,000 requests / minute"],
            ["Update memories", "1,000 requests / minute"],
        ], w=S(2), theme="yellow", size=15, head_size=16, title="Quotas", title_size=22)
    qt.place(cv, 0, top)
    req = card(S(2), "Requirements and limits", [
        "Compatible Azure OpenAI chat and embedding model deployments in the project",
        "The project's system-assigned managed identity enabled and given Foundry User on the account",
        "Hosted-agent quickstart: also Cognitive Services OpenAI User, else writes fail with 401",
        "! No VNet integration for memory stores; not with connected models or the Copilot harness",
        "Pricing: preview; you pay for the underlying chat and embedding model usage, and rates can change",
    ], theme="indigo", icon="vnet", src=src("what", "pricing"))
    req.place(cv, 0, qt.bottom + 28)
    regs = ["Australia East", "Brazil South", "Canada East", "East US 2", "France Central", "Italy North", "Japan East", "Korea Central", "North Central US", "Norway East",
            "South Africa North", "South India", "Sweden Central", "Switzerland North", "UAE North", "UK South", "West US", "West US 2", "West US 3"]
    with cv.panel(X(2), top, title="Regions with memory (19, as of 2026-11-03)", sub="the concept page lists no others", theme="indigo", style="dotted", pad=20, title_size=22,
                  sub_size=14, min_w=S(2)) as rp:
        ChipFlow(regs, w=S(2) - 44, theme="indigo", size=15, fill="soft").place(cv, rp.ix, rp.iy + 4)
    sec = card(S(2), "Memory poisoning and prompt injection", [
        "An LLM extracts and consolidates what is stored, so incorrect or harmful content can end up in memory and steer later answers",
        "Validate inputs and outputs of the memory system with prompt injection detection",
        "Attack-test the agent regularly and treat memory content as untrusted until proven otherwise",
    ], theme="pink", icon="content-safety", src=src("what", "safety"))
    sec.place(cv, X(2), rp.bottom + 28)
    # guard-rail flow (third column pair)
    gx = X(4)
    cv.text(gx, top, "Where to put the guard rails", size=22, color=THEMES["pink"].deep)
    gy = top + 50
    b1 = Box(150, "Conversation", theme="gray", h=76, size=16, fill="hatch")
    b1.place(cv, gx, gy + 40)
    g1 = Box(210, "Input check", sub="prompt injection detection", theme="pink", shape="diamond", h=150, size=16, sub_size=12, fill="hatch")
    g1.place(cv, gx + 190, gy + 3)
    b2 = Box(190, "Memory system", sub="LLM extraction and consolidation", theme="teal", h=100, size=16, sub_size=12, fill="hatch")
    b2.place(cv, gx + 440, gy + 28)
    b3 = Box(140, "Store", sub="scoped items", theme="teal", h=100, size=16, sub_size=12, fill="hatch")
    b3.place(cv, gx + 670, gy + 28)
    g2 = Box(210, "Output check", sub="before memories reach the agent", theme="pink", shape="diamond", h=150, size=16, sub_size=12, fill="hatch")
    g2.place(cv, gx + 840, gy + 3)
    for a_, b_ in ((b1, g1), (g1, b2), (b2, b3), (b3, g2)):
        connect(cv, a_, b_, a_side="right", b_side="left", sw=2.5, gap=3)
    cv.text(gx, gy + 170, "Validate all prompts entering or leaving the memory system with Azure AI Content Safety prompt injection detection, and stress-test with adversarial exercises.",
            size=14, color=INK, wrap=S(2))
    ret = card(S(2), "Data minimization, retention and erasure", [
        "user_profile_details tells the system what to focus on and what to avoid (age, financials, precise location, credentials)",
        "Store-level TTL, delete_scope for a user and item-level delete support retention and data-rights requests",
        "Scope per user prevents cross-user leakage; avoid shared scopes for personal data",
        "General Agent Service handling (not memory-specific): data at rest stays in the resource's geography, AES-256 by default, optional customer-managed keys - "
        "preview features may not support them",
    ], theme="red", icon="key-vault", src=src("usage", "privacy"))
    ret.place(cv, gx, gy + 240 + 28)
    return max(req.bottom, sec.bottom, ret.bottom)

# ================================================================================================ band 8: operate and gaps
def band_operate(cv: Canvas, y: float) -> float:
    y = head(cv, y, "8  Troubleshoot, docs disagree and what the docs do not say - as of 2026-11-03",
             "The how-to's troubleshooting table, then the places where two pages (or a page and a blog) disagree.")
    top = y
    t = Table(
        [("Symptom", 470), ("Likely cause", 520), ("Fix", 786)],
        [
            ["Authentication or authorization errors", "Your identity or the project managed identity lacks the roles", "Check the role assignments; for REST, generate a fresh access token"],
            ["Memories do not appear after a conversation", "The update is debounced or still processing", "Wait longer, or call the update API with update_delay 0 to process immediately"],
            ["Memory search returns nothing", "The scope differs from the one used when storing", "Use the same scope for update and search; map scope to a stable user id"],
            ["The agent ignores stored memory", "The memory search tool is missing or names the wrong store", "Confirm the agent definition includes memory_search_preview and the right memory_store_name"],
            ["Procedural memory or TTL setting did not take effect", "Default options can only be set at store creation (latest preview)", "Recreate the store with the defaults, or check post-create support for your API version"],
            ["A remember/forget request returned no command items", "Tool configuration, or the phrase was not recognized as a command", "Confirm the tool configuration and test with direct remember/forget phrasing"],
        ], w=S(3), theme="gray", size=14, head_size=15, title="Troubleshooting (the how-to)", title_size=22)
    t.place(cv, 0, top)
    dd = Table(
        [("Topic", 250), ("One source says", 760), ("Another says", 766)],
        [
            [ct("API versions", "orange"), "Memory store API: 2025-11-15-preview", "Agents API: v1 (the two differ in the same article)"],
            [ct("Role names", "orange"), "Foundry User (current name)", "The LangChain page still says Azure AI Developer (legacy naming)"],
            [ct("Memory types", "orange"), "Three types (concept page)", "Two (LangChain page); 'procedural, user, session' (blog)"],
            [ct("update_delay", "orange"), "Default 300 s (5 min); samples use 1 s", "Low-level update and LangChain test mode use 0"],
        ], w=S(3), theme="orange", size=14, head_size=15, title="Docs disagree", title_size=22)
    dd.place(cv, X(3), top)
    g = Note(S(3), "Not documented in the pages read: where memory items are stored at rest and how they are encrypted (only general Agent Service data handling is documented), "
                   "memory pricing rates, how consolidation resolves ties, a maximum item size, and retention beyond the TTL option. Nothing on this canvas fills those gaps.",
             kind="quote", title="What the docs do not say", size=15, src=src("what", "privacy"))
    g.place(cv, X(3), dd.bottom + 24)
    return max(t.bottom, g.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Foundry Memory (Preview): long-term memory for agents",
        "Memory stores, scopes and the extract - consolidate - retrieve lifecycle  |  prompt agents, hosted agents and LangChain  |  quotas, privacy and doc conflicts  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Memory and knowledge", "teal"), ("Identity and security", "red"),
                           ("Observability and triggers", "violet"), ("Cost and capacity", "yellow"), ("State and data", "cyan"), ("Networking", "indigo"),
                           ("Guardrails", "pink"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Prompt agents in depth", "Hosted agents: your code on Foundry's runtime", "Hosted agents: deploy and operate",
                "Microsoft IQ: the enterprise-context layer", "Guardrails and controls", "Network isolation"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_big(cv, y) + 56
    y = band_kinds(cv, y) + 56
    y = band_lifecycle(cv, y) + 56
    y = band_stores(cv, y) + 56
    y = band_scope(cv, y) + 56
    y = band_agents(cv, y) + 56
    y = band_privacy(cv, y) + 56
    y = band_operate(cv, y) + 56
    sources(cv, 0, y, [
        ("Memory in Foundry Agent Service (preview)", U["what"][1]), ("Create and use memory in Foundry Agent Service", U["usage"][1]),
        ("Quickstart: give a hosted agent persistent memory", U["qshosted"][1]), ("Use Foundry Memory with LangChain and LangGraph", U["langchain"][1]),
        ("Build with agents, conversations and responses", U["runtime"][1]), ("Durable state store for hosted agents", U["state"][1]),
        ("azure.yaml reference", U["azyaml"][1]), ("Data, privacy and security for Agent Service", U["privacy"][1]),
        ("Memory Stores REST: create memory store", U["rest"][1]), ("Agent Service limits, quotas and regions", U["limits"][1]),
        ("Hosted agents (concepts)", U["hosted"][1]), ("What is Foundry IQ?", U["iq"][1]),
        ("File search tool", U["filesearch"][1]), ("Prompt injection detection (Azure AI Content Safety)", U["safety"][1]),
        ("Foundry Agent Service pricing", U["pricing"][1]), ("Role-based access control for Foundry", U["rbac"][1]),
    ], w=W, cols=4)
