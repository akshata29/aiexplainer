"""Model APIs and capabilities (2/2): images, video, embeddings, audio and realtime, GPT-Live, MAI models, Claude hosting, coding agents and webhooks."""
from __future__ import annotations

from generator.xd import *
from generator.xd import Note as _KitNote
from generator.xd import metrics
from generator.xd import theme as get_theme

META = dict(
    id="model-apis-capabilities-part-2", title="Media, voice, MAI models and Claude on Foundry", section="2", group="Models", order=25.5,
    description="The rest of the capability map: image and video generation, embeddings, audio, Realtime and GPT-Live voice, the Microsoft AI (MAI) models, "
                "Claude hosted on Azure or on Anthropic, coding agents and webhooks.",
    tags=["realtime", "gpt-live", "mai", "claude", "images", "webhooks"],
)

W, G, C = 3000, 48, 460          # canvas width, standard gap, one-column card width (6-column grid)
MUTED_ = "#495057"


def span(n: int) -> float:
    return n * C + (n - 1) * G


def colx(i: int) -> float:
    return i * (C + G)


def L(label: str, path: str, base: str = "azure/foundry"):
    return (label, learn(path, base=base))


S_IMG = L("Image generation models", "openai/how-to/dall-e")
S_VIDEO = L("Video generation with Sora", "openai/concepts/video-generation")
S_VISION = L("Vision-enabled chats", "openai/how-to/gpt-with-vision")
S_EMB = L("Embeddings", "openai/how-to/embeddings")
S_MAIIMG = L("MAI-Image models", "foundry-models/how-to/use-foundry-models-mai-image")
S_MAITHINK = L("MAI-Thinking-1", "foundry-models/how-to/use-foundry-models-mai-thinking")
S_MSDEC = L("Microsoft-Decision-1", "foundry-models/how-to/use-foundry-models-microsoft-decision")
S_RT2 = L("Realtime API (GPT Realtime 2)", "openai/concepts/realtime-2")
S_RTWEBRTC = L("Realtime audio with WebRTC", "openai/how-to/realtime-audio-webrtc")
S_RTSIP = L("Realtime audio with SIP", "openai/how-to/realtime-audio-sip")
S_LIVE = L("GPT-Live", "openai/concepts/gpt-live")
S_LIVEWEBRTC = L("GPT-Live with WebRTC", "openai/how-to/gpt-live-webrtc")
S_LIVEDELEG = L("GPT-Live delegation", "openai/how-to/gpt-live-delegation")
S_TRANSLATE = L("GPT Realtime Translate", "openai/concepts/gpt-realtime-translate")
S_WHISPER = L("GPT Realtime Transcribe", "openai/concepts/gpt-realtime-whisper")
S_MAIVOICE = ("MAI voices", learn("azure/ai-services/speech-service/mai-voices", base=""))
S_MAITRANS = ("MAI-Transcribe", learn("azure/ai-services/speech-service/mai-transcribe", base=""))
S_MAISTREAM = ("MAI-Transcribe-2-Streaming", learn("azure/ai-services/speech-service/mai-transcribe-2-streaming", base=""))
S_CLAUDE = L("Claude models in Foundry", "foundry-models/concepts/claude-models")
S_CLAUDEUSE = L("Use Claude in Foundry", "foundry-models/how-to/use-foundry-models-claude")
S_CLAUDEHOST = L("Claude hosting comparison", "foundry-models/concepts/claude-models-hosting-comparison")
S_CLAUDEQ = L("Claude quotas and limits", "foundry-models/concepts/claude-models-quotas-limits")
S_CLAUDEBILL = L("Claude billing (CCU)", "foundry-models/concepts/claude-models-billing")
S_CLAUDEPRIV = L("Claude data privacy", "responsible-ai/claude-models/data-privacy")
S_CCODE = L("Configure Claude Code", "foundry-models/how-to/configure-claude-code")
S_CDESK = L("Configure Claude Desktop", "foundry-models/how-to/configure-claude-desktop")
S_CODEX = L("Codex CLI on Azure", "openai/how-to/codex")
S_HOOKS = L("Webhooks", "openai/how-to/webhooks")
S_SCHED = L("Model retirement schedule", "openai/concepts/model-retirement-schedule")


# ---------------------------------------------------------------------------------------------- helpers
def Note(w, text, **kw):
    """Kit Note plus bottom breathing room when it carries a Learn: link (the kit draws that link flush with the border)."""
    n = _KitNote(w, text, **kw)
    if kw.get("src") and "min_h" not in kw:
        n = _KitNote(w, text, min_h=n.h + 14, **kw)
    return n


def banner(cv, y, n, title, sub=None, theme="lime"):
    """Numbered section banner across the canvas; returns the y where content can start."""
    numbered(cv, 24, y + 26, n, theme=theme, d=44, size=24)
    _, bottom = section_header(cv, 60, y, title, sub, size=32, sub_size=17, w=W - 60)
    return bottom + 26


def tile_h(num, label, sub, w, num_size=60):
    nw, nh = text_size(num, num_size)
    avail = (w - (26 + nw + 22) - 16) * 0.965
    lr = metrics.line_ratio()
    return max(nh + 24, len(wrap_text(label, avail, 21)) * 21 * lr + 4 + len(wrap_text(sub, avail, 15)) * 15 * lr + 28)


