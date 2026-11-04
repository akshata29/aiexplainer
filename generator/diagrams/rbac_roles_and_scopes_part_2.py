"""Foundry roles part 2 - elevated-role tasks by area, the project managed identity's roles on backing resources, feature-specific roles, Azure Policy beside RBAC."""
from generator.xd import *

META = dict(
    id="rbac-roles-and-scopes-part-2", title="Foundry roles, part 2: elevated tasks, feature roles and Azure Policy", section="5", order=2.5,
    description="Which tasks force Owner or User Access Administrator, the roles the project managed identity holds on backing resources, "
                "extra roles per feature (evaluations, tracing, Agent 365, hosted agents, publishing), Azure Policy beside RBAC and a permission-error cheat sheet.",
    tags=["rbac", "elevated-roles", "managed-identity", "azure-policy", "least-privilege"],
)

W = 3360
G = 60
C3 = (W - 2 * G) / 3
XB, XC = C3 + G, 2 * (C3 + G)
C4 = (W - 3 * 50) / 4           # four-column grid (802)


def L(path, **kw):
    return learn(path, **kw)


RBAC = ("RBAC for Foundry", L("concepts/rbac-foundry"))
ADMIN = ("Foundry administrator guide", L("concepts/administrator-guide"))
HOSTED = ("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions"))
EVALP = ("Evaluation permissions", L("observability/how-to/evaluation-permissions"))
TRACEP = ("Trace ingestion with Entra", L("observability/how-to/trace-ingestion-entra-authentication"))
A365 = ("Grant Agent 365 permissions", L("agents/how-to/grant-agent-365-permissions"))
PUBLISH = ("Publish to Teams and Microsoft 365", L("agents/how-to/publish-copilot"))
STD = ("Standard agent setup", L("agents/concepts/standard-agent-setup"))
MDP = ("Model deployment policy", L("how-to/model-deployment-policy"))
CUSTOMP = ("Custom policy definitions", L("how-to/custom-policy-definition"))
NOPREVIEW = ("Disable preview features", L("how-to/disable-preview-features"))
POLREF = ("Azure AI services policy reference", L("policy-reference", base="azure/ai-services"))
CPCOMP = ("Manage compliance and security (control plane)", L("control-plane/how-to-manage-compliance-security"))


def colhead(cv, x, y, text, w, sub=None):
    return section_header(cv, x, y, text, sub=sub, size=28, w=w, sub_size=15)[1]


def masonry(cv, x, y, cards, cols, gap_x, gap_y):
    """Equal-width cards flowed into the shortest column; each column's last card is stretched so the bottoms line up."""
    heights, assign = [0.0] * cols, [[] for _ in range(cols)]
    for c in cards:
        i = min(range(cols), key=lambda k: heights[k])
        assign[i].append(c)
        heights[i] += c.h + gap_y
    target = max(heights) - gap_y
    for i, col_cards in enumerate(assign):
        cy = y
        for j, c in enumerate(col_cards):
            last = j == len(col_cards) - 1
            h = c.h + (target - (heights[i] - gap_y)) if last else None
            c.place(cv, x + i * (c.w + gap_x), cy, h=h)
            cy += c.h + gap_y
    return y + target


def stamps(cv, y):
    sw = (W - 3 * 40) / 4
    spec = [
        ("Role assignment forces an elevated role",
         "Assigning any role needs Owner or User Access Administrator; Account Owner and Project Manager assign only within ABAC limits", "red"),
        ("Foundry roles stop at the Foundry resource",
         "Cosmos DB, AI Search, Storage, ACR, Log Analytics and Key Vault roles are assigned on those resources", "orange"),
        ("Entra roles live outside IAM",
         "AI Administrator, Global Administrator, Application Administrator and Conditional Access Administrator: Entra admin center", "violet"),
        ("Policy sits beside RBAC",
         "RBAC decides who may act; Azure Policy decides which configurations are allowed - model deployment policies run at deployment time", "grape"),
    ]
    boxes = [Box(sw, t, sub=s, theme=th, size=24, sub_size=16, h=112, sw=3) for t, s, th in spec]
    row(cv, 0, y, boxes, gap=40)
    return y + 112


