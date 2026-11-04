"""CI/CD and infrastructure as code for Foundry: pipeline swim-lanes with gates, API surfaces, IaC options, azd, evaluation gates, quota-aware deployment, ACR and rollout."""
from __future__ import annotations

from generator.xd import *

META = dict(
    id="cicd-and-iac", title="CI/CD and infrastructure as code", section="6", order=2,
    description="A ten-station pipeline with platform, app and gate lanes; which API surface each artefact lives on; Bicep, Terraform and azd; evaluation gates, quota-aware deployment, ACR options and rollout.",
    tags=["cicd", "iac", "azd", "bicep", "terraform", "gates"],
)

W = 3100
ASOF = "as of 2026-11-03"

S = dict(
    cicd=("Set up CI/CD for hosted agents (preview)", learn("agents/how-to/set-up-ci-cd-cli")),
    prod=("Promote hosted agents to production (preview)", learn("agents/how-to/deploy-hosted-agent-production")),
    tf=("Deploy a hosted agent with Terraform", learn("agents/how-to/deploy-hosted-agent-terraform")),
    acr=("Hosted agents with a private Azure Container Registry", learn("agents/how-to/deploy-hosted-agent-private-azure-container-registry")),
    ext=("Install the azd Foundry extensions", learn("agents/how-to/install-cli-foundry-extensions")),
    gha=("Evaluation GitHub Action (preview)", learn("how-to/evaluation-github-action")),
    ado=("Evaluation in Azure DevOps (preview)", learn("how-to/evaluation-azure-devops")),
    azdeval=("Evaluate with the Azure Developer CLI (preview)", learn("observability/how-to/azure-developer-cli-evaluation")),
    tmpl=("Create a Foundry resource with a template", learn("how-to/create-resource-template")),
    tfres=("Create a Foundry resource with Terraform", learn("how-to/create-resource-terraform")),
    quota=("Automate quota-aware deployments", learn("openai/how-to/automate-quota-deployments")),
    spill=("Spillover traffic management", learn("openai/how-to/spillover-traffic-management")),
    std=("Standard agent setup", learn("agents/concepts/standard-agent-setup")),
    hosted=("Hosted agents", learn("agents/concepts/hosted-agents")),
    manage=("Manage hosted agents", learn("agents/how-to/manage-hosted-agent")),
    policy=("Model deployment policy", learn("how-to/model-deployment-policy")),
    arch=("Baseline Foundry chat architecture", learn("azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat", base="")),
    evals_repo=("microsoft/ai-agent-evals (GitHub)", "https://github.com/microsoft/ai-agent-evals"),
    samples=("microsoft-foundry/foundry-samples (infrastructure)", "https://github.com/microsoft-foundry/foundry-samples"),
)


def src(*keys: str) -> list:
    return [S[k] for k in keys]


# ---------------------------------------------------------------------------------------------- helpers
def pill(cv: Canvas, x: float, y: float, text: str, theme: str, size: int = 14, dashed: bool = False,
         solid: bool = True) -> float:
    th = THEMES[theme]
    tw, thh = text_size(text, size)
    cv.rect(x, y, tw + 18, thh + 8, stroke=th.stroke, fill=th.fill if solid else "transparent", style="solid", sw=1.5,
            rough=0, dash="dashed" if dashed else "solid")
    cv.text(x + 9, y + 4, text, size=size, color=th.deep)
    return tw + 18


def head(cv: Canvas, y: float, n, text: str, sub: str | None = None, tags=(), x: float = 0, w: float = W) -> float:
    _, bottom = section_header(cv, x, y, f"{n}   {text}", sub=sub, size=32, w=w)
    tx = x + w
    for label, theme, dashed in reversed(tags):
        wpx = text_size(label, 15)[0] + 18
        tx -= wpx
        pill(cv, tx, y + 8, label, theme, 15, dashed, solid=not dashed)
        tx -= 14
    return bottom + 22


DOC = ("Documented", "green", False)
SUG = ("Suggested shape - our synthesis", "orange", True)
PREV = ("Preview", "orange", False)


def learn_line(cv: Canvas, x: float, y: float, items: list[tuple[str, str]]) -> float:
    cx = x
    for label, url in items:
        t = cv.text(cx, y, f"Learn: {label}", size=12, color=LINK, link=url)
        cx += t.w + 26
    return y + 18


class Code(Rect2):
    """Monospace snippet in a dashed box (settings the docs call out; not a verbatim sample)."""

    def __init__(self, w, title, lines, theme="gray", size=14, pad=14, src=(), note=None):
        self.th = THEMES[theme]
        self.w, self.title, self.lines, self.size, self.pad, self.src = w, title, lines, size, pad, list(src)
        self.note = note
        self.lh = metrics.line_ratio(metrics.MONO) * size
        self.t_lines = wrap_text(title, w - 2 * pad, 18)
        h = pad + len(self.t_lines) * 18 * metrics.line_ratio() + 10 + len(lines) * self.lh + pad
        self.n_lines = wrap_text(note, (w - 2 * pad) * 0.965, 14) if note else []
        if self.n_lines:
            h += len(self.n_lines) * 14 * metrics.line_ratio() + 8
        self.src_lines = []
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
            ty = y + self.pad
            cv.text(x + self.pad, ty, "\n".join(self.t_lines), size=18, color=th.deep)
            ty += len(self.t_lines) * 18 * metrics.line_ratio() + 10
            cv.text(x + self.pad, ty, "\n".join(self.lines), size=self.size, color=INK, font=metrics.MONO)
            ty += len(self.lines) * self.lh + 8
            if self.n_lines:
                cv.text(x + self.pad, ty, "\n".join(self.n_lines), size=14, color=MUTED)
            for txt, url, off in self.src_lines:
                cv.text(x + self.pad, y + off, txt, size=12, color=LINK, link=url)
        cv.register("code", x, y, self.w, H)
        return self

    @property
    def bind_target(self):
        return None