def tile(cv, x, y, w, h, num, label, sub, th_name, num_size=60):
    """Big-number summary tile."""
    th = get_theme(th_name)
    cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    nw, nh = text_size(num, num_size)
    cv.text(x + 26, y + (h - nh) / 2, num, size=num_size, color=th.deep)
    tx = x + 26 + nw + 22
    avail = (w - (tx - x) - 16) * 0.965
    lab, sl = wrap_text(label, avail, 21), wrap_text(sub, avail, 15)
    lr = metrics.line_ratio()
    total = len(lab) * 21 * lr + 4 + len(sl) * 15 * lr
    ty = y + (h - total) / 2
    cv.text(tx, ty, "\n".join(lab), size=21, color=th.deep)
    cv.text(tx, ty + len(lab) * 21 * lr + 4, "\n".join(sl), size=15, color=INK)
    cv.register("tile:" + label, x, y, w, h)


def code_need(w, lines, size=15, notes=None, src=None):
    """Natural height of a code_box (code lines, optional bullet notes, optional Learn link)."""
    lh = size * metrics.line_ratio(metrics.MONO)
    need = 12 + 26 + 8 + len(lines) * lh + 14 + (18 if src else 0)
    if notes:
        need += 34 + sum(len(wrap_text(t, w - 56, 15)) * 15 * metrics.line_ratio() + 5 for t in notes)
    return need


def code_box(cv, x, y, w, title, lines, th_name="blue", size=15, h=None, src=None, notes=None):
    """Monospace code panel with a coloured title (and optional 'reading the call' bullets); returns its height."""
    th = get_theme(th_name)
    lh = size * metrics.line_ratio(metrics.MONO)
    H = max(code_need(w, lines, size, notes, src), h or 0)
    cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
    cv.text(x + 16, y + 10, title, size=18, color=th.deep)
    cv.text(x + 16, y + 44, "\n".join(lines), size=size, color=INK, font=metrics.MONO)
    if notes:
        ny = y + 44 + len(lines) * lh + 20
        cv.line((x + 16, ny - 8), (x + w - 16, ny - 8), stroke=th.stroke, sw=1, dash="dashed")
        cv.text(x + 16, ny, "Reading the call", size=16, color=th.deep)
        ny += 26
        for t in notes:
            tl = wrap_text(t, w - 56, 15)
            cv.ellipse(x + 18, ny + 6, 8, 8, stroke=th.stroke, sw=2, rough=0)
            cv.text(x + 38, ny, "\n".join(tl), size=15, color=INK)
            ny += len(tl) * 15 * metrics.line_ratio() + 5
    if src:
        cv.text(x + 16, y + H - 26, "Learn: " + src[0], size=12, color=LINK, link=src[1])
    cv.register("code:" + title, x, y, w, H)
    return H


def std(theme, title, body, w=C, **kw):
    """Standard dense card (consistent type scale)."""
    kw.setdefault("title_size", 20)
    kw.setdefault("body_size", 15)
    return Card(w, title, body, theme=theme, **kw)


def two_pass(fn, cv, y):
    """Run a section twice: measure the side-by-side panels on a scratch canvas, then draw them all at the tallest height."""
    _, hs = fn(Canvas("scratch"), y, 0)
    return fn(cv, y, max(hs))[0]


def flow_steps(cv, x, y, w, steps, th_name, gap=30):
    """Vertical numbered steps joined by arrows; returns bottom y."""
    bxs = []
    cy = y
    for i, (t, s) in enumerate(steps):
        b = Box(w - 44, t, sub=s, theme=th_name, size=18, sub_size=14, fill="hatch", pad=12)
        b.place(cv, x + 44, cy)
        numbered(cv, x + 18, b.cy, i + 1, theme=th_name, d=32, size=18)
        bxs.append(b)
        cy = b.bottom + gap
    for a, b in zip(bxs, bxs[1:]):
        connect(cv, a, b, a_side="bottom", b_side="top", sw=2)
    return bxs[-1].bottom


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Media, voice, MAI models and Claude on Foundry",
        "Images, video, embeddings, Realtime and GPT-Live, the Microsoft AI models, Claude hosting, coding agents and webhooks "
        "(facts as of 2026-11-03; text, tools and decisions: part 1)", w=W)
    y = bottom + 36
    y = summary_tiles(cv, y)
    y = section_pictures(cv, y + 56)
    y = section_voice(cv, y + 56)
    y = section_mai(cv, y + 56)
    y = section_claude(cv, y + 56)
    y = section_devtools(cv, y + 56)
    section_sources(cv, y + 56)


# ---------------------------------------------------------------------------------------------- summary
def summary_tiles(cv, y):
    tiles = [
        ("3", "Realtime transports", "WebRTC for browsers and mobile, WebSocket for servers, SIP for phone calls", "lime", 60),
        ("256K", "tokens of context in gpt-realtime-2.1", "GA since 2026-07-07: speech to speech with built-in reasoning", "lime", 40),
        ("24 kHz", "mono PCM16 audio", "Headerless, base64: Realtime and GPT-Live", "lime", 40),
        ("2", "ways to host Claude", "On Azure (v2, all GA) or on Anthropic infrastructure (v1)", "orange", 60),
        ("1M", "tokens of Claude context", "On the newest Claude models, 128K output; the 4.5 generation: 200K and 64K", "orange", 40),
        ("5", "MAI model families", "Thinking, Image, Voice, Transcribe and Code: mostly preview", "violet", 60),
    ]
    hs = [tile_h(*t[:3], C, t[4]) for t in tiles]
    H = max(hs)
    for i, (num, label, sub, th, ns) in enumerate(tiles):
        tile(cv, colx(i), y, C, H, num, label, sub, th, ns)
    y += H + 22
    cx = 0.0
    cv.text(cx, y + 2, "Also in this series:", size=16, color=MUTED_)
    cx += text_size("Also in this series:", 16)[0] + 16
    for label, th in (("Foundry Models catalog", "blue"), ("Deployment types and offers", "blue"), ("PTU and quota", "yellow"),
                      ("Model router: one deployment, many models", "blue"), ("Fine-tuning: from data to a deployed model", "blue"),
                      ("Part 1: Model APIs and capabilities: the surface map", "blue")):
        c = Chip(label, theme=th, size=15, fill="soft").place(cv, cx, y - 2)
        cx += c.w + 14
    return y + 38


