"""Unit tests for features/math_functions.feature."""

import pytest

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_abs(to_python, run_python):
    code = to_python("PRINT ABS(-7)")
    assert run_python(code).strip() == "7"


def test_sqr(to_python, run_python):
    code = to_python("PRINT SQR(16)")
    assert run_python(code).strip() == "4"


def test_int_floors_toward_negative_infinity(to_python, run_python):
    # Scenario: Translate INT (truncation toward negative infinity)
    code = to_python(
        """
        PRINT INT(4.7)
        PRINT INT(-4.7)
        """
    )
    assert run_python(code).splitlines() == ["4", "-5"]


def test_rnd_is_seedable_for_reproducible_tests(to_python, run_python):
    # Scenario: Translate RND with a seedable random source
    # The generated code is expected to expose a seed hook; this test just
    # checks the translation succeeds and produces a numeric line of output.
    code = to_python("PRINT RND")
    output = run_python(code).strip()
    assert output != ""
    float(output)  # should parse as a number


def test_sqr_of_negative_number_raises_runtime_error(to_python, run_python):
    # Scenario: Translate SQR of a negative number as a runtime error
    code = to_python("PRINT SQR(-1)")
    with pytest.raises(RuntimeError):
        run_python(code)
