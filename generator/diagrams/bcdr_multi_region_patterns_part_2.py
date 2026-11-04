"""Multi-region patterns for Foundry, part 2: retries, backoff, circuit breakers and health probes; three failure walk-throughs drawn
as before/after topologies (regional model outage, PTU exhausted, dependency outage); agent-state consistency; rebuilding from code
and gotchas."""
from __future__ import annotations

from generator.diagrams.bcdr_multi_region_patterns import (
    S_HA, S_GW, S_BASE, S_SPILL, S_PTU, S_PTU_BILL, S_QUOTA, S_DEP, S_HEALTH, S_AGENT_DR, S_APIM_MR, S_APIM_BACKENDS, S_APIM_CAP, S_APIM_REL,
    S_PLATFORM_DR, S_COSMOS_REL)
from generator.diagrams.ra_ai_gateway_pattern import (
    W, C, N, StepsCard, pill, _node, _frame, _pe, _wire, _mini_panel, RED, GREY)
from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import theme as get_theme

META = dict(
    id="bcdr-multi-region-patterns-part-2", title="Multi-region patterns, part 2", section="4", order=2.5,
    description="Retry, backoff and circuit-breaker mechanics, health probes, three failure walk-throughs drawn as before/after "
                "topologies (regional model outage, PTU exhausted, dependency outage), agent-state consistency and rebuild with IaC.",
    tags=["bcdr", "circuit-breaker", "retry", "failure-walkthrough", "iac", "agent-state"],
)

S_OPERATOR_DR = learn("how-to/agent-service-operator-disaster-recovery")
S_STD_SETUP = learn("agents/concepts/standard-agent-setup")
S_SAMPLES = "https://github.com/microsoft-foundry/foundry-samples"
S_SEARCH_REL = learn("reliability/reliability-ai-search", base="azure")
S_STORAGE_REL = learn("reliability/reliability-storage-blob", base="azure")


# ====================================================================== 0. title and key messages
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Multi-region patterns for Foundry, part 2",
        "Retry and circuit-breaker mechanics, three failure walk-throughs as before/after topologies, agent state and rebuild from code "
        "(facts as of 2026-11-03)", icon="regions", w=W)
    y = bottom + 36
    gap = 36
    cw = (W - 5 * gap) / 6
    cards = [
        C(cw, "Retry at the client, break at the gateway", [
            "SDKs retry 429 and honour retry-after; the default is 2 retries",
            "The gateway circuit breaker trips on 429, 500 and 503 and honours Retry-After",
        ], theme="yellow", icon="gear", src=[("Manage quota", S_QUOTA)]),
        C(cw, "Probes: passive beats synthetic", [
            "Many AI services have no health endpoint; synthetic calls use capacity",
            "The API Management status endpoint tests the gateway, not the model",
        ], theme="violet", icon="service-health", src=[("Gateway health checks", S_GW + "#gateway-health-checks")]),
        C(cw, "Three failures, before and after", [
            "Regional model outage",
            "PTU exhausted",
            "Dependency outage: Cosmos DB, AI Search or Storage",
        ], theme="red", icon="alerts", src=[("High availability and resiliency", S_HA)]),
        C(cw, "Agent state is yours", [
            "Not replicated: recovery rebuilds agents with new IDs and no thread history",
            "Hide IDs behind configuration or the gateway",
        ], theme="cyan", icon="cosmos", src=[("Agent Service disaster recovery", S_AGENT_DR)]),
        C(cw, "Rebuild from code", [
            "IaC deploys both regions from one pipeline",
            "Role assignments, identities, network and policy are part of the template",
        ], theme="green", icon="devops", src=[("High availability and resiliency", S_HA)]),
        C(cw, "Docs disagree in places", [
            "Cosmos DB failover timing, AI Search recovery and Storage failover are flagged where they appear",
            "Verify against the linked pages before you plan around a number",
        ], theme="orange", icon="learn", src=[("Agent Service disaster recovery", S_AGENT_DR)]),
    ]
    _, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    note = N(W, "Part 1 ('Multi-region patterns') draws the region-pair topologies, PTU and spillover mechanics, quota planning and the cost ladder. This part covers what "
                "happens at request level, walks three failures through those topologies, and closes with agent state, IaC and gotchas.", kind="info",
             title="Where this part fits")
    note.place(cv, 0, y)
    return note.bottom + 70


