from .parser import Node, Parser
from .types import AzorType, BOOL, INT, NOT_TYPE, ARITH_TYPE, LOGIC_TYPE, COMPARE_TYPE, MAINTYPE


class Variable:
    def __init__(self, azortype, value):
        self.azortype = azortype
        self.value = value


STDLIB = {
    '!': Variable(NOT_TYPE, lambda kw: lambda subkw: not kw["b"](subkw)),
    '+': Variable(ARITH_TYPE, lambda kw: kw["m"] + kw["n"]),
    '-': Variable(ARITH_TYPE, lambda kw: kw["m"] - kw["n"]),
    '*': Variable(ARITH_TYPE, lambda kw: kw["m"] * kw["n"]),
    '%': Variable(ARITH_TYPE, lambda kw: kw["m"] % kw["n"]),
    '==': Variable(COMPARE_TYPE, lambda kw: kw["m"] == kw["n"]),
    '!=': Variable(COMPARE_TYPE, lambda kw: kw["m"] != kw["n"]),
    '<': Variable(COMPARE_TYPE, lambda kw: kw["m"] < kw["n"]),
    '>': Variable(COMPARE_TYPE, lambda kw: kw["m"] > kw["n"]),
    '<=': Variable(COMPARE_TYPE, lambda kw: kw["m"] <= kw["n"]),
    '>=': Variable(COMPARE_TYPE, lambda kw: kw["m"] >= kw["n"]),
    '&': Variable(LOGIC_TYPE, lambda kw: kw["a"] and kw["b"]),
    '|': Variable(LOGIC_TYPE, lambda kw: kw["a"] or kw["b"]),
    '^': Variable(LOGIC_TYPE, lambda kw: kw["a"] != kw["b"]),
    '!^': Variable(LOGIC_TYPE, lambda kw: kw["a"] == kw["b"]),
    '~': Variable(AzorType("LIST"), lambda kw: [kw["h"]] + kw["t"])
}


def azor_printi(kw):
    print(kw["n"])
    return kw["n"]


PRINTI_TYPE = AzorType("FUNCTION", rtype=INT, argnames=["n"], argtypes=[INT])

STDLIB["printi"] = Variable(PRINTI_TYPE, azor_printi)


def azor_printb(kw):
    print(str(kw["b"]).lower())
    return kw["b"]


PRINTB_TYPE = AzorType("FUNCTION", rtype=BOOL, argnames=["b"], argtypes=[BOOL])

STDLIB["printb"] = Variable(PRINTB_TYPE, azor_printb)


class LHS:
    def __init__(self, label, azortype):
        self.label = label
        self.azortype = azortype

    def __str__(self):
        return f"{self.label}:{str(self.azortype)}"


