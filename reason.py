import gl, conc

class Rule:
    def __init__(self,actualconcept):       # an instance represents a single rule to apply for the actual concept
        self.actual = actualconcept         # index of concept in WM for which we found a rule
        self.rule = -1                      # index of rule in KB, an IM(g,k) concept
        self.condition = []                 # indices (in KB) of a,b,c in IM(Z(a,b),k)  . here c=Z(a,b)
        self.match=[]                       # indices of m,n,q in WM, where m matches a, n matches b etc
        self.matchrelation=-2               # if for example b=X(%2,%3) and n matches b, then we store the relation found in m
        self.matchvalue = []                # %1 %2 %3 matching concepts
        self.matchp = []                    # p1 p2 etc matching p values

    # According to the e-mail of Zoltan, this is an exercise for the search:
    def jo_gyakorlat_1(self, wm_index):
        if gl.WM.cp[wm_index].relation == 1:
            wordlink_num = gl.WM.cp[wm_index].wordlink[0]
            for j in range(0, len(gl.KB.cp)):
                if gl.KB.cp[j].relation == 1:
                    if wordlink_num == gl.KB.cp[j].wordlink[0]:
                        # I have found the word!
                        print('Kblink for word in WM: ' + gl.WL.wcp[wordlink_num].word)
                        return
        else:
            for k in range(0, len(gl.WM.cp[wm_index].parent)):
                for j in range(0, len(gl.KB.cp)):
                    if gl.KB.cp[j].relation == gl.WM.cp[wm_index].relation:
                        for l in range(0, gl.WM.cp[wm_index].parent):
                            self.jo_gyakorlat_1(l)
                            # parent check

                print('parent - ')
                print(gl.WM.cp[gl.WM.cp[wm_index].parent[k]].mentstr)

    def do_they_match(self, wm_index, kb_index):
        if gl.WM.cp[wm_index].relation == 1 and gl.KB.cp[kb_index].relation == 1:
            wordlink_num = gl.WM.cp[wm_index].wordlink[0]
            if wordlink_num == gl.KB.cp[kb_index].wordlink[0]:
                return True
            else:
                return False
        elif gl.WM.cp[wm_index].relation == gl.KB.cp[kb_index].relation:
            if len(gl.WM.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(gl.WM.cp[wm_index].parent)):
                return self.do_they_match(gl.WM.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j])

    def jo_gyakorlat_caller(self):
        map_of_eq = {}
        for j in range(0, len(gl.WM.cp)):
            for k in range(0, len(gl.KB.cp)):
                equality = self.do_they_match(j, k)
                if equality == True:
                    map_of_eq[j] = k
                    break
