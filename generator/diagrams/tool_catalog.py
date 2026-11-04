"""Tool catalog - every tool an agent can use: where it runs, auth, status, toolbox eligibility, network, limits, billing."""
from generator.xd import *
from generator.xd import theme as get_theme
from generator.xd.blocks import draw_mark

META = dict(
    id="tool-catalog", title="Tool catalog", section="2", group="Tools and MCP", order=31,
    description="Every tool an agent can use: one comparison matrix of where it runs, auth, GA or preview, toolbox eligibility, "
                "network isolation, region/model limits and billing - plus a dispatch diagram and a decision tree.",
    tags=["tools", "toolbox", "mcp", "catalog", "matrix", "agents"],
)

W = 3300
AS_OF = "as of 2026-11-03"
T_ = "agents/how-to/tools/"

# family code -> (title, theme, icon)
FAMS = [
    ("A", "Code and compute", "lime", "code"),
    ("B", "Knowledge and retrieval", "teal", "ai-search"),
    ("C", "Web and browser", "cyan", "globe"),
    ("D", "Integration", "orange", "mcp"),
    ("E", "Enterprise data", "indigo", "m365"),
    ("F", "Foundry Tools", "blue", "ai-services"),
    ("G", "Memory, skills and meta", "grape", "toolbox"),
]
FAM = {c: (t, th, ic) for c, t, th, ic in FAMS}

# status -> (matrix label, theme, chip dash, chip suffix)
ST = {
    "ga": ("GA", "green", "solid", ""),
    "ga_sub": ("GA (some sub-features preview)", "green", "solid", ""),
    "preview": ("Preview", "orange", "dashed", " (preview)"),
    "mixed": ("GA + preview parts", "yellow", "dotted", " (GA + preview)"),
    "retire": ("Preview; deprecated 2026-11-06", "red", "dashed", " (deprecated 2026-11-06)"),
    "notag": ("No preview tag", "gray", "solid", ""),
}
# where -> (matrix label, theme)
WH = {
    "svc": ("Service-side", "green"),
    "svc_local": ("Service-side (or local mode)", "green"),
    "out": ("Calls out", "ink"),
    "cli": ("Client-side", "red"),
}


def T(id, fam, name, typ, st, wh, tb, net, what, auth, limits, bill, url, chip=None):
    return dict(id=id, fam=fam, name=name, typ=typ, st=st, wh=wh, tb=tb, net=net, what=what, auth=auth,
                limits=limits, bill=bill, url=url, chip=chip or name)


