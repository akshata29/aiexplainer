"""Foundry authentication and authorization map - identities, credentials, token audiences, planes and request flows."""
from generator.xd import *

META = dict(
    id="authn-authz-overview", title="Authentication and authorization map", section="5", order=1,
    description="Who proves what to whom: identity types, Entra ID vs API keys, token audiences, control vs data plane, "
                "connections and secrets, plus five numbered request-flow sequences.",
    tags=["authentication", "entra", "rbac", "tokens", "managed-identity", "api-keys"],
)

W = 3360                      # canvas width
G = 60                        # gutter
C3 = (W - 2 * G) / 3          # three-column grid (1080)
XB, XC = C3 + G, 2 * (C3 + G)  # x of columns 2 and 3


def L(path, **kw):
    return learn(path, **kw)


def cite(cv, x, y, label, url, size=12):
    """Clickable 'Learn: ...' line (for tables, which have no src= parameter). Returns the bottom y."""
    t = cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)
    return t.bottom


def src_cell(label, url):
    return dict(text=label, link=url, color=LINK)


def hop(cv, a, b, ta, tb, n, text, theme, *, label_w=430, a_side="right", b_side="left", dash="solid", size=15):
    """Horizontal credential arrow a -> b with a numbered badge and the credential written above it."""
    th = THEMES[theme]
    connect(cv, a, b, a_side=a_side, b_side=b_side, ta=ta, tb=tb, color=th.stroke, sw=3, dash=dash, gap=4)
    (x1, y), (x2, _) = a.pt(a_side, ta), b.pt(b_side, tb)
    lines = wrap_text(text, label_w, size)
    h = len(lines) * size * 1.25
    ty = y - 14 - h
    numbered(cv, x1 + 24, ty + 12, n, theme=theme)
    cv.text(x1 + 46, ty, "\n".join(lines), size=size, color=INK)


def colhead(cv, x, y, text, w=C3):
    return section_header(cv, x, y, text, size=28, w=w)[1]


# ====================================================================== 0. title + stamps
def title_and_stamps(cv):
    right, bottom = title_block(cv, 0, 0, "Foundry authentication and authorization map",
                                "Who proves what to whom: identities, credentials, token audiences and the two RBAC planes",
                                icon="foundry", w=W)
    y = bottom + 40
    sw = (W - 3 * 40) / 4
    stamps = [
        Box(sw, "Entra ID = production", sub="API keys = rapid prototyping and isolated test environments only",
            theme="green", size=24, sub_size=16, h=104, sw=3),
        Box(sw, "Agents, Evaluations and Toolbox: Entra only", sub="These features have no API-key support",
            theme="red", size=24, sub_size=16, h=104, sw=3),
        Box(sw, "Agent endpoints do not accept API keys", sub="Callers come with Entra tokens, or through an Azure Bot Service channel",
            theme="red", size=24, sub_size=16, h=104, sw=3),
        Box(sw, "Owner and Contributor are not data-plane roles", sub="Broad ARM rights, but no Foundry data-plane rights",
            theme="orange", size=24, sub_size=16, h=104, sw=3),
    ]
    row(cv, 0, y, stamps, gap=40)
    return y + 104


