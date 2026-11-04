"""YouTube videos, sessions and blogs - the curated 'under the hood' shelf (29 entries, verified 2026-11-03).

Every card's title is a link to the source (the card shape and the title both carry `link=`), and the card shows speaker, event/date,
a short summary written from the research brief, which of our under-the-hood canvases it informs and a reliability rating.
Cards that only repeat a video or blog claim are never presented as documentation; gaps are drawn as dotted grey '?' cards.
"""
from __future__ import annotations

import math

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="youtube-and-session-catalog",
    title="Videos, sessions and blogs: the under-the-hood shelf",
    section="8", order=10,
    description="A curated, link-checked shelf of 29 sources - 19 YouTube videos and sessions plus blogs, repos and Learn anchors - grouped by topic, "
                "with speaker, date, a short summary, the canvases each one informs and how far to trust it (as of 2026-11-03).",
    tags=["youtube", "videos", "sessions", "blogs", "catalog", "reading list"],
)

W = 3250
GREY = "#868e96"
AMBER = "#f08c00"
INK_GRAY = "#495057"
RED_TXT = "#c92a2a"

# ------------------------------------------------------------------------------------------------ our nine canvases
# the order is the brief's canvas numbering; labels are short forms of the canvas titles in the gallery
CANVAS = {
    1: "Agent Service architecture", 2: "Hosted agent runtime", 3: "One Responses call", 4: "Model serving",
    5: "Agentic retrieval", 6: "Networking internals", 7: "Safety pipeline", 8: "Telemetry pipeline", 9: "Memory internals",
}

# topic -> (theme, label)
TOPIC = {
    "agent": ("lime", "Agent Service"), "hosted": ("green", "Hosted agents / microVM"), "cp": ("grape", "Control plane"),
    "sec": ("red", "Security"), "ops": ("violet", "Ops"), "iq": ("teal", "IQ and retrieval"), "models": ("blue", "Models / PTU"),
    "learn": ("gray", "Learn"),
}

Y = "https://www.youtube.com/watch?v="


def E(n, kind, topic, title, who, url, summary, informs, stars, trust, *, flag=False, srcs=None, ctx=False):
    """One catalog entry. informs = canvas numbers (or 'all'); srcs = extra (label, url) pairs for multi-URL entries;
    ctx = the entry is context only for the canvases it lists (the brief's '(context only)')."""
    return dict(n=n, kind=kind, topic=topic, title=title, who=who, url=url, summary=summary, informs=informs, stars=stars,
                trust=trust, flag=flag, srcs=srcs or [], ctx=ctx)


