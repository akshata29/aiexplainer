"""Microsoft Foundry capability atlas - THE exhaustive inventory (part 1 of 2: areas 1-6).

One coloured panel per area; every row = status badge + clickable capability name (Learn link) + one-line purpose,
sub-pages as clickable chips.  The data for all 11 areas lives here (single source of truth) so both canvases can draw
the same per-area count strip; capability_atlas_part_2.py imports this module and draws areas 7-11.
"""
from __future__ import annotations

from collections import Counter
import itertools
from typing import Optional

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="capability-atlas", title="Foundry capability atlas (part 1)", section="1", group="Overview", order=2,
    description="The exhaustive inventory, part 1 of 2: build surfaces, models, agents, tools, knowledge and observability - every capability with its GA/preview status, one-line purpose and a clickable Learn link.",
    tags=["atlas", "capabilities", "inventory", "status", "learn-links"],
)

# ------------------------------------------------------------------------------------------------ geometry
COL, GUT, NCOL = 620, 40, 5
W = NCOL * COL + (NCOL - 1) * GUT            # 3260
PAD = 16
PILL_W, PILL_H = 68, 22
LH = metrics.line_ratio()
MUTED_TXT = "#495057"
RED_TAG = "#c92a2a"
DWIDE = 2 * COL + GUT

# status key -> (label, fill theme, stroke theme)
STATUS_STYLE = {
    "ga": ("GA", "green", "green"),
    "gap": ("GA*", "green", "orange"),
    "pre": ("Preview", "orange", "orange"),
    "unk": ("GA?", "yellow", "yellow"),
    "ret": ("Retiring", "red", "red"),
    "dead": ("Retired", "gray", "red"),
    "doc": ("Docs", "gray", "gray"),
}
BAR_ORDER = ["ga", "gap", "pre", "unk", "ret", "dead", "doc"]


# ------------------------------------------------------------------------------------------------ data model
def _u(path: str) -> str:
    return path if path.startswith("http") else learn(path)


def _d(v) -> tuple:
    return () if v is None else ((v,) if isinstance(v, int) else tuple(v))


class Item:
    def __init__(self, name, st, purpose, path=None, chips=(), plus=False, d=(), group=False):
        self.name, self.st, self.purpose, self.path = name, st, purpose, path
        self.chips, self.plus, self.d, self.group = tuple(chips), plus, tuple(d), group

    @property
    def url(self) -> Optional[str]:
        return _u(self.path) if self.path else None


def r(name, st, purpose, path, *chips, plus=False, d=None) -> Item:
    """One capability row: name links to `path`; chips = (label, path[, status]) sub-pages."""
    return Item(name, st, purpose, path, chips, plus, _d(d))


def g(name, st, purpose, *chips, plus=False, d=None) -> Item:
    """Group row: no single page, every chip is itself a capability (counts individually)."""
    return Item(name, st, purpose, None, chips, plus, _d(d), True)


class Cluster:
    def __init__(self, title, items, theme=None):
        self.title, self.items, self.theme = title, items, theme


class Area:
    def __init__(self, num, short, title, theme, blurb, clusters, cols=1, colmap=None):
        self.num, self.short, self.title, self.theme, self.blurb = num, short, title, theme, blurb
        self.clusters, self.cols, self.colmap = clusters, cols, colmap


def capabilities(it: Item) -> list:
    """[(label, url, status)] for everything an item contributes to the capability count."""
    if it.group:
        return [(c[0], _u(c[1]), c[2] if len(c) > 2 else it.st) for c in it.chips]
    return [(it.name, it.url, it.st)]


def tally(area: Area) -> tuple:
    n, by = 0, Counter()
    for cl in area.clusters:
        for it in cl.items:
            for _l, _u_, st in capabilities(it):
                n += 1
                by[st] += 1
    return n, by


def plus_count(area: Area) -> int:
    """Capabilities in the area that the official capability reference does not list."""
    k = 0
    for cl in area.clusters:
        for it in cl.items:
            if it.plus:
                k += len(capabilities(it))
    return k


# ------------------------------------------------------------------------------------------------ pills
def draw_pill(cv: Canvas, x: float, y: float, st: str, *, w=PILL_W, h=PILL_H, size=13, opacity=100) -> None:
    label, ft, stt = STATUS_STYLE[st]
    f, s = THEMES[ft], THEMES[stt]
    cv.rect(x, y, w, h, stroke=s.stroke, fill=f.fill, style="solid", sw=2 if st == "gap" else 1.5, rough=0,
            opacity=opacity)
    tw, th_ = metrics.text_size(label, size)
    cv.text(x + (w - tw) / 2, y + (h - th_) / 2, label, size=size, color=f.deep, opacity=opacity)


# ------------------------------------------------------------------------------------------------ area panel
ICONS = {1: "code", 2: "openai", 3: "agent", 4: "toolbox-icon", 5: "ai-search", 6: "app-insights", 7: "metrics",
         8: "content-safety", 9: "policy", 10: "api", 11: "ai-services"}


class AreaBlock(Rect2):
    """One coloured area panel. Layout is computed at construction (so heights are known for packing)."""
    SUB_GAP = 30

    def __init__(self, area: Area, w: float):
        self.area, self.w = area, w
        self.th = THEMES[area.theme]
        self.ops: list = []
        inner = w - 2 * PAD
        n, _by = tally(area)
        y = PAD
        self.ops.append(("num", PAD + 20, y + 20, area.num, area.theme))
        tx = PAD + 52
        cnt = f"{n} capabilities"
        cw = metrics.line_width(cnt, 15)
        icon_w = 46 if ICONS.get(area.num) else 0
        if icon_w:
            self.ops.append(("icon", w - PAD - 38, y + 1, ICONS[area.num]))
        size = 26
        while metrics.line_width(area.title, size) > w - PAD - tx - cw - icon_w - 14 and size > 20:
            size -= 1
        self.ops.append(("text", tx, y + (26 - size) / 2 + 1, area.title, size, self.th.deep, None))
        self.ops.append(("text", w - PAD - icon_w - cw, y + 9, cnt, 15, MUTED_TXT, None))
        y += 26 * LH + 2
        bl = metrics.wrap_text(area.blurb, inner - 52 - icon_w, 14)
        self.ops.append(("text", tx, y, "\n".join(bl), 14, MUTED_TXT, None))
        y += len(bl) * 14 * LH + 8
        y = max(y, PAD + 46)
        self.ops.append(("line", PAD, y, w - PAD, y, self.th.stroke, 2, "solid"))
        y += 12
        ncols = area.cols
        sub_w = (inner - self.SUB_GAP * (ncols - 1)) / ncols
        colmap = area.colmap or [list(range(len(area.clusters)))]
        bottoms = []
        for ci, idxs in enumerate(colmap):
            cx = PAD + ci * (sub_w + self.SUB_GAP)
            cy = y
            for k in idxs:
                cy = self._cluster(area.clusters[k], cx, cy, sub_w)
            bottoms.append(cy)
        self.notes: list = []
        footer = getattr(area, "footer", None)
        if footer:
            kind, ftitle, ftext, fsrc = footer
            nt = Note(sub_w, ftext, kind=kind, title=ftitle, src=fsrc, size=14, title_size=16)
            ci = min(range(len(bottoms)), key=lambda i: bottoms[i])
            self.notes.append((nt, PAD + ci * (sub_w + self.SUB_GAP), bottoms[ci] + 2))
            bottoms[ci] += nt.h + 12
        self.h = max(bottoms) - 10 + PAD
        self.x = self.y = 0.0

    # ---- layout helpers
    def _cluster(self, cl: Cluster, x: float, y: float, w: float) -> float:
        cth = THEMES[cl.theme] if cl.theme else self.th
        if cl.title:
            self.ops.append(("text", x, y, cl.title, 18, cth.deep, None))
            y += 18 * LH + 3
            self.ops.append(("line", x, y, x + w, y, cth.stroke, 1.5, "dotted"))
            y += 8
        for i, it in enumerate(cl.items):
            y = self._row(it, x, y, w, cth, zebra=(i % 2 == 1))
        return y + 10

    def _row(self, it: Item, x: float, y: float, w: float, th, zebra: bool) -> float:
        tx = x + PILL_W + 12
        tw = w - PILL_W - 12 - 6
        name = ("+ " if it.plus else "") + it.name
        nl = metrics.wrap_text(name, tw - 18, 16)
        pl = metrics.wrap_text(it.purpose, tw, 14)
        name_h, pur_h = len(nl) * 16 * LH, len(pl) * 14 * LH
        extra_h = 0.0
        extra_ops = []
        if it.chips and it.group:                       # boxed chips: every chip is a capability
            cx = cy = 0.0
            ch = 13 * LH + 6
            for c in it.chips:
                label, url = c[0], _u(c[1])
                cst = c[2] if len(c) > 2 else None
                cw = metrics.line_width(label, 13) + 16
                if cx and cx + cw > tw:
                    cx, cy = 0.0, cy + ch + 6
                extra_ops.append(("chip", cx, cy, cw, ch, label, url, cst, th.name))
                cx += cw + 6
            extra_h = cy + ch
        elif it.chips:                                  # sub-page links: blue text, bullet separated
            cx = cy = 0.0
            lh = 13 * LH
            n = len(it.chips)
            for i, c in enumerate(it.chips):
                pre = len(c) > 2 and c[2] == "pre"
                text = c[0] + (" (preview)" if pre else "") + (" \u2022" if i < n - 1 else "")
                cw = metrics.line_width(text, 13)
                if cx and cx + cw > tw:
                    cx, cy = 0.0, cy + lh + 3
                extra_ops.append(("link", cx, cy, text, _u(c[1]), "#d9480f" if pre else LINK))
                cx += cw + 8
            extra_h = cy + lh
        h = 8 + name_h + 2 + pur_h + ((6 + extra_h) if extra_h else 0) + 10
        h = max(h, 8 + PILL_H + ((3 + 13 * LH) if it.d else 0) + 8)
        if zebra:
            self.ops.append(("band", x - 8, y, w + 16, h))
        self.ops.append(("pill", x, y + 8, it.st))
        if it.d:
            self.ops.append(("text", x, y + 8 + PILL_H + 3, " ".join(f"D{n}" for n in it.d), 13, RED_TAG, None))
        self.ops.append(("text", tx, y + 8, "\n".join(nl), 16, th.deep, it.url))
        self.ops.append(("text", tx, y + 8 + name_h + 2, "\n".join(pl), 14, MUTED_TXT, None))
        y0 = y + 8 + name_h + 2 + pur_h + 6
        for op in extra_ops:
            self.ops.append((op[0], tx + op[1], y0 + op[2]) + tuple(op[3:]))
        return y + h

    @staticmethod
    def measure_row(it: Item, w: float) -> float:
        tmp = AreaBlock.__new__(AreaBlock)
        tmp.ops = []
        return tmp._row(it, 0.0, 0.0, w, THEMES["gray"], False)

    # ---- drawing
    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "AreaBlock":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=3)
            for op in self.ops:
                k = op[0]
                if k == "text":
                    _, dx, dy, s, size, color, link = op
                    cv.text(x + dx, y + dy, s, size=size, color=color, link=link)
                elif k == "pill":
                    draw_pill(cv, x + op[1], y + op[2], op[3])
                elif k == "chip":
                    _, dx, dy, cw, ch, label, url, cst, tname = op
                    if cst:
                        ct = THEMES[STATUS_STYLE[cst][1]]
                        stroke, fill, deep = ct.stroke, ct.soft, ct.deep
                    else:
                        ct = THEMES[tname]
                        stroke, fill, deep = ct.stroke, "#ffffff", ct.deep
                    cv.rect(x + dx, y + dy, cw, ch, stroke=stroke, fill=fill, style="solid", sw=1.5, rough=0)
                    cv.text(x + dx + 8, y + dy + 3, label, size=13, color=deep, link=url)
                elif k == "icon":
                    place_icon(cv, op[3], x + op[1], y + op[2], 38)
                elif k == "link":
                    _, dx, dy, text, url, color = op
                    cv.text(x + dx, y + dy, text, size=13, color=color, link=url)
                elif k == "band":
                    _, dx, dy, bw, bh = op
                    cv.rect(x + dx, y + dy, bw, bh, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                            rough=0, round_=False, opacity=70)
                elif k == "line":
                    _, x1, y1, x2, y2, color, sw, dash = op
                    cv.line((x + x1, y + y1), (x + x2, y + y1), stroke=color, sw=sw, dash=dash, rough=0)
                elif k == "num":
                    numbered(cv, x + op[1], y + op[2], op[3], theme=op[4], d=40, size=22)
            for nt, dx, dy in self.notes:
                nt.place(cv, x + dx, y + dy)
        cv.register(f"area {self.area.num}", x, y, self.w, H, container=True)
        return self


