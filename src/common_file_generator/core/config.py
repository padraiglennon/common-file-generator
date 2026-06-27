"""Load and validate the JSON injection config.

The config is the contract a non-technical user edits. It maps named template
elements to the data that should be injected:

* ``text``   - maps a ``{{token}}`` name to the string that replaces it.
* ``tables`` - maps a named table shape to a header + rows (multi-row/column).
* ``media``  - maps a named picture-placeholder shape to a local asset path.

Validation favours clear, plain-English error messages over stack traces.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a config file is missing, malformed, or fails validation."""


@dataclass(frozen=True)
class TableSpec:
    """Data for one named table: an optional header row plus body rows."""

    name: str
    rows: list[list[str]]
    header: list[str] | None = None


@dataclass(frozen=True)
class MediaSpec:
    """An image to place into a named picture-placeholder shape."""

    name: str
    path: Path


@dataclass(frozen=True)
class Config:
    """A validated injection config."""

    text: dict[str, str] = field(default_factory=dict)
    tables: list[TableSpec] = field(default_factory=list)
    media: list[MediaSpec] = field(default_factory=list)


def load_config(path: str | Path, *, base_dir: str | Path | None = None) -> Config:
    """Load and validate a JSON config file into a :class:`Config`.

    ``base_dir`` is the directory that relative media paths resolve against;
    it defaults to the config file's own directory.
    """
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Config file {path.name} is not valid JSON: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})."
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigError(
            f"Config file {path.name} must be a JSON object at the top level, "
            f"got {_type_name(raw)}."
        )

    resolve_base = Path(base_dir) if base_dir is not None else path.parent
    return Config(
        text=_parse_text(raw.get("text", {})),
        tables=_parse_tables(raw.get("tables", [])),
        media=_parse_media(raw.get("media", []), resolve_base),
    )


def _parse_text(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ConfigError(
            f"'text' must be a mapping of token names to values, "
            f"got {_type_name(value)}."
        )
    text: dict[str, str] = {}
    for key, val in value.items():
        if not isinstance(val, str | int | float):
            raise ConfigError(
                f"'text.{key}' must be a string or number, got {_type_name(val)}."
            )
        text[str(key)] = str(val)
    return text


def _parse_tables(value: Any) -> list[TableSpec]:
    if not isinstance(value, list):
        raise ConfigError(
            f"'tables' must be a list of table objects, got {_type_name(value)}."
        )
    tables: list[TableSpec] = []
    for index, item in enumerate(value):
        tables.append(_parse_one_table(item, index))
    return tables


def _parse_one_table(item: Any, index: int) -> TableSpec:
    where = f"tables[{index}]"
    if not isinstance(item, dict):
        raise ConfigError(f"'{where}' must be an object, got {_type_name(item)}.")

    name = item.get("name")
    if not isinstance(name, str) or not name:
        raise ConfigError(f"'{where}.name' must be a non-empty string.")

    rows = _parse_rows(item.get("rows", []), f"{where}.rows")
    header = item.get("header")
    if header is not None:
        header = _parse_row(header, f"{where}.header")
    return TableSpec(name=name, rows=rows, header=header)


def _parse_rows(value: Any, where: str) -> list[list[str]]:
    if not isinstance(value, list):
        raise ConfigError(f"'{where}' must be a list of rows, got {_type_name(value)}.")
    return [_parse_row(row, f"{where}[{i}]") for i, row in enumerate(value)]


def _parse_row(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        raise ConfigError(
            f"'{where}' must be a list of cell values, got {_type_name(value)}."
        )
    cells: list[str] = []
    for i, cell in enumerate(value):
        if not isinstance(cell, str | int | float):
            raise ConfigError(
                f"'{where}[{i}]' must be a string or number, got {_type_name(cell)}."
            )
        cells.append(str(cell))
    return cells


def _parse_media(value: Any, base_dir: Path) -> list[MediaSpec]:
    if not isinstance(value, list):
        raise ConfigError(
            f"'media' must be a list of media objects, got {_type_name(value)}."
        )
    media: list[MediaSpec] = []
    for index, item in enumerate(value):
        where = f"media[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f"'{where}' must be an object, got {_type_name(item)}.")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise ConfigError(f"'{where}.name' must be a non-empty string.")
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ConfigError(f"'{where}.path' must be a non-empty string.")
        asset_path = Path(raw_path)
        if not asset_path.is_absolute():
            asset_path = base_dir / asset_path
        media.append(MediaSpec(name=name, path=asset_path))
    return media


def _type_name(value: Any) -> str:
    return {
        dict: "an object",
        list: "a list",
        str: "a string",
        bool: "a boolean",
        int: "a number",
        float: "a number",
        type(None): "null",
    }.get(type(value), type(value).__name__)
