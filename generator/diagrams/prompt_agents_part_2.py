"""Prompt agents in depth (part 2): Microsoft Copilot harness (preview), incoming A2A (preview), routines (preview),
legacy Agent applications vs the agent endpoint model, optimizer pointers, migration from classic and disabling classic agents."""
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS

META = dict(
    id="prompt-agents-part-2", title="Prompt agents: harness, A2A, routines and migration", section="2", group="Agent Service", order=11.5,
    description="Prompt agents, part 2: the Microsoft Copilot harness (preview) with its tools and rules, incoming A2A (preview), routines (preview), legacy Agent applications, optimizer pointers, and migrating from or disabling classic agents.",
    tags=["prompt-agents", "copilot-harness", "a2a", "routines", "migration"],
)

W = 3000
HARNESS = learn("agents/how-to/use-tools-skills-copilot-harness")
PA = learn("agents/concepts/prompt-agents")
CA = learn("agents/how-to/configure-agent")
A2A = learn("agents/how-to/enable-agent-to-agent-endpoint")
ROUT_C = learn("agents/concepts/routines")
ROUT_H = learn("agents/how-to/use-routines")
ROUT_R = learn("reference/rest/create-or-update-routine")
APPS = learn("agents/how-to/agent-applications")
MIGAPP = learn("agents/how-to/migrate-agent-applications")
MIG = learn("agents/how-to/migrate")
DIS = learn("agents/how-to/disable-classic-agents")
OPT = learn("agents/concepts/agent-optimizer-overview")
LQR = learn("agents/concepts/limits-quotas-regions")
REST = learn("reference/rest/agents-patch-agent-object")


# ---------------------------------------------------------------------------------------------- helpers
def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def hdr(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


def link(cv, x, y, label, url):
    return cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)


# ---------------------------------------------------------------------------------------------- section 0
def glance(cv, y):
    note = Note(W, "The Microsoft Copilot harness, incoming A2A, routines and the network egress controls are all in preview - they carry Preview badges below. "
                   "Everything is as of 2026-11-03; part 1 covers anatomy, the request flow, the endpoint and its authorization.",
                kind="preview", title="Four preview features, one migration story",
                src=[("Prompt agents", PA), ("Use the Copilot harness", HARNESS)])
    note.place(cv, 0, y)
    y = note.bottom + 26
    items = [
        ("Copilot harness", "multi-step tool, skill, file and command workflows in a Foundry-operated sandbox", "agent", "green", "preview"),
        ("Incoming A2A", "expose a prompt agent as an A2A server through one PATCH", "a2a", "pink", "preview"),
        ("Routines", "one trigger + one action: invoke the agent on a time or an event", "scheduler", "violet", "preview"),
        ("Applications to endpoints", "legacy Agent applications collapse into the agent endpoint model", "versions", "gray", None),
        ("Migrate from classic", "move code constructs to the new SDK; disable classic assistants with a tag", "learn", "orange", None),
    ]
    gap = 28
    bw = (W - gap * (len(items) - 1)) / len(items)
    boxes = [Box(bw, lab, sub=sub, icon=ic, icon_pos="left", icon_size=44 if ic == "a2a" else 36, theme=th, size=19, sub_size=14, h=128)
             for lab, sub, ic, th, _ in items]
    r, b = row(cv, 0, y, boxes, gap=gap)
    for bx, it in zip(boxes, items):
        if it[4]:
            badge_on(cv, bx, it[4])
    return b + 60


