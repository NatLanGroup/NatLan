import sys
min=0
max=1                   #global variables for p,r min,max value

class Arguments:
    def __init__(self):
        self.argnum=len(sys.argv)
        global WL, KB, WM                       #global variables for word list, knowledgebase, working memory
        WM = Kbase("WM")                        # WORKING MEMORY
        KB = Kbase("KB")                        # KNOWLEDGE BASE
        WL = Wlist("WL")                        # WORD LIST
        self.pgranu=4                           # granularity for p, pgranu+1 discrete values from 0
        self.pclas=[[0,0,0,0,0],[0,1,1,1,1],[0,1,1,2,2],[0,1,2,2,3],[0,1,2,3,4]]     #pclas is the matrix for class reasoning. C(%1,%2)p1 and %X(%2,%3)p2 -> %x(%2,%3)pclas, pclas[p2,p1]
        self.relationcode={"W":1,"S":2,"D":3,"C":4,"F":5,"Q":6,"A":7,"I":8,"R":9,"T":10,"P":11,"M":12,"IM":13,"N":14,"V":15,"AND":16,"NOT":17,"OR":18,"XOR":19}

class Logging:
    def __init__(self,fname="logfile.txt"):
        try: self.logf=open(fname,"w")
        except: print("ERROR: Logging: log file could not be opened")

    def add_log(self,what):                                 #what must be iterable
        try:
            for item in what: log.logf.write(str(item))
            log.logf.write("\n")
        except: print("ERROR: Logging: log file not present or called incorrectly",str(what))
        


# ******** START FILE CONC.PY **********

class Concept:
    def __init__(self):
        self.p=0.5                      #p value of concept
        self.relation=0                 #relation code
        self.parent = []                #parents list
        self.child = []                 #children list

class Kbase:
    def __init__(self,instancename):
        self.cp = []                    # CONCEPT LIST CP
        self.name=instancename          # the name of the instance can be used in the log file

    def add_concept(self,new_p,new_rel,new_parents):        #add new concept to WM or KB. parents argument is list
        self.cp.append(Concept())                           #concept added
        self.ci=len(self.cp)-1                              #current index
        self.cp[self.ci].p=new_p                            #set p value
        self.cp[self.ci].relation=new_rel                   # set relation code
        for parentitem in new_parents:                      #set parents
            self.cp[self.ci].parent.append(parentitem)
        log.add_log((self.name," add_concept index=",self.ci))      #content to be logged is tuple (( ))

# *****************  START FILE WORD.PY   *****************

class Word:
    def __init__(self,wordstring):
        self.word = str(wordstring)                     # a Word object has the word string itself
        self.wchild = []                                # a Word object has the meanings, indices in KB

class Wlist:
    def __init__(self,instancename):
        self.wcp = []
        self.wname = instancename
        
    def add_word(self,new_word):                        # add new word to the word list WL
        self.wcp.append(Word(new_word))                 # add the object
        self.wci = len(self.wcp)-1                      # current index in WL
        KB.add_concept(1,1,[self.wci])                  # create the concept for the word meaning. Parent is this word.
        self.wcp[self.wci].wchild.append(KB.ci)         # add the meaning concept as child in the word object.
        log.add_log((self.wname," add_word ",self.wcp[self.wci].word," wordindex=",self.wci," KB index=",KB.ci))

#*** continue file natlan2.py *****

args=Arguments()                #initialize
log=Logging()                   #open log file
KB.add_concept(3,3,[9,5])
WL.add_word("pista")
WM.add_concept(4,2,[17])
WM.add_concept(3,1,[19])
WL.add_word("joska")
log.logf.close()
print (KB.cp[0].parent,"word with index 1=",WL.wcp[1].word,"  Now test the word with index 1:",WL.wcp[KB.cp[WL.wcp[1].wchild[0]].parent[0]].word)
		
