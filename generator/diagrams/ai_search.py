"""Azure AI Search as the knowledge layer behind Foundry agents: Foundry IQ knowledge bases, agentic retrieval, classic indexes."""
from __future__ import annotations

from generator.xd import *
from generator.xd.blocks import SAFETY
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="ai-search", title="Azure AI Search: the knowledge layer", section="7", order=1,
    description="Foundry IQ knowledge bases on Azure AI Search: knowledge sources, agentic retrieval, classic indexes, the three ways agents use search content, identity, networking, trimming, tiers and billing.",
    tags=["ai-search", "foundry-iq", "agentic-retrieval", "knowledge-base", "rag"],
)

W = 3360          # canvas content width
GAP = 48          # standard gap between cards
ASOF = "as of 2026-11-03"
SRC = "azure/search/"


def S(path: str) -> str:
    """Azure AI Search Learn page."""
    return learn(SRC + path, base="")


# ---------------------------------------------------------------------------------------------- local helpers
class Spot(Rect2):
    """Invisible anchor rectangle for connectors."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


def badge_w(kind: str, size=13) -> float:
    _, label = STATUS.get(kind, ("gray", kind))
    return metrics.line_width(label, size) + 18


def stamp(cv, blk, kind, dx=-14, dy=-12) -> None:
    """GA / Preview sticker overlapping the top-right corner of a placed block."""
    draw_badge(cv, blk.right - badge_w(kind) + dx + 14, blk.y + dy, kind)


class Pill(Rect2):
    """Rounded label with optional icon and a GA / Preview sticker (dashed outline when preview)."""

    def __init__(self, w, label, *, badge=None, theme="teal", icon=None, size=16, h=42, pad=10, icon_size=26):
        self.th = get_theme(theme)
        self.w, self.badge, self.icon, self.size, self.pad, self.icon_size = w, badge, icon, size, pad, icon_size
        self.bw = badge_w(badge) if badge else 0
        avail = (w - 2 * pad - (icon_size + 8 if icon else 0) - (self.bw + 8 if badge else 0)) * SAFETY
        self.lines = metrics.wrap_text(label, avail, size)
        self.h = max(h, len(self.lines) * size * metrics.line_ratio() + 16)
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="solid", sw=2,
                                   dash="dashed" if self.badge == "preview" else "solid")
            tx = x + self.pad
            if self.icon:
                place_icon(cv, self.icon, tx, y + (H - self.icon_size) / 2, self.icon_size)
                tx += self.icon_size + 8
            tH = len(self.lines) * self.size * metrics.line_ratio()
            cv.text(tx, y + (H - tH) / 2, "\n".join(self.lines), size=self.size, color=th.deep)
            if self.badge:
                draw_badge(cv, x + self.w - self.pad - self.bw, y + (H - 22) / 2, self.badge)
        cv.register(f"pill:{self.lines[0]}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


class Chev(Rect2):
    """Chevron (pentagon arrow) step with a centred label and optional small sub-label."""

    def __init__(self, w, label, *, sub=None, theme="teal", h=72, size=17, sub_size=13, notch=28, first=False,
                 fill="hachure", dash="solid"):
        self.th = get_theme(theme)
        self.w, self.h, self.size, self.sub_size, self.notch, self.first = w, h, size, sub_size, notch, first
        self.fill, self.dash = fill, dash
        self.box_w = w - notch * (1 if first else 2) - 6
        inner = self.box_w * SAFETY
        self.lines = metrics.wrap_text(label, inner, size)
        self.sub_lines = metrics.wrap_text(sub, inner, sub_size) if sub else []
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, n, w = self.th, self.notch, self.w
        pts = [(x, y), (x + w - n, y), (x + w, y + H / 2), (x + w - n, y + H), (x, y + H)]
        if not self.first:
            pts.append((x + n, y + H / 2))
        pts.append(pts[0])
        lr = metrics.line_ratio()
        tH = len(self.lines) * self.size * lr + (len(self.sub_lines) * self.sub_size * lr + 2 if self.sub_lines else 0)
        tx = x + (0 if self.first else n) + 3
        with cv.group():
            cv.poly(pts, kind="line", stroke=th.stroke, sw=2, fill=th.fill, fill_style=self.fill, dash=self.dash)
            ty = y + (H - tH) / 2
            cv.text(tx, ty, "\n".join(self.lines), size=self.size, color=th.deep, align="center", w=self.box_w)
            if self.sub_lines:
                ty += len(self.lines) * self.size * lr + 2
                cv.text(tx, ty, "\n".join(self.sub_lines), size=self.sub_size, color=MUTED, align="center",
                        w=self.box_w)
        return self


def band(cv, y, n, title, sub=None, theme="teal"):
    """Numbered section header spanning the canvas; returns the y below it."""
    numbered(cv, 24, y + 27, n, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 66, y, title, sub=sub, size=34, w=W - 66, sub_size=17)
    return bottom + 26


# ---------------------------------------------------------------------------------------------- bands
def band_summary(cv, y):
    cw = (W - 3 * GAP) // 4
    cards = [
        Card(cw, "Foundry IQ = Azure AI Search + a KB layer", [
            "Managed knowledge layer: knowledge bases + knowledge sources + agentic retrieval, built on Azure AI Search",
            "Azure AI Search is required; Foundry Agent Service is not; the LLM is optional (planning / synthesis only)",
            "Not a database: you pay for Search plus model tokens; a free tier and a free token allowance exist",
        ], theme="teal", icon="ai-search", src=[("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq"))]),
        Card(cw, "GA vs preview follows the API version", [
            "2026-04-01 (GA): knowledge bases with minimal effort only - no LLM, extractive data, intents",
            "2026-08-01-preview: LLM query planning, answer synthesis, low / medium / auto, most knowledge-source kinds",
            f"Azure portal and Foundry portal use the preview API: preview-only access ({ASOF})",
        ], theme="grape", icon="versions", src=[("Migrate agentic retrieval code", S("agentic-retrieval-how-to-migrate"))]),
        Card(cw, "Three ways to give an agent search content", [
            "File search: agent-managed vector stores of files that users upload",
            "Azure AI Search tool: connect one existing index per tool",
            "Foundry IQ knowledge base over MCP: many sources, LLM planning, permission-aware",
        ], theme="orange", icon="toolbox", src=[("Azure AI Search tool", learn("agents/how-to/tools/ai-search")),
                                                ("File search", learn("agents/how-to/tools/file-search"))]),
        Card(cw, "Two identities, two role sets", [
            "AI Search tool (keyless): Foundry account system-assigned MI with Search Index Data Contributor + Search Service Contributor",
            "Foundry IQ connection: Foundry project MI with Search Index Data Reader",
            "Search service MI needs Cognitive Services User on the Foundry resource when the KB has an LLM",
        ], theme="red", icon="managed-identity", src=[("Connect a KB to Agent Service", learn("agents/how-to/foundry-iq-connect"))]),
    ]
    _, bottom = row(cv, 0, y, cards, gap=GAP)
    return bottom


def band_picture(cv, y):
    y = band(cv, y, 1, "Foundry IQ is a layer on top of Azure AI Search",
             "sources feed knowledge sources; a knowledge base runs agentic retrieval; agents consume it three ways")
    legend(cv, 0, y, [("Foundry IQ layer", "teal"), ("Indexed source / classic index", "cyan"),
                      ("Remote source", "gray"), ("Agent-facing tool", "orange")])
    draw_badge(cv, 1380, y - 1, "ga")
    cv.text(1425, y, "solid outline", size=15, color=MUTED)
    draw_badge(cv, 1590, y - 1, "preview")
    cv.text(1685, y, "dashed outline = preview API", size=15, color=MUTED)
    top = y + 52

    LW, CX, CW, RX, RW = 560, 750, 1500, 2440, 560

    # ---- sources (left)
    indexed = [("Existing search index (searchIndex)", "ai-search", "ga"), ("Blob / ADLS Gen2 (azureBlob)", "storage", "ga"),
               ("OneLake (indexedOneLake)", "onelake", "ga"), ("SharePoint, indexed", "sharepoint", "preview"),
               ("Azure SQL", "sql", "preview"), ("File upload (no indexer)", "file", "preview")]
    remote = [("Web, Bing-backed (web)", "globe", "ga"), ("Remote SharePoint", "sharepoint", "preview"),
              ("Fabric data agent", "fabric", "preview"), ("Fabric ontology (fabricOntology)", "fabric", "preview"),
              ("MCP server (mcp)", "mcp", "preview"), ("Work IQ", "iq", "preview")]
    with cv.panel(0, top, title="Indexed: copied into Search", sub="indexers chunk + embed; ACLs captured at ingest",
                  theme="cyan", style="dashed", fill="soft", pad=24, title_size=22, sub_size=14, w=LW) as pi:
        yy = pi.iy
        for label, icon, badge in indexed:
            Pill(LW - 48, label, badge=badge, icon=icon, theme="cyan").place(cv, pi.ix, yy)
            yy += 50
    with cv.panel(0, pi.bottom + 30, title="Remote: queried live", sub="no copy; per-user token where the source supports it",
                  theme="gray", style="dashed", fill="soft", pad=24, title_size=22, sub_size=14, w=LW) as pr:
        yy = pr.iy
        for label, icon, badge in remote:
            Pill(LW - 48, label, badge=badge, icon=icon, theme="gray").place(cv, pr.ix, yy)
            yy += 50
    total_h = pr.bottom - top

    # ---- centre: the Azure AI Search service
    with cv.panel(CX, top, title="Azure AI Search service", sub="one service to secure: identity, network, tier, billing",
                  theme="teal", style="dotted", fill="none", pad=28, title_size=28, sub_size=15, w=CW, min_h=total_h) as ps:
        ix, iy = ps.ix, ps.iy
        cv.text(ix, iy, f"Agentic retrieval pipeline run by the knowledge base ({ASOF})", size=17, color=get_theme("teal").deep)
        steps = [("Plan", "LLM planning (preview)"), ("Fan out", "parallel subqueries"), ("Rerank", "semantic L2 (L3 in medium)"),
                 ("Merge", "results merged"), ("Synthesize", "optional (preview)"), ("Return", "response + activity + refs")]
        cwid, notch = 250, 26
        cx0 = ix
        for i, (lab, sub) in enumerate(steps):
            Chev(cwid, f"{i + 1} {lab}", sub=sub, theme="teal", first=(i == 0), notch=notch, h=72,
                 dash="dashed" if lab in ("Plan", "Synthesize") else "solid").place(cv, cx0, iy + 30)
            cx0 += cwid - notch + 8
        ky = iy + 30 + 72 + 26
        kb = Card(1444, "Knowledge base (KB): the agentic retrieval engine", [
            "References 1-10 knowledge sources; optional LLM (Azure OpenAI chat deployment) for planning and synthesis",
            "Effort: minimal (GA), low / medium / auto (preview); output: extractive data (GA) or answer synthesis (preview)",
            "Exposed as REST / SDK retrieve and as an MCP endpoint with one tool: knowledge_base_retrieve",
        ], theme="teal", icon="iq", min_h=190, subtitle="GA in 2026-04-01: minimal effort, no LLM").place(cv, ix, ky)
        ks = Card(1444, "Knowledge sources (KS): reusable connections to content", [
            "Indexed KS: auto pipeline (data source + skillset + indexer + index) or reuse an existing index",
            "Remote KS: queried live per request; GA kinds: searchIndex, azureBlob, indexedOneLake, web",
        ], theme="teal", icon="cubes", min_h=140).place(cv, ix, kb.bottom + 42)
        with cv.panel(ix, ks.bottom + 42, theme="cyan", style="solid", fill="hatch", pad=16, w=1444, min_h=140) as idx:
            place_icon(cv, "ai-search", idx.ix, idx.iy, 36)
            cv.text(idx.ix + 48, idx.iy + 5, "Classic index: the foundation (every tier)", size=20, color=get_theme("cyan").deep)
            ChipFlow(["Vector search (<= 4,096 dims)", "Hybrid with RRF", "Semantic ranker (L2)", "Integrated vectorization",
                      "Skillsets (AI enrichment)", "Security filters / ACLs"], 1380, theme="cyan", size=16).place(cv, idx.ix, idx.iy + 56)
    connect(cv, ks, kb, a_side="top", b_side="bottom", label="KB queries 1-10 KS", label_size=14, end_head="arrow", dash="solid")
    connect(cv, idx, ks, a_side="top", b_side="bottom", label="indexed KS wrap an index", label_size=14)

    # sources -> knowledge sources
    connect(cv, pi, ks, a_side="right", b_side="left", tb=0.3, route="elbow", label="ingest", label_size=14, label_t=0.12)
    connect(cv, pr, ks, a_side="right", b_side="left", tb=0.7, route="elbow", dash="dashed", label="live calls", label_size=14,
            label_t=0.12, label_pos="below")

    # ---- consumers (right)
    bh = 64
    with cv.panel(RX - 24, top, title="Consumers: how agents reach it", theme="orange", style="dotted", fill="none", pad=24,
                  title_size=22, w=RW + 48, min_h=total_h) as pc:
        rest = Box(RW, "REST / SDK retrieve", sub="Azure SDKs, Agent Framework, any app", theme="gray", icon="api",
                   icon_pos="left", h=bh, fill="hatch").place(cv, RX, kb.y)
        mcp = Box(RW, "Foundry IQ KB over MCP", sub="tool knowledge_base_retrieve", theme="orange", icon="mcp",
                  icon_pos="left", h=bh, fill="hatch").place(cv, RX, kb.y + bh + 14)
        tool = Box(RW, "Azure AI Search tool", sub="connects one index per tool", theme="orange", icon="ai-search",
                   icon_pos="left", h=bh, fill="hatch").place(cv, RX, idx.y)
        fsr = Box(RW, "File search", sub="agent-managed vector stores", theme="orange", icon="files", icon_pos="left",
                  h=bh, fill="hatch").place(cv, RX, idx.y + bh + 14)
    stamp(cv, mcp, "preview")
    connect(cv, kb, rest, a_side="right", b_side="left", ta=(rest.cy - kb.y) / kb.h, label="retrieve", label_size=14)
    connect(cv, kb, mcp, a_side="right", b_side="left", ta=(mcp.cy - kb.y) / kb.h, label="MCP endpoint", label_size=14)
    connect(cv, idx, tool, a_side="right", b_side="left", ta=(tool.cy - idx.y) / idx.h, label="queries 1 index", label_size=14)
    connect(cv, idx, fsr, a_side="right", b_side="left", ta=(fsr.cy - idx.y) / idx.h, label="vector stores", label_size=14)
    bx = pc.right + 14
    brace(cv, bx, mcp.y, fsr.bottom, side="right", depth=16)
    ty = (mcp.y + fsr.bottom) / 2 - 50
    cv.text(bx + 34, ty, "Toolbox", size=22, color=get_theme("orange").deep)
    cv.text(bx + 34, ty + 30, "one MCP endpoint can\nwrap all three tools", size=15, color=MUTED)
    return max(ps.bottom, pr.bottom, pc.bottom)


def band_versions(cv, y):
    y = band(cv, y, 2, "GA vs preview follows the API version",
             f"Search REST 2026-04-01 is the first stable version for agentic retrieval; 2026-08-01-preview is the newest preview ({ASOF})",
             theme="grape")
    tw = 2060
    t = Table(
        [("Capability", 330), ("2026-04-01  (GA stable)", 760), ("2026-08-01-preview  (Preview)", 970)],
        [
            ["Knowledge base + retrieve", "Yes: minimal effort only, extractive data only. Request uses intents (replaces messages); no running transcript - send a new intent per follow-up",
             "Yes: multi-turn messages"],
            ["LLM query planning (low, medium, auto)", dict(text=CROSS, align="center"), dict(text=CHECK, align="center")],
            ["Answer synthesis (outputMode answerSynthesis)", dict(text=CROSS, align="center"), dict(text=CHECK, align="center")],
            ["models (LLM) on the KB", "Optional: needed only when the KB contains a web KS (web content is always LLM-summarised)",
             "Required for planning / synthesis"],
            ["GA knowledge-source kinds", "searchIndex, azureBlob (Blob / ADLS Gen2), indexedOneLake, web", "Same, plus the preview kinds"],
            ["Preview knowledge-source kinds", "None (indexed and remote SharePoint are not available in 2026-04-01)",
             "Azure SQL, File (upload), Indexed SharePoint, Remote SharePoint, Fabric Data Agent, Fabric Ontology, MCP server, Work IQ"],
            ["Ingestion permission options (ACL, RBAC scope, Purview label)", "Removed: ingestionPermissionOptions is not supported on azureBlob / indexedOneLake",
             "Supported (preview)"],
            ["Removed or renamed fields", "retrievalReasoningEffort, outputMode, alwaysQuerySource, instructions removed; maxOutputSize becomes maxOutputSizeInTokens. Removed fields return 400",
             "Preview contract; breaking changes listed at the right"],
        ], w=tw, theme="grape", size=15, head_size=16, first_col_theme="grape", title="What each API version gives you", title_size=22)
    t.place(cv, 0, y)
    nx = tw + GAP
    nw = W - nx
    n1 = Note(nw, "Work IQ knowledge source uses workIQParameters.entraAppAuthentication; header x-ms-query-work-iq-source-authorization; "
                  "$top / $skip removed; MCP knowledge source inclusionMode renamed resultsProcessing (rerank / none).",
              kind="warn", title="Breaking changes in 2026-08-01-preview", src=[("Migrate agentic retrieval code", S("agentic-retrieval-how-to-migrate"))])
    n1.place(cv, nx, y)
    n2 = Note(nw, "2025-08-01-preview is the legacy knowledge agent contract (no retrievalReasoningEffort). 2025-11-01-preview renamed knowledge "
                  "agents to knowledge bases (/agents became /knowledgebases). The migrate page explains moving to KBs.",
              kind="info", title="Older versions you may still meet")
    n2.place(cv, nx, n1.bottom + 22)
    n3 = Note(tw, "Foundry blog, 2026-06-02 (Pablo Castro): GA = knowledge bases, Foundry IQ MCP server, minimal effort, KS Blob / search index / Web / OneLake. "
                  "Preview = Serverless Developer tier, new KS (Work IQ, Fabric, File, Azure SQL, MCP), cross-tenant CMK, Purview label auditing, "
                  "SharePoint incremental permission sync. Consistent with the table above.",
              kind="quote", title="Blog-sourced, not in Learn",
              src=[("Foundry IQ blog", "https://devblogs.microsoft.com/foundry/build-smarter-agents-faster-with-foundry-iq/")])
    n3.place(cv, 0, t.bottom + 26)
    return max(n3.bottom, n2.bottom)


def band_kb_ks(cv, y):
    y = band(cv, y, 3, "Knowledge bases and knowledge sources",
             "what a KB holds, what a retrieve call carries and returns, and every knowledge-source kind")
    cw = (W - 3 * GAP) // 4
    c1 = Card(cw, "Knowledge base properties", [
        "description; knowledgeSources[] (names only; 1-10 per KB depending on tier)",
        "models[]: kind azureOpenAI with resourceUri, deploymentId, modelName, authIdentity",
        "Preview-only: retrievalInstructions, answerInstructions, outputMode (extractiveData default / answerSynthesis), retrievalReasoningEffort",
        "encryptionKey (customer-managed key), retrieveDefaults, corsOptions",
        "KB LLM = Azure OpenAI chat deployment; the search service MI needs Cognitive Services User on it (MI needs Basic tier or higher). Model lists differ between pages: section 11",
    ], theme="teal", icon="iq", src=[("Create a knowledge base", S("agentic-retrieval-how-to-create-knowledge-base"))])
    c2 = Card(cw, "Retrieve request", [
        "intents (GA) or messages (preview): the user question(s)",
        "outputMode and retrievalReasoningEffort override the KB defaults (preview)",
        "maxRuntimeInSeconds: 10-600 s, default 90 s; Work IQ KS needs >= 120 s",
        "maxOutputSizeInTokens (maxOutputSize in 2026-05-01-preview and later): default 5,000; maxOutputDocuments caps documents",
        "knowledgeSourceParams per source: alwaysQuerySource / neverQuerySource (preview), failOnError, rerankerThreshold, filterAddOn, includeReferences",
    ], theme="teal", icon="rest", src=[("Query a knowledge base", S("agentic-retrieval-how-to-retrieve"))])
    c3 = Card(cw, "Retrieve response", [
        "response[]: grounding text; citations [ref_id:n] when synthesised",
        "activity[]: query plan, per-source timings and token counts",
        "references[]: source documents (sourceData); Purview label info when present",
        "Fabric ontology returns fabricAnswer + fabricRawData (CSV)",
        "206 = partial success; 502 = every selected source failed, or a failOnError source failed",
    ], theme="teal", icon="rest", src=[("Query a knowledge base", S("agentic-retrieval-how-to-retrieve"))])
    hmax = max(c1.h, c2.h, c3.h)
    row(cv, 0, y, [c1, c2, c3], gap=GAP)
    n = Card(cw, "Indexed knowledge-source pipeline", [
        "1  Source (Blob, OneLake, SharePoint, SQL) read by an indexer",
        "2  Text split into chunks",
        "3  Chunks embedded with an Azure OpenAI deployment",
        "4  Index written, plus ACL / label metadata",
        "5  Queryable by the KB; schedule indexer runs for incremental refresh",
    ], theme="cyan", icon="data-factory", src=[("Knowledge sources overview", S("agentic-knowledge-source-overview"))])
    n.place(cv, 3 * (cw + GAP), y, h=hmax)
    y = hmax + y + 40

    GA, PV = ("GA", "green"), ("Preview", "orange")
    IDX, RMT = ("Indexed", "cyan"), ("Remote", "gray")
    t = Table(
        [("Knowledge source kind", 300), ("Mode", 160), ("Status", 100), ("Auth / permission behaviour", 1040), "Notes"],
        [
            ["searchIndex", ("Existing index", "cyan"), GA, "ACL / RBAC enforced only if the index carries them", "Reuse any index"],
            ["azureBlob (Blob, ADLS Gen2)", ("Indexed, auto pipeline", "cyan"), GA,
             "ingestionPermissionOptions (ACL / RBAC scope / Purview label) - preview, not in 2026-04-01",
             "Auto-creates data source + skillset + indexer + index; chunks + embeds (for example text-embedding-3-large); assetStore for images (excludes ingestionPermissionOptions); per-language analyzers; private ingestion via shared private link"],
            ["indexedOneLake", IDX, GA, "OneLake permissions applied at ingest", "Private ingestion via shared private link is not supported"],
            ["SharePoint, indexed", IDX, PV, "SharePoint ACLs synced at ingest", "Incremental permission sync is preview (blog-sourced)"],
            ["Azure SQL", IDX, PV, "-", "Shared private link group: sqlServer"],
            ["File (direct upload)", IDX, PV, "-", "No indexer; separate limits"],
            ["SharePoint, remote", RMT, PV, "Per-user token (Copilot Retrieval API)",
             "No Copilot connectors or OneDrive; 200 requests per user per hour; 1,500-character query; 25 results; text only"],
            ["web", RMT, GA, "None (public web)",
             "Bing Custom Search-backed; domain include / exclude; content always LLM-summarised; not in private or sovereign clouds; DPA does not apply"],
            ["Fabric Data Agent", RMT, PV, "User token exchanged for a Fabric-scoped token; same tenant", "-"],
            ["fabricOntology", RMT, PV, "OBO via x-ms-query-source-authorization (scope https://search.azure.com/.default)",
             "Parameters workspaceId, ontologyId; minimal effort not supported"],
            ["MCP server (mcp)", RMT, PV, "foundryConnection (only when called from Agent Service) or storedHeaders (static, write-only); per-request headers",
             "Output parsing auto / json / split / none; minimal effort unsupported; resultsProcessing rerank / none; no alwaysQuerySource"],
            ["Work IQ", RMT, PV, "Customer Entra app + federated credential on the search service MI (issuer login.microsoftonline.com/<tenant>/v2.0, subject = MI principal ID, "
                                  "audience api://AzureADTokenExchange); scope api://<appId>/access_as_user; user assertion header",
             "40-60 s+ latency; maxRuntimeInSeconds >= 120; delegated only; actions may perform writes (warning)"],
        ], w=W, theme="teal", size=14, head_size=16, first_col_theme="teal", title=f"Knowledge-source catalog ({ASOF})", title_size=22)
    t.place(cv, 0, y)
    return t.bottom


def far_msg(seq, src, dst, text, anchor, *, num=None, dash="solid", color=INK):
    """Sequence message whose label sits between two chosen lifelines so it never crosses an intermediate one."""
    cv = seq.cv
    x1, x2 = seq._cx(src), seq._cx(dst)
    a, b = sorted((seq._cx(anchor[0]), seq._cx(anchor[1])))
    lines = metrics.wrap_text(text, b - a - 44, seq.label_size)
    txt = "\n".join(lines)
    tw, th_ = metrics.text_size(txt, seq.label_size)
    y = seq.cur + th_ + 14
    sg = 1 if x2 > x1 else -1
    cv.poly([(x1 + 4 * sg, y), (x2 - 4 * sg, y)], kind="arrow", stroke=color, sw=2, dash=dash, end_head="arrow")
    cv.text(a + (b - a - tw) / 2, y - th_ - 5, txt, size=seq.label_size, color=INK, align="center", w=tw)
    if num is not None:
        numbered(cv, (min(x1, x2) + 22) if sg > 0 else (max(x1, x2) - 22), y - 16, num, theme=seq.actors[src][1].name, d=26, size=15)
    seq.cur = y + 20
    return y


def band_pipeline(cv, y):
    y = band(cv, y, 4, "How agentic retrieval runs",
             "plan, fan out, rerank, merge, synthesize, return - and how much LLM work each effort level buys")
    top = y
    seq = Sequence(cv, 0, top, [("Agent or app", "green", "agent"), ("Knowledge base", "teal", "iq"), ("KB LLM", "blue", "openai"),
                                ("Knowledge sources", "cyan", "ai-search")], spacing=380, head_w=210, head_h=62)
    seq.msg(0, 1, "retrieve (REST / SDK) or MCP tool knowledge_base_retrieve: intents or messages, effort, optional user token", num=1)
    seq.msg(1, 2, "low / medium / auto: plan subqueries and pick knowledge sources (preview)", num=2)
    seq.msg(2, 1, "query plan", dash="dashed")
    far_msg(seq, 1, 3, "subqueries in parallel: keyword / vector / hybrid on indexed KS, live calls to remote KS", (2, 3), num=3)
    far_msg(seq, 3, 1, "results (per-user token honoured where supported)", (2, 3), dash="dashed")
    seq.note(1, 2, "semantic rerank (L2); medium adds an L3 classifier and may iterate once; results merged", kind="info")
    seq.msg(1, 2, "optional answer synthesis, citations [ref_id:n] (preview)", num=4)
    seq.msg(2, 1, "cited answer", dash="dashed")
    seq.msg(1, 0, "response + activity (plan, tokens, timings) + references", num=5, dash="dashed")
    sbot = seq.end()

    rx = 3 * 380 + 210 + 70
    rw = W - rx
    t = Table(
        [("Effort level", 170), ("Status", 100), ("What happens", 760), "Limits"],
        [
            [("minimal", "teal"), ("GA", "green"), "No LLM planning: direct text + vector search on all KS in the KB; no query expansion; alwaysQuerySource ignored",
             "extractiveData only; no answer synthesis; no web KS (docs differ, see section 11); <= 10 KS per KB; meant for migrations from the Search API or DIY planning"],
            [("low (default when unset)", "teal"), ("Preview", "orange"), "One pass of LLM query planning + KS selection; subqueries fan out; merge; synthesis optional",
             "5,000 answer tokens; semantic ranking over <= 50 docs (10 if L3 classification)"],
            [("medium", "teal"), ("Preview", "orange"), "low + deeper stack: a semantic classifier checks the first results; if insufficient, one follow-up iteration with a revised plan (L3 rescoring, range 0-4.0 like L2)",
             "10,000 answer tokens; <= 50 docs (20 with L3); select regions only (see note)"],
            [("auto", "teal"), ("Preview", "orange"), "Lightweight first pass; returns if grounding suffices, else LLM planning up to medium",
             "Needs 2026-08-01-preview + a KB model; all agentic-retrieval regions; older API versions return 400"],
        ], w=rw, theme="teal", size=15, head_size=16, title="Retrieval reasoning effort", title_size=22)
    t.place(cv, rx, top)
    mw = (rw - GAP) // 2
    m1 = Card(mw, "Extractive data (default)", [
        "Raw grounding chunks with references; the agent's own LLM writes the answer",
        "The only output mode for minimal effort",
    ], theme="teal", badge="ga", src=[("Set the retrieval reasoning effort", S("agentic-retrieval-how-to-set-retrieval-reasoning-effort"))])
    m2 = Card(mw, "Answer synthesis", [
        "KB LLM writes a cited answer following answerInstructions; citations [ref_id:n]",
        "Billed as Azure OpenAI input / output tokens on the KB's LLM",
        "Set on the KB (default) or per retrieve request (override); incompatible with minimal",
    ], theme="teal", badge="preview", src=[("Answer synthesis", S("agentic-retrieval-how-to-answer-synthesis"))])
    row(cv, rx, t.bottom + 34, [m1, m2], gap=GAP)
    n1 = Note(rw, "medium is available in select regions only: East US 2, East US, South Central US, West US 3, West US 2, West US, Germany West Central, "
                  "North Europe, Switzerland North, Sweden Central, Spain Central, UK South, Korea Central, Japan East, Southeast Asia.",
              kind="warn", title=f"Regions for medium ({ASOF})")
    n1.place(cv, rx, m1.bottom + 28)
    n2 = Note(rw, "KS selectable per retrieval, 2026-05-01-preview and later: minimal / low / medium = Free 3, Basic 5 or 10, others 10. "
                  "2025-11-01-preview: low = 3 on every tier, medium = 5 (Free 3); the Foundry IQ FAQ limits (low: 3 sources, 3 subqueries, 5,000 answer tokens; "
                  "medium: 5 / 5 / 10,000) match that older version.", kind="info", title="Per-retrieval limits depend on the API version")
    n2.place(cv, rx, n1.bottom + 22)
    return max(sbot, n2.bottom)


def band_ways(cv, y):
    y = band(cv, y, 5, "Three ways an agent can use search content",
             "decide by what the content is and who may see it - then compare the options row by row", theme="orange")
    qw = 560
    gap = (W - 5 * qw) / 4
    qs = [
        ("Files the user uploads in chat?", "File search", "agent-managed vector store", "orange", "files", None),
        ("One existing vector index?", "Azure AI Search tool", "connect the index you already have", "orange", "ai-search", None),
        ("Several or remote sources, per-user ACLs, LLM planning, or sharing across agents?", "Foundry IQ knowledge base (MCP)",
         "multi-source, permission-aware, reusable", "teal", "iq", None),
        ("Need web freshness?", "Web search tool or Web IQ", "a separate tool, not Azure AI Search", "gray", "globe", None),
        ("Need live structured business data?", "Fabric IQ", "ontology, semantic model, data agent (preview)", "gray", "fabric", "preview"),
    ]
    qb, ab = [], []
    for i, (q, a, sub, th, icon, badge) in enumerate(qs):
        x = i * (qw + gap)
        qbox = Box(qw, q, theme="gray", fill="soft", h=104, size=18).place(cv, x, y)
        abox = Box(qw, a, sub=sub, theme=th, icon=icon, icon_pos="left", fill="hatch", h=96, size=19).place(cv, x, y + 104 + 84)
        if badge:
            stamp(cv, abox, badge)
        connect(cv, qbox, abox, a_side="bottom", b_side="top", label="yes", label_size=15, label_pos="right")
        qb.append(qbox)
        ab.append(abox)
    for i in range(4):
        connect(cv, qb[i], qb[i + 1], a_side="right", b_side="left", dash="dashed", label="no", label_size=15)
    y = y + 104 + 84 + 96 + 50

    T, FS, IQ = ("orange"), None, None
    t = Table(
        [("", 230), ("File search (vector store)", 1040), ("Azure AI Search tool", 1040), ("Foundry IQ KB over MCP", 1050)],
        [
            ["What it is", "Agent-managed vector stores of uploaded files", "Connect an existing index", "KB over many sources + agentic retrieval"],
            ["Backing store", "Basic setup: Microsoft-managed storage + search. Standard setup: your Blob + your AI Search. Sources: local upload (Basic + Standard), Azure Blob (Standard only)",
             "Your search service and index", "Your search service"],
            ["Ingestion", "Platform parses, chunks (800 tokens, 400 overlap) and embeds (text-embedding-3-large at 256 dims)",
             "You build the index: searchable + retrievable Edm.String, Collection(Edm.Single) vector field, text + source-URL citation fields",
             "KS auto pipeline or reuse an index; remote KS queried live"],
            ["Retrieval", "Query rewrite + parallel searches + hybrid + rerank; up to 20 chunks into context",
             "query_type simple / vector / semantic / vector_simple_hybrid / vector_semantic_hybrid (default vector_semantic_hybrid); top_k default 5; filter applies to every query",
             "LLM planning, parallel subqueries across sources, semantic rerank, optional synthesis"],
            ["Multi-source", "No: 1 vector store per agent and per conversation", "No: one index per tool", "Yes: up to 10 KS per KB"],
            ["Per-user trimming", "Not documented on the tool page", "Only via a filter you craft", "x-ms-query-source-authorization flow (section 7)"],
            ["Connection", "Uses the agent-setup resources", "Project connection: category CognitiveSearch, authType AAD or ApiKey",
             "Project connection: category RemoteTool, authType ProjectManagedIdentity"],
            ["In a Toolbox", "Yes", "Yes (recommended)", "Yes, as an MCP tool"],
            ["Private network", "Via private endpoint; but Azure Blob files with File Search are unsupported in a BYO-VNet config (file-search page)",
             "Via private endpoint; needs project MI (no keys); basic setup cannot reach private Search",
             "MCP; Foundry network table: Foundry IQ (preview) supported via MCP"],
            ["Limits", "<= 10,000 files per store; 512 MB per file; <= 500 files per batch; conversation stores expire 7 days after last active",
             "1 index; same tenant", "Per-tier KS / KB limits (section 10)"],
            ["Use when", "Quick RAG over uploaded docs", "One existing vector index", "Multiple or remote sources, permission-aware, planning, reuse across agents"],
        ], w=W, theme="orange", size=15, head_size=18, first_col_theme="orange", title="Comparison", title_size=22)
    t.place(cv, 0, y)
    nw = (W - 2 * GAP) // 3
    y = t.bottom + 30
    n1 = Note(nw, "File-search page: 5,000,000 tokens per file; limits page: 2,000,000. Check both pages before sizing a vector store.",
              kind="warn", title="Docs disagree: vector-store per-file token limit",
              src=[("File search", learn("agents/how-to/tools/file-search")), ("Vector stores", learn("agents/concepts/vector-stores"))])
    n2 = Note(nw, "File-search page: Azure Blob files with File Search are unsupported in a BYO-VNet config. Network tables: File search is supported through a private endpoint.",
              kind="warn", title="Docs disagree: File search in private networks", src=[("Configure private link", learn("how-to/configure-private-link"))])
    n3 = Note(nw, "Neither tool page labels itself preview, and both support basic and standard agent setups. The file-search page itself says: existing AI Search index, use the AI Search tool; "
                  "to combine several sources, use multiple tools together.", kind="info", title="Good to know",
              src=[("Azure AI Search tool", learn("agents/how-to/tools/ai-search"))])
    hmax = max(n1.h, n2.h, n3.h)
    for i, n in enumerate((n1, n2, n3)):
        n.place(cv, i * (nw + GAP), y, h=hmax)
    return y + hmax


def band_connect(cv, y):
    y = band(cv, y, 6, "Connect a knowledge base to a Foundry agent",
             "seven setup steps; the call path is agent tool -> project connection -> KB MCP endpoint on the search service")
    cw, notch = 500, 30
    step = cw - notch + 6
    steps = ["Search service with system-assigned MI + RBAC data plane", "Create knowledge source(s): indexed or remote",
             "Create the KB: models, effort, instructions", "Grant roles (see section 7)",
             "Create the RemoteTool project connection (preview)", "Add the MCPTool to the agent or a Toolbox",
             "Agent calls knowledge_base_retrieve on a user turn"]
    for i, s in enumerate(steps):
        Chev(cw, f"{i + 1}  {s}", theme="teal", first=(i == 0), notch=notch, h=76, size=16).place(cv, i * step, y)
    y += 76 + 40
    cwid = 580
    gap = (W - 5 * cwid) / 4
    c_tool = Card(cwid, "Agent MCPTool", [
        "server_url = the KB MCP endpoint",
        "project_connection_id = the connection",
        "allowed_tools = [knowledge_base_retrieve]",
        "require_approval as needed; attach to the agent or to a Toolbox",
    ], theme="orange", icon="mcp", src=[("Connect a KB to Agent Service", learn("agents/how-to/foundry-iq-connect"))])
    c_conn = Card(cwid, "Project connection", [
        "Category RemoteTool (preview), authType ProjectManagedIdentity",
        "Audience https://search.azure.com/; isSharedToAll; metadata ApiType Azure",
        "Created through the ARM connections API 2025-10-01-preview",
    ], theme="orange", icon="api-connections", badge="preview")
    c_kb = Card(cwid, "KB MCP endpoint", [
        "{search-endpoint}/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview",
        "Exposes one tool, knowledge_base_retrieve: the only tool supported with Agent Service",
    ], theme="teal", icon="iq")
    c_roles = Card(cwid, "Roles to grant", [
        "Foundry User on the Foundry account to use the tool; Foundry Project Manager to create the connection",
        "Project MI: Search Index Data Reader (Contributor only if the agent writes)",
        "Search service MI: Cognitive Services User on the Foundry account, only if the KB has an LLM",
    ], theme="red", icon="managed-identity")
    c_cite = Card(cwid, "Citations and prerequisites", [
        "Blob KS returns the document URL; search-index KS falls back to the MCP endpoint URL",
        "Needs azure-ai-projects >= 2.0.0",
        "Hub-based projects are not supported",
    ], theme="teal", icon="files")
    cards = [c_tool, c_conn, c_kb, c_roles, c_cite]
    hmax = max(c.h for c in cards)
    for i, c in enumerate(cards):
        c.place(cv, i * (cwid + gap), y, h=hmax)
    connect(cv, c_tool, c_conn, label="project_connection_id", label_size=14, label_wrap=130)
    connect(cv, c_conn, c_kb, label="MCP call as the project MI", label_size=14, label_wrap=130)
    connect(cv, c_kb, c_roles, dash="dashed", label="needs", label_size=14)
    y += hmax + 30
    n = Note(W, "Hosted agents use a connection with authType agentic-identity: the agent's own identity is used and a user token is rejected. "
                "Grant that identity Search Index Data Reader after you deploy.", kind="info", title="Hosted-agent variant",
             src=[("Quickstart: Foundry IQ with a hosted agent", learn("agents/quickstarts/quickstart-foundry-iq-hosted-agent"))])
    n.place(cv, 0, y)
    return n.bottom


LANE = 1650
RX2 = W - LANE


def band_identity(cv, y):
    y = band(cv, y, 7, "Identity, roles and per-user trimming",
             "who calls Search as whom, which roles they hold, and how document-level permissions reach the query", theme="red")
    top = y
    # ---- left lane: identity diagram + roles table
    with cv.panel(0, top, title="Who calls Search as whom: managed identities and the roles they need", theme="red", style="dotted",
                  fill="none", pad=24, title_size=22, w=LANE) as p:
        bw, cw, hgap, vgap = 380, 322, 240, 190
        t0 = p.iy + 44
        b1 = Box(bw, "Foundry account", sub="system-assigned MI: AI Search tool, keyless", theme="red", icon="managed-identity",
                 icon_pos="left", fill="hatch", h=110).place(cv, p.ix, t0)
        b2 = Box(bw, "Foundry project", sub="managed identity: Foundry IQ connection (RemoteTool)", theme="red", icon="managed-identity",
                 icon_pos="left", fill="hatch", h=110).place(cv, p.ix, t0 + vgap)
        sx = p.ix + bw + hgap
        srch = Box(cw, "Azure AI Search service", sub="its own system-assigned MI makes the outbound calls", theme="teal", icon="ai-search",
                   fill="hatch", h=vgap + 110).place(cv, sx, t0)
        tx = sx + cw + hgap
        b3 = Box(bw, "Foundry / Azure OpenAI resource", sub="chat deployment for the KB LLM; embedding models", theme="blue", icon="openai",
                 icon_pos="left", fill="hatch", h=110).place(cv, tx, t0)
        b4 = Box(bw, "Azure Storage", sub="Blob / ADLS Gen2 for the azureBlob knowledge source", theme="cyan", icon="storage",
                 icon_pos="left", fill="hatch", h=110).place(cv, tx, t0 + vgap)
        connect(cv, b1, srch, a_side="right", b_side="left", tb=(b1.cy - srch.y) / srch.h,
                label="Search Index Data Contributor + Search Service Contributor", label_size=14, label_wrap=225)
        connect(cv, b2, srch, a_side="right", b_side="left", tb=(b2.cy - srch.y) / srch.h,
                label="Search Index Data Reader (+ Contributor if the agent writes)", label_size=14, label_wrap=225)
        connect(cv, srch, b3, a_side="right", b_side="left", ta=(b3.cy - srch.y) / srch.h, dash="dashed",
                label="Cognitive Services User: KB planning / synthesis and ingestion embeddings", label_size=14, label_wrap=225)
        connect(cv, srch, b4, a_side="right", b_side="left", ta=(b4.cy - srch.y) / srch.h, dash="dashed",
                label="Storage Blob Data Reader: blob KS ingestion", label_size=14, label_wrap=225)
    t = Table(
        [("Who", 470), ("Role (built-in role ID)", 790), "Why"],
        [
            ["Developer creating KBs, knowledge sources and indexes",
             "Search Service Contributor (7ca78c08-252a-4471-8644-bb5ff32d4ba0) + Search Index Data Contributor (8ebe5a00-799e-43f5-93ac-243d3dce84a7)",
             "Manage objects; load data"],
            ["Anyone or any agent that queries", "Search Index Data Reader (1407120a-92aa-4202-b7e9-c0e197c71c8f)", "Query; also lets the caller retrieve from a KB"],
            ["Owner / Contributor / Reader", "Control plane only", "No data access"],
            ["Foundry account system-assigned MI (AI Search tool, keyless)", "Search Index Data Contributor + Search Service Contributor", "AI Search tool page prerequisite"],
            ["Foundry project MI (Foundry IQ connection)", "Search Index Data Reader (+ Search Index Data Contributor for writes)", "Foundry IQ connect page"],
            ["Search service MI to Foundry / Azure OpenAI", "Cognitive Services User", "Planning and synthesis LLM; ingestion embeddings"],
            ["Search service MI to Storage", "Storage Blob Data Reader", "Blob KS ingestion"],
            ["Elevated read (preview)", "Search Index Data Contributor", "Bypass ACL trimming for admin reads"],
        ], w=LANE, theme="red", size=15, head_size=16, first_col_theme="red", title="Identity and roles matrix", title_size=22)
    t.place(cv, 0, p.bottom + 30)
    nt = Note(LANE, "Roles used in the private tutorial: Storage Blob Data Contributor, Search Service Contributor, Search Index Data Contributor, Foundry Project Manager, Foundry User. "
                     "The AI Search tool connection accepts Entra ID (keyless) or an API key; key-based auth is not supported with private virtual networking.",
              kind="info", title="Roles in the private tutorial",
              src=[("Azure AI Search RBAC", S("search-security-rbac")), ("Azure AI Search tool", learn("agents/how-to/tools/ai-search"))])
    nt.place(cv, 0, t.bottom + 24)
    left_bottom = nt.bottom

    # ---- right lane: per-user trimming sequence + approaches
    cv.text(RX2, top, "Per-user trimming: permissions are captured at ingestion and enforced at query time", size=22, color=get_theme("red").deep)
    seq = Sequence(cv, RX2, top + 40, [("Microsoft Entra ID", "red", "enterprise-apps"), ("Agent Service", "green", "agent"),
                                        ("Knowledge base", "teal", "iq"), ("Search index", "cyan", "ai-search")],
                   spacing=380, head_w=200, head_h=62)
    seq.msg(1, 1, "user turn: the caller is a signed-in user", num=1)
    seq.msg(1, 0, "on-behalf-of token request for https://search.azure.com (agent blueprint: user_impersonation)", num=2)
    seq.msg(0, 1, "user token (missing consent returns an oauth_consent_request item)", dash="dashed")
    seq.msg(1, 2, "retrieve + header x-ms-query-source-authorization (normal Search auth is still required)", num=3)
    seq.msg(2, 3, "match user / group identity to ingestion-time ACL, RBAC scope or label metadata", num=4)
    seq.msg(3, 2, "only permitted chunks", dash="dashed")
    seq.msg(2, 1, "grounded response + citations", dash="dashed", num=5)
    sb = seq.end()
    ta = Table(
        [("Way to get permissions into the index", 640), ("Status", 100), "Notes"],
        [
            ["Security filters on a string field", ("GA", "green"), "You craft the filter yourself"],
            ["POSIX-like ACLs / Azure RBAC scopes", ("Preview", "orange"), "Captured at ingestion (ingestionPermissionOptions)"],
            ["Microsoft Purview sensitivity labels", ("Preview", "orange"), "Single tenant; system-assigned MI only"],
            ["SharePoint ACLs", ("Preview", "orange"), "Synced at ingest by the indexed SharePoint KS"],
        ], w=LANE, theme="red", size=15, head_size=16, title="Four approaches", title_size=22)
    ta.place(cv, RX2, sb + 30)
    n1 = Note(LANE, "If the query omits the user token, or the source has no ingestion-time permission option, results are unfiltered.",
              kind="gotcha", title="Trimming is opt-in at both ends", src=[("Document-level access overview", S("search-document-level-access-overview"))])
    n1.place(cv, RX2, ta.bottom + 24)
    n2 = Note(LANE, "Agent Service sets the header for you when the caller is a user (OBO). Otherwise pass the token through structured inputs with the placeholder {{search_auth_token}}. "
                    "Remote sources (Fabric ontology, Fabric data agent, remote SharePoint) do their own OBO exchange; Work IQ uses x-ms-query-work-iq-source-authorization.",
              kind="info", title="Who sends the token", src=[("User delegation", learn("agents/concepts/user-delegation"))])
    n2.place(cv, RX2, n1.bottom + 20)
    return max(left_bottom, n2.bottom)


def band_network(cv, y):
    y = band(cv, y, 8, "Networking and private agentic retrieval",
             "inbound through a private endpoint, outbound through shared private links - and what the Foundry side needs", theme="indigo")
    top = y
    targets = [("Storage: blob / table / dfs / file", "storage"), ("Cosmos DB for NoSQL: Sql", "cosmos"), ("Azure SQL: sqlServer", "sql"),
               ("Key Vault: vault", "key-vault"), ("Web apps / Functions: sites", "app-service"), ("Azure OpenAI: openai_account", "openai"),
               ("Foundry: foundry_account", "foundry"), ("Foundry Tools: cognitiveservices_account", "ai-services"),
               ("Fabric: workspace", "fabric"), ("API Management: Gateway", "apim")]
    with cv.panel(0, top, title="Private path: Foundry agent, then Search, then data and models", theme="indigo", style="dotted",
                  fill="none", pad=24, title_size=22, w=LANE) as p:
        t0 = p.iy + 8
        with cv.panel(p.ix, t0, title="Your virtual network", sub="standard agent setup with VNet injection", theme="indigo",
                      style="dashed", fill="soft", pad=20, title_size=20, sub_size=14, w=420) as vn:
            a = Box(380, "Agent subnet", sub="delegated to Microsoft.App/environments; /24 recommended; Foundry in the same region as the VNet",
                    theme="indigo", icon="subnet", icon_pos="left", fill="hatch", h=150).place(cv, vn.ix, vn.iy)
            pe = Box(380, "Private endpoint subnet", sub="Search private endpoint; DNS zone privatelink.search.windows.net", theme="indigo",
                     icon="private-endpoint", icon_pos="left", fill="hatch", h=150).place(cv, vn.ix, vn.iy + 150 + 64)
            connect(cv, a, pe, a_side="bottom", b_side="top", label="inbound: project MI, no API keys", label_size=14, label_wrap=190)
        tx = vn.right + 170 + 330 + 170
        tpw = LANE - 24 - tx
        with cv.panel(tx, t0, title="Outbound: shared private links", sub="approve each link on the target side", theme="gray", style="dashed",
                      fill="soft", pad=22, title_size=20, sub_size=14, w=tpw) as tp:
            yy = tp.iy
            for lab, icon in targets:
                Pill(tpw - 44, lab, theme="gray", icon=icon, size=15, h=40).place(cv, tp.ix, yy)
                yy += 48
        srch = Box(330, "Azure AI Search", sub="agentic retrieval, indexers, embeddings", theme="teal", icon="ai-search", fill="hatch",
                   h=230).place(cv, vn.right + 170, (vn.y + tp.bottom) / 2 - 115)
        connect(cv, pe, srch, a_side="right", b_side="left", route="elbow", label="private endpoint", label_size=14)
        connect(cv, srch, tp, a_side="right", b_side="left", route="elbow", dash="dashed", label="shared private links", label_size=14,
                label_wrap=150)
    t = Table(
        [("Tier", 150), ("Max private endpoints", 330), ("Max group types", 250), "Private-endpoint indexers and skillsets"],
        [
            ["Free", "not listed", "not listed", "No private-endpoint indexers"],
            ["Basic", "10 or 30", "4", "Indexers yes; skillsets no"],
            ["S1", "100", "7", "Indexers yes; skillsets only if created after 2024-04-03"],
            ["S2 / S3", "400", "15", "Indexers and skillsets yes"],
            ["S3 HD", "not listed", "not listed", "No private-endpoint indexers or skillsets"],
            ["L1 / L2", "20", "4", "Indexers and skillsets yes"],
        ], w=LANE, theme="indigo", size=15, head_size=16, first_col_theme="indigo", title=f"Shared private link limits by tier ({ASOF})",
        title_size=22)
    t.place(cv, RX2, top)
    n1 = Note(LANE, "Even with shared private links, ingestion-time embedding calls still rely on Foundry's trusted-service bypass "
                    "(networkAcls.bypass = AzureServices). Keep it enabled.", kind="gotcha", title="Trusted-service bypass must stay on",
              src=[("Private agentic retrieval tutorial", learn("agents/how-to/foundry-iq-tutorial-private-overview"))])
    n1.place(cv, RX2, t.bottom + 26)
    n2 = Note(LANE, "The AI Search tool with a private Search service needs the standard agent setup + VNet injection + project MI (no keys). The basic setup cannot reach private Search. "
                    "Use the new Foundry portal for this scenario.", kind="info", title="Foundry side",
              src=[("Azure AI Search tool", learn("agents/how-to/tools/ai-search"))])
    n2.place(cv, RX2, n1.bottom + 20)
    n3 = Note(LANE, "Hand-built indexers need executionEnvironment = Private for private ingestion. The Serverless Developer tier (preview) supports private endpoints + IP firewall, "
                    "but not shared private links or NSP to data sources.", kind="info", title="Indexers and the serverless tier")
    n3.place(cv, RX2, n2.bottom + 20)
    n4 = Note(LANE, "configure-private-link says auto-generated indexers of indexed KS do not support the private execution environment; the private tutorial and KS pages use shared private links for blob KS. "
                    "Basic-tier footnotes also differ: unsupported to preserve stability vs supported on Basic / S1 created after 2024-04-03.",
              kind="warn", title="Docs disagree: private ingestion", src=[("Configure private link", learn("how-to/configure-private-link"))])
    n4.place(cv, RX2, n3.bottom + 20)
    y = max(p.bottom, n4.bottom) + 40

    cv.text(0, y, "Private agentic retrieval: the four-part tutorial (overview, inbound, outbound, retrieval)", size=24, color=get_theme("indigo").deep)
    y += 40
    cw = (W - 3 * GAP) // 4
    cards = [
        Card(cw, "1  Deploy the base", [
            "Template 15-private-network-standard-agent-setup",
            "VNet with an agent subnet (/24) and a private endpoint subnet (/24)",
            "Foundry + project, Search, Storage, Cosmos DB, ACR, private endpoints, DNS",
        ], theme="indigo", icon="vnet"),
        Card(cw, "2  Inbound", [
            "Private endpoint to the search service",
            "DNS zone privatelink.search.windows.net",
            "The agent reaches Search over the VNet with the project MI",
        ], theme="indigo", icon="private-endpoint"),
        Card(cw, "3  Outbound", [
            "Shared private links Search to Blob (blob) and Search to Foundry (openai_account), created with az rest, API 2025-05-01",
            "Approve the links on the target side",
            "Search MI gets Storage Blob Data Reader + Cognitive Services User",
        ], theme="indigo", icon="private-link"),
        Card(cw, "4  Retrieve privately", [
            "Deploy text-embedding-3-large + a GPT-5-family model",
            "Create the azureBlob KS (ResourceId= connection string, embeddingModel azureOpenAI) and the KB (extractiveData, minimal effort)",
            "Query over the private path",
        ], theme="indigo", icon="ai-search", src=[("Tutorial: private agentic retrieval", learn("agents/how-to/foundry-iq-tutorial-private-overview"))]),
    ]
    _, bottom = row(cv, 0, y, cards, gap=GAP)
    for i in range(3):
        connect(cv, cards[i], cards[i + 1], a_side="right", b_side="left", gap=4)
    return bottom


def band_features(cv, y):
    y = band(cv, y, 9, "Under the hood: classic search features and the bill",
             "what the knowledge layer is built from, and the meters that run (qualitative; numbers only where documented)", theme="yellow")
    cw = (LANE - GAP) // 2
    cv.text(0, y, "Classic Azure AI Search features inside the box", size=24, color=get_theme("cyan").deep)
    cv.text(RX2, y, f"Billing meters ({ASOF})", size=24, color=get_theme("yellow").deep)
    y += 42
    f1 = Card(cw, "Vector search", [
        "Available on all tiers and regions",
        "Up to 4,096 dimensions per vector field",
    ], theme="cyan", icon="ai-search", src=[("Vector search overview", S("vector-search-overview"))])
    f2 = Card(cw, "Hybrid search", [
        "One request carries search + vectorQueries",
        "Text and vector result sets are merged with Reciprocal Rank Fusion (RRF)",
    ], theme="cyan", icon="ai-search", src=[("Hybrid search overview", S("hybrid-search-overview"))])
    f3 = Card(cw, "Semantic ranker (L2)", [
        "Re-scores the top 50 results; 2,048-token summary per document",
        "rerankerScore 0-4; captions and answers",
        "Query rewrite (preview): up to 10 variants",
        "Free plan, then standard",
    ], theme="cyan", icon="ai-search", src=[("Semantic ranking", S("semantic-search-overview"))])
    f4 = Card(cw, "Integrated vectorization and skillsets", [
        "Indexer + skillset (Text Split or Content Understanding + AzureOpenAIEmbedding skill) + index vectorizer",
        "Custom skill; Foundry / AML catalog vectorizer (preview)",
        "Shared private link groups: openai_account, foundry_account, cognitiveservices_account, sites",
        "Skillsets = AI enrichment at indexing",
    ], theme="cyan", icon="ai-search", src=[("Integrated vectorization", S("vector-search-integrated-vectorization")),
                                              ("Skillsets", S("cognitive-search-working-with-skillsets"))])
    b1 = Card(cw, "Dedicated tiers", [
        "Search units by tier (replicas x partitions)",
        "Plus storage by tier",
    ], theme="yellow", icon="cost-management", src=[("Search tiers", S("search-sku-tier"))])
    b2 = Card(cw, "Serverless Developer tier", [
        "Capacity-unit hours + GB-months; scales to zero; billing began 2026-09-13",
        "Blog-sourced rates, West Central US: $0.288 per CU-hour + $0.239 per GB-month; 0.25 CU-minute increments",
        "Check the pricing page: its price cells are dynamic and were not captured",
    ], theme="yellow", icon="cost-management", badge="preview", src=[("Azure AI Search pricing", "https://azure.microsoft.com/en-us/pricing/details/search/")])
    b3 = Card(cw, "Agentic retrieval", [
        "knowledgeRetrieval property: free (default) or standard; Basic and above; management API 2026-03-01-preview",
        "Separate from semanticSearch since 2026-04-01",
        "Billed on retrieval tokens (semantic ranking) + Azure OpenAI tokens (planning, synthesis) on the KB's LLM deployment",
    ], theme="yellow", icon="cost-management", src=[("Agentic retrieval overview", S("agentic-retrieval-overview"))])
    b4 = Card(cw, "Also on the bill", [
        "Semantic ranker: free plan, then standard",
        "Skillset enrichment (for example image extraction, custom entity lookup)",
        "Confidential-compute surcharge",
        "Web KS (Bing) and Work IQ (Copilot Credits) bill outside Search",
    ], theme="yellow", icon="cost-management")
    r1 = max(f1.h, f2.h, b1.h, b2.h)
    r2 = max(f3.h, f4.h, b3.h, b4.h)
    for i, c in enumerate((f1, f2)):
        c.place(cv, i * (cw + GAP), y, h=r1)
    for i, c in enumerate((f3, f4)):
        c.place(cv, i * (cw + GAP), y + r1 + 28, h=r2)
    for i, c in enumerate((b1, b2)):
        c.place(cv, RX2 + i * (cw + GAP), y, h=r1)
    for i, c in enumerate((b3, b4)):
        c.place(cv, RX2 + i * (cw + GAP), y + r1 + 28, h=r2)
    return y + r1 + 28 + r2


def band_tiers(cv, y):
    y = band(cv, y, 10, "Tiers, replicas and partitions",
             f"documented limits only ({ASOF}); partitions add storage, replicas add query capacity and availability", theme="yellow")
    tw = 2300
    t = Table(
        [("", 300), "Free", "Basic", "S1", "S2", "S3", "S3 HD", "L1", "L2", "Serverless Developer (preview)"],
        [
            ["Max services per region", "1", "16", "16", "8", "6", "6", "6", "6", "5"],
            ["Partitions / replicas (max)", "shared", "3 / 3 (services after 2024-04-03)", "12 / 12", "12 / 12", "12 / 12", "3 / 12", "12 / 12", "12 / 12", "none"],
            ["Storage per partition (services after 2024-05-17)", "50 MB total", "15 GB", "160 GB", "512 GB", "1 TB", "1 TB", "2 TB", "4 TB", "GB-month metered"],
            ["Max indexes", "3", "15", "50", "200", "200", "1,000 per partition", "10", "10", "30 (blog)"],
            ["Max KS = max KB per service", "3", "5 or 15", "50", "200", "200", "1,000 per partition or 3,000 per service", "10", "10", "30"],
            ["Max KS per KB", "3", "5 or 10", "10", "10", "10", "10", "10", "10", "10"],
        ], w=tw, theme="yellow", size=15, head_size=16, first_col_theme="yellow", title="Capacity by tier", title_size=22)
    t.place(cv, 0, y)
    n0 = Note(tw, "Pay per capacity-unit-hour + GB-month, scales to zero, no replicas or partitions, no SLA, no tier migration, limited regions, no shared private links or NSP; "
                  "billing began 2026-09-13. Blog-sourced: 1 GB per index, 30 indexes per service, 5 services per subscription per region.",
              kind="preview", title="Serverless Developer tier (preview)", src=[("Search limits, quotas and capacity", S("search-limits-quotas-capacity"))])
    n0.place(cv, 0, t.bottom + 24)
    nx = tw + GAP
    nw = W - nx
    n1 = Note(nw, "Search unit (SU) = replicas x partitions; max 36 SU on S and L tiers. Basic services created before 2024-04-03: 1 partition, KS / KB limits 5, 2 GB partitions.",
              kind="info", title="Capacity math", src=[("Capacity planning", S("search-capacity-planning"))])
    n1.place(cv, nx, y)
    n2 = Note(nw, "The subscription-limits table says Basic max is 3 SU; the service-limits footnote and the pricing page say 9 SU (3 partitions x 3 replicas).",
              kind="warn", title="Docs disagree: Basic max search units")
    n2.place(cv, nx, n1.bottom + 20)
    n3 = Note(nw, "SLA needs >= 2 replicas (read) or >= 3 replicas (read-write). Zone redundancy is automatic on Basic and above with >= 2 replicas in availability-zone regions "
                  "(placement not guaranteed; scale out or in to rebalance).", kind="tip", title="Availability",
              src=[("Reliability in Azure AI Search", learn("azure/reliability/reliability-ai-search", base=""))])
    n3.place(cv, nx, n2.bottom + 20)
    n4 = Note(nw, "Single-region service with no built-in backup: rebuild from source. Free tier: one per subscription; may be deleted after extended inactivity.",
              kind="gotcha", title="Recovery")
    n4.place(cv, nx, n3.bottom + 20)
    n5 = Note(nw, "Confidential-compute services disable agentic retrieval, semantic ranker, query rewrite, skillsets and vectorization.",
              kind="warn", title="Confidential compute")
    n5.place(cv, nx, n4.bottom + 20)
    return max(n0.bottom, n5.bottom)


def band_conflicts(cv, y):
    y = band(cv, y, 11, "Where the docs disagree", f"as documented ({ASOF}): both values are shown - verify on the linked pages before you rely on either", theme="orange")
    t = Table(
        [("#", 50), ("Topic", 520), ("One page says", 1380), "Another page says"],
        [
            ["1", "Vector-store per-file token limit", "File-search page: 5,000,000", "Limits page: 2,000,000"],
            ["2", "Models supported for the KB LLM", "Foundry IQ FAQ: gpt-4o / gpt-4.1 / gpt-5", "Create-KB page: model families up to GPT-5.x; 4.x flagged deprecated"],
            ["3", "Basic tier maximum search units", "Subscription-limits table: 3 SU", "Service-limits footnote and pricing page: 9 SU (3 partitions x 3 replicas)"],
            ["4", "Private ingestion for auto-generated indexers", "configure-private-link: auto-generated indexers of indexed KS do not support the private execution environment",
             "Private tutorial and KS pages: shared private links for blob KS ingestion"],
            ["5", "Basic tier shared private links to Foundry", "One footnote: unsupported, to preserve stability", "Another footnote: embedding-model private connections supported on Basic / S1 created after 2024-04-03"],
            ["6", "File search in private networks", "File-search page: Azure Blob files unsupported in a BYO-VNet config", "Network tables: File search supported through a private endpoint"],
            ["7", "web KS under the GA API", "web is listed as a GA KS kind; models is optional unless a web KS is present", "The only GA effort (minimal) excludes web KS: exact GA behaviour not verified"],
            ["8", "Foundry IQ status", "Build 2026 blog: GA", "Foundry network table: (preview); AI Search docs: GA or preview by API version"],
        ], w=W, theme="orange", size=15, head_size=16, first_col_theme="orange", title="Documented contradictions", title_size=22)
    t.place(cv, 0, y)
    return t.bottom


def band_sources(cv, y):
    items = [
        ("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
        ("Connect a Foundry IQ knowledge base to Agent Service", learn("agents/how-to/foundry-iq-connect")),
        ("Azure AI Search tool", learn("agents/how-to/tools/ai-search")),
        ("File search tool", learn("agents/how-to/tools/file-search")),
        ("Private agentic retrieval tutorial (overview)", learn("agents/how-to/foundry-iq-tutorial-private-overview")),
        ("Configure private link for Foundry", learn("how-to/configure-private-link")),
        ("User delegation in Agent Service", learn("agents/concepts/user-delegation")),
        ("Agentic retrieval overview", S("agentic-retrieval-overview")),
        ("Knowledge sources overview", S("agentic-knowledge-source-overview")),
        ("Create a knowledge base", S("agentic-retrieval-how-to-create-knowledge-base")),
        ("Set the retrieval reasoning effort (preview)", S("agentic-retrieval-how-to-set-retrieval-reasoning-effort")),
        ("Migrate agentic retrieval code (GA vs preview)", S("agentic-retrieval-how-to-migrate")),
        ("Query a knowledge base (retrieve, MCP endpoint)", S("agentic-retrieval-how-to-retrieve")),
        ("Service limits, quotas and capacity", S("search-limits-quotas-capacity")),
    ]
    return sources(cv, 0, y, items, w=W, cols=3).bottom


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Azure AI Search", f"The knowledge layer behind Foundry agents: Foundry IQ knowledge bases, agentic retrieval and classic indexes ({ASOF})",
        icon="ai-search", w=W)
    y = bottom + 40
    y = band_summary(cv, y) + 70
    y = band_picture(cv, y) + 70
    y = band_versions(cv, y) + 70
    y = band_kb_ks(cv, y) + 70
    y = band_pipeline(cv, y) + 70
    y = band_ways(cv, y) + 70
    y = band_connect(cv, y) + 70
    y = band_identity(cv, y) + 70
    y = band_network(cv, y) + 70
    y = band_features(cv, y) + 70
    y = band_tiers(cv, y) + 70
    y = band_conflicts(cv, y) + 70
    band_sources(cv, y)
