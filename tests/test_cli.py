"""Tests for the thin CLI wrapper."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation

from ms_office_file_generator.cli import main


def _config_file(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_fill_success(pptx_template: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pptx"
    code = main(
        [
            "fill",
            "--template",
            str(pptx_template),
            "--config",
            str(_config_file(tmp_path, {"text": {"title": "Hi"}})),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert out.is_file()


def test_fill_reports_problems_with_exit_1(pptx_template: Path, tmp_path: Path) -> None:
    code = main(
        [
            "fill",
            "--template",
            str(pptx_template),
            "--config",
            str(_config_file(tmp_path, {"text": {"ghost": "x"}})),
            "--out",
            str(tmp_path / "out.pptx"),
        ]
    )
    assert code == 1


def test_fill_bad_config_exits_2(pptx_template: Path, tmp_path: Path) -> None:
    code = main(
        [
            "fill",
            "--template",
            str(pptx_template),
            "--config",
            str(tmp_path / "missing.json"),
            "--out",
            str(tmp_path / "out.pptx"),
        ]
    )
    assert code == 2


def test_deck_success(tmp_path: Path) -> None:
    out = tmp_path / "deck.pptx"
    code = main(["deck", "--out", str(out), "--complexity", "maximum", "--slides", "5"])
    assert code == 0
    assert len(Presentation(str(out)).slides) == 5


def test_deck_invalid_slides_exits_2(tmp_path: Path) -> None:
    code = main(["deck", "--out", str(tmp_path / "d.pptx"), "--slides", "0"])
    assert code == 2