# ====================================================================== 1. elevated tasks by area
def area_cards():
    c = {}
    c["res"] = dict(title="Resources", theme="blue", icon="foundry", body=[
        "Create resource or project: Contributor, Foundry Account Owner or Foundry Owner (subscription or RG; resource)",
        "Upgrade from Azure OpenAI: Owner or Contributor",
        "Recover or purge a deleted account: Contributor (subscription)",
        "Bicep deployment: Contributor or Owner (resource group)"])
    c["ra"] = dict(title="Role assignment", theme="red", icon="key-vault", body=[
        "! Assign any role: Owner or User Access Administrator",
        "Foundry Account Owner and Project Manager can conditionally assign Foundry User only (per the administrator guide)",
        "! Create custom roles: Owner",
        "! Assign custom roles: User Access Administrator or RBAC Administrator"])
    c["std"] = dict(title="Standard agent setup", theme="green", icon="agent", body=[
        "! Cross-service roles (Cosmos DB, Search, Storage): Owner or RBAC Administrator (resource group)",
        "Provision: Foundry Account Owner or Owner (subscription)",
        "The caller also needs Storage Blob Data Contributor (each BYO storage) and Cosmos DB Operator (each BYO Cosmos DB)",
        "AI Search needs no caller role (capability settings API 2026-07-15-preview)"], src=[STD])
    c["host"] = dict(title="Hosted agent setup", theme="green", icon="container-apps", body=[
        "Create ACR, Application Insights, Log Analytics: Contributor or Owner (resource group)",
        "Create agents and versions: Foundry User, Project Manager or Foundry Owner (project)",
        "! Owner or Contributor alone are insufficient to create agents",
        "Project connections: Project Manager, Account Owner, Foundry Owner, Contributor or Owner",
        "! ACR pull role for the project managed identity: Owner or RBAC Administrator on the ACR",
        "Push: Container Registry Repository Writer or AcrPush",
        "Evaluations read telemetry: Log Analytics Data Reader to the project managed identity"], src=[HOSTED])
    c["byo"] = dict(title="Bring-your-own resources", theme="cyan", icon="storage", body=[
        "Attach: Foundry Account Owner or Owner (subscription)",
        "! Assign roles to the managed identity: Owner or User Access Administrator (on the target resource)"])
    c["tools"] = dict(title="Agent tools", theme="orange", icon="toolbox", body=[
        "Grounding with Bing: Contributor or Owner",
        "Browser automation (preview): Contributor or Owner (resource group)",
        "AI Search tool: Search Index Data Contributor + Search Service Contributor",
        "File search: Storage Blob Data Contributor (project storage)",
        "Custom code interpreter (preview): Container Apps ManagedEnvironments Contributor + Foundry Owner",
        "OpenAPI or MCP tool: Contributor or Owner (project); A2A: Contributor or Owner (resource)",
        "Azure Speech tool: Storage Blob Data Contributor"])
    c["pub"] = dict(title="Publish", theme="green", icon="teams", body=[
        "Publish as Agent Application: Foundry Project Manager (resource)",
        "Invoke a published Agent Application: Foundry User (application resource)",
        "Publish to Microsoft 365 or Teams: Foundry Project Manager (project) per the administrator guide",
        "! Reassign RBAC to the published agent identity: Owner or User Access Administrator",
        "= Docs disagree: the publish how-to lists Foundry User + Azure Bot Service Contributor (see part 1)"], src=[PUBLISH])
    c["models"] = dict(title="Models", theme="blue", icon="openai", body=[
        "Deploy catalog, Foundry or provisioned-throughput models: Foundry Account Owner (resource)",
        "Marketplace models: Contributor (subscription; creates a billing agreement)",
        "Fireworks: Foundry Owner (project) + Contributor (subscription)",
        "Fine-tune: Foundry Owner, or Foundry User + Foundry Account Owner; cross-tenant fine-tune deploy: Foundry Project Manager (source and destination)",
        "View or edit quotas, blocklists: Foundry Account Owner; request an increase: Contributor (subscription)"])
    c["net"] = dict(title="Network and encryption", theme="indigo", icon="vnet", body=[
        "! Private endpoint: Contributor or Owner (Foundry resource) + Network Contributor (VNet) + Private DNS Zone Contributor (zone)",
        "Managed VNet: Owner or Contributor",
        "! RBAC on the target resources of a managed VNet: Owner or RBAC Administrator",
        "Network Security Perimeter (the administrator guide labels it preview): Owner, Contributor or Network Contributor",
        "! Customer-managed keys: Owner or User Access Administrator on the Key Vault to grant Key Vault Crypto User; Contributor or Owner on the Foundry resource to enable",
        "Key Vault connection: Key Vault Contributor + Key Vault Administrator"])
    c["guard"] = dict(title="Guardrails and policy", theme="pink", icon="content-safety", body=[
        "Guardrails: Foundry Account Owner or higher",
        "! Guardrail, model-deployment and custom policies: Owner or Resource Policy Contributor",
        "! Third-party guardrails: Owner (subscription) + Key Vault Administrator",
        "AI Gateway token limits and tool governance: API Management Service Contributor or Owner"])
    c["comp"] = dict(title="Compliance and monitoring", theme="violet", icon="defender", body=[
        "Defender for Cloud: Security Admin or Owner",
        "Purview: Foundry Account Owner",
        "Diagnostic settings: Monitoring Contributor; Application Insights tracing: Contributor or higher",
        "! Agent availability: Entra AI Administrator or Global Administrator",
        "Conditional Access: Conditional Access Administrator",
        "= Entra roles are assigned in the Entra admin center, not in IAM"])
    c["dr"] = dict(title="Disaster recovery", theme="yellow", icon="recovery-vault", body=[
        "High availability: Owner or Contributor + User Access Administrator",
        "Agent Service DR (operator): Owner or Contributor + DocumentDB Account Contributor + Search Service Contributor + Storage Blob Data Contributor",
        "Agent Service DR (platform): Contributor or Owner + Storage Account Contributor"])
    return c


