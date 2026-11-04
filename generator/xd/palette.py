"""Colour themes in the Excalidraw "open colour" palette so output looks native when opened in Excalidraw."""
from __future__ import annotations

from dataclasses import dataclass

INK = "#1e1e1e"
MUTED = "#495057"
LINK = "#1971c2"
WHITE = "#ffffff"


@dataclass(frozen=True)
class Theme:
    name: str
    stroke: str   # strong border / heading colour
    fill: str     # pastel fill (hatch lines or solid)
    soft: str     # very light tint (table zebra, chip backgrounds)
    deep: str     # dark text colour that reads well on `fill`


THEMES: dict[str, Theme] = {t.name: t for t in [
    Theme("red",    "#e03131", "#ffc9c9", "#fff5f5", "#c92a2a"),
    Theme("pink",   "#c2255c", "#fcc2d7", "#fff0f6", "#a61e4d"),
    Theme("grape",  "#9c36b5", "#eebefa", "#f8f0fc", "#862e9c"),
    Theme("violet", "#6741d9", "#d0bfff", "#f3f0ff", "#5f3dc4"),
    Theme("indigo", "#3b5bdb", "#bac8ff", "#edf2ff", "#364fc7"),
    Theme("blue",   "#1971c2", "#a5d8ff", "#e7f5ff", "#1864ab"),
    Theme("cyan",   "#0c8599", "#99e9f2", "#e3fafc", "#0b7285"),
    Theme("teal",   "#099268", "#96f2d7", "#e6fcf5", "#087f5b"),
    Theme("green",  "#2f9e44", "#b2f2bb", "#ebfbee", "#2b8a3e"),
    Theme("lime",   "#66a80f", "#d8f5a2", "#f4fce3", "#5c940d"),
    Theme("yellow", "#f08c00", "#ffec99", "#fff9db", "#e67700"),
    Theme("orange", "#e8590c", "#ffd8a8", "#fff4e6", "#d9480f"),
    Theme("gray",   "#495057", "#e9ecef", "#f8f9fa", "#343a40"),
    Theme("ink",    "#1e1e1e", "#ced4da", "#f1f3f5", "#1e1e1e"),
]}

# aliases that read naturally in diagram code
THEMES["purple"] = THEMES["violet"]
THEMES["amber"] = THEMES["yellow"]
THEMES["grey"] = THEMES["gray"]
THEMES["azure"] = THEMES["blue"]

# badge/status colours
STATUS = {
    "ga": ("green", "GA"),
    "preview": ("orange", "Preview"),
    "retiring": ("red", "Retiring"),
    "new": ("violet", "New"),
    "classic": ("gray", "Classic"),
}


def theme(name: str | Theme) -> Theme:
    if isinstance(name, Theme):
        return name
    try:
        return THEMES[name]
    except KeyError as exc:
        raise KeyError(f"unknown theme {name!r}; choose from {sorted(THEMES)}") from exc
