"""Evaluation in depth - evaluator taxonomy, datasets, run modes, results, limits and CI/CD (Observability and safety)."""
from generator.xd import *

META = dict(
    id="evaluation", title="Evaluation in depth", section="2", group="Observability and safety", order=42,
    description="The Foundry evaluation workbench: every built-in evaluator by family, datasets and simulation, run modes (portal, SDK, azd, CI/CD, continuous), results, limits and regions.",
    tags=["evaluation", "evaluators", "datasets", "cloud-evaluation", "ci-cd", "red-teaming"],
)

W = 3320                      # canvas content width: 4 columns x 800 + 3 gaps x 40
CW, G = 800, 40
COLX = [i * (CW + G) for i in range(4)]

# one colour per evaluator family (kept identical in the flow, the catalog and the matrices)
FAM = dict(general="blue", sim="cyan", rag="teal", risk="pink", agent="green", rubric="violet", graders="lime",
           custom="orange")
PREVIEW, DEPREC = "orange", "red"
E = "concepts/evaluation-evaluators/"
OH = "observability/how-to/"


def span(n: int) -> float:
    return n * CW + (n - 1) * G


def hdr(cv: Canvas, y: float, n, text: str, sub: str = None) -> float:
    """Numbered section header spanning the canvas; returns the y for the first block below it."""
    if n:
        numbered(cv, 24, y + 26, n, theme="violet", d=48, size=28)
        _, b = section_header(cv, 66, y, text, sub, size=36, w=W - 66)
    else:
        _, b = section_header(cv, 0, y, text, sub, size=36, w=W)
    return b + 30


def src_lines(cv: Canvas, x: float, y: float, items, size: int = 12) -> float:
    cy = y
    for label, url in items:
        t = cv.text(x, cy, f"Learn: {label}", size=size, color=LINK, link=url)
        cy = t.bottom + 2
    return cy


def wrapped(text: str, w: float, size: int = 14) -> str:
    return "\n".join(wrap_text(text, w, size))


def fam_panel(cv, x, y, w, title, sub, theme, cols, rows, src, notes=(), size=14, pad=18, badge=None):
    """Soft-tinted family panel: title + facts line + table + notes + Learn links."""
    subw = wrapped(sub, w - 2 * pad - 6, 14) if sub else None
    with cv.panel(x, y, title=title, sub=subw, theme=theme, style="solid", fill="soft", pad=pad, title_size=24,
                  sub_size=14, w=w) as p:
        t = Table(cols, rows, w=w - 2 * pad, theme=theme, size=size, head_size=size + 1, first_col_theme=theme)
        t.place(cv, p.ix, p.iy)
        yy = t.bottom + 10
        for n in notes:
            tt = cv.text(p.ix, yy, wrapped(n, w - 2 * pad - 6, 14), size=14, color=INK)
            yy = tt.bottom + 6
        src_lines(cv, p.ix, yy, src)
        if badge:
            draw_badge(cv, x + w - pad - 90, y + pad - 2, badge)
    return p


def chain(cv, x, y, labels, bw, theme, gap=40, size=16, min_h=0):
    """Row of equal-width boxes joined by arrows; returns (right, bottom)."""
    boxes = [Box(bw, lab, theme=theme, size=size, min_h=min_h, fill="solid", pad=10) for lab in labels]
    r, b = row(cv, x, y, boxes, gap=gap)
    for a, c in zip(boxes, boxes[1:]):
        arrow(cv, [(a.right + 5, a.cy), (c.x - 5, c.cy)], sw=2.5)
    return r, b


def stack(cv, y, columns, gap=G):
    """Place explicit column stacks of blocks at the four grid columns; returns the lowest bottom."""
    low = y
    for i, blocks in enumerate(columns):
        cy = y
        for b in blocks:
            b.place(cv, COLX[i], cy)
            cy = b.bottom + gap
        low = max(low, cy - gap)
    return low


# ============================================================================================ 0. summary
def summary(cv: Canvas, y: float) -> float:
    ew, sg = 1040, 100
    data = Card(ew, "DATA", [
        "An existing dataset of query / response pairs or whole conversations",
        "Responses Foundry generates from your model or agent using test inputs",
        "Simulated or synthetic conversations and production traces",
    ], theme="cyan", icon="files", title_size=28, body_size=18, src=[("Evaluation in Foundry", learn("concepts/evaluation-overview"))])
    evals = Card(ew, "EVALUATORS", [
        "Scoring methods: deterministic calculations, or AI-assisted (a judge model that also explains its score)",
        "Built-in families, rubric, Azure OpenAI graders or your own custom evaluators",
        "Fields are mapped with data_mapping: {{item.field}}, {{sample.output_text}}, {{sample.output_items}}",
    ], theme="violet", icon="metrics", title_size=28, body_size=18, src=[("Built-in evaluators", learn("concepts/built-in-evaluators"))])
    res = Card(ew, "METRICS + EXPLANATIONS", [
        "Per evaluator: label (pass / fail), score, threshold, passed and reason; some add details",
        "Compare versions, find failure patterns and decide whether the app is ready to deploy",
        "Results live in your Foundry project and can also flow to Application Insights",
    ], theme="blue", icon="dashboard", title_size=28, body_size=18, src=[("Evaluation results", learn(OH + "cloud-evaluation-results"))])
    r, b = row(cv, 0, y, [data, evals, res], gap=sg)
    for left, sign in ((data, "+"), (evals, "=")):
        tw, th = text_size(sign, 72)
        cv.text(left.right + (sg - tw) / 2, left.y + (left.h - th) / 2, sign, size=72, color=INK)

    y2 = b + 46
    cv.text(0, y2, "Where evaluation fits in the lifecycle", size=24, color=THEMES["violet"].deep)
    y2 += 40
    s1 = Card(CW, "Base model selection", ["Foundry benchmarks and the Azure AI Evaluation SDK on model endpoints"],
              theme="blue", body_size=17, src=[("Observability", learn("concepts/observability"))])
    s2 = Card(CW, "Pre-production", ["Datasets, edge cases and the AI Red Teaming Agent (PyRIT)"], theme="violet", body_size=17,
              src=[("AI Red Teaming Agent", learn("concepts/ai-red-teaming-agent"))])
    s3 = Card(CW, "Post-production", ["Operational metrics, continuous evaluation, scheduled evaluation, scheduled red teaming and Azure Monitor alerts"],
              theme="green", body_size=17, src=[("Monitor agents", learn(OH + "how-to-monitor-agents-dashboard"))])
    n1 = Note(CW, "Risk and safety evaluations and evaluations in the agent playground are billed on consumption. "
                  "Agent-playground evaluations are ON by default for every project - turn them off by unselecting all evaluators under Metrics in the playground.",
              kind="warn", title="Billing and defaults",
              src=[("Evaluation overview", learn("concepts/evaluation-overview")),
                   ("Foundry observability pricing", "https://azure.microsoft.com/pricing/details/foundryobservability/")])
    hmax = max(s1.h, s2.h, s3.h, n1.h)
    for i, blk in enumerate((s1, s2, s3, n1)):
        blk.place(cv, COLX[i], y2, h=hmax)
    for a, c in ((s1, s2), (s2, s3)):
        arrow(cv, [(a.right + 5, a.cy), (c.x - 5, c.cy)], sw=3)
    return y2 + hmax + 70


# ============================================================================================ A. workbench
GROUPS = [
    ("You bring the data", "cyan", ["Dataset file (JSONL / CSV)", "Conversation dataset (messages)"]),
    ("Foundry generates the responses", "green", ["Model target", "Agent target (prompt + hosted)"]),
    ("Already captured", "teal", ["Response IDs", "Traces (preview)", "Deployed conversations (preview)"]),
    ("Foundry generates the data", "violet", ["Synthetic queries (preview)", "Synthetic conversations",
                                              "Simulated user conversations", "Benchmark datasets (preview)"]),
]
FAMS = [
    ("General purpose (2)", "Coherence, Fluency", FAM["general"]),
    ("Textual similarity (6)", "Similarity, F1, BLEU, GLEU, ROUGE, METEOR", FAM["sim"]),
    ("RAG (6)", "Retrieval, Document retrieval, Groundedness (+ Pro), Relevance, Response completeness", FAM["rag"]),
    ("Risk and safety (10)", "Hate, sexual, violence, self-harm, protected material, XPIA, code vulnerability ...", FAM["risk"]),
    ("Agent (13 listed)", "Task completion, intent resolution, tool-call accuracy, output and tool-use quality ...", FAM["agent"]),
    ("Rubric (preview)", "Weighted custom criteria scored 1-5, normalised to 0-1", FAM["rubric"]),
    ("Azure OpenAI graders (4)", "label_model, score_model, string_check, text_similarity", FAM["graders"]),
    ("Custom (preview)", "Code-based, prompt-based or endpoint-based", FAM["custom"]),
]
DOORS = [
    ("Foundry portal", "Evaluation page, or the agent's Evaluation tab", "violet"),
    ("SDK cloud evaluation", "Evals API: evals.create, then evals.runs.create", "violet"),
    ("azd CLI (preview)", "azd ai agent eval generate / run / update", "violet"),
    ("CI/CD (preview)", "GitHub Action or Azure DevOps task", "violet"),
    ("Continuous + scheduled", "Monitor settings: rule on each completed response, or a recurrence schedule", "violet"),
    ("Benchmarks (preview)", "Predefined dataset + task category + evaluation logic", "violet"),
    ("Human evaluation (preview)", "Templates and the Preview web app for reviewers", "violet"),
    ("Red-team scan", "AI Red Teaming Agent on the same Evals API (scenario red_team)", "pink"),
]
STEPS = [
    ("Aggregate", "result_counts (passed / failed / total) and per-evaluator pass_rate; p50 / p95 latency and estimated cost for model targets", "violet"),
    ("Row by row", "query, response, ground truth, score and the evaluator's explanation", "violet"),
    ("Compare runs", "t-test per evaluator: ImprovedStrong ... Inconclusive; pick a baseline run", "violet"),
    ("Cluster analysis (preview)", "embedding-based clusters of outputs and feedback, with recommendations", "teal"),
    ("Optimize and iterate", "fix the prompt, tools, model or rubric; mine traces into datasets; azd ai agent optimize", "green"),
]


