import sys
import argparse

from src.tokens import Tokenizer
from src.parser import Parser
from src.typecheck import TypeChecker
from src.interpret import Interpreter
from src.compile import Compiler


cli = argparse.ArgumentParser(description="A mini programming language")
cli.add_argument('filename', type=str)
cli.add_argument('-c', '--compile', action='store_true')
cli.add_argument('-o', '--outfile', action='store')


if __name__ == "__main__":
    cli_args = cli.parse_args()
    if cli_args.filename is None:
        print("Please pass the name of an Azor file to execute.")
        sys.exit(1)

    with open(cli_args.filename, "r") as fh:
        lines = fh.readlines()

    tokens = Tokenizer(lines).tokenize()

    stmts = Parser(tokens).parse()

    TypeChecker(stmts).check()

    if cli_args.compile:
        if cli_args.outfile:
            outfile = cli_args.outfile
        elif cli_args.filename.endswith(".azor"):
            outfile = cli_args.filename[:-5] + ".c"
        else:
            print("Please provide an outfile name.")
            sys.exit(1)

        Compiler(stmts).compile(outfile)

    else:
        interpreter = Interpreter(stmts)

        print(interpreter.main())