# ------------------------------------------------------------------------------------------------ stacking
def span_w(span: int) -> float:
    return span * COL + (span - 1) * GUT


def _copy(area: Area, clusters: list, cols: int, colmap) -> Area:
    out = Area(area.num, area.short, area.title, area.theme, area.blurb, clusters, cols=cols, colmap=colmap)
    out.footer = getattr(area, "footer", None)
    return out


def balanced(area: Area, span: int, cut_penalty: float = 140.0) -> Area:
    """Copy of `area` laid out in `span` sub-columns. Rows keep their order; cut points minimise the tallest
    sub-column, with a penalty for cutting inside a cluster (the second part then repeats the title)."""
    if span == 1:
        return _copy(area, area.clusters, 1, None)
    sub_w = (span_w(span) - 2 * PAD - AreaBlock.SUB_GAP * (span - 1)) / span
    seq = []                                    # (cluster idx, item, row height)
    for ci, cl in enumerate(area.clusters):
        for it in cl.items:
            seq.append((ci, it, AreaBlock.measure_row(it, sub_w)))
    n = len(seq)

    def seg_h(i: int, j: int) -> float:
        h, seen = 0.0, set()
        for ci, _it, rh in seq[i:j]:
            if ci not in seen:
                seen.add(ci)
                if area.clusters[ci].title:
                    h += 18 * LH + 11
                h += 10
            h += rh
        return h

    def cut_cost(i: int) -> float:
        return cut_penalty if seq[i - 1][0] == seq[i][0] else 0.0

    best = None
    for cuts in itertools.combinations(range(1, n), span - 1):
        b = (0,) + cuts + (n,)
        cost = max(seg_h(b[k], b[k + 1]) for k in range(span)) + sum(cut_cost(c) for c in cuts)
        if best is None or cost < best[0]:
            best = (cost, b)
    b = best[1]
    clusters, colmap = [], []
    for k in range(span):
        idxs = []
        part = {}
        for ci, it, _rh in seq[b[k]:b[k + 1]]:
            part.setdefault(ci, []).append(it)
        for ci, its in part.items():
            cl = area.clusters[ci]
            first = seq[b[k]][0] == ci and b[k] > 0 and seq[b[k] - 1][0] == ci
            title = (cl.title + " (cont.)") if (first and cl.title) else cl.title
            clusters.append(Cluster(title, its, cl.theme))
            idxs.append(len(clusters) - 1)
        colmap.append(idxs)
    return _copy(area, clusters, span, colmap)


def place_stacks(cv: Canvas, y0: float, stacks: list, gap: float = 40) -> float:
    """stacks = [(x, [blocks])]; stretches the last block of each so every stack ends at the same y."""
    nat = [sum(b.h for b in blocks) + gap * (len(blocks) - 1) for _x, blocks in stacks]
    target = max(nat)
    for (x, blocks), n in zip(stacks, nat):
        cy = y0
        for i, b in enumerate(blocks):
            extra = (target - n) if i == len(blocks) - 1 else 0
            b.place(cv, x, cy, h=b.h + extra)
            cy += b.h + gap
    return y0 + target


AI = "https://learn.microsoft.com/en-us/azure/ai-services/"
SPEECH = AI + "speech-service/"

# ================================================================================================ AREA 1
A1 = Area(1, "Build surfaces", "Build surfaces and developer tools", "gray",
          "Where you author, test and ship Foundry work: portal, SDKs, CLIs, editors, MCP server and samples", [
    Cluster(None, [
        r("Foundry portal (ai.azure.com)", "gap",
          "Web UI with a New Foundry toggle (Home, Discover, Build, Operate, Manage, Docs); core is GA, several panes are preview",
          "concepts/general-availability"),
        r("Playgrounds (Model, Agents, Images, Video)", "gap",
          "Prototype interactively and compare up to 3 models; agents with tools, memory, tracing and eval. Video is preview, Audio is classic-only",
          "concepts/concept-playgrounds"),
        r("Foundry SDKs (Python, C#, JS, Java)", "ga",
          "Thin client over the project endpoint plus an OpenAI client; 2.x stable line", "how-to/develop/sdk-overview"),
        r("Azure Developer CLI (azd) extensions", "unk",
          "Scaffold, run, test and deploy agent projects: azd ai agent, connection, toolbox, skill, routine, project, inspector",
          "agents/concepts/cli-agent-development",
          ("Install the extensions", "agents/how-to/install-cli-foundry-extensions")),
        r("VS Code: Foundry Toolkit", "unk",
          "New name for AI Toolkit: models, Agent Builder, Tool Catalog, Inspector, hosted-agent deploy, evals and traces; some experiences preview",
          "how-to/develop/get-started-projects-visual-studio-code"),
        r("Foundry Agent Canvas", "pre", "GitHub Copilot App side panel to design, test and deploy hosted agents",
          "agents/concepts/foundry-canvas"),
        r("Coding-agent integration (Foundry Skill)", "unk",
          "Reusable guidance so coding agents deploy, evaluate and troubleshoot Foundry; azd ai for coding agents",
          "how-to/develop/use-microsoft-foundry-skill",
          ("azd with coding agents", "agents/how-to/use-cli-with-coding-agents")),
        r("Foundry MCP Server", "pre",
          "Cloud MCP server at mcp.ai.azure.com with 79 tools in 17 categories (as of 2026-11-03); cannot reach private-link Foundry resources",
          "mcp/get-started", ("Available tools", "mcp/available-tools"),
          ("Security best practices", "mcp/security-best-practices")),
        r("Templates and samples", "ga", "Solution templates (9 scenarios), agent templates and GitHub samples",
          "how-to/develop/ai-template-get-started",
          ("foundry-samples on GitHub", "https://github.com/microsoft-foundry/foundry-samples")),
        r("LangChain and LangGraph integration", "unk",
          "langchain-azure-ai: models, agents, hosting, middleware, toolbox, memory and tracing", "how-to/develop/langchain",
          ("Models", "how-to/develop/langchain-models"), ("Agents", "how-to/develop/langchain-agents"),
          ("Hosted agents", "how-to/develop/langchain-hosted-agents"), ("Toolbox", "how-to/develop/langchain-toolbox"),
          ("Memory", "how-to/develop/langchain-memory"), ("Tracing", "how-to/develop/langchain-traces"),
          ("Middleware", "how-to/develop/langchain-middleware")),
        r("Foundry DevPack", "pre",
          "One-command installer for azd and azd ai, the Foundry Skill, the Toolkit and Canvas (installers are preview per DevBlog)",
          "how-to/develop/install-cli-sdk", plus=True),
        r("Agent Inspector (azd and VS Code)", "unk", "Local request/response and tool-call debugging",
          "agents/how-to/agent-inspector", ("VS Code inspector", "how-to/develop/vs-code-agent-inspector"),
          ("VS Code tracing", "how-to/develop/vs-code-tracing")),
        r("Claude Code and Claude Desktop setup", "unk", "Point Anthropic tooling at Foundry-hosted Claude",
          "foundry-models/how-to/configure-claude-code", ("Claude Desktop", "foundry-models/how-to/configure-claude-desktop"),
          plus=True),
        r("Foundry Local", "unk",
          "On-device runtime (ONNX); version 2.1 adds bring-your-own-model. Seen in the Sept 2026 DevBlog and the VS Code Toolkit page; no Learn article was checked for this atlas",
          "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-september-2026/", plus=True),
        r("Quickstarts and idea-to-prototype tutorial", "doc", "Guided first-run paths", "quickstarts/quickstarts",
          ("Idea to prototype", "tutorials/developer-journey-idea-to-prototype"),
          ("Create Foundry resources", "tutorials/quickstart-create-foundry-resources"), plus=True),
    ]),
])

