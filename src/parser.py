from .tokens import Token, Tokenizer


class Node:
    NODETYPES = {"SIMPLE", "LIST", "TUPLE", "STATEMENT", "CALL", "IF", "UNPACK", "TYPE", "WITH", "TILDE"}

    def __init__(self, start_token: Token, ntype: str):
        self.start_token = start_token
        self.ntype = ntype

        self.condition = None
        self.left = None
        self.right = None
        self.args = None
        self.elements = None

    def __str__(self):
        if self.ntype == "SIMPLE":
            return self.start_token.s
        elif self.ntype == "LIST":
            return f"[{', '.join(str(e) for e in self.elements)}]"
        elif self.ntype == "TUPLE":
            return f"({', '.join(str(e) for e in self.elements)})"
        elif self.ntype == "STATEMENT":
            return f"{str(self.left)} = {str(self.right)}\n"
        elif self.ntype == "CALL":
            return f"{str(self.left)}({' '.join(str(a) for a in self.args.elements)})"
        elif self.ntype == "IF":
            return f"({str(self.condition)} ? {str(self.left)} : {str(self.right)})"
        elif self.ntype == "UNPACK":
            return f"({str(self.condition)} -> {str(self.left)} {str(self.right)})"
        elif self.ntype == "TYPE":
            return f"{str(self.left)}:{str(self.right)}"


