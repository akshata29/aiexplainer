"""Microsoft Foundry in an Azure landing zone, part 2: Foundry resource ownership models and the rollout path, Azure Policy
guardrails and where they attach, subscription vending and CI/CD, the AI Landing Zones accelerators and Well-Architected notes."""
from __future__ import annotations

import os

from generator.diagrams.ra_landing_zone import (
    W, SRC_ALZ, S_ALZ, S_AILZ, S_AILZ_AGENT, S_AILZ_CFG, S_AILZ_CHECK, S_AILZ_DOCS, S_AILZ_FAQ, S_AILZ_GW, S_AILZ_NET,
    S_AILZ_PLAN, S_ARCH, S_BASE, S_CAF_AI, S_CAF_LZ, S_CAF_PLAN, S_CAF_SHARE, S_CUSTOM_POL, S_MODEL_POL, S_PLAN, S_POL_REF,
    S_PRIVLINK, S_VEND, Node, learn_line, pill)
from generator.xd import *
from generator.xd import theme as get_theme

META = dict(
    id="ra-landing-zone-part-2", title="Foundry in an Azure landing zone, part 2", section="3", order=3.5,
    description="Foundry resource ownership models and the rollout path, Azure Policy guardrails and where they attach, "
                "subscription vending and CI/CD, the AI Landing Zones accelerators and Well-Architected notes.",
    tags=["landing-zone", "ownership-models", "policy", "vending", "ai-landing-zones", "well-architected"],
)

S_CAF_SHARE_L = ("AI platform sharing, isolation and colocation (CAF)", S_CAF_SHARE[1])
SRC_PLAN = [("Foundry rollout across my organization", S_PLAN[1])]
SRC_SHARE = [("AI platform sharing decision guidance (CAF)", S_CAF_SHARE[1])]
SRC_AILZ = [("AI Landing Zones (GitHub)", S_AILZ[1])]


# ----------------------------------------------------------------------------------------------------- sections
def _head(cv):
    right, bottom = title_block(
        cv, 0, 0, "Microsoft Foundry in an Azure landing zone, part 2",
        "Ownership models, Azure Policy guardrails, subscription vending and CI/CD, the AI Landing Zones accelerators and "
        "Well-Architected notes (facts as of 2026-11-03)", icon="foundry", w=W)
    y = bottom + 46
    cw, gap = 688, 40
    cards = [
        Card(cw, "One Foundry resource per production workload", [
            "Production: isolation is the default; colocation only by a documented exception",
            "Exploration: colocation is the default (one shared resource, one project per use case)",
            "Not recommended: a central resource per business group with a project per workload",
        ], theme="blue", icon="foundry", src=SRC_PLAN),
        Card(cw, "Guardrails come from Azure Policy", [
            "Approve models and tools: audit first, then deny",
            "Deny public network access and local (key) authentication",
            "Custom policy for connection categories; evaluated at deployment time",
        ], theme="grape", icon="policy", src=[("Built-in policies for model deployment", S_MODEL_POL[1])]),
        Card(cw, "Vend the subscription, deploy from a pipeline", [
            "The platform assigns the MG and creates the subscription, spoke, peering, UDRs, DNS and policy",
            "The workload deploys infrastructure as code from network-connected build agents",
            "Agents as code; pinned model and agent versions",
        ], theme="yellow", icon="subscription", src=[("Subscription vending (CAF)", S_VEND[1])]),
        Card(cw, "AI Landing Zones speeds it up", [
            "Azure/AI-Landing-Zones: an Agent Landing Zone and an AI Gateway Landing Zone",
            "Bicep and Terraform on Azure Verified Modules; with or without a platform landing zone",
            "Default spoke VNet 192.168.0.0/21",
        ], theme="teal", icon="github", badge="preview", src=SRC_AILZ),
        Card(cw, "Well-Architected view", [
            "Reliability: multi-region means separate Foundry resources; no built-in Agent Service DR",
            "Security: keep NSGs next to hub non-transitivity; WAF in deny mode; Purview",
            "Cost: firewall and DDoS become shared platform costs",
        ], theme="orange", icon="service-health", src=SRC_ALZ),
    ]
    r, b = row(cv, 0, y, cards, gap=gap)
    y = b + 26
    legend(cv, 0, y, [("Platform team (yellow)", "yellow"), ("Workload team (blue)", "blue"),
                      ("Policy and governance (grape)", "grape"), ("Networking (indigo)", "indigo"),
                      ("Identity and security (red)", "red"), ("Agents (green)", "green"), ("Data (cyan)", "cyan"),
                      ("Observability (violet)", "violet")], size=16, gap=30)
    cv.text(0, y + 30, "Part 1 (Foundry in an Azure landing zone) covers the management groups, the hub-spoke topology, who owns "
                       "what, DNS and egress, and the Agent Service gotchas.", size=14, color="#495057")
    return y + 72


def _wrap(s, w, size):
    return "\n".join(wrap_text(s, w, size))


def _models(cv, y):
    r, b = section_header(
        cv, 0, y, "1  Who owns the Foundry resource: centralized or federated",
        sub="One shared resource with a project per workload, or one resource per workload. The landing-zone article recommends the "
            "second; the planning guide and CAF explain when sharing is acceptable (as of 2026-11-03)", size=34, w=W)
    y0 = b + 34
    PW = 1780
    strip_h = 76

    def platform_strip(p, w):
        return Box(w, "Platform landing zone", sub="management groups and policy, hub network, private DNS, firewall, DDoS Protection",
                   icon="landing-zone", icon_pos="left", theme="yellow", h=strip_h, size=18, sub_size=13).place(cv, p.ix, p.iy)

    # ---- federated
    with cv.panel(0, y0, title="Federated: one Foundry resource per workload", theme="blue", style="dotted", pad=18,
                  title_size=26, sub_size=14, w=PW,
                  sub="Recommended topology in the landing-zone article; the production default in the planning guide") as pl:
        inner = PW - 36
        strip = platform_strip(pl, inner)
        ww = (inner - 2 * 32) / 3
        wy = strip.bottom + 74
        wps = []
        for i, nm in enumerate("ABC"):
            x = pl.ix + i * (ww + 32)
            with cv.panel(x, wy, title=f"Workload {nm} subscription", theme="blue", style="solid", fill="soft", pad=14,
                          title_size=18, w=ww) as wp:
                with cv.panel(wp.ix, wp.iy, title="Foundry resource", sub="own quota, network and identity", theme="blue",
                              style="dashed", pad=12, title_size=17, sub_size=12, w=ww - 28) as fp:
                    Box(ww - 28 - 24, "Project", sub="agents, connections, evaluations", icon="foundry", icon_pos="left",
                        theme="green", h=58, size=15, sub_size=12, icon_size=28).place(cv, fp.ix, fp.iy)
                dw = (ww - 28 - 16) / 3
                for j, (lab, ic) in enumerate((("Cosmos DB", "cosmos"), ("Storage", "storage"), ("AI Search", "ai-search"))):
                    Box(dw, lab, icon=ic, icon_pos="top", theme="cyan", h=70, size=13, icon_size=26).place(
                        cv, wp.ix + j * (dw + 8), fp.bottom + 14)
                cv.text(wp.ix, fp.bottom + 92, "Agent Service dependencies: workload-owned", size=12, color="#0b7285")
            wps.append(wp)
        for wp in wps:
            arrow(cv, [(wp.cx, strip.bottom + 6), (wp.cx, wp.y - 6)], sw=3, color="#9c36b5", dash="dashed")
        cv.text(wps[1].cx + 14, strip.bottom + 28, "policy, DNS and egress apply to every workload subscription", size=13,
                color="#862e9c")
        cv.text(pl.ix, wps[0].bottom + 14, "Strict containment, independent access control, quota and cost per workload. "
                                           "Trade-off: harder self-serve, more resources and setup overhead.", size=14,
                color="#495057")

    # ---- centralized
    XR = PW + 40
    with cv.panel(XR, y0, title="Centralized: one shared Foundry resource, a project per workload", theme="red", style="dotted",
                  pad=18, title_size=26, sub_size=14, min_h=pl.h, w=PW,
                  sub="One resource per business group. Not recommended by the landing-zone article") as pr:
        inner = PW - 36
        strip = platform_strip(pr, inner)
        with cv.panel(pr.ix, strip.bottom + 74, title="Shared Foundry resource (one per business group)", theme="blue",
                      style="dashed", fill="soft", pad=16, title_size=20, w=inner) as sp:
            pw3 = (inner - 32 - 2 * 24) / 3
            prj = []
            for i, nm in enumerate("ABC"):
                prj.append(Box(pw3, f"Workload {nm} project", sub="agents, connections", icon="foundry", icon_pos="left",
                               theme="green", h=76, size=16, sub_size=13, icon_size=30).place(cv, sp.ix + i * (pw3 + 24), sp.iy))
            Box(inner - 32, "One set of model deployments, quota, network and identity boundary for every project",
                theme="gray", h=60, size=15, fill="soft").place(cv, sp.ix, prj[0].bottom + 16)
        arrow(cv, [(sp.cx, strip.bottom + 6), (sp.cx, sp.y - 6)], sw=3, color="#9c36b5", dash="dashed")
        cv.text(sp.cx + 14, strip.bottom + 28, "policy, DNS and egress", size=13, color="#862e9c")
        Note(inner, "The landing-zone article doesn't recommend it, citing resource-organization and cost-allocation limitations. "
                    "Co-location also shares the blast radius: incidents, quota exhaustion and misconfiguration. The planning guide "
                    "still uses a shared resource for exploration and prototypes: see the rollout path below.",
             kind="gotcha", title="Why the article does not recommend it for workloads", size=15,
             src=[S_ALZ, ("Foundry rollout across my organization", S_PLAN[1])]).place(cv, pr.ix, sp.bottom + 20)
    return max(pl.bottom, pr.bottom) + 50


