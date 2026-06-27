"""Tests for the complexity-driven Markdown document generator."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from common_file_generator.core import Complexity, generate_markdown
from common_file_generator.generators import MarkdownComplexityGenerator

_SECTION_HEADING = re.compile(r"^## \d+\. ", re.MULTILINE)


def test_creates_nonempty_markdown(tmp_path: Path) -> None:
    out = tmp_path / "d.md"
    generate_markdown(str(out), complexity="standard", sections=5, seed=1)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# ")  # document title


def test_section_count_drives_headings(tmp_path: Path) -> None:
    out = tmp_path / "d.md"
    generate_markdown(str(out), complexity="standard", sections=8, seed=1)
    text = out.read_text(encoding="utf-8")
    assert len(_SECTION_HEADING.findall(text)) == 8


def test_invalid_section_count_raises() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        MarkdownComplexityGenerator(Complexity.MINIMAL, sections=0)


def test_invalid_blocks_per_section_raises() -> None:
    with pytest.raises(ValueError, match="blocks_per_section"):
        MarkdownComplexityGenerator(
            Complexity.MINIMAL, sections=2, blocks_per_section=0
        )


def test_minimal_has_no_tables_or_code_blocks(tmp_path: Path) -> None:
    out = tmp_path / "d.md"
    generate_markdown(str(out), complexity="minimal", sections=10, seed=3)
    text = out.read_text(encoding="utf-8")
    assert "| --- |" not in text  # no table separators
    assert "```" not in text  # no fenced code blocks (the image substitute)


def test_maximum_has_rich_blocks(tmp_path: Path) -> None:
    out = tmp_path / "d.md"
    generate_markdown(str(out), complexity="maximum", sections=30, seed=7)
    text = out.read_text(encoding="utf-8")
    assert "## " in text  # section headings
    assert "\n- " in text  # bullets
    assert "| --- |" in text  # a GFM table
    assert "```" in text  # image rendered as a fenced code block
    assert "\n> " in text  # a block quote


def test_blocks_per_section_override(tmp_path: Path) -> None:
    out = tmp_path / "d.md"
    generate_markdown(
        str(out), complexity="minimal", sections=4, seed=1, blocks_per_section=6
    )
    text = out.read_text(encoding="utf-8")
    # The override forces 6 extra blocks per section beyond the minimal default
    # (1), so the document is far longer than a default-minimal one.
    default = tmp_path / "default.md"
    generate_markdown(str(default), complexity="minimal", sections=4, seed=1)
    assert len(text) > len(default.read_text(encoding="utf-8"))


def test_seed_is_deterministic(tmp_path: Path) -> None:
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    generate_markdown(str(a), complexity="complex", sections=10, seed=42)
    generate_markdown(str(b), complexity="complex", sections=10, seed=42)
    # Markdown has no embedded timestamp, so output is byte-for-byte identical.
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


def test_different_seed_differs(tmp_path: Path) -> None:
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    generate_markdown(str(a), complexity="complex", sections=10, seed=1)
    generate_markdown(str(b), complexity="complex", sections=10, seed=2)
    assert a.read_text(encoding="utf-8") != b.read_text(encoding="utf-8")
