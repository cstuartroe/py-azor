import re
import sys

INT_RE = "([1-9][0-9]*|0)"
LABEL_RE = "([a-zA-Z_][a-zA-Z0-9_]*)"

BINOP_PRECS = {
    '+': 2,
    '-': 2,
    '*': 3,
    '/': 3,
    '**': 4,
    '%': 2.
}

COMPARISONS = {
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
}

LOGIC = {
    "|",
    "&",
    "^",
    "!^",
}

PUNCT = {
    '<-',
    ':',
    ',',
    '~',
    "=",
    "(",
    ")",
    "[",
    "]",
    "!"
}

ALL_PUNCTUATION = set(BINOP_PRECS.keys()) | COMPARISONS | LOGIC | PUNCT


class Token:
    def __init__(self, line_no, col_no, s):
        self.line_no = line_no
        self.col_no = col_no
        self.s = s
        self.val = None

        if s == "INT":
            self.ttype = "TYPE"
            self.val = int
        elif s == "BOOL":
            self.ttype = "TYPE"
            self.val = bool

        elif s == "if":
            self.ttype = "IF"
        elif s == "then":
            self.ttype = "THEN"
        elif s == "else":
            self.ttype = "ELSE"

        elif s == "let":
            self.ttype = "LET"
        elif s == "in":
            self.ttype = "IN"
        elif s == "of":
            self.ttype = "OF"

        elif s == "true":
            self.ttype = "BOOL"
            self.val = True
        elif s == "false":
            self.ttype = "BOOL"
            self.val = False
        elif re.fullmatch(INT_RE, s):
            self.ttype = "INT"
            self.val = int(s)
        elif re.fullmatch(LABEL_RE, s):
            self.ttype = "LABEL"
            self.val = s

        elif s in BINOP_PRECS:
            self.ttype = "BINOP"
            self.val = s
        elif s in COMPARISONS:
            self.ttype = "COMPARISON"
            self.val = s
        elif s in LOGIC:
            self.ttype = "LOGIC"
            self.val = s

        elif s in PUNCT:
            self.ttype = s

        else:
            self.ttype = None

    def __str__(self):
        return f"<Token line: {self.line_no}, col: {self.col_no}, s: {repr(self.s)}, type: {self.ttype}, value: {repr(self.val)}>"

    def __repr__(self):
        return str(self)


class Tokenizer:
    def __init__(self, lines):
        self.lines = lines

    def grab_tokens(self, line_no, line):
        i = 0
        while i < len(line):
            rest = line[i:]
            if line[i] in ' \t\r\n':
                i += 1
                continue

            elif re.match(LABEL_RE, rest):
                s = re.match(LABEL_RE, rest).groups()[0]

            elif re.match(INT_RE, rest):
                s = re.match(INT_RE, rest).groups()[0]

            elif rest[:2] in ALL_PUNCTUATION:
                s = rest[:2]

            else:
                s = rest[0]

            token = Token(line_no=line_no, col_no=i, s=s)
            if token.ttype is None:
                self.raise_error(token, "Bad token")

            i += len(s)
            yield token

    def tokenize(self):
        tokens = []
        for line_no, line in enumerate(self.lines):
            tokens += self.grab_tokens(line_no, line)
        return tokens

    def raise_error(self, token, message):
        s = self.lines[token.line_no] + "\n"
        s += ' '*token.col_no + '^' + "\n"
        s += f"(line {token.line_no}, column {token.col_no}) " + message
        print(s)
        sys.exit()