# ================================================================================================ AREA 2
A2 = Area(2, "Models", "Models", "blue",
          "Catalog, deployment and capacity, inference APIs and model features, customization and lifecycle", [
    Cluster("Catalog and model families", [
        r("Foundry Models catalog", "ga",
          "Discover, compare and deploy: 10,000+ models, about 50 new per month, in two categories",
          "concepts/foundry-models-overview"),
        r("Models sold by Azure", "ga",
          "Microsoft-hosted with Microsoft support and SLAs. Providers: Azure OpenAI, Black Forest Labs, Cohere, DeepSeek, Meta, Microsoft, Mistral, Moonshot AI, SpaceXAI",
          "foundry-models/concepts/models-sold-directly-by-azure",
          ("Azure Government models", "foundry-models/concepts/models-sold-directly-by-azure-gov")),
        r("Models from partners and community", "ga",
          "Anthropic, Cohere, Meta, Microsoft, Mistral AI, NTT Data; Azure Marketplace subscription; provider-supported",
          "foundry-models/concepts/models-from-partners"),
        r("GPT-6 family (Astra, Sol, Luna)", "ga",
          "GPT-6 Astra, GPT-6.1 Sol, GPT-6 Luna: 1.05M-token context, up to 128K output; Global Standard in 28 regions (as of 2026-11-03; GA per Sept 2026 blogs)",
          "foundry-models/concepts/models-sold-directly-by-azure#gpt-6", plus=True),
        r("Claude (Anthropic)", "gap",
          "V1 Anthropic-hosted (some models preview) vs V2 Azure-hosted (all GA); Marketplace plus Claude Consumption Units billing; /anthropic Messages API",
          "foundry-models/concepts/claude-models",
          ("Hosting comparison", "foundry-models/concepts/claude-models-hosting-comparison"),
          ("Quotas and limits", "foundry-models/concepts/claude-models-quotas-limits"),
          ("Billing", "foundry-models/concepts/claude-models-billing"),
          ("Use Claude", "foundry-models/how-to/use-foundry-models-claude"), plus=True),
        r("MAI models", "pre",
          "MAI-Image-2.6 and 2.6-Flash and MAI-Thinking-1 are preview; MAI-Voice and MAI-Transcribe: check the docs",
          "foundry-models/how-to/use-foundry-models-mai-image",
          ("MAI-Thinking-1", "foundry-models/how-to/use-foundry-models-mai-thinking", "pre"),
          ("MAI-Voice", SPEECH + "mai-voices"), ("MAI-Transcribe", SPEECH + "mai-transcribe"),
          ("MAI-Transcribe Streaming", SPEECH + "mai-transcribe-2-streaming"), plus=True),
        r("Black Forest Labs (FLUX)", "unk", "FLUX image generation and editing",
          "foundry-models/how-to/use-foundry-models-flux", plus=True),
        r("SpaceXAI (Grok)", "gap", "grok-4.7 (coding, extraction, agentic) is GA; grok-4.6 is preview",
          "foundry-models/how-to/use-foundry-models-grok", plus=True),
        r("Microsoft-Decision-1 model", "unk", "Model for typed, non-generative decisions: classify, route, score",
          "foundry-models/how-to/use-foundry-models-microsoft-decision", plus=True),
        r("Decisions API", "unk",
          "/openai/v1/decisions; currently gpt-6-luna only, rolling out, East US 2 excluded (as of 2026-11-03)",
          "openai/how-to/decisions", plus=True),
        r("Hugging Face models", "pre", "Open models on Foundry Managed Compute (preview), with a classic fallback",
          "foundry-models/how-to/hugging-face-models", d=7),
        r("Fireworks on Foundry", "ga",
          "Fireworks models, pay-per-token or provisioned, with custom model import incl. LoRA; a subscription admin must enable it",
          "how-to/fireworks/enable-fireworks-models",
          ("Model catalog", "how-to/fireworks/fireworks-model-catalog"),
          ("Import custom models", "how-to/fireworks/import-custom-models"),
          ("Privacy and compliance FAQ", "how-to/fireworks/privacy-compliance-faq")),
        r("Healthcare AI models", "pre",
          "MedImageInsight Premium and CXRReportGen Premium (+ fine-tuning) as serverless endpoints; limited preview, research use only",
          "how-to/healthcare-ai/healthcare-ai-models",
          ("MedImageInsight Premium", "how-to/healthcare-ai/deploy-medimageinsight-premium"),
          ("CXRReportGen Premium", "how-to/healthcare-ai/deploy-cxrreportgen-premium"),
          ("Fine-tune premium models", "how-to/healthcare-ai/fine-tune-premium-healthcare-models")),
        r("Model benchmarks and leaderboards", "pre",
          "Compare quality, cost and performance with View leaderboard and Compare models", "concepts/model-benchmarks",
          ("Benchmark a model", "how-to/benchmark-model-in-catalog"),
          ("Benchmark evaluations", "observability/how-to/benchmark-evaluations"),
          ("Model choice guide", "foundry-models/how-to/model-choice-guide")),
    ]),
    Cluster("Deploy and capacity", [
        r("Model deployment", "ga",
          "Create and manage deployments; the alias = name + version + capacity type + content filter + rate limit",
          "foundry-models/how-to/deploy-foundry-models",
          ("Create deployments", "foundry-models/how-to/create-model-deployments")),
        r("Deployment types", "ga",
          "GlobalStandard, GlobalProvisionedManaged, GlobalBatch, DataZoneStandard, DataZoneProvisionedManaged, DataZoneBatch, Standard, ProvisionedManaged, DeveloperTier",
          "foundry-models/concepts/deployment-types",
          ("Government types", "foundry-models/concepts/deployment-types-gov"),
          ("Deployments overview", "concepts/deployments-overview")),
        r("Managed compute", "pre",
          "Dedicated GPUs (A100 80GB, H100 80GB, MI300X) for open models; vLLM, SGLang, TRT-LLM, NIM runtimes; billed hourly per accelerator",
          "concepts/managed-compute-overview", ("Deploy on managed compute", "how-to/deploy-models-managed"), d=7),
        r("Adapter (LoRA) deployment", "pre",
          "Host fine-tuned LoRA adapters on a compatible base deployment on managed compute",
          "concepts/adapter-deployment-overview", ("Deploy a LoRA adapter", "how-to/deploy-lora-managed-compute"),
          plus=True),
        r("Instant access models", "pre",
          "Call a model by name with no deployment; West US 3 only (as of 2026-11-03); global quota pool; no per-model guardrails",
          "concepts/instant-models"),
        r("Model router", "unk",
          "Routes each request to a best-fit model (auto or direct routing); 32 regions per Sept 2026 blog; session affinity and routing metadata preview",
          "openai/concepts/model-router",
          ("How it works", "openai/concepts/model-router-how-it-works"), ("Use it", "openai/how-to/model-router"),
          ("Monitor", "openai/how-to/monitor-model-router"), ("Evaluate", "openai/how-to/evaluate-model-router"),
          ("With agents", "openai/how-to/model-router-agents"), ("Policy", "how-to/model-router-policy")),
        r("Batch processing", "gap",
          "Global and Data Zone Batch: 50% discount, 24-hour async; some list-batch operations are preview",
          "openai/how-to/batch"),
        r("Flex processing", "pre", "50% discount for latency-tolerant work (Global Standard)",
          "openai/how-to/flex-processing", plus=True),
        r("Priority processing", "unk", "Faster, priority serving tier; the GPT-6 family shows n/a",
          "openai/concepts/priority-processing"),
        r("Provisioned throughput (PTU)", "ga", "Reserved throughput: sizing, billing, production operations, spillover",
          "openai/concepts/provisioned-throughput",
          ("Billing", "openai/concepts/provisioned-throughput-billing"),
          ("Sizing", "openai/how-to/provisioned-throughput-sizing"),
          ("Get started", "openai/how-to/provisioned-get-started"),
          ("Spillover", "openai/how-to/spillover-traffic-management"),
          ("Quickstart", "openai/provisioned-quickstart")),
        r("Quotas and region availability", "ga",
          "Per subscription, region and model quotas; Foundry Models limits; region matrices", "foundry-models/quotas-limits",
          ("Quota how-to", "how-to/quota"), ("Azure OpenAI quotas", "openai/quotas-limits"),
          ("Region availability", "foundry-models/concepts/models-sold-directly-by-azure-region-availability"),
          ("Region support", "reference/region-support")),
    ]),
    Cluster("Text, tools and reasoning", [
        r("Chat Completions", "ga", "Core chat inference API", "openai/how-to/chatgpt", plus=True),
        r("Responses API", "ga", "Stateful inference with tools and background mode", "openai/how-to/responses"),
        r("Text generation (Foundry Models)", "ga",
          "Generate text from Foundry Models such as Microsoft AI and DeepSeek models through the Responses API",
          "foundry-models/how-to/generate-responses", plus=True),
        g("Tool use and structured outputs", "ga", "Typed tool use and typed model outputs",
          ("Function calling", "openai/how-to/function-calling"),
          ("Programmatic tool calling", "openai/concepts/programmatic-tool-calling"),
          ("Structured outputs", "openai/how-to/structured-outputs"), ("JSON mode", "openai/how-to/json-mode"),
          plus=True),
        r("Multi-agent orchestration (Responses)", "pre",
          "Root agent spawns parallel subagents (api-version=preview, multi_agent.enabled)",
          "openai/how-to/responses-multi-agent", plus=True),
        g("Responses API built-ins", "unk", "Built-in tools and modes of the Responses API; the pages carry no status label",
          ("Deep research", "openai/how-to/deep-research"), ("Tool search", "openai/how-to/tool-search"),
          ("Web search", "openai/how-to/web-search"), ("WebSocket mode", "openai/how-to/websockets"),
          ("Shell tool", "openai/how-to/shells"), ("Skills", "openai/how-to/skills"), plus=True),
        r("Predicted outputs", "pre", "Latency reduction when much of the output is predictable",
          "openai/how-to/predicted-outputs", plus=True),
        g("Performance, reasoning and embeddings", "unk",
          "Prompt caching, reasoning, vectors, coding agent and async events; the pages carry no status label",
          ("Prompt caching", "openai/how-to/prompt-caching"), ("Reasoning models", "openai/how-to/reasoning"),
          ("Reasoning in Foundry Models", "foundry-models/how-to/use-chat-reasoning"),
          ("Embeddings", "openai/how-to/embeddings"), ("Codex", "openai/how-to/codex"),
          ("Webhooks", "openai/how-to/webhooks"), plus=True),
    ]),
    Cluster("Images, video and voice", [
        g("Images and vision", "unk",
          "gpt-image-1/2, FLUX and vision input; dall-e-3 was retired 2026-03-04, so use gpt-image models",
          ("Image generation", "openai/how-to/dall-e"), ("Vision chats", "openai/how-to/gpt-with-vision"),
          ("Prompt transformation", "openai/concepts/prompt-transformation"), plus=True),
        r("Video generation (Sora 2)", "pre", "Text-to-video", "openai/concepts/video-generation", plus=True),
        r("GPT-Live", "unk", "Full-duplex voice model: listen and speak at once, delegate to a backend, over WebRTC",
          "openai/concepts/gpt-live", ("How-to", "openai/how-to/gpt-live"), ("WebRTC", "openai/how-to/gpt-live-webrtc"),
          ("Delegation", "openai/how-to/gpt-live-delegation"), ("Event reference", "openai/gpt-live-reference"),
          plus=True),
        r("GPT Realtime 2.1 and Realtime API", "ga",
          "Speech-to-speech with built-in reasoning over WebRTC, WebSockets or SIP", "openai/concepts/realtime-2",
          ("Realtime how-to", "openai/how-to/realtime-audio"), ("WebRTC", "openai/how-to/realtime-audio-webrtc"),
          ("WebSockets", "openai/how-to/realtime-audio-websockets"), ("SIP", "openai/how-to/realtime-audio-sip"),
          ("Migrate from the preview API", "openai/how-to/realtime-audio-preview-api-migration-guide"), plus=True),
        r("Realtime Translate", "ga", "Continuous real-time translation for live multilingual audio",
          "openai/concepts/gpt-realtime-translate", plus=True),
        r("Realtime Transcribe", "ga", "Streaming transcription for low-latency captioning and monitoring of live audio",
          "openai/concepts/gpt-realtime-whisper", plus=True),
        r("Voice Live API", "gap",
          "Fully managed speech-to-speech (STT + LLM + TTS + avatar) in Azure Speech in Foundry Tools; some models preview",
          SPEECH + "voice-live", ("Quickstart", SPEECH + "voice-live-quickstart"), plus=True),
        g("Audio and speech", "unk", "Azure OpenAI audio plus Azure Speech; the pages carry no status label",
          ("Audio generation", "openai/audio-completions-quickstart"), ("Speech to text", SPEECH + "get-started-speech-to-text"),
          ("Text to speech", SPEECH + "get-started-text-to-speech"), ("Whisper quickstart", "openai/whisper-quickstart"),
          plus=True),
    ]),
    Cluster("Customization and lifecycle", [
        r("Fine-tuning: Managed Training", "ga",
          "Supervised, preference (DPO), reinforcement (RFT), vision and tool-calling fine-tuning; synthetic data and safety evaluation are preview",
          "fine-tuning/overview", ("SFT", "openai/how-to/fine-tuning"),
          ("DPO", "openai/how-to/fine-tuning-direct-preference-optimization"),
          ("RFT", "openai/how-to/reinforcement-fine-tuning"), ("Vision", "openai/how-to/fine-tuning-vision"),
          ("Tool calling", "openai/how-to/fine-tuning-functions"),
          ("Synthetic data", "fine-tuning/data-generation", "pre"),
          ("Safety evaluation", "openai/how-to/fine-tuning-safety-evaluation", "pre"),
          ("Deploy", "fine-tuning/deploy-fine-tuned-models"), ("Cost management", "fine-tuning/cost-management")),
        r("Fine-tuning: Programmed Training", "pre", "Code-driven training loops; needs explicit access approval",
          "fine-tuning/programmed-training/overview", ("Quickstart", "fine-tuning/programmed-training/quickstart"),
          ("SDK cheat sheet", "fine-tuning/programmed-training/sdk-cheatsheet"),
          ("Concepts", "fine-tuning/programmed-training/concepts"),
          ("Troubleshoot", "fine-tuning/programmed-training/troubleshoot"), plus=True),
        r("Model versions and lifecycle", "ga",
          "Versions, automatic updates, upgrades, retirement policy and schedule, retired models",
          "foundry-models/concepts/model-versions", ("Model migration", "foundry-models/concepts/model-migration"),
          ("Working with models", "openai/how-to/working-with-models"),
          ("Retirement policy", "openai/concepts/model-retirements"),
          ("Retirement schedule", "openai/concepts/model-retirement-schedule"),
          ("Retired models", "openai/concepts/retired-models")),
        r("Data privacy for the model catalog", "ga", "How data is handled for models in the catalog",
          "responsible-ai/openai/data-privacy", plus=True),
        r("Deployment helpers and best practices", "ga",
          "Migrate from retired GitHub Models (retired 2026-07-30), troubleshoot errors, automate deployments, prompt and latency guidance",
          "foundry-models/how-to/quickstart-github-models",
          ("Troubleshoot errors", "openai/how-to/troubleshoot-errors"),
          ("Automate deployments with quota", "openai/how-to/automate-quota-deployments"),
          ("Prompt engineering", "openai/concepts/prompt-engineering"), ("Latency", "openai/how-to/latency"),
          ("Integrate with other apps", "how-to/integrate-with-other-apps"),
          ("DeepSeek reasoning tutorial", "foundry-models/tutorials/get-started-deepseek-r1"), plus=True),
    ]),
])

