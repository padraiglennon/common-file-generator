"""Core engine: config loading, validation, reporting, and the base injector."""

from ms_office_file_generator.core.complexity import (
    Complexity,
    doc_block_pool,
    sheet_feature_pool,
    slide_pool,
)
from ms_office_file_generator.core.config import (
    Config,
    ConfigError,
    MediaSpec,
    TableSpec,
    load_config,
)
from ms_office_file_generator.core.injector import Injector, generate
from ms_office_file_generator.core.report import Issue, Report, Severity

__all__ = [
    "Complexity",
    "Config",
    "ConfigError",
    "Injector",
    "Issue",
    "MediaSpec",
    "Report",
    "Severity",
    "TableSpec",
    "doc_block_pool",
    "generate",
    "generate_deck",
    "generate_doc",
    "generate_sheet",
    "load_config",
    "sheet_feature_pool",
    "slide_pool",
]

DEFAULT_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def generate_deck(
    out: str,
    *,
    complexity: Complexity | str = Complexity.STANDARD,
    slides: int = 10,
    seed: int = 0,
    video_url: str = DEFAULT_VIDEO_URL,
    theme_path: str | None = None,
    background: str = "none",
    background_color: str | None = None,
) -> str:
    """Generate a complexity-driven PowerPoint deck and write it to ``out``.

    This is generate mode (build from scratch), distinct from :func:`generate`
    which injects into a Golden template. Kept here so a future UI can call it.

    ``theme_path`` may point at a designed ``.pptx`` whose master/layouts are used
    as the base; otherwise the in-code theme is applied. ``background`` is one of
    ``none`` / ``theme`` / ``random``; ``background_color`` is an explicit hex that
    overrides the mode with a single consistent colour.
    """
    from ms_office_file_generator.generators import PptxComplexityGenerator
    from ms_office_file_generator.generators.background import (
        Background,
        BackgroundMode,
        parse_hex,
    )
    from ms_office_file_generator.generators.theme import DEFAULT_THEME

    level = complexity if isinstance(complexity, Complexity) else Complexity(complexity)
    bg = Background(
        DEFAULT_THEME,
        mode=BackgroundMode(background),
        explicit=parse_hex(background_color) if background_color else None,
    )
    generator = PptxComplexityGenerator(
        level,
        slides=slides,
        seed=seed,
        video_url=video_url,
        theme_path=theme_path,
        background=bg,
    )
    return str(generator.save(out))


def generate_doc(
    out: str,
    *,
    complexity: Complexity | str = Complexity.STANDARD,
    sections: int = 5,
    seed: int = 0,
    blocks_per_section: int | None = None,
) -> str:
    """Generate a complexity-driven Word document and write it to ``out``.

    Generate mode for Word: builds a ``.docx`` from scratch (distinct from
    :func:`generate`, which injects into a template). Kept here so the CLI and a
    future UI reuse the same core. ``blocks_per_section`` overrides the
    per-complexity default density.
    """
    from ms_office_file_generator.generators import DocxComplexityGenerator

    level = complexity if isinstance(complexity, Complexity) else Complexity(complexity)
    generator = DocxComplexityGenerator(
        level,
        sections=sections,
        seed=seed,
        blocks_per_section=blocks_per_section,
    )
    return str(generator.save(out))


def generate_sheet(
    out: str,
    *,
    complexity: Complexity | str = Complexity.STANDARD,
    sheets: int = 3,
    seed: int = 0,
    rows: int | None = None,
    cols: int | None = None,
) -> str:
    """Generate a complexity-driven Excel workbook and write it to ``out``.

    Generate mode for Excel: builds an ``.xlsx`` from scratch (distinct from
    :func:`generate`, which injects into a template). Kept here so the CLI and a
    future UI reuse the same core. ``rows`` overrides the per-complexity table
    size; ``cols`` fixes the column count (default randomised per table).
    """
    from ms_office_file_generator.generators import XlsxComplexityGenerator

    level = complexity if isinstance(complexity, Complexity) else Complexity(complexity)
    generator = XlsxComplexityGenerator(
        level, sheets=sheets, seed=seed, rows=rows, cols=cols
    )
    return str(generator.save(out))