# ====================================================================== 1. hero: request path
def hero(cv, y):
    _, b = section_header(cv, 0, y, "1  Who authenticates to what along one agent request", size=34,
                          sub="Callers -> endpoints -> agent runtime -> model, tools, data and telemetry. Numbers match the flow diagrams in section 5; "
                              "B1-B3 are the three independent boundaries.")
    rgap = 26
    hub_x, hub_pad, lw_, rw_ = 900, 24, 460, 380
    hub_w = hub_pad + lw_ + 60 + rw_ + hub_pad
    tx = hub_x + hub_w + 470
    tw = W - tx

    # ---- measure every card first so the four rows share one height
    ep = Card(lw_, "Project endpoint", [
        "https://<resource>.services.ai.azure.com/api/projects/<project>",
        "AuthZ: Azure RBAC dataActions at project or resource scope (Foundry User)",
    ], theme="blue", icon="foundry", src=[("Authentication and authorization", L("concepts/authentication-authorization-foundry"))])
    ag = Card(lw_, "Agent endpoint (stable, per agent)", [
        ".../agents/<agent>/endpoint/protocols/openai/responses?api-version=v1",
        "Also .../activityProtocol (the Teams / M365 route)",
        "AuthZ: authorization_schemes - AzureRbac (Foundry Agent Consumer), AgentBlueprint (preview), BotService*",
        "! API keys are not accepted",
    ], theme="green", icon="agent", src=[("Agent endpoint authorization", L("agents/concepts/agent-endpoint-authorization"))])
    cp = Card(lw_, "Control plane (ARM)", [
        "https://management.azure.com",
        "AuthZ: Azure RBAC actions (Owner, Contributor, Foundry Account Owner ...)",
        "! Owner and Contributor stop here: no Foundry data actions",
    ], theme="grape", icon="resource-group")
    rt = Card(rw_, "Agent runtime", [
        "Prompt agent or hosted-agent code",
        "Prompt agents act as the project managed identity (infrastructure operations; not available to hosted-agent code)",
        "Hosted code runs as its own agent identity, which starts with no permissions",
        "The caller is derived from the Entra token (per-user session isolation for hosted agents)",
    ], theme="green", icon="container-apps", src=[("Identity and access overview", L("agents/concepts/identity-access-overview"))])
    t_model = Card(tw, "Model deployment", [
        "Prompt agents: the project proxies to the account-level deployment as the project managed identity (Foundry User at the Foundry account scope). "
        "Hosted code: its agent identity, with implicit access to project-endpoint inference",
        "Direct calls to https://{account}.cognitiveservices.azure.com need an account-scope role: Cognitive Services OpenAI User (OpenAI only) or Foundry User",
    ], theme="blue", icon="openai", src=[("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions"))])
    t_tool = Card(tw, "Tools: MCP, A2A, OpenAPI, ...", [
        "The credential is produced server-side from the project connection's authType; the agent never sees the secret",
        "The tool server or downstream service makes its own authorization decision: Azure RBAC, service data-plane roles, app roles or ACLs",
    ], theme="orange", icon="mcp", src=[("Tool authentication", L("agents/how-to/tools/tool-authentication"))])
    t_data = Card(tw, "Data: AI Search, Cosmos DB, Storage", [
        "Standard agent setup: the project managed identity holds data-plane roles on each resource",
        "Cosmos DB Built-in Data Contributor, Search Index Data Contributor + Search Service Contributor, Storage Blob Data Contributor / Owner",
        "A missing role shows up as a 403 at runtime",
    ], theme="cyan", icon="storage", src=[("Standard agent setup", L("agents/concepts/standard-agent-setup"))])
    t_ai = Card(tw, "Application Insights", [
        "Server-side spans use the project managed identity; hosted-agent code spans use the agent identity",
        "Both need Monitoring Metrics Publisher (local auth disabled on App Insights)",
    ], theme="violet", icon="app-insights", badge="preview",
        src=[("Trace ingestion with Entra", L("observability/how-to/trace-ingestion-entra-authentication"))])
    targets = [t_model, t_tool, t_data, t_ai]
    rowh = max([c.h for c in (ep, cp, *targets)] + [(ag.h - rgap) / 2, (rt.h - 3 * rgap) / 4, 150])

    # ---------------------------------------------------------------- hub (middle)
    with cv.panel(hub_x, b + 30, title="Foundry resource and project",
                  sub="Microsoft.CognitiveServices/accounts  |  where each request is authorized", theme="blue", style="solid",
                  fill="soft", pad=hub_pad, title_size=28, sub_size=16) as hub:
        top = hub.iy
        ep.place(cv, hub.ix, top, h=rowh)
        ag.place(cv, hub.ix, top + rowh + rgap, h=2 * rowh + rgap)
        cp.place(cv, hub.ix, top + 3 * (rowh + rgap), h=rowh)
        rt.place(cv, hub.ix + lw_ + 60, top, h=4 * rowh + 3 * rgap)
        for c in (ep, ag):
            connect(cv, c, rt, a_side="right", b_side="left", ta=0.5, tb=(c.cy - rt.y) / rt.h, sw=2, color="#495057", gap=4)

    # ---------------------------------------------------------------- callers (left)
    cw = 470
    ys = [top + i * (rowh + rgap) + rowh / 2 for i in range(4)]
    kw = dict(theme="gray", icon_pos="left", fill="hatch", h=150, size=20, sub_size=15)
    c_dev = Box(cw, "Developer", sub="SDK, CLI, VS Code: a user principal, or a CI service principal", icon="users", **kw)
    c_app = Box(cw, "App or end user", sub="Delegated user token, or app-only workload identity / certificate", icon="app", **kw)
    c_bot = Box(cw, "Teams / M365 channel", sub="Azure Bot Service validates the channel's own token", icon="teams", **kw)
    c_adm = Box(cw, "Admin or pipeline", sub="Azure portal, Azure CLI, Bicep, Terraform", icon="automation", **kw)
    for c, yy in zip((c_dev, c_app, c_bot, c_adm), ys):
        c.place(cv, 0, yy - 75)

    hop(cv, c_dev, ep, 0.5, (ys[0] - ep.y) / ep.h, 1, "Entra token, scope https://ai.azure.com/.default", "blue")
    hop(cv, c_app, ag, 0.5, (ys[1] - ag.y) / ag.h, 2, "Entra token for https://ai.azure.com (preview: the agent-blueprint audience)", "blue")
    hop(cv, c_bot, ag, 0.5, (ys[2] - ag.y) / ag.h, 6, "Channel call through Azure Bot Service to the activityProtocol route", "gray")
    hop(cv, c_adm, cp, 0.5, (ys[3] - cp.y) / cp.h, "B1", "Entra token for Azure Resource Manager (https://management.azure.com)", "grape")

    # ---------------------------------------------------------------- targets (right)
    for i, c in enumerate(targets):
        c.place(cv, tx, top + i * (rowh + rgap), h=rowh)
    labels = [
        (3, "Project managed identity (prompt agents), or the agent identity (hosted-agent code)", "red"),
        (4, "Per-connection authType: stored key, project MI, agent identity, per-user OAuth or user token", "orange"),
        (5, "Project managed identity + data-plane roles on the resource", "red"),
        (7, "Project MI (+ the agent identity for hosted code)", "violet"),
    ]
    for c, (n, text, th) in zip(targets, labels):
        hop(cv, rt, c, (c.y + c.h / 2 - rt.y) / rt.h, 0.5, n, text, th, label_w=440)

    bottom = max(hub.bottom, t_ai.bottom)
    # boundary bands + note + legend
    by = bottom + 34
    b2 = Box(hub.x - 40, "B2  Caller -> agent endpoint: the endpoint's authorization scheme decides", theme="blue", fill="soft",
             size=19, h=64, dash="dashed")
    b2.place(cv, 0, by)
    b3 = Box(W - (hub.right + 40), "B3  Agent -> tool or resource: the downstream service decides, with the credential you configured",
             theme="red", fill="soft", size=19, h=64, dash="dashed")
    b3.place(cv, hub.right + 40, by)
    n = Note(W, "B1 = developer or admin -> Foundry management (Azure RBAC). B2 = caller -> agent endpoint. B3 = agent -> downstream tool or resource. "
                "A principal that can manage an agent is not automatically allowed to call it, and an agent's access to a downstream resource does not "
                "grant callers access to the agent. Support differs per tool, protocol and channel - do not assume every tool supports every method. "
                "Deep dive: the agent-identity-and-delegation canvas.",
             kind="key", title="Three independent boundaries: permissions never carry across them",
             src=[("Identity and access overview", L("agents/concepts/identity-access-overview"))])
    n.place(cv, 0, by + 64 + 26)
    legend(cv, 0, n.bottom + 22, [("Caller's Entra token", "blue"), ("Managed identity / agent identity", "red"),
                                  ("Connection credential (varies)", "orange"), ("Telemetry export", "violet"),
                                  ("Channel (Bot Service)", "gray"), ("Control plane (ARM)", "grape")])
    return n.bottom + 70


