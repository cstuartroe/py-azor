class AzorType:
    ATYPES = {"BOOL", "INT", "LIST", "TUPLE", "FUNCTION"}

    def __init__(self, atype, constituents=None, rtype=None, argtypes=None, etype=None, argnames=None):
        assert(atype in AzorType.ATYPES)
        self.atype = atype

        if atype == "LIST":
            self.etype = etype
        elif atype == "TUPLE":
            self.constituents = constituents
        elif atype == "FUNCTION":
            self.rtype = rtype
            if argnames is not None and len(argtypes) != len(argnames):
                raise ValueError()
            self.argtypes = argtypes
            self.argnames = argnames

    def __eq__(self, other):
        if self.atype != other.atype:
            return False
        if self.atype in {"BOOL", "INT"}:
            return True
        elif self.atype == "LIST":
            return other.etype == self.etype
        elif self.atype == "TUPLE":
            return all(t1 == t2 for t1, t2 in zip(self.constituents, other.constituents))
        elif self.atype == "FUNCTION":
            return (self.rtype == other.rtype) and all(t1 == t2 for t1, t2 in zip(self.argtypes, other.argtypes))

    def __repr__(self):
        if self.atype in {"INT", "BOOL"}:
            return self.atype
        elif self.atype == "LIST":
            return f"[{str(self.etype)}]"
        elif self.atype == "TUPLE":
            return f"({', '.join(str(c) for c in self.constituents)})"
        elif self.atype == "FUNCTION":
            l = [f"{name}:{azortype}" for name, azortype in zip(self.argnames, self.argtypes)]
            return f"{self.rtype}({', '.join(l)})"


BOOL = AzorType("BOOL")
INT = AzorType("INT")
NOT_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[BOOL], argnames=["b"])
ARITH_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[INT, INT], argnames=["m", "n"])
COMPARE_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[INT, INT], argnames=["m", "n"])
LOGIC_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[BOOL, BOOL], argnames=["a", "b"])

INT_LIST = AzorType("LIST", etype=INT)

PRINT_TYPE = AzorType("FUNCTION", rtype=INT_LIST, argtypes=[INT_LIST])
INPUT_TYPE = AzorType("FUNCTION", rtype=INT_LIST, argtypes=[])
RAND_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[INT])
MAIN_TYPE = AzorType("INT")
