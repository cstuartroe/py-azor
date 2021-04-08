#!/home/cstuartroe/git_repos/azor/venv/bin/python

import sys

from src.parser import Parser
from src.typecheck import TypeChecker
from src.evaluate import Interpreter


if __name__ == "__main__":
    stdlib_stmts = Parser.parse_file("stdlib.azor")
    stmts = stdlib_stmts + Parser.parse_file(sys.argv[1])

    TypeChecker(stmts).check()

    interpreter = Interpreter(stmts)
    sys.exit(interpreter.main())
