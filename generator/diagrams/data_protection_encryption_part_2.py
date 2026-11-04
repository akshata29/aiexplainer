"""Data protection part 2 - customer-managed keys end to end, Key Vault for connection secrets, managed vs BYO storage, MCSB baseline, compliance and Azure Government."""
from generator.xd import *
from generator.xd import metrics

META = dict(
    id="data-protection-encryption-part-2", title="Data protection, part 2: keys, secrets, storage and compliance", section="5", order=5.5,
    description="Customer-managed keys end to end (prerequisites, enablement, rotation, revocation), Key Vault for connection secrets, managed vs your own storage, "
                "the security-baseline control families, Defender, Purview and Azure Government.",
    tags=["encryption", "customer-managed-keys", "key-vault", "byo-storage", "security-baseline", "compliance"],
)

W = 3360
G = 60
C3 = (W - 2 * G) / 3
XB, XC = C3 + G, 2 * (C3 + G)
C4 = (W - 3 * 50) / 4


def L(path, **kw):
    return learn(path, **kw)


CMK = ("Customer-managed keys", L("concepts/customer-managed-keys"))
CMKP = ("Customer-managed keys in the portal", L("concepts/encryption-keys-portal"))
KVC = ("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection"))
BYOS = ("Bring your own Azure Storage", L("how-to/bring-your-own-azure-storage-foundry"))
STD = ("Standard agent setup", L("agents/concepts/standard-agent-setup"))
PLAN = ("Plan your Foundry rollout", L("concepts/planning"))
BASE = ("Azure security baseline for Foundry", L("azure-ai-foundry-security-baseline", base="security/benchmark/azure/baselines"))
CPC = ("Manage compliance and security (control plane)", L("control-plane/how-to-manage-compliance-security"))
DIAG = ("Diagnostic logging", L("how-to/diagnostic-logging"))
A365D = ("Configure Agent 365 data collection", L("agents/how-to/configure-agent-365-data-collection"))
GOV = ("Foundry in Azure Government", L("concepts/foundry-azure-government"))
GOVA = ("Agent Service in Azure Government", L("agents/concepts/azure-government"))
ADMIN = ("Foundry administrator guide", L("concepts/administrator-guide"))

Y, N, P, D = CHECK, CROSS, PARTIAL, DASH


def cite(cv, x, y, items, size=12):
    for label, url in items:
        t = cv.text(x, y, f"Learn: {label}", size=size, color=LINK, link=url)
        y = t.bottom + 2
    return y


class CodeBlock(Rect2):
    """Monospace snippet in a soft rounded box (Comic Shanns, the repo's monospaced hand-drawn face)."""

    def __init__(self, w, lines, *, title=None, theme="gray", size=15, pad=14, src=()):
        self.th = THEMES[theme]
        self.w, self.size, self.pad, self.title = w, size, pad, title
        self.lines = list(lines)
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


def steps(cv, x, y, w, items, *, theme, n_theme=None, src_first=(), gap_min=70):
    """Numbered left-to-right step cards joined by arrows; returns the bottom y."""
    n = len(items)
    cw = (w - (n - 1) * gap_min) / n
    cards = [Card(cw, t, body, theme=theme, icon=ic, src=src_first if i == 0 else ()) for i, (t, ic, body) in enumerate(items)]
    _, bottom = row(cv, x, y, cards, gap=gap_min)
    for a, b in zip(cards, cards[1:]):
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=4)
    for i, c in enumerate(cards):
        numbered(cv, c.x + 34, c.y, i + 1, theme=n_theme or theme)
    return bottom


def stamps(cv, y):
    sw = (W - 3 * 40) / 4
    spec = [
        ("Microsoft-managed keys by default",
         "FIPS 140-2 compliant 256-bit AES at rest, transparent, with no code change", "green"),
        ("Customer-managed keys are opt-in",
         "Key Vault or Managed HSM in the same region, soft delete and purge protection on, key access granted before you enable", "red"),
        ("A project can move to CMK but not back",
         "Revoking the key makes encrypted data inaccessible; CMK is available only in select regions (as of 2026-11-03)", "orange"),
        ("The security baseline is stale",
         "It is built on MCSB v1.0 and says local auth is unsupported while other pages document API keys: docs disagree", "grape"),
    ]
    boxes = [Box(sw, t, sub=s, theme=th, size=24, sub_size=16, h=112, sw=3) for t, s, th in spec]
    row(cv, 0, y, boxes, gap=40)
    return y + 112


