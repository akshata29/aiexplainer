"""Regenerate the generated blocks of README.md: hero, stats, screenshot gallery, canvas index, topic index, reading paths.

Inputs: diagrams/manifest.json, the .excalidraw files (counts) and docs/featured.json (screenshot crops, captions,
section highlights, reading paths). The hand-written parts of README.md are left alone.

    python tools/gen_readme.py                                            # links open the .excalidraw files
    python tools/gen_readme.py --site https://<user>.github.io/<repo>/    # links open the hosted viewer instead

The screenshots themselves are rendered with:  node tools/render.mjs --shots
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "diagrams" / "manifest.json").read_text(encoding="utf-8"))
featured = json.loads((ROOT / "docs" / "featured.json").read_text(encoding="utf-8"))
sections = manifest["sections"]
by_id = {d["id"]: d for d in manifest["diagrams"]}

site = ""
if "--site" in sys.argv:
    site = sys.argv[sys.argv.index("--site") + 1].rstrip("/") + "/"


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def view(canvas_id: str) -> str:
    return f"{site}#/d/{canvas_id}" if site else f"diagrams/{by_id[canvas_id]['file']}"


def canvas(canvas_id: str) -> dict:
    if canvas_id not in by_id:
        raise SystemExit(f"docs/featured.json references unknown canvas id: {canvas_id}")
    return by_id[canvas_id]


# ----------------------------------------------------------------------------------------------- scene statistics
stats: dict[str, dict] = {}
urls: set[str] = set()
file_ids: set[str] = set()
for d in manifest["diagrams"]:
    path = ROOT / "diagrams" / d["file"]
    scene = json.loads(path.read_text(encoding="utf-8"))
    els = [e for e in scene["elements"] if not e.get("isDeleted")]
    x0 = min(e["x"] for e in els)
    y0 = min(e["y"] for e in els)
    stats[d["id"]] = {
        "w": int(max(e["x"] + e.get("width", 0) for e in els) - x0),
        "h": int(max(e["y"] + e.get("height", 0) for e in els) - y0),
        "elements": len(els),
        "texts": sum(1 for e in els if e["type"] == "text"),
        "images": sum(1 for e in els if e["type"] == "image"),
        "links": sum(1 for e in els if e.get("link")),
        "bytes": path.stat().st_size,
    }
    for e in els:
        if e.get("link") and re.match(r"https?://", e["link"]):
            urls.add(e["link"])
        if e["type"] == "image" and e.get("fileId"):
            file_ids.add(e["fileId"])


def total(key: str) -> int:
    return sum(s[key] for s in stats.values())


# ----------------------------------------------------------------------------------------------------------- blocks
def hero_block() -> str:
    hero = next(s for s in featured["shots"] if s.get("hero"))
    cid = hero["id"]
    st = stats[cid]
    img = f"![{hero['title']}](docs/screenshots/{hero['name']}.{featured.get('format', 'webp')})"
    if site:
        img = f"[{img}]({view(cid)})"
    hint = "Click the image to open the canvas." if site else "Click the image for full resolution."
    return (f"{img}\n\n"
            f"<sub>Excerpt of [`{cid}`]({view(cid)}) ({st['w']:,} x {st['h']:,} px, {st['elements']:,} elements): "
            f"{hero['caption']} {hint}</sub>")


def stats_block() -> str:
    widths = [s["w"] for s in stats.values()]
    heights = [s["h"] for s in stats.values()]
    mb = total("bytes") / 1024 / 1024
    rows = [
        ("Canvases", f"**{len(stats)}** in {len(sections)} sections; larger topics are split into a main canvas plus `-part-2`"),
        ("Drawn elements", f"**{total('elements'):,}** hand-drawn elements: {total('texts'):,} text, {total('images'):,} embedded Azure icons"),
        ("Citations", f"**{total('links'):,}** clickable Microsoft Learn links ({len(urls):,} unique URLs, verified with `tools/check_links.py`)"),
        ("Canvas size", f"{min(widths):,} - {max(widths):,} px wide, {min(heights):,} - {max(heights):,} px tall; {mb:.0f} MB of compact JSON in total"),
        ("Content date", f"Facts are current as of **{featured['asOf']}** (stamped on each canvas); preview features are marked"),
    ]
    out = ["| | |", "|---|---|"] + [f"| **{k}** | {v} |" for k, v in rows]
    out += ["", "| # | Section | Canvases | Scope |", "|---|---|---|---|"]
    for key, sec in sections.items():
        n = sum(1 for d in manifest["diagrams"] if d["section"] == key)
        out.append(f"| {key} | **{esc(sec['title'])}** | {n} | {esc(sec['blurb'])} |")
    return "\n".join(out)


def gallery_block() -> str:
    fmt = featured.get("format", "webp")
    out: list[str] = []
    for s in featured["shots"]:
        if s.get("hero") or s.get("gallery") is False:
            continue
        cid = s["id"]
        canvas(cid)
        st = stats[cid]
        out.append(f"### {s['title']}")
        out.append("")
        out.append(f"**{s['label']}** · excerpt of [`{cid}`]({view(cid)}) "
                   f"({st['w']:,} x {st['h']:,} px, {st['elements']:,} elements, {st['links']:,} Learn links)")
        out.append("")
        out.append(f"![{s['title']}](docs/screenshots/{s['name']}.{fmt})")
        out.append("")
        out.append(s["caption"])
        out.append("")
        out += [f"- {p}" for p in s.get("points", [])]
        rel = [r for r in s.get("related", []) if r != cid][:6]
        if rel:
            links = " · ".join(f"[{esc(canvas(r)['title'])}]({view(r)})" for r in rel)
            out += ["", f"<sub>**Same topic:** {links}</sub>"]
        out.append("")
    return "\n".join(out).rstrip()


def paths_block() -> str:
    out = ["| If you are... | Read in this order |", "|---|---|"]
    for p in featured["paths"]:
        chain = " → ".join(f"[{esc(label)}]({view(canvas(cid)['id'])})" for cid, label in p["ids"])
        out.append(f"| **{esc(p['who'])}** | {chain} |")
    return "\n".join(out)


def topics_block() -> str:
    out = ["| Topic | Canvases |", "|---|---|"]
    for t in featured["topics"]:
        links = " · ".join(f"[`{canvas(i)['id']}`]({view(i)})" for i in t["ids"])
        out.append(f"| {esc(t['topic'])} | {links} |")
    return "\n".join(out)


def index_block() -> str:
    out: list[str] = []
    for key, sec in sections.items():
        items = [d for d in manifest["diagrams"] if d["section"] == key]
        if not items:
            continue
        out.append("<details>")
        out.append(f"<summary><b>{key}. {html.escape(sec['title'])}</b> &nbsp;·&nbsp; {len(items)} canvases &nbsp;·&nbsp; "
                   f"<i>{html.escape(sec['blurb'])}</i></summary>")
        out.append("")
        for h in featured["sections"].get(key, {}).get("highlights", []):
            out.append(f"- {h}")
        out.append("")
        out.append("| Preview | Diagram | What it covers |")
        out.append("|---|---|---|")
        for d in items:
            thumb = f"diagrams/previews/{d['id']}.thumb.webp"
            link = view(d["id"])
            title = esc(d["title"]) + (f" <br/><sub>{esc(d['group'])}</sub>" if d.get("group") else "")
            out.append(f"| <a href=\"{link}\"><img src=\"{thumb}\" width=\"150\" alt=\"{html.escape(d['title'])}\"/></a> "
                       f"| [{title}]({link}) | {esc(d['description'])} |")
        out.append("")
        out.append("</details>")
        out.append("")
    return "\n".join(out).rstrip()


BLOCKS = {
    "HERO": hero_block,
    "STATS": stats_block,
    "GALLERY": gallery_block,
    "DIAGRAMS": index_block,
    "TOPICS": topics_block,
    "PATHS": paths_block,
}

readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
for name, fn in BLOCKS.items():
    pattern = re.compile(rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"README.md is missing the <!-- {name}:START --> / <!-- {name}:END --> markers")
    body = fn()
    text = pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text, count=1)
readme.write_text(text, encoding="utf-8")
print(f"README updated: {len(manifest['diagrams'])} canvases, {sum(1 for s in featured['shots'] if s.get('gallery') is not False)} screenshots")
