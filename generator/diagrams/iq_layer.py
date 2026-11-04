"""Microsoft IQ - Work IQ, Fabric IQ, Foundry IQ and Web IQ as the enterprise-context layer around Foundry agents."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="iq-layer", title="Microsoft IQ: the enterprise-context layer", section="7", order=3,
    description="Work IQ, Fabric IQ, Foundry IQ and Web IQ: what each provides, how it reaches a Foundry agent (tool, Toolbox or knowledge-base source), auth and trimming, prerequisites, network support and status.",
    tags=["iq", "work-iq", "fabric-iq", "foundry-iq", "web-iq", "toolbox"],
)

# ------------------------------------------------------------------ geometry (one shared grid for the whole canvas)
W = 3548          # canvas width
IX = 28           # inner padding of the big panels
LW = 330          # left rail (Identity)
RW = 330          # right rail (Memory)
GAP = 36
MX = IX + LW + GAP        # main zone start (394)
CW = 690                  # one pillar column
MR = MX + 4 * CW          # main zone end (3154)
RX = MR + GAP             # right rail start (3190)

PILLARS = [
    dict(key="work", name="Work IQ", theme="blue", icon="m365"),
    dict(key="fabric", name="Fabric IQ", theme="cyan", icon="fabric"),
    dict(key="foundry", name="Foundry IQ", theme="teal", icon="ai-search"),
    dict(key="web", name="Web IQ", theme="violet", icon="globe"),
]
BY_KEY = {p["key"]: p for p in PILLARS}


# ------------------------------------------------------------------ small helpers
def pill(cv: Canvas, x: float, y: float, label: str, theme="gray", *, size=13, fill="solid", dash="solid") -> tuple[float, float]:
    th = get_theme(theme)
    label, _ = metrics.sanitize(label)
    w = metrics.line_width(label, size) + 18
    h = size * 1.25 + 7
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill if fill == "solid" else th.soft, style="solid", sw=1.5,
                rough=0, dash=dash)
        cv.text(x + 9, y + 3.5, label, size=size, color=th.deep)
    return w, h


def pills_right(cv: Canvas, right: float, y: float, items: list[tuple[str, str]], *, gap=8) -> None:
    """Draw status pills right-aligned so the last item ends at `right`."""
    x = right
    for label, th in reversed(items):
        w = metrics.line_width(label, 13) + 18
        x -= w
        pill(cv, x, y, label, th)
        x -= gap


def label_at(cv: Canvas, x: float, y: float, text: str, *, size=14, color=INK, bg=True, wrap=None) -> El:
    if wrap:
        text = "\n".join(metrics.wrap_text(text, wrap, size))
    tw, th_ = metrics.text_size(text, size)
    if bg:
        cv.rect(x - 4, y - 1, tw + 8, th_ + 2, stroke="transparent", fill="#ffffff", style="solid", sw=0, rough=0,
                opacity=92, round_=False)
    return cv.text(x, y, text, size=size, color=color, align="center" if "\n" in text else "left", w=tw)


def steps_panel(cv: Canvas, x: float, y: float, w: float, title: str, steps: list[str], theme: str, *,
                sub: str | None = None, src: list[tuple[str, str]] | None = None, size=15, min_h=0) -> Panel:
    """Dotted panel with numbered steps (numbered circles + wrapped text) and optional clickable Learn lines."""
    with cv.panel(x, y, title=title, sub=sub, theme=theme, style="dotted", fill="none", pad=22, w=w, min_h=min_h,
                  title_size=22, sub_size=14) as p:
        cy = p.iy
        tw = w - 44 - 44
        for i, s in enumerate(steps, 1):
            lines = metrics.wrap_text(s, tw * 0.97, size)
            h = len(lines) * size * metrics.line_ratio()
            numbered(cv, p.ix + 15, cy + 15, i, theme=theme, d=28, size=15)
            cv.text(p.ix + 44, cy + 2, "\n".join(lines), size=size, color=INK)
            cy += max(h + 4, 30) + 12
        if src:
            cy += 2
            for label, url in src:
                cv.text(p.ix, cy, f"Learn: {label}", size=12, color=LINK, link=url)
                cy += 16
    return p


class Seq(Sequence):
    """Kit Sequence with white label backgrounds, so message text stays readable where it crosses lifelines."""

    def msg(self, src: int, dst: int, text: str, *, dash="solid", num=None, note=None, color=INK, gap_after=0,
            end_head="arrow") -> float:
        cv = self.cv
        x1, x2 = self._cx(src), self._cx(dst)
        th = self.actors[src][1]
        lr = metrics.line_ratio()
        if src == dst:
            w = 70
            lines = metrics.wrap_text(text, self.spacing * 0.9, self.label_size)
            txt = "\n".join(lines)
            tw, th_ = metrics.text_size(txt, self.label_size)
            y = self.cur + 6
            cv.poly([(x1, y), (x1 + w, y), (x1 + w, y + 30), (x1 + 4, y + 30)], kind="arrow", stroke=color, sw=2,
                    dash=dash, end_head=end_head)
            if num is not None:
                numbered(cv, x1 + 12, y + 15, num, theme=th.name, d=26, size=15)
            cv.rect(x1 + w + 6, y - 6, tw + 8, th_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                    rough=0, opacity=95, round_=False)
            cv.text(x1 + w + 10, y - 4, txt, size=self.label_size, color=INK)
            self.cur = y + max(30, th_) + 26 + gap_after
            return y
        lo, hi = sorted((x1, x2))
        span = hi - lo
        lw = max(span - 50 - (30 if num is not None else 0), 120)
        lines = metrics.wrap_text(text, lw, self.label_size)
        txt = "\n".join(lines)
        tw, th_ = metrics.text_size(txt, self.label_size)
        y = self.cur + th_ + 14
        cv.poly([(x1 + (4 if x2 > x1 else -4), y), (x2 - (4 if x2 > x1 else -4), y)], kind="arrow", stroke=color,
                sw=2, dash=dash, end_head=end_head)
        tx = lo + (span - tw) / 2
        if num is not None:
            numbered(cv, lo + 22 if x2 > x1 else hi - 22, y - 16, num, theme=th.name, d=26, size=15)
            tx += 12
        cv.rect(tx - 5, y - th_ - 7, tw + 10, th_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                rough=0, opacity=95, round_=False)
        cv.text(tx, y - th_ - 5, txt, size=self.label_size, color=INK, align="center", w=tw)
        self.cur = y + 20 + gap_after
        return y


class Matrix:
    """Pillar-coloured comparison matrix: row labels + 4 tinted columns. Cells are lists of short items.
    Item prefixes: '! ' red (limit / not supported), '+ ' green, '@ ' monospace (endpoints)."""

    def __init__(self, label_w: float, col_w: float, rows: list[dict], *, size=14, label_size=17, pad_x=12, pad_y=9,
                 item_gap=5, head_h=62):
        self.label_w, self.col_w, self.rows = label_w, col_w, rows
        self.size, self.label_size, self.pad_x, self.pad_y, self.item_gap, self.head_h = (
            size, label_size, pad_x, pad_y, item_gap, head_h)
        lr = metrics.line_ratio()
        self.lay: list[dict] = []
        for r in rows:
            cells = []
            for items in r["cells"]:
                laid, hh = [], 0.0
                multi = len(items) > 1
                for raw in items:
                    kind, font, sz, t = "normal", metrics.HAND, size, raw
                    if t.startswith("! "):
                        kind, t = "warn", t[2:]
                    elif t.startswith("+ "):
                        kind, t = "good", t[2:]
                    if t.startswith("@ "):
                        font, sz, t = metrics.MONO, size - 1, t[2:]
                    t, _ = metrics.sanitize(t, font)
                    indent = 16 if multi else 0
                    lines = metrics.wrap_text(t, (col_w - 2 * pad_x - indent) * 0.965, sz, font)
                    h = len(lines) * sz * metrics.line_ratio(font)
                    laid.append(dict(kind=kind, font=font, size=sz, lines=lines, h=h, indent=indent, y=hh))
                    hh += h + item_gap
                cells.append(dict(items=laid, h=max(hh - item_gap, 0)))
            lab = metrics.wrap_text(r["label"], (label_w - 2 * pad_x) * 0.965, label_size)
            sub = metrics.wrap_text(r.get("sub", ""), (label_w - 2 * pad_x) * 0.965, 14) if r.get("sub") else []
            lab_h = len(lab) * label_size * lr + (len(sub) * 14 * lr + 3 if sub else 0)
            row_h = max(max(c["h"] for c in cells), lab_h) + 2 * pad_y
            self.lay.append(dict(cells=cells, lab=lab, sub=sub, h=row_h))
        self.w = label_w + 4 * col_w
        self.h = head_h + sum(r["h"] for r in self.lay)
        self.x = self.y = 0.0

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def place(self, cv: Canvas, x: float, y: float) -> "Matrix":
        self.x, self.y = x, y
        lw, cw, lr = self.label_w, self.col_w, metrics.line_ratio()
        cy = y + self.head_h
        for ri, r in enumerate(self.rows):
            rh = self.lay[ri]["h"]
            lt = get_theme(r.get("theme", "gray"))
            cv.rect(x + 1, cy + 1, lw - 2, rh - 2, stroke="transparent", fill=lt.fill, style="solid", sw=0,
                    round_=False, rough=0, opacity=80)
            for ci, p in enumerate(PILLARS):
                if ri % 2 == 1:
                    cv.rect(x + lw + ci * cw + 1, cy, cw - 2, rh, stroke="transparent", fill=get_theme(p["theme"]).soft,
                            style="solid", sw=0, round_=False, rough=0)
            cy += rh
        for ci, p in enumerate(PILLARS):
            th = get_theme(p["theme"])
            hx = x + lw + ci * cw
            cv.rect(hx, y, cw, self.head_h, stroke=th.stroke, fill=th.fill, style="solid", sw=2, round_=False, rough=1)
            place_icon(cv, p["icon"], hx + 14, y + (self.head_h - 36) / 2, 36)
            cv.text(hx + 62, y + (self.head_h - 22 * lr) / 2, p["name"], size=22, color=th.deep)
        cv.rect(x, y, lw, self.head_h, stroke="#495057", fill="#e9ecef", style="solid", sw=2, round_=False, rough=1)
        cv.text(x + self.pad_x, y + (self.head_h - 16 * lr * 2) / 2, "As documented\n(as of 2026-11-03)", size=16, color="#343a40")
        total_h = self.h
        cv.rect(x, y, self.w, total_h, stroke="#495057", fill="transparent", sw=2, round_=False, rough=1)
        for ci in range(0, 5):
            cx = x + lw + ci * cw
            cv.line((cx, y), (cx, y + total_h), stroke="#495057", sw=1, rough=1, opacity=70)
        cy = y + self.head_h
        for ri in range(len(self.rows) - 1):
            cy += self.lay[ri]["h"]
            cv.line((x, cy), (x + self.w, cy), stroke="#adb5bd", sw=1, rough=1, opacity=90)
        cy = y + self.head_h
        for ri, r in enumerate(self.rows):
            lay = self.lay[ri]
            lt = get_theme(r.get("theme", "gray"))
            ty = cy + self.pad_y
            cv.text(x + self.pad_x, ty, "\n".join(lay["lab"]), size=self.label_size, color=lt.deep)
            if lay["sub"]:
                cv.text(x + self.pad_x, ty + len(lay["lab"]) * self.label_size * lr + 3, "\n".join(lay["sub"]), size=14,
                        color="#495057")
            for ci, cell in enumerate(lay["cells"]):
                th = get_theme(PILLARS[ci]["theme"])
                cx = x + lw + ci * cw + self.pad_x
                for it in cell["items"]:
                    color = {"normal": INK, "warn": "#c92a2a", "good": "#2b8a3e"}[it["kind"]]
                    iy = ty + it["y"]
                    cv.text(cx + it["indent"], iy, "\n".join(it["lines"]), size=it["size"], color=color, font=it["font"])
                    if it["indent"]:
                        mc = "#e03131" if it["kind"] == "warn" else "#2f9e44" if it["kind"] == "good" else th.stroke
                        cv.ellipse(cx + 1, iy + it["size"] * 0.62 - 3, 7, 7, stroke=mc, fill=mc, style="solid", sw=1, rough=0)
            cy += lay["h"]
        cv.register("matrix", x, y, self.w, total_h)
        return self


# ====================================================================== sections
def banner(cv: Canvas, y: float) -> float:
    nw = (W - 2 * 40) / 3
    n1 = Note(nw, "Microsoft IQ brings together four interconnected capabilities so agents and Copilot are grounded in a shared, "
                  "continuously updated understanding of the organization: Work IQ (how people work), Fabric IQ (live state of the "
                  "business), Foundry IQ (curated institutional knowledge) and Web IQ (fresh real-world intelligence from the web). "
                  "It respects identity and permissions - it is not an AI model or LLM.",
              kind="key", title="Microsoft IQ is a solution layer, not a model", size=16,
              src=[("Microsoft IQ documentation", "https://learn.microsoft.com/en-us/microsoft-iq/"),
                   ("Microsoft IQ (microsoft.com)", "https://www.microsoft.com/en-us/ai/microsoft-iq")])
    n2 = Note(nw, "Web IQ is a separate API service (REST + MCP at api.microsoft.ai/v3) with its own Learn area and portal. It is "
                  "NOT the Foundry Web Search tool and NOT Grounding with Bing: different endpoint, billing and compliance. "
                  "Foundry's table of contents lists only Foundry IQ, Fabric IQ (preview) and Work IQ (preview), so Web IQ reaches "
                  "Foundry as an MCP tool, inside a Toolbox, or as an MCP knowledge source in a Foundry IQ knowledge base.",
              kind="info", theme="violet", title="Web IQ is the fourth pillar - and it is not the Web Search tool", size=16,
              src=[("Web IQ overview", learn("web-iq/overview", base="")),
                   ("Foundry web tools overview", learn("agents/how-to/tools/web-overview"))])
    n3 = Note(nw, "Top: how Identity, Toolbox, IQ and Memory compose around your agents. Then: three ways to plug an IQ in, a "
                  "connection matrix, auth and onboarding flows, related tools, scenarios and gotchas. GA and Preview badges are "
                  "as documented on 2026-11-03 and can change. [blog] marks a fact from a Microsoft blog or video rather than Learn.",
              kind="tip", title="How to read this canvas", size=16)
    _, nb = row(cv, 0, y, [n1, n2, n3], gap=40)
    leg = legend(cv, 0, nb + 24, [("Work IQ", "blue"), ("Fabric IQ", "cyan"), ("Foundry IQ", "teal"), ("Web IQ", "violet"),
                                  ("Toolbox / MCP", "orange"), ("Agents", "green"), ("Identity", "red")], size=16)
    return leg.y + leg.h


def composition(cv: Canvas, y_sec: float) -> float:
    section_header(cv, 0, y_sec, "How the layers compose: agents -> identity + Toolbox + IQ + Memory",
                   sub="Identity = who the agent acts as   |   Toolbox = how it reaches tools   |   IQ = what it knows   |   Memory = what it learned",
                   size=32, w=W)
    y_ag = y_sec + 96

    # ---- agents band
    with cv.panel(MX, y_ag, title="Foundry agents and other MCP clients", sub="who asks - and what the layer below gives them",
                  theme="green", style="dashed", fill="soft", pad=22, w=4 * CW, title_size=24, sub_size=15) as ag:
        agent_boxes = []
        bw, bgap = 720, 150
        bx = ag.ix + (4 * CW - 44 - (3 * bw + 2 * bgap)) / 2
        for label, sub, icon in (("Prompt agent", "attaches an IQ tool directly or a Toolbox", "agent"),
                                 ("Hosted agent", "your code; agent identity (agentic-identity) or managed identity", "container-apps"),
                                 ("Other MCP clients", "e.g. Agent Framework FoundryToolbox; need the Foundry Agent Consumer role", "mcp")):
            b = Box(bw, label, h=100, theme="green", sub=sub, icon=icon, icon_pos="left", icon_size=44, size=20, sub_size=15,
                    fill="solid")
            b.place(cv, bx, ag.iy + 2)
            agent_boxes.append(b)
            bx += bw + bgap

    y1 = ag.bottom + 120          # top of the context panel
    ty = y1 + IX                  # top of the Toolbox panel and of both rails

    # ---- measure what goes into the context panel
    holds = [Chip(t, theme=th, size=14) for t, th in (
        ("MCP", "orange"), ("Web search", "orange"), ("Azure AI Search", "orange"), ("Code interpreter", "orange"),
        ("File search", "orange"), ("OpenAPI", "orange"), ("A2A", "orange"), ("Browser automation", "orange"),
        ("Fabric IQ", "cyan"), ("Work IQ", "blue"), ("Tool search", "orange"), ("Skills (preview)", "orange"))]
    direct = [Chip(t, theme="gray", size=14, fill="soft", dash="dashed") for t in (
        "Function calling", "Grounding with Bing", "Computer use", "Image generation", "SharePoint", "Fabric data agent",
        "Azure Functions")]
    t2w, t3w = 800, 744
    t1w = 4 * CW - 36 - 24 * 2 - t2w - t3w
    holds_flow = ChipFlow(holds, t2w - 32, gap=8)
    direct_flow = ChipFlow(direct, t3w - 32, gap=8)
    t1 = Card(t1w, "Toolbox: one versioned MCP endpoint", [
        "Endpoint: {project}/toolboxes/{name}/mcp?api-version=v1 (pin a version with /versions/{v}/mcp)",
        "tool_search + call_tool; skills (preview); guardrails (RAI policy) apply on the toolbox",
        "SDK: project.toolboxes.create_version; Agent Framework: FoundryToolbox",
        "Per-tool auth: none, custom-keys, project-managed-identity, agentic-identity, oauth2, user-entra-token",
        "Consumers need Foundry Agent Consumer; same tenant only",
    ], theme="orange", icon="toolbox-icon", fill="hatch", body_size=15,
        src=[("Toolbox overview", learn("agents/concepts/toolbox-overview")), ("Toolbox how-to", learn("agents/how-to/tools/toolbox"))])
    holds_need = 18 + 40 + holds_flow.h + 16 + 22
    tb_h = max(t1.h, holds_need)

    pillar_body = {
        "work": [
            "Microsoft 365 work context: mail, meetings, OneDrive and SharePoint documents, Teams, people and org, Planner, enterprise search",
            "Honours permissions and sensitivity labels; Workspaces via SharePoint Embedded",
            "Usage is independent of Microsoft 365 Copilot licensing",
        ],
        "fabric": [
            "Live state of the business on Fabric and OneLake: entities, relationships, properties, actions, rules",
            "Items: Ontology (preview), Power BI semantic model, Planning, Graph (preview), Data agent, Operations agent",
            "Ontology has an MCP server (preview; service principals currently unsupported)",
            "A Fabric data agent can attach an Azure AI Search index (preview)",
        ],
        "foundry": [
            "Managed knowledge layer on Azure AI Search: knowledge bases + knowledge sources + agentic retrieval",
            "Permission-aware and reusable across agents; Search required, Agent Service not required, LLM optional",
            "Also a router: one KB can federate Work IQ, Fabric (ontology, data agent) and Web IQ as knowledge sources",
        ],
        "web": [
            "AI-native APIs: Web Search, News, Images, Videos, Browse (GA) and Auto (beta, enabled on request)",
            "Returns ranked, citation-ready passages and evidence objects; not an LLM; public web only",
            "SDKs: Python webiq (3.11+), TypeScript @microsoft/webiq (Node 22.18+); 164 ms p95 latency (Learn)",
        ],
    }
    pillar_sub = {
        "work": "how people work: people, collaboration, workflows",
        "fabric": "the live state of the business",
        "foundry": "curated institutional knowledge",
        "web": "fresh, real-world intelligence from the web",
    }
    pillar_src = {
        "work": [("Work IQ in Foundry", learn("agents/how-to/tools/work-iq")),
                 ("Work IQ overview", learn("microsoft-365/copilot/extensibility/work-iq", base=""))],
        "fabric": [("Fabric IQ tool", learn("agents/how-to/tools/fabric-iq")),
                   ("Fabric IQ overview", learn("fabric/iq/overview", base=""))],
        "foundry": [("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
                    ("Connect a KB to an agent", learn("agents/how-to/foundry-iq-connect"))],
        "web": [("Web IQ overview", learn("web-iq/overview", base="")),
                ("Web IQ MCP integration", learn("web-iq/integrations/mcp", base=""))],
    }
    pcards = [Card(CW - 20, p["name"], pillar_body[p["key"]], theme=p["theme"], icon=p["icon"], subtitle=pillar_sub[p["key"]],
                   body_size=15, src=pillar_src[p["key"]]) for p in PILLARS]
    id_card = Card(LW, "Identity", [
        "# who the agent acts as",
        "Project managed identity (project-managed-identity): shared, project-level access",
        "Agent identity (agentic-identity): Entra blueprint + one identity per agent; starts with no permissions",
        "On-behalf-of user (UserEntraToken, AgentOnBehalfOfUser): the signed-in user's rights",
        "In-conversation OAuth (oauth2): oauth_consent_request when consent is missing",
        "Keys (custom-keys, API key) or none",
        "! Agent identity acting on behalf of a user is Preview and needs the AgentBlueprint endpoint scheme",
    ], theme="red", icon="managed-identity", body_size=15,
        src=[("Tool authentication", learn("agents/how-to/tools/tool-authentication")),
             ("User delegation", learn("agents/concepts/user-delegation")),
             ("Agent identity", learn("agents/concepts/agent-identity"))])
    mem_card = Card(RW, "Memory", [
        "# what it learned",
        "Foundry Memory (preview): user profile, chat summary and procedural memory",
        "Or do it yourself with the Cosmos DB Agent Memory Toolkit",
        "Needs chat + embedding model deployments",
    ], theme="teal", fill="soft", dash="dashed", body_size=15, badge="preview",
        src=[("What is memory?", learn("agents/concepts/what-is-memory"))])

    with cv.panel(0, y1, title=None, theme="teal", style="dotted", fill="none", pad=IX, w=W) as ctx:
        # ---- Toolbox band
        with cv.panel(MX, ty, title="Toolbox", sub="how it reaches tools - one endpoint in front of many tools",
                      theme="orange", style="dashed", fill="soft", pad=18, w=4 * CW, title_size=24, sub_size=15) as tb:
            t1.place(cv, tb.ix, tb.iy, h=tb_h)
            with cv.panel(t1.right + 24, tb.iy, title="A Toolbox can hold", theme="orange", style="solid", fill="soft", pad=16,
                          w=t2w, h=tb_h, title_size=20) as hp:
                holds_flow.place(cv, hp.ix, hp.iy)
                cv.text(hp.ix, tb.iy + tb_h - 30, "Learn: Toolbox network isolation", size=12, color=LINK,
                        link=learn("agents/how-to/tools/toolbox-network-isolation"))
            with cv.panel(hp.right + 24, tb.iy, title="Direct only (not in a Toolbox)", theme="gray", style="dashed", fill="soft",
                          pad=16, w=t3w, h=tb_h, title_size=20) as dp:
                direct_flow.place(cv, dp.ix, dp.iy)
        # ---- orange bus from the Toolbox to the four pillars
        centers = [MX + i * CW + CW / 2 for i in range(4)]
        bus_y = tb.bottom + 50
        cards_top = bus_y + 80
        arrow(cv, [(MX + 2 * CW, tb.bottom + 4), (MX + 2 * CW, bus_y)], color="#e8590c", sw=3, end_head=None)
        arrow(cv, [(centers[0], bus_y), (centers[3], bus_y)], color="#e8590c", sw=3, end_head=None)
        tool_labels = ["work_iq_preview (A2A)", "fabric_iq_preview (MCP)", "knowledge_base_retrieve (MCP)",
                       "MCP: api.microsoft.ai/v3/mcp"]
        for c, lab in zip(centers, tool_labels):
            arrow(cv, [(c, bus_y), (c, cards_top - 6)], color="#e8590c", sw=3)
            label_at(cv, c + 14, bus_y + 26, lab, size=15, color="#d9480f")
        # ---- the four pillar cards (column headers of the matrix below)
        _, cards_bottom = row(cv, MX + 10, cards_top, pcards, gap=20)
        pills_right(cv, pcards[0].right - 16, pcards[0].y + 15, [("Preview", "orange")])
        pills_right(cv, pcards[1].right - 16, pcards[1].y + 15, [("Preview", "orange")])
        pills_right(cv, pcards[2].right - 16, pcards[2].y + 15, [("GA", "green"), ("Preview", "orange")])
        pills_right(cv, pcards[3].right - 16, pcards[3].y + 15, [("GA", "green"), ("Auto: beta", "yellow")])
        # ---- dashed federation bus: a Foundry IQ KB can hold the other three as knowledge sources
        fed_y = cards_bottom + 52
        teal = get_theme("teal").stroke
        arrow(cv, [(centers[2], cards_bottom + 4), (centers[2], fed_y)], color=teal, sw=3, dash="dashed", end_head=None)
        arrow(cv, [(centers[2], fed_y), (centers[0], fed_y), (centers[0], cards_bottom + 6)], color=teal, sw=3, dash="dashed")
        arrow(cv, [(centers[1], fed_y), (centers[1], cards_bottom + 6)], color=teal, sw=3, dash="dashed")
        arrow(cv, [(centers[2], fed_y), (centers[3], fed_y), (centers[3], cards_bottom + 6)], color=teal, sw=3, dash="dashed")
        fed_lab = label_at(cv, (centers[0] + centers[2]) / 2 - 330, fed_y + 12,
                           "Path C: a Foundry IQ knowledge base can hold Work IQ, Fabric (ontology, data agent) and Web IQ "
                           "(MCP) as knowledge sources", size=15, color="#087f5b", wrap=700)
        rail_h = max(fed_lab.y + fed_lab.h - ty, id_card.h + 20 + 400, mem_card.h + 20 + 380)
        # ---- rails: Identity (left) and Memory (right), each with a second block that adds per-IQ detail
        id_card.place(cv, IX, ty)
        with cv.panel(IX, id_card.bottom + 20, title="Who is the actor, per IQ", theme="red", style="dotted", fill="soft",
                      pad=14, w=LW, h=ty + rail_h - id_card.bottom - 20, title_size=18) as ip:
            by = ip.iy
            for key, txt in (("work", "AgentOnBehalfOfUser; OAuth2 with admin consent"),
                             ("fabric", "OBO user; OAuth (managed or custom app)"),
                             ("foundry", "project MI; OBO user; agentic-identity for hosted agents"),
                             ("web", "API key; Entra client credentials; MI or Agent ID")):
                p = BY_KEY[key]
                bb = Box(LW - 28, p["name"], h=72, theme=p["theme"], sub=txt, size=17, sub_size=13, pad=8).place(cv, ip.ix, by)
                by += bb.h + 10
        mem_card.place(cv, RX, ty)
        with cv.panel(RX, mem_card.bottom + 20, title="Which store for what?", theme="teal", style="dotted", fill="soft",
                      pad=14, w=RW, h=ty + rail_h - mem_card.bottom - 20, title_size=18) as mp:
            by = mp.iy
            for lab, sub, th, dash in (("Memory", "learned user context", "teal", "dashed"),
                                       ("Foundry IQ", "curated organizational content", "teal", "solid"),
                                       ("File search", "user-provided documents", "gray", "solid")):
                bb = Box(RW - 28, lab, h=84, theme=th, sub=sub, size=18, sub_size=14, dash=dash, pad=8,
                         fill="soft" if th == "gray" else "solid").place(cv, mp.ix, by)
                by += bb.h + 10
            cv.text(mp.ix, by + 2, "Learn: What is memory?", size=12, color=LINK, link=learn("agents/concepts/what-is-memory"))

    # tab straddling the top border of the context panel
    tab_txt = "Enterprise context layer: identity + Toolbox + IQ + memory"
    tw_, th_ = metrics.text_size(tab_txt, 22)
    tab_x = (agent_boxes[0].cx + agent_boxes[1].cx) / 2 - tw_ / 2
    with cv.group():
        cv.rect(tab_x - 18, y1 - 20, tw_ + 36, th_ + 14, stroke=get_theme("teal").stroke, fill=get_theme("teal").fill,
                style="solid", sw=2)
        cv.text(tab_x, y1 - 13, tab_txt, size=22, color=get_theme("teal").deep)

    # ---- arrows from the agents into the layer
    for b in agent_boxes:
        arrow(cv, [(b.cx, b.bottom + 6), (b.cx, ty - 4)], color="#2b8a3e", sw=3)
    label_at(cv, agent_boxes[1].cx + 14, ag.bottom + 26, "MCP: tool_search + call_tool", size=15, color="#2b8a3e")
    ym = ag.y + ag.h * 0.55
    arrow(cv, [(MX - 6, ym), (IX + LW / 2, ym), (IX + LW / 2, ty - 4)], color="#e03131", sw=3, label="acts as", label_t=0.2,
          label_size=15, label_color="#c92a2a", label_dy=-2)
    arrow(cv, [(MR + 6, ym), (RX + RW / 2, ym), (RX + RW / 2, ty - 4)], color=get_theme("teal").stroke, sw=3, dash="dotted",
          start_head="arrow", label="recall + store", label_t=0.2, label_size=15, label_color="#087f5b", label_dy=-2)
    return ctx.bottom


def three_ways(cv: Canvas, y2: float) -> float:
    section_header(cv, 0, y2, "Three ways to plug an IQ into an agent",
                   sub="the same four IQs, three attachment paths - pick by how many agents, how many sources and how much control you need",
                   size=32, w=W)
    y3 = y2 + 96
    ax, aw = IX, 260
    cx1, cw1 = ax + aw + 120, 650
    cx2, cw2 = cx1 + cw1 + 110, 820
    cx3, cw3 = cx2 + cw2 + 110, 690
    cx4 = cx3 + cw3 + 60
    cw4 = W - IX - cx4
    row_h, row_gap = 124, 22
    lanes = [
        dict(k="A", title="A. Attach the tool directly", sub="MCPTool, A2A, fabric_iq_preview or work_iq_preview on the agent",
             auth="Per-tool connection",
             auth_sub="RemoteTool (Foundry IQ, project MI), RemoteA2A (Work IQ, OAuth2), Fabric item connection (OBO or OAuth), custom keys for Web IQ [blog]",
             reach="The IQ endpoint itself", reach_sub="KB MCP endpoint, Fabric MCP URL, Work IQ A2A endpoint, api.microsoft.ai/v3/mcp",
             note=("tip", "Simplest path, but configured per agent. Web IQ has no native tool type: it is a generic MCP tool.")),
        dict(k="B", title="B. Attach a Toolbox", sub="one versioned MCP endpoint with tool_search + call_tool and guardrails",
             auth="Per-tool auth inside the toolbox", auth_sub="none, custom-keys, project-managed-identity, agentic-identity, oauth2, user-entra-token",
             reach="The same endpoints, as toolbox tools", reach_sub="Fabric IQ and Work IQ as native tools; Foundry IQ and Web IQ as MCP entries",
             note=("key", "Recommended way to bundle the IQs for Foundry agents [blog]. Reusable across agents; network behaviour follows the project.")),
        dict(k="C", title="C. Inside a Foundry IQ knowledge base", sub="the agent only calls knowledge_base_retrieve on the KB MCP endpoint",
             auth="Per-source permission headers",
             auth_sub="x-ms-query-source-authorization (user token), x-ms-query-work-iq-source-authorization, stored x-apikey (Web IQ MCP source)",
             reach="Knowledge sources in the KB", reach_sub="Work IQ source, Fabric Ontology / Data Agent source, MCP source (Web IQ tool web)",
             note=("warn", "One retrieval with planning, rerank and synthesis. These source kinds are preview; Work IQ adds 40-60 s+ latency.")),
    ]
    lane_h = 3 * row_h + 2 * row_gap
    with cv.panel(0, y3, title=None, theme="gray", style="dotted", fill="none", pad=IX, w=W) as lp:
        top = y3 + IX + 34
        for cx, txt in ((cx1, "1  What you attach to the agent"), (cx2, "2  How the call is authenticated"),
                        (cx3, "3  What it reaches"), (cx4, "Notes")):
            cv.text(cx, y3 + IX - 4, txt, size=18, color="#495057")
        Box(aw, "Foundry agent", h=lane_h, theme="green", sub="prompt or hosted", icon="agent", size=22, sub_size=15,
            icon_size=44).place(cv, ax, top)
        for i, ln in enumerate(lanes):
            ry = top + i * (row_h + row_gap)
            b1 = Box(cw1, ln["title"], h=row_h, theme="orange", sub=ln["sub"], size=19, sub_size=15).place(cv, cx1, ry)
            b2 = Box(cw2, ln["auth"], h=row_h, theme="red", sub=ln["auth_sub"], size=19, sub_size=15).place(cv, cx2, ry)
            b3 = Box(cw3, ln["reach"], h=row_h, theme="teal", sub=ln["reach_sub"], size=19, sub_size=15).place(cv, cx3, ry)
            nt = Note(cw4, ln["note"][1], kind=ln["note"][0], size=15)
            nt.place(cv, cx4, ry + (row_h - nt.h) / 2)
            arrow(cv, [(ax + aw + 6, ry + row_h / 2), (cx1 - 6, ry + row_h / 2)], color="#2b8a3e", sw=3, num=ln["k"],
                  num_theme="green")
            connect(cv, b1, b2, a_side="right", b_side="left", sw=2)
            connect(cv, b2, b3, a_side="right", b_side="left", sw=2)
    return lp.bottom


def matrix_section(cv: Canvas, y4: float) -> float:
    section_header(cv, 0, y4, "Connection matrix: how each IQ reaches a Foundry agent",
                   sub="prerequisites, identity, trimming, network and billing side by side - the pillar cards above are the column headers",
                   size=32, w=W)
    y5 = y4 + 100
    rows1 = [
        dict(label="Status", sub="GA or preview, as documented", theme="gray", cells=[
            ["Preview in the Foundry docs (work_iq_preview)", "Work IQ APIs GA 2026-06-16 per a partner recap blog [blog]"],
            ["Preview (Foundry tool type fabric_iq_preview)", "Ontology and Graph items are preview in Fabric"],
            ["GA: knowledge bases and minimal retrieval effort (Search API 2026-04-01)",
             "Preview: LLM query planning, answer synthesis, most knowledge-source kinds (2026-08-01-preview)",
             "Foundry's network page still labels it '(preview)'"],
            ["GA: Web Search, News, Images, Videos, Browse", "Auto = beta, enabled on request", "Pricing effective 2026-10-16"]]),
        dict(label="Foundry surface", sub="what the agent attaches", theme="orange", cells=[
            ["Tool type work_iq_preview (SDK WorkIQPreviewTool; Toolbox WorkIQPreviewToolboxTool) over A2A", "Also the Work IQ MCP tools"],
            ["Tool type fabric_iq_preview (SDK FabricIQPreviewTool; Toolbox FabricIQPreviewToolboxTool)", "MCP endpoints per item type"],
            ["MCP tool knowledge_base_retrieve (the only supported tool) on the KB's MCP endpoint"],
            ["Generic MCP tool, or a Toolbox MCP entry", "Or an MCP knowledge source inside a Foundry IQ KB (source kind mcp, tool web)",
             "! No Web IQ tool type in the Foundry docs"]]),
        dict(label="Endpoint", sub="where the call goes", theme="orange", cells=[
            ["@ https://workiq.svc.cloud.microsoft/a2a/", "A2A v1.0 via header A2A-Version: 1.0 (default 0.3); method SendMessage"],
            ["@ ontology: https://{host}/v1/mcp/dataPlane/workspaces/{workspaceId}/items/{itemId}/ontologyEndpoint",
             "@ data agent: https://{host}/v1/mcp/workspaces/{workspaceId}/dataagents/{dataAgentId}/agent",
             "@ semantic model: https://{host}/v1/mcp/fabricaihub/integrations/m365",
             "Host is usually api.fabric.microsoft.com (workspace private-link host differs)"],
            ["@ {search}/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview"],
            ["@ https://api.microsoft.ai/v3/mcp", "Tools web, videos, browse, news, images - scoped to the AppID's allowed services",
             "@ REST: https://api.microsoft.ai/v3/..."]]),
        dict(label="Auth to the IQ", sub="how the connection authenticates", theme="red", cells=[
            ["OAuth2 delegated: azd ai connection create --kind remote-a2a --auth-type oauth2",
             "Scopes api://workiq.svc.cloud.microsoft/WorkIQAgent.Ask + offline_access", "Connection category RemoteA2A"],
            ["Incoming Entra user context (OBO; API values UserEntraToken / AgentOnBehalfOfUser) or OAuth (managed or custom app)",
             "Data agent also accepts a user or service-principal token for direct MCP clients (scope https://api.fabric.microsoft.com/.default)"],
            ["Project managed identity via a RemoteTool connection (audience https://search.azure.com/)", "OBO user for source authorization"],
            ["API key in header x-apikey, or Entra client credentials (scope https://api.microsoft.ai/.default; bind the Entra app client ID to the AppID)",
             "Hosted agents can use managed identity or Agent ID"]]),
        dict(label="Who is the actor", sub="the identity the IQ sees", theme="red", cells=[
            ["AgentOnBehalfOfUser; OAuth2 with admin consent", "! Not supported: app-only access, UserEntraToken"],
            ["OBO user; OAuth (managed or custom app)", "! Not supported: service principal for the ontology MCP (currently)"],
            ["Project MI (connection); OBO user for source authorization; hosted agents: agentic-identity",
             "! Not supported: a user token on an agentic-identity connection"],
            ["API key; Entra client credentials; MI or Agent ID for hosted agents", "! Not supported: Azure RBAC, Private Link"]]),
        dict(label="Permission trimming", sub="whose rights limit the results", theme="red", cells=[
            ["Microsoft 365 permissions and sensitivity labels of the signed-in user"],
            ["Fabric item permissions of the calling user"],
            ["Per-user ACLs via the x-ms-query-source-authorization header"],
            ["None - public web only"]]),
    ]
    rows2 = [
        dict(label="Prerequisites", sub="what must exist first", theme="gray", cells=[
            ["One-time Global Admin: provision the Work IQ service principal (app id fdcc1f02-fc51-4226-8753-f668596af7f7), a single-tenant Entra app and admin consent for WorkIQAgent.Ask",
             "Foundry User at both account and project scope"],
            ["Item must be published (ontology, semantic model or data agent)",
             "Fabric capacity F2+ or P1+ with the full Fabric stack (not Power BI-only regions) and a Fabric license",
             "Data agent and its sources on same-region capacities", "Foundry User + Foundry Project Manager",
             "Custom OAuth app: delegated Item.Execute.All, Item.Read.All (+ offline_access), DataAgent.Execute.All; admin consent by a Global Admin"],
            ["Azure AI Search service + a knowledge base", "Foundry User (use) + Foundry Project Manager (create the connection)",
             "Project MI: Search Index Data Reader; Search service MI: Cognitive Services User when the KB has an LLM"],
            ["Paid Azure subscription (credits don't work)", "Azure Web IQ resource: metering and billing only, not in the request path",
             "AppID issued when the resource is connected in the Web IQ portal (default 15 QPS, HTTP 429 above)"]]),
        dict(label="Network (project isolated)", sub="behaviour in a network-isolated project", theme="indigo", cells=[
            ["! Not supported in network-isolated projects", "Public HTTPS endpoint (via the single-tenant data proxy) even with BYO VNet"],
            ["Partial: data agent = tenant + workspace private link; ontology = tenant-level private link; semantic model = public only"],
            ["Supported via MCP", "Foundry's network table labels it '(preview)'"],
            ["Public endpoint only: no Private Link, VNet or IP allow-list", "Can sit behind API Management"]]),
        dict(label="Billing", sub="who gets the bill", theme="yellow", cells=[
            ["Work IQ API usage in Copilot Credits [blog]", "Connector-backed Microsoft 365 tools may need a Microsoft 365 Copilot license per user"],
            ["Fabric capacity"],
            ["Azure AI Search + Azure OpenAI tokens"],
            ["Per 1K calls: /web, /video, /news, /images $7.00; /browse $1.00 (effective 2026-10-16)", "Auto: free while in beta"]]),
        dict(label="Data handling", sub="retention and compliance", theme="grape", cells=[
            ["Permissions and labels are enforced", "Compliance terms: check the Work IQ docs"],
            ["May leave the Azure compliance boundary"],
            ["Your Search service + the KB's model deployment", "Web knowledge source: the DPA does not apply"],
            ["Queries are logged (Microsoft is the data controller); excluded from the DPA and EU Data Boundary; no residency commitments",
             "Response content cannot be cached or stored; no PII masking", "SafeSearch strict by default; LinkedIn excluded"]]),
        dict(label="Gotchas", sub="what bites in practice", theme="red", cells=[
            ["Connection fields cannot be edited after creation", "Delegated only (no app-only)",
             "! Actions can write: Write tools create, update, delete, do_action [blog]"],
            ["Only the data-agent endpoint supports background mode", "Page recommends gpt-5.4 / opus 4.7 for semantic models",
             "! The Fabric data agent tool retires 2026-11-06"],
            ["Needs azure-ai-projects >= 2.0.0; hub-based projects are not supported",
             "GA vs preview is by API version; the Azure and Foundry portals give preview-only access"],
            ["! Foundry docs have no Web IQ tool type", "A Foundry blog calls Web IQ via the MCP knowledge source 'limited access' [blog]"]]),
    ]
    m1 = Matrix(MX, CW, rows1)
    m1.place(cv, 0, y5)
    m2 = Matrix(MX, CW, rows2)
    m2.place(cv, 0, m1.bottom + 40)

    # right rail: callouts next to the matrix
    rn1 = Note(RW + 28, "Foundry IQ: GA (Build 2026 blog) vs '(preview)' (Foundry network table) vs GA or preview by API version (AI Search docs). "
                        "Work IQ: GA (partner blog, video Q&A) vs preview (Foundry tool; AI Search knowledge source). "
                        "Treat labels as 'as documented 2026-11-03' and re-check before you commit.",
               kind="gotcha", title="Docs disagree: status", size=15)
    rn2 = Note(RW + 28, "A Foundry blog claims 'zero data retention' for Foundry IQ and 'limited access' for Web IQ via the MCP source. "
                        "The Web IQ FAQ says queries are logged and Zero Query Logging is approval-based, not self-serve. "
                        "A July video's 'private preview' and finance / sports tools are outdated against Learn.",
               kind="gotcha", title="Docs disagree: Web IQ data", size=15,
               src=[("Web IQ FAQ", learn("web-iq/resources/faq", base=""))])
    rn3 = Note(RW + 28, "Work IQ MCP tool names differ between a write-up and other listings. The write-up lists 10 generic tools: "
                        "ask, list_agents, search_paths, get_schema, fetch, call_function, create, update, delete, do_action; "
                        "allowed paths /me/, /users/, /sites/ [blog].",
               kind="info", title="Tool names can change", size=15)
    rn4 = Note(RW + 28, "Web IQ Auto is beta and free while in beta; POST /v3/auto with mode fast or advanced returns typed evidence "
                        "(text, image, video, weather, time zone) with citations.",
               kind="preview", title="Web IQ Auto (beta)", size=15, src=[("Auto reference", learn("web-iq/reference/auto", base=""))])
    col(cv, RX - 14, y5, [rn1, rn2, rn3, rn4], gap=22)
    return m2.bottom


def flows(cv: Canvas, y6: float) -> float:
    section_header(cv, 0, y6, "Flows: auth and onboarding, step by step",
                   sub="Work IQ as a sequence (the most involved handshake), plus the Fabric IQ, Web IQ and Work-IQ-in-a-KB recipes",
                   size=32, w=W)
    y7 = y6 + 100
    seq = Seq(cv, 0, y7, [("Admin / developer", "red", "users"), ("End user", "gray", "user"),
                          ("Agent Service", "green", "foundry"), ("Work IQ (A2A)", "blue", "m365")],
              spacing=340, head_w=200, head_h=58, size=15, label_size=14)
    seq.msg(0, 3, "One-time (Global Admin): provision the Work IQ service principal, create a single-tenant Entra app, grant admin consent for WorkIQAgent.Ask", num=1)
    seq.msg(0, 2, "Create the RemoteA2A connection (OAuth2; scopes api://workiq.svc.cloud.microsoft/WorkIQAgent.Ask + offline_access; cannot be edited later), then attach work_iq_preview directly or in a Toolbox", num=2)
    seq.msg(1, 2, "User asks a question", num=3)
    seq.msg(2, 2, "Exchange the user's token (audience api://workiq.svc.cloud.microsoft) on behalf of the user", num=4)
    seq.msg(2, 3, "SendMessage to https://workiq.svc.cloud.microsoft/a2a/", num=5)
    seq.msg(3, 3, "Reason over the user's mail, meetings, files and Teams within their permissions and labels", num=6)
    seq.msg(3, 2, "Answer returns to the agent", dash="dashed")
    seq.msg(2, 1, "Agent answers the user", dash="dashed")
    sbot = seq.end()
    sx = 200 + 3 * 340 + 60
    spw = (W - sx - 2 * 36) / 3
    p1 = steps_panel(cv, sx, y7, spw, "Fabric IQ tool", [
        "Publish the item: ontology, semantic model or data agent",
        "Check capacity and licences (F2+ / P1+, full Fabric stack)",
        "Create the connection: OBO, or OAuth with a custom app (admin consent)",
        "Attach fabric_iq_preview to the agent (Toolbox recommended)",
        "Agent calls the tool; Agent Service calls the item's Fabric MCP URL with the user's token",
        "Fabric enforces the user's item permissions",
        "Result returns documents[] (title + url) for citations"], "cyan", sub="onboarding and call",
        src=[("Fabric IQ tool", learn("agents/how-to/tools/fabric-iq"))])
    p2 = steps_panel(cv, sx + spw + 36, y7, spw, "Web IQ onboarding", [
        "Use a paid Azure subscription; create the Azure Web IQ resource (portal or CLI)",
        "In the Web IQ portal choose Get Started as the subscription owner and connect the resource: an AppID is issued",
        "Get an API key from Profile Management, or bind Entra client credentials to the AppID",
        "In Foundry add an MCP tool or Toolbox entry for api.microsoft.ai/v3/mcp with header x-apikey (project connection 'custom keys' [blog]) - or add an MCP knowledge source to a KB (stored header x-apikey, tool web)",
        "Agent calls web / news / browse; stay under the AppID's QPS (default 15) to avoid HTTP 429"],
        "violet", sub="from subscription to first call",
        src=[("Deploy in the Azure portal", learn("web-iq/get-started/deploy-azure-portal", base="")),
             ("Authentication", learn("web-iq/get-started/authentication", base=""))])
    p3 = steps_panel(cv, sx + 2 * (spw + 36), y7, spw, "Work IQ inside a KB: token chain", [
        "User token (audience Search) is sent on retrieve",
        "Search exchanges it with a federated credential on the search service's managed identity for the customer's Entra app (scope api://<appId>/access_as_user)",
        "Header x-ms-query-work-iq-source-authorization carries the user assertion",
        "Work IQ returns results; allow maxRuntimeInSeconds >= 120"],
        "blue", sub="path C, preview",
        src=[("Work IQ knowledge source", learn("azure/search/agentic-knowledge-source-how-to-work-iq", base=""))])
    return max(sbot, p1.bottom, p2.bottom, p3.bottom)


def related(cv: Canvas, y8: float) -> float:
    section_header(cv, 0, y8, "Related tools that sit beside the IQs",
                   sub="the Fabric data agent tool is being replaced; SharePoint and the web tools are separate surfaces", size=32, w=W)
    y9 = y8 + 100
    cw4c = (W - 3 * 40) / 4
    rc1 = Card(cw4c, "Fabric data agent tool", [
        "fabric_dataagent_preview is scheduled for deprecation on 2026-11-06 (as of 2026-11-03)",
        "Migrate to the Fabric IQ tool: portal Tools -> Browse all tools -> Fabric IQ (OneLake Catalog)",
        "Old connection: category CustomKeys with workspace_id / artifact_id; OBO only; no service principal",
        "! Not supported in network-isolated projects (workspace-level private link unsupported)",
    ], theme="red", icon="fabric", badge="retiring",
        src=[("Fabric data agent tool", learn("agents/how-to/tools/fabric")), ("Migrate to Fabric IQ", learn("agents/how-to/tools/fabric-iq"))])
    rc2 = Card(cw4c, "SharePoint tool", [
        "sharepoint_grounding_preview: uses the Copilot Retrieval API",
        "Needs a Microsoft 365 Copilot license or pay-as-you-go; user (OBO) auth only; same tenant",
        "One per agent; limits: 25 results, 200 requests/user/hour, 1,500-char query; text only",
        "File types for hybrid: .doc .docx .pptx .pdf .aspx .one",
        "Public endpoint (works in isolated projects); not in a Toolbox",
        "! Does not work when the agent is published to Teams",
    ], theme="teal", icon="sharepoint", badge="preview", src=[("SharePoint tool", learn("agents/how-to/tools/sharepoint"))])
    rc3 = Card(cw4c, "Foundry web tools", [
        "Web Search (GA): Microsoft-managed Grounding with Bing resource; user_location, search_context_size low / medium / high",
        "Grounding with Bing Search (GA): your Bing resource; count, freshness, market, set_lang; non-OpenAI models on Azure",
        "Grounding with Bing Custom Search (preview)",
        "! First Party Consumption Services: DPA does not apply, data leaves the Azure compliance and geo boundary, public endpoints, no private endpoint",
    ], theme="cyan", icon="bing", src=[("Web tools overview", learn("agents/how-to/tools/web-overview")), ("Web Search tool", learn("agents/how-to/tools/web-search"))])
    rc4 = Card(cw4c, "Work IQ MCP surface", [
        "10 generic tools in 4 groups: Chat (ask, list_agents), Schema (search_paths, get_schema), Read (fetch, call_function), Write (create, update, delete, do_action)",
        "Allowed path prefixes /me/, /users/, /sites/; blocked /authentication/, /servicePrincipals/",
        "API domains: Chat, Context, Tools, Workspaces; Copilot-Credit consumption pricing",
        "! Tool names differ between sources and may change",
    ], theme="blue", icon="m365", badge="blog",
        src=[("Work IQ API overview", learn("microsoft-365/copilot/extensibility/work-iq/api-overview", base=""))])
    _, rb = row(cv, 0, y9, [rc1, rc2, rc3, rc4], gap=40)

    # comparison table: Web IQ vs the Foundry web tools
    y10 = rb + 56
    tw_ = 2150
    cmp_t = Table([("", 190), "Web IQ", "Foundry Web Search tool", "Grounding with Bing Search"], [
        [("Surface", "violet"), "api.microsoft.ai/v3 REST + MCP; own portal and Azure resource", "Foundry-native tool", "Foundry-native tool + your Bing resource"],
        [("Status", "violet"), "GA (Auto = beta)", "GA", "GA (Custom Search = preview)"],
        [("Output", "violet"), "Ranked passages / evidence objects; Browse returns the full page", "Model answer with inline citations", "Model answer with citations"],
        [("Billing", "violet"), "Web IQ resource, per 1K calls", "Microsoft-managed Bing grounding", "Your Bing resource"],
        [("In a Toolbox", "violet"), "Yes, via a generic MCP entry", "Yes", "No (direct only)"],
        [("Compliance", "violet"), "Queries logged; outside the DPA and the EU Data Boundary", "First Party Consumption Service", "Same"],
    ], w=tw_, theme="violet", size=15, head_size=16, title="Web IQ vs the Foundry web grounding tools (as of 2026-11-03)",
        title_size=22)
    cmp_t.place(cv, 0, y10)
    nx = tw_ + 50
    cmp_n = Note(W - nx, "The Foundry web tools are Bing-backed First Party Consumption Services; Web IQ is its own API service with its own resource, "
                         "billing and logging terms. A Microsoft session says the Foundry web search tool is different from Web IQ, "
                         "so expect different results from the two [blog].",
                 kind="tip", title="Two different web surfaces", size=16)
    cmp_n.place(cv, nx, y10 + 36)
    return max(cmp_t.bottom, cmp_n.bottom)


def scenarios(cv: Canvas, y11: float) -> float:
    section_header(cv, 0, y11, "Example scenarios (illustrative compositions of documented capabilities)",
                   sub="not documented reference architectures - they show which IQ answers which question", size=32, w=W)
    y12 = y11 + 100
    cw4c = (W - 3 * 40) / 4
    sc = [
        (Card(cw4c, "1. Policy and HR Q&A with per-user access", [
            "Foundry IQ knowledge base over Blob + indexed SharePoint, with ACL trimming",
            "Exposed to the agent through the KB MCP endpoint (knowledge_base_retrieve)",
            "Each user only gets documents they are allowed to read",
        ], theme="teal", icon="ai-search", badge="illustrative"),
         "What does our travel policy say about rail versus air?", "teal"),
        (Card(cw4c, "2. Store-ops assistant", [
            "Fabric IQ ontology (stores, inventory, products, suppliers) answers by following relationships",
            "Work IQ adds related mail and calendar",
            "Based on the retail-ontology demo [blog]",
        ], theme="cyan", icon="fabric", badge="illustrative"),
         "Which store has the most hammers?", "cyan"),
        (Card(cw4c, "3. Account prep", [
            "Web IQ news + Browse for the customer",
            "Work IQ for recent emails and meetings",
            "Fabric IQ semantic model for the pipeline numbers",
        ], theme="violet", icon="globe", badge="illustrative"),
         "Prepare me for tomorrow's call with Contoso.", "violet"),
        (Card(cw4c, "4. One federated knowledge base", [
            "Remote SharePoint + Fabric Ontology + Web (MCP source) behind a single retrieve",
            "Planning, rerank and answer synthesis in one call",
            "All three are preview knowledge-source kinds",
        ], theme="teal", icon="ai-search", badge="illustrative", fill="cross"),
         "Summarise our top supplier risks and any news about them.", "teal"),
    ]
    _, sb = row(cv, 0, y12, [c for c, _, _ in sc], gap=40)
    for c, q, th in sc:
        Bubble(cw4c - 40, q, theme=th, tail="top").place(cv, c.x + 30, sb + 26)
    return sb + 26 + 50


def timeline(cv: Canvas, y13: float) -> float:
    section_header(cv, 0, y13, "Timeline", sub="blog or video dates are tagged [blog] and [video]; pricing and retirement dates come from Learn",
                   size=32, w=W)
    ty0 = y13 + 130
    events = [
        ("2025-11-18 to 11-20", "Ignite 2025", "Foundry IQ and Fabric IQ + Ontology in public preview [blog]", "gray"),
        ("2026-06-02", "Build 2026", "Web IQ first release; Foundry IQ knowledge-base GA [blog]", "gray"),
        ("2026-06-16", "Work IQ APIs GA", "Chat, Context, Tools, Workspaces domains [blog]", "gray"),
        ("2026-07-28 to 07-30", "Microsoft IQ Deep Dive", "Foundry IQ + Web IQ, Work IQ and Fabric IQ sessions [video]", "gray"),
        ("2026-10-16", "Web IQ pricing effective", "$7.00 per 1K calls; Browse $1.00 (Learn)", "violet"),
        ("2026-11-06", "Fabric data agent tool retires", "Move to the Fabric IQ tool (Learn)", "red"),
    ]
    step = W / len(events)
    cv.line((0, ty0), (W - 10, ty0), stroke=INK, sw=3)
    cv.poly([(W - 24, ty0 - 9), (W - 8, ty0), (W - 24, ty0 + 9)], kind="line", stroke=INK, sw=3)
    lw_ = 520
    bottom = ty0
    for i, (when, title, detail, th_name) in enumerate(events):
        th = get_theme(th_name)
        cx = step * (i + 0.5)
        cv.ellipse(cx - 11, ty0 - 11, 22, 22, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        cv.line((cx, ty0 + 12), (cx, ty0 + 30), stroke=th.stroke, sw=2)
        tl = metrics.wrap_text(title, lw_, 19)
        dl = metrics.wrap_text(detail, lw_, 15)
        by = ty0 + 34
        cv.text(cx - lw_ / 2, by, when, size=18, color=th.deep, align="center", w=lw_)
        cv.text(cx - lw_ / 2, by + 18 * 1.25, "\n".join(tl), size=19, color=INK, align="center", w=lw_)
        yb = by + 18 * 1.25 + len(tl) * 19 * 1.25 + 4
        cv.text(cx - lw_ / 2, yb, "\n".join(dl), size=15, color=MUTED, align="center", w=lw_)
        bottom = max(bottom, yb + len(dl) * 15 * 1.25)
    tx_ = step * 5
    cv.line((tx_, ty0 - 52), (tx_, ty0 + 22), stroke="#e03131", sw=2, dash="dashed")
    cv.text(tx_ - 150, ty0 - 80, "today 2026-11-03", size=17, color="#c92a2a")
    return bottom


def gotchas(cv: Canvas, y14: float) -> float:
    section_header(cv, 0, y14, "Gotchas to read before you build", size=32, w=W)
    y15 = y14 + 70
    gw = (W - 3 * 40) / 4
    g = [
        Note(gw, "Queries are logged; excluded from the DPA and EU Data Boundary; public endpoint only; paid subscription required; "
                 "response content cannot be cached or stored.", kind="gotcha", title="Web IQ", size=15),
        Note(gw, "Delegated only; unsupported in network-isolated projects; Foundry User needed at account AND project scope; "
                 "the connection is immutable; actions can write.", kind="gotcha", title="Work IQ", size=15),
        Note(gw, "Data agent tool retires 2026-11-06; capacity must be F2+ / P1+ with the full Fabric stack; items must be published; "
                 "network support varies by item type.", kind="gotcha", title="Fabric IQ", size=15),
        Note(gw, "Hub-based projects are not supported; GA vs preview depends on the API version; the portals only expose the preview API.",
             kind="warn", title="Foundry IQ", size=15),
        Note(gw, "SharePoint tool: one per agent; it breaks when the agent is published to Teams.", kind="warn", title="SharePoint tool", size=15),
        Note(gw, "A Toolbox does not hold SharePoint, Fabric data agent, Grounding with Bing, Azure Functions, Function calling, "
                 "Computer use or Image generation. The overview also lists a Reminder tool that the how-to table omits.",
             kind="warn", title="Toolbox limits", size=15),
        Note(gw, "Agent identity acting on behalf of a user is Preview and needs the AgentBlueprint endpoint scheme; Foundry can act as "
                 "actor only for a limited set of Microsoft-owned tools.", kind="preview", title="Delegation", size=15,
             src=[("User delegation", learn("agents/concepts/user-delegation"))]),
        Note(gw, "Foundry's table of contents shows only three IQs. Web IQ lives in its own Learn area (/en-us/web-iq/) and portal "
                 "(webiq.microsoft.ai).", kind="info", title="Where is Web IQ?", size=15),
    ]
    _, gb = grid(cv, 0, y15, g, cols=4, gap_x=40, gap_y=24)
    return gb


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Microsoft IQ",
        "Work IQ, Fabric IQ, Foundry IQ and Web IQ - the enterprise-context layer around Foundry agents (status as of 2026-11-03)",
        w=W)
    y = banner(cv, bottom + 34)
    y = composition(cv, y + 50) + 70
    y = three_ways(cv, y) + 70
    y = matrix_section(cv, y) + 76
    y = flows(cv, y) + 70
    y = related(cv, y) + 70
    y = scenarios(cv, y) + 50
    y = timeline(cv, y) + 60
    y = gotchas(cv, y) + 70

    items = [
        ("Microsoft IQ documentation (hub)", "https://learn.microsoft.com/en-us/microsoft-iq/"),
        ("Microsoft IQ - microsoft.com (marketing page)", "https://www.microsoft.com/en-us/ai/microsoft-iq"),
        ("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
        ("Connect a Foundry IQ knowledge base to an agent", learn("agents/how-to/foundry-iq-connect")),
        ("Fabric IQ tool for Foundry agents", learn("agents/how-to/tools/fabric-iq")),
        ("Work IQ tool for Foundry agents", learn("agents/how-to/tools/work-iq")),
        ("Fabric data agent tool (retiring 2026-11-06)", learn("agents/how-to/tools/fabric")),
        ("SharePoint tool", learn("agents/how-to/tools/sharepoint")),
        ("Foundry web tools overview", learn("agents/how-to/tools/web-overview")),
        ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
        ("Network isolation for a toolbox", learn("agents/how-to/tools/toolbox-network-isolation")),
        ("Tool authentication", learn("agents/how-to/tools/tool-authentication")),
        ("Web IQ overview", learn("web-iq/overview", base="")),
        ("Web IQ pricing", learn("web-iq/resources/pricing", base="")),
    ]
    s1 = sources(cv, 0, y, items, w=W, cols=4)
    sources(cv, 0, s1.y + s1.h + 24, [
        ("Fabric IQ overview", learn("fabric/iq/overview", base="")),
        ("Work IQ overview (Microsoft 365)", learn("microsoft-365/copilot/extensibility/work-iq", base="")),
        ("AI Search: Work IQ knowledge source", learn("azure/search/agentic-knowledge-source-how-to-work-iq", base="")),
        ("Blog: Announcing Microsoft Web IQ (Bing, 2026-06-02) [blog]", "https://blogs.bing.com/search/2026/6/Announcing-Microsoft-Web-IQ/"),
        ("Blog: Learn how to use the four IQs (Tech Community, 2026-08-03) [blog]",
         "https://techcommunity.microsoft.com/blog/AzureDevCommunityBlog/learn-how-to-use-the-four-iqs-web-iq-work-iq-fabric-iq-foundry-iq/4542916"),
        ("Blog: Foundry IQ build smarter agents faster (2026-06-02) [blog]", "https://devblogs.microsoft.com/foundry/build-smarter-agents-faster-with-foundry-iq/"),
    ], w=W, cols=3, title="More Learn pages and blog or video sources (not Learn)")