# ====================================================================== 1. encryption at rest + CMK
def key_diagram(cv, x, y, w):
    with cv.panel(x, y, title="How customer-managed keys protect a Foundry resource",
                  sub="Your key store holds the key; managed identities of the Foundry resource and its projects wrap and unwrap with it",
                  theme="red", style="dotted", pad=26, title_size=24, sub_size=15, w=w) as p:
        bw = (w - 2 * 26 - 2 * 130) / 3
        top = p.iy + 10
        a = Box(bw, "Foundry resource", sub="properties.encryption: keySource Microsoft.KeyVault, keyVaultUri, keyName, optional keyVersion and identityClientId",
                theme="blue", icon="foundry", size=21, sub_size=15, h=190, sw=3)
        b = Box(bw, "Managed identity", sub="System-assigned and/or user-assigned. The account identity and the project identity need key access before you enable CMK",
                theme="pink", icon="managed-identity", size=21, sub_size=15, h=190, sw=3)
        c = Box(bw, "Azure Key Vault or Managed HSM", sub="Same region as the Foundry resource; soft delete and purge protection on; RSA key of at least 2048 bits",
                theme="red", icon="key-vault", size=21, sub_size=15, h=190, sw=3)
        for i, bx in enumerate((a, b, c)):
            bx.place(cv, p.ix + i * (bw + 130), top)
        connect(cv, a, b, a_side="right", b_side="left", sw=3, gap=4, label="acts as", label_size=14)
        connect(cv, b, c, a_side="right", b_side="left", sw=3, gap=4, label="wrap / unwrap key", label_size=14, label_wrap=130)
        d = Box(w - 2 * 26, "Data encrypted with the customer-managed key", theme="cyan", icon="storage", icon_pos="left", size=20, sub_size=15,
                sub="Project assets (agents, prompts, datasets, evaluations) | uploaded files (fine-tuning, Files API) | user state (conversation history, system prompts, fine-tuned models) | indexed representations",
                h=110, fill="soft")
        d.place(cv, p.ix, top + 190 + 60)
        connect(cv, a, d, a_side="bottom", b_side="top", ta=0.5, tb=(a.cx - d.x) / d.w, sw=3, gap=4, label="encrypts", label_size=14, label_pos="right")
        roles = Card(bw * 2 + 130, "Roles that make it work", [
            "Key Vault with Azure RBAC: Key Vault Crypto User. Vault access policy: Encrypt, Decrypt, Wrap Key, Unwrap Key, Sign, Verify (portal) for the account and project identities; the Bicep sample uses get, wrapKey and unwrapKey",
            "Managed HSM: Managed HSM Crypto User, assigned with az keyvault role assignment create (local RBAC)",
        ], theme="red", fill="soft", body_size=15, src=[CMK, CMKP])
        roles.place(cv, p.ix, d.bottom + 36)
        dflt = Card(bw, "Default: Microsoft-managed keys", [
            "No setup; transparent",
            "CMK is an extra layer for rotation, revocation and audit",
        ], theme="green", dash="dashed", fill="soft", body_size=15)
        dflt.place(cv, p.ix + 2 * (bw + 130), d.bottom + 36, h=roles.h)
        connect(cv, dflt, roles, a_side="left", b_side="right", sw=2, gap=4, dash="dashed", label="optional upgrade", label_size=14)
    return p


def cmk_matrix(cv, x, y, w):
    rows = [
        [("Prompt agents", "blue"), N, Y, "Configure CMK separately on Cosmos DB, Storage and AI Search"],
        [("Hosted agents", "blue"), N, P, "$HOME is platform-managed and not CMK-encrypted"],
        [("Fine-tuning", "blue"), Y, D, "No BYO storage"],
        [("Batch jobs", "blue"), Y, Y, ""],
        [("Evaluations", "blue"), Y, Y, ""],
        [("Hugging Face models on managed compute", "blue"), D, D, "Weights are on Microsoft-managed registries"],
        [("Speech", "blue"), N, Y, ""],
        [("Language", "blue"), Y, Y, ""],
        [("Content Understanding", "blue"), D, Y, "BYO storage is required"],
        [("OpenAI Assistants (deprecated)", "blue"), N, D, ""],
        [("Connected services: AI Search, Logic Apps, Functions", "blue"), D, D, "Their own encryption lifecycle"],
    ]
    t = Table([("Capability", 270), ("CMK on Foundry-managed storage", 130), ("CMK on customer-managed storage", 130), "Note"], rows, w=w,
              theme="red", size=14, head_size=14, pad_x=6, align=["left", "center", "center", "left"],
              title="CMK support by capability", title_size=22)
    t.place(cv, x, y)
    yy = y + t.h + 12
    from generator.xd.blocks import draw_mark
    cx = x
    for kind, label in ((Y, "supported"), (N, "not supported"), (P, "partial"), (D, "not applicable")):
        draw_mark(cv, kind, cx + 11, yy + 11)
        tt = cv.text(cx + 28, yy + 1, label, size=14)
        cx += 28 + tt.w + 22
    cb = cite(cv, x, yy + 32, [CMK])
    return t, cb


def compute_stack(cv, x, y, w):
    rows = [
        [("Persistent stores and Foundry artifacts", "red"), Y, "CMK is enforced"],
        [("Runtime compute", "red"), ("Ephemeral", "gray"), "Data is CMK-unwrapped to process, re-wrapped on write and cleaned after the job"],
        [("Fine-tune serving", "red"), P, "Weights are unwrapped into serving infrastructure at deploy and removed on delete"],
        [("Managed-compute model hosting", "red"), P, "In-memory weights and cache are not CMK-protected"],
        [("Inference and agent runtime", "red"), P, "Outputs are CMK-protected only if you bring your own storage"],
        [("Hosted-agent sandbox", "red"), N, "Root disk lives up to 24 hours and $HOME is retained 30 days: no CMK"],
        [("Fine-tune training", "red"), N, "Temporary job-local files are not CMK-protected"],
    ]
    t = Table([("Layer of the compute stack", 290), ("CMK", 100), "What happens"], rows, w=w, theme="red", size=14, head_size=15,
              align=["left", "center", "left"], title="Where CMK applies along the compute stack", title_size=22)
    t.place(cv, x, y)
    cb = cite(cv, x, y + t.h + 8, [CMK])
    return cb


