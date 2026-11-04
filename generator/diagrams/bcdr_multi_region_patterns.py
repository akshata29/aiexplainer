"""Multi-region patterns for Foundry: the global entry, the gateway tier and a region pair; active/active and active/passive
topologies; PTU-to-Standard spillover; quota and capacity planning across regions. Part 2 covers retries, health probes, agent
state, IaC rebuild, cost levers and three failure walk-throughs."""
from __future__ import annotations

from generator.diagrams.ra_ai_gateway_pattern import (
    W, C, N, StepsCard, pill, _node, _frame, _pe, _wire, _mini_panel, RED, GREY)
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="bcdr-multi-region-patterns", title="Multi-region patterns", section="4", order=2,
    description="Region-pair topologies behind Front Door, Traffic Manager or API Management (active/active and active/passive), "
                "PTU-to-Standard spillover mechanics and quota planning across regions, drawn from the documented patterns.",
    tags=["bcdr", "multi-region", "spillover", "quota", "api-management", "front-door"],
)

AC = "azure/architecture"
S_HA = learn("how-to/high-availability-resiliency")
S_GW = learn("ai-ml/guide/azure-openai-gateway-multi-backend", base=AC)
S_BASE = learn("ai-ml/architecture/baseline-microsoft-foundry-chat", base=AC)
S_SPILL = learn("openai/how-to/spillover-traffic-management")
S_PTU = learn("openai/concepts/provisioned-throughput")
S_PTU_BILL = learn("openai/concepts/provisioned-throughput-billing")
S_PTU_START = learn("openai/how-to/provisioned-get-started")
S_QUOTA = learn("openai/how-to/quota")
S_DEP = learn("foundry-models/concepts/deployment-types")
S_HEALTH = learn("how-to/stay-informed-service-health")
S_AGENT_DR = learn("how-to/agent-service-disaster-recovery")
S_APIM_MR = learn("api-management/api-management-howto-deploy-multi-region", base="azure")
S_APIM_BACKENDS = learn("api-management/backends", base="azure")
S_APIM_CAP = learn("api-management/genai-gateway-capabilities", base="azure")
S_APIM_REL = learn("reliability/reliability-api-management", base="azure")
S_PLATFORM_DR = learn("how-to/agent-service-platform-disaster-recovery")
S_COSMOS_REL = learn("reliability/reliability-cosmos-db-nosql", base="azure")


# ====================================================================== 0. title and key messages
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Multi-region patterns for Foundry",
        "Gateway, spillover and quota across a region pair - what the docs document, and what is yours to build (facts as of 2026-11-03)",
        icon="regions", w=W)
    y = bottom + 36
    gap = 36
    cw = (W - 5 * gap) / 6
    cards = [
        C(cw, "No automatic cross-region failover", [
            "Foundry doesn't fail over for you: you create resources in two regions and switch to the other one",
            "A gateway or your application decides when",
        ], theme="red", icon="regions", src=[("High availability and resiliency", S_HA)]),
        C(cw, "Spillover is not failover", [
            "PTU -> Standard spillover happens inside one Foundry resource",
            "Cross-region traffic moves only through a gateway or your code",
            "No PTU-to-PTU failover is documented",
        ], theme="yellow", icon="quotas", src=[("Spillover for provisioned deployments", S_SPILL)]),
        C(cw, "Quota is per subscription and region", [
            "Standard quota: subscription x region x model x deployment type",
            "Load balancing standard instances in one subscription adds no throughput",
            "Quota is not capacity",
        ], theme="yellow", icon="quotas", src=[("Manage quota", S_QUOTA)]),
        C(cw, "Global and Data Zone are not a plan", [
            "They route inference inside their scope",
            "That 'doesn't replace application-level regional failover'",
            "The layer that processes API requests is regional to your resource",
        ], theme="blue", icon="openai", src=[("High availability and resiliency", S_HA)]),
        C(cw, "Gateways have limits too", [
            "A single-region gateway is a global single point of failure",
            "Multi-region API Management: Premium tier, one control plane",
            "Its status endpoint tests the gateway, not the model backend",
        ], theme="indigo", icon="apim", src=[("Multi-region deployment", S_APIM_MR)]),
        C(cw, "Agent state is yours", [
            "Agent Service doesn't replicate state: recovery is reconstruction",
            "Agent and thread IDs change on rebuild",
            "Keep IDs behind configuration or the gateway",
        ], theme="cyan", icon="cosmos", src=[("Agent Service disaster recovery", S_AGENT_DR)]),
    ]
    _, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    note = N(W, "Related canvases: 'Foundry high availability and resiliency' (the resilience stack, recovery strategies with RTO and RPO, deployment-type "
                "resiliency) and 'Agent Service disaster recovery'. The gateway footprint options are drawn in 'Hub AI gateway reference architecture'. "
                "This canvas covers the region-pair patterns, spillover, quota and the cost ladder; part 2 covers retries, health probes, three failure "
                "walk-throughs, agent state and rebuild with IaC.", kind="info", title="Where this canvas fits")
    note.place(cv, 0, y)
    y = note.bottom + 24
    legend(cv, 0, y, [("Clients and entry", "gray"), ("Global routing and networking", "indigo"), ("Gateway", "grape"), ("Models and deployments", "blue"),
                      ("Capacity, quota and cost", "yellow"), ("Agent state and data", "cyan"), ("Agents", "green"), ("Identity", "red"),
                      ("Observability", "violet")], size=15, gap=28)
    return y + 56


