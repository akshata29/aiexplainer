"""Data protection and encryption (part 1): where your data lives and who can see it - trust-boundary map, commitments, residency, abuse monitoring, CCC."""
from generator.xd import *

META = dict(
    id="data-protection-encryption", title="Data protection and encryption: where your data lives", section="5", order=5,
    description="A trust-boundary map of where prompts, agent state, traces and secrets live and who can see them, plus the data commitments, "
                "residency by deployment type, abuse monitoring, protected trace content and the Customer Copyright Commitment.",
    tags=["data-protection", "residency", "privacy", "abuse-monitoring", "encryption", "copyright-commitment"],
)

W = 3360
G = 60
C3 = (W - 2 * G) / 3
XB, XC = C3 + G, 2 * (C3 + G)


def L(path, **kw):
    return learn(path, **kw)


DP = ("Data, privacy and security for Foundry Models", L("responsible-ai/openai/data-privacy"))
DPA = ("Data, privacy and security for Agent Service", L("responsible-ai/agents/data-privacy-security"))
DPC = ("Data privacy for Claude in Foundry", L("responsible-ai/claude-models/data-privacy"))
CLH = ("Claude hosting options compared", L("foundry-models/concepts/claude-models-hosting-comparison"))
ABUSE = ("Abuse monitoring", L("openai/concepts/abuse-monitoring"))
CCC = ("Customer Copyright Commitment", L("responsible-ai/openai/customer-copyright-commitment"))
DEPL = ("Deployment types for Foundry Models", L("foundry-models/concepts/deployment-types"))
ARCH = ("Foundry architecture", L("concepts/architecture"))
TRACE = ("Trace data", L("observability/concepts/trace-data"))
TRACE_SENS = ("Protect sensitive trace content", L("observability/how-to/traces-sensitive-content"))
HOSTED = ("Hosted agents", L("agents/concepts/hosted-agents"))
STD = ("Standard agent setup", L("agents/concepts/standard-agent-setup"))
A365 = ("Agent 365 integration", L("agents/concepts/agent-365-integration"))
CMK = ("Customer-managed keys", L("concepts/customer-managed-keys"))
BASELINE = ("Azure security baseline for Foundry", L("azure-ai-foundry-security-baseline", base="security/benchmark/azure/baselines"))


def cite(cv, x, y, items, size=12):
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def stamps(cv, y):
    sw = (W - 3 * 40) / 4
    spec = [
        ("Data at rest stays in your geography",
         "Only the processing location varies with the deployment type: Global, Data Zone, Standard or Regional, Developer", "blue"),
        ("Not used to train foundation models without your permission",
         "Prompts, completions, embeddings and training data are not available to other customers, OpenAI or other providers", "green"),
        ("Hosted-agent $HOME is not CMK-encrypted",
         "Session storage is platform-managed, kept 30 days, and BYO storage is not supported for it (as of 2026-11-03)", "red"),
        ("Some paths leave the Foundry boundary",
         "Grounding with Bing, Claude on Anthropic infrastructure and the hosted Foundry MCP server follow other terms or locations", "orange"),
    ]
    boxes = [Box(sw, t, sub=s, theme=th, size=24, sub_size=16, h=112, sw=3) for t, s, th in spec]
    row(cv, 0, y, boxes, gap=40)
    return y + 112


