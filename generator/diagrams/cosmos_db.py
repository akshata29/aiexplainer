"""Azure Cosmos DB in the Foundry ecosystem: the standard agent setup's enterprise_memory store, RBAC, private networking,
disaster recovery, Cosmos DB as agent memory / vector store / semantic cache, the Cosmos MCP Toolkit and Fabric mirroring."""
from __future__ import annotations

import math

from generator.xd import *
from generator.xd import metrics
from generator.xd.blocks import SAFETY
from generator.xd.palette import Theme, theme as get_theme

META = dict(
    id="cosmos-db", title="Azure Cosmos DB in the Foundry ecosystem", section="7", order=2,
    description="The standard agent setup's enterprise_memory database and containers, RBAC, private networking, what Foundry does not back up, plus Cosmos DB as agent memory, vector store, semantic cache, MCP tool and Fabric mirror source.",
    tags=["cosmos-db", "agent-state", "enterprise-memory", "vector-search", "mcp", "disaster-recovery"],
)

W = 3300                      # canvas content width
GAP = 48
C4 = (W - 3 * GAP) // 4       # one of four columns (789)
C3 = (W - 2 * GAP) // 3       # one of three columns (1068)
C2 = (W - GAP) // 2           # one of two columns (1626)
ASOF = "as of 2026-11-03"
CLASSIC = Theme("classic", "#495057", "#ced4da", "#e9ecef", "#343a40")   # slightly darker gray so hatching is visible


def CD(path: str) -> str:
    """Azure Cosmos DB Learn page."""
    return learn("azure/cosmos-db/" + path, base="")


# ---------------------------------------------------------------------------------------------- local helpers
class Cyl(Rect2):
    """Database cylinder: name, one-line role and a capacity chip. Dashed outline = created lazily."""

    def __init__(self, w, name, sub, *, theme="cyan", ru="1,000 RU/s", dash="solid", size=16, sub_size=14, ry=22):
        self.th = get_theme(theme)
        self.w, self.dash, self.ru, self.ry = w, dash, ru, ry
        self.size, self.sub_size = size, sub_size
        inner = (w - 28) * SAFETY
        self.name_lines = metrics.wrap_text(name, inner, size)
        self.sub_lines = metrics.wrap_text(sub, inner, sub_size)
        lr = metrics.line_ratio()
        self.ru_w = metrics.line_width(ru, 14) + 22
        self.text_h = len(self.name_lines) * size * lr + 4 + len(self.sub_lines) * sub_size * lr
        self.h = 3 * ry + 50 + self.text_h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, ry, w = self.th, self.ry, self.w
        n = 16
        pts = [(x, y + ry), (x, y + H - ry)]
        for i in range(1, n):
            t = math.pi - math.pi * i / n
            pts.append((x + w / 2 + w / 2 * math.cos(t), y + H - ry + ry * math.sin(t)))
        pts += [(x + w, y + H - ry), (x + w, y + ry)]
        for i in range(1, n):
            t = math.pi * i / n
            pts.append((x + w / 2 + w / 2 * math.cos(t), y + ry - ry * math.sin(t)))
        pts.append((x, y + ry))
        lr = metrics.line_ratio()
        with cv.group():
            cv.poly(pts, kind="line", stroke=th.stroke, sw=2, fill=th.fill, fill_style="hachure", dash=self.dash)
            cv.ellipse(x, y, w, 2 * ry, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash=self.dash)
            ty = y + 2 * ry + 6
            cv.text(x, ty, "\n".join(self.name_lines), size=self.size, color=th.deep, align="center", w=w)
            ty += len(self.name_lines) * self.size * lr + 4
            cv.text(x, ty, "\n".join(self.sub_lines), size=self.sub_size, color=MUTED, align="center", w=w)
            yc = get_theme("yellow")
            cy = y + H - ry - 30
            cv.rect(x + (w - self.ru_w) / 2, cy, self.ru_w, 25, stroke=yc.stroke, fill=yc.fill, style="solid", sw=1.5,
                    rough=0)
            cv.text(x + (w - self.ru_w) / 2 + 11, cy + 3, self.ru, size=14, color=yc.deep)
        cv.register(f"cyl:{self.name_lines[0]}", x, y, w, H)
        return self


class CodeCard(Rect2):
    """Card with a monospace code/JSON sketch in a white window."""

    def __init__(self, title, lines, *, theme="teal", note=None, src=(), size=14, pad=16, w=None):
        self.th = get_theme(theme)
        self.title, self.lines, self.src, self.size, self.pad = title, lines, list(src), size, pad
        txt = "\n".join(lines)
        tw, th_ = metrics.text_size(txt, size, metrics.MONO)
        self.code_w = tw + 2 * 12
        self.w = w or (self.code_w + 2 * pad)
        self.code_h = th_ + 2 * 10
        lr = metrics.line_ratio()
        self.title_lines = metrics.wrap_text(title, (self.w - 2 * pad) * SAFETY, 20)
        self.note_lines = metrics.wrap_text(note, (self.w - 2 * pad) * SAFETY, 14) if note else []
        h = pad + len(self.title_lines) * 20 * lr + 8 + self.code_h
        if self.note_lines:
            h += 8 + len(self.note_lines) * 14 * lr
        self.src_y = h + 8
        h += 8 + len(self.src) * 12 * lr + pad
        self.h = h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad, lr = self.th, self.pad, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            ty = y + pad
            cv.text(x + pad, ty, "\n".join(self.title_lines), size=20, color=th.deep)
            ty += len(self.title_lines) * 20 * lr + 8
            cv.rect(x + pad, ty, self.w - 2 * pad, self.code_h, stroke=th.stroke, fill="#ffffff", style="solid", sw=1.5,
                    rough=0)
            cv.text(x + pad + 12, ty + 10, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            ty += self.code_h
            if self.note_lines:
                cv.text(x + pad, ty + 8, "\n".join(self.note_lines), size=14, color=MUTED)
                ty += 8 + len(self.note_lines) * 14 * lr
            sy = ty + 8
            for label, url in self.src:
                cv.text(x + pad, sy, f"Learn: {label}", size=12, color=LINK, link=url)
                sy += 12 * lr
        cv.register(f"code:{self.title}", x, y, self.w, H)
        return self


def band(cv, y, tag, title, sub=None, theme="cyan"):
    """Numbered / lettered section header spanning the canvas; returns the y below it."""
    numbered(cv, 24, y + 27, tag, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 66, y, title, sub=sub, size=34, w=W - 66, sub_size=17)
    return bottom + 26


def steps(cv, x, y, w, items, theme="cyan", size=17, detail_size=15):
    """Vertical numbered steps joined by a dotted line; returns the bottom y."""
    th = get_theme(theme)
    lr = metrics.line_ratio()
    tx, tw = x + 46, (w - 46) * SAFETY
    cy = y
    for i, (title, detail) in enumerate(items, 1):
        tl = metrics.wrap_text(title, tw, size)
        dl = metrics.wrap_text(detail, tw, detail_size) if detail else []
        h = max(len(tl) * size * lr + (len(dl) * detail_size * lr + 2 if dl else 0), 32)
        numbered(cv, x + 17, cy + 17, i, theme=theme, d=32, size=18)
        cv.text(tx, cy, "\n".join(tl), size=size, color=th.deep)
        if dl:
            cv.text(tx, cy + len(tl) * size * lr + 2, "\n".join(dl), size=detail_size, color=INK)
        nxt = cy + h + 16
        if i < len(items):
            cv.line((x + 17, cy + 34), (x + 17, nxt + 1), stroke=th.stroke, sw=2, dash="dotted")
        cy = nxt
    return cy - 16


def cite(cv, x, y, items, size=12):
    """Clickable 'Learn:' lines; returns the bottom y."""
    cy = y
    for label, url in items:
        t = cv.text(x, cy, f"Learn: {label}", size=size, color=LINK, link=url)
        cy = t.bottom + 2
    return cy


# ---------------------------------------------------------------------------------------------- band 0: summary
def band_summary(cv, y):
    cards = [
        Card(C4, "Three roles for Cosmos DB around Foundry", [
            "A. Platform state: the standard agent setup keeps conversations and agent state in YOUR Cosmos DB for NoSQL account",
            "B. Your agent's memory: documents per turn, vector + full-text + hybrid search, semantic cache in your own app",
            "C. Tools and analytics: Cosmos MCP Toolkit as a custom tool, Fabric mirroring, an AI Search indexer",
        ], theme="cyan", icon="cosmos", src=[("AI agents and Azure Cosmos DB", CD("ai-agents"))]),
        Card(C4, "What the platform creates (standard setup)", [
            "Database enterprise_memory with 3 to 5 containers, 1,000 RU/s each (3 classic + 2 Responses API)",
            "The account needs at least 3,000 RU/s; too little makes project provisioning fail",
            "Classic and Responses-API runtimes use different containers; the 2 new ones appear on first agent use",
        ], theme="green", icon="agent", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
                                              ("Use your own resources", learn("agents/how-to/use-your-own-resources"))]),
        Card(C4, "Roles and network it needs", [
            "Project managed identity: Cosmos DB Operator on the account (Azure RBAC)",
            "Same identity: Cosmos DB Built-in Data Contributor on the enterprise_memory database (Cosmos data-plane RBAC)",
            "Private endpoint sub-resource Sql + privatelink.documents.azure.com; the portal flow does not create it",
        ], theme="red", icon="managed-identity", src=[("Cosmos DB data-plane RBAC", CD("how-to-connect-role-based-access-control"))]),
        Card(C4, "Foundry gives you no backup or DR here", [
            "No backups, point-in-time restore, cross-region replication or failover from the service",
            "You enable PITR, multi-region + service-managed failover, zone redundancy and delete locks",
            "Deleted threads are unrecoverable; a rebuilt project gets new agent IDs",
        ], theme="grape", icon="recovery-vault", src=[("Agent Service disaster recovery", learn("how-to/agent-service-disaster-recovery"))]),
    ]
    _, bottom = row(cv, 0, y, cards, gap=GAP)
    return bottom


