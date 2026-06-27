"""Shared ``{{token}}`` replacement for python-pptx / python-docx paragraphs.

Office documents often split a single visible word across several runs (because
of spell-check or formatting boundaries), so a ``{{token}}`` may not live in one
run. We replace at the paragraph level: read the full paragraph text, substitute,
write the result back into the first run, and blank the remaining runs. This
preserves the first run's formatting and keeps the operation robust.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Protocol

_TOKEN_RE = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")


class _Run(Protocol):
    text: str


class _Paragraph(Protocol):
    @property
    def runs(self) -> list[_Run]: ...

    @property
    def text(self) -> str: ...


def find_tokens(text: str) -> set[str]:
    """Return the set of token names present in ``text``."""
    return {match.group(1) for match in _TOKEN_RE.finditer(text)}


def replace_in_paragraph(paragraph: _Paragraph, values: Mapping[str, str]) -> set[str]:
    """Replace known tokens in one paragraph. Returns the token names used.

    Unknown tokens are left untouched so they can be reported as missing data.
    """
    original = paragraph.text
    present = find_tokens(original)
    if not present:
        return set()

    used = present & set(values)
    if not used:
        return set()

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        return values[name] if name in values else match.group(0)

    new_text = _TOKEN_RE.sub(_sub, original)
    _write_paragraph_text(paragraph, new_text)
    return used


def _write_paragraph_text(paragraph: _Paragraph, text: str) -> None:
    runs = paragraph.runs
    if not runs:
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""