# ================================================================================================ AREA 3
A3 = Area(3, "Agents", "Agents", "green",
          "Foundry Agent Service: prompt and hosted agents, triggers, identity, publishing and the development lifecycle", [
    Cluster("Agent types and runtime", [
        r("Foundry Agent Service", "ga",
          "Managed platform to build, deploy and scale agents: runtime, toolboxes, models, observability, optimization, identity, publishing",
          "agents/overview"),
        r("Prompt agents", "ga", "Declarative agents: instructions + model + tools; versioned; no code or containers",
          "agents/concepts/prompt-agents", ("Quickstart", "agents/quickstarts/prompt-agent")),
        r("Voice-based prompt agents", "pre",
          "Real-time voice via Voice Live over WebSocket; telephony through Teams Phone extensibility, Twilio and SIP (region-limited)",
          "agents/quickstarts/prompt-voice-agent",
          ("Configure", "agents/how-to/configure-voice-agent"),
          ("Telephony channels", "agents/how-to/voice-agent-telephony-channels"),
          ("SIP", "agents/how-to/voice-agent-telephony-channels-sip"),
          ("Best practices", "agents/concepts/voice-agent-best-practice"),
          ("Observability", "agents/concepts/voice-agent-observability"),
          ("Pricing", "agents/concepts/voice-agent-pricing"),
          ("Migrate from Voice Live", "agents/how-to/migrate-from-voice-live"), d=(8, 10)),
        r("Hosted agents", "ga",
          "Your code or framework in per-session VM-isolated sandboxes; Responses, Invocations, Invocations (WebSocket) and Activity protocols; 0.5, 1 or 2 vCPU",
          "agents/concepts/hosted-agents",
          ("Runtime components", "agents/concepts/runtime-components"),
          ("Hosted-agent contract", "agents/concepts/hosted-agent-contract"),
          ("Quickstart", "agents/quickstarts/quickstart-hosted-agent"),
          ("Deploy", "agents/how-to/deploy-hosted-agent"), ("Manage", "agents/how-to/manage-hosted-agent"),
          ("Manage sessions", "agents/how-to/manage-hosted-sessions"), d=11),
        r("Microsoft Copilot harness", "pre",
          "Optional runtime for prompt agents with built-in file, shell, web-fetch and subagent tools; chosen only at creation",
          "agents/how-to/use-tools-skills-copilot-harness",
          ("Web research agent quickstart", "agents/quickstarts/create-web-research-agent"), plus=True),
        r("Workflows", "ret",
          "Declarative multi-agent and step orchestration; preview and retiring 2026-12-01 (as of 2026-11-03), use Microsoft Agent Framework",
          "agents/concepts/workflow", d=9),
        r("Autopilots", "pre",
          "Blueprint from a hosted agent, hired as instances that each get an agent identity and agent user account (mail, calendar, Teams presence); Frontier program",
          "agents/concepts/autopilot-overview", ("Lifecycle", "agents/concepts/autopilot-lifecycle"),
          ("Agent 365 how-to", "agents/how-to/agent-365"), plus=True, d=4),
    ]),
    Cluster("Triggers, protocols and identity", [
        r("Routines", "ga",
          "Trigger (timer, recurring schedule, GitHub issue, Teams channel message) runs an agent; identity and run history stay in the project",
          "agents/concepts/routines", ("Use routines", "agents/how-to/use-routines")),
        r("Agent-to-agent (A2A)", "ga",
          "Call other agents and expose your own A2A endpoint; v1.0 GA, v0.3 preview; the a2a_preview tool type is preview",
          "agents/how-to/tools/agent-to-agent",
          ("Enable an A2A endpoint", "agents/how-to/enable-agent-to-agent-endpoint"),
          ("A2A authentication", "agents/concepts/agent-to-agent-authentication")),
        r("Responses API for agents", "ga", "Stateful API; supports the ephemeral-agents pattern",
          "agents/quickstarts/responses-api"),
        r("Microsoft Agent 365 integration", "unk",
          "Registry sync of published agents, autopilots, observability data to Agent 365 (a365LoggingEnabled); autopilots need Frontier",
          "agents/concepts/agent-365-integration",
          ("Grant permissions", "agents/how-to/grant-agent-365-permissions"),
          ("Data collection", "agents/how-to/configure-agent-365-data-collection")),
        r("Agent identity", "gap",
          "Entra Agent ID blueprint + identity per agent; the on-behalf-of 'agent identity as actor' flow is preview",
          "agents/concepts/agent-identity",
          ("Identity and access overview", "agents/concepts/identity-access-overview"),
          ("Endpoint authorization", "agents/concepts/agent-endpoint-authorization", "pre"),
          ("User delegation", "agents/concepts/user-delegation"),
          ("Delegated consent", "agents/concepts/entra-delegated-access-consent")),
    ]),
    Cluster("Build, ship and run", [
        r("Agent development lifecycle", "ga", "Create, test, trace, evaluate, optimize, publish, monitor",
          "agents/concepts/development-lifecycle"),
        r("CI/CD for agents", "unk", "azd with GitHub Actions or Azure DevOps templates; production promotion; Terraform",
          "agents/quickstarts/set-up-cicd-hosted-agent", ("CI/CD with the CLI", "agents/how-to/set-up-ci-cd-cli"),
          ("Production deploy", "agents/how-to/deploy-hosted-agent-production"),
          ("Terraform", "agents/how-to/deploy-hosted-agent-terraform")),
        r("Agent debugging tools", "unk", "Inspector, test, debug, doctor, logs and telemetry export",
          "agents/how-to/agent-inspector", ("Test", "agents/how-to/test-hosted-agent"),
          ("Debug", "agents/how-to/debug-hosted-agent"), ("Doctor", "agents/how-to/agent-doctor"),
          ("Logs", "agents/how-to/monitor-hosted-agent-logs"),
          ("Telemetry export", "agents/how-to/configure-hosted-agent-telemetry")),
        r("Voice with hosted agents", "unk",
          "Custom speech-to-speech or cascaded pipeline in your container over invocations_ws (Pipecat, LiveKit, Voice Live), or a Voice Live wrapper around a text agent",
          "agents/how-to/build-voice-agent",
          ("Voice-first with a hosted agent", "how-to/voice-first-with-hosted-agent"),
          ("Voice Live + hosted agent", SPEECH + "how-to-voice-live-hosted-agent-integration"), plus=True, d=8),
        r("Long-running hosted agents", "pre",
          "Durable work identity, lease-based crash recovery, stream replay, steerable turns, human-in-the-loop approval, durable state, cancel",
          "agents/concepts/long-running-agent-resilience",
          ("Reference", "agents/concepts/long-running-agent-reference"),
          ("State store", "agents/concepts/agent-state-store"),
          ("Resilient deploy", "agents/how-to/deploy-resilient-agent"),
          ("Steerable deploy", "agents/how-to/deploy-steerable-agent"),
          ("Recover work", "agents/how-to/recover-long-running-work"), ("Steer", "agents/how-to/steer-hosted-agent"),
          ("Cancel a turn", "agents/how-to/cancel-hosted-agent-turn"),
          ("Human in the loop", "agents/how-to/add-human-in-the-loop"),
          ("Stream with reconnect", "agents/how-to/stream-with-reconnect"),
          ("Task state", "agents/how-to/manage-task-state"), plus=True, d=3),
        r("Hosted-agent platform details", "unk",
          "azure.yaml and agent.yaml schema, token service, permissions, env vars, protocol adapter, on-behalf-of forwarding, session isolation, BYO and private ACR",
          "agents/concepts/azure-yaml-reference", ("agent.yaml", "agents/concepts/agent-yaml-reference"),
          ("Token service", "agents/concepts/hosted-agent-token-service"),
          ("Permissions", "agents/concepts/hosted-agent-permissions"),
          ("Author azure.yaml", "agents/how-to/author-azure-yaml"),
          ("Protocol adapter", "agents/how-to/add-protocol-adapter"),
          ("On-behalf-of flow", "agents/how-to/use-on-behalf-of-flow"),
          ("Per-user sessions", "agents/how-to/isolate-sessions-per-user"),
          ("Multiplex users", "agents/how-to/multiplex-session-users"),
          ("Isolation keys", "agents/how-to/pass-isolation-keys"),
          ("Private registry", "agents/how-to/private-registry-connections"),
          ("Private ACR deploy", "agents/how-to/deploy-hosted-agent-private-azure-container-registry"), plus=True),
        r("Publish and share", "gap",
          "Publish to Microsoft Copilot and Teams (portal or REST/VNet), voice-agent channels and the Entra Agent Registry; legacy Agent Applications",
          "agents/how-to/publish-copilot",
          ("Publish in a VNet", "agents/how-to/publish-copilot-virtual-network"),
          ("Voice-agent channels", "agents/how-to/voice-agent-channels-publish"),
          ("Agent Applications", "agents/how-to/agent-applications"),
          ("Migrate Agent Applications", "agents/how-to/migrate-agent-applications"), plus=True),
        r("Models, configuration and structured inputs", "unk",
          "Connected Foundry models, BYO models via AI gateway, agent configuration and sharing, runtime structured inputs",
          "agents/how-to/connected-models", ("AI gateway", "agents/how-to/ai-gateway"),
          ("Configure an agent", "agents/how-to/configure-agent"),
          ("Structured inputs", "agents/how-to/structured-inputs"), plus=True),
        r("Limits, quotas, regions and FAQ", "ga",
          "Defaults as of 2026-11-03: 1,000 concurrent hosted sessions per subscription per region (2,000 in 7 regions), 128 tools and 1,000 versions per agent",
          "agents/concepts/limits-quotas-regions", ("Azure Government", "agents/concepts/azure-government"),
          ("FAQ", "agents/faq"), plus=True),
        r("Classic to new agents migration", "ga",
          "Move Assistants and classic agents to Responses-based agents; a tag can disable classic agent creation",
          "agents/how-to/migrate", ("Disable classic agents", "agents/how-to/disable-classic-agents"), plus=True, d=12),
    ]),
])

