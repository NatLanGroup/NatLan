import gl

class Testinput:
    def __init__(self,testfilename):
        self.name=testfilename
        self.eng = []               #english text
        self.mentalese = []         #mentalese version of english
        self.goodanswer = []        #expected answer (if english is a question)
        self.question = []          #flag to indicate questions
        self.systemanswer = []      #output of the system
        self.evaluation = []        #evaluation of system output includinmg mentalese translation
        try:
            self.testf = open(testfilename,"r")
        except: gl.log.add_log(("ERROR: Testinput: the file could not be opened:",self.name))
    def readtest(self):
        gl.log.add_log(("Test file started:",self.name))
        for line in self.testf:
            i=0;epos=-1;mpos=-1;apos=-1;comment=-1
            self.eng.append(" "); self.mentalese.append(" ")            #each list must have a new item
            self.goodanswer.append(" "); self.question.append(0)
            self.systemanswer.append(" "); self.evaluation.append(" ")
            rowi=len(self.eng)-1                                        #index of the new item
            while i<len(line):
                if "e/" in line[i:i+2]:epos=i                           #order of e/ m/ a/ // is fixed but all are optioonal
                if "m/" in line[i:i+2]:
                    mpos=i
                    if (epos>-1): self.eng[rowi]=line[epos+2:mpos]
                if "a/" in line[i:i+2]:
                    apos=i
                    self.question[rowi]=1
                    if (mpos>-1): self.mentalese[rowi]=line[mpos+2:apos]
                    if (mpos==-1 and epos>-1): self.eng[rowi]=line[epos+2:apos]
                if "//" in line[i:i+2]:
                    comment=i
                    if (epos>-1 and mpos==-1): self.eng[rowi]=line[epos+2:comment]
                    if (mpos>-1 and apos==-1): self.mentalese[rowi]=line[mpos+2:comment]
                    if (apos>-1): self.goodanswer[rowi]=line[apos+2:comment]
                i=i+1
            if (epos>-1 and mpos==-1 and apos==-1 and comment==-1):
                self.eng[rowi]=line[epos+2:i].strip()
            if (mpos>-1 and apos==-1 and comment==-1):
                self.mentalese[rowi]=line[mpos+2:i].strip()
            if (apos>-1 and comment==-1):
                self.question[rowi]=1
                self.goodanswer[rowi]=line[apos+2:i].strip()

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
