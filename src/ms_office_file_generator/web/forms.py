"""Build the deck-form field schema by introspecting the core.

Keeping the form a function of the core's public surface means new options
(another ``Complexity`` value, a new ``BackgroundMode``, a changed default) show
up in the UI automatically, without editing templates. An explicit per-field
label/kind table keeps internals from leaking verbatim into the HTML.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum

from ms_office_file_generator.core import Complexity, generate_deck, generate_doc
from ms_office_file_generator.generators.background import BackgroundMode


@dataclass(frozen=True)
class Choice:
    """One option in a select, with a friendly label."""

    value: str
    label: str


@dataclass(frozen=True)
class Field:
    """One labelled form input derived from the core."""

    name: str
    label: str
    kind: str  # "select" | "number" | "text"
    default: str
    help: str
    required: bool = False
    choices: tuple[Choice, ...] = field(default_factory=tuple)


# Presentation metadata for the introspected parameters: (label, kind, help).
# Help text is written in plain, non-technical language. Only parameters listed
# here are exposed; anything else in the signature (e.g. theme_path, handled as a
# file upload) is intentionally omitted.
_DECK_FIELD_META: dict[str, tuple[str, str, str]] = {
    "complexity": (
        "Complexity",
        "select",
        "How busy each slide is. Higher means more charts, tables, pictures "
        "and videos.",
    ),
    "slides": (
        "Number of slides",
        "number",
        "How many slides to create.",
    ),
    "seed": (
        "Variation",
        "number",
        "Pick any number. The same number makes the same deck every time; "
        "change it for a different one.",
    ),
    "background": (
        "Slide background",
        "select",
        "The colour behind your slides. Pick 'Custom colour' to choose your own.",
    ),
    "video_url": (
        "Video link",
        "text",
        "A YouTube link to show on video slides. Leave it as it is if you are "
        "not sure.",
    ),
}

# Friendly labels for enum-derived choices, plus the UI-only "custom" option.
_BACKGROUND_LABELS: dict[str, str] = {
    "none": "Plain white",
    "theme": "Soft blue (same on every slide)",
    "random": "Soft colours (different per slide)",
    "custom": "Custom colour...",
}
_COMPLEXITY_LABELS: dict[str, str] = {
    "minimal": "Minimal",
    "simple": "Simple",
    "standard": "Standard",
    "complex": "Complex",
    "maximum": "Maximum",
}

# Metadata for the Word document form (generate_doc parameters).
_DOC_FIELD_META: dict[str, tuple[str, str, str]] = {
    "complexity": (
        "Complexity",
        "select",
        "How rich each section is. Higher means more lists, tables, images and quotes.",
    ),
    "sections": (
        "Number of sections",
        "number",
        "How many sections (a heading plus content) to create.",
    ),
    "seed": (
        "Variation",
        "number",
        "Pick any number. The same number makes the same document every time; "
        "change it for a different one.",
    ),
}

_ENUM_CHOICES: dict[str, type[Enum]] = {
    "complexity": Complexity,
    "background": BackgroundMode,
}


def deck_fields() -> list[Field]:
    """Return the deck form fields, derived from ``generate_deck``'s signature."""
    return _fields_from(generate_deck, _DECK_FIELD_META)


def doc_fields() -> list[Field]:
    """Return the document form fields, derived from ``generate_doc``'s signature."""
    return _fields_from(generate_doc, _DOC_FIELD_META)


def _fields_from(func: object, meta: dict[str, tuple[str, str, str]]) -> list[Field]:
    signature = inspect.signature(func)
    fields: list[Field] = []
    for name, (label, kind, help_text) in meta.items():
        parameter = signature.parameters.get(name)
        default = _default_str(parameter.default if parameter else "")
        fields.append(
            Field(
                name=name,
                label=label,
                kind=kind,
                default=default,
                help=help_text,
                choices=_choices_for(name),
            )
        )
    return fields


def _choices_for(name: str) -> tuple[Choice, ...]:
    enum = _ENUM_CHOICES.get(name)
    if enum is None:
        return ()
    values = [member.value for member in enum]
    if name == "background":
        values.append("custom")  # UI-only: reveals a colour picker
        labels = _BACKGROUND_LABELS
    elif name == "complexity":
        labels = _COMPLEXITY_LABELS
    else:
        labels = {}
    return tuple(Choice(value=v, label=labels.get(v, v)) for v in values)


def _default_str(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    if value in (None, inspect.Parameter.empty):
        return ""
    return str(value)