ENTRIES = {
    1: E(1, "video", "hosted", "Foundry Agent Service + Microsoft Agent Framework Explained",
         "Jeff Hollan (Microsoft Mechanics) | 2026-04-22 | 14:29", Y + "iR7_57lJOz8",
         "Launch-week explainer of the new hosted agents: each user session gets its own microVM sandbox (0:03:12, 0:03:59-0:04:20), actions "
         "trace to the agent identity (0:03:45) and every interaction is checked against guardrail policies (0:04:24-0:04:46). No hypervisor or VMM is named.",
         [2, 7, 3], 3, "current; marketing-level 'what', not 'how'; Learn confirms the VM-isolated sandbox"),
    2: E(2, "video", "hosted", "From prototype to production: build and run agents at scale (BRK241)",
         "Tina Schuchman, Jeff Hollan | Build 2026, uploaded 2026-06-03 | 43:34", Y + "_8UKz197JuM",
         "Live hosted-agent runtime demo: per-conversation and routine sessions, scale-to-zero with state resume (0:20:22-0:26:02), a human-approval "
         "wait held by Durable Task Scheduler while sessions idle, and the procedural-memory preview announcement (0:39:39).",
         [2, 3, 9], 3, "current; speaker claims, no SLO numbers; transcript quality moderate (the cold-start line around 0:19:26-0:19:34 is garbled)",
         srcs=[("Session repo: Build26-BRK241", "https://github.com/microsoft/Build26-BRK241-from-prototype-to-production-build-and-run-agents-at-scale")]),
    3: E(3, "video", "hosted", "Claw and agent harness in Microsoft Foundry (BRK243)",
         "Shawn Henry, Amanda Foster, Glenn Condron | Build 2026, uploaded 2026-06-04 | 45:51", Y + "e_ZJy3RsNkg",
         "The clearest statement of session semantics: the session ID controls the filesystem; a new ID means a new VM recreated from the deploy-time "
         "snapshot (0:15:00-0:15:30); idle shutdown after about 15 minutes with routines waking the same session (0:14:18-0:14:35); files kept about 30 days after inactivity (0:19:27).",
         [2, 3], 3, "current; demo-driven (some network flakiness on stage)",
         srcs=[("Session repo: Build26-BRK243", "https://github.com/microsoft/Build26-BRK243-claw-and-agent-harness-in-microsoft-foundry")]),
    4: E(4, "video", "hosted", "Host your agents on Foundry: Microsoft Agent Framework",
         "Pamela Fox | Microsoft Reactor stream, 2026-04-27 | 61:58", Y + "8N7q0Ucr3rw",
         "Code, Responses adapter, Dockerfile, ACR, then Agent Service 'serves it on this new micro VM platform' (0:35:01-0:35:27); the azd up flow; in Q&A the "
         "presenter calls it the 'fast micro VM platform' and says the earlier version ran on Container Apps (0:40:19-0:40:58); tracing walk-through 0:42:09-0:46:24.",
         [2, 3, 8], 3, "good for the developer flow; the platform-internals remark is informal, unofficial naming and conflicts with Learn's 'on Azure Container Apps' diagram",
         flag=True, srcs=[("Reactor series page (parts 2-3 not reviewed)", "https://developer.microsoft.com/en-us/reactor/series/S-1655/")]),
    5: E(5, "video", "agent", "Turn your agents into action: Connect tools, APIs, and documents (BRK242)",
         "Ronak Chokshi, Maria Naggaga, Joe Filcik | Build 2026, uploaded 2026-06-04 | 43:17", Y + "nZM5PkjzSKo",
         "Toolbox as one governed endpoint for many tool types; tool search is a tool inside the toolbox that looks up tool metadata so only the needed tool "
         "enters the context window (0:14:28-0:15:20); governance dashboard (0:11:58); Content Understanding add-ons.",
         [1, 3], 2, "concept-level; Learn toolbox pages are more precise; not reviewed beyond tool search"),
    6: E(6, "video", "agent", "How Foundry integrates with open-source frameworks and tools (DEM333)",
         "Facundo Santiago, Nagkumar Arkalgud | Build 2026, uploaded 2026-06-03 | 16:27", Y + "AmqjXd7v_x4",
         "An OpenClaw-style agent built from open-source parts, then hosted on Foundry behind the Responses API (0:09:32-0:10:10); the portal Traces tab shows "
         "invoke_agent and chat spans (0:12:07); skills mounted at a virtual path (0:05:41); Copilot CLI reaches the agent over A2A.",
         [3, 8], 2, "short demo, useful as a trace and endpoint illustration; reviewed for highlights only"),
    7: E(7, "video", "ops", "Any agent, any cloud: Standardized tracing with Foundry + OpenTelemetry (DEM341)",
         "Hanchi Wang, Nagkumar Arkalgud | Build 2026, uploaded 2026-06-04 | 23:58", Y + "WprbDyANqy0",
         "How external or any-cloud agents emit OpenTelemetry into Foundry: a distro, an Application Insights connection and agent ID registration so traces "
         "correlate (0:15:51-0:16:46), then the trace tree in the portal.",
         [8], 3, "aligned with the Learn observability pages (external agents are preview)"),
    8: E(8, "video", "ops", "From observability to ROI for AI agents on any framework (BRK252)",
         "Sebastian Kohlmeier, Filisha Shah, Vivek Bhadauria | Build 2026, uploaded 2026-06-03 | 35:28", Y + "a7FELS8hQAE",
         "Continuous evaluation pulls production traces from Application Insights and scores them (0:07:57-0:08:24); Azure Monitor integration (0:10:31); "
         "rubric evaluators; Microsoft is contributing OpenTelemetry semantic conventions for memory (0:32:05-0:32:21).",
         [8, 9], 2, "good on the evaluation and monitoring layer; little emission-point detail"),
    9: E(9, "video", "iq", "Foundry IQ: Fuel agents with enterprise knowledge and agentic retrieval (BRK246)",
         "Pablo Castro | Build 2026, uploaded 2026-06-04 | 45:01", Y + "FRptM_WiBRg",
         "Owner-level walkthrough: three layers - integration, agentic retrieval, core engine (0:07:07-0:08:11); serverless Foundry IQ that scales to zero "
         "(0:09:07-0:10:49); the plan, search, judge, iterate loop (0:31:44-0:32:20) and where quality gains come from (0:34:00-0:34:46).",
         [5], 3, "best retrieval source; serverless and latency statements are speaker claims, not in Learn"),
    10: E(10, "video", "iq", "Foundry IQ: the future of RAG with knowledge retrieval and AI Search (BRK196)",
          "Pablo Castro | Ignite 2025, 2025-11-20 | 43:54", Y + "slDdNIQCJBQ",
          "First public tour of knowledge bases, knowledge sources and agentic retrieval, from the preview era. Linked from the Learn 'What is Foundry IQ?' page.",
          [5], 2, "concepts hold; defaults and limits are superseded by Learn and BRK246", flag=True),
    11: E(11, "video", "iq", "Deep Dive into Foundry IQ",
          "John Savill (John Savill's Technical Training) | 2026-01-19 | 38:05", Y + "uDVkcZwB0EU",
          "Whiteboard and portal demo: reasoning-effort levels (0:18:49), medium-effort self-reflection with a second pass (0:23:51-0:24:27), output modes (0:25:39) "
          "and an activity log showing two iterations and planning tokens (0:33:11-0:34:20). Linked from Learn.",
          [5], 3, "matches Learn; third-party presenter; one of the most-watched here (43.4K views)"),
    12: E(12, "video", "iq", "Foundry IQ for Multi-Source AI Knowledge Bases",
          "Pablo Castro with Jeremy Chapman (Microsoft Mechanics) | 2025-12-01 | 13:47", Y + "bHL1jbWjJUc",
          "Intro-level: multi-source knowledge bases, how it works (0:05:51), a visualisation tool (0:06:52) and evaluating results (0:10:10). Linked from Learn.",
          [5], 2, "quick primer, superseded in detail by #9 and #11; the most-watched here (44.7K views)"),
    13: E(13, "video", "agent", "AI builder's guide to agent development in Foundry Agent Service (BRK201)",
          "Salman Quazi, Dan Taylor, Travis Wilson | Ignite 2025, 2025-11-20 | 47:26", Y + "7faSLQS501E",
          "Responses as a stateful API that persists history and agent definitions (0:36:27-0:37:24); versions are first-class; BYO Cosmos and Search with "
          "'transitive VNet injection' (0:37:06); built to move from multitenant to single-tenant 'with no code changes' (0:03:39-0:03:56); traces include service and LangGraph spans (0:32:49-0:33:18).",
          [1, 6, 3], 2, "architecture hints still valid; the hosted-agent parts are the container-era v1, superseded by the 2026 runtime", flag=True),
    14: E(14, "video", "agent", "AI agents in Microsoft Foundry: ship fast, scale fearlessly (BRK189)",
          "Yina Arenas, David Feldman, Mark Oost, Tina Schuchman, Elijah Straight | Ignite 2025, 2025-11-20 | 43:27", Y + "hBpbKMEOVEw",
          "Platform overview; hosted agents v1 pitched as 'valet parking' (0:16:23), a Citrix case (0:16:34) and Entra Agent ID (0:27:10).",
          [1, 2], 1, "marketing and overview, no internals; the hosted agents shown pre-date the microVM runtime; not reviewed in full", flag=True, ctx=True),
    15: E(15, "video", "cp", "AI Operations to own the fleet, master the mission in Microsoft Foundry (BRK205)",
          "Ken Archer, Sarah Bird, Florent Ricci | Ignite 2025, 2025-11-21 | 45:28", Y + "oOO6OG4biEY",
          "Control Plane tour - fleet inventory, policy and observability - and the guardrail creation UI (0:13:47).",
          [7, 8], 2, "UI-level; useful for the control-plane framing; not reviewed in full"),
    16: E(16, "video", "agent", "Using Microsoft Agent Framework with Foundry managed memory",
          "Lewis Liu (Microsoft, Foundry memory) with Amy Boyd and Jorge Arteiro (Open at Microsoft) | 2026-04-16 | 32:32", Y + "DZn9bNDEs4U",
          "Memory as a tool the agent calls to extract, consolidate and fetch at inference (0:02:55-0:03:18); scope as a data container (0:07:31-0:09:21); a "
          "dairy-allergy conflict resolved by consolidation (0:11:13-0:11:41); TTL for decaying facts (0:12:39); the update_delay trade-off (0:17:55-0:18:21); roadmap: UI, procedural memory, lineage (0:14:48-0:16:14).",
          [9], 3, "the only video on memory; concepts only, no storage internals"),
    17: E(17, "video", "models", "Model Mondays - Spotlight on Model router in Microsoft Foundry",
          "Microsoft Reactor stream | 2026-08-24 | 71:47", Y + "od_WTpE2nH4",
          "The router is a small, specially-trained model that analyses prompt, context and tools (0:03:14-0:03:37, 0:08:41-0:09:35); failover and the at-least-two-model "
          "subset rule (0:20:41-0:21:53); Azure Policy honoured in routing (0:24:14-0:25:06). The '~50 ms' overhead is a speaker figure.",
          [4], 3, "aligned with the Learn model-router pages; long (71 minutes)"),
    18: E(18, "video", "models", "One model deployment to route them all",
          "Microsoft Developer | 2026-09-25 | 4:26", Y + "cify-SUpqz4",
          "A 4-minute portal demo: deploy model-router, pick a mode (quality, cost or balanced) and a subset (the demo used the default 27 models), swap the agent's "
          "deployment name and watch which model served each request.",
          [4], 2, "UI demo only (shows Global Standard and Data Zone Standard options)"),
    19: E(19, "video", "models", "Deploy OpenAI Services at Scale Using Provision Throughput Units",
          "Azure Essentials show | 2024-11-05 | 11:46", Y + "XLXHEPqnwUM",
          "PTU basics from the Azure OpenAI era.",
          [4], 1, "dated: pre-Foundry rename, no spillover, priority or Global and Data Zone PTU detail; cite Learn instead", flag=True),
    20: E(20, "blog", "hosted", "Introducing the new hosted agents in Foundry Agent Service",
          "Takuto Higuchi, Jeff Hollan, Lakshmi Ramakrishnan | Foundry Blog, 2026-04-22",
          "https://devblogs.microsoft.com/foundry/introducing-the-new-hosted-agents-in-foundry-agent-service-secure-scalable-compute-built-for-agents/",
          "The launch post: a per-session sandbox with a persistent filesystem, 'not process isolation ... production-proven hypervisor isolation', predictable "
          "cold starts, scale-to-zero and an identity per agent.",
          [2, 3], 3, "the only official source for the 'hypervisor isolation' wording; no VMM named"),
    21: E(21, "blog", "hosted", "What's New in Hosted Agents in Foundry Agent Service",
          "Tina Manghnani, Pranav Pandit | Foundry Blog, 2026-06-02", "https://devblogs.microsoft.com/foundry/hosted-agents-build26/",
          "Source-code deploy (no container), modalities, 20 regions at the time and the road-to-GA list (private ACR, managed VNet, long-running agents).",
          [2, 6], 2, "superseded where Learn now differs (31 regions listed, managed VNet supports hosted agents)", flag=True),
    22: E(22, "blog", "agent", "Build and run agents at scale with Microsoft Foundry at Build 2026",
          "Tina Schuchman | Foundry Blog, 2026-06-02", "https://devblogs.microsoft.com/foundry/agent-service-build2026/",
          "Build, Deploy, Operate framing; Toolboxes (preview then), a Foundry IQ GA claim with a serverless tier in preview, tracing and the optimizer loop.",
          [1, 5, 8], 2, "product-marketing level; status claims since overtaken (Toolboxes GA per #23)", flag=True),
    23: E(23, "blog", "hosted", "What's new in Microsoft Foundry: July and August 2026 + GPT-5.6 now available in Microsoft Foundry",
          "Nick Brady | Foundry Blog, 2026-09-09 + Azure blog, 2026-07-09",
          "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-july-august-2026/",
          "Two sources for the GA of hosted agents: the 2026-07-09 announcement and the roundup, which says Hosted Agents, Voice Live integration and Toolboxes "
          "are GA, plus Model Router region and pool updates.",
          [2, 4], 3, "newest status evidence; the Learn pages read carry no GA banner",
          srcs=[("Azure blog: GPT-5.6 now available in Microsoft Foundry", "https://azure.microsoft.com/en-us/blog/gpt-5-6-now-available-in-microsoft-foundry/")]),
    24: E(24, "blog", "sec", "Foundry hosted agent isolation with Microsoft Agent Framework",
          "Agent Framework blog | 2026-09-22",
          "https://devblogs.microsoft.com/agent-framework/foundry-hosted-agent-isolation-with-microsoft-agent-framework/",
          "Separates user isolation (whose data) from hosted-session isolation (which VM-isolated sandbox, keyed by agent_session_id): 'a session is not a "
          "conversation'. A pooled-session design keeps response chains private per user while the filesystem is shared.",
          [2, 3], 3, "current and precise; notes the SDK and hosting packages are still pre-release"),
    25: E(25, "blog", "agent", "Memory posts: Introducing Memory in Foundry Agent Service + Making agent memory more reliable, transparent, and production-ready",
          "Foundry Blog | 2025-11-25 and 2026-06-03", "https://devblogs.microsoft.com/foundry/introducing-memory-in-foundry-agent-service/",
          "The three phases (extract, consolidate with LLMs, hybrid-search retrieve) and the June update: procedural memory (trajectory audit into 'when to use' and "
          "'what to do' items), TTL, multimodal, direct commands, portal UI and file-based memory in Agent Framework.",
          [9], 3, "product-team blogs; the vendor benchmark claim (about +5% on STATE-Bench and Tau-Bench) is unverified",
          srcs=[("Foundry Blog 2026-06-03: Making agent memory more reliable", "https://devblogs.microsoft.com/foundry/memory-build2026/")]),
    26: E(26, "repo", "hosted", "Production Hosted Agents on Foundry (architecture.md)",
          "microsoft/agenticai-design-patterns | GitHub repo",
          "https://github.com/microsoft/agenticai-design-patterns/blob/main/assets/agent-runtime/production-hosted-agents-on-foundry/docs/architecture.md",
          "A pattern repo with 'observed in preview' behaviours, for example a session reporting ACTIVE before the server is ready (HTTP 424) and unpinned "
          "requests creating new sessions.",
          [2], 2, "useful field notes, not vendor-verified; preview-era"),
    27: E(27, "repo", "hosted", "Build 2026 session repos (BRK241, BRK243)",
          "Microsoft GitHub | runnable session samples",
          "https://github.com/microsoft/Build26-BRK241-from-prototype-to-production-build-and-run-agents-at-scale",
          "Runnable samples: two hosted agents (field-ops-agent, fibey-coordinator) with the exact RBAC the platform assigns (Container Registry Repository "
          "Reader to the project managed identity, Foundry User to each agent identity) and .NET agent-harness steps.",
          [2, 3], 3, "accurate sample code, no architecture prose; only the READMEs were read",
          srcs=[("Build26-BRK243 repo", "https://github.com/microsoft/Build26-BRK243-claw-and-agent-harness-in-microsoft-foundry")]),
    28: E(28, "learn", "learn", "Learn anchors (authoritative; read first)",
          "Microsoft Learn | pages under learn.microsoft.com/en-us/azure/foundry/", "https://learn.microsoft.com/en-us/azure/foundry/",
          "The only sources that name the platform components (Foundry endpoint, Micro VM host layer, Tools Service, Data Proxy), the identity and token mechanics, "
          "PTU leaky-bucket rules, router behaviour, memory quotas and the span vocabulary.",
          "all", 3, "primary; a few internal conflicts are flagged on the canvases"),
    29: E(29, "learn", "hosted", "Dynamic sessions in Azure Container Apps (adjacent technology)",
          "Microsoft Learn | Azure Container Apps | updated 2026-04-14", "https://learn.microsoft.com/en-us/azure/container-apps/sessions",
          "Describes Hyper-V-isolated sandboxes with pre-warmed pools and sub-second start - the closest public description of the kind of isolation the hosted-agent "
          "blog alludes to. Not stated to be the same platform.",
          [2, 6], 3, "authoritative for Azure Container Apps; for Foundry it is only an analogy (our inference)", flag=True, ctx=True),
}

