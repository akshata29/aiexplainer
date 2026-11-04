"""Fallback citation panel: if a canvas has no 'Sources ...' panel, build one from its own clickable links.

Every card/table/note that cites Microsoft Learn already carries a `link`; this collects the distinct URLs (with the
text of the element that carries the link as its label) so no canvas ships without a complete, accurate source list.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from .xd import Canvas, sources


def _label(el: dict, url: str) -> str:
    text = el.get("text", "") if el["type"] == "text" else ""
    text = re.sub(r"^\s*learn:\s*", "", text.replace("\n", " "), flags=re.I).strip()
    if not text or len(text) > 110 or text.lower().startswith("http"):
        tail = urlparse(url).path.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ")
        text = tail.capitalize() if tail else url
    return text


def has_sources_panel(cv: Canvas) -> bool:
    for e in cv._els:
        if e and e["type"] == "text" and e["fontSize"] >= 14:
            t = e["text"].strip().lower()
            if len(t) < 90 and t.startswith(("sources", "citations", "references")):
                return True
    return False


def add_auto_sources(cv: Canvas) -> int:
    """Append the panel when missing; returns the number of links listed (0 = nothing added)."""
    if has_sources_panel(cv):
        return 0
    seen: dict[str, str] = {}
    for e in cv._els:
        if not e:
            continue
        url = e.get("link")
        if not url or not str(url).startswith("http") or url in seen:
            continue
        seen[url] = _label(e, url)
    if not seen:
        return 0
    minx, _miny, maxx, maxy = cv.bounds()
    width = max(maxx - minx, 1800)
    cols = 3 if width >= 2600 else 2
    items = [(label, url) for url, label in sorted(seen.items())]
    sources(cv, minx, maxy + 70, items, w=width, cols=cols, title="Sources and further reading (links are clickable)")
    return len(items)
