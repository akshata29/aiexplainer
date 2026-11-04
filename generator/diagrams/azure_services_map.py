"""Map of every Azure / Microsoft service that plugs into Foundry: hub-and-spoke diagram, BYO / auth / network pills, a service-by-service reference table, setup tiers, tool traffic, RBAC, flows."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.blocks import SAFETY
from generator.xd.palette import STATUS, theme as get_theme

META = dict(
    id="azure-services-map", title="Azure and Microsoft services around Foundry", section="7", order=4,
    description="Hub-and-spoke map of every Azure and Microsoft service that plugs into Foundry: the role it plays, which feature needs it, mandatory vs bring-your-own, and the connection, auth and network pattern.",
    tags=["services-map", "byo", "connections", "private-networking", "integrations", "rbac"],
)

W = 3300
GAP = 48
C4 = (W - 3 * GAP) // 4       # 789
C3 = (W - 2 * GAP) // 3       # 1068
C2 = (W - GAP) // 2           # 1626
ASOF = "as of 2026-11-03"


def L(path: str, slug: str | None = None, base: str = "azure/foundry"):
    """(label, url) for a Learn page; the label defaults to the last path segment."""
    return (slug or path.rstrip("/").split("/")[-1], learn(path, base=base))


# ---------------------------------------------------------------------------------------------- service data
# One entry per service: used for the tile in the map AND the row in the reference table.
# byo: M mandatory for the Standard agent setup | O optional bring-your-own | D Microsoft-managed by default | N/A another tenant | ? not documented
DISTRICTS = [
    dict(num="1", title="Data and knowledge", sub="state, files, vectors and enterprise data", theme="cyan",
         note=("key", "The mandatory BYO triad", "Standard agent setup needs your Cosmos DB + Storage + AI Search. Their private endpoints are not auto-created in the portal flow."), rows=[
        dict(name="Azure Cosmos DB (NoSQL)", icon="cosmos", role="agent state: threads and conversations", byo=["M"], auth=["MI"], net=["PE"],
             uses="Agent runtime state: threads, conversations and agent state (database enterprise_memory)",
             feat="Standard agent setup; Responses-API runtime", byo_txt="M - Basic setup is Microsoft-managed",
             conn="Capability settings documentStore or connection AzureCosmosDb (preview, code-only); project MI = Cosmos DB Operator + Built-in Data Contributor; private endpoint sub-resource Sql, privatelink.documents.azure.com",
             learn=L("agents/concepts/standard-agent-setup")),
        dict(name="Azure AI Search", icon="ai-search", role="vector store, AI Search tool, Foundry IQ", byo=["M"], auth=["MI", "Keys"], net=["PE"],
             uses="Vector store for file search (standard setup), the AI Search tool and Foundry IQ knowledge bases",
             feat="Standard setup (vectorStore); AI Search tool; Foundry IQ", byo_txt="M for the vector store; a separate service is fine for Foundry IQ or the tool",
             conn="Connection CognitiveSearch (AAD or ApiKey) or RemoteTool (knowledge-base MCP); roles Search Index Data Reader / Contributor + Search Service Contributor; private endpoint privatelink.search.windows.net; outbound shared private links",
             learn=L("agents/how-to/tools/ai-search")),
        dict(name="Azure Storage (Blob, ADLS, Queue)", icon="storage", role="agent files, eval data, Functions queues", byo=["M"], auth=["MI"], net=["PE"],
             uses="Agent files (blobStore); evaluation data and datasets (connections); Content Understanding; Speech / Language userOwnedStorage (set at creation, immutable); queues for the Functions tool",
             feat="Standard setup; evaluations; Azure Functions tool; Speech tool (SAS)", byo_txt="M for Standard; O or D otherwise (managed by default)",
             conn="Account needs allowSharedKeyAccess=false, TLS 1.2, allowBlobPublicAccess=false; project MI Storage Blob Data Contributor (Queue Data Contributor for Functions); private endpoint privatelink.blob.core.windows.net",
             learn=L("how-to/bring-your-own-azure-storage-foundry")),
        dict(name="Microsoft Fabric, OneLake, Power BI", icon="fabric", role="Fabric IQ tool: ontology, semantic model", byo=["N/A"], auth=["OBO", "OAuth"], net=["Public", "PE"], badge="preview",
             uses="Fabric IQ tool (ontology, semantic model, data agent); the Fabric data agent tool is scheduled for deprecation on 2026-11-06; AI Search OneLake knowledge source; Cosmos mirroring target",
             feat="Fabric IQ", byo_txt="N/A - your Fabric tenant and capacity",
             conn="On-behalf-of user / OAuth; connection type 'Microsoft Fabric' (preview); public, or tenant / workspace private link, depending on the item type",
             learn=L("agents/how-to/tools/fabric-iq")),
        dict(name="Azure Databricks", icon="databricks", role="Jobs and Genie as tools", byo=["N/A"], auth=["Entra", "OBO"], net=[], badge="preview",
             uses="Jobs, Genie and other Databricks capabilities as tools", feat="Databricks tools", byo_txt="N/A",
             conn="Connection type 'Azure Databricks' (preview; SDK-only as a FunctionTool; Entra auth); Genie MCP via on-behalf-of user (AgentOnBehalfOfUser)",
             learn=L("how-to/connections-add")),
        dict(name="SharePoint and OneDrive (M365)", icon="sharepoint", role="SharePoint tool and knowledge source", byo=["N/A"], auth=["OBO"], net=["Public"], badge="preview",
             uses="SharePoint tool (preview): grounding over a SharePoint site or folder with identity passthrough; AI Search SharePoint knowledge source; Work IQ SharePoint / OneDrive tools",
             feat="SharePoint tool", byo_txt="N/A - your Microsoft 365 tenant",
             conn="On-behalf-of user only (no app-only identity); connection type 'SharePoint' (preview, code-only); public endpoint; same tenant; one SharePoint tool per agent; needs a Microsoft 365 Copilot license or pay-as-you-go retrieval; does not work when published to Teams",
             learn=L("agents/how-to/tools/sharepoint")),
        dict(name="Azure SQL", icon="sql", role="AI Search knowledge source", byo=["N/A"], auth=[], net=["PE"], badge="preview",
             uses="Source for an AI Search knowledge source (preview)", feat="Foundry IQ indexed knowledge source", byo_txt="N/A",
             conn="Shared private link group sqlServer", learn=L("azure/search/agentic-knowledge-source-overview", base="")),
    ]),
    dict(num="2", title="Models and AI services", sub="models, Foundry Tools and web grounding", theme="blue",
         note=("warn", "Model deployments", "Cross-subscription connections for model deployments are unsupported."), rows=[
        dict(name="Azure OpenAI and model deployments", icon="openai", role="chat + embedding models, KB, Memory, eval judge", byo=["D"], auth=[], net=[],
             uses="Chat and embedding models for agents; knowledge-base planning and synthesis; Memory (chat + embedding); evaluation judge",
             feat="Agents, Foundry IQ, Memory, evaluations", byo_txt="D in-resource, or an 'Azure OpenAI' connection",
             conn="The Search service MI needs Cognitive Services User for a knowledge base; cross-subscription connections for model deployments are unsupported",
             learn=L("how-to/connections-add")),
        dict(name="Azure Speech", icon="speech", role="Speech MCP tool", byo=["O"], auth=["Keys"], net=["n/s"], badge="preview",
             uses="Azure Speech MCP tool", feat="Speech tool", byo_txt="O",
             conn="Key-based; Blob SAS container URL; not supported in network-secured Foundry; the page says the MCP needs the Agent Service Enterprise tier",
             learn=L("agents/how-to/tools/azure-ai-speech")),
        dict(name="Azure Language", icon="language", role="Language MCP, CLU + CQA agents", byo=["O"], auth=["Keys"], net=["Public"], badge="preview",
             uses="Language MCP server (https://{foundry-resource-name}.cognitiveservices.azure.com/language/mcp, api-version 2025-11-15-preview); intent-routing agent (CLU + CQA); exact question-answering agent (CQA)",
             feat="Language tools", byo_txt="O - needs an Azure Language resource",
             conn="Custom connection (Custom keys, header Ocp-Apim-Subscription-Key); network-secured projects may require a public MCP",
             learn=L("azure/ai-services/language-service/concepts/foundry-tools-agents", base="")),
        dict(name="Vision, Document Intelligence, Content Understanding", icon="vision", role="Foundry Tools resource kinds", byo=["?"], auth=[], net=[],
             uses="Foundry Tools resource kinds; Content Understanding sits under AIServices and can use a Storage connection", feat="Not verified in the pages read",
             byo_txt="? - check docs", conn="Not verified in the pages read", learn=L("concepts/architecture")),
        dict(name="Azure AI Content Safety", icon="content-safety", role="classifiers behind guardrails", byo=["D"], auth=[], net=[],
             uses="Classifiers behind guardrails at user input, tool call (preview), tool response (preview) and output; default policy Microsoft.DefaultV2; agent guardrails are in preview",
             feat="Guardrails / control plane", byo_txt="D", conn="Managed by Foundry", learn=L("guardrails/guardrails-overview")),
        dict(name="Bing (Web Search, Grounding, Custom Search)", icon="bing", role="Web Search, Grounding with Bing, Custom Search", byo=["D", "O"], auth=[], net=["Public"],
             uses="Public-web grounding", feat="Web tools", byo_txt="D for Web Search (managed Bing); O for Grounding with Bing (your Bing resource)",
             conn="Connection type 'Grounding with Bing Search'; Microsoft.Bing provider; public endpoint; data protection addendum not applicable",
             learn=L("agents/how-to/tools/web-overview")),
        dict(name="Web IQ (api.microsoft.ai)", icon="iq", role="AI-native web APIs via MCP", byo=["O"], auth=["Keys", "Entra"], net=["Public"],
             uses="AI-native web APIs via MCP (see the iq-layer canvas)", feat="Web IQ MCP tool or knowledge source", byo_txt="O - your own Web IQ resource (paid subscription)",
             conn="x-apikey or Entra; public only", learn=L("web-iq/overview", base="")),
        dict(name="Azure Machine Learning (hub-based, legacy)", icon="ml", role="legacy hub-based projects", byo=[], auth=[], net=[], badge="classic",
             uses="Legacy project model", feat="None for new features", byo_txt="-",
             conn="No upgrade path from hub-based to new projects; hub-based is not supported for Foundry IQ connect; Microsoft.MachineLearningServices provider still registered; az ml does not support new projects; legacy -azureml- blob container names",
             learn=L("agents/how-to/use-your-own-resources")),
    ]),
    dict(num="3", title="Identity, security and governance", sub="who can act, what is encrypted, what is allowed", theme="red",
         note=("gotcha", "RBAC is not automatic", "An agent identity starts with no permissions. Defender and Purview are toggles in the Compliance workspace; Purview has no network isolation support yet."), rows=[
        dict(name="Microsoft Entra ID and Agent ID", icon="app-registrations", role="project MI, agent identity, OBO, OAuth", byo=["D"], auth=["Agent ID", "OBO", "OAuth"], net=[],
             uses="Project managed identity; agent identity blueprint (federated credential trusting the first-party Azure Machine Learning resource provider app 0736f41a-0425-4b46-bdb5-1563eff02385) + per-agent identity; OBO; OAuth; tenant-wide agent inventory; Conditional Access, Identity Protection, sign-in and audit logs",
             feat="All authentication", byo_txt="D",
             conn="Four-stage token exchange for an agent identity (blueprint credentials, agent token, scoped token, call); hosted agents get tokens via a token service; RBAC is NOT auto-assigned (an agent identity starts with no permissions)",
             learn=L("agents/concepts/agent-identity")),
        dict(name="Azure RBAC (Foundry roles)", icon="pim", role="Foundry User, Project Manager, Account Owner, Owner", byo=["D"], auth=[], net=[],
             uses="Foundry User, Foundry Project Manager, Foundry Account Owner, Foundry Owner; Foundry Agent Consumer (toolbox)", feat="Access control", byo_txt="D",
             conn="Role IDs are unchanged by the 2026 rename (formerly Azure AI ...)", learn=L("concepts/rbac-foundry")),
        dict(name="Azure Key Vault", icon="key-vault", role="connection secrets, customer-managed keys", byo=["O"], auth=[], net=[],
             uses="Connection secrets (without a Key Vault connection they sit in a managed vault that does not show in your subscription); customer-managed keys", feat="BYO Key Vault connection (AzureKeyVault); CMK", byo_txt="O - default is a Microsoft-managed Key Vault (the standard-agent-setup page lists a vault as a prerequisite - docs differ)",
             conn="One Key Vault connection per Foundry resource; no secret migration (recreate connections after attaching); deleting the vault breaks the resource; create the connection first in IaC; roles Key Vault Secrets Officer / Contributor / Administrator (up to 30 min to propagate). CMK: same-region vault, soft delete + purge protection, Key Vault Crypto User",
             learn=L("concepts/customer-managed-keys")),
        dict(name="Microsoft Defender for Cloud", icon="defender", role="threat protection, security posture", byo=["O"], auth=[], net=[],
             uses="Threat protection for Foundry Tools (for example jailbreak alerts); Compliance workspace 'Security posture'", feat="Control plane", byo_txt="O",
             conn="Security Admin or Owner", learn=L("control-plane/how-to-manage-compliance-security")),
        dict(name="Microsoft Purview", icon="info-protection", role="audit, DSPM for AI, eDiscovery", byo=["O"], auth=[], net=["n/s"],
             uses="Toggle on the account: Audit, DSPM for AI, eDiscovery; a Purview connection for eDiscovery of Agent Service state; AI Search Purview labels (preview)", feat="Compliance", byo_txt="O",
             conn="Needs Foundry Account Owner; no network isolation support yet; pay-as-you-go or an Agent 365 subscription, otherwise audit only; DSPM policies need Entra user context on /chat/completions",
             learn=L("control-plane/how-to-manage-compliance-security")),
        dict(name="Azure Policy", icon="policy", role="approved models, block public tools", byo=["O"], auth=[], net=[],
             uses="Guardrail policies; built-ins 'Foundry model deployments should only use approved models' (allowedPublishers, allowedAssetIds prefix match; Deny / Audit) and '... should meet eligibility requirements' (onlyAllowDirectFromAzure, denyPreviewModels); denyAction + locks for HA; can block public-endpoint tools",
             feat="Governance", byo_txt="O", conn="Owner or Resource Policy Contributor", learn=L("how-to/model-deployment-policy")),
    ]),
    dict(num="4", title="Observability, evaluation and CI/CD", sub="traces, logs and automated agent evaluation", theme="violet",
         note=("info", "Tracing is off by default", "Connect Application Insights to get OpenTelemetry traces. Diagnostic settings are separate (up to 2 h latency). Evaluation in GitHub Actions and Azure DevOps is preview."), rows=[
        dict(name="Application Insights and Log Analytics", icon="app-insights", role="OpenTelemetry traces (off by default)", byo=["O"], auth=[], net=["PE"],
             uses="OpenTelemetry traces of agent runs and tool calls", feat="Tracing (off by default)", byo_txt="O - connect your Application Insights",
             conn="Application Insights connection; viewers need Log Analytics Reader / Monitoring Reader (+ Privileged Monitoring Data Reader for protected tables); App Insights Private Link scope; hosted-agent permissions in hosted-agent-permissions",
             learn=L("observability/concepts/trace-agent-concept")),
        dict(name="Diagnostic settings sinks", icon="diagnostics", role="resource logs to Log Analytics, Storage, Event Hubs", byo=["O"], auth=[], net=[],
             uses="Resource logs: Audit, RequestResponse, Azure OpenAI Request Usage, AllMetrics", feat="Diagnostic logging", byo_txt="O",
             conn="Sinks: Log Analytics, Storage (container insights-logs-<category>), Event Hubs; up to 2 h latency", learn=L("how-to/diagnostic-logging")),
        dict(name="GitHub Actions", icon="github", role="CI/CD agent evaluation", byo=["O"], auth=["Entra"], net=[], badge="preview",
             uses="CI/CD agent evaluation; routines trigger", feat="Evaluations (preview)", byo_txt="O",
             conn="Action microsoft/ai-agent-evals@v3-beta with azure/login OIDC (inputs azure-ai-project-endpoint, deployment-name, data-path, agent-ids as name:version, baseline-agent-id)",
             learn=L("how-to/evaluation-github-action")),
        dict(name="Azure DevOps", icon="devops", role="CI/CD agent evaluation, ADO MCP", byo=["O"], auth=["Entra", "OBO"], net=[], badge="preview",
             uses="CI/CD agent evaluation; Azure DevOps MCP", feat="Evaluations (preview)", byo_txt="O",
             conn="Task AIAgentEvaluation@2 via an ARM service connection (AzureCLI@2); the Azure DevOps MCP uses on-behalf-of user",
             learn=L("how-to/evaluation-azure-devops")),
    ]),
    dict(num="5", title="Compute, hosting and API layer", sub="where agent code, tools and gateways run", theme="green", rows=[
        dict(name="Azure Container Registry / BYO registry", icon="acr", role="hosted-agent images", byo=["D", "O"], auth=["Agent ID"], net=["PE"],
             uses="Hosted-agent images", feat="Hosted agents", byo_txt="D - azd ai agent init creates a project ACR; O - bring your own",
             conn="BYO ACR roles: developer AcrPush (local build) / Container Registry Tasks Contributor (remote build) / Repository Writer (ABAC); the agent identity gets AcrPull; private ACR supported for projects created after 2026-06-25; non-Azure registry via OIDC token exchange (CustomKeys connection, type=registry_connection, mode=oauth_token_exchange; JFrog validated; Docker Distribution needs an adapter)",
             learn=L("agents/how-to/deploy-hosted-agent-private-azure-container-registry")),
        dict(name="Azure Container Apps", icon="container-apps", role="hosted-agent micro-VMs, private MCP", byo=["D", "O"], auth=[], net=["VNet"],
             uses="Hosted agents run on Container Apps-based micro-VMs in your delegated subnet (each session in a VM-isolated sandbox); private MCP servers (internal-only ingress + dedicated MCP subnet); host of the Cosmos DB MCP Toolkit",
             feat="Hosted agents; private MCP", byo_txt="D (platform) / O (your MCP server)",
             conn="Microsoft.App provider; subnet delegated to Microsoft.App/environments", learn=L("agents/concepts/hosted-agents")),
        dict(name="Azure Functions", icon="functions", role="Functions tool, custom MCP host", byo=["O"], auth=["MI", "Keys"], net=["VNet"],
             uses="(a) Azure Functions tool: queue-based AzureFunctionTool; (b) host for custom remote MCP servers (endpoint https://{app}.azurewebsites.net/runtime/webhooks/mcp)",
             feat="Functions tool (needs the Standard setup); custom MCP", byo_txt="O",
             conn="Tool: Storage queues, Storage Queue Data Contributor for the project MI and the function MI, Flex Consumption recommended. MCP auth: function keys x-functions-key / Entra (project MI) / OAuth passthrough / unauthenticated (not recommended); network through the VNet subnet",
             learn=L("agents/how-to/tools/azure-functions")),
        dict(name="AKS and App Service", icon="aks", role="no documented first-party integration", byo=["?"], auth=[], net=[],
             uses="No Foundry-specific integration page read; the Search shared private link 'sites' covers Functions and App Service; Microsoft.ContainerService appears in network-setup provider lists",
             feat="-", byo_txt="? - unverified", conn="Unverified", learn=None),
        dict(name="Azure API Center", icon="api", role="private MCP tool catalog", byo=["O"], auth=[], net=[],
             uses="Private organisational tool (MCP) catalog: register an MCP server (Inventory, Assets, Register an asset, MCP server), Governance > Authorization (API key / OAuth / HTTP), Manage Access (preview); appears in Foundry Build > Tools",
             feat="Private tool catalog", byo_txt="O", conn="Foundry shows catalog servers; limit enabled tools to least privilege",
             learn=L("mcp/build-your-own-mcp-server")),
        dict(name="API Management (AI gateway)", icon="apim", role="AI gateway: TPM, quota, MCP governance", byo=["O"], auth=["Keys"], net=[],
             uses="Foundry-managed AI gateway in front of model calls: per-project TPM / quota (429 for TPM, 403 for quota), MCP tool governance, bring-your-own-model via a gateway connection",
             feat="AI gateway", byo_txt="O - new projects enabled by default; Basic v2 APIM created or a v2 tier reused; Standard v2 / Premium v2 for production or private",
             conn="Same tenant and subscription; connection types 'Azure APIM (preview)' and 'Model Gateway (preview)'; APIM subscription key; a gateway created from a private Foundry is public - harden it in the Azure portal; Search shared private link 'Gateway'; can also front Web IQ",
             learn=L("configuration/enable-ai-api-management-gateway-portal")),
    ]),
    dict(num="6", title="Integration and channels", sub="connectors, routines and where users meet agents", theme="orange",
         note=("warn", "Network-isolated projects", "The Logic Apps tool is not supported; portal publish is unsupported when public access is disabled."), rows=[
        dict(name="Logic Apps and Connector namespaces", icon="logic-apps", role="managed MCP servers, 1,000+ connectors", byo=["O"], auth=["OAuth"], net=["n/s"], badge="preview",
             uses="Managed MCP servers via a Connector Namespace per Foundry account: 1,000+ connectors, per-project environment, OAuth2 only in the portal, triggers not supported there; event triggers for routines (Teams channel message)",
             feat="Managed MCP; routines", byo_txt="O", conn="The Logic Apps tool is not supported in network-isolated projects ('under development')",
             learn=L("agents/how-to/tools/connectors")),
        dict(name="Event Grid, Service Bus, Event Hubs", icon="event-grid", role="no native Foundry triggers", byo=["?"], auth=[], net=[],
             uses="No native Foundry triggers; routines = timer / recurring (min 5 min) / event (GitHub issue, Teams channel message via a connector namespace); Event Hubs is a diagnostics sink; Azure Functions 'hosted skills' (preview, a separate Azure product) can trigger from them",
             feat="-", byo_txt="? - adjacent only", conn="Adjacent only", learn=L("agents/concepts/routines")),
        dict(name="Azure Bot Service, Teams, M365 Copilot", icon="bot", role="publish channel (Activity protocol)", byo=["D"], auth=[], net=[],
             uses="Publishing creates an Azure Bot Service resource (Microsoft.BotService; Azure Bot Service Contributor); Activity protocol; auth schemes BotServiceRbac (just you) / BotServiceTenant (org; M365 admin center approval)",
             feat="Publish to Teams / Copilot", byo_txt="D - created on publish",
             conn="Portal publish unsupported for public-access-disabled projects (REST enable_m365_public_endpoint; see the VNet publish page); the SharePoint tool does not work when published to Teams",
             learn=L("agents/how-to/publish-copilot")),
        dict(name="Copilot Studio", icon="power-platform", role="connection type; KB via a Foundry agent", byo=["O"], auth=[], net=[],
             uses="Connection type 'Copilot Studio Environment'; a Foundry IQ knowledge base reaches Copilot Studio through a Foundry agent", feat="Integration", byo_txt="O",
             conn="-", learn=L("how-to/connections-add")),
        dict(name="Agent 365 autopilots", icon="copilot", role="M365-resident agents (video/blog)", byo=["?"], auth=[], net=[],
             uses="Autopilots: own M365 identity, activity protocol v1, Azure Bot Service, M365 admin approval (video / blog-sourced, not in Learn)", feat="M365-resident agents",
             byo_txt="? - video / blog", conn="Pamela Fox's Work IQ write-up (secondary source)", learn=None),
        dict(name="VNet, Private DNS, Azure Firewall", icon="vnet", role="network fabric of the hub", byo=["O"], auth=[], net=["VNet", "PE"], hub=True,
             uses="Delegated agent subnet; private DNS; hub-and-spoke egress inspection", feat="Network-secured setups", byo_txt="O",
             conn="Foundry must be in the VNet's region (other resources may differ); allow-list entries on the firewall", learn=L("agents/how-to/virtual-networks")),
    ]),
]

TAGS = {"M": "red", "O": "blue", "D": "green", "N/A": "gray", "?": "yellow"}
AUTH_TH, NET_TH = "pink", "indigo"
NET_THEMES = {"Public": "orange", "n/s": "gray"}


# ---------------------------------------------------------------------------------------------- local helpers
def badge_w(kind: str, size=13) -> float:
    _, label = STATUS.get(kind, ("gray", kind))
    return metrics.line_width(label, size) + 18


def pill_w(label: str, size=12) -> float:
    return metrics.line_width(label, size) + 14


def pill(cv, x, y, label, theme, *, size=12, h=22):
    th = get_theme(theme)
    w = pill_w(label, size)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0)
    cv.text(x + 7, y + (h - size * metrics.line_ratio()) / 2, label, size=size, color=th.deep)
    return w


class Node(Rect2):
    """Service tile: icon, name, one-line role and BYO / auth / network pills. Dashed outline = preview."""

    def __init__(self, w, d, theme, *, size=16, role_size=13, pad=10, icon_size=30):
        self.th = get_theme(theme)
        self.w, self.d, self.size, self.role_size, self.pad, self.icon_size = w, d, size, role_size, pad, icon_size
        self.badge = d.get("badge")
        self.link = d["learn"][1] if d.get("learn") else None
        bw = badge_w(self.badge) + 6 if self.badge else 0
        name_w = (w - 2 * pad - icon_size - 8 - bw) * SAFETY
        self.name_lines = metrics.wrap_text(d["name"], name_w, size)
        self.role_lines = metrics.wrap_text(d["role"], (w - 2 * pad) * SAFETY, role_size)
        lr = metrics.line_ratio()
        self.head_h = max(icon_size, len(self.name_lines) * size * lr)
        self.pills = ([(t, TAGS.get(t, "gray")) for t in d.get("byo", [])] + [(a, AUTH_TH) for a in d.get("auth", [])]
                      + [(n, NET_THEMES.get(n, NET_TH)) for n in d.get("net", [])])
        row_w = sum(pill_w(t) for t, _ in self.pills) + 6 * max(0, len(self.pills) - 1)
        self.pill_h = 22 if self.pills else 0
        self.h = pad + self.head_h + 4 + len(self.role_lines) * role_size * lr + 8 + self.pill_h + pad
        self.overflow = row_w > w - 2 * pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, lr = self.th, self.pad, metrics.line_ratio()
        if self.overflow:
            cv.warn(f"pills overflow in node {self.d['name']!r}")
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill="#ffffff", style="solid", sw=2,
                    dash="dashed" if self.badge == "preview" else "solid", link=self.link)
            place_icon(cv, self.d["icon"], x + pad, y + pad, self.icon_size)
            ty = y + pad + (self.head_h - len(self.name_lines) * self.size * lr) / 2
            cv.text(x + pad + self.icon_size + 8, ty, "\n".join(self.name_lines), size=self.size, color=th.deep)
            if self.badge:
                draw_badge(cv, x + self.w - pad - badge_w(self.badge), y + 8, self.badge)
            ry = y + pad + self.head_h + 4
            cv.text(x + pad, ry, "\n".join(self.role_lines), size=self.role_size, color=MUTED)
            px = x + pad
            py = y + H - pad - self.pill_h
            for label, pth in self.pills:
                px += pill(cv, px, py, label, pth) + 6
        cv.register(f"node:{self.d['name']}", x, y, self.w, H)
        return self


def band(cv, y, n, title, sub=None, theme="blue"):
    numbered(cv, 24, y + 27, n, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 66, y, title, sub=sub, size=34, w=W - 66, sub_size=17)
    return bottom + 26


def steps(cv, x, y, w, items, theme="blue", size=16, detail_size=14):
    """Vertical numbered steps joined by a dotted line; returns the bottom y."""
    th = get_theme(theme)
    lr = metrics.line_ratio()
    tx, tw = x + 42, (w - 42) * SAFETY
    cy = y
    for i, it in enumerate(items, 1):
        title, detail = (it, None) if isinstance(it, str) else it
        tl = metrics.wrap_text(title, tw, size)
        dl = metrics.wrap_text(detail, tw, detail_size) if detail else []
        h = max(len(tl) * size * lr + (len(dl) * detail_size * lr + 2 if dl else 0), 30)
        numbered(cv, x + 15, cy + 15, i, theme=theme, d=30, size=17)
        cv.text(tx, cy + 2, "\n".join(tl), size=size, color=INK)
        if dl:
            cv.text(tx, cy + 2 + len(tl) * size * lr + 2, "\n".join(dl), size=detail_size, color=MUTED)
        nxt = cy + h + 12
        if i < len(items):
            cv.line((x + 15, cy + 32), (x + 15, nxt + 1), stroke=th.stroke, sw=2, dash="dotted")
        cy = nxt
    return cy - 12


def cite(cv, x, y, items, size=12):
    cy = y
    for label, url in items:
        t = cv.text(x, cy, f"Learn: {label}", size=size, color=LINK, link=url)
        cy = t.bottom + 2
    return cy


def legend_group(cv, x, y, w, title, pairs, theme="gray"):
    """Panel with wrapped (pill, explanation) pairs; returns the panel."""
    with cv.panel(x, y, title=title, theme=theme, style="dotted", fill="none", pad=16, title_size=20, w=w) as p:
        cx, cy = p.ix, p.iy
        for label, th_name, text in pairs:
            tw = metrics.line_width(text, 14)
            need = pill_w(label) + 8 + tw + 22
            if cx > p.ix and cx + need > x + w - 16:
                cx, cy = p.ix, cy + 30
            pill(cv, cx, cy, label, th_name)
            cv.text(cx + pill_w(label) + 8, cy + 2, text, size=14, color=INK)
            cx += need
    return p


def district_rows(d, nw):
    """Tile rows (3 per row) of one district plus an optional note that fills free slots or adds a row.

    Returns (rows, heights) where rows = [[(col, block, span), ...], ...]."""
    nodes = [Node(nw, r, d["theme"]) for r in d["rows"] if not r.get("hub")]
    rows = [[(j, n, 1) for j, n in enumerate(nodes[i:i + 3])] for i in range(0, len(nodes), 3)]
    note = d.get("note")
    if note:
        kind, title, text = note
        free = 3 - len(rows[-1])
        if free > 0:
            span = free
            nt = Note(span * nw + (span - 1) * 14, text, kind=kind, title=title, size=13, title_size=16)
            rows[-1].append((3 - span, nt, span))
        else:
            nt = Note(3 * nw + 2 * 14, text, kind=kind, title=title, size=13, title_size=16)
            rows.append([(0, nt, 3)])
    return rows, [max(b.h for _, b, _ in r) for r in rows]


def panel_height(d, nw, pad=22, title_size=26, sub_size=15):
    lr = metrics.line_ratio()
    _, heights = district_rows(d, nw)
    content = sum(heights) + 14 * (len(heights) - 1)
    hdr = pad + (title_size * lr + 6 + sub_size * lr + 2 + 8)
    return hdr + content + pad


# ---------------------------------------------------------------------------------------------- band 0: legend + summary
def top_legend(cv, y):
    w = C3
    g1 = legend_group(cv, 0, y, w, "BYO status of each service", [
        ("M", "red", "mandatory for the Standard agent setup"), ("O", "blue", "optional bring-your-own"),
        ("D", "green", "Microsoft-managed by default"), ("N/A", "gray", "another tenant or service"),
        ("?", "yellow", "not documented or unverified")])
    g2 = legend_group(cv, w + GAP, y, w, "Auth pattern", [
        ("MI", AUTH_TH, "project managed identity (project-managed-identity)"),
        ("Agent ID", AUTH_TH, "agent identity (agentic-identity); starts with no permissions"),
        ("OBO", AUTH_TH, "on-behalf-of user (UserEntraToken, AgentOnBehalfOfUser)"),
        ("OAuth", AUTH_TH, "in-conversation OAuth (oauth2, oauth_consent_request)"),
        ("Keys", AUTH_TH, "keys and secrets (custom-keys, API key)"), ("Entra", AUTH_TH, "Entra token or OIDC")])
    g3 = legend_group(cv, 2 * (w + GAP), y, w, "Network pattern", [
        ("VNet", NET_TH, "through your agent subnet (Microsoft.App/environments)"), ("PE", NET_TH, "private endpoint"),
        ("Backbone", NET_TH, "Microsoft backbone"), ("Public", "orange", "public endpoint"), ("n/s", "gray", "not supported in network-isolated projects")])
    return max(g1.bottom, g2.bottom, g3.bottom)


def band_summary(cv, y):
    cards = [
        Card(C4, "How to read the map", [
            "Hub = the Foundry resource (Microsoft.CognitiveServices/accounts, kind AIServices) and its projects",
            "Six districts = the Azure and Microsoft services around it; one tile per service",
            "Each tile shows BYO status, auth pattern and network pattern; the tables below give the detail and a Learn link",
        ], theme="gray", icon="foundry", src=[("Foundry architecture", learn("concepts/architecture"))]),
        Card(C4, "What is mandatory", [
            "BYO is mandatory only for the Standard agent setup: Cosmos DB + Storage + AI Search",
            "Optional BYO: Container Registry, Application Insights, the APIM gateway and a Key Vault connection (the standard-agent-setup page lists a vault among its prerequisites - docs differ)",
            "Everything else is managed by default or lives in another tenant or service",
        ], theme="red", icon="key-vault", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))]),
        Card(C4, "Network reality check", [
            "Web search, Grounding with Bing, SharePoint and Work IQ use public endpoints even in private projects",
            "Private endpoints to Search, Storage and Cosmos DB are NOT auto-created by the portal flow",
            "Several connection types are still preview: Cosmos DB, Fabric, Databricks, SharePoint, serverless models",
        ], theme="indigo", icon="private-link", src=[("Tool network isolation", learn("agents/how-to/tools/toolbox-network-isolation"))]),
        Card(C4, "Not documented (as of 2026-11-03)", [
            "Event Grid, Service Bus, AKS and App Service have no documented first-party Foundry integration in the pages read",
            "Event Hubs appears only as a diagnostics sink; Functions 'hosted skills' are an adjacent Azure Functions feature",
            "Vision, Document Intelligence and Content Understanding feature mappings were not verified",
        ], theme="yellow", icon="info-protection", src=[("Routines", learn("agents/concepts/routines"))]),
    ]
    _, b = row(cv, 0, y, cards, gap=GAP)
    return b


# ---------------------------------------------------------------------------------------------- band 1: hub and spoke
SPOKES = {
    "1": ("connections: project MI + RBAC, private endpoints", "solid"),
    "2": ("model deployments and Foundry Tools connections", "dashed"),
    "3": ("identity, secrets, policy, compliance", "solid"),
    "4": ("traces, diagnostic logs, CI evaluation", "dashed"),
    "5": ("hosted agents, MCP / Functions tools, AI gateway", "solid"),
    "6": ("managed MCP, routines, publish to Teams", "dashed"),
}


def hub_map(cv, y):
    y = band(cv, y, "1", "The map: the Foundry resource in the middle, six districts around it",
             sub=f"Dashed tile = preview ({ASOF}). Spokes: solid = managed identity + RBAC; dashed = connection with key or OAuth (the dominant pattern; the pills on each tile give the detail)",
             theme="blue")
    gx = 60
    pw = (W - 2 * gx) // 3
    nw = (pw - 44 - 2 * 14) // 3
    hts = [panel_height(d, nw) for d in DISTRICTS]
    top_h, bot_h = max(hts[:3]), max(hts[3:])
    yt = y
    spoke = 110
    yh = yt + top_h + spoke
    hub_h = 300
    yb = yh + hub_h + spoke
    panels = {}
    for idx, d in enumerate(DISTRICTS):
        col = idx % 3
        py = yt if idx < 3 else yb
        px = col * (pw + gx)
        with cv.panel(px, py, title=f"{d['num']}  {d['title']}", sub=d["sub"], theme=d["theme"], style="dashed", fill="soft", pad=22,
                      title_size=26, sub_size=15, w=pw, min_h=(top_h if idx < 3 else bot_h)) as p:
            rows_, heights_ = district_rows(d, nw)
            ny = p.iy
            for r_, hh in zip(rows_, heights_):
                for col_, blk, span in r_:
                    blk.place(cv, p.ix + col_ * (nw + 14), ny, h=hh)
                ny += hh + 14
        panels[d["num"]] = p

    # hub band
    with cv.panel(0, yh, title="HUB - Microsoft Foundry: the resource, its projects and the network fabric", theme="gray", style="solid", fill="soft", pad=24,
                  title_size=28, w=W, min_h=hub_h) as hub:
        hgap = 130
        cw = (W - 48 - 2 * hgap) // 3
        ca = Card(cw, "Foundry resource", [
            "Microsoft.CognitiveServices/accounts, kind AIServices: the governance boundary",
            "Model deployments, connections, guardrails and diagnostics live here",
            "Connected resources (Search = Microsoft.Search, Cosmos DB, Storage ...) are independent Azure resources with their own governance",
        ], theme="blue", icon="foundry", src=[("Foundry architecture", learn("concepts/architecture"))])
        cb = Card(cw, "Projects", [
            "Agents, evaluations and files behind a project endpoint, with a project managed identity",
            "Capability settings (or a capability host) point agent state at your Cosmos DB, Storage and AI Search",
            "Connections reference Key Vault, Application Insights, the APIM gateway, Bing, Fabric and more",
        ], theme="green", icon="agent", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
        cc = Card(cw, "Network fabric", [
            "BYO VNet: agent subnet delegated to Microsoft.App/environments; Foundry in the VNet's region (other resources may differ)",
            "Or a Managed virtual network",
            "Private endpoints (not auto-created), Private DNS and Azure Firewall allow-lists",
        ], theme="indigo", icon="vnet", src=[("Configure private link", learn("how-to/configure-private-link")), ("Virtual networks", learn("agents/how-to/virtual-networks"))])
        hh = max(ca.h, cb.h, cc.h)
        for i, c in enumerate((ca, cb, cc)):
            c.place(cv, hub.ix + i * (cw + hgap), hub.iy, h=hh)
        connect(cv, ca, cb, a_side="right", b_side="left", label="contains", label_size=14)
        connect(cv, cb, cc, a_side="right", b_side="left", label="injected into", label_size=14, dash="dashed")

    # spokes
    for idx, d in enumerate(DISTRICTS):
        p = panels[d["num"]]
        label, dash = SPOKES[d["num"]]
        th = get_theme(d["theme"])
        xc = p.x + p.w / 2
        if idx < 3:
            pts = [(xc, p.bottom + 6), (xc, hub.y - 6)]
        else:
            pts = [(xc, hub.bottom + 6), (xc, p.y - 6)]
        arrow(cv, pts, dash=dash, color=th.stroke, sw=3, start_head="arrow", end_head="arrow", label=label, label_size=15, label_wrap=360,
              label_dx=0)
    return panels["4"].bottom


# ---------------------------------------------------------------------------------------------- band 2: patterns
def patterns(cv, y):
    y = band(cv, y, "2", "Patterns that cut across services: setup tiers, tool traffic and roles",
             sub="Which resources you bring, which tool calls stay private, who needs which role", theme="indigo")
    t_tier = Table(
        [("", 190), ("Basic agent setup", 400), ("Standard agent setup", 500), "Network-secured standard (BYO VNet or private link)"],
        [
            [("Data resources", "gray"), "Microsoft-managed (portal fields for Storage, Search and Cosmos DB left empty)", "BYO Cosmos DB + Storage + AI Search",
             "Same, plus private endpoints (not auto-created), a delegated agent subnet and DNS zones"],
            [("Needed for", "gray"), "Quick start; the AI Search tool against a public Search service",
             "Azure Functions tool (queue-based), Azure Blob files in file search, control over data, DR", "Private Search, private MCP, OpenAPI, A2A and Functions through the VNet"],
            [("Networking choice", "gray"), "Public or private endpoint", "Same", "BYO VNet (delegated subnet) or a Managed virtual network"],
        ], w=C2, theme="indigo", size=14, head_size=15, title="Three setup tiers", title_size=22)
    n_tpl = Note(C2, "Templates in microsoft-foundry/foundry-samples/infrastructure: 10-private-network-basic, 11-private-network-basic-vnet, 15-private-network-standard-agent-setup, 19-private-network-agent-tools (Bicep); Terraform 15a, 15b and 19-private-network-agent-setup-with-tools. Managed virtual network: how-to/managed-virtual-network.",
                 kind="info", title="Templates", size=14,
                 src=[("Configure private link", learn("how-to/configure-private-link")), ("Networking options", learn("agents/concepts/networking-options"))])
    t_rbac = Table(
        [("Principal", 230), "Typical roles"],
        [
            [("Developer", "red"), "Foundry User (use); Foundry Project Manager (create connections / projects); Foundry Account Owner / Owner; AcrPush etc. for hosted deploys"],
            [("Project MI", "red"), "Storage Blob Data Contributor; Cosmos DB Operator + Built-in Data Contributor; Search Index Data Contributor + Search Service Contributor (Standard setup)"],
            [("Agent identity", "red"), "Explicit grants only (for example AcrPull; Search Index Data Reader for the Foundry IQ hosted quickstart)"],
            [("Search service MI", "red"), "Cognitive Services User (Foundry); Storage Blob Data Reader"],
            [("Toolbox consumers", "red"), "Foundry Agent Consumer"],
        ], w=C2, theme="red", size=14, head_size=15, title="RBAC cheat-sheet", title_size=22)
    n_ren = Note(C2, "Foundry User, Foundry Owner, Foundry Account Owner and Foundry Project Manager were previously named Azure AI User, Azure AI Owner, Azure AI Account Owner and Azure AI Project Manager. You may still see the old names while the rename rolls out; the role IDs and core permissions are unchanged.",
                 kind="info", title="Renamed roles", size=14, src=[("RBAC for Foundry", learn("concepts/rbac-foundry"))])
    h_left = t_tier.h + 22 + n_tpl.h
    h_right = t_rbac.h + 22 + n_ren.h
    H1 = max(h_left, h_right)
    t_tier.place(cv, 0, y)
    n_tpl.place(cv, 0, t_tier.bottom + 22, h=n_tpl.h + H1 - h_left)
    t_rbac.place(cv, C2 + GAP, y)
    n_ren.place(cv, C2 + GAP, t_rbac.bottom + 22, h=n_ren.h + H1 - h_right)

    y2 = y + H1 + 44
    tw = 2 * C3 + GAP
    t_tool = Table(
        [("Tool", 640), ("Support", 110), "Traffic flow"],
        [
            ["MCP (private), OpenAPI, A2A, Azure Functions", CHECK, "Through your VNet subnet"],
            ["Azure AI Search, File search", CHECK, "Private endpoint (file-search page: Azure Blob files unsupported in a BYO-VNet config)"],
            ["Code interpreter, Function calling", CHECK, "Microsoft backbone"],
            ["Web search, Grounding with Bing, SharePoint", CHECK, ("Public endpoint", "orange")],
            ["Foundry IQ (preview)", CHECK, "Via MCP"],
            ["Fabric IQ", PARTIAL, "By item: data agent tenant + workspace private link; ontology tenant private link; semantic model public only"],
            ["Fabric data agent tool, Logic Apps, Browser automation, Computer use, Image generation", CROSS, "Not supported"],
            ["Work IQ", CROSS, "Not supported (toolbox table); otherwise public HTTPS via the data proxy"],
        ], w=tw, theme="indigo", size=14, head_size=15, title="Tool traffic in a network-isolated project", title_size=22)
    n_cap = Note(C3, "Tool traffic that leaves Foundry through your VNet needs a PROJECT-level capability host (an account-level one alone fails with 'name or host unknown'). Public-endpoint tools can be blocked with Azure Policy. The table covers new Responses-API agents only (not classic-portal agents); workflow agents are inbound-only. Publishing to Teams from a private Foundry needs extra steps.",
                 kind="gotcha", title="Where the tool-traffic table applies", size=14,
                 src=[("Tool network isolation", learn("agents/how-to/tools/toolbox-network-isolation")), ("Publish to Teams from a VNet", learn("agents/how-to/publish-copilot-virtual-network"))])
    H2 = max(t_tool.h, n_cap.h)
    t_tool.place(cv, 0, y2)
    n_cap.place(cv, tw + GAP, y2, h=H2)
    return y2 + H2


# ---------------------------------------------------------------------------------------------- band 3: reference tables
def connection_types(cv, y):
    """Connection types a project can hold, as listed on the connections page."""
    PRE = ("Preview", "orange")
    cols = [("Connection type", 260), ("Preview?", 100), ("Creation", 190), "What the page says"]
    left = Table(cols, [
        [("Azure AI Search", "teal"), "", "-", "Required for Standard Agent deployment"],
        [("Azure Storage", "cyan"), "", "-", "Required for Standard Agent deployment"],
        [("Azure Cosmos DB", "cyan"), PRE, "Code only", "Required for Standard Agent deployment"],
        [("Azure OpenAI", "blue"), "", "-", "OpenAI models (including GPT-5, GPT-4o, GPT-image-1) and embeddings"],
        [("Application Insights", "violet"), "", "-", "Performance anomalies, diagnostics and application behaviour (traces)"],
        [("Azure Key Vault", "red"), "", "-", "Secrets; see the Key Vault limitations in the per-service reference"],
        [("Foundry", "blue"), "", "-", "Connect to other Foundry resources"],
        [("OpenAI", "blue"), "", "-", "Connect to your OpenAI models"],
        [("Serp", "gray"), "", "-", "Search Engine Results Pages for real-time data"],
        [("API key", "gray"), "", "-", "Authentication to a specified target, one at a time"],
        [("Custom key", "gray"), "", "-", "Keys plus related properties (targets, versions); you manage authentication"],
    ], w=C2, theme="gray", size=14, head_size=15, title="Connection types in a project (1 of 2)", title_size=22, pad_y=5)
    right = Table(cols, [
        [("Grounding with Bing Search", "cyan"), "", "-", "Real-time web grounding for queries"],
        [("Grounding with Bing Custom Search", "cyan"), PRE, "Code only", "A custom Bing search instance for tailored web grounding"],
        [("Serverless Model", "blue"), PRE, "Code only", "Serverless API deployment"],
        [("Azure Databricks", "cyan"), PRE, "Code only", "Jobs, Genie and Other; SDK-only, integrated as a FunctionTool; not in the Playground"],
        [("SharePoint", "teal"), PRE, "Code only", "Agents access and manage organisational documents"],
        [("Microsoft Fabric", "teal"), PRE, "Fabric data agent tool or ARM REST", "Provide the Fabric workspace and artifact IDs"],
        [("Azure APIM", "green"), PRE, "Code only", "Governance for AI models called in Agent Service"],
        [("Model Gateway", "green"), PRE, "Code only", "Governance for AI models called in Agent Service"],
        [("Copilot Studio Environment", "orange"), "", "Portal: Connected resources", "Bring Copilot Studio agents into the Foundry Control Plane to view"],
    ], w=C2, theme="gray", size=14, head_size=15, title="Connection types in a project (2 of 2)", title_size=22, pad_y=5)
    left.place(cv, 0, y)
    right.place(cv, C2 + GAP, y)
    yb = max(left.bottom, right.bottom)
    cite(cv, 0, yb + 6, [("Add a new connection to your project", learn("how-to/connections-add"))])
    n1 = Note(C2, "Connections let a project authenticate to Microsoft and other resources and are required for Standard Agent setups and agent knowledge tools. Certain connections can be created in the Foundry UI; others require code (Bicep). '-' means the page states no creation restriction. Cross-subscription connections used for model deployment (Foundry, Azure OpenAI) are not supported.",
              kind="info", title=f"Reading the tables ({ASOF})", size=14)
    n2 = Note(C2, "The Microsoft Fabric connection is created by adding the Fabric data agent tool. That tool (fabric_dataagent_preview) is scheduled for deprecation on 2026-11-06 - use the Fabric IQ tool instead.",
              kind="warn", title="Time-sensitive: Fabric data agent tool", size=14, src=[("Fabric tool", learn("agents/how-to/tools/fabric"))])
    hn = max(n1.h, n2.h)
    n1.place(cv, 0, yb + 44, h=hn)
    n2.place(cv, C2 + GAP, yb + 44, h=hn)
    return yb + 44 + hn


def reference(cv, y):
    y = band(cv, y, "3", "Service by service: how Foundry uses it, what needs it, BYO or not, and the connection pattern",
             sub=f"One row per service on the map ({ASOF}); the VNet row is the hub's network fabric; the Learn column links to the page the row summarises", theme="blue")
    y = connection_types(cv, y) + 50
    cv.text(0, y, "Per-service reference", size=26, color=INK)
    y += 44
    for d in DISTRICTS:
        rows = []
        for r in d["rows"]:
            tag = (r.get("byo") or ["-"])[0]
            cell_th = TAGS.get(tag) if tag in TAGS else None
            learn_cell = ({"text": r["learn"][0], "link": r["learn"][1], "color": "#1971c2"} if r.get("learn")
                          else "none documented")
            rows.append([
                (r["name"], d["theme"]) if False else r["name"],
                r["uses"], r["feat"],
                (r["byo_txt"], cell_th) if cell_th else r["byo_txt"],
                r["conn"], learn_cell,
            ])
        t = Table(
            [("Service", 270), ("How Foundry uses it", 700), ("Feature that needs it", 330), ("BYO?", 230), "Connection, auth and network", ("Learn", 330)],
            rows, w=W, theme=d["theme"], size=14, head_size=15, first_col_theme=d["theme"], pad_y=5,
            title=f"{d['num']}  {d['title']}", title_size=24)
        t.place(cv, 0, y)
        y = t.bottom + 36
    return y - 36


# ---------------------------------------------------------------------------------------------- band 4: flows
def flows(cv, y):
    y = band(cv, y, "4", "Typical flows across the services", sub="Provision a network-secured project, deploy a hosted agent, publish, observe, add a private MCP server", theme="green")
    specs = [
        ("A  Provision a Standard, network-secured project", "indigo", 820, [
            "Register the resource providers (check the list on the page you follow)",
            "Create the VNet with a delegated agent subnet and a private-endpoint subnet",
            "Create Cosmos DB, Storage and AI Search with private endpoints and DNS zones",
            "Create the Foundry account and project with capability settings",
            "Deploy models",
            "Connect Application Insights (optionally Key Vault, the APIM gateway, a registry)",
            "Assign roles: project MI on Cosmos DB, Storage and Search; developers Foundry User",
            "Verify each tool path: VNet, private endpoint, backbone or public",
        ]),
        ("B  Hosted-agent deploy", "green", 620, [
            "azd ai agent init (creates a project registry by default)",
            "Build the image: AcrPush (local) or Container Registry Tasks Contributor (remote)",
            "Foundry runs it on a Container Apps micro-VM in the delegated subnet",
            "The agent identity pulls the image (AcrPull)",
            "Traces go to Application Insights",
        ]),
        ("C  Publish to Teams or Microsoft 365", "orange", 570, [
            "Publish: an Azure Bot Service resource is created (Activity protocol)",
            "Choose BotServiceRbac (just you) or BotServiceTenant (org; M365 admin approval)",
            "Users chat in Teams or Copilot; a private Foundry needs REST enable_m365_public_endpoint and extra steps",
        ]),
        ("D  Observability", "violet", 560, [
            "Tracing is off by default: connect Application Insights",
            "OpenTelemetry traces land in Application Insights and Log Analytics",
            "Separately enable diagnostic settings to Log Analytics, Storage or Event Hubs (up to 2 h latency)",
        ]),
        ("E  Custom MCP server behind the firewall", "orange", 640, [
            "Build the server on Azure Functions (public) or Container Apps (internal ingress + dedicated MCP subnet, private)",
            "Optionally register it in API Center",
            "Add it as a custom MCP tool (key, project MI or OAuth passthrough)",
            "The agent calls it through the VNet subnet",
        ]),
    ]
    lr = metrics.line_ratio()

    def steps_h(w, items, size=16, detail_size=14):
        tw = (w - 42) * SAFETY
        total = 0.0
        for it in items:
            title, detail = (it, None) if isinstance(it, str) else it
            tl = metrics.wrap_text(title, tw, size)
            dl = metrics.wrap_text(detail, tw, detail_size) if detail else []
            total += max(len(tl) * size * lr + (len(dl) * detail_size * lr + 2 if dl else 0), 30) + 12
        return total - 12

    def panel_h(w, items):
        return 22 + (22 * lr + 6 + 8) + steps_h(w - 44, items) + 22

    # ---- flow A: horizontal chain of boxes
    title, th, _, items = specs[0]
    nb = len(items)
    bgap = 64
    bw = (W - 2 * 26 - (nb - 1) * bgap) / nb
    labels = [
        ("Register providers", "check the list on the page you follow", "subscription"),
        ("VNet + subnets", "delegated agent subnet and a private-endpoint subnet", "vnet"),
        ("Data resources", "Cosmos DB, Storage and AI Search with private endpoints and DNS zones", "private-endpoint"),
        ("Foundry account + project", "with capability settings", "foundry"),
        ("Deploy models", "agent-compatible chat and embedding models", "openai"),
        ("Connections", "Application Insights; optionally Key Vault, the APIM gateway, a registry", "api-connections"),
        ("Roles", "project MI on Cosmos DB, Storage and Search; developers Foundry User", "managed-identity"),
        ("Verify tool paths", "VNet, private endpoint, backbone or public", "alerts"),
    ]
    with cv.panel(0, y, title=title, theme=th, style="dotted", fill="none", pad=26, title_size=24, w=W) as pa:
        boxes = [Box(bw, lab, sub=sub, theme=th, icon=ic, fill="solid", min_h=190, size=17, sub_size=14) for lab, sub, ic in labels]
        hh = max(b.h for b in boxes)
        for i, b in enumerate(boxes):
            b.place(cv, pa.ix + i * (bw + bgap), pa.iy, h=hh)
            numbered(cv, b.x + 18, b.y + 18, i + 1, theme=th, d=30)
        for a, b in zip(boxes, boxes[1:]):
            connect(cv, a, b, a_side="right", b_side="left")
    y2 = pa.bottom + 40

    # ---- flows B-E: four columns, each panel may carry a closing note
    cw4 = C4
    rest = specs[1:]
    extras = {
        "C": ("warn", "Portal publish is unsupported for public-access-disabled projects, and the SharePoint tool does not work when the agent is published to Teams."),
        "D": ("info", "Viewers need Log Analytics Reader / Monitoring Reader (plus Privileged Monitoring Data Reader for protected tables); private setups use an Application Insights Private Link scope."),
        "E": ("info", "Functions MCP endpoint: https://{app}.azurewebsites.net/runtime/webhooks/mcp. Auth: function key (x-functions-key), Entra (project MI), OAuth passthrough, or unauthenticated (not recommended)."),
    }

    def extra_note(title):
        kind_text = extras.get(title[0])
        return Note(cw4 - 44, kind_text[1], kind=kind_text[0], size=13) if kind_text else None

    hh = max(panel_h(cw4, s[3]) + ((extra_note(s[0]).h + 16) if extra_note(s[0]) else 0) for s in rest)
    bottom = y2
    for k, (title, th, _, items) in enumerate(rest):
        with cv.panel(k * (cw4 + GAP), y2, title=title, theme=th, style="dotted", fill="none", pad=22, title_size=22, w=cw4, min_h=hh) as p:
            sb = steps(cv, p.ix, p.iy, cw4 - 44, items, theme=th)
            en = extra_note(title)
            if en:
                en.place(cv, p.ix, sb + 16)
        bottom = max(bottom, p.bottom)
    return bottom


# ---------------------------------------------------------------------------------------------- band 5: gotchas
def gotchas(cv, y):
    y = band(cv, y, "5", "Gotchas and where the docs disagree", sub=f"Cautious reading of the documentation ({ASOF})", theme="red")
    notes = [
        Note(C3, "Several tools use public endpoints even in private projects: Web search, Grounding with Bing, SharePoint and Work IQ. Public-endpoint tools can be blocked with Azure Policy.",
             kind="gotcha", title="Public even when private", size=14, src=[("Tool network isolation", learn("agents/how-to/tools/toolbox-network-isolation"))]),
        Note(C3, "Private endpoints to Search, Storage and Cosmos DB are not created by the portal flow. Resource providers named on network and tutorial pages differ (KeyVault, CognitiveServices, Storage, MachineLearningServices, Search, App, ContainerService, Bing, BotService, DocumentDB) - verify per page.",
             kind="warn", title="Create endpoints yourself", size=14, src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))]),
        Note(C3, "BYO Key Vault: one per Foundry resource; deleting it breaks the resource; create the Key Vault connection first in IaC. Customer-managed keys need a same-region vault with soft delete and purge protection.",
             kind="warn", title="Key Vault rules", size=14, src=[("Customer-managed keys", learn("concepts/customer-managed-keys"))]),
        Note(C3, "Purview and Defender are toggles and policies in the Compliance workspace; Purview lacks network isolation support. Evaluations in GitHub Actions and Azure DevOps are preview - keep evaluation runs off every commit (cost tip).",
             kind="info", title="Compliance and CI", size=14, src=[("Compliance and security", learn("control-plane/how-to-manage-compliance-security"))]),
        Note(C3, "Foundry has no automatic cross-region failover; customer-owned resources (Cosmos DB, Storage, AI Search) need their own DR. For multi-region availability deploy separate Foundry resources and route in your application layer.",
             kind="gotcha", title="DR is yours", size=14, src=[("High availability", learn("how-to/high-availability-resiliency"))]),
        Note(C3, "The Fabric data agent tool (fabric_dataagent_preview) is scheduled for deprecation on 2026-11-06 - use the Fabric IQ tool. Private Container Registry is supported for projects created after 2026-06-25.",
             kind="warn", title=f"Time-sensitive ({ASOF})", size=14, src=[("Fabric tool", learn("agents/how-to/tools/fabric"))]),
        Note(C3, "The file-search page says Azure Blob files are unsupported in a BYO-VNet configuration, while the network tables list File search as supported through a private endpoint.",
             kind="warn", title="Docs disagree: file search in private networks", size=14),
        Note(C3, "Foundry IQ is called GA in a Build 2026 blog, '(preview)' in the Foundry network table and GA or preview by API version in the AI Search docs. Work IQ is GA in a partner blog and video Q&A but preview in the Foundry Work IQ tool page.",
             kind="warn", title="Docs disagree: Foundry IQ and Work IQ status", size=14),
        Note(C3, "The standard-agent-setup page lists an Azure Key Vault among its prerequisites (for secrets and connection strings), while the connections page says Foundry uses a managed Key Vault unless you add a Key Vault connection. Check the path you follow.",
             kind="warn", title="Docs disagree: Key Vault in the Standard setup", size=14,
             src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup")), ("Add connections", learn("how-to/connections-add"))]),
    ]
    bottom = y
    for r in range(3):
        chunk = notes[r * 3:(r + 1) * 3]
        hh = max(n.h for n in chunk)
        for i, n in enumerate(chunk):
            n.place(cv, i * (C3 + GAP), bottom, h=hh)
        bottom += hh + 24
    return bottom - 24


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Azure and Microsoft services around Foundry",
                                f"A hub-and-spoke map: the role each service plays, which feature needs it, BYO or managed, and the auth and network pattern ({ASOF})",
                                icon="foundry", w=W)
    y = top_legend(cv, bottom + 26) + 36
    y = band_summary(cv, y) + 60
    y = hub_map(cv, y) + 60
    y = patterns(cv, y) + 60
    y = reference(cv, y) + 60
    y = flows(cv, y) + 60
    y = gotchas(cv, y) + 60
    sources(cv, 0, y, [
        ("Microsoft Foundry architecture", learn("concepts/architecture")),
        ("Add a new connection to your project", learn("how-to/connections-add")),
        ("Set up standard agent resources", learn("agents/concepts/standard-agent-setup")),
        ("Use your own resources with Agent Service", learn("agents/how-to/use-your-own-resources")),
        ("Bring your own Azure Storage", learn("how-to/bring-your-own-azure-storage-foundry")),
        ("Configure network isolation (private link)", learn("how-to/configure-private-link")),
        ("Tool network isolation (toolbox)", learn("agents/how-to/tools/toolbox-network-isolation")),
        ("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
        ("Agent identity", learn("agents/concepts/agent-identity")),
        ("Hosted agents", learn("agents/concepts/hosted-agents")),
        ("AI gateway (API Management)", learn("agents/how-to/ai-gateway")),
        ("Publish agents to Microsoft 365 Copilot and Teams", learn("agents/how-to/publish-copilot")),
        ("Connectors and managed MCP servers", learn("agents/how-to/tools/connectors")),
        ("Build your own MCP server", learn("mcp/build-your-own-mcp-server")),
        ("Compliance and security (Defender, Purview)", learn("control-plane/how-to-manage-compliance-security")),
    ], w=W, cols=3)
