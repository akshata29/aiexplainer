"""Governance, policy and compliance (part 2 of 2) - the evidence plane, residency and Azure Government.

Part 1 covers the control stack. This part covers how you prove it: diagnostic logging, Defender, Purview, Entra and Agent 365,
Service Health and the consolidated view, data residency by deployment type, Azure Government availability and the choice
between co-located and isolated Foundry resources.
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="governance-policy-compliance-part-2", title="Governance, policy and compliance, part 2", section="2",
    group="Control plane and cost", order=52.5,
    description="The evidence plane for Foundry governance - diagnostic logging, Defender, Purview, Entra and Agent 365, Service Health and the consolidated view - plus data residency by deployment type, Azure Government availability and co-located versus isolated boundaries.",
    tags=["governance", "compliance", "diagnostic-logging", "defender", "purview", "data-residency"],
)

CW, GUT = 520, 48
STEP = CW + GUT
W = 6 * CW + 5 * GUT          # 3360


def X(i: int) -> float:
    return i * STEP


def SPAN(n: int) -> float:
    return n * CW + (n - 1) * GUT


S = dict(
    diag=("Diagnostic logging", learn("how-to/diagnostic-logging")),
    consol=("Consolidated view for Foundry Tools", learn("concepts/foundry-consolidated-view")),
    health=("Stay informed with Service Health", learn("how-to/stay-informed-service-health")),
    gov=("Foundry in Azure Government", learn("concepts/foundry-azure-government")),
    plan=("Plan your Foundry rollout", learn("concepts/planning")),
    arch=("Foundry architecture", learn("concepts/architecture")),
    dtypes=("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
    privacy=("Data, privacy and security", learn("responsible-ai/openai/data-privacy")),
    compliance=("Manage compliance and security", learn("control-plane/how-to-manage-compliance-security")),
    defender=("Enable threat protection for AI services", learn("azure/defender-for-cloud/ai-onboarding", base="")),
    baseline=("Azure security baseline for Foundry", learn("security/benchmark/azure/baselines/azure-ai-foundry-security-baseline", base="")),
    a365=("Agent 365 integration with Foundry", learn("agents/concepts/agent-365-integration")),
    a365cfg=("Configure Agent 365 data collection", learn("agents/how-to/configure-agent-365-data-collection")),
    a365ov=("Overview of Microsoft Agent 365", learn("microsoft-agent-365/overview", base="")),
    govern=("Govern agent infrastructure (Entra admin)", learn("control-plane/govern-agent-infrastructure-entra-admin")),
    agentid=("Agent identity", learn("agents/concepts/agent-identity")),
    faq=("Agent Service FAQ", learn("agents/faq")),
    std=("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
    mvnet=("Managed virtual network", learn("how-to/managed-virtual-network")),
    ha=("High availability and resiliency", learn("how-to/high-availability-resiliency")),
    ft=("Fine-tuning cost management", learn("fine-tuning/cost-management")),
    guardrails=("Guardrails overview", learn("guardrails/guardrails-overview")),
    rbac=("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
    trust=("Azure compliance documentation (Service Trust Portal)", "https://aka.ms/AzureCompliance"),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


_KitNote = Note


def Note(*a, **kw):  # noqa: N802 - the kit leaves no bottom padding under citation lines; add it here
    n = _KitNote(*a, **kw)
    if kw.get("src"):
        n.h += 10
    return n


def chain(cv: Canvas, x: float, y: float, w: float, steps, *, theme="grape", dash="solid", gap=56, size=20, sub_size=15):
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


def mark(cv: Canvas, kind: str, cx: float, cy: float, size: float = 18) -> None:
    """Vector tick, cross or dash (Excalifont has no check glyphs); same look as the kit's table marks."""
    s = size / 2
    if kind == "v":
        cv.poly([(cx - s * 0.7, cy + s * 0.05), (cx - s * 0.2, cy + s * 0.6), (cx + s * 0.8, cy - s * 0.7)], stroke="#2f9e44", sw=3, rough=1)
    elif kind == "x":
        cv.line((cx - s * 0.6, cy - s * 0.6), (cx + s * 0.6, cy + s * 0.6), stroke="#e03131", sw=3)
        cv.line((cx - s * 0.6, cy + s * 0.6), (cx + s * 0.6, cy - s * 0.6), stroke="#e03131", sw=3)
    else:
        cv.line((cx - s * 0.5, cy), (cx + s * 0.5, cy), stroke="#868e96", sw=3)


