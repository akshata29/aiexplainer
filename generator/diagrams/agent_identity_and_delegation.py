"""Agent identity and delegation - who is the caller at each hop (Entra Agent ID, endpoint auth, delegation, consent)."""
from generator.xd import *
from generator.xd import metrics

META = dict(
    id="agent-identity-and-delegation", title="Agent identity and delegation", section="5", order=3,
    description="Entra Agent ID (blueprint + per-agent identity), endpoint authorization schemes, user delegation and consent, "
                "the hosted-agent token service and per-user session isolation - who is the caller at each hop.",
    tags=["entra-agent-id", "delegation", "obo", "consent", "least-privilege"],
)

COL, GAP = 520, 48          # six 520 px columns -> 3360 px canvas


def span(n: int) -> int:
    return n * COL + (n - 1) * GAP


def colx(i: int) -> int:
    return i * (COL + GAP)


W = span(6)
HALF = span(3)
GRAPE, RED = THEMES["grape"], THEMES["red"]


# ---------------------------------------------------------------------------------------------- local helpers
def kv_block(cv, x, y, w, rows, *, label_w=124, size=16, theme="gray", gap=9) -> float:
    """label / value rows; returns the bottom y."""
    th = THEMES[theme]
    cy = y
    for label, value in rows:
        lines = wrap_text(value, (w - label_w) * 0.965, size)
        cv.text(x, cy + 1, label, size=size - 1, color=th.deep)
        cv.text(x + label_w, cy, "\n".join(lines), size=size, color=INK)
        cy += max(len(lines) * size * 1.25, (size - 1) * 1.25) + gap
    return cy - gap


class CodeBlock(Rect2):
    """Monospace snippet in a soft rounded box (Excalifont has no code face, so Comic Shanns is used)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=14, pad=14, dash="solid", src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title, self.dash = w, size, pad, title, dash
        inner = (w - 2 * pad) * 0.965
        self.lines: list[str] = []
        for ln in lines:
            if metrics.line_width(ln, size, MONO) <= inner:
                self.lines.append(ln)      # keep leading spaces: wrap_text would collapse them
            else:
                self.lines += wrap_text(ln, inner, size, MONO)
        self.lh = size * metrics.line_ratio(MONO)
        self.t_h = (17 * 1.25 + 6) if title else 0
        self.src = list(src)
        self.src_h = (8 + len(self.src) * 15) if self.src else 0
        self.h = pad * 2 + self.t_h + len(self.lines) * self.lh + self.src_h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=2, dash=self.dash)
            ty = y + self.pad
            if self.title:
                cv.text(x + self.pad, ty, self.title, size=17, color=self.th.deep)
                ty += self.t_h
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=MONO)
            sy = ty + len(self.lines) * self.lh + 8
            for label, url in self.src:
                cv.text(x + self.pad, sy, f"Learn: {label}", size=12, color=LINK, link=url)
                sy += 15
        cv.register("code", x, y, self.w, H)
        return self


def cite(cv, x, y, items) -> float:
    """Clickable 'Learn:' lines under a table or diagram; returns the bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 2
    return y


def steps_list(cv, x, y, w, steps, *, theme="blue", size=15, gap=12, d=28) -> float:
    """Numbered vertical list (numbered circle + wrapped text); returns the bottom y."""
    cy = y
    for i, s in enumerate(steps, 1):
        lines = wrap_text(s, (w - d - 14) * 0.965, size)
        h = max(len(lines) * size * 1.25, d)
        numbered(cv, x + d / 2, cy + d / 2, i, theme=theme, d=d, size=15)
        cv.text(x + d + 12, cy + (h - len(lines) * size * 1.25) / 2, "\n".join(lines), size=size, color=INK)
        cy += h + gap
    return cy - gap


def boundary_panel(cv, x, y, w, n, title, theme, left, right, edge, rows):
    """One of the three boundaries: actor -> actor with the authorization named on the arrow, then Q/A rows."""
    bw = 360
    with cv.panel(x, y, title=f"B{n}  {title}", theme=theme, style="solid", fill="soft", pad=22, title_size=26, w=w) as p:
        a = Box(bw, left[0], h=96, theme=left[1], icon=left[2], icon_pos="left", sub=left[3], fill="solid")
        b = Box(bw, right[0], h=96, theme=right[1], icon=right[2], icon_pos="left", sub=right[3], fill="solid")
        a.place(cv, p.ix, p.iy + 4)
        b.place(cv, p.ix + (w - 44) - bw, p.iy + 4)
        connect(cv, a, b, label=edge, label_size=15, label_wrap=250, sw=3, color=THEMES[theme].stroke)
        kv_block(cv, p.ix, p.iy + 96 + 34, w - 44, rows, theme=theme)
    return p


