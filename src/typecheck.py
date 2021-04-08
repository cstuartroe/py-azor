from typing import Dict, List, Set
from .tokens import BINOP_PRECS, COMPARISONS, LOGIC
from .parser import Expression, TypeNode, Declaration, Parser
from .types import (
    AzorType,
    BOOL,
    INT,
    NOT_TYPE,
    ARITH_TYPE,
    LOGIC_TYPE,
    COMPARE_TYPE,
    INT_LIST,
    PRINT_TYPE,
    INPUT_TYPE,
    RAND_TYPE,
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

assert set(BINOP_TYPES.keys()) == (set(BINOP_PRECS.keys()) | COMPARISONS | LOGIC)

SIDE_EFFECT_TYPES = {
    "print": PRINT_TYPE,
    "input": INPUT_TYPE,
    "rand": RAND_TYPE,
}


class LHS:
    def __init__(self, label: str, azortype: AzorType):
        self.label = label
        self.azortype = azortype

    def __str__(self):
        return f"{self.label} : {str(self.azortype)}"


class TypeChecker:
    def __init__(self, stmts: List[Declaration]):
        self.stmts = stmts
        self.symbol_table: Dict[str, AzorType] = {**SIDE_EFFECT_TYPES}
        self.stmts_by_label: Dict[str, Declaration] = {}

    def check(self):
        for stmt in self.stmts:
            lhs = self.parselhs(stmt)
            if lhs.label in self.symbol_table:
                self.raise_error(stmt, "Variable name already set: " + lhs.label)
            self.symbol_table[lhs.label] = lhs.azortype
            self.stmts_by_label[lhs.label] = stmt

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

            for argname, argtype in zip(azortype.argnames, azortype.argtypes):
                if argname in env:
                    self.raise_error(stmt, "Duplicate variable name: " + argname)
                if argname in self.symbol_table:
                    self.raise_error(stmt, "Variable shadows name from outer scope: " + argname)

                env[argname] = argtype

            self.assert_expr(
                azortype=azortype.rtype,
                expr=stmt.rhs,
                env=env,
                generics=set(azortype.generics),
            )

        else:
            self.assert_expr(
                azortype=azortype,
                expr=stmt.rhs,
                env={},
                generics=set(),
            )

    def assert_expr(self, azortype: AzorType, expr: Expression, env: Dict[str, AzorType], generics: Set[str]):
        t = self.checkexpr(expr=expr, env=env, generics=generics)
        if t != azortype:
            self.raise_error(expr, f"Does not have expected type (expected {azortype}, got {t})")

    def checkexpr(self, expr: Expression, env: Dict[str, AzorType], generics: Set[str]) -> AzorType:
        if expr.expr_type == Expression.SIMPLE:
            if expr.token.ttype == "LABEL":
                label = expr.token.val
                if label in env:
                    return env[label]
                elif label in self.symbol_table:
                    return self.symbol_table[label]
                else:
                    self.raise_error(expr, "Label not assigned: " + label)

            elif expr.token.ttype == "BOOL":
                return BOOL
            elif expr.token.ttype == "INT":
                return INT
            elif expr.token.ttype == "STRING":
                return INT_LIST

        elif expr.expr_type == Expression.LIST:
            azortype = AzorType("LIST")
            if len(expr.elements) == 0:
                azortype.etype = self.eval_type(expr.typehint, allowed_generics=generics)

            else:
                azortype.etype = self.checkexpr(expr.elements[0], env, generics)
                for e in expr.elements[1:]:
                    self.assert_expr(azortype.etype, e, env, generics)

            return azortype

        elif expr.expr_type == Expression.TUPLE:
            azortype = AzorType("TUPLE", constituents=[])
            for e in expr.elements:
                azortype.constituents.append(self.checkexpr(e, env, generics))
            return azortype

        elif expr.expr_type == Expression.CALL:
            functype = self.checkexpr(expr.left, env, generics)
            if functype.atype != "FUNCTION":
                self.raise_error(expr.left, f"Object of type {str(functype)} cannot be called")

            if functype.generics:
                if expr.generic_spec is None:
                    self.raise_error(expr, "Must specify generics resolution for this function")
                elif len(functype.generics) != len(expr.generic_spec):
                    self.raise_error(expr.generic_spec[-1],
                                     f"Wrong number of types supplied (expected {len(functype.generics)},"
                                     f"got {len(expr.generic_spec)}")

                spec = {}
                for generic_label, type_node in zip(functype.generics, expr.generic_spec):
                    spec[generic_label] = self.eval_type(type_node, allowed_generics=set(generics))

                functype = functype.resolve_generics(spec)

            else:
                if expr.generic_spec is not None:
                    self.raise_error(expr, "Generics were specified on a non-generic function")

            if len(functype.argtypes) != len(expr.args.elements):
                self.raise_error(expr.args, "Too few arguments: expected " + str(len(functype.argtypes)))

            for argtype, e in zip(functype.argtypes, expr.args.elements):
                self.assert_expr(argtype, e, env, generics)

            # this is ugly but must be done for interpreter
            expr.argnames = functype.argnames

            return functype.rtype

        elif expr.expr_type == Expression.IF:
            if expr.condition.expr_type == Expression.ARROW:
                head, tail, lst = expr.condition.left.left, expr.condition.left.right, expr.condition.right

                subenv = {}
                subenv.update(env)

                ltype = self.checkexpr(lst, env, generics)
                if ltype.atype != "LIST":
                    self.raise_error(lst, "Expected list type but got " + str(ltype))

                for e in head, tail:
                    label = e.token.s
                    if label in subenv:
                        self.raise_error(e, "Duplicate variable name: " + label)
                    elif label in self.symbol_table:
                        self.raise_error(e, "Shadows name from outer scope: " + label)

                subenv[head.token.val] = ltype.etype
                subenv[tail.token.val] = ltype

            else:
                self.assert_expr(BOOL, expr.condition, env, generics)
                subenv = env

            thentype = self.checkexpr(expr.left, subenv, generics)
            elsetype = self.checkexpr(expr.right, env, generics)
            if thentype != elsetype:
                self.raise_error(expr, f"Then and else have different types: {str(thentype)} and {str(elsetype)}")
            return thentype

        elif expr.expr_type == Expression.LET:
            subenv = {}
            subenv.update(env)

            dest, unpacked, main_expr = expr.left.left, expr.left.right, expr.right
            unpacked_type = self.checkexpr(unpacked, env, generics)

            if dest.expr_type == Expression.TUPLE:
                if unpacked_type.atype != "TUPLE":
                    self.raise_error(unpacked, "Expected tuple but got " + str(unpacked_type))

                if len(dest.elements) != len(unpacked_type.constituents):
                    self.raise_error(dest, f"Mismatched number of elements: expected {len(unpacked_type.constituents)}")

                for e, azortype in zip(dest.elements, unpacked_type.constituents):
                    if e.expr_type != Expression.SIMPLE or e.token.ttype != "LABEL":
                        self.raise_error(e, "Can only unpack to label")

                    label = e.token.val

                    if label in subenv:
                        self.raise_error(e, "Duplicate variable name: " + label)
                    elif label in self.symbol_table:
                        self.raise_error(e, "Shadows name from outer scope: " + label)

                    subenv[label] = azortype

            elif dest.expr_type == Expression.SIMPLE and dest.token.ttype == "LABEL":
                label = dest.token.val

                if label in subenv:
                    self.raise_error(dest, "Duplicate variable name: " + label)
                elif label in self.symbol_table:
                    self.raise_error(dest, "Shadows name from outer scope: " + label)

                subenv[label] = unpacked_type

            else:
                self.raise_error(dest, "Invalid left-hand side for assignment")

            return self.checkexpr(main_expr, subenv, generics)

        elif expr.expr_type == Expression.CONS:
            azortype = self.checkexpr(expr.right, env, generics)
            if azortype.atype == "LIST":
                self.assert_expr(azortype.etype, expr.left, env, generics)
            else:
                self.raise_error(expr.right.token, "Not a list type")
            return azortype

        elif expr.expr_type == Expression.BINOP:
            ftype = BINOP_TYPES[expr.token.val]
            self.assert_expr(ftype.argtypes[0], expr.left, env, generics)
            self.assert_expr(ftype.argtypes[1], expr.right, env, generics)
            return ftype.rtype

        else:
            self.raise_error(expr, f"Unexpected expression type: {expr.expr_type}")

        raise RuntimeError("Didn't return??")

    def raise_error(self, node, message):
        node.token.raise_error(message)

    def parselhs(self, stmt: Declaration):
        azortype = self.eval_type(stmt.typehint)
        return LHS(stmt.label.val, azortype)

    def eval_type(self, node: TypeNode, allowed_generics: Set[str] = None):
        allowed_generics = allowed_generics or set()

        declared_generics = [g.token.val for g in (node.generics or [])]
        if len(allowed_generics & set(declared_generics)) != 0:
            self.raise_error(
                node.generics[0],
                f"Redeclared generic(s): {','.join(allowed_generics & set(declared_generics))}",
            )
        allowed_generics |= set(declared_generics)

        if node.ttype == TypeNode.SIMPLE:
            if node.simpletype == int:
                basictype = INT
            elif node.simpletype == bool:
                basictype = BOOL
            else:
                raise RuntimeError("?")

        elif node.ttype == TypeNode.LIST:
            basictype = AzorType("LIST", etype=self.eval_type(
                node.etype,
                allowed_generics=allowed_generics
            ))

        elif node.ttype == TypeNode.TUPLE:
            basictype = AzorType("TUPLE", constituents=[
                self.eval_type(el, allowed_generics=allowed_generics)
                for el in node.constituents
            ])

        elif node.ttype == TypeNode.GENERIC:
            if node.label.val not in allowed_generics:
                self.raise_error(node, "This generic name was not declared")
            basictype = AzorType("GENERIC", label=node.label.val)

        else:
            self.raise_error(node, "Invalid type")

        if node.argtypes is not None:
            return AzorType(
                atype="FUNCTION",
                rtype=basictype,
                argtypes=[
                    self.eval_type(at, allowed_generics)
                    for at in node.argtypes
                ],
                argnames=node.argnames,
                generics=declared_generics,
            )
        else:
            return basictype
