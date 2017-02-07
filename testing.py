import gl, conc

def addspaces(ins,num):
    stt=""
    for i in range(num-len(ins)):
        stt=stt+" "
    return stt

class Testinput:
    def __init__(self, testfilename):
        self.name = testfilename
        self.eng = []           # english text
        self.mentalese = []     # mentalese version of english
        self.goodanswer = []    # expected answer (if english is a question)
        self.question = []      # flag to indicate questions
        self.systemanswer = []  # output of the system
        self.evaluation = []    # evaluation of system output includinmg mentalese translation
        self.comment = []       # comment
        try:
            self.testf = open(testfilename, "r")
            pos=testfilename.find(".")
            self.resultf = open(testfilename[:pos]+"_result"+testfilename[pos:],"w")    #output file
        except:
            gl.log.add_log(("ERROR: Testinput: input or output file could not be opened:", self.name))

    def readtest(self):
        gl.log.add_log(("Test file started:", self.name))
        for line in self.testf:
            i = 0;
            epos = -1;
            mpos = -1;
            apos = -1;
            comment = -1
            self.eng.append("");
            self.mentalese.append("")  # each list must have a new item
            self.goodanswer.append("");
            self.question.append(0)
            self.systemanswer.append([]);
            self.evaluation.append("")
            self.comment.append("")
            rowi = len(self.eng) - 1  # index of the new item
            while i < len(line):
                if "e/" in line[i:i + 2]: epos = i  # order of e/ m/ a/ // is fixed but all are optioonal
                if "m/" in line[i:i + 2]:
                    mpos = i
                    if epos > -1: self.eng[rowi] = line[epos + 2:mpos]
                if "a/" in line[i:i + 2]:
                    apos = i
                    self.question[rowi] = 1
                    if mpos > -1: self.mentalese[rowi] = line[mpos + 2:apos]
                    if mpos == -1 and epos > -1: self.eng[rowi] = line[epos + 2:apos]
                if "//" in line[i:i + 2]:
                    comment = i
                    self.comment[rowi]=line[comment:]
                    if epos > -1 and mpos == -1: self.eng[rowi] = line[epos + 2:comment]
                    if mpos > -1 and apos == -1: self.mentalese[rowi] = line[mpos + 2:comment]
                    if apos > -1: self.goodanswer[rowi] = line[apos + 2:comment]
                i += 1
            if epos > -1 and mpos == -1 and apos == -1 and comment == -1:
                self.eng[rowi] = line[epos + 2:i].strip()
            if mpos > -1 and apos == -1 and comment == -1:
                self.mentalese[rowi] = line[mpos + 2:i].strip()
            if apos > -1 and comment == -1:
                self.question[rowi] = 1
                self.goodanswer[rowi] = line[apos + 2:i].strip()

    def goodanswer_list(self,starti,endi):              # get indices of good answers
        subanswerlist=[]
        finalanswerlist=[]
        for i in range(endi-starti):
            for pari in gl.WM.cp[starti+i+1].parent:
                if (pari>starti and pari<=endi):
                    subanswerlist.append(pari)          # collect non-final answers
        for i in range(endi-starti):
            if starti+i+1 not in subanswerlist:
                finalanswerlist.append(starti+i+1)
        return finalanswerlist

    def eval_test(self,rowindex):                       # evaluation string of a row of the input file
        finalanswers=[]
        eval="       "
        if (self.question[rowindex]==1):                # *** QUESTION ***
            eval="OK     "
            tfment=[]; counter=0                        # good answer mentalese string
            starti=gl.WM.ci
            tfment.append(self.goodanswer[rowindex])
            if "not found" not in tfment[0]: notfound=0
            else: notfound=1
            while (notfound==0 and len(tfment[0])>3 and counter<20):
                gl.WM.read_concept(tfment)              # store good answer in WM temporarliy
                counter=counter+1
            endi=gl.WM.ci                               # final index in WM
            finalanswers[:]=self.goodanswer_list(starti,endi)[:]    # get indices of good answers
            sysamatch=[0]*len(self.systemanswer[rowindex])          # all system answer has 1 element, initially 0
            for gooda in finalanswers:                  # take all good answers
                sysindex=0; goodmatch=0
                for sysa in self.systemanswer[rowindex]:    # and take all system answers
