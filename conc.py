import sys, gl, branch

class Concept:
    def __init__(self,rel=0):
        self.p = 0.5        # p value of concept
        self.c = 1          # consistence of this concept and previous concepts
        self.relevance = 1  # relevance of the concept
        self.relation = rel # relation code
        self.parent = []    # parents list
        self.child = []     # children list
        self.previous = -1  # previous concept
        self.next = []      # list of next concepts
        self.wordlink = []  # link to WL, if this is a word
        self.kblink = []    # link to KB, if this is in WM
        self.mentstr = ""   # string format of mentalese
        self.rulestr = ""   # string for rule-information like p=p1 or p=pclas

    def add_parents(self, parents):
        for parentitem in parents: self.parent.append(parentitem)
        
    def is_leaf(self):
        return len(self.next) == 0


class Kbase:
    def __init__(self, instancename):
        self.cp = []                    # CONCEPT LIST CP
        self.ci = -1
        self.name = instancename          # the name of the instance can be used in the log file

    def add_concept(self, new_p, new_rel, new_parents,kbl=[]):        #add new concept to WM or KB. parents argument is list
        c = Concept(new_rel)                        #concept added
        c.p = new_p                              #set p value
        c.add_parents(new_parents)               #set parents
        c.kblink[:]=kbl[:]                       # set link to KB
        
        if (new_rel != gl.args.rcode["W"]):                     # if this is not a word
            c.mentstr = gl.args.rcodeBack[new_rel] + "("     # set mentstr
            for cind in c.parent:
                c.mentstr = c.mentstr + self.cp[cind].mentstr + ","
            c.mentstr = c.mentstr[:-1] + ")"

        else:                                                   #this is a word
            if (len(kbl)>0):                                    #set word link if we have KB link
                c.wordlink.append(gl.KB.cp[kbl[0]].wordlink[0])      # we have a single word link
                c.mentstr = gl.KB.cp[kbl[0]].mentstr[:]
                
                self.activate_concepts(kbl[0])
                
        if gl.args.rcodeBack[new_rel] == 'IM' : 
            c.p = gl.args.pdef_unknown
            for par in c.parent : 
                self.cp[par].p = gl.args.pdef_unknown
                
        if self.name == "WM":
            return branch.add_concept_to_all_branches(c)
        else:
            return [self.add_concept_to_cp(c)]
            
    def add_concept_to_cp(self, concept):
        self.cp.append(concept)
        self.ci = len(self.cp) - 1
        if (concept.relation != gl.args.rcode["W"]):
            for par in self.cp[self.ci].parent:                 #register new concept as the child of parents
                self.cp[par].child.append(self.ci)
                
        gl.log.add_log((self.name," add_concept index=",self.ci," p=",concept.p," rel=",concept.relation," parents=",concept.parent," wordlink=",concept.wordlink," mentstr=",concept.mentstr))      #content to be logged is tuple (( ))
        return self.ci
        
    def activate_concepts(self, kbi):
        if gl.WL.wcp[gl.KB.cp[kbi].wordlink[0]].word != "?" and gl.WL.wcp[gl.KB.cp[kbi].wordlink[0]].word[0] != "%":
            activated = self.rec_get_activated_children(kbi)
            for a in activated:
                conc = gl.KB.cp[a]
                if conc.relation == gl.args.rcode["D"] and kbi in conc.parent:
                    print("mapping opportunity: " + conc.mentstr)
            
    def rec_get_activated_children(self, kbi):
        activated = []
        for child in gl.KB.cp[kbi].child:
            if gl.KB.cp[child].relevance == 1:
                activated.append(child)
                activated.extend(self.rec_get_activated_children(child))
        return activated

    def remove_concept(self):
        gl.log.add_log((self.name," remove concept index=",self.ci))
        if (self.ci>-1):
            self.cp.pop()
            self.ci=self.ci-1   
        return self.ci

    def rec_match(self, what1, inwhat, castSecondKbase=0):  # two concepts match? handles questions
        # TODO should we use booleans instead numbers?
        # e.g. result = True
        # castSecondKbase help to compare WM concept with KB concept
        #       castSecondKbase = 0 -> no cast, both concepts are searched in the Kbase from which the function was called
        #       castSecondKbase = 1 -> cast to KB, i.e. second concepts is searched in KB, whichever Kbase the function was called from
        #       castSecondKbase = 2 -> cast to WM, i.e. second concepts is searched in WM, whichever Kbase the function was called from

        if what1.relation != -1 and inwhat.relation != -1 and what1.relation != inwhat.relation:
            return 0     # relation is neither same nor -1 -> not match

        if what1.relation == 1:     # comparing two word concepts
            if what1.kblink == inwhat.kblink :
                return 1
            else: 
                return 0
        
        if len(what1.parent) != len(inwhat.parent):
            return 0     # if number of parents are not equal -> not match
            
        for pindex in range(0, len(what1.parent)):
            if what1.parent[pindex] == -1 or inwhat.parent[pindex] == -1 :     # handle -1 parents
                continue    # -1 indicates question mark, this is considered as matching

            if castSecondKbase == 1 : 
                if self.rec_match(self.cp[what1.parent[pindex]], gl.KB.cp[inwhat.parent[pindex]], castSecondKbase) == 0 : 
                    return 0    # if parent concept does not match -> no match
            elif castSecondKbase == 2 : 
                if self.rec_match(self.cp[what1.parent[pindex]], gl.WM.cp[inwhat.parent[pindex]], castSecondKbase) == 0 : 
                    return 0    # if parent concept does not match -> no match
            else :
                if self.rec_match(self.cp[what1.parent[pindex]], self.cp[inwhat.parent[pindex]]) == 0:      # compare parent concepts for match
                    return 0    # if parent concept does not match -> no match
            
        return 1

    def get_child(self,rel,parents=[]):                      # search concept as child of parent
        found=-1
        for child in self.cp[parents[0]].child:         # in children of the first parent
            if (self.cp[child].relation==rel):          # relation must match
                if (self.cp[child].parent==parents):    # parents must match
                    found=child
        return found

    def walk_db(self,curri,lasti=-2):                   # recursive walk over WM or KB from curri towards all parents. Call without lasti.
        while (len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp=self.cp[curri].parent.index(lasti)+1
            except:
                lasti=-2        # enter lower level
                nextp=0
            lasti=self.walk_db(self.cp[curri].parent[nextp],lasti)
        print ("walk",self.name,"current concept",curri,"parents",self.cp[curri].parent,"mentalese",self.cp[curri].mentstr,"rule:"[:5*len(self.cp[curri].rulestr)],self.cp[curri].rulestr)
        return curri

    def copyto_kb(self,curri,lasti=-2):         # copy concept in WM on curri to KB with all parents
        while (len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp=self.cp[curri].parent.index(lasti)+1
            except:
                lasti=-2        # enter lower level
                nextp=0
            lasti=self.copyto_kb(self.cp[curri].parent[nextp],lasti)
        # COPY ACTION to follow:
        if self.name=="WM":                         # copy from WM only
            if len(self.cp[curri].kblink)==0:       # not yet in KB
                plist=[]                            # holds parent indices valiod in KB
                for pari in self.cp[curri].parent:  # parents valid in WM
                    plist.append(self.cp[pari].kblink[0])   # append parent index valid in KB
                kbl=gl.KB.get_child(self.cp[curri].relation,plist)   # search concept in KB as child of parent
                if kbl==-1:                         # not found in KB
                    kbl=gl.KB.add_concept(self.cp[curri].p,self.cp[curri].relation,plist)[0]   # copy to KB
                    gl.KB.cp[kbl].rulestr=gl.WM.cp[curri].rulestr                           # copy rule string like p=p1    
                self.cp[curri].kblink.append(kbl)   # set KB link in WM
                # print ("KB copy curri",curri,"KB index",kbl,"ment:",gl.KB.cp[kbl].mentstr)
        return curri
            
    def move_rule(self,tf,ri,starti):           # if this is a rule then move it to KB
        if ("%1" in tf.mentalese[ri]):          # if this is a rule
            gl.WM.copyto_kb(gl.WM.ci)           # copy last concept in WM, which should be the rule, to KLB
            for i in range(gl.WM.ci-starti): gl.WM.remove_concept()     # remove rule from WM
        

    def search_inlist(self, swhat):
        found = []
        sindex = 0
        for conitem in self.cp:
            if self.rec_match(swhat, conitem) == 1:
                found.append(sindex)  # add to found list
            sindex = sindex + 1
        return found
        
    def get_previous_sentence(self, beforei):           # finds the previous full sentence concept (before the given id)
        i = beforei - 1                                 # the previous sentence concept's id must be before the given id
        while i >= 0:
            if len(self.cp[i].child) == 0:              # a concept is a full sentence concept, if it doesn't have children
                return i
            i -= 1
        return -1                                       # return -1 if no previous sentence concept available

    def rec_set_undefined_parents(self, childi):        # recursive function to replace ? words with parent=-1
        paridx=0
        for pari in gl.WM.cp[childi].parent:
            for wi in gl.WM.cp[pari].wordlink:
                if (gl.WL.wcp[wi].word=="?"):           # replace ? word with parent=-1
                    gl.WM.cp[childi].parent[paridx]=-1
            self.rec_set_undefined_parents(pari)
            paridx=paridx+1

    def answer_question(self,starti,endi):           # answer a question that is is WM
        answerlist=[]
        self.rec_set_undefined_parents(endi)
        answers=gl.WM.search_inlist(gl.WM.cp[endi])     # search in WM
        for aw in answers:
            if (aw<endi):                               # answer must be before question
                answerlist.append(aw)
        if len(answerlist)==0:                          # no answer
            if -1 not in gl.WM.cp[endi].parent:         # question not for parent but for p Z(a,b)?
                starti=endi                              # we keep the question as answer
                answerlist.append(endi)
                gl.WM.cp[endi].p=gl.args.pdef_unknown   # p is set to unknown value, 0.5
        for i in range(endi-starti): gl.WM.remove_concept()     # remove question from WM
        return answerlist
    
    def read_mentalese(self,mfilename,mlist=[]):    #read Mentalese from a file or get in a list
        if (len(mlist)==0):                         #no input in mlist
            try: 
                mfile = open(mfilename,"r")             #open Mentalese input file
                for mline in mfile:                     #read lines one-by-one and process them
                    attr=[mline]
                    while len(attr[0])>1:
                        self.read_concept(attr)
            except IOError:
                print("ERROR: Mentalese input file not present or read incorrectly")
            mfile.close()
        else:
            while len(mlist[0])>1:
                self.read_concept(mlist)

    def get_rulestr(self, aStr, pos):            # process the rule-part of mentalese string, like p=p1
        pos +=1
        out=""
        while (pos<len(aStr) and aStr[pos]!="," and aStr[pos]!=")" and aStr[pos]!=" "):
            out=out+aStr[pos]
            pos +=1
        return out
            
    def read_concept(self,attrList):                # recursive function to read concepts from Mentalese input
        aStr=str(attrList[0]).strip()               # parameter is passed in a wrapping list to be able to use recursion
        rulStr=""                                   # string for rule-information like p=p1
        actPos=0
        relType=0
        pp=gl.args.pdefault                         #default p is set to 0.5
        parents=[]
        isWord=1
        while (actPos<len(aStr)):
            c = aStr[actPos]                        #check the characters in the string one-by-one
            if c == '(':                            #if finds a "(", check the relType before "(", and read the embedded concept
                isWord=0
                relType=gl.args.rcode[aStr[0:actPos]]
                attrList[0]=str(aStr[actPos+1:]).strip()
                parents.extend(self.read_concept(attrList))
                aStr=str(attrList[0]).strip()
                actPos=0
                continue
            elif c == ',':                          #if finds a ",", there is two possible way
                if isWord==1:                       #if the concept is a word, register it to WL, add a new concept for it and return back its id
                    ss = aStr[0:actPos]
                    wl_ind = gl.WL.find(ss)
                    attrList[0]=str(aStr[actPos:]).strip()
                    if wl_ind == -1:
                        wl_ind = gl.WL.add_word(ss)
                    return self.add_concept(1,1,[],[wl_ind])  #parent is empty, KB link is wl_ind
                else:                               #if the concept is not a single word, register the embedded concept as parent, and read the next parent
                    attrList[0]=str(aStr[actPos+1:]).strip()
                    parents.extend(self.read_concept(attrList))
                    aStr=str(attrList[0]).strip()
                    actPos=0
                    continue
            elif c == ')':                          #if finds a ")", there is two possible way
                if isWord==1:                       #if the concept is a word, register it to WL, add a new concept for it and return back its id
                    ss=aStr[0:actPos]
                    wl_ind=gl.WL.find(ss)
                    attrList[0]=str(aStr[actPos:]).strip()
                    if wl_ind == -1:
                        wl_ind = gl.WL.add_word(ss)
                    return self.add_concept(1,1,[],[wl_ind])
                else:                               #if the concept is not a single word, register the embedded concept as parent, and read the next parent
                    if actPos+2 < len(aStr) and aStr[actPos+1]=='p' and aStr[actPos+2]=='=':
                        n_end=actPos+4
                        while n_end <= len(aStr):
                            try:
                                newp=float(aStr[actPos+3:n_end])
                            except:
                                n_end -= 1
                                break
                            else:
                                n_end += 1
                        try: newp=float(aStr[actPos+3:n_end])               # explicit p value like p=0.1
                        except:                                             # rule, like p=p1
                            newp=gl.args.pdef_unknown
                            rulStr=self.get_rulestr(aStr,actPos)            # process the rule-string
                            n_end=actPos+1+len(rulStr)
                        pp=newp
                        actPos=n_end
                    else:
                        actPos += 1
                    attrList[0]=str(aStr[actPos:]).strip()
                    newindexes=self.add_concept(pp,relType,parents)           # add the concept to WM
                    for newindex in newindexes:
                        self.cp[newindex].rulestr=rulStr                        # add the rule string
                    return newindexes
                
            actPos=actPos+1
        return []


if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