# ================================================================================================ AREA 4
A4 = Area(4, "Tools", "Tools", "orange",
          "What an agent can call: catalog, Toolbox, built-in tools, MCP, connectors, skills and Foundry Tools", [
    Cluster("Catalog, Toolbox and governance", [
        r("Tool catalog", "ga",
          "Browse every tool (1,400+ in the portal catalog as of 2026-11-03); each tool carries its own GA or preview label",
          "agents/concepts/tool-catalog"),
        r("Toolbox", "gap",
          "Curated tools and skills behind one MCP-compatible endpoint with central auth, guardrails and immutable versions; hosted-agent toolboxes GA, prompt-agent toolboxes preview",
          "agents/concepts/toolbox-overview", ("Use a Toolbox", "agents/how-to/tools/toolbox"),
          ("Hosted-agent toolbox", "agents/how-to/tools/use-toolbox-hosted-agent"),
          ("Quickstart", "agents/quickstarts/quickstart-toolbox-agent"),
          ("Tool authentication", "agents/how-to/tools/tool-authentication"),
          ("Network isolation", "agents/how-to/tools/toolbox-network-isolation"),
          ("Best practices", "agents/concepts/tool-best-practice")),
        r("Tool search", "ga",
          "Hide tool definitions and expose tool_search + call_tool meta-tools; pin and auto-pin; toolbox only",
          "agents/how-to/tools/tool-search"),
        r("MCP and tool governance", "pre",
          "Route MCP tools through an AI gateway (APIM); applies to new portal-created MCP tools without managed OAuth",
          "agents/how-to/tools/governance", plus=True),
    ]),
    Cluster("Built-in agent tools", [
        r("Function calling", "ga", "Your own functions with structured arguments, executed client-side",
          "agents/how-to/tools/function-calling"),
        r("Code interpreter", "ga", "Run generated code in a sandbox to analyze data and produce files",
          "agents/how-to/tools/code-interpreter"),
        r("Custom code interpreter", "pre", "Bring your own runtime for the code-interpreter tool",
          "agents/how-to/tools/custom-code-interpreter", plus=True),
        r("File search", "ga",
          "Ground answers in uploaded files through managed vector stores: 10,000 files per store, 512 MB per file",
          "agents/how-to/tools/file-search", ("Vector stores", "agents/concepts/vector-stores")),
        r("Web search", "ga", "Web Search tool; needs no extra resource", "agents/how-to/tools/web-search",
          ("Web grounding overview", "agents/how-to/tools/web-overview")),
        r("Grounding with Bing Search", "ga",
          "First-party consumption service: DPA does not apply and data leaves the compliance and geo boundary",
          "agents/how-to/tools/bing-tools", ("Manage Bing grounding", "agents/how-to/manage-grounding-with-bing")),
        r("Grounding with Bing Custom Search", "pre", "Ground agent responses with web data using Bing Custom Search",
          "agents/how-to/tools/bing-tools", plus=True),
        r("Browser automation", "unk",
          "Playwright Workspaces-backed browser sessions with Live View, take-control and private-site browsing (public preview)",
          "agents/how-to/tools/browser-automation",
          ("Hosted-agent quickstart", "agents/how-to/tools/browser-automation-hosted-agent-quickstart"), d=1),
        r("Computer use", "pre", "Operate a virtual computer UI; security risks include prompt injection",
          "agents/how-to/tools/computer-use"),
        r("Image generation (agent tool)", "pre", "Generate images from an agent", "agents/how-to/tools/image-generation"),
        r("OpenAPI tool", "ga", "Call any REST API described by an OpenAPI specification", "agents/how-to/tools/openapi"),
        r("Azure AI Search tool", "ga", "Use an AI Search index as agent knowledge (also listed in area 5)",
          "agents/how-to/tools/ai-search"),
        r("Azure Functions tool", "unk", "Queue-based AzureFunctionTool; Flex Consumption recommended",
          "agents/how-to/tools/azure-functions", d=6),
        r("Reminder tool", "pre", "reminder_preview: a hosted agent schedules itself to run later",
          "agents/how-to/tools/reminder-tool", plus=True),
    ]),
    Cluster("Connectors, skills and Foundry Tools", [
        r("Model Context Protocol (MCP)", "gap",
          "Remote MCP servers (key, Entra agent or project identity, OAuth passthrough or OBO, unauthenticated); long-running operations and managed servers are preview",
          "agents/how-to/tools/model-context-protocol",
          ("Connectors (managed MCP)", "agents/how-to/tools/connectors", "pre"),
          ("MCP authentication", "agents/how-to/mcp-authentication"),
          ("Build your own MCP server", "mcp/build-your-own-mcp-server"),
          ("Private tool catalog", "agents/how-to/private-tool-catalog", "pre")),
        r("SharePoint tool", "pre", "SharePoint grounding for agents", "agents/how-to/tools/sharepoint"),
        r("Fabric data agent tool", "ret",
          "Preview; deprecation scheduled 2026-11-06 (as of 2026-11-03), use Fabric IQ instead", "agents/how-to/tools/fabric"),
        r("Skills", "pre",
          "Reusable, versioned multi-step behavior (the how, where a tool is the what); attach to a toolbox; private catalog",
          "agents/how-to/tools/skills", ("Skills with the shell tool", "agents/how-to/tools/skills-shell-tool"),
          ("Private skill catalog", "agents/how-to/private-skill-catalog")),
        r("Foundry Tools as agent tools", "unk",
          "Speech STT and TTS tool for agents, Language (CLU, PII, detection) and Translator (text, document)",
          "agents/how-to/tools/azure-ai-speech",
          ("Language in agents", AI + "language-service/concepts/foundry-tools-agents"),
          ("Text translation", AI + "translator/text-translation/overview"),
          ("Document translation", AI + "translator/document-translation/overview")),
    ]),
])

# ================================================================================================ AREA 5
A5 = Area(5, "Knowledge and memory", "Knowledge, retrieval and memory", "teal",
          "How agents and apps ground answers in your data: RAG, AI Search, vector stores, the IQ layer and memory", [
    Cluster(None, [
        r("Retrieval-augmented generation (RAG)", "doc", "Patterns for grounding model responses in your own content",
          "concepts/retrieval-augmented-generation"),
        r("Azure AI Search integration", "ga", "Use an Azure AI Search index as agent knowledge (tool)",
          "agents/how-to/tools/ai-search"),
        r("Vector stores", "ga", "Managed storage and indexing for file search: parse, chunk, embed; keyword and semantic",
          "agents/concepts/vector-stores"),
        r("Foundry IQ", "gap",
          "Knowledge base = knowledge sources (Blob, SharePoint, OneLake, public web) + agentic retrieval; ACL sync, Purview labels, runs as the caller's Entra identity",
          "agents/concepts/what-is-foundry-iq", ("FAQ", "agents/concepts/foundry-iq-faq"),
          ("Connect to an agent", "agents/how-to/foundry-iq-connect"),
          ("Private-network tutorial", "agents/how-to/foundry-iq-tutorial-private-overview"),
          ("Hosted-agent quickstart", "agents/quickstarts/quickstart-foundry-iq-hosted-agent"), d=5),
        r("Fabric IQ", "pre",
          "Reason over Fabric and OneLake through an ontology (entity types, NL2Ontology), Fabric data agent and Power BI semantic models",
          "agents/how-to/tools/fabric-iq"),
        r("Work IQ", "pre",
          "Microsoft 365 work data (mail, meetings, files, chats) as a peer agent through A2A, with user context and M365 permissions",
          "agents/how-to/tools/work-iq"),
        r("Memory", "pre",
          "Managed long-term memory stores: user profile and chat summary types, item CRUD, default TTL; extraction, consolidation, retrieval",
          "agents/concepts/what-is-memory", ("Use memory", "agents/how-to/memory-usage"),
          ("Hosted-agent quickstart", "agents/quickstarts/quickstart-memory-hosted-agent"),
          ("LangChain memory", "how-to/develop/langchain-memory")),
    ]),
])

# ================================================================================================ AREA 6
A6 = Area(6, "Observability", "Observability", "violet",
          "Understand what agents and models are doing in production: tracing, monitoring, insights, logs and alerts", [
    Cluster(None, [
        r("Foundry Observability", "gap",
          "Evaluation, monitoring and tracing built on OpenTelemetry and Application Insights; core GA, Monitoring preview",
          "concepts/observability"),
        r("Tracing", "gap",
          "End-to-end spans for LLM, tool and agent steps. GA for prompt and hosted agents; preview for workflow and external agents, Tracing VNet and convert-to-dataset",
          "observability/concepts/trace-agent-concept", ("Set up tracing", "observability/how-to/trace-agent-setup"),
          ("Trace Replay", "observability/how-to/trace-agent-replay"),
          ("Client-side spans", "observability/how-to/trace-agent-client-side"),
          ("Frameworks", "observability/how-to/trace-agent-framework"),
          ("Traces to dataset", "observability/how-to/traces-to-dataset", "pre"),
          ("Annotations", "observability/how-to/trace-annotations"),
          ("Sensitive content", "observability/how-to/traces-sensitive-content"),
          ("Entra ingestion", "observability/how-to/trace-ingestion-entra-authentication"),
          ("Trace data", "observability/concepts/trace-data"),
          ("Troubleshooting", "observability/how-to/troubleshooting"), d=2),
        r("Agent monitoring dashboard", "pre",
          "Health, usage, quality and cost over time; continuous-evaluation setup; agent metrics",
          "observability/how-to/how-to-monitor-agents-dashboard"),
        r("Insights in Foundry", "pre", "Trace-backed findings with evidence, likely cause and a proposed fix",
          "observability/how-to/agent-insights", plus=True),
        r("Model deployment monitoring", "unk",
          "Latency, throughput and errors for model endpoints, including the model router",
          "foundry-models/how-to/monitor-models", ("Monitor the model router", "openai/how-to/monitor-model-router")),
        r("End-user feedback logging", "pre", "Collect feedback signals from your application",
          "observability/how-to/log-end-user-feedback"),
        r("Notification Center", "unk", "Security, policy and performance alerts for your AI solutions in one place",
          "concepts/concept-notification-center"),
        r("External agent registration", "pre",
          "Bring agents running elsewhere into Foundry observability, evaluation and optimization; replaces custom-agent registration",
          "agents/how-to/register-external-agent",
          ("Migrate from custom agents", "control-plane/migrate-custom-to-external-agent")),
        r("Diagnostic logging", "ga",
          "Audit Logs, Request and Response Logs, Azure OpenAI Request Usage and AllMetrics to Log Analytics, Storage or Event Hubs",
          "how-to/diagnostic-logging"),
        r("Service Health alerts and known issues", "ga", "Stay informed of regressions; known-issue list",
          "how-to/stay-informed-service-health", ("Known issues", "reference/foundry-known-issues"), plus=True),
    ]),
])

# ================================================================================================ AREA 7
EV = "concepts/evaluation-evaluators/"
CE = "observability/how-to/cloud-evaluation"
A7 = Area(7, "Evaluation and optimization", "Evaluation and optimization", "violet",
          "Measure and improve quality, safety and cost: evaluators, datasets, optimizers, red teaming and CI/CD gates", [
    Cluster("Score and analyze", [
        r("Evaluations", "gap",
          "Score models and agents from the portal, SDK or CI/CD; turn-level and conversation-level; some evaluators and features are preview",
          "concepts/evaluation-overview", ("Evaluate an app", "how-to/evaluate-generative-ai-app"),
          ("Evaluate results", "how-to/evaluate-results")),
        r("Built-in evaluators", "ga",
          "General-purpose, textual similarity, RAG, risk and safety, agent, Azure OpenAI graders and rubric evaluators; Groundedness Pro is preview",
          "concepts/built-in-evaluators", ("General purpose", EV + "general-purpose-evaluators"),
          ("Textual similarity", EV + "textual-similarity-evaluators"), ("RAG", EV + "rag-evaluators"),
          ("Risk and safety", EV + "risk-safety-evaluators"), ("Agent", EV + "agent-evaluators"),
          ("Azure OpenAI graders", EV + "azure-openai-graders"), ("Rubric", EV + "rubric-evaluators")),
        r("Custom evaluators", "pre", "Prompt-based or code-based scoring logic", EV + "custom-evaluators"),
        r("Agent evaluation", "ga", "Evaluate agent trajectories, tool calls and task completion",
          "observability/how-to/evaluate-agent"),
        r("Continuous evaluation", "pre",
          "Sample production traffic on an ongoing basis (hosted agents: interval in hours; prompt agents: sampling rate)",
          "observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation"),
        r("Cloud evaluation via SDK", "gap",
          "Cloud runs over datasets, targets, deployed interactions, conversations and simulated or synthetic conversations; some parts preview",
          CE, ("Datasets", CE + "-datasets"), ("Targets", CE + "-targets"),
          ("Deployed interactions", CE + "-deployed-interactions"), ("Conversations", CE + "-conversations"),
          ("Deployed conversations", CE + "-deployed-conversations"),
          ("Simulate conversations", CE + "-simulate-conversations"),
          ("Synthetic conversations", CE + "-synthetic-conversations"),
          ("Synthetic data", CE + "-synthetic-data"), ("Results", CE + "-results"),
          ("Admin-connected models", "observability/how-to/evaluate-admin-connected-models")),
        r("Evaluation datasets", "unk",
          "Overview, schema, synthetic generation and traces-to-dataset (traces-to-dataset is preview)",
          "observability/how-to/evaluation-datasets", ("Schema", "observability/how-to/evaluation-dataset-schema"),
          ("Synthetic generation", "observability/how-to/evaluation-dataset-synthetic"),
          ("Traces to dataset", "observability/how-to/traces-to-dataset", "pre")),
        r("Human evaluation", "pre", "Structured human judgments and annotated traces",
          "observability/how-to/human-evaluation"),
        r("Cluster analysis", "pre", "Cluster failures and root causes in evaluation results",
          "observability/how-to/cluster-analysis", plus=True),
        r("Benchmark evaluations", "pre", "Run benchmark evaluations on models",
          "observability/how-to/benchmark-evaluations", plus=True),
        r("Evaluation platform limits", "ga",
          "Permissions, regions and rate limits, VNet support and the safety-evaluations transparency note",
          "observability/how-to/evaluation-permissions",
          ("Regions and limits", "concepts/evaluation-regions-limits-virtual-network"),
          ("Virtual network", "concepts/evaluation-virtual-network"),
          ("Transparency note", "concepts/safety-evaluations-transparency-note"), plus=True),
    ]),
    Cluster("Optimize, red-team and gate", [
        r("Prompt optimizer", "unk", "Improve agent instructions automatically from evaluation results",
          "observability/how-to/prompt-optimizer"),
        r("Agent optimizer", "pre",
          "Evaluate, then generate candidates for instructions, skills, tool descriptions and model choice; needs Foundry-Features: AgentsOptimization=V2Preview; limited preview",
          "agents/concepts/agent-optimizer-overview", ("Costs", "agents/concepts/agent-optimizer-costs"),
          ("Optimize a prompt agent", "agents/quickstarts/quickstart-optimize-prompt-agent"),
          ("Optimize a hosted agent", "agents/quickstarts/quickstart-optimize-hosted-agent"),
          ("Make an agent optimizer-ready", "agents/how-to/make-agent-optimizer-ready"),
          ("Create an optimizer dataset", "agents/how-to/create-optimizer-dataset"),
          ("Optimization targets", "agents/how-to/optimize-agent-targets"), d=13),
        r("AI red teaming", "gap", "Automated adversarial scans: cloud runs are GA, local runs are preview",
          "concepts/ai-red-teaming-agent", ("Run in the cloud", "how-to/develop/run-ai-red-teaming-cloud"),
          ("Run locally", "how-to/develop/run-scans-ai-red-teaming-agent", "pre")),
        r("Evaluations in CI/CD", "pre", "Gate releases with evaluations in GitHub Actions or Azure DevOps",
          "how-to/evaluation-github-action", ("Azure DevOps", "how-to/evaluation-azure-devops")),
        r("azd evaluation", "pre", "azd ai agent eval (quick) and azd ai eval (project, CI gates)",
          "observability/how-to/azure-developer-cli-evaluation", plus=True),
    ]),
])