# ====================================================================== 1. trust-boundary map
def trust_map(cv, y):
    _, b = section_header(cv, 0, y, "1  Where is my data? A map with three trust boundaries", size=34,
                          sub="Read left to right: your tenant, the Microsoft-operated Foundry service in your resource's geography, and everything outside that boundary. "
                              "Numbers 1 to 4 trace one inference request; dashed arrows are optional or opt-in flows.")
    y0 = b + 30
    ZL, ZM, ZR = (0, 800), (850, 1600), (2500, 860)
    pad = 40

    # ---- nodes (measured first so the zones can be sized around them)
    cw, cgap = 320, 80
    l1 = Box(720, "Your app, client or developer", sub="Entra ID token; encrypted in transit; the caller needs an RBAC role on the project or agent",
             theme="gray", icon="user", icon_pos="left", size=20, sub_size=15)
    chain = [
        Box(cw, "Foundry endpoint", sub="Entra ID authentication; data encrypted in transit", theme="blue", icon="foundry", size=20, sub_size=14),
        Box(cw, "Deployment", sub="Its type sets where prompts are processed: Global, Data Zone, Standard or Regional, Developer",
            theme="blue", icon="openai", size=20, sub_size=14),
        Box(cw, "Guardrails", sub="Content filtering runs synchronously; no prompts or outputs are stored in the classifier models",
            theme="pink", icon="content-safety", size=20, sub_size=14),
        Box(cw, "Model", sub="Stateless: nothing is stored in the model; fine-tuned models are exclusively yours",
            theme="blue", icon="openai", size=20, sub_size=14),
    ]
    ch = max(bx.h for bx in chain)
    core = Card(560, "Agent Service", [
        "# Written only if you use the feature",
        "Stateful entities: Responses API conversations, Assistants threads, stored completions",
        "Files API uploads and vector stores",
        "Hosted agents: session $HOME and /files",
        "Voice agents: transcripts, events and audio, if conversation storage is enabled",
        "# Not persisted",
        "MCP tool header data: available only for the current run",
        "# Where it lands",
        "Basic setup: Microsoft-managed multitenant storage, logically separated",
        "Standard setup: your Cosmos DB, Storage and AI Search, isolated per project",
    ], theme="green", subtitle="prompt agents and hosted agents run here", icon="agent",
        src=[DPA, ("Standard agent setup", L("agents/concepts/standard-agent-setup"))])
    lnodes = [
        Card(720, "Your stores: standard agent setup or BYO", [
            "Cosmos DB (messages, conversation history, agent metadata), Storage (files), AI Search (vector stores)",
            "Isolated per project; you configure CMK on each service separately",
        ], theme="cyan", icon="cosmos"),
        Card(720, "Your Application Insights and Log Analytics", [
            "Traces (prompts, outputs, tool calls) only if you connect a project; off by default",
            "Retention follows your workspace; sensitive content goes to the protected AppGenAIContent table (preview)",
        ], theme="violet", icon="app-insights"),
        Card(720, "Your Key Vault or Managed HSM", [
            "Customer-managed key for encryption at rest (optional)",
            "Optional bring-your-own vault for connection secrets",
        ], theme="red", icon="key-vault"),
    ]
    r1 = Card(780, "Claude hosted on Anthropic infrastructure", [
        "A hosting option for Claude: processed on Anthropic infrastructure, possibly outside Azure or your region",
        "Global Standard only; Anthropic is the independent data processor and its DPA applies",
    ], theme="orange", icon="claude", src=[CLH])
    rnodes = [
        Card(780, "External tools: Bing, SharePoint, third-party MCP", [
            "Provider terms apply; Grounding with Bing is a Microsoft-as-controller service outside the Products and Services DPA",
        ], theme="orange", icon="bing"),
        Card(780, "Microsoft 365 and Teams (published agents)", [
            "Publish metadata (name, icon, description) and agent responses sit under M365 and Teams terms and residency",
        ], theme="orange", icon="teams"),
        Card(780, "Agent 365 activity data", [
            "Follows the Entra tenant geography, not the Azure region; opt out per Foundry resource (a365LoggingEnabled=false)",
        ], theme="orange", icon="agent", src=[A365]),
        Card(780, "Hosted Foundry MCP server", [
            "A global stateless proxy: EU or US requests may be processed cross-region",
        ], theme="orange", icon="mcp", badge="preview"),
    ]
    sw_ = 350
    stores = [
        Card(sw_, "Basic-setup agent state", [
            "Threads, messages and files in Microsoft-managed multitenant storage, logically separated",
            "AES-256 with Microsoft-managed keys; deletable any time",
            "No CMK on Foundry-managed storage for prompt agents",
        ], theme="cyan", icon="storage"),
        Card(sw_, "Hosted-agent session storage", [
            "Session $HOME and /files in platform-managed storage",
            "! Not CMK-encrypted; BYO storage not supported; cannot be disabled",
            "$HOME kept 30 days; the session is deleted after 30 days idle",
        ], theme="green", icon="container-apps"),
        Card(sw_, "Abuse-monitoring store", [
            "Separate store per geography, logically separated by Foundry resource ID",
            "Only flagged data or suspect patterns; none if modified abuse monitoring is approved",
        ], theme="pink", icon="content-safety"),
        Card(sw_, "Microsoft-managed Key Vault", [
            "Default store for connection secrets, outside your subscription",
            "Secrets cannot be retrieved across projects through the APIs",
            "Deleting a connection deletes its secret",
        ], theme="red", icon="key-vault"),
    ]
    sh = max(c.h for c in stores)

    # ---- geometry
    chain_y = y0 + 120
    c_y = chain_y + ch + 70
    lh = sum(n.h for n in lnodes) + 36 * 2
    rh = sum(n.h for n in rnodes) + 28 * 3
    c_h = max(core.h, lh + 40, rh + 40)
    sp_y = c_y + c_h + 80
    sp_h = 100 + sh + 40
    m_bottom = sp_y + sp_h + 40
    l_top = c_y + (c_h - lh) / 2
    r_top = c_y + (c_h - rh) / 2
    l_bottom = l_top + lh + 40
    r_bottom = r_top + rh + 40

    # ---- zones (drawn first so everything else sits on top)
    for (x0, w), h, title, sub, th, style, fill in (
            (ZL, l_bottom - y0, "Your tenant and subscription", "you hold the RBAC, the keys and the retention", "blue", "dotted", "none"),
            (ZM, m_bottom - y0, "Microsoft Foundry service", "Microsoft-operated, inside your Foundry resource's Azure geography", "blue", "solid", "soft"),
            (ZR, r_bottom - y0, "Outside the Foundry boundary", "other terms, other processors, sometimes another location", "red", "dashed", "none")):
        with cv.panel(x0, y0, title=title, sub=sub, theme=th, style=style, fill=fill, w=w, h=h, pad=30, title_size=26, sub_size=15):
            pass
    with cv.panel(ZM[0] + pad, sp_y, title="Service-side storage in your geography", sub="Microsoft-operated; data at rest stays in the designated geography",
                  theme="cyan", style="dotted", fill="none", w=ZM[1] - 2 * pad, h=sp_h, pad=24, title_size=22, sub_size=15):
        pass

    # ---- place nodes
    l1.place(cv, 40, chain_y + (ch - l1.h) / 2)
    x = ZM[0] + pad
    for bx in chain:
        bx.place(cv, x, chain_y, h=ch)
        x += cw + cgap
    r1.place(cv, ZR[0] + 40, chain_y + (ch - r1.h) / 2)
    core.place(cv, ZM[0] + (ZM[1] - core.w) / 2, c_y, h=c_h)
    ly = l_top
    for n in lnodes:
        n.place(cv, 40, ly)
        ly += n.h + 36
    ry = r_top
    for n in rnodes:
        n.place(cv, ZR[0] + 40, ry)
        ry += n.h + 28
    x = ZM[0] + pad + 24
    for c in stores:
        c.place(cv, x, sp_y + 84, h=sh)
        x += sw_ + 24

    # ---- arrows
    e, d, g, m = chain
    connect(cv, l1, e, a_side="right", b_side="left", sw=3, gap=4)
    numbered(cv, (l1.right + e.x) / 2, l1.cy - 28, 1, theme="blue")
    for i, (a, bb) in enumerate(((e, d), (d, g), (g, m))):
        connect(cv, a, bb, a_side="right", b_side="left", sw=3, gap=4)
        numbered(cv, (a.right + bb.x) / 2, a.cy - 28, i + 2, theme="blue")
    connect(cv, m, r1, a_side="right", b_side="left", sw=2, gap=4, dash="dashed", color="#c92a2a")
    connect(cv, e, core, a_side="bottom", b_side="top", tb=0.2, route="elbow", sw=3, gap=4)
    labels_l = ["standard setup: state, files, vector stores", "traces, if you enable them", "keys and secrets (CMK, BYO vault)"]
    for n, lab in zip(lnodes, labels_l):
        both = n is lnodes[2]
        connect(cv, core, n, a_side="left", b_side="right", ta=(n.cy - core.y) / core.h, tb=0.5, sw=2, gap=4, dash="dashed",
                label=lab, label_size=14, start_head="arrow" if both else None, color="#0b7285" if n is lnodes[0] else ("#5f3dc4" if n is lnodes[1] else "#c92a2a"))
    labels_r = ["tool calls", "publish", "activity data", "MCP requests"]
    for n, lab in zip(rnodes, labels_r):
        connect(cv, core, n, a_side="right", b_side="left", ta=(n.cy - core.y) / core.h, tb=0.5, sw=2, gap=4, dash="dashed",
                label=lab, label_size=14, color="#c92a2a")
    arrow(cv, [(core.cx, core.bottom + 6), (core.cx, sp_y - 6)], sw=3, label="state, $HOME, abuse sample and secrets land here",
          label_size=14, label_pos="right")

    # ---- reading guide and residency note in the free corners
    guide = Card(ZL[1], "How to read the map", [
        "Blue dotted: your boundary - you hold RBAC, keys and retention",
        "Solid blue: the Microsoft Foundry service, in the geography of your Foundry resource",
        "Red dashed: outside the Foundry boundary - other terms, processors or locations",
        "Numbers 1 to 4: the inference path (request, deployment, guardrails, model)",
        "Dashed arrows: optional or opt-in flows",
    ], theme="gray", icon="info-protection", src=[ARCH])
    gy = l_bottom + 40
    guide.place(cv, 0, gy)
    note = Note(ZR[1], "Residency is about data at rest, which stays in the designated geography. Processing location varies with the deployment type, and Claude on Anthropic "
                "infrastructure and the hosted Foundry MCP server can process outside your region.", kind="gotcha", title="Residency is about data at rest",
                src=[DEPL])
    note.place(cv, ZR[0], r_bottom + 40)
    return max(m_bottom, guide.bottom, note.bottom)