def workbench(cv: Canvas, y: float) -> float:
    y = hdr(cv, y, None, "The evaluation workbench: four lanes and one feedback loop",
            "Evaluators score data - a dataset, generated responses, simulated conversations or production traces - and the results drive the next iteration")
    LW, LG, PAD = 740, 120, 22
    IW = LW - 2 * PAD
    lx = [i * (LW + LG) for i in range(4)]
    panels = []

    def lane(i, title, sub, fill_fn):
        with cv.panel(lx[i], y, title=None, theme="gray", style="dotted", pad=PAD, w=LW) as p:
            numbered(cv, p.ix + 24, p.iy + 26, i + 1, theme="violet", d=50, size=28)
            cv.text(p.ix + 64, p.iy - 4, title, size=30, color=INK)
            cv.text(p.ix + 64, p.iy + 34, sub, size=15, color=MUTED)
            fill_fn(p.ix, p.iy + 84)
        panels.append(p)

    def lane1(x, yy):
        a = Box(340, "Turn level", sub="default: scores each response; earlier messages are context", theme="blue",
                size=19, sub_size=14, min_h=108)
        b = Box(340, "Conversation level", sub="scores the whole multi-turn interaction; needs the messages format",
                theme="violet", size=19, sub_size=14, min_h=108)
        _, bt = row(cv, x, yy, [a, b], gap=16)
        yy = bt + 22
        for gtitle, th, items in GROUPS:
            t = cv.text(x, yy, gtitle, size=17, color=THEMES[th].deep)
            cf = ChipFlow(items, IW, gap=10, theme=th, size=15)
            cf.place(cv, x, t.bottom + 6)
            yy = cf.y + cf.h + 20

    def lane2(x, yy):
        boxes = [Box(340, lab, sub=sub, theme=th, size=20, sub_size=15, min_h=116, fill="solid") for lab, sub, th in FAMS]
        _, bt = grid(cv, x, yy, boxes, 2, gap_x=16, gap_y=14)
        Chip("deployment_name + data_mapping + threshold per evaluator", theme="violet", size=15,
             fill="soft").place(cv, x, bt + 18)

    def lane3(x, yy):
        boxes = [Box(340, lab, sub=sub, theme=th, size=20, sub_size=15, min_h=116, fill="solid") for lab, sub, th in DOORS]
        _, bt = grid(cv, x, yy, boxes, 2, gap_x=16, gap_y=14)
        Chip("every door calls the same Evals API", theme="violet", size=15, fill="soft").place(cv, x, bt + 18)

    def lane4(x, yy):
        boxes = [Box(IW, lab, sub=sub, theme=th, size=20, sub_size=15, min_h=92, fill="solid") for lab, sub, th in STEPS]
        _, bt = col(cv, x, yy, boxes, gap=30)
        for a, c in zip(boxes, boxes[1:]):
            arrow(cv, [(a.cx, a.bottom + 3), (c.cx, c.y - 3)], sw=2.5)

    lane(0, "CHOOSE UNIT + DATA", "what to score, and where the rows come from", lane1)
    lane(1, "PICK EVALUATORS", "scoring methods, one or many per run", lane2)
    lane(2, "RUN", "pick a door: the engine is the same", lane3)
    lane(3, "REVIEW + IMPROVE", "read, compare, cluster, fix", lane4)

    H = max(p.h for p in panels)
    for p in panels:
        p.el.el["height"] = round(H, 2)
        p.h = H
    labels = ["rows to\nscore", "testing\ncriteria", "eval run +\noutput items"]
    for i in range(3):
        connect(cv, panels[i], panels[i + 1], a_side="right", b_side="left", ta=0.42, tb=0.42, sw=3.5,
                color="#5f3dc4", label=labels[i], label_size=15, label_dy=-2, gap=8)
    bot = y + H
    pts = [(panels[3].cx, bot + 6), (panels[3].cx, bot + 62), (panels[0].cx, bot + 62), (panels[0].cx, bot + 6)]
    arrow(cv, pts, dash="dashed", color="#5f3dc4", sw=3.5, end_head="arrow", label_size=17,
          label="iterate: change one thing, re-run the same recipe, compare runs; mine production traces into the next dataset",
          label_pos="above", label_dy=-4)

    # how a cloud evaluation is wired
    y2 = bot + 120
    cv.text(0, y2, "How one cloud evaluation is wired (Evals API)", size=26, color=THEMES["violet"].deep)
    y2 += 46
    wsteps = [
        ("1  Prepare data", "Upload a versioned dataset with project_client.datasets.upload_file(...), or pass file_content inline.", "cyan"),
        ("2  Create the eval", "evals.create(data_source_config, testing_criteria). Each criterion: type azure_ai_evaluator, evaluator_name builtin.<id>, initialization_parameters, data_mapping.", "violet"),
        ("3  Create a run", "evals.runs.create(data_source): dataset, model or agent target, response IDs, traces, simulation ...", "violet"),
        ("4  Poll", "evals.runs.retrieve until completed, failed or canceled. Stuck? evals.runs.cancel(run_id, eval_id=...).", "violet"),
        ("5  Read the results", "run.report_url, result_counts, per_testing_criteria_results and evals.runs.output_items.list.", "blue"),
    ]
    cards = [Card(600, t, [("para", b, 0)], theme=th, title_size=22, body_size=17) for t, b, th in wsteps]
    _, bb = row(cv, 0, y2, cards, gap=80)
    for a, c in zip(cards, cards[1:]):
        arrow(cv, [(a.right + 6, a.cy), (c.x - 6, c.cy)], sw=3, color="#5f3dc4")
    n = Note(W, "REST: POST https://{account}.services.ai.azure.com/api/projects/{project}/openai/evals?api-version=v1, then .../openai/evals/{eval_id}/runs?api-version=v1 "
                "(the benchmark page uses api-version=2025-11-15-preview). Token audience: https://ai.azure.com. "
                "SDK minimums for azure-ai-projects: 2.2.0 cloud evaluation, 2.5.0 synthetic conversations, 2.8.0 data generation and evaluate-agent (latest version not verified).",
             kind="info", title="Endpoints and SDK versions",
             src=[("Cloud evaluation", learn(OH + "cloud-evaluation"))])
    n.place(cv, 0, bb + 24)
    return n.bottom + 90


# ============================================================================================ 1. data
def run_mode_rows():
    def m(label, path):
        return dict(text=label, link=learn(path), theme="cyan")
    return [
        [m("Dataset (turn)", OH + "cloud-evaluation-datasets"), "SDK, portal",
         "jsonl or csv + source {type: file_id | file_content}; data_source_config type custom with an item_schema",
         "Recommended: upload a versioned dataset"],
        [m("Model target", OH + "cloud-evaluation-targets"), "SDK, portal",
         "azure_ai_target_completions + target {type: azure_ai_model, model, sampling_params} + an input_messages template",
         "Model router is allowed ONLY as a target"],
        [m("Agent target", OH + "cloud-evaluation-targets"), "SDK, portal, azd, CI/CD",
         "same, with target {type: azure_ai_agent, name, version?}; works for prompt AND hosted agents",
         "Hosted agent with only the invocations protocol: free-form input_messages such as {\"message\": \"{{item.query}}\"}; if both protocols exist, responses is used"],
        [m("Response IDs", OH + "cloud-evaluation-deployed-interactions"), "SDK",
         "azure_ai_responses + data_source_config {type: azure_ai_source, scenario: responses}",
         "file_content only - file_id returns HTTP 400"],
        [m("Traces (preview)", OH + "cloud-evaluation-deployed-interactions"), "SDK, portal (Traces)",
         "azure_ai_traces (agent_id or agent_name + version, trace_ids, max_traces, lookback_hours), scenario traces",
         "Needs invoke_agent spans; recommended for agents outside Agent Service (LangChain, custom)"],
        [m("Synthetic queries (preview)", OH + "cloud-evaluation-synthetic-data"), "SDK, portal",
         "azure_ai_synthetic_data_gen_preview + item_generation_params {samples_count 15-1,000, model_deployment_name, prompt, output_dataset_name, sources (1 file)}",
         "Generated queries are saved as a dataset; with input_messages only the system role is allowed"],
        [m("Conversation dataset", OH + "cloud-evaluation-conversations"), "SDK, portal",
         "jsonl with messages and an evaluation_level", "Conversation level needs the messages format"],
        [m("Deployed conversations (preview)", OH + "cloud-evaluation-deployed-conversations"), "SDK",
         "azure_ai_trace_data_source_preview + trace_source: conversation_ids (lookback default 168 h) or agent_filter (max_traces default 1,000; filter_strategy random_sampling (default) or smart_filtering; window >= 15 min)",
         "The page pins SDK 2.7.0"],
        [m("Simulation", OH + "cloud-evaluation-simulate-conversations"), "SDK, portal",
         "azure_ai_user_conversation_simulation + model_configuration {model: connection/deployment, sampling_params, voice_model} + default_simulation_configuration",
         "Settings are in the simulation card above"],
        [m("Synthetic conversations", OH + "cloud-evaluation-synthetic-conversations"), "SDK",
         "azure_ai_synthetic_data_generation_with_simulation + generation_sources[] (agent, prompt or file; combinable)",
         "azure-ai-projects >= 2.5.0; generates scenarios, simulates and evaluates in ONE run"],
        [m("Benchmarks (preview)", OH + "benchmark-evaluations"), "Portal, REST",
         "eval group data_source_config {type: azure_ai_source, scenario: benchmark_preview, benchmark_name: builtin.truthful_qa, benchmark_version, grader_model?}; run type azure_ai_benchmark_preview",
         "See the benchmarks card"],
        [m("Human evaluation (preview)", OH + "human-evaluation"), "Portal", "Templates + the Preview web app",
         "Needs Application Insights"],
        [m("Continuous / scheduled", OH + "how-to-monitor-agents-dashboard"), "Monitor settings, SDK",
         "evaluation_rules (ContinuousEvaluationRuleAction, max_hourly_runs default 100, event RESPONSE_COMPLETED) or beta.schedules (RecurrenceTrigger, DailyRecurrenceSchedule(hours=[9]))",
         "See the continuous evaluation card"],
        [m("azd", OH + "azure-developer-cli-evaluation"), "CLI", "azd ai agent eval generate / run / update / list / show", "Preview"],
        [m("CI/CD", "how-to/evaluation-github-action"), "GitHub Action, Azure DevOps",
         "microsoft/ai-agent-evals@v3-beta;  AIAgentEvaluation@2", "Preview"],
    ]


