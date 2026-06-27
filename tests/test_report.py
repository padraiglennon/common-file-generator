"""Tests for the plain-English report."""

from __future__ import annotations

from pathlib import Path

from common_file_generator.core import Report, Severity


def test_clean_report_has_no_problems() -> None:
    report = Report()
    assert not report.has_problems
    assert "successfully" in report.render()


def test_info_is_not_a_problem() -> None:
    report = Report()
    report.info("x", "fyi")
    assert not report.has_problems


def test_warning_and_error_are_problems() -> None:
    report = Report()
    report.warning("tables.T", "too many rows")
    report.error("media.L", "file missing")
    assert report.has_problems
    text = report.render()
    assert "Errors: 1" in text
    assert "Warnings: 1" in text
    assert "too many rows" in text
    assert "file missing" in text


def test_write_creates_file(tmp_path: Path) -> None:
    report = Report()
    report.warning("a", "b")
    out = report.write(tmp_path / "r.txt")
    assert out.read_text(encoding="utf-8") == report.render()


def test_severity_values() -> None:
    assert {s.value for s in Severity} == {"info", "warning", "error"}
