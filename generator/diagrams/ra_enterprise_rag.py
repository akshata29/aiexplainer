"""Enterprise RAG reference architecture - Foundry IQ knowledge bases on Azure AI Search agentic retrieval."""
from __future__ import annotations

from generator.xd import *
from generator.xd.metrics import line_ratio, line_width
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="ra-enterprise-rag", title="Enterprise RAG / knowledge-grounded agent", section="3", order=4,
    description="Foundry IQ knowledge bases on Azure AI Search agentic retrieval: ask, plan, fan out, synthesize; ingestion, per-user security trimming, the private variant, retrieval options and RAG evaluation.",
    tags=["rag", "foundry-iq", "ai-search", "agentic-retrieval", "knowledge-base", "security-trimming"],
)

W = 3300
CH = 128
GAP = 64
LH = line_ratio()
AS_OF = "as of 2026-11-03"


# ====================================================================== local helpers
def pill(cv: Canvas, x: float, y: float, label: str, theme: str = "blue", size: int = 13, dash: str = "solid"):
    """Small coloured label pill; returns (w, h)."""
    th = get_theme(theme)
    w, h = line_width(label, size) + 18, size * 1.25 + 6
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0, dash=dash)
        cv.text(x + 9, y + 3, label, size=size, color=th.deep)
    return w, h


class Chevron(Rect2):
    """Pipeline step drawn as a chevron (closed polygon) with a centred title + detail line."""

    def __init__(self, w, title, sub="", *, theme="teal", notch=36, first=False, size=20, sub_size=15, num=None,
                 tag=None, tag_theme="blue", h=0, num_theme="blue"):
        self.th = get_theme(theme)
        self.w, self.notch, self.first, self.size, self.sub_size = w, notch, first, size, sub_size
        self.num, self.tag, self.tag_theme, self.num_theme = num, tag, tag_theme, num_theme
        self.left = 14 if first else notch + 8
        self.inner = w - self.left - notch - 8
        self.t_lines = wrap_text(title, self.inner * 0.965, size)
        self.s_lines = wrap_text(sub, self.inner * 0.965, sub_size) if sub else []
        self.text_h = len(self.t_lines) * size * LH + (len(self.s_lines) * sub_size * LH + 4 if sub else 0)
        self.h = max(h, self.text_h + 34)
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "Chevron":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, n = self.th, self.notch
        pts = [(x, y), (x + self.w - n, y), (x + self.w, y + H / 2), (x + self.w - n, y + H), (x, y + H)]
        if not self.first:
            pts.append((x + n, y + H / 2))
        pts.append((x, y))
        with cv.group():
            cv.poly(pts, kind="line", stroke=th.stroke, sw=2, fill=th.fill, fill_style="hachure")
            tx = x + self.left
            ty = y + (H - self.text_h) / 2 + (6 if self.tag else 0)
            cv.text(tx, ty, "\n".join(self.t_lines), size=self.size, color=th.deep, align="center", w=self.inner)
            ty += len(self.t_lines) * self.size * LH + 4
            if self.s_lines:
                cv.text(tx, ty, "\n".join(self.s_lines), size=self.sub_size, color=INK, align="center", w=self.inner)
            if self.tag:
                tw = line_width(self.tag, 13) + 18
                pill(cv, x + self.left + (self.inner - tw) / 2, y + 7, self.tag, self.tag_theme)
            if self.num is not None:
                numbered(cv, x + (n + 4 if not self.first else 18), y + 2, self.num, theme=self.num_theme)
        cv.register(f"chevron:{self.t_lines[0]}", x + n, y, self.w - 2 * n, H)
        return self


class Steps(Rect2):
    """Numbered step list: circles on a dotted spine, headline + detail text, optional Learn citations.
    head_w set -> two-column rows (headline column, detail column) which is more compact."""

    def __init__(self, w, title, steps, *, theme="blue", num_theme="blue", size=15, head_size=17, title_size=22,
                 pad=20, row_gap=11, sub=None, fill="soft", src=(), icon=None, d=34, head_w=None):
        self.th = get_theme(theme)
        self.w, self.title, self.title_size, self.pad, self.d, self.fill = w, title, title_size, pad, d, fill
        self.num_theme, self.size, self.head_size, self.icon, self.head_w = num_theme, size, head_size, icon, head_w
        self.sub = sub
        full_w = w - 2 * pad - d - 18
        text_w = (full_w - head_w - 26) if head_w else full_w
        y = pad + (title_size * LH)
        self.sub_lines = wrap_text(sub, (w - 2 * pad) * 0.965, 15) if sub else []
        if self.sub_lines:
            y += 2 + len(self.sub_lines) * 15 * LH
        y += 12
        self.rows = []
        for n, head, detail in steps:
            hl = wrap_text(head, (head_w or full_w) * 0.965, head_size)
            dl = wrap_text(detail, text_w * 0.965, size) if detail else []
            if head_w:
                hh = max(len(hl) * head_size * LH, len(dl) * size * LH, d)
            else:
                hh = max(len(hl) * head_size * LH + (len(dl) * size * LH + 3 if dl else 0), d)
            self.rows.append((n, hl, dl, y, hh))
            y += hh + row_gap
        y -= row_gap
        self.src = list(src)
        self.src_lines = []
        if self.src:
            y += 10
            for label, url in self.src:
                self.src_lines.append((f"Learn: {label}", url, y))
                y += 12 * LH + 2
            y -= 2
        self.h = y + pad
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "Steps":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, d = self.th, self.pad, self.d
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft if self.fill == "soft" else th.fill,
                    style="solid" if self.fill == "soft" else "hachure", sw=2)
            tx = x + pad
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad - 4, 34)
                tx += 44
            cv.text(tx, y + pad, self.title, size=self.title_size, color=th.deep)
            if self.sub_lines:
                cv.text(x + pad, y + pad + self.title_size * LH + 2, "\n".join(self.sub_lines), size=15, color=MUTED)
            if len(self.rows) > 1:
                cx = x + pad + d / 2
                cv.line((cx, y + self.rows[0][3] + d / 2), (cx, y + self.rows[-1][3] + d / 2), stroke=th.stroke,
                        sw=2, dash="dotted", opacity=70)
            for n, hl, dl, ry, hh in self.rows:
                numbered(cv, x + pad + d / 2, y + ry + d / 2, n, theme=self.num_theme, d=d, size=16)
                bx = x + pad + d + 18
                if self.head_w:
                    cv.text(bx, y + ry + 2, "\n".join(hl), size=self.head_size, color=th.deep)
                    if dl:
                        cv.text(bx + self.head_w + 26, y + ry + 2, "\n".join(dl), size=self.size, color=INK)
                else:
                    cv.text(bx, y + ry, "\n".join(hl), size=self.head_size, color=th.deep)
                    if dl:
                        cv.text(bx, y + ry + len(hl) * self.head_size * LH + 3, "\n".join(dl), size=self.size, color=INK)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self


class KS(Rect2):
    """Knowledge-source chip: icon + label + optional status badge."""

    def __init__(self, w, label, *, theme="teal", icon=None, badge=None, dash="solid", size=15, pad=10, bg="#ffffff"):
        self.th = get_theme(theme)
        self.w, self.icon, self.badge, self.dash, self.size, self.pad, self.bg = w, icon, badge, dash, size, pad, bg
        self.icon_w = 30 if icon else 0
        blabel = STATUS[badge][1] if badge in STATUS else badge
        self.badge_w = (line_width(blabel, 13) + 18) if badge else 0
        tw = w - 2 * pad - self.icon_w - (self.badge_w + 8 if badge else 0)
        self.lines = wrap_text(label, tw * 0.965, size)
        self.h = max(len(self.lines) * size * LH + 16, 42)
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "KS":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=self.bg, style="solid", sw=1.8, dash=self.dash)
            if self.icon:
                place_icon(cv, self.icon, x + self.pad, y + (H - 24) / 2, 24)
            text_h = len(self.lines) * self.size * LH
            cv.text(x + self.pad + self.icon_w, y + (H - text_h) / 2, "\n".join(self.lines), size=self.size, color=INK)
            if self.badge:
                draw_badge(cv, x + self.w - self.pad - self.badge_w, y + (H - 22) / 2, self.badge)
        cv.register(f"ks:{self.lines[0]}", x, y, self.w, H)
        return self


