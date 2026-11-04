"""From Azure AI Studio to Microsoft Foundry (part 1): naming lineage, evolution timeline, previous-vs-current mapping,
Assistants -> Responses, deprecation clock and what's new (as of 2026-11-03). Part 2 holds the migration playbook."""
from __future__ import annotations

import datetime as dt

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="evolution-classic-to-new", title="From Azure AI Studio to Microsoft Foundry", section="1", group="Overview", order=5,
    description="Why there are two portals, two SDK majors and two agent APIs: the Azure AI Studio -> Azure AI Foundry -> Microsoft Foundry "
                "timeline, previous-vs-current mapping, Assistants -> Responses, the deprecation clock and what's new.",
    tags=["evolution", "classic", "timeline", "responses-api", "deprecations"],
)

W = 3000
AS_OF = dt.date(2026, 11, 3)

# ------------------------------------------------------------------------------------------------ sources
WHAT = learn("what-is-foundry")
NAV = learn("how-to/navigate-from-classic")
MIG = learn("agents/how-to/migrate")
UPG = learn("how-to/upgrade-azure-openai")
UPGA = learn("how-to/upgrade-azure-openai-auto")
HUB = learn("foundry-classic/how-to/migrate-project", base="azure")
CLASSIC = learn("foundry-classic/what-is-foundry", base="azure")
GHM = learn("foundry-models/how-to/quickstart-github-models")
INFER = learn("how-to/model-inference-to-openai-migration")
GA = learn("concepts/general-availability")
WN = learn("whats-new-foundry")
FABRIC = learn("agents/how-to/tools/fabric")
CUSTOM = learn("control-plane/register-custom-agent")
SDK = learn("how-to/develop/sdk-overview")
HOSTED = learn("agents/concepts/hosted-agents")
BROWSER = learn("agents/how-to/tools/browser-automation")
DISABLE = learn("agents/how-to/disable-classic-agents")

B_AZ2024 = "https://azure.microsoft.com/en-us/blog/the-next-wave-of-azure-innovation-azure-ai-foundry-intelligent-data-and-more/"
B_BUILD = "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/build-recap-new-azure-ai-foundry-resource-developer-apis-and-tools/4427241"
B_AGENTGA25 = "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/announcing-general-availability-of-azure-ai-foundry-agent-service/4414352"
B_IGNITE25 = "https://azure.microsoft.com/en-us/blog/azure-at-microsoft-ignite-2025-all-the-intelligent-cloud-news-explained/"
B_DEV_ON25 = "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-oct-nov-2025/"
B_AGENTGA = "https://devblogs.microsoft.com/foundry/foundry-agent-service-ga/"
B_HOSTED = "https://devblogs.microsoft.com/foundry/introducing-the-new-hosted-agents-in-foundry-agent-service-secure-scalable-compute-built-for-agents/"
B_JULAUG = "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-july-august-2026/"
B_SEPT = "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-september-2026/"
B_DEVPACK = "https://devblogs.microsoft.com/foundry/foundry-devpack-announcement/"
B_ROUTINES = "https://devblogs.microsoft.com/foundry/from-chatbots-to-automated-assistants-routines-in-microsoft-foundry-are-now-generally-available/"
B_BROWSER = "https://devblogs.microsoft.com/foundry/browser-automation-tool-ga/"


# ================================================================================================ local helpers
class LCard(Card):
    """Card whose footer links may use any prefix (Blog:, Learn:, GitHub:) - Card.src always says 'Learn:'."""

    def __init__(self, w, title=None, body=(), *, links=(), **kw):
        super().__init__(w, title, body, **kw)
        self.links = list(links)
        self._lk: list[tuple[str, str, float]] = []
        extra = 0.0
        if self.links:
            extra = 8.0
            inner = (self.w - 2 * self.pad) * 0.965
            for prefix, label, url in self.links:
                lines = metrics.wrap_text(f"{prefix}: {label}", inner, self.src_size)
                self._lk.append(("\n".join(lines), url, extra))
                extra += len(lines) * self.src_size * metrics.line_ratio() + 2
            extra -= 2
        self._extra = extra
        self.content_h += extra
        self.h = max(self.content_h, self.min_h)

    def place(self, cv, x, y, h=None):
        with cv.group():
            super().place(cv, x, y, h)
            top = y + self.h - self.pad - self._extra
            for text, url, off in self._lk:
                cv.text(x + self.pad, top + off, text, size=self.src_size, color=LINK, link=url)
        return self


def block_arrow(cv, x, y, w, h, text, *, th="blue", size=17, tip=40, notch=False, sub=None, sub_size=14, reg=True):
    """Chevron-style block arrow with centred text (swim-arrow)."""
    t = theme(th)
    pts = [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h)]
    if notch:
        pts.append((x + tip, y + h / 2))
    pts.append(pts[0])
    pad_l = (tip + 12) if notch else 16
    tw = w - tip - pad_l - 12
    lines = metrics.wrap_text(text, tw, size)
    sub_lines = metrics.wrap_text(sub, tw, sub_size) if sub else []
    lh = metrics.line_ratio()
    th_h = len(lines) * size * lh + (len(sub_lines) * sub_size * lh + 3 if sub_lines else 0)
    with cv.group():
        cv.poly(pts, kind="line", stroke=t.stroke, fill=t.fill, fill_style="hachure", sw=2)
        ty = y + (h - th_h) / 2
        cv.text(x + pad_l, ty, "\n".join(lines), size=size, color=t.deep, align="center", w=tw)
        if sub_lines:
            cv.text(x + pad_l, ty + len(lines) * size * lh + 3, "\n".join(sub_lines), size=sub_size, color=MUTED,
                    align="center", w=tw)
    if reg:
        cv.register("blockarrow", x, y, w, h)