# ---------------------------------------------------------------------------------------------- 1 pictures
def section_pictures(cv, y):
    y = banner(cv, y, 1, "Pictures, video and vectors", "Image models are called through image generation, the Responses image tool or the Images playground; video is an async job")
    img = std("lime", "OpenAI image generation", [
        "gpt-image-2.5-sunburst (GA): the most capable, best editing precision",
        "gpt-image-2.5-flare (GA): the fastest high-quality option",
        "gpt-image-2 (GA): high resolution up to 4K, broad aspect ratios; base64 output only",
        "gpt-image-1.5, gpt-image-1 and gpt-image-1-mini: limited-access preview, apply for access",
        "Text and image in, image out; 4,000-character prompt",
        "Default quotas: gpt-image-1 9 RPM, gpt-image-1-mini 12, gpt-image-1.5 9, gpt-image-2 9",
        "! dall-e-3 was retired on 2026-03-04",
    ], w=span(2), icon="image", src=[S_IMG])
    mai = std("violet", "MAI-Image and FLUX", [
        "MAI-Image-2.5, -2.5-Pro, -2.5-Flash, -2.6 and -2.6-Flash: Global Standard, preview",
        "Versions: 2026-06-02 (2.5, 2.5-Flash), 2026-06-19 (2.5-Pro), 2026-07-31 (2.6, 2.6-Flash)",
        "Text to image and image edits (up to 5 input images, JPEG or PNG) through the generations and edits APIs",
        "Minimum 768 x 768; at most 1,048,576 pixels (2.5 family) or 2,359,296 (2.6 family)",
        "FLUX.2-pro and -flex, FLUX.1-Kontext-pro and FLUX-1.1-pro: through the BFL API or images/generations and images/edits",
    ], w=span(2), badge="preview", icon="mai", src=[S_MAIIMG])
    vid = std("lime", "Sora 2 video", [
        "Text to video, image to video, video to video, audio in the output, and remix for targeted edits",
        "v1 API; an async job: create, poll, then download from a URL",
        "Per-second billing; the docs say IP and photorealistic content is blocked; default 2 job requests a minute",
        "The Video playground keeps videos for 24 hours",
        "! The schedule lists Sora-2 versions retiring 2026-07-15 and 2026-10-15, both already past: check the Models API for today's availability",
    ], w=span(2), badge="preview", icon="video-indexer", src=[S_VIDEO, S_SCHED])
    _, b1 = row(cv, 0, y, [img, mai, vid], gap=G)
    y2 = b1 + G
    vis = std("lime", "Vision input", [
        "Vision-enabled chats accept images on GPT-5.x and 4.x, o-series (not o3-mini), Llama-4, Mistral-Large-3, Kimi and Grok 4.x",
        "At most 50 images per request (gpt-4o, gpt-4.1)",
        "The router routes on text only (part 1)",
    ], icon="vision", src=[S_VISION])
    emb = Table([("Embedding model", 250), ("Dimensions", 200), "Notes"], [
        [("text-embedding-3-large", "teal"), "3,072", "dimensions parameter shrinks the vector (v3 models)"],
        [("text-embedding-3-small", "teal"), "1,536", "dimensions parameter shrinks the vector (v3 models)"],
        [("text-embedding-ada-002", "teal"), "1,536", "Older model"],
        [("embed-v-4-0 (Cohere)", "teal"), "256, 512, 1,024 or 1,536", "Text and images"],
        [("Cohere-embed-v3-*", "teal"), "-", "Deprecated from 2026-11-15; retires 2027-02-15 (replacement Cohere-embed-v5-fast or -pro)"],
        [("MedImageInsight", "teal"), "-", "Medical imaging embeddings"],
    ], w=span(3), theme="teal", size=14, head_size=15, title="Embedding models", title_size=20)
    emb_rules = std("teal", "Embeddings API rules", [
        "v1 route; Entra ID needs the Cognitive Services OpenAI User role",
        "At most 2,048 inputs and 300,000 tokens per call",
        "! You cannot upgrade between embedding models in place: switching means re-embedding your data",
        "OpenAI embedding models run on an extended retirement timeline (2028-02-09 on the schedule)",
    ], w=span(2), icon="search", src=[S_EMB])
    vis.place(cv, colx(0), y2, h=max(vis.h, emb.h, emb_rules.h))
    emb.place(cv, colx(1), y2)
    emb_rules.place(cv, colx(4), y2, h=max(vis.h, emb.h, emb_rules.h))
    return max(vis.bottom, emb.bottom, emb_rules.bottom)