# ====================================================================== 1. retries, circuit breakers, health
def _retry(cv, y):
    _, hb = section_header(
        cv, 0, y, "1  Retries, backoff, circuit breakers and health", size=32,
        sub="One request that meets a throttled backend: the client retries politely, the gateway removes the backend for a while and tries the next one")
    y = hb + 36
    LW = 1600
    with cv.panel(0, y, w=LW, title="One request that hits a throttled backend", sub="numbers follow the steps; solid = request, dashed = response",
                  theme="yellow", style="dotted", fill="none", pad=24, title_size=24, sub_size=15) as lp:
        seq = Sequence(cv, lp.ix + 20, lp.iy + 6, [("Client app (SDK)", "gray", "app"), ("Gateway", "grape", "apim"),
                                                  ("Backend, priority 1", "blue", "openai"), ("Backend, priority 2", "blue", "foundry")],
                       spacing=410, head_w=290, head_h=64, size=17, label_size=15)
        seq.msg(0, 1, "request to the gateway endpoint (OpenAI SDK default: 2 retries, configurable)", num=1)
        seq.msg(1, 2, "call with the gateway's managed identity", num=2)
        seq.msg(2, 1, "429 with Retry-After (or a 500 / 503)", dash="dashed", num=3)
        seq.msg(1, 1, "circuit breaker trips: rule met, Retry-After accepted")
        seq.msg(1, 3, "retry on the next backend (priority 2) before any error goes back", num=4)
        seq.msg(3, 1, "200 OK", dash="dashed")
        seq.msg(1, 0, "200 OK + token metrics", dash="dashed", num=5)
        seq.note(0, 3, "No backend left? The breaker returns 503 to the client and the gateway health check reports unhealthy. "
                       "The client then honours retry-after-ms, otherwise it backs off as below.", kind="warn")
        sb = seq.end()
        # client backoff ladder (the docs' four steps; the bar lengths are illustrative, not durations)
        by = sb + 30
        cv.text(lp.ix, by, "Client-side backoff for a 429 that has no retry-after-ms", size=20, color=get_theme("yellow").deep)
        steps = [("1  wait a short, random delay after the first failure", 110), ("2  if the retry fails, double the delay (exponential backoff)", 220),
                 ("3  add random jitter so all clients don't retry at the same instant", 220)]
        for i, (lab, bw) in enumerate(steps):
            ry = by + 40 + i * 46
            cv.rect(lp.ix + 10, ry, bw, 32, stroke="#f08c00", fill="#ffec99", style="solid" if i < 2 else "hachure", sw=2, round_=False)
            cv.text(lp.ix + 10 + bw + 16, ry + 4, lab, size=16, color=INK)
        ry = by + 40 + 3 * 46
        cv.line((lp.ix + 20, ry), (lp.ix + 60, ry + 32), stroke=RED, sw=5)
        cv.line((lp.ix + 20, ry + 32), (lp.ix + 60, ry), stroke=RED, sw=5)
        cv.text(lp.ix + 76, ry + 4, "4  set a maximum number of retries (the docs' example: 5 to 10) to avoid infinite loops", size=16, color="#c92a2a")
        cv.text(lp.ix, ry + 52, "Unsuccessful requests still count toward the per-minute rate limit: resending without backing off makes throttling worse. "
                                 "Bar lengths are illustrative.", size=14, color=MUTED, wrap=LW - 60)
    # right: pool
    RX = LW + 60
    RW_ = W - RX
    with cv.panel(RX, y, w=RW_, h=500, title="API Management backend pool", sub="up to 30 backends; load balancing is approximate across gateway instances",
                  theme="grape", style="solid", fill="soft", pad=20, title_size=24, sub_size=15) as pp:
        gw_ = _node(cv, pp.ix, pp.iy + 60, 250, 120, "Gateway", "apim", "grape", sub="pool + breaker", icon_pos="top")
        g1 = _frame(cv, pp.ix + 330, pp.iy + 10, 620, 170, "Priority group 1: used first", "blue", dash="solid")
        _node(cv, pp.ix + 350, pp.iy + 54, 280, 80, "Backend A", "openai", "blue", sub="weight 3", icon_pos="left", size=17)
        _node(cv, pp.ix + 650, pp.iy + 54, 280, 80, "Backend B", "openai", "blue", sub="weight 1", icon_pos="left", size=17)
        g2 = _frame(cv, pp.ix + 330, pp.iy + 214, 620, 130, "Priority group 2: only if every group-1 backend is tripped", "blue", dash="dashed")
        _node(cv, pp.ix + 350, pp.iy + 256, 580, 70, "Backend C", "foundry", "blue", sub="other region", icon_pos="left", size=17)
        _wire(cv, gw_, g1, a_side="right", b_side="left", ta=0.4, tb=0.5, sw=3)
        _wire(cv, gw_, g2, a_side="right", b_side="left", ta=0.8, tb=0.5, sw=3, passive=True)
        ChipFlow(["round-robin", "weighted", "priority-based", "session awareness (cookie)"], RW_ - 60, theme="grape", size=14, fill="soft").place(
            cv, pp.ix, pp.iy + 372)
    br = C(RW_, "Circuit breaker rule", [
        "A rule = failure count or percentage in an interval + a status-code range (for example 3 or more 5xx in 1 hour, 500-599) + a trip duration (default 1 hour) + accept the Retry-After header",
        "When tripped, requests stop going to that backend and a 503 goes back to the client if no other backend remains",
        "! Only one rule per backend; not supported in the Consumption tier; trip rules are approximate across gateway instances",
        "! Azure OpenAI can return a Retry-After as large as 1 day: design the rule for it",
    ], theme="yellow", icon="service-health", src=[("Backends in API Management", S_APIM_BACKENDS)])
    br.place(cv, RX, y + 524)
    return max(lp.bottom, br.bottom) + 40


