"""Unit tests for features/multi_target_translation.feature.

Unlike the other test files, most of these check the *architecture* of the
translate() interface itself (that it distinguishes "unimplemented backend"
from "implemented backend, bad input" consistently) rather than needing a
working Python backend -- so several of these can and should pass today.
"""

import pytest

from basic_translator import (
    SUPPORTED_TARGETS,
    TranslationError,
    UnsupportedTargetError,
    translate,
    translate_many,
)


def test_unknown_target_language_is_rejected():
    with pytest.raises(UnsupportedTargetError):
        translate('PRINT "hi"', target="cobol")


@pytest.mark.parametrize("target", sorted(SUPPORTED_TARGETS - {"python"}))
def test_recognized_but_unbuilt_targets_raise_unsupported_target_error(target):
    # Scenario: A translation run reports which target languages were attempted
    # and their pass/fail status (partial slice: each non-python target is
    # currently "not yet built", and should say so clearly rather than
    # crashing with an unrelated error).
    with pytest.raises(UnsupportedTargetError) as exc_info:
        translate('PRINT "hi"', target=target)
    assert exc_info.value.target == target


def test_same_program_produces_equivalent_output_on_python(to_python, run_python):
    # Scenario: The same program produces equivalent observable output across all targets
    # (Python slice only until other backends exist -- add parametrized
    # variants here as each new backend comes online.)
    code = to_python(
        """
        DIM total AS INTEGER
        total = 0
        FOR i = 1 TO 5
            total = total + i
        NEXT i
        PRINT "Sum: "; total
        """
    )
    assert run_python(code).strip() == "Sum: 15"


def test_unsupported_construct_error_category_consistent_on_python():
    # Scenario: Unsupported constructs fail the same way regardless of target
    with pytest.raises(TranslationError) as exc_info:
        translate("10 GOTO 10", target="python")
    assert exc_info.value.category == "unsupported"


def test_translation_run_summary_reports_per_target_status():
    # Scenario: A translation run reports which target languages were attempted
    # and their pass/fail status
    results = translate_many('PRINT "hi"')
    assert [r.target for r in results] == sorted(SUPPORTED_TARGETS)

    by_target = {r.target: r for r in results}
    assert by_target["python"].ok is True
    assert by_target["python"].output
    assert by_target["python"].error is None
    assert by_target["kotlin"].ok is False
    assert "No backend" in by_target["kotlin"].error
    assert by_target["kotlin"].category == "unsupported"
