"""Classic to new: the migration playbook (part 2 of 'From Azure AI Studio to Microsoft Foundry') - decision tree, five migration
paths, what stays classic-only, portal map and agent tool availability (as of 2026-11-03)."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="evolution-classic-to-new-part-2", title="Classic to new: the migration playbook", section="1", group="Overview", order=5.5,
    description="A decision tree and five swim-arrow migration paths (Azure OpenAI upgrade incl. auto-upgrade, hub to Foundry project, Assistants to agents, "
                "Agent Applications, GitHub Models), what stays classic-only, the portal map and agent tool availability.",
    tags=["migration", "upgrade", "hub", "assistants", "agent-applications"],
)

W = 3000

# ------------------------------------------------------------------------------------------------ sources
NAV = learn("how-to/navigate-from-classic")
MIG = learn("agents/how-to/migrate")
MIGAPP = learn("agents/how-to/migrate-agent-applications")
DISABLE = learn("agents/how-to/disable-classic-agents")
UPG = learn("how-to/upgrade-azure-openai")
UPGA = learn("how-to/upgrade-azure-openai-auto")
HUB = learn("foundry-classic/how-to/migrate-project", base="azure")
CLASSIC = learn("foundry-classic/what-is-foundry", base="azure")
GHM = learn("foundry-models/how-to/quickstart-github-models")
INFER = learn("how-to/model-inference-to-openai-migration")
GA = learn("concepts/general-availability")
SDK = learn("how-to/develop/sdk-overview")
CC2R = learn("ai/how-to/azure-openai-to-responses", base="azure/developer")
FABRIC = learn("agents/how-to/tools/fabric")
TOOL = "https://aka.ms/agent/migrate/tool"


# ================================================================================================ local helpers
def block_arrow(cv, x, y, w, h, text, *, th="blue", size=17, tip=40, sub=None, sub_size=14):
    """Chevron-style block arrow with centred text (swim-arrow)."""
    t = theme(th)
    pts = [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h), (x, y)]
    tw = w - tip - 28
    lines = metrics.wrap_text(text, tw, size)
    sub_lines = metrics.wrap_text(sub, tw, sub_size) if sub else []
    lh = metrics.line_ratio()
    th_h = len(lines) * size * lh + (len(sub_lines) * sub_size * lh + 3 if sub_lines else 0)
    with cv.group():
        cv.poly(pts, kind="line", stroke=t.stroke, fill=t.fill, fill_style="hachure", sw=2)
        ty = y + (h - th_h) / 2
        cv.text(x + 16, ty, "\n".join(lines), size=size, color=t.deep, align="center", w=tw)
        if sub_lines:
            cv.text(x + 16, ty + len(lines) * size * lh + 3, "\n".join(sub_lines), size=sub_size, color=MUTED, align="center", w=tw)
    cv.register("blockarrow", x, y, w, h)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Classic to new: the migration playbook",
                                "Five starting points, what transfers and what does not, which roles you need, and what stays classic-only  |  part 2 of From Azure AI Studio to Microsoft Foundry  |  as of 2026-11-03",
                                w=W)
    y = bottom + 26
    legend(cv, 0, y, [("Classic / previous", "gray"), ("Current platform", "blue"), ("Agents and the Responses API", "green"),
                      ("Gotcha or loss", "red"), ("Preview or caution", "orange")])
    y += 56
    y = s_decision(cv, y) + 70
    y = s_migration(cv, y) + 80
    y = s_parity(cv, y) + 80
    y = s_notes(cv, y) + 60
    sources(cv, 0, y, [
        ("Migrate from the Foundry (classic) portal", NAV),
        ("Migrate to the new agents developer experience", MIG),
        ("Migrate from agent applications to the new agent endpoint", MIGAPP),
        ("Disable creation of classic agents and assistants", DISABLE),
        ("Upgrade from Azure OpenAI to Microsoft Foundry", UPG),
        ("Manage automatic upgrades from Azure OpenAI", UPGA),
        ("Migrate from hub-based to Foundry projects (classic)", HUB),
        ("Migrate from GitHub Models to Foundry Models", GHM),
        ("Migrate from azure-ai-inference to the OpenAI SDK", INFER),
        ("Azure OpenAI to the Responses API (Azure developer docs)", CC2R),
        ("Microsoft Foundry portal general availability overview", GA),
        ("Microsoft Foundry SDKs overview", SDK),
        ("Foundry (classic) - What is Microsoft Foundry?", CLASSIC),
        ("Assistants API migration tool (aka.ms/agent/migrate/tool)", TOOL),
    ], w=W, cols=3)


# ================================================================================================ 0. decision tree
def s_decision(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Where do I start? Work through the questions", w=W,
                   sub="Answers are not exclusive: follow every 'yes'. Details for each path follow below.  |  Learn: migration decision flow built from the classic-to-new, upgrade and agent migration pages")
    y += 96
    qs = [
        ("Standalone Azure OpenAI resource?", "blue", "Path 1: upgrade in place", "opt-in, or Microsoft auto-upgrade; Owner role + managed identity"),
        ("Hub-based project?", "blue", "Path 2: migrate the project", "new Foundry project on the Foundry resource; Owner role"),
        ("Assistants API or classic agents?", "green", "Path 3: move to new agents", "map tools, create_version(), conversations and responses"),
        ("Published Agent Applications?", "green", "Path 4: adopt the agent object", "endpoint, identity and deployment are built into the agent"),
        ("GitHub Models, azure-ai-inference or Chat Completions?", "blue", "Path 5: Foundry Models + openai", "same API shape: change endpoint and credentials"),
    ]
    dw, dh, gap = 400, 150, 130
    top = y + 44
    Chip("Start: what are you running today?", theme="blue", size=18, fill="solid").place(cv, 0, y)
    diamonds, paths = [], []
    for i, (q, th, ptitle, psub) in enumerate(qs):
        x = i * (dw + gap)
        d = Box(dw, q, h=dh, theme=th, shape="diamond", fill="hatch", size=17)
        d.place(cv, x, top)
        diamonds.append(d)
        p = Box(dw, ptitle, sub=psub, theme=th, fill="solid", size=18, sub_size=14, min_h=110, icon="foundry" if th == "blue" else "agent", icon_pos="left", icon_size=30)
        p.place(cv, x, top + dh + 70)
        paths.append(p)
    for i in range(4):
        connect(cv, diamonds[i], diamonds[i + 1], a_side="right", b_side="left", label="no", label_size=17, sw=3, gap=8)
    for d, p in zip(diamonds, paths):
        connect(cv, d, p, a_side="bottom", b_side="top", label="yes", label_size=17, sw=3, gap=8)
    fx = 4 * (dw + gap) + dw + 120
    fin = Box(W - fx, "Everyone: check your region", sub="does it support the Responses API and Foundry Agent Service? If not, create a new Foundry resource in a supported region",
              theme="orange", fill="hatch", size=18, sub_size=14, min_h=dh, icon="regions", icon_pos="top", icon_size=30)
    fin.place(cv, fx, top + dh / 2 - fin.h / 2 if fin.h < dh else top)
    connect(cv, diamonds[4], fin, a_side="right", b_side="left", label="no", label_size=17, sw=3, gap=8)
    bottom = max(p.bottom for p in paths)
    return bottom


# ================================================================================================ 1. migration paths
def lane(cv: Canvas, y: float, title: str, sub: str, th: str, strip, cards, *, notes=(), flow=None, strip_w=1100) -> float:
    sh = strip(Canvas("measure"), 0, 0)
    all_cards = all(isinstance(c, Card) for c in cards)
    ch = max(c.h for c in cards)
    left_h = sh + sum(20 + n.h for n in notes)
    H = max(ch, left_h)
    off = (H - left_h) / 2 if (not notes and H > left_h) else 0
    with cv.panel(0, y, w=W, title=title, sub=sub, theme=th, style="dashed", fill="soft", pad=22, title_size=26, sub_size=16) as p:
        top = p.iy + 4
        ny = strip(cv, p.ix, top + off)
        for nt in notes:
            ny += 20
            nt.place(cv, p.ix, ny)
            ny = nt.bottom
        if all_cards:
            for c in cards:
                c.min_h = H
                c.h = max(c.h, H)
        row(cv, p.ix + strip_w + 50, top, cards, gap=18, equalize=all_cards)
        bottom = top + H
        if flow is not None:
            bottom = flow(cv, p.ix, bottom + 24, W - 2 * p.pad)
    return p.bottom


def step_flow(title, steps, th, *, optional_from=None, src=(), size=15, h=88):
    """Horizontal chevron process flow under a lane: steps drawn as numbered chevrons (optional ones dashed)."""
    def draw(cv, x, y, w):
        t = theme(th)
        cv.text(x, y, title, size=18, color=t.deep)
        y0 = y + 30
        n, gap, tip = len(steps), 6, 26
        sw = (w - (n - 1) * gap) / n
        for i, s in enumerate(steps):
            sx = x + i * (sw + gap)
            pts = [(sx, y0), (sx + sw - tip, y0), (sx + sw, y0 + h / 2), (sx + sw - tip, y0 + h), (sx, y0 + h)]
            if i > 0:
                pts.append((sx + tip, y0 + h / 2))
            pts.append(pts[0])
            opt = optional_from is not None and i >= optional_from
            with cv.group():
                cv.poly(pts, kind="line", stroke=t.stroke, fill=t.fill if not opt else t.soft, fill_style="hachure" if not opt else "solid", sw=2,
                        dash="dashed" if opt else "solid")
                lx = sx + (tip + 14 if i > 0 else 14)
                numbered(cv, lx + 14, y0 + h / 2, i + 1, theme=th, d=28, size=15)
                tw = sw - (tip + 14 if i > 0 else 14) - tip - 14 - 36
                lines = metrics.wrap_text(s, tw, size)
                cv.text(lx + 40, y0 + (h - len(lines) * size * metrics.line_ratio()) / 2, "\n".join(lines), size=size, color=INK)
            cv.register("stepchevron", sx + (tip if i > 0 else 0) + 2, y0 + 2, sw - tip - 4, h - 4)
        yy = y0 + h + 6
        for label, url in src:
            cv.text(x, yy, f"Learn: {label}", size=12, color=LINK, link=url)
            yy += 15
        return yy
    return draw


def simple_strip(src_box, arrow_text, dst_box, th, *, aw=420):
    def draw(cv, x, y):
        H = max(src_box.h, dst_box.h)
        src_box.place(cv, x, y, h=H)
        block_arrow(cv, src_box.right + 12, y + H / 2 - 62, aw, 124, arrow_text, th=th, size=17, tip=36)
        dst_box.place(cv, src_box.right + 12 + aw + 12, y, h=H)
        return y + H
    return draw


def s_migration(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Five migration paths", w=W,
                   sub="Roles and limits as documented on Learn  |  preview surfaces are marked  |  as of 2026-11-03")
    y += 96
    pre = [
        Note(960, "The Responses API and Foundry Agent Service are not available in every Azure region. If your Foundry resource is in an unsupported region, "
                  "agents and other Responses API features do not work in the new portal: create a new Foundry resource in a supported region first.",
             kind="gotcha", title="Check your region first", src=[("Migrate from the Foundry (classic) portal", NAV)]),
        Note(960, "Foundry projects aren't yet at full parity with hub-based projects, and the new portal shows only Foundry projects. "
                  "Hub-based projects and standalone Azure OpenAI resources stay reachable by switching the New Foundry toggle off.",
             kind="warn", title="Keep the classic portal handy", src=[("Portal general availability overview", GA)]),
        Note(960, "Foundry User, Foundry Owner, Foundry Account Owner and Foundry Project Manager were previously named Azure AI User / Owner / Account Owner / "
                  "Project Manager. Role IDs and core permissions are unchanged; you may still see the old names in places.",
             kind="info", title="Role names", src=[("Migrate from the Foundry (classic) portal", NAV)]),
    ]
    row(cv, 0, y, pre, gap=60)
    y += max(n.h for n in pre) + 36

    # ---- path 1: Azure OpenAI -> Foundry resource
    s1 = simple_strip(Box(330, "Azure OpenAI resource", sub="kind: OpenAI", theme="gray", fill="soft", dash="dashed", icon="openai", size=19, sub_size=15, min_h=150),
                      "Upgrade in place: opt-in, or scheduled by Microsoft (auto-upgrade)",
                      Box(330, "Foundry resource", sub="kind: AIServices + allowProjectManagement; gets a default project", theme="blue", fill="hatch", icon="foundry",
                          size=19, sub_size=15, min_h=150), "blue")
    n1 = Table([("What you gain by upgrading", 450), ("Azure OpenAI", 200), ("Foundry", 450)], [
        ["Foundry Models sold by Azure", "Azure OpenAI only", "Azure OpenAI, Black Forest Labs, DeepSeek, Meta, xAI, Mistral, Microsoft"],
        ["Partner and community models through Marketplace (Stability, Cohere, others)", CROSS, CHECK],
        ["Azure OpenAI API: batch, stored completions, fine-tuning, evaluation", CHECK, CHECK],
        ["Agent Service and the Foundry API", CROSS, CHECK],
        ["Foundry Tools: Speech, Vision, Language, Content Understanding", CROSS, CHECK],
    ], w=1100, theme="blue", size=14, head_size=15, align=["left", "center", "left"])
    c1a = Card(590, "How to upgrade (opt-in)", [
        "Both resource types stay GA and supported before and after; the upgrade is opt-in and your first 'default' project is backward compatible",
        "Foundry (classic) portal or Azure portal: banner 'Want to try the latest industry models and Agents?' -> Get started",
        "Bicep or ARM template: kind OpenAI -> AIServices, allowProjectManagement: true, managed identity; recommended for custom security settings",
        "Terraform: AzureRM 4.56.0 or later (non-destructive kind change), or AzAPI",
        "Needs: Owner on the subscription or resource group, and system-assigned managed identity on the resource",
    ], theme="blue", body_size=15, src=[("Upgrade from Azure OpenAI to Foundry", UPG)])
    c1b = Card(590, "What carries over - and the limits", [
        "+ Keeps: resource name, tags, network and identity configuration, API endpoint and key, custom domain, fine-tuning jobs, batch, stored completions",
        "! Weights & Biases integration is not supported on a Foundry resource",
        "! Existing private endpoints block the portal upgrade: delete and recreate them, or use Bicep or Terraform; extra DNS zones are needed",
        "Agent Service is available in fewer regions than Azure OpenAI",
        "Detect an upgraded resource: properties.previousKind = OpenAI",
    ], theme="gray", body_size=15, src=[("Upgrade from Azure OpenAI to Foundry", UPG)])
    c1c = Card(590, "Auto-upgrade, opt-out and rollback", [
        "Microsoft upgrades eligible resources in stages; private-networking and CMK resources are not selected at first",
        "ARM block foundryAutoUpgrade: mode, plannedByMicrosoft, scheduledAt, statusReason (preview API 2026-01-15-preview)",
        "Defer in the Azure portal (Resource upgrade); opt out with mode: Disabled in Bicep or Terraform AzAPI",
        "Rollback: delete projects, connections and non-OpenAI deployments first, then roll back (portal, or set kind back to OpenAI)",
        "After upgrade: Cognitive Services User = all Foundry features; Cognitive Services OpenAI User = OpenAI only. Review wildcard roles and policies",
    ], theme="violet", body_size=15, badge="preview", src=[("Manage automatic upgrades", UPGA)])
    y = lane(cv, y, "Path 1: Azure OpenAI resource -> Foundry resource", "Do you have a standalone Azure OpenAI resource?", "blue", s1, [c1a, c1b, c1c],
             notes=[n1]) + 30

    # ---- path 2: hub -> Foundry project
    s2 = simple_strip(Box(330, "Hub-based project", sub="visible only in the classic portal", theme="gray", fill="soft", dash="dashed", icon="ml", size=19, sub_size=15, min_h=140),
                      "Create a Foundry project on the Foundry resource (Owner role, about 5-10 minutes)",
                      Box(330, "Foundry project", sub="child of the Foundry (AI Services) resource", theme="blue", fill="hatch", icon="foundry", size=19, sub_size=15, min_h=140),
                      "blue")
    st2 = step_flow("How (Learn: classic migrate-project article)", [
        "Locate your existing Foundry (AI Services) resource",
        "Create the new Foundry project on that resource from your hub-based project",
        "Optional: recreate connections",
        "Optional: migrate agents by recreating them in code",
    ], "blue", optional_from=2, src=[("Migrate from hub-based to Foundry projects (classic)", HUB)])
    c2a = Card(590, "What transfers", ["+ Model deployments", "+ Data files", "+ Fine-tuned models", "+ Vector stores"], theme="green", body_size=15,
               src=[("Migrate from hub-based to Foundry projects (classic)", HUB)])
    c2b = Card(590, "What does not transfer", ["! Preview agent state (messages, threads, files): recreate the agent in code in the new project",
                                              "! Open-source model deployments: Foundry projects do not support them yet",
                                              "! Hub project access: hub-based projects cannot see the new projects"], theme="red", body_size=15,
               src=[("Migrate from hub-based to Foundry projects (classic)", HUB)])
    c2c = Card(590, "Why move", ["New generative AI and model-centric features are available only through the Foundry resource and its projects",
                                 "Foundry API + Foundry SDK; agents, models and tools managed together for permissions, networking, cost and policy",
                                 "Projects are child resources: set security and connectivity once at the resource, create projects as folders"],
               theme="blue", body_size=15, src=[("Migrate from hub-based to Foundry projects (classic)", HUB)])
    y = lane(cv, y, "Path 2: hub-based project -> Foundry project", "Do you have a hub-based project?", "blue", s2, [c2a, c2b, c2c], flow=st2) + 30

    # ---- path 3: Assistants / classic agents -> new agents
    s3 = simple_strip(Box(330, "Assistants API / classic agents", sub="threads, messages, runs; asst_... ids", theme="gray", fill="soft", dash="dashed", icon="agent", size=19, sub_size=15, min_h=140),
                      "Map tools, create_version(), then conversations and responses",
                      Box(330, "New agents", sub="prompt or hosted agents on the Responses API", theme="green", fill="hatch", icon="agent", size=19, sub_size=15, min_h=140),
                      "green")
    st3 = step_flow("At minimum, four steps (Learn)", [
        "Compare your tools with the agent tool availability table (below) and pick replacements for any that do not carry over",
        "Migrate the agent definition: classic agents or Assistants API path",
        "Replace threads with conversations and runs with responses",
        "Verify state, tool calls, outputs and error handling",
    ], "green", src=[("Migrate to the new agents developer experience", MIG)], h=100)
    c3a = Card(590, "Migration tool", [
        "A migration tool automates Assistants API -> Agents (aka.ms/agent/migrate/tool)",
        "GitHub: microsoft-foundry/foundry-samples, migration folder, v1_to_v2_migration.py",
        "Migrates asst_... assistants including their files and file_search vector stores",
        "Needs Foundry User on the target project",
    ], theme="green", body_size=15, src=[("Migrate to the new agents developer experience", MIG)])
    c3b = Card(590, "Block new classic agents", [
        "Tag MS-AOAI-Feature-Assistants=Disabled on an Azure OpenAI account",
        "Blocks create or update of assistants and classic agents, create thread, create run and similar calls",
        "Other model and inference features stay unchanged; set the tag to Enabled to re-enable",
        "Needs Owner or Contributor on the subscription or resource group",
    ], theme="red", body_size=15, src=[("Disable creation of classic agents", DISABLE)])
    c3c = Card(590, "What else changes", [
        "Threads -> conversations: streams of items, not just messages",
        "Runs -> responses: send input items or a conversation, receive output items; tool-call loops are managed explicitly",
        "Connected Agents and Deep Research are not in the new agents: use the A2A tool, or the Deep Research model with Web Search",
        "New agents are stateful by default, work with any Foundry model, and can be backed by your own Cosmos DB",
    ], theme="blue", body_size=15, src=[("Migrate to the new agents developer experience", MIG)])
    y = lane(cv, y, "Path 3: Assistants API and classic agents -> new agents", "Do you have Assistants or classic agents?", "green", s3, [c3a, c3b, c3c], flow=st3) + 30

    # ---- path 4: Agent Applications -> agent object
    def strip4(cv, x, y):
        bx = Box(300, "Agent", sub="data plane", theme="gray", fill="soft", dash="dashed", size=17, sub_size=14, min_h=64)
        by = Box(300, "Agent Application", sub="control plane; own identity + endpoint", theme="gray", fill="soft", dash="dashed", size=17, sub_size=14, min_h=64)
        bz = Box(300, "Deployment", sub="control plane; start / stop", theme="gray", fill="soft", dash="dashed", size=17, sub_size=14, min_h=64)
        yy = y
        for b in (bx, by, bz):
            b.place(cv, x, yy)
            yy += b.h + 12
        hh = yy - 12 - y
        block_arrow(cv, x + 312, y + hh / 2 - 60, 250, 120, "Create the agent: that is the whole step", th="green", size=16, tip=34)
        nb = x + 312 + 250 + 12
        pw = 1100 - (nb - x)
        with cv.panel(nb, y, w=pw, title="Agent (new object model)", sub="absorbs endpoint, identity and deployment", theme="green", style="solid", fill="soft",
                      pad=14, title_size=20, sub_size=14, min_h=hh) as ap:
            cf = ChipFlow(["id", "name", "versions", "agent_endpoint", "protocol_configuration", "authorization_schemes", "version_selector",
                           "blueprint", "instance_identity", "agent_card"], pw - 28, theme="green", size=14, gap=8, fill="soft")
            cf.place(cv, ap.ix, ap.iy)
        return max(y + hh, ap.bottom)
    n4 = Note(1100, "Before: publishing created a separate Agent Application with its own identity, endpoint and deployment. After: only Agent objects exist; "
                    "'publishing' now means distributing through M365 and Teams. Preview REST gate: Foundry-Features: AgentEndpoints=V1Preview.",
              kind="preview", title="Collapse three objects into one", src=[("Migrate from agent applications", MIGAPP)])
    c4a = Card(590, "What the new model gives every agent", [
        "Every new agent gets its own Entra Agent Blueprint and Agent Identity, and a stable endpoint, from the moment it is created",
        "agent_card surfaces details and capabilities to consumers and A2A",
        "Select an agent version to expose through the stable endpoint; publish that endpoint to M365 and Teams when needed",
    ], theme="green", body_size=15, src=[("Migrate from agent applications", MIGAPP)])
    c4b = Card(590, "Agent types in the transition", [
        "New agent: agent identity is non-null; all new features",
        "Legacy agent: identity is null (shared project identity and blueprint); backfilled with endpoint properties but cannot be published to Teams or M365 via its stable endpoint",
        "! No in-place upgrade yet: create a new agent with the same definition (instructions, tools, model); an upgrade path is planned",
    ], theme="orange", body_size=15, src=[("Migrate from agent applications", MIGAPP)])
    c4c = Card(590, "What keeps working", [
        "Existing Agent Applications keep serving traffic through their endpoints",
        "Agents published to M365 and Teams through Agent Applications keep working",
        "The project endpoint stays available for backward compatibility, though it is no longer the recommended path",
        "Legacy agents stay functional for development and testing",
    ], theme="gray", body_size=15, src=[("Migrate from agent applications", MIGAPP)])
    y = lane(cv, y, "Path 4: Agent Applications -> the new agent object", "Do you publish agents as Agent Applications?", "green", strip4, [c4a, c4b, c4c], notes=[n4]) + 30

    # ---- path 5: GitHub Models / azure-ai-inference -> Foundry Models + openai SDK
    def strip5(cv, x, y):
        a = Box(330, "GitHub Models", sub="retired 2026-07-30", theme="gray", fill="soft", dash="dashed", icon="github", size=18, sub_size=15, min_h=84)
        b = Box(330, "azure-ai-inference", sub="retired 2026-08-26", theme="gray", fill="soft", dash="dashed", icon="python", size=18, sub_size=15, min_h=84)
        a.place(cv, x, y)
        b.place(cv, x, y + a.h + 14)
        hh = a.h + 14 + b.h
        block_arrow(cv, x + 342, y + hh / 2 - 62, 420, 124, "Same inference API shape: change the endpoint and credentials", th="blue", size=17, tip=36)
        c = Box(330, "Foundry Models + the openai package", sub="OpenAI(base_url=...) replaces AzureOpenAI()", theme="blue", fill="hatch", icon="foundry", size=19, sub_size=15)
        c.place(cv, x + 342 + 420 + 12, y, h=hh)
        return y + hh
    c5a = Card(590, "GitHub Models and azure-ai-inference", [
        "GitHub Models retired on 2026-07-30; the inference API shape stays the same: change the endpoint and credentials",
        "Usage is billed to Azure by deployment type; partner models need permission to purchase from Azure Marketplace",
        "azure-ai-inference retired on 2026-08-26: migrate to the openai package",
        "OpenAI() with base_url replaces AzureOpenAI(); Azure-specific code is eliminated",
    ], theme="blue", body_size=15, badge="retiring", src=[("Migrate from GitHub Models", GHM), ("azure-ai-inference to OpenAI SDK", INFER)])
    c5c = Card(1100, "Chat Completions -> Responses API", [
        "Chat Completions stays available for models sold by Azure; new agent features build on the Responses API",
        "Step-by-step guide on Learn (Azure developer docs): migrate from Azure OpenAI Chat Completions to the Responses API",
        "The project endpoint does not route embeddings: use the OpenAI endpoint (/openai/v1) for them",
    ], theme="green", body_size=15, src=[("Azure OpenAI to Responses API", CC2R), ("Foundry SDK overview", SDK)])
    sdk_rows = [
        ["openai", "azure-ai-inference", "retired 2026-08-26"],
        ["OpenAI() with base_url", "AzureOpenAI()", "Azure-specific code eliminated"],
        ["azure-ai-projects 2.x", "azure-ai-projects 1.x", "2.x targets the new portal; 1.x targets the classic portal"],
        ["azure-ai-projects 2.x", "azure-ai-generative", "capabilities merged into the project client"],
        ["azure-ai-projects 2.x", "azure-ai-ml", "for hub-to-project migration scenarios"],
        ["azure-ai-projects (remote) + azure-ai-evaluation (local)", "azure-ai-evaluation (standalone)", "remote evals via the project client; local evals unchanged"],
        ["azure-search-documents (via project connections)", "azure-search-documents", "separate package, discoverable through the project client"],
    ]
    t5 = Table([("Use", 400), ("Instead of", 300), "Notes"], sdk_rows, w=1198, theme="blue", size=14, head_size=15, title="SDK mapping (Learn: migrate from the classic portal)", title_size=20)
    y = lane(cv, y, "Path 5: GitHub Models and azure-ai-inference -> Foundry Models and the OpenAI SDK", "Do you call models through GitHub Models or azure-ai-inference?", "blue",
             strip5, [c5a, t5], notes=[c5c]) + 0
    return y


# ================================================================================================ 2. parity, portal map, tool availability
def s_parity(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "What lives where: new portal, classic portal, or both", w=W,
                   sub="Learn: feature comparison (portal navigation page) and 'Unsupported at GA' (portal GA overview)  |  as of 2026-11-03")
    y += 96
    c = Card(1020, "Classic only: migration needed, or unsupported in the new portal", [
        "# Migration required",
        "Azure OpenAI resources: upgrade to a Foundry resource",
        "Hub-based projects: switch the toggle to classic, or migrate to Foundry projects",
        "# Unsupported at GA (needs classic)",
        "Assistant creation and authoring; standalone Azure OpenAI or single-service resources",
        "Audio playground; AI service fine-tuning (Speech or Vision custom model training); Content Understanding",
        "Prebuilt prompts in the video playground; adding data directly from the Data tab; AOAI evaluation files as datasets",
        "Classic docs also keep prompt flow and hub managed-compute deployments",
    ], theme="gray", dash="dashed", badge="classic", icon="foundry", body_size=16, src=[("Portal general availability overview", GA), ("Foundry (classic) docs", CLASSIC)])
    a = Table([("In both portals", 300), ("Classic", 90), ("New", 90), "Notes"], [
        ["Foundry projects", CHECK, CHECK, ""],
        ["Chat completions", CHECK, CHECK, ""],
        ["Fine-tuning", CHECK, CHECK, ""],
        ["Evaluations", CHECK, CHECK, "Enhanced in the new portal"],
        ["Model catalog", CHECK, CHECK, "Expanded in the new portal"],
    ], w=800, theme="gray", size=15, head_size=16, align=["left", "center", "center", "left"])
    b = Card(1020, "New portal only", [
        "Responses API (GA); Agents v2 on the Responses API (GA)",
        "Tool catalog, 1,400+ tools (GA; check each tool's own label for GA or Preview)",
        "Hosted agents (GA); agent publishing to M365 and Teams (GA)",
        "A2A protocol: v1.0 GA, v0.3 preview",
        "Foundry IQ: Preview in this table, partial GA in the GA overview",
        "Agent memory (preview); Foundry Control Plane (preview)",
        "Multi-agent workflows (preview; retiring 2026-12-01)",
    ], theme="green", icon="agent", badge="new", body_size=16, src=[("Migrate from the Foundry (classic) portal", NAV), ("Portal general availability overview", GA)])
    hh = max(c.h, b.h)
    c.place(cv, 0, y, h=hh)
    a.place(cv, c.right + 80, y)
    cv.text(a.x, a.bottom + 8, "Learn: Migrate from the Foundry (classic) portal (feature comparison)", size=12, color=LINK, link=NAV)
    b.place(cv, a.right + 80, y, h=hh)
    y += hh + 50

    LW = 1500
    secs = Table([("Section", 150), ("Scope", 330), "What you find there"], [
        [("Home", "blue"), "Selected project", "Project overview and quick actions"],
        [("Discover", "blue"), "Selected project", "Model catalog and model benchmarks"],
        [("Build", "blue"), "Selected project", "Create: Agents, Models, Services, Tools, Knowledge, Memory, Guardrails, Data. Optimize: Evaluations, Fine-tune"],
        [("Operate", "blue"), "All projects", "Compliance, fleet health, tracing, assets"],
        [("Manage", "blue"), "Selected project and its resource", "Quota, AI Gateway, resource details, project details"],
        [("Docs", "blue"), "n/a", "Documentation links"],
    ], w=LW, theme="blue", size=15, title="The new portal: six top-level sections (classic had one left pane plus Management center)", title_size=20)
    secs.place(cv, 0, y)
    moved = Table([("Task", 300), ("Classic portal location", 440), "New portal location"], [
        ["View model deployments", "Models + endpoints (left pane)", "Build > Models"],
        ["Open a playground", "Playgrounds (left pane)", "Build > Models > select a model"],
        ["Build agents", "Agents (left pane)", "Build > Agents"],
        ["Browse the model catalog", "Model catalog (left pane)", "Discover > Model catalog"],
        ["View evaluations", "Evaluation (left pane)", "Build > Evaluations"],
        ["Fine-tune a model", "Fine-tuning (left pane)", "Build > Fine-tuning"],
        ["Tracing and monitoring", "Tracing (left pane)", "Operate > Tracing"],
        ["Manage quotas", "Management center > Quota", "Manage > Quota"],
        ["Manage users and permissions", "Management center > Users", "Manage > Project details > Users"],
        ["View all projects and resources", "Management center > All resources", "Project name dropdown > View all projects"],
        ["Connected resources", "Management center > Connected resources", "Manage > Project details > Connected resources"],
        ["Guardrails and content filters", "Guardrails + controls (left pane)", "Operate > Compliance"],
    ], w=LW, theme="gray", size=15, title="Where things moved", title_size=20, first_col_theme="gray")
    moved.place(cv, 0, secs.bottom + 36)
    cv.text(0, moved.bottom + 8, "Learn: Migrate from the Foundry (classic) portal", size=12, color=LINK, link=NAV)
    t = cv.text(0, moved.bottom + 30, "Switch with the New Foundry toggle in the top banner (it preserves your project context). The new portal shows only Foundry projects.",
                size=14, color=MUTED)
    left_bottom = t.bottom

    TX = LW + 70
    TW = W - TX
    G, P, N, R = ("GA", "green"), ("Preview", "orange"), ("No", "gray"), ("No", "red")
    tool_rows = [
        ["Agent to Agent (A2A)", N, G, "a2a_preview remains in public preview"],
        ["Azure AI Search", G, G, ""],
        ["Azure Functions", G, R, "Docs disagree: a tool page exists (updated 2026-08-24)"],
        ["Browser Automation", P, P, "Docs disagree: the tool page says GA (2026-11-02)"],
        ["Code Interpreter", G, G, ""],
        ["Computer Use", P, P, ""],
        ["Connected Agents", P, R, "Recommended: the A2A tool"],
        ["Deep Research", P, R, "Recommended: Deep Research model with Web Search"],
        ["Fabric Data Agent", P, P, "Deprecation 2026-11-06 -> Fabric IQ tool"],
        ["File Search", G, G, ""],
        ["Function", G, G, ""],
        ["Grounding with Bing Search", G, G, ""],
        ["Grounding with Bing Custom Search", P, P, ""],
        ["Image Generation", N, P, ""],
        ["MCP", P, G, ""],
        ["OpenAPI", G, G, ""],
        ["SharePoint Grounding", P, P, ""],
        ["Web Search", N, G, ""],
    ]
    rows = []
    for name, c1, c2, note in tool_rows:
        rows.append([name, dict(text=c1[0], theme=c1[1], align="center"), dict(text=c2[0], theme=c2[1], align="center"), note])
    tt = Table([("Tool", 270), ("Classic", 100), ("New", 100), "Note"], rows, w=1000, theme="green", size=15,
               title="Agent tool availability: classic agents -> new agents", title_size=20, align=["left", "center", "center", "left"])
    tt.place(cv, TX, y)
    cv.text(TX, tt.bottom + 8, "Learn: Migrate to the new agents developer experience (agent tool availability)", size=12, color=LINK, link=MIG)
    dx, dw = TX + tt.w + 30, TW - tt.w - 30
    d1 = Card(dw, "New in the new agents", ["A2A: GA (a2a_preview stays in preview)", "Web Search: GA", "Image Generation: preview", "MCP: preview -> GA"],
              theme="green", body_size=15, src=[("Agent tool availability", MIG)])
    d2 = Card(dw, "Not carried over", ["Connected Agents: use the A2A tool", "Deep Research: use the Deep Research model with the Web Search tool",
                                       "Azure Functions: 'No' in the migration table, yet a tool page exists - docs disagree"],
              theme="red", body_size=15, src=[("Agent tool availability", MIG)])
    d3 = Card(dw, "Deprecating", ["Fabric Data Agent: scheduled for deprecation 2026-11-06 -> use the Fabric IQ tool"], theme="orange", body_size=15, badge="retiring",
              src=[("Fabric data agent tool", FABRIC)])
    col(cv, dx, y + 38, [d1, d2, d3], gap=22)
    return max(left_bottom, tt.bottom + 30)


# ================================================================================================ 3. notes
def s_notes(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Gotchas and where the docs disagree", w=W)
    y += 64
    nw = 973
    notes = [
        Note(nw, "Browser Automation: the tool page (2026-11-02) and the DevBlog say GA; the migration table and capability reference still say preview. Azure Functions: "
                 "the migration table says not in the new agents, yet a tool page exists. Foundry IQ: Preview in the portal-migration table, partial GA in the GA overview. "
                 "Check each feature's own page and label.", kind="warn", title="Docs disagree: tool and feature status",
             src=[("Migrate to the new agents experience", MIG), ("Portal GA overview", GA)]),
        Note(nw, "The migration page still words 2026-08-26 as 'Assistants API sunsets' (now past), while the portal GA overview says existing assistants and v1 agents "
                 "are not supported in the new portal 'until assistant upgrade is available'. Treat classic Assistants as sunset or legacy and plan the move.",
             kind="warn", title="Docs disagree: is the Assistants API gone?", src=[("Migrate from the classic portal", NAV), ("Portal GA overview", GA)]),
        Note(nw, "Resource upgrade changes what a role can do: Cognitive Services User unlocks all Foundry features on an upgraded resource, while Cognitive Services OpenAI User stays "
                 "OpenAI-only. Review wildcard role assignments and Azure Policy before an auto-upgrade lands.", kind="gotcha", title="Governance after an upgrade",
             src=[("Manage automatic upgrades", UPGA)]),
        Note(nw, "Hub-based projects and standalone Azure OpenAI resources are invisible in the new portal. If projects seem to be missing after switching, toggle New Foundry off "
                 "or migrate them to Foundry projects.", kind="info", title="Where did my projects go?", src=[("Migrate from the classic portal", NAV)]),
        Note(nw, "Preview surfaces in these paths: the foundryAutoUpgrade property (API 2026-01-15-preview) and the agent-endpoint REST gate "
                 "(Foundry-Features: AgentEndpoints=V1Preview). Pin and test before relying on them in automation.", kind="preview", title="Preview surfaces",
             src=[("Manage automatic upgrades", UPGA), ("Migrate from agent applications", MIGAPP)]),
        Note(nw, "azure-ai-projects 2.x targets the new portal and 1.x targets classic; mixing a 2.x sample with a 1.x setup (or the reverse) causes errors. "
                 "Prerequisites for the SDK migration: Python 3.10+ or .NET 8+. Match the endpoint too: old multi-endpoint URLs no longer resolve - use the single project endpoint.",
             kind="tip", title="Match the SDK major and the endpoint", src=[("Migrate from the classic portal", NAV), ("Foundry SDK overview", SDK)]),
    ]
    bottom = y
    for i in range(0, len(notes), 3):
        r = notes[i:i + 3]
        hmax = max(n.h for n in r)
        for j, n in enumerate(r):
            n.place(cv, j * (nw + 40), bottom, h=hmax)
        bottom += hmax + 30
    return bottom - 30
