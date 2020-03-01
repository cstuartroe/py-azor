from .tokens import Token, Tokenizer


class Node:
    NODETYPES = {"SIMPLE", "LIST", "TUPLE", "STATEMENT", "CALL", "IF", "UNPACK", "TYPE"}

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
            return f"[{' '.join(str(e) for e in self.elements)}]"
        elif self.ntype == "TUPLE":
            return f"({' '.join(str(e) for e in self.elements)})"
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
        left = self.grab_expr()
        if left.ntype == "CALL":
            if left.left.ntype != "TYPE":
                self.tokenizer.raise_error(left.start_token, "Declarations must include a type")
            for arg in left.args.elements:
                if arg.ntype != "TYPE":
                    self.tokenizer.raise_error(arg.start_token, "All arguments must include a type annotation")
        elif left.ntype != "TYPE":
            self.tokenizer.raise_error(left.start_token, "Declarations must include a type")

        self.expect('=')
        self.lhs = False

        right = self.grab_expr()

        n = Node(left.start_token, "STATEMENT")
        n.left = left
        n.right = right
        return n

    def grab_expr(self):
        if self.next().ttype == '[':
            n = Node(self.next(), "LIST")
            self.i += 1
            n.elements = self.grab_series()
            self.expect(']')
            return n

        elif self.next().ttype == '(':
            start_token = self.next()
            self.i += 1

            if self.next().ttype == "IF":
                self.i += 1
                n = Node(start_token, "IF")
                n.condition = self.grab_expr()
                self.expect('then')
                n.left = self.grab_expr()
                self.expect('else')
                n.right = self.grab_expr()

            elif self.next().ttype == ")":
                n = Node(start_token, "TUPLE")
                n.elements = []

            else:
                expr = self.grab_expr()

                if self.next().ttype == "ARROW":
                    self.i += 1
                    n = Node(start_token, "UNPACK")
                    n.condition = expr
                    n.left = self.grab_expr()
                    n.right = self.grab_expr()
                    for e in n.left, n.right:
                        if e.ntype != "SIMPLE" or e.start_token.ttype != "LABEL":
                            self.tokenizer.raise_error(e.start_token, "Must be a label")

                else:
                    n = Node(start_token, "TUPLE")
                    elements = self.grab_series()
                    n.elements = [expr] + elements

            self.expect(')')
            return n

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

        if not self.eof() and self.next().ttype == "COLON":
            if n.ntype != "SIMPLE" or n.start_token.ttype != "LABEL":
                self.tokenizer.raise_error(n.start_token, "Cannot declare type of a non-label")
            elif not self.lhs:
                self.tokenizer.raise_error(self.next(), "Type annotations not allowed on rhs")
            expr = Node(n.start_token, "TYPE")
            expr.left = n
            self.expect(':')
            expr.right = self.grab_expr()
            n = expr

        if not self.eof() and self.next().ttype == "(":
            call = Node(n.start_token, "CALL")
            call.left = n
            call.args = self.grab_expr()
            if call.args.ntype != "TUPLE":
                self.tokenizer.raise_error(call.args.start_token, "Args must be a tuple")
            n = call

        return n

    def grab_series(self):
        elems = []
        while self.next().ttype not in "])":
            elems.append(self.grab_expr())
        return elems
