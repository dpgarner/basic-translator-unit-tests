"""Translate the BASIC AST into Python source code."""

from __future__ import annotations

from . import basic_ast as ast
from .errors import TranslationError
from .parser import parse
from .semantics import collect_symbols, validate_array_bounds, validate_undeclared

INDENT = "    "
RETURN_VAR = "_result"

RUNTIME_PRELUDE = '''\
import sys as _sys
import random as _random
import math as _math


def _fmt(_v):
    """Render a value the way the feature spec expects: numbers print plainly,
    without QuickBASIC's sign column; strings are untouched."""
    if isinstance(_v, bool):
        _v = int(_v)
    if isinstance(_v, float) and _v.is_integer():
        return str(int(_v))
    return str(_v)


def _basic_print(*_parts):
    """Join PRINT items: a number directly after another number takes the single
    space its sign column would have occupied; strings keep their own spacing."""
    _out = ""
    _prev_numeric = False
    for _v in _parts:
        _numeric = isinstance(_v, (int, float)) and not isinstance(_v, bool)
        if _numeric and _prev_numeric:
            _out += " "
        _out += _fmt(_v)
        _prev_numeric = _numeric
    return _out


def _basic_input(_prompt=None):
    if _prompt is not None:
        _sys.stdout.write(_prompt)
        _sys.stdout.flush()
    _line = _sys.stdin.readline()
    if _line.endswith("\\n"):
        _line = _line[:-1]
    return _line


def _basic_int_input(_prompt=None):
    _raw = _basic_input(_prompt).strip()
    try:
        return int(_raw)
    except ValueError:
        return 0


def _basic_left(_s, _n):
    return _s[: max(0, int(_n))]


def _basic_right(_s, _n):
    _n = max(0, int(_n))
    return _s[-_n:] if _n else ""


def _basic_mid(_s, _start, _length=None):
    _start = max(1, int(_start)) - 1
    if _start >= len(_s):
        return ""
    if _length is None:
        return _s[_start:]
    return _s[_start:_start + max(0, int(_length))]


def _basic_int(_x):
    return _math.floor(_x)


def _basic_sqr(_x):
    if _x < 0:
        raise ValueError("Illegal function call: SQR of a negative number")
    return _math.sqrt(_x)


def _basic_range(_start, _end, _step):
    if _step == 0:
        raise ValueError("FOR loop STEP cannot be zero")
    _cur = _start
    if _step > 0:
        while _cur <= _end:
            yield _cur
            _cur += _step
    else:
        while _cur >= _end:
            yield _cur
            _cur += _step
'''

BINOP_PY = {
    "PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/", "MOD": "%",
    "EQ": "==", "NE": "!=", "LT": "<", "GT": ">", "LE": "<=", "GE": ">=",
    "AND": "and", "OR": "or",
}

TYPE_DEFAULTS = {
    "INTEGER": "0", "LONG": "0", "SINGLE": "0.0", "DOUBLE": "0.0", "STRING": '""',
}


def pyname(name: str) -> str:
    return f"v_{name}"


class CodegenCtx:
    def __init__(self, array_names: set, callable_names: set):
        self.array_names = array_names
        self.callable_names = callable_names
        self.current_function_name: str | None = None
        self._temp_counter = 0

    def next_temp(self) -> int:
        self._temp_counter += 1
        return self._temp_counter


def default_for_type(var_type: str) -> str:
    return TYPE_DEFAULTS.get(var_type.upper(), "0")


def expr_to_py(e, ctx: CodegenCtx) -> str:
    if isinstance(e, ast.NumberLit):
        return repr(e.value)
    if isinstance(e, ast.StringLit):
        return repr(e.value)
    if isinstance(e, ast.Name):
        if e.name == "rnd":
            return "_random.random()"
        return pyname(e.name)
    if isinstance(e, ast.UnaryOp):
        inner = expr_to_py(e.operand, ctx)
        if e.op == "MINUS":
            return f"(-{inner})"
        if e.op == "NOT":
            return f"(not {inner})"
        raise TranslationError(f"Unknown unary operator {e.op}", category="syntax")
    if isinstance(e, ast.BinOp):
        left = expr_to_py(e.left, ctx)
        right = expr_to_py(e.right, ctx)
        py_op = BINOP_PY[e.op]
        return f"({left} {py_op} {right})"
    if isinstance(e, ast.Call):
        return _call_to_py(e, ctx)
    raise TranslationError(f"Unknown expression node {e!r}", category="syntax")


