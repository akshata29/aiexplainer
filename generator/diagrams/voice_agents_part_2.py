"""Voice-based prompt agents (Preview), part 2: hosted voice agents (the Voice Live Bridge conversation engine and fully custom invocations_ws
pipelines), best practices and instruction design, observability and evaluation, pricing and limits, migrating from Voice Live with a text
agent, and the doc conflicts (Direct SIP, GA vs preview, region and Azure Government facts).

Part 1 ('voice-agents') holds the architecture, models, the definition setting by setting, the WebSocket session and the telephony path.
Preview items carry a Preview badge; time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="voice-agents-part-2", title="Voice agents: hosted voice, operate and migrate", section="2", group="Agent Service", order=15.5,
    description="Voice agents part 2 (Preview): hosted voice (conversation engine and invocations_ws), best practices, tracing and evaluation, "
                "pricing and limits, migrating from Voice Live with a text agent, and the docs conflicts (Direct SIP, GA vs preview).",
    tags=["voice", "hosted-agents", "observability", "pricing", "migration", "best-practices"],
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
    pub=("Publish and share a voice-based agent", learn("agents/how-to/voice-agent-channels-publish")),
    best=("Best practices for voice-based agents", learn("agents/concepts/voice-agent-best-practice")),
    opt=("Optimize instructions for voice agents", learn("agents/how-to/optimize-voice-agent-instructions")),
    obs=("Voice agent tracing, monitoring and evaluation", learn("agents/concepts/voice-agent-observability")),
    price=("Pricing for voice-based agents", learn("agents/concepts/voice-agent-pricing")),
    migrate=("Migrate from Voice Live with Foundry Agent Service", learn("agents/how-to/migrate-from-voice-live")),
    build=("Build a voice agent with hosted agents", learn("agents/how-to/build-voice-agent")),
    engine=("Use a hosted agent as the conversation engine", learn("how-to/voice-first-with-hosted-agent")),
    limits=("Agent Service limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    toolbox=("Use a toolbox in a hosted agent", learn("agents/how-to/tools/use-toolbox-hosted-agent")),
    convrest=("REST: list agent conversations", learn("reference/rest/agent-endpoint-conversations-list-agent-conversations")),
    vl=("Voice Live overview (Speech)", learn("azure/ai-services/speech-service/voice-live", base="")),
    vlhost=("Voice Live with a hosted agent (Speech)", learn("azure/ai-services/speech-service/how-to-voice-live-hosted-agent-integration", base="")),
    vlagents=("Voice Live with a Foundry agent (Speech)", learn("azure/ai-services/speech-service/voice-live-agents-quickstart", base="")),
    vlinteg=("Voice Live agent integration (Speech)", learn("azure/ai-services/speech-service/how-to-voice-agent-integration", base="")),
    gptlive=("GPT-Live", learn("openai/concepts/gpt-live")),
    gptdeleg=("GPT-Live delegation", learn("openai/how-to/gpt-live-delegation")),
    mgmt=("Manage costs for Microsoft Foundry", learn("concepts/manage-costs")),
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


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "2 hosted routes", "A hosted text agent as the conversation engine behind Voice Live, or a fully custom voice pipeline inside your container over invocations_ws.", "green"),
        Tile(C, "TTFA", "Time to first audio is what a caller feels. Trace one conversation per trace; the Monitor tab splits latency by pipeline stage.", "violet"),
        Tile(C, "5 cost drivers", "Audio tokens, model hosting, session length, tools, and optional avatar or storage. Rates live on the pricing pages.", "yellow"),
        Tile(C, "60 min", "Maximum voice session duration; stored voice conversations and Microsoft-managed audio are kept 60 days (as of 2026-11-03).", "cyan"),
        Tile(C, "New agent, not a switch", "A text agent cannot be converted to voice: migrating from Voice Live with a text agent creates a new kind: voice agent.", "blue"),
        Tile(C, "Docs disagree", "Direct SIP (overview vs SIP page) and voice GA vs preview (Learn pages vs a Build 2026 blog) - read section 6 before you rely on either.", "orange"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: hosted voice
def band_hosted(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  Hosted voice agents - two ways to bring your own code",
             "Use Voice Live as the audio layer around a hosted text agent, or run the whole voice pipeline yourself inside a hosted-agent container over the invocations_ws full-duplex WebSocket.")
    top = y
    hw = 1760
    with cv.panel(0, top, title="Route A: hosted conversation engine (Preview)", sub=wrap("Voice Live handles audio; your hosted text agent handles conversation logic, model calls and tools", hw - 60, 15),
                  theme="green", style="solid", fill="soft", pad=22, title_size=26, sub_size=15, min_w=hw, min_h=372) as pa:
        bw, bh = 300, 130
        b1 = Box(bw, "Caller audio", sub="browser, WebRTC or phone channel", theme="gray", h=bh, size=19, sub_size=13, fill="hatch", icon="user", icon_pos="top", icon_size=30)
        b2 = Box(bw, "Voice wrapper agent", sub="kind: voice - keeps audio, voice, greeting and store; Voice Live recognition and synthesis", theme="teal", h=bh, size=19, sub_size=13, fill="hatch",
                 icon="speech", icon_pos="top", icon_size=30)
        b3 = Box(bw + 70, "Hosted target agent", sub="kind: hosted - keeps model, instructions and tools; text and control events over invocations_ws", theme="green", h=bh, size=19, sub_size=13,
                 fill="hatch", icon="container-apps", icon_pos="top", icon_size=30)
        xs = [pa.ix, pa.ix + bw + 90, pa.ix + bw + 90 + bw + 150]
        yy = pa.iy + 10
        b1.place(cv, xs[0], yy)
        b2.place(cv, xs[1], yy)
        b3.place(cv, xs[2], yy)
        connect(cv, b1, b2, a_side="right", b_side="left", sw=3, gap=4)
        connect(cv, b2, b3, a_side="right", b_side="left", sw=3, gap=4, start_head="arrow")
        cv.text(b2.right + 10, yy + bh / 2 - 46, "Bridge\nProtocol 1.0", size=14, color=THEMES["green"].deep, align="center", w=b3.x - b2.right - 20)
        ChipFlow(["conversationEngine { type: hosted_agent, name, version }", "store: false on the wrapper", "wrapper and target need different agent names"], w=hw - 50, theme="green",
                 size=14, fill="soft").place(cv, pa.ix, yy + bh + 24)
        cv.text(pa.ix, yy + bh + 112, "azd path: one azure.yaml declares both services (the wrapper `uses` the target so the target deploys first); SDK path: VoiceHostedAgentConversationEngine inside "
                                      "VoiceAgentDefinition. create_version validates the engine config but not the target - the service checks compatibility when a session starts.",
                size=14, color=INK, wrap=hw - 50)
    with cv.panel(hw + G, top, title="Route B: custom voice agent in your container", sub=wrap("You run the pipeline: Voice Live, Pipecat or LiveKit inside the sandbox", W - hw - G - 60, 15),
                  theme="orange", style="solid", fill="soft", pad=22, title_size=26, sub_size=15, min_w=W - hw - G, min_h=372) as pb:
        bw2, bh2 = 280, 130
        c1 = Box(bw2, "Client", sub="browser or mobile app, or a telephony bridge (ACS or Twilio)", theme="gray", h=bh2, size=19, sub_size=13, fill="hatch", icon="app", icon_pos="top", icon_size=30)
        c2 = Box(bw2 + 40, "Hosted agent container", sub="declares invocations_ws; runs your speech-to-speech or STT -> LLM -> TTS pipeline", theme="orange", h=bh2, size=19, sub_size=13, fill="hatch",
                 icon="container-apps", icon_pos="top", icon_size=30)
        cx0 = pb.ix
        cy0 = pb.iy + 10
        c1.place(cv, cx0, cy0)
        c2.place(cv, cx0 + bw2 + 110, cy0)
        connect(cv, c1, c2, a_side="right", b_side="left", sw=3, gap=4, start_head="arrow")
        cv.text(c1.right + 6, cy0 + bh2 / 2 - 50, "full-duplex\nWebSocket", size=14, color=THEMES["orange"].deep, align="center", w=98)
        ChipFlow(["Voice Live", "Pipecat", "LiveKit Agents", "cascaded", "speech-to-speech"], w=W - hw - G - 50, theme="orange", size=14, fill="soft").place(cv, cx0, cy0 + bh2 + 24)
        cv.text(cx0, cy0 + bh2 + 100, "Hosted agents give the container a dedicated Entra agent identity, so it reaches Foundry models and Toolbox tools without keys. Any containerized voice framework works; "
                                      "these three have validated samples.", size=14, color=INK, wrap=W - hw - G - 50)
    y1 = max(pa.bottom, pb.bottom) + 36
    # protocol facts table
    t = Table(
        [("Aspect", 260), ("Route A: conversation engine", 760), ("Route B: custom invocations_ws", 760)],
        [
            [ct("Who handles audio", "gray"), "Voice Live (managed): recognition, turn-taking, interruptions and synthesis", "Your container: any voice framework you ship"],
            [ct("What the hosted agent sees", "gray"), "Text and control events (Bridge Protocol 1.0) - it does not process caller audio", "Raw audio frames (binary) and JSON control messages on the WebSocket"],
            [ct("Protocol declaration", "gray"), "invocations_ws version 1.0.0 with voiceLiveCompatible: \"true\" and bridgeProtocolVersion: \"1.0\" in the target's metadata",
             "invocations_ws declared in protocol_versions, alone or with responses and invocations (the doc example shows version 2.0.0)"],
            [ct("Roles and identity", "gray"), "The hosted agent's identity needs Cognitive Services OpenAI User on the parent Foundry resource (or equivalent inherited permissions)",
             "Dedicated Entra agent identity; no API keys or connection strings in code; tools through the Toolbox MCP endpoint"],
            [ct("Pick it when", "gray"), "Your hosted code must own the conversation logic for every turn but you want managed audio", "You need a custom audio pipeline, custom voices, or a framework such as Pipecat or LiveKit"],
        ], w=S(4), theme="green", size=14, head_size=15, title="Route A vs Route B", title_size=22)
    t.place(cv, 0, y1)
    n1 = Note(S(2), "Docs differ by page, probably by scenario: the conversation-engine page has the target declare invocations_ws 1.0.0 (and says the Bridge Protocol version is distinct "
                    "from the invocations_ws transport version), while the custom voice-agent examples declare 2.0.0. Check the page for the route you build.", kind="warn",
              title="Docs disagree: the invocations_ws version", size=14, src=src("engine", "build"))
    n1.place(cv, X(4), y1)
    y2 = max(t.bottom, n1.bottom) + 36
    # lifecycle + limits
    lc = Table(
        [("Limit or behavior", 340), ("Value (as of 2026-11-03)", 820)],
        [
            ["Frame types", "Text (UTF-8) for JSON control, binary for audio, continuation, ping/pong keep-alive, close - relayed as raw bytes, not parsed by the platform"],
            ["Maximum frame size", "1 MB (larger frames are rejected with close code 1009); 20 ms PCM at 16 kHz mono is about 640 bytes"],
            ["Maximum connection duration", "About 30 minutes; the platform sends close code 1001 on shutdown drain - reconnect with the same agent_session_id"],
            ["Session state", "The sandbox and in-process state persist across reconnects; the platform does not replay missed frames - you need an application-level resume protocol"],
            ["Authentication", "Entra bearer token on the upgrade Authorization header, validated by the platform; the container does not see it (do not accept an authorization query parameter)"],
            ["Sandbox size", "Up to 2 vCPU / 4 GiB; at least 1 vCPU / 2 GiB recommended for voice"],
            ["Session idle timeout", "2 to 240 minutes (15-minute default); compute is deprovisioned, session state persisted (REST says 120 to 3,600 s: see the hosted-agent canvases)"],
        ], w=S(3) - 160, theme="orange", size=14, head_size=15, title="invocations_ws limits and behavior", title_size=22)
    lc.place(cv, 0, y2)
    wr = card(S(2), "WebRTC media with WebSocket signaling", [
        "Hosted agents have no managed WebRTC media service, TURN service, SFU or signaling protocol",
        "Use invocations_ws as the authenticated signaling channel (JSON text frames such as ice_config, offer, ice_candidate, disconnect); audio flows over the WebRTC peer connection you operate",
        "You provide the TURN relay configuration and any WebRTC reconnect or resume behavior; prefer direct WebSocket audio for prototypes, telephony bridges and controlled networks",
    ], theme="orange", icon="gear", src=src("build"))
    wr.place(cv, S(3) - 160 + G, y2)
    hx = S(3) - 160 + G + wr.w + G
    n2 = Note(W - hx, "Telephony for Route B: a provider such as Azure Communication Services or Twilio bridges PSTN calls to the hosted agent's invocations_ws endpoint and handles SIP signaling, "
                      "media transcoding and DTMF. The native channels on part 1 are for voice-based prompt agents.", kind="info", title="Phone calls", size=14, src=src("build"))
    n2.place(cv, hx, y2)
    return max(lc.bottom, wr.bottom, n2.bottom)


# ================================================================================================ band 2: best practices
def band_practices(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Operate it well - best practices, instruction design and release",
             "From the best-practice and instruction pages: design for time to first audio, make turn-taking natural, write for the ear, protect callers, release by immutable version.")
    top = y
    cw = (W - 3 * G) / 4
    c1 = card(cw, "Design for latency first", [
        "Time to first audio, not total response time, is what a caller experiences",
        "Prefer static_interim_response (no model latency); lower the 2,000 ms threshold for conversation",
        "Cap output with max_output_tokens; keep instructions, context and tool inventories small",
        "Prefer speech-to-speech for conversation; use cascaded only when model, voice, locale or transcription control outweigh the extra stages",
        "Monitor TTFA and stage latency after every release",
    ], theme="violet", icon="monitor", src=src("best"))
    c2 = card(cw, "Natural turn-taking", [
        "Raise silence_duration_ms when callers pause or read numbers; raise threshold in noisy places",
        "Use a semantic turn type when callers pause mid-sentence; basic detection when you must tune thresholds",
        "Change one turn-detection setting at a time; leave interrupt_response on",
        "Match noise_reduction to the channel: near_field, far_field, azure_deep_noise_suppression",
        "Test short answers, hesitant speech and interruptions at the start, middle and end of a reply",
    ], theme="green", icon="speech", src=src("best"))
    c3 = card(cw, "Write for the ear", [
        "One or two sentences per turn; the answer first; one question at a time",
        "No markdown, bullets, headings, tables, raw URLs or long menus",
        "Speak numbers, currency, dates and identifiers as natural words",
        "Greeting: name the organization and two or three capabilities, end with an open question; use the greeting field, not instructions",
        "Add phrase_list hints or custom speech for product names and identifiers",
    ], theme="teal", icon="doc-intelligence", src=src("best", "opt"))
    c4 = card(cw, "Tools, interruptions, handoff", [
        "Return small results; choose response_scheduling deliberately; make operations idempotent",
        "Handle failures out loud and never fabricate - state only what a tool returned",
        "An interruption truncates the context to what was heard: put the useful part first",
        "Decide handoff up front; never claim a transfer succeeded before the downstream system confirms",
        "Add end_conversation so completed calls end instead of idling",
    ], theme="orange", icon="toolbox-icon", src=src("best"))
    _, b1 = row(cv, 0, top, [c1, c2, c3, c4], gap=G)
    y1 = b1 + 36
    # instruction sections
    cv.text(0, y1, "Instruction structure: five sections, in order (the instructions page)", size=22, color=THEMES["green"].deep)
    secs = [("Personality", "who the agent is: a name, a role and a few concrete traits; never guess - look up or hand off"),
            ("Environment", "a live call, the caller only hears, identity unknown until verified, tools are the only source of truth"),
            ("Tone", "short natural replies, no markup, numbers as words, one question at a time, brief acknowledgments"),
            ("Goal", "a numbered sequence with verification and spoken confirmation as steps; close with end_conversation"),
            ("Guardrails", "verify identity first, stay in scope, state only what tools return, hand off on request or failure")]
    sw_ = (W - 4 * 60) / 5
    sb = []
    for i, (t_, s_) in enumerate(secs):
        b = Box(sw_, t_, sub=s_, theme="green", h=170, size=21, sub_size=14, fill="hatch")
        b.place(cv, i * (sw_ + 60), y1 + 40)
        sb.append(b)
    for i in range(4):
        connect(cv, sb[i], sb[i + 1], a_side="right", b_side="left", sw=2.5, gap=3)
    y2 = y1 + 40 + 170 + 36
    t = Table(
        [("Symptom", 560), ("Setting to check before rewriting instructions", 1100)],
        [
            ["The agent interrupts callers who pause mid-sentence", "Increase silence_duration_ms, or use a semantic turn detection type"],
            ["The agent responds to background speech", "Raise threshold and set noise_reduction for the environment"],
            ["The agent speaks too quickly for the audience", "Lower speed on the output configuration"],
            ["Domain terms are transcribed incorrectly", "Add phrase_list hints or configure custom_speech"],
            ["Long silence while a tool runs", "Configure interim_response instead of telling the agent to announce waits"],
        ], w=S(3) - 40, theme="green", size=14, head_size=15, title="Tune audio before prompts", title_size=22)
    t.place(cv, 0, y2)
    rel = Steps(S(3) - 20, "Release safely - every change is an immutable version", [
        "Save a version and test the complete scenario matrix with real audio (typed tests hide transcription errors)",
        "Review traces and run supported evaluations; confirm roles, identities, pricing and quota",
        "Validate browser and telephone channels; pin the tested version for each channel (x-agent-version-override while testing)",
        "Record the released version, monitor the rollout, and keep a tested rollback version",
    ], theme="yellow", num_theme="green", src=src("best", "pub"))
    rel.place(cv, X(3) + 20, y2)
    y3 = max(t.bottom, rel.bottom) + 36
    p1 = card(S(2), "Protect callers and data", [
        "Verify before disclosing; gate account tools behind verification; confirm before high-impact actions",
        "Managed identity or approved Entra authentication with least privilege; never expose secrets in instructions, transcripts or source control",
        "Give required AI, recording and monitoring notices and obtain consent where required",
        "store stays off by default - it persists audio as well as transcripts; trace content capture is a separate privacy decision",
        "Plan deletion: deleting a conversation cascades to its responses, items and audio",
        "Decide storage ownership early: with bring-your-own storage access is governed by Azure RBAC on your account",
    ], theme="red", icon="managed-identity", src=src("best"))
    p2 = card(S(2), "Test across channels and watch the right signals", [
        "Browser and phone audio differ: test built-in and external devices, noisy and quiet rooms, mobile and poor networks, reconnects and DTMF expectations",
        "Test the same version on every channel, preview web app access with a non-developer account, Teams resource-account and Twilio numbers",
        "Track TTFA, barge-in rate and session outcome; rising idle_timeout or client_abort outcomes usually mean callers give up",
        "Text evaluators do not replace human review of pronunciation, prosody, interruption or acoustic quality",
    ], theme="violet", icon="monitor", src=src("best"))
    p3 = card(S(2), "Production readiness checklist (condensed)", [
        "Preview terms accepted; region and model availability confirmed; instructions optimized for listening",
        "Recognition and turn detection pass the scenario matrix; voice and avatar approvals complete; tools least-privilege",
        "Human handoff tested; AI, recording, privacy and consent notices approved; Application Insights access and retention set",
        "Phone-number security and provider callbacks validated (Event Grid delivery for Teams inbound); costs reviewed; a versioned rollback plan exists",
    ], theme="gray", icon="compliance", src=src("best"))
    r_, b3 = row(cv, 0, y3, [p1, p2, p3], gap=G)
    return b3


# ================================================================================================ band 3: observability
def band_obs(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Observe and evaluate - one trace per conversation",
             "Voice agents reuse the Foundry observability stack: the same Application Insights connection, OpenTelemetry data, tracing tools, monitoring dashboard and transcript-based evaluators.")
    top = y
    # pipeline with spans and metric brackets
    names = [("Voice activity detection", "turn start and end", "gray"), ("Speech-to-text", "ASR latency, real-time factor", "teal"), ("Model call", "TTFT, TTLT, tokens per second", "blue"),
             ("Tool calls", "client function or service-run mcp and toolbox", "orange"), ("Text-to-speech", "TTFA, TTLA", "teal"), ("Agent audio", "first audio the caller hears", "green")]
    bw, bh = 330, 140
    gap = (S(4) - 6 * bw) / 5
    bs = []
    for i, (t_, s_, th) in enumerate(names):
        b = Box(bw, t_, sub=s_, theme=th, h=bh, size=18, sub_size=13, fill="hatch")
        b.place(cv, i * (bw + gap), top + 104)
        bs.append(b)
    for i in range(5):
        connect(cv, bs[i], bs[i + 1], a_side="right", b_side="left", sw=2.5, gap=3)
    cv.text(0, top, "Spans in one voice turn (a trace holds one span per turn with child spans per stage)", size=20, color=THEMES["violet"].deep)
    hbrace(cv, bs[0].right - 30, bs[5].x + 60, top + 104 + bh + 24, side="bottom", depth=16)
    cv.text(bs[1].x, top + 104 + bh + 52, "Time to first audio (TTFA): from the end of voice activity detection to the first agent audio", size=16, color=THEMES["violet"].deep, align="center", w=S(2))
    hbrace(cv, bs[2].x + 20, bs[2].right - 20, top + 104 - 14, side="top", depth=12)
    cv.text(bs[2].x - 20, top + 104 - 56, "TTFT: end of VAD to the first generated token", size=14, color=THEMES["violet"].deep, align="center", w=bw + 40)
    tv = Table(
        [("Trace view", 220), ("What it shows", 810)],
        [
            [ct("Trajectories", "violet"), "The voice pipeline as a span tree and waterfall timeline: duration and hierarchy of every stage per turn"],
            [ct("User view", "violet"), "Caller and agent turns linked to spans, with full-conversation and per-turn audio playback when audio is available"],
            [ct("Graph view", "violet"), "The conversation connected to agent turns and their VAD, speech-to-text, model and text-to-speech operations"],
        ], w=S(2), theme="violet", size=14, head_size=15, title="Three trace views", title_size=22)
    tv.place(cv, X(4), top)
    y1 = max(top + 104 + bh + 100, tv.bottom) + 30
    m = Table(
        [("Monitor tab metric", 330), ("What it shows", 840)],
        [
            ["Average time to first audio", "Start of a caller turn to first agent audio; NaN means telemetry was found but no valid sample, not zero seconds"],
            ["Total sessions, duration, turns", "Session counts, total and average duration, total turns and average turns per session"],
            ["Audio token usage", "Input, output and cached audio token categories when the model emits them"],
            ["Concurrent sessions", "Estimated peak concurrent sessions per minute for the agent - a usage chart, not a concurrency quota"],
            ["New connections per minute (NCPM)", "The agent's NCPM, total NCPM across all agents in the Foundry resource, and the shared resource-level NCPM quota (Request quota link)"],
            ["Tokens per minute (TPM)", "The agent's model token usage; no TPM quota comparison is drawn"],
        ], w=S(2) + 90, theme="violet", size=14, head_size=15, title="Monitoring: summary and quota", title_size=22)
    m.place(cv, 0, y1)
    lt = Table(
        [("Latency chart", 260), ("What it shows", 810)],
        [
            ["Overall latency", "TTFT and TTFA, both measured from the end of voice activity detection"],
            ["LLM latency", "Time to first token, time to last token and tokens per second"],
            ["Speech-to-text latency", "ASR latency and real-time factor (recognition time divided by audio duration; below 1 is faster than real time)"],
            ["Text-to-speech latency", "Time to first audio chunk and time to last audio"],
            ["Errors", "Invalid request errors separated from server errors"],
        ], w=S(2) - 60, theme="violet", size=14, head_size=15, title="Latency charts by stage", title_size=22)
    lt.place(cv, S(2) + 90 + G, y1)
    n1 = Note(S(2), "Insights and ROI tabs are not currently available for voice-based agents; recurring evaluations run on a fixed schedule, but event-triggered evaluations are not supported for "
                    "full-conversation voice evaluation. Voice-specific monitoring cards need Application Insights.", kind="gotcha", title="Not available (as of 2026-11-03)", size=14, src=src("obs", "overview"))
    n1.place(cv, X(4), y1)
    y2 = max(m.bottom, lt.bottom, n1.bottom) + 36
    ev = Table(
        [("Evaluation workflow", 330), ("Voice behavior", 1100)],
        [
            [ct("Dataset-based", "violet"), "Stored voice transcripts from a JSONL dataset, with the standard turn-level or conversation-level evaluators"],
            [ct("Trace-based", "violet"), "Existing conversations ingested from Application Insights, selected by trace ID, conversation ID or agent and time filters; one trace = one conversation row"],
            [ct("Simulation-based", "violet"), "Scenarios run against the voice agent; adds a text-to-speech voice, audio effects (volume-controlled) and simulated user interruptions; Foundry User at account scope"],
        ], w=S(3) - 60, theme="violet", size=14, head_size=15, title="Three evaluation workflows (transcript-based evaluators)", title_size=22)
    ev.place(cv, 0, y2)
    c1 = card(S(3) // 2 - 12 + 60, "Evaluators judge text, not sound", [
        "Intent resolution, task adherence, tool-call accuracy, coherence, relevance, groundedness and content safety work on transcripts",
        "They do not assess pronunciation, prosody, echo, background noise, audio quality or interruption timing",
        "The overview also lists single-turn and simulated-conversation evaluation as not currently supported (docs disagree - section 6)",
    ], theme="violet", icon="monitor", src=src("obs", "overview"))
    c1.place(cv, X(3) + 20, y2)
    y3 = max(ev.bottom, c1.bottom) + 28
    st = card(S(2), "Stored conversations (store = true)", [
        "Persists the transcript, event timeline and raw audio together; the default is false and there is no separate audio-logging switch",
        "Read them at /agents/{agent}/endpoint/protocols/voice/conversations: per-turn text and audio plus a merged stereo recording (caller left, agent right)",
        "Deleting a stored conversation also deletes its responses, items and audio; recording finalization is not necessarily immediate",
        "Retention: stored voice conversations and Microsoft-managed audio 60 days; with bring-your-own storage, recordings come back as a URI in your account governed by Azure RBAC",
        "Application Insights retention controls telemetry, not stored voice conversations and audio",
    ], theme="cyan", icon="storage", src=src("obs", "limits", "convrest"))
    ac = card(S(2), "Access boundaries", [
        "Tracing, trace viewing, annotation writes, evaluation submission and service-side trace reads are separate authorization operations",
        "The project managed identity emits Agent Service traces; a hosted agent can use its own identity; viewers need Log Analytics Reader (protected tables: Privileged Monitoring Data Reader)",
        "Trace evaluations: Reader for the project managed identity on the connected Application Insights resource",
        "Viewing a trace does not grant permission to save an annotation (builder annotations are tagged source builder)",
    ], theme="red", icon="log-analytics", src=src("obs"))
    pv = card(S(2), "Privacy: content capture is separate", [
        "Transcripts and audio references are not captured in traces by default - treat content capture as a privacy decision, not a debugging setting",
        "Audio stays in voice-agent-owned storage; Application Insights keeps only the telemetry reference; audio is requested only on playback or download",
        "Anyone who can read the connected Application Insights resource and protected telemetry can read captured content",
        "Phone numbers are personal data: the session root span carries the provider, provider call ID and dialed and calling numbers; no Responses response_id exists for voice traces",
    ], theme="pink", icon="content-safety", src=src("obs"))
    r_, b3 = row(cv, 0, y3, [st, ac, pv], gap=G)
    return b3


# ================================================================================================ band 4: pricing and limits
def band_pricing(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Pricing drivers, limits and availability",
             "The docs give qualitative meters only - no per-minute rates. For current rates use the Foundry pricing pages; Microsoft Cost Management for billing.")
    top = y
    t = Table(
        [("Cost driver", 250), ("Effect", 900)],
        [
            [ct("Audio tokens", "yellow"), "Caller audio and agent speech are both tokenized; audio tokens typically outnumber text tokens in a voice session by a wide margin"],
            [ct("Model hosting", "yellow"), "managed models are billed through the service as part of the voice agent; self_deployed through your own Foundry model deployment's pricing model"],
            [ct("Session length", "yellow"), "Cost scales with connected conversation time because audio is consumed and produced continuously"],
            [ct("Tools", "yellow"), "Tool calls add model turns; toolboxes and MCP servers bill through their own resources"],
            [ct("Optional features", "yellow"), "Avatars add video synthesis; store = true adds storage for transcripts and audio"],
        ], w=S(2) + 60, theme="yellow", size=14, head_size=15, title="Five things drive the cost of a voice agent", title_size=22)
    t.place(cv, 0, top)
    rd = card(S(2) - 60, "Reduce cost", [
        "Cap max_output_tokens; write short instructions (they are resent every turn)",
        "Prefer static interim responses (an LLM one adds a model call on every trigger)",
        "End calls deliberately with end_conversation; keep store off unless you review conversations",
        "Scope tools: every attached tool adds tokens to each turn's context",
    ], theme="yellow", icon="cost-management", src=src("price", "mgmt"))
    rd.place(cv, S(2) + 60 + G, top)
    est = card(S(2), "See usage before the invoice", [
        "Traces carry per-turn token usage and estimated-cost attributes on the turn span and the session root span",
        "Split into a managed and a self-deployed component under microsoft.foundry.voice.estimated_cost.*; avatar cost is reported separately on the root span",
        "! Estimates for analysis and tuning, not commerce or invoice records - use Microsoft Cost Management",
        "Stored conversations expose a usage field after the session completes",
    ], theme="violet", icon="metrics", src=src("price", "obs"))
    est.place(cv, X(4), top)
    y1 = max(t.bottom, rd.bottom, est.bottom) + 36
    pot = card(S(2), "Potential charges (the overview's list)", [
        "Generative AI model input and output; speech recognition and synthesis",
        "Custom voice training and hosting; avatar usage",
        "Application Insights ingestion and retention",
        "Azure Communication Services calling and phone numbers; Microsoft Teams and telephony services",
        "Connected tools and data services",
    ], theme="gray", icon="cost-management", src=src("overview", "price"))
    pot.place(cv, 0, y1)
    lim = Table(
        [("Limit, setting or availability", 560), ("Value (as of 2026-11-03)", 560)],
        [
            ["Maximum voice session duration", "60 minutes"],
            ["Stored voice conversations and Microsoft-managed audio retention", "60 days"],
            ["Voice-based agents in Azure Government", "No (prompt agents: yes; hosted agents: no)"],
            ["Regions without voice-based agents", "Poland Central and Spain Central (the regional table shows No)"],
            ["Region rule", "The region must support Agent Service and the Voice Live capabilities for the model and channel you pick"],
            ["Direct SIP inbound / outbound regions", "East US 2, France Central, Southeast Asia, Sweden Central, West US / Southeast Asia only"],
            ["Twilio", "Public cloud only"],
        ], w=S(2) + 60, theme="cyan", size=14, head_size=15, title="Limits and availability", title_size=22)
    lim.place(cv, X(2), y1)
    n1 = Note(S(2) - 60, "Not published in the pages read: per-minute or per-token prices for voice agents, Voice Live meter rates, the NCPM quota value, and hosted voice-agent prices "
                         "(rates live on the Azure pricing pages). Nothing on this canvas fills those gaps.", kind="quote", title="What the docs do not say", size=14, src=src("price"))
    n1.place(cv, X(4) + 60, y1)
    return max(pot.bottom, lim.bottom, n1.bottom)


# ================================================================================================ band 5: migrate
def band_migrate(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Migrate from Voice Live with a Foundry text agent to a Foundry voice agent",
             "A voice agent is a separate kind: voice agent (a text agent's interaction mode cannot be changed), so migration creates a new agent. Each voice conversation is a new record.")
    top = y
    with cv.panel(0, top, title="Today: Voice Live around a text agent", sub=wrap("Every spoken turn passes through the separate text agent", 1000, 15), theme="gray", style="dotted", pad=20,
                  title_size=24, sub_size=15, min_w=S(2) + 20, min_h=330) as pa:
        a = [Box(150, "Caller audio", theme="gray", h=84, size=16, fill="hatch"), Box(240, "Voice Live", sub="recognition, turn detection", theme="teal", h=84, size=16, sub_size=12, fill="hatch"),
             Box(300, "Foundry text agent", sub="text model, instructions, tools, knowledge", theme="green", h=84, size=16, sub_size=12, fill="hatch"),
             Box(220, "Voice Live", sub="speech synthesis", theme="teal", h=84, size=16, sub_size=12, fill="hatch")]
        x = pa.ix
        bx = []
        for b in a:
            b.place(cv, x, pa.iy + 14)
            bx.append(b)
            x += b.w + 44
        for p_, q_ in zip(bx, bx[1:]):
            connect(cv, p_, q_, a_side="right", b_side="left", sw=2.5, gap=3)
        cv.text(pa.ix, pa.iy + 128, "Endpoint /voice-live/realtime on the Voice Live resource; the Python client is azure-ai-voicelive; telephony is your own integration (provider APIs or a solution accelerator).",
                size=14, color=INK, wrap=S(2) - 30)
        cv.text(pa.ix, pa.iy + 186, "Traces cover the text-model interaction only: turn detection, audio input and audio output are not in the agent trace.", size=14, color=MUTED, wrap=S(2) - 30)
    with cv.panel(X(2) + 20, top, title="After: one versioned kind: voice definition", sub=wrap("Voice Live runs the definition; no separate text agent per turn", 1000, 15), theme="green",
                  style="solid", fill="soft", pad=20, title_size=24, sub_size=15, min_w=S(4) - 20, min_h=330) as pb:
        b1 = Box(520, "Foundry voice agent", sub="model, instructions, audio, greeting and tools in one definition; speech-to-speech or cascaded", theme="green", h=140, size=21, sub_size=14, fill="hatch")
        b1.place(cv, pb.ix, pb.iy + 14)
        o = [("Tools and knowledge", "client functions, MCP, toolboxes (Foundry IQ through MCP)", "orange"), ("Optional specialist", "your existing prompt or hosted agent as a subagent", "green"),
             ("Phone and storage", "built-in telephony; opt-in transcripts and audio", "indigo")]
        ob = []
        oy = pb.iy + 14 - 30
        for t_, s_, th in o:
            b = Box(560, t_, sub=s_, theme=th, h=78, size=17, sub_size=13, fill="hatch")
            b.place(cv, pb.ix + 520 + 110, oy)
            ob.append(b)
            connect(cv, b1, b, a_side="right", b_side="left", route="elbow", sw=2.5, gap=4)
            oy += 78 + 14
        cv.text(pb.ix, pb.iy + 176, "Endpoint: the voice protocol path under the project and agent. Client: azure-ai-projects beta.voice_agents.realtime. Voice-pipeline traces include turn detection and audio.",
                size=14, color=INK, wrap=520)
    y1 = top + 330 + 40
    t1 = Table(
        [("Migration approach", 330), ("Use it when", 620), ("What to change", 700)],
        [
            [ct("Model-backed voice agent", "green"), "The voice agent should handle the conversation and call tools directly", "Adapt instructions, select a supported model, reconfigure tools"],
            [ct("Text agent as a subagent", "green"), "Keep specialist reasoning, retrieval or business logic in an existing prompt or hosted agent", "Configure subagent_config and say when to delegate; same project; not in VNet-isolated projects"],
            [ct("Hosted conversation engine", "green"), "Your hosted code must own the conversation logic for every turn", "Follow the hosted conversation engine guide; the target needs Bridge Protocol 1.0 over invocations_ws"],
        ], w=S(3) - 40, theme="green", size=14, head_size=15, title="Choose how to reuse your existing agent", title_size=22)
    t1.place(cv, 0, y1)
    st = Steps(S(3) - 20, "Cutover, step by step", [
        "Inventory the source: agent name and version, model, instructions, tools, connections, Voice Live settings (reassemble microsoft.voice-live.configuration), client session.update overrides, auth",
        "Create a NEW voice agent (portal: Voice interaction mode; code: VoiceAgentDefinition) - creating it does not copy tools, connections or history",
        "Map settings into the definition, reconnect tools and knowledge, then update the client connection and event handlers",
        "Test side by side: business behavior, speech, turn-taking, tools, identity, history, channels, TTFA, reliability, cost",
        "Pin the tested version and switch traffic gradually; let existing calls finish; keep the old path for rollback; retire it last",
    ], theme="yellow", num_theme="green", src=src("migrate"))
    st.place(cv, X(3) + 20, y1)
    y2 = max(t1.bottom, st.bottom) + 36
    m1 = Table(
        [("Existing Voice Live setting", 420), ("Voice-agent definition field", 420), ("Migration action", 800)],
        [
            ["Text-agent instructions", "instructions", "Adapt for speech, or keep specialist instructions on the subagent"],
            ["session.voice.name / .type / .temperature", "audio.output.voice / voice_type / voice_temperature", "Voice name is a string, not a nested object; temperature only for voice types that support it"],
            ["session.input_audio_transcription", "audio.input.transcription", "Set the transcription model explicitly and carry over language and vocabulary settings"],
            ["session.turn_detection", "audio.input.turn_detection", "Review pause detection, automatic response creation, interruption and truncation"],
            ["session.input_audio_noise_reduction / _echo_cancellation", "audio.input.noise_reduction / echo_cancellation", "Preserve noise reduction; match the echo reference source and channel layout to your client"],
            ["session.input_audio_format / output_audio_format", "audio.input.format / audio.output.format", "Use format objects such as {type: audio/pcm, rate: 24000} instead of the legacy pcm16 string"],
            ["session.modalities", "output_modalities", "Audio output defaults to [audio]; do not copy the old array without review"],
            ["session.interim_response / client-generated opening", "interim_response / greeting", "Reconfigure on the definition; choose a template or an LLM-generated greeting and remove the old startup trigger"],
        ], w=S(3) - 40, theme="blue", size=14, head_size=15, title="Move voice settings into the definition", title_size=22)
    m1.place(cv, 0, y2)
    ev = Table(
        [("Purpose", 300), ("Older Voice Live event", 420), ("Voice-agent v1 event", 440)],
        [
            ["Stream reply audio", "response.audio.delta / .done", "response.output_audio.delta / .done"],
            ["Stream the reply transcript", "response.audio_transcript.delta / .done", "response.output_audio_transcript.delta / .done"],
            ["Stream text output", "response.text.delta / .done", "response.output_text.delta / .done"],
            ["Append, commit, clear input; speech started and stopped", "input_audio_buffer.*", "Unchanged"],
            ["Create or cancel a response; response state", "response.create / cancel; response.created / done", "Unchanged - do not create a second response while one is active"],
            ["Function arguments and results", "response.function_call_arguments.*; conversation.item.create with function_call_output", "Unchanged - the client must implement the call loop"],
        ], w=S(3) + 90, theme="blue", size=14, head_size=15, title="Event renames (the rest is unchanged)", title_size=22)
    ev.place(cv, X(3) + 20, y2)
    y3 = max(m1.bottom, ev.bottom) + 28
    c1 = card(S(2), "Client connection changes", [
        "Use the Foundry project endpoint, not the Voice Live resource endpoint; api-version=v1 plus Foundry-Features: VoiceAgents=V1Preview",
        "Raw WebSocket: replace /voice-live/realtime with /api/projects/<project>/agents/<agent>/endpoint/protocols/voice; Entra token for https://ai.azure.com/.default in the Authorization header",
        "Pin a version with x-agent-version-override; azure-ai-voicelive becomes azure-ai-projects[voice] beta.voice_agents.realtime",
        "Remove startup code that resends the full legacy session configuration; keep only supported per-session overrides",
    ], theme="red", icon="key", src=src("migrate"))
    c2 = card(S(2), "Reconnect tools and knowledge", [
        "Foundry IQ knowledge bases: an mcp tool, directly or through a toolbox; remote or custom MCP servers: native mcp or toolbox",
        "Azure AI Search and file search, web search and code interpreter, OpenAPI business APIs, A2A, browser automation, Fabric IQ and Work IQ: a toolbox reference",
        "Custom function calling: a native function tool, with the WebSocket function-call loop in your client",
        "The toolbox is referenced rather than every text-agent tool type being accepted directly; do not copy the text agent's tools array unchanged",
    ], theme="orange", icon="toolbox-icon", src=src("migrate"))
    c3 = card(S(2), "History, recordings and monitoring at cutover", [
        "Start a new voice conversation at cutover; prior text-agent history is not imported by conversation ID",
        "Decide on store (default false); capture the conversation ID from session.created for correlation and read-back",
        "Conversation storage and trace content capture stay separate controls; configure voice tracing and monitoring first",
        "Voice Live and text-agent pages under Speech remain, now pointing to Foundry voice agents (as of 2026-11-03)",
    ], theme="cyan", icon="storage", src=src("migrate", "vlagents"))
    r_, b3 = row(cv, 0, y3, [c1, c2, c3], gap=G)
    return b3


# ================================================================================================ band 6: gotchas
def band_gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Docs disagree and what is not documented - as of 2026-11-03",
             "Where two Learn pages (or Learn and a blog) give different answers, both sides are shown. Verify against the live pages before you rely on one.")
    t = Table([("Topic", 300), ("One source says", 860), ("Another source says", 860), "How to read it"], [
        [ct("Direct SIP", "orange"), "Agent Service overview: Direct SIP is 'not currently offered as a supported customer flow' (phone numbers: Teams Phone extensibility and Twilio)",
         "The SIP how-to documents Direct SIP (Preview): SipInbound and SipOutbound connections, a generated ingress URI, inbound in five regions and outbound in Southeast Asia only",
         "Treat Direct SIP as available only where you have confirmed it for your subscription and region"],
        [ct("Voice GA or preview", "orange"), "Learn voice pages (Oct 2026) mark voice-based prompt agents, telephony and SIP as preview",
         "A Build 2026 recap (blog, not Learn) lists 'Voice Live prompt agents: generally available' and hosted voice agents as public preview",
         "Probably different products (Voice Live with a text agent vs the kind: voice agent) - the docs do not say so explicitly"],
        [ct("Evaluation scope", "orange"), "The overview: single-turn and simulated-conversation evaluation are not currently supported for voice agents",
         "The observability page documents dataset-, trace- and simulation-based evaluation workflows for voice agents (voice simulation adds voice, audio effects and interruptions)",
         "The newer observability page reads as current; the overview may lag"],
        [ct("Teams publishing", "orange"), "Voice-agent Channels hide the standard Teams and Microsoft 365 Copilot publishing card on purpose",
         "Publish to Teams and connecting a Teams phone number are different integrations; the general Agent Application route may not match the native voice media path",
         "Use Teams Phone extensibility for phone calls; verify support before releasing an Agent Application route"],
        [ct("Azure Government and regions", "orange"), "Voice-based agents are not available in Azure Government; Poland Central and Spain Central show No",
         "The region must support Agent Service and the Voice Live capabilities for your model and channel",
         "Check the portal model and voice menus per resource and region"],
    ], w=S(6), theme="orange", size=14, head_size=15, title="Docs disagree", title_size=22)
    t.place(cv, 0, y)
    ny = t.bottom + 30
    g1 = Note(S(2), "Voice agent tools: use individual tools OR one toolbox, not both; parallel_tool_calls is unsupported; subagents are not supported in VNet-isolated projects; the "
                    "Foundry-Features: VoiceAgents=V1Preview header is required on REST calls; the old azure-ai-voiceagents package and /voice_agents route are obsolete.",
              kind="gotcha", title="Definition gotchas", src=src("conf", "migrate", "sub"))
    g1.place(cv, 0, ny)
    g2 = Note(S(2), "Telephony: Twilio is public cloud only and a Twilio binding rewrites the number's voice URL; outbound SIP is Southeast Asia only; a 202 call-job response is not an answered call; "
                    "cancel does not hang up a connected call; caller ID is asserted signaling, not identity proof.", kind="warn", title="Phone gotchas", src=src("tel", "sip"))
    g2.place(cv, X(2), ny)
    g3 = Note(S(2), "Not documented in the pages read: a voice-agent SLA, hosted-voice and voice-per-minute prices, cold-start latency figures, the NCPM quota value, and how a WebRTC "
                    "transport interacts with BYOM or hosted voice agents beyond 'not supported'. Nothing on this canvas fills those gaps.", kind="quote", title="What the docs do not say",
              src=src("overview"))
    g3.place(cv, X(4), ny)
    return max(g1.bottom, g2.bottom, g3.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Voice agents: hosted voice, operate and migrate",
        "Part 2 of 'Voice agents'  |  hosted voice routes, best practices, tracing and evaluation, pricing and limits, migrating from Voice Live with a text agent, docs conflicts  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models and speech", "teal"), ("Tools and toolbox", "orange"), ("Identity and security", "red"),
                           ("Observability", "violet"), ("Guardrails and privacy", "pink"), ("Cost and capacity", "yellow"), ("State and data", "cyan"), ("Neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Voice agents (Preview): architecture, definition and telephony", "Foundry Agent Service: the map", "Hosted agents: your code on Foundry's runtime",
                "Hosted agents: deploy and operate", "Foundry Toolbox", "Observability: one data model"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 56
    y = band_hosted(cv, y) + 56
    y = band_practices(cv, y) + 56
    y = band_obs(cv, y) + 56
    y = band_pricing(cv, y) + 56
    y = band_migrate(cv, y) + 56
    y = band_gotchas(cv, y) + 56
    sources(cv, 0, y, [
        ("Agent Service overview: how voice-based agents work", U["overview"][1]), ("Build a voice agent with hosted agents", U["build"][1]),
        ("Use a hosted agent as the conversation engine", U["engine"][1]), ("Best practices for voice-based agents", U["best"][1]),
        ("Optimize instructions for voice agents", U["opt"][1]), ("Voice agent tracing, monitoring and evaluation", U["obs"][1]),
        ("Pricing for voice-based agents", U["price"][1]), ("Migrate from Voice Live with Foundry Agent Service", U["migrate"][1]),
        ("Publish and share a voice-based agent", U["pub"][1]), ("Connect a voice agent to telephony via SIP", U["sip"][1]),
        ("Agent Service limits, quotas and regions", U["limits"][1]), ("Agent Service in Azure Government", U["gov"][1]),
        ("REST: list agent conversations", U["convrest"][1]), ("Voice Live overview (Speech)", U["vl"][1]),
        ("Voice Live with a Foundry agent (Speech)", U["vlagents"][1]), ("Hosted agents (concepts)", U["hosted"][1]),
    ], w=W, cols=4)
