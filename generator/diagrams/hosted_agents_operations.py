"""Hosted agents - operations: every deploy path, versions / rollout / promotion, CI/CD, logs, telemetry and debugging,
guardrails (preview) and long-running resilient agents (preview).

Companion of 'hosted-agents' (concepts, runtime contract, sessions, identity, scale, regions).  Developer / operator view
only: Micro VM internals are on 'hood-hosted-agent-runtime'.  Preview items carry a Preview badge; doc conflicts are warn Notes.
"""
from __future__ import annotations

from generator.xd import *
from generator.xd import metrics

META = dict(
    id="hosted-agents-operations", title="Hosted agents: deploy and operate", section="2", group="Agent Service", order=12.5,
    description="Hosted agents in operation: seven deploy paths, versions and safe rollout, CI/CD, logs and debugging, guardrails (preview) "
                "and long-running resilient agents (preview) - crash recovery, steering, cancel, human-in-the-loop, stream reconnect and the durable state store.",
    tags=["hosted-agents", "deploy", "azd", "versions", "cicd", "long-running"],
)

W = 3600
G = 48
C = 560


def X(i: int) -> float:
    return i * (C + G)


def S(n: int) -> float:
    return n * C + (n - 1) * G


# ---------------------------------------------------------------------------------------------- sources
U = dict(
    hosted=("Hosted agents (concepts)", learn("agents/concepts/hosted-agents")),
    deploy=("Deploy a hosted agent", learn("agents/how-to/deploy-hosted-agent")),
    code=("Deploy from source code", learn("agents/how-to/deploy-hosted-agent-code")),
    tf=("Deploy with Terraform", learn("agents/how-to/deploy-hosted-agent-terraform")),
    privacr=("Deploy from a private Azure Container Registry", learn("agents/how-to/deploy-hosted-agent-private-azure-container-registry")),
    byo=("Private registry connections", learn("agents/how-to/private-registry-connections")),
    prod=("Deploy hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production")),
    cicd=("Set up CI/CD with the CLI", learn("agents/how-to/set-up-ci-cd-cli")),
    manage=("Manage hosted agents", learn("agents/how-to/manage-hosted-agent")),
    sessions=("Manage hosted agent sessions", learn("agents/how-to/manage-hosted-sessions")),
    epcli=("Update the agent endpoint with the CLI", learn("agents/how-to/update-agent-endpoint-cli")),
    env=("Hosted agent environment variables", learn("agents/how-to/configure-hosted-agent-env-variables")),
    otel=("Configure hosted agent telemetry", learn("agents/how-to/configure-hosted-agent-telemetry")),
    logs=("Monitor hosted agent logs", learn("agents/how-to/monitor-hosted-agent-logs")),
    debug=("Debug a hosted agent", learn("agents/how-to/debug-hosted-agent")),
    lat=("Reduce startup latency for hosted agents", learn("agents/how-to/optimize-hosted-agent-latency")),
    snap=("Enable memory snapshots for hosted agents", learn("agents/how-to/use-hosted-agent-memory-snapshots")),
    doctor=("Agent doctor", learn("agents/how-to/agent-doctor")),
    inspector=("Agent inspector", learn("agents/how-to/agent-inspector")),
    gc=("Hosted agent guardrails (concepts)", learn("agents/concepts/hosted-agent-guardrails")),
    gh=("Add guardrails to a hosted agent", learn("agents/how-to/add-hosted-agent-guardrails")),
    lr=("Resilience for long-running hosted agents", learn("agents/concepts/long-running-agent-resilience")),
    lrr=("Long-running agent reference", learn("agents/concepts/long-running-agent-reference")),
    resil=("Deploy a resilient agent", learn("agents/how-to/deploy-resilient-agent")),
    steer=("Steer a hosted agent", learn("agents/how-to/steer-hosted-agent")),
    cancel=("Cancel a hosted agent turn", learn("agents/how-to/cancel-hosted-agent-turn")),
    hitl=("Add human-in-the-loop", learn("agents/how-to/add-human-in-the-loop")),
    reconnect=("Stream with reconnect", learn("agents/how-to/stream-with-reconnect")),
    recover=("Recover long-running work", learn("agents/how-to/recover-long-running-work")),
    taskstate=("Manage task state", learn("agents/how-to/manage-task-state")),
    state=("Durable state store", learn("agents/concepts/agent-state-store")),
    azyaml=("azure.yaml reference", learn("agents/concepts/azure-yaml-reference")),
    cli=("CLI agent development", learn("agents/concepts/cli-agent-development")),
    perms=("Hosted agent permissions", learn("agents/concepts/hosted-agent-permissions")),
    migrate=("Migrate from the initial hosted-agent preview", learn("agents/how-to/migrate-hosted-agent-preview")),
    vnet=("Configure virtual networks for agents", learn("agents/how-to/virtual-networks")),
    limits=("Limits, quotas and regions", learn("agents/concepts/limits-quotas-regions")),
    rest=("REST: update an agent (version selector)", learn("reference/rest/agents-patch-agent-object")),
)


def src(*keys: str) -> list:
    return [U[k] for k in keys]


def card(w, title, body, theme="green", **kw) -> Card:
    kw.setdefault("title_size", 19)
    kw.setdefault("body_size", 15)
    kw.setdefault("sub_size", 13)
    kw.setdefault("pad", 14)
    kw.setdefault("gap", 4)
    kw.setdefault("icon_size", 30)
    return Card(w, title, body, theme=theme, **kw)


class Tile(Rect2):
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


def head(cv, y, text, sub=None) -> float:
    _, b = section_header(cv, 0, y, text, sub=sub, w=W, size=32, sub_size=17)
    return b + 28


def label(cv, x, y, text, theme="green", size=22) -> float:
    t = cv.text(x, y, text, size=size, color=THEMES[theme].deep)
    return t.bottom + 12


def bracket(cv, x1, x2, y, up=12, color=INK) -> None:
    """Flat bracket under a group of boxes: end ticks point up at the boxes, a centre tick points down at the caption."""
    cv.poly([(x1, y - up), (x1, y), (x2, y), (x2, y - up)], kind="line", stroke=color, sw=2)
    xm = (x1 + x2) / 2
    cv.line((xm, y), (xm, y + 12), stroke=color, sw=2)


# ================================================================================================ A  deploy
LANES = [
    # (lane label, theme, icon, build text, arrow label, store text)
    ("azd end to end", "green", "builds", "azd ai agent init (deploy mode code is the default for Python and .NET; --deploy-mode container builds or references an image), then azd up or azd deploy",
     "zip or build", "Code mode: azd zips your source and uploads it. Container mode: the image is built remotely in ACR - no local Docker needed (remoteBuild: false builds locally)"),
    ("Source zip (code)", "green", "folder", "Zip of source plus code_configuration: runtime, entry_point, dependency_resolution - no container image to build or push",
     "upload", "The zip (up to 250 MB, flat root) travels with the create call - no registry. remote_build or bundled dependencies"),
    ("Container image to ACR", "gray", "container-apps", "Your own CI builds and pushes a linux/amd64 image",
     "push", "Azure Container Registry; the version is created with container_configuration.image"),
    ("Private ACR", "indigo", "private-link", "azd ai agent init --acr-connection, or a prebuilt --image; azd ai agent doctor checks the setup",
     "push", "ACR with public access disabled - run azd up from inside the VNet (projects created after 2026-06-25)"),
    ("BYO registry (non-Azure)", "gray", "api-connections", "Push the image to a non-Azure registry, for example JFrog",
     "push + OIDC", "CustomKeys registry connection with OIDC token exchange; registryConnectionId, docker.imagePassthrough: true"),
    ("Terraform (AzAPI)", "grape", "workflow", "azapi_data_plane_resource of type Microsoft.Foundry/agents@v1",
     "apply", "Pin the image by DIGEST; rai_policy_name takes the full ARM ID; parent_id is the project endpoint without https://"),
    ("REST or SDK", "gray", "code", "POST /agents/{name}/versions (api-version=v1) or the Python SDK",
     "create", "HostedAgentDefinition(cpu, memory, environment_variables, protocol_versions); delete(force=True) cascades to sessions"),
]


