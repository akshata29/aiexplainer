"""Foundry resource model and service architecture - EXEMPLAR diagram (copy its structure for new canvases)."""
from generator.xd import *

META = dict(
    id="resource-model", title="Foundry resource model", section="1", order=4, group="Overview",
    description="Foundry resource -> projects -> deployments, connections and connected Azure services; control vs data plane; storage, networking, encryption and data residency.",
    tags=["architecture", "resource", "project", "rbac", "networking"],
)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Microsoft Foundry", "Resource model and architecture - one governed resource, many isolated projects",
                                w=2640)
    top = bottom + 56

    # ------------------------------------------------------------------ main structure (left)
    with cv.panel(0, top, title="Azure subscription / resource group", theme="gray", style="dotted", pad=30,
                  title_size=22) as rg:
        with cv.panel(rg.ix, rg.iy, title="Foundry resource",
                      sub="Microsoft.CognitiveServices/accounts   |   kind: AIServices   |   the governance boundary",
                      theme="blue", style="solid", fill="soft", pad=26, title_size=30, sub_size=16) as fr:
            cw = 372
            deployments = Card(cw, "Model deployments", [
                "Created once at the resource and reused by every project",
                "Deployment type sets where prompts are processed: global, data zone or regional",
                "Billing: standard (per token), provisioned (hourly reserved) or batch",
            ], theme="blue", icon="openai", src=[("Deployment types", learn("foundry-models/concepts/deployment-types"))])
            connections = Card(cw, "Connections", [
                "Point at Azure services you keep separately: Storage, Key Vault, AI Search",
                "Key-based connection secrets sit in a managed Key Vault by default",
                "Bring your own Key Vault: one connection manages all project and resource secrets",
            ], theme="cyan", icon="api-connections", src=[("Key Vault connection", learn("how-to/set-up-key-vault-connection"))])
            security = Card(cw, "Security and networking", [
                "Azure RBAC at resource and project scope; managed identities at either scope",
                "Network isolation: private endpoints, BYO VNet or managed VNet",
                "Customer-managed keys for encryption at rest",
                "Azure Policy aliases shared with other Microsoft.CognitiveServices kinds",
            ], theme="red", icon="key-vault", src=[("Architecture", learn("concepts/architecture"))])
            guard = Card(cw, "Guardrails and monitoring", [
                "Guardrails = risks + intervention points + actions; filters run inline, set per deployment",
                "Azure Monitor metrics at resource scope: tokens, latency, requests, errors",
                "Diagnostic settings to Log Analytics, Storage or Event Hubs",
            ], theme="pink", icon="content-safety", src=[("Guardrails overview", learn("guardrails/guardrails-overview"))])
            r1_right, r1_bottom = row(cv, fr.ix, fr.iy + 4, [deployments, connections, security, guard], gap=22)

            # projects ----------------------------------------------------------
            py = r1_bottom + 44
            projects = []
            px = fr.ix
            for name, sub in (("Project A", "development boundary for one team or use case"),
                              ("Project B", "same shape: its own agents, evaluations and files")):
                with cv.panel(px, py, title=name, sub=sub, theme="green", style="dashed", fill="soft", pad=22,
                              title_size=26, sub_size=15) as pr:
                    c_agents = Card(350, "Agents", [
                        "Prompt agents and hosted agents",
                        "Built against the project endpoint (azure-ai-projects SDK + OpenAI client)",
                    ], theme="green", icon="agent", src=[("Agent Service", learn("agents/overview"))])
                    c_eval = Card(350, "Evaluations and traces", [
                        "Evaluation runs and results stay in the project scope",
                        "Project metrics: evaluation outcomes, agent invocations, file operations",
                    ], theme="violet", icon="app-insights", src=[("Observability", learn("concepts/observability"))])
                    c_files = Card(350, "Files and data", [
                        "Uploaded files, datasets, vector stores",
                        "Basic setup: Microsoft-managed storage. Standard setup: your accounts, isolated by project",
                    ], theme="cyan", icon="storage", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
                    c_id = Card(350, "Project identity", [
                        "Project managed identity reaches connected resources",
                        "Starter RBAC: Foundry User for the project identity at resource scope",
                    ], theme="pink", icon="managed-identity", src=[("RBAC for Foundry", learn("concepts/rbac-foundry"))])
                    row(cv, pr.ix, pr.iy, [c_agents, c_eval], gap=18)
                    row(cv, pr.ix, pr.iy + max(c_agents.h, c_eval.h) + 18, [c_files, c_id], gap=18)
                projects.append(pr)
                px = pr.right + 28
    # ------------------------------------------------------------------ connected resources (right)
    cx = rg.right + 170
    with cv.panel(cx, top, title="Connected Azure resources", sub="independent governance boundaries - you secure each one",
                  theme="gray", style="dotted", pad=24, title_size=24, sub_size=15) as cr:
        cards = [
            Card(430, "Azure Storage", ["Files for OpenAI models and agents, evaluation + batch inputs/outputs",
                                        "Default: Microsoft-managed accounts; or connect your own"], theme="cyan",
                 icon="storage", src=[("Bring your own storage", learn("how-to/bring-your-own-azure-storage-foundry"))]),
            Card(430, "Azure Key Vault", ["Connection secrets (BYO option)", "Customer-managed keys: same region, soft delete + purge protection on, Key Vault Crypto User role"],
                 theme="red", icon="key-vault", src=[("Customer-managed keys", learn("concepts/customer-managed-keys"))]),
            Card(430, "Azure AI Search", ["Provider Microsoft.Search", "Knowledge retrieval over your data; vector stores for agents in the standard setup"],
                 theme="teal", icon="ai-search", src=[("Foundry IQ", learn("agents/concepts/what-is-foundry-iq"))]),
            Card(430, "Azure Cosmos DB", ["Standard agent setup: conversations / threads stored in your account, isolated by project"],
                 theme="green", icon="cosmos", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))]),
            Card(430, "Log Analytics / Event Hubs", ["Diagnostic logs and metrics destinations", "Application Insights for traces"],
                 theme="violet", icon="log-analytics", src=[("Diagnostic logging", learn("how-to/diagnostic-logging"))]),
        ]
        col(cv, cr.ix, cr.iy, cards, gap=20)
    arrow(cv, [(rg.right + 6, top + 300), (cr.x - 6, top + 300)], dash="dashed", color="#1971c2", sw=3, start_head="arrow",
          end_head="arrow", label="referenced through connections", label_size=15, label_wrap=150)

    # ------------------------------------------------------------------ lower band
    y2 = max(rg.bottom, cr.bottom) + 60
    section_header(cv, 0, y2, "Who can do what, where is the data, how is it isolated", size=32)
    y3 = y2 + 70

    t_types = Table(
        [("Resource type", 190), ("Provider / type", 340), ("Kind", 100), ("Capabilities", 370)],
        [
            [("Microsoft Foundry", "blue"), "Microsoft.CognitiveServices/accounts", "AIServices",
             "Agents, evaluations, Azure OpenAI, Speech, Vision, Language, Content Understanding"],
            [("Foundry project", "blue"), "Microsoft.CognitiveServices/accounts/projects", "AIServices", "Subresource of the Foundry resource"],
            ["Azure Speech in Foundry Tools", "Microsoft.CognitiveServices/accounts", "Speech", "Speech"],
            ["Azure Language in Foundry Tools", "Microsoft.CognitiveServices/accounts", "Language", "Language"],
            ["Azure Vision in Foundry Tools", "Microsoft.CognitiveServices/accounts", "Vision", "Vision"],
            ["Azure AI Search", "Microsoft.Search", "-", "Knowledge retrieval over your data"],
        ], w=1000, theme="blue", size=14, head_size=15, title="Resource types and providers",
        title_size=22)
    t_types.place(cv, 0, y3)

    rbac = Card(500, "Control plane vs data plane", [
        "# Control plane (ARM)",
        "Create deployments and projects, configure security, networking and connections",
        "# Data plane",
        "Build agents, run evaluations, upload files",
        "# Starter least-privilege assignments",
        "Foundry User for each developer at resource scope",
        "Foundry User for each project managed identity at resource scope",
        "! Roles were renamed: Foundry User/Owner/Account Owner/Project Manager were Azure AI User/Owner/Account Owner/Project Manager - IDs and permissions unchanged",
    ], theme="red", icon="managed-identity", src=[("RBAC for Foundry", learn("concepts/rbac-foundry"))])
    rbac.place(cv, t_types.right + 40, y3)

    state = Card(520, "Agent state and file storage", [
        "# Basic agent setup",
        "Threads, messages and files in Microsoft-managed multitenant storage with logical separation",
        "# Standard agent setup",
        "You bring Azure resources for all customer data: files, conversations, vector stores",
        "Data is isolated by project inside your storage accounts",
    ], theme="cyan", icon="storage", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
    state.place(cv, rbac.right + 40, y3)

    net = Card(560, "Compute, isolation and networking", [
        "Agents, evaluations and batch run on Microsoft-managed compute",
        "Workloads are isolated per Foundry resource; customer code does not share runtime containers with other tenants",
        "# Outbound isolation",
        "Customer-managed VNet (BYO): subnet delegated to Microsoft.App/environments; platform injects into it",
        "Managed VNet: Foundry manages the network for you",
        "! Some network-isolated scenarios need SDK or CLI, not the portal",
    ], theme="indigo", icon="vnet", src=[("Architecture", learn("concepts/architecture")), ("Networking options", learn("agents/concepts/networking-options"))])
    net.place(cv, state.right + 40, y3)

    y4 = max(t_types.bottom, rbac.bottom, state.bottom, net.bottom) + 40
    t_dep = Table(
        ["Deployment type", "Data processing", "Billing"],
        [
            ["Global Standard", "Cross-region, Azure-managed", "Pay-per-token"],
            ["Global Provisioned", "Cross-region, Azure-managed", "Hourly reserved capacity"],
            ["Global Batch", "Cross-region, Azure-managed", "Batch token pricing"],
            ["Data Zone Standard", "Within data-zone boundary", "Pay-per-token"],
            ["Data Zone Provisioned", "Within data-zone boundary", "Hourly reserved capacity"],
            ["Data Zone Batch", "Within data-zone boundary", "Batch token pricing"],
            ["Standard", "Single region", "Pay-per-token"],
            ["Regional Provisioned", "Single region", "Hourly reserved capacity"],
            [("Developer", "yellow"), "Any Azure region, no residency guarantee", "Pay-per-token; fine-tuned model evaluation only, 24 h lifetime, no SLA"],
        ], w=1000, theme="blue", size=14, head_size=15, title="Model deployment types by data-processing scope", title_size=22,
        first_col_theme="blue")
    t_dep.place(cv, 0, y4)

    enc = Card(500, "Encryption, secrets and data residency", [
        "Default: Microsoft-managed keys, FIPS 140-2 compliant 256-bit AES at rest, TLS in transit",
        "Customer-managed keys need: Key Vault in the same region, soft delete + purge protection, Key Vault Crypto User for the managed identities",
        "Data at rest stays in the designated Azure geography",
        "Prompts and completions follow the deployment type: global may route to any region, data zone stays in the US or EU zone, standard/regional stay in the deployment region",
    ], theme="red", icon="key-vault", src=[("Customer-managed keys", learn("concepts/customer-managed-keys")), ("Data privacy", learn("responsible-ai/openai/data-privacy"))])
    enc.place(cv, t_dep.right + 40, y4)

    n1 = Note(560, "No automatic cross-region failover. For multi-region availability deploy separate Foundry resources per region and handle data synchronization and routing in your application layer.",
              kind="gotcha", title="Resilience", src=[("High availability", learn("how-to/high-availability-resiliency"))])
    n1.place(cv, enc.right + 40, y4)
    n2 = Note(560, "Most new APIs are available at the project scope. Some capabilities that came from Azure OpenAI, Speech, Vision and Language (for example the Translator API) exist only at the Foundry resource level - plan your structure around the API scopes you need.",
              kind="info", title="Scope matters")
    n2.place(cv, enc.right + 40, n1.bottom + 22)
    n3 = Note(560, "Single developer exploring? One Foundry resource with one project is the recommended default. Only need completions with no agents or evaluations? A standalone Azure OpenAI resource can be enough. Hub-based projects stay in the Foundry (classic) portal; new investment targets Foundry projects.",
              kind="tip", title="Rule of thumb")
    n3.place(cv, enc.right + 40, n2.bottom + 22)

    y5 = max(t_dep.bottom, enc.bottom, n3.bottom) + 60
    sources(cv, 0, y5, [
        ("Microsoft Foundry architecture", learn("concepts/architecture")),
        ("Role-based access control for Microsoft Foundry", learn("concepts/rbac-foundry")),
        ("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
        ("Use your own resources with Agent Service", learn("agents/how-to/use-your-own-resources")),
        ("Configure network isolation (private link)", learn("how-to/configure-private-link")),
        ("Customer-managed keys for Foundry", learn("concepts/customer-managed-keys")),
        ("High availability and resiliency", learn("how-to/high-availability-resiliency")),
        ("Plan your Foundry rollout", learn("concepts/planning")),
    ], w=2640, cols=3)