# ====================================================================== 2. who can see it
def visibility(cv, y):
    _, b = section_header(cv, 0, y, "2  Who can see it?", size=34,
                          sub="The visibility legend for the map: access inside your tenant is controlled by RBAC; everything else follows the party's own terms.")
    top = b + 30
    n = 7
    gap = 28
    w = (W - (n - 1) * gap) / n
    spec = [
        ("You, through RBAC", "user", "green", "Agent state, files, vector stores and stored completions; only you can use your fine-tuned models"),
        ("Trace readers", "log-analytics", "violet", "Log Analytics Reader, Monitoring Reader or Reader on your App Insights; protected AppGenAIContent also needs Privileged Monitoring Data Reader"),
        ("Project members", "key", "red", "Can read the API keys stored in project connections (Microsoft-managed or your Key Vault)"),
        ("Microsoft abuse reviewers", "content-safety", "pink", "Authorized staff only, on flagged data: Secure Access Workstations with just-in-time approval; EEA staff for EEA-deployed models"),
        ("Anthropic", "claude", "orange", "Claude on Anthropic infrastructure (processor); flagged content from Azure-hosted Claude may go to Anthropic Trust and Safety"),
        ("M365, Teams and Agent 365 admins", "teams", "orange", "Published agent responses under M365 terms; Agent 365 data in the Entra tenant geography"),
        ("Tool and MCP providers", "bing", "orange", "Bing, SharePoint and third-party MCP servers see what your agent sends them, under their own terms"),
    ]
    boxes = [Box(w, t, sub=s, theme=th, icon=ic, size=19, sub_size=15, h=215, fill="soft", sw=2) for t, ic, th, s in spec]
    row(cv, 0, top, boxes, gap=gap)
    return top + max(bx.h for bx in boxes)


