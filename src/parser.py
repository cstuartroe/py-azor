from .tokens import Tokenizer, BINOP_PRECS
from .ast import Expression, TypeNode, Declaration


class Parser:
    SUFFIX_PRECS = {
        "~": 1,
        "COMPARISON": 1,
        "LOGIC": 2,
    }

    @staticmethod
    def get_prec(token):
        if token.ttype in Parser.SUFFIX_PRECS:
            return Parser.SUFFIX_PRECS[token.ttype]
        elif token.ttype == "BINOP":
            return BINOP_PRECS[token.val]
        else:
            raise ValueError

    @classmethod
    def parse_file(cls, filename):
        with open(filename, "r") as fh:
            code = fh.read().replace('\t', '    ')

        lines = code.split("\n")
        tokens = Tokenizer(lines).tokenize()
        return cls(tokens).parse()

    def __init__(self, tokens):
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

    def expect(self, ttype):
        if self.next().ttype != ttype:
            self.next().raise_error("Expected " + ttype)
        self.i += 1

    def grab_declaration(self):
        label = self.next()
        self.expect("LABEL")

        if self.next().ttype == "{":
            self.i += 1
            generics, _ = self.grab_series(lambda: self.grab_expr(-1))
            self.expect("}")
            for g in generics:
                if g.expr_type != Expression.SIMPLE or g.token.ttype != "LABEL":
                    g.token.raise_error("Generic names must be labels")

        else:
            generics = []

        if self.next().ttype == ':':
            self.i += 1
            typehint = self.grab_type_node(vbl_names=True)

        elif self.next().ttype == '(':
            typehint = TypeNode(
                ttype=TypeNode.EMPTY,
                token=self.next(),
            )
            typehint.argnames, typehint.argtypes = self.grab_type_node_args(vbl_names=True)

        else:
            typehint = TypeNode(
                ttype=TypeNode.EMPTY,
                token=label,
            )

        typehint.set_generics(generics)

        self.expect('=')

        rhs = self.grab_expr(-1)

        return Declaration(label, typehint, rhs)

    def grab_type_node(self, vbl_names=False):
        t = self.next()

        if t.ttype == "TYPE":
            out = TypeNode(
                ttype=TypeNode.SIMPLE,
                simpletype=self.next().val,
                token=t,
            )
            self.i += 1
        elif t.ttype == "(":
            self.i += 1
            constituents, _ = self.grab_series(self.grab_type_node)
            out = TypeNode(
                ttype=TypeNode.TUPLE,
                constituents=constituents,
                token=t,
            )
            self.expect(")")
        elif t.ttype == "[":
            self.i += 1
            out = TypeNode(
                ttype=TypeNode.LIST,
                etype=self.grab_type_node(),
                token=t,
            )
            self.expect("]")
        elif t.ttype == "LABEL":
            self.i += 1
            out = TypeNode(
                ttype=TypeNode.GENERIC,
                label=t,
                token=t,
            )
        else:
            t.raise_error("Illegal start to type")

        if not self.eof() and self.next().ttype == "(":
            argnames, argtypes = self.grab_type_node_args(vbl_names)
            out.argnames = argnames
            out.argtypes = argtypes

        return out

    def grab_type_node_args(self, vbl_names):
        self.expect("(")

        argnames = []
        argtypes = []

        while self.next().ttype != ")":
            if vbl_names:
                argnames.append(self.next().val)
                self.expect("LABEL")
                self.expect(":")

            argtypes.append(self.grab_type_node())

            if self.next().ttype == ",":
                self.i += 1
            else:
                break

        self.expect(")")

        return (argnames if vbl_names else None), argtypes

    def grab_expr(self, suffix_precedence):
        if self.next().ttype in {"LABEL", "BOOL", "INT", "STRING"}:
            n = Expression(self.next(), Expression.SIMPLE)
            self.i += 1

        elif self.next().ttype == '[':
            n = self.grab_list()

        elif self.next().ttype == '(':
            n = self.grab_tuple()
            if len(n.elements) == 1 and not n.ended_with_comma:
                n = n.elements[0]

        elif self.next().ttype == "IF":
            n = self.grab_if()

        elif self.next().ttype == "LET":
            n = self.grab_let()

        elif self.next().ttype in ")]}":
            self.next().raise_error("Mismatched braces")

        else:
            self.next().raise_error("Invalid start to expression")

        return self.check_suffixes(n, suffix_precedence)

    def grab_list(self):
        out = Expression(self.next(), Expression.LIST)
        self.expect("[")

        out.elements, _ = self.grab_series(lambda: self.grab_expr(-1))

        self.expect(']')

        if len(out.elements) == 0:
            self.expect("OF")
            out.typehint = self.grab_type_node()

        return out

    def grab_if(self):
        out = Expression(self.next(), "IF")
        self.expect("IF")

        condition = self.grab_expr(-1)

        if self.next().ttype == "<-":
            if condition.expr_type != Expression.CONS:
                condition.token.raise_error("If unpacking must be a ~ expression")
            for e in condition.left, condition.right:
                if e.expr_type != Expression.SIMPLE or e.token.ttype != "LABEL":
                    e.token.raise_error("Must be a label")

            condition = self.grab_arrow(condition)

        out.condition = condition

        self.expect("THEN")

        out.left = self.grab_expr(-1)

        self.expect('ELSE')

        out.right = self.grab_expr(-1)

        return out

    def grab_arrow(self, lhs):
        self.expect("<-")
        rhs = self.grab_expr(-1)

        arrow = Expression(lhs.token, Expression.ARROW)
        arrow.left = lhs
        arrow.right = rhs

        return arrow

    def grab_tuple(self):
        out = Expression(self.next(), Expression.TUPLE)
        self.expect("(")

        out.elements, out.ended_with_comma = self.grab_series(lambda: self.grab_expr(-1))

        self.expect(")")

        return out

    def grab_let(self):
        out = Expression(self.next(), Expression.LET)
        self.expect("LET")

        lhs = self.grab_expr(1)
        out.left = self.grab_arrow(lhs)

        self.expect("IN")

        out.right = self.grab_expr(1)

        return out

    def check_suffixes(self, n, precedence):
        if self.eof():
            return n

        t = self.next()

        if t.ttype == '{':
            resolution = Expression(n.token, Expression.GENERIC)
            resolution.left = n
            resolution.elements = self.grab_generic_spec()
            return self.check_suffixes(resolution, precedence)

        elif t.ttype in "(":
            call = Expression(n.token, Expression.CALL)
            call.left = n
            call.args = self.grab_tuple()
            return self.check_suffixes(call, precedence)

        if t.ttype == "~" and precedence < Parser.get_prec(t):
            cons = Expression(n.token, Expression.CONS)
            self.i += 1
            cons.left = n
            cons.right = self.grab_expr(Parser.get_prec(t))
            return self.check_suffixes(cons, precedence)

        if t.ttype in ["BINOP", *Parser.SUFFIX_PRECS.keys()]:
            binop = Expression(t, Expression.BINOP)
            self.i += 1
            binop.left = n
            binop.right = self.grab_expr(Parser.get_prec(t))
            return self.check_suffixes(binop, precedence)

        return n

    def grab_series(self, grabber):
        elems = []
        ended_with_comma = True
        while self.next().ttype not in "])}":
            elems.append(grabber())
            if self.next().ttype == ",":
                self.i += 1
            else:
                ended_with_comma = False
                break
        return elems, ended_with_comma

    def grab_generic_spec(self):
        self.expect('{')
        types, _ = self.grab_series(lambda: self.grab_type_node(vbl_names=False))
        self.expect('}')
        return types