# ---------------------------------------------------------------------------------------------- section 1
def harness(cv, y):
    y = hdr(cv, y, "1  Microsoft Copilot harness (preview)",
            "A second runtime for the same prompt-agent resource: choose it when you create the agent - you cannot switch later.") + 40
    Y = y
    # --- fork (left)
    FW = 1000
    start = Box(250, "Create a prompt agent", sub="portal, SDK, REST or azd", theme="gray", h=96, size=18)
    d1 = Box(500, "Default prompt-agent behavior", sub="the simplest runtime configuration", icon="agent", icon_pos="left", theme="green", h=110, size=19, sub_size=15)
    d2 = Box(500, "Microsoft Copilot harness (preview)", sub="supported multi-step tool, skill, file and command workflows; Foundry operates the harness and its sandbox",
             icon="agent", icon_pos="left", theme="green", h=150, size=19, sub_size=15, dash="dashed")
    d1.place(cv, FW - 500, Y + 6)
    d2.place(cv, FW - 500, Y + 6 + d1.h + 70)
    start.place(cv, 0, (d1.cy + d2.cy) / 2 - start.h / 2)
    badge_on(cv, d2, "preview")
    connect(cv, start, d1, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, start, d2, a_side="right", b_side="left", route="elbow", sw=2.5)
    nt = Note(FW, "Same agent type, same endpoint, same roles and governance - you still call it through the Responses API. You do not deploy or maintain harness code. "
                  "To change the runtime, create a new agent. The Responses API 'ephemeral agent' pattern cannot use the harness (it needs a saved version).",
              kind="key", title="Chosen at creation, then fixed", src=[("What is Foundry Agent Service?", learn("agents/overview"))])
    nt.place(cv, 0, d2.bottom + 40)

    # --- inside the harness (right)
    IX, IW = FW + 60, W - FW - 60
    with cv.panel(IX, Y, w=IW, title="Inside the harness", sub="a conversation-scoped workspace in a service-managed sandbox - CPU, memory and lifecycle are not customer-configurable",
                  theme="green", style="solid", fill="soft", pad=22, title_size=26, sub_size=15) as inner:
        tw_ = (IW - 44 - 4 * 18) / 5
        tools = [
            Box(tw_, "filesystem_read", sub="file read", theme="green", h=100, size=17, sub_size=14),
            Box(tw_, "filesystem_write", sub="file write", theme="green", h=100, size=17, sub_size=14),
            Box(tw_, "shell", sub="shell commands", theme="green", h=100, size=17, sub_size=14),
            Box(tw_, "web", sub="fetch a URL", theme="green", h=100, size=17, sub_size=14),
            Box(tw_, "subagents", sub="sub-agents", theme="green", h=100, size=17, sub_size=14),
        ]
        r, b = row(cv, inner.ix, inner.iy + 6, tools, gap=18)
        cv.text(inner.ix, b + 12, "Five built-in tools, on by default (subject to service and organizational policy) - ONE microsoft_copilot_toolset_preview block configures them.",
                size=16, color="#2b8a3e", wrap=IW - 44)
        cf = ChipFlow(["Skills: up to 50 top-level references", "Function tools (non-strict; no ___ in names)", "Foundry web search",
                       "Declared tools through the managed toolbox"], IW - 44, theme="orange", size=16, gap=12)
        cf.place(cv, inner.ix, b + 62)
        n_mem = Chip("Foundry Memory: not supported", theme="red", size=16, icon=None)
        n_mem.place(cv, inner.ix, b + 62 + cf.h + 14)
    link(cv, IX, inner.bottom + 6, "Use the Copilot harness with prompt agents", HARNESS)
    top_bottom = max(nt.bottom, inner.bottom + 24)

    # --- cards
    cw3 = (W - 2 * 40) / 3
    y2 = top_bottom + 50
    c1 = Card(cw3, "Prerequisites", [
        "A supported region (9 - see below) and a model that supports reasoning and tool calling",
        "A new prompt agent; Foundry User on the project",
        "Bring your own model (BYOM) is not supported",
        "The agent's own identity (instance_identity.principal_id) needs Foundry User at project scope to call a Toolbox or return generated files - not the project managed identity; allow about 5 minutes",
        "azd 1.37.0 or later, azure.ai.agents 1.0.0-beta.22 or later, env AZD_ALPHA_ENABLE_AGENTS_MANAGED_HARNESS=true",
        "Python azure-ai-projects 2.9.0 or later; SDK class MicrosoftCopilotHarness; azure.yaml: harness { type: microsoft_copilot_preview }",
    ], theme="green", icon="learn", src=[("Use the Copilot harness", HARNESS)])
    c2 = Card(cw3, "Request and definition rules", [
        "Every request needs a conversation; omit store or keep it true",
        "store: false and previous_response_id are not supported",
        "Do not set temperature, top_p, tool_choice, text.format or text.verbosity in the definition",
        "Do not set max_output_tokens, max_tool_calls, parallel_tool_calls, truncation, context_management, top_logprobs, safety_identifier, prompt_cache_key, prompt_cache_retention, service_tier or user",
        "Unsupported fields return an error - they are not ignored",
        "Text, image and file input over HTTP; no input_audio and no WebSocket response.create",
    ], theme="red", icon="gear", src=[("Quotas, limits and regions", LQR)])
    c3 = Card(cw3, "Workspace, skills and cleanup", [
        "The workspace is conversation-scoped; it survives normal sandbox idle, resume and replacement - keep important outputs in Foundry Files",
        "Skills: up to 50 top-level references; names unique, lowercase letters, digits and hyphens, at most 64 characters; each resolves to an immutable version",
        "Function tools: unique names, no reserved ___ separator, no clash with harness tool names, strict: true unsupported",
        "No individual responses.delete - delete the conversation; Foundry also cleans up the backing harness session",
    ], theme="orange", icon="files", src=[("Quotas, limits and regions", LQR)])
    r, b = row(cv, 0, y2, [c1, c2, c3], gap=40)

    # --- network egress + regions
    y3 = b + 40
    c4 = Card(cw3, "Network egress controls", [
        "A responsible-AI (RAI) policy with Network rules: default Allow or Deny, then first-match host rules",
        "Audit logs a match; Enforce returns HTTP 403",
        "Applies to the shell and the harness Web tool only - other prompt agents and model deployments are unaffected; declared Foundry tools keep their own network boundaries",
        "Attach in the portal (Build > Guardrails > Create > Network) or with policies: - type: rai_policy and rai_config.rai_policy_name",
    ], theme="pink", icon="content-safety", badge="preview", src=[("Use the Copilot harness", HARNESS)])
    c5_regions = ["Australia East", "Canada Central", "Central US", "Germany West Central", "Japan East", "Sweden Central", "UK South", "West Europe", "West US"]
    cf5 = ChipFlow(c5_regions, cw3 - 32, theme="indigo", size=15, gap=8)
    h45 = max(c4.h, cf5.h + 150)
    c4.place(cv, 0, y3, h=h45)
    with cv.panel(cw3 + 40, y3, w=cw3, h=h45, title="Supported regions (9)", theme="indigo", style="solid", fill="hatch", pad=16, title_size=20) as c5:
        place_icon(cv, "regions", c5.x + cw3 - 16 - 36, y3 + 12, 36)
        t5 = cv.text(c5.ix, c5.iy, "The harness runs in a subset of the regions that support prompt agents:", size=15, color=INK, wrap=cw3 - 32)
        cf5.place(cv, c5.ix, t5.bottom + 14)
        link(cv, c5.ix, y3 + h45 - 30, "Quotas, limits and regions", LQR)
    n6 = Note(cw3, "The docs and azd call it the 'Microsoft Copilot harness' (type microsoft_copilot_preview), but the REST schema lists github_copilot_preview, "
                   "'GitHub Copilot managed harness for prompt agents'. The Foundry Agent Canvas page describes a separate GitHub Copilot App extension. "
                   "Use the azd / SDK names and check the REST reference before scripting.",
              kind="warn", title="Docs disagree: harness naming", src=[("Agent object schema (REST)", REST)])
    n6.place(cv, 2 * (cw3 + 40), y3)
    return max(c4.bottom, n6.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 2
def a2a(cv, y):
    y = hdr(cv, y, "2  Incoming A2A (preview): expose a prompt agent as an A2A server",
            "One PATCH adds an agent card and turns on the a2a protocol next to responses - REST or SDK only (Python azure-ai-projects 2.5.0 or later).") + 40
    Y = y
    seq = Sequence(cv, 0, Y, [("You (agent owner)", "gray", "user"), ("Foundry agent endpoint", "green", "agent"), ("A2A client", "pink", "agent")],
                   spacing=520, head_w=230, head_h=64, size=16, label_size=15)
    seq.msg(0, 1, "PATCH the agent: agent_card (description, version, skills[]) + protocol_configuration { responses: {}, a2a: {} }", num=1)
    seq.msg(2, 1, "GET .../a2a/agentCard/v1.0 (or /v0.3)", num=2, note="or the A2A-Version header, or ?a2a-version=")
    seq.msg(1, 2, "agent card - Entra only, no anonymous card", dash="dashed")
    seq.msg(2, 1, "call .../protocols/a2a with an Entra token (Foundry Agent Consumer)", num=3)
    seq.msg(1, 2, "task result - text only, no streaming", dash="dashed", num=4, note="tasks and contexts are kept 60 days from the last write")
    bottom = seq.end()
    SW_ = 230 + 2 * 520 + 40
    RX = SW_ + 60
    RW = W - RX
    rw2 = (RW - 40) / 2
    c1 = Card(rw2, "Version negotiation", [
        "Agent card at .../a2a/agentCard/v1.0 or /v0.3",
        "Or the A2A-Version header, or the ?a2a-version= query",
        "Conflicting selectors: 400 version-ambiguous",
        "! If nothing is specified Foundry serves v0.3 (preview) - pin v1.0 for production",
        "v1.0: JSON-RPC only. v0.3: HTTP+JSON and JSON-RPC. No gRPC",
    ], theme="pink", icon="a2a", icon_size=44, src=[("Enable an A2A endpoint", A2A)])
    c2 = Card(rw2, "Access and limits", [
        "Entra only: no API keys, no anonymous agent card",
        "Callers need Foundry Agent Consumer at project or agent scope",
        "Tasks and contexts are retained for 60 days from the last write",
        "Text modality only; no streaming",
        "Requires the responses protocol on the same agent",
    ], theme="pink", icon="security", src=[("Enable an A2A endpoint", A2A)])
    r, b = row(cv, RX, Y, [c1, c2], gap=40)
    badge_on(cv, c1, "preview")
    n = Note(RW, "The A2A how-to only describes prompt agents, while the hosted-agents concept page and azure.yaml also list a2a as a hosted-agent protocol. "
                 "Check the hosted-agents canvas before assuming either.", kind="warn", title="Docs disagree: which agents can serve A2A?",
             src=[("Hosted agents", learn("agents/concepts/hosted-agents"))])
    n.place(cv, RX, b + 30)
    return max(bottom, n.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 3
def routines(cv, y):
    y = hdr(cv, y, "3  Routines (preview): when a time or an event occurs, invoke this agent",
            "A routine is exactly one trigger plus one action. REST calls need the header Foundry-Features: Routines=V2Preview.") + 40
    Y = y
    TW_ = 640
    trig = [
        Box(TW_, "timer", sub="one-shot; inactive after it fires", theme="violet", h=100, size=19, sub_size=14),
        Box(TW_, "schedule (recurring)", sub="5-field cron + time_zone; minimum interval 5 minutes; azd omits the time zone = UTC", theme="violet", h=118, size=19, sub_size=14),
        Box(TW_, "github_issue", sub="issue opened or closed; connection_id, owner, repository", icon="github", icon_pos="left", theme="violet", h=100, size=19, sub_size=14),
        Box(TW_, "custom - provider teams", sub="a message in a Teams channel", icon="teams", icon_pos="left", theme="violet", h=100, size=19, sub_size=14),
    ]
    with cv.panel(0, Y, w=TW_ + 44, title="Triggers", sub="pick one", theme="violet", style="dotted", pad=22, title_size=24, sub_size=15) as tp:
        col(cv, tp.ix, tp.iy + 4, trig, gap=22)
    RX_ = tp.right + 190
    routine = Box(480, "Routine", sub="one trigger + one action. Run history keeps inputs, outputs, status and trace links", icon="scheduler", icon_pos="left", theme="violet",
                  h=190, size=26, sub_size=15)
    routine.place(cv, RX_, tp.y + tp.h / 2 - 95)
    badge_on(cv, routine, "preview")
    AX = routine.right + 190
    acts = [
        Box(640, "invoke_agent_responses_api", sub="static input (no templating); optional conversation", theme="green", h=104, size=18, sub_size=14),
        Box(640, "invoke_agent_invocations_api", sub="static input; optional hosted session_id", theme="green", h=104, size=18, sub_size=14),
    ]
    AP_H = 384
    with cv.panel(AX, Y + (tp.h - AP_H) / 2, w=640 + 44, h=AP_H, title="Action", sub="pick one", theme="green", style="dotted", pad=22, title_size=24, sub_size=15) as ap:
        col(cv, ap.ix, ap.iy + 22, acts, gap=40)
    agent = Box(420, "The agent", sub="prompt agent (or hosted agent)", icon="agent", icon_pos="left", theme="green", h=130, size=22, sub_size=15)
    agent.place(cv, ap.right + 150, ap.y + ap.h / 2 - 65 - 20)
    ident = Chip("runs as the agent identity by default", theme="red", size=15, icon=None)
    ident.place(cv, agent.x - 10, agent.bottom + 18)
    connect(cv, trig[1], routine, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, trig[0], routine, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, trig[2], routine, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, trig[3], routine, a_side="right", b_side="left", route="elbow", sw=2.5)
    connect(cv, routine, acts[0], a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, routine, acts[1], a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, acts[0], agent, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, acts[1], agent, a_side="right", b_side="left", route="elbow", sw=3)
    link(cv, 0, tp.bottom + 8, "Routines (concept)", ROUT_C)
    cv.text(220, tp.bottom + 8, "Learn: Use routines", size=12, color=LINK, link=ROUT_H)
    cv.text(400, tp.bottom + 8, "Learn: Create or update a routine (REST)", size=12, color=LINK, link=ROUT_R)

    # facts
    y2 = tp.bottom + 56
    cw3 = (W - 2 * 40) / 3
    f1 = Card(cw3, "Identity and security", [
        "Default identity: the agent's own identity; a creator identity can be chosen only at creation and is immutable",
        "The agent needs the AzureRbac (Entra) authorization scheme - AgentBlueprint is not supported for routines",
        "Not available for workflow agents; customer-managed keys are not supported",
    ], theme="red", icon="managed-identity", src=[("Routines", ROUT_C)])
    f2 = Card(cw3, "Delivery and limits", [
        "Up to 5 delivery attempts per run",
        "30 seconds per downstream request",
        "A real GitHub event payload overwrites the static input",
        "Hosted agents can schedule themselves with the toolbox reminder tool",
    ], theme="yellow", icon="quotas", src=[("Use routines", ROUT_H)])
    f3 = Card(cw3, "Regions", [
        "Routines are NOT available in UK West, Switzerland West, Japan West, UAE North or Norway East",
        "Run history in the portal shows inputs, outputs, status and links to traces",
    ], theme="indigo", icon="regions", src=[("Routines", ROUT_C)])
    r, b = row(cv, 0, y2, [f1, f2, f3], gap=40)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 4
def legacy_apps(cv, y):
    y = hdr(cv, y, "4  Legacy Agent applications become the agent endpoint model",
            "Publishing used to create an ARM resource; now every agent carries its own endpoint, blueprint and identity from the start.") + 40
    Y = y
    LW_ = 1330
    NX = LW_ + 150
    NW = W - NX
    PTOP = 96                      # title + subtitle band inside both panels

    # legacy panel content (measured first so both panels can share one height)
    a = Card(LW_ - 44, "What it was", [
        "Publishing created an Agent Application: ARM resource Microsoft.CognitiveServices/accounts/projects/applications",
        "Plus a Deployment: Managed for prompt agents, Hosted for hosted agents; ONE active deployment = 100% of traffic",
        "One protocol at a time; stateless Responses at .../applications/{app}/protocols/openai",
        "Foundry Project Manager to publish; Foundry User on the application to invoke; publisher pays",
        "Not registered in the Entra Agent Registry",
    ], theme="gray", icon="app-registrations", fill="hatch", src=[("Agent applications", APPS)])
    n_ = Note(LW_ - 44, "instance_identity null = a legacy agent: shared project identity, cannot publish to Teams or Microsoft 365 through the stable endpoint, no in-place identity upgrade yet. "
                        "Check with GET {endpoint}/agents/{name}?api-version=2025-11-15-preview and the header Foundry-Features: AgentEndpoints=V1Preview.",
              kind="gotcha", title="Is this agent legacy?", src=[("Migrate Agent applications", MIGAPP)])

    # new panel content
    cw2 = (NW - 44 - 30) / 2
    b1 = Card(cw2, "Every new agent gets", [
        "A stable endpoint, live at creation",
        "A unique Entra blueprint and an instance identity",
        "Several protocols at once, not one at a time",
    ], theme="green", icon="agent", fill="hatch")
    b2 = Card(cw2, "Publishing now means distribution", [
        "Microsoft 365 and Teams distribution, portal only",
        "That page says there is no public publish API - but the REST reference has Agent Microsoft 365 Publishing operations (see the publish-and-channels canvas)",
    ], theme="green", icon="teams", fill="hatch", src=[("Migrate Agent applications", MIGAPP)])
    hh = max(b1.h, b2.h)
    t_map = Table(
        [("", 170), ("Legacy application", 400), "New agent endpoint"],
        [
            ["Resources", "Application + Deployment (ARM)", "One Agent object"],
            ["Responses route", ".../applications/{app}/protocols/openai", ".../agents/{agent}/endpoint/protocols/openai/responses"],
            ["Traffic", "ONE active deployment = 100%", "version_selector: latest or pinned"],
            ["Client roles", "Foundry User on the application", "Assigned at PROJECT scope"],
        ], w=NW - 44, theme="green", size=14, head_size=15, first_col_theme="green")
    body_h = max(a.h + 22 + n_.h, hh + 22 + t_map.h)
    PH = PTOP + body_h + 22

    with cv.panel(NX, Y, w=NW, h=PH, title="Now: the Agent object carries it all", sub="Application + Deployment collapse into the agent", theme="green", style="solid", fill="soft",
                  pad=22, title_size=26, sub_size=16) as new:
        b1.place(cv, new.ix, Y + PTOP, h=hh)
        b2.place(cv, new.ix + cw2 + 30, Y + PTOP, h=hh)
        t_map.place(cv, new.ix, Y + PTOP + hh + 22)
    with cv.panel(0, Y, w=LW_, h=PH, title="Legacy: Agent application + Deployment", sub="still works - deprecation planned, end of support not yet announced", theme="gray",
                  style="dashed", pad=22, title_size=26, sub_size=16) as old:
        a.place(cv, old.ix, Y + PTOP)
        n_.place(cv, old.ix, a.bottom + 22)
    arrow(cv, [(old.right + 10, Y + PH / 2), (new.x - 10, Y + PH / 2)], color="#2f9e44", sw=4, label="collapse into", label_size=16, label_dy=-6)
    return Y + PH + 70


# ---------------------------------------------------------------------------------------------- section 5
def optimizer(cv, y):
    y = hdr(cv, y, "5  Optimizer pointers", "Details live in the agent-lifecycle-optimizer canvas; this is only where the two entry points sit on a prompt agent.") + 40
    cw3 = (W - 2 * 40) / 3
    c1 = Card(cw3, "Optimize tab - agent optimizer", [
        "A portal wizard for prompt agents that do NOT use the Copilot harness",
        "Improves instructions, function-tool descriptions and model selection",
        "Shows a cost estimate before the run",
        "Needs a saved agent version - so the ephemeral Responses API pattern cannot use it",
    ], theme="violet", icon="gear", badge="preview", src=[("Agent optimizer overview", OPT)])
    c2 = Card(cw3, "Prompt Optimizer", [
        "The pencil-sparkle icon on the Instructions field",
        "Text only: it works on the instruction text, nothing else in the definition",
        "A separate feature from the agent optimizer wizard",
    ], theme="violet", icon="files", src=[("Agent optimizer overview", OPT)])
    c3 = Card(cw3, "Where the rest lives", [
        "The overview page says the agent optimizer covers prompt agents and hosted agents; this canvas only shows the prompt-agent entry points",
        "Prompt Optimizer regions (15), the optimizer job API and CI/CD use: see the agent-lifecycle-optimizer canvas",
    ], theme="gray", icon="learn", fill="soft", dash="dashed", src=[("What is Foundry Agent Service?", learn("agents/overview"))])
    r, b = row(cv, 0, y, [c1, c2, c3], gap=40)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 6
def migrate(cv, y):
    y = hdr(cv, y, "6  Migrate from classic agents - and switch classic off",
            "The migration tool moves code constructs, not state: runs, threads and messages are not migrated (https://aka.ms/agent/migrate/tool).") + 40
    Y = y
    # four steps
    gap = 70
    bw = (W - 3 * gap) / 4
    steps = [
        ("Compare tools", "check each classic tool's availability in the new service (table below)", "gray"),
        ("Migrate the definition", "recreate the agent: create_agent() is gone, use create_version()", "green"),
        ("Threads -> conversations, runs -> responses", "move your calls to the OpenAI client on the project", "blue"),
        ("Verify", "run the same prompts and tools; check traces", "violet"),
    ]
    boxes = [Box(bw, f"{i + 1}  {lab}", sub=sub, theme=th, h=118, size=19, sub_size=15) for i, (lab, sub, th) in enumerate(steps)]
    row(cv, 0, Y, boxes, gap=gap)
    for i in range(3):
        connect(cv, boxes[i], boxes[i + 1], a_side="right", b_side="left", sw=3)
    y2 = Y + 118 + 50

    # SDK before / after
    with cv.panel(0, y2, w=1330, title="SDK change (azure-ai-projects 2.0.0)", theme="gray", style="solid", fill="soft", pad=22, title_size=24) as sdk:
        lines = [
            "# classic - create_agent() was removed in v2.0.0",
            "agent = project.agents.create_agent(...)",
            "",
            "# new - saving a version creates the agent version",
            "project.agents.create_version(agent_name,",
            "    definition=PromptAgentDefinition(...))",
            "",
            "# conversations and responses live on the OpenAI client",
            "openai = project.get_openai_client()",
        ]
        cv.text(sdk.ix, sdk.iy + 4, "\n".join(lines), size=16, color=INK, font=MONO)
    link(cv, 0, sdk.bottom + 6, "Migrate from classic agents", MIG)

    # disable classic (left column, under the SDK panel)
    dc = Card(1330, "Disable classic agents with one tag", [
        "Tag the Azure OpenAI account with MS-AOAI-Feature-Assistants = Disabled (needs Owner or Contributor)",
        "It blocks create and update of assistants / agents, threads, runs, thread-and-run and assistant files",
        "Existing items stay readable (read-only); set the tag to Enabled to turn the classic APIs back on",
    ], theme="red", icon="policy", src=[("Disable classic agents", DIS)])
    dc.place(cv, 0, sdk.bottom + 56)

    t = Table(
        [("Tool", 420), ("Classic", 230), "New service"],
        [
            ["A2A", ("No", "red"), ("Yes (GA)", "green")],
            ["Connected Agents", ("Yes (preview)", "yellow"), ("No - use A2A", "red")],
            ["Deep Research", ("Yes (preview)", "yellow"), ("No - use the Deep Research model + web search", "red")],
            ["Image generation", ("No", "red"), ("Preview", "yellow")],
            ["MCP", ("Preview", "yellow"), ("GA", "green")],
            ["Web search", ("No", "red"), ("GA", "green")],
            ["Azure Functions", ("Yes", "green"), ("No - other pages disagree", "yellow")],
            ["AI Search, Code Interpreter, File Search, Function, Bing, OpenAPI", "same", "same"],
            ["Browser Automation, Computer Use, Fabric, SharePoint", "preview", "preview"],
        ], w=W - 1330 - 70, theme="orange", size=14, head_size=15, title="Tool availability: classic vs new (as of 2026-11-03)", title_size=22, first_col_theme="orange")
    t.place(cv, 1330 + 70, y2)
    link(cv, 1330 + 70, t.bottom + 8, "Migrate from classic agents", MIG)
    return max(dc.bottom, t.bottom + 30) + 70


# ---------------------------------------------------------------------------------------------- section 7
def gotchas(cv, y):
    y = hdr(cv, y, "7  Gotchas and where the docs disagree") + 36
    nw = (W - 2 * 40) / 3
    n1 = Note(nw, "Harness: preview, a 9-region subset, no bring-your-own model, no Foundry Memory, a conversation on every call, and no per-response delete. "
                  "Declared tools keep their own network boundaries; the egress policy covers only the shell and the harness Web tool.",
              kind="gotcha", title="Harness limits to remember", src=[("Use the Copilot harness", HARNESS)])
    n2 = Note(nw, "Incoming A2A serves v0.3 (preview) when no version is specified. Pin v1.0 (JSON-RPC only) for production, and remember there is no streaming and only text modality.",
              kind="warn", title="A2A defaults to the older version", src=[("Enable an A2A endpoint", A2A)])
    n3 = Note(nw, "Portal and VNet docs use api-version v1; the autopilot quickstart, voice azd binding and memory store API use 2025-11-15-preview. "
                  "The migrate page lists Azure Functions as unsupported in the new service, but the Azure Government and limits pages list it as supported.",
              kind="warn", title="Docs disagree: API versions and Azure Functions", src=[("Quotas, limits and regions", LQR)])
    r, b = row(cv, 0, y, [n1, n2, n3], gap=40)
    return b + 70


def sources_block(cv, y):
    sources(cv, 0, y, [
        ("Use the Copilot harness with prompt agents", HARNESS),
        ("Prompt agents", PA),
        ("Configure an agent", CA),
        ("Enable an Agent-to-Agent endpoint", A2A),
        ("Routines (concept)", ROUT_C),
        ("Use routines", ROUT_H),
        ("Create or update a routine (REST)", ROUT_R),
        ("Agent applications (legacy)", APPS),
        ("Migrate Agent applications to agent endpoints", MIGAPP),
        ("Migrate from classic agents", MIG),
        ("Disable classic agents", DIS),
        ("Agent optimizer overview", OPT),
        ("Quotas, limits and regions", LQR),
        ("Agent object schema (REST reference)", REST),
    ], w=W, cols=3)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Prompt agents, part 2",
                                "Copilot harness (preview), incoming A2A (preview), routines (preview), legacy applications, the optimizer and migrating from classic  |  as of 2026-11-03",
                                icon="foundry", w=W)
    y = glance(cv, bottom + 34)
    y = harness(cv, y + 20)
    y = a2a(cv, y)
    y = routines(cv, y)
    y = legacy_apps(cv, y)
    y = optimizer(cv, y)
    y = migrate(cv, y)
    y = gotchas(cv, y)
    sources_block(cv, y)