# ---------------------------------------------------------------------------------------------- 2 voice
def realtime_panel(cv, x, y, w, mh=0):
    with cv.panel(x, y, title="Realtime API (GA): speech to speech, three ways in", sub="wss://<resource>.openai.azure.com/openai/v1/realtime?model=<deployment>   (no api-version)",
                  theme="lime", style="dotted", pad=22, title_size=24, sub_size=16, w=w, min_h=mh) as p:
        iw = w - 44
        steps = [("gpt-realtime", "2025-08-28"), ("gpt-realtime-mini", "2025-10-06 and 2025-12-15"), ("gpt-realtime-1.5", "see the Models page"), ("gpt-realtime-2", "2026-05-07"),
                 ("gpt-realtime-2.1 and -2.1-mini", "2026-07-07, GA: Global Standard + Data Zone Standard")]
        bw = (iw - 4 * 44) / 5
        bxs = []
        for i, (t, s) in enumerate(steps):
            last = i == 4
            b = Box(bw, t, sub=s, theme="lime", size=17, sub_size=13, fill="solid" if last else "hatch", h=112, sw=3 if last else 2)
            b.place(cv, p.ix + i * (bw + 44), p.iy + 4)
            bxs.append(b)
        for a, b in zip(bxs, bxs[1:]):
            connect(cv, a, b, sw=2)
        ty = bxs[0].bottom + 40
        lane_h, lane_gap = 118, 22
        cw_, hub_w = 520, 470
        hub_x = p.ix + iw - hub_w - 360
        lanes = [
            ("Browser or mobile app", "WebRTC: preferred for client apps - lower latency, codecs, jitter and loss handling, peer to peer", "lime", "WebRTC"),
            ("Your server", "WebSocket: server to server; audio is headerless mono PCM16 at 24 kHz, base64", "lime", "WebSocket"),
            ("Phone callers via a SIP trunk", "Twilio, Vonage or Bandwidth route inbound VoIP calls to sip:proj_<internalId>@...", "lime", "SIP"),
        ]
        cl = []
        for i, (t, s, th, lab) in enumerate(lanes):
            b = Box(cw_, t, sub=s, theme="gray", size=18, sub_size=14, fill="hatch", h=lane_h)
            b.place(cv, p.ix, ty + i * (lane_h + lane_gap))
            cl.append(b)
        hub = Box(hub_w, "Realtime API", sub="gpt-realtime-2.1: built-in reasoning (minimal to high), response phases commentary and final_answer, 256,000-token context",
                  theme="lime", icon="openai", icon_pos="top", icon_size=40, size=24, sub_size=15, fill="solid", sw=3,
                  h=3 * lane_h + 2 * lane_gap)
        hub.place(cv, hub_x, ty)
        for (t, s, th, lab), b in zip(lanes, cl):
            arrow(cv, [(b.right + 6, b.cy), (hub.x - 8, b.cy)], color=INK, sw=3, start_head="arrow", end_head="arrow", label=lab, label_size=17, label_pos="above")
        wb = Box(310, "Your webhook", sub="realtime.call.incoming starts a SIP session", theme="gray", size=18, sub_size=14, fill="hatch", h=lane_h, dash="dashed")
        wb.place(cv, hub.right + 50, cl[2].y)
        arrow(cv, [(hub.right + 6, cl[2].cy), (wb.x - 6, cl[2].cy)], dash="dashed", color=INK, sw=2)
        nt = Note(310, "SIP needs a webhook for incoming calls, the project id proj_<internalId>, global deployments in East US 2 or Sweden Central, and the "
                  "Cognitive Services User or Contributor role.", kind="info", size=14, src=[S_RTSIP])
        nt.place(cv, hub.right + 50, ty)
        end = ty + 3 * lane_h + 2 * lane_gap
        n2 = Note(iw, "Realtime 2.x has no truncation setting in session.update: use conversation.item.truncate and conversation.item.delete instead. "
                  "Billing is input, cached input and output tokens (image input separately); audio-token and concurrent-session quotas are separate. "
                  "Voices: alloy, ash, ballad, coral, cedar, echo, marin, sage, shimmer, verse.", kind="warn", title="Realtime 2.x details", size=15, src=[S_RT2, S_RTWEBRTC])
        n2.place(cv, p.ix, end + 30)
    return p


def gptlive_panel(cv, x, y, w, mh=0):
    with cv.panel(x, y, title="GPT-Live: full duplex voice, with the work delegated", sub="gpt-live-1: listens and speaks at the same time; voice-only output; speech translation (quality varies by language pair)",
                  theme="lime", style="dotted", pad=22, title_size=24, sub_size=16, w=w, min_h=mh) as p:
        seq = Sequence(cv, p.ix + 20, p.iy + 6, [("Browser", "gray", "app"), ("Your backend", "gray", "api"), ("GPT-Live", "lime", "openai"), ("Responses deployment", "blue", "openai")],
                       spacing=430, head_w=260, head_h=60, step=62, label_size=15)
        seq.msg(0, 1, "SDP offer (GPT-Live has no ephemeral client keys)", num=1)
        seq.msg(1, 2, "POST /openai/v1/live/sessions: offer + session config (API key or Entra)", num=2)
        seq.msg(2, 1, "SDP answer", dash="dashed", num=3)
        seq.msg(1, 0, "SDP answer", dash="dashed", num=4)
        seq.msg(0, 2, "audio on the media track,              events on the oai-events data channel", num=5)
        seq.msg(2, 3, "Responses delegation: { type: responses, responses: { model, instructions, tools } }", num=6)
        seq.msg(3, 2, "hosted tools run server side (normal Responses charges); function calls go back to your app", dash="dashed", num=7)
        seq.note(0, 3, "Interrupting the speech does not cancel backend work. Your app owns permissions, confirmations and state.", kind="gotcha")
        seq.end()
    return p