# ====================================================================== 1. the big picture
def _big(cv, y):
    _, hb = section_header(
        cv, 0, y, "1  The big picture: one global entry, a gateway tier, a region pair", size=32,
        sub="Solid = normal path  |  dashed orange = spillover inside one resource, or failover between regions  |  red dotted = not replicated for you")
    y = hb + 40

    # ---- entry band (row A) and gateway tier (row B), both centred over the region pair
    cl = _node(cv, 0, y + 30, 330, 140, "Clients and apps", "app", "gray", sub="call one FQDN", icon_pos="left", size=19, sub_size=15)
    EW = 1800
    ex = (W - EW) / 2
    with cv.panel(ex, y, w=EW, h=200, title="Global entry: pick by network type", theme="indigo", style="solid", fill="soft", pad=20, title_size=22) as ge:
        bw = (EW - 40 - 2 * 30) / 3
        _node(cv, ge.ix, ge.iy, bw, 104, "Azure Front Door", "front-door", "indigo", sub="public; needs a WAF; the gateway must not be bypassable",
              icon_pos="left", size=18, sub_size=13)
        _node(cv, ge.ix + bw + 30, ge.iy, bw, 104, "Traffic Manager", "traffic-manager", "indigo", sub="no WAF; DNS TTL is acceptable",
              icon_pos="left", size=18, sub_size=13)
        _node(cv, ge.ix + 2 * (bw + 30), ge.iy, bw, 104, "DNS record toggling", "dns", "indigo",
              sub="private networking: Azure has no native private global load balancer", icon_pos="left", size=18, sub_size=13)
    arrow(cv, [(cl.right + 6, y + 100), (ex - 8, y + 100)], sw=3, num=1, num_theme="indigo", label="one FQDN", label_size=15, label_pos="below",
          label_dy=14)
    how = C(W - ex - EW - 60, "How to read it", [
        "Numbers 1-6 follow the request path (steps card below)",
        "Solid = normal path",
        "Dashed orange = spillover or failover",
        "Red dotted = not replicated for you",
    ], theme="gray", fill="soft", title_size=18, body_size=15)
    how.place(cv, ex + EW + 60, y)
    gy = y + 200 + 100
    GWW = 1300
    gw = _node(cv, (W - GWW) / 2, gy, GWW, 150, "Generative AI gateway", "apim", "grape", icon_pos="left", size=24, sub_size=15, icon_size=44,
               sub="API Management multi-region or custom code: load balancing, circuit breaker honouring Retry-After, rate limiting, priority routing, central logging")
    arrow(cv, [(W / 2, y + 200 + 6), (W / 2, gy - 8)], sw=3, num=2, num_theme="indigo", label="a healthy gateway", label_size=15, label_pos="right")
    tier = C(gw.x - 60, "Gateway tier: pick one", [
        "API Management multi-region: a gateway per region and a built-in lowest-latency FQDN",
        "Custom code: one highly available scale unit per region behind Front Door or Traffic Manager",
        "API Management: at least 2 units across 2 zones; custom code: at least 3 instances",
    ], theme="grape", fill="soft", title_size=18, body_size=14, src=[("Gateway implementations", S_GW)])
    tier.place(cv, 0, gy)
    prob = C(W - gw.right - 60, "Probes and early warning", [
        "The status endpoint tests the gateway, not the model: add a dedicated health API",
        "Service Health and Resource Health alerts; Application Insights availability tests on agent endpoints",
    ], theme="violet", fill="soft", title_size=18, body_size=14, src=[("High availability and resiliency", S_HA)])
    prob.place(cv, gw.right + 60, gy)

    # ---- region pair
    ry = gy + 150 + 130
    RW, RH = 1430, 560
    xs = [0, W - RW]
    names = ["Region 1 (primary)", "Region 2 (secondary)"]
    sub_r = ["serves traffic today", "a full twin you build and keep in sync"]
    parts = []
    for i in range(2):
        with cv.panel(xs[i], ry, w=RW, h=RH, title=names[i], sub=sub_r[i], theme="gray", style="dotted", fill="none", pad=24, title_size=26,
                      sub_size=15) as rp:
            fw = 780
            dw = RW - 48 - fw - 50
            if i == 0:
                fx, dx = rp.ix + dw + 50, rp.ix
            else:
                fx, dx = rp.ix, rp.ix + fw + 50
            with cv.panel(fx, rp.iy + 4, w=fw, title="Foundry resource", sub="one resource per region", theme="blue", style="solid", fill="soft", pad=20,
                          title_size=22, sub_size=15) as fr:
                ptu = _node(cv, fr.ix, fr.iy, fw - 40, 104, "Provisioned (PTU) deployment", "openai", "blue", icon_pos="left", size=18,
                            sub="reserved capacity answers first; 429 at 100% utilization")
                std = _node(cv, fr.ix, ptu.bottom + 96, fw - 40, 104, "Standard deployment", "openai", "blue", icon_pos="left", size=18,
                            sub="same model and version; per-token overflow", dash="dashed", fill="soft")
            with cv.panel(dx, rp.iy + 4, w=dw, title="Agent Service dependencies", sub="standard setup: in your subscription", theme="cyan",
                          style="dashed", fill="soft", pad=20, title_size=22, sub_size=15) as dp:
                d1 = _node(cv, dp.ix, dp.iy, dw - 40, 86, "Azure Cosmos DB", "cosmos", "cyan", icon_pos="left", size=17,
                           sub="conversations and agent state")
                d2 = _node(cv, dp.ix, d1.bottom + 16, dw - 40, 86, "Azure AI Search", "ai-search", "teal", icon_pos="left", size=17,
                           sub="file and vector knowledge")
                d3 = _node(cv, dp.ix, d2.bottom + 16, dw - 40, 86, "Azure Storage", "storage", "cyan", icon_pos="left", size=17,
                           sub="files; failover is yours to run")
            _pe(cv, fx + fw / 2, ry + RH - 46, "private endpoint")
        parts.append(dict(rp=rp, fr=fr, ptu=ptu, std=std, dp=dp, deps=(d1, d2, d3)))
    p1, p2 = parts
    # arrows from the gateway to the PTU deployments (symmetric elbows)
    connect(cv, gw, p1["ptu"], a_side="bottom", b_side="top", ta=0.3, tb=0.5, route="elbow", sw=3, num=3, num_theme="grape", bend=0.2)
    connect(cv, gw, p2["ptu"], a_side="bottom", b_side="top", ta=0.7, tb=0.5, route="elbow", sw=3, bend=0.2)
    for p in parts:
        connect(cv, p["ptu"], p["std"], a_side="bottom", b_side="top", dash="dashed", sw=3, color="#f08c00", num=4, num_theme="yellow",
                label="spillover: same resource only", label_size=15, label_pos="right", label_wrap=240)
    # failover between regions
    connect(cv, p1["fr"], p2["fr"], a_side="right", b_side="left", ta=0.92, tb=0.92, sw=3, dash="dashed", color="#e8590c",
            num=5, num_theme="orange", label="failover: gateway logic, not a Foundry feature", label_size=15, label_wrap=300, label_pos="above",
            label_dy=-24)
    # foundry -> dependencies
    for p, side_a, side_b in ((p1, "left", "right"), (p2, "right", "left")):
        connect(cv, p["fr"], p["dp"], a_side=side_a, b_side=side_b, ta=0.5, tb=0.5, sw=2.5, num=6, num_theme="cyan")
    # not replicated
    by = ry + RH + 36
    d_left, d_right = p1["dp"], p2["dp"]
    arrow(cv, [(d_left.x + d_left.w / 2, d_left.bottom + 8), (d_left.x + d_left.w / 2, by), (d_right.x + d_right.w / 2, by),
               (d_right.x + d_right.w / 2, d_right.bottom + 8)], dash="dotted", color=RED, sw=3, start_head=None, end_head=None)
    mx = W / 2
    cv.line((mx - 14, by - 14), (mx + 14, by + 14), stroke=RED, sw=6)
    cv.line((mx - 14, by + 14), (mx + 14, by - 14), stroke=RED, sw=6)
    cv.text(mx - 600, by + 24, "Agent state, threads and files are not replicated between regions: recovery is reconstruction",
            size=16, color="#c92a2a", align="center", w=1200)
    return by + 80, gw


