"""Where to start with Microsoft Foundry: the 'Start with your goal' decision tree, the declarative -> full-code spectrum
(single model call, ephemeral agent, prompt agent, hosted agent), the five-step path for new developers, the quickstart shelf and a
persona -> entry-point map (as of 2026-11-03)."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="where-to-start", title="Where to start with Microsoft Foundry", section="1", group="Overview", order=3,
    description="Start with your goal: a decision tree from 'I want to...' to the right first page, the declarative -> full-code spectrum "
                "(model call, prompt agent, hosted agent), the five-step path for new developers and a persona -> entry-point map.",
    tags=["getting-started", "decision-tree", "prompt-agent", "hosted-agent", "personas"],
)

W = 3000

# ------------------------------------------------------------------------------------------------ sources
CAP = learn("concepts/capabilities")
CAPREF = learn("concepts/capability-reference")
WHAT = learn("what-is-foundry")
WHAT_BUILD = learn("what-is-foundry#start-by-building-an-agent")
AGENTS = learn("agents/overview")
PROMPT = learn("agents/concepts/prompt-agents")
HOSTED = learn("agents/concepts/hosted-agents")
GET_CODE = learn("quickstarts/get-started-code")
QS = learn("quickstarts/quickstarts")
HOSTED_QS = learn("agents/quickstarts/quickstart-hosted-agent")
PROMPT_QS = learn("agents/quickstarts/prompt-agent")
VOICE_QS = learn("agents/quickstarts/prompt-voice-agent")
RESP_QS = learn("agents/quickstarts/responses-api")
OWN_CODE_QS = learn("agents/quickstarts/quickstart-deploy-own-code")
FRAMEWORKS = learn("how-to/develop/framework-hosted-agents")
EVAL = learn("how-to/evaluate-generative-ai-app")
OBS = learn("concepts/observability")
CICD = learn("agents/quickstarts/set-up-cicd-hosted-agent")
CP = learn("control-plane/overview")
INSTALL = learn("how-to/develop/install-cli-sdk")
MODELS = learn("concepts/foundry-models-overview")
TOOLBOX = learn("agents/concepts/toolbox-overview")
IQ = learn("agents/concepts/what-is-foundry-iq")
MEMORY = learn("agents/concepts/what-is-memory")
WORKFLOW = learn("agents/concepts/workflow")
SDK = learn("how-to/develop/sdk-overview")
VSCODE = learn("how-to/develop/get-started-projects-visual-studio-code")
SKILL = learn("how-to/develop/use-microsoft-foundry-skill")
LANGCHAIN = learn("how-to/develop/langchain")
REDTEAM = learn("concepts/ai-red-teaming-agent")
GUARD = learn("guardrails/guardrails-overview")
FINETUNE = learn("openai/how-to/fine-tuning")
AZD = learn("agents/concepts/cli-agent-development")
GA = learn("concepts/general-availability")
PUBLISH = learn("agents/how-to/publish-copilot")
HARNESS = learn("agents/how-to/use-tools-skills-copilot-harness")
AUTOPILOT = learn("agents/concepts/autopilot-overview")


# ================================================================================================ local helpers
def sticker(cv, x, y, text, th="red", size=14):
    """Small solid pill drawn over a card edge (not registered, so it does not trigger overlap warnings)."""
    t = theme(th)
    tw = metrics.line_width(text, size) + 20
    with cv.group():
        cv.rect(x, y, tw, size * 1.25 + 8, stroke=t.stroke, fill=t.fill, style="solid", sw=2, rough=0)
        cv.text(x + 10, y + 4, text, size=size, color=t.deep)
    return tw


def block_arrow(cv, x, y, w, h, text, *, th="blue", size=17, tip=40, notch=False, sub=None, sub_size=14):
    """Chevron-style block arrow with centred text; notch=True gives the 'follows another chevron' shape."""
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
            cv.text(x + pad_l, ty + len(lines) * size * lh + 3, "\n".join(sub_lines), size=sub_size, color=MUTED, align="center", w=tw)
    cv.register("chevron", x, y, w, h)


def learn_line(cv, x, y, items, size=12, gap=24):
    """Row of clickable 'Learn: ...' links; returns the bottom y."""
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=size, color=LINK, link=url)
        cx += t.w + gap
    return y + size * metrics.line_ratio()


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Where to start with Microsoft Foundry",
                                "Start with your goal: the shortest path from what you want to do to the right first page  |  as of 2026-11-03", w=W)
    y = bottom + 26
    legend(cv, 0, y, [("Models", "blue"), ("Agents", "green"), ("Tools and tooling", "orange"), ("Evaluation and tracing", "violet"),
                      ("Operate and govern", "grape"), ("Security and safety", "pink"), ("Environment and neutral", "gray")])
    y += 54
    y = s_tree(cv, y) + 90
    y = s_spectrum(cv, y) + 90
    y = s_path(cv, y) + 90
    y = s_shelf(cv, y) + 90
    y = s_personas(cv, y) + 70
    sources(cv, 0, y, [
        ("Microsoft Foundry product and capability map (Start with your goal)", CAP),
        ("Microsoft Foundry capability reference", CAPREF),
        ("What is Microsoft Foundry? (Start by building an agent)", WHAT_BUILD),
        ("Agents in Microsoft Foundry (Choose how to build)", AGENTS),
        ("Prompt agents", PROMPT),
        ("Hosted agents (protocols, sessions, compute)", HOSTED),
        ("Microsoft Foundry quickstarts", QS),
        ("Frameworks for hosted agents", FRAMEWORKS),
        ("Set up your developer environment (CLI, SDK, Dev Pack)", INSTALL),
        ("Evaluate generative AI apps", EVAL),
        ("Foundry Observability", OBS),
        ("Set up CI/CD for hosted agents", CICD),
        ("Foundry control plane overview", CP),
        ("Foundry Models overview", MODELS),
    ], w=W, cols=3)


# ================================================================================================ 1. decision tree
GOALS = [
    dict(goal="Send a prompt to a model, with no agent or tools", th="blue", icon="openai", start="Build with models and agents", kind="Quickstart",
         src=[("Build with models and agents", GET_CODE)],
         why="The shortest path to a working call. Add an agent later only if you need tools or orchestration."),
    dict(goal="Build my first agent", th="green", icon="agent", start="Choose how to build", kind="Overview: prompt agent or hosted agent",
         src=[("What is Microsoft Foundry? (Start by building an agent)", WHAT_BUILD)],
         why="Decides prompt agent versus hosted agent before you invest in either. That choice shapes everything after it."),
    dict(goal="Host an agent I already wrote", th="green", icon="container-apps", start="Deploy a hosted agent", kind="Quickstart",
         src=[("Deploy a hosted agent", HOSTED_QS)],
         why="Runs your existing code or container with a managed endpoint, scaling and identity."),
    dict(goal="Use an open-source framework with Foundry", th="green", icon="langgraph", start="Frameworks for hosted agents", kind="How-to",
         src=[("Frameworks for hosted agents", FRAMEWORKS)],
         why="Shows how LangGraph, Microsoft Agent Framework and Semantic Kernel map onto Foundry hosting."),
    dict(goal="Evaluate agent quality", th="violet", icon="metrics", start="Evaluate generative AI apps", kind="How-to",
         src=[("Evaluate generative AI apps", EVAL)],
         why="Establishes a baseline score first, so later changes are measurable rather than anecdotal."),
    dict(goal="Add observability", th="violet", icon="app-insights", start="Foundry Observability", kind="Concept",
         src=[("Foundry Observability", OBS)],
         why="Tracing, monitoring and evaluation share one data model, so set them up together."),
    dict(goal="Deploy and operate an application", th="grape", icon="devops", start="Set up CI/CD for agents", kind="Quickstart",
         src=[("Set up CI/CD for agents", CICD), ("Foundry control plane (fleet-wide governance)", CP)],
         why="Gets a repeatable release path before you scale. For fleet-wide governance, see the control plane."),
    dict(goal="Not sure what exists yet", th="gray", icon="learn", start="Product and capability map", kind="Concept: the page this map comes from",
         src=[("Product and capability map", CAP), ("Capability reference (everything in Foundry)", CAPREF)],
         why="Maps goals to starting points, compares the major products, and links to the exhaustive capability reference."),
]


def s_tree(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Start with your goal", w=W,
                   sub="Learn's 'Start with your goal' table (Microsoft Foundry product and capability map, page updated 2026-10-08) drawn as a decision map  |  "
                       "follow the branch closest to what you are trying to do")
    top = y + 100
    RW_, GX, GW, CX, CW, BX, BW = 380, 500, 640, 1260, 760, 2065, 935
    rows = []
    for g in GOALS:
        dashed = g["th"] == "gray"
        goal = Box(GW, g["goal"], theme=g["th"], fill="soft", icon=g["icon"], icon_pos="left", icon_size=36, size=19, min_h=88,
                   dash="dashed" if dashed else "solid", sw=3)
        card = Card(CW, g["start"], [], subtitle=g["kind"], theme=g["th"], fill="hatch", dash="dashed" if dashed else "solid", title_size=22,
                    sub_size=14, pad=14, src=g["src"])
        why = Bubble(BW, g["why"], theme="gray", size=16, tail="left", pad=13)
        rows.append((goal, card, why, max(goal.h, card.h, why.h)))
    rh = max(r[3] for r in rows)
    gap = 22
    total = len(rows) * rh + (len(rows) - 1) * gap
    root = Box(RW_, "What do you want to do?", h=260, theme="ink", shape="ellipse", fill="hatch", size=26, icon="foundry", icon_size=44, icon_pos="top")
    root.place(cv, 0, top + total / 2 - root.h / 2)
    for i, (goal, card, why, _) in enumerate(rows):
        cy = top + i * (rh + gap) + rh / 2
        goal.place(cv, GX, cy - goal.h / 2)
        card.place(cv, CX, cy - card.h / 2)
        why.place(cv, BX, cy - why.h / 2)
        connect(cv, root, goal, a_side="right", b_side="left", route="elbow", bend=0.4, sw=3, gap=8, color="#495057")
        th = GOALS[i]["th"]
        arrow(cv, [(goal.right + 8, cy), (card.x - 8, cy)], sw=3, end_head="arrow", color=theme(th).stroke, label="start here", label_size=15,
              label_color=theme(th).deep)
        sticker(cv, card.right - 118, card.y - 13, "START HERE", th, size=13)
    cv.text(0, top + total + 18, "The Why column quotes Learn in condensed form. 'Start here' links go to Microsoft Learn pages under /azure/foundry/.", size=14, color=MUTED)
    return top + total + 44


# ================================================================================================ 2. spectrum
def s_spectrum(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "From a single model call to your own code", w=W,
                   sub="Learn: foundry meets you anywhere on the spectrum from declarative to full code  |  start simple and move up only when your needs grow")
    LBL, CW = 250, (W - 250) / 4
    BW = CW - 40
    STEP, BH = 118, 150
    T = y + 112

    rungs = [
        dict(n=1, title="Single model call", sub="Your code calls the model endpoint", th="blue", icon="openai", dash="solid"),
        dict(n=2, title="Ephemeral agent", sub="Responses API: the agent logic lives in your app", th="green", icon="code", dash="dashed"),
        dict(n=3, title="Prompt agent", sub="Declarative: Foundry runs it, the least to manage", th="green", icon="agent", dash="solid"),
        dict(n=4, title="Hosted agent", sub="Full code: Foundry runs your code, the most control", th="green", icon="container-apps", dash="solid"),
    ]
    boxes = []
    for i, r in enumerate(rungs):
        b = Box(BW, r["title"], sub=r["sub"], theme=r["th"], fill="hatch", dash=r["dash"], icon=r["icon"], icon_pos="left", icon_size=46, size=24, sub_size=15,
                min_h=BH, sw=3)
        b.place(cv, LBL + i * CW + 20, T + (3 - i) * STEP)
        boxes.append(b)
        numbered(cv, b.x + 4, b.y + 4, r["n"], theme=r["th"], d=44, size=24)
    for i in range(3):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", route="elbow", sw=3.5, gap=3, color=theme("green").stroke)
    sticker(cv, boxes[2].right - 196, boxes[2].y - 13, "LEAST TO MANAGE", "green", size=14)
    sticker(cv, boxes[3].right - 160, boxes[3].y - 13, "MOST CONTROL", "green", size=14)

    # ---- variants and caveats in the free space under the higher steps
    under3 = boxes[2].bottom + 18
    vw = (BW - 16) / 2
    v3b = Card(vw, "3b  Voice-based prompt agent", [
        "Speaks and listens in real time, connected over a WebSocket",
        "Foundry manages the voice orchestration (Voice Live)",
        "Text only? Use a plain prompt agent",
    ], theme="green", badge="preview", dash="dashed", title_size=17, body_size=14, pad=12, src=[("Voice-based prompt agent quickstart", VOICE_QS)])
    v3c = Card(vw, "3c  + Copilot harness", [
        "Optional runtime, selected only when you create the agent",
        "Adds file-system, shell, web-fetch and subagent tools",
        "Still a prompt agent, called through Responses; a first-class conversation is needed for every response",
    ], theme="orange", badge="preview", dash="dashed", title_size=17, body_size=14, pad=12, src=[("Use the Copilot harness with prompt agents", HARNESS)])
    hh = max(v3b.h, v3c.h)
    v3b.place(cv, boxes[2].x, under3, h=hh)
    v3c.place(cv, boxes[2].x + vw + 16, under3, h=hh)
    v5 = Card(BW, "5  Autopilot (an edge case)", [
        "A hosted agent published as a blueprint; each hired instance gets its own agent identity and an agent user account",
        "The account gives it email, calendar, OneDrive and Teams presence, and lets it act as itself in Microsoft 365",
        "You build the blueprint, not the autopilot; only hosted agents can be blueprints",
        "Preview: needs the Microsoft Frontier program and Agent 365 Frontier licence",
    ], theme="orange", badge="preview", dash="dashed", title_size=18, body_size=14, pad=13, src=[("Autopilots", AUTOPILOT)])
    v5.place(cv, boxes[3].x, boxes[3].bottom + 18)
    n2 = Note(BW, "The definition can change on every request. It cannot select the Copilot harness or run the prompt-agent optimizer: both need a saved prompt agent version.",
              kind="info", title="Ephemeral caveat", size=14, title_size=16, pad=10, src=[("Prompt agents", PROMPT)])
    n2.place(cv, boxes[1].x, boxes[1].bottom + 18)

    # ---- left rail: the up arrow
    cv.text(0, T, "You can start declarative and move to code as your needs grow", size=17, color=MUTED, wrap=LBL - 20)
    ytab = T + 3 * STEP + BH + 40
    arrow(cv, [(110, ytab - 24), (110, T + 120)], sw=6, end_head="arrow", color=theme("green").stroke, dash="solid")
    cv.text(0, ytab - 20, "start here", size=15, color=theme("green").deep)

    # ---- comparison table aligned with the steps
    cols = [("", LBL)] + [(h, CW) for h in ("1  Single model call", "2  Ephemeral agent (Responses API)", "3  Prompt agent", "4  Hosted agent")]
    G = lambda t: (t, "gray")
    rows = [
        [G("What it is"),
         "Send prompts to a deployed model (or an instant-access model, preview); no tools, no orchestration",
         "The definition (model, instructions, tools) lives in your app code; each call assembles it and runs it on the Responses API. No persisted Foundry agent resource",
         "Declarative: instructions + model + tools (+ skills, toolboxes). A versioned resource in a project, invoked through the Responses API",
         "Your code or framework (Agent Framework, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, Copilot SDK, custom) shipped as a container image or a .zip of source; Foundry builds the image from a .zip"],
        [G("Who runs it, what you manage"),
         "You call the model endpoint and write everything around it",
         "Your process hosts the logic. Foundry supplies catalog models, platform tools, project data, On-Behalf-Of auth, tracing and governance through the project endpoint",
         "Nothing to run: no code, container or compute. Foundry runs the agent",
         "Foundry runs it: managed endpoint, per-session VM-isolated sandbox, dedicated Entra agent identity, session-state persistence, observability. You own the code that runs inside the sandbox"],
        [G("Pick it when"),
         "You only need text, image or other generation from a model",
         "You already run agent code elsewhere and want the definition to version with the app",
         "Fastest start; internal tools; production agents without custom orchestration",
         "You bring your own code; need custom protocols (webhooks, AG-UI, voice) or control over CPU and memory"],
        [G("Boundary: when to go further"),
         "Need tools or orchestration? Use an agent",
         "Need the Copilot harness or the optimizer? Save a prompt agent version",
         "Need custom code, containers or protocols? Use a hosted agent",
         "Billed per-call inference + tool usage + container compute; hosted agents support Python and C#"],
    ]
    tbl = Table(cols, rows, w=W, theme="green", size=15, head_size=18, first_col_theme="gray", pad_y=8)
    tbl.place(cv, 0, ytab)
    ly = tbl.bottom + 8
    for i, (lab, url) in enumerate([("Build with models and agents", GET_CODE), ("Quickstart: Build agents using the Responses API", RESP_QS),
                                    ("Quickstart: Create a prompt agent", PROMPT_QS), ("Quickstart: Deploy a hosted agent", HOSTED_QS)]):
        cv.text(LBL + i * CW + 12, ly, f"Learn: {lab}", size=12, color=LINK, link=url)
    ly += 24

    # ---- two small decision trees
    top = ly + 36
    LW_, RW_, GAP = 1910, W - 1910 - 60, 60
    ph = 0
    with cv.panel(0, top, w=LW_, title="Which agent path?", sub="Our reading of Learn's 'Choose how to build': a yes drops to the answer, a no moves right",
                  theme="green", style="dashed", fill="soft", pad=24, title_size=24, sub_size=15) as lp:
        cw_, g_ = 312, 75
        qs = [("Only prompts to a model: no tools, no orchestration?", "Single model call", "Start with the quickstart: add an agent later", "blue", "openai", "solid"),
              ("Already run agent code elsewhere?", "Call the Responses API", "An ephemeral agent: no agent resource to manage", "green", "code", "dashed"),
              ("Want full control in Foundry: your own code, container or protocols?", "Hosted agent", "Bring your own code and framework; Foundry runs it", "green", "container-apps", "solid"),
              ("Want a real-time voice experience without hosting its orchestration?", "Voice-based prompt agent", "Preview: configure it, connect over Voice Live", "green", "speech", "dashed")]
        ds = []
        for i, (q, a, asub, th, ic, dash) in enumerate(qs):
            d = Box(cw_, q, h=170, theme="yellow", shape="diamond", fill="soft", size=15, sw=2.5)
            d.place(cv, lp.ix + i * (cw_ + g_), lp.iy + 10)
            ds.append(d)
            ans = Box(cw_, a, sub=asub, theme=th, fill="hatch", dash=dash, icon=ic, icon_pos="left", icon_size=30, size=18, sub_size=14, min_h=108)
            ans.place(cv, d.x, d.bottom + 76)
            connect(cv, d, ans, a_side="bottom", b_side="top", label="yes", label_size=16, sw=3, gap=6)
        last = Box(cw_, "Prompt agent", sub="The least to manage for text: instructions, model, tools", theme="green", fill="hatch", icon="agent", icon_pos="left", icon_size=30,
                   size=20, sub_size=14, min_h=108)
        last.place(cv, lp.ix + 4 * (cw_ + g_), ds[0].y + (170 - last.h) / 2)
        for i in range(3):
            connect(cv, ds[i], ds[i + 1], a_side="right", b_side="left", label="no", label_size=16, sw=3, gap=6)
        connect(cv, ds[3], last, a_side="right", b_side="left", label="no", label_size=16, sw=3, gap=6)
        learn_line(cv, lp.ix, ds[0].bottom + 76 + 108 + 14, [("Agents in Microsoft Foundry (Choose how to build)", AGENTS)])
    with cv.panel(LW_ + GAP, top, w=RW_, title="Hosted agent: which protocol?", sub="a yes drops to the answer; an agent can expose several protocols",
                  theme="green", style="dashed", fill="soft", pad=24, title_size=24, sub_size=15) as rp:
        cw2, g2 = 290, 60
        d1 = Box(cw2, "Chat-style conversation?", h=150, theme="yellow", shape="diamond", fill="soft", size=16, sw=2.5)
        d1.place(cv, rp.ix, rp.iy + 10)
        d2 = Box(cw2, "Real-time voice or two-way streaming?", h=150, theme="yellow", shape="diamond", fill="soft", size=16, sw=2.5)
        d2.place(cv, rp.ix + cw2 + g2, rp.iy + 10)
        a1 = Box(cw2, "Responses", sub="Platform manages history, streaming and background runs", theme="green", fill="hatch", size=19, sub_size=14, min_h=108)
        a1.place(cv, d1.x, d1.bottom + 60)
        a2 = Box(cw2, "Invocations (WebSocket)", sub="Bidirectional streaming on one connection (invocations_ws)", theme="green", fill="hatch", size=19, sub_size=14, min_h=108)
        a2.place(cv, d2.x, d2.bottom + 60)
        a3 = Box(cw2, "Invocations", sub="Webhooks, batch work, custom payloads, AG-UI: JSON in, JSON out", theme="green", fill="hatch", size=19, sub_size=14, min_h=108)
        a3.place(cv, rp.ix + 2 * (cw2 + g2), d2.y + (150 - a3.h) / 2)
        connect(cv, d1, a1, a_side="bottom", b_side="top", label="yes", label_size=16, sw=3, gap=6)
        connect(cv, d2, a2, a_side="bottom", b_side="top", label="yes", label_size=16, sw=3, gap=6)
        connect(cv, d1, d2, a_side="right", b_side="left", label="no", label_size=16, sw=3, gap=6)
        connect(cv, d2, a3, a_side="right", b_side="left", label="no", label_size=16, sw=3, gap=6)
        ny = max(a1.bottom, a2.bottom, a3.bottom) + 22
        nt1 = Note((3 * cw2 + 2 * g2 - 20) / 2, "Published to Teams or Microsoft 365: Responses + Activity, bridged automatically. A2A (agent-to-agent delegation) is another protocol: v1.0 GA, v0.3 preview.",
                   kind="info", size=14, title_size=16, pad=10)
        nt2 = Note((3 * cw2 + 2 * g2 - 20) / 2, "Not sure? Start with Responses. A hosted agent can support several protocols at once, so the choice is not permanent.", kind="tip",
                   size=14, title_size=16, pad=10, src=[("Hosted agents", HOSTED)])
        hh2 = max(nt1.h, nt2.h)
        nt1.place(cv, rp.ix, ny, h=hh2)
        nt2.place(cv, rp.ix + nt1.w + 20, ny, h=hh2)
    # equalise panel heights (cosmetic): draw nothing, just return the lower edge
    return max(lp.bottom, rp.bottom)


# ================================================================================================ 3. path for new developers
def s_path(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Recommended path for new developers", w=W,
                   sub="Learn: What is Microsoft Foundry? - five steps from zero to a working integration, then what to do before you ship")
    cw, gap = 560, 50
    top = y + 104
    steps = [
        ("Make your first model call", "blue", "openai", ["Set up your environment and send a prompt", "No tools or orchestration yet: add an agent later only if you need them"],
         [("Build with models and agents", GET_CODE)]),
        ("Set up your developer environment", "gray", "code", ["Install the CLI and SDK so you can build in code",
                                                                 "The Foundry Dev Pack (preview) installs azd, the Foundry Skill and, when VS Code is present, the Foundry Toolkit with one command"],
         [("Set up your developer environment", INSTALL)]),
        ("Choose a model", "blue", "cubes", ["Browse the catalog and compare options", "More than 10,000 models from Microsoft, OpenAI, Anthropic, Meta and others"],
         [("Foundry Models overview", MODELS)]),
        ("Build your first agent", "green", "agent", ["Start with a prompt agent", "Go straight to a hosted agent if you want to bring your own code"],
         [("Create a prompt agent", PROMPT_QS), ("Deploy a hosted agent", HOSTED_QS)]),
        ("Add tools and knowledge", "orange", "toolbox-icon", ["Start with the Toolbox: the recommended way to add tools to an agent", "Then retrieval (Foundry IQ) and memory (preview)"],
         [("Toolbox overview", TOOLBOX), ("Foundry IQ", IQ)]),
    ]
    cards = []
    for i, (title, th, ic, body, src) in enumerate(steps):
        cards.append(Card(cw, title, body, theme=th, icon=ic, src=src, title_size=21, body_size=16, pad=16))
    ch = max(c.h for c in cards)
    cy = top + 64 + 34
    circles = []
    for i, c in enumerate(cards):
        x = i * (cw + gap)
        c.place(cv, x, cy, h=ch)
        circles.append((x + cw / 2, top + 32))
    for i in range(4):
        arrow(cv, [(circles[i][0] + 40, top + 32), (circles[i + 1][0] - 40, top + 32)], sw=4, end_head="arrow", color="#495057", dash="dashed")
    for i, ((cx, cyy), (title, th, *_), c) in enumerate(zip(circles, steps, cards), 1):
        numbered(cv, cx, cyy, i, theme=th, d=64, size=32)
        cv.line((cx, cyy + 32), (cx, c.y), stroke=theme(th).stroke, sw=2.5)
    by = cy + ch + 56
    t_before = cv.text(0, by, "Before you ship", size=26, color=INK)
    cv.text(t_before.w + 24, by + 8, "evaluate, trace, gate, publish, govern  |  Learn: Evaluate generative AI apps, Foundry Observability, CI/CD for agents, Publishing, Foundry control plane",
            size=15, color=MUTED)
    fy = by + 48
    fcw, fg = (W - 4 * 10) / 5, 10
    flow = [
        ("Evaluate", "Set a baseline score first, so later changes are measurable", "violet", EVAL, "Evaluate generative AI apps"),
        ("Trace", "Tracing, monitoring and evaluation share one data model", "violet", OBS, "Foundry Observability"),
        ("Gate in CI/CD", "A repeatable release path before you scale", "grape", CICD, "Set up CI/CD for agents"),
        ("Publish", "Stable endpoints; share through Teams, Microsoft Copilot and A2A", "green", PUBLISH, "Publish an agent"),
        ("Govern", "Control plane: policy and oversight across projects", "grape", CP, "Foundry control plane overview"),
    ]
    for i, (t, sub, th, url, lab) in enumerate(flow):
        sx = i * (fcw + fg)
        block_arrow(cv, sx, fy, fcw, 124, t, th=th, size=24, tip=34, notch=i > 0, sub=sub, sub_size=15)
        cv.text(sx + (46 if i else 14), fy + 132, f"Learn: {lab}", size=12, color=LINK, link=url)
    return fy + 160


# ================================================================================================ 4. quickstart shelf + gotchas
def s_shelf(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "The quickstart shelf and a few things to know first", w=W,
                   sub="Learn: Microsoft Foundry quickstarts (page updated 2026-10-28)  |  click a quickstart name to open it")
    top = y + 100
    TW = 1790
    L = lambda text, url: dict(text=text, link=url, color=LINK)
    S = lambda t, th: (t, th)
    rows = [
        [S("Set up", "gray"), L("Create resources", learn("tutorials/quickstart-create-foundry-resources")), "Create a Foundry project, deploy a model and grant your team access"],
        [S("Build your first agent", "green"), L("Create a prompt agent", PROMPT_QS), "Build a prompt agent with the Microsoft Foundry SDK"],
        [S("", "green"), L("Create a web research agent", learn("agents/quickstarts/create-web-research-agent")), "Portal or azd: a prompt agent combining the Microsoft Copilot harness (preview), web search and a reusable skill"],
        [S("", "green"), L("Create a voice-based prompt agent", VOICE_QS), "Create a managed real-time voice agent, connect over WebSocket, complete a spoken turn (preview)"],
        [S("", "green"), L("Optimize a prompt agent", learn("agents/quickstarts/quickstart-optimize-prompt-agent")), "Run the agent optimizer in the portal, then promote the best candidate (optimizer: preview)"],
        [S("", "green"), L("Build agents using the Responses API", RESP_QS), "Call the Responses API from your own code with the Agent Framework or the OpenAI SDK"],
        [S("", "green"), L("Chat with an agent in code", GET_CODE), "Use the Microsoft Foundry SDK to build an AI chat application"],
        [S("Deploy hosted agents", "green"), L("Deploy a hosted agent", HOSTED_QS), "Deploy a containerized agent with azd or the Foundry Toolkit for VS Code"],
        [S("", "green"), L("Deploy your own code as a hosted agent", OWN_CODE_QS), "Add one hosting library to your existing Python agent and deploy it"],
        [S("", "green"), L("Build a toolbox for a hosted agent", learn("agents/quickstarts/quickstart-toolbox-agent")), "Combine web search and the Microsoft Learn MCP server, then use the toolbox from a hosted agent"],
        [S("", "green"), L("Give a hosted agent persistent memory", learn("agents/quickstarts/quickstart-memory-hosted-agent")), "Provision a Foundry memory store; the agent remembers facts about each user across sessions (memory: preview)"],
        [S("", "green"), L("Add a Foundry IQ knowledge base", learn("agents/quickstarts/quickstart-foundry-iq-hosted-agent")), "Ground a hosted agent in a Foundry IQ knowledge base exposed through a toolbox"],
        [S("", "green"), L("Optimize a hosted agent", learn("agents/quickstarts/quickstart-optimize-hosted-agent")), "Run the agent optimizer, then deploy the winning candidate (optimizer: preview)"],
        [S("", "green"), L("Create a CI/CD pipeline", CICD), "A CI/CD pipeline for a hosted agent in a Foundry project"],
        [S("Evaluate and trace", "violet"), L("Evaluate a hosted agent", learn("observability/quickstarts/quickstart-evaluate-hosted-agent")), "Generate a test suite, run an evaluation and review the results"],
        [S("", "violet"), L("Trace your hosted agent", learn("observability/quickstarts/quickstart-tracing-hosted-agent")), "View end-to-end traces with built-in OpenTelemetry instrumentation"],
    ]
    tbl = Table([("Stage", 190), ("Quickstart", 520), "What you do"], rows, w=TW, theme="green", size=14, head_size=16, pad_y=5, first_col_theme="gray")
    tbl.place(cv, 0, top)
    cv.text(0, tbl.bottom + 8, "Learn: Microsoft Foundry quickstarts", size=12, color=LINK, link=QS)

    nx, nw = TW + 60, W - TW - 60
    notes = [
        Note(nw, "Voice-based prompt agents, the Microsoft Copilot harness, memory, Fabric IQ and Work IQ are preview. Workflows are preview and retire on 2026-12-01: "
                 "use Microsoft Agent Framework for new development and do not draw Workflows into a new plan.",
             kind="warn", title="Preview and retiring (as of 2026-11-03)", src=[("Portal general availability overview", GA)]),
        Note(nw, "Prompt agents need no compute. Hosted agents bill per-call inference + tool usage + container compute. Voice agents bill Voice Live and model usage.",
             kind="info", title="The cost shape follows the rung", src=[("Agents in Microsoft Foundry", AGENTS)]),
        Note(nw, "The Responses API and Foundry Agent Service are not available in every Azure region, and hosted agents have their own region list. Check before you commit to a region.",
             kind="gotcha", title="Region matters", src=[("Hosted agents", HOSTED)]),
        Note(nw, "Hosted agents support Python and C# and any agent framework: the protocol libraries are framework-agnostic. Ship a container image or a .zip of source.",
             kind="tip", title="Bring any framework", src=[("Frameworks for hosted agents", FRAMEWORKS)]),
        Note(nw, "This canvas follows Learn's capability map. The front-page picture is the 'Microsoft Foundry platform overview' canvas, the exhaustive inventory is the "
                 "'Capability atlas' canvas, and 'Ways to build on Foundry' covers the surfaces (portal, SDKs, azd, VS Code, coding agents).",
             kind="key", title="Where to go next in this gallery", src=[("Capability map", CAP), ("Capability reference", CAPREF)]),
    ]
    ny = top
    for n in notes:
        n.place(cv, nx, ny)
        ny = n.bottom + 20
    return max(tbl.bottom + 30, ny - 20)


# ================================================================================================ 5. persona map
def entry(name, what, but, path, th, badge=None, w=608):
    return Card(w, name, [f"= {but}"], subtitle=what, theme=th, badge=badge, src=[(name, learn(path) if not path.startswith("http") else path)],
                title_size=19, body_size=15, sub_size=14, pad=14, fill="hatch")


def s_personas(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Who is it for? Persona -> entry points", w=W,
                   sub="Learn: the 'Who it's for' column of the product and capability map  |  each card states the fit first, then the boundary where another option is a better match")
    PW, GAPX, CWD = 380, 70, 608
    personas = [
        ("Anyone evaluating Foundry", "gray", "browser", [
            entry("Foundry portal", "Web experience for models, agents, evaluations and resources", "Need repeatable builds? Move to the SDKs or the CLI.", "concepts/general-availability", "gray")]),
        ("Application developer", "blue", "code", [
            entry("Foundry Models", "Catalog of models from Microsoft, OpenAI, Anthropic, Meta and others", "A model needs your domain data? Consider fine-tuning.", "concepts/foundry-models-overview", "blue"),
            entry("Microsoft Foundry SDKs", "Client libraries for Python, C#, JavaScript and Java", "Scaffolding and deploying agent projects? Add the Azure Developer CLI.", "how-to/develop/sdk-overview", "blue"),
            entry("Visual Studio Code extension", "Foundry projects, models and agents inside the editor", "Want an AI assistant to drive Foundry? Use coding agents.", "how-to/develop/get-started-projects-visual-studio-code", "blue"),
            entry("Coding agents and MCP", "Foundry Skill and the Foundry MCP Server (preview) for coding agents", "Prefer direct authoring? Use the VS Code extension.", "how-to/develop/use-microsoft-foundry-skill", "blue")]),
        ("Agent developer", "green", "agent", [
            entry("Prompt agents", "Declarative agents defined by instructions, a model and tools", "Need custom code or a container? Use hosted agents.", "agents/quickstarts/prompt-agent", "green"),
            entry("Voice-based prompt agents", "Prompt agents that speak and listen in real time", "Only need text responses? Use prompt agents.", "agents/quickstarts/prompt-voice-agent", "green", "preview"),
            entry("Hosted agents", "Your own agent code or framework, run by Foundry", "Instructions and tools are enough? Prompt agents are simpler.", "agents/concepts/hosted-agents", "green"),
            entry("Toolbox", "Managed endpoint that packages the tools an agent can call", "Agent only needs your own data? Start with Foundry IQ.", "agents/concepts/toolbox-overview", "orange"),
            entry("Foundry IQ", "Agentic retrieval over a knowledge base", "Only a few uploaded files? File search is lighter weight.", "agents/concepts/what-is-foundry-iq", "teal", "Partial GA"),
            entry("Memory", "Persistent agent recall across sessions", "Each request stands alone? Skip it.", "agents/concepts/what-is-memory", "teal", "preview"),
            entry("Workflows", "Orchestration of multiple agents and steps", "A single agent with tools can finish the job? Stay simpler. Retires 2026-12-01.", "agents/concepts/workflow", "green", "retiring"),
            entry("LangChain and LangGraph", "Integration of Foundry models, tools, memory and tracing", "Starting fresh? Native agents need less glue code.", "how-to/develop/langchain", "green")]),
        ("ML engineer", "blue", "ml", [
            entry("Fine-tuning", "Customization of a model on your own data", "The gap is missing context? Use retrieval instead.", "openai/how-to/fine-tuning", "blue")]),
        ("Platform engineer", "grape", "gear", [
            entry("Azure Developer CLI (azd)", "Command-line scaffolding, deployment and environment management", "Only calling models from an app? The SDKs are enough.", "agents/concepts/cli-agent-development", "grape"),
            entry("Foundry control plane", "Governance for agents, models and tools across your estate", "Governing a single project? Project settings are enough.", "control-plane/overview", "grape")]),
        ("AI quality engineer", "violet", "metrics", [
            entry("Foundry Observability", "Tracing, monitoring and dashboards for agents and models", "Comparing versions before release? Start with evaluations.", "concepts/observability", "violet"),
            entry("Evaluations", "Scoring for generative AI apps and agents", "Need adversarial coverage? Add AI red teaming.", "how-to/evaluate-generative-ai-app", "violet")]),
        ("Security administrator", "pink", "security", [
            entry("AI red teaming", "Automated adversarial scans against a model or agent", "Measuring everyday quality? Evaluations fit better.", "concepts/ai-red-teaming-agent", "pink"),
            entry("Guardrails and controls", "Content filters and safety controls for models and agents", "Testing safety before release? Pair it with AI red teaming.", "guardrails/guardrails-overview", "pink")]),
    ]
    ry = y + 104
    for label, th, icon, cards in personas:
        nrows = -(-len(cards) // 4)
        rh = [max(c.h for c in cards[i * 4:(i + 1) * 4]) for i in range(nrows)]
        block_h = sum(rh) + 18 * (nrows - 1)
        with cv.panel(0, ry, w=W, theme=th, style="dotted", fill="none", pad=18) as p:
            pb = Box(PW, label, sub=f"{len(cards)} entry point{'s' if len(cards) != 1 else ''}", theme=th, fill="hatch", icon=icon, icon_pos="top", icon_size=40, size=23, sub_size=15,
                     h=block_h)
            pb.place(cv, p.ix, p.iy)
            cx0 = p.ix + PW + GAPX
            yy = p.iy
            for ri in range(nrows):
                xx = cx0
                for c in cards[ri * 4:(ri + 1) * 4]:
                    c.place(cv, xx, yy, h=rh[ri])
                    xx += CWD + 24
                yy += rh[ri] + 18
            arrow(cv, [(pb.right + 8, p.iy + min(block_h, rh[0]) / 2), (cx0 - 8, p.iy + min(block_h, rh[0]) / 2)], sw=3.5, end_head="arrow", color=theme(th).stroke)
        ry = p.bottom + 24
    return ry - 24
