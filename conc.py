import sys, gl
from timeit import default_timer as timer

class Concept:
    def __init__(self,rel=0):
        self.p = int(gl.args.pmax/2)        # p value of concept
        self.c = int(gl.args.cmax)          # consistence of this concept and previous concepts
        self.g = int(gl.args.gmax)          # generality: how specific (0) or general (1) is the concept
        self.each = int(gl.args.eachmax/2)  # each property: 0 means exception, 4 means each=no exception for sure
        self.relevance = int(gl.args.rmax/2)  # relevance of the concept
        self.relation = rel # relation code
        self.parent = []    # parents list
        self.child = []     # children list
        self.previous = -1  # previous concept
        self.next = []      # list of next concepts
        self.wordlink = []  # link to WL, if this is a word
        self.kblink = []    # link to KB, if this is in WM
        self.mapto = -1     # another concept in WM where this one is mapped to
        self.wmuse = [-1]   # what concepts were used to get this one by reasoning. Or -1 if original input.
        self.reasonuse = [] # rule and concepts directly used for reasoning
        self.usedby = set() # new concepts that use this old concept for reasoning
        self.general = set([])  # set of lists of concepts more general than this one
        self.same = set()   # set of concepts being the same
        self.mentstr = ""   # string format of mentalese
        self.rulestr = []   # strings for rule-information like p=p1 or p=pclas
        self.kb_rules = []  # list of rules in KB which match this concept
        self.rule_match = []  # list of WM concepts that match the respective rule of kb_rules

    def add_parents(self, parents):
        for parentitem in parents: self.parent.append(parentitem)
        
    def is_leaf(self):
        return len(self.next) == 0


