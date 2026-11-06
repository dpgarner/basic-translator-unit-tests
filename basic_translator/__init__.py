"""BASIC-to-many-languages translator.

Public interface:
    translate(basic_source, target="python") -> generated source code (str)
    TranslationError, UnsupportedTargetError
"""

from __future__ import annotations

from .errors import TranslationError, UnsupportedTargetError

SUPPORTED_TARGETS = {"python", "typescript", "kotlin", "rust", "erlang"}

__all__ = ["translate", "TranslationError", "UnsupportedTargetError", "SUPPORTED_TARGETS"]


def translate(basic_source: str, target: str = "python") -> str:
    """Translate BASIC source into `target` language source code.

    Raises:
        UnsupportedTargetError: if `target` is not a known/implemented backend.
        TranslationError: for syntax, semantic, or unsupported-construct problems
            in the BASIC source itself (category set accordingly).
    """
    if target not in SUPPORTED_TARGETS:
        raise UnsupportedTargetError(target)

    if target == "python":
        from .codegen_python import generate_python

        return generate_python(basic_source)

    # Every other recognized target is a known future backend, not yet built.
    raise UnsupportedTargetError(target)
