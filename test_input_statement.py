"""Unit tests for features/input_statement.feature -- INPUT statement translation."""

import pytest

def test_input_with_prompt_into_string_variable(to_python, run_python):
    # Scenario: Translate INPUT with a prompt into a string variable
    code = to_python('INPUT "Enter your name: ", NAME$')
    output = run_python(code, stdin_data="Alice\n")
    assert "Enter your name: " in output


def test_input_into_numeric_variable(to_python, run_python):
    # Scenario: Translate INPUT into a numeric variable
    code = to_python(
        """
        INPUT "Enter your age: ", AGE%
        PRINT AGE% + 1
        """
    )
    output = run_python(code, stdin_data="30\n")
    assert output.strip().endswith("31")


def test_input_invalid_numeric_value_does_not_crash(to_python, run_python):
    # Scenario: Translate INPUT into a numeric variable (non-numeric input)
    code = to_python('INPUT "Enter your age: ", AGE%')
    # Should not raise -- generated program should handle bad input gracefully.
    run_python(code, stdin_data="not-a-number\n")


def test_input_multiple_comma_separated_variables(to_python, run_python):
    # Scenario: Translate INPUT with multiple comma-separated variables
    code = to_python(
        """
        INPUT "Enter X and Y: ", X, Y
        PRINT X + Y
        """
    )
    output = run_python(code, stdin_data="3,4\n")
    assert output.strip().endswith("7")


def test_input_without_prompt_displays_nothing(to_python, run_python):
    # Scenario: Flag INPUT without a prompt as valid but note the missing prompt
    code = to_python("INPUT NAME$")
    output = run_python(code, stdin_data="Bob\n")
    assert output == ""


def test_input_prompt_accepts_semicolon_separator(to_python, run_python):
    # Scenario: Translate INPUT with a semicolon after the prompt
    code = to_python('INPUT "Name"; NAME$')
    output = run_python(code, stdin_data="Alice\n")
    assert "Name" in output