def _sharing(cv, y):
    BL = get_theme("blue")
    # ---- rollout path (planning guide, sample Contoso deployment)
    with cv.panel(0, y, title="Rollout path in the planning guide: the sample Contoso platform deployment", theme="blue",
                  style="dotted", pad=20, title_size=24, sub_size=14, w=W,
                  sub="Use cases move from open exploration to progressively stronger isolation: only a handful reach dev/test, "
                      "and an even smaller subset reaches production") as rp:
        x0, y0 = rp.ix, rp.iy
        cv.text(x0, y0 + 6, "Use cases in the sample:", size=16, color="#495057")
        cx_ = x0 + 240
        for n in ("Customer support", "Employee helpdesk", "Finance ops", "Procurement", "Sales"):
            c = Chip(n, theme="gray", size=15).place(cv, cx_, y0)
            cx_ += c.w + 12
        bw, gp, bh = 1080, 150, 150
        sx = x0
        sy = y0 + 56
        s1 = Box(bw, "Shared exploration Foundry", sub="One instance for all teams: limited capacity, pre-connected data and "
                 "tools. Exploration defaults to colocation, one project per use case", icon="foundry", icon_pos="left",
                 theme="blue", fill="soft", h=bh, size=21, sub_size=15, sw=2).place(cv, sx, sy)
        s2 = Box(bw, "Development and test", sub="Isolated, or co-located when use cases share CRM data, personas and connected "
                 "systems, for example two sales use cases. Pre-production is shared per environment tier by default",
                 icon="foundry", icon_pos="left", theme="blue", fill="hatch", h=bh, size=21, sub_size=15, sw=3).place(
            cv, sx + bw + gp, sy)
        s3 = Box(bw, "Isolated production", sub="One Foundry resource per production workload boundary, often with one primary "
                 "project. Isolation is the default unless there is a documented exception", icon="foundry", icon_pos="left",
                 theme="blue", fill="solid", h=bh, size=21, sub_size=15, sw=5).place(cv, sx + 2 * (bw + gp), sy)
        connect(cv, s1, s2, a_side="right", b_side="left", sw=3, label="a handful", label_size=14)
        connect(cv, s2, s3, a_side="right", b_side="left", sw=3, label="fewer still", label_size=14)
        ya = s1.bottom + 28
        arrow(cv, [(sx, ya), (s3.right, ya)], sw=3, color=BL.stroke, dash="dashed")
        cv.text(sx + 10, ya + 6, "progressively stronger isolation, ownership and controls", size=15, color=BL.deep)
    learn_line(cv, 0, rp.bottom + 6, SRC_PLAN[0])
    y = rp.bottom + 44

    # ---- CAF sharing, isolation and colocation
    cv.text(0, y, "CAF decision guidance: sharing, isolation and colocation of an AI platform instance", size=24,
            color=get_theme("grape").deep)
    y += 40
    ws = [660, 1400, 700, 740]
    gp = (W - sum(ws)) / 3
    c1 = Card(ws[0], "1  Define the sharing boundaries", [
        "An AI platform instance is a network, identity and quota boundary",
        "Business unit: common operations and funding",
        "Data domain: common compliance",
        "Product owner: common lifecycle",
        "Consistency matters more than which model you pick",
    ], theme="grape", icon="management-group", src=SRC_SHARE)
    c2 = Card(ws[1], "2  Production: isolation is the default", [
        "# Colocate only by a documented exception, and only when ALL of these hold:",
        "Same regulatory scope, data classification, residency and data-handling standards",
        "Same network boundary, DNS namespace and identity boundary",
        "The organization accepts the shared outage risk and the shared quota exhaustion risk",
        "Separate instances cost materially more than isolation is worth: cost pressure alone isn't sufficient",
        "The team accepts that splitting later is costly: AI platform state doesn't transfer cleanly",
        "= Every shared instance also needs a named platform owner for quota management, network configuration, access reviews, "
        "lifecycle operations and incident coordination",
    ], theme="red", icon="defender", src=SRC_SHARE)
    c3 = Card(ws[2], "3  Segment use cases in the product", [
        "One Foundry project per use case inside the Foundry resource; when colocation is permitted, enforce it as a policy "
        "requirement",
        "Azure Machine Learning: a hub workspace with project workspaces",
        "Each use case gets its own assets and role assignments and shares the common security and connectivity infrastructure",
    ], theme="blue", icon="foundry", src=SRC_SHARE)
    c4 = Card(ws[3], "4  Pre-production: shared per environment tier", [
        "Development, test and stage default to one shared instance per environment tier",
        "A dedicated instance per workload only for regulated data in test, or to mirror the production topology for "
        "performance validation: an exception that needs explicit approval",
        "Trade-off: interference (a misconfigured fine-tuning job or runaway evaluation consumes shared quota), and results "
        "that don't always predict production",
    ], theme="teal", icon="deployment-environments", src=SRC_SHARE)
    r_, b_ = row(cv, 0, y, [c1, c2, c3, c4], gap=gp)
    y = b_ + 56

    # ---- capability x scope table
    G, R_, A = "green", "red", "yellow"
    Yes, No = ("Yes", G), ("No", R_)
    cols = [("Capability area", 470), ("Organize by project", 220), ("Project-level RBAC isolation", 250), ("BYO storage", 230),
            ("Network and encryption", 270), ("Implication", 570)]
    rows = [
        ["Agent capabilities: agents, responses, evaluations, datasets, indexes, files, playground", Yes, Yes, Yes,
         ("Limited in basic (managed storage): use standard", A), "Good fit for a project per use case"],
        ["Fine-tune training", ("No: default project only", R_), No, ("Partial: inputs only", A), Yes,
         "Separate Foundry resources if teams need independent fine-tuning; fine-tuned deployments are shared across the "
         "projects of a resource"],
        ["OpenAI image, video and batch", No, No, ("Partial: Batch only", A), Yes, "Isolated workload setup; validate RBAC early"],
        ["Content Understanding", Yes, No, Yes, Yes, "Strict per-use-case isolation needs separate resources"],
        ["Speech", ("Yes: fine-tune", G), No, Yes, ("Limited in basic", A), "Bring your own storage for full customer-managed keys"],
        ["Language", ("Yes: fine-tune", G), No, Yes, ("Limited in basic", A), "Bring your own storage for full customer-managed keys"],
        ["Translator", No, No, No, Yes, "A separate resource if isolation is required"],
    ]
    tc = Table(cols, rows, theme="blue", size=14, head_size=15,
               title="What you can isolate per project, and what needs its own Foundry resource", title_size=22).place(cv, 0, y)
    learn_line(cv, 0, tc.bottom + 8, SRC_PLAN[0])
    nest = Card(W - tc.w - 50, "How the pieces nest", [
        "Foundry resource = Microsoft.CognitiveServices/accounts of kind AIServices; a project is an accounts/projects "
        "subresource",
        "Connected resources (Storage, Key Vault, AI Search) are independent governance boundaries",
        "Connections can live at resource level (inherited by every project) or at project level",
        "Newer agent-centric APIs support project-scope permissions; some Foundry Tools APIs (for example speech-to-text) "
        "still need parent resource-scope access",
        "Control plane versus data plane RBAC: Owner and Contributor aren't enough to chat with an agent",
        "Azure Monitor metrics are segmented at resource level and project level",
        "Customer-managed keys need a Key Vault in the same region with soft delete and purge protection, and the Key Vault Crypto "
        "User role",
        "With your own Key Vault, one Azure Key Vault connection manages the secrets of all project-level and resource-level "
        "connections",
    ], theme="blue", icon="foundry", src=[("Microsoft Foundry architecture", S_ARCH[1]), SRC_PLAN[0]])
    nest.place(cv, tc.right + 50, y, h=max(nest.h, tc.h + 24))
    y = max(tc.bottom + 32, nest.bottom) + 50

    # ---- rollout checklist
    cv.text(0, y, "Rollout checklist from the planning guide", size=24, color=get_theme("grape").deep)
    y += 40
    cw = (W - 5 * 34) / 6
    items = [
        ("1  Define isolation boundaries", "grape", "management-group", [
            "Non-negotiable sharing boundaries: business unit, data domain, product ownership, environment tier",
            "Production defaults to isolation unless a documented exception",
            "Exploration defaults to colocation",
            "An owner per boundary: security, cost, incident response"]),
        ("2  Security baseline", "red", "defender", [
            "Identity: admin, project manager and project user personas map to Entra groups and least-privilege roles",
            "Networking: managed VNet (more secure, straightforward) or BYO VNet (advanced control, custom routing)",
            "Validate private DNS and endpoint approval before production",
            "Keys: Microsoft-managed or customer-managed. Auth: Entra ID and RBAC; API keys only where role granularity isn't "
            "required"]),
        ("3  Model, region and capacity", "blue", "quotas", [
            "Model families and deployment types",
            "Data processing: global or regional",
            "Throughput and latency needs",
            "Quota and provisioned capacity, for steady state and for peak"]),
        ("4  Connectivity and data", "indigo", "private-link", [
            "Inventory data stores, internal APIs and SaaS tools",
            "Plan private endpoints, DNS and egress; managed or BYO VNet",
            "Connections at resource level (inherited by all projects) or project level"]),
        ("5  Automation and ops", "green", "devops", [
            "Infrastructure as code with Bicep or Terraform",
            "Standard pipelines for projects, connections and model deployments",
            "Rollback and incident runbooks",
            "Samples for private networking, CMK and RBAC in the foundry-samples repo"]),
        ("6  Self-serve guardrails and governance", "violet", "policy", [
            "Who can create projects, deploy models and connect external tools; budget alerts",
            "Policy for model providers and tool connections",
            "Enforce trace logging into central observability across Foundry, Copilot Studio and M365",
            "Precreated Entra groups map to Foundry roles",
            "Dashboards: Control Plane fleet monitoring, Agent 365, Defender for Cloud, Azure Policy"]),
    ]
    cards = [Card(cw, t, bl, theme=th, icon=ic, title_size=19, body_size=14, src=SRC_PLAN) for t, th, ic, bl in items]
    r_, b_ = row(cv, 0, y, cards, gap=34)
    return b_ + 70