# ====================================================================== 3. encryption at a glance
def encryption_glance(cv, y):
    _, b = section_header(cv, 0, y, "3  Encryption at a glance", size=34,
                          sub="Defaults protect everything without any setup; customer-managed keys and your own Key Vault are optional extra layers. The deep dive is in part 2.")
    top = b + 34
    gap = 96
    cw = (W - 3 * gap) / 4
    c1 = Card(cw, "In transit", [
        "Encrypted in transit: the security baseline marks DP-3 as supported and on by default (a Microsoft responsibility)",
        "The caller authenticates with a Microsoft Entra token",
    ], theme="blue", icon="private-link", src=[BASELINE])
    c2 = Card(cw, "At rest: Microsoft-managed keys (default)", [
        "FIPS 140-2 compliant 256-bit AES, transparent, no code change",
        "The baseline for every stored item: files, state, stored completions, fine-tune data",
    ], theme="green", icon="key-vault", src=[CMK, DP])
    c3 = Card(cw, "At rest: customer-managed keys (optional)", [
        "Azure Key Vault or Managed HSM gives you rotation, revocation and audit",
        "Only in select regions (Azure AI Search capacity); a project can move to CMK but not back",
        "Hosted-agent $HOME and prompt agents on Foundry-managed storage are not CMK-encrypted",
    ], theme="red", icon="key-vault", src=[CMK])
    c4 = Card(cw, "Connection secrets", [
        "A Microsoft-managed Key Vault outside your subscription (default)",
        "Or bring your own: one AzureKeyVault connection manages all project and resource secrets",
    ], theme="red", icon="key-vault", src=[("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection"))])
    _, bb = row(cv, 0, top, [c1, c2, c3, c4], gap=gap)
    connect(cv, c1, c2, a_side="right", b_side="left", sw=3, gap=4)
    connect(cv, c2, c3, a_side="right", b_side="left", sw=3, gap=4, label="optional extra layer", label_size=14, label_wrap=80)
    connect(cv, c3, c4, a_side="right", b_side="left", sw=3, gap=4, dash="dashed")
    return bb


# ====================================================================== 4. commitments
def commitments(cv, y):
    _, b = section_header(cv, 0, y, "4  What Microsoft commits to, by service", size=34,
                          sub="Models sold directly by Azure, Agent Service and Claude each have their own data terms. The Microsoft Products and Services DPA governs the first two.")
    top = b + 34
    models = Card(C3, "Models sold directly by Azure", [
        "Prompts, completions, embeddings and training data are not available to other customers, not available to OpenAI or other providers, and not used to improve their models",
        "Not used to train foundation models without your permission, and not used to improve Microsoft or third-party products without explicit permission",
        "Fine-tuned models are exclusively yours; models are stateless, hosted by Microsoft in Azure and do not interact with OpenAI services",
        "# Data processed",
        "Prompts and generated content; uploaded data (Files, vector stores); stateful-entity data (Responses API, Assistants threads, stored completions); augmented data; training and validation data",
        "# Data stored",
        "At rest in the Foundry resource in your tenant, in the same geography; always AES-256 with Microsoft-managed keys as the baseline; optional CMK (some preview features may not support it); deletable at any time",
        "Guardrails run synchronously; no prompts or outputs are stored in the classifier models",
    ], theme="blue", icon="openai", src=[DP])
    agents = Card(C3, "Agent Service", [
        "Prompts, completions and data are not available to other customers or to OpenAI, Meta, Cohere or Mistral, and are not used to improve their models",
        "! External tools, for example Grounding with Bing, are Microsoft-as-controller services with their own terms, outside the Products and Services DPA",
        "MCP tool header data is available only for the current run and is not persisted",
        "Stored data lives in the Azure OpenAI or Foundry resource in your tenant and geography; optional CMK; deletable",
        "Processing location depends on the model endpoint and on the tool hosting location; the deployment's content filters apply",
        "Publishing to Microsoft 365 or Teams stores publish metadata (name, icon, description) and agent responses under M365 and Teams terms and residency",
    ], theme="green", icon="agent", src=[DPA])
    claude_tbl = Table([("", 190), ("Hosted on Azure", 420), ("Hosted on Anthropic infrastructure", 420)], [
        [("Processing", "gray"), "On Azure: ingress, API and GPU inference", "On Anthropic infrastructure, possibly outside Azure or your region"],
        [("Data at rest and retention", "gray"), "At rest in the selected geography", "Retention is governed by Anthropic's DPA"],
        [("Deployment scope", "gray"), "Global or Data Zone Standard (US)", "Global Standard only"],
        [("Terms", "gray"), "Flagged content may go to Anthropic Trust and Safety (exceptions-only review)",
         "Anthropic DPA and Commercial Terms; Microsoft shares billing, usage and contact data with Anthropic for Marketplace"],
        [("Common", "gray"), "Anthropic is the seller, operator and an independent data processor in both options; support is Microsoft Support; billing via CCU (MACC-eligible)", ""],
    ], w=C3, theme="orange", size=14, head_size=15, title="Claude in Foundry: two hosting options", title_size=22, first_col_theme="gray")
    models.place(cv, 0, top)
    agents.place(cv, XB, top)
    hosted_note = Note(C3, "Hosted agents keep session data in platform-managed storage: $HOME is retained 30 days, is not CMK-encrypted and cannot use BYO storage; "
                           "Foundry User on the project can list and manage all sessions. Voice agents with conversation storage enabled keep a Microsoft-managed copy for 60 days; "
                           "your own BYO audio copy is never auto-deleted.", kind="gotcha", title="Session data has its own retention (as of 2026-11-03)", src=[HOSTED])
    hosted_note.place(cv, XB, agents.bottom + 22)
    claude_tbl.place(cv, XC, top)
    cb = cite(cv, XC, claude_tbl.bottom + 8, [DPC, CLH])
    nclaude = Note(C3, "Claude subscriptions have type restrictions: free trial, student, credit-based, CSP and South Korea enterprise subscriptions are excluded (as of 2026-11-03).",
                   kind="warn", title="Subscription limits for Claude", src=[CLH])
    nclaude.place(cv, XC, cb + 18)
    return max(models.bottom, hosted_note.bottom, nclaude.bottom)


