import gl, conc
from timeit import default_timer as timer


# TO DO: X-relation
# TO DO: XOR(%1.p=p1,%2) this p value should work
# TO DO: NOT() relation  or Q(not,x)  just like Q(some,x) Q(maybe,x) Q(probably,x) etc
# TO DO: N() rule - necessary condition - not so important
# TO DO: no general AND reasoning to arrive at R(of,mother).  A(family,F(consist,R(of,AND(father,mother))))
# TO DO: spreading activation is exploding.
# TO DO: inv olve KB in reasoning. done: for a new IM relation, the condition is searched in KB, condition p gets updated.

class Reasoning:
    def __init__(self):
        self.actual=0
        self.reason_processed=0         # last indec in gl:WM.cp that was processed for reasoning
        self.words_to_map = {}          # wmposition-word pairs to store the index of D(x) added in mapping_Insert
        self.question_specific_words=[] # words in a question that have g=0 and need mapping
        self.recordrel = []             # collect relations of the compound concept to be reasoned
        self.imparents = []             # list to collect parents of a concept to be reasoned
        self.recordparents = []         # list to collect parents of a compound concept to be reasoned
        self.topparents = []            # record which parents on top level are to be affected by reasoning.
        self.noreplace = {}             # map to record inhibited replacements
        self.replaced = []              # show replacements happened
        self.imcount=0                  # number of concepts added
        self.addedconcfor={}            # note original concepts to be replaced
        self.rtabname = ""              # remember reasoning table used now
        self.thisactiv = []             # concepts activated while a specific concept is being reasoned on    

    #This method checks if the 2 indexes from WM and KB matches (in syntax, not in each word).
    def do_they_match_for_rule(self, wm_index, kb_index):
        if gl.KB.cp[kb_index].relation == 1:
            if "%" in gl.KB.cp[kb_index].mentstr:                               #also finds rules where %1 refers to an entire concept
                return True
            if gl.KB.cp[kb_index].mentstr==gl.WM.cp[wm_index].mentstr:          # word given in rule, it matches
                return True
            else: return False
        rule_relation=gl.KB.cp[kb_index].relation
        if rule_relation==-1 or rule_relation==gl.WM.cp[wm_index].relation:         #handles X concept - X must be the last concept in rule condition
            if len(gl.WM.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(gl.WM.cp[wm_index].parent)):
                if not self.do_they_match_for_rule(gl.WM.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j]):
                    return False
            return True
        return False

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
        
    def vs_createConceptRules(self, db, wm_pos):                # collect matching rule fragments
        matching_rules = []
        for kb_pos in range(0, gl.KB.cp.__len__()):
            if self.do_they_match_for_rule(wm_pos, kb_pos):
                matching_rules.append(kb_pos)
        db.cp[wm_pos].kb_rules = matching_rules[:]

    def createConceptRules(self):
        for liv in gl.VS.wmliv:                             # all WMs
            db = gl.VS.wmlist[liv]
            for wm_pos in range(1, db.ci+1):                # all concepts
                if db.cp[wm_pos].kbrules_filled==0:         # not yet processed
                    matching_rules = []
                    for kb_pos in range(0, gl.KB.cp.__len__()):
                        storewm = gl.WM
                        gl.WM = db                             # in the next functionb gl.WM should be db
                        if self.do_they_match_for_rule(wm_pos, kb_pos):
                            matching_rules.append(kb_pos)
                        gl.WM = storewm
                    db.cp[wm_pos].kb_rules = matching_rules[:]
                    db.cp[wm_pos].kbrules_filled=1          # remember this was processed


    def ruleargs_wordmatch(self,new,ruleindex):         # see if word matches rule in D(%1,elephant)
        parenti=0; matching=1
        for rparent in gl.KB.cp[ruleindex].parent:
            if "%" not in gl.KB.cp[rparent].mentstr:
                if (gl.KB.cp[rparent].mentstr != gl.WM.cp[gl.WM.cp[new].parent[parenti]].mentstr):      # word in KB does not match WM
                    matching=0
            parenti+=1
        return matching
        
    def convert_KBrules(self,new,enable):           #converts the rule fractions in kb_rules to [imlevel,condition] list
        imcombined=[]                               #finds first arg of rule and records all potential matches
        gl.WM.cp[new].kbrules_converted=1           # remember this function was used here
        for ruleindex in gl.WM.cp[new].kb_rules:    #low level condition fractions already in kb_rules
            im=[]
            for child in gl.KB.cp[ruleindex].child:
                if gl.KB.cp[child].relation==13 and gl.KB.cp[ruleindex].relation!=1:    #IM relation, single condition, condition not word
                    if ruleindex==gl.KB.cp[child].parent[0]:    #this is the condition, not the implication
                        if (self.ruleargs_wordmatch(new,ruleindex)==1):     #word in rule matches WM
                            im.append(child)            #rule on IM level
                            im.append(ruleindex)        #rule condition
                            if im not in imcombined: imcombined.append(im)
                            im=[]
                if gl.KB.cp[child].relation==16:                #this is the AND-relation of the rule condition
                    for andchild in gl.KB.cp[child].child:      #at least 1 child of AND should be IM relation
                        if gl.KB.cp[andchild].relation==13:     #this is the IM relation
                            if child==gl.KB.cp[andchild].parent[0]:     #AND concept is the condition, not implication in IM
                                if (self.ruleargs_wordmatch(new,ruleindex)==1):     #word in rule matches WM
                                    im.append(andchild)             #rule on IM level
                                    im.append(ruleindex)            #rule condition
                                    if im not in imcombined: imcombined.append(im)
                                    im=[]                                
        gl.WM.cp[new].kb_rules=[]                               #delete old kb_rules content
        for rulei in range(len(imcombined)):                    #copy imcombined to kb_rules and add resoned concept (single condition)
            gl.args.total_reasoncount+=1
            gl.WM.cp[new].kb_rules.append(imcombined[rulei])
            if gl.KB.cp[imcombined[rulei][0]].track==1:         # this conceptg needs tracking
                print ("TRACK rule in convert_KBrules. rule:",imcombined[rulei][0],"concept matching",new,"rule condition",imcombined[rulei][1])
            if enable==1:                                       # enable==0 shows this "new" is parent of an IM concept so reasoning must be skipped
                if gl.d==9: print ("KBRULES db=",gl.WM.this,"concept=",new,gl.WM.cp[new].mentstr,"rule=",gl.WM.cp[new].kb_rules[rulei])
                self.add_ReasonedConcept(new,rulei)                 #add reasoned concept to WM based on new - works for single condition
        while len(gl.WM.cp[new].rule_match)<len(gl.WM.cp[new].kb_rules):    #rule_match must have corresponding items to kb_rules
            gl.WM.cp[new].rule_match.append([])                 #each kb_rules item will have corresponding list of matching WM concepts here

    def add_ReasonedConcept(self,new,rulei,old=-1,wmpi=-1):     #add the resoned concept to WM - rulei applies in "old" if provided
        # new: most recent concept in WM. rulei: index of current rule in kb_rules  old: earlier concept that has all concepts to perform reasoning
        if old==-1:                                 #single condition, called from convert_KBrules
            rule=gl.WM.cp[new].kb_rules[rulei]      #this is [x,y] where x is IM-concept in KB, y is one of the conditions of IM
            firstarg=gl.KB.cp[rule[0]].parent[0]
            if gl.KB.cp[firstarg].relation!=16:     #not AND, single condition
                self.generate_UniConcept(new,rule)
        else:                                       #2 or more conditions, called from append_match
            rule=gl.WM.cp[old].kb_rules[rulei]
            firstarg=gl.KB.cp[rule[0]].parent[0]
            if gl.KB.cp[firstarg].relation==16:     #AND relation
                self.generate_MultiConcept(new,old,rulei,wmpi)

    def kill_Duplicatebranch(self,newparent):                   # kill the branch if it has the same assumption as another one
        if gl.d==4: print ("KILL DUPLICATE BRANCH")
        thisbranch=self.brancho[0].get_previous_concepts(gl.WM.ci)
        ownleaf=-1
        for brd in gl.WM.cp[self.brancho[0].lastbrpos].next:        # run on the D concepts of branching
            if brd in thisbranch: ownleaf=brd
            if gl.WM.cp[brd].relation==3:                           #relation is D
                if sorted(newparent)==sorted(gl.WM.cp[brd].parent): #curent comncept parents are the same as in D()
                    self.brancho[0].kill_Branch(brd,"Reason: duplicate branch on:"+str(gl.WM.ci))  #kill this duplicated branch
                    print ("KILL DUPLICATE. Added:",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"Killed:",brd)
                    

    def set_Use(self,conclist,finalconc=1):                     #set the concept.wmuse to record what input was used for reasoning
        gl.WM.cp[gl.WM.ci].reasonuse.extend(conclist)           # record concepts directly used for reasoning
        if finalconc!=1:
            gl.WM.cp[gl.WM.ci].wmuse=[-2]                       # this shows the concept is a parent of a reasoned concept
        else:
            if conclist!=[]:
                gl.WM.cp[gl.WM.ci].wmuse=[]
                for con in conclist:
                    gl.WM.cp[con].usedby.add(gl.WM.ci)          # record in old concept, in which new concept it was used
                    if gl.WM.cp[con].wmuse==[-1] or gl.WM.cp[con].wmuse==[] or gl.WM.cp[con].wmuse==[-2]:   #not a reasoned concept
                        gl.WM.cp[gl.WM.ci].wmuse.append(con)                #remember this concept in wmuse
                    else:
                        gl.WM.cp[gl.WM.ci].wmuse.extend(gl.WM.cp[con].wmuse)    #reasoned concept, transfer wmuse to current concept
                        gl.WM.cp[gl.WM.ci].wmuse = sorted(list(set(gl.WM.cp[gl.WM.ci].wmuse)))   # remove duplicates
                    if len(gl.WM.cp[con].override)>0:           # used concept was overridden
                        gl.WM.cp[gl.WM.ci].override.update((gl.WM.cp[con].override-set(gl.WM.cp[gl.WM.ci].wmuse)))  # inherit the basis of override
                    
    def same_Reasoned(self,pos,samelist):                       # is this concept the same as original inputs, or originate from same wmuse?
        for wmused in gl.WM.cp[pos].wmuse:                      # original conceptgs used for this reasoning
            if wmused>0:
                if gl.WM.rec_match(gl.WM.cp[pos],gl.WM.cp[wmused],[pos,wmused])==1:     #reasoned concept is the same as one in wmuse
                    return 1
        for samecon in samelist:                                # also check that samelist originate from the same wmuse?
            if gl.WM.rec_match(gl.WM.cp[pos],gl.WM.cp[samecon],[pos,samecon])==1:   #reasoned concept is the same
                wmu_old = set(gl.WM.cp[samecon].wmuse)
                wmu_new = set(gl.WM.cp[pos].wmuse)
                if len(wmu_new)>0 and wmu_new!=set([-1]) and wmu_new!=set([-2]) and wmu_old==wmu_new:   # resoning originated from same concept
                    if gl.args.loglevel>0: gl.log.add_log(("INHIBIT reasoning is same_Reasoned. Same wmuse used. inhibited concept: ",gl.WM.cp[pos].mentstr," wmuse",wmu_new," same old concept",samecon))
                    return 1                                    # same reasoned, this reasoning will be inhibited
        return 0

    def add_Reasonedword(self,newparent):                   # if implication has specific words, add them to WM
        wcount=0
        for npi in range(len(newparent)):
            pari=newparent[npi]
            if type(pari) is not int:                       # parent is not an index but a word
                kbli=gl.WL.find(pari)                       # word1s first meaning in KB. Always found as this is a rule in KB.
                g_value=gl.args.gmax                        # default g for now. TO DO: handle g-value in rule.
                wordwm = gl.WM.add_concept(gl.args.pmax,1,[],[kbli],g_value)   # add word in WM
                newparent[npi]=wordwm                       # update parent list with word in WM
                wcount+=1
        return wcount

    def update_Prevnext(self,addedconcept,leaf,addedword):  # update previous and next after reasoned concepts added
        if len(addedconcept)>1: recentleaf=addedconcept[-2]  # check that more than 1 concept was added
        else: recentleaf=leaf                               # exactly 1 concept added
        gl.WM.cp[gl.WM.ci-addedword].previous=recentleaf    # correct with the number of words added
        gl.WM.cp[recentleaf].next = [gl.WM.ci-addedword]

    def worst_Kvalue(self,r_known,clist):                       # return worst known value
        kbottom=4
        for con in clist:
            if gl.WM.cp[con].known<kbottom:
                kbottom = gl.WM.cp[con].known
        if r_known>-1 and r_known < kbottom:
            kbottom = r_known
        return kbottom
        
    def finaladd_Concept(self,conclist,reasoned_p,rel_list,nplist,rule,r_known=-1):     # single function to add a list of reasoned concepts to WM together with its parents
        s=timer()
        kbottom = self.worst_Kvalue(r_known,conclist)       # final known value will be worst of input or of provided r_known
        if rule[0]>0:                                       # not C,D reasoning
            if gl.KB.cp[rule[0]].track==1:                  # rule tracked
                print ("TRACK rule in finaladd_C 1.  attempted rule:",rule[0],"concepts used",conclist)   
        center=gl.WM.ci                                      #remember ci at entering finaladd
        new=sorted(conclist,key=int,reverse=True)[0]        # latest concept of reasoning basis - the latest reason used
        reasoned_p=int(reasoned_p)
        if type(nplist[0]) is not list: nplist=[nplist]     # old way to add a single concept
        if type(rel_list) is not list: rel_list=[rel_list]
        relevant = gl.WM.select_Relevant(new)               #collect branches on which new can be found
        if kbottom<1: relevant=[]                           # inhibit reasoning of a concept that is not known!
        for leaf in relevant:                               # on all leafs where the reasoned concept must be added
            addedconcept=[]                                 # will hold indices of concepts added now
            ccount=0
            samelist=[]
            for newparent in nplist:                        # parent list of next concept to add
                relation=rel_list[ccount]
                ccount+=1
                for i in range(len(newparent)):
                    if type(newparent[i])==int and newparent[i]<0:      # parent is a compound concept that was added now
                        newparent[i]=addedconcept[(-1)*newparent[i]-1]  # insert the index of this concept
                addedword = self.add_Reasonedword(newparent)    # if implication has specific words, add them first
                if newparent==nplist[-1]: finalconcept=1    # this is the main concept
                else: finalconcept=0
                if finalconcept==1:                         # we are at the main concept
                #VS    thisbranch = self.brancho[0].get_previous_concepts(leaf)    #next entire branch
                #VS    found = gl.WM.search_fullmatch(reasoned_p, relation,newparent,rule,samelist,thisbranch,conclist[:])      #see whether the concept is already on the branch
                    found = gl.WM.search_fullmatch(reasoned_p, relation,newparent,rule,samelist,conclist=conclist[:])      #see whether the concept is already on the branch
                else: found=0                               # add the concept anyway
                if found == 0:
                    if finalconcept==1: apply_p=reasoned_p                  # use reasoned_p in the final concept only
                    else: apply_p = gl.args.pmax/2                          # parents only get pmax/2
                    gl.WM.add_concept(apply_p, relation,newparent)          # add the reasoned concept
                    if finalconcept==0: gl.WM.cp[gl.WM.ci].known=0          # known value set to 0 for parents
                    addedconcept.append(gl.WM.ci)                           # remember where we added a concept
                    gl.WM.cp[gl.WM.ci].rule_use=[rule[0]]                   # record IM level rule used for reasoning
                    self.set_Use(conclist[:],finalconcept)                  # remember used concepts
                    is_inhibited=False                                      # TO DO: move inhibition and same_reasoned to search_fullmatch!!
                    if finalconcept==1:
                        if self.reason_Inhibit(relation,newparent)==1: is_inhibited=True
                        if r_known>-1:                                      # reasoned known value provided
                            gl.WM.cp[gl.WM.ci].known = r_known
                    if self.same_Reasoned(gl.WM.ci,samelist)==1 or is_inhibited:    # same concept reasoned as the input used, or inhibited
                        while gl.WM.ci>center: gl.WM.remove_concept()               # remove all concepts added in this round
                    else:
                        #VS self.update_Prevnext(addedconcept,leaf,addedword)           # update previous and next values
                        if finalconcept==1:
                            #VS gl.WM.update_Branchinfo(leaf,gl.WM.ci)                  # update branch and branchvalue and samstring
                            if gl.d==1: print ("FINALADD 8 WM=",gl.WM.this,"concept added here=",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"p=",gl.WM.cp[gl.WM.ci].p)
                            gl.args.success_reasoncount += 1                            # how many concepts have been reasoned
                            gl.log.add_log(("REASONED concept added! input new,old:",conclist," wmuse:",gl.WM.cp[gl.WM.ci].wmuse," on branch leaf:",leaf," on index:",gl.WM.ci," rule:",rule," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr, " p=",reasoned_p," known=",gl.WM.cp[gl.WM.ci].known," parents:",gl.WM.cp[gl.WM.ci].parent))
                            gl.WM.track_Concept(gl.WM.ci,"New REASONED.")               # concept and rule usage tracking
                    #VS        if relation==3 and reasoned_p==gl.args.pmax:            # D(x,y) added with p=pmax: kill duplicate branch
                    #VS            if newparent in self.brancho[0].lastbr_list or list(reversed(newparent)) in self.brancho[0].lastbr_list:    #parents match
                    #VS                self.kill_Duplicatebranch(newparent)            # try to kill a potentially duplicate branch
                else:                                                   #found==1
                    while gl.WM.ci>center:                              # all added concepts need to be removed
                        gl.WM.remove_concept()
        gl.args.settimer("reason_002: finaladd_Concept", timer()-s)     # measure execution time


    def lookup_Rtable(self,new,old,rulei,wmpi,implication):             #read p value from reasoning table for multi condition
        rule=gl.WM.cp[old].kb_rules[rulei][:]
        try: rtable = gl.KB.cp[rule[0]].rulestr[0][:]                   # the first string is the table name
        except: 
            print("ERROR! Rules must have table. ",gl.KB.cp[rule[0]].mentstr)
            gl.log.add_log(("ERROR lookup_Rtable: Rules must have a table! p=table missing. Rule: ",gl.KB.cp[rule[0]].mentstr))
        indexrules = gl.KB.cp[rule[0]].rulestr[1:]  
        reasoned_p=0
        indexlist=[]
        wmpack= gl.WM.cp[old].rule_match[rulei][wmpi]
        condition = gl.KB.cp[rule[0]].parent[0]
        for indexitem in indexrules:                        # take condition portions
            if len(indexitem)>3: indexlist.append(-1)       # placeholder
        if indexrules==[]:
            print("ERROR! p=p0 missing in rule. Rule: ",gl.KB.cp[rule[0]].mentstr)
            gl.log.add_log(("ERROR lookup_Rtable: p=p0, p=p1 missing in rule. Rule: ",gl.KB.cp[rule[0]].mentstr))
        if gl.d==9: print ("RTABL rtable",rtable,"indexruls",indexrules)
        for indexitem in indexrules:                        # take condition portions
            if len(indexitem)>3:
                indexnow=-2
                try:
                    if rule[1] == int(indexitem[:indexitem.find("p=")]):        #condition portion index is stored left to p=
                        indexnow = int(gl.WM.cp[old].p)                         #we have the condition portion that matches "old"
                    else:
                        for wmitem in wmpack:                                   #this condition must match something in wmpack
                            for rulei in range(len(gl.WM.cp[wmitem].kb_rules)): # we check all rules - this is general.
                                if wmitem==new or [old] in gl.WM.cp[wmitem].rule_match[rulei]: # we remembered which rule matches "old"
                                    wmitemcondi=gl.WM.cp[wmitem].kb_rules[rulei][1]
                                if wmitemcondi == int(indexitem[:indexitem.find("p=")]):    # this is teh first match, left to p=
                                    indexnow = int(gl.WM.cp[wmitem].p)
                    pep="p=p"
                    indexlist[int(indexitem[indexitem.find(pep)+3:])-1] = indexnow    #serial number of index is right to p=p
                except:
                    gl.log.add_log(("ERROR lookup_Rtable: could not get indices for reasoning table. Rule:",gl.KB.cp[rule[0]].mentstr," indices found:",indexlist," concepts used:",new," ",old))
        try:
            reasoned_p = gl.args.pmap[rtable[(rtable.find("=")+1):]]        #not yet p, but the entire table
            for index in indexlist:                                         #take indices one by one
                reasoned_p = reasoned_p[index]
            reasoned_p=int(reasoned_p)
            self.rtabname = rtable[(rtable.find("=")+1):]                   # remember table name used
        except:
            gl.log.add_log(("ERROR in lookup_Rtable: could not read pmap reasoning table. Table name not given or wrong, no =, too many indices, or too big index values. Rule:",gl.KB.cp[rule[0]].mentstr," Table name:",rtable[(rtable.find("=")+1):]," indexc attempted:",indexlist))
        if gl.KB.cp[rule[0]].track==1:                          # rule tracked
            print ("TRACK rule in lookup_Rtable. reasoning with rule:",rule[0]," table used:",rtable[(rtable.find("=")+1):]," index in table:",indexlist," p=",reasoned_p)
        if type(reasoned_p) is list: 
            print("ERROR! p=p1 missing in rule, more p= values needed. Rule: ",gl.KB.cp[rule[0]].mentstr)
            gl.log.add_log(("ERROR lookup_Rtable: p=p1 missing in rule, more p= valéues needed. Rule: ",gl.KB.cp[rule[0]].mentstr))        
        return reasoned_p

    def reason_Inhibit (self,reasoned_rel,reasoned_parents):     #check reasoned concept to stop stupid reasoning
        inhibit=0; visitand=[]
        parent1=reasoned_parents[0]
        allsame=1
        for pind in range(len(reasoned_parents)):
            if pind!=0:
                p2=reasoned_parents[pind]
                same = gl.WM.rec_match(gl.WM.cp[parent1],gl.WM.cp[p2], [parent1,p2])   # compare parents whether they are the same
                if same != 1: allsame=0                                 # a single difference is enough
        if allsame==1:                                                  # if concept parents are all the same      
            if reasoned_rel==2 or reasoned_rel==3 or reasoned_rel==4 or reasoned_rel==16:   #S,D,C,AND relation
                inhibit=1                                               #inhibit D(x,x) C(x,x) etc
        for parent in reasoned_parents:                              # check all parents if they have AND relation
            if "AND(" in gl.WM.cp[parent].mentstr:
                visitand=[]                                          # this list has the full hierarchy of this parent
                gl.WM.visit_db(gl.WM,parent,visitand)                # fill visitand with parent
                for item in visitand:                                # check entire hierarchy
                    if gl.WM.cp[item[0]].relation==16:               # AND rel
                        for ppar in gl.WM.cp[item[0]].parent:        # parents of AND rel
                            if gl.WM.cp[ppar].relation==16: inhibit=1  # inhibit AND(AND(), ...)
        return inhibit
    
    def generate_MultiConcept(self,new,old,rulei,wmpi):      # create reasoned concept if condition is AND()
        # rulei is the index to be used both in kb_rules and rule_match
        # wmpi is the index of wm pack in rule_match[rulei]
        rule=gl.WM.cp[old].kb_rules[rulei]
        condicount = len(gl.KB.cp[gl.KB.cp[rule[0]].parent[0]].parent)   # how many conditions arte there
        if gl.d==9: print ("GEN MULT 1 db=",gl.WM.this,"new",new,"old",old)
        if len(gl.WM.cp[old].rule_match[rulei][wmpi])+1 == condicount:   # we have all conditions
            implication=gl.KB.cp[rule[0]].parent[1]                      # implication in KB
            condition = rule[1]                                          # condition portion in KB, corresponds to "old" in WM
            visitcond=[]
            self.visit_concept(gl.KB,condition,visitcond)                # flattenden KB rule condition
            visitnew=[]            
            self.visit_concept(gl.WM,old,visitnew)                       # flattend corresponding WM concept "old"
            for wmitem in gl.WM.cp[old].rule_match[rulei][wmpi]:         # take concepts of wm pack - these are conditions
                ruleset = gl.WM.cp[wmitem].kb_rules                      # next matching rule set
                for rule_wmitem in ruleset:                              # all matching rules
                    if rule_wmitem[0]==rule[0]:                          # same as our current rule for reasoning (on IM level)
                        if rule_wmitem[1] != condition:                  # first item in ruleset not the same as condition was
                            condit2 = rule_wmitem[1]
                self.visit_concept(gl.KB,condit2,visitcond)              # further build flattend KB condi
                self.visit_concept(gl.WM,wmitem,visitnew)                # further build flattend corresponding WM concept
            condimap = self.check_condition(visitnew,visitcond)          # check that %1 %1 etc have the proper words in new
            if len(condimap)>0:                                          # all new parents successfully created in condimap
                reasoned_p = self.lookup_Rtable(new,old,rulei,wmpi,implication)  # read p values form reasoning table
                if gl.d==9: print ("GEN MULT 8 new",new,gl.WM.cp[new].mentstr,"old=",old,gl.WM.cp[old].mentstr,"rulei",rulei,"wmpi",wmpi,"impl",implication,"reas_p",reasoned_p)
                clist = [new,old]                                        # initiallist of concepts used for reasoning
                for olditem in gl.WM.cp[old].rule_match[rulei][wmpi]:    # look at further concepts used
                    if olditem not in clist: clist.append(olditem)
                self.imparents=[]; self.recordparents=[]; self.recordrel=[]; self.imcount=0
                if gl.d==9: print ("GEN MULT 9 db=",gl.WM.this,"new=",new,"old=",old,"rule=",rule,"reasoned_P:",reasoned_p)
                self.build_concept(gl.KB, implication, condimap, clist[:], reasoned_p, rule)  # call finaladd_Concept for several concepts
                
                

    def generate_IMconcept(self,new,rule,implication,condition,wmcondi,condi_p=-1): # handle the rule IM(IM(%1,%2),%2) normal implication. 
        if len(gl.KB.cp[condition].parent)==2:          # IM() has a single condition and a single implication TO DO: multiple implications
            if "%" in gl.KB.cp[gl.KB.cp[condition].parent[0]].mentstr:      # % in IM(%1,%2)
                if gl.KB.cp[gl.KB.cp[condition].parent[1]].mentstr == gl.KB.cp[implication].mentstr:  # %2 in IM(IM(%1,%2),%2). The rule is now identified.
                    if condi_p==-1:                     # called from generate_uniconcept: the IM rule is found in WM
                        index1 = int(gl.WM.cp[gl.WM.cp[new].parent[0]].p)   # parent of IM is the condition. Its p value was earlier matched to the
                                                                            # last occurance of this concept in WM, if present. So p is correctly taken.
                        clist = [gl.WM.cp[new].parent[0]]   # new is the IM relation, its parent is the condition used, its p value was overridden.
                    else:                                   # called from enter_RuleMatch: the condition was now found, the IM is older. Now "new" has the IM.
                        index1 = int(condi_p)               # the condition p value is explicitley submitted to this function.
                        clist = [wmcondi]                   # the comndition used for IM reasoning
                    index2 = int(gl.WM.cp[new].p)           # p value of IM. That is always the secong index in the im reasoning table.
                    clist.append(new)                       # the IM relation added to the list of concepts used for this reasoning
                    for basec in clist:
                        gl.WM.track_Concept(basec,"IM reasoning attempted using:"+str(clist)+" ")    # track usage           
                    try: reasoned_p = gl.args.im[index1][index2]    # the table name "im" is hardcoded here.
                    except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.im could not be accessed. Indices attempted:",index1,index2))
                    try: kp_known = gl.args.kp_im[index1][index2]   # known value based on p values.
                    except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.kp_im could not be accessed. Indices attempted:",index1,index2))
                    self.rtabname="im"
                    reasoned_concept = gl.WM.cp[new].parent[1]      # the second parent of IM is the implication that we want to reason now.
                    matching=0
                    inhibit = self.reason_Inhibit(gl.KB.cp[implication].relation,gl.WM.cp[reasoned_concept].parent)      #inhibit if needed
                    if condi_p!=-1:                         # if we found the condition, we may not add the implication again
                        matching = gl.WM.search_fullmatch(reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule,[],[],clist[:])  #this is probably ok: we may not reason in case we would have a new p value!!
                    if 0==inhibit and 0==matching :         # in matching, reasoning got inhibited based on unknown concept
                        self.finaladd_Concept(clist[:],reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule,kp_known)
                        if condi_p==-1:                     # IM was the last concept we found
                            gl.WM.cp[gl.WM.cp[new].parent[1]].p = int(reasoned_p)   # set reasoned p value in IM parent occurance too. Consistency.
                            gl.log.add_log(("PVALUE OVERRIDE in generate_IMconcept: implication p=",reasoned_p," in WM concept:",gl.WM.cp[new].parent[1]," ",gl.WM.cp[gl.WM.cp[new].parent[1]].mentstr))
                     
    def visit_concept(self,db,curri,visitmap,nextp=0,relation_remember="0"):    # recursive walk over db from curri towards parents. Call without nextp.
        s=timer()
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.visit_concept(db,db.cp[curri].parent[nextp],visitmap,0,relation_remember+"."+str(db.cp[curri].relation))        # go down to parent
            nextp=nextp+1                                                       # next parent
        visitmap.append([curri, db.cp[curri].mentstr, relation_remember])       # visitmap is a flattened representation of teh context
        gl.args.settimer("reason_901: visit_concept",timer()-s)

    def check_condition(self, visitnew, visitcond):         # check that condition %1 %2 etc and words in WM (new) do match
        s=timer(); error=0
        condimap={}                                         # condition KB string mapped to index in WM
        shift=0                                             # shifting of indexing in visitnew to synchronize with visitcond in compound concept
        for item in range(len(visitcond)):                  # walk in condition parents
            if visitcond[item][2] != visitnew[item+shift][2]:  #the chain of  relations does not match
                while visitcond[item][2] != visitnew[item+shift][2] and len(visitnew)>len(visitcond)+shift:
                    shift+=1                                # shift applied in visitnew until we start to match again
            if visitcond[item][2] != visitnew[item+shift][2]: return {}  # shifting unsuccessful, no match
            try:                                            # try read this condition %1
                if gl.WM.cp[condimap[visitcond[item][1]]].mentstr != visitnew[item+shift][1]:    # will not run if this i sfirst occurence of %1
                    return {}                               # not first occurence and %1 does not match: BAD
            except:                                         # first occurence of %1 or %2 etc
                condimap[visitcond[item][1]] = visitnew[item+shift][0]    # add it to the mapping, %1 etc string mapped to index in WM
        gl.args.settimer("reason_902: check_condition",timer()-s)
        return condimap

    def build_concept(self,db,curri,condimap,conclist,reasoned_p,rule,nextp=0):     #recursive build of reasoned concept starting with parents
        if nextp==0 and db.cp[curri].relation!=1: self.imparents.append([])     # curri is the index of the implication in KB
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.build_concept(db,db.cp[curri].parent[nextp],condimap,conclist,reasoned_p,rule,0)
            nextp=nextp+1
        if db.cp[curri].relation==1:
            try: self.imparents[-1].append(condimap[db.cp[curri].mentstr])      # collect parents for a concept that has words as parents
            except: self.imparents[-1].append(db.cp[curri].mentstr)             # we assume that curri points to a specific word in the rule
        thispnum=len(db.cp[curri].parent)
        if thispnum == len(self.imparents[-1]):                                 # detect that all parents are in place
            self.recordparents.append(self.imparents.pop())                     # remove added fraction parents and record them
            self.recordrel.append(db.cp[curri].relation)                        # record the relation
            self.imcount+=1                                                     # count the concepts added
            if len(self.imparents)>0:                                           # not yet complete
                self.imparents[-1].append(-1*self.imcount)                      # notify finaladd to use some previous concept as parent
            if len(self.imparents)==0:                                          # detect that last concept was added
                if gl.d==9: print ("BUILD CONC 8 db=",gl.WM.this,"conclist:",conclist,"p=",reasoned_p,"relation:",self.recordrel,"parents:",self.recordparents,"rule:",rule)
                self.finaladd_Concept(conclist,reasoned_p,self.recordrel,self.recordparents,rule)
                

    def generate_UniConcept(self,new,rule):         #add reasoned concept to WM if condition is a single concept
        implication=gl.KB.cp[rule[0]].parent[1]
        condition=gl.KB.cp[rule[0]].parent[0]
        cpalist=gl.KB.cp[condition].parent[:]
        impalist=gl.KB.cp[implication].parent[:]
        try: rtable=gl.KB.cp[rule[0]].rulestr[0][:]         #first string on IM level is the table name
        except: print ("ERROR: RULES MUST HAVE TABLE!",gl.KB.cp[rule[0]].mentstr)
        reasoned_p=1
        newparent=[]                                                #this will hold the parents of the reasoned concept
        visitcond=[]; self.visit_concept(gl.KB,condition,visitcond)   # list of %1 %2 etc parents in KB rule condition part
        visitnew=[]; self.visit_concept(gl.WM,new,visitnew)         # list of parents in corresponding WM concept
        condimap = self.check_condition(visitnew,visitcond)         # check that %1 %2 etc in condition have the proper words in new
        if len(condimap)>0 and not (gl.KB.cp[implication].mentstr=="%2" and gl.KB.cp[rule[1]].relation == 13): # condition and new match, not the im rule
            if len(rtable)!=0:                              # reasoning table exist
                try:
                    reasoned_p=gl.args.pmap[rtable[(rtable.find("=")+1):]][int(gl.WM.cp[new].p)]   #index is p value of condition in WM
                    self.rtabname = rtable[(rtable.find("=")+1):]
                except:
                    gl.log.add_log(("ERROR generate_Uniconcept: could not read pmap reasoning table. Too few dimensions? Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable[(rtable.find("=")+1):]," index attempted:",int(gl.WM.cp[new].p)))
                if type(reasoned_p) is list:                # error message for too many dimensions
                    gl.log.add_log(("ERROR generate_Uniconcept: bad pmap reasoning table: Too many dimensions! Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable[(rtable.find("=")+1):]," index attempted:",int(gl.WM.cp[new].p)))
            self.imparents=[]; self.recordparents=[]
            self.recordrel=[]; self.imcount=0
            if gl.KB.cp[implication].mentstr!="%2" or gl.KB.cp[rule[1]].relation!=13:   # this is not the IM(IM(%1,%2),%2) rule
                if gl.d==9: print("UNICONC 8 db=",gl.WM.this,"new",new)
                self.build_concept(gl.KB, implication, condimap, [new][:], reasoned_p,rule)   # call finaladd_Concept for several concepts
        if gl.KB.cp[implication].mentstr=="%2" and gl.KB.cp[rule[1]].relation == 13:    # rule portion is IM, the implication in rule is just %2
            self.generate_IMconcept(new,rule,implication,condition,0)     # wmcondi not known. this is hard-wired for rule: IM(IM(%1,%2),%2)

    def combine_condi(self,condim1,condim2):                # combine two condimaps into one, check that %1 mean the same in both
        s=timer(); condiout={}
        if condim1=={} or condim2=={}: return {}            # empty input is nonmatch. visit function failed because of length error.
        for c1 in condim1:
            if c1 in condiout:
                coutv=condiout[c1]
                c1v=condim1[c1]
                match=gl.WM.rec_match(gl.WM.cp[coutv],gl.WM.cp[c1v],[coutv,c1v])    # match concepts - may be words or even compound?
                if match!=1:                                # mismatch for %1 between old and new
                    return {}                               # failure
            else:
                condiout[c1]=condim1[c1]
            for c2 in condim2:
                if c2 in condiout:
                    c1v=condiout[c2]
                    c2v=condim2[c2]
                    match=gl.WM.rec_match(gl.WM.cp[c1v],gl.WM.cp[c2v],[c1v,c2v])    # match concepts - may be words or even compound?
                    if match!=1:                                # mismatch for %1 between old and new
                        return {}                               # failure
                else:
                    condiout[c2]=condim2[c2]
        gl.args.settimer("reason_903: combine_condi",timer()-s)
        return condiout
                    

    def final_RuleMatch(self,new,old,rulenew,ruleold):      #%1 %2 etc must mean the same thing in new and old
        s=timer()
        visitrulen=[]; self.visit_concept(gl.KB,rulenew[1],visitrulen)
        visitnew=[]; self.visit_concept(gl.WM,new,visitnew)
        condimapnew=self.check_condition(visitnew,visitrulen)   # check that %1 %2 in condition have the proper words in new
        visitruleo=[]; self.visit_concept(gl.KB,ruleold[1],visitruleo)
        visitold=[]; self.visit_concept(gl.WM,old,visitold)
        condimapold=self.check_condition(visitold,visitruleo)   # check that %1 %2 in condition have the proper words in old
        condimap=self.combine_condi(condimapnew,condimapold)    # only new and old are matched. TO DO: match 3+ conditions.
        finalmatch=1
        if condimap=={}: finalmatch=0
        if finalmatch==1:
            for neo in [new,old]:               # take both new and old to check if general is matched to g=0 concept
                if gl.WM.cp[neo].relation==3:   # special for D relation. TO DO: not strategic?
                    if len(gl.WM.cp[neo].parent)==2:
                        g0=gl.WM.cp[gl.WM.cp[neo].parent[0]].g
                        g1=gl.WM.cp[gl.WM.cp[neo].parent[1]].g
                        if (g0==gl.args.gmin and g1>gl.args.gmin) or (g0>gl.args.gmin and g1==gl.args.gmin):  # general mixed with specific
                            finalmatch=0        # not allowed, reasoning willnot work with such D concept
        gl.args.settimer("reason_011: final_RuleMatch", timer()-s)     # measure execution time
        return finalmatch

    def append_Match(self,new,old,rulenew,ruleold,orulei):  #append "new" to old's rule_match wm pack on orulei
        s=timer(); wmpi=0; stored=[]
        for wmpack in gl.WM.cp[old].rule_match[orulei]:     #wm package of matching concepts
            same=0
            for wmitem in wmpack:                           #a single wm concept in the package
                for existingmatch in gl.WM.cp[wmitem].kb_rules:     #rules already added to this single wm concept
                    if existingmatch[1]==rulenew[1]: same=1         #now the condition portion in new is the same as already in "old"
            if same==0:                                     #not the same condition
                extended=gl.WM.cp[old].rule_match[orulei][wmpi][:]  #this pack will be extended with new
                stored=extended[:]                          #need to remember before extension
                finalmatch=1                                #we see whether "new" matches every concept already in wm pack
                for otheritem in stored:                    #all concepts already in wm pack
                    otherrule=self.select_Rule(ruleold[0],gl.WM.cp[otheritem].kb_rules)     #tale its appropriate rule
                    if len(otherrule)==0:
                        finalmatch=0
                    else:
                        thismatch=self.final_RuleMatch(new,otheritem,rulenew,otherrule)     #compare "new" with the other concept
                        if thismatch==0: finalmatch=0
                if finalmatch==1:
                    extended.append(new)                                    #add new to the pack
                    if extended not in gl.WM.cp[old].rule_match[orulei]:    #a wm pack that is not yet there
                        gl.WM.cp[old].rule_match[orulei][wmpi].append(new)  #now we add new
                        self.add_ReasonedConcept(new,orulei,old,wmpi)       #try add reasoned concept based on this exteded wm package
                same=1                                                      #this was the 3-condition case
            wmpi+=1
            if len(stored)>0 and stored not in gl.WM.cp[old].rule_match[orulei]:
                gl.WM.cp[old].rule_match[orulei].append(stored)         #we keep the original package for future extensions
        if [new] not in gl.WM.cp[old].rule_match[orulei]:
            gl.WM.cp[old].rule_match[orulei].append([new])              #we also add a wm package containing "new" only
            nrulei = gl.WM.cp[new].kb_rules.index(rulenew)              # which rule do we consider now in "new" ?
            if [old] not in gl.WM.cp[new].rule_match[nrulei]:           # we want to remember in "new" which is the matching "old" WM concept
                gl.WM.cp[new].rule_match[nrulei].append([old])          # old added to remember. ONLY FOR 2-CONDITION ! TO DO:MAKE GENERAL FOR 3+ cond!
            newpos=len(gl.WM.cp[old].rule_match[orulei])
            self.add_ReasonedConcept(new,orulei,old,newpos-1)           #again try to add reasoned concept : 2-condition case
        gl.args.settimer("reason_012: append_Match", timer()-s)     # measure execution time

    def select_Rule(self,imlevel,rulelist):                 #find the last matching rule
        found=[]
        for rule in rulelist:
            if rule[0]==imlevel:
                found=rule[:]
        return found

    def isenabled_CDreplace(self,new,old,fromc,toc):   # check that C od D reasoning is OK. new is the CD rel.
        isenabled=True
        self.noreplace={}
        for rel in gl.args.noreplace:                       #all relations
            if gl.WM.cp[new].relation==4:                   #new is C relation
                self.noreplace[rel]=gl.args.noreplace[rel][:]   #copy noreplace
            else:
                self.noreplace[rel]=[99]                    #dummy
        if gl.WM.cp[new].relation==4:                       # C rel
            if gl.WM.cp[old].relation==3:                   # old is D rel
                isenabled=False                             # in a D rel, no replacement possible based on C
        if gl.WM.cp[old].relation in gl.args.noxx and len(gl.WM.cp[old].parent)>1:    #disable AND(x,x) D(x,x) and similar
            samecount=0
            for pari in gl.WM.cp[old].parent:           #all parents of target
                if pari==fromc: samecount+=1
                if pari==toc: samecount+=1
            if samecount==len(gl.WM.cp[old].parent): isenabled=False
        #further cases based on gl.noreplace handled in visit_Replace
        return isenabled

    def count_Addedconc(self,repl,parentlist):              # remember orig concepts being replaced and added concept count
        clist=[]
        for pari in gl.WM.cp[repl].parent:                  # concepts potentially already replaced
            if pari in self.addedconcfor:                   # pari was added earlier
                for plist in self.addedconcfor[pari]:       #
                    clist.append(plist)
        if repl in self.addedconcfor:                       # added earlier
            self.addedconcfor[repl].append(parentlist)
        else:
            self.addedconcfor[repl] = [parentlist]          # else insert list of parents being used for addition
        for plist in clist:
            if plist not in self.addedconcfor[repl]:
                self.addedconcfor[repl].append(plist)

    def fix_imcount(self,repmap,pari,pix,rel):              # decrease imcount if disabled replacement is occuring
        if pari in repmap and pix in self.noreplace[rel]:   # parent needs replace, and is disabled !!
            if pari in self.addedconcfor:                   # for pari, concept already planned to be added
                decr = len(self.addedconcfor[pari])
                self.imcount = self.imcount-decr            # adjust imcount because pari replace is disabled
                for pfor in self.addedconcfor[pari]:        # parents not needed
                    for precordi in range(len(self.recordparents)-1,-1,-1): # parents in self.recordparents, backwards
                        if pfor == self.recordparents[precordi]:    #
                            del self.recordparents[precordi]        # delet the most recent unused parent
                            del self.recordrel[precordi]            # delet relation as well
                            self.addedconcfor[pari].remove(pfor)    # this is not being added anymore
                            for ppp in self.addedconcfor:           # check entire list of conc to be added
                                if ppp>pari:                        # a parent potentially using pfor
                                    if pfor in self.addedconcfor[ppp]:  # yes it is using pfor
                                        self.addedconcfor[ppp].remove(pfor)
                                        if ppp in repmap:
                                            repmap[ppp]=repmap[ppp]-decr  # fix the replace index in repmap
                            break                                   # only delete once

    def manage_Replaced (self,rel,pari,repmap,pix,top):     # calculate replacement disable or enable
        if (-1 not in self.replaced) and pari in repmap and pix in self.noreplace[rel]:   # now disable
            if rel in gl.args.enable_repl:                  # special enablement, override noreplace
                if len(self.replaced)>0 and self.replaced[-1] in gl.args.enable_repl[rel]:  # replacement happened on special enablement pos
                    self.noreplace[rel]=[99]                # override noreplace, enable
                else:
                    if len(self.replaced)>1 and self.replaced[-2] in gl.args.enable_repl[rel]:  # replacement happened on special enablement pos
                        self.noreplace[rel]=[99]                # override noreplace, enable
                    else:
                        self.replaced.append(-1)            #disable further replacements
                        if gl.WM.cp[top].track==1:          # concept tracked
                            print ("TRACK concept in manage_Repl 1. WM index:",top,"CD reasoning has been disabled for relation:",rel,"parent",pix)
            else:
                self.replaced.append(-1)            #disable further replacements
                if gl.WM.cp[top].track==1:          # concept tracked
                    print ("TRACK concept in manage_Repl 2. WM index:",top,"CD reasoning has been disabled for relation:",rel,"parent",pix)

                
    def visit_Replace (self,top,curri,repmap):              #recursive visit of old and build of reasoned concept
        nextp=0
        while (len(gl.WM.cp[curri].parent)>0 and nextp<len(gl.WM.cp[curri].parent)):
            self.visit_Replace(top,gl.WM.cp[curri].parent[nextp],repmap)    #go down to parent
            nextp+=1
        repl=curri                              #default is no replace
        rel=gl.WM.cp[repl].relation
        if curri in repmap:                     #curri needs to be replaced
            repl=repmap[curri]                  #replace it using the pair in repmap
        parentlist=gl.WM.cp[repl].parent[:]
        mentales=gl.WM.cp[repl].mentstr[:]
        pix=0 ; repcount=0                      #zero parents needed replacement in concept repl
        for pari in gl.WM.cp[repl].parent:      #parents may need to be replaced7
            self.manage_Replaced(rel,pari,repmap,pix,top)           # enable or disable replacement
            if pari in repmap and pix not in self.noreplace[rel] and (-1 not in self.replaced):   # parent need replace and is not disabled
                parentlist[pix]=repmap[pari]        #replace parent
                #print ("VIS 1 parentlist",parentlist," repcount",repcount)
                mentales="!new!"                #only for debbuging. new concept will bedded.
                if repcount==0:                 #this is the first parent to be replaced
                    self.imcount+=1             #number of concepts to add
                    self.count_Addedconc(repl,parentlist)  # remember how many concepts are added
                    self.recordrel.append(rel)  #remember the relation to be added
                    self.recordparents.append(parentlist)   #parentlist has both the unchanged parents and the replaced one
                    repmap[repl]=gl.WM.ci+self.imcount  #we know the index of the concept to be added. repl needs to be replaced because it has a replaced parent.
                else:                           #more than 1 parent to be replaced TO DO: test: C(dog,animal) F(animal,F(strong,animal))
                    self.recordparents[self.imcount-1][pix]=repmap[pari]   #replace more parents.
                repcount+=1                     #coiunt how many parents are replaced
                self.replaced.append(rel)       # flag what is replaced
                if curri==top:                  #we are on the level of the origoinal concept, not its parents
                    self.topparents.append(pari)   # remember parent needs replace
            self.fix_imcount(repmap,pari,pix,rel)  # decrese imcount if disabled replacement is occuring
            pix+=1                              #index of next pari

    def build_Repmap(self,fromc,toc,repmap):            # fromc and same concepts to fromc need to be replaced by toc
        if fromc not in repmap: repmap[fromc]=toc       # repmap maps concept to replace to the concept by which it is replaced
        for samc in gl.WM.cp[fromc].same:               # all concepts that are the same as fromc
            if samc not in repmap: repmap[samc]=toc    # these also get replaced

    def read_ptable(self,tname,indexlist):              #read reasoning table
        reasoned_p=0
        try:
            reasoned_p=gl.args.pmap[tname]              #entire table
            for index in indexlist:                     #take indices one by one
                reasoned_p=reasoned_p[index]
            reasoned_p=int(reasoned_p)
        except:
            gl.log.add_log(("ERROR in read_ptable (reason.py): could not read pmap reasoning table:",tname," table name wrong or too many indices or too big index values. Indices:",indexlist))
        return reasoned_p

    def process_CDrel(self,new,old):                    # if new is C or D relation, reason on old
        if len(gl.WM.cp[new].parent)==2:
            if gl.WM.cp[new].relation==3 and gl.WM.cp[old].relation==3 and len(gl.WM.cp[old].parent)==2 and new>old:  #D rels: reverse D(a,b) to D(b,a)
                gl.WM.reverse_Drel(new,old)
            p0=gl.WM.cp[new].p                          # p value of C D rel
            p1=gl.WM.cp[old].p                          # p of target concept
            pval=self.read_ptable("pclass",[int(p0),int(p1)])   # p value of reasoned concept based on C reasoning table
            kval=self.read_ptable("kp_pclass",[int(p0),int(p1)])   # known value of reasoned concept based on kp_pclass, index: p values            
            if kval>0:                                  # inhibit a result where known==0
                fromc=gl.WM.cp[new].parent[1]           #class, this will be replaced
                toc=gl.WM.cp[new].parent[0]                 #member, this will be used
                isenab=self.isenabled_CDreplace(new,old,fromc,toc)  #check that reasoning is OK
                if isenab and gl.WM.cp[fromc].mentstr in gl.WM.cp[old].mentstr:  #enabled and fromc somewhere occurs in old:
                    repmap={}                               #map to hold pairs of concept replacements
                    self.build_Repmap(fromc,toc,repmap)     # populate repmap
                    self.imcount=0; self.recordrel=[];self.recordparents=[];self.topparents=[]
                    self.addedconcfor = {}
                    try:
                        self.replaced=[]                        # need to initialize
                        self.visit_Replace(old,old,repmap)      #perform replacement and recursively add reasoned concept with parents
                        if len(self.topparents)>0 and (-1 not in self.replaced):  # we have something to reason and not disabled
                            self.finaladd_Concept([new,old][:],pval,self.recordrel,self.recordparents,[0])  # add the reasoned concepts
                    except:
                        gl.error+=1
                        gl.log.add_log(("ERROR in process_CDrel 1, reason.py. new:",gl.WM.cp[new].mentstr," old:",gl.WM.cp[old].mentstr))
                if gl.WM.cp[new].relation==3:               #D relation: replace parent 0 with 1
                    fromc=gl.WM.cp[new].parent[0]           # this will be replaced
                    toc=gl.WM.cp[new].parent[1]             #member, this will be used
                    isenab=self.isenabled_CDreplace(new,old,fromc,toc)  #check that reasoning is OK
                    if isenab and gl.WM.cp[fromc].mentstr in gl.WM.cp[old].mentstr:  #enabled and fromc somewhere occurs in old:
                        repmap={}                           #map to hold pairs of concept replacements
                        self.build_Repmap(fromc,toc,repmap) # populate repmap
                        self.imcount=0; self.recordrel=[];self.recordparents=[];self.topparents=[]
                        self.addedconcfor = {}
                        try:
                            self.replaced=[]                    # need to initialize
                            self.visit_Replace(old,old,repmap)  #perform replacement and recursively add reasoned concept with parents
                            if len(self.topparents)>0 and (-1 not in self.replaced):    # we have something to reason and not disabled
                                self.finaladd_Concept([new,old][:],pval,self.recordrel,self.recordparents,[0])  # add the reasoned concepts
                        except:
                            gl.error+=1
                            gl.log.add_log(("ERROR in process_CDrel 2, reason.py. new:",gl.WM.cp[new].mentstr," old:",gl.WM.cp[old].mentstr))
                    
    def process_Anyrel(self,new,old):                   #if new is any relation, use earlier C or D in old to reason
        if (gl.WM.cp[old].relation==3 or gl.WM.cp[old].relation==4) and len(gl.WM.cp[old].parent)==2:   #C or D rel with 2 parents
            isfirst=True                                #old is the first occurence of this C or D rel
            for samec in gl.WM.vs_samestring[gl.WM.cp[old].mentstr]:   #same concepts: check that this occurence of old is the first
                if samec<old: isfirst=False             #TO DO check that this is enough just based on mentstr
            #if gl.d==1: print ("ANYREL new old",new,old,"isfirst",isfirst)
            if isfirst: self.process_CDrel(old,new)     #perform CD reasoning, old is teh CD rel
                                                        #TO DO: search for any applicable CD relation in KB!
    def isnew_CDrel(self,new):                  #check that this C or D relation is its first occurence
        is_new=True
        for samec in gl.WM.cp[new].same:                    #same concepts
            if samec < new:                                 # VS there is some saem concept that occured earlier   
                if gl.WM.cp[new].p == gl.WM.cp[samec].p:    # p is same
                    if gl.WM.cp[new].known == gl.WM.cp[samec].known:    # known is same
                        is_new=False                    # this one ("new") is not new, no need to reason with it
                        if gl.WM.cp[new].track==1: print ("TRACK concept use:"+str(new)+" "+gl.WM.cp[new].mentstr+" Concept is not used for C,D reasoning because not new. Same conc:"+str(samec))
                                                #TO DO: add check for C/D relation in KB
        return is_new
                
    def enter_RuleMatch(self,new,old,enable):         # VS:same_list deleted. enable: will cause reasoning be skipped if concept is argument of an IM() relation
        s=timer(); orulei=0
        #hard wired reasoning follows for C and D relation
        #TO DO: check the override implication based on more general C, D relation! Maybe not running.
        if (gl.WM.cp[new].relation==3 or gl.WM.cp[new].relation==4) and gl.WM.cp[old].relation!=1 and enable==1 and len(gl.WM.cp[new].parent)==2:
            if self.isnew_CDrel(new):                           #see if this C or D rel is the first occurence
                #if gl.d==1: print ("ENTER 1 CDREL call. new is rel=3 or 4.")
                self.process_CDrel(new,old)                     #reason on old, using the C or D rel in new
        if gl.WM.cp[new].relation!=1 and enable==1:             #not a word
            self.process_Anyrel(new,old)                        #check that old is C or D and reason on new
        gl.args.settimer("reason_013: enter_Rulematch process_CDrel", timer()-s)

        #reasoning follows based on rules
        if gl.d==9: print ("ENTER 0 db=",gl.WM.this, "new",new,"old",old,"ruleold",gl.WM.cp[old].kb_rules,"rulenew",gl.WM.cp[new].kb_rules)
        self.rtabname=""
        for ruleold in gl.WM.cp[old].kb_rules:              # all rules already added to old concept
            if gl.d==9: print ("ENTER 1 call IM new old",new,old)
            for rulenew in gl.WM.cp[new].kb_rules:          # all pairs with the latest concept
                if gl.d==9: print ("ENTER 3. new",new,"old",old)
                if ruleold[0]==rulenew[0]:                  # IM level rule is th same
                    if rulenew[1] not in ruleold:           # the new condition is not the same what we already had in old concept
                        finalmatch=self.final_RuleMatch(new,old,rulenew,ruleold)    #%1 %2 etc must mean the same thing in new and old
                        if enable==1 and finalmatch==1 and (new not in gl.WM.cp[old].rule_match[orulei]):     #not skipped, and new not in WM pack
                            self.append_Match(new,old,rulenew,ruleold,orulei)                   #add new to the current wm pack
                            if gl.d==9: print ("ENTER 5 APPEND called. new",new,"old",old)            
                # this might be the condition of an earlier IM concept. This has nothing in kb_rules for this.
            if gl.KB.cp[ruleold[1]].relation==13:           # for old, the matching rule's condition is IM, as in IM(IM(%1,%2),%2)
                if gl.WM.cp[old].relation==13:              # redundant for WM
                    if gl.WM.cp[new].relation==gl.WM.cp[gl.WM.cp[old].parent[0]].relation:  #condition in old IM() matches the new concept's relation
                        p2=gl.WM.cp[old].parent[0]
                        if gl.WM.rec_match(gl.WM.cp[new],gl.WM.cp[p2],[new,p2])==1:    # this is exactly the condition
                            gl.WM.cp[old].rule_match[orulei].append([new])   # for debugging and logging, remember the condition now found in "old"
                            implication=gl.KB.cp[ruleold[0]].parent[1]       # implication part of the rule for "old"
                            condition=gl.KB.cp[ruleold[0]].parent[0]         # condition part of the rule
                            condi_p = gl.WM.cp[new].p                        # p value of teh condition, which was found now
                            self.generate_IMconcept(old,ruleold,implication,condition,new,condi_p)  # reason the implication now
                                    
            orulei+=1
        gl.args.settimer("reason_010: enter_RuleMatch", timer()-s)     # measure execution time
        
 
    #def deleted_reset_Currentmapping(self,oldment):         # delete words from currentmapping that are not in the current row
    #def deleted_create_Branchlist(self):
    #def deleted_mapping_Insert(self,qmentalese):                    #insert some D(x) relations before question to force mapping
    #def deleted_insert_Drel(self,starti,qmentalese):                # insert a D(x) relation to force mapping, by calling mapping_Insert    
    #def deleted_add_Samestring(self,wm_pos,thisbranch):           # update samestring dict with wm_pos and return same concepts to wm_pos
    
    def kill_Branch(self,wmi,reason):                             # kill the WM version wmi (given by index)
        gl.log.add_log(("BAD BRANCH KILLED db=",wmi," WM value was:",gl.VS.wmlist[wmi].branchvalue," ",reason," All living versions:",gl.VS.wmliv.keys()))
        print ("BAD BRANCH KILLED db=",wmi," WM value was:",gl.VS.wmlist[wmi].branchvalue," All living versions:",gl.VS.wmliv.keys())
        gl.WM.printlog_WM(gl.VS.wmliv[wmi])
        del gl.VS.wmliv[wmi]

    def compare_Branches(self):                             # find bad branches to be killed
        brmax = 0 ; maxvs = 0
        for liv in gl.VS.wmliv:                             # all living WMs - get best version
            db = gl.VS.wmlist[liv]
            if db.branchvalue > brmax:                      # better than all so far
                brmax = db.branchvalue
                maxvs = liv                                 # this is the best branch
        kill_limit = gl.args.branch_kill[brmax]             # limit set in branch_kill parameter table
        tokill=set()                                           # set to hold versions to kill
        for liv in gl.VS.wmliv:                             # all living WMs - get best version
            db = gl.VS.wmlist[liv]
            if db.branchvalue < kill_limit:                 # version worse than kill limit
                if gl.d==1: print ("KILL db=",db.this,"value=",db.branchvalue,"limit:",kill_limit)
                tokill.add(liv)                             # add to list of those to kill
        if len(tokill)==len(gl.VS.wmliv):                   # all of them would be killed
            tokill.remove(maxvs)                            # the best is not killed
        for killwm in tokill:
            self.kill_Branch(killwm,"Reason: low branch value.")  # kill this version
        gl.WM = gl.VS.wmliv[maxvs]                          # gl.WM gets reassigned to maxvs, because it might have been killed.
    
    def evaluate_Branch(self,db,wmpos):                     # update consistency of gl.WM
    #    allbr = self.select_Relbr(wmpos)                       #get all branches where we have wmpos
        consi = db.cp[wmpos].c                                  # consistency of this concept
        oldvalue = db.branchvalue                               # current consistency of branch
        db.branchvalue = gl.args.branchvalue[oldvalue][consi]   # new branchvalue = by old value and current consistency
        if gl.d==2: print ("EVALU db=",db.this,"wmpos=",wmpos,"consi oldvalue",consi,oldvalue,"new value:",db.branchvalue)
        if oldvalue != db.branchvalue:                          # branch value changed
            gl.log.add_log(("BRANCH VALUE CHANGE db=",db.this," WM value was:",oldvalue," new value:",db.branchvalue," based on concept:",wmpos," consistency=",db.cp[wmpos].c))
                                 
    def vs_perform_Reason(self, qflag):                     # perform reasoning on all wm versions
        s=timer()                                           # qflag shows this is a question
        for liv in gl.VS.wmliv:                                     # all living WMs
            db = gl.VS.wmlist[liv]
            storewm = gl.WM; gl.WM = db                             # set gl.WM to current db
            if qflag==1 and gl.act.act_qw==1:                       # this is a qquestion, and activation on question necessary
                gl.reasoning.vs_recent_Activation()                 # activate on question
            toprocess = db.activ_new.copy()                         # concepts to process in reasoning: those that have been newly activated
            processed = set()                                       # from toprocess, these are processed in this round
            while len(toprocess)>0:                                 # continue reasoning while there is any concept to process
                for wm_pos in sorted(toprocess):                    # this round, toprocess does not change
                    if db.cp[wm_pos].kbrules_filled == 0:           # not yet applied
                        self.vs_createConceptRules(db,wm_pos)       # collect matching rule fragments
                        self.convert_KBrules(wm_pos,1)              # converts the rule fractions in kb_rules to [imlevel,condition] list
                                                                    # also calls the addition of reasoned concept to WM if condition is not AND
                        db.cp[wm_pos].kbrules_filled = 1            # this wmpos is now processed
                    reason_due = (db.activ-set([wm_pos])) - db.cp[wm_pos].reasoned_with  # reasoning to be done with all activ, except itself, and those already done
                    for old in reason_due:                          # iterate over concepts active and not yet used with wm_pos
                        cnew=db.cp[wm_pos]; cold=db.cp[old]
                        if db.cp[old].kbrules_filled==1:                    # only for concepts that have kb_rules filled
                            #if gl.d==1: print ("VSPERF 0 wmpos old",wm_pos,old,"old rel:",db.cp[old].relation,"kbrules old",db.cp[old].kb_rules,"wmpos kbrules",db.cp[wm_pos].kb_rules)
                            if db.cp[old].kb_rules!=[] or cnew.relation in [3,4] or cold.relation in [3,4]:  # old has the rule, or it is C, D relation
                                self.replaced=[]                            # initialize replacement flag
                                gl.args.total_reasoncount+=1                # reasoning attempt
                                self.enter_RuleMatch(wm_pos,old,1)          # 1.completes rule_match list  2. runs reasoning
                                db.cp[wm_pos].reasoned_with.add(old)        # remember this pair was reasoned about
                                db.cp[old].reasoned_with.add(wm_pos)        # remember this pair was reasoned about  
                    self.evaluate_Branch(db,wm_pos)                 # update consistency for db
                    processed.add(wm_pos)                           # remember this was processed
                processed = processed | toprocess                   # add concepts that were processed in this round (toprocess) to all processed
                toprocess = db.activ_new - processed                # concepts that have been activated while reasoning (reasoned concepts)
            db.activ_new = set()                                # resoning completed in this db, no activation is "new"
            db.activ = db.activ - db.activ_qu                   # remove from activated concepts those that were activated due to question      
            db.activ_qu = set()                                 # resoning completed in this db, clear activations based on question
            gl.WM = storewm                                     # restore gl.WM
        self.compare_Branches()                                 # after reasoning complete, we try to kill some bad branches
        gl.args.settimer("reason_000: perform_reason", timer()-s)       # measure execution time

    def vs_recent_Activation(self):                   # we are at question, We activate additional concepts.
        s=timer()
        question = gl.WM.last_question                              # locate the question
        wordlist = gl.WM.get_Wordinment(gl.WM.cp[question].mentstr)  # get words from question mentalese
        gl.act.vs_activate_Fromwords(wordlist)                      # activation based on words of question
        gl.args.settimer("reason_001: recent_Activation",timer()-s)
       
        
