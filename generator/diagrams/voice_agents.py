"""Voice-based prompt agents (Preview), part 1: the architecture (native speech-to-speech vs cascaded vs hosted conversation engine),
models (managed vs self-deployed), the voice agent definition setting by setting, the WebSocket session and the telephony path
(Teams Phone extensibility, Twilio, Direct SIP).

Part 2 ('voice-agents-part-2') covers hosted voice agents, best practices, observability and evaluation, pricing and limits, migrating from
Voice Live with a text agent, and the doc conflicts.  Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="voice-agents", title="Voice agents (Preview): architecture, definition and telephony", section="2", group="Agent Service", order=15,
    description="Voice-based prompt agents (Preview): native speech-to-speech vs cascaded pipelines, managed vs self-deployed models, every setting of "
                "the voice agent definition, the WebSocket session and the telephony path (Teams Phone, Twilio, Direct SIP).",
    tags=["voice", "voice-live", "speech-to-speech", "telephony", "websocket", "preview"],
)

W = 3600          # canvas width
G = 48            # gutter
C = 560           # one grid column (6 columns = 3600)


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    overview=("Agent Service overview: how voice-based agents work", learn("agents/overview")),
    qs=("Quickstart: create a voice-based prompt agent", learn("agents/quickstarts/prompt-voice-agent")),
    conf=("Configure a voice agent", learn("agents/how-to/configure-voice-agent")),
    img=("Send image input to a voice agent", learn("agents/how-to/send-image-input-voice-agent")),
    sub=("Use a subagent in a voice-based agent", learn("agents/how-to/use-subagent-voice-first-agent")),
    tel=("Integrate telephony channels (Teams Phone extensibility, Twilio)", learn("agents/how-to/voice-agent-telephony-channels")),
    sip=("Connect a voice agent to telephony via SIP", learn("agents/how-to/voice-agent-telephony-channels-sip")),
    pub=("Publish and connect voice agent channels", learn("agents/how-to/voice-agent-channels-publish")),
    best=("Best practices for voice-based agents", learn("agents/concepts/voice-agent-best-practice")),
    opt=("Optimize voice agent instructions", learn("agents/how-to/optimize-voice-agent-instructions")),
    obs=("Voice agent tracing, monitoring and evaluation", learn("agents/concepts/voice-agent-observability")),
    price=("Pricing for voice-based agents", learn("agents/concepts/voice-agent-pricing")),
    migrate=("Migrate from Voice Live with Foundry Agent Service", learn("agents/how-to/migrate-from-voice-live")),
    build=("Build a voice agent with hosted agents", learn("agents/how-to/build-voice-agent")),
    engine=("Use a hosted agent as the conversation engine", learn("how-to/voice-first-with-hosted-agent")),
    limits=("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    toolbox=("Create and manage a toolbox", learn("agents/how-to/tools/toolbox")),
    wsrest=("REST: connect to a voice agent (WebSocket)", learn("reference/rest/voice-agent-web-socket-connect-voice-agent")),
    bindrest=("REST: create a telephony binding", learn("reference/rest/agent-telephony-create-telephony-binding")),
    convrest=("REST: list agent conversations", learn("reference/rest/agent-endpoint-conversations-list-agent-conversations")),
    vl=("Voice Live overview (Speech)", learn("azure/ai-services/speech-service/voice-live", base="")),
    vlhost=("Voice Live with a hosted agent (Speech)", learn("azure/ai-services/speech-service/how-to-voice-live-hosted-agent-integration", base="")),
    gptlive=("GPT-Live", learn("openai/concepts/gpt-live")),
    tpe=("Teams Phone extensibility overview (ACS)", learn("azure/communication-services/concepts/interop/tpe/teams-phone-extensibility-overview", base="")),
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


def lk(label, key):
    return {"text": label, "link": U[key][1], "color": LINK}


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


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
    """Numbered walk-through card: the circles match the numbered arrows of the diagram next to it."""

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


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def badge_on(cv, blk, kind, dx=-10, dy=-12):
    """Status pill straddling the top-right corner of a placed block."""
    lab = {"ga": "GA", "preview": "Preview", "retiring": "Retiring", "new": "New", "classic": "Classic"}.get(kind, kind)
    bw = metrics.line_width(lab, 13) + 18
    draw_badge(cv, blk.right - bw + dx + 10, blk.y + dy, kind)


LX = 560   # left edge of the diagram area inside a lane


def lane_frame(cv, y, h, n, title, sub, theme, badge=None, src_=()):
    th = THEMES[theme]
    cv.rect(0, y, W, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    numbered(cv, 44, y + 44, n, theme=theme, d=44, size=24)
    t = cv.text(84, y + 20, title, size=25, color=th.deep, wrap=410)
    s = cv.text(86, t.bottom + 6, sub, size=15, color="#495057", wrap=410)
    by = s.bottom + 12
    if badge:
        draw_badge(cv, 86, by, badge)
        by += 34
    for lab, url in src_:
        cv.text(86, by, f"Learn: {lab}", size=12, color=LINK, link=url, wrap=410)
        by += 17
    cv.line((520, y + 18), (520, y + h - 18), stroke=th.stroke, sw=1.5, dash="dotted", opacity=60)


def flow_lane(cv, y, n, title, sub, theme, badge, srcs, steps, gap, card_x, facts_title, facts, min_h=200, dash=False):
    """A lane with a left-to-right box flow and a facts card on the right. steps: (w, label, sub, theme, icon). Returns bottom y."""
    c = card(W - card_x - 24, facts_title, facts, theme=theme, title_size=18)
    boxes = [Box(w_, lab, sub=sb, theme=th, h=128, size=18, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=34,
                 dash="dashed" if dash and th == "gray" else "solid") for w_, lab, sb, th, ic in steps]
    bh = max(b.h for b in boxes)
    h = max(min_h, c.h + 44, bh + 70)
    lane_frame(cv, y, h, n, title, sub, theme, badge, srcs)
    cy = y + h / 2
    x = LX
    for b in boxes:
        b.place(cv, x, cy - bh / 2, h=bh)
        x += b.w + gap
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=4)
    c.place(cv, card_x, cy - c.h / 2)
    return y + h

# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "Preview", "The Learn voice pages mark voice-based prompt agents, telephony and SIP as preview. A Build 2026 recap (blog, not Learn) says GA: docs disagree (part 2).", "yellow"),
        Tile(C, "No speech stack to host", "Foundry manages the lifecycle and voice orchestration; Voice Live does recognition, turn-taking, model interaction and synthesis.", "green"),
        Tile(C, "2 pipelines", "Native speech-to-speech, or cascaded (recognition, text model, synthesis). The service derives it from the model you choose.", "blue"),
        Tile(C, "kind: voice", "Every create or update is an immutable version. The Text or Voice interaction mode cannot change after creation.", "green"),
        Tile(C, "3 phone paths", "Teams Phone extensibility, Twilio and Direct SIP (the overview says SIP is not a supported customer flow: docs disagree).", "indigo"),
        Tile(C, "60 min, 60 days", "Maximum voice session duration; stored voice conversations and Microsoft-managed audio are kept 60 days (as of 2026-11-03).", "cyan"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: pipelines
def band_pipelines(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  Two voice pipelines - and the hosted variant",
             "Foundry Agent Service runs the agent lifecycle and uses Voice Live for recognition, turn-taking, model interaction and synthesis. You pick a model; the pipeline follows from it.")
    y = flow_lane(
        cv, y, 1, "Native speech-to-speech", "One realtime model hears the caller and speaks the reply", "blue", None, src("overview"),
        [(300, "Caller audio", "microphone, phone call or browser", "gray", "user"), (560, "Realtime speech model", "gpt-realtime family or azure-realtime", "blue", "openai"),
         (300, "Spoken response", "streamed as audio deltas", "green", "agent")], 110, 2050, "Native speech-to-speech", [
            "Optimized for natural, low-latency conversation: the realtime model handles spoken input and output directly",
            "Self-deployed realtime deployments (for example gpt-realtime) also run this way",
            "Supported settings and voice families depend on the selected model",
        ]) + 24
    y = flow_lane(
        cv, y, 2, "Cascaded text model", "Recognition, then a text model, then synthesis", "teal", None, src("overview", "conf"),
        [(250, "Caller audio", "", "gray", "user"), (330, "Speech recognition", "Azure Speech in Foundry Tools; a transcription model", "teal", "speech"),
         (330, "Text model", "Azure OpenAI text, Claude, other chat-completion", "blue", "openai"), (330, "Speech synthesis", "an Azure voice", "teal", "speech"),
         (250, "Spoken response", "", "green", "agent")], 80, 2470, "Cascaded text model", [
            "Broader text-model and Azure voice choices; explicit control of transcription, phrase lists, turn detection and interim responses",
            "Each stage adds latency: recognition, turn detection, model, synthesis, playback",
            "Azure OpenAI text models, Claude, Fireworks, other chat-completion models and managed compute all run cascaded",
        ], min_h=210) + 24
    y = flow_lane(
        cv, y, 3, "Hosted conversation engine", "Your hosted agent owns the conversation, Voice Live owns the audio", "green", "preview", src("engine"),
        [(230, "Caller audio", "", "gray", "user"), (340, "Voice Live", "recognition, turn-taking, interruption handling", "teal", "speech"),
         (440, "Hosted text agent", "model calls, instructions, tools - Voice Live Bridge Protocol 1.0 over invocations_ws", "green", "container-apps"),
         (330, "Voice Live", "speech synthesis", "teal", "speech"), (230, "Spoken response", "", "green", "agent")], 70, 2470, "Hosted conversation engine", [
            "A kind: voice wrapper keeps audio, greeting and store; the kind: hosted target keeps model, instructions and tools",
            "The target must implement Bridge Protocol 1.0; a text endpoint alone is not enough. Details on part 2",
        ], min_h=210, dash=True)
    return y


def band_compare(cv: Canvas, y: float) -> float:
    top = y + 40
    t = Table(
        [("", 220), ("Native speech-to-speech", 1040), ("Cascaded text model", 1040)],
        [
            [ct("Pipeline", "gray"), "Caller audio -> realtime model -> spoken response", "Caller audio -> speech recognition -> text model -> speech synthesis -> spoken response"],
            [ct("Latency", "gray"), "Lowest; the model fuses audio understanding and generation into one step", "Each stage contributes to end-to-end latency"],
            [ct("Model choice", "gray"), "Realtime models; the portal menu lists gpt-realtime-2.1, azure-realtime, gpt-realtime-1.5, -2.1-mini and -mini",
             "Native text models in the portal (gpt-5.4, gpt-5.3-chat, gpt-5-mini, gpt-5-nano) plus self-deployed text, Claude, Fireworks, managed compute"],
            [ct("Control", "gray"), "Settings and voice families depend on the model", "Explicit control over transcription, phrase lists, turn detection and interim responses; broader Azure voice choice"],
            [ct("Pick it when", "gray"), "Conversation feel and latency matter most (the best-practice page's default advice for conversation)",
             "Model and voice flexibility, custom voices, specific locales or transcription control outweigh the extra stages"],
        ], w=S(4), theme="blue", size=14, head_size=15, title="Speech-to-speech vs cascaded (as documented)", title_size=22)
    t.place(cv, 0, top)
    res = card(S(2), "Typical resources behind a portal-created voice agent", [
        "A Foundry resource and project, and a versioned voice-based prompt agent",
        "A fully managed Voice Live model (no separate audio model to deploy) or an eligible customer-deployed model",
        "Azure Speech in Foundry Tools for transcription or synthesis when the pipeline needs it; Application Insights for traces, monitoring and evaluation",
        "Teams inbound: Azure Communication Services + Event Grid. Twilio: a project connection. Direct SIP: none of those",
    ], theme="gray", icon="foundry", src=src("overview"))
    res.place(cv, X(4), top)
    return max(t.bottom, res.bottom)


# ================================================================================================ band 2: models
def band_models(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Models - managed or self-deployed, and what the portal offers",
             "model_type managed: the service hosts the model. model_type self_deployed: your own Foundry deployment, set by deployment name. Self-deployed means the deployment, not hosting the voice agent yourself.")
    top = y
    t1 = Table(
        [("Customer need", 250), ("Managed model", 640), ("Self-deployed model", 854)],
        [
            ["Less setup", "Pick a model and start; no separate deployment to maintain", "Reuse a compatible deployment, or deploy one first"],
            ["Existing quota or capacity", "Use service-managed models when you do not need your own capacity", "Use available quota or provisioned throughput (PTUs) on your deployment, where supported"],
            ["Broader model choice", "The service-managed models available to your resource", "Anthropic Claude, Fireworks models, chat-completion models on managed compute"],
            ["Customize the model", "Capabilities of the available managed models", "A supported fine-tuned model or custom weights"],
            ["Data-processing needs", "Pick it when the managed choices meet them", "Choose supported deployment locations for your model"],
            ["Safety and upkeep", "Custom guardrails in the voice-agent settings; the service manages the deployment", "Custom guardrails too; you manage capacity and updates"],
        ], w=S(3), theme="blue", size=14, head_size=15, first_col_theme="blue", title="Managed vs self-deployed", title_size=22)
    t1.place(cv, 0, top)
    t2 = Table(
        [("Self-deployed model", 420), ("Pipeline", 230), ("Choose it when", 1094)],
        [
            ["Azure OpenAI realtime (for example gpt-realtime)", ("Speech-to-speech", "blue"), "A realtime model handles spoken input and output on your own deployment"],
            ["Azure OpenAI text models", ("Cascaded", "teal"), "Reuse an existing text model, or pick it for its reasoning and tool-calling"],
            ["Anthropic Claude in Foundry", ("Cascaded", "teal"), "A supported Claude deployment handles the conversation"],
            ["Other chat-completion models, incl. Fireworks", ("Cascaded", "teal"), "Another provider, an open-source model or supported custom weights"],
            ["Chat-completion models on managed compute", ("Cascaded", "teal"), "An open-source model on dedicated GPU capacity that you configure in Foundry"],
        ], w=S(3), theme="teal", size=14, head_size=15, title="What each self-deployed category runs as", title_size=22)
    t2.place(cv, X(3), top)
    y1 = max(t1.bottom, t2.bottom) + 36
    m1 = Table(
        [("Speech-to-speech model", 330), ("~latency", 150), ("Tier", 150)],
        [["gpt-realtime-2.1", "800 ms", "Pro"], ["azure-realtime", "500 ms", "Pro"], ["gpt-realtime-1.5", "700 ms", "Pro"],
         ["gpt-realtime-2.1-mini", "1,100 ms", "Standard"], ["gpt-realtime-mini", "400 ms", "Standard"]],
        w=630, theme="blue", size=14, head_size=15, title="Portal menu: native speech-to-speech", title_size=22)
    m1.place(cv, 0, y1)
    m2 = Table(
        [("Native text model", 330), ("~latency", 150), ("Tier", 150)],
        [["gpt-5.4", "1,500 ms", "Pro"], ["gpt-5.3-chat", "not shown", "Pro"], ["gpt-5-mini", "1,400 ms", "Standard"], ["gpt-5-nano", "not shown", "Lite"]],
        w=630, theme="teal", size=14, head_size=15, title="Portal menu: native text (cascaded)", title_size=22)
    m2.place(cv, 630 + G, y1)
    nx = 2 * 630 + 2 * G
    n1 = Note(X(4) - G - nx, "Latency in the menu is a comparison aid, not a guaranteed end-to-end response time: transcription, synthesis, tools, network and avatar rendering add time. "
                             "Availability and metadata are loaded per Foundry resource and change by region and release stage - the portal is the source of truth (as of 2026-11-03).",
              kind="info", title="Read the model menu with care", size=14, src=src("conf"))
    n1.place(cv, nx, y1)
    c1 = card(S(2), "Latency and safety for self-deployed models", [
        "Prefer a regional deployment next to your voice-agent resource, or a Data Zone deployment in the same zone; compare with Global under the same workload",
        "Prefer asynchronous output filtering where supported: synchronous filtering buffers text and delays speech",
        "! Spoken content cannot be retracted: asynchronous filtering can let content be spoken before a delayed violation signal - use synchronous checks if policy needs moderation first",
        "Size capacity for concurrent calls; measure TTFT and time to first audio",
    ], theme="pink", icon="content-safety", src=src("conf"))
    c1.place(cv, X(4), y1)
    y2 = max(m1.bottom, m2.bottom, n1.bottom, c1.bottom) + 30
    c2 = card(S(2), "Choosing and switching models", [
        "managed: the service hosts it, for example gpt-realtime-2.1. self_deployed: model = your Foundry deployment name; same Foundry resource = no extra role assignment (unlike direct Voice Live BYOM)",
        "Changing the model can change compatible voices, the user transcript model field, advanced settings, interim-response availability and tool support",
        "If the voice is not compatible Foundry picks a default: review Voice and Advanced settings after every model change",
    ], theme="blue", icon="openai", src=src("conf"))
    c2.place(cv, 0, y2)
    c3 = card(S(2), "Quota, PTU and billing", [
        "Quota and PTU reuse apply to the model deployment; speech and other voice-agent charges still apply",
        "Managed models are billed through the service as part of the voice agent; self-deployed ones through your deployment's pricing model",
    ], theme="yellow", icon="quotas", src=src("conf", "price"))
    c3.place(cv, X(2), y2)
    n2 = Note(S(2), "Related, not voice-agent model options in the pages read: GPT-Live (gpt-live-1, a full-duplex voice API), GPT Realtime over WebRTC, WebSocket or SIP, "
                    "Translate and Transcribe variants and MAI-Voice models appear elsewhere in the Foundry docs. Confirm availability on the portal's Models page.",
              kind="quote", title="Not the same surface", size=14, src=src("gptlive"))
    n2.place(cv, X(4), y2)
    return max(c2.bottom, c3.bottom, n2.bottom)

# ================================================================================================ band 3: the definition
def band_definition(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  The voice agent definition - every setting in one place",
             "A voice-based agent is an agent whose kind is voice (alias prompt-voice). The values in audio and avatar are session defaults; a client can override supported fields with session.update when it connects.")
    top = y
    bw, bh, vg = 660, 150, 34
    hub = Box(560, "Voice agent definition", sub="kind: voice (alias prompt-voice); each create or update is an immutable version", shape="ellipse", theme="green", h=300,
              size=24, sub_size=15, fill="solid")
    hub.place(cv, 790, top + (4 * bh + 3 * vg) / 2 - 150)
    left = [
        ("Model", "model_type + model: managed (the service hosts it) or self_deployed (your deployment name). The pipeline follows the model.", "blue"),
        ("Behavior", "instructions, greeting, structured_inputs: Handlebars placeholders; the greeting is a fixed template or llm_generated.", "green"),
        ("Listening: audio.input", "24-kHz PCM by default, turn detection, noise reduction, echo cancellation and transcription (phrase_list, custom_speech).", "green"),
        ("Speaking: audio.output", "voice_type, voice, speed 0.25 to 1.5, word timestamps; output_modalities default [audio], plus text, animation or avatar.", "green"),
    ]
    right = [
        ("Actions: tools", "function (your client), mcp, toolbox, system (end_conversation); tool_choice; parallel_tool_calls is not supported.", "orange"),
        ("Latency: interim_response", "Speaks while the agent thinks or waits on a tool: static texts (no model call) or LLM-written filler.", "green"),
        ("Specialists: subagent_config", "Delegate to prompt or hosted agents in the same project; not supported in VNet-isolated projects.", "green"),
        ("Data: store, limits", "store defaults to false; true keeps transcript, event timeline and raw audio together. max_output_tokens caps replies.", "cyan"),
    ]
    for i, (t_, s_, th) in enumerate(left):
        b = Box(bw, t_, sub=s_, theme=th, h=bh, size=19, sub_size=14, fill="hatch")
        b.place(cv, 0, top + i * (bh + vg))
        connect(cv, b, hub, a_side="right", b_side="left", route="elbow", sw=2.5, gap=4)
    for i, (t_, s_, th) in enumerate(right):
        b = Box(bw, t_, sub=s_, theme=th, h=bh, size=19, sub_size=14, fill="hatch")
        b.place(cv, 1480, top + i * (bh + vg))
        connect(cv, hub, b, a_side="right", b_side="left", route="elbow", sw=2.5, gap=4)
    hy = top + 4 * bh + 3 * vg + 18
    cv.text(0, hy, "Also on the definition: avatar (browser visual layer), rai_config (guardrail assignment), include (extra output fields).", size=15, color=MUTED)
    vc = card(1360, "Versions, endpoint and playground", [
        "Every create or update produces a new immutable version; the endpoint is live after the first version",
        "Test a version with the x-agent-version-override header before you make it active; keep the previous version for rollback",
        "! The interaction mode (Text or Voice) cannot be changed after creation: create another agent",
        "Playground tabs: Playground, Details, Traces, Monitor, Evaluation, Channels; controls are disabled during an active voice session",
    ], theme="green", icon="versions", src=src("conf", "qs"))
    vc.place(cv, 2240, top)
    cc = card(1360, "Four ways to create one", [
        "Portal: Agents > Build an agent > Interaction mode Voice > Create agent and open playground",
        "Python SDK: VoiceAgentDefinition with azure-ai-projects[voice] 2.7.0 or later; a JavaScript or TypeScript SDK path needs Node.js 22 or later",
        "Azure Developer CLI: azd ai agent init with --kind prompt-voice --voice (azd 1.32.0 or later and the Foundry extensions)",
        "REST: the agent PATCH and version APIs with the Foundry-Features: VoiceAgents=V1Preview opt-in",
        "Needs Foundry User on the project and a voice model available in your region",
    ], theme="gray", icon="azd", src=src("qs"))
    cc.place(cv, 2240, vc.bottom + 24)
    y1 = max(hy + 24, cc.bottom) + 40
    # ---- row 1: input audio
    t1 = Table(
        [("turn_detection type", 360), ("Use it when", 808)],
        [
            [ct("server_vad", "green"), "You want straightforward silence-based detection; suits most business scenarios"],
            [ct("semantic_vad", "green"), "You want the OpenAI semantic end-of-turn model"],
            [ct("azure_semantic_vad", "green"), "You want Azure semantic detection with an explicit languages list"],
            [ct("azure_semantic_vad_en", "green"), "Your callers speak English only"],
            [ct("azure_semantic_vad_multilingual", "green"), "Your callers switch languages within a call"],
            [ct("None", "gray"), "Turn detection off (it is on by default): your client must trigger each response"],
        ], w=S(2), theme="green", size=14, head_size=15, title="Input audio: turn detection types", title_size=22)
    t1.place(cv, 0, y1)
    t2 = Table(
        [("Option", 330), ("Effect", 838)],
        [
            ["threshold", "Activation sensitivity from 0 to 1; raise it in noisy places"],
            ["prefix_padding_ms", "Audio kept before detected speech"],
            ["silence_duration_ms", "Silence needed before the turn ends; increase it when callers pause often"],
            ["idle_timeout_ms / speech_duration_ms", "Maximum idle time before the detector ends the turn / minimum speech that triggers detection"],
            ["remove_filler_words", "Drops filler words from transcription (default False)"],
            ["create_response / interrupt_response", "Respond automatically when speech stops (default True) / caller speech can interrupt the agent (default True)"],
            ["end_of_utterance_detection", "Adds a semantic end-of-utterance model; None disables it. auto_truncate trims the input buffer when speech stops"],
        ], w=S(2), theme="green", size=14, head_size=15, title="Shared options of the Azure semantic types", title_size=22)
    t2.place(cv, X(2), y1)
    c1 = card(S(2), "Noise, echo and transcription", [
        "noise_reduction.type: near_field (headsets, handsets), far_field (speakerphones, rooms) or azure_deep_noise_suppression (noisy places such as contact centers); None disables",
        "echo_cancellation when the agent's output reaches the caller's microphone; reference_source defaults to server, client needs two interleaved input channels",
        "transcription model: azure-speech, whisper-1, gpt-4o-transcribe or gpt-4o-mini-transcribe - a model name, not a deployment name; None disables it",
        "Foundry extras: phrase_list (bias recognition toward product names and identifiers) and custom_speech (your custom speech deployments by locale)",
    ], theme="green", icon="speech", src=src("conf"))
    c1.place(cv, X(4), y1)
    y2 = max(t1.bottom, t2.bottom, c1.bottom) + 36
    # ---- row 2: output audio and tools
    t3 = Table(
        [("voice_type", 270), ("Fields that apply", 898)],
        [
            [ct("openai", "green"), "voice, speed"],
            [ct("azure-standard", "green"), "voice, voice_locale, speed, voice_temperature, lexicon and normalization URLs, prefer_locales, style, pitch, volume"],
            [ct("azure-custom", "green"), "The azure-standard fields except style, plus custom_voice_endpoint_id"],
            [ct("azure-personal", "green"), "The azure-standard fields except style, plus personal_voice_model"],
            [ct("avatar-voice-sync", "green"), "The azure-standard fields except voice and style, plus personal_voice_model; the voice name comes from the avatar"],
            [ct("azure-realtime-native", "green"), "voice, speed"],
        ], w=S(2), theme="green", size=14, head_size=15, title="Output audio: voice_type decides the fields", title_size=22)
    t3.place(cv, 0, y2)
    t4 = Table(
        [("Tool kind", 190), ("Executed by", 220), ("Notes", 758)],
        [
            [ct("function", "orange"), "Your client", "The service forwards the call over the live session; your app returns the result"],
            [ct("mcp", "orange"), "The service", "Points at a remote MCP server"],
            [ct("toolbox", "orange"), "The service", "References a versioned Foundry toolbox by toolbox_name and toolbox_version"],
            [ct("system", "orange"), "The service", "Session controls with no code: end_conversation lets the agent end the call"],
        ], w=S(2), theme="orange", size=14, head_size=15, title="Tools: four kinds", title_size=22)
    t4.place(cv, X(2), y2)
    cf = ChipFlow(["response_scheduling for mcp and toolbox:", "when_idle (default)", "interrupt", "skip_if_busy", "silent"], w=S(2), theme="orange", size=15, fill="soft")
    cf.place(cv, X(2), t4.bottom + 16)
    c2 = card(S(2), "Tools: rules of the road", [
        "Server-side tools (web search, Azure AI Search, OpenAPI) go through a toolbox, not directly; use individual tools or one toolbox, not both",
        "tool_choice defaults to auto; none blocks calls, required forces at least one, or name a tool",
        "Test a toolbox without tool search first; use tool search mainly beyond 10 to 15 tools, configured on the toolbox version",
        "A function schema alone executes nothing: your realtime client must implement the call loop",
    ], theme="orange", icon="toolbox-icon", src=src("conf", "toolbox"))
    c2.place(cv, X(4), y2)
    y3 = max(t3.bottom, cf.bottom, c2.bottom) + 36
    # ---- row 3: greeting, interim, subagents
    g1 = card(S(2), "Greeting and structured inputs", [
        "greeting: a template (exact text) or llm_generated (tool_choice default none)",
        "The greeting streams as its own response with its own response.done: do not send response.create for it, and remove old client-side greeting triggers",
        "instructions and greeting use Handlebars; every placeholder needs a structured input or the session fails to start",
        "Connect with the structured_input query parameter: JSON up to 32 KiB, depth up to 16",
        "Write instructions for the ear: short sentences, no markdown or lists",
    ], theme="green", icon="agent", src=src("conf", "wsrest"))
    g2 = card(S(2), "Interim responses, limits and persistence", [
        "interim_response triggers: latency, tool or both; latency_threshold_ms defaults to 2,000 ms in the SDK (the portal shows 500 ms)",
        "static_interim_response picks from your texts and adds no model latency; llm_interim_response lets a model write the filler (max_completion_tokens default 50)",
        "max_output_tokens caps each reply (or inf); include adds optional output fields such as input transcription logprobs",
        "store (default false) keeps transcript, event timeline and raw audio together; override per session with the store query parameter",
    ], theme="yellow", icon="quotas", src=src("conf"))
    g3 = card(S(2), "Subagents (subagent_config, Preview)", [
        "subagents[]: prompt or hosted agents in the same project, at least one entry; not supported in VNet-isolated projects",
        "agent_name and agent_capabilities are required (the capabilities text tells the voice agent when to forward); agent_version defaults to the active version; invoke_timeout_seconds 5 to 1,200",
        "response_policy: immediate_ack (+ ack_instructions), enable_delta_progress (default false), gap_filling_interval 5 to 120 s, progress_update_interval 5 to 300 s",
        "Give each subagent one clearly defined capability and tell the voice agent when to delegate",
    ], theme="green", icon="agent", badge="preview", src=src("sub"))
    r_, b3 = row(cv, 0, y3, [g1, g2, g3], gap=G)
    return b3


# ================================================================================================ band 4: the WebSocket session
def band_session(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Build a client - one WebSocket session, event by event",
             "The agent owns model, instructions, voice, turn detection and noise suppression on the server, so a client can start talking after session.created without sending session.update.")
    top = y
    seq = Sequence(cv, 0, top, [("Client app", "gray", "app"), ("Foundry voice endpoint", "green", "agent"), ("Model and tools", "blue", "openai")], spacing=880, head_w=260,
                   head_h=62, size=16, label_size=15)
    seq.msg(0, 1, "Upgrade GET wss://.../agents/{agent}/endpoint/protocols/voice?api-version=v1 with an Entra bearer token and Foundry-Features: VoiceAgents=V1Preview", num=1)
    seq.msg(1, 0, "session.created carries the stored conversation_id (then session.updated if you sent a session.update)", dash="dashed", num=2)
    seq.msg(1, 0, "Greeting, if configured: its own response and response.done before the first user turn", dash="dashed", num=3)
    seq.msg(0, 1, "input_audio_buffer.append: base64 audio in the configured input format", num=4)
    seq.msg(1, 2, "Turn detection commits the turn; the model answers; mcp and toolbox tools run inside the service", num=5)
    seq.msg(1, 0, "Function tool calls return to the client, which runs them and sends conversation.item.create (function_call_output), then one response.create", dash="dashed", num=6)
    seq.msg(1, 0, "response.output_audio.delta and response.output_audio_transcript.* stream the reply; response.done carries the final status", dash="dashed", num=7)
    seq.msg(0, 1, "Caller interrupts: input_audio_buffer.speech_started - flush queued playback; the context is truncated to what was heard", num=8)
    sb = seq.end()
    RX = 2180
    RW = W - RX
    c1 = card(RW, "Connect: endpoint, auth and query", [
        "Entra bearer token (scope https://ai.azure.com/.default) in the Authorization header on the upgrade; resource API keys are not a substitute; never put tokens in the URL or long-lived credentials in browser code",
        "Header Foundry-Features: VoiceAgents=V1Preview (or the foundry_features query); WebSocket subprotocol realtime; HTTP 409 agent_disabled if the agent is disabled",
        "Query: transport=websocket or webrtc (WebRTC: the socket carries only SDP signaling, rtc.call.sdp.create and created; not for BYOM or hosted-agent voice agents), store, structured_input",
        "x-agent-version-override pins a tested version; the project endpoint is https://<account>.services.ai.azure.com/api/projects/<project>",
    ], theme="red", icon="key", src=src("wsrest", "migrate"))
    c1.place(cv, RX, top)
    c2 = card(RW, "SDKs and tools", [
        "Python azure-ai-projects[voice] 2.7.0 or later: beta.voice_agents.realtime.connect adds the opt-in header and returns typed events; a JavaScript or TypeScript SDK path exists too",
        "azd: azd ai agent init with --kind prompt-voice --voice to scaffold, provision, deploy and test without writing runtime code",
        "! The old private-preview azure-ai-voiceagents package and /voice_agents route are obsolete",
    ], theme="gray", icon="sdk", src=src("qs", "migrate"))
    c2.place(cv, RX, c1.bottom + 22)
    # images in a turn
    iy = c2.bottom + 30
    cv.text(RX, iy, "Images in a turn (Preview)", size=22, color=THEMES["green"].deep)
    ib = [Box(430, "conversation.item.create", sub="input_text + input_image (Base64 data URL, detail)", theme="gray", h=96, size=17, sub_size=13, fill="hatch"),
          Box(300, "response.create", sub="one request after the item", theme="green", h=96, size=17, sub_size=13, fill="hatch"),
          Box(560, "Spoken answer about the image", sub="the deployment must support images", theme="blue", h=96, size=17, sub_size=13, fill="hatch")]
    ibx = RX
    for b in ib:
        b.place(cv, ibx, iy + 40)
        ibx += b.w + 60
    connect(cv, ib[0], ib[1], a_side="right", b_side="left", sw=2.5, gap=3)
    connect(cv, ib[1], ib[2], a_side="right", b_side="left", sw=2.5, gap=3)
    cv.text(RX, iy + 150, "Camera frames: send about one every 2 seconds as conversation items WITHOUT response.create. A browser needs a server-side proxy for authentication. "
                          "store does not turn on trace content capture - they are separate privacy switches.", size=14, color=INK, wrap=RW)
    cv.text(RX, iy + 218, "Learn: Send image input to a voice agent", size=12, color=LINK, link=U["img"][1])
    return max(sb, iy + 240)


# ================================================================================================ band 5: telephony
SX = 2300   # x of the tall Foundry endpoint box


def phone_lane(cv, y, h, n, title, sub, theme, badge, srcs, steps, gap=60):
    th = THEMES[theme]
    cv.rect(0, y, SX - 70, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    numbered(cv, 44, y + 44, n, theme=theme, d=44, size=24)
    t = cv.text(84, y + 20, title, size=24, color=th.deep, wrap=380)
    s = cv.text(86, t.bottom + 6, sub, size=14, color="#495057", wrap=380)
    by = s.bottom + 8
    if badge:
        draw_badge(cv, 86, by, badge)
        by += 32
    for lab, url in srcs:
        by = cv.text(86, by, f"Learn: {lab}", size=12, color=LINK, link=url, wrap=380).bottom + 3
    cv.line((500, y + 16), (500, y + h - 16), stroke=th.stroke, sw=1.5, dash="dotted", opacity=60)
    boxes = [Box(w_, lab, sub=sb, theme=tn, h=120, size=17, sub_size=13, fill="hatch", icon=ic, icon_pos="top", icon_size=30) for w_, lab, sb, tn, ic in steps]
    bh = max(b.h for b in boxes)
    x = 540
    for b in boxes:
        b.place(cv, x, y + (h - bh) / 2, h=bh)
        x += b.w + gap
    for a, b in zip(boxes, boxes[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=4)
    return boxes[-1]


def band_telephony(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Telephony - how a phone call reaches the agent",
             "A binding routes inbound calls to one agent. Outbound calls use call jobs and need no binding. All three paths below are Preview (Direct SIP: the overview disagrees, see section 6 on part 2).")
    top = y
    LH = 196
    GP = 22
    lanes = []
    lanes.append(phone_lane(cv, top, LH, 1, "Teams Phone extensibility", "Your Teams tenant keeps the number; ACS provides call automation and media", "indigo", "preview", src("tel", "tpe"),
                            [(300, "Caller dials the Teams number", "a service number on a resource account", "gray", "user"),
                             (290, "Teams resource account", "routes the call to your ACS resource", "indigo", "teams"),
                             (300, "Azure Communication Services", "call automation and media path", "indigo", "ai-services"),
                             (330, "Event Grid", "IncomingCall event to the binding's incoming_call_url", "indigo", "event-grid")], gap=42))
    lanes.append(phone_lane(cv, top + LH + GP, LH, 2, "Twilio", "Foundry discovers your Twilio numbers through the project connection", "indigo", "preview", src("tel"),
                            [(300, "Caller dials a Twilio number", "active, voice-capable", "gray", "user"),
                             (430, "Twilio", "creating a binding rewrites the number's voice URL and status callback", "indigo", "api-connections")], gap=60))
    lanes.append(phone_lane(cv, top + 2 * (LH + GP), LH, 3, "Direct SIP", "No ACS, Teams, Twilio or Event Grid needed; SIP over TLS", "indigo", "preview", src("sip"),
                            [(270, "Caller", "via a provider or your enterprise telephony", "gray", "user"),
                             (290, "SIP trunk or SBC", "SipInbound connection: digest or source IP ACL", "indigo", "vnet"),
                             (340, "Foundry SIP ingress", "a SIP or SIPS URI generated with the binding", "indigo", "private-link")], gap=60))
    yb = top + 3 * LH + 2 * GP
    ep = Box(420, "Foundry project telephony endpoint", sub="matches the call to an active binding (project, agent, callee); calls without a match are not answered", theme="green",
             h=yb - top, size=22, sub_size=15, fill="hatch", icon="foundry", icon_pos="top", icon_size=44)
    ep.place(cv, SX, top)
    for k, lb in enumerate(lanes):
        lane_cy = top + k * (LH + GP) + LH / 2
        connect(cv, lb, ep, a_side="right", b_side="left", ta=0.5, tb=(lane_cy - top) / (yb - top), sw=3, gap=4)
    ann = ["Foundry validates the Entra token Event Grid attaches to each delivery, then answers the call on your ACS resource and streams the audio to the agent",
           "Foundry uses the project connection to list the numbers in your Twilio account and creates one binding per number you select",
           "Configure your trunk or SBC to route inbound calls to the generated SIP or SIPS ingress URI; Foundry authenticates the peer through the SipInbound connection"]
    for k, a in enumerate(ann):
        lane_cy = top + k * (LH + GP) + LH / 2
        lb = lanes[k]
        ax = lb.right + 24
        aw = SX - 70 - ax - 20
        ah = len(wrap_text(a, aw, 14)) * 14 * metrics.line_ratio()
        cv.text(ax, lane_cy - 16 - ah, a, size=14, color=MUTED, wrap=aw)
    bd = Box(380, "Telephony binding", sub="provider (teams_phone_extension, twilio, sip), connection_name, status active or suspended", theme="green", h=170, size=21, sub_size=14,
             fill="hatch", icon="api-connections", icon_pos="top", icon_size=36)
    bd.place(cv, ep.right + 80, top + (yb - top) / 2 - 85)
    va = Box(W - (bd.right + 70), "Voice agent", sub="the agent that owns the binding answers with its active version; transfer to a person through configured targets", theme="green", h=170,
             size=22, sub_size=14, fill="hatch", icon="agent", icon_pos="top", icon_size=36)
    va.place(cv, bd.right + 70, top + (yb - top) / 2 - 85)
    connect(cv, ep, bd, a_side="right", b_side="left", sw=3, gap=4)
    connect(cv, bd, va, a_side="right", b_side="left", sw=3, gap=4)
    y1 = yb + 36    # channel table
    t = Table(
        [("Channel", 280), ("You bring", 560), ("Foundry connection", 640), ("Direction and regions", 700), ("Good to know", 1420)],
        [
            [ct("Playground and preview web app", "gray"), "A browser with microphone and speakers", "None",
             "Testing and sharing", "The web app is shown when the endpoint supports the Responses protocol; Open, Copy link and Grant access (organization sign-in)"],
            [ct("Teams Phone extensibility", "indigo"), "A Teams service number on a resource account; an ACS resource; a Teams or Microsoft 365 admin",
             "An ACS project connection plus the resource-account object ID (a GUID without the 28:orgid: prefix)", "Inbound and outbound (call jobs)",
             "Foundry project and ACS in the same Entra tenant; ACS reached through the project managed identity (no keys); Event Grid secure delivery automatic or manual, up to 500 subscriptions per system topic"],
            [ct("Twilio", "indigo"), "An active voice-capable Twilio number", "A Twilio project connection: Account SID and Primary Auth Token (the token stays in the connection)",
             "Inbound and outbound; public cloud only", "No ACS, Teams resource account or Event Grid; a Twilio binding cannot change number or connection - delete and recreate"],
            [ct("Direct SIP", "indigo"), "A SIP trunk or SBC with SIP over TLS (outbound: non-ICE SDES-SRTP)", "SipInbound or SipOutbound: digest or source IP ACL (SipOutbound: IP ACL only); source_cidrs up to 64, empty = allow all",
             "Inbound: East US 2, France Central, Southeast Asia, Sweden Central, West US. Outbound: Southeast Asia only",
             "Codecs g722, pcmu, pcma, opus, amr-wb (default g722, pcmu, pcma); portal creates connections and inbound bindings, outbound call jobs through the SDK or REST; outbound dispatch must be configured for the service instance"],
            [ct("Teams and Microsoft 365 Copilot publishing", "gray"), "-", "-", "Not a phone path",
             "The standard text-agent card is intentionally hidden for voice agents: publishing to Teams is not connecting a Teams phone number"],
            [ct("Avatar", "gray"), "A browser", "-", "Browser visual output over WebRTC only", "Phone callers get audio only; avatar usage is charged separately"],
        ], w=W, theme="indigo", size=14, head_size=15, title="Channels side by side (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, y1)
    y2 = t.bottom + 36
    a = card(S(2), "Bindings API", [
        ".../agents/{agent}/telephony/bindings: create, list, read, update (merge-patch with If-Match and the latest ETag) and delete",
        "provider teams_phone_extension, twilio or sip; status active or suspended (suspending stops new inbound calls without deleting)",
        "SIP: allowed_calling_numbers up to 64 anchored E.164 patterns, not arbitrary regular expressions; Teams: connection and display number can change, the provider and resource-account ID cannot",
        "azd bindings are create-only and can declare provider twilio or acs in azure.yaml; REST needs Foundry-Features: VoiceAgents=V1Preview",
    ], theme="indigo", icon="api-connections", src=src("tel", "bindrest"))
    b = card(S(2), "Outbound calls (call jobs)", [
        "POST .../telephony/call_jobs with an Idempotency-Key (1 to 256 characters); 202 Accepted means accepted, not answered",
        "retry_policy: fixed interval, max_attempts 1 to 5 including the first; schedule.not_before and expires_at; purpose and structured_inputs",
        "Terminal statuses: completed, blocked, expired, failed, cancelled. Cancel does not hang up a connected call (409 Conflict)",
        "A job ID is not a live call ID; for SIP outbound, publish the agent first",
    ], theme="indigo", icon="scheduler", src=src("tel", "sip"))
    c = card(S(2), "Hand off, manage live calls and tune for the phone", [
        "Transfer targets (PUT .../telephony/transfer_targets): kinds pstn, teams or sip; descriptions tell the agent when to use each; replace the whole list with the ETag",
        "Live calls: list, get, :transfer and :end - use a live call ID",
        "Phone tuning: azure_deep_noise_suppression, a larger silence_duration_ms, phrase_list hints for identifiers, the end_conversation tool",
        "Tracing: the session root span records the provider, the provider call ID and the dialed and calling numbers - personal data",
    ], theme="indigo", icon="gear", src=src("tel"))
    r_, b2 = row(cv, 0, y2, [a, b, c], gap=G)
    return b2

# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Voice agents (Preview): architecture, definition and telephony",
        "Voice-based prompt agents (kind: voice) on Foundry Agent Service  |  part 1: pipelines, models, the definition, the WebSocket session and phone channels  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Tools and toolbox", "orange"), ("Identity and security", "red"),
                           ("Memory and knowledge", "teal"), ("Observability", "violet"), ("Guardrails", "pink"), ("Telephony and networking", "indigo"),
                           ("State and data", "cyan"), ("Cost and capacity", "yellow")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Prompt agents in depth", "Hosted agents: your code on Foundry's runtime", "Foundry Toolbox",
                "Voice agents part 2: hosted voice, operate and migrate", "Foundry Memory (Preview)"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_pipelines(cv, y)
    y = band_compare(cv, y) + 56
    y = band_models(cv, y) + 56
    y = band_definition(cv, y) + 56
    y = band_session(cv, y) + 56
    y = band_telephony(cv, y) + 56
    sources(cv, 0, y, [
        ("Agent Service overview: how voice-based agents work", U["overview"][1]), ("Quickstart: create a voice-based prompt agent", U["qs"][1]),
        ("Configure a voice agent", U["conf"][1]), ("Send image input to a voice agent", U["img"][1]),
        ("Use a subagent in a voice-based agent", U["sub"][1]), ("Integrate telephony channels (Teams Phone extensibility, Twilio)", U["tel"][1]),
        ("Connect a voice agent to telephony via SIP", U["sip"][1]), ("Publish and connect voice agent channels", U["pub"][1]),
        ("Pricing for voice-based agents", U["price"][1]), ("Migrate from Voice Live with Foundry Agent Service", U["migrate"][1]),
        ("Agent Service limits, quotas and regions", U["limits"][1]), ("REST: connect to a voice agent (WebSocket)", U["wsrest"][1]),
        ("REST: create a telephony binding", U["bindrest"][1]), ("Create and manage a toolbox", U["toolbox"][1]),
        ("Voice Live overview (Speech)", U["vl"][1]), ("Teams Phone extensibility overview (ACS)", U["tpe"][1]),
    ], w=W, cols=4)
