"""Governance, policy and compliance (part 1 of 2) - the control stack.

A layer cake of the controls from tenant down to agent (scope, mode, role), the Azure Policy built-ins for Foundry,
the deployment gate, custom policies, preview-feature suppression and the roles that configure each control.
Part 2 covers the evidence plane (logging, Defender, Purview, Entra, Service Health), residency and Azure Government.
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="governance-policy-compliance", title="Governance, policy and compliance", section="2",
    group="Control plane and cost", order=52,
    description="The governance stack in layers - tenant, management group and subscription, resource group, Foundry resource, project, deployment, agent - with Azure Policy built-ins, the deployment gate, preview suppression and the role that configures each control.",
    tags=["governance", "azure-policy", "rbac", "compliance", "preview-features", "landing-zone"],
)

# ---------------------------------------------------------------------------------------------- grid
CW, GUT = 520, 48
STEP = CW + GUT
W = 6 * CW + 5 * GUT          # 3360


def X(i: int) -> float:
    return i * STEP


def SPAN(n: int) -> float:
    return n * CW + (n - 1) * GUT


# ---------------------------------------------------------------------------------------------- sources
S = dict(
    mdp=("Model deployment policy", learn("how-to/model-deployment-policy")),
    custom=("Custom policy definitions", learn("how-to/custom-policy-definition")),
    router=("Model router policy", learn("how-to/model-router-policy")),
    preview=("Disable preview features", learn("how-to/disable-preview-features")),
    admin=("Administrator guide", learn("concepts/administrator-guide")),
    rbac=("Role-based access control for Foundry", learn("concepts/rbac-foundry")),
    diag=("Diagnostic logging", learn("how-to/diagnostic-logging")),
    consol=("Consolidated view for Foundry Tools", learn("concepts/foundry-consolidated-view")),
    health=("Stay informed with Service Health", learn("how-to/stay-informed-service-health")),
    gov=("Foundry in Azure Government", learn("concepts/foundry-azure-government")),
    plan=("Plan your Foundry rollout", learn("concepts/planning")),
    arch=("Foundry architecture", learn("concepts/architecture")),
    dtypes=("Deployment types for Foundry Models", learn("foundry-models/concepts/deployment-types")),
    privacy=("Data, privacy and security", learn("responsible-ai/openai/data-privacy")),
    ga=("Feature status at GA", learn("concepts/general-availability")),
    compliance=("Manage compliance and security", learn("control-plane/how-to-manage-compliance-security")),
    quickstart=("Create a guardrail policy", learn("control-plane/quickstart-create-guardrail-policy")),
    guardrails=("Guardrails overview", learn("guardrails/guardrails-overview")),
    govern=("Govern agent infrastructure (Entra admin)", learn("control-plane/govern-agent-infrastructure-entra-admin")),
    agentid=("Agent identity", learn("agents/concepts/agent-identity")),
    instant=("Instant access to models (preview)", learn("concepts/instant-models")),
    gw=("Enable an AI gateway", learn("configuration/enable-ai-api-management-gateway-portal")),
    std=("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
    costs=("Plan and manage costs", learn("concepts/manage-costs")),
    toolgov=("Govern tools with the AI gateway (preview)", learn("agents/how-to/tools/governance")),
    polref=("Built-in policy definitions for Foundry Tools", learn("azure/ai-services/policy-reference", base="")),
    baseline=("Azure security baseline for Foundry", learn("security/benchmark/azure/baselines/azure-ai-foundry-security-baseline", base="")),
    defender=("Enable threat protection for AI services", learn("azure/defender-for-cloud/ai-onboarding", base="")),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


_KitNote = Note


def Note(*a, **kw):  # noqa: N802 - the kit leaves no bottom padding under citation lines; add it here
    n = _KitNote(*a, **kw)
    if kw.get("src"):
        n.h += 10
    return n


# ---------------------------------------------------------------------------------------------- small helpers
class Blk(Rect2):
    """Placed rectangle (anchor for connectors)."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


DOT = dict(deny=("#e03131", "#ffc9c9"), audit=("#f08c00", "#ffec99"), fix=("#2f9e44", "#b2f2bb"))


def dot(cv: Canvas, cx: float, cy: float, kind: str, on: bool = True, d: float = 22) -> None:
    stroke, fill = DOT[kind]
    if on:
        cv.ellipse(cx - d / 2, cy - d / 2, d, d, stroke=stroke, fill=fill, style="solid", sw=2, rough=0)
    else:
        cv.ellipse(cx - d / 2 + 4, cy - d / 2 + 4, d - 8, d - 8, stroke="#adb5bd", sw=1.5, dash="dotted", rough=0)


class ModeCell(Rect2):
    """Three dots: Deny (red), Audit (amber), Fix = DeployIfNotExists or Modify (green); a hollow dot = not at this layer."""

    def __init__(self, w, modes, theme):
        self.w, self.modes, self.th = w, modes, THEMES[theme]
        self.h = 56
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=1.5)
        for i, (kind, on) in enumerate(zip(("deny", "audit", "fix"), self.modes)):
            dot(cv, x + self.w * (2 * i + 1) / 6, y + H / 2, kind, bool(on))
        cv.register("mode", x, y, self.w, H)
        return self


class ChipBox(Rect2):
    """Soft panel holding captioned groups of chips; a (label, 'preview') spec draws a dashed chip."""

    def __init__(self, w, groups, theme, *, pad=14):
        self.w, self.th, self.pad = w, THEMES[theme], pad
        self.groups = []
        h = pad
        for cap, specs in groups:
            chips = []
            for s in specs:
                label, kind = (s, "") if isinstance(s, str) else s
                chips.append(Chip(label, theme=theme, size=16, dash="dashed" if kind == "preview" else "solid"))
            flow = ChipFlow(chips, w - 2 * pad, gap=9)
            cap_h = 14 * 1.25 + 5 if cap else 0
            self.groups.append((cap, flow, cap_h))
            h += cap_h + flow.h + 12
        self.h = h - 12 + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=1.5)
        yy = y + self.pad
        for cap, flow, cap_h in self.groups:
            if cap:
                cv.text(x + self.pad, yy, cap, size=14, color=self.th.deep)
                yy += cap_h
            flow.place(cv, x + self.pad, yy)
            yy += flow.h + 12
        cv.register("chipbox", x, y, self.w, H, container=True)
        return self