class TypeChecker:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.symbol_table = {}
        self.symbol_table.update(STDLIB)
        self.stmts_by_label = {}
        self.stmts = self.parser.parse()

    def check(self):
        for stmt in self.stmts:
            lhs = self.parselhs(stmt.left)
            if lhs.label in self.symbol_table:
                self.raise_error(stmt, "Variable name already set: " + lhs.label)
            self.symbol_table[lhs.label] = Variable(lhs.azortype, None)
            self.stmts_by_label[lhs.label] = stmt

        if "main" not in self.symbol_table:
            self.raise_error(self.stmts[-1], "No main method defined")
        elif self.symbol_table["main"].azortype != MAINTYPE:
            self.raise_error(self.stmts_by_label["main"], "Main method must have type " + str(MAINTYPE))

        for label in self.stmts_by_label:
            self.checkstmt(label)

    def execute_main(self):
        val = self.symbol_table["main"].value({'m': 4, 'n': 3})
        if not val:
            print("Exit failure")

    def evaluate(self):
        for label, stmt in self.stmts_by_label.items():
            azortype = self.symbol_table[label].azortype
            if azortype.atype == "FUNCTION":
                self.symbol_table[label].value = self.function_factory(stmt.right)

        for label, stmt in self.stmts_by_label.items():
            azortype = self.symbol_table[label].azortype
            if azortype.atype != "FUNCTION":
                self.symbol_table[label].value = self.evaluate_expr(stmt.right, {})

    def function_factory(self, expr):
        def f(local_vars):
            return self.evaluate_expr(expr, local_vars)
        return f

    def evaluate_expr(self, expr, local_vars):
        if expr.ntype == "SIMPLE":
            if expr.start_token.ttype == "LABEL":
                label = expr.start_token.s
                if label in self.symbol_table:
                    return self.symbol_table[label].value
                else:
                    return local_vars[label]
            else:
                return expr.start_token.val

        elif expr.ntype == "LIST":
            return [self.evaluate_expr(e, local_vars) for e in expr.elements]

        elif expr.ntype == "TUPLE":
            t = tuple(self.evaluate_expr(e, local_vars) for e in expr.elements)
            if len(t) == 1:
                return t[0]
            else:
                return t

        elif expr.ntype == "CALL":
            func = self.evaluate_expr(expr.left, local_vars)

            label = expr.left.start_token.s  # TODO: dynamic functions
            subkw = {}
            for i in range(len(expr.args.elements)):
                argname = self.symbol_table[label].azortype.argnames[i]
                subkw[argname] = self.evaluate_expr(expr.args.elements[i], local_vars)

            return func(subkw)

        elif expr.ntype == "IF":
            if expr.condition.ntype == "UNPACK":
                l = self.evaluate_expr(expr.condition.left, local_vars)
                if len(l) > 0:
                    subkw = {}
                    subkw.update(local_vars)
                    subkw[expr.condition.right.left.start_token.s] = l[0]
                    subkw[expr.condition.right.right.start_token.s] = l[1:]
                    return self.evaluate_expr(expr.left, subkw)
                else:
                    return self.evaluate_expr(expr.right, local_vars)

            else:
                b = self.evaluate_expr(expr.condition, local_vars)
                assert(type(b) is bool)
                if b:
                    return self.evaluate_expr(expr.left, local_vars)
                else:
                    return self.evaluate_expr(expr.right, local_vars)

        elif expr.ntype == "WITH":
            tup = self.evaluate_expr(expr.condition.left, local_vars)
            subkw = {}
            subkw.update(local_vars)
            for e, labelexpr in zip(tup, expr.condition.right.elements):
                subkw[labelexpr.start_token.s] = e
            return self.evaluate_expr(expr.left, subkw)

        elif expr.ntype == "TILDE":
            return [self.evaluate_expr(expr.left, local_vars)] + self.evaluate_expr(expr.right, local_vars)

        else:
            self.raise_error(expr, "Evaluation of " + expr.ntype + " not yet implemented!")

    def checkstmt(self, label):
        env = {}
        stmt = self.stmts_by_label[label]
        azortype = self.symbol_table[label].azortype

        if azortype.atype == "FUNCTION":
            for argname, argtype in zip(azortype.argnames, azortype.argtypes):
                if argname in env:
                    self.raise_error(stmt.left.args, "Duplicate variable name: " + argname)
                if argname in self.symbol_table:
                    self.raise_error(stmt.left.args, "Variable shadows name from outer scope: " + argname)

                env[argname] = Variable(argtype, None)

            self.checkexpr(azortype.rtype, stmt.right, env)

        else:
            self.checkexpr(azortype, stmt.right, {})

    def checkexpr(self, expected_type: AzorType, expr: Node, env: dict):
        azortype = None

        if expr.ntype == "SIMPLE":
            if expr.start_token.ttype == "LABEL":
                label = expr.start_token.s
                if label in env:
                    azortype = env[label].azortype
                elif label in self.symbol_table:
                    azortype = self.symbol_table[label].azortype
                else:
                    self.raise_error(expr, "Label not assigned: " + label)

            elif expr.start_token.ttype == "BOOL":
                azortype = BOOL
            elif expr.start_token.ttype == "INT":
                azortype = INT

        elif expr.ntype == "LIST":
            azortype = AzorType("LIST")
            if len(expr.elements) == 0:
                if expected_type and expected_type.atype == "LIST":
                    azortype.subtype = expected_type.subtype
                else:
                    azortype.subtype = INT  # TODO: proper generics

            else:
                azortype.subtype = self.checkexpr(None, expr.elements[0], env)
                for e in expr.elements[1:]:
                    self.checkexpr(azortype.subtype, e, env)

        elif expr.ntype == "TUPLE":
            if len(expr.elements) == 1:
                azortype = self.checkexpr(expected_type, expr.elements[0], env)

            else:
                azortype = AzorType("TUPLE", constituents=[])
                for e in expr.elements:
                    azortype.constituents.append(self.checkexpr(None, e, env))

        elif expr.ntype == "CALL":
            functype = self.checkexpr(None, expr.left, env)
            if functype.atype != "FUNCTION":
                self.raise_error(expr.left, f"Object of type {str(functype)} cannot be called")

            if len(functype.argtypes) != len(expr.args.elements):
                self.raise_error(expr.args, "Too few arguments: expected " + str(len(azortype.argtypes)))

            for argtype, e in zip(functype.argtypes, expr.args.elements):
                self.checkexpr(argtype, e, env)

            azortype = functype.rtype

        elif expr.ntype == "IF":
            if expr.condition.ntype == "UNPACK":
                subenv = {}
                subenv.update(env)

                ltype = self.checkexpr(None, expr.condition.left, env)  # TODO: dynamic unpacks
                if ltype.atype != "LIST":
                    self.raise_error(expr.condition.left, "Expected list type but got " + str(ltype))

                for e in expr.condition.right.left, expr.condition.right.right:
                    label = e.start_token.s
                    if label in subenv:
                        self.raise_error(e, "Duplicate variable name: " + label)
                    elif label in self.symbol_table:
                        self.raise_error(e, "Shadows name from outer scope: " + label)

                subenv[expr.condition.right.left.start_token.s] = Variable(ltype.subtype, None)
                subenv[expr.condition.right.right.start_token.s] = Variable(ltype, None)

            else:
                self.checkexpr(BOOL, expr.condition, env)
                subenv = env

            azortype = self.checkexpr(expected_type, expr.left, subenv)
            righttype = self.checkexpr(expected_type, expr.right, subenv)
            if azortype != righttype:
                self.raise_error(expr, f"Then and else have different types: {str(azortype)} and {str(righttype)}")

        elif expr.ntype == "WITH":
            subenv = {}
            subenv.update(env)

            tuptype = self.checkexpr(None, expr.condition.left, env)
            if tuptype.atype != "TUPLE":
                self.raise_error(expr.condition.left, "Expected tuple but got " + str(tuptype))

            if len(expr.condition.right.elements) != len(tuptype.constituents):
                self.raise_error(expr.condition, f"Mismatched number of elements: expected {len(tuptype.constituents)}")

            for e, azortype in zip(expr.condition.right.elements, tuptype.constituents):
                label = e.start_token.s
                if label in subenv:
                    self.raise_error(e, "Duplicate variable name: " + label)
                elif label in self.symbol_table:
                    self.raise_error(e, "Shadows name from outer scope: " + label)
                subenv[label] = Variable(azortype, None)

            azortype = self.checkexpr(expected_type, expr.left, subenv)

        elif expr.ntype == "TILDE":
            azortype = self.checkexpr(None, expr.right, env)
            if azortype.atype == "LIST":
                self.checkexpr(azortype.subtype, expr.left, env)

        elif expr.ntype == "UNPACK":
            self.raise_error(expr, "Unpack expression can only occur as condition of if or with statement")

        else:
            self.raise_error(expr, "???")

        if expected_type is not None and azortype != expected_type:
            self.raise_error(expr, f"Expected type {str(expected_type)}, not {str(azortype)}")
        else:
            return azortype

    def raise_error(self, node, message):
        self.parser.tokenizer.raise_error(node.start_token, message)

    def parselhs(self, lhs: Node):
        if lhs.ntype == "CALL":
            label = lhs.left.left.start_token.s
            rtype = self.parsetype(lhs.left.right)
            argtypes = []
            argnames = []
            for el in lhs.args.elements:
                arg = self.parselhs(el)
                argtypes.append(arg.azortype)
                argnames.append(arg.label)
            azortype = AzorType("FUNCTION", rtype=rtype, argtypes=argtypes, argnames=argnames)

        elif lhs.ntype == "TYPE":
            azortype = self.parsetype(lhs.right)
            label = lhs.left.start_token.s

        else:
            self.raise_error(lhs, "???")

        return LHS(label, azortype)
            
    def parsetype(self, node: Node):
        if node.ntype == "SIMPLE" and node.start_token.ttype == "TYPE":
            if node.start_token.val == int:
                return INT
            elif node.start_token.val == bool:
                return BOOL
            else:
                raise RuntimeError("?")

        elif node.ntype == "LIST":
            if len(node.elements) != 1:
                self.raise_error(node, "List type must have exactly one element")
            else:
                return AzorType("LIST", subtype=self.parsetype(node.elements[0]))

        elif node.ntype == "TUPLE":
            return AzorType("TUPLE", constituents=[self.parsetype(el) for el in node.elements])

        self.raise_error(node, "Invalid type")