# ============================================================================================== 0. title, key, summary
def title_and_key(cv: Canvas) -> float:
    _, bottom = title_block(
        cv, 0, 0, "Governance, policy and compliance, part 2",
        "Part 2 of 2 - the evidence plane: logging, Defender, Purview and Entra, Service Health, data residency, Azure Government and governance boundaries  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    with cv.panel(0, y, theme="gray", style="dotted", pad=16, w=W) as k:
        cv.text(k.ix, k.iy - 2, "Colour = area", size=16, color="#343a40")
        legend(cv, k.ix + 150, k.iy - 2, [
            ("Models and deployments", "blue"), ("Agents and projects", "green"), ("Observability", "violet"),
            ("Guardrails", "pink"), ("Identity, security, RBAC", "red"), ("Networking", "indigo"),
            ("Governance and policy", "grape"), ("Cost and quota", "yellow"), ("Data", "cyan"), ("Neutral", "gray")],
            size=15, gap=22)
        y2 = k.iy + 34
        cv.text(k.ix, y2, "Markers", size=16, color="#343a40")
        cx = k.ix + 150
        draw_badge(cv, cx, y2 - 1, "ga")
        draw_badge(cv, cx + 50, y2 - 1, "preview")
        t = cv.text(cx + 140, y2, "status as of 2026-11-03", size=15)
        cx += 140 + t.w + 32
        cv.rect(cx, y2 + 1, 28, 18, stroke="#495057", sw=2, dash="dashed")
        t = cv.text(cx + 38, y2, "our ordering of documented guidance, or not stated in the docs", size=15)
        cx += 38 + t.w + 32
        for kind, label in (("v", "available"), ("x", "not available"), ("-", "not stated in the docs")):
            mark(cv, kind, cx + 10, y2 + 10)
            t = cv.text(cx + 28, y2, label, size=15)
            cx += 28 + t.w + 28
    return k.bottom


def summary_strip(cv: Canvas, y: float) -> float:
    def tile(title, body, theme, icon, keys):
        return Card(CW, title, ["= " + body], theme=theme, icon=icon, fill="hatch", title_size=22, body_size=15, pad=14,
                    gap=4, icon_size=34, src=src(*keys))

    tiles = [
        tile("Logs lag up to 2 hours", "Diagnostic settings send audit, request and response logs and metrics to Log Analytics or Storage.",
             "violet", "diagnostics", ("diag",)),
        tile("Defender and Purview are paid", "Defender adds posture and prompt-attack alerts; Purview adds audit, SIT classification and DSPM for AI, and needs a tenant licence.",
             "red", "defender", ("defender", "compliance")),
        tile("Entra owns agent availability", "Admins block, unblock or delete agents; Agent 365 residency follows the Entra tenant, not the Azure region.",
             "red", "conditional-access", ("govern", "a365")),
        tile("Residency follows the deployment type", "Global may process anywhere, Data Zone stays in its zone, Standard and Regional stay in the geography; data at rest stays put.",
             "blue", "regions", ("dtypes", "privacy")),
        tile("Azure Government differs", "No model router, evaluations or optimization; Control Plane and AI gateway availability is not stated.",
             "gray", "globe", ("gov",)),
        tile("Co-locate or isolate", "Production defaults to isolation, exploration to colocation. Quota, blast radius and cost boundaries follow the choice.",
             "green", "resource-group", ("plan",)),
    ]
    _, bottom = row(cv, 0, y, tiles, gap=GUT)
    return bottom


# ============================================================================================== 1. diagnostic logging
def logging_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "1  Diagnostic logging: from the Foundry resource to your workspace", size=34,
                   sub="Azure Monitor resource logs are the audit trail for model traffic. Enforce them at scale with the logging policy group from part 1.")
    y += 100
    cats = ChipFlow([Chip(t, theme="violet", size=16) for t in ("Audit Logs", "Request and Response Logs", "Azure OpenAI Request Usage", "AllMetrics")],
                    660, gap=10)
    with cv.panel(610, y, title="Diagnostic setting", sub="Foundry resource > Monitoring > Diagnostic settings > + Add", theme="violet", style="dashed",
                  fill="soft", pad=20, title_size=24, sub_size=15, w=720) as ds:
        cv.text(ds.ix, ds.iy, "Tick these categories", size=16, color="#5f3dc4")
        cats.place(cv, ds.ix, ds.iy + 26)
        cv.text(ds.ix, ds.iy + 36 + cats.h + 8, "Role: Monitoring Contributor", size=15, color="#495057")
    fr = Box(480, "Foundry resource", sub="Microsoft.CognitiveServices/accounts", theme="blue", icon="foundry", fill="hatch", size=22,
             sub_size=15, min_h=190)
    fr.place(cv, 0, ds.y + (ds.h - fr.h) / 2)
    la = Card(900, "Log Analytics workspace", [
        "Table AzureDiagnostics",
        "Filter: ResourceProvider == \"MICROSOFT.COGNITIVESERVICES\" and Category == \"RequestResponse\"",
        "Sample KQL: latency percentiles (P50, P90, P95, P99) by response code; counts by code; AzureMetrics",
    ], theme="violet", icon="log-analytics", fill="hatch", title_size=21, body_size=16, src=src("diag"))
    st = Card(900, "Storage account", ["Blobs under insights-logs-<category>/.../PT1H.json"], theme="cyan", icon="storage",
              fill="hatch", title_size=21, body_size=16, src=src("diag"))
    eh = Card(900, "Event Hubs", ["The logging policy group includes a definition that routes category-group logs to an Event Hub"],
              theme="indigo", icon="event-hubs", fill="hatch", dash="dashed", title_size=21, body_size=16, src=src("diag"))
    dx = 1460
    _, dend = col(cv, dx, y, [la, st, eh], gap=22)
    connect(cv, fr, ds, a_side="right", b_side="left", end_head="arrow", sw=2, label="emits", label_size=15)
    for c in (la, st, eh):
        connect(cv, ds, c, a_side="right", b_side="left", end_head="arrow", sw=2, route="elbow")
    nx = dx + 900 + 70
    n1 = Note(W - nx, "When models sit behind the AI gateway, request logs also land in API Management (ApiManagementGatewayLogs). They are separate from these resource logs.",
              kind="info", title="Gateway logs are separate", src=src("diag"))
    n2 = Note(W - nx, "Agent traces travel as OpenTelemetry to Application Insights. The Traces UI keeps about 90 days; retention follows the App Insights configuration.",
              kind="info", title="Agent telemetry is another channel", src=src("diag"))
    n3 = Note(W - nx, "Diagnostic data can take up to 2 hours to show up in the destination.", kind="warn", title="Up to 2 hours of lag")
    col(cv, nx, y, [n1, n2, n3], gap=20)
    yb = max(dend, ds.bottom, n3.bottom) + 50
    with cv.panel(0, yb, title="Logging at scale", sub="documented pieces in our order: policy deploys the setting, policy proves coverage, you query", theme="violet",
                  style="dashed", pad=22, title_size=26, sub_size=15, w=W) as pr:
        chain(cv, pr.ix, pr.iy, W - 44, [
            ("Assign the DeployIfNotExists policy", "Enable logging by category group for Cognitive Services to Log Analytics"),
            ("A remediation task creates the settings", "existing Foundry resources get a diagnostic setting"),
            ("Assign the audit policy", "Diagnostic logs in Azure AI services resources should be enabled: proves coverage"),
            ("Query AzureDiagnostics", "lag of up to 2 hours before new data appears"),
        ], theme="violet", dash="dashed", gap=70)
    return pr.bottom