# ================================================================================================ AREA 8
CS = AI + "content-safety/"
A8 = Area(8, "Trust and safety", "Trust and safety", "pink",
          "Guardrails, risk detectors, content safety and responsible AI", [
    Cluster(None, [
        r("Guardrails and controls", "gap",
          "A guardrail is a named set of controls (risk + intervention points + action). Intervention points: user input, tool call (preview), tool response (preview), output. GA for Models, preview for Agents; hosted-agent network egress controls are preview",
          "guardrails/guardrails-overview", ("Create guardrails", "guardrails/how-to-create-guardrails"),
          ("Intervention points", "guardrails/intervention-points"),
          ("Default safety policies", "guardrails/default-safety-policies"),
          ("Hosted-agent guardrails", "agents/concepts/hosted-agent-guardrails"),
          ("Add to a hosted agent", "agents/how-to/add-hosted-agent-guardrails")),
        r("Risk detectors", "ga",
          "Harm categories and severity levels, Prompt Shields (jailbreak, prompt injection), groundedness, PII, protected material, content streaming",
          "openai/concepts/content-filter-severity-levels",
          ("Prompt Shields", "openai/concepts/content-filter-prompt-shields"),
          ("Groundedness", "openai/concepts/content-filter-groundedness"),
          ("PII", "openai/concepts/content-filter-personal-information"),
          ("Protected material", "openai/concepts/content-filter-protected-material"),
          ("Protected material (code)", CS + "quickstart-protected-material-code"),
          ("Content streaming", "openai/concepts/content-streaming")),
        r("Custom filtering", "unk", "Block lists and custom categories (Content Safety)",
          "guardrails/how-to-create-guardrails", ("Blocklists", CS + "quickstart-blocklist"),
          ("Custom categories", CS + "concepts/custom-categories")),
        r("Task adherence", "pre",
          "Detect agents straying from the assigned task (Content Safety agent:analyzeTaskAdherence, API 2024-12-15-preview)",
          "guardrails/task-adherence"),
        r("Guided Guardrail", "pre", "Guided setup experience for agent guardrails", "guardrails/guided-set-up"),
        r("Third-party guardrail integrations", "unk", "Plug partner safety systems into Foundry intervention points",
          "guardrails/third-party-integrations"),
        r("Safety system messages and best practices", "doc",
          "Templates and guidance for safety system messages; planning red teaming for LLMs",
          "openai/concepts/safety-system-message-templates", ("System message design", "openai/concepts/system-message"),
          ("Red teaming LLMs", "openai/concepts/red-teaming"), plus=True),
        r("Responsible AI docs", "doc",
          "Transparency notes, data privacy, limited access, abuse monitoring, Customer Copyright Commitment and Code of Conduct",
          "responsible-use-of-ai-overview",
          ("Agent Service transparency note", "responsible-ai/agents/transparency-note"),
          ("Agent data privacy", "responsible-ai/agents/data-privacy-security"),
          ("Azure OpenAI transparency note", "responsible-ai/openai/transparency-note"),
          ("Limited access", "responsible-ai/openai/limited-access"),
          ("Abuse monitoring", "openai/concepts/abuse-monitoring"),
          ("Customer Copyright Commitment", "responsible-ai/openai/customer-copyright-commitment"),
          ("Code of Conduct", "https://learn.microsoft.com/en-us/legal/ai-code-of-conduct")),
        r("Content provenance", "unk", "Provenance and disclosure plus text watermarking for GPT deployments",
          "responsible-ai/content-safety/provenance-disclosure",
          ("Enable text watermarking", "responsible-ai/content-safety/enable-text-watermarking-gpt-models"), plus=True),
    ]),
])

# ================================================================================================ AREA 9
A9 = Area(9, "Manage, secure, govern", "Manage, secure and govern", "grape",
          "Platform administration at scale: control plane, policy, identity, network, keys, cost, resilience and rollout", [
    Cluster("Control plane and policy", [
        r("Foundry resources and projects", "ga",
          "Resource = governance boundary, project = development boundary; default project and capability settings",
          "how-to/create-projects", ("Architecture", "concepts/architecture"), ("Planning", "concepts/planning"),
          ("Multi-service resource", AI + "multi-service-resource")),
        r("Foundry control plane", "pre",
          "Fleet Overview, Assets and Compliance (Operate) plus Quota and AI Gateway (Manage); Defender, Purview, Entra and Azure Policy integration; drift and cost anomalies",
          "control-plane/overview", ("Manage agents", "control-plane/how-to-manage-agents"),
          ("Compliance and security", "control-plane/how-to-manage-compliance-security"),
          ("Entra admin governance", "control-plane/govern-agent-infrastructure-entra-admin")),
        r("Fleet monitoring", "pre", "Health, performance and cost across many agents, multi-platform",
          "control-plane/monitoring-across-fleet"),
        r("Token limit enforcement", "unk", "Cap model consumption per agent, project or team through the AI gateway",
          "control-plane/how-to-enforce-limits-models"),
        r("Guardrail policy for models", "pre", "Organization-level guardrail policies with bulk remediation",
          "control-plane/quickstart-create-guardrail-policy", plus=True),
        r("AI gateway integration", "pre",
          "Front Foundry with Azure API Management for routing and policy; bring your own models",
          "configuration/enable-ai-api-management-gateway-portal", ("AI gateway for agents", "agents/how-to/ai-gateway")),
        r("Custom agent registration", "ret",
          "Existing custom agents in the control plane; no new registrations, retiring 2027-04-30 (as of 2026-11-03), use external agents",
          "control-plane/register-custom-agent",
          ("Migrate to external agents", "control-plane/migrate-custom-to-external-agent"), plus=True),
        r("Azure Policy support", "ga",
          "Built-in and custom definitions; model-deployment policy (approved models, publishers); disable preview features",
          "how-to/model-deployment-policy", ("Custom policy definition", "how-to/custom-policy-definition"),
          ("Disable preview features", "how-to/disable-preview-features"),
          ("Policy reference", AI + "policy-reference")),
    ], "grape"),
    Cluster("Identity, network and keys", [
        r("Role-based access control", "ga",
          "Foundry User, Project Manager, Account Owner, Owner and Agent Consumer roles at resource, project and agent scope",
          "concepts/rbac-foundry", ("Administrator guide", "concepts/administrator-guide"),
          ("Authentication and authorization", "concepts/authentication-authorization-foundry")),
        r("Keyless authentication", "ga", "Microsoft Entra ID instead of API keys; a custom subdomain is required",
          "foundry-models/how-to/configure-entra-id"),
        r("Customer-managed keys", "ga", "CMK for Foundry data; BYO Key Vault for connection secrets",
          "concepts/customer-managed-keys", ("Encryption keys in the portal", "concepts/encryption-keys-portal"),
          ("Key Vault connection", "how-to/set-up-key-vault-connection")),
        r("Network isolation", "gap",
          "Private endpoints, managed VNet (CLI group preview), BYO VNet, network security perimeter, on-premises access",
          "agents/concepts/networking-options", ("Private link", "how-to/configure-private-link"),
          ("Managed VNet", "how-to/managed-virtual-network"),
          ("On-premises access", "how-to/access-on-premises-resources"),
          ("Network security perimeter", "how-to/add-foundry-to-network-security-perimeter"),
          ("Agent VNets", "agents/how-to/virtual-networks"),
          ("Networking deep dive", "agents/concepts/agents-networking-deep-dive")),
    ], "red"),
    Cluster("Cost, resilience and rollout", [
        r("Cost management", "gap", "Meters, budgets and the consolidated view; project-level chargeback is preview",
          "concepts/manage-costs", ("Consolidated view", "concepts/foundry-consolidated-view")),
        r("High availability and disaster recovery", "unk",
          "Resiliency design (no automatic cross-region failover); Agent Service DR for platform outage, resource and data loss",
          "how-to/high-availability-resiliency", ("Agent Service DR", "how-to/agent-service-disaster-recovery"),
          ("Platform DR", "how-to/agent-service-platform-disaster-recovery"),
          ("Operator DR", "how-to/agent-service-operator-disaster-recovery")),
        r("Azure Government", "gap",
          "US Gov Virginia and Arizona at ai.azure.us; a subset of features (as of 2026-11-03 no serverless endpoints, Content Understanding, Agents playground, fine-tuning, batch or VS Code extension)",
          "concepts/foundry-azure-government", ("Agents in Azure Government", "agents/concepts/azure-government"),
          ("Region support", "reference/region-support")),
        r("Infrastructure as code", "ga", "Bicep, Terraform, Azure CLI and ARM", "how-to/create-resource-template",
          ("Terraform", "how-to/create-resource-terraform"),
          ("ARM template reference", "https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts")),
        r("Upgrade and migrate", "ga",
          "Azure OpenAI to Foundry (manual and auto), Inference SDK to OpenAI SDK, classic to new portal",
          "how-to/upgrade-azure-openai", ("Auto upgrade", "how-to/upgrade-azure-openai-auto"),
          ("Inference SDK to OpenAI SDK", "how-to/model-inference-to-openai-migration"),
          ("Navigate from classic", "how-to/navigate-from-classic"), plus=True),
        r("Security baseline, compliance, SLA and pricing", "ga",
          "Azure security baseline, data privacy, compliance offerings, SLA and the pricing page",
          "https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-ai-foundry-security-baseline",
          ("Data privacy", "responsible-ai/openai/data-privacy"),
          ("Compliance offerings", "https://aka.ms/AzureCompliance"),
          ("Pricing", "https://azure.microsoft.com/en-us/pricing/details/microsoft-foundry/"), plus=True),
    ], "gray"),
])