#                    if (conc.match(gl.WM.cp[gooda],gl.WM.cp[sysa])==1): # relation and parents match
                    if (gl.WM.rec_match(gl.WM.cp[gooda],gl.WM.cp[sysa])==1): # relation and parents match
                        goodmatch=1
                        if (gl.WM.cp[gooda].p == gl.WM.cp[sysa].p):     # p value is the same
                            sysamatch[sysindex]=1
                        else: eval="***BADP"                # p value mismatch
                    sysindex=sysindex+1
                if (goodmatch==0): eval="***MISS"           # good answer missing, override p mismatch
            if (eval=="OK     " and (0 in sysamatch)):      # too many system answers
                eval="***MORE"
            for i in range(endi-starti):                # good answer concepts in WM
                gl.WM.remove_concept()                  # remove them from WM
        return eval

 
    def write_result(self,rowindex):                    # write outpit file
        evals=self.eval_test(rowindex)
        self.resultf.write(evals)                       # write OK, BAD
        self.resultf.write(" /e ")
        self.resultf.write(self.eng[rowindex])
        addspaces(self.eng[rowindex],22)                # fill spaces up to 22 characters
        self.resultf.write(" /m ")
        self.resultf.write(self.mentalese[rowindex])
        addspaces(self.mentalese[rowindex],22)
        self.resultf.write(" /a ")
        self.resultf.write(self.goodanswer[rowindex])
        self.resultf.write(" /s ")
        self.resultf.write(str(self.systemanswer[rowindex]))
        if (len(self.eng[rowindex])==0 and len(self.mentalese[rowindex])==0 and len(self.comment[rowindex])>0):
            self.resultf.write("\n")
            self.resultf.write(self.comment[rowindex])
        for sysa in self.systemanswer[rowindex]:
            self.resultf.write(gl.WM.cp[sysa].mentstr + str(gl.WM.cp[sysa].p)+" ")   # write answer string
        self.resultf.write("\n")
        

class Temptest:                                 # unit tests and other temporary data
    def __init__(self):
        self.dog=gl.WL.add_word("dog")

    def utest_read_concept(self):               # unit test for conc: read_concept
        testcase=[]; testretain=[]; counter=0
        k0 = gl.KB.add_concept(1,2,[0])         # a test concept in KB which is not a word
        c0 = ["A(boy,run)p=0.4"]                # mukodik
        c1 = ["A(boy,run)"]                     # mukodik de az inputban zarojel marad
        c2 = ["AND(A(boy,run)p=0.82,S(boy,girl))"]    # mukodik
        c3 = ["AND(A(boy,run),S(boy,girl))"]    # nem mukodik
        c4 = ["S(boy,dog)p=0.2 A(boy,run)p=0"]  # mukodik
        c5 = ["S(boy,dog) A(boy,run)p=0"]       # nem mukodik
        c6 = ["S(boy,dog)p=0.2 A(boy,run)"]     # mukodik de zarojel marad az inputban
        c7 = ["F(A(dog,run),fast)p=0.99"]       # nem mukodik
        if (gl.args.argnum==2):
            x=1
        else:
            testcase[:]=c5[:]
            testretain[:]=testcase[:]
            while (len(testcase[0])>3 and counter<20):
                gl.WM.read_concept(testcase)
                counter=counter+1

        print ("TEST read_concept",testretain,"remained:",testcase,"counter",counter)
        for i in range(len(gl.WL.wcp)):
            print ("W",i,gl.WL.wcp[i].word)
        print ("KB 0 parents",gl.KB.cp[0].parent,"Wlink",gl.KB.cp[0].wordlink,"KBlink",gl.KB.cp[0].kblink,"KB 1 parents",gl.KB.cp[1].parent,"Wlink",gl.KB.cp[1].wordlink,"KBlink",gl.KB.cp[1].kblink)
        for i in range(len(gl.WM.cp)):
            w=""
            if (len(gl.WM.cp[i].wordlink)>0): w="word: "+gl.WL.wcp[gl.WM.cp[i].wordlink[0]].word
            print ("WM",i,"relation",gl.WM.cp[i].relation,"parents",gl.WM.cp[i].parent,"WLink",gl.WM.cp[i].wordlink,"KBlink",gl.WM.cp[i].kblink,"p=",gl.WM.cp[i].p,w)
            

        
        
        

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
