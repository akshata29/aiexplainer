"""Foundry failure-mode matrix and runbook: component x failure x detection x mitigation x owner, a triage flow and the alert pack."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="bcdr-failure-modes-runbook", title="Failure-mode matrix and runbook", section="4", order=4,
    description="What breaks, how you see it, what you do and whose job recovery is: 32 failure modes across models, agents, state, edge, identity and tools, plus a 15-minute triage flow, the alert pack and a drill plan.",
    tags=["bcdr", "runbook", "failure-modes", "triage", "alerts", "drills"],
)

W = 2800
ASOF = "as of 2026-11-03"

S = dict(
    health=("Stay informed with Service Health", learn("how-to/stay-informed-service-health")),
    monitor=("Monitor model deployments", learn("foundry-models/how-to/monitor-models")),
    known=("Foundry known issues", learn("reference/foundry-known-issues")),
    ha=("High availability and resiliency", learn("how-to/high-availability-resiliency")),
    dr=("Agent Service disaster recovery", learn("how-to/agent-service-disaster-recovery")),
    drp=("Agent Service platform outage", learn("how-to/agent-service-platform-disaster-recovery")),
    dro=("Agent Service resource and data loss", learn("how-to/agent-service-operator-disaster-recovery")),
    limits=("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    hosted=("Hosted agents", learn("agents/concepts/hosted-agents")),
    lrr=("Long-running agent resilience", learn("agents/concepts/long-running-agent-resilience")),
    state=("Agent state store", learn("agents/concepts/agent-state-store")),
    tools=("Tool best practices", learn("agents/concepts/tool-best-practice")),
    bing=("Grounding with Bing Search", learn("agents/how-to/tools/bing-tools")),
    ptu=("Provisioned throughput", learn("openai/concepts/provisioned-throughput")),
    spill=("Spillover traffic management", learn("openai/how-to/spillover-traffic-management")),
    cosmos=("Reliability in Azure Cosmos DB for NoSQL", learn("azure/reliability/reliability-cosmos-db-nosql", base="")),
    search=("Reliability in Azure AI Search", learn("azure/reliability/reliability-ai-search", base="")),
    storage=("Reliability in Azure Blob Storage", learn("azure/reliability/reliability-storage-blob", base="")),
    kv=("Key Vault availability and redundancy", learn("azure/key-vault/general/disaster-recovery-guidance", base="")),
    apim=("Reliability in API Management", learn("azure/reliability/reliability-api-management", base="")),
    apim_mr=("Deploy API Management to multiple regions", learn("azure/api-management/api-management-howto-deploy-multi-region", base="")),
    entra=("Entra: client app resilience", learn("entra/architecture/resilience-client-app", base="")),
    entra_bk=("Entra: backup authentication system", learn("entra/architecture/backup-authentication-system-apps", base="")),
    arch=("Baseline Foundry chat architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")),
    amba=("Azure Monitor baseline alerts", "https://azure.github.io/azure-monitor-baseline-alerts/"),
    insights=("Insights in Foundry (preview)", learn("observability/how-to/agent-insights")),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


SEV = dict(zone="yellow", region="orange", human="red", cap="blue", other="gray")
SEV_LABELS = [("zone", "Zone failure"), ("region", "Region failure"), ("human", "Human error or deletion"),
              ("cap", "Throttle, capacity or quota"), ("other", "Other: runtime, identity, provider, lifecycle")]
OWN = dict(ms=("Microsoft", "blue"), shared=("Shared", "violet"), you=("You", "orange"))


# ---------------------------------------------------------------------------------------------- helpers
def wrap(text: str, width: float, size: float) -> str:
    return "\n".join(wrap_text(text, width, size))


def pill(cv: Canvas, x: float, y: float, text: str, theme: str, size: int = 14, dashed: bool = False,
         solid: bool = True) -> float:
    """Label pill drawn without registering a block (safe next to other blocks). Returns its width."""
    th = THEMES[theme]
    tw, thh = text_size(text, size)
    cv.rect(x, y, tw + 18, thh + 8, stroke=th.stroke, fill=th.fill if solid else "transparent", style="solid", sw=1.5,
            rough=0, dash="dashed" if dashed else "solid")
    cv.text(x + 9, y + 4, text, size=size, color=th.deep)
    return tw + 18


def head(cv: Canvas, y: float, n: int, text: str, sub: str | None = None, tags=()) -> float:
    """Numbered section header with right-aligned provenance tags. Returns the y where content can start."""
    _, bottom = section_header(cv, 0, y, f"{n}   {text}", sub=sub, size=32, w=W)
    tx = W
    for label, theme, dashed in reversed(tags):
        wpx = text_size(label, 15)[0] + 18
        tx -= wpx
        pill(cv, tx, y + 8, label, theme, 15, dashed, solid=not dashed)
        tx -= 14
    return bottom + 22


DOC = ("Documented", "green", False)
SUG = ("Suggested - our synthesis", "orange", True)


def learn_line(cv: Canvas, x: float, y: float, items: list[tuple[str, str]]) -> float:
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=12, color=LINK, link=url)
        cx += t.w + 26
    return y + 18


def pins(cv: Canvas, bx: Rect2, kinds: list[str], size: int = 17) -> None:
    """Failure-class pins that hang on the top edge of a node."""
    x = bx.right - 20
    for k in kinds:
        th = THEMES[SEV[k]]
        cv.ellipse(x - size / 2, bx.y - size / 2, size, size, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
        x -= size + 7


def node(cv: Canvas, x: float, y: float, w: float, label: str, sub: str, kinds: list[str], theme: str,
         icon: str | None = None, h: float = 112) -> Box:
    b = Box(w, label, h=h, theme=theme, sub=sub, icon=icon, icon_pos="left", icon_size=30, size=17, sub_size=14)
    b.place(cv, x, y)
    pins(cv, b, kinds)
    return b


class Anchor(Rect2):
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


# ---------------------------------------------------------------------------------------------- 0. legend + summary
def legend_panel(cv: Canvas, y: float) -> float:
    with cv.panel(0, y, title="How to read this canvas", theme="gray", style="dotted", pad=20, title_size=22, w=W) as p:
        x0, y0 = p.ix, p.iy
        cv.text(x0, y0, "Failure class: colour of the ID cell in each table and of the pins on the map", size=15, color=MUTED)
        for i, (k, label) in enumerate(SEV_LABELS):
            th = THEMES[SEV[k]]
            yy = y0 + 28 + i * 27
            cv.rect(x0, yy + 1, 30, 18, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
            cv.text(x0 + 42, yy, label, size=16)
        x2 = x0 + 900
        cv.text(x2, y0, "Owner column: who recovers", size=15, color=MUTED)
        for i, (k, desc) in enumerate((("ms", "Microsoft restores the service"),
                                       ("shared", "platform restores, you rebuild or reconfigure"),
                                       ("you", "your configuration, your recovery"))):
            lab, th_name = OWN[k]
            yy = y0 + 28 + i * 36
            wpx = pill(cv, x2, yy, lab, th_name, 15)
            cv.text(x2 + wpx + 14, yy + 3, desc, size=15)
        x3 = x0 + 1620
        cv.text(x3, y0, "Provenance and status stickers", size=15, color=MUTED)
        rows = [(("Documented", "green", False), "plain text is stated on the cited Learn page"),
                (("Suggested", "orange", True), "our synthesis: not stated by the docs"),
                (("Preview", "orange", False), "labelled preview by the docs: no SLA"),
                (("Docs disagree", "gray", False), f"pages conflict: read cautiously ({ASOF})")]
        for i, ((lab, th_name, dashed), desc) in enumerate(rows):
            yy = y0 + 28 + i * 33
            wpx = pill(cv, x3, yy, lab, th_name, 15, dashed, solid=not dashed)
            cv.text(x3 + wpx + 14, yy + 3, desc, size=15)
    return p.bottom + 36


def summary_strip(cv: Canvas, y: float) -> float:
    cw = (W - 4 * 34) / 5
    cards = [
        Card(cw, "Detection is yours", [
            "= Microsoft doesn't automatically notify you when a zone is down (Cosmos DB, AI Search and Key Vault reliability pages).",
            "= Wire Resource Health and Service Health alerts first.",
        ], theme="violet", icon="service-health", src=src("cosmos", "kv")),
        Card(cw, "Failover is yours", [
            "= 'Because the layer that processes API requests is regional to your Azure resource, an outage ... requires you to fail over to another region.'",
            "= Foundry itself provides no automatic failover.",
        ], theme="blue", icon="regions", src=src("ha")),
        Card(cw, "Recovery = reconstruction", [
            "= Agent Service has no replication, backup, point-in-time restore or active-active.",
            "= Rebuilt agents get new IDs and no thread history.",
        ], theme="green", icon="agent", src=src("dr")),
        Card(cw, "Numbers are approximate", [
            "= Foundry publishes no SLA-backed RTO or RPO. Every RTO and RPO here is as quoted by the docs.",
            "= Several pages disagree: see the docs-disagree table.",
        ], theme="yellow", icon="quotas", src=src("ha")),
        Card(cw, "Dependencies fail loudest", [
            "= 'An outage in Azure Storage is unlikely to manifest as a limited scope outage in your workload.'",
            "= When every agent in a project fails, look at Cosmos DB first.",
        ], theme="cyan", icon="cosmos", src=src("drp")),
    ]
    _, bottom = row(cv, 0, y, cards, gap=34)
    return bottom + 44


# ---------------------------------------------------------------------------------------------- 1. failure-point map
def failure_map(cv: Canvas, y: float) -> float:
    y = head(cv, y, 1, "Where things break: a failure-point map",
             sub="Pins on a box = the failure classes documented for it (colours in the key above). IDs point at the matrix rows below.",
             tags=(SUG,))
    top = y + 8
    ph = 456
    # callers
    clients = Box(190, "Clients and apps", h=112, theme="gray", icon="user", icon_pos="top", size=17).place(cv, 0, top + 70)
    # edge and gateway
    with cv.panel(250, top, title="Edge and gateway", theme="indigo", style="dotted", pad=20, title_size=22, h=ph) as ed:
        fd = node(cv, ed.ix, ed.iy, 250, "Front Door or Traffic Manager", "D4  origin health probes", ["region"], "indigo", "front-door")
        am = node(cv, ed.ix + 320, ed.iy, 250, "API Management gateway", "D1 D2 D3  zone, region, bad config", ["zone", "region", "human"], "indigo", "apim")
        connect(cv, fd, am)
        e1 = Note(570, "Front Door for WAF and public traffic; Traffic Manager for DNS-TTL failover. Keep the gateway non-bypassable.",
                  kind="tip", title="Edge is yours", size=15)
        e1.place(cv, ed.ix, ed.iy + 112 + 30)
        Note(570, "Zones: Premium (classic), Premium v2 and Standard v2. Multi-region: Premium classic only; the management plane and developer portal go down with the primary region.",
             kind="info", title="APIM tiers matter", size=15, src=src("apim")).place(cv, ed.ix, e1.bottom + 18)
    # Foundry resource
    fx = ed.right + 130
    with cv.panel(fx, top, title="Foundry resource: regional", theme="blue", style="solid", fill="soft", pad=20, title_size=22, h=ph) as fp:
        bw = 340
        r1 = [node(cv, fp.ix, fp.iy, bw, "Foundry resource and projects", "A1 A2  regional outage, deletion", ["region", "human"], "blue", "foundry"),
              node(cv, fp.ix + bw + 26, fp.iy, bw, "Model deployments", "A3 A4 A8  429, 5xx, retirement", ["cap", "region", "other"], "blue", "openai"),
              node(cv, fp.ix + 2 * (bw + 26), fp.iy, bw, "PTU deployments", "A5 A6 A7  utilisation, capacity, 400", ["cap"], "blue", "quotas")]
        py = fp.iy + 112 + 26
        with cv.panel(fp.ix, py, title="Project", theme="green", style="dashed", pad=18, title_size=20) as pj:
            ag = node(cv, pj.ix, pj.iy, bw, "Agent Service (Standard setup)", "B1 B2 B3 B4  outage, deletion, caps", ["region", "human", "cap"], "green", "agent")
            hr = node(cv, pj.ix + bw + 26, pj.iy, bw, "Hosted-agent runtime", "B5 B6 B7  crash, eviction, bad release", ["other", "human"], "green", "container-apps")
        Note(1072 - pj.w - 26, "Standard deployments run in one region and have no availability-zone support. Global and Data Zone routing 'doesn't replace' regional failover.",
             kind="warn", title="Regional by design", size=14, src=src("arch")).place(cv, pj.right + 26, py)
    # tools and grounding
    tx = fp.right + 130
    with cv.panel(tx, top, title="Tools and grounding", theme="orange", style="dotted", pad=20, title_size=22, h=ph) as tp:
        tw_ = W - tx - 40
        t1 = node(cv, tp.ix, tp.iy, tw_, "Tools: MCP, OpenAPI, A2A", "F1  endpoint down, auth, region support", ["other"], "orange", "mcp", h=104)
        t2 = node(cv, tp.ix, tp.iy + 126, tw_, "Grounding with Bing Search", "F2  provider outage, outside the Geo boundary", ["other"], "orange", "bing", h=104)
        t3 = node(cv, tp.ix, tp.iy + 252, tw_, "Speech custom TTS models", "F3  no DR copy (known issue 2001)", ["other"], "orange", "speech", h=104)
    arrow(cv, [(clients.right + 6, clients.cy), (ed.x - 6, clients.cy)], end_head="arrow")
    connect(cv, ed, fp, label="request", label_size=14, a_side="right", b_side="left")
    connect(cv, fp, tp, a_side="right", b_side="left", dash="dashed", label="tool calls", label_size=14)
    # state plane
    sy = top + ph + 78
    with cv.panel(0, sy, title="State, secrets and knowledge: your resources in the Standard agent setup", theme="cyan", style="dotted",
                  pad=20, title_size=22) as sp:
        nw = (W - 40 - 5 * 22) / 6
        items = [("Azure Cosmos DB", "C1  agent state", ["zone", "region"], "cosmos"),
                 ("Azure AI Search", "C2  vector store, knowledge", ["zone", "region"], "ai-search"),
                 ("Azure Storage", "C3  agent files", ["zone", "region"], "storage"),
                 ("Azure Key Vault", "C4  secrets and keys", ["zone", "region"], "key-vault"),
                 ("Azure Container Registry", "C5  hosted-agent images", ["region"], "acr"),
                 ("Application Insights", "C6  traces, availability tests", ["region"], "app-insights")]
        for i, (lab, sub, kinds, ic) in enumerate(items):
            node(cv, sp.ix + i * (nw + 22), sp.iy, nw, lab, sub, kinds, "cyan", ic, h=104)
    arrow(cv, [(fp.cx, fp.bottom + 6), (fp.cx, sp.y - 6)], dash="dashed", start_head="arrow", end_head="arrow",
          label="agent state, files, knowledge, secrets", label_size=14, label_pos="right")
    # identity + network
    cy_ = sp.bottom + 50
    hw = (W - 40) / 2
    with cv.panel(0, cy_, title="Identity (cross-cutting)", theme="red", style="dotted", pad=20, title_size=22, w=hw) as ip:
        w2 = (hw - 40 - 24) / 2
        node(cv, ip.ix, ip.iy, w2, "Microsoft Entra ID", "E1  sign-in and token service disruption", ["other"], "red", "entra-connect", h=104)
        node(cv, ip.ix + w2 + 24, ip.iy, w2, "Project managed identity", "E2  new identity after recreate", ["human"], "red", "managed-identity", h=104)
    with cv.panel(hw + 40, cy_, title="Network (cross-cutting)", theme="indigo", style="dotted", pad=20, title_size=22, w=hw) as np_:
        node(cv, np_.ix, np_.iy, w2, "DNS and private endpoints", "D5  region failover with Private Link", ["region"], "indigo", "private-endpoint", h=104)
        node(cv, np_.ix + w2 + 24, np_.iy, w2, "Egress firewall and delegated subnet", "D6  SNAT and subnet exhaustion", ["cap"], "indigo", "firewall", h=104)
    return max(ip.bottom, np_.bottom) + 44


# ---------------------------------------------------------------------------------------------- 2. triage flow
def triage(cv: Canvas, y: float) -> float:
    y = head(cv, y, 2, "The 15-minute triage flow",
             sub="Start here during an incident. The order and the 15-minute budget are our synthesis; every signal and action comes from the cited pages.",
             tags=(SUG,))
    lane_w = 840
    lanes = [
        Card(lane_w, "5xx + ModelAvailabilityRate drop: outage path", [
            "Confirm scope with Service Health and Resource Health for your region and service",
            "Decide per project: reroute at the gateway (circuit breaker to the secondary: A4, D2) or rebuild in the warm standby (Agent Service: B1)",
            "Keep the secondary identical: same model and version, quota in place, private DNS and endpoints (D5)",
        ], theme="orange", icon="regions", fill="soft", src=src("health", "drp"), title_size=19, body_size=15),
        Card(lane_w, "429: capacity or quota path", [
            "Read the headers: x-ratelimit-* and retry-after-ms; an effective limit below your TPM is a temporary adjustment (A3)",
            "PTU deployment? Spillover to Standard, retry, or scale PTUs (A5 to A7)",
            "Standard deployment? Rebalance TPM, back off with jitter, spread across deployments and regions",
            "Sustained production 429s below your quota: open a support ticket",
        ], theme="blue", icon="quotas", fill="soft", src=src("monitor", "spill"), title_size=19, body_size=15),
        Card(lane_w, "Latency only: shared-pool variability", [
            "TimeToResponse or NormalizedTimeBetweenTokens up, with no 429s or 5xx",
            "Look at PTU or a regional deployment",
        ], theme="gray", icon="metrics", fill="soft", src=src("monitor"), title_size=19, body_size=15),
        Card(lane_w, "Errors on agents: isolate the dependency", [
            "Every agent in a project fails: a dependency, Cosmos DB first (C1), then AI Search and Storage (C2, C3)",
            "Only agents with file knowledge fail: AI Search or Storage",
            "Suggested: also rule out hosted-agent session caps (B3) and tool endpoints (F1)",
        ], theme="green", icon="agent", fill="soft", src=src("drp"), title_size=19, body_size=15),
    ]
    lane_gap = 18
    total = sum(c.h for c in lanes) + lane_gap * 3
    top = y + 76
    lx = 1540
    yy = top
    for c in lanes:
        c.place(cv, lx, yy)
        yy += c.h + lane_gap
    cyc = top + total / 2
    # left cluster
    start = Box(160, "Alert or user report", theme="gray", shape="ellipse", size=17, h=130)
    start.place(cv, 0, cyc - start.h / 2)
    s1 = Box(230, "1  Platform check", theme="gray", sub="Azure status page, Service Health, Foundry known issues", size=18, sub_size=14,
             icon="service-health", icon_pos="top", h=170).place(cv, 190, cyc - 85)
    d1 = Box(230, "Known service issue for your region?", theme="grape", shape="diamond", size=16, h=210).place(cv, 480, cyc - 105)
    s2 = Box(250, "2  Split ModelRequests", theme="violet", sub="by StatusCode, ModelDeploymentName and Region", size=18, sub_size=14,
             icon="metrics", icon_pos="top", h=170).place(cv, 800, cyc - 85)
    d2 = Box(220, "3  What dominates?", theme="grape", shape="diamond", size=17, h=200).place(cv, 1120, cyc - 100)
    connect(cv, start, s1)
    connect(cv, s1, d1)
    connect(cv, d1, s2, label="no", label_size=15, label_dy=-4)
    connect(cv, s2, d2)
    # lane arrows from d2
    labels = ["5xx", "429", "slow only", "agents"]
    for c, lab in zip(lanes, labels):
        p1x, p2x = d2.right + 6, c.x - 6
        l1 = 0.4 * (p2x - p1x)
        l2 = abs(c.cy - d2.cy)
        l3 = p2x - p1x - l1
        connect(cv, d2, c, a_side="right", b_side="left", route="elbow", bend=0.4, label=lab, label_size=14,
                label_t=(l1 + l2 + 0.5 * l3) / (l1 + l2 + l3), label_pos="above")
    # known issue -> outage lane (over the top)
    ty_ = top - 34
    arrow(cv, [(d1.cx, d1.y - 4), (d1.cx, ty_), (lanes[0].cx, ty_), (lanes[0].cx, lanes[0].y - 6)], color="#e8590c", sw=3,
          label="yes: a known incident covers you", label_size=14, label_t=0.40, label_pos="above")
    # brace and communicate
    bx = lx + lane_w + 24
    brace(cv, bx, top, top + total, side="right", depth=22)
    comm = Card(W - (bx + 70), "4  Communicate", [
        "Tell users about the standby environment: its state is not portable",
        "Resubmit in-flight jobs",
        "Suggested: log the gaps you hit, then update the IaC and runbook",
    ], theme="pink", icon="groups", title_size=19, body_size=15)
    comm.place(cv, bx + 70, cyc - comm.h / 2)
    arrow(cv, [(bx + 24, cyc), (bx + 64, cyc)], end_head="arrow")
    bottom = top + total
    # notes above and below the left cluster (kept clear of the 'yes' arrow at x ~ 595 and the lane bus at x ~ 1,400)
    n1 = Note(530, "The Foundry known-issues page lists no currently active Agent Service known issues at the time of reading (" + ASOF + "). Re-check it during every incident and set up outage notifications in Service Health.",
              kind="info", title="Step 1 detail", src=src("known", "health"))
    n1.place(cv, 0, top + 10)
    n2 = Note(690, "Route a failed dependency or platform problem to its owner. Do not patch the agent for a failing tool, model, network or platform.",
              kind="tip", title="Fix the right layer", src=src("insights"))
    n2.place(cv, 660, top + 10)
    n3 = Note(1330, "Diamonds are decisions. The lane colour is the failure class: orange = region, blue = capacity or quota, gray = other, green = agent plane. Letters and numbers such as A3 or B1 are the matrix rows below. Metric names are the Foundry resource metrics.",
              kind="key", title="Reading the flow")
    n3.place(cv, 0, cyc + 125)
    return max(bottom, n1.bottom, n3.bottom) + 44


# ---------------------------------------------------------------------------------------------- 3. alert pack
def alert_pack(cv: Canvas, y: float) -> float:
    y = head(cv, y, 3, "The alert pack: documented building blocks",
             sub="Five signal sources feed one action group. The building blocks are documented; combining them into this pack is our suggestion.",
             tags=(DOC, SUG))
    cw = (W - 4 * 34) / 5
    cards = [
        Card(cw, "Service Health alert rule", [
            "Scope: Azure OpenAI, Foundry Models and Foundry Agent Service, plus your regions",
            "Event types: service issue, planned maintenance, health advisories, security advisories",
        ], theme="gray", icon="service-health", src=src("health")),
        Card(cw, "Resource Health and Azure Monitor alerts", [
            "Resource Health alerts on Cosmos DB, Azure OpenAI and Storage (high-availability page)",
            "Azure Monitor alerts on Cosmos DB, AI Search and Storage (agent DR overview)",
        ], theme="gray", icon="alerts", src=src("ha", "dr")),
        Card(cw, "Metric alerts on the Foundry resource", [
            "ModelRequests (StatusCode 5xx), ModelAvailabilityRate below target, TimeToResponse, NormalizedTimeBetweenTokens, ProvisionedUtilization",
            "Split by ModelDeploymentName and StatusCode",
            "Creating them needs Monitoring Contributor",
        ], theme="blue", icon="metrics", src=src("monitor")),
        Card(cw, "Azure Monitor baseline alerts", [
            "A baseline alert set for AI services and Azure AI Search, referenced by the Architecture Center",
        ], theme="cyan", icon="monitor", src=src("amba", "arch")),
        Card(cw, "Availability tests on agent endpoints", [
            "Application Insights availability tests run from multiple geographies",
            "The outside-in detector for the regional-outage rows (A1, B1)",
        ], theme="green", icon="app-insights", src=src("dr")),
    ]
    _, cb = row(cv, 0, y, cards, gap=34)
    ag_y = cb + 64
    ag = Box(W, "Action group", theme="violet", sub="email, SMS, webhook, ITSM", size=22, sub_size=16, icon="alerts",
             icon_pos="left", h=84).place(cv, 0, ag_y)
    for c in cards:
        arrow(cv, [(c.cx, ag_y - 6), (c.cx, c.bottom + 6)], start_head="arrow", end_head=None, sw=2, color="#6741d9")
    rp_y = ag_y + 84 + 60
    rp = Box(1250, "Responders", theme="pink", sub="the triage flow above, an ITSM ticket or webhook automation", size=22, sub_size=15,
             icon="groups", icon_pos="left", h=96).place(cv, 0, rp_y)
    arrow(cv, [(rp.cx, rp.y - 6), (rp.cx, ag.bottom + 6)], start_head="arrow", end_head=None, sw=3)
    n1 = Note(W - (rp.right + 50), "The full alert catalogue, dashboards and the on-call flow are on the 'Monitoring, alerting and incident response' canvas. The Notification Center is an in-portal feed, not a paging channel.",
              kind="info", title="See also")
    n1.place(cv, rp.right + 50, rp_y, h=96)
    return rp_y + 96 + 44


# ---------------------------------------------------------------------------------------------- 4. matrices
def own(key: str, text: str | None = None):
    lab, th = OWN[key]
    return (text or lab, th)


def sev(id_: str, kind: str):
    return (id_, SEV[kind])


GAP = DASH

A_ROWS = [
    [sev("A1", "region"), "Foundry resource: control plane and data-plane endpoint", "Regional outage",
     "Azure Service Health alert (scope: Azure OpenAI, Foundry Models, Foundry Agent Service + your regions); Resource Health; Application Insights availability tests; ModelAvailabilityRate drop and 5xx",
     "'Because the layer that processes API requests is regional to your Azure resource, an outage ... requires you to fail over to another region.' Manual: switch the app config (App Configuration) to the secondary project or endpoint. Semi-automatic: APIM load balancing + circuit breaker.",
     own("shared", "Microsoft restores; you fail over")],
    [sev("A2", "human"), "Foundry account or project", "Deleted by a human or automation",
     "Activity Log delete events. Suggested: alert on them (the docs only say prevent with locks + denyAction).",
     "Prevent with a CanNotDelete lock + policy. Recover the account within 48 h (do not purge). A project is not soft-deletable: recreate it from IaC; agents get new IDs.",
     own("you")],
    [sev("A3", "cap"), "Model deployment (Standard, Global, Data Zone)", "429 rate limit",
     "ModelRequests split by StatusCode; x-ratelimit-* headers; an effective x-ratelimit-limit-tokens below the configured TPM = a temporary adjustment",
     "Back off with jitter and honour retry-after-ms; raise or rebalance TPM; request quota; spread across deployments and regions; PTU for guaranteed capacity. Sustained production 429s below quota: open a support ticket.",
     own("you", "You (Microsoft for shared-pool adjustments)")],
    [sev("A4", "region"), "Model deployment", "Regional model or service errors (5xx)",
     "ModelAvailabilityRate minimum below target; ModelRequests 5xx; Service Health",
     "Gateway circuit breaker to a secondary region or deployment. Keep the same model + version there and verify its quota.",
     own("shared", "You (gateway); Microsoft (restore)")],
    [sev("A5", "cap"), "PTU deployment", "Utilisation at or above 100%",
     "ProvisionedUtilization (Models metrics) or 'Provisioned-managed utilization V2' (Azure OpenAI metrics); 429 with retry-after-ms",
     "Spillover to Standard; retry; scale PTUs (needs capacity); enterprise PTU pool",
     own("you")],
    [sev("A6", "cap"), "PTU deployment", "Capacity unavailable to create, scale or recreate",
     "Portal capacity check; Model Capacities API; deployment failure",
     "Try fewer PTUs, another region or retry later; request via the quota form (takes days); avoid scale-down-then-up churn",
     own("shared", "You; Microsoft owns the capacity pool")],
    [sev("A7", "cap"), "PTU deployment", "Long-context request (for example gpt-4.1 PTU context below 128K)",
     "HTTP 400",
     "Spillover covers 400 long-context requests",
     own("you")],
    [sev("A8", "other"), "Model lifecycle", "Version retirement or auto-upgrade behaviour change",
     "Retirement notices; evaluation regression",
     "Pin the version, disable auto-upgrade and keep a regression suite (see the FinOps, capacity and model-lifecycle canvas)",
     own("you")],
]

B_ROWS = [
    [sev("B1", "region"), "Agent Service (Standard setup)", "Regional platform outage: control plane, runtime and dependencies",
     "Service Health; data-plane API errors or timeouts; portal unavailable; Application Insights availability test",
     "Warm-standby Foundry account (VNet, no projects) -> recreate projects, dependencies and the user-assigned identity from IaC -> redeploy agents (new IDs) -> repoint the gateway. Documented: RTO 30+ min per project; RPO = state is not transferable.",
     own("shared", "Microsoft restores the region; you rebuild")],
    [sev("B2", "human"), "Agent Service", "Project, agent, thread or account deleted; Cosmos DB, AI Search or Storage deleted",
     "Errors on agent or thread IDs; Activity Log; Resource Health",
     "See the Agent Service disaster recovery canvas, scenario table: point-in-time restore, rebuild, destructive reset.",
     own("you")],
    [sev("B3", "cap"), "Agent Service quotas", "Hosted-agent session caps",
     f"429 session_quota_exceeded (default 2,000 concurrent sessions per subscription per region in Canada Central, East US 2, Japan East, North Central US, South Africa North, Southeast Asia and Sweden Central; 1,000 elsewhere, {ASOF}); regional_session_quota_exceeded (429); subnet_exhausted (429)",
     "Stop idle sessions or delete unneeded ones; raise the limit via a support ticket; retry with backoff or use another region; use a larger delegated subnet.",
     own("shared", "You (limits); Microsoft (regional capacity)")],
    [sev("B4", "cap"), "Agent definition", "Version cap",
     "HTTP 400 UserError at 1,000 versions per agent: terminal, do not retry",
     "Delete old versions in the pipeline",
     own("you")],
    [sev("B5", "other"), "Hosted-agent runtime", "Container crash, out-of-memory, restart or redeploy",
     "Logs (monitor-hosted-agent-logs), traces, the agent dashboard run-success-rate (below 95% warrants investigation)",
     "Opt in to resilient background execution (Responses protocol, stored background responses): lease-based reclaim, and the handler is re-entered from the beginning, not replayed. Foreground responses are not reinvoked. Use a durable state store (items up to 1 MB, default 30-day idle expiry), idempotency keys and side-effect watermarks.",
     own("shared", "Platform: identity and lease; you: idempotency")],
    [sev("B6", "other"), "Hosted-agent runtime", "Idle eviction or compute loss",
     "Session resume latency",
     "$HOME and /files persist (disk budget up to 20 GiB at 1 vCPU or more, about 20% reserved); idle timeout 2 to 240 min (default 15); a session is deleted after 30 days idle.",
     own("ms")],
    [sev("B7", "human"), "Hosted-agent runtime", "Bad release",
     "Evaluation or monitor regression",
     "Versions are immutable. Roll back by pointing the endpoint version selector at the prior version: no rebuild, no new version. Docs disagree about canary splits: see the docs-disagree table.",
     own("you")],
]

C_ROWS = [
    [sev("C1", "region"), "Azure Cosmos DB (agent state)",
     "Zone-redundant account: synchronous replication, no data loss, brief interruptions of seconds. Non-zonal accounts may sit in one zone.",
     "Single region: read and write lost until restored (no data loss unless unrecoverable). Multi-region single-write: service-managed failover (can take 1 h or more to declare) or forced failover (unreplicated-write loss); PPAF option. Multi-write: automatic routing. RPO by consistency: session, consistent prefix, eventual under 15 min; bounded staleness = min(100,000 writes, 300 s) for multi-region; strong = 0.",
     "Resource Health, Service Health, Azure Monitor alerts on Cosmos DB",
     "Enable zone redundancy, add a read region + service-managed failover, turn on continuous backup (PITR)",
     own("you")],
    [sev("C2", "region"), "Azure AI Search (agent vector store and your knowledge indexes)",
     "Zone-redundant on Basic and higher with 2 or more replicas; replicas are spread (not guaranteed); primary promotion takes seconds for writes.",
     "A single-region service: unavailable if the region is down. Multi-region = you deploy N services, sync the indexes and add a load balancer.",
     "Resource Health, Service Health, Azure Monitor baseline alerts for AI Search",
     "3 or more replicas for the read-write SLA (2 or more for read-only). No self-service backup (sample index backup-restore scripts): rebuild from source; offline index + swap.",
     own("you", "You (SLA conditions: billable tier + replicas)")],
    [sev("C3", "region"), "Azure Storage (agent files)",
     "ZRS: synchronous across zones, no data loss.",
     "GRS and GZRS are asynchronous: RPO 'typically under 15 min, not guaranteed' (check Last Sync Time). Customer-managed failover typically under 60 min RTO; the account becomes LRS after failover. Microsoft-managed failover is a last resort: do not rely on it.",
     "Resource Health; Last Sync Time",
     "GZRS + customer-managed failover (agent playbook: RTO 20+ min, RPO about 15 min; failback 10+ min); soft delete. The docs disagree on GRS and GZRS for Foundry: see the table below.",
     own("you")],
    [sev("C4", "region"), "Azure Key Vault",
     "Automatic zone redundancy (synchronous), no data loss.",
     "Paired-region asynchronous replication. Microsoft-managed failover is best effort and 'likely to occur after a significant delay' (hours). Read-only after failover (list, get, crypto operations, backup only). Private Link reconnection up to 20 min. Not available for Brazil South, Brazil Southeast, West US 3 or unpaired regions.",
     "Resource Health",
     "Soft delete (default 90 days) + purge protection; backup and restore to another region (same subscription and geography, up to 500 versions); separate vaults per availability domain; cache secrets; about 200 operations per second per software-key vault.",
     own("shared", "Microsoft + you")],
    [sev("C5", "region"), "Azure Container Registry", GAP, "Geo-replication to the paired region", GAP,
     "Use the same registry for both projects; enable ACR geo-replication", own("you")],
    [sev("C6", "region"), "Application Insights", GAP, "One per region per project", GAP,
     "Retention per the Application Insights configuration", own("you")],
]

D_ROWS = [
    [sev("D1", "zone"), "APIM gateway", "Zone failure",
     "Resource Health; availability",
     "Premium (classic), Premium v2 and Standard v2 support zones; Basic v2, Basic, Standard (classic), Developer and Consumption do not. Use 2 or more units across zones.",
     own("you")],
    [sev("D2", "region"), "APIM gateway", "Region failure",
     "Regional status endpoint /status-0123456789abcdef (gateway only); Traffic Manager probes",
     "Multi-region (Premium classic only): auto-reroute to the next closest gateway. The management plane and developer portal are down if the primary region is down; gateways keep serving the last config. Config sync takes under about 10 s (recent changes could be lost); rate-limit counters are regional. Backup and restore: 30-day expiry (Developer, Basic, Standard, Premium classic).",
     own("you", "You (Microsoft detects and reroutes within multi-region)")],
    [sev("D3", "human"), "APIM", "Bad config or deletion",
     GAP,
     "APIOps and IaC; backup and restore; service update settings (test instance early, production late; maintenance window in Basic, Standard, Premium classic and Developer)",
     own("you")],
    [sev("D4", "region"), "Front Door or Traffic Manager", "Gateway origin health",
     "Probes",
     "Front Door for WAF and public traffic; Traffic Manager for DNS-TTL failover; keep the gateway non-bypassable; Gateway Routing pattern",
     own("you")],
    [sev("D5", "region"), "Networking, DNS and private endpoints", "Region failover with Private Link and no gateway",
     "DNS resolution failures after failover",
     "Manually update Private DNS to the secondary private endpoints. Split-brain DNS if all traffic goes through the gateway. No native private GSLB: toggle DNS records. Private endpoints for each instance in each region. Account recovery does not restore private endpoints: recreate them.",
     own("you")],
    [sev("D6", "cap"), "Networking", "Egress firewall SNAT exhaustion; subnet exhaustion",
     "Firewall SNAT metrics; subnet_exhausted 429",
     "Azure Firewall across zones + multiple public IPs; larger delegated subnet",
     own("you")],
]

E_ROWS = [
    [sev("E1", "other"), "Microsoft Entra ID", "Sign-in or token service disruption",
     "Authentication failures",
     "Entra's backup authentication system gives resilience for supported protocols and flows. Use MSAL-style token caching and serialise the caches; use user-assigned managed identities; keep role assignments in both regions.",
     own("shared", "Microsoft + you")],
    [sev("E2", "human"), "Project managed identity", "System-assigned identity regenerated when the project or resource is recreated",
     "403s after recovery",
     "Prefer a user-assigned identity (re-attach after restore). With a system-assigned identity, recreate the role assignments (immutable principal ID).",
     own("you")],
]

F_ROWS = [
    [sev("F1", "other"), "Tools: MCP, OpenAPI and A2A endpoints", "Endpoint down, auth failure, or tool not available in the region or model",
     "Agent traces (tool inputs and outputs); tool-call failures",
     f"Validate the endpoint is reachable and auth works. Tool availability needs both model and region support: code interpreter is missing in southcentralus and spaincentral; file search is missing in Italy North and Brazil South ({ASOF}). Check before choosing the DR region. Instruct the agent how to respond when a tool fails; govern centrally via the AI gateway (preview).",
     own("you", "Tool owner and you")],
    [sev("F2", "other"), "Grounding with Bing Search", "Provider outage or policy",
     "Tool failures in traces",
     "Data flows outside the Azure compliance and Geo boundary and the DPA does not apply. The tool doc has no HA or SLA statement: design graceful degradation.",
     own("shared", "Microsoft Bing and you")],
    [sev("F3", "other"), "Speech custom TTS models", "No model copy for DR",
     f"Known issue 2001 (June 2025): 'The TTS service doesn't allow model copying via the REST API for disaster recovery purposes.' No workaround ({ASOF}).",
     "Plan to retrain in the secondary region",
     own("you")],
]


def mtable(title: str, theme: str, rows: list, *, size: int = 14) -> Table:
    cols = [("ID", 62), ("Component", 250), ("Failure", 290), ("Detect: documented signals", 690), ("Mitigate and runbook", 1238), ("Owner", 270)]
    return Table(cols, rows, w=W, theme=theme, size=size, head_size=15, title=title, title_size=24)


def matrices(cv: Canvas, y: float) -> float:
    y = head(cv, y, 4, "The failure-mode matrix: component x failure x detect x mitigate x owner",
             sub=f"32 failure modes in six bands. Plain text is documented; 'Suggested' marks our additions. All numbers are as quoted by the docs ({ASOF}).",
             tags=(DOC, SUG))
    cv.text(0, y, "ID cell colour:", size=15, color=MUTED)
    lg = legend(cv, 140, y, [("Zone", "yellow"), ("Region", "orange"), ("Human error", "red"), ("Throttle or capacity", "blue"), ("Other", "gray")], size=15)
    ox = lg.x + lg.w + 50
    cv.text(ox, y, "Owner (from the shared-responsibility statements on the cited pages):", size=15, color=MUTED)
    px = ox + text_size("Owner (from the shared-responsibility statements on the cited pages):", 15)[0] + 20
    for k in ("ms", "shared", "you"):
        lab, th_name = OWN[k]
        px += pill(cv, px, y - 4, lab, th_name, 15) + 12
    y += 56
    cv.text(0, y, f"Numbers at a glance: RTO and RPO as the docs quote them. Approximate and not SLA-backed ({ASOF}).", size=22, color=INK)
    y += 40
    cw = (W - 5 * 28) / 6
    nums = [
        Card(cw, "30+ min", ["Agent Service regional platform outage, warm-standby rebuild (B1)", "RPO: the state is not transferable"],
             subtitle="RTO per project", theme="green", title_size=28, src=src("drp")),
        Card(cw, "20+ min", ["Agent-state Storage: GZRS + customer-managed failover (C3)", "RPO about 15 min; failback 10+ min"],
             subtitle="RTO, agent playbook", theme="cyan", title_size=28, src=src("drp")),
        Card(cw, "Under 60 min", ["Storage customer-managed failover, typical RTO (C3)", "RPO typically under 15 min, not guaranteed: check Last Sync Time"],
             subtitle="RTO, Storage reliability page", theme="cyan", title_size=28, src=src("storage")),
        Card(cw, "Under 15 min", ["Cosmos DB RPO for session, consistent prefix and eventual consistency (C1)", "Bounded staleness: min(100,000 writes, 300 s). Strong: 0",
                                  "Service-managed failover can take 1 h or more to declare"],
             subtitle="RPO, Cosmos DB", theme="cyan", title_size=28, src=src("cosmos")),
        Card(cw, "Hours", ["Key Vault Microsoft-managed failover is best effort: 'likely to occur after a significant delay' (C4)", "Read-only after failover; Private Link reconnection up to 20 min"],
             subtitle="Key Vault failover", theme="red", title_size=28, src=src("kv")),
        Card(cw, "About 10 s", ["APIM multi-region config sync: recent changes could be lost (D2)", "AI Search primary promotion for writes takes seconds (C2)"],
             subtitle="Sync and promotion", theme="indigo", title_size=28, src=src("apim_mr", "search")),
    ]
    _, nb = row(cv, 0, y, nums, gap=28)
    y = nb + 36
    bands = [
        ("A   Model plane: deployments, PTU and lifecycle", "blue", A_ROWS, ("monitor", "ha", "ptu", "spill")),
        ("B   Agent plane: Agent Service and the hosted-agent runtime", "green", B_ROWS, ("limits", "hosted", "lrr", "state", "dr")),
    ]
    for title, theme, rows, cites in bands:
        t = mtable(title, theme, rows)
        t.place(cv, 0, y)
        y = learn_line(cv, 0, t.bottom + 8, src(*cites)) + 30
    # state plane has its own columns
    cols = [("ID", 62), ("Component", 230), ("Zone failure", 400), ("Region failure", 790), ("Detect", 250), ("Mitigate", 790), ("Owner", 278)]
    tc = Table(cols, [[r[0], r[1], (r[2], "yellow") if r[2] != GAP else r[2], (r[3], "orange") if r[3] != GAP else r[3], r[4], r[5], r[6]] for r in C_ROWS],
               w=W, theme="cyan", size=14, head_size=15, title="C   State plane: Standard-mode dependencies and your own knowledge stores", title_size=24)
    tc.place(cv, 0, y)
    y = learn_line(cv, 0, tc.bottom + 8, src("cosmos", "search", "storage", "kv", "dr")) + 30
    bands2 = [
        ("D   Edge and network: gateway, DNS, private endpoints", "indigo", D_ROWS, ("apim", "apim_mr", "ha", "arch")),
        ("E   Identity", "red", E_ROWS, ("entra", "entra_bk")),
        ("F   Tools and grounding", "orange", F_ROWS, ("tools", "bing", "known")),
    ]
    for title, theme, rows, cites in bands2:
        t = mtable(title, theme, rows)
        t.place(cv, 0, y)
        y = learn_line(cv, 0, t.bottom + 8, src(*cites)) + 30
    return y + 10


# ---------------------------------------------------------------------------------------------- 5. docs disagree + drills
def disagree(cv: Canvas, y: float) -> float:
    y = head(cv, y, 5, "Where the docs disagree: treat these cells cautiously",
             sub=f"Both sides are Microsoft Learn pages ({ASOF}). We did not pick a winner; verify in your own environment before you rely on a number.",
             tags=(("Docs disagree", "gray", False),))
    rows = [
        ["Storage GRS and GZRS for Foundry", "The high-availability page: Foundry projects don't support default storage account failover using GRS, GZRS, RA-GRS or RA-GZRS.",
         "The Agent Service DR pages require GZRS + customer-managed failover for the agent-state storage account.", "Follow the agent playbook for agent-state storage and test it before relying on it."],
        ["Cosmos DB failover timing", "Agent DR pages: the Cosmos team triggers service-managed failover; fail-back three or more days later; RTO 30+ min once triggered; up to 15 min data loss.",
         "The Cosmos reliability page: service-managed failover can take one hour or more; forced failover is recommended for faster recovery.", "Do not trust one number. Plan on the slower figure and drill with forced failover."],
        ["Cosmos DB standby sizing and restore", "Agent DR: five containers, each requiring 1,000 RU/s (3,000 RU/s or more in total). Architecture Center: always restore to the same account and database.",
         "Troubleshooting: 3,000 RU/s (1,000 x 3 containers). The high-availability page example restores to a new account name.", "Size the standby with the larger RU/s figure; decide the restore target per scenario and rehearse it."],
        ["AI Search recovery", "The Agent Service DR series: rebuild from IaC and source data.", "Architecture Center: contact Microsoft Support for index restoration.", "Keep the rebuild path; treat support restoration as a bonus."],
        ["Hosted-agent traffic splitting", "The hosted-agents concept page: traffic splitting between versions isn't supported. The Architecture Center baseline: no built-in blue-green or canary for agents.",
         "The preview 'Promote hosted agents to production' page documents FixedRatio canary rules.", "Plan for one version at 100% unless you verify weighted routing yourself (see B7)."],
        ["Diagnostic log latency", "The monitor-models page: diagnostic logs take up to 15 minutes.", "The diagnostic-logging page: up to two hours.", "Assume the slower figure for log-based alerts."],
    ]
    t = Table([("Topic", 260), ("One page says", 920), ("Another page says", 860), ("How to read it here (our reading)", 760)], rows, w=W, theme="gray", size=15,
              head_size=16, first_col_theme="gray")
    t.place(cv, 0, y)
    y = learn_line(cv, 0, t.bottom + 8, src("ha", "dr", "cosmos", "monitor", "hosted", "arch")) + 56
    return y


def drills(cv: Canvas, y: float) -> float:
    y = head(cv, y, 6, "Prove it before the incident: the failover drill",
             sub="Verify failover readiness on a regular schedule (the docs' example: quarterly). The five checks are documented; the loop is drawn as one cycle.",
             tags=(DOC,))
    steps = [
        ("Secondary is current", "secondary project, models and connections match the primary"),
        ("Run a real job", "a representative agent job in the secondary, including Cosmos DB, AI Search and Storage access"),
        ("RBAC is in place", "role assignments exist in the secondary"),
        ("Network works", "DNS and connectivity, including private endpoints and VPN"),
        ("Record the gaps", "write down what failed and update the IaC"),
    ]
    sw = 470
    sg = (W - 5 * sw) / 4
    bxs = []
    for i, (t, d) in enumerate(steps):
        b = Box(sw, f"{i + 1}  {t}", theme="green" if i < 4 else "violet", sub=d, size=20, sub_size=15, h=130).place(cv, i * (sw + sg), y)
        bxs.append(b)
    for a, b in zip(bxs, bxs[1:]):
        connect(cv, a, b, sw=3)
    ly = y + 130 + 46
    arrow(cv, [(bxs[0].cx, bxs[0].bottom + 8), (bxs[0].cx, ly), (bxs[4].cx, ly), (bxs[4].cx, bxs[4].bottom + 6)], dash="dashed",
          color="#6741d9", sw=3, start_head="arrow", end_head=None, label="repeat on a schedule (docs example: quarterly)",
          label_size=15, label_t=0.5, label_pos="below")
    cy_ = ly + 70
    lv = [
        Note(880, "API Management supports drills with disableGateway on a gateway.", kind="tip", title="Lever: APIM"),
        Note(880, "A Cosmos DB forced failover simulates a region being down.", kind="tip", title="Lever: Cosmos DB"),
        Note(880, "A Storage planned failover (RPO 0) can be used for DR drills.", kind="tip", title="Lever: Storage"),
    ]
    _, bb = row(cv, 0, cy_, lv, gap=(W - 3 * 880) / 2)
    cv.text(0, bb + 10, "Drill levers are documented on the service pages. Quarterly is the docs' example cadence; no monthly cadence is documented, so adapt it to your risk.", size=14, color=MUTED)
    return bb + 48


# ---------------------------------------------------------------------------------------------- 6. gotchas + sources
def gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, 7, "Gotchas and gaps", tags=(DOC,))
    nw = (W - 2 * 34) / 3
    notes = [
        Note(nw, "Zone-redundant configurations don't protect against full regional outages or human or automation errors. And Microsoft doesn't automatically notify you when a zone is down: wire Resource Health and Service Health alerts yourself.",
             kind="gotcha", title="Zones are not regions", src=src("ha", "cosmos", "kv")),
        Note(nw, "Storage RPO is 'not guaranteed' and the Cosmos DB failover timing differs between pages. A storage outage often cascades into everything downstream.",
             kind="warn", title="Do not over-trust numbers", src=src("storage", "drp")),
        Note(nw, "No Learn page documents DR or redundancy for the hosted-agent durable state store or the session $HOME and /files storage, or cross-region hosted-agent behaviour (" + ASOF + ").",
             kind="warn", title="Undocumented: hosted-agent state", src=src("state", "hosted")),
        Note(nw, "No published SLA statement was found for Agent Service or hosted agents, and the Grounding with Bing Search page has no HA statement. We print no SLA percentage here.",
             kind="warn", title="No SLA numbers", src=src("ha", "bing")),
        Note(nw, "The Notification Center is an in-portal feed (Defender alerts, policy and compliance, evaluation and training run completions). It is not a paging channel.",
             kind="info", title="Notification Center is not paging"),
        Note(nw, "Tool availability needs model and region support: check code interpreter and file search in the DR region before you choose it.",
             kind="tip", title="Choose the DR region by tool support", src=src("limits", "tools")),
    ]
    _, bb = grid(cv, 0, y, notes, 3, gap_x=34, gap_y=26)
    return bb + 52


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Failure modes and runbook",
                                f"Component x failure x detect x mitigate x owner: what breaks, how you see it, what you do and whose job recovery is ({ASOF})",
                                icon="foundry", w=W)
    y = legend_panel(cv, bottom + 36)
    y = summary_strip(cv, y)
    y = failure_map(cv, y)
    y = triage(cv, y)
    y = alert_pack(cv, y)
    y = matrices(cv, y)
    y = disagree(cv, y)
    y = drills(cv, y)
    y = gotchas(cv, y)
    sources(cv, 0, y, [
        S["health"], S["monitor"], S["known"], S["ha"], S["dr"], S["drp"], S["dro"], S["limits"], S["hosted"], S["lrr"],
        S["cosmos"], S["search"], S["kv"], S["apim_mr"],
    ], w=W, cols=3)