def sticker(cv, x, y, text, th="red", size=14):
    """Small pill drawn over a card edge (not registered, so it does not trigger overlap warnings)."""
    t = theme(th)
    tw = metrics.line_width(text, size) + 20
    with cv.group():
        cv.rect(x, y, tw, size * 1.25 + 8, stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0)
        cv.text(x + 10, y + 4, text, size=size, color=t.deep)
    return tw


def src_line(cv, x, y, items, size=12, gap=24):
    """Row of clickable 'Learn: ...' links; returns bottom y."""
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * metrics.line_ratio()


def rel_days(d: dt.date) -> str:
    n = (d - AS_OF).days
    if n == 0:
        return "today"
    return f"in {n} days" if n > 0 else f"{-n} days ago"


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "From Azure AI Studio to Microsoft Foundry",
                                "Why there are two portals, two SDK majors and two agent APIs - what changed, when, and what is retiring next  |  as of 2026-11-03",
                                w=W)
    y = bottom + 26
    legend(cv, 0, y, [("Classic / previous", "gray"), ("Current platform", "blue"), ("Agents and the Responses API", "green"),
                      ("Retired, retiring or deprecated", "red"), ("Preview or tools (as of 2026-11-03)", "orange")])
    y += 52
    H = s_glance(Canvas("measure"), 0, 0)
    y = s_glance(cv, y, H) + 70
    y = s_timeline(cv, y) + 80
    y = s_ladder_and_map(cv, y) + 80
    y = s_clock(cv, y) + 80
    y = s_news(cv, y) + 50
    y = s_notes(cv, y) + 60
    sources(cv, 0, y, [
        ("What is Microsoft Foundry? (Evolution of Foundry)", WHAT),
        ("Migrate from the Foundry (classic) portal", NAV),
        ("Migrate to the new agents developer experience", MIG),
        ("Upgrade from Azure OpenAI to Microsoft Foundry", UPG),
        ("Manage automatic upgrades from Azure OpenAI", UPGA),
        ("Migrate from hub-based to Foundry projects (classic)", HUB),
        ("Migrate from GitHub Models to Foundry Models", GHM),
        ("Microsoft Foundry portal general availability overview", GA),
        ("What's new in Microsoft Foundry (August 2026)", WN),
        ("Fabric data agent tool (deprecation 2026-11-06)", FABRIC),
        ("Register a custom agent (deprecation 2027-04-30)", CUSTOM),
        ("Foundry (classic) - What is Microsoft Foundry?", CLASSIC),
        ("Foundry DevBlog: What's new, September 2026", B_SEPT),
        ("Azure Blog: the next wave of Azure innovation (2024-11-19)", B_AZ2024),
    ], w=W, cols=3)


