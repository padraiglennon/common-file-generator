"""Core engine: config loading, validation, reporting, and the base injector."""

from ms_office_file_generator.core.complexity import Complexity, slide_pool
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
    "generate",
    "generate_deck",
    "load_config",
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
