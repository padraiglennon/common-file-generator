"""Tests for best-effort behaviour: mismatches report, never crash."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from common_file_generator.core import Config, MediaSpec, TableSpec, generate


def test_too_many_rows_truncates_and_warns(pptx_template: Path, tmp_path: Path) -> None:
    # Template table is 3x3; provide a header + 5 rows = 6 > 3.
    cfg = Config(
        tables=[
            TableSpec(
                name="RevenueTable",
                header=["A", "B", "C"],
                rows=[[str(i)] * 3 for i in range(5)],
            )
        ]
    )
    out = tmp_path / "out.pptx"
    report = generate(pptx_template, cfg, out)

    assert report.has_problems
    assert any("kept the first 3" in i.message for i in report.issues)
    # File still produced and openable.
    assert Presentation(str(out)).slides


def test_too_many_columns_truncates_and_warns(
    pptx_template: Path, tmp_path: Path
) -> None:
    cfg = Config(
        tables=[TableSpec(name="RevenueTable", rows=[["1", "2", "3", "4", "5"]])]
    )
    report = generate(pptx_template, cfg, tmp_path / "out.pptx")
    assert any("kept the first 3" in i.message for i in report.issues)


def test_missing_table_name_reports_error(pptx_template: Path, tmp_path: Path) -> None:
    cfg = Config(tables=[TableSpec(name="DoesNotExist", rows=[["x"]])])
    report = generate(pptx_template, cfg, tmp_path / "out.pptx")
    assert any(
        i.where == "tables.DoesNotExist" and "no table" in i.message
        for i in report.issues
    )


def test_unused_text_token_warns(pptx_template: Path, tmp_path: Path) -> None:
    cfg = Config(text={"title": "ok", "ghost": "unused"})
    report = generate(pptx_template, cfg, tmp_path / "out.pptx")
    assert any(i.where == "text.ghost" for i in report.issues)


def test_missing_media_file_reports_error(pptx_template: Path, tmp_path: Path) -> None:
    cfg = Config(media=[MediaSpec(name="Logo", path=tmp_path / "nope.png")])
    report = generate(pptx_template, cfg, tmp_path / "out.pptx")
    assert any(
        i.where == "media.Logo" and "not found" in i.message for i in report.issues
    )
