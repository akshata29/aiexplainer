"""Agent lifecycle and the optimizer (Agent Service), part 2: the agent optimizer in depth (Preview) - prompt-agent wizard vs hosted azd path,
making a hosted agent optimizer-ready, datasets and evaluators, run / monitor / apply / deploy, REST and SDK, costs and token usage - plus the
separate Prompt Optimizer and the hosted-agent CI/CD template quickstart.

Part 1 ('agent-lifecycle-optimizer') draws the lifecycle loop, local toolbelt, evaluation hooks, optimizer at a glance, release path and
what-to-use-when table.  Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import Note as _KitNote
from generator.xd.palette import STATUS

META = dict(
    id="agent-lifecycle-optimizer-part-2", title="The agent optimizer in depth: files, datasets, runs, costs and the Prompt Optimizer", section="2", group="Agent Service", order=17.5,
    description="The agent optimizer (Preview) in depth: prompt-agent wizard vs hosted azd path, optimizer-ready files, datasets and evaluators, run, apply and deploy, "
                "REST, cost estimates and token usage, the separate Prompt Optimizer and the hosted-agent CI/CD template.",
    tags=["agent-optimizer", "prompt-optimizer", "datasets", "eval-yaml", "token-usage", "ci-cd"],
)


class Note(_KitNote):
    """Kit Note plus 10 px of bottom padding when it carries Learn: lines (the kit lets the last link touch the border)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if self.src_lines:
            self.h += 10


W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    ovo=("Agent optimizer overview", learn("agents/concepts/agent-optimizer-overview")),
    costs=("Agent optimizer costs and token usage", learn("agents/concepts/agent-optimizer-costs")),
    ready=("Make your agent optimizer-ready", learn("agents/how-to/make-agent-optimizer-ready")),
    ds=("Create an optimizer dataset and evaluators", learn("agents/how-to/create-optimizer-dataset")),
    tg=("Optimize agent instructions, skills, tools and models", learn("agents/how-to/optimize-agent-targets")),
    qh=("Quickstart: optimize a hosted agent", learn("agents/quickstarts/quickstart-optimize-hosted-agent")),
    qp=("Quickstart: optimize a prompt agent", learn("agents/quickstarts/quickstart-optimize-prompt-agent")),
    po=("Optimize agent prompts with Prompt Optimizer", learn("observability/how-to/prompt-optimizer")),
    cicd=("Set up CI/CD for hosted agents with azd", learn("agents/how-to/set-up-ci-cd-cli")),
    cdq=("Quickstart: set up CI/CD for a hosted agent", learn("agents/quickstarts/set-up-cicd-hosted-agent")),
    rest=("REST: create an agent optimization job", learn("reference/rest/agent-optimization-jobs-create")),
    life=("Agent development lifecycle", learn("agents/concepts/development-lifecycle")),
    azdeval=("Evaluate agents with the Azure Developer CLI", learn("observability/how-to/azure-developer-cli-evaluation")),
    ctx=("Set the Foundry project context for azd commands", learn("agents/how-to/cli-project-context")),
)


def src(*keys: str) -> list:
    return [U[k] for k in keys]


def card(w, title, body, theme="green", **kw) -> Card:
    """Dense-column card: one type scale for the whole canvas."""
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("sub_size", 13)
    kw.setdefault("pad", 14)
    kw.setdefault("gap", 4)
    kw.setdefault("icon_size", 30)
    return Card(w, title, body, theme=theme, **kw)


def wrap(s: str, w: float, size: float) -> str:
    return "\n".join(wrap_text(s, w, size))


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


def bullets(cv, x, y, w, items, theme_name="violet", size=15, gap=6) -> float:
    """Ring-bullet list drawn straight on the canvas (same look as Card bullets, no border); returns the bottom y."""
    th = THEMES[theme_name]
    cy, lh = y, size * metrics.line_ratio()
    for it in items:
        warn = it.startswith("! ")
        txt = it[2:] if warn else it
        lines = wrap_text(txt, (w - 22) * 0.965, size)
        mc = "#e03131" if warn else th.stroke
        cv.ellipse(x + 2, cy + lh / 2 - 4, 9, 9, stroke=mc, sw=2, rough=0)
        cv.text(x + 22, cy, "\n".join(lines), size=size, color="#c92a2a" if warn else INK)
        cy += len(lines) * lh + gap
    return cy - gap


