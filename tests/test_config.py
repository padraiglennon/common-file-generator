"""Tests for config loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from common_file_generator.core import ConfigError, load_config


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_full_config(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "text": {"title": "Hello", "count": 3},
            "tables": [
                {"name": "T", "header": ["A", "B"], "rows": [["1", "2"], ["3", "4"]]}
            ],
            "media": [{"name": "Logo", "path": "logo.png"}],
        },
    )
    cfg = load_config(path)
    assert cfg.text == {"title": "Hello", "count": "3"}
    assert cfg.tables[0].name == "T"
    assert cfg.tables[0].header == ["A", "B"]
    assert cfg.tables[0].rows == [["1", "2"], ["3", "4"]]
    assert cfg.media[0].name == "Logo"
    assert cfg.media[0].path == tmp_path / "logo.png"


def test_empty_config_is_valid(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, {}))
    assert cfg.text == {}
    assert cfg.tables == []
    assert cfg.media == []


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.json")


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(path)


def test_top_level_must_be_object(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="object at the top level"):
        load_config(_write(tmp_path, [1, 2, 3]))


def test_table_without_name_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"tables\[0\].name"):
        load_config(_write(tmp_path, {"tables": [{"rows": []}]}))


def test_media_without_path_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"media\[0\].path"):
        load_config(_write(tmp_path, {"media": [{"name": "X"}]}))


def test_absolute_media_path_preserved(tmp_path: Path) -> None:
    abs_path = (tmp_path / "x" / "logo.png").resolve()
    cfg = load_config(
        _write(tmp_path, {"media": [{"name": "L", "path": str(abs_path)}]})
    )
    assert cfg.media[0].path == abs_path
