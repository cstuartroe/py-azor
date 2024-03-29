class AzorType:
    ATYPES = {"BOOL", "INT", "LIST", "TUPLE", "FUNCTION", "GENERIC"}

    def __init__(self, atype, constituents=None, rtype=None, argtypes=None, etype=None, argnames=None,
                 generics=None, label=None):
        assert(atype in AzorType.ATYPES)
        self.atype = atype

        if atype == "LIST":
            self.etype = etype
        elif atype == "TUPLE":
            self.constituents = constituents
        elif atype == "GENERIC":
            self.label = label
        elif atype == "FUNCTION":
            self.rtype = rtype
            if argnames is not None and len(argtypes) != len(argnames):
                raise ValueError()
            self.argtypes = argtypes
            self.argnames = argnames
            self.generics = generics

    def resolve_generics(self, spec):
        if self.atype in {"BOOL", "INT"}:
            return self
        elif self.atype == "LIST":
            return AzorType(atype="LIST", etype=self.etype.resolve_generics(spec))
        elif self.atype == "TUPLE":
            return AzorType(atype="TUPLE", constituents=[
                c.resolve_generics(spec) for c in self.constituents
            ])
        elif self.atype == "GENERIC":
            return spec[self.label]
        elif self.atype == "FUNCTION":
            return AzorType(
                atype="FUNCTION",
                rtype=self.rtype.resolve_generics(spec),
                argtypes=[t.resolve_generics(spec) for t in self.argtypes],
                argnames=self.argnames,
            )

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
        elif self.atype == "GENERIC":
            return self.label == other.label
        else:
            raise ValueError

    def __repr__(self):
        if self.atype in {"INT", "BOOL"}:
            return self.atype
        elif self.atype == "LIST":
            return f"[{str(self.etype)}]"
        elif self.atype == "TUPLE":
            return f"({', '.join(str(c) for c in self.constituents)})"
        elif self.atype == "FUNCTION":
            if self.argnames is not None:
                l = [f"{name}:{azortype}" for name, azortype in zip(self.argnames, self.argtypes)]
            else:
                l = map(str, self.argtypes)
            return f"{self.rtype}({', '.join(l)})"
        elif self.atype == "GENERIC":
            return self.label


BOOL = AzorType("BOOL")
INT = AzorType("INT")
NIL = AzorType("TUPLE", constituents=[])
ARITH_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[INT, INT], argnames=["m", "n"])
COMPARE_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[INT, INT], argnames=["m", "n"])
LOGIC_TYPE = AzorType("FUNCTION", rtype=BOOL, argtypes=[BOOL, BOOL], argnames=["a", "b"])

INT_LIST = AzorType("LIST", etype=INT)

PRINT_TYPE = AzorType("FUNCTION", rtype=NIL, argtypes=[INT_LIST])
INPUT_TYPE = AzorType("FUNCTION", rtype=INT_LIST, argtypes=[])
RAND_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[INT])
MAIN_TYPE = AzorType("FUNCTION", rtype=INT, argtypes=[AzorType("LIST", etype=INT_LIST)], argnames=["args"])