EFFECT_TH = {"Audit": "yellow", "Deny": "red", "Disabled": "gray", "Modify": "orange", "DINE": "teal", "Preview": "violet",
             "GA": "green"}
S_POL_FAM = ("Azure Policy built-ins for Foundry Tools", S_POL_REF[1])


def policy_card(cv, x, y, w, title, theme, icon, rows, note=None, dash="solid", h=None, src=None, size=14):
    """Card frame with policy rows: [(effects, text)] drawn as coloured effect pills + wrapped policy text."""
    th = get_theme(theme)
    PWD = 232                                  # width reserved for the effect pills
    tw = w - 32 - PWD - 8
    prepared = []
    total = 66
    for eff, text in rows:
        lines = wrap_text(text, tw, size)
        rh = max(len(lines) * size * 1.25, 24) + 12
        prepared.append((eff, lines, rh))
        total += rh
    nl = wrap_text(note, w - 32, 12) if note else []
    if nl:
        total += len(nl) * 15 + 12
    srcl = (src or [])
    total += len(srcl) * 16 + (10 if srcl else 0) + 16
    H = max(total, h or 0)
    with cv.group():
        cv.rect(x, y, w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2, dash=dash)
        place_icon(cv, icon, x + 16, y + 14, 36)
        cv.text(x + 64, y + 18, title, size=20, color=th.deep)
        cy = y + 66
        for eff, lines, rh in prepared:
            px = x + 16
            for e in eff:
                pw_, ph_ = pill(cv, px, cy + 2, e, EFFECT_TH.get(e, "gray"), 12, pad=7)
                px += pw_ + 6
            cv.text(x + 16 + PWD + 8, cy + 1, "\n".join(lines), size=size, color="#1e1e1e")
            cy += rh
        if nl:
            cv.text(x + 16, cy + 2, "\n".join(nl), size=12, color="#495057")
            cy += len(nl) * 15 + 12
        for label, url in srcl:
            cv.text(x + 16, cy + 6, f"Learn: {label}", size=12, color=LINK, link=url)
            cy += 16
    cv.register(f"policy:{title}", x, y, w, H)
    return Node(x, y, w, H)