# ---------------------------------------------------------------------------------------------- lane A
def hero(cv, y0):
    """Foundry project + network path on the left, the Cosmos DB account with its containers on the right."""
    b_agent = Box(436, "Agent Service runtime", sub="classic threads + Responses API (new runtime)", theme="green",
                  icon="agent", icon_pos="left", fill="solid")
    b_cap = Box(436, "Capability settings", sub="documentStore = resource ID of your Cosmos DB account (legacy: AzureCosmosDb connection + capability host)",
                theme="cyan", icon="gear", icon_pos="left", fill="solid")
    b_mi = Box(436, "Project managed identity", sub="system- or user-assigned; holds the Cosmos roles", theme="red",
               icon="managed-identity", icon_pos="left", fill="solid")
    b_sub = Box(350, "Agent subnet", sub="delegated to Microsoft.App/environments (/24 recommended, /27 minimum)",
                theme="indigo", icon="subnet", icon_pos="left", fill="solid")
    b_pe = Box(350, "Private endpoint", sub="sub-resource Sql; DNS zone privatelink.documents.azure.com", theme="indigo",
               icon="private-endpoint", icon_pos="left", fill="solid")
    H1 = max(b_agent.h, b_sub.h, b_pe.h)

    with cv.panel(0, y0, title="Foundry project", sub="Microsoft-managed Agent Service runtime", theme="green",
                  style="dashed", fill="soft", pad=22, title_size=26, sub_size=15) as p1:
        b_agent.place(cv, p1.ix, p1.iy, h=H1)
        b_cap.place(cv, p1.ix, b_agent.bottom + 30)
        b_mi.place(cv, p1.ix, b_cap.bottom + 30)
    with cv.panel(p1.right + 100, y0, title="Network-secured setup (optional)", sub="private endpoints are NOT auto-created in the portal flow",
                  theme="indigo", style="dashed", fill="soft", pad=22, title_size=26, sub_size=15) as p2:
        b_sub.place(cv, p2.ix, p2.iy, h=H1)
        b_pe.place(cv, b_sub.right + 90, p2.iy, h=H1)

    cos_x = p2.right + 110
    avail = (W - cos_x) - 2 * 26 - 2 * 22
    cw = int((avail - 170) / 5)
    cos_ref = {}
    with cv.panel(cos_x, y0, title="Azure Cosmos DB for NoSQL account (yours)",
                  sub="provisioned or serverless documented as supported | total throughput >= 3,000 RU/s | one dedicated account per workload recommended",
                  theme="cyan", style="solid", fill="soft", pad=26, title_size=30, sub_size=15, w=W - cos_x) as cos:
        with cv.panel(cos.ix, cos.iy, title="Database: enterprise_memory",
                      sub="created by the platform | direct manipulation of it is unsupported (DR docs)", theme="cyan",
                      style="dotted", fill="none", pad=22, title_size=26, sub_size=15) as db:
            with cv.panel(db.ix, db.iy, title="Classic runtime", sub="Foundry Agent Service (Classic): created at provisioning",
                          theme="gray", style="dashed", fill="soft", pad=20, title_size=22, sub_size=14) as g1:
                cyls = [
                    Cyl(cw, "thread-message-store", "end-user conversations", theme=CLASSIC),
                    Cyl(cw, "system-thread-message-store", "internal system messages", theme=CLASSIC),
                    Cyl(cw, "agent-entity-store", "agent metadata or model inputs/outputs (docs disagree)", theme=CLASSIC),
                ]
                HC = max(c.h for c in cyls)
                row(cv, g1.ix, g1.iy, [c for c in cyls], gap=20)
            with cv.panel(g1.right + 30, db.iy, title="New runtime (Responses API)",
                          sub="Foundry Agent Service (New): created dynamically on first agent use", theme="green", style="dashed",
                          fill="soft", pad=20, title_size=22, sub_size=14) as g2:
                cyls2 = [
                    Cyl(cw, "agent-definitions-v1", "agent definitions and configuration", theme="green", dash="dashed"),
                    Cyl(cw, "run-state-v1", "execution state of agent runs", theme="green", dash="dashed"),
                ]
                row(cv, g2.ix, g2.iy, cyls2, gap=20)
            n3 = Note(g2.right - g1.x, "Docs disagree on how many containers exist. standard-agent-setup: the standard setup provisions FIVE (and elsewhere says three are provisioned for project isolation). use-your-own-resources and the Cosmos DB page: THREE TO FIVE - three at provisioning, up to two more created dynamically when you create Responses-API agents. Plan RU/s for five.",
                      kind="warn", title="3 vs 5 containers", size=15)
            n3.place(cv, g1.x, max(g1.bottom, g2.bottom) + 22)
        t_cont = Table(
            [("Container", 330), ("standard-agent-setup page says", 700), "Cosmos DB page (azure-agent-service) says"],
            [
                ["thread-message-store", "End-user conversations", "Stores end-user conversation messages"],
                ["system-thread-message-store", "Internal system messages", "Manages internal system messages"],
                ["agent-entity-store", ("Agent metadata (instructions, tools, name)", "yellow"), ("Captures and stores model inputs and outputs", "yellow")],
                ["agent-definitions-v1", "Agent metadata (instructions, tools, name, versions)", "Stores agent definitions and configuration"],
                ["run-state-v1", ("Internal messages and end-user conversations", "yellow"), ("Tracks the execution state of agent runs", "yellow")],
            ], w=W - cos_x - 52, theme="cyan", size=14, head_size=15, first_col_theme="cyan",
            title="What each container holds - as documented (yellow = the two pages differ)", title_size=20)
        t_cont.place(cv, cos.ix, db.bottom + 28)
        cite(cv, cos.ix, t_cont.bottom + 6, [("Cosmos DB: integration with Agent Service", CD("gen-ai/azure-agent-service")),
                                              ("Set up standard agent resources", learn("agents/concepts/standard-agent-setup"))])
    place_icon(cv, "cosmos", cos.right - 26 - 52, y0 + 18, 52)

    # arrows: runtime path and setup relationships
    connect(cv, b_agent, b_sub, a_side="right", b_side="left", label="threads + state", label_wrap=100, label_size=13)
    connect(cv, b_sub, b_pe, a_side="right", b_side="left")
    arrow(cv, [(b_pe.right + 6, b_pe.cy), (cos.x - 6, b_pe.cy)], label="Sql", label_size=14, color="#3b5bdb")
    for blk, color, lab in ((b_cap, "#0c8599", "documentStore -> account resource ID"),
                            (b_mi, "#e03131", "Cosmos DB Operator (account) + Built-in Data Contributor (database)")):
        arrow(cv, [(blk.right + 6, blk.cy), (cos.x - 6, blk.cy)], dash="dashed", color=color, label=lab, label_size=14,
              label_dx=-30)

    # left-bottom: provisioning flow
    yl = max(p1.bottom, p2.bottom) + 44
    with cv.panel(0, yl, title="Provision and run", sub="manual provisioning: allow roughly 30-45 minutes (standard-agent-setup)",
                  theme="cyan", style="dotted", fill="none", pad=22, title_size=24, sub_size=15, w=p2.right) as pf:
        sb = steps(cv, pf.ix, pf.iy, p2.right - 44, [
            ("Pick or create the Cosmos DB for NoSQL account", "dedicated per workload, unique name; add continuous backup + multi-region if you need DR"),
            ("Leave RU/s headroom", "account total >= 3,000 RU/s; plan 5,000 per project once the Responses-API containers appear"),
            ("Create the Foundry account and project with capability settings", "documentStore = Cosmos resource ID (legacy: AzureCosmosDb connection + capability host)"),
            ("Grant the project identity its Cosmos roles", "Cosmos DB Operator on the account + Built-in Data Contributor on enterprise_memory"),
            ("The platform creates enterprise_memory", "3 classic containers now; the first Responses-API agent adds agent-definitions-v1 and run-state-v1"),
            ("Runtime", "Agent Service reads and writes conversations and state through the agent subnet and private endpoint (arrows above)"),
        ], theme="cyan")
    return max(cos.bottom, pf.bottom)


