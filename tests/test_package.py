"""Smoke tests for the package skeleton."""

import ms_office_file_generator


def test_version_exposed() -> None:
    assert ms_office_file_generator.__version__ == "0.1.0"