KIND_LABEL = {"video": "Video", "blog": "Blog", "repo": "Repo", "learn": "Learn"}
SRC_PREFIX = {"video": "Video", "blog": "Blog", "repo": "Repo", "learn": "Learn"}
STAR = {3: ("#2f9e44", "#b2f2bb"), 2: ("#f08c00", "#ffec99"), 1: ("#e03131", "#ffc9c9")}

# --------------------------------------------------------------------------- Learn anchors (card #28 + sources panel)
LEARN_ANCHORS = [
    ("Networking deep dive", learn("agents/concepts/agents-networking-deep-dive")),
    ("Hosted agents", learn("agents/concepts/hosted-agents")),
    ("Hosted agent contract", learn("agents/concepts/hosted-agent-contract")),
    ("Hosted agent token service", learn("agents/concepts/hosted-agent-token-service")),
    ("Hosted agent guardrails", learn("agents/concepts/hosted-agent-guardrails")),
    ("Model router: how it works", learn("openai/concepts/model-router-how-it-works")),
    ("Provisioned throughput", learn("openai/concepts/provisioned-throughput")),
    ("Memory (what is memory)", learn("agents/concepts/what-is-memory")),
    ("Agentic retrieval (Azure AI Search)", learn("azure/search/agentic-retrieval-overview", base="")),
    ("Agent tracing overview", learn("observability/concepts/trace-agent-concept")),
]
U_ACA = "https://learn.microsoft.com/en-us/azure/container-apps/sessions"
U_PATTERNS = ENTRIES[26]["url"]


# =========================================================================== small helpers
def link_label(url: str) -> str:
    """Readable short form of a URL; keeps the video id for YouTube links (short_url drops the query string)."""
    if "youtube.com/watch?v=" in url:
        return "youtube.com/watch?v=" + url.split("v=", 1)[1]
    return short_url(url)


def banner(cv: Canvas, y: float, letter, title: str, sub: str, theme: str = "gray") -> float:
    """Section banner with a lettered marker; returns the y where content can start."""
    numbered(cv, 24, y + 30, letter, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 62, y, title, sub, size=34, sub_size=17, w=W - 62)
    return bottom + 26