def section_tasks(cv, y):
    _, b = section_header(cv, 0, y, "1  Elevated-role tasks by area: the minimum role and scope", size=34,
                          sub="Per the administrator guide (as of 2026-11-03). Red bullet = the task forces Owner, User Access Administrator, RBAC Administrator or another elevated role, "
                              "or a role on a different resource or in Entra.")
    top = b + 34
    a = area_cards()
    order = ["res", "ra", "std", "host", "byo", "tools", "pub", "models", "net", "guard", "comp", "dr"]
    cards = [Card(C4, v["title"], v["body"], theme=v["theme"], icon=v["icon"], src=v.get("src", [ADMIN]))
             for v in (a[k] for k in order)]
    return masonry(cv, 0, top, cards, 4, 50, 40)


# ====================================================================== 2. project managed identity role map
def section_identity(cv, y):
    _, b = section_header(cv, 0, y, "2  What the project managed identity holds on its backing resources", size=34,
                          sub="Hub and spokes: Foundry User at the Foundry resource is the starter assignment; every other role below is assigned on the backing resource itself.")
    top = b + 40
    hub = Box(980, "Project managed identity", sub="Needs Owner, User Access Administrator or RBAC Administrator on each target resource to assign these roles",
              theme="red", icon="managed-identity", icon_pos="left", size=26, sub_size=16, h=130, sw=3)
    hub.place(cv, (W - hub.w) / 2, top)

    cw, gap = 520, 48
    spokes = [
        Card(cw, "Foundry resource", [
            "Foundry User (the starter assignment)",
            "Also for continuous or scheduled evaluation rules, and for VNet evaluation and red-team runs (resource scope)",
        ], theme="blue", icon="foundry", src=[EVALP, RBAC]),
        Card(cw, "Azure Storage (BYO)", [
            "Storage Account Contributor (account)",
            "Storage Blob Data Contributor on <workspaceId>-azureml-blobstore",
            "Storage Blob Data Owner on <workspaceId>-azureml-agent (some pages say agents-blobstore)",
            "Evaluations with Entra storage: Storage Blob Data Owner for the user and the project resource",
        ], theme="cyan", icon="storage", src=[STD, ("Bring your own storage", L("how-to/bring-your-own-azure-storage-foundry"))]),
        Card(cw, "Azure Cosmos DB (BYO)", [
            "Cosmos DB Operator (account level)",
            "Cosmos DB Built-in Data Contributor (data plane)",
            "! Not visible in the IAM blade: use az cosmosdb sql role assignment create or Bicep",
        ], theme="cyan", icon="cosmos", src=[STD, ADMIN]),
        Card(cw, "Azure AI Search", [
            "Search Index Data Contributor + Search Service Contributor (standard agent setup)",
            "Foundry IQ indexing: Search Index Data Contributor",
            "Private retrieval tutorial (preview): Search Index Data Reader, or Contributor if it writes",
        ], theme="teal", icon="ai-search", src=[STD, ("Foundry IQ private retrieval", L("agents/how-to/foundry-iq-tutorial-private-retrieval"))]),
        Card(cw, "App Insights and Log Analytics", [
            "Monitoring Metrics Publisher: trace ingestion with local auth disabled (preview)",
            "Reader on App Insights for trace-based evaluations and datasets",
            "Privileged Monitoring Data Reader for protected tables",
            "Log Analytics Reader, or Log Analytics Data Reader in DataActionsOnly mode",
            "Log Analytics Data Reader at the workspace for hosted-agent evaluations",
        ], theme="violet", icon="app-insights", src=[EVALP, TRACEP]),
        Card(cw, "Azure Container Registry", [
            "Container Registry Repository Reader or AcrPull for the hosted-agent image pull",
            "The ACR needs azureADAuthenticationAsArmPolicy enabled",
            "! Docs disagree: the private-ACR how-to has azd deploy grant AcrPull to a per-agent identity",
        ], theme="indigo", icon="acr", src=[HOSTED]),
    ]
    sy = hub.bottom + 90
    _, sb = row(cv, 0, sy, spokes, gap=(W - 6 * cw) / 5)
    for s in spokes:
        line_between(cv, hub, s, a_side="bottom", b_side="top", route="elbow", bend=0.45, color="#c92a2a", sw=2, dash="dotted")
    return sb


