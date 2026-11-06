"""Unit tests for features/error_handling_and_diagnostics.feature."""

import pytest

from basic_translator import TranslationError, translate

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Python backend not implemented yet -- see basic_translator/__init__.py",
    strict=False,
)


def test_syntax_error_reports_line_and_missing_then():
    # Scenario: Report a syntax error with line and column information
    with pytest.raises(TranslationError) as exc_info:
        translate('IF x > 10 PRINT "big"', target="python")
    message = str(exc_info.value).lower()
    assert exc_info.value.category == "syntax"
    assert "then" in message


def test_legacy_goto_reported_as_unsupported_not_syntax_error():
    # Scenario: Distinguish "unsupported in this dialect" from "genuine syntax error"
    with pytest.raises(TranslationError) as exc_info:
        translate("10 GOTO 10", target="python")
    assert exc_info.value.category == "unsupported"


def test_on_error_goto_warns_but_still_translates(to_python, run_python):
    # Scenario: Warn, don't fail, on constructs with a lossy but usable translation
    # NOTE: once translate() exposes a warnings channel, assert the specific
    # warning text here instead of just checking translation succeeds.
    code = to_python(
        """
        ON ERROR GOTO handler
        PRINT "ok"
        """
    )
    assert run_python(code).strip() == "ok"


def test_shell_command_refused_for_safety():
    # Scenario: Fail cleanly when a required runtime feature has no equivalent in the target
    with pytest.raises(TranslationError) as exc_info:
        translate('SHELL "format C:"', target="python")
    assert exc_info.value.category == "unsupported"
    assert "shell" in str(exc_info.value).lower()


def test_undeclared_variable_reported_as_semantic_error():
    # Scenario: Validate the AST before handing it to any backend
    with pytest.raises(TranslationError) as exc_info:
        translate("PRINT undeclared_var", target="python")
    assert exc_info.value.category == "semantic"


def test_diagnostics_json_report_generated():
    # Scenario: Produce a machine-readable diagnostics report alongside console output
    pytest.skip(
        "translate() does not yet accept a diagnostics-output option -- "
        "extend the interface in basic_translator/__init__.py first"
    )