# ============================================================================================== 2. defender, purview, entra
def partners_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2  Defender, Purview and Entra: what each contributes to compliance", size=34,
                   sub="Foundry guardrails work at the model layer; these services add posture, data security and identity governance around them")
    y += 100
    cw = (W - 3 * GUT) / 4

    def pc(title, body, theme, icon, keys, badge=None):
        return Card(cw, title, body, theme=theme, icon=icon, badge=badge, fill="hatch", title_size=22, body_size=16, pad=16, gap=5,
                    icon_size=36, src=src(*keys))

    cards = [
        pc("Defender for Cloud", [
            "Security posture tab: recommendations with resource, risk level and a link to remediation",
            "Threat-protection alerts for jailbreak and user-prompt attacks, shown as security alerts",
            "Enable Defender on the subscription plus threat protection for Foundry Tools (the AI services plan); covers workloads on managed inference endpoints",
            "! Defender for AI Services is a paid plan",
        ], "red", "defender", ("compliance", "defender")),
        pc("Microsoft Purview", [
            "Audit, sensitive information type (SIT) classification, DSPM for AI, Insider Risk Management, Communication Compliance, Data Lifecycle Management, eDiscovery",
            "Switch on per subscription: Operate > Compliance > Data security and governance > Powered by Microsoft Purview (Foundry Account Owner)",
            "Data Security Policies need Entra user-context tokens (AzureUserSecurityContext on /chat/completions); other auth shows only in Audit and the DSPM activity explorer",
            "! Paid Purview feature, not included in the Defender plan; not yet compatible with network isolation",
        ], "red", "info-protection", ("compliance", "defender")),
        pc("Microsoft Entra", [
            "Agent identities appear in the tenant inventory; the Entra ID column in Foundry shows application and object ID",
            "Conditional Access, Identity Protection, network access, governance with expiry, owners and sponsors",
            "Sign-in logs filter by agent type (blueprint, agent identity, agent user); audit logs carry agentType and blueprintId",
            "Block, Unblock, Delete, Restore and Permanently delete take up to 10 min to reach Foundry",
        ], "red", "conditional-access", ("govern", "agentid")),
        pc("Agent 365", [
            "Microsoft's enterprise control plane for AI agents: Registry, Access control, Visualization, Interoperability, Security",
            "Every published Foundry agent syncs to the registry",
            "Data flows only if licence, tenant consent and the a365LoggingEnabled flag on the Foundry resource are all true (flag defaults to true once Agent 365 is enabled; no per-project or per-agent override)",
            "GA for Commercial since 2026-05-01, per-user licensing",
        ], "grape", "m365", ("a365", "a365cfg", "a365ov")),
    ]
    _, y1 = row(cv, 0, y, cards, gap=GUT)
    y2 = y1 + 40
    n1 = Note(SPAN(2), "Foundry guardrails (content filters, prompt shields, abuse detection at the model layer) plus Defender (posture and threat protection) plus Purview "
              "(audit, SIT, DSPM for AI).", kind="key", title="Defence in depth", src=src("compliance"))
    n2 = Note(SPAN(2), "The compliance page says AI interaction data flows from all applications and agents in the subscription; the Defender onboarding page says the Purview "
              "integration does not include data or context from Foundry agents. The compliance page's tab table omits the Data security and governance tab it later "
              "tells you to use. The Defender enable role differs (Security Admin or Owner versus Owner or Contributor), and one page prints Azure AI Account Owner for the Purview role.",
              kind="warn", title="Docs disagree: Purview and Defender", src=src("compliance", "defender"))
    n3 = Note(SPAN(2), "The Foundry page asks for at least one Microsoft 365 Copilot licence plus Frontier program enrollment and Global Administrator enablement. The Agent 365 overview says "
              "general availability for Commercial since 2026-05-01, per-user licensing, and works best with Microsoft E5. Check both pages for your tenant.",
              kind="warn", title="Docs disagree: Agent 365 prerequisites", src=src("a365", "a365ov"))
    _, yn = row(cv, 0, y2, [n1, n2, n3], gap=GUT)
    y3 = yn + 50
    with cv.panel(0, y3, title="Emergency stop across layers", sub="documented actions in our order: least destructive first", theme="red", style="dashed", pad=22,
                  title_size=26, sub_size=15, w=W) as pr:
        chain(cv, pr.ix, pr.iy, W - 44, [
            ("Entra or Agent 365 Block", "effective in up to 10 min, for agents created on or after 2026-10-23"),
            ("Else disable the endpoint", "minimum role Foundry User on the agent resource"),
            ("Stop the deployments", "Foundry Owner on the agent application"),
            ("Delete last", "prefer reversible actions; governance deletion does not delete Azure resources"),
            ("Elevate only if needed", "only a Global Administrator can elevate to User Access Administrator at /; remove it afterwards"),
        ], theme="red", dash="dashed", gap=60)
    return pr.bottom