def _policy(cv, y):
    GR = get_theme("grape")
    r, b = section_header(
        cv, 0, y, "2  Azure Policy guardrails and where they attach",
        sub="Policy and RBAC are assigned on management groups and inherited downwards. The Foundry policies are evaluated when a "
            "resource or deployment is created or changed (as of 2026-11-03)", size=34, w=W)
    y0 = b + 34
    LW = 1500
    # ---- where policy attaches (outline tree + stamps)
    rows = [
        (0, "Tenant root group", "grape", "management-group",
         "Policy and RBAC assigned here reach every management group and subscription below. In a landing zone, expect "
         "pre-existing management-group policies"),
        (1, "Platform", "grape", "management-group",
         "Platform-owned constraint and DINE policies: private DNS records, diagnostics to the central workspace, Azure "
         "Monitor baseline alerts. DINE is best-effort, no SLA"),
        (1, "Workload landing zones", "grape", "management-group",
         "AI-service policies applied through the hierarchy: Foundry model deployments, Foundry Tools, AI Search, VMs (CAF). "
         "Example placement: one assignment covers Corp and Online"),
        (2, "Corp (internal)", "grape", "management-group",
         "Internal AI workloads. There are no AI-specific management groups: reuse the Corp and Online boundaries"),
        (2, "Online (internet-facing)", "grape", "management-group",
         "Internet-facing AI workloads: public Application Gateway IP, DDoS Protection"),
        (3, "Workload subscription", "blue", "subscription",
         "Workload-specific policy, for example Application Gateway WAF in deny mode. Dev, test and prod subscriptions inherit "
         "the same MG policies: keep pre-production under the same policies as production"),
    ]
    with cv.panel(0, y0, title="Where policy attaches", sub="Model policies can be assigned at management group, subscription or "
                                                           "resource group scope: the placement below is an example",
                  theme="grape", style="dotted", pad=20, title_size=24, sub_size=14, w=LW) as tp:
        rh, nw = 84, 330
        nodes = []
        ry = tp.iy
        sx = tp.ix + nw + 3 * 46 + 30
        for lvl, label, th, ic, text in rows:
            nx = tp.ix + lvl * 46
            nb = Box(nw, label, h=60, theme=th, icon=ic, icon_pos="left", size=18, icon_size=30).place(cv, nx, ry + 8)
            nodes.append((lvl, nb))
            sw_ = tp.ix + LW - 40 - sx
            lines = wrap_text(text, sw_ - 70, 14)
            sh = max(len(lines) * 17.5 + 20, 60)
            with cv.group():
                cv.rect(sx, ry + 8 + 30 - sh / 2, sw_, sh, stroke=GR.stroke, fill=GR.soft, style="solid", sw=2, dash="dashed")
                place_icon(cv, "policy", sx + 12, ry + 8 + 30 - 16, 32)
                cv.text(sx + 56, ry + 8 + 30 - len(lines) * 17.5 / 2, "\n".join(lines), size=14, color="#1e1e1e")
            cv.register(f"stamp:{label}", sx, ry + 8 + 30 - sh / 2, sw_, sh)
            cv.line((nb.right + 4, nb.cy), (sx - 4, nb.cy), stroke=GR.stroke, sw=2, dash="dotted")
            ry += rh
        stack = []
        for lvl, nb in nodes:
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            if stack:
                pb = stack[-1][1]
                vx = pb.x + 24
                cv.line((vx, pb.bottom), (vx, nb.cy), stroke="#868e96", sw=2)
                cv.line((vx, nb.cy), (nb.x - 2, nb.cy), stroke="#868e96", sw=2)
            stack.append((lvl, nb))
    learn_line(cv, 0, tp.bottom + 6, S_CAF_AI)

    # ---- model deployment check (flow)
    yf = tp.bottom + 56
    cv.text(0, yf, "How a model deployment is checked", size=24, color=GR.deep)
    yf += 40
    bw, gp, bh = 300, 100, 110
    f1 = Box(bw, "Deploy a model", sub="portal, ARM or CLI", icon="gpt", icon_pos="left", theme="gray", h=bh, size=18,
             sub_size=14).place(cv, 0, yf)
    f2 = Box(bw, "Approved models", sub="allowedPublishers, allowedAssetIds: IDs match as prefixes", icon="policy",
             icon_pos="left", theme="grape", h=bh, size=18, sub_size=13).place(cv, bw + gp, yf)
    f3 = Box(bw, "Eligibility", sub="onlyAllowDirectFromAzure, denyPreviewModels", icon="policy", icon_pos="left",
             theme="grape", h=bh, size=18, sub_size=13).place(cv, 2 * (bw + gp), yf)
    f4 = Box(bw, "Allowed", sub="the Deploy button works", icon="foundry", icon_pos="left", theme="green", h=56, size=18,
             sub_size=13).place(cv, 3 * (bw + gp), yf - 6)
    f5 = Box(bw, "Blocked", sub="Deploy is disabled with the reason; ARM and CLI fail", icon="chaos", icon_pos="left",
             theme="red", h=64, size=18, sub_size=13).place(cv, 3 * (bw + gp), yf + 62)
    connect(cv, f1, f2, a_side="right", b_side="left", sw=3)
    connect(cv, f2, f3, a_side="right", b_side="left", sw=3, label="approved first", label_size=13)
    connect(cv, f3, f4, a_side="right", b_side="left", sw=3, route="elbow", label="then", label_size=13)
    connect(cv, f3, f5, a_side="right", b_side="left", sw=3, route="elbow", dash="dashed", color="#e03131")
    learn_line(cv, 0, f1.bottom + 10, ("Built-in policies for model deployment", S_MODEL_POL[1]))
    yl = f1.bottom + 40

    # ---- policy families (right)
    XR = LW + 50
    CW = (W - XR - 40) / 2
    pm = policy_card(cv, XR, y0, CW, "Model governance", "grape", "policy", [
        (["GA", "Audit", "Deny", "Disabled"], "Foundry model deployments should only use approved models: parameters "
                                              "allowedPublishers and allowedAssetIds"),
        (["GA", "Audit", "Deny"], "Foundry model deployments should meet eligibility requirements: parameters "
                                  "onlyAllowDirectFromAzure and denyPreviewModels (both default to false)"),
        (["Preview"], "Microsoft Foundry agents and toolboxes should only use approved tools, and should not use denied tools: "
                      "restrict tool types, MCP endpoints and MCP connectors"),
        (["Preview", "Audit", "Disabled"], "Content-filter policies for agents and for deployments"),
        (["Preview"], "Model router policies: regions, rules, logging"),
    ], note="Definition IDs: approved models aafe3651-cb78-4f68-9f81-e7e41509110f (formerly 'Cognitive Services Deployments "
            "should only use approved Registry Models'); eligibility 8791d062-ba96-4c34-b604-8538f7e30ca0; approved tools "
            "e7352ad2-6c86-4a07-9573-47f67b557ba8; denied tools 7740c22b-07ef-4bac-9f5a-e38d188f80b7",
        src=[("Built-in policies for model deployment", S_MODEL_POL[1])])
    pn = policy_card(cv, XR, pm.bottom + 24, CW, "Network", "indigo", "private-link", [
        (["Audit", "Deny"], "Restrict network access for Azure AI Services resources"),
        (["Audit"], "Use Azure Private Link"),
        (["Modify"], "Disable public network access on Cognitive Services accounts"),
        (["DINE"], "Configure Cognitive Services accounts with private endpoints"),
    ], src=[S_POL_FAM])
    pi = policy_card(cv, XR + CW + 40, y0, CW, "Identity and keys", "red", "key-vault", [
        (["Audit", "Deny"], "Key access disabled: disable local authentication"),
        (["Modify"], "Configure accounts to disable local authentication methods"),
        (["DINE"], "Configure Azure AI Services resources to disable local key access"),
        (["Audit", "Deny"], "Use a managed identity"),
        (["Audit", "Deny"], "Encrypt data with customer-managed keys (CMK)"),
        (["Audit", "Deny"], "Use customer owned storage"),
    ], note="Names in the Network, Identity and Observability cards are paraphrased: exact names and IDs are in the policy reference.",
        src=[S_POL_FAM])
    po = policy_card(cv, XR + CW + 40, pi.bottom + 24, CW, "Observability", "violet", "diagnostics", [
        (["DINE"], "Diagnostic settings to Log Analytics, Event Hub or Storage"),
        (["Audit"], "Diagnostic logs in Azure AI services resources should be enabled"),
    ], src=[S_POL_FAM])
    cc = Card(CW, "Custom policy definitions", [
        "Allow only approved connection categories: field category notIn allowedCategories on "
        "Microsoft.CognitiveServices/accounts[/projects]/connections",
        "Deny connections that use API-key authentication",
        "Audit accounts without valid agent capability settings (VNet subnet ARM ID and custom storage)",
        "Deny account kinds that lack full Foundry capabilities",
        "Samples: foundry-samples, 05-custom-policy-definitions. Needs Resource Policy Contributor or Owner",
    ], theme="grape", icon="policy", dash="dashed", src=[("Custom policy definitions for Foundry", S_CUSTOM_POL[1])])
    cc.place(cv, XR + CW + 40, po.bottom + 24)
    yb = max(yl, pn.bottom + 24, cc.bottom) + 40

    # ---- behaviour and gotchas
    nw3 = (W - 2 * 50) / 3
    n1 = Note(nw3, "Evaluated at deployment time. The catalog doesn't hide models: the Deploy button is disabled with the reason "
                   "(approval is checked first, then eligibility). The policies also cover the models a model router selects: "
                   "with ARM or CLI one noncompliant model fails the whole deployment, so allow the Microsoft publisher for the "
                   "router plus every publisher in its routing set. Assigning needs Owner or Resource Policy Contributor; wait "
                   "about 15 minutes for a new assignment and up to 24 hours for compliance data.",
              kind="info", title="How the model policies behave", size=15, src=[("Built-in policies for model deployment", S_MODEL_POL[1])])
    n2 = Note(nw3, "From the landing-zone article: 'Secrets should have the specified maximum validity period' (Foundry connection "
                   "secrets have no expiry), 'AI Search services should use customer-managed keys to encrypt data at rest', and "
                   "'Foundry models should not be preview' (a developer using a preview model). DINE policies are best-effort "
                   "with no SLA.", kind="gotcha", title="Landing-zone policies can collide with Foundry defaults", size=15,
              src=SRC_ALZ)
    n3 = Note(nw3, "Bing grounding, web search and SharePoint tools use public endpoints even when the Foundry resource is "
                   "isolated: block them with Azure Policy if your organization forbids it. For models, audit first and enforce "
                   "(deny) afterwards.", kind="warn", title="Tool egress is a policy decision too", size=15,
              src=[("Configure private link for Foundry", S_PRIVLINK[1]), ("AI Landing Zones: design checklist", S_AILZ_CHECK[1])])
    hh = max(n1.h, n2.h, n3.h)
    for i, n in enumerate((n1, n2, n3)):
        n.place(cv, i * (nw3 + 50), yb, h=hh)
    return yb + hh + 70