def dial(cv: Canvas, x: float, y: float, w: float, segs, sel: int, *, theme="teal", h=36, size=16, label=None):
    """Segmented selector (reasoning-effort dial). The selected segment is solid."""
    th = get_theme(theme)
    sw_ = w / len(segs)
    with cv.group():
        if label:
            cv.text(x, y - 24, label, size=14, color=MUTED)
        for i, s in enumerate(segs):
            sx = x + i * sw_
            cv.rect(sx, y, sw_, h, stroke=th.stroke, fill=th.fill if i == sel else "#ffffff", style="solid",
                    sw=2.5 if i == sel else 1.5, round_=False, rough=0)
            tw = line_width(s, size)
            cv.text(sx + (sw_ - tw) / 2, y + (h - size * LH) / 2, s, size=size, color=th.deep)
    cv.register("dial", x, y - (24 if label else 0), w, h + (24 if label else 0))


def cites(cv: Canvas, x: float, y: float, items, size: int = 13, gap: int = 28, max_w: float = 0) -> float:
    """Row of clickable 'Learn: ...' citation links; returns the bottom y."""
    cx, cy = x, y
    for label, url in items:
        txt = f"Learn: {label}"
        tw = line_width(txt, size)
        if max_w and cx + tw > x + max_w and cx > x:
            cx, cy = x, cy + size * LH + 4
        cv.text(cx, cy, txt, size=size, color=LINK, link=url)
        cx += tw + gap
    return cy + size * LH


# ====================================================================== sections
def _title(cv: Canvas) -> float:
    right, bottom = title_block(
        cv, 0, 0, "Enterprise RAG / knowledge-grounded agent",
        f"Foundry IQ knowledge bases on Azure AI Search agentic retrieval: ask, plan, fan out, synthesize - ingestion underneath ({AS_OF})",
        icon="foundry", w=W)
    legend(cv, 0, bottom + 18, [("agents", "green"), ("knowledge / IQ / search", "teal"), ("models", "blue"),
                                ("tools / MCP", "orange"), ("identity / security", "red"), ("network", "indigo"),
                                ("data / storage", "cyan"), ("evaluation", "violet"), ("cost / limits", "yellow")])
    msg = "Badges say Preview or GA exactly as the docs label them, " + AS_OF
    cv.text(W - text_size(msg, 15)[0], bottom + 17, msg, size=15, color=MUTED)
    return bottom + 52


def _key_messages(cv: Canvas, y: float) -> float:
    cw = 780
    k1 = Card(cw, "Foundry IQ = the managed knowledge layer", [
        "A knowledge base (KB) groups knowledge sources and is reusable across agents",
        "Engine: agentic retrieval - LLM query planning, parallel subqueries, semantic rerank, synthesis",
        "12 knowledge-source kinds: 6 indexed (content in a search index) and 6 remote (queried live)",
    ], theme="teal", icon="iq", src=[("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq"))])
    k2 = Card(cw, "Azure AI Search required, Agent Service optional", [
        "Azure AI Search hosts the KB and every indexed knowledge source",
        "Agents reach the KB through one MCP tool: knowledge_base_retrieve",
        "No Agent Service? Call the KB retrieve REST API / SDK from Microsoft Agent Framework or any app",
    ], theme="teal", icon="ai-search", src=[("Foundry IQ FAQ", learn("agents/concepts/foundry-iq-faq"))])
    k3 = Card(cw, "GA vs preview follows the Search API version", [
        "2026-04-01 = GA surface: minimal effort, extractiveData output, no LLM inside the KB",
        "2026-08-01-preview = LLM planning, answer synthesis, multi-turn, preview knowledge sources",
        "! The Azure and Foundry portals emit preview-only schemas that may need migrating later",
    ], theme="orange", icon="versions", badge="preview",
        src=[("Agentic retrieval overview", learn("azure/search/agentic-retrieval-overview", base=""))])
    k4 = Card(cw, "Trim at retrieval time, per user", [
        "Per-user filter rides in the header x-ms-query-source-authorization",
        "! Token missing -> permission-enabled sources return results unfiltered (docs' warning)",
        "Enforcement only reflects permissions already synced to the index",
    ], theme="red", icon="key-vault",
        src=[("Document-level access", learn("azure/search/search-document-level-access-overview", base=""))])
    _, b = row(cv, 0, y, [k1, k2, k3, k4], gap=60)
    return b


