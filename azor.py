#!/home/cstuartroe/git_repos/azor/venv/bin/python

import sys

from src.tokens import Tokenizer
from src.parser import Parser
from src.typecheck import TypeChecker
from src.evaluate import Interpreter


if __name__ == "__main__":
    with open(sys.argv[1], "r") as fh:
        code = fh.read().replace('\t', '    ')

    lines = code.split("\n")
    t = Tokenizer(lines)
    p = Parser(t)
    tc = TypeChecker(p)
    tc.check()
    interpreter = Interpreter(tc.stmts)
    print(''.join(chr(n) for n in interpreter.main()))