# ---------------------------------------------------------------------------------------------- section 1
def sec_boundaries(cv, y):
    right, bottom = section_header(cv, 0, y, "Three boundaries, one request",
                                   sub="Each boundary asks a different question and has its own identity and authorization", size=32)
    top = bottom + 34
    pw = span(2)
    p1 = boundary_panel(
        cv, colx(0), top, pw, 1, "Developer or admin -> Foundry management", "grape",
        ("Developer / admin", "gray", "users", "creates and configures"),
        ("Foundry resource, project, agent", "grape", "foundry", "management surface"),
        "Azure RBAC: actions and dataActions",
        [("Asks", "Who may create, configure, update or delete projects, agents and other resources?"),
         ("Identity", "User, service principal or managed identity"),
         ("Authorized by", "Azure RBAC: management actions and data actions"),
         ("Configure with", "Foundry RBAC role assignments at resource, project or agent scope")])
    p2 = boundary_panel(
        cv, colx(2), top, pw, 2, "Caller -> agent endpoint", "green",
        ("Caller", "gray", "app", "user, app, workload or channel"),
        ("Agent endpoint", "green", "agent", "stable URL per agent"),
        "endpoint authorization scheme",
        [("Asks", "Who may call the agent at runtime?"),
         ("Identity", "User, application or workload token, or a Teams / Microsoft 365 channel request"),
         ("Authorized by", "The scheme: AzureRbac, AgentBlueprint (preview) or a Bot Service scheme"),
         ("Configure with", "authorization_schemes on the agent endpoint")])
    p3 = boundary_panel(
        cv, colx(4), top, pw, 3, "Agent -> tool or downstream resource", "orange",
        ("Agent", "green", "agent", "Agent Service acts for it"),
        ("Tool or resource", "orange", "mcp", "MCP, A2A, Azure data plane..."),
        "tool connection authType",
        [("Asks", "Which identity does the tool call carry: agent, project, user, stored credential or none?"),
         ("Identity", "Agent identity, project managed identity, the user, an API key or OAuth session, or none"),
         ("Authorized by", "The downstream service's own model: Azure RBAC, data-plane roles, app roles, ACLs"),
         ("Configure with", "The tool or connection auth type, per tool")])
    bot = max(p1.bottom, p2.bottom, p3.bottom)
    n1 = Note(span(4), "A principal that may manage an agent is not automatically authorized to call it, and an agent's access to a "
                       "downstream resource does not let callers reach the agent. Check each boundary on its own.",
              kind="gotcha", title="Permissions never carry across boundaries", title_size=22, size=16,
              src=[("Identity and access in Agent Service", learn("agents/concepts/identity-access-overview"))])
    n1.place(cv, 0, bot + 30)
    n2 = Note(span(2), "Support differs per tool, protocol and channel - never assume every tool supports every authentication method.",
              kind="warn", title="Check each tool", size=16)
    n2.place(cv, colx(4), bot + 30, h=n1.h)
    return max(n1.bottom, n2.bottom)


