"""Publishing and channels (Agent Service), part 2: Microsoft Agent 365 (registry sync, telemetry permission) and autopilots - identity-based
'digital coworkers': why they exist, one blueprint -> many hired instances, the eight-stage lifecycle as a swimlane, onboarding and operating
an instance, and the first-autopilot quickstart (licensing, permissions, publish fields).

Part 1 ('publish-and-channels') covers the endpoint, channel map, authorization, identity, publishing to Microsoft 365 and Teams.
Frontier-preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import Note as _KitNote

META = dict(
    id="publish-and-channels-part-2", title="Agent 365 and autopilots: identity-based digital coworkers", section="2", group="Agent Service", order=16.5,
    description="Microsoft Agent 365 registry sync and telemetry, and autopilots - an identity, not a capability: one blueprint to many hired instances, "
                "the eight-stage lifecycle across four roles, onboarding and operating an instance, and the first-autopilot quickstart (25-seat preview).",
    tags=["agent-365", "autopilot", "blueprint", "agent-user", "entra-agent-id", "lifecycle"],
)

class Note(_KitNote):
    """Kit Note plus 10 px of bottom padding when it carries Learn: lines (the kit lets the last link touch the border)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if self.src_lines:
            self.h += 10


W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    a365=("Microsoft Agent 365 integration", learn("agents/concepts/agent-365-integration")),
    a365perm=("Grant Agent 365 permissions to a hosted agent", learn("agents/how-to/grant-agent-365-permissions")),
    apov=("What is an autopilot in Microsoft Foundry?", learn("agents/concepts/autopilot-overview")),
    aplc=("Autopilot lifecycle in Microsoft Foundry", learn("agents/concepts/autopilot-lifecycle")),
    ap1=("Foundry agents in Microsoft Agent 365 (your first autopilot)", learn("agents/how-to/agent-365")),
    pub=("Publish agents to Microsoft Copilot and Microsoft Teams", learn("agents/how-to/publish-copilot")),
    vnet=("Publish agents by using the REST API", learn("agents/how-to/publish-copilot-virtual-network")),
    auth=("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
    ident=("Agent identity", learn("agents/concepts/agent-identity")),
    rpub=("REST: publish an agent to Microsoft 365", learn("reference/rest/microsoft365-publishing-publish-agent-to-microsoft365")),
    rdef=("REST: get Microsoft 365 publish defaults", learn("reference/rest/microsoft365-publishing-get-microsoft365-publish-defaults")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    eid=("What are agent identities? (Microsoft Entra Agent ID)", learn("entra/agent-id/what-are-agent-identities", base="")),
    eau=("Agent users (Microsoft Entra Agent ID)", learn("entra/agent-id/agent-users", base="")),
    rbac=("Role-based access control for Microsoft Foundry", learn("concepts/rbac-foundry")),
)


def src(*keys: str) -> list:
    return [U[k] for k in keys]


def card(w, title, body, theme="green", **kw) -> Card:
    """Dense-column card: one type scale for the whole canvas."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("sub_size", 13)
    kw.setdefault("pad", 14)
    kw.setdefault("gap", 4)
    kw.setdefault("icon_size", 30)
    return Card(w, title, body, theme=theme, **kw)


def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(wrap_text(s, w, size))


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


class Tile(Rect2):
    """Big-number summary tile: headline + one caption."""

    def __init__(self, w, big, cap, theme="green", big_size=34, cap_size=15, pad=14):
        self.th = THEMES[theme]
        self.w, self.big_size, self.cap_size, self.pad = w, big_size, cap_size, pad
        inner = (w - 2 * pad) * 0.965
        self.big_lines = wrap_text(big, inner, big_size)
        self.cap_lines = wrap_text(cap, inner, cap_size)
        lr = metrics.line_ratio()
        self.h = pad * 2 + len(self.big_lines) * big_size * lr + 8 + len(self.cap_lines) * cap_size * lr
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            ty = y + self.pad
            inner = self.w - 2 * self.pad
            cv.text(x + self.pad, ty, "\n".join(self.big_lines), size=self.big_size, color=th.deep, align="center", w=inner)
            ty += len(self.big_lines) * self.big_size * lr + 8
            cv.text(x + self.pad, ty, "\n".join(self.cap_lines), size=self.cap_size, color=INK, align="center", w=inner)
        cv.register("tile", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class Steps(Rect2):
    """Numbered walk-through card."""

    def __init__(self, w, title, steps, theme="yellow", num_theme="blue", size=14, pad=14, src=(), title_size=19):
        self.th = THEMES[theme]
        self.w, self.title, self.steps, self.num_theme, self.size, self.pad, self.title_size = w, title, steps, num_theme, size, pad, title_size
        self.tw = (w - 2 * pad - 38) * 0.965
        lr = metrics.line_ratio()
        self.lines = [wrap_text(t, self.tw, size) for t in steps]
        self.row_h = [max(len(ln) * size * lr, 26) + 9 for ln in self.lines]
        self.src = list(src)
        h = pad + title_size * lr + 8 + sum(self.row_h) + 4
        self.src_lines = []
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * lr + 2
        self.h = h + pad - (2 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=th.deep)
            cy = y + self.pad + self.title_size * lr + 8
            for i, (ln, rh) in enumerate(zip(self.lines, self.row_h)):
                numbered(cv, x + self.pad + 13, cy + 13, i + 1, theme=self.num_theme, d=26, size=15)
                cv.text(x + self.pad + 38, cy + 4, "\n".join(ln), size=self.size, color=INK)
                cy += rh
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("steps", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class CodeBlock(Rect2):
    """Monospace snippet in a soft rounded box (Excalifont has no code face, so Comic Shanns is used)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=14, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title = w, size, pad, title
        inner = (w - 2 * pad) * 0.965
        self.lines: list[str] = []
        for ln in lines:
            if metrics.line_width(ln, size, MONO) <= inner:
                self.lines.append(ln)
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
            cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=2)
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


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "2 integrations", "Registry sync (every published agent) and autopilots (hosted agents only) are the two ways Foundry meets Microsoft Agent 365.", "grape"),
        Tile(C, "Identity, not capability", "Memory, proactivity and planning describe an autopilot. Its own agent user account is what establishes it.", "grape"),
        Tile(C, "1 : many", "You build one blueprint; each hire creates an instance with its own agent identity and agent user account.", "green"),
        Tile(C, "Hosted only", "Only Foundry hosted agents can be published as autopilot blueprints; prompt agents get registry sync but no autopilot.", "green"),
        Tile(C, "8 stages", "Provision, build and publish, approve, hire, onboard, operate, offboard, retire or delete - across four roles.", "gray"),
        Tile(C, "25 seats", "The Agent 365 Frontier license is a 25-seat preview; each autopilot instance consumes one license (as of 2026-11-03).", "yellow"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: Agent 365
def band_agent365(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  Microsoft Agent 365: the enterprise control plane, and the two ways Foundry meets it",
             "Agent 365 is Microsoft's enterprise control plane for agents. A published Foundry agent can appear in its registry (registry sync); a hosted agent can also be published as an autopilot.")
    top = y
    LW = S(4)
    with cv.panel(0, top, title="Foundry project", sub="published agents", theme="green", style="dotted", pad=20, title_size=24, sub_size=15, w=640) as fp:
        pa = Box(600, "Prompt agent", sub="registry sync, activity data - no autopilot", theme="green", h=120, size=20, sub_size=14, fill="hatch", icon="agent", icon_pos="left", icon_size=34)
        ha = Box(600, "Hosted agent", sub="registry sync, autopilot blueprint, activity data via the Agent 365 SDK", theme="green", h=120, size=20, sub_size=14, fill="hatch",
                 icon="container-apps", icon_pos="left", icon_size=34)
        pa.place(cv, fp.ix, fp.iy)
        ha.place(cv, fp.ix, pa.bottom + 90)
    GAP_A = 260
    ax = 640 + GAP_A
    aw = LW - ax
    with cv.panel(ax, top, title="Microsoft Agent 365", sub="registry and control plane for agents", theme="grape", style="solid", fill="soft", pad=20, title_size=24, sub_size=15,
                  w=aw, min_h=fp.h) as ap:
        names = [("Registry", "every published agent", "enterprise-apps"), ("Access control", "RBAC and ABAC + Conditional Access", "conditional-access"),
                 ("Visualization", "", "dashboard"), ("Interoperability", "Microsoft 365 + Work IQ", "iq"),
                 ("Security", "Defender + Purview", "defender")]
        gap = 12
        bw = (aw - 40 - 4 * gap) / 5
        for i, (nm, sb, ic) in enumerate(names):
            b = Box(bw, nm, sub=sb, theme="grape", h=150, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=32)
            b.place(cv, ap.ix + i * (bw + gap), ap.iy + 6)
        cv.text(ap.ix, ap.iy + 176, "Five pillars as the integration page describes them", size=14, color=MUTED)
    arrow(cv, [(pa.right + 24, pa.cy), (ax - 8, pa.cy)], color="#862e9c", sw=3, dash="dashed", label="registry sync", label_size=14, label_wrap=GAP_A - 50, end_head="arrow")
    arrow(cv, [(ha.right + 24, ha.cy - 14), (ax - 8, ha.cy - 14)], color="#862e9c", sw=3, label="registry sync + autopilot blueprint", label_size=14, label_wrap=GAP_A - 50, end_head="arrow")
    arrow(cv, [(ha.right + 24, ha.cy + 34), (ax - 8, ha.cy + 34)], color="#6741d9", sw=2, dash="dashed", label="activity data (Agent 365 SDK)", label_size=13, label_wrap=GAP_A - 50,
          label_pos="below", end_head="arrow")
    y2 = max(fp.bottom, ap.bottom) + 36
    t = Table([("Agent kind", 300), ("Registry sync", 320), ("Autopilot", 320), ("Activity data", 560)], [
        [ct("Prompt agents", "green"), CHECK, CROSS, "Yes"],
        [ct("Hosted agents", "green"), CHECK, CHECK, "Through the Agent 365 SDK"],
    ], w=LW, theme="grape", size=15, head_size=16, align=["left", "center", "center", "left"], title="Support matrix (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, y2)
    cv.text(0, t.bottom + 8, "Learn: Microsoft Agent 365 integration", size=12, color=LINK, link=U["a365"][1])

    rx, rw = LW + G, S(2)
    c1 = card(rw, "Turn it on", [
        "The tenant needs at least one Microsoft 365 Copilot license and enrollment in the Frontier preview program",
        "A global administrator enables Agent 365 and accepts the terms",
        "Per-resource logging configuration: agent365Config",
        "Data residency shifts from the Azure region to the Entra tenant's storage",
        "! Frontier enrollment and Copilot or Agent 365 licensing are prerequisites even when the Azure-side settings are on",
    ], theme="grape", icon="enterprise-apps", badge="preview", src=src("a365"))
    c1.place(cv, rx, top)

    y3 = max(t.bottom + 36, c1.bottom, ap.bottom) + 48
    cv.text(0, y3, "Telemetry to Agent 365 from a hosted agent", size=24, color=THEMES["grape"].deep)
    cy = y3 + 44
    fw = 560
    f1 = Box(fw, "1  Grant Agent365.Observability.OtelWrite", sub="app role assigned to the hosted agent's Entra agent identity", theme="red", h=140, size=18, sub_size=14, fill="hatch",
             icon="managed-identity", icon_pos="left", icon_size=32)
    f2 = Box(fw, "2  The agent emits telemetry", sub="through the Agent 365 SDK when data collection is on", theme="green", h=140, size=18, sub_size=14, fill="hatch", icon="agent",
             icon_pos="left", icon_size=32)
    f3 = Box(fw, "3  Data lands in the Entra tenant", sub="the tenant's storage location, not your Azure region", theme="grape", h=140, size=18, sub_size=14, fill="hatch",
             icon="enterprise-apps", icon_pos="left", icon_size=32)
    row(cv, 0, cy, [f1, f2, f3], gap=100)
    connect(cv, f1, f2, sw=3, color="#862e9c")
    connect(cv, f2, f3, sw=3, color="#862e9c")
    dx = 3 * fw + 2 * 100 + G
    d1 = card(W - dx, "The permission grant", [
        "App role Agent365.Observability.OtelWrite, appRoleId 8f71190c-00c8-461d-a63b-f74abde9ba52",
        "Done by a Global Administrator or Application Administrator",
        "Microsoft Graph: POST /servicePrincipals/<id>/appRoleAssignments returns 201; allow 2 to 5 minutes; 409 means it is already assigned",
        "! A private source-code deploy must let the agent reach agent365.svc.cloud.microsoft on port 443 when data collection is on",
    ], theme="red", icon="key-vault", src=src("a365perm"))
    d1.place(cv, dx, cy - 6)
    return max(f3.bottom, d1.bottom)


# ================================================================================================ band 2: autopilot concept
def band_concept(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Autopilot: an identity, not a capability",
             "Every Foundry agent has an Entra agent identity. An autopilot also has an Entra agent user account, so it acts as itself in Microsoft 365 - a persistent, named member of the organization with a manager.")
    top = y
    cw = S(2)
    c1 = card(cw, "Problem 1: no user in the loop", [
        "Without an agent user account an agent can act in Microsoft 365 only on behalf of a signed-in user",
        "An agent triggered by an event has no signed-in user to act for, so it cannot send email or edit a document at all",
    ], theme="red", icon="user")
    c2 = card(cw, "Problem 2: group settings", [
        "In a group chat the agent must guess on whose behalf to act, and there is no right answer",
        "That person's permissions apply to the whole thread: actions are attributed to someone who did not ask, and members can see content they cannot access",
    ], theme="red", icon="groups")
    c3 = card(cw, "The fix: its own agent user account", [
        "Gives the autopilot its own email, calendar, OneDrive, Teams presence and a place in the org chart",
        "It performs Microsoft 365 actions as itself, so it works with a whole team at once and can respond to a trigger when no user is present",
    ], theme="grape", icon="users", badge="preview", src=src("apov", "eau"))
    _, b = row(cv, 0, top, [c1, c2, c3], gap=G)
    y2 = b + 36
    d1 = card(cw, "Capabilities do not define it", [
        "Memory, proactivity, reasoning, planning and learning describe what an autopilot can do - and change with every release",
        "If capabilities defined the category, adding memory in a release would make an agent an autopilot while nothing about who it is changed",
    ], theme="gray", icon="gear")
    d2 = card(cw, "Autonomy does not define it either", [
        "A background service agent can run on its own all day and is not an autopilot",
        "An autopilot need not be fully autonomous: your organization controls when it responds, who it talks to, what it can reach and which actions it can take",
    ], theme="gray", icon="scheduler")
    d3 = Note(cw, "Capabilities describe an autopilot. Identity establishes it. The distinction is binary: an agent either has its own agent user account or it does not.",
              kind="quote", title="The definition", size=17, src=src("apov"))
    row(cv, 0, y2, [d1, d2, d3], gap=G)
    y3 = max(d1.bottom, d2.bottom, d3.bottom) + 48

    # ---- why a blueprint
    cv.text(0, y3, "Why you build a blueprint, not an autopilot", size=26, color=THEMES["grape"].deep)
    y4 = y3 + 48
    LW = S(2)
    with cv.panel(0, y4, title="Rebuild the agent for every team", sub="what the blueprint avoids", theme="gray", style="dotted", pad=20, title_size=22, sub_size=15, w=LW) as pl:
        bx = []
        for t in ("Team A", "Team B", "Team C"):
            b = Box((LW - 40 - 2 * 16) / 3, f"{t} agent", sub="own copy of the logic, own access, own governance", theme="gray", h=118, size=17, sub_size=13, fill="hatch")
            bx.append(b)
        row(cv, pl.ix, pl.iy, bx, gap=16)
        cv.text(pl.ix, bx[0].bottom + 16, wrap("Ten teams later: ten near-identical agents. Their controls drift apart, and a compromised tool has to be chased down one agent at a time.",
                                               LW - 40, 15), size=15, color="#c92a2a")
    RX = LW + G
    RW = W - RX
    with cv.panel(RX, y4, title="One blueprint, per-team instances", sub="shared logic, separate access", theme="grape", style="solid", fill="soft", pad=20, title_size=22, sub_size=15,
                  w=RW, min_h=pl.h) as pr:
        bp = Box(300, "Agent blueprint", sub="what it knows how to do + the platform infrastructure it needs (storage for tracked items and memory)", theme="gray", h=170, size=19, sub_size=13, fill="hatch")
        bp.place(cv, pr.ix, pr.iy + 6)
        insts = []
        for i, (t, acc) in enumerate((("Team A instance", "Team A's Azure DevOps project and SharePoint site"), ("Team B instance", "Team B's Azure DevOps project and SharePoint site"),
                                      ("Team C instance", "Team C's own project and site (and so on for every hire)"))):
            b = Box(470, t, sub=f"own identity, permissions and assignment; access: {acc}", theme="grape", h=88, size=17, sub_size=13, fill="hatch")
            b.place(cv, pr.ix + 300 + 150, pr.iy + 6 + i * 100)
            insts.append(b)
            connect(cv, bp, b, a_side="right", b_side="left", sw=3, color="#862e9c", label="hire", label_size=14)
        tx = pr.ix + 300 + 150 + 470 + 24
        cv.text(tx, pr.iy + 6, wrap("A blueprint never grants a team's business resources. Holding a tool is not holding access to the data behind it: a SharePoint tool opens no site, "
                                    "a mailbox does not send mail.", RX + RW - 20 - tx, 14), size=14, color=INK)
    y5 = max(pl.bottom, pr.bottom) + 20
    n = Note(W, "Policy is set once and every instance inherits it. Update the blueprint and every instance updates. Block the blueprint and every instance stops, because every instance token "
                "chains back to the blueprint's credential. Only Foundry hosted agents can be published as autopilot blueprints.", kind="key", title="One governance layer for the whole fleet",
             src=src("apov", "aplc"))
    n.place(cv, 0, y5)
    y6 = n.bottom + 36
    pat = [
        card(S(2), "Group autopilot", ["Works for a team: lives where the team works and holds context the whole team shares", "Involves every role; the access manager split matters most here"], theme="green",
             icon="groups", src=src("apov")),
        card(S(2), "Company-wide autopilot", ["A centrally managed capability for everyone, typically one production instance per business process",
                                              "One instance and one manager answer for the organization, so 'teammate' stops being a useful distinction"], theme="green", icon="enterprise-apps", src=src("aplc")),
        card(S(2), "Personal autopilot", ["Works for one person: an isolated instance created and used by that person",
                                          "Involves only the developer, who is usually the manager and the only user"], theme="green", icon="user", src=src("aplc")),
    ]
    _, b = row(cv, 0, y6, pat, gap=G)
    return b


# ================================================================================================ band 3: lifecycle swimlane
LANES = [
    ("Azure administrator", "What the platform runs on, and who can build on it", "indigo"),
    ("Developer", "The blueprint's role and capabilities, and the conditions it was built and tested for", "green"),
    ("Tenant administrator", "Whether the autopilot can operate in your tenant, and under what policy", "grape"),
    ("Manager", "The employment of the instance, from hire to offboard", "orange"),
]
STAGES = [  # title, lane, owner text, what it does, produces, reversible (text, theme)
    ("Provision infrastructure", 0, "Sets up the environment and the agent's platform resources; gives developers minimum permissions to build, test and deploy",
     "A development environment and platform resources", ("Yes", "green")),
    ("Build and publish", 1, "Defines role and behavior; declares permission scopes and two ceilings: who can hire, and the widest access a manager can grant",
     "A published blueprint with declared scopes and ceilings", ("Yes", "green")),
    ("Approve, configure, consent", 2, "Reviews the blueprint, consents to its scopes, approves it and selects who can hire (Microsoft 365 admin center)",
     "An activated blueprint that selected people can hire", ("Yes", "green")),
    ("Hire", 3, "One action that creates both objects; the person who hires becomes the manager",
     "An agent identity and an agent user account", ("By offboarding", "yellow")),
    ("Onboard", 3, "Sets audience, listening scope, messaging scope, access and source of truth: the first grant of business resources",
     "The instance's audience and its access to team resources", ("Yes", "green")),
    ("Operate", 3, "Use, observe, govern and coach run at the same time; teammates and business leads take part",
     "Day-to-day work, observation and coaching", ("Yes", "green")),
    ("Offboard", 3, "Removes the agent user account and revokes its memberships; access ends immediately",
     "A removed instance", ("No", "red")),
    ("Retire or delete", 2, "Retire (tenant administrator): no new hires. Delete: removes the blueprint and every instance",
     "A blueprint with no new hires, or none at all", ("Retire yes, delete no", "red")),
]


def band_lifecycle(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  The lifecycle: eight stages, four roles, three layers",
             "An Azure administrator provisions, a developer builds and publishes a blueprint, a tenant administrator approves it, and a manager hires and runs each instance. Responsibility passes from role to role.")
    top = y
    LBL = 380
    CW = (W - LBL) / 8
    BW = CW - 48

    def colx(i):
        return LBL + i * CW + 24

    # layer bars
    bars = [(0, 3, "BLUEPRINT LAYER: runs once; every instance inherits the result", "grape"),
            (3, 4, "INSTANCE LAYER: runs once per hire; many are alive at the same time", "orange"), (7, 1, "BLUEPRINT EXIT", "grape")]
    cv.text(0, top + 12, "Layer", size=20, color=MUTED)
    for c0, n, label, th_name in bars:
        th = THEMES[th_name]
        x0 = LBL + c0 * CW + 4
        w0 = n * CW - 8
        cv.rect(x0, top, w0, 52, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        lines = wrap_text(label, w0 - 20, 16)
        tw, thh = text_size("\n".join(lines), 16)
        cv.text(x0 + 10, top + (52 - thh) / 2, "\n".join(lines), size=16, color=th.deep, align="center", w=w0 - 20)
    ly0 = top + 52 + 22
    LH = 190
    # lane bands first
    for k, (nm, decision, th_name) in enumerate(LANES):
        th = THEMES[th_name]
        ly = ly0 + k * LH
        cv.rect(0, ly, W, LH - 10, stroke=th.stroke, fill=th.soft, style="solid", sw=1.5, dash="dotted", rough=0)
        Box(LBL - 20, nm, sub=decision, theme=th_name, h=LH - 30, size=19, sub_size=13, fill="solid").place(cv, 8, ly + 10)
    # stage boxes
    placed = []
    for i, (title, lane, text, produces, rev) in enumerate(STAGES):
        b = Box(BW, f"{i + 1}  {title}", sub=text, theme=LANES[lane][2], h=LH - 34, size=17, sub_size=13, fill="hatch")
        b.place(cv, colx(i), ly0 + lane * LH + 12)
        placed.append(b)
    # standing activities
    dev_bar = Box(6 * CW - 48, "Developer, standing: operate the blueprint",
                  sub="observe, evaluate and optimize; fixes ship as new versions to every instance; a version that widens scopes re-enters the consent gate. "
                      "A developer can block the blueprint but, like everyone, cannot unblock it.", theme="green", h=LH - 34, size=17, sub_size=14, fill="soft", dash="dashed")
    dev_bar.place(cv, colx(2), ly0 + 1 * LH + 12)
    fleet = Box(4 * CW - 48, "Tenant administrator, standing: manage the fleet",
                sub="one registry lists every hire with team, blueprint and version; observe, govern and secure. Blocking the blueprint stops every instance at once; "
                    "only a tenant administrator can restart a blocked one.", theme="grape", h=LH - 34, size=17, sub_size=14, fill="soft", dash="dashed")
    fleet.place(cv, colx(3), ly0 + 2 * LH + 12)
    # annotations in the otherwise empty lane cells
    cv.text(colx(1), ly0 + 44, wrap("Done before development begins. The Azure administrator is the only role that finishes before the autopilot reaches a user; "
                                    "the setup applies per environment, not per autopilot, and every blueprint built there inherits it.", 4 * CW, 15), size=15, color=MUTED)
    cv.text(colx(0), ly0 + 3 * LH + 40, wrap("Approval enables hiring: the one point where the blueprint layer meets the instance layer. Until onboarding nothing has been granted - "
                                             "an autopilot can hold every scope it needs and still reach no data.", 3 * CW - 90, 15), size=15, color=MUTED)
    # hand-off arrows
    for a, b in zip(placed[:3], placed[1:4]):
        connect(cv, a, b, a_side="right", b_side="left", route="elbow", sw=3, color="#343a40")
    for a, b in zip(placed[3:6], placed[4:7]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, color="#343a40")
    connect(cv, fleet, placed[7], a_side="right", b_side="left", sw=3, color="#862e9c", dash="dashed")
    # produced + reversible rows
    ry = ly0 + 4 * LH + 4
    cv.text(0, ry + 4, "Produces", size=20, color=MUTED)
    cv.text(0, ry + 62, "Reversible?", size=20, color=MUTED)
    for i, st in enumerate(STAGES):
        cv.text(colx(i), ry, wrap(st[3], BW, 14), size=14, color=INK)
        lab, th_name = st[4]
        Chip(lab, theme=th_name, size=14, fill="solid").place(cv, colx(i), ry + 62)
    bottom = ry + 104
    n = Note(W, "The line that organizes the whole lifecycle: every control in the operate stages and the standing activities can be undone. Offboarding an instance and deleting a blueprint cannot. "
                "A blueprint defect is always systemic - every instance carries the same flaw - which is why the block applies to the blueprint.", kind="key",
             title="Reversible until offboard or delete", src=src("aplc"))
    n.place(cv, 0, bottom + 20)
    return n.bottom


# ================================================================================================ band 4: onboard, operate, roles
def band_operate(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Onboard, operate and govern an instance",
             "Hiring creates the identity and the account; onboarding is where employment really begins. Every audience starts as the manager alone and extends only up to the developer's ceiling.")
    top = y
    t1 = Table([("Onboarding setting", 250), ("What it controls", 918)], [
        [ct("Audience", "orange"), "Who can use the instance"],
        [ct("Listening scope", "orange"), "Which conversations and surfaces the instance receives"],
        [ct("Messaging scope", "orange"), "Who the instance can message"],
        [ct("Access", "orange"), "Which business resources the instance can reach (security-group membership, an Azure DevOps project, a SharePoint site)"],
        [ct("Source of truth", "orange"), "Which content grounds the instance's answers"],
    ], w=S(2), theme="orange", size=15, head_size=16, title="Five onboarding settings (the manager configures them)", title_size=20)
    t1.place(cv, 0, top)
    n1 = Note(S(2), "Non-teammates are blocked by default, before the autopilot ever calls a model on their behalf. Authorization starts at onboarding but never finishes: teams, "
                    "resources and grants change.", kind="warn", title="Blocked by default", src=src("aplc"))
    n1.place(cv, 0, t1.bottom + 24)

    mx = S(2) + G
    c1 = card(S(2), "Consent and access are different gates", [
        "Scopes and consent govern the token: which kinds of calls are allowed. Microsoft Entra ID enforces this gate",
        "Group memberships and roles govern the account: which data those calls reach. Each resource enforces this gate against its own lists and never checks consent",
        "For a person, IT closes both gates before day one. For an autopilot both are new at hire, so onboarding includes work that feels like it should already be done",
        "If the hirer cannot make the grants, an access manager hires, onboards and authorizes the instance, then transfers the manager role",
    ], theme="red", icon="key-vault", src=src("aplc"))
    c1.place(cv, mx, top)
    c1b = card(S(2), "What the developer builds and declares", [
        "Defines what the agent does and how it behaves: when it replies, when it stays silent, when it asks for approval, and what it must never do",
        "The platform provides memory, routines and self-improvement as building blocks: the developer enables and configures them",
        "A development instance lets the developer iterate without re-entering tenant approval for every change",
        "Publishing records the declared scopes and two ceilings (who can hire, the widest access a manager can grant). Nothing in this stage grants access",
    ], theme="green", icon="agent", src=src("aplc"))
    c1b.place(cv, mx, c1.bottom + 24)

    rx = 2 * (S(2) + G)
    t2 = Table([("Activity while operating", 250), ("Who", 250), ("What happens", 668)], [
        [ct("Use", "green"), "Teammates and manager", "Teams chats, channels and email; teammates give standing work (routines) in one message"],
        [ct("Observe", "violet"), "Manager and business leads", "What the instance did, for whom, at what cost, and whether anything needs investigating"],
        [ct("Govern", "red"), "Manager and business leads", "Tighten or revoke access, or block. Blocking is asymmetric: many can stop it, only a tenant administrator can restart it"],
        [ct("Coach and customize", "grape"), "Manager alone", "Style, memory edits and routines. Anyone can give objective corrections (a slipped date, a wrong owner)"],
    ], w=S(2), theme="gray", size=14, head_size=15, title="Four activities run at the same time", title_size=20)
    t2.place(cv, rx, top)
    n2 = Note(S(2), "Governance decides who can stop an instance, and by design almost everyone can. Accountability decides who must: always the manager, whoever is at fault.",
              kind="info", title="Governance vs accountability", src=src("aplc"))
    n2.place(cv, rx, t2.bottom + 24)

    y2 = max(n1.bottom, c1b.bottom, n2.bottom) + 48
    t3 = Table([("Role", 330), ("Layer", 150), ("Their part", 1500), ("Notes", 1620)], [
        [ct("Azure administrator", "indigo"), "Platform", "Provisions Foundry infrastructure and the agent's platform resources; assigns developer permissions and permissions for the default instance identity",
         "Finishes before the autopilot reaches a user"],
        [ct("Developer", "green"), "Blueprint", "Defines what the agent does and how it behaves; sets blueprint and instance authorization; declares permission scopes; publishes, tests and updates",
         "Changes what every instance is. A manager changes how one instance behaves"],
        [ct("Tenant administrator", "grape"), "Fleet", "Manages licensing; approves and activates the blueprint; grants admin consent; selects who can hire; observes the fleet; blocks the blueprint",
         "A wider ceiling after a new version re-enters the consent gate"],
        [ct("Manager", "orange"), "Instance", "Hires the instance; configures who can use it; grants team resources; monitors and customizes it; offboards it", "Becomes the manager by hiring; accountable for stopping a broken instance"],
        [ct("Executive business sponsor (optional)", "gray"), "Blueprint", "Joins when an executive wants the autopilot across an organization and funds it; sets blueprint-wide controls", "No authority over any single instance"],
        [ct("Access manager (optional)", "gray"), "Instance", "Hires and onboards the instance, authorizes its access, then transfers the manager role", "Joins when the hirer cannot or should not judge least privilege"],
        [ct("Teammates and business leads", "gray"), "Instance", "Teammates use the autopilot and give corrections; business leads can observe and block but cannot delete or transfer", "Anyone close enough to see misbehavior can stop it"],
    ], w=W, theme="gray", size=14, head_size=15, title="Who does what (four roles own the four decisions; the rest are optional)", title_size=22)
    t3.place(cv, 0, y2)
    cv.text(0, t3.bottom + 8, "Learn: Autopilot lifecycle in Microsoft Foundry", size=12, color=LINK, link=U["aplc"][1])
    return t3.bottom + 30


# ================================================================================================ band 5: first autopilot
def band_first(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Your first autopilot: licensing, permissions and the publish flow (quickstart)",
             "A hosted agent published with publishAsAutopilot becomes a blueprint request in the Microsoft 365 admin center; a manager then hires an instance from Teams. Samples: foundry-samples, samples/csharp and samples/python, foundry-autopilot-agent.")
    top = y
    c1 = card(S(2), "Licensing (as of 2026-11-03)", [
        "Enrollment in the Frontier preview program",
        "Agent 365 terms accepted",
        "At least one Microsoft 365 Copilot license, or an Agent 365 license (including E7)",
        "An Agent 365 Frontier license: a 25-seat preview",
        "! Each autopilot instance consumes one license",
    ], theme="yellow", icon="cost-management", badge="preview", src=src("ap1"))
    t1 = Table([("Step", 300), ("Permission the quickstart lists", 868)], [
        [ct("Provision", "indigo"), "Owner, or Contributor plus RBAC Administrator, on the resource group"],
        [ct("Build", "green"), "Foundry User, plus AcrPush or Repository Writer on the registry"],
        [ct("Publish", "green"), "Foundry User"],
        [ct("Approve", "grape"), "Global Administrator or AI Administrator (Microsoft 365 admin center)"],
    ], w=S(2), theme="gray", size=14, head_size=15, title="Permissions by step", title_size=20)
    c1.place(cv, 0, top)
    t1.place(cv, S(2) + G, top)
    code = CodeBlock(S(2), [
        "publishAsAutopilot: true",
        'publishScope: "Tenant"',
        "useAgenticUserTemplate: true",
        "agenticUserTemplate:",
        "  Id: digitalWorkerTemplate",
        "  File: agenticUserTemplateManifest.json",
        "  SchemaVersion: <schema version>",
        "  AgentIdentityBlueprintId: <blueprint ID>",
        "  CommunicationProtocol: activityProtocol",
    ], title="Publish fields for an autopilot (names from the quickstart)", theme="grape", src=src("ap1", "rpub"))
    code.place(cv, 2 * (S(2) + G), top)
    y2 = max(c1.bottom, t1.bottom, code.bottom) + 36
    steps = [
        Box(C, "1  azd provision", sub="Provisions the infrastructure, builds the hosted agent (creating its blueprint and identity) and publishes; the request waits in the admin center", theme="indigo", h=190,
            size=18, sub_size=14, fill="hatch", icon="azd", icon_pos="top", icon_size=30),
        Box(C, "2  Admin wizard", sub="Publish to users and Activate (None, All users or Specific users and groups) > Apply template > Grant admin consent > Publish; registry status becomes Available",
            theme="grape", h=190, size=18, sub_size=14, fill="hatch", icon="enterprise-apps", icon_pos="top", icon_size=30),
        Box(C, "3  Hire in Teams", sub="Apps > Agents for your team > Create instance: name (up to 32 characters), alias, domain and manager. Creation is asynchronous and takes a few minutes",
            theme="orange", h=190, size=18, sub_size=14, fill="hatch", icon="teams", icon_pos="top", icon_size=30),
        Box(C, "4  Onboard and operate", sub="The new instance has its own agent identity and agent user account; set audience, scopes and access, then use it in Teams, email and documents",
            theme="green", h=190, size=18, sub_size=14, fill="hatch", icon="agent", icon_pos="top", icon_size=30),
    ]
    row(cv, 0, y2, steps, gap=G)
    for a, b in zip(steps, steps[1:]):
        connect(cv, a, b, sw=3, color="#343a40")
    n = Note(S(2), "The hosted-agent token service issues a blueprint exchange token for the agent-user flow. The REST publish API takes publishAsAutopilot; the defaults route takes "
                   "a publishAsDigitalWorker flag (the API's word for an autopilot).", kind="info", title="Where the publish fields go",
             src=src("ap1", "rdef"))
    n.place(cv, X(4), y2)
    n2 = Note(S(2), "The autopilot quickstart shows api-version=2025-11-15-preview while the portal and private-network publish pages show api-version=v1. Check the live reference for the version "
                    "you target.", kind="warn", title="Docs disagree: api-version", src=src("ap1", "vnet"))
    n2.place(cv, X(4), n.bottom + 22)
    return max(steps[0].bottom, n2.bottom, code.bottom)


# ================================================================================================ band 6: docs disagree and gotchas
def band_gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Docs disagree, gotchas and what the pages do not say - as of 2026-11-03",
             "One list for both parts. Where two Learn pages (or Learn and a blog) give different answers, both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 1100), ("Another source says", 1100), ("How to read it", 1100)], [
        [ct("Publish API", "orange"), "Migrate from Agent applications: there is no public publish API",
         "The REST reference has Agent Microsoft 365 Publishing: publish, publish defaults and app package", "Use the REST group; confirm the api-version you target"],
        [ct("api-version", "orange"), "Portal and private-network pages: api-version=v1", "Autopilot quickstart: api-version=2025-11-15-preview",
         "Follow the version in the page you are using; test before you pin one"],
        [ct("Incoming A2A on hosted agents", "orange"), "The enable-A2A page describes prompt agents only",
         "The hosted-agents concept page and azure.yaml list a2a as a hosted protocol", "Check the hosted-agent canvases and the live page before relying on it"],
        [ct("Direct SIP", "orange"), "Agent Service overview: not currently offered as a supported customer flow",
         "The SIP how-to documents it (Preview); outbound only in Southeast Asia", "Treat SIP as available only where you have confirmed it"],
        [ct("Publish status", "orange"), "The Learn publish pages read for these canvases carry no preview banner",
         "A Build 2026 blog recap (not Learn) said Teams and Microsoft 365 publishing was planned to go GA in June 2026", "Check the live page for current status before you commit a date"],
        [ct("Traffic split across versions", "orange"), "The configure-agent, manage-hosted-agent and hosted-agents pages: no traffic splitting, one version at 100%",
         "The production-deploy page documents 90/10, 50/50 and 100/0 canary steps with azd ai agent endpoint update; REST exposes FixedRatio rules with traffic_percentage",
         "Treat splitting as unconfirmed; see 'Hosted agents: deploy and operate'"],
        [ct("Role names", "orange"), "Some pages still say Azure AI User or Azure AI Developer",
         "Current names are Foundry User, Foundry Owner, Foundry Account Owner and Foundry Project Manager; role IDs and permissions are unchanged", "Use the Foundry names; the GUIDs do not change"],
    ], w=W, theme="orange", size=14, head_size=15, title="Docs disagree (parts 1 and 2)", title_size=22)
    t.place(cv, 0, y)
    top = t.bottom + 36
    w = S(2)
    g1 = Note(w, "Autopilot = identity, not capability. Only hosted agents can be blueprints; one license per instance; the Frontier license is a 25-seat preview.", kind="gotcha",
              title="Three limits in one line", src=src("apov", "ap1"))
    g2 = Note(w, "Frontier preview enrollment and Copilot or Agent 365 licensing are prerequisites even when the Azure-side settings are on. A new blueprint and every widened scope re-enter the admin consent gate: "
                 "plan administrator review time into your rollout.", kind="warn", title="Licensing and consent come first", src=src("ap1", "aplc"))
    g3 = Note(w, "Azure Government: published agents get a stable endpoint and an Entra identity, but there is no A2A tool and no hosted agents - and only hosted agents can be autopilot blueprints.", kind="info",
              title="Azure Government", src=src("gov"))
    row(cv, 0, top, [g1, g2, g3], gap=G)
    ny = top + max(g1.h, g2.h, g3.h) + 28
    q = Note(W, "Not stated on the autopilot and Agent 365 pages read for these canvases: a price per license, a maximum number of instances per blueprint, and per-region availability of the Frontier "
                "program. Nothing on these canvases fills those gaps.", kind="quote", title="What the pages do not say", src=src("a365", "apov", "aplc"))
    q.place(cv, 0, ny)
    return q.bottom


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Agent 365 and autopilots",
        "Part 2 of 'Publishing and channels'  |  registry sync, telemetry, identity-based digital coworkers, and the docs conflicts for both parts  |  Frontier preview, as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Identity and security", "red"), ("Platform and infrastructure", "indigo"), ("Observability", "violet"),
                           ("Governance and Agent 365", "grape"), ("Managers and Teams", "orange"), ("Cost and licenses", "yellow"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Publishing and channels: endpoint, Microsoft 365, Teams and identity", "Agent identity and delegation", "Foundry Control Plane",
                "Hosted agents: your code on Foundry's runtime", "Hosted agents: deploy and operate", "AgentOps lifecycle"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_agent365(cv, y) + 56
    y = band_concept(cv, y) + 56
    y = band_lifecycle(cv, y) + 56
    y = band_operate(cv, y) + 56
    y = band_first(cv, y) + 56
    y = band_gotchas(cv, y) + 56
    sources(cv, 0, y, [
        ("Microsoft Agent 365 integration", U["a365"][1]), ("Grant Agent 365 permissions to a hosted agent", U["a365perm"][1]),
        ("What is an autopilot in Microsoft Foundry?", U["apov"][1]), ("Autopilot lifecycle in Microsoft Foundry", U["aplc"][1]),
        ("Foundry agents in Microsoft Agent 365 (your first autopilot)", U["ap1"][1]), ("Publish agents to Microsoft Copilot and Microsoft Teams", U["pub"][1]),
        ("Publish agents by using the REST API", U["vnet"][1]), ("Agent endpoint authorization", U["auth"][1]), ("Agent identity", U["ident"][1]),
        ("REST: publish an agent to Microsoft 365", U["rpub"][1]), ("REST: get Microsoft 365 publish defaults", U["rdef"][1]),
        ("What are agent identities? (Microsoft Entra Agent ID)", U["eid"][1]), ("Agent users (Microsoft Entra Agent ID)", U["eau"][1]),
        ("Agent Service in Azure Government", U["gov"][1]),
    ], w=W, cols=4)