def _vending(cv, y):
    r, b = section_header(
        cv, 0, y, "3  Subscription vending, onboarding and CI/CD",
        sub="How a workload team gets a landing zone, what it asks the platform for, and how infrastructure and agents are "
            "deployed afterwards (as of 2026-11-03)", size=34, w=W)
    y0 = b + 34
    bh = 130
    LH = 57 + bh + 14
    cw_, gp_ = 640, 90
    cx = lambda i: 20 + i * (cw_ + gp_)
    with cv.panel(0, y0, title="Workload team", theme="blue", style="dotted", fill="soft", pad=16, title_size=22, w=W,
                  min_h=LH) as lw:
        pass
    with cv.panel(0, lw.bottom + 22, title="Platform team", theme="yellow", style="dotted", fill="soft", pad=16, title_size=22,
                  w=W, min_h=LH) as lp:
        pass
    by_w, by_p = lw.iy, lp.iy
    s1 = Box(cw_, "1  File the vending request", sub="Region, a spoke of /21 or larger, the private endpoint list, the FQDN egress list, "
             "the ingress profile and the central AI services you need", icon="subscription", icon_pos="left", theme="blue",
             h=bh, size=19, sub_size=14).place(cv, cx(0), by_w)
    s2 = Box(cw_, "2  Place, create and connect", sub="Assign the MG (Online or Corp) by criticality and exposure; create the "
             "subscription(s) and spoke VNet; peer to the hub; UDR 0.0.0.0/0 to the hub firewall; DNS, DDoS, baseline policies "
             "and DINE", icon="landing-zone", icon_pos="left", theme="yellow", h=bh, size=19, sub_size=14).place(cv, cx(1), by_p)
    s3 = Box(cw_, "3  Deploy the workload as code", sub="NSGs, subnets, private endpoints, the Foundry resource with network "
             "injection at creation, BYO Cosmos DB, Storage and AI Search, project, capability host after DNS resolves, "
             "Application Gateway + WAF, App Service, Key Vault, monitoring", icon="devops", icon_pos="left", theme="blue",
             h=bh, size=19, sub_size=14).place(cv, cx(2), by_w)
    s4 = Box(cw_, "4  Open the firewall for approved FQDNs", sub="Public MCP servers and grounding sources get firewall "
             "application rules; the workload mirrors them in its NSGs", icon="firewall", icon_pos="left", theme="yellow",
             h=bh, size=19, sub_size=14).place(cv, cx(3), by_p)
    s5 = Box(cw_ - 40, "5  Operate", sub="The workload owns the app and agent lifecycle; the platform owns the hub. Both keep the "
             "change-impact lists current (see part 1)", icon="monitor", icon_pos="left", theme="violet",
             h=(by_p + bh) - by_w, size=19, sub_size=14).place(cv, cx(4), by_w)
    connect(cv, s1, s2, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, s2, s3, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, s3, s4, a_side="right", b_side="left", route="elbow", sw=3)
    connect(cv, s4, s5, a_side="right", b_side="left", route="elbow", sw=3)
    yt = lp.bottom + 10
    cv.text(0, yt, "Onboarding flow synthesised from the Architecture Center subscription checklist and CAF subscription vending "
                   "(the docs don't present it as one procedure).", size=14, color="#495057")
    ly = learn_line(cv, 0, yt + 24, S_ALZ)
    learn_line(cv, 520, yt + 24, ("Subscription vending (CAF)", S_VEND[1]))
    y1 = ly + 40

    # ---- negotiation checklist + cards
    TWD = 1150
    cols = [("Design consideration", 360), ("Workload requirement for this architecture", TWD - 360)]
    rows = [
        ["Number and size of spoke VNets", "One dedicated spoke; request at least a /21 of contiguous space (core workload plus the private MCP "
         "host; more for side-by-side deployments). Drivers: Application Gateway subnet (fixed), private endpoints (single IPs), "
         "build agent subnet (fixed), Agent Service subnet within a /24 (data proxy), MCP subnet /24 delegated to "
         "Microsoft.App/environments"],
        ["VNet address prefixes", "The agent subnet needs a valid private prefix: 10.0.0.0/8, 172.16.0.0/12 or 192.168.0.0/16 (the "
         "landing-zone article lists these three only; the docs disagree on 100.64.0.0/10, see part 1)"],
        ["Deployment region", "The hub must exist in the same region; regions must support availability zones; Azure OpenAI in Foundry "
         "Models has limited regional availability"],
        ["Data sovereignty", "Make sure the platform isn't duplicating diagnostics or sending Purview data to a disallowed region"],
        ["Traffic type, volume and pattern", "Users' consumption, transport protocol, peak and off-peak, chatty versus background"],
        ["Firewall configuration", "Outbound from the spoke: agent and private MCP traffic; build agents and jump boxes need OS patching; "
         "agents may call internet grounding sources, public MCP servers, tools and other agents"],
        ["Ingress from specialised roles", "Data scientists and developers reach the Foundry portal from corporate workstations; operators "
         "reach compute through the workload jump box"],
        ["Public internet access", "Tell the platform the ingress profile (public IP on Application Gateway, FQDNs for the TLS "
         "certificate): it drives MG placement, DDoS Protection and certificate procurement"],
        ["Private endpoint usage", "List AI Search, Cosmos DB, Key Vault, Foundry and the Storage accounts; agree who manages the private DNS "
         "zone records, DNS Private Resolver ruleset links and VNet DNS settings"],
        ["Centralized AI resources", "Say which AI and ML resources you use (Foundry, Agent Service, Foundry Models) and which central AI "
         "services you must use"],
    ]
    tv = Table(cols, rows, theme="blue", size=14, head_size=15,
               title="Negotiation checklist: what the workload tells the platform", title_size=22).place(cv, 0, y1)
    learn_line(cv, 0, tv.bottom + 8, S_ALZ)
    XR = TWD + 50
    CW = W - XR
    cv_ = Card(CW, "Subscription vending, platform side", [
        "Follow the CAF subscription vending process",
        "The platform assigns the management group by business criticality and technical needs; an internet-exposed workload goes "
        "to the appropriate MG",
        "It creates the subscription(s) and the spoke VNet, peers it to the hub, sets the UDR to the hub firewall and the DNS "
        "settings, and adds DDoS Protection, baseline policies and DINE",
        "Ask for the data scientists' private portal access and the cross-premises DNS in the same request",
    ], theme="yellow", icon="subscription", src=[("Subscription vending (CAF)", S_VEND[1]), S_ALZ])
    cp_ = Card(CW, "Pipelines and agents as code", [
        "Deploy agents as code; CI/CD runs from network-connected build agents (snet-buildAgents)",
        "Pin the agent version and the model version (disable auto-upgrade); agent versions are immutable",
        "Hosted agents roll back by re-pointing the endpoint's version selector. There is no native blue-green or canary: add a "
        "routing layer such as an API gateway",
        "Create projects through IaC only: projects created in the portal don't inherit the private endpoints or NSGs",
    ], theme="green", icon="devops", src=[("Baseline Foundry chat (Architecture Center)", S_BASE[1])])
    ce_ = Card(CW, "Environments, identities and Terraform state", [
        "A Foundry resource with its own dependencies per environment. AI Landing Zones keeps DEV, TEST and PROD in separate azd "
        "environments and resource groups (separate subscriptions strengthen the admin and quota boundary)",
        "Each environment gets its own App Configuration, Key Vault, data stores, network, DNS and private endpoints; keep the "
        "deployment, project and runtime identities distinct",
        "Terraform: keep the remote state outside the workload; native azd disables state locking, so allow a single authorized "
        "writer",
    ], theme="blue", icon="deployment-environments", src=[S_AILZ_PLAN, ("AI Landing Zones: deployment settings", S_AILZ_CFG[1])])
    cy_ = y1
    for c in (cv_, cp_, ce_):
        c.place(cv, XR, cy_)
        cy_ = c.bottom + 22
    return max(tv.bottom + 34, cy_) + 50

