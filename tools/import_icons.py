"""Copy a curated subset of the official Azure Architecture icons into generator/assets/icons.

Source: https://learn.microsoft.com/azure/architecture/icons/  (Azure_Public_Service_Icons_V23.zip).
Microsoft permits using these icons in architecture diagrams, training material and documentation.

    python tools/import_icons.py --pack <folder containing the unzipped icon categories>
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "generator" / "assets" / "icons"

# slug used in diagram code -> icon name inside the Azure pack (text after '-icon-service-')
WANTED: dict[str, str] = {
    # AI
    "foundry": "AI-Studio", "openai": "Azure-OpenAI", "ai-search": "Cognitive-Search", "ai-services": "Cognitive-Services",
    "content-safety": "Content-Safety", "ml": "Machine-Learning", "language": "Language", "speech": "Speech-Services",
    "translator": "Translator-Text", "vision": "Computer-Vision", "doc-intelligence": "Form-Recognizers",
    "bot": "Bot-Services", "face": "Face-APIs", "custom-vision": "Custom-Vision", "video-indexer": "Azure-Video-Indexer",
    "applied-ai": "Azure-Applied-AI-Services",
    # data
    "cosmos": "Azure-Cosmos-DB", "sql": "SQL-Database", "storage": "Storage-Accounts", "redis": "Cache-Redis",
    "adx": "Azure-Data-Explorer-Clusters", "databricks": "Azure-Databricks", "synapse": "Azure-Synapse-Analytics",
    "data-factory": "Data-Factories", "event-hubs": "Event-Hubs", "service-bus": "Azure-Service-Bus",
    "event-grid": "Event-Grid-Topics", "stream-analytics": "Stream-Analytics-Jobs", "postgres": "Azure-Database-PostgreSQL-Server",
    "data-lake": "Data-Lake-Storage-Gen1", "file-shares": "Azure-Fileshares",
    # security / identity
    "key-vault": "Key-Vaults", "defender": "Microsoft-Defender-for-Cloud", "sentinel": "Azure-Sentinel",
    "conditional-access": "Conditional-Access", "managed-identity": "Entra-Managed-Identities", "users": "Users",
    "groups": "Groups", "enterprise-apps": "Enterprise-Applications", "app-registrations": "App-Registrations",
    "pim": "Entra-Privleged-Identity-Management", "verified-id": "Entra-Verified-ID", "mfa": "Multi-Factor-Authentication",
    "identity-protection": "Entra-ID-Protection", "identity-governance": "Identity-Governance",
    "info-protection": "Azure-Information-Protection", "security": "Security", "entra-connect": "Entra-Connect",
    "external-id": "External-Identities", "private-access": "Entra-Private-Access",
    # network
    "vnet": "Virtual-Networks", "private-link": "Private-Link", "private-endpoint": "Private-Endpoints",
    "app-gateway": "Application-Gateways", "front-door": "Front-Door-and-CDN-Profiles", "firewall": "Firewalls",
    "firewall-policy": "Azure-Firewall-Policy", "traffic-manager": "Traffic-Manager-Profiles",
    "load-balancer": "Load-Balancers", "dns": "DNS-Zones", "dns-resolver": "DNS-Private-Resolver",
    "vpn-gateway": "Virtual-Network-Gateways", "expressroute": "ExpressRoute-Circuits", "nsg": "Network-Security-Groups",
    "subnet": "Subnet", "bastion": "Bastions", "waf": "Web-Application-Firewall-Policies(WAF)",
    "nsp": "Network-Security-Perimeters", "ddos": "DDoS-Protection-Plans", "route-table": "Route-Tables",
    "vwan": "Virtual-WANs", "public-ip": "Public-IP-Addresses", "cdn": "CDN-Profiles",
    # compute / app
    "functions": "Function-Apps", "app-service": "App-Services", "container-apps": "Container-Apps-Environments",
    "acr": "Container-Registries", "aks": "Kubernetes-Services", "aci": "Container-Instances", "vm": "Virtual-Machine",
    "vmss": "VM-Scale-Sets", "static-web-apps": "Static-Apps", "apim": "API-Management-Services",
    "logic-apps": "Logic-Apps", "api-connections": "API-Connections", "power-platform": "Power-Platform",
    "container-app": "Worker-Container-App", "batch": "Batch-Accounts",
    # management / governance / devops
    "monitor": "Monitor", "app-insights": "Application-Insights", "log-analytics": "Log-Analytics-Workspaces",
    "alerts": "Alerts", "metrics": "Metrics", "diagnostics": "Diagnostics-Settings", "activity-log": "Activity-Log",
    "policy": "Policy", "cost-management": "Cost-Management-and-Billing", "advisor": "Advisor",
    "service-health": "Service-Health", "compliance": "Compliance", "workbooks": "Azure-Workbooks",
    "resource-group": "Resource-Groups", "subscription": "Subscriptions", "management-group": "Management-Groups",
    "reservations": "Reservations", "quotas": "Azure-Quotas", "landing-zone": "Landing-Zone", "arc": "Azure-Arc",
    "blueprints": "Blueprints", "backup": "Azure-Backup-Center", "recovery-vault": "Recovery-Services-Vaults",
    "chaos": "Azure-Chaos-Studio", "grafana": "Azure-Managed-Grafana", "load-testing": "Azure-Load-Testing",
    "devops": "Azure-DevOps", "automation": "Automation-Accounts", "template-specs": "Template-Specs",
    "dashboard": "Dashboard", "deployment-environments": "Azure-Deployment-Environments", "dev-box": "Microsoft-Dev-Box",
    # general
    "learn": "Learn", "toolbox-icon": "Toolbox", "search": "Search", "workflow": "Workflow", "gear": "Gear",
    "code": "Code", "tag": "Tag", "folder": "Folder-Blank", "cubes": "Cubes", "marketplace": "Marketplace",
    "preview-features": "Preview-Features", "regions": "Region-Management", "browser": "Browser", "files": "Files",
    "file": "File", "image": "Image", "versions": "Versions", "builds": "Builds", "bug": "Bug", "branch": "Branch",
    "commit": "Commit", "globe": "Globe-Success", "all-resources": "All-Resources", "scheduler": "Scheduler",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True, help="folder that contains the unzipped icon categories")
    args = ap.parse_args()
    pack = Path(args.pack)
    index: dict[str, Path] = {}
    for svg in pack.rglob("*.svg"):
        m = re.match(r"^\d+-icon-service-(.+)\.svg$", svg.name)
        if m:
            index.setdefault(m.group(1).strip(), svg)
    DEST.mkdir(parents=True, exist_ok=True)
    missing = []
    for slug, name in WANTED.items():
        src = index.get(name)
        if not src:
            missing.append(f"{slug} ({name})")
            continue
        shutil.copyfile(src, DEST / f"{slug}.svg")
    print(f"copied {len(WANTED) - len(missing)} icons -> {DEST}")
    if missing:
        print("missing:", ", ".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