def star_poly(cv: Canvas, cx: float, cy: float, r: float, filled: bool, level: int) -> None:
    stroke, fill = STAR[level] if filled else ("#adb5bd", "transparent")
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pts.append(pts[0])
    cv.poly(pts, kind="line", stroke=stroke, sw=1.5, fill=fill, fill_style="solid", rough=0)


def stars(cv: Canvas, x: float, cy: float, level: int, r=9, gap=22) -> None:
    for i in range(3):
        star_poly(cv, x + r + i * gap, cy, r, i < level, level)


def evidence_note_chip(label: str, theme: str) -> Chip:
    return Chip(label, theme=theme, size=13, pad_x=8, pad_y=3)


# =========================================================================== the shelf card
class ShelfCard(Rect2):
    """One catalog entry: number, linked title, byline, summary, 'informs' chips, star rating + trust note, source link lines.

    Evidence styling follows the other under-the-hood canvases: a Learn page is solid + hatch; a video, blog or repo (a claim, not a
    specification) is dashed + soft. The topic colour rides on the border, the number badge and the title.
    """

    PAD = 16
    NUM_D = 34

    def __init__(self, w: float, e: dict, theme: str):
        self.w, self.e, self.theme = w, e, theme
        self.th = THEMES[theme]
        self.is_learn = e["kind"] == "learn"
        pad = self.PAD
        inner = (w - 2 * pad) * 0.965
        lh = metrics.line_ratio()
        self.kind_chip = Chip(KIND_LABEL[e["kind"]], theme=theme, size=13, pad_x=9, pad_y=3, fill="solid")
        tw = (w - 2 * pad - self.NUM_D - 12 - self.kind_chip.w - 10) * 0.965
        self.title_lines = metrics.wrap_text(e["title"], tw, 20)
        self.by_lines = metrics.wrap_text(e["who"], inner, 14)
        self.sum_lines = metrics.wrap_text(e["summary"], inner, 15)
        y = pad
        y += max(len(self.title_lines) * 20 * lh, self.NUM_D) + 4
        self.by_y = y
        y += len(self.by_lines) * 14 * lh + 8
        self.sum_y = y
        y += len(self.sum_lines) * 15 * lh + 10
        ctx = e.get("ctx", False)
        names = ["All nine canvases"] if e["informs"] == "all" else [CANVAS[i] + (" (context)" if ctx else "") for i in e["informs"]]
        self.label_w = metrics.line_width("Informs", 13) + 12
        self.chips = ChipFlow([Chip(n, theme="gray", size=13, pad_x=8, pad_y=3, fill="none" if ctx else "soft", dash="dotted" if ctx else "solid")
                               for n in names], inner - self.label_w, gap=6)
        self.inf_y = y
        y += max(self.chips.h, 22) + 10
        self.star_w = 3 * 22 + 10
        self.trust_lines = metrics.wrap_text(e["trust"], inner - self.star_w, 14)
        self.tr_y = y
        y += max(len(self.trust_lines) * 14 * lh, 20) + 8
        self.src_lines = []
        for label, url in [(e["url"], e["url"])] + list(e["srcs"]):
            shown = link_label(url) if label == url else label
            lines = metrics.wrap_text(f"{SRC_PREFIX[e['kind']] if label == url else 'Also'}: {shown}", inner, 12)
            self.src_lines.append(("\n".join(lines), url, y))
            y += len(lines) * 12 * lh + 2
        self.content_h = y + pad - 2
        self.h = self.content_h
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "ShelfCard":
        self.x, self.y = x, y
        H = max(self.content_h, h or 0)
        self.h = H
        e, th, pad = self.e, self.th, self.PAD
        with cv.group():
            if self.is_learn:
                self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2, link=e["url"])
            else:
                self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed", link=e["url"])
            numbered(cv, x + pad + self.NUM_D / 2, y + pad + self.NUM_D / 2 + 1, e["n"], theme=self.theme, d=self.NUM_D, size=17)
            cv.text(x + pad + self.NUM_D + 12, y + pad, "\n".join(self.title_lines), size=20, color=th.deep, link=e["url"])
            self.kind_chip.place(cv, x + self.w - pad - self.kind_chip.w, y + pad)
            cv.text(x + pad, y + self.by_y, "\n".join(self.by_lines), size=14, color=MUTED)
            cv.text(x + pad, y + self.sum_y, "\n".join(self.sum_lines), size=15, color=INK)
            cv.text(x + pad, y + self.inf_y + 4, "Informs", size=13, color=MUTED)
            self.chips.place(cv, x + pad + self.label_w, y + self.inf_y)
            stars(cv, x + pad, y + self.tr_y + 10, e["stars"])
            cv.text(x + pad + self.star_w, y + self.tr_y, "\n".join(self.trust_lines), size=14, color=RED_TXT if e["flag"] else INK)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"shelf:{e['n']}", x, y, self.w, H, container=True)
        return self

    @property
    def bind_target(self):
        return self.rect_el


def nd_card(w: float, title: str, items: list, *, h=None) -> Card:
    """Dotted grey 'searched, not found' card."""
    body = [("para", i) for i in items]
    return Card(w, "? " + title, body, theme="gray", dash="dotted", fill="none", body_color=MUTED, title_color=GREY, title_size=19,
                body_size=15, para_gap=9, gap=9, min_h=h or 0)


def evidence_key(cv: Canvas, right: float, y: float) -> None:
    """Legend for the three evidence styles used on this shelf (right aligned)."""
    specs = [("solid", INK_GRAY, "Learn page: documentation", ""),
             ("dashed", INK_GRAY, "Video, blog or repo (video/blog): a claim", ""),
             ("dotted", GREY, "Searched, not found", "?")]
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


def band_header(cv: Canvas, y: float, icon: str, title: str, sub: str, theme: str) -> float:
    place_icon(cv, icon, 0, y, 54)
    t = cv.text(72, y - 4, title, size=34, color=INK)
    s = cv.text(74, t.bottom, sub, size=17, color=MUTED)
    cv.line((0, s.bottom + 8), (W, s.bottom + 8), stroke=THEMES[theme].stroke, sw=3)
    return s.bottom + 8 + 26


