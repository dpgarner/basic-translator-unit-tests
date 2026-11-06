"""Unit tests for features/variables_and_comments.feature."""

import pytest

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_typed_dim_declaration(to_python, run_python):
    # Scenario: Translate a typed DIM declaration
    code = to_python(
        """
        DIM count AS INTEGER
        PRINT count
        """
    )
    assert run_python(code).strip() == "0"


def test_dim_with_initializer_via_let(to_python, run_python):
    # Scenario: Translate DIM with an initializer via LET
    code = to_python(
        """
        DIM total AS INTEGER
        LET total = 0
        PRINT total
        """
    )
    assert run_python(code).strip() == "0"


def test_implicit_let_bare_assignment(to_python, run_python):
    # Scenario: Translate implicit LET (bare assignment)
    code = to_python(
        """
        DIM total AS INTEGER
        total = 5
        total = total + 1
        PRINT total
        """
    )
    assert run_python(code).strip() == "6"


def test_rem_comment_preserved_and_inert(to_python, run_python):
    # Scenario: Translate a REM comment
    code = to_python(
        """
        REM This calculates the running total
        PRINT 1
        """
    )
    assert "This calculates the running total" in code
    assert run_python(code).strip() == "1"


def test_apostrophe_inline_comment(to_python, run_python):
    # Scenario: Translate an apostrophe-style inline comment
    code = to_python("x = 5 ' set default")
    assert "set default" in code
