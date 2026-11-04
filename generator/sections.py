"""Gallery sections (META['section'] is one of these keys)."""
SECTIONS: dict[str, tuple[str, str]] = {
    "1": ("Foundry overview", "The platform at a glance: every capability, the resource model, how Foundry evolved and where to start."),
    "2": ("Feature deep dives", "Agent Service, models, Toolbox and MCP, observability, tracing, guardrails, control plane and cost - in detail."),
    "3": ("Reference architectures", "Common scenarios and the Azure landing zone, drawn end to end."),
    "4": ("BCDR and resiliency", "High availability, regional failover, Agent Service disaster recovery and runbooks."),
    "5": ("Authentication and authorization", "Identity types, RBAC roles, agent identity, delegation, network and data protection."),
    "6": ("AI Ops", "AgentOps: lifecycle, CI/CD, monitoring, FinOps and capacity operations."),
    "7": ("Surrounding services", "AI Search, Cosmos DB, the IQ layer and the Azure services Foundry plugs into."),
    "8": ("Under the hood", "How Agent Service, hosted agents, model serving, retrieval and safety work internally."),
}
