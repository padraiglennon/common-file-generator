"""Named complexity levels for generate mode.

Complexity controls **which designed slide types** may appear and **how often**.
Each level maps to a list of ``(slide_type, weight)`` pairs; the generator draws
each slide's type at random using those weights. Sparse "punctuation" slides such
as section dividers carry a low weight so they stay rare, while content slides
(bullets, charts, tables, image+text) dominate. ``minimal`` is plain bullets;
``maximum`` draws from the full pool.
"""

from __future__ import annotations

from enum import Enum


class Complexity(Enum):
    MINIMAL = "minimal"
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    MAXIMUM = "maximum"


# (slide_type, weight) per level. Weights are relative; dividers/video are kept
# rare on purpose so the deck doesn't fill up with sparse slides.
_POOLS: dict[Complexity, tuple[tuple[str, int], ...]] = {
    Complexity.MINIMAL: (("bullets", 1),),
    Complexity.SIMPLE: (
        ("bullets", 5),
        ("chevron", 3),
    ),
    Complexity.STANDARD: (
        ("bullets", 5),
        ("chevron", 4),
        ("image_text", 3),
        ("image_bullets", 4),
        ("chart", 3),
    ),
    Complexity.COMPLEX: (
        ("bullets", 5),
        ("chevron", 4),
        ("image_text", 3),
        ("image_bullets", 4),
        ("chart", 3),
        ("table", 3),
        ("divider", 1),
    ),
    Complexity.MAXIMUM: (
        ("bullets", 5),
        ("chevron", 4),
        ("image_text", 3),
        ("image_bullets", 4),
        ("chart", 3),
        ("table", 3),
        ("video", 2),
        ("divider", 1),
    ),
}


def slide_pool(level: Complexity) -> tuple[tuple[str, int], ...]:
    """Return the weighted ``(slide_type, weight)`` pool allowed at ``level``."""
    return _POOLS[level]


# Word content blocks per level. A section always opens with a heading and a
# paragraph; these are the *extra* blocks that may follow, drawn by weight.
# Richer levels are supersets, so a document always has variety.
_DOC_BLOCKS: dict[Complexity, tuple[tuple[str, int], ...]] = {
    Complexity.MINIMAL: (("paragraph", 1),),
    Complexity.SIMPLE: (
        ("paragraph", 4),
        ("bullets", 3),
    ),
    Complexity.STANDARD: (
        ("paragraph", 4),
        ("bullets", 3),
        ("numbered", 3),
        ("table", 2),
    ),
    Complexity.COMPLEX: (
        ("paragraph", 4),
        ("bullets", 3),
        ("numbered", 3),
        ("table", 3),
        ("image", 2),
        ("quote", 2),
    ),
    Complexity.MAXIMUM: (
        ("paragraph", 4),
        ("bullets", 3),
        ("numbered", 3),
        ("table", 3),
        ("image", 3),
        ("quote", 2),
        ("page_break", 1),
    ),
}


def doc_block_pool(level: Complexity) -> tuple[tuple[str, int], ...]:
    """Return the weighted ``(block_type, weight)`` pool for Word sections."""
    return _DOC_BLOCKS[level]
