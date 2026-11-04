"""Foundry Tools (formerly Azure AI services): resource kinds, endpoints, and how each tool reaches an agent.

Layout: summary strip -> resource model (subscription -> resource group -> Foundry resource -> project, plus the separate Speech /
Language / Vision / Search resources) -> hub-and-spoke "how it shows up" lanes (agent tool, prebuilt agent, portal tool, platform
plumbing, API only) -> the ten available tools as tiles (+ the retired six) -> endpoint table -> per-service facts exactly as the
docs state them -> three worked flows -> retirement timeline, network notes and gotchas -> sources.
Document Intelligence, Vision and Content Safety are drawn as NOT documented agent tools, because no Learn page read says otherwise.
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="foundry-tools-and-ai-services", title="Foundry Tools (formerly Azure AI services)", section="2", group="Tools and MCP", order=34,
    description="What Foundry Tools are, which resource kinds and endpoints back them, and which ones surface as agent tools (Speech and Language MCP, Translator via OpenAPI) versus resource-level or guardrail plumbing only.",
    tags=["foundry-tools", "ai-services", "speech", "language", "content-understanding", "kinds"],
)

CW, GUT = 520, 48
STEP = CW + GUT
W = 6 * CW + 5 * GUT          # 3360


def X(i: int) -> float:
    return i * STEP


def SPAN(n: int) -> float:
    return n * CW + (n - 1) * GUT


AIS = "azure/ai-services/"
S = dict(
    what=("What are Foundry Tools?", learn(AIS + "what-are-ai-services", base="")),
    multi=("Multi-service resource", learn(AIS + "multi-service-resource", base="")),
    arch=("Foundry architecture", learn("concepts/architecture")),
    sdk=("Foundry SDK overview (Foundry Tools endpoints)", learn("how-to/develop/sdk-overview")),
    speech=("Azure Speech tool for agents", learn("agents/how-to/tools/azure-ai-speech")),
    langagents=("Foundry Tools and agents for Azure Language", learn(AIS + "language-service/concepts/foundry-tools-agents", base="")),
    pii=("PII detection quickstart", learn(AIS + "language-service/personally-identifiable-information/quickstart", base="")),
    clu=("CLU multi-turn conversations quickstart", learn(AIS + "language-service/conversational-language-understanding/how-to/quickstart-multi-turn-conversations", base="")),
    langdet=("Language detection quickstart", learn(AIS + "language-service/language-detection/quickstart", base="")),
    translator=("Text translation overview", learn(AIS + "translator/text-translation/overview", base="")),
    cu=("Content Understanding overview", learn(AIS + "content-understanding/overview", base="")),
    di=("Document Intelligence overview", learn(AIS + "document-intelligence/overview", base="")),
    vision=("Azure Vision overview", learn(AIS + "computer-vision/overview", base="")),
    cs=("Content Safety overview", learn(AIS + "content-safety/overview", base="")),
    voicelive=("Voice Live with Foundry Agent Service", learn(AIS + "speech-service/how-to-voice-agent-integration", base="")),
    voiceagent=("Voice agent quickstart", learn("agents/quickstarts/prompt-voice-agent")),
    guard=("Guardrails overview", learn("guardrails/guardrails-overview")),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


_KitNote = Note


def Note(*a, **kw):  # noqa: N802 - the kit leaves no bottom padding under citation lines; add it here
    n = _KitNote(*a, **kw)
    if kw.get("src"):
        n.h += 10
    return n


# lane colours: how a Foundry Tool shows up in Foundry
LANE = dict(tool="orange", agent="green", portal="teal", plumb="pink", api="gray")


def chain(cv: Canvas, x: float, y: float, w: float, steps, *, theme="orange", dash="solid", gap=48, size=18, sub_size=14):
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    boxes = [Box(bw, lab, sub=sub, theme=theme, fill="hatch", dash=dash, size=size, sub_size=sub_size, pad=10, min_h=96) for lab, sub in steps]
    hmax = max(b.h for b in boxes)
    cx = x
    for i, b in enumerate(boxes):
        b.place(cv, cx, y, h=hmax)
        numbered(cv, b.x + 6, b.y + 6, i + 1, theme=theme, d=28, size=16)
        cx += bw + gap
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", dash=dash, end_head="arrow", sw=2)
    return boxes, y + hmax


# ============================================================================================== 0. title, key, summary
def title_and_key(cv: Canvas) -> float:
    _, bottom = title_block(
        cv, 0, 0, "Foundry Tools (formerly Azure AI services)",
        "Resource kinds, endpoints, and which tools actually reach an agent: Speech and Language through MCP, Translator through OpenAPI, the rest as APIs or guardrail plumbing  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    with cv.panel(0, y, theme="gray", style="dotted", pad=16, w=W) as k:
        cv.text(k.ix, k.iy - 2, "Colour = how it shows up", size=16, color="#343a40")
        legend(cv, k.ix + 220, k.iy - 2, [
            ("Agent tool you can call", "orange"), ("Prebuilt agent", "green"), ("Portal tool or playground", "teal"),
            ("Platform plumbing (guardrails)", "pink"), ("API or SDK only: no agent tool documented", "gray"), ("Foundry resource and project", "blue")],
            size=15, gap=22)
        y2 = k.iy + 34
        cv.text(k.ix, y2, "Markers", size=16, color="#343a40")
        cx = k.ix + 220
        draw_badge(cv, cx, y2 - 1, "ga")
        draw_badge(cv, cx + 50, y2 - 1, "preview")
        t = cv.text(cx + 140, y2, "status as stated on each Learn page, as of 2026-11-03", size=15)
        cx += 140 + t.w + 32
        cv.rect(cx, y2 + 1, 28, 18, stroke="#495057", sw=2, dash="dashed")
        t = cv.text(cx + 38, y2, "retired, or not documented as an agent tool", size=15)
    return k.bottom


def summary_strip(cv: Canvas, y: float) -> float:
    def tile(title, body, theme, icon, keys):
        return Card(CW, title, ["= " + body], theme=theme, icon=icon, fill="hatch", title_size=22, body_size=15, pad=14,
                    gap=4, icon_size=34, src=src(*keys))

    tiles = [
        tile("Renamed, not replaced", "Foundry Tools is the new name for Azure AI services: prebuilt and customizable APIs and models. Most are REST plus client libraries; many have a free tier (F0 SKU); containers cover on-premises.",
             "blue", "ai-services", ("what",)),
        tile("One kind to remember: AIServices", "Only the AIServices kind gives the multi-service Foundry resource. The Speech, Language and Vision kinds are single-service resources.",
             "blue", "foundry", ("arch", "multi")),
        tile("10 available, 6 retiring", "Not for new apps: Anomaly Detector, Content Moderator, Language Understanding (LUIS), Metrics Advisor, Personalizer and QnA Maker.",
             "gray", "applied-ai", ("what",)),
        tile("Speech and Language are agent tools", "Both through MCP servers (Language is preview). Translator is reachable through the generic OpenAPI tool, with no built-in tool documented. No Learn page read documents Document Intelligence, Vision or Content Safety as an agent tool.",
             "orange", "toolbox", ("speech", "langagents")),
        tile("Endpoints differ", "Most share https://<resource>.cognitiveservices.azure.com. Speech to text and text to speech use regional hosts; Text Translation is global at api.cognitive.microsofttranslator.com.",
             "indigo", "api-connections", ("sdk",)),
        tile("Retirements to footnote", "Fabric data agent tool: Nov 6, 2026. Language Studio: Mar 20, 2027. Content Safety preview items: Apr 30, 2027. Image Analysis 4.0: Sept 25, 2028.",
             "red", "service-health", ("langagents", "cs", "vision")),
    ]
    _, bottom = row(cv, 0, y, tiles, gap=GUT)
    return bottom


# ============================================================================================== 1. resource model
def resource_model(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "1  The resource model behind Foundry Tools", size=34,
                   sub="One Foundry resource reaches Azure OpenAI and the multi-service tools through one endpoint and key; some tools also live in their own resources")
    y += 100
    bw = SPAN(2)
    sub_ = Box(bw, "Azure subscription", theme="gray", icon="subscription", icon_pos="left", icon_size=30, fill="hatch", size=19, min_h=60)
    rg = Box(bw, "Resource group", theme="gray", icon="resource-group", icon_pos="left", icon_size=30, fill="hatch", size=19, min_h=60)
    sub_.place(cv, 0, y)
    rg.place(cv, 0, sub_.bottom + 34)
    connect(cv, sub_, rg, a_side="bottom", b_side="top", end_head="arrow", sw=2)
    fy = rg.bottom + 34
    with cv.panel(0, fy, title="Microsoft Foundry resource", sub="Microsoft.CognitiveServices/accounts  |  kind AIServices", theme="blue", style="solid", fill="soft",
                  pad=18, title_size=24, sub_size=15, w=bw) as fr:
        cv.text(fr.ix, fr.iy, "The primary Azure resource type for building, deploying and managing generative AI models, applications and agents. "
                "Azure OpenAI and Foundry Tools are reachable through one endpoint and key.", size=15, color="#343a40", wrap=bw - 40)
        chips = ChipFlow([Chip(t, theme="blue", size=16) for t in ("Agents", "Evaluations", "Azure OpenAI", "Speech", "Vision", "Language", "Content Understanding")],
                         bw - 40, gap=10)
        chips.place(cv, fr.ix, fr.iy + 76)
    pj = Box(bw, "Foundry project", sub="Microsoft.CognitiveServices/accounts/projects  |  kind AIServices  |  subresource of the Foundry resource", theme="green",
             icon="folder", icon_pos="left", icon_size=30, fill="hatch", size=19, sub_size=14, min_h=84)
    pj.place(cv, 0, fr.bottom + 34)
    connect(cv, rg, fr, a_side="bottom", b_side="top", end_head="arrow", sw=2)
    connect(cv, fr, pj, a_side="bottom", b_side="top", end_head="arrow", sw=2)
    # separate resources
    sx = X(2) + 100
    sw_ = SPAN(2) - 100
    others = [
        Box(sw_, "Azure Speech in Foundry Tools", sub="Microsoft.CognitiveServices/accounts  |  kind Speech  |  Speech", theme="orange", icon="speech", icon_pos="left", icon_size=30,
            fill="hatch", size=18, sub_size=14, min_h=84, dash="dashed"),
        Box(sw_, "Azure Language in Foundry Tools", sub="Microsoft.CognitiveServices/accounts  |  kind Language  |  Language", theme="orange", icon="language", icon_pos="left",
            icon_size=30, fill="hatch", size=18, sub_size=14, min_h=84, dash="dashed"),
        Box(sw_, "Azure Vision in Foundry Tools", sub="Microsoft.CognitiveServices/accounts  |  kind Vision  |  Vision", theme="gray", icon="vision", icon_pos="left", icon_size=30,
            fill="hatch", size=18, sub_size=14, min_h=84, dash="dashed"),
        Box(sw_, "Azure AI Search", sub="provider Microsoft.Search  |  knowledge retrieval over your data", theme="teal", icon="ai-search", icon_pos="left", icon_size=30,
            fill="hatch", size=18, sub_size=14, min_h=84, dash="dashed"),
    ]
    _, ob = col(cv, sx, y, others, gap=30)
    for o in others:
        connect(cv, rg, o, a_side="right", b_side="left", end_head="arrow", sw=2, dash="dotted", route="elbow", bend=0.15)
    cv.text(sx, ob + 8, "Separate resources: the single-service kinds and a different provider", size=15, color="#495057")
    # create it
    c1 = Card(SPAN(2), "Create the right kind", [
        "Azure portal: Foundry > Foundry; or https://portal.azure.com/#create/Microsoft.CognitiveServicesAIFoundry",
        "CLI: az cognitiveservices account create ... --kind AIServices",
        "! Azure provides more than one resource kind for Foundry Tools: be sure to create the kind AIServices",
        "Roles to create: Contributor, Owner, or a custom role with Microsoft.CognitiveServices/accounts/write",
    ], theme="blue", icon="foundry", fill="hatch", title_size=21, body_size=16, src=src("arch", "multi"))
    c2 = Card(SPAN(2), "Setup flavours", [
        "Basic",
        "With security controls",
        "Standard setup for agents: your own Cosmos DB, AI Search and Storage. The variants apply to Speech, Language, Vision and Content Understanding",
        "Resource types in the same namespace share management APIs, RBAC actions, networking and Azure Policy aliases: existing Azure OpenAI policies and RBAC keep applying after the upgrade",
    ], theme="blue", icon="resource-group", fill="hatch", title_size=21, body_size=16, src=src("arch"))
    c1.place(cv, X(4), y)
    c2.place(cv, X(4), c1.bottom + 28)
    return max(pj.bottom, ob + 30, c2.bottom)


# ============================================================================================== 2. hub-and-spoke lanes
def lanes(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2  How each Foundry Tool shows up: five lanes from one hub", size=34,
                   sub="Only lane 1 is an agent tool you call. Lanes 2 to 4 are other ways Foundry uses the services. Lane 5 has no documented agent tool.")
    y += 100
    lw = (W - 4 * GUT) / 5
    hub = Box(820, "Your agent or app in Microsoft Foundry", sub="how a Foundry Tool shows up depends on the service", theme="green", icon="agent", icon_pos="left",
              icon_size=40, fill="hatch", size=24, sub_size=16, pad=14, min_h=110)
    hub.place(cv, (W - hub.w) / 2, y)

    def lc(title, body, theme, badge=None, keys=(), icon=None):
        return Card(lw - 32, title, body, theme=theme, badge=badge, icon=icon, fill="hatch", title_size=19, body_size=15, pad=12, gap=4, icon_size=28, src=src(*keys))

    lane_defs = [
        ("1  Agent tool", "call it from an agent", "tool", [
            lc("Azure Speech MCP Server", ["Remote MCP server from the Catalog: speech to text and text to speech"], "orange", icon="speech", keys=("speech",)),
            lc("Azure Language MCP server", ["Named entity recognition, Text Analytics for health, CLU, CQA, language detection, sentiment analysis, summarization, key phrase extraction, PII redaction",
                                             "A local MCP server also exists"], "orange", badge="preview", icon="language", keys=("langagents",)),
            lc("Azure AI Search", ["AI Search tool, Foundry IQ (knowledge base MCP) and file search (Standard)", "Separate provider Microsoft.Search; see the tool catalog"],
               "orange", icon="ai-search", keys=("arch",)),
        ]),
        ("2  Prebuilt agent", "create it in the portal", "agent", [
            lc("Language intent routing agent", ["CLU classifies the intent, CQA returns a curated answer, with an optional RAG fallback"], "green", badge="preview", icon="language", keys=("langagents",)),
            lc("Exact Question Answering agent", ["CQA, no code, verbatim answers"], "green", badge="preview", icon="language", keys=("langagents",)),
        ]),
        ("3  Portal tool or playground", "build or try in the portal", "portal", [
            lc("Content Understanding Tool", ["Foundry portal tool for agentic workflows; Content Understanding Studio complements it"], "teal", icon="doc-intelligence", keys=("cu",)),
            lc("Language playground", ["PII redaction models, language detection and CLU tiles"], "teal", icon="language", keys=("pii", "langdet", "clu")),
            lc("Voice Live and Foundry voice agents", ["A voice-first agent layer, not a tool", "Foundry voice agents are preview; Voice Live is fully managed"], "teal",
               icon="speech", keys=("voicelive", "voiceagent")),
        ]),
        ("4  Platform plumbing", "works for you behind guardrails", "plumb", [
            lc("Azure AI Content Safety", ["Classification models behind Foundry guardrails: hate, sexual, self-harm, violence, Prompt Shields, protected material", "Not an agent tool"],
               "pink", icon="content-safety", keys=("cs", "guard")),
            lc("Preview items retiring April 30, 2027", ["Analyze Multimodal", "Custom categories (rapid) for text and image", "Connected and disconnected containers",
                                                          "The Embedded Content Safety SDK", "Groundedness detection (preview)"],
               "pink", icon="service-health", keys=("cs",)),
        ]),
        ("5  API or SDK only", "no agent tool documented", "api", [
            lc("Azure Document Intelligence", ["OCR and intelligent document processing"], "gray", icon="doc-intelligence", keys=("di",)),
            lc("Azure Vision", ["Face, Image Analysis (legacy) and OCR (legacy)"], "gray", icon="vision", keys=("vision",)),
            lc("Azure Translator", ["Text translation API; reachable from an agent through the OpenAPI tool, with no built-in tool documented"], "gray", icon="translator", keys=("translator",)),
        ]),
    ]
    need = 0
    ly = hub.bottom + 90
    panels = []
    for i, (title, sub, key, cards) in enumerate(lane_defs):
        th = LANE[key]
        with cv.panel(i * (lw + GUT), ly, title=title, sub=sub, theme=th, style="dotted" if key != "api" else "dashed", fill="soft", pad=16, title_size=24, sub_size=15,
                      w=lw) as p:
            col(cv, p.ix, p.iy, cards, gap=22)
        panels.append(p)
    bends = [0.30, 0.55, 0.5, 0.55, 0.30]
    dashes = ["solid", "solid", "dashed", "dashed", "dotted"]
    for p, key, bend, dash in zip(panels, ("tool", "agent", "portal", "plumb", "api"), bends, dashes):
        connect(cv, hub, p, a_side="bottom", b_side="top", end_head="arrow", sw=3, dash=dash, route="elbow", bend=bend, color=THEMES[LANE[key]].stroke)
    # side notes beside the hub
    nl = Note(1000, "A Foundry Tool can reach Foundry in five different ways. Only the first lane is a tool your agent calls; the others are prebuilt agents, portal tools, "
              "platform plumbing, or APIs and SDKs you call from your own code.", kind="key", title="Reading the lanes", src=src("what"))
    nl.place(cv, hub.x - 80 - nl.w, hub.y + (hub.h - nl.h) / 2)
    nr = Note(1000, "The five lanes are our grouping of what the docs describe: the docs do not use these lane names. A service appears in the tool lane only when a Learn page "
              "documents it as an agent tool.", kind="info", title="Our grouping, the docs' facts", src=src("speech", "langagents"))
    nr.place(cv, hub.right + 80, hub.y + (hub.h - nr.h) / 2)
    return max(p.bottom for p in panels)


# ============================================================================================== 3. service tiles
def tiles(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3  The ten available Foundry Tools, with official names and what the docs say", size=34,
                   sub="Quoted descriptions come from the What are Foundry Tools? page; the colour is the lane from the section above")
    y += 100
    tw = (W - 4 * GUT) / 5

    def tile(title, sub, body, theme, icon, keys, badge=None, dash="solid"):
        return Card(tw, title, body, theme=theme, subtitle=sub, badge=badge, icon=icon, fill="hatch", dash=dash, title_size=20, body_size=15, sub_size=14, pad=14, gap=4,
                    icon_size=34, src=src(*keys))

    cards = [
        tile("Azure Speech in Foundry Tools", "kind Speech", [
            "\"Speech to text, text to speech, translation, and speaker recognition\"",
            "Agent tool: Azure Speech MCP Server",
            "STT: https://<REGION>.stt.speech.microsoft.com",
            "TTS: https://<REGION>.tts.speech.microsoft.com",
            "Custom Voice: https://<RESOURCE-NAME>.cognitiveservices.azure.com/",
        ], "orange", "speech", ("what", "sdk")),
        tile("Azure text translation in Microsoft Foundry", "Translator", [
            "\"more than 100 in-use, at-risk, and endangered languages and dialects\"",
            "No built-in agent tool documented; OpenAPI tool example",
            "Text Translation: https://api.cognitive.microsofttranslator.com/ (global; geography and resource-specific endpoints also exist)",
            "Document Translation: https://<RESOURCE-NAME>.cognitiveservices.azure.com/",
        ], "gray", "translator", ("what", "translator")),
        tile("Azure Language in Foundry Tools", "kind Language", [
            "\"natural language understanding\"",
            "Agent tool: Language MCP server (preview); prebuilt agents (preview)",
            "Text analysis: https://<RESOURCE-NAME>.cognitiveservices.azure.com",
            "MCP: https://{foundry-resource-name}.cognitiveservices.azure.com/language/mcp?api-version=2025-11-15-preview",
        ], "orange", "language", ("what", "langagents"), badge="preview"),
        tile("Azure Content Understanding in Foundry Tools", "part of the Foundry resource", [
            "\"Analyze and comprehend various media content types\"",
            "Portal: Content Understanding Tool for agentic workflows",
            "API 2025-11-01 is GA; 2026-06-01-preview adds agentic mode",
        ], "teal", "doc-intelligence", ("what", "cu")),
        tile("Azure Document Intelligence in Foundry Tools", "documents", [
            "\"Turn documents into intelligent data-driven solutions\"",
            "A machine-learning based OCR and intelligent document processing service; API monikers 2.1, 3.0, 3.1 and 4.0",
            "Not documented as an agent tool",
        ], "gray", "doc-intelligence", ("what", "di")),
        tile("Azure Vision in Foundry Tools", "kind Vision", [
            "\"Analyze content in images and videos\"",
            "Face; Image Analysis (legacy; Image Analysis 4.0 retires Sept 25, 2028); OCR (legacy)",
            "Not documented as an agent tool; check the migration guide",
        ], "gray", "vision", ("what", "vision")),
        tile("Azure AI Search", "provider Microsoft.Search", [
            "Knowledge retrieval over your data",
            "Agent tool: AI Search tool, Foundry IQ (knowledge base MCP) and file search (Standard)",
            "One index per AI Search tool; key or managed identity",
        ], "orange", "ai-search", ("what", "arch")),
        tile("Azure AI Content Safety", "the Foundry Tools list says Content Safety", [
            "\"detects unwanted contents\"",
            "Endpoint: https://<your-resource-name>.cognitiveservices.azure.com/",
            "Powers Foundry guardrails; not an agent tool",
            "! Some preview features retire on April 30, 2027",
        ], "pink", "content-safety", ("what", "cs")),
        tile("Custom Vision", "listed as available", [
            "Listed among the available Foundry Tools. The pages read for this canvas give no further detail",
        ], "gray", "custom-vision", ("what",), dash="dashed"),
        tile("Immersive Reader", "listed as available", [
            "Listed among the available Foundry Tools. The pages read for this canvas give no further detail",
        ], "gray", "applied-ai", ("what",), dash="dashed"),
    ]
    _, b = grid(cv, 0, y, cards, 5, gap_x=GUT, gap_y=30)
    y2 = b + 36
    with cv.panel(0, y2, title="Retired or being retired: do not use for new apps", sub="greyed on the What are Foundry Tools? page", theme="gray", style="dashed", fill="none",
                  pad=18, title_size=22, sub_size=15, w=W) as rp:
        ChipFlow([Chip(t, theme="gray", size=17, dash="dashed", fill="soft") for t in (
            "Anomaly Detector", "Content Moderator", "Language Understanding (LUIS)", "Metrics Advisor", "Personalizer", "QnA Maker")], W - 40, gap=14).place(cv, rp.ix, rp.iy)
    return rp.bottom


# ============================================================================================== 4. endpoints
def endpoints(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Endpoints: which host answers for which tool", size=34,
                   sub="Speech to text and text to speech use regional hosts, not the cognitiveservices.azure.com pattern")
    y += 100
    t = Table([("Foundry Tool or surface", 560), ("Endpoint", 1180), ("Note", 484)], [
        [("Computer Vision, Content Safety, Document Intelligence, Language, Translation, Token", "gray"), "https://<your-resource-name>.cognitiveservices.azure.com/",
         "Through the Azure AI Services endpoint; a custom subdomain replaces the resource name"],
        [("Speech to Text (Standard)", "orange"), "https://<REGION>.stt.speech.microsoft.com", "regional host"],
        [("Text to Speech (Neural)", "orange"), "https://<REGION>.tts.speech.microsoft.com", "regional host"],
        [("Custom Voice", "orange"), "https://<RESOURCE-NAME>.cognitiveservices.azure.com/", ""],
        [("Text Translation", "gray"), "https://api.cognitive.microsofttranslator.com/", "Global; geography and resource-specific endpoints also exist"],
        [("Document Translation", "gray"), "https://<RESOURCE-NAME>.cognitiveservices.azure.com/", ""],
        [("Language text analysis", "orange"), "https://<RESOURCE-NAME>.cognitiveservices.azure.com", ""],
        [("Azure Language MCP server (preview)", "orange"), "https://{foundry-resource-name}.cognitiveservices.azure.com/language/mcp?api-version=2025-11-15-preview", "preview"],
        [("Foundry project: agents, toolboxes, skills, connections", "blue"), "https://<account>.services.ai.azure.com/api/projects/<project>", ""],
        [("Azure OpenAI v1", "blue"), "https://<resource>.openai.azure.com/openai/v1/", "from the shell tool page"],
        [("Foundry MCP Server (for coding agents)", "blue"), "https://mcp.ai.azure.com", ""],
    ], theme="indigo", size=15, head_size=16, title="Endpoint patterns (SDK overview and the service pages)", title_size=22)
    t.place(cv, 0, y)
    n1 = Note(SPAN(2), "On March 20, 2027, Azure Language Studio retires and migrates to Microsoft Foundry. If your workloads use retiring Azure AI Language features, for example "
              "sentiment analysis, key phrase extraction, summarization, entity linking, CLU or CQA, plan to migrate to Microsoft Foundry alternatives (quoted as the page words it).",
              kind="warn", title="Language Studio retirement", src=src("langagents", "sdk"))
    n1.place(cv, X(4), y)
    n2 = Note(SPAN(2), "The Language MCP and agents pages still present CLU and CQA while the same Language page warns they are retiring. Check the current page before you build on either.",
              kind="info", title="Docs overlap", src=src("langagents"))
    n2.place(cv, X(4), n1.bottom + 24)
    return max(t.bottom, n2.bottom)


# ============================================================================================== 5. per-service facts
def facts(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Per-service facts, as the docs state them", size=34,
                   sub="Auth, status and gotchas for the services that surface in Foundry. Nothing here is inferred beyond the pages cited.")
    y += 100
    w3 = SPAN(2)

    def fc(title, body, theme, icon, keys, badge=None, dash="solid", w=w3):
        return Card(w, title, body, theme=theme, icon=icon, badge=badge, fill="hatch", dash=dash, title_size=21, body_size=15, pad=14, gap=4, icon_size=32, src=src(*keys))

    speech = fc("Azure Speech: a remote MCP server from the Catalog", [
        "Add it: Agent playground > Tools > Add > Catalog tab > Azure Speech MCP Server. The page carries no preview tag",
        "Parameters: foundry-resource-name; Bearer = the Foundry resource KEY1 or KEY2; header X-Blob-Container-Url = a container SAS (read and write) for the output audio",
        "Treat the key and the SAS as secrets; use the shortest SAS expiry; Storage Blob Data Contributor is needed to mint the SAS",
        "Needs a Foundry resource in a Speech-supported region and a tool-calling model (gpt-4o or later)",
        "STT audio: WAV, MP3, OGG or FLAC (best: WAV 16 kHz 16-bit). TTS output: WAV (voice example en-US-JennyNeural)",
        "! The page says MCP tools require the Agent Service Enterprise tier (error: Invalid tool value(s): mcp. Use the Enterprise offerings...); no other page read explains this",
        "! Does not support a network-secured Foundry resource",
    ], "orange", "speech", ("speech",))
    voice = fc("Voice Live and Foundry voice agents", [
        "Voice Live with Foundry Agent Service: the VoiceLive SDK with agent_name, project_name and an optional agent_version; foundry_resource_override plus authentication_identity_client_id for cross-resource; interim_response modes llm_interim_response or static_interim_response",
        "Foundry voice agents (preview): speech-to-speech and text models, built-in telephony and voice-pipeline tracing. Create with Interaction mode = Voice (cannot be changed later); managed realtime model such as gpt-realtime; 24-kHz PCM audio; automatic turn detection; live session over WebSocket; azd ai agent init --kind prompt-voice (azd 1.32.0 or later)",
        "Maximum voice session: 60 min. Stored voice conversations and audio are kept 60 days",
        "Entra only in agent mode (no keys). No audio model to deploy: Voice Live is fully managed. Foundry User for the Voice Live resource's managed identity on the target agent resource",
        "Voice-based agents (preview) are not available in Poland Central and Spain Central",
    ], "teal", "speech", ("voicelive", "voiceagent"))
    lang = fc("Azure Language: MCP server and prebuilt agents", [
        "MCP server (preview): NER, Text Analytics for health, CLU, CQA, language detection, sentiment analysis, summarization, key phrase extraction, PII redaction. A local MCP server also exists (Azure-Samples/ai-language-samples)",
        "Intent routing agent (preview) = CLU + CQA with an optional RAG fallback. Exact Question Answering agent (preview) = CQA: no code, verbatim answers",
        "Auth: a custom keys connection with Ocp-Apim-Subscription-Key = the resource key (or the project managed identity in the toolbox quickstart sample, granted access on the Language resource)",
        "Needs a Foundry resource plus a Language resource, and Contributor or Owner on the resource group. Network-secured projects can require publicly accessible MCP servers",
        "For CLU and CQA agents, create projects on a Foundry, AI hub or Language resource and deploy; no azure.yaml template is provided",
    ], "orange", "language", ("langagents",), badge="preview")
    row1_r, y1 = row(cv, 0, y, [speech, voice, lang], gap=GUT)
    y1 += 36
    pii = fc("Language PII, language detection and CLU: playground, not tools", [
        "New Foundry playground models: Azure Language-Text PII redaction, -Conversational PII redaction and -Document PII redaction (native .pdf, .docx, .txt; redacted rendering side by side)",
        "Policies: character mask, entity mask or no mask. Options: API version, model version, language, types to include, values to exclude, synonyms, redaction character",
        "Language playground tiles: Detect language; Conversational language understanding (Fine-tune); Quick deploy with LLM",
        "CLU multi-turn entity slot filling is available only in Foundry (classic)",
        "Entra is recommended (RBAC enforced); keys give full access",
    ], "teal", "language", ("pii", "clu", "langdet"))
    trans = fc("Azure Translator: no built-in agent tool", [
        "Reachable through an OpenAPI tool with the project managed identity (audience https://cognitiveservices.azure.com)",
        "Text translation REST is GA at 2026-06-06, a breaking change from v3.0: request inputs, response value. Operations: Languages, Translate, Transliterate",
        "Model choice NMT or LLM (LLM needs a Foundry resource, for example GPT-5.1); adaptive custom translation (up to 5 reference translations or a dataset index ID); tone (formal, informal, neutral) and gender controls",
        "Auth: resource key Ocp-Apim-Subscription-Key, a time-limited token, or Entra (keyless)",
        "Limits: Translate takes 1,000 array elements x 50,000 chars; LLM takes 50 x 5,000. Billing: NMT by source characters, LLM by input and output tokens",
    ], "gray", "translator", ("translator",))
    cu = fc("Azure Content Understanding", [
        "Foundry portal: the Content Understanding Tool for agentic workflows; Content Understanding Studio complements it",
        "API 2025-11-01 is GA (production). 2026-06-01-preview adds agentic mode, richer classification and in-page segmentation, signature detection, document metadata and analyzer improvement",
        "Inputs: documents, images, audio, video. Analyzers (prebuilt and custom); extraction (OCR, layout, selection marks, barcodes, formulas); segmentation; field extraction (extract, classify, generate); confidence and grounding; contextualization. Output: Markdown or a JSON schema",
        "Needs a Foundry resource and your own deployments of supported generative and embedding models",
        "Inherits Foundry guardrails (warnings and errors; annotate-only is available by approval)",
    ], "teal", "doc-intelligence", ("cu",))
    _, y2 = row(cv, 0, y1, [pii, trans, cu], gap=GUT)
    y2 += 36
    nd = Card(SPAN(4), "Not documented as agent tools (as of 2026-11-03)", [
        "Document Intelligence: a machine-learning based OCR and intelligent document processing service, API monikers 2.1, 3.0, 3.1, 4.0. Content Understanding Studio offers a smooth transition from Document Intelligence",
        "Vision: Face; Image Analysis (legacy; Image Analysis 4.0 retires Sept 25, 2028); OCR (legacy). A caution banner points to the migration guide",
        "Content Safety: powers Foundry guardrails (hate, sexual, self-harm, violence, Prompt Shields, protected material); Foundry memory docs advise Content Safety plus prompt-injection detection",
        "! No Learn page read documents Document Intelligence, Vision or Content Safety as a built-in agent tool: do not draw them as tools",
    ], theme="gray", icon="content-safety", fill="hatch", dash="dashed", title_size=21, body_size=15, src=src("di", "vision", "cs", "guard"))
    nd.place(cv, 0, y2)
    nn = Note(SPAN(2), "Speech MCP is not network-secured; the Language MCP server may need public access in network-secured projects; web grounding with Bing leaves the Azure "
              "boundary; Work IQ uses public HTTPS. Foundry Tools list certifications: Cloud Security Alliance STAR, FedRAMP Moderate and HIPAA BAA (see the Trust Center for privacy).",
              kind="warn", title="Network and compliance notes", src=src("what", "speech", "langagents"))
    nn.place(cv, X(4), y2)
    return max(nd.bottom, nn.bottom)


# ============================================================================================== 6. flows
def flows(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6  Three worked flows: Speech, Language intent routing and Translator", size=34,
                   sub="The shortest documented path for each service to reach an agent")
    y += 100
    with cv.panel(0, y, title="Flow 1: use Azure Speech from an agent", sub="remote MCP server from the Catalog", theme="orange", style="dashed", fill="none", pad=20,
                  title_size=24, sub_size=15, w=W) as p1:
        chain(cv, p1.ix, p1.iy, W - 40, [
            ("Create a Foundry resource", "in a Speech-supported region"),
            ("Storage and a SAS", "storage account, container, SAS with read and write"),
            ("Create an agent", "with a tool-calling model"),
            ("Add the tool", "Tools > Add > Catalog > Azure Speech MCP Server"),
            ("Fill and connect", "foundry-resource-name, Bearer key, X-Blob-Container-Url"),
            ("Prompt it", "STT: Recognize this audio file located in the SAS. TTS: Convert text to speech"),
            ("Read the result", "a WAV is saved to the container"),
        ], theme="orange", gap=34, size=17, sub_size=14)
    with cv.panel(0, p1.bottom + 36, title="Flow 2: Language intent routing agent", sub="preview", theme="green", style="dashed", fill="none", pad=20, title_size=24, sub_size=15, w=SPAN(4)) as p2:
        chain(cv, p2.ix, p2.iy, SPAN(4) - 40, [
            ("Deploy CLU and CQA projects", "on a Foundry, AI hub or Language resource"),
            ("Custom keys connection", "Ocp-Apim-Subscription-Key"),
            ("Create the agent", "in the portal"),
            ("CLU classifies the intent", "then CQA returns the curated answer"),
            ("Optional RAG fallback", "when no curated answer fits"),
        ], theme="green", gap=34, size=17, sub_size=14)
    with cv.panel(X(4), p1.bottom + 36, title="Flow 3: Translator", sub="through the OpenAPI tool", theme="gray", style="dashed", fill="none", pad=20, title_size=24, sub_size=15,
                  w=SPAN(2)) as p3:
        chain(cv, p3.ix, p3.iy, SPAN(2) - 40, [
            ("Grant the role", "project managed identity gets the Translator role"),
            ("OpenAPI connection", "ProjectManagedIdentity, audience https://cognitiveservices.azure.com"),
            ("Add the tool", "OpenAPI tool with translator_openapi.json"),
            ("Call translate", "the agent invokes the translate operation"),
        ], theme="gray", gap=26, size=16, sub_size=13)
    return max(p2.bottom, p3.bottom)


# ============================================================================================== 7. timeline + gotchas
def retirements(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "7  Retirements to footnote, and gotchas", size=34,
                   sub="Dates as the pages state them, read on 2026-11-03")
    y += 100
    bottom = timeline(cv, 0, y + 125, W, [
        ("Nov 6, 2026", "Fabric data agent tool: deprecation date", "an agent tool, not a Foundry Tool: see the tool catalog"),
        ("Mar 20, 2027", "Azure Language Studio retires", "and migrates to Microsoft Foundry"),
        ("Apr 30, 2027", "Content Safety preview items retire", "including Groundedness detection (preview)"),
        ("Sept 25, 2028", "Image Analysis 4.0 retires", "Azure Vision, legacy Image Analysis"),
    ], label_w=640, size=20, theme="red")
    y2 = bottom + 50
    notes = [
        Note(CW, "Only the AIServices kind gives the multi-service Foundry resource. The Speech, Language and Vision kinds are single-service. Speech to text and text to speech use regional host names, not cognitiveservices.azure.com.",
             kind="gotcha", title="Kinds and hosts", src=src("arch", "sdk")),
        Note(CW, "Document Intelligence, Vision and Content Safety are services and APIs here: Content Safety is the guardrails backbone. Do not draw them as agent tools unless a later source says so.",
             kind="gotcha", title="Not agent tools", src=src("di", "vision", "cs")),
        Note(CW, "Naming is not yet uniform: the Translator overview is titled Azure text translation in Microsoft Foundry, and the Content Safety page is still titled What is Azure AI Content Safety?",
             kind="warn", title="Names still drift", src=src("translator", "cs")),
        Note(CW, "The Speech tool page requires the Agent Service Enterprise tier for MCP tools and no other page explains it. Check your tier before you build on it.",
             kind="warn", title="Enterprise tier", src=src("speech")),
        Note(CW, "The Language pages present CLU and CQA while the same pages warn that several Language features are retiring. Treat Language agents as preview.",
             kind="preview", title="Preview and retiring at once", src=src("langagents")),
        Note(CW, "Standard setup for agents (your own Cosmos DB, AI Search and Storage) has variants for Speech, Language, Vision and Content Understanding.",
             kind="info", title="Standard setup", src=src("arch")),
    ]
    _, b = row(cv, 0, y2, notes, gap=GUT)
    return b


def related(cv: Canvas, y: float) -> float:
    cv.text(0, y, "See also in this gallery:", size=18, color="#343a40")
    items = [("Tool catalog", "orange"), ("Foundry Toolbox", "orange"), ("MCP in Foundry: catalogs and servers", "orange"), ("MCP and tool authentication", "red"),
             ("Voice agents (Preview): architecture, definition and telephony", "green"), ("Foundry resource model", "blue")]
    f = ChipFlow([Chip(t, theme=th, size=16, fill="soft") for t, th in items], W - 260, gap=12).place(cv, 250, y - 4)
    return max(y + 28, f.y + f.h)


def sources_panel(cv: Canvas, y: float) -> None:
    items = [S[k] for k in ("what", "multi", "arch", "sdk", "speech", "langagents", "pii", "clu", "langdet", "translator", "cu", "di", "vision", "cs", "voicelive", "voiceagent", "guard")]
    sources(cv, 0, y, items, w=W, cols=4)


def build(cv: Canvas) -> None:
    y = title_and_key(cv) + 30
    y = summary_strip(cv, y) + 60
    y = resource_model(cv, y) + 70
    y = lanes(cv, y) + 70
    y = tiles(cv, y) + 70
    y = endpoints(cv, y) + 70
    y = facts(cv, y) + 70
    y = flows(cv, y) + 70
    y = retirements(cv, y) + 50
    y = related(cv, y) + 40
    sources_panel(cv, y)