def data_section(cv: Canvas, y: float) -> float:
    y = hdr(cv, y, 1, "Choose the unit and the data",
            "Turn or conversation first - then bring a dataset, let Foundry run a target, replay traces, or generate the data")
    unit = Card(CW, "Turn or conversation?", [
        "evaluation_level: turn (default) scores individual responses; earlier messages are context",
        "conversation scores the whole multi-turn interaction and requires the messages format (query / response data can't)",
        "Conversation-capable built-ins: output_quality, tool_use_quality, deflection_rate, customer_satisfaction, task_completion, coherence, groundedness",
        "Every other built-in is turn-only: fluency, relevance, intent_resolution, task_adherence, the tool evaluators ...",
        "Turn level: all built-ins except document_retrieval and the deprecated quality_grader accept messages; OpenAI graders do not",
        "Example: a user retries 'reset email' 3 times - turn level rates the last polite answer high; conversation-level Customer Satisfaction flags the repeated failing action",
        "! Portal 'Full conversations' scope is preview",
    ], theme="violet", icon="workflow", src=[("Evaluation levels", learn("concepts/built-in-evaluators") + "#evaluation-levels"),
                                              ("Evaluate conversation datasets", learn(OH + "cloud-evaluation-conversations"))])
    schema = Card(CW, "Dataset formats and schema", [
        "JSONL (one object per line); CSV works for simple string query / response",
        "Versioned Foundry datasets: project_client.datasets.upload_file(...); or inline with file_content",
        "# Primary column by scenario",
        "Existing interaction: messages",
        "Stored input + output: query, response",
        "Target evaluation: messages ending with a user message, or query (Foundry generates the response; any stored response is ignored)",
        "Simulation: test_case_description (+ optional desired_num_turns)",
        "# Supporting columns: ground_truth, tool_definitions, context",
        "messages roles: developer, system, user, assistant, tool; content is a string or typed items (text, input_text, output_text, tool_call, tool_result)",
        "No dataset needed for response-ID, trace-based or synthetic-query evaluations",
        "Multimodal (portal, preview): image_url (+ caption), audio_data (WAV data URI + expected), or chat-format image_url / input_audio items",
    ], theme="cyan", icon="file", src=[("Evaluation datasets", learn(OH + "evaluation-datasets")),
                                       ("Dataset schema", learn(OH + "evaluation-dataset-schema"))])
    gen = Card(CW, "Synthetic datasets (data generation service)", [
        "SDK azure-ai-projects >= 2.8.0: project_client.datasets.begin_create_generation_job; needs Foundry User and a Responses-API-capable model",
        "# Task types",
        "Simple QnA (single-turn): query + ground_truth",
        "Simulation seed (multi-turn): test_case_description (+ id, category, desired_num_turns)",
        "# Sources",
        "Agent definition (AgentDataGenerationJobSource), Prompt (PromptDataGenerationJobSource) or Reference file (FileDataGenerationJobSource)",
        "Reference file: must be in processed state, >= 1 KB; .txt .md .csv .json .xml .html .pdf .png .jpg .jpeg .gif .tiff .tif .svg",
        "Simple QnA needs an agent or prompt source plus at most one reference file",
        "max_samples 1-1,000 per dataset job; portal: Data Generation tab > Create dataset > Generate synthetic (Dataset usage = Evaluation)",
        "! The SDK 2.8.0 simulation-seed config does not expose max_samples - use the portal for seeds",
    ], theme="cyan", icon="ml", src=[("Synthetic datasets", learn(OH + "evaluation-dataset-synthetic"))])
    traces = Card(CW, "Datasets from production traces", [
        "Traces live in Application Insights; sampling, MinHash and redact_private_content are covered in the Tracing explainer",
        "Intelligent sampling (traces evaluation, portal toggle): exact dedupe -> hard filters (broken or truncated sessions, malformed tool calls) -> aggregation -> MinHash farthest-first selection",
        "Sampling runs on local compute with no extra model cost",
        "azure_ai_traces needs invoke_agent spans; recommended for agents outside Agent Service (LangChain, custom)",
        "Deployed conversations (preview): by conversation_ids (lookback default 168 h) or agent_filter (max_traces default 1,000; random_sampling by default or smart_filtering; window >= 15 min)",
        "Data generation regions (28) also cover traces-to-dataset - see the region matrix",
    ], theme="teal", icon="app-insights", src=[("Traces to dataset", learn(OH + "traces-to-dataset")),
                                                ("Deployed conversations", learn(OH + "cloud-evaluation-deployed-conversations"))])
    _, b = row(cv, 0, y, [unit, schema, gen, traces], gap=G)

    y2 = b + G
    sim = Card(CW, "Simulated user conversations", [
        "Data source azure_ai_user_conversation_simulation + model_configuration {model: connection/deployment, sampling_params, voice_model} + default_simulation_configuration",
        "test_case_description: 1-2,500 characters; each test case has a test_case_id and a simulation_configuration",
        "Run defaults: max_num_turns 20, conversation_repetitions 1; desired_num_turns must be <= max",
        "user_behavior (e.g. interruption.type = default); audio_effects: street_traffic, crowd_chatter, background_tv, metro_station, telephonic_voice (volume_percentage 1-100, default 15)",
        "Run-only: enable_conversation_dataset_generation (default false) + output_conversation_dataset_name; result output_datasets [{type: simulated_user_conversations}]",
        "Voice: voice_model.type azure-standard (+ neural voice name, temperature 0-1) through the Voice Live endpoint",
        "! Model router is not allowed as the simulator",
    ], theme="violet", icon="bot", src=[("Simulate conversations", learn(OH + "cloud-evaluation-simulate-conversations"))])
    sim2 = Card(CW, "Portal limits and synthetic conversations", [
        "# Portal limits for simulation",
        "Simulator models: gpt-4.1 (recommended), gpt-4o, gpt-4o-mini, gpt-4.1-mini",
        "1-5 conversations per scenario; 1-50 turns",
        "'Existing conversations': 1-100 conversations; quick filters Last Day, 7D, 1M, 3M",
        "# Synthetic conversations (one run, three stages)",
        "azure_ai_synthetic_data_generation_with_simulation + generation_sources[] of type agent, prompt or file (combinable)",
        "Generates scenarios, simulates them and evaluates the conversations in ONE run; azure-ai-projects >= 2.5.0",
        "Pair with conversation-level evaluators: Customer Satisfaction, Task Completion, Output Quality",
    ], theme="violet", icon="bot", src=[("Synthetic conversations", learn(OH + "cloud-evaluation-synthetic-conversations"))])
    nrow = Note(span(2), "Turn-only evaluators in a conversation-level run: built-in-evaluators and cloud-evaluation-conversations say they are SKIPPED (not failed); "
                         "the Troubleshooting page says a turn-only evaluator at conversation level causes an \"incompatible evaluation level\" error. "
                         "Until the pages agree, keep conversation-level runs to conversation-capable evaluators.",
                kind="warn", title="Docs disagree: turn-only evaluator in a conversation-level run",
                src=[("Built-in evaluators", learn("concepts/built-in-evaluators") + "#evaluation-levels"),
                     ("Troubleshooting", learn(OH + "troubleshooting"))])
    rb = max(sim.h, sim2.h)
    sim.place(cv, COLX[0], y2, h=rb)
    sim2.place(cv, COLX[1], y2, h=rb)
    nrow.place(cv, COLX[2], y2)
    # model roles table beside it
    roles = Table(
        [("Role", 270), "Allowed or recommended (as of 2026-11-03)", ("Not allowed / notes", 300)],
        [
            [("Judge: AI-assisted built-ins", "violet"), "Azure OpenAI or OpenAI reasoning / non-reasoning models; gpt-5-mini gives the best balance of performance and cost", "Model router: no"],
            [("Judge: composite evaluators", "violet"), "A GPT-5.6-family model; gpt-5.6-luna is the lowest-cost option", ""],
            [("Judge: rubric (preview)", "violet"), "Recommended: gpt-5.5, gpt-5.4, gpt-5.4-mini (best balance), gpt-5.4-nano, gpt-5.2, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano. Acceptable: gpt-4.1, gpt-4o", ""],
            [("Target (the model under test)", "blue"), "Any model deployment or agent", "Model router is allowed ONLY here"],
            [("User simulator (portal)", "blue"), "gpt-4.1 (recommended), gpt-4o, gpt-4o-mini, gpt-4.1-mini", "Model router: no"],
            [("Synthetic data generator", "cyan"), "A Responses-API-capable model", "Model router: no; admin-connected models: no"],
            [("Admin-connected model (preview)", "gray"), "A model behind an enterprise AI gateway (APIM or non-Azure) as connection-name/deployment-name, for judge, target or simulator; must expose Chat Completions", "Not for synthetic data generation"],
        ], w=span(2), theme="violet", size=14, head_size=15, title="Which model plays which role", title_size=22)
    roles.place(cv, COLX[2], nrow.bottom + 24)
    y3 = max(sim.bottom, roles.bottom) + 44

    t = Table([("Mode", 330), ("Where", 250), ("Data source type and key parameters", 1500), ("Notes", 1240)], run_mode_rows(),
              w=W, theme="cyan", size=14, head_size=16, first_col_theme="cyan",
              title="Pick the data-source type - 15 ways to feed an evaluation (mode names link to the how-to page)", title_size=24)
    t.place(cv, 0, y3)
    return t.bottom + 90


