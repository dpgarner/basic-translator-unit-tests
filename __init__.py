"""Minimal BASIC-translator interface (stub).

This module defines the CONTRACT the translator must satisfy. None of the
actual lexing/parsing/code-generation logic is implemented yet -- these
functions exist purely so the unit test suite in tests/ can run against a
real interface and drive implementation (the "red" phase of TDD).

As you implement each feature from features/*.feature, replace the relevant
NotImplementedError with real logic and the corresponding tests will start
passing. Do not remove the raised errors below until there is real behavior
to replace them with.
"""

from __future__ import annotations

# Target languages the feature files define requirements for. Only "python"
# has test coverage wired up so far (see tests/). Add a backend module per
# target as you implement it.
SUPPORTED_TARGETS = {"python", "typescript", "kotlin", "rust", "erlang"}


class TranslationError(Exception):
    """Raised when BASIC source cannot be translated.

    Attributes:
        category: one of "syntax", "unsupported", "semantic". Mirrors the
            error categories required by error_handling_and_diagnostics.feature.
    """

    def __init__(self, message: str, category: str = "syntax"):
        super().__init__(message)
        self.category = category


class UnsupportedTargetError(TranslationError):
    """Raised when the requested target language has no backend yet."""

    def __init__(self, target: str):
        super().__init__(
            f"No backend implemented yet for target '{target}'", category="unsupported"
        )
        self.target = target


def translate(basic_source: str, target: str = "python") -> str:
    """Translate BASIC source into `target` language source code.

    Raises:
        UnsupportedTargetError: if `target` is not a known/implemented backend.
        TranslationError: for syntax, semantic, or unsupported-construct problems
            in the BASIC source itself (category set accordingly).
        NotImplementedError: for backends that are recognized but not yet built.
    """
    if target not in SUPPORTED_TARGETS:
        raise UnsupportedTargetError(target)

    if target == "python":
        # TODO: implement the QuickBASIC-subset -> Python backend here.
        # See features/output_print.feature, features/variables_and_comments.feature,
        # etc. for the full requirements this must satisfy.
        raise NotImplementedError("Python backend not implemented yet")

    # Every other recognized target is a known future backend, not yet built.
    raise UnsupportedTargetError(target)
