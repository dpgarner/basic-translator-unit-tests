"""Shared fixtures for the BASIC translator unit test suite.

Each test file here mirrors one feature file under features/ -- see
features/README.md for the full mapping. These tests currently target the
Python backend only, per the "wire up one backend first" recommendation in
that README.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from basic_translator import translate


def run_python_source(code: str, stdin_data: str = "") -> str:
    """Execute generated Python source in a subprocess and return stdout.

    Raises RuntimeError (with captured stderr) if the generated code itself
    raises an exception, so a broken translation shows up as an obvious test
    failure rather than a silently-empty pass.
    """
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Generated Python code raised an error:\n{result.stderr}")
    return result.stdout


@pytest.fixture
def to_python():
    """Translate a BASIC source snippet to Python source code."""

    def _translate(basic_source: str) -> str:
        return translate(textwrap.dedent(basic_source).strip(), target="python")

    return _translate


@pytest.fixture
def run_python():
    """Execute generated Python code and return captured stdout."""
    return run_python_source