# right-hand cards for the voice section
def section_voice(cv, y):
    y = banner(cv, y, 2, "Audio, Realtime and GPT-Live: speak to models, and let them speak back",
               "Chained speech-to-text and text-to-speech, turn-based Realtime, or full-duplex GPT-Live - pick the architecture first")
    # ---- row A: audio model table (full width)
    at = Table([("Capability", 260), ("Models", 900), "API and notes"], [
        ["Audio in and out", "gpt-audio, gpt-audio-mini, gpt-audio-1.5", "Through Chat Completions; 128K tokens in, 16,384 out"],
        ["Speech to text", "whisper, gpt-transcribe, gpt-4o-transcribe, gpt-4o-mini-transcribe, gpt-4o-transcribe-diarize", "/audio/transcriptions; gpt-transcribe suits offline files (25 MB, language hints)"],
        ["Translation", "whisper", "Audio translation"],
        ["Text to speech", "tts, tts-hd, gpt-4o-mini-tts", "gpt-4o-mini-tts is style-steerable"],
        ["Azure Speech in Foundry Tools", "Speech to text, text to speech, avatar, Voice Live, video translation", "Separate Speech service docs"],
    ], w=W, theme="lime", size=15, head_size=15, title="Audio and speech through the APIs", title_size=20)
    at.place(cv, 0, y)
    yb = at.bottom + 40
    # ---- row B: realtime panel + a column of cards
    f1 = std("lime", "gpt-realtime-2.1 in one card", [
        "Speech to speech with built-in reasoning: reasoning.effort minimal, low, medium or high",
        "Response phases: commentary (a preamble) and final_answer",
        "256,000-token context and stricter instruction following",
        "Audio: headerless mono PCM16, 24 kHz, base64",
        "Billing: input, cached input and output tokens (image input separately)",
    ], w=span(2), badge="ga", icon="speech", src=[S_RT2])
    f2 = std("lime", "Migrating from preview", [
        "A preview-to-GA migration guide exists for Realtime",
        "Concurrent-session quotas are separate from token quotas",
        "WebRTC and WebSocket guides: see the Realtime audio how-tos",
    ], w=span(2), icon="learn", src=[S_RTWEBRTC])
    tr = std("lime", "GPT Realtime Translate", [
        "gpt-realtime-translate (2026-05-06): continuous, non-chunked live translation to translated speech and a transcript",
        "Realtime API; Global Standard; billed hourly",
        "Pair with Transcribe for source-language captions",
    ], w=span(2), icon="translator", src=[S_TRANSLATE])
    ts = std("lime", "GPT Realtime Transcribe", [
        "gpt-realtime-whisper (2026-05-06); gpt-live-transcribe (2026-07-29) is the current recommendation",
        "Persistent streaming session, low latency; offline files use gpt-transcribe",
        "Hourly billing; ISO-639-1 language hint",
    ], w=span(2), icon="speech", src=[S_WHISPER])
    colh = f1.h + f2.h + tr.h + ts.h + 3 * 24
    rp = realtime_panel(cv, 0, yb, span(4), mh=colh)
    col(cv, colx(4), yb, [f1, f2, tr, ts], gap=24)
    yc = max(rp.bottom, yb + colh) + 40
    # ---- row C: GPT-Live
    ws = Table([("WebSocket (GPT-Live)", 330), "Details"], [
        ["Address", "wss://<resource>.openai.azure.com/openai/v1/live/sessions"],
        ["Handshake", "First event session.start, then wait for session.started"],
        ["Audio in", "session.input_audio.append: 24 kHz PCM16 mono, base64; also 16 kHz PCM and G.711 u-law or A-law"],
        ["Audio out", "session.output_audio.delta"],
        ["Transcripts", "session.input_transcript.delta and session.output_transcript.delta"],
        ["Updates", "session.update and session.instructions.append; model, instructions and voice are immutable; default voice marin"],
    ], w=span(2), theme="lime", size=14, head_size=15, title="GPT-Live over WebSocket", title_size=20)
    dl = std("lime", "Two kinds of delegation", [
        "Client delegation (default): your app does the backend work",
        "Responses delegation: routed to a Responses deployment; hosted tools run server side, function calls come back to your app",
        "Automatic context summarisation near the window limit",
    ], w=span(2), icon="agent", src=[S_LIVEDELEG])
    n = Note(span(2), "The GPT-Live page says it supports three transports but lists two: WebSocket and WebRTC. gpt-live-1 is named on the GPT-Live pages but was not in the "
             "sold-by-Azure model tables read.", kind="warn", title="Docs disagree", size=14, src=[S_LIVE])
    gp = gptlive_panel(cv, 0, yc, span(4))
    ws.place(cv, colx(4), yc)
    dl.place(cv, colx(4), ws.bottom + 24)
    n.place(cv, colx(4), dl.bottom + 24)
    yd = max(gp.bottom, n.bottom) + 40
    # ---- row D: choosing the architecture
    ch = Table([("Architecture", 300), ("Shape", 620), ("Pick it when", 780), "Mind"], [
        [("GPT-Live", "lime"), "Full duplex voice API with a separate backend (delegation)", "Natural interruptions and a voice front end for real work behind it",
         "Concurrent-session quota by tier (default 10 up to Tier 5: 500); no ephemeral keys"],
        [("Realtime API", "lime"), "Single turn-based speech-to-speech model", "One model that listens, reasons and speaks, with WebRTC, WebSocket or SIP",
         "Separate audio-token and concurrent-session quotas; no truncation in session.update for 2.x"],
        [("Chained STT, agent, TTS", "lime"), "Speech to text, then an agent, then text to speech", "You need a specific agent, voice or recogniser at each hop",
         "More hops, more latency"],
    ], w=W, theme="lime", size=15, head_size=15, title="Which voice architecture?", title_size=20)
    ch.place(cv, 0, yd)
    return ch.bottom


