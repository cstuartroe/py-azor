import re
import sys

INT_RE = "(-?[1-9][0-9]*|0)"
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
    "!",
    "{",
    "}",
}

ALL_PUNCTUATION = set(BINOP_PRECS.keys()) | COMPARISONS | LOGIC | PUNCT


class Token:
    def __init__(self, line, line_no, col_no, s):
        self.line = line
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

        elif s.startswith('"'):
            val = parse_string(s)
            self.ttype = "STRING" if (val is not None) else None
            self.val = val

        else:
            self.raise_error("Bad token")

    def __str__(self):
        return f"<Token line: {self.line_no}, col: {self.col_no}, s: {repr(self.s)}, type: {self.ttype}, value: {repr(self.val)}>"

    def __repr__(self):
        return str(self)

    def raise_error(self, message):
        s = self.line + "\n"
        s += ' '*self.col_no + '^' + "\n"
        s += f"(line {self.line_no + 1}, column {self.col_no + 1}) " + message
        print(s)
        sys.exit()


ESCAPES = {
    't': '\t',
    'r': '\r',
    'n': '\n',
    '\\': '\\',
    '"': '"',
}


def parse_string(s):
    assert s.startswith('"') and s.endswith('"') and len(s) >= 2

    body = s[1:-1]
    i = 0
    out = ""

    while i < len(body):
        if body[i] == '\\':
            if len(body) >= i + 2 and body[i+1] in ESCAPES:
                out += ESCAPES[body[i+1]]
                i += 2
            else:
                return None
        else:
            out += body[i]
            i += 1

    return [ord(c) for c in out]


def grab_string(line):
    assert line[0] == '"'
    out = line[0]
    i = 1
    while i < len(line):
        if len(line) >= i + 2 and line[i:i+2] == '\\"':
            jump = 2
        else:
            jump = 1

        c = line[i:i+jump]
        out += c
        i += jump

        if c == '"':
            return out

    raise ValueError


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

            elif rest[0] == '"':
                try:
                    s = grab_string(rest)
                except ValueError:
                    Token(line=line, line_no=line_no, col_no=i, s="").raise_error("Invalid string")

            else:
                s = rest[0]

            token = Token(line=line, line_no=line_no, col_no=i, s=s)

            i += len(s)
            yield token

    def tokenize(self):
        tokens = []
        for line_no, line in enumerate(self.lines):
            tokens += self.grab_tokens(line_no, line)
        return tokens