# ============================================================================================ 2. evaluators
def combos(cv: Canvas, y: float) -> float:
    cv.text(0, y, "Combine evaluators (Learn's recommended starting sets)", size=24, color=THEMES["violet"].deep)
    y += 42
    sets = [
        ("RAG applications", "teal", [("Retrieval", "teal"), ("Groundedness", "teal"), ("Relevance", "teal"), ("Content safety", "pink")]),
        ("Agent applications", "green", [("Output Quality", "green"), ("Tool Use Quality", "green"), ("Rubric", "violet"), ("Content safety", "pink")]),
        ("Translation applications", "cyan", [("BLEU", "cyan"), ("METEOR", "cyan"), ("Fluency", "blue"), ("Coherence", "blue")]),
        ("All applications", "pink", [("Hate and Unfairness", "pink"), ("Sexual", "pink"), ("Violence", "pink"), ("Self-Harm", "pink")]),
    ]
    bottoms = []
    for i, (title, th, chips) in enumerate(sets):
        with cv.panel(COLX[i], y, title=title, theme=th, style="dashed", fill="soft", pad=18, title_size=22, w=CW) as p:
            cf = ChipFlow([Chip(lab, theme=ct, size=17) for lab, ct in chips], CW - 36, gap=10)
            cf.place(cv, p.ix, p.iy)
            tail = "add the risk and safety evaluators for responsible AI practices" if i == 3 else "run these together for a rounded view"
            tt = cv.text(p.ix, cf.y + cf.h + 10, tail, size=14, color=MUTED)
            src_lines(cv, p.ix, tt.bottom + 6, [("Combining evaluators", learn("concepts/built-in-evaluators") + "#combining-evaluators")])
        bottoms.append(p.bottom)
    return max(bottoms) + 46


def decision_matrix(cv: Canvas, y: float) -> float:
    F = FAM
    rows = [
        [("Is the text well formed?", F["general"]), "coherence, fluency", "query + response, or messages",
         "LLM judge, English only, unreliable below ~20 tokens; fluency is turn-only, coherence also runs at conversation level"],
        [("Does it match a known good answer?", F["sim"]), "similarity (semantic); f1_score, rouge_score, bleu_score, gleu_score, meteor_score (overlap)", "ground_truth (+ query for similarity)",
         "All six are GA; rouge_type is required; only similarity needs a judge deployment"],
        [("Did retrieval fetch the right chunks?", F["rag"]), "retrieval (no ground truth); document_retrieval (labelled)", "query + context; retrieval_ground_truth + retrieved_documents",
         "document_retrieval needs no model: Fidelity, NDCG, XDCG, Max Relevance, Holes - use it for sweeps of search algorithm, top_k and chunk size"],
        [("Is the answer grounded in the context?", F["rag"]), "groundedness; groundedness_pro (preview)", "response + context (+ query, tool_definitions)",
         "Pro is strict, runs on Azure AI Content Safety, needs no model deployment, East US 2 and Sweden Central only"],
        [("Does it answer the question fully?", F["rag"]), "relevance; response_completeness (preview)", "query + response; ground_truth + response",
         "Completeness is recall against the ground truth, groundedness is precision"],
        [("Is the content harmful?", F["risk"]), "hate_unfairness, sexual, violence, self_harm", "query + response, or messages",
         "Hosted evaluation-service models (no deployment_name); severity 0-7, pass if score <= 3 by default; 22 regions"],
        [("Copyright, prompt injection, insecure code, inferred attributes?", F["risk"]), "protected_material, indirect_attack (XPIA), code_vulnerability, ungrounded_attributes", "query + response (+ context for ungrounded_attributes)",
         "protected_material: East US 2 only; indirect_attack: model targets only; code_vulnerability: 7 languages, 19 subclasses"],
        [("Is my agent breaking rules or leaking data?", F["risk"]), "prohibited_actions, sensitive_data_leakage (both preview)", "query, response, tool_calls, or messages",
         "Agent targets only (not dataset or model evaluations); turn level only"],
        [("Did the agent finish the job and satisfy the user?", F["agent"]), "task_completion, customer_satisfaction (both preview); output_quality (composite)", "agent messages",
         "All three also run at conversation level; customer_satisfaction scores 6 dimensions on a 1-5 Likert scale"],
        [("Did it follow the rules and read the intent?", F["agent"]), "task_adherence, intent_resolution (both preview)", "agent messages", "Turn level; both are also batched inside output_quality"],
        [("Are the tools used correctly?", F["agent"]), "tool_call_accuracy, tool_selection, tool_input_accuracy, tool_output_utilization, tool_call_success; tool_use_quality (composite)", "agent messages",
         "Full support: File Search, Function tool, MCP, Knowledge-based MCP. Limited: Azure AI Search, Bing, SharePoint, Code Interpreter, Fabric Data Agent, Web Search"],
        [("Did it take the expected steps?", F["agent"]), "task_navigation_efficiency", "expected_actions + (actions or messages)",
         "matching_mode: exact_match, in_order_match or any_order_match; requires ground truth"],
        [("Does it meet my own business criteria?", F["rubric"]), "rubric (preview); label_model or score_model grader; custom prompt-based", "rubric dimensions, labels or a judge prompt",
         "Docs recommend rubric as the primary agent-quality measure, paired with built-ins for safety, groundedness and harm"],
        [("Exact, pattern or fuzzy match?", F["graders"]), "string_check (eq, ne, like, ilike); text_similarity grader (fuzzy_match, bleu, gleu, meteor, cosine, rouge_*)", "input + reference (+ pass_threshold)",
         "OpenAI graders do not accept messages; they run locally or remotely"],
        [("Something no built-in covers?", F["custom"]), "custom evaluator: code-based, prompt-based or endpoint-based (preview)", "grade(sample, item); a judge prompt; an HTTP endpoint",
         "Code: 2 min per call, no network; endpoint: 30 s timeout; conversation level via evaluation_level"],
    ]
    rows = [[(r[0][0], r[0][1]), r[1], r[2], r[3]] for r in rows]
    t = Table([("If you need to know ...", 560), ("Reach for", 1000), ("You supply", 620), ("Fine print", 1140)], rows, w=W,
              theme="violet", size=14, head_size=16,
              title="Which evaluator when - pick the question, read across (first column is coloured by evaluator family)", title_size=24)
    t.place(cv, 0, y)
    return t.bottom + 50


def constraint_map(cv: Canvas, y: float) -> float:
    cv.text(0, y, "Constraint map - what each evaluator needs (chip colour = family)", size=24, color=THEMES["violet"].deep)
    y += 44
    F = FAM
    rows = [
        ("Needs ground truth, labels or expected actions", "red", [
            ("similarity", F["sim"]), ("f1_score", F["sim"]), ("bleu_score", F["sim"]), ("gleu_score", F["sim"]), ("rouge_score", F["sim"]),
            ("meteor_score", F["sim"]), ("response_completeness (preview)", F["rag"]), ("document_retrieval", F["rag"]),
            ("task_navigation_efficiency", F["agent"])]),
        ("No judge deployment needed", "gray", [
            ("f1_score", F["sim"]), ("bleu_score", F["sim"]), ("gleu_score", F["sim"]), ("rouge_score", F["sim"]), ("meteor_score", F["sim"]),
            ("document_retrieval", F["rag"]), ("groundedness_pro (Content Safety)", F["rag"]), ("all 10 risk and safety (hosted models)", F["risk"]),
            ("string_check", F["graders"]), ("text_similarity grader", F["graders"])]),
        ("Also run at conversation level", "violet", [
            ("coherence", F["general"]), ("groundedness", F["rag"]), ("task_completion", F["agent"]), ("customer_satisfaction", F["agent"]),
            ("output_quality", F["agent"]), ("tool_use_quality", F["agent"]), ("deflection_rate (undocumented)", F["agent"]),
            ("rubric", F["rubric"]), ("custom (evaluation_level)", F["custom"])]),
        ("Target restrictions", "pink", [
            ("prohibited_actions: agents only", F["risk"]), ("sensitive_data_leakage: agents only", F["risk"]), ("indirect_attack: model only", F["risk"])]),
        ("Region-limited", "teal", [
            ("risk and safety: 22 regions", F["risk"]), ("protected_material: East US 2", F["risk"]), ("groundedness_pro: East US 2, Sweden Central", F["rag"])]),
        ("Preview", "orange", [
            ("groundedness_pro", F["rag"]), ("response_completeness", F["rag"]), ("prohibited_actions", F["risk"]), ("sensitive_data_leakage", F["risk"]),
            ("task_completion", F["agent"]), ("customer_satisfaction", F["agent"]), ("task_adherence", F["agent"]), ("intent_resolution", F["agent"]),
            ("output_quality", F["agent"]), ("tool_use_quality", F["agent"]), ("rubric", F["rubric"]), ("custom evaluators", F["custom"])]),
        ("Deprecated", "red", [("quality_grader (cannot be run)", F["agent"])]),
    ]
    lw = 400
    with cv.panel(0, y, title=None, theme="gray", style="dotted", fill="none", pad=20, w=W) as p:
        yy = p.iy
        for label, th, chips in rows:
            tt = Text_wrap(cv, p.ix, yy + 8, label, lw - 20, th)
            cf = ChipFlow([Chip(c, theme=ct, size=15, pad_y=5) for c, ct in chips], W - 40 - lw, gap=9)
            cf.place(cv, p.ix + lw, yy)
            h = max(cf.h, tt)
            yy += h + 16
    return p.bottom + 70


def Text_wrap(cv, x, y, text, w, theme, size=17):
    t = cv.text(x, y, wrapped(text, w, size), size=size, color=THEMES[theme].deep)
    return t.h