# ---------------------------------------------------------------------------------------------- 3 MAI
def section_mai(cv, y):
    y = banner(cv, y, 3, "Microsoft AI (MAI) models: one glance", "Microsoft's own models and the Foundry Models catalog entries around them; most are preview", "violet")
    t = Table([("Model", 330), ("Type", 520), ("Status and version", 330), "Where and API"], [
        [("MAI-Thinking-1", "violet"), "Reasoning chat; 256K context, up to 64K output; tool calling; encrypted chain of thought", "Preview; 2026-06-01",
         "Global Standard only (no PTU); chat completions, OpenAI-compatible; Foundry Models, sold by Azure"],
        [("MAI-Image-2.5, -2.5-Flash, -2.5-Pro, -2.6, -2.6-Flash", "violet"), "Text to image and image edit", "Preview; 2026-06-02, 06-02, 06-19, 07-31, 07-31",
         "Global Standard; generations and edits APIs"],
        [("MAI-Voice-2.1, MAI-Voice-2.1-Flash", "violet"), "Text to speech, 23 languages; SSML styles; gated instant voice cloning from a consented 5-60 second clip", "Preview",
         "Azure Speech in Foundry Tools (SSML, Voice Live)"],
        [("MAI-Transcribe-2, -1.5; MAI-Transcribe-2-Streaming", "violet"), "Speech to text, 60 languages; diarization, word timestamps, language ID, keyword biasing, code switching",
         "-2 and streaming: preview; -1 deprecated 2026-08-20", "Speech REST (enhanced mode), Realtime API (WebSocket) or Azure Speech SDK"],
        [("Microsoft-Decision-1", "violet"), "Typed decisions (noul, choice, score); text or JSON up to 32K tokens", "Version 1", "/providers/microsoft/v1/systemone; Global and Data Zone Standard"],
        [("MAI-Code-1.1-Flash", "violet"), "Coding; reinforcement fine-tuning capable", "Preview", "Serverless Global Standard (see the fine-tuning canvas)"],
        [("model-router", "blue"), "Routes each request to the best-fit model", "GA 2025-11-18", "Global and Data Zone Standard (see the model router canvas)"],
    ], w=span(4), theme="violet", size=14, head_size=15, title="MAI at a glance", title_size=20)
    t.place(cv, 0, y)
    c1 = std("violet", "MAI speech details", [
        "MAI-Voice: long-form fidelity for audiobooks and podcasts (2.1); ultra-low latency for voice agents and IVR (2.1-Flash); SSML mstts:express-as styles such as joy, excitement and empathy",
        "MAI-Transcribe-2: REST with enhancedMode.enabled=true and enhancedMode.model MAI-Transcribe-2; WAV, MP3 or FLAC; needs a Speech (Foundry) resource",
        "MAI-Transcribe-2-Streaming (preview): incremental and final transcripts; served from swedencentral, centralus, eastus2 and southeastasia",
    ], w=span(2), badge="preview", icon="speech", src=[S_MAIVOICE, S_MAITRANS, S_MAISTREAM])
    c1.place(cv, colx(4), y)
    n = Note(span(2), "The schedule row for MAI-Image-2.5 carries 2026-10-01 (passed) yet it still reads Preview, and MAI-Transcribe-1 shows both a deprecation date and a retirement "
             "date. Trust the Models API for the current status.", kind="warn", title="Docs disagree", size=14, src=[S_SCHED])
    n.place(cv, colx(4), c1.bottom + 24)
    return max(t.bottom, n.bottom)