# ================================================================================================ AREA 10
A10 = Area(10, "APIs and SDKs", "APIs and SDKs", "gray",
           "Programmatic surfaces for building on Foundry: reference, endpoints, REST, management API and SDKs", [
    Cluster(None, [
        r("Foundry API reference", "ga", "Interactive reference for Foundry data-plane operations",
          "https://ai.azure.com/api-reference/"),
        r("Foundry Models endpoints", "ga",
          "Call deployments by alias; Azure OpenAI v1 route (/openai/v1/); Responses and Chat Completions; Entra scope https://ai.azure.com/.default",
          "foundry-models/concepts/endpoints"),
        r("Foundry v1 REST API", "ga",
          "OpenAI-compatible surface: chat, responses, embeddings, files, fine-tuning, vector stores, evals",
          "https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/?view=rest-microsoft-foundry-v1"),
        r("Resource management API", "ga",
          "ARM, Bicep and Azure CLI for Microsoft.CognitiveServices/accounts; GA API versions include 2026-09-01, preview 2026-09-15-preview (as of 2026-11-03)",
          "https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts?pivots=deployment-language-bicep"),
        r("Azure OpenAI API lifecycle and references", "ga",
          "API versions and lifecycle, SDK language support, monitoring data reference, Realtime and GPT-Live event references",
          "openai/api-version-lifecycle", ("Language support", "openai/supported-languages"),
          ("Monitoring data reference", "openai/monitor-openai-reference"),
          ("Realtime events", "openai/realtime-audio-reference"), ("GPT-Live events", "openai/gpt-live-reference"),
          plus=True),
        r("Foundry SDK reference", "ga", "Python, C#, JavaScript and Java azure-ai-projects packages (2.x line)",
          "https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme",
          ("C#", "https://learn.microsoft.com/en-us/dotnet/api/overview/azure/ai.projects-readme"),
          ("JavaScript", "https://learn.microsoft.com/en-us/javascript/api/overview/azure/ai-projects-readme"),
          ("Java", "https://learn.microsoft.com/en-us/java/api/overview/azure/ai-projects-readme")),
    ]),
])

# ================================================================================================ AREA 11
A11 = Area(11, "Foundry Tools", "Foundry Tools", "teal",
           "Formerly Azure AI Services: prebuilt AI APIs under the Foundry resource (kind AIServices) or as single-service kinds", [
    Cluster(None, [
        r("Foundry Tools overview", "ga", "Prebuilt AI APIs under the Foundry resource or as single-service resources",
          AI + "what-are-ai-services", plus=True),
        r("Azure Speech", "gap",
          "Speech to text, text to speech (+ avatar, custom voice), translation, speaker recognition; Voice Live; some features preview",
          SPEECH + "overview", plus=True),
        r("Azure Language", "ga",
          "Language detection, PII, Text Analytics for Health and prebuilt and custom NER continue", AI + "language-service/overview",
          plus=True),
        r("Azure Language: retiring features", "ret",
          "Retiring 2029-03-31: key phrases, sentiment, summarization, entity linking, CLU, CQA, custom text classification, orchestration workflow; Language Studio retires 2027-03-20 (as of 2026-11-03)",
          AI + "language-service/overview", plus=True),
        r("Azure Translator", "ga", "Text and document translation, 100+ languages; resource-level only (not project-scoped)",
          AI + "translator/overview", plus=True),
        r("Azure Vision, Custom Vision and Face", "ga", "Image analysis, OCR and Face", AI + "computer-vision/overview",
          plus=True),
        r("Content Understanding", "unk",
          "Multimodal (documents, images, video, audio) to user-defined structured output with confidence and grounding; BYO storage required; classic portal only at GA",
          AI + "content-understanding/overview", plus=True, d=14),
        r("Document Intelligence", "ga", "Turn documents into structured data", AI + "document-intelligence/overview",
          plus=True),
        r("Content Safety", "ga", "Harm detection APIs, Prompt Shields, protected material and custom categories",
          AI + "content-safety/overview", plus=True),
        r("Azure AI Search (Microsoft.Search)", "gap",
          "Retrieval and agentic-retrieval substrate for Foundry IQ; agentic retrieval is partly preview",
          "https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search", plus=True),
        r("Retired Foundry-adjacent services", "dead",
          "Anomaly Detector, Content Moderator, LUIS, Metrics Advisor, Personalizer and QnA Maker are retired",
          AI + "what-are-ai-services", plus=True),
    ]),
])

A2.footer = ("info", "Calling a deployment",
             "Call a deployment by name on one endpoint. The Responses API works with Azure OpenAI models and the Foundry Models sold by Azure that support it (otherwise 400 Model not supported: use Chat Completions). Claude uses the separate /anthropic Messages endpoint.",
             [("Foundry Models endpoints", learn("foundry-models/concepts/endpoints"))])
A3.footer = ("key", "Core objects",
             "An agent is a named, versioned asset; a conversation holds persisted items; a response is the unit of execution. Conversations, items, responses and agent versions replace Assistants threads, messages, runs and assistants.",
             [("Runtime components", learn("agents/concepts/runtime-components"))])

AREAS: list = [A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11]


# ================================================================================================ drift notes
class DriftBox(Rect2):
    """Numbered list of status contradictions: tag + clickable title + verdict pill + one cautious paragraph."""

    def __init__(self, w: float, title: str, sub: str, items: list, theme="orange", cols: int = 1):
        self.w, self.th = w, THEMES[theme]
        self.ops: list = []
        y = PAD
        self.ops.append(("text", PAD, y, title, 24, self.th.deep, None))
        y += 24 * LH + 2
        sl = metrics.wrap_text(sub, w - 2 * PAD, 14)
        self.ops.append(("text", PAD, y, "\n".join(sl), 14, MUTED_TXT, None))
        y += len(sl) * 14 * LH + 14
        gap = 30
        cw = (w - 2 * PAD - gap * (cols - 1)) / cols
        # measure items for the sub-column width, then fill the columns top-down
        sized = []
        for it in items:
            n, name, st, body, url = it
            nl = metrics.wrap_text(name, cw - 46 - PILL_W - 10, 16)
            bl = metrics.wrap_text(body, cw - 46, 14)
            head_h = max(len(nl) * 16 * LH, PILL_H)
            sized.append((it, nl, bl, head_h, head_h + 2 + len(bl) * 14 * LH + 14))
        total = sum(s[4] for s in sized)
        col_y = [y] * cols
        ci, acc = 0, 0.0
        for it, nl, bl, head_h, ih in sized:
            if ci < cols - 1 and acc + ih / 2 > total / cols:
                ci, acc = ci + 1, 0.0
            x0 = PAD + ci * (cw + gap)
            yy = col_y[ci]
            n, name, st, body, url = it
            tx = x0 + 46
            self.ops.append(("tag", x0 + 18, yy + 17, f"D{n}"))
            self.ops.append(("text", tx, yy + (head_h - len(nl) * 16 * LH) / 2, "\n".join(nl), 16, self.th.deep, url))
            self.ops.append(("pill", x0 + cw - PILL_W, yy, st))
            self.ops.append(("text", tx, yy + head_h + 2, "\n".join(bl), 14, INK, None))
            col_y[ci] += ih
            acc += ih
        self.h = max(col_y) - 14 + PAD
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h: Optional[float] = None) -> "DriftBox":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=3, dash="dashed")
            for op in self.ops:
                if op[0] == "text":
                    _, dx, dy, s, size, color, link = op
                    cv.text(x + dx, y + dy, s, size=size, color=color, link=link)
                elif op[0] == "pill":
                    draw_pill(cv, x + op[1], y + op[2], op[3])
                elif op[0] == "tag":
                    numbered(cv, x + op[1], y + op[2], op[3], theme="red", d=36, size=14)
        cv.register("drift box", x, y, self.w, H)
        return self


DRIFT_1 = [
    (1, "Browser automation", "unk",
     "The tool page (2026-11-02) and a DevBlog post (2026-10-19) say GA; the capability reference and the classic-to-new migration page (2026-10-07) still say preview.",
     learn("agents/how-to/tools/browser-automation")),
    (2, "Trace Replay", "unk",
     "The GA matrix lists tracing, including Trace Replay, as GA for prompt and hosted agents; the Trace Replay how-to title still says preview.",
     learn("observability/how-to/trace-agent-replay")),
    (3, "Long-running hosted agents", "pre",
     "The August What's-new article and the September DevBlog say preview; Learn pages updated 2026-11-02 carry no label. Shown as preview until a GA announcement is found.",
     learn("agents/concepts/long-running-agent-resilience")),
    (4, "Autopilots", "pre",
     "Concept pages carry no label, but the quickstart needs the Microsoft Frontier preview program and an Agent 365 Frontier license (25-seat preview subscription).",
     learn("agents/concepts/autopilot-overview")),
    (5, "Foundry IQ", "gap",
     "The classic-migration page says preview; the GA matrix says partial GA (API-level GA depends on the Search REST API version, portal access is preview).",
     learn("agents/concepts/what-is-foundry-iq")),
    (6, "Azure Functions tool", "unk",
     "The migration page shows GA in classic but No for new agents; a tool page exists (updated 2026-08-24) and the Toolbox table lists it as direct-only.",
     learn("agents/how-to/tools/azure-functions")),
    (7, "Managed compute", "pre",
     "The models overview and classic pages still say managed compute and Hugging Face models need a hub-based project in classic; newer pages call it a preview deployment type in the new portal.",
     learn("concepts/managed-compute-overview")),
    (8, "Voice maturity", "pre",
     "Voice-based prompt agents are preview (Learn banners, Sept DevBlog); July-August DevBlogs call hosted agents with Voice Live integration GA. Two labels, kept separate.",
     learn("agents/quickstarts/prompt-voice-agent")),
    (9, "Workflows", "ret",
     "Preview and retiring 2026-12-01 (GA overview, VS Code page), yet several older pages still present Workflows as a core path.",
     learn("agents/concepts/workflow")),
    (10, "SIP for voice agents", "pre",
     "The agents overview says direct SIP is not a supported customer flow; the SIP how-to (updated 2026-10-30) documents inbound and outbound SIP as preview and region-limited.",
     learn("agents/how-to/voice-agent-telephony-channels-sip")),
    (11, "Hosted agents wording", "ga",
     "Hosted agents went GA in July 2026 (DevBlog), but the private-link page intro still says hosted (preview) agents.",
     learn("how-to/configure-private-link")),
    (12, "Assistants API sunset (2026-08-26, passed)", "dead",
     "The classic-migration page still says sunsets and the GA page says assistants continue in classic until an upgrade is available. Treated as legacy here.",
     learn("agents/how-to/migrate")),
]

DRIFT_2 = [
    (13, "Agent optimizer", "pre",
     "The GA matrix says limited preview, the capability reference says preview, Learn titles carry no label, REST still needs AgentsOptimization=V2Preview, and a September DevBlog called GA a late-September target (unconfirmed).",
     learn("agents/concepts/agent-optimizer-overview")),
    (14, "Content Understanding", "unk",
     "Service shown GA? because the portal experience is classic-only at GA and a September DevBlog adds preview tooling; auth pages also disagree (GA page: Entra only; auth matrix: batch jobs accept keys).",
     AI + "content-understanding/overview"),
]


# ================================================================================================ page furniture
STRIP_VERBS = {(2, 3): "deploy", (3, 4): "attach", (5, 6): "trace", (6, 7): "score", (7, 8): "enforce", (8, 9): "govern"}


def _bar_segments(by: Counter) -> list:
    segs = []
    for st in BAR_ORDER:
        if by.get(st):
            segs.append((st, by[st]))
    return segs


def _tally_text(by: Counter) -> str:
    return "  ".join(f"{STATUS_STYLE[st][0]} {n}" for st, n in _bar_segments(by))


def draw_tile(cv: Canvas, a: Area, x: float, y: float, w: float, h: float, on: bool, other: str) -> None:
    th = THEMES[a.theme]
    n, by = tally(a)
    op = 100 if on else 45
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2.5, dash="solid" if on else "dashed",
            opacity=op)
    nx = x + 12
    if on:
        numbered(cv, nx + 15, y + 27, a.num, theme=a.theme, d=30, size=17)
        name_x = nx + 38
    else:
        name_x = nx
    nl = metrics.wrap_text(a.short if on else f"{a.num}  {a.short}", x + w - 10 - name_x, 16)
    cv.text(name_x, y + 11, "\n".join(nl), size=16, color=th.deep, opacity=op)
    cv.text(nx, y + 58, str(n), size=38, color=INK, opacity=op)
    cv.text(nx + metrics.line_width(str(n), 38) + 8, y + 82, "capabilities", size=13, color=MUTED_TXT, opacity=op)
    if on:
        bx, bw, by_ = nx, w - 24, y + 112
        total = sum(c for _s, c in _bar_segments(by)) or 1
        cx = bx
        for st, c in _bar_segments(by):
            sw_ = max(5.0, bw * c / total)
            f = THEMES[STATUS_STYLE[st][1]]
            s = THEMES[STATUS_STYLE[st][2]]
            cv.rect(cx, by_, sw_, 12, stroke=s.stroke, fill=f.fill, style="solid", sw=1.5, rough=0, round_=False)
            cx += sw_
        tl = metrics.wrap_text(_tally_text(by), w - 24, 12)
        cv.text(nx, y + 130, "\n".join(tl), size=12, color=MUTED_TXT)
        pc = plus_count(a)
        if pc:
            cv.text(nx, y + 130 + len(tl) * 12 * LH + 4, f"+ {pc} not in the reference", size=12,
                    color=th.deep)
    else:
        cv.text(nx, y + 118, other, size=14, color=MUTED_TXT, opacity=70)
    cv.register(f"tile {a.num}", x, y, w, h)