def catalog(cv: Canvas, y: float) -> float:
    cv.text(0, y, "The full built-in catalog by family (every evaluator listed on Learn)", size=24, color=THEMES["violet"].deep)
    y += 46
    pv = lambda name: (name + "\n(preview)", PREVIEW)
    # ------------------------------------------------------------- column 0
    general = fam_panel(
        cv, COLX[0], y, CW, "General purpose (2)",
        "LLM judge  |  English only  |  unreliable for very short responses (< ~20 tokens)  |  1-5 scale, default threshold 3", FAM["general"],
        [("Evaluator", 170), "Scores", ("Inputs / output", 280)],
        [["coherence", "Logical flow and organisation of ideas", "query + response, or messages; also conversation level"],
         ["fluency", "Grammar, vocabulary and readability", "response or messages; turn level only"]],
        [("General purpose evaluators", learn(E + "general-purpose-evaluators"))])
    sim = fam_panel(
        cv, COLX[0], general.bottom + 30, CW, "Textual similarity (6)",
        "All six generally available  |  only similarity needs a judge deployment (deployment_name)", FAM["sim"],
        [("Evaluator", 170), "Scores", ("Inputs / output", 290)],
        [["similarity", "AI-assisted semantic similarity to the ground truth (query-aware)", "query, response, ground_truth + deployment_name; 1-5 int, threshold 3"],
         ["f1_score", "Token-overlap F1 (precision + recall)", "ground_truth, response; 0-1, threshold 0.5"],
         ["bleu_score", "BLEU n-gram overlap (translation quality)", "same inputs; 0-1, threshold 0.5"],
         ["gleu_score", "Google-BLEU, sentence-level overlap", "same inputs; 0-1, threshold 0.5"],
         ["rouge_score", "ROUGE recall-oriented overlap; returns precision, recall and F1 (F1 primary)", "rouge_type required (rouge1 .. rouge5, rougeL); optional precision / recall / f1 thresholds (0.5 each)"],
         ["meteor_score", "METEOR: synonym, stemming and paraphrase aware", "same inputs; 0-1, threshold 0.5"]],
        [("Textual similarity evaluators", learn(E + "textual-similarity-evaluators"))])
    graders = fam_panel(
        cv, COLX[0], sim.bottom + 30, CW, "Azure OpenAI graders (4)",
        "OpenAI Evals API grader types - not azure_ai_evaluator  |  run locally or remotely  |  do NOT accept messages", FAM["graders"],
        [("Grader type", 140), ("Required parameters", 340), "Output"],
        [["label_model", "model, name, input, labels, passing_labels", "label; passes if it is in passing_labels"],
         ["score_model", "model, name, input; optional range (default [0, 1]), pass_threshold", "0-1 float; no pass / fail without a threshold"],
         ["string_check", "input, reference, operation: eq (case-sensitive exact), ne, like (wildcards), ilike (case-insensitive)", "1 or 0"],
         ["text_similarity", "input, reference, evaluation_metric (fuzzy_match, bleu, gleu, meteor, cosine, rouge_1 .. rouge_5, rouge_l), pass_threshold", "0-1 float"]],
        [("Azure OpenAI graders", learn(E + "azure-openai-graders"))],
        notes=["python_grader is named only on the cloud-evaluation-conversations page (as not accepting messages) and has no reference entry - treat as unverified."])
    # ------------------------------------------------------------- column 1
    rag = fam_panel(
        cv, COLX[1], y, CW, "RAG (6)",
        "Process = the retrieval step  |  System = the final response  |  context is a plain string: join chunks with a blank line", FAM["rag"],
        [("Evaluator", 168), ("Type", 78), "Scores", ("Inputs / output", 250)],
        [["retrieval", "Process", "Relevance of the retrieved chunks to the query (no ground truth)", "query, context; LLM judge, 1-5 -> pass / fail (3)"],
         ["document_retrieval", "Process", "Search quality vs labelled ground truth: Fidelity, NDCG (ndcg@3), XDCG (xdcg@3), Max Relevance (top1, top3), Holes",
          "retrieval_ground_truth + retrieved_documents; no model; label range 0-4 in the SDK; not messages"],
         ["groundedness", "System", "Response vs context, no fabrication (precision)", "response + context (recommended), optional query; agent mode: query, response, tool_definitions; 1-5 (3)"],
         [pv("groundedness_pro"), "System", "Strict groundedness through Azure AI Content Safety - no model deployment", "query, response, context; True / False; East US 2, Sweden Central"],
         ["relevance", "System", "Accuracy, completeness and direct relevance to the query", "query, response; 1-5 (3)"],
         [pv("response_completeness"), "System", "Covers the expected information (recall)", "ground_truth, response; 1-5"]],
        [("RAG evaluators", learn(E + "rag-evaluators"))])
    rubric = Card(CW, "Rubric evaluator", [
        "An LLM judge scores each applicable dimension 1-5; overall = weighted average normalised to 0-1; default pass threshold 0.5 (editable 0.0-1.0)",
        "Per-dimension reasons in properties.dimension_scores[]",
        "Rubric fields: id (stable slug), description, weight (generation: one criterion weighted 8-10, the others 1-6), always_applicable (default false; for a general-quality criterion)",
        "Auto-generate from a Foundry agent (instructions for prompt agents, description for hosted), an agent system prompt or reference files; optionally add production traces (traces alone are not enough) - or author it by hand",
        "Docs recommend rubric as the primary agent-quality measure, paired with built-ins for safety, groundedness and harm",
        "Usable in continuous evaluation (Monitor settings)",
    ], theme=FAM["rubric"], badge="preview", icon="metrics", src=[("Rubric evaluators", learn(E + "rubric-evaluators"))])
    rubric.place(cv, COLX[1], rag.bottom + 30)
    # ------------------------------------------------------------- column 2
    risk = fam_panel(
        cv, COLX[2], y, CW, "Risk and safety (10)",
        "Hosted Foundry evaluation-service models: no deployment_name  |  defect rate = % undesired content  |  also used inside the AI Red Teaming Agent", FAM["risk"],
        [("Evaluator", 210), ("Targets", 104), "Output"],
        [["hate_unfairness", "Model + agents", "Severity 0-7 (Very low 0-1, Low 2-3, Medium 4-5, High 6-7); default threshold 3, pass if score <= threshold"],
         ["sexual", "Model + agents", "Same 0-7 severity scale"],
         ["violence", "Model + agents", "Same 0-7 severity scale"],
         ["self_harm", "Model + agents", "Same 0-7 severity scale"],
         ["protected_material", "Model + agents", "Pass / fail; Azure AI Content Safety Protected Material for Text (lyrics, recipes, articles); East US 2 only"],
         ["indirect_attack (XPIA)", "Model only", "Fails if any of: manipulated content, intrusion, information gathering"],
         ["code_vulnerability", "Model + agents", "Fails if any of 19 subclasses; Python, Java, C++, C#, Go, JavaScript, SQL"],
         ["ungrounded_attributes", "Model + agents", "Boolean: emotional state or protected class detected AND ungrounded in context; needs query, response, context"],
         [pv("prohibited_actions"), "Agents only", "Pass / fail against a user-verified policy of prohibited actions and tool uses; query, response, tool_calls or messages"],
         [pv("sensitive_data_leakage"), "Agents only", "Pass / fail; exposure of financial, personal-identifier or health data"]],
        [("Risk and safety evaluators", learn(E + "risk-safety-evaluators"))],
        notes=["Required inputs for the 8 content evaluators: query + response, or messages. The text severity scales are defined per category on the page."])
    cvul = Card(CW, "code_vulnerability: the 19 subclasses", [
        ("para", "path-injection, sql-injection, code-injection, stack-trace-exposure, incomplete-url-substring-sanitization, flask-debug, "
                 "clear-text-logging-sensitive-data, incomplete-hostname-regexp, server-side-unvalidated-url-redirection, weak-cryptographic-algorithm, "
                 "full-ssrf, bind-socket-all-network-interfaces, client-side-unvalidated-url-redirection, likely-bugs, reflected-xss, "
                 "clear-text-storage-sensitive-data, tarslip, hardcoded-credentials, insecure-randomness", 0),
    ], theme=FAM["risk"], body_size=15, src=[("Risk and safety evaluators", learn(E + "risk-safety-evaluators"))])
    cvul.place(cv, COLX[2], risk.bottom + 30)
    # ------------------------------------------------------------- column 3
    agent = fam_panel(
        cv, COLX[3], y, CW, "Agent (13 listed)",
        "Behave like unit tests: binary pass / fail, or a scaled score turned into pass / fail by a threshold  |  System = end-to-end outcome, Process = step by step",
        FAM["agent"],
        [("Evaluator", 192), ("Type", 92), "Scores", ("Level", 122)],
        [[pv("task_completion"), "System", "Completed the task end-to-end with a usable deliverable (binary)", "turn + conversation"],
         [pv("customer_satisfaction"), "System", "Holistic satisfaction on 6 dimensions: helpfulness, completeness, clarity, tone, resolution, adaptability (1-5 Likert)", "turn + conversation"],
         [pv("task_adherence"), "System", "Follows system-message rules, procedures and policy (binary)", "turn"],
         [pv("intent_resolution"), "System", "Identifies and addresses the user's intent (1-5 -> pass / fail)", "turn"],
         ["task_navigation_efficiency", "System", "Tool-call sequence vs the expected path; needs expected_actions + actions or messages; matching_mode exact_match, in_order_match, any_order_match", "turn"],
         ["tool_call_accuracy", "Process", "Right tool calls with correct parameters and no redundancy (1-5 -> pass / fail)", "turn"],
         ["tool_selection", "Process", "Correct and necessary tools only (binary)", "turn"],
         ["tool_input_accuracy", "Process", "All parameters correct on 6 strict criteria: groundedness, type, format, required, no unexpected, value appropriateness (binary)", "turn"],
         ["tool_output_utilization", "Process", "Correctly understands and uses tool results (binary)", "turn"],
         ["tool_call_success", "Process", "Tool calls succeeded without technical errors or exceptions (binary)", "turn"],
         [("output_quality\n(preview, composite)", PREVIEW), "System + quality", "ONE judge call batching Fluency, Coherence, Intent Resolution, Task Adherence, Groundedness, Task Completion", "turn + conversation"],
         [("tool_use_quality\n(preview, composite)", PREVIEW), "Process", "ONE judge call batching Tool Call Accuracy, Tool Call Success, Tool Input Accuracy, Tool Output Utilization, Tool Selection", "turn + conversation"],
         [("quality_grader\n(deprecated)", DEPREC), "-", "Relevance, abstention, answer completeness, groundedness, context coverage in one evaluator - can no longer be run", "-"]],
        [("Agent evaluators", learn(E + "agent-evaluators"))])
    # ------------------------------------------------------------- extras that fill the short columns
    comp = Card(CW, "Composite evaluators: one judge call, many scores", [
        "Primary result = 1 only if EVERY applicable component passes; components that don't apply are skipped; all skipped -> not_applicable",
        "Outputs: <component>_score, _result, _reason, _status, plus <composite>_reason and <composite>_properties",
        "output_quality defaults: Fluency 1-5 (3), Coherence 1-5 (3), Intent Resolution 1-5 (3), Task Adherence 0/1 (1), Groundedness 1-5 (3), Task Completion 0/1 (1)",
        "tool_use_quality defaults: Tool Call Accuracy 1-5 (3); Tool Call Success, Tool Input Accuracy, Tool Output Utilization, Tool Selection 0/1 (1)",
        "Use the primary result as a strict quality gate and the components to find the failing dimension",
        "Judge: a GPT-5.6-family model; gpt-5.6-luna is the lowest-cost option that keeps evaluation quality high",
    ], theme=FAM["agent"], badge="preview", icon="metrics", src=[("Composite evaluators", learn(E + "agent-evaluators"))])
    comp.place(cv, COLX[1], rubric.bottom + 30)
    tools = Card(CW, "Agent evaluators and tools: what is supported", [
        "# Supported tools",
        "File Search, Function tool, MCP, Knowledge-based MCP",
        "# Limited support - avoid tool_call_accuracy, tool_input_accuracy, tool_output_utilization, tool_call_success and groundedness with",
        "Azure AI Search, Bing Grounding, Bing Custom Search, SharePoint Grounding, Code Interpreter, Fabric Data Agent, Web Search",
        "+ Workaround: wrap them as user-defined function tools",
        "For a textual agent answer you can also apply Relevance and Groundedness, which accept agentic inputs",
    ], theme=FAM["agent"], icon="toolbox", src=[("Agent evaluators", learn(E + "agent-evaluators"))])
    tools.place(cv, COLX[2], cvul.bottom + 30)
    qg = Note(CW, "The evaluator overview still lists Quality Grader as (preview). The agent-evaluators page says it is deprecated and can no longer be run in an evaluation, "
                  "and cloud-evaluation-conversations also calls it deprecated. Treat it as deprecated; use output_quality instead.",
              kind="warn", title="Docs disagree: Quality Grader",
              src=[("Built-in evaluators", learn("concepts/built-in-evaluators")), ("Agent evaluators", learn(E + "agent-evaluators"))])
    qg.place(cv, COLX[3], agent.bottom + 30)
    dr = Note(CW, "builtin.deflection_rate is accepted as a conversation-level evaluator on the cloud-evaluation pages but is not described in the evaluator reference - its purpose, scale and threshold are undocumented.",
              kind="info", title="Named but not documented")
    dr.place(cv, COLX[3], qg.bottom + 22)
    return max(comp.bottom, tools.bottom, dr.bottom, graders.bottom)