# ============================================================================================== 0. title, key, summary
def title_and_key(cv: Canvas) -> float:
    _, bottom = title_block(
        cv, 0, 0, "Governance, policy and compliance",
        "Part 1 of 2 - the control stack: which control lives at which layer, who configures it, and how to gate, suppress and roll it out  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    with cv.panel(0, y, theme="gray", style="dotted", pad=16, w=W) as k:
        cv.text(k.ix, k.iy - 2, "Colour = area", size=16, color="#343a40")
        legend(cv, k.ix + 150, k.iy - 2, [
            ("Models and deployments", "blue"), ("Agents and projects", "green"), ("Tools", "orange"),
            ("Observability", "violet"), ("Guardrails", "pink"), ("Identity, security, RBAC", "red"),
            ("Networking", "indigo"), ("Governance and policy", "grape"), ("Cost and quota", "yellow"),
            ("Data", "cyan"), ("Neutral", "gray")], size=15, gap=22)
        y2 = k.iy + 34
        cv.text(k.ix, y2, "Markers", size=16, color="#343a40")
        cx = k.ix + 150
        for kind, label in (("deny", "Deny: preventive"), ("audit", "Audit: detective"),
                            ("fix", "DeployIfNotExists or Modify: corrective")):
            dot(cv, cx + 9, y2 + 10, kind, True, d=18)
            t = cv.text(cx + 26, y2, label, size=15)
            cx += 26 + t.w + 32
        dot(cv, cx + 9, y2 + 10, "deny", False, d=18)
        t = cv.text(cx + 26, y2, "hollow = not offered at that layer", size=15)
        cx += 26 + t.w + 32
        draw_badge(cv, cx, y2 - 1, "ga")
        draw_badge(cv, cx + 50, y2 - 1, "preview")
        t = cv.text(cx + 140, y2, "status as of 2026-11-03", size=15)
        cx += 140 + t.w + 32
        Chip("dashed chip", theme="gray", size=14, dash="dashed", pad_y=3).place(cv, cx, y2 - 3)
        t = cv.text(cx + 120, y2, "= preview control", size=15)
        cx += 120 + t.w + 32
        cv.rect(cx, y2 + 1, 28, 18, stroke="#495057", sw=2, dash="dashed")
        cv.text(cx + 38, y2, "our ordering of documented guidance", size=15)
    return k.bottom


def summary_strip(cv: Canvas, y: float) -> float:
    def tile(title, body, theme, icon, keys):
        return Card(CW, title, ["= " + body], theme=theme, icon=icon, fill="hatch", title_size=22, body_size=15, pad=14,
                    gap=4, icon_size=34, src=src(*keys))

    tiles = [
        tile("Policies are off by default", "Foundry's built-in Azure Policies are not enabled by default: review them and assign the ones you need.",
             "grape", "policy", ("baseline",)),
        tile("24 built-in definitions", "Index read on 2026-11-03. Model approval and eligibility are GA; content-filter and tool allow / deny groups are preview.",
             "grape", "compliance", ("polref",)),
        tile("Deny gates the Deploy button", "Policy is evaluated at deployment time. The catalog still lists every model; Deploy is disabled with the policy name and assignment ID.",
             "blue", "openai", ("mdp",)),
        tile("Existing deployments stay", "Deny never removes what is already deployed. The compliance view flags them: edit the model subset or delete the deployment.",
             "blue", "foundry", ("mdp",)),
        tile("Roles split the work", "Owner or Resource Policy Contributor writes policy; Foundry Account Owner deploys; Entra AI Administrator or Global Administrator governs agent availability.",
             "red", "managed-identity", ("admin",)),
        tile("Minutes to a day", "Role assignments up to 5 min, Entra agent state up to 10 min, a new policy assignment 15 min or more, custom and guardrail policies up to 30 min, diagnostic logs up to 2 h, compliance state up to 24 h.",
             "yellow", "scheduler", ("mdp", "diag")),
    ]
    _, bottom = row(cv, 0, y, tiles, gap=GUT)
    return bottom


# ============================================================================================== 1. layer cake
LABEL_W, STAIR, G = 470, 34, 24
C_W, WH_W, M_W = 1160, 740, 210
R_W = W - LABEL_W - C_W - WH_W - M_W - 4 * G

LAYERS = [
    dict(code="L0", name="Tenant", sub="Microsoft Entra and Agent 365", theme="red", icon="conditional-access",
         groups=[(None, ["Agent availability: block, unblock, delete, restore", "Conditional Access", "Identity Protection",
                         "Network access", "Expiry, owners, sponsors", "Agent 365 registry", "Data-collection consent"])],
         where=["Entra admin center and Microsoft 365 admin center (Agent 365)",
                "Preventive runtime disable. Foundry enforces Entra state for agents created on or after 2026-10-23 16:00 UTC; older agents keep a legacy exception"],
         modes=(1, 0, 0),
         roles=["Entra AI Administrator or Global Administrator; owners and sponsors for their own identities",
                "Conditional Access Administrator for Conditional Access"],
         src=("govern", "agentid")),
    dict(code="L1", name="Management group or subscription", sub="the widest Azure scope you govern", theme="grape", icon="management-group",
         groups=[("Azure Policy assignments", ["Model approval and eligibility", ("Content-filter policies", "preview"),
                                              ("Tool allow / deny", "preview"), "Customer-managed keys", "Disable local (key) auth",
                                              "Network access", "Diagnostic logging"]),
                 ("Subscription services and switches", ["Defender for Cloud plan", "Purview toggle", "Budgets in Cost Management",
                                                         "Service Health alerts", "Quota: subscription x region x model",
                                                         "Preview-suppression tag", "Custom RBAC roles", ("Instant-access disable", "preview")])],
         where=["Azure Policy, the Defender plans page, Foundry Operate > Compliance (preview), Cost Management and Service Health",
                "Mode follows the definition's effect: Deny, Audit, DeployIfNotExists or Modify"],
         modes=(1, 1, 1),
         roles=["Owner or Resource Policy Contributor: Azure Policy", "Security Admin or Owner: Defender for Cloud",
                "Foundry Account Owner: Purview toggle", "Contributor or Tag Contributor: tags", "Owner: custom RBAC roles"],
         src=("mdp", "compliance", "preview")),
    dict(code="L2", name="Resource group", sub="same controls, narrower scope", theme="gray", icon="resource-group",
         groups=[(None, ["Same policy assignments, narrower scope", "Guardrail-policy scope", "RBAC",
                         "Cost scope: Cost analysis defaults to the resource group", "Tags"])],
         where=["Azure Policy, or the Foundry Compliance wizard: a guardrail policy is an Azure Policy assignment on one subscription or one resource group"],
         modes=(1, 1, 0),
         roles=["Owner or Resource Policy Contributor"],
         src=("quickstart", "costs")),
    dict(code="L3", name="Foundry resource", sub="Microsoft.CognitiveServices/accounts", theme="blue", icon="foundry",
         groups=[(None, ["RBAC", "Private link, managed VNet, NSP", "Customer-managed keys", "Disable local (key) auth", "Diagnostic settings",
                         "AI Gateway link", "a365LoggingEnabled", "Model deployments + deployment type", "Guardrail (RAI policy) creation",
                         "Content blocklists", ("Instant-model allow-list", "preview"), "Tag AZML_DISABLE_PREVIEW_FEATURE"])],
         where=["ARM, portal and Azure Policy aliases",
                "Foundry shares the Microsoft.CognitiveServices namespace, so existing Azure OpenAI custom policies and RBAC actions continue to apply"],
         modes=(1, 1, 1),
         roles=["Foundry Account Owner, Foundry Owner or Contributor", "Monitoring Contributor for diagnostic settings"],
         src=("arch", "admin", "diag")),
    dict(code="L4", name="Project", sub="the development boundary", theme="green", icon="folder",
         groups=[(None, ["RBAC: Foundry User and friends", "Connections: custom policy on category", "No API-key auth connections",
                         "Application Insights connection", "Per-project token limits (AI gateway)", ("project cost tag", "preview"),
                         "BYO resources: standard agent setup", "Network: agent subnet"])],
         where=["Foundry portal and Azure Policy (a custom policy on the connection category)"],
         modes=(1, 1, 0),
         roles=["Foundry Project Manager: manage the project, conditionally assign Foundry User", "Foundry Owner",
                "API Management Service Contributor or Owner: token limits through the gateway"],
         src=("custom", "gw", "std")),
    dict(code="L5", name="Model deployment", sub="evaluated when you deploy", theme="blue", icon="openai",
         groups=[(None, ["Approved models", "Eligibility: no preview models, Direct from Azure only", "Model-router subset",
                         "Deployment type (SKU) restriction", "Guardrail: Microsoft.DefaultV2 or a custom RAI policy",
                         "Guardrail compliance in Operate > Compliance", "Token limits per deployment"])],
         where=["Azure Policy at deploy time, plus Foundry guardrails",
                "Deny blocks the deployment; the compliance scan flags existing ones"],
         modes=(1, 1, 0),
         roles=["Foundry Account Owner: create deployments and guardrails", "Resource Policy Contributor: policy"],
         src=("mdp", "router", "guardrails")),
    dict(code="L6", name="Agent", sub="the narrowest scope", theme="green", icon="agent",
         groups=[(None, ["Agent identity: blueprint + identity, no default permissions", "Agent-scope RBAC: endpoint access only",
                         "Agent guardrail overrides the model's", ("Tool allow / deny policy", "preview"), "Enable, disable, publish",
                         "Entra Block (agents created from 2026-10-23)"])],
         where=["Entra, Foundry and Azure Policy",
                "Guardrails apply to agents built in Agent Service, not to other agents registered in the Control Plane"],
         modes=(1, 1, 0),
         roles=["Foundry Project Manager: publish, at Foundry resource scope", "Foundry User: disable or enable the agent endpoint",
                "Foundry Owner: stop application deployments"],
         src=("agentid", "rbac", "govern")),
]


def layer_cake(cv: Canvas, y: float) -> float:
    x_c = LABEL_W + G
    x_w = x_c + C_W + G
    x_m = x_w + WH_W + G
    x_r = x_m + M_W + G
    for x, text in ((0, "Layer (scope narrows going down)"), (x_c, "Controls you can set at this layer"),
                    (x_w, "Where it is enforced, and how"), (x_m + 6, "Mode"), (x_r, "Role that configures it")):
        cv.text(x, y, text, size=20, color="#343a40")
    for i, (kind, lab) in enumerate((("deny", "Deny"), ("audit", "Audit"), ("fix", "Fix"))):
        tw = text_size(lab, 13)[0]
        cv.text(x_m + M_W * (2 * i + 1) / 6 - tw / 2, y + 26, lab, size=13, color=DOT[kind][0])
    cv.line((0, y + 46), (W, y + 46), stroke="#343a40", sw=2)
    top = y + 62
    prev = None
    for i, L in enumerate(LAYERS):
        label = Card(LABEL_W - i * STAIR, f"{L['code']}  {L['name']}", [], theme=L["theme"], subtitle=L["sub"], icon=L["icon"],
                     fill="solid", title_size=21, sub_size=14, pad=14, icon_size=32)
        ctl = ChipBox(C_W, L["groups"], L["theme"])
        where = Card(WH_W, None, L["where"], theme=L["theme"], fill="soft", body_size=16, pad=12, gap=4, src=src(*L["src"]))
        mode = ModeCell(M_W, L["modes"], L["theme"])
        roles = Card(R_W, None, L["roles"], theme=L["theme"], fill="soft", body_size=16, pad=12, gap=4)
        h = max(label.h, ctl.h, where.h, mode.h, roles.h)
        label.place(cv, i * STAIR, top, h=h)
        ctl.place(cv, x_c, top, h=h)
        where.place(cv, x_w, top, h=h)
        mode.place(cv, x_m, top, h=h)
        roles.place(cv, x_r, top, h=h)
        if prev is not None:
            arrow(cv, [(LABEL_W - 26, prev + 3), (LABEL_W - 26, top - 3)], color="#868e96", sw=2, end_head="arrow")
        prev = top + h
        top += h + 26
    return prev


def clock(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "How long until a change bites (as of 2026-11-03)", size=28,
                   sub="Plan the order of operations around these delays: test a Deny only after the assignment has propagated")
    line_y = y + 195
    bottom = timeline(cv, 0, line_y, W, [
        ("up to 5 min", "Role assignments", "Azure RBAC propagation (administrator guide)"),
        ("up to 10 min", "Entra agent state", "Block or Unblock reaches Foundry"),
        ("wait >= 15 min", "Policy assignment", "before you test a negative deployment"),
        ("up to 30 min", "Custom policy or guardrail policy", "evaluation, and the Foundry Compliance UI after create or edit"),
        ("up to 2 h", "Diagnostic logs", "arrive in Log Analytics or Storage"),
        ("up to 24 h", "Compliance state", "or trigger an on-demand scan"),
    ], label_w=480, size=20, theme="grape")
    return bottom


def evidence_teaser(cv: Canvas, y: float) -> float:
    with cv.panel(0, y, title="Evidence plane: how you prove the controls work",
                  sub="the detail is in Governance, policy and compliance, part 2: logging, Defender, Purview, Entra, Service Health, residency and Azure Government",
                  theme="violet", style="dotted", pad=22, title_size=24, sub_size=15, w=W) as p:
        bw = (W - 2 * 22 - 5 * 24) / 6
        items = [
            ("Azure Monitor diagnostics", "audit, request and response logs, metrics", "violet", "diagnostics"),
            ("Policy compliance", "per-assignment state; scan up to 24 h", "grape", "policy"),
            ("Defender for Cloud", "posture recommendations and prompt-attack alerts", "red", "defender"),
            ("Microsoft Purview", "audit, DSPM for AI, SIT classification", "red", "info-protection"),
            ("Consolidated view", "Azure portal: alerts, cost, utilization, quota", "gray", "dashboard"),
            ("Service Health", "service issues, planned maintenance, advisories", "indigo", "service-health"),
        ]
        boxes = [Box(bw, t, sub=s, theme=th, icon=ic, icon_pos="left", icon_size=30, fill="hatch", size=18, sub_size=14, pad=12, min_h=92)
                 for t, s, th, ic in items]
        _, b = row(cv, p.ix, p.iy, boxes, gap=24)
    return p.bottom


# ============================================================================================== 2. policy index
def eff(text: str):
    t = text.lower()
    th = "red" if "deny" in t else ("green" if ("deployifnotexists" in t or "modify" in t) else "yellow")
    return (text, th)


PREV = ("Preview, 1.0.0-preview", "orange")
COLS = [("Definition (portal name)", 860), ("Effects", 420), ("Status, version", 376)]


def policy_index(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2  Azure Policy built-in definitions for Foundry: 24 in the index (read 2026-11-03)", size=34,
                   sub="Not enabled by default. The Effects cell is tinted by the strongest effect the definition offers.")
    y += 100
    lx = 0
    for label, th in (("can Deny: preventive", "red"), ("DeployIfNotExists or Modify: corrective", "green"),
                      ("Audit or AuditIfNotExists only: detective", "yellow")):
        ch = Chip(label, theme=th, size=16).place(cv, lx, y)
        lx += ch.w + 18
    cv.text(lx + 10, y + 5, "Disabled is an allowed effect on every definition", size=15, color=MUTED)
    y += 56
    t_model = Table(COLS, [
        ["Foundry model deployments should only use approved models\nformerly: Cognitive Services Deployments should only use approved Registry Models; same definition ID aafe3651-cb78-4f68-9f81-e7e41509110f",
         eff("Audit, Deny, Disabled"), ("GA, v1.0.2", "green")],
        ["Foundry model deployments should meet eligibility requirements\nID 8791d062-ba96-4c34-b604-8538f7e30ca0; checks availability status (preview or GA) and distribution source",
         eff("Audit, Deny, Disabled"), ("GA, v1.0.1", "green")],
    ], theme="blue", size=14, head_size=15, title="Model governance", title_size=22)
    t_tools = Table(COLS, [
        ["[Preview] Microsoft Foundry agents and toolboxes should not use denied tools\nID 7740c22b-07ef-4bac-9f5a-e38d188f80b7; covers tool types, MCP endpoints and MCP connectors",
         eff("Audit, Deny, Disabled"), PREV],
        ["[Preview] Microsoft Foundry agents and toolboxes should only use approved tools\nID e7352ad2-6c86-4a07-9573-47f67b557ba8",
         eff("Audit, Deny, Disabled"), PREV],
    ], theme="orange", size=14, head_size=15, title="Tool governance", title_size=22)
    cf_rows = [
        "[Preview] Cognitive Services Agents should only use allowed control (multi-severity harmful-content filtering)",
        "[Preview] Cognitive Services Agents should only use allowed prompt content filtering",
        "[Preview] Cognitive Services Deployments should only use allowed completion content filtering",
        "[Preview] Cognitive Services Deployments should only use allowed control (multi-severity)",
        "[Preview] Cognitive Services Deployments Should Only Use Allowed Control Mode",
        "[Preview] Cognitive Services Deployments should only use allowed prompt content filtering",
    ]
    t_cf = Table(COLS, [[r, eff("Audit, Disabled"), PREV] for r in cf_rows], theme="pink", size=14, head_size=15,
                 title="Content filtering and guardrails (Audit only)", title_size=22)
    t_id = Table(COLS, [
        ["Azure AI Services resources should encrypt data at rest with a customer-managed key (CMK)\nnot assessed by default: apply only when compliance or policy requires it",
         eff("Audit, Deny, Disabled"), "v2.2.0"],
        ["Azure AI Services resources should have key access disabled (disable local authentication)\nAzure OpenAI Studio requires key access and will not function if it is disabled",
         eff("Audit, Deny, Disabled"), "v1.1.0"],
        ["Configure Azure AI Services resources to disable local key access (disable local authentication)", eff("DeployIfNotExists, Disabled"), "v1.0.0"],
        ["Configure Cognitive Services accounts to disable local authentication methods", eff("Modify, Disabled"), "v1.0.0"],
        ["Azure AI Services resources should restrict network access", eff("Audit, Deny, Disabled"), "v3.3.0"],
        ["Azure AI Services resources should use Azure Private Link", eff("Audit, Disabled"), "v1.0.0"],
        ["Configure Cognitive Services accounts to disable public network access", eff("Disabled, Modify"), "v3.0.0"],
        ["Configure Cognitive Services accounts with private endpoints", eff("DeployIfNotExists, Disabled"), "v3.0.0"],
        ["Cognitive Services accounts should use a managed identity", eff("Audit, Deny, Disabled"), "v1.0.0"],
        ["Cognitive Services accounts should use customer owned storage", eff("Audit, Deny, Disabled"), "v2.0.0"],
    ], theme="red", size=14, head_size=15, title="Identity, network and encryption", title_size=22)
    t_log = Table(COLS, [
        ["Diagnostic logs in Azure AI services resources should be enabled", eff("AuditIfNotExists, Disabled"), "v1.0.0"],
        ["Enable logging by category group for Cognitive Services (microsoft.cognitiveservices/accounts) to Event Hub",
         eff("DeployIfNotExists, AuditIfNotExists, Disabled"), "v1.2.0"],
        ["Enable logging by category group for Cognitive Services (microsoft.cognitiveservices/accounts) to Log Analytics",
         eff("DeployIfNotExists, AuditIfNotExists, Disabled"), "v1.1.0"],
        ["Enable logging by category group for Cognitive Services (microsoft.cognitiveservices/accounts) to Storage",
         eff("DeployIfNotExists, AuditIfNotExists, Disabled"), "v1.1.0"],
    ], theme="violet", size=14, head_size=15, title="Logging", title_size=22)
    gap = 34
    yl = y
    for t in (t_model, t_tools, t_cf):
        t.place(cv, 0, yl)
        yl = t.y + t.h + gap
    yr = y
    for t in (t_id, t_log):
        t.place(cv, X(3), yr)
        yr = t.y + t.h + gap
    yb = max(yl, yr) - gap + 40
    n1 = Note(SPAN(2), "The model-router-specific definitions (deployment regions, required routing rules, logging configurations; public preview) are named on the "
              "model router policy page but are not in this index. Find them in the Azure Policy Definitions catalog.",
              kind="info", title="Not in the index", src=src("router", "polref"))
    n2 = Note(SPAN(2), "Foundry provides built-in Azure Policies, but they are not enabled by default: review them and enable the ones you need. The security baseline page "
              "is based on Microsoft cloud security benchmark v1.0 and warns that it may contain outdated guidance.",
              kind="warn", title="Policies are not enabled by default", src=src("baseline"))
    n3 = Note(SPAN(2), "Azure OpenAI Studio requires key access and will not function once key access is disabled. Plan Microsoft Entra authentication "
              "before you assign the disable-local-auth definitions.", kind="gotcha", title="Disable local auth breaks key-based tools", src=src("polref"))
    _, b = row(cv, 0, yb, [n1, n2, n3], gap=GUT)
    return b


# ============================================================================================== 3. deployment gate
def chain(cv: Canvas, x: float, y: float, w: float, steps, *, theme="grape", dash="solid", gap=56, size=19, sub_size=15):
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


def deployment_gate(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3  Model deployment policy: the deployment gate", size=34,
                   sub="Policy runs at deployment time. The catalog never hides a model: it disables Deploy and tells you why. The order of the checks is our reading: the docs state only that approval is reported before eligibility.")
    y += 100
    widths = dict(A=380, B=560, C=400, D=400, E=420, F=380)
    gap = (W - sum(widths.values())) / 5
    xs, cx = {}, 0.0
    for k in "ABCDEF":
        xs[k] = cx
        cx += widths[k] + gap
    with cv.panel(xs["B"], y, title="Azure Policy gate", sub="approval is checked first, then eligibility", theme="grape", style="dashed",
                  fill="soft", pad=18, title_size=24, sub_size=15, w=widths["B"]) as pb:
        bx = pb.ix
        bw = widths["B"] - 36
        inner = [
            Box(bw, "Approved models", sub="allowedPublishers, allowedAssetIds (prefix match)", theme="grape", fill="hatch", size=18, sub_size=14, pad=8, min_h=72),
            Box(bw, "Eligibility", sub="denyPreviewModels, onlyAllowDirectFromAzure", theme="grape", fill="hatch", size=18, sub_size=14, pad=8, min_h=72),
            Box(bw, "Deployment type (SKU)", sub="custom policy on deployments/sku.name", theme="grape", fill="hatch", size=18, sub_size=14, pad=8, min_h=72, dash="dashed"),
        ]
        col(cv, bx, pb.iy, inner, gap=14)
    ym = pb.y + pb.h / 2

    def mid(k, label, sub, theme, icon=None, dash="solid"):
        b = Box(widths[k], label, sub=sub, theme=theme, fill="hatch", size=19, sub_size=14, pad=10, icon=icon, icon_pos="left", icon_size=32,
                min_h=118, dash=dash)
        return b.place(cv, xs[k], ym - b.h / 2)

    A = mid("A", "Developer selects Deploy", "portal, ARM, CLI or REST", "gray", "users")
    C = mid("C", "RBAC check", "Foundry Account Owner on the resource; marketplace models also need Contributor on the subscription", "red", "managed-identity")
    D = mid("D", "Quota check", "TPM or PTU available for this subscription x region x model?", "yellow", "quotas")
    E = mid("E", "Guardrail assigned", "Microsoft.DefaultV2 by default, or a custom RAI policy", "pink", "content-safety")
    F = mid("F", "Deployment created", "now a compliance asset", "blue", "openai")
    for n, b in zip((1, 3, 4, 5, 6), (A, C, D, E, F)):
        numbered(cv, b.x + 6, b.y + 6, n, theme=b.th.name, d=28, size=16)
    numbered(cv, pb.x + 10, pb.y + 10, 2, theme="grape", d=28, size=16)
    connect(cv, A, pb, a_side="right", b_side="left", end_head="arrow", sw=2)
    connect(cv, pb, C, a_side="right", b_side="left", end_head="arrow", sw=2, label="allowed", label_size=15)
    connect(cv, C, D, a_side="right", b_side="left", end_head="arrow", sw=2)
    connect(cv, D, E, a_side="right", b_side="left", end_head="arrow", sw=2)
    connect(cv, E, F, a_side="right", b_side="left", end_head="arrow", sw=2)
    # second row
    y2 = pb.bottom + 66
    blocked = Box(widths["B"], "Blocked at deploy time", sub="Portal: Deploy is disabled with the reason, the policy name and the assignment ID. ARM, CLI or REST: a noncompliant model fails the whole deployment",
                  theme="red", fill="hatch", size=19, sub_size=14, pad=10, min_h=118).place(cv, xs["B"], y2)
    connect(cv, pb, blocked, a_side="bottom", b_side="top", end_head="arrow", sw=2, color="#e03131", label="Deny", label_size=16, label_color="#c92a2a")
    G7 = Box(widths["F"], "Compliance scan", sub="up to 24 h, or an on-demand scan", theme="grape", fill="hatch", size=19, sub_size=14, pad=10, min_h=118, dash="dashed").place(cv, xs["F"], y2)
    G8 = Box(widths["E"], "Operate > Compliance (preview)", sub="Violations detected; guardrail coverage gaps", theme="grape", fill="hatch", size=19, sub_size=14, pad=10, min_h=118, dash="dashed").place(cv, xs["E"], y2)
    G9 = Box(widths["D"], "Fix now", sub="opens the deployment's guardrail configuration; for a noncompliant model, edit the subset or delete the deployment", theme="green", fill="hatch", size=19, sub_size=14, pad=10, min_h=118, dash="dashed").place(cv, xs["D"], y2)
    for n, b in zip((7, 8, 9), (G7, G8, G9)):
        numbered(cv, b.x + 6, b.y + 6, n, theme=b.th.name, d=28, size=16)
    connect(cv, F, G7, a_side="bottom", b_side="top", end_head="arrow", sw=2, dash="dashed")
    connect(cv, G7, G8, a_side="left", b_side="right", end_head="arrow", sw=2, dash="dashed")
    connect(cv, G8, G9, a_side="left", b_side="right", end_head="arrow", sw=2, dash="dashed")
    nb = Note(widths["C"], "Deny never removes existing deployments. The compliance view flags them; remediate by editing the subset or deleting.",
              kind="info", title="Brownfield", src=src("mdp")).place(cv, xs["C"], y2)
    y3 = max(blocked.bottom, G9.bottom, nb.bottom) + 56

    # detail cards ------------------------------------------------------------------------------
    def dc(title, body, theme, icon, keys, badge=None):
        return Card(CW, title, body, theme=theme, icon=icon, badge=badge, fill="hatch", title_size=20, body_size=15, pad=14, gap=4, icon_size=32, src=src(*keys))

    cards = [
        dc("Approved models policy", [
            "Parameters: effect (Deny recommended, Audit to trial first), allowedPublishers, allowedAssetIds",
            "allowedPublishers: publisher name from the model card, case-sensitive, for example OpenAI",
            "allowedAssetIds: the model's Model ID, for example azureml://registries/azure-openai/models/gpt-5.2/versions/1",
            "! Asset IDs are prefix-matched: .../models/gpt-5 also matches gpt-5.2 and gpt-5.4. End with / to pin one model (all versions) or give the full versioned ID",
        ], "blue", "openai", ("mdp",)),
        dc("Eligibility policy", [
            "Two parameters, both false by default, so an unconfigured policy restricts nothing",
            "onlyAllowDirectFromAzure: only models sold directly by Azure",
            "denyPreviewModels: block preview models",
            "Checks availability status (preview or GA) and distribution source",
            "When several policies block, approval is reported first, then eligibility",
        ], "blue", "policy", ("mdp",)),
        dc("Model router", [
            "Honours the same policies: the router and every model in its routing set must be allowed (publisher Microsoft for the router, plus each routed model's publisher such as Anthropic)",
            "ARM, CLI, REST: any noncompliant model fails the entire deployment",
            "Portal: unapproved checkboxes are disabled under a banner 'governed by Azure Policy'; View blocked lists 'Models blocked by IT Admin'; the compliant subset can be deployed",
            "Router-specific definitions (deployment regions, required routing rules, logging configurations) are in public preview",
        ], "blue", "ai-services", ("router",)),
        dc("Scope, roles, timing", [
            "Scope: management group, subscription or resource group",
            "Role: Owner or Resource Policy Contributor",
            "Wait at least 15 min after assigning; compliance state takes up to 24 h, or run an on-demand scan",
            "Best practices listed: granular scoping, naming convention, tags, documentation, periodic review, test in non-prod, communicate to developers",
        ], "grape", "management-group", ("mdp",)),
        dc("Instant access (preview)", [
            "Covered by the same approval and eligibility policies",
            "Admins can disable it per account: properties.instant = { raiPolicyName: Microsoft.DefaultV2, modelAllowList: [] } (api-version 2026-01-15-preview)",
            "West US 3 only, as of 2026-11-03",
        ], "orange", "preview-features", ("instant",), badge="preview"),
        dc("Restrict a deployment type", [
            "Custom policy on Microsoft.CognitiveServices/accounts/deployments with deployments/sku.name equal to the SKU, for example GlobalStandard",
            "! The doc snippet shows the if condition only, with no then effect: add the effect you want",
        ], "blue", "regions", ("dtypes",)),
    ]
    _, y4 = row(cv, 0, y3, cards, gap=GUT)

    # roll out safely ---------------------------------------------------------------------------
    y5 = y4 + 56
    with cv.panel(0, y5, title="Roll out a policy safely", sub="documented best practices in our order: Audit first is documented, the sequence is ours", theme="grape",
                  style="dashed", pad=22, title_size=26, sub_size=15, w=W) as pr:
        chain(cv, pr.ix, pr.iy, W - 44, [
            ("Assign with Audit", "trial the effect first"),
            ("Watch compliance", "Operate > Compliance or the Azure Policy dashboard"),
            ("Switch to Deny", "recommended effect for approved models"),
            ("Wait >= 15 min", "assignment propagation"),
            ("Test both ways", "one noncompliant and one compliant deployment, in non-prod first"),
            ("Tell developers", "naming convention, tags and documentation"),
            ("Review periodically", "granular scoping keeps exceptions small"),
        ], theme="grape", dash="dashed", gap=52)
    return pr.bottom


# ============================================================================================== 4. custom policies + preview
def custom_and_preview(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Custom policies, and switching preview features off", size=34,
                   sub="When the built-ins are not enough, write your own; when preview is not allowed, hide it in the portal and block it at the API")
    y += 100
    _, yc = chain(cv, 0, y, W, [
        ("Open Policy > Authoring > Definitions", "Azure portal, then + Policy definition"),
        ("Pick the location", "a subscription or management group; category such as AI Governance"),
        ("Paste the JSON rule", "the if and then rule, with parameters"),
        ("Assign it with parameters", "Resource Policy Contributor is the least-privilege role; Owner also works"),
        ("Validate", "a blocked request returns RequestDisallowedByPolicy; evaluation takes up to 30 min"),
    ], theme="grape", gap=56)
    c1 = Card(SPAN(2), "Why a custom policy", [
        "Block unauthorised creation of Foundry accounts, projects or connections",
        "Constrain what accounts and projects may declare in their capability settings",
        "Enforce tags",
        "Allow only approved integrations",
    ], theme="grape", icon="policy", fill="hatch", title_size=21, body_size=16, src=src("custom"))
    c2 = Card(SPAN(2), "Scenarios the page lists", [
        "Only approved connection categories",
        "Deny connections that use API-key authentication",
        "Audit accounts without valid agent capability settings: VNet subnet ARM ID plus custom storage, for regulated Agent Service",
        "Deny account kinds that lack full Foundry capabilities",
    ], theme="grape", icon="compliance", fill="hatch", title_size=21, body_size=16, src=src("custom"))
    c3 = Card(SPAN(2), "Worked example and samples", [
        "Example: deny connections whose category is not in the allowedCategories parameter",
        "It targets Microsoft.CognitiveServices/accounts/connections and .../accounts/projects/connections; the default allowed category is BingLLMSearch",
        "Force an evaluation with az policy state trigger-scan --resource-group <rg>",
        "Samples: microsoft-foundry/foundry-samples, folder infrastructure/infrastructure-setup-bicep/05-custom-policy-definitions",
    ], theme="grape", icon="github", fill="hatch", title_size=21, body_size=16, src=src("custom"))
    _, yb = row(cv, 0, yc + 40, [c1, c2, c3], gap=GUT)
    yb += 60

    # disable preview features ------------------------------------------------------------------
    t_app = Table([("Approach", 190), ("How", 520), ("Scope", 330), ("Effect", 616)], [
        [("Azure tag", "orange"), "Tag key AZML_DISABLE_PREVIEW_FEATURE with value true (exact, case-sensitive). Roles: Contributor or Tag Contributor",
         "Subscription, resource group or Foundry resource",
         "Hides preview surfaces in both the new and classic portals: no PREVIEW labels in the new portal, the Preview-features tool is disabled in classic. Remove the tag and preview reappears within minutes. Portal-level only"],
        [("Custom RBAC role", "red"), "Role JSON with notDataActions (notActions for Tracing); create it with az role definition create, then assign it",
         "Any assignable scope you choose", "Blocks at the API level"],
    ], theme="orange", size=14, head_size=15, title="Disable preview features: two approaches", title_size=22)
    t_app.place(cv, 0, yb)
    t_areas = Table([("Preview area", 250), ("Permission paths blocked (under Microsoft.CognitiveServices/accounts/)", 1406)], [
        ["Agent Service", "AIServices/agents/*"],
        ["Content Understanding", "MultiModalIntelligence/* (analyzers, classifiers, batchAnalysisJobs, labelingProjects)"],
        ["Fine-tuning", "OpenAI/fine-tunes/*, files/*, uploads/*, stored-completions/*, evals/*, models/* (plus 1p-jobs/* for RLHF)"],
        ["Evaluations", "AIServices/evaluations/*"],
        ["Content Safety", "ContentSafety/*"],
        ["Tracing", "Control-plane Microsoft.Insights reads (alertRules, diagnosticSettings, logDefinitions, metricdefinitions, metrics), listed in notActions"],
    ], theme="red", size=14, head_size=15, title="Blockable preview areas and the paths that block them", title_size=22)
    t_areas.place(cv, X(3), yb)
    yc = max(t_app.bottom, t_areas.bottom) + 40
    _, yd = chain(cv, 0, yc, SPAN(4), [
        ("Tag the subscription", "AZML_DISABLE_PREVIEW_FEATURE = true"),
        ("Verify both portals", "new: no PREVIEW labels; classic: Preview-features tool disabled"),
        ("Add the custom role", "notDataActions for API-level blocking"),
        ("Re-enable later", "remove the tag and the role"),
    ], theme="orange", gap=56)
    n = Note(SPAN(2), "Tags hide preview in the portals only; RBAC blocks at the API. The general-availability page tells you to define an organization policy for "
             "GA-only production and to cross-check its feature table.", kind="info", title="Suppress preview in production", src=src("preview", "ga"))
    n.place(cv, X(4), yc)
    return max(yd, n.bottom)


# ============================================================================================== 5. rbac elevated tasks
def rbac_tasks(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Control, where it is enforced, who owns it: the minimum role for each admin task", size=34,
                   sub="Foundry User builds and runs; admin work needs an elevated role. Role changes propagate in up to 5 min.")
    y += 100
    t = Table([("Control or task", 500), ("Where it is enforced", 560), ("Who owns it: minimum role (scope)", 1164)], [
        [("Create a Foundry resource or project", "red"), "Azure RBAC: the resource group for the resource, the Foundry resource for a project", "Contributor, Foundry Account Owner or Foundry Owner"],
        [("Assign roles", "red"), "Azure RBAC at any scope", "Owner or User Access Administrator. Foundry Account Owner and Foundry Project Manager can conditionally assign Foundry User only"],
        [("Deploy a model, including provisioned", "red"), "L3 Foundry resource, evaluated as an L5 deployment", "Foundry Account Owner at the resource. Marketplace models: Contributor on the subscription (creates billing agreements). Fireworks: Foundry Owner plus Contributor on the subscription"],
        [("Fine-tune", "red"), "L3 Foundry resource", "Foundry Owner, or Foundry User plus Foundry Account Owner: it creates training jobs that consume compute and storage"],
        [("View, edit or request quota", "red"), "L1 subscription x region x model; Manage > Quota", "Foundry Account Owner to view and edit; Contributor to request an increase; Cognitive Services Usages Reader to view at subscription scope"],
        [("Create guardrails or blocklists", "red"), "L3 Foundry resource", "Foundry Account Owner or higher"],
        [("Guardrail policies, model deployment policies, custom policies", "red"), "L1 and L2 Azure Policy assignments (management group, subscription or resource group)", "Owner or Resource Policy Contributor"],
        [("Third-party guardrails", "red"), "Subscription scope, plus a Key Vault", "Owner on the subscription plus Key Vault Administrator"],
        [("Token limits or MCP governance through the AI gateway", "red"), "L4 project x deployment, through the AI gateway", "API Management Service Contributor or Owner, on the API Management instance"],
        [("Enable the AI gateway and link it to Foundry", "red"), "L3 Foundry resource (the AI Gateway link)", "Contributor or Owner (resource group or subscription) to enable; Foundry Account Owner or Foundry Owner to link"],
        [("Defender for Cloud, Purview, diagnostic settings", "red"), "L1 subscription (Defender plan, Purview toggle); L3 resource (diagnostic settings)", "Security Admin or Owner on the subscription for Defender; Foundry Account Owner for the Purview toggle; Monitoring Contributor for diagnostic settings"],
        [("Manage agent availability", "red"), "L0 tenant: Entra admin center or Microsoft 365 admin center", "Entra AI Administrator or Global Administrator"],
        [("Publish an agent", "red"), "L6 agent", "Foundry Project Manager, at Foundry resource scope"],
        [("Network: private endpoint, VNet, DNS, NSP, customer-managed keys", "red"), "L3 Foundry resource", "Contributor or Owner, plus Network Contributor, Private DNS Zone Contributor or the Key Vault roles"],
        [("Tags", "red"), "L1 to L3: subscription, resource group or Foundry resource", "Contributor or Tag Contributor"],
    ], theme="red", size=15, head_size=16, title="Control to where it is enforced to who owns it", title_size=22)
    t.place(cv, 0, y)
    r1 = Card(SPAN(2), "Roles at a glance", [
        "Foundry User, at resource or project scope: build agents, run inference, most features",
        "Owner or Contributor alone cannot create or update agents: data-plane Foundry roles are needed",
        "Foundry Agent Consumer: least privilege, interact with agent endpoints only",
        "A small team: you as Owner on the resource group, each developer as Foundry User at resource scope, and Foundry Account Owner for whoever deploys models, sets quotas and creates guardrails or blocklists",
    ], theme="red", icon="managed-identity", fill="hatch", title_size=21, body_size=16, src=src("admin", "rbac"))
    r1.place(cv, X(4), y)
    n1 = Note(SPAN(2), "Publish gives the agent a new Entra identity; permissions held by the project's shared identity do not transfer.", kind="gotcha",
              title="Publishing changes identity", src=src("rbac"))
    n1.place(cv, X(4), r1.bottom + 24)
    n2 = Note(SPAN(2), "Foundry User, Foundry Owner, Foundry Account Owner and Foundry Project Manager were Azure AI User, Owner, Account Owner and Project Manager; role IDs "
              "are unchanged. One compliance page still prints Azure AI Account Owner. Do not use the Cognitive Services roles (except Cognitive Services Usages Reader) "
              "or the Azure AI Developer role for Foundry work.", kind="warn", title="Renamed roles; roles to avoid", src=src("rbac"))
    n2.place(cv, X(4), n1.bottom + 24)
    return max(t.bottom, n2.bottom)


# ============================================================================================== 6. gotchas + related
def gotchas(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6  Gotchas to remember", size=34)
    y += 70
    notes = [
        Note(CW, "Asset-ID prefix matching and case-sensitive publisher names are the most common cause. End an asset ID with / to pin one model, or give the full versioned ID.",
             kind="gotcha", title="Approved model blocked?", src=src("mdp")),
        Note(CW, "The content-filter, tool allow / deny and model-router definition groups are preview, and Operate > Compliance itself is preview (as of 2026-11-03). Expect names and behaviour to change.",
             kind="preview", title="Preview is moving", src=src("polref", "ga")),
        Note(CW, "Guardrails apply to agents built in Foundry Agent Service, not to other agents registered in the Control Plane. An agent's own guardrail fully overrides its model's guardrail.",
             kind="gotcha", title="Guardrails and non-Foundry agents", src=src("guardrails")),
        Note(CW, "Foundry-specific Azure Policy aliases live under Microsoft.CognitiveServices, shared with Azure OpenAI, Speech, Vision and Language: existing custom policies and RBAC actions keep working.",
             kind="info", title="Shared namespace", src=src("arch")),
        Note(CW, "Whether a developer with only Foundry User can save the guardrail changes that Fix now opens is not stated. Creating guardrails needs Foundry Account Owner or higher.",
             kind="warn", title="Not stated in the docs", src=src("admin")),
        Note(CW, "Foundry pages show both Audit and Deny but do not prescribe a rollout order. Audit then Deny is standard Azure Policy practice and is how the flow above is ordered.",
             kind="tip", title="Our ordering", src=src("mdp")),
    ]
    _, b = row(cv, 0, y, notes, gap=GUT)
    return b


def related(cv: Canvas, y: float) -> float:
    cv.text(0, y, "See also in this gallery:", size=18, color="#343a40")
    items = [("Governance, policy and compliance, part 2: evidence, residency, Azure Government", "grape"),
             ("Foundry Control Plane", "grape"), ("AI gateway and token limits", "grape"), ("Microsoft Foundry Cost Structure", "yellow"),
             ("Foundry in an Azure landing zone, part 2: policy placement in the management-group hierarchy", "indigo"),
             ("Foundry roles, scopes and least-privilege assignments", "red"), ("Guardrails and controls", "pink")]
    f = ChipFlow([Chip(t, theme=th, size=16, fill="soft") for t, th in items], W - 260, gap=12).place(cv, 250, y - 4)
    return max(y + 28, f.y + f.h)


# ============================================================================================== sources
def sources_panel(cv: Canvas, y: float) -> float:
    items = [S[k] for k in ("mdp", "custom", "router", "preview", "admin", "rbac", "polref", "baseline", "quickstart", "compliance",
                            "govern", "agentid", "ga", "plan", "dtypes", "instant")]
    sources(cv, 0, y, items, w=W, cols=4)
    return y


# ============================================================================================== build
def build(cv: Canvas) -> None:
    y = title_and_key(cv) + 30
    y = summary_strip(cv, y) + 54
    section_header(cv, 0, y, "1  The governance layer cake: which control sits at which layer", size=34,
                   sub="Assignments apply to everything inside their scope. Each band lists what you can control, the mode it runs in and the role you need.")
    y = layer_cake(cv, y + 96) + 60
    y = clock(cv, y) + 50
    y = evidence_teaser(cv, y) + 70
    y = policy_index(cv, y) + 70
    y = deployment_gate(cv, y) + 70
    y = custom_and_preview(cv, y) + 70
    y = rbac_tasks(cv, y) + 70
    y = gotchas(cv, y) + 50
    y = related(cv, y) + 40
    sources_panel(cv, y)
