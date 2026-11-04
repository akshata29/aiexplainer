"""AgentOps lifecycle on Foundry - flywheel, environments, versions, gates, promotion/rollback, owners."""
from __future__ import annotations

import math

from generator.xd import *

META = dict(
    id="agentops-lifecycle", title="AgentOps lifecycle", section="6", order=1,
    description="The end-to-end AgentOps loop on Foundry: plan, build, evaluate, deploy, operate, monitor, optimize - environments, versioning, gates, promotion and rollback, and who owns what.",
    tags=["agentops", "lifecycle", "environments", "versioning", "gates", "raci"],
)

W = 3000                    # canvas content width
COL, GAP = 460, 48          # 6-column grid: n columns = n*COL + (n-1)*GAP


def cw(n: int) -> int:
    return n * COL + (n - 1) * GAP


def cx_(i: int) -> int:
    return i * (COL + GAP)


# ----------------------------------------------------------------------------------------------- loop geometry
LOOP_A = 850


def _lem(s: float, cx: float, cy: float, a: float = LOOP_A) -> tuple[float, float]:
    """Point on a lemniscate (infinity loop). s in [0,1): 0 = centre heading up-right, .25 = right tip."""
    t = math.pi / 2 - 2 * math.pi * s
    d = 1 + math.sin(t) ** 2
    return cx + a * math.cos(t) / d, cy - a * math.sin(t) * math.cos(t) / d


def _inside(p, node, pad=10) -> bool:
    x, y = p
    if node["gate"]:
        return abs(x - node["cx"]) / (node["w"] / 2 + pad) + abs(y - node["cy"]) / (node["h"] / 2 + pad) <= 1
    return abs(x - node["cx"]) <= node["w"] / 2 + pad and abs(y - node["cy"]) <= node["h"] / 2 + pad