# ---------------------------------------------------------------------------------------------- section 2
def sec_object_model(cv, y):
    right, bottom = section_header(cv, 0, y, "Who is the agent? Microsoft Entra Agent ID in Foundry",
                                   sub="Every new agent gets its own blueprint and identity - nothing is shared, nothing is granted", size=32)
    top = bottom + 34
    bw, bh, rg = 440, 92, 22
    with cv.panel(0, top, title="Foundry project", sub="what developers create", theme="green", style="dashed", fill="soft",
                  pad=22, title_size=24, sub_size=14, w=bw + 44) as fp:
        ys = [fp.iy + k * (bh + rg) for k in range(4)]
        a1 = Box(bw, "Agent A (new)", sub="agent.identity is set", theme="green", icon="agent", icon_pos="left", h=bh).place(cv, fp.ix, ys[0])
        a2 = Box(bw, "Agent B (new)", sub="agent.identity is set", theme="green", icon="agent", icon_pos="left", h=bh).place(cv, fp.ix, ys[1])
        a3 = Box(bw, "Legacy agents", sub="agent.identity is null", theme="gray", icon="agent", icon_pos="left", h=bh,
                 dash="dashed").place(cv, fp.ix, ys[2])
        a4 = Box(bw, "Project managed identity", sub="SMI or UMI; platform use only", theme="red", icon="managed-identity",
                 icon_pos="left", h=bh).place(cv, fp.ix, ys[3])
    ex = fp.right + 160
    ew = HALF - ex
    with cv.panel(ex, top, title="Microsoft Entra tenant", sub="Agent ID objects - one inventory next to Copilot Studio agents",
                  theme="red", style="solid", fill="soft", pad=22, title_size=24, sub_size=14, w=ew) as ep:
        bw2 = 392
        gx = ep.ix + (ew - 44) - bw2
        b1 = Box(bw2, "Blueprint A", sub="parent + template", theme="red", icon="app-registrations", icon_pos="left", h=bh).place(cv, ep.ix, ys[0])
        i1 = Box(bw2, "Agent identity A", sub="default instance - no permissions", theme="red", icon="managed-identity", icon_pos="left",
                 h=bh, fill="hatch").place(cv, gx, ys[0])
        b2 = Box(bw2, "Blueprint B", sub="parent + template", theme="red", icon="app-registrations", icon_pos="left", h=bh).place(cv, ep.ix, ys[1])
        i2 = Box(bw2, "Agent identity B", sub="default instance - no permissions", theme="red", icon="managed-identity", icon_pos="left",
                 h=bh, fill="hatch").place(cv, gx, ys[1])
        b3 = Box(bw2, "Shared project blueprint", sub="legacy", theme="gray", icon="app-registrations", icon_pos="left", h=bh,
                 dash="dashed").place(cv, ep.ix, ys[2])
        i3 = Box(bw2, "Shared project identity", sub="legacy; shared by every legacy agent", theme="gray", icon="managed-identity",
                 icon_pos="left", h=bh, dash="dashed").place(cv, gx, ys[2])
        connect(cv, b1, i1, label="parent may impersonate", label_size=15, label_wrap=190, sw=3, color="#e03131")
        connect(cv, b2, i2, sw=3, color="#e03131")
        connect(cv, b3, i3, dash="dashed", sw=3, color="#868e96")
    connect(cv, a1, b1, label="creating an agent provisions both", label_size=14, label_wrap=140, sw=3, color="#2f9e44", a_side="right", b_side="left")
    connect(cv, a2, b2, sw=3, color="#2f9e44", a_side="right", b_side="left")
    connect(cv, a3, b3, dash="dashed", sw=3, color="#868e96", a_side="right", b_side="left")
    with cv.panel(ex, ys[3] - 18, theme="gray", style="dotted", pad=18, w=ew) as ip:
        infra = Box(ew - 36, "Platform infrastructure: ACR image pull, Application Insights ingestion, BYO resources, project-MI tool connections",
                    theme="gray", h=bh - 10, fill="soft", size=16).place(cv, ip.ix, ip.iy + 5)
    connect(cv, a4, infra, dash="dashed", sw=3, color="#c92a2a", a_side="right", b_side="left",
            label="not for agent code", label_size=14, label_wrap=140)
    diag_bottom = max(ep.bottom, ip.bottom, fp.bottom)

    # who-is-who table (right half)
    t = Table(
        [("Identity", 230), ("What it is", 600), "Used for"],
        [
            ["Agent identity", "Special service principal under a blueprint; one per agent instance",
             "Downstream tool and resource access; hosted code reaches it through the token service"],
            ["Agent identity blueprint", "Parent and template for agent identities; holds the OAuth credential",
             "Provisions identities; optional inbound sign-in audience (AgentBlueprint scheme, preview)"],
            ["Project managed identity", "System- or user-assigned MI of the project; a UMI can only be set at project creation",
             "Infrastructure: ACR pull, App Insights ingestion, BYO resources, project-MI tool connections. Not available to hosted-agent code"],
            ["Shared project identity (legacy)", "Project-level blueprint + identity used by legacy agents (agent.identity is null)",
             "Permissions on it do not transfer to new agents; deleting the project deletes it"],
            ["Agent Application identity (legacy)", "Distinct identity created when a legacy agent was published as an Agent Application",
             "Deleted with the application; its roles do not transfer to the new agent object"],
            ["Agent user account", "Entra user object, autopilot agents only",
             "Mailbox, calendar, OneDrive, Teams presence, org-chart slot - Microsoft 365 actions as itself"],
        ], w=HALF, theme="red", size=14, head_size=15, first_col_theme="red", title="Which identity is used for what", title_size=22)
    t.place(cv, colx(3), top)
    cite(cv, t.x, t.bottom + 6, [("Agent identity concepts", learn("agents/concepts/agent-identity")),
                                 ("Migrate from Agent Applications", learn("agents/how-to/migrate-agent-applications"))])
    c_types = Table(
        [("Agent type", 200), ("Identity it uses", 450), "Notes"],
        [
            [("Assistive", "green"), "Agent identity + the signed-in user's context", "Acts with the user present"],
            [("Background service", "green"), "Agent identity, application-only", "No Microsoft 365 actions"],
            [("Autopilot", "green"), "Agent identity + an agent user account",
             "One blueprint, many hired instances - each with its own identity, permissions and assignment. Only hosted agents can be "
             "published as autopilot blueprints; needs a Microsoft 365 Copilot license and the Frontier preview program (check docs)"],
        ], w=HALF, theme="green", size=14, head_size=15, title="Three kinds of agent (Entra Agent ID)", title_size=20)
    c_types.place(cv, colx(3), t.bottom + 68)
    cite(cv, c_types.x, c_types.bottom + 6, [("Autopilot overview", learn("agents/concepts/autopilot-overview"))])
    y_next = max(diag_bottom, c_types.bottom + 22) + 44

    # fact cards
    c_bp = Card(COL, "Blueprint = the parent", [
        "Template and parent for agent identities; container for identity admin",
        "Holds the OAuth client ID, credentials and the AgentIdentity.CreateAsManager Graph permission",
        "Can do exactly one thing in a tenant: provision and deprovision agent identities",
        "Conditional Access on a blueprint applies to all of its identities",
        "Disabling a blueprint stops all its identities from authenticating",
        "Holds requiredResourceAccess and inheritablePermissions declarations",
    ], theme="red", icon="app-registrations", src=[("Agent identity blueprints (Entra)", learn("entra/agent-id/agent-blueprint", base=""))])
    c_id = Card(COL, "Agent identity = the instance", [
        "Represents the agent instance when it calls downstream resources",
        "The parent blueprint is authorized to impersonate it",
        "Starts with NO permissions - Foundry never auto-assigns RBAC to it",
        "Grant access through the target service's own model, using the identity's object ID",
        "Same model for text and voice prompt agents",
        "No identity change at publish time",
    ], theme="red", icon="managed-identity", src=[("Agent identity concepts", learn("agents/concepts/agent-identity"))])
    c_trust = Card(COL, "How Foundry holds the credential", [
        "A federated identity credential on the blueprint trusts the first-party 'Azure Machine Learning' resource provider app",
        "App ID 0736f41a-0425-4b46-bdb5-1563eff02385 - not 'Azure Machine Learning Services' (the portal sign-in principal)",
        "Trusted only when acting in your tenant; no client secret or certificate",
        "Projects, agent code and the project MI never hold it",
    ], theme="red", icon="key-vault", src=[("Agent identity concepts", learn("agents/concepts/agent-identity"))])
    c_own = Card(COL, "Owners, sponsors, managers", [
        "Owners: technical admins (users or service principals, not groups); can re-enable, restore and hard-delete",
        "Sponsors: required on every agent identity and blueprint; business accountability; can disable or soft-delete, cannot re-enable",
        "Sponsors may be users and dynamic or M365-assigned groups; max 100 including at most 5 groups",
        "Managers: reporting hierarchy for agent user accounts",
    ], theme="red", icon="groups", src=[("Owners, sponsors, managers", learn("entra/agent-id/agent-owners-sponsors-managers", base=""))])
    c_audit = Card(span(2), "Monitor and audit agent identity activity", [
        "Entra admin center: tenant-wide inventory next to Copilot Studio agents; Conditional Access, Identity Protection, network access, expiry, owners, sponsors",
        "Sign-in logs: filter by agent type (blueprint, agent identity or the agent's user account); show which identity got a token for which resource, and for which user",
        "Audit logs: blueprint and identity creation and deletion; agentType names the object, blueprintId ties an identity to its blueprint",
        "Foundry tracing: tool calls per agent in the Application Insights resource connected to the project",
    ], theme="red", icon="identity-protection", src=[("Agent identity concepts", learn("agents/concepts/agent-identity"))])
    c_ext = Note(span(2), "Agent identity authentication does not change an external tool provider's data handling or retention. Calls to "
                          "non-Microsoft tools can send data outside Microsoft services - review and log that access.",
                 kind="warn", title="External tools", size=15)
    four = [c_bp, c_id, c_trust, c_own]
    rowh = max(max(c.h for c in four), c_audit.h + 24 + c_ext.h)
    for i, c in enumerate(four):
        c.place(cv, colx(i), y_next, h=rowh)
    ah = rowh - 24 - c_ext.h
    c_audit.place(cv, colx(4), y_next, h=ah)
    c_ext.place(cv, colx(4), y_next + ah + 24)
    return y_next + rowh