# ============================================================================================== 3. stay informed
def stay_informed(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3  Stay informed: Service Health alerts, metric alerts and the consolidated view", size=34,
                   sub="Know about a service issue before your users do, and see cost, utilization and quota across Foundry Tools in one place")
    y += 100
    _, y1 = chain(cv, 0, y, W, [
        ("Open Service Health", "Azure portal > Service Health > Health alerts"),
        ("Add service health alert", "role: Monitoring Contributor"),
        ("Scope", "subscriptions, regions and services: Azure OpenAI, Foundry Models, Foundry Agent Service"),
        ("Condition", "Service issue, Planned maintenance, Health advisories, Security advisories"),
        ("Action group", "email, SMS or webhook"),
        ("Rule details", "complete the rule details; use Resource Health for a single resource"),
    ], theme="indigo", gap=56)
    y2 = y1 + 50
    m = Card(SPAN(2), "Metric alerts on deployments", [
        "ModelRequests: split by StatusCode to alert on 4xx, 5xx and 429",
        "ModelAvailabilityRate = (total requests - server errors) / total requests",
        "TimeToResponse",
        "NormalizedTimeBetweenTokens",
        "Split by ModelDeploymentName or StatusCode",
    ], theme="violet", icon="alerts", fill="hatch", title_size=21, body_size=16, src=src("health"))
    m.place(cv, 0, y2)
    rl = Card(SPAN(2), "Roles to see the consolidated view", [
        "Reader on the subscription or resource group",
        "For costs, also Foundry User on the resource and Cost Management Reader",
        "For quota at subscription scope, Cognitive Services Usages Reader (or Reader)",
    ], theme="gray", icon="dashboard", fill="hatch", title_size=21, body_size=16, src=src("consol"))
    rl.place(cv, 0, m.bottom + 28)
    t = Table([("Signal", 200), ("Mitigation the page lists", 888)], [
        [("5xx or a regional outage", "red"), "Fail over to another region. Global and Data Zone deployments add resilience but do not replace a multi-region plan"],
        [("Sustained 429", "yellow"), "Back off and honour Retry-After; spread load across deployments and regions with the APIM AI gateway; raise quota; or move to provisioned throughput (PTU-M)"],
        [("High latency", "blue"), "PTU (dedicated capacity and a latency SLA), or a nearby regional Standard deployment. Global and Data Zone optimise availability, not latency"],
    ], theme="indigo", size=15, head_size=16, title="Mitigations", title_size=22)
    t.place(cv, X(2), y2)
    n = Note(SPAN(2), "The docs' early-warning examples (quota above 80 percent, day-over-day cost above 15 percent) are illustrative, not product thresholds. "
             "The view lives in the Azure portal at portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/overview.",
             kind="warn", title="Examples, not thresholds", src=src("consol"))
    n.place(cv, X(2), t.bottom + 28)
    # consolidated view mock-up
    with cv.panel(X(4), y2, title="Azure portal: Foundry Tools consolidated view", sub="not the Foundry portal; no new resource types", theme="gray", style="dotted",
                  fill="soft", pad=20, title_size=22, sub_size=15, w=SPAN(2)) as cvp:
        iw = SPAN(2) - 40
        tw3 = (iw - 32) / 3

        def tile(w, label, sub=None, theme="gray", icon=None):
            return Box(w, label, sub=sub, theme=theme, fill="hatch", size=17, sub_size=13, pad=8, min_h=70, icon=icon, icon_pos="left", icon_size=26)

        r1 = [tile(tw3, "Alerts and service health", theme="indigo", icon="alerts"), tile(tw3, "Active resources by cost", theme="yellow", icon="cost-management"),
              tile(tw3, "Accumulated costs", theme="yellow", icon="cost-management")]
        _, b1 = row(cv, cvp.ix, cvp.iy, r1, gap=16)
        r2 = [tile(iw, "Model utilization", theme="blue", icon="metrics")]
        _, b2 = row(cv, cvp.ix, b1 + 16, r2, gap=16)
        r3 = [tile((iw - 16) / 2, "Resource breakdown by type", theme="gray", icon="all-resources"),
              tile((iw - 16) / 2, "Quota utilization", sub="docs example: gpt-4o 9,500 of 10,000 TPM in West US", theme="yellow", icon="quotas")]
        row(cv, cvp.ix, b2 + 16, r3, gap=16)
    return max(rl.bottom, n.bottom, cvp.bottom)