def card(w, title, body, theme, icon=None, keys=(), badge=None, fill="hatch", **kw):
    return Card(w, title, body, theme=theme, icon=icon, src=src(*keys), badge=badge, fill=fill, **kw)


# ---------------------------------------------------------------------------------------------- 0. summary
def summary(cv: Canvas, y: float) -> float:
    cw = (W - 4 * 30) / 5
    cards = [
        card(cw, "Two owners, two surfaces", [
            "= 'A platform team can own the Foundry account, project, model deployments, guardrail policies, connections, and monitoring. An application team can own the agent code, container image, and logical agent definition.'",
        ], "grape", "template-specs", ("cicd",)),
        card(cw, "azd is the glue", [
            "= azd pipeline config generates the GitHub Actions or Azure DevOps pipeline.",
            "= The default flow is azd provision then azd deploy, the same as azd up locally. azd owns hosted-agent versions.",
        ], "green", "azd", ("cicd",), badge="preview"),
        card(cw, "Gate on evidence", [
            "= The quick eval can't enforce thresholds. The optional azd evaluation extension adds --fail-on pass-rate=0.8.",
            "= The GitHub Action and the Azure DevOps task add pairwise comparison against a baseline.",
        ], "violet", "metrics", ("azdeval", "gha"), badge="preview"),
        card(cw, "Pin before you test", [
            "= By default the endpoint follows the latest version, so a deploy-then-test pipeline can change production before the tests run.",
            "= Pin the stable version first.",
        ], "red", "versions", ("cicd", "prod")),
        card(cw, "Mostly preview", [
            f"= Most azd, CI/CD and evaluation pages are marked preview: no SLA ({ASOF}).",
            "= Re-check the pages before you standardise on them.",
        ], "orange", "preview-features", ("ext",)),
    ]
    _, bottom = row(cv, 0, y, cards, gap=30)
    return bottom + 56


# ---------------------------------------------------------------------------------------------- 1. pipeline railway
LANE_TH = ["grape", "green", "gray"]