# ---------------------------------------------------------------------------------------------- section 3
def cutover_diagram(cv, x, y, w):
    """Entra-state enforcement: legacy exception before the cut-over, enforced after it."""
    half = (w - 70) / 2
    left = Card(half, "Created BEFORE 2026-10-23 16:00 UTC", [
        "Bypass Entra-state enforcement, whatever their developer configuration or Entra state at the cut-over",
        "Can run with a disabled Entra state while developer configuration is enabled",
        "Developer disable still stops them; a later Entra block or delete does not",
        "Reconciling Entra state does not end the exception",
    ], theme="yellow", subtitle="earlier agents: legacy exception",
        src=[("Manage agent availability as an administrator", learn("control-plane/govern-agent-infrastructure-entra-admin"))])
    right_c = Card(half, "Created ON or AFTER 2026-10-23 16:00 UTC", [
        "An Entra Block, SoftDelete or HardDelete stops the agent even if developer configuration is enabled",
        "Effective state = developer configuration AND Entra admin state",
        "Developer Enable does not override an Entra block; Unblock alone does not enable a developer-disabled agent",
        "A change takes up to 10 minutes to show",
    ], theme="red", subtitle="newer agents: enforced")
    row(cv, x, y, [left, right_c], gap=70)
    ay = left.bottom + 62
    mid = x + half + 35
    arrow(cv, [(x, ay), (x + w, ay)], sw=3, start_head=None, end_head="arrow", color=INK)
    cv.line((mid, left.bottom + 14), (mid, ay + 26), stroke="#c92a2a", sw=3, dash="dashed")
    cv.text(mid - 150, ay + 32, "2026-10-23 16:00 UTC - cut-over", size=17, color="#c92a2a", align="center", w=300)
    tx = x + w - 230
    cv.ellipse(tx - 8, ay - 8, 16, 16, stroke="#2f9e44", fill="#b2f2bb", style="solid", sw=2, rough=0)
    cv.text(tx - 110, ay + 18, "Today: 2026-11-03", size=17, color="#2b8a3e", align="center", w=220)
    cv.text(x, ay - 30, "agent creation time", size=14, color=MUTED)
    return ay + 56


