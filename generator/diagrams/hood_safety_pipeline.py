"""Under the hood: the inline safety pipeline - four gates, annotate vs block, streaming modes, hosted-agent guardrails.

Evidence convention (same as the other 'under the hood' canvases):
  solid border + hatch  = documented on Microsoft Learn
  dashed border + soft  = only a video / blog says it (labelled "(video/blog)")
  dotted grey + "?"     = not documented anywhere checked (or inferred: said so in the box)
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-safety-pipeline",
    title="Safety pipeline: inline guardrails under the hood",
    section="8", order=7,
    description="One agent turn through the four guardrail gates - Prompt Shields, harm classifiers, protected material, PII and "
                "task adherence - annotate vs block, default vs asynchronous streaming, and the hosted-agent traps: an inert "
                "invocations policy, a bad policy ID that fails open, bodies over 2 MB, and the agent guardrail that overrides the model's.",
    tags=["guardrails", "content safety", "prompt shields", "hosted agents", "egress", "streaming"],
)

W = 3160
GREY = "#868e96"
GA_C = "#2f9e44"      # arrow colour: content passes the gate
HIT_C = "#e03131"     # arrow colour: a control hit with Annotate and block

# ---------------------------------------------------------------- citations (label, url)
L_INTERV = ("Intervention points and controls", learn("guardrails/intervention-points"))
L_OVERVIEW = ("Guardrails and controls overview", learn("guardrails/guardrails-overview"))
L_DEFAULT = ("Default safety policies", learn("guardrails/default-safety-policies"))
L_TASK = ("Task adherence", learn("guardrails/task-adherence"))
L_3P = ("Third-party integrations", learn("guardrails/third-party-integrations"))
L_SHIELDS = ("Prompt Shields", learn("openai/concepts/content-filter-prompt-shields"))
L_PII = ("Personal data (PII) detection", learn("openai/concepts/content-filter-personal-information"))
L_STREAM = ("Content streaming", learn("openai/concepts/content-streaming"))
L_HOSTED = ("Hosted agent content safety overview", learn("agents/concepts/hosted-agent-guardrails"))
L_ADD = ("Add guardrails to a hosted agent", learn("agents/how-to/add-hosted-agent-guardrails"))
L_INSTANT = ("Instant models", learn("concepts/instant-models"))
L_MANAGED = ("Managed compute", learn("concepts/managed-compute-overview"))

U_BLOG = "https://devblogs.microsoft.com/foundry/hosted-agents-build26/"
U_MECH = "https://www.youtube.com/watch?v=iR7_57lJOz8"
U_BRK205 = "https://www.youtube.com/watch?v=oOO6OG4biEY"


# ---------------------------------------------------------------- evidence-styled blocks
def retag(card, prefix):
    """Card.src lines always read 'Learn: ...'; relabel them for video / blog evidence."""
    card.src_lines = [(t.replace("Learn: ", f"{prefix}: ", 1), u, y) for (t, u, y) in card.src_lines]
    return card


def vb(w, title, body, *, theme="yellow", src=(), prefix="Video", **kw) -> Card:
    """Video / blog only: dashed border, soft fill, '(video/blog)' in the title."""
    return retag(Card(w, "(video/blog) " + title, body, theme=theme, dash="dashed", fill="soft", src=src, **kw), prefix)


def nd(w, title, body, **kw) -> Card:
    """Not documented: dotted grey, empty fill, '?' in the title."""
    body = [("para", b) for b in ([body] if isinstance(body, str) else body)]
    kw.setdefault("title_color", GREY)
    return Card(w, "? " + title, body, theme="gray", dash="dotted", fill="none", body_color=MUTED, **kw)


def nd_box(w, label, sub, h=None) -> Box:
    return Box(w, "? " + label, sub=sub, theme="gray", dash="dotted", fill="none", size=17, sub_size=14, h=h)


def evidence_key(cv: Canvas, right: float, y: float) -> None:
    specs = [("solid", "Documented on Learn", ""), ("dashed", "Video or blog only (video/blog)", ""),
             ("dotted", "Not documented", "?")]
    widths = [64 + 14 + text_size(s[1], 15)[0] for s in specs]
    total = sum(widths) + 36 * (len(specs) - 1)
    x = right - total
    cv.text(x, y, "Evidence key", size=15, color=MUTED)
    cx, cy = x, y + 26
    for (dash, label, mark), w in zip(specs, widths):
        if dash == "solid":
            cv.rect(cx, cy, 64, 32, stroke="#c2255c", fill="#fcc2d7", style="hachure", sw=2)
        elif dash == "dashed":
            cv.rect(cx, cy, 64, 32, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, cy, 64, 32, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            mw, mh = text_size(mark, 20)
            cv.text(cx + (64 - mw) / 2, cy + (32 - mh) / 2, mark, size=20, color=GREY)
        cv.text(cx + 78, cy + 5, label, size=15, color=INK)
        cx += w + 36


def banner(cv: Canvas, y: float, letter: str, title: str, sub: str, theme: str = "pink") -> float:
    """Section banner with a lettered marker; returns the y where content can start."""
    numbered(cv, 24, y + 30, letter, theme=theme, d=46, size=26)
    _, bottom = section_header(cv, 62, y, title, sub, size=34, sub_size=17, w=W - 62)
    return bottom + 20


def tile(cv: Canvas, x, y, w, h, big, caption, theme, kind="doc") -> None:
    th = THEMES[theme]
    if kind == "doc":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y, w, h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
    cv.text(x, y + 10, big, size=36, color=th.deep if kind != "nd" else GREY, align="center", w=w)
    lines = wrap_text(caption, (w - 34) * 0.96, 15)
    cv.text(x + 17, y + 10 + 36 * 1.25 + 2, "\n".join(lines), size=15, color=INK if kind != "nd" else MUTED,
            align="center", w=w - 34)
    cv.register("tile", x, y, w, h)


def see_also(cv: Canvas, right: float, y: float, labels) -> None:
    """Right-aligned 'See also' chips that name sibling canvases by their gallery titles."""
    chips = [Chip(lab, theme="gray", size=14, pad_x=10, pad_y=4) for lab in labels]
    head = "See also (other canvases):"
    hw = text_size(head, 14)[0]
    total = hw + 12 + sum(c.w for c in chips) + 10 * (len(chips) - 1)
    x = right - total
    cv.text(x, y + 6, head, size=14, color=MUTED)
    cx = x + hw + 12
    for c in chips:
        c.place(cv, cx, y)
        cx += c.w + 10


def arrow_key(cv: Canvas, x: float, y: float, entries) -> None:
    for color, label in entries:
        arrow(cv, [(x, y + 11), (x + 64, y + 11)], color=color, sw=3)
        t = cv.text(x + 76, y, label, size=15, color=INK)
        x += 76 + t.w + 34


# ====================================================================== build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "Safety pipeline: inline guardrails under the hood",
        "Where the classifiers run in one agent turn, what happens on a hit, and where screening silently does not happen - as documented on Learn (as of 2026-11-03)",
        w=W)
    evidence_key(cv, W, 6)

    y = strip(cv, bottom + 40)
    y = section_a(cv, y + 56)
    y = section_b(cv, y + 60)
    y = section_c(cv, y + 60)
    y = section_d(cv, y + 60)
    y = section_e(cv, y + 60)
    y = section_f(cv, y + 60)
    y = section_g(cv, y + 60)
    y = section_sources(cv, y + 60)


# ---------------------------------------------------------------- summary strip
def strip(cv: Canvas, y: float) -> float:
    section_header(cv, 0, y, "Seven things to hold in your head", size=30, w=W)
    see_also(cv, W, y + 2, ["Guardrails and controls", "Hosted agent runtime: how a container becomes an agent endpoint"])
    y += 62
    tiles = [
        ("4 gates", "User input, tool call (preview), tool response (preview) and output: the four places a guardrail can scan one agent turn",
         "pink", "doc"),
        ("50-100 ms", "added at each intervention point; it varies with content length and the number of active controls", "pink", "doc"),
        ("Agent > model", "An agent's own guardrail fully overrides its model deployment's; with none assigned, it inherits the model's",
         "grape", "doc"),
        ("2 actions", "Annotate (models only) or Annotate and block (models and agents), at blocking levels Off, Low, Medium or High",
         "pink", "doc"),
        ("3 silent gaps", "Hosted agents: an invocations policy with no moderation settings, a bad policy ID and a body over 2 MB all raise no error",
         "red", "doc"),
        ("2 stream modes", "Default buffers, evaluates, then releases. Asynchronous filter streams first and flags a violation within about 1,000 characters",
         "pink", "doc"),
        ("? classifiers", "How the classifier models are hosted and scheduled is not documented beyond '50-100 ms per intervention point'",
         "gray", "nd"),
    ]
    gap = 28
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + gap), y, tw, 140, big, cap, th, kind)
    return y + 140


# ---------------------------------------------------------------- A: one agent turn through four gates
GW, SW, GAP = 370, 240, 56
OFF = 16
COLS = [SW, GW, SW, GW, SW, GW, SW, GW, SW]       # stage, gate, stage, gate, stage, gate, stage, gate, stage


def colx(i: int) -> float:
    return OFF + sum(COLS[:i]) + GAP * i


def section_a(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "A", "One agent turn through the four gates",
               "Left to right: what happens to a request. Each pink diamond is a decision point where the agent's guardrail scans content; "
               "a clean result continues, a hit with Annotate and block takes the red branch.")
    arrow_key(cv, W - 1010, y0 + 14, [(GA_C, "green arrow: content passes the gate"),
                                      (HIT_C, "red arrow: a hit with Annotate and block")])

    # ---- blocks stacked above the belt: controls per gate (pink) and notes per stage (gray / blue)
    g1 = Card(GW, "Controls at user input", [
        "Harm categories: hate, sexual, self-harm, violence, each blocked at Off, Low, Medium or High",
        "Prompt Shields, user prompt attack: on by default",
        "Prompt Shields, document attack: off by default; for model calls it scans documents here",
        "Spotlighting (preview): models only, never agents; base-64 encodes documents",
    ], theme="pink", subtitle="models and agents", title_size=18, body_size=14, sub_size=13, gap=4, pad=12, src=[L_INTERV, L_SHIELDS])
    g2 = Card(GW, "Controls at tool call", [
        "Harm categories on the tool name and arguments the agent proposes (Learn's example: Hate at High)",
        "Only for tools that support moderation: Azure AI Search, Azure Functions, OpenAPI, SharePoint grounding, Fabric Data Agent, "
        "Bing grounding, Bing Custom Search, Browser Automation",
    ], theme="pink", subtitle="agents only", badge="preview", title_size=18, body_size=14, sub_size=13, gap=4, pad=12,
        src=[L_INTERV])
    g2b = nd(GW, "Task adherence (preview)",
             "Learn does not name its intervention point. Inferred, not documented: it checks a planned tool call against the user's intent "
             "and returns taskRiskDetected plus details.", title_size=17, body_size=14, pad=12, src=[L_TASK])
    g3 = Card(GW, "Controls at tool response", [
        "Prompt Shields, document attack: scans the full payload a tool sends back (indirect prompt injection)",
        "Harm categories, if you configure them here: a risk with no control at this gate is not scanned",
        "Same supported-tool list as gate 2: other tools are not scanned at all",
    ], theme="pink", subtitle="agents only", badge="preview", title_size=18, body_size=14, sub_size=13, gap=4, pad=12,
        src=[L_INTERV, L_SHIELDS])
    g4 = Card(GW, "Controls at output", [
        "Harm categories: hate, sexual, self-harm, violence",
        "Protected material, text and code (DefaultV2 includes both for text models)",
        "PII (preview): per category, Annotate or Annotate and block the entire output",
        "Groundedness (preview): models only; retires 2027-04-30",
    ], theme="pink", subtitle="models and agents", title_size=18, body_size=14, sub_size=13, gap=4, pad=12,
        src=[L_INTERV, L_PII])
    n0 = Note(SW, "On the invocations protocol, a request body over 2 MB is forwarded without input screening (see D).", kind="warn",
              title="Size cap", size=14, title_size=16, pad=10)
    n2 = Note(SW, "A hosted agent's boundary policy is independent of the filter on its own model calls.", kind="info",
              title="Two layers", size=14, title_size=16, pad=10, src=[L_HOSTED])
    n4 = Note(SW, "Hosted agents: an egress proxy inside the sandbox enforces egress rules; a denied call gets HTTP 403 (see F).",
              kind="preview", title="Egress rules", size=14, title_size=16, pad=10)
    n6 = Note(SW, "Default mode holds output in a buffer; asynchronous filter streams it (see E).", kind="info", title="Streaming",
              size=14, title_size=16, pad=10)
    n8 = Note(SW, "Annotations come back with the content; an asynchronous stream also carries content_filter_offsets.", kind="info",
              title="Annotations", size=14, title_size=16, pad=10)
    stacks = {0: [n0], 1: [g1], 2: [n2], 3: [g2, g2b], 4: [n4], 5: [g3], 6: [n6], 7: [g4], 8: [n8]}
    heights = {i: sum(b.h for b in s) + 14 * (len(s) - 1) for i, s in stacks.items()}
    top_h = max(heights.values())

    # ---- the belt: stages and gates
    DH = 176
    ym = y + top_h + 58
    cv.rect(0, ym - 24, W, DH + 48, stroke=GREY, fill=THEMES["gray"].soft, style="solid", sw=1.5, dash="dotted", rough=0)
    stage_spec = {
        0: (1, "Request arrives", "at the model deployment or the agent endpoint", "gray"),
        2: (3, "Agent and model reason", "The model plans and may propose a tool call", "green"),
        4: (5, "Tool executes", "Service-side, or inside your hosted container", "orange"),
        6: (7, "Model writes the answer", "The final output is assembled", "blue"),
        8: (9, "Response delivered", "Content plus annotations", "gray"),
    }
    gate_spec = {1: (2, "GATE 1\nUser input"), 3: (4, "GATE 2\nTool call"), 5: (6, "GATE 3\nTool response"), 7: (8, "GATE 4\nOutput")}
    belt = {}
    for i in range(9):
        x = colx(i)
        if i in stage_spec:
            n, label, sub, th = stage_spec[i]
            b = Box(SW, label, sub=sub, theme=th, fill="hatch", size=19, sub_size=14, h=150).place(cv, x, ym + (DH - 150) / 2)
            numbered(cv, b.x + 22, b.y + 4, n, theme=th, d=32, size=18)
        else:
            n, label = gate_spec[i]
            b = Box(GW, label, theme="pink", fill="hatch", size=21, shape="diamond", h=DH).place(cv, x, ym)
            numbered(cv, b.x + b.w * 0.25, b.y + b.h * 0.25, n, theme="pink", d=32, size=18)
        belt[i] = b
    for i in range(8):
        lab = "clean" if i in gate_spec else None
        connect(cv, belt[i], belt[i + 1], a_side="right", b_side="left", sw=2, color=GA_C, label=lab, label_size=14)

    # ---- stacks above (bottom-aligned so each touches its stage)
    for i, stack in stacks.items():
        yy = y + top_h - heights[i]
        for b in stack:
            b.place(cv, colx(i), yy)
            yy += b.h + 14
        line_between(cv, stack[-1] if i != 3 else g2b, belt[i], dash="dotted",
                     color=THEMES["pink" if i in gate_spec else "gray"].stroke)

    # ---- below the belt: what a hit does (gates) and what Learn does not say (stages)
    hy = ym + DH + 66
    hits = {
        1: ("Hit and block: HTTP 400", "error code content_filter, before the agent runs. A streamed Responses request emits no events. "
                                       "For a model call: an error response"),
        3: ("Hit and block: no tool call", "Foundry does not execute the tool call. The agent stops until it receives another user input"),
        5: ("Hit and block: agent stops", "Foundry stops the agent, and the tool's content is not saved to agent memory"),
        7: ("Hit: flag, or block", "Annotate only (models): a flag in the annotation response. Annotate and block: HTTP 400, or "
                                   "HTTP 200 plus a terminal SSE error event when the output was streamed"),
    }
    hboxes = {i: Box(GW, lab, sub=sub, theme="red", fill="soft", size=18, sub_size=14) for i, (lab, sub) in hits.items()}
    hh = max(b.h for b in hboxes.values())
    for i, b in hboxes.items():
        b.place(cv, colx(i), hy, h=hh)
        connect(cv, belt[i], b, a_side="bottom", b_side="top", sw=2, color=HIT_C, label="hit" if i == 1 else None, label_size=14)
    nds = {
        0: nd_box(SW, "Classifier hosting", "Not documented: where and how the scanners run", h=hh),
        2: nd_box(SW, "History re-scan", "Not documented: whether gate 1 re-scans hydrated conversation history", h=hh),
        4: nd_box(SW, "Tools in a container", "Not documented: gates 2 and 3 for tools that run inside a hosted container", h=hh),
    }
    for i, b in nds.items():
        b.place(cv, colx(i), hy)
    k6 = Note(SW, "A control whose risk an agent does not support (Spotlighting, groundedness) does nothing for that agent, and raises no error.",
              kind="gotcha", title="Silent no-ops", size=14, title_size=16, pad=10, src=[L_OVERVIEW]).place(cv, colx(6), hy)
    k8 = Note(SW, "Annotate only is not available for agents: a control on an agent can only Annotate and block.", kind="info",
              title="Agents: block only", size=14, title_size=16, pad=10, src=[L_OVERVIEW]).place(cv, colx(8), hy)
    return max(hy + hh, k6.bottom, k8.bottom)


# ---------------------------------------------------------------- shared helpers for B-F
def bullets(cv: Canvas, x: float, y: float, w: float, items, size=15, color=INK, gap=7, marker="#c2255c") -> float:
    """Ring-bullet list as free text (no box). Returns the bottom y."""
    lr = metrics.line_ratio()
    for it in items:
        lines = wrap_text(it, (w - 22) * 0.965, size)
        cv.ellipse(x, y + size * lr / 2 - 4.5, 9, 9, stroke=marker, sw=2, rough=0)
        cv.text(x + 20, y, "\n".join(lines), size=size, color=color)
        y += len(lines) * size * lr + gap
    return y - gap


def char_strip(cv: Canvas, x: float, y: float, segs, sq=24, gp=4):
    """Row of small squares standing for streamed characters. segs = [(count, kind)]; kinds: ok, hold, open, hit, future."""
    cx = x
    spans = []
    for count, kind in segs:
        x0 = cx
        for _ in range(count):
            if kind == "ok":
                cv.rect(cx, y, sq, sq, stroke="#2f9e44", fill="#b2f2bb", style="solid", sw=1.5, rough=0, round_=False)
            elif kind == "hold":
                cv.rect(cx, y, sq, sq, stroke="#c2255c", fill="#fcc2d7", style="hachure", sw=1.5, rough=0, round_=False)
            elif kind == "open":
                cv.rect(cx, y, sq, sq, stroke="#f08c00", fill="#ffec99", style="solid", sw=1.5, rough=0, round_=False)
            elif kind == "hit":
                cv.rect(cx, y, sq, sq, stroke="#e03131", fill="#ffa8a8", style="solid", sw=2.5, rough=0, round_=False)
            else:
                cv.rect(cx, y, sq, sq, stroke=GREY, fill="transparent", sw=1.5, dash="dashed", rough=0, round_=False)
            cx += sq + gp
        spans.append((x0, cx - gp))
    return spans, y + sq


# ---------------------------------------------------------------- B: control cheat sheet
def section_b(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "B", "What each control looks for, and where it runs",
               "A control = a risk to detect + the intervention point(s) + an action. The classifiers are Azure AI Content Safety models; "
               "a guardrail is a named collection of controls.")
    G, P, R = ("no preview tag; on agents preview", "green"), ("preview", "orange"), ("preview, retires 2027-04-30", "red")
    rows = [
        ["Harm categories", "Gates 1 and 4; on agents also 2 and 3",
         "Hate and fairness, sexual, violence and self-harm, each in four severity levels (Safe, Low, Medium, High). The blocking level "
         "(Off, Low, Medium, High) sets which severities are blocked. Trained and tested on eight languages: Chinese, English, French, "
         "German, Italian, Japanese, Portuguese, Spanish",
         "DefaultV2: Medium on prompts and completions. Off for outputs only for approved customers", G],
        ["Prompt Shields: user prompt attack", "Gate 1",
         "Formerly 'jailbreak risk detection'. Detects attempts to change system rules, embed a conversation mockup, take on a new "
         "persona (role-play) or use encoding attacks. Annotation: jailbreak {detected, filtered}",
         "On by default", G],
        ["Prompt Shields: document attack", "Gate 1 for model calls; gate 3 for agents (supported tools)",
         "Hidden instructions inside documents, emails or web pages that try to hijack the session (indirect attacks). Primarily "
         "trained and evaluated on English",
         "Off by default: enable it per control", ("no preview tag; at gate 3 preview", "green")],
        ["Spotlighting", "Document content in Chat Completions; models only, never agents",
         "Tags input documents as lower trust by base-64 encoding them. No direct cost, but more document tokens, and large documents "
         "can exceed input limits",
         "Off by default", P],
        ["Protected material, text and code", "Gate 4",
         "Flags copyrighted text or licensed code in the completion. Learn's example: Annotate only puts a flag in the annotation response",
         "Both are in DefaultV2 for text models", G],
        ["Personal data (PII)", "Gate 4 (completions)",
         "Entity types: personal information, financial, government IDs (50+ countries), Azure secrets and keys, geolocation. Per "
         "category: Annotate, or Annotate and block the ENTIRE output",
         "Not in DefaultV2's text-model list", P],
        ["Task adherence", "Not named by Learn (inferred: gate 2)",
         "Content Safety API agent:analyzeTaskAdherence (2024-12-15-preview): is a planned tool call misaligned with what the user "
         "asked? Returns taskRiskDetected and details. Text up to 100,000 characters; tested on English; data may be processed in "
         "other US and EU regions",
         "A signal for blocking the call or escalating to a human", P],
        ["Groundedness", "Output versus source material; models only",
         "Detects ungrounded content. Learn points to Foundry evaluation tooling, or your own LLM-based grounding check, as the "
         "replacement",
         "Not available to agents", R],
    ]
    t = Table([("Control", 330), ("Where it runs", 330), ("What it looks for and how it works", 1500), ("Default and notes", 600),
               ("Status on Learn", 400)], rows, w=W, theme="pink", size=14, head_size=15, first_col_theme="pink",
              title="Control cheat sheet (Learn, as of 2026-11-03)", title_size=20)
    t.place(cv, 0, y)
    nt = Note(W, "'No preview tag' means the Learn page does not label the control preview; guardrails on agents are preview as a "
                 "whole. Third-party controls (Palo Alto Networks Prisma AIRS, Zenity) are covered in section G. Custom blocklists and "
                 "custom categories are further controls you can add to a guardrail: see the Guardrails and controls canvas.",
              kind="info", title="Reading the status column", size=14, title_size=16, pad=10, src=[L_OVERVIEW, L_SHIELDS])
    nt.place(cv, 0, t.y + t.h + 24)
    return nt.bottom


# ---------------------------------------------------------------- C: which guardrail runs for an agent
def section_c(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "C", "Which guardrail runs for an agent? The override trap",
               "An agent is judged by the guardrail assigned to the agent itself, not by the guardrail of its model deployment", "grape")
    top = y
    LW = 1560
    DH = 170
    st = Box(300, "A request reaches an agent", sub="in Foundry Agent Service", theme="gray", fill="hatch", size=18, h=110)
    q1 = Box(340, "Agent has its own guardrail?", theme="grape", fill="hatch", shape="diamond", size=19, h=DH)
    o1 = Box(690, "Only the agent's guardrail runs",
             sub="'The agentic guardrail fully overrides the model's guardrail.' The controls on the model deployment are not "
                 "consulted for this agent",
             theme="pink", fill="hatch", size=19, sub_size=15, h=130)
    o2 = Box(780, "The agent inherits its model deployment's guardrail",
             sub="It uses Microsoft.DefaultV2 only if the deployment uses it, or you assign it. Learn's example: a deployment "
                 "guardrail named MyCustomGuardrails is also the agent's, until you assign another",
             theme="gray", fill="hatch", size=19, sub_size=15, h=130)
    st.place(cv, 0, top + 4 + (DH - 110) / 2)
    q1.place(cv, 380, top + 4)
    o1.place(cv, 870, top + 4 + (DH - 130) / 2)
    o2.place(cv, q1.cx - o2.w / 2 + 100, q1.bottom + 70)
    connect(cv, st, q1, a_side="right", b_side="left", sw=2)
    connect(cv, q1, o1, a_side="right", b_side="left", label="yes", label_size=15, sw=2, color=THEMES["pink"].stroke)
    connect(cv, q1, o2, a_side="bottom", b_side="top", tb=0.38, label="no", label_size=15, sw=2, color=THEMES["gray"].stroke)
    rx = 1640
    rw = W - rx
    n1 = Note(rw, "The overview page says an agent with no guardrail inherits its model deployment's. The hosted-agent page says an "
                  "agent whose definition omits rai_config runs with no content safety guardrail at the hosted-agent boundary, "
                  "independent of any filter on its model calls. For hosted agents think in two layers (see D).",
              kind="warn", title="Docs word hosted agents differently", size=14, title_size=16, pad=10, src=[L_OVERVIEW, L_HOSTED])
    lim = Card(LW, "What an agent guardrail cannot do (Learn)", [
        "Annotate only is not available for agents: a control can only Annotate and block",
        "Spotlighting and groundedness have no effect for agents; they still apply to models that use the same guardrail",
        "Tool-call and tool-response controls work only for tools that support moderation (Azure AI Search, Azure Functions, OpenAPI, "
        "SharePoint grounding, Fabric Data Agent, Bing grounding, Bing Custom Search, Browser Automation); availability can also vary "
        "by region and model",
        "Not applied to other agents registered in the Foundry Control Plane, or to audio-transcription models",
        "Not a substitute for authorization, data loss prevention, tool permissions or human approval",
    ], theme="pink", src=[L_OVERVIEW, L_HOSTED])
    lim.place(cv, 0, o2.bottom + 40)
    left_bottom = lim.bottom
    with cv.panel(rx, top, title="Learn's worked example: Violence detection", theme="grape", style="dotted", w=rw, pad=20,
                  title_size=24, sub="Same model, two guardrails: which one scans what?", sub_size=15) as pe:
        iw = rw - 40
        cm = Card((iw - 20) / 2, "Model deployment's guardrail", ["Violence: High, on user input and output"], theme="blue",
                  title_size=18, body_size=15, pad=14)
        ca = Card((iw - 20) / 2, "The agent's own guardrail", ["Violence: Low, on user input and output",
                                                               "No Violence control at all for tool calls and tool responses"],
                  theme="pink", title_size=18, body_size=15, pad=14)
        hh = max(cm.h, ca.h)
        cm.place(cv, pe.ix, pe.iy, h=hh)
        ca.place(cv, pe.ix + cm.w + 20, pe.iy, h=hh)
        ry = pe.iy + hh + 40
        cv.text(pe.ix, ry - 26, "What the agent actually gets, gate by gate", size=15, color=MUTED)
        gw4 = (iw - 3 * 20) / 4
        res = [("Gate 1: user input", "scanned for Violence at Low", "pink", "hatch"),
               ("Gate 2: tool call", "NOT scanned for Violence", "gray", "soft"),
               ("Gate 3: tool response", "NOT scanned for Violence", "gray", "soft"),
               ("Gate 4: output", "scanned for Violence at Low", "pink", "hatch")]
        rb = []
        for i, (lab, sub, th, fl) in enumerate(res):
            rb.append(Box(gw4, lab, sub=sub, theme=th, fill=fl, size=18, sub_size=15, h=104).place(cv, pe.ix + i * (gw4 + 20), ry))
        nn = Note(iw, "Raising the model deployment to High does not make the agent stricter. The agent is scanned at Low, and its "
                      "tool traffic is not scanned for Violence at all. Check the guardrail assigned to the AGENT.", kind="gotcha",
                  title="The trap", size=15, title_size=17, pad=12, src=[L_OVERVIEW])
        nn.place(cv, pe.ix, ry + 104 + 26)
    n1.place(cv, rx, pe.bottom + 28)
    return max(left_bottom, n1.bottom)


# ---------------------------------------------------------------- C: hosted agents - will this request be screened?
def section_d(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "D", "Hosted agents: will this request actually be screened?",
               "Hosted-agent guardrails are in preview (as of 2026-11-03). Follow a request down the decision chain; every red outcome "
               "raises no error and the agent still answers HTTP 200.", "red")
    top = y
    DW, DHH, STEP = 290, 170, 400
    cy0 = top + 176
    labels = ["rai_config set on the agent version?", "Real policy, full ARM resource ID?", "Which protocol?",
              "invocations_moderation set?", "Text found and body 2 MB or less?"]
    dia = []
    for i, lab in enumerate(labels):
        d = Box(DW, lab, theme="pink", fill="hatch", shape="diamond", size=17, h=DHH).place(cv, i * STEP, cy0)
        numbered(cv, d.x + d.w * 0.25, d.y + d.h * 0.25, i + 1, theme="pink", d=30, size=17)
        dia.append(d)
    oy = cy0 + DHH + 72
    ow, oh = 300, 168

    def outcome(i, label, sub, th, fill="soft", dash="solid"):
        return Box(ow, label, sub=sub, theme=th, fill=fill, dash=dash, size=18, sub_size=14, h=oh)

    o_no_cfg = outcome(0, "No boundary guardrail", "The agent runs without a content safety guardrail at the hosted-agent boundary",
                       "gray").place(cv, dia[0].cx - ow / 2, oy)
    o_open = outcome(1, "FAILS OPEN",
                     "A policy that does not exist can still deploy as active: no filtering, and harmful prompts reach the agent",
                     "red").place(cv, dia[1].cx - ow / 2, oy)
    o_ws = outcome(2, "invocations_ws: no moderation", "Content safety moderation is not available on the WebSocket protocol",
                   "gray").place(cv, dia[2].cx - ow / 2, oy)
    o_auto = Box(ow, "responses or activity: automatic", sub="The platform knows the request and response shapes and finds the text itself",
                 theme="green", fill="soft", size=18, sub_size=14, h=130).place(cv, dia[2].cx - ow / 2, top)
    o_inert = outcome(3, "INERT policy", "Attached but screens nothing: the platform cannot find the text. The agent still deploys, HTTP 200",
                      "red").place(cv, dia[3].cx - ow / 2, oy)
    o_bypass = outcome(4, "Forwarded unscreened",
                       "Body is not valid JSON, input_paths select nothing, or the request body is over 2 MB", "red").place(
        cv, dia[4].cx - ow / 2, oy)
    fin = Box(ow, "Input screened", sub="Before the agent runs. Text over 10,000 characters in one check is truncated", theme="green",
              fill="hatch", size=19, sub_size=14, h=150).place(cv, 5 * STEP, cy0 + (DHH - 150) / 2)
    gc, rc = THEMES["green"].stroke, HIT_C
    for a, b, lab in ((0, 1, "yes"), (1, 2, "yes"), (3, 4, "yes")):
        connect(cv, dia[a], dia[b], a_side="right", b_side="left", label=lab, label_size=15, sw=2, color=gc)
    connect(cv, dia[2], dia[3], a_side="right", b_side="left", label="invocations", label_size=14, sw=2, color=gc)
    connect(cv, dia[4], fin, a_side="right", b_side="left", label="yes", label_size=15, sw=2, color=gc)
    for d, o, lab in ((dia[0], o_no_cfg, "no"), (dia[1], o_open, "no"), (dia[3], o_inert, "no"), (dia[4], o_bypass, "no")):
        connect(cv, d, o, a_side="bottom", b_side="top", label=lab, label_size=15, sw=2, color=rc)
    connect(cv, dia[2], o_ws, a_side="bottom", b_side="top", label="invocations_ws", label_size=14, sw=2, color=THEMES["gray"].stroke)
    connect(cv, dia[2], o_auto, a_side="top", b_side="bottom", label="responses, activity", label_size=14, sw=2, color=gc)

    # right column: attach rules
    ax = 2400
    aw = W - ax
    ar = Card(aw, "Attach rules (Learn)", [
        "rai_config.rai_policy_name is the FULL ARM resource ID of the RAI policy, not the bare name; only one policy per agent",
        "No rai_config: no guardrail. rai_config without a policy name: the account-scoped Microsoft.DefaultV2",
        "azd has no rai_config in azure.yaml: a policies list (type rai_policy, raiPolicyName) is mapped to it",
        "SDK floors (as of 2026-11-03): azure-ai-projects 2.2.0, and 2.7.0 for invocations_moderation",
    ], theme="pink", badge="preview", src=[L_ADD])
    ar.place(cv, ax, top)
    ow2 = Note(aw, "A bad policy ID is not caught at deploy time on many subscriptions. After you deploy, confirm the policy exists on the "
                   "account, then send a prompt it must block.", kind="gotcha", title="Deploy-time validation will not save you",
               size=14, title_size=16, pad=10, src=[L_ADD])
    ow2.place(cv, ax, ar.bottom + 24)

    y2 = oy + oh + 52
    cw = [1040, 1040, 960]
    gap = 60
    t1 = Table([("Protocol", 150), ("You configure", 330), ("Content safety behaviour", 560)], [
        ["responses", "rai_policy_name", "Foundry knows the request and response shapes and locates the text to screen"],
        ["invocations", "rai_policy_name AND invocations_moderation", "You declare where the text lives. Without the settings the policy screens nothing"],
        ["activity", "rai_policy_name", "Automatic on three paths: input, output, and outbound events sent to Microsoft 365 with POST or PUT"],
        ["invocations_ws", "(nothing to set)", "Content safety moderation is not available"],
    ], w=cw[0], theme="pink", size=14, head_size=15, title="Protocol matrix", title_size=20, first_col_theme="pink")
    t2 = Table([("Setting", 230), ("Needed", 230), ("What it does", 580)], [
        ["response_mode", "always", "non_streaming, streaming or both: the output shapes the agent can return. Input is screened whatever you set"],
        ["input / output_content_type", "optional", "json (default) or text; text screens the body itself, so no paths are needed"],
        ["input_paths", "json input", "Path expressions such as $.messages[*].content; several matches are joined and screened together"],
        ["output_paths", "json, non-streaming or both", "The same syntax, for a buffered response body"],
        ["stream_selectors", "json, streaming or both", "event_type + text_field pairs: exact, case-sensitive, top-level only. text_field is a name, not a path; default delta"],
    ], w=cw[1], theme="pink", size=14, head_size=15, title="invocations_moderation settings", title_size=20, first_col_theme="pink")
    t3 = Table([("Limit or condition", 430), ("Behaviour", 530)], [
        ["Request body over 2 MB", "Forwarded to the agent without input screening"],
        ["Buffered response body over 1 MB", "Rejected with HTTP 502; it never reaches the client"],
        ["Text over 10,000 characters in one check", "Truncated before analysis"],
        ["A response shape you did not declare", "Rejected with HTTP 502, not skipped"],
        ["Body not JSON, or paths select nothing", "Forwarded unscreened"],
        ["Error responses and empty acknowledgments", "Not screened"],
    ], w=cw[2], theme="red", size=14, head_size=15, title="Limits (as of 2026-11-03)", title_size=20, first_col_theme="red")
    t1.place(cv, 0, y2)
    t2.place(cv, cw[0] + gap, y2)
    t3.place(cv, cw[0] + cw[1] + 2 * gap, y2)
    y3 = max(t1.y + t1.h, t2.y + t2.h, t3.y + t3.h) + 36
    c1 = Card(cw[0], "What the caller sees (hosted agents)", [
        "Blocked input (Responses or Invocations): HTTP 400, error code content_filter, before the agent runs; a streamed Responses "
        "request emits no events",
        "Blocked non-streaming or buffered output: HTTP 400, content_filter, with a message that names the output stage",
        "! Blocked STREAMED output: the status stays HTTP 200 because headers are already sent. The stream ends with one terminal SSE "
        "error event, code content_filter, and the user may already have seen partial output",
        "Do not use the HTTP status alone to decide whether streamed output passed",
    ], theme="red", src=[L_HOSTED, L_ADD])
    c2 = Card(cw[1], "Test it before you trust it", [
        "GET the agent version and check definition.rai_config (and rai_config.invocations_moderation)",
        "List the policies on the account and confirm the last segment of rai_policy_name matches one",
        "Send a prompt your policy must block: expect HTTP 400 content_filter at the input stage; a harmful prompt that is not blocked "
        "means the policy, the paths or the selectors are wrong",
        "With azd, send the body as a file (azd ai agent invoke -f): a message argument goes as text/plain, a json input type cannot "
        "parse it, and the request is forwarded unscreened",
    ], theme="pink", src=[L_ADD])
    c3 = vb(cw[2], "What the launch material says", [
        "Build blog (2026-06-02): hosted agents now include built-in content safety guardrails; each prompt is evaluated before it "
        "reaches your agent code and each response before it reaches your users; public preview in all hosted-agent regions",
        "Mechanics video (0:04:24 to 0:04:46): every interaction is checked against guardrail policies, covering content filtering, "
        "prompt injection and copyrighted material",
    ], src=[("Build blog: hosted agents", U_BLOG), ("Mechanics at 0:04:24", U_MECH)], prefix="Video/blog")
    h3 = max(c1.h, c2.h, c3.h)
    c1.place(cv, 0, y3, h=h3)
    c2.place(cv, cw[0] + gap, y3, h=h3)
    c3.place(cv, cw[0] + cw[1] + 2 * gap, y3, h=h3)
    return y3 + h3


# ---------------------------------------------------------------- D: streaming - buffer first, or stream first
def section_e(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "E", "Streaming: buffer first, or stream first",
               "The same four gates, two delivery contracts. Each square stands for streamed text: what the client already has, "
               "and what the classifier has actually checked.", "pink")
    top = y
    pw = 1540
    with cv.panel(0, top, title="Default: synchronous prevention", sub="buffer, evaluate, release", theme="pink", style="dotted",
                  w=pw, pad=20, title_size=24, sub_size=15) as p1:
        sy = p1.iy + 52
        cv.text(p1.ix, sy - 26, "the text as it is generated: only released text reaches the client", size=15, color=MUTED)
        spans, bot = char_strip(cv, p1.ix, sy, [(16, "ok"), (8, "hold"), (8, "future")])
        hbrace(cv, spans[0][0], spans[0][1], bot + 14, side="top", depth=12)
        cv.text(spans[0][0], bot + 34, "released to the client, chunk by chunk", size=15, color="#2b8a3e")
        hbrace(cv, spans[1][0], spans[1][1], bot + 14, side="top", depth=12)
        cv.text(spans[1][0] - 20, bot + 34, "held in the buffer while\nthe classifier evaluates it", size=15, color="#a61e4d")
        cv.text(spans[2][0] + 10, bot + 34, "not generated yet", size=15, color=MUTED)
        by = bullets(cv, p1.ix, bot + 104, pw - 40, [
            "Content is buffered, evaluated, then released in chunks, not token by token; this repeats until the stream ends",
            "Strongest prevention for the content selected for screening, in exchange for a later first visible text",
            "Gotcha: the last segment can be returned before the policy is applied. In a Learn test a blocklisted term in roughly the last "
            "15 to 30 words came back with finish_reason: stop",
            "Hosted agents: input is screened before the agent runs; the output is buffered and only approved content is released. "
            "A violation stops the response and returns a content-filter error",
        ])
    with cv.panel(pw + 80, top, title="Asynchronous filter: deferred detection", sub="stream now, verdict later", theme="pink",
                  style="dotted", w=pw, pad=20, title_size=24, sub_size=15) as p2:
        sx = p2.ix
        sy2 = p2.iy + 52
        spans, bot = char_strip(cv, sx, sy2, [(14, "ok"), (6, "open"), (1, "hit"), (3, "open"), (8, "future")])
        hbrace(cv, spans[0][0], spans[0][1], bot + 14, side="top", depth=12)
        cv.text(spans[0][0], bot + 34, "check_offset: fully moderated\n(it never decreases)", size=15, color="#2b8a3e")
        o_l, o_r = spans[1][0], spans[3][1]
        hbrace(cv, o_l, o_r, bot + 14, side="top", depth=12)
        cv.text(o_l, bot + 34, "already shown, not yet checked: the\nsignal is guaranteed within ~1,000 characters", size=15,
                color="#e67700")
        hx = (spans[2][0] + spans[2][1]) / 2
        cv.text(hx - 70, p2.iy + 2, "violation found here", size=15, color=HIT_C)
        arrow(cv, [(hx, p2.iy + 28), (hx, sy2 - 3)], color=HIT_C, sw=2)
        cv.text(spans[4][1] + 24, sy2 - 2, "stream stops:\nfinish_reason content_filter", size=15, color=HIT_C)
        by2 = bullets(cv, sx, bot + 104, pw - 40, [
            "Tokens stream immediately. Separate annotation messages with empty text carry content_filter_offsets: check_offset, "
            "start_offset and end_offset",
            "GA, API version 2024-02-01 or later; set per deployment in the content filter configuration (needs permission to modify filters)",
            "Your app must retract what was already shown. Content flagged retroactively as protected material might not qualify for the "
            "Customer Copyright Commitment",
            "Hosted agents: the stream stops with a protocol-specific moderation signal; handle content already displayed, stored or passed on",
        ])
    y2 = max(p1.bottom, p2.bottom) + 40
    t = Table([("Compare", 240), ("Default", 520), ("Asynchronous filter", 760)], [
        ["Status", "GA", "GA"],
        ["Who can use it", "All customers", "All customers"],
        ["How to enable", "On by default, no action needed", "Foundry portal: content filter configuration, applied per deployment"],
        ["What streams", "Buffered chunks", "Tokens immediately: no buffering, filters run asynchronously"],
        ["Filtering signal", "Immediate", "Delayed: in increments of up to about 1,000 characters"],
        ["Modality", "Text; all GPT models", "Text; all GPT models"],
    ], w=1540, theme="pink", size=14, head_size=15, title="Chat Completions streaming modes (Learn)", title_size=20, first_col_theme="pink")
    t.place(cv, 0, y2)
    hh2 = max(t.h, 0)
    b = Card(760, "Billing when a filter fires", [
        "Status 400 (prompt filtered): you are charged for prompt evaluation",
        "Status 200 with finish_reason content_filter: charged for the prompt and the completion tokens generated before filtering",
        "Both modes are billed this way",
    ], theme="yellow", src=[L_STREAM])
    lt = Card(760, "Latency in hosted agents", [
        "Time to first visible text = content generation + moderation processing + buffering and release",
        "Guardrail time is not reported separately: output-policy buffering is folded into the x-ms-debug-latency-container-response-ms header",
        "Measure end to end with representative inputs, policy and region: a model-only number does not include this path",
    ], theme="pink", src=[L_HOSTED])
    hh2 = max(t.h, b.h, lt.h)
    b.place(cv, pw + 80, y2, h=hh2)
    lt.place(cv, pw + 80 + 780, y2, h=hh2)
    return max(t.y + t.h, b.bottom, lt.bottom)


# ---------------------------------------------------------------- E: network egress controls
def section_f(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "F", "Network egress controls: the other half of a hosted-agent guardrail",
               "Preview, hosted agents only (API 2026-05-15-preview on the RAI policy). Content safety screens what is said; egress "
               "rules govern where the agent can connect.", "pink")
    top = y
    ag = Box(250, "Agent code", sub="inside the sandbox", theme="green", fill="hatch", size=19, sub_size=14, h=140, icon="agent",
             icon_pos="left", icon_size=34)
    px = Box(330, "Egress proxy", sub="runs inside the Foundry-managed agent sandbox, not in your firewall", theme="pink", fill="hatch",
             size=20, sub_size=14, h=170)
    dm = Box(380, "Rules top to bottom: first match wins", theme="pink", fill="hatch", shape="diamond", size=18, h=210)
    cy = top + 330
    ag.place(cv, 0, cy - ag.h / 2)
    px.place(cv, 390, cy - px.h / 2)
    dm.place(cv, 840, cy - dm.h / 2)
    ox, ow = 1330, 440
    outs = [("Allow", "The request goes to the destination", "green"),
            ("Deny", "The proxy returns HTTP 403 to the agent's HTTP client; the agent handles the error itself", "red"),
            ("Transform", "Allow, and edit headers: Set, Insert or Remove", "orange"),
            ("Rewrite", "Redirect the request to another destination, such as an enterprise gateway", "indigo"),
            ("No rule matched", "The default action: Deny (allow list, recommended) or Allow (deny list)", "gray")]
    ob = []
    oy = top
    for lab, sub, th in outs:
        b = Box(ow, lab, sub=sub, theme=th, fill="soft", size=19, sub_size=14, h=100).place(cv, ox, oy)
        ob.append(b)
        oy += 100 + 26
    connect(cv, ag, px, a_side="right", b_side="left", label="outbound call", label_size=14, sw=2)
    connect(cv, px, dm, a_side="right", b_side="left", label="match on host", label_size=14, sw=2)
    for b, th in zip(ob, ("green", "red", "orange", "indigo", "gray")):
        connect(cv, dm, b, a_side="right", b_side="left", route="elbow", sw=2, color=THEMES[th].stroke)
    fc = Note(380, "If the policy cannot be evaluated, the request is denied (fail-closed). Foundational platform domains are "
                   "allow-listed automatically.", kind="gotcha", title="Fail-closed", size=14, title_size=16, pad=10, src=[L_ADD])
    fc.place(cv, 840, dm.bottom + 34)
    left_bottom = ob[-1].bottom

    rx = 1860
    rw = W - rx
    t = Table([("Mode", 150), ("Deny rules", 470), ("Transform and Rewrite", rw - 620)], [
        ["Audit", "Would-be denies are logged, not blocked: traffic flows normally", "Still applied"],
        ["Enforce", "Matching Deny rules block the request (HTTP 403)", "Applied"],
    ], w=rw, theme="pink", size=14, head_size=15, title="Audit first, then Enforce", title_size=20, first_col_theme="pink")
    t.place(cv, rx, top)
    f = Card(rw, "Policy facts (preview)", [
        "Stored in the same RAI policy you attach to the agent (egressPolicy: mode, defaultAction, rules)",
        "Each rule matches the request host; wildcards such as *.contoso.com work. Actions: Allow, Deny, Transform, Rewrite",
        "At most 480 egress rules per policy (an Azure support request can raise it)",
        "Running sandboxes do not reload policy changes: start a new session or resume it after you update the policy",
        "Complements Azure Firewall rather than replacing it; not centrally enforced through Azure Policy",
    ], theme="pink", badge="preview", src=[L_ADD])
    f.place(cv, rx, t.y + t.h + 26)
    left2 = max(left_bottom, fc.bottom) + 44
    r1 = Card(880, "TLS and the injected certificate authority", [
        "To inspect HTTPS the runtime injects the proxy's CA into the sandbox trust bundle: SSL_CERT_FILE, REQUESTS_CA_BUNDLE, "
        "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH, NODE_EXTRA_CA_CERTS",
        "It differs across hosted-agent clusters and regions and rotates about every 30 days (as of 2026-11-03), even while a sandbox runs",
        "! Never pin, copy or persist the CA",
    ], theme="indigo", src=[L_ADD])
    r2 = Card(880, "See the decisions", [
        "Each decision is a span named Network egress decision: Decision, Reason, Matched rule, Rule source, Enforcement, "
        "Destination, Default action",
        "Playground: the Trajectories tab. Application Insights: traces | where message == \"Network egress decision\"",
        "Allowed calls show success, denied calls show failure",
    ], theme="violet", src=[L_ADD])
    r3 = Card(880, "Roll it out in four steps", [
        "Start in Audit with a Deny default and run representative tasks",
        "Review the egress decisions and add the hosts the agent really needs",
        "Switch the mode to Enforced and deploy a new agent version",
        "Start a new session and run the same tasks again",
    ], theme="green", src=[L_ADD])
    h = max(r1.h, r2.h, r3.h)
    r1.place(cv, 0, left2, h=h)
    r2.place(cv, 920, left2, h=h)
    r3.place(cv, 1840, left2, h=h)
    nt = Note(W - 2760, "Not yet, per Learn: secret header values (secret references are not supported in preview), Azure service-tag "
                        "and IP-range rules, MCP tool policies, PII and DLP inspection, custom webhook hooks.", kind="warn",
              title="Not available yet", size=14, title_size=16, pad=10, src=[L_ADD])
    nt.place(cv, 2760, left2, h=h)
    return max(f.bottom, left2 + h)


# ---------------------------------------------------------------- F: defaults, scope, third parties, evidence
def section_g(cv: Canvas, y0: float) -> float:
    y = banner(cv, y0, "G", "Defaults, scope and the evidence trail",
               "What every model gets without configuring anything, where the pipeline is absent, and who says what", "gray")
    top = y
    cw = 1000
    gap = 80
    t = Table([("Risk category", 400), ("Scans", 300), ("Default threshold", 300)], [
        ["Hate and fairness", "Prompts and completions", "Medium"],
        ["Violence", "Prompts and completions", "Medium"],
        ["Sexual", "Prompts and completions", "Medium"],
        ["Self-harm", "Prompts and completions", "Medium"],
        ["User prompt injection attack (jailbreak)", "Prompts", "N/A"],
        ["Protected material, text", "Completions", "N/A"],
        ["Protected material, code", "Completions", "N/A"],
    ], w=cw, theme="pink", size=14, head_size=15, title="Microsoft.DefaultV2 for text models", title_size=20, first_col_theme="pink")
    t.place(cv, 0, top)
    d = Card(cw, "Defaults worth knowing", [
        "Core-harm filters and user prompt attack detection are on by default; document attack detection is off",
        "Medium blocks content classified medium or high; the four harm classifiers are tested on eight languages",
        "Models get Microsoft.DefaultV2 by default. An agent uses it only if its deployment does, or you assign it",
        "Blocked input returns an error response; blocked output can return a filtered completion",
    ], theme="pink", src=[L_DEFAULT, L_OVERVIEW])
    d.place(cv, 0, t.y + t.h + 26)

    x2 = cw + gap
    absent = Card(cw, "Where the pipeline is not in the path", [
        "Audio-transcription models: prompts and completions are not processed by the guardrail system",
        "Other agents registered in the Foundry Control Plane: guardrails apply only to agents developed in Agent Service",
        "Instant models (preview): default guardrails only. No per-model RAI policy; an account-level default applies to all of them",
        "Managed compute (preview): built-in Azure AI Content Safety filters are not in the data path; call the Content Safety APIs yourself",
        "Hosted agents with no rai_config (see D)",
    ], theme="red", src=[L_OVERVIEW, L_INSTANT, L_MANAGED])
    absent.place(cv, x2, top)
    tp = Card(cw, "Third-party guardrails (bring your own license)", [
        "Palo Alto Networks Prisma AIRS and Zenity AI Detection and Response attach to a guardrail and run at runtime",
        "Needs Key Vault and a user-assigned managed identity attached to the Foundry resource; Owner on the subscription to set up",
        "! Your data is processed OUTSIDE Foundry under the partner's terms; keep the project in the partner's region",
        "A hit shows up as external_safety_provider inside content_filter_result",
    ], theme="orange", src=[L_3P])
    tp.place(cv, x2, absent.bottom + 26)

    x3 = 2 * (cw + gap)
    ndc = nd(cw, "What Learn does not tell you", [
        "Where the classifier models are hosted, how requests reach them and their latency distribution beyond '50-100 ms per intervention point'",
        "The intervention point of task adherence (this canvas infers tool call)",
        "Whether gate 1 re-scans hydrated history, and gates 2 and 3 for tools that run inside a hosted container",
    ], title_size=20, body_size=15, pad=16)
    ndc.place(cv, x3, top)
    ev = vb(cw, "More from the launch material", [
        "Ignite 2025 BRK205 at 0:13:47: a UI walk-through of creating a guardrail with prompt-injection and PII controls. It shows the "
        "portal, not the internals",
        "Build blog (2026-06-02) and the Mechanics video (0:04:24) are summarised in D; both are product-team material, not a spec",
    ], src=[("Ignite 2025 BRK205", U_BRK205), ("Build blog: hosted agents", U_BLOG)], prefix="Video/blog")
    ev.place(cv, x3, ndc.bottom + 26)
    return max(d.bottom, tp.bottom, ev.bottom)


# ---------------------------------------------------------------- sources
def section_sources(cv: Canvas, y: float) -> float:
    items = [L_OVERVIEW, L_INTERV, L_DEFAULT, L_TASK, L_3P, L_SHIELDS, L_PII, L_STREAM, L_HOSTED, L_ADD, L_INSTANT, L_MANAGED,
             ("(blog) What's new in hosted agents (Build 2026)", U_BLOG),
             ("(video) Microsoft Mechanics: Agent Service explained, v=iR7_57lJOz8", U_MECH)]
    r = sources(cv, 0, y, items, w=W, cols=4)
    return r.y + r.h