def custom_section(cv: Canvas, y: float) -> float:
    rows = [
        [("How it works", "orange"), "A Python function grade(sample, item) -> float", "A judge prompt with {{query}}-style variables", "An external HTTP POST endpoint that you own"],
        [("Score", "orange"), "0.0-1.0, continuous", "Ordinal, continuous or binary; returns {\"result\", \"reason\"}",
         "JSON {schema_version: \"0.0.1\", score, reason, status: completed | error | skipped, properties, threshold, passed}"],
        [("Required init parameters", "orange"), "pass_threshold, deployment_name (the schema requires it even though no LLM runs)", "deployment_name, threshold", "Supplied through data_mapping keys"],
        [("Limits", "orange"), "Code < 256 KB; 2 minutes per call; no network; 2 GB RAM, 1 GB disk, 2 CPU; exceptions and timeouts score 0.0 plus an error", "The judge model costs per call",
         "30-second timeout; auth = API key or Entra ID project connection (ApiKey / CustomKeys category); Entra needs an app registration, Easy Auth and an app role for the project managed identity"],
    ]
    t = Table([("Custom evaluators (preview)", 270), ("Code-based", 1000), ("Prompt-based", 760), ("Endpoint-based", 1290)], rows, w=W,
              theme="orange", size=14, head_size=17, first_col_theme="orange",
              title="Custom evaluators (preview): three kinds, registered in the project evaluator catalog", title_size=24)
    t.place(cv, 0, y)
    y2 = t.bottom + 12
    tt = cv.text(0, y2, "Register: Evaluation > Evaluator catalog > Custom evaluator > Create, or the SDK project_client.beta.evaluators.create_version.", size=15, color=INK)
    src_lines(cv, 0, tt.bottom + 4, [("Custom evaluators", learn(E + "custom-evaluators"))])
    y3 = tt.bottom + 34
    pk = Card(span(2), "Code-based sandbox packages", [
        ("para", "numpy 2.2.4, scipy 1.15.2, pandas 2.2.3, scikit-learn 1.6.1, rapidfuzz 3.10.1, sympy 1.13.3, jsonschema 4.23.0, pydantic 2.10.6, deepdiff 8.4.2, "
                 "nltk 3.9.1, rouge-score 0.1.2, pyyaml 6.0.2 - plus the NLTK corpora punkt, stopwords, wordnet, omw-1.4 and names.", 0),
    ], theme="orange", icon="code", src=[("Custom evaluators", learn(E + "custom-evaluators"))])
    cl = Card(span(2), "Custom evaluators at conversation level and in monitoring", [
        "Set evaluation_level=\"conversation\"; grade() then reads item[\"messages\"]",
        "Add custom evaluators to continuous evaluation: Monitor > Settings > Continuous evaluation > Add evaluator(s)",
    ], theme="orange", icon="scheduler", src=[("Custom evaluators", learn(E + "custom-evaluators"))])
    _, b = row(cv, 0, y3, [pk, cl], gap=G)
    return b + 90