def _call_to_py(e: ast.Call, ctx: CodegenCtx) -> str:
    args = [expr_to_py(a, ctx) for a in e.args]
    name = e.name

    if name == "len":
        return f"len({args[0]})"
    if name == "left":
        return f"_basic_left({args[0]}, {args[1]})"
    if name == "right":
        return f"_basic_right({args[0]}, {args[1]})"
    if name == "mid":
        if len(args) == 2:
            return f"_basic_mid({args[0]}, {args[1]})"
        return f"_basic_mid({args[0]}, {args[1]}, {args[2]})"
    if name == "abs":
        return f"abs({args[0]})"
    if name == "sqr":
        return f"_basic_sqr({args[0]})"
    if name == "int":
        return f"_basic_int({args[0]})"
    if name == "ucase":
        return f"({args[0]}).upper()"
    if name == "lcase":
        return f"({args[0]}).lower()"
    if name == "rnd":
        return "_random.random()"

    if name in ctx.callable_names:
        return f"{pyname(name)}({', '.join(args)})"

    # Array element access (default assumption for any other NAME(args) call).
    base = pyname(name)
    for a in args:
        base += f"[{a}]"
    return base


def _array_init_expr(dims: list, var_type: str, ctx: CodegenCtx) -> str:
    expr_code = default_for_type(var_type)
    for dim in reversed(dims):
        size_code = f"(({expr_to_py(dim, ctx)}) + 1)"
        expr_code = f"[{expr_code} for _ in range({size_code})]"
    return expr_code


def gen_stmts(stmts: list, indent: int, ctx: CodegenCtx) -> list:
    lines: list = []
    for s in stmts:
        stmt_lines = gen_stmt(s, indent, ctx)
        if s.trailing_comment and stmt_lines:
            stmt_lines[-1] = f"{stmt_lines[-1]}  # {s.trailing_comment}"
        lines.extend(stmt_lines)
    return lines


def _line(indent: int, text: str) -> str:
    return f"{INDENT * indent}{text}"