def section_setup_flow(cv, y):
    _, b = section_header(cv, 0, y, "Standard agent setup: who needs which role, in order", size=26, w=W)
    top = b + 26
    cw = 770
    steps = [
        ("Create the account and project", "foundry", "blue",
         ["Foundry Account Owner creates the account and project", "Owner or RBAC Administrator is needed for the role assignments"]),
        ("Caller sets capability settings", "api-connections", "cyan",
         ["Caller identity: Storage Blob Data Contributor + Cosmos DB Operator", "AI Search needs no caller role"]),
        ("Assign the project managed identity roles", "managed-identity", "red",
         ["Cosmos DB Operator + Storage Account Contributor (account level)", "Then the data-plane roles (Cosmos DB, Search, Storage)"]),
        ("Grant developers access", "users", "green",
         ["Foundry User on the project for each developer", "Reader on the Foundry resource if they should browse it"]),
    ]
    cards = [Card(cw, t, body, theme=th, icon=ic, src=[STD, ADMIN] if i == 0 else ()) for i, (t, ic, th, body) in enumerate(steps)]
    hgap = (W - 4 * cw) / 3
    _, fb = row(cv, 0, top, cards, gap=hgap)
    for a, c in zip(cards, cards[1:]):
        connect(cv, a, c, a_side="right", b_side="left", sw=3, gap=4)
    for i, c in enumerate(cards):
        numbered(cv, c.x + 34, c.y, i + 1, theme="red")
    return fb


