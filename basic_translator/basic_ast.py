"""AST node definitions for the QuickBASIC-subset dialect."""

from __future__ import annotations

from dataclasses import dataclass, field


# --- Expressions -----------------------------------------------------------

class Expr:
    pass


@dataclass
class NumberLit(Expr):
    value: object


@dataclass
class StringLit(Expr):
    value: str


@dataclass
class Name(Expr):
    name: str


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr


@dataclass
class Call(Expr):
    """NAME(args) -- resolved at codegen time as array index, builtin, or
    user-defined function call, based on the symbol table."""

    name: str
    args: list


# --- Statements --------------------------------------------------------------

class Stmt:
    trailing_comment: str | None = None


@dataclass
class Print(Stmt):
    parts: list  # list[Expr]
    trailing_semicolon: bool = False
    trailing_comment: str | None = None


@dataclass
class Input(Stmt):
    prompt: str | None
    targets: list  # list[tuple[str, bool]] -- (normalized_name, is_string)
    trailing_comment: str | None = None


@dataclass
class Dim(Stmt):
    name: str
    var_type: str
    dims: list | None = None  # list[Expr] for array bounds, None for scalar
    trailing_comment: str | None = None


@dataclass
class ReDim(Stmt):
    name: str
    dims: list
    var_type: str
    preserve: bool = False
    trailing_comment: str | None = None


@dataclass
class LValue:
    name: str
    indices: list | None = None  # list[Expr] if this is an array element


@dataclass
class Let(Stmt):
    target: LValue
    value: Expr
    trailing_comment: str | None = None


@dataclass
class If(Stmt):
    cond: Expr
    then_body: list
    elif_clauses: list  # list[(Expr, list[Stmt])]
    else_body: list | None
    trailing_comment: str | None = None


@dataclass
class CaseClause:
    values: list  # list[Expr], empty means CASE ELSE
    is_else: bool
    body: list


@dataclass
class SelectCase(Stmt):
    expr: Expr
    cases: list  # list[CaseClause]
    trailing_comment: str | None = None


@dataclass
class For(Stmt):
    var: str
    start: Expr
    end: Expr
    step: Expr | None
    body: list
    trailing_comment: str | None = None


@dataclass
class While(Stmt):
    cond: Expr
    body: list
    trailing_comment: str | None = None


@dataclass
class Param:
    name: str
    param_type: str
    by_ref: bool = False
    default: Expr | None = None


@dataclass
class SubDecl(Stmt):
    name: str
    params: list  # list[Param]
    body: list
    trailing_comment: str | None = None


@dataclass
class FunctionDecl(Stmt):
    name: str
    params: list
    return_type: str
    body: list
    trailing_comment: str | None = None


@dataclass
class CallStmt(Stmt):
    name: str
    args: list
    trailing_comment: str | None = None


@dataclass
class Comment(Stmt):
    text: str


@dataclass
class OnErrorGoto(Stmt):
    label: str
    trailing_comment: str | None = None


@dataclass
class End(Stmt):
    """A bare END statement: stop the program successfully."""

    trailing_comment: str | None = None


@dataclass
class Program:
    statements: list = field(default_factory=list)