def section_cmk(cv, y):
    _, b = section_header(cv, 0, y, "1  Encryption at rest and customer-managed keys (CMK)", size=34,
                          sub="Persistent stores and Foundry artifacts honour the CMK; runtime compute is ephemeral. Coverage differs by capability and by where the data is stored.")
    top = b + 34
    LW = XC - G                      # two columns wide
    p = key_diagram(cv, 0, top, LW)
    cw = (LW - 2 * 40) / 3
    pre = Card(cw, "Prerequisites", [
        "Key store in the same region as the Foundry resource",
        "Soft delete and purge protection on the vault",
        "A managed identity (system-assigned and/or user-assigned) with key access before you enable CMK",
        "Owner or User Access Administrator on the vault (Managed HSM Administrator for an HSM); Contributor or Owner on the Foundry resource",
        "RSA key of at least 2048 bits",
    ], theme="red", icon="key-vault", src=[CMK])
    rot = Card(cw, "Rotation", [
        "Leave keyVersion empty and the resource uses the latest key version automatically",
        "If you pin a version, update the resource after each rotation",
        "Enable Key Vault or HSM diagnostics to audit key use",
    ], theme="green", icon="recovery-vault", src=[CMK])
    con = Card(cw, "Constraints", [
        "A project can move from Microsoft-managed keys to CMK but cannot revert",
        "A project's CMK can only change to keys in the same key store",
        "Storage charges continue during soft-delete retention",
        "CMK is available only in select regions, because of Azure AI Search capacity constraints",
        "! Private Foundry: key store with a private endpoint plus Allow trusted Microsoft services (recommended), or trusted services alone over the public endpoint",
    ], theme="orange", icon="preview-features", src=[CMK])
    _, left_bottom = row(cv, 0, p.bottom + 36, [pre, rot, con], gap=40)
    t, cb1 = cmk_matrix(cv, XC, top, C3)
    cs = compute_stack(cv, XC, cb1 + 34, C3)
    return max(left_bottom, cs)


def section_enable(cv, y):
    _, b = section_header(cv, 0, y, "2  Enable, audit and revoke", size=34,
                          sub="User-assigned identity: one deployment. System-assigned identity: two deployments, because the key access must exist before encryption is switched on.")
    top = b + 34
    LW = XC - G
    cy = top
    cv.text(0, cy, "A  User-assigned managed identity: one deployment", size=24, color=THEMES["red"].deep)
    cy += 40
    bb = steps(cv, 0, cy, LW, [
        ("Create the key", "key-vault", ["RSA key of at least 2048 bits in a same-region vault or HSM", "Soft delete and purge protection on"]),
        ("Create the identity", "managed-identity", ["Create the user-assigned managed identity"]),
        ("Grant key access", "key", ["Key Vault Crypto User (or Managed HSM Crypto User) to the identity"]),
        ("Deploy the account", "foundry", ["Add encryption with keyVaultProperties and identityClientId"]),
        ("Verify", "compliance", ["Check properties.encryption.keySource"]),
    ], theme="red", n_theme="red", src_first=[CMK], gap_min=70)
    cy = bb + 36
    cv.text(0, cy, "B  System-assigned managed identity: two deployments", size=24, color=THEMES["red"].deep)
    cy += 40
    bb = steps(cv, 0, cy, LW, [
        ("Deploy without encryption", "foundry", ["Create the Foundry resource with a system-assigned identity"]),
        ("Read the principal ID", "managed-identity", ["Read identity.principalId; allow time for principal-ID propagation"]),
        ("Grant key access", "key", ["Key Vault Crypto User (or Managed HSM Crypto User) to that principal"]),
        ("Update with encryption", "foundry", ["Add the encryption block and redeploy"]),
    ], theme="red", n_theme="red", gap_min=70)
    cy = bb + 36

    # right: code block, portal route, troubleshooting
    code = CodeBlock(C3, [
        "properties:",
        "  encryption:",
        "    keySource: Microsoft.KeyVault",
        "    keyVaultProperties:",
        "      keyVaultUri: <vault or HSM URI>",
        "      keyName: <key name>",
        "      keyVersion: <optional>",
        "      identityClientId: <user-assigned>",
    ], title="ARM shape of the encryption property", theme="red", size=15, src=[CMK])
    code.place(cv, XC, top)
    n_portal = Note(C3, "Portal: Resource Management > Encryption > Customer-Managed Keys, then enter the key store URL and key name. The samples 30-customer-managed-keys "
                        "and 32-customer-managed-keys-user-assigned-identity show both patterns.", kind="info", title="Portal route", src=[CMKP])
    n_portal.place(cv, XC, code.bottom + 22)
    pol = Card(C3, "Troubleshoot and audit", [
        "403: Key Vault Crypto User or wrap/unwrap permission is missing",
        "Key store not found: the vault and the Foundry resource are in different regions",
        "Key version not supported: the RSA key is smaller than 2048 bits",
        "Policy: Azure AI Services resources should encrypt data at rest with a customer-managed key (Audit, Deny, Disabled) - not assessed by default",
    ], theme="gray", icon="policy", src=[CMK])

    # revocation flow (left) next to the troubleshooting card (right)
    ry = max(cy, n_portal.bottom + 22) + 30
    pol.place(cv, XC, ry)
    cv.text(0, ry, "C  Revoking the key: what stops and what keeps serving", size=24, color=THEMES["red"].deep)
    by = ry + 50
    cw = (LW - 3 * 70) / 4
    r1 = Box(cw, "Remove the role, disable or delete the key", sub="Or the whole key store", theme="red", size=20, sub_size=15, h=200, icon="key-vault")
    r2 = Box(cw, "Encrypted data becomes inaccessible", sub="Downloading training results and creating or deploying fine-tuned models fail", theme="red", size=20, sub_size=15, h=200, icon="alerts")
    r3 = Box(cw, "Deployed fine-tuned models keep serving", sub="Until they are deleted; then they cannot be recreated without restoring the key", theme="orange", size=20, sub_size=15, h=200, icon="openai")
    r4 = Box(cw, "Recover", sub="Restore the key version; a purged key store may need Azure support", theme="green", size=20, sub_size=15, h=200, icon="recovery-vault")
    row(cv, 0, by, [r1, r2, r3, r4], gap=70)
    for a, c in zip((r1, r2, r3), (r2, r3, r4)):
        connect(cv, a, c, a_side="right", b_side="left", sw=3, gap=4)
    return max(by + 200, pol.bottom)