# ====================================================================== 2. planes, identities, credentials
def planes_identities_credentials(cv, y):
    _, b = section_header(cv, 0, y, "2  Planes, identities and credentials", size=34,
                          sub="Which API surface you call, who you are, and what you present")
    y0 = b + 34

    # ---------------------------------------------------------------- col A: control vs data plane
    hb = colhead(cv, 0, y0, "Control plane vs data plane")
    t_plane = Table([("", 150), ("Control plane (resource management)", 465), ("Data plane (runtime)", 465)], [
        ["Scope in Foundry", "Resources, projects, networking, encryption, connections",
         "Model inference, agent interactions, evaluation jobs, content-safety calls"],
        ["Typical operations", "Create or delete resources, assign roles, rotate keys, set up Private Link",
         "Chat completions, embeddings, start fine-tune jobs, send agent messages, analyzer and classifier operations"],
        ["Tools", "Azure portal, Azure CLI, ARM, Bicep, Terraform", "SDKs, REST APIs, Foundry portal playground"],
        ["Authorization surface", ("Azure RBAC actions", "blue"), ("Azure RBAC dataActions", "green")],
        ["Foundry examples", "Create a Foundry resource or project; capability settings; model deployment; account and project connections",
         "Build agents; run evaluations; tracing and monitoring; fine-tuning"],
        ["Endpoint / token", "https://management.azure.com (ARM REST; token audience not separately stated)",
         "Token scope https://ai.azure.com/.default"],
    ], w=C3, theme="blue", size=14, head_size=15, first_col_theme="gray")
    t_plane.place(cv, 0, hb + 14)
    cy = cite(cv, 0, t_plane.bottom + 6, "Authentication and authorization in Foundry", L("concepts/authentication-authorization-foundry"))
    n1 = Note(C3, "Owner and Contributor have broad ARM rights but no Foundry data-plane rights: \"a user can manage resources but still need data plane roles "
                  "to chat with an agent\". Admin access is not developer access.",
              kind="gotcha", title="Management is not usage",
              src=[("Plan your Foundry rollout", L("concepts/planning")), ("Configure key-less authentication", L("foundry-models/how-to/configure-entra-id"))])
    n1.place(cv, 0, cy + 22)
    n2 = Note(C3, "Starting a fine-tune job is data plane; deploying the fine-tuned model is control plane. Foundry Owner is the only built-in role with both, "
                  "or pair Foundry User (data) with Foundry Account Owner (control).",
              kind="info", title="Fine-tuning needs both planes", src=[("RBAC for Foundry", L("concepts/rbac-foundry"))])
    n2.place(cv, 0, n1.bottom + 20)
    bottom_a = n2.bottom

    # ---------------------------------------------------------------- col B: identity types
    colhead(cv, XB, y0, "Identity types")
    cw = (C3 - 24) / 2
    cards = [
        Card(cw, "User principal", ["An individual Microsoft Entra user", "Gets Foundry roles directly or through Entra groups"],
             theme="gray", icon="users"),
        Card(cw, "Service principal (app registration)", ["Application identity with a client secret or certificate",
                                                          "CI/CD and middle tiers: prefer a certificate or federated credential over a secret"],
             theme="red", icon="app-registrations"),
        Card(cw, "Managed identity: system-assigned", ["Bound to a resource and managed by the platform",
                                                       "The Foundry resource (account) has one",
                                                       "The project managed identity is the runtime identity for connected resources"],
             theme="red", icon="managed-identity"),
        Card(cw, "Managed identity: user-assigned", ["Standalone; attachable to many resources",
                                                     "For a project it can only be set at project creation",
                                                     "Switching a project between system- and user-assigned later is unsupported"],
             theme="red", icon="managed-identity", src=[("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions"))]),
        Card(cw, "Agent identity (Entra Agent ID)", ["A special service principal under an agent identity blueprint, created automatically for each agent",
                                                    "Starts with no permissions until you grant them",
                                                    "Legacy agents share a project-level identity"],
             theme="green", icon="agent", src=[("Agent identity", L("agents/concepts/agent-identity"))]),
        Card(cw, "Account-level shared identity", ["Some setups also rely on the account-level shared identity (admin guide)",
                                                   "Use the identity name that matches the scenario: the project managed identity and the account identity are not interchangeable"],
             theme="red", icon="foundry", dash="dashed", src=[("Administrator guide", L("concepts/administrator-guide"))]),
    ]
    _, gb = grid(cv, XB, y0 + 62, cards, 2, gap_x=24, gap_y=22)
    cy = cite(cv, XB, gb + 8, "Authentication and authorization in Foundry (identity types)", L("concepts/authentication-authorization-foundry"))
    n3 = Note(C3, "A new role assignment can take about 5 minutes to take effect (up to 30 minutes for the Key Vault role). "
                  "Group membership changes propagate immediately.", kind="tip", title="Propagation delay")
    n3.place(cv, XB, cy + 22)
    bottom_b = n3.bottom

    # ---------------------------------------------------------------- col C: Entra ID vs API key
    colhead(cv, XC, y0, "Entra ID vs API key")
    t_cred = Table([("", 130), ("Microsoft Entra ID (keyless)", 475), ("API key", 475)], [
        ["Mechanism", "OAuth 2.0 bearer token; documented scope https://ai.azure.com/.default",
         "Static secret scoped to one Foundry resource (two keys); sent in the api-key header"],
        ["Use for", "Production; Conditional Access, MFA, just-in-time access; least-privilege RBAC; managed identity",
         "Rapid prototyping; isolated test environments where single-secret rotation is acceptable"],
        ["Strengths", "Per-principal audit, controllable token lifetime, automatic secret hygiene, managed identities for services",
         "Simple, language agnostic, no token acquisition"],
        ["Limits", "Needs a custom subdomain on the resource (the regional endpoint will not work); RBAC learning curve",
         "No user identity, hard to scope, hard to audit; \"not recommended by Microsoft\" for enterprise production"],
        ["Revocation", "Remove the role or disable the principal (short token lifetime applies)", "Rotate the key"],
    ], w=C3, theme="green", size=14, head_size=15, first_col_theme="gray")
    t_cred.place(cv, XC, y0 + 62)
    cy = cite(cv, XC, t_cred.bottom + 6, "Authentication and authorization in Foundry", L("concepts/authentication-authorization-foundry"))
    n4 = Note(C3, "Replace DefaultAzureCredential with a deterministic credential (ManagedIdentityCredential or a pared-down ChainedTokenCredential) "
                  "and configure a system- or user-assigned managed identity on the compute.", kind="tip",
              title="Production credential guidance", src=[("Configure key-less authentication", L("foundry-models/how-to/configure-entra-id"))])
    n4.place(cv, XC, cy + 22)
    bottom_c = n4.bottom
    return max(bottom_a, bottom_b, bottom_c) + 70


# ====================================================================== 2b. features, disable local auth, rotate keys
def step_flow(cv, x, y, w, steps, gap=34):
    """Numbered cards stacked top -> bottom with arrows between them. steps: (title, bullets, theme, src)."""
    prev, cur = None, y
    for i, (title, body, theme, src) in enumerate(steps):
        c = Card(w - 64, title, body, theme=theme, src=src, title_size=19, body_size=15)
        c.place(cv, x + 64, cur)
        numbered(cv, x + 26, cur + 28, i + 1, theme=theme, d=36, size=19)
        if prev is not None:
            connect(cv, prev, c, a_side="bottom", b_side="top", gap=3, color="#495057", sw=2)
        prev, cur = c, c.bottom + gap
    return prev.bottom