# ====================================================================== 4. residency by deployment type
def residency(cv, y):
    _, b = section_header(cv, 0, y, "5  Data residency by deployment type", size=34,
                          sub="The deployment type decides where inference is processed. Data at rest stays in the designated geography for every type. As of 2026-11-03.")
    top = b + 34

    # nested scopes (left)
    ow = 1380
    with cv.panel(0, top, title="Global types: processed in any Azure region where the model is deployed", theme="blue", style="dashed",
                  fill="none", pad=26, title_size=22, w=ow) as gp:
        ChipFlow([Chip("GlobalStandard", theme="blue", size=15), Chip("GlobalProvisionedManaged", theme="blue", size=15),
                  Chip("GlobalBatch", theme="blue", size=15)], ow - 2 * 26, gap=10).place(cv, gp.ix, gp.iy)
        iw = ow - 2 * 26 - 60
        with cv.panel(gp.ix + 30, gp.iy + 56, title="Data Zone types: only inside the Microsoft-specified data zone", theme="indigo", style="dashed",
                      fill="none", pad=26, title_size=22, w=iw) as dz:
            ChipFlow([Chip("DataZoneStandard", theme="indigo", size=15), Chip("DataZoneProvisionedManaged", theme="indigo", size=15),
                      Chip("DataZoneBatch", theme="indigo", size=15)], iw - 52, gap=10).place(cv, dz.ix, dz.iy)
            zc = Card(iw - 52, None, [
                "US",
                "EU = the Azure EU Data Boundary (may include EFTA countries such as Norway and Switzerland)",
                "APAC - Microsoft may add regions without notice",
            ], theme="indigo", fill="soft", body_size=15)
            zc.place(cv, dz.ix, dz.iy + 56)
            iw2 = iw - 2 * 26 - 60
            with cv.panel(dz.ix + 30, dz.iy + 56 + zc.h + 24, title="Standard and Regional Provisioned: inside the Azure geography", theme="teal",
                          style="dashed", fill="none", pad=26, title_size=22, w=iw2) as geo:
                ChipFlow([Chip("Standard", theme="teal", size=15), Chip("ProvisionedManaged", theme="teal", size=15)],
                         iw2 - 52, gap=10).place(cv, geo.ix, geo.iy)
                Card(iw2 - 52, None, ["May move between regions inside the geography for operations"], theme="teal", fill="soft",
                     body_size=15).place(cv, geo.ix, geo.iy + 52)
    nest_bottom = gp.bottom
    dev = Card(ow, "Developer tier (DeveloperTier)", [
        "Any region and no residency guarantee; no SLA; fine-tuned-model evaluation only; 24-hour lifetime",
    ], theme="yellow", dash="dashed", icon="regions", src=[DEPL])
    dev.place(cv, 0, nest_bottom + 24)
    band = Note(ow, "Data at rest always stays in the designated geography, including the abuse-monitoring store for Global and Data Zone types. "
                "Batch is a Global type: data at rest stays in the geography until capacity frees.", kind="key", title="At rest vs in processing", src=[ARCH])
    band.place(cv, 0, dev.bottom + 24)

    # table + notes (right)
    tx = ow + G
    tw = W - tx
    t = Table([("Deployment type (SKU)", 560), ("Where inference is processed", 760), "Billing"], [
        [("Global Standard (GlobalStandard), Global Provisioned (GlobalProvisionedManaged), Global Batch (GlobalBatch)", "blue"),
         "Any Azure region where the model is deployed", "Pay-per-token; PTU; batch (50% off, 24 h target)"],
        [("Data Zone Standard (DataZoneStandard), Provisioned (DataZoneProvisionedManaged), Batch (DataZoneBatch)", "indigo"),
         "Only within the Microsoft-specified data zone: US; EU = Azure EU Data Boundary; APAC", "Same billing models"],
        [("Standard (Standard), Regional Provisioned (ProvisionedManaged)", "teal"),
         "Within the Azure geography; may move between regions in the geography for operations", "Same billing models"],
        [("Developer (DeveloperTier)", "yellow"), "Any region; no residency guarantee; no SLA", "Pay-per-token"],
    ], w=tw, theme="blue", size=14, head_size=15, title="Processing location and billing by type", title_size=22)
    t.place(cv, tx, top)
    cb = cite(cv, tx, t.bottom + 8, [DEPL])
    n1 = Note(tw, "Foundry has no automatic cross-region failover: deploy separate resources per region and route or synchronize in your application. Global and Data Zone "
                  "Standard deployments are all affected if the primary region is interrupted.", kind="gotcha", title="No automatic cross-region failover",
              src=[("High availability and resiliency", L("how-to/high-availability-resiliency"))])
    n2 = Note(tw, "Restrict deployment types with an Azure Policy on Microsoft.CognitiveServices/accounts/deployments sku.name (the deployment types page has a sample deny rule).",
              kind="tip", title="Enforce it with policy", src=[DEPL])
    n3 = Note(tw, "Agent 365 data follows the Entra tenant geography (not the Azure region), with an opt-out per Foundry resource. The hosted Foundry MCP Server (preview) is a global "
                  "stateless proxy that may process EU and US requests cross-region. Microsoft 365 and Teams data follows M365 residency.", kind="warn",
              title="Residency exceptions", src=[A365])
    _, nb = col(cv, tx, cb + 20, [n1, n2, n3], gap=22)
    pick = Card(tw, "Picking a type by residency need", [
        "Processing must stay inside one Azure geography: Standard or Regional Provisioned",
        "Processing must stay inside the US, the EU Data Boundary or the APAC data zone: Data Zone types",
        "No processing-location requirement: Global types (any Azure region where the model is deployed)",
        "Developer tier: no residency guarantee and no SLA, so keep it for fine-tuned-model evaluation only",
        "! These types are Foundry deployments. Claude hosted on Anthropic infrastructure is processed there, possibly outside Azure or your region, under the Anthropic DPA",
    ], theme="blue", icon="regions", src=[DEPL, DPC])
    pick.place(cv, tx, nb + 22)
    return max(band.bottom, pick.bottom)


