"""BASIC-to-many-languages translator.

Public interface:
    translate(basic_source, target="python", *, warnings=None, diagnostics=None) -> str
    translate_many(basic_source, targets=None) -> list[TargetResult]
    TranslationError, UnsupportedTargetError, TargetResult
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import TranslationError, UnsupportedTargetError

SUPPORTED_TARGETS = {"python", "typescript", "kotlin", "rust", "erlang"}

__all__ = [
    "translate",
    "translate_many",
    "TargetResult",
    "TranslationError",
    "UnsupportedTargetError",
    "SUPPORTED_TARGETS",
]


@dataclass
class TargetResult:
    """One target's outcome in a batch run."""

    target: str
    ok: bool
    output: str | None = None
    error: str | None = None
    category: str | None = None


def translate(
    basic_source: str,
    target: str = "python",
    *,
    warnings: list | None = None,
    diagnostics: str | Path | None = None,
) -> str:
    """Translate BASIC source into `target` language source code.

    Args:
        warnings: optional list that collected warnings -- constructs that
            translate but lose meaning -- are appended to.
        diagnostics: optional path; a JSON report of the run is written there,
            including when the run fails.

    Raises:
        UnsupportedTargetError: if `target` is not a known/implemented backend.
        TranslationError: for syntax, semantic, or unsupported-construct problems
            in the BASIC source itself (category set accordingly).
    """
    collected = [] if warnings is None else warnings
    if target not in SUPPORTED_TARGETS:
        error = UnsupportedTargetError(target)
        _write_diagnostics(diagnostics, target, collected, error)
        raise error

    try:
        if target == "python":
            from .codegen_python import generate_python

            output = generate_python(basic_source, warnings=collected)
        else:
            # Every other recognized target is a known future backend, not yet built.
            raise UnsupportedTargetError(target)
    except TranslationError as error:
        _write_diagnostics(diagnostics, target, collected, error)
        raise

    _write_diagnostics(diagnostics, target, collected, None)
    return output


def translate_many(basic_source: str, targets=None) -> list:
    """Translate one program for several targets and report each outcome.

    Targets default to every supported language, in sorted order. A target with
    no backend is reported as a failed result rather than aborting the run.
    """
    chosen = sorted(SUPPORTED_TARGETS if targets is None else targets)
    results = []
    for name in chosen:
        collected = []
        try:
            output = translate(basic_source, target=name, warnings=collected)
        except TranslationError as error:
            results.append(TargetResult(name, False, None, str(error), error.category))
        else:
            results.append(TargetResult(name, True, output, None, None))
    return results


def _write_diagnostics(path, target, warnings, error) -> None:
    if path is None:
        return
    report = {
        "target": target,
        "ok": error is None,
        "warnings": list(warnings),
        "error": None
        if error is None
        else {
            "category": error.category,
            "message": str(error),
            "line": getattr(error, "line", None),
        },
    }
    Path(path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
