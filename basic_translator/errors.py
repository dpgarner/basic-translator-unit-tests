"""Error types for the BASIC translator."""

from __future__ import annotations


class TranslationError(Exception):
    """Raised when BASIC source cannot be translated.

    Attributes:
        category: one of "syntax", "unsupported", "semantic".
    """

    def __init__(self, message: str, category: str = "syntax", line: int | None = None):
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
        self.category = category
        self.line = line


class UnsupportedTargetError(TranslationError):
    """Raised when the requested target language has no backend yet."""

    def __init__(self, target: str):
        super().__init__(
            f"No backend implemented yet for target '{target}'", category="unsupported"
        )
        self.target = target
