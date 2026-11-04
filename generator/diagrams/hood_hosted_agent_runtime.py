"""Hosted agents runtime under the hood - how a container becomes an agent endpoint (Micro VM cut-away).

Evidence convention used on this canvas (keep it honest):
  solid border + hatch  = documented on Microsoft Learn
  dashed border + soft  = only a video / blog / repo says it (labelled "(video/blog)")
  dotted grey + "?"     = not documented anywhere checked
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hood-hosted-agent-runtime",
    title="Hosted agent runtime: how a container becomes an agent endpoint",
    section="8", order=2,
    description="Cut-away of the per-session Micro VM sandbox and the platform layers around it - build and provision, "
                "runtime contract, session lifecycle, identity, egress proxy, networking and crash recovery - with "
                "documented, video/blog-only and not-documented facts drawn differently.",
    tags=["hosted-agents", "microvm", "sandbox", "sessions", "runtime", "isolation"],
)

W = 3300
GREY = "#868e96"

# --------------------------------------------------------------------------- Learn / evidence URLs
L_HOSTED = learn("agents/concepts/hosted-agents")
L_CONTRACT = learn("agents/concepts/hosted-agent-contract")
L_TOKEN = learn("agents/concepts/hosted-agent-token-service")
L_IDENT = learn("agents/concepts/agent-identity")
L_PERMS = learn("agents/concepts/hosted-agent-permissions")
L_NETDEEP = learn("agents/concepts/agents-networking-deep-dive")
L_SESS = learn("agents/how-to/manage-hosted-sessions")
L_ISO = learn("agents/how-to/isolate-sessions-per-user")
L_DEPLOY = learn("agents/how-to/deploy-hosted-agent")
L_CODE = learn("agents/how-to/deploy-hosted-agent-code")
L_LIMITS = learn("agents/concepts/limits-quotas-regions")
L_STATE = learn("agents/concepts/agent-state-store")
L_RESIL = learn("agents/concepts/long-running-agent-resilience")
L_RESREF = learn("agents/concepts/long-running-agent-reference")
L_EGRESS = learn("agents/how-to/add-hosted-agent-guardrails")
L_LOGS = learn("agents/how-to/monitor-hosted-agent-logs")
L_OTEL = learn("agents/how-to/configure-hosted-agent-telemetry")
L_ENTRA_ING = learn("observability/how-to/trace-ingestion-entra-authentication")
L_CMK = learn("concepts/customer-managed-keys")
L_MIGRATE = learn("agents/how-to/migrate-hosted-agent-preview")
L_ENDPOINT_AUTH = learn("agents/concepts/agent-endpoint-authorization")

U_BLOG = "https://devblogs.microsoft.com/foundry/introducing-the-new-hosted-agents-in-foundry-agent-service-secure-scalable-compute-built-for-agents/"
U_BLOG_BUILD = "https://devblogs.microsoft.com/foundry/hosted-agents-build26/"
U_MAF_BLOG = "https://devblogs.microsoft.com/agent-framework/foundry-hosted-agent-isolation-with-microsoft-agent-framework/"
U_MECH = "https://www.youtube.com/watch?v=iR7_57lJOz8"
U_REACTOR = "https://www.youtube.com/watch?v=8N7q0Ucr3rw"
U_BRK243 = "https://www.youtube.com/watch?v=e_ZJy3RsNkg"
U_BRK241 = "https://www.youtube.com/watch?v=_8UKz197JuM"
U_PATTERNS = "https://github.com/microsoft/agenticai-design-patterns/blob/main/assets/agent-runtime/production-hosted-agents-on-foundry/docs/architecture.md"
U_GA = "https://azure.microsoft.com/en-us/blog/gpt-5-6-now-available-in-microsoft-foundry/"
U_ACA_SESS = "https://learn.microsoft.com/en-us/azure/container-apps/sessions"


# =========================================================================== evidence-styled blocks
def _retag(card: Card, prefix) -> Card:
    """Card.src lines always read 'Learn: ...'; relabel them for video / blog / repo evidence (str or one per line)."""
    prefixes = [prefix] * len(card.src_lines) if isinstance(prefix, str) else list(prefix)
    card.src_lines = [(t.replace("Learn: ", f"{p}: ", 1), u, y) for (t, u, y), p in zip(card.src_lines, prefixes)]
    return card


def vb(w, title, body, *, theme="yellow", src=(), prefix="Video", **kw) -> Card:
    """Video / blog / repo only: dashed border, soft fill, '(video/blog)' in the title."""
    c = Card(w, "(video/blog) " + title, body, theme=theme, dash="dashed", fill="soft", src=src, **kw)
    return _retag(c, prefix)


def nd(w, title, body, **kw) -> Card:
    """Not documented: dotted grey, empty fill, '?' in the title."""
    body = [("para", b) for b in ([body] if isinstance(body, str) else body)]
    kw.setdefault("title_color", GREY)
    return Card(w, "? " + title, body, theme="gray", dash="dotted", fill="none", body_color=MUTED, **kw)


def tile(cv: Canvas, x, y, w, h, big, caption, theme, kind="doc") -> None:
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


def evidence_legend(cv: Canvas, x: float, y: float) -> float:
    cx = x
    for kind, label in (("doc", "Solid + hatch: documented on Microsoft Learn"),
                        ("vb", "Dashed + soft, tagged (video/blog): only a video, blog or repo says so"),
                        ("nd", "Dotted grey ?: not documented anywhere I could find")):
        if kind == "doc":
            cv.rect(cx, y, 64, 34, stroke="#2f9e44", fill="#b2f2bb", style="hachure", sw=2)
        elif kind == "vb":
            cv.rect(cx, y, 64, 34, stroke="#f08c00", fill="#fff9db", style="solid", sw=2, dash="dashed")
        else:
            cv.rect(cx, y, 64, 34, stroke=GREY, fill="transparent", sw=2, dash="dotted")
            cv.text(cx + 24, y + 3, "?", size=26, color=GREY)
        t = cv.text(cx + 78, y + 5, label, size=17)
        cx += 78 + t.w + 56
    draw_badge(cv, cx, y + 4, "preview")
    t = cv.text(cx + 82, y + 5, "Preview feature (check Learn before relying on it)", size=17)
    cx += 82 + t.w + 56
    cv.text(cx, y + 5, "Time-sensitive facts carry: as of 2026-11-03", size=17, color="#c92a2a")
    return y + 46


# =========================================================================== arrows with tidy labels
def harrow(cv: Canvas, x1, x2, y, *, num=None, label=None, dash="solid", color=INK, size=14, label_cx=None,
           label_w=None, num_theme="green", sw=2, num_x=None, start_head=None) -> None:
    """Horizontal arrow x1 -> x2 at height y: label sits above the line, a step circle sits on it."""
    arrow(cv, [(x1, y), (x2, y)], dash=dash, color=color, sw=sw, end_head="arrow", start_head=start_head)
    d = 1 if x2 >= x1 else -1
    if num is not None:
        numbered(cv, num_x if num_x is not None else x1 + d * 26, y, num, theme=num_theme, d=28, size=15)
    if label:
        txt = "\n".join(wrap_text(label, label_w, size)) if label_w else label
        tw, th_ = text_size(txt, size)
        lc = label_cx if label_cx is not None else (x1 + x2) / 2
        cv.text(lc - tw / 2, y - th_ - (22 if num is not None else 7), txt, size=size, color=INK, align="center", w=tw)


def varrow(cv: Canvas, x, y1, y2, *, num=None, label=None, dash="solid", color=INK, size=14, num_theme="green",
           label_w=None, sw=2) -> None:
    arrow(cv, [(x, y1), (x, y2)], dash=dash, color=color, sw=sw, end_head="arrow")
    d = 1 if y2 >= y1 else -1
    if num is not None:
        numbered(cv, x, y1 + d * 24, num, theme=num_theme, d=28, size=15)
    if label:
        txt = "\n".join(wrap_text(label, label_w, size)) if label_w else label
        tw, th_ = text_size(txt, size)
        cv.text(x + 22, (y1 + y2) / 2 - th_ / 2, txt, size=size, color=INK, w=tw)


class Steps(Rect2):
    """A card whose rows carry the same numbered circles used on the diagram (the legend for the markers)."""

    def __init__(self, w, title, steps, *, theme="green", size=15, pad=16, d=28, src=(), title_size=20):
        self.th = THEMES[theme]
        self.theme, self.w, self.title, self.size, self.pad, self.d, self.title_size = (
            theme, w, title, size, pad, d, title_size)
        lr = metrics.line_ratio()
        tw = (w - 2 * pad - d - 12) * 0.965
        y = pad + title_size * lr + 10
        self.rows = []
        for n, text in steps:
            lines = wrap_text(text, tw, size)
            h = max(len(lines) * size * lr, d)
            self.rows.append((n, lines, y, h))
            y += h + 9
        y -= 9
        self.src_lines = []
        if src:
            y += 8
            for label, url in src:
                lines = wrap_text(f"Learn: {label}", w - 2 * pad, 12)
                self.src_lines.append(("\n".join(lines), url, y))
                y += len(lines) * 12 * lr + 2
            y -= 2
        self.h = y + pad
        self.x = self.y = 0.0
        self.rect_el = None

    def place(self, cv: Canvas, x: float, y: float, h=None) -> "Steps":
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        lr = metrics.line_ratio()
        with cv.group():
            self.rect_el = cv.rect(x, y, self.w, H, stroke=self.th.stroke, fill=self.th.fill, style="hachure", sw=2)
            cv.text(x + self.pad, y + self.pad, self.title, size=self.title_size, color=self.th.deep)
            for n, lines, ry, rh in self.rows:
                numbered(cv, x + self.pad + self.d / 2, y + ry + self.d / 2, n, theme=self.theme, d=self.d, size=15)
                th_ = len(lines) * self.size * lr
                cv.text(x + self.pad + self.d + 12, y + ry + (rh - th_) / 2, "\n".join(lines), size=self.size)
            for txt, url, sy in self.src_lines:
                cv.text(x + self.pad, y + sy, txt, size=12, color=LINK, link=url)
        cv.register(f"steps:{self.title}", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return self.rect_el


# =========================================================================== band 1: container -> endpoint
def band_pipeline(cv: Canvas, y: float) -> float:
    _, hb = section_header(cv, 0, y, "From container to endpoint: what happens between azd up and a live agent URL",
                           sub="Build and register, create a version (= provision), identity and endpoint appear, "
                               "then the first request creates a session",
                           size=32, w=W)
    top = hb + 28
    cw = 440
    gap = (W - 6 * cw) / 5
    cards = [
        Card(cw, "A  Package", [
            "Container image: linux/amd64 only, pushed to Azure Container Registry; use unique tags, not :latest",
            "Or a source zip: runtime python_3_13, python_3_14 or dotnet_10, plus an entry_point",
            "Python and C#; any framework (Agent Framework, LangGraph, OpenAI Agents SDK, custom)",
        ], theme="gray", icon="code", src=[("Deploy a hosted agent", L_DEPLOY)]),
        Card(cw, "B  Registry", [
            "azd builds remotely in ACR by default; remoteBuild: false uses local Docker",
            "Bring your own registry is supported",
            "Private (network-secured) ACR only for projects created after 2026-06-25; older projects need a public endpoint",
        ], theme="cyan", icon="acr", src=[("Hosted agents: private networking", L_HOSTED)]),
        Card(cw, "C  Create a version", [
            "Every call makes an immutable version: image or code, cpu + memory, env vars, protocol config, idle timeout",
            "Max 1,000 versions per agent",
            "There is no separate start step: creating the version provisions the agent",
        ], theme="green", icon="versions", src=[("Hosted agents: versioning", L_HOSTED)]),
        Card(cw, "D  Provision", [
            "The platform pulls the image with the project managed identity and builds a container snapshot",
            "Status: creating -> active (or failed)",
            "Typically under one minute, depending on image size",
        ], theme="green", icon="vm", src=[("Deploy a hosted agent", L_DEPLOY)]),
        Card(cw, "E  Identity and endpoint", [
            "A dedicated Entra agent identity is created - with no permissions yet",
            "Implicit access only: model inference through the project endpoint, and session storage",
            "A dedicated endpoint per agent: /responses, /invocations, WebSocket, /a2a",
        ], theme="red", icon="managed-identity", src=[("Agent identity", L_IDENT)]),
        Card(cw, "F  Serve sessions", [
            "The first request creates a session: a Micro VM is provisioned and your container started",
            "Compute follows the session, not the request",
            "Each session is bound to one version when it is created",
        ], theme="green", icon="agent", src=[("Manage hosted sessions", L_SESS)]),
    ]
    r, b = row(cv, 0, top, cards, gap=gap)
    labels = ["docker push or azd up", "create_version", "pull + snapshot", "created at deploy", "first request"]
    for i, lab in enumerate(labels):
        mx = cards[i].right + gap / 2
        harrow(cv, cards[i].right + 6, cards[i + 1].x - 6, top + 70, label=lab, label_w=gap - 24, label_cx=mx)

    # ---- details row (4 columns)
    y2 = b + 44
    t_pack = Table(
        [("Path", 140), ("Set on the version", 250), ("What you ship", 450), ("What the platform does", 420)],
        [
            [("Container image", "gray"), "container_configuration.image",
             "Full ACR URL and tag; linux/amd64 only; unique tags, not :latest",
             "Pulls it with the project managed identity (Container Registry Repository Reader) and builds a container snapshot"],
            [("Source zip", "gray"), "code_configuration: runtime, entry_point, dependency_resolution",
             "remote_build (default): the platform installs requirements.txt or restores .NET during provisioning. "
             "bundled: the zip runs as-is with prebuilt Linux dependencies",
             "Runs it on a platform-built image for the runtime value; verifies the SHA-256; the zip can be downloaded for audit"],
        ], theme="gray", size=14, head_size=15, title="Two packaging paths - mutually exclusive per version",
        title_size=22)
    t_pack.place(cv, 0, y2)
    n_net = Note(t_pack.w, "Source-code deploys inside a private VNet need outbound access to mcr.microsoft.com and "
                           "*.login.microsoft.com during provisioning. With Agent 365 data collection on, also "
                           "agent365.svc.cloud.microsoft (TCP 443), plus the Application Insights endpoints.",
                 kind="info", title="Provisioning-time egress", src=[("Deploy from source code", L_CODE)])
    n_net.place(cv, 0, t_pack.bottom + 26)
    cx = t_pack.right + 40
    c_ver = Card(640, "Version lifecycle", [
        "Version status: creating -> active | failed -> deleting -> deleted",
        "Poll until active before you invoke",
        "Env vars, cpu + memory, protocol config and the idle timeout are frozen per version",
        "Each session is bound to one version when created; pin it with version_indicator (a concrete version, not @latest)",
        "Environment variables are per version, immutable, and are the way to configure the container",
    ], theme="green", icon="versions", src=[("Hosted agents: versioning", L_HOSTED), ("Manage sessions", L_SESS)])
    c_ver.place(cv, cx, y2)
    c_id = Card(640, "Two identities, two jobs", [
        "Project managed identity: platform operations such as the ACR image pull. Never available to your code",
        "Agent identity (per agent): what your code runs as for models, tools and Azure resources",
        "A new agent identity has no permissions: assign RBAC to it for Storage, Search and so on",
        "! The Azure AI Developer role is not enough for hosted agents (it targets Azure ML and Foundry hubs); use Foundry User or higher",
    ], theme="red", icon="managed-identity", src=[("Hosted agent permissions", L_PERMS)])
    c_id.place(cv, cx + 640 + 40, y2)
    n_split = Note(W - (cx + 1320), "The concept page says an endpoint serves one version and traffic splitting is not "
                   "supported. The production rollout guide and the launch blog describe a versionSelector with "
                   "FixedRatio weights. Treat percentage rollouts as unconfirmed until the pages agree.",
                   kind="warn", title="Docs disagree: version traffic splitting",
                   src=[("Hosted agents: versioning", L_HOSTED)])
    n_split.place(cv, cx + 1320, y2)
    return max(t_pack.bottom, n_net.bottom, c_ver.bottom, c_id.bottom, n_split.bottom)


# =========================================================================== band 2 (hero): the Micro VM cut-away
def band_cutaway(cv: Canvas, y: float) -> float:
    _, hb = section_header(cv, 0, y, "The cut-away: one session's Micro VM and the platform layers around it",
                           sub="Numbered circles follow one request; dashed = video/blog only, dotted grey = not documented",
                           size=32, w=W)
    hy = hb + 30

    # ------------------------------------------------------------ measure every block first
    EP_W, SBW, RC_W, RES_W = 360, 1380, 350, 352
    PAD = 24
    inner = SBW - 2 * PAD
    lw = 664
    rw = inner - lw - 24
    NIC_W = 320

    nd_vmm = nd(lw, "Hypervisor / VMM, guest OS, snapshot engine", [
        "Not documented. Learn says only 'VM-isolated sandbox' and 'Micro VM: the lightweight virtual machine that "
        "runs a Hosted agent'. No VMM, guest OS, restore mechanism or host density is named."])
    vb_vmm = vb(rw, "'Hypervisor isolation'", [
        "Launch blog: 'Not process isolation. Not a code execution-only sandbox. Production-proven hypervisor "
        "isolation, at cloud scale.' Mechanics video: 'a secure microVM'."],
                src=[("Foundry launch blog, 2026-04-22", U_BLOG), ("Microsoft Mechanics, 0:03:59", U_MECH)],
                prefix=["Blog", "Video"])
    row0_h = max(nd_vmm.h, vb_vmm.h)

    disks = Card(lw, "Two disks inside the VM", [
        "# Root disk",
        "Ephemeral root disk for the sandbox; lasts up to 24 hours",
        "# $HOME + /files data volume",
        "Persistent, backed by platform-managed storage; restored when the session resumes",
        "Budget up to 20 GiB at 1 vCPU or more (less for smaller sizes); about 20% reserved for the system",
        "! Not CMK-encrypted; no bring-your-own storage; cannot be disabled (as of 2026-11-03)",
    ], theme="cyan", icon="storage", src=[("Hosted agents: session storage", L_HOSTED), ("CMK coverage", L_CMK)])
    egress = Card(lw, "Egress proxy", [
        "Runs inside the sandbox and applies ordered host rules before traffic leaves the runtime",
        "Allow / Deny / Transform / Rewrite, first match wins; max 480 rules; Audit or Enforce",
        "Its CA is injected into the trust bundle (SSL_CERT_FILE and friends) and rotates about every 30 days",
        "A denied call gets HTTP 403 and a 'Network egress decision' span",
    ], theme="pink", icon="firewall", badge="preview", src=[("Add hosted-agent guardrails", L_EGRESS)])
    container = Card(rw, "Your container + protocol library", [
        "Starts from the version's container snapshot (image or source zip)",
        "The protocol library bundles the HTTP server, health check and OpenTelemetry (Responses, Invocations, WebSocket)",
        "Responses adapter hydrates conversation history and emits created -> in_progress -> completed | failed | cancelled",
        "Listens on 0.0.0.0:8088, plain HTTP/1.1; the platform terminates TLS",
        "GET /readiness must return 200; anything else asks the platform to restart the instance",
        "On SIGTERM: stop accepting, finish in-flight work, flush $HOME, exit",
        "# Injected at start",
        "FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_AGENT_NAME / _VERSION / _ID, FOUNDRY_AGENT_SESSION_ID",
        "IDENTITY_ENDPOINT + IDENTITY_HEADER; APPLICATIONINSIGHTS_CONNECTION_STRING when project monitoring is on",
    ], theme="green", icon="agent", src=[("Hosted agent runtime contract", L_CONTRACT)])
    sizes = Card(rw, "Size and billing", [
        "One pair per agent version: 0.5 vCPU / 1 GiB, 1 vCPU / 2 GiB or 2 vCPU / 4 GiB",
        "The pair describes one session, not the whole agent; billing follows CPU + memory of active sessions",
        "Right-size from Application Insights: raise it when sustained peaks pass about 70% of the allocation",
    ], theme="yellow", icon="quotas", src=[("Hosted agents: scaling and right-sizing", L_HOSTED)])
    nic1 = Box(NIC_W, "NIC 1: dedicated, in your delegated subnet",
               sub="the agent's own outbound traffic goes direct (bring-your-own VNet)",
               theme="indigo", icon="vnet", icon_pos="left", icon_size=30, size=16, sub_size=14, fill="hatch")
    nic2 = Box(NIC_W, "NIC 2", sub="Learn: 'two network interfaces'; tool-server calls reach the single-tenant data proxy",
               theme="indigo", icon="vnet", icon_pos="left", icon_size=30, size=16, sub_size=14, fill="hatch")
    ident = Note(inner - 2 * NIC_W - 48, "The sandbox holds no blueprint credential. Code gets tokens only from the token "
                 "service or the tool server. Both run outside the sandbox, identify the calling session, and issue "
                 "tokens only for the associated agent.", kind="gotcha", title="No blueprint credential inside the sandbox",
                 src=[("Agent identity", L_IDENT)])

    endpoint = Card(EP_W, "Foundry endpoint (API gateway)", [
        "Authenticates the caller (Entra token, audience https://ai.azure.com) and routes by agent type",
        "Needs the endpoints/interact/action permission (Foundry Agent Consumer is the least-privilege role); API keys are not supported",
        "Forwards only an allow-list of caller headers (x-client-* and tracing headers), never Authorization or Cookie",
        "Prompt agents take another path: no Micro VM, straight to the Tools Service and data proxy",
    ], theme="green", icon="foundry", src=[("Networking deep dive", L_NETDEEP), ("Endpoint authorization", L_ENDPOINT_AUTH)])
    steps = Steps(EP_W, "First request of a session", [
        (1, "Client calls the agent endpoint over HTTPS with an Entra token"),
        (2, "The gateway authenticates, resolves the version and routes by agent type"),
        (3, "Quota check, then a Micro VM is provisioned (an IP from your subnet in BYO-VNet mode)"),
        (4, "$HOME and /files are restored onto it"),
        (5, "The container starts with env vars injected; the gateway posts the request"),
        (6, "Your handler loops: token requests (6a), tool server (6b), model calls (6c), the tool path (6d-6f) "
            "and its own outbound calls (6g)"),
        (7, "The response (JSON or SSE) returns; the idle timer starts"),
    ], theme="green", src=[("Hosted agents: request flow", L_HOSTED)])

    c_tok = Card(RC_W, "Hosted-agent token service", [
        "Runs outside the sandbox; issues tokens only for the associated agent",
        "ManagedIdentityCredential and DefaultAzureCredential reach it through IDENTITY_ENDPOINT - not IMDS, never the project identity",
    ], theme="red", icon="managed-identity", body_size=15, src=[("Token service reference", L_TOKEN)])
    c_tool = Card(RC_W, "Tool server", [
        "Runs outside the sandbox and identifies the calling session",
        "A project-level backend; in BYO-VNet its traffic goes through the data proxy",
    ], theme="orange", icon="toolbox", body_size=15, src=[("Networking deep dive", L_NETDEEP)])
    c_model = Card(RC_W, "Project endpoint (model proxy)", [
        "The project proxies inference to the account-level deployment with its own managed identity",
        "The agent identity has implicit access to inference through the project endpoint",
    ], theme="blue", icon="openai", body_size=15, src=[("Hosted agent permissions", L_PERMS)])
    c_ts = Card(RC_W, "Tools Service", [
        "Hosted path: Micro VM -> Tools Service -> data proxy -> your resources",
    ], theme="orange", icon="toolbox-icon", body_size=15, src=[("Networking deep dive", L_NETDEEP)])
    c_dp = Card(RC_W, "Data proxy host layer", [
        "Single-tenant: one isolated instance per Foundry project",
        "All tool calls route through it; in BYO-VNet it takes IPs from your delegated subnet",
    ], theme="indigo", icon="private-link", body_size=15, src=[("Networking deep dive", L_NETDEEP)])
    res = Card(RES_W, "Your resources (BYO VNet)", [
        "Reached through private endpoints in your PE subnet",
        "Storage, Cosmos DB, AI Search, Key Vault, SQL",
        "Private DNS zones keep name resolution inside the VNet",
    ], theme="cyan", icon="storage", body_size=15, src=[("Networking deep dive", L_NETDEEP)])
    inet = Card(210, "Your network", [
        "NSG, UDRs, Azure Firewall, peering, internet",
        "You control this egress",
    ], theme="gray", icon="globe", body_size=15, title_size=19)

    # container must be tall enough that the three arrows to the outside services leave from beside it
    stack_h = c_tok.h + c_tool.h + c_model.h + 2 * 24
    cont_h = max(container.h, stack_h - 80)

    # ------------------------------------------------------------ geometry
    PLAT_X = 330
    ex = PLAT_X + 28
    host_x = ex + EP_W + 190
    with cv.panel(PLAT_X, hy, title="Microsoft-managed Foundry platform network", theme="gray", style="dotted",
                  pad=28, title_size=24) as plat:
        endpoint.place(cv, ex, plat.iy)
        steps.place(cv, ex, endpoint.bottom + 30)
        with cv.panel(host_x, plat.iy, title="Micro VM host layer",
                      sub="documented component name: it runs Hosted agents", theme="green", style="solid",
                      fill="none", pad=26, title_size=26, sub_size=15) as host:
            with cv.panel(host.ix, host.iy, title="Micro VM sandbox: session A", sub="the VM-isolated sandbox, cut open",
                          theme="green", style="solid", fill="soft", pad=PAD, title_size=24, sw=3, w=SBW) as sb:
                r0y = sb.iy
                nd_vmm.place(cv, sb.ix, r0y, h=row0_h)
                vb_vmm.place(cv, sb.ix + lw + 24, r0y, h=row0_h)
                r1y = r0y + row0_h + 24
                container.place(cv, sb.ix + lw + 24, r1y, h=cont_h)
                sizes.place(cv, sb.ix + lw + 24, container.bottom + 24)
                disks.place(cv, sb.ix, r1y)
                egress.place(cv, sb.ix, disks.bottom + 24, h=max(egress.h, sizes.bottom - (disks.bottom + 24)))
                ry = max(egress.bottom, sizes.bottom) + 28
                nic1.place(cv, sb.ix, ry)
                nic2.place(cv, sb.ix + inner - NIC_W, ry)
                ident.place(cv, sb.ix + NIC_W + 24, ry)
                row_h = max(nic1.h, nic2.h, ident.h)
                nic1.h = nic2.h = row_h
            # session siblings + the black box
            sy = sb.bottom + 34
            sess = [Box(206, f"Session {n}", sub="its own Micro VM", theme="green", icon="vm", icon_pos="left",
                        icon_size=30, h=96, size=17, sub_size=13, fill="hatch") for n in ("B", "C", "N")]
            sx = host.ix
            for s in sess:
                s.place(cv, sx, sy)
                sx += s.w + 22
            nd_sched = nd(SBW - (sx - host.ix), "Placement, warm pool, scheduler", [
                "Learn: 'no replica count to configure and no warm pool to size'. That describes what you can "
                "configure, not how placement works."])
            nd_sched.place(cv, sx, sy, h=96)
        # right column: services outside the sandbox
        rx = host.right + 150
        c_tok.place(cv, rx, container.y - 30)
        c_tool.place(cv, rx, c_tok.bottom + 24)
        c_model.place(cv, rx, c_tool.bottom + 24)
        c_ts.place(cv, rx, max(c_model.bottom + 24, nic2.cy - c_ts.h / 2))
        c_dp.place(cv, rx, c_ts.bottom + 52)
    # outside the platform panel
    res.place(cv, plat.right + 80, c_dp.y)
    client = Box(210, "Callers", sub="SDK / REST, portal, Teams + M365 (Activity), other agents (A2A)", theme="gray",
                 icon="user", h=150, size=19, sub_size=14, fill="hatch")
    client.place(cv, 0, endpoint.cy - 75)
    inet.place(cv, 0, nic1.cy - inet.h / 2)

    # ------------------------------------------------------------ arrows and step markers
    harrow(cv, client.right + 6, endpoint.x - 6, endpoint.cy, num=1, label="HTTPS + Entra token", label_w=90,
           label_cx=(client.right + PLAT_X) / 2, num_x=client.right + 104)
    numbered(cv, endpoint.right - 8, endpoint.y + 8, 2, theme="green")
    t3w = text_size("Micro VM host layer", 26)[0]
    numbered(cv, host.x + 26 + t3w + 30, host.y + 18 + 16, 3, theme="green")
    numbered(cv, disks.right - 26, disks.y + 24, 4, theme="green")
    gap_mid = (endpoint.right + host.x) / 2
    harrow(cv, endpoint.right + 6, sb.x - 6, sb.y + 120, num=5, label="POST /responses or /invocations", label_w=150,
           label_cx=gap_mid, num_x=sb.x - 40)
    harrow(cv, sb.x - 6, endpoint.right + 6, sb.y + 235, num=7, dash="dashed", label="response (JSON or SSE)",
           label_w=150, label_cx=gap_mid, num_x=endpoint.right + 40)
    for tgt, lab, n in ((c_tok, "token request", "6a"), (c_tool, "tool calls", "6b"), (c_model, "model calls", "6c")):
        harrow(cv, sb.right + 6, tgt.x - 6, tgt.cy, num=n, label=lab, label_cx=(host.right + tgt.x) / 2 + 6,
               label_w=130, num_x=sb.right + 38)
    harrow(cv, nic2.right + 4, c_ts.x - 6, nic2.cy, num="6d", label="tool path", label_cx=(host.right + c_ts.x) / 2 + 6,
           num_x=sb.right + 38)
    varrow(cv, c_ts.cx, c_ts.bottom + 4, c_dp.y - 4, num="6e")
    harrow(cv, c_dp.right + 6, res.x - 6, c_dp.cy, num="6f", label="private endpoints", label_w=100,
           label_cx=(c_dp.right + res.x) / 2, num_x=c_dp.right + 36)
    harrow(cv, nic1.x - 4, inet.right + 6, nic1.cy, num="6g", label="agent's own outbound traffic: direct",
           label_cx=(inet.right + PLAT_X) / 2 + 110, num_x=inet.right + 40)
    return max(plat.bottom, res.bottom, inet.bottom)


# =========================================================================== band 3: what is known / said / not said
def band_evidence(cv: Canvas, y: float) -> float:
    _, hb = section_header(cv, 0, y, "What we actually know about the Micro VM",
                           sub="Learn confirms the isolation boundary and the plumbing; only videos and blogs name the "
                               "technology; nobody names the hypervisor",
                           size=32, w=W)
    top = hb + 28
    cw = (W - 2 * 40) / 3
    c1 = Card(cw, "Learn says (documented)", [
        "Each hosted-agent session runs in its own VM-isolated sandbox; sessions are isolated from each other",
        "'Micro VM' is the lightweight virtual machine that runs a hosted agent; it has two network interfaces",
        "In BYO-VNet mode each session takes one IP from your delegated subnet (default mapping 1 : 1)",
        "No blueprint credential inside the sandbox; the token service and tool server run outside it",
        "Ephemeral root disk (up to 24 h) plus a persistent $HOME and /files volume on platform-managed storage",
        "Compute is deprovisioned when idle and provisioned again later, possibly on other infrastructure",
        "The 2026 hosting backend is new: deployments on the initial preview backend were supported only until 2026-08-20",
    ], theme="green", icon="learn", src=[("Hosted agents", L_HOSTED), ("Networking deep dive", L_NETDEEP),
                                         ("Migrate hosted agents", L_MIGRATE)])
    c2 = vb(cw, "Videos and blogs say", [
        "Launch blog: 'Not process isolation ... production-proven hypervisor isolation, at cloud scale'",
        "Mechanics video: each user's session runs in 'a secure microVM'",
        "Build BRK243: a new session ID gives a brand-new file system and a new VM recreated from the snapshot deployed with the agent",
        "Blog table: cold starts 'seconds (low variance, predictable)'; text: sessions spin up 'virtually instantly'",
        "Reactor speaker, informally: the new 'fast micro VM platform' replaced a Container-Apps-based predecessor",
        "Agent Framework blog (2026-09-22): hosted agents are GA; AgentServer SDKs and hosting packages are still pre-release",
    ], theme="yellow", src=[("Launch blog", U_BLOG), ("Mechanics", U_MECH), ("BRK243", U_BRK243), ("Reactor", U_REACTOR),
                            ("Agent Framework blog", U_MAF_BLOG)],
        prefix=["Blog", "Video", "Video", "Video", "Blog"])
    c3 = nd(cw, "Nobody says", [
        "Which hypervisor or VMM runs the Micro VM, and what the guest OS is",
        "How a session is snapshotted and restored, whether a warm pool exists, how many VMs share a host",
        "Whether process memory is ever persisted (Learn: only $HOME and /files)",
        "A numeric cold-start or resume time",
        "Whether an idle session gives its delegated-subnet IP back",
        "Whether 'on Azure Container Apps' in Learn's networking diagram still describes the Micro VMs",
        "Whether 'Tools Service' (networking page) and 'tool server' (identity page) are one component",
        "Adjacent, not the same: ACA dynamic sessions use Hyper-V-isolated sandboxes with pre-warmed pools; no page says hosted agents are built on them",
    ])
    row(cv, 0, top, [c1, c2, c3], gap=40)
    return max(c1.bottom, c2.bottom, c3.bottom)


# =========================================================================== band 4: session lifecycle
def state_diagram(cv: Canvas, x: float, y: float) -> float:
    NW, NH = 270, 132
    cv.text(x, y, "State diagram (documented states: Active, Idle, Resumed)", size=22, color="#2b8a3e")
    y += 50

    def node(label, sub, theme, px, py):
        return Box(NW, label, sub=sub, theme=theme, h=NH, fill="hatch", size=19, sub_size=14).place(cv, x + px, y + py)

    P = node("Provisioning", "first request; compute is being provisioned; counts toward the quota", "green", 80, 0)
    A = node("Active", "compute running, requests routed, $HOME + /files available; each request resets the idle timer",
             "green", 520, 0)
    I = node("Idle", "no request for the idle timeout: compute deprovisioned, state persisted; not counted toward the quota",
             "gray", 960, 0)
    D = node("Deleted", "DELETE, or 30 days of inactivity: sandbox released and the persistent volume deleted", "red",
             1400, 0)
    R = node("Resumed", "same session ID again: new compute (maybe other infrastructure), state restored; needs free quota",
             "green", 740, 300)
    S = node("Stopped", "POST :stop (idempotent): compute terminated, volume kept; not counted toward the quota",
             "gray", 80, 300)
    # start dot
    ym = y + NH / 2
    cv.ellipse(x + 14, ym - 11, 22, 22, stroke=INK, fill=INK, style="solid", rough=0)
    arrow(cv, [(x + 38, ym), (P.x - 6, ym)])
    harrow(cv, P.right + 6, A.x - 6, ym, label="compute is up", label_w=150, label_cx=(P.right + A.x) / 2)
    harrow(cv, A.right + 6, I.x - 6, ym, label="no request for the idle timeout", label_w=150, label_cx=(A.right + I.x) / 2)
    harrow(cv, I.right + 6, D.x - 6, ym - 30, label="30 days of inactivity", label_w=150, label_cx=(I.right + D.x) / 2)
    cv.text(I.x, I.y - 36, "2 min - 4 h, default 15 min", size=14, color="#c92a2a", align="center", w=NW)
    # I -> R (down then left), R -> A (diagonal up), A -> S (elbow), S -> R (straight)
    connect(cv, I, R, a_side="bottom", b_side="right", route="elbow", label="same session ID again", label_wrap=140,
            label_size=14, label_pos="right", label_t=0.3)
    connect(cv, R, A, a_side="top", b_side="bottom", ta=0.35, tb=0.78, label="state restored, request served",
            label_wrap=150, label_size=14, label_pos="left", label_t=0.5)
    connect(cv, A, S, a_side="bottom", b_side="top", ta=0.2, tb=0.5, route="elbow", label=":stop", label_size=14,
            label_t=0.25)
    harrow(cv, S.right + 6, R.x - 6, S.cy, label="invoke again with the session ID", label_w=200,
           label_cx=(S.right + R.x) / 2)
    # S -> D along the bottom, DELETE chip -> D
    yb = y + 300 + NH + 56
    arrow(cv, [(S.cx - 60, S.bottom + 6), (S.cx - 60, yb), (D.x - 36, yb), (D.x - 36, D.y + 100), (D.x - 6, D.y + 100)],
          dash="solid")
    cv.text(S.cx + 160, yb - 24, "30 days of inactivity (stopped sessions too)", size=14, color=INK)
    chip = Chip("DELETE /sessions/{id}, any time", theme="red", size=14).place(cv, D.x, D.bottom + 70)
    arrow(cv, [(chip.cx, chip.y - 4), (chip.cx, D.bottom + 6)], dash="dashed")
    cv.text(chip.x, chip.bottom + 6, "releases the sandbox and deletes the volume", size=13, color=MUTED)
    return yb + 24


def lanes(cv: Canvas, x: float, y: float, w: float) -> float:
    cv.text(x, y, "The same session over time (not to scale)", size=22, color="#0b7285")
    y += 44
    lx = x + 190
    tw = w - 190
    marks = [(0.0, "first request"), (0.30, "idle timeout"), (0.52, "same session ID again"),
             (0.74, "idle timeout"), (0.93, "30 days idle")]
    px = [lx + tw * f for f, _ in marks]
    lane_h, lane_gap = 74, 18
    ys = [y + 44 + i * (lane_h + lane_gap) for i in range(3)]
    names = ["Compute (Micro VM)", "State: $HOME + /files", "Quota and billing"]
    for yy, nm in zip(ys, names):
        cv.text(x, yy + lane_h / 2 - 18, nm, size=17, color=INK, w=180, wrap=170)
    # top labels
    for (f, lab), xx in zip(marks, px):
        tw_ = text_size(lab, 14)[0]
        cv.text(min(max(xx - tw_ / 2, lx - 40), x + w - tw_), y + 6, lab, size=14, color="#c92a2a")
        cv.line((xx, y + 32), (xx, ys[-1] + lane_h + 10), stroke="#868e96", sw=1, dash="dashed", opacity=80)

    def block(i, a, b, text, theme, kind="doc"):
        th = THEMES[theme]
        x0, x1 = px[a], px[b] if b < len(px) else lx + tw
        if kind == "doc":
            cv.rect(x0 + 3, ys[i], x1 - x0 - 6, lane_h, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
        else:
            cv.rect(x0 + 3, ys[i], x1 - x0 - 6, lane_h, stroke=GREY, fill="transparent", sw=2, dash="dotted")
        lines = wrap_text(text, x1 - x0 - 30, 14)
        cv.text(x0 + 12, ys[i] + (lane_h - len(lines) * 14 * 1.25) / 2, "\n".join(lines), size=14,
                color=th.deep if kind == "doc" else MUTED, align="center", w=x1 - x0 - 24)
        cv.register("lane", x0 + 3, ys[i], x1 - x0 - 6, lane_h)

    block(0, 0, 1, "Micro VM #1: active, requests served", "green")
    block(0, 1, 2, "no compute", "gray", "dim")
    block(0, 2, 3, "Micro VM #2: new compute, maybe other infrastructure", "green")
    block(0, 3, 5, "no compute until the next request", "gray", "dim")
    block(1, 0, 4, "persisted the whole time; restored onto every new VM", "cyan")
    block(1, 4, 5, "deleted", "red")
    block(2, 0, 1, "counts toward quota; CPU + memory billed", "yellow")
    block(2, 1, 2, "not counted; no CPU + memory billing", "gray", "dim")
    block(2, 2, 3, "counts again; CPU + memory billed", "yellow")
    block(2, 3, 5, "not counted; no CPU + memory billing", "gray", "dim")
    return ys[-1] + lane_h + 20


def band_lifecycle(cv: Canvas, y: float) -> float:
    _, hb = section_header(cv, 0, y, "Session lifecycle: compute is ephemeral, state is not",
                           sub="A session is compute plus persisted files (agent_session_id); a conversation is message "
                               "history; the state store is your own durable key-value data",
                           size=32, w=W)
    top = hb + 30
    LW = 1760
    sb = state_diagram(cv, 0, top)
    lb = lanes(cv, 0, sb + 30, LW)

    rx = LW + 80
    cw = (W - rx - 36) / 2
    scale = Card(cw, "Scale to zero and cold start", [
        "Scale per session, not per replica: a new VM-isolated sandbox for each session, on demand",
        "No replica count to configure and no warm pool to size",
        "Each request resets the idle timer; at the timeout the compute is deprovisioned and the files persisted",
        "Compute is ephemeral: only $HOME and /files are persisted",
        "Starting or resuming can need compute provisioning; Learn promises 'predictable cold starts' but gives no number",
    ], theme="green", icon="vm", src=[("Hosted agents: scaling", L_HOSTED), ("Networking deep dive", L_NETDEEP)])
    cold = vb(cw, "Cold start, as the blog puts it", [
        "Blog table: traditional compute 'seconds to minutes (high variance)' vs hosted agents 'seconds (low variance, predictable)'",
        "Reactor speaker, informally: 'very fast startup' on the 'fast micro VM platform'",
    ], src=[("Foundry launch blog", U_BLOG), ("Reactor, 0:40:19", U_REACTOR)], prefix=["Blog", "Video"])
    cold_nd = nd(cw, "A cold-start number", [
        "No cold-start or resume-time target is published on Learn; the blog only says 'seconds'. Plan from your own "
        "measurements for your image size and region."])
    field = vb(cw, "Field notes from a pattern repo", [
        "Not vendor-verified, observed in preview: a session can report ACTIVE before your HTTP server is ready (HTTP 424 seen), "
        "so send a smoke turn first; unpinned requests may create new sessions; a new version does not evict running sessions."],
               src=[("microsoft/agenticai-design-patterns", U_PATTERNS)], prefix="Repo")
    quota = Card(cw, "Concurrency quota (as of 2026-11-03)", [
        "Per subscription and region: 2,000 concurrent sessions in Canada Central, East US 2, Japan East, North Central US, "
        "South Africa North, Southeast Asia and Sweden Central; 1,000 in every other hosted-agent region",
        "A session counts while its compute is being provisioned or running; idle and stopped sessions do not",
        "Resuming needs free quota; ask Azure support for a higher limit",
        "HTTP 429: session_quota_exceeded, regional_session_quota_exceeded, subnet_exhausted",
    ], theme="yellow", icon="quotas", src=[("Agent Service limits and quotas", L_LIMITS)])
    brk = vb(cw, "Session = file system = VM", [
        "BRK243: 'every session ID controls the file system'; a new session ID is a brand-new file system and a brand-new VM, "
        "recreated from the snapshot deployed with the agent. Idle shutdown after about 15 minutes; files kept about 30 days."],
             src=[("Build BRK243, 0:15:00", U_BRK243)], prefix="Video")
    idle_nd = nd(cw, "Do idle sessions hold subnet IPs?", [
        "Learn takes idle sessions out of the concurrency quota and maps subnet IPs to concurrent sessions, but never "
        "states whether an idle session releases its delegated-subnet IP."])
    colA = [scale, cold, cold_nd, field]
    colB = [quota, brk, idle_nd]
    ya = top
    for c in colA:
        c.place(cv, rx, ya)
        ya = c.bottom + 24
    yb2 = top
    for c in colB:
        c.place(cv, rx + cw + 36, yb2)
        yb2 = c.bottom + 24
    y2 = max(lb, ya, yb2) + 30

    t_sc = Table(
        [("Aspect", 130), ("Session", 400), ("Conversation", 380), ("State store", 440)],
        [
            ["Holds", "Sandbox compute and persisted files ($HOME, /files)", "Messages, tool calls and responses",
             "Your own keyed JSON items: checkpoints, history you manage, artifacts, preferences"],
            ["Identifier", "agent_session_id", "conversation, or previous_response_id (Responses only)",
             "store name + item key"],
            ["Managed by", "The platform, through the /sessions API", "The platform (Responses); your code (Invocations)",
             "Your agent writes it explicitly; the platform never fills it"],
            ["Lifetime", "Idle timeout 2 min - 4 h (default 15 min); deleted after 30 days of inactivity",
             "Stored in Foundry, independent of compute",
             "Idle window default 30 days (writes renew, reads do not), or never expire; item up to 1 MB"],
        ], theme="green", size=14, head_size=15, first_col_theme="green",
        title="Session vs conversation vs state store", title_size=22)
    t_sc.place(cv, 0, y2)
    iso = Card(850, "Per-session and per-user isolation", [
        "Each session is its own VM-isolated sandbox with a private $HOME",
        "Container protocol 2.0.0: each request carries its own user context, so one session can serve many users",
        "The platform derives the caller from the Entra token; that caller's conversations, sessions and stored data stay private",
        "Foundry User at project scope can list and manage every session on the agent",
        "! Delegated users (x-ms-user-identity) are not fenced from each other: two users routed to one session see each other's data",
    ], theme="red", icon="managed-identity", src=[("Isolate sessions per user", L_ISO), ("Migrate: container protocol 2.0.0", L_MIGRATE)])
    iso.place(cv, t_sc.right + 40, y2)
    maf = vb(W - (iso.right + 40), "Two independent isolation controls", [
        "User isolation = whose data may be used (the Entra caller, or a delegated identity). Hosted session isolation = "
        "where code and files continue to live (the VM-isolated sandbox keyed by agent_session_id). "
        "'A Foundry hosted session is not a conversation.' In a pooled design a middle tier maps users to a bounded set "
        "of sessions: response chains stay private per user while the sandbox filesystem stays shared."],
             src=[("Agent Framework blog, 2026-09-22", U_MAF_BLOG)], prefix="Blog")
    maf.place(cv, iso.right + 40, y2)
    return max(t_sc.bottom, iso.bottom, maf.bottom)


def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Hosted agents: how a container becomes an agent endpoint",
        "Under the hood - one Micro VM sandbox per session: what Learn documents, what only a video says, and what nobody has published",
        icon="foundry", w=W)
    y = bottom + 34
    tiles = [
        ("1 = 1", "session = one VM-isolated sandbox that Learn calls a 'Micro VM'; sessions are isolated from each other", "green", "doc"),
        ("2 NICs", "per Micro VM: its own outbound NIC, and tool-server calls through the single-tenant data proxy", "indigo", "doc"),
        ("0.5 - 2 vCPU", "with 1 - 4 GiB per session; billing follows CPU + memory of active sessions", "yellow", "doc"),
        ("2 min - 4 h", "idle timeout per version (default 15 min); then the compute is deprovisioned", "green", "doc"),
        ("30 days", "of inactivity and the session is permanently deleted, $HOME included", "cyan", "doc"),
        ("8088", "the contract: plain HTTP, GET /readiness, POST /responses or /invocations", "green", "doc"),
        ("? s", "cold start: 'predictable' on Learn, 'seconds' in a blog, no published number", "gray", "nd"),
        ("? VMM", "hypervisor, guest OS and snapshot engine are not named anywhere", "gray", "nd"),
    ]
    tw = (W - 7 * 24) / 8
    for i, (big, cap, th, kind) in enumerate(tiles):
        tile(cv, i * (tw + 24), y, tw, 132, big, cap, th, kind)
    y = evidence_legend(cv, 0, y + 132 + 24)
    y = band_pipeline(cv, y + 50)
    y = band_cutaway(cv, y + 60)
    y = band_evidence(cv, y + 60)
    y = band_lifecycle(cv, y + 60)

