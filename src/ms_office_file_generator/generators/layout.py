"""Geometry helper for placing generated elements.

A :class:`Box` is a rectangle in EMU, ready to pass straight to python-pptx
``add_*`` calls. Designed slide types compute their own boxes; keeping this type
shared avoids passing four loose Length arguments everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.util import Emu


@dataclass(frozen=True)
class Box:
    """A rectangle in EMU (left, top, width, height)."""

    left: Emu
    top: Emu
    width: Emu
    height: Emu