def _flow_notes(cv, y):
    wf = StepsCard(1500, "How a request moves (numbers match the diagram)", [
        (1, "Clients call one FQDN: Front Door when traffic is public and needs a WAF, Traffic Manager when it doesn't, DNS record toggling for private networking", "indigo"),
        (2, "The global router sends the call to a healthy gateway; probe the regional status endpoints (they test the gateway, not the model)", "indigo"),
        (3, "The gateway routes to the same-region Foundry resource first (lowest latency), PTU deployment before Standard", "grape"),
        (4, "A PTU that can't serve (429, long-context 400, 500 or 503) spills over to the Standard deployment in the same resource", "yellow"),
        (5, "A regional or model failure trips the gateway's circuit breaker and the request is retried on the other region: same model, same version", "orange"),
        (6, "Agent Service state lives in the dependencies of each region; nothing replicates it for you", "cyan"),
    ], theme_name="indigo", icon="workflow", src=[("High availability and resiliency", S_HA), ("Hub gateway topologies", S_GW)], gap=20)
    nx = 1500 + 40
    nw = (W - nx - 40) / 2
    n1 = N(nw, "Spillover lives inside one Foundry resource: it isn't a cross-region mechanism. Cross-region means a gateway, or application logic.",
           kind="gotcha", title="Spillover is not cross-region", src=[("Spillover for provisioned deployments", S_SPILL)])
    n1.place(cv, nx, y)
    n2 = N(nw, "Global and Data Zone deployments route inference across their permitted scope, but that 'doesn't replace application-level regional failover'. "
               "Use a gateway or application logic when you must switch between regional resource endpoints.",
           kind="gotcha", title="Global routing is not a failover plan", src=[("High availability and resiliency", S_HA)])
    n2.place(cv, nx + nw + 40, y)
    n3 = N(nw, "Failover targets must run the same model and version (never X -> X+1) and are easier to route to when the deployment name is the same on every instance.",
           kind="warn", title="Same model, same version", src=[("Gateway tips", S_GW + "#tips-for-the-multiple-instances-in-a-single-region-and-single-subscription-topology")])
    n3.place(cv, nx, max(n1.bottom, n2.bottom) + 24)
    n4 = N(nw, "If a region is down the survivor must carry 100% of the traffic: over-provision PTU in each region, or fail PTU over to Standard.",
           kind="warn", title="The survivor absorbs everything", src=[("Multi-region API Management", S_GW + "#use-api-management-multi-region-deployment")])
    n4.place(cv, nx + nw + 40, max(n1.bottom, n2.bottom) + 24)
    ry = max(n3.bottom, n4.bottom) + 24
    n5 = N(nw, "With stateful features such as the Assistants API, pin a client to one backend during the interaction, for example by storing instance data in a cookie. "
               "Consider returning a 429 to a pinned client instead of re-routing it to an instance that has no history: the client then handles the unavailability explicitly.",
           kind="info", title="Pin stateful sessions",
           src=[("Stateful interactions", S_GW + "#stateful-interactions")])
    n5.place(cv, nx, ry)
    n6 = N(nw, "Don't add a unified gateway just to raise quota (use Global Standard), when the model and version aren't in every region, or across geopolitical "
               "boundaries when data residency applies: run one isolated gateway stack per boundary.", kind="tip", title="When not to unify",
           src=[("Reasons to avoid a gateway across regions", S_GW + "#reasons-to-avoid-a-gateway-for-multiple-instances-in-multiple-regions")])
    n6.place(cv, nx + nw + 40, ry)
    wf.place(cv, 0, y, h=max(n5.bottom, n6.bottom) - y)
    return max(wf.bottom, n5.bottom, n6.bottom) + 70


# ====================================================================== 2. region-pair patterns
PH2 = 700
PE2 = 526
FD2 = 592


def _pat_panel(cv, x, y, title, sub, th_name):
    _mini_panel(cv, x, y, 740, PH2, title, sub, th_name)


def _two_regions(cv, x, y, g1, g2, *, passive2=False, label2=None, sub_f="PTU + standard", cross=False):
    """Gateway pair -> private endpoints -> Foundry pair, shared by the active/active and active/passive patterns."""
    pe1 = _pe(cv, g1.cx, y + PE2, "private endpoint")
    pe2 = _pe(cv, g2.cx, y + PE2, "private endpoint")
    f1 = _node(cv, x + 56, y + FD2, 300, 70, "Foundry - region 1", "foundry", "blue", sub=sub_f, icon_pos="left")
    f2 = _node(cv, x + 384, y + FD2, 300, 70, "Foundry - region 2", "foundry", "blue", sub=label2 or sub_f, icon_pos="left",
               dash="dashed" if passive2 else "solid", fill="soft" if passive2 else "solid")
    _wire(cv, g1, pe1, a_side="bottom", b_side="top")
    _wire(cv, g2, pe2, a_side="bottom", b_side="top", passive=passive2)
    _wire(cv, pe1, f1, a_side="bottom", b_side="top")
    _wire(cv, pe2, f2, a_side="bottom", b_side="top", passive=passive2)
    return f1, f2


def _m1(cv, x, y):
    _pat_panel(cv, x, y, "1  Active/active, public", "Front Door in front of API Management in both regions", "green")
    cl = _node(cv, x + 295, y + 84, 150, 68, "Clients", "app", "gray")
    fd = _node(cv, x + 190, y + 190, 360, 76, "Azure Front Door", "front-door", "indigo", sub="public global router with a WAF", icon_pos="left")
    _frame(cv, x + 30, y + 336, 680, 134, "API Management", "green", dash="solid")
    g1 = _node(cv, x + 56, y + 380, 300, 70, "Gateway - region 1", "apim", "grape", icon_pos="left")
    g2 = _node(cv, x + 384, y + 380, 300, 70, "Gateway - region 2", "apim", "grape", icon_pos="left")
    _wire(cv, cl, fd, a_side="bottom", b_side="top")
    _wire(cv, fd, g1, a_side="bottom", b_side="top", route="elbow", ta=0.3, bend=0.3)
    _wire(cv, fd, g2, a_side="bottom", b_side="top", route="elbow", ta=0.7, bend=0.3)
    _two_regions(cv, x, y, g1, g2)