def cite(cv, x, y, items) -> float:
    """Clickable 'Learn:' lines; returns the bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 2
    return y


class Tile(Rect2):
    """Big-number summary tile: headline + one caption."""

    def __init__(self, w, big, cap, theme="green", big_size=34, cap_size=15, pad=14):
        self.th = THEMES[theme]
        self.w, self.big_size, self.cap_size, self.pad = w, big_size, cap_size, pad
        inner = (w - 2 * pad) * 0.965
        self.big_lines = wrap_text(big, inner, big_size)
        self.cap_lines = wrap_text(cap, inner, cap_size)
        lr = metrics.line_ratio()
        self.h = pad * 2 + len(self.big_lines) * big_size * lr + 8 + len(self.cap_lines) * cap_size * lr
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            ty = y + self.pad
            inner = self.w - 2 * self.pad
            cv.text(x + self.pad, ty, "\n".join(self.big_lines), size=self.big_size, color=th.deep, align="center", w=inner)
            ty += len(self.big_lines) * self.big_size * lr + 8
            cv.text(x + self.pad, ty, "\n".join(self.cap_lines), size=self.cap_size, color=INK, align="center", w=inner)
        cv.register("tile", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class Steps(Rect2):
    """Numbered walk-through card."""

    def __init__(self, w, title, steps, theme="yellow", num_theme="blue", size=14, pad=14, src=(), title_size=19):
        self.th = THEMES[theme]
        self.w, self.title, self.steps, self.num_theme, self.size, self.pad, self.title_size = w, title, steps, num_theme, size, pad, title_size
        self.tw = (w - 2 * pad - 38) * 0.965
        lr = metrics.line_ratio()
        self.lines = [wrap_text(t, self.tw, size) for t in steps]
        self.row_h = [max(len(ln) * size * lr, 26) + 9 for ln in self.lines]
        self.src = list(src)
        h = pad + title_size * lr + 8 + sum(self.row_h) + 4
        self.src_lines = []
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * lr + 2
        self.h = h + pad - (2 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, lr = self.th, metrics.line_ratio()
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=th.deep)
            cy = y + self.pad + self.title_size * lr + 8
            for i, (ln, rh) in enumerate(zip(self.lines, self.row_h)):
                numbered(cv, x + self.pad + 13, cy + 13, i + 1, theme=self.num_theme, d=26, size=15)
                cv.text(x + self.pad + 38, cy + 4, "\n".join(ln), size=self.size, color=INK)
                cy += rh
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("steps", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


class CodeBlock(Rect2):
    """Monospace snippet in a soft rounded box (Excalifont has no code face, so Comic Shanns is used)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=14, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title = w, size, pad, title
        inner = (w - 2 * pad) * 0.965
        self.lines: list[str] = []
        for ln in lines:
            if metrics.line_width(ln, size, MONO) <= inner:
                self.lines.append(ln)
            else:
                self.lines += wrap_text(ln, inner, size, MONO)
        self.lh = size * metrics.line_ratio(MONO)
        self.t_h = (17 * 1.25 + 6) if title else 0
        self.src = list(src)
        self.src_h = (8 + len(self.src) * 15) if self.src else 0
        self.h = pad * 2 + self.t_h + len(self.lines) * self.lh + self.src_h
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.soft, style="solid", sw=2)
            ty = y + self.pad
            if self.title:
                cv.text(x + self.pad, ty, self.title, size=17, color=self.th.deep)
                ty += self.t_h
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=MONO)
            sy = ty + len(self.lines) * self.lh + 8
            for label, url in self.src:
                cv.text(x + self.pad, sy, f"Learn: {label}", size=12, color=LINK, link=url)
                sy += 15
        cv.register("code", x, y, self.w, H)
        return self


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "5 to 60 min", "Run time grows with candidates (3 to 10 tasks): 2 candidates take about 5 to 10 minutes, 5 take 20 to 30, 10 take 30 to 60.", "violet"),
        Tile(C, "15 to 1,000", "azd ai agent eval generate --max-samples accepts 15 to 1,000 tasks. For hand-written sets, 5 to 10 tasks balance speed and coverage.", "violet"),
        Tile(C, "Min / Est / Max", "A pre-run cost estimate exists only for prompt-agent portal runs, and the maximum is not a spending cap.", "yellow"),
        Tile(C, "60 + 120 + 12", "Worked example: 2 candidates x 20 rows x 2 evaluators = 60 agent calls, 120 judge calls and about 12 reflection calls.", "yellow"),
        Tile(C, "Apply, then deploy", "A hosted candidate is applied to .agent_configs/<id>/ and redeployed; a prompt-agent candidate is promoted to a new version.", "green"),
        Tile(C, "Ephemeral", "Prompt Optimizer results are not stored: select Use prompt before you close the dialog. There is no version history.", "gray"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: two paths
def band_paths(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  Two paths, one six-step workflow",
             "Prompt agents use a portal wizard and need no code. Hosted agents use azd (or the Foundry Toolkit) and a small code integration. Both walk the same six steps.")
    top = y
    gap = 64
    bw = (W - 5 * gap) / 6
    flow = [("1  Select the baseline", "the version or configuration to beat"), ("2  Dataset", "representative tasks"), ("3  Evaluation criteria", "built-in or custom evaluators"),
            ("4  Run", "choose targets and models; generate and evaluate candidates"), ("5  Review", "compare candidate scores with the baseline"),
            ("6  Apply", "promote, or apply and redeploy")]
    boxes = [Box(bw, lab, sub=sub, theme="violet", h=130, size=19, sub_size=14, fill="hatch") for lab, sub in flow]
    row(cv, 0, top, boxes, gap=gap)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#6741d9")
    ty = boxes[0].bottom + 30
    t = Table([("Step", 250), ("Prompt agent: portal wizard (Preview)", 1560), ("Hosted agent: azd or Foundry Toolkit (Preview)", 1790)], [
        [ct("1 Baseline", "violet"), "Target step: pick the baseline agent version",
         "The optimizer-ready configuration: .agent_configs/baseline/ (referenced as agent.config in eval.yaml)"],
        [ct("2 Dataset", "violet"), "Generate one from agent traces, pick a registered dataset or upload JSONL in the wizard",
         "A local JSONL file (local_uri) or a registered Foundry dataset (name and version); azd ai agent eval generate makes a seed dataset"],
        [ct("3 Criteria", "violet"), "Built-in, custom or rubric evaluators",
         "evaluators in eval.yaml: built-in (for example builtin.task_adherence) or custom; an editable rubric_dimensions.json"],
        [ct("4 Run", "violet"), "Target settings: optimization model, max candidates, evaluation model, Compare across models. Review shows the cost estimate, then Submit",
         "azd ai agent optimize [--config eval.yaml]; --eval-model and --optimize-model flags; an asynchronous cloud job"],
        [ct("5 Review", "violet"), "Compare scores, the before and after instructions, token usage and per-evaluator results on the Optimize tab",
         "A results table with a star on the best candidate; optimize status <operation-id> --watch, list and cancel; the portal Optimize tab"],
        [ct("6 Apply", "violet"), "Promote candidate: it becomes a new prompt-agent version (set it active if the endpoint is pinned)",
         "optimize apply --candidate <id> writes .agent_configs/<id>/; review the diff, then azd deploy (optimize deploy is for quick tests)"],
    ], w=W, theme="violet", size=14, head_size=15, title="Same steps, different surfaces", title_size=22)
    t.place(cv, 0, ty)
    cite(cv, 0, t.bottom + 8, src("ovo", "qp", "qh"))
    return t.bottom + 50


# ================================================================================================ band 2: optimizer-ready
def band_ready(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Hosted agents: make the agent optimizer-ready",
             "The optimizer improves the configuration your code loads at runtime. A baseline folder plus one function call is all the integration there is; the Foundry Toolkit can scaffold it for you.")
    top = y
    tree = CodeBlock(S(2), [
        ".agent_configs/",
        "  baseline/                your current configuration",
        "    metadata.yaml          model + instruction_file (required);",
        "                           tools_file, skill_dir, temperature (optional)",
        "    instructions.md        instruction tuning target",
        "    tools.json             tool optimization target (function-calling only)",
        "    skills/<name>/SKILL.md skill improvement target (Agent Skills format)",
        "  <candidate_id>/          written by: azd ai agent optimize apply",
    ], title="What the optimizer reads", theme="violet", src=src("ready"))
    tree.place(cv, 0, top)
    st = Steps(S(2), "Four steps (as of 2026-11-03)", [
        "pip install azure-ai-agentserver-optimization (Python 3.10 or later)",
        "Create .agent_configs/baseline/ with metadata.yaml and instructions.md; add tools.json and skills/ if you want those targets",
        "Call load_config() at startup. It returns the baseline normally and the candidate configuration during an optimization run",
        "Check the agent answers (azd ai agent invoke \"test\"), then run azd ai agent optimize",
    ], theme="violet", num_theme="violet", size=15, src=src("ready", "qh"))
    st.place(cv, X(2) + 0, top)
    # load_config diagram
    dx = 2 * (S(2) + G)
    with cv.panel(dx, top, title="One code path, two configurations", theme="violet", style="dotted", pad=18, title_size=22, w=S(2)) as pn:
        a = Box(300, "Your agent code", sub="unchanged between runs", theme="green", h=100, size=18, sub_size=13, fill="hatch", icon="agent", icon_pos="left", icon_size=30)
        b = Box(290, "load_config()", sub="no flags, no branching", theme="violet", h=100, size=18, sub_size=13, fill="hatch", icon="gear", icon_pos="left", icon_size=30)
        c1 = Box(330, "Baseline", sub="a normal run", theme="gray", h=76, size=17, sub_size=13, fill="hatch")
        c2 = Box(330, "Candidate", sub="during an optimization run", theme="violet", h=76, size=17, sub_size=13, fill="hatch")
        a.place(cv, pn.ix, pn.iy + 50)
        b.place(cv, pn.ix + 380, pn.iy + 50)
        c1.place(cv, pn.ix + 760, pn.iy + 0)
        c2.place(cv, pn.ix + 760, pn.iy + 110)
        connect(cv, a, b, sw=3, color="#6741d9")
        connect(cv, b, c1, a_side="right", b_side="left", route="elbow", sw=3, color="#6741d9")
        connect(cv, b, c2, a_side="right", b_side="left", route="elbow", sw=3, color="#6741d9")
    y2 = max(tree.bottom, st.bottom, pn.bottom) + 30
    n1 = Note(S(2), "Hosted-agent optimization needs the Responses protocol and is available in all hosted regions except Norway East (as of 2026-11-03).", kind="warn",
              title="Constraints", src=src("ovo"))
    n2 = Note(S(2), "Skills use the open Agent Skills format: one SKILL.md per skill under skills/<name>/. The optimizer can refine existing skills and can also discover and create skills.",
              kind="info", title="Skills", src=src("ready"))
    n3 = Note(S(2), "Tool optimization changes descriptions of function-calling tools only: never names, types, defaults or required fields. Only function-calling tools are supported.",
              kind="info", title="Tools", src=src("ovo"))
    row(cv, 0, y2, [n1, n2, n3], gap=G)
    return y2 + max(n1.h, n2.h, n3.h)


# ================================================================================================ band 3: datasets
def band_data(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Datasets and evaluators: what to test, and how to judge it",
             "Weak evaluators give noisy scores and poor candidates: invest in them as much as in representative tasks. azd ai agent eval generate creates a starting set for you.")
    top = y
    LW = S(3)
    t1 = Table([("Flag of azd ai agent eval generate", 400), ("What it does", 1376)], [
        ["--gen-instruction, --gen-instruction-file", "Describe the test scenarios you want generated"],
        ["--eval-model", "Selects the generation model"],
        ["--out-file", "Selects the output configuration"],
        ["--max-samples", "Sample count, 15 to 1,000"],
        ["--no-wait", "Submit without waiting for completion"],
        ["--dataset, --evaluator", "Supply an existing dataset; select evaluator names"],
    ], w=LW, theme="violet", size=14, head_size=15, title="Generate", title_size=20)
    t1.place(cv, 0, top)
    gen = card(LW, "What generate produces by default", [
        "A seed dataset of tasks tuned to your agent's domain",
        "Evaluators: a built-in one such as builtin.task_adherence plus a custom rubric evaluator, kept as an editable rubric_dimensions.json",
        "A runnable eval.yaml that wires them together; azd ai agent optimize then auto-detects it",
        "To refine: edit rubric_dimensions.json, then azd ai agent eval update (use --dataset-only, --evaluator-only or --config to scope it)",
    ], theme="violet", icon="metrics", src=src("ds"))
    gen.place(cv, 0, t1.bottom + 24)
    c1 = card(LW, "Two dataset sources", [
        "Foundry dataset: registered in the project; reference it in eval.yaml by name and version",
        "Local dataset: a JSONL file in your project; reference it by local_uri (relative to the config file)",
        "Validate JSONL before a run: a bad line fails with 'invalid JSON on line N'",
    ], theme="violet", icon="files", src=src("ds"))
    c1.place(cv, 0, gen.bottom + 24)

    rx = LW + G
    t2 = Table([("Task field", 200), ("Required", 140), ("Description", 1436)], [
        ["name", ct("Yes", "red"), "Unique task identifier"],
        ["query", ct("Yes", "red"), "The message sent to the agent"],
        ["ground_truth", ct("No", "gray"), "Expected answer, for evaluators that support a reference"],
        ["criteria[].name and criteria[].instruction", ct("No", "gray"), "Optional per-task checks, scored together with the shared evaluators; be specific and testable"],
    ], w=LW, theme="violet", size=14, head_size=15, title="JSONL task schema (one JSON object per line)", title_size=20)
    t2.place(cv, rx, top)
    code = CodeBlock(LW, [
        '{"name": "refund_policy", "query": "What is your refund policy?",',
        ' "criteria": [{"name": "mentions_30_days",',
        '   "instruction": "Response must mention the 30-day refund window"}]}',
        '{"name": "geography_fact", "query": "Largest city in France?", "ground_truth": "Paris"}',
    ], title="Two example tasks (illustrative)", theme="violet", src=src("ds"))
    code.place(cv, rx, t2.bottom + 24)
    t3 = Table([("Dataset size", 260), ("Trade-off", 1516)], [
        ["3 to 5 tasks", "Quick iteration, limited signal"], ["5 to 10 tasks", "Good balance of speed and coverage"],
        ["10 to 20 tasks", "Comprehensive evaluation, longer runs"], ["20 or more", "Thorough but slow: consider it for final validation"],
    ], w=LW, theme="violet", size=14, head_size=15, title="Size guidelines", title_size=20)
    t3.place(cv, rx, code.bottom + 24)
    left_b = c1.bottom
    y2 = max(left_b, t3.bottom) + 36
    c2 = card(LW, "Register and version with azd ai dataset", [
        "azd ext install azure.ai.dataset, then azd ai project set <project-endpoint>",
        "azd ai dataset create <name> --from-file <jsonl>; update, list, show, versions list, download, delete",
        "Keep the dataset version fixed when you compare agent changes; azd ai eval dataset exposes the same lifecycle",
    ], theme="cyan", icon="storage", src=src("ds"))
    c3 = card(LW, "Write good datasets", [
        "Include edge cases: out-of-scope requests, ambiguous queries, adversarial inputs, multi-step tasks",
        "Use real user messages where you can; provide ground_truth when it helps",
        "Vague criteria give inconsistent scores between runs: make each one specific and testable",
    ], theme="gray", icon="learn", src=src("ds"))
    row(cv, 0, y2, [c2, c3], gap=G)
    return y2 + max(c2.h, c3.h)


# ================================================================================================ band 4: run
def band_run(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Run, monitor, apply and deploy",
             "One command starts a cloud job; follow-up commands watch it; apply brings the winner back into your repo so the normal deploy path ships it.")
    top = y
    gap = 64
    bw = (W - 4 * gap) / 5
    flow = [
        ("azd ai agent optimize", "add --config eval.yaml to control the run; --agent <name> when several services exist", "azd", "violet"),
        ("Watch the job", "optimize status <operation-id> --watch, optimize list, optimize cancel; or the portal Optimize tab", "monitor", "violet"),
        ("Read the results", "a table with a star on the best candidate; if every candidate scores below the baseline, deploy nothing", "metrics", "violet"),
        ("optimize apply --candidate <id>", "downloads .agent_configs/<id>/ (prompt agents: updates the local model, instructions and matching tool descriptions)", "files", "green"),
        ("Review the diff, then azd deploy", "the normal deploy path; use apply then deploy for production", "builds", "green"),
    ]
    boxes = [Box(bw, lab, sub=sub, theme=th, h=170, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for lab, sub, ic, th in flow]
    row(cv, 0, top, boxes, gap=gap)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#343a40")
    y2 = boxes[0].bottom + 40
    code = CodeBlock(S(2), [
        "name: my-optimization",
        "agent:",
        "  name: my-agent              # deployed hosted agent",
        "  kind: hosted",
        '  version: "1"                # optional',
        "  model: gpt-4.1-mini         # baseline deployment",
        "  config: .agent_configs/baseline/metadata.yaml",
        "dataset:",
        "  local_uri: ./eval.jsonl     # or name + version",
        "# validation_dataset: ...     # optional held-out set",
        "evaluators:",
        "  - builtin.task_adherence",
        "options:",
        "  eval_model: gpt-4.1-mini    # scores responses",
        "  optimization_model: gpt-5.1 # required",
        "  max_candidates: 4           # default 5",
        "  optimization_config:",
        "    model_search_space:",
        "      - gpt-4.1",
    ], title="eval.yaml (shape from the how-to)", theme="violet", src=src("tg"))
    code.place(cv, 0, y2)
    t = Table([("Max candidates", 260), ("Time", 240), ("Best for", 668)], [
        ["2", "5 to 10 min", "Quick experiments"], ["5 (default)", "20 to 30 min", "A good balance"], ["10", "30 to 60 min", "Thorough exploration"],
    ], w=S(2), theme="violet", size=15, head_size=16, title="How many candidates (3 to 10 tasks)", title_size=20)
    t.place(cv, X(2), y2)
    n1 = Note(S(2), "The optimizer learns from earlier candidates, so later ones tend to score higher. max_candidates is the expected count: the run normally returns once it is reached, unless it "
                    "stops early on an error or another stopping condition. Larger datasets or a slower eval model lengthen the run.", kind="info", title="More candidates, more exploration", src=src("tg"))
    n1.place(cv, X(2), t.bottom + 24)
    n2 = Note(S(2), "optimization_model is required: without it (in eval.yaml or --optimize-model) the API returns an error. The model_search_space list must name deployments in your project; "
                    "your agent's current model is removed from it automatically, and an empty list is a validation error.", kind="warn", title="Models are checked up front", src=src("tg", "ovo"))
    n2.place(cv, X(2), n1.bottom + 24)
    n_alt = Note(S(2), "optimize deploy --candidate <id> deploys through the API without changing your local files: handy for quick A/B tests. For production use apply, review, then azd deploy. "
                       "If every candidate scores below the baseline, deploy none: the baseline stays active.", kind="warn", title="Alternative: direct deploy", src=src("tg"))
    n_alt.place(cv, 2 * (S(2) + G), y2)
    c1 = card(S(2), "No azure.yaml? Run standalone", [
        "Deploy the agent first and make it optimizer-ready; omit agent.config in eval.yaml",
        "azd ai project set <project-endpoint> (or pass --project-endpoint), then azd ai agent optimize --agent <deployed-name> --config eval.yaml",
        "Run it interactively: it asks for the baseline instruction (do not use --no-prompt); skill and tool file baselines need an azd project",
        "Keep the operation ID: with no azd environment the CLI does not store it",
        "! apply and direct deploy need an azd project; otherwise deploy the winner from the Foundry portal",
    ], theme="violet", icon="browser", src=src("tg", "ctx"))
    c1.place(cv, 2 * (S(2) + G), n_alt.bottom + 24)
    return max(code.bottom, n2.bottom, c1.bottom)


# ================================================================================================ band 5: REST
def band_rest(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  REST and SDK: the AgentOptimizationJobs operations",
             "The portal and azd call the same API. It needs a feature header while it is in preview, and the job is long-running: create it, then poll the operation location.")
    top = y
    LW = S(4)
    t = Table([("Operation", 320), ("Route as documented", 760), ("Notes", 1304)], [
        [ct("Create a job", "violet"), "POST /agent_optimization_jobs", "Idempotent through the Operation-Id header; poll the Operation-Location header the response returns; needs the feature header below"],
        [ct("Estimate", "yellow"), ".../estimate", "Named with the job operations in the REST reference; its request and response were not read for this canvas"],
        [ct("List and get candidates", "violet"), "route not read", "Candidate operations are named in the REST reference; their details were not read"],
        [ct("Promote a candidate", "green"), "route not read", "The REST counterpart of Promote candidate in the portal wizard"],
    ], w=LW, theme="violet", size=14, head_size=15, title="Operations (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, top)
    cb = CodeBlock(LW, [
        "feature header: AgentsOptimization=V2Preview   (C#: FoundryFeaturesPolicy)",
        "",
        "agent_optimization",
        "  goal                          improve_quality (the only documented value)",
        "  training / validation sets    target_completion (single turn) or user_conversation_simulation",
        "  evaluators, evaluation_model",
        "  candidate_search_configuration.max_candidates     default 1 in the REST schema",
        "  baseline_agent_configuration",
        "  agent_optimization_space",
        "    target_attributes           default: instructions",
        "    model_search_space",
        "prompt_optimization             one-shot rewrite, no comparative evaluation",
        "",
        "result: baseline_score, candidate_summary, token_usage[], run_duration_ms",
    ], title="Configuration outline (key names from the REST reference)", theme="violet", src=src("rest"))
    cb.place(cv, 0, t.bottom + 28)
    rx = LW + G
    n1 = Note(S(2), "The eval.yaml documentation says max_candidates defaults to 5; the REST schema defaults candidate_search_configuration.max_candidates to 1. Set it explicitly "
                    "whichever surface you use.", kind="warn", title="Docs disagree: default candidates", src=src("tg", "rest"))
    n1.place(cv, rx, top)
    n2 = Note(S(2), "Only the Agents PATCH, sessions, files, invocations, voice, Microsoft 365 publishing, routines and optimization-job create pages were read in detail for this set; "
                    "the candidate and estimate operations above are named from the operation list, so open the REST reference before you build on them.",
              kind="quote", title="What was and was not read", src=src("rest"))
    n2.place(cv, rx, n1.bottom + 24)
    return max(cb.bottom, n2.bottom)


# ================================================================================================ band 6: wizard
def band_wizard(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Prompt agents: the portal wizard",
             "Agents, your agent, Optimize tab, Create optimization run. Not for agents that use the Microsoft Copilot harness; no code changes are required.")
    top = y
    gap = 64
    bw = (W - 5 * gap) / 6
    flow = [
        ("1  Open Optimize", "Agents > your agent > Optimize tab > Create optimization run", "agent"),
        ("2  Target", "baseline version, optimization model, max candidates, evaluation model, Compare across models", "gear"),
        ("3  Dataset", "generate from traces, pick a registered dataset or upload JSONL", "storage"),
        ("4  Criteria", "built-in, custom or rubric evaluators", "metrics"),
        ("5  Review and submit", "the cost estimate: minimum, estimated, maximum", "cost-management"),
        ("6  Compare and promote", "scores, before and after instructions, token usage; Promote candidate = a new version", "versions"),
    ]
    boxes = [Box(bw, lab, sub=sub, theme="violet", h=200, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for lab, sub, ic in flow]
    row(cv, 0, top, boxes, gap=gap)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#6741d9")
    y2 = boxes[0].bottom + 30
    n1 = Note(S(2), "Prompt-agent function tools run on the client, so the optimizer can improve their and their parameters' descriptions but cannot evaluate their execution during tool-description "
                    "optimization.", kind="info", title="Client-side tools", src=src("ovo"))
    n2 = Note(S(2), "Instructions, function-tool descriptions and the model are the three prompt-agent targets. Skills are hosted-only. Apply updates the local service's model, instructions and "
                    "matching function-tool descriptions; it does not add unmatched function tools.", kind="info", title="What the wizard can change", src=src("ovo", "tg"))
    n3 = Note(S(2), "After promoting, set the new version active if the agent endpoint is pinned: the stable endpoint keeps serving the pinned version until you move the selector.", kind="tip",
              title="Promote is not rollout", src=src("qp"))
    row(cv, 0, y2, [n1, n2, n3], gap=G)
    return y2 + max(n1.h, n2.h, n3.h)


# ================================================================================================ band 7: costs
def band_costs(cv: Canvas, y: float) -> float:
    y = head(cv, y, "7  Costs and token usage",
             "Cost is model tokens spent in three kinds of call: your agent, an eval model that judges and an optimization model that reflects. Only prompt-agent portal runs get a pre-run estimate; every run gets measured usage afterwards.")
    top = y
    cf = ChipFlow([Chip("Minimum", theme="green", size=20), Chip("Estimated", theme="yellow", size=20), Chip("Maximum (not a spending cap)", theme="red", size=20)], S(2), gap=14)
    cv.text(0, top, "Pre-run estimate (prompt agents, portal)", size=22, color=THEMES["yellow"].deep)
    cf.place(cv, 0, top + 40)
    c1 = card(S(2), "What drives the estimate", [
        "Max candidates, plus one for the baseline evaluation",
        "Dataset rows and the number of evaluators",
        "Optimization behavior: reflection steps and early stopping",
        "The models you pick",
    ], theme="yellow", icon="cost-management", src=src("costs"))
    c1.place(cv, 0, cf.y + cf.h + 22)
    t1 = Table([("Call", 260), ("Input tokens", 450), ("Output tokens", 458)], [
        [ct("Agent call", "green"), "2,000", "400"], [ct("Judge call", "violet"), "3,000", "120"], [ct("Reflection call", "orange"), "6,000", "2,000"],
    ], w=S(2), theme="yellow", size=15, head_size=16, title="Static token assumptions per call", title_size=22)
    t1.place(cv, X(2), top)
    ex = card(S(2), "Worked example from the page", [
        "2 candidates x 20 rows x 2 evaluators",
        "Agent calls: (2 candidates + 1 baseline) x 20 rows = 60",
        "Judge calls: 60 x 2 evaluators = 120",
        "Reflection calls: about 12 - usually the largest cost",
    ], theme="yellow", icon="metrics", src=src("costs"))
    ex.place(cv, X(2), t1.bottom + 24)
    t2 = Card(S(2), "Post-run token usage (both agent kinds)", [
        "One table, one row per phase and model",
        "Columns: phase, model, input tokens, output tokens, total tokens, estimated cost",
        "Excludes charges from any external tools your agent called",
    ], theme="gray", icon="log-analytics", src=src("costs"))
    t2.place(cv, 2 * (S(2) + G) - 0, top)
    n = Note(S(2), "The estimate uses static token assumptions per call, and the maximum is not a spending cap. Measured usage is shown after the run for both agent kinds and "
                   "excludes charges from external tools your agent called.", kind="warn", title="Estimate is not a quote", src=src("costs"))
    n.place(cv, 2 * (S(2) + G), t2.bottom + 24)
    return max(c1.bottom, ex.bottom, n.bottom)


# ================================================================================================ band 8: Prompt Optimizer
def band_prompt(cv: Canvas, y: float) -> float:
    y = head(cv, y, "8  Prompt Optimizer: a different, smaller tool",
             "It rewrites the text of an agent's instructions in the portal playground. There is no dataset, no evaluation and no candidate ranking: only best-practice restructuring with reasons.")
    top = y
    gap = 64
    bw = (W - 4 * gap) / 5
    flow = [
        ("1  Open it", "Build > Agents > your agent > Instructions: the pencil-and-sparkle icon (New Foundry toggle on)", "agent"),
        ("2  Describe or paste", "a description for a new agent, or the existing instructions; optionally a suggestion such as 'make the tone more conversational'", "files"),
        ("3  Optimize", "an LLM applies prompt-engineering best practices; changed paragraphs are highlighted in purple", "gear"),
        ("4  Read the reasons", "a chat-bubble icon per changed paragraph, or Show all reasoning; iterate with new suggestions on the latest text", "learn"),
        ("5  Use prompt", "applies the result to the Instructions field - do this before you close the dialog", "versions"),
    ]
    boxes = [Box(bw, lab, sub=sub, theme="violet" if i != 4 else "red", h=200, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for i, (lab, sub, ic) in enumerate(flow)]
    row(cv, 0, top, boxes, gap=gap)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#6741d9")
    y2 = boxes[0].bottom + 30
    c1 = card(S(2), "Limitations", [
        "Text-based instructions only: not tool definitions or knowledge sources",
        "Results are ephemeral: nothing is stored across sessions",
        "No version history: copy your original instructions first if you may want them back",
        "Needs a prompt agent or a workflow agent and a model deployment in a supported region",
        "In an unsupported region the Optimize button does not appear",
    ], theme="red", icon="preview-features", src=src("po"))
    c2 = card(S(2), "Best practices from the page", [
        "Start simple, then refine with specific suggestions - 'add error handling for invalid dates' beats 'make it better'",
        "Review the reasoning before you accept a change",
        "Test in the playground after applying; reloading before you save the agent restores the previous instructions",
        "Run a full evaluation on your own dataset afterwards: the optimizer applies general practices, your data shows whether they help",
    ], theme="green", icon="learn", src=src("po"))
    with cv.panel(X(4), y2, title="15 supported regions (as of 2026-11-03)", sub="the project's region decides availability", theme="indigo", style="dotted", pad=18, title_size=22,
                  sub_size=14, w=S(2)) as rp:
        regs = ["Central US", "East US 2", "France Central", "Germany West Central", "Italy North", "Japan West", "North Central US", "Poland Central", "Spain Central",
                "Sweden Central", "Switzerland West", "UAE North", "West US", "West US 2", "West US 3"]
        ChipFlow([Chip(r_, theme="indigo", size=14, fill="soft") for r_ in regs], S(2) - 36, gap=8).place(cv, rp.ix, rp.iy)
    row(cv, 0, y2, [c1, c2], gap=G)
    # place the regions panel at the same top as the cards (c1/c2 occupy X(0)..X(4)-G)
    return max(c1.bottom, c2.bottom, rp.bottom)


# ================================================================================================ band 9: CI/CD template
def band_cicd(cv: Canvas, y: float) -> float:
    y = head(cv, y, "9  Hosted-agent CI/CD template: deploy on push and smoke-test the agent",
             "A quickstart template: .github/workflows/hosted-agent-cd.yml runs on a push to main (or by hand), deploys the updated code to existing infrastructure and invokes the agent once.")
    top = y
    gap = 64
    bw = (S(4) - 3 * gap) / 4
    flow = [
        ("Trigger", "push to main, or workflow_dispatch", "github", "gray"),
        ("Sign in with OIDC", "GitHub OIDC with an Entra app and a federated credential", "managed-identity", "red"),
        ("Deploy the code", "the updated hosted-agent code goes to the existing project", "builds", "green"),
        ("Smoke test", "invoke the agent with a test prompt and check for a non-empty response", "agent", "violet"),
    ]
    boxes = [Box(bw, f"{i + 1}  {lab}", sub=sub, theme=th, h=200, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for i, (lab, sub, ic, th) in enumerate(flow)]
    row(cv, 0, top, boxes, gap=gap)
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, sw=3, color="#343a40")
    y2 = boxes[0].bottom + 28
    cv.text(0, y2, "Repository variables", size=18, color=MUTED)
    cf = ChipFlow([Chip(v, theme="gray", size=14, fill="soft") for v in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID", "AZURE_LOCATION", "FOUNDRY_PROJECT_ENDPOINT",
                                                                      "AZURE_AI_PROJECT_ID", "FOUNDRY_MODEL_NAME")], S(4), gap=8)
    cf.place(cv, 0, y2 + 30)
    cv.text(0, cf.y + cf.h + 14, "Placeholders to set: AGENT_PROJECT_DIR, AZD_ENV_NAME (staging) and AGENT_TEST_PROMPT.", size=15, color=INK)
    left_bottom = cf.y + cf.h + 40
    rx = S(4) + G
    c1 = card(S(2), "Before you use it", [
        "Run azd provision and azd deploy once first: the template deploys to existing infrastructure",
        "Infrastructure provisioned with Terraform: start from the CI/CD how-to instead",
        "The workflow identity needs Foundry User and Contributor on the target project for a code deploy; a container deploy needs extra registry permissions",
        "The Microsoft Foundry skill can tailor the template to your repo",
    ], theme="yellow", icon="devops", src=src("cdq", "cicd"))
    c1.place(cv, rx, top)
    return max(left_bottom, c1.bottom)


# ================================================================================================ band 10: gotchas
def band_gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "10  Docs disagree and what is not said - as of 2026-11-03",
             "Where two Learn pages (or Learn and a blog) give different answers, both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 1100), ("Another source says", 1100), ("How to read it", 1100)], [
        [ct("Default candidates", "orange"), "eval.yaml documentation: max_candidates defaults to 5", "REST schema: candidate_search_configuration.max_candidates defaults to 1", "Set it explicitly"],
        [ct("Optimizer scope", "orange"), "Lifecycle page: optimize hosted agents", "Overview and the prompt-agent quickstart: prompt agents and hosted agents", "Read the overview as current"],
        [ct("Goal values", "orange"), "REST agent_optimization goal enum lists only improve_quality", "The overview names four targets (instructions, skills, tool descriptions, model)",
         "Goal and target_attributes are separate fields"],
    ], w=W, theme="orange", size=14, head_size=15, title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    q = Note(W, "Not stated on the pages read for this canvas: a price list for optimizer runs beyond the static token assumptions, how reflection steps are counted for early stopping, "
                "a maximum dataset size for the optimizer, and the status label (Preview or GA) of the Prompt Optimizer page. Nothing on this canvas fills those gaps.",
             kind="quote", title="What the docs do not say", src=src("costs", "po"))
    q.place(cv, 0, t.bottom + 30)
    return q.bottom


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "The agent optimizer in depth",
        "Part 2 of 'Agent lifecycle and the optimizer'  |  optimizer-ready files, datasets, run and apply, REST, costs, Prompt Optimizer, CI/CD template  |  Preview, as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Evaluation and optimizer", "violet"), ("Models and tools", "orange"), ("Identity and security", "red"),
                           ("Networking", "indigo"), ("CI/CD and cost", "yellow"), ("State and data", "cyan"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Agent lifecycle and the optimizer: build, test, ship, improve", "Hosted agents: deploy and operate", "AgentOps lifecycle", "Evaluation in depth",
                "Prompt agents in depth", "Microsoft Foundry Cost Structure"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_paths(cv, y) + 56
    y = band_ready(cv, y) + 56
    y = band_data(cv, y) + 56
    y = band_run(cv, y) + 56
    y = band_rest(cv, y) + 56
    y = band_wizard(cv, y) + 56
    y = band_costs(cv, y) + 56
    y = band_prompt(cv, y) + 56
    y = band_cicd(cv, y) + 56
    y = band_gotchas(cv, y) + 56
    sources(cv, 0, y, [
        ("Agent optimizer overview", U["ovo"][1]), ("Agent optimizer costs and token usage", U["costs"][1]), ("Make your agent optimizer-ready", U["ready"][1]),
        ("Create an optimizer dataset and evaluators", U["ds"][1]), ("Optimize agent instructions, skills, tools and models", U["tg"][1]),
        ("Quickstart: optimize a hosted agent", U["qh"][1]), ("Quickstart: optimize a prompt agent", U["qp"][1]), ("Optimize agent prompts with Prompt Optimizer", U["po"][1]),
        ("Set up CI/CD for hosted agents with azd", U["cicd"][1]), ("Quickstart: set up CI/CD for a hosted agent", U["cdq"][1]), ("REST: create an agent optimization job", U["rest"][1]),
        ("Agent development lifecycle", U["life"][1]), ("Evaluate agents with the Azure Developer CLI", U["azdeval"][1]), ("Set the Foundry project context for azd commands", U["ctx"][1]),
    ], w=W, cols=4)
