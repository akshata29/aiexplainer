"""MCP and tool authentication - every auth mode, who holds which token, and which one to choose."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.flows import Sequence as _Sequence

META = dict(
    id="mcp-and-tool-authentication", title="MCP and tool authentication", section="2", group="Tools and MCP",
    order=33,
    description="How agents authenticate to MCP servers, A2A agents and tools: every auth mode (none, key, project "
                "managed identity, agent identity, OAuth passthrough, UserEntraToken, AgentOnBehalfOfUser), who holds "
                "which token, consent, a decision table and gotchas.",
    tags=["mcp", "authentication", "oauth", "entra", "agent-identity", "obo"],
)

W = 3600                 # canvas content width
G3, C3 = 60, 1160        # three-column grid: 3 * 1160 + 2 * 60 = 3600
G4, C4 = 45, 866         # four-column grid: 4 * 866 + 3 * 45 = 3599

LINKS = {
    "mcp-auth": ("Set up MCP server authentication", learn("agents/how-to/mcp-authentication")),
    "tool-auth": ("Toolbox authentication in Microsoft Foundry", learn("agents/how-to/tools/tool-authentication")),
    "delegation": ("User delegation for tools in Microsoft Foundry", learn("agents/concepts/user-delegation")),
    "cfg-delegation": ("Configure user delegation for tools", learn("agents/how-to/configure-user-delegation")),
    "consent": ("Microsoft Entra consent for delegated access", learn("agents/concepts/entra-delegated-access-consent")),
    "a2a-auth": ("Agent2Agent (A2A) authentication", learn("agents/concepts/agent-to-agent-authentication")),
    "endpoint": ("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
    "cfg-endpoint": ("Configure agent endpoint authorization",
                     learn("agents/how-to/configure-agent-endpoint-authorization")),
    "id-overview": ("Identity and access overview for Agent Service", learn("agents/concepts/identity-access-overview")),
    "agent-identity": ("Agent identity concepts", learn("agents/concepts/agent-identity")),
    "mcp-tool": ("Connect agents to MCP server endpoints", learn("agents/how-to/tools/model-context-protocol")),
    "a2a-tool": ("Connect to an A2A agent endpoint", learn("agents/how-to/tools/agent-to-agent")),
    "work-iq": ("Connect agents to Microsoft 365 with Work IQ (preview)", learn("agents/how-to/tools/work-iq")),
    "connections": ("Add a new connection to your project", learn("how-to/connections-add")),
    "rbac": ("Role-based access control for Microsoft Foundry", learn("concepts/rbac-foundry")),
    "toolbox": ("Create and manage a toolbox", learn("agents/how-to/tools/toolbox")),
    "entra-mcp": ("Secure an MCP server with Microsoft Entra ID",
                  learn("entra/agent-id/secure-mcp-server-with-entra-id", base="")),
    "foundry-mcp": ("Foundry MCP Server best practices and security", learn("mcp/security-best-practices")),
}


def S(*keys):
    """Citation tuples for Card/Note src=."""
    return [LINKS[k] for k in keys]


def nt(cv, x, y, w, text, *, kind="info", title=None, src=(), min_h=0, **kw):
    """Note placed with a little extra height when it carries a citation (keeps the Learn line off the border)."""
    n = Note(w, text, kind=kind, title=title, src=list(src), **kw)
    extra = 14 if src else 0
    n.place(cv, x, y, h=max(n.h + extra, min_h))
    return n


class Seq(_Sequence):
    """Sequence with knocked-out message labels and compact self-messages (loop on the left for the last lane)."""

    def msg(self, src, dst, text, *, dash="solid", num=None, note=None, color=INK, gap_after=0, end_head="arrow"):
        cv = self.cv
        x1, x2 = self._cx(src), self._cx(dst)
        th = self.actors[src][1]
        lo, hi = sorted((x1, x2))
        span = hi - lo
        lw = max(span - 50 - (30 if num is not None else 0), 120)
        txt = "\n".join(metrics.wrap_text(text, lw, self.label_size))
        tw, th_ = metrics.text_size(txt, self.label_size)
        y = self.cur + th_ + 14
        sgn = 1 if x2 > x1 else -1
        cv.poly([(x1 + 4 * sgn, y), (x2 - 4 * sgn, y)], kind="arrow", stroke=color, sw=2, dash=dash, end_head=end_head)
        tx = lo + (span - tw) / 2
        if num is not None:
            numbered(cv, lo + 22 if x2 > x1 else hi - 22, y - 16, num, theme=th.name, d=26, size=15)
            tx += 12
        cv.rect(tx - 5, y - th_ - 6, tw + 10, th_ + 3, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                rough=0, opacity=94, round_=False)
        cv.text(tx, y - th_ - 5, txt, size=self.label_size, color=INK, align="center", w=tw)
        if note:
            nl = metrics.wrap_text(note, max(span - 30, 120), self.label_size - 2)
            cv.text(lo + 14, y + 6, "\n".join(nl), size=self.label_size - 2, color=MUTED)
            self.cur = y + 12 + len(nl) * (self.label_size - 2) * 1.25 + gap_after
        else:
            self.cur = y + 20 + gap_after
        return y

    def selfmsg(self, i, text, *, num=None, dash="solid"):
        cv = self.cv
        x1 = self._cx(i)
        sgn = -1 if i == len(self.actors) - 1 else 1
        loop = 44
        gap = 14 + (28 if num is not None else 0)
        lines = metrics.wrap_text(text, self.spacing - loop - gap - 40, self.label_size)
        txt = "\n".join(lines)
        tw, th_ = metrics.text_size(txt, self.label_size)
        y = self.cur + 8
        cv.poly([(x1 + sgn * 4, y), (x1 + sgn * loop, y), (x1 + sgn * loop, y + 26), (x1 + sgn * 4, y + 26)],
                kind="arrow", stroke=INK, sw=2, dash=dash, end_head="arrow")
        if num is not None:
            numbered(cv, x1 + sgn * (loop + 20), y + 13, num, theme=self.actors[i][1].name, d=26, size=15)
        tx = x1 + loop + gap if sgn > 0 else x1 - loop - gap - tw
        cv.text(tx, y - 3, txt, size=self.label_size, color=INK, align="left" if sgn > 0 else "right", w=tw)
        self.cur = y + max(30, th_ - 2) + 24
        return y


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "MCP and tool authentication",
        "How a Foundry agent proves who it is to an MCP server, A2A agent or tool - every auth mode, who holds which "
        "token, and which one to choose (status as of 2026-11-03)", icon="foundry", w=W)
    y = bottom + 46
    y = band_boundaries(cv, y)
    y = band_connection(cv, y)
    y = band_modes(cv, y)
    y = band_sequences(cv, y)
    y = band_deep(cv, y)
    y = band_decide(cv, y)
    y = band_gotchas(cv, y)
    sources(cv, 0, y + 20, [LINKS[k] for k in (
        "mcp-auth", "tool-auth", "delegation", "cfg-delegation", "consent", "a2a-auth", "endpoint", "id-overview",
        "agent-identity", "mcp-tool", "a2a-tool", "work-iq", "connections", "entra-mcp")], w=W, cols=3)


# ====================================================================== section 1: three boundaries
def boundary_panel(cv, x, y, n, theme, title, sub, left, right, arrow_label, bullets, src, here=False):
    with cv.panel(x, y, title=title, sub=sub, theme=theme, style="dotted", fill="none", pad=24, title_size=28,
                  sub_size=15, w=C3) as p:
        numbered(cv, x + C3 - 56, y + 52, n, theme=theme, d=56, size=32)
        if here:
            draw_badge(cv, x + C3 - 56 - 26 - 128, y + 38, "you are here", size=14)
        y0 = p.iy + 14
        bl = Box(350, left[0], sub=left[1], theme=left[2], icon=left[3], icon_pos="left", h=104).place(cv, p.ix + 16, y0)
        br = Box(350, right[0], sub=right[1], theme=right[2], icon=right[3], icon_pos="left", h=104).place(
            cv, p.ix + C3 - 48 - 16 - 350, y0)
        connect(cv, bl, br, label=arrow_label, label_size=14, label_wrap=250, sw=3, gap=8)
        card = Card(C3 - 48, None, bullets, theme=theme, fill="soft", body_size=15, src=src)
        card.place(cv, p.ix, y0 + 104 + 30)
    return p


def band_boundaries(cv, y):
    _, b = section_header(cv, 0, y, "1.  Three trust boundaries - permissions never carry across",
                          sub="Identity and access in Agent Service spans three independent boundaries; "
                              "this canvas zooms into the third one", size=34)
    y0 = b + 34
    p1 = boundary_panel(
        cv, 0, y0, 1, "grape", "Developer or admin  ->  Foundry resources", "management access",
        ("Developer or admin", "user or service identity", "gray", "users"),
        ("Foundry resource and project", "agents, toolboxes, connections", "grape", "foundry"),
        "create, configure, update, delete",
        ["A user or service identity must be allowed to create, configure, update or delete projects, agents and "
         "connections",
         "Built-in roles: Foundry User (build and test), Foundry Project Manager, Foundry Account Owner, Foundry Owner",
         "! Management access is not call access: a manager isn't automatically allowed to call an agent at runtime"],
        S("id-overview", "rbac"))
    p2 = boundary_panel(
        cv, C3 + G3, y0, 2, "green", "Caller  ->  agent endpoint", "runtime access to the stable agent URL",
        ("User, app, service or channel", "the caller", "gray", "users"),
        ("Agent endpoint", "one URL for clients and channels", "green", "agent"),
        "token for Foundry or for the agent blueprint",
        ["The scheme on the endpoint decides how the caller's token is validated",
         "AzureRbac (alias Entra): token for https://ai.azure.com + Azure RBAC; least-privilege role Foundry Agent "
         "Consumer",
         "AgentBlueprint (preview): token for the agent's blueprint; the caller needs no Foundry role",
         "BotServiceRbac, BotServiceTenant and BotService (legacy) cover Teams and Microsoft 365 channels",
         "! API keys aren't supported for agent endpoints"],
        S("endpoint"))
    p3 = boundary_panel(
        cv, 2 * (C3 + G3), y0, 3, "orange", "Agent  ->  downstream tool", "the connection's authType decides",
        ("Agent Service runtime", "runs the agent, calls tools", "green", "agent"),
        ("MCP server, A2A agent or tool", "OpenAPI, toolbox, SaaS, Azure service", "orange", "mcp"),
        "credential chosen by the connection's authType",
        ["Downstream request can represent nobody, a stored key, the project, the agent or the signed-in user",
         "Foundry handles token acquisition, exchange, refresh and injection on the service side - never in agent code",
         "The downstream service then makes its own authorization decision",
         "+ Support differs by tool, protocol and channel: check the tool's page before choosing"],
        S("id-overview", "tool-auth"), here=True)
    bottom = max(p1.bottom, p2.bottom, p3.bottom)
    n = nt(cv, 0, bottom + 30, W, "Permissions don't carry across these boundaries. A principal that can manage an agent "
                                  "isn't automatically allowed to call it. A runtime caller isn't automatically "
                                  "authorized to reach downstream resources through the agent. And the agent's access to "
                                  "a resource doesn't give callers access to the agent.",
           kind="key", title="Why three boundaries matter", src=S("id-overview"))
    return n.bottom + 70


# ====================================================================== section 2: auth lives on the connection
def band_connection(cv, y):
    _, b = section_header(cv, 0, y, "2.  Authentication is a property of the connection, not code in your agent",
                          sub="You pick the authentication type once, when you create the project connection; "
                              "Foundry does acquisition, exchange, refresh and injection", size=34)
    y0 = b + 34
    cw, gap = 520, 100
    c1 = Card(cw, "1  Create it once", [
        "Foundry portal: connect a tool and pick the authentication type",
        "azd ai connection create <name> --kind remote-tool | remote-a2a --target <url> --auth-type <type>",
        "ARM / REST: category RemoteTool (MCP) or RemoteA2A (A2A)",
        "Chosen at creation - never in agent code",
        "! azd ai connection update can't change the auth type: create a new connection",
    ], theme="grape", icon="foundry", subtitle="portal, azd or ARM / REST", body_size=15, src=S("tool-auth", "mcp-tool"))
    c2 = Card(cw, "2  Project connection", [
        "category: RemoteTool (MCP) or RemoteA2A (A2A)",
        "target: the MCP or A2A endpoint URL",
        "authType: one of the seven modes in section 3",
        "audience: canonical Entra resource for the identity modes",
        "scopes: delegated permissions requested for the user modes",
        "credentials: keys, or OAuth client id and secret",
        "metadata: type generic_mcp (MCP) or ApiType Azure (A2A)",
        "Secrets sit in a Foundry-managed Key Vault unless you attach your own",
    ], theme="red", icon="key-vault", subtitle="authType + target + credentials", body_size=15,
        src=S("cfg-delegation", "connections"))
    c3 = Card(cw, "3  The agent tool points at it", [
        "mcp tool: server_label, server_url, allowed_tools, require_approval, project_connection_id",
        "If the connection's endpoint and server_url differ, the connection's endpoint is used",
        "a2a and toolbox tools carry project_connection_id the same way",
        "! OpenAPI tools need a connection even for anonymous access",
    ], theme="orange", icon="mcp", subtitle="mcp, a2a, OpenAPI or toolbox tool", body_size=15,
        src=S("mcp-auth", "a2a-tool"))
    c4 = Card(cw, "4  Agent Service does the auth", [
        "Acquires, exchanges, refreshes and injects the credential on the service side",
        "Keeps per-user credentials isolated by user and connection",
        "Hands your app oauth_consent_request and mcp_approval_request items when needed",
        "Your agent code stays free of authentication logic",
    ], theme="green", icon="agent", subtitle="per tool call, service side", body_size=15, src=S("tool-auth"))
    row(cv, 0, y0, [c1, c2, c3, c4], gap=gap)
    connect(cv, c1, c2, label="creates", label_size=14, sw=3)
    connect(cv, c2, c3, label="referenced by", label_size=14, sw=3, label_wrap=80)
    connect(cv, c3, c4, label="resolved by", label_size=14, sw=3, label_wrap=80)

    gx = 2 * (C3 + G3)        # third column of the 3-column grid
    s_card = Card(560, "Shared authentication", [
        "Every user of the agent reaches the tool with the same identity",
        "User context doesn't persist",
        "Modes: unauthenticated, key-based, Entra agent identity, Entra project managed identity",
        "+ Right when every user should get the same level of access",
    ], theme="gray", icon="users", body_size=15, src=S("mcp-auth"))
    i_card = Card(560, "Individual authentication", [
        "The tool reuses the Entra user context of the incoming agent request, or each user signs in separately",
        "User context persists, so the downstream service can trim results to that user's permissions",
        "Modes: UserEntraToken, AgentOnBehalfOfUser (preview), OAuth identity passthrough",
    ], theme="red", icon="managed-identity", body_size=15, src=S("mcp-auth", "delegation"))
    r_right, r_bottom = row(cv, gx, y0, [s_card, i_card], gap=40)
    tip = nt(cv, gx, r_bottom + 24, C3, "When in doubt, start with Microsoft Entra authentication if the MCP server supports "
                                        "it: no secrets to manage and built-in token rotation. For private MCP servers on "
                                        "a virtual network it is a natural fit.", kind="tip", title="Rule of thumb",
             src=S("mcp-auth"))
    return max(c1.bottom, c2.bottom, c3.bottom, c4.bottom, tip.bottom) + 70


# ====================================================================== section 3: the auth-mode ladder
MODE_W, MODE_GAP = 488, 30


def band_modes(cv, y):
    _, b = section_header(cv, 0, y, "3.  The auth-mode ladder - seven connection types, from shared to per-user",
                          sub="Pick by whose identity the tool must see. Colour = who owns the credential "
                              "(status labels as of 2026-11-03)", size=34)
    y0 = b + 30
    legend(cv, 0, y0, [("anonymous", "gray"), ("credential owned by the tool or provider: key, OAuth session", "orange"),
                       ("Microsoft Entra token: project MI, agent identity, user via on-behalf-of", "red")], size=16)
    step = MODE_W + MODE_GAP
    span1 = 4 * MODE_W + 3 * MODE_GAP
    x2 = 4 * step
    span2 = 3 * MODE_W + 2 * MODE_GAP
    ytxt, ybrace = y0 + 46, y0 + 128
    cv.text(0, ytxt, "SHARED identity - every user looks the same to the tool, user context is lost", size=22,
            color="#495057")
    cv.text(x2, ytxt, "INDIVIDUAL identity - the tool sees the user, user context persists", size=22, color="#c92a2a")
    hbrace(cv, 0, span1, ybrace, side="bottom", color="#495057")
    hbrace(cv, x2, x2 + span2, ybrace, side="bottom", color="#c92a2a")
    yt = ybrace + 36

    def lost():
        return "! User context is lost: everyone gets the same authority"

    tiles = [
        Card(MODE_W, "Unauthenticated", [
            "# Whose identity", "Nobody: the request is anonymous",
            "# Who holds what", "Nothing to hold or rotate",
            "# Use for", "Public servers, for example the Microsoft Learn MCP server",
            "Private servers that rely on network isolation instead of authentication",
            "OpenAPI tools still need a connection, even for anonymous access",
            "Check the server's terms of service and rate limits",
            lost()], theme="gray", icon="globe", subtitle="azd: none   |   ARM: None", body_size=15,
             src=S("mcp-auth")),
        Card(MODE_W, "Key-based", [
            "# Whose identity", "The principal tied to the stored key or PAT",
            "# Who holds what",
            "The secret sits in the project connection (Foundry-managed Key Vault unless you bring your own)",
            "Agent Service injects the header - the agent never sees the secret",
            "# Use for",
            "Key-based SaaS: Authorization header (GitHub PAT), x-api-key, custom header, Functions x-functions-key",
            "! Anyone with project access can read a stored key: store only shared secrets, rotate, least privilege",
            lost()], theme="orange", icon="key-vault", subtitle="azd: custom-keys   |   ARM: CustomKeys",
             body_size=15, src=S("mcp-auth", "tool-auth")),
        Card(MODE_W, "Project managed identity", [
            "# Whose identity", "The Foundry project's managed identity",
            "# Who holds what", "Microsoft Entra issues the token; Agent Service requests it for the connection's audience",
            "# Use for",
            "Shared project-level access to Azure resources and MCP servers; AI Search over a private VNet needs it",
            "Set the audience; grant RBAC on the target to the project MI (not the account MI)",
            lost()], theme="red", icon="managed-identity",
             subtitle="azd: project-managed-identity   |   ARM: ProjectManagedIdentity", body_size=15,
             src=S("mcp-auth", "a2a-auth")),
        Card(MODE_W, "Agent identity", [
            "# Whose identity", "The agent's own Entra agent identity (blueprint, then identity)",
            "# Who holds what",
            "Blueprint federated credential trusts the Azure Machine Learning resource-provider app: no client secret "
            "or certificate",
            "# Use for", "Per-agent audit and least privilege",
            "Grant RBAC to the agent identity's object ID - Foundry assigns no roles automatically",
            "! A user token is intentionally rejected",
            lost()], theme="red", icon="agent", subtitle="azd: agentic-identity   |   ARM: AgenticIdentityToken",
             body_size=15, src=S("agent-identity", "mcp-auth")),
        Card(MODE_W, "OAuth identity passthrough", [
            "# Whose identity", "The user who completes OAuth consent - per user, per tool",
            "# Who holds what",
            "Agent Service stores access + refresh tokens scoped to user + connection and refreshes them "
            "(add offline_access)",
            "# Use for", "Per-user third-party or Entra-protected MCP and A2A servers",
            "Managed OAuth (publisher- or Microsoft-managed app, --connector-name) or custom OAuth (your app "
            "registration)",
            "Callers need Foundry Agent Consumer and the project's tenant",
            "+ User context persists: consent per user per tool"], theme="orange", icon="oauth",
             subtitle="azd: oauth2   |   ARM: OAuth2", body_size=15, src=S("mcp-auth", "a2a-auth")),
        Card(MODE_W, "UserEntraToken", [
            "# Whose identity",
            "The signed-in user via on-behalf-of. Actor = Foundry (Foundry-audience token) or the agent identity "
            "(blueprint-audience token)",
            "# Who holds what", "Agent Service does the exchange; your app never sees the downstream token",
            "# Use for",
            "A limited set of Microsoft-owned tools (Fabric IQ, Foundry MCP, Dataverse, Azure DevOps MCP, Sentinel, "
            "Work IQ M365 servers) and A2A to Foundry agents (compat path)",
            "Foundry as actor needs no extra consent grant",
            "+ User context persists: the tool trims data to the user"], theme="red", icon="users",
             subtitle="azd: user-entra-token   |   ARM: UserEntraToken", body_size=15,
             src=S("delegation", "cfg-delegation")),
        Card(MODE_W, "AgentOnBehalfOfUser", [
            "# Whose identity", "The user plus the agent identity as actor: the downstream token represents both",
            "# Who holds what",
            "Agent Service does the exchange; needs the AgentBlueprint endpoint scheme and a blueprint-audience token",
            "# Use for",
            "Your own Entra-protected MCP servers; Work IQ MCP and Azure Databricks Genie MCP (AgentOnBehalfOfUser "
            "only, not UserEntraToken)",
            "Scopes required: exact, fully qualified, one downstream resource per connection",
            "Conditional Access can govern the calls",
            "+ User context persists, and the resource can authorize the agent too"], theme="red",
             icon="app-registrations", badge="preview",
             subtitle="azd: use the connection API   |   ARM: AgentOnBehalfOfUser", body_size=15,
             src=S("cfg-delegation", "delegation")),
    ]
    r, tb = row(cv, 0, yt, tiles, gap=MODE_GAP)
    # configuration reference + managed OAuth catalogue
    y1 = tb + 56
    left_w = 2 * C3 + G3
    cfg = Table(
        [("Mode", 250), ("azd --auth-type", 230), ("azd extra flags", 400), ("ARM authType", 240),
         ("Properties on the connection", 560), ("Watch out", 700)],
        [
            [("Unauthenticated", "gray"), "none", "-", "None", "-",
             "Even anonymous OpenAPI tools need a connection"],
            [("Key-based", "orange"), "custom-keys (api-key for some kinds)", '--custom-key "Header=Value" (repeatable)',
             "CustomKeys", "Credentials.Keys: header name = value",
             "Header name and value format must match the server: Authorization, X-API-Key, Api-Key; Bearer token or "
             "bare token"],
            [("Project managed identity", "red"), "project-managed-identity", "--audience (optional)",
             "ProjectManagedIdentity", "audience",
             "Assign the project's system-assigned MI the RBAC role on the target; role changes can take up to 10 "
             "minutes"],
            [("Agent identity", "red"), "agentic-identity", "--audience", "AgenticIdentityToken", "audience",
             "Assign RBAC to the agent identity; for a Foundry agent target use audience https://ai.azure.com"],
            [("OAuth passthrough", "orange"), "oauth2",
             "--connector-name (managed) or --authorization-url --token-url --client-id --client-secret --scopes",
             "OAuth2",
             "connectorName (managed); or credentials.clientId / clientSecret, authorizationUrl, tokenUrl, refreshUrl, "
             "scopes (custom)",
             "Custom OAuth connections can't be updated: recreate. Foundry returns a redirect URL to add to your "
             "OAuth app"],
            [("UserEntraToken", "red"), "user-entra-token", "--audience", "UserEntraToken",
             "audience (required), scopes (optional: defaults per recognized target)",
             "The actor follows the incoming token's audience: Foundry or agent identity"],
            [("AgentOnBehalfOfUser (preview)", "red"), "not in azd: use the project connection API", "-",
             "AgentOnBehalfOfUser", "scopes (required): exact, fully qualified, one resource",
             "Endpoint must use AgentBlueprint; not available through AzureRbac or its Entra alias"],
        ], w=left_w, theme="red", size=14, head_size=15, title="Connection configuration, by authentication type",
        title_size=24)
    cfg.place(cv, 0, y1)
    mx = 2 * (C3 + G3)
    managed = Table(
        [("MCP server", 640), ("--connector-name", 520)],
        [["Azure Databricks Genie", "foundrydatabricksmcp"], ["GitHub", "foundrygithubmcp"],
         ["Infobip WhatsApp MCP server", "foundryinfobipmcp"], ["Infobip RCS MCP server", "foundryinfobiprcsmcp"],
         ["Infobip SMS MCP server", "foundryinfobipsmsmcp"], ["LSEG Data and Analytics", "foundrylsegmcp"],
         ["Morningstar MCP Server", "foundrymorningstarmcp"], ["Neon", "foundryneonmcp"],
         ["Pipedream", "foundrypipedreammcp"], ["Vercel", "foundryvercelmcp"]],
        w=C3, theme="orange", size=14, head_size=15, title="Managed OAuth: the 10 servers with a Foundry-managed app",
        title_size=22)
    managed.place(cv, mx, y1)
    nt(cv, mx, managed.bottom + 18, C3, "Only these MCP servers support a Foundry-managed OAuth app. For other "
                                        "OAuth-enabled MCP servers, bring your own app registration (custom OAuth).",
       kind="info", src=S("mcp-tool"))
    return max(cfg.bottom, managed.bottom + 90) + 70


# ====================================================================== section 4: who holds which token
SEQ_W = dict(head_w=200, spacing=304, head_h=84)


def seq_panel(cv, x, y, spec, min_h=0):
    letter, title, sub, theme, fn, is_preview, ledger_items = spec
    with cv.panel(x, y, title=f"{letter}   {title}", sub=sub, theme=theme, style="dotted", fill="none", pad=24,
                  title_size=28, sub_size=15, w=C3, min_h=min_h) as p:
        if is_preview:
            draw_badge(cv, x + C3 - 24 - 74, y + 24, "preview", size=14)
        bottom = fn(cv, p.ix, p.iy + 6)
        card = Card(C3 - 48, "Token ledger", ledger_items, theme=theme, fill="soft", body_size=15, title_size=19)
        card.place(cv, p.ix, max(bottom + 26, y + min_h - 24 - card.h))
    return p


def seq_row(cv, y, specs):
    heights = []
    for i, sp in enumerate(specs):
        scratch = Canvas(f"measure{i}")
        heights.append(seq_panel(scratch, 0, 0, sp).h)
    hmax = max(heights)
    panels = [seq_panel(cv, i * (C3 + G3), y, sp, min_h=hmax) for i, sp in enumerate(specs)]
    return max(p.bottom for p in panels)


def seq_a(cv, x, y):
    s = Seq(cv, x, y, [("Developer or admin", "gray", "users"), ("Agent Service", "green", "agent"),
                       ("Project connection", "red", "key-vault"), ("MCP, A2A or OpenAPI tool", "orange", "mcp")],
            **SEQ_W)
    s.msg(0, 2, "create the connection: custom-keys, Header=Value (portal, azd or ARM)", num=1,
          note="stored in the project connection - Foundry-managed Key Vault unless you attach your own")
    s.selfmsg(1, "model calls the tool; runtime resolves project_connection_id", num=2)
    s.msg(1, 2, "read the credential", num=3)
    s.msg(2, 1, "Header=Value - the agent never sees the secret", dash="dashed")
    s.msg(1, 3, "tool request with the injected header: Authorization, x-api-key or custom", num=4)
    s.selfmsg(3, "authorizes the principal behind the key", num=5)
    s.msg(3, 1, "result", dash="dashed")
    return s.end()


def seq_b(cv, x, y):
    s = Seq(cv, x, y, [("Admin", "gray", "users"), ("Agent Service", "green", "agent"),
                       ("Microsoft Entra ID", "red", "app-registrations"), ("Target service", "orange", "mcp")],
            **SEQ_W)
    s.msg(0, 3, "assign RBAC on the target to the agent identity's object ID (Foundry assigns none)")
    s.selfmsg(1, "tool call; connection = agentic-identity + audience (for example https://storage.azure.com)")
    s.msg(1, 2, "present the blueprint credential (federated: no secret or certificate)", num=1)
    s.msg(2, 1, "agent identity token", dash="dashed", num=2)
    s.msg(1, 2, "present it and request a token scoped to the downstream audience", num=3)
    s.msg(2, 1, "access token for that audience", dash="dashed")
    s.msg(1, 3, "call the MCP or A2A endpoint with the bearer token", num=4)
    s.selfmsg(3, "validates the token and checks the agent identity's RBAC")
    s.msg(3, 1, "result", dash="dashed")
    return s.end()


def seq_c(cv, x, y):
    s = Seq(cv, x, y, [("User and client app", "gray", "users"), ("Agent Service", "green", "agent"),
                       ("OAuth provider (IdP)", "red", "oauth"), ("MCP server", "orange", "mcp")], **SEQ_W)
    s.note(0, 2, "Admin first: an oauth2 connection (managed: --connector-name; custom: add Foundry's redirect URL "
                 "to your OAuth app). Callers need Foundry Agent Consumer and the project's tenant.", kind="info")
    s.msg(0, 1, "first request that needs the tool", num=1)
    s.msg(1, 0, "output item oauth_consent_request with consent_link", dash="dashed", num=2)
    s.msg(0, 2, "open the link in a browser: sign in and consent (scopes incl. offline_access)", num=3)
    s.msg(2, 1, "access + refresh tokens, stored per user and connection", dash="dashed", num=4)
    s.msg(0, 1, "continue the response (previous_response_id)", num=5)
    s.msg(1, 3, "tool call with the user's access token", num=6)
    s.msg(3, 1, "result under the user's own permissions", dash="dashed")
    s.selfmsg(1, "later: the refresh token renews the access token (about 1 h)", num=7)
    return s.end()


def seq_d(cv, x, y):
    s = Seq(cv, x, y, [("User and client app", "gray", "users"), ("Agent Service", "green", "agent"),
                       ("Microsoft Entra ID", "red", "app-registrations"), ("Microsoft-owned tool", "orange", "mcp")],
            **SEQ_W)
    s.msg(0, 2, "sign in; request a token for Foundry (audience https://ai.azure.com)", num=1)
    s.msg(2, 0, "user token", dash="dashed")
    s.msg(0, 1, "call the agent endpoint with that token (AzureRbac)", num=2)
    s.selfmsg(1, "Azure RBAC check: interact/action (Foundry Agent Consumer)", num=3)
    s.msg(1, 2, "on-behalf-of exchange with the connection audience and scopes; actor = Foundry", num=4)
    s.msg(2, 1, "downstream token for the user (no extra consent grant)", dash="dashed")
    s.msg(1, 3, "tool call with the bearer token - your app never sees it", num=5)
    s.selfmsg(3, "authorizes the USER: permission trimming", num=6)
    s.msg(3, 1, "only what the user may see", dash="dashed")
    return s.end()


def seq_e(cv, x, y):
    s = Seq(cv, x, y, [("User and client app", "gray", "users"), ("Agent Service", "green", "agent"),
                       ("Microsoft Entra ID", "red", "app-registrations"), ("Entra-protected MCP server", "orange", "mcp")],
            **SEQ_W)
    s.note(0, 3, "Needs: AgentBlueprint scheme on the endpoint (keep AzureRbac while any client still uses the Foundry "
                 "audience), an AgentOnBehalfOfUser connection with exact scopes, and blueprint requiredResourceAccess "
                 "+ inheritablePermissions declared (bookkeeping - grants nothing).", kind="preview")
    s.msg(0, 2, "sign in; request a token for the agent blueprint (api://<blueprint-client-id>/access_agent)", num=1)
    s.msg(0, 1, "call the agent endpoint with the blueprint-audience token", num=2)
    s.selfmsg(1, "validate token_validation_rules: audiences, tenants, clients, principals, permissions", num=3)
    s.msg(1, 2, "exchange for the connection scopes; actor = agent identity", num=4)
    s.msg(1, 0, "no grant yet: oauth_consent_request with consent_link (for the agent identity)", dash="dashed", num=5)
    s.msg(0, 2, "user or tenant admin consents (or the resource preauthorizes the blueprint)", num=6)
    s.msg(1, 2, "retry the exchange: token for user + agent actor", num=7)
    s.msg(1, 3, "tool call with the downstream token", num=8)
    s.selfmsg(3, "authorizes the user, can authorize the agent; Conditional Access can govern")
    s.msg(3, 1, "result", dash="dashed")
    return s.end()


def seq_f(cv, x, y):
    s = Seq(cv, x, y, [("User", "gray", "users"), ("Agent or MCP client", "green", "agent"),
                       ("Toolbox MCP endpoint", "orange", "toolbox-icon"), ("Downstream tool", "orange", "mcp")],
            **SEQ_W)
    s.msg(1, 2, "tools/call + Entra token (scope https://ai.azure.com/.default) + x-agent-foundry-call-id", num=1)
    s.selfmsg(2, "authorize the agent identity (gates the toolbox, not each tool); guardrail screens input", num=2)
    s.selfmsg(2, "find the tool's connection; inject the credential by authType", num=3)
    s.msg(2, 1, "first use of a per-user OAuth tool: error -32006 CONSENT_REQUIRED + URL", dash="dashed", num=4)
    s.msg(1, 0, "show the consent link; the user signs in (Foundry stores the tokens)", dash="dashed", num=5)
    s.msg(1, 2, "retry tools/call", num=6)
    s.msg(2, 3, "call with the injected credential", num=7)
    s.msg(3, 2, "result", dash="dashed")
    s.selfmsg(2, "guardrail screens the output")
    s.msg(2, 1, "MCP result", dash="dashed")
    return s.end()


def band_sequences(cv, y):
    _, b = section_header(cv, 0, y, "4.  Who holds which token - one sequence per mode",
                          sub="Read each lane as an identity: who presents a token, for which audience, and who "
                              "finally authorizes the call", size=34)
    y0 = b + 28
    legend(cv, 0, y0, [("user, client or admin", "gray"), ("Agent Service / agent", "green"),
                       ("Microsoft Entra ID or OAuth provider", "red"), ("MCP server, tool or toolbox", "orange")],
           size=16)
    cv.text(1900, y0, "solid arrow = request, dashed = response, numbers = steps (restart in each diagram)", size=16,
            color="#495057")
    y1 = y0 + 52
    bottom = seq_row(cv, y1, [
        ("A", "Key-based (custom-keys)", "shared secret in the connection - the key's principal reaches the tool",
         "orange", seq_a, False, [
             "Presented to the tool: the stored key, as a header value",
             "Held by: the project connection (Foundry-managed Key Vault unless you bring your own)",
             "Actor: whoever owns the key - not the user, not the agent",
             "! Anyone with project access can read the key: store only shared secrets, rotate, least privilege"]),
        ("B", "Agent identity / project MI", "keyless Entra token - the agent (or project) is the principal",
         "red", seq_b, False, [
             "Presented to the tool: the agent identity's access token (the project MI's for project-managed-identity)",
             "Audience: the connection's audience, for example https://storage.azure.com",
             "Actor: the agent identity itself - no user. Project MI: same shape in one step",
             "! agentic-identity rejects user tokens; hosted-agent sandboxes hold no blueprint credential"]),
        ("C", "OAuth identity passthrough", "per-user OAuth session - the user who consented reaches the tool",
         "orange", seq_c, False, [
             "Presented to the tool: the user's OAuth access token (about 1 h); the refresh token stays in Agent Service",
             "Held by: Agent Service, per user and connection",
             "Actor: the user who consented - no agent identity exchange",
             "! Declined consent fails the call; a revoked refresh token means consent again"])])
    bottom2 = seq_row(cv, bottom + 50, [
        ("D", "UserEntraToken", "on-behalf-of with Foundry as actor - the user is the principal",
         "red", seq_d, False, [
             "Presented to the tool: a downstream token for the user (on-behalf-of)",
             "Audience and scopes: the connection's audience; default scopes per recognized target unless set",
             "Actor: Foundry, because the incoming token's audience is Foundry",
             "! With a blueprint-audience token the actor flips to the agent identity and consent may be needed (E)"]),
        ("E", "AgentOnBehalfOfUser", "on-behalf-of with the agent identity as actor - user + agent",
         "red", seq_e, True, [
             "Presented to the tool: a downstream token for the user and the agent",
             "Audience and scopes: one downstream resource per connection, exact fully qualified scopes",
             "Actor: the agent identity (incoming audience = agent blueprint); authorizes user and agent",
             "! Endpoint consent (client to agent) and downstream consent (agent to resource) are separate"]),
        ("F", "Toolbox call: two identities", "agent to toolbox is one boundary, toolbox to tool is another",
         "orange", seq_f, False, [
             "Agent to toolbox: the agent's Entra token, scope https://ai.azure.com/.default (+ call id for hosted agents)",
             "Toolbox to tool: the connection's credential - key, project MI, agent identity, user OAuth or user token",
             "Actors: the agent identity gates the toolbox; the user is the principal for per-user tools",
             "! Direct clients: no agent blueprint sign-in, no AgentOnBehalfOfUser - use per-tool OAuth2, handle -32006"])])
    return bottom2 + 80


# ====================================================================== section 5: deep dives
def cite(cv, x, y, *keys):
    """Clickable 'Learn:' lines under a table (Cards and Notes carry their own)."""
    for k in keys:
        label, url = LINKS[k]
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 3
    return y


def deep_actor(cv, x, y):
    with cv.panel(x, y, title="Who is the actor? The incoming token's audience decides", theme="red", style="dotted",
                  fill="none", pad=24, title_size=26, sub="user delegation through Microsoft Entra on-behalf-of",
                  sub_size=15, w=C3) as p:
        bw, bh = 330, 116
        gap = (C3 - 48 - 3 * bw) / 2
        hx = [p.ix + i * (bw + gap) for i in range(3)]
        hy = p.iy + 4
        for xx, t in zip(hx, ("Incoming token (caller to agent)", "Who acts for the user", "Consent at the resource")):
            cv.text(xx, hy, t, size=16, color="#495057")
        ya = hy + 30
        a1 = Box(bw, "Token for Foundry", sub="https://ai.azure.com - AzureRbac or Entra scheme", theme="gray",
                 h=bh).place(cv, hx[0], ya)
        a2 = Box(bw, "Actor = Foundry", sub="UserEntraToken only; a limited set of Microsoft-owned tools",
                 theme="red", h=bh).place(cv, hx[1], ya)
        a3 = Box(bw, "No extra consent grant", sub="not available for custom or third-party servers", theme="green",
                 h=bh).place(cv, hx[2], ya)
        yb = ya + bh + 30
        b1 = Box(bw, "Token for the agent blueprint", sub="api://<blueprint-client-id>/access_agent - AgentBlueprint "
                                                           "scheme (preview)", theme="gray", h=bh).place(cv, hx[0], yb)
        b2 = Box(bw, "Actor = agent identity", sub="UserEntraToken (conditional) or AgentOnBehalfOfUser (always); "
                                                    "preview", theme="red", h=bh).place(cv, hx[1], yb)
        b3 = Box(bw, "User, admin or preauthorization", sub="consent for the individual agent identity",
                 theme="violet", h=bh).place(cv, hx[2], yb)
        for a, b_ in ((a1, a2), (a2, a3), (b1, b2), (b2, b3)):
            connect(cv, a, b_, sw=3)
        nt(cv, p.ix, yb + bh + 28, C3 - 48,
           "Foundry development clients, Azure Bot Service integrations and routines keep using the Foundry audience "
           "(routine dispatch doesn't support AgentBlueprint). Keep AzureRbac or its Entra alias while any of them "
           "calls the agent.", kind="warn", title="Keep AzureRbac while any client still needs it",
           src=S("delegation", "endpoint"))
    return p.bottom


def deep_endpoint(cv, x, y):
    t = Table([("Scheme", 215), ("Token audience", 225), ("How access is decided", 410), ("Notes", 310)], [
        [("AzureRbac (alias Entra, never both)", "green"), "Foundry resource: https://ai.azure.com",
         "Azure RBAC: interact/action at project or agent scope. Foundry Agent Consumer is the least-privilege role; "
         "Foundry User also works", "Default scheme. Agent-scope assignments reach one agent only"],
        [("AgentBlueprint (preview)", "violet"),
         "The agent's blueprint; default scope api://<agent-blueprint-client-id>/access_agent",
         "token_validation_rules: audiences, tenants, clients, principals, delegated permissions. App-only tokens "
         "need a non-empty allowed_clients list",
         "No Foundry role for the caller. Foundry preauthorizes portal, CLI and VS Code clients. Routines don't "
         "support it"],
        [("BotServiceRbac", "gray"), "Azure Bot Service channel",
         "The channel is validated, then Azure RBAC decides per signed-in user",
         "Teams and Microsoft 365; sign-in prompt in the conversation"],
        [("BotServiceTenant", "gray"), "Azure Bot Service channel",
         "Fixed rule: the signed-in user must be in the configured tenant", "No per-user Foundry RBAC needed"],
        [("BotService (legacy)", "gray"), "Azure Bot Service channel",
         "No extra user rule once the channel is validated",
         "Legacy only; configure just one of the three BotService schemes"],
    ], w=C3, theme="green", size=14, head_size=15, title="Agent endpoint schemes (caller to agent)", title_size=22)
    t.place(cv, x, y)
    return cite(cv, x, t.bottom + 8, "endpoint", "cfg-endpoint")


def deep_iq(cv, x, y):
    n = nt(cv, x, y, C3, "Foundry IQ knowledge bases use on-behalf-of access with target-specific source "
                         "authorization: Agent Service dynamically sets x-ms-query-source-authorization to the "
                         "signed-in user's Azure AI Search token (https://search.azure.com/user_impersonation), whether "
                         "the incoming token targets Foundry or the agent blueprint. Missing consent can return an "
                         "oauth_consent_request.", kind="key", title="Foundry IQ source authorization",
           src=S("delegation"))
    return n.bottom


def deep_scopes(cv, x, y):
    both = "UserEntraToken or AgentOnBehalfOfUser"
    t = Table([("Tool", 330), ("Connection auth types", 210), ("Delegated scope(s)", 570)], [
        [("Azure Databricks Genie MCP", "violet"), ("AgentOnBehalfOfUser only", "violet"),
         "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/user_impersonation"],
        [("Work IQ MCP (preview)", "violet"), ("AgentOnBehalfOfUser only", "violet"),
         "api://workiq.svc.cloud.microsoft/WorkIQAgent.Ask"],
        ["Azure DevOps MCP", both, "api://2a72489c-aab2-4b65-b93a-a91edccf33b8/Ado.Mcp.Tools"],
        ["Fabric IQ: Fabric Data Agent, also with workspace private link (preview)", both,
         "https://analysis.windows.net/powerbi/api/DataAgent.Execute.All"],
        ["Fabric IQ ontology (preview)", both,
         "https://analysis.windows.net/powerbi/api/Item.Execute.All and https://analysis.windows.net/powerbi/api/"
         "Item.Read.All"],
        ["Fabric IQ Power BI semantic model (preview)", both,
         "https://analysis.windows.net/powerbi/api/Item.Read.All, https://analysis.windows.net/powerbi/api/"
         "Item.Execute.All and https://analysis.windows.net/powerbi/api/Dataset.Read.All"],
        ["Foundry MCP (preview)", both, "https://mcp.ai.azure.com/Foundry.Mcp.Tools"],
        ["Microsoft Dataverse", both, "api://ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/McpServers.Dataverse.All"],
        ["Sentinel: Data Exploration, Graph, Knowledge Objects, Memory", both,
         "4500ebfb-89b6-4b14-a480-7f749797bfcd/.default"],
        ["Work IQ (preview): Calendar, Copilot, Mail, OneDrive, SharePoint, Teams, User, Word", both,
         "api://ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/McpServers.{Calendar, CopilotMCP, Mail, OneDrive, SharePoint, "
         "Teams, Me, Word}.All"],
    ], w=C3, theme="red", size=14, head_size=15, title="Supported delegated targets and scopes", title_size=22)
    t.place(cv, x, y)
    n = nt(cv, x, t.bottom + 18, C3,
           "UserEntraToken: omit scopes to use these defaults, or set them explicitly. AgentOnBehalfOfUser: scopes are "
           "required - exact, fully qualified, one downstream resource per connection (never combine resources). "
           "Custom MCP servers aren't listed: get the scopes from the server's publisher and use AgentOnBehalfOfUser.",
           kind="info", title="Reading the table", src=S("cfg-delegation"))
    return n.bottom


def deep_migration(cv, x, y):
    c = Card(C3, "Migrate: Azure RBAC to agent blueprint access", [
        "= 1  Inventory the connection target, audience, scopes and existing consent grants",
        "= 2  Keep the UserEntraToken connection; add the AgentBlueprint scheme next to AzureRbac",
        "= 3  Test blueprint-audience tokens - no new connection needed, the actor follows the token's audience",
        "= 4  Complete downstream consent for the blueprint where required",
        "= 5  Verify the tool call and user isolation, then move clients over",
        "= 6  Remove AzureRbac or Entra once no client or channel needs the Foundry audience",
        "= 7  Optional: update in place to AgentOnBehalfOfUser - change authType, remove audience, set exact scopes "
        "- and validate again",
        "# Coming from another auth type?",
        "Create a separate AgentOnBehalfOfUser connection, attach it only to a test agent version, never expose both "
        "connections for the same tool in one version, and keep the old one for rollback",
    ], theme="red", badge="preview", icon="versions", subtitle="from the user delegation migration guidance",
        body_size=15, src=S("cfg-delegation", "cfg-endpoint"))
    c.place(cv, x, y)
    return c.bottom


def deep_consent(cv, x, y):
    with cv.panel(x, y, title="Delegated consent: two boundaries, six elements", theme="red", style="dotted",
                  fill="none", pad=24, title_size=26, sub="who may authorize what, and where each setting lives",
                  sub_size=15, w=C3) as p:
        bw = 260
        gap = (C3 - 48 - 3 * bw) / 2
        yy = p.iy + 6
        c = Box(bw, "Client app", sub="signed-in user", theme="gray", icon="users", icon_pos="left",
                h=96).place(cv, p.ix, yy)
        a = Box(bw, "Agent", sub="blueprint + agent identity", theme="green", icon="agent", icon_pos="left",
                h=96).place(cv, p.ix + bw + gap, yy)
        r = Box(bw, "Downstream resource", sub="Graph, Search, MCP server", theme="orange", icon="mcp",
                icon_pos="left", h=96).place(cv, p.ix + 2 * (bw + gap), yy)
        connect(cv, c, a, num=1, label="endpoint consent", label_wrap=120, sw=3)
        connect(cv, a, r, num=2, label="downstream consent", label_wrap=120, sw=3)
        intro = Card(C3 - 48, None, [
            "= 1  Endpoint consent: AzureRbac asks for Foundry's delegated permission; AgentBlueprint asks for the "
            "permission the blueprint exposes",
            "= 2  Downstream consent: lets the blueprint obtain a token for the resource with the consented scopes, "
            "in the user's context",
            "! A grant at one boundary never satisfies the other. OAuth2 connections use a separate, provider-owned "
            "session instead",
        ], theme="red", fill="soft", body_size=15)
        intro.place(cv, p.ix, yy + 96 + 26)
        t = Table([("Element", 255), ("Where it lives", 255), ("Question it answers", 602)], [
            ["Connection scopes", "Foundry project connection", "Which delegated permissions does Agent Service request "
                                                                  "for this tool?"],
            ["requiredResourceAccess", "Agent blueprint", "Which downstream permissions does the blueprint declare for "
                                                          "administrator review?"],
            ["inheritablePermissions", "Agent blueprint", "Which granted permissions can flow from the blueprint "
                                                          "principal to its agent identities?"],
            ["api.preAuthorizedApplications", "Downstream resource app registration",
             "Which clients may request specific delegated permissions without a prompt?"],
            ["Consent grant", "Microsoft Entra tenant", "Has a user or administrator authorized the application to "
                                                        "request those permissions?"],
            ["Resource authorization", "Downstream resource", "Does the signed-in user have access to the data or "
                                                              "operation?"],
        ], w=C3 - 48, theme="red", size=14, head_size=15, title="How permissions become available to an agent identity",
            title_size=20)
        t.place(cv, p.ix, intro.bottom + 24)
        w2 = (C3 - 48 - 30) / 2
        ways = Card(w2, "Three ways to authorize", [
            "Interactive user consent: tenant policy must let the user consent",
            "Tenant administrator consent: central review, no prompts",
            "Preauthorization: the resource owner lists the blueprint in api.preAuthorizedApplications",
            "The consent link asks for the individual agent identity; watch for {projectEndpoint}/consent/done",
        ], theme="red", fill="soft", body_size=15, src=S("consent"))
        policy = Card(w2, "Tenant policy decides if the link works", [
            "Default: only low-impact permissions for qualifying apps",
            "User consent disabled: the link appears but fails - use admin consent or preauthorization",
            "Custom: organization-defined conditions",
            "Entra Application Developer role lets a developer consent on their own behalf for eligible permissions",
        ], theme="red", fill="soft", body_size=15, src=S("consent"))
        _, rb = row(cv, p.ix, t.bottom + 24, [ways, policy], gap=30)
        nt(cv, p.ix, rb + 22, C3 - 48,
           "Declaring a permission doesn't grant it, and inheritance doesn't create a grant. Collaborators don't "
           "inherit your grants: shared or published agents need admin consent or preauthorization (autopilot "
           "blueprint approval shows the permissions to the administrator). Removing a scope doesn't revoke a "
           "grant. Consent is per resource.", kind="info", title="Lifecycle", src=S("consent", "cfg-delegation"))
    return p.bottom


def deep_identity(cv, x, y):
    with cv.panel(x, y, title="Agent identity internals", theme="red", style="dotted", fill="none", pad=24,
                  title_size=26, sub="blueprint, identity and the federated credential", sub_size=15, w=C3) as p:
        bw = 300
        gap = (C3 - 48 - 3 * bw) / 2
        yy = p.iy + 8
        b1 = Box(bw, "Azure Machine Learning RP app", sub="0736f41a-0425-4b46-bdb5-1563eff02385", theme="gray",
                 h=108).place(cv, p.ix, yy)
        b2 = Box(bw, "Agent identity blueprint", sub="the agent's template and parent; sign-in point for the "
                                                      "AgentBlueprint scheme", theme="red", h=108).place(
            cv, p.ix + bw + gap, yy)
        b3 = Box(bw, "Agent identity", sub="special service principal for the agent instance", theme="red",
                 h=108).place(cv, p.ix + 2 * (bw + gap), yy)
        connect(cv, b1, b2, label="trusted by the blueprint's federated credential", label_wrap=170, sw=3,
                label_size=13)
        connect(cv, b2, b3, label="parent; may impersonate", label_wrap=130, sw=3, label_size=13)
        card = Card(C3 - 48, None, [
            "Creating an agent provisions a unique blueprint and a default-instance identity; Foundry assigns no RBAC "
            "roles automatically",
            "No client secret or certificate: projects, agent code and the project managed identity never hold the "
            "credential",
            "Legacy agents share a project-level identity; migrating changes the identity - role assignments don't "
            "transfer",
            "Entra shows agent identities tenant-wide: Conditional Access, Identity Protection, owners, sponsors, "
            "expiry, sign-in and audit logs by agentType and blueprintId",
            "Hosted agents: each session runs in a VM-isolated sandbox without the blueprint credential; code gets "
            "tokens from the token service, and the project MI isn't available to it",
        ], theme="red", fill="soft", body_size=15, src=S("agent-identity"))
        card.place(cv, p.ix, yy + 108 + 30)
    return p.bottom


def deep_toolbox(cv, x, y):
    c = Card(C3, "Toolbox and direct clients: the constraints", [
        "Two boundaries: agent to toolbox uses the agent's Entra identity (scope https://ai.azure.com/.default); "
        "toolbox to tool uses each connection's authType",
        "Hosted agents: FoundryToolbox (Python) or AddFoundryToolboxes (.NET) forwards x-agent-foundry-call-id so the "
        "toolbox resolves the caller - never hard-code or reuse it",
        "! Direct toolbox clients can't use agent blueprint sign-in to reach the toolbox, and can't use "
        "AgentOnBehalfOfUser for downstream tools",
        "Direct clients use per-tool OAuth2 and must surface the consent request (-32006) and continue - a generic "
        "MCP client won't do it for you",
        "Service-to-service callers multiplexing users set x-ms-user-identity (stable per user) to partition OAuth state",
        "! Work IQ MCP and Azure Databricks Genie MCP support AgentOnBehalfOfUser only - not UserEntraToken",
    ], theme="orange", icon="toolbox-icon", subtitle="agent-mediated vs direct access", body_size=15,
        src=S("tool-auth", "toolbox"))
    c.place(cv, x, y)
    return c.bottom


def deep_oauth(cv, x, y):
    c1 = Card(C3, "Custom OAuth: what Foundry needs", [
        "Client ID (required) and client secret (optional, depends on your OAuth app)",
        "Authorization URL and Token URL (required)",
        "Refresh URL (required): reuse the token URL if there is no separate refresh endpoint",
        "Scopes: include offline_access for automatic refresh; portal and spec use a single space between scopes",
        "Foundry returns a redirect URL after configuration - add it to your OAuth app registration",
        "! Custom OAuth connections can't be updated: recreate them",
    ], theme="orange", icon="oauth", body_size=15, src=S("mcp-auth"))
    c1.place(cv, x, y)
    c2 = Card(C3, "Agent 365 MCP servers via your own Entra app (Frontier tenants only)", [
        "Resource app Agent 365 Tools, id ea9ffc3e-8a23-4a7d-836d-234d7c7565c1: grant admin consent in your tenant",
        "Delegated permissions (each .All): McpServers.Mail, Calendar, Teams, Me, OneDriveSharepoint, SharepointLists, "
        "Word, CopilotMCP, M365Admin, Dataverse",
        "Scopes: ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/{permission} offline_access (space-separated)",
        "Authorization and token URLs: https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/authorize and /token; "
        "the refresh URL is the /token endpoint",
    ], theme="orange", icon="m365", body_size=15, src=S("mcp-auth"))
    c2.place(cv, x, c1.bottom + 40)
    return c2.bottom


def deep_server(cv, x, y):
    c = Card(C3, "Your own Entra-protected MCP server", [
        "Register it as an app: v2 access tokens (requestedAccessTokenVersion 2) and an Application ID URI equal to the "
        "server URL - clients send resource=<URL>",
        "Define delegated scopes such as tool.read or tool.execute: the fully qualified scope goes on an "
        "AgentOnBehalfOfUser connection",
        "Optional app roles for agent identities: assigned roles arrive in the roles claim for app-only callers",
        "Validate every token with a library: signature, iss, tid, aud, expiry, then scp or roles",
        "Publish protected resource metadata (RFC 9728) and answer unauthenticated calls with 401 + WWW-Authenticate",
        "! Don't rely on passing your server's token on to a downstream Microsoft service: Foundry blocks Microsoft "
        "audiences to untrusted MCP endpoints",
    ], theme="orange", icon="mcp", subtitle="the server side of delegation", body_size=15,
        src=S("entra-mcp", "mcp-auth"))
    c.place(cv, x, y)
    return c.bottom


def deep_a2a(cv, x, y):
    c = Card(C3, "A2A authentication: the same menu, plus the agent card", [
        "Same modes as MCP: key-based, Entra agent identity, Entra project MI, client user delegation, OAuth "
        "passthrough, unauthenticated",
        "The agent card fetch is anonymous by default; for a protected card path set send_credentials_for_agent_card "
        "to true (credentials go only to the base_url host, over HTTPS)",
        "Foundry agent target: connection target https://{account}.services.ai.azure.com/api/projects/{project}/"
        "agents/{agent}/endpoint/protocols/a2a, audience https://ai.azure.com, no agent card path",
        "The target must enable incoming A2A (preview) and the caller needs Foundry Agent Consumer on it",
        "App-only call: agentic-identity with audience https://ai.azure.com; delegated: UserEntraToken (compat) or "
        "AgentOnBehalfOfUser (preview)",
        "Protocol 1.0 (GA, JSON-RPC) or 0.3 (preview); text only, no streaming responses",
    ], theme="green", icon="a2a", body_size=15, src=S("a2a-auth", "a2a-tool"))
    c.place(cv, x, y)
    with cv.panel(x, c.bottom + 40, title="A2A call to a Foundry agent", theme="green", style="dotted", fill="none",
                  pad=24, title_size=26, sub="agent card first, then the task with the credential", sub_size=15,
                  w=C3) as p:
        s = Seq(cv, p.ix, p.iy + 6, [("Calling agent", "green", "agent"), ("Entra or OAuth provider", "red",
                                                                           "app-registrations"),
                                     ("Target A2A agent", "orange", "a2a")], spacing=456, head_w=200, head_h=84)
        s.msg(0, 2, "GET the agent card - anonymous by default", num=1)
        s.msg(2, 0, "agent card; protocol version negotiated (1.0 or 0.3)", dash="dashed")
        s.msg(0, 1, "get a credential: agent identity (app-only), UserEntraToken or AgentOnBehalfOfUser (delegated), "
                    "or an OAuth session", num=2)
        s.msg(1, 0, "token for the connection's audience (Foundry target: https://ai.azure.com)", dash="dashed")
        s.msg(0, 2, "send the task with the credential", num=3)
        s.selfmsg(2, "checks access: Foundry Agent Consumer on the target", num=4)
        s.msg(2, 0, "text response (no streaming)", dash="dashed")
        s.end()
    return p.bottom


def stack(cv, x, y, builders, gap=60):
    for fn in builders:
        y = fn(cv, x, y) + gap
    return y - gap


def band_deep(cv, y):
    _, b = section_header(cv, 0, y, "5.  Deep dives - delegation, scopes, consent, identity, OAuth, A2A and toolbox",
                          sub="The details behind the sequences: who may act, which scopes exist, how consent is "
                              "granted, and what the constraints are", size=34)
    y0 = b + 34
    x1, x2 = C3 + G3, 2 * (C3 + G3)
    r1 = max(stack(cv, 0, y0, [deep_actor, deep_endpoint, deep_iq]),
             stack(cv, x1, y0, [deep_scopes, deep_migration]),
             deep_consent(cv, x2, y0))
    y1 = r1 + 70
    r2 = max(stack(cv, 0, y1, [deep_identity, deep_toolbox]),
             stack(cv, x1, y1, [deep_oauth, deep_server]),
             deep_a2a(cv, x2, y1))
    return r2 + 80


# ====================================================================== section 6: which auth for which scenario
def decision_tree(cv, x, y):
    DW, DH, LW, LH = 330, 150, 250, 90
    xl, xr = x + 340, x + 870                       # left / right diamond columns
    root = Box(DW, "Must the tool know WHICH USER is calling?", h=DH, theme="gray", shape="diamond", size=16).place(
        cv, x + 605, y)

    def dia(cx_left, row, text):
        return Box(DW, text, h=DH, theme="gray", shape="diamond", size=16).place(cv, cx_left, y + 210 + row * 210)

    def leaf(lx, ly, label, sub, theme, w=LW, badge=None):
        b = Box(w, label, sub=sub, theme=theme, h=LH, size=17, sub_size=13, fill="solid").place(cv, lx, ly)
        if badge:
            draw_badge(cv, lx + w - 78, ly - 12, badge, size=13)
        return b

    q2 = dia(xl, 0, "Is the tool public, with no secrets?")
    q3 = dia(xl, 1, "Does it accept Microsoft Entra tokens?")
    q4 = dia(xl, 2, "Need per-agent audit and least privilege?")
    q5 = dia(xr, 0, "Third-party OAuth provider (GitHub, Vercel, Neon...)?")
    q6 = dia(xr, 1, "Microsoft-owned tool on the delegated list?")
    ly = lambda row: y + 210 + row * 210 + (DH - LH) / 2
    l_none = leaf(x, ly(0), "none", "public servers", "gray")
    l_key = leaf(x, ly(1), "custom-keys", "shared secrets only", "orange")
    l_agent = leaf(x, ly(2), "agentic-identity", "per-agent audit", "red")
    l_pmi = leaf(xl, y + 210 + 2 * 210 + DH + 56, "project-managed-identity", "shared by every agent in the project",
                 "red", w=DW)
    l_oauth = leaf(x + 1290, ly(0), "oauth2", "managed if one of the 10, else custom", "orange")
    l_uet = leaf(x + 1290, ly(1), "UserEntraToken", "Foundry or agent actor", "red")
    l_aobo = leaf(xr, y + 210 + 1 * 210 + DH + 56, "AgentOnBehalfOfUser", "your own Entra-protected MCP server", "red",
                  w=DW, badge="preview")
    connect(cv, root, q2, a_side="left", b_side="top", route="elbow", label="No", label_t=0.2, sw=3)
    connect(cv, root, q5, a_side="right", b_side="top", route="elbow", label="Yes", label_t=0.2, sw=3)
    connect(cv, q2, l_none, a_side="left", b_side="right", label="Yes", sw=3)
    connect(cv, q2, q3, a_side="bottom", b_side="top", label="No", sw=3)
    connect(cv, q3, l_key, a_side="left", b_side="right", label="No", sw=3)
    connect(cv, q3, q4, a_side="bottom", b_side="top", label="Yes", sw=3)
    connect(cv, q4, l_agent, a_side="left", b_side="right", label="Yes", sw=3)
    connect(cv, q4, l_pmi, a_side="bottom", b_side="top", label="No", sw=3)
    connect(cv, q5, l_oauth, a_side="right", b_side="left", label="Yes", sw=3)
    connect(cv, q5, q6, a_side="bottom", b_side="top", label="No", sw=3)
    connect(cv, q6, l_uet, a_side="right", b_side="left", label="Yes", sw=3)
    connect(cv, q6, l_aobo, a_side="bottom", b_side="top", label="No", sw=3)
    cv.text(x, y + 28, "No: shared identity,\nuser context is lost", size=17, color="#495057")
    cv.text(x + 1290, y + 28, "Yes: per-user identity,\nuser context persists", size=17, color="#c92a2a")
    nt(cv, xr - 30, y + 210 + 1 * 210 + DH + 56 + LH + 34, 690,
       "Work IQ MCP and Azure Databricks Genie MCP accept AgentOnBehalfOfUser only. Every per-user mode needs the "
       "user in the project's tenant and Foundry Agent Consumer (or more) for callers.", kind="info",
       title="Check support before you choose", src=S("cfg-delegation"))
    return l_pmi.bottom


def band_decide(cv, y):
    _, b = section_header(cv, 0, y, "6.  Which auth for which scenario",
                          sub="A quick chooser on the right, the full decision table on the left", size=34)
    y0 = b + 34
    G, O, R = "gray", "orange", "red"
    t = Table([("Scenario", 700), ("Use", 430), ("Why and watch-outs", 870)], [
        ["Public MCP or OpenAPI endpoint, no secrets", ("none", G),
         "OpenAPI still needs a connection; check rate limits and terms"],
        ["One shared SaaS API key or PAT", ("custom-keys", O),
         "Anyone with project access can read it: rotate, least privilege, shared secrets only"],
        ["Azure-hosted tool (Functions, APIM, Storage, AI Search) shared by every agent in the project",
         ("project-managed-identity", R),
         "Grant RBAC to the project MI and set the audience; private-network friendly; AI Search over a private VNet "
         "requires it"],
        ["The same, but with per-agent audit and least privilege", ("agentic-identity", R),
         "Grant RBAC to the agent identity's object ID; user tokens are rejected"],
        ["Per-user access to third-party SaaS (GitHub, Vercel, Neon...)",
         ("oauth2: managed if the server is one of the 10, else custom", O),
         "Needs Foundry Agent Consumer and the same tenant; add offline_access; consent per user per tool"],
        ["Per-user access to Microsoft data: Fabric IQ, Dataverse, Azure DevOps, Foundry MCP, Work IQ M365 tools, "
         "Sentinel", ("UserEntraToken (Foundry or agent actor) or AgentOnBehalfOfUser (preview)", R),
         "Check the tool's support; Work IQ MCP and Databricks Genie are AgentOnBehalfOfUser only; one resource per "
         "connection"],
        ["Your own Entra-protected MCP server that needs user context",
         ("AgentOnBehalfOfUser (preview), not UserEntraToken", R),
         "Needs the AgentBlueprint endpoint scheme; blueprint declares permissions; plan the consent path"],
        ["Foundry agent calls another Foundry agent, no user context",
         ("agentic-identity, audience https://ai.azure.com", R),
         "The target needs incoming A2A enabled and Foundry Agent Consumer for the caller"],
        ["Foundry agent calls another Foundry agent and preserves the user",
         ("UserEntraToken (compat) or AgentOnBehalfOfUser (preview)", R), "Test per-user isolation"],
        ["Client talks directly to a toolbox (no Foundry agent)", ("Entra token for the toolbox + per-tool OAuth2", O),
         "No agent blueprint sign-in, no AgentOnBehalfOfUser; the client must surface -32006 and continue"],
        ["SharePoint or Fabric data agent as direct agent tools", ("user identity (on-behalf-of) only", R),
         "No service principal; same tenant; SharePoint needs a Microsoft 365 Copilot license"],
        ["Browser automation", ("project managed identity (recommended), API key or agent identity", R),
         "Playwright workspace RBAC"],
        ["Foundry IQ knowledge base", ("project MI connection + per-user x-ms-query-source-authorization", R),
         "Azure AI Search roles + ACL metadata"],
        ["Speech MCP, Language MCP, Translator",
         ("resource keys (Bearer KEY1 or KEY2 + X-Blob-Container-Url; Ocp-Apim-Subscription-Key) or Entra", O),
         "Keys are secrets; Translator takes a key, a token or Entra"],
        ["Coding agent managing Foundry (Foundry MCP Server, preview)",
         ("Entra user token (on-behalf-of), scope https://mcp.ai.azure.com", R),
         "Reader, Contributor or Owner per operation; Conditional Access application id "
         "fcdfa2de-b65b-4b54-9a1c-81c8a18282d9"],
    ], w=2000, theme="red", size=14, head_size=15, title="Decision table: scenario to authentication type",
        title_size=24)
    t.place(cv, 0, y0)
    cite(cv, 0, t.bottom + 8, "mcp-auth", "cfg-delegation", "foundry-mcp")
    bt = decision_tree(cv, 2060, y0 + 4)
    return max(t.bottom + 70, bt) + 80


# ====================================================================== section 7: gotchas, roles, checks
def band_gotchas(cv, y):
    _, b = section_header(cv, 0, y, "7.  Gotchas, roles and checks",
                          sub="What goes wrong in practice, who needs which role, and how to verify (status as of "
                              "2026-11-03)", size=34)
    y0 = b + 34
    notes = [
        ("gotcha", "Cannot pass Microsoft token to untrusted MCP endpoint",
         "With managed OAuth and Microsoft Entra, Agent Service blocks tokens scoped to a known Microsoft audience from "
         "going to custom or third-party MCP servers. Register your server with an audience you control and use custom "
         "OAuth with your own Entra app registration.", ("mcp-auth",)),
        ("warn", "Stored keys are readable by the project",
         "People who have access to the project can access an API key stored in a project connection. Store only "
         "shared secrets; for user-specific access use user delegation or OAuth passthrough.", ("mcp-auth",)),
        ("warn", "UserEntraToken's actor flips with the audience",
         "A Foundry-audience token makes Foundry the actor; a blueprint-audience token makes the agent identity the "
         "actor. Plan the migration and keep AzureRbac or Entra while any client or channel still uses the Foundry "
         "audience.", ("cfg-delegation",)),
        ("info", "Consent is not access",
         "Consent doesn't grant the user access to data the resource would otherwise deny. Declaring a permission "
         "doesn't grant it, inheritance doesn't create a grant, and removing a scope doesn't revoke one.",
         ("consent", "delegation")),
        ("tip", "A successful call proves nothing",
         "Test with a user who lacks access and confirm each user gets their own authorization flow. Record the "
         "response ID and tool call ID; never log bearer tokens, refresh tokens or consent links.",
         ("cfg-delegation",)),
        ("gotcha", "Same tenant only",
         "OAuth passthrough, SharePoint, the Fabric data agent and Work IQ need the user's Entra tenant to equal the "
         "project's tenant: cross-tenant token exchange isn't supported.", ("mcp-auth", "work-iq")),
        ("warn", "Connections are hard to change",
         "azd ai connection update can't change the auth type and custom OAuth connections can't be updated at all - "
         "recreate them. azd ai connection show --show-credentials reveals secrets. Role changes on the target can "
         "take up to 10 minutes to propagate.", ("mcp-tool", "a2a-auth")),
        ("preview", "Preview as of 2026-11-03",
         "AgentOnBehalfOfUser, the AgentBlueprint scheme, agent identity as actor, Work IQ, Fabric IQ, managed MCP "
         "connectors and the Foundry MCP Server are preview. GA vs preview isn't uniform across tools: check the "
         "tool's page.", ("delegation", "work-iq")),
        ("info", "Authentication is not approval",
         "require_approval (default always for the mcp tool) is enforced by the agent runtime; a toolbox endpoint "
         "doesn't block tools/call. Authentication proves who is calling; approval decides whether the call runs.",
         ("mcp-auth", "toolbox")),
    ]
    cols = [[], []]
    for i, nspec in enumerate(notes):
        cols[i % 2].append(nspec)
    bottoms = []
    for ci, items in enumerate(cols):
        yy = y0
        for kind, title, text, keys in items:
            n = nt(cv, ci * (C3 + G3), yy, C3, text, kind=kind, title=title, src=S(*keys))
            yy = n.bottom + 22
        bottoms.append(yy - 22)
    rx = 2 * (C3 + G3)
    roles = Table([("Role or rule", 255), ("Who", 300), ("What it unlocks", 605)], [
        [("Foundry User", "green"), "developers; the agent identity (prompt-agent toolbox scenario); users in OAuth "
                                    "flows per the toolbox page",
         "build and test agents and toolboxes; Work IQ lists it for the developer, the agent's runtime identity and "
         "any user identity in OAuth flows"],
        [("Foundry Project Manager", "green"), "whoever creates MCP, A2A or Work IQ connections",
         "create the project connection (A2A and Work IQ pages)"],
        [("Foundry Agent Consumer", "green"), "end users and service principals that only call agents",
         "least-privilege role for an AzureRbac endpoint and for OAuth passthrough (Foundry User also works but is "
         "meant for developers)"],
        [("Target-service RBAC", "red"), "the project MI or the agent identity",
         "role on the target resource; changes can take up to 10 minutes to propagate"],
        [("Entra Application Developer", "red"), "developers, when user consent is disabled",
         "consent on your own behalf for eligible permissions"],
        [("Entra Global Administrator (PIM)", "red"), "one tenant admin, just in time",
         "one-time Work IQ setup: provision the Work IQ service principal and grant admin consent for WorkIQAgent.Ask"],
        [("Same tenant", "red"), "the user's Entra tenant = the project's tenant",
         "no cross-tenant token exchange for OAuth passthrough, SharePoint, Fabric or Work IQ"],
    ], w=C3, theme="red", size=14, head_size=15, title="Roles and tenant rules", title_size=24)
    roles.place(cv, rx, y0)
    cite_y = cite(cv, rx, roles.bottom + 8, "rbac", "id-overview")
    dd = nt(cv, rx, cite_y + 14, C3,
            "Who can create a connection: the connections page lists Foundry User, Foundry Owner or Azure Contributor; "
            "the A2A and Work IQ pages name Foundry Project Manager. End-user role for OAuth flows: the MCP page says "
            "Foundry Agent Consumer; the toolbox page lists Foundry User. Scope separator: portal and spec use a "
            "single space; the MCP page's azd guidance says commas; an A2A azd sample shows a space.",
            kind="warn", title="Docs disagree", src=S("connections", "a2a-tool", "mcp-tool"))
    return max(max(bottoms), dd.bottom) + 80
