"""Base injector workflow and the public ``generate`` entry point.

The base :class:`Injector` owns the format-agnostic workflow; concrete
subclasses implement only the per-format mechanics (loading, saving, and the
three injection steps). ``generate`` dispatches to the right injector by file
extension so new formats plug in without changing callers.
"""

from __future__ import annotations

import abc
from pathlib import Path

from common_file_generator.core.config import Config, load_config
from common_file_generator.core.report import Report


class Injector(abc.ABC):
    """Template-driven data injector for one Office format.

    Subclasses must not generate layout - only populate elements that already
    exist in the loaded template document.
    """

    #: File extensions this injector handles, e.g. ``{".pptx"}``.
    extensions: frozenset[str] = frozenset()

    def __init__(self, template_path: str | Path) -> None:
        self.template_path = Path(template_path)
        if not self.template_path.is_file():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        self.report = Report()
        self._document = self._load(self.template_path)

    def inject(self, config: Config) -> None:
        """Run all injection steps, recording issues rather than raising."""
        self._inject_text(config)
        self._inject_tables(config)
        self._inject_media(config)

    def save(self, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self._save(out_path)
        return out_path

    # --- per-format hooks ------------------------------------------------

    @abc.abstractmethod
    def _load(self, path: Path) -> object:
        """Open the template and return the underlying document object."""

    @abc.abstractmethod
    def _save(self, path: Path) -> None:
        """Write the populated document to ``path``."""

    @abc.abstractmethod
    def _inject_text(self, config: Config) -> None:
        """Replace ``{{token}}`` placeholders with text values."""

    @abc.abstractmethod
    def _inject_tables(self, config: Config) -> None:
        """Populate named tables with rows."""

    @abc.abstractmethod
    def _inject_media(self, config: Config) -> None:
        """Insert media into named picture-placeholder shapes."""


def _injector_registry() -> dict[str, type[Injector]]:
    # Imported lazily to avoid importing every Office library up front.
    from common_file_generator.injectors.docx import DocxInjector
    from common_file_generator.injectors.pptx import PptxInjector
    from common_file_generator.injectors.xlsx import XlsxInjector

    registry: dict[str, type[Injector]] = {}
    for cls in (PptxInjector, DocxInjector, XlsxInjector):
        for ext in cls.extensions:
            registry[ext] = cls
    return registry


def injector_for(template_path: str | Path) -> Injector:
    """Return the injector that handles ``template_path`` by its extension."""
    ext = Path(template_path).suffix.lower()
    registry = _injector_registry()
    cls = registry.get(ext)
    if cls is None:
        supported = ", ".join(sorted(registry))
        raise ValueError(
            f"Unsupported template type '{ext}'. Supported types: {supported}."
        )
    return cls(template_path)


def generate(
    template: str | Path,
    config: str | Path | Config,
    out: str | Path,
    *,
    report_path: str | Path | None = None,
) -> Report:
    """Inject ``config`` data into ``template`` and write the result to ``out``.

    Returns the :class:`Report` of any issues found. A plain-English copy is
    written next to ``out`` (or to ``report_path`` if given).
    """
    cfg = config if isinstance(config, Config) else load_config(config)
    injector = injector_for(template)
    injector.inject(cfg)
    out_path = injector.save(out)

    resolved_report = (
        Path(report_path)
        if report_path is not None
        else out_path.with_name(f"{out_path.stem}.report.txt")
    )
    injector.report.write(resolved_report)
    return injector.report