# ---------------------------------------------------------------------------------------------- 4 Claude
def section_claude(cv, y):
    y = banner(cv, y, 4, "Claude on Foundry: two hosting versions, one Marketplace offer", "Anthropic is the seller of record and data processor; Microsoft Support is the support path for both", "orange")
    t = Table([("Topic", 260), ("Hosted on Azure (v2, all GA)", 640), "Hosted on Anthropic infrastructure (v1)"], [
        ["Seller, data processor, SLA operator", "Anthropic", "Anthropic"],
        ["Support path", "Microsoft Support", "Microsoft Support"],
        ["Purchase and billing", "Azure Marketplace offer Claude Platform on Foundry; CCU meter; MACC-eligible", "Same"],
        ["Data residency", "At rest in the selected Azure geography; processing scoped to the Global or Data Zone deployment", "May be processed outside Azure and your region"],
        ["Deployment types", "Global Standard and Data Zone Standard (US)", "Global Standard only"],
        ["Models", "Opus 5.5 Fast, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5.5, Sonnet 5, Haiku 5.5, Haiku 4.5", "Adds Opus 4.7, 4.6 and 4.5, Sonnet 4.6 and 4.5, and the Fable and Mythos previews"],
        ["APIs", "Messages and token counting", "Adds /files, /skills and more"],
        ["Other", "No web fetch and no Files API; web search web_search_20250305; images as base64 or URL only", "Web fetch and the Files API are available"],
        ["Compliance", "Anthropic Trust Center", "Anthropic Trust Center"],
    ], w=span(4), theme="orange", size=14, head_size=15, title="Azure-hosted vs Anthropic-hosted (as of 2026-11-03)", title_size=20, first_col_theme="orange")
    t.place(cv, 0, y)
    with cv.panel(colx(4), y, title="Claude on Foundry in four steps", theme="orange", style="dotted", pad=20, title_size=22, w=span(2)) as pf:
        flow_steps(cv, pf.ix, pf.iy, span(2) - 40, [
            ("Subscribe", "Claude Platform on Foundry in the Azure Marketplace; needs Contributor or Owner plus Marketplace access"),
            ("Deploy", "Azure-hosted by default; Global Standard or Data Zone Standard"),
            ("Call the Messages API", "POST https://<resource>.services.ai.azure.com/anthropic/v1/messages, header anthropic-version: 2023-06-01"),
            ("Pay in CCU", "Hourly metering, monthly in arrears, MACC-decrementing"),
        ], "orange")
    y2 = max(t.bottom, pf.bottom) + 40
    with cv.panel(0, y2, title="Model catalogue: context and maximum output", sub="Thinking: adaptive only on 4.7 and later; effort low, medium, high, xhigh or max per model", theme="orange",
                  style="dotted", pad=22, title_size=24, sub_size=16, w=span(4)) as pm:
        iw = span(4) - 44
        groups = [
            ("1M context, 128K output", "orange", ["claude-opus-5-5", "claude-opus-5-5-fast (Azure only)", "claude-opus-5", "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6",
                                                   "claude-sonnet-5-5", "claude-sonnet-5", "claude-sonnet-4-6", "claude-haiku-5-5"], False),
            ("200K context, 64K output (4.5 generation)", "red", ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5"], True),
            ("Previews", "violet", ["claude-fable-5", "claude-fable-5-1"], False),
            ("Gated research (Entra ID only, defensive cyber focus)", "gray", ["claude-mythos-5", "claude-mythos-5-1", "claude-mythos-preview"], False),
        ]
        cy = pm.iy + 4
        for name, th, items, retiring in groups:
            cv.text(pm.ix, cy, name, size=17, color=get_theme(th).deep)
            cy += 26
            chips = [Chip(i, theme="red" if retiring else th, size=15, pad_x=10, pad_y=5, dash="dashed" if retiring else "solid", fill="soft" if retiring else "solid") for i in items]
            fl = ChipFlow(chips, iw, gap=8)
            fl.place(cv, pm.ix, cy)
            cy += fl.h + 14
        cv.text(pm.ix, cy, "Red dashed: on the retirement list (claude-haiku-4-5 2026-11-15, claude-opus-4-5 2026-11-24, claude-sonnet-4-5 2026-11-30), as of 2026-11-03. "
                "Fable previews: classifiers may return 200 with stop_reason refusal; refused input is not billed.", size=14, color=MUTED_)
        cy += 24
        rules = Note(iw, "top_p must be 0.99 on newer models; top_k, temperature and manual thinking {type: enabled} are rejected on most 5.x and 4.7+ models.", kind="gotcha",
                     title="Parameter rules on newer models", size=15, src=[S_CLAUDE])
        rules.place(cv, pm.ix, cy + 6)
    cap = std("orange", "What the Messages API supports", [
        "Streaming, thinking (adaptive, effort), citations, vision, PDF, 1M context, token counting",
        "Structured outputs (output_config.format, strict: true)",
        "Tools: client-side bash, text editor, computer use and memory; web search; web fetch (Anthropic-hosted only); MCP connector; tool search (BM25 or regex, *_20251119); fine-grained tool streaming (beta header)",
        "Prompt caching: automatic, 5-minute or 1-hour breakpoints; context editing (beta header context-management-2025-06-27)",
        "Beta: per-turn effort, mid-conversation system messages, token budgets (task_budget)",
        "Agents: Microsoft Agent Framework or the Claude Agent SDK",
    ], w=span(2), icon="claude", src=[S_CLAUDEUSE])
    cap.place(cv, colx(4), y2)
    y3 = max(pm.bottom, cap.bottom) + 40
    b1 = std("orange", "Billing: Claude Consumption Units", [
        "Tokens are converted through Anthropic's per-model rates (plus private-offer discounts) at a fixed CCU price",
        "Hourly metering, monthly in arrears; no prepaid credits; decrements MACC",
        "Cost Management shows cost by model and usage type (input, output, cache); tags are at the resource level, not per project",
        "Plan capacity in TPM and RPM, not CCU",
    ], w=span(2), icon="cost-management", src=[S_CLAUDEBILL])
    b2 = std("orange", "Data privacy and safety", [
        "Claude models are third-party Marketplace offerings; Anthropic is an independent data processor",
        "Azure-hosted: request ingress, API and GPU inference run on Azure; Anthropic reviews only by exception through Trust and Safety safeguards",
        "Anthropic-hosted: Anthropic's DPA and Commercial Terms; Microsoft still shares billing, usage and contact data under Marketplace terms",
        "EU watermarking standard compliance: interwoven text watermark and C2PA",
        "! Foundry offers no built-in content filtering for Claude; content safety is Anthropic's",
    ], w=span(2), icon="content-safety", src=[S_CLAUDEPRIV])
    b3 = std("orange", "Quota", [
        "Subscription-level limits in RPM, ITPM and OTPM",
        "Pay-as-you-go: 40 RPM, 40K ITPM and 8K OTPM for most models; Enterprise and MCA-E: 10,000 RPM, 10M ITPM, 2M OTPM",
        "Detail: the PTU and quota canvas",
    ], w=span(2), icon="quotas", src=[S_CLAUDEQ])
    _, bb = row(cv, 0, y3, [b1, b2, b3], gap=G)
    return bb


# ---------------------------------------------------------------------------------------------- 5 dev tools
def section_devtools(cv, y, mh=0):
    y = banner(cv, y, 5, "Developer tools and push events", "Coding agents run against your Foundry deployments; webhooks tell you when long jobs finish", "gray")
    top = y
    codex = std("gray", "Codex CLI on Azure", [
        "OpenAI Codex CLI (npm install -g @openai/codex, or brew install --cask codex) against the v1 Responses API through ~/.codex/config.toml",
        "Deploy a reasoning model: gpt-6-astra, gpt-6-sol, gpt-5.3-codex, gpt-5.2-codex, gpt-5.1-codex-max, -codex or -codex-mini, gpt-5-codex, gpt-5, -mini or -nano",
        "Validated: Codex CLI 0.152.1 and 0.153.0 with gpt-6-astra (multi-agent, prompt caching); 0.155.1 with gpt-6-sol and gpt-6-luna",
        "Triggers: terminal, VS Code, GitHub Actions; macOS 12+, Ubuntu 20.04+ or Debian 10+, Windows 11 via WSL2; Contributor in Foundry",
    ], w=span(2), icon="github", src=[S_CODEX])
    cc = std("orange", "Claude Code on Foundry", [
        "CLI and VS Code extension running on Foundry; deploy roles in the page: primary claude-sonnet-4-6, fast claude-haiku-4-5, extended thinking claude-opus-4-6",
        "Or use the model router with a subset that includes Claude models (deploy them first)",
        "Install natively (curl or irm script, or Homebrew); npm is deprecated. Auth: Entra ID or API key; project context file; GitHub Actions for CI",
        "Needs Contributor or Owner plus Marketplace access",
        "! The page examples use older Claude models than the catalogue lists",
    ], w=span(2), icon="claude", src=[S_CCODE])
    cd = std("orange", "Claude Desktop through Foundry", [
        "Claude Desktop (Cowork and Claude Code) uses Foundry as its inference provider",
        "Help, Troubleshooting, Enable Developer Mode, then Developer, Configure third-party inference; use the API key of the Foundry deployment",
        "Conversations stay on the device; billing is on Azure",
        "Fleet rollout with Intune, Group Policy or Jamf",
    ], w=span(2), icon="claude", src=[S_CDESK])
    _, tb_ = row(cv, 0, top, [codex, cc, cd], gap=G)
    wy = tb_ + 40
    with cv.panel(0, wy, title="Webhooks: signed push events for long-running work", sub="Event types shown in the examples: response.completed, response.failed, realtime.call.incoming",
                  theme="gray", style="dotted", pad=22, title_size=24, sub_size=16, w=W) as pw:
        iw = W - 44
        sw = (iw - 4 * 54) / 5
        steps = [
            ("Host a listener", "The page uses Flask on App Service"),
            ("Register it", "REST only: POST https://<resource>.openai.azure.com/openai/v1/dashboard/webhook_endpoints with name, url and event_types"),
            ("Store the secret", "The signing secret is shown once: put it in Key Vault; it cannot be updated later"),
            ("Verify each event", "Webhook-ID, Webhook-Timestamp and Webhook-Signature headers; client.webhooks.unwrap(body, headers); invalid means reply 400"),
            ("Reply 200 fast", "Offload heavy work and deduplicate on Webhook-ID"),
        ]
        bx = []
        for i, (t, s) in enumerate(steps):
            b = Box(sw, t, sub=s, theme="gray", size=18, sub_size=14, fill="hatch")
            bx.append(b)
        hh = max(b.h for b in bx)
        for i, b in enumerate(bx):
            b.place(cv, pw.ix + i * (sw + 54), pw.iy + 6, h=hh)
            numbered(cv, b.x + 18, b.y + 2, i + 1, theme="gray", d=30, size=17)
        for a, b in zip(bx, bx[1:]):
            connect(cv, a, b, sw=2)
        cv.text(pw.ix, bx[0].bottom + 12, "Trigger a response.completed event with a Responses call that uses background=True. List is a GET, update a POST to /<webhook_id>, delete is supported; "
                "the page shows no portal path.", size=14, color=MUTED_)
        cv.text(pw.ix, bx[0].bottom + 36, "Learn: Webhooks", size=12, color=LINK, link=S_HOOKS[1])
    return pw.bottom


# ---------------------------------------------------------------------------------------------- sources
def section_sources(cv, y):
    y = banner(cv, y, 6, "Gotchas and sources", None, "gray")
    nw = (W - 3 * G) / 4
    notes = [
        Note(nw, "Claude is not sold by Azure: Anthropic is the seller of record and data processor, billing is in CCU, Foundry has no built-in content filter for it, and Anthropic-hosted "
             "data may leave Azure.", kind="gotcha", title="Claude is a Marketplace offer", size=15, src=[S_CLAUDEHOST]),
        Note(nw, "Realtime 2.x has no truncation in session.update. GPT-Live has no ephemeral keys: your backend must broker WebRTC. MAI-Thinking-1 is Global Standard only, with no PTU.",
             kind="gotcha", title="Voice and MAI limits", size=15, src=[S_RT2, S_LIVE]),
        Note(nw, "dall-e-3 is retired (2026-03-04); gpt-image-1, -1.5 and -mini are limited-access; the MAI, Sora, Fable and Mythos models are preview or gated. Re-check before you publish a deck.",
             kind="preview", title="Preview and limited access", size=15, src=[S_IMG]),
        Note(nw, "Both Entra token scopes appear in examples (https://ai.azure.com/.default and https://cognitiveservices.azure.com/.default), and some Claude Code page examples "
             "use older model names. Use the scope and model on the page you follow.", kind="warn", title="Docs disagree", size=15, src=[S_CCODE]),
    ]
    _, nb = row(cv, 0, y, notes, gap=G)
    y = nb + 40
    sources(cv, 0, y, [
        ("Image generation models", learn("openai/how-to/dall-e")),
        ("Video generation with Sora", learn("openai/concepts/video-generation")),
        ("Embeddings", learn("openai/how-to/embeddings")),
        ("MAI-Image models", learn("foundry-models/how-to/use-foundry-models-mai-image")),
        ("MAI voices (Azure Speech in Foundry Tools)", learn("azure/ai-services/speech-service/mai-voices", base="")),
        ("Realtime API (GPT Realtime 2)", learn("openai/concepts/realtime-2")),
        ("GPT-Live", learn("openai/concepts/gpt-live")),
        ("GPT-Live delegation", learn("openai/how-to/gpt-live-delegation")),
        ("Claude models in Foundry", learn("foundry-models/concepts/claude-models")),
        ("Claude hosting comparison", learn("foundry-models/concepts/claude-models-hosting-comparison")),
        ("Claude billing (CCU)", learn("foundry-models/concepts/claude-models-billing")),
        ("Configure Claude Code", learn("foundry-models/how-to/configure-claude-code")),
        ("Codex CLI on Azure", learn("openai/how-to/codex")),
        ("Webhooks", learn("openai/how-to/webhooks")),
    ], w=W, cols=3)