class Parser:
    SUFFIX_PRECEDENCE = {
        "TYPE": 3,
        "CALL": 2,
        "TILDE": 1,
        "WITH": 0
    }

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer
        self.tokens = tokenizer.tokenize()
        self.i = 0
        self.lhs = False

    def parse(self):
        self.i = 0
        self.lhs = False
        stmts = []
        while self.i < len(self.tokens):
            stmt = self.grab_statement()
            stmts.append(stmt)

        return stmts

    def next(self):
        if self.i >= len(self.tokens):
            self.tokenizer.raise_error(self.tokens[-1], "Unexpected EOF")
        return self.tokens[self.i]

    def eof(self):
        return self.i == len(self.tokens)

    def expect(self, s):
        if self.next().s != s:
            self.tokenizer.raise_error(self.next(), "Expected " + s)
        self.i += 1

    def grab_statement(self):
        self.lhs = True
        left = self.grab_expr(-1)
        if left.ntype == "CALL":
            if left.left.ntype != "TYPE":
                self.tokenizer.raise_error(left.start_token, "Declarations must include a type")
            for arg in left.args.elements:
                if arg.ntype != "TYPE":
                    self.tokenizer.raise_error(arg.start_token, "All arguments must include a type annotation " + arg.ntype)
        elif left.ntype != "TYPE":
            self.tokenizer.raise_error(left.start_token, "Declarations must include a type")

        self.expect('=')
        self.lhs = False

        right = self.grab_expr(-1)

        n = Node(left.start_token, "STATEMENT")
        n.left = left
        n.right = right
        return n

    def grab_expr(self, suffix_precedence):
        if self.next().ttype == '[':
            n = Node(self.next(), "LIST")
            self.i += 1
            n.elements = self.grab_series()
            self.expect(']')

        elif self.next().ttype == '(':
            start_token = self.next()
            self.i += 1

            if self.next().ttype == "IF":
                self.i += 1
                n = Node(start_token, "IF")
                n.condition = self.grab_expr(-1)
                if n.condition.ntype == "UNPACK":
                    if n.condition.right.ntype != "TILDE":
                        self.tokenizer.raise_error(n.condition.right.start_token,
                                                   "If unpacking must be a tilde expression")
                    for e in n.condition.right.left, n.condition.right.right:
                        if e.ntype != "SIMPLE" or e.start_token.ttype != "LABEL":
                            self.tokenizer.raise_error(e.start_token, "Must be a label")

                self.expect('then')
                n.left = self.grab_expr(-1)
                self.expect('else')
                n.right = self.grab_expr(-1)

            elif self.next().ttype == ")":
                n = Node(start_token, "TUPLE")
                n.elements = []

            else:
                expr = self.grab_expr(-1)

                if self.next().ttype == "ARROW":
                    self.i += 1
                    n = Node(start_token, "UNPACK")
                    n.left = expr
                    n.right = self.grab_expr(-1)

                elif self.next().ttype == "COMMA":
                    n = Node(start_token, "TUPLE")
                    self.i += 1
                    n.elements = [expr] + self.grab_series()

                elif self.next().ttype == ")":
                    n = Node(start_token, "TUPLE")
                    n.elements = [expr]

                elif self.next().ttype == "LABEL":
                    n = Node(start_token, "CALL")
                    n.left = Node(self.next(), "SIMPLE")
                    self.i += 1
                    n.args = Node(start_token, "TUPLE")
                    n.args.elements = [expr, self.grab_expr(-1)]

            self.expect(')')

        elif self.next().ttype in ")]":
            raise self.tokenizer.raise_error(self.next(), "Mismatched braces")

        elif self.next().ttype == "TYPE":
            n = Node(self.next(), "SIMPLE")
            self.i += 1
            return n

        elif self.next().ttype in {"LABEL", "BOOL", "INT"}:
            n = Node(self.next(), "SIMPLE")
            self.i += 1

        else:
            self.tokenizer.raise_error(self.next(), "Invalid start to expression")

        return self.check_suffixes(n, suffix_precedence)

    def check_suffixes(self, n, precedence):
        if self.eof():
            return n

        if self.next().ttype == "COLON" and precedence < Parser.SUFFIX_PRECEDENCE["TYPE"]:
            if n.ntype != "SIMPLE" or n.start_token.ttype != "LABEL":
                self.tokenizer.raise_error(n.start_token, "Cannot declare type of a non-label")
            elif not self.lhs:
                self.tokenizer.raise_error(self.next(), "Type annotations not allowed on rhs")
            expr = Node(n.start_token, "TYPE")
            expr.left = n
            self.expect(':')
            expr.right = self.grab_expr(Parser.SUFFIX_PRECEDENCE["TYPE"])
            return self.check_suffixes(expr, -1)

        if self.next().ttype == "(" and precedence < Parser.SUFFIX_PRECEDENCE["CALL"]:
            call = Node(n.start_token, "CALL")
            call.left = n
            call.args = self.grab_expr(Parser.SUFFIX_PRECEDENCE["CALL"])
            if call.args.ntype != "TUPLE":
                self.tokenizer.raise_error(call.args.start_token, "Args must be a tuple, not " + str(call.args.ntype))
            return self.check_suffixes(call, -1)

        if self.next().ttype == "WITH" and precedence < Parser.SUFFIX_PRECEDENCE["WITH"]:
            withnode = Node(self.next(), "WITH")
            self.i += 1
            withnode.left = n
            withnode.condition = self.grab_expr(Parser.SUFFIX_PRECEDENCE["WITH"])
            if withnode.condition.ntype != "UNPACK":
                self.tokenizer.raise_error(n.condition.start_token, "Expected unpack")
            if withnode.condition.right.ntype != "TUPLE":
                self.tokenizer.raise_error(withnode.condition.right.start_token, "with unpack must be into tuple")
            for e in withnode.condition.right.elements:
                if e.ntype != "SIMPLE" or e.start_token.ttype != "LABEL":
                    self.tokenizer.raise_error(e.start_token, "Must be a label")
            return self.check_suffixes(withnode, -1)

        if self.next().ttype == "TILDE" and precedence < Parser.SUFFIX_PRECEDENCE["TILDE"]:
            tildenode = Node(n.start_token, "TILDE")
            self.i += 1
            tildenode.left = n
            tildenode.right = self.grab_expr(Parser.SUFFIX_PRECEDENCE["TILDE"])
            return self.check_suffixes(tildenode, -1)

        return n

    def grab_series(self):
        elems = []
        cont = self.next().ttype not in "])"
        while cont:
            elems.append(self.grab_expr(-1))
            if self.next().ttype == "COMMA":
                self.i += 1
            else:
                cont = False
        return elems