def sec_migration(cv, y):
    right, bottom = section_header(cv, 0, y, "From the shared legacy identity to one identity per agent - and the admin kill-switch",
                                   sub="Migration steps, the three agent types, effective state and the enforcement cut-over (as of 2026-11-03 the cut-over has passed)",
                                   size=32)
    top = bottom + 38
    sw = (HALF - 3 * 56) / 4
    steps = [
        Card(sw, "Check the agent", [
            "GET {endpoint}/agents/{agent_name} (preview API)",
            "instance_identity is null: legacy agent on the shared project identity and blueprint",
            "Non-null: new agent with its own blueprint and default-instance identity",
        ], theme="gray", icon="search"),
        Card(sw, "Create a new agent", [
            "Same definition: instructions, tools, model configuration",
            "No in-place upgrade yet - the docs call the upgrade gesture 'coming soon' (as of 2026-11-03)",
            "The new agent gets a unique identity and a stable endpoint at creation; no separate publish step",
        ], theme="green", icon="agent"),
        Card(sw, "Re-grant downstream RBAC", [
            "Roles on the shared project identity or an Agent Application identity do not transfer",
            "Assign least-privilege roles to the NEW agent identity; remove what is not needed",
            "azd gave the shared identity Foundry User for compatibility - it grants nothing on ACR, App Insights or custom resources",
        ], theme="red", icon="managed-identity"),
        Card(sw, "Re-point clients, then publish", [
            "Client roles scoped to the Agent Application: re-assign at project or agent scope (Foundry Agent Consumer)",
            "Switch URLs to the agent's stable endpoint",
            "Publish to Microsoft 365 and Teams from the portal (no public publish API); then delete the old Agent Application - agent versions stay",
        ], theme="green", icon="teams"),
    ]
    row(cv, 0, top, steps, gap=56)
    for i, c in enumerate(steps):
        numbered(cv, c.x + 20, c.y - 2, i + 1, theme=c.th.name, d=34, size=18)
    for a, b in zip(steps, steps[1:]):
        connect(cv, a, b, sw=3, color="#495057")
    yl = max(c.bottom for c in steps) + 46
    cv.text(0, yl, "When does an Entra block stop an agent?", size=24, color=GRAPE.deep)
    yl = cutover_diagram(cv, 0, yl + 42, HALF) + 34
    cv.text(0, yl, "Kill-switch in four steps", size=24, color=GRAPE.deep)
    fw = (HALF - 3 * 72) / 4
    flow2 = [
        Box(fw, "Entra admin, owner or sponsor blocks or soft-deletes the blueprint or identity", theme="grape", icon="identity-governance", icon_pos="left", h=116, size=15),
        Box(fw, "Entra status of the object becomes disabled", theme="red", icon="managed-identity", icon_pos="left", h=116, size=15),
        Box(fw, "Foundry shows state=disabled and state_source within 10 minutes", theme="green", icon="foundry", icon_pos="left", h=116, size=15),
        Box(fw, "Runtime stops serving the agent; developer Enable does not override", theme="gray", icon="agent", icon_pos="left", h=116, size=15),
    ]
    fx = 0
    for b in flow2:
        b.place(cv, fx, yl + 42)
        fx += b.w + 72
    for i, (a, b) in enumerate(zip(flow2, flow2[1:])):
        connect(cv, a, b, sw=3, color="#862e9c", num=i + 1, num_theme="grape")
    yl = flow2[0].bottom + 46
    em = Card(HALF, "Emergency path: Azure infrastructure actions", [
        "Prefer Agent 365 or Entra actions - they keep the agent definition and the Azure infrastructure",
        "Infrastructure actions hit every consumer of the resource, including other tenants: disable or enable a Foundry agent endpoint (Foundry User); stop or start an Agent Application's deployments (Foundry Owner)",
        "Entra roles and owner or sponsor status grant no Azure access; a Global Administrator can elevate to User Access Administrator at root scope and must de-elevate afterwards",
        "Assign roles at the narrowest scope - never subscription or management group; prefer PIM-eligible assignments",
    ], theme="grape", icon="policy", src=[("Manage agent availability as an administrator", learn("control-plane/govern-agent-infrastructure-entra-admin"))])
    em.place(cv, 0, yl)
    left_bottom = em.bottom

    # right column --------------------------------------------------------------------------------
    rx = colx(3)
    t_types = Table(
        [("Type", 220), ("agent.identity", 190), "What it is"],
        [
            [("New agent", "green"), "non-null",
             "Created after the object-model update. Unique identity and blueprint; all new features available."],
            [("Legacy agent", "gray"), "null",
             "Created before the update. Uses the shared project identity and blueprint; backfilled with agent_endpoint, protocol_configuration and "
             "agent_card, but cannot be published to Teams or Microsoft 365 through its stable endpoint without a unique identity."],
            [("Published agent (Agent Application)", "orange"), "n/a - separate resource",
             "Legacy resource from the old publish flow; wraps a Deployment that points to an agent version. Has its own identity, deleted with the application."],
        ], w=HALF, theme="gray", size=14, head_size=15, title="Three kinds of agent during the transition", title_size=20)
    t_types.place(cv, rx, top - 6)
    yr = cite(cv, rx, t_types.bottom + 6, [("Migrate from Agent Applications", learn("agents/how-to/migrate-agent-applications"))]) + 30
    url = CodeBlock(HALF, [
        "Responses  legacy: https://{account}.../projects/{project}/applications/{app}/protocols/openai",
        "           new:    https://{account}.../projects/{project}/agents/{agent}/endpoint/protocols/openai/responses",
        "Activity   legacy: https://{account}.../projects/{project}/applications/{app}/protocols/activityprotocol",
        "           new:    https://{account}.../projects/{project}/agents/{agent}/endpoint/protocols/activityprotocol",
    ], title="Endpoint URLs change with the new agent model", theme="gray", size=14)
    url.place(cv, rx, yr)
    yr = url.bottom + 28
    cv.text(rx, yr, "Migration status on the Learn page (as of 2026-11-03)", size=16, color=MUTED)
    flow = ChipFlow([Chip("New agent object model: available", theme="green", size=15),
                     Chip("Legacy Agent Applications keep working", theme="green", size=15),
                     Chip("Identity upgrade gesture: coming soon", theme="yellow", size=15),
                     Chip("Agent Application deprecation: planned", theme="yellow", size=15),
                     Chip("End of support: TBD", theme="gray", size=15)], HALF, gap=10)
    flow.place(cv, rx, yr + 28)
    yr = flow.y + flow.h + 46
    t_act = Table(
        [("Action", 125), ("Agent 365 / Entra label", 285), "Runtime effect", ("Undo with", 150), ("Owner", 80), ("Sponsor", 90)],
        [
            [("Block", "red"), "Block / Disable in this tenant", "Disables the agent", "Unblock", CHECK, CHECK],
            [("Unblock", "green"), "Unblock / Enable", "Removes the restriction; developer configuration still controls enablement", "Block again", CHECK, CROSS],
            [("SoftDelete", "red"), "Delete / Delete", "Disables the agent", "Restore", CHECK, CHECK],
            [("Restore", "green"), "Restore agent / Restore agent", "Removes the deletion restriction; developer configuration still controls enablement", "Soft-delete again", CHECK, CROSS],
            [("HardDelete", "red"), "Permanently delete / Delete permanently", "Disables the agent permanently", "Not recoverable", CHECK, CROSS],
        ], w=HALF, theme="grape", size=14, head_size=15, align=["left", "left", "left", "left", "center", "center"],
        title="Five governance actions and who may run them", title_size=20)
    t_act.place(cv, rx, yr)
    yr = cite(cv, rx, t_act.bottom + 6, [("Manage agent availability as an administrator", learn("control-plane/govern-agent-infrastructure-entra-admin"))])
    yr = cv.text(rx, yr + 4, "Tenant-wide: Entra AI Administrator or Global Administrator (activate the role first if you use PIM).",
                 size=15, color=INK).bottom + 36
    t_eff = Table(
        [("Developer configuration", 270), ("Entra admin state", 270), "Runtime state"],
        [
            [("Enabled", "green"), "Permits operation", ("Enabled", "green")],
            [("Enabled", "green"), "Blocks operation", ("Disabled", "red")],
            [("Disabled", "red"), "Permits operation", ("Disabled", "red")],
            [("Disabled", "red"), "Blocks operation", ("Disabled", "red")],
        ], w=HALF, theme="grape", size=14, head_size=15, title="Effective state under normal enforcement (the agent's state)", title_size=20)
    t_eff.place(cv, rx, yr)
    yr = t_eff.bottom + 8
    nt = Note(HALF, "Properties: state, state_source (agent_blueprint or agent_instance_identity), configuration_state, instance_identity.status, blueprint.status. "
                    "If an agent should run, Unblock a blocked object or Restore a soft-deleted one; a permanently deleted object cannot be restored - re-provision with a new identity.",
              kind="info", title="Read the state", size=14)
    nt.place(cv, rx, yr + 10)
    return max(left_bottom, nt.bottom)