def _mechanics(cv, y):
    rows = [
        [("Client SDK retry", "yellow"),
         "OpenAI SDKs retry 429 by default honouring retry-after; max_retries defaults to 2 and is configurable (the docs' examples set 5). Best practice: honour retry-after-ms, otherwise exponential backoff with random jitter, and cap the retries (the docs' examples use 5 to 10). .NET: options.Retry.MaxRetries and RetryMode.Exponential; Polly adds circuit breakers"],
        [("Rate-limit headers", "yellow"),
         "x-ratelimit-limit-requests and -tokens, x-ratelimit-remaining-requests and -tokens, x-ratelimit-reset-requests and -tokens, and retry-after-ms on a 429. Watch the remaining values to throttle before you hit the limit"],
        [("PTU behaviour", "blue"),
         "A PTU deployment returns a 429 immediately at 100% utilization with retry-after-ms: 'a traffic-management signal' rather than a service error; accepted requests keep predictable latency"],
        [("429 causes", "yellow"),
         "Rate limit exceeded, system capacity throttling, or a temporary rate-limit adjustment on a shared Standard pool: listed under 'Quota and capacity' in part 1. Sustained 429s below approved quota in production: open a support request"],
        [("Gateway guidance", "grape"),
         "Honour Retry-After and don't keep hitting an endpoint that returns 429. Don't predict throttling: use response codes. Treat 429, 500 and 503 as circuit-break signals. Retry the current request on another backend before returning a gateway error. The gateway health check signals unhealthy when no backend is available"],
        [("Health probes", "violet"),
         "Many AI services have no dedicated health endpoint and synthetic transactions consume capacity, so prefer passive signals. API Management's per-region status endpoint (/status-0123456789abcdef) covers the gateway only: add a dedicated health API. Traffic Manager probes the regional status endpoints; Application Insights availability tests probe agent endpoints from several locations; Service Health and Resource Health alerts warn early"],
    ]
    t = Table([("Mechanism", 230), "Documented behaviour (as of 2026-11-03)"], rows, w=W, theme="yellow", size=15, head_size=16, first_col_theme="yellow")
    t.place(cv, 0, y)
    ly = t.bottom + 10
    x = 0
    for label, url in (("Manage quota (rate limits, 429 types, retries)", S_QUOTA), ("Backends in API Management", S_APIM_BACKENDS),
                       ("Use a gateway in front of multiple model deployments", S_GW), ("High availability and resiliency", S_HA)):
        tt = cv.text(x, ly, f"Learn: {label}", size=12, color=LINK, link=url)
        x += tt.w + 28
    return ly + 60


# ====================================================================== 2. failure walk-throughs
SW, SH = 880, 580


def _cross(cv, cx, cy, s=22, sw=6):
    cv.line((cx - s, cy - s), (cx + s, cy + s), stroke=RED, sw=sw)
    cv.line((cx - s, cy + s), (cx + s, cy - s), stroke=RED, sw=sw)


def _scen_panels(cv, y, title_l, title_r, sub_l, sub_r, th_r="red"):
    _mini_panel(cv, 0, y, SW, SH, title_l, sub_l, "green")
    _mini_panel(cv, SW + 120, y, SW, SH, title_r, sub_r, th_r)
    # failure arrow between the two panels
    ax = SW + 14
    arrow(cv, [(ax, y + SH / 2), (ax + 92, y + SH / 2)], sw=5, color=RED)
    cv.text(ax - 8, y + SH / 2 - 54, "failure", size=18, color="#c92a2a", align="center", w=108)