def pipeline(cv: Canvas, y: float) -> float:
    y = head(cv, y, 1, "The pipeline: ten stations, three lanes, four gates",
             sub="Read left to right. The stations and lanes are our synthesis of the cited pages; every command and gate shown is documented.",
             tags=(DOC, SUG))
    X0, PITCH, BW = 220, 290, 254
    lane_h = [200, 220, 270]
    ly = [y]
    for h in lane_h[:-1]:
        ly.append(ly[-1] + h + 12)
    names = [("Platform team", "IaC: account, project, deployments, policy, monitoring"),
             ("App team", "agent code, image, agent definition, eval recipe"),
             ("Gates", "what stops a bad release")]
    for i in range(3):
        th = THEMES[LANE_TH[i]]
        cv.rect(0, ly[i], W, lane_h[i], stroke=th.stroke, fill=th.soft, style="solid", sw=1.5, dash="dotted", rough=0, round_=False)
        Box(176, names[i][0], h=lane_h[i] - 24, theme=LANE_TH[i], sub=names[i][1], size=20, sub_size=14).place(cv, 12, ly[i] + 12)

    def st(col, lane, n, title, sub, theme, dashed=False):
        h = 156
        return Box(BW, f"{n}  {title}", h=h, theme=theme, sub=sub, size=18, sub_size=14,
                   dash="dashed" if dashed else "solid").place(cv, X0 + col * PITCH, ly[lane] + (lane_h[lane] - h) / 2)

    s1 = st(0, 1, 1, "Source + IaC lint", "commit code, infra/, azure.yaml, eval.yaml; code review", "green")
    s2 = st(1, 0, 2, "Platform apply (rare)", "Terraform or Bicep: account, project, deployments, connections, policy", "grape", dashed=True)
    s3 = st(2, 1, 3, "Build", "linux/amd64 image: local, ACR remote build or a pre-built digest", "green")
    s4 = st(3, 1, 4, "Deploy to dev", "azd provision, azd deploy: a new hosted-agent version; wait for active", "green")
    s5 = st(4, 1, 5, "Evaluate", "eval run (smoke), then eval run start --fail-on pass-rate=0.8", "green")
    s6 = st(5, 1, 6, "Safety", "AI Red Teaming Agent scan (cloud)", "green")
    s7 = st(6, 1, 7, "Deploy to test", "same commit; regression and integration tests", "green")
    s8 = st(7, 1, 8, "Approval", "environment protection rules, or approvals and checks, on production", "green")
    s9 = st(8, 1, 9, "Prod rollout", "pin stable, deploy candidate, test with --version, canary, ramp or roll back", "green")
    s10 = st(9, 0, 10, "Post-deploy", "continuous and scheduled evaluation, alerts, dashboard", "grape")
    chain = [s1, s3, s4, s5, s6, s7, s8, s9]
    for a, b in zip(chain, chain[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=4)
    connect(cv, s2, s4, a_side="right", b_side="top", route="elbow", dash="dashed", color="#9c36b5", sw=2,
            label="base infrastructure must exist first", label_size=14, label_pos="above")
    connect(cv, s9, s10, a_side="top", b_side="left", route="elbow", sw=3, gap=4)
    # gates
    gates = [(s5, "Eval gate", "violet", "fails the run below the threshold, for example pass-rate 0.8"),
             (s6, "Red-team gate", "pink", "the cloud red-team scan must pass before the test environment"),
             (s8, "Manual approval", "grape", "GitHub environment protection rules, or Azure DevOps approvals and checks"),
             (s9, "Canary gate", "green", "keep the stable version until the candidate is accepted")]
    for stn, label, th_name, cap in gates:
        dia = Box(176, label, shape="diamond", theme=th_name, size=17, h=124)
        dia.place(cv, stn.cx - 88, ly[2] + 18)
        arrow(cv, [(stn.cx, stn.bottom + 4), (stn.cx, dia.y - 4)], dash="dotted", end_head=None, color=THEMES[th_name].stroke, sw=2)
        cv.text(stn.cx - BW / 2, dia.bottom + 8, wrap(cap, BW, 14), size=14, color="#343a40", align="center", w=BW)
    return ly[2] + lane_h[2] + 44


def wrap(text: str, width: float, size: float) -> str:
    return "\n".join(wrap_text(text, width, size))


def stage_table(cv: Canvas, y: float) -> float:
    cv.text(0, y, "Stations in detail: what runs, and what gates it", size=24, color=INK)
    y += 40
    G = THEMES
    rows = [
        [("1", "green"), "Source + IaC lint", "Commit code + infra/ + azure.yaml + eval.yaml; code review", "Branch policy"],
        [("2", "grape"), "Platform apply (rare)",
         "Terraform or Bicep for the Foundry account, project, model deployments (quota-checked), connections, guardrail policy, registry connection, identities and RBAC, and monitoring",
         "Plan review; serialize writers; remote state per environment"],
        [("3", "green"), "Build",
         "linux/amd64 container. Local build (needs AcrPush) or ACR remote build (default docker.remoteBuild: true; needs Container Registry Tasks Contributor; ABAC registries need Repository Writer, or Owner or Contributor). Or source-code deploy (azd deploy uploads a source package). Or a pre-built image from a separate scan and sign pipeline (image: in azure.yaml, pinned to a @sha256: digest).",
         "Vulnerability scan and signing, if a separate pipeline builds the image"],
        [("4", "green"), "Deploy to dev",
         "azd provision --no-prompt, then azd deploy --no-prompt: a new hosted-agent version. Wait for active; azd ai agent show --output json; invoke with --new-session --new-conversation.",
         "Readiness is not correctness: run an app-level smoke test that checks expected content"],
        [("5", "green"), "Evaluate",
         "azd ai agent eval run (smoke), then azd ai eval run start --fail-on pass-rate=0.8 (needs the azure.ai.evaluations extension), or microsoft/ai-agent-evals@v3-beta, or AIAgentEvaluation@2 (CI + pairwise significance versus a baseline).",
         ("Eval gate", "violet")],
        [("6", "green"), "Safety", "AI Red Teaming Agent scan (cloud)", ("Red-team gate", "pink")],
        [("7", "green"), "Deploy to test", "Same commit or source revision; regression and integration tests. Source is deployed separately per environment, not as one shared artefact.", "Test results"],
        [("8", "green"), "Approval", "GitHub environment protection rules, or Azure DevOps approvals and checks, on production", ("Manual approval", "grape")],
        [("9", "green"), "Prod rollout",
         "Capture the current routing -> pin stable at 100% via agentEndpoint.versionSelector (azd ai agent endpoint update) -> azd deploy the candidate -> test with --version N -> canary 10% -> ramp -> 100%, or roll back to stable.",
         ("Canary gate: keep stable until the candidate is accepted", "green")],
        [("10", "grape"), "Post-deploy", "Continuous and scheduled evaluation, alerts and the dashboard (see the monitoring canvas)", "Alerts"],
    ]
    TW = 2330
    t = Table([("#", 54), ("Station", 230), ("What runs", 1450), ("Gate or evidence", 596)], rows, w=TW, theme="gray", size=14, head_size=15)
    t.place(cv, 0, y)
    fl = card(W - TW - 40, "Five flows through the stations", [
        "Platform PR: plan, then apply the base infrastructure (account, project, a model deployment after the quota and capacity check, guardrail policy, registry connection, identity and RBAC). Station 2",
        "App PR: build and push the image, azd deploy to dev, readiness, smoke test, eval gate, red-team gate. Stations 1 and 3 to 6",
        "Same commit: test environment, regression tests, approval. Stations 7 and 8",
        "Production: pin stable, deploy the candidate, test with --version, canary 10%, inspect, ramp, then done or roll back. Station 9",
        "After release: record the commit, image digest, version, routing configuration and the dataset and evaluator versions. Station 10",
    ], "gray", "workflow", ("cicd", "prod"), title_size=21)
    fl.place(cv, TW + 40, y)
    return max(learn_line(cv, 0, t.bottom + 8, src("cicd", "prod", "ext", "azdeval", "acr")), fl.bottom) + 50


# ---------------------------------------------------------------------------------------------- 2. surfaces
def surfaces(cv: Canvas, y: float) -> float:
    y = head(cv, y, 2, "What lives where: owners, API surfaces and deploy tools",
             sub="Which team owns each artefact, which API surface it lives on, and what you deploy it with.", tags=(DOC,))
    top = y
    pw = 690
    with cv.panel(0, top, title="Platform team: ARM control plane", theme="grape", style="solid", fill="soft", pad=20, title_size=24, w=pw) as pp:
        items = [("Foundry account", "Microsoft.CognitiveServices/accounts", "foundry"),
                 ("Projects", "Microsoft.CognitiveServices/accounts/projects", "folder"),
                 ("Connections", "Microsoft.CognitiveServices/accounts/projects/connections", "api-connections"),
                 ("Model deployments", "Microsoft.CognitiveServices/accounts/deployments", "openai"),
                 ("Capability host and settings", "BYO Cosmos DB, AI Search and Storage", "cosmos")]
        yy = pp.iy
        for lab, sub, ic in items:
            b = Box(pw - 40, lab, sub=sub, h=84, theme="grape", icon=ic, icon_pos="left", icon_size=30, size=18, sub_size=13).place(cv, pp.ix, yy)
            yy += b.h + 14
    with cv.panel(pw + 40, top, title="App team: data plane and registry", theme="green", style="solid", fill="soft", pad=20, title_size=24, w=pw) as ap:
        items = [("Logical hosted agent", "Microsoft.Foundry/agents@v1 (project data plane)", "agent", "green"),
                 ("Agent versions", "immutable; created by deploy", "versions", "green"),
                 ("Container image", "in Azure Container Registry", "acr", "cyan"),
                 ("Eval datasets, evaluators, recipes", "registered and versioned in the project, plus repo files", "metrics", "violet")]
        yy = ap.iy
        for lab, sub, ic, th_name in items:
            b = Box(pw - 40, lab, sub=sub, h=84, theme=th_name, icon=ic, icon_pos="left", icon_size=30, size=18, sub_size=13).place(cv, ap.ix, yy)
            yy += b.h + 14
        Note(pw - 40, "Terraform manages the named agent, not each version: azd owns agent-version deployment.", kind="info", title="Versions", size=14).place(cv, ap.ix, yy)
    rows = [
        ["Account, projects, connections, model deployments (Microsoft.CognitiveServices/accounts and its children)", ("ARM control plane", "grape"),
         "Bicep, Terraform (AzAPI or AzureRM), ARM or the CLI"],
        ["Capability host and capability settings (BYO Cosmos DB, AI Search, Storage)", ("ARM control plane", "grape"),
         "Bicep, or Terraform with AzAPI only (AzureRM: no, use AzAPI)"],
        ["Logical hosted agent (Microsoft.Foundry/agents@v1)", ("Project data plane", "green"),
         "azd deploy (azd owns agent-version deployment), or Terraform azapi_data_plane_resource, the SDK or REST"],
        ["Agent versions", ("Project data plane", "green"), "Created by deploy; immutable. Terraform manages the named agent, not each version"],
        ["Container image", ("Azure Container Registry", "cyan"), "azd build (local or ACR remote build), or a separate pipeline that scans and signs"],
        ["Eval datasets, evaluators and recipes", ("Foundry project + repo files", "violet"), "azd ai agent eval ..., azd ai eval ..., the GitHub Action or the Azure DevOps task"],
    ]
    tx = 2 * pw + 40 + 60
    t = Table([("Artefact", 500), ("Surface", 250), ("Deploy with", W - tx - 750)], rows, w=W - tx, theme="grape", size=14, head_size=15,
              title="Which tool for which API surface", title_size=22)
    t.place(cv, tx, top)
    ly = learn_line(cv, tx, t.bottom + 8, src("tfres", "tmpl", "std", "tf"))
    n1 = Note(W - tx, "Keep Terraform states and permissions separate if you run two configurations. 'Don't let two independent configurations manage the same fields', for example the endpoint selector.",
              kind="gotcha", title="One writer per field", src=src("tf", "cicd"))
    n1.place(cv, tx, ly + 22)
    n2 = Note(W - tx, "Reading the surfaces: ARM resources are the platform team's; the hosted agent and its versions live on the project data plane (azd, SDK, REST or Terraform data-plane resource); the image lives in the registry; eval assets are registered and versioned in the project.",
              kind="key", title="Reading the table")
    n2.place(cv, tx, n1.bottom + 20)
    return max(pp.bottom, ap.bottom, n2.bottom) + 56


# ---------------------------------------------------------------------------------------------- 3. IaC
def iac(cv: Canvas, y: float) -> float:
    y = head(cv, y, 3, "Infrastructure as code: Bicep, Terraform, ARM and the CLI",
             sub="Pick the tool by the API surface: the control plane takes Bicep or Terraform; the hosted agent itself is a data-plane resource.",
             tags=(DOC,))
    cw = (W - 2 * 50) / 3
    c1 = card(cw, "Bicep", [
        "Quickstart: foundry-samples/infrastructure/infrastructure-setup-bicep/00-basic deploys an account + project (az deployment group create ... --parameters aiFoundryName=... aiProjectName=...)",
        "Production-ready variants sit in the same folder, for example 43-standard-agent-setup-with-customization",
        "Portal: Automation > Export template > Bicep. Replace hard-coded IDs with parameters; the export may carry warnings",
        "Assigning roles in the template needs an Owner-type role",
        "The template location defaults to eastus2",
        "Account names: 2 to 64 characters, lowercase letters, numbers and hyphens, globally unique (error AccountNameInvalid)",
    ], "grape", "template-specs", ("tmpl", "samples"), title_size=22)
    c2 = card(cw, "ARM, REST and the CLI", [
        "Microsoft.CognitiveServices/accounts/deployments, API 2023-05-01, carries quota-aware TPM capacity",
        "az cognitiveservices ... for accounts, models and quota",
        "The spillover property needs API 2024-10-01 in the doc sample",
    ], "grape", "api-connections", ("quota", "spill"), title_size=22)
    rows = [
        ["Scope", "All control-plane configuration, including preview features", "Core management only"],
        ["Resources", "AzAPI resources; azapi_data_plane_resource for the hosted agent", "azurerm_cognitive_account, azurerm_cognitive_account_project, azurerm_cognitive_deployment"],
        ["Capability host (BYO Cosmos DB, AI Search, Storage)", ("Yes", "green"), ("No: use AzAPI", "red")],
        ["Version", "~> 2.5 in the basic sample; the hosted-agent article needs 2.9.0 or later", "Not stated"],
        ["Model deployments with quota", "Use AzAPI for deployments", "The doc note says AzureRM lacked the quota schema at the time of writing: verify the current provider"],
    ]
    t = Table([("", 200), ("AzAPI", 400), ("AzureRM", cw - 600)], rows, w=cw, theme="grape", size=14, head_size=15, title="Terraform: AzAPI or AzureRM",
              title_size=22, first_col_theme="grape")
    c3 = card(cw, "azd-generated infrastructure", [
        "azd ai agent init --infra=terraform or --infra=bicep generates infra/",
        "Without --infra, azd synthesises the infrastructure from azure.yaml",
        "Keep infra/ and the provider lockfile in Git",
        "! Do not commit Terraform state, .terraform/, saved plans or .azure/",
    ], "green", "azd", ("cicd", "tf"), badge="preview", title_size=22)
    c4 = card(cw, "Policy as code", [
        "Custom and built-in Azure Policy: the model deployment policy, a deployment-type restriction (JSON) and denyAction",
    ], "grape", "policy", ("policy",), title_size=22)
    c5 = card(cw, "Deployment permission gotchas", [
        "If the template sets agent capability settings, the deploying identity needs Storage Blob Data Contributor on the referenced Storage account and Cosmos DB Operator on the referenced Cosmos DB account. AI Search needs no caller role",
        "Runtime roles for the project managed identity are separate: assign them after provisioning",
        "! ServiceModelDeprecating: the template references a retired or deprecating model version",
        "List GA models: az cognitiveservices model list --location <loc> --query \"[?model.lifecycleStatus=='GenerallyAvailable']\"",
    ], "red", "managed-identity", ("tmpl", "tf"), title_size=22)
    c1.place(cv, 0, y)
    c2.place(cv, 0, c1.bottom + 24)
    t.place(cv, cw + 50, y)
    nt = Note(cw, "Terraform state can hold secrets: use a secure remote backend and never upload state or plan files as unrestricted artefacts.", kind="warn", title="State is sensitive", size=14)
    nt.place(cv, cw + 50, t.bottom + 20)
    c4.place(cv, cw + 50, nt.bottom + 24)
    c3.place(cv, 2 * (cw + 50), y)
    c5.place(cv, 2 * (cw + 50), c3.bottom + 24)
    return max(c2.bottom, c4.bottom, c5.bottom) + 60


# ---------------------------------------------------------------------------------------------- 4. azd + workflow
def azd_section(cv: Canvas, y: float) -> float:
    y = head(cv, y, 4, "azd and the CI/CD workflow", sub="One command wires the pipeline; the same azd commands you run by hand run in CI.",
             tags=(DOC, PREV))
    bw = (W - 4 * 96) / 5
    steps = [
        ("Run azd pipeline config", "detects GitHub or Azure DevOps", "gray", "azd"),
        ("Creates a service principal", "federated (OIDC) credentials", "red", "managed-identity"),
        ("Writes repo secrets and variables", "AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_ENV_NAME, AZURE_LOCATION", "cyan", "key-vault"),
        ("Generates the workflow", ".github/workflows/azure-dev.yml or azure-pipelines.yml", "green", "github"),
        ("A push to main runs it", "default flow: azd provision, then azd deploy (the same as azd up locally)", "violet", "builds"),
    ]
    bxs = []
    for i, (t_, s_, th_, ic_) in enumerate(steps):
        bxs.append(Box(bw, f"{i + 1}  {t_}", sub=s_, theme=th_, icon=ic_, icon_pos="top", size=18, sub_size=14, h=170).place(cv, i * (bw + 96), y))
    for a, b in zip(bxs, bxs[1:]):
        connect(cv, a, b, sw=3, gap=4)
    y2 = y + 170 + 40
    code = Code(940, "GitHub Actions: settings the docs call out (illustrative skeleton)", [
        "permissions:",
        "  id-token: write",
        "concurrency:",
        "  group: hosted-agent-deployment",
        "  cancel-in-progress: false",
        "steps:",
        "  - uses: Azure/setup-azd@v2",
        "  - uses: hashicorp/setup-terraform@v3   # if the repo has .tf files",
        "  - run: azd ext install microsoft.foundry",
        "  - run: azd auth login --federated-credential-provider github",
        "  - run: azd provision --no-prompt",
        "  - run: azd deploy --no-prompt",
    ], theme="gray", size=14, note="Assembled from the settings the CI/CD page lists, not a verbatim sample. The runner image does not include the microsoft.foundry extension, and Terraform keeps its own ARM_* OIDC variables.",
        src=[S["cicd"]])
    code.place(cv, 0, y2)
    cmds = [
        ["azd pipeline config", "Wires GitHub Actions or Azure DevOps: service principal, secrets and variables, workflow file. Default trigger: push to main"],
        ["azd provision --no-prompt, then azd deploy --no-prompt", "Provision infrastructure, then deploy: a new hosted-agent version. --no-prompt in every CI run"],
        ["azd ai agent show --output json", "Read the version and its status; wait for active"],
        ["azd ai agent invoke --new-session --new-conversation", "Smoke test; --version N tests a specific version"],
        ["azd ai agent endpoint update", "Change the version selector without a new version"],
        ["azd ai agent eval run", "Quick evaluation. It cannot enforce thresholds"],
        ["azd ai eval run start --fail-on pass-rate=0.8", "Gated evaluation (needs the azure.ai.evaluations extension)"],
        ["azd env new <name>", "One azd environment per stage, with its own subscription and location"],
        ["azd ai project set <endpoint> --no-prompt", "Project context; or FOUNDRY_PROJECT_ENDPOINT, or --project-endpoint / -p"],
        ["azd ai agent doctor", "Pre-flight diagnostic (deterministic, not AI): see the AI-assisted operations canvas"],
    ]
    tc = Table([("Command", 520), ("What it does", 800)], cmds, w=1320, theme="green", size=14, head_size=15, title="Commands you will meet in pipelines", title_size=22,
               first_col_theme="green")
    tc.place(cv, 990, y2)
    files = [
        ["azure.yaml", "azd project and services; image: for a pre-built image; docker.remoteBuild (default true); agentEndpoint.versionSelector", ("commit", "green")],
        ["infra/ and the provider lockfile", "Bicep or Terraform from azd ai agent init --infra", ("commit", "green")],
        ["eval.yaml", "Quick eval config at the agent root", ("commit", "green")],
        ["evals/azure.eval.yaml", "Gated eval config: not interchangeable with eval.yaml", ("commit", "green")],
        [".github/workflows/azure-dev.yml or azure-pipelines.yml", "Generated by azd pipeline config", ("commit", "green")],
        ["Terraform state, .terraform/, saved plans, .azure/", "May contain secrets or local environment settings", ("never", "red")],
    ]
    tf = Table([("File", 320), ("What it is", 350), ("Git", 80)], files, w=750, theme="gray", size=14, head_size=15, title="Repo files: commit or not", title_size=22)
    tf.place(cv, 990 + 1320 + 40, y2)
    yb = max(code.bottom, tc.bottom, tf.bottom) + 40
    cw = (W - 2 * 50) / 3
    k1 = card(cw, "Terraform remote state", [
        "Azure Storage backend with use_azuread_auth",
        "A different state key per environment: hosted-agent-ci/${AZURE_ENV_NAME}.tfstate",
        "Backend settings from environment variables: RS_RESOURCE_GROUP, RS_STORAGE_ACCOUNT, RS_CONTAINER_NAME",
        "The pipeline identity needs Blob data-plane access",
        "! Backend locking doesn't coordinate other tools updating the same hosted agent: serialize production releases across azd, Terraform and any other deployment writers",
        "! Don't add a long-lived client secret solely because your infrastructure uses Terraform",
    ], "cyan", "storage", ("cicd", "tf"), title_size=22)
    k2 = card(cw, "Pipeline-safe flags and environments", [
        "--no-prompt always in CI; --output json for parsing; --debug for diagnostics",
        "Project context: FOUNDRY_PROJECT_ENDPOINT, --project-endpoint or -p, or azd ai project set",
        "One azd env new <name> per environment, each with its own subscription and location",
        "Branch triggers work (main to production, develop to staging); the promote page prefers dev, test, prod jobs from the same commit with approvals",
    ], "gray", "branch", ("cicd", "prod"), title_size=22)
    k3 = card(cw, "Prerequisites and extensions", [
        "Provisioning needs Contributor + Foundry Owner; extension install needs internet",
        "microsoft.foundry meta-package = 7 core extensions: azure.ai.agents (azd ai agent), connections, inspector, projects, routines, skills, toolboxes",
        "Install separately: azure.ai.evaluations (azd ai eval: scaffold, manage evaluators, inspect, gate builds), azure.ai.dataset, azure.ai.finetune, azure.ai.models",
        "! Docs disagree on the minimum azd: 1.36.0 (CI page) or 1.37.0 (extension page)",
    ], "blue", "gear", ("ext", "cicd"), title_size=22)
    _, kb = row(cv, 0, yb, [k1, k2, k3], gap=50)
    return kb + 64


# ---------------------------------------------------------------------------------------------- 5/6. eval + quota (side by side)
def eval_and_quota(cv: Canvas, y: float) -> float:
    HW = 1500
    RX = HW + 100
    y0 = head(cv, y, 5, "Evaluation gates in pipelines", sub=f"Two formats; only one can fail a build. GitHub Action @v3-beta and the Azure DevOps task are preview ({ASOF}).", tags=(PREV,), x=0, w=HW)
    rows = [
        ["Config", "eval.yaml at the agent root (agent target, dataset reference, evaluators, options)", "evals/azure.eval.yaml. The two formats are not interchangeable"],
        ["Commands", "eval generate (wizard or flags: --gen-instruction --eval-model --max-samples --dataset --evaluator), eval run, eval update, eval list, eval show, optimize --config eval.yaml",
         "azd ai eval init, then azd ai eval create, then azd ai eval run start --fail-on pass-rate=0.8"],
        ["Gate", ("Cannot enforce thresholds", "red"), ("--fail-on quality gates", "green")],
        ["Notes", "Target-based eval works for the responses and invocations protocols, synchronous and non-streaming. A2A, Activity, long-running or streaming agents: evaluate traces instead. azd provision doesn't create eval assets; --no-wait defers generation; pin versions as strings",
         "Optional azure.ai.evaluations extension: scaffold, manage evaluators, inspect and gate builds"],
    ]
    t = Table([("", 110), ("Quick: azd ai agent eval", 760), ("Gated: azd ai eval (optional extension)", 630)], rows, w=HW, theme="violet", size=14, head_size=15,
              first_col_theme="violet")
    t.place(cv, 0, y0)
    ga = card(HW, "GitHub Action and Azure DevOps task", [
        "microsoft/ai-agent-evals@v3-beta; Azure DevOps extension AIAgentEvaluation@2, run after an AzureCLI@2 service connection",
        "Inputs: azure-ai-project-endpoint; deployment-name (the judge model); data-path (JSON: name, evaluators[], data[] with query + optional ground_truth and context, openai_graders, evaluator_parameters, data_mapping); agent-ids (name:version, comma-separated); optional baseline-agent-id",
        "Output: a score table with confidence intervals and a pairwise statistical comparison against the baseline",
        "Evaluator categories: agent, RAG, risk and safety, general purpose, OpenAI graders, custom",
    ], "violet", "github", ("gha", "ado", "evals_repo"), badge="preview", title_size=22)
    ga.place(cv, 0, t.bottom + 24)
    ne = Note(HW, "Do not run evaluations on every commit: they cost money (a docs gotcha). Gate where it matters, for example before the test and production stages (our suggestion).", kind="tip",
              title="Mind the cost", size=15)
    ne.place(cv, 0, ga.bottom + 22)
    # quota-aware deployment
    yq = head(cv, y, 6, "Quota-aware deployment automation", sub="Check quota and capacity before you create a deployment.", tags=(DOC,), x=RX, w=HW)
    bw = (HW - 3 * 40) / 4
    qs = [
        ("Check consumption", "Usages API: GET .../locations/{location}/usages; az cognitiveservices usage list -l <region>; Get-AzCognitiveServicesUsage", "yellow", "quotas"),
        ("Check capacity", "Model Capacities API: deployable capacity per location and deployment type", "yellow", "regions"),
        ("Create the deployment", "Microsoft.CognitiveServices/accounts/deployments, API 2023-05-01: sku.name, sku.capacity, properties.model", "blue", "openai"),
        ("Wire spillover", "properties.spilloverDeploymentName on the PTU deployment (API 2024-10-01 in the doc sample)", "blue", "versions"),
    ]
    qb = []
    for i, (t_, s_, th_, ic_) in enumerate(qs):
        qb.append(Box(bw, f"{i + 1}  {t_}", sub=s_, theme=th_, icon=ic_, icon_pos="top", size=17, sub_size=13, h=200).place(cv, RX + i * (bw + 40), yq))
    for a, b in zip(qb, qb[1:]):
        connect(cv, a, b, sw=3, gap=4)
    rows = [
        ["sku.name", "Standard, GlobalStandard, GlobalProvisionedManaged (examples)"],
        ["sku.capacity", "Standard: 1 = 1,000 TPM. Provisioned: the number of PTUs"],
        ["properties.model", "format, name, version"],
    ]
    tq = Table([("Field", 220), ("Meaning", HW - 220)], rows, w=HW, theme="yellow", size=14, head_size=15, first_col_theme="yellow", title="The deployment payload", title_size=20)
    tq.place(cv, RX, qb[0].bottom + 24)
    cq = card(HW, "Rules and gotchas", [
        "Needs Cognitive Services Contributor at resource scope; the CLI quota commands need Azure CLI 2.51.0 or later",
        "2023-05-01 is the resource-management API version only: it does not affect inference API versions",
        "RPM and TPM ratios differ by model, so programmatic deployment risks 'accidental misallocation of quota'",
        "Terraform: use AzAPI for deployments (the doc note says AzureRM lacked the quota schema at the time of writing; verify the current provider)",
    ], "yellow", "quotas", ("quota", "spill"), title_size=22)
    cq.place(cv, RX, tq.bottom + 24)
    return max(ne.bottom, cq.bottom) + 60


# ---------------------------------------------------------------------------------------------- 7/8. ACR + rollout (side by side)
def acr_and_rollout(cv: Canvas, y: float) -> float:
    HW = 1500
    RX = HW + 100
    y0 = head(cv, y, 7, "Registry options (ACR)", sub="Where the hosted-agent image comes from.", tags=(DOC, PREV), x=0, w=HW)
    cw = (HW - 2 * 30) / 3
    a = card(cw, "Default: project ACR", [
        "azd ai agent init creates a project ACR",
        "azd up pushes the image to it",
    ], "cyan", "acr", ("acr",), title_size=21)
    b = card(cw, "Bring your own ACR", [
        "When: compliance (centrally audited), a registry shared across projects, ABAC-mode registries, hardened, scanned or signed images",
        "AZURE_CONTAINER_REGISTRY_ENDPOINT; AZURE_CONTAINER_REGISTRY_RESOURCE_ID enables the scoped RBAC preflight",
        "--acr-connection <conn> for builds against an existing project",
    ], "cyan", "acr", ("acr",), title_size=21)
    c = card(cw, "Pre-built image", [
        "image: myregistry.azurecr.io/agents/my-agent:1.2.3 in azure.yaml; prefer a digest",
        "azd ai agent init --image ... --registry-connection <conn>",
        "Terraform path: linux/amd64, runtime contract, container protocol 2.0.0, image digest, full RAI policy resource ID, readiness gate (version active), prevent_destroy on the agent",
    ], "cyan", "acr", ("acr", "tf"), title_size=21)
    _, rb = row(cv, 0, y0, [a, b, c], gap=30)
    rows = [
        ["Developer: local build", "AcrPush"],
        ["Developer: ACR remote build", "Container Registry Tasks Contributor"],
        ["ABAC registry, local build", "Repository Writer"],
        ["ABAC registry, remote build", "Owner or Contributor"],
        ["Agent identity at deploy", "AcrPull, granted automatically"],
    ]
    tr = Table([("Who and how", 640), ("Role", HW - 640)], rows, w=HW, theme="red", size=14, head_size=15, first_col_theme="red", title="Registry roles", title_size=20)
    tr.place(cv, 0, rb + 24)
    n1 = Note(HW, f"If publicNetworkAccess is Disabled, azd up must run inside the VNet (self-hosted runner, Azure DevOps agent or jump host). Projects created after June 25, 2026 support a private (network-secured) ACR for the agent image; earlier projects need the registry reachable over its public endpoint ({ASOF}). azd ai agent doctor shows the RBAC state.",
              kind="warn", title="Private registry", src=src("acr"))
    n1.place(cv, 0, tr.bottom + 22)
    # rollout
    yr = head(cv, y, 8, "Rollout strategies", sub="Prompt agents, hosted agents, models and infrastructure roll out differently.", tags=(DOC, PREV), x=RX, w=HW)
    rows = [
        [("Prompt agents", "green"), "Version, then publish; use a gateway or router for progressive rollout"],
        [("Hosted agents", "green"), "Pin the stable version first, then canary with FixedRatio rules (preview); roll back by changing the version selector"],
        [("Models", "blue"), "Blue-green through the gateway with side-by-side deployments"],
        [("Infrastructure", "grape"), "Serialize releases; keep separate state per environment"],
    ]
    tt = Table([("Artefact", 240), ("Strategy", HW - 240)], rows, w=HW, theme="gray", size=14, head_size=15, first_col_theme="gray")
    tt.place(cv, RX, yr)
    steps = ["Capture the current routing", "Pin stable at 100%", "azd deploy the candidate", "Test with --version N", "Canary 10%, inspect, ramp", "100%, or roll back"]
    cv.text(RX, tt.bottom + 26, "Hosted-agent production rollout, in order (detail on the 'Hosted agents: deploy and operate' canvas)", size=17, color="#2b8a3e")
    sw_ = (HW - 5 * 38) / 6
    sb = []
    for i, s_ in enumerate(steps):
        sb.append(Box(sw_, f"{i + 1}  {s_}", theme="green" if i < 5 else "gray", size=15, h=110).place(cv, RX + i * (sw_ + 38), tt.bottom + 60))
    for p, q in zip(sb, sb[1:]):
        connect(cv, p, q, sw=2, gap=3)
    dd = Note(HW, "The 'Promote hosted agents to production' page (preview) documents FixedRatio canary rules (for example 90/10, then 50/50). The hosted-agents concept page says traffic splitting between versions isn't supported, and the Architecture Center baseline says there is no built-in blue-green or canary for agents. Treat percentage canaries as preview and in flux; the pin-first, test, promote-by-selector sequence is common to all the pages.",
              kind="warn", title=f"Docs disagree on canary rules ({ASOF})", src=src("prod", "hosted", "arch"))
    dd.place(cv, RX, sb[0].bottom + 26)
    n2 = Note(HW, "Default routing follows the latest version. If a pipeline deploys and only then tests, production can serve an untested version in between: pin first, then deploy the candidate.",
              kind="gotcha", title="The endpoint follows the latest version", src=src("cicd", "manage"))
    n2.place(cv, RX, dd.bottom + 18)
    return max(n1.bottom, n2.bottom) + 60


# ---------------------------------------------------------------------------------------------- 9. gotchas
def gotchas(cv: Canvas, y: float) -> float:
    y = head(cv, y, 9, "Gotchas", tags=(DOC,))
    nw = (W - 3 * 34) / 4
    notes = [
        Note(nw, f"Most azd, CI/CD and evaluation pages are marked preview: no SLA ({ASOF}).", kind="preview", title="Preview everywhere"),
        Note(nw, "Choosing Terraform for the infrastructure does not put hosted-agent versions under Terraform: azd owns version deployment.", kind="gotcha", title="azd owns versions", src=src("tf")),
        Note(nw, "The quick azd ai agent eval run cannot enforce thresholds. Use the optional extension for --fail-on.", kind="warn", title="Quick eval is not a gate", src=src("azdeval")),
        Note(nw, "Terraform state and plan files can contain secrets: never upload them as unrestricted artefacts.", kind="gotcha", title="Secrets in state", src=src("cicd")),
        Note(nw, "AzureRM cannot configure capability hosts; use AzAPI.", kind="warn", title="AzureRM limits", src=src("tfres")),
        Note(nw, "CI needs Contributor + Foundry Owner. The deploying identity also needs Cosmos DB Operator and Storage Blob Data Contributor if the template sets capability settings.", kind="gotcha", title="Roles for CI", src=src("cicd", "tmpl")),
        Note(nw, "Backend locking does not coordinate other tools that update the same hosted agent: serialize production releases across azd, Terraform and any other writer.", kind="warn", title="Serialize releases", src=src("cicd")),
        Note(nw, "Record each release: the commit, image digest, version, routing configuration, and the dataset and evaluator versions.", kind="tip", title="Keep a release record", src=src("prod")),
    ]
    _, bb = grid(cv, 0, y, notes, 4, gap_x=34, gap_y=26)
    return bb + 64


def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "CI/CD and infrastructure as code",
                                f"Pipelines, quality gates and IaC for Foundry: who owns what, which API surface each artefact lives on and what stops a bad release ({ASOF})",
                                icon="foundry", w=W)
    y = summary(cv, bottom + 40)
    y = pipeline(cv, y)
    y = stage_table(cv, y)
    y = surfaces(cv, y)
    y = iac(cv, y)
    y = azd_section(cv, y)
    y = eval_and_quota(cv, y)
    y = acr_and_rollout(cv, y)
    y = gotchas(cv, y)
    sources(cv, 0, y, [
        S["cicd"], S["prod"], S["tf"], S["acr"], S["ext"], S["gha"], S["ado"], S["azdeval"], S["tmpl"], S["tfres"],
        S["quota"], S["spill"], S["evals_repo"], S["samples"],
    ], w=W, cols=3)
