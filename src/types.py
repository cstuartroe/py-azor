from itertools import zip_longest


class AzorType:
    ATYPES = {"BOOL", "INT", "FUNCTION"}

    def __init__(self, atype, rtype=None, args=None):
        self.atype = atype

        if atype == "FUNCTION":
            self.rtype = rtype
            self.args = args

    def argtypes(self):
        return list(self.args.values())

    def __eq__(self, other):
        if self.atype != other.atype:
            return False

        if self.atype in {"BOOL", "INT"}:
            return True

        elif self.atype == "FUNCTION":
            if self.rtype != other.rtype:
                return False

            for t_self, t_other in zip_longest(self.argtypes(), other.argtypes()):
                if t_self != t_other:
                    return False

            return True

        else:
            raise ValueError

    def __str__(self):
        if self.atype == "FUNCTION":
            return f"{self.rtype}({str(self.args)[1: -1]})"
        else:
            return self.atype


BOOL = AzorType("BOOL")
INT = AzorType("INT")

ARITH_TYPE = AzorType("FUNCTION", rtype=INT, args={"m": INT, "n": INT})
COMPARE_TYPE = AzorType("FUNCTION", rtype=BOOL, args={"m": INT, "n": INT})
LOGIC_TYPE = AzorType("FUNCTION", rtype=BOOL, args={"a": BOOL, "b": BOOL})

MAIN_TYPE = AzorType("FUNCTION", rtype=INT, args={})