def _thin(pts, step: float = 55.0, tail: float = 46.0):
    """Keep sparse points; Excalidraw scales the arrowhead by the last segment, so keep that one long."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.dist(p, out[-1]) >= step:
            out.append(p)
    end = pts[-1]
    while len(out) > 1 and math.dist(out[-1], end) < tail:
        out.pop()
    out.append(end)
    return out


def _segment(s0: float, s1: float, nodes, cx, cy) -> list[tuple[float, float]]:
    """Visible path points between two consecutive nodes (trimmed where it enters a node)."""
    if s1 <= s0:
        s1 += 1.0
    n = max(8, int((s1 - s0) / 0.0015))
    pts, started = [], False
    for i in range(n + 1):
        p = _lem((s0 + (s1 - s0) * i / n) % 1.0, cx, cy)
        inside = any(_inside(p, nd) for nd in nodes)
        if not started:
            if not inside:
                started = True
                pts.append(p)
            continue
        if inside:
            break
        pts.append(p)
    return _thin(pts)


STAGES = [  # key, label, sub, s, theme, icon
    ("plan", "Plan", "isolation, RBAC, region, quota, ownership", 0.595, "grape", "blueprints"),
    ("build", "Build", "agent, model, tools, knowledge, guardrails", 0.705, "green", "agent"),
    ("eval", "Evaluate", "datasets, evaluators, simulation, red team", 0.855, "violet", "metrics"),
    ("deploy", "Deploy", "immutable version, publish, gradual rollout", 0.148, "green", "builds"),
    ("operate", "Operate", "inventory, policy, quota, SOC routing", 0.272, "grape", "dashboard"),
    ("monitor", "Monitor", "traces, alerts, continuous and scheduled evals", 0.332, "violet", "app-insights"),
    ("optimize", "Optimize", "prompts, tools, models - then re-evaluate", 0.452, "green", "gear"),
]
GATES = [  # key, label, s, theme, caption, (dx, dy) of caption centre, align
    ("g1", "G1", 0.775, "violet", "pre-merge\nsmoke eval", (-100, 0), "right"),
    ("g2", "G2", 0.950, "violet", "pre-prod\nquality gate", (-30, 64), "center"),
    ("g3", "G3", 0.036, "pink", "safety and\nred-team gate", (92, -4), "left"),
    ("g4", "G4", 0.083, "grape", "approval", (0, -58), "center"),
    ("g6", "G6", 0.213, "yellow", "cost and\nquota guard", (94, 0), "left"),
    ("g5", "G5", 0.392, "violet", "post-deploy\nguard", (0, 62), "center"),
]


def _loop(cv: Canvas, x0: float, y0: float, width: float) -> float:
    """Draw the flywheel; returns the bottom y of the drawing."""
    cx, cy = x0 + width / 2, y0 + 392
    # lobe tints first so the path and nodes sit on top
    left = [_lem(0.5 + i / 160, cx, cy) for i in range(81)]
    right = [_lem(i / 160, cx, cy) for i in range(81)]
    cv.poly(left + [left[0]], kind="line", stroke="transparent", sw=0, fill="#f3f0ff", fill_style="solid", curved=True)
    cv.poly(right + [right[0]], kind="line", stroke="transparent", sw=0, fill="#ebfbee", fill_style="solid", curved=True)

    nodes = []
    for key, label, sub, s, th, icon in STAGES:
        px, py = _lem(s, cx, cy)
        nodes.append(dict(key=key, label=label, sub=sub, s=s, th=th, icon=icon, cx=px, cy=py, w=248, h=98, gate=False))
    for key, label, s, th, cap, off, al in GATES:
        px, py = _lem(s, cx, cy)
        nodes.append(dict(key=key, label=label, s=s, th=th, cap=cap, off=off, al=al, cx=px, cy=py, w=104, h=80, gate=True))
    nodes.sort(key=lambda n: n["s"])

    # arrows between consecutive nodes, drawn first (behind the nodes)
    for i, nd in enumerate(nodes):
        nxt = nodes[(i + 1) % len(nodes)]
        pts = _segment(nd["s"], nxt["s"], nodes, cx, cy)
        if len(pts) < 2:
            continue
        if nd["key"] == "optimize":   # the return strand
            arrow(cv, pts, color="#343a40", sw=3, curved=True, end_head="arrow", dash="dashed", label="feedback",
                  label_size=16, label_t=0.2, label_bg=True, label_pos="right")
        else:
            arrow(cv, pts, color="#343a40", sw=3, curved=True, end_head="arrow")

    for nd in nodes:
        if nd["gate"]:
            Box(nd["w"], nd["label"], h=nd["h"], theme=nd["th"], shape="diamond", size=19).place(cv, nd["cx"] - nd["w"] / 2, nd["cy"] - nd["h"] / 2)
            dx, dy = nd["off"]
            tw, th_ = text_size(nd["cap"], 14)
            if nd["al"] == "right":
                tx = nd["cx"] + dx - tw
            elif nd["al"] == "left":
                tx = nd["cx"] + dx
            else:
                tx = nd["cx"] + dx - tw / 2
            cv.text(tx, nd["cy"] + dy - th_ / 2, nd["cap"], size=14, color="#343a40", align=nd["al"] if nd["al"] != "center" else "center", w=tw)
        else:
            b = Box(nd["w"], nd["label"], h=nd["h"], theme=nd["th"], sub=nd["sub"], icon=nd["icon"], icon_pos="left",
                    icon_size=34, size=21, sub_size=14)
            b.place(cv, nd["cx"] - nd["w"] / 2, nd["cy"] - nd["h"] / 2)
            n = [k[0] for k in STAGES].index(nd["key"]) + 1
            numbered(cv, b.x + 6, b.y + 4, n, theme=nd["th"], d=30, size=17)

    # lobe captions
    lx, rx = cx - 0.56 * LOOP_A, cx + 0.56 * LOOP_A
    for mx, title, sub, body, col in (
        (lx, "INNER LOOP", "DataOps - experimentation - evaluation", "before release", "#5f3dc4"),
        (rx, "OUTER LOOP", "deployment - inferencing and monitoring - feedback", "in production", "#2b8a3e"),
    ):
        tw = 330
        cv.text(mx - tw / 2, cy - 78, title, size=32, color=col, align="center", w=tw)
        cv.text(mx - tw / 2, cy - 36, sub, size=16, color="#343a40", align="center", w=tw, wrap=tw)
        cv.text(mx - tw / 2, cy + 20, body, size=15, color="#495057", align="center", w=tw)
    return cy + 392


def _legend(cv: Canvas, x: float, y: float, w: float) -> float:
    with cv.panel(x, y, title="How to read this canvas", theme="gray", style="dotted", pad=18, title_size=20, w=w) as p:
        cy = p.iy + 2
        cx = p.ix
        c1 = Chip("Documented on Microsoft Learn", theme="blue", fill="hatch", size=15).place(cv, cx, cy)
        cx = c1.right + 16
        c2 = Chip("Our synthesis / proposal", theme="orange", fill="none", dash="dashed", size=15).place(cv, cx, cy)
        cx = c2.right + 36
        draw_badge(cv, cx, cy + 4, "preview")
        t = cv.text(cx + 80, cy + 4, "preview feature (status as of 2026-11-03)", size=15)
        cx = t.right + 36
        draw_badge(cv, cx, cy + 4, "docs disagree")
        t = cv.text(cx + 128, cy + 4, "Learn pages contradict each other", size=15)
        cx = t.right + 36
        Box(44, "G", h=34, theme="violet", shape="diamond", size=14).place(cv, cx, cy - 2)
        cv.text(cx + 54, cy + 4, "release gate (G1-G6 numbering is ours; the evidence is documented)", size=15)
    return p.bottom


def _bullets_h(items, w: float, size: int = 15, gap: int = 6) -> float:
    h = 0.0
    for it in items:
        txt = it[2:] if it.startswith("! ") else it
        h += len(wrap_text(txt, (w - 22) * 0.965, size)) * size * 1.25 + gap
    return h - gap if items else 0.0


def _bullets(cv: Canvas, x: float, y: float, w: float, items, *, theme_name: str = "gray", size: int = 15,
             gap: int = 6) -> float:
    """Ring-bullet list drawn straight on the canvas (same look as Card bullets); returns the bottom y."""
    th = theme(theme_name)
    cy, lh = y, size * 1.25
    for it in items:
        warn = it.startswith("! ")
        txt = it[2:] if warn else it
        lines = wrap_text(txt, (w - 22) * 0.965, size)
        mc = "#e03131" if warn else (th.stroke if theme_name not in ("gray", "ink") else "#f08c00")
        cv.ellipse(x + 2, cy + lh / 2 - 4, 9, 9, stroke=mc, sw=2, rough=0)
        cv.text(x + 22, cy, "\n".join(lines), size=size, color="#c92a2a" if warn else INK)
        cy += len(lines) * lh + gap
    return cy - gap


def _src_line(cv: Canvas, x: float, y: float, label: str, url: str) -> float:
    t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
    return t.bottom


def _resource(cv: Canvas, x: float, y: float, w: float, title: str, projects, *, sub: str | None = None):
    """A Foundry resource (blue panel) with project boxes (green) inside."""
    with cv.panel(x, y, title=title, sub=sub, theme="blue", style="solid", fill="soft", pad=12, title_size=17,
                  sub_size=13, w=w) as p:
        n = len(projects)
        pw = (w - 24 - 10 * (n - 1)) / n
        px = p.ix
        for name in projects:
            Box(pw, name, h=40, theme="green", size=14).place(cv, px, p.iy)
            px += pw + 10
    return p


def _bar(cv: Canvas, x: float, y: float, w: float, segs, h: float = 46) -> float:
    """Stacked traffic bar. segs: [(label, fraction, theme)]."""
    cx = x
    for label, frac, th_name in segs:
        th = theme(th_name)
        sw_ = w * frac
        cv.rect(cx, y, sw_, h, stroke=th.stroke, fill=th.fill, style="solid", sw=2, round_=False, rough=0)
        tw, thh = text_size(label, 16)
        cv.text(cx + (sw_ - tw) / 2, y + (h - thh) / 2, label, size=16, color=th.deep)
        cx += sw_
    return y + h


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "AgentOps on Microsoft Foundry",
        "The end-to-end loop - plan, build, evaluate, deploy, operate, monitor, optimize - with environments, versions, gates, rollback and owners",
        icon="foundry", w=W)
    y = _legend(cv, 0, bottom + 26, W) + 46

    # ------------------------------------------------------------------------------------------ 1  the loop
    section_header(cv, 0, y, "1   The loop: seven stages, six gates, two nested cycles",
                   sub="Our synthesis of the Foundry agent lifecycle, Cloud Adoption Framework and GenAIOps guidance - the stage names are ours, every capability named is documented",
                   size=32, w=W)
    loop_w = cw(4)
    y0 = y + 100
    loop_bottom = _loop(cv, 0, y0, loop_w)
    with cv.panel(0, loop_bottom + 14, title="Govern and secure - continuous, across all seven stages (CAF)", theme="grape",
                  style="solid", fill="soft", pad=18, title_size=22, w=loop_w) as gp:
        ChipFlow(["Responsible AI policies", "Governance and security", "Azure Policy", "Microsoft Defender",
                  "Network and RBAC baseline", "Foundry Control Plane", "AI gateway (API Management)",
                  "Multi-point guardrails", "Centralized blocklists"], loop_w - 36, theme="grape", size=16).place(cv, gp.ix, gp.iy)

    rx, rw = cw(4) + GAP, cw(2)
    steps = [
        ("Choose an agent type", "prompt, voice prompt or hosted", False),
        ("Create and test", "in the playground or in code", False),
        ("Add tools and data", "configuration must succeed before you save", False),
        ("Save changes as versions", "immutable; compare versions", False),
        ("Debug with tracing", "tool calls, latency, end to end", True),
        ("Evaluate quality and safety", "repeatable runs catch regressions", True),
        ("Optimize hosted agents", "agent optimizer", True),
        ("Publish and integrate", "agent application with a stable endpoint", False),
        ("Monitor and iterate", "update and republish as needed", False),
    ]
    with cv.panel(rx, y0, title="Foundry's own 9-step agent lifecycle (documented)", theme="green", style="solid",
                  fill="soft", pad=20, title_size=24, w=rw) as sp:
        bw, bh, bg = (rw - 40 - 2 * 18) / 3, 92, 18
        for i, (lab, sub, prev) in enumerate(steps):
            bx = sp.ix + (i % 3) * (bw + bg)
            by = sp.iy + 8 + (i // 3) * (bh + 22)
            Box(bw, lab, h=bh, theme="green", sub=sub, size=17, sub_size=14).place(cv, bx, by)
            numbered(cv, bx + 4, by + 4, i + 1, theme="green", d=28, size=16)
            if prev:
                draw_badge(cv, bx + bw - 76, by - 12, "preview")
        _src_line(cv, sp.ix, sp.iy + 8 + 3 * (bh + 22) - 8, "Agent development lifecycle", learn("agents/concepts/development-lifecycle"))
    flows = Card(rw, "Six flows around the loop", [
        "A  Plan boundaries -> choose topology per environment -> IaC the platform -> policies and guardrails",
        "B  Build in the exploration or dev project: create agent -> add tools -> save version -> trace -> evaluate",
        "C  CI: eval gates -> red-team gate -> build image (hosted) -> deploy to test project -> regression tests",
        "D  Approve -> pin prod -> deploy candidate -> canary 10% (preview) -> inspect errors, latency, quality -> ramp -> 100%, or roll back",
        "E  Operate: dashboards, alerts, continuous eval, drift checks, monthly quota review, quarterly audit",
        "F  Optimize: eval results + traces -> optimizer or prompt tweaks -> new version -> back to B",
    ], theme="gray", dash="dashed", badge="Our synthesis", icon="workflow", fill="soft")
    flows.place(cv, rx, sp.bottom + 24)

    y2 = max(gp.bottom, flows.bottom) + 70
    y3 = _stages(cv, y2)
    y4 = _environments(cv, y3 + 70)
    y5 = _versions(cv, y4 + 70)
    y6 = _promotion(cv, y5 + 70)
    y7 = _gates(cv, y6 + 70)
    y8 = _cadence(cv, y7 + 70)
    y9 = _raci(cv, y8 + 70)
    sources(cv, 0, y9 + 60, [
        ("Agent development lifecycle", learn("agents/concepts/development-lifecycle")),
        ("Plan your Foundry rollout", learn("concepts/planning")),
        ("Observability in Microsoft Foundry", learn("concepts/observability")),
        ("Promote hosted agents to production with azd (preview)", learn("agents/how-to/deploy-hosted-agent-production")),
        ("Set up CI/CD for hosted agents with azd (preview)", learn("agents/how-to/set-up-ci-cd-cli")),
        ("Manage hosted agents (endpoint routing, release without changing production)", learn("agents/how-to/manage-hosted-agent")),
        ("Hosted agents in Foundry Agent Service", learn("agents/concepts/hosted-agents")),
        ("Run agent evaluations with the azd CLI (preview)", learn("observability/how-to/azure-developer-cli-evaluation")),
        ("Monitor agents with the Agent Monitoring Dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard")),
        ("CAF: Integrate, manage and operate AI agents", learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base="")),
        ("CAF: Organizational readiness for AI agents", learn("azure/cloud-adoption-framework/ai-agents/organization-people-readiness-plan", base="")),
        ("Architecture Center: GenAIOps for MLOps practitioners", learn("azure/architecture/ai-ml/guide/genaiops-for-mlops", base="")),
        ("Well-Architected: MLOps and GenAIOps for AI workloads", learn("azure/well-architected/ai/mlops-genaiops", base="")),
        ("Baseline Microsoft Foundry chat reference architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")),
    ], w=W, cols=3)


# ----------------------------------------------------------------------------------------------- 2 stage by stage
def _stages(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2   Stage by stage: what happens and which Foundry or Azure capability backs it",
                   sub="Documented capabilities grouped into our seven stages (stage names are ours)", size=32, w=W)
    ty = y + 100
    rows = [
        [("Plan", "grape"),
         "Business and technology plan, organizational readiness and data architecture. Decide isolation boundaries, capability and RBAC needs, resource topology, security baseline, model/region/capacity, connectivity, automation and operations, self-serve guardrails and ownership.",
         "Foundry 'Plan your rollout' (concepts/planning); Cloud Adoption Framework (CAF) 'Plan for agents'"],
        [("Govern and secure", "grape"),
         "Responsible AI policies, governance and security; prepare the environment (policy, Defender, network).",
         "CAF 'Govern and secure AI agents'; Azure Policy; Microsoft Defender; Foundry Control Plane"],
        [("Build", "green"),
         "1 Agent orchestration (charter, managed vs code-first, deterministic workflows). 2 Model selection (tiered; quota and cost governance). 3 Knowledge, tools and memory (explicit tool boundaries, human in the loop for high-impact actions, externalized state). 4 Observability. 5 Security (multi-point guardrails, centralized blocklists).",
         "CAF 'Process to build agents'; agent types prompt / voice / hosted; Toolbox; Foundry Skills"],
        [("Evaluate", "violet"),
         "Pre-production evaluation on datasets with evaluators and simulation; AI red teaming (local or cloud); regression run after any meaningful change.",
         "Evaluations + datasets; built-in and custom evaluators; AI Red Teaming Agent (PyRIT; cloud runs for pre-deployment scale and scheduled post-deployment)"],
        [("Deploy", "green"),
         "Save an immutable version, then publish it as an agent application (stable endpoint) or deploy a hosted-agent version. Promote the same source revision dev -> test -> prod; gateway-based progressive rollout.",
         "Agent versions; azd (azd deploy, azd ai agent endpoint update); CI/CD - see the CI/CD and IaC canvas"],
        [("Operate", "grape"),
         "Asset lifecycle (estate audit, retire unused agents), continuous compliance and security (SOC routing), quota optimization (monthly), administration (inventory, AI gateway, pause/resume).",
         "CAF 'Operate AI agents'; Foundry Control Plane; AI gateway (Azure API Management); Azure Policy; Defender"],
        [("Monitor", "violet"),
         "Operational metrics, traces, continuous and scheduled evaluation, scheduled red team, alerts, user feedback.",
         "Agent Monitoring Dashboard (Application Insights), tracing (OpenTelemetry), Notification Center, Azure Monitor"],
        [("Optimize", "green"),
         "Improve prompts and instructions, skills, tools and models using the evaluation signal; re-evaluate.",
         "Agent optimizer + prompt optimizer (hosted agents, preview); azd ai agent optimize --config eval.yaml - does not auto-apply or redeploy"],
    ]
    t = Table([("Stage", 150), ("What happens", 780), "Foundry / Azure capability (as documented)"], rows, w=cw(4),
              theme="blue", size=15, head_size=16)
    t.place(cv, 0, ty)

    rx, rw = cw(4) + GAP, cw(2)
    g1 = Card(rw, "GenAIOps extends MLOps", [
        "Inner loop = DataOps, experimentation, evaluation. Outer loop = deployment, inferencing and monitoring, feedback loop.",
        "Adds to MLOps: prompt and RAG experimentation, search-index maintenance, orchestrator and data-store deployment, gateway-based progressive rollout, content-safety monitoring, quota and throttling management.",
    ], theme="gray", icon="learn", src=[("GenAIOps for MLOps practitioners", learn("azure/architecture/ai-ml/guide/genaiops-for-mlops", base=""))])
    g2 = Card(rw, "Well-Architected view", [
        "DevOps + DataOps + MLOps + GenAIOps: 'Automation and monitoring are your key operational strategies'.",
        "Put qualitative tests in release pipelines - outputs are non-deterministic. Prevent model drift and decay.",
        "Maturity model: MLOps maturity plus workload-specific GenAIOps levels with entry and exit criteria for data and prompt versioning, experimentation and evaluation, deployment automation, monitoring, content safety and resource management.",
    ], theme="gray", icon="learn", src=[("MLOps and GenAIOps for AI workloads", learn("azure/well-architected/ai/mlops-genaiops", base=""))])
    g1.place(cv, rx, ty)
    g2.place(cv, rx, g1.bottom + 24)
    with cv.panel(rx, g2.bottom + 24, title="Evaluate across the lifecycle (observability overview)", theme="violet",
                  style="solid", fill="soft", pad=20, title_size=22, w=rw) as lp:
        bw = (rw - 40 - 2 * 44) / 3
        bxs = [
            Box(bw, "1  Base model selection", h=150, theme="violet", sub="benchmarks; compare quality and safety", size=17, sub_size=14),
            Box(bw, "2  Pre-production evaluation", h=150, theme="violet", sub="bring your own data; red teaming", size=17, sub_size=14),
            Box(bw, "3  Post-production monitoring", h=150, theme="violet",
                sub="operational metrics, continuous and scheduled evaluation, scheduled red team, Azure Monitor alerts", size=17, sub_size=14),
        ]
        row(cv, lp.ix, lp.iy + 4, bxs, gap=44)
        connect(cv, bxs[0], bxs[1])
        connect(cv, bxs[1], bxs[2])
        _src_line(cv, lp.ix, bxs[0].bottom + 12, "Observability in Foundry", learn("concepts/observability"))
    return max(t.bottom, lp.bottom)


# ----------------------------------------------------------------------------------------------- 3 environments
def _environments(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3   Environments: separate projects, resources and subscriptions",
                   sub="Isolation increases from exploration to production - environment names alone don't isolate Azure resources",
                   size=32, w=W)
    ty = y + 100
    tw_, tg = 632, 44
    specs = [
        dict(title="Exploration", sub="co-located by default", style="dotted",
             res=[("Foundry resource (shared)", ["Use case A", "Use case B", "Use case C"])],
             bullets=["One Foundry resource, many projects - one per use case",
                      "Limited capacity, pre-connected data and tools, non-production data",
                      "! Shared blast radius: incidents, quota exhaustion, misconfiguration",
                      "Default to colocation unless compliance requires isolation"]),
        dict(title="Dev / Test", sub="isolated, or co-located for related use cases", style="dashed",
             res=[("Resource: dev", ["Project dev"]), ("Resource: test", ["Project test"])],
             bullets=["Use cases that share CRM data or personas may stay co-located through dev/test",
                      "Fully isolated dev/test and prod environments for proven use cases",
                      "Hosted agents: bind each environment to a separate existing project"]),
        dict(title="Production", sub="isolated by default", style="solid",
             res=[("Workload A", ["Primary project"]), ("Workload B", ["Primary project"])],
             bullets=["One Foundry resource per production workload boundary (often one primary project)",
                      "Independent quota, cost and access boundaries",
                      "Trade-off: harder self-serve and more setup",
                      "Colocation only as a deliberate, documented exception"]),
    ]
    panels = []
    inner = tw_ - 40
    for i, sp in enumerate(specs):
        with cv.panel(i * (tw_ + tg), ty, title=sp["title"], sub=sp["sub"], theme="gray", style=sp["style"], fill="soft",
                      pad=20, title_size=28, sub_size=16, w=tw_, min_h=470) as p:
            n = len(sp["res"])
            rw_ = (inner - 16 * (n - 1)) / n
            rb = p.iy + 6
            for j, (rt, projs) in enumerate(sp["res"]):
                rp = _resource(cv, p.ix + j * (rw_ + 16), p.iy + 6, rw_, rt, projs)
                rb = max(rb, rp.bottom)
            _bullets(cv, p.ix, rb + 20, inner, sp["bullets"], theme_name="gray", size=15)
        panels.append(p)
    pb = max(p.bottom for p in panels)
    arrow(cv, [(0, pb + 34), (cw(4), pb + 34)], color="#343a40", sw=3, end_head="arrow")
    t = cv.text(cw(4) / 2 - 130, pb + 40, "isolation increases", size=20, color="#343a40")
    note = Note(cw(4), "Each tier maps to its own azd environment, bound to that project's subscription and region: azd env new development | test | production --subscription <id> --location <region>. Switching an azd environment doesn't copy a project's dependencies or deployment permissions.",
                kind="info", title="Environments in the hosted-agent promotion flow",
                src=[("Promote hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production"))])
    note.place(cv, 0, pb + 80)

    rx, rw = cw(4) + GAP, cw(2)
    c1 = Card(rw, "Isolation rules from the docs", [
        "'For production, treat isolation as the default. Use colocation as a deliberate exception.'",
        "'Set a prod policy that defaults to isolation, unless a documented exception allows colocation.'",
        "'Assign ownership for each boundary, including security, cost, and incident response ownership.'",
        "Architecture Center baseline: distinct, isolated Foundry resources, including dependencies, for experimentation, testing and production.",
        "Each project needs its own dependencies and deployment permissions.",
        "Well-Architected: lower environments that handle production data must be as secure as production.",
    ], theme="grape", icon="management-group", src=[
        ("Plan your Foundry rollout", learn("concepts/planning")),
        ("Baseline Foundry chat architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")),
    ])
    c2 = Card(rw, "Feature caveats that shape the layout", [
        "Fine-tune training is default-project only: use separate Foundry resources for independent fine-tuning per team.",
        "Some Foundry Tools APIs (for example Speech-to-text) need RBAC at the parent resource scope.",
        "Connections can be defined at account or project level; account-level connections are inherited by all projects.",
        "Control plane (Owner, Contributor) and data plane (for example Foundry User) roles are separate - management roles aren't sufficient for all development scenarios.",
    ], theme="gray", icon="resource-group", src=[("Plan your Foundry rollout", learn("concepts/planning"))])
    c1.place(cv, rx, ty)
    c2.place(cv, rx, c1.bottom + 24)
    return max(note.bottom, c2.bottom)


# ----------------------------------------------------------------------------------------------- 4 versions
def _versions(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4   Version ledger: what to version, and how",
                   sub="Anything that can change agent behavior should be versioned and recoverable", size=32, w=W)
    ty = y + 100
    rows = [
        [("Prompt / declarative agent", "green"),
         "Immutable versions; the name is fixed at creation and code refers to <agent_name>:<version>. Compare setup, chat output and YAML across versions; direct requests to a specific version for controlled deployment and rollback. Limit: 1,000 versions per agent (HTTP 400 UserError, terminal) as of 2026-11-03.",
         "Unsaved playground changes are lost - save a version for history, monitoring and full evaluation. Use get-or-create; treat a 404 as terminal."],
        [("Hosted agent", "green"),
         "A version is an immutable snapshot of container image, CPU and memory, environment variables and protocol configuration. Environment variables are set per version. An unchanged deployment can reuse an existing version.",
         "Terraform manages the named agent, not each version - azd owns version deployment."],
        [("Instructions and prompts", "green"),
         "Keep them in source control with automated validation: eval scripts or secondary agents check safety and format before deploy. Use structured inputs for per-request parameters (instruction text only - don't template tool endpoints).",
         "CAF: standardize the instruction architecture."],
        [("Model deployment", "blue"),
         "Pin the model version and set the deployment's version upgrade option to not auto-upgrade (Architecture Center) so an update can't change responses before validation. Keep old and new deployments side by side behind a gateway for progressive rollout.",
         "Retirement schedule and NoAutoUpgrade behavior: see the FinOps and capacity operations canvas."],
        [("Datasets and evaluators", "violet"),
         "eval.yaml pins registered dataset and evaluator versions; azd ai agent eval update registers new versions. Existing evaluation runs stay tied to the versions they used. Treat version fields as strings.",
         "Don't let 'latest' silently change the recipe."],
        [("RAG data and indexes", "teal"),
         "Version the data and keep experiments reproducible (chunking and embedding variants, rollback). Plan index rebuilds and maintenance, including right-to-be-forgotten requests.",
         "Index updates must meet freshness and compliance needs."],
        [("Infrastructure as code", "grape"),
         "Bicep or Terraform modules; remote state per environment (separate state key).",
         "Don't commit state or saved plans."],
        [("Agent definitions in Git", "gray"),
         "JSON or YAML definitions, tool bindings and knowledge references under source control; scheduled export for disaster recovery.",
         "Avoid untracked portal edits."],
    ]
    t = Table([("Asset", 220), ("Versioning mechanism", 1100), "Gotcha"], rows, w=cw(4), theme="green", size=15, head_size=16)
    t.place(cv, 0, ty)
    rx, rw = cw(4) + GAP, cw(2)
    rec = Card(rw, "Release record - capture it on every release", [
        "Agent version (<name>:<version>) plus the source commit or image digest",
        "Model deployment name and pinned version",
        "Dataset and evaluator versions used by the eval gate",
        "Final endpoint routing configuration, so the next pipeline run doesn't reapply a stale traffic split",
        "Gate evidence: scores, thresholds, approver (Ignite 2025 session summary, not Learn)",
    ], theme="gray", dash="dashed", badge="Our synthesis", icon="versions", fill="soft",
        src=[("Promote hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production"))])
    n1 = Note(rw, "The agent name is fixed at creation; refer to it as <agent_name>:<version>. A 404 for an ID you created earlier means the agent was deleted - recreate it (get-or-create) and never retry the same ID in a loop.",
              kind="info", title="Names and IDs", src=[("Agent development lifecycle", learn("agents/concepts/development-lifecycle"))])
    n2 = Note(rw, "Creating a version fails with HTTP 400 at the cap. Rotate old versions in your pipeline, but keep the stable and rollback versions - deleting an agent or a version isn't a rollback.",
              kind="warn", title="Version cap: 1,000 per agent (as of 2026-11-03)",
              src=[("Agent Service limits", learn("agents/concepts/limits-quotas-regions")), ("Manage hosted agents", learn("agents/how-to/manage-hosted-agent"))])
    col(cv, rx, ty, [rec, n1, n2], gap=24)
    return max(t.bottom, n2.bottom)


# ----------------------------------------------------------------------------------------------- 5 promotion / rollback
def _promotion(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5   Promotion and rollback: three kinds of release",
                   sub="Prompt agents, hosted agents and model deployments roll out differently - and the Learn pages are not consistent about hosted-agent canaries",
                   size=32, w=W)
    top = y + 100
    LW, SW, SH, SG = 300, 300, 104, 100
    sx = [LW + 56 + i * (SW + SG) for i in range(4)]
    nx = sx[3] + SW + 56
    nw = W - nx

    def chain(yy, steps, theme_name):
        bxs = []
        for xx, (lab, sub) in zip(sx, steps):
            bxs.append(Box(SW, lab, h=SH, theme=theme_name, sub=sub, size=19, sub_size=14).place(cv, xx, yy))
        return bxs

    # ---- lane A: prompt agents
    Box(LW, "Prompt agents", h=SH, theme="green", sub="declarative and versioned", icon="agent", icon_pos="left",
        size=22, sub_size=14, fill="hatch").place(cv, 0, top)
    a = chain(top, [("Save a version", "immutable; <name>:<version>"),
                    ("Evaluate", "gates G1-G3 on that exact version"),
                    ("Publish as agent application", "stable endpoint to open, test, share, embed"),
                    ("Republish or redirect", "new version any time; direct requests to a specific version to roll back")], "green")
    for p, q in zip(a, a[1:]):
        connect(cv, p, q)
    na1 = Note(nw, "Permissions assigned to the project identity don't automatically transfer to the published agent. Reassign what the published agent identity needs.",
               kind="gotcha", title="Publishing changes the identity", src=[("Agent development lifecycle", learn("agents/concepts/development-lifecycle"))])
    na2 = Note(nw, "'Foundry doesn't provide built-in support for blue-green or canary deployments of agents.' Use an API gateway or custom router to shift traffic between agent versions, and coordinate agent removal with active chat sessions: migrate sessions, pin users, or force new sessions.",
               kind="info", title="Architecture Center: no built-in canary for agents",
               src=[("Baseline Foundry chat architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base=""))])
    na1.place(cv, nx, top)
    na2.place(cv, nx, na1.bottom + 16)
    laneA_bottom = max(top + SH, na2.bottom)

    # ---- lane B: hosted agents
    by = laneA_bottom + 40
    dev = Box(SW, "Dev", h=SH, theme="green", sub="azd deploy, invoke, record the source commit", size=19, sub_size=14).place(cv, sx[0], by)
    tst = Box(SW, "Test", h=SH, theme="green", sub="same commit; regression and integration tests", size=19, sub_size=14).place(cv, sx[1], by)
    gate = Box(150, "G4", h=SH, theme="grape", shape="diamond", size=20, sub="approval", sub_size=14)
    gate.place(cv, sx[2] + (SW - 150) / 2, by)
    prod = Box(SW, "Production", h=SH, theme="green", sub="pin, deploy candidate, test, shift traffic", size=19, sub_size=14).place(cv, sx[3], by)
    connect(cv, dev, tst, label="same commit", label_size=14, label_pos="above")
    connect(cv, tst, gate)
    connect(cv, gate, prod)
    nb1 = Note(nw, "By default a Foundry endpoint follows the latest version. A pipeline that deploys and then tests can change production traffic before the test runs - pin production to its current version first.",
               kind="gotcha", title="Default routing = latest version",
               src=[("Set up CI/CD for hosted agents (preview)", learn("agents/how-to/set-up-ci-cd-cli"))])
    nb1.place(cv, nx, by)
    # traffic rail
    ry = max(by + SH, nb1.bottom) + 66
    bw_, bg_ = 360, 70
    rail = [
        ("Default routing", "follows the latest version: a new version takes all traffic as soon as it exists",
         [("latest = new version, 100%", 1.0, "red")]),
        ("1  Pin stable", "azd ai agent endpoint update - before azd deploy; read it back with endpoint show",
         [("v1 100%", 1.0, "blue")]),
        ("2  Canary (preview)", "test the candidate: invoke --version 2 --new-session --new-conversation",
         [("v1 90%", 0.9, "blue"), ("10%", 0.1, "green")]),
        ("3  Ramp", "approval required before each increase; review errors, latency, quality",
         [("v1 50%", 0.5, "blue"), ("v2 50%", 0.5, "green")]),
        ("4  Complete", "keep v1 until the release is accepted; save the final routing config",
         [("v2 100%", 1.0, "green")]),
        ("Rollback", "rewrite the rules to the stable version - no rebuild, no new version",
         [("v1 100%", 1.0, "blue")]),
    ]
    cv.text(sx[0] - 4, ry - 42, "Version selector in hosted-agent production rollout (agentEndpoint.versionSelector, FixedRatio rules)", size=17, color="#2b8a3e")
    rects = []
    for i, (title, cap, segs) in enumerate(rail):
        bx = sx[0] - 4 + i * (bw_ + bg_)
        _bar(cv, bx, ry, bw_, segs)
        r = Rect2()
        r.x, r.y, r.w, r.h = bx, ry, bw_, 46
        rects.append(r)
        cv.text(bx, ry + 54, title, size=17, color="#2b8a3e" if i not in (0, 5) else ("#c92a2a" if i == 0 else "#495057"))
        cv.text(bx, ry + 78, cap, size=14, color="#343a40", wrap=bw_)
    for i in (1, 2, 3):
        connect(cv, rects[i], rects[i + 1], gap=4)
    connect(cv, rects[3], rects[5], a_side="top", b_side="top", via=[(rects[3].cx, ry - 22), (rects[5].cx, ry - 22)], dash="dashed",
            color="#e03131", curved=True, label="a canary check fails", label_size=14, label_t=0.5, label_pos="above")
    rail_bottom = ry + 150
    dd = Note(W - sx[0], "The 'Promote hosted agents to production' page (preview) documents FixedRatio traffic splits (for example 90/10, 50/50). The 'Hosted agents' concept page and the 'Manage hosted agents' page say an endpoint serves one version at 100% and traffic splitting isn't supported, and the Architecture Center baseline says there is no built-in canary for agents. Treat percentage canaries as preview and in flux. The sequence common to the pages: pin production, test a version-pinned candidate session, promote by re-pointing the selector at 100%, roll back by re-pointing it.",
              kind="warn", title="Docs disagree on hosted-agent traffic splitting (as of 2026-11-03)",
              src=[("Promote hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production")),
                   ("Manage hosted agents", learn("agents/how-to/manage-hosted-agent")),
                   ("Hosted agents concept page", learn("agents/concepts/hosted-agents"))])
    dd.place(cv, sx[0], rail_bottom + 14)
    Box(LW, "Hosted agents", h=dd.bottom - by, theme="green", sub="container image or source code; the endpoint serves a version", icon="container-apps",
        icon_pos="top", size=22, sub_size=14, fill="hatch").place(cv, 0, by)
    badge_y = by - 14
    draw_badge(cv, LW - 80, badge_y, "preview")

    # ---- lane C: model deployments
    cy_ = dd.bottom + 44
    Box(LW, "Model versions", h=SH, theme="blue", sub="deployments behind a gateway", icon="openai", icon_pos="left",
        size=22, sub_size=14, fill="hatch").place(cv, 0, cy_)
    c = chain(cy_, [("Pin the version", "version upgrade option = no auto-upgrade"),
                    ("Deploy beside the old", "Standard or provisioned side by side behind the gateway"),
                    ("Validate", "run the test suite - gates G1-G3 - before user traffic"),
                    ("Shift traffic", "gateway moves traffic incrementally (blue-green)")], "blue")
    for p, q in zip(c, c[1:]):
        connect(cv, p, q)
    nc = Note(nw, "Retirement dates, replacement lead times and NoAutoUpgrade behavior are covered on the FinOps and capacity operations canvas.",
              kind="info", title="See also")
    nc.place(cv, nx, cy_)
    return max(cy_ + SH, nc.bottom)


# ----------------------------------------------------------------------------------------------- 6 gates
def _gates(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6   Gates: what stops a bad release",
                   sub="The G1-G6 numbering is ours; the evidence and automation behind each gate are documented",
                   size=32, w=W)
    ty = y + 100
    ev = [("Run agent evaluations with azd (preview)", learn("observability/how-to/azure-developer-cli-evaluation"))]
    cards = [
        Card(COL, "G1  Pre-merge smoke", [
            "azd ai agent eval run --no-prompt runs the checked-in quick-eval recipe (eval.yaml)",
            "No --fail-on here: it can't enforce a threshold",
            "! A non-empty CLI output isn't a smoke test - check the expected response content",
        ], theme="violet", icon="azd", badge="preview", src=ev),
        Card(COL, "G2  Pre-prod quality gate", [
            "azd ai eval run start --fail-on pass-rate=0.8 --no-prompt",
            "Needs the optional azure.ai.evaluations extension; config is evals/azure.eval.yaml, not eval.yaml",
            "GitHub Action microsoft/ai-agent-evals@v3-beta or Azure DevOps AIAgentEvaluation@2: confidence intervals and pairwise significance between agent versions",
            "! To minimize costs, don't run evaluation on every commit",
        ], theme="violet", icon="metrics", badge="preview",
            src=[("Evaluation in GitHub Actions (preview)", learn("how-to/evaluation-github-action")),
                 ("Evaluation in Azure DevOps (preview)", learn("how-to/evaluation-azure-devops"))]),
        Card(COL, "G3  Safety and red-team gate", [
            "AI Red Teaming Agent: local scans (preview) while developing",
            "Cloud runs for pre-deployment scans: larger attack-strategy x risk-category matrices plus agentic risks",
            "'Prohibited actions' is an agents-only, cloud-only risk category",
            "CAF: red team again, especially after major model updates or architectural changes",
        ], theme="pink", icon="pyrit", badge="preview",
            src=[("Run AI red teaming in the cloud", learn("how-to/develop/run-ai-red-teaming-cloud"))]),
        Card(COL, "G4  Approval", [
            "GitHub environment protection rules, or Azure DevOps approvals and checks, on the production environment",
            "Require approval before increasing the canary share",
            "Ignite 2025 session summary (not Learn): scores and thresholds stored in GitHub; humans approve or reject releases against them",
        ], theme="grape", icon="users",
            src=[("Promote hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production"))]),
        Card(COL, "G5  Post-deploy guard", [
            "Continuous evaluation on sampled live traffic: the rule fires on RESPONSE_COMPLETED; sampling uses max_hourly_runs=100, random or intelligent",
            "Scheduled evaluation on a golden dataset to detect drift; scheduled red team",
            "Alerts: latency, token usage, evaluation scores, red-team findings",
        ], theme="violet", icon="alerts", badge="preview",
            src=[("Agent Monitoring Dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard"))]),
        Card(COL, "G6  Cost and quota guard", [
            "Token caps and rate limits at the AI gateway",
            "Budgets",
            "Quota headroom check before deploying: Usages API (consumption vs limit) and Model Capacities API (deployable capacity)",
        ], theme="yellow", icon="cost-management",
            src=[("Foundry Models quota", learn("openai/how-to/quota"))]),
    ]
    _, bottom = row(cv, 0, ty, cards, gap=GAP)
    return bottom


# ----------------------------------------------------------------------------------------------- 7 change management
def _cadence(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "7   Change management: which event triggers which routine",
                   sub="Per release, per model change, continuous, monthly, quarterly - plus a phased adoption plan", size=32, w=W)
    ty = y + 100
    caf = [("CAF: Operate AI agents", learn("azure/cloud-adoption-framework/ai-agents/integrate-manage-operate", base=""))]
    cards = [
        Card(COL, "Per release", [
            "Eval, red team, approval and canary",
            "Record the release: version IDs, dataset and evaluator versions, image digest or commit, routing configuration",
        ], theme="green", icon="builds"),
        Card(COL, "Per model change", [
            "Triggers: a retirement notice, a version upgrade, a new model",
            "Run the regression suite and pin versions",
            "Red team again",
        ], theme="blue", icon="openai"),
        Card(COL, "Continuous", [
            "Feedback becomes a backlog of unresolved queries and feature requests (CAF continuous improvement cycles)",
            "Convert traces and feedback into evaluation datasets",
        ], theme="violet", icon="app-insights", src=caf),
        Card(COL, "Monthly (CAF)", [
            "Review consumption trends",
            "Adjust quotas by business priority",
            "Right-size model choice",
        ], theme="yellow", icon="cost-management", src=caf),
        Card(COL, "Quarterly (CAF)", [
            "Estate audit: retire unused agents - dormant agents consume quota and widen the attack surface",
            "Align availability with criticality",
        ], theme="grape", icon="compliance", src=caf),
        Card(COL, "Phased adoption", [
            "Start with specific business units and high-impact use cases, measure, then expand (CAF)",
            "Plan training and communication",
            "'Define rollback and incident response procedures for model and policy changes' (Foundry rollout guide)",
        ], theme="gray", icon="landing-zone", src=[("Plan your Foundry rollout", learn("concepts/planning"))]),
    ]
    _, bottom = row(cv, 0, ty, cards, gap=GAP)
    return bottom


# ----------------------------------------------------------------------------------------------- 8 roles and RACI
def _raci(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "8   Who owns what: roles and a proposed RACI",
                   sub="The roles come from the Cloud Adoption Framework; the RACI allocation is our proposal - the docs do not publish one",
                   size=32, w=W)
    ty = y + 100

    def rc(txt: str):
        base = txt.split(" ")[0]
        th = {"A/R": "green", "A": "green", "R": "blue", "C": "yellow", "I": "gray"}[base]
        return dict(text=txt, theme=th, align="center")

    rows = [
        ["Landing zone, Foundry resource topology, policy, network, quotas", rc("A/R"), rc("C"), rc("C"), rc("C"), rc("C")],
        ["Agent design, prompts, tools, knowledge", rc("C"), rc("A/R"), rc("C"), rc("I"), rc("I")],
        ["Evaluation datasets, evaluators, thresholds", rc("C"), rc("A/R"), rc("C (standards)"), rc("C"), rc("I")],
        ["Red teaming and guardrail configuration", rc("R (policy)"), rc("R"), rc("C"), rc("A"), rc("I")],
        ["Release approval to production", rc("C"), rc("A/R"), rc("I"), rc("C"), rc("I")],
        ["Runtime monitoring and on-call", rc("R (platform)"), rc("A/R (agent)"), rc("I"), rc("I"), rc("I")],
        ["Security alerts and jailbreak response", rc("C"), rc("C"), rc("I"), rc("A/R"), rc("I")],
        ["Quota and cost reviews", rc("R"), rc("R"), rc("I"), rc("I"), rc("A")],
        ["Estate audit and retiring agents", rc("A/R"), rc("R"), rc("C"), rc("C"), rc("C")],
    ]
    with cv.panel(0, ty, title="Proposed RACI - our synthesis, not Microsoft guidance", theme="orange", style="dashed",
                  fill="none", pad=24, title_size=24, w=cw(4)) as rp:
        lx = rp.ix
        for lab, th in (("A  accountable", "green"), ("R  responsible", "blue"), ("C  consulted", "yellow"), ("I  informed", "gray")):
            ch = Chip(lab, theme=th, size=15).place(cv, lx, rp.iy + 4)
            lx = ch.right + 14
        t = Table(["Activity", ("Platform", 220), ("Workload", 220), ("AI CoE", 220), ("SOC / Security", 220), ("FinOps", 220)],
                  rows, w=cw(4) - 48, theme="orange", size=15, head_size=16,
                  align=["left", "center", "center", "center", "center", "center"])
        t.place(cv, rp.ix, rp.iy + 52)
    rx, rw = cw(4) + GAP, cw(2)
    roles = Card(rw, "Roles in the CAF organizational readiness plan", [
        "Platform team: technical foundation and governance guardrails; audits and enforces responsible AI and governance",
        "Workload team: owns the end-to-end lifecycle of specific agents - requirements, domain data, conversation flows",
        "AI Center of Excellence: advisory - strategy, responsible AI principles, training, expert guidance",
        "SOC: CAF routes agent security alerts to the security operations center",
        "FinOps / Finance: added by us for budgets - inferred, not a role in the CAF list",
    ], theme="gray", icon="groups",
        src=[("CAF: Organizational readiness", learn("azure/cloud-adoption-framework/ai-agents/organization-people-readiness-plan", base=""))])
    roles.place(cv, rx, ty)
    rbac = Table([("Role", 300), "Where the lifecycle docs use it"], [
        [("Foundry Account Owner", "red"), "Create the account and project"],
        [("Role Based Access Control Administrator", "red"), "Role assignments in the standard agent setup"],
        [("Foundry User", "red"), "Create and edit agents (data plane)"],
        [("Foundry Agent Consumer", "red"), "Call agent endpoints only"],
        [("Foundry Owner", "red"), "CI provisioning with azd (with Contributor)"],
        [("Cognitive Services Contributor", "red"), "Model deployments"],
        [("Foundry Project Manager", "red"), "Create project connections"],
    ], w=rw, theme="red", size=14, head_size=15, title="RBAC roles that appear in the lifecycle docs", title_size=20)
    rbac.place(cv, rx, roles.bottom + 28)
    rn = Note(rw, "Foundry User, Owner, Account Owner and Project Manager were previously named Azure AI User, Owner, Account Owner and Project Manager. Role IDs and core permissions are unchanged.",
              kind="info", title="Renamed roles", src=[("Install the azd Foundry extensions", learn("agents/how-to/install-cli-foundry-extensions"))])
    rn.place(cv, rx, rbac.bottom + 24)
    return max(rp.bottom, rn.bottom)
