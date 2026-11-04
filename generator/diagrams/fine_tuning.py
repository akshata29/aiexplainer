"""Fine-tuning in Microsoft Foundry: data -> job -> checkpoints -> deploy -> monitor, with methods, training types, cost and safety gates."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="fine-tuning", title="Fine-tuning: from data to a deployed model", section="2", group="Models", order=24,
    description="End-to-end fine-tuning pipeline with quality gates: Managed vs Programmed Training, SFT/DPO/RFT, training types, "
                "supported models, hosting, cost management and safety evaluation.",
    tags=["fine-tuning", "sft", "dpo", "rft", "lora", "models"],
)

W, G, C = 3000, 48, 460          # canvas width, standard gap, 1-column card width (6-column grid)
MUTED_ = "#495057"
BLUE_DEEP = get_theme("blue").deep


def span(n: int) -> float:
    return n * C + (n - 1) * G


def colx(i: int) -> float:
    return i * (C + G)


def L(label: str, path: str):
    return (label, learn(path))


S_OVERVIEW = L("Fine-tuning in Microsoft Foundry", "fine-tuning/overview")
S_SFT = L("Supervised fine-tuning", "openai/how-to/fine-tuning")
S_DPO = L("Direct preference optimization", "openai/how-to/fine-tuning-direct-preference-optimization")
S_RFT = L("Reinforcement fine-tuning", "openai/how-to/reinforcement-fine-tuning")
S_VISION = L("Vision fine-tuning", "openai/how-to/fine-tuning-vision")
S_TOOLS = L("Improve tool calling with fine-tuning", "openai/how-to/fine-tuning-functions")
S_DATAGEN = L("Generate synthetic data (preview)", "fine-tuning/data-generation")
S_PROG = L("What is Programmed Training (preview)?", "fine-tuning/programmed-training/overview")
S_DEPLOY = L("Deploy fine-tuned models", "fine-tuning/deploy-fine-tuned-models")
S_COST = L("Manage fine-tuning costs", "fine-tuning/cost-management")
S_SAFETY = L("Safety evaluation for fine-tuning (preview)", "openai/how-to/fine-tuning-safety-evaluation")
S_HEALTH = L("Customize a premium healthcare AI model", "how-to/healthcare-ai/fine-tune-premium-healthcare-models")
S_QUOTAS = L("Azure OpenAI quotas and limits", "openai/quotas-limits")


# ---------------------------------------------------------------------------------------------- helpers
def sec(cv, y, title, sub=None):
    """Section header across the full width; returns the y where content starts."""
    _, hb = section_header(cv, 0, y, title, sub=sub, size=32, w=W)
    return hb + 22


def tile(cv, x, y, w, h, num, label, sub, th_name):
    """Big-number summary tile."""
    th = get_theme(th_name)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    nw, nh = text_size(num, 72)
    cv.text(x + 26, y + (h - nh) / 2, num, size=72, color=th.deep)
    tx = x + 26 + nw + 24
    avail = (w - (tx - x) - 18) * 0.965
    lab = wrap_text(label, avail, 22)
    sl = wrap_text(sub, avail, 15)
    lr = metrics.line_ratio()
    total = len(lab) * 22 * lr + 4 + len(sl) * 15 * lr
    ty = y + (h - total) / 2
    cv.text(tx, ty, "\n".join(lab), size=22, color=th.deep)
    cv.text(tx, ty + len(lab) * 22 * lr + 4, "\n".join(sl), size=15, color=INK)
    cv.register("tile:" + label, x, y, w, h)


def stack_h(blocks, gap):
    return sum(b.h for b in blocks) + gap * (len(blocks) - 1)


def station(cv, x, y, w, H, n, title, th_name, blocks, gap=16, pad=18):
    """Numbered pipeline station: a solid soft panel with a header and stacked blocks."""
    lr = metrics.line_ratio()
    t_lines = wrap_text(title, (w - 2 * pad - 50) * 0.965, 24)
    head_h = max(40, len(t_lines) * 24 * lr) + 14
    with cv.panel(x, y, theme=th_name, style="solid", fill="soft", pad=pad, w=w, h=H, sw=3) as p:
        numbered(cv, p.ix + 18, p.iy + 20, n, theme=th_name, d=38, size=21)
        cv.text(p.ix + 50, p.iy + 20 - len(t_lines) * 24 * lr / 2, "\n".join(t_lines), size=24,
                color=get_theme(th_name).deep)
        cy = p.iy + head_h
        for b in blocks:
            b.place(cv, p.ix, cy)
            cy += b.h + gap
    return p


def code_box(cv, x, y, w, title, lines, th_name="blue", size=15, h=None):
    th = get_theme(th_name)
    lh = size * metrics.line_ratio(metrics.MONO)
    need = 14 + 26 + len(lines) * lh + 16
    H = max(need, h or 0)
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 16, y + 10, title, size=18, color=th.deep)
    cv.text(x + 16, y + 42, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    cv.register("code:" + title, x, y, w, H)
    return H


def mk(ok: bool):
    return {"text": CHECK, "theme": "green"} if ok else {"text": DASH}


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Fine-tuning in Microsoft Foundry",
        "From data to a deployed, monitored model - methods, training types, hosting, cost and safety gates (facts as of 2026-11-03)",
        w=W)
    y = bottom + 40

    # ======================================================================= summary tiles
    tiles = [
        ("2", "training approaches", "Managed Training, or Programmed Training (preview)", "blue"),
        ("3", "managed methods", "SFT, DPO and RFT - distillation = SFT on teacher data", "blue"),
        ("4", "training types", "Standard, Data zone (US only), Global, Developer", "yellow"),
        ("3", "ways to serve", "Serverless, Managed compute (preview), Fireworks (preview)", "blue"),
        ("2", "safety gates (preview)", "Data check before training, model check after", "pink"),
        ("3", "cost buckets", "Train, host, infer - the hosting fee accrues even when idle", "yellow"),
    ]
    for i, (n, lab, sub, th) in enumerate(tiles):
        tile(cv, colx(i), y, C, 118, n, lab, sub, th)
    y += 118 + 54

    # ======================================================================= HERO: assembly line
    _, hb = section_header(cv, 0, y, "The assembly line: from data to a deployed model, with quality gates",
                           sub="Follow stations 1 to 6 left to right. The dashed arrow is the iterate loop. Orange pills mark preview features - re-check their status before you rely on them.",
                           size=34, w=W)
    lg = legend(cv, 0, hb + 16, [("Data", "cyan"), ("Training and serving", "blue"), ("Billed / cost", "yellow"),
                                  ("Safety gates", "pink"), ("Evaluation", "violet")])
    draw_badge(cv, lg.right + 24, hb + 14, "preview")
    cv.text(lg.right + 112, hb + 16, "= preview feature", size=15)
    y = hb + 16 + 22 + 34

    SW, SG, IW = 410, 108, 374
    sx = [i * (SW + SG) for i in range(6)]

    s1 = [
        Card(IW, "Real data", [
            "JSONL: a training file + a validation file",
            "Keep a separate test set; never train on it",
            "Upload with purpose=fine-tune",
            "Distillation = SFT on teacher-generated examples",
        ], theme="cyan", icon="files"),
        Card(IW, "Synthetic data", [
            "Portal: Data > Data Generation",
            "Simple Q&A or Tool use generators",
            "50-1,000 samples, optional 80/20 split",
            "Combine with real data; validate first",
        ], theme="cyan", badge="preview"),
        Card(IW, "Format follows the method", [
            "SFT: chat messages (system, user, assistant)",
            "DPO: input + preferred + non-preferred output",
            "RFT: user message + the fields your grader needs",
        ], theme="cyan"),
    ]
    s2 = [
        Card(IW, "Managed Training", [
            "Submit data + settings; Foundry runs the job",
            "Model-specific SFT, DPO or RFT",
        ], theme="blue", icon="ml"),
        Card(IW, "Programmed Training", [
            "Your Python loop; Foundry runs sampling and LoRA updates",
            "Needs explicit access approval",
        ], theme="blue", badge="preview", fill="cross"),
        Card(IW, "Pick a training type", [
            "Standard: your region, residency kept",
            "Data zone: US zone only",
            "Global: cheaper, no data residency",
            "Developer: cheapest, preemptible",
        ], theme="yellow", icon="quotas"),
    ]
    s3 = [
        Box(IW, "Create the job", sub="portal, API or azd", theme="blue", h=62, size=19),
        Box(IW, "Queue", sub="not billed", theme="gray", h=62, size=19),
        Box(IW, "Gate 1: data safety check", sub="preview. Harmful data: job fails, no charge", theme="pink", h=76, size=18),
        Box(IW, "Train", sub="billed: tokens x epochs (SFT, DPO) or hours (RFT)", theme="yellow", h=76, size=19),
        Box(IW, "Gate 2: model safety check", sub="preview. Fail: not deployable, run not charged", theme="pink", h=76, size=18),
    ]
    s4 = [
        Card(IW, "Checkpoints", [
            "Appear as training runs (none while queued)",
            "Compare on held-out tasks; the latest isn't automatically best",
            "RFT: a per-job cost limit pauses the job and creates a deployable checkpoint",
        ], theme="violet", icon="versions"),
        Card(IW, "Metrics", [
            "SFT: train and validation loss, token accuracy",
            "DPO: judge on held-out preference examples",
            "RFT: grader reward; test graders against adversarial answers",
            "Events, checkpoints and a results CSV via the API",
        ], theme="violet", icon="metrics"),
    ]
    s5 = [
        Box(IW, "Serverless", sub="Foundry hosts it. Pick a deployment type and capacity within quota; monitor on the Models page", theme="blue", h=100, size=20),
        Box(IW, "Managed compute", sub="LoRA adapter on a matching, LoRA-enabled base deployment; multi-LoRA shares compute", theme="blue", h=110, size=20),
        Box(IW, "Fireworks on Foundry", sub="needs Fireworks.EnableDeploy; one adapter merged into a full-weight copy of the base model", theme="blue", h=110, size=20),
        Note(IW, "Foundry Owner deploys. Max 10 fine-tuned deployments per resource. Not supported for fine-tuned models: Batch, Instant access.",
             kind="info", size=14),
    ]
    s6 = [
        Card(IW, "Evaluate", [
            "Playground: pick the fine-tuned deployment, not the base",
            "Portal evaluations or the cloud evaluation SDK",
            "Compare with your baseline on held-out data",
        ], theme="violet", icon="app-insights"),
        Card(IW, "Monitor cost", [
            "Training + hosting + inference",
            "Hosting fee accrues even at zero traffic",
            "Delete idle deployments (cancelling training doesn't)",
        ], theme="yellow", icon="cost-management"),
        Note(IW, "Fine-tuned models aren't auto-upgraded; training and deployment retire on separate clocks.", kind="warn", size=14),
    ]
    stations = [
        (1, "Data", "cyan", s1, 16), (2, "Choose the lane", "blue", s2, 16), (3, "Training job", "blue", s3, 30),
        (4, "Checkpoints and metrics", "violet", s4, 16), (5, "Deploy", "blue", s5, 16),
        (6, "Evaluate, monitor, iterate", "violet", s6, 16),
    ]
    H = max(stack_h(b, g) for _, _, _, b, g in stations) + 18 * 2 + 54
    panels = [station(cv, sx[i], y, SW, H, n, title, th, blocks, gap=gap)
              for i, (n, title, th, blocks, gap) in enumerate(stations)]
    labels = ["dataset", "job settings", "events + checkpoints", "deployable model", "endpoint"]
    ya = y + 18 + 20
    for i in range(5):
        arrow(cv, [(panels[i].right + 6, ya), (panels[i + 1].x - 6, ya)], end_head="arrow", sw=3, label=labels[i],
              label_size=14, label_wrap=88, label_dy=-2)
    for a, b in zip(s3, s3[1:]):
        arrow(cv, [(a.x + a.w / 2, a.y + a.h + 3), (b.x + b.w / 2, b.y - 3)], end_head="arrow", sw=2)
    for a in s5[:2]:
        cv.text(a.x + a.w / 2 - 8, a.y + a.h + 0, "or", size=14, color=MUTED_)
    for b in (s5[1], s5[2], s3[2], s3[4]):
        draw_badge(cv, b.x + b.w - 78, b.y - 11, "preview")
    yb = y + H
    arrow(cv, [(panels[5].cx, yb + 5), (panels[5].cx, yb + 46), (panels[0].cx, yb + 46), (panels[0].cx, yb + 6)],
          dash="dashed", color="#1971c2", sw=3, end_head="arrow",
          label="iterate or retire: new data, a different method or a new base model", label_size=16, label_bg=True)
    y = yb + 46 + 56

    # ======================================================================= 2a  why fine-tune + challenges
    y = sec(cv, y, "Before you start: why fine-tune, and what can go wrong")
    why = Card(span(2), "Why fine-tune?", [
        "= Adapts a pretrained model through extra training on task data. It adjusts the model's weights instead of adding examples to every prompt.",
        "# Fine-tuning can help you",
        "Improve accuracy and relevance with more examples than fit in a prompt",
        "Reduce prompt overhead: fewer in-prompt examples, lower token cost and latency",
        "Align style and structure: tone, format or schema",
        "Improve tool selection and argument accuracy",
        "Use retrieved context better: prioritise what is relevant, ignore the rest",
        "Specialise a smaller model with teacher-generated examples",
        "! Benefits aren't guaranteed: compare with your baseline on held-out data",
        "! Adds training and hosting cost; doesn't replace retrieval for current facts or application-level safety",
    ], theme="blue", icon="ml", src=[S_OVERVIEW])
    chal = Table([("Challenge", 350), "How to address it"], [
        ["Data quality and coverage", "Use accurate, consistent, representative examples; inspect for missing scenarios, duplicates, bias and sensitive information before upload"],
        ["Overfitting and evaluation leakage", "Separate training, validation and final test data; compare checkpoints on held-out tasks, not just training loss"],
        ["Misleading reward signals (RFT)", "Test graders on correct, incorrect and adversarial answers; a rising reward doesn't prove a better model if it exploits the grader"],
        ["Experimentation and cost", "Budget for repeated runs, grading, evaluation, hosting and inference; stop experiments that don't improve the target metric"],
        ["Model and serving compatibility", "Confirm method, tier, version and deployment eligibility first; an adapter isn't interchangeable across similarly named base models"],
        ["Maintenance", "Reassess as task data changes or a base model nears retirement; retraining and redeployment can be necessary"],
        ["Safety and governance", "Review data handling and managed safety evaluation; keep application-level safety controls; evaluate the final serving runtime"],
        ["Programmed Training runtime", "You maintain the driver, environments, tokenization, checkpoints and recovery; in-session sampling isn't proof of production serving behavior"],
    ], w=span(4), theme="orange", size=15, head_size=16, first_col_theme="orange", title="Challenges and limitations (from the overview page)",
        title_size=22)
    why.place(cv, 0, y)
    chal.place(cv, span(2) + G, y)
    y = max(why.bottom, chal.bottom) + 52

    # ======================================================================= 2b  managed vs programmed + RL loop
    y = sec(cv, y, "Two training approaches on Foundry-managed infrastructure (no GPUs to provision)")
    appr = Table([("", 150), "Managed Training", "Programmed Training (preview)"], [
        ["How it works", "Submit data and settings; Foundry runs the training job", "Write a Python loop; Foundry executes training and sampling operations (LoRA updates on serverless GPUs)"],
        ["Best for", "Beginners and AI engineers who prefer predefined workflows", "Experienced ML practitioners building custom training workflows"],
        ["You control", "Data, supported hyperparameters and RFT graders", "Losses, rewards, rollouts, gradient accumulation, updates and checkpoints"],
        ["Methods", "Model-specific SFT, DPO and RFT; distillation through teacher-generated SFT data", "Recipes for SFT, reinforcement learning, preference learning, distillation and custom losses"],
        ["Example uses", "Distill a larger model, learn from support conversations, improve responses with a grader", "Collect tool-use rollouts, apply custom rewards, change update and evaluation behavior"],
        ["Where the driver runs", "n/a: Foundry runs the job", "On a CPU or your own machine"],
    ], w=span(3), theme="blue", size=15, head_size=17, first_col_theme="blue", title="Managed vs Programmed Training", title_size=22)
    appr.place(cv, 0, y)

    with cv.panel(colx(3), y, title="Programmed Training loop (RL recipe)", sub="the numbered steps repeat; primitives named under each step", theme="blue",
                  style="dashed", fill="soft", pad=24, w=span(3), title_size=24) as rl:
        bw, gx = 300, 76
        by1 = rl.iy + 6
        by2 = by1 + 96 + 66
        steps1 = [("Save sampler weights", "save_weights_for_sampler"), ("Sample rollouts", "sample"),
                  ("Score with your reward", "your code"), ("Advantages", "reward minus the prompt-group mean")]
        steps2 = [("Token masks", "Datum: tokenised batch + masks"), ("Accumulate gradients", "forward_backward"),
                  ("Update the adapter", "optim_step (Adam params)"), ("Refresh weights, evaluate, checkpoint", "then loop again")]
        row1, row2 = [], []
        for i, (lab, sub) in enumerate(steps1):
            row1.append(Box(bw, lab, sub=sub, theme="orange" if i >= 2 else "blue", h=96, size=18, sub_size=14).place(cv, rl.ix + i * (bw + gx), by1))
        for i, (lab, sub) in enumerate(steps2):
            row2.append(Box(bw, lab, sub=sub, theme="violet" if i == 3 else "blue", h=96, size=18, sub_size=14).place(cv, rl.ix + (3 - i) * (bw + gx), by2))
        for i, b in enumerate(row1 + row2, 1):
            numbered(cv, b.x + 4, b.y + 4, i, theme="blue", d=30, size=17)
        for a, b in zip(row1, row1[1:]):
            connect(cv, a, b, sw=2)
        connect(cv, row1[3], row2[0], sw=2)
        for a, b in zip(row2, row2[1:]):
            connect(cv, a, b, sw=2)
        connect(cv, row2[3], row1[0], dash="dashed", color="#1971c2", sw=3, label="repeat", label_size=15)
        cv.text(rl.ix, by2 + 96 + 18, "Orange = your code (reward, advantages). Violet = checkpoint and evaluation. Blue = Foundry primitives.",
                size=14, color=MUTED_)
    y = max(appr.bottom, rl.bottom) + 36

    prim = Card(span(2), "Programmed Training primitives (preview)", [
        "FineTuningSession.create starts a session with a LoRA adapter; create_from_checkpoint resumes one",
        "Datum is a tokenised batch with masks; sample, forward and forward_backward (accumulates gradients)",
        "optim_step applies the update (Adam parameters)",
        "save_weights_for_sampler refreshes the sampler; save_weights keeps adapter + optimizer state",
        "Losses: cross_entropy, importance_sampling, ppo",
        "Advantages = reward minus the prompt-group mean",
    ], theme="blue", icon="python", badge="preview", src=[S_PROG])
    prog2 = Card(span(2), "Models, regions and billing (preview)", [
        "Models: Muse-Glimmer-30B, Qwen3.6-35B-A3B, Qwen3.8-27B (preview), gpt-oss-20b, gpt-oss-120b (preview)",
        "Global regions: 11 of the Global training regions (see the region map below)",
        "Billing: prefill + cached prefill + sampling + training tokens, cumulative across the whole run",
        "Managed Training job discounts and RFT spending limits don't define Programmed Training pricing or limits",
    ], theme="blue", badge="preview", src=[S_PROG, S_COST])
    prog3 = Card(span(2), "Access and your responsibilities (preview)", [
        "Needs explicit access approval: request it via the preview sign-up form (aka.ms/foundry-interactive-training-signup) and wait before creating training sessions",
        "New to customization? Start with Managed Training",
        "You maintain the driver, environments, tokenization, checkpoints and recovery logic",
        "! In-session sampling isn't proof of production serving behavior - evaluate the deployed model",
    ], theme="violet", badge="preview", src=[S_PROG])
    row(cv, 0, y, [prim, prog2, prog3], gap=G)
    y = max(prim.bottom, prog2.bottom, prog3.bottom) + 60

    # ======================================================================= 3  methods and data formats
    y = sec(cv, y, "Methods and data formats (Managed Training)",
            sub="Pick the method by the signal you have: demonstrations, preferences or a grader.")
    m_sft = Card(C, "Supervised (SFT)", [
        "Signal: prompts + desired responses; use when you can demonstrate the behavior",
        "training.jsonl + validation.jsonl; one conversation per line (system, user, assistant messages)",
        "Hyperparameters: batch_size, learning_rate_multiplier, n_epochs; each a number or auto",
        "Metrics: train_loss, full_valid_loss, train_mean_token_accuracy, full_valid_mean_token_accuracy",
        "Keep validation and test data out of training; check per-model file-size and minimum-example rules",
    ], theme="blue", icon="ml", src=[S_SFT])
    m_dpo = Card(C, "Preference (DPO)", [
        "Signal: preferred vs rejected responses to the same input; use when quality is tone or completeness",
        "Each line: input (messages, optional tools + parallel_tool_calls) + preferred_output + non_preferred_output",
        "Job method type dpo, plus method.dpo.hyperparameters",
        "Can follow SFT: pass the fine-tuned model identifier, not the deployment name (supported models)",
        "Evaluate on held-out preference examples, not token accuracy",
    ], theme="blue", icon="branch", src=[S_DPO])
    m_rft = Card(C, "Reinforcement (RFT)", [
        "Signal: prompts + a grader that scores outputs; use when many answers are possible but quality is scorable",
        "Examples: messages ending in a user message + fields the grader needs (e.g. reference_answer)",
        "Template refs: {{sample.output_text}}, {{sample.output_json}}, {{item.<field>}}",
        "Test graders: client.fine_tuning.alpha.graders.validate and .run",
        "A model grader may need its own deployment",
        "! GPT-5 RFT needs an invitation (account team)",
    ], theme="blue", icon="metrics", src=[S_RFT])
    m_vis = Card(C, "Vision fine-tuning", [
        "Only gpt-4o (2024-08-06) and gpt-4.1 (2025-04-14)",
        "Up to 50,000 image examples per file, 64 images per example, 10 MB each",
        "JPEG, PNG or WEBP; RGB or RGBA; public URL or base64 data URI; no images in assistant output",
        "detail: low (downscaled to 512x512, cheaper), high or auto; at least 10 examples",
        "People, faces and CAPTCHAs are screened out (face detection only)",
        "! Not supported in Japan East",
    ], theme="blue", icon="vision", src=[S_VISION])
    m_tool = Card(C, "Tool-calling fine-tuning", [
        "Use tools; the older functions and function_call parameters are deprecated",
        "Assistant tool_calls, an optional tool response, then a final assistant message",
        "At least 10 examples",
        "Cost lever: after tuning, omit function descriptions, properties or whole definitions",
        "Quality: keep function definitions identical between training and inference",
    ], theme="blue", icon="functions", src=[S_TOOLS])
    m_syn = Card(C, "Synthetic data generation", [
        "Portal: Data > Data Generation",
        "Simple Q&A: PDF, Markdown or text under 20 MB; long or short answers",
        "Tool use: OpenAPI 3.0.x or 3.1.x JSON under 20 MB -> multi-turn tool-call conversations",
        "Exactly one reference file; 50 to 1,000 samples; optional 80/20 train/validation split",
        "Generator model is auto-deployed if absent (Foundry Owner needed); roles Foundry User or Project Manager",
        "Output JSONL via Use this dataset; combine with real data and validate",
    ], theme="cyan", icon="data-factory", badge="preview", src=[S_DATAGEN])
    _, mb = row(cv, 0, y, [m_sft, m_dpo, m_rft, m_vis, m_tool, m_syn], gap=G)
    y = mb + 44

    graders = Table([("Grader (RFT)", 190), ("What it does", 380), "Options and notes"], [
        ["string_check", "String comparison against a reference", "ops: eq, ne, like, ilike"],
        ["text_similarity", "Similarity to a reference", "fuzzy_match, bleu, gleu, meteor, rouge_1 to rouge_5, rouge_l (cosine is for evaluations, not RFT)"],
        ["score_model", "A model grades with your rubric", "rubric, range, sampling_params; may need its own deployment"],
        ["python", "Your grade(sample, item) function", "Constrained runtime; no network access"],
        ["multi", "Combines named child graders", "calculate_output expression: + - * / ^ min max abs floor ceil exp sqrt log"],
    ], w=span(3), theme="blue", size=15, head_size=16, first_col_theme="blue", title="RFT grader types", title_size=22)
    graders.place(cv, 0, y)
    gnote = Note(span(3), "Rising reward is not proof of a better model. Test the grader against correct, incorrect and adversarial responses before you spend on a run.",
                 kind="gotcha", title="Graders can be gamed", size=15, src=[S_RFT])
    gnote.place(cv, 0, graders.bottom + 22)

    sx0 = colx(3)
    cv.text(sx0, y, "What one training line looks like (schematic)", size=22, color=BLUE_DEEP)
    cw2 = (span(3) - 24) / 2
    hh1 = 5 * 15 * metrics.line_ratio(metrics.MONO) + 68
    code_box(cv, sx0, y + 40, cw2, "SFT: one conversation", [
        '{"messages": [',
        '  {"role": "system", ...},',
        '  {"role": "user", ...},',
        '  {"role": "assistant", ...}',
        ']}'], h=hh1)
    code_box(cv, sx0 + cw2 + 24, y + 40, cw2, "DPO: a preference pair", [
        '{"input": {"messages": [...],',
        '           "tools": [...]},',
        ' "preferred_output": [...],',
        ' "non_preferred_output": [...]}'], h=hh1)
    code_box(cv, sx0, y + 40 + hh1 + 20, cw2, "RFT: prompt + grader fields", [
        '{"messages": [',
        '  {"role": "user", ...}],',
        ' "reference_answer": "..."}'], h=hh1 - 20)
    code_box(cv, sx0 + cw2 + 24, y + 40 + hh1 + 20, cw2, "Tool calling", [
        '{"messages": [',
        '  {"role": "assistant", "tool_calls": [...]},',
        '  {"role": "tool", ...},',
        '  {"role": "assistant", ...}],',
        ' "tools": [...]}'], h=hh1 - 20)
    y = max(gnote.bottom, y + 40 + hh1 + 20 + hh1 - 20) + 60

    # ======================================================================= 4  training / deployment types, models
    y = sec(cv, y, "Training types, deployment types and supported models",
            sub="Training types decide where a job runs; deployment types decide how the result is served. They are separate choices.")
    ttypes = Table([("Training type", 150), ("What it means", 520), ("Data residency", 170), "Good for"], [
        [("Standard", "blue"), "Trains in the current Foundry resource's region", "Guaranteed", "Workloads where data must stay in one region"],
        [("Data zone", "blue"), "Trains inside a supported data zone. Only the US data zone is supported today", "Kept inside the zone", "Workloads where data must stay in the zone"],
        [("Global", "yellow"), "More affordable per token: uses capacity beyond your region, data and weights are copied to the training region; faster queues. API: trainingType GlobalStandard", "None", "Residency isn't a restriction and you want faster queues"],
        [("Developer", "yellow"), "Significant savings from idle capacity. No latency or SLA; jobs may be preempted and resumed later; paused jobs aren't billed", "None", "Experimentation and price-sensitive workloads"],
    ], w=span(3), theme="yellow", size=15, head_size=16, title="Training types (where training runs)", title_size=22)
    dtypes = Table([("Deployment type", 190), "What it means for a fine-tuned model"], [
        [("Standard", "blue"), "Inference in the deployment's region; per-token billing plus the fine-tuned-model hourly hosting charge"],
        [("Data Zone Standard", "blue"), "Inference inside a supported data zone (US only); per-token billing"],
        [("Global Standard", "blue"), "Global capacity, per-token billing; custom weights may be stored temporarily outside the resource's geography"],
        [("Developer", "yellow"), "Global, per-token at Global Standard rates, no hourly hosting fee, no residency; evaluation only, lasts 24 hours, no availability SLA"],
        [("Provisioned Throughput", "blue"), "Regional capacity billed in PTUs for predictable throughput"],
        [("Global Provisioned", "blue"), "Global capacity with PTU billing, for imported custom models"],
    ], w=span(3), theme="blue", size=15, head_size=16, title="Deployment types (how the result is served)", title_size=22)
    ttypes.place(cv, 0, y)
    dtypes.place(cv, colx(3), y)
    tn = Note(span(3), "Global training can still serve on Standard where the model supports it. Global and Developer training don't guarantee regional data residency; Data zone covers the US zone only.",
              kind="gotcha", title="Training type is not deployment type", size=15, src=[S_OVERVIEW])
    tn.place(cv, 0, ttypes.bottom + 22)
    y = max(ttypes.bottom + 22 + tn.h, dtypes.bottom) + 52

    # heat map ---------------------------------------------------------------
    cols = [("Model (version)", 380), ("SFT", 76), ("DPO", 76), ("RFT", 76), ("Programmed (preview)", 120),
            ("Standard", 96), ("Data zone", 96), ("Global", 90), ("Developer", 100),
            ("Serverless", 100), ("Managed compute", 112), ("Fireworks", 100), ("Notes", 490)]
    T, F = True, False
    rows = [
        ["gpt-4o-mini (2024-07-18)", mk(T), mk(F), mk(F), mk(F), mk(T), mk(T), mk(T), mk(T), mk(T), mk(F), mk(F), "Developer deployment type not supported"],
        ["gpt-4o (2024-08-06)", mk(T), mk(T), mk(F), mk(F), mk(T), mk(T), mk(T), mk(T), mk(T), mk(F), mk(F), "Also vision fine-tuning; Developer deployment type not supported"],
        ["gpt-4.1, gpt-4.1-mini, gpt-4.1-nano (2025-04-14)", mk(T), mk(T), mk(F), mk(F), mk(T), mk(T), mk(T), mk(T), mk(T), mk(F), mk(F), "Vision fine-tuning: gpt-4.1 only (not mini or nano)"],
        ["o4-mini (2025-04-16)", mk(F), mk(F), mk(T), mk(F), mk(T), mk(T), mk(T), mk(T), mk(T), mk(F), mk(F), ""],
        ["gpt-5 (2025-08-07)", mk(F), mk(F), mk(T), mk(F), mk(T), mk(T), mk(T), mk(F), mk(T), mk(F), mk(F), "RFT needs an invitation; Standard deployment type only"],
        ["Llama-3.3-70B-Instruct, Qwen3-32B, Ministral-3B (2411)", mk(T), mk(F), mk(F), mk(F), mk(F), mk(T), mk(T), mk(F), mk(T), mk(F), mk(F), "Serverless: Global Standard only"],
        ["gpt-oss-20b", mk(T), mk(F), mk(F), mk(T), mk(F), mk(T), mk(T), mk(F), mk(T), mk(F), mk(F), "Serverless: Global Standard only"],
        ["gpt-oss-120b, Qwen3.6-35B-A3B, Qwen3.8-27B, Muse-Glimmer-30B (all preview)", mk(T), mk(F), mk(T), mk(T), mk(F), mk(F), mk(T), mk(T), mk(F), mk(T), mk(T), "Fireworks: Provisioned Throughput only"],
        ["MAI-Code-1.1-Flash (preview)", mk(F), mk(F), mk(T), mk(F), mk(F), mk(F), mk(T), mk(T), mk(T), mk(F), mk(F), "Serverless: Global Standard only"],
        ["MedImageInsight-Premium, CXRReportgen-Premium (preview)", mk(T), mk(F), mk(F), mk(F), mk(F), mk(F), mk(T), mk(F), mk(T), mk(F), mk(F), "Limited preview; Serverless: Global Standard only"],
    ]
    hm = Table(cols, rows, theme="blue", size=15, head_size=15, first_col_theme="blue", pad_y=8)
    gy = y + 90
    hm.place(cv, 0, gy)
    cw = hm.col_w
    groups = [("Method (Managed Training)", 1, 3, "blue"), ("Programmed", 4, 4, "violet"), ("Training type", 5, 8, "yellow"),
              ("Deployment option", 9, 11, "indigo")]
    xs = [sum(cw[:i]) for i in range(len(cw) + 1)]
    cv.text(0, y, "Supported models: method x training type x deployment option", size=22, color=BLUE_DEEP)
    cv.text(0, y + 28, "Green tick = supported, dash = not supported (as of 2026-11-03). Confirm in the overview page before you plan a run.",
            size=15, color=MUTED_, link=S_OVERVIEW[1])
    for label, a, b, th in groups:
        x1, x2 = xs[a], xs[b + 1]
        t = get_theme(th)
        tw = text_size(label, 16)[0]
        cv.text(x1 + (x2 - x1 - tw) / 2, gy - 30, label, size=16, color=t.deep)
        cv.line((x1 + 4, gy - 8), (x2 - 4, gy - 8), stroke=t.stroke, sw=3)

    rx = hm.right + G
    rw = W - rx
    with cv.panel(rx, y, title="Global training regions", sub="Managed and Programmed Training (as of 2026-11-03)", theme="blue", style="dotted",
                  fill="none", pad=20, w=rw, title_size=22, sub_size=14) as rp:
        chips_a = ["Australia East", "East US", "East US 2", "Korea Central", "North Central US", "Sweden Central",
                   "Switzerland North", "UK South", "West US 3"]
        chips_b = ["Canada East", "UAE North"]
        chips_c = ["Brazil South", "Canada Central", "France Central", "Germany West Central", "Italy North", "Japan East *",
                   "Norway East", "Poland Central *", "South Africa North", "South Central US", "South India", "Southeast Asia",
                   "Spain Central", "Switzerland West", "West Europe", "West US"]
        flow = ChipFlow([Chip(c, theme="blue", size=14) for c in chips_a] + [Chip(c, theme="violet", size=14) for c in chips_b] +
                        [Chip(c, theme="gray", size=14) for c in chips_c], rw - 40, gap=8)
        flow.place(cv, rp.ix, rp.iy)
        ly = flow.y + flow.h + 12
        legend(cv, rp.ix, ly, [("All models + Programmed", "blue"), ("Programmed; Managed has caveats", "violet")], size=13, gap=14)
        legend(cv, rp.ix, ly + 24, [("Managed only; not the four open-weight preview models", "gray")], size=13)
        note_t = ("* Japan East: no vision fine-tuning. Poland Central: no Managed Training for gpt-4.1-nano. Canada East: Managed Training "
                  "excludes the four open-weight preview models; UAE North supports Managed only for those four.")
        nt = wrap_text(note_t, (rw - 40) * 0.965, 13)
        cv.text(rp.ix, ly + 52, "\n".join(nt), size=13, color=MUTED_)
    sv_rows = [
        ["gpt-4o-mini", mk(F), mk(T), mk(T), mk(T), mk(T)],
        ["gpt-4o", mk(T), mk(F), mk(T), mk(T), mk(T)],
        ["gpt-4.1", mk(F), mk(T), mk(T), mk(F), mk(T)],
        ["gpt-4.1-mini, -nano", mk(F), mk(T), mk(T), "", ""],
        ["o4-mini", mk(T), mk(F), mk(T), "", ""],
        ["gpt-5", mk(F), mk(T), mk(T), "", ""],
    ]
    sv = Table([("Model", 170), ("East US 2", 100), ("N. Central US", 100), ("Sweden Central", 100), ("N. Central US", 100), ("Sweden Central", 100)],
               sv_rows, theme="blue", size=14, head_size=14, first_col_theme="blue")
    sv_y = rp.bottom + 78
    sv.place(cv, rx, sv_y)
    cv.text(rx, sv_y - 54, "Serving regions: Standard (cols 2-4), Provisioned Throughput (cols 5-6)", size=17, color=BLUE_DEEP)
    cv.text(rx, sv_y - 28, "Only these models and regions serve fine-tuned Standard or PTU deployments", size=14, color=MUTED_)
    y = max(hm.bottom, sv.bottom) + 60

    # ======================================================================= 5  run it (+ limits)
    y = sec(cv, y, "Run it: API sequence, portal, azd, roles and limits")
    seq = Sequence(cv, 0, y, [("Your code", "gray", "user"), ("Files API", "cyan", "storage"), ("Fine-tuning jobs", "blue", "ml"),
                              ("Events and checkpoints", "violet", "metrics")], spacing=415, head_w=230, head_h=62)
    seq.msg(0, 1, 'client.files.create(file=..., purpose="fine-tune")', num=1)
    seq.msg(1, 0, "file id", dash="dashed")
    seq.msg(0, 1, "client.files.wait_for_processing(id)", num=2)
    seq.msg(0, 2, "client.fine_tuning.jobs.create(model, training_file, validation_file, method, extra_body trainingType)", num=3)
    seq.msg(2, 0, "job id, status pending", dash="dashed")
    seq.note(0, 2, "Service side: queue, data safety check, training, model safety check, model created", kind="info")
    seq.msg(0, 3, "GET .../fine_tuning/jobs/{id}/events and /checkpoints", num=4)
    seq.msg(3, 0, "metrics, events, checkpoints", dash="dashed")
    seq.msg(0, 1, "GET /openai/v1/files/{id}/content  (results CSV)", num=5)
    sbot = seq.end()

    pc = Card(C, "Portal path", [
        "1. Build > Fine-tune; pick the base model and the method",
        "2. Choose the training type",
        "3. Upload or choose training and validation data",
        "4. Hyperparameters (defaults first); optional model suffix",
        "5. Submit; follow the Monitor and Checkpoints tabs",
        "Roles: Foundry User to train; Foundry Owner to deploy",
    ], theme="blue", icon="foundry", src=[S_SFT])
    az = Card(C, "azd path", [
        "azd ext install azure.ai.finetune (azd 1.22.1 or later)",
        "azd ai finetuning init -e <project-endpoint>",
        "azd ai finetuning jobs submit -f <yaml>",
        "jobs show | pause | resume | cancel -i <job-id>",
        "! Pause and resume don't exist for every model and method",
        "Samples: foundry-samples, samples/cli/finetuning",
    ], theme="indigo", icon="azd", src=[S_SFT])
    ap = Card(C, "API v1 facts", [
        "POST {endpoint}/openai/v1/fine_tuning/jobs",
        "GET .../jobs/{id}, /events and /checkpoints",
        "Cancel: client.fine_tuning.jobs.cancel(id)",
        "Delete uploaded files separately",
        "Deploy needs Foundry Owner or Microsoft.CognitiveServices/accounts/deployments/write",
    ], theme="blue", icon="api", src=[S_SFT])
    _, cb = row(cv, colx(3), y, [pc, az, ap], gap=G)
    lim = Table([("Limit (per resource)", 480), "Value"], [
        ["Fine-tuned model deployments", "10"],
        ["Training jobs", "100"],
        ["Simultaneously running jobs", "3 (Standard and Global training); 5 (Developer)"],
        ["Queued jobs", "20"],
        ["Fine-tuning files", "100"],
        ["Total file size", "1 GB"],
        ["Maximum file size", "512 MB (API); 200 MB (portal)"],
        ["Maximum job time", "720 hours"],
        ["Maximum job size (tokens in file x epochs)", "2 billion"],
    ], w=span(3), theme="orange", size=15, head_size=16, first_col_theme="orange", title="Fine-tuning limits (as of 2026-11-03)", title_size=22)
    lim.place(cv, colx(3), cb + 36)
    cv.text(colx(3) + lim.w - 360, cb + 40, "Learn: Azure OpenAI quotas and limits", size=12, color="#1971c2", link=S_QUOTAS[1])
    y = max(sbot, lim.bottom) + 60

    # ======================================================================= 6  safety gates + deploy
    y = sec(cv, y, "Safety gates and deployment")
    with cv.panel(0, y, title="Two safety gates (preview)", sub="managed evaluation: no thresholds to tune, and a failed gate isn't charged", theme="pink", style="dashed",
                  fill="soft", pad=24, w=span(3), title_size=24) as sg:
        bw3, gx3 = 230, 69
        yy = sg.iy + 14
        b_data = Box(bw3, "Training data", sub="uploaded files", theme="cyan", h=84, size=19).place(cv, sg.ix, yy)
        g1 = Box(bw3, "Gate 1: data evaluation", sub="harm categories (hate_fairness, self_harm, violence ...)", theme="pink", h=100, size=18).place(cv, sg.ix + (bw3 + gx3), yy - 8)
        b_train = Box(bw3, "Training", sub="billed phase", theme="yellow", h=84, size=19).place(cv, sg.ix + 2 * (bw3 + gx3), yy)
        g2 = Box(bw3, "Gate 2: model evaluation", sub="simulated conversation, risk and safety metrics", theme="pink", h=100, size=18).place(cv, sg.ix + 3 * (bw3 + gx3), yy - 8)
        b_ok = Box(bw3, "Deployable model", sub="only this result is persisted", theme="green", h=84, size=19).place(cv, sg.ix + 4 * (bw3 + gx3), yy)
        for a, b in ((b_data, g1), (g1, b_train), (b_train, g2), (g2, b_ok)):
            connect(cv, a, b, sw=3)
        f1 = Box(bw3, "Job fails", sub="not charged", theme="red", h=74, size=18).place(cv, g1.x, yy + 100 + 56)
        f2 = Box(bw3, "Not deployable", sub="run not charged", theme="red", h=74, size=18).place(cv, g2.x, yy + 100 + 56)
        connect(cv, g1, f1, dash="dashed", color="#e03131", sw=3, label="above threshold", label_size=14)
        connect(cv, g2, f2, dash="dashed", color="#e03131", sw=3, label="fails", label_size=14)
        facts = Card(span(3) - 48, "How the gates work", [
            "Thresholds are predefined and not customer-modifiable; they are independent of your content filters",
            "Evaluation runs in dedicated, customer-specific private workspaces in the same geography as your Foundry resource",
            "Training data isn't stored for evaluation; only the deployable / not-deployable result is persisted",
        ], theme="pink", icon="content-safety", src=[S_SAFETY])
        facts.place(cv, sg.ix, yy + 100 + 56 + 74 + 30)
    dx = colx(3)
    with cv.panel(dx, y, title="Deploy a fine-tuned model", sub="from the completed job's details page: Deploy, then choose", theme="blue", style="dashed",
                  fill="soft", pad=24, w=span(3), title_size=24) as dp:
        ow = span(3) - 48 - 190 - 100
        o1 = Card(ow, "Serverless", [
            "Name it, pick the deployment type the model supports, set capacity within your quota",
            "Monitor it on the Models page; hourly hosting + tokens (see the cost section)",
        ], theme="blue", icon="openai", src=[S_DEPLOY])
        o2 = Card(ow, "Managed compute", [
            "Needs a base deployment created from a LoRA-enabled template; the adapter must match the base model and version",
            "Multi-LoRA: several adapters share one compute; pick the compatible base deployment",
            "Managed-compute adapter deployments can't import external adapters",
        ], theme="blue", icon="container-apps", badge="preview", src=[S_DEPLOY])
        o3 = Card(ow, "Fireworks on Foundry", [
            "Subscription needs Fireworks.EnableDeploy; one adapter is merged into a full-weight copy",
            "Review pricing and provider terms; import local model files instead of re-uploading a registered model",
        ], theme="blue", icon="marketplace", badge="preview", src=[S_DEPLOY])
        ox, oy = dp.ix + 190 + 100, dp.iy + 6
        o1.place(cv, ox, oy)
        o2.place(cv, ox, o1.bottom + 20)
        o3.place(cv, ox, o2.bottom + 20)
        root = Box(190, "Completed job", sub="open its details page, click Deploy", theme="blue", h=120, size=19).place(
            cv, dp.ix, (oy + o3.bottom) / 2 - 60)
        for o in (o1, o2, o3):
            connect(cv, root, o, route="elbow", sw=3)
    y = max(sg.bottom, dp.bottom) + 28
    post = Note(span(6), "After deployment: test in the Playground by selecting the fine-tuned deployment (not the base), then evaluate with portal evaluations or the cloud evaluation SDK. "
                         "Delete the deployment to stop charges - cancelling training doesn't delete deployments. Limits: max 10 fine-tuned model deployments per resource; "
                         "Batch and Instant access aren't supported for fine-tuned models. Fine-tuned models aren't auto-upgraded and training and deployment retire on separate clocks (see the model-router-lifecycle canvas).",
                kind="tip", title="After you deploy", size=15, src=[S_DEPLOY])
    post.place(cv, 0, y)
    y = post.bottom + 60

    # ======================================================================= 7  cost
    y = sec(cv, y, "Cost management: three buckets",
            sub="Total cost = training + hosting + inference. Current rates are on the fine-tuning pricing page; the examples below use symbolic rates.")
    b_tr = Card(span(2), "1  Training", [
        "# SFT and DPO: token billing",
        "tokens in the file x epochs x training price per token",
        "# RFT (Managed Training): training-time billing",
        "hours in the Training phase (2 decimals) x hourly rate + grader tokens (a model grader is billed separately at data-zone rates)",
        "# Programmed Training (preview)",
        "prefill + cached prefill + sampling + training tokens, cumulative across the run",
        "# Any method",
        "Developer training is preemptible; paused Developer jobs aren't billed",
    ], theme="yellow", icon="cost-management", src=[S_COST])
    b_ho = Card(span(2), "2  Hosting", [
        "Standard and Global Standard: hourly fine-tuned-model hosting fee, billed even when unused",
        "Regional Provisioned Throughput: PTU-hours; no separate per-token charge",
        "Developer: no hosting fee, but evaluation only and removed after 24 hours",
        "Fireworks: per-token for supported catalog models; PTU-hours for imported custom models",
        "Managed compute (preview): GPUs per instance x instances x hours x GPU-hour rate - charged while it runs, even idle",
    ], theme="yellow", icon="batch", src=[S_COST])
    b_in = Card(span(2), "3  Inference", [
        "Standard: input and output tokens at base-model Standard rates",
        "Global Standard: input and output tokens at base-model Global Standard rates",
        "Developer: Global Standard token rates",
        "Provisioned Throughput: none per token; you pay PTU-hours",
        "Hosting and inference prices are the same for Managed- and Programmed-trained models with the same model and deployment configuration",
    ], theme="yellow", icon="quotas", src=[S_COST])
    row(cv, 0, y, [b_tr, b_ho, b_in], gap=G)
    mid = max(b_tr.bottom, b_ho.bottom, b_in.bottom)
    for i in (0, 1):
        px_ = span(2) + i * (span(2) + G) + G / 2
        pt = text_size("+", 52)
        cv.text(px_ - pt[0] / 2, y + (mid - y) / 2 - pt[1] / 2, "+", size=52, color="#e67700")
    y = mid + 36

    ex = Table([("Scenario", 330), ("Usage (from the cost page's examples)", 600), "Cost with symbolic rates"], [
        ["SFT, GPT-4.1, global training", "1M training tokens, 2 epochs; the 2 h 15 min run time doesn't set the charge", "2T  (T = training rate per million tokens)"],
        ["RFT without a model grader", "4 hours in the Training phase; preprocessing, safety checks and model creation not billed", "4H  (H = hourly training rate)"],
        ["RFT with an o3-mini score_model grader", "4 h training + 5M grader input and 4.9M grader output tokens", "4H + 5I + 4.9O"],
        ["Programmed Training (preview)", "1M prefill, 3M cached prefill, 2M sampling, 4M training tokens", "P + 3C + 2S + 4T"],
        ["Serverless hosting, o4-mini chatbot", "720 hours of hosting, 20M input and 40M output tokens in a 30-day month", "720H + 20I + 40O"],
        ["Fireworks provisioned custom model", "80 PTUs for 10 hours", "80 x 10 x U = 800U"],
        ["Managed compute (preview)", "2 GPUs per instance, 1 instance, 10 hours = 20 GPU-hours", "2 x 1 x 10 x G = 20G"],
    ], w=span(3), theme="yellow", size=15, head_size=16, first_col_theme="yellow", title="Worked examples (symbolic rates)", title_size=22)
    ex.place(cv, 0, y)
    rftc = Card(span(2), "RFT cost controls (Managed Training)", [
        "A per-job spending limit pauses the job and creates a deployable checkpoint; resuming continues with no further cost limit",
        "Start small: reasoning_effort low, shorter runs, smaller validation sets",
        "Limit validation and eval_samples; use the smallest grader that meets quality",
        "Tune compute_multiplier to trade convergence speed for cost",
        "Service errors aren't billed; a cancelled run is billed for the work done",
    ], theme="yellow", icon="gear", src=[S_COST])
    nb = Card(C, "Not billed", [
        "Time in the queue",
        "Failed jobs (SFT and DPO)",
        "Jobs cancelled before training begins",
        "Data safety checks",
        "Stop the meter: delete unused deployments",
    ], theme="green", icon="cost-management", src=[S_COST])
    row(cv, span(3) + G, y, [rftc, nb], gap=G, equalize=False)
    y = max(ex.bottom, rftc.bottom, nb.bottom) + 60

    # ======================================================================= 8  healthcare + gotchas
    y = sec(cv, y, "Healthcare premium models and gotchas")
    hc = Card(span(2), "Healthcare premium models", [
        "MedImageInsight-Premium and CXRReportgen-Premium (limited preview); SFT only, via the OpenAI Python client from the Foundry project SDK",
        "Model-specific data schemas and hyperparameters (separate guides); job states pending, running, then succeeded, failed or cancelled",
        "Deploy as a distinct deployment; everything uses GlobalStandard",
        "Check quota row AIServices.GlobalStandard.<model-name>-finetune with az cognitiveservices usage list; no row = you can't fine-tune there",
        "Base and fine-tuned deployments don't share quota; Entra needs Foundry User at the AIServices account scope",
        "! Research use only; not for clinical use",
    ], theme="teal", icon="ai-services", badge="preview", src=[S_HEALTH])
    hc.place(cv, 0, y)
    gn1 = [
        Note(span(2), "Standard and Global Standard hosting bills by the hour even at zero traffic, and Developer deployments are removed after 24 hours. Delete what you don't need.",
             kind="gotcha", title="Hosting accrues while idle", size=14),
        Note(span(2), "A LoRA adapter is valid only on its exact base model and version. Managed compute can't import external adapters; Fireworks import can (preview).",
             kind="warn", title="An adapter fits one exact base", size=14),
        Note(span(2), "Standard-type serving is limited to East US 2, North Central US and Sweden Central (per model). Open-weight serverless is Global Standard only; several models need managed compute or Fireworks PTU.",
             kind="warn", title="Serving regions are narrow", size=14),
    ]
    col(cv, span(2) + G, y, gn1, gap=18)
    gn2 = [
        Note(span(2), "Programmed Training, synthetic data generation, safety evaluation, managed compute, Fireworks serving, Developer-tier serving, MAI-Code-1.1-Flash, the open-weight preview models and the healthcare premium models are preview or limited preview as of 2026-11-03. Re-check before you rely on them.",
             kind="preview", title="Preview features", size=14),
        Note(span(2), "An RFT job auto-pauses at a per-job cost limit; resuming removes that limit. GPT-5 RFT needs an invitation through your Microsoft account team.",
             kind="gotcha", title="RFT limits and access", size=14),
        Note(span(2), "Fine-tuned models aren't auto-upgraded. Training and deployment have separate retirement clocks - plan retraining before the base model retires (see the model-router-lifecycle canvas).",
             kind="info", title="Plan for base-model retirement", size=14),
    ]
    col(cv, 2 * (span(2) + G), y, gn2, gap=18)
    y = max(hc.bottom, gn1[-1].bottom, gn2[-1].bottom) + 60

    sources(cv, 0, y, [
        ("Fine-tuning in Microsoft Foundry (overview, supported models)", learn("fine-tuning/overview")),
        ("Fine-tune a model with supervised fine-tuning", learn("openai/how-to/fine-tuning")),
        ("Fine-tune with direct preference optimization", learn("openai/how-to/fine-tuning-direct-preference-optimization")),
        ("Fine-tune with reinforcement fine-tuning", learn("openai/how-to/reinforcement-fine-tuning")),
        ("Vision fine-tuning", learn("openai/how-to/fine-tuning-vision")),
        ("Improve tool calling with fine-tuning", learn("openai/how-to/fine-tuning-functions")),
        ("Generate synthetic data (preview)", learn("fine-tuning/data-generation")),
        ("What is Programmed Training (preview)?", learn("fine-tuning/programmed-training/overview")),
        ("Deploy fine-tuned models", learn("fine-tuning/deploy-fine-tuned-models")),
        ("Manage fine-tuning costs", learn("fine-tuning/cost-management")),
        ("Safety evaluation for fine-tuning (preview)", learn("openai/how-to/fine-tuning-safety-evaluation")),
        ("Customize a premium healthcare AI model with fine-tuning", learn("how-to/healthcare-ai/fine-tune-premium-healthcare-models")),
        ("Azure OpenAI in Foundry Models quotas and limits", learn("openai/quotas-limits")),
    ], w=W, cols=3)
