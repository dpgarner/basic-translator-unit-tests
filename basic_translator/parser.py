"""Recursive-descent parser for the QuickBASIC-subset dialect."""

from __future__ import annotations

from . import basic_ast as ast
from .errors import TranslationError
from .lexer import Token, tokenize

END_OF_STMT = {"NEWLINE", "COLON", "EOF", "COMMENT"}
COMPARISON_OPS = {"EQ", "NE", "LT", "GT", "LE", "GE"}
ADDITIVE_OPS = {"PLUS", "MINUS"}
MULT_OPS = {"STAR", "SLASH", "MOD"}


def normalize_name(raw: str) -> str:
    if raw and raw[-1] in "$%!#":
        raw = raw[:-1]
    return raw.lower()


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        # Loops still waiting to be closed by an inner NEXT that listed their
        # variables too ("NEXT j, i").
        self.next_extra_closures = 0

    # --- token helpers -----------------------------------------------------

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def check(self, kind: str) -> bool:
        return self.current().kind == kind

    def check_seq(self, *kinds: str) -> bool:
        return all(self.peek(i).kind == k for i, k in enumerate(kinds))

    def advance(self) -> Token:
        tok = self.current()
        if tok.kind != "EOF":
            self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        if not self.check(kind):
            tok = self.current()
            raise TranslationError(
                f"Expected {kind} but found {tok.kind} ({tok.value!r})",
                category="syntax",
                line=tok.line,
            )
        return self.advance()

    def at_statement_end(self) -> bool:
        return self.current().kind in END_OF_STMT

    def skip_separators(self):
        while self.check("NEWLINE") or self.check("COLON"):
            self.advance()

    # --- top level -----------------------------------------------------------

    def parse_program(self) -> ast.Program:
        stmts = self.parse_statements(until_check=None)
        self.expect("EOF")
        return ast.Program(stmts)

    def parse_statements(self, until_check) -> list:
        stmts = []
        while True:
            self.skip_separators()
            if self.check("EOF"):
                break
            if until_check and until_check():
                break
            stmt = self.parse_statement()
            if self.check("COMMENT") and stmt is not None:
                stmt.trailing_comment = self.advance().value
            elif self.check("COMMENT"):
                self.advance()
            if stmt is not None:
                stmts.append(stmt)
            if self.check("NEWLINE") or self.check("COLON"):
                self.advance()
            elif self.check("EOF"):
                break
            elif until_check and until_check():
                break
            else:
                tok = self.current()
                raise TranslationError(
                    f"Unexpected token {tok.kind} ({tok.value!r}) after statement",
                    category="syntax",
                    line=tok.line,
                )
        return stmts

    # --- statement dispatch --------------------------------------------------

    def parse_statement(self):
        tok = self.current()

        if tok.kind == "ON":
            return self.parse_on_error_goto()
        if tok.kind == "NUMBER" and self.peek(1).kind == "GOTO":
            raise TranslationError(
                "GOTO / line-number based control flow is out of scope for this "
                "translator's QuickBASIC-subset dialect",
                category="unsupported",
                line=tok.line,
            )
        if tok.kind == "GOTO":
            raise TranslationError(
                "GOTO is out of scope for this translator's QuickBASIC-subset dialect",
                category="unsupported",
                line=tok.line,
            )
        if tok.kind == "SHELL":
            raise TranslationError(
                "SHELL is not supported -- raw OS shell execution is intentionally "
                "excluded from all backends for safety reasons",
                category="unsupported",
                line=tok.line,
            )
        if tok.kind == "END":
            # END IF / END SUB / END FUNCTION / END SELECT are consumed by their
            # own statement parsers, so a bare END here ends the program.
            self.advance()
            return ast.End()
        if tok.kind == "COMMENT":
            self.advance()
            return ast.Comment(tok.value)
        if tok.kind == "OPTION":
            self.advance()
            self.expect("BASE")
            self.expect("NUMBER")
            return None
        if tok.kind == "PRINT":
            return self.parse_print()
        if tok.kind == "INPUT":
            return self.parse_input()
        if tok.kind == "DIM":
            return self.parse_dim()
        if tok.kind == "REDIM":
            return self.parse_redim()
        if tok.kind == "LET":
            return self.parse_ident_statement()
        if tok.kind == "IF":
            return self.parse_if()
        if tok.kind == "SELECT":
            return self.parse_select_case()
        if tok.kind == "FOR":
            return self.parse_for()
        if tok.kind == "WHILE":
            return self.parse_while()
        if tok.kind == "SUB":
            return self.parse_sub()
        if tok.kind == "FUNCTION":
            return self.parse_function()
        if tok.kind == "IDENT":
            return self.parse_ident_statement()

        raise TranslationError(
            f"Unexpected token {tok.kind} ({tok.value!r}) at start of statement",
            category="syntax",
            line=tok.line,
        )

    # --- individual statements ------------------------------------------------

    def parse_on_error_goto(self):
        self.expect("ON")
        self.expect("ERROR")
        self.expect("GOTO")
        label_tok = self.expect("IDENT")
        return ast.OnErrorGoto(label_tok.value)

    def parse_print(self):
        self.expect("PRINT")
        if self.check("USING"):
            tok = self.current()
            raise TranslationError(
                "PRINT USING is not supported by this translator",
                category="unsupported",
                line=tok.line,
            )
        parts = []
        trailing_semicolon = False
        if not self.at_statement_end():
            parts.append(self.parse_expr())
            while self.check("SEMI") or self.check("COMMA"):
                self.advance()
                if self.at_statement_end():
                    trailing_semicolon = True
                    break
                parts.append(self.parse_expr())
        return ast.Print(parts, trailing_semicolon)

    def parse_input(self):
        self.expect("INPUT")
        prompt = None
        if self.check("STRING"):
            prompt = self.advance().value
            # QuickBASIC accepts either separator after the prompt.
            if not (self.check("SEMI") or self.check("COMMA")):
                self.expect("COMMA")
            self.advance()
        targets = [self._input_target()]
        while self.check("COMMA"):
            self.advance()
            targets.append(self._input_target())
        return ast.Input(prompt, targets)

    def _input_target(self):
        tok = self.expect("IDENT")
        is_string = tok.value.endswith("$")
        return (normalize_name(tok.value), is_string)

    def parse_type(self) -> str:
        tok = self.current()
        if tok.kind in {"INTEGER", "STRING", "DOUBLE", "SINGLE", "LONG"}:
            self.advance()
            return tok.kind
        tok2 = self.expect("IDENT")
        return tok2.value.upper()

    def parse_dim(self):
        self.expect("DIM")
        name = normalize_name(self.expect("IDENT").value)
        dims = None
        if self.check("LPAREN"):
            self.advance()
            dims = [self.parse_expr()]
            while self.check("COMMA"):
                self.advance()
                dims.append(self.parse_expr())
            self.expect("RPAREN")
        var_type = "INTEGER"
        if self.check("AS"):
            self.advance()
            var_type = self.parse_type()
        return ast.Dim(name, var_type, dims)

    def parse_redim(self):
        self.expect("REDIM")
        preserve = False
        if self.check("PRESERVE"):
            self.advance()
            preserve = True
        name = normalize_name(self.expect("IDENT").value)
        self.expect("LPAREN")
        dims = [self.parse_expr()]
        while self.check("COMMA"):
            self.advance()
            dims.append(self.parse_expr())
        self.expect("RPAREN")
        var_type = "INTEGER"
        if self.check("AS"):
            self.advance()
            var_type = self.parse_type()
        return ast.ReDim(name, dims, var_type, preserve)

    def parse_ident_statement(self):
        if self.check("LET"):
            self.advance()
        name_tok = self.expect("IDENT")
        name = normalize_name(name_tok.value)
        if self.check("LPAREN"):
            self.advance()
            indices = self.parse_expr_list_until("RPAREN")
            self.expect("RPAREN")
            if self.check("EQ"):
                self.advance()
                value = self.parse_expr()
                return ast.Let(ast.LValue(name, indices), value)
            return ast.CallStmt(name, indices)
        if self.check("EQ"):
            self.advance()
            value = self.parse_expr()
            return ast.Let(ast.LValue(name), value)
        args = []
        if not self.at_statement_end():
            args.append(self.parse_expr())
            while self.check("COMMA"):
                self.advance()
                args.append(self.parse_expr())
        return ast.CallStmt(name, args)

    def parse_if(self):
        self.expect("IF")
        cond = self.parse_expr()
        if not self.check("THEN"):
            tok = self.current()
            raise TranslationError(
                "Expected THEN after IF condition",
                category="syntax",
                line=tok.line,
            )
        self.expect("THEN")
        if self.check("NEWLINE") or self.check("COMMENT"):
            if self.check("COMMENT"):
                self.advance()
            self.advance()  # NEWLINE
            then_body = self.parse_statements(
                until_check=lambda: self.check("ELSEIF")
                or self.check("ELSE")
                or self.check_seq("END", "IF")
            )
            elif_clauses = []
            while self.check("ELSEIF"):
                self.advance()
                econd = self.parse_expr()
                self.expect("THEN")
                self.skip_separators()
                ebody = self.parse_statements(
                    until_check=lambda: self.check("ELSEIF")
                    or self.check("ELSE")
                    or self.check_seq("END", "IF")
                )
                elif_clauses.append((econd, ebody))
            else_body = None
            if self.check("ELSE"):
                self.advance()
                self.skip_separators()
                else_body = self.parse_statements(
                    until_check=lambda: self.check_seq("END", "IF")
                )
            self.expect("END")
            self.expect("IF")
            return ast.If(cond, then_body, elif_clauses, else_body)
        else:
            then_stmt = self.parse_statement()
            else_body = None
            if self.check("ELSE"):
                self.advance()
                else_body = [self.parse_statement()]
            return ast.If(cond, [then_stmt], [], else_body)

    def parse_select_case(self):
        self.expect("SELECT")
        self.expect("CASE")
        expr = self.parse_expr()
        self.skip_separators()
        cases = []
        while self.check("CASE"):
            self.advance()
            if self.check("ELSE"):
                self.advance()
                values, is_else = [], True
            else:
                is_else = False
                values = [self.parse_expr()]
                if self.check("TO"):
                    tok = self.current()
                    raise TranslationError(
                        "CASE ... TO range clauses are not supported",
                        category="unsupported",
                        line=tok.line,
                    )
                while self.check("COMMA"):
                    self.advance()
                    values.append(self.parse_expr())
            self.skip_separators()
            body = self.parse_statements(
                until_check=lambda: self.check("CASE") or self.check_seq("END", "SELECT")
            )
            cases.append(ast.CaseClause(values, is_else, body))
        self.expect("END")
        self.expect("SELECT")
        return ast.SelectCase(expr, cases)

    def parse_for(self):
        self.expect("FOR")
        var = normalize_name(self.expect("IDENT").value)
        self.expect("EQ")
        start = self.parse_expr()
        self.expect("TO")
        end = self.parse_expr()
        step = None
        if self.check("STEP"):
            self.advance()
            step = self.parse_expr()
        self.skip_separators()
        body = self.parse_statements(
            until_check=lambda: self.check("NEXT") or self.next_extra_closures > 0
        )
        if self.next_extra_closures > 0:
            # An inner NEXT listed this loop's variable too, so it is closed.
            self.next_extra_closures -= 1
            return ast.For(var, start, end, step, body)
        self.expect("NEXT")
        closed = 0
        if self.check("IDENT"):
            self.advance()
            closed = 1
            # NEXT j, i closes several loops with one statement.
            while self.check("COMMA"):
                self.advance()
                self.expect("IDENT")
                closed += 1
        self.next_extra_closures = closed - 1 if closed > 1 else 0
        return ast.For(var, start, end, step, body)

    def parse_while(self):
        self.expect("WHILE")
        cond = self.parse_expr()
        self.skip_separators()
        body = self.parse_statements(until_check=lambda: self.check("WEND"))
        self.expect("WEND")
        return ast.While(cond, body)

    def parse_param(self) -> ast.Param:
        by_ref = False
        if self.check("BYVAL"):
            self.advance()
        elif self.check("BYREF"):
            self.advance()
            by_ref = True
        name = normalize_name(self.expect("IDENT").value)
        ptype = "INTEGER"
        if self.check("AS"):
            self.advance()
            ptype = self.parse_type()
        default = None
        if self.check("EQ"):
            self.advance()
            default = self.parse_expr()
        return ast.Param(name, ptype, by_ref, default)

    def parse_params(self) -> list:
        params = []
        if self.check("LPAREN"):
            self.advance()
            if not self.check("RPAREN"):
                params.append(self.parse_param())
                while self.check("COMMA"):
                    self.advance()
                    params.append(self.parse_param())
            self.expect("RPAREN")
        return params

    def parse_sub(self):
        self.expect("SUB")
        name = normalize_name(self.expect("IDENT").value)
        params = self.parse_params()
        self.skip_separators()
        body = self.parse_statements(
            until_check=lambda: self.check_seq("END", "SUB")
        )
        self.expect("END")
        self.expect("SUB")
        return ast.SubDecl(name, params, body)

    def parse_function(self):
        self.expect("FUNCTION")
        name = normalize_name(self.expect("IDENT").value)
        params = self.parse_params()
        return_type = "INTEGER"
        if self.check("AS"):
            self.advance()
            return_type = self.parse_type()
        self.skip_separators()
        body = self.parse_statements(
            until_check=lambda: self.check_seq("END", "FUNCTION")
        )
        self.expect("END")
        self.expect("FUNCTION")
        return ast.FunctionDecl(name, params, return_type, body)

    # --- expressions -----------------------------------------------------------

    def parse_expr_list_until(self, end_kind: str) -> list:
        parts = []
        if not self.check(end_kind):
            parts.append(self.parse_expr())
            while self.check("COMMA"):
                self.advance()
                parts.append(self.parse_expr())
        return parts

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check("OR"):
            self.advance()
            right = self.parse_and()
            left = ast.BinOp("OR", left, right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.check("AND"):
            self.advance()
            right = self.parse_comparison()
            left = ast.BinOp("AND", left, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.current().kind in COMPARISON_OPS:
            op = self.advance().kind
            right = self.parse_additive()
            left = ast.BinOp(op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current().kind in ADDITIVE_OPS:
            op = self.advance().kind
            right = self.parse_multiplicative()
            left = ast.BinOp(op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.current().kind in MULT_OPS:
            op = self.advance().kind
            right = self.parse_unary()
            left = ast.BinOp(op, left, right)
        return left

    def parse_unary(self):
        if self.check("MINUS"):
            self.advance()
            return ast.UnaryOp("MINUS", self.parse_unary())
        if self.check("NOT"):
            self.advance()
            return ast.UnaryOp("NOT", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()
        if tok.kind == "NUMBER":
            self.advance()
            return ast.NumberLit(tok.value)
        if tok.kind == "STRING":
            self.advance()
            return ast.StringLit(tok.value)
        if tok.kind == "TRUE":
            self.advance()
            return ast.NumberLit(1)
        if tok.kind == "FALSE":
            self.advance()
            return ast.NumberLit(0)
        if tok.kind == "LPAREN":
            self.advance()
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
        if tok.kind == "IDENT":
            self.advance()
            name = normalize_name(tok.value)
            if self.check("LPAREN"):
                self.advance()
                args = self.parse_expr_list_until("RPAREN")
                self.expect("RPAREN")
                return ast.Call(name, args)
            return ast.Name(name)
        raise TranslationError(
            f"Unexpected token {tok.kind} ({tok.value!r}) in expression",
            category="syntax",
            line=tok.line,
        )


def parse(source: str) -> ast.Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()