def draw_strip(cv: Canvas, x: float, y: float, active: set, other: str) -> float:
    """Count strip + flow chain over all 11 areas. Returns the bottom y."""
    total = sum(tally(a)[0] for a in AREAS)
    plus_total = sum(plus_count(a) for a in AREAS)
    section_header(cv, x, y, "Atlas map: 11 areas, how they feed each other, and how many capabilities each lists",
                   sub=f"As of 2026-11-03: {total} capabilities across both canvases, {plus_total} of them not in the official capability reference. Dashed tiles live on the other canvas.",
                   size=30, w=W)
    top = y + 150
    n = len(AREAS)
    tw, th_ = 214, 192
    gap = (W - n * tw) / (n - 1)
    tiles = []
    for i, a in enumerate(AREAS):
        tx = x + i * (tw + gap)
        draw_tile(cv, a, tx, top, tw, th_, a.num in active, other)
        t = Rect2()
        t.x, t.y, t.w, t.h = tx, top, tw, th_
        tiles.append(t)
    ym = top + 86
    for (a, b), verb in STRIP_VERBS.items():
        ta, tb = tiles[a - 1], tiles[b - 1]
        dim = a not in active and b not in active
        arrow(cv, [(ta.right + 6, ym), (tb.x - 6, ym)], label=verb, label_size=15, sw=2.5, end_head="arrow",
              opacity=45 if dim else 100)
    plus_x = (tiles[3].right + tiles[4].x) / 2
    cv.text(plus_x - metrics.line_width("+", 36) / 2, ym - 24, "+", size=36, color=MUTED_TXT,
            opacity=100 if (4 in active or 5 in active) else 45)
    bx1, bx2 = tiles[1].x, tiles[8].right
    hbrace(cv, bx1, bx2, top - 12, side="top", depth=14, color="#868e96", sw=2)
    label = "Area 1 (portal, SDKs, azd, VS Code, Canvas, MCP Server) cuts across every stage"
    cv.text((bx1 + bx2) / 2 - metrics.line_width(label, 16) / 2, top - 12 - 14 - 24, label, size=16, color=MUTED_TXT)
    return top + th_


def draw_legend(cv: Canvas, x: float, y: float, w: float, h: float, where: str) -> None:
    th = THEMES["gray"]
    cv.rect(x, y, w, h, stroke=th.stroke, fill="transparent", style="solid", sw=2, dash="dotted")
    cv.text(x + 20, y + 12, "How to read the atlas", size=26, color=th.deep)
    colw = (w - 40 - 40) / 2
    ry = y + 62
    for st, text in [("ga", "Generally available (Learn page, GA overview or release blog)"),
                     ("gap", "GA core, but some sub-features are still in preview"),
                     ("pre", "Public, private or limited preview - not recommended for production"),
                     ("unk", "No status label on the page, or sources disagree - verify before relying on it"),
                     ("ret", "Retirement or deprecation date announced"),
                     ("dead", "Already retired"),
                     ("doc", "Guidance page rather than a product feature")]:
        draw_pill(cv, x + 20, ry, st)
        cv.text(x + 20 + PILL_W + 12, ry + 2, "\n".join(metrics.wrap_text(text, colw - PILL_W - 12, 15)), size=15)
        ry += 31
    rx = x + 20 + colw + 40
    off = 132
    ry = y + 62
    cv.text(rx, ry, "+ Name", size=16, color=THEMES["gray"].deep)
    cv.text(rx + off, ry + 1, "Not listed in the official capability reference (as of 2026-11-03)", size=15)
    ry += 31
    cv.text(rx, ry + 3, "D3", size=13, color=RED_TAG)
    cv.text(rx + off, ry + 1, f"Status contested: see the drift list ({where})", size=15)
    ry += 31
    cv.text(rx, ry + 3, "Deploy \u2022 Manage", size=13, color=LINK)
    cv.text(rx + off, ry + 1, "Blue sub-page links open the related Learn pages", size=15)
    ry += 31
    cw_ = metrics.line_width("Tool search", 13) + 16
    cv.rect(rx, ry, cw_, 22, stroke=th.stroke, fill="#ffffff", style="solid", sw=1.5, rough=0)
    cv.text(rx + 8, ry + 3, "Tool search", size=13, color=th.deep)
    cv.text(rx + off, ry + 1, "Boxed chips are capabilities in their own right (group rows)", size=15)
    ry += 31
    cv.text(rx, ry + 1, "Click", size=16, color=LINK)
    cv.text(rx + off, ry + 1, "any capability name or link to open its Microsoft Learn page", size=15)
    ry += 40
    legend(cv, x + 20, y + h - 40, [("Models", "blue"), ("Agents", "green"), ("Tools", "orange"),
                                    ("Knowledge, Foundry Tools", "teal"), ("Observability and evaluation", "violet"),
                                    ("Safety", "pink"), ("Governance", "grape"), ("Surfaces and APIs", "gray")],
           size=15, gap=22)
    cv.register("legend", x, y, w, h)


def header_band(cv: Canvas, y: float, part: int) -> float:
    """Legend panel (left) + three notes (right). Returns the bottom y."""
    lw = 1560
    nw = W - lw - 40
    n1 = Note(nw, "Each status is the most recent signal among the row's own Learn page, the GA overview (dated 2026-09-23), the capability reference (updated 2026-10-08) and Foundry DevBlog round-ups. The Learn What's-new article only covers August 2026, so some September-October 2026 items rest on blog posts. Labels drift weekly: open the page before you rely on a status.",
              kind="key", title="Verified 2026-11-03",
              src=[("Feature status at GA", learn("concepts/general-availability")),
                   ("Capability reference", learn("concepts/capability-reference")),
                   ("What's new in Foundry", learn("whats-new-foundry"))])
    n2 = Note(nw, "The row shows the cautious label plus a red D tag that points into the status-drift list; the atlas never silently picks a side. Where the capability reference describes an item differently from its own page (Routines, SharePoint and Fabric connectors, Foundry Agent Canvas) the row follows the page.",
              kind="tip", title="When sources disagree")
    n3 = Note(nw, "Counts are individually listed capabilities. Blue sub-page links are not counted separately; chip-only rows such as the Responses API built-ins count every chip. A capability that lives in two areas (the Azure AI Search tool) is listed in both.",
              kind="info", title="How counts work")
    gap = 14
    total = n1.h + n2.h + n3.h + 2 * gap
    where = "below the atlas" if part == 1 else "D13-D14 here, D1-D12 in part 1"
    draw_legend(cv, 0, y, lw, max(total, 340), where)
    cy = y
    for n in (n1, n2, n3):
        n.place(cv, lw + 40, cy)
        cy += n.h + gap
    return y + max(total, 340)


def page_sources(cv: Canvas, y: float, items: list) -> float:
    r_ = sources(cv, 0, y, items, w=W, cols=3)
    return r_.bottom


def cx_(c: int) -> float:
    return c * (COL + GUT)


def link_for(name: str) -> str:
    """URL of the row (or chip) called `name`, so summary chips stay live Learn links."""
    for a in AREAS:
        for cl in a.clusters:
            for it in cl.items:
                if it.name == name and it.url:
                    return it.url
    for a in AREAS:
        for cl in a.clusters:
            for it in cl.items:
                for c in it.chips:
                    if c[0] == name:
                        return _u(c[1])
    raise KeyError(name)


def chips_height(items: list, w: float, *, size=14, gap=8, row_gap=8) -> float:
    cx, cy = 0.0, 0.0
    ch = size * LH + 8
    for it in items:
        cw = metrics.line_width(it[0], size) + 18
        if cx and cx + cw > w:
            cx, cy = 0.0, cy + ch + row_gap
        cx += cw + gap
    return cy + ch


def draw_chips(cv: Canvas, x: float, y: float, w: float, items: list, theme: str, *, size=14, gap=8, row_gap=8) -> float:
    """Boxed link chips wrapped into width w; items = (label, url[, status]). Returns the bottom y."""
    cx, cy = 0.0, 0.0
    ch = size * LH + 8
    for it in items:
        label, url = it[0], it[1]
        cst = it[2] if len(it) > 2 else None
        cw = metrics.line_width(label, size) + 18
        if cx and cx + cw > w:
            cx, cy = 0.0, cy + ch + row_gap
        ct = THEMES[STATUS_STYLE[cst][1]] if cst else THEMES[theme]
        cv.rect(x + cx, y + cy, cw, ch, stroke=ct.stroke, fill="#ffffff" if not cst else ct.soft, style="solid", sw=1.5,
                rough=0)
        cv.text(x + cx + 9, y + cy + 4, label, size=size, color=ct.deep, link=url)
        cx += cw + gap
    return y + cy + ch


SOURCES_1 = [
    ("Microsoft Foundry capability reference", learn("concepts/capability-reference")),
    ("Product and capability map", learn("concepts/capabilities")),
    ("Feature status at GA (matrix, dated 2026-09-23)", learn("concepts/general-availability")),
    ("What is Microsoft Foundry?", learn("what-is-foundry")),
    ("What's new in Foundry (August 2026 article)", learn("whats-new-foundry")),
    ("Foundry Models overview", learn("concepts/foundry-models-overview")),
    ("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
    ("Foundry Agent Service overview", learn("agents/overview")),
    ("Hosted agents", learn("agents/concepts/hosted-agents")),
    ("Toolbox overview", learn("agents/concepts/toolbox-overview")),
    ("Foundry IQ", learn("agents/concepts/what-is-foundry-iq")),
    ("Observability in Foundry", learn("concepts/observability")),
    ("Region support", learn("reference/region-support")),
    ("DevBlog: What's new in Microsoft Foundry, September 2026 (blog)",
     "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-september-2026/"),
]


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry capability atlas",
                                "Part 1 of 2: build and run (areas 1-6) - every capability with its status, purpose and a Learn link - verified 2026-11-03",
                                w=W)
    y = header_band(cv, bottom + 36, 1) + 56
    y = draw_strip(cv, 0, y, {1, 2, 3, 4, 5, 6}, "see part 2") + 56

    models = AreaBlock(balanced(A2, 2), span_w(2))
    a1, a3, a4, a5, a6 = (AreaBlock(a, COL) for a in (A1, A3, A4, A5, A6))
    drift = DriftBox(span_w(3), "Status drift: where Learn disagrees with itself",
                     "As of 2026-11-03. The pill is the verdict shown on the row; open the linked page to confirm. Tags D1-D12 match the red tags on the rows.",
                     DRIFT_1, cols=3)
    a6_y = y + a1.h + GUT
    col2_bottom = max(a6_y + a6.h, y + models.h)
    models.place(cv, cx_(0), y, h=col2_bottom - y)
    a1.place(cv, cx_(2), y)
    a6.place(cv, cx_(2), a6_y, h=col2_bottom - a6_y)
    a4.place(cv, cx_(4), y)
    a5_y = a4.bottom + GUT
    dy = col2_bottom + GUT
    end = max(a5_y + a5.h, dy + drift.h)
    a5.place(cv, cx_(4), a5_y, h=end - a5_y)
    drift.place(cv, 0, dy, h=end - dy)
    a3.place(cv, cx_(3), y, h=end - y)
    page_sources(cv, end + 60, SOURCES_1)