class Kbase:
    
    def __init__(self, instancename):
        self.cp = []                    # CONCEPT LIST CP
        self.ci = -1
        self.branch=[]                  #list of living branches (branch leafs)
        self.brelevant = set()          # set of relevant branches, where current wmpos occurs
        self.branchvalue = {}           # evaluation (consistency) of each branch. Mapped to branch leaf.
        self.branchactiv = {}           # set of activated concepts on branch
        self.samestring = {}            # for each branch leaf: a map of mentalese string: all occurence index on branch
        self.paragraph = []             # concepts where the latest paragraph ended on all branches
        self.name = instancename        # the name of the instance can be used in the log file
        self.thispara = []              # list of concepts in this paragraph
        self.prevpara = []              # list of concepts in previous paragraph

    def check_Contradiction(self,sindex,rule,pin,conclist):     # process contradiction
        if self.cp[sindex].p == pin:                        # no contradiction
            return 1                                        # match found
        elif pin==gl.args.pmax/2 or self.cp[sindex].p==gl.args.pmax/2:   # one of the concepts is unknown
            return 0                                        # no match
        else:                                               # contradiction found
            try:
                if rule[0] in gl.KB.cp[self.cp[sindex].reasonuse[0]].general:   # the new concept's rule is more general than used for old
                    gl.log.add_log(("CONTRADICTION: inhibit reasoning in check_Contra: based on more general rule. Specific rule based old  index=",sindex," general rule:",rule[0]))
                    return 1                                # match found, inhibits reasoning
                if self.cp[sindex].reasonuse[0] in gl.KB.cp[rule[0]].general:   # the contradicting old concept used a more general rule
                    gl.log.add_log(("CONTRADICTION: PVALUE OVERRIDE in check_Contra because p was based on general rule. index=",sindex," old p=",self.cp[sindex].p," new p=",pin," used by:",self.cp[sindex].usedby))
                    self.cp[sindex].p=pin                   # override p in old
                    for used in self.cp[sindex].usedby:     # concepts that used this sindex
                        gl.log.add_log(("CONTRADICTION: PVALUE OVERRIDE TO MAX/2 in check_Contra because based on p-overriden concept. index=",used," old p=",self.cp[used].p," overriden concept:",sindex))
                        self.cp[used].p=gl.args.pmax/2      # set p value to unknown
            except: a=0
        if len(conclist)>0:                                 # list of concepts used for the new reasoning
            alluse=set()
            for newuse in conclist:
                alluse.add(newuse)
                alluse.update(self.cp[newuse].same)         # add those concepts same as used concept to all used concepts
            general_newconc = alluse & self.cp[sindex].general  # set of used concepts that are general to the old concept
            if len(general_newconc)>0:                      # new concept would use input that is more general than the old concept
                gl.log.add_log(("CONTRADICTION: inhibit reasoning in check_Contra: more general input. Specific old index=",sindex," too general input=",general_newconc))
                return 1                                    # found=1 will inhibit reasoning
        # TO DO: if new concept is more specific, than input used for the old concept, override p value of old !!!!! MISSING
        return 0

    def search_fullmatch(self,pin,rel,parents,rule,branch=[],conclist=[]):
        found=0; s=timer()
        if self.convert_p(pin) == self.convert_p(gl.args.pmax/2):   #p70.5 will not be reasoned
            found=1
        else:
            for sindex in range(0,self.ci+1):                       # search for match in entire WM (on branch)
                con=self.cp[sindex]
                if con.relation==rel and (branch==[] or sindex in branch):   #only match to concepts in branch
                    if len(con.parent)==len(parents) and (1==1 or con.p==pin):    # p value not checked here but in check_Contra                                        # p value checked currently
                        pari=0; allsame=1                           #allsame will show if all parents are the same
                        while pari<len(con.parent) and allsame==1:  #only check until first different parent found
                            parent1wm=con.parent[pari]
                            if len(parents)>pari:
                                p1=parent1wm; p2=parents[pari]
                                thisfound=self.rec_match(self.cp[p1],self.cp[p2],[p1,p2])     #parents are compared
                                if thisfound!=1: allsame=0
                                else:                               #exception for D( , ) relation for mapping
                                    if con.relation==3 and len(parents)==2 and len(con.parent)==2 and parents[0]!=con.parent[0]:
                                        allsame=0                   #direct index comparison
                            else:
                                allsame=0
                            pari+=1
                        if allsame==1:
                            foundnow=self.check_Contradiction(sindex,rule,pin,conclist)    # check whether we have contradiction and resolve it
                            if foundnow == 1: found=1
        gl.args.settimer("concep_902: search_fullmatch",timer()-s)
        return found    # TO DO: feed back allsame in found, to populate .general in reasoned concept in finaladd


    def convert_p(self,newp):                       # convert p from 0..1 to 0,1,2,3,...
        out=newp
        if gl.args.pmax==gl.args.pgranu:            # this initiates conversion
            if newp<=1:
                out1=float(gl.args.pmax)/gl.args.pgranu
                out=out1 * round(newp*gl.args.pmax)
        if out>1: out=round(out)                    # this converts 1.1
        return out

    def getp_backward(self,swhat,pback):            # search earlier occurence of swhat and return p
        sindex=self.cp[swhat].previous              # proceed on branch
        found=0
        while sindex>-1 and pback==gl.args.pmax/2:  #do not stop on p=2
            if self.rec_match(self.cp[swhat], self.cp[sindex], [swhat,sindex]) == 1:
                found=1
                pback=self.cp[sindex].p
                self.cp[swhat].wmuse=[sindex]       #set wmuse to see whjere we get the p value from
            sindex=self.cp[sindex].previous
        return pback

    def update_Samestring(self,oldleaf,newleaf):                #update WM.samestring dictionary key and WM.brelevant set
        if self.name=="WM":
            if oldleaf in gl.WM.samestring:
                gl.WM.samestring[newleaf] = gl.WM.samestring.pop(oldleaf)   # this removes the oldleaf key
            if oldleaf in gl.WM.brelevant:                      # brelevant is the set of branch leafs for current wm_pos
                gl.WM.brelevant.remove(oldleaf)
                gl.WM.brelevant.add(newleaf)
                
    def add_concept(self, new_p, new_rel, new_parents,kbl=[],gvalue=None):        #add new concept to WM or KB. parents argument is list
        self.cp.append(Concept(new_rel))                        #concept added
        self.ci = len(self.cp) - 1                              #current index
        self.cp[self.ci].previous=self.ci-1                     #set previous
        if self.ci>0:
            if self.cp[self.ci-1].next==[]:
                self.cp[self.ci-1].next.append(self.ci)         # set next                
        self.cp[self.ci].p = int(new_p)                         # set p value
        self.cp[self.ci].add_parents(new_parents)               # set parents
        self.cp[self.ci].kblink[:]=kbl[:]                       # set link to KB
        if kbl==[] and self.name=="KB" and new_rel==1:          # word addition in KB
            self.cp[self.ci].kblink.append(self.ci)             # add own index in KB
        if (new_rel != gl.args.rcode["W"]):                     # if this is not a word
            for par in self.cp[self.ci].parent:                 # register new concept as the child of parents
                self.cp[par].child.append(self.ci)

            self.cp[self.ci].mentstr = gl.args.rcodeBack[new_rel] + "("     # set mentstr
            for cind in self.cp[self.ci].parent:
                self.cp[self.ci].mentstr = self.cp[self.ci].mentstr + self.cp[cind].mentstr + ","
            self.cp[self.ci].mentstr = self.cp[self.ci].mentstr[:-1] + ")"
            
        else:                                                   #this is a word
            if (len(kbl)>0):                                    #set word link if we have KB link
                self.cp[self.ci].wordlink.append(gl.KB.cp[kbl[0]].wordlink[0])      # we have a single word link
                self.cp[self.ci].mentstr = gl.KB.cp[kbl[0]].mentstr[:]
            if gvalue!=None: self.cp[self.ci].g=gvalue          #explicit generality provided
        if self.name=="WM" and self.branch==[]:                 #in WM, no leafs stored
            self.update_Samestring(gl.WM.ci-1,gl.WM.ci)         #update the leaf in samestring
        if new_rel == 13 :                                      # IM relation
            pari=0
            for par in self.cp[self.ci].parent : 
                self.cp[par].p = self.convert_p(gl.args.pdef_unknown)       #this is after concept is added. So log file is bad.
                if pari==0:                                     # condition in IM
                    self.cp[par].p = self.getp_backward(par,self.convert_p(gl.args.pdef_unknown))   # use the p value of earlier occurence of concept
                    gl.log.add_log(("PVALUE modification in add_concept. WM index:",par," new p value:",self.cp[par].p))
                pari+=1

        gl.log.add_log((self.name," add_concept index=",self.ci," p=",self.cp[self.ci].p," rel=",new_rel," parents=",new_parents," wordlink=",self.cp[self.ci].wordlink," mentstr=",self.cp[self.ci].mentstr))      #content to be logged is tuple (( ))
        return self.ci

    def copy_Samestring(self,oldleaf,newleaf):              # expand the WM.samestring dictionary with newleaf key, copyiing content from oldleaf
        if oldleaf in gl.WM.samestring:                     #this expand is needed when new branch was added
            gl.WM.samestring[newleaf]={}
            for ment in gl.WM.samestring[oldleaf]:          #mentalese strings are keys
                gl.WM.samestring[newleaf].update({ment:gl.WM.samestring[oldleaf][ment][:]})   #copy list of identical mentalese concepts
        if oldleaf in gl.WM.brelevant:                      # brelevant is the list of leafs for current WM pos
            gl.WM.brelevant.add(newleaf)                    # add this element to the set
        if oldleaf in gl.WM.branchactiv:                    # expand branchactiv mapping
            gl.WM.branchactiv[newleaf]=set()
            gl.WM.branchactiv[newleaf].update(gl.WM.branchactiv[oldleaf])  # copy activated concepts of old branch
            if oldleaf in gl.WM.branchactiv[newleaf]:
                gl.WM.branchactiv[newleaf].remove(oldleaf)  # oldleaf is not part of newleaf branch (branching happened before oldleaf)

    def update_Branchactiv(self,oldleaf,newleaf):           # update WM.branchactiv keys
        if self.name=="WM":
            if oldleaf in gl.WM.branchactiv:
                gl.WM.branchactiv[newleaf]=gl.WM.branchactiv.pop(oldleaf)   # this removes oldleaf key and replaces with newleaf
            else:
                if oldleaf==-1:                             # only for first concept in WM
                    gl.WM.branchactiv[newleaf] = set()      # leaf needs to be added
            if newleaf<oldleaf:                             # concept removal has happened (removal impacts a leaf in any case)
                if newleaf in gl.WM.branchactiv:
                    if oldleaf in gl.WM.branchactiv[newleaf]:  # old leaf was activated but got removed
                        gl.WM.branchactiv[newleaf].remove(oldleaf)  # remove old leaf as that was removed from WM
            else:                                           # concept addition happened
                if gl.act.allwmactive == 1:                 # entire WM needs activation
                    gl.act.activate_Conc(newleaf,[newleaf]) # activate the concept added now

    def update_Branchinfo(self,oldleaf,newleaf,newvalue=-999):  # update branch related info in self.branch, self.branchvalue and self.samestring
        if oldleaf!=newleaf:                                # update necessary
            self.update_Samestring(oldleaf,newleaf)         # WM.samestring key must be updated anyway
            self.update_Branchactiv(oldleaf,newleaf)        # WM.branchactiv key must be updated anyway
            if oldleaf in gl.WM.branch:                     # this is in fact a leaf
                gl.WM.branch.remove(oldleaf)
                try:
                    value=self.branchvalue[oldleaf]
                    del self.branchvalue[oldleaf]           #value remembered, old item removed
                except:
                    value=4   #FIX NEEDED
                    gl.log.add_log(("ERROR in update_Branchinfo (conc.py): oldleaf not existing in WM.branchvalue:",oldleaf," branches=",gl.WM.branch))
                if newleaf>-1:
                    gl.WM.branch.append(newleaf)
                    self.cp[newleaf].next=[]                #for a leaf, next is empty
                    if newvalue==-999:                      #no new branch value provided
                        self.branchvalue[newleaf]=value     #old value kept
                    else: self.branchvalue[newleaf]=newvalue

            
    def remove_concept(self):
        gl.log.add_log((self.name," remove concept index=",self.ci))
        if (self.ci>-1):
            newleaf=self.cp[self.ci].previous
            self.cp.pop()
            self.ci=self.ci-1
            if self.name=="WM":
                self.update_Branchinfo(self.ci+1,newleaf)   #update branch related lists and dicts
        return self.ci

    def get_branch_concepts(self, beforei):             #returns the id list of previous concepts on branch (inclusive)
        previous_concepts=[]
        curri=beforei
        while curri != -1:
            previous_concepts.append(curri)
            curri = gl.WM.cp[curri].previous
        return previous_concepts

    def reverse_Drel(self,new,old):                     #new and old are D relations, the function checks reverse order.
        pn0=self.cp[new].parent[0]
        pn1=self.cp[new].parent[1]
        po0=self.cp[old].parent[0]
        po1=self.cp[old].parent[1]
        if self.cp[pn0].mentstr == self.cp[po1].mentstr and self.cp[pn1].mentstr == self.cp[po0].mentstr:  #strings match in reverse order
            if self.rec_match(self.cp[pn0],self.cp[po1],[pn0,po1]):     #they match
                if self.rec_match(self.cp[pn1],self.cp[po0],[pn1,po0]):     #other pair also match
                    if self.cp[new].p==gl.args.pmax/2:                  #new needs update
                        self.cp[new].p=self.cp[old].p                   #new updated
                        gl.log.add_log(("PVALUE OVERRIDE in reverse_Drel. overridden=",new," based on:",old,"new p=",self.cp[old].p))
                    if self.cp[old].p==gl.args.pmax/2:                  #old needs update
                        self.cp[old].p=self.cp[new].p                   #old updated
                        gl.log.add_log(("PVALUE OVERRIDE in reverse_Drel. overridden=",old," based on:",new,"new p=",self.cp[old].p))
                        
    def search_onbranch(self,swhat,swhatindex):                     # search answer on branches separately
        found=[]
        if self.branch==[]: branches=[gl.WM.ci]                     #no branches, just the default
        else: branches = self.branch[:]
        for leaf in branches:                                       #all branches
            thisbr = self.get_branch_concepts(leaf)                 #entire branch, reverse order
            sindex = len(thisbr)-1
            while sindex>=0:
                if gl.WM.cp[thisbr[sindex]].relation==3 and swhat.relation==3 and thisbr[sindex]<swhatindex:    # two D relations: replace parent 0 with 1
                    if len(gl.WM.cp[thisbr[sindex]].parent) == 2 and len(swhat.parent)==2:
                        self.reverse_Drel(swhatindex,thisbr[sindex]) # reverse D() and override p   
                if self.rec_match(swhat,gl.WM.cp[thisbr[sindex]], [swhatindex,thisbr[sindex]]) == 1:     # identical concept
                    found.append([leaf, thisbr[sindex]])            # add to found list, noting the branch too
                sindex = sindex-1
        return found

    def get_previous_concepts(self,beforei):            # returns the id list of previous concepts (inclusive)
        previous_concepts = []
        curri = beforei
        while curri != -1:
            previous_concepts.append(curri)
            curri = gl.WM.cp[curri].previous
        return previous_concepts

    def select_Relevant(self,wmpos):        #select all branches in which we have wmpos
        relevant=[]
        for br in gl.WM.branch:
            thisbr=self.get_previous_concepts(br)
            if wmpos in thisbr: relevant.append(br)
        if gl.WM.branch==[]:
            relevant=[gl.WM.ci]
        return relevant                     #this is empty list if branch of wmpos was killed earlier