# ============================================================================================== 4. data residency
def residency(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Data residency: the deployment type decides where inference runs", size=34,
                   sub="Data at rest (uploads, the abuse-monitoring store, fine-tuned models) stays in the customer-designated geography for every deployment type")
    y += 100
    # nested boundaries
    with cv.panel(0, y, title="Global", sub="processes in any Azure geography where the model is deployed", theme="gray", style="dotted", fill="soft", pad=20,
                  title_size=24, sub_size=15, w=SPAN(3)) as g:
        with cv.panel(g.ix, g.iy, title="Data zone: US, EU Data Boundary or APAC", sub="Data Zone Standard, Provisioned and Batch process only inside the zone",
                      theme="blue", style="dashed", fill="soft", pad=20, title_size=22, sub_size=15, w=SPAN(3) - 40) as z:
            with cv.panel(z.ix, z.iy, title="Your designated geography", sub="Standard and Regional Provisioned process here; may hop between regions inside it for operations",
                          theme="cyan", style="solid", fill="soft", pad=18, title_size=21, sub_size=15, w=SPAN(3) - 80) as geo:
                chips = ChipFlow([Chip(t, theme="cyan", size=16) for t in ("Uploaded files", "Abuse-monitoring store", "Fine-tuned models", "Agent Service data (same region as the endpoint)")],
                                 SPAN(3) - 120, gap=10)
                chips.place(cv, geo.ix, geo.iy)
                cv.text(geo.ix, geo.iy + chips.h + 8, "Data at rest: stays in the designated geography for all deployment types", size=16, color="#0b7285")
    t = Table([("Deployment type", 300), ("Where prompts and completions are processed", 640), ("Notes", 676)], [
        [("Global (Standard, Provisioned)", "blue"), "Any Azure geography where the model is deployed", "Data at rest stays in the designated geography"],
        [("Global Batch", "blue"), "May process in any geography", "Data at rest stays in the designated geography until capacity is available"],
        [("Data Zone (Standard, Provisioned)", "blue"), "Only inside the data zone: US, EU Data Boundary or APAC", ""],
        [("Data Zone Batch", "blue"), "Processing stays inside the zone", ""],
        [("Standard, Regional Provisioned", "blue"), "In the chosen geography; may hop between regions inside it for operations", ""],
        [("Prompt caching", "gray"), "In-memory caching works everywhere", "Extended caching stays within the data-zone or regional boundary"],
        [("Fine-tuning", "gray"), "Global and Developer training do not guarantee regional residency", "See fine-tuning cost management"],
    ], theme="blue", size=15, head_size=16, title="Processing location by deployment type (as of 2026-11-03)", title_size=22)
    t.place(cv, X(3), y)
    y2 = max(g.bottom, t.bottom) + 40
    a = Card(SPAN(2), "Agent Service data", [
        "Endpoints are regional and data is stored in the same region",
        "Standard agent setup keeps threads, files and vector stores in your own Cosmos DB, Storage and AI Search; basic setup is Microsoft-managed",
        "Customer-managed keys apply only in the standard setup",
    ], theme="cyan", icon="cosmos", fill="hatch", title_size=21, body_size=16, src=src("faq", "std"))
    p = Card(SPAN(2), "Privacy statements", [
        "Prompts, completions, embeddings and training data are not used to train foundation models without permission",
        "Abuse monitoring: sampled review by automated means (LLMs), with human review only on flagged data; the store is logically separated per customer resource per geography",
        "Modified abuse monitoring approvals remove the storage and the human review",
    ], theme="red", icon="key-vault", fill="hatch", title_size=21, body_size=16, src=src("privacy"))
    r365 = Card(SPAN(2), "Residency exceptions and attestations", [
        "Agent 365 residency follows the storage location of the Entra tenant, not the Azure region of the Foundry resource: opt out per Foundry resource for residency-sensitive workloads",
        "Compliance attestations: the Foundry navigation links to aka.ms/AzureCompliance (the Service Trust Portal). The attestation lists were not read for this canvas: use the link",
    ], theme="grape", icon="compliance", fill="hatch", title_size=21, body_size=16, src=src("a365", "trust"))
    _, y3 = row(cv, 0, y2, [a, p, r365], gap=GUT)
    return y3