def rotation_grid(cv, x, y, w):
    labw, gap = 90, 8
    colw = (w - labw - 5 * gap) / 5
    steps = [("Move all clients to key 1", "clients", "idle"), ("Regenerate key 2", "clients", "regenerated"),
             ("Move clients to key 2", "idle", "clients"), ("Regenerate key 1", "regenerated", "clients"),
             ("Move clients to the new key 1", "clients", "idle")]
    th = {"clients": "green", "idle": "gray", "regenerated": "yellow"}
    hy, hh, ch = y + 20, 112, 64
    for i, (title, k1, k2) in enumerate(steps):
        bx = x + labw + gap + i * (colw + gap)
        Box(colw, title, theme="gray", fill="soft", size=15, h=hh, pad=8).place(cv, bx, hy)
        numbered(cv, bx + 16, hy, i + 1, theme="gray", d=30, size=17)
        for r, state in enumerate((k1, k2)):
            Box(colw, state, theme=th[state], fill="solid", size=16, h=ch,
                dash="dashed" if state == "idle" else "solid").place(cv, bx, hy + hh + 14 + r * (ch + 12))
    for r, name in enumerate(("Key 1", "Key 2")):
        Box(labw, name, theme="ink", fill="soft", size=19, h=ch).place(cv, x, hy + hh + 14 + r * (ch + 12))
    return hy + hh + 14 + 2 * ch + 12


def credential_row(cv, y):
    # ---------------------------------------------------------------- A: feature support
    hb = colhead(cv, 0, y, "Which features accept which credential")
    R = lambda t: (t, "red")
    rows = [
        ["Basic model inference (chat, embeddings)", CHECK, CHECK],
        ["Fine-tuning operations - Entra ID adds per-principal audit", CHECK, CHECK],
        [R("Agents service - use Entra ID for managed identity tool access"), CROSS, CHECK],
        [R("Evaluations"), CROSS, CHECK],
        [R("Toolbox - use Entra ID for managed identity tool access"), CROSS, CHECK],
        ["Content safety analyze calls - use RBAC to limit high-risk operations", CHECK, CHECK],
        ["Batch analysis jobs (Content Understanding) - Entra ID recommended at scale", CHECK, CHECK],
        ["Portal playground - runs in project connection mode", CHECK, CHECK],
        ["Network isolation with Private Link - Entra ID adds Conditional Access", CHECK, CHECK],
        ["Least privilege with built-in and custom roles - keys are all-or-nothing per resource", CROSS, CHECK],
        ["Managed identity, system- or user-assigned - enables secret-less auth", CROSS, CHECK],
        ["Per-request user attribution - the token carries tenant and object IDs", CROSS, CHECK],
        [("Assistants API - page says deprecated, retires August 26, 2026; that date has passed as of 2026-11-03, so verify its status", "yellow"), CHECK, CHECK],
        ["Batch inferencing", CHECK, CHECK],
    ]
    t = Table([("Capability or feature", 760), ("API key", 160), ("Entra ID", 160)], rows, w=C3, theme="green", size=14,
              head_size=15, align=["left", "center", "center"])
    t.place(cv, 0, hb + 14)
    cy = cite(cv, 0, t.bottom + 6, "Authentication and authorization in Foundry (feature support matrix)",
              L("concepts/authentication-authorization-foundry"))
    n5 = Note(C3, "The Foundry User role definition includes accounts/listkeys/action and all Microsoft.CognitiveServices/* data actions. "
                  "With local auth enabled a Foundry User can fetch keys - disable local auth to enforce Entra-only.", kind="gotcha",
              title="Roles can reach the keys", src=[("Built-in roles: AI + machine learning", L("azure/role-based-access-control/built-in-roles/ai-machine-learning", base=""))])
    n5.place(cv, 0, cy + 22)
    n6 = Note(C3, "The Foundry security baseline page says local authentication to the data plane is \"not supported\", but it is built on MCSB v1.0 "
                  "(\"may contain outdated guidance\") and contradicts the API-key support in the authentication page. Prefer the authentication page.",
              kind="warn", title="Docs disagree: security baseline")
    n6.place(cv, 0, n5.bottom + 20)
    bottom_a = n6.bottom

    # ---------------------------------------------------------------- B: disable local auth
    colhead(cv, XB, y, "Disable local (key) authentication")
    steps = [
        ("Enforce it with Azure Policy", [
            "Azure AI Services resources should have key access disabled (disable local authentication): Audit, Deny or Disabled, at subscription or resource group scope",
            "DeployIfNotExists and Modify variants exist: Configure Azure AI Services resources to disable local key access; Configure Cognitive Services accounts to disable local authentication methods",
        ], "grape", [("Policy reference", L("azure/ai-services/policy-reference", base=""))]),
        ("Or set it on the resource", [
            "Bicep / ARM: disableLocalAuth: true. PowerShell: Set-AzCognitiveServicesAccount ... -DisableLocalAuth $true",
        ], "grape", [("Disable local authentication", L("azure/ai-services/disable-local-auth", base=""))]),
        ("Wait: it is not instant", [
            "The control-plane change is immediate, but the shared gateway can keep accepting old keys until its cache refreshes",
            "Typically a few minutes; it can take up to several hours. Re-enabling has the same delay",
        ], "orange", []),
        ("Verify with an old key", [
            "A data-plane request with the old key must return HTTP 401: Access denied due to invalid subscription key or wrong API endpoint",
        ], "green", []),
        ("Revoke existing keys", [
            "Azure portal > Keys and Endpoint > regenerate Key 1 and Key 2. Remove key auth only after all callers use tokens",
        ], "red", [("Authentication and authorization in Foundry", L("concepts/authentication-authorization-foundry"))]),
    ]
    sb = step_flow(cv, XB, y + 62, C3, steps, gap=28)
    nw = Note(C3, "The policy text warns that Azure OpenAI Studio (dev/test) needs key access, so disabling local auth can break that experience.",
              kind="warn", title="Dev/test tooling")
    nw.place(cv, XB, sb + 24)
    bottom_b = nw.bottom

    # ---------------------------------------------------------------- C: rotate keys
    colhead(cv, XC, y, "Rotate keys without downtime")
    gb = rotation_grid(cv, XC, y + 62, C3)
    legend(cv, XC, gb + 18, [("clients use this key", "green"), ("regenerated", "yellow"), ("idle", "gray")])
    n7 = Note(C3, "Once a key is regenerated, the older version of that key stops working immediately and clients still using it get 401 access denied - "
                  "that is why all clients move to the other key first. Check logs that users swapped keys before the next step.",
              kind="gotcha", title="A regenerated key stops working immediately",
              src=[("Rotate API keys", L("azure/ai-services/rotate-keys", base=""))])
    n7.place(cv, XC, gb + 62)
    n8 = Note(C3, "Each resource has two API keys to enable secret rotation. Rotating keys is the revocation path for API keys; for Entra ID you remove the role "
                  "or disable the principal.", kind="info", title="Two keys per resource")
    n8.place(cv, XC, n7.bottom + 20)
    bottom_c = n8.bottom
    return max(bottom_a, bottom_b, bottom_c) + 70


