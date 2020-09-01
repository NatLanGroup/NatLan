import sys, gl, branch
from timeit import default_timer as timer

class Concept:
    def __init__(self,rel=0):
        self.p = int(gl.args.pmax/2)        # p value of concept
        self.c = int(1+gl.args.cmax/2)          # consistency of this concept and previous concepts
        self.g = int(gl.args.gmax)          # generality: how specific (0) or general (1) is the concept
        self.cons_avg = int(1+gl.args.cmax/2)   # rolling average of consistency of this concept 
        self.acts = 0                       # activation level of concept
        self.exception = gl.args.exdef      # are exceptions possible? 4=yes. Also for rules. Concepts inherit from rule.        
        self.known = int(gl.args.kmax/2)    # how solid is the knowledge of p, exception for this concept
        self.relevance = int(gl.args.rmax/2) # relevance of the concept
        self.count = 1      # count the occurance of this concept
        self.relation = rel # relation code
        self.parent = []    # parents list
        self.child = []     # children list
        self.previous = -1  # previous concept
        self.next = []      # list of next concepts
        self.wordlink = []  # link to WL, if this is a word
        self.kblink = []    # link to KB, if this is in WM
        self.mapto = -1     # another concept in WM where this one is mapped to
        self.wmuse = [-1]   # what concepts (from WM) were used to get this one by reasoning. [-1]: original input [-2]: parent [-3]: reasoned, based on KB only
        self.kb_use = []    # what concepts in KB were used for reasoning
        self.override = set()   # what were the wmuse concepts, based on which this concept was overridden
        self.reasonuse = [] # rule and concepts directly used for reasoning (from WM)
        self.rule_use = []  # rule directly used for reasoning
        self.usedby = set() # new concepts that use this old concept for reasoning
        self.general = set([])  # set of lists of concepts more general than this one
        self.same = set()   # set of concepts being the same
        self.mentstr = ""   # string format of mentalese
        self.rulestr = []   # strings for rule-information like p=p1 or p=pclas
        self.kb_rules = []  # list of rules in KB which match this concept
        self.kb_rulenew = []  # list of new rules in KB which match this concept, just added in this round
        self.kbrules_upto = 0   # up to which rule are kb_rules filled. We need a new function that fills kb_rules in a single step. TO DO.
        self.kbrules_filled = 0 # flag: kb_rules filling first step done
    #    self.kbrules_converted = 0  # COMP NOT USED IN VSTEST flag to show if convert_KBrules was called for this concept
        self.rule_match = []  # list of WM concepts that match the respective rule of kb_rules. max 3 dimension list, can be 2 or 1 dimension.
        self.track = 0      # track the usage of this concept for debugging
        self.compared_upto=0 # this comcept was already compared to older ones up to this index
        self.reasoned_with = set()  # set of concepts that were already used to reason with
        
    def add_parents(self, parents):
        for parentitem in parents: self.parent.append(parentitem)
        
    def is_leaf(self):
        return len(self.next) == 0


