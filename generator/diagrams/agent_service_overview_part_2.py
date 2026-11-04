"""Foundry Agent Service overview, part 2: Basic / Standard / Standard + BYO VNet setup, where state lives and the roles it needs,
capability hosts (retained for reference) and capability settings, the real limits and error codes, regions, Azure Government,
data privacy and the no-built-in-DR note."""
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS

META = dict(
    id="agent-service-overview-part-2", title="Agent Service: setup, limits, regions and Azure Government", section="2", group="Agent Service", order=10.5,
    description="Agent Service reference sheet: Basic vs Standard vs Standard + BYO VNet, where state lives, capability hosts and settings, every limit and error code, 30 regions, hosted-session quotas and the Azure Government matrix.",
    tags=["agent-service", "setup", "limits", "regions", "azure-government"],
)

W = 3000
OV = learn("agents/overview")
ENV = learn("agents/environment-setup")
STD = learn("agents/concepts/standard-agent-setup")
CAP = learn("agents/concepts/capability-hosts")
BYO = learn("agents/how-to/use-your-own-resources")
VNET = learn("agents/how-to/virtual-networks")
LQR = learn("agents/concepts/limits-quotas-regions")
GOV = learn("agents/concepts/azure-government")
DEEP = learn("agents/concepts/agents-networking-deep-dive")
FAQ = learn("agents/faq")
DR = learn("how-to/agent-service-disaster-recovery")
PRIV = learn("responsible-ai/agents/data-privacy-security")


# ---------------------------------------------------------------------------------------------- helpers
def badge_on(cv, blk, kind, inset=14, up=13):
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def ypt(blk, y):
    return (y - blk.y) / blk.h


def hdr(cv, y, text, sub=None):
    return section_header(cv, 0, y, text, sub=sub, size=34, sub_size=17, w=W)[1]


def link(cv, x, y, label, url):
    return cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)