def band_deploy(cv: Canvas, y: float) -> float:
    y = head(cv, y, "A  Seven ways to deploy - every path ends in a new immutable agent version",
             "Pick the path by where your build lives and how locked down the registry is. All of them end in the same version and the same dedicated endpoint.")
    LBL_W, BUILD_W, STORE_W, VER_W, END_W = 290, 780, 850, 700, 596
    g1, g2, g3, g4 = 24, 130, 130, 100
    x_b = LBL_W + g1
    x_s = x_b + BUILD_W + g2
    x_v = x_s + STORE_W + g3
    x_e = x_v + VER_W + g4
    LH, LG = 76, 14
    # column headings
    for xx, t in ((0, "Path"), (x_b, "You run"), (x_s, "Package and store"), (x_v, "Result"), (x_e, "Serves")):
        cv.text(xx, y, t, size=20, color=THEMES["green"].deep)
    y0 = y + 38
    for i, (nm, th, ic, build, al, store) in enumerate(LANES):
        ly = y0 + i * (LH + LG)
        Box(LBL_W, nm, theme=th, icon=ic, icon_pos="left", icon_size=30, size=17, h=LH, fill="solid").place(cv, 0, ly)
        Box(BUILD_W, build, theme=th, fill="soft", size=16, h=LH).place(cv, x_b, ly)
        Box(STORE_W, store, theme=th, fill="soft", size=16, h=LH).place(cv, x_s, ly)
        cy = ly + LH / 2
        arrow(cv, [(x_b + BUILD_W + 6, cy), (x_s - 6, cy)], label=al, label_size=14, sw=2)
        arrow(cv, [(x_s + STORE_W + 6, cy), (x_v - 6, cy)], sw=2)
    total = len(LANES) * (LH + LG) - LG
    ver = card(VER_W, "Agent version (immutable)", [
        "Created by every path on the left - each deploy makes a new version",
        "A snapshot of image or code, cpu/memory, env vars and protocols; env vars are fixed once created",
        "Poll status: creating, then active or failed (also deleting, deleted)",
        "Provisioning takes under 1 min (deploy page) or 2-5 min (manage page) - docs disagree",
        "Existing sessions stay on their original version",
        "Up to 1,000 versions per agent (a 400 error when exceeded)",
    ], theme="green", icon="versions", src=src("manage", "deploy", "limits"))
    ver.place(cv, x_v, y0)
    pvx = card(VER_W, "Settings that live on a version", [
        "cpu and memory: a valid resource tier, or the call fails with a 400 (the docs disagree on the tier list)",
        "Environment variables, protocol_versions (set every one to 2.0.0) and the image or code",
        "Idle timeout: sessionConfiguration.idleTimeoutSeconds in azd; changing it makes a new version",
        "Optional rai_config (guardrails, preview) and draft: true (preview) - section B and E",
    ], theme="green", icon="gear", src=src("manage", "azyaml"))
    pvx.place(cv, x_v, ver.bottom + 18, h=max(pvx.h, y0 + total - (ver.bottom + 18)))
    end = card(END_W, "Endpoint + identity", [
        "Dedicated endpoint, live right after deploy - publishing is not required for programmatic access",
        "Routes follow the protocols declared on the version: Responses, Invocations, Invocations (WebSocket), A2A",
        "Dedicated Entra agent identity: grant it RBAC for what your code calls",
        "The version selector decides which version serves (section B)",
    ], theme="red", icon="foundry", src=src("hosted"))
    end.place(cv, x_e, y0)
    first = card(END_W, "First call and switch-off", [
        "Callers need a Foundry Agent Consumer or Foundry User role and an Entra token for https://ai.azure.com/",
        "azd ai agent invoke tests the deployed agent; add --version to hit a specific version",
        "POST /agents/{name}:disable or :enable turns the endpoint off or on",
    ], theme="gray", icon="globe", src=src("manage", "prod"))
    first.place(cv, x_e, end.bottom + 18, h=max(first.h, y0 + total - (end.bottom + 18)))
    arrow(cv, [(x_v + VER_W + 6, y0 + ver.h / 2), (x_e - 6, y0 + ver.h / 2)], sw=3)

    # ---- detail cards
    dy = max(y0 + total, pvx.bottom, first.bottom) + 44
    azd = card(C, "azd: init, up, deploy", [
        "azd ai agent init takes --deploy-mode code|container (code is the default for Python and .NET), --runtime, --entry-point, --dep-resolution",
        "azure.yaml is the single config file: it replaces agent.manifest.yaml + agent.yaml",
        "Needs azd >= 1.36.0 (voice agents >= 1.32.0) and the azure.ai.agents extension >= 1.0.0-beta.20",
        "azd ai agent endpoint update patches the endpoint without a new version",
    ], theme="green", icon="builds", src=src("deploy", "code", "azyaml"))
    zipc = card(C, "Source zip details", [
        "Runtimes: python_3_13, python_3_14, dotnet_10; the platform ships a built image for each runtime",
        "remote_build (default) installs requirements.txt or restores .NET during provisioning; bundled runs the zip as-is with packages/ or dotnet publish output",
        "REST multipart POST /agents: parts metadata + code; headers x-ms-code-zip-sha256 (always) and x-ms-agent-name (create only, 63 chars max)",
        "Version stuck in creating for over 10 min on a remote build: switch to bundled",
    ], theme="green", icon="folder", src=src("code"))
    reg = card(C, "Private ACR and BYO registry", [
        "# Private ACR",
        "Project managed identity: Container Registry Repository Reader (or AcrPull); deployer: Repository Writer (or AcrPush); ACR needs azureADAuthenticationAsArmPolicy enabled",
        "Projects created before 2026-06-25 need the registry reachable on its public endpoint",
        "# BYO registry",
        "Entra app audience; the registry trusts the project managed identity. Not for ACR behind a private endpoint",
    ], theme="indigo", icon="acr", src=src("privacr", "byo"))
    tfc = card(C, "Terraform notes", [
        "Split shared infrastructure from agent releases",
        "Add a readiness gate before traffic moves",
        "Keep secrets out of the env map",
        "In a pipeline, Terraform keeps its remote state in a storage account (section C)",
    ], theme="grape", icon="workflow", src=src("tf", "cicd"))
    envc = card(C, "Env vars and connections", [
        "Set env on the azure.ai.agent service in azure.yaml; ${VAR} comes from the azd environment. Values are per version and immutable",
        "Placeholders ${{connections.<name>.<credentials.<field> | target | metadata.<field>>}} resolve at sandbox start - create the connection first; secrets are write-only",
        "FOUNDRY_ and AGENT_ prefixes are reserved",
    ], theme="cyan", icon="key-vault", src=src("env"))
    net = card(C, "Networking at deploy time", [
        "VNet injection for hosted agents must be set when the Foundry account is created",
        "azure.ai.project.network: peSubnet, agentSubnet, isolationMode AllowInternetOutbound or AllowOnlyApprovedOutbound",
        "Each session takes an IP in the delegated subnet (1 per session by default; 1:10 through support) - 429 subnet_exhausted when it runs out",
        "Source-code deploys in a private VNet need egress to mcr.microsoft.com and *.login.microsoft.com (plus agent365.svc.cloud.microsoft on 443 with Agent 365 data collection)",
    ], theme="indigo", icon="vnet", src=src("vnet", "deploy"))
    _, rb = row(cv, 0, dy, [azd, zipc, reg, tfc, envc, net], gap=G)
    return rb


