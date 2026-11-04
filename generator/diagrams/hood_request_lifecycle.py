"""Under the hood: one Responses call, end to end - a prompt agent and a hosted agent as two numbered sequence
diagrams (who handled each hop, as which identity, where the four guardrail gates sit, what was saved and traced).

Evidence convention on this canvas (same as the other 'under the hood' canvases): solid = documented on Microsoft
Learn, dashed amber = only a video or blog says so (labelled '(video/blog)'), dotted grey '?' = not documented."""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-request-lifecycle", title="One Responses call, end to end",
    section="8", order=3,
    description="A single Responses call followed hop by hop for a prompt agent and for a hosted agent: which component handles each step, "
                "which identity is on the wire, where the four guardrail gates sit, and what is persisted, streamed and traced.",
    tags=["responses api", "request lifecycle", "guardrails", "identity", "tracing"],
)

W = 3300
MAIN = 2260
SIDE_X = MAIN + 80
SIDE_W = W - SIDE_X
GREY = "#868e96"
RED = "#c92a2a"
LR = metrics.line_ratio()
LD = learn
YT = "https://www.youtube.com/watch?v="

# token key -> (theme, short name): the identity whose credential is on the wire for that arrow
TOK = {
    "caller": ("blue", "Caller"),
    "pmi": ("teal", "Project MI"),
    "agent": ("orange", "Agent identity"),
    "obo": ("violet", "User (OBO)"),
    "int": ("gray", "Not documented"),
}


def tcol(token):
    return GREY if token == "int" else THEMES[TOK[token][0]].stroke


def tdeep(token):
    return "#495057" if token == "int" else THEMES[TOK[token][0]].deep


# ---------------------------------------------------------------------------------------------- generic helpers
def vb_card(w, title, body, theme="yellow", **kw):
    """Video / blog-only claim: dashed amber border."""
    return Card(w, f"(video/blog) {title}", body, theme=theme, fill="soft", dash="dashed", **kw)


def nd_card(w, title, body, **kw):
    """Not documented or inferred: dotted grey border, '?' in the title."""
    return Card(w, f"? {title}", body, theme="gray", fill="soft", dash="dotted", **kw)


