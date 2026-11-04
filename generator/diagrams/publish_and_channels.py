"""Publishing and channels (Agent Service), part 1: the stable agent endpoint and its authorization schemes, the channel map,
Entra agent identity, publishing to Microsoft 365 Copilot and Teams (sequence, scopes, package, private-network option and the
authorization fix), incoming A2A, telephony bindings, legacy Agent applications and the Agent Microsoft 365 Publishing REST operations.

Part 2 ('publish-and-channels-part-2') covers Microsoft Agent 365 and autopilots.  Preview items carry a Preview badge;
time-sensitive facts are stamped 'as of 2026-11-03'.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics
from generator.xd import Note as _KitNote

META = dict(
    id="publish-and-channels", title="Publishing and channels: endpoint, Microsoft 365, Teams and identity", section="2", group="Agent Service", order=16,
    description="How an agent becomes reachable and shareable: the stable endpoint and its authorization schemes, the channel map, Entra agent identity, "
                "publishing to Microsoft 365 Copilot and Teams (sequence, scopes, private-network option, authorization fixes), incoming A2A, telephony and the publishing REST operations.",
    tags=["publish", "agent-endpoint", "microsoft-365", "teams", "authorization", "entra-agent-id", "rest"],
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
    pub=("Publish agents to Microsoft Copilot and Microsoft Teams", learn("agents/how-to/publish-copilot")),
    vnet=("Publish agents by using the REST API (private network option)", learn("agents/how-to/publish-copilot-virtual-network")),
    tshoot=("Troubleshoot publishing agents to Microsoft Copilot and Teams", learn("agents/how-to/troubleshoot-publish-copilot")),
    tauth=("Troubleshoot authorization errors for published agents", learn("agents/how-to/troubleshoot-publish-copilot-authorization")),
    conf=("Configure your agent endpoint and settings", learn("agents/how-to/configure-agent")),
    auth=("Agent endpoint authorization", learn("agents/concepts/agent-endpoint-authorization")),
    cauth=("Configure agent endpoint authorization", learn("agents/how-to/configure-agent-endpoint-authorization")),
    idov=("Identity and access in Agent Service", learn("agents/concepts/identity-access-overview")),
    ident=("Agent identity", learn("agents/concepts/agent-identity")),
    apps=("Agent applications (legacy)", learn("agents/how-to/agent-applications")),
    mig=("Migrate from Agent applications", learn("agents/how-to/migrate-agent-applications")),
    a2a=("Enable the agent-to-agent endpoint", learn("agents/how-to/enable-agent-to-agent-endpoint")),
    a365=("Microsoft Agent 365 integration", learn("agents/concepts/agent-365-integration")),
    apov=("What is an autopilot in Microsoft Foundry?", learn("agents/concepts/autopilot-overview")),
    vpub=("Publish and connect voice agent channels", learn("agents/how-to/voice-agent-channels-publish")),
    vtel=("Integrate telephony channels (Teams Phone extensibility, Twilio)", learn("agents/how-to/voice-agent-telephony-channels")),
    rpub=("REST: publish an agent to Microsoft 365", learn("reference/rest/microsoft365-publishing-publish-agent-to-microsoft365")),
    rdef=("REST: get Microsoft 365 publish defaults", learn("reference/rest/microsoft365-publishing-get-microsoft365-publish-defaults")),
    rzip=("REST: generate a Microsoft 365 app package", learn("reference/rest/microsoft365-publishing-get-microsoft365-app-package")),
    priv=("Data, privacy and security for Agent Service", learn("responsible-ai/agents/data-privacy-security")),
    gov=("Agent Service in Azure Government", learn("agents/concepts/azure-government")),
    rbac=("Role-based access control for Microsoft Foundry", learn("concepts/rbac-foundry")),
    netw=("Set up private networking for Foundry Agent Service", learn("agents/how-to/virtual-networks")),
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


def cite(cv, x, y, items) -> float:
    """Clickable 'Learn:' lines; returns the bottom y."""
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=12, color=LINK, link=url)
        y = t.bottom + 2
    return y


def ct(text, th):
    return {"text": text, "theme": th, "color": THEMES[th].deep}


def head(cv, y, text, sub=None) -> float:
    """Section header across the canvas; returns the y where content can start."""
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


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


class Seq:
    """Sequence diagram whose labels sit on white backing, so a lifeline never runs through readable text."""

    def __init__(self, cv, x, y, actors, *, spacing=380, head_w=210, head_h=62, size=16, label_size=14):
        self.cv, self.x, self.label_size, self.spacing = cv, x, label_size, spacing
        self.gaps: dict = {}
        self.mark = cv.mark()
        self.actors = []
        for i, (label, th, icon) in enumerate(actors):
            cx = x + head_w / 2 + i * spacing
            b = Box(head_w, label, h=head_h, theme=th, icon=icon, icon_pos="left", icon_size=30, size=size, fill="solid")
            b.place(cv, cx - head_w / 2, y)
            self.actors.append((cx, THEMES[th], b))
        self.cur = y + head_h + 26
        self.right = x + head_w + (len(actors) - 1) * spacing

    def cx(self, i: int) -> float:
        return self.actors[i][0]

    def msg(self, a, b, text, *, num=None, dash="solid", wrap_w=None, sub=None):
        cv = self.cv
        x1, x2 = self.cx(a), self.cx(b)
        d = 1 if x2 > x1 else -1
        lo, hi = sorted((x1, x2))
        span = hi - lo
        ww = wrap_w or (span - 96 if span <= self.spacing + 1 else 400)
        txt = "\n".join(wrap_text(text, ww, self.label_size))
        tw, th_ = text_size(txt, self.label_size)
        y = self.cur + th_ + 12
        cv.poly([(x1 + 6 * d, y), (x2 - 6 * d, y)], kind="arrow", stroke=INK, sw=2, dash=dash, end_head="arrow")
        tx = (lo + hi) / 2 - tw / 2
        cv.rect(tx - 5, y - th_ - 8, tw + 10, th_ + 4, stroke="transparent", fill="#ffffff", style="solid", sw=0, rough=0,
                opacity=92, round_=False)
        cv.text(tx, y - th_ - 6, txt, size=self.label_size, color=INK, align="center", w=tw)
        if num is not None:
            numbered(cv, x1 + d * 20, y - 16, num, theme="blue", d=26, size=15)
        self.cur = y + 16
        if sub:
            sl = "\n".join(wrap_text(sub, max(span - 40, 160), self.label_size - 1))
            sw_, sh_ = text_size(sl, self.label_size - 1)
            cv.text((lo + hi) / 2 - sw_ / 2, y + 6, sl, size=self.label_size - 1, color=MUTED, align="center", w=sw_)
            self.cur = y + 12 + sh_
        return y

    def note(self, a, text, *, kind="info", w=340, b=None, title=None):
        n = Note(w, text, kind=kind, size=self.label_size, pad=10, title=title, title_size=16)
        mid = self.cx(a) if b is None else (self.cx(a) + self.cx(b)) / 2
        n.place(self.cv, mid - w / 2, self.cur)
        self.gaps.setdefault(a, []).append((self.cur, self.cur + n.h))
        self.cur += n.h + 20
        return n

    def end(self) -> float:
        cv = self.cv
        bottom = self.cur + 6
        for i, (cx, th, box) in enumerate(self.actors):
            y0 = box.y + box.h
            segs = []
            for g0, g1 in sorted(self.gaps.get(i, [])):
                if g0 - 4 > y0:
                    segs.append((y0, g0 - 4))
                y0 = max(y0, g1 + 4)
            segs.append((y0, bottom))
            for s0, s1 in segs:
                ln = cv.line((cx, s0), (cx, s1), stroke=th.stroke, sw=2, dash="dashed", opacity=70)
                cv.move_to(ln, self.mark)
        return bottom


def badge_on(cv, blk, kind, inset=14, up=13):
    """Status pill straddling the top-right corner of a placed block."""
    from generator.xd.palette import STATUS
    _, label = STATUS.get(kind, ("gray", kind))
    w = metrics.line_width(label, 13) + 18
    draw_badge(cv, blk.right - w - inset, blk.y - up, kind)


# ================================================================================================ band 0: tiles
def band_tiles(cv: Canvas, y: float) -> float:
    tiles = [
        Tile(C, "1 endpoint", "Every agent in the new model gets a stable endpoint and its own Entra agent identity at creation. Publishing is distribution, not endpoint creation.", "green"),
        Tile(C, "No API keys", "API keys are not supported. Callers use Entra (Azure RBAC, or an agent blueprint token in Preview) or an Azure Bot Service channel scheme.", "red"),
        Tile(C, "2 scopes", "Teams and Microsoft 365: Just you (no admin approval) or People in your organization (admin approval in the Microsoft 365 admin center).", "gray"),
        Tile(C, "Publish once", "New versions flow through the stable endpoint: move the version selector - no republish to Teams or Microsoft 365.", "green"),
        Tile(C, "Identity, not capability", "An autopilot is an agent with its own agent user account. One blueprint, many hired instances; hosted agents only (part 2).", "grape"),
        Tile(C, "As of 2026-11-03", "Preview: AgentBlueprint scheme, incoming A2A, MCP protocol, voice and telephony, Agent 365 Frontier (25 seats). Publishing carries no preview banner on Learn; a blog planned GA for June 2026.", "orange"),
    ]
    _, b = row(cv, 0, y, tiles, gap=G)
    return b


# ================================================================================================ band 1: the channel map
def band_map(cv: Canvas, y: float) -> float:
    y = head(cv, y, "1  The channel map: one stable endpoint, six ways in",
             "The endpoint and its Entra identity exist from the moment the agent is created. Each channel reaches it differently and is authorized differently.")
    top = y
    SPW, GH = 860, 210
    hubx = SPW + GH
    HUBW = W - 2 * hubx

    left = [
        card(SPW, "Programmatic clients", [
            "Apps, SDKs, REST clients, CLI and developer tools",
            "Entra token for the Foundry audience (https://ai.azure.com)",
            "Needs Foundry Agent Consumer (least privilege) at project or agent scope",
        ], theme="gray", icon="sdk", src=src("conf")),
        card(SPW, "Microsoft 365 Copilot and Teams", [
            "Publishing puts the stable endpoint in the Copilot and Teams catalogs",
            "Azure Bot Service relays the Activity protocol; a Teams app manifest is generated",
            "Scope: Just you, or People in your organization (admin approval)",
        ], theme="gray", icon="teams", src=src("pub")),
        card(SPW, "Other agents: incoming A2A", [
            "Agent card plus the a2a protocol on the endpoint",
            "Entra only; callers need Foundry Agent Consumer",
            "A2A v0.3 is the default if you do not specify; tasks are kept 60 days",
        ], theme="green", icon="a2a", badge="preview", src=src("a2a")),
    ]
    right = [
        card(SPW, "Phone calls (voice agents)", [
            "Teams Phone extensibility, Twilio or Direct SIP - the docs disagree on SIP, see the Voice agents canvases",
            "Channels tab: Preview web app and Phone numbers",
            "REST: .../telephony/bindings",
        ], theme="teal", icon="speech", badge="preview", src=src("vpub")),
        card(SPW, "Routines and triggers", [
            "A routine is one trigger plus one action: a timer or schedule, a GitHub issue event or a Teams channel message calls the agent",
            "Dispatch uses a Foundry-audience token; the AgentBlueprint scheme is not supported",
            "Keep AzureRbac (or its alias Entra) configured on the endpoint",
        ], theme="violet", icon="scheduler", badge="preview", src=src("auth")),
        card(SPW, "Microsoft Agent 365 registry", [
            "Registry sync: every published Foundry agent appears in the Agent 365 registry",
            "Autopilots: hosted agents only (part 2 of this canvas)",
            "Needs Frontier preview enrollment and Copilot or Agent 365 licensing",
        ], theme="grape", icon="enterprise-apps", badge="preview", src=src("a365")),
    ]
    need = max(sum(b.h for b in left), sum(b.h for b in right)) + 2 * 34
    with cv.panel(hubx, top, title="Agent endpoint", sub="one stable URL per agent - created with the agent, never republished", theme="green",
                  style="solid", fill="soft", pad=24, title_size=32, sub_size=16, w=HUBW, min_h=need) as hub:
        iw = HUBW - 48
        cv.text(hub.ix, hub.iy, "Protocols - several can be enabled at once", size=16, color=MUTED)
        chips = [Chip(t, theme=th, size=16) for t, th in (
            ("Responses", "green"), ("Activity", "green"), ("Invocations", "green"), ("A2A", "green"), ("MCP (preview)", "orange"),
            ("invocations_ws (hosted)", "green"), ("voice (voice agents)", "teal"))]
        cf = ChipFlow(chips, iw, gap=10)
        cf.place(cv, hub.ix, hub.iy + 28)
        by = cf.y + cf.h + 26
        bw = (iw - 26) / 2
        b1 = Box(bw, "version_selector", sub="latest (default) or pinned to one agent version. A new version flows through the endpoint: nothing to republish.",
                 theme="green", h=132, size=19, sub_size=14, fill="hatch", icon="versions", icon_pos="left", icon_size=32)
        b2 = Box(bw, "Entra agent identity", sub="blueprint + instance identity from creation; no Azure RBAC until you grant it; no secret or certificate.",
                 theme="red", h=132, size=19, sub_size=14, fill="hatch", icon="managed-identity", icon_pos="left", icon_size=32)
        row(cv, hub.ix, by, [b1, b2], gap=26)
        sy = by + 132 + 28
        cv.text(hub.ix, sy, "Who may call it: endpoint authorization schemes (section 2)", size=16, color=MUTED)
        chips2 = [Chip("AzureRbac (alias Entra)", theme="red", size=15), Chip("AgentBlueprint (preview)", theme="red", size=15, fill="soft", dash="dashed"),
                  Chip("BotServiceRbac", theme="red", size=15), Chip("BotServiceTenant", theme="red", size=15),
                  Chip("BotService (legacy)", theme="gray", size=15), Chip("NO API KEYS", theme="red", size=15, fill="hatch", sw=3)]
        cf2 = ChipFlow(chips2, iw, gap=10)
        cf2.place(cv, hub.ix, sy + 28)
        CodeBlock(iw, [
            "https://{account}.services.ai.azure.com/api/projects/{project}/agents/{agent}/endpoint/protocols/openai/responses",
            "https://{account}.services.ai.azure.com/api/projects/{project}/agents/{agent}/endpoint/protocols/activityProtocol?api-version=v1",
        ], title="Endpoint routes (new agent model): one URL per protocol under the agent", theme="green", size=14,
                  src=[U["conf"], U["vnet"]]).place(cv, hub.ix, cf2.y + cf2.h + 26)

    def stack(blocks, x):
        total = sum(b.h for b in blocks)
        gap = (hub.h - total) / (len(blocks) - 1)
        yy = top
        for b in blocks:
            b.place(cv, x, yy)
            yy += b.h + gap

    stack(left, 0)
    stack(right, W - SPW)
    lw = GH - 40
    col_in = "#2b8a3e"
    for b, lab in zip(left, ("Responses or another enabled protocol", "Activity protocol via Azure Bot Service", "A2A (preview)")):
        arrow(cv, [(b.right + 8, b.cy), (hubx - 8, b.cy)], color=col_in, sw=3, label=lab, label_size=14, label_wrap=lw, end_head="arrow")
    for b, lab in zip(right[:2], ("voice protocol and telephony bindings", "routine dispatch (AzureRbac or Entra)")):
        arrow(cv, [(b.x - 8, b.cy), (hubx + HUBW + 8, b.cy)], color=col_in, sw=3, label=lab, label_size=14, label_wrap=lw, end_head="arrow")
    arrow(cv, [(hubx + HUBW + 8, right[2].cy), (right[2].x - 8, right[2].cy)], color="#862e9c", sw=3, dash="dashed", label="registry sync",
          label_size=14, label_wrap=lw, end_head="arrow")

    ny = max(hub.bottom, left[-1].bottom, right[-1].bottom) + 36
    n1 = Note(S(2), "The endpoint exists from creation. Publishing adds the Activity protocol, a Bot Service authorization scheme and catalog entries; programmatic "
                    "clients never needed a publish step.", kind="key", title="Publishing is distribution, not endpoint creation", src=src("conf", "pub"))
    n2 = Note(S(2), "Where the store lists the agent (scope) and who may call it (authorization scheme) are separate settings. A user who can open the agent can still be "
                    "refused: section 5 shows the fix.", kind="warn", title="Visibility is not authorization", src=src("tauth"))
    n3 = Note(S(2), "Published agents get a stable endpoint and an Entra identity. There is no A2A tool and no hosted agents in Azure Government (as of 2026-11-03).",
              kind="info", title="Azure Government", src=src("gov"))
    row(cv, 0, ny, [n1, n2, n3], gap=G, equalize=True)
    return ny + max(n1.h, n2.h, n3.h)


# ================================================================================================ band 2: authorization
def band_auth(cv: Canvas, y: float) -> float:
    y = head(cv, y, "2  Who may call the endpoint: authorization schemes",
             "Configure several schemes on one endpoint (for example Azure RBAC for apps plus one Bot Service scheme for Teams). The token audience selects the scheme that can authorize a request.")
    top = y
    t = Table([("Scheme", 270), ("Token and validation", 760), ("Who is allowed (authorization rule)", 800), ("Typical use", 554)], [
        [ct("AzureRbac (alias Entra)", "red"), "The caller presents a token for the Foundry resource (audience https://ai.azure.com)",
         "Azure RBAC: the principal needs the interact permission (Foundry Agent Consumer) at project or agent scope",
         "Applications, SDKs, REST clients, developer tools and workload callers"],
        [ct("AgentBlueprint (Preview)", "orange"), "A token for the agent's own agent blueprint; the endpoint applies the scheme's token-validation rules",
         "No Foundry role: delegated clients must be allowed to request the scope; app-only callers need an allowed_clients list",
         "Applications that need access to one agent without Foundry RBAC permissions"],
        [ct("BotServiceRbac", "red"), "Azure Bot Service validates the channel request (Activity protocol)",
         "Azure RBAC: the signed-in user needs an Azure role that permits access to the agent",
         "Teams and Microsoft 365 where each user needs the Azure permission (the Just you scope)"],
        [ct("BotServiceTenant", "red"), "Azure Bot Service validates the channel request (Activity protocol)",
         "A fixed tenant rule: the signed-in user must be in the configured tenant",
         "Teams and Microsoft 365 for tenant-wide access (People in your organization)"],
        [ct("BotService (legacy)", "gray"), "Azure Bot Service validates the channel request",
         "No additional user authorization rule",
         "Legacy compatibility only: new agents use BotServiceRbac or BotServiceTenant"],
    ], w=S(4), theme="red", size=14, head_size=15, title="Five schemes (as of 2026-11-03)", title_size=22)
    t.place(cv, 0, top)
    ny = t.bottom + 20
    cv.text(0, ny, "Learn: Agent endpoint authorization", size=12, color=LINK, link=U["auth"][1])
    ny += 30
    nw = (S(4) - 2 * G) / 3
    n1 = Note(nw, "Only one of BotService, BotServiceRbac and BotServiceTenant at a time. A PATCH replaces the whole authorization_schemes array, so send every scheme you want to keep. "
                  "Never configure both AzureRbac and its alias Entra on one endpoint.", kind="warn", title="Rules that bite")
    n2 = Note(nw, "Routine dispatch uses a Foundry-audience token and does not support the preview AgentBlueprint scheme: keep AzureRbac (or Entra) on any endpoint a routine calls.",
              kind="info", title="Routines")
    n3 = Note(nw, "Calling an agent and managing it are different permissions. Agent-scope role assignments give invoke only; they never grant control-plane or management rights.",
              kind="key", title="Invoke is not manage")
    row(cv, 0, ny, [n1, n2, n3], gap=G, equalize=True)
    left_bottom = ny + max(n1.h, n2.h, n3.h)

    rx, rw = S(4) + G, S(2)
    c1 = card(rw, "Azure RBAC scheme in detail", [
        "The default scheme for an agent endpoint",
        "Permission: Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action",
        "Foundry Agent Consumer is the least-privilege role (definition ID eed3b665-ab3a-47b6-8f48-c9382fb1dad6); Foundry User also includes the permission but can create and manage agents",
        "Assign at project scope (every agent) or agent scope (one agent)",
        "Entra is the older name for the same behaviour: keep it only for existing configurations or client libraries",
    ], theme="red", icon="key-vault", src=src("auth", "rbac"))
    c1.place(cv, rx, top)
    c2 = card(rw, "AgentBlueprint scheme in detail", [
        "Delegated: sign the user in and request api://<agent-blueprint-client-id>/access_agent (both parts are defaults you can change)",
        "App-only: request /.default; the rules need a non-empty token_validation_rules.allowed_clients that contains the caller's application ID",
        "Foundry preauthorizes first-party clients (portal, CLI, Visual Studio Code); customer-owned clients need preauthorization or consent",
        "Rules can restrict audiences, tenants, client applications, principals and delegated permissions",
        "! Getting a blueprint token and being accepted by the endpoint are separate checks",
    ], theme="orange", icon="managed-identity", badge="preview", src=src("auth", "cauth"))
    c2.place(cv, rx, c1.bottom + 24)
    return max(left_bottom, c2.bottom)


# ================================================================================================ band 3: identity
def band_identity(cv: Canvas, y: float) -> float:
    y = head(cv, y, "3  Identity: who is the caller at each hop, and what an autopilot adds",
             "Every Foundry agent has an Entra agent identity from creation. Permissions never carry across the three boundaries - see the 'Agent identity and delegation' canvas for the full model.")
    top = y
    bw = S(2)
    bounds = [
        ("Boundary 1 - manage", "gray", ("Developer", "user", "gray"), ("Foundry project and agent", "foundry", "green"), "create, configure,\nupdate, delete",
         "Decided by Foundry RBAC roles (management access)."),
        ("Boundary 2 - invoke", "red", ("Caller: app, user or channel", "sdk", "gray"), ("Agent endpoint", "agent", "green"), "interact\n(section 2)",
         "Decided by the endpoint authorization scheme. Being allowed to invoke never grants management."),
        ("Boundary 3 - act", "orange", ("Agent with its own identity", "managed-identity", "red"), ("Tool, data or model", "toolbox", "orange"), "calls as\nthe agent",
         "A separate hop: the agent's own identity reaches the tool. Permissions do not carry across boundaries."),
    ]
    bottoms = []
    for i, (title, th, a, b, lab, cap) in enumerate(bounds):
        x0 = i * (bw + G)
        with cv.panel(x0, top, title=title, theme=th, style="dotted", pad=18, title_size=20, w=bw) as p:
            ba = Box(340, a[0], h=92, theme=a[2], icon=a[1], icon_pos="left", icon_size=30, size=17, fill="hatch")
            bb = Box(340, b[0], h=92, theme=b[2], icon=b[1], icon_pos="left", icon_size=30, size=17, fill="hatch")
            ba.place(cv, p.ix, p.iy)
            bb.place(cv, x0 + bw - 18 - 340, p.iy)
            arrow(cv, [(ba.right + 8, ba.cy), (bb.x - 8, bb.cy)], color=THEMES[th].stroke, sw=3, label=lab, label_size=14,
                  label_wrap=max(bb.x - ba.right - 40, 120), end_head="arrow")
            cv.text(p.ix, ba.bottom + 14, wrap(cap, bw - 40, 15), size=15, color=INK)
        bottoms.append(p.bottom)
    top2 = max(bottoms) + 40

    # ---- identity ladder (left)
    sw_ = S(3)
    cw3 = (sw_ - 2 * 36) / 3
    cv.text(0, top2, "Identity ladder: three kinds of Foundry agent", size=22, color=THEMES["red"].deep)
    s1 = card(cw3, "Assistive", [
        "Agent identity + the signed-in user's context",
        "Acts on behalf of a user, only within that user's permissions",
        "Best for personal productivity, for example a meeting-prep agent that drafts a deck on request",
    ], theme="red", icon="user")
    s2 = card(cw3, "Background service", [
        "Agent identity with app-only permissions",
        "Acts as itself, autonomously, with no signed-in user and no agent user account",
        "Cannot perform Microsoft 365 actions",
        "Best for app automation, for example an operations agent that restarts a VM on an alert",
    ], theme="red", icon="gear")
    s3 = card(cw3, "Autopilot", [
        "Agent identity + an Entra agent user account",
        "The account gives it an email address, calendar, OneDrive, Teams presence and an org-chart slot",
        "Acts as itself in Microsoft 365, including in group chats, with no user in the loop",
        "Best for digital coworkers, for example a release manager in a Teams group chat",
    ], theme="grape", icon="users", badge="preview", src=src("apov"))
    base = max(s1.h, s2.h, s3.h)
    steps_y = top2 + 80
    for i, s in enumerate((s1, s2, s3)):
        s.place(cv, i * (cw3 + 36), steps_y, h=base)
    gy = steps_y + base + 14
    cv.line((0, gy), (sw_, gy), stroke=THEMES["red"].stroke, sw=3)
    cv.text(0, gy + 8, "Common to all three: an Entra agent identity (a service principal) exists from the moment the agent is created. The agent user account is what an autopilot adds.",
            size=15, color=INK)
    arrow(cv, [(10, steps_y - 22), (sw_ - 10, steps_y - 22)], color="#862e9c", sw=3, dash="dashed",
          label="more autonomy as itself in Microsoft 365", label_size=16, end_head="arrow")

    # ---- shapes: 1 blueprint : 1 identity vs 1 blueprint : many hired instances
    my = gy + 64
    pw1 = 560
    with cv.panel(0, my, title="Regular agent: 1 : 1 : 1", sub="one blueprint, one identity, no user account", theme="green", style="dashed", pad=16,
                  title_size=20, sub_size=14, w=pw1) as pa:
        bp = Box(210, "Agent blueprint", h=76, theme="gray", size=16, fill="hatch")
        ai = Box(210, "Agent identity", h=76, theme="red", size=16, fill="hatch")
        bp.place(cv, pa.ix, pa.iy + 6)
        ai.place(cv, pa.ix + pw1 - 32 - 210, pa.iy + 6)
        connect(cv, bp, ai, sw=3, color="#2b8a3e")
    pbx = pw1 + 40
    pbw = sw_ - pbx
    with cv.panel(pbx, my, title="Autopilot: one blueprint, many hired instances", sub="each hire creates its own agent identity and agent user account", theme="grape",
                  style="dashed", pad=16, title_size=20, sub_size=14, w=pbw) as pb2:
        bp2 = Box(200, "Agent blueprint", sub="what it can do + platform infrastructure", h=150, theme="gray", size=16, sub_size=13, fill="hatch")
        inst = [Box(440, f"{t} instance", sub="own agent identity + own agent user account; one license", h=70, theme="grape", size=16, sub_size=13, fill="hatch")
                for t in ("Team A", "Team B")]
        bp2.place(cv, pb2.ix, pb2.iy + 4)
        ix_ = pb2.ix + 200 + 130
        inst[0].place(cv, ix_, pb2.iy)
        inst[1].place(cv, ix_, pb2.iy + 80)
        for b_ in inst:
            connect(cv, bp2, b_, a_side="right", b_side="left", sw=3, color="#862e9c", label="hire", label_size=14)
        cv.text(ix_ + 440 + 22, pb2.iy, wrap("Policy is set once: every instance inherits it. Update the blueprint and all instances update; block it and all stop.", pbx + pbw - 16 - (ix_ + 440 + 22), 14),
                size=14, color=INK)
    left_bottom = max(pa.bottom, pb2.bottom) + 6

    # ---- tables and token flow (right)
    rx, rwid = S(3) + G, S(3)
    t1 = Table([("Object", 230), ("What it is", 250), "What it holds"], [
        [ct("Agent identity", "red"), "A service principal", "The agent ID, agent name, sponsor and the permissions the agent authenticates with. For an autopilot it secures the infrastructure that runs the agent."],
        [ct("Agent user account", "grape"), "A user object", "Display name, manager and user principal name: the autopilot's presence in Microsoft 365. Never interchangeable with the agent identity."],
    ], w=rwid, theme="red", size=14, head_size=15, title="Two identity objects, two jobs", title_size=20)
    t1.place(cv, rx, top2)
    t2 = Table([("Shape", 230), ("Blueprint : identity : user account", 480), "Notes"], [
        [ct("Regular Foundry agent", "green"), "1 agent : 1 blueprint : 1 agent identity : no user account", "The blueprint is an agent blueprint application plus a blueprint service principal that holds the security context and credentials."],
        [ct("Autopilot", "grape"), "1 blueprint : many hired instances; each instance has its own agent identity and agent user account", "You build a blueprint, not an autopilot. Only hosted agents can be published as autopilot blueprints."],
    ], w=rwid, theme="red", size=14, head_size=15, title="Identity shapes", title_size=20)
    t2.place(cv, rx, t1.bottom + 24)
    fy = t2.bottom + 30
    cv.text(rx, fy, "Runtime token exchange: four stages, no secret or certificate", size=20, color=THEMES["red"].deep)
    fw = (rwid - 3 * 56) / 4
    flow = [
        Box(fw, "1 Blueprint authenticates", sub="the blueprint signs in with a federated credential: no secret or certificate", theme="red", h=112, size=16, sub_size=13, fill="hatch"),
        Box(fw, "2 Agent-identity token", sub="an agent-identity token for the instance", theme="red", h=112, size=16, sub_size=13, fill="hatch"),
        Box(fw, "3 Scoped token", sub="a scoped token for the downstream resource", theme="red", h=112, size=16, sub_size=13, fill="hatch"),
        Box(fw, "4 Tool call", sub="the call to the tool", theme="orange", h=112, size=16, sub_size=13, fill="hatch"),
    ]
    row(cv, rx, fy + 36, flow, gap=56)
    for a, b in zip(flow, flow[1:]):
        connect(cv, a, b, sw=3, color="#c92a2a")
    iy = flow[0].bottom + 20
    cv.text(rx, iy, "Identities appear in the Entra admin center inventory:", size=15, color=MUTED)
    cf = ChipFlow([Chip(t, theme="gray", size=14, fill="soft") for t in ("Conditional Access", "Sign-in logs", "Audit logs", "Sponsors")], rwid - 440, gap=8)
    cf.place(cv, rx + 440, iy - 6)
    cv.text(rx, cf.y + cf.h + 8, "Learn: Agent identity", size=12, color=LINK, link=U["ident"][1])
    cv.text(rx + 190, cf.y + cf.h + 8, "Learn: Identity and access in Agent Service", size=12, color=LINK, link=U["idov"][1])
    nk = Note(rwid, "The blueprint's federated credential trusts the 'Azure Machine Learning' resource-provider app (0736f41a-0425-4b46-bdb5-1563eff02385). A new agent identity starts "
                    "with no Azure RBAC assignments: grant it only what its tools need.", kind="key", title="Nothing to store, nothing to rotate")
    nk.place(cv, rx, cf.y + cf.h + 44)
    return max(left_bottom, nk.bottom + 6)


# ================================================================================================ band 4: publish
def band_publish(cv: Canvas, y: float) -> float:
    y = head(cv, y, "4  Publish to Microsoft 365 Copilot and Teams",
             "Publishing submits the agent's stable endpoint to the Copilot and Teams catalogs through Azure Bot Service. Users reach the same endpoint, so a new agent version needs no republish.")
    top = y
    seq = Seq(cv, 0, top, [("Developer", "gray", "user"), ("Foundry", "green", "foundry"), ("Azure Bot Service", "indigo", "bot"),
                           ("Microsoft 365", "gray", "teams"), ("End user", "gray", "user")], spacing=385, head_w=225)
    seq.msg(0, 1, "Publish: scope + metadata (name, version, descriptions, developer links)", num=1)
    seq.msg(1, 2, "Create or reuse the Azure Bot Service (REST: pass botServiceArmId)", num=2)
    seq.note(1, "Foundry builds the Teams app manifest .zip, turns on the activity protocol and sets BotServiceRbac (Just you) or BotServiceTenant (organization).", kind="info", w=370)
    seq.msg(1, 3, "Submit the manifest to the Copilot and Teams catalogs", num=3)
    seq.note(3, "Organization scope: an admin approves in the Microsoft 365 admin center. Just you: no approval; listed under Your agents.", kind="warn", w=370)
    seq.msg(4, 3, "Find the agent in the store", num=4)
    seq.msg(4, 3, "Send a message; sign in when prompted", num=5)
    seq.msg(3, 2, "The channel relays the message to the bot", num=6)
    seq.msg(2, 1, "Activity protocol call to the stable endpoint", num=7)
    seq.note(1, "Foundry validates the signed channel token against the agent identity, then the scheme: Azure RBAC (BotServiceRbac) or tenant (BotServiceTenant).", kind="key", w=370)
    seq.msg(1, 4, "Reply from the active version (latest or pinned) via the channel", num=8, dash="dashed")
    sbottom = seq.end()
    cv.text(0, sbottom + 12, "Learn: Publish agents to Microsoft Copilot and Microsoft Teams", size=12, color=LINK, link=U["pub"][1])
    sbottom += 36

    rx, rw = S(3) + G, S(3)
    cw = (rw - G) / 2
    pre = card(cw, "Prerequisites", [
        "Azure Bot Service Contributor (or Contributor or Owner) on the resource group: Microsoft.BotService/botServices/write and .../channels/write",
        "Foundry roles do not include those permissions",
        "Foundry User on the project: create, manage and publish agents",
        "The Microsoft.BotService resource provider registered in the subscription",
        "An active agent version, tested thoroughly in the portal first",
        "! The portal cannot publish a project that disables public network access - use the REST route (section 5)",
    ], theme="red", icon="key-vault", src=src("pub"))
    does = card(cw, "What publish does", [
        "Validates the submitted properties (display name, description, version)",
        "Compiles a Teams app manifest as a .zip package",
        "Submits the manifest to the Microsoft Copilot and Teams agent catalogs on your behalf",
        "Enables the activity protocol on the endpoint",
        "Enables BotServiceRbac (Just you) or BotServiceTenant (organization)",
        "The active version is what the stable endpoint serves: confirm it before you publish (Details > Active version, or the Publish button)",
    ], theme="green", icon="teams", src=src("pub"))
    _, b = row(cv, rx, top, [pre, does], gap=G)
    ty = b + 26
    t1 = Table([("Portal option", 190), ("REST publishScope", 190), ("Authorization scheme", 190), ("Admin approval", 170), ("Where it appears", 560), ("Best for", 476)], [
        [ct("Just you", "green"), "Shared (Personal is accepted and treated as Shared)", "BotServiceRbac", "Not required",
         "Available at once under Your agents; only you see it - share the agent link. In a Teams chat, participants with the required Foundry permissions on the project can use it.",
         "Personal testing, small teams, pilots"],
        [ct("People in your organization", "grape"), "Tenant", "BotServiceTenant", "Required: Microsoft 365 admin center, Requests",
         "After approval it appears under Built by your org for everyone in the tenant; app policies control which users can access it.",
         "Organization-wide distribution, production deployments"],
    ], w=rw, theme="gray", size=14, head_size=15, title="Scope = visibility, and it picks the authorization scheme", title_size=20)
    t1.place(cv, rx, ty)
    cv.text(rx, t1.bottom + 8, "Naming: one FAQ calls Just you 'Individual scope (previously Shared scope)'.  Learn: Publish agents to Microsoft Copilot and Microsoft Teams",
            size=12, color=LINK, link=U["pub"][1])
    my = t1.bottom + 40
    t2 = Table([("Metadata field", 300), ("What to enter", 1000), ("Status", 476)], [
        ["Name", "Display name shown in the agent store", ct("Required", "red")],
        ["Publish version", "Three-part version number (major.minor.patch); raise it to change user-facing properties", ct("Required", "red")],
        ["Short description", "One sentence about what the agent does", ct("Required", "red")],
        ["Description", "Longer text: the agent's responsibilities and the actions it can take", ct("Required", "red")],
        ["Developer", "Your name or organization name (shown under Author)", ct("Required", "red")],
        ["Developer website, Terms of use, Privacy statement", "URLs under More; HTTPS is required", ct("Optional", "gray")],
    ], w=rw, theme="gray", size=14, head_size=15, title="Portal metadata fields (no secrets or API keys: users can see them)", title_size=20)
    t2.place(cv, rx, my)
    right_bottom = t2.bottom

    y2 = max(sbottom, right_bottom) + 44
    c1 = card(C, "Direct publish or download", [
        "Portal: Publish > Teams and Microsoft Copilot (or Details > Channels)",
        "Metadata dialog, then Next: Publish options",
        "Direct publish tab: choose who can use it, then Publish",
        "Download and customize tab: Download ZIP, edit the user-facing metadata, then in Teams use Apps > Manage your apps > Upload an app",
        "Foundry validates the ZIP exactly like a direct publish; an invalid package returns an error, never an unvalidated ZIP",
    ], theme="green", icon="teams", src=src("pub"))
    c2 = card(C, "Inspect the package", [
        "Contents: manifest.json, icon-color.png and icon-outline.png (more files for extra Microsoft 365 capabilities)",
        "Check: version, name.short and name.full, descriptions, developer links, bots[0].scopes and the icons at the ZIP root",
        "! Keep the service-generated IDs unchanged: id, bots[0].botId, webApplicationInfo.id and copilotAgents.customEngineAgents[0].id",
        "Change only user-facing metadata and assets; never remove generated agent sections",
    ], theme="gray", icon="files", src=src("pub"))
    c3 = card(C, "Update after publishing", [
        "New agent version: update the version selector. The endpoint stays the same - no republish",
        "Always use latest (the default) serves a new version in Microsoft 365 and Teams at once; if you pinned a version, move the selector",
        "Display text: Publish > Update agent Teams and Microsoft Copilot display properties; changed fields overwrite, others carry forward",
        "appVersion auto-increments if you do not set it; REST republish of an existing version fails",
        "! Docs disagree on splitting traffic across versions: see part 2, section 6",
    ], theme="teal", icon="versions", src=src("pub"))
    c4 = card(C, "Limitations (as of 2026-11-03)", [
        "File uploads and image generation do not work in Microsoft 365 (they work in Teams)",
        "No streaming responses and no citations for published agents",
        "Foundry User is not enough for the Bot Service resource",
        "Voice agents hide the standard Teams and Microsoft 365 card; phone numbers are a different integration",
    ], theme="orange", icon="preview-features", src=src("vnet", "pub"))
    n = Note(S(2), "Microsoft 365 and Teams process and store data tied to publishing and using the agent: its name, icon and description, and the responses users receive. "
                   "That data follows Microsoft 365 and Teams terms, compliance commitments and data residency, not your Foundry region. Check your own compliance and residency "
                   "requirements before you publish. Never put secrets or API keys in metadata: users can see those fields.",
             kind="gotcha", title="Data flows leave the Foundry boundary", src=src("pub", "priv"))
    row(cv, 0, y2, [c1, c2, c3, c4], gap=G)
    n.place(cv, X(4), y2)
    return max(c1.bottom, c2.bottom, c3.bottom, c4.bottom, n.bottom)


# ================================================================================================ band 5: private network + troubleshooting
def band_private(cv: Canvas, y: float) -> float:
    y = head(cv, y, "5  Private networks and authorization: the two things that go wrong",
             "A project with public network access disabled needs a scoped exception for the Activity route; a user who can open the agent may still be refused. Both have documented fixes.")
    top = y
    GAP_A = 170
    BX = 330 + GAP_A
    with cv.panel(BX, top, title="Foundry public service endpoint", sub="Activity Protocol route only; Foundry terminates TLS", theme="green", style="solid", fill="soft",
                  pad=20, title_size=24, sub_size=15, w=980) as pb:
        b1 = Box(940, "3  Source-IP check", sub="Azure Bot Service and Microsoft 365 ranges kept by Foundry; an absent, malformed or outside address is denied (fail closed)",
                 theme="indigo", h=104, size=18, sub_size=14, fill="hatch")
        b2 = Box(940, "4  Authenticate and authorize", sub="signed channel token validated against the agent identity, then BotServiceRbac or BotServiceTenant (tenant and RBAC checks)",
                 theme="red", h=104, size=18, sub_size=14, fill="hatch")
        b1.place(cv, pb.ix, pb.iy)
        b2.place(cv, pb.ix, b1.bottom + 44)
        connect(cv, b1, b2, a_side="bottom", b_side="top", sw=3)
    CX = BX + 980 + GAP_A
    with cv.panel(CX, top, title="Project: public network access disabled", sub="private endpoint; every other route stays private", theme="indigo", style="dotted",
                  pad=20, title_size=22, sub_size=15, w=S(4) - CX, min_h=pb.h) as pc:
        v = Box(S(4) - CX - 40, "Active agent version", sub="the version the stable endpoint serves", theme="green", h=96, size=19, sub_size=14, fill="hatch", icon="agent",
                icon_pos="left", icon_size=32)
        v.place(cv, pc.ix, pc.iy)
        cv.text(pc.ix, v.bottom + 20, "Still private:", size=16, color=MUTED)
        ChipFlow([Chip(t, theme="indigo", size=15, fill="soft") for t in ("Management APIs", "Responses", "Invocations", "A2A", "MCP")], S(4) - CX - 40, gap=8).place(cv, pc.ix, v.bottom + 46)
    A = Box(330, "Microsoft 365 and Teams channel infrastructure", sub="Copilot and Teams adapters", theme="gray", icon="teams", icon_pos="top", h=180, size=18,
            sub_size=14, fill="hatch")
    A.place(cv, 0, pb.cy - 90)
    arrow(cv, [(A.right + 8, pb.cy), (pb.x - 8, pb.cy)], color="#2b8a3e", sw=3, label="1 and 2  HTTPS over the public internet to the Activity route", label_size=14,
          label_wrap=GAP_A - 24, end_head="arrow")
    arrow(cv, [(pb.right + 8, pb.cy), (pc.x - 8, pb.cy)], color="#2b8a3e", sw=3, label="5  route to the active version; the reply returns through the channel", label_size=14,
          label_wrap=GAP_A - 24, end_head="arrow")
    cy = pb.bottom + 26
    cf = ChipFlow([Chip(t, theme="green", size=15, fill="soft") for t in (
        "No Private Link: the channel uses the public route", "No public IP, DNS record, DNAT rule, load balancer or proxy for you", "Foundry maintains the source ranges",
        "Outbound rules for your agent are unchanged")], S(4), gap=10)
    cf.place(cv, 0, cy)
    cv.text(0, cf.y + cf.h + 8, "Learn: Publish agents by using the REST API (private network option)", size=12, color=LINK, link=U["vnet"][1])
    left_bottom = cf.y + cf.h + 28

    rx, rw = S(4) + G, S(2)
    c1 = card(rw, "What enable_m365_public_endpoint does", [
        "Set agent_endpoint.protocol_configuration.activity.enable_m365_public_endpoint to true",
        "Adds a service-managed, source-IP-filtered public path to the Activity route only; Responses, Invocations, A2A, MCP and management APIs stay private",
        "No public access on the Foundry account and no public ingress in your virtual network",
        "It changes reachability, not authorization: keep a Bot Service scheme configured. With public access allowed it is not needed",
    ], theme="indigo", icon="private-link", src=src("vnet", "netw"))
    c1.place(cv, rx, top)
    n1 = Note(rw, "Microsoft 365 does not support private connectivity for agents, so the channel needs a public route. The source-IP check is defense in depth, not proof of identity: "
                  "the ranges are shared across tenants, so token validation and the scheme still decide.", kind="gotcha", title="Public reachability is not anonymous access", src=src("vnet"))
    n1.place(cv, rx, c1.bottom + 22)
    right_bottom = n1.bottom

    y2 = max(left_bottom, right_bottom) + 44
    st = Steps(S(3), "REST route in five steps (run from a client that can reach the project's private endpoint)", [
        "Get a bearer token for https://ai.azure.com, GET the agent and copy instance_identity.client_id (principal_id is not used); note your tenant ID",
        "Create an Azure Bot Service with Bicep: kind azurebot, location global, msaAppId = the agent identity client ID, SingleTenant, publicNetworkAccess Disabled, "
        "Teams channel; its endpoint is .../agents/<agent>/endpoint/protocols/activityProtocol?api-version=v1",
        "PATCH the agent: set enable_m365_public_endpoint to true and add BotServiceRbac or BotServiceTenant. The PATCH replaces protocol_configuration and "
        "authorization_schemes, so resend responses and AzureRbac (or Entra)",
        "POST .../agents/<agent>/microsoft365/publish with botServiceArmId and publishScope (Shared or Tenant)",
        "Review the network path, then verify: find the agent in the store, send a message and confirm a reply",
    ], theme="indigo", num_theme="indigo", size=15, src=src("vnet"))
    st.place(cv, 0, y2)
    code = CodeBlock(S(3), [
        "PATCH {endpoint}/agents/{agent}?api-version=v1",
        "Content-Type: application/merge-patch+json",
        "",
        "{",
        '  "agent_endpoint": {',
        '    "protocol_configuration": {',
        '      "responses": {},',
        '      "activity": { "enable_m365_public_endpoint": true }',
        "    },",
        '    "authorization_schemes": [',
        '      { "type": "AzureRbac" },',
        '      { "type": "BotServiceRbac" }',
        "    ]",
        "  }",
        "}",
    ], title="Step 3 body (illustrative): resend every protocol and scheme you keep", theme="indigo", src=src("vnet"))
    code.place(cv, S(3) + G, y2)
    y3 = max(st.bottom, code.bottom) + 56

    # ---- troubleshooting tree
    cv.text(0, y3, "Fix an authorization error: the agent opens, the call is refused", size=26, color=THEMES["red"].deep)
    cv.text(0, y3 + 36, "Learn: Troubleshoot authorization errors for agents published to Microsoft Copilot and Teams", size=12, color=LINK, link=U["tauth"][1])
    ty = y3 + 64
    BW = 1810
    BXX = W - BW
    br_a = Steps(BW, "Everyone in the tenant: switch the endpoint to BotServiceTenant", [
        "Publish at tenant scope first: People in your organization (portal) or publishScope Tenant (REST)",
        "A Microsoft 365 admin approves the request in the Microsoft 365 admin center; the agent then shows under Built by your org",
        "GET the agent and its authorization_schemes, then PATCH: keep Entra and any other non-Bot scheme, replace BotServiceRbac with BotServiceTenant (the PATCH replaces the array; never both Bot schemes)",
        "A user in the tenant starts a new conversation and sends a message",
    ], theme="green", num_theme="green", size=15, src=src("tauth"))
    br_b = card(BW, "Only selected users: grant Foundry Agent Consumer", [
        "Assign the built-in role Foundry Agent Consumer (definition ID eed3b665-ab3a-47b6-8f48-c9382fb1dad6)",
        "Project scope: access to every agent endpoint in the project. Agent scope (.../projects/<project>/agents/<agent>): that one endpoint only",
        "You need permission to create role assignments at that scope; use Azure CLI for project- or agent-scoped assignments",
        "Assignments take several minutes to propagate; then the user starts a new conversation",
        "Replacing a scheme changes endpoint authorization only; it never changes where the agent appears in the store",
    ], theme="red", icon="managed-identity", src=src("tauth"))
    br_a.place(cv, BXX, ty)
    br_b.place(cv, BXX, br_a.bottom + 36)
    ym = (br_a.y + br_b.bottom) / 2
    start = Box(500, "A user finds the agent in Copilot or Teams but gets an authorization or insufficient-permissions error", theme="red", fill="hatch", size=17, h=190)
    why = Box(600, "Store visibility is not endpoint authorization. Just you (Shared) uses BotServiceRbac, so each user needs an Azure role that lets them invoke the endpoint.",
              theme="orange", fill="hatch", size=17, h=190)
    dec = Box(400, "Who should be able to call it?", shape="diamond", theme="green", fill="hatch", size=18, h=240)
    start.place(cv, 0, ym - start.h / 2)
    why.place(cv, 590, ym - why.h / 2)
    dec.place(cv, 1280, ym - dec.h / 2)
    arrow(cv, [(start.right + 8, ym), (why.x - 8, ym)], sw=3, end_head="arrow")
    arrow(cv, [(why.right + 8, ym), (dec.x - 8, ym)], sw=3, end_head="arrow")
    midx = (dec.right + BXX) / 2
    arrow(cv, [(dec.right + 6, ym), (midx, ym), (midx, br_a.cy), (BXX - 8, br_a.cy)], sw=3, color="#2b8a3e", end_head="arrow")
    arrow(cv, [(dec.right + 6, ym), (midx, ym), (midx, br_b.cy), (BXX - 8, br_b.cy)], sw=3, color="#c92a2a", end_head="arrow")
    return br_b.bottom


# ================================================================================================ band 6: troubleshooting
def band_trouble(cv: Canvas, y: float) -> float:
    y = head(cv, y, "6  Troubleshooting: symptom, cause, fix",
             "The rows of the troubleshooting page that come up most; the page has more. Authorization errors have their own decision tree at the end of section 5.")
    top = y
    TW = S(3)
    ta = Table([("When you publish", 520), ("Cause", 480), ("Fix", 776)], [
        ["Validation error: AppVersion not digits and periods, or starting with 0; developer name over 32 characters; description over 4,000; website not https; missing botServiceArmId or publishScope",
         "The metadata, version or a required field is invalid", "Fix the field the error names and retry. Version: digits and periods, not starting with 0. publishScope: Personal, Shared or Tenant"],
        ["'App version already exists'", "You republished an existing appVersion", "Increment appVersion. To change agent behavior, change the agent version that receives traffic instead"],
        ["Icon rejected: not base64, not a PNG, not 192x192", "The icon fails the format or size rules", "A 192x192 color PNG and a 32x32 outline PNG, base64-encoded, within the size limit"],
        ["Download ZIP gives no package, or the package API returns 400", "The request or generated manifest failed validation; an unvalidated package is never returned", "Correct the field the error names and call again"],
        ["Teams rejects a package that downloaded fine", "A required file, generated ID or manifest section changed after download", "Download again; edit only supported user-facing metadata and assets"],
        ["Package API 401, 403 or 429", "Bad token, no agent write permission, wrong endpoint, or throttling", "Token for https://ai.azure.com, Foundry User (or equivalent agent write permission), the project endpoint; for 429 wait for Retry-After"],
        ["Azure Bot Service creation fails, or 403 AuthorizationFailed on Microsoft.BotService/botServices/write", "No permission in the resource group, or the Microsoft.BotService provider is not registered",
         "Azure Bot Service Contributor (or Contributor or Owner) on the resource group; register the provider; retry"],
        ["Identity error, agent.identity is null, or the portal says the older format cannot be published", "A legacy agent application has no unique identity",
         "Migrate the agent application to the new agent model, then publish; existing legacy agents keep working"],
    ], w=TW, theme="gray", size=14, head_size=15, title="Publish and package errors", title_size=22, first_col_theme="gray")
    ta.place(cv, 0, top)
    tb = Table([("After you publish", 500), ("Cause", 470), ("Fix", 806)], [
        ["Not in the store right after publishing; or not in the section you expect", "The store cache refreshes about hourly; organization scope may await approval; scope decides the section",
         "Just you: clear the store cache or sign out and in; it lives under Your agents. Organization: confirm approval in the Microsoft 365 admin center; it lives under Built by your org"],
        ["Stuck conversation, no response, or 'no tool output found'", "The conversation locked after a tool error",
         "Reset it: start a new chat in Microsoft Copilot; in Teams send /foundry_new_preview. The previous conversation cannot be restored"],
        ["Insufficient permissions or authorization error", "BotServiceRbac, and the user cannot invoke the endpoint", "Follow the decision tree at the end of section 5"],
        ["Works in the playground, fails after publishing; or authentication errors at run time", "The agent identity lacks roles on the Azure resources it uses, or the agent identity application is disabled",
         "Assign the required roles to the agent identity for each resource; check the identity is enabled"],
        ["MCP approval not given; tool calls fail on licenses; sign-in card will not complete", "A tool approval was dismissed; licenses or service plans are missing; a firewall blocks the Foundry redirect domain",
         "Approve in the chat or start a new one; assign the licenses and service plans; allow outbound HTTPS on TCP 443 to *.azureml.ms"],
        ["Rate limit, prompt too large, 'another response in progress', or a file upload fails (invalid_file)", "Capacity or context window exceeded; a response is still running; the file is unsupported, corrupted or protected",
         "Wait and retry, add capacity, or start a new conversation; send a supported, unprotected copy. If it persists give support the ConversationId, activityId and ms-cv"],
        ["Private network: portal publish returns 403; the channel gets 403 NetworkAccessDenied; Activity requests are rejected",
         "Public access is off; enable_m365_public_endpoint is omitted or false; the source IP is outside the allowed ranges; no Bot Service scheme, or the user is outside the project's tenant",
         "Use the REST route from a client that reaches the private endpoint; set the setting to true; test through Copilot or Teams; configure BotServiceRbac or BotServiceTenant. Guest users cannot use these agents"],
    ], w=TW, theme="gray", size=14, head_size=15, title="Store, run-time and private-network issues", title_size=22, first_col_theme="gray")
    tb.place(cv, TW + G, top)
    ny = max(ta.bottom, tb.bottom) + 18
    cite(cv, 0, ny, src("tshoot"))
    ny += 36
    n1 = Note(S(3), "End users do not need a Microsoft 365 Copilot license to use a published agent in Microsoft Copilot Chat. Without one, usage that reaches shared tenant data such as "
                    "SharePoint or Copilot connectors might incur usage-based charges.", kind="info", title="Licenses for end users", src=src("tshoot"))
    n2 = Note(S(3), "The portal cannot publish from a project that disables public network access. The troubleshooting page also lets you download the manifest .zip and create the agent from it "
                    "in the Microsoft 365 admin center.", kind="tip", title="Another way around the portal limit", src=src("tshoot"))
    row(cv, 0, ny, [n1, n2], gap=G)
    return ny + max(n1.h, n2.h)


# ================================================================================================ band 7: REST + other channels
def band_rest(cv: Canvas, y: float) -> float:
    y = head(cv, y, "7  The REST operations and the other ways in",
             "'Agent Microsoft 365 Publishing' has three operations. Incoming A2A, telephony bindings and the legacy Agent application model complete the channel list. All docs conflicts for both parts are collected at the end of part 2.")
    top = y
    LW = S(4)
    t1 = Table([("Operation", 230), ("Route (api-version is required)", 760), ("What it does", 820), ("Notes", 574)], [
        [ct("Publish", "green"), "POST /agents/{agent_name}/microsoft365/publish",
         "Publishes the agent to Microsoft 365 and Teams; a successful response returns the published title ID (titleId) and the Teams app ID (teamsAppId)",
         "Needs Foundry User on the project and the Bot Service permissions; re-posting an existing appVersion fails with 'version already exists'"],
        [ct("Publish defaults", "teal"), "GET /agents/{agent_name}/microsoft365/publishdefaults",
         "Returns default and previously published values to pre-fill a request: scope, display name, appVersion and recommendedNextAppVersion, titleId, teamsAppId, botServiceArmId, descriptions, URLs",
         "The publishAsDigitalWorker query flag returns the defaults for publishing as an autopilot"],
        [ct("App package", "gray"), "POST /agents/{agent_name}/microsoft365/zip",
         "Builds the Teams app package (application/zip) from the same body, without publishing or creating a publish record",
         "Needs agent write permission and may update the endpoint configuration it requires; a validation failure returns the error, not a ZIP"],
    ], w=LW, theme="green", size=14, head_size=15, title="REST group: Agent Microsoft 365 Publishing", title_size=22)
    t1.place(cv, 0, top)
    t2 = Table([("Body field", 330), ("Meaning", 1000), ("Constraint", 1054)], [
        [ct("publishScope", "green"), "The publish scope of the generated Teams app (required)", "Personal, Shared or Tenant; Personal is treated as Shared"],
        ["agentDisplayName", "Name shown in Teams and Microsoft Copilot", "Optional; defaults to the agent name from the route"],
        ["botServiceArmId", "ARM resource ID of the Azure Bot Service that fronts the agent", "Required on the default bot-based backend; optional on the API-based backend; must not be sent with publishAsAutopilot"],
        ["appVersion", "Version written into the Teams manifest, for example 1.2.3", "Digits and periods only; must not start with 0; must end with a digit; republishing an existing version fails"],
        ["shortDescription, fullDescription", "Text for the app listing and the details page", "Optional in REST"],
        ["developerName, developerWebsiteUrl, privacyUrl, termsOfUseUrl", "Developer metadata shown in the listing", "developerWebsiteUrl must be https; privacyUrl may be http or https"],
        ["colorIconBase64, outlineIconBase64", "Custom icons as base64 PNG", "Color 192x192 with no border or rounded corners; outline 32x32; each at most 1 MB after decode; platform defaults if omitted"],
        ["canRespondWithoutMention", "true: respond to all messages on its Teams surfaces; false: only when @mentioned", "Optional; left unchanged when omitted"],
        [ct("publishAsAutopilot", "grape"), "Publish as an autopilot (digital worker): the bot ID comes from the blueprint identity", "Hosted agents only (part 2); the manifest is marked as a digital worker"],
        [ct("accessBoundaries[], optionalPermissionScopes[]", "grape"), "Autopilot only: Activity protocol access boundaries; delegated permission scopes granted to the blueprint",
         "An empty accessBoundaries list clears the existing ones; optionalPermissionScopes only with publishAsAutopilot; mandatory platform permissions are always granted"],
    ], w=LW, theme="green", size=14, head_size=15, title="Request body (publish and package share it)", title_size=22)
    t2.place(cv, 0, t1.bottom + 40)
    cv.text(0, t2.bottom + 8, "Learn: REST publish operation", size=12, color=LINK, link=U["rpub"][1])
    cv.text(250, t2.bottom + 8, "Learn: REST publish defaults", size=12, color=LINK, link=U["rdef"][1])
    cv.text(500, t2.bottom + 8, "Learn: REST app package", size=12, color=LINK, link=U["rzip"][1])
    rx, rw = LW + G, S(2)
    n1 = Note(rw, "The portal and private-network pages show api-version=v1; the autopilot quickstart shows api-version=2025-11-15-preview. The migrate page says there is no public "
                  "publish API, yet the REST reference lists these three operations. Check the live reference for the version you target before you automate.",
              kind="warn", title="Docs disagree: api-version and publish API", src=src("vnet", "mig", "rpub"))
    n1.place(cv, rx, top)
    n2 = Note(rw, "The API says digital worker where the docs say autopilot: publishAsDigitalWorker on the defaults query, and a manifest 'marked as a digital worker'.",
              kind="info", title="Same thing, two words", src=src("rdef", "rzip"))
    n2.place(cv, rx, n1.bottom + 22)
    n3 = Note(rw, "Portal publish calls this same API. The portal's Download ZIP is the package operation: same validation, no publish record.",
              kind="tip", title="Portal = REST", src=src("pub"))
    n3.place(cv, rx, n2.bottom + 22)

    y2 = max(t2.bottom + 36, n3.bottom) + 44
    w3 = S(2)
    a2a = card(w3, "Incoming A2A endpoint (Preview)", [
        "Enable it by PATCHing the agent: an agent card plus the a2a protocol on the endpoint",
        "Entra authorization only: callers need Foundry Agent Consumer",
        "A2A v0.3 is the default if you do not specify a version; the docs list v1.0 as GA and v0.3 as preview",
        "Tasks are retained for 60 days",
        "! Docs disagree on hosted agents: the enable page describes prompt agents only, the hosted-agents concept lists a2a as a hosted protocol",
        "Full sequence and the six authentication methods: the 'Multi-agent orchestration in depth' canvas",
    ], theme="green", icon="a2a", badge="preview", src=src("a2a", "conf"))
    tel = card(w3, "Telephony bindings (voice agents, Preview)", [
        "A voice agent's Channels tab offers a Preview web app and Phone numbers",
        "Phone numbers: Teams Phone extensibility, Twilio or Direct SIP",
        "REST: .../telephony/bindings creates and manages a binding",
        "The standard Teams and Microsoft 365 publishing card is hidden for voice agents",
        "! Direct SIP: the overview says it is not a supported customer flow; the SIP page documents it as Preview",
        "Details: the 'Voice agents' canvases",
    ], theme="teal", icon="speech", badge="preview", src=src("vpub", "vtel"))
    leg = card(w3, "Legacy Agent applications", [
        "ARM resources: applications + agentdeployments; one active deployment takes 100% of traffic",
        "One protocol per application; stateless Responses at /applications/{app}/protocols/openai",
        "Publishing needs Foundry Project Manager; the publisher pays; not in the Entra Agent Registry",
        "New model: the agent object has an endpoint and identity from creation. Both models coexist; deprecation is planned, with no end-of-support date yet",
        "Assign client roles at project scope; there is no in-place identity upgrade yet",
    ], theme="gray", icon="app-registrations", badge="classic", src=src("apps", "mig"))
    row(cv, 0, y2, [a2a, tel, leg], gap=G)
    return max(a2a.bottom, tel.bottom, leg.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Publishing and channels",
        "A stable endpoint with its own Entra identity -> Microsoft 365 Copilot, Teams, other agents, phones, routines and Agent 365  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Identity and security", "red"), ("Tools and MCP", "orange"), ("Voice and speech", "teal"),
                           ("Networking", "indigo"), ("Observability and triggers", "violet"), ("Governance and Agent 365", "grape"), ("Cost and licenses", "yellow"),
                           ("Channels and neutral", "gray")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Foundry Agent Service: the map", "Prompt agents in depth", "Hosted agents: your code on Foundry's runtime", "Agent identity and delegation",
                "Workflows, routines, A2A and multi-agent orchestration", "Voice agents (Preview): architecture, definition and telephony", "Foundry Control Plane"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    y = band_tiles(cv, y) + 50
    y = band_map(cv, y) + 50
    y = band_auth(cv, y) + 50
    y = band_identity(cv, y) + 50
    y = band_publish(cv, y) + 50
    y = band_private(cv, y) + 50
    y = band_trouble(cv, y) + 50
    y = band_rest(cv, y) + 50
    sources(cv, 0, y, [
        ("Publish agents to Microsoft Copilot and Microsoft Teams", U["pub"][1]), ("Publish agents by using the REST API (private network)", U["vnet"][1]),
        ("Troubleshoot publishing agents to Microsoft Copilot and Teams", U["tshoot"][1]), ("Troubleshoot authorization errors for published agents", U["tauth"][1]),
        ("Configure your agent endpoint and settings", U["conf"][1]), ("Agent endpoint authorization", U["auth"][1]),
        ("Configure agent endpoint authorization", U["cauth"][1]), ("Agent identity", U["ident"][1]), ("Identity and access in Agent Service", U["idov"][1]),
        ("Enable the agent-to-agent endpoint", U["a2a"][1]), ("Migrate from Agent applications", U["mig"][1]),
        ("Microsoft Agent 365 integration", U["a365"][1]), ("REST: publish an agent to Microsoft 365", U["rpub"][1]),
        ("Role-based access control for Microsoft Foundry", U["rbac"][1]),
    ], w=W, cols=4)