def gen_stmt(s, indent: int, ctx: CodegenCtx) -> list:
    if isinstance(s, ast.Comment):
        text = f"# {s.text}" if s.text else "#"
        return [_line(indent, text)]

    if isinstance(s, ast.OnErrorGoto):
        return [_line(
            indent,
            f"# ON ERROR GOTO {s.label} (approximated: error handling not translated)",
        )]

    if isinstance(s, ast.Print):
        parts_code = [expr_to_py(p, ctx) for p in s.parts]
        joined = f"_basic_print({', '.join(parts_code)})" if parts_code else '""'
        if s.trailing_semicolon:
            if not parts_code:
                return []
            return [_line(indent, f"_sys.stdout.write({joined})")]
        return [_line(indent, f"print({joined})")]

    if isinstance(s, ast.Input):
        prompt_code = repr(s.prompt) if s.prompt is not None else "None"
        if len(s.targets) == 1:
            name, is_string = s.targets[0]
            fn = "_basic_input" if is_string else "_basic_int_input"
            return [_line(indent, f"{pyname(name)} = {fn}({prompt_code})")]
        temp = ctx.next_temp()
        line_var = f"_input_line_{temp}"
        parts_var = f"_input_parts_{temp}"
        lines = [
            _line(indent, f"{line_var} = _basic_input({prompt_code})"),
            _line(indent, f"{parts_var} = [_p.strip() for _p in {line_var}.split(',')]"),
        ]
        for i, (name, is_string) in enumerate(s.targets):
            if is_string:
                lines.append(_line(indent, f"{pyname(name)} = {parts_var}[{i}] if len({parts_var}) > {i} else ''"))
            else:
                lines.append(_line(
                    indent,
                    f"{pyname(name)} = int({parts_var}[{i}]) if len({parts_var}) > {i} and {parts_var}[{i}] else 0",
                ))
        return lines

    if isinstance(s, ast.Dim):
        if s.dims is None:
            return [_line(indent, f"{pyname(s.name)} = {default_for_type(s.var_type)}")]
        return [_line(indent, f"{pyname(s.name)} = {_array_init_expr(s.dims, s.var_type, ctx)}")]

    if isinstance(s, ast.ReDim):
        return [_line(indent, f"{pyname(s.name)} = {_array_init_expr(s.dims, s.var_type, ctx)}")]

    if isinstance(s, ast.Let):
        value_code = expr_to_py(s.value, ctx)
        if s.target.indices:
            base = pyname(s.target.name)
            for idx in s.target.indices:
                base += f"[{expr_to_py(idx, ctx)}]"
            return [_line(indent, f"{base} = {value_code}")]
        if ctx.current_function_name is not None and s.target.name == ctx.current_function_name:
            return [_line(indent, f"{RETURN_VAR} = {value_code}")]
        return [_line(indent, f"{pyname(s.target.name)} = {value_code}")]

    if isinstance(s, ast.If):
        lines = [_line(indent, f"if {expr_to_py(s.cond, ctx)}:")]
        body = gen_stmts(s.then_body, indent + 1, ctx) or [_line(indent + 1, "pass")]
        lines.extend(body)
        for econd, ebody in s.elif_clauses:
            lines.append(_line(indent, f"elif {expr_to_py(econd, ctx)}:"))
            body = gen_stmts(ebody, indent + 1, ctx) or [_line(indent + 1, "pass")]
            lines.extend(body)
        if s.else_body is not None:
            lines.append(_line(indent, "else:"))
            body = gen_stmts(s.else_body, indent + 1, ctx) or [_line(indent + 1, "pass")]
            lines.extend(body)
        return lines

    if isinstance(s, ast.SelectCase):
        temp = f"_case_{ctx.next_temp()}"
        lines = [_line(indent, f"{temp} = {expr_to_py(s.expr, ctx)}")]
        else_case = None
        first = True
        for case in s.cases:
            if case.is_else:
                else_case = case
                continue
            cond = " or ".join(f"{temp} == {expr_to_py(v, ctx)}" for v in case.values)
            kw = "if" if first else "elif"
            lines.append(_line(indent, f"{kw} {cond}:"))
            body = gen_stmts(case.body, indent + 1, ctx) or [_line(indent + 1, "pass")]
            lines.extend(body)
            first = False
        if else_case is not None:
            kw = "if True" if first else "else"
            lines.append(_line(indent, f"{kw}:"))
            body = gen_stmts(else_case.body, indent + 1, ctx) or [_line(indent + 1, "pass")]
            lines.extend(body)
        return lines

    if isinstance(s, ast.For):
        start_code = expr_to_py(s.start, ctx)
        end_code = expr_to_py(s.end, ctx)
        step_code = expr_to_py(s.step, ctx) if s.step is not None else "1"
        lines = [_line(
            indent,
            f"for {pyname(s.var)} in _basic_range({start_code}, {end_code}, {step_code}):",
        )]
        body = gen_stmts(s.body, indent + 1, ctx) or [_line(indent + 1, "pass")]
        lines.extend(body)
        return lines

    if isinstance(s, ast.While):
        lines = [_line(indent, f"while {expr_to_py(s.cond, ctx)}:")]
        body = gen_stmts(s.body, indent + 1, ctx) or [_line(indent + 1, "pass")]
        lines.extend(body)
        return lines

    if isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
        params_code = ", ".join(
            f"{pyname(p.name)}" + (f"={expr_to_py(p.default, ctx)}" if p.default is not None else "")
            for p in s.params
        )
        lines = [_line(indent, f"def {pyname(s.name)}({params_code}):")]
        prev_fn = ctx.current_function_name
        if isinstance(s, ast.FunctionDecl):
            ctx.current_function_name = s.name
            body_lines = [_line(indent + 1, f"{RETURN_VAR} = {default_for_type(s.return_type)}")]
            body_lines.extend(gen_stmts(s.body, indent + 1, ctx))
            body_lines.append(_line(indent + 1, f"return {RETURN_VAR}"))
        else:
            ctx.current_function_name = None
            body_lines = gen_stmts(s.body, indent + 1, ctx) or [_line(indent + 1, "pass")]
        ctx.current_function_name = prev_fn
        lines.extend(body_lines)
        return lines

    if isinstance(s, ast.CallStmt):
        args_code = ", ".join(expr_to_py(a, ctx) for a in s.args)
        return [_line(indent, f"{pyname(s.name)}({args_code})")]

    raise TranslationError(f"Unknown statement node {s!r}", category="syntax")


def generate_python(source: str) -> str:
    program = parse(source)
    validate_undeclared(program)
    validate_array_bounds(program)
    array_names, callable_names = collect_symbols(program.statements)
    ctx = CodegenCtx(array_names, callable_names)
    body_lines = gen_stmts(program.statements, 0, ctx)
    if not body_lines:
        body_lines = ["pass"]
    return RUNTIME_PRELUDE + "\n" + "\n".join(body_lines) + "\n"