# ---------------------------------------------------------------------------------------------- section 4
def sec_endpoint_auth(cv, y):
    right, bottom = section_header(cv, 0, y, "B2: who may call the agent? Endpoint authorization schemes",
                                   sub="The token's audience picks the scheme; agent endpoints do not accept API keys; AgentBlueprint is preview as of 2026-11-03",
                                   size=32)
    top = bottom + 38
    cw, sbw, rw = 340, 392, 512
    sx = cw + 190
    rx = sx + sbw + 44 + 190
    bh, rg = 104, 30
    with cv.panel(sx, top, title="Agent endpoint", sub="authorization_schemes[ ] - several can coexist", theme="green", style="dashed",
                  fill="soft", pad=22, title_size=24, sub_size=14, w=sbw + 44) as sp:
        ys = [sp.iy + k * (bh + rg) for k in range(3)]
        s1 = Box(sbw, "AzureRbac (alias Entra)", sub="the default scheme", theme="green", icon="agent", icon_pos="left", h=bh, size=18).place(cv, sp.ix, ys[0])
        s2 = Box(sbw, "AgentBlueprint", sub="per-agent audience; no Foundry role needed", theme="green", icon="agent", icon_pos="left", h=bh, size=18).place(cv, sp.ix, ys[1])
        s3 = Box(sbw, "BotServiceRbac or BotServiceTenant", sub="BotService = legacy compatibility only", theme="green", icon="bot", icon_pos="left", h=bh, size=18).place(cv, sp.ix, ys[2])
    draw_badge(cv, s2.right - 92, s2.y - 13, "preview")
    c1 = Box(cw, "SDKs, apps, dev tools, workloads", sub="token for the Foundry resource", theme="gray", icon="app", icon_pos="left", h=bh).place(cv, 0, ys[0])
    c2 = Box(cw, "A client of this one agent", sub="token for the agent's blueprint", theme="gray", icon="app", icon_pos="left", h=bh).place(cv, 0, ys[1])
    c3 = Box(cw, "Teams and Microsoft 365 users", sub="channel request via Azure Bot Service", theme="gray", icon="teams", icon_pos="left", h=bh).place(cv, 0, ys[2])
    r1 = Box(rw, "Azure RBAC check", sub="endpoints/interact/action at project or agent scope: Foundry Agent Consumer (Foundry User also includes it)",
             theme="red", h=bh).place(cv, rx, ys[0])
    r2 = Box(rw, "Token-validation rules", sub="audience, tenant, client, principal, scope - the caller needs no Foundry role",
             theme="red", h=bh).place(cv, rx, ys[1])
    r3 = Box(rw, "Signed-in user check", sub="Rbac: the user holds the Azure role. Tenant: the user is in the configured tenant (fixed rule)",
             theme="red", h=bh).place(cv, rx, ys[2])
    connect(cv, c1, s1, label="aud: https://ai.azure.com", label_size=14, label_wrap=170, sw=3, color="#495057", b_side="left")
    connect(cv, c2, s2, label="aud: api://<blueprint-client-id>", label_size=14, label_wrap=170, sw=3, color="#495057")
    connect(cv, c3, s3, label="signed channel token", label_size=14, label_wrap=170, sw=3, color="#495057")
    connect(cv, s1, r1, sw=3, color="#e03131")
    connect(cv, s2, r2, sw=3, color="#e03131")
    connect(cv, s3, r3, sw=3, color="#e03131")
    dy = sp.bottom + 26
    cv.text(0, dy, "Direct client token example: scope https://ai.azure.com/.default via get_bearer_token_provider(...). Management calls (GET and PATCH on the agent) always use a Foundry-audience token.",
            size=15, color=MUTED, wrap=HALF)
    diag_bottom = dy + 48

    rtx = colx(3)
    t_rules = Table(
        [("Rule", 230), ("Omitted or null", 760), "Empty array"],
        [
            ["allowed_audiences", "The backing agent blueprint audience", ("Blocks all", "red")],
            ["allowed_tenants", "The blueprint's tenant", ("Blocks all", "red")],
            ["allowed_clients", "Delegated tokens: no restriction. App-only tokens: denied - a non-empty list is required", ("Blocks all", "red")],
            ["allowed_principals", "No restriction", ("Blocks all", "red")],
            ["required_scopes", "Requires access_agent", ("Invalid configuration", "red")],
        ], w=HALF, theme="green", size=14, head_size=15, first_col_theme="green",
        title="AgentBlueprint token-validation rules (preview)", title_size=20)
    t_rules.place(cv, rtx, top)
    yr = cv.text(rtx, t_rules.bottom + 8, "Each rule accepts up to 10 values. Use permission names, not full URIs, in required_scopes.",
                 size=15, color=MUTED).bottom + 2
    yr = cite(cv, rtx, yr + 4, [("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
                                ("Configure agent endpoint authorization", learn("agents/how-to/configure-agent-endpoint-authorization"))]) + 22
    n_patch = Note(HALF, "PATCH replaces the whole authorization_schemes array (application/merge-patch+json). GET the agent first and send back every scheme you want to keep; "
                         "publishing to Teams can replace a different Bot Service scheme.", kind="gotcha", title="PATCH is a replace, not a merge", size=15)
    n_patch.place(cv, rtx, yr)
    n_aud = Note(HALF, "Foundry concept and how-to pages use https://ai.azure.com/.default for Entra tokens, including OpenAI-compatible /openai/v1 calls; the Azure OpenAI v1 "
                       "REST reference lists https://cognitiveservices.azure.com/.default. This canvas draws ai.azure.com.",
                 kind="warn", title="Docs disagree: token audience", size=15,
                 src=[("Authentication and authorization in Foundry", learn("concepts/authentication-authorization-foundry")),
                      ("Azure OpenAI v1 REST reference", learn("rest/api/microsoft-foundry/azureopenai/responses", base=""))])
    n_aud.place(cv, rtx, n_patch.bottom + 20)
    y2 = max(diag_bottom, n_aud.bottom) + 46

    cards = [
        Card(COL, "AgentBlueprint: delegated vs app-only", [
            "# Delegated",
            "The client signs in the user and requests api://<blueprint-client-id>/access_agent (names are customizable defaults)",
            "Foundry preauthorizes first-party clients (portal, CLI, VS Code); customer-owned clients need preauthorization or user or admin consent",
            "# App-only",
            "A confidential client (certificate or federated credential) requests <audience>/.default; no app role needed",
            "allowed_clients must be a non-empty list that contains the caller's app ID",
        ], theme="green", badge="preview", icon="agent", src=[("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))]),
        Card(COL, "Management stays on Foundry access", [
            "GET and PATCH on the agent always use a Foundry-audience token, even when runtime accepts only AgentBlueprint",
            "Foundry dev clients (portal, CLI, VS Code), routine dispatch and Bot Service keep using Foundry access - keep AzureRbac (or Entra) for them",
            "AgentBlueprint does not yet apply to routines, dev clients or Bot Service (preview)",
            "Authorizing a client for the blueprint grants no management access to the project",
        ], theme="grape", icon="gear", src=[("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization"))]),
        Card(COL, "Teams and Microsoft 365 channel", [
            "Publishing sets a Bot Service scheme and uses the agent endpoint's Activity Protocol route",
            "BotServiceRbac: the signed-in user needs the Azure role",
            "BotServiceTenant: the user must be in the configured tenant (People in your organization needs Microsoft 365 admin approval)",
            "Only one of BotService, BotServiceRbac, BotServiceTenant; both new schemes prompt a sign-in in the conversation",
        ], theme="green", icon="teams", src=[("Publish agents to Copilot and Teams", learn("agents/how-to/publish-copilot"))]),
        Card(COL, "Header-based isolation keys", [
            "isolation_key_source.kind is Entra (identity from the token) or Header (a trusted middle tier sends x-ms-user-identity)",
            "With AgentBlueprint, Header isolation accepts only app-only tokens whose app ID is in BOTH isolation_key_source.allowed_clients and token_validation_rules.allowed_clients",
            "Never set both Entra and AzureRbac on one endpoint",
        ], theme="red", icon="key-vault", src=[("Configure agent endpoint authorization", learn("agents/how-to/configure-agent-endpoint-authorization"))]),
    ]
    rowh = max(c.h for c in cards)
    with cv.panel(0, y2, title="Transition: AzureRbac -> AgentBlueprint", sub="keep both schemes until every client has moved",
                  theme="green", style="dotted", fill="none", pad=22, title_size=22, sub_size=14, w=span(2), min_h=rowh) as tp:
        steps_list(cv, tp.ix, tp.iy + 4, span(2) - 44, [
            "Keep AzureRbac on the endpoint",
            "Add AgentBlueprint and its token-validation rules",
            "Read the agent and note blueprint.client_id",
            "Authorize each client to obtain a blueprint token",
            "Test with both token audiences",
            "Move clients to the blueprint audience",
            "Monitor sign-ins and failures",
            "Later - after the preview - remove AzureRbac",
        ], theme="green", size=16, gap=11)
    for i, c in enumerate(cards):
        c.place(cv, colx(2 + i), y2, h=max(rowh, tp.h))
    return max(tp.bottom, y2 + rowh)


# ---------------------------------------------------------------------------------------------- section 5
def sec_downstream(cv, y):
    right, bottom = section_header(cv, 0, y, "B3: what does the agent present downstream - and when does it act for the user?",
                                   sub="The connection authType decides; the downstream service makes the final call. Agent identity acting for users is preview as of 2026-11-03",
                                   size=32)
    top = bottom + 38
    spokes = [
        ("None", "authType none: anonymous - public tools only", "gray", None, "solid"),
        ("API key or custom key", "authType custom-keys: a principal tied to the stored credential. Anyone with project access can read it - store shared secrets only", "yellow", "key", "solid"),
        ("Project managed identity", "authType project-managed-identity: shared, project-level access", "red", "managed-identity", "solid"),
        ("Agent identity", "authType agentic-identity: the agent as an independent principal - roles or app permissions", "red", "managed-identity", "hatch"),
        ("The signed-in user (Entra OBO)", "UserEntraToken or AgentOnBehalfOfUser (preview): user-specific data such as mail, files, records", "red", "user", "solid"),
        ("The signed-in user (OAuth2 passthrough)", "OAuth2: a separate per-connection OAuth session in the conversation", "red", "oauth", "solid"),
    ]
    sx, swd, sh, sg = 470, 760, 86, 20
    total = len(spokes) * sh + (len(spokes) - 1) * sg
    hub = Box(300, "Agent Service reads the tool connection's authType", theme="green", icon="foundry", icon_pos="top", h=190, size=18).place(
        cv, 0, top + (total - 190) / 2)
    boxes = []
    for i, (label, sub, th, ic, fl) in enumerate(spokes):
        b = Box(swd, label, sub=sub, theme=th, icon=ic, icon_pos="left", h=sh, size=18, fill=fl).place(cv, sx, top + i * (sh + sg))
        boxes.append(b)
        connect(cv, hub, b, a_side="right", b_side="left", route="elbow", sw=2.5, color=THEMES[th].stroke if th != "gray" else "#495057")
    brace(cv, sx + swd + 22, top, top + total, side="right", depth=22, color="#495057")
    n_dec = Note(HALF - (sx + swd + 66), "Whatever the credential, the downstream service authorizes it: Azure RBAC, data-plane roles, app roles or its own policies. "
                                          "Grant access to the identity's object ID.",
                 kind="info", title="The service decides", size=15)
    n_dec.place(cv, sx + swd + 66, top + total / 2 - n_dec.h / 2)
    ys2 = top + total + 54
    cv.text(0, ys2, "Service-managed tool call with the agent identity: the four-stage token exchange", size=22, color=RED.deep)
    seq = Sequence(cv, 0, ys2 + 40, [("Agent Service", "green", "foundry"), ("Microsoft Entra ID", "red", "app-registrations"),
                                     ("MCP or A2A endpoint", "orange", "mcp")], spacing=480, head_w=220, label_size=15)
    seq.msg(0, 1, "present the blueprint's OAuth credential (proves Agent Service may act for the blueprint)", num=1)
    seq.msg(1, 0, "agent identity token - the agent as an independent actor", dash="dashed")
    seq.msg(0, 1, "present that token; ask for an access token scoped to the downstream audience", num=2)
    seq.msg(1, 0, "scoped access token", dash="dashed")
    seq.msg(0, 2, "call the tool with the scoped token", num=3)
    seq.note(1, 2, "The downstream resource validates the token and checks the agent identity's RBAC assignments", kind="info", size=15)
    sbot = seq.end()
    n_aud = Note(HALF - 1240 - 40, "The audience is the OAuth resource identifier (for example https://storage.azure.com) - not necessarily the tool URL. "
                                  "Authenticating does not by itself grant access.", kind="tip", title="Audience", size=15,
                 src=[("Agent identity concepts", learn("agents/concepts/agent-identity"))])
    n_aud.place(cv, 1240 + 40, ys2 + 60)
    left_bottom = sbot

    # ---- right column
    rx = colx(3)
    t_auth = Table(
        [("authType", 250), ("Behaviour", 650), "Needs"],
        [
            [("UserEntraToken", "red"), "Conditional actor by the incoming token's audience: a Foundry-audience token means Foundry acts for the user (limited Microsoft-owned tools, no extra consent); a blueprint-audience token means the agent identity acts",
             "Works under AzureRbac or AgentBlueprint; omit scopes to use the target's defaults; not for custom or third-party servers"],
            [("AgentOnBehalfOfUser (preview)", "orange"), "The agent identity is always the actor",
             "Endpoint must use AgentBlueprint; explicit fully-qualified scopes for ONE resource; the way to do OBO to a custom MCP server; not available under AzureRbac or Entra"],
            [("OAuth2 (OAuth identity passthrough)", "red"), "A separate OAuth session per connection, in the conversation",
             "Managed OAuth (connectorName) or custom (clientId, clientSecret, authorizationUrl, tokenUrl, refreshUrl, scopes including offline_access)"],
        ], w=HALF, theme="red", size=14, head_size=15, title="Acting for the user: three connection authTypes", title_size=20)
    t_auth.place(cv, rx, top - 6)
    yr = cite(cv, rx, t_auth.bottom + 6, [("User delegation for tools", learn("agents/concepts/user-delegation")),
                                           ("Configure user delegation", learn("agents/how-to/configure-user-delegation"))]) + 24
    cards = [
        Card(COL, "OAuth2 facts", [
            "Agent Service stores and refreshes the credentials, partitioned by user + connection",
            "Consumers need at least Foundry Agent Consumer",
            "The user's Entra tenant must equal the project tenant - no cross-tenant exchange",
            "A service serving many users must set x-ms-user-identity per user so OAuth state is not shared",
            "The client app must be able to surface the sign-in request",
        ], theme="red", icon="oauth"),
        Card(COL, "Foundry IQ source authorization", [
            "Agent Service dynamically sets the header x-ms-query-source-authorization with the user's AI Search token",
            "The knowledge base then enforces source permissions - for both token audiences",
            "For the blueprint audience it requests https://search.azure.com/user_impersonation",
        ], theme="teal", icon="ai-search"),
        Card(COL, "Toolbox: two identities per call", [
            "agent -> toolbox: the agent identity gates the toolbox itself; tool -> data: a per-user credential",
            "Hosted agents use FoundryToolbox (Python) or AddFoundryToolboxes (.NET) to forward x-agent-foundry-call-id",
            "Direct toolbox clients (no Foundry agent): no blueprint sign-in and no AgentOnBehalfOfUser - use per-tool OAuth2",
        ], theme="orange", icon="toolbox"),
    ]
    rowh = max(c.h for c in cards)
    for i, c in enumerate(cards):
        c.place(cv, colx(3 + i), yr, h=rowh)
    yr += rowh + 40
    t_sc = Table(
        [("Delegated target", 400), "Scope the connection requests"],
        [
            ["Azure Databricks Genie MCP", "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/user_impersonation"],
            ["Azure DevOps MCP", "api://2a72489c-aab2-4b65-b93a-a91edccf33b8/Ado.Mcp.Tools"],
            ["Fabric data agent", "https://analysis.windows.net/powerbi/api/DataAgent.Execute.All"],
            ["Fabric ontology", "https://analysis.windows.net/powerbi/api/Item.Execute.All and .../Item.Read.All"],
            ["Power BI semantic model", "https://analysis.windows.net/powerbi/api/Item.Read.All, .../Item.Execute.All and .../Dataset.Read.All"],
            ["Foundry MCP", "https://mcp.ai.azure.com/Foundry.Mcp.Tools"],
            ["Dataverse", "api://ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/McpServers.Dataverse.All"],
            ["Sentinel (Data Exploration, Graph, Knowledge Objects, Memory)", "4500ebfb-89b6-4b14-a480-7f749797bfcd/.default"],
            ["Work IQ Calendar, Copilot, Mail, OneDrive, SharePoint, Teams, User, Word",
             "api://ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/McpServers.<Calendar|CopilotMCP|Mail|OneDrive|SharePoint|Teams|Me|Word>.All"],
            ["Work IQ MCP (AgentOnBehalfOfUser only)", "api://workiq.svc.cloud.microsoft/WorkIQAgent.Ask"],
        ], w=HALF, theme="red", size=14, head_size=15, first_col_theme="red", title="Supported delegated targets and scopes", title_size=20)
    t_sc.place(cv, rx, yr)
    cite(cv, rx, t_sc.bottom + 6, [("Configure user delegation", learn("agents/how-to/configure-user-delegation"))])
    return max(left_bottom, t_sc.bottom + 24)


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Agent identity and delegation",
                                "Who is the caller at each hop - Entra Agent ID, endpoint authorization, acting for the user, consent", w=W)
    legend(cv, 0, bottom + 18, [("agents", "green"), ("identity / security", "red"), ("tools", "orange"),
                                ("governance / control plane", "grape"), ("data / storage", "cyan"), ("observability", "violet")])
    y = bottom + 76
    y = sec_boundaries(cv, y) + 68
    y = sec_object_model(cv, y) + 68
    y = sec_migration(cv, y) + 68
    y = sec_endpoint_auth(cv, y) + 68
    y = sec_downstream(cv, y) + 68
