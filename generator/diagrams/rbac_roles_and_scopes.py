"""Foundry roles, scopes and least-privilege assignments - scope ladder, six Foundry roles, capability matrices, starter assignments, doc conflicts."""
from generator.xd import *
from generator.xd.blocks import draw_mark

META = dict(
    id="rbac-roles-and-scopes", title="Foundry roles, scopes and least-privilege assignments", section="5", order=2,
    description="Every built-in Foundry role and related role (control plane vs data plane), the scope ladder down to one agent, "
                "role-by-capability matrices, starter least-privilege assignments and the places where Learn pages disagree.",
    tags=["rbac", "roles", "scopes", "least-privilege", "foundry-user", "agent-consumer"],
)

W = 3360                       # canvas width
G = 60                         # gutter
C3 = (W - 2 * G) / 3           # three-column grid (1080)
XB, XC = C3 + G, 2 * (C3 + G)  # x of columns 2 and 3


def L(path, **kw):
    return learn(path, **kw)


RBAC = ("RBAC for Foundry", L("concepts/rbac-foundry"))
ADMIN = ("Foundry administrator guide", L("concepts/administrator-guide"))
ROLES = ("Built-in roles: AI + machine learning", L("role-based-access-control/built-in-roles/ai-machine-learning", base="azure"))
HOSTED = ("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions"))
AUTH = ("Authentication and authorization", L("concepts/authentication-authorization-foundry"))
CLASSIC_RBAC = ("Azure OpenAI roles (Foundry classic)", L("openai/how-to/role-based-access-control", base="azure/foundry-classic"))

Y, N, P, D = CHECK, CROSS, PARTIAL, DASH