# ====================================================================== 3. feature-specific roles
def section_features(cv, y):
    _, b = section_header(cv, 0, y, "3  Feature-specific role requirements", size=34,
                          sub="Extra roles that specific features ask for on top of Foundry User. Preview items are labelled; as of 2026-11-03.")
    top = b + 34
    cards = [
        Card(C4, "Evaluations", [
            "# Your identity or CI service principal",
            "Foundry User on the project or resource (azd evals: on the resource)",
            "Evaluations that invoke a model: Foundry User at the Foundry account scope",
            "# Project managed identity",
            "Foundry User for continuous or scheduled evaluation rules",
            "Reader on App Insights for trace-based evaluations; Privileged Monitoring Data Reader for protected tables",
            "BYO storage via Entra: Storage Blob Data Contributor (other pages say Owner)",
            "= Viewing traces: Log Analytics Reader. Evaluations use Entra only",
        ], theme="violet", icon="app-insights", src=[EVALP]),
        Card(C4, "Tracing and App Insights", [
            "Enable tracing: Foundry Account Owner or Foundry Owner (it is off by default)",
            "Ingestion (preview): Monitoring Metrics Publisher to the project managed identity, plus the Agent Identity for hosted agents, on an App Insights resource with local auth disabled",
            "Assigning it needs at least User Access Administrator on App Insights",
            "View: Log Analytics Reader, Monitoring Reader or Reader, plus project access",
            "! Foundry User alone sees metrics, not traces",
        ], theme="violet", icon="monitor", badge="preview", src=[TRACEP, ("Trace data", L("observability/concepts/trace-data"))]),
        Card(C4, "Agent 365", [
            "The tenant needs at least one Microsoft 365 Copilot license and the Frontier program",
            "A Global Administrator enables Agent 365 and accepts the terms",
            "Assign the Entra app role Agent365.Observability.OtelWrite (8f71190c-00c8-461d-a63b-f74abde9ba52) of the Agent365Observability service principal to the hosted agent's Entra Agent Identity",
            "The assigner needs Global Administrator or Application Administrator",
            "a365LoggingEnabled and a365Status need Owner or Contributor on the Foundry resource",
        ], theme="violet", icon="m365", src=[A365, ("Agent 365 integration", L("agents/concepts/agent-365-integration"))]),
        Card(C4, "Hosted agents", [
            "# Project managed identity",
            "Foundry User at the account; Container Registry Repository Reader or AcrPull at the ACR; Log Analytics Data Reader at the workspace",
            "# People and callers",
            "Deployer: Container Registry Repository Writer or AcrPush (local build); Container Registry Tasks Contributor (remote build; ABAC-mode ACR needs Owner or Contributor)",
            "Users: Foundry User or Project Manager at the project; callers: Foundry Agent Consumer",
            "Middle tier: the custom UserIdentityImpersonation role; telemetry readers: Monitoring Reader",
        ], theme="green", icon="container-apps", src=[HOSTED]),
        Card(C4, "Publish to Teams and Microsoft 365", [
            "Microsoft.BotService/botServices/write and channels/write: Azure Bot Service Contributor, Contributor or Owner - Foundry roles do not grant them",
            "Plus Foundry User at the project (agent-endpoint model); the Microsoft.BotService provider must be registered",
            "Tenant scope needs Microsoft 365 admin approval",
            "Each caller under BotServiceRbac needs Foundry Agent Consumer",
            "! The administrator guide and RBAC for Foundry still say Project Manager (Agent Application model)",
        ], theme="green", icon="teams", src=[PUBLISH, ("Troubleshoot publish authorization", L("agents/how-to/troubleshoot-publish-copilot-authorization"))]),
        Card(C4, "Foundry IQ private retrieval", [
            "You: Storage Blob Data Contributor; Search Service Contributor + Search Index Data Contributor; Foundry Project Manager (create the project connection) + Foundry User",
            "Search managed identity: Storage Blob Data Reader + Cognitive Services User on Foundry",
            "Project managed identity: Search Index Data Reader (Contributor if it writes)",
        ], theme="teal", icon="ai-search", badge="preview",
            src=[("Foundry IQ private retrieval tutorial", L("agents/how-to/foundry-iq-tutorial-private-retrieval"))]),
        Card(C4, "Managed compute deployments", [
            "Five operations: managedComputeDeployments read, write and delete; managedComputeCapacities/read; locations/managedComputeUsages/read",
            "Full: Cognitive Services Contributor, Foundry Owner and Foundry Account Owner",
            "Read, capacities and usages: Foundry Project Manager, Foundry User, Cognitive Services User",
            "Inference needs Foundry User at the account",
            "! The locations/*/read wildcard does not cover managedComputeCapacities/read",
        ], theme="blue", icon="ml", badge="preview", src=[RBAC]),
        Card(C4, "Quota and eligibility", [
            "Cognitive Services Usages Reader at the subscription: quota visibility and deployment eligibility checks",
            "View or edit quotas: Foundry Account Owner; request an increase: Contributor at the subscription",
            "! The Usages API rejects resource group, resource and project assignments",
        ], theme="yellow", icon="quotas", src=[RBAC, ADMIN]),
    ]
    return masonry(cv, 0, top, cards, 4, 50, 40)