def _ailz(cv, y):
    title = "4  AI Landing Zones: Azure/AI-Landing-Zones"
    r, b = section_header(
        cv, 0, y, title,
        sub="An application landing zone for AI apps and agents that you deploy with or without a platform landing zone. The "
            "project labels itself preview (as of 2026-11-03)", size=34, w=W)
    draw_badge(cv, text_size(title, 34)[0] + 24, y + 12, "preview", size=18)
    y0 = b + 30
    a1 = Card(1100, "AI Landing Zones", [
        "An application (workload) landing zone for AI apps and agents; deploys with or without a platform landing zone",
        "Currently in preview, and it may use preview services to offer the latest features",
        "Bicep and Terraform on Azure Verified Modules (AVM), or a Deploy-to-Azure portal path",
        "Foundry AVM modules: Terraform Azure/avm-ptn-aiml-ai-foundry/azurerm; Bicep avm/ptn/ai-ml/ai-foundry",
        "Aligned with the CAF AI scenario and the Well-Architected AI workload guidance",
        "Use cases: chat using Foundry, agents, document generation, conversational agent, build-your-own copilot, content "
        "processing, conversation knowledge mining, modernize code",
    ], theme="teal", icon="github", badge="preview", src=[S_AILZ, S_AILZ_DOCS, S_AILZ_FAQ])
    a2 = Card(1250, "Agent Landing Zone (Azure/agent-landing-zone)", [
        "Infrastructure for agents plus a reference Agent Application: native Microsoft Agent Framework agents and workflows, web "
        "chat, Foundry IQ retrieval",
        "Hosted execution, or durable Container Apps execution with Durable Task Scheduler (host: hosted or container_apps); "
        "APPLICATION_MODE conversational, workflow or both",
        "Optional: AI Gateway integration, Application Gateway for protected public web ingress, the Agent App MCP server "
        "(MCP_TOOLSETS nl2sql)",
        "Planning: Bicep by default, or Terraform; standalone or hub-integrated; three resource-group destinations (Foundry and "
        "grounding, application, workload networking) that map to one to three resource groups",
        "! NETWORK_ISOLATION defaults to false: set it to true for private networking in production",
    ], theme="green", icon="agent", src=[S_AILZ_AGENT, S_AILZ_PLAN])
    a3 = Card(1150, "AI Gateway Landing Zone (Citadel Governance Hub)", [
        "Deploy it as a dedicated spoke VNet peered to the hub (recommended for large enterprises with strict segmentation: agentic "
        "workloads in other spokes route to the hub firewall, then to the gateway network), or inside the enterprise hub VNet "
        "(direct communication with the spokes)",
        "Delivered by the Citadel Governance Hub solution accelerator: Azure API Management as the unified AI gateway, usage "
        "ingestion with Logic Apps, Event Hub and Cosmos DB, IaC in Bicep and Terraform, validation notebooks and an operational "
        "guide",
        "Built from Azure-Samples/ai-hub-gateway-solution-accelerator and Azure/terraform-ai-gateway-landing-zone",
        "Contract-driven governance: backend contracts onboard LLM backends and models, access contracts onboard use cases and "
        "agents; publish contracts are labelled Preview on the page",
        "A separate landing zone: the Agent Landing Zone doesn't provision it",
    ], theme="grape", icon="apim", src=[S_AILZ_GW])
    r_, b_ = row(cv, 0, y0, [a1, a2, a3], gap=50)
    y = b_ + 46

    # ---- three deployment shapes
    cv.text(0, y, "Agent Landing Zone: three deployment shapes", size=24, color=get_theme("teal").deep)
    y += 40
    PWD = (W - 2 * 60) / 3
    IND = get_theme("indigo")

    def shape_panel(x, title, sub):
        return cv.panel(x, y, title=title, sub=sub, theme="indigo", style="dotted", pad=16, title_size=22, sub_size=14, w=PWD,
                        min_h=250)

    with shape_panel(0, "1  Standalone", "its own VNet and networking services, no hub") as p1:
        with cv.panel(p1.ix, p1.iy, title="Agent Landing Zone VNet", theme="blue", style="dashed", fill="soft", pad=12,
                      title_size=17, w=PWD - 32) as v1:
            sw3 = (PWD - 32 - 24 - 16) / 3
            for i, (lab, th) in enumerate((("agent-subnet", "green"), ("aca-environment-subnet", "green"), ("pe-subnet", "indigo"))):
                Box(sw3, lab, theme=th, h=56, size=14, sub=None).place(cv, v1.ix + i * (sw3 + 8), v1.iy)
            for i, (lab, th) in enumerate((("Azure Bastion", "gray"), ("Azure Firewall (Basic)", "gray"), ("Jump box", "gray"))):
                Box(sw3, lab, theme=th, h=50, size=14, fill="soft").place(cv, v1.ix + i * (sw3 + 8), v1.iy + 68)
    with shape_panel(PWD + 60, "2  With a platform hub", "the hub supplies connectivity, DNS and firewall or egress") as p2:
        hubb = Box(280, "Platform hub", sub="connectivity, DNS, firewall and egress", icon="landing-zone", icon_pos="top",
                   theme="yellow", h=150, size=17, sub_size=13).place(cv, p2.ix, p2.iy + 10)
        with cv.panel(p2.ix + 280 + 130, p2.iy, title="Agent Landing Zone spoke", theme="blue", style="dashed", fill="soft", pad=12,
                      title_size=17, w=PWD - 32 - 410) as sp2:
            for i, (lab, th) in enumerate((("agent-subnet", "green"), ("aca-environment-subnet", "green"), ("pe-subnet", "indigo"))):
                Box(PWD - 32 - 410 - 24, lab, theme=th, h=40, size=14).place(cv, sp2.ix, sp2.iy + i * 48)
        arrow(cv, [(hubb.right + 6, hubb.cy), (sp2.x - 6, hubb.cy)], sw=3, color=IND.stroke, start_head="arrow", end_head="arrow",
              label="peering", label_size=13, label_pos="above")
    with shape_panel(2 * (PWD + 60), "3  With an AI gateway", "a separate AI Gateway landing zone, not auto-provisioned") as p3:
        hub3 = Box(PWD - 32, "Platform hub", sub="connectivity, DNS, firewall and egress", icon="landing-zone", icon_pos="left",
                   theme="yellow", h=64, size=17, sub_size=13).place(cv, p3.ix, p3.iy)
        bw3 = (PWD - 32 - 70) / 2
        al = Box(bw3, "Agent Landing Zone", sub="agentic workload", icon="agent", icon_pos="left", theme="green", h=84,
                 size=16, sub_size=13).place(cv, p3.ix, hub3.bottom + 70)
        gw = Box(bw3, "AI Gateway Landing Zone", sub="APIM and Foundry", icon="apim", icon_pos="left", theme="grape", h=84,
                 size=16, sub_size=13).place(cv, p3.ix + bw3 + 70, hub3.bottom + 70)
        arrow(cv, [(al.cx, hub3.bottom + 6), (al.cx, al.y - 6)], sw=3, color=IND.stroke, start_head="arrow", end_head="arrow")
        arrow(cv, [(gw.cx, hub3.bottom + 6), (gw.cx, gw.y - 6)], sw=3, color=IND.stroke, start_head="arrow", end_head="arrow")
        cv.text(p3.ix, al.bottom + 12, "Agent traffic goes to the hub firewall, then to the gateway network", size=13, color="#495057")
    y = max(p1.bottom, p2.bottom, p3.bottom) + 40

    # ---- default subnet map
    cv.text(0, y, "Default VNet 192.168.0.0/21 and its subnets", size=24, color=get_theme("teal").deep)
    y += 40
    tiles = [
        ("agent-subnet", "192.168.0.0/24", "Foundry Agent Service; delegated Microsoft.App/environments", "green"),
        ("aca-environment-subnet", "192.168.1.0/24", "Container Apps environment; same delegation", "green"),
        ("pe-subnet", "192.168.2.0/26", "Foundry and grounding private endpoints", "indigo"),
        ("AzureBastionSubnet", "192.168.2.64/26", "Azure Bastion", "gray"),
        ("AzureFirewallSubnet", "192.168.2.128/26", "Azure Firewall", "gray"),
        ("GatewaySubnet", "192.168.2.192/26", "VPN or ExpressRoute reservation; opt-in; no NSG, UDR or delegation", "gray"),
        ("AppGatewaySubnet", "192.168.3.0/27", "Application Gateway", "indigo"),
        ("jumpbox-subnet", "192.168.3.64/27", "Jump box", "indigo"),
        ("devops-build-agents-subnet", "192.168.3.96/27", "Build agents", "indigo"),
        ("application-pe-subnet", "192.168.3.128/26", "Application private endpoints, separate from the Foundry and grounding ones", "indigo"),
        ("AzureFirewallManagementSubnet", "192.168.3.192/26", "Basic firewall only", "gray"),
        ("powerplatform-subnet", "192.168.4.0/24", "Delegation Microsoft.PowerPlatform/enterprisePolicies", "violet"),
        ("ai-gateway-subnet", "192.168.5.0/24", "APIM Standard v2 or Premium v2 outbound VNet integration: at least /27, delegated "
                                                 "Microsoft.Web/serverFarms, NSG, outbound HTTPS to Key Vault", "grape"),
    ]
    tw_, tg = (W - 6 * 16) / 7, 16
    th_rows = []
    for rr in range(2):
        hs = []
        for nm, cidr, purpose, th in tiles[rr * 7:(rr + 1) * 7]:
            hs.append(14 + 20 * len(wrap_text(nm, tw_ - 22, 16)) + 20 + 17 * len(wrap_text(purpose, tw_ - 22, 14)) + 10)
        th_rows.append(max(hs))
    for i, (nm, cidr, purpose, th) in enumerate(tiles):
        rr, cc = divmod(i, 7)
        tx, ty = cc * (tw_ + tg), y + (0 if rr == 0 else th_rows[0] + 14)
        t = get_theme(th)
        nl = wrap_text(nm, tw_ - 22, 16)
        pl = wrap_text(purpose, tw_ - 22, 14)
        with cv.group():
            cv.rect(tx, ty, tw_, th_rows[rr], stroke=t.stroke, fill=t.fill, style="hachure", sw=2,
                    dash="dashed" if nm == "GatewaySubnet" else "solid")
            cv.text(tx + 11, ty + 8, "\n".join(nl), size=16, color=t.deep)
            ny = 8 + 20 * len(nl)
            cv.text(tx + 11, ty + ny, cidr, size=15, color="#1e1e1e")
            cv.text(tx + 11, ty + ny + 20, "\n".join(pl), size=14, color="#343a40")
        cv.register(f"subnet:{nm}", tx, ty, tw_, th_rows[rr])
    y += th_rows[0] + 14 + th_rows[1]
    cv.text(0, y + 8, _wrap("An address plan, not a resource inventory: prepared subnets aren't deployed services, and shared-hub services "
                            "don't need these reservations in the spoke. Delegations: agent and Container Apps subnets "
                            "Microsoft.App/environments, Power Platform Microsoft.PowerPlatform/enterprisePolicies, AI Gateway "
                            "Microsoft.Web/serverFarms, all others none. With network isolation off, no VNet or subnets are "
                            "provisioned.", W - 20, 14), size=14, color="#495057")
    learn_line(cv, 0, y + 56, S_AILZ_CFG)
    y += 90

    # ---- configuration (left) and design checklist (right)
    LCW = 1500
    cv.text(0, y, "Configuration: hub integration and private DNS", size=24, color=get_theme("teal").deep)
    d2 = Card(LCW, "Hub integration and private DNS inputs", [
        "HUB_INTEGRATION_HUB_VNET_RESOURCE_ID and ..._CREATE_HUB_PEERING (default true: the hub owner supplies the reverse "
        "peering); gateway transit and remote gateway flags",
        "..._EGRESS_NEXT_HOP_IP (hub firewall private IP as the default route) or ..._EXISTING_ROUTE_TABLE_RESOURCE_ID: mutually "
        "exclusive. DEPLOYMENT_MODE is only a label: it doesn't attach the hub",
        "POLICY_MANAGED_PRIVATE_DNS, or explicit EXISTING_PRIVATE_DNS_ZONE_<ZONE>_RESOURCE_ID (COGSVCS, OPENAI, AISERVICES, SEARCH, "
        "COSMOS, BLOB, KEYVAULT and others): mutually exclusive",
        "Foundry backing resources (aiSearchResourceId, aiFoundryStorageAccountResourceId, aiFoundryCosmosDBAccountResourceId) are a "
        "dedicated set, not arbitrary shared application stores",
        "Standalone private deployments default to the Basic firewall (Standard when DNS proxy is needed); DEV, TEST and PROD are "
        "separate azd environments",
    ], theme="indigo", icon="vnet", src=[S_AILZ_CFG, S_AILZ_NET])
    d2.place(cv, 0, y + 40)
    XC = LCW + 50
    cv.text(XC, y, "Design checklist: eight areas to decide before you deploy", size=24, color=get_theme("teal").deep)
    chk = [
        ("Compute and cost", "teal", "PTU versus pay-as-you-go, spillover through the gateway, deployment type, shutdown"),
        ("Data", "cyan", "Where agent state lives; which resources may be shared across projects (keep app storage separate from the "
                         "Agent Service backing storage); the Fabric data agent"),
        ("Governance", "grape", "Policies; NIST AI RMF; responsible-AI evaluation; content safety; which models teams may deploy "
                                "(audit first, then enforce)"),
        ("Identity", "red", "Managed identity; MFA and PIM; Entra ID versus keys; Conditional Access; least privilege; disable local "
                            "authentication"),
        ("Monitoring", "violet", "SLOs; baseline alerts; traceability; diagnostic retention; quality drift; diagnosing private "
                                 "connectivity"),
        ("Reliability", "orange", "RTO and RPO; region and model availability; quota, including the separate Agent Service backing "
                                  "resources; account, project and billing boundaries"),
        ("Security", "red", "Defender AI posture; Purview; MITRE ATLAS and OWASP; Prompt Shields"),
        ("Networking", "indigo", "DDoS Protection; Bastion; private endpoints; NSGs; WAF (Application Gateway or Front Door); AI "
                                 "gateway through APIM; firewall; DNS; outbound allow-list"),
    ]
    cw4 = (W - XC - 30) / 2
    cards = [Card(cw4, t, [("para", s)], theme=th, title_size=19, body_size=14, pad=14) for t, th, s in chk]
    r_, b_ = grid(cv, XC, y + 40, cards, 2, gap_x=30, gap_y=16)
    learn_line(cv, XC, b_ + 6, S_AILZ_CHECK)
    yR = b_ + 34

    # ---- citadel layers (left), public-path gotcha and regions (right)
    LWD = LCW
    yL = d2.bottom + 40
    cv.text(0, yL, "AI Citadel Blueprint: four layers", size=22, color=get_theme("grape").deep)
    cv.text(0, yL + 28, "One Agent Execution Plane per business unit or use case", size=14, color="#495057")
    ly = yL + 60
    layers = [
        ("L1  Governance Hub", "grape", "runtime: unified AI gateway, policy-as-code, identity validation, token rate limiting, "
                                        "content filtering, cost attribution"),
        ("L2  Agent Operations", "green", "Foundry Agents and the Foundry Control Plane"),
        ("L3  Agent Management", "violet", "Agent 365 identities, blueprints, shadow-agent detection, sponsorship, access packages"),
        ("L4  Security Foundation", "red", "Microsoft Defender, Microsoft Purview, Microsoft Entra"),
    ]
    for i, (lab, th, sub) in enumerate(layers):
        Box(LWD, lab, sub=sub, theme=th, h=70, size=18, sub_size=14).place(cv, 0, ly + i * 78)
    yl_end = learn_line(cv, 0, ly + 4 * 78 + 2, S_AILZ_GW)
    XR = XC
    RW = W - XR
    gn = Note(RW, "Teams and M365 Copilot publication uses a manually enabled, source-IP-filtered public Activity endpoint: not private "
                  "end to end, so don't use it if public agent ingress is prohibited. Copilot Studio uses a delegated Power "
                  "Platform private-network path (no Activity exception). Search to source and model private ingestion needs Search "
                  "shared private links and owner approval. Peering alone doesn't propagate DNS: hub integration needs agreement on "
                  "reverse peering, routes, DNS and gateway transit.", kind="warn",
              title="A private foundation doesn't make every integration private", size=15, src=[S_AILZ_NET]).place(cv, XR, yR)
    regions = ["australiaeast", "eastus", "francecentral", "germanywestcentral", "japaneast", "koreacentral", "norwayeast",
               "polandcentral", "southafricanorth", "southeastasia", "spaincentral", "swedencentral", "switzerlandnorth",
               "uaenorth", "uksouth"]
    cf = ChipFlow(regions, RW - 32, theme="teal", size=14, gap=8)
    with cv.panel(XR, gn.bottom + 24, title="Regions with full deployment (15, as of 2026-11-03)", theme="teal", style="solid",
                  fill="hatch", pad=16, title_size=19, w=RW) as rp:
        pt = cv.text(rp.ix, rp.iy, _wrap("Needs co-availability of AI Services, AI Search, Container Apps, Cosmos DB, ACR, App "
                                         "Configuration, Key Vault and zonal compute; partial deployments are unsupported",
                                         RW - 40, 15), size=15, color="#1e1e1e")
        cf.place(cv, rp.ix, pt.bottom + 12)
        cv.text(rp.ix, rp.iy + (pt.bottom - rp.iy) + 12 + cf.h + 8, "Learn: AI Landing Zones documentation", size=12, color=LINK,
                link=S_AILZ_DOCS[1])
    return max(yl_end, rp.bottom) + 56