# ============================================================================================== 5. government + baseline
def government(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Azure Government and the security baseline", size=34,
                   sub="Availability differs in the US sovereign cloud; the baseline pages describe what to enable yourself")
    y += 100
    t = Table([("Capability", 400), ("Azure Government", 220), ("Note", 468)], [
        ["Responses API", CHECK, ""], ["Agent identity", CHECK, ""], ["Private networking", CHECK, ""], ["RBAC", CHECK, ""],
        ["Network security perimeter (NSP)", CHECK, ""],
        ["Content safety and guardrails", CHECK, "block lists, jailbreak, protected materials"],
        ["Tracing", CHECK, "prompt agents"],
        ["Provisioned throughput (PTU)", CHECK, "has its own Government page"],
        [("Model router", "red"), CROSS, ""], [("Evaluations", "red"), CROSS, ""], [("Optimization", "red"), CROSS, ""],
        ["Control Plane and AI gateway", DASH, "availability not stated in the Government pages"],
    ], theme="gray", size=15, head_size=16, title="Foundry in Azure Government (as of 2026-11-03)", title_size=22, align=["left", "center", "left"])
    t.place(cv, 0, y)
    g = Card(SPAN(2), "Regions and endpoints", [
        "Regions: US Gov Virginia (usgovvirginia) and US Gov Arizona (usgovarizona)",
        "Foundry portal: https://ai.azure.us/nextgen",
        "Project endpoint: https://{resource}.services.ai.azure.us/api/projects/{project}",
        "Azure portal: https://portal.azure.us",
    ], theme="gray", icon="globe", fill="hatch", title_size=21, body_size=16, src=src("gov"))
    g.place(cv, X(2), y)
    b = Card(SPAN(2), "Baselines to apply yourself", [
        "Managed VNet with Allow Only Approved Outbound and FQDN rules creates a managed Azure Firewall: extra cost, one per Foundry account",
        "Private link, Network Security Perimeter (preview), customer-managed keys and keyless authentication",
        "! The Azure security baseline page is based on Microsoft cloud security benchmark v1.0 and may contain outdated guidance",
        "Built-in Azure Policies are not enabled by default (part 1)",
    ], theme="indigo", icon="firewall", fill="hatch", title_size=21, body_size=16, src=src("baseline", "mvnet", "plan"))
    b.place(cv, X(4), y)
    n = Note(SPAN(4), "No model router, evaluations or optimization in Azure Government, and the Control Plane and AI gateway are not mentioned on the Government pages. "
             "Check the page before you design an Azure Government landing zone around them.", kind="gotcha", title="Plan around the gaps", src=src("gov"))
    n.place(cv, X(2), max(g.bottom, b.bottom) + 28)
    return max(t.bottom, n.bottom)