# ====================================================================== 3. secrets
def section_secrets(cv, y):
    _, b = section_header(cv, 0, y, "3  Connection secrets: Microsoft-managed Key Vault or your own", size=34,
                          sub="Key-based connection secrets never sit in the agent: they go to a vault. You choose which one - at the start, because there is no secret migration.")
    top = b + 34
    hw = (W - G) / 2
    with cv.panel(0, top, title="Default: a Microsoft-managed Key Vault", sub="outside your subscription", theme="green", style="dashed", pad=24, w=hw, title_size=24, sub_size=15) as p1:
        a = Box(300, "Project connections", sub="API keys and connection details", theme="gray", icon="api-connections", size=19, sub_size=14, h=120)
        v = Box(380, "Microsoft-managed Key Vault", sub="Outside your subscription", theme="green", icon="key-vault", size=19, sub_size=14, h=120)
        a.place(cv, p1.ix, p1.iy + 10)
        v.place(cv, p1.ix + 300 + 100, p1.iy + 10)
        connect(cv, a, v, a_side="right", b_side="left", sw=3, gap=4, label="store secret", label_size=14)
        Card(hw - 48, None, [
            "Secrets cannot be retrieved across projects through the APIs (security baseline IM-8)",
            "Deleting a connection deletes its secret",
            "Project members can read the API keys stored in the connections of their project",
            "Autodeploy templates authenticate with a managed identity and use a Microsoft-managed Key Vault by default",
        ], theme="green", fill="soft", body_size=15, src=[KVC]).place(cv, p1.ix, p1.iy + 160)
    with cv.panel(hw + G, top, title="Bring your own Key Vault: one AzureKeyVault connection", sub="you own the vault, the roles and the lifecycle", theme="red", style="dashed", pad=24, w=hw, title_size=24, sub_size=15) as p2:
        a2 = Box(300, "All project and resource connections", sub="One connection manages every secret", theme="gray", icon="api-connections", size=19, sub_size=14, h=120)
        v2 = Box(380, "Your Azure Key Vault", sub="Foundry resource managed identity holds a role on it", theme="red", icon="key-vault", size=19, sub_size=14, h=120)
        a2.place(cv, p2.ix, p2.iy + 10)
        v2.place(cv, p2.ix + 300 + 100, p2.iy + 10)
        connect(cv, a2, v2, a_side="right", b_side="left", sw=3, gap=4, label="store secret", label_size=14)
        Card(hw - 48, None, [
            "Bicep: category AzureKeyVault, authType AccountManagedIdentity, isSharedToAll true",
            "Roles for the Foundry resource's managed identity on the vault: Key Vault Secrets Officer (the minimum; b86a8fe4-44ce-4948-aee5-eccb2c155cd7), Key Vault Contributor (f25e0fa2-a7c8-4377-a976-54943a77a395) or Key Vault Administrator (00482a5a-887f-4fb3-b363-3b7fe8e74483) - or the equivalent access policy",
            "Role propagation can take up to 30 minutes; the creator needs Key Vault Contributor + Key Vault Administrator (administrator guide)",
        ], theme="red", fill="soft", body_size=15, src=[KVC, ADMIN]).place(cv, p2.ix, p2.iy + 160)
    y2 = max(p1.bottom, p2.bottom) + 36
    n1 = Note(C3, "Only one Key Vault connection per Foundry resource, and create it when the resource has no other connections.", kind="gotcha",
              title="One connection, created first", src=[KVC])
    n2 = Note(C3, "No secret migration: switching vaults means deleting and recreating the connections. Deleting the Key Vault connection deletes its secrets.",
              kind="gotcha", title="No migration path", src=[KVC])
    n3 = Note(C3, "Deleting the vault breaks the Foundry resource, and deleting individual secrets can break other connections. The standard agent setup also lists a Key Vault as a prerequisite for secrets.",
              kind="warn", title="The vault is a dependency", src=[KVC, STD])
    row(cv, 0, y2, [n1, n2, n3], gap=G)
    return y2 + max(n1.h, n2.h, n3.h)