def cite(cv, x, y, items, size=12):
    """Clickable 'Learn: ...' lines under a table (tables have no src= parameter). Returns the bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def colhead(cv, x, y, text, w, sub=None):
    return section_header(cv, x, y, text, sub=sub, size=28, w=w, sub_size=15)[1]


def mark_legend(cv, x, y):
    """Small key for the vector marks used in the matrices."""
    cx = x
    for kind, label in ((Y, "allowed"), (N, "not allowed"), (P, "docs disagree"), (D, "not applicable")):
        draw_mark(cv, kind, cx + 11, y + 11)
        t = cv.text(cx + 28, y + 1, label, size=15)
        cx += 28 + t.w + 26
    return y + 26


# ====================================================================== 0. stamps
def stamps(cv, y):
    sw = (W - 3 * 40) / 4
    spec = [
        ("Foundry User is the working role",
         "Data actions on Microsoft.CognitiveServices/*, reader on projects and accounts - and it includes accounts/listkeys/action",
         "green"),
        ("Owner and Contributor are not data-plane roles",
         "They provision resources but hold no Foundry data actions: they cannot create agents or chat with agents", "orange"),
        ("Assign at the narrowest scope that works",
         "Roles inherit downward: subscription, resource group, Foundry resource, project, agent", "blue"),
        ("Callers get Foundry Agent Consumer",
         "One data action. The Azure portal assigns it only at account scope - project or agent scope needs the Azure CLI", "red"),
    ]
    boxes = [Box(sw, t, sub=s, theme=th, size=24, sub_size=16, h=112, sw=3) for t, s, th in spec]
    row(cv, 0, y, boxes, gap=40)
    return y + 112


# ====================================================================== 1. ladder + roles
def ladder(cv, x, y, w, height=None):
    spec = [
        dict(title="Azure subscription", icon="subscription", theme="gray",
             sub="Broadest practical scope: governance, quota and marketplace billing",
             body=["IT admin: Owner - enforces standards and assigns Foundry Account Owner / Project Manager",
                   "Cognitive Services Usages Reader works here only: the quota API rejects resource group, resource and project scope",
                   "Contributor here: marketplace model deployments (billing agreement), quota increase requests, recover or purge deleted accounts"]),
        dict(title="Resource group", icon="resource-group", theme="gray",
             sub="A role here covers every Foundry resource and project in the group",
             body=["Contributor or Owner: provision the Foundry resource, ACR, Application Insights, Log Analytics, Bot Service",
                   "Small team of 1-5: Owner on yourself at the resource group"]),
        dict(title="Foundry resource (account)", icon="foundry", theme="blue",
             sub="Microsoft.CognitiveServices/accounts - the top-level admin, security and monitoring boundary",
             body=["A role here covers all projects in the resource",
                   "Foundry Account Owner: deploy models, quotas, guardrails, blocklists, Purview",
                   "Foundry Project Manager: team leads - members and projects (docs disagree on create projects; see section 5) - and it must sit here to publish",
                   "Foundry User for each developer and each project managed identity (starter assignments)",
                   "! Evaluations that invoke a model need Foundry User at account scope; project scope alone does not authorize inference"],
             src=[RBAC, ADMIN]),
        dict(title="Project", icon="foundry", theme="green",
             sub="Microsoft.CognitiveServices/accounts/projects - the access boundary for Foundry APIs, tools and dev workflows",
             body=["Developers: Foundry User on the project and Reader on the Foundry resource",
                   "Foundry Agent Consumer: callers of every agent in the project (Azure CLI)",
                   "The project managed identity holds data-plane roles on BYO Cosmos DB, AI Search and Storage (standard agent setup)"]),
        dict(title="Agent", icon="agent", theme="green", dash="dashed", badge="new",
             sub=".../projects/<project>/agents/<agent>",
             body=["Any role assignable at project scope can be assigned here",
                   "! Evaluated only for agent-endpoint access: no control-plane or management rights come from this scope",
                   "Foundry Agent Consumer here lets a caller reach one agent's endpoint only"]),
    ]
    step = 40   # each level steps in, so the ladder reads as nesting
    cards = [Card(w - i * step, s["title"], s["body"], theme=s["theme"], subtitle=s["sub"], icon=s["icon"], badge=s.get("badge"),
                  dash=s.get("dash", "solid"), src=s.get("src", ())) for i, s in enumerate(spec)]
    gap = 56
    if height:   # stretch the gaps so the ladder ends level with the neighbouring column
        gap = max(56, min(130, (height - sum(c.h for c in cards)) / (len(cards) - 1)))
    cy = y
    for i, c in enumerate(cards):
        c.place(cv, x + i * step, cy)
        cy = c.bottom + gap
    for i, (a, b) in enumerate(zip(cards, cards[1:])):
        ax = b.x + 46
        arrow(cv, [(ax, a.bottom + 4), (ax, b.y - 4)], sw=3, label="role assignments inherit downward" if i == 0 else "inherits",
              label_size=15)
    return cards[-1].bottom


def role_cards(cv, x, y):
    w, gap = 746, 41
    kw = dict(src=[ROLES])
    consumer = Card(w, "Foundry Agent Consumer", [
        "Only data action: Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action",
        "Least-privilege caller of agent endpoints: project scope (all agents) or agent scope (one agent)",
        "! The Azure portal can assign it only at the Foundry account scope; project or agent scope needs the Azure CLI",
        "= Role ID eed3b665-ab3a-47b6-8f48-c9382fb1dad6",
    ], theme="green", subtitle="Data plane only - callers of agent endpoints", icon="agent", **kw)
    runtime = Card(w, "Foundry Project Runtime User", [
        "Data actions: AIServices/responses/read, responses/write and responses/delete",
        "Described as interacting with Foundry agents at runtime with minimal required permissions",
        "! Appears only on the built-in roles page; the RBAC for Foundry article does not describe it (as of 2026-11-03)",
        "= Role ID 142bfaed-a13f-4c2d-bed2-6db62c4a1009",
    ], theme="green", subtitle="Data plane only - agent runtime", icon="agent", **kw)
    user = Card(w, "Foundry User", [
        "Actions: Microsoft.CognitiveServices/*/read and accounts/listkeys/action (reader on projects and accounts), plus Microsoft.Resources/deployments/*",
        "Data actions: all Microsoft.CognitiveServices/*",
        "Developers building and testing agents; also the role for the project managed identity (resource or project scope)",
        "! Cannot create projects or accounts, manage models or publish",
        "= Role ID 53ca6127-db72-4b80-b1b0-d745d6d5456d",
    ], theme="green", subtitle="Data plane + read | formerly Azure AI User", icon="user", **kw)
    pm = Card(w, "Foundry Project Manager", [
        "Control plane: accounts/projects/*, accounts/*/read, locations/*/read",
        "Role-assignment write/delete, limited by an ABAC condition to Foundry User; data actions Microsoft.CognitiveServices/*",
        "Team leads. Publishing needs this role at Foundry resource scope (Publish stays disabled otherwise)",
        "! Cannot deploy models. Learn pages disagree on whether it can create projects (see the table at the bottom)",
        "= Role ID eadc314b-1a2d-4efa-be10-5d325db5065e",
    ], theme="red", subtitle="Projects + data plane | formerly Azure AI Project Manager", icon="users", **kw)
    ao = Card(w, "Foundry Account Owner", [
        "Microsoft.CognitiveServices/* control plane, plus diagnostics, deployments and support",
        "Create accounts and projects, deploy models, quotas, blocklists, guardrails, Purview",
        "! No data actions: it cannot create agents or chat with agents until you also assign Foundry User",
        "Role-assignment write/delete limited by ABAC to 4 roles: Foundry User, Container Registry Contributor and Data Access Configuration Administrator, Container Registry Repository Writer, Log Analytics Reader",
        "= Role ID e47c6f54-e4a2-4754-9501-8e0985b135e1",
    ], theme="grape", subtitle="Control plane only | formerly Azure AI Account Owner", icon="foundry", **kw)
    owner = Card(w, "Foundry Owner", [
        "Control plane as Foundry Account Owner plus all Microsoft.CognitiveServices/* data actions",
        "Same ABAC-limited role assignment as Foundry Account Owner",
        "The highly privileged self-serve role: fine-tuning, hosted-agent deployment",
        "Combine with Azure Monitor Reader when you need observability",
        "! hosted-agent-permissions says it cannot create role assignments; RBAC for Foundry and the role definition say it can, conditionally",
        "= Role ID c883944f-8b7b-4483-af10-35834be79c4a",
    ], theme="red", subtitle="Both planes | formerly Azure AI Owner", icon="foundry", **kw)
    _, b1 = row(cv, x, y, [consumer, runtime, user], gap=gap)
    _, b2 = row(cv, x, b1 + 40, [pm, ao, owner], gap=gap)
    return b2


def assignment_cards(cv, x, y):
    w, gap = 746, 41
    c1 = Card(w, "Assign a role", [
        "Foundry portal: Manage > Project details > Users > Add user (same on Resource details); you need role-assignment rights",
        "Azure portal: Access control (IAM) > Add role assignment",
        "CLI: az role assignment create --assignee-object-id <id> --assignee-principal-type ServicePrincipal --role <GUID> --scope <scope>",
        "! Azure AI User, Owner, Account Owner and Project Manager were renamed to Foundry ...; IDs and permissions are unchanged. Use the role GUID, not the name, in code during the rollout",
    ], theme="red", icon="key-vault", src=[RBAC, ("Create projects", L("how-to/create-projects"))])
    c2 = Card(w, "Verify and wait", [
        "Verify with az role assignment list, or IAM Check access",
        "Propagation can take up to about 5 minutes: ask the user to sign out and back in",
        "Cosmos DB Built-in Data Contributor is not visible in the IAM blade: use az cosmosdb sql role assignment create or Bicep",
        "Entra directory roles (for example AI Administrator or Global Administrator) are assigned in the Entra admin center, not in IAM",
    ], theme="gray", icon="pim", src=[RBAC, ADMIN])
    c3 = Card(w, "Who gets Foundry User automatically", [
        "A project created in the portal UI by someone who can assign roles: Foundry User goes to the creator and to the project managed identity",
        "! Not when the project is created by SDK, CLI or Bicep: assign Foundry User yourself",
        "Create a custom role only as Owner on the scope; assign custom roles as User Access Administrator or RBAC Administrator",
    ], theme="green", icon="managed-identity", src=[("Create projects", L("how-to/create-projects")), ADMIN])
    return row(cv, x, y, [c1, c2, c3], gap=gap)[1]


def role_picker(cv, x, y, w):
    """Need -> role mini flow: five pairs, role boxes coloured by plane."""
    _, b = section_header(cv, x, y, "Which role do I give? Start from what the person or app needs to do", size=24, w=w)
    gap = 30
    cw = (w - 4 * gap) / 5
    spec = [
        ("Call agent endpoints only", "Foundry Agent Consumer", "Project scope (all agents) or agent scope (one agent); Azure CLI", "green"),
        ("Build and test agents on pre-deployed models", "Foundry User", "Project or Foundry resource scope", "green"),
        ("Create projects, invite members, publish", "Foundry Project Manager", "Foundry resource scope (needed to publish); docs disagree on create projects", "red"),
        ("Deploy models, set quotas, guardrails and blocklists", "Foundry Account Owner", "Foundry resource scope; add Foundry User to build", "grape"),
        ("Fine-tune models or deploy hosted agents with one role", "Foundry Owner", "The highly privileged self-serve role", "red"),
    ]
    needs = [Box(cw, n, theme="gray", size=17, h=76, fill="soft") for n, _, _, _ in spec]
    roles = [Box(cw, r, sub=s, theme=th, size=18, sub_size=14, h=100) for _, r, s, th in spec]
    ny = b + 26
    row(cv, x, ny, needs, gap=gap)
    ry = ny + max(n.h for n in needs) + 52
    row(cv, x, ry, roles, gap=gap)
    for n, r in zip(needs, roles):
        connect(cv, n, r, a_side="bottom", b_side="top", sw=3, gap=4)
    return ry + max(r.h for r in roles)


def section_roles(cv, y):
    _, b = section_header(cv, 0, y, "1  The scope ladder and the six Foundry roles", size=34,
                          sub="Control plane = Azure Resource Manager actions (create, configure, deploy). Data plane = what you do through the Foundry APIs: "
                              "build agents, run evaluations, call agent endpoints.")
    top = b + 30
    LW = 980
    x0 = LW + G
    colhead(cv, 0, top, "Scope ladder: where an assignment lives", LW)
    colhead(cv, x0, top, "Six built-in Foundry roles", W - x0)
    legend(cv, x0 + 560, top + 8, [("Data plane", "green"), ("Control plane", "grape"), ("Both planes", "red")])
    y0 = top + 70
    rb = role_cards(cv, x0, y0)
    imp = Note(W - x0, "A trusted middle tier that sends the x-ms-user-identity header needs the custom data action "
                       "Microsoft.CognitiveServices/accounts/AIServices/agents/endpoints/UserIdentityImpersonation/action. No built-in role grants it: the "
                       "Microsoft.CognitiveServices/* data-action wildcard on Foundry User and Foundry Owner no longer includes it, so assign it through a custom role. "
                       "See the canvas 'Agent identity and delegation' for per-user session isolation (isolation_key_source = Header).", kind="gotcha",
               title="x-ms-user-identity needs a custom data action that no built-in role grants", src=[HOSTED, RBAC])
    imp.place(cv, x0, rb + 36)
    pb = role_picker(cv, x0, imp.bottom + 46, W - x0)
    ab = assignment_cards(cv, x0, pb + 46)
    lb = ladder(cv, 0, y0, LW, height=ab - y0)
    return max(lb, ab)


# ====================================================================== 2. matrices
def section_matrices(cv, y):
    _, b = section_header(cv, 0, y, "2  Role x capability matrices: what each role can actually do", size=34,
                          sub="Matrix A is the capability table of RBAC for Foundry; matrix B is the task-by-minimum-role table of hosted agent permissions. "
                              "Amber = the pages disagree. As of 2026-11-03.")
    top = b + 34

    rows_a = [
        [("Foundry Agent Consumer", "red"), N, N, N, N, N, N, N, Y],
        [("Foundry User", "red"), N, N, Y, N, Y, N, N, Y],
        [("Foundry Project Manager", "red"), P, N, Y, ("Foundry User only", "yellow"), Y, N, Y, Y],
        [("Foundry Account Owner", "red"), Y, Y, N, ("Foundry User, ACR and monitoring roles", "yellow"), Y, Y, N, N],
        [("Foundry Owner", "red"), Y, Y, Y, ("Foundry User, ACR and monitoring roles", "yellow"), Y, Y, Y, Y],
        [("Owner", "gray"), Y, Y, N, ("Any role, any user", "green"), Y, Y, Y, N],
        [("Contributor", "gray"), Y, Y, N, N, Y, Y, N, N],
        [("Reader", "gray"), N, N, N, N, Y, N, N, N],
    ]
    ta = Table([("Role", 190), ("Create projects", 92), ("Create accounts", 92), ("Build and develop (data actions)", 105),
                ("Complete role assignments", 200), ("Reader on projects and accounts", 112), ("Manage models", 90),
                ("Publish agents", 90), ("Interact with agent endpoints", 109)], rows_a, theme="red", size=14, head_size=14,
               pad_x=6, align=["left", "center", "center", "center", "left", "center", "center", "center", "center"],
               title="A  Capability by role (RBAC for Foundry)", title_size=22)
    ta.place(cv, 0, top)
    yy = mark_legend(cv, 0, ta.bottom + 14)
    cite(cv, 0, yy + 6, [RBAC])

    rows_b = [
        ["Create a Foundry account (resource group; accounts/write)", Y, Y, D, N, N, Y, Y],
        ["Deploy a model (account; deployments/write)", Y, Y, D, N, N, Y, Y],
        ["Create a project (account; projects/write)", Y, Y, D, N, Y, Y, Y],
        ["Create a connection (project; connections/write)", Y, Y, D, P, Y, Y, Y],
        ["Create an agent application (project) or agentDeployment (account)", Y, Y, D, N, Y, Y, Y],
        [("Create an agent, agent version or change the active version (project; data plane agents/write)", "yellow"), N, N, N, Y, Y, N, Y],
        [("Interact with an agent endpoint (project or agent; endpoints/interact/action)", "yellow"), N, N, Y, Y, Y, N, Y],
        ["Invoke an agent application (applications/invoke/action)", N, N, N, Y, Y, N, Y],
        ["Create ACR, App Insights, Log Analytics or Bot Service (resource group)", Y, Y, D, N, N, N, N],
        ["Create a role assignment on ACR or a Log Analytics workspace (Project Manager and Account Owner: Foundry User only)", Y, N, D, N, N, N, N],
        ["Read agent traces in App Insights (Foundry User and Account Owner see metrics only)", Y, Y, D, N, N, N, N],
        ["Model inference by the agent identity at project scope", N, N, D, Y, Y, N, Y],
    ]
    tb = Table([("Task (minimum scope; action)", 358), ("Owner", 103), ("Contributor", 103), ("Agent Consumer", 103),
                ("Foundry User", 103), ("Project Manager", 103), ("Account Owner", 103), ("Foundry Owner", 103)], rows_b,
               theme="red", size=14, head_size=14, pad_x=6, align=["left"] + ["center"] * 7,
               title="B  Task by minimum role (hosted agent permissions)", title_size=22)
    tb.place(cv, XB, top)
    cb_ = cite(cv, XB, tb.bottom + 10, [HOSTED])

    # ---- notes: column 1 under matrix A, column 2 under matrix B, delegation diagram + disagreements in column 3
    n1 = Note(C3, "Owner and Contributor hold no Foundry data actions, so they cannot create agents or chat with agents. Foundry Account Owner is control plane only: "
                  "it cannot either, until you also give it Foundry User.", kind="gotcha",
              title="Control plane is not data plane", src=[RBAC, HOSTED])
    n2 = Note(C3, "Foundry User's actions include accounts/listkeys/action next to Microsoft.CognitiveServices/*/read: holders can list the account keys. "
                  "Cognitive Services User includes listkeys too.", kind="key", title="Foundry User includes listkeys", src=[ROLES])
    col(cv, 0, yy + 50, [n1, n2], gap=22)
    n6 = Note(C3, "Interact with an agent endpoint is allowed for Agent Consumer, Foundry User, Project Manager and Foundry Owner - not for Owner, Contributor or Account Owner. "
                  "Highlighted rows are the two data-plane tasks: Owner, Contributor and Account Owner are not allowed to do either. Role Based Access Control Administrator can create the ACR and Log Analytics assignments; "
                  "Monitoring Reader, Log Analytics Reader or Privileged Monitoring Data Reader read telemetry.", kind="tip", title="Reading matrix B", src=[HOSTED])
    n6.place(cv, XB, cb_ + 22)

    dg = delegation(cv, XC, top, C3)
    n3 = Note(C3, "The capability matrix says Foundry Project Manager cannot create projects; the same page's persona table, hosted agent permissions and the role "
                  "definition (accounts/projects/*) say it can. Drawn as an amber circle in matrix A - verify in your tenant.",
              kind="warn", title="Docs disagree: Project Manager and create projects", src=[RBAC, HOSTED])
    n4 = Note(C3, "Add a connection and the administrator guide allow Foundry User to create project connections; hosted agent permissions says it cannot (amber in matrix B).",
              kind="warn", title="Docs disagree: who may create connections", src=[("Add a connection", L("how-to/connections-add")), HOSTED])
    _, nb = col(cv, XC, dg + 24, [n3, n4], gap=22)
    return max(n6.bottom, nb, n2.bottom) + 70


def delegation(cv, x, y, w):
    """Who can assign which roles: assigner boxes -> assignable role chips (dashed = ABAC-limited)."""
    rows = [
        ("Owner", "any role, any user; creates custom roles", "gray",
         [Chip("Any role", theme="green", size=15)], "solid"),
        ("User Access Administrator or RBAC Administrator", "any role, including custom roles", "gray",
         [Chip("Any role", theme="green", size=15),
          Chip("Needed for ACR, Log Analytics, Cosmos DB, Search, Storage, Key Vault roles", theme="gray", size=14)], "solid"),
        ("Foundry Account Owner", "role assignment limited by an ABAC condition", "grape",
         [Chip("Foundry User", theme="green", size=15),
          Chip("Container Registry Contributor and Data Access Configuration Administrator", theme="gray", size=14),
          Chip("Container Registry Repository Writer", theme="gray", size=14),
          Chip("Log Analytics Reader", theme="gray", size=14)], "dashed"),
        ("Foundry Owner", "same ABAC-limited assignment rights", "red",
         [Chip("The same four roles as Foundry Account Owner", theme="gray", size=14)], "dashed"),
        ("Foundry Project Manager", "role assignment limited by an ABAC condition", "red",
         [Chip("Foundry User", theme="green", size=15)], "dashed"),
    ]
    bw, gap = 340, 70
    with cv.panel(x, y, title="Who can assign which roles", sub="Dashed arrow = limited by an ABAC condition (role definitions, as of 2026-11-03)",
                  theme="red", style="dotted", pad=24, title_size=24, sub_size=15, w=w) as p:
        cy = p.iy
        for label, sub, theme, chips, dash in rows:
            flow = ChipFlow(chips, w - 2 * 24 - bw - gap, gap=8)
            box = Box(bw, label, sub=sub, theme=theme, size=17, sub_size=14, min_h=64)
            rh = max(box.h, flow.h + 6)
            box.place(cv, p.ix, cy, h=rh)
            flow.place(cv, p.ix + bw + gap, cy + (rh - flow.h) / 2)
            arrow(cv, [(box.right + 6, cy + rh / 2), (p.ix + bw + gap - 8, cy + rh / 2)], dash=dash, sw=3,
                  color=THEMES[theme].stroke)
            cy += rh + 16
        t = cv.text(p.ix, cy + 2, "Not in the ABAC sets: Container Registry Repository Reader (AcrPull) and Log Analytics Data Reader - "
                    "those still need Owner or RBAC Administrator. Some pages say Account Owner can assign Foundry User only.",
                    size=14, color=MUTED, wrap=w - 48)
        cv.text(p.ix, t.bottom + 4, "Learn: Foundry administrator guide", size=12, color=LINK, link=ADMIN[1])
    return p.bottom


# ====================================================================== 3. starter assignments
def section_starter(cv, y):
    _, b = section_header(cv, 0, y, "3  Starter least-privilege assignments", size=34,
                          sub="Minimum to get started, a sample enterprise mapping, scenario-to-role guidance and the day-0 onboarding path (portal).")
    top = b + 34

    persona = Table([("Persona", 190), ("Role @ scope", 330), "Purpose"], [
        ["IT admin", ("Owner @ subscription", "gray"), "Enforces standards; assigns Foundry Account Owner / Project Manager"],
        ["Managers", ("Foundry Account Owner @ Foundry resource", "grape"),
         "Manage the resource, deploy models, audit compute and connections, shared connections - cannot build until they self-assign Foundry User"],
        ["Team lead / lead developer", ("Foundry Project Manager @ Foundry resource", "red"), "Create projects, invite members, assign Foundry User"],
        ["Developers", ("Foundry User @ project + Reader @ Foundry resource", "green"), "Build agents on pre-deployed models and pre-built connections"],
        ["Agent consumers / end users", ("Foundry Agent Consumer @ project (or agent)", "green"), "Call agent endpoints only"],
    ], w=C3, theme="red", size=14, head_size=15, title="Sample enterprise mapping", title_size=22)
    start = Card(C3, "Minimum to get started", [
        "# Three assignments",
        "= 1  Foundry User to your user principal at the Foundry resource",
        "= 2  Foundry User to the project managed identity at the Foundry resource",
        "= 3  Optional: Cognitive Services Usages Reader at the subscription (quota and eligibility checks)",
        "# Callers only",
        "Foundry Agent Consumer at project scope (all agents) or agent scope (one agent) - Azure CLI",
    ], theme="green", icon="user", src=[RBAC])
    start.place(cv, 0, top)
    persona.place(cv, 0, start.bottom + 34)
    cb = cite(cv, 0, persona.bottom + 8, [RBAC])

    scen = Table([("Scenario", 250), ("Typical built-in role", 250), "Page note"], [
        ["Build agents with pre-deployed models", ("Foundry User", "green"), "Data plane usage only; no management writes"],
        ["Manage deployments or fine-tune models", ("Foundry Project Manager (docs disagree)", "orange"),
         "The page says it includes model deployment creation and update; RBAC for Foundry, hosted agent permissions and the role definition say it cannot create deployments"],
        ["Rotate keys or manage the resource", ("Foundry Account Owner", "grape"), "High privilege; consider a custom role for least privilege"],
        ["Manage resource, manage deployments, build agents", ("Foundry Owner", "red"),
         "Highly privileged self-serve role; combine with Azure Monitor Reader if observability is required"],
        ["Observability, tracing, monitoring", ("Foundry User (minimum)", "green"),
         "Add Azure Monitor Reader on Application Insights (this page's wording; other pages name Monitoring Reader or Log Analytics Reader)"],
    ], w=C3, theme="red", size=14, head_size=15, title="Scenario to role (authentication and authorization page)", title_size=22)
    scen.place(cv, XB, top)
    sb = cite(cv, XB, scen.bottom + 8, [AUTH])
    nfine = Note(C3, "Fine-tuning: only Foundry Owner holds both planes; otherwise combine Foundry User (data plane) with Foundry Account Owner (control plane).",
                 kind="info", title="Fine-tuning needs both planes", src=[ADMIN])
    nfine.place(cv, XB, sb + 20)

    small = Card(C3, "Small team (1-5 developers)", [
        "Owner on yourself at the resource group",
        "Foundry User for each developer at Foundry resource scope",
        "Foundry Account Owner for whoever deploys models, sets quotas, guardrails and blocklists",
    ], theme="blue", icon="foundry", src=[ADMIN])
    custom = Card(C3, "Custom role example: My Enterprise Foundry User", [
        "Actions: Microsoft.CognitiveServices/*/read, Microsoft.Authorization/*/read, .../accounts/listkeys/action, Microsoft.Resources/deployments/*",
        "DataActions: Microsoft.CognitiveServices/accounts/AIServices/agents/*",
        "Creating it needs Owner on the scope",
    ], theme="gray", icon="key-vault", src=[RBAC])
    hyg = Card(C3, "Hygiene for elevated roles", [
        "Use Entra security groups for people instead of individual assignments",
        "Consider PIM-eligible assignments for the elevated roles",
        "Assign at the narrowest scope that works: a role at resource group scope covers every Foundry resource in it",
    ], theme="gray", icon="pim", src=[RBAC, ADMIN])
    _, cbot = col(cv, XC, top, [small, custom, hyg], gap=22)
    row_bottom = max(nfine.bottom, cb, cbot)

    # ---- day-0 onboarding flow
    fy = row_bottom + 50
    section_header(cv, 0, fy, "Day-0 onboarding, portal path: who does what, in order", size=26, w=W)
    fy += 66
    cw = 560
    steps = [
        ("Create the resource and project", "foundry", "blue",
         ["IT admin (Owner) creates the Foundry resource and a project in the portal",
          "Foundry User is auto-assigned to the creator and to the project managed identity"]),
        ("Delegate administration", "pim", "grape",
         ["Admin assigns Foundry Account Owner and Foundry Project Manager at resource scope",
          "Use Entra groups; make the elevated assignments PIM-eligible"]),
        ("Team lead sets up projects", "users", "red",
         ["Creates projects; assigns developers Foundry User on the project and Reader on the Foundry resource"]),
        ("Developers build", "code", "green",
         ["Agents on pre-deployed models and pre-built connections", "Data-plane work only: no management writes"]),
        ("Callers get access", "agent", "green",
         ["Foundry Agent Consumer at project scope (all agents) or agent scope (one agent)", "Below account scope, assign with the Azure CLI"]),
    ]
    cards = [Card(cw, t, body, theme=th, icon=ic, src=[RBAC, ADMIN] if i == 0 else ()) for i, (t, ic, th, body) in enumerate(steps)]
    hgap = (W - 5 * cw) / 4
    _, fb = row(cv, 0, fy, cards, gap=hgap)
    for i, (a, bb) in enumerate(zip(cards, cards[1:])):
        connect(cv, a, bb, a_side="right", b_side="left", sw=3, gap=4)
    for i, c in enumerate(cards):
        numbered(cv, c.x + 34, c.y, i + 1, theme="red")
    return fb


# ====================================================================== 4. related roles
def section_related(cv, y):
    _, b = section_header(cv, 0, y, "4  Related roles the docs mention: use, avoid or special-case", size=34,
                          sub="General Azure roles you still need, then the Cognitive Services and legacy roles. Verdicts follow RBAC for Foundry; amber marks pages that disagree.")
    top = b + 34
    hw = (W - G) / 2
    gen = Table([("Role", 290), ("Verdict", 100), "When"], [
        ["Owner", ("Use", "green"), "Any role assignment; needed to create custom roles. Neither Owner nor Contributor has Foundry data actions"],
        ["Contributor", ("Use", "green"), "Provisioning, marketplace deployments, private endpoint creation; cannot assign roles"],
        ["User Access Administrator / Role Based Access Control Administrator", ("Use", "green"),
         "Needed for assignments beyond the ABAC limits of Foundry Account Owner, Project Manager and Foundry Owner: ACR, Log Analytics, Cosmos DB, Search, Storage, Key Vault"],
        ["Cognitive Services Usages Reader\nbba48692-92b0-4667-a9ad-c31c7b334ac2", ("Use", "green"),
         "Subscription scope only: quota visibility and deployment eligibility checks; the Usages API rejects other scopes. The only Cognitive Services role RBAC for Foundry recommends"],
        ["Azure AI Enterprise Network Connection Approver\nb556d68e-0be0-4f35-a333-ad7ee1ce17ea", ("Special", "yellow"),
         "Assign to the Foundry account managed identity so managed-VNet private endpoints are auto-approved (also App Gateway)"],
    ], w=hw, theme="gray", size=14, head_size=15, title="General Azure roles and special-purpose roles", title_size=22)
    gen.place(cv, 0, top)
    cite(cv, 0, gen.bottom + 8, [RBAC, ADMIN])

    cs = Table([("Role", 290), ("Verdict", 100), "What the docs say"], [
        ["Cognitive Services User\na97b65f3-24c7-4388-baec-2e87135dc908", ("Docs disagree", "orange"),
         "Data actions Microsoft.CognitiveServices/*, includes listkeys. Documented for Foundry Models inference with Entra, account-level Speech/Vision/Language for agents "
         "and the Search managed identity in the Foundry IQ tutorial - yet RBAC for Foundry says not to assign Cognitive Services roles except Usages Reader"],
        ["Cognitive Services OpenAI User\n5e0bd9bd-7b93-4f28-af87-19fc36ad61bd", ("Caution", "yellow"),
         "OpenAI/*/read plus completion, chat, embedding, image, video, assistants and responses actions; NotDataActions: stored completions read. Account-level OpenAI endpoint only"],
        ["Cognitive Services OpenAI Contributor\na001fd3d-188f-4b5d-821b-7da978bf7442", ("Caution", "yellow"),
         "Deployments write/delete, raiPolicies, commitmentplans and OpenAI/* data actions; the classic doc lists fine-tune, datasets, stored completions, create/edit deployments; cannot list keys, no quota"],
        ["Cognitive Services Contributor\n25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68", ("Caution", "yellow"),
         "Managed-compute deployments full CRUD; classic doc: create resources, view/regenerate keys, guardrails; cannot call inference with Entra"],
        ["Azure AI Developer\n64702f94-c441-49e6-a78b-ef80e0188fee", ("Avoid", "red"),
         "Do not use for Foundry projects or hosted agents: it is scoped to Azure ML workspaces and hubs (the legacy hub-project role error)"],
    ], w=hw, theme="gray", size=14, head_size=15, title="Cognitive Services and legacy roles", title_size=22)
    cs.place(cv, hw + G, top)
    cite(cv, hw + G, cs.bottom + 8, [RBAC, CLASSIC_RBAC, ROLES])
    return max(gen.bottom, cs.bottom) + 70


# ====================================================================== 5. conflicts
def section_conflicts(cv, y):
    _, b = section_header(cv, 0, y, "5  Where Learn pages disagree (as of 2026-11-03)", size=34,
                          sub="Each row is a conflict between pages that were read for this canvas. Verify the live role definitions in your tenant before relying on either side.")
    top = b + 34
    t = Table([("Topic", 300), ("One page says", 860), ("Another page says", 900), "How this canvas draws it"], [
        [("Project Manager: create projects", "orange"), "RBAC for Foundry capability matrix: Create projects = not allowed",
         "The same page's persona table (team lead creates projects), hosted agent permissions and the role definition (accounts/projects/*) say it can",
         "Amber circle in matrix A; allowed in matrix B"],
        [("Project Manager: model deployments", "orange"), "Authentication and authorization page: scenario table says it 'includes model deployment creation and update'",
         "RBAC for Foundry ('can read deployments and quota but cannot create or delete them'), hosted agent permissions and the role definition (no deployments/write)",
         "Drawn as cannot deploy; the scenario row is marked 'docs disagree'"],
        [("Owner and Account Owner: role assignments", "orange"),
         "RBAC for Foundry and the role definition: conditional assignment of Foundry User, Container Registry Contributor and Data Access Configuration Administrator, Container Registry Repository Writer, Log Analytics Reader",
         "Hosted agent permissions: Foundry Owner 'can't create role assignments'; Account Owner: Foundry User only",
         "Shown as ABAC-limited. The set excludes Container Registry Repository Reader (AcrPull) and Log Analytics Data Reader: those still need Owner or RBAC Administrator"],
        [("Who may create connections", "orange"), "Add a connection and the administrator guide: Foundry User is allowed", "Hosted agent permissions: Foundry User cannot",
         "Amber circle in matrix B"],
        [("Publish roles", "orange"), "RBAC for Foundry and the administrator guide (Agent Application model): Foundry Project Manager at Foundry resource scope",
         "Publish how-to (agent-endpoint model): Foundry User at project scope plus Azure Bot Service Contributor (Contributor or Owner also work); Foundry roles do not grant Microsoft.BotService writes",
         "Both models noted; the administrator guide itself says the publishing experience is changing"],
        [("Cognitive Services roles", "orange"), "RBAC for Foundry: do not assign Cognitive Services roles except Usages Reader",
         "Entra keyless setup for Foundry Models and the Foundry IQ tutorial assign Cognitive Services User", "Listed as 'docs disagree' in the roles table"],
        [("Role definition text", "orange"), "The built-in Foundry Project Manager definition still says assignments are limited to the 'Cognitive Service User' role",
         "The ABAC condition and the docs say Foundry User", "Drawn as Foundry User only"],
        [("Hosted-agent image pull identity", "orange"), "Hosted agent permissions and hosted agents: the project managed identity needs Container Registry Repository Reader or AcrPull",
         "Private ACR how-to: a per-agent identity is granted AcrPull by azd deploy", "Not drawn here; check which identity pulls in your setup"],
    ], w=W, theme="orange", size=14, head_size=15)
    t.place(cv, 0, top)
    return t.bottom + 70


def build(cv: Canvas) -> None:
    _, bottom = title_block(cv, 0, 0, "Foundry roles, scopes and least-privilege assignments",
                            "Who gets which role at which scope: control plane vs data plane, the scope ladder and capability matrices - as of 2026-11-03",
                            icon="foundry", w=W)
    y = stamps(cv, bottom + 40) + 70
    y = section_roles(cv, y) + 70
    y = section_matrices(cv, y)
    y = section_starter(cv, y) + 70
    y = section_related(cv, y)
    y = section_conflicts(cv, y)
    nxt = Note(W, "Continues in 'Foundry roles, part 2: elevated tasks, feature roles and Azure Policy': the tasks that force Owner or User Access Administrator, the extra roles "
                  "each feature needs, the roles the project managed identity holds on backing resources and the Azure Policy guardrails that sit beside RBAC. "
                  "See also: 'Authentication and authorization map' (identity types, token audiences, control vs data plane), 'Agent identity and delegation' "
                  "(Entra Agent ID, endpoint authorization schemes, the UserIdentityImpersonation custom role) and 'Network isolation'.",
               kind="key", title="Continue in this series", size=16)
    nxt.place(cv, 0, y)
    y = nxt.bottom + 60
    sources(cv, 0, y, [
        ("Role-based access control for Microsoft Foundry", L("concepts/rbac-foundry")),
        ("Foundry administrator guide", L("concepts/administrator-guide")),
        ("Built-in roles: AI + machine learning", L("role-based-access-control/built-in-roles/ai-machine-learning", base="azure")),
        ("Hosted agent permissions", L("agents/concepts/hosted-agent-permissions")),
        ("Authentication and authorization in Foundry", L("concepts/authentication-authorization-foundry")),
        ("Create projects", L("how-to/create-projects")),
        ("Add a connection to a project", L("how-to/connections-add")),
        ("Publish agents to Teams and Microsoft 365", L("agents/how-to/publish-copilot")),
        ("Standard agent setup", L("agents/concepts/standard-agent-setup")),
        ("Use your own resources with Agent Service", L("agents/how-to/use-your-own-resources")),
        ("Azure OpenAI roles (Foundry classic)", L("openai/how-to/role-based-access-control", base="azure/foundry-classic")),
        ("Agent environment setup", L("agents/environment-setup")),
    ], w=W, cols=3)
