"""Dev tool: compare kit text metrics against the real browser. Usage: python tools/check_metrics.py"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator.xd import metrics  # noqa: E402

SAMPLES = [
    "Declarative: instructions + model + tools",
    "Hosted by Foundry - no code or containers",
    "Frameworks: Agent Framework, LangGraph, Semantic Kernel",
    "Per-session isolation, scale to zero",
    "Microsoft Foundry", "Deployment types", "Global Standard", "Hourly reserved capacity",
    "POST /openai/v1/responses (Entra token)", "learn.microsoft.com/azure/foundry/what-is-foundry",
    "The quick brown fox jumps over the lazy dog 0123456789", "AIIIIii WWWWMMM mmmmm lllll",
    "Azure AI Search \u2022 Cosmos DB \u2022 Key Vault \u2013 RBAC", "Foundry resource (Microsoft.CognitiveServices/accounts)",
]
FAM = {5: "Excalifont", 8: "Comic Shanns"}
items = []
for fid, fam in FAM.items():
    for size in (12, 16, 20, 36):
        for s in SAMPLES:
            items.append({"text": s, "size": size, "family": fam, "fid": fid})
res = subprocess.run(["node", str(ROOT / "tools" / "measure.mjs")], input=json.dumps(items), text=True,
                     capture_output=True, cwd=ROOT)
if res.returncode:
    print(res.stderr)
    raise SystemExit(1)
widths = json.loads(res.stdout)
ratios = {5: [], 8: []}
worst = []
for it, bw in zip(items, widths):
    pw = metrics.line_width(it["text"], it["size"], it["fid"])
    r = bw / pw if pw else 1
    ratios[it["fid"]].append(r)
    worst.append((abs(r - 1), r, it["fid"], it["size"], it["text"][:45], round(pw, 1), round(bw, 1)))
for fid, rs in ratios.items():
    print(f"font {FAM[fid]:13s} browser/python ratio: min {min(rs):.4f} mean {sum(rs)/len(rs):.4f} max {max(rs):.4f}")
worst.sort(reverse=True)
print("largest deviations:")
for w in worst[:8]:
    print("  dev=%.3f ratio=%.4f font=%d size=%d %r py=%s browser=%s" % w)