def link_lines(cv, x, y, items, size=12, prefix="Learn: "):
    for label, url in items:
        t = cv.text(x, y, f"{prefix}{label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


def src_panel(cv, x, y, items, w, cols, title, theme="gray", dash="solid", size=14):
    """Citation panel (own version so Learn sources keep a solid border and video/blog sources a dashed one)."""
    th = THEMES[theme]
    colw = (w - 40 - 24 * (cols - 1)) / cols
    entries = []
    for label, url in items:
        l1 = wrap_text(label, colw * 0.965, size)
        l2 = wrap_text(short_url(url), colw * 0.965, size - 2, MONO)
        h = len(l1) * size * LR + len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
        entries.append((l1, l2, url, h))
    per_col = -(-len(entries) // cols)
    heights = [sum(e[3] for e in entries[c * per_col:(c + 1) * per_col]) for c in range(cols)]
    H = 30 + max(heights) + 36
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash=dash)
        cv.text(x + 20, y + 14, title, size=size + 4, color=th.deep)
        for c in range(cols):
            cx = x + 20 + c * (colw + 24)
            cy = y + 14 + 30 + 6
            for l1, l2, url, h in entries[c * per_col:(c + 1) * per_col]:
                cv.text(cx, cy, "\n".join(l1), size=size, color=INK)
                cy += len(l1) * size * LR
                cv.text(cx, cy, "\n".join(l2), size=size - 2, color=LINK, font=MONO, link=url)
                cy += len(l2) * (size - 2) * metrics.line_ratio(MONO) + 8
    cv.register("sources", x, y, w, H)
    return y + H


def tile(cv, x, y, w, h, big, caption, theme, kind="doc"):
    """Big-number tile: solid hatch = Learn, dashed soft = video/blog, dotted grey = not documented."""
    th = THEMES[theme]
    if kind == "doc":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
    elif kind == "vb":
        cv.rect(x, y, w, h, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
    else:
        cv.rect(x, y, w, h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
    cv.text(x, y + 10, big, size=36, color=th.deep if kind != "nd" else GREY, align="center", w=w)
    lines = wrap_text(caption, (w - 30) * 0.96, 15)
    cv.text(x + 15, y + 10 + 36 * 1.25 + 2, "\n".join(lines), size=15, color=INK if kind != "nd" else MUTED,
            align="center", w=w - 30)
    cv.register("tile", x, y, w, h)


# ---------------------------------------------------------------------------------------------- the sequence engine
class Flow:
    """Sequence diagram + annotation table. Layout happens as rows are added; draw() renders everything in z-order
    (heads, lifelines, phase strips, frames, rows) and returns the bottom y.

    actors: [(label, sub, theme, icon)].  Each row can carry `what` (plain text, left column) and `extra`
    (right column items: ('fail'|'nd'|'vb'|'warn', text))."""

    def __init__(self, cv, x, y, actors, *, spacing, head_w=216, head_h=88, right=W, c1_share=0.56):
        self.cv, self.x, self.y = cv, x, y
        self.actors = actors
        self.sp, self.hw, self.hh = spacing, head_w, head_h
        self.cx = [x + head_w / 2 + i * spacing for i in range(len(actors))]
        self.diag_right = self.cx[-1] + head_w / 2
        self.right = right
        self.ax = self.diag_right + 46
        self.aw = right - self.ax
        self.c1 = round(self.aw * c1_share)
        self.cur = head_h + 24
        self.rows, self.phases, self.frames = [], [], []

    # ---- annotation layout
    def _ann(self, what, extra):
        w1 = self.c1 - 50
        l1 = wrap_text(what, w1, 14) if what else []
        h1 = len(l1) * 14 * LR
        w2 = self.aw - self.c1 - 8
        items, h2 = [], 0.0
        for kind, text in extra:
            prefix = {"nd": "? ", "vb": "(video/blog) "}.get(kind, "")
            pad = 7 if kind in ("nd", "vb", "warn") else 0
            lines = wrap_text(prefix + text, (w2 - 2 * pad) * 0.97, 14)
            bh = len(lines) * 14 * LR + 2 * pad
            items.append((kind, lines, bh))
            h2 += bh + 6
        if items:
            h2 -= 6
        return l1, items, max(h1, h2)

    # ---- layout-time API
    def phase(self, text, theme="gray"):
        self.phases.append(dict(y=self.cur, text=text, theme=theme))
        self.cur += 36 + 14

    def frame_open(self, label, lanes, theme="gray"):
        self.frames.append(dict(label=label, lanes=lanes, y0=self.cur, y1=None, theme=theme))
        self.cur += 36

    def frame_close(self):
        f = [f for f in self.frames if f["y1"] is None][-1]
        f["y1"] = self.cur + 2
        self.cur += 18

    def divider(self, text, lanes):
        self.rows.append(dict(kind="divider", y=self.cur, h=34, text=text, lanes=lanes))
        self.cur += 34

    def msg(self, src, dst, label, *, num=None, token="int", note=None, what="", extra=(), tag="doc", lw=None):
        x1, x2 = self.cx[src], self.cx[dst]
        span = abs(x2 - x1)
        lw = lw or min(max(span - 100, 170), 560)
        ll = wrap_text(label, lw, 15)
        lh = len(ll) * 15 * LR
        nl = wrap_text(note, max(span - 24, 170), 13) if note else []
        nh = len(nl) * 13 * LR
        left = 6 + lh + 8 + 8 + nh
        l1, items, ah = self._ann(what, extra)
        h = max(left, ah + 4, 52) + 16
        self.rows.append(dict(kind="msg", y=self.cur, h=h, src=src, dst=dst, ll=ll, lh=lh, nl=nl, num=num, token=token,
                              tag=tag, l1=l1, items=items))
        self.cur += h

    def step(self, lane, label, *, num=None, token="int", note=None, what="", extra=(), tag="doc", w=None):
        bw = w or min(self.sp - 14, 250)
        ll = wrap_text(label, bw - 28, 15)
        lh = len(ll) * 15 * LR
        nl = wrap_text(note, bw - 28, 13) if note else []
        nh = len(nl) * 13 * LR
        bh = 10 + lh + (4 + nh if nl else 0) + 10
        l1, items, ah = self._ann(what, extra)
        h = max(bh + 8, ah + 4, 52) + 16
        self.rows.append(dict(kind="step", y=self.cur, h=h, lane=lane, ll=ll, lh=lh, nl=nl, nh=nh, bw=bw, bh=bh, num=num,
                              token=token, tag=tag, l1=l1, items=items))
        self.cur += h

    # ---- drawing
    def _numc(self, cx, cy, n, token):
        s = str(n)
        d = 30 if len(s) < 3 else 38
        numbered(self.cv, cx, cy, n, theme=TOK[token][0], d=d, size=15 if len(s) < 3 else 14)

    def _draw_ann(self, r, Y):
        cv = self.cv
        if r.get("num") is not None:
            self._numc(self.ax + 18, Y + 22, r["num"], r["token"])
        if r["l1"]:
            cv.text(self.ax + 44, Y + 8, "\n".join(r["l1"]), size=14, color=INK)
        yy = Y + 8
        tx = self.ax + self.c1 + 6
        w2 = self.aw - self.c1 - 14
        for kind, lines, bh in r["items"]:
            txt = "\n".join(lines)
            if kind == "fail":
                cv.text(tx, yy, txt, size=14, color=RED)
            elif kind == "nd":
                cv.rect(tx - 3, yy - 3, w2, bh, stroke=GREY, fill="#f8f9fa", style="solid", sw=1.5, dash="dotted")
                cv.text(tx + 4, yy + 4, txt, size=14, color="#495057")
            elif kind == "vb":
                cv.rect(tx - 3, yy - 3, w2, bh, stroke="#f08c00", fill="#fff9db", style="solid", sw=1.5, dash="dashed")
                cv.text(tx + 4, yy + 4, txt, size=14, color="#5c3d00")
            else:  # warn: docs disagree
                cv.rect(tx - 3, yy - 3, w2, bh, stroke="#e8590c", fill="#fff4e6", style="solid", sw=1.5)
                cv.text(tx + 4, yy + 4, txt, size=14, color="#9c3a00")
            yy += bh + 6
        cv.line((self.ax, Y + r["h"] - 3), (self.right, Y + r["h"] - 3), stroke="#ced4da", sw=1, dash="dotted")

    def draw(self):
        cv = self.cv
        bottom = self.y + self.cur + 8
        # heads + lifelines
        for i, (label, sub, theme, icon) in enumerate(self.actors):
            Box(self.hw, label, sub=sub, h=self.hh, theme=theme, icon=icon, icon_pos="left", icon_size=32, size=16,
                sub_size=12).place(cv, self.cx[i] - self.hw / 2, self.y)
            cv.line((self.cx[i], self.y + self.hh), (self.cx[i], bottom), stroke=THEMES[theme].stroke, sw=2, dash="dashed",
                    opacity=55)
        # annotation header
        cv.text(self.ax + 44, self.y + self.hh / 2 - 14, "What happens", size=20, color=INK)
        cv.text(self.ax + self.c1 + 6, self.y + self.hh / 2 - 14, "If it goes wrong, and limits", size=20, color=RED)
        cv.line((self.ax - 24, self.y), (self.ax - 24, bottom), stroke="#adb5bd", sw=2, dash="dotted")
        cv.line((self.ax, self.y + self.hh + 8), (self.right, self.y + self.hh + 8), stroke=INK, sw=2)
        # phase strips (cover the lifelines)
        for p in self.phases:
            th = THEMES[p["theme"]]
            Y = self.y + p["y"]
            cv.rect(self.x, Y, self.right - self.x, 36, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0,
                    round_=False)
            cv.text(self.x + 14, Y + 6, p["text"], size=18, color=th.deep)
        # frames
        for f in self.frames:
            th = THEMES[f["theme"]]
            a, b = f["lanes"]
            fx0 = self.cx[a] - self.sp * 0.46
            fx1 = self.cx[b] + self.sp * 0.46
            Y0, Y1 = self.y + f["y0"], self.y + f["y1"]
            cv.rect(max(fx0, self.x), Y0, fx1 - max(fx0, self.x), Y1 - Y0, stroke=th.stroke, sw=2, dash="dotted",
                    style="solid")
            tw = metrics.text_size(f["label"], 15)[0] + 22
            cv.rect(max(fx0, self.x), Y0, tw, 26, stroke=th.stroke, fill=th.fill, style="solid", sw=1.5, rough=0, round_=False)
            cv.text(max(fx0, self.x) + 11, Y0 + 3, f["label"], size=15, color=th.deep)
        # rows
        for r in self.rows:
            Y = self.y + r["y"]
            if r["kind"] == "divider":
                a, b = r["lanes"]
                x0, x1 = self.cx[a] - self.sp * 0.4, self.cx[b] + self.sp * 0.4
                cv.line((max(x0, self.x), Y + 17), (x1, Y + 17), stroke=GREY, sw=1.5, dash="dotted")
                tw = metrics.text_size(r["text"], 14)[0] + 16
                cv.rect((x0 + x1) / 2 - tw / 2, Y + 6, tw, 22, stroke="transparent", fill="#ffffff", style="solid", sw=0, rough=0,
                        round_=False)
                cv.text((x0 + x1) / 2 - tw / 2 + 8, Y + 8, r["text"], size=14, color="#495057")
                continue
            col = tcol(r["token"])
            dash = {"doc": "solid", "inf": "dashed", "vb": "dashed", "nd": "dotted"}[r["tag"]]
            if r["kind"] == "msg":
                x1, x2 = self.cx[r["src"]], self.cx[r["dst"]]
                s = 1 if x2 >= x1 else -1
                ay = Y + 6 + r["lh"] + 8
                arrow(cv, [(x1 + s * 8, ay), (x2 - s * 8, ay)], color=col, sw=3, dash=dash, end_head="arrow")
                lane_theme = THEMES[self.actors[r["dst"]][2]]
                cv.rect(x2 - 6, ay - 14, 12, 28, stroke=lane_theme.stroke, fill=lane_theme.fill, style="solid", sw=1.5, rough=0,
                        round_=False)
                cxl = ((x1 + s * 50) + (x2 - s * 12)) / 2
                lt = "\n".join(r["ll"])
                tw, th_ = text_size(lt, 15)
                cv.rect(cxl - tw / 2 - 5, Y + 4, tw + 10, th_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                        rough=0, opacity=88, round_=False)
                cv.text(cxl - tw / 2, Y + 6, lt, size=15, color=INK, align="center", w=tw)
                if r["nl"]:
                    nt = "\n".join(r["nl"])
                    nw, nh_ = text_size(nt, 13)
                    cv.rect(cxl - nw / 2 - 5, ay + 6, nw + 10, nh_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0,
                            rough=0, opacity=88, round_=False)
                    cv.text(cxl - nw / 2, ay + 8, nt, size=13, color=tdeep(r["token"]), align="center", w=nw)
                if r["num"] is not None:
                    self._numc(x1 + s * 30, ay, r["num"], r["token"])
            else:
                cx = self.cx[r["lane"]]
                bx = max(cx - r["bw"] / 2, self.x)
                th = THEMES[TOK[r["token"]][0]]
                cv.rect(bx, Y + 4, r["bw"], r["bh"], stroke=col, fill=th.soft, style="solid", sw=2, dash=dash)
                lt = "\n".join(r["ll"])
                cv.text(bx + 14, Y + 4 + 10, lt, size=15, color=INK, align="center", w=r["bw"] - 28)
                if r["nl"]:
                    cv.text(bx + 14, Y + 4 + 10 + r["lh"] + 4, "\n".join(r["nl"]), size=13, color=tdeep(r["token"]),
                            align="center", w=r["bw"] - 28)
                if r["num"] is not None:
                    self._numc(bx if r["lane"] else bx + 16, Y + 4 + 4, r["num"], r["token"])
            self._draw_ann(r, Y)
        # footer heads: repeat the lane names where the eye ends up
        for i, (label, sub, theme, icon) in enumerate(self.actors):
            Box(self.hw, label, sub=sub, h=self.hh, theme=theme, icon=icon, icon_pos="left", icon_size=32, size=16,
                sub_size=12).place(cv, self.cx[i] - self.hw / 2, bottom)
        return bottom + self.hh


# ---------------------------------------------------------------------------------------------- top band
def phase_strip(cv, y):
    """Six phase cards: the 30-second story before the detailed sequences."""
    cw, gap = 490, 72
    cards = [
        Card(cw, "Admit the call", ["Caller token (audience https://ai.azure.com)", "DNS, TLS and the private endpoint",
                                    "Gateway authenticates and authorises", "Route by agent type"],
             theme="green", subtitle="steps 0 to 3", icon="foundry"),
        Card(cw, "Resolve and hydrate", ["Agent name to an immutable version", "Conversation or response chain",
                                         "Memories injected"], theme="cyan", subtitle="steps 4 to 5", icon="cosmos"),
        Card(cw, "Gate 1", ["User input: harm classes and Prompt Shields", "About +50 to 100 ms; block is HTTP 400"],
             theme="pink", subtitle="step 6", icon="content-safety"),
        Card(cw, "Think and act (a loop)", ["Model call: quota, router, cache", "Gate 2 on tool calls, Gate 3 on tool results",
                                            "Approvals; tools run in the service or in your app"],
             theme="blue", subtitle="steps 7 to 12", icon="openai"),
        Card(cw, "Release and persist", ["Gate 4 on the output", "Items appended, memories updated"], theme="pink",
             subtitle="steps 13 to 14", icon="content-safety"),
        Card(cw, "Stream and trace", ["SSE events or a background response", "invoke_agent spans and metrics"], theme="violet",
             subtitle="steps 15 to 16", icon="app-insights"),
    ]
    hmax = max(c.h for c in cards)
    for i, c in enumerate(cards):
        c.place(cv, i * (cw + gap), y, h=hmax)
        if i:
            arrow(cv, [(c.x - gap + 8, y + 52), (c.x - 8, y + 52)], color=INK, sw=3)
    return y + hmax


def legend_panel(cv, x, y, w):
    with cv.panel(x, y, title="How to read the two sequence diagrams", theme="gray", style="solid", fill="soft", pad=20,
                  title_size=22, w=w) as lg:
        cx, cy = lg.ix, lg.iy
        # row 1: line styles = evidence
        ax = cx
        for dash, col, label in (("solid", INK, "documented on Microsoft Learn"),
                                 ("dashed", "#f08c00", "only a video or blog says so, or it is inferred (video/blog)"),
                                 ("dotted", GREY, "? not documented")):
            arrow(cv, [(ax, cy + 12), (ax + 70, cy + 12)], color=col, sw=3, dash=dash)
            t = cv.text(ax + 82, cy + 1, label, size=16)
            ax += 82 + t.w + 44
        cv.text(ax + 10, cy + 1, "Time-sensitive facts carry: as of 2026-11-03", size=16, color=RED)
        # row 2: token colours
        cy2 = cy + 44
        cv.text(cx, cy2, "Arrow colour = whose credential is on the wire:", size=16, color="#495057")
        ax = cx + 410
        for key in ("caller", "pmi", "agent", "obo", "int"):
            arrow(cv, [(ax, cy2 + 12), (ax + 56, cy2 + 12)], color=tcol(key), sw=4)
            label = {"caller": "Caller (Entra token, audience https://ai.azure.com)", "pmi": "Project managed identity",
                     "agent": "Agent identity", "obo": "User OBO (preview)", "int": "Identity not documented"}[key]
            t = cv.text(ax + 66, cy2 + 1, label, size=16, color=tdeep(key))
            ax += 66 + t.w + 40
        # row 3: markers
        cy3 = cy2 + 44
        numbered(cv, cx + 15, cy3 + 12, 7, theme="blue")
        t = cv.text(cx + 40, cy3 + 1, "step number (H3 to H11 = hosted-agent only)", size=16)
        gx = cx + 40 + t.w + 40
        cv.rect(gx, cy3 - 2, 12, 28, stroke="#c2255c", fill="#fcc2d7", style="solid", sw=1.5, rough=0, round_=False)
        t = cv.text(gx + 24, cy3 + 1, "gate = a guardrail checkpoint", size=16)
        gx += 24 + t.w + 40
        cv.rect(gx, cy3 - 2, 70, 28, stroke=GREY, sw=2, dash="dotted", style="solid")
        t = cv.text(gx + 82, cy3 + 1, "loop or alternative frame", size=16)
        gx += 82 + t.w + 40
        draw_badge(cv, gx, cy3 + 2, "preview")
        cv.text(gx + 80, cy3 + 1, "preview feature", size=16)
        # row 4: the right-hand column
        cy4 = cy3 + 44
        cv.text(cx, cy4, "Right-hand column:", size=16, color="#495057")
        gx = cx + 200
        t = cv.text(gx, cy4 + 1, "red text = failure signal or limit", size=16, color=RED)
        gx += t.w + 50
        for kind, label in (("nd", "? not documented"), ("vb", "(video/blog) only a video or blog says so"),
                            ("warn", "docs disagree")):
            tw = metrics.text_size(label, 15)[0] + 20
            if kind == "nd":
                cv.rect(gx, cy4 - 3, tw, 28, stroke=GREY, fill="#f8f9fa", style="solid", sw=1.5, dash="dotted")
                col = "#495057"
            elif kind == "vb":
                cv.rect(gx, cy4 - 3, tw, 28, stroke="#f08c00", fill="#fff9db", style="solid", sw=1.5, dash="dashed")
                col = "#5c3d00"
            else:
                cv.rect(gx, cy4 - 3, tw, 28, stroke="#e8590c", fill="#fff4e6", style="solid", sw=1.5)
                col = "#9c3a00"
            cv.text(gx + 10, cy4, label, size=15, color=col)
            gx += tw + 30
    return lg


def identity_section(cv, y):
    _, hb = section_header(cv, 0, y, "Who is on the wire: four credentials, plus the ones nobody documents", w=W,
                           sub="Don't draw one 'Foundry' identity: the gateway, the platform and your agent each act as someone different")
    y0 = hb + 28
    rows = [
        [("Caller", "blue"), "A user, app, managed identity or channel. Entra token for audience https://ai.azure.com (AzureRbac) or the agent's blueprint audience (AgentBlueprint, preview)",
         "Authenticates to the project or agent endpoint. Needs the interact/action data action: Foundry Agent Consumer at agent scope, or Foundry User at project scope. API keys are not supported for agent endpoints"],
        [("Project MI", "teal"), "The project's managed identity",
         "Platform infrastructure: container image pull, Cosmos DB / Storage / AI Search runtime access, the model-inference proxy for hosted agents, service-side trace export"],
        [("Agent identity", "orange"), "A per-agent Entra identity under a blueprint. The credential never leaves the platform; the sandbox holds none",
         "Service-managed tool auth (the 4-stage exchange) and in-sandbox Azure or Entra calls through the token service"],
        [("User (OBO)", "violet"), "The signed-in user's delegated token (preview; needs AgentBlueprint access)",
         "Foundry IQ, Work IQ, Fabric, Dataverse and Azure DevOps MCP on behalf of the user. Agent Service sets x-ms-query-source-authorization itself for AI Search"],
        [("Not documented", "gray"), "Service-internal hops",
         "The guardrail engine and the prompt-agent runtime on the model hop: Learn doesn't say which identity they use"],
    ]
    t = Table([("Credential", 170), ("Principal", 690), "Used for"], rows, w=MAIN, theme="red", size=14, head_size=15,
              title="The four tokens you will see drawn on the arrows (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, y0)
    ly = link_lines(cv, 0, t.bottom + 8, [("Agent identity", LD("agents/concepts/agent-identity")),
                                          ("Hosted agent permissions", LD("agents/concepts/hosted-agent-permissions")),
                                          ("Agent endpoint authorization", LD("agents/concepts/agent-endpoint-authorization"))])
    n1 = Note(SIDE_W, "The agent guardrail REPLACES the model deployment's own filter, so Gate 1 and Gate 4 never double-scan. Gates 2 and 3 are preview and "
                      "only cover some tool types.", kind="key", title="Guardrail override",
              src=[("Guardrail intervention points", LD("guardrails/intervention-points"))])
    n1.place(cv, SIDE_X, y0)
    n2 = Note(SIDE_W, "Hosted-agent code never sees the blueprint credential: the token service and the tool server run outside the sandbox and only "
                      "identify the calling session.", kind="info", title="Where the credentials live",
              src=[("Hosted agent token service", LD("agents/concepts/hosted-agent-token-service"))])
    n2.place(cv, SIDE_X, n1.bottom + 24)
    return max(ly, n2.bottom)


# ---------------------------------------------------------------------------------------------- diagram A: prompt agent
def prompt_diagram(cv, y):
    actors = [
        ("Client", "SDK, app or channel", "gray", "users"),
        ("Foundry endpoint", "API gateway", "green", "foundry"),
        ("Prompt-agent runtime", "orchestrator on managed compute", "green", "container-apps"),
        ("Guardrail engine", "four gates", "pink", "content-safety"),
        ("Model gateway", "deployment, router, cache", "blue", "openai"),
        ("Tools Service", "+ Data Proxy in a BYO VNet", "orange", "toolbox-icon"),
        ("State stores", "agents, conversations, responses", "cyan", "cosmos"),
        ("App Insights", "traces and metrics", "violet", "app-insights"),
    ]
    f = Flow(cv, 0, y, actors, spacing=262)
    f.phase("A  Admit and prepare: steps 0 to 6", "green")
    f.step(0, "Get an Entra token, build the request", num=0, token="caller", note="caller token, audience https://ai.azure.com",
           what="AIProjectClient(endpoint, credential). POST {project}/openai/v1/responses with agent_reference {name} plus conversation or previous_response_id, stream, store, background.",
           extra=[("fail", "401 without a valid token. Agent endpoints don't support API keys.")])
    f.msg(0, 1, "HTTPS to the project endpoint", num=1, token="caller", note="as the caller",
          what="The name resolves to a public IP, or to the private-endpoint IP through privatelink.services.ai.azure.com (plus the openai and cognitiveservices zones) when isolated.",
          extra=[("fail", "Name resolution is the most common private-network error.")])
    f.step(1, "Authenticate and authorise", num=2, token="caller", note="validates the caller token",
           what="The API gateway validates the token, then checks the interact/action data action: Foundry Agent Consumer at agent scope, or Foundry User at project scope.",
           extra=[("fail", "401 or 403")])
    f.msg(1, 2, "Route by agent type", num=3, token="int", note="service-internal",
          what="Prompt agent: the prompt-agent runtime on Microsoft-managed compute (Learn's networking page draws it on Azure Container Apps). Hosted agent: a Micro VM (diagram B). The Copilot harness variant (preview) requires a conversation.")
    f.msg(2, 6, "Resolve the agent name to an immutable version", num=4, token="pmi", note="as the project MI",
          what="A version carries the model deployment, instructions, tools and the assigned guardrail. The project MI reads it from the Microsoft-managed store or from your Cosmos DB (agent-definitions-v1).",
          extra=[("fail", "404 unknown agent or version"), ("nd", "Which version runs when only a name is sent: not documented (samples pass the name only).")])
    f.msg(2, 6, "Hydrate the conversation or response chain", num=5, token="pmi", note="as the project MI (BYO Cosmos) or the managed store",
          what="conversation: load its items. previous_response_id: load the stored chain. store=false keeps nothing server-side. History longer than the context window is truncated for the model, not in the conversation. With the memory tool attached, static memories are injected at conversation start and contextual ones per turn.",
          extra=[("fail", "404 unknown conversation")])
    f.msg(2, 3, "Gate 1: user input", num=6, token="int", note="identity not documented",
          what="The agent's guardrail (else the deployment's) runs harm classifiers and Prompt Shields. About +50 to 100 ms per intervention point.",
          extra=[("fail", "Block = HTTP 400 content_filter, no model or tool call (documented for models and hosted agents; the prompt-agent shape is inferred)."),
                 ("nd", "Whether hydrated history is re-scanned: not documented.")])

    f.phase("B  Think and act: the model and tool loop, steps 7 to 12", "blue")
    f.frame_open("loop", (0, 5), "blue")
    f.msg(2, 4, "Model call", num=7, token="int", note="prompt-agent identity: not documented",
          what="The deployment named in the version: scope (Global, Data Zone, Regional), quota gate, optional model-router pick, prompt-cache lookup (prefix of at least 1,024 tokens), inference.",
          extra=[("fail", "HTTP 429 with retry-after-ms. PTU: instant 429 at 100%, no queue; spillover also fires on a 400 for long context, 500 and 503."),
                 ("nd", "The identity the prompt-agent runtime uses on this hop is not documented (hosted: project MI proxy).")])
    f.msg(2, 3, "Gate 2: tool call (preview)", num=8, token="int", note="identity not documented",
          what="If the model emitted a tool call: harm and task-adherence checks on its name and arguments. Supported tools only: AI Search, Functions, OpenAPI, SharePoint grounding, Fabric Data Agent, Bing grounding and Custom Search, Browser Automation.",
          extra=[("fail", "Block = the tool is not run; the agent halts until the next user input.")])
    f.msg(2, 0, "mcp_approval_request: the response ends", num=9, token="caller", note="your app approves in the same conversation",
          what="With require_approval the response ends with an mcp_approval_request item. Your app replies with mcp_approval_response: a NEW Responses call that re-enters at step 10.",
          extra=[("fail", "No reply = the run stays paused. 'The agent never continues' = wrong conversation or id.")])
    f.msg(2, 5, "Run the service-side tool", num="10a", token="agent", note="agent identity (blueprint exchange) or the project connection",
          what="Tools Service runs file search, code interpreter, web search, AI Search, MCP, OpenAPI, A2A and Azure Functions tools. Auth: the project connection, or the 4-stage blueprint exchange to an agent-identity token. BYO VNet: through the single-tenant Data Proxy.",
          extra=[("fail", "A non-streaming MCP call times out at 100 s (use background mode). 401 or 403 from the tool.")])
    f.divider("or, for client-side function calling", (0, 5))
    f.msg(2, 0, "function_call item: your app runs it", num="10b", token="caller", note="client-side; the app posts function_call_output next",
          what="The response completes with a function_call item. YOUR app runs the function and sends function_call_output in the next Responses call. One extra round trip.")
    f.msg(2, 3, "Gate 3: tool response (preview)", num=11, token="int", note="identity not documented",
          what="Scans the full tool payload for indirect and document attacks (supported tools only).",
          extra=[("fail", "Block = the agent stops immediately; the content is not saved to memory.")])
    f.step(2, "Append the results, call the model again", num=12, token="int", note="steps 7 to 11 repeat",
           what="Tool-result items are appended and the model is called again; several model and tool calls per run are possible.",
           extra=[("nd", "Maximum iterations and whole-run timeout: not documented.")])
    f.frame_close()

    f.phase("C  Release, persist and report: steps 13 to 16", "violet")
    f.msg(2, 3, "Gate 4: output", num=13, token="int", note="identity not documented",
          what="Harm, protected material and PII. Default: buffer, evaluate, release in chunks (costs time to first token). Async filter: stream now, verdict within about 1,000 characters.",
          extra=[("fail", "Blocked non-stream = 400 content_filter. Blocked stream = HTTP 200 plus a terminal SSE error (documented for hosted agents; prompt-agent equivalent inferred).")])
    f.msg(2, 6, "Persist the items, update memories", num=14, token="pmi", note="as the project MI",
          what="Response items are appended to the conversation (store=true is the default). Memory: update_memories is scheduled and debounced by update_delay.",
          extra=[("warn", "Docs disagree: retention is 30 days by default on the Azure OpenAI Responses page, 'until you delete it' on the Agent Service pages."),
                 ("nd", "When the commit happens relative to streaming: not documented.")])
    f.msg(1, 0, "Stream or return the response", num=15, token="caller", note="as the caller",
          what="SSE events flow while steps 7 to 13 run. Reconnect with GET /responses/{id}?stream=true&starting_after=<seq> (needs store=true and the original stream=true). background=true: queued, in_progress, then a terminal state.",
          extra=[("fail", "Known issue: background plus streaming performance; background has a higher time to first token.")])
    f.msg(2, 7, "Spans and metrics", num=16, token="pmi", note="as the project MI",
          what="Root span invoke_agent with children execute_tool, plan and memory spans, batched to Application Insights (Entra-auth ingestion). Model metrics (requests, PTU utilization, IsSpillover) live in Azure Monitor. The portal reads traces as the viewer.",
          extra=[("fail", "Forbidden on ingest = missing Monitoring Metrics Publisher or a local-auth mismatch.")])
    return f.draw()


# ---------------------------------------------------------------------------------------------- diagram B: hosted agent
def hosted_diagram(cv, y):
    actors = [
        ("Client", "SDK, app or channel", "gray", "users"),
        ("Foundry endpoint", "gateway + session control", "green", "foundry"),
        ("Guardrail engine", "agent-boundary gates", "pink", "content-safety"),
        ("Micro VM", "your container, one per session", "green", "vm"),
        ("Token service", "and tool server, outside the sandbox", "red", "managed-identity"),
        ("Project endpoint", "model proxy to the deployment", "blue", "openai"),
        ("Tools Service", "+ Data Proxy in a BYO VNet", "orange", "toolbox-icon"),
        ("State", "files, state store, conversations", "cyan", "cosmos"),
        ("App Insights", "two emitters", "violet", "app-insights"),
    ]
    f = Flow(cv, 0, y, actors, spacing=250)
    f.phase("A  Admit the call and wake the sandbox: steps 0 to H6", "green")
    f.step(0, "Get an Entra token, build the request", num=0, token="caller", note="same as diagram A",
           what="Same caller token and request as diagram A: POST {project}/openai/v1/responses with agent_reference, or the agent endpoint URL. Hosted endpoints serve /responses and /invocations.",
           extra=[("fail", "401 without a valid token.")])
    f.msg(0, 1, "HTTPS to the project endpoint", num=1, token="caller", note="as the caller",
          what="Same DNS and private-endpoint path as diagram A. See 'Networking internals' for the packet path into your VNet.")
    f.step(1, "Authenticate and authorise", num=2, token="caller", note="validates the caller token",
           what="Same checks as diagram A. Only an allow-list of caller headers reaches a hosted agent: x-client-*, content negotiation and tracing. Never Authorization, Host, Cookie or x-forwarded-*.",
           extra=[("fail", "401 or 403")])
    f.step(1, "Route by agent type: hosted", num=3, token="int", note="service-internal",
           what="A hosted agent takes the Micro VM path; a prompt agent takes the path in diagram A.")
    f.msg(1, 3, "Session, quota, version: provision or resume the Micro VM", num="H3", token="int", note="IP from your delegated subnet (BYO VNet)",
          what="agent_session_id in the body, or a conversation (it binds a stable session); none = a new session. Quota check, then the platform provisions or resumes a Micro VM and restores $HOME and /files. The session is bound to ONE version when it is created (versionSelector, FixedRatio).",
          extra=[("fail", "HTTP 429: session_quota_exceeded (the subscription's concurrent-session limit: 1,000 per region, 2,000 in seven regions), "
                          "regional_session_quota_exceeded (the region lacks capacity: back off or use another region) or subnet_exhausted (BYO VNet: no free IP)."),
                 ("warn", "Docs disagree: the concept page says traffic splitting between versions isn't supported; the rollout guide and REST samples show FixedRatio weights."),
                 ("nd", "Cold-start time: no published number (a blog says 'seconds, low variance').")])
    f.step(1, "Add platform headers", num="H4", token="int", note="x-agent-user-id, x-agent-foundry-call-id",
           what="The gateway adds the protocol 2.0.0 headers. The per-user isolation key is derived from the Entra token (or x-ms-user-identity).")
    f.msg(1, 2, "Gate 1 at the agent boundary", num="H5", token="int", note="before the container sees the request",
          what="The hosted guardrail (rai_config.rai_policy_name, a full ARM id) is evaluated at the boundary, not inside your code.",
          extra=[("fail", "Block = HTTP 400 content_filter. The invocations protocol needs invocations_moderation or the guardrail is inert. A bad policy id FAILS OPEN. Requests over 2 MB are unscreened.")])
    f.msg(1, 3, "POST /responses to port 8088", num="H6", token="int", note="TLS terminated by the platform",
          what="The protocol library (azure-ai-agentserver-responses) emits response.created, hydrates history when conversation.id is present, then runs your handler. Readiness: GET /readiness.")

    f.phase("B  Run your code: model, tools and network, steps H7 to H8", "blue")
    f.msg(3, 4, "Ask for a token (never IMDS)", num="H7a", token="agent", note="IDENTITY_ENDPOINT + IDENTITY_HEADER",
          what="ManagedIdentityCredential or DefaultAzureCredential talk to the hosted-agent token service, which runs outside the sandbox. The blueprint credential never enters it.")
    f.msg(3, 5, "Model call through FOUNDRY_PROJECT_ENDPOINT", num="H7b", token="agent", note="agent-identity token",
          what="The agent identity has implicit access to inference through the project endpoint. Going around it needs Cognitive Services OpenAI User or Foundry User on the account.")
    f.step(5, "Proxy to the account deployment", num="H7c", token="pmi", note="as the project MI",
           what="The project endpoint proxies inference to the account-level deployment with the project's managed identity, so the agent needs no role on the deployment. Quota, router and cache: diagram A, step 7.")
    f.msg(3, 6, "Tool call: Toolbox or MCP", num="H8a", token="agent", note="agent identity + x-agent-foundry-call-id",
          what="Toolbox and MCP calls go through the Tools Service and, in a BYO VNet, the single-tenant Data Proxy. Outbound Foundry calls must forward x-agent-foundry-call-id.")
    f.step(3, "Own outbound: egress proxy, then your NIC", num="H8b", token="int", note="HTTP 403 on deny (preview)",
           what="The agent's own outbound traffic is checked by the in-sandbox egress proxy (ordered host rules, first match wins; injected CA rotates about every 30 days), then leaves through the dedicated NIC under your NSG, UDRs and firewall.",
           extra=[("fail", "Deny = HTTP 403 to your HTTP client and a 'Network egress decision' span.")])
    f.msg(3, 2, "? Gates 2 and 3 for tools your code runs", num="H8c", token="int", tag="nd",
          what="", extra=[("nd", "Gates 2 and 3 for tools executed inside the container are not described for hosted agents; the egress policy is the documented analogue.")])

    f.phase("C  Return, persist and report: steps H9 to 16", "violet")
    f.msg(3, 2, "Gate 4 at the boundary: output", num="H9", token="int", note="identity not documented",
          what="Output is buffered or async-moderated at the boundary. Guardrail time shows up inside x-ms-debug-latency-container-response-ms.",
          extra=[("fail", "Blocked stream = HTTP 200 plus a terminal SSE error. A buffered response over 1 MB = 502; checks are truncated at 10,000 characters.")])
    f.msg(1, 0, "Stream or return the response", num=15, token="caller", note="as the caller",
          what="Lifecycle: created, in_progress, then completed, failed or cancelled. A later response.in_progress is a snapshot reset. Reconnect with starting_after (needs store=true).")
    f.msg(3, 7, "Persist files and state; the idle timer starts", num="H10", token="int", note="$HOME and /files persist; memory does not",
          what="Files persist on $HOME and /files, in-memory state does not. A durable key-value state store (explicit writes) and resilient background tasks (preview) cover crash recovery. Idle timeout: 900 s by default (120 to 14,400 s), then SIGTERM, flush, deprovision. Deleted after 30 days idle.",
          extra=[("vb", "BRK243 (about 0:15): a new session ID gets a brand-new filesystem and a VM recreated from the snapshot deployed with the agent; routines (preview) wake the same session.")])
    f.msg(3, 8, "In-sandbox spans (OpenTelemetry)", num="H11", token="agent", note="as the agent identity",
          what="Two exporters run in parallel: in-sandbox OTel spans (service.name = the agent name; optional OTLP) and the Agent Service spans below. Egress decisions show up here as 'Network egress decision' spans (preview).")
    f.msg(1, 8, "Agent Service spans (invoke_agent)", num=16, token="pmi", note="as the project MI",
          what="Service-side root span invoke_agent with execute_tool, plan and memory children, batched to Application Insights. The portal reads traces as the viewer.",
          extra=[("fail", "Forbidden on ingest = missing Monitoring Metrics Publisher or a local-auth mismatch."),
                 ("vb", "BRK201 (about 0:33): the traces show both service-injected spans and framework spans (LangGraph, LangChain): two emitters.")])
    return f.draw()


# ---------------------------------------------------------------------------------------------- sources
def sources_block(cv, y):
    learn_items = [
        ("Agent Service runtime components (agent, conversation, response lifecycle)", LD("agents/concepts/runtime-components")),
        ("Responses API: retention, background mode, starting_after", LD("openai/how-to/responses")),
        ("Model Context Protocol tool: approvals, allowed_tools, timeouts", LD("agents/how-to/tools/model-context-protocol")),
        ("Stream with reconnect", LD("agents/how-to/stream-with-reconnect")),
        ("Agent identity", LD("agents/concepts/agent-identity")),
        ("Agent endpoint authorization", LD("agents/concepts/agent-endpoint-authorization")),
        ("Guardrail intervention points", LD("guardrails/intervention-points")),
        ("Hosted agent guardrails", LD("agents/concepts/hosted-agent-guardrails")),
        ("Hosted agent runtime contract", LD("agents/concepts/hosted-agent-contract")),
        ("Hosted agent token service", LD("agents/concepts/hosted-agent-token-service")),
        ("Hosted agent permissions", LD("agents/concepts/hosted-agent-permissions")),
        ("Deep dive into Agent Service networking (Micro VM, Tools Service, Data Proxy)", LD("agents/concepts/agents-networking-deep-dive")),
        ("Add guardrails to a hosted agent (network egress controls, preview)", LD("agents/how-to/add-hosted-agent-guardrails")),
        ("Manage hosted sessions", LD("agents/how-to/manage-hosted-sessions")),
        ("Trace an agent: concepts and spans", LD("observability/concepts/trace-agent-concept")),
    ]
    vb_items = [
        ("Ignite 2025 BRK201 (about 0:32 and 0:36): service plus framework spans; stateful Responses", YT + "7faSLQS501E"),
        ("Build 2026 BRK243 (about 0:14 to 0:20): the session ID controls the filesystem", YT + "e_ZJy3RsNkg"),
        ("Reactor: Host your agents on Foundry (about 0:40): 'fast micro VM platform'", YT + "8N7q0Ucr3rw"),
    ]
    b1 = src_panel(cv, 0, y, learn_items, MAIN, 2, "Sources and further reading (Microsoft Learn)")
    b2 = src_panel(cv, SIDE_X, y, vb_items, SIDE_W, 1, "Sources: video and blog (not Learn)", theme="yellow", dash="dashed")
    return max(b1, b2)


# ---------------------------------------------------------------------------------------------- build
def build(cv: Canvas) -> None:
    _, bottom = title_block(
        cv, 0, 0, "One Responses call, end to end",
        "Under the hood - who handled each hop, as which identity, where the four guardrail gates sit, and what was saved and traced: a prompt agent, then a hosted agent",
        icon="foundry", w=W)
    y = bottom + 34
    y = phase_strip(cv, y) + 44
    lg = legend_panel(cv, 0, y, W)
    y = lg.bottom + 50
    y = identity_section(cv, y) + 60
    _, hb = section_header(cv, 0, y, "A  Prompt agent: streaming, one service-side tool and one MCP tool that needs approval", w=W,
                           sub="The orchestrator is Microsoft-managed. Every arrow names the credential on the wire; the right-hand table says what happens and how it fails")
    y = prompt_diagram(cv, hb + 34) + 60
    _, hb = section_header(cv, 0, y, "B  Hosted agent: the same call, with your container in a per-session Micro VM", w=W,
                           sub="Same front door and the same gates, but your code runs inside the sandbox: the H steps are what changes. Two emitters, three identities")
    y = hosted_diagram(cv, hb + 34) + 60
    n_next = Note(MAIN, "Part 2 follows four variants of the same call (client-side function, MCP approval, background and reconnect, Foundry IQ), "
                        "the time and limit markers along the path, what nobody documents and the docs that disagree. "
                        "For the packet path into your VNet see 'Networking internals: container injection and private paths'; "
                        "for the Micro VM itself see 'Hosted agent runtime'.", kind="key",
                  title="Continue with part 2 (hood-request-lifecycle-part-2)")
    n_next.place(cv, 0, y)
    sources_block(cv, n_next.bottom + 50)
