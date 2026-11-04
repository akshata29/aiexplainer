# Diagram authoring guide (xd kit)

Every canvas is a Python module in `generator/diagrams/` that draws hand-drawn Excalidraw shapes with the `xd`
kit. `python -m generator.build` turns modules into `diagrams/<id>.excalidraw` (the deliverable; open in
excalidraw.com or the VS Code Excalidraw extension) and `python -m generator.preview <id>` renders PNGs for visual QA.

```python
from generator.xd import *

META = dict(id="hosted-agents", title="Hosted agents", section="2", group="Agent Service", order=23,
            description="One-line gallery blurb.", tags=["agents", "hosted"])

def build(cv: Canvas) -> None:
    right, bottom = title_block(cv, 0, 0, "Hosted agents", "Your code, Foundry's runtime", icon="foundry", w=2600)
    a = Card(420, "Runtime contract", ["Responses protocol", "  sub-bullet", "! warning"], theme="green",
             badge="preview", icon="container-apps", src=[("Hosted agents", learn("agents/concepts/hosted-agents"))])
    a.place(cv, 0, bottom + 50)
    ...
    sources(cv, 0, y, [("Label", learn("path")), ...], w=2600, cols=3)      # clickable citations
```

Workflow: write module -> `python -m generator.build <id>` (fast; fix every warning) -> `python tools/qa_check.py <id>` (static
layout check) -> `python -m generator.preview <id>` and **view** `diagrams/previews/work/<id>.png` (overview) -> inspect problem
areas with `python -m generator.preview <id> --tiles r2c1,r3c2` (full-resolution tiles; a few at a time) -> fix -> repeat.
Renders are serialized machine-wide (one at a time), so keep them to a handful per canvas.
The footer ("Updated <date>", disclaimer) is added automatically by the build.

## Content rules (non-negotiable)
1. **Accurate or absent.** Every statement must come from Microsoft Learn (or a cited video/blog) that you actually read.
   Never invent names, limits, prices, roles, API routes. Mark preview features with `badge="preview"`; if unsure about
   status, say "check docs" rather than guessing. If a source says something is *not* documented, say so.
2. **Cite.** Each card that summarises a page carries `src=[("Page title", learn("path"))]` (rendered as a clickable
   "Learn: ..." line) and every canvas ends with `sources(...)` listing 6-14 canonical URLs. Use `learn("agents/overview")`
   for `/azure/foundry/` pages and `learn("azure/search/agentic-retrieval-overview", base="")` for other Learn areas.
3. **Dense but legible.** The user wants *all the details*. Prefer many small, well-grouped cards/tables over a few
   walls of text: <= 8 bullets per card, ~<= 110 characters per bullet. Use tables for comparisons, sequences for
   auth/request flows, panels to group, notes for gotchas.
4. **Terminology:** Microsoft Foundry (not Azure AI Foundry), Foundry Tools (not Azure AI Services), Foundry User /
   Project Manager / Account Owner / Owner roles (formerly Azure AI ...), Responses API + conversations/items/agent
   versions (not Assistants threads/runs). "Foundry (classic)" = the old portal and hub-based projects.

## Visual conventions
* Canvas: x starts at 0; title block at (0,0); first content ~ y=170-200; typical width 2400-3300 px; 40-60 px gaps.
  Left-align everything on a grid (columns of 380-520 px cards). Group related items in `cv.panel(...)`.
* **Colour semantics (keep consistent across all canvases):**
  models/deployments = `blue` · agents/Agent Service = `green` · tools/toolbox/MCP = `orange` ·
  knowledge/IQ/search/memory = `teal` · observability/evaluation/tracing = `violet` · guardrails/safety = `pink` ·
  identity/security/RBAC = `red` · networking = `indigo` · governance/control plane/policy = `grape` ·
  cost/capacity/quota = `yellow` · data/storage/Cosmos = `cyan` · neutral/context = `gray`.
* Text sizes: canvas title 48, section header 30, panel title 24-30, card title 20, body 15-16, table 14-15, citations 12.
  Don't go below 12. Only Excalifont is used (hand-drawn). **It has no arrows/check/inequality glyphs**: write `->`, `>=`
  or use `connect(...)`, `CHECK`/`CROSS`/`PARTIAL` table marks. The kit warns on unsupported glyphs.
* Arrows: `connect(cv, a, b, label=..., num=..., dash="dashed", route="elbow")` between placed blocks; `arrow(cv, [pts])` for
  free arrows. Solid = synchronous/primary flow, dashed = async/optional/return, dotted = relationship.
  Leave >= 90 px between blocks that need a labelled arrow. Number steps with `num=` and repeat the numbers in a legend/steps card.