def lane_a(cv, y):
    y = band(cv, y, "A1", "Platform state: Foundry Agent Service runs on YOUR Cosmos DB account",
             sub="Basic setup = Microsoft-managed storage (portal fields left empty). Standard setup = bring your own Cosmos DB for NoSQL (threads), Storage (files) and AI Search (vectors)",
             theme="cyan")
    cv.text(0, y + 8, "Standard setup = three BYO resources:", size=19, color=INK)
    cite(cv, 0, y + 40, [("Set up standard agent resources", learn("agents/concepts/standard-agent-setup"))])
    cf3 = ChipFlow([
        Chip("Azure Cosmos DB for NoSQL: BYO thread storage - messages, conversation history, agent metadata", theme="cyan", icon="cosmos", size=16),
        Chip("Azure Storage: BYO file storage - files from developers and end users", theme="cyan", icon="storage", size=16),
        Chip("Azure AI Search: BYO search - vector stores the agent creates", theme="teal", icon="ai-search", size=16),
    ], W - 420, gap=14)
    cf3.place(cv, 420, y)
    y = y + max(cf3.h, 60) + 34
    y = hero(cv, y) + 54

    # ---- row A2: RBAC | RU calculator | networking
    t_rbac = Table(
        [("Identity", 330), ("Role", 520), ("Scope", 400), "Kind"],
        [
            [("Project managed identity (system- or user-assigned)", "red"), "Cosmos DB Operator", "the Cosmos DB account", "Azure RBAC (control plane)"],
            [("Project managed identity", "red"), "Cosmos DB Built-in Data Contributor (role definition 00000000-0000-0000-0000-000000000002)", "database enterprise_memory (not per container)", "Cosmos native data-plane RBAC"],
            [("Identity that runs the capability-settings deployment", "red"), "Cosmos DB Operator + Storage Blob Data Contributor (Azure AI Search: no caller role)", "Cosmos account + Storage account", "Azure RBAC (API 2026-07-15-preview)"],
            [("Developers who create or edit agents", "red"), "Foundry User", "the Foundry project", "Azure RBAC (Foundry)"],
        ], w=C2, theme="red", size=14, head_size=15, title="Required RBAC for the Cosmos DB account", title_size=22)
    t_rbac.place(cv, 0, y)
    nw = (C2 - 24) // 2
    n_dp = Note(nw, "Cosmos DB data-plane roles are NOT Azure RBAC assignments. They live inside the Cosmos account, creating them needs control-plane permission, and the scope can be account (/), database or container. Managed identities and agent identities need the data-plane role.",
                kind="gotcha", title="Two different RBAC systems", size=14,
                src=[("Cosmos DB data-plane RBAC", CD("how-to-connect-role-based-access-control"))])
    n_comp = Note(nw, "Companion roles on the other BYO resources: Storage Account Contributor (account); Storage Blob Data Contributor on <workspaceId>-azureml-blobstore; Storage Blob Data Owner on <workspaceId>-azureml-agent (the BYO-storage page calls it <workspaceId>-agents-blobstore - docs disagree); Search Index Data Contributor + Search Service Contributor.",
                  kind="info", title="Roles on Storage and AI Search", size=14,
                  src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))])
    hn = max(n_dp.h, n_comp.h)
    n_dp.place(cv, 0, t_rbac.bottom + 22, h=hn)
    n_comp.place(cv, nw + 24, t_rbac.bottom + 22, h=hn)

    t_ru = Table(
        [("Scenario", 330), ("Containers", 150), "Min RU/s"],
        [
            ["One project, classic runtime only", "3", "3,000 (account minimum)"],
            ["One project + Responses-API runtime", "5", "5,000"],
            ["Two projects, classic only", "6", "6,000"],
            ["Two projects, Responses API", "10", "10,000"],
        ], w=C4, theme="yellow", size=14, head_size=15, title="RU/s calculator (1,000 per container)", title_size=22)
    t_ru.place(cv, C2 + GAP, y)
    n_ru = Note(C4, "Illustrative arithmetic from 1,000 RU/s per container; containers are prefixed with the project ID. Responses-API containers appear lazily, so the RU/s must already exist. Insufficient RU/s makes project provisioning fail. Docs say provisioned or serverless works yet also require 1,000 RU/s per container - check how serverless behaves for you.",
                kind="gotcha", title="Capacity before first use", size=14,
                src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
    n_ru.place(cv, C2 + GAP, t_ru.bottom + 22)

    c_net = Card(C4, "Private networking for Cosmos DB", [
        "Private endpoint to sub-resource Sql; DNS zone privatelink.documents.azure.com",
        "Other zones: privatelink.cognitiveservices.azure.com, privatelink.openai.azure.com, privatelink.services.ai.azure.com, privatelink.search.windows.net, privatelink.blob.core.windows.net",
        "Azure DNS resolver 168.63.129.16",
        "Create the Search, Storage and Cosmos private endpoints yourself - the portal flow does not",
        "Agent subnet: RFC1918 + restricted CGNAT 100.64.0.0/10, dedicated per Foundry resource; Foundry in the VNet's region",
        "Hosted-agent VNet injection must be set at account creation",
        "Timeout of 60000ms errors: check Cosmos connectivity (private endpoint, DNS)",
    ], theme="indigo", icon="private-link", src=[("Configure private link", learn("how-to/configure-private-link")),
                                                 ("Agent Service virtual networks", learn("agents/how-to/virtual-networks"))])
    c_net.place(cv, 2 * (C4 + GAP) + C4 + GAP, y)
    yA2 = max(n_comp.bottom, n_ru.bottom, c_net.bottom) + 54

    # ---- row A3: capability settings vs host | gotchas | templates
    t_cap = Table(
        [("Aspect", 190), ("Capability settings (new)", 720), "Capability host (legacy)"],
        [
            ["API", "ARM CapabilitySettings on Microsoft.CognitiveServices accounts and projects; API 2026-07-15-preview / 2026-09-15-preview", "API 2025-06-01, capabilityHostKind: Agents"],
            ["Properties", "blobStore (Storage), documentStore (Cosmos DB - agent runtime state), vectorStore (AI Search)", "storageConnections (Storage), threadStorageConnections (Cosmos DB), vectorStoreConnections (Search), optional aiServicesConnections"],
            ["Scope", "Account-level defaults inherited by projects at create time only; not updatable on an existing project (delete and recreate)", "One per scope; no update (delete and recreate); no account-to-project inheritance"],
            ["Inputs", "Resource IDs", "Connections with authType, category (AzureStorageAccount / AzureCosmosDb / CognitiveSearch), target and metadata.ResourceId; one non-empty value per property"],
            ["Network", "scenario: agent or none, subnetArmId, useMicrosoftManagedNetwork", "Via account properties and templates"],
        ], w=C2, theme="cyan", size=14, head_size=15, first_col_theme="cyan",
        title="How you wire it: capability settings (new) vs capability host (legacy) - as of 2026-11-03", title_size=22)
    t_cap.place(cv, 0, yA2)
    cite(cv, 0, t_cap.bottom + 6, [("Capability hosts", learn("agents/concepts/capability-hosts")),
                                    ("Environment setup (capability settings)", learn("agents/environment-setup"))])
    g1 = Note(C4, "Foundry connection type 'Azure Cosmos DB' is Preview and can only be created in code (no portal). It is required for the standard agent setup. The page how-to/configure-capability-settings currently redirects to agents/environment-setup, and the capability-settings ARM API versions are preview.",
              kind="preview", title="Preview + code-only", size=14,
              src=[("Add connections", learn("how-to/connections-add"))])
    g1.place(cv, C2 + GAP, yA2)
    g2 = Note(C4, "Tool calls that leave Foundry through your VNet need a PROJECT-level capability host; an account-level one alone fails with 'name or host unknown'. A single-tenant data proxy fronts tool calls (guidance: about 250 low-traffic or 25 heavy projects per setup); firewall allow-list entries are needed for egress control.",
              kind="gotcha", title="Capability host scope", size=14,
              src=[("Toolbox network isolation", learn("agents/how-to/tools/toolbox-network-isolation"))])
    g2.place(cv, C2 + GAP, g1.bottom + 20)
    c_tpl = Card(C4, "Templates and providers", [
        "Bicep: 15-private-network-standard-agent-setup; Terraform: 15a / 15b; 19-private-network-agent-tools for private tools (microsoft-foundry/foundry-samples)",
        "Providers named by use-your-own-resources: KeyVault, CognitiveServices, Storage, MachineLearningServices, Search, App, ContainerService (+ Bing for Grounding)",
        "The network tutorial also names DocumentDB and BotService - verify the list on the page you follow",
        "Role assignments need Role Based Access Administrator or Owner",
    ], theme="gray", icon="template-specs", src=[("Use your own resources", learn("agents/how-to/use-your-own-resources"))])
    c_tpl.place(cv, 3 * (C4 + GAP), yA2)
    return max(g2.bottom, c_tpl.bottom, t_cap.bottom + 40)


# ---------------------------------------------------------------------------------------------- disaster recovery
def dr_band(cv, y):
    y = band(cv, y, "A2", "Foundry gives you no backup or disaster recovery for this account - you own it",
             sub=f"Cosmos DB is a customer-owned resource, so every resilience control below is yours to switch on ({ASOF})", theme="grape")
    c_no = Card(C3, "What Foundry does NOT provide", [
        "! No built-in DR: no cross-region replication, backups or point-in-time restore by the service",
        "! No active-active multi-region and no automatic cross-region failover",
        "! Deleted threads are unrecoverable",
        "! Reconstructing a project yields NEW agent IDs",
        "! Direct manipulation of enterprise_memory is unsupported",
        "! Customer-owned resources (Cosmos DB, Storage, AI Search) need their own DR",
    ], theme="red", icon="recovery-vault", src=[("Agent Service disaster recovery", learn("how-to/agent-service-disaster-recovery")),
                                                 ("High availability and resiliency", learn("how-to/high-availability-resiliency"))])
    c_yes = Card(C3, "What you enable on the Cosmos DB account", [
        "+ Continuous backup (PITR): docs mention 7- and 30-day tiers; a 35-day figure also appears (docs disagree)",
        "+ Multi-region reads + service-managed failover",
        "+ Zone redundancy",
        "+ Delete locks: a Cosmos lock protects the account, databases and containers, not the data",
        "+ A dedicated Cosmos / Search / Storage set per workload; user-assigned managed identity preferred",
        "+ Optional: a Purview connection for eDiscovery",
    ], theme="green", icon="backup", src=[("Operator disaster recovery", learn("how-to/agent-service-operator-disaster-recovery")),
                                           ("Platform disaster recovery", learn("how-to/agent-service-platform-disaster-recovery"))])
    c_rs = Card(C3, "Restore and multi-region facts", [
        "PITR restores to a DIFFERENT account, or a database / container into the same account",
        "Role assignments are not restored - re-create them after a restore",
        "Use unique account names: a restore recreates the original name",
        "Foundry does not fail over across regions: for multi-region availability deploy separate Foundry resources and handle data synchronisation and routing in your application layer",
    ], theme="grape", icon="regions", src=[("Operator disaster recovery", learn("how-to/agent-service-operator-disaster-recovery")),
                                           ("High availability and resiliency", learn("how-to/high-availability-resiliency"))])
    HH = max(c_no.h, c_yes.h, c_rs.h)
    c_no.place(cv, 0, y, h=HH)
    c_yes.place(cv, C3 + GAP, y, h=HH)
    c_rs.place(cv, 2 * (C3 + GAP), y, h=HH)
    with cv.panel(0, y + HH + 40, title="Recovery after data loss", sub="summary of the operator DR page - Foundry gives you none of this for free", theme="grape",
                  style="dotted", fill="none", pad=26, title_size=26, sub_size=15, w=W) as pr:
        bw = 560
        gx = (W - 52 - 5 * bw) / 4
        items = [
            ("Before the incident", "PITR + multi-region + zone redundancy + locks are already on; roles and settings are written down", "backup", "grape"),
            ("Incident", "the account, a database or a container is lost or corrupted", "alerts", "red"),
            ("Restore", "PITR restores to a DIFFERENT account, or a database / container into the same account", "recovery-vault", "cyan"),
            ("Reconnect or rebuild the project", "a reconstructed project gets NEW agent IDs", "foundry", "green"),
            ("Re-assign roles and validate", "role assignments are not restored; data never backed up (for example deleted threads) is gone", "managed-identity", "red"),
        ]
        bxs = [Box(bw, lab, sub=sub, theme=th_, icon=ic, fill="solid", min_h=170) for lab, sub, ic, th_ in items]
        hb = max(b.h for b in bxs)
        for i, b in enumerate(bxs):
            b.place(cv, pr.ix + i * (bw + gx), pr.iy, h=hb)
            numbered(cv, b.x + 18, b.y + 18, i + 1, theme=items[i][3], d=30)
        for a, b in zip(bxs, bxs[1:]):
            connect(cv, a, b, a_side="right", b_side="left")
    return pr.bottom


# ---------------------------------------------------------------------------------------------- not cosmos
def not_cosmos(cv, y):
    y = band(cv, y, "A3", "What is NOT documented as Cosmos-backed", sub="Do not draw these three as Cosmos DB stores - Learn does not say so", theme="gray")
    cards = [
        Card(C4, "Hosted-agent durable state store", [
            "FoundryStateStore: key-value JSON items, up to 1 MB each, up to 16 tags",
            "30-day default idle expiry; per-user isolation via x-agent-foundry-call-id",
            "The backing store is not stated",
        ], theme="gray", dash="dashed", icon="storage", src=[("Agent state store", learn("agents/concepts/agent-state-store"))]),
        Card(C4, "Foundry Memory (preview)", [
            "Managed long-term memory: user profile, chat summary, procedural",
            "Limits: 100 scopes per store, 10,000 memories per scope, 1,000 requests/min; VNet not supported",
            "Needs Azure OpenAI chat + embedding deployments; the backing store is not stated",
        ], theme="gray", dash="dashed", icon="agent", badge="preview", src=[("What is memory?", learn("agents/concepts/what-is-memory"))]),
        Card(C4, "File search (basic mode)", [
            "Files and vectors live in Microsoft-managed storage and search",
            "Your Cosmos, Storage and AI Search accounts are used only in the standard setup",
        ], theme="gray", dash="dashed", icon="files", src=[("Standard agent setup", learn("agents/concepts/standard-agent-setup"))]),
    ]
    _, b = row(cv, 0, y, cards, gap=GAP)
    n = Note(C4, "The Agent Memory Toolkit in lane B is different: it is your code writing to your own Cosmos DB account. Foundry Memory is managed, preview, and its store is unstated.",
             kind="key", title="Contrast", size=15)
    n.place(cv, 3 * (C4 + GAP), y, h=b - y)
    return b


# ---------------------------------------------------------------------------------------------- lane B
def lane_b(cv, y):
    y = band(cv, y, "B", "Your agent app: Cosmos DB as memory, vector store, hybrid search and semantic cache",
             sub="None of this is created by Foundry - it is your own code against your own Cosmos DB account", theme="teal")
    why = Card(C4, "Why Cosmos DB for agent memory", [
        "Documented claims: speed, scale and simplicity in one database",
        "NoSQL API advertises 99.999% availability (multi-region) and single-digit-millisecond reads",
        "Serverless, provisioned or autoscale throughput; multitenancy patterns",
        "Vector, full-text and hybrid search in one query engine",
    ], theme="teal", icon="cosmos", src=[("AI agents and Azure Cosmos DB", CD("ai-agents")), ("Why Cosmos DB for AI", CD("gen-ai/why-cosmos-ai"))])
    mem = Card(C4, "Short-term vs long-term memory", [
        "Short-term: recent turns, state and tool results for the current thread; expire with TTL, summarise, or promote to long-term",
        "Long-term: facts, preferences and summaries kept across threads (for example 'User is vegetarian')",
        "Pair the container with a vector index, a full-text index (BM25), hybrid ranking and a semantic cache",
    ], theme="teal", icon="agent", src=[("Agent memory in Cosmos DB", CD("gen-ai/agentic-memories"))])
    t_pk = Table(
        [("Partition key", 300), ("Example values", 330), "Best for / trade-off"],
        [
            ["GUID per item (/pk)", "b9c5b6ce-2d9a-4a2b-...", "Write-heavy ephemeral turns, logging and analytics; no hot partitions. Queries span partitions and cost more"],
            ["/threadId", "thread-1234", "Turns and summaries co-located: latest N, phrase filters, vector search inside a thread. Needs enough threads to avoid hot partitions"],
            ["Hierarchical [/tenantId, /threadId]", "contoso + thread-1234", "Multitenant apps: locality per thread, grouping per tenant, fewer cross-partition scans, safer isolation"],
        ], w=C2, theme="teal", size=14, head_size=15, first_col_theme="teal", title="Partition key choices for memory containers", title_size=22)
    HH = max(why.h, mem.h)
    why.place(cv, 0, y, h=HH)
    mem.place(cv, C4 + GAP, y, h=HH)
    t_pk.place(cv, 2 * (C4 + GAP), y)
    cite(cv, 2 * (C4 + GAP), t_pk.bottom + 6, [("Agent memory in Cosmos DB", CD("gen-ai/agentic-memories"))])
    y2 = max(HH, t_pk.h + 24) + y + 54

    # row B2: document sketch | alternatives | vector index table
    doc = CodeCard("One document per turn (recommended)", [
        "{",
        '  "id": "tenant-001",',
        '  "threadId": "thread-1234",',
        '  "turnIndex": 7,',
        '  "messages": [',
        '    { "role": "user", "content": "...",',
        '      "timestamp": "...", "metadata": {...} },',
        '    { "role": "agent", "content": "..." }',
        "  ],",
        '  "embedding": [0.013, -0.092, ...],',
        '  "metrics": { "latencyMs": 300 }',
        "}",
    ], theme="teal", w=C4, note="Simplified from the documented example: one item per back-and-forth exchange, easy to vectorise, TTL and use as a semantic-cache entry.",
        src=[("Agent memory in Cosmos DB", CD("gen-ai/agentic-memories"))])
    alt = Card(C4, "Why that model, and the alternatives", [
        "# Why one document per turn",
        "Latest N turns by ordering on turnIndex or timestamp; one embedding per turn for in-thread vector search and semantic caching",
        "Easy to expire old turns with TTL; small items avoid costly updates",
        "You may add summary turns and prune or compact old turns",
        "# One response per item",
        "One item per utterance, same threadId: fine-grained retrieval and analytics; weaker for semantic caching",
        "# One thread per item",
        "Whole conversation in one array: a single read, but every append rewrites the item",
        "! Typically not recommended: long or unbounded threads cost high RU per write",
    ], theme="teal", src=[("Agent memory in Cosmos DB", CD("gen-ai/agentic-memories"))])
    h2 = max(doc.h, alt.h)
    doc.place(cv, 0, y2, h=h2)
    alt.place(cv, C4 + GAP, y2, h=h2)
    t_vec = Table(
        [("Vector index", 190), ("Max dims", 110), "Notes"],
        [
            ["flat", "505", "Exact (brute-force) search"],
            ["quantizedFlat", "4,096", "Compressed vectors; recommended up to about 50K vectors; needs at least 1,000 vectors, otherwise a full scan"],
            ["diskANN", "4,096", "Scalable approximate nearest neighbour; at least 1,000 vectors; optional sharding with vectorIndexShardKey (tenant, user or session)"],
        ], w=C2, theme="teal", size=14, head_size=15, first_col_theme="teal", title="Vector indexes in Cosmos DB for NoSQL", title_size=22)
    t_vec.place(cv, 2 * (C4 + GAP), y2)
    chips = ChipFlow([
        "float32 / float16 / int8 / uint8", "cosine / dotproduct / euclidean", "quantizerType: product / spherical",
        "enable: capability EnableNoSQLVectorSearch (about 15 min)", "TOP N in queries",
    ], C2, theme="teal", size=14, gap=8)
    chips.place(cv, 2 * (C4 + GAP), t_vec.bottom + 16)
    n_vec = Note(C2, "The vector policy and index are immutable, vector search cannot be disabled once enabled, and it is not supported on shared-throughput (database-level) accounts.",
                 kind="gotcha", title="Vector search constraints", size=15,
                 src=[("Vector search in Cosmos DB", CD("vector-search"))])
    n_vec.place(cv, 2 * (C4 + GAP), chips.y + chips.h + 14)
    y3 = max(doc.bottom, alt.bottom, n_vec.bottom) + 54

    # row B3: memory pattern flow
    with cv.panel(0, y3, title="Memory pattern in your own app", sub="turn -> document -> vector -> hybrid recall -> semantic cache", theme="teal",
                  style="dotted", fill="none", pad=26, title_size=26, sub_size=15, w=W) as pf:
        bw = 470
        gapx = (W - 52 - 6 * bw) / 5
        items = [
            ("Turn arrives", "user message, agent reply and any tool call", "agent", "green"),
            ("Upsert one document per turn", "partition key threadId or [tenantId, threadId]; TTL optional", "cosmos", "cyan"),
            ("Embed the text, store the vector", "embedding property in the container's vector policy", "openai", "blue"),
            ("Next turn: hybrid recall", "ORDER BY RANK RRF over vector + full-text, scoped to the partition", "cosmos", "teal"),
            ("Check the semantic cache", "reuse a stored answer when prompt + chat history are similar", "cosmos", "teal"),
            ("Call the LLM only on a miss", "write the answer and its embedding back to the cache", "gpt", "blue"),
        ]
        boxes = []
        bx = pf.ix
        for i, (lab, sub, ic, th_) in enumerate(items):
            b = Box(bw, lab, sub=sub, theme=th_, icon=ic, fill="solid", min_h=170)
            boxes.append(b)
        hh = max(b.h for b in boxes)
        for i, b in enumerate(boxes):
            b.place(cv, pf.ix + i * (bw + gapx), pf.iy, h=hh)
            numbered(cv, b.x + 18, b.y + 18, i + 1, theme=items[i][3], d=30)
        for a, b in zip(boxes, boxes[1:]):
            connect(cv, a, b, a_side="right", b_side="left")
    y4 = pf.bottom + 54

    # row B4: hybrid | semantic cache loop
    c_hyb = Card(C4, "Hybrid search: RRF", [
        "Reciprocal Rank Fusion combines vector similarity and full-text (BM25) rankings in one query",
        "ORDER BY RANK RRF(VectorDistance(...), FullTextScore(...))",
        "Optional weights array, for example [2, 1]",
        "Full-text indexes tokenise, stem and normalise case on paths such as /content",
    ], theme="teal", icon="cosmos", src=[("Hybrid search", CD("gen-ai/hybrid-search")), ("Agent memory", CD("gen-ai/agentic-memories"))])
    c_sc = Card(C4, "Semantic cache", [
        "Reuse a prior LLM answer when a new prompt is similar enough - saves latency, tokens and cost",
        "Embed the prompt, vector-search the cache container, answer from a hit, call the LLM on a miss and store the result",
        "! The cache key must include the conversation context (chat history), not just the last prompt text",
    ], theme="teal", icon="cosmos", src=[("Semantic cache", CD("gen-ai/semantic-cache"))])
    hh4 = max(c_hyb.h, c_sc.h)
    c_hyb.place(cv, 0, y4, h=hh4)
    c_sc.place(cv, C4 + GAP, y4, h=hh4)
    t_fw = Table(
        [("Framework", 260), ("Cosmos DB pieces (all connectors support key and Entra / managed identity auth)")],
        [
            [("Microsoft Agent Framework", "green"), "Python: CosmosDBWorkflowCheckpointStorage, CosmosDBHistoryProvider. .NET: CheckpointStore, ChatHistoryProvider (package Microsoft.Agents.AI.CosmosNoSql)"],
            [("LangGraph", "green"), "CosmosDBSaver / CosmosDBSaverSync (checkpointer), CosmosDBCache, CosmosDBStore (long-term memory)"],
            [("LangChain", "green"), "langchain-azure-cosmosdb: vector store, semantic cache, chat history"],
            [("Semantic Kernel", "green"), "Cosmos DB vector store connector"],
            [("LlamaIndex", "green"), "Vector, document, index, chat and key-value stores"],
            [("Spring AI", "green"), "Vector store"],
        ], w=C2, theme="teal", size=14, head_size=15, title="Framework integrations", title_size=22)
    t_fw.place(cv, 2 * (C4 + GAP), y4)
    cite(cv, 2 * (C4 + GAP), t_fw.bottom + 6, [("Cosmos DB gen-AI integrations", CD("gen-ai/integrations"))])
    y5 = max(hh4, t_fw.h + 24) + y4 + 54

    # row B5: Agent Memory Toolkit
    with cv.panel(0, y5, title="Agent Memory Toolkit for Azure Cosmos DB", sub="Python SDK - get it at aka.ms/agentmemorytoolkit | your code + your Cosmos account (Foundry Memory, by contrast, is managed) | preview as of 2026-11-03",
                  theme="teal", style="dashed", fill="none", pad=26, title_size=26, sub_size=15, w=W) as pt:
        bw = 660
        gx = (W - 52 - 4 * bw) / 3
        t1 = Box(bw, "Your agent app + toolkit", sub="Python SDK: add, upload, retrieve, search, summarise", theme="green",
                 icon="agent", icon_pos="left", fill="solid")
        t2 = Box(bw, "Cosmos DB container", sub="JSON documents of four memory types", theme="cyan", icon="cosmos", icon_pos="left", fill="solid")
        t3 = Box(bw, "Azure Durable Functions", sub="production mode: a sibling function app processes new turns in the background", theme="orange", icon="functions",
                 icon_pos="left", fill="solid")
        t4 = Box(bw, "Foundry models", sub="embedding and chat / language models used for memory transformation", theme="blue", icon="foundry", icon_pos="left", fill="solid")
        hh = max(b.h for b in (t1, t2, t3, t4))
        for i, b in enumerate((t1, t2, t3, t4)):
            b.place(cv, pt.ix + i * (bw + gx), pt.iy, h=hh)
        connect(cv, t1, t2, a_side="right", b_side="left", num=1, label="writes turns", label_size=14, label_dy=-14)
        connect(cv, t2, t3, a_side="right", b_side="left", num=2, label="change feed", label_size=14, label_dy=-14)
        connect(cv, t3, t4, a_side="right", b_side="left", num=3, label="calls", label_size=14, label_dy=-14)
        yv = t3.bottom + 46
        connect(cv, t3, t2, a_side="bottom", b_side="bottom", via=[(t3.cx, yv), (t2.cx, yv)], dash="dashed", num=4,
                label="derived memories (summary, fact, user_summary) stored as JSON documents", label_size=14, label_dy=-14)
        yb = yv + 50
        cv.text(pt.ix, yb, "Memory types stored as documents", size=20, color=get_theme("teal").deep)
        yb += 34
        chipw = (W - 52 - 3 * 28) / 4
        mt = [
            Card(chipw, "turn", ["Raw user, agent, tool and system messages"], theme="teal", title_size=19, body_size=15),
            Card(chipw, "summary", ["Per-thread summary generated from turns"], theme="teal", title_size=19, body_size=15),
            Card(chipw, "fact", ["Discrete assertion: preference, requirement or decision"], theme="teal", title_size=19, body_size=15),
            Card(chipw, "user_summary", ["Cross-thread user profile"], theme="teal", title_size=19, body_size=15),
        ]
        _, rb = row(cv, pt.ix, yb, mt, gap=28)
        nw2 = (W - 52 - 28) // 2
        n_ops = Note(nw2, "Add (local in-memory or direct to Cosmos DB), upload, retrieve by user / thread / recent, semantic and hybrid (vector + full-text) search, generate summaries, extract facts, generate user summaries, and reconcile facts.",
                     kind="info", title="Operations", size=15, src=[("Agent Memory Toolkit", CD("gen-ai/agent-memory-toolkit"))])
        n_rec = Note(nw2, "Reconcile detects duplicate and contradictory facts; superseded records are soft-deleted with an audit trail. Production = Azure Durable Functions + Cosmos DB change feed; proof of concept = orchestrate manually in app code.",
                     kind="key", title="Reconcile and run modes", size=15)
        hn2 = max(n_ops.h, n_rec.h)
        n_ops.place(cv, pt.ix, rb + 24, h=hn2)
        n_rec.place(cv, pt.ix + nw2 + 28, rb + 24, h=hn2)
    draw_badge(cv, pt.right - 130, pt.y + 20, "preview")
    return pt.bottom


# ---------------------------------------------------------------------------------------------- lane C
def lane_c(cv, y):
    y = band(cv, y, "C", "Tools and analytics: Cosmos DB MCP Toolkit, Fabric mirroring, AI Search indexer",
             sub=f"Ways to reach the same data from agents, analytics and search ({ASOF})", theme="orange")
    with cv.panel(0, y, title="Cosmos DB MCP Toolkit - read-only data access for agents",
                  sub="open source AzureCosmosDB/MCPToolKit | May 2026 release | hosted on Azure Container Apps", theme="orange", style="dotted",
                  fill="none", pad=26, title_size=26, sub_size=15, w=W) as pm:
        bw = 640
        gx = (W - 52 - 4 * bw) / 3
        m1 = Box(bw, "Foundry agent", sub="calls the MCP tool like any other tool", theme="green", icon="agent", icon_pos="left", fill="solid")
        m2 = Box(bw, "Foundry custom MCP tool", sub="Tools -> Add Custom Tool; Entra authentication; project or user identity", theme="orange", icon="mcp",
                 icon_pos="left", fill="solid")
        m3 = Box(bw, "Cosmos MCP Toolkit on Azure Container Apps", sub="validates the Entra JWT; app role Mcp.Tool.Executor", theme="orange",
                 icon="container-apps", icon_pos="left", fill="solid")
        m4 = Box(bw, "Azure Cosmos DB for NoSQL", sub="toolkit identity holds Cosmos DB Data Reader", theme="cyan", icon="cosmos", icon_pos="left", fill="solid")
        hh = max(b.h for b in (m1, m2, m3, m4))
        for i, b in enumerate((m1, m2, m3, m4)):
            b.place(cv, pm.ix + i * (bw + gx), pm.iy, h=hh)
        connect(cv, m1, m2, a_side="right", b_side="left", num=1, label="MCP request", label_size=14, label_dy=-14)
        connect(cv, m2, m3, a_side="right", b_side="left", num=2, label="Entra token", label_size=14, label_dy=-14)
        connect(cv, m3, m4, a_side="right", b_side="left", num=3, label="read-only queries", label_size=14, label_dy=-14)
        ye = m1.bottom + 70
        m5 = Box(bw, "Azure OpenAI embeddings", sub="only for vector_search; toolkit needs Cognitive Services OpenAI User", theme="blue", icon="openai",
                 icon_pos="left", fill="solid")
        m5.place(cv, m3.x, ye)
        connect(cv, m3, m5, a_side="bottom", b_side="top", label="vector_search", label_size=14)
        tools_w = 2 * bw + gx - 20
        c_roles = Card(bw, "Roles and hardening", [
            "Toolkit identity: Cosmos DB Data Reader",
            "Deployer: AcrPush",
            "Embeddings: Cognitive Services OpenAI User",
            "Private endpoints recommended",
        ], theme="red", icon="managed-identity", src=[("Cosmos DB MCP Toolkit", CD("gen-ai/model-context-protocol-toolkit"))])
        c_roles.place(cv, m4.x, ye)
        ot = get_theme("orange")
        cf = ChipFlow(["list_databases", "list_collections", "get_recent_documents (1-20)", "find_document_by_id", "text_search",
                       "vector_search", "get_approximate_schema"], tools_w - 36, theme="orange", size=17, gap=12)
        h_tools = max(56 + cf.h + 20, c_roles.h)
        with cv.group():
            cv.rect(pm.ix, ye, tools_w, h_tools, stroke=ot.stroke, fill=ot.fill, style="hachure", sw=2)
            cv.text(pm.ix + 18, ye + 14, "7 read-only tools exposed by the toolkit", size=20, color=ot.deep)
            cf.place(cv, pm.ix + 18, ye + 56)
        cv.register("card:tools", pm.ix, ye, tools_w, h_tools, container=True)
    y2 = pm.bottom + 54

    with cv.panel(0, y2, title="Analytics and search around the account", sub="mirroring, Cosmos DB in Fabric and an Azure AI Search indexer", theme="cyan",
                  style="dotted", fill="none", pad=26, title_size=26, sub_size=15, w=C2) as pa:
        bw = 350
        a2 = Box(bw, "Fabric OneLake", sub="mirrored database; near-real-time, no RU consumption", theme="teal", icon="onelake", fill="solid", min_h=150)
        a3 = Box(bw, "Fabric IQ (preview)", sub="live business state in OneLake for agents", theme="teal", icon="fabric", fill="solid", min_h=150)
        a4 = Box(bw, "Azure AI Search", sub="indexer over Cosmos DB for NoSQL; shared private link group Sql", theme="teal", icon="ai-search", fill="solid", min_h=150)
        a5 = Box(bw, "Foundry agents", sub="AI Search tool or Foundry IQ", theme="green", icon="agent", fill="solid", min_h=150)
        a1 = Box(bw, "Azure Cosmos DB for NoSQL", sub="mirroring needs continuous backup", theme="cyan", icon="cosmos", fill="solid", min_h=150)
        x2 = pa.ix + bw + 200
        a2.place(cv, x2, pa.iy)
        a3.place(cv, a2.right + 130, pa.iy)
        a4.place(cv, x2, a2.bottom + 40)
        a5.place(cv, a3.x, a4.y)
        a1.place(cv, pa.ix, (a2.cy + a4.cy) / 2 - a1.h / 2)
        connect(cv, a1, a2, a_side="right", b_side="left", route="elbow", bend=0.3, label="mirroring", label_size=14, label_t=0.86)
        connect(cv, a2, a3, a_side="right", b_side="left", label="OneLake data", label_size=13)
        connect(cv, a1, a4, a_side="right", b_side="left", route="elbow", bend=0.3, label="indexer", label_size=14, label_t=0.86)
        connect(cv, a4, a5, a_side="right", b_side="left", label="index", label_size=14)
    c_mir = Card(C4, "Fabric mirroring: what to know", [
        "NoSQL API only; needs continuous backup (7- or 30-day; 7-day is free)",
        "Near-real-time replication with no RU consumption; replication compute is free",
        "Not in sovereign clouds; no multi-write regions; vector-enabled accounts supported",
        "Entra needs readMetadata + readAnalytics; private network via VNet data gateway + trusted-workspace bypass",
    ], theme="cyan", icon="onelake", src=[("Mirroring Azure Cosmos DB", learn("fabric/mirroring/azure-cosmos-db", base=""))])
    c_fab = Card(C4, "Cosmos DB in Fabric", [
        "AI-optimised NoSQL database inside Fabric",
        "Vector, full-text and hybrid (RRF) search",
        "Auto-mirrored to OneLake",
        "Listed separately from mirroring: mirroring replicates an existing Azure Cosmos DB account into Fabric",
    ], theme="teal", icon="fabric", src=[("Cosmos DB in Fabric", learn("fabric/database/cosmos-db/overview", base=""))])
    hmf = max(c_mir.h, c_fab.h)
    c_mir.place(cv, C2 + GAP, y2, h=hmf)
    c_fab.place(cv, C2 + GAP + C4 + GAP, y2, h=hmf)
    return max(pa.bottom, y2 + hmf)


# ---------------------------------------------------------------------------------------------- docs disagree
def disagree(cv, y):
    y = band(cv, y, "?", "Where the docs disagree", sub=f"Both values are shown as documented ({ASOF}) - check the live page before you size or automate", theme="yellow")
    t = Table(
        [("Topic", 380), ("One page says", 1400), "Another page says"],
        [
            ["How many containers up front (3 vs 5)", "standard-agent-setup: the standard setup provisions five containers of 1,000 RU/s each (and elsewhere: three provisioned for project isolation)",
             "use-your-own-resources and the Cosmos DB page: three to five - three at provisioning, up to two more created dynamically for Responses-API agents"],
            ["agent-entity-store", "standard-agent-setup: agent metadata (instructions, tools, name)", "Cosmos DB azure-agent-service page: captures model inputs and outputs"],
            ["run-state-v1", "standard-agent-setup: internal messages and end-user conversations", "Cosmos DB page: tracks the execution state of agent runs"],
            ["Agent blob container name", "standard-agent-setup and use-your-own-resources: <workspaceId>-azureml-agent", "BYO-storage page: <workspaceId>-agents-blobstore"],
            ["PITR retention tiers", "7 and 30 days (continuous backup tiers)", "A 35-day figure also appears across the DR pages"],
            ["Serverless vs 1,000 RU/s per container", "Docs say provisioned or serverless accounts are supported", "Docs also require 1,000 RU/s on every container - check serverless behaviour before choosing it"],
            ["Capability settings how-to", "Linked from the setup pages as how-to/configure-capability-settings", "The page currently redirects to agents/environment-setup; capability-settings ARM API versions are preview only"],
        ], w=W, theme="yellow", size=15, head_size=16, first_col_theme="yellow")
    t.place(cv, 0, y)
    return t.bottom


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Azure Cosmos DB in the Foundry ecosystem",
                                f"Agent state, memory, vectors and tools - three roles around Cosmos DB for NoSQL ({ASOF})",
                                icon="cosmos", w=W)
    y = bottom + 22
    legend(cv, 0, y, [("Foundry agents / runtime", "green"), ("Cosmos DB / data", "cyan"), ("Identity and RBAC", "red"),
                      ("Networking", "indigo"), ("Memory / knowledge", "teal"), ("Tools / MCP", "orange"), ("Capacity (RU/s)", "yellow"),
                      ("Disaster recovery", "grape"), ("Classic / not Cosmos-backed", "gray")])
    cv.text(W - 520, y, "dashed outline = preview, optional or created lazily", size=15, color=MUTED)
    y = band_summary(cv, y + 50) + 70
    y = lane_a(cv, y) + 70
    y = dr_band(cv, y) + 70
    y = not_cosmos(cv, y) + 70
    y = lane_b(cv, y) + 70
    y = lane_c(cv, y) + 70
    y = disagree(cv, y) + 70
    sources(cv, 0, y, [
        ("Set up standard agent resources (Foundry Agent Service)", learn("agents/concepts/standard-agent-setup")),
        ("Use your own resources in Foundry Agent Service", learn("agents/how-to/use-your-own-resources")),
        ("Capability hosts", learn("agents/concepts/capability-hosts")),
        ("Integration with Foundry Agent Service (Cosmos DB for NoSQL)", CD("gen-ai/azure-agent-service")),
        ("Foundry Agent Service disaster recovery", learn("how-to/agent-service-disaster-recovery")),
        ("Operator disaster recovery (Agent Service)", learn("how-to/agent-service-operator-disaster-recovery")),
        ("Configure network isolation (private link)", learn("how-to/configure-private-link")),
        ("Cosmos DB data-plane role-based access control", CD("how-to-connect-role-based-access-control")),
        ("Agent memory in Azure Cosmos DB for NoSQL", CD("gen-ai/agentic-memories")),
        ("Vector search in Azure Cosmos DB for NoSQL", CD("vector-search")),
        ("Hybrid search in Azure Cosmos DB for NoSQL", CD("gen-ai/hybrid-search")),
        ("Semantic cache in Azure Cosmos DB for NoSQL", CD("gen-ai/semantic-cache")),
        ("Agent Memory Toolkit for Azure Cosmos DB (preview)", CD("gen-ai/agent-memory-toolkit")),
        ("Azure Cosmos DB MCP Toolkit", CD("gen-ai/model-context-protocol-toolkit")),
        ("Mirroring Azure Cosmos DB (Microsoft Fabric)", learn("fabric/mirroring/azure-cosmos-db", base="")),
    ], w=W, cols=3)