def _m2(cv, x, y):
    _pat_panel(cv, x, y, "2  Active/passive, public", "region 2 stays warm or cold until it is needed", "orange")
    cl = _node(cv, x + 295, y + 84, 150, 68, "Clients", "app", "gray")
    tm = _node(cv, x + 190, y + 190, 360, 76, "Front Door or Traffic Manager", "traffic-manager", "indigo", sub="public global router in active/passive mode", icon_pos="left")
    _frame(cv, x + 30, y + 336, 680, 134, "Gateway tier", "orange", dash="solid")
    g1 = _node(cv, x + 56, y + 380, 300, 70, "Gateway - region 1", "apim", "grape", sub="API Management or custom", icon_pos="left")
    g2 = _node(cv, x + 384, y + 380, 300, 70, "Gateway - region 2", "apim", "grape", sub="API Management or custom", icon_pos="left", dash="dashed", fill="soft")
    _wire(cv, cl, tm, a_side="bottom", b_side="top")
    _wire(cv, tm, g1, a_side="bottom", b_side="top", route="elbow", ta=0.3, bend=0.3)
    _wire(cv, tm, g2, a_side="bottom", b_side="top", route="elbow", ta=0.7, bend=0.3, passive=True)
    _two_regions(cv, x, y, g1, g2, passive2=True, label2="warm: models deployed; or cold")


def _m3(cv, x, y):
    _pat_panel(cv, x, y, "3  One gateway region", "models in two regions behind a single gateway region", "red")
    cl = _node(cv, x + 295, y + 84, 150, 68, "Clients", "app", "gray")
    _frame(cv, x + 170, y + 214, 400, 214, "", "red", fill="none")
    cv.text(x + 392, y + 178, "global single point of failure", size=16, color="#c92a2a")
    g = _node(cv, x + 220, y + 270, 300, 104, "API Management", "apim", "grape", sub="one region", icon_pos="left")
    pe1 = _pe(cv, x + 190, y + PE2, "private endpoint")
    pe2 = _pe(cv, x + 550, y + PE2, "private endpoint")
    f1 = _node(cv, x + 40, y + FD2, 300, 70, "Foundry - region 1", "foundry", "blue", sub="active: the gateway's own region", icon_pos="left")
    f2 = _node(cv, x + 400, y + FD2, 300, 70, "Foundry - region 2", "foundry", "blue", sub="standard passive host, or active", icon_pos="left",
               dash="dashed", fill="soft")
    _wire(cv, cl, g, a_side="bottom", b_side="top")
    _wire(cv, g, pe1, a_side="bottom", b_side="top", route="elbow", ta=0.25)
    _wire(cv, g, pe2, a_side="bottom", b_side="top", route="elbow", ta=0.75, passive=True, label="cross-region: latency + egress", label_size=14,
          label_wrap=190, label_pos="left", label_t=0.78)
    _wire(cv, pe1, f1, a_side="bottom", b_side="top")
    _wire(cv, pe2, f2, a_side="bottom", b_side="top", passive=True)


def _m4(cv, x, y):
    _pat_panel(cv, x, y, "4  Private networking", "no native private global load balancer", "indigo")
    cl = _node(cv, x + 120, y + 84, 500, 76, "Hybrid network", "expressroute", "gray", sub="ExpressRoute or VPN that survives a region loss",
               icon_pos="left")
    dn = _node(cv, x + 190, y + 196, 360, 76, "DNS record toggling", "dns", "indigo", sub="active/passive through the gateway endpoint record",
               icon_pos="left")
    _frame(cv, x + 30, y + 336, 680, 134, "Gateway tier", "indigo", dash="solid")
    g1 = _node(cv, x + 56, y + 380, 300, 70, "Gateway - region 1", "apim", "grape", sub="API Management or custom", icon_pos="left")
    g2 = _node(cv, x + 384, y + 380, 300, 70, "Gateway - region 2", "apim", "grape", sub="API Management or custom", icon_pos="left", dash="dashed", fill="soft")
    _wire(cv, cl, dn, a_side="bottom", b_side="top")
    _wire(cv, dn, g1, a_side="bottom", b_side="top", route="elbow", ta=0.3, bend=0.3)
    _wire(cv, dn, g2, a_side="bottom", b_side="top", route="elbow", ta=0.7, bend=0.3, passive=True)
    _two_regions(cv, x, y, g1, g2, passive2=True, sub_f="a private endpoint per instance")