* Status badges: `badge="ga" | "preview" | "retiring" | "new" | "classic"` on cards.
* Icons: `icon="foundry"` etc. (`available_icons()` lists them: Azure architecture icons + text badges such as `mcp`, `a2a`,
  `agent`, `toolbox`, `github`). Unknown names fall back to a text badge and warn.

## API cheat sheet (all in `generator.xd`)
| Thing | Use |
|---|---|
| `Canvas cv` | `cv.rect/ellipse/diamond/text/line/poly/image`, `cv.group()`, `cv.panel(x, y, title=, sub=, theme=, style="dotted"/"dashed"/"solid", fill="none"/"soft"/"hatch"/"solid", pad=)` (auto-sizing; place children at `p.ix`, `p.iy`; after the block `p.x/y/w/h/right/bottom` are valid) |
| `title_block(cv,x,y,title,subtitle,icon=,w=)` | big title + logo + rule -> returns `(right, bottom)` |
| `section_header(cv,x,y,text,sub=)` | underlined heading -> `(right, bottom)` |
| `Card(w, title, body, theme=, subtitle=, badge=, icon=, src=, fill="hatch"/"soft"/"solid"/"cross"/"none", dash=, align=)` | measure on construct; `.place(cv,x,y,h=None)`; has `.x .y .w .h .right .bottom .pt(side)` |
| body markup | `"text"` bullet · `"  text"` sub-bullet · `"# text"` sub-heading · `"= text"` paragraph · `"! text"` warning (red) · `"+ text"` positive (green) |
| `Table(cols, rows, w=, theme=, size=, title=, first_col_theme=)` | cols `["A", ("B", 200)]`; cells `str`, `(text, theme)` or dict; `CHECK/CROSS/PARTIAL/DASH` draw vector marks |
| `Chip(label, theme=, icon=)`, `ChipFlow(items, w, theme=)` | pills / wrapped pill lists |
| `Note(w, text, kind="info"/"tip"/"warn"/"gotcha"/"preview"/"quote"/"key", title=, src=)` | callout |
| `Bubble(w, text, theme=, tail="left")` | speech bubble (sample prompts / quotes) |
| `Box(w, label, h=, theme=, sub=, icon=, icon_pos="top"/"left", shape="rect"/"ellipse"/"diamond", fill=, dash=)` | centred label shape for architecture/flow nodes |
| `connect(cv, a, b, a_side=, b_side=, label=, num=, dash=, route="straight"/"elbow"/"curve", via=[pts], start_head=, end_head=, color=, sw=)` | arrow between any placed blocks (auto side choice) |
| `arrow(cv, pts, ...)`, `line_between(...)`, `numbered(cv,cx,cy,n,theme=)`, `brace(cv,x,y1,y2,side=)`, `hbrace(...)` | free connectors & markers |
| `Sequence(cv,x,y,[(label,theme,icon),...],spacing=)` | `.msg(src,dst,text,num=,dash=,note=)`, `.note(a,b,text,kind=)`, `.end()` -> bottom y; actors are indexes |
| `timeline(cv,x,y,w,[(when,title,detail),...])` | horizontal timeline |
| `row(cv,x,y,blocks,gap=,equalize=True)`, `col(...)`, `grid(cv,x,y,blocks,cols)` | place blocks; return `(right, bottom)` |
| `legend(cv,x,y,[(label,theme),...])` | colour key |
| `sources(cv,x,y,[(label,url),...],w=,cols=)` | clickable citation panel |
| `learn(path, base="azure/foundry")` | canonical Learn URL |
| `text_size/wrap_text` | measure text with the exact Excalifont metrics (use to size custom shapes) |

`build` warns about overlapping blocks (`OVERLAP ...`) and unsupported glyphs - fix them all.

## Quality checklist before you call a canvas done
- [ ] Overview PNG reads as a clear story left-to-right / top-to-bottom; tiles show no clipped, overlapping or tiny text.
- [ ] `python -m generator.build <id>` prints **no** `!` warnings.
- [ ] Every card/table summarising a doc page has a `Learn:` citation; `sources(...)` block at the bottom with clickable links.
- [ ] Preview/GA and renamed-term accuracy; no invented facts; numbers only where documented.
- [ ] Colour semantics above respected; icons meaningful; consistent card widths on a grid.
- [ ] 100-600 elements is typical; if > 900, split into two canvases.

## Do / don't
* Do keep your own helper functions inside your module. **Don't edit `generator/xd/`, `tools/`, `src/` or other people's diagrams.**
* Don't run `python -m generator.build` without ids (it rewrites the manifest); use `python -m generator.build <id>` or `generator.preview <id>`.
* If the kit lacks something, work around it in your module and mention it in your final report.