# ====================================================================== 3. token audiences
def audiences(cv, y):
    _, b = section_header(cv, 0, y, "3  Token audiences and endpoints, exactly as documented", size=34,
                          sub="Foundry pages use https://ai.azure.com/.default as the primary Entra scope - one REST reference lists another (flagged)")
    y0 = b + 34
    lw = 2200
    A = lambda t: (t, "green")
    Y = lambda t: (t, "yellow")
    rows = [
        [A("Foundry data plane, project, agents"), "Token scope https://ai.azure.com/.default. CLI: az account get-access-token --resource https://ai.azure.com. "
         "Azure Government: https://ai.azure.us/.default", src_cell("Authentication and authorization", L("concepts/authentication-authorization-foundry"))],
        ["Foundry resource endpoint", "https://<resource>.services.ai.azure.com (example, list deployments: /openai/deployments?api-version=2024-10-21)",
         src_cell("Authentication and authorization", L("concepts/authentication-authorization-foundry"))],
        ["Project endpoint", "https://<resource>.services.ai.azure.com/api/projects/<project>", "Several Foundry how-to pages"],
        ["OpenAI-compatible (Responses and more)", "Base https://<resource>.openai.azure.com/openai/v1/ or https://<resource>.services.ai.azure.com/openai/v1/. "
         "Foundry docs use token scope https://ai.azure.com/.default", src_cell("Configure key-less authentication", L("foundry-models/how-to/configure-entra-id"))],
        [Y("Same OpenAI v1 REST reference (differs)"), "OAuth2 (implicit) scope listed as https://cognitiveservices.azure.com/.default; also two API-key schemes "
         "(the api-key header and the authorization header)", src_cell("REST reference: Responses", L("rest/api/microsoft-foundry/azureopenai/responses", base=""))],
        ["Agent endpoint (stable, per agent)", ".../api/projects/<p>/agents/<agent>/endpoint/protocols/openai/responses?api-version=v1 (also .../activityProtocol). "
         "AzureRbac accepts tokens whose audience is the Foundry resource https://ai.azure.com. AgentBlueprint (preview) accepts api://<agent-blueprint-client-id>/access_agent "
         "(delegated) or <audience>/.default (app-only)", src_cell("Agent endpoint authorization", L("agents/concepts/agent-endpoint-authorization"))],
        ["Account-level direct (not proxied by the project)", "https://{account}.cognitiveservices.azure.com needs an account-scope role: Foundry User or Cognitive Services OpenAI User",
         src_cell("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions"))],
        ["Foundry Models (MaaS) with Entra", "Role Cognitive Services User on the resource; custom-role data action Microsoft.CognitiveServices/accounts/MaaS/*; "
         "Bicep sample output https://<acct>.services.ai.azure.com/models", src_cell("Configure key-less authentication", L("foundry-models/how-to/configure-entra-id"))],
        ["ARM control plane", "https://management.azure.com (az rest and ARM REST examples; the audience is not separately stated)", "Foundry how-to pages (managed network and others)"],
        ["Hosted-agent token service", "REST parameter resource = the resource URI (for example https://storage.azure.com, not /.default); SDK scope = <resource>/.default; "
         "api-version=2019-08-01", src_cell("Hosted agent token service", L("agents/concepts/hosted-agent-token-service"))],
        ["Foundry MCP Server (preview)", "Token scoped https://mcp.ai.azure.com; delegated scope https://mcp.ai.azure.com/Foundry.Mcp.Tools; Entra app id "
         "fcdfa2de-b65b-4b54-9a1c-81c8a18282d9 (the target for Conditional Access)", src_cell("MCP security best practices", L("mcp/security-best-practices"))],
        ["Foundry IQ source authorization", "The agent requests https://search.azure.com/user_impersonation on behalf of the user (blueprint audience)",
         src_cell("User delegation", L("agents/concepts/user-delegation"))],
        ["Project-MI tool connection (example)", "--audience https://cognitiveservices.azure.com", src_cell("Tool authentication", L("agents/how-to/tools/tool-authentication"))],
        ["Foundry portal (ai.azure.com)", "Users sign in with Entra. The portal's first-party sign-in principal is \"Azure Machine Learning Services\", distinct from the "
         "\"Azure Machine Learning\" resource-provider app that Foundry's blueprint credential trusts. The playground runs in project connection mode; "
         "roles are managed under Manage > Project details > Users", src_cell("Agent identity", L("agents/concepts/agent-identity"))],
    ]
    t = Table([("Surface", 330), ("Endpoint / audience as documented", 1340), ("Source page", 530)], rows, w=lw, theme="blue", size=14, head_size=15)
    t.place(cv, 0, y0)
    rx, rw = lw + G, W - lw - G
    n1 = Note(rw, "Foundry concept and how-to pages use https://ai.azure.com/.default for Entra tokens, including the OpenAI-compatible /openai/v1 routes. "
                  "The Azure OpenAI v1 REST reference lists the OAuth2 scope https://cognitiveservices.azure.com/.default instead. "
                  "Treat ai.azure.com as primary and check the page you are following.", kind="warn", title="Docs disagree: which scope for OpenAI v1 calls?",
              src=[("REST reference: Responses", L("rest/api/microsoft-foundry/azureopenai/responses", base="")),
                   ("Configure key-less authentication", L("foundry-models/how-to/configure-entra-id"))])
    n1.place(cv, rx, y0)
    err = Card(rw, "Common authentication errors", [
        "401 Unauthorized: missing or expired token, wrong scope, or an invalid API key",
        "403 Forbidden: missing RBAC role assignment (for example Foundry User at resource or project scope)",
        "AADSTS700016: application not found in the tenant - check the app registration and client ID",
        "Custom subdomain required: the resource uses a regional endpoint; token-based auth needs a custom subdomain",
    ], theme="red", icon="security", src=[("Troubleshoot authentication errors", L("concepts/authentication-authorization-foundry"))])
    err.place(cv, rx, n1.bottom + 24)
    n2 = Note(rw, "Management requests and runtime calls use different audiences: the ARM control plane is https://management.azure.com, while Foundry data-plane "
                  "calls use https://ai.azure.com. A token for one does not work for the other.", kind="info", title="Two audiences, two planes")
    n2.place(cv, rx, err.bottom + 24)
    cy = cite(cv, 0, t.bottom + 8, "Source pages are linked per row; full list in the Sources panel", L("concepts/authentication-authorization-foundry"))
    return max(t.bottom, n2.bottom) + 70


