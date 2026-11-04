"""Microsoft Foundry capability atlas - part 2 of 2: areas 7-11 plus the status wall.

Evaluation and optimization, trust and safety, manage/secure/govern, APIs and SDKs, Foundry Tools - every capability
with status, purpose and a clickable Learn link - then a GA / preview / retiring wall for the whole atlas.
The data model and renderer live in capability_atlas.py (part 1), which holds the data for all 11 areas.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from generator.xd import *
from generator.xd import metrics

_p = Path(__file__).with_name("capability_atlas.py")
_spec = importlib.util.spec_from_file_location("gen_diagram_capability_atlas_shared", _p)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

META = dict(
    id="capability-atlas-part-2", title="Foundry capability atlas (part 2)", section="1", group="Overview", order=2.5,
    description="The exhaustive inventory, part 2 of 2: evaluation, trust and safety, governance, APIs and SDKs and Foundry Tools - with the GA / preview / retiring status wall and the status-drift notes.",
    tags=["atlas", "capabilities", "inventory", "governance", "status"],
)

OTHER_1 = (
    "Entra token scope: nearly every page uses https://ai.azure.com/.default; one sample on the classic-migration page shows https://cognitiveservices.azure.com/.default for the OpenAI v1 client, and the Foundry MCP Server uses https://mcp.ai.azure.com.\n"
    "Endpoint hostnames: the SDK overview uses <resource>.openai.azure.com/openai/v1, the LangChain page uses <resource>.services.ai.azure.com/openai/v1; the endpoints page says both are accepted.\n"
    "API keys: the GA page says agents, evaluations, datasets and Content Understanding need Entra; the auth matrix says agents, evaluations and Toolbox do not accept keys but Content Understanding batch jobs do."
)
OTHER_2 = (
    "SDK versions move weekly: Learn shows Python 2.3.0 or later, JavaScript 2.8.0, Java 2.3.0 and .NET 2.0.0 (GA) while blogs mention newer lines; read 2.x as the stable line.\n"
    "Vector-store tokens per file: 2,000,000 on the limits page, 5,000,000 on the file-search page (512 MB per file and 10,000 files per store agree).\n"
    "Capability-reference wording: Routines, SharePoint and Fabric connectors and Foundry Agent Canvas are described differently from their target pages; this atlas follows the pages."
)

SOURCES_2 = [
    ("Microsoft Foundry capability reference", learn("concepts/capability-reference")),
    ("Feature status at GA (matrix, dated 2026-09-23)", learn("concepts/general-availability")),
    ("Evaluation in Foundry", learn("concepts/evaluation-overview")),
    ("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
    ("Guardrails and controls overview", learn("guardrails/guardrails-overview")),
    ("Foundry control plane overview", learn("control-plane/overview")),
    ("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
    ("Network isolation options", learn("agents/concepts/networking-options")),
    ("Plan and manage costs", learn("concepts/manage-costs")),
    ("Foundry Models endpoints", learn("foundry-models/concepts/endpoints")),
    ("What are Foundry Tools?", A.AI + "what-are-ai-services"),
    ("Content Understanding overview", A.AI + "content-understanding/overview"),
    ("Region support", learn("reference/region-support")),
    ("DevBlog: What's new in Microsoft Foundry, September 2026 (blog)",
     "https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-september-2026/"),
]


def wall_items():
    L = A.link_for
    ga = [("Foundry portal (core)", L("Foundry portal (ai.azure.com)")), ("Models catalog", L("Foundry Models catalog")),
          ("Prompt agents", L("Prompt agents")), ("Hosted agents", L("Hosted agents")), ("Routines", L("Routines")),
          ("A2A v1.0", L("Agent-to-agent (A2A)")), ("Toolbox (hosted agents)", L("Toolbox")),
          ("Tool search", L("Tool search")), ("MCP", L("Model Context Protocol (MCP)")),
          ("Web search", L("Web search")), ("Code interpreter", L("Code interpreter")),
          ("File search", L("File search")), ("OpenAPI tool", L("OpenAPI tool")),
          ("Function calling", L("Function calling")), ("Evaluations", L("Evaluations")),
          ("AI red teaming (cloud)", L("AI red teaming")),
          ("Fine-tuning (Managed Training)", L("Fine-tuning: Managed Training")),
          ("Guardrails (Models)", L("Guardrails and controls")), ("Publish to Copilot and Teams", L("Publish and share")),
          ("Foundry IQ (API)", L("Foundry IQ"))]
    pre = [("Managed compute", L("Managed compute")), ("Instant access models", L("Instant access models")),
           ("Leaderboards", L("Model benchmarks and leaderboards")), ("Voice-based agents", L("Voice-based prompt agents")),
           ("Copilot harness", L("Microsoft Copilot harness")), ("Memory", L("Memory")), ("Fabric IQ", L("Fabric IQ")),
           ("Work IQ", L("Work IQ")), ("Skills", L("Skills")), ("Computer use", L("Computer use")),
           ("Image generation tool", L("Image generation (agent tool)")), ("SharePoint tool", L("SharePoint tool")),
           ("Control plane", L("Foundry control plane")), ("AI gateway", L("AI gateway integration")),
           ("Monitoring dashboard", L("Agent monitoring dashboard")), ("Insights", L("Insights in Foundry")),
           ("Guardrails (Agents, controls)", L("Guardrails and controls")), ("Guided Guardrail", L("Guided Guardrail")),
           ("Task adherence", L("Task adherence")), ("Human evaluation", L("Human evaluation")),
           ("Evaluations in CI/CD", L("Evaluations in CI/CD")), ("Foundry Agent Canvas", L("Foundry Agent Canvas")),
           ("Foundry MCP Server", L("Foundry MCP Server")),
           ("Programmed Training", L("Fine-tuning: Programmed Training")),
           ("Video playground", L("Playgrounds (Model, Agents, Images, Video)")),
           ("Sora 2", L("Video generation (Sora 2)")), ("Flex processing", L("Flex processing")),
           ("Healthcare models (limited)", L("Healthcare AI models")), ("MAI-Image and MAI-Thinking", L("MAI models")),
           ("Hugging Face (managed compute)", L("Hugging Face models")),
           ("Long-running hosted agents", L("Long-running hosted agents")), ("Autopilots", L("Autopilots"))]
    ret = [("Fabric data agent tool: 2026-11-06", L("Fabric data agent tool")),
           ("Workflows: 2026-12-01", L("Workflows")),
           ("Language Studio: 2027-03-20", L("Azure Language: retiring features")),
           ("Custom-agent registration: 2027-04-30", L("Custom agent registration")),
           ("Language features: 2029-03-31", L("Azure Language: retiring features"))]
    dead = [("dall-e-3: 2026-03-04", L("Image generation")), ("GitHub Models: 2026-07-30", L("Deployment helpers and best practices")),
            ("azure-ai-inference SDK: 2026-08-26", L("Inference SDK to OpenAI SDK")),
            ("Assistants API: 2026-08-26", L("Classic to new agents migration")),
            ("Anomaly Detector, Content Moderator, LUIS, Metrics Advisor, Personalizer, QnA Maker",
             L("Retired Foundry-adjacent services"))]
    return ga, pre, ret, dead


def status_wall(cv: Canvas, y: float) -> float:
    ga, pre, ret, dead = wall_items()
    widths = (1000, 1320, 820)
    gap = (A.W - sum(widths)) / 2
    pad = 18
    specs = [
        ("GA", "green", "Core platform and the capabilities with a GA verdict; region availability still varies",
         [(a, b, "ga") for a, b in ga], None),
        ("Preview", "orange",
         "Offered under supplemental terms of use and not recommended for production workloads; preview status varies by feature, region and API version",
         [(a, b, "pre") for a, b in pre], None),
        ("Retiring and retired", "red", "Dates are retirement or deprecation dates (as of 2026-11-03)",
         [(a, b, "ret") for a, b in ret], [(a, b, "dead") for a, b in dead]),
    ]
    # measure
    heights = []
    for (title, theme, sub, chips, chips2), w in zip(specs, widths):
        inner = w - 2 * pad
        sl = metrics.wrap_text(sub, inner, 14)
        h = pad + 30 + len(sl) * 14 * A.LH + 12 + A.chips_height(chips, inner)
        if chips2:
            h += 14 + 18 * A.LH + 8 + A.chips_height(chips2, inner)
        heights.append(h + pad)
    H = max(heights)
    x = 0.0
    for (title, theme, sub, chips, chips2), w in zip(specs, widths):
        th = THEMES[theme]
        inner = w - 2 * pad
        with cv.group():
            cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=3)
            cv.text(x + pad, y + pad - 2, title, size=26, color=th.deep)
            sl = metrics.wrap_text(sub, inner, 14)
            cv.text(x + pad, y + pad + 30, "\n".join(sl), size=14, color=A.MUTED_TXT)
            cy = y + pad + 30 + len(sl) * 14 * A.LH + 12
            cy = A.draw_chips(cv, x + pad, cy, inner, chips, theme) + 14
            if chips2:
                cv.text(x + pad, cy, "Already retired", size=18, color=th.deep)
                cy += 18 * A.LH + 8
                A.draw_chips(cv, x + pad, cy, inner, chips2, theme)
        cv.register(f"wall {title}", x, y, w, H)
        x += w + gap
    return y + H


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry capability atlas",
                                "Part 2 of 2: evaluate, protect, govern and integrate (areas 7-11), plus the GA / preview / retiring wall - verified 2026-11-03",
                                w=A.W)
    y = A.header_band(cv, bottom + 36, 2) + 56
    y = A.draw_strip(cv, 0, y, {7, 8, 9, 10, 11}, "see part 1") + 56

    d2 = A.span_w(2)
    a7 = A.AreaBlock(A.balanced(A.A7, 2), d2)
    a8 = A.AreaBlock(A.balanced(A.A8, 2), d2)
    a9 = A.AreaBlock(A.balanced(A.A9, 2), d2)
    a10 = A.AreaBlock(A.A10, A.COL)
    a11 = A.AreaBlock(A.A11, A.COL)
    drift = A.DriftBox(d2, "Status drift in these areas",
                       "As of 2026-11-03. Tags D13-D14 match the red tags on the rows; D1-D12 are on part 1.", A.DRIFT_2, cols=2)
    o1 = Note(A.COL, OTHER_1, kind="warn", title="Other places the docs disagree (1/2)", size=15)
    o2 = Note(A.COL, OTHER_2, kind="warn", title="Other places the docs disagree (2/2)", size=15)
    G = A.GUT
    heights = [a7.h + G + a8.h + G + drift.h, a9.h + G + max(o1.h, o2.h), a10.h + G + a11.h]
    end = y + max(heights)
    x1, x2, x3 = A.cx_(0), A.cx_(2), A.cx_(4)
    a7.place(cv, x1, y)
    a8.place(cv, x1, a7.bottom + G)
    drift.place(cv, x1, a8.bottom + G, h=end - (a8.bottom + G))
    a9.place(cv, x2, y)
    oh = max(o1.h, o2.h)
    o1.place(cv, x2, a9.bottom + G, h=oh)
    o2.place(cv, x2 + A.COL + A.GUT, a9.bottom + G, h=oh)
    a10.place(cv, x3, y)
    a11.place(cv, x3, a10.bottom + G, h=end - (a10.bottom + G))

    wy = end + 60
    section_header(cv, 0, wy, "Status wall: what is GA, preview and retiring across the whole atlas (as of 2026-11-03)",
                   sub="Curated from the row verdicts in both parts; every chip opens its Learn page.", size=30, w=A.W)
    wb = status_wall(cv, wy + 100)
    sources(cv, 0, wb + 60, SOURCES_2, w=A.W, cols=3)