# ============================================================================================== 6. governance boundaries
def boundaries(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6  Plan your governance boundaries: co-located or isolated", size=34,
                   sub="Production defaults to isolation, exploration to colocation. Assign security, cost and incident ownership per boundary.")
    y += 100

    def project(w, name):
        return Box(w, name, theme="green", fill="hatch", size=18, min_h=60, dash="dashed", icon="folder", icon_pos="left", icon_size=26)

    with cv.panel(0, y, title="Co-located: one Foundry resource, many projects", sub="the default for exploration", theme="blue", style="dotted", fill="soft",
                  pad=22, title_size=24, sub_size=15, w=SPAN(3)) as left:
        with cv.panel(left.ix, left.iy, title="Foundry resource", sub="shared quota and a shared blast radius", theme="blue", style="solid", fill="none", pad=18,
                      title_size=21, sub_size=15, w=SPAN(3) - 44) as fr:
            pw = (SPAN(3) - 44 - 36 - 2 * 16) / 3
            row(cv, fr.ix, fr.iy, [project(pw, "Project A"), project(pw, "Project B"), project(pw, "Project C")], gap=16)
        n = Note(SPAN(3) - 44, "Trade-off: a shared blast radius for incidents, quota exhaustion and misconfiguration.", kind="gotcha", title="What you accept")
        n.place(cv, left.ix, fr.bottom + 18)
    with cv.panel(X(3), y, title="Isolated: one Foundry resource per production workload", sub="the default for production", theme="blue", style="dotted", fill="soft",
                  pad=22, title_size=24, sub_size=15, w=SPAN(3)) as right:
        rw = (SPAN(3) - 44 - 2 * 16) / 3
        resources = []
        px = right.ix
        for name in ("Workload 1", "Workload 2", "Workload 3"):
            with cv.panel(px, right.iy, title=f"Foundry resource: {name}", theme="blue", style="solid", fill="none", pad=14, title_size=17, w=rw) as r:
                project(rw - 28, "Project").place(cv, r.ix, r.iy)
            resources.append(r)
            px = r.right + 16
        n2 = Note(SPAN(3) - 44, "Strict containment, independent access control, and independent quota or cost boundaries. Self-serve is harder.", kind="tip", title="What you gain")
        n2.place(cv, right.ix, resources[0].bottom + 18)
    y2 = max(left.bottom, right.bottom) + 40
    c1 = Card(SPAN(2), "What does not isolate per project", [
        "Fine-tune training",
        "OpenAI image, video and batch",
        "Content Understanding",
        "Speech, Language and Translator",
        "Use separate Foundry resources when isolation is a must",
    ], theme="blue", icon="foundry", fill="hatch", title_size=21, body_size=16, src=src("plan"))
    c2 = Card(SPAN(2), "Self-serve guardrails to define", [
        "Who can create projects, deploy models and connect tools",
        "Policy on model providers and tool connections",
        "Cost controls and budget alerts",
        "Enforce trace logging into central observability across Foundry, Copilot Studio and Microsoft 365",
    ], theme="grape", icon="policy", fill="hatch", title_size=21, body_size=16, src=src("plan"))
    c3 = Card(SPAN(2), "Governance dashboards", [
        "Monitoring across fleets",
        "Agent 365 integration",
        "Defender for Cloud",
        "Azure Policy",
        "Sharing boundaries come from the Cloud Adoption Framework AI platform guidance",
    ], theme="gray", icon="dashboard", fill="hatch", title_size=21, body_size=16, src=src("plan", "arch"))
    _, y3 = row(cv, 0, y2, [c1, c2, c3], gap=GUT)
    return y3


