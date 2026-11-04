"""Foundry high availability and resiliency - what is built in, what is yours (BCDR overview)."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="bcdr-overview", title="Foundry high availability and resiliency", section="4", order=1,
    description="The layered resilience stack: what Microsoft builds in, what you own, availability zones, regional failure, deployment-type resiliency, SLAs and what you must replicate yourself.",
    tags=["bcdr", "availability-zones", "regional-failover", "deployment-types", "resiliency"],
)

W = 2800
HA = learn("how-to/high-availability-resiliency")
DEP = learn("foundry-models/concepts/deployment-types")
PTU = learn("openai/concepts/provisioned-throughput")
DR = learn("how-to/agent-service-disaster-recovery")
HEALTH = learn("how-to/stay-informed-service-health")
RECOVER = learn("azure/ai-services/recover-purge-resources", base="")
ARCH = learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")
GW = learn("azure/architecture/ai-ml/guide/azure-openai-gateway-multi-backend", base="")
SEARCH_REL = learn("azure/reliability/reliability-ai-search", base="")
COSMOS_REL = learn("azure/reliability/reliability-cosmos-db-nosql", base="")
KV_DR = learn("azure/key-vault/general/disaster-recovery-guidance", base="")
APIM_REL = learn("azure/reliability/reliability-api-management", base="")
FT_CLASSIC = learn("azure/foundry-classic/how-to/fine-tune-serverless", base="")
FT_COPY = "https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/fine-tuning#fine-tuning---copy-checkpoint"
FAQ = learn("azure/ai-foundry/openai/faq", base="")
SLA_DOC = "https://www.microsoft.com/licensing/docs/view/Service-Level-Agreements-SLA-for-Online-Services"

OWNERS = {"ms": ("Microsoft", "blue"), "shared": ("Shared", "violet"), "you": ("You", "orange")}


# ---------------------------------------------------------------------------------------------- helpers
def wrap(text: str, width: float, size: float) -> str:
    return "\n".join(wrap_text(text, width, size))


def owner_dot(cv: Canvas, cx: float, cy: float, who: str) -> None:
    th = THEMES[OWNERS[who][1]]
    cv.ellipse(cx - 15, cy - 15, 30, 30, stroke=th.stroke, fill=th.stroke, style="solid", sw=2, rough=0)


def tag(cv: Canvas, x: float, y: float, text: str, th_name: str, size: int = 14) -> tuple[float, float]:
    """Small label pill drawn without registering a block (safe to overlay on boxes)."""
    th = THEMES[th_name]
    tw, thh = text_size(text, size)
    cv.rect(x, y, tw + 18, thh + 8, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0)
    cv.text(x + 9, y + 4, text, size=size, color=th.deep)
    return tw + 18, thh + 8


def ghost(cv: Canvas, x: float, y: float, w: float, h: float, label: str, th_name: str = "gray", size: int = 14) -> None:
    th = THEMES[th_name]
    cv.rect(x, y, w, h, stroke=th.stroke, fill="transparent", sw=2, dash="dashed")
    lab = wrap(label, w - 20, size)
    tw, thh = text_size(lab, size)
    cv.text(x + (w - tw) / 2, y + (h - thh) / 2, lab, size=size, color=th.deep, align="center", w=tw)


def cross(cv: Canvas, x: float, y: float, w: float, h: float, color: str = "#e03131", sw: int = 5) -> None:
    cv.line((x, y), (x + w, y + h), stroke=color, sw=sw)
    cv.line((x, y + h), (x + w, y), stroke=color, sw=sw)


def src_line(cv: Canvas, x: float, y: float, items: list[tuple[str, str]]) -> float:
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=12, color=LINK, link=url)
        cx += t.w + 24
    return y + 16


# ---------------------------------------------------------------------------------------------- 0. summary
def summary_strip(cv: Canvas, y: float) -> float:
    cw = (W - 4 * 36) / 5
    cards = [
        Card(cw, "No automatic cross-region failover", [
            "= Foundry itself doesn't provide automatic failover or disaster recovery.",
            "= For multiregion you create Foundry resources and other infrastructure in two regions, and switch to the other region when a regional outage occurs.",
        ], theme="red", icon="regions", src=[("High availability and resiliency", HA)]),
        Card(cw, "Zones are not regions", [
            "= Zone redundant configurations don't protect against full regional outages or human or automation errors.",
            "= Microsoft-hosted Agent Service components are zone redundant. Zone redundancy for Cosmos DB, AI Search and Storage is yours to configure.",
        ], theme="indigo", icon="subnet", src=[("High availability and resiliency", HA)]),
        Card(cw, "Shared responsibility", [
            "= Microsoft runs the control plane and the agent runtime infrastructure.",
            "= You own the durability of the stateful dependencies (Cosmos DB, AI Search, Storage) in Standard agent mode.",
        ], theme="grape", icon="groups", src=[("High availability and resiliency", HA)]),
        Card(cw, "Recovery = reconstruction", [
            "= Agent Service doesn't replicate state, create backups or support point-in-time restore.",
            "= Rebuilt agents get new agent IDs; thread history and uploaded files don't come back.",
        ], theme="green", icon="agent", src=[("Agent Service disaster recovery", DR)]),
        Card(cw, "SLAs depend on deployment type", [
            "= Availability SLA for all resources; latency SLA for provisioned-managed deployments (Learn FAQ).",
            "= Standard types are best-effort, Developer has no SLA, preview has no SLA. No percentages are printed here.",
        ], theme="yellow", icon="service-health", src=[("Deployment types", DEP)]),
    ]
    _, bottom = row(cv, 0, y, cards, gap=36)
    return bottom


# ---------------------------------------------------------------------------------------------- 1. resilience stack
LAYERS = [  # top -> bottom; (number, title, theme, icon, text, owners)
    (8, "App and operations", "gray", "app",
     "Config-driven endpoint switch (for example Azure App Configuration), agents as code, IaC for both regions, Service Health and Resource Health alerts, quarterly failover drills.",
     ["you"]),
    (7, "Network and identity", "indigo", "vnet",
     "Private endpoints and Private DNS per region, VPN or ExpressRoute resilience, user-assigned managed identities, role assignments in both regions.",
     ["you"]),
    (6, "Gateway and global traffic", "indigo", "apim",
     "Generative AI Gateway (for example API Management multi-region) plus Azure Front Door (public) or DNS record toggling (private networking).",
     ["you"]),
    (5, "State and knowledge dependencies", "cyan", "cosmos",
     "Cosmos DB, AI Search, Storage (Standard agent mode), Key Vault, ACR, Application Insights, Logic Apps / Functions / Event Grid, Purview, SharePoint and custom APIs: 'You own their high availability configuration.'",
     ["you"]),
    (4, "Agent Service runtime", "green", "agent",
     "'The Microsoft-hosted components of the Agent Service are zone redundant.' No built-in DR: it 'doesn't replicate state, create backups, or support point-in-time restore.'",
     ["shared"]),
    (3, "Model deployments", "blue", "openai",
     "Global and Data Zone Standard can route inference across their permitted scope, but that routing 'doesn't replace application-level regional failover'. Provisioned = dedicated capacity + latency SLA. Spillover: PTU -> Standard, same Foundry resource only.",
     ["shared"]),
    (2, "Foundry resource and projects", "grape", "foundry",
     "Control plane and project metadata: regional, 'no customer action for zone configuration'. 'If a regional disaster occurs, you can't recover service data' (mostly metadata). Projects are geo-replicated 'by You': create them in each selected region.",
     ["ms", "you"]),
    (1, "Azure region and availability zones", "gray", "regions",
     "Zone failures are handled only by services configured for zone redundancy. 'Zone redundant configurations don't protect against full regional outages or human or automation errors.'",
     ["ms", "you"]),
]


def resilience_stack(cv: Canvas, y: float) -> float:
    cx0, cw = 56, 1330
    col_x = [cx0 + cw + 70, cx0 + cw + 170, cx0 + cw + 270]
    for key, cxm in zip(("ms", "shared", "you"), col_x):
        lab, thn = OWNERS[key]
        ch = Chip(lab, theme=thn, size=16)
        ch.place(cv, cxm - ch.w / 2, y)
    cv.text(cx0, y + 4, "Bottom-up: each layer sits on the one below it. Who operates it, according to the docs:", size=16, color=MUTED)
    top = y + 48
    cy = top
    cards = []
    for num, title, thn, icon, text, owners in LAYERS:
        c = Card(cw, title, ["= " + text], theme=thn, icon=icon, title_size=20, body_size=15, fill="hatch", icon_size=34)
        c.place(cv, cx0, cy)
        cards.append((c, num, thn, owners))
        cy += c.h + 12
    bottom = cy - 12
    for key, cxm in zip(("ms", "shared", "you"), col_x):
        th = THEMES[OWNERS[key][1]]
        cv.rect(cxm - 46, top, 92, bottom - top, stroke=th.stroke, fill=th.soft, style="solid", sw=1.5, dash="dotted")
    for c, num, thn, owners in cards:
        numbered(cv, 26, c.cy, num, theme=thn, d=34, size=19)
        for key in owners:
            owner_dot(cv, col_x[("ms", "shared", "you").index(key)], c.cy, key)
    return bottom


def ledger(cv: Canvas, x: float, y: float, w: float) -> float:
    built = Card(w, "Built in (Microsoft)", [
        "Foundry control plane and project metadata: regional platform infrastructure",
        "Microsoft-hosted Agent Service components are zone redundant",
        "Global and Data Zone deployments route inference inside their processing scope",
        "Provisioned deployments: dedicated capacity with a latency SLA",
        "Key Vault: automatic zone redundancy + async replication to the paired region; Microsoft-managed failover is best-effort, can be delayed, read-only after failover",
        "Soft-delete recovery: Foundry accounts within 48 h if not purged (Agent Service DR page); Key Vault soft delete",
    ], theme="blue", icon="foundry", src=[("High availability", HA), ("Agent Service DR", DR), ("Key Vault DR", KV_DR)])
    built.place(cv, x, y)
    yours = Card(w, "Yours to build and run", [
        "A second Foundry resource + projects + model deployments + connections in another region",
        "Quota in both regions: allocate full quota to primary and secondary",
        "Agent definitions as code, AI Search index rebuild, Cosmos DB and Storage redundancy and backup",
        "ACR geo-replication, Application Insights per region, private endpoints + Private DNS, role assignments",
        "Gateway + global load balancer, failover runbooks and drills",
    ], theme="orange", icon="user", src=[("High availability", HA)])
    yours.place(cv, x, built.bottom + 20)
    nsync = Note(w, "Foundry doesn't sync or recover artifacts or metadata between projects. Jobs running during an outage don't automatically transition to the secondary project: resubmit them. Resources shared with geo-replication enabled (Docker images in ACR, configured datastores, Key Vault) can be common to both projects.",
                 kind="gotcha", title="Explicitly NOT synced", src=[("High availability", HA)])
    nsync.place(cv, x, yours.bottom + 20)
    return nsync.bottom


# ---------------------------------------------------------------------------------------------- 2. zones + rings
ZONE_ROWS = [
    ("Microsoft-hosted Agent Service components", "Zone redundant. The agent runtime infrastructure is operated by Microsoft.",
     "green", "agent", "Microsoft", "blue"),
    ("Azure Cosmos DB account with zone redundancy", "Synchronous data replication across zones lowers the risk of data loss or downtime from a single-zone failure.",
     "cyan", "cosmos", "You configure", "orange"),
    ("Azure AI Search: replicas spread across zones", "Automatic with Basic tier or higher and 2+ replicas; placement is attempted, not guaranteed. The Architecture Center baseline says Standard tier or higher with 3+ replicas.",
     "teal", "ai-search", "You configure", "orange"),
    ("Azure Storage with ZRS or GZRS", "ZRS replicates across zones; GZRS combines zone and regional redundancy (customer-managed failover).",
     "cyan", "storage", "You configure", "orange"),
    ("Azure Key Vault", "Automatic zone redundancy when supported. You configure RBAC and purge protection.",
     "red", "key-vault", "Automatic", "blue"),
]


def zones_panel(cv: Canvas, x: float, y: float, w: float) -> float:
    pad, gap = 26, 16
    zw = (w - 2 * pad - 2 * gap) / 3
    full = 3 * zw + 2 * gap
    with cv.panel(x, y, w=w, title="Inside one Azure region that supports availability zones",
                  sub="What the docs say about zone redundancy, layer by layer", theme="indigo", style="dashed",
                  pad=pad, title_size=26, sub_size=15) as p:
        zy = p.iy + 2
        bh, bgap = 64, 8
        ZH = 44 + len(ZONE_ROWS) * (bh + bgap) + 8 + 80
        for i in range(3):
            zx = p.ix + i * (zw + gap)
            bad = i == 1
            th = THEMES["red" if bad else "indigo"]
            cv.rect(zx, zy, zw, ZH, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
            lab = f"Availability zone {i + 1}" + ("  (example: this zone fails)" if bad else "")
            cv.text(zx + 14, zy + 10, lab, size=17, color=th.deep)
        by = zy + 44
        for label, sub, thn, icon, who, wth in ZONE_ROWS:
            b = Box(full - 24, label, sub=wrap(sub, full - 330, 14), h=bh, theme=thn, icon=icon, icon_pos="left", icon_size=34,
                    size=17, sub_size=14, fill="solid")
            b.place(cv, p.ix + 12, by)
            tg_w, tg_h = text_size(who, 14)
            tag(cv, b.right - tg_w - 30, by + (b.h - tg_h - 8) / 2, who, wth)
            by += b.h + bgap
        dep = Box(zw - 24, "Your single-zone or non-redundant dependency", sub="for example a custom tool connection or an external data source", h=70,
                  theme="red", fill="soft", dash="dashed", size=15, sub_size=13)
        dep.place(cv, p.ix + zw + gap + 12, by + 6)
        cross(cv, dep.right - 44, dep.y + 8, 28, 28)
        for i in (0, 2):
            tag(cv, p.ix + i * (zw + gap) + 14, by + 28, "zone-redundant services keep serving", "green", 14)
        ty = zy + ZH + 12
        cv.text(p.ix, ty, wrap("Services configured for zone redundancy continue to operate when a zone fails. Services that aren't zone-redundant might experience interruptions. Any single-zone or nonredundant dependency can undermine the whole layer.", full, 15),
                size=15, color="#2b8a3e")
        ty += 52
        cv.text(p.ix, ty, "Regional layers: no customer zone controls", size=19, color="#364fc7")
        ty += 30
        rw = (full - 2 * gap) / 3
        regional = [
            Box(rw, "Foundry control plane + project metadata", sub=wrap("Regional. No customer action for zone configuration (HA page).", rw - 30, 14), theme="grape", icon="foundry", size=16, sub_size=14, fill="solid"),
            Box(rw, "Foundry portal, data plane APIs, Agent Service capability", sub=wrap("'Don't provide direct controls for zone redundancy' (Architecture Center).", rw - 30, 14), theme="green", icon="agent", size=16, sub_size=14, fill="solid"),
            Box(rw, "Standard model deployment", sub=wrap("'Operates in a single region and doesn't support availability zones'. For multi-datacenter availability use a Global or Data Zone deployment.", rw - 30, 14), theme="blue", icon="openai", size=16, sub_size=14, fill="solid"),
        ]
        hmax = max(b.h for b in regional)
        rx = p.ix
        for b in regional:
            b.place(cv, rx, ty, h=hmax)
            rx += rw + gap
        ty += hmax + 16
        n1 = Note(full / 2 - 8, "A full regional outage and human or automation errors (deleting or mis-configuring a resource) are not covered by zone redundancy.",
                  kind="gotcha", title="What zones do NOT cover", src=[("High availability", HA)])
        n2 = Note(full / 2 - 8, "The HA and DR pages don't state whether the Foundry resource itself or model deployments are zone redundant, beyond the statements above. Don't assume zone-redundant model deployments.",
                  kind="warn", title="Docs are silent here", src=[("Architecture Center baseline", ARCH)])
        hh = max(n1.h, n2.h)
        n1.place(cv, p.ix, ty, h=hh)
        n2.place(cv, p.ix + full / 2 + 8, ty, h=hh)
        ty += hh
        src_line(cv, p.ix, ty + 8, [("AI Search reliability", SEARCH_REL), ("Cosmos DB reliability", COSMOS_REL)])
    return p.bottom


def rings_panel(cv: Canvas, x: float, y: float, w: float) -> float:
    pad = 26
    iw = w - 2 * pad
    with cv.panel(x, y, w=w, title="Where inference may be processed", sub="The deployment type sets the scope. Data stored at rest stays in the designated Azure geography.",
                  theme="blue", style="dashed", pad=pad, title_size=26, sub_size=15) as p:
        with cv.panel(p.ix, p.iy, w=iw, title="Global", sub="Inference may be processed in any Azure region", theme="blue", fill="soft",
                      style="solid", pad=22, title_size=24, sub_size=15) as r1:
            c1 = ChipFlow(["Global Standard", "Global Provisioned", "Global Batch"], w=iw - 44, theme="blue", size=15)
            c1.place(cv, r1.ix, r1.iy)
            w2 = iw - 44
            with cv.panel(r1.ix, r1.iy + c1.h + 20, w=w2, title="Data Zone",
                          sub=wrap("Processed only inside the Microsoft-specified zone: US, EU or APAC (APAC per the deployment-types page). The EU zone follows the Azure EU Data Boundary; Microsoft can add regions without prior notice.", w2 - 44, 15),
                          theme="indigo", fill="soft", style="solid", pad=22, title_size=24, sub_size=15) as r2:
                c2 = ChipFlow(["Data Zone Standard", "Data Zone Provisioned", "Data Zone Batch"], w=w2 - 44, theme="indigo", size=15)
                c2.place(cv, r2.ix, r2.iy)
                w3 = w2 - 44
                with cv.panel(r2.ix, r2.iy + c2.h + 20, w=w3, title="Azure geography",
                              sub=wrap("Prompts and responses are processed within the customer-specified geography and might be processed between regions within it for operational purposes.", w3 - 44, 15),
                              theme="cyan", fill="soft", style="solid", pad=22, title_size=24, sub_size=15) as r3:
                    c3 = ChipFlow(["Standard", "Regional Provisioned"], w=w3 - 44, theme="cyan", size=15)
                    c3.place(cv, r3.ix, r3.iy)
                    pin = Box(w3 - 44, "Data at rest: the designated Azure geography (all deployment types)", theme="teal", icon="storage",
                              icon_pos="left", icon_size=28, size=15, fill="solid", h=52)
                    pin.place(cv, r3.ix, r3.iy + c3.h + 16)
        dev = Box(iw, "Developer (DeveloperTier)", sub=wrap("Any Azure region, no residency guarantee, no SLA. Fixed 24-hour lifetime; fine-tuned model evaluation only.", iw - 40, 14),
                  theme="yellow", fill="soft", size=17, sub_size=14)
        dev.place(cv, p.ix, r1.bottom + 22)
        res = Card(iw, "Data residency rule", [
            "Data stored at rest remains in the designated Azure geography, for every deployment type",
            "Doc guidance: if residency requirements allow it, prefer Global Standard; Data Zone deployments (US/EU) are the next best option",
            "A single gateway across geopolitical regions breaks residency: run one isolated gateway stack per boundary",
        ], theme="cyan", icon="regions", src=[("Deployment types", DEP), ("HA page", HA), ("Gateway guidance", GW)])
        res.place(cv, p.ix, dev.bottom + 22)
    return p.bottom


# ---------------------------------------------------------------------------------------------- 3. twin regions
TWIN = [
    ("Foundry account + projects", "foundry", "grape",
     "Create in both regions with IaC (Bicep or Terraform). Build the IaC modular so each project can be deployed independently."),
    ("Model deployments + quota", "openai", "blue",
     "Same models and versions in both regions. Verify full quota is allocated to primary and secondary: az cognitiveservices account list-usage."),
    ("Connections", "api-connections", "cyan",
     "Two resources in two regions, two project connections, verify both are active. Connections to data accounts work across regions."),
    ("Agent definitions, knowledge files, tool bindings", "agent", "green",
     "JSON in source control. Export with AIProjectClient.agents.list() daily or after each deployment, redeploy through the API, update clients for the new agent IDs."),
    ("Vector stores and AI Search indexes", "ai-search", "teal",
     "Search holds a derived, query-optimized projection: keep authoritative content elsewhere, recreate index definitions from IaC, re-run ingestion, verify with baseline queries."),
    ("Files and datasets", "storage", "cyan",
     "Keep large datasets in a separate storage account (limits blast radius, simplifies replication). Choose LRS, GRS or GZRS by RPO; one account can be connected from several regions."),
    ("Thread and conversation history", "cosmos", "red",
     "NOT replicated: 'no built-in one-click export or import' of complete conversation histories. A Purview connection preserves a compliance copy only."),
    ("Fine-tuned models", "ml", "blue",
     "Not covered by the HA and DR pages. Foundry (classic) fine-tuning docs: deploy to another region or subscription. REST 'copy checkpoint' (preview) copies a checkpoint to a destination account and region."),
    ("Network, identity and RBAC", "private-endpoint", "indigo",
     "VNets, private endpoints, VPN and DNS in both regions; role assignments in both; one user-assigned managed identity per project."),
]


def twin_diagram(cv: Canvas, y: float) -> float:
    PW = 690
    MX = PW + 70
    BX = W - PW
    MW = BX - 70 - MX
    section_header(cv, 0, y, "3  A regional outage: what you must replicate yourself", size=32,
                   sub="Region A and Region B are twins that you build and keep in sync. Nothing fails over for you.")
    stamp = Box(1160, "NO AUTOMATIC CROSS-REGION FAILOVER", sub="'Foundry itself doesn't provide automatic failover or disaster recovery.'", theme="red", fill="hatch",
                size=28, sub_size=15, sw=4, h=88)
    stamp.place(cv, W - 1160, y - 6)
    top = y + 110
    cmid = MX + MW / 2
    g_w = 600
    gtraffic = Box(g_w, "Global traffic", sub=wrap("Azure Front Door (public) or DNS record toggling (private networking: Azure has no native global load balancer for private DNS)", g_w - 100, 14),
                   theme="indigo", icon="front-door", icon_pos="left", icon_size=34, size=17, sub_size=14, fill="soft", h=96)
    gtraffic.place(cv, cmid - g_w / 2, top)
    client = Box(250, "Client apps", sub="call the gateway FQDN only", theme="gray", icon="user", icon_pos="left", icon_size=30, size=17, sub_size=13, fill="soft", h=96)
    client.place(cv, gtraffic.x - 90 - 250, top)
    # arrow key (right of the band)
    kx, ky = gtraffic.right + 70, top + 8
    for i, (lab, col, dsh) in enumerate((("normal path", INK, "solid"), ("failover path you must route", "#e8590c", "dashed"), ("not replicated", "#e03131", "dashed"))):
        arrow(cv, [(kx, ky + 12 + i * 30), (kx + 60, ky + 12 + i * 30)], color=col, dash=dsh, sw=2.5)
        cv.text(kx + 74, ky + 2 + i * 30, lab, size=15, color=INK)
    bh = 66
    mboxes = []
    for label, icon, thn, method in TWIN:
        mboxes.append(Box(MW, method, theme="red" if thn == "red" else "gray", fill="soft", size=15, h=bh))
    rh = max(b.h for b in mboxes)
    pitch = rh + 14
    ph_top = top + 150
    gate_w = 600
    gateway = Box(gate_w, "Generative AI Gateway", sub=wrap("for example API Management multi-region: load balancing, circuit breaker, rate limiting, priority routing", gate_w - 100, 14),
                  theme="indigo", icon="apim", icon_pos="left", icon_size=34, size=17, sub_size=14, fill="soft", h=104)
    gateway.place(cv, cmid - gate_w / 2, ph_top + 12)
    connect(cv, client, gtraffic, a_side="right", b_side="left", gap=4)
    connect(cv, gtraffic, gateway, a_side="bottom", b_side="top", gap=4)
    rows_y = ph_top + 144
    panel_h = (rows_y + len(TWIN) * pitch + 14) - ph_top
    a_boxes, b_boxes = [], []
    with cv.panel(0, ph_top, w=PW, h=panel_h, title="Region A (primary)", sub="what runs today", theme="blue", fill="soft", style="solid", pad=30,
                  title_size=26, sub_size=15) as pa:
        for i, (label, icon, thn, method) in enumerate(TWIN):
            b = Box(PW - 60, label, h=rh, theme=thn, icon=icon, icon_pos="left", icon_size=32, size=17, fill="solid")
            b.place(cv, pa.ix, rows_y + i * pitch)
            a_boxes.append(b)
    with cv.panel(BX, ph_top, w=PW, h=panel_h, title="Region B (secondary)", sub="what you must build and keep in sync", theme="orange", fill="soft", style="dashed", pad=30,
                  title_size=26, sub_size=15) as pb:
        for i, (label, icon, thn, method) in enumerate(TWIN):
            b = Box(PW - 60, label, h=rh, theme=thn, icon=icon, icon_pos="left", icon_size=32, size=17, fill="soft", dash="dashed")
            b.place(cv, pb.ix, rows_y + i * pitch)
            b_boxes.append(b)
    for i, mb in enumerate(mboxes):
        mb.place(cv, MX, rows_y + i * pitch, h=rh)
        red = TWIN[i][2] == "red"
        col = "#e03131" if red else INK
        connect(cv, a_boxes[i], mb, a_side="right", b_side="left", gap=4, color=col, dash="dashed" if red else "solid")
        connect(cv, mb, b_boxes[i], a_side="right", b_side="left", gap=4, color=col, dash="dashed" if red else "solid")
        if red:
            mx = (mb.right + b_boxes[i].x) / 2
            cross(cv, mx - 12, mb.cy - 12, 24, 24, sw=4)
    connect(cv, gateway, pa, a_side="left", b_side="right", tb=(gateway.cy - pa.y) / pa.h, gap=4, label="normal path", label_size=15)
    connect(cv, gateway, pb, a_side="right", b_side="left", tb=(gateway.cy - pb.y) / pb.h, gap=4, dash="dashed", label="failover: you route it", label_size=15, color="#e8590c")
    yb = ph_top + panel_h
    src_line(cv, 0, yb + 12, [("Plan for multiregional deployment", HA), ("Fine-tuning: cross-region deployment (classic)", FT_CLASSIC), ("REST: copy checkpoint (preview)", FT_COPY)])
    sy = yb + 44
    cw = (W - 2 * 30 - 2 * 30) / 3
    with cv.panel(0, sy, w=W, title="Shared or per-region services", sub="Their own replication story", theme="gray", style="dotted", pad=30, title_size=24, sub_size=15) as ps:
        items = [
            Box(cw, "Azure Key Vault", sub=wrap("One vault used by both regions. Microsoft-managed paired-region failover: best-effort, can come after a significant delay, read-only after failover.", cw - 110, 14),
                theme="red", icon="key-vault", icon_pos="left", icon_size=36, size=17, sub_size=14, fill="solid"),
            Box(cw, "Azure Container Registry", sub=wrap("Enable geo-replication to the paired region and use the same instance for both projects.", cw - 110, 14),
                theme="blue", icon="acr", icon_pos="left", icon_size=36, size=17, sub_size=14, fill="solid"),
            Box(cw, "Application Insights", sub=wrap("Create one per project in each region; set the data retention period and details.", cw - 110, 14),
                theme="violet", icon="app-insights", icon_pos="left", icon_size=36, size=17, sub_size=14, fill="solid"),
        ]
        hm = max(b.h for b in items)
        sx = ps.ix
        for b in items:
            b.place(cv, sx, ps.iy, h=hm)
            sx += cw + 30
    return ps.bottom


# ---------------------------------------------------------------------------------------------- 4. deployment types
def deployment_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Deployment types: resiliency characteristics as documented", size=32,
                   sub="Where inference is processed, how it is billed and what the docs promise (as of 2026-11-03)")
    y += 96
    tw = 1740
    t = Table(
        [("Deployment type", 180), ("SKU code", 290), ("Data processing", 190), ("Billing", 170), "Resiliency and SLA note, as documented"],
        [
            [("Global Standard", "blue"), "GlobalStandard", "Any Azure region", "Pay-per-token",
             "Best-effort (standard types). Highest default quota; 'eliminates the need to load balance across multiple resources'. If the primary region is interrupted, all traffic initially routed to it is affected."],
            [("Global Provisioned", "blue"), "GlobalProvisionedManaged", "Any Azure region", "Reserved PTU, hourly or reservation",
             "Guaranteed throughput with a latency SLA (defined latency target per model). PTU page: 'Highest availability; when routing region isn't constrained'."],
            [("Global Batch", "blue"), "GlobalBatch", "Any Azure region", "50% discount, 24-hour target",
             "No real-time SLA: targets completion within 24 hours but might take longer."],
            [("Data Zone Standard", "indigo"), "DataZoneStandard", "Within the data zone", "Pay-per-token",
             "Best-effort. Same caveat as Global Standard: an interruption in the primary region affects all traffic initially routed to it."],
            [("Data Zone Provisioned", "indigo"), "DataZoneProvisionedManaged", "Within the data zone", "Reserved PTU",
             "Latency SLA. PTU page: 'Zone-level data residency with higher availability than regional'."],
            [("Data Zone Batch", "indigo"), "DataZoneBatch", "Within the data zone", "50% discount", "No real-time SLA."],
            [("Standard", "cyan"), "Standard", "Within the Azure geography", "Pay-per-token",
             "Best-effort. Single region: Architecture Center says Standard deployments don't support availability zones."],
            [("Regional Provisioned", "cyan"), "ProvisionedManaged", "Within the Azure geography", "Reserved PTU",
             "Latency SLA. PTU page: 'Stays in the deployment's specific Azure region'; 'Strict single-region data residency requirements'."],
            [("Developer", "yellow"), "DeveloperTier", "Any Azure region", "Pay-per-token",
             "No SLA and no residency guarantee. Fixed 24-hour lifetime. Fine-tuned model evaluation only."],
        ], w=tw, theme="blue", size=14, head_size=15)
    t.place(cv, 0, y)
    src_line(cv, 0, t.bottom + 8, [("Deployment types", DEP), ("Provisioned throughput", PTU), ("Architecture Center baseline", ARCH)])
    rx, rw = 1788, W - 1788
    sla = Card(rw, "SLAs: what the docs say (no percentages)", [
        "Learn FAQ: an Availability SLA for all resources and a Latency SLA for Provisioned-Managed deployments",
        "Standard types: best-effort; latency SLA 'None' on the PTU comparison table. Batch: no real-time SLA. Developer: no SLA",
        "Items marked preview in the HA article are provided without an SLA",
        "Dependencies carry their own SLAs (as of 2026-11-03): AI Search needs a billable tier + 2 replicas (read) or 3+ (read-write); Cosmos DB depends on zone redundancy, multi-read and multi-write; API Management rises with multi-zone and multi-region",
        "! SLA percentages live in Microsoft's 'SLA for Online Services' document: check it before quoting a number",
    ], theme="yellow", icon="service-health", src=[("Azure OpenAI FAQ", FAQ), ("SLA for Online Services", SLA_DOC), ("AI Search reliability", SEARCH_REL)])
    sla.place(cv, rx, y)
    dis = Note(rw, "PTU page: Data Zone Provisioned stays 'within a geographic zone (US or EU)'. The deployment-types page lists US, EU and Asia Pacific (APAC) data zones. Check the current list before you plan.",
               kind="warn", title="Docs disagree: data zones", src=[("PTU page", PTU), ("Deployment types", DEP)])
    dis.place(cv, rx, sla.bottom + 20)
    recipe = Card(tw, "HA recipes from the docs for model deployments", [
        "# Standard deployments",
        "Prefer Global Standard when residency allows; otherwise default to Data Zone (US or EU). Create one deployment per model in the primary region and duplicate it in the secondary when you need separate regional endpoints",
        "Size each deployment: don't assume the full available quota is independently available to every deployment",
        "# Provisioned deployments",
        "Enterprise PTU pool: one Data Zone PTU deployment behind API Management; place it in a different region than your primary Standard deployment",
        "Workload-dedicated PTU: place it in a different region than the enterprise pool; fail over to the pool or to Standard through your gateway",
        "! Don't assume automatic PTU-to-PTU failover: only spillover from PTU to a Standard deployment in the same Foundry resource is documented",
    ], theme="blue", icon="openai", src=[("High availability", HA), ("Spillover", learn("openai/how-to/spillover-traffic-management"))])
    recipe.place(cv, 0, t.bottom + 36)
    return max(recipe.bottom, dis.bottom)


# ---------------------------------------------------------------------------------------------- 5. strategies
def strategy_card(cv: Canvas, x: float, y: float, w: float, name: str, thn: str, meaning: str, rto: str, rpo: str, cost: str, best: str,
                  b_state: list[str]) -> Rect2:
    pad = 24
    th = THEMES[thn]
    with cv.panel(x, y, w=w, title=name, sub=wrap(meaning, w - 2 * pad - 20, 15), theme=thn, fill="soft", style="solid", pad=pad, title_size=30, sub_size=15) as p:
        rw = (w - 2 * pad - 50) / 2
        rows = ["Foundry + other resources + data", "Critical resources (for example deployed models)", "Non-critical resources (pipelines and so on)"]
        ry0 = p.iy + 36
        rh, rg = 50, 10
        for rx, who, states in ((p.ix, "Region A (active)", ["on"] * 3), (p.ix + rw + 50, "Region B (secondary)", b_state)):
            cv.text(rx, p.iy + 4, who, size=17, color=th.deep)
            for i, (lab, st) in enumerate(zip(rows, states)):
                yy = ry0 + i * (rh + rg)
                if st == "on":
                    Box(rw, lab, h=rh, theme="gray", fill="solid", size=14).place(cv, rx, yy)
                elif st == "ready":
                    Box(rw, lab + " (ready to start)", h=rh, theme=thn, fill="solid", size=14, dash="dashed").place(cv, rx, yy)
                else:
                    ghost(cv, rx, yy, rw, rh, lab + ": deploy manually", thn, 14)
        cy = ry0 + 3 * (rh + rg) + 12
        for k, (lab, thx) in enumerate(((f"RTO {rto}", thn), (f"RPO {rpo}", thn), (f"Cost: {cost}", "gray"))):
            ch = Chip(lab, theme=thx, size=15)
            ch.place(cv, p.ix, cy + k * 42)
        cv.text(p.ix, cy + 3 * 42 + 8, wrap("Best for: " + best, w - 2 * pad, 15), size=15, color=INK)
    return p


def strategies_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Pick a recovery strategy per component", size=32,
                   sub="Approximate targets from the HA page: actual values depend on deployment size, services in use and data replication configuration")
    y += 96
    cw = (W - 2 * 40) / 3
    cards = [
        strategy_card(cv, 0, y, cw, "Hot/hot", "red", "Both regions are active at the same time and either one is ready to use immediately.",
                      "~ minutes", "~ near zero", "highest, a full duplicate", "production workloads with zero-downtime requirements", ["on", "on", "on"]),
        strategy_card(cv, cw + 40, y, cw, "Hot/warm", "yellow", "Primary active. The secondary has critical resources (for example deployed models) ready to start; deploy noncritical resources manually.",
                      "~ 30 min to 2 h", "~ minutes to hours (replication lag)", "moderate", "business-critical workloads that tolerate a brief disruption", ["on", "ready", "off"]),
        strategy_card(cv, 2 * (cw + 40), y, cw, "Hot/cold", "blue", "Primary active. The secondary has Foundry, other resources and the required data; deploy models, model deployments and pipelines manually.",
                      "~ 2 to 8 h", "~ hours (backup frequency)", "lowest, provisioned but not active", "development, staging, cost-sensitive workloads", ["on", "off", "off"]),
    ]
    by = max(c.bottom for c in cards) + 24
    nw = (W - 2 * 36) / 3
    n1 = Note(nw, "Depending on your business requirements you might treat Foundry services differently: for example hot/hot for production pipelines or model deployments and hot/cold for development.", kind="tip", title="Mix strategies",
              src=[("High availability", HA)])
    n2 = Note(nw, "Use a region in the same geographic area, not necessarily the closest. Paired regions coordinate platform updates and prioritize recovery, but not all regions are paired.", kind="info", title="Choosing the second region",
              src=[("High availability", HA)])
    n3 = Note(nw, "The strategy table values are approximate. The docs give no SLA-backed RTO or RPO for Foundry itself.", kind="warn", title="Targets are approximate", src=[("High availability", HA)])
    hh = max(n.h for n in (n1, n2, n3))
    for i, n in enumerate((n1, n2, n3)):
        n.place(cv, i * (nw + 36), by, h=hh)
    return by + hh


# ---------------------------------------------------------------------------------------------- 6. prevent / detect / fail over / drill
def steps_card(cv: Canvas, x: float, y: float, w: float, title: str, steps: list[str], thn: str, icon: str,
               src: list[tuple[str, str]] = (), foot: str = "") -> Rect2:
    pad = 18
    th = THEMES[thn]
    inner = w - 2 * pad - 46
    wrapped = [wrap(s, inner, 15) for s in steps]
    hs = [text_size(t, 15)[1] for t in wrapped]
    foot_w = wrap(foot, w - 2 * pad, 15) if foot else ""
    foot_h = text_size(foot_w, 15)[1] + 10 if foot else 0
    H = pad + 40 + sum(h + 14 for h in hs) + foot_h + (len(src) * 15 + 8 if src else 0) + pad - 14
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    place_icon(cv, icon, x + pad, y + pad - 2, 34)
    cv.text(x + pad + 46, y + pad + 2, title, size=20, color=th.deep)
    cy = y + pad + 46
    for i, (t, h) in enumerate(zip(wrapped, hs)):
        numbered(cv, x + pad + 15, cy + 12, i + 1, theme=thn, d=28, size=16)
        cv.text(x + pad + 46, cy, t, size=15)
        cy += h + 14
    if foot:
        cv.text(x + pad, cy, foot_w, size=15, color="#c92a2a")
        cy += foot_h
    for label, url in src:
        cv.text(x + pad, cy + 4, f"Learn: {label}", size=12, color=LINK, link=url)
        cy += 15
    cv.register("steps:" + title, x, y, w, H)
    r = Rect2()
    r.x, r.y, r.w, r.h = x, y, w, H
    return r


def flow_row(cv: Canvas, x: float, y: float, w: float, title: str, steps: list[str], thn: str, src: list[tuple[str, str]] = ()) -> float:
    n = len(steps)
    gap = 46
    bw = (w - (n - 1) * gap) / n
    cv.text(x, y, title, size=22, color=THEMES[thn].deep)
    by = y + 48
    boxes = [Box(bw, s, theme=thn, fill="soft", size=15) for s in steps]
    hmax = max(b.h for b in boxes)
    for i, b in enumerate(boxes):
        b.place(cv, x + i * (bw + gap), by, h=hmax)
        numbered(cv, b.x + 16, b.y, i + 1, theme=thn, d=30)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", gap=4)
    bottom = by + hmax
    if src:
        src_line(cv, x, bottom + 8, list(src))
        bottom += 24
    return bottom


def operate_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6  Prevent, detect, fail over, drill", size=32,
                   sub="The HA page's playbook: harden first, configure recovery features before the incident, watch for regional degradation, rehearse the switch")
    y += 96
    tw = 1640
    t = Table(
        [("Control", 260), ("What it protects", 540), "Limits and notes"],
        [
            [("CanNotDelete lock on the Foundry account", "red"), "Prevents deleting the account, projects, models, connections and agent runtime infrastructure", "Doesn't protect individual agents or threads"],
            [("Lock on the Cosmos DB account", "red"), "Prevents deleting the account, the enterprise_memory database and its containers", "Doesn't protect data inside containers"],
            [("Lock on the AI Search service", "red"), "Prevents deleting the search service instance", "Doesn't protect indexes or the data in them"],
            [("Lock on the Storage account", "red"), "Prevents deleting the account and blob containers", "Doesn't protect individual blobs. Users with Owner can remove the lock first"],
            [("Azure Policy denyAction", "red"), "Layered defense: blocks resource provider delete requests, whatever each resource's recovery capabilities", "Combine with locks"],
            [("Least privilege", "red"), "No standing delete permissions in production. Only the project's managed identity has standing write to the state stores",
             "'No built-in AI role is read only' for these data plane operations: Foundry User can delete operational data. Use custom roles that limit Microsoft.CognitiveServices/*/write data actions"],
            [("Single responsibility", "red"), "A dedicated Cosmos DB, AI Search and Storage for this workload's Agent Service", "Sharing with other Foundry accounts widens the permission surface and the blast radius"],
            [("Zone-redundant configuration", "red"), "Cosmos DB, AI Search and Storage survive a single-zone failure", "Doesn't protect against regional outages or human or automation errors"],
        ], w=tw, theme="red", size=14, head_size=15, title="Prevent first: controls and what they do not cover", title_size=22)
    t.place(cv, 0, y)
    n_lock = Note(tw, "Creating locks needs the Owner role: Contributor doesn't include Microsoft.Authorization/locks/write. Locks protect against resource-level deletion, not data plane operations.",
                  kind="tip", title="Locks need Owner", src=[("High availability", HA)])
    n_lock.place(cv, 0, t.bottom + 16)
    rx, rw = 1688, W - 1688
    cfg = Card(rw, "Configure recovery features BEFORE the incident", [
        "Standard agent mode (Basic mode has almost no recovery options for resource loss)",
        "Foundry account: explicit Microsoft Purview connection (compliance data survives thread loss, for eDiscovery)",
        "Foundry project: a user-assigned managed identity, not system-assigned (role assignments survive recreation)",
        "Cosmos DB: continuous backup with point-in-time restore (7, 30 or 35-day tier), read replication to the failover region plus service-managed failover, a unique account name",
        "AI Search: a unique, organization-specific service name. Storage: GZRS so customer-managed failover has a predetermined target",
        "! Continuous backup can't be enabled retroactively: no point-in-time restore unless it was configured in advance",
    ], theme="green", icon="agent", src=[("High availability", HA)])
    cfg.place(cv, rx, y)
    det = steps_card(cv, rx, cfg.bottom + 20, rw, "Early detection (monitor for regional degradation)", [
        "Enable Azure Service Health alerts for all Azure services in your Foundry workload: advance notice of planned maintenance and early warning of unplanned outages",
        "Configure Resource Health alerts for Cosmos DB, Azure OpenAI and Storage accounts to detect individual resource failures",
        "Set up Application Insights availability tests that probe your agent endpoints continuously from multiple geographic locations",
        "Define alert action groups (email, SMS, incident management system) so failover decisions are made quickly",
    ], "violet", "service-health", src=[("High availability", HA), ("Service health alerts", HEALTH)],
        foot="Microsoft doesn't automatically notify you when a zone is down (AI Search reliability page): rely on Resource Health and Service Health alerts.")
    y2 = max(n_lock.bottom, det.bottom) + 44
    left_w = 1330
    b1 = flow_row(cv, 0, y2, left_w, "Fail over to the secondary project", [
        "Identify the secondary project's endpoint and connection details from your IaC configuration or deployment documentation",
        "Switch app config (environment variables or Azure App Configuration) to the secondary endpoint. With a gateway, check the circuit breaker already routes to secondary endpoints. Update direct Cosmos DB, AI Search and Storage connections if not shared",
        "Verify connectivity with a test request against the secondary project endpoint",
        "Resubmit in-progress jobs: jobs running during an outage don't automatically transition to the secondary project",
    ], "orange", src=[("Initiate a failover", HA)])
    b2 = flow_row(cv, left_w + 60, y2, W - left_w - 60, "Verify failover readiness on a schedule (for example quarterly)", [
        "Confirm the secondary project, deployed models and connections match the primary",
        "Run a representative agent or pipeline job in the secondary, including Cosmos DB, AI Search and Storage access",
        "Validate RBAC role assignments for managed identities, users and service principals in the secondary",
        "Test DNS resolution and connectivity, including private endpoints and VPN paths, from client environments",
        "Document gaps and update IaC or pipelines before the next review cycle",
    ], "teal", src=[("Verify failover readiness", HA)])
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- 7. gotchas
def gotchas_section(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "7  Gotchas and open questions", size=32,
                   sub="Documented limits, and where the docs disagree or are silent (check before you rely on them, as of 2026-11-03)")
    y += 96
    nw = (W - 3 * 36) / 4
    notes = [
        Note(nw, "Global Standard and Data Zone deployments distribute inference across regions, which adds resilience to single-region inference outages, but they don't replace a multiregional failover plan. The layer that processes API requests is regional to your Azure resource, so an outage in the service requires you to fail over to another region.",
             kind="gotcha", title="Global is not failover", src=[("Stay informed about service health", HEALTH)]),
        Note(nw, "Foundry projects are not soft-deletable ('Foundry project: No'). Key Vault soft delete: yes. Storage: see its own recover page. Foundry accounts can be recovered only within 48 h and only if not purged (Agent Service DR page).",
             kind="gotcha", title="Soft delete is uneven", src=[("High availability", HA), ("Recover or purge deleted resources", RECOVER)]),
        Note(nw, "A secondary deployment fails with quota errors if quota wasn't allocated in the failover region (check az cognitiveservices account list-usage). PTU quota is per subscription, region and deployment type, and having PTU quota doesn't guarantee capacity.",
             kind="gotcha", title="Quota is not capacity", src=[("High availability", HA), ("Provisioned throughput", PTU)]),
        Note(nw, "Private Link without a gateway: after a region failover update Private DNS records manually. Azure has no native global server load balancer for workloads that need private DNS resolution: use DNS record toggling for active/passive.",
             kind="warn", title="Private DNS after failover", src=[("High availability", HA)]),
        Note(nw, "HA page: 'Foundry projects don't support default storage account failover using GRS/GZRS/RA-GRS/RA-GZRS'. The Agent Service DR pages say to use GZRS with customer-managed failover for the agent-state account. Verify which applies to your setup and test it.",
             kind="warn", title="Docs disagree: storage failover", src=[("High availability", HA), ("Agent Service DR", DR)]),
        Note(nw, "The HA and DR pages don't state zone redundancy for the Foundry resource itself or for model deployments. The Architecture Center says Standard deployments don't support availability zones. This canvas does not draw zone-redundant model deployments.",
             kind="warn", title="Zone resilience not stated", src=[("Architecture Center baseline", ARCH)]),
        Note(nw, "Key Vault failover to the paired region is best-effort, can happen after a significant delay and leaves the vault read-only. It isn't available for some regions (Brazil South, Brazil Southeast, West US 3) or for unpaired regions (as of 2026-11-03).",
             kind="info", title="Key Vault failover is not a plan", src=[("Key Vault availability and redundancy", KV_DR)]),
        Note(nw, "Items marked preview in the HA article carry no SLA. Developer deployments have no SLA, no residency guarantee and a 24-hour lifetime. The REST 'copy checkpoint' API for fine-tuned models is preview.",
             kind="preview", title="Preview and Developer: no SLA", src=[("High availability", HA), ("REST: copy checkpoint", FT_COPY)]),
    ]
    hh = max(n.h for n in notes[:4])
    hh2 = max(n.h for n in notes[4:])
    for i, n in enumerate(notes[:4]):
        n.place(cv, i * (nw + 36), y, h=hh)
    for i, n in enumerate(notes[4:]):
        n.place(cv, i * (nw + 36), y + hh + 28, h=hh2)
    return y + hh + 28 + hh2


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Foundry high availability and resiliency",
                                "What is built in, what is yours: zones, regions, deployment types and what you must replicate (as of 2026-11-03)",
                                icon="foundry", w=W)
    y = summary_strip(cv, bottom + 40) + 56

    section_header(cv, 0, y, "1  The resilience stack: what is built in and what is yours", size=32,
                   sub="Eight layers from the Azure region up to your operations. Owner dots follow the HA and Agent Service DR pages.")
    y += 100
    b1 = resilience_stack(cv, y)
    b2 = ledger(cv, 1788, y, W - 1788)
    y = max(b1, b2) + 60

    section_header(cv, 0, y, "2  Availability zones and data-processing scope", size=32,
                   sub="Zone redundancy protects inside one region; the deployment type decides where inference may be processed")
    y += 96
    z = zones_panel(cv, 0, y, 1740)
    r = rings_panel(cv, 1788, y, W - 1788)
    y = max(z, r) + 70

    y = twin_diagram(cv, y) + 70
    y = deployment_section(cv, y) + 70
    y = strategies_section(cv, y) + 70
    y = operate_section(cv, y) + 70
    y = gotchas_section(cv, y) + 70
    sources(cv, 0, y, [
        ("High availability and resiliency for Foundry projects and Agent Services", HA),
        ("Deployment types for Foundry Models", DEP),
        ("What is provisioned throughput for Foundry Models?", PTU),
        ("Agent Service disaster recovery", DR),
        ("Baseline Microsoft Foundry chat reference architecture", ARCH),
        ("Use a gateway in front of multiple model deployments or instances", GW),
        ("Stay informed about service health regressions", HEALTH),
        ("Reliability in Azure AI Search", SEARCH_REL),
        ("Reliability in Azure Cosmos DB for NoSQL", COSMOS_REL),
        ("Azure Key Vault availability and redundancy", KV_DR),
        ("Reliability in Azure API Management", APIM_REL),
        ("Recover or purge deleted Foundry resources", RECOVER),
        ("Azure OpenAI frequently asked questions (SLAs)", FAQ),
        ("SLA for Online Services (Microsoft licensing)", SLA_DOC),
        ("Fine-tune models (Foundry classic): cross-region deployment", FT_CLASSIC),
    ], w=W, cols=3)
