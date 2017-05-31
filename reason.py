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


class Reasoning:
    def __init__(self):
        pass

    #This method checks if the 2 indexes from WM and KB matches (in syntax, not in each word).
    def do_they_match_for_rule(self, wm_index, kb_index):
        if gl.WM.cp[wm_index].relation == 1 and gl.KB.cp[kb_index].relation == 1:
            wl_index = gl.KB.cp[kb_index].wordlink[0]
            if "%" in gl.WL.wcp[wl_index].word:
                return True
            else:
                return False
        elif gl.WM.cp[wm_index].relation == gl.KB.cp[kb_index].relation:
            if len(gl.WM.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(gl.WM.cp[wm_index].parent)):
                return self.do_they_match_for_rule(gl.WM.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j])

    def get_children_implication(self, kb_index, res_list = None):
        if res_list is None:
            res_list = []
        for i in range(0, gl.KB.cp[kb_index].child.__len__()):
            if gl.KB.cp[gl.KB.cp[kb_index].child[i]].relation == 13:
                res_list.append(gl.KB.cp[gl.KB.cp[kb_index].child[i]])
            else:
                self.get_children_implication(gl.KB.cp[kb_index].child[i], res_list)

    def getCondition(self, impl):
        return impl.parent[0]

    def getRulesFor(self, wm_pos):
        matching_rules = []

        for i in range(0, gl.KB.cp.__len__() - 1):
            match = self.do_they_match_for_rule(wm_pos, i)
            if match:
                matching_rules.append(i)
                print("match: " + gl.WM.cp[wm_pos].mentstr + " " + gl.KB.cp[i].mentstr)
                res_list = []
                self.get_children_implication(i, res_list)

    def createRules(self):
        for i in range(0, gl.WM.cp.__len__() - 1):
            self.getRulesFor(i)

    def createRule(self, wm_pos):
        if wm_pos == -1:
            return
        for i in range(0, gl.KB.cp.__len__()):
            matching_rules = []
            if self.do_they_match_for_rule(wm_pos, i):
                matching_rules.append(i)
        return matching_rules

    def createConceptRules(self, starti, endi):
        # print('starti: ' + str(starti) + '  endi: ' + str(endi) + '  wm size: ' + str(gl.WM.cp.__len__()))

        for wm_pos in range(starti, endi):
            matching_rules = []
            for kb_pos in range(0, gl.KB.cp.__len__()):
                if self.do_they_match_for_rule(wm_pos, kb_pos):
                    matching_rules.append(kb_pos)
            gl.WM.cp[wm_pos].kb_rules = matching_rules

    def addReasonedConcept (self, j, wm_pos, condition1, condition2, implication, rule_words):
        if (gl.WM.cp[j].parent.__len__() > 0):
            first_parent = gl.WM.cp[gl.WM.cp[j].parent[0]].mentstr
            second_parent = gl.WM.cp[gl.WM.cp[j].parent[1]].mentstr
            #print (rule_words)
            if len(rule_words)>0 and first_parent == rule_words['%2'] and gl.WM.cp[j].relation == gl.KB.cp[condition2].relation:
               gl.WM.add_concept(1, gl.KB.cp[implication].relation, [ gl.WM.cp[wm_pos].parent[0], gl.WM.cp[j].parent[1]])
        

    def generateNewConcepts(self, starti, endi):

        for wm_pos in range(starti, endi):
            for rule_nr in range(0, gl.WM.cp[wm_pos].kb_rules.__len__()):
                # print('found rule: ' + gl.KB.cp[gl.WM.cp[wm_pos].kb_rules[rule_nr]].mentstr)
                res_list = []
                self.get_children_implication(gl.WM.cp[wm_pos].kb_rules[0], res_list)

                for i in range(0, res_list.__len__()):
                    if gl.KB.cp[res_list[i].parent[0]].relation == 16:  # the first parent of the IM rule is AND
                        andConcept = gl.KB.cp[res_list[i].parent[0]]
                        condition1 = andConcept.parent[0]               # first concept in AND
                        condition2 = andConcept.parent[1]               # second concept in AND
                        implication = res_list[i].parent[1]             # the implication in IM rule

                        outgoing = gl.KB.cp[res_list[i].parent[1]]

                        if condition1 == gl.WM.cp[wm_pos].kb_rules[rule_nr]:
                            rule_words = {}
                            for j in range(0, gl.KB.cp[condition1].parent.__len__()):
                                rule_words[gl.KB.cp[gl.KB.cp[condition1].parent[j]].mentstr ] = gl.WM.cp[gl.WM.cp[wm_pos].parent[j]].mentstr

                            for j in range(0, gl.WM.cp.__len__()):
                                self.addReasonedConcept(j,wm_pos,condition1,condition2,implication,rule_words)

                        # megvan, hogy %1 -> ez a rule, %2 -> másik, most keresni kell

                        if condition2 == gl.WM.cp[wm_pos].kb_rules[rule_nr]:
                            rule_words = {}
                            for j in range(0, gl.KB.cp[condition2].parent.__len__()):
                                rule_words[ gl.KB.cp[gl.KB.cp[condition2].parent[j]].mentstr ] = gl.WM.cp[gl.WM.cp[wm_pos].parent[j]].mentstr
                        # megvan, hogy %1 -> ez a rule, %2 -> másik, most keresni kell


                        # print('---------')
                        # print('condition1: ' + str(gl.KB.cp[condition1].mentstr))
                        # print('condition2: ' + str(gl.KB.cp[condition2].mentstr))
                        # print('kb_rule: ' + str(gl.KB.cp[gl.WM.cp[wm_pos].kb_rules[rule_nr]].mentstr))
                        # print('---------')