# ====================================================================== 4. Azure Policy beside RBAC
def gates(cv, x, y, w):
    """Two-gate diagram: RBAC answers 'may this identity act?', Azure Policy answers 'is this configuration allowed?'."""
    bw = (w - 3 * 120) / 4
    req = Box(bw, "Deployment or API request", sub="portal, ARM, CLI or Bicep", theme="gray", icon="user", size=19, sub_size=14, h=150)
    g1 = Box(bw, "Gate 1: Azure RBAC", sub="May this identity perform the action? Roles, scopes, ABAC conditions, custom roles with notDataActions",
             theme="red", icon="key-vault", size=19, sub_size=14, h=150)
    g2 = Box(bw, "Gate 2: Azure Policy", sub="Is this configuration allowed? Audit, Deny, Modify or DeployIfNotExists; model deployment policies run at deployment time",
             theme="grape", icon="policy", size=19, sub_size=14, h=150)
    res = Box(bw, "Allowed, or blocked at deployment time", sub="A noncompliant model deployment: the Deploy button is disabled with a reason, or the ARM or CLI deployment fails as a whole",
              theme="green", icon="foundry", size=19, sub_size=14, h=150)
    blocks = [req, g1, g2, res]
    row(cv, x, y, blocks, gap=120)
    for i, (a, b2) in enumerate(zip(blocks, blocks[1:])):
        connect(cv, a, b2, a_side="right", b_side="left", sw=3, gap=4)
        numbered(cv, (a.right + b2.x) / 2, a.cy - 30, i + 1, theme="red")
    return y + 150


