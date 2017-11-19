import sys


# This is a "glue" module

class Arguments:
    def __init__(self):
        self.argnum = len(sys.argv)
        self.pdefault=1         #default value of p
        self.pdef_unknown=0.5
        self.pgranu = 4         # granularity for p, pgranu+1 discrete values from 0
        self.pmax = 4           # maximum p value. Like 1 for p=0..1, or 4 for p=0,1,2,3,4.
        self.rmax = 4           # maximum relevance
                                # set pgranu=pmax for p=0,1,2,....pmax
        
        i=1.1                   # to be used instead of 1
        self.im = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 3, 3], [2, 2, 2, 3, 4]]         # IM rule
        self.pide1 = [0,i,2,3,4]                                                                                # D-rule single arg
        self.pide2 = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [i, i, 2, 2, 3], [0, i, 2, 3, 4]]      # D-rule IM(AND(D(),D()),D())
        self.pclass = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [i, i, 2, 2, 3], [0, i, 2, 3, 4]]
        self.pxor = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, i, i], [2, 2, 2, i, 0]]
        # pclass is the matrix for class reasoning. C(%1,%2)p1 and %X(%2,%3)p2 -> %x(%2,%3)pclas, pclass[p2,p1]
        self.pmap = {"pide1":self.pide1,"pide2":self.pide2,"pclass":self.pclass,"pxor":self.pxor}

        self.rcode = {
            "X":-1, "W": 1, "S": 2, "D": 3, "C": 4, "F": 5,
            "Q": 6, "A": 7, "I": 8, "R": 9, "T": 10,
            "P": 11, "M": 12, "IM": 13, "N": 14, "V": 15,
            "AND": 16, "NOT": 17, "OR": 18, "XOR": 19
        }

        self.rcodeBack = {
            -1:"X", 1: "W", 2: "S", 3: "D", 4: "C", 5: "F",
            6: "Q", 7: "A", 8: "I", 9: "R", 10: "T",
            11: "P", 12: "M", 13: "IM", 14: "N", 15: "V",
            16: "AND", 17: "NOT", 18: "OR", 19: "XOR"
        }


class Logging:
    def __init__(self, fname="logfile.txt"):
        try:
            self.logf = open(fname, "w")
        except:
            print("ERROR: Logging: log file could not be opened")

    def add_log(self, what):  # what must be iterable
        try:
            for item in what: self.logf.write(str(item))
            self.logf.write("\n")
        except:
            print("ERROR: Logging: log file not present or called incorrectly", str(what))


if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