# ================================================================================================ B  versions
def _snapshot(cv: Canvas, x: float, y: float, title: str, vers: list, sel: str, test: bool = False) -> float:
    """One frame of the 'selector over time' story: endpoint -> the version it serves; optional pinned test session."""
    ty = label(cv, x, y, title, theme="green", size=21)
    ep = Box(260, "Endpoint", sub="version_selector", theme="green", size=18, sub_size=13, h=64)
    ep.place(cv, x + 10, ty + 4)
    vw, vgap = 172, 28
    by = ty + 4 + 64 + 76
    boxes = {}
    for i, (name, sub, th, dash) in enumerate(vers):
        b = Box(vw, name, sub=sub, theme=th, size=19, sub_size=13, h=84, dash=dash, fill="hatch" if dash == "solid" else "soft")
        b.place(cv, x + 10 + i * (vw + vgap), by)
        boxes[name] = b
    connect(cv, ep, boxes[sel], a_side="bottom", b_side="top", route="elbow", sw=3, gap=5, label="serves", label_size=14)
    bottom = by + 84
    if test:
        tb = Box(300, "Test session", sub="version_indicator = v4", theme="yellow", size=17, sub_size=13, h=64)
        tb.place(cv, boxes["v4"].x - 128, by + 84 + 56)
        connect(cv, tb, boxes["v4"], a_side="top", b_side="bottom", ta=0.7, tb=0.5, dash="dashed", sw=2, gap=5)
        bottom = tb.bottom
    return bottom


def band_versions(cv: Canvas, y: float) -> float:
    y = head(cv, y, "B  Versions, rollout and promotion - release without touching production",
             "The endpoint follows the latest version by default, so pin production first. Draft versions and the traffic-splitting question are called out below.")
    # ---- version lifecycle mini diagram
    ty = label(cv, 0, y, "Version lifecycle")
    bw = 230
    gap = (S(2) - 4 * bw) / 3
    mk = lambda t, s_, th, dash="solid": Box(bw, t, sub=s_, theme=th, size=19, sub_size=13, h=96, dash=dash, fill="hatch" if dash == "solid" else "soft")
    b_cr = mk("creating", "2-5 min or under 1 min (docs disagree)", "yellow")
    b_ac = mk("active", "serves traffic", "green")
    b_dl = mk("deleting", "removal in progress", "gray")
    b_dd = mk("deleted", "gone", "gray", dash="dashed")
    for i, b_ in enumerate((b_cr, b_ac, b_dl, b_dd)):
        b_.place(cv, i * (bw + gap), ty)
    b_fa = Box(bw, "failed", sub="fix and create a new version", theme="red", size=19, sub_size=13, h=96)
    b_fa.place(cv, 0, ty + 96 + 70)
    connect(cv, b_cr, b_ac, a_side="right", b_side="left", label="ok", label_size=14, sw=3, gap=5)
    connect(cv, b_ac, b_dl, a_side="right", b_side="left", label="delete", label_size=14, sw=3, gap=5)
    connect(cv, b_dl, b_dd, a_side="right", b_side="left", sw=3, gap=5)
    connect(cv, b_cr, b_fa, a_side="bottom", b_side="top", label="error", label_size=14, sw=3, gap=5)
    n_v = Note(S(2) - bw - gap, "A version is an immutable snapshot of image or code, cpu/memory, env vars and protocols. Existing sessions stay on their original version, "
                                "and a session is bound to one version for its whole life. Deleting a version is not a rollback.", kind="info",
               title="What a version is", src=src("manage"))
    n_v.place(cv, bw + gap, ty + 96 + 70 - 10)
    # ---- draft versions + routing cards
    dr = card(C, "Draft versions", [
        "Create with draft: true; the version id is draft-{timestamp}",
        "Drafts are excluded from latest and from endpoint routing",
        "Promote by creating the version again without draft - it gets an integer version",
        "! Needs subscription enablement; otherwise the request silently creates a normal version",
    ], theme="orange", icon="preview-features", badge="preview", src=src("manage"))
    dr.place(cv, X(2), y)
    rt = card(C, "Endpoint routing", [
        "PATCH /agents/{name} (merge-patch) sets agent_endpoint.version_selector.version_selection_rules",
        "The manage page documents ONE FixedRatio rule at 100% (see Docs disagree)",
        "azd ai agent endpoint update patches endpoint and card without a new version; azd deploy applies endpoint settings - do not let it overwrite a pin",
        "POST /agents/{name}:disable or :enable turns the endpoint off or on",
    ], theme="green", icon="versions", src=src("manage", "epcli", "rest"))
    rt.place(cv, X(3), y)
    # ---- traffic splitting: two sides + the documented canary
    cv.text(X(4), y, "Docs disagree: traffic splitting", size=22, color=THEMES["orange"].deep)
    a = card(C, "One page says: no splitting", [
        "The concept, manage and configure-agent pages: the endpoint serves one version at 100%",
        "Traffic splitting between versions is not supported",
    ], theme="orange", fill="soft", src=src("manage", "hosted"))
    b = card(C, "Another page says: canary", [
        "The production page documents a canary: 90/10, then 50/50, then one rule at 100%",
        "azure.yaml agentEndpoint.versionSelector.versionSelectionRules: type FixedRatio, agentVersion, trafficPercentage; apply with azd ai agent endpoint update",
        "REST and SDK model: traffic_percentage; a blog says weighted rollouts",
    ], theme="orange", fill="soft", src=src("prod", "rest"))
    ah = max(a.h, b.h)
    a.place(cv, X(4), y + 40, h=ah)
    b.place(cv, X(4) + C + G, y + 40, h=ah)
    numbered(cv, X(4) + C + G / 2, y + 40 + ah / 2, "vs", theme="orange", d=34, size=15)
    cy_ = y + 40 + ah + 26
    cv.text(X(4), cy_, "The canary as the production page draws it (stable v1, candidate v2):", size=15, color=MUTED)
    cs = [("v1 100%", "stable only", "gray"), ("v1 90 / v2 10", "canary", "yellow"), ("v1 50 / v2 50", "ramp", "yellow"), ("v2 100%", "complete", "green")]
    cw_ = 250
    cgap = (S(2) - 4 * cw_) / 3
    cb = []
    for i, (t_, s_, th) in enumerate(cs):
        bx_ = Box(cw_, t_, sub=s_, theme=th, size=18, sub_size=13, h=70)
        bx_.place(cv, X(4) + i * (cw_ + cgap), cy_ + 30)
        cb.append(bx_)
    for i in range(3):
        connect(cv, cb[i], cb[i + 1], a_side="right", b_side="left", sw=3, gap=4)
    cv.text(X(4), cy_ + 30 + 70 + 10, "To go back, apply v1 at 100% again - no rebuild, no new version.", size=14, color=MUTED)
    n_ts = Note(S(2), "Plan for one version at 100% unless you verify weighted routing in your own environment. Both are Microsoft Learn pages (as of 2026-11-03), "
                      "so neither side can simply be dismissed.", kind="warn", title="Read it cautiously")
    n_ts.place(cv, X(4), cy_ + 30 + 70 + 40)
    yy = max(b_fa.y + b_fa.h, n_v.bottom, dr.bottom, rt.bottom) + 44

    # ---- the selector over time: three frames (left four columns; the traffic-splitting block sits on the right)
    ty_s = label(cv, 0, yy, "How the selector moves during a release - the endpoint serves whichever version it points at", size=24)
    FW = 790
    fb = []
    fb.append(_snapshot(cv, 0, ty_s, "1  Pin: production serves v3",
                        [("v1", "older", "gray", "solid"), ("v2", "older", "gray", "solid"), ("v3", "pinned", "green", "solid")], "v3"))
    fb.append(_snapshot(cv, FW + 20, ty_s, "2  Create v4, test it in a pinned session",
                        [("v1", "older", "gray", "solid"), ("v2", "older", "gray", "solid"), ("v3", "still serving", "green", "solid"),
                         ("v4", "candidate: active, not serving", "orange", "dashed")], "v3", test=True))
    fb.append(_snapshot(cv, 2 * (FW + 20), ty_s, "3  Promote: the selector moves to v4",
                        [("v1", "older", "gray", "solid"), ("v2", "older", "gray", "solid"), ("v3", "kept for rollback", "gray", "dashed"),
                         ("v4", "serving", "green", "solid")], "v4"))
    yy = max(max(fb), n_ts.bottom) + 46

    # ---- six-step safe release
    ty2 = label(cv, 0, yy, "Safe release in six steps - the candidate is never reachable from production until you promote it")
    steps = [
        ("1  Pin production", "Patch the selector to a concrete version so a new deploy cannot reach production by accident"),
        ("2  Create the candidate", "azd deploy or the API creates a new immutable version"),
        ("3  Verify it is active", "Poll the version status until active; failed means fix and create again"),
        ("4  Test in a pinned session", "Create a session with version_indicator set to the candidate and run your checks there"),
        ("5  Promote", "Patch version_selection_rules to the candidate"),
        ("6  Verify or roll back", "Check the endpoint; to roll back restore the previous selector. Deleting is not a rollback"),
    ]
    cards = [card(C, t, [("para", d)], theme="green", title_size=19) for t, d in steps]
    hmax = max(c.h for c in cards)
    for i, c in enumerate(cards):
        c.place(cv, X(i), ty2, h=hmax)
    for i in range(5):
        connect(cv, cards[i], cards[i + 1], a_side="right", b_side="left", sw=3, gap=4)
    return ty2 + hmax


