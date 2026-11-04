"""Microsoft 365 / Fabric / event-driven integration - part 2: the autopilot lifecycle as a swimlane, routines, the Azure Functions
queue pattern and Logic Apps, what survives network isolation, design decisions, gotchas and the documented Well-Architected guidance."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme
from generator.xd.blocks import draw_mark

META = dict(
    id="ra-m365-fabric-integration-part-2",
    title="Microsoft 365, Fabric and event-driven integration: autopilots, routines and operations",
    section="3", group="Reference architectures", order=6.5,
    description="Part 2: the autopilot lifecycle as a four-lane swimlane, routines, the Azure Functions queue pattern, Logic Apps, which integrations survive "
                "network isolation, design decisions, gotchas and the documented Well-Architected guidance.",
    tags=["autopilot", "agent-365", "routines", "logic-apps", "azure-functions", "network-isolation"],
)

W = 3300
ASOF = "as of 2026-11-03"
GRN, RED, GRY, INKC, IND, ORG = "#2f9e44", "#e03131", "#868e96", "#1e1e1e", "#3b5bdb", "#e8590c"

# ----------------------------------------------------------------------------------------------------- citations
S_PUB = ("Publish an agent to Microsoft 365 Copilot and Teams", learn("agents/how-to/publish-copilot"))
S_PUBVNET = ("Publish from a network-isolated project", learn("agents/how-to/publish-copilot-virtual-network"))
S_A365 = ("Agent 365 integration", learn("agents/concepts/agent-365-integration"))
S_A365PERM = ("Grant Agent 365 permissions", learn("agents/how-to/grant-agent-365-permissions"))
S_AUTO = ("Autopilot overview", learn("agents/concepts/autopilot-overview"))
S_AUTOLC = ("Autopilot lifecycle", learn("agents/concepts/autopilot-lifecycle"))
S_AUTOQS = ("Build your first autopilot", learn("agents/how-to/agent-365"))
S_ROUT = ("Routines", learn("agents/concepts/routines"))
S_FIQ = ("Fabric IQ tool", learn("agents/how-to/tools/fabric-iq"))
S_FDA = ("Fabric data agent tool", learn("agents/how-to/tools/fabric"))
S_FUNC = ("Azure Functions tool", learn("agents/how-to/tools/azure-functions"))
S_WORKIQ = ("Work IQ tool", learn("agents/how-to/tools/work-iq"))
S_SP = ("SharePoint tool", learn("agents/how-to/tools/sharepoint"))
S_AUTHZ = ("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))
S_TOOLAUTH = ("Tool authentication", learn("agents/how-to/tools/tool-authentication"))
S_LA1 = ("Automate Foundry agents with Logic Apps workflows", learn("azure/logic-apps/automate-foundry-agents-with-workflows", base=""))
S_LA2 = ("Add agent tools: connector actions in Logic Apps", learn("azure/logic-apps/add-agent-tools-connector-actions", base=""))
S_ALZ = ("Baseline Foundry chat in an Azure landing zone",
         learn("ai-ml/architecture/baseline-microsoft-foundry-landing-zone", base="azure/architecture"))
S_PRIV = ("Configure private link for Foundry", learn("how-to/configure-private-link"))


# ----------------------------------------------------------------------------------------------------- helpers
def chapter(cv, y, text, sub=None):
    _, b = section_header(cv, 0, y, text, sub=sub, size=34, w=W, sub_size=17)
    return b + 30


def zone(cv, x, y, w, h, title=None, *, theme="indigo", sub=None, style="dotted", fill="none", icon=None, title_size=22,
         sub_size=15, pad=16, sw=2, icon_size=30):
    """Explicit-size boundary drawn BEFORE its children."""
    th = get_theme(theme)
    bg, fs = "transparent", "solid"
    if fill == "hatch":
        bg, fs = th.fill, "hachure"
    elif fill == "solid":
        bg, fs = th.fill, "solid"
    elif fill == "soft":
        bg, fs = th.soft, "solid"
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=bg, style=fs, sw=sw, dash=style)
        tx = x + pad
        if icon:
            place_icon(cv, icon, x + pad, y + pad * 0.5, icon_size)
            tx += icon_size + 10
        if title:
            t = cv.text(tx, y + pad * 0.7, title, size=title_size, color=th.deep)
            if sub:
                cv.text(tx, t.bottom + 2, sub, size=sub_size, color=MUTED)


def pill(cv, x, y, text, th="indigo", size=12, right=False, pad=7, solid=True):
    t = get_theme(th)
    tw, hh = metrics.text_size(text, size)
    w, h = tw + 2 * pad, hh + 6
    if right:
        x -= w
    with cv.group():
        cv.rect(x, y, w, h, stroke=t.stroke, fill=t.fill if solid else "transparent", style="solid", sw=1.5, rough=0)
        cv.text(x + pad, y + 3, text, size=size, color=t.deep)
    return w, h


def chips_row(cv, x, y, items, max_w, size=13, gap=8, center=False):
    """Rows of (label, theme) pills starting at x (or centered on x); returns bottom y."""
    rows, cur, cw = [], [], 0.0
    for lab, th in items:
        w = metrics.text_size(lab, size)[0] + 14
        if cur and cw + gap + w > max_w:
            rows.append((cur, cw))
            cur, cw = [], 0.0
        cw += (gap if cur else 0) + w
        cur.append((lab, th, w))
    if cur:
        rows.append((cur, cw))
    yy = y
    for r, rw in rows:
        xx = x - rw / 2 if center else x
        for lab, th, w in r:
            pill(cv, xx, yy, lab, th, size)
            xx += w + gap
        yy += metrics.text_size("Ag", size)[1] + 6 + 5
    return yy


ID_TH, NET_PRIV, NET_PUB, NET_FILT, ST_PRE, ST_DEP = "red", "indigo", "orange", "yellow", "violet", "red"


# ----------------------------------------------------------------------------------------------------- 0 title + glance
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Microsoft 365, Fabric and event-driven integration - autopilots, routines and operations",
        f"Part 2: the autopilot lifecycle, what triggers an agent, what survives network isolation, the decisions and the traps - {ASOF}. "
        "Part 1 has the map, the identity of every hop and publishing to Teams", w=W)
    y = bottom + 34
    gap = 30
    gw = (W - 4 * gap) / 5
    items = [
        ("Autopilot = blueprint + hires", "publish a blueprint from a hosted agent; managers hire instances, one licence each", "agent", "green"),
        ("Block is easy, unblock is not", "anyone can block an autopilot; only a tenant admin can unblock; offboarding is irreversible", "conditional-access", "red"),
        ("Routines: one trigger, one action", "timer, recurring (min 5 minutes) or event; 5 attempts, 30 s timeout", "scheduler", "violet"),
        ("Logic Apps and Fabric data agent: not under isolation", "Functions and routines are; Fabric IQ is partial", "logic-apps", "orange"),
        ("Fabric data agent tool: 2026-11-06", "deprecation scheduled; migrate to the Fabric IQ tool", "fabric", "cyan"),
    ]
    boxes = [Box(gw, a, sub=b, icon=ic, icon_pos="left", theme=t, h=128, size=18, sub_size=13) for a, b, ic, t in items]
    row(cv, 0, y, boxes, gap=gap)
    return y + 128 + 56


# ----------------------------------------------------------------------------------------------------- 1 autopilot
def _autopilot(cv, y):
    y = chapter(cv, y, "1  Autopilots: an agent identity plus an Entra agent user account",
                f"The lifecycle as a swimlane: who does what, in order ({ASOF}); Frontier preview enrolment and Agent 365 terms are prerequisites")
    gap = 40
    bw = (W - 2 * gap) / 3
    styles = [
        ("Assistive", "acts on behalf of the user (OBO)", "user", "blue"),
        ("Background service", "app-only identity; no Microsoft 365 actions", "gear", "gray"),
        ("Autopilot", "acts as itself: agent identity + an Entra agent user (mailbox, calendar, Teams, org chart)", "agent", "green"),
    ]
    sb = [Box(bw, a, sub=b, icon=ic, icon_pos="left", theme=th, h=100, size=20, sub_size=14, icon_size=40) for a, b, ic, th in styles]
    row(cv, 0, y, sb, gap=gap)
    cv.text(0, y + 112, "Identity defines the type, not capabilities. You build a blueprint (hosted agents only); managers hire instances, one blueprint to many instances.",
            size=15, color=MUTED)
    y += 160

    # ---- steps (measured first so every lane has the same height)
    steps = [
        (0, "Provision", [
            "azd provision creates the Foundry account + project, model deployment, ACR, Application Insights + Log Analytics and the role assignments",
            "Needs Owner, or Contributor + Role Based Access Control Administrator at resource-group scope",
        ], "blue"),
        (1, "Build the blueprint", [
            "Container -> ACR -> hosted agent + first version",
            "Foundry auto-creates the agent identity blueprint and an agent identity",
            "Needs Foundry User on the project + AcrPush or Container Registry Repository Writer on the registry",
        ], "green"),
        (1, "Publish the blueprint", [
            "POST {project_endpoint}/agents/<agent>/microsoft365/publish?api-version=2025-11-15-preview (token audience https://ai.azure.com)",
            "publishAsAutopilot: true, publishScope: Tenant, useAgenticUserTemplate: true, plus the agenticUserTemplate (activityProtocol)",
            "Each publish needs a new version number",
        ], "green"),
        (2, "Approve", [
            "M365 admin center > Agents > All agents > Requests (Pending activate): Global Administrator or AI Administrator",
            "Wizard: publish to users (activate: none, all users, or the hiring scope), apply the policy template (shows licences left), accept permissions (grant admin consent)",
            "Registry tab then shows Available",
        ], "red"),
        (3, "Hire an instance", [
            "Teams: Apps > Agents for your team (or Copilot: Agents > Agents for your team) > Create instance",
            "Name up to 32 characters, alias, domain, manager; asynchronous, and you become the manager",
            "Consumes one licence and creates the instance's own agent identity + agent user account",
        ], "teal"),
        (3, "Operate", [
            "Onboard: audience, listening scope, messaging scope, access, source of truth",
            "Anyone can block; only a tenant admin can unblock",
            "Consent governs the token; group membership and roles govern the account",
        ], "teal"),
        (3, "Offboard, retire", [
            "Offboarding is irreversible; then retire or delete",
            "Deleting the Azure resources does NOT remove hired instances: retire the blueprint with the admin",
        ], "teal"),
    ]
    LABEL_W = 190
    x0 = LABEL_W + 22
    SW = 380
    pitch = (W - x0 - SW) / 6
    cards = [Card(SW, f"{n + 1}  {t}", body, theme=th, fill="soft", title_size=19, body_size=14, pad=14, gap=4)
             for n, (li, t, body, th) in enumerate(steps)]
    ch = max(c.h for c in cards)
    LH = ch + 28
    lanes = [("Azure administrator", "blue"), ("Developer", "green"), ("Tenant administrator", "red"), ("Manager", "teal")]
    placed = []
    for li, (nm, th) in enumerate(lanes):
        ly = y + li * (LH + 10)
        zone(cv, 0, ly, W, LH, theme=th, style="dotted", fill="none", sw=1.5)
        Box(LABEL_W, nm, theme=th, h=LH - 20, size=19, fill="solid").place(cv, 10, ly + 10)
    for i, c in enumerate(cards):
        li = steps[i][0]
        ly = y + li * (LH + 10)
        c.place(cv, x0 + i * pitch, ly + 14, h=ch)
        placed.append(c)
    for i, (a, b) in enumerate(zip(placed, placed[1:])):
        same = steps[i][0] == steps[i + 1][0]
        connect(cv, a, b, a_side="right", b_side="left" if same else "top", route="straight" if same else "elbow", sw=3,
                color=get_theme(steps[i + 1][3]).stroke)
    yb = y + 4 * (LH + 10)
    # ---- the cards under the swimlane
    cw = (W - 2 * gap) / 3
    c1 = Card(cw, "Roles in the lifecycle", [
        "Azure administrator, Developer, Tenant administrator and Manager; plus an executive sponsor and an access manager",
        "Autopilot controls: block and unblock, sponsor, access manager; Conditional Access and identity governance through Entra Agent ID",
    ], theme="red", icon="managed-identity", src=[S_AUTO, S_AUTOLC])
    c2 = Card(cw, "Licensing", [
        "Frontier preview enrolment + Agent 365 terms; at least one Microsoft 365 Copilot or Agent 365 licence (including E7)",
        "Each instance consumes one Agent 365 Frontier licence (25-seat preview subscription) because each creates an agent user account",
        "! With no free seat the build succeeds and instance creation fails later",
    ], theme="yellow", icon="cost-management", badge="preview", src=[S_AUTOQS, S_AUTO])
    c3 = Card(cw, "Permissions along the way", [
        "Provision: Owner, or Contributor + Role Based Access Control Administrator",
        "Build: Foundry User + AcrPush / Container Registry Repository Writer; publish: Foundry User",
        "Approve: Global Administrator or AI Administrator; hire: membership in the hiring scope",
    ], theme="red", icon="key-vault", src=[S_AUTOQS])
    r, b = row(cv, 0, yb + 24, [c1, c2, c3], gap=gap)
    return b + 60


# ----------------------------------------------------------------------------------------------------- 2 event driven
def _events(cv, y):
    y = chapter(cv, y, "2  What triggers an agent: routines, Azure Functions and Logic Apps",
                f"Three ways to run an agent without a person typing ({ASOF})")
    gap = 40
    zw = (W - 2 * gap) / 3
    ZH = 780

    def chain(x, y0, labels, theme, w, *, h=86, gap_=40, size=15):
        bxs = []
        yy = y0
        for lab, sub in labels:
            b = Box(w, lab, sub=sub, theme=theme, h=h, size=size, sub_size=13).place(cv, x, yy)
            bxs.append(b)
            yy = b.bottom + gap_
        for a_, b_ in zip(bxs, bxs[1:]):
            connect(cv, a_, b_, a_side="bottom", b_side="top", sw=2.5, color=get_theme(theme).stroke)
        return bxs

    # ---- routines
    zone(cv, 0, y, zw, ZH, "Routines: one trigger + one action", theme="violet", style="solid", fill="soft", sw=2.5, title_size=24, icon="scheduler",
         icon_size=34, pad=18, sub="dispatch flow")
    rb = chain(24, y + 84, [
        ("1  Trigger fires", "timer, recurring (>= 5 min) or event: github_issue; custom with the teams provider for channel messages (connector-namespace connection)"),
        ("2  Routine service gets a token", "Foundry audience: the agent identity (default) or the creator identity (opt-in at create time, permanent)"),
        ("3  Calls the agent endpoint", "Responses or Invocations API; the endpoint must still accept AzureRbac / Entra (AgentBlueprint is unsupported)"),
        ("4  Delivery", "up to 5 attempts, 30 s timeout per request"),
        ("5  Agent runs", "prompt or hosted agent; hosted agents can also schedule their own reminders with the toolbox reminder tool"),
    ], "violet", zw - 48, h=96, gap_=28)
    cy_ = rb[-1].bottom + 18
    chips_row(cv, 24, cy_, [("VNet projects supported", NET_PRIV), ("no CMK", "gray"), ("no workflow agents", "gray"), ("AgentBlueprint scheme unsupported", "gray"),
                            ("not in UK West, Switzerland West, Japan West, UAE North, Norway East", NET_PUB)], zw - 48)
    cv.text(24, y + ZH - 22, f"Learn: Routines ({ASOF})", size=12, color=LINK, link=S_ROUT[1])

    # ---- functions
    fx = zw + gap
    zone(cv, fx, y, zw, ZH, "Azure Functions tool: the queue pattern", theme="orange", style="solid", fill="soft", sw=2.5, title_size=24, icon="functions",
         icon_size=34, pad=18, sub="agent -> queue -> function -> queue -> agent")
    fb = chain(fx + 24, y + 84, [
        ("1  Agent tool call", "writes a message to the input Storage queue; project MI holds Storage Queue Data Contributor"),
        ("2  Input queue", "Azure Storage queue in the standard setup's storage"),
        ("3  Queue-triggered function", "Flex Consumption recommended: scale to zero, VNet identity-based"),
        ("4  Output queue", "the function's MI also holds Storage Queue Data Contributor"),
        ("5  Agent continues", "reads the output queue and carries on"),
    ], "orange", zw - 48, h=96, gap_=28)
    chips_row(cv, fx + 24, fb[-1].bottom + 18, [("standard agent setup only", ID_TH), ("not available in a toolbox", "gray"), ("VNet supported", NET_PRIV)], zw - 48)
    cv.text(fx + 24, y + ZH - 22, f"Learn: Azure Functions tool ({ASOF})", size=12, color=LINK, link=S_FUNC[1])

    # ---- logic apps
    lx = 2 * (zw + gap)
    zone(cv, lx, y, zw, ZH, "Azure Logic Apps (Standard) - preview", theme="indigo", style="solid", fill="soft", sw=2.5, title_size=24, icon="logic-apps",
         icon_size=34, pad=18, sub="three modes")
    modes = [
        ("i", "Workflow -> Agent action -> Foundry agent", ["Inside a workflow, the Agent action uses a Foundry project as the agent model source"], "blue"),
        ("ii", "Autonomous agent in Logic Apps", ["Started by an event or a schedule, across 1,400+ connectors"], "green"),
        ("iii", "Workflow or connector as an agent tool", [
            "A workflow exposed as a tool must start with a Request trigger and end with a Response action",
            "Connector actions as tools through an MCP server registered in the Azure portal wizard; limited to managed connectors without OAuth2 and a single connector",
            "Appears in the Foundry portal 'Logic app connectors' registry"], "orange"),
    ]
    my = y + 84
    for tag, title, body, th in modes:
        c = Card(zw - 48, f"({tag})  {title}", body, theme=th, fill="soft", title_size=19, body_size=14, pad=14)
        c.place(cv, lx + 24, my)
        my = c.bottom + 20
    chips_row(cv, lx + 24, my, [("not supported under Foundry network isolation", NET_PUB), ("built-in actions can VNet-integrate", NET_PRIV),
                                ("low-code migration target for retiring Workflows", ST_DEP)], zw - 48)
    cv.text(lx + 24, y + ZH - 22, f"Learn: Logic Apps and Foundry agents ({ASOF})", size=12, color=LINK, link=S_LA1[1])
    return y + ZH + 60


# ----------------------------------------------------------------------------------------------------- 3 isolation support
def _isolation(cv, y):
    y = chapter(cv, y, "3  What survives network isolation",
                f"Support for a private Foundry, per integration ({ASOF}); the tool lanes for the baseline are in the canvas 'Baseline chat: decisions, operations and gotchas'")
    rows = [
        [("Publish to Teams / Microsoft 365 Copilot", "blue"), PARTIAL, "Public, source-IP-filtered Activity route, enabled manually through REST (fail-closed); portal publish unsupported",
         "Responses, A2A and MCP stay private; Microsoft 365 has no private connectivity; Copilot Studio uses a delegated private path"],
        [("Work IQ tool (preview)", "blue"), PARTIAL, "Public workiq.svc.cloud.microsoft; passes through the data proxy in a BYO VNet but is not private",
         "Not supported in network-isolated toolbox projects"],
        [("SharePoint tool (preview)", "teal"), PARTIAL, "Public endpoint even in an isolated Foundry", "Can be blocked with Azure Policy"],
        [("Fabric IQ tool (preview)", "cyan"), PARTIAL, "Over MCP: data agents tenant + workspace private link, ontologies tenant-level, Power BI semantic models public only",
         "Published items, F2+ or P1+ capacity, same region and tenant"],
        [("Fabric data agent tool", "cyan"), CROSS, "Fabric must have public network access", "Deprecation scheduled for 2026-11-06"],
        [("Azure Logic Apps (preview)", "indigo"), CROSS, "Not supported under Foundry network isolation", "Built-in actions can VNet-integrate on their own"],
        [("Azure Functions tool", "orange"), CHECK, "VNet supported: Flex Consumption, identity-based", "Standard agent setup only; not in a toolbox"],
        [("Routines", "violet"), CHECK, "VNet projects supported", "No CMK; no workflow agents; five regions unavailable"],
        [("Agent 365 telemetry (hosted agents)", "indigo"), PARTIAL, "Outbound TCP 443 to agent365.svc.cloud.microsoft (or the AzureFrontDoor.Frontend service tag)",
         "Opt out with a365LoggingEnabled=false on the Foundry resource"],
    ]
    t = Table([("Integration", 400), ("Behind the VNet", 150), ("Network path", 1300), ("Notes", 0)], rows, w=W, theme="indigo", size=14, head_size=15,
              title="Network-isolation support per integration", title_size=22, align=["left", "center", "left", "left"])
    t.place(cv, 0, y)
    return t.bottom + 60


# ----------------------------------------------------------------------------------------------------- 4 decisions
def _decisions(cv, y):
    y = chapter(cv, y, "4  Design decisions and trade-offs",
                f"Each row is a fork; the right-hand column is what the documentation says ({ASOF})")
    rows = [
        [("Publish audience", "blue"), "Just you: BotServiceRbac", "Organization: BotServiceTenant",
         "RBAC = per-user Azure permission, no approval; Tenant = a fixed tenant rule + M365 admin center approval"],
        [("Private Foundry + Microsoft 365", "red"), "Accept the public, IP-filtered Activity route (REST publish)", "Don't publish to Microsoft 365; use Copilot Studio's delegated private path",
         "A private foundation doesn't make every integration private; don't use the Activity route if public agent ingress is prohibited"],
        [("Microsoft 365 knowledge", "teal"), "Work IQ: broad M365 context, A2A, OBO, public", "SharePoint tool (Retrieval API, one per agent, public, not in Teams) or the Foundry IQ SharePoint source (indexed ACL-aware, or remote)",
         "Delegated-only everywhere; choose by control (indexed) versus freshness (remote, Work IQ)"],
        [("Fabric grounding", "cyan"), "Fabric data agent tool (deprecation scheduled 2026-11-06)", "Fabric IQ (preview)",
         "Migrate now; semantic model = public only; ontology = tenant-level private link only"],
        [("Agent identity style", "green"), "Assistive (OBO)", "Background service (app-only) or autopilot (own user account)",
         "Identity defines the type; autopilots need a licence per instance"],
        [("Event-driven runtime", "violet"), "Routines: one trigger + one action, agent identity", "Logic Apps (1,400+ connectors, preview, unsupported under isolation) or the Functions queue tool",
         "Routines are unavailable in five regions; Logic Apps is Foundry's low-code migration target for Workflows"],
        [("Function integration", "orange"), "Azure Functions tool: queue pattern, standard setup, not in a toolbox", "OpenAPI tool or Logic Apps",
         "Both managed identities need Storage Queue Data Contributor"],
    ]
    t = Table([("Decision", 300), ("Option A", 780), ("Option B", 900), ("Documented guidance", 0)], rows, w=W, theme="grape", size=14, head_size=15,
              title="Decisions, options and guidance", title_size=22)
    t.place(cv, 0, y)
    return t.bottom + 60


# ----------------------------------------------------------------------------------------------------- 5 gotchas
def _gotchas(cv, y):
    y = chapter(cv, y, "5  Eleven gotchas to know before you ship",
                f"Collected from the pages read ({ASOF}); most of these are preview behaviour and may change")
    gap = 36
    cw = (W - 3 * gap) / 4
    items = [
        ("gotcha", "Fabric data agent deprecation", "Scheduled for 2026-11-06. The Fabric data agent and Logic Apps are unsupported under network isolation; Fabric IQ is partial.", [S_FDA, S_FIQ]),
        ("gotcha", "The Microsoft 365 path is public", "IP-filtered and fail-closed; M365 has no private connectivity. No streaming or citations; uploads and image generation fail in M365 (they work in Teams).", [S_PUBVNET]),
        ("gotcha", "Publishing needs a separate role", "Azure Bot Service Contributor is separate from the Foundry roles and is the usual cause of failed publishes.", [S_PUB]),
        ("gotcha", "SharePoint and Work IQ are public", "The SharePoint tool breaks when published to Teams and is public even in an isolated Foundry; Work IQ is public and not allowed in network-isolated toolbox projects.", [S_SP, S_WORKIQ]),
        ("warn", "Work IQ setup is admin-heavy", "Needs a Global Administrator (PIM); connection fields are immutable after creation; billed in Copilot Credits.", [S_WORKIQ]),
        ("warn", "Autopilot licensing", "Each hire consumes a licence (25-seat preview subscription). With no free seat the build succeeds and instance creation fails later.", [S_AUTOQS]),
        ("warn", "Block, unblock and offboard", "Anyone can block, only a tenant admin can unblock; offboarding is irreversible; consent governs the token, not data access.", [S_AUTOLC]),
        ("warn", "Autopilot publish", "Needs a new version number per publish, and publishScope must be Tenant.", [S_AUTOQS]),
        ("warn", "Routines are permanent and regional", "The creator-identity choice can't change; the endpoint must keep AzureRbac / Entra; unavailable in UK West, Switzerland West, Japan West, UAE North, Norway East; no CMK, no workflow agents.", [S_ROUT]),
        ("warn", "Agent 365 data and telemetry", "Foundry stores data in the Azure region, Agent 365 in the Entra tenant geography; hosted-agent telemetry needs the OtelWrite role (Global or Application Administrator) and outbound 443 to agent365.svc.cloud.microsoft.", [S_A365, S_A365PERM]),
        ("warn", "Fabric IQ prerequisites", "Needs published items, F2+ or P1+ capacity, the same region and tenant; not available where Power BI is the only Fabric workload; results move across regions if they differ.", [S_FIQ]),
    ]
    notes = [Note(cw, text, kind=k, title=title, size=14, src=src) for k, title, text, src in items]
    r, b = grid(cv, 0, y, notes, 4, gap_x=gap, gap_y=26)
    return b + 60


# ----------------------------------------------------------------------------------------------------- 6 well-architected
def _pillars(cv, y):
    y = chapter(cv, y, "6  Documented Well-Architected guidance",
                f"Thin by nature: only what the pages read state ({ASOF})")
    gap = 30
    cw = (W - 4 * gap) / 5
    cards = [
        Card(cw, "Security", [
            "Delegated (OBO) access preserves per-user permissions and sensitivity labels",
            "Admin consent governs token scope only",
            "Fail-closed IP filtering for the Microsoft 365 route",
            "Entra-only auth on endpoints (no keys); secrets in Key Vault",
            "Autopilot controls: block and unblock, sponsor, access manager",
        ], theme="red", icon="defender", src=[S_AUTHZ, S_TOOLAUTH]),
        Card(cw, "Reliability", [
            "Routine delivery: 5 attempts, 30 s timeout",
            "Queue-decoupled Functions integration with scale-to-zero Flex Consumption",
            "Keep Fabric sources in the same region as the data agent",
        ], theme="orange", icon="service-health", src=[S_ROUT, S_FUNC]),
        Card(cw, "Cost optimization", [
            "Copilot Credits for the Work IQ API path",
            "A per-instance Agent 365 licence for autopilots",
            "Microsoft 365 Copilot licence or pay-as-you-go for the SharePoint tool",
            "Fabric F2+ capacity",
        ], theme="yellow", icon="cost-management", src=[S_WORKIQ, S_SP, S_FIQ]),
        Card(cw, "Operational excellence", [
            "Agent 365 registry and visualization",
            "Version-pinned agent endpoint (version_selector)",
            "azd-driven provisioning and publishing",
            "App-role verification steps for Agent 365 telemetry",
        ], theme="violet", icon="monitor", src=[S_A365, S_AUTOQS]),
        Card(cw, "Performance efficiency", [
            "Same-region Fabric and Foundry",
            "Minimum 5-minute recurrence for routines",
            "Instance creation for autopilots is asynchronous",
        ], theme="blue", icon="metrics", src=[S_ROUT, S_FIQ]),
    ]
    r, b = row(cv, 0, y, cards, gap=gap)
    return b + 60


def _sources(cv, y):
    sources(cv, 0, y, [S_PUB, S_PUBVNET, S_A365, S_A365PERM, S_AUTO, S_AUTOLC, S_AUTOQS, S_ROUT, S_FIQ, S_FDA, S_FUNC, S_WORKIQ, S_SP, S_AUTHZ, S_TOOLAUTH, S_LA1,
                       S_LA2, S_ALZ], w=W, cols=3)


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _autopilot(cv, y)
    y = _events(cv, y)
    y = _isolation(cv, y)
    y = _decisions(cv, y)
    y = _gotchas(cv, y)
    y = _pillars(cv, y)
    _sources(cv, y)