#    def select_Relevant_quick(self,wmpos,thisbr):        #faster select all branches in which we have wmpos
 #       relevant=[]
  #      for br in gl.WM.branch:
   #         if wmpos in thisbr: relevant.append(br)
    #    if gl.WM.branch==[]:
     #       relevant=[gl.WM.ci]
      #  return relevant                     #this is empty list if branch of wmpos was killed earlier

    def isword_Special(self,what1,inwhat):          # compare two words to see if one word is a special case of the other
        is_special=0                # one of the words may be a specific one, the other %1, then %1 is more general
        end1=gl.KB.cp[what1.kblink[0]].mentstr[1:]
        end2=gl.KB.cp[inwhat.kblink[0]].mentstr[1:]
        if gl.KB.cp[what1.kblink[0]].mentstr[0]=="%":
            try:
                float(end1)                         # check that the word after the % is numeric
                if gl.KB.cp[inwhat.kblink[0]].mentstr[0]!="%":
                    is_special=2                    # the inwhat word is special
            except: is_special=is_special
        if gl.KB.cp[inwhat.kblink[0]].mentstr[0]=="%":
            try:
                float(end2)                         # check that the word after the % is numeric
                if gl.KB.cp[what1.kblink[0]].mentstr[0]!="%":
                    is_special=3                    # the what1 word is special
            except: is_special=is_special
        return is_special
            

    def rec_match(self, what1, inwhat, wmindex=[], castSecondKbase=0, goodanswer=0):  # two concepts match? handles questions
        # castSecondKbase help to compare WM concept with KB concept
        #       castSecondKbase = 0 -> no cast, both concepts are searched in the Kbase from which the function was called
        #       castSecondKbase = 1 -> cast to KB, i.e. second concepts is searched in KB, whichever Kbase the function was called from
        #       castSecondKbase = 2 -> cast to WM, i.e. second concepts is searched in WM, whichever Kbase the function was called from
        # wmindex is the concept index pair in WM for g=0 comparison
        # goodanswer is a flag to show that we are doing expected good answer vs system answer comaprison from eval_test
        s=timer()
        match=1
        if what1.relation != -1 and inwhat.relation != -1 and what1.relation != inwhat.relation:
            if len(wmindex)==2 and wmindex[0] in inwhat.general: return 2   # indicates special case concept of inwhat
            if len(wmindex)==2 and wmindex[1] in what1.general: return 3    # indicates special case concept of what1
            if what1.relation==1 and what1.mentstr[0]=="%": return 2        # indicates special case concept of inwhat
            if inwhat.relation==1 and inwhat.mentstr[0]=="%": return 3        # indicates special case concept of what1
    # check that the compound concept is rfeally a special case of word: C(compond,word) or compound=F(word,feature)
            return 0     # relation is neither same nor -1 -> not match

        if what1.relation == 1:     # comparing two word concepts. Handle specific words differently as general ones.
            if what1.kblink == inwhat.kblink and what1.g==gl.args.gmax and inwhat.g==gl.args.gmax:
                return 1                                                    # two words are the same, both are general
            if len(wmindex)==2 and wmindex[0] in inwhat.general: return 2
            if len(wmindex)==2 and wmindex[1] in what1.general: return 3
            if what1.kblink == inwhat.kblink:
                if self.name=="WM" and (castSecondKbase==0 or castSecondKbase==2):   # two WM concepts compared
                    if what1.g>gl.args.gmin and inwhat.g>gl.args.gmin:      # both concepts are general
                        return 1
                    else:                                                   # one or two concepts are specific. Indices must match.
                        if len(wmindex)==2 and wmindex[0]==wmindex[1]:      # compare concept index directly
                            return 1                                        # match only if indices are the same.
                        else:                                               
                            if goodanswer==1: return 1                    # match if this is answer goodness evaluation
                            else: return 0                                  # probably some error.
                else: return 1                                              # for KB comparison return 1
            else: 
                return self.isword_Special(what1,inwhat)                    # see whether %1 and specific word are given
        
        if len(what1.parent) != len(inwhat.parent):
            return 0     # if number of parents are not equal -> not match
            
        for pindex in range(0, len(what1.parent)):
            p1 = what1.parent[pindex]; p2 = inwhat.parent[pindex]
            allpis2=0; allpis3=0                                            # will indicate if what1 or inwhat is special case
            if what1.parent[pindex] == -1 or inwhat.parent[pindex] == -1 :     # handle -1 parents
                continue    # -1 indicates question mark, this is considered as matching
            if castSecondKbase == 1 : 
                pm = self.rec_match(self.cp[p1], gl.KB.cp[p2], [p1,p2], castSecondKbase)
            elif castSecondKbase == 2 : 
                pm = self.rec_match(self.cp[p1], gl.WM.cp[p2], [p1,p2], castSecondKbase)
            else :
                pm = self.rec_match(self.cp[p1], self.cp[p2], [p1,p2],goodanswer=goodanswer)      # compare parent concepts for match
            if pm==0: return 0                          # if parent concept does not match -> no match
            if pm == 2:
                self.cp[p2].general.add(p1)             # record general relation for parent
                if match == 3: return 0                 # cross special
            if pm == 3:
                self.cp[p1].general.add(p2)             # record general relation
                if match==2: return 0                   # cross special
            if pm>1 and match==1: match=pm              # special 2 or 3
        if match==2 and len(wmindex)==2 : inwhat.general.add(wmindex[0])    # remember that what1 is general of inwhat
        if match==3 and len(wmindex)==2: what1.general.add(wmindex[1])      # remember that inwhat is general of what1
        gl.args.settimer("concep_901: rec_match",timer()-s)    
        return match

    def get_child(self,rel,parents=[]):                 # search concept as child of parent
        found=-1
        for child in self.cp[parents[0]].child:         # in children of the first parent
            if (self.cp[child].relation==rel):          # relation must match
                if (self.cp[child].parent==parents):    # parents must match
                    found=child
        return found

    def walk_db(self,curri,lasti=-2):                   # recursive walk over WM or KB from curri towards all parents. Call without lasti.
        # jumps over identical items !!!!!!
        while (len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp=self.cp[curri].parent.index(lasti)+1
            except:
                lasti=-2        # enter lower level
                nextp=0
            lasti=self.walk_db(self.cp[curri].parent[nextp],lasti)
        print ("walk",self.name,"current concept",curri,"parents",self.cp[curri].parent,"mentalese",self.cp[curri].mentstr,"rule:"[:5*len(self.cp[curri].rulestr)],self.cp[curri].rulestr)
        return curri

    def visit_db(self,db,curri,visitmap,nextp=0):       #demo a recursive walk that is not jumping over identical items
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk over parents of same level
            self.visit_db(db,db.cp[curri].parent[nextp],visitmap,0)             # one level down
            nextp=nextp+1
        visitmap.append([curri,db.cp[curri].mentstr])       # actual data manipulation
        return

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
                    kbl=gl.KB.add_concept(self.cp[curri].p,self.cp[curri].relation,plist)   # copy to KB
                    gl.KB.cp[kbl].relevance = self.cp[curri].relevance  #copy relevance
                    gl.KB.cp[kbl].g = self.cp[curri].g  # copy generality
                self.cp[curri].kblink.append(kbl)   # set KB link in WM
        return curri

    def check_Children(self,db,curri,what,result,nextp=0):  # recursive check towards children to compare concepts
        while len(db.cp[curri].child)>0 and nextp<len(db.cp[curri].child):  # walk over children of same level
            self.check_Children(db,db.cp[curri].child[nextp],what,result,0)
            nextp+=1                                                        # next child
        if db.cp[curri].relation==13 and len(db.cp[curri].child)==0:        # we are on IM level
            match = db.rec_match(db.cp[what],db.cp[curri])                  # compoare rules
            if match==2 and [what,curri] not in result: result.append([what,curri])     # curri is special
            if match==3 and [curri,what] not in result: result.append([curri,what])     # kblink[0] is special
        else: return 0
        return match

    def check_Specialrule(self,kblink):         # compare new rule to old ones
        i1 = gl.WL.find_word("%1")
        speclist=[]
        self.check_Children(gl.KB,gl.WL.wcp[i1].wchild[0],kblink[0],speclist)   # in KB we take all children of the first meaning of word %1
        return speclist
            
    def move_rule(self,tf,ri,starti):           # if this is a rule then move it to KB
        if ("%1" in tf.mentalese[ri]):          # if this is a rule
            gl.WM.copyto_kb(gl.WM.ci)           # copy last concept in WM, which should be the rule, to KLB
            kblink=gl.WM.cp[gl.WM.ci].kblink
            speclist = self.check_Specialrule(kblink)   # is this rule a special case of a more general one, or vicxe versa?
            for sp in speclist:                 # record special and general cases
                gl.KB.cp[sp[1]].general.add(sp[0])   # in the special concept, add the general index
            for i in range(gl.WM.ci-starti):
                try:
                    if len(gl.WM.cp[gl.WM.ci].rulestr)>0:   #rule string like p=p0 is there
                        #record rule string info on the IM level of the rule:
                        gl.KB.cp[kblink[0]].rulestr.append(str(gl.WM.cp[gl.WM.ci].kblink[0])+gl.WM.cp[gl.WM.ci].rulestr)
                except: gl.log.add_log(("ERROR in move_rule in conc.py: could not assemble rule string. KB index:",kblink[0]," WM index:",gl.WM.ci)) 
                gl.WM.remove_concept()     # remove rule from WM
        

    def move_relevant(self, starti):                # if this is top relevant knowledge, move it to KB
        if (gl.WM.cp[gl.WM.ci].relevance==gl.args.rmax):    #r=rmax
            gl.WM.copyto_kb(gl.WM.ci)               #copy the relevant concept to KB
            for i in range(gl.WM.ci-starti):        #entire group of moved concept
                gl.WM.remove_concept()              #remove copied concept from WM

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

    def remove_Frombranch(self,starti,endi,awlist):     # remove input (question etc) from all branches
        leng = endi-starti
        awoutlist = []
        if endi == gl.WM.ci :
            if self.branch == []: branches=[self.ci]
            else: branches = self.branch[:]
        if len(branches)>1:
            bsort = sorted(branches, key=int, reverse=True)
            leng = bsort[0]-bsort[1]                #on the branch we only have the new input. so this is the length of it.
        for leaf in sorted(branches, key=int, reverse=True):    #branches starting from the last one
            if leaf == gl.WM.ci:                    #this must hold as we had the new input as last addition
                if leng>0: gl.log.add_log((self.name, " remove several concepts from index=",self.ci," number of concepts removed=",leng))
                for i in range(leng):               #remove proper number of concepts
                    preleaf = self.cp[self.ci].previous     #new leaf value
                    self.cp.pop()                   #remove concept
                    self.ci = self.ci -1
                if leng>0:                          #something removed from a branch
                    self.update_Branchinfo(leaf,preleaf)  # update branch related lists and dicts
                for aw in awlist:                   #update leaf values in answerlist !!
                    if leaf == aw[0]:               #this needs update
                        if leng>0 and preleaf>-1:
                            awoutlist.append([preleaf,aw[1]])
        return awoutlist

    def find_undefined_parents(self,curri,qc,lasti=-2): # recursive search for ? parent. Call without lasti.
        while (curri>-1 and len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp = self.cp[curri].parent.index(lasti)+1
            except: lasti=-2; nextp=0
            lasti = self.find_undefined_parents(self.cp[curri].parent[nextp],qc, lasti)
        if curri==-1: qc[0]=qc[0]+1                 #qc[0] is the counter for ? parents which have -1 value
        return curri                                #qc[0] is also kept as it is transferred by reference


    def answer_question(self,starti,endi):          #answer a question now stored in WM
        answerlist=[]                           
        self.rec_set_undefined_parents(endi)        #sets -1 parents instead of ? character
        qcount=[0]                                   #counter for ? parents
        self.find_undefined_parents(endi,qcount)    #recursive search for -1. qcount gets updated.
        answers = gl.WM.search_onbranch(gl.WM.cp[endi],endi) #search for answers on all branches
        if self.branch == []: branches=[self.ci]
        else: branches=self.branch[:]
        awbrlist=[]                                 # here we note if we have answer on this branch
        for aw in answers:
            if (aw[1] not in branches or (aw[0] not in awbrlist and qcount[0]==0)):               #the question itself is an answer and a leaf, must be removed
                answerlist.append(aw)
            awbrlist.append(aw[0])
        if qcount[0]>0:                             #if -1 parent in input, then it must be removed
            answerlist = self.remove_Frombranch(starti,endi,answerlist[:])[:]
        for leaf in branches:                       #do not remove question if it is Z(a,b)? but may need to be added to answers
            answeryes=[]
            for anw in answerlist:
                if leaf==anw[0]: answeryes=1        #remember we have answer
            if qcount[0]==0:                        #question like Z(a,b)?
                if answeryes==0: answerlist.append([leaf,leaf]) #question added as answer
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
        
    def get_numeric_value(self, aStr, actPos):
        n_end=actPos+4
        while n_end <= len(aStr):
            try:
                value=float(aStr[actPos+3:n_end])
            except:
                n_end -= 1
                break
            else:
                n_end += 1
        value=float(aStr[actPos+3:n_end])
        return (value, n_end)
        
    def get_p(self, aStr, actPos):
        try: 
            numeric_result=self.get_numeric_value(aStr, actPos)
            return numeric_result + ([],)
        except:                                             # rule, like p=p1
            rulStr=self.get_rulestr(aStr,actPos)            # process the rule-string
            return (gl.args.pdef_unknown, actPos+1+len(rulStr), rulStr)
        
    def get_r(self, aStr, actPos):
        return self.get_numeric_value(aStr, actPos)               # explicit r value like r=0.1

    def get_g(self, aStr, actPos):
        return self.get_numeric_value(aStr, actPos)               # explicit g value like g=0

    def word_get_num(self, aStr, actPos):               # someword.g=0 format for explicit g value for words
        gvalue=gl.args.gmax                             # TO DO make it general for p, r ...
        if ".g=" in aStr[0:actPos]:
            actpos2=aStr.find(".g=")
            gvalue=self.get_numeric_value(aStr,actpos2)[0]
        return gvalue
        

    def get_Maprules(self,wordpos,wordstr=""):                 # find mapping rules for the word on self.wmpos
        maplist=[]
        word_kb=-1
        if wordstr=="" and gl.WM.cp[wordpos].relation==1:       #this is a word
            wordstr=gl.WM.cp[wordpos].mentstr
        if wordstr!="":
            wpos=gl.WL.find_word(wordstr)
            word_kb = gl.WL.wcp[wpos].wchild[0]     #word meaning in KB
            rulecount=1
        if word_kb!=-1:
            for child in gl.KB.cp[word_kb].child:
                if gl.KB.cp[child].relation==4:     #C relation
                    
                    if gl.KB.cp[child].relevance==gl.args.rmax: #top relevant C relation
                        if wordstr==gl.KB.cp[gl.KB.cp[child].parent[0]].mentstr:  #word is x in C(x,y)
                            if rulecount==1:    #TO DO now we handle 1 rule only
                                maplist.append(child)
                                rulecount+=1
        return maplist


    def override_Parent(self, isq, wordpos, leaf):  # perform default mapping for question argument and for g=0 concepts
        overparent = wordpos                        # wordpos is the original parent, initially we have no override
        qsw = gl.reasoning.question_specific_words[:]   # copy words of the question to be mapped and g=0
        thisbr = self.get_branch_concepts(leaf)     # leaf is the real branch where wordpos will be added to
        if isq == 1:                                # question override needed
            for qword in qsw:                       # critical words of teh question
                if gl.WM.cp[wordpos].mentstr == qword[0]:   # this word of the question is stored as question spec word
                    if qword[1] in thisbr:          # qword is on the same branch as this word
                        overparent = qword[1]       # override parent
        if overparent == wordpos and gl.WM.cp[wordpos].g==gl.args.gmin:   # not override but g=0. does not need to be question.
            maprule=self.get_Maprules(wordpos)      # is this to be mapped?
            if maprule==[]:                         # not mapped
                for con in thisbr:                  # backward on branch
                    if con in self.paragraph: break   # stop if paragraph border exceeded
                    if gl.WM.cp[con].g==gl.args.gmin and gl.WM.cp[con].mentstr==gl.WM.cp[wordpos].mentstr:    # TO DO is this general?
                        overparent = con            # override parent, repeatedly up to the first occurence in paragraph
        if wordpos!=overparent:                     # override happens
            gl.reasoning.currentmapping[gl.WM.cp[wordpos].mentstr]=overparent   # collect mappings based on word
        return overparent

    def override_Old(self,contralist):              # override old p if new input is more special
        for contraitem in contralist:               # contradictions
            newi=contraitem[0]; old=contraitem[1]
            genset=set()
            for gen in self.cp[newi].general:       # collect general items, including same items to general ones
                genset.add(gen)
                genset.update(self.cp[gen].same)
            gen_used=set(self.cp[old].reasonuse) & genset   # general items that were used to reason old
            if len(gen_used)>0:                     # any used: p needs override
                gl.log.add_log(("CONTRADICTION: PVALUE OVERRIDE from set_General: old p was based on more general input. index=",old," old p=",self.cp[old].p," new index=",newi," new p=",self.cp[newi].p))
                self.cp[old].p = self.cp[newi].p    # override old p
                for used in self.cp[old].usedby:    # reasoned concepts that use this old
                    gl.log.add_log(("CONTRADICTION: PVALUE OVERRIDE TO MAX/2 from set_General: make concept unknown. This concept used a too general input. index=",used," old p=",self.cp[used].p," contradicting concept:",old))
                    self.cp[used].p=gl.args.pmax/2  # set this concept to unknown

    def set_General(self,startpos):                 # investigate if latest input concepts involve a generality relation
        s=timer()
        contralist=[]
        for newi in range(startpos+1,self.ci+1):    # on all newly added inputs including self.ci
            con=self.cp[newi]                       # current concept
            old=newi
            while self.cp[old].previous!=-1:        # entire WM on current branch backward
                old=self.cp[old].previous           # next item on branch
                match = self.rec_match(con,self.cp[old],[newi,old])
                if match==1:
                    self.cp[newi].general.update(self.cp[old].general)  # if concept is the same make general list the same
                    self.cp[newi].same.add(old)     # same gets extended
                    self.cp[old].same.add(newi)     # same gets extended
                    if self.cp[newi].p!=self.cp[old].p:   # we seem to have contradiction
                        if self.cp[newi].p!=gl.args.pmax/2 and self.cp[old].p!=gl.args.pmax/2:  #contradiction
                            contralist.append([newi,old])   # collect contradictions for override
            if con.relation==5:                     # F relation
                if len(con.parent)>1:
                    con.general.add(con.parent[0])  # x is more general than F(x,y)
                    con.general.update(self.cp[con.parent[0]].same)  # concepts same to x are also general to F(x,y)
                    con.general.update(self.cp[con.parent[0]].general)  # concepts general to x are also general to F(x,y)
            if con.relation==4:                     # C relation
                if len(con.parent)>1:
                    cla=1
                    while cla<len(con.parent):     # C(x,y,z) y and z are more general than x
                        self.cp[con.parent[0]].general.add(con.parent[cla])
                        self.cp[con.parent[0]].general.update(self.cp[con.parent[cla]].same)
                        self.cp[con.parent[0]].general.update(self.cp[con.parent[cla]].general)
                        cla+=1
        self.override_Old(contralist)              # override p in contraditions found
        gl.args.settimer("concep_904: set_General",timer()-s)
                    
            
    def read_concept(self,attrList,isquestion,correct_leaf=-1,isparent=-1):     # recursive function to read concepts from Mentalese input
                                                    # we may submit the leaf of the current branch. Function returns parent indices!
        aStr=str(attrList[0]).strip()               # parameter is passed in a wrapping list to be able to use recursion
        rulStr=""                                   # string for rule-information like p=p1
        actPos=0
        relType=0
        parents=[]
        isWord=1
        while (actPos<len(aStr)):
            c = aStr[actPos]                        #check the characters in the string one-by-one
            if c == '(':                            #if finds a "(", check the relType before "(", and read the embedded concept
                isWord=0
                relType=gl.args.rcode[aStr[0:actPos]]
                attrList[0]=str(aStr[actPos+1:]).strip()
                parents.append(self.read_concept(attrList,isquestion,correct_leaf,isparent=1))
                aStr=str(attrList[0]).strip()
                actPos=0
                continue
            elif c == ',':                          #if finds a ",", there is two possible way
                if isWord==1:                       #if the concept is a word, register it to WL, add a new concept for it and return back its id
                    ss = aStr[0:actPos]
                    if ".g=" in ss: ss=aStr[0:aStr.find(".g=")]     #delete .g= from word TO DO make it general
                    wl_ind = gl.WL.find(ss)
                    attrList[0]=str(aStr[actPos:]).strip()
                    g_value=self.word_get_num(aStr,actPos)          #get g value of the word
                    if wl_ind == -1:
                        wl_ind = gl.WL.add_word(ss,g_value)
                    thisparent = self.add_concept(gl.args.pmax,1,[],[wl_ind],g_value)   #parent is empty, KB link is wl_ind
                    overparent=self.override_Parent(isquestion,thisparent,correct_leaf)
                    gl.WM.cp[thisparent].mapto=overparent           # remember in the word where it was overridden to
                    return overparent   # return the parent after potential override
                else:                               #if the concept is not a single word, register the embedded concept as parent, and read the next parent
                    attrList[0]=str(aStr[actPos+1:]).strip()
                    parents.append(self.read_concept(attrList,isquestion,correct_leaf,isparent=1))
                    aStr=str(attrList[0]).strip()
                    actPos=0
                    continue
            elif c == ')':                          #if finds a ")", there is two possible way
                if isWord==1:                       #if the concept is a word, register it to WL, add a new concept for it and return back its id
                    ss=aStr[0:actPos]
                    if ".g=" in ss: ss=aStr[0:aStr.find(".g=")]     #delete .g= from word TO DO make it general
                    wl_ind=gl.WL.find(ss)
                    attrList[0]=str(aStr[actPos:]).strip()
                    g_value=self.word_get_num(aStr,actPos)          #get g value of the word
                    if wl_ind == -1:
                        wl_ind = gl.WL.add_word(ss,g_value)
                    thisparent = self.add_concept(gl.args.pmax,1,[],[wl_ind],g_value)   #parent is empty, KB link is wl_ind
                    overparent=self.override_Parent(isquestion,thisparent,correct_leaf)
                    gl.WM.cp[thisparent].mapto=overparent           # remember in the word where it was overridden to
                    return overparent   # return the parent after potential override
                else:                               #if the concept is not a single word, register the embedded concept as parent, and read the next parent
                    p_result = None
                    r_result = None
                    g_result = None
                    if actPos+2 < len(aStr) and aStr[actPos+1:actPos+3]=='p=':
                        p_result = self.get_p(aStr, actPos)
                        actPos = p_result[1]
                        if actPos+2 < len(aStr) and aStr[actPos:actPos+3]==',r=':
                            r_result = self.get_r(aStr, actPos)
                            actPos = r_result[1]
                            if actPos+2 < len(aStr) and aStr[actPos:actPos+3]==',g=':
                                g_result = self.get_g(aStr, actPos)
                                actPos = g_result[1]
                        elif actPos+2 < len(aStr) and aStr[actPos+1:actPos+3]=='g=':
                            g_result = self.get_g(aStr, actPos)
                            actPos = g_result[1]
                    elif actPos+2 < len(aStr) and aStr[actPos+1:actPos+3]=='r=':
                        r_result = self.get_r(aStr, actPos)
                        actPos = r_result[1]
                        if actPos+2 < len(aStr) and aStr[actPos:actPos+3]==',p=':
                            p_result = self.get_p(aStr, actPos)
                            actPos = p_result[1]
                    elif actPos+2 < len(aStr) and aStr[actPos+1:actPos+3]=='g=':
                        g_result = self.get_g(aStr, actPos)
                        actPos = g_result[1]
                    else:
                        actPos += 1
                        
                    attrList[0]=str(aStr[actPos:]).strip()
                    
                    if p_result is not None:
                        if isparent==-1:                                            # this is not a parent but the top concept
                            newindex=self.add_concept(self.convert_p(p_result[0]),relType,parents)           # add the concept to WM
                        else:
                            newindex=self.add_concept(gl.args.pmax/2,relType,parents)           # add the concept to WM, parent has p=pmax/2
                        self.cp[newindex].rulestr=p_result[2]                        # add the rule string
                    else:
                        if isquestion==1:                                           # for question set pmax/2 p value
                            newindex=self.add_concept(int(gl.args.pmax/2),relType,parents)           # add the concept to WM
                        else:
                            if isparent==-1:                                            # this is not a parent but the top concept
                                newindex=self.add_concept(gl.args.pdefault,relType,parents)           # add the concept to WM
                            else:
                                newindex=self.add_concept(gl.args.pmax/2,relType,parents)           # add the concept to WM, parent has p=pmax/2
                        
                    if r_result is not None:
                        self.cp[newindex].relevance=r_result[0]
                    if g_result is not None:
                        self.cp[newindex].g=g_result[0]
                        
                    return newindex
                
            actPos=actPos+1
        return

    def branch_read_concept(self,starti,tfment,isquestion):     #read new input on all branches
        inibr = self.branch[:]
        try: inibr.remove(gl.WM.ci)                             #this leaf is handled separatly
        except: a=0
        mentalese = tfment[:]                                   #remember the input
        lastleaf = gl.WM.ci                                     #storeleaf has changed to this value
        if gl.WM.branch==[] or gl.WM.ci in gl.WM.branch:        #we process gl.WM.ci only if needed
            storeleaf = gl.WM.ci                                #remember the most recent leaf
            self.read_concept(tfment,isquestion,storeleaf)      #read the input to a single branch from storeleaf
            self.update_Branchinfo(storeleaf,gl.WM.ci)          #update branch related lists and dicts
            
        for leaf in inibr:                                      #any further leafs
            startpos=gl.WM.ci
            mentalese2=mentalese[:]
            if len(tfment[0])>1:
                self.read_concept(tfment,isquestion,leaf)
            else:
                self.read_concept(mentalese2,isquestion,leaf)   #read the input again. then connect it to the branch of leaf.
            if gl.WM.ci>startpos:                               #something added to WM
                gl.WM.cp[lastleaf].next=[]                      #remove continuity with lastleaf
                self.update_Branchinfo(leaf,gl.WM.ci)           #update branch related lists and dicts
                gl.WM.cp[leaf].next=[startpos+1]                #new input is continuation of branch of leaf
                gl.WM.cp[startpos+1].previous = leaf            #connectioon backward
            lastleaf=leaf
            

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