def _patterns(cv, y):
    _, hb = section_header(
        cv, 0, y, "2  Active/active and active/passive: four region-pair patterns", size=32,
        sub="Two Foundry resources behind Front Door, Traffic Manager or API Management. Solid = active, dashed = passive or standby. "
            "Hot/hot, hot/warm and hot/cold are defined in 'Foundry high availability and resiliency'")
    y = hb + 36
    xs = [0, 820, 1640, 2460]
    for fn, x in zip((_m1, _m2, _m3, _m4), xs):
        fn(cv, x, y)
    cy = y + PH2 + 20
    SRC_HA = [("High availability and resiliency", S_HA)]
    cols = [
        (["Production workloads with zero-downtime targets (hot/hot): approximate RTO in minutes",
          "Front Door fails traffic over automatically when a region becomes unavailable"],
         ["The surviving region must absorb 100% of the traffic: over-provision PTU or add active-passive hosts",
          "Clients must honour the DNS TTL and retry after a DNS failover"], SRC_HA),
        (["Business-critical workloads that can tolerate a brief disruption (hot/warm) or have relaxed targets (hot/cold)",
          "Cheaper: the secondary holds critical resources only, or is provisioned but inactive"],
         ["Approximate RTO per the HA page: 30 minutes to 2 hours (hot/warm), 2 to 8 hours (hot/cold)",
          "In a cold secondary you deploy models, deployments and pipelines by hand",
          "Traffic Manager has no WAF; probe the regional status endpoints, and the API Management page suggests the Priority routing method for traffic control during maintenance"],
         [("High availability and resiliency", S_HA), ("Custom routing to regional gateways", S_APIM_MR + "#use-custom-routing-to-api-management-regional-gateways")]),
        (["Protects against a regional model-endpoint outage",
          "Active-passive: normal traffic stays in the gateway's region and falls back to another region's standard deployment"],
         ["A global single point of failure: any gateway outage makes every region inaccessible; not for business-critical workloads",
          "Needs cross-region network line of sight; adds latency and egress charges",
          "Not usable for data residency across a geopolitical boundary"], [("Single-region gateway", S_GW + "#use-api-management-single-region-deployment")]),
        (["Organizations with hybrid connectivity that consume the service over a private network",
          "A private endpoint per Foundry instance in each region"],
         ["Hybrid connectivity must itself survive the loss of a region",
          "Use split-brain Private DNS when all traffic goes through the gateway; update Private DNS records by hand if direct access is needed",
          "Active/passive means toggling DNS records"], SRC_HA),
    ]
    bottoms = []
    for (good, watch, src), x in zip(cols, xs):
        c1 = C(740, "Good for", ["+ " + g for g in good], theme="green", src=src)
        c1.place(cv, x, cy)
        c2 = C(740, "Watch out", ["! " + w for w in watch], theme="red")
        c2.place(cv, x, c1.bottom + 18)
        bottoms.append(c2.bottom)
    y = max(bottoms) + 44

    rows = [
        [("A  One gateway region", "red"), "One API Management region. Active-active load balancing across regions, or active-passive: normal traffic goes to the same-region instance and fails over to a standard deployment in another region",
         "Protects against a regional model-endpoint outage",
         "A global single point of failure: any gateway outage makes every region inaccessible; not for business-critical workloads. Cross-region latency and egress; not for data sovereignty across a geopolitical boundary"],
        [("B  API Management multi-region", "green"), "One API Management instance with a gateway in each region, each reaching its own region's private endpoint. The built-in FQDN routes on lowest latency and around an outage",
         "No global traffic-handling single point of failure; disable a regional gateway to rehearse a DR drill",
         "Premium tier (classic): see the multi-region page. The control plane and developer portal stay in the primary region. Survivors must absorb 100%. Policy needs region conditionals; honour DNS TTL"],
        [("C  B plus active-passive hosts", "green"), "Each gateway can also reach the other region's endpoint and fail over from provisioned to standard. Only two private endpoints are needed",
         "'Can significantly increase the reliability'; the passive standard deployment is cost-effective",
         "Same data-residency warning across geopolitical boundaries"],
        [("D  Custom-coded gateway", "gray"), "Container Apps or similar: one highly available scale unit per region behind Azure Front Door (WAF, public) or Traffic Manager (no WAF, DNS TTL is enough), with latency-based routing and health checks",
         "Routing rules too complex for API Management policy",
         "Block bypass: private endpoints behind Front Door and validate X_AZURE_FDID; per-region resource groups; at least 3 instances across zones"],
        [("E  Foundry HA page variants", "indigo"), "Public: Front Door -> API Management instances in several regions (or the multi-region feature) -> Azure OpenAI per region. Private: resilient hybrid connectivity, a Private Link endpoint per instance per region, split-brain Private DNS, DNS toggling for active/passive",
         "Public variant: automatic failover when a region is unavailable",
         "No native private global load balancer; Private DNS records must be updated by hand when direct access is needed"],
    ]
    t = Table([("Documented pattern", 280), ("What it is", 1180), ("Strength", 640), "Watch out"], rows, w=W, theme="indigo", size=15, head_size=16,
              first_col_theme="indigo", title="The documented patterns, as written (A to D from the gateway article, E from the Foundry HA page)", title_size=22)
    t.place(cv, 0, y)
    ly = t.bottom + 10
    x = 0
    for label, url in (("Use a gateway in front of multiple model deployments or instances", S_GW), ("High availability and resiliency", S_HA),
                       ("Deploy API Management to multiple regions", S_APIM_MR)):
        tt = cv.text(x, ly, f"Learn: {label}", size=12, color=LINK, link=url)
        x += tt.w + 28
    return ly + 60


# ====================================================================== 3. PTU, Standard and spillover
def _spike_chart(cv, x, y, w, h):
    levels = [0.55, 0.75, 0.65, 1.35, 0.85, 1.7, 1.0, 0.6]
    n = len(levels)
    bw = (w - 40) / n - 12
    base = y + h
    unit = h * 0.5
    cv.line((x, y), (x, base), stroke=INK, sw=2)
    cv.line((x, base), (x + w, base), stroke=INK, sw=2)
    for i, lv in enumerate(levels):
        bx = x + 24 + i * (bw + 12)
        total = lv * unit
        served = min(total, unit)
        cv.rect(bx, base - served, bw, served, stroke="#1971c2", fill="#a5d8ff", style="solid", sw=2, round_=False)
        if total > unit:
            cv.rect(bx, base - total, bw, total - unit, stroke="#f08c00", fill="#ffec99", style="solid", sw=2, round_=False)
    cv.line((x, base - unit), (x + w, base - unit), stroke="#1971c2", sw=2.5, dash="dashed")
    cv.text(x + 8, base - unit - 24, "PTU capacity", size=15, color="#1864ab")