def _pillars(cv, y):
    r, b = section_header(cv, 0, y, "5  Well-Architected notes for Foundry in a landing zone",
                          sub="What changes for each pillar when the hub, DNS, firewall and policy are shared (as of 2026-11-03)",
                          size=34, w=W)
    y0 = b + 30
    pw, gp = 688, 40
    SRC_WAF = [("AI workloads on Azure (Well-Architected)", learn("well-architected/ai/get-started", base="azure"))]
    p_rel = Card(pw, "Reliability", [
        "The landing zone adds no new reliability considerations for the core workload components; it adds dependencies",
        "The platform should support multi-region workload landing zones; check which regions offer the approved AI services, models "
        "and capacity",
        "Failover must include model deployments and retrieval data; keep retrieval data near the AI services and inside residency "
        "limits",
        "Foundry has no automatic cross-region failover: separate Foundry resources per region, sync and routing in the app layer",
        "Failure mode analysis: treat egress firewall, DNS resolution, DINE policies and management-group policies as dependencies, "
        "with incident contacts and escalation paths for each",
    ], theme="orange", icon="service-health", src=[S_CAF_AI, S_ALZ])
    p_sec = Card(pw, "Security", [
        "Don't rely on the hub's non-transitive routing alone: keep NSGs on the subnets",
        "Egress: allow only the required outbound connectivity in NSGs and deny the rest; stop unwanted egress as close to the "
        "source as possible",
        "Policy example: Application Gateway WAF in deny mode. DDoS Protection: the platform team might use IP protection plans "
        "or enforce VNet protection plans with Azure Policy",
        "The workload typically procures the TLS certificate, aligned with the platform; customer-managed keys are optional: "
        "landing zones don't mandate an encryption method",
        "Same Defender plans as the baseline if vending doesn't enable them. Purview: enable Microsoft Purview Data Security in the "
        "Foundry Control Plane",
    ], theme="red", icon="defender", src=SRC_ALZ)
    p_cost = Card(pw, "Cost optimization", [
        "Firewall and DDoS Protection move to the platform, even through chargeback: more cost-effective than self-managing them",
        "The workload's pricing estimate excludes the shared Firewall, Bastion, DDoS Protection and hub networking",
        "Don't consolidate the Agent Service dependencies as platform resources to save money",
        "Cost pressure alone isn't a reason to colocate production workloads",
        "A subscription is the boundary for quota, cost, governance and security",
    ], theme="yellow", icon="cost-management", src=[S_ALZ, S_CAF_SHARE_L])
    p_ops = Card(pw, "Operational excellence", [
        "The workload keeps its own Log Analytics workspace and Application Insights; the platform may add central copies and baseline "
        "alerts",
        "Write a triage runbook to correlate workload and platform logs; the platform grants read access and enables firewall logs "
        "(network rules, application rules, DNS proxy)",
        "Build agents are deployed and run by the workload, with platform-approved images, patching and authentication",
        "Infrastructure as code and CI/CD; agents as code with pinned versions",
        "Track the change-impact lists in both directions",
    ], theme="violet", icon="monitor", src=SRC_ALZ)
    p_perf = Card(pw, "Performance efficiency", [
        "The workload team keeps control of the resources in the application flows: scale the chat UI host, models and other "
        "components to workload and cost constraints",
        "Egress and cross-premises latency",
        "SKU limitations from cost-containment governance",
        "The baseline performance guidance still applies; design AI workloads with the Well-Architected AI workloads guidance",
    ], theme="blue", icon="metrics", src=SRC_ALZ + SRC_WAF)
    r_, b_ = row(cv, 0, y0, [p_rel, p_sec, p_cost, p_ops, p_perf], gap=gp)
    return b_ + 56