# ====================================================================== 4. storage
def section_storage(cv, y):
    _, b = section_header(cv, 0, y, "4  Managed vs bring-your-own storage", size=34,
                          sub="By default Foundry stores data in Microsoft-managed accounts; with the standard agent setup you bring Storage, Cosmos DB and AI Search, isolated per project.")
    top = b + 34
    hw = (W - G) / 2
    managed = Card(C3, "Default: Microsoft-managed", [
        "Microsoft-managed storage accounts, logically separated, for direct file upload (OpenAI models, Agents)",
        "Basic agent setup: threads, messages and files in Microsoft-managed multitenant storage with logical separation",
        "Without blobStore in the capability settings, agent files use Microsoft-managed storage",
    ], theme="gray", icon="storage", src=[BYOS, STD])
    byo = Card(C3, "Standard setup: you bring the stores", [
        "Storage for files, AI Search for vector stores, Cosmos DB for messages, conversation history and agent metadata",
        "Isolated per project: two blob containers and Cosmos DB containers are provisioned automatically per project",
        "Private network isolation of agent outbound traffic is available for the standard setup only",
    ], theme="cyan", icon="cosmos", src=[STD, BYOS])
    sett = Card(C3, "Required storage account settings", [
        "allowSharedKeyAccess = false (Foundry uses Entra and the project managed identity)",
        "minimumTlsVersion = TLS1_2",
        "allowBlobPublicAccess = false",
        "allowCrossTenantReplication = false (recommended)",
    ], theme="cyan", icon="storage", src=[BYOS])
    _, b1 = row(cv, 0, top, [managed, byo, sett], gap=G)

    y2 = b1 + 40
    appr = Table([("Approach", 230), ("What it is", 560), ("Notes", 420)], [
        [("Connections", "cyan"), "A shared data pointer for Agents, Evaluations, Datasets and Content Understanding", "Create the connection in the project or resource"],
        [("Capability settings", "cyan"), "blobStore and the other settings, set through the API version 2026-07-15-preview", "The caller needs Storage Blob Data Contributor and Cosmos DB Operator"],
        [("userOwnedStorage", "cyan"), "Speech and Language only: one shared account, set at resource creation", "Breaking it stops Speech and Language"],
    ], w=hw, theme="cyan", size=14, head_size=15, title="Three ways to bring your own storage", title_size=22)
    appr.place(cv, 0, y2)
    cb = cite(cv, 0, appr.bottom + 8, [BYOS, STD])
    roles = Table([("Project managed identity role", 420), ("Scope", 520), "Note"], [
        [("Storage Account Contributor", "cyan"), "The storage account", ""],
        [("Storage Blob Data Contributor", "cyan"), "<workspaceId>-azureml-blobstore", ""],
        [("Storage Blob Data Owner", "cyan"), "<workspaceId>-azureml-agent", "Docs disagree: other pages name the container agents-blobstore"],
    ], w=hw, theme="cyan", size=14, head_size=15, title="Roles the project managed identity needs on BYO storage", title_size=22)
    roles.place(cv, hw + G, y2)
    cb2 = cite(cv, hw + G, roles.bottom + 8, [BYOS, ADMIN])

    y3 = max(cb, cb2) + 30
    plan = Table([("Capability", 330), ("Project-level isolation, BYO storage and networking", 1500), "Plan accordingly"], [
        [("Agents, evaluations, datasets", "teal"), "Supported", "Use projects as the isolation boundary"],
        [("Fine-tune training", "orange"), "No per-project isolation: the default project only", "Use separate Foundry resources"],
        [("OpenAI image, video and batch", "orange"), "No project isolation; BYO storage is partial (batch only)", "Plan at the resource level"],
        [("Content Understanding", "orange"), "You can organise by project, but there is no RBAC isolation", "Do not rely on project RBAC for separation"],
        [("Speech and Language", "orange"), "BYO storage is needed for full CMK coverage", "Configure userOwnedStorage at resource creation"],
        [("Translator", "orange"), "Resource level only", "Plan at the resource level"],
    ], w=W, theme="teal", size=14, head_size=15, title="Isolation and BYO support differ by API", title_size=22)
    plan.place(cv, 0, y3)
    cb3 = cite(cv, 0, plan.bottom + 8, [PLAN])
    return cb3


# ====================================================================== 5. security baseline
FAM = {"NS": "indigo", "IM": "red", "PA": "pink", "DP": "cyan", "AM": "grape", "LT": "violet", "PV": "orange", "ES": "yellow", "BR": "green"}