TOOLS = [
    # ------------------------------------------------------------------ A  code and compute
    T("function", "A", "Function calling", "function", "ga", "cli", CROSS, CHECK,
      "Model emits a function_call item; your app runs it and returns function_call_output in the same conversation",
      "Foundry User only; your code owns auth. Definitions are SDK or REST only (the portal can't add or edit them)",
      "Runs expire 10 minutes after creation. Region table: No in Brazil South, North Central US, South Central US, West US",
      "Model tokens only (no separate meter stated)", learn(T_ + "function-calling")),
    T("code_interpreter", "A", "Code interpreter", "code_interpreter", "ga", "svc", CHECK, CHECK,
      "Model writes and runs Python in a Microsoft-managed sandbox (Azure Container Apps dynamic sessions, Hyper-V isolation); returns files and charts",
      "Basic or Standard agent setup; upload files with purpose=assistants",
      "No outbound network; session up to 1 h, idle timeout 30 min; one session per concurrent conversation; 27 supported file-type rows; region table: Yes in all 29 listed regions",
      "Additional charges beyond tokens, per session", learn(T_ + "code-interpreter")),
    T("custom_ci", "A", "Custom code interpreter", "MCP + ACA session pool", "preview", "out", PARTIAL, DASH,
      "Your own Azure Container Apps Dynamic Sessions pool exposes an MCP server: custom packages, images and compute",
      "Standard setup only; Foundry User; provisioning needs Foundry Owner + Container Apps ManagedEnvironment Contributor (PIM) and the Microsoft.App/SessionPoolsSupportMCP feature",
      "Region must support Agent Service and ACA Dynamic Sessions; pool deploy takes up to 1 h; use mcpServerEndpoint as server_url (not poolManagementEndpoint); no direct file I/O - use data or SAS URLs. Toolbox: as a generic MCP tool",
      "Your Azure Container Apps session-pool compute", learn(T_ + "custom-code-interpreter")),
    T("shell", "A", "Shell tool and skills", "shell", "preview", "svc_local", PARTIAL, DASH,
      "Runs commands in a hosted Linux container (container_auto) or in local mode (you run shell_calls) via the Responses API; skills are SKILL.md bundles",
      "Responses-API model deployment that supports shell; Foundry User; Entra or key",
      "Hosted: Debian 12, Python 3.11 (+ Node, Java, PHP, Ruby, Go), no outbound network, no sudo; idle 20 min, deleted 1 h after creation. Toolbox: the shell type appears only in the skills-shell sample. Skills with shell: preview",
      "Shell tool requests and model calls can incur charges", learn(T_ + "skills-shell-tool"), chip="Shell tool + skills"),
    T("image", "A", "Image generation", "image_generation", "preview", "svc", CROSS, CROSS,
      "An orchestrator LLM calls gpt-image-1 and returns a base64 image (image_generation_call.result)",
      "Approval to use gpt-image-1; two deployments in the same project (orchestrator + gpt-image-1)",
      "Orchestrator: gpt-5 only; request must carry header x-ms-oai-image-generation-deployment; no editing, masks or partial streaming (use the Azure OpenAI Image API); Java can't set the header - use REST",
      "Model usage", learn(T_ + "image-generation")),
    # ------------------------------------------------------------------ B  knowledge and retrieval
    T("file_search", "B", "File search + vector stores", "file_search", "ga", "svc", CHECK, CHECK,
      "Service parses, chunks, embeds and indexes uploaded files; hybrid keyword + semantic search with query rewrite, parallel sub-queries and rerank",
      "Foundry User; Storage Blob Data Contributor on project storage. Basic = Microsoft-managed storage and search; Standard = your Blob and your AI Search",
      "Chunk 800 / overlap 400 tokens; 10,000 files per store, 512 MB per file; 1 store per agent + 1 per conversation (conversation stores expire 7 days after last active); not available in Italy North and Brazil South",
      "Additional charges beyond tokens", learn(T_ + "file-search"), chip="File search + vector stores"),
    T("ai_search", "B", "Azure AI Search", "azure_ai_search", "ga", "svc", CHECK, CHECK,
      "Queries one existing search index with inline citations",
      "Project connection to your search service: key, or keyless with the Foundry account system-assigned MI (Search Index Data Contributor + Search Service Contributor); same tenant",
      "One index per tool; top_k default 5; query_type default vector_semantic_hybrid; private AI Search needs Standard setup + VNet injection + Entra project MI (no keys)",
      "Azure AI Search service charges", learn(T_ + "ai-search")),
    T("foundry_iq", "B", "Foundry IQ knowledge base", "MCP: knowledge_base_retrieve", "mixed", "out", PARTIAL, CHECK,
      "Managed multi-source knowledge base on Azure AI Search agentic retrieval: LLM query planning, parallel search, semantic rerank, citations; ACL and Purview aware",
      "RemoteTool connection with ProjectManagedIdentity; project MI = Search Index Data Reader; search MI = Cognitive Services User if the KB uses an LLM; hub-based projects not supported",
      "Exposes one tool: knowledge_base_retrieve; reasoning effort minimal / low / medium; sources: Blob, SharePoint, OneLake, web; Python SDK >= 2.0.0 or REST 2026-08-01-preview. Toolbox: rides the MCP + connection path",
      "AI Search + LLM tokens (free tier and free token allocation for PoC)", learn("agents/concepts/what-is-foundry-iq")),
    # ------------------------------------------------------------------ C  web and browser
    T("web_search", "C", "Web search", "web_search", "ga", "svc", CHECK, PARTIAL,
      "Grounding with Bing through a Microsoft-managed resource; inline URL citations; runs server-side in the Responses API; also deep research with o3-deep-research. Recommended default for web",
      "No extra Azure resource or role beyond Foundry access; domain-restricted needs a Bing Custom Search resource + instance + remote-tool connection (Foundry Project Manager)",
      "search_context_size low / medium (default) / high; custom_search_configuration for allow or block domains; live internet access isn't supported (external_web_access always false); public endpoint even in network-secured projects",
      "Costs beyond tokens (Bing pricing)", learn(T_ + "web-search")),
    T("bing_grounding", "C", "Grounding with Bing Search", "bing_grounding", "ga", "svc", CROSS, PARTIAL,
      "Explicit Bing tool using your own Grounding with Bing Search resource and a project connection",
      "Microsoft.Bing provider registered; Contributor (PIM) on the resource group; Foundry Project Manager for the connection",
      "count default 5 (max 50), freshness, market, set_lang; works with Azure OpenAI and non-OpenAI Foundry Models; defeats prompt caching (timestamp injected each request); public endpoint",
      "Bing pricing", learn(T_ + "bing-tools")),
    T("bing_custom", "C", "Grounding with Bing Custom Search", "bing_custom_search_preview", "preview", "svc", PARTIAL, DASH,
      "Restricts grounding to the domains, paths or pages in a Bing Custom Search instance",
      "As Bing grounding + a Bing Custom Search instance (Contributor on that resource just-in-time)",
      "Public Bing-indexed pages only; granularity domain, domain + path or webpage; block-list mode possible. Toolbox: via web_search + custom_search_configuration",
      "Bing pricing", learn(T_ + "bing-tools"), chip="Bing Custom Search"),
    T("browser", "C", "Browser automation", "browser_automation", "ga", "out", CHECK, CROSS,
      "Managed remote browser through the Playwright Workspaces remote MCP server: navigate, inspect, fill forms; Live View, screenshots, Take control",
      "Playwright workspace + project connection: API key, project MI (recommended) or agent identity; Foundry User + Foundry Project Manager; Playwright Workspace Contributor for the project MI",
      "Learn lists 7 regions (australiaeast, eastasia, eastus, japaneast, switzerlandnorth, westeurope, westus3); region table: No in Japan West, Switzerland West, West Central US; azure-ai-projects >= 2.8.0; client timeout >= 5 min",
      "Playwright workspace pricing", learn(T_ + "browser-automation")),
    T("computer_use", "C", "Computer use", "computer_use_preview", "preview", "cli", CROSS, CROSS,
      "Model proposes UI actions from screenshots (click, type, scroll); your app executes them and returns a new screenshot (loop)",
      "Application form for access to computer-use-preview (limited access); sandboxed VM; Foundry User",
      "Model computer-use-preview only; the page lists eastus2, swedencentral, southindia while the region table shows Yes in 9 regions; pending_safety_checks must be acknowledged",
      "Model usage", learn(T_ + "computer-use")),
    # ------------------------------------------------------------------ D  integration
    T("mcp", "D", "MCP (remote server)", "mcp", "ga_sub", "out", CHECK, CHECK,
      "Calls tools on a remote MCP server: public catalog, managed connectors, private catalog or your own",
      "Set on the connection: none, custom keys, project MI, agent identity, OAuth2, user Entra token or AgentOnBehalfOfUser",
      "100 s non-streaming timeout; remote servers only; private MCP needs Standard setup + an ACA subnet; allowed_tools [] = all tools; default require_approval = always",
      "Not stated; non-Foundry tools might incur costs", learn(T_ + "model-context-protocol"), chip="MCP (remote server)"),
    T("managed_mcp", "D", "Managed MCP connectors", "Connector Namespace", "preview", "svc", CHECK, DASH,
      "More than 1,000 connectors surfaced as a Foundry-hosted MCP server",
      "OAuth2 only (portal experience)",
      "14 regions; connector actions only (no triggers); scoped to the project",
      "Not stated", learn(T_ + "connectors")),
    T("openapi", "D", "OpenAPI", "openapi", "ga", "out", CHECK, CHECK,
      "Calls your REST API from an OpenAPI 3.0 or 3.1 spec embedded inline",
      "Anonymous, API key or project managed identity - always through a project connection (auth.type: project_connection)",
      "operationId mandatory (letters, -, _); JSON and JSON-patch bodies; one API-key scheme per tool; in a toolbox: project MI only; the connection needs securitySchemes + security or the key isn't injected",
      "Not stated", learn(T_ + "openapi")),
    T("azure_functions", "D", "Azure Functions", "azure_function", "ga", "out", CROSS, CHECK,
      "Agent drops a message on a Storage input queue; a queue-triggered function replies on an output queue (async, scale to zero)",
      "Standard setup only; Storage Queue Data Contributor for BOTH the project MI and the function-app MI",
      "Models: gpt-5.1 and gpt-5.2 only; the reply must echo CorrelationId; Flex Consumption recommended; alternatives: Functions as an MCP server (sync) or an HTTP function + OpenAPI",
      "Not stated; runs in your subscription", learn(T_ + "azure-functions")),
    T("a2a", "D", "Agent2Agent (A2A)", "a2a / a2a_preview", "mixed", "out", CHECK, CHECK,
      "Calls a remote A2A endpoint, including another Foundry agent. a2a = GA (v1.0); a2a_preview = preview (v0.3)",
      "Key-based, agent identity, project MI, UserEntraToken, AgentOnBehalfOfUser (preview), OAuth2 or none; target Foundry agent needs incoming A2A + the Foundry Agent Consumer role",
      "Foundry targets: text only, no streaming; tasks and context kept 60 days; the classic Connected Agents tool isn't available (use A2A or Workflows); incoming A2A (expose your agent) is preview",
      "Not stated", learn(T_ + "agent-to-agent")),
    # ------------------------------------------------------------------ E  enterprise data
    T("sharepoint", "E", "SharePoint", "sharepoint_grounding_preview", "preview", "svc", CROSS, PARTIAL,
      "Retrieves permission-trimmed text from a site or folder through the Microsoft Copilot Retrieval API",
      "User identity (OBO) only - app-only identity fails; same tenant; READ on the site; M365 Copilot license or pay-as-you-go; Foundry User",
      "One SharePoint tool per agent; <= 25 results; 200 requests per user per hour; query <= 1,500 chars; text only; doesn't work when published to Teams",
      "M365 Copilot license or pay-as-you-go", learn(T_ + "sharepoint")),
    T("fabric_iq", "E", "Fabric IQ", "fabric_iq_preview", "preview", "out", CHECK, PARTIAL,
      "Delegates natural-language tasks to Fabric IQ: ontology, Power BI semantic model or Fabric data agent through MCP endpoints",
      "Foundry connection per item; reuse the incoming Entra user context or managed / custom OAuth; Fabric license; F2+ or P1+ capacity",
      "Only the data-agent endpoint supports background mode; VNet partial (semantic models: public access only); not in Power-BI-only regions; gpt-5.4+ recommended for semantic-model queries",
      "Fabric capacity + license", learn(T_ + "fabric-iq")),
    T("fabric_dataagent", "E", "Fabric data agent (legacy)", "fabric_dataagent_preview", "retire", "svc", CROSS, CROSS,
      "Legacy tool: NL2SQL over a published Fabric data agent, with OBO",
      "User identity only (no service principal); F2+ or P1+ capacity; same tenant and same-region capacities; workspace_id + artifact_id GUIDs",
      "Scheduled for deprecation on November 6, 2026: replace type fabric_dataagent_preview with fabric_iq_preview (portal: Tools > Add > Browse all tools > Fabric IQ)",
      "Fabric capacity", learn(T_ + "fabric")),
    T("work_iq", "E", "Work IQ", "work_iq_preview", "preview", "out", CHECK, CROSS,
      "Delegates Microsoft 365 tasks (mail, meetings, files, chats) to Work IQ as a peer agent over A2A; also MCP options: Copilot Chat, Teams, Word, Outlook, SharePoint, OneDrive",
      "Delegated user only (no app-only); one-time Global Admin consent of WorkIQAgent.Ask + a custom OAuth app; Foundry Project Manager for the connection",
      "A2A v1.0 (send A2A-Version: 1.0) and v0.3; docs disagree on network isolation (toolbox page: not supported; Work IQ page: public HTTPS endpoint); connection fields can't be edited after creation",
      "Usage-based (Copilot Credits); connector-backed tools may need an M365 Copilot license per user", learn(T_ + "work-iq")),
    # ------------------------------------------------------------------ F  Foundry Tools
    T("speech_mcp", "F", "Azure Speech MCP Server", "Catalog MCP server", "ga", "out", DASH, CROSS,
      "Speech-to-text and text-to-speech through a remote MCP server from the Catalog",
      "Custom keys: Bearer = Foundry resource KEY1 or KEY2; header X-Blob-Container-Url = container SAS (read + write)",
      "Page says MCP tools need the Agent Service Enterprise tier; model must support tool calling (gpt-4o or later); not supported in network-secured Foundry; Foundry resource in a Speech-supported region",
      "Not stated", learn(T_ + "azure-ai-speech")),
    T("language_mcp", "F", "Azure Language MCP server", "language/mcp", "preview", "out", CHECK, PARTIAL,
      "NER, health text analytics, CLU, CQA, language detection, sentiment, summarization, key phrases and PII redaction over MCP",
      "Custom keys: Ocp-Apim-Subscription-Key = resource key (or the project MI in the toolbox quickstart sample)",
      "Endpoint {foundry-resource}.cognitiveservices.azure.com/language/mcp?api-version=2025-11-15-preview; network-secured projects can require a publicly accessible MCP server",
      "Not stated", learn("azure/ai-services/language-service/concepts/foundry-tools-agents", base=""), chip="Azure Language MCP server"),
    T("language_agents", "F", "Language prebuilt agents", "intent routing + Exact QA", "preview", "svc", DASH, DASH,
      "Intent routing agent = CLU + CQA (+ optional RAG fallback); Exact Question Answering agent = CQA (no-code, verbatim answers)",
      "Custom keys connection (Ocp-Apim-Subscription-Key); Foundry resource + Language resource; Contributor or Owner on the resource group",
      "Create the CLU and CQA projects first; no azure.yaml template provided",
      "Not stated", learn("azure/ai-services/language-service/concepts/foundry-tools-agents", base="")),
    T("cu_tool", "F", "Content Understanding tool", "Foundry portal", "mixed", "svc", DASH, DASH,
      "Foundry portal tool for agentic workflows over documents, images, audio and video using analyzers (prebuilt + custom)",
      "Foundry resource; bring your own deployments of supported generative + embedding models",
      "API 2025-11-01 is GA; 2026-06-01-preview adds agentic mode; inherits Foundry guardrails (annotate-only by approval)",
      "Not stated", learn("azure/ai-services/content-understanding/overview", base="")),
    T("translator", "F", "Azure Translator (via OpenAPI)", "openapi", "ga", "out", PARTIAL, DASH,
      "No built-in agent tool documented; call the REST API through the OpenAPI tool",
      "OpenAPI connection ProjectManagedIdentity, audience https://cognitiveservices.azure.com; grant the project MI a Translator role",
      "Text translation REST GA version 2026-06-06; Translate: 1,000 array elements x 50,000 chars (LLM translation: 50 x 5,000)",
      "NMT by source characters; LLM by input and output tokens", learn("azure/ai-services/translator/text-translation/overview", base=""), chip="Azure Translator (via OpenAPI)"),
    # ------------------------------------------------------------------ G  memory, skills and meta
    T("memory", "G", "Memory", "memory_search_preview", "preview", "svc", DASH, CROSS,
      "Managed long-term memory: extraction, LLM consolidation, retrieval; user profile, chat summary and procedural memories",
      "Compatible Azure OpenAI chat + embedding deployments; explicit scope (auto-scope only with {{$userId}} + header x-memory-user-id)",
      "100 scopes per store; 10,000 memories per scope; search and update 1,000 req/min each; 19 regions; no VNet; not supported with the Copilot harness",
      "Underlying chat + embedding model usage (preview pricing may change)", learn("agents/concepts/what-is-memory")),
    T("skills", "G", "Skills", "skill_reference", "preview", "svc", CHECK, PARTIAL,
      "SKILL.md bundles that define how to do a task: toolbox MCP resources (skill://name), the Copilot harness or the shell tool",
      "Same Foundry project only; header Foundry-Features: Skills=V1Preview; a prompt agent uses skills only through the shell tool",
      "name <= 64 chars, description <= 1,024; versions immutable; up to 200 skills + 50 file_ids per shell environment; Copilot harness: up to 50 skill references",
      "Not stated", learn(T_ + "skills")),
    T("reminder", "G", "Reminder", "reminder_preview", "preview", "svc", CHECK, DASH,
      "A hosted agent schedules itself: minutes (1-43,200 = 30 days) + input create a scheduled routine that re-invokes the same agent on the same conversation",
      "Connectionless; toolbox only; hosted agents only",
      "Not for prompt agents; unlike regular routines (new conversations) it keeps the conversation context",
      "Routine invocation; no meter stated", learn(T_ + "reminder-tool")),
    T("tool_search", "G", "Tool search", "toolbox_search", "notag", "svc", CHECK, DASH,
      "Hides all toolbox tools and returns tool_search + call_tool; BM25 ranking over tool name, description and parameters",
      "Toolbox only - not available for direct integration",
      "tool_search limit default 5, max 10; use beyond ~10-15 tools; pin, add context or auto-pin; doesn't count toward the unnamed-tool limit",
      "Not stated", learn(T_ + "tool-search")),
    T("toolbox", "G", "Toolbox (the bundle)", "one MCP endpoint", "mixed", "svc", DASH, DASH,
      "Bundles tools and skills behind one governed, versioned MCP endpoint; guardrail (RAI policy) applied at the toolbox layer",
      "Agent identity needs Foundry User on the project; each tool authenticates through its own connection",
      "At most one unnamed tool per built-in type (name the rest); no numeric toolbox limits documented; GA not stated - sub-features are preview",
      "No toolbox pricing statement found", learn("agents/concepts/toolbox-overview")),
]
BY_ID = {t["id"]: t for t in TOOLS}