# ====================================================================== 4. connections and secrets
def connections(cv, y):
    _, b = section_header(cv, 0, y, "4  Connections and where credentials live", size=34,
                          sub="Connections authenticate a project to Microsoft and other resources; their secrets sit in a Key Vault")
    yy = b + 40
    LBW = 1640
    a1 = Box(340, "Foundry resource connection", sub="available to all projects", theme="blue", icon="foundry", icon_pos="left",
             fill="hatch", h=110, size=19, sub_size=15)
    a2 = Box(340, "Project connection", sub="this project only", theme="green", icon="agent", icon_pos="left", fill="hatch",
             h=110, size=19, sub_size=15)
    a1.place(cv, 0, yy)
    a2.place(cv, 0, yy + 150)
    dec = Box(380, "Bring your own Key Vault?", shape="diamond", theme="yellow", fill="solid", size=20, h=250)
    dec.place(cv, 560, yy + 130 - 125)
    connect(cv, a1, dec, a_side="right", b_side="left", route="elbow", color="#495057", sw=2)
    connect(cv, a2, dec, a_side="right", b_side="left", route="elbow", color="#495057", sw=2)
    cv.text(350, yy + 255, "connection details\nand secrets", size=14, color=MUTED)

    n_card = Card(600, "No (default): Microsoft-managed Key Vault", [
        "Connection details and keys go to a Microsoft-managed Key Vault outside your subscription",
        "Secrets can't be retrieved across projects through APIs (security baseline IM-8)",
    ], theme="red", fill="soft", dash="dashed", icon="key-vault", src=[("Architecture", L("concepts/architecture"))])
    y_card = Card(600, "Yes: your Key Vault", [
        "One AzureKeyVault connection manages all project- and resource-level connection secrets",
        "Bicep: category AzureKeyVault, authType AccountManagedIdentity, isSharedToAll: true",
        "The Foundry resource's managed identity needs a role on the vault (see the roles card)",
    ], theme="red", icon="key-vault", src=[("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection"))])
    kx = 1040
    n_card.place(cv, kx, yy - 10)
    y_card.place(cv, kx, n_card.bottom + 36)
    connect(cv, dec, n_card, a_side="right", b_side="left", route="elbow", color="#495057", sw=2)
    connect(cv, dec, y_card, a_side="right", b_side="left", route="elbow", color="#495057", sw=2)
    cv.text(950, n_card.cy - 30, "No", size=18, color="#c92a2a")
    cv.text(950, y_card.cy + 6, "Yes", size=18, color="#c92a2a")

    # IaC order chain
    cy0 = max(y_card.bottom, a2.bottom) + 50
    cv.text(0, cy0, "Infrastructure as code: create in this order, delete in reverse", size=22, color="#a61e4d")
    steps = [("Foundry resource", "red"), ("Project", "red"), ("Key Vault connection", "red"), ("RBAC on the vault for the resource's MI", "red"),
             ("(Optional) validate the role", "gray"), ("All other connections, dependsOn steps 3 and 4", "red")]
    bw = (LBW - 5 * 36) / 6
    boxes = []
    for i, (t, th) in enumerate(steps):
        bx = Box(bw, t, theme=th, fill="hatch", size=16, h=104, pad=8, dash="dashed" if th == "gray" else "solid")
        bx.place(cv, i * (bw + 36), cy0 + 44)
        numbered(cv, i * (bw + 36) + 18, cy0 + 44, i + 1, theme=th, d=30, size=17)
        boxes.append(bx)
    for p, q in zip(boxes, boxes[1:]):
        connect(cv, p, q, a_side="right", b_side="left", color="#495057", sw=2, gap=3)
    cn = Note(LBW, "Delete in reverse: all connections, then the Key Vault connection, then the projects, then the Foundry resource. Without this order "
                   "templates hit race conditions and deployments work sometimes and fail at other times, because Foundry does not migrate secrets.",
              kind="tip", title="Why the order matters", src=[("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection"))])
    cn.place(cv, 0, boxes[0].bottom + 28)
    left_bottom = cn.bottom

    # ---------------------------------------------------------------- right block
    rx, cw = LBW + G, (W - LBW - G - 40) / 2
    limits = Card(cw, "Bring your own Key Vault: limits", [
        "! One Key Vault connection per Foundry resource; create it while the resource has no other connections",
        "! No secret migration: to switch vaults, delete the connection and recreate every connection and its secret",
        "! Deleting the vault breaks the Foundry resource",
        "! Deleting connection secrets in the vault can break other connections",
        "! Deleting the Key Vault connection deletes its secrets",
    ], theme="red", icon="key-vault", src=[("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection"))])
    limits.place(cv, rx, yy - 10)
    roles = Card(cw, "Roles on the vault for the resource's managed identity", [
        "Key Vault Secrets Officer (minimal): b86a8fe4-44ce-4948-aee5-eccb2c155cd7",
        "Key Vault Contributor: f25e0fa2-a7c8-4377-a976-54943a77a395",
        "Key Vault Administrator: 00482a5a-887f-4fb3-b363-3b7fe8e74483",
        "Or the equivalent access policy when the vault uses access policies",
        "Propagation can take up to 30 minutes",
        "Setup prerequisite: any one of the three roles; the administrator guide lists Key Vault Contributor + Key Vault Administrator for the creator",
    ], theme="red", icon="managed-identity", src=[("Administrator guide", L("concepts/administrator-guide"))])
    roles.place(cv, rx, limits.bottom + 24)

    cx2 = rx + cw + 40
    ga = ["Azure AI Search", "Azure Storage", "Azure OpenAI", "Application Insights", "Azure Key Vault", "Foundry", "OpenAI", "Serp", "API key",
          "Custom key", "Grounding with Bing Search", "Copilot Studio Environment"]
    pv = ["Azure Cosmos DB (code-only)", "Serverless Model", "Azure Databricks", "SharePoint", "Microsoft Fabric", "Grounding with Bing Custom Search",
          "Azure APIM", "Model Gateway"]
    with cv.panel(cx2, yy - 10, title="Connection types", sub="GA unless marked preview (orange)", theme="cyan", style="solid", fill="soft",
                  pad=20, title_size=22, sub_size=15, w=cw) as p1:
        chips = [Chip(t, theme="cyan", size=15, pad_y=5) for t in ga] + [Chip(t, theme="orange", size=15, pad_y=5, dash="dashed") for t in pv]
        ChipFlow(chips, cw - 40, gap=8).place(cv, p1.ix, p1.iy)
    cite(cv, cx2, p1.bottom + 6, "Add a connection", L("how-to/connections-add"))
    with cv.panel(cx2, p1.bottom + 40, title="authType values on a connection", sub="CLI form (top) and extra ARM / REST names (bottom)", theme="orange",
                  style="solid", fill="soft", pad=20, title_size=22, sub_size=15, w=cw) as p2:
        cli = ["none", "custom-keys", "project-managed-identity", "agentic-identity", "oauth2", "user-entra-token"]
        rest = ["UserEntraToken", "AgentOnBehalfOfUser (preview)", "OAuth2", "ProjectManagedIdentity", "AAD", "AccountManagedIdentity"]
        f1 = ChipFlow([Chip(t, theme="orange", size=15, pad_y=5) for t in cli], cw - 40, gap=8)
        f1.place(cv, p2.ix, p2.iy)
        f2 = ChipFlow([Chip(t, theme="yellow", size=15, pad_y=5) for t in rest], cw - 40, gap=8)
        f2.place(cv, p2.ix, p2.iy + f1.h + 12)
    cite(cv, cx2, p2.bottom + 6, "Tool authentication", L("agents/how-to/tools/tool-authentication"))
    ng = Note(cw, "Anyone with project access can read an API key stored in a project connection. Store only shared secrets there; use user delegation "
                  "or OAuth passthrough for user-specific access, and never put secrets in container images or hosted-agent environment variables.",
              kind="gotcha", title="Shared secrets only", src=[("MCP authentication", L("agents/how-to/mcp-authentication"))])
    ng.place(cv, cx2, p2.bottom + 40)
    nd = Note(cw, "connections-add and the administrator guide let a Foundry User, Foundry Owner or Contributor (or higher) add a connection; "
                  "hosted-agent-permissions says Foundry User cannot create connections.", kind="warn", title="Docs disagree: who can create connections?")
    nd.place(cv, cx2, ng.bottom + 20)
    return max(left_bottom, roles.bottom, nd.bottom) + 70


