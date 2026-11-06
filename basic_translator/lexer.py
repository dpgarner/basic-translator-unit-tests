"""Tokenizer for the QuickBASIC-subset BASIC dialect."""

from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = {
    "PRINT", "INPUT", "DIM", "LET", "AS", "INTEGER", "STRING", "DOUBLE",
    "SINGLE", "LONG", "IF", "THEN", "ELSE", "ELSEIF", "END", "SELECT",
    "CASE", "FOR", "TO", "STEP", "NEXT", "WHILE", "WEND", "SUB", "FUNCTION",
    "BYVAL", "BYREF", "REDIM", "PRESERVE", "GOTO", "GOSUB", "ON", "ERROR",
    "SHELL", "USING", "TRUE", "FALSE", "AND", "OR", "NOT", "MOD", "OPTION",
    "BASE",
}

SYMBOLS = [
    ("<=", "LE"), (">=", "GE"), ("<>", "NE"), ("=", "EQ"), ("<", "LT"),
    (">", "GT"), ("+", "PLUS"), ("-", "MINUS"), ("*", "STAR"), ("/", "SLASH"),
    ("(", "LPAREN"), (")", "RPAREN"), (",", "COMMA"), (";", "SEMI"),
    (":", "COLON"),
]


@dataclass
class Token:
    kind: str
    value: object
    line: int
    col: int

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"Token({self.kind!r}, {self.value!r}, line={self.line})"


class LexError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(message)
        self.line = line


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    col = 1
    i = 0
    n = len(source)

    def peek(offset: int = 0) -> str:
        j = i + offset
        return source[j] if j < n else ""

    while i < n:
        ch = source[i]

        if ch == "\n":
            tokens.append(Token("NEWLINE", "\n", line, col))
            i += 1
            line += 1
            col = 1
            continue

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Line continuation with underscore at end of line (QuickBASIC style)
        if ch == "_" and peek(1) in ("\n", "\r"):
            i += 1
            while i < n and source[i] in "\r\n":
                i += 1
                line += 1
            col = 1
            continue

        # Comments: REM ... or ' ...
        if ch == "'":
            start = i
            while i < n and source[i] != "\n":
                i += 1
            text = source[start + 1 : i].strip()
            tokens.append(Token("COMMENT", text, line, col))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] in "_"):
                i += 1
            # allow a trailing sigil ($ % ! #) as part of the identifier
            if i < n and source[i] in "$%!#":
                i += 1
            word = source[start:i]
            upper = word.upper()
            if upper == "REM":
                # REM comment: consume to end of line
                rest_start = i
                while i < n and source[i] != "\n":
                    i += 1
                text = source[rest_start:i].strip()
                tokens.append(Token("COMMENT", text, line, col))
                continue
            if upper in KEYWORDS:
                tokens.append(Token(upper, word, line, col))
            else:
                tokens.append(Token("IDENT", word, line, col))
            col += i - start
            continue

        if ch.isdigit() or (ch == "." and peek(1).isdigit()):
            start = i
            is_float = False
            while i < n and source[i].isdigit():
                i += 1
            if i < n and source[i] == ".":
                is_float = True
                i += 1
                while i < n and source[i].isdigit():
                    i += 1
            text = source[start:i]
            value = float(text) if is_float else int(text)
            tokens.append(Token("NUMBER", value, line, col))
            col += i - start
            continue

        if ch == '"':
            start_line, start_col = line, col
            i += 1
            buf = []
            while i < n:
                if source[i] == '"':
                    if peek(1) == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                if source[i] == "\n":
                    raise LexError("Unterminated string literal", line)
                buf.append(source[i])
                i += 1
            tokens.append(Token("STRING", "".join(buf), start_line, start_col))
            continue

        matched = False
        for sym, kind in SYMBOLS:
            if source.startswith(sym, i):
                tokens.append(Token(kind, sym, line, col))
                i += len(sym)
                col += len(sym)
                matched = True
                break
        if matched:
            continue

        raise LexError(f"Unexpected character {ch!r}", line)

    tokens.append(Token("NEWLINE", "\n", line, col))
    tokens.append(Token("EOF", None, line, col))
    return tokens