# ====================================================================== small helpers
def chip_for(tid, size=15, w=None, label=None):
    t = BY_ID[tid]
    th_name = FAM[t["fam"]][1]
    _, _, dash, suffix = ST[t["st"]]
    if t["st"] == "retire":
        th_name = "red"
    return Chip((label or t["chip"]) + suffix, theme=th_name, size=size, dash=dash, w=w)


class Stat(Rect2):
    """Big-number summary tile."""

    def __init__(self, w, big, caption, theme_name, h=132, big_size=48, split=236, cap_size=18):
        self.th = get_theme(theme_name)
        self.w, self.big, self.big_size, self.split, self.cap_size = w, big, big_size, split, cap_size
        self.lines = wrap_text(caption, w - split - 22, cap_size)
        self.h = max(h, len(self.lines) * cap_size * 1.25 + 40)
        self.x = self.y = 0.0

    def place(self, cv, x, y, h=None):
        self.x, self.y = x, y
        H = max(self.h, h or 0)
        self.h = H
        bw, bh = text_size(self.big, self.big_size)
        th = self.th
        with cv.group():
            cv.rect(x, y, self.w, H, stroke=th.stroke, fill=th.fill, style="hachure", sw=2)
            cv.text(x + 22, y + (H - bh) / 2, self.big, size=self.big_size, color=th.deep)
            cv.text(x + self.split, y + (H - len(self.lines) * self.cap_size * 1.25) / 2, "\n".join(self.lines),
                    size=self.cap_size, color=INK)
        cv.register("stat", x, y, self.w, H)
        return self


