"""Complexity-driven Markdown document generator.

Builds a ``.md`` from scratch (not template injection). A document is a series of
**sections**; each section opens with a heading and a paragraph, then draws extra
content blocks from a weighted pool that grows with the complexity level. Content
is seeded lorem-ipsum, so the same ``(complexity, sections, seed)`` always yields
the identical text.

Output is a single self-contained text file: there are no image bytes in
Markdown, so the ``image`` block renders as a fenced code block, and the
``page_break`` block (meaningless in Markdown) renders as a horizontal rule.
"""

from __future__ import annotations

import random
from pathlib import Path

from ms_office_file_generator.core.complexity import Complexity, doc_block_pool
from ms_office_file_generator.core.lorem import Lorem

# Extra content blocks per section, by complexity. Mirrors the docx generator so
# section richness scales with complexity, not just which block types appear.
_BLOCKS_PER_SECTION: dict[Complexity, int] = {
    Complexity.MINIMAL: 1,
    Complexity.SIMPLE: 2,
    Complexity.STANDARD: 3,
    Complexity.COMPLEX: 4,
    Complexity.MAXIMUM: 5,
}


class MarkdownComplexityGenerator:
    """Generate a Markdown document at a chosen complexity level."""

    def __init__(
        self,
        complexity: Complexity = Complexity.STANDARD,
        *,
        sections: int = 5,
        seed: int = 0,
        blocks_per_section: int | None = None,
    ) -> None:
        if sections < 1:
            raise ValueError("sections must be at least 1")
        if blocks_per_section is not None and blocks_per_section < 1:
            raise ValueError("blocks_per_section must be at least 1")
        self.complexity = complexity
        self.sections = sections
        self.blocks_per_section = (
            blocks_per_section
            if blocks_per_section is not None
            else _BLOCKS_PER_SECTION[complexity]
        )
        pool = doc_block_pool(complexity)
        self._block_keys = [key for key, _ in pool]
        self._block_weights = [weight for _, weight in pool]
        self._rng = random.Random(seed)
        self._lorem = Lorem(self._rng)

    def build(self) -> str:
        parts: list[str] = [f"# {self._lorem.title(6)}"]  # document title
        for index in range(1, self.sections + 1):
            self._add_section(parts, index)
        return "\n\n".join(parts) + "\n"

    def save(self, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(self.build(), encoding="utf-8")
        return out_path

    # --- sections + blocks ----------------------------------------------

    def _add_section(self, parts: list[str], index: int) -> None:
        parts.append(f"## {index}. {self._lorem.title()}")
        self._add_paragraph(parts)
        for _ in range(self.blocks_per_section):
            key = self._rng.choices(self._block_keys, weights=self._block_weights)[0]
            self._BLOCKS[key](self, parts)

    def _add_paragraph(self, parts: list[str]) -> None:
        parts.append(self._lorem.paragraph(2, 4))

    def _add_bullets(self, parts: list[str]) -> None:
        parts.append(f"### {self._lorem.title(3)}")
        items = self._lorem.bullets(self._rng.randint(3, 5))
        parts.append("\n".join(f"- {text}" for text in items))

    def _add_numbered(self, parts: list[str]) -> None:
        parts.append(f"### {self._lorem.title(3)}")
        items = self._lorem.bullets(self._rng.randint(3, 5))
        parts.append("\n".join(f"{n}. {text}" for n, text in enumerate(items, 1)))

    def _add_table(self, parts: list[str]) -> None:
        cols = self._rng.randint(3, 4)
        rows = self._rng.randint(3, 6)
        header = [self._lorem.title(2) for _ in range(cols)]
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * cols) + " |",
        ]
        for _ in range(rows - 1):
            cells = [self._lorem.words(self._rng.randint(1, 3)) for _ in range(cols)]
            lines.append("| " + " | ".join(cells) + " |")
        parts.append("\n".join(lines))

    def _add_image(self, parts: list[str]) -> None:
        # No image bytes in Markdown - a fenced code block keeps a single,
        # self-contained file with no broken image references.
        parts.append("```\n" + self._lorem.paragraph(1, 2) + "\n```")

    def _add_quote(self, parts: list[str]) -> None:
        parts.append(f"> {self._lorem.sentence(8, 16)}")

    def _add_page_break(self, parts: list[str]) -> None:
        # Page breaks are meaningless in Markdown; a horizontal rule is the
        # closest section-divider equivalent.
        parts.append("---")

    _BLOCKS = {
        "paragraph": _add_paragraph,
        "bullets": _add_bullets,
        "numbered": _add_numbered,
        "table": _add_table,
        "image": _add_image,
        "quote": _add_quote,
        "page_break": _add_page_break,
    }