# ================================================================================================ 0. glance
def s_glance(cv: Canvas, y: float, H: float = 0) -> float:
    LW, RW, GAP = 1440, 1500, 60
    # ---- left: naming lineage
    with cv.panel(0, y, w=LW, min_h=H, title="Same platform, three names", sub="Learn: the Azure resource type stays Microsoft.CognitiveServices/accounts through every rename",
                  theme="gray", style="dotted", pad=24, title_size=26, sub_size=15) as lp:
        bw, gap = 360, 156
        chain1 = [("Azure AI Studio", "the earlier portal name", "gray"), ("Azure AI Foundry", "Ignite 2024: portal + SDK + Agent Service", "indigo"),
                  ("Microsoft Foundry", "current name (Ignite 2025)", "blue")]
        chain2 = [("Azure Cognitive Services", "the earlier services brand", "gray"), ("Azure AI Services", "renamed with the platform", "indigo"),
                  ("Foundry Tools", "current: Speech, Vision, Language, Content Safety, Content Understanding", "blue")]
        cy = lp.iy
        for chain in (chain1, chain2):
            boxes = [Box(bw, lab, sub=sub, theme=th, fill="hatch" if th != "gray" else "soft", dash="dashed" if th == "gray" else "solid",
                         size=19, sub_size=14, min_h=100, icon="foundry" if th == "blue" else None, icon_pos="left", icon_size=30)
                     for lab, sub, th in chain]
            hh = max(b.h for b in boxes)
            for i, b in enumerate(boxes):
                b.place(cv, lp.ix + i * (bw + gap), cy, h=hh)
            for i in range(2):
                a, b = boxes[i], boxes[i + 1]
                arrow(cv, [(a.right + 8, cy + hh / 2), (b.x - 8, cy + hh / 2)], end_head="arrow", sw=3)
            cy += hh + 26
        n = Note(LW - 48, "Microsoft's own wording: the AI platform evolved from Azure AI Studio -> Azure AI Foundry -> Microsoft Foundry (current), and the "
                          "services portfolio from Azure Cognitive Services -> Azure AI Services -> Foundry Tools (current). "
                          "All names in the documentation refer to the same evolving platform.", kind="key", title="One platform, renamed twice",
                 src=[("Migrate from the Foundry (classic) portal", NAV)])
        n.place(cv, lp.ix, cy)
    # ---- right: two of everything
    rx = LW + GAP
    with cv.panel(rx, y, w=RW, min_h=max(H, lp.h), title="Why there are two of everything", sub="classic = the previous generation, still reachable with the portal toggle  |  new = where new investment goes",
                  theme="blue", style="dotted", pad=24, title_size=26, sub_size=15) as rp:
        cols = [
            ("Portal", ("Foundry (classic)", "hub-based projects and Azure OpenAI resources"), ("Foundry", "ai.azure.com - New Foundry toggle in the banner")),
            ("Docs", ("Classic doc set", "learn.microsoft.com/azure/foundry-classic"), ("Current doc set", "learn.microsoft.com/azure/foundry")),
            ("SDK major", ("azure-ai-projects 1.x", "targets the classic portal"), ("azure-ai-projects 2.x", "targets the new portal")),
            ("Agent API", ("Assistants API", "Agents v0.5 / v1"), ("Responses API", "Agents v2")),
            ("Resource model", ("Hub + Azure OpenAI + Azure AI Services", "several resources"), ("Foundry resource + projects", "one resource, child projects")),
        ]
        cw, cg = 268, 20
        top = rp.iy
        pairs = []
        for lab, old, new in cols:
            ob = Box(cw, old[0], sub=old[1], theme="gray", fill="soft", dash="dashed", size=17, sub_size=13, min_h=118)
            nb = Box(cw, new[0], sub=new[1], theme="blue", fill="hatch", size=17, sub_size=13, min_h=118)
            pairs.append((lab, ob, nb))
        oh = max(p[1].h for p in pairs)
        nh = max(p[2].h for p in pairs)
        for i, (lab, ob, nb) in enumerate(pairs):
            x0 = rp.ix + i * (cw + cg)
            ch = Chip(lab, theme="blue", size=16, fill="solid")
            ch.place(cv, x0 + (cw - ch.w) / 2, top)
            ob.place(cv, x0, top + 46, h=oh)
            nb.place(cv, x0, top + 46 + oh + 46, h=nh)
            arrow(cv, [(x0 + cw / 2, top + 46 + oh + 6), (x0 + cw / 2, top + 46 + oh + 40)], end_head="arrow", sw=3)
        yy = top + 46 + oh + 46 + nh + 22
        src_line(cv, rp.ix, yy, [("What is Microsoft Foundry? (Evolution of Foundry)", WHAT), ("Migrate from the Foundry (classic) portal", NAV)])
    return max(lp.bottom, rp.bottom)


