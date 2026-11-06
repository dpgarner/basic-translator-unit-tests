"""Unit tests for features/output_print.feature -- PRINT statement translation.

Mirrors the scenarios in that feature file, Python target only for now.
"""

import pytest

from basic_translator import TranslationError, translate

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_print_literal_string(to_python, run_python):
    # Scenario: Translate a literal string PRINT statement
    code = to_python('PRINT "Hello, World!"')
    assert run_python(code) == "Hello, World!\n"


def test_print_numeric_expression(to_python, run_python):
    # Scenario: Translate PRINT with a numeric expression
    code = to_python("PRINT 2 + 2")
    assert run_python(code).strip() == "4"


def test_print_multiple_semicolon_expressions(to_python, run_python):
    # Scenario: Translate PRINT with multiple semicolon-separated expressions
    code = to_python('PRINT "Total: "; 10 + 5')
    assert run_python(code).strip() == "Total: 15"


def test_print_using_is_rejected_as_unsupported():
    # Scenario: Reject PRINT USING (legacy formatting) as out of scope
    with pytest.raises(TranslationError) as exc_info:
        translate('PRINT USING "###.##"; 3.14159', target="python")
    assert "PRINT USING" in str(exc_info.value)
    assert exc_info.value.category == "unsupported"
