from typing import Dict, List
from .parser import Expression, TypeNode, Declaration
from .types import (
    AzorType,
    BOOL,
    INT,
    ARITH_TYPE,
    LOGIC_TYPE,
    COMPARE_TYPE,
    MAIN_TYPE,
)

BINOP_TYPES = {
    '+': ARITH_TYPE,
    '-': ARITH_TYPE,
    '*': ARITH_TYPE,
    '/': ARITH_TYPE,
    '%': ARITH_TYPE,
    '**': ARITH_TYPE,

    '==': COMPARE_TYPE,
    '!=': COMPARE_TYPE,
    '<': COMPARE_TYPE,
    '>': COMPARE_TYPE,
    '<=': COMPARE_TYPE,
    '>=': COMPARE_TYPE,

    '&': LOGIC_TYPE,
    '|': LOGIC_TYPE,
    '^': LOGIC_TYPE,
    '!^': LOGIC_TYPE,
}


class TypeChecker:
    def __init__(self, stmts: List[Declaration]):
        self.stmts = stmts
        self.symbol_table: Dict[str, AzorType] = {}
        self.stmts_by_label: Dict[str, Declaration] = {}

    def check(self):
        for stmt in self.stmts:
            label, azortype = stmt.label.s, self.eval_type(stmt.typehint)

            if label in self.symbol_table:
                self.raise_error(stmt, "Variable name already set: " + label)

            self.symbol_table[label] = azortype
            self.stmts_by_label[label] = stmt

        if "main" not in self.symbol_table:
            self.raise_error(self.stmts[-1], "No main method defined")
        elif self.symbol_table["main"] != MAIN_TYPE:
            self.raise_error(self.stmts_by_label["main"], "Main method must have type " + str(MAIN_TYPE))

        for label in self.stmts_by_label:
            self.checkstmt(label)

    def checkstmt(self, label):
        stmt = self.stmts_by_label[label]
        azortype = self.symbol_table[label]

        if azortype.atype == "FUNCTION":
            env = {}

            for argname, argtype in azortype.args.items():
                if argname in self.symbol_table:
                    self.raise_error(stmt, "Variable shadows global: " + argname)

                env[argname] = argtype

            self.assert_expr(
                azortype=azortype.rtype,
                expr=stmt.rhs,
                env=env,
            )

        else:
            self.assert_expr(
                azortype=azortype,
                expr=stmt.rhs,
                env={},
            )

    def assert_expr(self, azortype: AzorType, expr: Expression, env: Dict[str, AzorType]):
        t = self.checkexpr(expr=expr, env=env)
        if t != azortype:
            self.raise_error(expr, f"Does not have expected type (expected {azortype}, got {t})")

    def checkexpr(self, expr: Expression, env: Dict[str, AzorType]) -> AzorType:
        if expr.expr_type == Expression.SIMPLE:
            if expr.token.ttype == "LABEL":
                label = expr.token.s
                if label in env:
                    return env[label]

                elif label in self.symbol_table:
                    t: AzorType = self.symbol_table[label]
                    if t is None or (t.atype == "FUNCTION" and t.rtype is None):
                        try:
                            self.checkstmt(label)
                        except RecursionError:
                            self.raise_error(expr, "Recursion or mutual recursion of implicit typing detected")
                    return t

                else:
                    self.raise_error(expr, "Label not assigned: " + label)

            elif expr.token.ttype == "BOOL":
                return BOOL
            elif expr.token.ttype == "INT":
                return INT

        elif expr.expr_type == Expression.CALL:
            functype = self.checkexpr(expr.left, env)
            if functype.atype != "FUNCTION":
                self.raise_error(expr.left, f"Object of type {str(functype)} cannot be called")

            if len(functype.args) != len(expr.args):
                self.raise_error(expr, "Incorrect number of arguments arguments: expected " + str(len(functype.args)))

            for argtype, e in zip(functype.args.values(), expr.args):
                self.assert_expr(argtype, e, env)

            return functype.rtype

        elif expr.expr_type == Expression.IF:
            self.assert_expr(BOOL, expr.condition, env)

            thentype = self.checkexpr(expr.left, env)
            elsetype = self.checkexpr(expr.right, env)

            if thentype != elsetype:
                self.raise_error(expr, f"Then and else have different types: {str(thentype)} and {str(elsetype)}")

            return thentype

        elif expr.expr_type == Expression.BINOP:
            ftype = BINOP_TYPES[expr.token.s]

            (aname1, atype1), (aname1, atype2) = ftype.args.items()

            self.assert_expr(atype1, expr.left, env)
            self.assert_expr(atype2, expr.right, env)

            return ftype.rtype

        elif expr.expr_type == Expression.PREFIX:
            if expr.token.ttype == '!':
                self.assert_expr(BOOL, expr.right, env)
                return BOOL
            elif expr.token.s == '-':
                self.assert_expr(INT, expr.right, env)
                return INT
            else:
                raise ValueError

        else:
            self.raise_error(expr, f"Unexpected expression type: {expr.expr_type}")

    def raise_error(self, node, message):
        node.token.raise_error(message)

    def eval_type(self, node: TypeNode):
        if node.simpletype is int:
            basictype = INT
        elif node.simpletype is bool:
            basictype = BOOL
        else:
            raise RuntimeError("?")

        if node.args is not None:
            args = {}

            for name, tnode in node.args:
                args[name] = self.eval_type(tnode)

            return AzorType(
                atype="FUNCTION",
                rtype=basictype,
                args=args,
            )
        else:
            return basictype