# ====================================================================== 5. data map table
def data_table(cv, y):
    _, b = section_header(cv, 0, y, "6  Where is each kind of data stored, protected and visible?", size=34,
                          sub="The reference table behind the map. n/s = not stated in the pages read for this canvas. As of 2026-11-03.")
    top = b + 34
    rows = [
        [("Prompts and completions in inference", "blue"), "Not stored in the model; processed per deployment type", "In transit and platform protection", "Stateless", "You; abuse monitoring (section 7)"],
        [("Abuse-monitoring store", "pink"), "Separate store per geography, logically separated by Foundry resource ID, inside the service boundary", "n/s",
         "Only data flagged or in suspect patterns; none if modified abuse monitoring is approved", "Authorized Microsoft reviewers (human review only when needed)"],
        [("Responses and conversations, Files API uploads, vector stores, stored completions, fine-tune data and models", "cyan"),
         "Basic setup: Microsoft-managed multitenant storage, logically separated. Standard setup: your Cosmos DB, Storage and AI Search, isolated per project",
         "AES-256 with Microsoft-managed keys as the baseline; CMK optional (see part 2)", "Deletable any time (Files and fine-tune DELETE APIs)",
         "You, through RBAC; fine-tuned models only you"],
        [("Hosted-agent session $HOME and /files", "green"),
         "Platform-managed storage per session ($HOME plus a disk budget of up to 20 GiB at 1 vCPU or more, about 20% reserved)",
         "Not CMK-encrypted; BYO storage not supported; cannot be disabled",
         "Sandbox deleted at idle timeout (2-240 min, default 15); $HOME kept 30 days; session deleted after 30 days idle; root disk ephemeral for up to 24 h",
         "The caller's session identity; Foundry User on the project can list and manage all sessions"],
        [("Voice agent transcripts, events and audio (if conversation storage is enabled)", "teal"),
         "Microsoft-managed, plus an extra audio copy in your BYO storage", "n/s", "Managed copy 60 days; your copy is never auto-deleted", "You"],
        [("Traces: prompts, outputs, tool calls", "violet"), "Your Application Insights and Log Analytics (off by default)", "Azure Monitor settings",
         "Your workspace retention; disconnecting stops new data, old data stays",
         "Anyone with Log Analytics Reader, Monitoring Reader or Reader; protected AppGenAIContent needs Privileged Monitoring Data Reader"],
        [("Connection secrets", "red"), "A Microsoft-managed Key Vault outside your subscription (default) or your Key Vault", "Key Vault", "Delete the connection = delete the secret",
         "Project members can read stored API keys"],
        [("Agent 365 activity data", "orange"), "Agent 365 control plane, in the Entra tenant geography", "n/s", "Opt out with a365LoggingEnabled=false", "Agent 365 admins and analytics"],
        [("Published agent data in M365 or Teams", "orange"), "Microsoft 365 or Teams", "M365", "M365", "Per M365 terms"],
        [("External tool traffic: Bing, SharePoint, third-party MCP", "orange"), "The provider", "Provider", "Provider", "The provider"],
        [("Claude on Anthropic infrastructure", "orange"), "Anthropic", "Anthropic", "Anthropic DPA", "Anthropic"],
    ]
    t = Table([("Data", 440), ("Stored where", 780), ("Encryption / key", 560), ("Retention / deletion", 780), "Who can see it"], rows, w=W, theme="cyan",
              size=14, head_size=15)
    t.place(cv, 0, top)
    cb = cite(cv, 0, t.bottom + 8, [DP, DPA, HOSTED, TRACE])
    return cb