def _sources(cv, y):
    items = [
        ("Baseline Foundry chat in an Azure landing zone (Architecture Center)", S_ALZ[1]),
        ("Baseline Microsoft Foundry chat reference architecture", S_BASE[1]),
        ("Foundry rollout across my organization", S_PLAN[1]),
        ("Microsoft Foundry architecture", S_ARCH[1]),
        ("AI platform sharing, isolation and colocation (CAF)", S_CAF_SHARE[1]),
        ("Architecture and governance for AI (CAF)", S_CAF_AI[1]),
        ("What is an Azure landing zone? (CAF)", S_CAF_LZ[1]),
        ("Plan for AI adoption (CAF)", S_CAF_PLAN[1]),
        ("Subscription vending (CAF)", S_VEND[1]),
        ("Built-in policies for model deployment", S_MODEL_POL[1]),
        ("Custom policy definitions for Foundry", S_CUSTOM_POL[1]),
        ("Azure Policy built-ins for Foundry Tools", S_POL_REF[1]),
        ("Configure private link for Foundry", S_PRIVLINK[1]),
        ("AI Landing Zones (GitHub: Azure/AI-Landing-Zones)", S_AILZ[1]),
        ("AI Landing Zones documentation", S_AILZ_DOCS[1]),
        ("AI Landing Zones: Agent Landing Zone", S_AILZ_AGENT[1]),
        ("AI Landing Zones: planning", S_AILZ_PLAN[1]),
        ("AI Landing Zones: network design", S_AILZ_NET[1]),
        ("AI Landing Zones: deployment settings", S_AILZ_CFG[1]),
        ("AI Landing Zones: AI Gateway Landing Zone", S_AILZ_GW[1]),
        ("AI Landing Zones: FAQ", S_AILZ_FAQ[1]),
        ("AI Landing Zones: design checklist", S_AILZ_CHECK[1]),
        ("AI workloads on Azure (Well-Architected)", learn("well-architected/ai/get-started", base="azure")),
    ]
    s = sources(cv, 0, y, items, w=W, cols=4, title="Sources and further reading (links are clickable)")
    return s.bottom + 20


# (new sections are wired into build() below)


def build(cv: Canvas) -> None:
    only = os.environ.get("LZ2_SECTIONS")  # dev aid: e.g. "models"
    steps = [("models", _models), ("sharing", _sharing), ("policy", _policy), ("vending", _vending), ("ailz", _ailz),
             ("pillars", _pillars), ("sources", _sources)]
    y = _head(cv)
    for name, fn in steps:
        if only and name not in only.split(","):
            continue
        y = fn(cv, y)
