import sys

from src.parser import Parser
from src.typecheck import TypeChecker
from src.evaluate import Interpreter


if __name__ == "__main__":
    if len(sys.argv) == 0:
        print("Please pass the name of an Azor file to execute.")
        sys.exit(1)

    elif sys.argv[0].endswith("azor.py"):
        _, azor_file, *args = sys.argv

    else:
        azor_file, *args = sys.argv

    stdlib_stmts = Parser.parse_file("azor/stdlib.azor")
    stmts = stdlib_stmts + Parser.parse_file(azor_file)

    TypeChecker(stmts).check()

    interpreter = Interpreter(stmts)

    try:
        sys.exit(interpreter.main(args))
    except KeyboardInterrupt:
        pass
