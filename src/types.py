class AzorType:
    ATYPES = {"BOOL", "INT", "LIST", "TUPLE", "FUNCTION"}

    def __init__(self, atype, constituents=None, rtype=None, argtypes=None, subtype=None, argnames=None):
        assert(atype in AzorType.ATYPES)
        self.atype = atype

        if atype == "LIST":
            self.subtype = subtype
        elif atype == "TUPLE":
            self.constituents = constituents
        elif atype == "FUNCTION":
            self.rtype = rtype
            self.argtypes = argtypes
            self.argnames = argnames
            if len(self.argtypes) != len(self.argnames):
                raise ValueError()

    def __eq__(self, other):
        if self.atype != other.atype:
            return False
        if self.atype in {"BOOL", "INT"}:
            return True
        elif self.atype == "LIST":
            return other.subtype == self.subtype
        elif self.atype == "TUPLE":
            return all(t1 == t2 for t1, t2 in zip(self.constituents, other.constituents))
        elif self.atype == "FUNCTION":
            return (self.rtype == other.rtype) and all(t1 == t2 for t1, t2 in zip(self.argtypes, other.argtypes))

    # def subtype(self, other):
    #     if self.atype == "ANY":
    #         return other.atype == "ANY"
    #     elif self.atype == "SIMPLE":
    #         return other.atype in {"ANY", "SIMPLE"}
    #     elif self.atype == "BOOL":
    #         return other.atype in {"BOOL", "ANY", "SIMPLE"}
    #     elif self.atype == "INT":
    #         return other.atype in {"INT", "ANY", "SIMPLE"}
    #     elif self.atype == "LIST":
    #         return self.atype == other.atype
    #     elif self.atype == "TUPLE":
    #         return all(t1.subtype(t2) for t1, t2 in zip(self.constituents, other.constituents))
    #     elif self.atype == "FUNCTION":
    #         return self == other  # TODO

    def __str__(self):
        if self.atype in {"INT", "BOOL"}:
            return self.atype
        elif self.atype == "LIST":
            return f"[{str(self.subtype)}]"
        elif self.atype == "TUPLE":
            return f"({', '.join(str(c) for c in self.constituents)})"
        elif self.atype == "FUNCTION":
            l = [f"{name}:{str(azortype)}" for name, azortype in zip(self.argnames, self.argtypes)]
            return f"{str(self.rtype)}({' '.join(l)})"

    # @staticmethod
    # def typeof(o):
    #     if type(o) is AzorFunction:
    #         return o.azortype
    #     elif type(o) is int:
    #         return INT
    #     elif type(o) is bool:
    #         return BOOL


BOOL = AzorType("BOOL")
INT = AzorType("INT")
NOT_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[BOOL], argnames=["b"])
ARITH_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[INT, INT], argnames=["m", "n"])
COMPARE_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[INT, INT], argnames=["m", "n"])
LOGIC_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[BOOL, BOOL], argnames=["a", "b"])
MAINTYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[], argnames=[])
