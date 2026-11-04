"""Agent Service disaster recovery (3-page series): anatomy, who recovers what, incident map, the two playbooks."""
from __future__ import annotations

import math

from generator.xd import *
from generator.xd import metrics
from generator.xd.blocks import SAFETY, draw_badge
from generator.xd.palette import theme as get_theme

META = dict(
    id="bcdr-agent-service", title="Agent Service disaster recovery", section="4", order=3,
    description="Standard-setup Agent Service DR from all three DR pages: where state lives, what Microsoft recovers vs what you rebuild, the platform-outage and resource/data-loss playbooks with documented RTO and recovery points.",
    tags=["bcdr", "agent-service", "disaster-recovery", "cosmos-db", "recovery", "runbook"],
)

W = 2940
DR0 = learn("how-to/agent-service-disaster-recovery")
DRP = learn("how-to/agent-service-platform-disaster-recovery")
DRO = learn("how-to/agent-service-operator-disaster-recovery")
HA = learn("how-to/high-availability-resiliency")
STD = learn("agents/concepts/standard-agent-setup")
CAP = learn("agents/concepts/capability-hosts")
ENV = learn("agents/environment-setup")
LIM = learn("agents/concepts/limits-quotas-regions")
ARCH = learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")
COSREL = learn("azure/reliability/reliability-cosmos-db-nosql", base="")
SRCHREL = learn("azure/reliability/reliability-ai-search", base="")
STGREL = learn("azure/reliability/reliability-storage-blob", base="")
RECOVER = learn("azure/ai-services/recover-purge-resources", base="")
COSRESTORE = learn("azure/cosmos-db/restore-account-continuous-backup", base="")
GATEWAY = learn("azure/architecture/patterns/gateway-routing", base="")

GREEN, AMBER, RED = "green", "yellow", "red"


# ---------------------------------------------------------------------------------------------- helpers
def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(metrics.wrap_text(s, w * SAFETY, size))


def pill(cv: Canvas, x: float, y: float, label: str, theme: str = "gray", size: int = 14, *, fill: str = "solid",
         pad_x: float = 10, pad_y: float = 3, dash: str = "solid", min_w: float = 0, color: str | None = None):
    """Small rounded label that does not take part in overlap checks. Returns (w, h)."""
    th = get_theme(theme)
    label, _ = metrics.sanitize(label)
    tw, thh = metrics.text_size(label, size)
    w = max(tw + 2 * pad_x, min_w)
    h = thh + 2 * pad_y
    bg = {"solid": th.fill, "soft": th.soft, "none": "transparent"}[fill]
    with cv.group():
        cv.rect(x, y, w, h, stroke=th.stroke, fill=bg, style="solid", sw=1.5, dash=dash, rough=0)
        cv.text(x + (w - tw) / 2, y + pad_y, label, size=size, color=color or th.deep)
    return w, h


def cite(cv: Canvas, x: float, y: float, items: list[tuple[str, str]]) -> float:
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 2
    return y


def sec(cv: Canvas, y: float, num: str, text: str, sub: str | None = None) -> float:
    _, b = section_header(cv, 0, y, f"{num}  {text}", size=32, sub=sub, sub_size=17)
    return b + 34


