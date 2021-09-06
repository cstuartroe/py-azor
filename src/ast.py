from typing import List, Union
from .tokens import Token


class Expression:
    SIMPLE = "SIMPLE"
    CALL = "CALL"
    IF = "IF"
    BINOP = "BINOP"
    PREFIX = "PREFIX"

    def __init__(self, token: Token, expr_type: str):
        self.token = token
        self.expr_type = expr_type

        self.condition = None
        self.left = None
        self.right = None
        self.args = None

    def __repr__(self):
        if self.expr_type == Expression.SIMPLE:
            return self.token.s
        elif self.expr_type == Expression.CALL:
            return f"{self.left}({', '.join(map(str, self.args))})"
        elif self.expr_type == Expression.IF:
            return f"(if {self.condition} then {self.left} else {self.right})"
        elif self.expr_type == Expression.BINOP:
            return f"({self.left} {self.token.s} {self.right})"
        elif self.expr_type == Expression.PREFIX:
            return f"(!{self.right})"
        else:
            raise ValueError


class Declaration:
    def __init__(self, label: Token, argnames: Union[List[str], None], rhs: Expression):
        self.label = label
        self.token = label
        self.argnames = argnames
        self.rhs = rhs

    def __repr__(self):
        if self.argnames is None:
            argstring = ""
        else:
            argstring = f"({', '.join(self.argnames)})"

        return f"{self.label.s}{argstring} = {self.rhs}"
