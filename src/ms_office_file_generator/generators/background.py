"""Slide background colour policy for generate mode.

Resolves the per-slide background colour from a mode (``none`` / ``theme`` /
``random``) or an explicit hex colour. Content slide builders consult this; the
divider slide keeps its own dark background regardless.
"""

from __future__ import annotations

import random
from enum import Enum

from pptx.dml.color import RGBColor

from ms_office_file_generator.generators.theme import Theme


class BackgroundMode(Enum):
    NONE = "none"  # leave the template default (white)
    THEME = "theme"  # one consistent themed tint on every slide
    RANDOM = "random"  # a different themed tint per slide


class Background:
    """Decides the background colour for each content slide."""

    def __init__(
        self,
        theme: Theme,
        *,
        mode: BackgroundMode = BackgroundMode.NONE,
        explicit: RGBColor | None = None,
    ) -> None:
        self._theme = theme
        self._mode = mode
        self._explicit = explicit

    def color_for(self, rng: random.Random) -> RGBColor | None:
        """Return the colour for the next slide, or None to leave the default."""
        if self._explicit is not None:
            return self._explicit
        if self._mode is BackgroundMode.THEME:
            return self._theme.slide_tint
        if self._mode is BackgroundMode.RANDOM:
            return rng.choice(self._theme.random_tints)
        return None


def parse_hex(value: str) -> RGBColor:
    """Parse a ``RRGGBB`` (or ``#RRGGBB``) hex string into an RGBColor."""
    cleaned = value.lstrip("#").strip()
    if len(cleaned) != 6:
        raise ValueError(
            f"Invalid background colour '{value}'. Use a 6-digit hex like EAF2F8."
        )
    try:
        return RGBColor.from_string(cleaned.upper())
    except ValueError as exc:
        raise ValueError(
            f"Invalid background colour '{value}'. Use a 6-digit hex like EAF2F8."
        ) from exc