def _main_diagram(cv: Canvas, y: float) -> float:
    h_r, h_b = section_header(
        cv, 0, y, "Reference architecture: the query path (1-8) and the ingestion path (I1-I5)",
        sub="Ask the agent -> plan -> fan out to knowledge sources -> rerank -> synthesize. Indexed sources are fed by the ingestion chain underneath.",
        size=32)
    dy = h_b + 36
    LEFT_W = 2520
    CX = 2680          # right-hand dependency column
    CW = W - CX
    # ---------------------------------------------------------------- lane A: ask
    la_h = 226
    with cv.panel(0, dy, title="A   Ask: an agent calls the knowledge base through an MCP tool", theme="green",
                  style="dotted", w=LEFT_W, h=la_h, title_size=24, pad=24):
        by = dy + 88
        user = Box(230, "User / client app", sub="Entra identity = caller identity", theme="gray", icon="users",
                   h=112).place(cv, 44, by)
        agent = Box(330, "Agent", sub="Foundry Agent Service (prompt agent); its model decides when to call the tool",
                    theme="green", icon="agent", h=112).place(cv, 394, by)
        mcp = Box(350, "MCP tool: knowledge_base_retrieve", sub="only supported tool; require_approval: never",
                  theme="orange", icon="mcp", h=112).place(cv, 844, by)
        conn = Box(430, "Project connection", sub="RemoteTool | ProjectManagedIdentity | audience https://search.azure.com/",
                   theme="gray", icon="api-connections", h=112, fill="soft").place(cv, 1380, by)
        app = Box(470, "Any app / Microsoft Agent Framework",
                  sub="no Agent Service needed: the app calls the KB retrieve REST API / SDK and sets the user token header itself",
                  theme="gray", icon="app", h=112, fill="soft", dash="dashed").place(cv, 2010, by)
    connect(cv, user, agent, num=1, label="Responses API", num_theme="blue", label_dy=-20)
    connect(cv, agent, mcp, num=2, label="tool call", num_theme="blue", label_dy=-20)
    line_between(cv, mcp, conn, label="project_connection_id", label_size=14, label_wrap=170)

    # ---------------------------------------------------------------- lane B + C: Azure AI Search service
    ys = dy + la_h + 96
    with cv.panel(0, ys, title="Azure AI Search service (required)",
                  sub="hosts the knowledge base, the knowledge sources and the auto-generated ingestion objects",
                  theme="teal", style="dotted", w=LEFT_W, pad=24, title_size=26, sub_size=15) as ps:
        ky = ys + 92
        with cv.panel(24, ky, title="B   Knowledge base (Foundry IQ)",
                      sub="max 10 knowledge sources per KB on S1 and above; fewer on Free / Basic", theme="teal",
                      style="solid", fill="soft", w=LEFT_W - 48, pad=22, title_size=24, sub_size=15) as kb:
            r1 = ky + 100
            kbdef = Card(600, "KB definition", [
                "retrievalInstructions and answerInstructions",
                "outputMode: extractiveData | answerSynthesis",
                "models[]: Azure OpenAI deployment (planner / synthesizer)",
                "retrievalReasoningEffort: minimal | low (default) | medium | auto",
                "retrieveDefaults (preview): maxRuntimeInSeconds, maxOutputDocuments, maxOutputSizeInTokens",
                "encryptionKey (customer-managed key)",
                "per knowledge source: alwaysQuery flag + 'when to use me' guidance",
            ], theme="teal", fill="soft", icon="ai-search", icon_size=30, title_size=19, body_size=15)
            kbdef.place(cv, 46, ky + 92)
            dial(cv, 1150, ky + 36, 640, ["minimal", "low (default)", "medium", "auto (preview)"], 1,
                 label="retrievalReasoningEffort - how much LLM work the KB does")
            specs = [
                ("Plan", "KB LLM decomposes the question and picks sources (skipped at minimal)", 4, "KB LLM"),
                ("Fan out", "parallel subqueries: keyword / vector / hybrid on indexed, live calls on remote", 5, None),
                ("Semantic rerank", "'L3' rescoring of the candidates; one retry at medium effort", 6, None),
                ("Synthesize", "merged content always; answerSynthesis adds an LLM-written answer", 7, "KB LLM"),
            ]
            chev = []
            for i, (t, s, n, tag) in enumerate(specs):
                c = Chevron(364, t, s, theme="teal", first=(i == 0), num=n, tag=tag, h=CH)
                c.place(cv, 810 + i * 338, r1)
                chev.append(c)
            out = Box(262, "Output", sub="extractiveData or answerSynthesis, plus references and an activity log",
                      theme="teal", fill="soft", h=CH).place(cv, 810 + 4 * 338 - 8, r1)
            r2 = r1 + CH + 74
            with cv.panel(690, r2, title="Indexed knowledge sources",
                          sub="content copied into a search index you control", theme="teal", style="solid", fill="soft",
                          w=800, pad=20, title_size=21, sub_size=14) as pi:
                kinds = [("Search index (existing)", "ai-search", None), ("Azure Blob Storage + ADLS Gen2", "storage", None),
                         ("Azure SQL", "sql", "preview"), ("File (direct upload)", "file", "preview"),
                         ("OneLake", "onelake", None), ("SharePoint (indexed)", "sharepoint", "preview")]
                for i, (lab, ic, bd) in enumerate(kinds):
                    KS(372, lab, icon=ic, badge=bd).place(cv, pi.ix + (i % 2) * 392, pi.iy + (i // 2) * 50)
            with cv.panel(1520, r2, title="Remote knowledge sources",
                          sub="queried live, zero copy; no citation URLs", theme="teal", style="dashed", fill="none",
                          w=800, pad=20, title_size=21, sub_size=14) as pr:
                kinds = [("SharePoint (remote)", "sharepoint", "preview"), ("Web (Bing)", "bing", None),
                         ("MCP server", "mcp", "preview"), ("Fabric data agent", "fabric", "preview"),
                         ("Fabric ontology", "fabric", "preview"), ("Work IQ", "iq", "preview")]
                for i, (lab, ic, bd) in enumerate(kinds):
                    KS(372, lab, icon=ic, badge=bd, dash="dashed").place(cv, pr.ix + (i % 2) * 392, pr.iy + (i // 2) * 50)
        # ---- lane C inside the search service: the generated ingestion chain
        yc = kb.bottom + 64
        cv.text(46, yc - 44, "C   Ingest (indexed knowledge sources only): Search generates these four objects for you",
                size=22, color=get_theme("teal").deep)
        ds = Box(250, "Data source", sub="connection to your content", theme="cyan", h=108).place(cv, 60, yc)
        sk = Box(250, "Skillset", sub="chunk + embed (calls the embedding deployment)", theme="teal", h=108).place(cv, 420, yc)
        ix = Box(250, "Indexer", sub="on demand or scheduled (incremental refresh)", theme="teal", h=108).place(cv, 780, yc)
        idx = Box(250, "Index", sub="vector + text fields, permission metadata", theme="teal", h=108).place(cv, 1140, yc)
        connect(cv, ds, sk)
        connect(cv, sk, ix)
        connect(cv, ix, idx)
        numbered(cv, 40, yc - 44 + 14, "I2", theme="teal", d=36)
        numbered(cv, ix.x + 8, ix.y - 2, "I3", theme="teal", d=36)
        numbered(cv, idx.x + 8, idx.y - 2, "I4", theme="teal", d=36)
        Note(900, "Docs: Search generates the data source, skillset, indexer and index for each indexed knowledge source - do not edit them. "
                  "Schedule the indexer for incremental refresh.", kind="info", title="Auto-generated chain",
             src=[("Knowledge sources overview", learn("azure/search/agentic-knowledge-source-overview", base=""))]).place(cv, 1500, yc - 12)
    # ---------------------------------------------------------------- arrows 3 / 8 and the standalone path
    ax = mcp.cx
    ych = dy + la_h + (ys - dy - la_h) / 2
    arrow(cv, [(ax - 46, mcp.bottom + 6), (ax - 46, r1 - 8)], color="#1971c2", sw=3, num=3, num_theme="blue")
    arrow(cv, [(out.cx, out.y - 6), (out.cx, ych), (ax + 46, ych), (ax + 46, mcp.bottom + 6)], color="#1971c2", sw=3,
          dash="dashed", num=8, num_theme="blue", label="result: content + references", label_size=14, label_dy=-20)
    arrow(cv, [(app.x + app.w - 50, app.bottom + 6), (app.x + app.w - 50, ky - 4)], dash="dashed", color="#495057", sw=2.5)
    # fan-out arrows (double headed: subqueries out, candidates back)
    fx = chev[1].x + chev[1].w / 2
    ymid = r1 + CH + 34
    arrow(cv, [(fx - 30, r1 + CH + 4), (fx - 30, ymid), (pi.x + pi.w / 2 + 100, ymid), (pi.x + pi.w / 2 + 100, r2 - 4)],
          start_head="arrow", end_head="arrow", color="#099268", sw=3, label="subqueries out, candidates back", label_size=14,
          label_pos="below", label_dx=-150)
    arrow(cv, [(fx + 30, r1 + CH + 4), (fx + 30, ymid), (pr.x + pr.w / 2 - 100, ymid), (pr.x + pr.w / 2 - 100, r2 - 4)],
          start_head="arrow", end_head="arrow", color="#099268", sw=3, dash="dashed")
    arrow(cv, [(idx.cx, idx.y - 6), (idx.cx, pi.bottom + 4)], color="#099268", sw=3, num="I5", num_theme="teal",
          label="KB references the knowledge source", label_size=14, label_wrap=190)
    # ---------------------------------------------------------------- right column: Foundry + external systems
    fcard = Card(CW, "Foundry resource: KB LLM", [
        "Planner / synthesizer = an Azure OpenAI model deployed in the Foundry resource; not used at minimal effort",
        "The AI Search page lists GPT-5 family models and marks the gpt-4o and gpt-4.1 families deprecated",
        "! Docs disagree: the Foundry IQ FAQ lists a narrower, older model set - check before you choose",
        "Search system-assigned MI needs Cognitive Services User on the Foundry resource",
    ], theme="blue", icon="openai", src=[("Create a knowledge base", learn("azure/search/agentic-retrieval-how-to-create-knowledge-base", base=""))])
    fcard.place(cv, CX, r1 - 6)
    ecard = Card(CW, "External systems (remote sources)", [
        "SharePoint via the Microsoft Copilot Retrieval API: needs an M365 Copilot license or pay-as-you-go",
        "Web (Bing): real time, needs answerSynthesis, not available at minimal effort",
        "MCP server, Fabric data agent / ontology, Work IQ: delegated user identity",
    ], theme="gray", icon="api-connections", dash="dashed", src=[("Knowledge sources overview", learn("azure/search/agentic-knowledge-source-overview", base=""))])
    ecard.place(cv, CX, max(r2 - 4, fcard.bottom + 36))
    arrow(cv, [(kb.right + 6, fcard.y + 80), (CX - 6, fcard.y + 80)], dash="dashed", color="#1971c2", sw=3,
          label="plan + synthesize", label_size=14, label_wrap=120)
    arrow(cv, [(pr.right + 6, ecard.cy), (CX - 6, ecard.cy)], dash="dashed", color="#099268", sw=3, label="live calls",
          label_size=14)
    # ---------------------------------------------------------------- outside the search panel (below): data stores + embedding model
    yo = ps.bottom + 92
    stores = Box(380, "Your content stores", sub="Blob / ADLS Gen2, OneLake, SharePoint, Azure SQL, direct file upload, existing index",
                 theme="cyan", icon="storage", h=116).place(cv, 20, yo)
    emb = Box(380, "Embedding deployment in Foundry", sub="e.g. text-embedding-3-large; Search MI needs Cognitive Services User",
              theme="blue", icon="openai", h=116).place(cv, 470, yo)
    arrow(cv, [(stores.cx, stores.y - 6), (stores.cx, ds.bottom + 6)], color="#0c8599", sw=3, num="I1", num_theme="teal",
          label="create the source + choose options", label_size=14, label_wrap=150)
    arrow(cv, [(emb.cx, emb.y - 6), (emb.cx, sk.bottom + 6)], dash="dashed", color="#1971c2", sw=3, label="embeddings",
          label_size=14)
    return yo + 116


def _steps(cv: Canvas, y: float) -> float:
    q = Steps(1620, "Query path: how one question is answered (1-8)", [
        (1, "User -> agent endpoint", "Responses API call; the user's Entra identity is the caller identity."),
        (2, "The model decides to call the MCP tool", "knowledge_base_retrieve, bound to the project connection; allowed_tools is pinned to that one tool."),
        (3, "Agent Service -> KB MCP endpoint", "https://{search}.search.windows.net/knowledgebases/{kb}/mcp?api-version=... as the project managed identity (audience https://search.azure.com/). For a user caller it adds x-ms-query-source-authorization."),
        (4, "Query planning (KB LLM, skipped at minimal)", "Decomposes the question and chooses knowledge sources; each source carries 'when to use me' guidance and alwaysQuery forces one. Search system MI -> Foundry model (Cognitive Services User)."),
        (5, "Parallel subqueries", "Keyword / vector / hybrid on indexed sources; live calls on remote sources (SharePoint Copilot Retrieval API, Bing, MCP server, Fabric, Work IQ)."),
        (6, "Semantic ranking", "Candidates are reranked; 'L3' rescoring and one retry at medium effort."),
        (7, "Synthesis", "Merged content is always returned; answerSynthesis adds an LLM-written answer; optional references and activity log. Remote sources give no citation URLs."),
        (8, "KB -> agent over MCP", "The agent composes the final grounded answer. In extractiveData mode the agent's own model writes the prose."),
    ], theme="blue", num_theme="blue", head_w=400, src=[("Foundry IQ connect", learn("agents/how-to/foundry-iq-connect"))])
    q.place(cv, 0, y)
    ing = Steps(1620, "Ingestion path: indexed knowledge sources only (I1-I5)", [
        ("I1", "Create the knowledge source", "Blob / ADLS Gen2, OneLake, SharePoint (indexed), Azure SQL, direct file or an existing index; choose the embedding deployment and optional ingestion permission options."),
        ("I2", "Search auto-generates the chain", "data source -> skillset -> indexer -> index. The docs say do not edit these objects."),
        ("I3", "The indexer runs", "On demand or on a schedule for incremental refresh; embedding calls go to the Foundry embedding deployment (typical flow: crack, chunk, embed, write). In private mode the indexer runs with executionEnvironment: private over shared private links."),
        ("I4", "Permission metadata is stamped (preview)", "If ingestionPermissionOptions is set: ACL / RBAC scope / sensitivity label / SharePoint ACL metadata lands on the documents - it only reflects permissions already synced."),
        ("I5", "The KB exposes the source", "The KB references the knowledge source(s) and is exposed at the KB MCP endpoint."),
    ], theme="teal", num_theme="teal", head_w=400, src=[("Knowledge source (Blob) how-to", learn("azure/search/agentic-knowledge-source-how-to-blob", base=""))])
    ing.place(cv, 1680, y)
    n = Note(1620, "No Agent Service? App -> retrieve on the KB with the query + chat history; the app sets x-ms-query-source-authorization itself. "
                   "The docs read do not name the Search data-plane role the caller needs (Search Index Data Reader is an inference, not documented).",
             kind="tip", title="Standalone path (no Agent Service)", src=[("Foundry IQ FAQ", learn("agents/concepts/foundry-iq-faq"))])
    n.place(cv, 1680, ing.bottom + 22)
    return max(q.bottom, n.bottom)


def _security(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "Security trimming and identity wiring: who may see which chunk",
        sub="Zoom into steps 1, 3, 5 and 8 of the query path. Enforcement happens at retrieval time, inside Azure AI Search.",
        size=32)
    y0 = hb + 40
    # ---- column A: per-user sequence
    seq = Sequence(cv, 0, y0, [("End user", "gray", "users"), ("Agent Service", "green", "agent"),
                               ("KB MCP endpoint", "teal", "ai-search"), ("Search index", "cyan", "search")],
                   spacing=330, head_w=210, head_h=60, size=16, label_size=15)
    seq.msg(0, 1, "Responses API call as the signed-in user", num=1)
    seq.msg(1, 2, "MCP call as the project MI + header x-ms-query-source-authorization (user token for https://search.azure.com/.default)", num=3)
    seq.msg(2, 3, "subqueries with the per-user filter: security filter, ACL / RBAC scope, label or SharePoint ACL", num=5)
    seq.msg(3, 2, "only documents this user may see", dash="dashed")
    seq.msg(2, 1, "content + references (remote sources: no citation URLs)", dash="dashed", num=8)
    seq.msg(1, 0, "grounded answer composed by the agent", dash="dashed")
    seq.note(1, 2, "Caller is a user: Agent Service sets the header dynamically. Otherwise the app sets it explicitly with structured inputs and a {{search_auth_token}} placeholder in the MCP tool headers.", kind="info")
    seq.note(1, 3, "Token missing -> permission-enabled sources return results UNFILTERED (the docs' warning). Make the per-user header a design-review item.", kind="gotcha")
    sb = seq.end()

    # ---- column B: RBAC wiring
    xb, wb = 1290, 1000
    rb = Table(
        [("Principal", 230), ("Role", 290), ("Scope", 140), "Why"],
        [
            ["Foundry project managed identity", "Search Index Data Reader (Contributor only if writing)", "Azure AI Search",
             "The agent -> KB MCP call runs as the project MI"],
            ["Search service system-assigned MI", "Cognitive Services User", "Foundry resource",
             "KB planning / synthesis LLM call (only if the KB names an LLM) and the embedding calls"],
            ["Search service system-assigned MI", "Storage Blob Data Reader", "Storage account",
             "The blob indexer reads content (private tutorial, part 2)"],
            ["Caller creating the connection", "Foundry Project Manager", "Project", "Creates the RemoteTool project connection"],
            ["Caller using the connection / agent", "Foundry User (connect page); least-privilege 'invoke an agent endpoint' role = Foundry Agent Consumer", "Project", "Uses the agent"],
            ["End user (for trimming)", "Token for https://search.azure.com/.default in x-ms-query-source-authorization", "per request", "Per-user filter"],
        ], w=wb, theme="red", size=15, head_size=16, title=f"Identity and RBAC wiring ({AS_OF})", title_size=22,
        first_col_theme="red")
    rb.place(cv, xb, y0)
    cb = cites(cv, xb, rb.bottom + 8, [("Foundry IQ connect", learn("agents/how-to/foundry-iq-connect")),
                                       ("Private tutorial: outbound", learn("agents/how-to/foundry-iq-tutorial-private-outbound"))])
    n_pv = Note(wb, "Purview sensitivity-label extraction requires the Search service's system-assigned managed identity (user-assigned is not supported), "
                    "a Global Admin grant and a single tenant. Autocomplete and Suggest are then unavailable.", kind="info",
                title="Purview label extraction",
                src=[("Document-level access", learn("azure/search/search-document-level-access-overview", base=""))])
    n_pv.place(cv, xb, cb + 28)
    nk = Note(wb, "Prefer Entra ID over keys for Search and Foundry access; treat retrieved content as untrusted (prompt injection); "
                  "enforce access control at retrieval time; pin MCP allowed_tools.", kind="tip", title="Documented security guidance")
    nk.place(cv, xb, n_pv.bottom + 20)

    # ---- column C: document-level access approaches
    xc, wc = 2350, 950
    da = Table(
        [("Approach", 240), ("Status", 100), "How it works"],
        [
            [("Security filters", "teal"), ("GA", "green"), "String-match filter on a security field in the index; the app supplies the groups / ids"],
            [("POSIX-like ACLs / RBAC scopes", "teal"), ("Preview", "orange"), "ADLS Gen2 ACLs; blob RBAC scope at container level; stored through permissionFilter fields on the index"],
            [("Purview sensitivity labels", "teal"), ("Preview", "orange"), "Surfaced as sensitivityLabelInfo / responseSensitivityLabelInfo; encrypted labelled documents need Purview integration to be indexed (video)"],
            [("SharePoint ACLs", "teal"), ("Preview", "orange"), "Inherited-permission changes need an explicit refresh; unique-permission changes sync incrementally from 2026-05-01-preview"],
        ], w=wc, theme="teal", size=15, head_size=16, title="Document-level access: four approaches (AI Search)", title_size=22)
    da.place(cv, xc, y0)
    cc = cites(cv, xc, da.bottom + 8, [("Document-level access", learn("azure/search/search-document-level-access-overview", base=""))])
    nw = Note(wc, "Enforcement only reflects permissions after they are synced to the index (a lag window). SharePoint inherited-permission changes need an explicit refresh.",
              kind="warn", title="Permission sync is eventual")
    nw.place(cv, xc, cc + 28)
    ng = Note(wc, "ingestionPermissionOptions (ACL / RBAC scope / sensitivityLabel, preview) is incompatible with assetStore / image serving.",
              kind="gotcha", title="Option conflict")
    ng.place(cv, xc, nw.bottom + 20)
    return max(sb, nk.bottom, ng.bottom)


def _private(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "Private variant: private agentic retrieval (the 3-part Foundry tutorial)",
        sub="Template 15-private-network-standard-agent-setup, example region westus3. Ingestion-time embeddings still need the trusted-services bypass.",
        size=32)
    y0 = hb + 36
    with cv.panel(0, y0, title="Your virtual network", sub="tutorial example 10.42.0.0/16; subnets and private DNS zones come from the template",
                  theme="indigo", style="dotted", w=900, pad=22, title_size=26, sub_size=14) as vn:
        with cv.panel(vn.ix, vn.iy, title="agent-subnet (/24)", sub="delegated to Microsoft.App/environments", theme="indigo",
                      style="solid", fill="soft", w=410, pad=16, title_size=20, sub_size=14) as sa:
            ag = Box(378, "Agent Service (network-injected)", sub="reaches resources over private endpoints",
                     theme="green", icon="agent", icon_pos="left", h=82).place(cv, sa.ix, sa.iy)
        with cv.panel(vn.ix + 440, vn.iy, title="Bastion (/26) + test client", sub="optional mcp-subnet for private MCP servers",
                      theme="indigo", style="solid", fill="soft", w=410, pad=16, title_size=20, sub_size=14) as sc:
            cl = Box(378, "Test client inside the VNet", sub="validate from here, e.g. via Bastion", theme="gray",
                     icon="bastion", icon_pos="left", h=82).place(cv, sc.ix, sc.iy)
        py_ = max(sa.bottom, sc.bottom) + 28
        with cv.panel(vn.ix, py_, title="pe-subnet (/24)", sub="private endpoints; private DNS zones link them to the VNet", theme="indigo",
                      style="solid", fill="soft", w=856, pad=16, title_size=20, sub_size=14) as sp:
            Card(400, "Private DNS zones", [
                "Created by the template and linked to the VNet",
                "Zone list: see the Baseline network-isolated reference architecture canvas",
            ], theme="indigo", fill="soft", icon="dns", icon_size=30, title_size=18, body_size=15).place(cv, sp.ix, sp.iy + 2)
            pes = []
            for i, (lab, sub_) in enumerate([("PE: Foundry account", "models + project"), ("PE: Azure AI Search", "KB MCP endpoint"),
                                             ("PE: Storage (blob)", "content for the indexer"), ("PE: Cosmos DB, ACR", "standard agent setup")]):
                pes.append(Box(380, lab, sub=sub_, theme="indigo", icon="private-endpoint", icon_pos="left", h=70,
                               fill="solid").place(cv, sp.ix + 434, sp.iy + 2 + i * 100))
    px = vn.right + 200
    foundry = Box(500, "Foundry resource + project", sub="embedding + GPT-5-family deployments; networkAcls.bypass = AzureServices stays on",
                  theme="blue", icon="foundry", icon_pos="left", h=84).place(cv, px, pes[0].cy - 42)
    search = Box(500, "Azure AI Search", sub="RBAC enabled + system-assigned MI; private mode needs S2 / S3 / L1 / L2",
                 theme="teal", icon="ai-search", icon_pos="left", h=84).place(cv, px, pes[1].cy - 42)
    storage = Box(500, "Storage account", sub="blob content; Search MI = Storage Blob Data Reader", theme="cyan",
                  icon="storage", icon_pos="left", h=84).place(cv, px, pes[2].cy - 42)
    other = Box(500, "Cosmos DB + ACR", sub="agent state and images in the standard agent setup", theme="cyan",
                icon="cosmos", icon_pos="left", h=84).place(cv, px, pes[3].cy - 42)
    for pe, tgt in zip(pes, (foundry, search, storage, other)):
        line_between(cv, pe, tgt)
    numbered(cv, vn.right - 40, sp.y + 6, 1, theme="indigo", d=34)
    numbered(cv, cl.x + 8, cl.y - 6, 3, theme="indigo", d=34)
    ox = px + 500 + 70
    arrow(cv, [(search.right + 6, search.cy - 20), (ox, search.cy - 20), (ox, foundry.cy), (foundry.right + 6, foundry.cy)],
          color="#3b5bdb", sw=3.5, dash="dashed", num=2, num_theme="indigo",
          label="shared private link: openai_account (Search -> Foundry)", label_size=14, label_wrap=190, label_pos="right")
    arrow(cv, [(search.right + 6, search.cy + 20), (ox, search.cy + 20), (ox, storage.cy), (storage.right + 6, storage.cy)],
          color="#3b5bdb", sw=3.5, dash="dashed", num=2, num_theme="indigo",
          label="shared private link: blob (Search -> Storage)", label_size=14, label_wrap=190, label_pos="right")
    nb = Note(900, "Foundry networkAcls.bypass = AzureServices ('Allow Azure services on the trusted services list') must stay on for ingestion-time embedding "
                   "calls, otherwise 403 Public access is disabled.", kind="warn", title="Trusted-services bypass still needed",
              src=[("Private tutorial: retrieval", learn("agents/how-to/foundry-iq-tutorial-private-retrieval"))])
    nb.place(cv, px, y0)
    nd = Note(900, "The tutorial relies on the trusted-services bypass for ingestion-time embeddings, while the blob knowledge-source page documents full "
                   "networkAccessMode: private (create-time only; S2 / S3 / L1 / L2; indexed OneLake has no private sync). The docs do not reconcile the two - verify in your environment.",
              kind="gotcha", title="Docs disagree: how private is private?",
              src=[("Blob knowledge source", learn("azure/search/agentic-knowledge-source-how-to-blob", base=""))])
    nd.place(cv, px, nb.bottom + 20)
    # ---- tutorial steps (right)
    SX = 2060
    st = Steps(1240, "Tutorial: three parts", [
        (1, "Inbound: private endpoints and DNS", "Deploy the template: VNet 10.42.0.0/16, agent-subnet /24, pe-subnet /24, optional mcp-subnet, Bastion /26. It creates Foundry + project, Search, Storage, Cosmos DB, ACR, private endpoints and private DNS zones. Resource providers: CognitiveServices, MachineLearningServices, App, ContainerService, ContainerRegistry, Network, Search, Storage, DocumentDB."),
        (2, "Outbound: shared private links from Search", "Search -> Storage (blob) and Search -> Foundry (openai_account; ARM API 2025-05-01). The az search shared-private-link-resource create CLI can reject openai_account, so use az rest. Then approve each pending private-endpoint connection on the target (the Foundry one can take a minute or two to appear). Search needs RBAC enabled and a system-assigned MI."),
        (3, "Validate from a client inside the VNet", "Deploy text-embedding-3-large and a GPT-5-family model; create the azureBlob knowledge source and the KB (outputMode extractiveData, retrievalReasoningEffort minimal), the RemoteTool connection and the agent. Part 1 succeeds when Foundry and Search resolve to private IPs and accept TCP 443; part 3 when the prompt returns an answer grounded in your blob content with citations."),
    ], theme="indigo", num_theme="indigo", head_w=300,
        src=[("Tutorial overview", learn("agents/how-to/foundry-iq-tutorial-private-overview")),
             ("Part 1: inbound", learn("agents/how-to/foundry-iq-tutorial-private-inbound"))])
    st.place(cv, SX, y0)
    ops = Card(1240, "Operator permissions and troubleshooting", [
        "Contributor / Owner on Search to create the links; Contributor / Owner on Storage and Foundry to approve them",
        "Owner, User Access Administrator or RBAC Administrator to make the role assignments",
        "Search roles: Storage Blob Data Reader (storage) + Cognitive Services User (Foundry)",
        "! Link stuck Pending = not approved on the target; creation fails = wrong resource ID, group ID or API version",
        "! A subscription policy that forces local-auth-disabled Search can deny the sample template: pre-create Search and pass aiSearchResourceId",
    ], theme="red", icon="key-vault", title_size=19, body_size=15)
    ops.place(cv, SX, st.bottom + 22)
    return max(nd.bottom, ops.bottom, vn.bottom)


def _options(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "Which retrieval option? Foundry IQ knowledge base, Azure AI Search tool or file search",
        sub="The classic alternatives still work. The decision follows how many sources you ground on, whether you need per-user trimming and how much plumbing you want.",
        size=32)
    y0 = hb + 40
    start = Box(560, "Start: the agent must answer from your content", theme="gray", h=62).place(cv, 40, y0)
    q1 = Box(560, "Several sources, per-user trimming, cross-source reasoning, or one KB reused by many agents?",
             theme="yellow", shape="diamond", h=210, size=16).place(cv, 40, y0 + 112)
    kbbox = Box(400, "Foundry IQ knowledge base", sub="MCP tool knowledge_base_retrieve; up to 10 sources, 12 kinds", theme="teal",
                icon="iq", icon_pos="left", h=100).place(cv, 690, q1.cy - 50)
    q2 = Box(560, "You already own one good index and want the simplest hookup?", theme="yellow", shape="diamond", h=190,
             size=16).place(cv, 40, q1.bottom + 64)
    aitool = Box(400, "Azure AI Search tool", sub="ONE index; hybrid + semantic by default", theme="cyan", icon="ai-search",
                 icon_pos="left", h=100).place(cv, 690, q2.cy - 50)
    fs = Box(400, "File search (vector store)", sub="quick document Q&A and ad-hoc uploads", theme="blue", icon="file",
             icon_pos="left", h=100).place(cv, 120, q2.bottom + 56)
    connect(cv, start, q1, a_side="bottom", b_side="top")
    connect(cv, q1, kbbox, a_side="right", label="yes", label_size=17)
    connect(cv, q1, q2, a_side="bottom", b_side="top", label="no", label_size=17, label_pos="right")
    connect(cv, q2, aitool, a_side="right", label="yes", label_size=17)
    connect(cv, q2, fs, a_side="bottom", b_side="top", label="no", label_size=17, label_pos="right")

    tx = 1200
    t = Table(
        [("Dimension", 190), ("Foundry IQ KB (MCP knowledge_base_retrieve)", 640), ("Azure AI Search tool", 640), ("File search (vector store)", 630)],
        [
            ["Scope", "Multiple sources (<= 10 per KB), 12 kinds, reusable across agents", "ONE index per tool",
             "Files in a vector store: <= 10,000 files; 1 vector store per agent + 1 per conversation"],
            ["Retrieval", "LLM planning + parallel subqueries + semantic rerank (effort levels)",
             "query_type defaults to vector_semantic_hybrid, top_k defaults to 5, optional filter",
             "Chunks of 800 with 400 overlap, text-embedding-3-large at 256 dims, max 20 chunks in context"],
            ["Index requirement", "Generated for you (indexed sources) or yours", "Needs a vector field, a searchable text field and a retrievable source-URL field", "Managed for you"],
            ["Identity", "Project MI (+ per-user token for trimming)",
             "Project MI. A private VNet requires project-MI auth (no keys), same tenant; keyless roles = Search Index Data Contributor + Search Service Contributor on the Foundry account's system-assigned MI",
             "Platform. Basic setup = Microsoft-managed storage + search; standard setup = your Blob + AI Search"],
            ["Network isolation", "Yes: shared private links and private endpoints", "Yes: project-MI auth",
             "Basic: Microsoft-managed. 'Blob + file search' is not supported on the BYO-VNet page; recreate vector stores when a VNet is enabled without BYO"],
            ["Limits", "Per-tier limits table; max 10 sources per KB", "One index",
             "File <= 512 MB and <= 5M tokens; batches <= 500 files; conversation vector stores expire after 7 days idle; 60 s wait fallback for conversation stores"],
            ["Use when", "Multi-source, per-user trimming, cross-source reasoning, one KB reused by many agents",
             "You already have a single good index and want the simplest hookup", "Quick document Q&A or ad-hoc uploads"],
        ], w=2100, theme="teal", size=15, head_size=16, first_col_theme="teal",
        title=f"Three retrieval paths compared ({AS_OF})", title_size=22)
    t.place(cv, tx, y0)
    cb = cites(cv, tx, t.bottom + 8, [("File search tool", learn("agents/how-to/tools/file-search")),
                                      ("Vector stores", learn("agents/concepts/vector-stores")),
                                      ("Azure AI Search tool", learn("agents/how-to/tools/ai-search")),
                                      ("Retrieval-augmented generation", learn("concepts/retrieval-augmented-generation"))], max_w=2100)
    cv.text(tx, cb + 6, "GA / preview status labels for file search and the Azure AI Search tool were not captured here - check the docs.",
            size=14, color=MUTED)
    return max(fs.bottom, cb + 30)


def _tables(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "Reference tables: knowledge-source kinds, reasoning effort, limits and how the agent is wired",
        sub=f"All values as documented on the linked Learn pages ({AS_OF}).", size=32)
    y0 = hb + 36
    P = ("Preview", "orange")
    ks = Table(
        [("Kind", 250), ("Mode", 100), ("Status", 105), "Notes"],
        [
            [("Search index (existing)", "teal"), "Indexed", "-", "Wrap an index you already own"],
            [("Azure Blob Storage (+ ADLS Gen2)", "teal"), "Indexed", "-", "Auto-generates data source / skillset / indexer / index; ACL / RBAC-scope ingestion and networkAccessMode: private are preview options"],
            [("Azure SQL", "teal"), "Indexed", P, ""],
            [("File (direct upload)", "teal"), "Indexed", P, ""],
            [("OneLake", "teal"), "Indexed", "-", "Indexed OneLake does not support private sync"],
            [("SharePoint (indexed)", "teal"), "Indexed", P, "SharePoint ACLs can be ingested (preview)"],
            [("SharePoint (remote)", "teal"), "Remote", P, "Via the Microsoft Copilot Retrieval API; needs an M365 Copilot license or pay-as-you-go; no citation URLs"],
            [("Fabric data agent", "teal"), "Remote", P, "Fabric -> Foundry grounding. The separate Fabric data agent tool is flagged for deprecation on Nov 6, 2026 - check this kind's status"],
            [("Fabric ontology", "teal"), "Remote", P, ""],
            [("MCP server", "teal"), "Remote", P, ""],
            [("Work IQ", "teal"), "Remote", P, "Needs a delegated user identity"],
            [("Web (Bing)", "teal"), "Remote", "-", "Real time; requires answerSynthesis (FAQ); not available at minimal effort"],
        ], w=1100, theme="teal", size=15, head_size=16, title="12 knowledge-source kinds (6 indexed, 6 remote)", title_size=22)
    ks.place(cv, 0, y0)
    kn = Note(1100, "'-' = no preview label noted on the AI Search overview. GA coverage per kind on the 2026-04-01 surface was not captured - check the docs. "
                    "The Foundry IQ FAQ shows a shorter list (indexed: Blob, OneLake, SharePoint, search index; remote: SharePoint, web); the AI Search overview's 12 kinds are used here.",
              kind="info", title="Reading the status column",
              src=[("Knowledge sources overview", learn("azure/search/agentic-knowledge-source-overview", base=""))])
    kn.place(cv, 0, ks.bottom + 20)

    x2, w2 = 1160, 1060
    ef = Table(
        [("Effort", 140), ("LLM in KB?", 120), "Limits and behaviour"],
        [
            [("minimal", "teal"), CROSS, "outputMode must be extractiveData; <= 10 sources; no answer synthesis; no web source; available on the GA API (2026-04-01)"],
            [("low (default)", "teal"), CHECK, "<= 3 sources and <= 3 subqueries; 5,000 answer tokens; 50 docs to semantic ranking (10 for the 'L3' stage)"],
            [("medium", "teal"), CHECK, "<= 5 sources / subqueries; iterative search (one retry driven by a semantic classifier; 'L3' rescoring on a 0-4.0 scale); 10,000 answer tokens; select regions only"],
            [("auto", "teal"), CHECK, "Preview, 2026-08-01-preview only (needs a model); errors on older API versions"],
        ], w=w2, theme="teal", size=15, head_size=16, title="Retrieval reasoning effort (default low)", title_size=22)
    ef.place(cv, x2, y0)
    en = Note(w2, f"Medium effort, only in these 15 regions ({AS_OF}): East US 2, East US, South Central US, West US 3, West US 2, West US, Germany West Central, "
                  "North Europe, Switzerland North, Sweden Central, Spain Central, UK South, Korea Central, Japan East, Southeast Asia.",
              kind="warn", title="Regional availability of medium",
              src=[("Set the retrieval reasoning effort", learn("azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort", base=""))])
    en.place(cv, x2, ef.bottom + 18)
    lm = Table(
        [("Tier", 190), ("Knowledge sources / service", 280), ("KBs / service", 240), "Sources per KB"],
        [
            [("Free", "yellow"), "3", "3", "3"],
            [("Basic", "yellow"), "5 or 15", "5 or 15", "5 or 10 (older services lower)"],
            [("S1", "yellow"), "50", "50", "10"],
            [("S2 / S3", "yellow"), "200", "200", "10"],
            [("S3 HD", "yellow"), "1,000 per partition / 3,000 per service", "same", "10"],
            [("L1 / L2", "yellow"), "10", "10", "10"],
            [("Serverless Developer", "yellow"), "30", "30", "10"],
        ], w=w2, theme="yellow", size=15, head_size=16, title=f"Azure AI Search limits for agentic retrieval ({AS_OF})", title_size=22)
    lm.place(cv, x2, en.bottom + 36)
    cites(cv, x2, lm.bottom + 8, [("Search limits and quotas", learn("azure/search/search-limits-quotas-capacity", base=""))])

    x3, w3 = 2280, 1020
    wire = Card(w3, "Wiring the agent to the KB", [
        "# Project connection (ARM API 2025-10-01-preview)",
        "category RemoteTool, authType ProjectManagedIdentity, isSharedToAll true, metadata.ApiType Azure",
        "target https://{search}.search.windows.net/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview",
        "audience https://search.azure.com/",
        "# MCP tool on the agent",
        "type mcp, server_label knowledge-base, allowed_tools [knowledge_base_retrieve], require_approval never, project_connection_id",
        "Agent created with POST {project_endpoint}/agents?api-version=v1; SDK azure-ai-projects >= 2.0.0 (Python; REST also shown)",
        "! Hub-based projects are not supported",
    ], theme="orange", icon="mcp", title_size=20, body_size=15, src=[("Connect Foundry IQ", learn("agents/how-to/foundry-iq-connect"))])
    wire.place(cv, x3, y0)
    bill = Card(w3, f"How agentic retrieval is billed ({AS_OF})", [
        "Billed in tokens: AI Search retrieval tokens (subquery execution + semantic ranking; free monthly allowance, then pay-as-you-go)",
        "plus Azure OpenAI tokens for planning and synthesis",
        "Worked example on the page: about $4.32 for 2,000 retrievals (illustrative, gpt-4o-mini rates)",
        "Cost levers: fewer sources, lower effort (minimal uses no LLM tokens), curated content, a right-sized Search tier",
    ], theme="yellow", icon="cost-management", title_size=20, body_size=15,
        src=[("Agentic retrieval overview", learn("azure/search/agentic-retrieval-overview", base=""))])
    bill.place(cv, x3, wire.bottom + 24)
    mode = Card(w3, "Who writes the answer? (FAQ guidance)", [
        "Use extractive data for agents - the agent's model writes the answer",
        "Use answer synthesis for standalone apps; it is required for web sources",
        "FAQ cites ~36% higher response quality than single-shot RAG (vendor benchmark via a Tech Community post - blog-sourced, not in Learn)",
    ], theme="teal", icon="iq", title_size=20, body_size=15, src=[("Foundry IQ FAQ", learn("agents/concepts/foundry-iq-faq"))])
    mode.place(cv, x3, bill.bottom + 24)
    return max(kn.bottom, lm.bottom + 30, mode.bottom)


def _eval(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "RAG recap and evaluation: from classic RAG to agentic retrieval",
        sub="Architecture Center design guidance plus the Foundry RAG evaluators. Measure retrieval quality and answer quality separately.",
        size=32)
    y0 = hb + 36
    LW = 1700
    cv.text(0, y0, "Classic RAG app flow", size=21, color=get_theme("blue").deep)
    ya = y0 + 36
    ui = Box(230, "User / UI", theme="gray", icon="users", h=92).place(cv, 0, ya)
    orch = Box(330, "Orchestrator", sub="Agent Framework, Semantic Kernel, Agent Service or LangChain", theme="green", icon="agent", h=92).place(cv, 330, ya)
    srch = Box(250, "Azure AI Search", sub="retrieve top-N results", theme="teal", icon="ai-search", h=92).place(cv, 770, ya)
    llm = Box(290, "LLM", sub="top-N results packaged into the prompt", theme="blue", icon="openai", h=92).place(cv, 1110, ya)
    ans = Box(210, "Grounded answer", theme="gray", h=92).place(cv, 1490, ya)
    connect(cv, ui, orch, num=1, num_theme="blue")
    connect(cv, orch, srch, num=2, num_theme="blue")
    connect(cv, srch, llm, num=3, num_theme="blue")
    connect(cv, llm, ans, num=4, num_theme="blue")
    yb = ya + 92 + 40
    cv.text(0, yb, "Data pipeline (ingestion)", size=21, color=get_theme("cyan").deep)
    yb += 36
    for i, lab in enumerate(["Source media", "Chunk", "Enrich", "Embed", "Persist in the index"]):
        Chevron(340, lab, "", theme="cyan" if i < 4 else "teal", first=(i == 0), h=64, size=20).place(cv, i * 308, yb)
    yc = yb + 64 + 40
    cv.text(0, yc, "Design and evaluation ladder (Architecture Center RAG guide)", size=21, color=get_theme("violet").deep)
    yc += 36
    steps = [("Preparation", ""), ("Chunking", ""), ("Enrichment", ""), ("Embedding", ""), ("Retrieval", ""),
             ("LLM evaluation", "groundedness, completeness, utilization, relevancy")]
    for i, (lab, sub) in enumerate(steps):
        Chevron(300, lab, sub, theme="violet", first=(i == 0), h=96, size=19, sub_size=14).place(cv, i * 270, yc)
    t_exp = cv.text(0, yc + 96 + 14, "Experiment harness named in the guide: microsoft/rag-experiment-accelerator (GitHub)", size=15, color=LINK,
                    link="https://github.com/microsoft/rag-experiment-accelerator")
    cb = cites(cv, 0, t_exp.bottom + 6, [("RAG solution design and evaluation guide", learn("azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide", base=""))])
    ag = Card(1100, "When to go agentic (Architecture Center)", [
        "Multistep reasoning, dynamic source selection, query decomposition, iterative refinement, retrieval + action",
        "Guardrails given: keep tools < 20; iteration limit 5-10",
        "Expect ~8-15 s latency versus ~2-3 s for classic RAG",
        "Evaluate tool-selection accuracy, retrieval efficiency, latency and cost per request",
    ], theme="green", icon="agent", title_size=20, body_size=15,
        src=[("Agentic RAG", learn("azure/architecture/ai-ml/guide/rag/rag-agentic", base=""))])
    ag.place(cv, 0, cb + 28)

    ev = Table(
        [("Evaluator", 230), ("Measures", 430), "Notes"],
        [
            [("Document Retrieval", "violet"), "Fidelity, NDCG, XDCG, Max Relevance, Holes", "Needs relevance labels (retrieval_ground_truth / qrels); supports parameter sweeps, e.g. top-k and chunking"],
            [("Retrieval", "violet"), "Quality of the retrieved context for the query", ""],
            [("Groundedness", "violet"), "Is the response supported by the context", ""],
            [("Groundedness Pro", "violet"), "Same, powered by Azure AI Content Safety", ("Preview", "orange")],
            [("Relevance", "violet"), "Does the response address the query", ""],
            [("Response Completeness", "violet"), "Does the response cover the ground truth", ("Preview", "orange")],
        ], w=1500, theme="violet", size=15, head_size=16, title="Foundry RAG evaluators", title_size=22)
    ev.place(cv, 1800, y0)
    en2 = Note(1500, "Scores are 1-5 with a default pass threshold of 3. Inputs used across them: query, response, context, ground_truth, retrieval_ground_truth, retrieved_documents.",
               kind="info", title="Scoring", src=[("RAG evaluators", learn("concepts/evaluation-evaluators/rag-evaluators"))])
    en2.place(cv, 1800, ev.bottom + 20)
    nn = Note(1500, "Retrieval quality and answer quality fail differently: run Document Retrieval with labelled data to sweep top-k and chunking, then Groundedness and Relevance on the final answers.",
              kind="tip", title="How to use them together")
    nn.place(cv, 1800, en2.bottom + 20)
    return max(ag.bottom, nn.bottom)


def _dials(cv: Canvas, y: float) -> float:
    _, hb = section_header(
        cv, 0, y, "Choose your dials, and the Well-Architected view",
        sub="Trade-offs as documented; where the docs give no number, none is shown.", size=32)
    y0 = hb + 36
    dl = Table(
        [("Decision", 200), ("Option A", 440), ("Option B", 520), ("Documented guidance and trade-off", 700)],
        [
            [("Who writes the answer", "teal"), "extractiveData: the agent's model writes it", "answerSynthesis: the KB's LLM writes it",
             "FAQ: extractive for agents, synthesis for standalone apps; synthesis is required for web sources; minimal forces extractive"],
            [("How hard to think", "teal"), "minimal: no LLM, GA API, cheapest, <= 10 sources", "low (default) -> medium (iterative, select regions) -> auto (preview)",
             "More effort = better multi-hop recall but more tokens and latency; medium is limited to 15 regions"],
            [("Indexed or remote source", "teal"), "Indexed: you control the index, schedules, ACL sync and citations", "Remote: live, no ingestion, no citation URLs, delegated permissions",
             "Remote for freshness and zero copy; indexed for control and trimming"],
            [("How many sources", "teal"), "Few curated sources", "Many sources", "More sources -> more subqueries and tokens; low allows <= 3 sources and <= 3 subqueries, medium <= 5"],
            [("Network posture", "teal"), "Public endpoints (simplest)", "Private: shared private links, S2+ / L tier, create-time only, trusted-bypass dependency",
             "networkAccessMode cannot be changed after creation"],
            [("Call path", "teal"), "Agent through the MCP project connection", "Any app through the KB REST API / SDK (no Agent Service)", "The same KB can serve both"],
        ], w=2060, theme="teal", size=15, head_size=16, title="Design decisions: choose your dials", title_size=22)
    dl.place(cv, 0, y0)
    waf = Table(
        [("Pillar", 170), "Documented guidance"],
        [
            [("Security", "red"), "Entra ID over keys; treat retrieved content as untrusted (prompt injection); enforce access control at retrieval time; pin MCP allowed_tools; optional KB encryptionKey (CMK); PEs + shared private links; Purview labels need a system-assigned Search MI"],
            [("Cost", "yellow"), "Token-based billing (Search retrieval tokens + Azure OpenAI tokens); fewer sources, lower effort, curated content; free monthly allowance; right-size the Search tier (private mode needs S2+ / L)"],
            [("Reliability", "blue"), "Scheduled indexers for incremental refresh; permission-sync lag; medium effort only in 15 regions; per-tier limits; no HA / DR numbers for Foundry IQ were found on the pages read - check the docs"],
            [("Operations", "violet"), "Pin the API version (GA vs preview); IaC template 15-private-network-standard-agent-setup; activity log in the retrieve response; RAG evaluators + rag-experiment-accelerator"],
            [("Performance", "green"), "Classic ~2-3 s vs agentic ~8-15 s; effort levels bound subqueries (3 vs 5), answer tokens (5,000 vs 10,000) and rerank doc counts; keep tools < 20 and iterations 5-10"],
        ], w=1180, theme="gray", size=15, head_size=16, title="Well-Architected view (as documented)", title_size=22)
    waf.place(cv, 2120, y0)
    return max(dl.bottom, waf.bottom)


def _gotchas(cv: Canvas, y: float) -> float:
    _, hb = section_header(cv, 0, y, "Gotchas and things the docs leave open", sub="Read these before your design review.", size=32)
    y0 = hb + 36
    nw = 1060
    notes = [
        Note(nw, "On permission-enabled sources a missing x-ms-query-source-authorization token returns results unfiltered (docs' warning). Make the per-user header an explicit design-review item.",
             kind="gotcha", title="Missing user token = no trimming"),
        Note(nw, "2026-04-01 = GA (minimal / extractive only). 2026-08-01-preview = planning, synthesis, multi-turn, preview sources. The portals emit preview-only schemas - plan a migration.",
             kind="preview", title="Two API surfaces"),
        Note(nw, "Remote knowledge sources return no citation URLs. If you need citations, ingest (index) the content instead.",
             kind="warn", title="Remote sources: no citations"),
        Note(nw, "Tutorial: ingestion-time embeddings still rely on the Foundry trusted-services bypass (else 403 Public access is disabled). Blob knowledge-source page: full networkAccessMode: private "
                 "(create-time only; S2 / S3 / L1 / L2). Not reconciled - verify.",
             kind="gotcha", title="Docs disagree: private ingestion"),
        Note(nw, "A subscription policy that forces local-auth-disabled Search can deny the sample template - pre-create Search and pass aiSearchResourceId.",
             kind="gotcha", title="Policy collision"),
        Note(nw, "allowed_tools supports only knowledge_base_retrieve; hub-based projects are not supported; the SDK sample is Python (azure-ai-projects >= 2.0.0) plus REST.",
             kind="warn", title="One tool, no hub projects"),
        Note(nw, "Conversation vector stores expire after 7 days idle; the BYO-VNet page says Blob + file search is unsupported; recreate vector stores when a VNet is enabled without BYO.",
             kind="warn", title="File search caveats"),
        Note(nw, "The AI Search page lists GPT-5 family models and marks the gpt-4o and gpt-4.1 families deprecated; the Foundry IQ FAQ lists a narrower, older set.",
             kind="gotcha", title="Docs disagree: KB model list"),
        Note(nw, "A quickstart 'Add Foundry IQ with a toolbox' exists for hosted agents (agents/quickstarts/quickstart-foundry-iq-hosted-agent); it was not read for this canvas - check the page.",
             kind="info", title="Hosted agents route"),
    ]
    _, b = grid(cv, 0, y0, notes, 3, gap_x=60, gap_y=24)
    return b


def _sources(cv: Canvas, y: float) -> float:
    r = sources(cv, 0, y, [
        ("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
        ("Foundry IQ FAQ", learn("agents/concepts/foundry-iq-faq")),
        ("Connect Foundry IQ to an agent", learn("agents/how-to/foundry-iq-connect")),
        ("Private agentic retrieval tutorial (overview)", learn("agents/how-to/foundry-iq-tutorial-private-overview")),
        ("Private tutorial part 2: outbound shared private links", learn("agents/how-to/foundry-iq-tutorial-private-outbound")),
        ("Agentic retrieval overview (Azure AI Search)", learn("azure/search/agentic-retrieval-overview", base="")),
        ("Knowledge sources overview", learn("azure/search/agentic-knowledge-source-overview", base="")),
        ("Set the retrieval reasoning effort", learn("azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort", base="")),
        ("Create a knowledge base", learn("azure/search/agentic-retrieval-how-to-create-knowledge-base", base="")),
        ("Document-level access control", learn("azure/search/search-document-level-access-overview", base="")),
        ("Azure AI Search limits and quotas", learn("azure/search/search-limits-quotas-capacity", base="")),
        ("File search tool", learn("agents/how-to/tools/file-search")),
        ("Azure AI Search tool", learn("agents/how-to/tools/ai-search")),
        ("RAG evaluators", learn("concepts/evaluation-evaluators/rag-evaluators")),
        ("RAG solution design and evaluation guide", learn("azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide", base="")),
        ("Agentic RAG (Architecture Center)", learn("azure/architecture/ai-ml/guide/rag/rag-agentic", base="")),
        ("Ignite 2025 BRK196, Foundry IQ (video, not Learn)", "https://www.youtube.com/watch?v=slDdNIQCJBQ"),
        ("Foundry IQ: boost response relevance by 36% (Tech Community blog, not Learn)",
         "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-boost-response-relevance-by-36-with-agentic-retrieval/4470720"),
    ], w=W, cols=3)
    return r.bottom


def build(cv: Canvas) -> None:
    y = _title(cv)
    y = _key_messages(cv, y + 20) + GAP
    y = _main_diagram(cv, y) + GAP
    y = _steps(cv, y) + GAP
    y = _security(cv, y) + GAP
    y = _private(cv, y) + GAP
    y = _options(cv, y) + GAP
    y = _tables(cv, y) + GAP
    y = _eval(cv, y) + GAP
    y = _dials(cv, y) + GAP
    y = _gotchas(cv, y) + GAP
    _sources(cv, y)
