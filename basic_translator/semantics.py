"""Semantic analysis: undeclared-variable checking and symbol collection.

Runs after parsing, before code generation, so a program that parses fine but
references an undeclared variable is rejected before any backend-specific
code generation is attempted.
"""

from __future__ import annotations

from . import basic_ast as ast
from .errors import TranslationError

BUILTIN_FUNCS = {"len", "left", "right", "mid", "abs", "sqr", "int", "ucase", "lcase", "rnd"}


def collect_declared(stmts: list, declared: set) -> set:
    """Collect every name that is DIM'd, assigned, used as a loop variable,
    an INPUT target, or declared as a SUB/FUNCTION, anywhere in `stmts`
    (recursing into nested control-flow bodies but NOT into nested
    SUB/FUNCTION bodies, which get their own local scope)."""
    for s in stmts:
        if isinstance(s, (ast.Dim, ast.ReDim)):
            declared.add(s.name)
        elif isinstance(s, ast.Let):
            declared.add(s.target.name)
        elif isinstance(s, ast.Input):
            for name, _is_string in s.targets:
                declared.add(name)
        elif isinstance(s, ast.For):
            declared.add(s.var)
            collect_declared(s.body, declared)
        elif isinstance(s, ast.While):
            collect_declared(s.body, declared)
        elif isinstance(s, ast.If):
            collect_declared(s.then_body, declared)
            for _cond, body in s.elif_clauses:
                collect_declared(body, declared)
            if s.else_body:
                collect_declared(s.else_body, declared)
        elif isinstance(s, ast.SelectCase):
            for case in s.cases:
                collect_declared(case.body, declared)
        elif isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
            declared.add(s.name)
    return declared


def check_expr(expr, allowed: set):
    if isinstance(expr, ast.Name):
        if expr.name not in allowed and expr.name not in BUILTIN_FUNCS:
            raise TranslationError(
                f"Undeclared variable '{expr.name}'", category="semantic"
            )
    elif isinstance(expr, ast.BinOp):
        check_expr(expr.left, allowed)
        check_expr(expr.right, allowed)
    elif isinstance(expr, ast.UnaryOp):
        check_expr(expr.operand, allowed)
    elif isinstance(expr, ast.Call):
        if expr.name not in allowed and expr.name not in BUILTIN_FUNCS:
            raise TranslationError(
                f"Undeclared variable, array, or function '{expr.name}'",
                category="semantic",
            )
        for a in expr.args:
            check_expr(a, allowed)
    # NumberLit / StringLit: nothing to check


def check_stmts(stmts: list, allowed: set, base_declared: set):
    for s in stmts:
        check_stmt(s, allowed, base_declared)


def check_stmt(s, allowed: set, base_declared: set):
    if isinstance(s, ast.Print):
        for e in s.parts:
            check_expr(e, allowed)
    elif isinstance(s, ast.Input):
        pass
    elif isinstance(s, ast.Dim):
        if s.dims:
            for e in s.dims:
                check_expr(e, allowed)
    elif isinstance(s, ast.ReDim):
        for e in s.dims:
            check_expr(e, allowed)
    elif isinstance(s, ast.Let):
        if s.target.indices:
            for e in s.target.indices:
                check_expr(e, allowed)
        check_expr(s.value, allowed)
    elif isinstance(s, ast.If):
        check_expr(s.cond, allowed)
        check_stmts(s.then_body, allowed, base_declared)
        for cond, body in s.elif_clauses:
            check_expr(cond, allowed)
            check_stmts(body, allowed, base_declared)
        if s.else_body:
            check_stmts(s.else_body, allowed, base_declared)
    elif isinstance(s, ast.SelectCase):
        check_expr(s.expr, allowed)
        for case in s.cases:
            for v in case.values:
                check_expr(v, allowed)
            check_stmts(case.body, allowed, base_declared)
    elif isinstance(s, ast.For):
        check_expr(s.start, allowed)
        check_expr(s.end, allowed)
        if s.step:
            check_expr(s.step, allowed)
        check_stmts(s.body, allowed, base_declared)
    elif isinstance(s, ast.While):
        check_expr(s.cond, allowed)
        check_stmts(s.body, allowed, base_declared)
    elif isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
        local = set(base_declared)
        collect_declared(s.body, local)
        for p in s.params:
            local.add(p.name)
        local.add(s.name)
        check_stmts(s.body, local | BUILTIN_FUNCS, local)
    elif isinstance(s, ast.CallStmt):
        for a in s.args:
            check_expr(a, allowed)
    # Comment / OnErrorGoto: nothing to check


def validate_undeclared(program: ast.Program):
    declared = collect_declared(program.statements, set())
    check_stmts(program.statements, declared | BUILTIN_FUNCS, declared)