class Code(Rect2):
    """Monospace snippet in a dashed note-like box (documented azure.yaml / config fragments)."""

    def __init__(self, w, title, lines, theme="gray", size=14, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.title, self.lines, self.size, self.pad, self.src = w, title, lines, size, pad, list(src)
        self.lh = metrics.line_ratio(metrics.MONO) * size
        self.src_lines = []
        h = pad + 24 + 8 + len(lines) * self.lh + pad
        for lab, url in self.src:
            self.src_lines.append((f"Learn: {lab}", url, h))
            h += 12 * metrics.line_ratio() + 2
        self.h = h + (4 if self.src else 0)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.soft, style="solid", sw=2, dash="dashed")
            cv.text(x + self.pad, y + self.pad, self.title, size=18, color=th.deep)
            cv.text(x + self.pad, y + self.pad + 32, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("code", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


# ================================================================================================ C  CI/CD
def band_cicd(cv: Canvas, y: float) -> float:
    y = head(cv, y, "C  CI/CD - one Foundry project per environment, one source revision, gate on evaluation, pin before you test",
             "azd pipeline config wires GitHub Actions or Azure DevOps; development, test and production are dependent jobs or stages running the same azd commands you run by hand.")
    gap = (W - 5 * C) / 4
    st = [
        card(C, "1  One-time setup", ["azd pipeline config creates the GitHub Actions or Azure DevOps pipeline",
                                       "Secrets: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_ENV_NAME, AZURE_LOCATION",
                                       "--no-prompt for scripts; --output json or raw"], theme="gray", icon="devops", src=src("cicd")),
        card(C, "2  Provision infrastructure", ["Bicep or Terraform, chosen with --infra; Terraform keeps remote state in a storage account",
                                                 "Each environment (development, test, production) binds to its own existing Foundry project - environment names alone do not isolate Azure resources",
                                                 "Each project needs its own dependencies and deployment permissions"], theme="grape", icon="workflow", src=src("cicd", "prod")),
        card(C, "3  Development", ["azd deploy <service> -e development",
                                    "azd ai agent show, then azd ai agent invoke ... --new-session --new-conversation",
                                    "Confirm the result and record the source commit"],
             theme="green", icon="builds", src=src("prod")),
        card(C, "4  Test: same commit", ["Check out the same commit; repeat the commands for test, then run regression and integration tests",
                                          "Evaluation gate: azd ai agent eval run; azd ai eval run start --fail-on pass-rate=0.8 fails the run below the threshold",
                                          "If code or dependencies change, repeat both environments' checks"],
             theme="violet", icon="monitor", src=src("cicd", "prod")),
        card(C, "5  Production: approve, then roll out", ["After approval, the same commit goes to production",
                                                          "Record the stable route and keep it at 100% while you deploy the candidate; then canary, test with azd ai agent invoke --version, ramp or return",
                                                          "Serialize production deployments and route changes"],
             theme="green", icon="versions", src=src("prod", "manage")),
    ]
    hmax = max(c.h for c in st)
    for i, c in enumerate(st):
        c.place(cv, i * (C + gap), y, h=hmax)
    for i in range(4):
        connect(cv, st[i], st[i + 1], a_side="right", b_side="left", label=["then", "then", "gate", "approve"][i], label_size=14, sw=3, gap=6)
    ny = y + hmax + 30
    n1 = Note(S(2), "GitHub Actions: dependent jobs for development, test and production, variables and secrets scoped to each GitHub environment, environment protection rules for "
                    "production approval. Azure DevOps: dependent stages with deployment jobs, service connections per stage, approvals and checks on the production environment. "
                    "Require approval before increasing the candidate's traffic share.", kind="info", title="Approvals in the two pipelines", src=src("prod", "cicd"))
    n1.place(cv, 0, ny)
    n2 = Note(S(2), "Endpoint-follows-latest is the default. If a pipeline deploys and only then tests, production can serve an untested version in between - "
                    "pin first, promote after the gate (section B). A canary needs the stable route configured before the candidate is deployed.", kind="gotcha",
              title="Pin first", src=src("cicd", "prod"))
    n2.place(cv, X(2), ny)
    n3 = Note(S(2), "Package and deploy the source separately for each environment instead of sharing one build artifact: promote the tested source revision and its dependency files. "
                    "An unchanged deployment can reuse an existing agent version. Configure the azd environment on every runner - local .azure settings are not transferred.",
              kind="tip", title="Per-environment builds", src=src("prod"))
    n3.place(cv, X(4), ny)
    ny2 = max(n1.bottom, n2.bottom, n3.bottom) + 22
    cd = Code(S(2), "The canary as azure.yaml (from the production page)", [
        "agentEndpoint:",
        "  versionSelector:",
        "    versionSelectionRules:",
        "      - type: FixedRatio",
        "        agentVersion: \"1\"",
        "        trafficPercentage: 90",
        "      - type: FixedRatio",
        "        agentVersion: \"2\"",
        "        trafficPercentage: 10",
    ], theme="orange", src=[("Deploy hosted agents to production", learn("agents/how-to/deploy-hosted-agent-production"))])
    cd.place(cv, 0, ny2)
    n4 = Note(S(2), "Apply with azd ai agent endpoint update <service> -e production and read it back with azd ai agent endpoint show; endpoint updates change routing without a new version. "
                    "The --version flag on azd ai agent invoke selects a version for a test session; it does not change the traffic percentages.",
              kind="info", title="Apply, read back, test", src=src("prod", "epcli"))
    n4.place(cv, X(2), ny2)
    n5 = Note(S(2), "Save the final routing configuration with the production release settings and use it as the starting point for the next deployment, "
                    "so a later pipeline run does not re-apply an outdated traffic split. azd >= 1.36.0 and azure.ai.agents >= 1.0.0-beta.20.",
              kind="warn", title="Do not re-apply an old split", src=src("prod", "deploy"))
    n5.place(cv, X(4), ny2)
    return max(cd.bottom, n4.bottom, n5.bottom)


# ================================================================================================ D  observe and debug
def band_observe(cv: Canvas, y: float) -> float:
    y = head(cv, y, "D  Logs, telemetry and debugging - from your laptop to the platform",
             "Test locally first, read the platform log stream second, then follow traces in Application Insights.")
    c1 = card(C, "Agent inspector (local only)", [
        "azd ai inspector opens a UI on localhost:8087 that talks to your agent on 8088",
        "The VS Code Foundry Toolkit includes an Agent Inspector with workflow visualization",
    ], theme="violet", icon="bug", src=src("inspector"))
    c2 = card(C, "azd ai agent doctor", [
        "Read-only checks of the local setup and the remote agent",
        "Exit code 0, 1 or 2 tells a script how it went",
        "Also used with the private ACR deploy path",
    ], theme="violet", icon="diagnostics", src=src("doctor"))
    c3 = card(C, "Run and invoke locally", [
        "azd ai agent run, then azd ai agent invoke --local",
        "! Local runs do not enforce isolation or user-isolated state stores",
    ], theme="violet", icon="vscode", src=src("debug", "cli"))
    c4 = card(C, "Platform log stream", [
        "GET .../versions/{v}/sessions/{id}:logstream returns SSE events: event: log with timestamp and stream (stdout, stderr or status)",
        "A stream lasts at most 30 minutes",
        "azd ai agent monitor [--follow] [--type system] [--tail N] [--session-id]",
    ], theme="violet", icon="log-analytics", src=src("logs"))
    c5 = card(C, "Telemetry", [
        "Protocol libraries bundle OpenTelemetry",
        "Application Insights (connection string injected) and OTLP (OTEL_EXPORTER_OTLP_ENDPOINT; header secret in a Custom-keys connection) can run in parallel",
        "service.name is fixed to the agent name - OTEL_SERVICE_NAME is ignored; sampling via OTEL_TRACES_SAMPLER",
    ], theme="violet", icon="app-insights", src=src("otel"))
    c6 = card(C, "Where to read it", [
        "Application Insights: Investigate > Transaction search or Performance",
        "Agent traces also show in the Foundry portal",
        "Readers need Log Analytics Reader (+ Privileged Monitoring Data Reader for protected tables)",
    ], theme="violet", icon="monitor", src=src("hosted", "perms"))
    _, rb = row(cv, 0, y, [c1, c2, c3, c4, c5, c6], gap=G)
    yy = rb + 50
    # ---- latency bar
    ty = label(cv, 0, yy, "Latency debug headers - where did the time go?", theme="violet", size=24)
    chips = [Chip("send x-ms-debug-latency-enabled: true", theme="violet", size=15, fill="soft"),
             Chip("x-ms-debug-latency-session-start-type: cold | warm | resume", theme="violet", size=15, fill="soft")]
    cx = 0
    for ch in chips:
        ch.place(cv, cx, ty)
        cx += ch.w + 14
    by = ty + 60
    seg = [("platform-preprocessing-ms", "admission, authentication, session lookup and orchestration; excludes VM provisioning and container readiness", "gray"),
           ("infra-setup-ms", "time to provision the micro-VM; omitted for warm requests", "yellow"),
           ("container-readiness-ms", "from micro-VM creation until the container reports ready; omitted for warm requests", "indigo"),
           ("container-response-ms", "proxy forwarding until response headers are committed: transfer, handling, retries, output-policy buffering", "green")]
    sw_ = (S(3) - 3 * 8) / 4
    boxes = []
    for i, (t, s_, th) in enumerate(seg):
        b_ = Box(sw_, t, sub=s_, theme=th, size=16, sub_size=13, h=130)
        b_.place(cv, i * (sw_ + 8), by)
        boxes.append(b_)
    bracket(cv, 0, S(3), by + 130 + 26)
    note_y = by + 130 + 46
    cap = cv.text(0, note_y, "The four add up to response-begin-ms: service acceptance until response headers are committed - not the first body byte. The best-effort trailer "
                             "x-ms-debug-latency-final (HTTP/2 or later) adds first_byte_ms and total_last_byte_ms. Diagnostic signals, not an SLA or billing metric; not emitted for failed "
                             "proxy responses or WebSocket requests. Segments are drawn evenly, not to scale.", size=14, color=MUTED, wrap=S(3))
    # ---- three cards under the latency strip
    cy2 = cap.bottom + 30
    hd = card(C, "Capture these when you file a bug", [
        "x-agent-session-id response header: the session ID to pass to :logstream - returned even on 424 and 500",
        "x-ms-region: the region that handled the call, useful in a support ticket",
        "The response id (for example caresp_...) to correlate the call with container logs and latency timings",
    ], theme="violet", icon="info-protection", src=src("code", "logs", "debug"))
    cold = card(C, "Reduce cold-start latency", [
        "Measure first: compare container-readiness-ms across several cold or resumed requests",
        "Install dependencies and compile code at image build time, never at container startup (Python compileall; .NET ReadyToRun publish)",
        "Multistage build: leave build tools, caches and tests out of the runtime image",
        "No model calls, migrations, tool discovery or asset downloads before /readiness; keep /readiness lean",
    ], theme="violet", icon="quotas", src=src("lat"))
    snap = card(C, "Memory snapshots", [
        "enableMemorySnapshot: true on a new version (maps to definition.enable_memory_snapshot, default false); versions are not edited in place",
        "Foundry starts a temporary instance, waits for readiness, captures the initialized process, and restores new sandboxes from that baseline",
        "azd >= 1.37.0, azure.ai.agents 1.0.0-beta.23 and AZD_ALPHA_ENABLE_AGENTS_MEMORY_SNAPSHOT=true; optional before-snapshot and after-restore hooks",
        "! Snapshot-enabled sessions do not keep $HOME, local files or process memory across idle - persist state externally",
        "A failed capture fails the version; a failed restore returns session_restore_failed",
    ], theme="violet", icon="gear", badge="azd alpha switch", src=src("snap"))
    _, hb = row(cv, 0, cy2, [hd, cold, snap], gap=G, equalize=False)
    pk = Note(S(3), "Source-zip mistakes that end in session_creation_failed or ModuleNotFoundError: wrapping the source in a folder (main.py must sit at the zip root), "
                    "putting raw .whl files in packages/ instead of extracted modules, bundling Windows binaries (.pyd, .dll) for a Linux runtime. "
                    "Build the bundle with pip install --target packages/ --platform manylinux2014_x86_64 --only-binary=:all:.",
              kind="gotcha", title="Packaging mistakes", src=src("code"))
    pk.place(cv, 0, hb + 22)
    # ---- troubleshooting (right): symptom -> cause and fix, as documented
    tt = Table([("Symptom", 300), "Likely cause and what to do (as documented)"], [
        [("401 Unauthorized", "violet"), "Missing or wrong-scope token: acquire one for https://ai.azure.com"],
        [("403 Forbidden", "violet"), "The caller lacks RBAC on the project: Foundry Agent Consumer (invoke only) or Foundry User (also develop)"],
        [("409 on create: name already exists", "violet"), "Update the existing agent (POST /agents/{name}) or pick a new name"],
        [("400 valid resource tier", "violet"), "cpu and memory are not an accepted pair (the docs disagree on the list - see the concepts canvas)"],
        [("400 version is still being provisioned", "violet"), "A new version is mid-deploy: poll its status until active, then retry"],
        [("Version failed", "violet"), "Read the version's error object first: error.code and error.message (the pip or NuGet error line for remote builds); logstream only works once the container starts"],
        [("Version stuck in creating > 10 min", "violet"), "Remote build could not resolve requirements.txt: switch to dependency_resolution bundled and prebuild"],
        [("424 session_not_ready", "violet"), "The container started but GET /readiness did not return 200 in time: stream the logs, fix the probe or the startup error, redeploy"],
        [("409 on delete: agent has active sessions", "violet"), "Wait for sessions to go idle, or delete with force=true to cascade-delete them"],
        [("409 AgentNotCodeBased on a code download", "violet"), "The agent is image-based: use the container deploy path"],
        [("Deploy fails in a private VNet", "violet"), "The firewall blocks required outbound endpoints: allow them, then redeploy"],
        [("429 quota or subnet", "violet"), "session_quota_exceeded, regional_session_quota_exceeded or subnet_exhausted: concurrent-session quota or delegated-subnet addresses used up"],
        [("400 content_filter, or 200 then SSE error", "violet"), "A guardrail blocked the input, or blocked streamed output"],
        [("502 on an Invocations agent with moderation", "violet"), "The buffered response was larger than 1 MB"],
        [("Slow: session start cold or resume, infra-setup-ms high", "yellow"), "The platform spent the time provisioning the micro-VM: compare several cold or resumed requests; if it persists, record the response ID, timestamp and latency headers for a support request"],
        [("Slow: container-readiness-ms high", "yellow"), "The container took long to start and report ready: add timestamps to startup logs and see Reduce cold-start latency"],
        [("Slow: platform-preprocessing-ms high", "yellow"), "The delay is in the platform before provisioning or readiness: open a support request with the response ID, timestamp, session start type and latency headers"],
        [("Slow: container-response-ms or first_byte_ms high", "yellow"), "The delay began after proxy forwarding: instrument the handler and inspect agent logs, model calls, tool calls, retries and output buffering"],
        [("session_restore_failed", "yellow"), "Memory snapshots: check the after-restore hook, current credentials and reconnections"],
    ], w=S(3), theme="violet", size=14, head_size=15, first_col_theme="violet", title="Troubleshooting: symptom to cause", title_size=22)
    tt.place(cv, X(3), yy)
    return max(pk.bottom, tt.bottom)


# ================================================================================================ E  guardrails
def band_guardrails(cv: Canvas, y: float) -> float:
    y = head(cv, y, "E  Guardrails on a hosted agent (preview) - four intervention points, one policy per agent",
             "Optional rai_config on the agent version. Where the policy applies depends on the protocol - and a bad policy ID fails open.")
    ty = y + 14
    cl = Box(380, "Client", theme="gray", icon="user", icon_pos="left", size=19, h=96)
    ag = Box(560, "Hosted agent", sub="your code + the model", theme="green", icon="agent", icon_pos="left", size=19, sub_size=14, h=130)
    tl = Box(420, "Tool or Toolbox", sub="MCP, OpenAPI, search ...", theme="orange", icon="toolbox", icon_pos="left", size=19, sub_size=14, h=96)
    cl.place(cv, 0, ty + 25)
    ag.place(cv, 380 + 200, ty)
    tl.place(cv, 380 + 200 + 560 + 200, ty + 17)
    pk = dict(num_theme="pink", sw=3, gap=6)
    connect(cv, cl, ag, a_side="right", b_side="left", ta=0.28, tb=0.28, num=1, label="user input", label_size=14, label_dy=-14, **pk)
    connect(cv, ag, cl, a_side="left", b_side="right", ta=0.78, tb=0.78, num=4, label="output", label_size=14, label_dy=-14, dash="dashed", **pk)
    connect(cv, ag, tl, a_side="right", b_side="left", ta=0.28, tb=0.3, num=2, label="tool call (preview)", label_size=14, label_dy=-14, **pk)
    connect(cv, tl, ag, a_side="left", b_side="right", ta=0.76, tb=0.78, num=3, label="tool response (preview)", label_size=14, label_dy=-14, dash="dashed", **pk)
    # behaviour table
    t = Table([("When", 260), "What happens"], [
        [("Policy attach", "pink"), "rai_config on the agent version: rai_policy_name; an omitted name means Microsoft.DefaultV2; one policy per agent"],
        [("Blocked input", "pink"), "HTTP 400 with content_filter"],
        [("Blocked streamed output", "pink"), "HTTP 200, then an SSE error event with content_filter"],
        [("Output filter modes", "pink"), "Default synchronous, or asynchronous - the stream stops a little later"],
        [("Bad policy ID", "pink"), "Fails OPEN: the agent is active and nothing is filtered"],
    ], w=S(3), theme="pink", size=14, head_size=15, first_col_theme="pink", title="Behaviour", title_size=22)
    t.place(cv, X(3), y)
    # protocol cards
    py = max(ty + 130, t.bottom) + 40
    p1 = card(C, "Responses", ["Attach the policy and you are done: the policy alone is enough",
                                "Four intervention points: user input, tool call (preview), tool response (preview) and output"],
              theme="pink", icon="content-safety", badge="preview", src=src("gc", "gh"))
    p2 = card(C, "Invocations", ["The policy is not enough on its own: add invocations_moderation",
                                  "! Without invocations_moderation nothing is screened",
                                  "response_mode: non_streaming, streaming or both"], theme="pink", icon="content-safety", badge="preview", src=src("gc", "gh"))
    p3 = card(C, "Invocations: paths and limits", ["input_paths and output_paths pick the JSON fields to screen; stream_selectors for streamed events",
                                                    "A request over 2 MB goes unscreened; a buffered response over 1 MB returns 502; text over 10,000 characters is truncated"],
              theme="pink", icon="content-safety", src=src("gh"))
    p4 = card(C, "Invocations (WebSocket)", ["! Guardrails are not available on this protocol",
                                              "Moderate inside your own code if you need it"], theme="red", icon="content-safety", src=src("gc"))
    p5 = Note(S(2), "Guardrails for hosted agents are a preview. The tool-call and tool-response intervention points are preview within it. A wrong policy ID does not stop the deploy: "
                    "the agent comes up active with no filtering - test with a known-bad prompt after every change.", kind="preview", title="Preview and fail-open",
              src=src("gc", "gh"))
    _, rb = row(cv, 0, py, [p1, p2, p3, p4], gap=G)
    p5.place(cv, X(4), py)
    return max(rb, p5.bottom)


# ================================================================================================ F  long running
def band_longrunning(cv: Canvas, y: float) -> float:
    y = head(cv, y, "F  Long-running, resilient agents (preview) - survive crashes, steer, cancel, wait for a human, reconnect",
             "Three different things are easy to confuse: background work, resilient execution and stream replay. Each solves a different failure.")
    k1 = card(C, "Background", ["background: true - work continues after the request returns; the platform manages polling and cancellation",
                                 "! On its own it does not recover from a process crash"], theme="gray", icon="scheduler", src=src("lr"))
    k2 = card(C, "Resilient execution", ["Durable work identity, persisted input, a lease that detects a lost process, and handler re-entry",
                                          "Not deterministic replay: your handler decides what to redo"], theme="green", icon="agent", badge="preview", src=src("lr", "lrr"))
    k3 = card(C, "Stream replay", ["Cursor-based replay of a response stream to a reconnecting client",
                                    "! Not a checkpoint: it replays events, not your state"], theme="cyan", icon="log-analytics", badge="preview", src=src("lr", "reconnect"))
    row(cv, 0, y, [k1, k2, k3], gap=G)
    opt = Table([("Protocol", 180), ("How you opt in", 560), "What is covered"], [
        [("Responses", "green"), "ResponsesServerOptions(resilient_background=True)",
         "Only stored background responses (store=true, background=true). Foreground responses are marked failed on a crash; without the opt-in, background responses fail with server_error"],
        [("Invocations", "green"), "set_resilient_tasks_enabled(True) with @task or @multi_turn_task(steerable=...)", "Tasks carry the work identity; you choose the recovery strategy"],
        [("Minimum SDK", "green"), "core and responses >= 2.0.0 (Python), >= 1.0.0 (.NET)", "Defaults: default_fetch_history_count 100, shutdown_grace_period_seconds 10"],
    ], w=S(3), theme="green", size=14, head_size=15, first_col_theme="green", title="How you turn it on", title_size=22)
    opt.place(cv, X(3), y)
    yy = max(k1.bottom, k2.bottom, k3.bottom, opt.bottom) + 50

    # ---- crash recovery sequence (left)
    ty = label(cv, 0, yy, "Crash recovery of a background response", size=24)
    seq = Sequence(cv, 0, ty, [("Process A (original)", "green", "container-apps"), ("Client", "gray", "user"), ("Process B (new)", "green", "container-apps")],
                   spacing=520, head_w=340, head_h=60, step=62, size=16, label_size=15)
    seq.msg(1, 0, "POST /responses with store=true and background=true", num=1)
    for actor, n, text in ((0, 2, "The handler runs and holds a lease on the work"), (0, 3, "Process lost: crash or restart"),
                           (2, 4, "The lease expires and another process reclaims the work"),
                           (2, 5, "Handler re-entered with entry_mode = recovered: restore your checkpoint")):
        sy = seq.msg(actor, actor, text)
        numbered(cv, seq._cx(actor) - 28, sy + 15, n, theme="green", d=26, size=15)
    seq.msg(1, 2, "GET /responses/{id}?stream=true&starting_after=<seq>", num=6)
    seq.msg(2, 1, "Events after the cursor, then live events", dash="dashed", num=7)
    sb = seq.end()
    # ---- right: cards
    w1 = card(C, "Work model and retries", [
        "A unit of work has a work identity and an input identity",
        "entry_mode is fresh, resumed or recovered",
        "Strategies: safe rerun, response checkpoints, upstream-owned resume, side-effect watermarks (persist before a non-repeatable operation)",
        "RetryPolicy: initial_delay, backoff_coefficient >= 1, max_delay, max_attempts; crash recovery does not use up retries",
        "Task input about 10 MiB (InputTooLarge); status Pending, InProgress, Suspended, Completed",
    ], theme="green", icon="gear", badge="preview", src=src("lrr", "taskstate"))
    w2 = card(C, "Steerable conversations", [
        "steerable_conversations=True queues a new turn instead of returning 409 conversation_locked",
        "The running handler is cancelled cooperatively - watch ctx.pending_input_count",
        "SteeringQueueFull when the queue is full; if_last_input_id is a precondition",
    ], theme="green", icon="workflow", badge="preview", src=src("steer", "lrr"))
    w3 = card(C, "Cancel a turn", [
        "Responses: POST /responses/{id}/cancel - background responses only; your handler sees context.client_cancelled",
        "Invocations: the cancel route returns 404 unless you register @app.cancel_invocation_handler",
    ], theme="green", icon="scheduler", badge="preview", src=src("cancel"))
    w4 = card(C, "Human in the loop", [
        "A multi-turn chain stays suspended between turns - minutes to days - and survives restarts",
        "Frameworks use their own interrupt plus a checkpoint",
    ], theme="teal", icon="users", badge="preview", src=src("hitl"))
    w5 = card(S(2), "Stream with reconnect", [
        "Each turn has a stream ID; you choose the replay store: use_in_memory_live() (default), use_in_memory_replay(cursor_fn, ttl) or use_file_backed_replay(dir, cursor_fn)",
        "Reconnect with GET /responses/{id}?stream=true&starting_after=<seq>; a later response.in_progress event is a snapshot reset - replace what you rendered",
    ], theme="cyan", icon="log-analytics", badge="preview", src=src("reconnect"))
    _, b1 = row(cv, X(3), ty, [w1, w2, w3], gap=G, equalize=False)
    _, b2 = row(cv, X(3), b1 + 28, [w4], gap=G)
    w5.place(cv, X(3) + C + G, b1 + 28)
    yy = max(sb, b2, w5.bottom) + 50

    # ---- state store
    ty = label(cv, 0, yy, "Durable state store - key-value storage for the state that must outlive the container", size=24)
    ss = card(S(2), "FoundryStateStore", [
        "FoundryStateStore.get_or_create(name, user_isolation=True): fetch the store, or create it on first use; options apply only at creation",
        "Server-backed key-value storage for JSON; survives crashes, restarts and idle eviction. Your agent writes it explicitly - the platform never fills it",
        "Available only to hosted agents; the store name is its identity and cannot be changed later",
        "Item idle window defaults to 30 days; writes renew it, reads do not, and a store can be set to never expire items",
        "CLI: azd ai agent state-stores ...",
    ], theme="cyan", icon="storage", src=src("state", "taskstate"))
    ss.place(cv, 0, ty)
    keep = card(C, "What to keep in it", [
        "Framework checkpoints (LangGraph, Agent Framework)",
        "Conversation history your agent manages itself - the Invocations case",
        "Generated artifacts and intermediate work for later turns",
        "Per-user profiles and preferences",
        "Large binaries belong in blob storage, with a reference in the store",
    ], theme="cyan", icon="cosmos", src=src("state"))
    keep.place(cv, X(2), ty)
    part = card(C, "Partitioning and caller identity", [
        "Partition by store name (a hierarchy with / is fine) or by end user with user_isolation=True",
        "! Do not put an end-user ID in a store name - names show up in logs; use user isolation",
        "The user is resolved from x-agent-foundry-call-id (the SDKs forward it); deferred work needs the call ID passed explicitly",
        "Local runs cannot enforce user isolation - test it on a deployed agent",
    ], theme="cyan", icon="users", src=src("state"))
    part.place(cv, X(3), ty)
    items = card(C, "Items", [
        "A key plus a JSON value, with optional string tags (matched with AND when listing)",
        "Listing returns keys only; fetch values as a second step",
        "Every item has an ETag: use If-Match for read-modify-write; append-only checkpoints with fresh keys need none",
    ], theme="cyan", icon="files", src=src("state"))
    items.place(cv, X(4), ty)
    lim = Table([("Item", 190), "Limit (400 Bad Request names the field)"], [
        ["Store name", "1-128 characters"], ["Item key", "1-128 characters"], ["Item value", "up to 1 MB of JSON"],
        ["Tags", "up to 16 (key 1-64, value up to 256)"], ["Description", "up to 1,024 characters"],
        ["List page", "1-100 keys (default 20)"],
    ], w=C, theme="cyan", size=14, head_size=15, first_col_theme="cyan", title="Limits", title_size=22)
    lim.place(cv, X(5), ty - 40 + 40)
    yy = max(ss.bottom, keep.bottom, part.bottom, items.bottom, lim.bottom) + 28
    cmd = card(S(2), "Try it from the CLI", [
        "azd ai agent invoke --long-running --no-wait",
        "azd ai agent invocations show --id <id>   |   azd ai agent invocations follow --id <id>",
    ], theme="gray", icon="builds", src=src("resil", "recover"))
    cmd.place(cv, 0, yy)
    pv = Note(S(4), "Preview as of 2026-11-03: resilient execution, stream replay, steering, cancel and human-in-the-loop. The durable state store page carries no preview banner. "
                    "Resilience is opt-in - without it a crashed foreground response is marked failed.", kind="preview", title="Preview status", src=src("lr", "state"))
    pv.place(cv, X(2), yy)
    yy = max(cmd.bottom, pv.bottom) + 50

    # ---- which mechanism for which problem
    ty = label(cv, 0, yy, "Which mechanism for which problem", size=24)
    mt = Table([("Problem", 560), ("Mechanism", 700), "Where it applies"], [
        [("The client loses its connection mid-stream", "green"), "Stream replay: reconnect with starting_after=<seq>",
         "Responses streams; you choose the replay store (live in-memory, in-memory replay or file-backed replay)"],
        [("The hosting process crashes or restarts mid-work", "green"), "Resilient execution: the lease detects the lost process and the handler is re-entered",
         "Stored background responses (store=true, background=true) with resilient_background=True; Invocations tasks with resilient tasks enabled"],
        [("A new user message arrives while the agent is working", "green"), "Steerable conversations: the new turn is queued and the running handler is cancelled cooperatively",
         "steerable_conversations=True, or @multi_turn_task(steerable=...) for Invocations; otherwise 409 conversation_locked"],
        [("The user wants to stop", "green"), "Cancel the turn", "POST /responses/{id}/cancel (background only); on Invocations register @app.cancel_invocation_handler or get 404"],
        [("The agent needs a human decision", "green"), "Human in the loop: the multi-turn chain is suspended between turns", "Minutes to days, survives restarts; frameworks use interrupt + checkpoint"],
        [("State must outlive the process and the compute", "green"), "Durable state store", "FoundryStateStore; framework checkpoints can be kept there"],
    ], w=S(4), theme="green", size=14, head_size=15, first_col_theme="green")
    mt.place(cv, 0, ty)
    tp = Note(S(2), "The handler is re-entered, not replayed. Decide for every step whether it is safe to run twice, and persist a watermark before any operation that cannot be repeated.",
              kind="tip", title="Design for re-entry", src=src("lrr", "recover"))
    tp.place(cv, X(4), ty)
    return max(mt.bottom, tp.bottom)


# ================================================================================================ G  roles and migration
def band_roles(cv: Canvas, y: float) -> float:
    y = head(cv, y, "G  Roles for operators, and migrating off the initial preview",
             "Registry and telemetry roles live here; deploy and invoke roles are on the concepts canvas.")
    t = Table([("Who", 250), ("Needs", 560), "Why"], [
        [("Project managed identity", "red"), "Container Registry Repository Reader (or AcrPull) on the ACR", "The platform pulls your image with it; it is not the agent's runtime identity"],
        [("Deployer on ACR", "red"), "Container Registry Repository Writer (or AcrPush)", "Push the image; the ACR also needs azureADAuthenticationAsArmPolicy enabled"],
        [("Deployer on the project", "red"), "Foundry Project Manager at project scope", "Create agents and versions; ARM roles such as Owner or Contributor carry no data-plane rights"],
        [("Telemetry reader", "red"), "Log Analytics Reader (+ Privileged Monitoring Data Reader for protected tables)", "Query traces and logs behind Application Insights"],
        [("Teams publisher", "red"), "Microsoft.BotService/* permissions (Owner or Contributor)", "Publishing through Azure Bot Service"],
    ], w=S(4), theme="red", size=14, head_size=15, first_col_theme="red", title="Operator roles", title_size=22)
    t.place(cv, 0, y)
    mg = card(S(2), "Migrating from the initial preview", [
        "Agents on the initial public-preview hosting backend (deployed before April 2026; azure-ai-agentserver-agentframework / -langgraph adapters) are not auto-migrated",
        "! Support for that backend ended on 2026-08-20 - already past",
        "What changed: automatic compute lifecycle, session isolation, protocol libraries, a dedicated identity and endpoint per agent, no capability-host creation",
        "Needs azure-ai-projects >= 2.3.0; the az cognitiveservices agent ... commands were removed",
    ], theme="gray", icon="gear", badge="Ended 2026-08-20", src=src("migrate"))
    mg.place(cv, X(4), y)
    return max(t.bottom, mg.bottom)


# ================================================================================================ build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Hosted agents: deploy and operate",
        "Deploy paths, versions and safe rollout, CI/CD, logs and debugging, guardrails and long-running resilient agents  |  companion to 'Hosted agents'  |  as of 2026-11-03",
        icon="foundry", w=W)
    y = bottom + 26
    lg = legend(cv, 0, y, [("Agents and platform", "green"), ("Models", "blue"), ("Tools and toolbox", "orange"), ("Identity and security", "red"),
                           ("Memory and knowledge", "teal"), ("Observability", "violet"), ("Guardrails", "pink"), ("Networking", "indigo"),
                           ("State and data", "cyan"), ("Governance and IaC", "grape")], size=15, gap=22)
    bx = lg.right + 34
    draw_badge(cv, bx, y - 1, "preview")
    cv.text(bx + 84, y, "preview feature (as of 2026-11-03)", size=15)
    y += 36
    cv.text(0, y + 4, "Related canvases:", size=15, color=MUTED)
    x = 160
    for lab in ["Hosted agents: your code on Foundry's runtime", "Foundry Agent Service: the map", "Prompt agents in depth", "Hosted agent runtime: how a container becomes an agent endpoint",
                "AgentOps lifecycle", "Foundry Observability: one data model", "Guardrails and controls", "Agent Service disaster recovery"]:
        ch = Chip(lab, theme="gray", size=14, fill="soft")
        ch.place(cv, x, y)
        x += ch.w + 12
    y += 56
    tiles = [
        Tile(C, "7 ways in", "azd, source zip, container image to ACR, private ACR, BYO registry, Terraform AzAPI, REST or SDK. Every one creates a new immutable agent version.", "green"),
        Tile(C, "Pin, then test", "The endpoint follows the latest version by default: deploy-then-test can change production before the tests run.", "red"),
        Tile(C, "250 MB zip", "Source-zip limit (flat root). remote_build installs dependencies for you; bundled ships them prebuilt.", "gray"),
        Tile(C, "30 min stream", "A log stream (SSE) lasts at most 30 minutes; azd ai agent monitor follows it for you.", "violet"),
        Tile(C, "3 previews", "Draft versions, hosted-agent guardrails and long-running resilience are marked Preview in the docs.", "orange"),
        Tile(C, "Fails open", "A guardrail policy with a bad ID leaves the agent active with no filtering at all.", "pink"),
    ]
    _, y = row(cv, 0, y, tiles, gap=G)
    GAPB = 50
    y = band_deploy(cv, y + 56) + GAPB
    y = band_versions(cv, y) + GAPB
    y = band_cicd(cv, y) + GAPB
    y = band_observe(cv, y) + GAPB
    y = band_guardrails(cv, y) + GAPB
    y = band_longrunning(cv, y) + GAPB
    y = band_roles(cv, y) + GAPB
    sources(cv, 0, y, [
        ("Deploy a hosted agent", U["deploy"][1]), ("Deploy from source code", U["code"][1]),
        ("Deploy with Terraform", U["tf"][1]), ("Deploy from a private ACR", U["privacr"][1]),
        ("Private registry connections", U["byo"][1]), ("Deploy hosted agents to production", U["prod"][1]),
        ("Set up CI/CD with the CLI", U["cicd"][1]), ("Manage hosted agents", U["manage"][1]),
        ("Debug a hosted agent", U["debug"][1]), ("Monitor hosted agent logs", U["logs"][1]),
        ("Agent inspector", U["inspector"][1]), ("Agent doctor", U["doctor"][1]),
        ("Hosted agent guardrails", U["gc"][1]), ("Resilience for long-running hosted agents", U["lr"][1]),
        ("Durable state store", U["state"][1]), ("Enable memory snapshots for hosted agents", U["snap"][1]),
    ], w=W, cols=4)