# ================================================================================================ 1. timeline
def s_timeline(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Timeline: how the platform evolved",
                   sub="Dates only where Microsoft Learn or an official Microsoft blog gives one  |  spacing is not to scale  |  as of 2026-11-03", w=W)
    top = y + 92
    CW, G = 481, 22
    nodes = [
        dict(up=True, th="gray", date="Undated: the 'Previous' column", head="Azure AI Studio and the hub-based generation", badge="classic",
             body=["Resource model: a hub plus Azure OpenAI and Azure AI Services resources",
                   "azure-ai-inference, azure-ai-generative, azure-ai-ml and AzureOpenAI() against 5+ endpoints",
                   "Assistants API (Agents v0.5/v1) with threads, messages and runs; monthly api-version parameters",
                   "Learn's Evolution table lists these as 'Previous' without dating them"],
             links=[("Learn", "What is Microsoft Foundry? (Evolution of Foundry)", WHAT)]),
        dict(up=False, th="indigo", date="2024-11-19", head="Ignite 2024: Azure AI Foundry announced",
             body=["A unified platform; Azure AI Studio becomes the Azure AI Foundry portal",
                   "New Azure AI Foundry SDK and Azure AI Agent Service",
                   "Content Understanding (preview); risk and safety evaluations for images"],
             links=[("Blog", "Azure Blog, 2024-11-19", B_AZ2024)]),
        dict(up=True, th="blue", date="2025-05-19", head="Build 2025: Agent Service GA and the Foundry resource",
             body=["Azure AI Foundry Agent Service generally available",
                   "Foundry resource type with projects as child resources: a renaming of the former Azure AI Services resource type",
                   "Foundry API, Foundry SDK, VS Code extension; new RBAC roles split control and data plane",
                   "Date = the GA blog; the Build recap post is undated"],
             links=[("Blog", "Agent Service GA", B_AGENTGA25), ("Blog", "Build recap", B_BUILD)]),
        dict(up=False, th="blue", date="2025-11-18", head="Ignite 2025: Azure AI Foundry becomes Microsoft Foundry",
             body=["Next evolution of Foundry Agent Service: multi-agent workflows, persistent memory, governance, M365 integration",
                   "Microsoft Agent Framework and hosted agents with consumption pricing"],
             links=[("Blog", "Azure at Microsoft Ignite 2025", B_IGNITE25), ("Blog", "DevBlog Oct-Nov 2025", B_DEV_ON25)]),
        dict(up=True, th="green", date="2026-03-16", head="Next-gen Foundry Agent Service GA",
             body=["Built on the Responses API: wire-compatible with OpenAI agents, open-model support",
                   "End-to-end private networking (BYO VNet), including tools",
                   "MCP auth: key, Entra Agent Identity, managed identity, OAuth identity passthrough",
                   "Evaluations GA; ai.azure.com portal GA; Voice Live + Agents (preview)"],
             links=[("Blog", "Foundry Agent Service is GA", B_AGENTGA)]),
        dict(up=False, th="green", date="2026-04-22", head="New hosted agents announced",
             body=["Secure, scalable compute built for agents",
                   "Projects created after 2026-06-25 support a private ACR for hosted agents"],
             links=[("Blog", "Introducing the new hosted agents", B_HOSTED), ("Learn", "Hosted agents", HOSTED)]),
        dict(up=True, th="green", date="2026-07-09", head="Hosted agents GA",
             body=["Announced in the GPT-5.6 availability post; confirmed in the July-August round-up",
                   "Jul-Aug 2026: Voice Live integration and Toolboxes GA",
                   "Claude on Azure: structured outputs, web search, web fetch, MCP connector, tool search"],
             links=[("Blog", "What's new, July and August 2026", B_JULAUG)]),
        dict(up=False, th="red", date="2026-07-30 and 2026-08-26", head="Already retired (as of 2026-11-03)", badge="retired",
             body=["2026-07-30: GitHub Models retired -> Foundry Models",
                   "2026-08-26: azure-ai-inference package retired -> openai package",
                   "2026-08-26: Assistants API sunset -> Foundry Agent Service on the Responses API"],
             links=[("Learn", "Migrate from the classic portal", NAV), ("Learn", "GitHub Models migration", GHM)]),
        dict(up=True, th="blue", date="2026-09", head="September 2026 round-up",
             body=["GPT-6 Astra (09-03), GPT-6 Luna (09-22), GPT-6.1 Sol (09-29) GA: 1.05M-token context, up to 128K output",
                   "09-15 Foundry DevPack: one-command dev environment",
                   "09-24 Routines GA; Tool Search and A2A GA; Insights (public preview)"],
             links=[("Blog", "What's new, September 2026", B_SEPT), ("Blog", "Dev Pack", B_DEVPACK), ("Blog", "Routines GA", B_ROUTINES)]),
        dict(up=False, th="orange", date="2026-10-19", head="Browser Automation tool GA",
             body=["Also in October: Microsoft Copilot harness (preview)",
                   "Docs disagree: the capability reference and the migration table still say preview; the tool page (2026-11-02) says GA"],
             links=[("Blog", "Browser Automation GA", B_BROWSER), ("Learn", "Browser automation tool", BROWSER)]),
        dict(up=True, th="red", date="2026-11-03: today", head="Custom-agent registration: deprecation notice", badge="retiring",
             body=["Control Plane custom-agent registration is scheduled for deprecation on 2027-04-30; new custom agents can no longer be added -> use external agents",
                   "Next: 2026-11-06 Fabric data agent tool, then 2026-12-01 Workflows (see the clock below)"],
             links=[("Learn", "Register a custom agent", CUSTOM)]),
    ]
    cards = []
    for n in nodes:
        cards.append(LCard(CW, n["date"], ["# " + n["head"]] + n["body"], theme=n["th"], badge=n.get("badge"), links=n["links"],
                           body_size=15, title_size=20, pad=14))
    up_h = max(c.h for c, n in zip(cards, nodes) if n["up"])
    dn_h = max(c.h for c, n in zip(cards, nodes) if not n["up"])
    bar_y = top + up_h + 44
    bar_h = 92
    dn_y = bar_y + bar_h + 44
    ku = kd = 0
    xs = []
    for c, n in zip(cards, nodes):
        if n["up"]:
            x = ku * (CW + G)
            ku += 1
            c.place(cv, x, top, h=up_h)
        else:
            x = (CW + G) / 2 + kd * (CW + G)
            kd += 1
            c.place(cv, x, dn_y, h=dn_h)
        xs.append(x + CW / 2)
    # era bar (chevrons)
    mids = [(xs[0] + xs[1]) / 2, (xs[1] + xs[2]) / 2, (xs[2] + xs[3]) / 2]
    edges = [0, mids[0], mids[1], mids[2], W]
    eras = [("Azure AI Studio", None, "gray", 19), ("Azure AI Foundry", None, "indigo", 19),
            ("Foundry resource + projects", None, "blue", 17),
            ("Microsoft Foundry + Agents v2", "Responses API, v1 stable routes, azure-ai-projects 2.x, hosted agents - the current platform", "green", 26)]
    tip = 28
    for i, (name, sub, th, fs) in enumerate(eras):
        x0 = 0 if i == 0 else edges[i] - tip + 6
        block_arrow(cv, x0, bar_y, edges[i + 1] - x0, bar_h, name, th=th, size=fs, tip=tip, notch=i > 0, sub=sub, sub_size=16, reg=False)
    # stems + nodes
    for c, n, nx in zip(cards, nodes, xs):
        th = theme(n["th"])
        if n["up"]:
            cv.line((nx, top + up_h), (nx, bar_y - 10), stroke=th.stroke, sw=2.5)
            cv.ellipse(nx - 11, bar_y - 11, 22, 22, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        else:
            cv.line((nx, bar_y + bar_h + 10), (nx, dn_y), stroke=th.stroke, sw=2.5)
            cv.ellipse(nx - 11, bar_y + bar_h - 11, 22, 22, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
    last = cards[-1]
    sticker(cv, last.right - 150, last.y - 14, "TODAY", "red", size=16)
    return dn_y + dn_h


# ================================================================================================ 2. ladder + Assistants -> Responses
def s_ladder_and_map(cv: Canvas, y: float) -> float:
    LW = 1500
    section_header(cv, 0, y, "Previous -> Current: what each classic name became", w=LW,
                   sub="Learn: the 'Evolution of Foundry' table plus extra rows from the classic-to-new terminology map")
    src_line(cv, 0, y + 78, [("What is Microsoft Foundry?", WHAT), ("Migrate from the Foundry (classic) portal", NAV)])
    rows = [
        ("Brand", "Azure AI Studio / Azure AI Foundry", "Microsoft Foundry"),
        ("Services brand", "Azure AI Services (earlier: Azure Cognitive Services)", "Foundry Tools"),
        ("Portal", "Foundry (classic)", "Foundry (the New Foundry toggle switches between them)"),
        ("Portal settings", "Management Center", "Operate section (plus Manage): navigation reorganised"),
        ("Resource model", "Hub + Azure OpenAI + Azure AI Services", "Foundry resource: one AIServices kind with child projects"),
        ("Agent API", "Assistants API (Agents v0.5/v1)", "Responses API (Agents v2)"),
        ("API versioning", "Monthly api-version parameters", "v1 stable routes (/openai/v1/): no version parameter"),
        ("SDKs and endpoints", "azure-ai-inference, azure-ai-generative, azure-ai-ml, AzureOpenAI() against 5+ endpoints",
         "Unified project client (azure-ai-projects 2.x) + OpenAI() against one project endpoint"),
        ("Model billing", "Model-as-a-Service (MaaS)", "Foundry Direct Models: first-party models billed directly through Azure meters"),
        ("RBAC roles", "Cognitive Services OpenAI User", "Foundry User, Foundry Project Manager, Foundry Owner: control and data plane separated"),
        ("Terminology", "Threads, Messages, Runs, Assistants", "Conversations, Items, Responses, Agent Versions"),
        ("Documentation", "Classic docs (foundry-classic)", "Current docs (foundry): two separate doc sets"),
    ]
    pw, aw, nw = 540, 100, 700
    ty = y + 112
    tag_w = 200
    c_old = Chip("Previous (classic)", theme="gray", size=17, fill="solid")
    c_old.place(cv, tag_w + 20 + (pw - c_old.w) / 2, ty)
    c_new = Chip("Current (Microsoft Foundry)", theme="blue", size=17, fill="solid")
    c_new.place(cv, tag_w + 20 + pw + aw + (nw - 20 - c_new.w) / 2, ty)
    ty += 52
    for dim, old, new in rows:
        ob = Box(pw, old, theme="gray", fill="soft", dash="dashed", size=16, pad=9)
        nb = Box(nw - 20, new, theme="blue", fill="hatch", size=16, pad=9)
        hh = max(ob.h, nb.h, 54)
        t = Chip(dim, theme="gray", size=15, fill="hatch", w=tag_w - 10)
        t.place(cv, 0, ty + (hh - t.h) / 2)
        ob.place(cv, tag_w + 20, ty, h=hh)
        nb.place(cv, tag_w + 20 + pw + aw, ty, h=hh)
        arrow(cv, [(ob.right + 8, ty + hh / 2), (nb.x - 8, ty + hh / 2)], end_head="arrow", sw=3)
        ty += hh + 14
    why = Card(LW, "Why the new agents (Learn: key benefits)", [
        "More models: any Foundry model in an agent or as a direct response call; more tools: Web Search, File Search, Code Interpreter, MCP, image generation, reasoning summaries",
        "Background mode with durable streams (disconnect and reconnect); agents can be exposed as individual endpoints",
        "Single-tenant storage with an optional bring-your-own Azure Cosmos DB for state; stateful by default",
        "New features and model support are only added to the new agents",
    ], theme="green", icon="agent", body_size=15, src=[("Migrate to the new agents developer experience", MIG)])
    why.place(cv, 0, ty + 10)
    left_bottom = why.bottom

    # ---------------------------------------------------------------- right: Assistants -> Responses
    RX = LW + 70
    RW = W - RX
    section_header(cv, RX, y, "Assistants -> Responses: the object model", w=RW,
                   sub="Threads, messages and runs become conversations, items and responses; assistants become versioned agents")
    src_line(cv, RX, y + 78, [("Migrate to the new agents developer experience", MIG), ("Migrate from the classic portal", NAV)])
    py = y + 112
    LPW, MID = 500, 300
    RPW = RW - LPW - MID
    with cv.panel(RX, py, w=LPW, title="Assistants API (classic)", sub="Agents v0.5 / v1", theme="gray", style="dashed", fill="none", pad=18,
                  title_size=22, sub_size=15) as lp:
        old = [("Assistant / classic agent", "create_agent()"), ("Thread", "conversation state: messages"), ("Message", "a chat message in a thread"),
               ("Run", "async: create it, then poll for status")]
        obs = []
        yy = lp.iy
        for lab, sub in old:
            b = Box(LPW - 36, lab, sub=sub, theme="gray", fill="soft", dash="dashed", size=18, sub_size=14, min_h=92)
            b.place(cv, lp.ix, yy)
            obs.append(b)
            yy += b.h + 26
    with cv.panel(RX + LPW + MID, py, w=RPW, title="Responses API (current)", sub="Agents v2 / new Foundry Agent Service", theme="green", style="solid",
                  fill="soft", pad=18, title_size=22, sub_size=15) as rp:
        new = [("Agent version", "create_version() with PromptAgentDefinition; explicit kind: prompt, workflow, hosted"),
               ("Conversation", "a stream of items, not just messages"),
               ("Item", "superset of messages: messages, tool calls and tool outputs"),
               ("Response", "send input items or a conversation, get output items; sync by default, no polling")]
        nbs = []
        yy = rp.iy
        for (lab, sub), ob in zip(new, obs):
            b = Box(RPW - 36, lab, sub=sub, theme="green", fill="hatch", size=18, sub_size=14, min_h=92)
            b.place(cv, rp.ix, yy, h=ob.h)
            nbs.append(b)
            yy += ob.h + 26
    for ob, nb, lab in zip(obs, nbs, ["versioned", "stores items", "superset", "no polling loop"]):
        connect(cv, ob, nb, a_side="right", b_side="left", label=lab, label_size=15, sw=3, gap=10)
    my = max(lp.bottom, rp.bottom) + 40

    cw2 = (RW - 30) / 2
    c1 = Card(cw2, "Project client", ["AIProjectClient: create and version agents", "Connections, project properties, tracing"],
              theme="blue", icon="foundry", body_size=15)
    c2 = Card(cw2, "OpenAI client", ["project.get_openai_client(): conversations and responses", "Agent runs, evals, fine-tuning; C#: GetProjectResponsesClientForAgent()"],
              theme="green", icon="openai", body_size=15)
    rb = row(cv, RX, my, [c1, c2], gap=30)[1]
    t = cv.text(RX, rb + 6, "Most apps use both.  Learn: ", size=13, color=MUTED)
    cv.text(RX + t.w, rb + 6, "Migrate to the new agents developer experience", size=12, color=LINK, link=MIG)
    cy = rb + 48

    code = [("AzureOpenAI(...)", "OpenAI(base_url=...)"), ("azure-ai-inference", "openai   (retired 2026-08-26)"),
            ("azure-ai-projects 1.x", "azure-ai-projects 2.x"), ("create_agent()", "create_version(PromptAgentDefinition)"),
            ("thread / message / run", "conversation / item / response")]
    mono, fs = metrics.MONO, 17
    cw_l = max(metrics.line_width(a, fs, mono) for a, _ in code)
    ch_ = fs * metrics.line_ratio(mono)
    box_h = 20 + 26 + len(code) * (ch_ + 8) + 14
    with cv.group():
        cv.rect(RX, cy, RW, box_h, stroke="#495057", fill="#f8f9fa", style="solid", sw=2)
        cv.text(RX + 20, cy + 12, "Code-shape cheat sheet (names as documented)", size=18, color="#343a40")
        ly = cy + 46
        for a, b in code:
            cv.text(RX + 20, ly, a, size=fs, font=mono, color="#c92a2a")
            cv.text(RX + 20 + cw_l + 20, ly, "->", size=fs, font=mono, color=INK)
            cv.text(RX + 20 + cw_l + 70, ly, b, size=fs, font=mono, color="#2b8a3e")
            ly += ch_ + 8
    cv.register("cheatsheet", RX, cy, RW, box_h)
    cy += box_h + 28
    err = Note(RW, "404 or MethodNotAllowed means Assistants calls were sent to a Responses endpoint: rewrite the code to use create_version() instead of "
                   "create_agent(). Keep the SDK major in line with the portal (2.x = new, 1.x = classic).", kind="gotcha", title="Common migration error",
               src=[("Migrate from the Foundry (classic) portal", NAV)])
    err.place(cv, RX, cy)
    return max(left_bottom, err.bottom)


# ================================================================================================ 3. deprecation clock
def s_clock(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "The deprecation clock", w=W,
                   sub="Positions are ordered, not to scale  |  day counts are measured from 2026-11-03  |  Learn pages as of 2026-11-03")
    y += 4
    items = [
        (dt.date(2026, 7, 30), "GitHub Models retired", "Migrate to Foundry Models: same API shape, new endpoint and credentials", GHM, "Migrate from GitHub Models", "past"),
        (dt.date(2026, 8, 26), "azure-ai-inference package retired", "Use the openai package: OpenAI() with base_url replaces AzureOpenAI()", INFER, "azure-ai-inference to OpenAI SDK", "past"),
        (dt.date(2026, 8, 26), "Assistants API sunset", "Use Foundry Agent Service on the Responses API (create_version, conversations, responses)", MIG, "Migrate to the new agents experience", "past"),
        (dt.date(2026, 11, 6), "Fabric data agent tool deprecated", "Use the Fabric IQ tool instead; the Learn page has steps to update your agent", FABRIC, "Fabric data agent tool", "soon"),
        (dt.date(2026, 12, 1), "Workflows retire (preview)", "Use Microsoft Agent Framework for new development; do not build new production dependencies on Workflows", GA, "Portal general availability overview", "soon"),
        (dt.date(2027, 3, 20), "Azure Language Studio retires", "It migrates to Microsoft Foundry; all capabilities and future enhancements land in Foundry", SDK, "Foundry SDK overview", "later"),
        (dt.date(2027, 4, 30), "Custom-agent registration deprecated", "Control Plane: no new custom agents can be added; use external agents for evaluation, observability and optimization", CUSTOM, "Register a custom agent", "later"),
        (dt.date(2029, 3, 31), "Azure Language features end of support", "Sentiment analysis, key phrase extraction, summarization, entity linking, CQA and CLU (see Learn for the full list): move to Foundry models", SDK, "Foundry SDK overview", "later"),
    ]
    n = len(items)
    cw, g = 355, 22
    x0 = (W - (n * cw + (n - 1) * g)) / 2
    styles = {"past": ("gray", "soft", "dashed"), "soon": ("red", "hatch", "solid"), "later": ("orange", "hatch", "solid")}
    cards = []
    for d, title, what, url, lab, kind in items:
        th, fill, dash = styles[kind]
        days = rel_days(d)
        c = Card(cw, d.isoformat(), [f"# {title}", what], theme=th, fill=fill, dash=dash, body_size=15, title_size=22, pad=14,
                 badge="retired" if kind == "past" else None, src=[(lab, url)])
        cards.append((c, d, days, kind))
    hh = max(c.h for c, *_ in cards)
    y0 = y + 86
    bar_y = y0 + 92
    cy = y0 + 150
    cv.line((0, bar_y), (W - 30, bar_y), stroke=INK, sw=4)
    cv.poly([(W - 46, bar_y - 12), (W - 24, bar_y), (W - 46, bar_y + 12)], kind="line", stroke=INK, sw=4)
    today_x = x0 + 3 * (cw + g) - g / 2
    for i, (c, d, days, kind) in enumerate(cards):
        cx = x0 + i * (cw + g)
        c.place(cv, cx, cy, h=hh)
        th = theme(styles[kind][0])
        cv.line((cx + cw / 2, bar_y + 10), (cx + cw / 2, cy), stroke=th.stroke, sw=2.5)
        cv.ellipse(cx + cw / 2 - 11, bar_y - 11, 22, 22, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        cv.text(cx + cw / 2 - 90, bar_y - 46, days, size=22 if kind != "past" else 18, color=th.deep, align="center", w=180)
    cv.line((today_x, y0 + 36), (today_x, cy + hh + 10), stroke="#e03131", sw=3, dash="dashed")
    sticker(cv, today_x - 100, y0, "TODAY  2026-11-03", "red", size=16)
    Chip("Already retired (3)", theme="gray", size=16, fill="solid").place(cv, x0, y0)
    c2 = Chip("Still ahead (5)", theme="red", size=16, fill="solid")
    c2.place(cv, today_x + 150, y0)
    return cy + hh + 12


# ================================================================================================ 4. what's new ticker
def s_news(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "What's new: a ticker from July to October 2026", w=W,
                   sub="Learn's What's new article covers August 2026 only (page updated 2026-09-09); the other columns come from the Foundry DevBlog and are not Learn-verified")
    y += 96
    gap = 30
    cols = [
        ("Learn: What's new (August 2026)", WN, "Learn", [
            ("green", "Agent optimizer: cost and token usage"), ("green", "Autopilot overview and lifecycle"),
            ("orange", "Long-running agent resilience + API reference (preview)"), ("orange", "Human-in-the-loop approval (preview)"),
            ("orange", "Crash-resilient, steerable agents (preview)"), ("green", "Bring your own registry for hosted agents"),
            ("green", "Private skill catalog"), ("green", "Toolbox network isolation"), ("orange", "Optimize a prompt agent (preview)"),
            ("blue", "Model migration process"), ("blue", "Reasoning models"), ("blue", "Grok models"), ("blue", "MAI-Thinking-1"),
            ("blue", "Evaluate model router"), ("blue", "Multi-agent orchestration with the Responses API"),
            ("violet", "Cloud evaluation SDK set"), ("violet", "Admin-connected models"), ("violet", "Evaluation dataset schema"),
            ("orange", "Entra auth for trace ingestion (preview)"), ("gray", "Product and capability map"), ("gray", "Capability reference"),
            ("gray", "Customer-managed keys article"), ("gray", "Foundry Skill scenarios"), ("gray", "Foundry Toolkit for VS Code docs"),
            ("pink", "Content provenance"),
        ]),
        ("DevBlog: July and August 2026 round-up", B_JULAUG, "Blog", [
            ("green", "Hosted agents GA (2026-07-09)"), ("green", "Voice Live integration GA"), ("orange", "Toolboxes GA"),
            ("blue", "Claude on Azure: structured outputs"), ("blue", "Claude: web search and web fetch"), ("blue", "Claude: MCP connector and tool search"),
            ("blue", "Model Router: region and pool refresh"), ("gray", "Foundry DevPack 0.1.3 preview installers"),
        ]),
        ("DevBlog: September 2026 round-up", B_SEPT, "Blog", [
            ("blue", "GPT-6 Astra GA (09-03)"), ("blue", "GPT-6 Luna GA (09-22)"), ("blue", "GPT-6.1 Sol GA (09-29)"),
            ("gray", "Foundry DevPack launched (09-15)"), ("green", "Routines GA (09-24)"), ("orange", "Tool Search GA"), ("green", "A2A GA"),
            ("orange", "Insights (public preview)"), ("orange", "Toolboxes for prompt agents (public preview)"),
            ("orange", "Voice agents (public preview)"), ("orange", "Long-running hosted-agent resilience (public preview)"),
            ("blue", "Model Router session affinity (preview)"),
        ]),
        ("DevBlog: October 2026", B_BROWSER, "Blog", [
            ("orange", "Browser Automation tool GA (10-19)"), ("orange", "Microsoft Copilot harness (preview)"),
        ]),
    ]
    widths = [1150, 640, 760, 2910 - 1150 - 640 - 760]
    flows = []
    for (title, url, kind, chips), cw_ in zip(cols, widths):
        items = []
        for th, label in chips:
            prev = "preview" in label
            items.append(Chip(label, theme=th, size=14, fill="soft", dash="dashed" if prev else "solid", pad_x=10, pad_y=5))
        flows.append(ChipFlow(items, cw_ - 40, gap=8))
    maxh = max(f.h for f in flows)
    ph = maxh + 112
    x = 0
    for (title, url, kind, chips), f, cw_ in zip(cols, flows, widths):
        with cv.panel(x, y, w=cw_, h=ph, title=title, theme="gray", style="dotted", fill="none", pad=20, title_size=20) as p:
            f.place(cv, p.ix, p.iy)
        cv.text(x + 20, y + ph - 34, {"Learn": "Learn: What's new in Microsoft Foundry (August 2026)", "Blog": f"Blog: {title.split(': ', 1)[1]}"}[kind],
                size=12, color=LINK, link=url)
        x += cw_ + gap
    lg = legend(cv, 0, y + ph + 20, [("Agents", "green"), ("Models", "blue"), ("Tools", "orange"), ("Observability", "violet"), ("Platform", "gray"), ("Responsible AI", "pink")])
    cv.text(lg.right + 40, y + ph + 20, "dashed outline = preview as labelled in the source", size=15, color=MUTED)
    return y + ph + 40


# ================================================================================================ 5. notes
def s_notes(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Gotchas, caveats and what comes next", w=W)
    y += 64
    nw = 720
    notes = [
        Note(nw, "The migration page still words 2026-08-26 as 'Assistants API sunsets' (now past), while the portal GA overview says existing assistants and v1 agents "
                 "are not supported in the new portal 'until assistant upgrade is available', and a tag can block new classic agents. Treat classic Assistants as "
                 "sunset or legacy and plan the move.", kind="warn", title="Docs disagree: is the Assistants API gone?",
             src=[("Migrate from the classic portal", NAV), ("Portal GA overview", GA), ("Disable classic agents", DISABLE)]),
        Note(nw, "Ignite 2024's date comes from the Azure Blog byline; the Build 2025 recap post is undated (2025-05-19 is the GA blog); the Microsoft Foundry rename is "
                 "attributed to Ignite 2025 (Azure Blog 2025-11-18; a partner post 2025-12-11) - there is no single dated rename page. March and July 2026 dates come from "
                 "DevBlog posts.", kind="info", title="Timeline caveats"),
        Note(nw, "azure-ai-projects 2.x targets the new portal and 1.x targets classic; mixing a 2.x sample with a 1.x setup (or the reverse) causes errors. "
                 "Prerequisites for the SDK migration: Python 3.10+ or .NET 8+.", kind="tip", title="Match the SDK major to the portal",
             src=[("Migrate from the classic portal", NAV), ("Foundry SDK overview", SDK)]),
        Note(nw, "Part 2 of this canvas, 'Classic to new: the migration playbook', has the decision tree, the five migration paths (Azure OpenAI upgrade, hub to project, "
                 "Assistants to agents, Agent Applications, GitHub Models), what stays classic-only, the portal map and agent tool availability.",
             kind="key", title="Next: how to move"),
    ]
    hmax = max(n.h for n in notes)
    for j, n in enumerate(notes):
        n.place(cv, j * (nw + 40), y, h=hmax)
    return y + hmax