# ============================================================================================ 3. run
def run_section(cv: Canvas, y: float) -> float:
    y = hdr(cv, y, 3, "Run it", "Every door ends in the same Evals API - choose by rhythm: once, on every pull request, on a schedule or on live traffic")
    azd = Card(CW, "azd ai agent eval", [
        "Flow: azd ai agent init -> azd provision -> azd deploy -> azd ai agent eval generate -> eval run -> eval update; optional azd ai agent optimize --config eval.yaml",
        "Extension azure.ai.agents >= 0.1.40-preview (azd ext install azure.ai.agents)",
        "eval generate writes eval.yaml (agent target, dataset ref, evaluator refs, options) plus local datasets/ and evaluators/ (rubric_dimensions.json); registered service versions stay the source of truth",
        "Flags: --gen-instruction, --eval-model, --max-samples (15-1,000), --dataset, --evaluator builtin.<name> or <custom-name> (repeatable), --no-wait, --reset-defaults, --out-file",
        "eval list; eval show <eval-id> --eval-run-id <id>",
        "Works with hosted agents (responses or invocations protocol; synchronous, non-streaming) and prompt agents; role: Foundry User on the Foundry resource",
        "! A2A / Activity protocol, streaming or long-running agents: use trace evaluation instead",
        "! The tracing quickstart installs microsoft.foundry (azd >= 1.36.0) instead - extension naming differs between pages",
    ], theme="violet", badge="preview", icon="azd", src=[("azd evaluation", learn(OH + "azure-developer-cli-evaluation"))])
    cicd = Card(CW, "CI/CD gates", [
        "GitHub Action microsoft/ai-agent-evals@v3-beta; Azure DevOps task AIAgentEvaluation@2 (marketplace ms-azure-exp-external.microsoft-extension-ai-agent-evaluation)",
        "Inputs: azure-ai-project-endpoint, deployment-name, data-path, agent-ids (name:version, comma-separated), optional baseline-agent-id",
        "data-path is a JSON file: name, evaluators[], data[], optional openai_graders, evaluator_parameters, data_mapping",
        "Output: a step summary with scores, confidence intervals and a pairwise statistical comparison between agents",
        "Auth: Microsoft Entra ID (OIDC federated credential or ARM service connection); the pipeline workload identity needs Foundry User on the Foundry resource or project",
        "+ Docs tip: don't run evaluation on every commit",
    ], theme="violet", badge="preview", icon="github", src=[("GitHub Actions", learn("how-to/evaluation-github-action")),
                                                              ("Azure DevOps", learn("how-to/evaluation-azure-devops"))])
    cont = Card(CW, "Continuous and scheduled evaluation", [
        "Connect Application Insights, then create an eval with data source azure_ai_source (scenario responses)",
        "evaluation_rules.create_or_update(ContinuousEvaluationRuleAction(eval_id, max_hourly_runs=100), event type RESPONSE_COMPLETED, filter agent_name); max_hourly_runs defaults to 100",
        "Recurring: beta.schedules with RecurrenceTrigger, e.g. DailyRecurrenceSchedule(hours=[9])",
        "Results chart on the Monitor tab; Monitor > Settings > Continuous evaluation > Add evaluator(s) accepts built-in, rubric and custom evaluators",
        "Rules run as the project managed identity - grant it Foundry User",
        "! The JS SDK has no scheduled evaluation - use the portal",
        "Red team scans (preview) schedule from the same Monitor settings",
    ], theme="violet", icon="scheduler", src=[("Monitor agents", learn(OH + "how-to-monitor-agents-dashboard"))])
    human = Card(CW, "Human evaluation", [
        "Needs Application Insights; templates are created by Foundry Project Manager (or higher)",
        "Reviewers need Foundry User (+ Reader on the account) for the Preview web app: Preview > Send > Feedback panel > Save",
        "Question types: thumbs up / down, slider (1-5), multiple choice, free-form text",
        "! Only one template can be active at a time",
        "Results: Evaluation Results JSON (timestamp, prompt, response, questions, answers) and Download Results (CSV)",
        "Stored in Application Insights; retention follows App Insights",
        "! Not supported for external agents",
    ], theme="violet", badge="preview", icon="users", src=[("Human evaluation", learn(OH + "human-evaluation"))])
    bench = Card(CW, "Benchmark evaluations", [
        "A predefined package: dataset + task category + evaluation logic",
        "Build > Evaluations > Create, or the agent's Evaluation tab; target = an agent (versions) or model deployments",
        "A judge model is chosen when the benchmark uses model grading (REST grader_model = deployment or connection/deployment; missing -> BenchmarkGraderModelRequired)",
        "Results at group and run level with token usage (system + evaluation tokens); download results and user logs; raw JSON",
        "Use it to compare deployments and to detect fine-tune regressions",
        "The current portal flow focuses on built-in benchmark datasets and evaluators",
    ], theme="violet", badge="preview", icon="dashboard", src=[("Benchmark evaluations", learn(OH + "benchmark-evaluations"))])
    bt = Table([("Benchmark", 200), ("Items", 90), "Evaluator or note"],
               [["AIME 2025", "30", "reasoning and math"], ["BBEH", "4,520", "builtin.bbeh"], ["BIG-Bench Hard", "934", "builtin.regex_match"],
                ["ChemBench", "2,785", ""], ["FrontierScience", "160", ""], ["GPQA Diamond", "198", "builtin.regex_match"],
                ["MuSR", "756", "builtin.regex_match"], ["TruthfulQA", "790", "builtin.truthful_qa; e.g. 82% = 645 of 790"]],
               w=CW, theme="violet", size=14, head_size=15, title="Benchmarks the portal shows", title_size=22)
    adm = Card(CW, "Admin-connected models", [
        "A model behind an enterprise AI gateway (Azure API Management or a non-Azure gateway) is referenced as <connection-name>/<deployment-name>",
        "Use it as the judge (initialization_parameters.model), the target (target.model) or the simulator (model_configuration.model)",
        "The gateway must expose the Chat Completions API",
        "! Not available for synthetic data generation",
    ], theme="violet", badge="preview", icon="apim", src=[("Admin-connected models", learn(OH + "evaluate-admin-connected-models"))])
    tr = Table([("Symptom", 190), "Likely cause", "Action"],
               [["Run stays pending", "High load or queued jobs", "Refresh, verify quota, resubmit if prolonged"],
                ["Metrics missing", "Not selected at creation", "Re-run and select the metrics"],
                ["All safety metrics zero", "Category disabled or unsupported model", "Confirm model and evaluator support"],
                ["Groundedness unexpectedly low", "Retrieval or context incomplete", "Check context construction and retrieval latency"],
                ["HTTP 429 on run creation", "Tenant, subscription or project rate limit", "Honor retry-after; exponential backoff"],
                ["HTTP 400 on azure_ai_responses", "file_id used", "Pass file_content"],
                ["403 Public access is disabled", "VNet project without a private endpoint", "Configure a private endpoint"]],
               w=CW, theme="gray", size=14, head_size=15, title="Troubleshooting quick hits", title_size=22)
    low = stack(cv, y, [[azd, bench], [cicd, bt], [cont, tr], [human, adm]])
    y3 = low + 70

    # recipes
    cv.text(0, y3, "Four recipes - one engine, four rhythms", size=28, color=THEMES["violet"].deep)
    y3 += 52
    R = [
        ("1  Pre-production agent evaluation", "green",
         ["Build a dataset (synthetic from the agent definition and / or traces)", "evals.create: data_source_config + testing_criteria",
          "evals.runs.create with the agent as target", "Poll until completed", "Read report_url and the pass rate", "Cluster analysis",
          "Fix, then re-run the same recipe", "Compare the runs with the t-test"]),
        ("2  Production monitor", "teal",
         ["Connect Application Insights", "Create an eval: azure_ai_source, scenario responses",
          "evaluation_rules.create_or_update(ContinuousEvaluationRuleAction(eval_id, max_hourly_runs=100), RESPONSE_COMPLETED, filter agent_name)",
          "Charts on the Monitor tab"]),
        ("3  CI gate", "blue",
         ["Pull request", "GitHub Action ai-agent-evals", "Runs the agent on the data-path queries",
          "Report: scores, confidence intervals, pairwise comparison", "Fail the check or inspect"]),
        ("4  Simulation", "violet",
         ["Seeds (portal-generated or JSONL)", "A simulator model plays the user against the agent target",
          "Conversation-level evaluators (Customer Satisfaction, Task Completion, Output Quality ...)", "Optional persisted conversation dataset"]),
    ]
    TW, BW, CG = 400, 316, 40
    with cv.panel(0, y3, title=None, theme="gray", style="dotted", pad=22, w=W) as p:
        yy = p.iy
        for title, th, steps in R:
            tb = Box(TW, title, theme=th, size=22, fill="solid", min_h=100).place(cv, p.ix, yy)
            _, bb = chain(cv, p.ix + TW + 56, yy, steps, BW, th, gap=CG, size=16, min_h=100)
            arrow(cv, [(tb.right + 4, tb.cy), (p.ix + TW + 52, tb.cy)], sw=2.5)
            yy = max(bb, tb.bottom) + 24
    return p.bottom + 70


# ============================================================================================ 4. review
def review_section(cv: Canvas, y: float) -> float:
    y = hdr(cv, y, 4, "Review and improve", "Read the aggregate, drill into rows, compare runs, cluster the failures - then change one thing and go around again")
    sdk = Card(CW, "Results in code (SDK)", [
        "Poll evals.runs.retrieve until completed, failed or canceled; open run.report_url",
        "Rows: evals.runs.output_items.list",
        "Aggregates: result_counts {passed, failed, total}; per_testing_criteria_results [{name, passed, failed, pass_rate}]",
        "Model-target runs may add latency.target {p50_ms, p95_ms, sample_count} and estimated_cost.target",
        "Estimated cost: Global Standard deployments only; marked partial when some models can't be priced (unpriced_models); list prices, no discounts, excludes evaluator tokens",
        "Cloud results are stored in your Foundry project; they also go to Application Insights if connected",
    ], theme="blue", icon="code", src=[("Cloud evaluation results", learn(OH + "cloud-evaluation-results"))])
    portal = Card(CW, "Results in the portal", [
        "Evaluation page > a run: Name, Target, Dataset (download as CSV), Status (Running, Completed, Failed; the list also shows Partial), Evaluation tokens, Target tokens, Scores",
        "Hover a score for token usage; open a run for row-level query, response, ground truth, score and explanation",
        "Select two or more runs > Compare: side-by-side view with t-test colour codes; hover a cell for sample size and p-value",
        "Set a baseline run to see how every other run deviates",
        "! The comparison view isn't saved - reselect the runs to regenerate it",
    ], theme="blue", icon="dashboard", src=[("See evaluation results", learn("how-to/evaluate-results"))])
    tt = Table([("Legend", 170), "Meaning"],
               [[("ImprovedStrong", "green"), "p <= 0.001, moved in the desired direction"],
                [("ImprovedWeak", "green"), "0.001 < p <= 0.05, moved in the desired direction"],
                [("DegradedStrong", "red"), "p <= 0.001, moved in the wrong direction"],
                [("DegradedWeak", "red"), "0.001 < p <= 0.05, moved in the wrong direction"],
                [("ChangedStrong", "blue"), "p <= 0.001, desired direction is neutral"],
                [("ChangedWeak", "blue"), "0.001 < p <= 0.05, desired direction is neutral"],
                [("Inconclusive", "gray"), "Too few examples, or p >= 0.05"]],
               w=CW, theme="violet", size=14, head_size=15, title="Compare runs: the t-test legend", title_size=22)
    cl = Card(CW, "Cluster analysis", [
        "Select one or more completed runs > Cluster analysis > pick a deployed model > Generate; the setup window shows estimated time and token usage",
        "Summary stats: total samples, clusters, passed / failed, average score",
        "A map of dots: embedding-based clustering of outputs and feedback; click through cluster -> subcluster -> entry (conversation, scores, evaluators, timestamps, agent and trace IDs)",
        "Clusters carry a description of the likely cause and recommendations; filter or colour by cluster, evaluator, score or agent ID",
        "! The result is NOT stored - download it before you leave the page",
    ], theme="teal", badge="preview", icon="search", src=[("Cluster analysis", learn(OH + "cluster-analysis"))])
    low = stack(cv, y, [[sdk], [portal], [tt], [cl]])
    return low + 70


# ============================================================================================ ops
AM = ["Brazil South", "Canada Central", "Canada East", "Central US", "East US", "East US 2", "North Central US", "South Central US",
      "West Central US", "West US", "West US 2", "West US 3"]
EU = ["France Central", "Germany West Central", "Italy North", "North Europe", "Norway East", "Poland Central", "Spain Central",
      "Sweden Central", "Switzerland North", "Switzerland West", "UK South", "West Europe"]
AP = ["Australia East", "Central India", "East Asia", "Japan East", "Japan West", "Korea Central", "South India", "Southeast Asia"]
ME = ["South Africa North", "UAE North"]
ALL = AM + EU + AP + ME
PLAY = {"East US 2", "West US", "West US 2", "West US 3", "Central US", "East US", "North Central US", "South Central US",
        "France Central", "Norway East", "Sweden Central", "Germany West Central", "Italy North", "Poland Central", "Spain Central"}
BATCH = set(ALL) - {"Switzerland West"}
RISK = (set(AM) - {"West US 2"}) | {"France Central", "Germany West Central", "Italy North", "Norway East", "Poland Central", "Spain Central",
                                     "Sweden Central", "Switzerland North", "Switzerland West", "West Europe", "Australia East"}
DATA = (set(AM) - {"West US 2"}) | (set(EU) - {"North Europe", "Switzerland West"}) | {"Australia East", "Japan East", "Korea Central", "South India", "Southeast Asia"} | set(ME)
VNET = (set(AM) - {"Central US", "West Central US"}) | (set(EU) - {"North Europe", "Switzerland West"}) | {"Australia East", "Japan East", "Korea Central", "South India", "Southeast Asia"} | set(ME)
assert (len(ALL), len(PLAY), len(BATCH), len(RISK), len(DATA), len(VNET)) == (34, 15, 33, 22, 28, 27)


def region_table(names, title):
    mk = lambda s, n: CHECK if n in s else ""
    rows = [[n, mk(PLAY, n), mk(BATCH, n), mk(RISK, n), mk(DATA, n), mk(VNET, n)] for n in names]
    cols = [("Region", 214), ("Agent playground", 108), ("Batch", 90), ("Risk and safety", 108), ("Data generation", 108), ("VNet", 90)]
    return Table(cols, rows, w=CW, theme="indigo", size=14, head_size=14, pad_y=5, title=title, title_size=22,
                 first_col_theme="indigo", align=["left"] + ["center"] * 5)


