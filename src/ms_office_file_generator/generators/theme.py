"""Visual theme: colours, fonts, and gradient stops for designed slides.

python-pptx cannot author a real PowerPoint theme (slide-master backgrounds,
SmartArt) from scratch, so when no themed template is supplied the generator
falls back to this in-code palette to give slides a consistent, designed look:
themed fonts, gradient list items, coloured panels, and an accented background.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor


def _rgb(hex_value: int) -> RGBColor:
    return RGBColor((hex_value >> 16) & 0xFF, (hex_value >> 8) & 0xFF, hex_value & 0xFF)


@dataclass(frozen=True)
class Theme:
    """A palette + typography used to style generated slides."""

    name: str
    background: RGBColor
    divider_background: RGBColor
    primary: RGBColor
    accent: RGBColor
    gradient_start: RGBColor
    gradient_end: RGBColor
    heading_color: RGBColor
    body_color: RGBColor
    on_fill_color: RGBColor
    title_font: str = "Calibri Light"
    body_font: str = "Calibri"
    #: Consistent themed slide tint (light, so text stays readable).
    slide_tint: RGBColor = _rgb(0xEAF2F8)
    #: Curated soft tints used when backgrounds are randomised per slide.
    random_tints: tuple[RGBColor, ...] = (
        _rgb(0xEAF2F8),  # light blue
        _rgb(0xE8F6F1),  # light teal
        _rgb(0xF4F6F7),  # light grey
        _rgb(0xFEF9E7),  # light cream
        _rgb(0xF5EEF8),  # light lavender
    )


OCEAN = Theme(
    name="ocean",
    background=_rgb(0xFFFFFF),
    divider_background=_rgb(0x2B3A42),
    primary=_rgb(0x2E86C1),
    accent=_rgb(0x2EB88A),
    gradient_start=_rgb(0x3C78C8),
    gradient_end=_rgb(0x2EB88A),
    heading_color=_rgb(0x2E86C1),
    body_color=_rgb(0x333333),
    on_fill_color=_rgb(0xFFFFFF),
)

DEFAULT_THEME = OCEAN