def key_row(cv, x, y, parts, size=14, gap=26):
    """Legend row. parts: ('swatch', theme, label) | ('mark', MARK, label) | ('chip', theme, dash, label) | ('text', label)."""
    cx = x
    for p in parts:
        kind = p[0]
        if kind == "swatch":
            th = get_theme(p[1])
            cv.rect(cx, y + 1, 26, 18, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0)
            t = cv.text(cx + 34, y, p[2], size=size)
            cx += 34 + t.w + gap
        elif kind == "mark":
            draw_mark(cv, p[1], cx + 11, y + 10, 18)
            t = cv.text(cx + 30, y, p[2], size=size)
            cx += 30 + t.w + gap
        elif kind == "chip":
            c = Chip(p[3], theme=p[1], size=size, dash=p[2], pad_y=2, pad_x=9, fill="soft")
            c.place(cv, cx, y - 2)
            cx += c.w + gap - 6
        else:
            t = cv.text(cx, y, p[1], size=size, color=MUTED)
            cx += t.w + gap
    return cx


def masonry(cv, x, y, blocks, ncols, colw, gap=40):
    """Place blocks into the currently shortest column (keeps columns tidy for cards of different heights)."""
    heights = [0.0] * ncols
    for b in blocks:
        i = min(range(ncols), key=lambda k: heights[k])
        b.place(cv, x + i * (colw + gap), y + heights[i])
        heights[i] += b.h + gap
    return x + ncols * colw + (ncols - 1) * gap, y + max(heights) - gap


def ordered_columns(cv, x, y, blocks, ncols, colw, gap=40):
    """Split blocks into ncols contiguous groups that minimise the tallest column (keeps reading order and families together)."""
    hs = [b.h for b in blocks]
    n = len(hs)
    pre = [0.0]
    for h in hs:
        pre.append(pre[-1] + h)

    def seg(i, j):
        return pre[j] - pre[i] + gap * (j - i - 1)

    INF = 1e18
    best = [[INF] * (n + 1) for _ in range(ncols + 1)]
    cut = [[0] * (n + 1) for _ in range(ncols + 1)]
    best[0][0] = 0.0
    for c in range(1, ncols + 1):
        for j in range(1, n + 1):
            for i in range(c - 1, j):
                v = max(best[c - 1][i], seg(i, j))
                if v < best[c][j]:
                    best[c][j], cut[c][j] = v, i
    groups, j = [], n
    for c in range(ncols, 0, -1):
        i = cut[c][j]
        groups.append((i, j))
        j = i
    groups.reverse()
    bottom = y
    for ci, (i, j) in enumerate(groups):
        cy = y
        for b in blocks[i:j]:
            b.place(cv, x + ci * (colw + gap), cy)
            cy += b.h + gap
        bottom = max(bottom, cy - gap)
    return x + ncols * colw + (ncols - 1) * gap, bottom


# ====================================================================== wall (the menu)
def build_wall(cv, x, y):
    n = len(FAMS)
    gap = 22
    pw = (W - gap * (n - 1)) / n
    pad = 20
    by_fam = {c: [t for t in TOOLS if t["fam"] == c] for c, *_ in FAMS}
    max_n = max(len(v) for v in by_fam.values())
    head_h = 60
    chip_h = 32
    min_h = 2 * pad + head_h + max_n * (chip_h + 9) - 9
    bottom = y
    for i, (code, title, th_name, icon) in enumerate(FAMS):
        px = x + i * (pw + gap)
        with cv.panel(px, y, theme=th_name, style="solid", fill="soft", pad=pad, w=pw, min_h=min_h) as p:
            place_icon(cv, icon, p.ix, p.iy, 34)
            cv.text(p.ix + 46, p.iy - 1, f"{code}  {title}", size=21, color=get_theme(th_name).deep)
            cv.text(p.ix + 46, p.iy + 26, f"{len(by_fam[code])} tools", size=14, color=MUTED)
            cy = p.iy + head_h
            for t in by_fam[code]:
                c = chip_for(t["id"], size=15, w=pw - 2 * pad)
                c.place(cv, p.ix, cy)
                cy += c.h + 9
        bottom = max(bottom, p.bottom)
    return bottom


# ====================================================================== dispatch diagram
def build_dispatch(cv, x, y, w):
    with cv.panel(x, y, title="Who executes the tool call?", sub="the model only proposes a call - the Agent Service runtime dispatches it",
                  theme="gray", style="dotted", pad=26, title_size=28, sub_size=16, w=w) as fr:
        lx = fr.ix + 330
        lane_w = w - 52 - 330
        lane_pad = 18

        # ---- lane 1: client-side
        with cv.panel(lx, fr.iy, title="Client-side: your app executes it", sub="1 the runtime returns the call item   2 your app submits the output",
                      theme="red", style="dashed", fill="soft", pad=lane_pad, title_size=22, sub_size=15, w=lane_w) as l1:
            cx, cy = l1.ix, l1.iy
            c1 = chip_for("function", size=15)
            c1.place(cv, cx, cy + 2)
            c2 = chip_for("computer_use", size=15)
            c2.place(cv, cx, cy + 2 + c1.h + 10)
            a = Box(330, "Your app executes the action", sub="API call, database write, UI click", theme="red", h=86, size=17).place(cv, cx + 330, cy)
            b = Box(330, "Submits the output", sub="function_call_output or computer_call_output, same conversation", theme="red", h=86, size=17).place(cv, cx + 330 + 330 + 90, cy)
            connect(cv, a, b)
            cv.text(cx + 330, cy + 98, "Function runs expire 10 minutes after creation; computer use needs acknowledged_safety_checks", size=14, color=MUTED, wrap=lane_w - 330 - 40)

        # ---- lane 2: service-side
        with cv.panel(lx, l1.bottom + 24, title="Service-side: Foundry or a Microsoft-managed service runs it",
                      sub="3 the runtime runs the tool itself and returns the result (and citations) to the model",
                      theme="green", style="dashed", fill="soft", pad=lane_pad, title_size=22, sub_size=15, w=lane_w) as l2:
            ids = ["code_interpreter", "file_search", "ai_search", "web_search", "bing_grounding", "bing_custom", "image", "shell",
                   "memory", "sharepoint", "managed_mcp", "fabric_dataagent", "skills", "reminder", "tool_search",
                   "language_agents", "cu_tool"]
            cf = ChipFlow([chip_for(i, size=14) for i in ids], lane_w - 2 * lane_pad, gap=9)
            cf.place(cv, l2.ix, l2.iy + 2)
            cv.text(l2.ix, l2.iy + cf.h + 14, "Sandbox, vector store, Bing, Copilot Retrieval API, gpt-image-1, memory store ... run inside Foundry or its backing services",
                    size=14, color=MUTED, wrap=lane_w - 2 * lane_pad)

        # ---- lane 3: calls out
        with cv.panel(lx, l2.bottom + 24, title="Calls out: the runtime invokes a remote endpoint, resource or compute",
                      sub="4 MCP, HTTPS, A2A or a queue message goes out; the reply comes back as tool output",
                      theme="ink", style="dashed", fill="soft", pad=lane_pad, title_size=22, sub_size=15, w=lane_w) as l3:
            bw = (lane_w - 2 * lane_pad - 2 * 26) / 3
            items = [
                ("MCP server", "remote, 100 s non-streaming timeout", "orange"),
                ("Your REST API", "OpenAPI 3.0 / 3.1 spec, project connection", "orange"),
                ("Remote A2A agent", "a2a v1.0 GA, a2a_preview v0.3", "orange"),
                ("Function app", "Storage queues, echo CorrelationId", "orange"),
                ("ACA session pool", "custom code interpreter MCP server", "lime"),
                ("Playwright workspace", "browser automation, Live View", "cyan"),
            ]
            boxes = [Box(bw, t, sub=s, theme=th_name, h=78, size=17, sub_size=13, fill="soft") for t, s, th_name in items]
            r1, b1 = row(cv, l3.ix, l3.iy, boxes[:3], gap=26)
            r2, b2 = row(cv, l3.ix, b1 + 16, boxes[3:], gap=26)
            also = ChipFlow([chip_for(i, size=14) for i in ("foundry_iq", "fabric_iq", "work_iq", "speech_mcp", "language_mcp", "translator")],
                            lane_w - 2 * lane_pad - 235, gap=9)
            cv.text(l3.ix, b2 + 18, "Also over MCP, A2A or OpenAPI:", size=14, color=MUTED)
            also.place(cv, l3.ix + 235, b2 + 14)

        # ---- runtime bus
        top = l1.y + 20
        bottom = l3.bottom - 20
        rt = Box(250, "Agent Service runtime", sub="model proposes a tool call; the runtime dispatches it", theme="green", icon="agent",
                 h=bottom - top, size=22, sub_size=15, fill="hatch").place(cv, fr.ix, top)
        # (lane, vertical position inside the lane, step number, direction, number colour)
        for lane, frac, num, back, ntheme in ((l1, 0.30, 1, False, "red"), (l1, 0.72, 2, True, "red"),
                                              (l2, 0.5, 3, False, "green"), (l3, 0.5, 4, False, "gray")):
            yy = lane.y + lane.h * frac
            t_lane = (yy - lane.y) / lane.h
            t_rt = (yy - rt.y) / rt.h
            if back:
                connect(cv, lane, rt, a_side="left", b_side="right", ta=t_lane, tb=t_rt, dash="dashed", num=num, num_theme=ntheme)
            else:
                connect(cv, rt, lane, a_side="right", b_side="left", ta=t_rt, tb=t_lane, num=num, num_theme=ntheme)
    return fr


