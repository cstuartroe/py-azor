import sys

from src.tokens import Tokenizer


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please pass the name of an Azor file to execute.")
        sys.exit(1)

    azor_filename = sys.argv[-1]

    with open(azor_filename, "r") as fh:
        lines = fh.readlines()

    tokens = Tokenizer(lines).tokenize()

    for token in tokens:
        print(token)