# ====================================================================== 5. five flows
HW = 200


def _sp(n):
    return (C3 - 44 - HW) / (n - 1)


def _seq(cv, x, y, actors):
    return Sequence(cv, x, y, actors, spacing=_sp(len(actors)), head_w=HW, size=15, label_size=15)


def flow1(cv, x, y):
    s = _seq(cv, x, y, [("Developer or app", "gray", "users"), ("Microsoft Entra ID", "red", "entra-connect"),
                        ("Foundry project endpoint", "blue", "foundry")])
    s.note(0, 2, "Sign in first: az login, Visual Studio / VS Code, or an environment service principal. DefaultAzureCredential walks env -> "
                 "managed identity -> developer tools.", kind="info")
    s.msg(0, 1, "Request a token: scope https://ai.azure.com/.default", num=1, note="The resource needs a custom subdomain.")
    s.msg(1, 0, "Access token", dash="dashed", num=2)
    s.msg(0, 2, "AIProjectClient(endpoint, credential) or raw REST to .../api/projects/<project>, with the token in the Authorization header", num=3)
    s.note(0, 2, "Foundry validates the token, then evaluates Azure RBAC dataActions for that principal at project or resource scope "
                 "(Foundry User = Microsoft.CognitiveServices/* data actions).", kind="key")
    s.msg(2, 0, "200 - or 401 (token or audience) / 403 (no role)", dash="dashed", num=4, gap_after=12,
          note="A new role assignment can take about 5 minutes to take effect.")
    return s.end()


def flow2(cv, x, y):
    s = _seq(cv, x, y, [("Client app (user or workload)", "gray", "app"), ("Microsoft Entra ID", "red", "entra-connect"),
                        ("Agent endpoint", "green", "agent")])
    s.note(0, 2, "One time: register a client app. Delegated clients get consent for the Foundry resource's user_impersonation; app-only clients "
                 "use a workload identity or certificate.", kind="info")
    s.msg(0, 1, "Request a token for https://ai.azure.com/.default (preview: the agent-blueprint audience)", num=1)
    s.msg(1, 0, "Access token", dash="dashed", num=2)
    s.msg(0, 2, "POST .../agents/<agent>/endpoint/protocols/openai/responses?api-version=v1", num=3, note="An OpenAI client with a token provider.")
    s.note(0, 2, "The endpoint checks authorization_schemes. AzureRbac: data action endpoints/interact/action at project or agent scope (Foundry Agent "
                 "Consumer). AgentBlueprint (preview): token-validation rules. BotService*: Teams / M365. The platform then derives the caller from the "
                 "Entra token (per-user session isolation for hosted agents).", kind="key")
    s.msg(2, 0, "Agent response (or 401 / 403)", dash="dashed", num=4)
    return s.end()


def flow3(cv, x, y):
    s = _seq(cv, x, y, [("Prompt agent", "green", "agent"), ("Project endpoint", "blue", "foundry"),
                        ("Hosted-agent code", "green", "container-apps"), ("Model deployment", "blue", "openai")])
    s.msg(0, 1, "Model call through the project endpoint", num=1)
    s.msg(1, 3, "Proxy to the account-level deployment as the project managed identity", num=2,
          note="Needs Foundry User at the Foundry account scope; auto-assigned when the project is created in the portal by someone who can assign roles.")
    s.msg(2, 1, "Inference as the agent identity", num=3,
          note="Implicit access to project-endpoint inference and session storage: no role needed.")
    s.msg(2, 3, "Bypass the project: call the account endpoint", num=4, note="https://{account}.cognitiveservices.azure.com")
    s.note(1, 3, "Direct calls need an account-scope role: Cognitive Services OpenAI User (OpenAI only) or Foundry User. Speech, Content Safety, Vision, "
                 "Document Intelligence, Language, Translator: Cognitive Services User or Foundry User.", kind="warn")
    return s.end()


def flow4(cv, x, y):
    s = _seq(cv, x, y, [("Agent Service", "green", "agent"), ("Project connection", "cyan", "api-connections"),
                        ("Microsoft Entra ID", "red", "entra-connect"), ("Tool server (MCP, A2A, OpenAPI)", "orange", "mcp")])
    s.msg(0, 1, "Read the connection's authType", num=1,
          note="none, custom-keys, project-managed-identity, agentic-identity, oauth2, user-entra-token")
    s.msg(0, 2, "Mint the credential: project MI, agent identity or user-delegated token", num=2,
          note="custom-keys: the stored key header. oauth2: the per-user OAuth token. Agent identity: a 4-stage exchange.")
    s.msg(0, 3, "Call the tool with that credential", num=3)
    s.note(2, 3, "The tool server or downstream service validates the token or key and makes its own authorization decision: Azure RBAC, "
                 "service data-plane roles, app roles or ACLs.", kind="key")
    s.msg(3, 0, "Result", dash="dashed", num=4, gap_after=10, note="The agent never sees the secret.")
    return s.end()


def flow5(cv, x, y):
    s = _seq(cv, x, y, [("Agent Service", "green", "agent"), ("Microsoft Entra ID", "red", "entra-connect"),
                        ("Cosmos DB / Storage (BYO)", "cyan", "cosmos"), ("AI Search (BYO)", "teal", "ai-search")])
    s.note(0, 2, "Capability settings point the project at BYO Cosmos DB (threads, agent definitions, run state), Storage (files) and AI Search "
                 "(vectors). Connections carry authType AAD, category, target and metadata.ResourceId.", kind="info")
    s.msg(0, 1, "Request tokens as the project managed identity, one per resource audience", num=1)
    s.msg(1, 0, "Access tokens", dash="dashed", num=2)
    s.msg(0, 2, "Call Cosmos DB and Storage", num=3, note="Over private endpoints when network-isolated, via the single-tenant data proxy.")
    s.msg(0, 3, "Call AI Search", num=4, note="Search Index Data Contributor + Search Service Contributor.")
    s.note(1, 3, "Project MI roles: Cosmos DB Built-in Data Contributor (database enterprise_memory; CLI or Bicep only), Storage Blob Data Contributor / "
                 "Owner on the two containers, plus Cosmos DB Operator and Storage Account Contributor at account level. A missing role = a 403 at runtime.",
           kind="gotcha")
    return s.end()