def baseline_rows(spec):
    rows = []
    for fam, ctrl, sup, dflt, resp, note in spec:
        rows.append([(fam, FAM[fam]), ctrl, sup, dflt, resp, note])
    return rows


def section_baseline(cv, y):
    _, b = section_header(cv, 0, y, "5  Security baseline: Microsoft Cloud Security Benchmark control families", size=34,
                          sub="Supported = the control applies to Foundry; On by default; Who is responsible. The page is based on MCSB v1.0 and may contain outdated guidance (as of 2026-11-03).")
    top = b + 34
    hw = (W - G) / 2
    cols = [("Family", 70), ("Control", 330), ("Supported", 90), ("On by default", 100), ("Responsible", 130), "Note"]
    left = baseline_rows([
        ("NS", "NS-1 VNet integration", Y, N, "Shared", "Private Link, managed network isolation"),
        ("NS", "NS-1 NSG support", Y, N, "Customer", ""),
        ("NS", "NS-2 Private Link", Y, N, "Customer", ""),
        ("NS", "NS-2 Disable public access", Y, N, "Customer", ""),
        ("IM", "IM-1 Entra data-plane auth", Y, Y, "Microsoft", "RBAC with predefined roles"),
        ("IM", "IM-1 Local auth to the data plane", N, D, "-", "'Not supported' per the baseline - docs disagree"),
        ("IM", "IM-3 Managed identities", Y, N, "Customer", ""),
        ("IM", "IM-3 Service principals", Y, N, "Customer", ""),
        ("IM", "IM-7 Conditional Access", Y, N, "Customer", ""),
        ("IM", "IM-8 Key Vault integration", Y, Y, "Microsoft", "Secrets not retrievable across projects"),
        ("PA", "PA-1 Local admin accounts", Y, Y, "Microsoft", "Compute-instance root access: avoid local auth"),
        ("PA", "PA-7 Azure RBAC for the data plane", Y, Y, "Microsoft", ""),
        ("PA", "PA-8 Customer Lockbox", N, D, "-", "Not supported"),
        ("DP", "DP-1 Sensitive-data discovery", N, D, "-", "Use network isolation and access management"),
        ("DP", "DP-2 Data loss prevention", N, D, "-", "Use network isolation and access management"),
        ("DP", "DP-3 In-transit encryption", Y, Y, "Microsoft", ""),
        ("DP", "DP-4 Platform-key encryption at rest", Y, Y, "Microsoft", ""),
        ("DP", "DP-5 Customer-managed keys", Y, N, "Customer", "Opt-in; see section 1"),
        ("DP", "DP-6 Key management in Key Vault", Y, Y, "Microsoft", ""),
        ("DP", "DP-7 Certificate management in Key Vault", N, D, "-", ""),
    ])
    right = baseline_rows([
        ("AM", "AM-2 Azure Policy", Y, N, "Customer", "Policies are not enabled by default"),
        ("AM", "AM-5 Adaptive application controls", N, D, "-", ""),
        ("LT", "LT-1 Microsoft Defender", Y, N, "Customer", ""),
        ("LT", "LT-4 Resource logs", Y, Y, "Microsoft", ""),
        ("PV", "PV-3 Automation State Configuration", N, D, "-", ""),
        ("PV", "PV-3 Guest Configuration", Y, N, "Customer", ""),
        ("PV", "PV-3 Custom VM images", N, D, "-", ""),
        ("PV", "PV-3 Custom container images", Y, N, "Customer", ""),
        ("PV", "PV-5 Defender vulnerability assessment", Y, N, "Customer", ""),
        ("PV", "PV-6 Automation Update Management", N, D, "-", "Microsoft patches (see the vulnerability-management page)"),
        ("ES", "ES-1 Endpoint detection and response", N, D, "-", ""),
        ("ES", "ES-2 Anti-malware", N, D, "-", ""),
        ("ES", "ES-3 Anti-malware health", Y, N, "Customer", "Compute instance"),
        ("BR", "BR-1 Azure Backup", Y, N, "Customer", "Storage account"),
        ("BR", "BR-1 Service-native backup", N, D, "-", ""),
    ])
    t1 = Table(cols, left, w=hw, theme="gray", size=14, head_size=14, pad_x=6, align=["center", "left", "center", "center", "left", "left"],
               title="Network, identity, privileged access and data protection", title_size=22)
    t2 = Table(cols, right, w=hw, theme="gray", size=14, head_size=14, pad_x=6, align=["center", "left", "center", "center", "left", "left"],
               title="Assets, logging, posture, endpoint and backup", title_size=22)
    t1.place(cv, 0, top)
    t2.place(cv, hw + G, top)
    cb = cite(cv, hw + G, t2.bottom + 8, [BASE])
    legend(cv, hw + G, cb + 12, [("NS network", "indigo"), ("IM identity", "red"), ("PA privileged", "pink"), ("DP data", "cyan"), ("AM assets", "grape"),
                                 ("LT logging", "violet"), ("PV posture", "orange"), ("ES endpoint", "yellow"), ("BR backup", "green")], size=14, gap=16)
    n1 = Note(hw, "Page banner: based on a previous Microsoft Cloud Security Benchmark (v1.0) and 'may contain outdated guidance'; it includes hub and compute-instance era content. "
                  "Profile: AI + ML; customer can access the host or OS: Full Access; deployable into a customer VNet: True; stores customer content at rest: True.",
              kind="info", title="Read the baseline with its age in mind", src=[BASE])
    n1.place(cv, hw + G, cb + 56)
    n2 = Note(hw, "The baseline says local authentication to the data plane is 'not supported', yet the authentication and authorization page documents API keys. "
                  "Treat the baseline as guidance on control families, not as the current auth matrix. Customer Lockbox (PA-8) is not supported for Foundry.",
              kind="warn", title="Docs disagree: local auth", src=[BASE, ("Authentication and authorization", L("concepts/authentication-authorization-foundry"))])
    n2.place(cv, hw + G, n1.bottom + 22)
    return max(t1.bottom, n2.bottom)


