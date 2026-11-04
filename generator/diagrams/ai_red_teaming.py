"""AI Red Teaming Agent - automated adversarial testing (PyRIT + Foundry risk and safety evaluators).

Layout: summary strip -> the attack-lab pipeline (seed objectives -> converters -> target -> response -> evaluator -> ASR scorecard)
with the mitigate / re-run / schedule loop -> how it works + where it plugs in -> risk-category matrix and the agentic (cloud-only)
risks -> the 24 attack strategies as a periodic table -> local vs cloud -> cloud API flow, scheduling and scorecard shape ->
limits and transparency-note highlights -> manual red-teaming guidance -> gotchas -> sources.
"""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="ai-red-teaming", title="AI Red Teaming Agent", section="2", group="Observability and safety", order=43,
    description="How the AI Red Teaming Agent works: PyRIT attack strategies plus Foundry risk and safety evaluators produce an attack success rate scorecard - risk categories, agentic risks, cloud versus local runs, scheduling and limits.",
    tags=["red-teaming", "pyrit", "safety", "evaluation", "asr", "agentic-risks"],
)

CW, GUT = 520, 48
STEP = CW + GUT
W = 6 * CW + 5 * GUT          # 3360


def X(i: int) -> float:
    return i * STEP


def SPAN(n: int) -> float:
    return n * CW + (n - 1) * GUT