# ---------------------------------------------------------------------------------------------- section 1
def setup_modes(cv, y):
    y = hdr(cv, y, "1  Choose your environment setup",
            "Three modes, each one adds a layer: Basic keeps agent state in Microsoft-managed storage; Standard moves it into your own resources; Standard + BYO VNet also isolates outbound traffic.") + 40
    Y = y
    PW_ = 880
    GX = (W - 3 * PW_) / 2
    xs = [0, PW_ + GX, 2 * (PW_ + GX)]

    def panel_cards(x, title, sub, theme_name, cards, dashed=False):
        with cv.panel(x, Y, w=PW_, title=title, sub=sub, theme=theme_name, style="dashed" if dashed else "solid", fill="soft", pad=22, title_size=28, sub_size=16) as p:
            col(cv, p.ix, p.iy + 8, cards, gap=22)
        return p

    cw = PW_ - 44
    basic = [
        Card(cw, "Resources", [
            "A Foundry account, a project and a model deployment (the template deploys GPT-4.1)",
            "A Microsoft-managed Key Vault is used by default",
            "Authentication with managed identity",
        ], theme="blue", icon="foundry", fill="hatch"),
        Card(cw, "Where agent state lives", [
            "Microsoft-managed, logically separated storage (the default)",
            "Microsoft-managed keys only - no customer-managed keys",
        ], theme="cyan", icon="storage", fill="hatch"),
        Card(cw, "What you get", [
            "Compatible with OpenAI Assistants: the same tools and capabilities",
            "Plus non-OpenAI models and tools such as Azure AI Search and Bing",
            "Get started without managing resources",
        ], theme="green", icon="agent", fill="hatch"),
    ]
    std = [
        Card(cw, "Everything in Basic, plus your own resources", [
            "Single-tenant, in your Azure tenant:",
            "  Azure Storage - files",
            "  Azure AI Search - vector stores",
            "  Azure Cosmos DB for NoSQL - conversations and agent definitions",
            "Key Vault, and optionally Application Insights",
        ], theme="cyan", icon="cosmos", fill="hatch"),
        Card(cw, "Control", [
            "All conversation history, files and vector stores stay in your resources",
            "Customer-managed keys (CMK) are supported; preview features may not support CMK",
        ], theme="red", icon="key-vault", fill="hatch"),
        Card(cw, "Sizing and hygiene", [
            "Cosmos DB needs at least 3,000 RU/s (1,000 RU/s per container x 3 containers); multiply by the number of projects. Too few RU/s fails provisioning",
            "Use separate Foundry accounts and projects for Standard and Basic - avoid mixing them in one account",
        ], theme="yellow", icon="quotas", fill="hatch"),
    ]
    vn = [
        Card(cw, "Everything in Standard, plus private outbound", [
            "Private network isolation of agent OUTBOUND traffic - Standard setup only",
            "Container injection into a delegated subnet (Microsoft.App/environments)",
            "/24 recommended; /27 is the minimum but risky",
            "Foundry resource and VNet must be in the same region",
        ], theme="indigo", icon="vnet", fill="hatch"),
        Card(cw, "Inbound", [
            "Private endpoint + public network access disabled",
            "This works with every setup, including Basic",
        ], theme="indigo", icon="private-endpoint", fill="hatch"),
        Card(cw, "Hosted agents", [
            "VNet injection must be configured when the Foundry account is created",
            "A private Azure Container Registry works only for projects created after 2026-06-25",
        ], theme="green", icon="container-apps", fill="hatch"),
    ]
    p1 = panel_cards(xs[0], "Basic setup", "Microsoft-managed storage and keys", "blue", basic)
    p2 = panel_cards(xs[1], "Standard setup", "your single-tenant resources", "cyan", std)
    p3 = panel_cards(xs[2], "Standard + BYO virtual network", "your resources and your network", "indigo", vn)
    ph = max(p1.h, p2.h, p3.h)
    for p in (p1, p2, p3):
        p.el.el["height"] = round(ph, 2)
        p.h = ph
    ay = Y + 62
    arrow(cv, [(p1.right + 6, ay), (p2.x - 6, ay)], color="#0c8599", sw=4, label="+ your data", label_size=16, label_dy=-4)
    arrow(cv, [(p2.right + 6, ay), (p3.x - 6, ay)], color="#3b5bdb", sw=4, label="+ your network", label_size=16, label_dy=-4)
    y2 = Y + ph + 50

    # compare matrix + samples
    t = Table(
        [("Use case", 640), ("Basic", 170), ("Standard, public networking", 330), ("Standard, private networking", 330)],
        [
            ["Get started quickly without managing resources", CHECK, DASH, DASH],
            ["All conversation history, files and vector stores in your own resources", DASH, CHECK, CHECK],
            ["Customer-managed keys (CMK)", DASH, CHECK, CHECK],
            ["Private network isolation (bring your own virtual network)", DASH, DASH, CHECK],
        ], w=1470, theme="cyan", size=15, head_size=15, title="Compare setup options (as of 2026-11-03)", title_size=22, align=["left", "center", "center", "center"])
    t.place(cv, 0, y2)
    link(cv, 0, t.bottom + 8, "Set up your environment for Foundry Agent Service", ENV)
    cx = 1530
    d = Card(W - cx, "Deployment options and defaults", [
        "Bicep and Terraform samples: 40-basic-agent-setup, 41-standard-agent-setup, 42-... and 43-... (both with customization), 15-private-network-standard-agent-setup; the Terraform BYO VNet variant is 15b-...-byovnet",
        "Template defaults: model gpt-4.1, format OpenAI, version 2025-04-14, GlobalStandard, location eastus - do not change modelFormat (Azure OpenAI models only)",
        "Autodeploy finishes in about 5-10 minutes; a manual Standard setup takes about 30-45 minutes",
        "Missing quota or the Role Based Access Control Administrator role are the usual failures",
    ], theme="gray", icon="azd", icon_size=44, src=[("Standard agent setup", STD), ("Use your own resources", BYO)])
    d.place(cv, cx, y2)
    return max(t.bottom + 30, d.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 2
def state_and_roles(cv, y):
    y = hdr(cv, y, "2  Standard setup: where state lives and which roles make it work",
            "What Agent Service writes into your subscription, and who needs which role (Foundry roles were renamed - the IDs did not change).") + 40
    Y = y
    svc = Box(420, "Agent Service", sub="reads the project capability host; uses the project managed identity (roles on the right)", icon="agent", icon_pos="left", theme="green", h=170, size=24, sub_size=15)
    RW_ = 1000
    cosmos = Card(RW_, "Azure Cosmos DB for NoSQL - conversations and agent definitions", [
        "At least 3,000 RU/s (provisioned or serverless); each container uses 1,000 RU/s",
        "Classic runtime containers: thread-message-store, system-thread-message-store, agent-entity-store",
        "New runtime containers: agent-definitions-v1, run-state-v1 - created when the first Responses-based agent is made",
        "Database enterprise_memory (role: Cosmos DB Built-in Data Contributor)",
    ], theme="cyan", icon="cosmos", src=[("Standard agent setup", STD)])
    store = Card(RW_, "Azure Storage - files", [
        "Blob containers <workspaceId>-azureml-blobstore and -azureml-agent",
    ], theme="cyan", icon="storage")
    search = Card(RW_, "Azure AI Search - vector stores", [
        "Vector stores, embeddings and retrieval indexes",
    ], theme="teal", icon="ai-search")
    kv = Card(RW_, "Key Vault and Application Insights", [
        "A Microsoft-managed Key Vault is used by default; Application Insights is optional",
    ], theme="red", icon="key-vault")
    cards = [cosmos, store, search, kv]
    gap = 24
    total = sum(c.h for c in cards) + gap * 3
    ry = Y
    for c in cards:
        c.place(cv, 420 + 250, ry)
        ry += c.h + gap
    svc.place(cv, 0, Y + total / 2 - svc.h / 2)
    labs = [(cosmos, "conversations + definitions"), (store, "files"), (search, "vectors"), (kv, "secrets")]
    for c, lab in labs:
        connect(cv, svc, c, a_side="right", b_side="left", route="elbow", sw=3, bind=False, bend=0.25)
        tw_, th_ = metrics.text_size(lab, 14)
        cv.text(c.x - 14 - tw_, c.cy - th_ - 5, lab, size=14, color=INK)
    # roles
    RX = 420 + 250 + RW_ + 60
    RWD = W - RX
    t_who = Table(
        [("Action", 480), "Required role"],
        [
            ["Create an account and project", ("Foundry Account Owner (subscription scope)", "red")],
            ["Standard setup: assign RBAC on Cosmos DB, Search, Storage", ("Role Based Access Control Administrator, or Owner (needs Microsoft.Authorization/roleAssignments/write)", "red")],
            ["Create and edit agents", ("Foundry User", "red")],
            ["Call agent endpoints only", ("Foundry Agent Consumer (eed3b665-ab3a-47b6-8f48-c9382fb1dad6)", "red")],
        ], w=RWD, theme="red", size=14, head_size=15, title="Who does what", title_size=22)
    t_who.place(cv, RX, Y)
    link(cv, RX, t_who.bottom + 8, "Set up your environment", ENV)
    t_rt = Table(
        [("Runtime role for the project managed identity", 700), "Scope"],
        [
            ["Cosmos DB Operator  |  Storage Account Contributor", "account level of the Cosmos DB and the Storage resources"],
            ["Search Index Data Contributor and Search Service Contributor", "the Search service"],
            ["Storage Blob Data Contributor  |  Storage Blob Data Owner", "containers <workspaceId>-azureml-blobstore  |  -azureml-agent"],
            ["Cosmos DB Built-in Data Contributor", "the enterprise_memory database (covers all its containers)"],
        ], w=RWD, theme="red", size=14, head_size=15, title="Standard-mode runtime roles", title_size=22)
    t_rt.place(cv, RX, t_who.bottom + 56)
    link(cv, RX, t_rt.bottom + 8, "Standard agent setup", STD)
    n = Note(RWD, "Hosted agents need additional permissions - see the hosted-agents canvas. A new agent identity starts with no permissions of its own.",
             kind="info", title="Hosted agents and agent identities")
    n.place(cv, RX, t_rt.bottom + 40)
    return max(Y + total, n.bottom) + 70


# ---------------------------------------------------------------------------------------------- section 3
def capability(cv, y):
    y = hdr(cv, y, "3  Capability hosts (kept for reference) and capability settings",
            "How Agent Service is told which resources hold conversations, files and vectors.") + 40
    Y = y
    note = Note(W, "The capability-hosts article now says: to declare the Azure resources Agent Service uses for agent state, vector data and files, see 'Configure agent capability settings'; "
                   "the capability-hosts article is retained for reference. Newer capability settings (ARM 2026-07-15-preview) set the same thing on the account (defaults) and on the project "
                   "(override) and cannot be changed on an existing project. Docs quirk: how-to/configure-capability-settings currently renders the same content as the environment-setup page.",
                kind="warn", title="Capability settings are the current path - capability hosts are retained for reference",
                src=[("Capability hosts", CAP), ("Set up your environment", ENV)])
    note.place(cv, 0, Y)
    Y2 = note.bottom + 40

    # diagram: account scope -> project scope -> BYO resources
    AW, PWD = 700, 1000
    with cv.panel(0, Y2, w=AW, title="Account scope", sub="Foundry account", theme="blue", style="solid", fill="soft", pad=20, title_size=24, sub_size=15) as acc:
        ach = Box(AW - 40, "Account capability host", sub="enables Agent Service at the account level; must exist before a project capability host", icon="agent", icon_pos="left",
                  theme="blue", h=130, size=19, sub_size=14)
        ach.place(cv, acc.ix, acc.iy + 6)
    PX = AW + 170
    with cv.panel(PX, Y2, w=PWD, title="Project scope", sub="this is what Agent Service reads", theme="green", style="solid", fill="soft", pad=20, title_size=24, sub_size=15) as prj:
        pch = Box(PWD - 40, "Project capability host (capabilityHostKind: Agents)", sub="REST api-version 2025-06-01 - threadStorageConnections, vectorStoreConnections, storageConnections, optional aiServicesConnections",
                  icon="agent", icon_pos="left", theme="green", h=130, size=19, sub_size=14)
        pch.place(cv, prj.ix, prj.iy + 6)
        cf = ChipFlow(["Cosmos DB connection (conversations)", "AI Search connection (vectors)", "Storage connection (files)", "Azure OpenAI connection (optional)"], PWD - 40,
                      theme="cyan", size=15, gap=10)
        cf.place(cv, prj.ix, pch.bottom + 20)
    connect(cv, ach, pch, a_side="right", b_side="left", label="no automatic inheritance of BYO resources", label_size=15, label_wrap=140, sw=3, color="#e03131", bind=False)
    RX = PX + PWD + 60
    RW_ = W - RX
    c = Card(RW_, "Constraints", [
        "One capability host per scope - a second one with another name returns 409",
        "No update: delete and recreate",
        "The account host must exist first; the project host decides what a project uses",
        "REST only - no SDK support",
    ], theme="red", icon="policy", src=[("Capability hosts", CAP)])
    c.place(cv, RX, Y2)
    link_y = max(acc.bottom, prj.bottom, c.bottom)
    # row of three cards below
    y3 = link_y + 40
    cw3 = (W - 2 * 40) / 3
    k1 = Card(cw3, "Connection properties that must be set", [
        "authType - for example AAD",
        "category - AzureStorageAccount, AzureCosmosDb or CognitiveSearch",
        "target - the service endpoint URL, not the resource ID",
        "metadata.ResourceId - the full Azure resource ID; required to resolve resources at runtime",
    ], theme="cyan", icon="api-connections", src=[("Capability hosts", CAP)])
    k2 = Card(cw3, "Permissions to create them", [
        "Contributor on the Foundry account to create capability hosts",
        "User Access Administrator or Owner to assign access to the Azure resources (Standard setup)",
        "Create the Cosmos DB, Storage and AI Search connections first (and an Azure OpenAI connection if you use your own deployments)",
    ], theme="red", icon="managed-identity", src=[("Capability hosts", CAP)])
    k3 = Card(cw3, "Voice-based agents (preview)", [
        "Standard setup stores voice conversation data in your resources, plus an extra audio copy",
        "The Microsoft-managed copy still expires after 60 days; the copy in your storage does not - manage its retention yourself",
        "Voice traces follow the connected Application Insights retention",
    ], theme="violet", icon="speech", src=[("Capability hosts", CAP)])
    r, b = row(cv, 0, y3, [k1, k2, k3], gap=40)
    badge_on(cv, k3, "preview")
    return b + 70


# ---------------------------------------------------------------------------------------------- section 4
def limits(cv, y):
    y = hdr(cv, y, "4  Limits, quotas and error codes (as of 2026-11-03)",
            "Fixed for every subscription type - only the concurrent hosted-session quota can be raised, through an Azure support request.") + 40
    Y = y
    LW_ = 1100
    t = Table(
        [("Limit", 640), ("Value", 460)],
        [
            ["Files per agent or thread", "10,000"],
            ["Max file size uploaded for prompt agents", "512 MB"],
            ["Total size of all uploaded files for agents", "300 GB"],
            ["Max file size in tokens when attaching to a vector store", "2,000,000 tokens"],
            ["Messages per thread", "100,000"],
            ["Characters of text content per message", "1,500,000"],
            ["Tools registered per agent", "128"],
            ["Versions per agent", "1,000"],
            ["Voice session duration (voice-based agents, preview)", "60 minutes"],
            ["Stored voice conversations and Microsoft-managed audio", "kept 60 days"],
        ], w=LW_, theme="yellow", size=15, head_size=16, title="Agent Service limits", title_size=22, first_col_theme="yellow")
    t.place(cv, 0, Y)
    link(cv, 0, t.bottom + 8, "Quotas and limits for Foundry Agent Service", LQR)

    # hosted sessions
    HX = LW_ + 60
    HW = 880
    s2 = Box(HW / 2 - 15, "2,000", sub="concurrent hosted agent sessions per subscription and region", theme="yellow", fill="hatch", h=150, size=44, sub_size=15)
    s1 = Box(HW / 2 - 15, "1,000", sub="in every other region where hosted agents are available", theme="yellow", fill="hatch", h=150, size=44, sub_size=15)
    s2.place(cv, HX, Y)
    s1.place(cv, HX + HW / 2 + 15, Y)
    cf = ChipFlow(["Canada Central", "East US 2", "Japan East", "North Central US", "South Africa North", "Southeast Asia", "Sweden Central"], HW, theme="yellow", size=15, gap=8)
    cf.place(cv, HX, s2.bottom + 16)
    hn = Note(HW, "The quota counts sessions across all accounts and projects in the subscription and region while their compute is provisioning or running. Idle or stopped sessions keep "
                  "their state and do not count, but resuming one needs free quota. To raise it, open an Azure support request with the subscription, region and expected sessions - "
                  "approval depends on regional capacity.", kind="key", title="What counts, and how to raise it", src=[("Quotas and limits", LQR)])
    hn.place(cv, HX, cf.y + cf.h + 20)
    # errors
    RX = HX + HW + 60
    RW_ = W - RX
    te = Table(
        [("HTTP", 70), ("Error code", 300), "What to do"],
        [
            ["400", "file_size_exceeded", "Split content into smaller files"],
            ["400", "token_limit_exceeded", "Reduce file content or split files (vector store)"],
            ["400", "message_limit_exceeded", "Create a new thread"],
            ["400", "content_size_exceeded", "Use file search for large content"],
            ["400", "tool_limit_exceeded", "Remove unused tools"],
            ["400", "UserError (version cap)", "Delete older versions, then create; terminal - do not retry the same call"],
            ["429", "rate_limit_exceeded", "Exponential backoff with jitter (model deployment throttling)"],
            ["429", "session_quota_exceeded", "Stop idle sessions, delete sessions you no longer need, or request an increase"],
            ["429", "regional_session_quota_exceeded", "Retry with backoff or use another region"],
            ["429", "subnet_exhausted", "Stop sessions you do not need or use a larger delegated subnet"],
        ], w=RW_, theme="red", size=14, head_size=15, title="Limit error reference", title_size=22)
    te.place(cv, RX, Y)
    link(cv, RX, te.bottom + 8, "Quotas and limits for Foundry Agent Service", LQR)
    return max(t.bottom + 30, hn.bottom, te.bottom + 30) + 60


# ---------------------------------------------------------------------------------------------- section 5
def regions(cv, y):
    y = hdr(cv, y, "5  Regions: 30 for the Responses API and Agents",
            "Responses API, Agent Service and private VNet support are 'Yes' in all 30; voice-based agents (preview) are 'No' in two.") + 40
    Y = y
    all30 = ["Australia East", "Brazil South", "Canada Central", "Canada East", "Central US", "East US", "East US 2", "France Central", "Germany West Central",
             "Italy North", "Japan East", "Japan West", "Korea Central", "North Central US", "Norway East", "Poland Central", "South Africa North", "South Central US",
             "Southeast Asia", "South India", "Spain Central", "Sweden Central", "Switzerland North", "Switzerland West", "UAE North", "UK South", "West Central US",
             "West Europe", "West US", "West US 3"]
    LW_ = 1700
    chips = []
    for r_ in all30:
        no_voice = r_ in ("Poland Central", "Spain Central")
        chips.append(Chip(r_, theme="red" if no_voice else "green", size=16, fill="soft" if no_voice else "solid", dash="dashed" if no_voice else "solid"))
    cf = ChipFlow(chips, LW_ - 48, gap=10)
    with cv.panel(0, Y, w=LW_, title="Responses API + Agents + private VNet: all 30 regions", sub="red dashed = no voice-based agents (preview): Poland Central and Spain Central", theme="green",
                  style="solid", fill="soft", pad=24, title_size=24, sub_size=15) as p:
        cf.place(cv, p.ix, p.iy + 6)
    link(cv, 0, p.bottom + 6, "Quotas and limits - supported regions", LQR)
    # right: cards
    RX = LW_ + 60
    RW_ = W - RX
    c1 = Card(RW_, "Region subsets (details in other canvases)", [
        "Copilot harness (preview): 9 regions - Australia East, Canada Central, Central US, Germany West Central, Japan East, Sweden Central, UK South, West Europe, West US",
        "Memory: 19 regions - see the memory canvas",
        "Prompt Optimizer: 15 regions - see the agent-lifecycle-optimizer canvas",
        "Routines: not in UK West, Switzerland West, Japan West, UAE North, Norway East",
    ], theme="indigo", icon="regions", src=[("Quotas and limits", LQR)])
    c1.place(cv, RX, Y)
    y2 = max(p.bottom + 30, c1.bottom + 30)
    cw3 = (W - 2 * 40) / 3
    g1 = Card(cw3, "Tool gaps by region", [
        "File search: not in Italy North or Brazil South",
        "Computer Use: only 9 regions (Canada Central, Central US, East US 2, Japan West, South India, Sweden Central, Switzerland West, West Central US, West Europe)",
        "Browser Automation: not in Japan West, Switzerland West or West Central US",
        "Function tool: not in Brazil South, North Central US, South Central US or West US",
    ], theme="orange", icon="toolbox", src=[("Tool support by region and model", LQR)])
    g2 = Card(cw3, "Private networking regions", [
        "The Foundry resource and its virtual network must be in the same region",
        "Cosmos DB, AI Search and Storage may sit in other regions - mind the cost",
        "Grounding with Bing Search in a private network is limited to a subset of regions (list on the limits page)",
        "Tools also depend on the model: model router, for example, supports no web search and no A2A",
    ], theme="indigo", icon="vnet", src=[("Use a virtual network with Agent Service", VNET)])
    g3 = Card(cw3, "Where data is stored", [
        "Agent Service endpoints are regional; data is stored in the same region as the endpoint",
        "Stateful data is stored at rest in the geography of the resource",
    ], theme="cyan", icon="globe", src=[("Quotas and limits", LQR), ("Data, privacy and security", PRIV)])
    r, b = row(cv, 0, y2, [g1, g2, g3], gap=40)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 6
def government(cv, y):
    y = hdr(cv, y, "6  Azure Government (US Gov Virginia and US Gov Arizona)",
            "A subset of agent types and tools. Token resource https://ai.azure.us/.default; endpoints under *.services.ai.azure.us.") + 40
    Y = y
    t = Table(
        [("Agent type", 360), ("In Azure Government", 280)],
        [
            ["Prompt agents", ("Yes", "green")],
            ["Voice-based prompt agents", ("No", "red")],
            ["Workflows", ("Preview", "yellow")],
            ["Hosted agents", ("No", "red")],
        ], w=640, theme="gray", size=15, head_size=16, title="Agent types", title_size=22, first_col_theme="gray")
    t.place(cv, 0, Y)
    TX = 700
    TW_ = W - TX
    with cv.panel(TX, Y, w=TW_, title="Tools", sub="green = yes, yellow = preview, red = no", theme="gray", style="dotted", pad=22, title_size=24, sub_size=15) as tp:
        yes = ["Code Interpreter", "File Search", "Azure AI Search", "Azure Functions", "Function calling", "MCP", "OpenAPI"]
        prev = ["Custom Code Interpreter"]
        no = ["Web search", "Bing grounding", "Image generation", "Browser automation", "Computer use", "Fabric", "SharePoint", "A2A"]
        items = [Chip(s, theme="green", size=16) for s in yes] + [Chip(s + " (preview)", theme="yellow", size=16) for s in prev] + [Chip(s, theme="red", size=16, fill="soft") for s in no]
        cf = ChipFlow(items, TW_ - 48, gap=10)
        cf.place(cv, tp.ix, tp.iy + 6)
    n = Note(W, "Workflows are listed as Preview here, while the global workflows page announces their retirement on 2026-12-01 - confirm which applies to your cloud. Preview features may not carry the FedRAMP, DoD IL5 or CJIS commitments - check before using them with regulated workloads. "
                "Azure Functions is listed as supported here and on the limits page, while the migrate page marks it unsupported in the new service.",
             kind="warn", title="Azure Government: read the fine print", src=[("Agent Service feature availability in Azure Government", GOV)])
    n.place(cv, 0, max(t.bottom, tp.bottom) + 30)
    return n.bottom + 70


# ---------------------------------------------------------------------------------------------- section 7
def privacy_dr(cv, y):
    y = hdr(cv, y, "7  Data, privacy and disaster recovery") + 36
    cw3 = (W - 2 * 40) / 3
    p1 = Card(cw3, "Data and privacy", [
        "Prompts and completions are not shared with other customers or model providers and are not used to train models",
        "Stateful data is stored at rest in the geography of the resource",
        "AES-256 encryption at rest, optionally with customer-managed keys (preview features may not support CMK)",
        "You can delete your data at any time",
    ], theme="red", icon="security", src=[("Data, privacy and security for agents", PRIV)])
    p2 = Card(cw3, "No built-in disaster recovery (Standard setup)", [
        "No replication, backups, point-in-time restore or active-active",
        "Deleted threads cannot be recovered",
        "Recreating a project gives new agent IDs",
        "Recover by recreating the project and agents in another region",
        "See the Agent Service disaster recovery canvas for the runbooks",
    ], theme="indigo", icon="recovery-vault", src=[("Agent Service disaster recovery", DR)])
    p3 = Card(cw3, "Networking pointers", [
        "Network isolation covers agent OUTBOUND traffic in Standard setup only",
        "Inbound: private endpoint + public access disabled, for every setup",
        "Packet paths and the hosted-agent egress proxy: see the networking-internals canvas",
    ], theme="indigo", icon="vnet", src=[("Agents networking deep dive", DEEP), ("FAQ", FAQ)])
    r, b = row(cv, 0, y, [p1, p2, p3], gap=40)
    return b + 70


# ---------------------------------------------------------------------------------------------- section 8
def conflicts(cv, y):
    y = hdr(cv, y, "8  Where the docs disagree") + 36
    nw = (W - 2 * 40) / 3
    n1 = Note(nw, "The hosted-agents page lists 31 regions (including UK West); the limits page lists 30 for Agents; the Build-2026 blog said 20 regions during the preview. "
                  "We draw the limits page's 30.", kind="warn", title="Hosted-agent region count", src=[("Quotas and limits", LQR), ("Hosted agents", learn("agents/concepts/hosted-agents"))])
    n2 = Note(nw, "The VNet how-to allows the RFC 6598 range 100.64.0.0/10 (minus three reserved sub-ranges) for the delegated subnet; the networking deep dive and the FAQ say private RFC 1918 ranges only. "
                  "Stick to RFC 1918 until the pages agree.", kind="warn", title="Subnet address ranges", src=[("Use a virtual network", VNET), ("Networking deep dive", DEEP)])
    n3 = Note(nw, "Capability hosts (REST 2025-06-01) are 'retained for reference'; capability settings (ARM 2026-07-15-preview) are the newer path, but the capability-settings how-to "
                  "page currently shows the environment-setup content. Treat the capability-host constraints above as the documented behaviour.",
              kind="warn", title="Capability settings page is a duplicate", src=[("Set up your environment", ENV)])
    r, b = row(cv, 0, y, [n1, n2, n3], gap=40)
    return b + 70


def sources_block(cv, y):
    sources(cv, 0, y, [
        ("Set up your environment for Foundry Agent Service", ENV),
        ("Standard agent setup", STD),
        ("Capability hosts (retained for reference)", CAP),
        ("Use your own resources", BYO),
        ("Use a virtual network with Agent Service", VNET),
        ("Quotas and limits, regions, tool support", LQR),
        ("Feature availability in Azure Government", GOV),
        ("Agents networking deep dive", DEEP),
        ("Agent Service FAQ", FAQ),
        ("Agent Service disaster recovery", DR),
        ("Data, privacy and security for agents", PRIV),
        ("What is Foundry Agent Service?", OV),
    ], w=W, cols=3)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Agent Service: setup, limits, regions and Azure Government",
                                "Part 2 of the Agent Service map - Basic vs Standard vs BYO VNet, where state lives, capability hosts and settings, the real numbers  |  as of 2026-11-03",
                                icon="foundry", w=W)
    y = bottom + 34
    nt = Note(W, "Part 1 ('Foundry Agent Service: the map') covers the five agent kinds, the request path, the Responses-based object model and what the service manages. "
                 "This sheet is the operational reference: how to set the environment up, what lives where, and every documented limit.",
              kind="key", title="Reference sheet - read part 1 first", src=[("What is Foundry Agent Service?", OV)])
    nt.place(cv, 0, y)
    y = nt.bottom + 50
    y = setup_modes(cv, y)
    y = state_and_roles(cv, y)
    y = capability(cv, y)
    y = limits(cv, y)
    y = regions(cv, y)
    y = government(cv, y)
    y = privacy_dr(cv, y)
    y = conflicts(cv, y)
    sources_block(cv, y)