# ============================================================================================== 7. gotchas + sources
def gotchas(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "7  Gotchas to remember", size=34)
    y += 70
    notes = [
        Note(CW, "Purview does not yet work with network isolation, and its coverage of agents is described inconsistently across pages. Verify it for your tenant before you rely on it.",
             kind="gotcha", title="Purview limits", src=src("compliance", "defender")),
        Note(CW, "Agent 365 activity data follows the Entra tenant's storage location, so it can cross the residency model you chose for the Foundry resource. Opt out per resource.",
             kind="gotcha", title="Agent 365 residency", src=src("a365")),
        Note(CW, "Entra Block applies to agents created on or after 2026-10-23 16:00 UTC. Older agents keep a legacy exception and can still run when their developer configuration is enabled.",
             kind="warn", title="Older agents are not stopped", src=src("govern")),
        Note(CW, "The security baseline page is based on benchmark v1.0 and may contain outdated guidance. Treat it as a checklist, not the latest control mapping.",
             kind="warn", title="Baseline is v1.0", src=src("baseline")),
        Note(CW, "No model router, evaluations or optimization in Azure Government, and the Control Plane is not mentioned there (as of 2026-11-03).",
             kind="gotcha", title="Azure Government gaps", src=src("gov")),
        Note(CW, "Global and Data Zone deployments add resilience but do not replace a multi-region plan, and they optimise availability, not latency.",
             kind="info", title="Resilience is not residency", src=src("health", "ha")),
    ]
    _, b = row(cv, 0, y, notes, gap=GUT)
    return b


def related(cv: Canvas, y: float) -> float:
    cv.text(0, y, "See also in this gallery:", size=18, color="#343a40")
    items = [("Governance, policy and compliance, part 1: the control stack", "grape"), ("Foundry Control Plane", "grape"),
             ("AI gateway and token limits", "grape"), ("Microsoft Foundry Cost Structure", "yellow"), ("Data protection and encryption: where your data lives", "red"),
             ("Foundry roles, scopes and least-privilege assignments", "red"), ("Foundry in an Azure landing zone, part 2", "indigo"),
             ("Monitoring, alerting and incident response", "violet")]
    f = ChipFlow([Chip(t, theme=th, size=16, fill="soft") for t, th in items], W - 260, gap=12).place(cv, 250, y - 4)
    return max(y + 28, f.y + f.h)


def sources_panel(cv: Canvas, y: float) -> None:
    items = [S[k] for k in ("diag", "consol", "health", "gov", "plan", "arch", "dtypes", "privacy", "compliance", "defender", "baseline", "a365",
                            "a365cfg", "a365ov", "govern", "faq", "std", "mvnet", "ft", "trust")]
    sources(cv, 0, y, items, w=W, cols=4)


def build(cv: Canvas) -> None:
    y = title_and_key(cv) + 30
    y = summary_strip(cv, y) + 60
    y = logging_section(cv, y) + 70
    y = partners_section(cv, y) + 70
    y = stay_informed(cv, y) + 70
    y = residency(cv, y) + 70
    y = government(cv, y) + 70
    y = boundaries(cv, y) + 70
    y = gotchas(cv, y) + 50
    y = related(cv, y) + 40
    sources_panel(cv, y)