S = dict(
    concept=("AI Red Teaming Agent", learn("concepts/ai-red-teaming-agent")),
    cloud=("Run AI red teaming in the cloud", learn("how-to/develop/run-ai-red-teaming-cloud")),
    local=("Run AI red teaming scans locally", learn("how-to/develop/run-scans-ai-red-teaming-agent")),
    tn=("Transparency note for safety evaluations", learn("concepts/safety-evaluations-transparency-note")),
    manual=("Planning red teaming for LLM applications", learn("openai/concepts/red-teaming")),
    regions=("Evaluation regions, limits and virtual network", learn("concepts/evaluation-regions-limits-virtual-network")),
    rs=("Risk and safety evaluators", learn("concepts/evaluation-evaluators/risk-safety-evaluators")),
    mon=("Monitor agents dashboard", learn("observability/how-to/how-to-monitor-agents-dashboard")),
    ext=("Register an external agent", learn("agents/how-to/register-external-agent")),
    obs=("Observability in Foundry", learn("concepts/observability")),
    ga=("Feature status at GA", learn("concepts/general-availability")),
    guard=("Guardrails overview", learn("guardrails/guardrails-overview")),
    pyrit=("PyRIT on GitHub (not Learn)", "https://github.com/microsoft/PyRIT"),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


_KitNote = Note


def Note(*a, **kw):  # noqa: N802 - the kit leaves no bottom padding under citation lines; add it here
    n = _KitNote(*a, **kw)
    if kw.get("src"):
        n.h += 10
    return n


def chain(cv: Canvas, x: float, y: float, w: float, steps, *, theme="violet", dash="solid", gap=56, size=19, sub_size=15, themes=None):
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    boxes = [Box(bw, lab, sub=sub, theme=(themes[i] if themes else theme), fill="hatch", dash=dash, size=size, sub_size=sub_size, pad=10, min_h=96)
             for i, (lab, sub) in enumerate(steps)]
    hmax = max(b.h for b in boxes)
    cx = x
    for i, b in enumerate(boxes):
        b.place(cv, cx, y, h=hmax)
        numbered(cv, b.x + 6, b.y + 6, i + 1, theme=b.th.name, d=28, size=16)
        cx += bw + gap
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", dash=dash, end_head="arrow", sw=2)
    return boxes, y + hmax


# ============================================================================================== 0. title, key, summary
def title_and_key(cv: Canvas) -> float:
    _, bottom = title_block(
        cv, 0, 0, "AI Red Teaming Agent",
        "Automated adversarial testing: PyRIT attack strategies plus Foundry risk and safety evaluators produce an Attack Success Rate scorecard  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    with cv.panel(0, y, theme="gray", style="dotted", pad=16, w=W) as k:
        cv.text(k.ix, k.iy - 2, "Colour = role", size=16, color="#343a40")
        legend(cv, k.ix + 140, k.iy - 2, [
            ("Attack side (PyRIT, strategies)", "red"), ("Models", "blue"), ("Agents", "green"), ("Safety evaluators, guardrails", "pink"),
            ("Evaluation, scorecard, monitoring", "violet"), ("Cloud-only agentic risks", "orange"), ("Data and seeds", "cyan"),
            ("Neutral", "gray")], size=15, gap=22)
        y2 = k.iy + 34
        cv.text(k.ix, y2, "Markers", size=16, color="#343a40")
        cx = k.ix + 140
        draw_badge(cv, cx, y2 - 1, "ga")
        draw_badge(cv, cx + 50, y2 - 1, "preview")
        t = cv.text(cx + 140, y2, "status as of 2026-11-03", size=15)
        cx += 140 + t.w + 32
        cv.rect(cx, y2 + 1, 28, 18, stroke="#495057", sw=2, dash="dashed")
        t = cv.text(cx + 38, y2, "docs disagree, or the docs do not say", size=15)
        cx += 38 + t.w + 32
        cv.text(cx, y2, "Attack tiles: lime = Easy, yellow = Moderate, red = Difficult", size=15)
    return k.bottom


def summary_strip(cv: Canvas, y: float) -> float:
    def tile(title, body, theme, icon, keys):
        return Card(CW, title, ["= " + body], theme=theme, icon=icon, fill="hatch", title_size=22, body_size=15, pad=14,
                    gap=4, icon_size=34, src=src(*keys))

    tiles = [
        tile("PyRIT plus safety evaluators", "Microsoft's open-source Python Risk Identification Tool (PyRIT) generates the attacks; Foundry risk and safety evaluators score the responses.",
             "red", "bug", ("concept", "pyrit")),
        tile("ASR is the headline number", "Attack Success Rate = successful attacks / total attacks, reported by risk category, attack complexity and technique.",
             "violet", "metrics", ("concept",)),
        tile("10 risk categories", "Seven apply to models and agents; prohibited actions, sensitive data leakage and task adherence are agent-only and cloud-only.",
             "orange", "content-safety", ("concept",)),
        tile("24 attack strategies", "Encodings and jailbreaks (Easy), Tense (Moderate), Multi turn and Crescendo (Difficult). With none chosen, only baseline direct queries run.",
             "red", "code", ("concept",)),
        tile("Cloud or local", "Cloud runs through the Evals API in Foundry (new). The local SDK scan is preview and not compatible with the Foundry (new) portal and SDK.",
             "blue", "foundry", ("cloud", "local")),
        tile("A scan is not a substitute", "It does not replace human red teaming, systematic measurement or guardrails, and ASR is judged by generative models: review false positives.",
             "pink", "info-protection", ("concept", "tn")),
    ]
    _, bottom = row(cv, 0, y, tiles, gap=GUT)
    return bottom


# ============================================================================================== 1. the attack lab
def mini_scorecard(cv: Canvas, x: float, y: float, w: float) -> Rect2:
    """Schematic ASR scorecard: categories x complexity, deliberately without numbers."""
    th = THEMES["violet"]
    with cv.panel(x, y, title="ASR scorecard", sub="by risk category, complexity and technique", theme="violet", style="solid", fill="soft", pad=16,
                  title_size=22, sub_size=14, w=w) as p:
        inner = w - 32
        lab_w = 100
        cw_ = (inner - lab_w - 3 * 8) / 3
        gy = p.iy
        for j, head in enumerate(("Easy", "Moderate", "Difficult")):
            tw = text_size(head, 13)[0]
            cv.text(p.ix + lab_w + 8 + j * (cw_ + 8) + (cw_ - tw) / 2, gy, head, size=13, color=th.deep)
        gy += 22
        for cat in ("Violence", "Hate, unfair", "Sexual", "Self-harm"):
            cv.text(p.ix, gy + 6, cat, size=13, color="#343a40")
            for j in range(3):
                cv.rect(p.ix + lab_w + 8 + j * (cw_ + 8), gy, cw_, 28, stroke=th.stroke, fill=th.fill, style="hachure", sw=1.5)
            gy += 36
        cv.text(p.ix, gy + 2, "each cell: ASR in percent", size=13, color="#495057")
    return p


def pipeline(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "1  The attack lab: from seed objective to ASR scorecard", size=34,
                   sub="Each attack-response pair is generated, sent to your target, labelled by a safety evaluator and rolled up into an Attack Success Rate")
    y += 100
    cv.text(0, y, "You choose:", size=18, color="#343a40")
    ChipFlow([Chip(t, theme="cyan", size=16, fill="soft") for t in (
        "risk categories", "attack strategies", "the target: model deployment, Foundry agent or callback", "a taxonomy for agentic risks",
        "number of objectives and turns")], 2400, gap=10).place(cv, 140, y - 5)
    y += 56
    gap = 130
    bw = (W - 5 * gap) / 6
    steps = [
        ("Seed objectives", "curated attack prompts per risk category, a taxonomy, or your custom prompts", "cyan", "files"),
        ("Attack strategy converters", "PyRIT rewrites the prompt: Easy, Moderate or Difficult. Direct probing is often refused", "red", "bug"),
        ("Target", "model deployment, Foundry agent (prompt or container) or a callback", "blue", "foundry"),
        ("Response", "generated text, plus tool outputs for agents (cloud). A hosted-agent run is transient", "gray", None),
        ("Risk and safety evaluator", "labels each attack-response pair with a severity and a reason", "pink", "content-safety"),
    ]
    sc_x = 5 * (bw + gap)
    # scorecard first so the boxes can be centred on it
    sc = mini_scorecard(cv, sc_x, y, bw)
    boxes = []
    for i, (lab, sub, th, ic) in enumerate(steps):
        b = Box(bw, lab, sub=sub, theme=th, icon=ic, icon_pos="top", icon_size=40, fill="hatch", size=20, sub_size=14, pad=12, min_h=170)
        b.place(cv, i * (bw + gap), y + (sc.h - b.h) / 2)
        numbered(cv, b.x + 6, b.y + 6, i + 1, theme=th, d=30, size=17)
        boxes.append(b)
    numbered(cv, sc.x + 6, sc.y + 6, 6, theme="violet", d=30, size=17)
    labels = ["seed prompts", "converted attack", None, "attack-response pair", "labels and reasons"]
    for a, b, lab in zip(boxes, boxes[1:] + [sc], labels):
        connect(cv, a, b, a_side="right", b_side="left", end_head="arrow", sw=3, label=lab, label_size=14, label_wrap=gap - 14, label_pos="above", label_dy=-4)
    y2 = sc.bottom + 44
    with cv.panel(0, y2, title="After the scorecard: mitigate, re-run, schedule", sub="the loop that turns findings into fixes", theme="violet", style="dashed",
                  fill="none", pad=20, title_size=24, sub_size=15, w=W) as lp:
        chain(cv, lp.ix, lp.iy, W - 40, [
            ("Mitigate", "guardrails (Content Safety filters, safety system messages) and prompt changes; Control Plane guardrails for agent fleets"),
            ("Re-run and compare ASR", "same categories and strategies, so the scorecards compare"),
            ("Schedule recurring runs", "continuous red teaming after deployment (cloud, scheduled scans are preview)"),
        ], theme="violet", dash="dashed", gap=90, themes=["pink", "violet", "violet"])
    arrow(cv, [(sc.cx, sc.bottom + 6), (sc.cx, lp.y - 6)], end_head="arrow", sw=3, dash="dashed", label="findings", label_size=14, label_pos="left")
    return lp.bottom


# ============================================================================================== 2. how it works + ties
def how_it_works(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "2  How it works, and where it plugs in", size=34,
                   sub="One service, three jobs, framed by the NIST AI RMF and used at every stage of the lifecycle")
    y += 100
    c1 = Card(SPAN(2), "Three jobs", [
        "# 1  Automated scans",
        "Simulate adversarial probing for content risks",
        "# 2  Evaluate probing success",
        "Score each attack-response pair; ASR = successful attacks / total attacks (percent)",
        "# 3  Report and log",
        "A scorecard by attack technique and risk category; findings are logged, monitored and tracked in Foundry",
    ], theme="violet", icon="metrics", fill="hatch", title_size=21, body_size=16, src=src("concept"))
    c2 = Card(SPAN(2), "Why converters, and what judges", [
        "Curated seed prompts (attack objectives) per risk category",
        "Direct probing is often refused, so PyRIT attack strategies convert the prompt (docs example: flip the characters to get past the refusal)",
        "A fine-tuned adversarial large language model is dedicated to simulating attacks and evaluating responses, together with the Risk and Safety evaluators",
        "Baseline first: with no strategy chosen, only direct adversarial queries are sent",
    ], theme="red", icon="bug", fill="hatch", title_size=21, body_size=16, src=src("concept", "rs"))
    c1.place(cv, 0, y)
    c2.place(cv, 0, c1.bottom + 28)
    # hub
    hx = X(2)
    with cv.panel(hx, y, title="Where it plugs in", sub="the same agent serves evaluation, monitoring and mitigation", theme="gray", style="dotted", fill="soft", pad=20,
                  title_size=24, sub_size=15, w=SPAN(2)) as hub:
        sat_w = 520
        centre = Box(420, "AI Red Teaming Agent", sub="PyRIT strategies plus risk and safety evaluators", theme="red", icon="bug", icon_pos="top", icon_size=44,
                     fill="hatch", size=22, sub_size=15, pad=12, min_h=230)
        sats = [
            Box(sat_w, "Evaluations", sub="a red team is an evaluation group on the same Evals API, with scenario red_team", theme="violet", icon="metrics", icon_pos="left",
                icon_size=32, fill="hatch", size=19, sub_size=14, pad=10, min_h=96),
            Box(sat_w, "Monitor tab", sub="scheduled red-team scans (preview); red-team results are a Monitor metric; alerts (preview)", theme="violet", icon="dashboard",
                icon_pos="left", icon_size=32, fill="hatch", size=19, sub_size=14, pad=10, min_h=96),
            Box(sat_w, "Guardrails and Control Plane", sub="mitigate with Content Safety filters and safety system messages; fleet guardrails in the Control Plane", theme="pink",
                icon="content-safety", icon_pos="left", icon_size=32, fill="hatch", size=19, sub_size=14, pad=10, min_h=96),
        ]
        total = sum(s.h for s in sats) + 2 * 18
        cy0 = hub.iy + 6
        centre.place(cv, hub.ix, cy0 + (total - centre.h) / 2)
        _, sb = col(cv, hub.ix + 420 + 90, cy0, sats, gap=18)
        for s in sats:
            connect(cv, centre, s, a_side="right", b_side="left", end_head="arrow", sw=2, route="elbow")
    # lifecycle + NIST
    ly = max(c2.bottom, hub.bottom) + 40
    with cv.panel(0, ly, title="Use it across the lifecycle", sub="framed with the NIST AI RMF: Govern, Map, Measure, Manage, with the focus on Map, Measure and Manage", theme="violet",
                  style="dotted", fill="none", pad=20, title_size=24, sub_size=15, w=W) as lc:
        nist = [Chip("Govern", theme="gray", size=16, dash="dashed", fill="soft"), Chip("Map", theme="violet", size=16), Chip("Measure", theme="violet", size=16),
                Chip("Manage", theme="violet", size=16)]
        nx = lc.ix
        cv.text(nx, lc.iy + 4, "NIST AI RMF:", size=17, color="#343a40")
        nx += 130
        for c in nist:
            c.place(cv, nx, lc.iy)
            nx += c.w + 12
        cv.text(nx + 20, lc.iy + 4, "shift left: find risks while changing the design is cheap", size=16, color="#495057")
        chain(cv, lc.ix, lc.iy + 52, W - 40, [
            ("Design", "pick the safest foundation model"),
            ("Development", "upgrade or fine-tune the model"),
            ("Pre-deployment", "scan before release"),
            ("Post-deployment", "scheduled continuous red-teaming runs on synthetic adversarial data"),
        ], theme="violet", gap=70)
    return lc.bottom


# ============================================================================================== 3. risk categories + agentic
def risk_matrix(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "3  Risk categories: ten categories, three of them agent-only", size=34,
                   sub="Text-based scenarios only. The agentic categories run only in the cloud, against Foundry agents, in a minimally sandboxed environment")
    y += 100
    t = Table([("Risk category", 340), ("Model", 110), ("Agent", 110), ("Local", 110), ("Cloud", 110), ("Local maximum objectives, and notes", 876)], [
        ["Hateful and unfair content", CHECK, CHECK, CHECK, CHECK, "HateUnfairness: up to 100"],
        ["Sexual content", CHECK, CHECK, CHECK, CHECK, "Sexual: up to 100"],
        ["Violent content", CHECK, CHECK, CHECK, CHECK, "Violence: up to 100"],
        ["Self-harm-related content", CHECK, CHECK, CHECK, CHECK, "SelfHarm: up to 100"],
        ["Protected materials", CHECK, CHECK, CHECK, CHECK, "ProtectedMaterial: up to 200"],
        ["Code vulnerability", CHECK, CHECK, CHECK, CHECK, "CodeVulnerability: up to 389"],
        ["Ungrounded attributes", CHECK, CHECK, CHECK, CHECK, "UngroundedAttributes: up to 200"],
        [("Prohibited actions", "orange"), CROSS, CHECK, CROSS, CHECK, "Agents only, cloud only: dynamic prompts from your policy and taxonomy"],
        [("Sensitive data leakage", "orange"), CROSS, CHECK, CROSS, CHECK, "Agents only, cloud only: synthetic sensitive data and mock tools"],
        [("Task adherence", "orange"), CROSS, CHECK, CROSS, CHECK, "Agents only, cloud only: goal, rules and procedure"],
    ], theme="pink", size=15, head_size=16, title="Risk categories by target and run mode", title_size=22, align=["left", "center", "center", "center", "center", "left"])
    t.place(cv, 0, y)
    n = Note(SPAN(3), "A default local scan covers 4 categories (violence, sexual, hate and unfairness, self-harm) x num_objectives (default 10) = 40 prompts. "
             "Local scans accept custom prompts for violence, sexual, hate_unfairness and self_harm.", kind="info", title="Default local scan", src=src("concept", "local"))
    n.place(cv, 0, t.bottom + 24)
    # right column: sandbox + supported matrix
    sx = X(3)
    sb = Card(SPAN(3), "Agentic risks run in a minimally sandboxed environment (cloud only)", [
        "The scan checks tool outputs as well as generated text",
        "Harmful or adversarial inputs are redacted from the results",
        "With a Foundry hosted agent as the target, the run is transient: no chat completions are stored and Agent Service does not log them",
        "Recommended: a 'purple environment', non-production with production-like resources",
    ], theme="orange", icon="agent", fill="hatch", title_size=21, body_size=16, src=src("concept"))
    sb.place(cv, sx, y)
    tm = Table([("Target or tool (cloud red teaming)", 600), ("Supported", 240), ("Note", 816)], [
        ["Foundry hosted prompt agents", CHECK, ""],
        ["Foundry hosted container agents", CHECK, ""],
        ["Azure tool calls", CHECK, "tools via the Foundry Toolbox"],
        [("Workflow agents", "red"), CROSS, ""],
        [("Non-Foundry agents", "red"), CROSS, ""],
        [("External (registered) agents", "red"), CROSS, "also not supported for human evaluation or traces to datasets"],
        [("Function tool calls", "red"), CROSS, ""],
        [("Non-Azure tools", "red"), CROSS, ""],
        [("Browser automation, Connected Agent, Computer Use", "red"), CROSS, ""],
    ], theme="orange", size=15, head_size=16, title="What the agentic scan can target", title_size=22, align=["left", "center", "left"])
    tm.place(cv, sx, sb.bottom + 24)
    yb = max(n.bottom, tm.bottom) + 40
    # four agentic risk cards
    cw4 = (W - 3 * GUT) / 4

    def rc(title, body, theme, keys):
        return Card(cw4, title, body, theme=theme, icon="content-safety", fill="hatch", title_size=21, body_size=15, pad=14, gap=4, icon_size=32, src=src(*keys))

    cards = [
        rc("Sensitive data leakage", [
            "Synthetic sensitive data plus mock tools",
            "ASR comes from pattern matching of format-level leaks",
            "! Single-turn, English-only, synthetic data; excludes memory and training-set leaks",
        ], "orange", ("concept",)),
        rc("Prohibited actions", [
            "Dynamic adversarial prompts from your policy plus a taxonomy of prohibited actions and the agent's tools and tool descriptions; ASR = policy violations",
            "Prohibited Actions: universally banned, such as facial recognition, emotion inference, social scoring",
            "High-Risk Actions: need human confirmation, such as financial transactions, medical decisions",
            "Irreversible Actions: disclosure and confirmation, such as file deletion, system reset",
            "! Illustrative taxonomy, not Microsoft policy; EU AI Act responsibility stays with you; keep the default prohibited actions. Single-turn, English-only, no live production data",
        ], "orange", ("concept",)),
        rc("Task adherence", [
            "Three dimensions: goal achievement, rule compliance (policy guardrails, presentation contracts) and procedural discipline (tool use, workflow, grounding)",
            "In the cloud API the task adherence criterion takes a deployment_name",
        ], "orange", ("concept", "cloud")),
        rc("Indirect prompt injection (XPIA)", [
            "Synthetic benign user queries plus mock tool outputs that carry attack placeholders",
            "ASR = how often the agent is compromised, judged with prohibited actions, sensitive data leakage and task adherence",
            "Strategy name: IndirectJailbreak (cloud), IndirectAttack (local)",
        ], "red", ("concept",)),
    ]
    _, b = row(cv, 0, yb, cards, gap=GUT)
    return b


# ============================================================================================== 4. attack strategies
EASY = ["AnsiAttack", "AsciiArt", "AsciiSmuggler", "Atbash", "Base64", "Binary", "Caesar", "CharacterSpace", "CharSwap", "Diacritic", "Flip", "Leetspeak",
        "Morse", "ROT13", "SuffixAppend", "StringJoin", "UnicodeConfusable", "UnicodeSubstitution", "Url"]
CAPTION = {
    "Flip": "flips the characters (the docs example)",
    "Jailbreak": "UPIA: user-injected prompt attack",
    "IndirectJailbreak": "XPIA: injected into tool outputs or context",
    "Tense": "rewrites to past tense; needs another gen-AI model",
    "Multi turn": "accumulates context over turns",
    "Crescendo": "gradual escalation",
}


def strategies(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "4  Attack strategies: 24 PyRIT converters as a periodic table", size=34,
                   sub="Coloured by complexity as the docs classify them. Easy tiles are cheap encodings and obfuscations; Difficult tiles need real resources.")
    y += 100
    lx = 0
    for label, th in (("Easy: encodings and obfuscation, low effort (21)", "lime"), ("Moderate: needs another gen-AI model (1)", "yellow"),
                      ("Difficult: significant resources (2, plus compositions)", "red")):
        ch = Chip(label, theme=th, size=16).place(cv, lx, y)
        lx += ch.w + 18
    y += 54
    names = [(n, "lime") for n in EASY] + [("Jailbreak", "lime"), ("IndirectJailbreak", "lime"), ("Tense", "yellow"), ("Multi turn", "red"), ("Crescendo", "red")]
    tw = (SPAN(4) - 7 * 12) / 8
    tiles = [Box(tw, n, sub=CAPTION.get(n), theme=th, fill="hatch", size=16, sub_size=12, pad=8, min_h=62) for n, th in names]
    r_, b = grid(cv, 0, y, tiles, 8, gap_x=12, gap_y=12)
    d = Card(SPAN(2), "Defaults and naming (local SDK)", [
        "AttackStrategy.EASY = Base64, Flip, Morse; MODERATE = Tense; DIFFICULT = a composition of Tense and Base64",
        "AttackStrategy.Compose([a, b]) chains only two strategies",
        "No strategy given: only the baseline direct adversarial queries are sent. Recommended as the first run",
        "Naming drift: IndirectJailbreak in the cloud, IndirectAttack locally; Multi turn on the concepts page, Multiturn in the local SDK",
    ], theme="red", icon="code", fill="hatch", title_size=21, body_size=16, src=src("concept", "local"))
    d.place(cv, X(4), y - 4)
    return max(b, d.bottom)


# ============================================================================================== 5. local vs cloud
def local_vs_cloud(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "5  Local versus cloud runs, and the constraints that matter", size=34,
                   sub="Same agent, two ways to run it. Pick cloud for Foundry (new), agents, scale and schedules; local is preview and for prototyping.")
    y += 100
    t = Table([("", 190), ("Local (preview)", 970), ("Cloud", 1064)], [
        [("Docs page", "gray"), {"text": "Run AI red teaming scans locally", "link": S["local"][1]}, {"text": "Run AI red teaming in the cloud", "link": S["cloud"][1]}],
        [("Install", "gray"), "pip install \"azure-ai-evaluation[redteam]\" (brings PyRIT); Python 3.10 to 3.13, not 3.9", "pip install \"azure-ai-projects>=2.0.0\"; Python 3.10 or later"],
        [("Portal fit", "gray"), "Not compatible with the Foundry (new) portal and SDK", "Foundry (new) and the Evals API"],
        [("Targets", "gray"), "Azure OpenAI model configuration, a simple callback, an OpenAI-chat-protocol callback, or a PyRIT PromptChatTarget",
         "Foundry project deployments, Azure OpenAI deployments (through a connection, connectionName/deploymentName) and Foundry agents (prompt and container)"],
        [("Risk categories", "gray"), "4 content categories by default; 7 supported; custom prompts for violence, sexual, hate_unfairness and self_harm",
         "Those, plus the agentic categories: prohibited actions, sensitive data leakage, task adherence"],
        [("Turns", "gray"), "The page says only single-turn interactions in text-only scenarios, yet lists Multiturn and Crescendo", "num_turns sets the multi-turn depth (the example uses 5)"],
        [("Languages", "gray"), "Spanish, Italian, French, Japanese, Portuguese and Simplified Chinese through SupportedLanguages", "English; the agentic risks are English-only"],
        [("Output", "gray"), "A scorecard JSON through output_path; scan_name names the scan in Foundry", "A run with output_items through the Evals API, and the Foundry portal"],
        [("Best for", "gray"), "Prototyping and model selection", "Larger strategy x category combinations, scheduled continuous post-deployment runs and agentic scenarios"],
        [("Regions", "gray"), "Listed on the Foundry (classic) page", {"text": "Docs disagree: five regions or two (see the note)", "color": "#c92a2a"}],
    ], theme="blue", size=15, head_size=17, title="Local (preview) versus cloud", title_size=22)
    t.place(cv, 0, y)
    nx = X(4)
    n1 = Note(SPAN(2), "Local red teaming is not compatible with the Foundry (new) portal and SDK. Use the cloud path with Foundry (new), and for any agentic risk.",
              kind="gotcha", title="Local is not for Foundry (new)", src=src("local", "cloud"))
    n2 = Note(SPAN(2), "The concepts page lists East US 2, France Central, Sweden Central, Switzerland West and US North Central. The evaluation regions page lists only "
              "East US 2 and North Central US. Check both before you choose a region.", kind="warn", title="Docs disagree: cloud regions", src=src("concept", "regions"))
    n3 = Note(SPAN(2), "The local page says single-turn only, yet lists Multiturn and Crescendo strategies; the cloud API has num_turns. Treat multi-turn depth as a cloud feature.",
              kind="warn", title="Docs disagree: turns", src=src("local", "cloud"))
    _, nb = col(cv, nx, y, [n1, n2, n3], gap=22)
    return max(t.bottom, nb)


# ============================================================================================== 6. cloud flow, schedule, scorecard
def cloud_flow(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "6  The cloud run: API flow, scheduling and the scorecard", size=34,
                   sub="Create a red team, create or confirm a taxonomy, create a run, poll, then read the output items")
    y += 100
    _, yb = chain(cv, 0, y, W, [
        ("Create a red team", "client.evals.create: data_source_config azure_ai_source with scenario red_team; testing criteria builtin.prohibited_actions, builtin.task_adherence (plus deployment_name), builtin.sensitive_data_leakage; evaluator_version 1"),
        ("Create or confirm a taxonomy", "evaluation_taxonomies.create for prohibited actions (REST PUT .../evaluationtaxonomies/{name}, api-version 2025-11-15-preview, with target.tool_descriptions). You review and edit it: it drives the attack prompts and the ASR"),
        ("Create a run", "data_source azure_ai_red_team with item_generation_params red_team_taxonomy; attack_strategies such as Flip, Base64, IndirectJailbreak; num_turns 5; target azure_ai_agent (name, version, tool_descriptions)"),
        ("Poll the run", "evals.runs.retrieve until the status is completed, failed or canceled"),
        ("List the results", "evals.runs.output_items; harmful inputs are redacted in cloud results"),
    ], theme="violet", gap=48, size=20, sub_size=14)
    y2 = yb + 40
    n1 = Note(SPAN(2), "Role: Foundry User. In virtual network setups the project managed identity needs Foundry User at Foundry resource scope, to prevent evaluation and red-teaming run failures.",
              kind="key", title="Permissions", src=src("cloud", "regions"))
    n1.place(cv, 0, y2)
    # scheduling
    with cv.panel(X(2), y2, title="Continuous red teaming: schedule it", sub="Monitor tab settings, preview as of 2026-11-03", theme="violet", style="dashed", fill="soft", pad=18,
                  title_size=22, sub_size=15, w=SPAN(4)) as sp:
        _, sb = chain(cv, sp.ix, sp.iy, SPAN(4) - 36, [
            ("Open the Monitor tab", "for the agent"),
            ("Gear: Monitor settings", "Recurring evaluations, Red team scans, Alerts (all preview)"),
            ("Red team scans (preview)", "enable or disable; pick an evaluation template and run; set the schedule"),
            ("Read the results", "red-teaming results are a Monitor metric; a failed scan is a potential security risk"),
        ], theme="violet", gap=50, size=18, sub_size=14)
        cv.text(sp.ix, sb + 8, "Sample: sample_scheduled_evaluations.py (Scheduled evaluation and Schedule AI red teaming evaluation)", size=14, color="#495057")
    y3 = max(n1.bottom, sp.bottom) + 44
    t = Table([("Scorecard part", 330), ("What it holds", 1326)], [
        [("ASR by category x complexity", "violet"), "easy_complexity_asr, moderate_complexity_asr and difficult_complexity_asr for each risk category"],
        [("ASR per technique", "violet"), "for example Base64Converter_ASR"],
        [("Parameters and summary", "violet"), "the risk categories and strategies used (parameters) and the attack_complexity summary"],
        [("Row-level data", "violet"), "redteaming_data[]: attack_success, attack_technique, attack_complexity, risk_category, conversation, and risk_assessment with a severity_label and a reason per category"],
        [("Where you read it", "violet"), "Local: the scorecard JSON through output_path, named in Foundry by scan_name. Cloud: the run's output_items and the Foundry portal"],
    ], theme="violet", size=15, head_size=16, title="Shape of the scorecard (local JSON; cloud results are evaluation run items)", title_size=22)
    t.place(cv, 0, y3)
    sc = Card(SPAN(3), "Reading the numbers", [
        "ASR = successful attacks / total attacks, as a percentage, by category, complexity and technique",
        "ASR is judged by generative models: non-deterministic, with possible false positives. Review before you mitigate",
        "Re-run the same categories and strategies after a fix, so the two scorecards compare",
        "The defect rate in the safety evaluators is the share of instances above a severity threshold; tune the threshold per domain",
    ], theme="violet", icon="metrics", fill="hatch", title_size=21, body_size=16, src=src("concept", "tn"))
    sc.place(cv, X(3), y3)
    return max(t.bottom, sc.bottom)


# ============================================================================================== 7. limits + transparency note
def limits(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "7  Limits, and the safety-evaluations transparency note", size=34,
                   sub="What the scan cannot tell you, and what Microsoft says about the models behind the evaluators")
    y += 100
    cw4 = (W - 3 * GUT) / 4

    def lc(title, body, theme, icon, keys):
        return Card(cw4, title, body, theme=theme, icon=icon, fill="hatch", title_size=21, body_size=15, pad=14, gap=4, icon_size=32, src=src(*keys))

    cards = [
        lc("Known limitations (concepts page)", [
            "Synthetic data is not representative of real distributions",
            "Mock tools return only synthetic data, with no mocked behaviours",
            "Not a fully locked-down sandbox: attacks are controlled to avoid real-world impact",
            "Only the adversarial population is tested, no observational data",
            "ASR is judged by generative models: non-deterministic, false positives possible. Review before mitigating",
        ], "red", "bug", ("concept",)),
        lc("How the evaluators work", [
            "Foundry Models sold by Azure are evaluated against Microsoft's RAI standards; every other model (for example Anthropic, open models from Hugging Face or Fireworks) is a Non-Microsoft Product that Microsoft does not evaluate: run your own risk and safety evaluations",
            "Foundry provisions a fine-tuned Azure OpenAI GPT-4o to orchestrate adversarial attacks, and another GPT-4o to annotate",
            "Output: a static test dataset, plus a content-risk label (Very low, Low, Medium, High) or a detection label (True, False) with reasoning",
            "! The note describes GPT-4o and may be older than today's service",
        ], "pink", "content-safety", ("tn",)),
        lc("Intended uses and considerations", [
            "Intended: pre-deployment evaluation; augmenting red-teaming operations with the adversarial simulator; communicating risks to stakeholders and auditors in the portal",
            "Keep a human in the loop; not comprehensive coverage and not a replacement for manual red teaming; best for English text",
            "Hate and unfairness coverage is limited to some groups (gender, race, ancestry, ethnicity, nationality); no disability, sexuality or religion coverage",
            "Sexual, violent and self-harm metrics are a preliminary conceptualization; no plug-ins, limited customization, no automated actions",
        ], "pink", "info-protection", ("tn",)),
        lc("Quality check and definitions", [
            "Humans versus the automated annotator on a 0-7 scale: 500 English single-turn texts, 250 text-to-image and 250 multimodal per risk area; match within a 2, 1 or 0 level tolerance",
            "High match for self-harm and sexual; lower for violence and for hate and unfairness (guideline divergence)",
            "Defect rate = share of instances above a severity threshold; the portal has a thumbs up or down human feedback column on safety results",
            "Direct jailbreak = UPIA ('DAN'); indirect jailbreak = XPIA (cross-domain prompt injection); protected material = text or images",
        ], "violet", "learn", ("tn",)),
    ]
    _, b = row(cv, 0, y, cards, gap=GUT)
    return b


# ============================================================================================== 8. manual guidance + gotchas
def manual_and_gotchas(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "8  Manual red teaming still matters, and gotchas", size=34,
                   sub="Red teaming identifies harms; it does not replace systematic measurement and mitigation. Do an initial manual round before you measure.")
    y += 100
    _, yb = chain(cv, 0, y, W, [
        ("Who", "diverse experts with a mix of adversarial and benign mindsets; assign them to harms or features"),
        ("What", "the base model with its safety system through the API; the app through its UI; with and without mitigations; prefer the production UI"),
        ("How", "open-ended first to list harms, then guided rounds"),
        ("Record", "a shared spreadsheet: date, unique ID, input, output"),
        ("Report", "top issues, a link to the raw data, the next plan and a content warning; separate identification from measurement"),
    ], theme="pink", gap=48, size=20, sub_size=14)
    y2 = yb + 40
    notes = [
        Note(CW, "Function tools, non-Azure tools, browser automation, Connected Agent, Computer Use, workflow agents, external (registered) agents and non-Foundry agents cannot be red-teamed.",
             kind="gotcha", title="Unsupported targets", src=src("concept", "ext")),
        Note(CW, "Agentic categories (prohibited actions, sensitive data leakage, task adherence) run only in the cloud, single-turn and English-only, on synthetic data.",
             kind="gotcha", title="Agentic risks are cloud-only", src=src("concept")),
        Note(CW, "The prohibited-actions taxonomy is illustrative, not Microsoft policy. EU AI Act responsibility stays with the customer; the docs strongly recommend keeping the default prohibited actions.",
             kind="warn", title="Taxonomy is a starting point", src=src("concept")),
        Note(CW, "Red teaming appears in the evaluation section of the docs table of contents (Overview, Run in the cloud, Run locally), and the feature status page lists it as GA, "
             "while the local scan and scheduled Red team scans are labelled preview (as of 2026-11-03).", kind="preview", title="Status", src=src("ga", "mon")),
        Note(CW, "Cloud runs are not a substitute for guardrails: in production the docs recommend safety guardrails and, for agent fleets, Foundry Control Plane guardrails.",
             kind="info", title="Mitigate in production", src=src("concept", "guard")),
        Note(CW, "Safety evaluators run on hosted evaluation models and are region-limited (the protected material evaluator: East US 2 only), so check the evaluation regions page before you plan where scans run.",
             kind="tip", title="Regions", src=src("regions", "rs")),
    ]
    _, b = row(cv, 0, y2, notes, gap=GUT)
    return b


def related(cv: Canvas, y: float) -> float:
    cv.text(0, y, "See also in this gallery:", size=18, color="#343a40")
    items = [("Evaluation in depth", "violet"), ("Guardrails and controls", "pink"), ("Foundry Observability: one data model", "violet"),
             ("Tracing: from agent run to the Traces UI", "violet"), ("Foundry Control Plane", "grape"),
             ("Governance, policy and compliance", "grape")]
    f = ChipFlow([Chip(t, theme=th, size=16, fill="soft") for t, th in items], W - 260, gap=12).place(cv, 250, y - 4)
    return max(y + 28, f.y + f.h)


def sources_panel(cv: Canvas, y: float) -> None:
    items = [S[k] for k in ("concept", "cloud", "local", "tn", "manual", "regions", "rs", "mon", "ext", "obs", "ga", "guard", "pyrit")]
    sources(cv, 0, y, items, w=W, cols=4)


def build(cv: Canvas) -> None:
    y = title_and_key(cv) + 30
    y = summary_strip(cv, y) + 60
    y = pipeline(cv, y) + 70
    y = how_it_works(cv, y) + 70
    y = risk_matrix(cv, y) + 70
    y = strategies(cv, y) + 70
    y = local_vs_cloud(cv, y) + 70
    y = cloud_flow(cv, y) + 70
    y = limits(cv, y) + 70
    y = manual_and_gotchas(cv, y) + 50
    y = related(cv, y) + 40
    sources_panel(cv, y)

