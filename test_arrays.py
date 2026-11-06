"""Unit tests for features/arrays.feature."""

import pytest

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_fixed_size_array_declaration_defaults_to_zero(to_python, run_python):
    # Scenario: Translate a fixed-size one-dimensional array declaration
    code = to_python(
        """
        DIM scores(9) AS INTEGER
        PRINT scores(0)
        """
    )
    assert run_python(code).strip() == "0"


def test_array_element_assignment_and_access(to_python, run_python):
    # Scenario: Translate array element assignment and access
    code = to_python(
        """
        DIM scores(4) AS INTEGER
        scores(0) = 100
        PRINT scores(0)
        """
    )
    assert run_python(code).strip() == "100"


def test_two_dimensional_array(to_python, run_python):
    # Scenario: Translate a two-dimensional array
    code = to_python(
        """
        DIM grid(2, 2) AS INTEGER
        grid(1, 1) = 7
        PRINT grid(1, 1)
        """
    )
    assert run_python(code).strip() == "7"


def test_redim_grows_array(to_python, run_python):
    # Scenario: Translate REDIM growing an existing array
    code = to_python(
        """
        DIM items(4) AS STRING
        REDIM items(9) AS STRING
        items(9) = "last"
        PRINT items(9)
        """
    )
    assert run_python(code).strip() == "last"


def test_out_of_bounds_access_reported_statically():
    # Scenario: Reject array access out of translated bounds when statically detectable
    from basic_translator import TranslationError, translate

    with pytest.raises(TranslationError) as exc_info:
        translate(
            "DIM scores(4) AS INTEGER\nPRINT scores(10)",
            target="python",
        )
    assert "bounds" in str(exc_info.value).lower()