# ====================================================================== decision tree
TREE = [
    ("Private documents or knowledge", "teal", [
        ("file_search", "File search", "simplest; Basic setup = zero infra"),
        ("ai_search", "Azure AI Search", "you already have an index"),
        ("foundry_iq", "Foundry IQ knowledge base", "permission-aware, multi-source"),
        ("sharepoint", "SharePoint or Work IQ", "Microsoft 365 content per user (preview)"),
    ]),
    ("Fresh public web information", "cyan", [
        ("web_search", "Web search", "recommended default (GA)"),
        ("bing_grounding", "Grounding with Bing", "need count, freshness, market, set_lang or non-OpenAI models"),
        ("bing_custom", "Bing Custom Search", "restrict to chosen domains (preview)"),
    ]),
    ("Call an API, service or agent", "orange", [
        ("openapi", "OpenAPI", "your REST API"),
        ("mcp", "MCP", "real-time tools from an MCP server"),
        ("azure_functions", "Azure Functions", "async job over Storage queues"),
        ("a2a", "A2A", "another agent (or Workflows)"),
    ]),
    ("Operate a UI that has no API", "cyan", [
        ("browser", "Browser automation", "managed Playwright browser (GA)"),
        ("computer_use", "Computer use", "pixels and desktop; computer-use-preview (preview)"),
    ]),
    ("Run code or shell commands", "lime", [
        ("code_interpreter", "Code interpreter", "Python sandbox"),
        ("custom_ci", "Custom code interpreter", "own packages and images (preview)"),
        ("shell", "Shell tool + skills", "Linux container (preview)"),
    ]),
    ("Side effects inside my own app", "lime", [
        ("function", "Function calling", "client-side: your app executes it"),
    ]),
    ("Remember or schedule", "grape", [
        ("memory", "Memory", "long-term, across conversations (preview)"),
        ("reminder", "Reminder", "hosted agent re-invokes itself (preview)"),
    ]),
]


def build_tree(cv, x, y, min_h=0):
    root_w, cat_w, leaf_w, leaf_h = 230, 250, 240, 84
    gap_rc, gap_cl, leaf_gap = 70, 56, 16
    with cv.panel(x, y, title="Which tool for which job?", sub=f"pick the need first, then the constraint ({AS_OF})",
                  theme="gray", style="dotted", pad=26, title_size=28, sub_size=16, min_h=min_h) as fr:
        top = fr.iy
        pitch = leaf_h + 16 + 16
        cats = []
        leaf_x = fr.ix + root_w + gap_rc + cat_w + gap_cl
        for i, (cat, th_name, leaves) in enumerate(TREE):
            ry = top + i * pitch
            cb = Box(cat_w, cat, h=leaf_h + 16, theme=th_name, size=17, fill="solid").place(cv, fr.ix + root_w + gap_rc, ry)
            n = len(leaves)
            gw = n * leaf_w + (n - 1) * leaf_gap + 16
            with cv.panel(leaf_x, ry, theme=th_name, style="dotted", fill="none", pad=8, w=gw, min_h=leaf_h + 16) as gp:
                boxes = []
                for tid, nm, sub in leaves:
                    t = BY_ID[tid]
                    boxes.append(Box(leaf_w, nm, sub=sub, theme=FAM[t["fam"]][1], h=leaf_h, size=16, sub_size=13, fill="soft"))
                row(cv, gp.ix, gp.iy, boxes, gap=leaf_gap)
            connect(cv, cb, gp, a_side="right", b_side="left")
            cats.append(cb)
        total_h = len(TREE) * pitch - 16
        root = Box(root_w, "What does the agent need?", h=170, theme="green", shape="ellipse", size=20, fill="hatch").place(
            cv, fr.ix, top + total_h / 2 - 85)
        for cb in cats:
            connect(cv, root, cb, a_side="right", b_side="left", route="elbow")
    return fr


# ====================================================================== matrix
def matrix_rows():
    rows = []
    for code, title, th_name, _ in FAMS:
        th = get_theme(th_name)
        rows.append([{"text": f"{code}  {title}", "theme": th_name, "color": th.deep}] + [{"text": "", "theme": th_name}] * 8)
        for t in [t for t in TOOLS if t["fam"] == code]:
            st_label, st_theme, _, _ = ST[t["st"]]
            wh_label, wh_theme = WH[t["wh"]]
            rows.append([
                {"text": f"{t['name']}\n{t['typ']}", "theme": th_name, "color": th.deep, "link": t["url"]},
                t["what"],
                {"text": wh_label, "theme": wh_theme, "color": get_theme(wh_theme).deep},
                t["auth"],
                {"text": st_label, "theme": st_theme, "color": get_theme(st_theme).deep},
                t["tb"], t["net"],
                t["limits"], t["bill"],
            ])
    return rows


COLS = [("Tool and type string", 230), ("What it does and how it runs", 580), ("Executes", 190), ("Auth and prerequisites", 640),
        ("Status", 150), ("Toolbox", 100), ("VNet", 110), ("Region, model and limits", 940), ("Billing meter", 360)]


