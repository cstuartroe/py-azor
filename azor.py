import sys

from src.tokens import Tokenizer
from src.parser import Parser
from src.typecheck import TypeChecker


if __name__ == "__main__":
    with open(sys.argv[1], "r") as fh:
        code = fh.read().replace('\t', '    ')

    lines = code.split("\n")
    t = Tokenizer(lines)
    p = Parser(t)
    tc = TypeChecker(p)
    tc.check()
    tc.evaluate()
    tc.execute_main()
