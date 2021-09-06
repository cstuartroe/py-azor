from typing import List
from .tokens import BINOP_PRECS, Token
from .ast import Expression, Declaration


class Parser:
    SUFFIX_PRECS = {
        "COMPARISON": 1,
        "LOGIC": 0,
    }

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0
        self.lhs = False

    def parse(self):
        self.i = 0
        self.lhs = False
        stmts = []
        while self.i < len(self.tokens):
            stmts.append(self.grab_declaration())

        return stmts

    def next(self):
        if self.i >= len(self.tokens):
            self.tokens[-1].raise_error("Unexpected EOF")
        return self.tokens[self.i]

    def eof(self):
        return self.i == len(self.tokens)

    def expect(self, ttype: str):
        if self.next().ttype != ttype:
            self.next().raise_error("Expected " + ttype)
        tok = self.next()
        self.i += 1
        return tok

    def grab_declaration(self):
        label = self.expect("LABEL")

        if self.next().ttype == "(":
            argnames = self.grab_argnames()
        else:
            argnames = None

        self.expect('=')

        rhs = self.grab_expr(-1)

        return Declaration(label, argnames, rhs)

    def grab_argnames(self) -> List[str]:
        self.expect("(")

        argnames = []

        while self.next().ttype != ")":
            label = self.expect("LABEL")

            argnames.append(label.s)

            if self.next().ttype == ",":
                self.i += 1
            else:
                break

        self.expect(")")

        return argnames

    def grab_expr(self, suffix_precedence: int) -> Expression:
        if self.next().ttype in {"LABEL", "BOOL", "INT", "STRING", "CHAR"}:
            expr = Expression(self.next(), Expression.SIMPLE)
            self.i += 1

        elif self.next().s in '!-':
            t = self.next()
            self.i += 1
            expr = Expression(t, Expression.PREFIX)
            expr.right = self.grab_expr(10)

        elif self.next().ttype == "IF":
            expr = self.grab_if(suffix_precedence)

        elif self.next().ttype == "(":
            self.i += 1
            expr = self.grab_expr(-1)
            self.expect(")")

        else:
            self.next().raise_error("Invalid start to expression")

        return self.check_suffixes(expr, suffix_precedence)

    def grab_if(self, suffix_precedence: int) -> Expression:
        out = Expression(self.expect("IF"), "IF")

        out.condition = self.grab_expr(-1)

        self.expect("THEN")

        out.left = self.grab_expr(-1)

        self.expect('ELSE')

        out.right = self.grab_expr(suffix_precedence)

        return out

    def check_suffixes(self, expr: Expression, precedence: int) -> Expression:
        if self.eof():
            return expr

        t = self.next()

        if t.ttype == "(":
            call = Expression(expr.token, Expression.CALL)
            call.left = expr
            call.args = self.grab_args()
            return self.check_suffixes(call, precedence)

        elif t.ttype in ["BINOP", "COMPARISON", "LOGIC"]:
            op_prec = self.get_prec(t)

            if op_prec >= precedence:
                binop = Expression(t, Expression.BINOP)
                self.i += 1
                binop.left = expr
                binop.right = self.grab_expr(op_prec + 1)

                return self.check_suffixes(binop, precedence)

            else:
                return expr

        else:
            return expr

    @staticmethod
    def get_prec(token: Token):
        if token.ttype in Parser.SUFFIX_PRECS:
            return Parser.SUFFIX_PRECS[token.ttype]
        elif token.ttype == "BINOP":
            return BINOP_PRECS[token.s]
        else:
            raise ValueError

    def grab_args(self):
        self.expect("(")

        out = []
        while self.next().ttype not in "])}":
            out.append(self.grab_expr(-1))
            if self.next().ttype == ",":
                self.i += 1
            else:
                break

        self.expect(")")

        return out
