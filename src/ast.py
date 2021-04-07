from .tokens import Token


class Expression:
    SIMPLE = "SIMPLE"
    LIST = "LIST"
    TUPLE = "TUPLE"
    CALL = "CALL"
    IF = "IF"
    LET = "LET"
    CONS = "CONS"
    ARROW = "ARROW"
    BINOP = "BINOP"
    NOT = "NOT"

    def __init__(self, token: Token, expr_type: str):
        self.token = token
        self.expr_type = expr_type

        self.condition = None
        self.left = None
        self.right = None
        self.args = None
        self.elements = None
        self.typehint = None

    def __str__(self):
        if self.expr_type == Expression.SIMPLE:
            return self.token.s
        elif self.expr_type == Expression.LIST:
            return f"[{', '.join(str(e) for e in self.elements)}]{' of ' if self.typehint else ''}{self.typehint}"
        elif self.expr_type == Expression.TUPLE:
            return f"({', '.join(str(e) for e in self.elements)})"
        elif self.expr_type == Expression.CALL:
            return f"{self.left}{self.args}"
        elif self.expr_type == Expression.IF:
            return f"if {self.condition} then {self.left} else {self.right})"
        elif self.expr_type == Expression.LET:
            return f"let {self.left} in {self.right}"
        elif self.expr_type == Expression.CONS:
            return f"({self.left} ~ {self.right})"
        elif self.expr_type == Expression.ARROW:
            return f"{self.left} <- {self.right}"
        elif self.expr_type == Expression.BINOP:
            return f"({self.left} {self.token.val} {self.right})"
        elif self.expr_type == Expression.NOT:
            return f"(!{self.right})"


class TypeNode:
    SIMPLE = "SIMPLE"
    LIST = "LIST"
    TUPLE = "TUPLE"
    EMPTY = "EMPTY"

    def __init__(self, token, ttype, simpletype=None, etype=None, constituents=None):
        self.token = token
        self.ttype = ttype
        self.argtypes = None
        self.argnames = None

        if ttype == TypeNode.LIST:
            self.etype = etype
        elif ttype == TypeNode.TUPLE:
            self.constituents = constituents
        elif ttype == TypeNode.SIMPLE:
            self.simpletype = simpletype
        elif ttype == TypeNode.EMPTY:
            pass
        else:
            raise ValueError

    def __str__(self):
        if self.ttype == TypeNode.LIST:
            basetype = f"[{self.etype}]"
        elif self.ttype == TypeNode.TUPLE:
            basetype = f"({', '.join(map(str, self.constituents))})"
        elif self.ttype == TypeNode.SIMPLE:
            if self.simpletype == bool:
                basetype = "BOOL"
            elif self.simpletype == int:
                basetype = "INT"
            else:
                raise ValueError
        elif self.ttype == TypeNode.EMPTY:
            basetype = ""
        else:
            raise ValueError

        if self.argtypes:
            if self.argnames:
                argstr = ', '.join(f'{argname} : {argtype}' for argname, argtype in zip(self.argnames, self.argtypes))
            else:
                argstr = ', '.join(str(argtype) for argtype in self.argtypes)
            return f"{basetype}({argstr})"
        else:
            return basetype


class Declaration:
    def __init__(self, label: Token, typehint: TypeNode, rhs: Expression):
        self.label = label
        self.token = label
        self.typehint = typehint
        self.rhs = rhs

    def __str__(self):
        return f"{self.label.val} : {self.typehint} = {self.rhs}"
