"""Unit tests for features/loops.feature."""

import pytest

def test_simple_for_next_loop(to_python, run_python):
    # Scenario: Translate a simple FOR/NEXT loop
    code = to_python(
        """
        FOR i = 1 TO 5
            PRINT i
        NEXT i
        """
    )
    assert run_python(code).splitlines() == ["1", "2", "3", "4", "5"]


def test_for_next_with_step(to_python, run_python):
    # Scenario: Translate FOR/NEXT with a STEP clause
    code = to_python(
        """
        FOR i = 10 TO 0 STEP -2
            PRINT i
        NEXT i
        """
    )
    assert run_python(code).splitlines() == ["10", "8", "6", "4", "2", "0"]


def test_while_wend(to_python, run_python):
    # Scenario: Translate WHILE/WEND
    code = to_python(
        """
        DIM count AS INTEGER
        count = 0
        WHILE count < 3
            PRINT count
            count = count + 1
        WEND
        """
    )
    assert run_python(code).splitlines() == ["0", "1", "2"]


def test_nested_for_loops_preserve_order(to_python, run_python):
    # Scenario: Translate nested FOR loops preserving iteration order
    code = to_python(
        """
        FOR i = 1 TO 2
            FOR j = 1 TO 2
                PRINT i; j
            NEXT j
        NEXT i
        """
    )
    assert run_python(code).splitlines() == ["1 1", "1 2", "2 1", "2 2"]


def test_infinite_loop_pattern_warns_but_translates():
    # Scenario: Detect an infinite loop pattern and warn rather than silently translate
    # NOTE: the stub interface doesn't yet expose a warnings channel -- once
    # translate() supports returning/raising warnings, update this test to
    # assert a warning is emitted for "WHILE TRUE : WEND" style loops instead
    # of just checking it doesn't crash the translator outright.
    pytest.skip("Warnings channel not yet defined on the translate() interface")
