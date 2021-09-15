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
        self.good_values = []   # for each good answer, acceptable values of p, r, etc
        self.question = []      # flag to indicate questions
        self.next_question = [] # store mentalese of question in the row before the question
        self.systemanswer = []  # output of the system
        self.evaluation = []    # evaluation of system output includinmg mentalese translation
        self.comment = []       # comment
        self.debug = []         # show that this row needs debugging
        self.logrow = []        # list to hold logfile rows
        self.baselogrow = []    # list to hold the previous logfile rows
        self.lognewkb = []      # HOLDS the evaluation of KB based on log file
        self.logoldkb = []      # HOLDS the evaluation of KB base version based on log file    
        self.logcomp = []       # holds teh comparison of new and old KB
        self.tracking = []      # holds tracking info output
        self.track_con = []     # which concepts to track
        try:
            self.testf = open(testfilename, "r")
            pos=testfilename.find(".")
            self.resultf = open(testfilename[:pos]+"_result"+testfilename[pos:],"w")    #output file
            self.log_result = open("log_result.txt","w")                                # logfile evaluation file
        except:
            gl.log.add_log(("ERROR: Testinput: input or output file could not be opened:", self.name))
        try:
            self.trackf = open("track.txt","r")                   # tracking file as input
            trackflag=1
        except:
            trackflag=0
            gl.log.add_log(("WARNING: Testinput: track.txt file could not be opened for read."))        
        try:
            basefname = testfilename[:pos]+"_base"+testfilename[pos:]               # base file to compare result with
            self.basef = open(basefname, "r")
            print ("MESSAGE: Base file found: ",basefname)
        except: a=0
        if trackflag==1:                                        # there is track.txt to read
            self.read_Track()                                   # read which concepts to track                         
            self.trackf.close()
        try:
            self.trackf = open("track.txt","w")                 # tracking file as output  
        except:
            gl.log.add_log(("ERROR: Testinput: track.txt file could not be opened for write."))        

    def read_Track(self):
        lnum=0; trackpresent=0
        for line in self.trackf:
            if lnum==0:                                                     # first row of track file
                if "/TRACK" in line[0:6]: trackpresent=1                    # concepts follow to be tracked
            if lnum>0 and trackpresent==1 and "/END" not in line[0:6]:      # concepts given to track   
                self.track_con.append(line[:-1])
            if "/END" in line[0:6]: trackpresent=0                          # concepts ended to be tracked
            lnum+=1
        return

    def get_Value(self,gstring,pos):                            # parse the .p=4 value postions
        pos=pos+1                       # on pos we have a . character. gstring is the portion of the row of teh test file with the good answer mentalese.
        stop=0
        namevals=[]
        while pos<len(gstring) and stop==0:
            name=""; number=0; numberst=""
            while pos<len(gstring) and gstring[pos] != "=":
                name=name+gstring[pos]                      # collect the name .p=4 : p
                pos+=1
            if gstring[pos] == "=":                         # after = we have the value
                pos+=1
                while pos<len(gstring) and gstring[pos].isnumeric() and gstring[pos]!=".":
                    numberst=numberst+gstring[pos]
                    pos+=1
                if len(numberst) > 0:
                    number = int(numberst)
            if pos >= len(gstring) or gstring[pos]!=".": 
                stop=1                                      # only continue if we have one more .
            else:                                           # continue
                pos+=1
            namevals.append([name,number])
        return namevals

    def goodanswer_Populate(self,gooda,goodval,gstring):        # fill the goodanswer and good_values list
        item=""; openc=0; closec=0; pos=0
        wait=0; valu=[]                                         # wait for .p=4 etc to finish
        for ch in gstring:
            if ch == "(": openc+=1
            if ch == ")": closec+=1
            if ch != ".":                                       # detect X(a,b).p=4 syntax
                if ch != " ":          
                    if wait == 0: item = item + ch              # if not waiting, add to goodanswer item
                else:                                      
                    if openc==closec:                           # a space means end of concept, if () are all closed
                        gooda.append(item)
                        if wait==0: goodval.append([])
                        item=""; openc=0; closec=0; wait=0
            else:
                if openc==closec and wait==0:
                    valu = self.get_Value(gstring,pos)          # get the .p= values
                    goodval.append(valu)                     # start collecting these values
                    if gl.d==3: print ("POPUL 1 point at end item=",item,"valu",valu,"goodval",goodval)
                    wait=1 ; valu=[]                                     # after a . char, wait with adding to goodanswer until next mentalese starts
            pos+=1    
        if len(item)>0:
            gooda.append(item)                                  # add this answer item to the goodanswer list
            if len(goodval)<len(gooda): goodval.append([])
        if gl.d==3: print ("POPUL 2 gooda",gooda,"goodval",goodval)

    def readtest(self):
        gl.log.add_log(("Test file started:", self.name))
    #    try:
        if 1==1:
            for line in self.testf:
                i = 0;
                epos = -1;
                mpos = -1;
                apos = -1;
                comment = -1
                self.eng.append("");
                self.mentalese.append("")  # each list must have a new item
                self.goodanswer.append([])
                self.good_values.append([])
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
                        if apos > -1: self.goodanswer_Populate(self.goodanswer[rowi],self.good_values[rowi],line[apos + 2:comment])   # fill the goodanswer list
                    i += 1
                if epos > -1 and mpos == -1 and apos == -1 and comment == -1:
                    self.eng[rowi] = line[epos + 2:i].strip()
                if mpos > -1 and apos == -1 and comment == -1:
                    self.mentalese[rowi] = line[mpos + 2:i].strip()
                if apos > -1 and comment == -1:
                    self.question[rowi] = 1
                    self.goodanswer_Populate(self.goodanswer[rowi],self.good_values[rowi],line[apos + 2:i].strip())
    #    except: print("INPUT FILE ERROR. Input file may have wrong format. Or file name parameter missing, or could not be opened. ")

    def goodanswer_list(self,db,starti,endi):              # get indices of good answers
        subanswerlist=[]
        finalanswerlist=[]
        for i in range(endi-starti):
            for pari in db.cp[starti+i+1].parent:
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
            finalanswers[:]=self.goodanswer_list(gl.WM,starti,endi)[:]  # get indices of good answers
            sysamatch=[0]*len(self.systemanswer[rowindex])              # all system answer has 1 element, initially 0
            goodamatch=[0]*len(finalanswers)            # all good answers have 1 element, which is initially 0
            goodindex=0
            for gooda in finalanswers:                  # take all good answers
                sysindex=0; goodmatch=0
                for sysalist in self.systemanswer[rowindex]:        # and take all system answers
                    if type(sysalist) is list: sysa=sysalist[1]     #backward compatibility
                    else: sysa=sysalist
                    if sysalist[0]==-1:  db=gl.KB                    # -1 means KB. process answers from KB too.
                    else: db=gl.WM
                    if db.name=="KB":  castKB=1                      # rec_match called for compare with KB
                    else: castKB=0
                    if (gl.WM.rec_match(gl.WM.cp[gooda],db.cp[sysa],castSecondKbase=castKB,goodanswer=1)==1): # relation and parents match
                        goodmatch=1
                        if (gl.WM.cp[gooda].p == db.cp[sysa].p):     # p value is the same
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

    def vs_eval_test(self,rowindex):                       # evaluation string of a row of the input file
        finalanswers=[]
        eval="       "
        if (self.question[rowindex]==1):                # *** QUESTION ***
            eval="OK     "
            sysamatch=[0]*len(self.systemanswer[rowindex])              # all system answer has 1 element, initially 0
            goodamatch=[0]*len(self.goodanswer[rowindex])               # all good answers have 1 element, which is initially 0
            goodindex=0
            for gooda in self.goodanswer[rowindex]:                  # take all good answers
                sysindex=0; goodmatch=0
                goodamatch[goodindex]=-1                            # FIX4 -1 instead of 1
                for sysalist in self.systemanswer[rowindex]:        # and take all system answers
                    if sysalist[0]==-1:  db=gl.KB                   # -1 means KB. process answers from KB too.
                    else: db=gl.VS.wmlist[sysalist[0]]              # this is the WM we are in
                    sysa = sysalist[1]
                    if db.name=="KB":  castKB=1                     # rec_match called for compare with KB
                    else: castKB=0
                    goodment = gooda                                # TO DO GET P VALUE OFF mentalese of good answer
                    if db.cp[sysalist[1]].mentstr == goodment:      # mentalese format match
                        goodmatch=1
                        sysamatch[sysindex]=1                       # let us suppose matching p
                        goodvals=self.good_values[rowindex][goodindex][:]
                        if goodvals==[]: goodvals.append(["p",gl.args.pmax])   # at least p value must be checked
                        for goodval_item in goodvals:               # cycle through p=, g=, r= etc
                #            if gl.d==4: print ("TESTING 1 gooda",gooda,"goodamatch",goodamatch,"sysamatch",sysamatch,"goodindex",goodindex)
                            if (goodval_item[1] != db.map_Attrib(sysa,goodval_item[0])):   # p etc value is not the same
                                if goodamatch[goodindex] in [1,3]:        # earlier we had a match
                                    goodamatch[goodindex]=3         # some p matching, some not
                                    sysamatch[sysindex]=3
                                else: 
                                    goodamatch[goodindex]=0         # p mismatch
                                    sysamatch[sysindex]=2
                            if (goodval_item[1] == db.map_Attrib(sysa,goodval_item[0])):   # p etc value are  the same
                                if goodamatch[goodindex] in [0]:        # earlier we had a mismatch
                                    goodamatch[goodindex]=3         # some p m,atching, some not
                                    sysamatch[sysindex]=2
                                if goodamatch[goodindex] in [1,-1]:        # no earlier result or earlier matching
                                    goodamatch[goodindex]=1         # match
                                    sysamatch[sysindex]=1
                #            if gl.d==4: print ("TESTING 3 gooda",gooda,"goodamatch",goodamatch,"sysamatch",sysamatch)
                    sysindex=sysindex+1
                if (goodmatch==0): eval="***MISS"                   # good answer missing, override p mismatch
                goodindex+=1
            if (eval=="OK     " and (0 in goodamatch)):             # concept match OK but some p values do not match
                eval="***BADP"
 #           if (eval=="OK     " and (2 in sysamatch)):              # FIX4 remove concept match multiple cases, some p mismatching
  #              eval="***BADP"
            if (eval=="OK     " and (0 in sysamatch)):              # too many system answers
                eval="OK MORE"
        return eval

 
    def write_result(self,rowindex):                    # write output file
        evals = self.vs_eval_test(rowindex)
        self.resultf.write(evals)                       # write OK, BAD
        if len(self.eng[rowindex])>0:                   
            self.resultf.write(" e/ ")
            self.resultf.write(self.eng[rowindex])
            self.resultf.write(addspaces(self.eng[rowindex],35))  # fill spaces up to 22 characters
        if len(self.mentalese[rowindex])>0:
            self.resultf.write(" m/ ")
            self.resultf.write(self.mentalese[rowindex])
            self.resultf.write(addspaces(self.mentalese[rowindex],35))
        if len(self.goodanswer[rowindex])>0:
            self.resultf.write(" a/ ")
            ai=0
            for answ in self.goodanswer[rowindex]:
                self.resultf.write(answ)
                if self.good_values[rowindex][ai]!=[]:      # .p=4 values are stored here and now written in the output
                    for gooditem in self.good_values[rowindex][ai]:    # several good answers possible
                        if gooditem!=[]:
                            self.resultf.write(".")
                            self.resultf.write(gooditem[0])
                            self.resultf.write("=")
                            self.resultf.write(str(gooditem[1]))
                self.resultf.write(" ")
                ai+=1
            self.resultf.write(" s/ ")
        self.resultf.write(" ")
        self.resultf.write(self.comment[rowindex][:-1])
        for sysalist in self.systemanswer[rowindex]:
            if type(sysalist) is list: sysa=sysalist[1]
            else: sysa=sysalist
            if sysalist[0]==-1:  db=gl.KB                    # handle answer in KB
            else: db=gl.VS.wmlist[sysalist[0]]               # sysalist[0]ha sthe index of the WM version
            self.resultf.write(db.cp[sysa].mentstr + str(db.cp[sysa].p)+" ")   # write answer string
        if self.systemanswer[rowindex]!=[]:
            self.resultf.write(str(self.systemanswer[rowindex]))
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

    def locate_thisment(self,row,ment,lines,skip):   # locate mentalese from row in lines
        start=row; skip[1]=0
        while row<len(lines):
            if ment in lines[row]:              # mentalese located
                pos = lines[row].find(ment)-1   # mentalese in row
                while lines[row][pos]==" ": pos-=1  # back until not a space before mentalese
                if pos>0 and lines[row][pos]=="/" and lines[row][pos-1]=="m":     # /m means this mentalese is not commented out
                    try:
                        skip[1]=(row-start)-skip[0]   # count new rows that were now skipped in addition
                        return lines[row][0:7]
                    except: return "notfound"
                if pos>0 and lines[row][pos]=="/" and lines[row][pos-1]=="/":  # a mentalese that is commented out by //
                    return "notfound"
            row+=1
        return "notfound"

    def check_result(self):                     # compare _base file with _result file
        match=0; diff=0; notf=0; message=""; r_eval=" "
        skip=[0,0]                              # how many new rows were skipped
        try:                                    # if the files exist
            self.resultf.close()                # close current result file
            pos=self.name.find(".")
            self.resultf=open(self.name[:pos]+"_result"+self.name[pos:],"r")    # open result file for read
            resultlines=[]
            for rline in self.resultf:
                resultlines.append(rline[:])        # loafd entire result file
            brow=0
            for bline in self.basef:                # rows in base file
                try: bment=self.mentalese_fromrow(bline)   # get the mentalese
                except: print ("ERROR in testing.mentalese_fromrow. row:",brow)
                if len(bment)>0:
                    try: r_eval=self.locate_thisment(brow,bment,resultlines,skip)
                    except: print ("ERROR in testing.locate_thisment. row:",brow)
                    if skip[1]>0:
                        skip[0]=skip[0]+skip[1]     # increase skip counter with new skippings
                        print ("SKIPPED new rows in _result from row:",brow," number of skipped rows:",skip[1])
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
        else: print ("RESULT CHECK.",alleval,"match:",match,"difference:",diff,"not found:",notf, "new rows skipped:",skip[0],message)

    def  read_logfile(self,filename,loglist):
        ok=1
        try:
            logdone = open(filename, "r")
        except: 
            ok=0                            # no such file
        if ok==1:                           # file could be opened
            i=0
            for line in logdone:
                loglist.append(line)        # the lofgile is stored in the loglist row by row
                i+=1
        return ok

    def get_Section(self,row,ident,back,flag,thislog):   # search ident in thislog and if found return values after back
        ind=len(thislog)-1
        result=[]
        while ind>0:
            this = thislog[ind]         # current row
            found=ind; resi=""
            for identify in ident:
                if not(identify in this):
                    found=-1
            if found > -1 and not("known=0" in this):                  # thsi is a matching row
                resi=flag+" "
                for baci in back:           # values to be searched for
                    if baci in this: 
                        pos=this.find(baci)
                        end=this.find(" ",pos+1)
                        resi=resi+" "+this[pos:end]
                result.append(resi)
            ind = ind-1                     # search backward
        return result
    
    def get_Used(self,row,kbi,logfkb):                 # from row, get the used_ever field: which concepts were used to reason this.
        trig="frozenset({"
        useds=""
        logfkb[kbi]["used"]=[]                          # initialize the used list of lists in self.lognewkb or self.logoldkb
    #    for usecase in gl.KB.cp[kbi].use_ever:
     #       if list(usecase)!=[-1]:
      #          useds+=str(list(usecase))
       #         logfkb[kbi]["used"].append(list(usecase))
        for rowi in range(0,len(row)-len(trig)):            # collect the used_ever concepts
            if row[rowi:rowi+len(trig)] == trig:            # trig introduces used_ever items in the log file
                sta=rowi+len(trig)                          # current position
                num=row[sta:sta+1]; sta+=1; useds="["       # num will hold the number
                thiscase=[]                                 # a single list of used concepts
                while row[sta:sta+1] not in ["}"]:          # while not end of frozenset
                    while row[sta:sta+1] not in ["}",","]:
                        num+=row[sta:sta+1];sta+=1
                    if row[sta:sta+1] not in ["}"]: sta+=1
                    if num!="-1": 
                        useds+=num
                        thiscase.append(int(num))           # convert to number
                        #print ("GETUSED", kbi,thiscase)
                    num=""
                if thiscase!=[]: logfkb[kbi]["used"].append(thiscase)   # "used" holds the lists of used concepts
        useds+="]"
        if useds=="[]" or useds=="]": useds=""
        return useds

    def add_detail(self,logfkb,rowi,found,ment):     # rows showing INPUT and REASON origin of concepts
        if "(" in ment:                         # only compound concepts
            logfkb[rowi]["detail"]=[]           # rows showing INPUT and REASON origin of concepts
            for fitem in found: 
                if fitem!=[]:
                    logfkb[rowi]["detail"].append("   "+str(fitem))
        else:                                   # for words
            logfkb[rowi]["detail"]=[]
     
    def log_KB(self,logfkb,thislog):             # process the KB content of the log file. logfkb is either self.lognewkb or self.logoldkb.
        ind=len(thislog)-1                              # last index
        row=thislog[ind][:]
        while ind>0 and not "KB"==row[0:2]:             # get the first row of KB list at the end of the log file
            ind=ind-1
            row=thislog[ind][:] 
        logkb=[]
        while ind<len(thislog)-1:                       # all rows starting from the KB list first row
            ind+=1
            row=thislog[ind][:]
            spac=row.find(" ")                          # the space after the row number
            numb= row[0:spac]                           # row number
            ment= row[spac+1:row.find(" ",spac+1)]      # mentalese
            pval = row[row.find("p=")+2:row.find(" ",row.find("p=")+1)]   # p= value
        #    print ("LOGKB row",row,"pval",pval)
            know = row[row.find("known=")+6:row.find(" ",row.find("known=")+1)]   # known= value
            logfkb.append([]); rowi=len(logfkb)-1       # logfkb has items corresponding to the current KB
            logfkb[rowi]={"prval":(str(rowi)+" p="+pval+" k="+know+" "+ment)}  # logfkb items are lists of dicts. prval is the printable value for the KB row.
            logfkb[rowi]["ment"]=ment                   # mentalese
            logfkb[rowi]["pval"]=int(pval)              # store the p value in the data structure
            logfkb[rowi]["know"]=int(know)              # store the known value in the data structure
            found=[]
            if "wmuse=[-1]" in row or "frozenset({-1})" in row:   # FIXXXXX
                found=self.get_Section(row,["INPUT","ment= "+ment],["p=","known="],"INPUT ",thislog)    # search for rows with "INPUT"
            found2=self.get_Section(row,["reasoned concept:"+ment],["p="],"REASON",thislog)             # search for rows with "reasoned concept:"
            for ite in found2: found.append(ite)
            found3 = self.get_Used(row,rowi,logfkb)     # returns the string and also populates logfkb with the used concept indices
            logfkb[rowi]["prval"]+=" "+found3
            #print ("LOGKB rowi",rowi,"ment",ment,"found3",found3,"found",found,"***tghislog",thislog)
            self.add_detail(logfkb,rowi,found,ment)     # add rows showing INPUT and REASON origin of concepts

    def manage_Diff(self,oldi,found):                   # investigae differences between old and new KB content for a single concept
        old_detail=""
        for det in self.logoldkb[oldi]["detail"]:
            old_detail+=det                             # details into single string
        fnd_detail=""
        for det in self.lognewkb[found]["detail"]:
            fnd_detail+=det
        old_in=0; old_r=0; fnd_in=0; fnd_r=0
        if "INPUT" in old_detail: old_in=1              # oldi was (also) an input
        if "INPUT" in fnd_detail: fnd_in=1              #  was (also) an input
        if "REASON" in old_detail: old_r=1              #  was (also) a reasoned
        if "REASON" in fnd_detail: fnd_r=1              #  was (also) a reasoned
        if found not in self.logcomp["diff"] and (old_in!=fnd_in or old_r!=fnd_r):   # there will be difference
            self.logcomp["diff"][found]={"prval":str(found)+" DIFF old_id:"+str(oldi)+" "+self.lognewkb[found]["ment"]+" "}
            self.logcomp["diff"][found]["oldindex"]=oldi            
        if old_in==1 and fnd_in==0: self.logcomp["diff"][found]["prval"] += "MISSING input. "
        if old_in==0 and fnd_in==1: self.logcomp["diff"][found]["prval"] += "MORE input. "
        if old_r==1 and fnd_r==0: self.logcomp["diff"][found]["prval"] += "MISSING reason. "
        if old_r==0 and fnd_r==1: self.logcomp["diff"][found]["prval"] += "MORE reason. "
        pold = self.logoldkb[oldi]["pval"]
        pnew = self.lognewkb[found]["pval"]
        kold = self.logoldkb[oldi]["know"]
        knew = self.lognewkb[found]["know"]
        if pold!=pnew or kold!=knew:                    # any difference
            if found not in self.logcomp["diff"]: 
                self.logcomp["diff"][found]={"prval":str(found)+" DIFF old_id:"+str(oldi)+" "+self.lognewkb[found]["ment"]+" "}
                self.logcomp["diff"][found]["oldindex"]=oldi
            if pold != pnew: self.logcomp["diff"][found]["prval"] += " DIFF_P old p="+str(self.logoldkb[oldi]["pval"])
            if kold != knew: self.logcomp["diff"][found]["prval"] += " DIFF_K old k="+str(self.logoldkb[oldi]["know"])

    def comp_Missmore(self,logdb,index,pval,ment,strlow,strcap):         # create comparison messages
        msg=strcap+" as parent: "+ment
        for det in logdb[index]["detail"]:
            if "INPUT" in det:
                msg=strcap+" input: p="+str(pval)+" "+ment                          # record missing input
            if "REASON" in det:
                msg=strcap+" reason: p="+str(pval)+" "+ment                         # record missing reasoned concept
                if "INPUT" in det:
                    msg=strcap+" input and "+strcap+" reason: p="+str(pval)+" "+ment         # record missing reasoned concept
        self.logcomp[strlow][index]={"prval":msg}
        return msg

    def diff_Reason(self):                                  # find out the underlying reasons for different reasoning    
        for row in self.logcomp["missing"]:                                         # items found to be missing from new KB
            self.logcomp["missing"][row]["detail"]=[]
            if "used" in self.logoldkb[row] and self.logoldkb[row]["used"]!=[]:     # we have the used concepts
                self.logcomp["missing"][row]["prval"] += " old used: "+str(self.logoldkb[row]["used"])   # extend the logged row of the missing concept
                for uselist in self.logoldkb[row]["used"]:                          # used concepts for each separate reasoning case
                    for used in uselist:
                        usement=self.logoldkb[used]["ment"]
                        for row2 in self.logcomp["missing"]:
                            if used==row2 and usement in self.logcomp["missing"][row2]["prval"]:      # used mentalese is missing
                                self.logcomp["missing"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["missing"][row2]["prval"])
                        for row2 in self.logcomp["diff"]:
                            #print ("logcomp diff row2=",row2,"element=",self.logcomp["diff"][row2])
                            if used==self.logcomp["diff"][row2]["oldindex"]:        # used mentalese is different
                                self.logcomp["missing"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["diff"][row2]["prval"])
        for row in self.logcomp["diff"]:                                            # items found to be different from new KB
            #if gl.d==4: print ("DIFFR 2 row",row)
            oldrow=self.logcomp["diff"][row]["oldindex"]
            self.logcomp["diff"][row]["detail"]=[]
            if "used" in self.logoldkb[oldrow] and self.logoldkb[oldrow]["used"]!=[]:  # we have the used concepts
                self.logcomp["diff"][row]["prval"] += " old used: "+str(self.logoldkb[oldrow]["used"])   # extend the logged row of the missing concept
                for uselist in self.logoldkb[oldrow]["used"]:                          # used concepts for each separate reasoning case
                    for used in uselist:
                        usement=self.logoldkb[used]["ment"]
                        for row2 in self.logcomp["missing"]:
                            if used==row2 and usement in self.logcomp["missing"][row2]["prval"]:      # used mentalese is missing
                                self.logcomp["diff"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["missing"][row2]["prval"])
                        for row2 in self.logcomp["diff"]:
                            if used==self.logcomp["diff"][row2]["oldindex"]:        # used mentalese is different
                                self.logcomp["diff"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["diff"][row2]["prval"])
            if "used" in self.lognewkb[row] and self.lognewkb[row]["used"]!=[]:     # we have the new used concepts
                self.logcomp["diff"][row]["prval"] += " new used: "+str(self.lognewkb[row]["used"])   # extend the logged row of the missing concept
                for uselist in self.lognewkb[row]["used"]:                          # used concepts for each separate reasoning case
                    for used in uselist:
                        if row in self.logcomp["more"]: 
                            for row2 in self.logcomp["more"]:
                                if used==row2:                                          # used  is more
                                    self.logcomp["more"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["more"][row2]["prval"])
        for row in self.logcomp["more"]:                                            # items found to be more in new KB
            self.logcomp["more"][row]["detail"]=[]
            if "used" in self.lognewkb[row] and self.lognewkb[row]["used"]!=[]:     # we have the used concepts
                self.logcomp["more"][row]["prval"] += " used: "+str(self.lognewkb[row]["used"])   # extend the logged row of the missing concept
                for uselist in self.lognewkb[row]["used"]:                          # used concepts for each separate reasoning case
                    for used in uselist:
                        for row2 in self.logcomp["diff"]:
                    #        print ("more processing. used:",used,"row2:",row2,"row2 element:",self.logcomp["diff"][row2])
                            if used==row2:                                          # used  is different
                                self.logcomp["more"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["diff"][row2]["prval"])
                        for row2 in self.logcomp["more"]:
                            if used==row2:                                          # used  is more
                                self.logcomp["more"][row]["detail"].append("    "+str(used)+" USED "+self.logcomp["more"][row2]["prval"])


    def log_Compare(self):                      # compare new KB and old KB based on logfile reports, evaluate differences.    
        self.logcomp = {"missing":dict()}
        self.logcomp["more"] = dict()
        self.logcomp["diff"] = dict()
        for oldi in range(0,len(self.logoldkb)):            # old KB rows
            found=-1
            oment=self.logoldkb[oldi]["ment"]               # old mentalese
            opval=self.logoldkb[oldi]["pval"]               # old pval
            for newi in range(0,len(self.lognewkb)):        # new KB rows
                nment=self.lognewkb[newi]["ment"]           # new mentalese
                if oment==nment: found=newi                 # remember where this was found in new KB
            if found==-1:                                   # an old KB mentalese is missing from new KB
                msg=self.comp_Missmore(self.logoldkb,oldi,opval,oment,"missing","MISSING")      # create comparison messages
                #if "reason:" in msg: self.diff_Reason(oldi,oment) 
            if found>-1:
                self.manage_Diff(oldi,found)                # record differences between oldi and its pair found
        for newi in range(0,len(self.lognewkb)):            # new KB rows. Are any new concepts missing in OLD KB?
            found=-1
            nment=self.lognewkb[newi]["ment"]               # new mentalese
            npval=self.lognewkb[newi]["pval"]               # new pval
            for oldi in range(0,len(self.logoldkb)):        # old KB rows
                oment=self.logoldkb[oldi]["ment"]           # old mentalese
                if oment==nment: found=oldi                 # remember where this was found in old KB
            if found==-1:                                   # a new KB mentalese is missing from old KB
                self.comp_Missmore(self.lognewkb,newi,npval,nment,"more","MORE")      # create comparison messages
           
    def process_logfile(self):                                  # read logfile.txt and logfile_base.txt and evaluate them
        success=self.read_logfile("logfile.txt",self.logrow)                # read logfile into self.logrow
        if success==1:
            self.log_KB(self.lognewkb,self.logrow)                          # process the KB content of the current log file, "lognew"
        success=self.read_logfile("logfile_base.txt",self.baselogrow)       # read earlier logfile into self.baselogrow
        if success==1:                                                      # if we have an earlier log file
            self.log_KB(self.logoldkb,self.baselogrow)                      # process the KB content of the old log file, "logold", name: logfile_base.txt
            self.log_Compare()                                              # compare new KB and old KB, evaluate differences.
            self.diff_Reason()                                              # evaulate the reasons for some of the differences
        #self.print_Logeval()                                                # print the self.lognewkb and self.logoldkb evaluations on screen
        self.write_Logeval()                                                # write the log file evaluations into log_result.txt
        self.write_Tracking()                                               # write the tracking file track.txt
                
    def print_Logeval(self):                    # print the self.lognewkb and self.logoldkb evaluations on screen
    #    for row in self.logoldkb:               # old _base log file
     #       print (row["prval"])                # the printable evaluation row
      #      if "detail" in row:                 # INPUT and REASON details
       #         for ditem in row["detail"]:
        #            print (ditem)
        for row in self.lognewkb:               # current log file
            print (row["prval"])                 # the printable evaluation row
            #if row["used"]!=[]: print ("USED: ",row["used"][0])
            if "detail" in row:                 # INPUT and REASON details
                for ditem in row["detail"]:
                    print (ditem)
        print ("LOGCOMP:")
        for item in self.logcomp["more"]:
            print (self.logcomp["more"][item]["prval"])
            if "detail" in self.logcomp["more"][item]:
                for ditem in self.logcomp["more"][item]["detail"]:
                    print (ditem)
        for item in self.logcomp["missing"]:
            print (str(item)+" "+self.logcomp["missing"][item]["prval"])
            if "detail" in self.logcomp["missing"][item]:
                for ditem in self.logcomp["missing"][item]["detail"]:
                    print (ditem)
        for item in self.logcomp["diff"]:
            print (self.logcomp["diff"][item]["prval"])
            if "detail" in self.logcomp["diff"][item]:
                for ditem in self.logcomp["diff"][item]["detail"]:
                    print (ditem)
    
    def write_Logeval(self):                    # write the log file evaluations into log_result.txt
        self.log_result.write("\n"+"COMPARE with logfile_base.txt:"+"\n")
        for item in self.logcomp["more"]:
            self.log_result.write(str(item)+" "+self.logcomp["more"][item]["prval"]+"\n")
            if "detail" in self.logcomp["more"][item]:
                for ditem in self.logcomp["more"][item]["detail"]:
                    self.log_result.write(ditem+"\n")
        for item in self.logcomp["missing"]:
            self.log_result.write(str(item)+" "+self.logcomp["missing"][item]["prval"]+"\n")
            if "detail" in self.logcomp["missing"][item]:
                for ditem in self.logcomp["missing"][item]["detail"]:
                    self.log_result.write(ditem+"\n")
        for item in self.logcomp["diff"]:
            self.log_result.write(self.logcomp["diff"][item]["prval"] +" new: p="+str(self.lognewkb[item]["pval"])+" k="+str(self.lognewkb[item]["know"]) +"\n")
            if "detail" in self.logcomp["diff"][item]:
                for ditem in self.logcomp["diff"][item]["detail"]:
                    self.log_result.write(ditem+"\n")

        self.log_result.write("\n"+"NEW logfile : KB content"+"\n")
        for row in self.lognewkb:               # current log file
            self.log_result.write(row["prval"]+"\n") # the printable evaluation row
            if "detail" in row:                 # INPUT and REASON details
                for ditem in row["detail"]:
                    self.log_result.write(ditem+"\n")
        self.log_result.write("\n"+"OLD logfile : KB content"+"\n")
        for row in self.logoldkb:               # current log file
            self.log_result.write(row["prval"]+"\n") # the printable evaluation row
            if "detail" in row:                 # INPUT and REASON details
                for ditem in row["detail"]:
                    self.log_result.write(ditem+"\n")
    
    def write_Tracking(self):                   # write the tracking file
        if len(self.track_con)>0:               # any concepts to track
            self.trackf.write("/TRACK"+"\n")
            for ment in self.track_con:         # write back the concepts to track into track.txt, just as the input was
                self.trackf.write(ment+"\n")
            self.trackf.write("/END"+"\n")        
        self.trackf.write("Tracking output:"+"\n")
        for item in self.tracking:              # write the tracked items collected in self.tracking
            self.trackf.write(str(item)+"\n")

    def is_tracked(self,msg,tr,what):               # see if "what" is tracked
        for tritem in gl.test.track_con:            # items tracked
            if tritem == what:                      # rule has a tracked item
                tr=tr+msg; break
            if tritem[0]=="*" and tritem[1:] in what:
                tr=tr+msg; break
        return tr                

    def track(self,db,coni,msg,level,rule=""):              # write self.tracking with tracking rows
        tr=""; ruletext=""
   #     if gl.d==6: print ("TRACK 1 db",db.name,"coni",coni,"db ci",db.ci)
        tr = self.is_tracked(" TRACKED CONCEPT",tr,db.cp[coni].mentstr)    # record tracked concept in tr
        if len(rule)>0 :
            tr=self.is_tracked(" TRACKED RULE ",tr,rule)    # record tracked rule in tr              
            ruletext="  rule: "+rule
        if gl.args.debug>=level or len(tr)>0: 
            self.tracking.append (msg+tr+" db="+str(db.this)+" "+str(coni)+" "+db.cp[coni].mentstr+ruletext)
       # if gl.d==4: print (msg+tr+" db="+str(db.this)+" "+str(coni)+" "+db.cp[coni].mentstr+ruletext)

    def track_double(self,db,coni,msg,db2,coni2,msg2,level,rule=""):
        ruletext=""
        tr = self.is_tracked(" TRACKED CONCEPT","",db.cp[coni].mentstr)    # record tracked concept in tr
        if len(rule)>0 :
            tr=self.is_tracked(" TRACKED RULE ",tr,rule)    # record tracked rule in tr  
            ruletext="  rule: "+rule
        tr2 = self.is_tracked(" TRACKED CONCEPT","",db2.cp[coni2].mentstr)    # record tracked concept2 in tr
        if gl.args.debug>=level or len(tr)>0 or len(tr2)>0: 
            self.tracking.append (msg+tr+" db="+str(db.this)+" "+str(coni)+" "+db.cp[coni].mentstr+" p="+str(db.cp[coni].p)+msg2+tr2+" db2="+str(db2.this)+" "+str(coni2)+" "+db2.cp[coni2].mentstr+" p="+str(db2.cp[coni2].p)+ruletext)

            
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
