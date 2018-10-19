import gl, conc, branch

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
        self.next_question = [] # store mentalese of question in the row before the question
        self.systemanswer = []  # output of the system
        self.evaluation = []    # evaluation of system output includinmg mentalese translation
        self.comment = []       # comment
        self.debug = []         # show that this row needs debugging
        try:
            self.testf = open(testfilename, "r")
            pos=testfilename.find(".")
            self.resultf = open(testfilename[:pos]+"_result"+testfilename[pos:],"w")    #output file
        except:
            gl.log.add_log(("ERROR: Testinput: input or output file could not be opened:", self.name))
        try:
            basefname = testfilename[:pos]+"_base"+testfilename[pos:]               # base file to compare result with
            self.basef = open(basefname, "r")
            print ("MESSAGE: Base file found: ",basefname)
        except: a=0

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
            self.next_question.append("")
            self.systemanswer.append([]);
            self.evaluation.append("")
            self.comment.append("")
            self.debug.append(0)
            rowi = len(self.eng) - 1  # index of the new item
            while i < len(line):
                if "e/" in line[i:i + 2]: epos = i  # order of e/ m/ a/ // is fixed but all are optioonal
                if "m/" in line[i:i + 2]:
                    mpos = i
                    if epos > -1: self.eng[rowi] = line[epos + 2:mpos]
                    if "*" in line[i-1:i]:         # * means debug this row
                        self.debug[rowi]=1
                if "a/" in line[i:i + 2]:
                    apos = i
                    if mpos > -1: self.question[rowi] = 1
                    if mpos > -1: self.mentalese[rowi] = line[mpos + 2:apos]
                    if mpos == -1 and epos > -1: self.eng[rowi] = line[epos + 2:apos]
                    prerow = rowi-1
                    while prerow>0 and self.mentalese[prerow]=="": prerow-=1    # find previous nonempty row
                    if prerow >=0: self.next_question [prerow] = self.mentalese[rowi][:]    # store question mentalese
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
                gl.WM.read_concept(tfment,0)              # store good answer in WM temporarliy
                counter=counter+1
            endi=gl.WM.ci                               # final index in WM
            finalanswers[:]=self.goodanswer_list(starti,endi)[:]    # get indices of good answers
            sysamatch=[0]*len(self.systemanswer[rowindex])          # all system answer has 1 element, initially 0
            goodamatch=[0]*len(finalanswers)            # all good answers have 1 element, which is initially 0
            goodindex=0
            for gooda in finalanswers:                  # take all good answers
                sysindex=0; goodmatch=0
                for sysalist in self.systemanswer[rowindex]:        # and take all system answers
                    if type(sysalist) is list: sysa=sysalist[1]     #backward compatibility
                    else: sysa=sysalist
                    if (gl.WM.rec_match(gl.WM.cp[gooda],gl.WM.cp[sysa],goodanswer=1)==1): # relation and parents match
                        goodmatch=1
                        if (gl.WM.cp[gooda].p == gl.WM.cp[sysa].p):     # p value is the same
                            sysamatch[sysindex]=1
                            goodamatch[goodindex]=1
                        else:
                            if gl.WM.cp[sysa].p != gl.args.pmax/2:
                                if sysamatch[sysindex]==0:      # p mismatch, no perfect match earlier, may mean BADP
                                    sysamatch[sysindex]=2
                    sysindex=sysindex+1
                if (goodmatch==0): eval="***MISS"           # good answer missing, override p mismatch
                goodindex+=1
            if (eval=="OK     " and (0 in goodamatch)):      # concept match OK but some p values do not match
                eval="***BADP"
            if (eval=="OK     " and (2 in sysamatch)):      # concept match multiple cases, some p mismatching
                eval="***BADP"
            if (eval=="OK     " and (0 in sysamatch)):      # too many system answers
                eval="OK MORE"
            for i in range(endi-starti):                # good answer concepts in WM
                gl.WM.remove_concept()                  # remove them from WM
        return eval

 
    def write_result(self,rowindex):                    # write outpit file
        evals=self.eval_test(rowindex)
        self.resultf.write(evals)                       # write OK, BAD
        if len(self.eng[rowindex])>0:                   
            self.resultf.write(" e/ ")
            self.resultf.write(self.eng[rowindex])
            addspaces(self.eng[rowindex],22)                # fill spaces up to 22 characters
        if len(self.mentalese[rowindex])>0:
            self.resultf.write(" m/ ")
            self.resultf.write(self.mentalese[rowindex])
            addspaces(self.mentalese[rowindex],22)
        if len(self.goodanswer[rowindex])>0:
            self.resultf.write(" a/ ")
            self.resultf.write(self.goodanswer[rowindex])
            self.resultf.write(" s/ ")
        self.resultf.write(self.comment[rowindex][:-1])
        for sysalist in self.systemanswer[rowindex]:
            if type(sysalist) is list: sysa=sysalist[1]
            else: sysa=sysalist
            self.resultf.write(gl.WM.cp[sysa].mentstr + str(gl.WM.cp[sysa].p)+" ")   # write answer string
        if self.systemanswer[rowindex]!=[]: self.resultf.write(str(self.systemanswer[rowindex]))
        self.resultf.write("\n")
        
    def mentalese_fromrow(self,line):           # get mentalese string
        i=0; mentout=""
        epos=-1;mpos=-1;apos=-1;comment=-1
        while i<len(line):
            if "e/" in line[i:i+2]: epos=i      # order of e/ m/ a/ is fixed
            if "m/" in line[i:i+2]: mpos=i   
            if "a/" in line[i:i+2]:
                apos=i
                if mpos>-1: mentout = line[mpos+2 : apos][:].strip()
            if "//" in line[i:i+2]:
                comment=i
                if mpos>-1 and apos==-1: mentout = line[mpos+2 : comment][:].strip()
            i+=1
        if mpos>-1 and apos==-1 and comment==-1:
            mentout = line[mpos+2 : i][:].strip()
        return mentout

    def locate_thisment(self,row,ment,lines):   # locate mentalese from row in lines
        while row<len(lines):
            if ment in lines[row]:              # mentalese located
                try: return lines[row][0:7]
                except: return "notfound"
            row+=1
        return "notfound"

    def check_result(self):                     # compare _base file with _result file
        match=0; diff=0; notf=0; message=""; r_eval=" "
        try:                                    # if the files exist
            self.resultf.close()                # close current result file
            pos=self.name.find(".")
            self.resultf=open(self.name[:pos]+"_result"+self.name[pos:],"r")    # open result file for read
            resultlines=[]
            for rline in self.resultf:
                resultlines.append(rline[:])    # loafd entire result file
            brow=0
            for bline in self.basef:            # rows in base file
                try: bment=self.mentalese_fromrow(bline)   # get the mentalese
                except: print ("ERROR in testing.mentalese_fromrow. row:",brow)
                if len(bment)>0:
                    try: r_eval=self.locate_thisment(brow,bment,resultlines)
                    except: print ("ERROR in testing.locate_thisment. row:",brow)
                if bline[0:7] == r_eval: match+=1   # match
                else:
                    if r_eval == "notfound":
                        notf+=1
                        print ("NOT FOUND in RESULT: row=",brow," mentalese:",bment," base eval:",bline[0:7])
                    elif len(bment)>0:
                        diff +=1
                        print ("DIFF in RESULT: row=",brow," mentalese:",bment," base eval:",bline[0:7]," current eval:",r_eval)
                brow+=1
            self.resultf.close()
            self.basef.close()
        except: message = "ERROR in RESULT CHECK, probably _base file not found"
        if diff==0 and notf==0: alleval=" ALL OK"
        else: alleval=""
        if "ERROR" in message: print (message)
        else: print ("RESULT CHECK.",alleval,"match:",match,"difference:",diff,"not found:",notf, message)
                    
            
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
            


    def test_implication(self):
        c0 = ["IM(AND(C(%1,%2),X(%2,%3)),X(%1,%3))"]

        wrdlink1 = gl.WL.add_word("%1")
        wrdlink2 = gl.WL.add_word("%2")
        wrdlink3 = gl.WL.add_word("%3")
        
        ci1 = gl.WM.add_concept(1,1,[],[wrdlink1])  # %1
        ci2 = gl.WM.add_concept(1,1,[],[wrdlink2])  # %2
        ci3 = gl.WM.add_concept(1,1,[],[wrdlink3])  # %3
        ciC = gl.WM.add_concept(1,4,new_parents=[ci1,ci2])    # C(%1,%2)
        ciX1 = gl.WM.add_concept(1,-1,new_parents=[ci2,ci3])     # X(%2,%3)
        ciX2 = gl.WM.add_concept(1,-1,new_parents=[ci1,ci3])    # X(%1, %3)

        ciA = gl.WM.add_concept(1,16,new_parents=[ciC,ciX1])     # AND

        #the implication itself:
        gl.WM.add_concept(1,13,new_parents=[ciA,ciX2])

    def test_branch_functions(self):                # test for the branches
        for testconc in [(-1,[1]),(0,[2]),(1,[3,4]),(2,[5,6]),(2,[7]),(3,[8]),(3,[9]),(4,[10]),(5,[11,12]),(6,[]),
                        (7,[13,14,15]),(8,[16]),(8,[17]),(10,[]),(10,[]),(10,[]),(11,[]),(12,[])]:
            c = conc.Concept()
            c.previous = testconc[0]
            c.next.extend(testconc[1])
            gl.WM.cp.append(c)
        
        branch.rec_print_tree(0)
        
        for i in range(18):
            print("\n" + "#" * 40)
            print("\nGet leaves on branch starting from " + str(i) + ":")
            print(branch.rec_get_leaves(i))
            
            print("\nGet previous concepts from " + str(i) + ":")
            print(branch.get_previous_concepts(i))
            
            print("\nGet next concepts from " + str(i) + ":")
            print(branch.rec_get_next_concepts(i))
        
        # should not cause error
        for findonbranch in [(16,0),(0,2),(0,13),(6,0),(2,17),(8,3),(4,7),(11,5),(5,5)]:
            assert branch.search_on_branch(findonbranch[0], findonbranch[1])
        for notfindonbranch in [(3,4),(3,14),(4,6),(14,17),(13,14)]:
            assert not branch.search_on_branch(notfindonbranch[0], notfindonbranch[1])
        
        for parentchild in [(0,12),(1,16),(2,6),(7,14),(4,10),(10,14),(2,9),(8,16)]:
            gl.WM.cp[parentchild[0]].child.append(parentchild[1])
            
        # should not cause error
        for qa in [(13,-1),(16,11),(11,5),(12,5),(5,3)]:
            assert branch.get_previous_sentence_on_branch(qa[0]) == qa[1]
        
        print("\n" + "#" * 40 + "\n\nTest of deleting branches:\n\nOriginal tree:")
        branch.rec_print_tree(0, True)
        for delbranch in [12,3,14,7]:
            print("\nDeleting branch starting from " + str(delbranch) + ":")
            branch.remove_branch(delbranch)
            branch.rec_print_tree(0, True)
        

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