class Cylinder(Rect2):
    """Data-store cylinder (Excalidraw has no native one)."""

    def __init__(self, w: float, h: float, label: str, *, theme: str = "cyan", sub: str | None = None,
                 icon: str | None = None, cap: float = 34, size: int = 19, sub_size: int = 14):
        self.w, self.h, self.label, self.sub, self.theme, self.icon = w, h, label, sub, theme, icon
        self.cap, self.size, self.sub_size = cap, size, sub_size
        self.x = self.y = 0.0

    def place(self, cv: Canvas, x: float, y: float, h: float | None = None) -> "Cylinder":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, cap, w = get_theme(self.theme), self.cap, self.w
        with cv.group():
            cv.rect(x, y + cap / 2, w, H - cap, stroke="transparent", fill=th.soft, style="solid", sw=0,
                    round_=False, rough=0)
            cv.ellipse(x, y + H - cap, w, cap, stroke="transparent", fill=th.soft, style="solid", sw=0, rough=0)
            cv.line((x, y + cap / 2), (x, y + H - cap / 2), stroke=th.stroke, sw=2, rough=0)
            cv.line((x + w, y + cap / 2), (x + w, y + H - cap / 2), stroke=th.stroke, sw=2, rough=0)
            n = 16
            arc = [(x + w / 2 - (w / 2) * math.cos(math.pi * i / n), y + H - cap / 2 + (cap / 2) * math.sin(math.pi * i / n))
                   for i in range(n + 1)]
            cv.poly(arc, kind="line", stroke=th.stroke, sw=2, rough=0)
            cv.ellipse(x, y, w, cap, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
            # text block centred in the body
            left = 18 + (46 if self.icon else 0)
            lines = metrics.wrap_text(self.label, (w - left - 16) * SAFETY, self.size)
            subl = metrics.wrap_text(self.sub, (w - left - 16) * SAFETY, self.sub_size) if self.sub else []
            lh = metrics.line_ratio()
            th_h = len(lines) * self.size * lh + (len(subl) * self.sub_size * lh + 3 if subl else 0)
            top = y + cap + 4
            avail = H - cap - cap / 2 - 8
            ty = top + max(0, (avail - th_h) / 2)
            if self.icon:
                place_icon(cv, self.icon, x + 16, top + max(0, (avail - 38) / 2), 38)
            cv.text(x + left, ty, "\n".join(lines), size=self.size, color=th.deep)
            if subl:
                cv.text(x + left, ty + len(lines) * self.size * lh + 3, "\n".join(subl), size=self.sub_size, color=MUTED)
        return self


class FootCard(Card):
    """Card with an RTO / recovery-point footer. Pill colour = our reading of the documented recovery point."""
    LAB = 48

    def __init__(self, w: float, title: str, body, *, rto: str, rp: str, sev: str, foot_size: int = 15, **kw):
        super().__init__(w, title, body, **kw)
        self.rto, self.rp, self.sev, self.foot_size = rto, rp, sev, foot_size
        inner = (w - 2 * self.pad) * SAFETY - self.LAB - 8
        self.rto_lines = metrics.wrap_text(rto, inner, foot_size)
        self.rp_lines = metrics.wrap_text(rp, inner, foot_size)
        lh = foot_size * metrics.line_ratio()
        self.foot_h = (len(self.rto_lines) + len(self.rp_lines)) * lh + 6 + 14
        self.content_h += self.foot_h
        self.h = max(self.h, self.content_h)

    def place(self, cv: Canvas, x: float, y: float, h: float | None = None) -> "FootCard":
        super().place(cv, x, y, h)
        pad = self.pad
        lh = self.foot_size * metrics.line_ratio()
        fy = y + self.h - pad - (self.foot_h - 14)
        cv.line((x + pad, fy - 9), (x + self.w - pad, fy - 9), stroke=self.th.stroke, sw=1, dash="dotted", opacity=70)
        pill(cv, x + pad, fy - 1, "RTO", "blue", size=13, min_w=self.LAB)
        cv.text(x + pad + self.LAB + 8, fy, "\n".join(self.rto_lines), size=self.foot_size, color=INK)
        fy2 = fy + len(self.rto_lines) * lh + 6
        pill(cv, x + pad, fy2 - 1, "RP", self.sev, size=13, min_w=self.LAB)
        cv.text(x + pad + self.LAB + 8, fy2, "\n".join(self.rp_lines), size=self.foot_size, color=INK)
        return self


# ---------------------------------------------------------------------------------------------- 0. headline
def headline(cv: Canvas, y: float) -> float:
    q = Note(1140, "Agent Service doesn't provide built-in disaster recovery capabilities. It doesn't replicate state, "
                   "create backups, or support point-in-time restore. One project can't use the data of another project. "
                   "The service doesn't have any supported method for active-active, multi-region replication. "
                   "Microsoft Support can't recover orphaned data, migrate data between projects, or combine state from "
                   "multiple sources.\n\nThe recommendations in this guide are compensating controls. Recovery might not be possible.",
             kind="gotcha", title="The overview page, verbatim", size=17, src=[("Agent Service disaster recovery", DR0)])
    tw = (W - 1140 - 3 * 40) / 3
    t1 = Card(tw, "Failover rebuilds the project", [
        "Recovered agents are new agents with new IDs",
        "No access to prior threads or uploaded files",
        "Clients need the new FQDN and agent IDs - or route through a gateway",
        "Standby-region state is lost on failback",
    ], theme="red", icon="agent", src=[("Platform outage recovery", DRP)])
    t2 = Card(tw, "Multi-region data doesn't help", [
        "Cosmos DB multi-region writes and Storage multi-region recovery don't improve recovery",
        "enterprise_memory partitions data by a globally unique ID per project instance",
        "Data created during failover is keyed to new project IDs, so failback can't keep it",
    ], theme="red", icon="regions", src=[("Platform outage recovery", DRP)])
    t3 = Card(tw, "A deleted thread is gone", [
        "No supported way to restore a deleted conversation thread",
        "Cosmos DB PITR restores to a different account, not the same one; hand-editing enterprise_memory is unsupported",
        "Purview copy = eDiscovery only, and may lag (ingestion delay)",
    ], theme="red", icon="cosmos", src=[("Resource and data loss recovery", DRO)])
    _, b = row(cv, 0, y, [q, t1, t2, t3], gap=40)
    return b


# ---------------------------------------------------------------------------------------------- 1. anatomy
def anatomy(cv: Canvas, y: float) -> float:
    y0 = y
    AX, AW = 330, 830
    clients = Box(200, "Clients", sub="apps and AI gateway: hold the project FQDN and agent IDs", theme="gray",
                  icon="app", h=150, size=19, sub_size=14)
    with cv.panel(AX, y0, title="Foundry account", sub=wrap(
            "Microsoft operates the control plane, data-plane APIs and agent runtime (zone-redundant hosted components)",
            AW - 52, 15), theme="blue", style="solid", fill="soft", pad=26, title_size=30, sub_size=15, w=AW) as acct:
        with cv.panel(acct.ix, acct.iy, title="Project A: the recovery unit",
                      sub="blast-radius boundary with its own globally unique ID", theme="green", style="dashed",
                      fill="soft", pad=20, title_size=24, sub_size=15, w=AW - 52) as pa:
            rt = Box(330, "Agent runtime infrastructure", sub="per project; provisioned by Agent Service",
                     theme="green", icon="agent", icon_pos="left", h=96, size=17).place(cv, pa.ix, pa.iy)
            cs = Box(330, "Capability settings", sub="declare where state, vectors and files live", theme="green",
                     icon="gear", icon_pos="left", h=96, size=17).place(cv, pa.ix + 330 + 56, pa.iy)
            connect(cv, rt, cs, label="reads", color="#2f9e44")
        Box(AW - 52, "Project B: separate GUID and containers; can't read Project A's data", theme="gray", fill="none",
            dash="dashed", h=60, size=16).place(cv, acct.ix, pa.bottom + 18)
    clients.place(cv, 0, y0 + (acct.h - clients.h) / 2)
    connect(cv, clients, acct, a_side="right", b_side="left", ta=0.5, tb=0.5, label="data-plane APIs", label_size=14,
            color="#1971c2", sw=3)
    pill(cv, acct.right - 26 - 96, acct.y + 22, "Microsoft", "blue", size=15)

    YX = AX + AW + 60
    YW = W - YX
    bus_y = cs.cy
    cw = (YW - 52 - 2 * 45) / 3
    with cv.panel(YX, y0, title="Your subscription: agent state resources you bring (Standard setup)", sub=wrap(
            "You own their durability: redundancy, backup, replication, locks. They all depend on your region's availability.",
            YW - 52, 15), theme="orange", style="dotted", pad=26, title_size=30, sub_size=15, w=YW) as you:
        iso = Note(YW - 52, "Standard setup isolates data by project: separate blob containers and Cosmos DB containers per project, "
                            "so one project can't use another project's data. 'Projects are currently the unit of sharing and isolation in Foundry.'",
                   kind="info", title="Project-level isolation by default", size=15, src=[("Standard agent setup", STD)])
        iso.place(cv, you.ix, you.iy + 4)
        cyl_y = bus_y + 78
        xs = [you.ix + i * (cw + 45) for i in range(3)]
        cyls = [
            Cylinder(cw, 170, "Azure Cosmos DB for NoSQL", theme="cyan", sub="BYO Thread Storage - database enterprise_memory", icon="cosmos").place(cv, xs[0], cyl_y),
            Cylinder(cw, 170, "Azure AI Search", theme="teal", sub="BYO Search - vector stores for the runtime", icon="ai-search").place(cv, xs[1], cyl_y),
            Cylinder(cw, 170, "Azure Storage", theme="cyan", sub="BYO File Storage - blob containers", icon="storage").place(cv, xs[2], cyl_y),
        ]
        cosmos = Card(cw, "What Cosmos DB holds", [
            "Messages, conversation history, agent metadata and definitions, run state",
            "New runtime: agent-definitions-v1 (agent metadata incl. versions), run-state-v1 (internal messages + end-user conversations)",
            "Classic runtime: thread-message-store, system-thread-message-store, agent-entity-store - Classic and New use different containers",
            "Standard setup 'provisions five containers, each requiring 1000 RU/s'; account needs >= 3000 RU/s (provisioned or serverless)",
            "Data is partitioned by a globally unique ID per project instance",
        ], theme="cyan", icon="cosmos", src=[("Standard agent setup", STD)])
        search = Card(cw, "What AI Search holds", [
            "Vector stores the agent creates: real-time indexing for agent knowledge and thread uploads",
            "A dedicated instance for the Agent Service runtime - 'Don't confuse this instance with AI Search indexes that ... act as a durable knowledge store for workload data'",
            "Project identity roles: Search Index Data Contributor + Search Service Contributor",
            "AI Search is a derived projection: keep authoritative content elsewhere",
        ], theme="teal", icon="ai-search", src=[("Standard agent setup", STD), ("High availability", HA)])
        storage = Card(cw, "What Storage holds", [
            "Files uploaded by developers and end users, plus intermediate system data (chunks, embeddings)",
            "Two blob containers are provisioned for the project: <workspaceId>-azureml-blobstore (Storage Blob Data Contributor) and <workspaceId>-azureml-agent (Storage Blob Data Owner)",
            "! User-uploaded thread files 'generally can't be recovered': they aren't persisted outside the thread context",
        ], theme="cyan", icon="storage", src=[("Standard agent setup", STD), ("High availability", HA)])
        _, cards_b = row(cv, xs[0], cyl_y + 170 + 36, [cosmos, search, storage], gap=45)
        # bus: capability settings -> three stores
        col_ = "#e8590c"
        cx = [c.x + c.w / 2 for c in cyls]
        arrow(cv, [(cs.right + 6, bus_y), (cx[0], bus_y), (cx[0], cyl_y - 6)], color=col_, sw=3)
        arrow(cv, [(cx[0], bus_y), (cx[1], bus_y), (cx[1], cyl_y - 6)], color=col_, sw=3)
        arrow(cv, [(cx[1], bus_y), (cx[2], bus_y), (cx[2], cyl_y - 6)], color=col_, sw=3)
        for xx, lab in zip(cx, ("threadStorageConnections", "vectorStoreConnections", "storageConnections")):
            cv.text(xx + 12, bus_y + 12, lab, size=15, color="#d9480f")
    pill(cv, you.right - 26 - 52, you.y + 22, "You", "orange", size=15)

    # left column under the account: wiring + basic ghost
    wiring = Card(AX + AW, "How a project is wired to its state", [
        "Capability settings (new) / capability hosts (older REST sub-resources) declare which Azure resources hold agent state",
        "Project capability host properties: threadStorageConnections (Cosmos DB), vectorStoreConnections (AI Search), storageConnections (Storage), optional aiServicesConnections",
        "No automatic inheritance of BYO resource configuration from the account capability host to the project",
        "Updating capability hosts isn't supported: delete and recreate. Capability settings of an existing project can't be updated: delete and recreate the project",
        "Key Vault holds secrets and connection strings for the agent infrastructure (a Microsoft-managed Key Vault is used by default in the quickstart templates)",
    ], theme="green", icon="gear", src=[("Capability hosts", CAP), ("Standard agent setup", STD)])
    wiring.place(cv, 0, max(acct.bottom, 0) + 36)
    return max(wiring.bottom, you.bottom)


# ---------------------------------------------------------------------------------------------- 2. tables
def tables(cv: Canvas, y: float) -> float:
    t1 = Table([("Topic", 250), ("Basic setup", 540), ("Standard setup", 650)], [
        ["Where agent state lives", "Microsoft-managed storage, logically separated (default)", "Your Cosmos DB + AI Search + Storage (BYO)"],
        ["Threads, messages, agent definitions", "Microsoft-managed storage", "Azure Cosmos DB for NoSQL"],
        ["Files, uploads, attachments", "Microsoft-managed storage", "Azure Storage (Blob)"],
        ["Vector stores, retrieval indexes", "Microsoft-managed vector search", "Azure AI Search"],
        ["Customer-managed recovery procedures", ("Not applicable: 'almost no recovery options for resource loss'", "red"), ("Apply (this series)", "green")],
        ["Incident risk", "Lower self-inflicted deletion risk", "'Increases incident risk (for example, direct data deletion) but gives you control over recovery procedures'"],
        ["Backups, PITR", "None documented", "You configure: Cosmos DB continuous backup, Storage GZRS, locks"],
        ["Customer-managed keys", CROSS, CHECK],
        ["Private network isolation (BYO VNet)", CROSS, "Standard setup with private networking only"],
        ["Mixing both in one Foundry account", ("Avoid", "yellow"), ("Avoid: use separate Foundry accounts and projects for Standard and Basic", "yellow")],
    ], w=1440, theme="cyan", size=14, head_size=15, title="Basic vs Standard: what changes for DR", title_size=22,
        first_col_theme="cyan")
    t2 = Table([("Layer", 330), ("Microsoft", 520), ("You", 590)], [
        ["Control plane, data-plane APIs, agent runtime infrastructure", ("Operates and maintains them; hosted components are zone-redundant", "blue"), DASH],
        ["Cosmos DB regional outage", ("The Cosmos DB team triggers a service-managed failover automatically ('internal decisions that you can't directly influence'); fail-back possibly 'three or more days later'", "blue"),
         ("Optional forced failover (loses unreplicated writes); update the connection if the account changes", "orange")],
        ["AI Search outage", ("Restores the service", "blue"), ("Wait - or a destructive reset onto a new instance (complete data loss)", "orange")],
        ["Storage outage", ("Restores the service (Microsoft-managed failover only in extreme cases)", "blue"),
         ("Customer-managed (unplanned) failover: Invoke-AzStorageAccountFailover", "orange")],
        ["Agents, definitions, knowledge files, tool bindings", DASH, ("You: source control + redeploy automation", "orange")],
        ["Thread history and uploaded files", DASH, ("Not recoverable. Purview copy for eDiscovery only (ingestion delay: may be stale)", "red")],
        ["IaC, RBAC, private endpoints, locks, identities", DASH, ("You. Account recovery doesn't restore private endpoints, projects or role assignments", "orange")],
    ], w=1440, theme="blue", size=14, head_size=15, title="Who recovers what", title_size=22, first_col_theme="gray")
    t1.place(cv, 0, y)
    t2.place(cv, W - 1440, y)
    b1 = cite(cv, 0, t1.bottom + 8, [("Standard agent setup", STD), ("Environment setup", ENV)])
    b2 = cite(cv, W - 1440, t2.bottom + 8, [("Agent Service disaster recovery", DR0), ("Platform outage recovery", DRP)])
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- 3. incident map
PLATFORM = [
    ("Complete regional outage", "30+ min per project", "No state is transferable between regions", RED, "regions"),
    ("Fail back to the primary region", "10+ min per project", "Exactly as before failover; standby state is permanently lost", GREEN, "regions"),
    ("Cosmos DB regional outage", "30+ min once triggered", "Up to 15 min of data may be lost", AMBER, "cosmos"),
    ("AI Search regional outage", "Indeterminate", "Preserved up to the outage; in-flight work might not persist", GREEN, "ai-search"),
    ("Storage regional outage", "20+ min", "About 15 min before the outage; expect some data loss", AMBER, "storage"),
    ("Storage failback", "10+ min", "About 10 min before failback; expect some data loss", AMBER, "storage"),
]
HUMAN = [
    ("Foundry account deleted", "30+ min", "Complete state loss (all projects)", RED, "foundry"),
    ("Foundry project deleted", "Minutes", "Total loss of thread and file data", RED, "foundry"),
    ("Production agent deleted", "Minutes", "State preserved up to deletion", GREEN, "agent"),
    ("Production thread deleted", "Not recoverable", "All thread state destroyed", RED, "agent"),
    ("Cosmos DB account deleted", "10+ min", "State preserved up to deletion", GREEN, "cosmos"),
    ("enterprise_memory database deleted", "10+ min", "State preserved up to deletion", GREEN, "cosmos"),
    ("enterprise_memory container deleted", "10+ min", "State preserved up to deletion", GREEN, "cosmos"),
    ("enterprise_memory container data corrupted", "Situational", "Total loss for the affected entities", RED, "cosmos"),
    ("AI Search service deleted", "20+ min", "Thread state lost; agent knowledge rebuilt", AMBER, "ai-search"),
    ("AI Search index deleted", "Minutes", "Thread state lost; agent knowledge rebuilt", AMBER, "ai-search"),
    ("Storage account deleted", "20+ min", "Thread state lost; agent knowledge rebuilt", AMBER, "storage"),
    ("Destructive reset (single project)", "Minutes", "Complete state loss (single project)", RED, "gear"),
]


def incident_map(cv: Canvas, y: float) -> float:
    LX = 430
    LW = W - LX
    tile_w = (LW - 2 * 26 - 5 * 18) / 6

    def tiles(data):
        return [FootCard(tile_w, t[0], [], rto=t[1], rp=t[2], sev=t[3], theme=t[3], icon=t[4], title_size=17,
                         icon_size=30, pad=12, foot_size=14, gap=3) for t in data]

    with cv.panel(LX, y, title="Platform or regional outage", sub="platform outage page: warm standby, failover, failback, dependency outages",
                  theme="blue", style="dotted", pad=26, title_size=26, sub_size=15, w=LW) as l1:
        row(cv, l1.ix, l1.iy, tiles(PLATFORM), gap=18)
    with cv.panel(LX, l1.bottom + 40, title="Human or automation error", sub="resource and data loss page: deletes, corruption, destructive reset",
                  theme="orange", style="dotted", pad=26, title_size=26, sub_size=15, w=LW) as l2:
        _, b = row(cv, l2.ix, l2.iy, tiles(HUMAN[:6]), gap=18)
        row(cv, l2.ix, b + 18, tiles(HUMAN[6:]), gap=18)
    ymid = (l1.y + l2.bottom) / 2
    root = Box(230, "Something is down or gone", sub="the platform, or a delete or corruption?", theme="red", h=130, size=19).place(cv, 0, ymid - 65)
    xm = 276
    arrow(cv, [(root.right + 6, root.cy - 20), (xm, root.cy - 20), (xm, l1.y + 60), (l1.x - 6, l1.y + 60)], color="#1971c2", sw=3)
    cv.text(xm + 8, l1.y + 34, "Azure outage", size=14, color="#1864ab")
    arrow(cv, [(root.right + 6, root.cy + 20), (xm, root.cy + 20), (xm, l2.y + 60), (l2.x - 6, l2.y + 60)], color="#e8590c", sw=3)
    cv.text(xm + 8, l2.y + 34, "delete / corrupt", size=14, color="#d9480f")
    t = cv.text(0, l2.bottom + 14, "Recovery time and recovery point are quoted from the two playbook pages; the traffic-light colour is our reading of the recovery point. "
                "Foundry publishes no SLA-backed RTO or RPO for Agent Service.", size=15, color=MUTED)
    return t.bottom


# ---------------------------------------------------------------------------------------------- 4. playbook A
def playbook_a(cv: Canvas, y: float) -> float:
    y0 = y
    # --- decision tree (left)
    d1 = Box(290, "Region-wide outage?", shape="diamond", theme="red", h=150, size=19).place(cv, 0, y0 + 30)
    b1 = Box(320, "Decide per project", sub="business need vs expected outage duration, consequences and alternative plans",
             theme="grape", h=126, size=18).place(cv, 370, y0 + 42)
    b2 = Box(320, "Run your store and tool playbooks first", sub="don't fail over agents whose knowledge stores and tools don't fail over",
             theme="orange", h=126, size=18).place(cv, 760, y0 + 42)
    b3 = Box(320, "Warm-standby failover", sub="steps 1-6 below; per project; RTO 30+ min", theme="green", h=126, size=18,
             icon="agent").place(cv, 1150, y0 + 42)
    connect(cv, d1, b1)
    cv.text(d1.right + 26, d1.cy - 28, "yes", size=16)
    connect(cv, b1, b2)
    connect(cv, b2, b3)
    single = Box(1070, "Only one dependency is down", sub="Don't fail the whole project over: use the dependency playbook below. Cosmos DB: wait for the service-managed failover "
                 "(or force one). AI Search: wait. Storage: wait or customer-managed failover.", theme="cyan", h=118, size=19, sub_size=15)
    single.place(cv, 370, y0 + 250)
    arrow(cv, [(d1.cx, d1.bottom + 6), (d1.cx, single.cy), (single.x - 6, single.cy)], color=INK, sw=2)
    cv.text(d1.cx + 12, d1.bottom + 14, "no", size=16)

    mon = Card(1470, "Before the incident: monitor and automate", [
        "Azure Service Health alerts notify you of service issues and planned maintenance - e.g. az monitor activity-log alert create ... --condition category=ServiceHealth",
        "Automate the failover steps (scripts or IaC), triggered by monitoring or by operators - e.g. Azure Automation runbooks or Logic Apps in response to Service Health alerts",
        "Add a layer of indirection: the Gateway Routing pattern in a multi-region gateway such as API Management, so you fail over by updating gateway routing instead of every client's FQDN",
    ], theme="indigo", icon="alerts", src=[("Platform outage recovery", DRP), ("Gateway Routing pattern", GATEWAY)])
    mon.place(cv, 0, single.bottom + 30)

    # --- warm standby architecture (right)
    AXr = 1560
    AWr = W - AXr
    gw = Box(AWr, "AI gateway: multi-region API Management", sub="clients keep one FQDN; failing over = updating routing inside the gateway",
             theme="indigo", icon="apim", icon_pos="left", h=92, size=19).place(cv, AXr, y0)
    pw = 520
    with cv.panel(AXr, y0 + 190, title="Primary region", sub="the outage", theme="red", style="dotted", pad=22, title_size=24,
                  sub_size=15, w=pw, min_h=396) as prim:
        Box(pw - 44, "Foundry account + projects", sub="agents, capability settings", theme="green", icon="foundry",
            icon_pos="left", h=84, size=17).place(cv, prim.ix, prim.iy)
        Box(pw - 44, "Cosmos DB + AI Search + Storage", sub="the project state (per-project GUID)", theme="cyan", icon="cosmos",
            icon_pos="left", h=84, size=17).place(cv, prim.ix, prim.iy + 100)
        cv.text(prim.ix, prim.iy + 206, wrap(
            "During the incident: you can't create, delete, modify or invoke agents in any project; data-plane API calls error or time out; the Foundry portal is unavailable for the whole account.",
            pw - 44, 15), size=15, color="#c92a2a")
    fx = AXr + pw + 56
    fw = W - fx
    with cv.panel(fx, y0 + 190, title="Failover region: warm standby", sub="low idle cost, fully networked, always on; paired or otherwise acceptable region",
                  theme="green", style="dotted", pad=22, title_size=24, sub_size=15, w=fw, min_h=396) as fo:
        iw = fw - 44
        Box(iw, "VNet mirrors the primary subnet topology + cross-premises connectivity", sub="egress controls and firewall rules kept in sync while idle",
            theme="indigo", icon="vnet", icon_pos="left", h=84, size=16).place(cv, fo.ix, fo.iy)
        Box(iw, "Foundry account with agent capability enabled", sub="NO projects, NO project-specific connections, NO model deployments",
            theme="green", icon="foundry", icon_pos="left", h=84, size=16).place(cv, fo.ix, fo.iy + 100)
        Box(iw, "Diagnostics, Defender for Cloud, Purview integration", sub="match the production account configuration",
            theme="violet", icon="defender", icon_pos="left", h=84, size=16).place(cv, fo.ix, fo.iy + 200)
    arrow(cv, [(prim.cx, gw.bottom + 6), (prim.cx, prim.y - 6)], color="#2f9e44", sw=3, label="normal traffic", label_size=14)
    arrow(cv, [(fo.cx, gw.bottom + 6), (fo.cx, fo.y - 6)], color="#2f9e44", sw=3, dash="dashed", label="after failover", label_size=14)
    n = Note(AWr, "Re-create only the projects you need (and their dependencies) during failover and drills. Pre-provisioning the state resources cuts RTO but adds cost and "
                  "operational overhead: Storage is cheap when idle, AI Search isn't.", kind="tip", title="Hybrid pre-provisioning",
             src=[("Platform outage recovery", DRP)])
    n.place(cv, AXr, max(prim.bottom, fo.bottom) + 24)
    ybot = max(mon.bottom, n.bottom)

    # --- fail over chain
    yf = ybot + 60
    _, b = section_header(cv, 0, yf, "Fail over, per project you choose to recover", size=26,
                          sub="Don't fail over a project's agents unless the knowledge stores and tools they need fail over too", sub_size=16, underline=False)
    yf = b + 30
    cw = (W - 5 * 40) / 6
    steps = [
        ("Deploy state resources", "cosmos", [
            "Cosmos DB + AI Search + Storage in the recovery region from IaC; match topology and configuration",
            "Shared dependencies: do this once",
        ]),
        ("Create the project's identity", "managed-identity", [
            "A user-assigned managed identity for the project",
            "Give it access to the new regional dependencies",
        ]),
        ("Create the project in the standby account", "foundry", [
            "Via IaC: assign the identity, point capability settings at the new regional resources",
            "Apply role assignments for clients, operators and automation principals",
        ]),
        ("Redeploy agents", "agent", [
            "Definitions, knowledge files and tool connections from source control",
            "They are new agents with new IDs and no access to prior threads or files",
        ]),
        ("Recover client components", "app", [
            "If they're part of the workload: follow their own recovery playbooks",
        ]),
        ("Repoint clients", "apim", [
            "New account FQDN + new agent IDs - or update the AI gateway routing instead",
            "Tell users they're in a standby environment: history is unavailable and new conversations are lost after failback",
        ]),
    ]
    cards = [Card(cw, t, bl, theme="green", icon=ic, title_size=19, body_size=15, icon_size=34) for t, ic, bl in steps]
    r, bb = row(cv, 0, yf, cards, gap=40)
    for i, c in enumerate(cards):
        numbered(cv, c.x - 2, c.y - 2, i + 1, theme="green", d=34, size=19)
        if i:
            connect(cv, cards[i - 1], c, color="#2f9e44", sw=3)
    rn = Note(W, "RTO: 30 or more minutes per project.   RPO: no state is transferable between regions - original state returns only when the primary region is back; "
                 "threads and agents created in the standby region don't persist after failback. Recovery restores functionality only.",
              kind="key", title="Result (as documented)", size=16)
    rn.place(cv, 0, bb + 26)

    # --- fail back chain
    yb = rn.bottom + 56
    _, b = section_header(cv, 0, yb, "Fail back, once the primary region is stable", size=26,
                          sub="Return traffic and re-establish the secondary as a warm standby", sub_size=16, underline=False)
    yb = b + 30
    back = [
        ("Delete the project from the standby account", "foundry", ["This orphans all agents and threads created during the failover"]),
        ("Delete the project's managed identity", "managed-identity", ["The identity you created in failover step 2"]),
        ("Delete the 3 state resources", "storage", ["If this is the last project referencing them", "! Permanently deletes all state created during failover: no recovery, no merge"]),
        ("Point clients back", "apim", ["Original project FQDN and original agent IDs"]),
    ]
    bcards = [Card(cw, t, bl, theme="blue", icon=ic, title_size=19, body_size=15, icon_size=34) for t, ic, bl in back]
    r, bb2 = row(cv, 0, yb, bcards, gap=40)
    for i, c in enumerate(bcards):
        numbered(cv, c.x - 2, c.y - 2, i + 1, theme="blue", d=34, size=19)
        if i:
            connect(cv, bcards[i - 1], c, color="#1971c2", sw=3)
    rx = bcards[-1].right + 40
    res = Note(W - rx, "RTO: 10 or more minutes per project.\nRPO: state is exactly as it existed before failover; no cross-region state transfer; standby-region state is permanently lost.",
               kind="key", title="Result (as documented)", size=15)
    res.place(cv, rx, yb, h=bb2 - yb)

    # --- why multi-region data does not help + dependency outages
    yd = bb2 + 60
    q4 = (W - 3 * 40) / 4
    with cv.panel(0, yd, title="Why multi-region Cosmos DB / Storage doesn't help", theme="red", style="dotted", pad=22, title_size=21,
                  w=q4, fill="none") as why:
        cw2 = (q4 - 44 - 60) / 2
        c1 = Cylinder(cw2, 150, "Cosmos DB (primary)", theme="cyan", sub="keyed to project GUID-A", size=17, sub_size=14).place(cv, why.ix, why.iy)
        c2 = Cylinder(cw2, 150, "Cosmos DB (standby)", theme="cyan", sub="keyed to new project GUID-B", size=17, sub_size=14).place(cv, why.ix + cw2 + 60, why.iy)
        mx, my = why.ix + cw2 + 30, why.iy + 75
        cv.line((mx - 14, my - 14), (mx + 14, my + 14), stroke="#e03131", sw=4)
        cv.line((mx - 14, my + 14), (mx + 14, my - 14), stroke="#e03131", sw=4)
        txt = cv.text(why.ix, why.iy + 166, wrap(
            "enterprise_memory partitions by a globally unique ID per project instance, so multi-region writes don't prevent data loss on failback. Use a new temporary Cosmos DB during failover. Storage behaves the same way.",
            q4 - 44, 14), size=14, color=INK)
    dep_cosmos = FootCard(q4, "Cosmos DB account: regional outage", [
        "All projects using that enterprise_memory = complete outage; data-plane APIs error; portal agent experience unavailable",
        "Normally wait: the Cosmos DB team starts a service-managed failover itself - don't self-direct",
        "Business-critical? Forced failover to your failover region: loses writes not yet replicated",
        "! Docs disagree on timing: the Cosmos DB reliability page says declaring an outage can take 1 h or more and recommends a forced failover",
    ], rto="30+ min once the team (or you) triggers failover", rp="Up to 15 min of data may be lost: agents and threads created or updated just before the outage",
        sev=AMBER, theme="cyan", icon="cosmos", src=[("Platform outage recovery", DRP), ("Reliability in Cosmos DB", COSREL)])
    dep_search = FootCard(q4, "AI Search: regional outage", [
        "Agents with file knowledge error; recalling uploaded files and adding files error; agents without file knowledge mostly unaffected",
        "Recovery: none - wait, and degrade gracefully (no uploads)",
        "Business-critical alternative: destructive reset + a new Search in the failover region (complete data loss; repeat when the primary returns)",
        "! 'We don't advise' it unless users tolerate thread loss and agents can rehydrate file knowledge",
    ], rto="Indeterminate", rp="State preserved up to the outage; in-flight operations near it might not persist",
        sev=GREEN, theme="teal", icon="ai-search", src=[("Platform outage recovery", DRP)])
    dep_storage = FootCard(q4, "Storage: regional outage and failback", [
        "Can't create agents with file knowledge; adding files fails; others mostly fine - but a Storage outage often hits other services too",
        "Decide: wait, or failover. Get-AzStorageAccount -IncludeGeoReplicationStats, then Invoke-AzStorageAccountFailover -Force -AsJob (customer-managed, unplanned)",
        "Failback: follow the unplanned failback process; pause traffic to the Agent Service data endpoints 10 min before, ideally in a planned window",
    ], rto="20+ min failover; 10+ min failback", rp="About 15 min before the outage (about 10 min before failback): expect some data loss",
        sev=AMBER, theme="cyan", icon="storage", src=[("Platform outage recovery", DRP), ("Reliability in Blob Storage", STGREL)])
    hh = max(why.h, dep_cosmos.h, dep_search.h, dep_storage.h)
    dep_cosmos.place(cv, q4 + 40, yd, h=hh)
    dep_search.place(cv, 2 * (q4 + 40), yd, h=hh)
    dep_storage.place(cv, 3 * (q4 + 40), yd, h=hh)
    return yd + hh


# ---------------------------------------------------------------------------------------------- 5. playbook B
def ladder_row(cv: Canvas, y: float, items, *, dh: float = 130, dw: float = 340, gap: float = 40):
    """Decision diamonds above scenario cards. items: (question, theme, card). Returns (diamonds, cards, bottom)."""
    q4 = (W - 3 * gap) / 4
    diamonds, cards = [], []
    cards_h = max(c.h for _, _, c in items)
    cy = y + dh + 62
    for i, (q, th, card) in enumerate(items):
        x = i * (q4 + gap)
        d = Box(dw, q, shape="diamond", theme=th, h=dh, size=18).place(cv, x + (q4 - dw) / 2, y)
        card.place(cv, x, cy, h=cards_h)
        connect(cv, d, card, a_side="bottom", b_side="top", color=INK, sw=2)
        cv.text(d.cx + 12, d.bottom + 12, "yes", size=16)
        diamonds.append(d)
        cards.append(card)
    for a, b in zip(diamonds, diamonds[1:]):
        arrow(cv, [(a.right + 6, a.cy), (b.x - 6, a.cy)], color=INK, sw=2)
        cv.text((a.right + b.x) / 2 - 10, a.cy - 24, "no", size=16)
    return diamonds, cards, cy + cards_h


def playbook_b(cv: Canvas, y: float) -> float:
    q4 = (W - 3 * 40) / 4
    r1 = [
        ("Foundry account deleted?", "blue", FootCard(q4, "Foundry account deleted", [
            "1. Don't purge the account: a purge adds steps that aren't documented",
            "2. Within 48 h use the recover-account feature: az resource create ... --properties {restore: true}, or New-AzResource ... -ApiVersion 2026-03-01 (as of 2026-11-03). After 48 h an account can't be recovered",
            "3. Recreate the 3 private endpoints: account recovery doesn't restore them",
            "4. Recreate each project + capability settings from IaC, starting with the former default project: same name, same Cosmos DB / AI Search / Storage, same user-assigned identity (or re-enable SMI + redo role assignments)",
            "5. Redeploy agents (new IDs), restore project role assignments, update clients, reapply the delete lock",
            "! Old agent data is orphaned: 'can't be recovered through any supported action'",
        ], rto="30+ min", rp="Complete state loss for all projects in the account", sev=RED, theme="blue", icon="foundry",
            src=[("Resource and data loss recovery", DRO), ("Recover or purge deleted resources", RECOVER)])),
        ("Foundry project deleted?", "blue", FootCard(q4, "Foundry project deleted", [
            "1. Recreate the project + capability settings from IaC: same name, same dependencies, same user-assigned identity (or re-enable SMI; remove orphaned role assignments)",
            "2. Redeploy agents (definitions, knowledge files, tools): new agents, new IDs, no access to prior threads or files",
            "3. Apply the delete lock on the Foundry account",
            "Clients keep the same project name or FQDN pattern but must update stored agent IDs",
            "! Even with the same Cosmos DB, Search and Storage, lingering data 'isn't reused and is unreachable'",
        ], rto="Minutes", rp="Total loss of thread text and uploaded files for every agent in the project", sev=RED, theme="blue", icon="foundry",
            src=[("Resource and data loss recovery", DRO)])),
        ("Agent deleted?", "green", FootCard(q4, "Production agent deleted", [
            "1. Redeploy the agent (definition, knowledge files, tool connections) from source control: a new agent with a new ID",
            "2. Update clients to the new agent ID and resume on existing threads",
            "+ Other agents and existing threads (including ones the agent created) are unaffected",
        ], rto="Minutes", rp="State preserved up to deletion; in-flight operations at that moment might not persist", sev=GREEN, theme="green", icon="agent",
            src=[("Resource and data loss recovery", DRO)])),
        ("Thread deleted?", "green", FootCard(q4, "Production thread deleted", [
            "! No supported recovery capability",
            "Cosmos DB PITR lets you recover data to a different account, not the same account",
            "Directly recreating the thread's records in enterprise_memory isn't supported",
            "Previously indexed files from the thread are orphaned",
            "With Purview integration you can answer eDiscovery requests from Purview's copy; it doesn't restore the thread and may lag (ingestion delay)",
        ], rto="Not recoverable", rp="All thread state is destroyed", sev=RED, theme="green", icon="agent",
            src=[("Resource and data loss recovery", DRO)])),
    ]
    d1s, c1s, b1 = ladder_row(cv, y, r1)

    y2 = b1 + 90
    r2 = [
        ("Cosmos DB account deleted?", "cyan", FootCard(q4, "Cosmos DB account deleted", [
            "1. Restore the account - don't redeploy from IaC: portal, az cosmosdb restore or Restore-AzCosmosDBAccount, to the exact same resource group and account name, latest restore point (nominal fee)",
            "2. Reapply the delete lock; restore the diagnostics configuration",
            "3. Redeploy the projects' role assignments with IaC: the restore doesn't restore them",
            "! The name is released when you delete: act quickly. If another customer claims it, you lose the data and need a destructive reset",
        ], rto="10+ min", rp="State preserved up to account deletion; in-flight operations might not persist", sev=GREEN, theme="cyan", icon="cosmos",
            src=[("Resource and data loss recovery", DRO), ("Restore a Cosmos DB account", COSRESTORE)])),
        ("Database or container deleted, or data corrupted?", "cyan", FootCard(q4, "enterprise_memory database or container", [
            "Deleted database: in-account point-in-time restore of enterprise_memory (az cosmosdb sql database restore); role assignments are preserved",
            "Deleted container: in-account PITR of the container (az cosmosdb sql container restore); role assignments are preserved",
            "Choose the latest restore point (nominal fee), then reapply the delete lock",
            "! Corrupted data inside a container: generally no recovery. PITR 'only supports recovery from container, database, or account deletes'. Lost thread: see thread deleted. Lost agent: redeploy it",
        ], rto="10+ min if deleted; situational if corrupted", rp="Deleted: preserved up to deletion. Corrupted: total loss for the affected entities", sev=AMBER,
            theme="cyan", icon="cosmos", src=[("Resource and data loss recovery", DRO)])),
        ("AI Search service or index deleted?", "teal", FootCard(q4, "AI Search service or index deleted", [
            "Service: 1. IaC-deploy a new Search + private endpoints with the exact same resource group and name; 2. redeploy role assignments + diagnostics; 3. reapply the lock; 4. delete all agents that used file knowledge and redeploy them (new IDs, new indexes); 5. update clients",
            "Index: agent-knowledge index - delete and redeploy those agents (minutes). Thread-upload index - no recovery",
            "! Names are released on delete: act quickly or you need a destructive reset",
            "Mixing runtime and durable knowledge in one instance adds a rehydration of your durable store",
        ], rto="20+ min for the service; minutes for an index", rp="Thread state lost; agent knowledge rebuilt", sev=AMBER, theme="teal", icon="ai-search",
            src=[("Resource and data loss recovery", DRO), ("Reliability in AI Search", SRCHREL)])),
        ("Storage account deleted?", "cyan", FootCard(q4, "Storage account deleted", [
            "1. If soft delete is enabled: az storage account recover within the retention period",
            "2. Otherwise IaC-deploy a new account with the exact same resource group and name; restore diagnostics",
            "3. Reapply the delete lock; redeploy role assignments (account recovery doesn't restore them)",
            "4. Delete all agents that used file knowledge and redeploy them (new IDs, new blob data from source control); update clients",
            "! The name is released on delete: act quickly",
        ], rto="20+ min", rp="Thread state lost (files of existing threads unrecoverable); agent knowledge rebuilt from source control", sev=AMBER, theme="cyan",
            icon="storage", src=[("Resource and data loss recovery", DRO)])),
    ]
    d2s, c2s, b2 = ladder_row(cv, y2, r2)
    # wrap-around "no" connector: row 1 -> row 2
    xr = W + 26
    ygap = b1 + 40
    arrow(cv, [(d1s[3].right + 6, d1s[3].cy), (xr, d1s[3].cy), (xr, ygap), (d2s[0].cx, ygap), (d2s[0].cx, d2s[0].y - 6)], color=INK, sw=2)
    cv.text(d1s[3].right + 24, d1s[3].cy - 24, "no", size=16)
    cv.text(W - 560, ygap + 6, "none of these: check the state-store layer", size=15, color=MUTED)

    # --- last resort
    y3 = b2 + 90
    qd = Box(430, "Name claimed by someone else, or nothing above fits?", shape="diamond", theme="red", h=170, size=18).place(cv, 0, y3 + 30)
    xr2 = W + 26
    ygap2 = b2 + 44
    arrow(cv, [(d2s[3].right + 6, d2s[3].cy), (xr2, d2s[3].cy), (xr2, ygap2), (qd.cx, ygap2), (qd.cx, qd.y - 6)], color=INK, sw=2)
    cv.text(d2s[3].right + 24, d2s[3].cy - 24, "no", size=16)
    px = qd.right + 90
    pw = W - px
    with cv.panel(px, y3, title="Destructive reset of one project's agent state - LAST RESORT", theme="red", style="solid", fill="soft", pad=22,
                  title_size=26, sub=wrap("A fresh start that restores functionality but permanently orphans all agents, threads and related state: they become unretrievable through any Agent Service API call. "
                                          "It provides no data recovery point.", pw - 44, 15), sub_size=15, w=pw) as rp_:
        sw_ = (pw - 44 - 5 * 22) / 6
        steps = [
            ("Remove the delete lock", "Take the delete lock off the Foundry account"),
            ("Delete the capability host", "REST: Project Capability Hosts - Delete, for the project you reset. Orphans agent definitions, thread text and files, agent-level file knowledge"),
            ("Reapply the lock", "Put the delete lock back on the Foundry account"),
            ("Recreate the capability host", "IaC or Project Capability Hosts - Create, after confirming Cosmos DB, AI Search and Storage exist and the project's identity has the same roles as before"),
            ("Redeploy agents", "From source control: new agents, new IDs, no access to prior threads or data"),
        ]
        cards = [Card(sw_, t, [("para", b, 0)], theme="red", title_size=17, body_size=14, fill="soft", pad=12) for t, b in steps]
        cards.append(FootCard(sw_, "Result", [("para", "Lingering data from the previous association is never reused.", 0)], rto="Minutes",
                              rp="Complete state loss (single project)", sev=RED, theme="red", title_size=17, body_size=14, fill="hatch", pad=12, foot_size=14))
        _, bb = row(cv, rp_.ix, rp_.iy, cards, gap=22)
        for i, c in enumerate(cards[:5]):
            numbered(cv, c.x - 2, c.y - 2, i + 1, theme="red", d=30, size=17)
            connect(cv, c, cards[i + 1], color="#c92a2a", sw=2.5)
        cv.text(rp_.ix, bb + 12, wrap(
            "The legacy direct capability-host API remains available for backward compatibility and uses the project's managed identity during provisioning. "
            "This is the supported way out when a Cosmos DB, AI Search or Storage name was claimed by another customer: reset with a new dependency account.",
            pw - 44, 14), size=14, color=MUTED)
    return max(rp_.bottom, qd.bottom)


# ---------------------------------------------------------------------------------------------- 6. configure before
class NumCard(Rect2):
    """Card with numbered steps (numbers are drawn as markers, not text)."""

    def __init__(self, w: float, title: str, items: list[str], *, theme: str = "green", icon: str | None = None,
                 src=(), size: int = 15, title_size: int = 20, pad: int = 16):
        self.th = get_theme(theme)
        self.w, self.title, self.icon, self.src = w, title, icon, list(src)
        self.items, self.size, self.title_size, self.pad = items, size, title_size, pad
        inner = (w - 2 * pad) * SAFETY - 44
        self.lines = [metrics.wrap_text(t, inner, size) for t in items]
        lr = metrics.line_ratio()
        self.t_lines = metrics.wrap_text(title, (w - 2 * pad - (46 if icon else 0)) * SAFETY, title_size)
        head = max(len(self.t_lines) * title_size * lr, 36 if icon else 0)
        h = pad + head + 12
        self.item_h = []
        for ln in self.lines:
            ih = max(len(ln) * size * lr, 30)
            self.item_h.append(ih)
            h += ih + 10
        self.src_lines = []
        if self.src:
            h += 2
            for label, url in self.src:
                self.src_lines.append((f"Learn: {label}", url, h))
                h += 12 * lr + 2
        self.head = head
        self.h = h + pad - 8
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv: Canvas, x: float, y: float, h: float | None = None) -> "NumCard":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, 36)
            cv.text(x + pad + (46 if self.icon else 0), y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            cy = y + pad + self.head + 12
            for i, (ln, ih) in enumerate(zip(self.lines, self.item_h)):
                numbered(cv, x + pad + 15, cy + 15, i + 1, theme=th.name, d=30, size=17)
                cv.text(x + pad + 44, cy + (ih - len(ln) * self.size * metrics.line_ratio()) / 2, "\n".join(ln), size=self.size, color=INK)
                cy += ih + 10
            for txt, url, off in self.src_lines:
                cv.text(x + pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register(f"numcard:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


def config_section(cv: Canvas, y: float) -> float:
    q4 = (W - 3 * 40) / 4
    chk = NumCard(q4, "DR readiness checklist", [
        "Choose a recovery strategy per project (for example warm standby + reconstruction) and document your recovery objectives",
        "Configure baseline protections and recovery features on the dependencies (table)",
        "Treat agent definitions as code: definitions, knowledge assets and tool bindings in source control",
        "Automate redeployment, including client updates for new agent IDs (REST API or Azure AI Projects SDK); version the IaC for the state resources",
        "Practice recovery with periodic drills so operators can run the steps under time pressure",
        "Set Azure Monitor alerts on Cosmos DB, AI Search and Storage to catch degradation early",
    ], theme="green", icon="agent", src=[("Agent Service disaster recovery", DR0)])
    tbl = Table([("Resource", 190), ("Configure before the incident", 560), ("Why", 410)], [
        ["Foundry account", "Explicit connection to Microsoft Purview", "Compliance data continuity (eDiscovery) after thread data is lost"],
        ["Foundry project", "User-assigned managed identity, not system-assigned", "Restores access to dependencies without reapplying role assignments"],
        ["Agent Service", "Standard agent deployment mode", "Basic mode has 'almost no recovery options for resource loss'"],
        ["Cosmos DB", "Continuous backup with point-in-time restore (7-day, 30-day or 35-day tier). Enable it BEFORE any incident", "Recover a deleted enterprise_memory database, container or account"],
        ["Cosmos DB", "Unique, organization-specific name, e.g. contoso-agents-cosmosdb", "A restore recreates the original name; if it's taken, the restore fails"],
        ["Cosmos DB", "Read replication to the failover region + service-managed failover (az cosmosdb update --locations ... --enable-automatic-failover true)", "Lets Cosmos DB switch the write region in a prolonged regional outage"],
        ["AI Search", "Unique, organization-specific name, e.g. contoso-agents-search", "A restore recreates the original name; if it's taken, the restore fails"],
        ["Storage", "Geo-zone-redundant storage (GZRS)", "Allows customer-managed failover to a predetermined region"],
        ["Account, Cosmos DB, Search, Storage", "CanNotDelete locks + Azure Policy denyAction. Owner needed to create or remove locks", "Blocks resource-level deletes; doesn't protect agents, threads, indexes, blobs or data"],
        ["All dependencies", "Dedicated Cosmos DB, Search and Storage per workload (single responsibility)", "Smaller blast radius; per-workload recovery decisions"],
    ], w=1440, theme="cyan", size=14, head_size=15, title="Settings that make recovery possible", title_size=22, first_col_theme="cyan")
    red = Card(q4, "Redundancy settings per store", [
        "Cosmos DB: zone redundancy + continuous backup + read replication with service-managed failover",
        "AI Search: Basic tier or higher with >= 2 replicas for zone redundancy (placement is attempted, not guaranteed); >= 3 replicas for the read-write SLA; over-provision so a zone loss doesn't degrade",
        "Storage: GZRS per the HA and DR pages. Architecture Center: ZRS minimum, GZRS for more; 'If you use only ZRS, contact Microsoft support to restore data' (may extend RTO)",
        "No file uploads and no static-file knowledge? You 'might not need a DR plan' for AI Search or blobs",
        "! Zone redundancy doesn't protect against a full regional outage or human error",
    ], theme="teal", icon="regions", src=[("High availability", HA), ("Baseline chat architecture", ARCH)])
    rbac = Card(q4, "Roles and tooling for DR work", [
        "Contributor or Owner on the resource group; Owner to create or remove locks (Contributor lacks Microsoft.Authorization/locks/write)",
        "Foundry Project Manager for managing projects; User Access Administrator to assign roles to managed identities",
        "Storage Account Contributor (Storage failover), Cosmos DB Account Contributor (restore), Search Service Contributor, Storage Blob Data Contributor",
        "Azure CLI 2.86.0 or later, or Azure PowerShell, plus IaC (Bicep, ARM or Terraform) for the state resources - as of 2026-11-03",
        "Foundry User / Owner / Account Owner / Project Manager were Azure AI User / ...: IDs and permissions unchanged",
    ], theme="red", icon="managed-identity", src=[("Platform outage recovery", DRP), ("Resource and data loss recovery", DRO)])
    chk.place(cv, 0, y)
    tbl.place(cv, q4 + 40, y)
    col(cv, q4 + 40 + 1440 + 40, y, [red, rbac], gap=24)
    b = max(chk.bottom, tbl.bottom, rbac.bottom)
    cite(cv, q4 + 40, tbl.bottom + 8, [("High availability and resiliency", HA)])
    return max(b, tbl.bottom + 30)


# ---------------------------------------------------------------------------------------------- 7. pitfalls + conflicts
def pitfalls(cv: Canvas, y: float) -> float:
    n3 = (W - 2 * 40) / 3
    notes = [
        Note(n3, "Collections, containers and indexes the service creates are undocumented and subject to change without notice. Direct access can break the agent service or result in data loss. "
                 "Use the data-plane APIs, even for right-to-be-forgotten requests.", kind="gotcha", title="Never touch system-managed data", src=[("Baseline chat architecture", ARCH)]),
        Note(n3, "Cosmos DB, AI Search and Storage names are released when you delete the resource. Act quickly: if another customer claims the name, you need a destructive reset with a new dependency account.",
             kind="gotcha", title="Names are released on delete", src=[("Resource and data loss recovery", DRO)]),
        Note(n3, "Account, AI Search and Storage restores don't restore role assignments (database and container in-account restores do). Account recovery doesn't restore private endpoints or projects. "
                 "Use a user-assigned identity and IaC.", kind="gotcha", title="Restores don't restore access", src=[("Resource and data loss recovery", DRO)]),
        Note(n3, "Continuous backup can't be applied retroactively. The restore target account name must be free and the target resource group must already exist.",
             kind="warn", title="PITR must exist before the incident", src=[("High availability", HA)]),
        Note(n3, "If your own stores reference conversation or agent IDs, restoring only a subset of dependencies can leave orphaned or inconsistent data. "
                 "Build a recovery runbook for both application-owned and agent-owned state before production.", kind="warn", title="Recover transactionally", src=[("Baseline chat architecture", ARCH)]),
        Note(n3, "Every redeploy mints new agent IDs. Keep IDs behind a gateway or config. Existing threads work with new agent IDs only when the thread store survived "
                 "(agent deleted, Search lost).", kind="warn", title="New IDs, old threads", src=[("Resource and data loss recovery", DRO)]),
    ]
    _, b = grid(cv, 0, y, notes, 3, gap_x=40, gap_y=24)
    return b


def conflicts(cv: Canvas, y: float) -> float:
    n3 = (W - 2 * 40) / 3
    items = [
        ("Cosmos DB failover timing", [
            "Agent DR pages: the Cosmos DB team triggers a service-managed failover; fail-back 'three or more days later'; RTO 30+ min once triggered; up to 15 min of data loss",
            "Cosmos DB reliability page: declaring an outage 'can take ... one hour or more'; forced failover is recommended for faster recovery",
        ], [("Reliability in Cosmos DB", COSREL)]),
        ("Cosmos DB throughput", [
            "Standard setup 'provisions five containers, each requiring 1000 RU/s' (account >= 3000 RU/s)",
            "Troubleshooting on the same page: '3000 RU/s (1000 RU/s per container x 3 containers)'; multiply by the number of projects",
        ], [("Standard agent setup", STD)]),
        ("Cosmos DB restore target", [
            "Architecture Center: 'Always restore to the same account and database'",
            "HA page example restores to a new account name, then you repoint the Agent Service connection. Deleted-account scenario: restore to the same name and resource group",
        ], [("Baseline chat architecture", ARCH), ("High availability", HA)]),
        ("AI Search recovery", [
            "DR series: rebuild from IaC and redeploy agents with file knowledge",
            "Architecture Center: AI Search 'lacks built-in restore capabilities'; contact Microsoft Support for index restoration options. Treat rebuild as the supported path",
        ], [("Baseline chat architecture", ARCH)]),
        ("Storage geo-redundancy", [
            "HA page table: 'Foundry projects don't support default storage account failover using GRS/GZRS/RA-GRS/RA-GZRS'",
            "Agent Service DR pages: use GZRS + customer-managed failover for the agent-state storage account",
        ], [("High availability", HA)]),
        ("Vocabulary and containers", [
            "DR pages speak of threads, agents and the enterprise_memory database",
            "The new runtime uses agent-definitions-v1 and run-state-v1 (Responses and conversations); the docs don't map each recovery procedure onto them",
        ], [("Standard agent setup", STD)]),
    ]
    cards = [Card(n3, t, bl, theme="gray", badge="docs disagree", title_size=19, body_size=15, src=s) for t, bl, s in items]
    _, b = grid(cv, 0, y, cards, 3, gap_x=40, gap_y=24)
    return b


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Agent Service disaster recovery",
                                "Foundry Agent Service, Standard setup: what lives where, who recovers what, and why recovery = reconstruction, not restoration  |  as of 2026-11-03",
                                icon="foundry", w=W)
    y = bottom + 24
    cv.text(0, y, "Owner", size=16, color=MUTED)
    lg = legend(cv, 70, y, [("Microsoft", "blue"), ("Shared", "violet"), ("You", "orange")])
    x2 = 70 + lg.w + 50
    t = cv.text(x2, y, "Recovery point (our colour reading of the documented outcome)", size=16, color=MUTED)
    legend(cv, x2 + t.w + 20, y, [("state preserved", "green"), ("partial loss", "yellow"), ("total loss or not recoverable", "red")])
    y += 56
    y = headline(cv, y) + 64
    y = sec(cv, y, "1", "Where state lives: the Agent Service anatomy",
            "Standard setup: you bring Cosmos DB, AI Search and Storage. One project is the recovery unit; data is partitioned per project.")
    y = anatomy(cv, y) + 60
    y = tables(cv, y) + 60
    y = sec(cv, y, "2", "Incident map: what happens in each scenario",
            "Recovery time (RTO) and recovery point as documented. Green = state preserved, amber = partial, red = total loss.")
    y = incident_map(cv, y) + 64
    y = sec(cv, y, "3", "Playbook A: platform or regional outage",
            "Warm standby, failover and failback per project. Recovery restores functionality, not state.")
    y = playbook_a(cv, y) + 64
    y = sec(cv, y, "4", "Playbook B: resource and data loss (human or automation error)",
            "Walk the ladder from the Foundry layer down to the state stores. After every recovery, invoke an agent and check that new threads and existing history work.")
    y = playbook_b(cv, y) + 64
    y = sec(cv, y, "5", "Configure before the incident",
            "Recovery steps assume these settings were already in place; several can't be applied retroactively.")
    y = config_section(cv, y) + 64
    y = sec(cv, y, "6", "Pitfalls and where the docs disagree",
            "Pitfalls come from the three DR pages, the HA page and the Architecture Center baseline. Conflicts are flagged, not resolved.")
    y = pitfalls(cv, y) + 40
    y = conflicts(cv, y) + 64
    sources(cv, 0, y, [
        ("Agent Service disaster recovery (overview)", DR0),
        ("Agent Service platform outage recovery", DRP),
        ("Agent Service resource and data loss recovery", DRO),
        ("High availability and resiliency", HA),
        ("Set up standard agent resources", STD),
        ("Capability hosts", CAP),
        ("Set up your environment (Basic / Standard / Standard + BYO VNet)", ENV),
        ("Agent Service limits, quotas and regional support", LIM),
        ("Baseline Microsoft Foundry chat reference architecture", ARCH),
        ("Reliability in Azure Cosmos DB", COSREL),
        ("Reliability in Azure AI Search", SRCHREL),
        ("Reliability in Azure Blob Storage", STGREL),
        ("Recover or purge deleted Foundry resources", RECOVER),
        ("Restore an Azure Cosmos DB account (continuous backup)", COSRESTORE),
    ], w=W, cols=3)
