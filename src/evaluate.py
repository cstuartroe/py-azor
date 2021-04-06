from typing import List
from random import randrange
from src.tokens import Token
from src.ast import Declaration, Expression
from src.typecheck import BINOP_TYPES


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
    '^': lambda a, b: a is not b,
    '!^': lambda a, b: a is b,
}


def AzorPrint(nums):
    print(''.join([chr(n) for n in nums]), end='')


def AzorInput():
    s = input()
    return [ord(c) for c in s]


def AzorRand(n):
    return randrange(n)


SIDE_EFFECT_FUNCTIONS = {
    "print": AzorPrint,
    "input": AzorInput,
    "rand": AzorRand,
}


assert set(BINOPS.keys()) == set(BINOP_TYPES.keys())


class Interpreter:
    def __init__(self, stmts: List[Declaration]):
        self.stmts_by_label = {}
        for stmt in stmts:
            self.stmts_by_label[stmt.label.val] = stmt

        self.symbol_table = {**SIDE_EFFECT_FUNCTIONS}

    def main(self):
        return self.evaluate_global("main")

    def evaluate_global(self, name):
        if name not in self.symbol_table:
            stmt = self.stmts_by_label[name]

            if stmt.typehint.argnames is None:
                val = self.evaluate_expression(stmt.rhs, {})

            else:
                def val(*args):
                    env = dict(zip(stmt.typehint.argnames, args))
                    return self.evaluate_expression(stmt.rhs, env)

            self.symbol_table[name] = val

        return self.symbol_table[name]

    def evaluate_expression(self, expr: Expression, env):
        if expr.expr_type == Expression.SIMPLE:
            return self.evaluate_simple(expr.token, env)

        elif expr.expr_type == Expression.TUPLE:
            return tuple(self.evaluate_expression(e, env) for e in expr.elements)

        elif expr.expr_type == Expression.LIST:
            return [self.evaluate_expression(e, env) for e in expr.elements]

        elif expr.expr_type == Expression.IF:
            return self.evaluate_if(expr, env)

        elif expr.expr_type == Expression.BINOP:
            return BINOPS[expr.token.val](
                self.evaluate_expression(expr.left, env),
                self.evaluate_expression(expr.right, env),
            )

        elif expr.expr_type == Expression.CONS:
            return [
                self.evaluate_expression(expr.left, env),
                *self.evaluate_expression(expr.right, env),
            ]

        elif expr.expr_type == Expression.LET:
            label = expr.left.left.token.val
            value = self.evaluate_expression(expr.left.right, env)
            subenv = {**env, label: value}
            return self.evaluate_expression(expr.right, subenv)

        elif expr.expr_type == Expression.CALL:
            callee = self.evaluate_expression(expr.left, env)

            args = [self.evaluate_expression(arg, env) for arg in expr.args.elements]

            return callee(*args)

        else:
            raise ValueError(f"Cannot evaluate expression of type {expr.expr_type}")

    def evaluate_simple(self, token: Token, env):
        if token.ttype == "LABEL":
            if token.val in env:
                return env[token.val]
            else:
                return self.evaluate_global(token.val)
        elif token.ttype in ["BOOL", "INT", "STRING"]:
            return token.val
        else:
            raise ValueError(f"Unknown simple type: {token.ttype}")

    def evaluate_if(self, expr, env):
        if expr.condition.expr_type == Expression.ARROW:
            head, tail, lst_expr = expr.condition.left.left, expr.condition.left.right, expr.condition.right
            lst = self.evaluate_expression(lst_expr, env)
            if len(lst) > 0:
                subenv = {**env, head.token.val: lst[0], tail.token.val: lst[1:]}
                return self.evaluate_expression(expr.left, subenv)
            else:
                return self.evaluate_expression(expr.right, env)

        else:
            if self.evaluate_expression(expr.condition, env):
                return self.evaluate_expression(expr.left, env)
            else:
                return self.evaluate_expression(expr.right, env)
