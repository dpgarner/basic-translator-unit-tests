"""Unit tests for features/procedures.feature -- SUB and FUNCTION translation."""

import pytest

def test_function_with_return_value(to_python, run_python):
    # Scenario: Translate a FUNCTION with a return value
    code = to_python(
        """
        FUNCTION AddNumbers (a AS INTEGER, b AS INTEGER) AS INTEGER
            AddNumbers = a + b
        END FUNCTION
        PRINT AddNumbers(2, 3)
        """
    )
    assert run_python(code).strip() == "5"


def test_sub_with_no_return_value(to_python, run_python):
    # Scenario: Translate a SUB with no return value
    code = to_python(
        """
        SUB PrintGreeting (name AS STRING)
            PRINT "Hello, " + name
        END SUB
        PrintGreeting "Alice"
        """
    )
    assert run_python(code).strip() == "Hello, Alice"


def test_byval_parameter_does_not_mutate_caller(to_python, run_python):
    # Scenario: Translate a parameter passed BYVAL (default)
    code = to_python(
        """
        SUB Increment (n AS INTEGER)
            n = n + 1
        END SUB
        DIM x AS INTEGER
        x = 5
        Increment x
        PRINT x
        """
    )
    assert run_python(code).strip() == "5"


def test_recursive_function(to_python, run_python):
    # Scenario: Translate a recursive FUNCTION
    code = to_python(
        """
        FUNCTION Factorial (n AS INTEGER) AS INTEGER
            IF n <= 1 THEN
                Factorial = 1
            ELSE
                Factorial = n * Factorial(n - 1)
            END IF
        END FUNCTION
        PRINT Factorial(5)
        """
    )
    assert run_python(code).strip() == "120"


def test_procedure_with_default_parameter_value(to_python, run_python):
    # Scenario: Translate a procedure with a default parameter value
    code = to_python(
        """
        SUB Greet (name AS STRING = "World")
            PRINT "Hello, " + name
        END SUB
        Greet
        """
    )
    assert run_python(code).strip() == "Hello, World"