# ====================================================================== 6. compliance + governance
def section_compliance(cv, y):
    _, b = section_header(cv, 0, y, "6  Compliance, governance integrations and sovereign cloud", size=34,
                          sub="What layers on top of the platform: certifications, Defender for Cloud, Purview, guardrail policies, diagnostic logs and Agent 365 data collection. As of 2026-11-03.")
    top = b + 34
    comp = Card(C4, "Compliance offerings", [
        "The Foundry docs defer to the Azure compliance documentation, the Data Processing Addendum and the Microsoft Trust Center",
        "! The pages read for this canvas do not list per-service certifications: check the Azure compliance documentation for current attestations",
    ], theme="gray", icon="compliance", src=[("Azure compliance documentation", L("azure/compliance/", base=""))])
    dfc = Card(C4, "Microsoft Defender for Cloud", [
        "Roles: Security Admin or Owner",
        "Posture recommendations for Foundry resources",
        "Threat protection for Foundry Tools raises alerts for jailbreak and user-input attacks",
    ], theme="violet", icon="defender", src=[ADMIN, CPC])
    gp = Card(C4, "Guardrail policies", [
        "Azure Policy through the control plane requires minimum guardrail controls (content filters, prompt shields, abuse detection) across a subscription or resource group",
        "Owner or Resource Policy Contributor; up to 30 minutes to appear",
    ], theme="pink", icon="policy", src=[CPC])
    dl = Card(C4, "Diagnostic logging", [
        "Categories: Audit Logs, Request and Response Logs, Azure OpenAI Request Usage, AllMetrics",
        "To Storage (insights-logs-<category>) and Log Analytics; up to about 2 hours before data appears",
        "Policy: Diagnostic logs in Azure AI services resources should be enabled",
    ], theme="violet", icon="log-analytics", src=[DIAG])
    _, b1 = row(cv, 0, top, [comp, dfc, gp, dl], gap=50)

    y2 = b1 + 40
    a365 = Card(C3, "Agent 365 data collection", [
        "Needs an Agent 365 license and tenant consent and a365LoggingEnabled = true",
        "The flag defaults to true per Foundry resource once Agent 365 is enabled for the tenant; a365Status is read-only: Enabled, Disabled or NotLicensed",
        "Applies resource-wide: no per-project or per-agent override",
        "Hosted agents using the Foundry hosting libraries export automatically; explicit Agent 365 SDK configuration in the agent code can override",
        "Opt out per resource, or enforce with Azure Policy",
    ], theme="violet", icon="agent", src=[A365D, ("Agent 365 integration", L("agents/concepts/agent-365-integration"))])
    pur = Card(C3 + 400, "Microsoft Purview", [
        "Toggle in Foundry: Operate > Compliance > Data security and governance (Powered by Microsoft Purview); needs Foundry Account Owner and a tenant Purview license",
        "Pay-as-you-go meters or an Agent 365 subscription are needed, otherwise Audit only",
        "Provides Audit, sensitive-information-type classification, DSPM for AI, Insider Risk, Communication Compliance, Data Lifecycle Management and eDiscovery",
        "! Data security policies enforce only for Microsoft Entra user-context tokens on /chat/completions (AzureUserSecurityContext); other auth paths are audit and classification only",
        "! Not yet compatible with network isolation",
    ], theme="violet", icon="info-protection", src=[CPC])
    pur.place(cv, 0, y2, h=max(pur.h, a365.h))
    a365.place(cv, pur.right + 50, y2, h=max(pur.h, a365.h))
    # Purview flow
    fx = a365.right + 50
    fw = W - fx
    fy = y2
    fa = Box(fw, "Foundry Account Owner turns on Purview", sub="Per subscription, in Operate > Compliance", theme="violet", size=18, sub_size=14, h=100, icon="user", icon_pos="left")
    fb = Box(fw, "Interaction data flows to your tenant's Purview", sub="Audit always; classification, DSPM for AI and the other solutions", theme="violet", size=18, sub_size=14, h=100, icon="info-protection", icon_pos="left")
    fc = Box(fw, "Policy enforcement is conditional", sub="Only for Entra user-context tokens; PAYG or Agent 365 required", theme="orange", size=18, sub_size=14, h=100, icon="policy", icon_pos="left")
    fa.place(cv, fx, fy + 26)
    fb.place(cv, fx, fa.bottom + 56)
    fc.place(cv, fx, fb.bottom + 56)
    cv.text(fx, fy - 6, "Enable Purview, in three steps", size=20, color=THEMES["violet"].deep)
    connect(cv, fa, fb, a_side="bottom", b_side="top", sw=3, gap=4)
    connect(cv, fb, fc, a_side="bottom", b_side="top", sw=3, gap=4)
    y3 = max(pur.bottom, a365.bottom, fc.bottom) + 50

    # Azure Government
    with cv.panel(0, y3, title="Azure Government", sub="Foundry and Agent Service in the US sovereign cloud: what is available and what is not", theme="indigo", style="dotted", pad=26,
                  title_size=26, sub_size=16, w=W) as gp_:
        gw = (W - 2 * 26 - 2 * 50) / 3
        endpoints = Card(gw, "Regions and endpoints", [
            "Regions: usgovvirginia, usgovarizona",
            "Foundry portal: https://ai.azure.us/nextgen; Azure portal: https://portal.azure.us",
            "Project endpoint: https://{resource}.services.ai.azure.us/api/projects/{project}",
            "Token scope: https://ai.azure.us/.default",
            "SDK: azure-ai-projects 2.0.0 or later, with credential_scopes",
        ], theme="indigo", icon="regions", src=[GOV, GOVA])
        avail = Card(gw, "Available", [
            "+ Agent identity (Entra)",
            "+ Private networking (VNet integration) and Network Security Perimeter",
            "+ RBAC",
            "+ Content safety and guardrails: block lists, jailbreak detection, protected materials",
            "+ Prompt-agent tracing",
            "# In preview",
            "Workflows; Custom Code Interpreter",
        ], theme="green", icon="foundry", src=[GOVA])
        navail = Card(gw, "Not available", [
            "! Model router, evaluations, optimization",
            "! Voice agents and hosted agents",
            "! Web search, Grounding with Bing, Image Generation, Browser Automation, Computer Use",
            "! Fabric, SharePoint and A2A",
        ], theme="red", icon="alerts", src=[GOVA])
        row(cv, gp_.ix, gp_.iy + 10, [endpoints, avail, navail], gap=50)
        nn = Note(W - 2 * 26, "Preview features may not carry the same compliance commitments (FedRAMP, DoD IL5, CJIS): confirm before regulated use. The availability lists come from the "
                  "Azure Government pages as of 2026-11-03.", kind="warn", title="Confirm commitments for preview features", src=[GOV])
        nn.place(cv, gp_.ix, gp_.iy + 10 + max(endpoints.h, avail.h, navail.h) + 26)
    return gp_.bottom