def ops_section(cv: Canvas, y: float) -> float:
    y = hdr(cv, y, None, "Operating the workbench: permissions, limits, storage, network and regions",
            "Facts as of 2026-11-03 - rate limits and regions change; check the linked pages before you plan capacity")
    perm = Table(
        [("Scenario", 380), ("Identity", 330), "Role and scope"],
        [
            ["Most evaluation workflows", "You", "Foundry User on the project"],
            ["Evaluation invokes a model deployment (judge or target)", "You", "Foundry User at the Foundry ACCOUNT scope - a project-only assignment does not authorize model inference"],
            ["Continuous and scheduled rules", "Project managed identity", "Foundry User"],
            ["Trace evaluation and dataset from traces", "Project managed identity",
             "Reader on Application Insights; + Privileged Monitoring Data Reader if protected; + Log Analytics Reader on the workspace if 'Require workspace permissions'; Log Analytics Data Reader if DataActionsOnly"],
            ["Your own storage through Entra ID", "Project managed identity", "Storage Blob Data Contributor on the storage account (permissions page) - docs disagree, see below"],
            ["Synthetic data generation", "You", "Foundry User (plus a Responses-API-capable model)"],
            ["azd ai agent eval", "You", "Foundry User on the Foundry resource"],
            ["CI/CD pipeline", "Pipeline workload identity (OIDC or ARM service connection)", "Foundry User on the Foundry resource or project"],
            ["Human evaluation", "Builders / reviewers", "Foundry Project Manager (or higher) builds templates; reviewers need Foundry User + Reader on the account"],
            ["VNet evaluation setup", "Project managed identity", "Foundry User at the Foundry resource scope"],
            ["Assigning any of the above", "You", "Needs Microsoft.Authorization/roleAssignments/write"],
        ], w=span(2), theme="red", size=14, head_size=15, first_col_theme="red",
        title="Permissions for evaluation workflows (roles were renamed: Foundry User = formerly Azure AI User)", title_size=22)
    perm.place(cv, 0, y)
    lim = Card(CW, "Limits and rate limits", [
        "Maximum size per row: 2 MB; maximum rows per batch evaluation: 100,000",
        "Run creation is rate-limited at the tenant, subscription and project level",
        "Over the limit: the response carries a retry-after header and rate-limit details - use exponential backoff",
        "Judge-model quota (tokens per minute) is the usual bottleneck",
        "Cancel a stuck run: evals.runs.cancel(run_id, eval_id=...)",
        "The page publishes only the two size limits - no per-minute run quota",
    ], theme="yellow", icon="quotas", src=[("Rate limits, regions, VNet", learn("concepts/evaluation-regions-limits-virtual-network"))])
    byo = Card(CW, "Bring your own storage", [
        "Evaluation needs a storage account linked to the project through a connection (key or Entra ID)",
        "The account must be accessible to all projects; VNet projects use template 15a",
        "Dataset creation requires public network access on the BYO storage account",
        "! Entra role: Contributor on the permissions page vs Owner (account + project resource) on the regions page",
    ], theme="cyan", icon="storage", src=[("BYO storage", learn("concepts/evaluation-regions-limits-virtual-network") + "#bring-your-own-storage")])
    hh = max(perm.h, lim.h, byo.h)
    lim.place(cv, COLX[2], y, h=hh)
    byo.place(cv, COLX[3], y, h=hh)
    y2 = y + hh + 56

    cv.text(0, y2, "Region matrix: where each evaluation capability runs (tick = listed on the regions page)", size=26, color=THEMES["indigo"].deep)
    y2 += 48
    t1 = region_table(AM, "Americas (12)")
    t2 = region_table(EU, "Europe (12)")
    t3 = region_table(AP + ME, "Asia Pacific (8) and Middle East and Africa (2)")
    t1.place(cv, COLX[0], y2)
    t2.place(cv, COLX[1], y2)
    t3.place(cv, COLX[2], y2)
    fine = Card(CW, "Region fine print", [
        "Counts tallied from the Learn tables: agent playground 15, batch 33, risk and safety 22, data generation 28 (synthetic data and traces-to-dataset), VNet evaluation 27",
        "Risk and safety column: hate and unfairness, sexual, violent, self-harm, indirect attack, code vulnerabilities, ungrounded attributes",
        "Groundedness Pro: East US 2 and Sweden Central only; Protected material: East US 2 only",
        "AI red teaming (cloud): East US 2 and North Central US on this page; the red-teaming concepts page lists five regions (see the AI Red Teaming explainer)",
        "Local red-teaming regions and the Azure OpenAI graders regional list are in the Foundry (classic) pages",
    ], theme="indigo", icon="regions", src=[("Regional availability", learn("concepts/evaluation-regions-limits-virtual-network") + "#regional-availability")])
    fine.place(cv, COLX[3], y2)
    y3 = max(t1.bottom, t2.bottom, t3.bottom, fine.bottom) + 56

    vn = Card(CW, "Virtual network", [
        "Needs network injection through subnet delegation; evaluation-only Bicep template 15a; capability host at account and project level",
        "Assign Foundry User to the project managed identity at the Foundry resource scope during setup",
        "Public access disabled: 403 'Public access is disabled. Please configure private endpoint.'",
        "Custom DNS: Azure DNS Private Resolver or a conditional forwarder to 168.63.129.16; diagnostic script vnet-project-setup-diagnostic",
        "If Application Insights is connected, evaluation data is sent to it",
    ], theme="indigo", icon="vnet", src=[("Evaluation virtual network", learn("concepts/evaluation-virtual-network"))])
    dis = Table(
        [("Topic", 280), ("One page says", 700), ("Another page says", 760), "How this canvas treats it"],
        [
            [("Quality Grader", "orange"), "Built-in evaluators overview: listed as (preview)", "Agent evaluators: deprecated, can no longer be run; cloud-evaluation-conversations also says deprecated", "Shown as deprecated; use output_quality"],
            [("Turn-only evaluator in a conversation-level run", "orange"), "Built-in evaluators and cloud-evaluation-conversations: skipped, not failed", "Troubleshooting: causes an incompatible evaluation level error", "Keep conversation-level runs to conversation-capable evaluators"],
            [("Storage role for BYO storage (Entra ID)", "orange"), "Permissions and Troubleshooting pages: Storage Blob Data Contributor for the project managed identity", "Regions, limits and VNet page: Storage Blob Data Owner on the storage account and on the Foundry project resource", "Both quoted - pick deliberately; prefer the narrower role unless a run fails"],
            [("azd extension for evaluation", "orange"), "Evaluation page: azure.ai.agents >= 0.1.40-preview", "Tracing hosted-agent quickstart: microsoft.foundry with azd >= 1.36.0", "Both quoted - check which extension your azd installs"],
            [("Minimum sample counts", "orange"), "Synthetic-query runs: samples_count 15-1,000; azd --max-samples 15-1,000", "Dataset generation jobs: max_samples 1-1,000", "Different features, different minimums - easy to mix up"],
            [("Evaluator IDs", "orange"), "Most pages show builtin.<name> verbatim", "tool_call_accuracy, tool_selection, tool_input_accuracy, tool_output_utilization, tool_call_success, response_completeness and groundedness_pro appear without the prefix", "Assumed to follow builtin.<name>; confirm in the evaluator catalog"],
            [("deflection_rate and python_grader", "orange"), "Accepted by the cloud-evaluation pages (deflection_rate at conversation level; python_grader among graders that don't take messages)", "Neither has an entry in the reference pages (4 grader types are documented)", "Listed as undocumented / unverified"],
        ], w=span(3), theme="orange", size=14, head_size=15, first_col_theme="orange",
        title="Where the docs disagree or stay silent (as of 2026-11-03) - verify before you rely on it", title_size=24)
    vn.place(cv, COLX[0], y3, h=max(vn.h, dis.h))
    dis.place(cv, COLX[1], y3)
    return max(vn.bottom, dis.bottom) + 70


# ============================================================================================ sources
def sources_section(cv: Canvas, y: float) -> None:
    sources(cv, 0, y, [
        ("Evaluation in Microsoft Foundry", learn("concepts/evaluation-overview")),
        ("Built-in evaluators reference", learn("concepts/built-in-evaluators")),
        ("Agent evaluators", learn(E + "agent-evaluators")),
        ("Risk and safety evaluators", learn(E + "risk-safety-evaluators")),
        ("Custom evaluators", learn(E + "custom-evaluators")),
        ("Evaluation datasets", learn(OH + "evaluation-datasets")),
        ("Cloud evaluation with the Foundry SDK", learn(OH + "cloud-evaluation")),
        ("See evaluation results in the portal", learn("how-to/evaluate-results")),
        ("Cluster analysis", learn(OH + "cluster-analysis")),
        ("Run agent evaluations with the azd CLI", learn(OH + "azure-developer-cli-evaluation")),
        ("Run evaluations in GitHub Actions", learn("how-to/evaluation-github-action")),
        ("Run evaluations in Azure DevOps", learn("how-to/evaluation-azure-devops")),
        ("Rate limits, regions and virtual network", learn("concepts/evaluation-regions-limits-virtual-network")),
        ("Permissions for evaluation workflows", learn(OH + "evaluation-permissions")),
    ], w=W, cols=4)


# ============================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Evaluation in depth",
        "Evaluators, datasets, run modes, results and CI/CD - how Foundry measures models and agents (facts as of 2026-11-03)", w=W)
    y = bottom + 46
    y = summary(cv, y)
    y = workbench(cv, y)
    y = data_section(cv, y)
    y = hdr(cv, y, 2, "Pick the evaluators",
            "IDs follow builtin.<name>.  Orange cell = preview, red cell = deprecated.  Process = one step (retrieval, tool calls); System = the final outcome")
    y = combos(cv, y)
    y = decision_matrix(cv, y)
    y = constraint_map(cv, y)
    y = catalog(cv, y) + 90
    y = custom_section(cv, y)
    y = run_section(cv, y)
    y = review_section(cv, y)
    y = ops_section(cv, y)
    sources_section(cv, y)