def section_policy(cv, y):
    _, b = section_header(cv, 0, y, "4  Azure Policy and guardrails sit beside RBAC", size=34,
                          sub="RBAC is not the only control: policy restricts what may be deployed, which tools agents may use and how resources must be configured. As of 2026-11-03.")
    top = b + 40
    gb = gates(cv, 0, top, W)
    ty = gb + 56

    builtin = Card(C3, "Built-in policy definitions (Azure AI services policy reference)", [
        "Key access disabled (Audit, Deny, Disabled) plus DeployIfNotExists and Modify variants",
        "Customer-managed key (Audit, Deny, Disabled; not assessed by default)",
        "Restrict network access; use Azure Private Link (Audit); disable public network access (Modify); private endpoint (DeployIfNotExists)",
        "Accounts use managed identity; customer-owned storage",
        "Diagnostic logs; Event Hub, Log Analytics and Storage log DeployIfNotExists",
        "Foundry model deployments should only use approved models, and meet eligibility requirements (GA)",
        "Content-filtering control policies for deployments and agents (preview)",
        "Foundry agents and toolboxes should only use approved tools / should not use denied tools (preview; Audit, Deny, Disabled)",
    ], theme="grape", icon="policy", src=[POLREF])
    model = Card(C3, "Model deployment policies", [
        "Author as Owner or Resource Policy Contributor",
        "Evaluated at deployment time: the Deploy button is disabled with a reason; an ARM or CLI deployment fails as a whole if any model is noncompliant",
        "Approved models use allowedPublishers and allowedAssetIds (prefix match: add a trailing /)",
        "Eligibility uses onlyAllowDirectFromAzure and denyPreviewModels (default false); the model router honours both",
        "Allow at least 15 minutes to apply; compliance data takes up to 24 hours",
    ], theme="grape", icon="policy", src=[MDP])
    custom = Card(C3, "Guardrail and custom policies", [
        "# Guardrail policies (control plane)",
        "Owner or Resource Policy Contributor at subscription or resource group; up to 30 minutes to appear",
        "# Custom policies",
        "Allowed connection categories (aliases .../accounts/connections/category and .../projects/connections/category)",
        "Deny API-key connections; audit missing capability settings (VNet subnet, custom storage); deny account kinds that lack full Foundry capability",
        "Up to 30 minutes; az policy state trigger-scan; samples in 05-custom-policy-definitions",
    ], theme="grape", icon="policy", src=[CPCOMP, CUSTOMP])
    _, b1 = row(cv, 0, ty, [builtin, model, custom], gap=G)

    blk = Card(C3, "Block preview features", [
        "Tag AZML_DISABLE_PREVIEW_FEATURE=true on a subscription, resource group or resource (Contributor or Tag Contributor) hides preview surfaces in the new and classic portals",
        "Custom roles with notDataActions cover: Agent Service .../AIServices/agents/*, Evaluations .../AIServices/evaluations/*, Content Understanding .../MultiModalIntelligence/*, Fine-tuning .../OpenAI/{fine-tunes, files, uploads, stored-completions, evals, models}/*, Content Safety .../ContentSafety/*",
        "Tracing is blocked with control-plane notActions (Microsoft.Insights/... read)",
    ], theme="orange", icon="preview-features", src=[NOPREVIEW])
    ent = Card(C3, "Entra-side governance (not Azure RBAC)", [
        "AI Administrator, Global Administrator and agent sponsors or owners can block, unblock or delete agent identities",
        "Conditional Access Administrator manages Conditional Access; Entra roles are assigned in the Entra admin center",
        "See the canvas 'Agent identity and delegation' for the agent-identity lifecycle",
    ], theme="violet", icon="conditional-access", src=[ADMIN])
    lay = Card(C3, "Compliance layers", [
        "Microsoft Defender for Cloud (Security Admin or Owner): posture recommendations and threat protection",
        "Microsoft Purview (Foundry Account Owner): Audit, classification, DSPM for AI; not yet compatible with network isolation",
        "See the canvas 'Data protection, part 2: keys, secrets, storage and compliance' for the security baseline and compliance controls",
    ], theme="violet", icon="compliance", src=[ADMIN, CPCOMP])
    _, b2 = row(cv, 0, b1 + 40, [blk, ent, lay], gap=G)
    return b2