def build(cv: Canvas) -> None:
    _, bottom = title_block(cv, 0, 0, "Data protection, part 2: encryption keys, secrets, storage and compliance",
                            "Customer-managed keys end to end, the Key Vault for connection secrets, managed vs your own storage and the compliance layers - as of 2026-11-03",
                            icon="foundry", w=W)
    y = stamps(cv, bottom + 40) + 70
    y = section_cmk(cv, y) + 70
    y = section_enable(cv, y) + 70
    y = section_secrets(cv, y) + 70
    y = section_storage(cv, y) + 70
    y = section_baseline(cv, y) + 70
    y = section_compliance(cv, y) + 70
    nxt = Note(W, "Part 1 'Data protection and encryption: where your data lives' has the trust-boundary map, the commitments, residency by deployment type, abuse monitoring, trace content and the "
                  "Customer Copyright Commitment. See also 'Foundry roles, scopes and least-privilege assignments' for the roles used here and 'Network isolation' for private endpoints to the key store.",
               kind="key", title="Back to part 1", size=16)
    nxt.place(cv, 0, y)
    y = nxt.bottom + 60
    sources(cv, 0, y, [
        ("Customer-managed keys for Foundry", L("concepts/customer-managed-keys")),
        ("Customer-managed keys in the portal", L("concepts/encryption-keys-portal")),
        ("Set up a Key Vault connection", L("how-to/set-up-key-vault-connection")),
        ("Bring your own Azure Storage", L("how-to/bring-your-own-azure-storage-foundry")),
        ("Standard agent setup", L("agents/concepts/standard-agent-setup")),
        ("Plan your Foundry rollout", L("concepts/planning")),
        ("Azure security baseline for Foundry", L("azure-ai-foundry-security-baseline", base="security/benchmark/azure/baselines")),
        ("Manage compliance and security (control plane)", L("control-plane/how-to-manage-compliance-security")),
        ("Diagnostic logging", L("how-to/diagnostic-logging")),
        ("Agent 365 integration", L("agents/concepts/agent-365-integration")),
        ("Configure Agent 365 data collection", L("agents/how-to/configure-agent-365-data-collection")),
        ("Foundry in Azure Government", L("concepts/foundry-azure-government")),
        ("Agent Service in Azure Government", L("agents/concepts/azure-government")),
        ("Azure compliance documentation", L("azure/compliance/", base="")),
        ("Foundry administrator guide", L("concepts/administrator-guide")),
    ], w=W, cols=3)