# ====================================================================== 6. abuse monitoring
def abuse(cv, y):
    _, b = section_header(cv, 0, y, "7  Abuse monitoring: what is captured, who reviews, what you can opt out of", size=34,
                          sub="Content classification, pattern capture, review and notification, as documented. Preview models may use different practices.")
    top = b + 34
    cw = 790
    gap = (W - 4 * cw) / 3
    steps = [
        ("Content classification", "content-safety", "pink", ["Classifier models score prompts and completions"]),
        ("Abuse pattern capture", "log-analytics", "pink", ["Frequency, severity and intentionality scoring across requests"]),
        ("Review and decision", "user", "pink", ["Automated review first; human review only when needed (below)"]),
        ("Notification and action", "alerts", "pink", ["You are emailed on confirmed abuse; usually a chance to remediate, except severe or recurring abuse; may lead to suspension or termination"]),
    ]
    cards = [Card(cw, t, body, theme=th, icon=ic, src=[ABUSE] if i == 0 else ()) for i, (t, ic, th, body) in enumerate(steps)]
    _, fb = row(cv, 0, top, cards, gap=gap)
    for a, c in zip(cards, cards[1:]):
        connect(cv, a, c, a_side="right", b_side="left", sw=3, gap=4)
    for i, c in enumerate(cards):
        numbered(cv, c.x + 34, c.y, i + 1, theme="pink")
    auto = Card(C3, "Automated review is the default", [
        "AI models, including LLMs, review sampled flagged data; that data is not stored or used for training",
        "Human reviewers see data only when it is flagged or part of an abusive pattern",
    ], theme="pink", icon="agent", src=[ABUSE, DP])
    human = Card(C3, "Human review: only when needed", [
        "Only when automated confidence is insufficient or unavailable",
        "Authorized Microsoft employees on Secure Access Workstations, with just-in-time approval by team managers; point-wise queries by request ID",
        "Models deployed in the EEA: EEA-based reviewers",
    ], theme="pink", icon="user", src=[ABUSE])
    mod = Card(C3, "Modified abuse monitoring", [
        "Eligible Limited Access customers apply through a form",
        "Once approved: no data storage for abuse monitoring and no human review (automated review may still run; severe or recurring abuse can still lead to restrictions or a request to re-enable human review)",
        "Verify: Azure portal Overview > JSON view, or az cognitiveservices account show - the capability ContentLogging = false appears only when storage is off",
    ], theme="pink", icon="compliance", src=[ABUSE])
    _, ab = row(cv, 0, fb + 40, [auto, human, mod], gap=G)
    return ab


# ====================================================================== 7. trace content + CCC
def trace_content(cv, y):
    _, b = section_header(cv, 0, y, "8  Trace data: customer data that you must protect", size=34,
                          sub="Tracing captures prompts, outputs, tool calls and intermediate steps. It is off by default and only a Foundry Account Owner or Foundry Owner can turn it on.")
    top = b + 34
    cw = 790
    gap = (W - 4 * cw) / 3
    steps = [
        ("Register the feature", "subscription", "violet", ["Subscription Owner registers Microsoft.Insights/protectGenAISensitiveData (preview feature flag; opt in early)"]),
        ("Set the table to Protected", "log-analytics", "violet", ["Set AppGenAIContent to Protected (deny-by-default)"]),
        ("Grant access", "key", "violet", ["Assign Privileged Monitoring Data Reader to approved identities on the App Insights resource; workspace-level queries need it on the workspace"]),
        ("Verify", "user", "violet", ["A user with only Log Analytics Reader sees spans without content"]),
    ]
    cards = [Card(cw, t, body, theme=th, icon=ic, badge="preview" if i == 0 else None, src=[TRACE_SENS] if i == 0 else ()) for i, (t, ic, th, body) in enumerate(steps)]
    _, fb = row(cv, 0, top, cards, gap=gap)
    for a, c in zip(cards, cards[1:]):
        connect(cv, a, c, a_side="right", b_side="left", sw=3, gap=4)
    for i, c in enumerate(cards):
        numbered(cv, c.x + 34, c.y, i + 1, theme="violet")
    attrs = Card(C3, "Seven sensitive attributes", [
        "gen_ai.input.messages and gen_ai.output.messages",
        "gen_ai.system_instructions",
        "gen_ai.tool.definitions",
        "gen_ai.tool.call.arguments and gen_ai.tool.call.result",
        "gen_ai.evaluation.explanation",
        "= They route to the dedicated table AppGenAIContent. Foundry's own trace view is covered by the same role; custom roles holding the two Azure Monitor data actions also get access",
    ], theme="violet", icon="app-insights", badge="preview", src=[TRACE_SENS, TRACE])
    resp = Card(C3, "Your responsibilities", [
        "Inform end users, meet compliance obligations, control access and set retention",
        "Avoid logging secrets and tokens; redact personal data",
        "Restrict Log Analytics Reader; use PIM for time-bound access",
        "Hosted agents have extra considerations: platform-injected environment variables",
        "Disconnecting the project stops new collection only; old data stays in your workspace",
    ], theme="violet", icon="info-protection", src=[TRACE])
    tl = Card(C3, "Timeline (as of 2026-11-03)", [
        "Before Sep 30, 2026: sensitive values were written to both the legacy tables (AppDependencies, AppTraces, AppEvents) and AppGenAIContent",
        "From Sep 30, 2026 (already past): newly ingested values no longer go to the legacy tables (keys remain with a pointer)",
        "Sep 30, 2027 (upcoming): the temporary opt-out flag optOutProtectGenAISensitiveData is discontinued",
        "Update custom queries, alerts and workbooks; built-in Foundry and App Insights experiences adapt automatically",
    ], theme="violet", icon="alerts", badge="preview", src=[TRACE_SENS])
    _, tb = row(cv, 0, fb + 40, [attrs, resp, tl], gap=G)
    return tb


