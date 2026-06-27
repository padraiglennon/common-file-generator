"""Smoke tests for the package skeleton."""

import common_file_generator


def test_version_exposed() -> None:
    assert common_file_generator.__version__ == "0.1.0"
