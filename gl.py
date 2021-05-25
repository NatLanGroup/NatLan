import sys


# This is a "glue" module

class Arguments:
    def __init__(self):
        self.argnum = len(sys.argv)
        self.pdefault=4         #default value of p
        self.pdef_unknown=2
        self.pgranu = 4         # granularity for p, pgranu+1 discrete values from 0 set pgranu=pmax for p=0,1,2,....pmax
        self.cmax = 5           # max for consistency
        self.bmax = 5           # max for branch consistency (branchvalue)
        self.pmax = 4           # maximum p value. Like 1 for p=0..1, or 4 for p=0,1,2,3,4.
        self.rmax = 4           # maximum relevance
        self.rmove = 3          # limit from which concept is moved to KB
        self.gmax = 1           # max for generality
        self.gmin = 0           # threshold for generality for concept to be specific
        self.amax = 4           # maximum activation
        self.asec = 2           # level of second round spreading activation
        self.exmax = 4          # concept exception max value
        self.exdef = 2          # concept exception default value
        self.kmax = 4           # concept known max value
        self.eachmax = 4        # concept each property: level of exceptions
        self.timecheck = {}      # time consumption mapped to function name
        self.total_reasoncount = 0  # debug. all reasoning attempts.
        self.success_reasoncount=0  # debug. reasoned concepts.

        self.upd_pvalue = 1     # switch on p (etc) value update when contradicting, in update_Dimensions
        self.paragraph_tokb = 1 # switch for previous paragraph to move to kb. 0 means no move to kb.
        
        self.loglevel = 1       # level of logging. 0 is least log.
        self.tr_reas = 1        # track limit for REASONED
        self.tr_upd = 1         # track limit for UPDATE
        self.tr_reject = 2      # track limit for REJECT (do not update KB based on WM)
        self.tr_over = 1        # track limit for OVERRIDE p, known overrides
        self.tr_inp = 1         # track limit for INPUT
        self.tr_match = 4       # track level for MATCHING
        self.tr_att = 1         # track level for ATTEMPT
        self.tr_attcd = 2       # track level for ATTEMPT CD
        self.tr_dis = 1         # track level for DISABLE
        self.tr_stop = 1        # track limit for STOP stopping / inhibiting of add concept. (usually reason.)
        self.tr_addkb = 3       # track limit for ADDKB
        self.tr_add = 3         # track additions in WM ADD
        self.tr_finaladd = 3    # track additions in WM ADD (FIN) from finaladd_concept
        self.tr_set_spec = 2    # SET_SPEC most_special_use got set
        self.tr_act = 1         # ACTIV (KB) activated concepts in KB
        

      
        self.im = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 3, 3], [2, 2, 2, 3, 4]]         # IM rule
        self.kp_im = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 1, 1, 1], [0, 0, 1, 2, 2], [0, 0, 1, 2, 2]]      # known conversion for IM rule, addressed by p1,p2        
        self.can = [[0, 0, 0, 0, 0], [0, 1, 1, 1, 1], [0, 1, 2, 2, 2], [0, 1, 2, 3, 3], [0, 1, 2, 3, 4]]        # can rule
        self.cando = [0,1,2,2,2]                                                                                # cando rule
        self.does = [2,3,4,4,4]                                                                                 # does rule: doing sth means can do it
        self.cannot = [2,2,2,1,0]                                                                               # cannot rule
        self.pide1 = [0,1,2,3,4]                                                                                # D-rule single arg
        self.kp_pide1 = [2,2,2,2,2]                                                                                # known D-rule single arg
        self.pos1 = [2,2,2,3,4]                                                                                 # if special then general: IM(C(%1,F(%2,%3)),C(%1,%3))
        self.kp_pos1 = [0,0,1,2,2]                                                                                 # known: if special then general: IM(C(%1,F(%2,%3)),C(%1,%3))  IM(A(%1,live),C(%1,animal))
        self.pnot1 = [4,3,2,1,0]                                                                                # NOT() rule
        self.kp_pnot1 = [2,2,2,2,2]                                                                                # known: NOT() rule
        self.idedegrade = [1,1,2,3,3]                                                                           # degrading D rule
        self.pide2 = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [1, 1, 2, 2, 3], [0, 1, 2, 3, 4]]      # D-rule IM(AND(D(),D()),D())
        self.kp_pide2 = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [1, 1, 1, 1, 2]]      # known: D-rule IM(AND(D(),D()),D())
        self.pand = [[0, 0, 0, 0, 0], [0, 1, 1, 1, 1], [0, 1, 2, 2, 2], [0, 1, 2, 3, 3], [0, 1, 2, 3, 4]]       # AND-rule
        self.pclass = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [1, 1, 2, 2, 3], [0, 1, 2, 3, 4]]     # class relation
        self.kp_pclass = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2]]  # known conversion for class rule, addressed by p1,p2        
        self.degrade = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [1, 1, 2, 2, 3], [1, 1, 2, 3, 3]]    # degraded class
        # pclass is the matrix for class reasoning. C(%1,%2)p1 and %X(%2,%3)p2 -> %x(%2,%3)pclas, pclass[p2,p1]
        self.pxor = [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 1, 1], [2, 2, 2, 1, 0]]
        self.consist = [[4,4,3,3,2,0],[3,3,4,3,2,1],[3,3,4,3,3,3],[3,3,3,4,3,3],[1,2,3,3,4,3],[0,2,3,3,3,4]]        #consistency conversion for pair of concepts
        self.branchvalue = [[0,0,0,0,0,0],[0,1,1,1,1,1],[0,1,2,2,2,3],[0,2,3,3,3,4],[1,2,3,4,4,5],[2,3,4,5,5,5]]   #consistency conversion for entire branch
        self.branch_kill = [0,1,2,2,3,4]   # index = best branch value. output=limit below which branch is killed.
        self.pmap = {
            "im":self.im, "pide1":self.pide1,"pos1":self.pos1,"pide2":self.pide2,"pclass":self.pclass,"pxor":self.pxor,
            "idedegrade":self.idedegrade, "degrade":self.degrade, "pnot1":self.pnot1, "pand":self.pand,
            "can":self.can, "cando":self.cando, "does":self.does,"cannot":self.cannot,"kp_im":self.kp_im,"kp_pclass":self.kp_pclass,
            "kp_pide1":self.kp_pide1, "kp_pos1":self.kp_pos1, "kp_pnot1":self.kp_pnot1, "kp_pide2":self.kp_pide2
        }
        self.avg_lookback = 10                                                  # rolling average on this number of occurence. avg=0.9*avg+0.1*current
        self.worst_known = [[0,0,0,0,0],[0,1,1,1,1],[0,1,2,2,2],[0,1,2,3,3],[0,1,2,3,4]]   # known conversion from two known values
        self.k_advan = [[4,4,4,4,4],[4,0,1,2,3],[4,1,0,1,2],[4,2,1,0,1],[4,3,2,1,0]]    # known advantage conversion from two known values

        self.pdiff = [                                                                  # p diff conversion, top level: known advantage. next:
            [[0,1,2,3,4],[1,0,1,2,3],[2,1,0,1,2],[3,2,1,0,1],[4,3,2,1,0]],              # next: better known p last: less known p
            [[0,0,1,2,3],[0,0,0,1,2],[1,0,0,0,1],[2,1,0,0,0],[3,2,1,0,0]],
            [[0,0,0,1,2],[0,0,0,0,1],[0,0,0,0,0],[1,0,0,0,0],[2,1,0,0,0]],
            [[0,0,0,0,1],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[1,0,0,0,0]],
            [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]]

        self.pe_final = [                                                               # p or exception conversion, top level: known advantage. next:
            [[0,1,1,2,2],[1,1,2,2,2],[1,2,2,2,3],[2,2,2,3,3],[2,3,3,3,4]],              # next: better known p/exception last: less known p/exception
            [[0,0,1,1,2],[1,1,1,2,2],[2,2,2,2,2],[2,2,3,3,3],[3,3,3,3,4]],
            [[0,0,0,1,1],[1,1,1,1,2],[2,2,2,2,2],[2,2,3,3,3],[3,3,3,4,4]],
            [[0,0,0,0,1],[1,1,1,1,2],[2,2,2,2,2],[2,3,3,3,3],[3,3,4,4,4]],
            [[0,0,0,0,0],[1,1,1,1,1],[2,2,2,2,2],[3,3,3,3,3],[4,4,4,4,4]]]

        self.pmerge = [[0,1,1,1,2],[1,1,2,2,2],[1,2,2,2,3],[1,2,2,3,3],[2,2,3,3,4]]     # merge two p values equally known

        self.excep_final = [[0,0,1,1,1],[1,1,1,2,2],[2,2,2,2,3],[3,3,3,3,4],[4,4,4,4,4]]    # final exception value from pe_final and pdiff

        self.consist_final = [[4,4,3,2,0],[4,4,4,3,0],[4,4,4,4,3],[4,4,4,4,4],[4,4,4,4,4]]  # final consistency. Top: final exception. last: pdiff.                                                                           # TO DO: take input consistency into account !!

        self.known_final = [[0,0,0,0,0,0],[0,1,1,1,1,1],[1,1,1,2,2,2],[1,2,2,2,3,3],[1,2,2,3,4,4]]  # final klnown value. top:higher known value. next: avg consistency


        self.rcode = {
            "X":99, "W": 1, "S": 2, "D": 3, "C": 4, "F": 5,
            "Q": 6, "A": 7, "I": 8, "R": 9, "T": 10,
            "P": 11, "M": 12, "IM": 13, "N": 14, "V": 15,
            "AND": 16, "NOT": 17, "OR": 18, "XOR": 19
        }

        self.rcodeBack = {
            99:"X", 1: "W", 2: "S", 3: "D", 4: "C", 5: "F",
            6: "Q", 7: "A", 8: "I", 9: "R", 10: "T",
            11: "P", 12: "M", 13: "IM", 14: "N", 15: "V",
            16: "AND", 17: "NOT", 18: "OR", 19: "XOR"
        }

        self.noxx = [2,3,4,13,15,16,18,19]   #these relations make no sense in form of D(x,x) 

        self.noreplace = {                                              # for these relations (index of dict) no C reasoning possible on given arguments (value)
            1:[99],2:[99],3:[0,1,2],4:[1,2],5:[1,2],6:[99],7:[1,2],8:[0],9:[99],10:[99],       #all relations must have a dummy value 99 at least
            11:[1,2],12:[99],13:[99],14:[99],15:[99],16:[99],17:[99],18:[99],19:[99]
        }

        self.enable_repl = {                        # these are valid replacements. higher level enabled: [list of lower level enabling]
            7:[8], 4:[11], 5:[9]  }
            
        self.inhibit_pstruct = {                     # structures of parents that should not be reasoned
            "F(F(%1,%2),%2)", "A(F(%1,%2,-ing),%2)"  }

        self.noactivate_fromword ={                 # some concepts should not be activated from word if found in the given position
            4:[1]  }                                # relation not to activate : [list of positions of word]

        self.kbactiv_limit = [0,1,2,3,4] # limit of relevance, for KB concept activation, based on input occurence. Dimension is level deepness in terms of children.
                                # [0,1,2,3,4] means to activate first children concepts of the input (first children: round=2, threshold=2). But for children of children limit=3.
                                # [0,1,2,2,2] means children on all levels are activated.
        self.kbactiv_qlimit = [0,1,2,3,4] # limit of relevance, for KB concept activation, for question
                                # [0,2,2,1,0] means ordinary concepts in the input (round=1, r=2, threshold=2) activate all children in KB        
#        self.kbactiv_spreadlimit = [0,4,2,1,0] # TO DO IMPLEMENT: limit of relevance, for KB concept spreading activation. Dimension is activation round.
        self.kbactiv_addone =   { 4:{1:2}, 11:{1:0}, 7:{1:1}, 5:{1:1} }  
                            # somewhat inhibit some activations in KB. relation:{parent:addition}. exceptions to kbactiv_limit activations: relevance limit higher C(.., x) and P(.., x) is activated based on x with higher limit=+1.
            
        self.subject_rel = {5,6,7,9,11,17}          # concepts which have the subject of the proposition in the first argument like A(subject, ...)

        self.nospread_general = [0]                 # some rules should not spread .general backwards in reasonuse

    def settimer(self,fname,timeused):              # measure time spent in a function
        try: self.timecheck[fname] += timeused      # increase time spent in fname
        except: self.timecheck[fname] = timeused      # newly add time spent in fname

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