def collect_array_bounds(stmts: list, bounds: dict | None = None) -> dict:
    """Map array name -> list of literal upper bounds, for arrays whose DIM/REDIM
    dimensions are all literal numbers (so out-of-range literal indices can be
    caught statically, before code generation)."""
    if bounds is None:
        bounds = {}
    for s in stmts:
        if isinstance(s, (ast.Dim, ast.ReDim)):
            dims = getattr(s, "dims", None)
            if dims:
                literal_bounds = []
                all_literal = True
                for d in dims:
                    if isinstance(d, ast.NumberLit):
                        literal_bounds.append(int(d.value))
                    else:
                        all_literal = False
                        break
                if all_literal:
                    bounds[s.name] = literal_bounds
        elif isinstance(s, ast.For):
            collect_array_bounds(s.body, bounds)
        elif isinstance(s, ast.While):
            collect_array_bounds(s.body, bounds)
        elif isinstance(s, ast.If):
            collect_array_bounds(s.then_body, bounds)
            for _cond, body in s.elif_clauses:
                collect_array_bounds(body, bounds)
            if s.else_body:
                collect_array_bounds(s.else_body, bounds)
        elif isinstance(s, ast.SelectCase):
            for case in s.cases:
                collect_array_bounds(case.body, bounds)
        elif isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
            collect_array_bounds(s.body, bounds)
    return bounds


def _check_bounds_in_expr(e, bounds: dict):
    if isinstance(e, ast.Call):
        if e.name in bounds:
            declared_bounds = bounds[e.name]
            for i, a in enumerate(e.args):
                if isinstance(a, ast.NumberLit) and i < len(declared_bounds):
                    idx = a.value
                    if idx < 0 or idx > declared_bounds[i]:
                        raise TranslationError(
                            f"Array index {idx} out of bounds for '{e.name}' "
                            f"(valid range 0..{declared_bounds[i]})",
                            category="semantic",
                        )
        for a in e.args:
            _check_bounds_in_expr(a, bounds)
    elif isinstance(e, ast.BinOp):
        _check_bounds_in_expr(e.left, bounds)
        _check_bounds_in_expr(e.right, bounds)
    elif isinstance(e, ast.UnaryOp):
        _check_bounds_in_expr(e.operand, bounds)


def _check_bounds_in_lvalue(target: ast.LValue, bounds: dict):
    if not target.indices:
        return
    if target.name in bounds:
        declared_bounds = bounds[target.name]
        for i, idx in enumerate(target.indices):
            if isinstance(idx, ast.NumberLit) and i < len(declared_bounds):
                if idx.value < 0 or idx.value > declared_bounds[i]:
                    raise TranslationError(
                        f"Array index {idx.value} out of bounds for '{target.name}' "
                        f"(valid range 0..{declared_bounds[i]})",
                        category="semantic",
                    )
    for idx in target.indices:
        _check_bounds_in_expr(idx, bounds)


def check_bounds_stmts(stmts: list, bounds: dict):
    for s in stmts:
        if isinstance(s, ast.Print):
            for e in s.parts:
                _check_bounds_in_expr(e, bounds)
        elif isinstance(s, ast.Let):
            _check_bounds_in_lvalue(s.target, bounds)
            _check_bounds_in_expr(s.value, bounds)
        elif isinstance(s, ast.If):
            _check_bounds_in_expr(s.cond, bounds)
            check_bounds_stmts(s.then_body, bounds)
            for cond, body in s.elif_clauses:
                _check_bounds_in_expr(cond, bounds)
                check_bounds_stmts(body, bounds)
            if s.else_body:
                check_bounds_stmts(s.else_body, bounds)
        elif isinstance(s, ast.SelectCase):
            _check_bounds_in_expr(s.expr, bounds)
            for case in s.cases:
                for v in case.values:
                    _check_bounds_in_expr(v, bounds)
                check_bounds_stmts(case.body, bounds)
        elif isinstance(s, ast.For):
            _check_bounds_in_expr(s.start, bounds)
            _check_bounds_in_expr(s.end, bounds)
            if s.step:
                _check_bounds_in_expr(s.step, bounds)
            check_bounds_stmts(s.body, bounds)
        elif isinstance(s, ast.While):
            _check_bounds_in_expr(s.cond, bounds)
            check_bounds_stmts(s.body, bounds)
        elif isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
            check_bounds_stmts(s.body, bounds)
        elif isinstance(s, ast.CallStmt):
            for a in s.args:
                _check_bounds_in_expr(a, bounds)


def validate_array_bounds(program: ast.Program):
    bounds = collect_array_bounds(program.statements)
    check_bounds_stmts(program.statements, bounds)


def collect_symbols(stmts: list, array_names=None, callable_names=None):
    if array_names is None:
        array_names = set()
    if callable_names is None:
        callable_names = set()
    for s in stmts:
        if isinstance(s, ast.Dim) and s.dims is not None:
            array_names.add(s.name)
        elif isinstance(s, ast.ReDim):
            array_names.add(s.name)
        elif isinstance(s, (ast.SubDecl, ast.FunctionDecl)):
            callable_names.add(s.name)
            collect_symbols(s.body, array_names, callable_names)
        elif isinstance(s, ast.For):
            collect_symbols(s.body, array_names, callable_names)
        elif isinstance(s, ast.While):
            collect_symbols(s.body, array_names, callable_names)
        elif isinstance(s, ast.If):
            collect_symbols(s.then_body, array_names, callable_names)
            for _cond, body in s.elif_clauses:
                collect_symbols(body, array_names, callable_names)
            if s.else_body:
                collect_symbols(s.else_body, array_names, callable_names)
        elif isinstance(s, ast.SelectCase):
            for case in s.cases:
                collect_symbols(case.body, array_names, callable_names)
    return array_names, callable_names