# =========================================================================== A: how to use this shelf
def band_howto(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "A", "How to use this shelf", "Trust the ladder from the top down; treat every video as a claim until Learn confirms it")
    # ---------------------------------------------------------------- evidence ladder
    cv.text(0, y0, "Evidence ladder: how far to trust a source", size=24, color=INK)
    cv.text(0, y0 + 32, "A rule of thumb from the research brief, not an official ranking", size=15, color=MUTED)
    rungs = [
        ("Microsoft Learn", "authoritative: read first (#28)", "green"),
        ("Learn-linked session", "videos that Learn itself links to (#10, #11, #12)", "teal"),
        ("Product-team blog", "launch, what's-new and memory posts (#20-#25)", "blue"),
        ("Product-team video", "Build, Ignite and Mechanics sessions", "indigo"),
        ("Third-party video", "independent presenters (#11 is also Learn-linked)", "violet"),
        ("'Observed in preview' GitHub notes", "field notes, not vendor-verified (#26)", "gray"),
    ]
    ry = y0 + 70
    boxes = []
    step = 96
    for i, (lab, sub, th) in enumerate(rungs):
        b = Box(760, lab, sub=sub, theme=th, size=19, sub_size=14, h=64, fill="hatch")
        b.place(cv, i * 70, ry + i * step)
        numbered(cv, b.x + 18, b.y + 4, i + 1, theme=th, d=32, size=18)
        boxes.append(b)
    for a, b in zip(boxes, boxes[1:]):
        arrow(cv, [(a.x + 130, a.bottom + 5), (a.x + 130, b.y - 5)], sw=2, end_head="arrow", color=GREY)
    cv.text(boxes[0].right + 18, boxes[0].y + 18, "most trusted", size=15, color="#2b8a3e")
    cv.text(boxes[-1].right + 18, boxes[-1].y + 18, "least trusted", size=15, color=GREY)
    ladder_bottom = boxes[-1].bottom
    # ---------------------------------------------------------------- four rules
    nx = 1180
    nw = 1160
    cv.text(nx, y0, "Four rules for using a video as evidence", size=24, color=INK)
    notes = [
        Note(nw, "Anything that only a video or blog says is drawn dashed amber with a (video/blog) tag on the under-the-hood canvases. Use it to orient yourself, "
                 "then confirm it on Learn.", kind="warn", title="Videos are claims, not specifications"),
        Note(nw, "Names and terms get garbled (for example BRK241 around 0:19:26-0:19:34). Timestamps are h:mm:ss from those transcripts: verify any quote against the video "
                 "before you reuse it.", kind="warn", title="Transcripts are machine-generated"),
        Note(nw, "Ignite 2025 hosted-agent talks (#13, #14) describe the container-era hosted agents. The microVM and hypervisor story starts on 2026-04-22 (#1, #20).",
             kind="warn", title="Mind the dates"),
        Note(nw, "'Hypervisor isolation' (blog #20) and 'Micro VM' (Learn networking page) are official. 'Fast micro VM platform' (#4) and the '~50 ms router overhead' "
                 "(#17) are individual speakers.", kind="info", title="Official wording vs speaker wording"),
    ]
    ny = y0 + 44
    for n in notes:
        n.place(cv, nx, ny)
        ny += n.h + 20
    # ---------------------------------------------------------------- legend
    lx = nx + nw + 60
    lw = W - lx
    cv.text(lx, y0, "How to read a card", size=24, color=INK)
    ly = y0 + 50
    for lvl, txt in ((3, "current and Learn-aligned"), (2, "useful, but UI- or marketing-level, or partly superseded"), (1, "dated or superseded")):
        stars(cv, lx, ly + 11, lvl)
        cv.text(lx + 84, ly, txt, size=16, color=INK)
        ly += 36
    ly += 10
    cx = lx
    for k in ("video", "blog", "repo", "learn"):
        c = Chip(KIND_LABEL[k], theme="gray", size=14, fill="soft")
        c.place(cv, cx, ly)
        cx += c.w + 10
    cv.text(cx + 6, ly + 3, "what kind of source it is", size=15, color=INK)
    ly += 50
    numbered(cv, lx + 17, ly + 15, 13, theme="gray", d=34, size=17)
    cv.text(lx + 48, ly + 6, "entry number, used across the canvases", size=16, color=INK)
    ly += 50
    cv.text(lx, ly, "Title = link to the source (the whole card too)", size=16, color=INK)
    ly += 30
    cv.text(lx, ly, "Red trust text = a conflict or an age warning", size=16, color=RED_TXT)
    ly += 44
    cv.text(lx, ly, "Informs = the under-the-hood canvases that cite it:", size=16, color=INK)
    ly += 28
    cf = ChipFlow([Chip(CANVAS[i], theme="gray", size=13, pad_x=8, pad_y=3, fill="soft") for i in sorted(CANVAS)], lw, gap=6)
    cf.place(cv, lx, ly)
    return max(ladder_bottom, ny, cf.bottom) + 10


