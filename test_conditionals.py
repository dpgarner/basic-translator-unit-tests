"""Unit tests for features/conditionals.feature."""

import pytest

from basic_translator import TranslationError, translate

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_single_line_if_then(to_python, run_python):
    # Scenario: Translate a single-line IF/THEN
    code = to_python(
        """
        DIM x AS INTEGER
        x = 20
        IF x > 10 THEN PRINT "big"
        """
    )
    assert run_python(code).strip() == "big"


@pytest.mark.parametrize("x_value,expected", [(20, "big"), (5, "small")])
def test_block_if_then_else(to_python, run_python, x_value, expected):
    # Scenario: Translate a block IF/THEN/ELSE/END IF
    code = to_python(
        f"""
        DIM x AS INTEGER
        x = {x_value}
        IF x > 10 THEN
            PRINT "big"
        ELSE
            PRINT "small"
        END IF
        """
    )
    assert run_python(code).strip() == expected


@pytest.mark.parametrize(
    "grade,expected", [(95, "A"), (85, "B"), (50, "C or lower")]
)
def test_elseif_chain(to_python, run_python, grade, expected):
    # Scenario: Translate ELSEIF chains
    code = to_python(
        f"""
        DIM grade AS INTEGER
        grade = {grade}
        IF grade >= 90 THEN
            PRINT "A"
        ELSEIF grade >= 80 THEN
            PRINT "B"
        ELSE
            PRINT "C or lower"
        END IF
        """
    )
    assert run_python(code).strip() == expected


@pytest.mark.parametrize("day,expected", [(1, "Monday"), (2, "Tue or Wed"), (3, "Tue or Wed"), (7, "Other")])
def test_select_case(to_python, run_python, day, expected):
    # Scenario: Translate SELECT CASE
    code = to_python(
        f"""
        DIM day AS INTEGER
        day = {day}
        SELECT CASE day
            CASE 1
                PRINT "Monday"
            CASE 2, 3
                PRINT "Tue or Wed"
            CASE ELSE
                PRINT "Other"
        END SELECT
        """
    )
    assert run_python(code).strip() == expected


def test_select_case_range_clause_rejected():
    # Scenario: Reject a SELECT CASE with a range clause as a documented limitation
    with pytest.raises(TranslationError) as exc_info:
        translate(
            "SELECT CASE x\nCASE 1 TO 5\nPRINT 1\nEND SELECT",
            target="python",
        )
    assert exc_info.value.category == "unsupported"