def _s1(cv, x, y, after):
    cl = _node(cv, x + 24, y + 150, 150, 80, "Clients", "app", "gray")
    gw = _node(cv, x + 250, y + 120, 220, 140, "Gateway", "apim", "grape", sub="pool + circuit breaker", icon_pos="top")
    f1 = _node(cv, x + 560, y + 100, 290, 130, "Foundry - region 1", "foundry", "blue", sub="priority 1: the primary region", icon_pos="top",
               dash="solid" if not after else "dashed", fill="solid" if not after else "soft")
    f2 = _node(cv, x + 560, y + 290, 290, 130, "Foundry - region 2", "foundry", "blue", sub="priority 2: secondary, Data Zone or Global Standard",
               icon_pos="top", dash="dashed" if not after else "solid", fill="soft" if not after else "solid")
    _wire(cv, cl, gw, a_side="right", b_side="left")
    if not after:
        _wire(cv, gw, f1, a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow", num=1, num_theme="green")
        _wire(cv, gw, f2, a_side="right", b_side="left", ta=0.8, tb=0.5, route="elbow", passive=True, num=2, num_theme="orange")
        pill(cv, x + 24, y + 480, "breaker closed", "green", size=14, fill="soft")
        pill(cv, x + 24, y + 520, "verify: full quota, same model and version in region 2", "yellow", size=14, fill="soft")
    else:
        _wire(cv, gw, f1, a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow", passive=True, color=RED)
        _cross(cv, f1.right - 6, f1.y + 6, s=14, sw=5)
        _wire(cv, gw, f2, a_side="right", b_side="left", ta=0.8, tb=0.5, route="elbow", sw=3.5, num=3, num_theme="green")
        pill(cv, x + 250, y + 270, "breaker open", "red", size=15, fill="soft", icon="service-health")
        pill(cv, f1.x, f1.bottom + 12, "5xx or unreachable", "red", size=14, fill="soft")
        pill(cv, x + 24, y + 480, "no alternative left: clients get 503", "red", size=14, fill="soft")
        pill(cv, x + 24, y + 520, "after the trip duration the circuit resets", "green", size=14, fill="soft")


def _s2(cv, x, y, after):
    cl = _node(cv, x + 24, y + 150, 150, 80, "Clients", "app", "gray")
    gw = _node(cv, x + 250, y + 120, 200, 140, "Gateway", "apim", "grape", sub="pool + retry", icon_pos="top")
    _frame(cv, x + 520, y + 80, 340, 320, "Foundry - region 1", "blue", icon="foundry", dash="solid")
    pt = _node(cv, x + 544, y + 130, 292, 84, "PTU deployment", "openai", "blue", sub="at 100% utilization" if after else "under 100% utilization",
               icon_pos="left", size=17, fill="solid", dash="solid")
    st = _node(cv, x + 544, y + 296, 292, 84, "Standard deployment", "openai", "blue", sub="spillover target, same resource", icon_pos="left", size=17,
               dash="dashed", fill="soft" if not after else "solid")
    f2 = _node(cv, x + 520, y + 424, 340, 70, "Foundry - region 2", "foundry", "blue", sub="priority 2", icon_pos="left", dash="dashed", fill="soft")
    _wire(cv, cl, gw, a_side="right", b_side="left")
    if not after:
        _wire(cv, gw, pt, a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow", num=1, num_theme="green")
        pill(cv, x + 24, y + 480, "spillover enabled: spilloverDeploymentName", "yellow", size=14, fill="soft")
        pill(cv, x + 24, y + 520, "PTU served = hourly cost only", "blue", size=14, fill="soft")
    else:
        _wire(cv, gw, pt, a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow")
        connect(cv, pt, st, a_side="bottom", b_side="top", dash="dashed", sw=3.5, color="#f08c00", num=2, num_theme="yellow")
        cv.text(x + 712, y + 236, "429 + retry-after-ms\nthen spillover", size=14, color="#c92a2a")
        _wire(cv, gw, f2, a_side="bottom", b_side="left", ta=0.5, tb=0.5, route="elbow", passive=True, num=3, num_theme="orange")
        pill(cv, x + 24, y + 440, "headers x-ms-spillover-*", "yellow", size=14, fill="soft")
        pill(cv, x + 24, y + 480, "metric IsSpillover = True", "yellow", size=14, fill="soft")
        pill(cv, x + 24, y + 520, "if Standard fails too: retry on region 2", "orange", size=14, fill="soft")


def _s3(cv, x, y, after):
    cl = _node(cv, x + 24, y + 130, 130, 70, "Gateway", "apim", "grape", icon_pos="top", size=16)
    _frame(cv, x + 200, y + 90, 650, 400 if after else 350, "Region 1", "gray", dash="solid")
    ag = _node(cv, x + 224, y + 134, 200, 120, "Foundry project", "agent", "green", sub="Agent Service, standard setup", icon_pos="top", size=16, sub_size=13)
    co = _node(cv, x + 470, y + 130, 360, 64, "Cosmos DB", "cosmos", "cyan", sub="enterprise_memory: agents and threads", icon_pos="left", size=16, sub_size=13)
    se = _node(cv, x + 470, y + 204, 360, 64, "AI Search", "ai-search", "teal", sub="file knowledge and uploads", icon_pos="left", size=16, sub_size=13)
    sr = _node(cv, x + 470, y + 278, 360, 64, "Storage", "storage", "cyan", sub="files", icon_pos="left", size=16, sub_size=13)
    gi = _node(cv, x + 224, y + 290, 200, 64, "Your grounding index", "ai-search", "teal", sub="AI Search, one region", icon_pos="left", size=15, sub_size=12)
    _wire(cv, cl, ag, a_side="right", b_side="left")
    for d in (co, se, sr):
        _wire(cv, ag, d, a_side="right", b_side="left", sw=2, route="elbow")
    _wire(cv, ag, gi, a_side="bottom", b_side="top", sw=2)
    if after:
        for d in (co, se, sr):
            _cross(cv, d.right - 28, d.cy, s=12, sw=5)
        _cross(cv, gi.right - 24, gi.cy, s=12, sw=5)
        # replica in region 2
        _frame(cv, x + 200, y + 420 + 8, 650, 130, "Region 2", "gray", dash="dashed", fill="none")
        rep = _node(cv, x + 224, y + 466, 320, 68, "Second search service", "ai-search", "teal", sub="your own index, synced", icon_pos="left", size=15, sub_size=12,
                    dash="dashed", fill="soft")
        pill(cv, x + 570, y + 470, "sync indexes + failover", "orange", size=14, fill="soft")
        arrow(cv, [(gi.cx, gi.bottom + 6), (gi.cx, rep.y - 6)], dash="dashed", color="#e8590c", sw=3)
    else:
        pill(cv, x + 24, y + 430, "state, knowledge and files live in your subscription", "cyan", size=14, fill="soft")
        pill(cv, x + 24, y + 470, "regional services: each has its own recovery path", "gray", size=14, fill="soft")


def _scenario(cv, y, num, title, sub, steps, fn, titles, extra=None):
    th = "red"
    _, hb = section_header(cv, 0, y, f"Scenario {num}  {title}", size=28, sub=sub)
    y = hb + 30
    _scen_panels(cv, y, titles[0], titles[1], titles[2], titles[3])
    fn(cv, 0, y, False)
    fn(cv, SW + 120, y, True)
    sx = 2 * SW + 120 + 60
    st = StepsCard(W - sx, "Detect, contain, verify, recover", steps, theme_name="red", icon="alerts", size=15, gap=10)
    st.place(cv, sx, y)
    bottom = max(y + SH, st.bottom)
    if extra:
        bottom = extra(cv, sx, st.bottom + 16, W - sx, bottom)
    return bottom + 60


def _walkthroughs(cv, y):
    _, hb = section_header(
        cv, 0, y, "2  Three failure walk-throughs, drawn before and after", size=32,
        sub="Same topology in both panels. Green = healthy, red cross = failed, dashed orange = the path traffic takes instead. The red arrow is the failure")
    y = hb + 36

    # ---- scenario 1
    def extra1(cv, sx, yy, w, bottom):
        n = N(w, "Global and Data Zone Standard add resilience to single-region inference outages, but they 'don't replace application-level regional failover': "
                 "the layer that processes API requests is regional to your Azure resource.", kind="warn", title="Global routing is not the plan",
              src=[("High availability and resiliency", S_HA)])
        n.place(cv, sx, yy)
        return max(bottom, n.bottom)
    y = _scenario(cv, y, 1, "Regional model outage",
                  "The primary region's model endpoint returns 5xx or is unreachable",
                  [(1, "Detect: ModelAvailabilityRate drops and ModelRequests 5xx spikes; Service Health and Resource Health alerts fire; Application Insights availability tests fail", "red"),
                   (2, "Contain: the gateway circuit breaker trips (for example 3 or more 5xx in the interval) and the pool routes to the priority-2 backend in the secondary region. With no alternative the clients get a 503", "yellow"),
                   (3, "Verify: the secondary has full quota and the same model and version. Resubmit in-flight jobs: they don't automatically transition", "blue"),
                   (4, "Recover: after the trip duration, or the Retry-After, the circuit resets. Verify the primary, then run a post-incident drill", "green")],
                  _s1, ("Before: healthy, region 1 first", "After: region 1 fails, region 2 serves", "the pool prefers region 1; region 2 is the priority-2 backend",
                        "the breaker removed region 1; the pool uses region 2"), extra1)

    # ---- scenario 2
    def extra2(cv, sx, yy, w, bottom):
        n = N(w, "If spillover and a gateway-level failover are both active the same failure can be handled twice: keep the model and version identical in every target.",
              kind="warn", title="Double handling", src=[("Spillover for provisioned deployments", S_SPILL)])
        n.place(cv, sx, yy)
        return max(bottom, n.bottom)
    y = _scenario(cv, y, 2, "PTU exhausted",
                  "Reserved capacity is fully used: provisioned utilization reaches 100%",
                  [(1, "Detect: ProvisionedUtilization at or above 100% (or the 'Provisioned-managed utilization V2' metric): the PTU returns 429 with retry-after-ms. That is a traffic-management signal, not a service error", "red"),
                   (2, "Spill over: with spillover enabled the request goes to the Standard deployment in the same resource; response headers show x-ms-spillover-*; metrics show IsSpillover = True", "yellow"),
                   (3, "Escalate: if Standard also returns 429 or fails, the gateway retries on another backend or region (priority pool) with backoff and jitter", "orange"),
                   (4, "Fix: for sustained overflow resize the PTUs (needs capacity: check the Model Capacities API) or add a pool. Avoid scale-down and scale-up churn: capacity isn't guaranteed. Consider an enterprise PTU pool with priority routing", "green")],
                  _s2, ("Before: PTU serves everything", "After: overflow spills to Standard", "PTU under 100% utilization; spillover is configured",
                        "the PTU is exhausted; Standard absorbs the overflow, region 2 is the last resort"), extra2)

    # ---- scenario 3
    def extra3(cv, sx, yy, w, bottom):
        n1 = N(w, "Agent DR pages: the Cosmos DB team triggers a service-managed failover, RTO 30+ minutes once triggered, up to 15 minutes of data. The Cosmos DB reliability "
                  "page says declaring an outage can take an hour or more and recommends a forced failover for faster recovery.", kind="warn",
               title="Docs disagree: Cosmos DB failover timing", src=[("Platform outage playbooks", S_PLATFORM_DR), ("Reliability in Cosmos DB", S_COSMOS_REL)])
        n1.place(cv, sx, yy)
        n2 = N(w, "The Agent DR pages rebuild AI Search from infrastructure as code and re-ingest. The Architecture Center baseline says AI Search has no built-in restore "
                  "and points to Microsoft Support. Treat rebuild as the supported path. Storage: the HA page says Foundry projects don't support default storage account "
                  "failover with GRS or GZRS, while the DR pages require GZRS with customer-managed failover.", kind="warn",
               title="Docs disagree: AI Search recovery and Storage failover", src=[("High availability and resiliency", S_HA), ("Agent Service disaster recovery", S_AGENT_DR)])
        n2.place(cv, sx, n1.bottom + 16)
        return max(bottom, n2.bottom)
    y = _scenario(cv, y, 3, "Dependency outage: Cosmos DB, AI Search or Storage",
                  "A regional dependency of the standard agent setup, or your own grounding index, goes down while the model endpoint stays up",
                  [(1, "Detect: a Cosmos DB regional outage takes down every project that uses that enterprise_memory (data-plane APIs error). A Search outage breaks file knowledge and uploads only; agents without files are mostly fine. A Storage outage blocks creating agents with file knowledge and adding files", "red"),
                   (2, "Contain: degrade gracefully (disable uploads). Cosmos DB: wait for the service-managed failover, or choose a forced failover that can lose unreplicated writes. Storage: customer-managed failover (GZRS)", "yellow"),
                   (3, "Your own knowledge index: AI Search is single-region. Stand up a second search service in another region, sync the indexes, add load balancing or failover. Indexers retry transient faults; consider an offline index plus swap", "teal"),
                   (4, "Recover: verify with a test conversation, then reconcile restored resources and role assignments. Restores don't bring role assignments back", "green")],
                  _s3, ("Before: dependencies healthy", "After: dependencies down", "agents, files and threads run on resources in your subscription",
                        "the model endpoint is up, the dependencies are not"), extra3)
    return y


# ====================================================================== 3. agent state
def _state(cv, y):
    _, hb = section_header(
        cv, 0, y, "3  Agent state: what is not replicated and how to keep clients stable", size=32,
        sub="Agent Service state is per project. Recovery means reconstruction, so design the parts you own so that a rebuild doesn't break the caller")
    y = hb + 36
    LW = 1860
    with cv.panel(0, y, w=LW, title="The same app before and after a rebuild in region 2", sub="solid = normal, dotted red = not replicated, dashed teal = suggested design",
                  theme="cyan", style="dotted", fill="none", pad=24, title_size=24, sub_size=15) as sp:
        app = _node(cv, sp.ix + 530, sp.iy + 10, 740, 120, "Your app and gateway or configuration", "app", "gray", icon_pos="left", size=20, sub_size=15,
                    sub="a stable alias such as 'support-agent' points to the current agent ID: clients never hold IDs")
        PW_ = 800
        panels = []
        for i, (nm, sub_, th_) in enumerate((("Region 1 (primary)", "serves traffic today", "blue"), ("Region 2 (rebuilt from code)", "after a failover", "orange"))):
            px = sp.ix + i * (PW_ + 110)
            with cv.panel(px, sp.iy + 190, w=PW_, title=nm, sub=sub_, theme=th_, style="solid", fill="soft", pad=20, title_size=22, sub_size=15) as rp:
                a = _node(cv, rp.ix, rp.iy + 4, PW_ - 40, 92, "Agent", "agent", "green", icon_pos="left", size=18,
                          sub="agent ID A: definition from source control" if i == 0 else "new agent ID B: redeployed from source control")
                t = _node(cv, rp.ix, a.bottom + 22, PW_ - 40, 92, "Threads and conversations", "cosmos", "cyan", icon_pos="left", size=18,
                          sub="in this region's Cosmos DB, per project" if i == 0 else "new and empty: no prior history", dash="solid" if i == 0 else "dashed",
                          fill="solid" if i == 0 else "soft")
                f_ = _node(cv, rp.ix, t.bottom + 22, PW_ - 40, 80, "Uploaded files and knowledge", "storage", "cyan", icon_pos="left", size=18,
                           sub="rebuilt from source: not carried over" if i == 1 else "Storage and AI Search in your subscription", dash="solid" if i == 0 else "dashed",
                           fill="solid" if i == 0 else "soft")
            panels.append((rp, a, t, f_))
        _wire(cv, app, panels[0][1], a_side="bottom", b_side="top", ta=0.3, tb=0.5, route="elbow", num=1, num_theme="green", bend=0.35)
        _wire(cv, app, panels[1][1], a_side="bottom", b_side="top", ta=0.7, tb=0.5, route="elbow", passive=True, num=2, num_theme="orange", bend=0.35)
        mx = sp.ix + PW_ + 55
        my = panels[0][2].cy
        arrow(cv, [(panels[0][0].right + 6, my), (panels[1][0].x - 6, my)], dash="dotted", color=RED, sw=3.5, end_head="arrow")
        cv.line((mx - 14, my - 14), (mx + 14, my + 14), stroke=RED, sw=6)
        cv.line((mx - 14, my + 14), (mx + 14, my - 14), stroke=RED, sw=6)
        cv.text(mx - 70, my + 24, "not\nreplicated", size=14, color="#c92a2a", align="center", w=140)
        own = _node(cv, sp.ix + 330, panels[0][0].bottom + 40, 1100, 96, "A store you replicate (suggested)", "cosmos", "teal", icon_pos="left", size=19, sub_size=15,
                    sub="conversation memory in a multi-region Cosmos DB or your own database; treat Foundry threads as disposable", dash="dashed", fill="soft")
        _wire(cv, panels[0][0], own, a_side="bottom", b_side="left", ta=0.5, tb=0.5, route="elbow", passive=True, color="#099268")
        _wire(cv, panels[1][0], own, a_side="bottom", b_side="right", ta=0.5, tb=0.5, route="elbow", passive=True, color="#099268")
    CX = LW + 50
    CW = W - CX
    c1 = C(CW, "What the docs say", [
        "Agent Service state is per project: no replication, backup, point-in-time restore or multi-region active-active",
        "Recovery is reconstruction: agent IDs and thread or conversation IDs change on a rebuild",
        "Hide IDs behind a gateway or configuration; with an AI gateway update the gateway routing instead of the clients",
    ], theme="cyan", icon="cosmos", src=[("Agent Service disaster recovery", S_AGENT_DR), ("Platform outage playbooks", S_PLATFORM_DR)])
    c1.place(cv, CX, y)
    c2 = C(CW, "Compute doesn't change who owns state", [
        "Prompt and hosted agents support service-managed conversations (the platform persists them) or client-managed conversations (your code carries the state)",
        "Self-hosted orchestration always manages its own state",
        "Durable stores for chat history and agent configuration live in your subscription",
    ], theme="cyan", icon="agent", src=[("Baseline chat architecture", S_BASE)])
    c2.place(cv, CX, c1.bottom + 20)
    c3 = C(CW, "Hosted-agent sessions", [
        "$HOME and /files persist across idle; a session is deleted after 30 days idle; state-store items default to a 30-day idle expiry",
        "Neither is documented as geo-replicated (a gap in the docs as of 2026-11-03)",
    ], theme="green", icon="container-apps", src=[("Agent Service disaster recovery", S_AGENT_DR)])
    c3.place(cv, CX, c2.bottom + 20)
    y2 = max(sp.bottom, c3.bottom) + 24
    n1 = N(LW, "If your own stores reference conversation or agent IDs, coordinate their recovery with Agent Service's: 'Restoring only a subset of dependencies can "
               "result in orphaned or inconsistent data.' Never touch system-managed collections, containers or indexes directly.", kind="gotcha",
           title="Transactional consistency", src=[("Baseline chat architecture", S_BASE)])
    n1.place(cv, 0, y2)
    n2 = N(CW, "The state database partitions by a per-project GUID, so multi-region writes don't prevent data loss on failback. The DR pages use a new temporary Cosmos DB during a failover.",
           kind="warn", title="Multi-region Cosmos DB doesn't make threads portable", src=[("Platform outage playbooks", S_PLATFORM_DR)])
    n2.place(cv, CX, y2)
    n3 = N(LW, "Suggested design, our inference: the docs don't state it as such. If you need conversation continuity across regions, keep the conversation memory in a store "
               "you replicate and treat Foundry agent threads as disposable.", kind="quote", title="Design implication (suggested)")
    n3.place(cv, 0, n1.bottom + 20)
    return max(n3.bottom, n2.bottom) + 70


# ====================================================================== 4. rebuild from code
def _iac(cv, y):
    _, hb = section_header(
        cv, 0, y, "4  Rebuild from code: IaC for both regions, kept from drifting", size=32,
        sub="A pipeline that deploys the same template to both regions turns a failover into a configuration switch plus a redeploy")
    y = hb + 36
    LW = 2100
    with cv.panel(0, y, w=LW, title="One repository, one pipeline, two identical stamps", sub="dashed = periodic export, dotted = policy",
                  theme="green", style="dotted", fill="none", pad=24, title_size=24, sub_size=15) as ip:
        repo = _node(cv, ip.ix, ip.iy + 60, 330, 190, "Source control", "github", "gray", icon_pos="top", size=20, sub_size=14,
                     sub="Bicep, Terraform or ARM modules per project; agent definitions as JSON; tool and knowledge bindings")
        pipe = _node(cv, ip.ix + 420, ip.iy + 90, 250, 130, "CI/CD pipeline", "devops", "green", icon_pos="top", size=19, sub_size=14,
                     sub="deploys both regions; no untracked portal changes")
        stamps = []
        for i, nm in enumerate(("Region 1 stamp", "Region 2 stamp")):
            sy = ip.iy + 10 + i * 270
            with cv.panel(ip.ix + 770, sy, w=LW - 48 - 770, title=nm, theme="blue", style="solid", fill="soft", pad=18, title_size=22) as st:
                items = [("Foundry account and project", "foundry", "blue", "capability settings"), ("Dependencies", "cosmos", "cyan", "Cosmos DB, AI Search, Storage"),
                         ("Identity and RBAC", "managed-identity", "red", "user-assigned identity per project; roles for users"),
                         ("Network", "vnet", "indigo", "VNet, private endpoints, DNS, VPN")]
                bw = (LW - 48 - 770 - 36 - 3 * 14) / 4
                for k, (lab, ic, th_, sub_) in enumerate(items):
                    _node(cv, st.ix + k * (bw + 14), st.iy + 4, bw, 130, lab, ic, th_, sub=sub_, icon_pos="top", size=16, sub_size=13)
            stamps.append(st)
        _wire(cv, repo, pipe, a_side="right", b_side="left", sw=3, num=1, num_theme="green")
        _wire(cv, pipe, stamps[0], a_side="right", b_side="left", ta=0.3, tb=0.5, route="elbow", sw=3, num=2, num_theme="green")
        _wire(cv, pipe, stamps[1], a_side="right", b_side="left", ta=0.7, tb=0.5, route="elbow", sw=3)
        pol = _node(cv, ip.ix, ip.iy + 330, 670, 100, "Azure Policy", "policy", "grape", icon_pos="left", size=19, sub_size=14,
                    sub="keeps instances consistent; denyAction; a policy that restricts deployment types", dash="dashed", fill="soft")
        cv.line((pol.right + 8, pol.cy), (ip.ix + 760, pol.cy), stroke=get_theme("grape").stroke, sw=2.5, dash="dotted")
        exp = _node(cv, ip.ix, ip.iy + 470, 670, 100, "Scheduled export", "scheduler", "violet", icon_pos="left", size=19, sub_size=14,
                    sub="agents.list() to source control: definitions survive even if someone edited in the portal", dash="dashed", fill="soft")
        arrow(cv, [(exp.x + 40, exp.y - 6), (repo.x + 40, repo.bottom + 6)], dash="dashed", color=get_theme("violet").stroke, sw=3, num=3, num_theme="violet")
    CX = LW + 50
    CW = W - CX
    c1 = C(CW, "Development practices from the HA page", [
        "Use ARM templates or other infrastructure as code to deploy both regions quickly",
        "Update CI/CD pipelines to deploy to both regions so they don't drift",
        "Create role assignments for users in both regions",
        "Create networks and private endpoints for both regions; make sure users can reach both (VPN and DNS)",
    ], theme="green", icon="devops", src=[("High availability and resiliency", S_HA)])
    c1.place(cv, CX, y)
    c2 = C(CW, "Identity and samples", [
        "Prefer a user-assigned managed identity per project. With a system-assigned identity, include the principal ID in guid() so a regenerated identity gets a new role-assignment name",
        "foundry-samples: infrastructure/infrastructure-setup-bicep/43-standard-agent-setup-with-customization/main.bicep; reuse resources by passing existingAoaiResourceId, aiStorageAccountResourceId, cosmosDBResourceId and aiSearchServiceResourceId",
    ], theme="red", icon="managed-identity", src=[("Standard agent setup", S_STD_SETUP), ("High availability and resiliency", S_HA), ("foundry-samples (GitHub)", S_SAMPLES)])
    c2.place(cv, CX, c1.bottom + 20)
    y2 = max(ip.bottom, c2.bottom) + 24
    n1 = N(1020, "Foundry doesn't sync or recover artifacts or metadata between projects. If the primary and secondary projects share associated resources with geo-replication "
                 "enabled, some objects are available in the failover project: for example the same Docker images, configured datastores and Key Vault resources.",
           kind="gotcha", title="Nothing syncs between projects", src=[("High availability and resiliency", S_HA)])
    n1.place(cv, 0, y2)
    n2 = N(1020, "Verify readiness on a schedule (for example quarterly): the secondary's project, deployed models and connections match the primary; a representative agent job "
                 "runs end to end including Cosmos DB, AI Search and Storage; role assignments, DNS and private-endpoint paths work; fix the IaC for every gap you find.",
           kind="tip", title="Drill it", src=[("Verify failover readiness", S_HA + "#verify-failover-readiness")])
    n2.place(cv, 1090, y2)
    n3 = N(1020, "If you use a system-assigned identity, reapply the role assignments in the failover project; the HA page recommends switching to a user-assigned identity.",
           kind="warn", title="Identity mismatch", src=[("High availability and resiliency", S_HA)])
    n3.place(cv, 2180, y2)
    return max(n1.bottom, n2.bottom, n3.bottom) + 70


# ====================================================================== 5. gotchas
def _gotchas(cv, y):
    _, hb = section_header(cv, 0, y, "5  Gotchas to remember", size=32, sub="Things that go wrong quietly (as of 2026-11-03)")
    y = hb + 30
    cw = (W - 2 * 40) / 3
    notes = [
        N(cw, "API Management multi-region needs the Premium (classic) tier. Premium v2 and Standard v2 support availability zones but not multiregion deployments. "
              "Autoscale applies only to the primary region: scale secondary regions by hand or with your own tools.", kind="gotcha",
          title="Tier limits for multi-region gateways", src=[("Reliability in API Management", S_APIM_REL)]),
        N(cw, "A custom retry library on top of the SDK's built-in retry multiplies requests. Set max_retries=0 on the client when you use your own library, otherwise each attempt can trigger up to two more SDK retries.",
          kind="gotcha", title="Retries stack", src=[("Manage quota", S_QUOTA)]),
        N(cw, "The HA troubleshooting table lists 'APIM gateway returns 503 during regional outage' with the cause 'circuit breaker not configured'. A tripped breaker also returns 503 "
              "when no other backend remains, so check the pool and priorities first.", kind="warn", title="A 503 from the gateway", src=[("High availability and resiliency", S_HA), ("Backends in API Management", S_APIM_BACKENDS)]),
        N(cw, "Honour the DNS TTL and retry on the client when a global router fails over; Private DNS records must be updated by hand after a region loss if you use Private Link without a gateway.",
          kind="warn", title="DNS after a failover", src=[("High availability and resiliency", S_HA)]),
        N(cw, "Two preview features are in play around the gateway: the unified model API in API Management (preview) and the AI gateway in Foundry (preview). Verify their status "
              "before you depend on them.", kind="preview", title="Preview items", src=[("AI gateway capabilities in API Management", S_APIM_CAP)]),
        N(cw, "Standard model deployments run in a single region without availability-zone support (Architecture Center); for multi-datacenter availability use a global or data zone deployment. "
              "The HA page names Data Zone as US or EU; the deployment-types page also lists APAC, so check the current list.", kind="warn",
          title="Docs disagree: data zone names", src=[("Baseline chat architecture", S_BASE), ("Deployment types", S_DEP)]),
    ]
    xs = [0, cw + 40, 2 * (cw + 40)]
    b = y
    for i, n in enumerate(notes):
        col, rw = i % 3, i // 3
        if rw == 0:
            n.place(cv, xs[col], y)
        else:
            n.place(cv, xs[col], max(notes[j].bottom for j in range(3)) + 24)
    return max(n.bottom for n in notes) + 70


def build(cv: Canvas) -> None:
    y = _head(cv)
    y = _retry(cv, y)
    y = _mechanics(cv, y)
    y = _walkthroughs(cv, y)
    y = _state(cv, y)
    y = _iac(cv, y)
    y = _gotchas(cv, y)
    sources(cv, 0, y, [
        ("High availability and resiliency for Foundry", S_HA),
        ("Agent Service disaster recovery", S_AGENT_DR),
        ("Agent Service platform outage playbooks", S_PLATFORM_DR),
        ("Agent Service operator and data-loss playbooks", S_OPERATOR_DR),
        ("Standard agent setup (containers, roles, resources)", S_STD_SETUP),
        ("Baseline Foundry chat reference architecture", S_BASE),
        ("Use a gateway in front of multiple model deployments or instances", S_GW),
        ("Manage Azure OpenAI quota (rate limits, 429 types)", S_QUOTA),
        ("Manage traffic with spillover for provisioned deployments", S_SPILL),
        ("What is provisioned throughput for Foundry Models?", S_PTU),
        ("Provisioned throughput billing and reservations", S_PTU_BILL),
        ("Deployment types for Foundry Models", S_DEP),
        ("Stay informed about service health", S_HEALTH),
        ("Backends in API Management: pools and circuit breaker", S_APIM_BACKENDS),
        ("Deploy API Management to multiple regions", S_APIM_MR),
        ("Reliability in API Management", S_APIM_REL),
        ("Reliability in Azure Cosmos DB", S_COSMOS_REL),
        ("Reliability in Azure AI Search", S_SEARCH_REL),
        ("Reliability in Azure Blob Storage", S_STORAGE_REL),
        ("foundry-samples: standard agent setup Bicep (GitHub, not Learn)", S_SAMPLES),
    ], w=W, cols=3)