class Kbase:
    
    def __init__(self, instancename):
        self.cp = []                    # CONCEPT LIST CP
        self.ci = -1
        self.branch=[]                  #list of living branches (branch leafs)
        self.samestring = {}            # for each branch leaf: a map of mentalese string: all occurence index on branch
        self.paragraph = []             # concepts where the latest paragraph ended on all branches
        self.name = instancename        # the name of the instance can be used in the log file
        self.thispara = []              # list of concepts in this paragraph
        self.prevpara = []              # list of concepts in previous paragraph

        self.pawm = -1                  # id of parent WM
        self.this = -1                  # id of this WM, root WM is zero, KB is -1
        self.last = -1                  # last concept id used in this wm
        self.activ = set()              # set of activated concepts in this WM
        self.kbactiv = set()            # set of activated concepts in KB given this WM
        self.activ_new = set()          # set of newly activated concepts in this WM
        self.activ_qu = set()           # set of newly activated concepts based on question in this WM
        self.kbactiv_new = set()        # set of newly activated concepts in KB given this WM
        self.mapped_Inpara = {}         # words already mapped to something within paragraph : concept index
        self.mapped_Already = {}        # at the point of mapping (in old WM!) remember what mappings are complete for each concept to be mapped.
                                        # do not copy to the new WM, it is not applicable there !! This is to avoid such a new mapping that has just been perfomed in ANOTHER wm.
        self.last_question = -1         # remember the concept id of the last question
    #    self.reasoned = set([1])        # for which concept is reasoning done in WM
        self.vs_samestring = {}         # a map of mentalese string: all occurences in this wm (or in kb)
        self.branchvalue = int(1+gl.args.bmax/2) # evaluation (consistency) of branch. 
        
    def map_Attrib(self,concindex,char):    # read and return single letter attributes given in input (a/ good answer)
        conc = self.cp[concindex]
        conc.amap = {                       # attributes denoted by a single letter in the test file input, like F(dog,nice).p=4
            "p":conc.p,"c":conc.c,"g":conc.g,"a":conc.acts,"e":conc.exception,"k":conc.known,"r":conc.relevance,"m":conc.mentstr
        }
        return conc.amap[char]              # return the concept attribute value denoted by single letter
        
    def get_General(self,forconcepts):                      # return more geenral concepts than the inputs are based on
        m_general = set()                                   # more general concepts
        if type(forconcepts) is not list:
            forconlist = [forconcepts]
        else: forconlist = forconcepts[:]
        for forcon in forconlist:
            if self.cp[forcon].wmuse==[-1]:                 # an input concept
                m_general.update(self.cp[forcon].general)   # concepts more general than this input may be inhibitors in reasoning
            else:
                for con in self.cp[forcon].wmuse:           # base concepts
                    m_general.update(gl.WM.cp[con].general) # base concepts' generals may become inhibitors
        return m_general

    def based_General(self,new,old):                        # return whether either conmcept is based on more general ones
        #TO DO: check rules as well.
        more_general=0                                      # flag indicating sth more general
        if self.cp[new].wmuse!=[-1] and self.cp[old].wmuse!=[-1]:   # notinputs
            usenew = set(self.cp[new].wmuse)
            useold = set(self.cp[old].wmuse)
            gen_new = self.get_General(new)                 # concepts that are more general than the ones new is based on
            gen_old = self.get_General(old)                 # concepts that are more general than the ones old is based on
            old_isgen = gen_new & useold                    # if not empty, old is based on more general concs than new
            new_isgen = gen_old & usenew
            if len(new_isgen)>0:                            # new is based on more general (if both we return 0)
                if len(old_isgen)==0: more_general=1        # return that new is based on more general
            else:
                if len(old_isgen)>0: more_general=2         # return that old is based on more general
        return more_general
        
    def check_Contradiction(self,sindex,rule,pin,conclist):     # process contradiction before adding the new reasoned concept
        pmatch=0;  new_special=0                            # flag: the concept to be reasoned will be based on more special input
        if self.cp[sindex].p == pin:                        # no contradiction
            pmatch=1                                        # match found
        else:                                               # contradiction found
            try:
                if rule[0] in gl.KB.cp[self.cp[sindex].rule_use[0]].general:   # the new concept's rule is more general than used for old
                    gl.log.add_log(("CONTRADICTION: inhibit reasoning in check_Contra: based on more general rule. Specific rule based old  index=",sindex," general rule:",rule[0]))
                    return 2                                # match found, inhibits reasoning
                if self.cp[sindex].rule_use[0] in gl.KB.cp[rule[0]].general:   # the contradicting old concept used a more general rule
                    gl.log.add_log(("CONTRADICTION: PVALUE OVERRIDE in check_Contra because p was based on general rule. index=",sindex," old p=",self.cp[sindex].p," new p=",pin," used by:",self.cp[sindex].usedby))
                    self.cp[sindex].p=pin                   # override p in old
                    for used in self.cp[sindex].usedby:     # concepts that used this sindex
                        gl.log.add_log(("CONTRADICTION: OVERRIDE TO KNOWN=0 in check_Contra because based on p-overriden concept. index=",used," old p=",self.cp[used].p," overriden concept:",sindex))
                        self.cp[used].known=0               # set known value to unknown
                        
            except: a=0
        if len(conclist)>0:                                 # list of concepts used for the new reasoning
            alluse=set()
            for newuse in conclist:
                alluse.add(newuse)
                alluse.update(self.cp[newuse].same)         # add those concepts same as used concept to all used concepts
            if self.cp[sindex].known>0:
                old_general = self.get_General(sindex)      # get more general concepts than sindex is based on
            general_newconc = alluse & old_general          # set of used concepts that are general to the old concept
            if len(general_newconc)>0:                      # new concept would use input that is more general than the old concept
                gl.log.add_log(("CONTRADICTION: inhibit reasoning in check_Contra: more general input. Specific old index=",sindex," too general input=",general_newconc))
                return 2                                    # found=2 will inhibit reasoning
            new_general = self.get_General(conclist[:])     # concepts more general than the new one is based on
            if self.cp[sindex].wmuse!=[-1]:                 # old concept is reasoned
                if len(set(self.cp[sindex].wmuse) & new_general) > 0:  # we used some more general concepts in old
                    new_special = 1                         # enable such reasoning
        if pmatch==1 and new_special==0:                    # p is matching and new concept is not based on special
            return 1                                        # inhibit rerasoning
        return 0

    def track_Concept(self,coni,message,rule=-1):           # track concept or rule usage for debugging
        ruse = self.cp[coni].rule_use[:]
        reasoned_p = self.cp[coni].p
        if self.name=="WM" and len(ruse)>0 and gl.WM.ci==coni:      # coni has just been reasoned
            if gl.KB.cp[ruse[0]].track==1:                  # rule tracked
                print ("TRACK rule. Reasoning with rule and concepts used:",ruse," ",message," potentially reasoned index",coni)
        if rule!=-1 and gl.KB.cp[rule].track==1:            # tracked rule
            print ("TRACK rule. Reasoning with rule:",rule," ",message," potentially reasoned index",coni)
        if self.cp[coni].track==1:                          # this concept is tracked
            print ("TRACK input concept. ",message," Tracked:",coni," ",gl.WM.cp[coni].mentstr," p=",gl.WM.cp[coni].p," override:",gl.WM.cp[coni].override)
        for basec in self.cp[coni].wmuse:                   # base concepts used for this reasoning
            if basec>0 and self.cp[basec].track==1:         # this base concepts is tracked
                print ("TRACK usage of concept. ",message," Tracked:",basec," ",gl.WM.cp[basec].mentstr," used in concept:",coni," ",gl.WM.cp[coni].mentstr," p=",reasoned_p," wmuse:",gl.WM.cp[coni].wmuse," rule and conc used:",ruse," override:",gl.WM.cp[coni].override)

    def same_Use(self,sindex,conclist):                     # check that the concept to be reasoned is based on something new or not
        olduse = set(self.cp[sindex].wmuse)                 # the matching old concept's wmuse
        newuse = set()
        sameuse = 1                                         # default is that reasoning gets inhibited because nothing new used
        for con in conclist:
            if self.cp[con].wmuse == [-1]: con_use=[con]    # if this is input, use the concept itself
            else: con_use = self.cp[con].wmuse[:]
            if self.cp[con].wmuse == [-2]: con_use=[]    #parent of a reasoned concept
            newuse = newuse | set(con_use)                  # add new eleemnts. full set of used concepts.
    #    if gl.d==1: print ("SAMEUSE newuse",newuse,"olduse",olduse)
        if len(newuse-olduse)>0:                            # something new is used
            if max(newuse) > sindex:                        # more recent input used than the matching old concept
                sameuse=0                                   # significant new usage. Reasoning enabled.
        #if gl.d==1: print ("SAMEUSE sindex",sindex,"olduse",olduse,"newuse",newuse,"SAMEUSE:",sameuse)
        return sameuse
            

    def search_fullmatch(self,pin,rel,parents,rule,samelist,conclist=[]):
        found=0; s=timer()
        not_known=0
        if conclist[0]>0:                                           # conclist is meaningful, in WM
            for basec in conclist:                                      # base concepts used for reasoning
                if self.cp[basec].known==0:                             # one of them  not known
                    not_known=1; found=1 ; foundsave=basec              # return found=1, inhibit reasoning for not known base
        if not_known==0:                                            # all base wmuse concepts are known
            for sindex in range(0,self.ci+1):                       # search for match in entire WM 
                con=self.cp[sindex]
                if con.known>0 and con.relation==rel:   #only known,  match to concepts in this wm
                    if len(con.parent)==len(parents) and (1==1 or con.p==pin):    # p value not checked here but in check_Contra                                        # p value checked currently
                        pari=0; allsame=1                           #allsame will show if all parents are the same
                        while pari<len(con.parent) and allsame==1:  #only check until first different parent found
                            parent1wm=con.parent[pari]
                            if len(parents)>pari:
                                p1=parent1wm; p2=parents[pari]
                                if self.cp[p1].mentstr!=self.cp[p2].mentstr:    # mentalese different
                                    allsame=0
                                if (p2 not in self.cp[p1].same and p1!=p2) :    # for different indices, not recorded as same
                                    allsame=0                       # different parents
                                else:                               # different indices recorded as same
                                    if (len(self.cp[p1].kblink)!=0 and len(self.cp[p2].kblink)!=0):     # we have kblink
                                        if self.cp[p1].kblink != self.cp[p2].kblink:   # according to kblink different meaning 
                                            allsame=0               # different parents
                                                                    #exception for D( , ) relation for mapping
                                    if con.relation==3 and len(parents)==2 and len(con.parent)==2 and parents[0]!=con.parent[0]:
                                        allsame=0                   #direct index comparison
                            else:
                                allsame=0
                            pari+=1
                        if allsame==1:
                            samelist.append(sindex)                 #remember that in sindex the concept matches
                            sameuse = self.same_Use(sindex,conclist[:])   # check whether new concept will use some new base
                            foundnow=self.check_Contradiction(sindex,rule,pin,conclist[:])    # check whether we have contradiction and resolve it
                            if gl.d==2: print ("SEARCH FULL allsame=1","conclist",conclist,"sindex",sindex,"SAMEUSE:",sameuse,"ci",gl.WM.ci,"foundnow",foundnow)
                            if foundnow == 2 or (foundnow==1 and sameuse==1):   # p matching and same base used
                                found=1 ; foundsave=sindex
        if found==1:
            for basec in conclist: self.track_Concept(basec,"Attempted use inhibited in search_fullmatch. Inhibitor conc:"+str(foundsave)+" "+self.cp[foundsave].mentstr+" not known?:"+str(not_known)+" ",rule[0])
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

    def getp_backward(self,swhat):                  # search earlier occurence of swhat and return p
        s=timer()
        sindex=self.cp[swhat].previous              # proceed on branch
        wmfound=0; kback=0
        while sindex>-1 and kback==0:               # do not stop on unknown concept
            if self.rec_match(self.cp[swhat], self.cp[sindex], [swhat,sindex]) == 1:
                kback=self.cp[sindex].known         # the known value of this earlier occurence
                if kback>0: wmfound=sindex          # this is the earlier occurence
            sindex=self.cp[sindex].previous
        gl.args.settimer("concep_906: getp_backward",timer()-s)
        return wmfound                              # return the latest, same concept occurence

    def clone_Values(self,new,fromwm,fromkb):       # clone dimensions onto new, from earlier concept in wm (fromwm) or kb (fromkb)
        if fromkb>0:                                # we have an occurence in KB - we only use this for cloning
            gl.log.add_log(("DIMENSION OVERRIDE during add_concept, on concept:",new," ",self.cp[new].mentstr," earlier KB occurence:",fromkb, " old p,known,c:",self.cp[new].p," ",self.cp[new].known," ",self.cp[new].c," new p,known,c:",gl.KB.cp[fromkb].p," ",gl.KB.cp[fromkb].known," ",gl.KB.cp[fromkb].c))  
            self.cp[new].p = gl.KB.cp[fromkb].p     # p value updated
            self.cp[new].known = gl.KB.cp[fromkb].known     
            self.cp[new].c = gl.KB.cp[fromkb].c     #  value updated
            self.cp[new].relevance = gl.KB.cp[fromkb].relevance
            self.cp[new].reasonuse = gl.KB.cp[fromkb].reasonuse[:]
            self.cp[new].rule_use = gl.KB.cp[fromkb].rule_use[:]
            if gl.KB.cp[fromkb].wmuse!=[-1]:
                self.cp[new].wmuse = gl.KB.cp[fromkb].wmuse[:]
            else: self.cp[new].wmuse = [fromkb]
        if fromwm>0 and fromkb==0:                              
            gl.log.add_log(("DIMENSION OVERRIDE during add_concept, on concept:",new," ",self.cp[new].mentstr," earlier WM occurence:",fromwm, " old p,known,c:",self.cp[new].p," ",self.cp[new].known," ",self.cp[new].c," new p,known,c:",gl.WM.cp[fromwm].p," ",gl.WM.cp[fromwm].known," ",gl.WM.cp[fromwm].c))  
            self.cp[new].p = gl.WM.cp[fromwm].p     # p value updated
            self.cp[new].known = gl.WM.cp[fromwm].known     
            self.cp[new].c = gl.WM.cp[fromwm].c     #  value updated
            self.cp[new].relevance = gl.WM.cp[fromwm].relevance    
            self.cp[new].reasonuse = gl.WM.cp[fromwm].reasonuse[:]
            self.cp[new].rule_use = gl.WM.cp[fromwm].rule_use[:]
            if gl.WM.cp[fromwm].wmuse!=[-1]:
                self.cp[new].wmuse = gl.WM.cp[fromwm].wmuse[:]
            else: self.cp[new].wmuse = [fromwm]
            
    def update_Condip(self):                            # update p value of condition. Uses KB as well.
        pari=0                                          # p value updated on parent of self.ci. self.ci is an IM relation.
        for par in self.cp[self.ci].parent : 
            self.cp[par].p = gl.args.pdef_unknown       #this is after concept is added. So log file is bad.
            if pari==0:                                 # condition in IM
                wmfound = self.getp_backward(par)       # use the p value of earlier occurence of concept
                if wmfound > 0:                         # earlier occurence found
                    self.clone_Values(par,wmfound,0)    # copy dimensions from wmfound to par
                elif par>0 and self.name=="WM" and "%" not in self.cp[par].mentstr:   # no new p found in WM, then search KB
                        condinkb = self.search_KB(par)  # search the condition in KB
                        if condinkb[1]!=[-1]:           # found
                            self.clone_Values(par,0,condinkb[1][0])  # copy dimensions from the same concept found in KB
            pari+=1

    def update_Samecon(self,con):                       # update WM's vs_samestring and concept .same field based on parents and sameness
        ment = self.cp[con].mentstr
        if ment not in self.vs_samestring:
            self.vs_samestring[ment]=set()              # the first time this mentalese occurs
        self.vs_samestring[ment].add(con)               # add this concept to the set of same mentalese
        for scon in self.vs_samestring[ment]:           # all the same mentaleses
            if scon != con:                             # another concept
                match = self.rec_match(self.cp[con],self.cp[scon],[con,scon])    # see whether they match
                if match==1:                                # they match
                    self.cp[con].same.add(scon)             # update .same field
                    self.cp[scon].same.add(con)             # update .same field
                    for oldsame in self.cp[scon].same:      # old concepts that are the same as scon
                        if con!=oldsame:
                            self.cp[con].same.add(oldsame)  # this is also same as con
                            self.cp[oldsame].same.add(con)  # and vice versa
                    

    def update_Same(self,con):                          # update same field based on D relation, con is a D()
        same_g=self.cp[self.cp[con].parent[0]].g        # generality of first parent
        for par in self.cp[con].parent:
            if same_g != self.cp[par].g or self.cp[par].mentstr=="?":   # different g values
                same_g=-1                               # indicate difference
        if same_g != -1:                                # all g the same
            for par1 in self.cp[con].parent:
                for par2 in self.cp[con].parent:
                    if par1!=par2:
                        self.cp[par1].same.add(par2)     # add par2 in the same list of par1 (the cyvcle also adds par1 to par2.same)
                        for oldsame in self.cp[par2].same:  # consider concepts that are same as par2, e.g. older same concepts
                            if par1!=oldsame:
                                self.cp[par1].same.add(oldsame)  # these are now the same as par1
                                self.cp[oldsame].same.add(par1)  # oldsame is also the same now as par1 and par2

    def manage_parents(self,new_rel):                   # complete addition of a new concept thathas parents
        self.cp[self.ci].mentstr = gl.args.rcodeBack[new_rel] + "("  # relation in mentalese
        for par in self.cp[self.ci].parent:
            self.cp[par].child.append(self.ci)
            self.cp[self.ci].mentstr = self.cp[self.ci].mentstr + self.cp[par].mentstr + ","    # add parent mentalese           
        self.cp[self.ci].mentstr = self.cp[self.ci].mentstr[:-1] + ")"
 
    def copy_Rulematch(self,oldcon,newcon):         # copy the field rule_match from old to new concept
        ind1=0
        for rm1 in oldcon.rule_match:           # top level
            if type(rm1) is list:
                ind2=0
                newcon.rule_match.append([])
                nind1=len(newcon.rule_match)-1  # index that is valid in newcon: earlier content must be preserved
                for rm2 in rm1:                 # second level
                    if type(rm2) is list:
                        newcon.rule_match[nind1].append([])
                        for rm3 in rm2:         # third level
                            if type(rm3) is list:   # should never happen
                                gl.log.add_log(("ERROR in copy_Rulematch: more than 3 level deep list. concept=",oldcon.mentstr," rule_match:",oldcon.rule_match))
                            else:
                                newcon.rule_match[nind1][ind2].append(rm3)
                    else:
                        newcon.rule_match[nind1].append(rm2)
                    ind2+=1
            else:
                newcon.rule_match.append(rm1)
            ind1+=1
                    

    def copy_Conc(self,oldwm,newwm,concid):           # copy concept by adding new conc in newwm and copying fields from concid
       # oldwm = gl.VS.wmlist[oldwmid]                   # old wm object
        rel = oldwm.cp[concid].relation                 # old conc relation
        newwm.cp.append(Concept(rel))                   # add concept in newwm, concept list
        newwm.ci = len(newwm.cp)-1
        newwm.cp[newwm.ci].mentstr = oldwm.cp[concid].mentstr[:]   # copy mentalese
        newwm.cp[newwm.ci].p = oldwm.cp[concid].p
        newwm.cp[newwm.ci].c = oldwm.cp[concid].c
        newwm.cp[newwm.ci].g = oldwm.cp[concid].g
        newwm.cp[newwm.ci].cons_avg = oldwm.cp[concid].cons_avg
        newwm.cp[newwm.ci].acts = oldwm.cp[concid].acts
        newwm.cp[newwm.ci].exception = oldwm.cp[concid].exception
        newwm.cp[newwm.ci].known = oldwm.cp[concid].known
        newwm.cp[newwm.ci].relevance = oldwm.cp[concid].relevance
        newwm.cp[newwm.ci].count = oldwm.cp[concid].count
        newwm.cp[newwm.ci].parent = oldwm.cp[concid].parent[:]
        newwm.cp[newwm.ci].kblink = oldwm.cp[concid].kblink[:]
        newwm.cp[newwm.ci].wordlink = oldwm.cp[concid].wordlink[:]
        newwm.cp[newwm.ci].mapto = oldwm.cp[concid].mapto
        newwm.cp[newwm.ci].wmuse = oldwm.cp[concid].wmuse[:]
        newwm.cp[newwm.ci].kb_use = oldwm.cp[concid].kb_use[:]
        newwm.cp[newwm.ci].override = oldwm.cp[concid].override.copy()
        newwm.cp[newwm.ci].reasonuse = oldwm.cp[concid].reasonuse[:]
        newwm.cp[newwm.ci].rule_use = oldwm.cp[concid].rule_use[:]
        newwm.cp[newwm.ci].usedby = oldwm.cp[concid].usedby.copy()
        newwm.cp[newwm.ci].general = oldwm.cp[concid].general.copy()
        newwm.cp[newwm.ci].same = oldwm.cp[concid].same.copy()
        for rs in oldwm.cp[concid].rulestr:
            newwm.cp[newwm.ci].rulestr.append(rs[:])
        newwm.cp[newwm.ci].kb_rules = oldwm.cp[concid].kb_rules[:]
        newwm.cp[newwm.ci].kbrules_upto = oldwm.cp[concid].kbrules_upto
        newwm.cp[newwm.ci].kbrules_filled = oldwm.cp[concid].kbrules_filled
   #VS     newwm.cp[newwm.ci].kbrules_converted = oldwm.cp[concid].kbrules_converted   # may not be used
        newwm.cp[newwm.ci].track = oldwm.cp[concid].track
        newwm.cp[newwm.ci].compared_upto = oldwm.cp[concid].compared_upto
        newwm.cp[newwm.ci].reasoned_with = oldwm.cp[concid].reasoned_with.copy()
        for childi in oldwm.cp[concid].child:                               # copy only valid children
            if childi <= oldwm.last: newwm.cp[newwm.ci].child.append(childi)
        self.copy_Rulematch(oldwm.cp[concid],newwm.cp[newwm.ci])            # copy the rule_match multi-dimension list

    def get_Usedconc(self,latest):                          # return input, or wmuse of input
        wmu = [latest]                                      # if this is input
        if len(gl.WM.cp[latest].wmuse)>0:
            if gl.WM.cp[latest].wmuse!=[-1] and gl.WM.cp[latest].wmuse!=[-2]:
                wmu = gl.WM.cp[latest].wmuse[:]
        return wmu

    def inhibit_Update(self,latest,new):                    # inhibit duplicate dimension update
        inhibit=0
        latest_wmu=self.get_Usedconc(latest)                # earlier occurence used these concs
        new_over = list(gl.WM.cp[new].override)
        if len(latest_wmu)>0 and len(new_over)>0:
            if sorted(latest_wmu)[-1] in new_over:          # the most recent used concept of latest is used in overriding new
                inhibit=1                                   # inhibit dimension override of new, it would be duplicate override
        return inhibit            

    def update_Dimensions(self,latest,new):                 # update p,exception,known,c,cons_avg values for new
        if gl.WM.cp[new].count>1 and gl.WM.cp[new].count<gl.args.avg_lookback:
            div = float(gl.WM.cp[new].count)
        else: div = float(gl.args.avg_lookback)             # how to calculazte average, with maximum lookback
        gl.WM.cp[new].cons_avg = float(gl.WM.cp[latest].cons_avg*(div-1))/div + float(gl.WM.cp[new].c)/div     # calc average consistency
        k1 = gl.WM.cp[latest].known; k2 = gl.WM.cp[new].known
        inhibit_over = self.inhibit_Update(latest,new)      # inhibit duplicate overrides
        # known update:
        if k2>=k1:
            bigk=k2
            p1 = gl.WM.cp[new].p; p2 = gl.WM.cp[latest].p
        else:
            bigk=k1                                             # bigger known value
            p2 = gl.WM.cp[new].p; p1 = gl.WM.cp[latest].p       # p1 is the better known p
        if inhibit_over==0:
            conavg = int(gl.WM.cp[new].cons_avg + 0.5)              # rounded average consistency
            try:
                final_k = gl.args.known_final[bigk][conavg]         # calculate updated known value
                gl.WM.cp[new].known = final_k
            except: gl.log.add_log(("ERROR in update_Dimensions (reason.py). known_final table read failed, indices:",bigk," ",conavg," at concept",new," db=",gl.WM.this))
        # p update:
        if gl.args.upd_pvalue==1 and inhibit_over==0 and k1>0 and k2>0 :
            try:
                kadv = gl.args.k_advan[k1][k2]                  # k advantage
                pfinal = gl.args.pe_final[kadv][p1][p2]         # final p value
                pold = gl.WM.cp[new].p
                gl.WM.cp[new].p = pfinal                        # update p value
                usedc = self.get_Usedconc(latest)               # used concepts of latest
                gl.WM.cp[new].override = gl.WM.cp[new].override | (set(usedc) - set(gl.WM.cp[new].wmuse))   # remember which base concepts were involved in the override
                if pfinal != pold : 
                    gl.log.add_log(("PVALUE OVERRIDE in update_Dimensions, db=",gl.WM.this," on conc:",new," ",gl.WM.cp[new].mentstr," based on old conc:",latest," ",gl.WM.cp[latest].mentstr," original p:",pold," new p:",pfinal," kadv:",kadv," p1 p2:",p1," ",p2," k1 k2:",k1," ",k2))
                    gl.WM.track_Concept(new," Dimensions OVERRIDE. old p="+str(pold)+". Based on earlier occurence:"+str(latest)+".")   # track used concepts
            except: gl.log.add_log(("ERROR in update_Dimensions (reason.py): k_advan table or pe_final table read failed. index k,p:",k1," ",k2," ",p1," ",p2," at concept:",new," db=",gl.WM.this))
         
    def manage_Consistency(self,new):                           # calculate consistency and occurence
        s=timer()
        same_list=sorted(gl.WM.cp[new].same)                    # same concepts
        latest=0
        if gl.WM.cp[new].relation!=1 and gl.WM.cp[new].known>0: # not a word, known
            for old in same_list:                               # all concepts that have same mentalese. TO DO: involve KB.
                if new!=old and gl.WM.cp[old].known>0 and old>gl.WM.cp[new].compared_upto:   # for known concepts, that were not compared yet
                    gl.WM.cp[new].compared_upto=old             # remember where we are with comparison
                    match=0
                    if old in gl.WM.cp[new].same:  match=1      # if old in same list then they match
                    else:
                        match=gl.WM.rec_match(gl.WM.cp[new],gl.WM.cp[old],[new,old])    # concepts compare
                        if match==1: gl.WM.cp[new].same.add(old)   #record in same list
                    if match==1:
                        latest=old                              # latest matching concept
                        index1 = int(gl.WM.cp[new].p)
                        index2 = int(gl.WM.cp[old].p)
                        cons = gl.args.consist[index1][index2]  # read consistency table
                        if cons<gl.WM.cp[new].c:                # consistency is worse than stored
                            gl.WM.cp[new].c=cons                # we store the top inconsistency per concept, since compared_upto
                        if cons>gl.WM.cp[new].c: 
                            if gl.WM.cp[old].relevance == gl.args.rmax and cons==gl.args.cmax-1:     # top relevant and top consistent
                                gl.WM.cp[new].c=gl.args.cmax        # set new top consistent
        else: 
            if len(same_list)>0: latest = same_list[-1]         # for words
            else: latest=0
        if latest>0:                                            # we had some occurence earlier: update counter
            gl.WM.cp[new].count = gl.WM.cp[latest].count+1      # count occurence
            if gl.WM.cp[latest].relation!=1:                    # not a word
                more_general=gl.WM.based_General(new,latest)    # is one of these based on more general concs?
                if more_general==0:                             # nothing more general
                    self.update_Dimensions(latest,new)          # update p etc based on latest and new occurence
                if more_general==1:                             # new is based on more general
                    if gl.WM.cp[new].known>0: gl.log.add_log(("KNOWN OVERRIDE (in manage_Consistency) to zero because old occurence was more special. on new conc:",new," ",gl.WM.cp[new].mentstr," based on old conc:",latest," ",gl.WM.cp[latest].mentstr))
                    gl.WM.cp[new].known=0
                if more_general==2:                             # new based on more special
                    if gl.WM.cp[latest].known>0: gl.log.add_log(("KNOWN OVERRIDE (in manage_Consistency) to zero because new occurence is more special. on old conc:",latest," ",gl.WM.cp[latest].mentstr," based on new conc:",new," ",gl.WM.cp[new].mentstr))
                    gl.WM.cp[latest].known=0
        gl.args.settimer("reason_020: manage_Consistency",timer()-s)

    def set_Samegen(self,inwhat,gene):              # gene concept is also general to those same as inwhat
        for sconi in self.cp[inwhat].same:          # same concepts as inwhat
            con=self.cp[sconi]                      # set 3 sources of general
            con.general.add(gene)          
            con.general.update(self.cp[gene].same)            
            con.general.update(self.cp[gene].general)  
            
    def vs_set_General(self,newi):          # investigate if latest input concept involves a generality relation
        s=timer()
        contralist=[]
        con=self.cp[newi]                       # current concept
        old=newi; special=0
        if con.relation==5:                     # F relation
            if len(con.parent)>1:
                con.general.add(con.parent[0])                      # x is more general than F(x,y)
                con.general.update(self.cp[con.parent[0]].same)     # concepts same to x are also general to F(x,y)
                con.general.update(self.cp[con.parent[0]].general)  # concepts general to x are also general to F(x,y)
                self.set_Samegen(newi,con.parent[0])                # in concepts same as newi set general as well
        if con.relation==4 and con.p==gl.args.pmax and con.known>=gl.args.kmax/2:  # C relation, p=pmax, known
            if len(con.parent)>1:
                cla=1
                special = con.parent[0]             # remember: C(x,y) and x is special    
                while cla<len(con.parent):          # C(x,y,z) y and z are more general than x
                    self.cp[con.parent[0]].general.add(con.parent[cla])
                    self.cp[con.parent[0]].general.update(self.cp[con.parent[cla]].same)
                    self.cp[con.parent[0]].general.update(self.cp[con.parent[cla]].general)
                    self.set_Samegen(con.parent[0],con.parent[cla])     # in concepts same as con.pernt[0] set general as well
                    cla+=1
        while self.cp[old].previous!=-1:        # entire WM on current branch backward
            old=old-1                           # next item on branch
            genword = self.get_Generalword([newi,old])  # set general field based on same field
            if special>0 and special in self.cp[old].general:           # we had a special recorded, and now this "old" has special as general
                self.cp[old].general.update(self.cp[special].general)   # all that are general to special are general to old
            match = self.rec_match(con,self.cp[old],[newi,old])
            if match==1:
                self.cp[newi].general.update(self.cp[old].general)      # if concept is the same make general list the same
                self.cp[newi].same.add(old)     # same gets extended
                self.cp[old].same.add(newi)     # same gets extended
                if self.cp[newi].p!=self.cp[old].p:   # we seem to have contradiction
                    if self.cp[newi].p!=gl.args.pmax/2 and self.cp[old].p!=gl.args.pmax/2:  #contradiction
                        contralist.append([newi,old])   # collect contradictions for override
            if match==2:
                self.cp[old].general.update(self.cp[newi].general)      # newi is more general, generality inherited to old
                self.cp[old].general.update(self.cp[newi].same)         # general gets extended with same as old
            if match==3:
                self.cp[newi].general.update(self.cp[old].general)      # old is more general, generality inherited to newi
                self.cp[newi].general.update(self.cp[old].same)         # general gets extended with same as mewi
            #if gl.d==1 and newi<10: print ("SETGEN 2 db=",self.this,"con=",newi,"old=",old,"general=",self.cp[newi].general)
        #if gl.d==1 and newi<10: print ("SETGEN 4 db=",self.this,"con=",newi,"general=",self.cp[newi].general)
        self.spread_General(newi,self.cp[newi].general)    # spread the .general property to concepts in reasonuse
        self.override_Old(contralist)              # override p in contraditions found
        gl.args.settimer("concep_810: set_General",timer()-s)
                           
    def add_concept(self, new_p, new_rel, new_parents,kbl=[],gvalue=None,isquestion=0):        #add new concept to WM or KB. parents argument is list
        s=timer()
        self.cp.append(Concept(new_rel))                        #concept added
        self.ci = len(self.cp) - 1                              #current index
        self.thispara.append(self.ci)                           #note concept is in current paragraph
        self.cp[self.ci].previous=self.ci-1                     #set previous
        if self.ci>0:
            if self.cp[self.ci-1].next==[]:
                self.cp[self.ci-1].next.append(self.ci)         # set next                
        self.cp[self.ci].p = int(new_p)                         # set p value
        if isquestion==1: self.cp[self.ci].known=0              # set known=0 for questions
        self.cp[self.ci].track = 0                              # set default tracking to NO        
        self.cp[self.ci].add_parents(new_parents)               # set parents
        self.cp[self.ci].kblink[:]=kbl[:]                       # set link to KB
        if kbl==[] and self.name=="KB" and new_rel==1:          # word addition in KB
            self.cp[self.ci].kblink.append(self.ci)             # add own index in KB
        if (new_rel != gl.args.rcode["W"]):                     # if this is not a word
            self.manage_parents(new_rel)                        # add parents, edit mentalese str            
        else:                                                   #this is a word
            if (len(kbl)>0):                                    #set word link if we have KB link
                self.cp[self.ci].wordlink.append(gl.KB.cp[kbl[0]].wordlink[0])      # we have a single word link
                self.cp[self.ci].mentstr = gl.KB.cp[kbl[0]].mentstr[:]
            if gvalue!=None: self.cp[self.ci].g=gvalue          #explicit generality provided
        if new_rel==3 and len(self.cp[self.ci].parent)>1 and isquestion==0: # D relation with 2+ parents
            self.update_Same(self.ci)                           # update same field based on D()
        if self.name=="WM" and isquestion==0:
            self.update_Samecon(self.ci)                        # update same field based on parents, and vs_samestring
            self.manage_Consistency(self.ci)                    # update consistency field, override known value.
            self.vs_set_General(self.ci)                        # set .general field
        #if gl.d==1 and self.name!="KB":print ("ADD CON ci",self.ci,self.cp[self.ci].mentstr,self.cp[self.ci].same)
        if new_rel == 13 and self.name=="WM" :                  # IM relation
            self.update_Condip()                                # update p value of condition if needed
        if new_rel != 1:                                        # not a word
            gl.act.vs_activate_Conc(self.ci,self)               # activate this concept just added (WM)
        if self.name=="WM" and "%" not in self.cp[self.ci].mentstr:  # rules should not be activated based on %1
            kbpos = self.search_KB(self.ci)                     # search this WM concept in KB and set kblink
            gl.act.activate_inKB(self,self.ci,1)                # activate KB concepts based on occurence in WM (word etc) beyond relevance limit, in round=1
        dbstr=" db="+str(self.this)
        gl.log.add_log((self.name,dbstr," add_concept index=",self.ci," p=",self.cp[self.ci].p," rel=",new_rel," parents=",new_parents," wordlink=",self.cp[self.ci].wordlink," mentstr=",self.cp[self.ci].mentstr," general=",self.cp[self.ci].general))      #content to be logged is tuple (( ))
        gl.args.settimer("concep_800: add_concept",timer()-s)
        return self.ci
 
    def zero_Known(self,coni):                              # known value set to zero, and deactivate
        self.cp[coni].known=0                               # set known to zero
        self.cp[coni].acts=0                                # deactivate concept
        self.activ.discard(coni)                            # remove coni from activated set
        self.activ_new.discard(coni)                        # remove coni from activated set
                        
    def get_Wordinment(self,ment):                          # return words from any mentalese
        ment=ment.strip()
        wordlist=[]; thisword=""
        termination = [",",")",".g=",".p=",".r=",".c="]     # valid terminations of words
        beginning=["(",","]                                 # valid beginnings: must be a singe character
        pos=0
        while pos<len(ment):
            if ment[pos] in beginning:                      # word may begin
                done=0; gword=""
                while done==0:                              # build current word
                    pos+=1                                  # next position in word
                    thisword=thisword+ment[pos]             # add character to current word
                    for term in termination:
                        if term in thisword:                # we added a full termination
                            done=1                          # word ended
                            if term == ".g=":               # g value must be transferred
                                pos2=pos
                                while ment[pos2]!="," and ment[pos2]!=")":  # to the end of word with g value
                                    pos2+=1
                                gword = ment[pos-2:pos2]    # add .g=0 part
                            thisword = thisword[0:len(thisword)-len(term)]  # remove termination
                    if done==0 and "(" in thisword:         # not a word but compound concept like A( or AND(
                        done=1; thisword=""                 # no word
                if len(thisword)>0:
                    wordlist.append([thisword.strip(),gword])   # store result
                thisword=""
            else: pos+=1                                    #not a beginning: move one position
        return wordlist
            
    def remove_concept(self,allwm=0):                       # allwm==1 means the entire WM is removed (because moved to KB)
        gl.log.add_log((self.name," remove concept index=",self.ci))
        remcon = self.cp[self.ci]                           # to be removed
        if (self.ci>-1):
            ment = self.cp[self.ci].mentstr[:]
            #if gl.d==1: print ("REMOVE ci",self.ci,ment,self.cp[self.ci].same,"allwm",allwm)
            self.cp.pop()
            self.thispara.pop()                             # remove from list of this paragraph
            if allwm==0:                                    # just one concept remopved, not teh entire WM
                for old in range (1,self.ci):
                    if self.ci in self.cp[old].reasonuse:
                        self.cp[old].reasonuse.remove(self.ci)    # remove the concept to be deleted from the general concepts
                    self.cp[old].general.discard(self.ci)    # remove the concept to be deleted from the general concepts
                    self.cp[old].usedby.discard(self.ci)
                    self.cp[old].same.discard(self.ci)
                    self.cp[old].reasoned_with.discard(self.ci)
            if self.name=="WM":
                self.activ.discard(self.ci)                 # remove concept from activated list
                self.activ_new.discard(self.ci)             # remove concept from activated list
                if ment in self.vs_samestring:              # questions are not loaded here so we need this if
                    self.vs_samestring[ment].discard(self.ci)   # remove from vs_samestring
            self.ci=self.ci-1
        return self.ci

    def get_branch_concepts(self):             #returns the id list of concepts on branch (inclusive)
        previous_concepts=[]
        curri=self.ci
        while curri != -1:
            previous_concepts.append(curri)
            curri = curri-1
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
                        gl.log.add_log(("PVALUE OVERRIDE in reverse_Drel. overridden=",new," ",self.cp[new].mentstr," based on:",old,"new p=",self.cp[new].p))
                    if self.cp[old].p==gl.args.pmax/2:                  #old needs update
                        self.cp[old].p=self.cp[new].p                   #old updated
                        gl.log.add_log(("PVALUE OVERRIDE in reverse_Drel. overridden=",old," ",self.cp[old].mentstr," based on:",new,"new p=",self.cp[old].p))
                        
    def vs_search_Versions(self,qcount):                            # search answer in versions separately
        found=[]
        for wmi in gl.VS.wmliv:                                     # all living wm versions
            sconindex=0
            db = gl.VS.wmliv[wmi]
            swhat = db.cp[db.last_question]                         # the question index must be the stored in last_question
            if gl.d==7:print("SEARCH VS 1 db=",db.this,"last quest=",db.last_question,swhat.mentstr)
            db.rec_set_undefined_parents(db.last_question)          #sets -1 parents instead of ? character
            db.find_undefined_parents(db.last_question,qcount)      #recursive search for -1. qcount gets updated. used in answer_question.

            for scon in db.cp:                                      # all concepts in this wm
                if scon.relation==3 and swhat.relation==3 :         # two D relations: replace parent 0 with 1
                    if len(scon.parent) == 2 and len(swhat.parent)==2:
                        needtoimplement=1
                        #self.reverse_Drel(swhatindex,thisbr[sindex]) # reverse D() and override p
                if db.rec_match(swhat,scon, [db.last_question,sconindex]) == 1:    # identical concept
                    found.append([db.this, sconindex])                  #  add to found list, noting the branch too
                sconindex+=1
        return found

    def select_Relevant(self,wmpos):        #select all branches in which we have wmpos
        relevant=[]
        for br in gl.WM.branch:
            thisbr=self.get_previous_concepts(br)
            if wmpos in thisbr: relevant.append(br)
        if gl.WM.branch==[]:
            relevant=[gl.WM.ci]
        return relevant                     #this is empty list if branch of wmpos was killed earlier

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
            
    def get_Generalword(self,wmind):                # which word is more general
        w0g = gl.WM.cp[wmind[0]].general
        w1g = gl.WM.cp[wmind[1]].general
        w0s = gl.WM.cp[wmind[0]].same
        w1s = gl.WM.cp[wmind[1]].same
        w0gen = w0g & w1s                           # cocnepts more general than inwhat and same as what1
        w1gen = w1g & w0s
        if len(w0gen)>0:                            # wmind[0] more general than wmind[1]
            if len(w1gen)==0:
                gl.WM.cp[wmind[0]].general.add(wmind[1])
                return 3
        if len(w1gen)>0:                            # wmind[1] more general than wmind[0
            if len(w0gen)==0:
                gl.WM.cp[wmind[1]].general.add(wmind[0])
                return 2
        return 0

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
                rvalu = self.isword_Special(what1,inwhat)                    # see whether %1 and specific word are given
                return rvalu
        
        if len(what1.parent) != len(inwhat.parent):
            if gl.d==2: print ("NO MATCH 2")
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
            if pm==0:
                if gl.d==2: print ("NO MATCH 3 p1 p2:",p1,p2)                
                return 0                                                  # if parent concept does not match -> no match
            if pm == 2:
                if self.name=="WM" and not "%" in self.cp[p1].mentstr:     # only in WM, should not be a rule
                    self.cp[p2].general.add(p1)             # record general relation for parent
                if match == 3: return 0                 # cross special
            if pm == 3:
                if self.name=="WM" and not "%" in self.cp[p2].mentstr:     # only in WM, should not be a rule
                    self.cp[p1].general.add(p2)             # record general relation
                if match==2: return 0                   # cross special
            if pm>1 and match==1: match=pm              # special 2 or 3
        if match==2 and len(wmindex)==2 : inwhat.general.add(wmindex[0])    # remember that what1 is general of inwhat
        if match==3 and len(wmindex)==2: what1.general.add(wmindex[1])      # remember that inwhat is general of what1
        gl.args.settimer("concep_901: rec_match",timer()-s)    
        return match

    def get_child(self,rel,parents=[]):                 # search concept as child of parent
        found=-1
        if parents[0]==-1:  return -1                   # if parent not known, return not found 
        for child in self.cp[parents[0]].child:         # in children of the first parent
            if (self.cp[child].relation==rel):          # relation must match
                if (self.cp[child].parent==parents):    # parents must match
                    found=child
        return found

    def visit_db(self,db,curri,visitmap,nextp=0):       #demo a recursive walk that is not jumping over identical items
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk over parents of same level
            self.visit_db(db,db.cp[curri].parent[nextp],visitmap,0)             # one level down
            nextp=nextp+1
        visitmap.append([curri,db.cp[curri].mentstr])       # actual data manipulation
        return
        
    def visit_KBlinks(self,db,curri,kblinklist,nextp=0):       #demo a recursive walk that is not jumping over identical items
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk over parents of same level
            self.visit_KBlinks(db,db.cp[curri].parent[nextp],kblinklist,0)           # one level down
            nextp=nextp+1
        if db.cp[curri].kblink!=[]:
            if db.cp[curri].kblink[0] not in kblinklist:
                kblinklist.append(db.cp[curri].kblink[0])       # collect kblinks
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
                    gl.KB.cp[kbl].track = self.cp[curri].track  # copy track property
                self.cp[curri].kblink.append(kbl)   # set KB link in WM
        return curri

    def check_Crel(self,curr):                      # check if there is a C-relation for curr in KB or in this WM
        kbi = self.cp[curr].kblink[0]
        wmapto = -1
        print ("CHECK:",kbi,"children:",gl.KB.cp[kbi].child)
        for child in gl.KB.cp[kbi].child:
            if gl.KB.cp[child].relation == 4 and gl.KB.cp[child].known>0: # a C relation
                if len(gl.KB.cp[child].parent) == 2:        # C(x,y)
                    if gl.KB.cp[child].parent[0] == kbi:    # C(kbi , y)
                        wmapto = curr
        for wmcon in self.thispara:                         # now search C() in WM, this paragraph.
            if self.cp[wmcon].relation==4 and self.cp[wmcon].known>0:   # a C relation
                if len(self.cp[wmcon].parent) == 2:         # C(x,y)
                    if self.cp[wmcon].parent[0] in self.cp[curr].same:    # C(curr , y)
                        wmapto = curr                       
        return wmapto

    def populate_KBlink(self,coni):             # populate the KBlink of coni if parents are in KB (and kblink is filled)
        orig = self.cp[coni]
        if orig.kblink!=[]: return                              # kblink was already populated
        if orig.parent==[]: return
        if self.cp[orig.parent[0]].kblink == []: return         # parent should have kblink
        parentinkb = self.cp[orig.parent[0]].kblink[0]
        for childkb in gl.KB.cp[parentinkb].child:              # all children of this parent
            if gl.KB.cp[childkb].relation == orig.relation:     # relation match
                allmatch=1
                for pix in range(0,len(gl.KB.cp[childkb].parent)):
                    if self.cp[orig.parent[pix]].kblink == []: allmatch=0    # no match
                    else:
                        if self.cp[orig.parent[pix]].kblink[0] != gl.KB.cp[childkb].parent[pix]: allmatch = 0   # no match
                if allmatch==1:                                 # coni found in KB
                    orig.kblink.append(childkb)                 # kblink filled in
                    # no return after first match

    def search_KB(self,curri,lasti=-2,found=[]):         # search concept in KB. Concept is in WM on curri. Returns KB index.
        while (len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp=self.cp[curri].parent.index(lasti)+1
            except:
                lasti=-2        # enter lower level
                nextp=0
            lasti=self.search_KB(self.cp[curri].parent[nextp],lasti,found)[0]
        # SEARCH ACTION to follow:
        if self.name=="WM":                                             # copy from WM only
            if len(self.cp[curri].kblink)==0 or self.cp[curri].kblink[0]==-1:   # not yet linked to KB (but might be there)
                plist=[]                                                # holds parent indices valid in KB
                for pari in self.cp[curri].parent:                      # parents valid in WM
                    if len(self.cp[pari].kblink)==0: plist.append(-1)
                    else: plist.append(self.cp[pari].kblink[0])               # append parent index valid in KB
                kbl=gl.KB.get_child(self.cp[curri].relation,plist)      # search concept in KB as child of parent
                if kbl!=-1: self.cp[curri].kblink=[kbl]                 # set KB link in WM, this SHOULD NOT  be -1
            else: kbl = self.cp[curri].kblink[0]                        # kblink already had the link to KB
            if kbl not in found: found=[kbl]                        # kbl is -1 if not found among children. 
        return [curri,found]

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
        moved=0
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
                gl.WM.remove_concept()          # remove rule from WM
                moved=1                         # note something was moved
        return moved
        

    def move_relevant(self, starti):                # if this is top relevant knowledge, move it to KB
        if (gl.WM.cp[gl.WM.ci].relevance>=gl.args.rmove):    #r>=rmove limit, for example r=3 or 4
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
        for pari in self.cp[childi].parent:
            for wi in self.cp[pari].wordlink:
                if (gl.WL.wcp[wi].word=="?"):           # replace ? word with parent=-1
                    self.cp[childi].parent[paridx]=-1
            self.rec_set_undefined_parents(pari)
            paridx=paridx+1

    def find_undefined_parents(self,curri,qc,lasti=-2): # recursive search for ? parent. Call without lasti.
        while (curri>-1 and len(self.cp[curri].parent)>0 and lasti!=self.cp[curri].parent[-1]):
            try: nextp = self.cp[curri].parent.index(lasti)+1
            except: lasti=-2; nextp=0
            lasti = self.find_undefined_parents(self.cp[curri].parent[nextp],qc, lasti)
        if curri==-1: qc[0]=qc[0]+1                 #qc[0] is the counter for ? parents which have -1 value
        return curri                                #qc[0] is also kept as it is transferred by reference

    def get_Common(self,visitq,pwm):                # get common part of parents' matches in KB
        doneparent=0                                # how many parents of pwm are present in visitq
        finalkb=set()
        for vitem in visitq:
            if pwm==vitem[0]: doneparent+=1         # a completed parent found
        if doneparent == len(self.cp[pwm].parent):                  # WM fixed. we have all parents done in visitq
            parentcount=0
            for vitem in visitq:
                if pwm==vitem[0]:
                    parentcount+=1
                    if parentcount==1: finalkb=set(vitem[2])        # initialize finalkb with the first set of KB matches
                    else:
                        if list(vitem[2])==[-1]:                    # -1 parent means any concept will match
                            finalkb = finalkb                       # no change to finalkb
                        else:
                            if finalkb == set([-1]): finalkb = set(vitem[2])   # first parent was -1, initialize finalkb
                            else: finalkb = finalkb & set(vitem[2])  # take the common part of matches in KB

        wm_ment = self.cp[pwm].mentstr                     # we need to check relation match and parent positions
        if "?" in wm_ment:                                  # this is a A(Joe,?) type of question
            wm_ment = wm_ment[:wm_ment.index("?")]          # we only take the mentalese portion left to the ?
        outkb = set()
        for kbcon in finalkb:                               # this is to check the match of relations and parent positions
            if self.cp[pwm].relation == gl.KB.cp[kbcon].relation and wm_ment in gl.KB.cp[kbcon].mentstr:   # menstr string is for position
                outkb.add(kbcon)
        return outkb

    def all_Children(self,visitq,pwm):                  # get children of a KB concept set
        allch = set()                                   # holds the children
        finalkb = self.get_Common(visitq,pwm)           # get the common part of parents' matches
        if len(finalkb)>0:
            for kbconc in finalkb:
                allch.update(set(gl.KB.cp[kbconc].child))   # add children of kbconc to the set of all children
        return allch

    def update_Visitq(self,visitq,pwm,wmpar,kbchild):   # update inventory in visitq
        if pwm>0:
            dupl=0                                      # check duplication
            for vitem in visitq:
                if pwm==vitem[0] and wmpar==vitem[1]: dupl=1    # would be duplication
            if dupl==0: visitq.append([pwm,wmpar,kbchild])      # update if no duplication

    def pattern_KB(self,db,top,curri,visitq,nextp=0,pwm=0):     # search top (being in db) in KB, match A(Joe,?) type of patterns
        # top in WM is the concept to search for
        # curri is the current portion of top that is being visited
        if db.name=="WM":
            while curri>0 and len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent):  # walk over parents of same level
                rel=db.cp[curri].relation
                kbmatch = self.pattern_KB(db,top,db.cp[curri].parent[nextp],visitq,nextp=0,pwm=curri)   # one level down
                nextp = nextp + 1

            if curri==-1: crel=1
            else: crel = db.cp[curri].relation  # WM fixed
            if crel == 1:                                       # word or curri==-1
                for wmpar in db.cp[pwm].parent:
                    if wmpar != -1:
                        if db.cp[wmpar].relation==1:            # parent is word
                            kbchild = gl.KB.cp[db.cp[wmpar].kblink[0]].child   # WM fixed all children of word in KB
                        else:
                            kbchild = self.pattern_KB(db,top,wmpar,visitq)      # wmpar parent's children is being searched in KB
                        self.update_Visitq(visitq,pwm,wmpar,kbchild)
                    else:
                        self.update_Visitq(visitq,pwm,wmpar,[-1])           # mark this parent with -1, all will match
                finalch = self.all_Children(visitq,pwm)                     # take the children of the matching common final KB concepts
                for wmchild in db.cp[pwm].child:                            # WM fixed children of pwm, that have now potential matches to pwm
                    self.update_Visitq(visitq,wmchild,pwm,list(finalch))    # add potential matches of pwm to visitq
                return finalch
            if curri == top:                                                # we are back to the top level
                kbanswer = self.get_Common(visitq,top)                      # now get the final match in KB
                if len(kbanswer)>0:
                    return list(kbanswer)                                   # final asnwer list
            return []
                

    def answer_question(self,starti):          #answer a question now stored in WM
        s=timer()
        answerlist=[]                           
        qcount=[0]                                  #counter for ? parents
        answers = gl.WM.vs_search_Versions(qcount)  # search for answers in all versions  
        visitq=[]                                   # this will hold temporary results in KB search
        for wmi in gl.VS.wmliv:                     # living wms
            db1 = gl.VS.wmlist[wmi]                 # latest living wm in db1
        kbanswer = db1.pattern_KB(db1,db1.last_question,db1.last_question,visitq)   # get answer list from kb
        gl.args.settimer("concep_101: pattern_KB",timer()-s)
        awbrlist=[]                                 # here we note if we have answer on this branch
        for aw in answers:
            answerlist.append(aw)
            awbrlist.append(aw[0])
        answeryes=0
        for anw in answerlist:
            db=gl.VS.wmlist[anw[0]]                 # wm version of the answer
            if anw[0]>-1 and db.cp[anw[1]].wmuse!=[-2]:   # an answer not parent of reasoned
                ament=db.cp[anw[1]].mentstr         # answer mentalese
                if ",?" not in ament and "?," not in ament and "(?)" not in ament:  # not a A(Joe,?) type of question
                    answeryes+=1                    #remember we have answer, count them
        if qcount[0]==0:                            #question like Z(a,b)?
            if answeryes==0: answerlist.append([self.this,self.last_question]) # self.this=wm id !!  question added as answer
        if answeryes>1 :
            try: answerlist.remove([self.this,self.last_question])  # remove the question
            except: a=0
        for anw in answerlist[:]:                   # iterate on copy because we remove from answerlist
            db = gl.VS.wmlist[anw[0]]               # the WM in which we have the answer
            ament=db.cp[anw[1]].mentstr
            if db.cp[anw[1]].wmuse==[-2] or ",?" in ament or "?," in ament or "(?)" in ament:   # remove wmuse==-2 and X(?,y) concepts
                answerlist.remove(anw)
            if len(answerlist)>1 and db.cp[anw[1]].known==0 and anw in answerlist:   # remove known=0 answers
                answerlist.remove(anw)
        for kbaw in kbanswer:                       # answers we found in KB
            if "%" not in gl.KB.cp[kbaw].mentstr:   # not a rule
                answerlist.append([-1,kbaw])         # append kb answer, -1 means it is in KB  (does not work currently??)
        gl.args.settimer("concep_905: answer_question",timer()-s)
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


    def override_Parent(self, isq, wordpos):        # perform default mapping  for g=0 concepts
        overparent = wordpos                        # wordpos is the original parent, initially we have no override
        thisbr = self.get_branch_concepts()         # list of all concepts
                                                    # question argument override deleted
        if overparent == wordpos and gl.WM.cp[wordpos].g==gl.args.gmin:   # not override but g=0. does not need to be question.
            maprule=self.get_Maprules(wordpos)      # is this to be mapped?
            if maprule==[]:                         # not mapped
                for con in thisbr:                  # backward on branch
                    if con in self.paragraph: break   # stop if paragraph border exceeded
                    if gl.WM.cp[con].g==gl.args.gmin and gl.WM.cp[con].mentstr==gl.WM.cp[wordpos].mentstr:    # TO DO is this general?
                        overparent = con            # override parent, repeatedly up to the first occurence in paragraph
        return overparent

    def override_Old(self,contralist):              # override old p if new input is more special
        for contraitem in contralist:               # contradictions
            newi=contraitem[0]; old=contraitem[1]
            genset=set()
            news=[newi]
            if self.cp[newi].wmuse!=[] and self.cp[newi].wmuse!=[-1]:
                news=self.cp[newi].wmuse[:]         # take the original inputs
            for ncon in news:
                for gen in self.cp[ncon].general:       # collect general items, including same items to general ones
                    genset.add(gen)
                    genset.update(self.cp[gen].same)
            gen_used=(set(self.cp[old].reasonuse) | set(self.cp[old].wmuse)) & genset   # general items that were used to reason old
            if len(gen_used)>0:                     # any used: p needs override
                gl.log.add_log(("CONTRADICTION: KNOWN=0 OVERRIDE from set_General: old p was based on more general input. index=",old," old p=",self.cp[old].p," new index=",newi," new p=",self.cp[newi].p))
                self.cp[old].known = 0              # override known
                for used in self.cp[old].usedby:    # reasoned concepts that use this old
                    gl.log.add_log(("CONTRADICTION: PVALUE and KNOWN OVERRID from set_General: make concept unknown. This concept used a too general input. index=",used," old p=",self.cp[used].p," contradicting concept:",old))
                    self.cp[used].p=gl.args.pmax/2  # set this concept to unknown
                    self.cp[used].known=0           # set this concept unknown

    def spread_General(self,thiscon,gener):         # spread .general to anchestor concepts in reasonuse
        ancestor = self.cp[thiscon].reasonuse
        if ancestor!=[]:                            # not the original wmuse
            if ancestor[0] not in gl.args.nospread_general:   # spreading not inhibited
                for ancesti in range(1,len(ancestor)):
                    self.spread_General(ancestor[ancesti],gener)    # recursive call one level deeper
        else:                                       # original wmuse
            nowuse = self.cp[thiscon].wmuse
            if nowuse !=[] and nowuse!=[-1] and nowuse!=[-2]:    # parent if if relation with original wmuse filled in
                self.spread_General(nowuse[0],gener)   # recursive call one level deeper, this can only be 1 element
            else:
                self.cp[thiscon].general.update(gener)  # update .general on wmuse concept

    def copydata_KB(self,concid,newconid):           # copy concept fields from WM to the KB copy of the concept
        newwm = gl.KB                                       # the new database is KB
        oldwm = self
        newcon = newwm.cp[newconid]                         # concept in KB
        newcon.c = oldwm.cp[concid].c
        newcon.exception = oldwm.cp[concid].exception
        #copies:
        newcon.wordlink = oldwm.cp[concid].wordlink[:]
        for rs in oldwm.cp[concid].rulestr:
            newcon.rulestr.append(rs[:])
        newcon.kb_rules = oldwm.cp[concid].kb_rules[:]
        newcon.kbrules_upto = oldwm.cp[concid].kbrules_upto
        newcon.kbrules_filled = oldwm.cp[concid].kbrules_filled  
        newcon.rule_use = oldwm.cp[concid].rule_use[:]          # info from previous paragraph goes lost  
        newcon.kb_use = oldwm.cp[concid].kb_use[:]          
        # the fields below hold WM indices, these need be transformed in transform_kb:
        self.copy_Rulematch(oldwm.cp[concid],newcon)            # rule_match info from previous paragraph is not forgotten
        newcon.wmuse = oldwm.cp[concid].wmuse[:]                # wmuse from previous paragraph goes lost
        newcon.reasonuse = oldwm.cp[concid].reasonuse[:]        # reasonuse from previous paragraph goes lost
        return

    def transform_Rulematch(self,wm_tokb):          # copy the field rule_match from old to new concept
        trans_done = set()
        for wmoldi in wm_tokb:                      # all old wm indices that were moved to KB
            if wm_tokb[wmoldi] not in trans_done and len(self.cp[wmoldi].rule_match)>0:
                kbcon = gl.KB.cp[wm_tokb[wmoldi]]       # the concept in KB
                wmcon = self.cp[wmoldi]                 # the concept in WM, before removing
                ind1=0; oind1=0
                while ind1<len(kbcon.rule_match):            # top level  (- we look in wmcon because that is new)
                    rm1=kbcon.rule_match[ind1]
                    if len(wmcon.rule_match)>oind1 and rm1==wmcon.rule_match[oind1]:
                        if type(rm1) is list:  # old rile_match content in KB is over, this is teh first new one
                            ind2=0
                            for rm2 in rm1:                 # second level
                                if type(rm2) is list:
                                    ind3=0
                                    for rm3 in rm2:         # third level                                
                                        if type(rm3) is list:   # should never happen
                                            gl.log.add_log(("ERROR in copy_Rulematch: more than 3 level deep list. concept=",kbcon.mentstr," rule_match:",kbcon.rule_match))
                                        else:
                                            kbcon.rule_match[ind1][ind2][ind3]=wm_tokb[rm3]   # transform the value to that valid in KB
                                            if kbcon.rule_match[ind1] in kbcon.rule_match[:ind1]: 
                                                del kbcon.rule_match[ind1]   # remove duplicate
                                                ind1-=1
                                        ind3+=1
                                else:
                                    kbcon.rule_match[ind1][ind]=wm_tokb[rm2]
                            if rm1==[]: 
                                del kbcon.rule_match[ind1]
                                ind1-=1
                            ind2+=1
                        else:
                            kbcon.rule_match[ind1]=wm_tokb[rm1]
                        oind1+=1
                    ind1+=1
                trans_done.add(wm_tokb[wmoldi])     # remember transformation is done for this KB item
                
    def transform_List(self,trlist,wm_tokb):        # transform list in kbcon to values valid in KB
        nexti = 0
        while nexti < len(trlist):              # over list
            oldvalue=trlist[nexti]              # this was valid in WM
            if oldvalue>0:                      # 0 and -1 and -2 have special meanings
                newvalue = wm_tokb[oldvalue]    # set the new concept index, that is valid in KB, based on the transformation mapping
            else: newvalue=oldvalue
            if newvalue in trlist[:nexti]:      # this concept is already in list
                del trlist[nexti]               # remove duplicate element, list gets shorter, keep nexti value
            else: 
                trlist[nexti] = newvalue        # replace old value with new value that is valid in KB 
                nexti+=1                        # next in list

    def copy_Set(self,kbi,trset,oldset,wm_tokb,kbsign=0):      # transform a set in KB to valid KB concepts
        for oldvalue in oldset:                 # all values
            if oldvalue>1 and wm_tokb[oldvalue] != kbi:  # the new value will not be the KB concept itself
                trset.add(wm_tokb[oldvalue])    # add new value that is valid in KB. dummy concept on 1 needs be avoided 
            if oldvalue<0 and kbsign==1:        # kbsign shows that a negatiove value means an index in KB !!!! (due to reasoning with KB)
                trset.add(-oldvalue)            # add the positive signed oldvalue itself
        
    def transform_KB(self,wm_tokb):             # transform fields in the concepts that have just been copied to KB as part of paragraph 
                                                # this function transforms indices that were valid in WM to indices in KB
        self.transform_Rulematch(wm_tokb)       # transform the field rule_match
        trans_done=set()
        for wmoldi in wm_tokb:                  # all old wm indices that were moved to KB
            wmcon = self.cp[wmoldi]
            if wm_tokb[wmoldi] not in trans_done:               # transformation not yet done
                kbcon = gl.KB.cp[wm_tokb[wmoldi]]               # the concept in KB
                self.transform_List(kbcon.wmuse,wm_tokb)        # transform the wmuse list
                self.transform_List(kbcon.reasonuse,wm_tokb)    # transform the reasonuse list
                self.copy_Set(wm_tokb[wmoldi],kbcon.reasoned_with,wmcon.reasoned_with,wm_tokb,kbsign=1) # copy field
                self.copy_Set(wm_tokb[wmoldi],kbcon.usedby,wmcon.usedby,wm_tokb)    # copy field
                self.copy_Set(wm_tokb[wmoldi],kbcon.same,wmcon.same,wm_tokb)        # copy field
                self.copy_Set(wm_tokb[wmoldi],kbcon.general,wmcon.general,wm_tokb)  # copy the .general field
                trans_done.add(wm_tokb[wmoldi])             # remember that transformation is done for this kb content

    def consolidate_KB(self,wm_tokb):       # consolidate various attributes of concepts just copied to KB
        trans_done=set()
        for wmoldi in wm_tokb:                      # all old wm indices that were moved to KB
            wmcon = self.cp[wmoldi]    
            if wmcon.known>0 and wm_tokb[wmoldi] not in trans_done:   # wm concept known, transformation not yet done
                kbi = wm_tokb[wmoldi]
                kbcon = gl.KB.cp[kbi]               # the concept in KB 
                kbcon.cons_avg = (kbcon.cons_avg * kbcon.count + wmcon.cons_avg * wmcon.count)/(kbcon.count + wmcon.count)
                if kbcon.known > wmcon.known:       # KB is better known
                    a=1                             # we keep values in KB
                if kbcon.known == wmcon.known:      # same level known 
                    newp = gl.args.pmerge[kbcon.p][wmcon.p]      # read consolidation table
                    #if gl.d==1: print ("CONSOLID wmold",wmoldi,wmcon.mentstr,wmcon.p,"kb conc",kbi,kbcon.mentstr,kbcon.p,"newp",newp)
                    if newp != kbcon.p: gl.log.add_log(("PVALUE OVERRIDE IN KB when paragraph was copied. KB conc:",kbi," ",kbcon.mentstr," old p:",kbcon.p, " new p:",newp))
                    kbcon.p = newp                  # override p in KB
                if kbcon.known < wmcon.known:       # we know better now!
                    kbcon.known = wmcon.known
                    kbcon.p = wmcon.p
                kbcon.count = kbcon.count + wmcon.count # just increase already existing count
                
    def move_Paratokb(self):                # move paragraph to KB on all branches (usually 1 branch should be alive at paragraph end)
        wm_tokb = {}                            # a mapping of the old wm indices to the new KB locations
        remove_list=[]
        for liv in gl.VS.wmliv:                 # process all living branches 
            db = gl.VS.wmlist[liv]              # next WM
            lastmoved=len(db.cp)-1
            dblen=len(db.cp)                    # length of db (a wm) is changing during iteration
            for coni in range (dblen-1,0,-1):   # all concepts except the dummy concept, in reverse order
                if db.cp[coni].relation!=1 and db.cp[coni].known>0:   # not a word, not a parent, not a question
                    nowmoved=coni
                    for toremove in range(lastmoved,nowmoved,-1):   # remove concepts from WM, which were copied in the previous iteration.
                        if len(db.cp[toremove].kblink)>0:
                            wm_tokb[toremove]=db.cp[toremove].kblink[0]  # where was the last concept copied in KB
                        if db.cp[toremove].kblink!=[]:                  # this is copied to KB
                            db.copydata_KB(toremove,db.cp[toremove].kblink[0])    # copy fields of last concept to the KB concept 
                        remove_list.append(toremove)                    # remember to remove last concept
                    if coni>1:                  # do not move the dummy concept on index==1
                        oldlen=gl.KB.ci
                        db.copyto_kb(coni)      # copy concept on coni to kb. Will be deleted from WM in the next iteration.
                        if gl.KB.ci>oldlen: gl.KB.cp[gl.KB.ci].count=0  # if something added, count number will be copied
                    lastmoved=nowmoved
        if gl.d==1: print ("MOVEPARATOKB wm_tokb",wm_tokb)
        db.transform_KB(wm_tokb)                # transform concept that need transformation - these are concept indices that were valid in WM
        db.consolidate_KB(wm_tokb)              # consolidate p value, known value and other values between WM and KB
        for removthis in remove_list:           # remove paragraph from WM after transformation
            if db.ci == removthis:              # should always be true.
                db.remove_concept(allwm=1)      # remove last concept. 
            else: gl.log.add_log(("ERROR in move_Paratokb: WM=",db.this," This WM could not be removed because remove_list does not match last concept in WM."))

    def printlog_WM(self,wmitem):               # print and log branch concepts for debugging
        wminfo = "WM id:"+str(wmitem.this)+" parent WM:"+str(wmitem.pawm)+" WM length:"+str(wmitem.ci+1)+" WMvalue="+str(wmitem.branchvalue)+" last conc used:"+str(wmitem.last)+" activated:"+str(wmitem.activ)+" KB activ:"+str(wmitem.kbactiv)
        print (wminfo)
        gl.log.add_log((wminfo))
        for i,conc in enumerate(wmitem.cp): 
            concinfo = str(i)+ " "+conc.mentstr+" p="+str(conc.p)+" c="+str(conc.c)+" parents="+str(conc.parent)+" same="+str(conc.same)+" general="+str(conc.general)+" known="+str(conc.known)+" g="+str(conc.g)+" wmuse="+str(conc.wmuse)+" kb_use="+str(conc.kb_use)+" kblink:"+str(conc.kblink)+" kbrules:"+str(conc.kb_rules)+" count:"+str(conc.count)+" reasonuse:"+str(conc.reasonuse)
            print (concinfo)
            gl.log.add_log((concinfo))
 
    def keep_OneBranch(self):               # force kill all WMs except a single one, at paragraph end
        bestv = -100
        bestvs = 0
        for liv in gl.VS.wmliv:             # get best branch (first of bests)
            if bestv < gl.VS.wmlist[liv].branchvalue:
                bestv = gl.VS.wmlist[liv].branchvalue
                bestvs=liv
        for liv in gl.VS.wmliv.copy():      # kill branches except one
            if liv != bestvs:               # this is not the best
                gl.VS.kill_Branch(liv,"Not the best branch at paragraph end. Force kill.")
 
    def process_Para(self,rowment):             # process paragraph at paragraph border
        if gl.args.paragraph_tokb >= 1:         # if moving paragraph to KB is enabled
            for id in gl.VS.wmliv:              # print and log all wms living
                wmitem=gl.VS.wmliv[id]
                print ("PARAGRAPH ENDED.   "+rowment)
                gl.log.add_log(("PARAGRAPH ENDED. WM moved to KB: last row=",rowment))
                self.printlog_WM(wmitem)        # print and log branch concepts for debugging
            self.keep_OneBranch()               # force kill all WMs except a single one
            self.move_Paratokb()                # move a paragraph (can be the last one) to KB
        gl.act.update_Para()                    # update list of activated concepts in this and previous paragraph
                       
    def read_concept(self,attrList,isquestion,isparent=-1,istrack=0):     # recursive function to read concepts from Mentalese input
                                                    # Function returns parent indices!
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
                parents.append(self.read_concept(attrList,isquestion,isparent=1))
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
                    thisparent = self.add_concept(gl.args.pmax,1,[],[wl_ind],g_value,isquestion=isquestion)   #parent is empty, KB link is wl_ind
                    overparent=self.override_Parent(isquestion,thisparent) #ez nem mukodik?? VS
                    gl.WM.cp[thisparent].mapto=overparent           # remember in the word where it was overridden to
                    return overparent   # return the parent after potential override
                else:                               #if the concept is not a single word, register the embedded concept as parent, and read the next parent
                    attrList[0]=str(aStr[actPos+1:]).strip()
                    parents.append(self.read_concept(attrList,isquestion,isparent=1))
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
                    thisparent = self.add_concept(gl.args.pmax,1,[],[wl_ind],g_value,isquestion=isquestion)   #parent is empty, KB link is wl_ind
                    overparent=self.override_Parent(isquestion,thisparent)
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
                        if isparent==-1:                                                # this is not a parent but the top concept
                            newindex=self.add_concept(p_result[0],relType,parents,isquestion=isquestion)      # add the concept to WM
                        else:
                            newindex=self.add_concept(gl.args.pmax/2,relType,parents,isquestion=isquestion)   # add the concept to WM, parent has p=pmax/2
                        self.cp[newindex].rulestr=p_result[2]                           # add the rule string
                    else:
                        if isquestion==1:                                               # for question set pmax/2 p value
                            newindex=self.add_concept(int(gl.args.pmax/2),relType,parents,isquestion=isquestion)      # add the concept to WM
                            self.zero_Known(newindex)                                   # question known value is zero
                        else:
                            if isparent==-1:                                                # this is not a parent but the top concept
                                newindex=self.add_concept(gl.args.pdefault,relType,parents,isquestion=isquestion) # add the concept to WM
                            else:
                                newindex=self.add_concept(gl.args.pmax/2,relType,parents,isquestion=isquestion)   # add the concept to WM, parent has p=pmax/2
                                self.zero_Known(newindex)                                   # parent known value is zero
                        
                    if r_result is not None:
                        self.cp[newindex].relevance=r_result[0]
                    if g_result is not None:
                        self.cp[newindex].g=g_result[0]
                    self.cp[newindex].track=istrack             # track concept if needed
                    return newindex
                
            actPos=actPos+1
        return

    def branch_read_concept(self,starti,tfment,tf,ri):      # read new input on all branches
        s=timer()
        isquestion = tf.question[ri]                        # is it a question?
        mentalese = tfment[:]                               # remember the input
        storewm = gl.WM                                   
        brancho = branch.Branch(0)                          # create the branching object
        for lwmid in gl.VS.wmliv.copy():                    # read input into all living branches (copy because list changes)
            gl.WM = gl.VS.wmliv[lwmid]                      # next living WM into gl.WM
            mentalese3 = mentalese[:]
            lastcon=gl.WM.ci
            if len(tfment[0])>1:                            # tfment is not yet processed (it will become zero length)
                gl.WM.read_concept(tfment,isquestion,istrack=tf.debug[ri])   # read input into this branch
            else:
                gl.WM.read_concept(mentalese3,isquestion)   # read input into this branch
            moved=gl.WM.move_rule(tf,ri,starti)             # if this is a rule, move to KB
            if moved==0 and gl.WM.ci>=0:                    # not rule, not first conc
                gl.WM.move_relevant(starti)                 # if this concept is top relevant, r=4, move it to KB
            if isquestion == 1: gl.WM.last_question = gl.WM.ci
            for newcon in range(gl.WM.ci-lastcon):          # cycle through newly added concepts
                curcon=lastcon+newcon+1                     # current concept
                brancho.wmpos=curcon                        # position of new concept
                brancho.vs_perform_Branching(gl.WM)         # call branching after new concept was added to this branch
            #if gl.d==1: print ("BR READ db=",gl.WM.this,"thispara=",gl.WM.thispara)
        gl.WM = storewm
        gl.args.settimer("concep_700: branch_read_concept",timer()-s)            

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
