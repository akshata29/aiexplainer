"""Using AI to operate Foundry: Foundry MCP Server, Foundry Skill, azd ai, agent doctor, Insights, optimizer, Azure SRE Agent and Azure Copilot agents - what is real, what is preview, what is not AI."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="ai-assisted-ops", title="AI-assisted operations", section="6", order=5,
    description="Using AI to operate Foundry: the Foundry MCP Server (preview), Foundry Skill, azd ai agent doctor (not AI), Insights, Azure SRE Agent and Azure Copilot agents - what each can and cannot do, and what the docs do not say.",
    tags=["ai-ops", "mcp", "sre-agent", "copilot", "insights", "agent-doctor"],
)

ASOF = "as of 2026-11-03"
C4, G4 = 698, 56
W = 4 * C4 + 3 * G4          # 2960
C3 = (W - 2 * G4) / 3


def X4(i: int) -> float:
    return i * (C4 + G4)


def X3(i: int) -> float:
    return i * (C3 + G4)


S = dict(
    mcp_start=("Get started with Foundry MCP Server (preview)", learn("mcp/get-started")),
    mcp_tools=("Available tools and example prompts (preview)", learn("mcp/available-tools")),
    mcp_sec=("Foundry MCP Server security best practices", learn("mcp/security-best-practices")),
    skill=("Use the Microsoft Foundry Skill", learn("how-to/develop/use-microsoft-foundry-skill")),
    cli=("Use azd ai with coding agents", learn("agents/how-to/use-cli-with-coding-agents")),
    doctor=("azd ai agent doctor", learn("agents/how-to/agent-doctor")),
    insights=("Insights in Foundry (preview)", learn("observability/how-to/agent-insights")),
    fleet=("Monitoring across the fleet", learn("control-plane/monitoring-across-fleet")),
    canvas=("Foundry Canvas (preview)", learn("agents/concepts/foundry-canvas")),
    sre=("Azure SRE Agent overview", learn("azure/sre-agent/overview", base="")),
    sre_modes=("SRE Agent run modes", learn("azure/sre-agent/run-modes", base="")),
    sre_bill=("SRE Agent pricing and billing", learn("azure/sre-agent/pricing-billing", base="")),
    sre_cosmos=("Cosmos DB and the SRE Agent (preview)", learn("azure/cosmos-db/site-reliability-engineering-agent", base="")),
    cp_agents=("Agents in Azure Copilot", learn("azure/copilot/agents", base="")),
    cp_access=("Manage access to Azure Copilot", learn("azure/copilot/manage-access", base="")),
    cp_cap=("Azure Copilot capabilities", learn("azure/copilot/capabilities", base="")),
    cp_res=("Resiliency agent in Azure Copilot (preview)", learn("azure/copilot/resiliency-agent", base="")),
    obs=("Observability agent in Azure Monitor", learn("azure/azure-monitor/aiops/observability-agent-overview", base="")),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


# ---------------------------------------------------------------------------------------------- shared helpers
def pill(cv: Canvas, x: float, y: float, text: str, theme: str, size: int = 14, dashed: bool = False,
         solid: bool = True) -> float:
    """Label pill drawn without registering a block (safe on top of cards). Returns its width."""
    th = THEMES[theme]
    tw, thh = text_size(text, size)
    cv.rect(x, y, tw + 18, thh + 8, stroke=th.stroke, fill=th.fill if solid else "transparent", style="solid", sw=1.5,
            rough=0, dash="dashed" if dashed else "solid")
    cv.text(x + 9, y + 4, text, size=size, color=th.deep)
    return tw + 18


def head(cv: Canvas, y: float, n, text: str, sub: str | None = None, tags=(), color: str = INK) -> float:
    _, bottom = section_header(cv, 0, y, f"{n}   {text}", sub=sub, size=32, w=W, color=color)
    tx = W
    for label, theme, dashed in reversed(tags):
        wpx = text_size(label, 15)[0] + 18
        tx -= wpx
        pill(cv, tx, y + 8, label, theme, 15, dashed, solid=not dashed)
        tx -= 14
    return bottom + 22


DOC = ("Documented", "green", False)
SUG = ("Suggested - our synthesis", "orange", True)
INF = ("Inference (marked in the text)", "gray", True)
PREV = ("Preview", "orange", False)


def learn_line(cv: Canvas, x: float, y: float, items: list[tuple[str, str]]) -> float:
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=12, color=LINK, link=url)
        cx += t.w + 26
    return y + 18


def wrap(text: str, width: float, size: float) -> str:
    return "\n".join(wrap_text(text, width, size))


# pill vocabulary: LLM-driven / writes / maturity / human control
LLM_Y, LLM_P, LLM_N = "violet", "yellow", "gray"
WR_Y, WR_P, WR_N = "red", "yellow", "green"
M_PREV, M_GA, M_UNK = "orange", "green", "gray"
HUM = "blue"


class Tool(Rect2):
    """Toolbelt card: icon + title + status badge, four attribute pills, bullets, Learn links."""

    def __init__(self, w, title, body, *, theme, icon=None, badge=None, attrs=(), src=(), fill="soft",
                 title_size=22, body_size=15, pad=16, gap=5):
        self.th = THEMES[theme]
        self.w, self.title, self.icon, self.badge, self.attrs = w, title, icon, badge, list(attrs)
        self.src, self.fill, self.title_size, self.body_size, self.pad, self.gap = list(src), fill, title_size, body_size, pad, gap
        lr = metrics.line_ratio()
        inner = (w - 2 * pad) * 0.965
        self.icon_off = 46 if icon else 0
        label = {"preview": "Preview", "ga": "GA", "new": "New", "retiring": "Retiring", "classic": "Classic"}.get(badge, badge)
        self.badge_label = label
        self.badge_w = (text_size(label, 13)[0] + 18) if badge else 0
        t_w = inner - self.icon_off - (self.badge_w + 8 if badge else 0)
        self.t_lines = wrap_text(title, t_w, title_size)
        head_h = max(len(self.t_lines) * title_size * lr, 38 if icon else 0)
        y = pad + head_h + 8
        # attribute pills, wrapped
        self.pill_pos: list[tuple[float, float, str, str, float]] = []
        px, py, row_h = pad, y, 14 * lr + 8
        for text, th_name in self.attrs:
            pw = text_size(text, 14)[0] + 18
            if px > pad and px + pw > w - pad:
                px, py = pad, py + row_h + 7
            self.pill_pos.append((px, py, text, th_name, pw))
            px += pw + 8
        if self.attrs:
            y = py + row_h + 12
        # bullets
        self.layout = []
        first = True
        for kind, lvl, text in self._parse(body):
            if kind == "head":
                size, x0, tx, tw = body_size + 1, pad, pad, inner
                if not first:
                    y += 4
            elif kind == "para":
                size, x0, tx, tw = body_size, pad, pad, inner
            else:
                size = body_size - (1 if lvl else 0)
                x0 = pad + lvl * 20
                tx = x0 + 18
                tw = inner - lvl * 20 - 18
            lines = wrap_text(text, tw, size)
            lh = size * lr
            self.layout.append(dict(kind=kind, lvl=lvl, x0=x0, tx=tx, y=y, lines=lines, size=size, lh=lh))
            y += len(lines) * lh + gap
            first = False
        if self.layout:
            y -= gap
        self.src_lines = []
        if self.src:
            y += 8
            for lab, url in self.src:
                lines = wrap_text(f"Learn: {lab}", inner, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * 12 * lr + 2
            y -= 2
        self.h = y + pad
        self.x = self.y = 0.0

    @staticmethod
    def _parse(body):
        out = []
        for s in body:
            s = str(s)
            lvl = (len(s) - len(s.lstrip(" "))) // 2
            t = s.strip()
            kind = "bullet"
            for p, k in (("# ", "head"), ("= ", "para"), ("! ", "warn"), ("+ ", "good")):
                if t.startswith(p):
                    kind, t = k, t[2:]
                    break
            out.append((kind, lvl, t))
        return out

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "Tool":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        lr = metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft if self.fill == "soft" else th.fill,
                    style="solid" if self.fill == "soft" else "hachure", sw=2)
            if self.icon == "cross":
                cv.line((x + pad + 4, y + pad + 4), (x + pad + 32, y + pad + 32), stroke="#e03131", sw=4)
                cv.line((x + pad + 4, y + pad + 32), (x + pad + 32, y + pad + 4), stroke="#e03131", sw=4)
            elif self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, 36)
            cv.text(x + pad + self.icon_off, y + pad, "\n".join(self.t_lines), size=self.title_size, color=th.deep)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.badge_w, y + pad - 1, self.badge)
            for px, py, text, th_name, pw in self.pill_pos:
                pill(cv, x + px, y + py, text, th_name, 14)
            for it in self.layout:
                kind, ly = it["kind"], y + it["y"]
                color = INK
                if kind == "head":
                    color = th.stroke
                elif kind == "warn":
                    color = "#c92a2a"
                elif kind == "good":
                    color = "#2b8a3e"
                cv.text(x + it["tx"], ly, "\n".join(it["lines"]), size=it["size"], color=color)
                if kind in ("bullet", "warn", "good"):
                    mc = {"bullet": th.stroke, "warn": "#e03131", "good": "#2f9e44"}[kind]
                    cy = ly + it["size"] * lr / 2
                    mx = x + it["x0"] + 4
                    if it["lvl"]:
                        cv.ellipse(mx + 1, cy - 2.5, 5, 5, stroke=mc, fill=mc, style="solid", sw=1, rough=0)
                    else:
                        cv.ellipse(mx, cy - 4, 9, 9, stroke=mc, sw=2, rough=0)
            for text, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, text, size=12, color=LINK, link=url)
        cv.register(f"tool:{self.title}", x, y, self.w, H)
        return self


class Code(Rect2):
    """Monospace snippet in a dashed box (verbatim values from the cited page)."""

    def __init__(self, w, title, lines, theme="gray", size=14, pad=14, src=(), note=None):
        self.th = THEMES[theme]
        self.w, self.title, self.lines, self.size, self.pad, self.src = w, title, lines, size, pad, list(src)
        self.lh = metrics.line_ratio(metrics.MONO) * size
        self.t_lines = wrap_text(title, w - 2 * pad, 18)
        h = pad + len(self.t_lines) * 18 * metrics.line_ratio() + 10 + len(lines) * self.lh + pad
        self.n_lines = wrap_text(note, (w - 2 * pad) * 0.965, 14) if note else []
        if self.n_lines:
            h += len(self.n_lines) * 14 * metrics.line_ratio() + 8
        self.src_lines = []
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * metrics.line_ratio() + 2
        self.h = h + (4 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
            ty = y + self.pad
            cv.text(x + self.pad, ty, "\n".join(self.t_lines), size=18, color=th.deep)
            ty += len(self.t_lines) * 18 * metrics.line_ratio() + 10
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            ty += len(self.lines) * self.lh + 8
            if self.n_lines:
                cv.text(x + self.pad, ty, "\n".join(self.n_lines), size=14, color=MUTED)
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("code", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


# ---------------------------------------------------------------------------------------------- 0. verdict + legend
def verdict(cv: Canvas, y: float) -> float:
    cards = [
        Note(C4, "The docs support AI-assisted investigation and guided changes with human approval. They do not document autonomous failover, auto-remediation of Foundry quota or model outages, or AI capacity forecasting.",
             kind="key", title="Verdict, up front", size=17, title_size=24),
        Card(C4, "Real: AI assists, a human decides", [
            "Coding agent + Foundry Skill + Foundry MCP Server (preview): read telemetry, quota and deprecation schedules, then propose changes and make approved ones",
            "Insights (an LLM judge) analyses production traces and proposes fixes for a human to review; the agent optimizer proposes candidates and does not silently apply or redeploy",
            "Azure SRE Agent in Review mode: an administrator approves write actions",
        ], theme="green", icon="agent", title_size=21),
        Card(C4, "Sounds like AI, is not", [
            "azd ai agent doctor is a deterministic, read-only health check: pass, fail or skip, with exit codes for CI",
            "The Foundry Skill is guidance content plus MCP wiring, not a hosted service",
            "Foundry Control Plane monitors fleet health, cost and anomalies; no AI remediation is described in the pages read",
        ], theme="gray", icon="gear", title_size=21),
        Card(C4, "Not documented", [
            "! AI-driven automatic regional failover of Foundry",
            "! Automatic PTU resize or rebalance, and AI capacity forecasting",
            "! Copilot in Azure features specific to Foundry quota or capacity",
            "! An SLA for the Foundry MCP Server; private-network access for it",
        ], theme="red", icon="preview-features", title_size=21),
    ]
    _, bottom = row(cv, 0, y, cards, gap=G4)
    return bottom + 40


def legend_panel(cv: Canvas, y: float) -> float:
    with cv.panel(0, y, title="How to read the tool cards: four pills on every card", theme="gray", style="dotted", pad=20, title_size=22, w=W) as p:
        x0, y0 = p.ix, p.iy
        gw = (W - 40) / 4
        groups = [
            ("LLM-driven?", [("LLM: yes", LLM_Y), ("LLM: partly", LLM_P), ("No: rules-based", LLM_N)]),
            ("Writes?", [("Writes: yes", WR_Y), ("Proposes only", WR_P), ("Read-only", WR_N)]),
            ("Maturity, as documented", [("Preview", M_PREV), ("GA", M_GA), ("Status not stated", M_UNK)]),
            ("Human control", [("Human: approval, RBAC or review", HUM)]),
        ]
        for i, (title, pills) in enumerate(groups):
            gx = x0 + i * gw
            cv.text(gx, y0, title, size=15, color=MUTED)
            px = gx
            for text, th_name in pills:
                px += pill(cv, px, y0 + 26, text, th_name, 14) + 8
        yy = y0 + 76
        cv.text(x0, yy, "Provenance stickers:", size=15, color=MUTED)
        px = x0 + 170
        for lab, th_name, dashed in (DOC, SUG, INF, PREV, ("Docs disagree", "gray", False)):
            px += pill(cv, px, yy - 4, lab, th_name, 14, dashed, solid=not dashed) + 12
        cv.text(px + 20, yy, f"Plain text is stated on the cited Learn page. Time-sensitive facts carry '{ASOF}'.", size=14, color=MUTED)
    return p.bottom + 56


# ---------------------------------------------------------------------------------------------- 1. toolbelt
def band(cv: Canvas, y: float, letter: str, text: str, sub: str, theme: str, tag=None) -> float:
    th = THEMES[theme]
    numbered(cv, 24, y + 22, letter, theme=theme, d=44, size=24)
    t = cv.text(62, y, text, size=30, color=th.deep)
    cv.text(64, t.bottom + 1, sub, size=16, color=MUTED)
    cv.line((0, t.bottom + 30), (W, t.bottom + 30), stroke=th.stroke, sw=2)
    if tag:
        label, th_name, dashed = tag
        pill(cv, W - text_size(label, 15)[0] - 18, y + 6, label, th_name, 15, dashed, solid=not dashed)
    return t.bottom + 50


def toolbelt(cv: Canvas, y: float) -> float:
    y = head(cv, y, 1, "The operator's toolbelt: nine tools in three places",
             sub="Closest to you first. Each card says whether an LLM drives it, whether it can write, how mature the docs say it is and who approves.",
             tags=(DOC, PREV))
    # ---------------- A: IDE and CLI
    y = band(cv, y, "A", "In your IDE or CLI", "the tools a coding agent (GitHub Copilot in VS Code, Copilot CLI, Claude Code) calls for you", "orange")
    a1 = Tool(C4, "Foundry MCP Server", [
        "A cloud-hosted remote MCP server at https://mcp.ai.azure.com (HTTP): no infrastructure to deploy",
        "Microsoft Entra ID auth with a token scoped to https://mcp.ai.azure.com; the On-Behalf-Of flow makes it act with the signed-in user's RBAC",
        f"79 tools in 17 categories ({ASOF}); the docs mark each tool read or write",
        "! Public endpoint only: no Private Link, no SLA, and the tool set may change without notice",
        "Detail in section 2 below",
    ], theme="orange", icon="mcp", badge="preview", attrs=[("LLM: your agent's model", LLM_Y), ("Writes: yes, with Contributor", WR_Y), ("Preview, no SLA", M_PREV),
                                                            ("Human: host approval, RBAC", HUM)],
              src=src("mcp_start", "mcp_tools"))
    a2 = Tool(C4, "Microsoft Foundry Skill", [
        "The microsoft-foundry meta skill: reusable guidance plus routing to sub-skills for GitHub Copilot in VS Code, Copilot CLI and Claude Code",
        "Guidance content plus MCP wiring, not a hosted service",
        "Skill only: npx skills add https://github.com/microsoft/azure-skills --skill microsoft-foundry",
        "Azure Skills Plugin: the skill + Azure MCP Server config + Foundry MCP Server config. VS Code: the Foundry Toolkit extension includes the skill",
        "Copilot CLI: /plugin marketplace add microsoft/azure-skills, then /plugin install azure@azure-skills (check /mcp show). Claude Code: /plugin install azure@claude-plugins-official",
        "Needs Node 18+, Git, Azure CLI (az login) and azd (azd auth login)",
    ], theme="orange", icon="toolbox", attrs=[("LLM: guidance it reads", LLM_Y), ("Writes: via the agent", WR_P), ("Not labelled preview", M_UNK),
                                              ("Human: review plan, files, roles, cost", HUM)],
              src=src("skill"))
    a3 = Tool(C4, "azd ai for coding agents and scripts", [
        "--no-prompt always; azd goes non-interactive by itself in CI or when an AI-agent environment without a terminal is detected (AZD_NON_INTERACTIVE=false opts out)",
        "--output json is the stable contract; the text output may change",
        "! --no-prompt is not consent to delete: deletes need --force (state-store items: --yes)",
        "! create is not an upsert: --force replaces via an ARM PUT and can lose others' edits",
        "Project context: azd ai project set, FOUNDRY_PROJECT_ENDPOINT or --project-endpoint, with documented precedence",
        "azd ai agent invoke --agent-endpoint <url> calls an agent without a project",
    ], theme="orange", icon="azd", badge="preview", attrs=[("LLM: the agent calls the CLI", LLM_Y), ("Writes: yes", WR_Y), ("Preview", M_PREV),
                                                           ("Human: --no-prompt, --force", HUM)],
              src=src("cli"))
    a4 = Tool(C4, "azd ai agent doctor", [
        "Local checks: azd version, azure.yaml, the azure.ai.agent service, .env keys, container or code-deploy prerequisites",
        "Remote checks: project endpoint reachable, role assignments exist, deployed agent exists and is invocable, model deployment exists",
        "Each check is pass, fail or skip. Flags: --local-only, --unredacted",
        "Exit codes: 0 = at least one pass and none failed; 1 = any failed; 2 = all skipped. Stable enough for CI",
        "Pre-flight before azd up, eval, optimize or deploy. Related: azd ai agent monitor (logs), eval, optimize",
        "! The name sounds AI-ish; the doc describes a rules-based health check",
    ], theme="gray", icon="diagnostics", badge="preview", attrs=[("No: rules-based, not an LLM", LLM_N), ("Read-only", WR_N), ("Preview", M_PREV),
                                                                 ("Human: you read the result", HUM)],
              src=src("doctor"))
    _, ab = row(cv, 0, y, [a1, a2, a3, a4], gap=G4)
    # Foundry Skill: capability areas + operator prompts (both from the Skill page)
    sy = ab + 34
    with cv.panel(0, sy, title="Foundry Skill: what it covers and what operators ask it", sub="Both lists come from the Foundry Skill page. Resolved context comes from azure.yaml, .azure/<env>/.env, .foundry/agent-metadata.yaml and eval.yaml",
                  theme="orange", style="dotted", pad=20, title_size=22, w=W) as sp:
        areas = ["Onboarding and project setup", "Access and capacity: RBAC, managed identities, quota, model availability, region capacity", "Model deployment",
                 "Model customization: SFT, DPO, RFT", "Agent creation: Agent Framework, LangGraph, custom; Python and C#",
                 "Agent deployment: containerize, ACR push, create or update the hosted deployment, redeploy", "Invocation and testing",
                 "Evaluation and optimization: batch and continuous eval, compare versions, optimize prompts, prepare Agent Optimizer jobs",
                 "Trace and dataset work: query traces, analyze latency and failures, curate datasets from traces",
                 "Troubleshooting: hosted-agent logs, telemetry, deployment and runtime failures, repair-and-redeploy loop"]
        cf = ChipFlow([Chip(t_, theme="orange", size=14, pad_y=4, pad_x=10) for t_ in areas], w=1380, gap=10)
        cf.place(cv, sp.ix, sp.iy)
        prompts = ["check RBAC and quota blockers before I deploy this model", "troubleshoot why this hosted agent deployment is failing",
                   "create an evaluation dataset from the last seven days of production traces",
                   "call agent_insights_get ... include evidence and proposed remediation", "review this agent for deployment readiness"]
        bw_ = (W - 40 - 1380 - 60 - 48) / 2
        for i, p_ in enumerate(prompts):
            Bubble(bw_, p_, theme="orange", size=15, tail="left").place(cv, sp.ix + 1380 + 60 + 18 + (i % 2) * (bw_ + 30), sp.iy + (i // 2) * 62)
    y = sp.bottom + 56
    # ---------------- B: inside Foundry
    y = band(cv, y, "B", "Inside Foundry", "analysis that runs on your production traces, and the fleet view", "violet")
    b1 = Tool(C4, "Insights in Foundry", [
        "A judge model (GPT-5 or newer) analyses production traces in Application Insights for recurring behaviours",
        "Categories: Context and memory, Cost and tokens, Hallucinations, Latency, Output quality, Reliability errors, Security and risk, Tool call failures",
        "Each insight has severity, evidence, a likely cause and a proposed fix. The first scan looks back 7 days; run on demand or on a schedule",
        "Roles: Foundry User (prompt agents) or Foundry Project Manager (hosted agents), plus Monitoring Reader on Application Insights for you and the project's managed identity",
    ], theme="violet", icon="app-insights", badge="preview", attrs=[("LLM: GPT-5 or newer judge", LLM_Y), ("Read-only retrieval", WR_N), ("Preview", M_PREV),
                                                                    ("Human review", HUM)],
              src=src("insights"))
    b2 = Tool(C4, "What a human does with an insight", [
        "Investigate the evidence and the likely cause",
        "Add evaluation coverage for the behaviour",
        "Review the proposed improvement: a prompt-agent fix or a hosted-agent code fix",
        "Route a dependency or platform issue to its owner. Do not patch the agent for a failing tool, model, network or Foundry platform",
        "Resolve, dismiss or monitor for recurrence",
        "! Read through the Foundry MCP Server (agent_insights_get, paged by has_more and last_id) or the Foundry Skill it is read-only: it does not start scans, change status or modify the agent",
    ], theme="violet", icon="users", attrs=[("Human decides every step", HUM), ("Read-only via MCP", WR_N)],
              src=src("insights", "mcp_tools"))
    b3 = Tool(C4, "Agent and prompt optimizer", [
        "An evaluation-driven closed loop that proposes better instructions, skills, tool descriptions and model selection",
        "It does not silently apply source changes or redeploy: azd ai agent optimize apply --candidate <id>, then azd deploy, are explicit steps",
        "Uses evaluation and optimization models; tool calls execute during runs",
        "Detail: the 'Agent lifecycle and the optimizer' canvas",
    ], theme="violet", icon="ml", badge="preview", attrs=[("LLM: yes", LLM_Y), ("Proposes only", WR_P), ("Preview (hosted)", M_PREV),
                                                          ("Human: explicit apply, redeploy", HUM)])
    b4 = Tool(C4, "Foundry Control Plane", [
        "Fleet-level monitoring across several agent types, not one agent (below)",
        "Fleet health, cost and anomaly detection",
        "Detail: the 'Foundry Control Plane' and 'Monitoring, alerting and incident response' canvases",
    ], theme="violet", icon="dashboard", attrs=[("LLM: partly (anomaly detection)", LLM_P), ("Admin actions", WR_P), ("New portal", M_UNK),
                                                ("Human: RBAC", HUM)],
              src=src("fleet"))
    nc = Note(C4, "Foundry Canvas (preview) is a GitHub Copilot App extension for designing and deploying hosted agents from a side panel. It is a build-time tool, not an ops tool.",
              kind="info", title="Not an ops tool", src=src("canvas"))
    hb = max(b1.h, b2.h, b3.h + 20 + nc.h, b4.h + 150)
    b1.place(cv, X4(0), y, h=hb)
    b2.place(cv, X4(1), y, h=hb)
    b3.place(cv, X4(2), y)
    nc.place(cv, X4(2), b3.bottom + 20, h=y + hb - (b3.bottom + 20))
    b4.place(cv, X4(3), y, h=hb)
    cv.text(X4(3) + 16, b4.y + b4.h - 124, "Agent types it monitors", size=15, color=MUTED)
    px_, py_ = X4(3) + 16, b4.y + b4.h - 96
    for t_ in ("Foundry agents", "Azure SRE Agent", "Logic Apps agent loops", "Custom agents"):
        pw_ = text_size(t_, 14)[0] + 18
        if px_ + pw_ > X4(3) + C4 - 16:
            px_, py_ = X4(3) + 16, py_ + 36
        px_ += pill(cv, px_, py_, t_, "violet", 14) + 8
    y = y + hb + 56
    # ---------------- C: in Azure
    y = band(cv, y, "C", "In Azure: not Foundry-specific", "Azure products you can point at Foundry telemetry; the Foundry link is an inference unless stated", "grape",
             tag=("Foundry link: our inference", "gray", True))
    c1 = Tool(C4, "Azure SRE Agent", [
        "Connects to Azure resources, observability tools, incident platforms and repos",
        "Automates incidents: on an alert it queries monitoring, correlates signals, forms a root-cause hypothesis, proposes or executes mitigations and prefills a ServiceNow or PagerDuty ticket",
        "Also scheduled workflows (health checks, compliance sweeps) and natural-language investigate and advise",
        "Extension points: Skills, custom agents, Python tools, MCP servers (Datadog, Splunk, New Relic, Dynatrace, Elasticsearch, custom), agent hooks",
        "Integrations: Azure Monitor, Application Insights, Log Analytics, Azure Monitor alerts, PagerDuty, ServiceNow, GitHub, Azure DevOps, ADX, Teams, Outlook",
    ], theme="grape", icon="monitor", attrs=[("LLM: yes", LLM_Y), ("Writes: yes, by run mode", WR_Y), ("Status not stated", M_UNK),
                                             ("Human: run modes, allow/ask/deny", HUM)],
              src=src("sre"))
    c2 = Tool(C4, "SRE Agent governance and billing", [
        "Run modes: Review (the default) or Autonomous. Permissions are separate from run modes; tool-level allow, ask or deny",
        "Managed identity + RBAC, VNet integration, IaC (Bicep), governed skill distribution; it retains investigation context",
        f"Billed in Azure Agent Units: an always-on 4 AAUs per agent-hour from creation until deletion, plus variable active flow; always-on is waived during the trial ({ASOF})",
        "A Cosmos DB for NoSQL SRE Agent integration page is marked preview. Cosmos DB is an Agent Service dependency",
        "! The overview page states no GA or preview status. No Foundry-specific runbook page was found: pointing it at Foundry telemetry (Application Insights, Azure Monitor) is our inference, not a documented pattern",
    ], theme="grape", icon="cost-management", attrs=[("Review: you approve writes", HUM), ("Autonomous: it acts", WR_Y), ("Some sub-features preview", M_PREV)],
              src=src("sre_modes", "sre_bill", "sre_cosmos"))
    c3 = Tool(C4, "Observability agent (Azure Monitor)", [
        "Chat with logs and metrics, scoped to the resource you launch from (for example the Application Insights Logs page)",
        "Deep investigations, optimised for AKS, Application Insights and VMs; save them as Azure Monitor issues (preview)",
        "Autonomous operations (preview) correlate alerts into issues. It 'doesn't restart resources, change configuration, or resolve issues on its own'",
        "Optional Observability Agent resource (preview) with custom instructions",
        f"Regions ({ASOF}): Australia East, Canada Central, Central US, East Asia, East US, South Central US, UK South, West Central US, West Europe",
        "Limits: conversations up to 24 h, English only, no customer-managed keys",
        "! Foundry is not mentioned. Foundry traces land in Application Insights, so using it on them is our inference",
    ], theme="grape", icon="log-analytics", attrs=[("LLM: yes", LLM_Y), ("Creates issues only", WR_P), ("Preview parts; pages disagree", M_PREV),
                                                   ("Human: you decide actions", HUM)],
              src=src("obs"))
    c4 = Tool(C4, "Resiliency agent (Azure Copilot)", [
        "Assesses and improves zonal resiliency. Start Resilient: a resiliency report + Bicep. Get Resilient: check posture, prerequisites, enablement scripts, service groups, goals and compliance",
        "'Optimized for zonal resiliency scenarios. Regional resiliency ... future releases'",
        "Sample resources: VM, PostgreSQL, AKS, Redis, Storage, Cosmos DB, App Service, SQL, Front Door",
        "! No Foundry resource types are listed",
    ], theme="grape", icon="regions", badge="preview", attrs=[("LLM: yes", LLM_Y), ("Can enable some zonal settings", WR_P), ("Preview", M_PREV),
                                                              ("Human: you confirm", HUM)],
              src=src("cp_res"))
    _, cb = row(cv, 0, y, [c1, c2, c3, c4], gap=G4)
    y = cb + 40
    # ---------------- Azure Copilot band (table + capabilities)
    rows = [
        ["Troubleshooting", ("GA", "green"), ("Preview", "orange"), "Azure Copilot chat"],
        ["Deployment", ("no label", "gray"), ("Preview", "orange"), "Azure Copilot chat"],
        ["Optimization", ("Preview", "orange"), ("Preview", "orange"), "The agents page lists it in the chat; the access page says it isn't in the chat window"],
        ["Resiliency", ("Preview", "orange"), ("Preview", "orange"), "Azure Copilot chat"],
        ["Migration", ("Preview", "orange"), ("GA", "green"), "Azure Migrate"],
        ["Observability", ("GA", "green"), ("Preview", "orange"), "Azure Monitor"],
    ]
    tw = 2 * C4 + G4
    t = Table([("Azure Copilot agent", 230), ("'Agents in Azure Copilot'", 280), ("'Manage access to Azure Copilot'", 330), ("Where you invoke it", tw - 840)], rows, w=tw,
              theme="grape", size=14, head_size=15, first_col_theme="grape", title=f"Azure Copilot agents: the two pages disagree on maturity ({ASOF})", title_size=22)
    t.place(cv, 0, y)
    nl = learn_line(cv, 0, t.bottom + 8, src("cp_agents", "cp_access"))
    nt = Note(tw, "Statuses differ between Azure Copilot pages (Troubleshooting and Observability: GA on one, preview on the other; Migration: the reverse), so treat every label as unstable and verify at use time.",
              kind="warn", title="Docs disagree on maturity")
    nt.place(cv, 0, nl + 14)
    cg = Tool(tw, "General Azure Copilot capabilities that help Foundry ops (generic, not Foundry-specific)", [
        "Understand service health events; analyse, estimate and optimise costs; answer Azure Monitor metrics and logs questions",
        "Generate Terraform, Bicep, CLI and PowerShell; author API Management policies; Advisor recommendations across the Well-Architected pillars (Reliability, Cost, Operational Excellence, Performance, Security)",
        "! Limits: conversations up to 24 h; actions on more than 10 resources must be done outside Copilot; lists are capped at the top 5; it may throttle",
    ], theme="grape", icon="copilot", attrs=[("LLM: yes", LLM_Y), ("Writes: some, 10-resource cap", WR_P), ("Per agent; pages disagree", M_UNK)],
              src=src("cp_cap"))
    cg.place(cv, tw + G4, y)
    na = Note(tw, "Admins enable or disable each agent in the Azure Copilot admin center (Global Administrator). Access to the Optimization agent is managed there even though that agent isn't available through the chat window.",
              kind="info", title="Admin control", src=src("cp_access"))
    na.place(cv, tw + G4, cg.bottom + 20)
    return max(na.bottom, nt.bottom) + 60


# ---------------------------------------------------------------------------------------------- 2. MCP deep dive
def mcp_detail(cv: Canvas, y: float) -> float:
    y = head(cv, y, 2, "Foundry MCP Server in detail (preview)",
             sub=f"Remote MCP server at https://mcp.ai.azure.com, as documented {ASOF}. Public endpoint only, no SLA, tool set may change without notice.",
             tags=(DOC, PREV), color=THEMES["orange"].deep)
    # ---------- column 1: architecture + config
    x1 = X3(0)
    cv.text(x1, y, "How a request flows", size=22, color=THEMES["orange"].deep)
    yy = y + 40
    bw = C3 - 230
    cl = Box(bw, "MCP client", sub="for example GitHub Copilot Agent mode in VS Code 1.99 or later", theme="indigo", icon="vscode", icon_pos="left", h=96, size=18, sub_size=14)
    cl.place(cv, x1, yy)
    en = Box(bw, "Microsoft Entra ID", sub="token scoped to https://mcp.ai.azure.com", theme="red", icon="entra-connect", icon_pos="left", h=96, size=18, sub_size=14)
    en.place(cv, x1, yy + 96 + 64)
    mc = Box(bw, "Foundry MCP Server", sub="stateless proxy; requests may be processed in EU or US data centres; stores no data", theme="orange", icon="mcp", icon_pos="left", h=110,
             size=18, sub_size=14)
    mc.place(cv, x1, en.bottom + 64)
    fr = Box(bw, "Your Foundry resources", sub="projects, deployments, agents, evaluations: reached as the signed-in user", theme="blue", icon="foundry", icon_pos="left", h=110, size=18, sub_size=14)
    fr.place(cv, x1, mc.bottom + 64)
    connect(cv, cl, en, a_side="bottom", b_side="top", num=1, label="sign in", label_size=14)
    connect(cv, en, mc, a_side="bottom", b_side="top", num=2, label="token", label_size=14)
    connect(cv, mc, fr, a_side="bottom", b_side="top", num=3, label="On-Behalf-Of", label_size=14)
    rx_ = cl.right + 40
    arrow(cv, [(cl.right + 4, cl.cy), (rx_, cl.cy), (rx_, mc.cy), (mc.right + 4, mc.cy)], end_head="arrow", color="#e8590c", sw=2, dash="dashed")
    numbered(cv, rx_, (cl.cy + mc.cy) / 2, 4, theme="orange", d=30, size=17)
    cv.text(rx_ + 26, (cl.cy + mc.cy) / 2 - 22, wrap("tool calls over HTTP", 150, 14), size=14, color=INK)
    code = Code(bw, ".vscode/mcp.json entry (as documented)", [
        '{"servers": {',
        '  "foundry-mcp-remote": {',
        '    "type": "http",',
        '    "url": "https://mcp.ai.azure.com"',
        '}}}',
    ], theme="orange", note="Auth failure fix: az account get-access-token --resource https://mcp.ai.azure.com", src=src("mcp_start"))
    code.place(cv, x1, fr.bottom + 36)
    col1_b = code.bottom
    # ---------- column 2: categories + ops tools + prompts
    x2 = X3(1)
    cv.text(x2, y, "79 tools in 17 categories", size=22, color=THEMES["orange"].deep)
    cats = [("Agent management", "green"), ("Hosted agent sessions and files", "green"), ("Toolbox management", "orange"), ("Dataset management", "cyan"),
            ("Data generation jobs", "cyan"), ("Evaluation operations", "violet"), ("Trace evaluation", "violet"), ("Evaluation suites", "violet"),
            ("Evaluator catalog", "violet"), ("Evaluator generation jobs", "violet"), ("Model catalog and details", "blue"), ("Model deployment management", "blue"),
            ("Model analytics and recommendations", "blue"), ("Model monitoring and operations", "blue"), ("Project connections", "gray"), ("Prompt optimization", "green"),
            ("Continuous evaluation", "violet")]
    cf = ChipFlow([Chip(t_, theme=th_, size=14, pad_y=4, pad_x=10) for t_, th_ in cats], w=C3, gap=8)
    cf.place(cv, x2, y + 40)
    cv.text(x2, cf.y + cf.h + 8, "Chip colour = our grouping by area, not a docs field.", size=13, color=MUTED)
    ty = cf.y + cf.h + 40
    rows = [
        ["How are traffic and health?", "model_monitoring_metrics_get: requests, latency percentiles, errors, token usage"],
        ["Anything deprecated or retiring?", "model_deprecation_info_get: retirement schedules + suggested replacements"],
        ["How much quota is left?", "model_quota_list: quota and usage per region, including Managed Compute accelerator quota"],
        ["Is there a better or cheaper model?", "model_benchmark_get, model_benchmark_subset_get, model_similar_models_get, model_switch_recommendations_get"],
        ["Inspect or change deployments", "model_deployment_get, model_deployment_delete, model_deploy_managed_compute, model_catalog_list, model_details_get"],
        ["Run or manage agents", "agent_get, agent_update, agent_invoke, agent_delete, agent_container_control, agent_container_status_get"],
        ["Continuous evaluation", "continuous_eval_create, continuous_eval_get, continuous_eval_delete"],
        ["What are my production issues?", "agent_insights_get: read-only Insights retrieval"],
    ]
    t = Table([("Operator question", 250), ("Ops-relevant tools (names from the docs)", C3 - 250)], rows, w=C3, theme="orange", size=14, head_size=15, first_col_theme="orange",
              title="Ops-relevant tools", title_size=22)
    t.place(cv, x2, ty)
    nr = Note(C3, "The docs mark every tool read or write. Names starting get or list read; create, update, delete, deploy and invoke act. Check the available-tools page before you grant Contributor.",
              kind="info", title="Read or write", size=14, src=src("mcp_tools"))
    nr.place(cv, x2, t.bottom + 18)
    col2_b = nr.bottom
    # ---------- column 3: permissions, limits, safety
    x3 = X3(2)
    rows = [
        ["Reader", "Read tools"],
        ["Contributor", "Write and delete tools: create deployments, start evaluations"],
        ["Owner or User Access Administrator", "Manage access"],
        ["Conditional Access Administrator", "Only to configure tenant Conditional Access policies"],
    ]
    tp = Table([("Role", 330), ("What it allows", C3 - 330)], rows, w=C3, theme="red", size=14, head_size=15, first_col_theme="red", title="Permissions", title_size=22)
    tp.place(cv, x3, y)
    ca = Note(C3, "Block or limit users with Conditional Access on the Foundry MCP Server enterprise app. Materialise its service principal with: az ad sp create --id fcdfa2de-b65b-4b54-9a1c-81c8a18282d9 (the application ID the docs give for Foundry MCP Server).",
              kind="tip", title="Conditional Access", size=14, src=src("mcp_sec"))
    ca.place(cv, x3, tp.bottom + 18)
    pl = Card(C3, f"Preview limits ({ASOF})", [
        "! Public endpoint only: no network isolation. Resources behind Private Link are unreachable: use the SDK or REST, or build your own MCP server with Agent Service private networking",
        "Requests and responses may be processed in EU or US data centres; the stateless proxy does not store data",
        "! No SLA, and the tool set may change without notice",
    ], theme="red", icon="private-link", badge="preview", title_size=21, src=src("mcp_sec", "mcp_start"))
    pl.place(cv, x3, ca.bottom + 20)
    sg = Card(C3, "Safety guidance from the docs", [
        "Write operations have immediate live and billing impact: deployments bill immediately, deletions are permanent, evaluations consume quota, datasets can overwrite versions",
        "Verify the tool and parameters; check environment targeting; check dependencies before a delete; check quota first",
        "Test in non-production; change one resource at a time; validate with read tools; log via Activity Logs; back up configs",
        "'Always verify the accuracy of the language model's response.'",
    ], theme="pink", icon="content-safety", title_size=21, src=src("mcp_sec"))
    sg.place(cv, x3, pl.bottom + 20)
    col3_b = sg.bottom
    # ---------- example prompts row
    py = max(col1_b, col2_b, col3_b) + 36
    cv.text(0, py, "Example ops prompts from the docs", size=22, color=THEMES["orange"].deep)
    prompts = [
        "Check if any of my deployments are using deprecated model versions.",
        "Show me quota usage across all regions for my subscription.",
        "Recommend more cost-effective alternatives based on current usage.",
        "Delete unused test deployments to free up capacity.",
        "Update continuous evaluation to sample 25% of traffic, max 10 runs per hour.",
    ]
    pw = (W - 18 - 4 * 36) / 5
    bubs = [Bubble(pw, p_, theme="orange", size=15, tail="left") for p_ in prompts]
    bx = 18.0
    for b in bubs:
        b.place(cv, bx, py + 44)
        bx += pw + 36
    return max(b.y + b.h for b in bubs) + 60


# ---------------------------------------------------------------------------------------------- 3. flows
def flows(cv: Canvas, y: float) -> float:
    y = head(cv, y, 3, "Flows: how an AI-assisted operation actually runs",
             sub="Left: a coding agent investigates, proposes, you approve, it changes and validates. Right: an incident. The shapes are our synthesis of documented parts.",
             tags=(SUG, DOC))
    LW = 1860
    seq = Sequence(cv, 0, y, [("Operator", "gray", "user"), ("Coding agent + Foundry Skill", "indigo", "copilot"), ("Foundry MCP Server", "orange", "mcp"),
                              ("Foundry project and resources", "blue", "foundry"), ("Activity Log", "violet", "activity-log")],
                   spacing=(LW - 230) / 4, head_w=230, head_h=70, step=62, size=15, label_size=14)
    seq.msg(0, 1, "Plain-language request: check RBAC and quota blockers before I deploy this model", num=1)
    seq.note(1, 2, "The Foundry Skill discovers the MCP tools, loads the matching sub-skill, resolves context from azure.yaml, .azure/<env>/.env, .foundry/agent-metadata.yaml and eval.yaml, prefers structured MCP tools and asks only for missing values.", kind="tip", size=14)
    seq.msg(1, 2, "READ tools: model_quota_list, model_monitoring_metrics_get, model_deprecation_info_get, agent_insights_get", num=2, note="Entra token scoped to https://mcp.ai.azure.com")
    seq.msg(2, 3, "On-Behalf-Of: calls Foundry as the signed-in user, with that user's RBAC", num=3)
    seq.msg(3, 2, "metrics, quota, retirement schedules, insights", dash="dashed")
    seq.msg(2, 1, "results; the proxy stores nothing", dash="dashed")
    seq.msg(1, 0, "Summary and a proposed change. Review the plan, generated files, role assignments and cost-bearing resources", dash="dashed", num=4)
    seq.msg(0, 1, "Human gate: approve ONE write operation", num=5)
    seq.msg(1, 2, "WRITE tool: deploy, delete or update continuous evaluation", num=6, note="live, billed and permanent: check quota and dependencies first")
    seq.msg(2, 3, "Change applied with the user's RBAC")
    seq.msg(1, 2, "Validate with a read tool", num=7)
    seq.msg(3, 4, "The operation is recorded in the Activity Log", dash="dashed", num=8)
    sb = seq.end()
    nv = Note(LW, "'Always verify the accuracy of the language model's response.' Model-driven summaries can add inferred details.", kind="warn", size=14, title="Verify the summary",
              src=src("mcp_sec"))
    nv.place(cv, 0, sb + 24)
    # ---------- incident flow (right)
    fx = LW + 80
    fw = W - fx
    cx = fx + fw / 2
    cv.text(fx, y, "Incident: where the AI tools fit", size=22, color=THEMES["grape"].deep)
    top = y + 46
    a = Box(520, "1  An alert fires", sub="an Azure Monitor alert or a Service Health event", theme="gray", icon="alerts", icon_pos="left", h=86, size=18, sub_size=14)
    a.place(cv, cx - 260, top)
    b = Box(820, "2  Investigate (optional)", sub="Azure SRE Agent or Observability agent: query monitoring, correlate signals, form a root-cause hypothesis", theme="grape", icon="monitor",
            icon_pos="left", h=116, size=19, sub_size=14)
    b.place(cv, cx - 410, a.bottom + 54)
    d = Box(300, "3  Which run mode?", theme="grape", shape="diamond", size=17, h=200)
    d.place(cv, cx - 150, b.bottom + 56)
    r1 = Box(440, "Review (default)", sub="the agent proposes; an SRE Agent Administrator approves Azure infrastructure write actions", theme="green", h=140, size=19, sub_size=14)
    r1.place(cv, fx, d.bottom + 64)
    r2 = Box(440, "Autonomous", sub="executes immediately; meant for non-production or trusted recurring tasks", theme="red", h=140, size=19, sub_size=14)
    r2.place(cv, fx + fw - 440, d.bottom + 64)
    g = Box(560, "4  Azure-level mitigation applied", sub="verify the result; permissions are separate from run modes", theme="green", h=100, size=18, sub_size=14)
    g.place(cv, cx - 280, r1.bottom + 60)
    connect(cv, a, b, a_side="bottom", b_side="top")
    connect(cv, b, d, a_side="bottom", b_side="top")
    connect(cv, d, r1, a_side="left", b_side="top", route="elbow", label="Review", label_size=14, label_pos="above", label_t=0.2)
    connect(cv, d, r2, a_side="right", b_side="top", route="elbow", label="Autonomous", label_size=14, label_pos="above", label_t=0.2)
    connect(cv, r1, g, a_side="bottom", b_side="top", route="elbow", bend=0.4)
    connect(cv, r2, g, a_side="bottom", b_side="top", route="elbow", bend=0.4)
    nf = Note(fw, "Foundry-specific fixes (fail over, spill over, roll back a version, raise quota) run through your runbooks and IaC. The docs show no AI-driven auto-failover or auto-remediation for them. The Observability agent 'doesn't restart resources, change configuration, or resolve issues on its own'.",
              kind="gotcha", title="Foundry-specific fixes stay with you", size=15)
    nf.place(cv, fx, g.bottom + 40)
    return max(nv.bottom, nf.bottom) + 70


# ---------------------------------------------------------------------------------------------- 4. matrix
def matrix(cv: Canvas, y: float) -> float:
    y = head(cv, y, 4, "What each tool can and cannot do",
             sub=f"The reality-check ledger. Attribute columns and the can and cannot columns are documented ({ASOF}); the last column is our reading.",
             tags=(DOC, ("Verdict column: our reading", "orange", True)))
    G = lambda s: (s, "gray")
    rows = [
        ["Foundry MCP Server", CHECK, ("Your agent's LLM", "violet"), ("Yes: Contributor", "red"), ("Preview, no SLA, public endpoint", "orange"),
         "Per-tool approval in the host; RBAC; Conditional Access",
         "List, inspect, deploy and delete model deployments; read metrics, quota and deprecation schedules; manage agents and continuous evaluation; fetch Insights",
         "Reach Private Link-isolated resources. Carry an SLA. Keep a stable tool set",
         ("Real, preview", "orange")],
        ["Foundry Skill", CHECK, ("Guidance an LLM reads", "violet"), ("Via the agent's tools", "yellow"), G("Not labelled preview"),
         "Review the plan, generated files, role assignments and cost-bearing resources",
         "Route a coding agent to sub-skills; resolve workspace context; guide RBAC and quota checks, deployment, evaluation, trace analysis and troubleshooting",
         "Run anything by itself: it is guidance plus MCP wiring, not a hosted service",
         ("Real: guidance, not a service", "green")],
        ["azd ai with coding agents", CHECK, ("LLM calls the CLI", "violet"), ("Yes", "red"), ("Preview", "orange"),
         "--no-prompt, --force, --yes",
         "Run non-interactively with stable JSON output; call an agent without a project (--agent-endpoint)",
         "Treat --no-prompt as consent to delete; upsert (create is not an upsert)",
         ("Real, preview", "orange")],
        ["azd ai agent doctor", CHECK, ("No: rules-based", "gray"), ("No: read-only", "green"), ("Preview", "orange"), "Not applicable: you read pass, fail or skip",
         "Check local setup and remote readiness, including that role assignments exist; exit codes 0, 1 and 2 for CI",
         "Diagnose with AI, fix anything or change state",
         ("Real, but not AI", "gray")],
        ["Insights", CHECK, ("Yes: LLM judge", "violet"), ("No: read-only retrieval", "green"), ("Preview", "orange"), "Human review of each insight",
         "Analyse production traces for recurring behaviours, with evidence, likely cause and a proposed fix; on demand or scheduled",
         "Start scans, change status or modify the agent when read through MCP or the Skill; repair a failing dependency",
         ("Real, preview", "orange")],
        ["Agent optimizer", CHECK, ("Yes", "violet"), ("Proposes only", "yellow"), ("Preview (hosted)", "orange"), "Explicit optimize apply, then azd deploy",
         "Propose better instructions, skills, tool descriptions and model selection from an evaluation loop",
         "Silently apply source changes or redeploy",
         ("Real; proposes only", "green")],
        ["Foundry Control Plane", CHECK, ("Partly: anomaly detection", "yellow"), ("Admin actions", "yellow"), G("New portal"), "RBAC",
         "Monitor fleet health, cost and anomalies across Foundry agents, Azure SRE Agent, Logic Apps agent loops and custom agents",
         "No AI remediation is described in the sources read",
         ("Real; AI role is limited", "green")],
        ["Azure SRE Agent", CROSS, ("Yes", "violet"), ("Yes, by run mode", "red"), G("Not stated on the overview; some sub-features preview"),
         "Review or Autonomous run mode; tool allow, ask or deny; managed identity and RBAC",
         "Automate incidents, run scheduled workflows and answer questions; correlate signals, propose or execute mitigations, prefill a ServiceNow or PagerDuty ticket",
         "No Foundry-specific runbook page was found: using it on Foundry telemetry is an inference",
         ("Real Azure product; Foundry use is an inference", "yellow")],
        ["Observability agent", CROSS, ("Yes", "violet"), ("Creates issues only", "yellow"), ("Autonomous ops and agent resource: preview. Chat and investigation: pages disagree", "orange"), "You decide the actions",
         "Chat over logs and metrics; deep investigations (AKS, Application Insights, VMs); correlate alerts into issues",
         "Restart resources, change configuration or resolve issues on its own. Foundry is not mentioned. Conversations up to 24 h, English only, no CMK",
         ("Real; assists, does not act", "yellow")],
        ["Resiliency agent", CROSS, ("Yes", "violet"), ("Can enable some zonal settings", "yellow"), ("Preview", "orange"), "You confirm",
         "Assess and improve zonal resiliency: report + Bicep, enablement scripts, goals and compliance",
         "Regional resiliency (future releases). No Foundry resource types are listed",
         ("Real, preview; zonal only", "yellow")],
        ["Azure Copilot (general)", CROSS, ("Yes", "violet"), ("Some, with a 10-resource cap", "yellow"), G("Per agent; the pages disagree"), "Admins enable agents in the admin center (Global Administrator)",
         "Explain service health events; analyse and estimate costs; answer Azure Monitor questions; generate Terraform, Bicep, CLI and PowerShell; author APIM policies; Advisor recommendations",
         "Act on more than 10 resources; list more than the top 5; offer anything specific to Foundry quota or capacity",
         G("Real but generic")],
    ]
    cols = [("Tool", 215), ("Foundry-specific?", 100), ("LLM-driven?", 140), ("Writes?", 160), ("Maturity, as documented", 215), ("Human control", 270),
            ("Can do", 760), ("Cannot do, or not documented", 650), ("Real or hype? (our reading)", 450)]
    scale = W / sum(c[1] for c in cols)
    cols = [(n, w_ * scale) for n, w_ in cols]
    t = Table(cols, rows, w=W, theme="grape", size=14, head_size=15, first_col_theme="grape")
    t.place(cv, 0, y)
    ly = learn_line(cv, 0, t.bottom + 8, src("mcp_tools", "skill", "cli", "doctor", "insights", "fleet", "sre", "obs", "cp_res", "cp_cap"))
    return ly + 60


# ---------------------------------------------------------------------------------------------- 5. not documented
def not_documented(cv: Canvas, y: float) -> float:
    y = head(cv, y, 5, "Not documented: six things people assume exist",
             sub=f"None of these appears in the pages read ({ASOF}). Plan for the human-run alternative on the right of each card.", tags=(("Absence of evidence", "red", True),))
    items = [
        ("AI-driven automatic regional failover of Foundry", "Failover is yours: gateway reroute or a warm-standby rebuild (see 'Failure-mode matrix and runbook')."),
        ("Automatic PTU resize or rebalance", "Spillover to Standard and PTU scaling are your actions (see the PTU and quota canvases)."),
        ("AI capacity forecasting", "model_quota_list reads quota and usage per region; it does not forecast."),
        ("Copilot in Azure features specific to Foundry quota or capacity", "Only generic cost, Monitor and Advisor help is documented."),
        ("An SLA for the Foundry MCP Server", "The preview terms say no service-level agreement."),
        ("Private-network access for the hosted Foundry MCP Server", "Public endpoint only: use the SDK or REST, or your own MCP server with Agent Service private networking."),
    ]
    cw = (W - 5 * 28) / 6
    cards = [Tool(cw, t_, ["+ " + alt], theme="red", icon="cross", title_size=19, body_size=15) for t_, alt in items]
    _, bb = row(cv, 0, y + 4, cards, gap=28)
    return bb + 60


# ---------------------------------------------------------------------------------------------- 6. gotchas
def gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, 6, "Gotchas", tags=(DOC, SUG))
    nw = (W - 3 * 34) / 4
    notes = [
        Note(nw, "The hosted Foundry MCP Server cannot reach Private Link-isolated Foundry resources. Use the SDK or REST, or build your own MCP server with Agent Service private networking.",
             kind="gotcha", title="No private networking", src=src("mcp_sec")),
        Note(nw, "MCP and CLI write tools act with your RBAC. The docs recommend least privilege and Conditional Access.",
             kind="gotcha", title="Writes use your permissions", src=src("mcp_sec")),
        Note(nw, "--no-prompt means non-interactive, not consent to delete. Deletes need --force, and state-store items need --yes.",
             kind="warn", title="--no-prompt is not consent", src=src("cli")),
        Note(nw, "'Always verify the accuracy of the language model's response.' Model-driven summaries can add inferred details.",
             kind="warn", title="Verify the summary", src=src("mcp_sec")),
        Note(nw, "The host offers approval scopes (current session, current workspace, always allow). Choosing narrow scopes for write tools is our suggestion, not stated in the docs.",
             kind="tip", title="Suggested: narrow approval scopes"),
        Note(nw, f"GA and preview labels differ between Azure Copilot pages, and the SRE Agent overview states none ({ASOF}). Treat statuses as unstable and re-check.",
             kind="warn", title="Statuses are unstable", src=src("cp_agents", "cp_access", "sre")),
        Note(nw, "azd ai agent doctor is a rules-based, read-only check. The doc positions it as a pre-flight before azd up, evaluation, optimization or deploy; its output is a pass, fail or skip per check.",
             kind="tip", title="Doctor is a pre-flight check", src=src("doctor")),
        Note(nw, "Foundry Canvas (preview) designs and deploys hosted agents from a side panel. It is a build-time tool, not an operations tool.",
             kind="info", title="Canvas is not ops", src=src("canvas")),
    ]
    _, bb = grid(cv, 0, y, notes, 4, gap_x=34, gap_y=26)
    return bb + 64


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "AI-assisted operations",
                                f"Using AI to operate Foundry: what is real, what is preview, what is not AI, and what the docs do not say ({ASOF})",
                                icon="foundry", w=W)
    y = verdict(cv, bottom + 36)
    y = legend_panel(cv, y)
    y = toolbelt(cv, y)
    y = mcp_detail(cv, y)
    y = flows(cv, y)
    y = matrix(cv, y)
    y = not_documented(cv, y)
    y = gotchas(cv, y)
    sources(cv, 0, y, [S["mcp_start"], S["mcp_tools"], S["mcp_sec"], S["skill"], S["cli"], S["doctor"], S["insights"], S["fleet"],
                       S["sre"], S["sre_modes"], S["sre_bill"], S["cp_agents"], S["cp_access"], S["obs"]], w=W, cols=3)
