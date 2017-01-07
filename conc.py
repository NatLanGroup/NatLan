import sys, gl


def match(what1, inwhat):  # two concepts match? handles questions
    # TODO should we use booleans instead numbers?
    # e.g. result = True
    yes = 1;
    sparents = []
    if what1.relation != -1 and what1.relation != inwhat.relation:
        yes = 0  # relation is either same or -1
    else:
        for item in what1.parent: sparents.append(item)
        pindex = 0
        for parentitem in sparents:
            if parentitem == -1:  # -1 indicates question mark, this is considered as matching
                try:
                    sparents[pindex] = inwhat.parent[pindex]
                except:
                    yes = yes
            pindex = pindex + 1
        if sparents != inwhat.parent: yes = 0
        return yes


class Concept:
    def __init__(self):
        self.p = 0.5  # p value of concept
        self.relation = 2  # relation code
        self.parent = []  # parents list
        self.child = []  # children list

    def add_parents(self, parents):
        for parentitem in parents: self.parent.append(parentitem)


class Kbase:
    def __init__(self, instancename):
        self.cp = []  # CONCEPT LIST CP
        self.ci = -1
        self.name = instancename  # the name of the instance can be used in the log file

    def add_concept(self, new_p, new_rel, new_parents):  # add new concept to WM or KB. parents argument is list
        self.cp.append(Concept())  # concept added
        self.ci = len(self.cp) - 1  # current index
        self.cp[self.ci].p = new_p  # set p value
        self.cp[self.ci].relation = new_rel  # set relation code
        self.cp[self.ci].add_parents(new_parents)  # set parents
        gl.log.add_log((self.name, " add_concept index=", self.ci))  # content to be logged is tuple (( ))
        return self.ci

    def search_inlist(self, swhat):
        found = [0]
        sindex = 0
        for conitem in self.cp:
            if match(swhat, conitem) == 1:
                found.append(sindex)  # add to found list
                found[0] = found[0] + 1  # increase number of items found
            sindex = sindex + 1
        return found


if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
