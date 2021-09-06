from typing import List
from src.ast import Declaration, Expression


BINOPS = {
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a // b,
    '%': lambda a, b: a % b,
    '**': lambda a, b: a ** b,

    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    '<': lambda a, b: a < b,
    '>': lambda a, b: a > b,
    '<=': lambda a, b: a <= b,
    '>=': lambda a, b: a >= b,

    '&': lambda a, b: a and b,
    '|': lambda a, b: a or b,
}


class Interpreter:
    def __init__(self, stmts: List[Declaration]):
        self.stmts_by_label = {}
        for stmt in stmts:
            self.stmts_by_label[stmt.label.s] = stmt

        self.symbol_table = {}

    def main(self):
        return self.evaluate_global("main")()

    def evaluate_global(self, name):
        if name not in self.symbol_table:
            stmt = self.stmts_by_label[name]

            if stmt.argnames is None:
                val = self.evaluate_expression(stmt.rhs, {})

            else:
                def val(*args):
                    env = dict(zip(stmt.argnames, args))
                    return self.evaluate_expression(stmt.rhs, env)

            self.symbol_table[name] = val

        return self.symbol_table[name]

    def evaluate_expression(self, expr: Expression, env):
        if expr.expr_type == Expression.SIMPLE:
            token = expr.token

            if token.ttype == "LABEL":
                if token.s in env:
                    return env[token.s]
                else:
                    return self.evaluate_global(token.s)

            elif token.ttype == "BOOL":
                return True if token.s == "true" else False

            elif token.ttype == "INT":
                return int(token.s)

            else:
                raise ValueError(f"Unknown simple type: {token.ttype}")

        elif expr.expr_type == Expression.IF:
            if self.evaluate_expression(expr.condition, env):
                return self.evaluate_expression(expr.left, env)
            else:
                return self.evaluate_expression(expr.right, env)

        elif expr.expr_type == Expression.BINOP:
            return BINOPS[expr.token.s](
                self.evaluate_expression(expr.left, env),
                self.evaluate_expression(expr.right, env),
            )

        elif expr.expr_type == Expression.CALL:
            callee = self.evaluate_expression(expr.left, env)

            args = [self.evaluate_expression(arg, env) for arg in expr.args]

            return callee(*args)

        elif expr.expr_type == Expression.PREFIX:
            if expr.token.ttype == '!':
                return not self.evaluate_expression(expr.right, env)
            elif expr.token.s == '-':
                return -self.evaluate_expression(expr.right, env)
            else:
                raise ValueError

        else:
            raise ValueError(f"Cannot evaluate expression of type {expr.expr_type}")