def _ptu_chain(cv, x, y, w):
    h = 620
    _mini_panel(cv, x, y, w, h, "PTU placement and the failover chain", "your gateway or application does the failing over; spillover works only inside one resource", "yellow")
    gw = _node(cv, x + 24, y + 260, 230, 150, "Gateway or app", "apim", "grape", sub="failover chain you configure")
    fa = _frame(cv, x + 380, y + 100, 560, 220, "Region A: workload-dedicated PTU", "blue", icon="foundry", dash="solid")
    pa = _node(cv, x + 404, y + 146, 512, 60, "Workload PTU deployment", "openai", "blue", icon_pos="left", icon_size=26, size=16)
    sa = _node(cv, x + 404, y + 246, 512, 54, "Standard deployment (same resource)", None, "blue", dash="dashed", fill="soft", size=15)
    fb = _frame(cv, x + 380, y + 350, 560, 220, "Region B: enterprise PTU pool", "blue", icon="foundry", dash="solid")
    pb = _node(cv, x + 404, y + 396, 512, 60, "Data Zone PTU deployment behind the gateway", "openai", "blue", icon_pos="left", icon_size=26, size=16)
    sb = _node(cv, x + 404, y + 496, 512, 54, "Standard deployment (same resource)", None, "blue", dash="dashed", fill="soft", size=15)
    _wire(cv, gw, pa, a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow", num=1, num_theme="grape")
    _wire(cv, gw, pb, a_side="right", b_side="left", ta=0.7, tb=0.5, route="elbow", passive=True, num=2, num_theme="orange")
    cv.text(x + 262, y + 440, "failover: your\ngateway or app", size=14, color="#c2410c")
    for p, s in ((pa, sa), (pb, sb)):
        connect(cv, p, s, a_side="bottom", b_side="top", dash="dashed", sw=2.5, color="#f08c00", gap=2, label="spillover", label_size=14, label_pos="right")
    # no automatic PTU-to-PTU
    xm = x + 990
    arrow(cv, [(xm, y + 176), (xm, y + 426)], dash="dashed", color=RED, sw=3, end_head="arrow")
    cv.line((xm - 14, y + 286), (xm + 14, y + 316), stroke=RED, sw=6)
    cv.line((xm - 14, y + 316), (xm + 14, y + 286), stroke=RED, sw=6)
    cv.text(xm + 22, y + 272, "no automatic\nPTU-to-PTU\nfailover", size=14, color="#c92a2a")
    kx = x + 1200
    cv.text(kx, y + 110, "Order of attempts", size=19, color="#a16207")
    for i, (n, th_n, txt) in enumerate((
            (1, "grape", "First choice: the workload-dedicated PTU deployment"),
            (2, "orange", "Fallback you configure: the enterprise pool, or a Standard deployment"))):
        ky = y + 160 + i * 100
        numbered(cv, kx + 15, ky + 15, n, theme=th_n, d=30, size=17)
        cv.text(kx + 46, ky, txt, size=15, color=INK, wrap=240)
    return h


def _spillover_flow(cv, x, y, w):
    h = 620
    _mini_panel(cv, x, y, w, h, "Spillover: what happens to one request", "provisioned first, then the standard deployment in the same Foundry resource", "yellow")
    cv.text(x + 24, y + 104, "Spillover starts when the provisioned deployment returns one of these:", size=16, color=INK)
    ChipFlow(["429: PTUs exhausted", "400: long-context request", "500 or 503: server error"], 800, theme="yellow", size=15, fill="soft").place(cv, x + 24, y + 136)
    oy = 100
    rq = _node(cv, x + 24, y + 200 + oy, 150, 90, "Request", "app", "gray", size=17)
    pt = _node(cv, x + 220, y + 200 + oy, 220, 90, "PTU deployment", "openai", "blue", sub="answers first", icon_pos="left", size=17)
    cv.diamond(x + 500, y + 150 + oy, 270, 190, stroke="#f08c00", fill="#fff9db", style="solid", sw=2)
    cv.text(x + 500, y + 224 + oy, "PTU can serve?", size=18, color="#e67700", align="center", w=270)
    ok = _node(cv, x + 860, y + 90 + oy, 330, 100, "Served by the PTU", "quotas", "yellow", sub="only the hourly PTU cost applies", icon_pos="left", size=17)
    sd = _node(cv, x + 860, y + 270 + oy, 330, 120, "Standard deployment", "openai", "blue", sub="same resource; billed at input, cached and output token rates",
               icon_pos="left", size=17, dash="dashed", fill="soft")
    hd = _node(cv, x + 1240, y + 240 + oy, w - 1240 - 24, 180, "Response headers", "api", "gray", icon_pos="top", size=17, sub_size=13,
               sub="x-ms-spillover-from-deployment: the PTU name; x-ms-deployment-name: who served; x-ms-spillover-error: the code that triggered it")
    _wire(cv, rq, pt, a_side="right", b_side="left")
    arrow(cv, [(pt.right + 6, pt.cy), (x + 494, pt.cy)], sw=2.5)
    arrow(cv, [(x + 770, y + 190 + oy), (x + 860, y + 140 + oy)], sw=2.5, label="yes", label_size=15, label_pos="above")
    arrow(cv, [(x + 770, y + 300 + oy), (x + 856, y + 320 + oy)], sw=2.5, color="#f08c00", label="no", label_size=15, label_pos="below")
    _wire(cv, sd, hd, a_side="right", b_side="left")
    cv.text(x + 24, y + 556, "If the standard deployment also fails, its status and body come back with the spillover headers still present.", size=15,
            color=INK, wrap=1100)
    return h


def _ptu_spill(cv, y):
    _, hb = section_header(
        cv, 0, y, "3  PTU, Standard and spillover: capacity inside a region versus failover between regions", size=32,
        sub="Stack PTU for baseline demand and Standard for spikes; place pools in different regions; spillover is not a cross-region feature")
    y = hb + 36
    LW = 1500
    _ptu_chain(cv, 0, y, LW)
    RX = LW + 60
    _spillover_flow(cv, RX, y, W - RX)
    y += 620 + 30
    # baseline + spikes chart and recipe cards
    ch_h = 200
    PB = ch_h + 150
    _mini_panel(cv, 0, y, 760, PB, "PTU baseline, Standard spikes", "illustrative shape: no numbers", "blue")
    _spike_chart(cv, 40, y + 110, 680, ch_h)
    pills_y = y + 110 + ch_h + 14
    pill(cv, 40, pills_y, "served by PTU", "blue", size=14)
    pill(cv, 200, pills_y, "overflow served by Standard", "yellow", size=14)
    c1 = C(1340, "Enterprise PTU pool and workload-dedicated PTU", [
        "# Enterprise pool",
        "One Data Zone PTU deployment behind API Management, set up like a 'private Standard deployment' that protects against noisy neighbours",
        "The gateway controls priority, throughput limits, logging and failover logic; traffic smoothing lifts utilization",
        "Place it in a different region than your primary Standard Zone deployment",
        "# Workload-dedicated PTU",
        "Place it in a different region than the enterprise pool, for example workload pool in region A and enterprise pool in region B",
        "Configure the failover chain in your gateway or application; fall back to the enterprise pool or a Standard deployment",
        "! Don't assume automatic PTU-to-PTU failover: only spillover from PTU to a Standard deployment is documented",
    ], theme="blue", icon="openai", src=[("High availability and resiliency", S_HA)], min_h=ch_h + 150)
    c1.place(cv, 820, y)
    c2 = C(W - 820 - 1340 - 60, "Standard deployments", [
        "Default to Data Zone (US or EU); prefer Global Standard when residency allows",
        "Create one deployment per model in the primary region and duplicate it in the secondary when you need separate regional endpoints",
        "Size each deployment: the full available quota isn't independently available to every deployment",
        "Standard deployments run in one region with no availability-zone support; for multi-datacenter availability use a global or data zone deployment",
        "Architecture Center baseline: deploy a data zone provisioned and a data zone standard model with spillover for excess traffic or failures; use global deployments for maximum resilience when latency and geography allow",
        "! Foundry has no advanced load balancing or failover, such as round-robin or a circuit breaker, for model deployments: build it in a gateway",
    ], theme="blue", icon="openai", src=[("High availability and resiliency", S_HA), ("Baseline chat architecture", S_BASE)], min_h=ch_h + 150)
    c2.place(cv, 820 + 1340 + 60, y)
    y = max(y + ch_h + 150, c1.bottom, c2.bottom) + 36

    rowsL = [
        [("Purpose", "yellow"), "Route overage requests from a provisioned deployment to a corresponding standard deployment automatically; optional"],
        [("Triggers", "yellow"), "429 when PTUs are used up; 400 for a long-context request (for example gpt-4.1 series: PTU supports context under 128K); 500 or 503 server errors"],
        [("Prerequisites", "yellow"), "A provisioned managed deployment and a standard deployment of the same model and version in the same Foundry resource (at least one active pay-as-you-go deployment that matches); Cognitive Services Contributor or higher"],
        [("Enable for all requests", "yellow"), "Deployment property spilloverDeploymentName = the standard deployment's name (the REST example uses API 2024-10-01 and SKU GlobalProvisionedManaged), or the portal's Traffic spillover toggle in Custom settings"],
        [("Enable per request", "yellow"), "Header x-ms-spillover-deployment: <standard deployment>; without it no spillover happens. If both are set the deployment property wins"],
    ]
    rowsR = [
        [("Identify spilled requests", "yellow"), "Response headers x-ms-spillover-from-deployment (the PTU name), x-ms-deployment-name (the deployment that served) and x-ms-spillover-error (the code that triggered it, present even if the attempt fails)"],
        [("Monitor", "yellow"), "Azure Monitor metric Azure OpenAI Requests split by ModelDeploymentName and StatusCode; split by IsSpillover to see spilled requests on the standard deployment, counted with their final status and not double-counted as 429 on the PTU"],
        [("Cost", "yellow"), "PTU-served requests: only the hourly provisioned cost. Spilled requests: standard input, cached and output token rates"],
        [("Scope", "yellow"), "All Azure OpenAI models that support PTU; Foundry Models from other providers (Azure DeepSeek, Meta Llama) don't currently support spillover; works with Foundry Agent Service. The docs recommend enabling it for all global and data zone provisioned deployments"],
        [("Note", "yellow"), "The service tries the provisioned deployment first and only then spills over, which might add latency"],
    ]
    half = (W - 50) / 2
    tl = Table([("Spillover facts (1)", 230), "As documented (as of 2026-11-03)"], rowsL, w=half, theme="yellow", size=15, head_size=16, first_col_theme="yellow")
    tl.place(cv, 0, y)
    tr = Table([("Spillover facts (2)", 230), "As documented (as of 2026-11-03)"], rowsR, w=half, theme="yellow", size=15, head_size=16, first_col_theme="yellow")
    tr.place(cv, half + 50, y)
    ly = max(tl.bottom, tr.bottom) + 10
    cv.text(0, ly, "Learn: Manage traffic with spillover for provisioned deployments", size=12, color=LINK, link=S_SPILL)
    cv.text(560, ly, "Learn: What is provisioned throughput for Foundry Models?", size=12, color=LINK, link=S_PTU)
    return ly + 60


# ====================================================================== 4. quota and capacity
def _quota(cv, y):
    _, hb = section_header(
        cv, 0, y, "4  Quota and capacity across regions", size=32,
        sub="Quota is a policy limit per subscription and region; capacity is what the region can actually give you. Plan both before you need a second region")
    y = hb + 36
    LW = 1560
    cw_, ch_ = 740, 300
    _mini_panel(cv, 0, y, LW, 2 * ch_ + 150, "Where quota lives", "each cell is a separate pool", "yellow")
    cells = {}
    for r, sub_name in enumerate(("Subscription A", "Subscription B")):
        for c, reg in enumerate(("Region 1", "Region 2")):
            cx = 24 + c * (cw_ + 52)
            cy = y + 100 + r * (ch_ + 50)
            _frame(cv, cx, cy, cw_, ch_, f"{sub_name} - {reg}", "yellow", dash="solid", title_size=19)
            b1 = _node(cv, cx + 20, cy + 54, cw_ - 40, 70, "Standard TPM", "quotas", "yellow", sub="per model and deployment type", icon_pos="left", size=17,
                       sub_size=13)
            b2 = _node(cv, cx + 20, cy + 134, cw_ - 40, 70, "PTU quota", "quotas", "yellow", sub="Global, Data Zone and Regional are separate pools", icon_pos="left",
                       size=17, sub_size=13)
            b3 = _node(cv, cx + 20, cy + 214, cw_ - 40, 62, "Capacity", "regions", "red", sub="not guaranteed by quota", icon_pos="left", size=17, sub_size=13,
                       dash="dashed", fill="soft")
            cells[(r, c)] = (cx, cy)
    # annotations between cells
    ax = 24 + cw_ + 26
    ay = y + 100 + ch_ / 2
    arrow(cv, [(ax - 22, ay), (ax + 22, ay)], dash="dashed", color="#e8590c", sw=3, start_head="arrow", end_head="arrow")
    cv.text(24, y + 100 + 2 * ch_ + 62, "A gateway can only fail over to quota you have already allocated in the other region. A second subscription adds Standard quota in the same region.",
            size=15, color=INK, wrap=LW - 80)
    x2 = LW + 60
    wc = (W - x2 - 40) / 2
    facts = [
        C(wc, "Standard quota", [
            "TPM per subscription x region x model x deployment type; RPM follows from TPM by a model-specific ratio (for example older chat models: 1 unit = 6 RPM and 1,000 TPM; o3: 1 unit = 1 RPM and 1,000 TPM)",
            "Changes can take up to 15 minutes to propagate; up to 30 resources per region",
            "Increase requests are handled in the order received, with priority to customers who actively use their quota; partner and community models mostly can't get increases (Anthropic can)",
            "Load balancing standard instances in one subscription adds no throughput",
        ], theme="yellow", icon="quotas", src=[("Manage quota", S_QUOTA)]),
        C(wc, "PTU quota and capacity", [
            "PTU quota is per subscription x region x deployment type; Global, Data Zone and Regional are separate pools",
            "! Quota doesn't guarantee capacity: a deployment fails when the region is short; capacity changes through the day",
            "Scaling down releases capacity permanently",
            "Check with the Model Capacities API and the portal (it lists alternative regions); quota requests can take several days",
        ], theme="yellow", icon="quotas", src=[("Provisioned throughput", S_PTU), ("Get started with provisioned deployments", S_PTU_START)]),
        C(wc, "The HA rule", [
            "Allocate full quota to both the primary and the secondary deployment; verify with az cognitiveservices account list-usage",
            "If one region of an active-active pair fails the survivor carries 100%: over-provision PTU or fail PTU over to Standard",
            "Failover targets must use the same model and version",
        ], theme="red", icon="service-health", src=[("High availability and resiliency", S_HA)]),
        C(wc, "Gateway token budgets are regional", [
            "In a multi-region API Management deployment the llm-token-limit and azure-openai-token-limit policies count tokens separately at each regional gateway",
            "Their counters are not aggregated: size each region's budget on its own",
        ], theme="grape", icon="apim", src=[("Deploy API Management to multiple regions", S_APIM_MR)]),
        C(wc, "Reservations", [
            "Bought per deployment type: Global, Data Zone and Regional are separate purchases",
            "A Global reservation isn't region-specific and can cover Global PTU deployments in several regions; Data Zone and Regional reservations must match the deployment's region",
            "Reservations don't guarantee capacity: deploy first, then buy",
        ], theme="yellow", icon="reservations", src=[("PTU billing and reservations", S_PTU_BILL)]),
        C(wc, "429s are not all quota", [
            "Rate limit exceeded: raise TPM, rebalance quota or request an increase",
            "System capacity throttling: retry after retry-after-ms",
            "Temporary rate-limit adjustment on shared Standard pools: the effective x-ratelimit-limit-tokens is below your TPM; usually clears within hours",
            "Sustained 429s below approved quota in production: open a support request",
        ], theme="orange", icon="alerts", src=[("Manage quota", S_QUOTA)]),
    ]
    hts = []
    colb = [y, y]
    for i, f in enumerate(facts):
        col = i % 2
        f.place(cv, x2 + col * (wc + 40), colb[col])
        colb[col] = f.bottom + 24
    return max(max(colb), y + 2 * ch_ + 150) + 70


# ====================================================================== 5. cost ladder
def _cost(cv, y):
    _, hb = section_header(
        cv, 0, y, "5  The cost ladder: what readiness costs", size=32,
        sub="Qualitative: the docs give no prices. Recovery targets are approximate and depend on deployment size, services in use and replication configuration")
    y = hb + 36
    LW = 1560
    PHT = 560
    with cv.panel(0, y, w=LW, title="Three strategies, ordered by cost and recovery speed", sub="approximate targets from the HA page", theme="yellow",
                  style="dotted", fill="none", pad=24, title_size=24, sub_size=15) as lp:
        steps = [
            ("Hot/cold", "gray", 250, "RTO 2 to 8 hours", "RPO hours, depending on backup frequency",
             "Lowest cost: resources provisioned but not active; deploy models, deployments and pipelines by hand", "development, staging or cost-sensitive workloads"),
            ("Hot/warm", "yellow", 340, "RTO 30 minutes to 2 hours", "RPO minutes to hours, depending on replication lag",
             "Moderate cost: critical resources (for example deployed models) running, others on standby", "business-critical workloads that tolerate a brief disruption"),
            ("Hot/hot", "red", 430, "RTO minutes", "RPO near zero",
             "Highest cost: full duplicate resources running in both regions; PTU is billed hourly per deployed PTU regardless of use", "zero-downtime production workloads"),
        ]
        bw = 460
        base = lp.iy + PHT
        for i, (nm, th_, hh, rto, rpo, cost, best) in enumerate(steps):
            sx = lp.ix + i * (bw + 20)
            t = get_theme(th_)
            cv.rect(sx, base - hh, bw, hh, stroke=t.stroke, fill=t.fill, style="hachure", sw=2)
            cv.text(sx + 16, base - hh + 12, nm, size=26, color=t.deep)
            cv.text(sx + 16, base - hh + 50, rto + "\n" + rpo, size=15, color=INK, wrap=bw - 32)
            cv.text(sx + 16, base - hh + 112, cost, size=15, color=INK, wrap=bw - 32)
            cv.text(sx + 16, base - 54, "best for: " + best, size=14, color=MUTED, wrap=bw - 32)
        arrow(cv, [(lp.ix + 20, base + 30), (lp.ix + 3 * bw + 40, base + 30)], sw=3, color=GREY)
        cv.text(lp.ix + 20, base + 40, "more cost, faster recovery", size=15, color=MUTED)
    CX = LW + 50
    CW = W - CX
    half = (CW - 30) / 2
    levers = [
        C(half, "Standard standby and spillover", [
            "A passive Standard deployment costs per token only when it serves traffic",
            "Spillover: pay Standard rates only for overflow; PTU-served requests cost only the hourly PTU",
        ], theme="yellow", icon="quotas", src=[("Spillover for provisioned deployments", S_SPILL)]),
        C(half, "Warm-standby Foundry account", [
            "A Foundry account with agent capability, no projects, no connections and no model deployments, fully networked: low idle cost",
            "Pre-provisioning the state resources cuts RTO but adds cost: Storage is cheap when idle, AI Search isn't",
        ], theme="green", icon="foundry", src=[("Platform outage playbooks", S_PLATFORM_DR)]),
        C(half, "Gateway tier", [
            "API Management multi-region adds per-region units (Premium tier, classic)",
            "Calls from a gateway to a model in another region add latency and egress charges",
        ], theme="grape", icon="apim", src=[("Multi-region deployment", S_APIM_MR), ("Gateway topologies", S_GW)]),
        C(half, "Cosmos DB regions", [
            "An extra read or write region increases your costs for each region",
            "Regions with zone redundancy are charged at a premium, waived for multiregion writes and autoscale throughput",
        ], theme="cyan", icon="cosmos", src=[("Reliability in Cosmos DB", S_COSMOS_REL)]),
        C(half, "PTU reservations", [
            "A Global reservation isn't region-specific and can cover Global PTU deployments in both regions",
            "Data Zone and Regional reservations are separate purchases and must match the deployment's region",
            "Reservations don't guarantee capacity: deploy first, then buy",
        ], theme="yellow", icon="reservations", src=[("PTU billing and reservations", S_PTU_BILL)]),
        C(half, "Hot/hot PTU", [
            "PTU is billed hourly for deployed PTUs whether or not requests arrive",
            "If one region fails the survivor carries 100%: over-provisioning to absorb it is part of the cost",
        ], theme="red", icon="cost-management", src=[("Provisioned throughput", S_PTU), ("Gateway topologies", S_GW)]),
    ]
    _, b = grid(cv, CX, y, levers, 2, gap_x=30, gap_y=24)
    return max(lp.bottom, b) + 70


def build(cv: Canvas) -> None:
    y = _head(cv)
    y, _gw = _big(cv, y)
    y = _flow_notes(cv, y)
    y = _patterns(cv, y)
    y = _ptu_spill(cv, y)
    y = _quota(cv, y)
    y = _cost(cv, y)
    sources(cv, 0, y, [
        ("High availability and resiliency for Foundry", S_HA),
        ("Use a gateway in front of multiple model deployments or instances", S_GW),
        ("Baseline Foundry chat reference architecture", S_BASE),
        ("Manage traffic with spillover for provisioned deployments", S_SPILL),
        ("What is provisioned throughput for Foundry Models?", S_PTU),
        ("Get started with provisioned deployments", S_PTU_START),
        ("Provisioned throughput billing and reservations", S_PTU_BILL),
        ("Manage Azure OpenAI quota", S_QUOTA),
        ("Deployment types for Foundry Models", S_DEP),
        ("Stay informed about service health", S_HEALTH),
        ("Deploy API Management to multiple regions", S_APIM_MR),
        ("API Management backends: pools and circuit breaker", S_APIM_BACKENDS),
        ("AI gateway capabilities in API Management", S_APIM_CAP),
        ("Reliability in API Management", S_APIM_REL),
        ("Reliability in Azure Cosmos DB", S_COSMOS_REL),
        ("Agent Service platform outage playbooks", S_PLATFORM_DR),
    ], w=W, cols=3)
