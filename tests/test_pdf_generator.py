"""Tests for the complexity-driven PDF document generator."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from ms_office_file_generator.core import Complexity, generate_pdf
from ms_office_file_generator.generators import PdfComplexityGenerator


def test_creates_valid_pdf(tmp_path: Path) -> None:
    out = tmp_path / "d.pdf"
    generate_pdf(str(out), complexity="standard", sections=5, seed=1)
    assert out.is_file()
    assert out.read_bytes()[:4] == b"%PDF"


def test_invalid_section_count_raises() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        PdfComplexityGenerator(Complexity.MINIMAL, sections=0)


def test_invalid_blocks_per_section_raises() -> None:
    with pytest.raises(ValueError, match="blocks_per_section"):
        PdfComplexityGenerator(Complexity.MINIMAL, sections=2, blocks_per_section=0)


def test_richer_complexity_produces_more_content(tmp_path: Path) -> None:
    # Maximum is denser than minimal at the same section count, so it extracts to
    # at least as many pages.
    mn = tmp_path / "mn.pdf"
    mx = tmp_path / "mx.pdf"
    generate_pdf(str(mn), complexity="minimal", sections=8, seed=1)
    generate_pdf(str(mx), complexity="maximum", sections=8, seed=1)
    assert len(PdfReader(str(mx)).pages) >= len(PdfReader(str(mn)).pages)
    assert len(_text(mx)) > len(_text(mn))


def test_seed_is_deterministic(tmp_path: Path) -> None:
    # reportlab embeds a creation timestamp, so the bytes differ between runs;
    # the *content* (extracted text) is deterministic for a given seed.
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    generate_pdf(str(a), complexity="complex", sections=10, seed=42)
    generate_pdf(str(b), complexity="complex", sections=10, seed=42)
    assert _text(a) == _text(b)


def test_different_seed_differs(tmp_path: Path) -> None:
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    generate_pdf(str(a), complexity="complex", sections=10, seed=1)
    generate_pdf(str(b), complexity="complex", sections=10, seed=2)
    assert _text(a) != _text(b)


def test_blocks_per_section_override(tmp_path: Path) -> None:
    out = tmp_path / "d.pdf"
    default = tmp_path / "default.pdf"
    generate_pdf(
        str(out), complexity="minimal", sections=4, seed=1, blocks_per_section=6
    )
    generate_pdf(str(default), complexity="minimal", sections=4, seed=1)
    assert len(_text(out)) > len(_text(default))


def _text(path: Path) -> str:
    return "".join(page.extract_text() for page in PdfReader(str(path)).pages)
