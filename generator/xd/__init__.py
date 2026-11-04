"""xd - a tiny Python toolkit that writes hand-drawn Excalidraw scenes.

Typical diagram module (generator/diagrams/<id>.py):

    from generator.xd import *

    META = dict(id="resource-model", title="Foundry resource model", section="1", order=3,
                description="One-line description for the gallery.")

    def build(cv: Canvas) -> None:
        right, bottom = title_block(cv, 0, 0, "Microsoft Foundry", "Resource model")
        card = Card(420, "Foundry resource", ["bullet", "  sub-bullet", "! warning"], theme="blue").place(cv, 0, 120)
        ...
"""
from .blocks import (CHECK, CROSS, DASH, PARTIAL, Bubble, Card, Chip, ChipFlow, Note, Table, col, draw_badge,
                     footer, grid, learn, legend, row, section_header, short_url, sources, title_block)
from .canvas import Canvas, El, Panel, Rect2
from .flows import Box, Sequence, arrow, brace, connect, elbow_points, hbrace, line_between, numbered, timeline
from .icons import available as available_icons, place_icon
from .metrics import CODE, HAND, MONO, text_size, wrap_text
from .palette import INK, LINK, MUTED, THEMES, theme

__all__ = [n for n in dir() if not n.startswith("_")]