def section_cheat(cv, y):
    _, b = section_header(cv, 0, y, "5  Permission-error cheat sheet", size=34,
                          sub="Symptoms from the administrator guide and the fix it points to. Assign roles at the narrowest scope that works; allow up to about 5 minutes for propagation.")
    top = b + 34
    hw = (W - G) / 2
    t1 = Table([("Symptom", 500), "Fix"], [
        [("AuthorizationFailed", "red"), "A control-plane role is missing: assign it at the right scope (Contributor, Foundry Account Owner or Foundry Owner)"],
        [("roleAssignments/write error", "red"), "You cannot assign that role: you need Owner or RBAC Administrator"],
        [("ForbiddenError on a model deployment", "red"), "Use Foundry Account Owner"],
        [("LinkedAuthorizationFailed", "red"), "Missing permissions on the linked storage, Key Vault or search resource"],
        [("Publish Agent is disabled", "red"), "Foundry Project Manager must be assigned at the Foundry resource scope"],
    ], w=hw, theme="red", size=15, head_size=16, title="Control plane and role-assignment errors", title_size=22)
    t2 = Table([("Symptom", 500), "Fix"], [
        [("Agent creation fails with Owner or Contributor", "orange"),
         "Owner and Contributor hold no Foundry data actions: add Foundry User, Project Manager or Foundry Owner at the project"],
        [("Runtime 403", "orange"), "A data-plane role is missing on a backing resource"],
        [("Legacy Azure AI Developer assigned but it still fails", "orange"), "Use the Foundry roles instead"],
        [("'Could not resolve host' after adding a private endpoint", "orange"), "The private DNS zone is not linked to the VNet"],
        [("Authorization_RequestDenied from Microsoft Graph", "orange"), "A Microsoft Entra directory role is missing (assigned in Entra, not in IAM)"],
    ], w=hw, theme="orange", size=15, head_size=16, title="Data plane, identity and network errors", title_size=22)
    t1.place(cv, 0, top)
    t2.place(cv, hw + G, top)
    bot = max(t1.bottom, t2.bottom)
    cv.text(0, bot + 8, "Learn: Foundry administrator guide", size=12, color=LINK, link=ADMIN[1])
    return bot + 40


def build(cv: Canvas) -> None:
    _, bottom = title_block(cv, 0, 0, "Foundry roles, part 2: elevated tasks, feature roles and Azure Policy",
                            "Which tasks force Owner or User Access Administrator, what each feature adds, the project managed identity's role map and the policy guardrails - as of 2026-11-03",
                            icon="foundry", w=W)
    y = stamps(cv, bottom + 40) + 70
    y = section_tasks(cv, y) + 70
    y = section_identity(cv, y) + 60
    y = section_setup_flow(cv, y) + 70
    y = section_features(cv, y) + 70
    y = section_policy(cv, y) + 70
    y = section_cheat(cv, y) + 30
    nxt = Note(W, "Part 1 'Foundry roles, scopes and least-privilege assignments' covers the six Foundry roles, the scope ladder, the capability matrices and the places where Learn pages disagree. "
                  "See also 'Network isolation' for the Network Contributor and DNS requirements.", kind="key", title="Back to part 1", size=16)
    nxt.place(cv, 0, y)
    y = nxt.bottom + 60
    sources(cv, 0, y, [
        ("Foundry administrator guide", L("concepts/administrator-guide")),
        ("Role-based access control for Microsoft Foundry", L("concepts/rbac-foundry")),
        ("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions")),
        ("Standard agent setup", L("agents/concepts/standard-agent-setup")),
        ("Evaluation permissions", L("observability/how-to/evaluation-permissions")),
        ("Trace ingestion with Entra authentication", L("observability/how-to/trace-ingestion-entra-authentication")),
        ("Grant Agent 365 permissions", L("agents/how-to/grant-agent-365-permissions")),
        ("Publish agents to Teams and Microsoft 365", L("agents/how-to/publish-copilot")),
        ("Foundry IQ private retrieval tutorial", L("agents/how-to/foundry-iq-tutorial-private-retrieval")),
        ("Model deployment policy", L("how-to/model-deployment-policy")),
        ("Custom policy definitions", L("how-to/custom-policy-definition")),
        ("Disable preview features", L("how-to/disable-preview-features")),
        ("Azure AI services policy reference", L("policy-reference", base="azure/ai-services")),
        ("Manage compliance and security (control plane)", L("control-plane/how-to-manage-compliance-security")),
    ], w=W, cols=3)
