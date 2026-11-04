"""Icons: real Azure architecture icons (SVG, embedded in the scene) with text-badge fallbacks.

Icon files live in generator/assets/icons/<name>.svg (curated from the official Azure Architecture icon set,
see tools/import_icons.py). Brand logos we don't ship (GitHub, Teams, ...) are drawn as coloured text badges.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import metrics
from .canvas import Canvas, El
from .palette import theme as get_theme

ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"

# name -> (badge text, theme) for things we draw as badges instead of shipping a logo
BADGES: dict[str, tuple[str, str]] = {
    "github": ("GH", "gray"), "teams": ("T", "violet"), "m365": ("M365", "blue"), "copilot": ("Cp", "indigo"),
    "sharepoint": ("SP", "teal"), "fabric": ("Fab", "teal"), "onelake": ("OL", "cyan"), "powerbi": ("BI", "yellow"),
    "bing": ("Bing", "cyan"), "mcp": ("MCP", "grape"), "a2a": ("A2A", "pink"), "otel": ("OTel", "orange"),
    "pyrit": ("PyRIT", "red"), "azd": ("azd", "blue"), "vscode": ("VS", "blue"), "python": ("Py", "yellow"),
    "dotnet": (".NET", "violet"), "js": ("JS", "yellow"), "java": ("Jv", "orange"), "langgraph": ("LG", "green"),
    "agent": ("Ag", "green"), "toolbox": ("TB", "orange"), "iq": ("IQ", "indigo"), "user": ("U", "gray"),
    "app": ("App", "indigo"), "api": ("API", "gray"), "sdk": ("SDK", "blue"), "rest": ("REST", "gray"),
    "claude": ("Cl", "orange"), "llama": ("Ll", "blue"), "mistral": ("Mi", "orange"), "deepseek": ("DS", "indigo"),
    "phi": ("Phi", "cyan"), "mai": ("MAI", "violet"), "gpt": ("GPT", "green"), "hf": ("HF", "yellow"),
    "okta": ("ID", "blue"), "oauth": ("OA", "gray"), "key": ("Key", "yellow"), "token": ("Tok", "orange"),
}


def available() -> list[str]:
    return sorted(p.stem for p in ICON_DIR.glob("*.svg")) + sorted(BADGES)


def place_icon(cv: Canvas, name: str, x: float, y: float, size: float = 36, *, link: Optional[str] = None) -> Optional[El]:
    """Draw icon `name` with its top-left at x,y. Falls back to a text badge (and warns) if unknown."""
    for ext, mime in (("svg", "image/svg+xml"), ("png", "image/png")):
        path = ICON_DIR / f"{name}.{ext}"
        if path.exists():
            fid = cv.add_file(path.read_bytes(), mime)
            return cv.image(x, y, size, size, fid, link=link)
    text, th_name = BADGES.get(name, (name[:3].upper(), "gray"))
    if name not in BADGES:
        cv.warn(f"icon {name!r} not found (using badge); available: {', '.join(available()[:12])} ...")
    th = get_theme(th_name)
    # largest label that fits the tile: <= 42% of the tile height and <= 86% of its width (never overflow, floor 7px)
    unit_w = metrics.text_size(text, 1.0)[0] or 1.0
    fs = max(7.0, min(size * 0.42, size * 0.86 / unit_w))
    tw, thh = metrics.text_size(text, fs)
    with cv.group():
        r = cv.rect(x, y, size, size, stroke=th.stroke, fill=th.fill, style="solid", sw=2, rough=0, link=link)
        cv.text(x + (size - tw) / 2, y + (size - thh) / 2, text, size=fs, color=th.deep)
    return r