def copyright_section(cv, y):
    _, b = section_header(cv, 0, y, "9  Customer Copyright Commitment: the mitigations you must implement", size=34,
                          sub="Applies to Azure OpenAI and Configurable GAI Services. Microsoft defends against certain third-party IP claims on Output Content if you implemented the required mitigations - and you must show compliance when you claim.")
    top = b + 34
    tw = 2280
    t = Table([("Use case", 300), ("Required mitigations", 1380), "Effective"], [
        [("All use cases (universal)", "teal"),
         "A metaprompt that prevents copyright infringement (for example the 'Protected Material - Text' safety system message template), plus a testing and evaluation report (red teaming or systematic measurement) of third-party-content output and mitigations",
         "Dec 1, 2023"],
        [("Code generation", "teal"), "Protected-material code model on (annotate or filter; follow the cited license if you annotate) plus the jailbreak filter (Prompt Shield) in filter mode", ""],
        [("Text generation", "teal"), "Protected-material text in filter mode plus the jailbreak filter on", ""],
        [("Asynchronous filter (code or text)", "teal"), "Output that the asynchronous filter flags retroactively is not covered", "May 21, 2024"],
        [("Image generation, OpenAI transcription, other use cases", "teal"), "No additional mitigations", ""],
    ], w=tw, theme="teal", size=14, head_size=15, title="Required mitigations by use case", title_size=22)
    t.place(cv, 0, top)
    cb = cite(cv, 0, t.bottom + 8, [CCC])
    n1 = Note(W - tw - G, "GitHub offerings: no commitment text as of Apr 3, 2026. Copilot Studio: a bring-your-own model is covered only if it runs in Azure OpenAI with these mitigations (Jun 1, 2025).",
              kind="warn", title="Where the commitment does not reach", src=[CCC])
    n1.place(cv, tw + G, top)
    return max(cb, n1.bottom)


def dates(cv, y):
    _, b = section_header(cv, 0, y, "Dates that matter for data protection", size=30,
                          sub="Time-sensitive items from this canvas and its siblings. Today is 2026-11-03: check Microsoft Learn for the current status before relying on any date.")
    events = [
        ("2023-12-01", "CCC universal mitigations effective", "metaprompt + evaluation report"),
        ("2024-05-21", "CCC: asynchronous filter note", "retroactively flagged output not covered"),
        ("2025-06-01", "CCC: Copilot Studio BYO model note", ""),
        ("2026-04-03", "CCC: GitHub offerings", "no commitment as of this date"),
        ("2026-06-25", "Private ACR support", "projects created after this date (past)"),
        ("2026-08-26", "Assistants API retirement", "per the auth page; already past - confirm"),
        ("2026-09-30", "Sensitive trace content leaves legacy tables", "AppGenAIContent only (past)"),
        ("2026-10-23", "Entra agent-state enforcement", "16:00 UTC (past)"),
        ("2027-09-30", "Trace-protection opt-out discontinued", "optOutProtectGenAISensitiveData (upcoming)"),
    ]
    return timeline(cv, 40, b + 135, W - 80, events, label_w=330, size=16, theme="violet") + 30


def build(cv: Canvas) -> None:
    _, bottom = title_block(cv, 0, 0, "Data protection and encryption: where your data lives and who can see it",
                            "A trust-boundary map, the data commitments, residency by deployment type, abuse monitoring and trace content - as of 2026-11-03",
                            icon="foundry", w=W)
    y = stamps(cv, bottom + 40) + 70
    y = trust_map(cv, y) + 70
    y = visibility(cv, y) + 70
    y = encryption_glance(cv, y) + 70
    y = commitments(cv, y) + 70
    y = residency(cv, y) + 70
    y = data_table(cv, y) + 50
    y = abuse(cv, y) + 70
    y = trace_content(cv, y) + 70
    y = copyright_section(cv, y) + 70
    y = dates(cv, y) + 40
    nxt = Note(W, "Continues in 'Data protection, part 2: keys, secrets, storage and compliance': customer-managed keys (prerequisites, rotation, revocation), bring-your-own Key Vault and storage, "
                  "the security baseline, Defender, Purview and Azure Government. See also 'Network isolation' and 'Authentication and authorization map'.",
               kind="key", title="Continue in this series", size=16)
    nxt.place(cv, 0, y)
    y = nxt.bottom + 60
    sources(cv, 0, y, [
        ("Data, privacy and security for Foundry Models", L("responsible-ai/openai/data-privacy")),
        ("Data, privacy and security for Agent Service", L("responsible-ai/agents/data-privacy-security")),
        ("Data privacy for Claude in Foundry", L("responsible-ai/claude-models/data-privacy")),
        ("Claude hosting options compared", L("foundry-models/concepts/claude-models-hosting-comparison")),
        ("Abuse monitoring", L("openai/concepts/abuse-monitoring")),
        ("Customer Copyright Commitment", L("responsible-ai/openai/customer-copyright-commitment")),
        ("Deployment types for Foundry Models", L("foundry-models/concepts/deployment-types")),
        ("Foundry architecture", L("concepts/architecture")),
        ("Plan your Foundry rollout", L("concepts/planning")),
        ("Trace data", L("observability/concepts/trace-data")),
        ("Protect sensitive trace content", L("observability/how-to/traces-sensitive-content")),
        ("Hosted agents", L("agents/concepts/hosted-agents")),
        ("Standard agent setup", L("agents/concepts/standard-agent-setup")),
        ("Agent 365 integration", L("agents/concepts/agent-365-integration")),
    ], w=W, cols=3)
