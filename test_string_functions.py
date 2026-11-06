"""Unit tests for features/string_functions.feature."""

import pytest

BASIC_SETUP = 'DIM s AS STRING\ns = "Hello, World!"\n'

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_len(to_python, run_python):
    code = to_python(BASIC_SETUP + "PRINT LEN(s)")
    assert run_python(code).strip() == "13"


def test_left_dollar(to_python, run_python):
    code = to_python(BASIC_SETUP + "PRINT LEFT$(s, 5)")
    assert run_python(code).strip() == "Hello"


def test_right_dollar(to_python, run_python):
    code = to_python(BASIC_SETUP + "PRINT RIGHT$(s, 6)")
    assert run_python(code).strip() == "World!"


def test_mid_dollar_with_start_and_length(to_python, run_python):
    # NOTE: BASIC's MID$ start position is 1-based.
    code = to_python(BASIC_SETUP + "PRINT MID$(s, 8, 5)")
    assert run_python(code).strip() == "World"


def test_string_concatenation(to_python, run_python):
    code = to_python('PRINT "Hello" + ", " + "World!"')
    assert run_python(code).strip() == "Hello, World!"


def test_ucase_and_lcase(to_python, run_python):
    code = to_python(
        """
        PRINT UCASE$("abc")
        PRINT LCASE$("XYZ")
        """
    )
    assert run_python(code).splitlines() == ["ABC", "xyz"]


def test_mid_dollar_out_of_range_start_returns_empty_string(to_python, run_python):
    code = to_python(BASIC_SETUP + "PRINT MID$(s, 100, 5)")
    assert run_python(code).strip() == ""