# ====================================================================== build
def build(cv: Canvas) -> None:
    right, bottom = title_block(
        cv, 0, 0, "Every tool an agent can use",
        f"Foundry Agent Service tool catalog - where each tool runs, how it authenticates, GA or preview, toolbox or direct-only, network isolation, limits and billing  ({AS_OF})",
        icon="toolbox-icon", w=W)

    # ---------------------------------------------------------------- at a glance
    y = bottom + 34
    sw = (W - 4 * 40) / 5
    stats = [
        Stat(sw, "128", "tools can be registered per agent. More returns tool_limit_exceeded (HTTP 400).", "orange"),
        Stat(sw, "13 + 7", "toolbox-eligible tool types + direct-only ones (function calling, Bing grounding, computer use, image generation, SharePoint, Fabric data agent, Azure Functions).", "orange"),
        Stat(sw, "2", "tools your own app executes: function calling and computer use. The rest run in Foundry or call out to a remote endpoint.", "red"),
        Stat(sw, "2 gates", "Region AND model must both say Yes. If either table shows No, the tool can't run.", "yellow"),
        Stat(sw, "Nov 6", "2026-11-06: the Fabric data agent tool is scheduled for deprecation - use Fabric IQ (preview).", "red"),
    ]
    hh = max(s.h for s in stats)
    row(cv, 0, y, stats, gap=40)
    y += hh + 54

    # ---------------------------------------------------------------- the menu
    r, b = section_header(cv, 0, y, "The menu: 32 tools in 7 families", w=W, size=34,
                          sub="Dashed outline = preview, dotted = GA + preview parts, red = deprecated. GA means the Learn page shows no preview tag. Families A-G repeat in the matrix below.")
    y = b + 20
    bottom = build_wall(cv, 0, y)
    y = bottom + 60

    # ---------------------------------------------------------------- diagrams
    r, b = section_header(cv, 0, y, "Two ways to read the catalog: who executes the call, and which tool fits the job", w=W, size=34)
    y = b + 24
    tree_w = 230 + 70 + 250 + 56 + 4 * 240 + 3 * 16 + 16 + 52
    tree_x = W - tree_w
    dispatch = build_dispatch(cv, 0, y, tree_x - 60)
    tree = build_tree(cv, tree_x, y, min_h=dispatch.h)
    y = max(dispatch.bottom, tree.bottom) + 64

    # ---------------------------------------------------------------- matrix
    r, b = section_header(cv, 0, y, "The big comparison matrix", w=W, size=34,
                          sub="Each tool name links to its Learn page. Billing meters are qualitative: the docs say 'additional charges' without prices.")
    y = b + 18
    nx = key_row(cv, 0, y, [
        ("text", "Executes:"), ("swatch", "green", "Service-side (inside Foundry or a Microsoft-managed service)"),
        ("swatch", "ink", "Calls out (remote endpoint, resource or compute)"), ("swatch", "red", "Client-side (your app executes)"),
    ])
    y += 30
    key_row(cv, 0, y, [
        ("text", "Marks:"), ("mark", CHECK, "yes"), ("mark", PARTIAL, "conditional or indirect (see the row)"), ("mark", CROSS, "no / direct-only"),
        ("mark", DASH, "not stated in the docs read"),
        ("text", "VNet column ="), ("mark", CHECK, "private endpoint, VNet subnet or Microsoft backbone"), ("mark", PARTIAL, "public endpoint or partial"),
        ("mark", CROSS, "not supported"),
    ])
    y += 38
    tbl = Table(COLS, matrix_rows(), theme="gray", size=14, head_size=16, pad_x=10, pad_y=6, zebra=True)
    tbl.place(cv, 0, y)
    y = tbl.bottom + 64

    # ---------------------------------------------------------------- gates and limits
    r, b = section_header(cv, 0, y, "Gates and limits: region, model and Agent Service quotas", w=W, size=34,
                          sub=f"From the Agent Service quotas page ({AS_OF}). Check the live tables before you pick a region.")
    y = b + 24
    gate_rows = [
        [("Computer use", "cyan"), "Yes only in Canada Central, Central US, East US 2, Japan West, South India, Sweden Central, Switzerland West, West Central US, West Europe (the tool page lists only eastus2, swedencentral, southindia)",
         "computer-use-preview only; access by application form"],
        [("Browser automation", "cyan"), "No in Japan West, Switzerland West, West Central US (the tool page lists 7 regions - docs disagree)",
         "No on gpt-5.1 and gpt-5.2; Yes for GPT-4.1, GPT-4o, gpt-5, gpt-5.2-chat, gpt-5.3+ and others"],
        [("File search", "teal"), "No in Brazil South and Italy North", "Yes for almost every listed model (not computer-use-preview or o3-deep-research)"],
        [("Code interpreter", "lime"), "Yes in all 29 listed regions (tool-best-practice says No in southcentralus and spaincentral - docs disagree)",
         "Yes for almost every listed model (not computer-use-preview or o3-deep-research)"],
        [("Function calling", "lime"), "No in Brazil South, North Central US, South Central US, West US", "See the Functions column of the model table"],
        [("Image generation", "lime"), "Yes in all listed regions", "Orchestrator gpt-5 only, plus gpt-image-1 deployed in the same project"],
        [("Azure Functions", "orange"), "-", "gpt-5.1 and gpt-5.2 only"],
        [("A2A", "orange"), "Yes in all listed regions", "GPT-4.1 family, gpt-4o (+ mini), gpt-5, gpt-5.2-chat, gpt-5.3 / 5.4 / 5.5, gpt-chat-latest, o3, o3-mini, o4-mini, MAI-DS-R1 (No on gpt-5.1 and gpt-5.2)"],
        [("MCP", "orange"), "Yes in all listed regions", "Broad - GPT-4.1 / 4o / 5.x, o-series, Grok, Llama, DeepSeek, FW-*, model-router, gpt-oss-120b, MAI-DS-R1 - but not every variant (gpt-5-chat, gpt-5-nano, gpt-5-pro and o3-mini show No)"],
        [("Memory (preview)", "grape"), "19 regions: Australia East, Brazil South, Canada East, East US 2, France Central, Italy North, Japan East, Korea Central, North Central US, Norway East, South Africa North, South India, Sweden Central, Switzerland North, UAE North, UK South, West US, West US 2, West US 3",
         "Compatible Azure OpenAI chat + embedding deployments"],
        [("Bing grounding, private network", "cyan"), "With a network-secured setup only the regions listed on the limits page (25 regions)", "Azure OpenAI and non-OpenAI Foundry Models"],
    ]
    t_gate = Table([("Tool", 220), ("Region gate (Learn region table)", 860), ("Model gate (Learn model table)", 820)], gate_rows, theme="gray", size=14, head_size=16,
                   pad_y=6, first_col_theme="gray", title="Region and model gates", title_size=24)
    t_gate.place(cv, 0, y)
    lim_rows = [
        ["Tools registered per agent", "128 (tool_limit_exceeded, HTTP 400)"],
        ["Versions per agent", "1,000 (terminal UserError; delete old versions first)"],
        ["Files per agent or thread", "10,000"],
        ["File size, prompt agents", "512 MB"],
        ["File tokens, attach to a vector store", "2,000,000 per the limits page (the file-search page says 5,000,000 - docs disagree)"],
        ["Concurrent hosted-agent sessions", "2,000 in Canada Central, East US 2, Japan East, North Central US, South Africa North, Southeast Asia, Sweden Central; 1,000 elsewhere"],
        ["Session errors", "session_quota_exceeded, regional_session_quota_exceeded (HTTP 429), subnet_exhausted"],
        ["Voice session", "60 min; stored voice conversations and audio kept 60 days"],
    ]
    lim_w = W - t_gate.w - 60
    t_lim = Table([("Agent Service limit", 300), ("Default value", lim_w - 300)], lim_rows, theme="yellow", size=14, head_size=16, pad_y=6,
                  first_col_theme="yellow", title="Agent Service limits (fixed, not increasable)", title_size=24)
    t_lim.place(cv, t_gate.right + 60, y)
    y = max(t_gate.bottom, t_lim.bottom) + 64

    # ---------------------------------------------------------------- per-tool cards
    r, b = section_header(cv, 0, y, "Per-tool cards: limits, gotchas and the loops worth knowing", w=W, size=34,
                          sub="The matrix has the headline facts; these cards add the details an architect trips over.")
    y = b + 26
    CW = (W - 4 * 40) / 5
    S = lambda label, path, base="azure/foundry": (label, learn(path, base=base))
    cards = [
        Card(CW, "Function calling", [
            "Model emits a function_call item; your app executes it and returns function_call_output in the same conversation",
            "# Loop",
            "= define tools -> create agent version -> responses.create -> function_call -> app executes -> function_call_output -> final answer",
            "Submit outputs before the run expires: runs expire 10 minutes after creation",
            "Portal can't add or edit definitions - SDK or REST only; the Copilot harness rejects strict: true",
            "! Treat model-generated arguments and your outputs as untrusted; for long jobs return a status and poll",
        ], theme="lime", badge="ga", icon="code", body_size=15, src=[S("Function calling", T_ + "function-calling")]),
        Card(CW, "Code interpreter", [
            "Python in a Microsoft-managed sandbox: Azure Container Apps dynamic sessions with Hyper-V isolation",
            "Session active up to 1 h, idle timeout 30 min; each concurrent conversation gets its own session",
            "No outbound network and a fixed package set - use a custom code interpreter for more",
            "27 supported file-type rows (csv, docx, pdf, pptx, xlsx, py, json, png, zip ...)",
            "In a toolbox, upload via resource-level POST {account_endpoint}/openai/v1/files with header x-aml-project-id; files mount at /mnt/data/{file-id}-{name}",
            "! Hosted-agent toolbox: no user isolation (the container is project-shared)",
        ], theme="lime", badge="ga", icon="container-apps", body_size=15, src=[S("Code interpreter", T_ + "code-interpreter")]),
        Card(CW, "Custom code interpreter", [
            "Your ACA Dynamic Sessions pool exposes an MCP server; you pick packages, images and compute",
            "az 2.60+, Python 3.12+; register the feature Microsoft.App/SessionPoolsSupportMCP (15-30 min)",
            "Roles: Foundry Owner and Container Apps ManagedEnvironment Contributor (PIM, temporary) to provision",
            "! Use the mcpServerEndpoint output as server_url, not poolManagementEndpoint",
            "No direct file I/O - pass data or SAS URLs",
        ], theme="lime", badge="preview", icon="container-apps", body_size=15, src=[S("Custom code interpreter", T_ + "custom-code-interpreter")]),
        Card(CW, "Shell tool and skills", [
            "Hosted container (container_auto) or local mode where you run shell_calls",
            "Debian 12, Python 3.11, Node 22.16.0, Java 17, PHP 8.2, Ruby 3.1, Go 1.23.2; non-interactive, no sudo, no outbound network",
            "Skills are SKILL.md bundles; a prompt agent can use skills only through the shell tool",
            "Message attachments are NOT mounted - use environment.file_ids (up to 50, under /mnt/data); up to 200 skills",
            "! Skills are privileged code - don't expose open catalogs",
        ], theme="lime", badge="preview", icon="code", body_size=15, src=[S("Shell tool and skills", T_ + "skills-shell-tool"), S("Skills", T_ + "skills")]),
        Card(CW, "Image generation", [
            "Needs two deployments in the same project: an orchestrator LLM (gpt-5) and gpt-image-1",
            "Every request must carry header x-ms-oai-image-generation-deployment",
            "Parameters: size (1024x1024, 1024x1536, 1536x1024, auto), quality, background, output_format, output_compression 0-100, moderation",
            "! Java can't set the header - call REST; the content filter can block prompts",
        ], theme="lime", badge="preview", icon="image", body_size=15, src=[S("Image generation", T_ + "image-generation")]),
        Card(CW, "File search and vector stores", [
            "Defaults: chunk 800 tokens, overlap 400, text-embedding-3-large at 256 dims, up to 20 chunks in context",
            "10,000 files per vector store; 512 MB per file; batches up to 500 files",
            "Conversation vector stores expire 7 days after last active",
            "# Ingestion",
            "= upload (purpose=assistants) -> add to a vector store -> poll until completed -> attach (<= 1 per agent / conversation) -> respond",
            "! Per-file token cap: 5,000,000 on the file-search page vs 2,000,000 on the limits page",
            "! Deleting the underlying file removes it from every store and agent; portal toolbox flow needs vector_store_ids",
        ], theme="teal", badge="ga", icon="files", body_size=15, src=[S("File search", T_ + "file-search"), S("Vector stores", "agents/concepts/vector-stores")]),
        Card(CW, "Retrieval approach: RAG, fine-tuning or a tool?", [
            "RAG = retrieve -> augment -> generate; index modes are keyword, semantic, vector or hybrid (+ semantic ranking)",
            "RAG for private or changing data; fine-tuning for behaviour and style (not fresh knowledge); agent tools when the agent needs retrieval as a tool",
            "Agentic RAG: the model splits the input into focused sub-queries run in parallel and returns grounding data, citations and execution metadata",
            "Azure AI Search is a recommended index store; the project link is a project connection or an index asset ID",
            "! Apply access control at retrieval time (security filters), prefer Entra over keys, treat retrieved content as untrusted",
            "Cost levers: retrieval round trips, embeddings (index + query time), extra input tokens",
        ], theme="teal", icon="search", body_size=15, src=[S("Retrieval-augmented generation", "concepts/retrieval-augmented-generation")]),
        Card(CW, "Azure AI Search tool vs Foundry IQ", [
            "AI Search tool: one index per tool, top_k 5, query_type vector_semantic_hybrid by default",
            "Private AI Search: Standard setup + VNet injection + Entra project MI (no keys)",
            "az ml and azure-ai-ml can't create connections for new projects - use az cognitiveservices account project connection create",
            "Foundry IQ: knowledge base on agentic retrieval; Azure AI Search required, Agent Service not required",
            "Reasoning effort: minimal (<= 10 sources, no LLM) / low (<= 3 sources, <= 3 sub-queries) / medium (<= 5 sources, <= 5 sub-queries)",
            "LLM query planning only with gpt-4o, gpt-4.1 or gpt-5 series; sources: Blob, OneLake, SharePoint, web",
            "In a toolbox the KB rides a remote-tool connection with agentic-identity - a user token is rejected on purpose",
            "Three IQ workloads, each standalone: Fabric IQ (analytics), Work IQ (M365), Foundry IQ (enterprise knowledge)",
        ], theme="teal", icon="ai-search", body_size=15, src=[S("AI Search tool", T_ + "ai-search"), S("What is Foundry IQ?", "agents/concepts/what-is-foundry-iq")]),
        Card(CW, "Web search vs Grounding with Bing", [
            "web_search needs no extra resource: search_context_size low / medium / high, custom_search_configuration for domains",
            "Bing grounding: your Bing resource; count 5 (max 50), freshness, market, set_lang",
            "! Data leaves the Azure compliance and geography boundary; Microsoft DPA doesn't apply; GCC commitments are waived",
            "Both behave as public endpoints in network-secured projects",
            "Admins can disable per subscription (Azure CLI, Contributor via PIM) or block via Azure Policy deny-disallowed-connections",
        ], theme="cyan", badge="ga", icon="bing", body_size=15, src=[S("Web search", T_ + "web-search"), S("Bing tools", T_ + "bing-tools")]),
        Card(CW, "Browser automation", [
            "Playwright Workspaces remote MCP server: Live View, screenshots, Take control (human in the loop)",
            "Auth: Playwright access token (API key), project managed identity (recommended) or agent identity",
            "Roles: Foundry User, Foundry Project Manager, Playwright Workspace Contributor for the project MI",
            "Resource type Microsoft.LoadTestService/playwrightWorkspaces; billed at Playwright workspace pricing",
            "Hosted-agent quickstart uses PLAYWRIGHT_SERVICE_RESOURCE_ID and PLAYWRIGHT_SERVICE_URL; the Contributor role is granted after deploy",
            "! Live View URL is sensitive; avoid payments and sensitive sign-ins; not supported in network-isolated projects",
        ], theme="cyan", badge="ga", icon="browser", body_size=15, src=[S("Browser automation", T_ + "browser-automation")]),
        Card(CW, "Computer use", [
            "# Loop",
            "= request -> computer_call (click, type, scroll, screenshot) -> check pending_safety_checks -> user approves -> app executes -> screenshot -> computer_call_output with acknowledged_safety_checks -> repeat until text",
            "Safety checks: malicious_instructions, irrelevant_domain, sensitive_domain",
            "Chain turns with previous_response_id; run in a sandboxed VM",
            "! The page warns of significant security and privacy risks",
        ], theme="cyan", badge="preview", icon="vm", body_size=15, src=[S("Computer use", T_ + "computer-use")]),
        Card(CW, "MCP and OpenAPI", [
            "MCP: remote servers only; 100 s non-streaming timeout; allowed_tools [] = ALL tools; default require_approval = always",
            "OpenAPI 3.0 / 3.1 spec inline; operationId mandatory; one API-key scheme per tool",
            "Auth is always a project connection, even anonymous (auth.type: project_connection)",
            "Token audiences: Storage https://storage.azure.com, Key Vault https://vault.azure.net, AI Search https://search.azure.com, Translator https://cognitiveservices.azure.com, ARM https://management.azure.com",
        ], theme="orange", badge="ga", icon="mcp", body_size=15, src=[S("MCP", T_ + "model-context-protocol"), S("OpenAPI", T_ + "openapi")]),
        Card(CW, "A2A and Azure Functions", [
            "A2A: a2a (GA, v1.0) and a2a_preview (v0.3); the azd toolbox flow still emits the preview tool",
            "Target needs incoming A2A + Foundry Agent Consumer; tasks and context kept 60 days",
            "Incoming A2A (expose your agent) is preview, REST or Python SDK only; default served version is v0.3 if unspecified",
            "Azure Functions: Standard setup only; input queue -> trigger -> output queue; echo CorrelationId",
            "Needs Storage Queue Data Contributor for the project MI and the function-app MI",
        ], theme="orange", icon="a2a", body_size=15, src=[S("A2A", T_ + "agent-to-agent"), S("Azure Functions", T_ + "azure-functions")]),
        Card(CW, "SharePoint, Work IQ and Fabric IQ", [
            "All three act as the signed-in user (OBO or delegated): same tenant, per-user permissions, no app-only identity",
            "SharePoint: one tool per agent, 200 requests per user per hour, doesn't work when published to Teams",
            "! SharePoint with an app identity fails: AuthenticationError: AppOnly OBO tokens not supported",
            "Work IQ: one-time Global Admin consent of WorkIQAgent.Ask; A2A endpoint https://workiq.svc.cloud.microsoft/a2a/",
            "Work IQ 'Principal does not have access to API/Operation' -> Foundry User at account AND project scope",
            "Fabric IQ: ontology, semantic model or data agent; F2+ or P1+ capacity",
            "! Test with two users of different permissions - a successful call alone doesn't prove correct delegation",
        ], theme="indigo", badge="preview", icon="m365", body_size=15, src=[S("SharePoint", T_ + "sharepoint"), S("Work IQ", T_ + "work-iq"), S("Fabric IQ", T_ + "fabric-iq")]),
        Card(CW, "Network-isolated projects: tool gotchas", [
            "Agents reach tools through the project's private endpoint and need a project-level capability host; account-level only gives 'name or host unknown'",
            "Public-endpoint tools (Bing grounding, web search, SharePoint) can be blocked with Azure Policy",
            "AI Search indexer over private endpoints: set executionEnvironment to Private or the index silently stays empty",
            "Recreate file-search vector stores when a VNet is enabled (unless BYO) and again after disabling it",
            "! An APIM AI gateway created from the portal for a private Foundry is public by default - isolate it in the Azure portal",
            "Samples: 15-private-network-standard-agent-setup and 19-private-network-agent-tools (Bicep and Terraform)",
        ], theme="indigo", icon="vnet", body_size=15, src=[S("Configure private link", "how-to/configure-private-link"), S("Toolbox network isolation", T_ + "toolbox-network-isolation")]),
        Card(CW, "Memory", [
            "Extraction -> consolidation (LLM) -> retrieval; user profile, chat summary and procedural memories",
            "100 scopes per store, 10,000 memories per scope, search and update 1,000 req/min each",
            "update_delay debounces writes (set 0 to force); no VNet; not supported with the Copilot harness",
            "! Memory poisoning and prompt injection are real risks - use Content Safety",
        ], theme="grape", badge="preview", icon="cubes", body_size=15, src=[S("What is memory?", "agents/concepts/what-is-memory")]),
        Card(CW, "Tool search and toolbox rules", [
            "toolbox_search hides all toolbox tools and returns tool_search + call_tool (BM25; limit default 5, max 10)",
            "At most one tool without a name per built-in type in a toolbox; MCP tools need a unique server_label",
            "Stream tools/call: non-streaming returns 500; no ping and no prompts/list",
            "Add a description to every tool - it drives model selection and tool-search ranking",
        ], theme="grape", icon="toolbox", body_size=15, src=[S("Tool search", T_ + "tool-search"), S("Toolbox overview", "agents/concepts/toolbox-overview")]),
    ]
    notes = [
        Note(CW, "The Fabric data agent tool is scheduled for deprecation on November 6, 2026 (3 days after this research). Migrate in the portal via Tools > Add > Browse all tools > Fabric IQ, or replace the tool type in code.",
             kind="gotcha", title="Deprecation: Fabric data agent", src=[S("Fabric tool", T_ + "fabric")]),
        Note(CW, "Web search, Grounding with Bing and Work IQ send data beyond the Azure or Foundry compliance boundary. Several tools are Standard-agent-setup only: Azure Functions, custom code interpreter, private AI Search.",
             kind="warn", title="Boundaries and setup"),
        Note(CW, "Learn disagrees with itself in places (as of 2026-11-03): per-file token cap, code interpreter and browser automation regions, computer-use regions, 'web search = Azure OpenAI models only' vs the model table, and Work IQ network support. Draw from the tool page and verify in the live tables.",
             kind="info", title="Docs disagree"),
        Note(CW, "Many tool pages add: consider adding the tool through a toolbox to reuse it across agents and runtimes, centralizing credential management, versioning and policy enforcement behind one managed MCP endpoint.",
             kind="tip", title="Toolbox tip (from the tool pages)", src=[S("Toolbox overview", "agents/concepts/toolbox-overview")]),
        Note(CW, "Prompt-agent tools can be set per request with structured inputs - for example choose the vector store or files at runtime instead of baking them into the agent version.",
             kind="tip", title="Structured inputs", src=[S("Structured inputs", "agents/how-to/structured-inputs")]),
    ]
    right, bottom = ordered_columns(cv, 0, y, cards, 5, CW, gap=40)
    y = bottom + 50
    r, nb = row(cv, 0, y, notes, gap=40)
    y = nb + 64

    # ---------------------------------------------------------------- sources
    sources(cv, 0, y, [
        ("Quotas and limits for Agent Service (tool support by region and model)", learn("agents/concepts/limits-quotas-regions")),
        ("What is Toolbox in Foundry? (supported tools)", learn("agents/concepts/toolbox-overview")),
        ("Tool best practices", learn("agents/concepts/tool-best-practice")),
        ("Configure private link (agent tools with network isolation)", learn("how-to/configure-private-link")),
        ("Function calling", learn(T_ + "function-calling")),
        ("Code interpreter", learn(T_ + "code-interpreter")),
        ("File search", learn(T_ + "file-search")),
        ("Azure AI Search tool", learn(T_ + "ai-search")),
        ("What is Foundry IQ?", learn("agents/concepts/what-is-foundry-iq")),
        ("Web search tool", learn(T_ + "web-search")),
        ("Grounding with Bing tools", learn(T_ + "bing-tools")),
        ("Browser automation", learn(T_ + "browser-automation")),
        ("Computer use", learn(T_ + "computer-use")),
        ("OpenAPI tool", learn(T_ + "openapi")),
    ], w=W, cols=4)