# =========================================================================== B: reading paths
def band_paths(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "B", "If you only have about 45 minutes, watch these five in order",
                "Each stop is a timestamp range, not a whole video; the boxes are links")
    picks = [
        ("Mechanics: Agent Service + Agent Framework", "14 min. The microVM-per-session story in plain language (#1)", 1),
        ("Reactor: Host your agents on Foundry", "Chapters 33:31 Architecture to 44:24 Monitoring; the 'fast micro VM platform' remark at 0:40:19-0:40:58. How a container becomes a hosted agent (#4)", 4),
        ("BRK243: Claw and agent harness", "0:13:18-0:20:11. Session = filesystem = VM from snapshot, routines, 30-day retention (#3)", 3),
        ("BRK246: Foundry IQ", "0:07:07-0:11:00 and 0:31:44-0:35:00. The Foundry IQ layers and the iterative retrieval loop (#9)", 9),
        ("Memory video: Agent Framework + managed memory", "0:07:31-0:14:33. Scope, consolidation, TTL and the update-delay trade-off (#16)", 16),
    ]
    bw, gap = 560, 112.5
    bx = []
    for i, (lab, sub, n) in enumerate(picks):
        e = ENTRIES[n]
        th = TOPIC[e["topic"]][0]
        b = Box(bw, lab, sub=sub, theme=th, size=21, sub_size=15, h=214, fill="hatch", link=e["url"])
        b.place(cv, i * (bw + gap), y0)
        numbered(cv, b.x + 20, b.y + 6, i + 1, theme=th, d=36, size=20)
        bx.append(b)
    for a, b in zip(bx, bx[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3)
    y1 = bx[0].bottom + 54
    cv.text(0, y1, "The longer path, one topic per stop", size=24, color=INK)
    stops = [
        ("Learn first", "hosted agents and the networking deep dive (#28)", "gray", None),
        ("#1 Mechanics", "the concept in 14 minutes", "green", 1),
        ("#4 Reactor", "0:33:31-0:44:24: how a container becomes an agent", "green", 4),
        ("#3 BRK243", "0:13:18-0:20:11: session semantics", "green", 3),
        ("#24 blog", "user isolation vs session isolation", "red", 24),
        ("#9 and #11", "BRK246 and Savill: retrieval", "teal", 9),
        ("#16 Memory", "scope, consolidation, TTL", "lime", 16),
        ("#17 Model Mondays", "the router and failover", "blue", 17),
        ("#7 and #8", "DEM341 and BRK252: telemetry and evaluation", "violet", 7),
    ]
    pw = (W - 8 * 36) / 9
    py = y1 + 44
    pbx = []
    for i, (lab, sub, th, n) in enumerate(stops):
        b = Box(pw, lab, sub=sub, theme=th, size=18, sub_size=13, h=116, fill="hatch",
                link=ENTRIES[n]["url"] if n else learn("agents/concepts/hosted-agents"))
        b.place(cv, i * (pw + 36), py)
        numbered(cv, b.x + 16, b.y + 4, i + 1, theme=th, d=30, size=16)
        pbx.append(b)
    for a, b in zip(pbx, pbx[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=2, gap=3)
    return pbx[0].bottom


# =========================================================================== C: timeline
def band_timeline(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "C", "When each source was published - and why the dates matter",
                "Stickers are numbered entries (circle = video or session, square = blog, repo or Learn page), coloured by topic")
    slots = ["Nov 2024", "Nov 2025", "Dec", "Jan 2026", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    sw = W / len(slots)

    def sx(idx: int, frac: float = 0.0) -> float:
        return (idx + frac) * sw

    era_y = y0 + 30
    era_h = 64
    apr22 = sx(6, 21 / 30)
    jul09 = sx(9, 8 / 31)
    cv.rect(sx(1), era_y, apr22 - sx(1), era_h, stroke=GREY, fill="#f1f3f5", style="solid", sw=2, dash="dashed")
    cv.text(sx(1) + 16, era_y + 8, "Container-era hosted agents (v1)", size=20, color=INK_GRAY)
    cv.text(sx(1) + 16, era_y + 34, "as described in the Ignite 2025 talks (#13, #14); a presenter says it ran on Container Apps (#4)", size=15, color=MUTED)
    th = THEMES["green"]
    cv.rect(apr22, era_y, W - apr22, era_h, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(apr22 + 16, era_y + 8, "MicroVM-era hosted agents", size=20, color=th.deep)
    cv.text(apr22 + 16, era_y + 34, "2026-04-22 announcement (#1, #20); GA announced 2026-07-09 (#23); Learn pages carry no GA banner", size=15, color=MUTED)
    era_bottom = era_y + era_h
    lab_y = era_bottom + 18
    br_y = lab_y + 28
    axis_y = br_y + 66
    d = 38
    stickers_bottom = axis_y + 26 + 2 * (d + 8)
    # vertical markers first, so the stickers sit on top of them
    for xx, lab in ((apr22, "2026-04-22: microVM launch"), (jul09, "2026-07-09: GA announced")):
        cv.line((xx, era_bottom), (xx, stickers_bottom), stroke=th.stroke, sw=2, dash="dashed")
        cv.text(xx + 8, stickers_bottom - 18, lab, size=14, color=th.deep)
    # event brackets above the month labels
    for slot, lab in ((1, "Ignite 2025 sessions"), (8, "Build 2026 sessions")):
        x1, x2 = sx(slot) + 8, sx(slot + 1) - 8
        lw_, _ = text_size(lab, 16)
        cv.text((x1 + x2) / 2 - lw_ / 2, lab_y, lab, size=16, color=INK)
        cv.line((x1, br_y), (x2, br_y), stroke=INK, sw=2)
        cv.line((x1, br_y), (x1, br_y + 8), stroke=INK, sw=2)
        cv.line((x2, br_y), (x2, br_y + 8), stroke=INK, sw=2)
    cv.line((0, axis_y), (W, axis_y), stroke=INK, sw=3)
    cv.poly([(W - 14, axis_y - 8), (W, axis_y), (W - 14, axis_y + 8)], kind="line", stroke=INK, sw=3)
    for i, lab in enumerate(slots):
        cx = sx(i) + sw / 2
        cv.line((sx(i), axis_y - 8), (sx(i), axis_y + 8), stroke=INK, sw=2)
        tw_, _ = text_size(lab, 17)
        cv.text(cx - tw_ / 2, axis_y - 34, lab, size=17, color=INK)
    # axis break between the 2024 slot and Nov 2025
    cv.line((sx(1) - 10, axis_y + 10), (sx(1) - 2, axis_y - 10), stroke="#ffffff", sw=8)
    cv.line((sx(1) - 12, axis_y + 12), (sx(1) - 4, axis_y - 12), stroke=INK, sw=2)
    cv.line((sx(1) - 2, axis_y + 12), (sx(1) + 6, axis_y - 12), stroke=INK, sw=2)
    # stickers: (slot, date, entry number)
    items = [
        (0, "2024-11-05", 19),
        (1, "2025-11-20", 10), (1, "2025-11-20", 13), (1, "2025-11-20", 14), (1, "2025-11-21", 15), (1, "2025-11-25", 25),
        (2, "2025-12-01", 12), (3, "2026-01-19", 11),
        (6, "2026-04-14", 29), (6, "2026-04-16", 16), (6, "2026-04-22", 1), (6, "2026-04-22", 20), (6, "2026-04-27", 4),
        (8, "2026-06-02", 21), (8, "2026-06-02", 22), (8, "2026-06-03", 25), (8, "2026-06-03", 2), (8, "2026-06-03", 6), (8, "2026-06-03", 8),
        (8, "2026-06-04", 3), (8, "2026-06-04", 5), (8, "2026-06-04", 7), (8, "2026-06-04", 9),
        (9, "2026-07-09", 23),
        (10, "2026-08-24", 17),
        (11, "2026-09-09", 23), (11, "2026-09-22", 24), (11, "2026-09-25", 18),
    ]
    d = 38
    per_row = int((sw - 10) // (d + 6))
    counts: dict[int, int] = {}
    for slot, date, n in items:
        k = counts.get(slot, 0)
        counts[slot] = k + 1
        r, c = divmod(k, per_row)
        px = sx(slot) + 8 + c * (d + 6)
        py = axis_y + 26 + r * (d + 8)
        e = ENTRIES[n]
        thm = THEMES[TOPIC[e["topic"]][0]]
        if e["kind"] == "video":
            cv.ellipse(px, py, d, d, stroke=thm.stroke, fill=thm.fill, style="solid", sw=2, rough=0, link=e["url"])
        else:
            cv.rect(px, py, d, d, stroke=thm.stroke, fill=thm.fill, style="solid", sw=2, rough=0, link=e["url"])
        lab = str(n)
        lw_, lh_ = text_size(lab, 16)
        cv.text(px + (d - lw_) / 2, py + (d - lh_) / 2 + 1, lab, size=16, color=thm.deep)
    cv.text(sx(0) + 8, axis_y + 26 + d + 14, "dated: pre-Foundry", size=13, color=RED_TXT)
    # undated + topic legend
    ly = axis_y + 26 + 2 * (d + 8) + 30
    cv.text(0, ly, "Undated: #26 and #27 (repos), #28 (Learn anchors). #29 is placed at its Learn update date. Entries #25 and #23 appear twice, once per post or source "
                   "(#25: 2025-11-25 and 2026-06-03; #23: 2026-07-09 and 2026-09-09).", size=16, color=INK_GRAY)
    legend(cv, 0, ly + 34, [(lab, th_) for th_, lab in (TOPIC[k] for k in ("agent", "hosted", "cp", "sec", "ops", "iq", "models"))], size=16)
    return ly + 34 + 30


# =========================================================================== D: the shelf
def shelf_board(cv: Canvas, y: float) -> float:
    """A thin shelf board under a row of cards; returns the y below it."""
    cv.rect(0, y + 4, W, 12, stroke="#868e96", fill="#dee2e6", style="solid", sw=2, rough=1, round_=False)
    return y + 16


def col_labels(cv: Canvas, y: float, cw: float, gap: float, labels: list) -> float:
    """Group labels above card columns: (text, theme, first_col, n_cols). Returns the y where the cards can start."""
    for text, th, c0, n in labels:
        x1 = c0 * (cw + gap)
        x2 = x1 + n * cw + (n - 1) * gap
        t = THEMES[th]
        tw_, _ = text_size(text, 20)
        cv.text(x1, y, text, size=20, color=t.deep)
        cv.line((x1, y + 30), (x2, y + 30), stroke=t.stroke, sw=3)
        cv.line((x1, y + 30), (x1, y + 38), stroke=t.stroke, sw=3)
        cv.line((x2, y + 30), (x2, y + 38), stroke=t.stroke, sw=3)
    return y + 52


def card_row(cv: Canvas, y: float, cards: list, cw: float, gap: float = 50, labels=None, board=True) -> float:
    """Place up to four equal-width cards in one row (heights equalised) on a shelf board; returns the bottom y."""
    if labels:
        y = col_labels(cv, y, cw, gap, labels)
    _, b = row(cv, 0, y, cards, gap=gap)
    for c in cards:
        if isinstance(c, Card) and c.dash == "dotted" and c.h - c.content_h > 110:
            cv.text(c.right - 84, c.bottom - 92, "?", size=72, color="#ced4da", align="center", w=60)
    return shelf_board(cv, b) if board else b


def band_shelf(cv: Canvas, y: float) -> float:
    cw, gap = 775, 50
    y0 = banner(cv, y, "D", "The shelf: 29 entries by topic",
                "Each card links to its source. Solid = a Learn page; dashed = a video, blog or repo (a claim); dotted grey = searched for and not found (as of 2026-11-03)")

    def sc(n: int, theme=None) -> ShelfCard:
        e = ENTRIES[n]
        return ShelfCard(cw, e, theme or TOPIC[e["topic"]][0])

    # ---------------------------------------------------------------- start here
    y = band_header(cv, y0, "learn", "Start here: the Learn pages", "authoritative: the only sources that name the platform components", "gray")
    a28 = ENTRIES[28]
    w2 = 2 * cw + gap
    c28 = ShelfCard(w2, a28, "gray")
    note = Note(w2, "All 19 YouTube IDs were fetched on 2026-11-03 (title, length, upload date, playability OK). Transcripts were pulled with youtube-transcript-api and are "
                    "machine-generated, occasionally garbled. All non-YouTube URLs returned HTTP 200 on 2026-11-03. Timestamps are h:mm:ss from the transcripts.",
                kind="key", title="How this shelf was verified")
    cf = ChipFlow([Chip(lab, theme="gray", size=14, link=url, fill="soft") for lab, url in LEARN_ANCHORS], w2, gap=8)
    anchors_h = 30 + cf.h
    h_left = c28.h
    h_right = note.h + 24 + anchors_h
    H = max(h_left, h_right)
    c28.place(cv, 0, y, h=H)
    note.place(cv, w2 + gap, y)
    ay = note.bottom + 24
    cv.text(w2 + gap, ay, "The ten Learn anchors (each chip is a link):", size=16, color=MUTED)
    cf.place(cv, w2 + gap, ay + 30)
    bottom = shelf_board(cv, y + H)
    # ---------------------------------------------------------------- agent service
    y = band_header(cv, bottom + 60, "agent", "Agent Service", "the platform, toolbox, frameworks and memory", TOPIC["agent"][0])
    nd_as = nd_card(cw, "Not found: Agent Service internals", [
        "A video or blog that opens up the safety classifier pipeline.",
        "A video or blog that opens up the orchestrator ('Agent Runtime') internals.",
        "A video or blog that describes memory storage or index internals.",
    ])
    b = card_row(cv, y, [sc(13), sc(14), sc(5), sc(6)], cw)
    b = card_row(cv, b + 40, [sc(22), sc(16), sc(25), nd_as], cw)
    # ---------------------------------------------------------------- hosted agents
    y = band_header(cv, b + 60, "container-apps", "Hosted agents and microVMs", "the 2026 runtime: sessions, sandboxes, isolation, GA status", TOPIC["hosted"][0])
    nd_vmm = nd_card(cw, "Not found: what runs the sandbox", [
        "A public video or blog that names the hypervisor or VMM under hosted agents.",
        "The closest public description is the Hyper-V-isolated sandboxes of Azure Container Apps dynamic sessions (#29), which is not stated to be the same platform.",
    ])
    nd_net = nd_card(cw, "Not found: the networking deep dive on video", [
        "A video that walks the Learn networking deep dive: Micro VM, Tools Service and Data Proxy.",
        "The Learn page itself is the only source that names those components.",
    ])
    b = card_row(cv, y, [sc(1), sc(2), sc(3), sc(4)], cw)
    b = card_row(cv, b + 40, [sc(20), sc(21), sc(23), sc(26)], cw)
    b = card_row(cv, b + 40, [sc(27), sc(29), nd_vmm, nd_net], cw)
    # ---------------------------------------------------------------- control plane / security / ops
    y = band_header(cv, b + 60, "policy", "Control plane, security and ops", "fleet governance, isolation and the telemetry pipeline", TOPIC["cp"][0])
    b = card_row(cv, y, [sc(15), sc(24), sc(7), sc(8)], cw,
                 labels=[("Control plane", "grape", 0, 1), ("Security", "red", 1, 1), ("Ops: tracing and evaluation", "violet", 2, 2)])
    # ---------------------------------------------------------------- IQ and retrieval
    y = band_header(cv, b + 60, "iq", "Foundry IQ and retrieval", "agentic retrieval from the owner, a primer and a third-party deep dive", TOPIC["iq"][0])
    b = card_row(cv, y, [sc(9), sc(10), sc(11), sc(12)], cw)
    # ---------------------------------------------------------------- models and PTU
    y = band_header(cv, b + 60, "openai", "Models, model router and PTU", "routing and capacity: one good video, one demo, one dated", TOPIC["models"][0])
    nd_ptu = nd_card(cw, "Not found: PTU internals", [
        "A video or blog that explains the PTU leaky-bucket or spillover internals beyond Learn.",
        "The only PTU video found (#19) is dated, so cite Learn instead.",
    ])
    b = card_row(cv, y, [sc(17), sc(18), sc(19), nd_ptu], cw)
    return b


# =========================================================================== E: coverage and caveats
PRIMARY = {
    1: {13, 5, 28}, 2: {1, 3, 4, 20, 24, 28}, 3: {3, 6, 13, 28}, 4: {17, 18, 28}, 5: {9, 11, 12, 28},
    6: {13, 29, 28}, 7: {1, 15, 28}, 8: {7, 8, 6, 28}, 9: {16, 25, 28},
}


def band_coverage(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "E", "Which sources inform which canvas",
                "Rows are the nine under-the-hood canvases, columns are the 29 entries; a big dot is the best source in the research brief, a small dot also informs it")
    lab_w = 330
    cw_ = (W - lab_w - 20) / 29
    hy = y0 + 40
    gy = hy + 62
    rh = 46
    # column headers: entry numbers over a topic-coloured tab, video columns before the blog / repo / Learn columns
    for n in range(1, 30):
        e = ENTRIES[n]
        th = THEMES[TOPIC[e["topic"]][0]]
        cx = lab_w + (n - 1) * cw_
        cv.rect(cx + 3, hy, cw_ - 6, 44, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0)
        s = str(n)
        sw_, sh_ = text_size(s, 17)
        cv.text(cx + (cw_ - sw_) / 2, hy + (44 - sh_) / 2 + 1, s, size=17, color=th.deep)
    cv.text(lab_w + 9 * cw_ - 60, hy - 28, "videos and sessions (#1-#19)", size=15, color=MUTED, align="center", w=120)
    cv.text(lab_w + 24 * cw_ - 80, hy - 28, "blogs, repos and Learn (#20-#29)", size=15, color=MUTED, align="center", w=160)
    cv.line((lab_w + 19 * cw_, hy - 4), (lab_w + 19 * cw_, gy + 9 * rh), stroke=GREY, sw=2, dash="dashed")
    for i, name in CANVAS.items():
        ry = gy + (i - 1) * rh
        if i % 2 == 0:
            cv.rect(0, ry, W, rh, stroke="transparent", fill="#f8f9fa", style="solid", sw=0, rough=0, round_=False)
        numbered(cv, 20, ry + rh / 2, i, theme="gray", d=30, size=16)
        cv.text(46, ry + rh / 2 - 12, name, size=19, color=INK)
        cv.line((0, ry + rh), (W, ry + rh), stroke="#dee2e6", sw=1, rough=0)
    for i in range(1, 10):
        ry = gy + (i - 1) * rh
        for n in range(1, 30):
            e = ENTRIES[n]
            informs = list(CANVAS) if e["informs"] == "all" else e["informs"]
            if i not in informs:
                continue
            th = THEMES[TOPIC[e["topic"]][0]]
            cx = lab_w + (n - 1) * cw_ + cw_ / 2
            cy = ry + rh / 2
            if n in PRIMARY[i]:
                cv.ellipse(cx - 14, cy - 14, 28, 28, stroke=th.stroke, fill=th.stroke, style="solid", sw=2, rough=0, link=e["url"])
            else:
                dash = "dotted" if e.get("ctx") else "solid"
                cv.ellipse(cx - 8, cy - 8, 16, 16, stroke=th.stroke, fill=th.fill if dash == "solid" else "transparent", style="solid", sw=2,
                           rough=0, dash=dash, link=e["url"])
    ky = gy + 9 * rh + 22
    cv.ellipse(0, ky + 2, 24, 24, stroke="#495057", fill="#495057", style="solid", sw=2, rough=0)
    cv.text(34, ky + 3, "best non-Learn source in the brief (and #28, the Learn anchors, for every canvas)", size=16, color=INK)
    k2 = 34 + text_size("best non-Learn source in the brief (and #28, the Learn anchors, for every canvas)", 16)[0] + 50
    cv.ellipse(k2, ky + 6, 16, 16, stroke="#495057", fill="#e9ecef", style="solid", sw=2, rough=0)
    cv.text(k2 + 26, ky + 3, "also informs the canvas", size=16, color=INK)
    k3 = k2 + 26 + text_size("also informs the canvas", 16)[0] + 50
    cv.ellipse(k3, ky + 6, 16, 16, stroke="#495057", fill="transparent", style="solid", sw=2, rough=0, dash="dotted")
    cv.text(k3 + 26, ky + 3, "context only (#14, #29)", size=16, color=INK)
    k4 = k3 + 26 + text_size("context only (#14, #29)", 16)[0] + 50
    cv.text(k4, ky + 3, "Dot colours follow the topic of the entry; dots are links to the source.", size=16, color=MUTED)
    ty = ky + 56
    rows = [
        ["1  Agent Service architecture", "concepts/architecture; agents/concepts/runtime-components", "#13 BRK201, #5 BRK242"],
        ["2  Hosted agent runtime", "agents/concepts/hosted-agents; hosted-agent-contract; hosted-agent-token-service", "#1, #3, #4, #20, #24"],
        ["3  One Responses call", "agents/concepts/runtime-components; the MCP tools page; the hosted-agent contract", "#3, #6, #13"],
        ["4  Model serving", "openai/concepts/provisioned-throughput; the spillover page; openai/concepts/model-router-how-it-works", "#17, #18 (#19 is dated)"],
        ["5  Agentic retrieval", "azure/search/agentic-retrieval-overview; agents/concepts/what-is-foundry-iq", "#9, #11, #12"],
        ["6  Networking internals", "agents/concepts/agents-networking-deep-dive", "#13 (transitive VNet injection), #29 (adjacent)"],
        ["7  Safety pipeline", "guardrails/intervention-points; agents/concepts/hosted-agent-guardrails", "#1 (0:04:24), #15"],
        ["8  Telemetry pipeline", "observability/concepts/trace-agent-concept; trace-ingestion-entra-authentication", "#7, #8, #6"],
        ["9  Memory internals", "agents/concepts/what-is-memory; agents/how-to/memory-usage", "#16, #25"],
    ]
    t = Table([("Canvas", 500), ("Best Learn anchors (paths under learn.microsoft.com/en-us/azure/foundry/, except azure/search)", 1500), ("Best non-Learn sources", 1250)],
              rows, w=W, theme="gray", size=16, head_size=17, first_col_theme="gray", title="The same map as a table: best sources per canvas", title_size=22)
    t.place(cv, 0, ty)
    return t.bottom


def band_caveats(cv: Canvas, y: float) -> float:
    y0 = banner(cv, y, "F", "Read these entries with care: known conflicts, ageing claims and gaps",
                "Where two sources disagree we say so instead of picking a side")
    w3 = (W - 100) / 3
    n1 = Note(w3, "Learn's networking diagram says the Micro VMs and the data proxy run 'on Azure Container Apps'. The Reactor presenter (#4, 2026-04-27) says the earlier "
                  "version ran on Container Apps and the new platform is a different 'fast micro VM platform'. Treat the platform name as unconfirmed: the launch blog (#20) says only "
                  "'hypervisor isolation'.", kind="warn", title="Docs disagree: what do hosted agents run on?")
    n2 = Note(w3, "Toolboxes were preview at Build and GA by September (#22 vs #23); hosted agents were announced GA on 2026-07-09; long-running and resilience features remain "
                  "preview in Learn (August 2026 docs update). GA and preview status for hosted agents, Toolboxes and Foundry IQ comes from blogs, not Learn.",
              kind="gotcha", title="Status claims age fast")
    n3 = Note(w3, "Router '~50 ms' overhead; Foundry IQ 'few seconds to ~10 s'; serverless '10-20 seconds to create'; procedural memory '+~5%' on STATE-Bench and Tau-Bench; "
                  "'sub-200 ms' Web IQ. None of these is in Learn.", kind="warn", title="Numbers that are speaker claims")
    n4 = Note(w3, "BRK189, BRK205, BRK242 (beyond tool search), DEM333 (beyond highlights), the Reactor parts 2-3 and the long tail of Model Mondays were not reviewed in full. "
                  "For the GitHub repos only the READMEs were read; the agenticai-design-patterns notes are 'observed in preview'.", kind="info",
              title="What was not reviewed in full")
    n5 = Note(w3, "The most-watched entries are #12 (44.7K views), #11 (43.4K) and #1 (35.7K). Popularity is not accuracy: #12 is a quick primer that #9 and #11 supersede in detail.",
              kind="tip", title="Views are not evidence")
    n6 = Note(w3, "Region lists, quotas (for example sessions 1,000 and 2,000; memory 100 scopes and 10,000 memories), model lists and API versions change often. Several Learn pages "
                  "carry preview banners and the how-to/configure-capability-settings page redirects: re-check before you quote a number.",
              kind="key", title="Learn pages are a moving target (as of 2026-11-03)")
    _, b1 = row(cv, 0, y0, [n1, n2, n3], gap=50)
    _, b2 = row(cv, 0, b1 + 30, [n4, n5, n6], gap=50)
    # ---------------------------------------------------------------- search phrases
    sy = b2 + 50
    with cv.panel(0, sy, title="Search phrases tried (as of 2026-11-03)",
                  sub="None returned a public video or blog for the five gaps drawn as dotted '?' cards on the shelf: the hypervisor, PTU internals, the networking deep dive, "
                      "safety and orchestrator internals, and memory storage",
                  theme="gray", style="dotted", fill="none", pad=24, title_size=24, sub_size=15, w=W) as sp:
        phrases = ["Foundry Agent Service under the hood", "hosted agents microVM", "Foundry hosted agents architecture", "Foundry control plane deep dive",
                   "Foundry IQ agentic retrieval deep dive", "Azure OpenAI PTU spillover deep dive", "model router how it works",
                   "Foundry memory architecture", "Hyper-V isolated sandbox agents"]
        ChipFlow([Chip(p, theme="gray", size=15, dash="dotted", fill="none") for p in phrases], W - 48, gap=10).place(cv, sp.ix, sp.iy)
    return sp.bottom


# =========================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Videos, sessions and blogs: the under-the-hood shelf",
                                "29 verified entries - 19 YouTube videos and sessions, plus blogs, repos and Learn anchors - with what each covers, which canvases it informs "
                                "and how far to trust it (as of 2026-11-03)", w=W)
    evidence_key(cv, W, 6)
    y = bottom + 50
    y = band_howto(cv, y)
    y = band_paths(cv, y + 70)
    y = band_timeline(cv, y + 70)
    y = band_shelf(cv, y + 70)
    y = band_coverage(cv, y + 70)
    y = band_caveats(cv, y + 70)
    y += 56
    items = list(LEARN_ANCHORS) + [
        ("Dynamic sessions in Azure Container Apps (adjacent technology)", U_ACA),
        ("microsoft/agenticai-design-patterns: Production Hosted Agents on Foundry", U_PATTERNS),
        ("Reactor series: Host your agents on Foundry", "https://developer.microsoft.com/en-us/reactor/series/S-1655/"),
        ("Foundry blog: Introducing the new hosted agents (2026-04-22)", ENTRIES[20]["url"]),
    ]
    sources(cv, 0, y, items, w=W, cols=4, title="Sources and further reading (Learn pages; each card links its own source)")
