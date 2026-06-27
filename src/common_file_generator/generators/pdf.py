"""Complexity-driven PDF generator.

Builds a ``.pdf`` from scratch (not template injection) with reportlab's platypus
layout engine. A document is a series of **sections**; each section opens with a
heading and a paragraph, then draws extra content blocks from a weighted pool that
grows with the complexity level. Content is seeded lorem-ipsum and placeholder
images are generated in memory, so the same ``(complexity, sections, seed)``
yields the same content and no external assets are needed.

Note: reportlab embeds a creation timestamp in the PDF, so two runs are not
byte-identical; the generated *content* is deterministic for a given seed.
"""

from __future__ import annotations

import io
import random
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from common_file_generator.core.complexity import Complexity, doc_block_pool
from common_file_generator.core.lorem import Lorem

# Letter page (8.5") minus the SimpleDocTemplate default 1" margins each side.
_USABLE_WIDTH = 6.5 * inch
_IMAGE_WIDTH = 4.5 * inch
_PLACEHOLDER_SIZE = (480, 270)  # source PNG pixels; image height keeps this ratio

# Extra content blocks per section, by complexity. Mirrors the docx generator so
# section richness scales with complexity, not just which block types appear.
_BLOCKS_PER_SECTION: dict[Complexity, int] = {
    Complexity.MINIMAL: 1,
    Complexity.SIMPLE: 2,
    Complexity.STANDARD: 3,
    Complexity.COMPLEX: 4,
    Complexity.MAXIMUM: 5,
}


class PdfComplexityGenerator:
    """Generate a PDF document at a chosen complexity level."""

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
        self._styles = getSampleStyleSheet()

    def build(self) -> list:
        flow: list = [
            Paragraph(self._lorem.title(6), self._styles["Title"]),
            Spacer(1, 12),
        ]
        for index in range(1, self.sections + 1):
            self._add_section(flow, index)
        return flow

    def save(self, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        document = SimpleDocTemplate(str(out_path), pagesize=letter)
        document.build(self.build())
        return out_path

    # --- sections + blocks ----------------------------------------------

    def _add_section(self, flow: list, index: int) -> None:
        flow.append(
            Paragraph(f"{index}. {self._lorem.title()}", self._styles["Heading1"])
        )
        self._add_paragraph(flow)
        for _ in range(self.blocks_per_section):
            key = self._rng.choices(self._block_keys, weights=self._block_weights)[0]
            self._BLOCKS[key](self, flow)

    def _add_paragraph(self, flow: list) -> None:
        flow.append(Paragraph(self._lorem.paragraph(2, 4), self._styles["BodyText"]))
        flow.append(Spacer(1, 6))

    def _add_bullets(self, flow: list) -> None:
        flow.append(Paragraph(self._lorem.title(3), self._styles["Heading2"]))
        flow.append(self._list_flowable("bullet"))

    def _add_numbered(self, flow: list) -> None:
        flow.append(Paragraph(self._lorem.title(3), self._styles["Heading2"]))
        flow.append(self._list_flowable("1"))

    def _add_table(self, flow: list) -> None:
        cols = self._rng.randint(3, 4)
        rows = self._rng.randint(3, 6)
        data = [[self._lorem.title(2) for _ in range(cols)]]
        for _ in range(rows - 1):
            data.append(
                [self._lorem.words(self._rng.randint(1, 3)) for _ in range(cols)]
            )
        table = Table(data, colWidths=[_USABLE_WIDTH / cols] * cols)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        flow.append(table)
        flow.append(Spacer(1, 6))

    def _add_image(self, flow: list) -> None:
        width, height = _PLACEHOLDER_SIZE
        flow.append(
            Image(
                self._placeholder_png(),
                width=_IMAGE_WIDTH,
                height=_IMAGE_WIDTH * height / width,
            )
        )
        flow.append(Spacer(1, 6))

    def _add_quote(self, flow: list) -> None:
        flow.append(Paragraph(self._lorem.sentence(8, 16), self._styles["Italic"]))
        flow.append(Spacer(1, 6))

    def _add_page_break(self, flow: list) -> None:
        flow.append(PageBreak())

    _BLOCKS = {
        "paragraph": _add_paragraph,
        "bullets": _add_bullets,
        "numbered": _add_numbered,
        "table": _add_table,
        "image": _add_image,
        "quote": _add_quote,
        "page_break": _add_page_break,
    }

    # --- helpers --------------------------------------------------------

    def _list_flowable(self, bullet_type: str) -> ListFlowable:
        items = [
            ListItem(Paragraph(text, self._styles["BodyText"]))
            for text in self._lorem.bullets(self._rng.randint(3, 5))
        ]
        return ListFlowable(items, bulletType=bullet_type)

    def _placeholder_png(self) -> io.BytesIO:
        color = (
            self._rng.randint(40, 220),
            self._rng.randint(40, 220),
            self._rng.randint(40, 220),
        )
        image = PILImage.new("RGB", _PLACEHOLDER_SIZE, color)
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        stream.seek(0)
        return stream
