"""Foundry Models catalog - sold by Azure vs partners and community: contract, provider shelves, endpoints, discovery tools and BYO routes."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd.palette import STATUS

META = dict(
    id="model-catalog", title="Foundry Models catalog", section="2", group="Models", order=20,
    description="The Foundry Models catalog as a two-wing mall: sold by Azure vs partners and community - who sells, supports and bills (Claude is the special case), provider shelves with real model names, endpoints, discovery and compare tools, Hugging Face and Fireworks routes.",
    tags=["catalog", "sold-by-azure", "partners", "marketplace", "huggingface", "fireworks"],
)

# ---------------------------------------------------------------------------- grid
W = 3200
WING, SPINE, GAP = 1400, 280, 60
SX = WING + GAP                  # spine x
RX = SX + SPINE + GAP            # right wing x
CX = SX + SPINE / 2              # canvas centre line
AZ, PT = "blue", "orange"        # sold by Azure / partners and community
C5, G5 = 592, 40                 # five-column grid for the lower cards
SEC = 64                         # vertical gap between sections
INK2 = "#343a40"


def c5(i: int) -> float:
    return i * (C5 + G5)


def span5(n: int) -> float:
    return n * C5 + (n - 1) * G5


# ---------------------------------------------------------------------------- modality + chips
MOD = {
    "chat": ("Chat and reasoning", "#1971c2", "GPT, Claude, DeepSeek, Grok, Llama, Phi, Kimi"),
    "emb": ("Embeddings", "#099268", "text-embedding-3, embed-v-4-0"),
    "img": ("Image generation and editing", "#c2255c", "gpt-image, FLUX, MAI-Image"),
    "vid": ("Video generation", "#9c36b5", "sora-2"),
    "aud": ("Audio, speech and realtime", "#2f9e44", "GPT-Live, realtime-2.x, whisper, tts"),
    "rank": ("Rerank", "#66a80f", "Cohere-rerank-v4.0"),
    "doc": ("Document AI and OCR", "#f08c00", "Cohere-parse, mistral-ocr, document-ai"),
    "dec": ("Decision scoring", "#6741d9", "Microsoft-Decision-1"),
    "med": ("Healthcare imaging", "#e03131", "MedImageInsight, CXRReportGen"),
}
# tag -> (label, label colour, border dash, border colour override)
TAG = {
    "preview": ("preview", "#e8590c", "dashed", None),
    "gated": ("gated preview", "#e8590c", "dashed", None),
    "new": ("new", "#6741d9", "solid", None),
    "retiring": ("retiring", "#e03131", "solid", "#e03131"),
    "reg": ("registration", "#495057", "solid", None),
}
CHIP_H, CHIP_GAP = 30, 7


def chip_w(name: str, tag, size=15) -> float:
    w = 10 + 11 + 6 + metrics.line_width(name, size) + 10
    if tag:
        w += 6 + metrics.line_width(TAG[tag][0], 12)
    return w


def draw_chip(cv, x, y, name, mod, tag, th, size=15) -> float:
    w = chip_w(name, tag, size)
    lr = metrics.line_ratio()
    label, tcol, dash, stroke = TAG[tag] if tag else (None, None, "solid", None)
    col = MOD[mod][1]
    with cv.group():
        cv.rect(x, y, w, CHIP_H, stroke=stroke or th.stroke, fill="#ffffff", style="solid", sw=1.5, dash=dash)
        cv.ellipse(x + 10, y + CHIP_H / 2 - 5.5, 11, 11, stroke=col, fill=col, style="solid", sw=1, rough=0)
        nx = x + 27
        cv.text(nx, y + (CHIP_H - size * lr) / 2, name, size=size, color=INK)
        if tag:
            cv.text(nx + metrics.line_width(name, size) + 6, y + (CHIP_H - 12 * lr) / 2 + 1, label, size=12, color=tcol)
    return w


class Lane(Rect2):
    """One provider shelf: label block on the left, model chips (grouped) on the right."""

    def __init__(self, w, name, theme_name, groups, *, sub=None, label_w=214, size=15):
        self.th = theme(theme_name)
        self.w, self.name, self.size, self.label_w = w, name, size, label_w
        lr = metrics.line_ratio()
        inner = (label_w - 30) * 0.965
        self.name_lines = metrics.wrap_text(name, inner, 21)
        self.sub_lines = metrics.wrap_text(sub, inner, 14) if sub else []
        label_h = len(self.name_lines) * 21 * lr + ((6 + len(self.sub_lines) * 14 * lr) if sub else 0)
        self.cx0 = label_w + 18
        cw = (w - self.cx0 - 18) * 0.99
        y = 14.0
        self.items: list[tuple] = []
        for gi, (head, chips, note) in enumerate(groups):
            if gi:
                y += 10
            if head:
                self.items.append(("head", self.cx0, y, head))
                y += 14 * lr + 4
            x, rowy = 0.0, y
            for nm, mod, tag in chips:
                cwid = chip_w(nm, tag, size)
                if x and x + cwid > cw:
                    x, rowy = 0.0, rowy + CHIP_H + CHIP_GAP
                self.items.append(("chip", self.cx0 + x, rowy, (nm, mod, tag)))
                x += cwid + CHIP_GAP
            y = rowy + CHIP_H
            if note:
                nl = metrics.wrap_text(note, cw * 0.985, 14)
                self.items.append(("note", self.cx0, y + 5, "\n".join(nl)))
                y += 5 + len(nl) * 14 * lr
        self.h = max(label_h + 32, y + 14)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill="#ffffff", style="solid", sw=2)
            cv.rect(x + 8, y + 8, self.label_w - 8, H - 16, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            t = cv.text(x + 24, y + 18, "\n".join(self.name_lines), size=21, color=th.deep)
            if self.sub_lines:
                cv.text(x + 24, t.bottom + 6, "\n".join(self.sub_lines), size=14, color=INK2)
        for kind, ix, iy, payload in self.items:
            if kind == "head":
                cv.text(x + ix, y + iy, payload, size=14, color=th.deep)
            elif kind == "note":
                cv.text(x + ix, y + iy, payload, size=14, color=MUTED)
            else:
                draw_chip(cv, x + ix, y + iy, *payload, th, self.size)
        cv.register(f"lane:{self.name}", x, y, self.w, H)
        return self


class Steps(Rect2):
    """Card-like block with numbered steps joined by a dotted line."""

    def __init__(self, w, title, steps, *, theme_name="blue", badge=None, icon=None, src=(), size=15, pad=16,
                 fill="hatch", subtitle=None):
        self.th = theme(theme_name)
        self.theme_name = theme_name
        self.w, self.title, self.badge, self.icon, self.src, self.size, self.pad, self.fill = (
            w, title, badge, icon, list(src), size, pad, fill)
        lr = metrics.line_ratio()
        inner = w - 2 * pad
        self.icon_off = 46 if icon else 0
        self.badge_w = (metrics.line_width(STATUS[badge][1], 13) + 18) if badge else 0
        t_w = (inner - self.icon_off - (self.badge_w + 8 if badge else 0)) * 0.965
        self.t_lines = metrics.wrap_text(title, t_w, 20)
        self.sub_lines = metrics.wrap_text(subtitle, t_w, 14) if subtitle else []
        head_h = len(self.t_lines) * 20 * lr + (2 + len(self.sub_lines) * 14 * lr if subtitle else 0)
        head_h = max(head_h, 36 if icon else 0)
        y = pad + head_h + 12
        tw = (inner - 40) * 0.965
        self.rows: list[tuple] = []
        for s in steps:
            lines = metrics.wrap_text(s, tw, size)
            h = max(len(lines) * size * lr + 2, 26)
            self.rows.append((y, lines, h))
            y += h + 14
        y -= 14
        self.src_lines: list[tuple] = []
        if self.src:
            y += 10
            for label, url in self.src:
                lines = metrics.wrap_text(f"Learn: {label}", inner, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * 12 * lr + 2
            y -= 2
        self.h = y + pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th, pad = self.th, self.pad
        bg, fs = (th.fill, "hachure") if self.fill == "hatch" else (th.soft, "solid")
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=bg, style=fs, sw=2)
            if self.icon:
                place_icon(cv, self.icon, x + pad, y + pad, 36)
            t = cv.text(x + pad + self.icon_off, y + pad, "\n".join(self.t_lines), size=20, color=th.deep)
            if self.sub_lines:
                cv.text(x + pad + self.icon_off, t.bottom + 2, "\n".join(self.sub_lines), size=14, color=MUTED)
            if self.badge:
                draw_badge(cv, x + self.w - pad - self.badge_w, y + pad - 1, self.badge)
            centers = []
            for i, (ry, lines, rh) in enumerate(self.rows):
                cy = y + ry + 13
                centers.append(cy)
                cv.text(x + pad + 36, y + ry + 1, "\n".join(lines), size=self.size, color=INK)
            for i in range(len(centers) - 1):
                cv.line((x + pad + 14, centers[i] + 15), (x + pad + 14, centers[i + 1] - 15), stroke=th.stroke, sw=2,
                        dash="dotted")
            for i, cy in enumerate(centers):
                numbered(cv, x + pad + 14, cy, i + 1, theme=self.theme_name, d=28, size=16)
            for txt, url, sy in self.src_lines:
                cv.text(x + pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


def modality_key(cv, x, y, w):
    """Legend panel for the dot colours and chip styles (sits on the spine)."""
    with cv.panel(x, y, title="Dot colour = modality", theme="gray", style="dotted", w=w, pad=18, title_size=21) as p:
        yy = p.iy
        for _, (label, col, ex) in MOD.items():
            cv.ellipse(p.ix, yy + 4, 13, 13, stroke=col, fill=col, style="solid", sw=1, rough=0)
            t = cv.text(p.ix + 24, yy, label, size=15, color=INK)
            e = cv.text(p.ix + 24, t.bottom, ex, size=13, color=MUTED, wrap=w - 76)
            yy = e.bottom + 9
        yy += 4
        cv.line((p.ix, yy), (p.ix + w - 36, yy), stroke="#adb5bd", sw=1, dash="dashed")
        yy += 12
        t = cv.text(p.ix, yy, "Chip style", size=18, color=INK2)
        yy = t.bottom + 6
        for label, tag in (("GA or default", None), ("Preview (dashed)", "preview"), ("New", "new"),
                           ("Retiring by 2026-11-30", "retiring"), ("Registration needed", "reg")):
            stroke = TAG[tag][3] if tag and TAG[tag][3] else "#495057"
            dash = TAG[tag][2] if tag else "solid"
            cv.rect(p.ix, yy + 2, 34, 18, stroke=stroke, fill="#ffffff", style="solid", sw=1.5, dash=dash)
            if tag in ("new", "preview", "reg"):
                cv.text(p.ix + 4, yy + 3, {"new": "new", "preview": "pre", "reg": "reg"}[tag], size=12, color=TAG[tag][1])
            tt = cv.text(p.ix + 46, yy, label, size=15, color=INK)
            yy = tt.bottom + 8
        cv.text(p.ix, yy + 2, "Retiring dates: see the retirement schedule (as of 2026-11-03).", size=13, color=MUTED,
                wrap=w - 36)
    return p


class ClaudePanel(Rect2):
    """The Claude special case, drawn under the Anthropic shelf inside the partners wing."""

    def __init__(self, w, card_w=520):
        self.w, self.pad, self.card_w = w, 14, card_w
        self.card = Card(card_w, "Claude: the special case", [
            "# Same for both hosting options",
            "NOT sold by Azure: a Non-Microsoft Product under the Product Terms",
            "Anthropic is seller of record, operator and independent data processor; it provides any SLA",
            "Support path is Microsoft Support (deployment, billing, Marketplace, API connectivity)",
            "Buy through the Claude Platform on Foundry offer in Azure Marketplace",
            "Billed in Claude Consumption Units (CCU) on your Azure invoice: MACC-eligible, hourly metering, invoiced monthly in arrears, no prepaid credits",
            "! No built-in Foundry content filtering at deployment time",
        ], theme=PT, icon="claude", fill="hatch", body_size=15,
            src=[("Claude hosting comparison", learn("foundry-models/concepts/claude-models-hosting-comparison")),
                 ("Claude models", learn("foundry-models/concepts/claude-models"))])
        tw = w - 2 * self.pad - card_w - 18
        self.table = Table(
            [("", 112), "Hosted on Azure (v2)", "Hosted on Anthropic infrastructure (v1)"],
            [
                ["Models", "Opus 5.5 Fast, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5, Sonnet 5.5, Haiku 5.5, Haiku 4.5 (all GA)",
                 "Opus 5.5, Opus 5, Opus 4.8, Sonnet 5, Sonnet 5.5, Haiku 5.5, Haiku 4.5, preview Fable and Mythos, older Opus, Sonnet and Haiku"],
                ["Data", "At rest in the selected Azure geography; processing scoped to Global or Data Zone",
                 "May be processed outside Azure, including outside the selected Azure region"],
                ["Types", "Global Standard and Data Zone Standard (US)", "Global Standard only"],
                ["APIs", "Messages and token counting", "Messages, token counting, plus /files and /skills"],
                ["Pick it when", "You need data residency in an Azure geography or Data Zone Standard (US); it is the default when a model exists in both",
                 "You need API features that are not yet in the Azure-hosted version"],
            ], w=tw, theme=PT, size=14, head_size=15, first_col_theme=PT, title="What differs between the two hosting versions", title_size=19)
        self.h = max(self.card.h, self.table.h) + 2 * self.pad
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        cv.rect(x, y, self.w, H, stroke=theme(PT).stroke, fill="#ffffff", style="solid", sw=2, dash="dashed")
        self.card.place(cv, x + self.pad, y + self.pad, h=H - 2 * self.pad)
        self.table.place(cv, x + self.pad + self.card_w + 18, y + self.pad)
        return self


# ---------------------------------------------------------------------------- data: ladder
OVERVIEW = ("Foundry Models overview", learn("concepts/foundry-models-overview"))
PRIVACY = ("Data privacy for models sold by Azure", learn("responsible-ai/openai/data-privacy"))
PARTNERS = ("Models from partners and community", learn("foundry-models/concepts/models-from-partners"))
CLAUDE_HOST = ("Claude hosting comparison", learn("foundry-models/concepts/claude-models-hosting-comparison"))

# label, (azure title, body, src), (partner title, body, src)
RUNGS = [
    ("Who runs it",
     ("Microsoft hosts and operates", ['= "Hosted by Azure and operated by Azure": the models run on Azure infrastructure under Microsoft operations.'], []),
     ("Provider-defined", ["= Many run as serverless APIs on Azure infrastructure but are provider-operated. Hugging Face models run on managed compute."], [])),
    ("Terms",
     ("Microsoft Product Terms", ["= Billed as First Party Consumption Services (Azure meters) but NOT subject to Azure service terms - the model licence terms apply."], [OVERVIEW]),
     ("Non-Microsoft Products", ["= Under the Product Terms: the model provider's licence plus Azure Marketplace terms."], [PARTNERS])),
    ("Billing",
     ("Azure meters", ["= Metered on your Azure subscription."], []),
     ("Azure Marketplace SaaS offer", ["= Microsoft Commercial Marketplace Terms of Use. Managed compute: hourly per accelerator.",
                                       "! Claude bills in Claude Consumption Units (CCU), MACC-eligible."], [])),
    ("Support and SLA",
     ("Microsoft support, enterprise-grade SLAs", ["= Direct Microsoft support and maintenance."], []),
     ("Provider support, varying SLA", ["= Hugging Face: HF forum or HF support.",
                                        "! Claude: the support path is Microsoft Support, but Anthropic is the seller, operator and SLA provider."], [CLAUDE_HOST])),
    ("Responsible AI review",
     ("Microsoft internal review", ["= High-level outcomes appear in each model card. Reviews do not guarantee mitigations - run your own evaluations."], []),
     ("Typically provider-validated", ["= Integration guidelines come from Azure. Hugging Face models are Non-Microsoft Products that are not tested or evaluated by Microsoft."], [])),
    ("Data and privacy",
     ("Not shared, not used for training", ["= Prompts, completions, embeddings and training data are NOT available to other customers, OpenAI or other providers, and NOT used to train models. Models are stateless; fine-tuned models are exclusive to you."], [PRIVACY]),
     ("Provider may be a data processor", ["= For some models the provider acts as an independent data processor (Claude: Anthropic)."], [])),
    ("Eligibility and extras",
     ("Fungible provisioned throughput", ["= Some models let you use quota and reservations flexibly across them."], []),
     ("Offer availability region", ["= Pay-as-you-go needs a billing account in a country or region where the provider offers the model."], [])),
]

# ---------------------------------------------------------------------------- data: shelves
def chips(mod, *names, tag=None):
    """Helper: same modality + tag for several names."""
    return [(n, mod, tag) for n in names]


AZ_LANES = [
    dict(name="OpenAI", sub="all Azure OpenAI models", groups=[
        ("Reasoning and chat", chips("chat", "gpt-6.1-sol", "gpt-6.1-terra", tag="new")
         + chips("chat", "gpt-6-astra", "gpt-6-luna", "gpt-6-sol", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
         + chips("chat", "gpt-chat-latest", tag="preview")
         + chips("chat", "gpt-5.5", "gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.3-codex", "gpt-5.2",
                 "gpt-5.2-codex", "gpt-5.1", "gpt-5.1-codex", "gpt-5.1-codex-mini", "gpt-5.1-codex-max", "gpt-5",
                 "gpt-5-mini", "gpt-5-nano", "gpt-5-pro", "gpt-5-codex"),
         "Context: GPT-6.1, 6, 5.6, 5.5 and 5.4 = 1,050,000 (922,000 in / 128,000 out). GPT-5.x mini and nano, 5.2, 5.1 and 5 = 400,000 (272,000 in / 128,000 out)."),
        ("GPT-4 era and o-series", chips("chat", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini", "GPT-4 Turbo", "o1-mini")
         + chips("chat", "o3", "o4-mini", "o3-pro", "o3-mini", "o1", "codex-mini", tag="retiring")
         + chips("chat", "computer-use-preview", tag="reg"),
         "GPT-4.1 = 1,047,576 context (300,000 on standard; 128,000 on provisioned and batch). computer-use-preview needs a limited-access registration."),
        ("Open-weight", chips("chat", "gpt-oss-120b", "gpt-oss-20b", tag="preview"), None),
        ("Embeddings", chips("emb", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"),
         "3-large: 3,072 dims; 3-small and ada-002: 1,536. Max request 8,192 tokens (ada v1: 2,046), up to 2,048 inputs per call. No in-place upgrade between embedding models: re-embed."),
        ("Image and video", chips("img", "gpt-image-1", "gpt-image-1-mini", "gpt-image-1.5", "gpt-image-2", "gpt-image-2.5-flare",
                                  "gpt-image-2.5-sunburst") + chips("vid", "sora-2", tag="preview"),
         "Image prompts up to 4,000 characters."),
        ("Audio, speech and realtime", chips("aud", "gpt-audio", "gpt-audio-mini", "gpt-audio-1.5", "gpt-realtime", "gpt-realtime-mini",
                                             "gpt-realtime-1.5", "gpt-realtime-2", "gpt-realtime-2.1", "gpt-realtime-2.1-mini",
                                             "gpt-realtime-translate", "gpt-realtime-whisper", "gpt-live-transcribe", "whisper",
                                             "gpt-transcribe", "gpt-4o-mini-tts")
         + chips("aud", "gpt-4o-transcribe", "gpt-4o-mini-transcribe", "gpt-4o-transcribe-diarize", "tts", "tts-hd", tag="preview"),
         "gpt-realtime-translate, gpt-realtime-whisper and gpt-live-transcribe bill by duration. gpt-transcribe is offline file transcription (25 MB)."),
    ]),
    dict(name="Microsoft", sub="MAI, router, Decision-1. Phi sits under partners.", groups=[
        (None, chips("chat", "model-router") + chips("dec", "Microsoft-Decision-1") + chips("chat", "MAI-Thinking-1", tag="preview")
         + chips("img", "MAI-Image-2.6", "MAI-Image-2.6-Flash", "MAI-Image-2.5", "MAI-Image-2.5-Pro", "MAI-Image-2.5-Flash", tag="preview"),
         "model-router version 2025-11-18. Decision-1: text-only, 32K tokens, calibrated probability per answer option. MAI-Thinking-1: 256K context, encrypted chain-of-thought. MAI-Image: text plus up to 5 images in, 1 PNG out. MAI-Voice and MAI-Transcribe come through Azure Speech in Foundry Tools. Healthcare AI models are also Microsoft's."),
    ]),
    dict(name="DeepSeek", sub="reasoning chat with tool calling", groups=[
        (None, chips("chat", "DeepSeek-V4-Pro", "DeepSeek-V4-Flash", "DeepSeek-V3.2", "DeepSeek-V3.2-Speciale")
         + chips("chat", "DeepSeek-V4-Flash-0731", tag="preview"), "V4: 1,000,000 in / 384,000 out. V3.2: 128K."),
    ]),
    dict(name="Meta", sub="Maverick here, Scout under partners", groups=[
        (None, chips("chat", "Llama-4-Maverick-17B-128E-Instruct-FP8", tag="retiring") + chips("chat", "Llama-3.3-70B-Instruct"),
         "Maverick: text and image in, 1M context."),
    ]),
    dict(name="Mistral AI", sub="Large-3 and OCR here; Codestral, Ministral under partners", groups=[
        (None, chips("chat", "Mistral-Large-3", "mistral-medium-3-5", tag="preview") + chips("doc", "mistral-document-ai-2512")
         + chips("doc", "mistral-ocr-4-0", tag="preview"), "Document AI and OCR: image or PDF in, text out (30 pages, 30 MB)."),
    ]),
    dict(name="Moonshot AI", sub="Kimi multimodal reasoning", groups=[
        (None, chips("chat", "Kimi-K2.7-Code", "Kimi-K2.6", "Kimi-K2.5", tag="preview"), "Text and image in, 262,144 context."),
    ]),
    dict(name="SpaceXAI", sub="xAI Grok models", groups=[
        (None, chips("chat", "grok-4.7", "grok-4.1-fast-reasoning", "grok-4.1-fast-non-reasoning")
         + chips("chat", "grok-4.6", "grok-4.3", "grok-4-20-reasoning", "grok-4-20-non-reasoning", tag="preview")
         + chips("chat", "grok-4", "grok-code-fast-1", tag="reg"),
         "grok-4.7: GA, Chat Completions and Responses, 500,000 context. GA Grok models from 4.7 on stay available for at least six months."),
    ]),
    dict(name="Cohere", sub="Command A, rerank, parse, embed 4", groups=[
        (None, chips("chat", "Cohere-command-a") + chips("chat", "Cohere-command-a-plus-05-2026", tag="preview")
         + chips("rank", "Cohere-rerank-v4.0-pro", "Cohere-rerank-v4.0-fast") + chips("doc", "Cohere-parse-v5", tag="preview")
         + chips("emb", "embed-v-4-0"), "embed-v-4-0: text and images in; 256, 512, 1024 or 1536 dims. Cohere-parse-v5: image to Markdown. Older embed-v3 models sit under partners."),
    ]),
    dict(name="Black Forest Labs", sub="FLUX image generation", groups=[
        (None, chips("img", "FLUX.2-pro", "FLUX.2-flex", "FLUX.1-Kontext-pro", "FLUX-1.1-pro"),
         "Global Standard in all regions. FLUX.2 multi-reference images (up to 8 on pro, 10 on flex) work through the API, not the playground."),
    ]),
]

PT_LANES = [
    dict(name="Anthropic Claude", sub="Messages API, billed in CCU", groups=[
        ("Generally available", chips("chat", "claude-opus-5-5", "claude-opus-5-5-fast", "claude-opus-5", "claude-opus-4-8", "claude-sonnet-5-5",
                                      "claude-sonnet-5", "claude-haiku-5-5") + chips("chat", "claude-haiku-4-5", tag="retiring"), None),
        ("Preview and gated research preview", chips("chat", "claude-fable-5-1", "claude-fable-5", tag="preview")
         + chips("chat", "claude-mythos-5-1", "claude-mythos-5", "claude-mythos-preview", tag="gated"),
         "Hosted on Azure (v2, all GA) or hosted on Anthropic infrastructure (v1); not every model exists in both. Not sold by Azure."),
    ]),
    dict(name="Cohere", sub="older embeddings; newer models are sold by Azure", groups=[
        (None, chips("emb", "Cohere-embed-v3-english", "Cohere-embed-v3-multilingual", tag="retiring"),
         "Deprecated 2026-11-15, retire 2027-02-15 (replacement Cohere-embed-v5-fast or -pro), as of 2026-11-03."),
    ]),
    dict(name="Meta", sub="Scout here, Maverick sold by Azure", groups=[
        (None, chips("chat", "Llama-4-Scout-17B-16E-Instruct"), None),
    ]),
    dict(name="Mistral AI", sub="2025 models; hub-based project for the mistralai-* family", groups=[
        (None, chips("chat", "Codestral-2501", "Ministral-3B", "Mistral-small-2503", "Mistral-medium-2505"), None),
        ("Hub-based project only (Foundry classic)", chips("chat", "mistralai-Mistral-7B-Instruct-*", "mistralai-Mixtral-8x7B-Instruct-*",
                                                          "mistralai-Mixtral-8x22B-Instruct-*"), None),
    ]),
    dict(name="NTT Data", sub="Japanese and English", groups=[
        (None, chips("chat", "tsuzumi-7b"), "Needs a hub-based project (Foundry classic)."),
    ]),
    dict(name="Microsoft Phi", sub="listed under partners in the docs", groups=[
        (None, chips("chat", "Phi-4", "Phi-4-mini-instruct", "Phi-4-multimodal-instruct", "Phi-4-reasoning", "Phi-4-mini-reasoning"),
         "Offer availability region: not applicable. Phi-4-multimodal takes text, image and audio. Phi-4 family retires 2027-01-17 (replacement microsoft--phi-4 on Foundry Managed Compute), as of 2026-11-03."),
    ]),
    dict(name="Hugging Face hub", sub="managed compute (preview)", groups=[
        (None, chips("chat", "Qwen", "NVIDIA Nemotron", "selected Meta models", "selected Mistral models", tag=None),
         "Hundreds of models for real-time inference on managed compute; Hugging Face creates and maintains them."),
    ]),
    dict(name="NVIDIA", sub="catalog provider", groups=[
        (None, chips("chat", "NIM containers on managed compute", "FW-Nemotron-* on Fireworks"), None),
    ]),
    dict(name="Fireworks on Foundry", sub="FW- prefix, opt-in, GA", groups=[
        ("Pay-per-token examples", chips("chat", "FW-DeepSeek-V4.1-Flash", "FW-GLM-5.3", "FW-GLM-5.3-Flash", "FW-Kimi-K3", "FW-MiniMax-M3",
                                         "FW-Nemotron-3-Ultra-NVFP4", "FW-Nemotron-Lightning-3.5-30B-A3B"), None),
        ("Also on the PTU list (examples)", chips("chat", "Qwen3.5", "Qwen3.6", "Qwen3.8", "Gemma-4", "Llama-v3.1-8B", "GPT-OSS-20B",
                                                  "GPT-OSS-120B", "Ministral-3-3B", "Inkling (Thinking Machines Lab)")
         + chips("doc", "PaddleOCR-VL"), None),
    ]),
    dict(name="Healthcare AI", sub="limited preview, research use only", groups=[
        (None, chips("med", "MedImageInsight Premium", "CXRReportGen Premium", tag="preview") + chips("med", "Tempus", "Providence"),
         "Premium models: closed-weight, serverless pay-as-you-go, fine-tunable, NOT for clinical use. Tempus and Providence: digital pathology and biomedical research."),
    ]),
]


# ---------------------------------------------------------------------------- the canvas
def build(cv: Canvas) -> None:
    _, bottom = title_block(cv, 0, 0, "Foundry Models catalog",
                            "Two categories, one catalog: who sells it, who supports it, how you pay - and how to find, compare, deploy and import models (as of 2026-11-03)",
                            icon="foundry", w=W)

    # ============================================================ taxonomy: root -> two wings
    y = bottom + 46
    root = Box(560, "Foundry Models catalog", h=104, theme="gray", sub="10,000+ models, about 50 new each month", icon="foundry",
               icon_pos="left", icon_size=48, size=26, sub_size=16)
    root.place(cv, CX - 280, y)
    nl = Note(1250, "Pick models sold by Azure when you need deep Azure integration, guaranteed support and enterprise SLAs.",
              kind="key", theme=AZ, title="Sold by Azure: integration and guarantees",
              src=[("Foundry Models overview", learn("concepts/foundry-models-overview"))])
    nr = Note(1250, "Pick partners and community models for specialised and innovation-led scenarios - they make up the vast majority of the catalog.",
              kind="key", theme=PT, title="Partners and community: specialisation and speed")
    nl.place(cv, 0, y + (root.h - nl.h) / 2)
    nr.place(cv, W - 1250, y + (root.h - nr.h) / 2)

    by = y + root.h + 76
    left_b = Box(WING, "SOLD BY AZURE", h=116, theme=AZ, sub="Microsoft hosts, bills and supports - Azure meters, Microsoft support, enterprise-grade SLAs",
                 size=38, sub_size=18, icon="foundry", icon_pos="left", icon_size=62)
    right_b = Box(WING, "PARTNERS AND COMMUNITY", h=116, theme=PT, sub="Provider-operated Non-Microsoft Products - Azure Marketplace billing, provider support",
                  size=38, sub_size=18, icon="marketplace", icon_pos="left", icon_size=62)
    left_b.place(cv, 0, by)
    right_b.place(cv, RX, by)
    connect(cv, root, left_b, a_side="bottom", b_side="top", route="elbow", sw=3, color=theme(AZ).stroke)
    connect(cv, root, right_b, a_side="bottom", b_side="top", route="elbow", sw=3, color=theme(PT).stroke)

    # ============================================================ the contract ladder
    ly = by + left_b.h + 30
    for label, (azt, azb, azs), (ptt, ptb, pts) in RUNGS:
        cL = Card(WING, azt, azb, theme=AZ, fill="soft", pad=14, title_size=21, body_size=17, gap=4, src=azs)
        cR = Card(WING, ptt, ptb, theme=PT, fill="soft", pad=14, title_size=21, body_size=17, gap=4, src=pts)
        h = max(cL.h, cR.h)
        lab = Box(SPINE, label, h=h, theme="gray", size=20)
        cL.place(cv, 0, ly, h=h)
        lab.place(cv, SX, ly)
        cR.place(cv, RX, ly, h=h)
        line_between(cv, cL, lab, a_side="right", b_side="left", color=theme(AZ).stroke, sw=3)
        line_between(cv, lab, cR, a_side="right", b_side="left", color=theme(PT).stroke, sw=3)
        ly += h + 10

    # ---- surprise stickers
    sy = ly + 26
    sw_ = (W - 3 * 40) / 4
    stickers = [
        Note(sw_, "It sits under partners and community: a Non-Microsoft Product billed in CCU through Azure Marketplace. Support still goes through Microsoft Support.",
             kind="gotcha", title="Claude is NOT sold by Azure"),
        Note(sw_, "In the docs the Phi-4 family appears in the Microsoft section of the partners page, while MAI, model-router and Decision-1 are in the sold-by-Azure Microsoft table.",
             kind="warn", title="Phi is listed under partners"),
        Note(sw_, "DeepSeek, Meta, Mistral, Moonshot, SpaceXAI, Cohere and Black Forest Labs are billed with Azure meters and supported by Microsoft. A provider can appear in both wings.",
             kind="info", theme=AZ, title="Sold by Azure is not Microsoft-only"),
        Note(sw_, "First-party consumption (Azure meter), but not sold by Azure: no EU Data Boundary, no FedRAMP, PCI or SOC 1 Type 2, and Microsoft does not evaluate model safety.",
             kind="gotcha", title="Fireworks: no EU Data Boundary"),
    ]
    hmax = max(s.h for s in stickers)
    for i, s in enumerate(stickers):
        s.place(cv, i * (sw_ + 40), sy, h=hmax)

    # ============================================================ provider shelves
    hy = sy + hmax + SEC
    section_header(cv, 0, hy, "Provider shelves: concrete models named in the docs",
                   sub="Selections as of 2026-11-03 - dot colour = modality, dashed = preview, red = retiring soon", w=W)
    top = hy + 92
    lanes_l = [Lane(WING - 32, d["name"], AZ, d["groups"], sub=d["sub"]) for d in AZ_LANES]
    items_r = []
    for i, d in enumerate(PT_LANES):
        items_r.append(Lane(WING - 32, d["name"], PT, d["groups"], sub=d["sub"]))
        if i == 0:
            items_r.append(ClaudePanel(WING - 32))
    head, base_gap = 64, 14

    def stack_h(items, gap):
        return head + sum(it.h for it in items) + gap * (len(items) - 1) + 30

    H = max(stack_h(lanes_l, base_gap), stack_h(items_r, base_gap))
    for x0, items, th_name, title, link in (
            (0, lanes_l, AZ, "Sold by Azure: 9 provider shelves", ("Learn: Models sold by Azure", learn("foundry-models/concepts/models-sold-directly-by-azure"))),
            (RX, items_r, PT, "Partners and community: 10 provider shelves", ("Learn: Models from partners and community", learn("foundry-models/concepts/models-from-partners")))):
        th = theme(th_name)
        cv.rect(x0, top, WING, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2)
        cv.text(x0 + 22, top + 14, title, size=28, color=th.deep)
        cv.text(x0 + WING - 22 - metrics.line_width(link[0], 13), top + 24, link[0], size=13, color=LINK, link=link[1])
        gap = base_gap + (H - stack_h(items, base_gap)) / max(len(items) - 1, 1)
        yy = top + head
        for it in items:
            it.place(cv, x0 + 16, yy)
            yy += it.h + gap
    key = modality_key(cv, SX, top, SPINE)
    both = Card(SPINE, "Same provider, both wings", [
        "# Microsoft", "MAI, router, Decision-1 | Phi-4 family",
        "# Meta", "Llama-4-Maverick | Llama-4-Scout",
        "# Mistral AI", "Large-3, OCR | Codestral, Ministral",
        "# Cohere", "Command A, rerank, embed-4 | embed-v3",
    ], theme="gray", fill="soft", body_size=14, title_size=18, pad=14, gap=3)
    both.place(cv, SX, key.bottom + 24)
    req = Note(SPINE, "Search the catalog for a model that is not there (for example mymodel) and select Request a model.", kind="tip",
               title="Missing a model?", size=14, src=[("Foundry Models overview", learn("concepts/foundry-models-overview"))])
    req.place(cv, SX, both.bottom + 24)

    # ============================================================ endpoints
    ey = top + H + SEC
    section_header(cv, 0, ey, "One endpoint, one credential: how you call a catalog model",
                   sub="A deployment is a named alias for a model; the route you call depends on the API shape", w=W)
    ry = ey + 110
    routes = [
        ("OpenAI v1 route: Responses and Chat Completions",
         "https://<resource>.openai.azure.com/openai/v1/ (or https://<resource>.services.ai.azure.com/openai/v1/) - /responses and /chat/completions - pass the deployment name in model - implicit versioning, no api-version",
         "Sold-by-Azure models", ["OpenAI, DeepSeek, Meta, Mistral, Moonshot, SpaceXAI, Cohere", "Responses also works for DeepSeek, Llama and Grok when supported; otherwise HTTP 400 Model not supported - call Chat Completions"], AZ),
        ("Anthropic Messages route",
         "POST https://<resource>.services.ai.azure.com/anthropic/v1/messages (+ /v1/messages/count_tokens) - header anthropic-version: 2023-06-01 - use the Anthropic SDKs",
         "Claude", ["Partners and community", "Hosted on Azure or on Anthropic infrastructure; billed in CCU"], PT),
        ("Fireworks: passthrough or Foundry-supported route",
         "Direct passthrough: https://{resource}.services.ai.azure.com/providers/fireworks/v1/responses (Fireworks does session management) - or the Foundry-supported .../openai/v1/responses",
         "Fireworks FW-* models", ["Opt-in; Global or Data Zone (US) Standard or Provisioned"], PT),
        ("Black Forest Labs: provider API or Image API",
         "<resource>/providers/blackforestlabs/v1/flux-2-pro ... - or the Image API: /openai/deployments/{id}/images/generations | edits",
         "FLUX models", ["FLUX.2-pro, FLUX.2-flex, FLUX.1-Kontext-pro, FLUX-1.1-pro", "Global Standard in all regions"], AZ),
        ("Managed compute (preview)",
         "<endpoint>/managed-deployments/<deployment-name>/ - chat-completions runtimes are also on /openai/v1/",
         "Hugging Face, NIM, custom weights", ["Dedicated GPUs, hourly per accelerator", "No built-in content filtering"], PT),
        ("Decision-type APIs: typed answers",
         "Azure OpenAI Decisions API: POST /openai/v1/decisions (only gpt-6-luna) - Microsoft-Decision-1: <resource>/providers/microsoft/v1/systemone",
         "gpt-6-luna and Microsoft-Decision-1", ["Typed answers instead of text; Decision-1 returns a calibrated probability per answer option"], AZ),
    ]
    ROUTE_X, ROUTE_W, MODEL_X = 1130, 980, 2200
    MODEL_W = W - MODEL_X
    rows_ = []
    cy = ry
    for title, path, mtitle, mbody, th_name in routes:
        rc = Card(ROUTE_W, title, [], subtitle=path, theme=th_name, fill="soft", sub_size=14, title_size=19, pad=14)
        mc = Card(MODEL_W, mtitle, ["= " + t if i == 0 else t for i, t in enumerate(mbody)] if len(mbody) == 1 else mbody, theme=th_name,
                  fill="hatch", title_size=19, body_size=14, pad=14, gap=3)
        h = max(rc.h, mc.h)
        rc.place(cv, ROUTE_X, cy, h=h)
        mc.place(cv, MODEL_X, cy, h=h)
        arrow(cv, [(ROUTE_X + ROUTE_W + 4, cy + h / 2), (MODEL_X - 4, cy + h / 2)], color=theme(th_name).stroke, sw=3)
        rows_.append((cy, h))
        cy += h + 18
    rows_bottom = cy - 18
    RES_X, RES_W = 440, 560
    with cv.panel(RES_X, ry, title="Foundry resource", sub="one endpoint, one credential", theme=AZ, style="solid", fill="soft",
                  w=RES_W, min_h=rows_bottom - ry, pad=22, title_size=26, sub_size=16) as res:
        dep = Card(RES_W - 44, "Deployment = named alias", [
            "Gives a model a name plus configuration: model name, model version, capacity type, content-filter config, rate-limit config",
            "Capacity type, filter and rate limit depend on the model",
            "Only inference on deployments is billed",
            "Deployments are Azure resources: govern them with Azure Policy",
        ], theme=AZ, fill="hatch", icon="foundry", body_size=15, src=[("Endpoints for Foundry Models", learn("foundry-models/concepts/endpoints"))])
        dep.place(cv, res.ix, res.iy + 6)
        auth = Card(RES_W - 44, "Credential", [
            "Microsoft Entra ID (keyless, recommended) or API key",
            "Entra token scope: https://ai.azure.com/.default",
        ], theme="red", fill="hatch", icon="managed-identity", body_size=15)
        auth.place(cv, res.ix, dep.bottom + 18)
        cf = Card(RES_W - 44, "Content filtering", [
            "Default Azure AI Content Safety text moderation on serverless language models, billed separately",
            "Can be turned off per endpoint; not available for embedding and time-series models",
            "! Claude has no built-in filtering at deployment time",
        ], theme="pink", fill="hatch", icon="content-safety", body_size=15,
            src=[("Foundry Models overview", learn("concepts/foundry-models-overview"))])
        cf.place(cv, res.ix, auth.bottom + 18)
    app = Card(340, "Your app", ["OpenAI SDK, Anthropic SDK or plain REST", "model = your deployment name"], theme="gray", fill="hatch",
               icon="app", body_size=15)
    app.place(cv, 0, ry + 6)
    n_res = Note(340, "An Azure OpenAI resource only shows Azure OpenAI models in the catalog. Upgrade to a Foundry resource to deploy the full catalog.",
                 kind="info", title="Resource type matters", size=14, src=[("Deployment overview", learn("concepts/deployments-overview"))])
    n_res.place(cv, 0, app.bottom + 28)
    note_q = Note(340, "The Hugging Face page shows a different Entra token scope (https://cognitiveservices.azure.com/.default) from the ai.azure.com scope used on the other pages.",
                  kind="warn", title="Docs disagree", size=14)
    note_q.place(cv, 0, n_res.bottom + 20)
    arrow(cv, [(app.right + 6, app.cy), (RES_X - 6, app.cy)], sw=3, color=INK, label="token or key", label_size=14)
    arrow(cv, [(RES_X + RES_W + 4, ry + 24), (ROUTE_X - 4, ry + 24)], sw=3, color=theme(AZ).stroke)
    for (cy_, h_) in rows_[1:]:
        arrow(cv, [(RES_X + RES_W + 4, cy_ + h_ / 2), (ROUTE_X - 4, cy_ + h_ / 2)], sw=3, color=theme(AZ).stroke)

    # ============================================================ discovery ribbon
    ry2 = max(rows_bottom, res.bottom) + SEC
    section_header(cv, 0, ry2, "Find it, compare it, try it, deploy it, or bring your own",
                   sub="The catalog tools in the Foundry portal, left to right", w=W)
    cy2 = ry2 + 104
    RIB = (W - 4 * 60) / 5
    discover = Card(RIB, "Discover", [
        "Search plus 8 filters: Collections (provider), Region, Deployment options, Deployment SKU, Lifecycle, Industry, Supported features, Inference tasks",
        "Extra filter Available in my Project: only models deployable now, given GPU quota and region",
        "Model card tabs: Quick facts, Details, Deployments, Benchmarks, License",
        "Missing a model? Search for one that does not exist and select Request a model",
    ], theme="teal", icon="search", body_size=15, src=[("Foundry Models overview", learn("concepts/foundry-models-overview"))])
    compare = Card(RIB, "Compare", [
        "Model leaderboards: sort by Quality, Safety, Estimated cost or Throughput; trade-off chart; leaderboards by scenario",
        "Text LLM/SLM and embedding models only; sold-by-Azure models prioritised; not every model has data",
        "Compare 2-3 models (max 3): Performance benchmarks, Model details, Supported endpoints, Feature support",
        "Benchmark evaluations: Build > Evaluations > Create > Benchmarks dataset, optional judge model",
        "Datasets: AIME 2025 (30), BBEH (4,520), BIG-Bench Hard (934), ChemBench (2,785), FrontierScience (160), GPQA Diamond (198), MuSR (756), TruthfulQA (790)",
    ], theme="violet", icon="metrics", badge="preview", body_size=15,
        src=[("Model leaderboards", learn("concepts/model-benchmarks")), ("Benchmark evaluations", learn("observability/how-to/benchmark-evaluations"))])
    tryit = Card(RIB, "Try", [
        "Model playground: compare up to 3 models, system prompt, tools (web or file search, code interpreter), guardrails, code export, Open in VS Code",
        "Agents playground",
        "Video playground (preview): videos kept for 24 hours",
        "Images playground: inpainting and compare",
    ], theme="green", icon="browser", body_size=15, src=[("Playgrounds", learn("concepts/concept-playgrounds"))])
    deploy = Card(RIB, "Deploy", [
        "Serverless API: Foundry resource (no AI hub), tokens or PTUs; Global, Data Zone, Standard, Provisioned, Batch or Developer types",
        "Managed compute (preview): open, partner or custom weights on dedicated GPUs; hourly per accelerator; Global only",
        "Instant access (preview): call a supported model by name, no deployment; West US 3 only",
        "Azure OpenAI resources only show Azure OpenAI models: upgrade to a Foundry resource for the full catalog",
    ], theme=AZ, icon="foundry", body_size=15, src=[("Deployment overview", learn("concepts/deployments-overview"))])
    imp = Card(RIB, "Import your own", [
        "Hugging Face hub (preview): Foundry Managed Compute, weights stored on Azure",
        "Fireworks on Foundry: opt-in, GA; bring your own model with azd and deploy on PTUs",
        "Healthcare AI premium models: limited preview, research use only",
        "Azure Government has its own smaller catalog (see the cards below)",
    ], theme=PT, icon="hf", body_size=15)
    ribbon = [discover, compare, tryit, deploy, imp]
    r_right, r_bottom = row(cv, 0, cy2, ribbon, gap=60)
    for i in range(4):
        connect(cv, ribbon[i], ribbon[i + 1], a_side="right", b_side="right" if False else "left", sw=3, color=INK)
    for i, c in enumerate(ribbon):
        numbered(cv, c.x + 22, c.y + 2, i + 1, theme=["teal", "violet", "green", AZ, PT][i], d=34, size=19)

    # ============================================================ partner mechanics
    dy = r_bottom + SEC
    section_header(cv, 0, dy, "Partner mechanics: Marketplace, Hugging Face, Fireworks, healthcare and Government",
                   sub="What changes when the provider, not Microsoft, sells the model", w=W)
    y1 = dy + 104
    steps_partner = Steps(C5, "Subscribe to a partner model", [
        "Find it in Discover > Models and open the model card",
        "Subscribe to the provider's Azure Marketplace SaaS offer (one-time per subscription; needs the permissions at right)",
        "Deploy as a Serverless API, usually Global Standard (Data Zone Standard US where offered)",
        "Usage bills through Marketplace: per token, or CCU for Claude; managed compute bills hourly per accelerator",
        "Call the route with your deployment name and an Entra token",
    ], theme_name=PT, src=[("Models from partners and community", learn("foundry-models/concepts/models-from-partners"))])
    perms = Card(C5, "Permissions to subscribe", [
        "# On the Azure subscription",
        "Microsoft.MarketplaceOrdering/agreements/offers/plans/read",
        "Microsoft.MarketplaceOrdering/agreements/offers/plans/sign/action",
        "Microsoft.MarketplaceOrdering/offerTypes/publishers/offers/plans/agreements/read",
        "Microsoft.Marketplace/offerTypes/publishers/offers/plans/agreements/read",
        "Microsoft.SaaS/register/action (one-time registration)",
        "# On the resource group",
        "Microsoft.SaaS/resources/read and write",
        "= Owner and Contributor already include these.",
    ], theme="red", icon="managed-identity", body_size=14, src=[("Models from partners and community", learn("foundry-models/concepts/models-from-partners"))])
    cant = Note(C5, "Student, Visual Studio Enterprise and Free-credit subscriptions cannot buy Marketplace SaaS offers. CSP subscriptions cannot buy third-party model offers (use first-party consumption models). Claude also excludes Enterprise Accounts in South Korea, subscriptions without an active pay-as-you-go method and sponsored credit-only subscriptions.",
                kind="gotcha", title="Who cannot buy partner offers", size=14)
    note_ccu = Note(C5, "Marketplace partner meters appear under the resource group in Cost Management; CCU-billed Claude appears under the Foundry resource. Project-level cost attribution (preview) covers only sold-by-Azure models.",
                    kind="info", title="Where the bill shows up", size=14, src=[("Manage costs", learn("concepts/manage-costs"))])
    hf = Card(C5, "Hugging Face import", [
        "# Eligible models",
        "Tag Transformers, Diffusers or Sentence-Transformers",
        "Permissive commercial licence: Apache 2.0, MIT or OpenRAIL-M",
        "Supported task: chat-completion, image-to-text or embeddings",
        "Safetensors weights, no trust_remote_code",
        "# Checks",
        "Malware scan, code inspection, safe-format enforcement, API-conformance validation per model, runtime and accelerator",
        "! Gated Hugging Face models are not available in new Foundry: use Foundry (classic)",
    ], theme="yellow", icon="hf", badge="preview", body_size=15, src=[("Hugging Face models in Foundry", learn("foundry-models/how-to/hugging-face-models"))])
    hf_steps = Steps(C5, "Deploy a Hugging Face model", [
        "Discover > Models: Collections = Hugging Face, plus Available in my Project",
        "Deployment options = Managed compute, then Deploy",
        "Name it: 2-64 characters, letters, digits, _ and -, no dot",
        "Pick a deployment template and accelerator type",
        "Instance count: 1 to test, 2 or more for production",
        "Deploy; weights are stored on Azure (classic pulls from the Hub at deploy time)",
    ], theme_name="yellow", badge="preview", src=[("Hugging Face models in Foundry", learn("foundry-models/how-to/hugging-face-models"))])
    hf_note = Note(C5, "Cognitive Services Contributor (or Foundry Owner or Account Owner) deploys; Foundry User calls. GPU quota is separate from Azure VM quota: Manage > Quota > Managed compute > Request quota. SDK: sku.name GlobalManagedCompute, versionUpgradeOption OnceNewDefaultVersionAvailable, model azureml://registries/azure-huggingface/models/...",
                   kind="info", title="Roles, quota and SDK", size=14)
    # (placement happens in the masonry block below)

    # ---- Fireworks, healthcare
    fw_why = Card(C5, "Fireworks on Foundry", [
        "Newest open models, often before they are sold by Azure (FW- prefix)",
        "Bring your own model onto Fireworks GPUs and scale with PTU",
        "Custom deployment shape via your account team (customer-specific model version)",
        "! Opt-in: subscription Preview features > Fireworks.EnableDeploy (up to 30 min); Owner or Contributor enables, Foundry Owner deploys",
        "Not available in Azure Government",
        "The service itself is GA",
    ], theme="orange", badge="ga", body_size=15, src=[("Enable Fireworks models", learn("how-to/fireworks/enable-fireworks-models"))])
    fw_quota = Card(C5, "Fireworks: types, quota, notice", [
        "Global Standard and Data Zone Standard: pay-per-token; Global and Data Zone Provisioned: PTU",
        "Data Zone is US only: eastus, eastus2, centralus, northcentralus, southcentralus, westus, westus3",
        "Separate Global Standard and Data Zone Standard pools; enterprise default 10 million TPM per region per subscription per pool, shared by all Fireworks models",
        "Quota form: aka.ms/fireworks-quota",
        "Retirement notice: 15 days pay-per-token, 12 months PTU",
        "Cache hints: x-session-affinity, user, prompt_cache_key (takes priority)",
    ], theme="orange", body_size=15, src=[("Fireworks model catalog", learn("how-to/fireworks/fireworks-model-catalog"))])
    fw_comp = Card(C5, "Fireworks: compliance limits", [
        "First-party consumption service (Azure meter) under the Product Terms and DPA - but the open models are NOT sold by Azure",
        "! No SOC 1 Type 2, PCI, HITRUST or FedRAMP",
        "! Excluded from the EU Data Boundary",
        "Data leaves Microsoft facilities: Fireworks is a Microsoft subprocessor; no separate BAA",
        "ISO 42001 covers the AI management system, not model behaviour",
        "Microsoft does not evaluate the safety of these models",
    ], theme="red", icon="compliance", body_size=15, src=[("Privacy and compliance FAQ", learn("how-to/fireworks/privacy-compliance-faq"))])
    byom = Steps(C5, "Import a custom model into Fireworks", [
        "azd ext install azure.ai.models",
        "In the portal, select Generate upload command",
        "azd ai models create --base-model ... --source ... --weight-type FullWeight or LoRA",
        "The model shows as Registered",
        "Deploy with PTUs (ARM: sku.name GlobalProvisionedManaged, model.format FireworksCustom)",
    ], theme_name="orange", src=[("Import custom models", learn("how-to/fireworks/import-custom-models"))])
    byom_note = Note(C5, "Architectures: Kimi (K2, K2.5, K2.6), GLM (4.7, 4.8), gpt-oss-120b, Qwen3.5 (9B, 35B-A3B, 112B-A10B, 397B). Preview: LoRA adapters (merged into full weights; exceptions Ministral 3 3B, Qwen3.5 35B-A3B, Qwen3.5 4B) and draft models for speculative decoding. One active deployment per imported model per project; Fireworks Agents and Agent Builder are not supported.",
                     kind="preview", title="BYOM details", size=14)
    health = Card(C5, "Healthcare AI models", [
        "Premium models are closed-weight, serverless pay-as-you-go, limited preview, research use only",
        "MedImageInsight Premium: medical-imaging embeddings for classification, similarity and out-of-distribution or drift checks",
        "CXRReportGen Premium: structured draft chest X-ray findings, can use prior images",
        "Both are fine-tunable (Managed Training SFT, Global Standard only)",
        "Partner models: Tempus and Providence (digital pathology, biomedical research)",
        "! Not for clinical use. Managed-compute healthcare models live in Foundry (classic)",
    ], theme="red", badge="preview", body_size=15, src=[("Healthcare AI models", learn("how-to/healthcare-ai/healthcare-ai-models"))])
    # ---- Government + watch-outs
    gov = Card(C5, "Azure Government catalog", [
        "Lists GPT-5.6 sol, terra and luna, gpt-5.1, gpt-4.1, gpt-4.1-mini, o3-mini, gpt-4o and three embedding models",
        "Regions: usgovarizona, usgovvirginia",
        "Types: Data Zone Standard (USGov), Data Zone Provisioned, Standard, Provisioned managed",
        "GPT-4.1 1M context is not available in Government (128,000 standard and provisioned; 300,000 batch)",
        "Separate lifecycle and retirement pages exist",
    ], theme="gray", icon="compliance", body_size=15, src=[("Models sold by Azure (Government)", learn("foundry-models/concepts/models-sold-directly-by-azure-gov"))])
    g1 = Note(C5, "Preview models do not follow the standard Azure OpenAI model lifecycle, and Microsoft does not recommend them for production. They are upgraded to a later preview or GA, or retired.",
              kind="warn", title="Preview is not production", size=14)
    g2 = Note(C5, "Not available for embedding and time-series models. Claude has no built-in Foundry content filtering at deployment time; managed compute (preview) has none either.",
              kind="gotcha", title="Content filtering gaps", size=14)
    g3 = Note(C5, "Some partner models (for example mistralai-* and tsuzumi-7b) need a hub-based project: the catalog opens them in the Foundry (classic) portal.",
              kind="info", title="Hub-based projects", size=14)
    g4 = Note(C5, "Leaderboard pages disagree on the cost method (actual USD per benchmark run vs a 3:1 input-to-output estimate); performance metrics use 14 days x 24 trials at an 80:20 input-to-output token ratio. The models page lists the provider as SpaceXAI while one Tip still says xAI; the instant-access page says chat-gpt-latest while the models page says gpt-chat-latest.",
              kind="warn", title="Docs disagree", size=14)
    # masonry: one topic per column, stacks end at about the same height
    columns = [
        [steps_partner, cant, note_ccu, g1],
        [perms, gov, g3, g2],
        [hf, hf_steps, hf_note],
        [fw_why, fw_quota, fw_comp],
        [byom, byom_note, health, g4],
    ]
    bottoms = []
    for ci, items in enumerate(columns):
        yy = y1
        for it in items:
            it.place(cv, c5(ci), yy)
            yy = it.bottom + 20
        bottoms.append(yy - 20)
    y4 = max(bottoms) + SEC
    sources(cv, 0, y4, [
        ("Overview of Microsoft Foundry Models", learn("concepts/foundry-models-overview")),
        ("Foundry Models sold by Azure", learn("foundry-models/concepts/models-sold-directly-by-azure")),
        ("Foundry Models from partners and community", learn("foundry-models/concepts/models-from-partners")),
        ("Foundry Models sold by Azure (Azure Government)", learn("foundry-models/concepts/models-sold-directly-by-azure-gov")),
        ("Endpoints for Foundry Models", learn("foundry-models/concepts/endpoints")),
        ("Data, privacy and security for models sold by Azure", learn("responsible-ai/openai/data-privacy")),
        ("Claude models in Microsoft Foundry", learn("foundry-models/concepts/claude-models")),
        ("Compare hosting options for Claude models", learn("foundry-models/concepts/claude-models-hosting-comparison")),
        ("Hugging Face models in Foundry", learn("foundry-models/how-to/hugging-face-models")),
        ("Enable Fireworks models", learn("how-to/fireworks/enable-fireworks-models")),
        ("Fireworks model catalog", learn("how-to/fireworks/fireworks-model-catalog")),
        ("Import custom models into Fireworks", learn("how-to/fireworks/import-custom-models")),
        ("Fireworks privacy and compliance FAQ", learn("how-to/fireworks/privacy-compliance-faq")),
        ("Healthcare AI models", learn("how-to/healthcare-ai/healthcare-ai-models")),
        ("Model leaderboards and benchmarks", learn("concepts/model-benchmarks")),
        ("Playgrounds in Foundry", learn("concepts/concept-playgrounds")),
    ], w=W, cols=4)
