import re
import sys

INT_RE = "([1-9][0-9]*|0)"
LABEL_RE = "([a-zA-Z_][a-zA-Z0-9_]*)"
PUNCT = {'+', '-', '*', '%', '==', '!=', '<', '>', '<=', '>=', '&', '|', '^', '^!',
         '->', ':', ',', '~'}


class Token:
    def __init__(self, line_no, col_no, s):
        self.line_no = line_no
        self.col_no = col_no
        self.s = s
        self.settype(s)

    def settype(self, s):
        if s == "true":
            self.ttype = "BOOL"
            self.val = True
        elif s == "false":
            self.ttype = "BOOL"
            self.val = False
        elif s == "INT":
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
        elif s == "with":
            self.ttype = "WITH"
        elif re.fullmatch(INT_RE, s):
            self.ttype = "INT"
            self.val = int(s)
        elif re.fullmatch(LABEL_RE, s):
            self.ttype = "LABEL"
            self.val = s
        elif s in "[]()":
            self.ttype = s
        elif s == "=":
            self.ttype = "EQUAL"
        elif s == "!":
            self.ttype = "LABEL"
            self.val = '!'
        elif s == "->":
            self.ttype = "ARROW"
        elif s == ":":
            self.ttype = "COLON"
        elif s == ",":
            self.ttype = "COMMA"
        elif s == "~":
            self.ttype = "TILDE"
        elif s in PUNCT:
            self.ttype = "LABEL"
            self.val = s
        else:
            self.ttype = None

    def __str__(self):
        return self.s

    def __repr__(self):
        return repr(str(self))


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
            elif rest[:2] in PUNCT:
                s = rest[:2]
            elif rest[0] in PUNCT:
                s = rest[0]
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