def flow67(cv, x, y):
    iw = C3 - 44
    cv.text(x, y, "Flow 6  Teams / M365 channel call", size=20, color="#364fc7")
    bw, gp = (iw - 3 * 54) / 4, 54
    t = y + 36
    f6 = [Box(bw, "Teams / M365 channel", theme="gray", icon="teams", fill="hatch", h=118, size=16, pad=8),
          Box(bw, "Azure Bot Service", sub="validates its own identity-provider JWT", theme="blue", icon="bot", fill="hatch", h=118, size=16, sub_size=13, pad=8),
          Box(bw, "Agent activityProtocol route", sub="on the agent endpoint", theme="green", icon="agent", fill="hatch", h=118, size=16, sub_size=13, pad=8),
          Box(bw, "Scheme check", sub="BotServiceRbac or BotServiceTenant", theme="red", icon="security", fill="hatch", h=118, size=16, sub_size=13, pad=8)]
    for i, b in enumerate(f6):
        b.place(cv, x + i * (bw + gp), t)
    for p, q in zip(f6, f6[1:]):
        connect(cv, p, q, a_side="right", b_side="left", color="#495057", sw=2, gap=3)
    y2 = f6[0].bottom + 44
    cv.text(x, y2, "Flow 7  Trace export (preview)", size=20, color="#5f3dc4")
    t2 = y2 + 40
    bw2 = 330
    s1 = Box(bw2, "Agent Service: server-side spans", sub="project managed identity", theme="green", icon="agent", fill="hatch", h=92, size=16, sub_size=14, pad=8)
    s2 = Box(bw2, "Hosted-agent code spans", sub="agent identity", theme="green", icon="container-apps", fill="hatch", h=92, size=16, sub_size=14, pad=8)
    s1.place(cv, x, t2)
    s2.place(cv, x, t2 + 112)
    ai = Box(bw2, "Application Insights", sub="local auth disabled; Monitoring Metrics Publisher on both identities", theme="violet", icon="app-insights",
             fill="hatch", h=204, size=17, sub_size=14, pad=8)
    ai.place(cv, x + iw - bw2, t2)
    connect(cv, s1, ai, a_side="right", b_side="left", color="#6741d9", sw=3, gap=3, ta=0.5, tb=(s1.cy - ai.y) / ai.h)
    connect(cv, s2, ai, a_side="right", b_side="left", color="#6741d9", sw=3, gap=3, ta=0.5, tb=(s2.cy - ai.y) / ai.h)
    nn = Note(iw, "Two emitters, two identities: Agent Service spans use the project managed identity; hosted-agent code uses its agent identity. "
                  "The portal assigns Monitoring Metrics Publisher to the project MI.", kind="preview", size=14,
              src=[("Trace ingestion with Entra", L("observability/how-to/trace-ingestion-entra-authentication"))])
    nn.place(cv, x, ai.bottom + 22)
    return nn.bottom


def flows(cv, y):
    _, b = section_header(cv, 0, y, "5  Five request flows, step by step", size=34,
                          sub="Each numbered flow matches an arrow in section 1. Message numbers restart in every flow.")
    y0 = b + 36
    items = [
        (1, "Developer SDK call to the project endpoint", "Entra token -> Azure RBAC dataActions", flow1),
        (2, "App calls a published agent endpoint", "caller token -> authorization_schemes", flow2),
        (3, "Agent calls a model", "project MI, or the agent identity", flow3),
        (4, "Agent calls a tool through a connection", "authType decides the credential; the tool decides access", flow4),
        (5, "Agent Service calls BYO Cosmos DB, Storage, AI Search", "project managed identity + data-plane roles", flow5),
    ]
    panels = [(f"Flow {n}  {t}", s, fn) for n, t, s, fn in items]
    panels.append(("Also on the wire: flows 6 and 7", "channel calls and trace export", flow67))

    def measure(title, sub, fn):
        m = Canvas("measure")
        with m.panel(0, 0, title=title, sub=sub, theme="gray", style="dotted", pad=22, title_size=26, sub_size=15, w=C3) as p:
            fn(m, p.ix, p.iy)
        return p.h

    bottoms = []
    for r in range(2):
        chunk = panels[r * 3:(r + 1) * 3]
        hmax = max(measure(*c) for c in chunk)
        for i, (title, sub, fn) in enumerate(chunk):
            with cv.panel(i * (C3 + G), y0, title=title, sub=sub, theme="gray", style="dotted", pad=22, title_size=26, sub_size=15,
                          w=C3, h=hmax) as p:
                fn(cv, p.ix, p.iy)
        y0 += hmax + 50
    return y0 + 20


def build(cv: Canvas) -> None:
    y = title_and_stamps(cv)
    y = hero(cv, y + 56)
    y = planes_identities_credentials(cv, y)
    y = credential_row(cv, y)
    y = audiences(cv, y)
    y = connections(cv, y)
    y = flows(cv, y)
    sources(cv, 0, y, [
        ("Authentication and authorization in Microsoft Foundry", L("concepts/authentication-authorization-foundry")),
        ("Role-based access control for Microsoft Foundry", L("concepts/rbac-foundry")),
        ("Configure key-less authentication with Microsoft Entra ID", L("foundry-models/how-to/configure-entra-id")),
        ("Disable local authentication in Foundry Tools", L("azure/ai-services/disable-local-auth", base="")),
        ("Rotate API keys", L("azure/ai-services/rotate-keys", base="")),
        ("Azure Policy built-ins for Azure AI Services", L("azure/ai-services/policy-reference", base="")),
        ("Add a connection in Microsoft Foundry", L("how-to/connections-add")),
        ("Set up an Azure Key Vault connection", L("how-to/set-up-key-vault-connection")),
        ("Identity and access overview for agents", L("agents/concepts/identity-access-overview")),
        ("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions")),
        ("Agent endpoint authorization", L("agents/concepts/agent-endpoint-authorization")),
        ("Trace ingestion with Entra authentication (preview)", L("observability/how-to/trace-ingestion-entra-authentication")),
        ("Azure OpenAI v1 REST reference: Responses", L("rest/api/microsoft-foundry/azureopenai/responses", base="")),
        ("Foundry MCP Server security best practices (preview)", L("mcp/security-best-practices")),
    ], w=W, cols=3)
