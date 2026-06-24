"""Collect injection issues and render a plain-English report.

The reporter is what makes failures self-serviceable: every mismatch between
the data and the template (missing shape, too many rows, absent media file) is
recorded as a human-readable :class:`Issue` rather than raising. The run still
produces a best-effort file, and a summary report tells the user what to fix.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger("ms_office_file_generator")


class Severity(Enum):
    """How serious an issue is. Nothing here aborts the run."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Issue:
    """A single human-readable problem found during injection."""

    severity: Severity
    where: str
    message: str

    def as_line(self) -> str:
        return f"[{self.severity.value.upper()}] {self.where}: {self.message}"


@dataclass
class Report:
    """Accumulates issues across an injection run."""

    issues: list[Issue] = field(default_factory=list)

    def add(self, severity: Severity, where: str, message: str) -> None:
        issue = Issue(severity=severity, where=where, message=message)
        self.issues.append(issue)
        logger.log(_LOG_LEVELS[severity], "%s: %s", where, message)

    def info(self, where: str, message: str) -> None:
        self.add(Severity.INFO, where, message)

    def warning(self, where: str, message: str) -> None:
        self.add(Severity.WARNING, where, message)

    def error(self, where: str, message: str) -> None:
        self.add(Severity.ERROR, where, message)

    @property
    def has_problems(self) -> bool:
        return any(i.severity is not Severity.INFO for i in self.issues)

    def render(self) -> str:
        """Render a plain-English summary suitable for a non-technical reader."""
        if not self.issues:
            return "All data was injected successfully. No issues found.\n"

        warnings = sum(1 for i in self.issues if i.severity is Severity.WARNING)
        errors = sum(1 for i in self.issues if i.severity is Severity.ERROR)
        lines = [
            "Injection report",
            "================",
            f"Errors: {errors}    Warnings: {warnings}",
            "",
            "The file was still created, but please review the items below:",
            "",
        ]
        lines.extend(f"  - {issue.as_line()}" for issue in self.issues)
        lines.append("")
        return "\n".join(lines)

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.render(), encoding="utf-8")
        return path


_LOG_LEVELS = {
    Severity.INFO: logging.INFO,
    Severity.WARNING: logging.WARNING,
    Severity.ERROR: logging.ERROR,
}
