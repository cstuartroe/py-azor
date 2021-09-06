import re
import sys
from typing import List

INT_RE = "([1-9][0-9]*|0)"
LABEL_RE = "([a-zA-Z_][a-zA-Z0-9_]*)"

BINOP_PRECS = {
    '+': 2,
    '-': 2,
    '*': 3,
    '/': 3,
    '**': 4,
    '%': 3,
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
}

PUNCT = {
    ':',
    ',',
    "=",
    "(",
    ")",
    "!",
}

ALL_PUNCTUATION = set(BINOP_PRECS.keys()) | COMPARISONS | LOGIC | PUNCT


class Token:
    def __init__(self, line: str, line_no: int, col_no: int, s: str):
        self.line = line
        self.line_no = line_no
        self.col_no = col_no
        self.s = s

        if s == "if":
            self.ttype = "IF"
        elif s == "then":
            self.ttype = "THEN"
        elif s == "else":
            self.ttype = "ELSE"

        elif s == "true":
            self.ttype = "BOOL"
        elif s == "false":
            self.ttype = "BOOL"
        elif re.fullmatch(INT_RE, s):
            self.ttype = "INT"
        elif re.fullmatch(LABEL_RE, s):
            self.ttype = "LABEL"

        elif s in BINOP_PRECS:
            self.ttype = "BINOP"
        elif s in COMPARISONS:
            self.ttype = "COMPARISON"
        elif s in LOGIC:
            self.ttype = "LOGIC"

        elif s in PUNCT:
            self.ttype = s

        else:
            self.raise_error("Bad token")

    def __repr__(self):
        return f"<Token line_no: {self.line_no}, col_no: {self.col_no}, s: {repr(self.s)}, type: {self.ttype}>"

    def raise_error(self, message):
        s = self.line + "\n"
        s += ' '*self.col_no + '^' + "\n"
        s += f"(line {self.line_no + 1}, column {self.col_no + 1}) " + message
        print(s)
        sys.exit(1)


class Tokenizer:
    def __init__(self, lines: List[str]):
        self.lines = lines

    def grab_tokens(self, line_no: int):
        line = self.lines[line_no]
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

            token = Token(line=line, line_no=line_no, col_no=i, s=s)

            i += len(s)
            yield token

    def tokenize(self):
        tokens = []

        for line_no in range(len(self.lines)):
            tokens += self.grab_tokens(line_no)

        return tokens
