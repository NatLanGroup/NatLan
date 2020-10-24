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
        self.kbreplace = set()          # collect replacements where a KB index is replaced
        self.imcount=0                  # number of compound concepts added
        self.addedcount=0               # number of concepts added
        self.repused = []               # concepts that were replaced using repmap
        self.addedconcfor={}            # note original concepts to be replaced
        self.rtabname = ""              # remember reasoning table used now
        self.thisactiv = []             # concepts activated while a specific concept is being reasoned on   
        self.buildparent=[]             # build the parents when a KB concept is built in WM

    #This method checks if the 2 indexes from db and KB matches (in syntax, not in each word). 
    def do_they_match_for_rule(self, db, wm_index, kb_index):
        if gl.KB.cp[kb_index].relation == 1:
            if "%" in gl.KB.cp[kb_index].mentstr:                               #also finds rules where %1 refers to an entire concept
                return True
            if gl.KB.cp[kb_index].mentstr==db.cp[wm_index].mentstr:          # word given in rule, it matches
                return True
            else: return False
        rule_relation=gl.KB.cp[kb_index].relation
        if rule_relation==-1 or rule_relation==db.cp[wm_index].relation:         #handles X concept - X must be the last concept in rule condition
            if len(db.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(db.cp[wm_index].parent)):
                if not self.do_they_match_for_rule(db,db.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j]):
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

    def deleted_getRulesFor(self, wm_pos):
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

    def deleted_createRule(self, wm_pos):
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
            if self.do_they_match_for_rule(db,wm_pos,kb_pos):
                if not (db.name=="KB" and wm_pos==kb_pos):      # FIX3 should not find itself
                    matching_rules.append(kb_pos)
        db.cp[wm_pos].kb_rules = matching_rules[:]
        
    def vs_FillConceptRules(self, db, wm_pos):                  # collect matching rule fragments, starting from kbstart in KB
        matching_rules = []
        kbstart = db.cp[wm_pos].kbrules_upto                    # start browsing rules from the last concept that is already processed in KB
        for kb_pos in range(kbstart, gl.KB.cp.__len__()):
            if gl.d==1: print ("FILLC match?? wm_pos",wm_pos,"kb_pos",kb_pos,",match?",self.do_they_match_for_rule(wm_pos, kb_pos))
            if self.do_they_match_for_rule(wm_pos, kb_pos):
                matching_rules.append(kb_pos)
        #db.cp[wm_pos].kb_rules.extend(matching_rules[:])        #FIXED  add to existing content
        db.cp[wm_pos].kb_rulenew = matching_rules[:]            # remember these are the new matches
        db.cp[wm_pos].kbrules_upto=gl.KB.cp.__len__()           # remember up to which KB index have been rules filled
        if gl.d==1: print ("FILLCRULES wm_pos",wm_pos,"db:",db.name,"upto:",db.cp[wm_pos].kbrules_upto,"new matches",db.cp[wm_pos].kb_rulenew)

    def deleted_createConceptRules(self):
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


    def ruleargs_wordmatch(self,db,new,ruleindex):         # see if word matches rule in D(%1,elephant)
        parenti=0; matching=1
        for rparent in gl.KB.cp[ruleindex].parent:
            if "%" not in gl.KB.cp[rparent].mentstr:
                if (gl.KB.cp[rparent].mentstr != gl.WM.cp[db.cp[new].parent[parenti]].mentstr):      # word in KB does not match WM
                    matching=0
            parenti+=1
        return matching
        
    def convert_KBrules(self,db,new,enable):           #converts the rule fractions in kb_rules to [imlevel,condition] list
        imcombined=[]                               #finds first arg of rule and records all potential matches
        #gl.WM.cp[new].kbrules_converted=1           #FIXED delete. remember this function was used here
        for ruleindex in db.cp[new].kb_rules:       # low level condition fractions already in kb_rules
            im=[]
            for child in gl.KB.cp[ruleindex].child:
                if gl.KB.cp[child].relation==13 and gl.KB.cp[ruleindex].relation!=1:    #IM relation, single condition, condition not word
                    if ruleindex==gl.KB.cp[child].parent[0]:    #this is the condition, not the implication
                        if (self.ruleargs_wordmatch(db,new,ruleindex)==1):     #word in rule matches WM
                            im.append(child)                    #rule on IM level
                            im.append(ruleindex)                #rule condition
                            if im not in imcombined: imcombined.append(im)
                            im=[]
                if gl.KB.cp[child].relation==16:                #this is the AND-relation of the rule condition
                    for andchild in gl.KB.cp[child].child:      #at least 1 child of AND should be IM relation
                        if gl.KB.cp[andchild].relation==13:     #this is the IM relation
                            if child==gl.KB.cp[andchild].parent[0]:     #AND concept is the condition, not implication in IM
                                if (self.ruleargs_wordmatch(db,new,ruleindex)==1):     #word in rule matches WM
                                    im.append(andchild)         #rule on IM level
                                    im.append(ruleindex)        #rule condition
                                    if im not in imcombined: imcombined.append(im)
                                    im=[]                                
        db.cp[new].kb_rules=[]                                  # delete old kb_rules content
        for rulei in range(len(imcombined)):                    #copy imcombined to kb_rules and add resoned concept (single condition)
            gl.args.total_reasoncount+=1
            db.cp[new].kb_rules.append(imcombined[rulei])       # we add to existing kb_rules content!!
            if gl.KB.cp[imcombined[rulei][0]].track==1:         # this conceptg needs tracking
                print ("TRACK rule in convert_KBrules. rule:",imcombined[rulei][0],"concept matching",new,"rule condition",imcombined[rulei][1])
            if enable==1 :                                      # enable==0 shows this "new" is parent of an IM concept so reasoning must be skipped
                if gl.d==9: print ("KBRULES db=",db.this,"concept=",new,db.cp[new].mentstr,"rule=",db.cp[new].kb_rules[rulei])
                #if db.name=="WM":           # ITT TARTOK most meg csak WM eseten reasonel!!
                self.add_ReasonedConcept(db,new,rulei)              #add reasoned concept to WM based on new in db - works for single condition
        while len(db.cp[new].rule_match)<len(db.cp[new].kb_rules):  #rule_match must have corresponding items to kb_rules
            db.cp[new].rule_match.append([])                        #each kb_rules item will have corresponding list of matching WM concepts here

    def add_ReasonedConcept(self,db,new,rulei,old=-1,wmpi=-1):     #add the resoned concept to WM - rulei applies in "old" if provided
        # new: most recent concept in db. rulei: index of current rule in kb_rules  old: earlier concept that has all concepts to perform reasoning
        if old==-1:                                 #single condition, called from convert_KBrules
            rule=db.cp[new].kb_rules[rulei]      #this is [x,y] where x is IM-concept in KB, y is one of the conditions of IM
            firstarg=gl.KB.cp[rule[0]].parent[0]
            if gl.KB.cp[firstarg].relation!=16 and "%1" in gl.KB.cp[rule[0]].mentstr:     #not AND, single condition, FIX3: has %1 
                self.generate_UniConcept(db,new,rule)
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
            if conclist!=[] and conclist[0]>0:          #FIX >0
                gl.WM.cp[gl.WM.ci].wmuse=[]
                for con in conclist:
                    gl.WM.cp[con].usedby.add(gl.WM.ci)          # record in old concept, in which new concept it was used
                    if gl.WM.cp[con].wmuse==[] or gl.WM.cp[con].wmuse[0]<0:   #not a reasoned concept
                        gl.WM.cp[gl.WM.ci].wmuse.append(con)                #remember this concept in wmuse
                        #if gl.d==4: print ("SETUSE 1 here:",gl.WM.ci,"this:",con)
                    else:
                        gl.WM.cp[gl.WM.ci].wmuse.extend(gl.WM.cp[con].wmuse)    #reasoned concept, transfer wmuse to current concept
                        #if gl.d==4: print ("SETUSE 2 here:",gl.WM.ci,"this:",gl.WM.cp[con].wmuse)
                        gl.WM.cp[gl.WM.ci].wmuse = sorted(list(set(gl.WM.cp[gl.WM.ci].wmuse)))   # remove duplicates 
                    for kbcon in gl.WM.cp[con].kb_use:          # something from KB was used for con
                        if gl.KB.cp[kbcon].kb_use==[]:
                            if gl.d==2: print ("SETUSE 1 conclist",conclist,"ci:",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"kbcon:",kbcon)
                            gl.WM.cp[gl.WM.ci].kb_use.append(kbcon) # the KB concepts was used itself
                        else:
                            if gl.d==2: print ("SETUSE 2 conclist",conclist,"ci:",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"kbcon:",kbcon)
                            gl.WM.cp[gl.WM.ci].kb_use.extend(gl.KB.cp[kbcon].kb_use)    # transfer kbuse to current concept
                            gl.WM.cp[gl.WM.ci].kb_use = sorted(list(set(gl.WM.cp[gl.WM.ci].kb_use)))   # remove duplicates                             
                    if len(gl.WM.cp[con].override)>0:           # used concept was overridden
                        gl.WM.cp[gl.WM.ci].override.update((gl.WM.cp[con].override-set(gl.WM.cp[gl.WM.ci].wmuse)))  # inherit the basis of override
            elif conclist==[-3]:
                gl.WM.cp[gl.WM.ci].wmuse=[-3]                   # KB is used only
                    
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
        for kbu in gl.WM.cp[pos].kb_use:                        # KB concepts used for this reasoning
            if kbu in gl.WM.cp[pos].kblink:                     # the concept used in KB is the same as the kblink of this WM concept
                return 1                                        # same reasoned
        return 0

    def add_Reasonedword(self,newparent):                   # if implication has specific words, add them to WM
        wcount=0
        for npi in range(len(newparent)):
            pari=newparent[npi]
            if type(pari) is not int:                       # parent is not an index but a word
                kbli=gl.WL.find(pari)                       # word1s first meaning in KB. Always found as this is a rule in KB.
                g_value=gl.args.gmax                        # default g for now. TO DO: handle g-value in rule.
                wordwm = gl.WM.add_concept(gl.args.pmax,1,[],[kbli],g_value,isinput=False)   # add word in WM
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
        
    def finaladd_Concept(self,conclist,kb_use,reasoned_p,rel_list,nplist,rule,r_known=-1):     # single function to add a list of reasoned concepts to WM together with its parents
        s=timer()
        if conclist !=[-3]: kbottom = self.worst_Kvalue(r_known,conclist)       # final known value will be worst of input or of provided r_known
        else: kbottom = 2                                                       # except for conclist that is empty, only KB concepts used for reasoning
        if rule[0]>0:                                       # not C,D reasoning
            if gl.KB.cp[rule[0]].track==1:                  # rule tracked
                print ("TRACK rule in finaladd_C 1.  attempted rule:",rule[0],"concepts used",conclist)   
        center=gl.WM.ci                                      #remember ci at entering finaladd
        #new=sorted(conclist,key=int,reverse=True)[0]        # latest concept of reasoning basis - the latest reason used
        reasoned_p=int(reasoned_p)
        if type(nplist) is not list: nplist=[nplist]     # FIX nplist[0] old way to add a single concept
        if len(nplist)>0 and type(nplist[0])!=list: nplist=[nplist]  # FIX parentlist must be [[  ]] list of lists
        if type(rel_list) is not list: rel_list=[rel_list]
        #if gl.d==3 or gl.d==4: print ("FINALADD 0 rel:",rel_list,"parent:",nplist,"wmuse:",conclist,"kbuse:",kb_use)
        #relevant = gl.WM.select_Relevant(new)               #collect branches on which new can be found
        #if kbottom<1: relevant=[]                           # inhibit reasoning of a concept that is not known!
        if kbottom >= 1:                                    # this is not based on unknown concept
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
                    found = gl.WM.search_fullmatch(reasoned_p, relation,newparent,rule,samelist,conclist=conclist[:])      #see whether the concept is already on the branch
                    if gl.d==3: print ("FINALADD 2 found=",found,"relation",relation,"newparent",newparent,"samelist",samelist,"conclist",conclist)
                else: found=0                               # add the concept anyway
                if found == 0:
                    if finalconcept==1: apply_p=reasoned_p                  # use reasoned_p in the final concept only
                    else: apply_p = gl.args.pmax/2                          # parents only get pmax/2
                    if gl.d==11: print ("FINALADD 4 before adding to WM. nplist",nplist,"rel:",relation,"parents:",newparent,"kb_use",gl.WM.cp[gl.WM.ci].kb_use,"conclist",conclist)
                    if gl.d==8 : gl.WM.printlog_WM(gl.WM)
                    if gl.d==8 : gl.WM.printlog_WM(gl.KB)
                    gl.WM.add_concept(apply_p, relation,newparent,isinput=False,reason="REASONED ")    # add the reasoned concept
                    if finalconcept==0: gl.WM.cp[gl.WM.ci].known=0          # known value set to 0 for parents
                    if gl.d==1: print ("FINALADD 5 WM=",gl.WM.this,"concept added here=",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"p=",gl.WM.cp[gl.WM.ci].p,"kb_use",gl.WM.cp[gl.WM.ci].kb_use,"kbuse received",kb_use)
                    addedconcept.append(gl.WM.ci)                           # remember where we added a concept
                    gl.WM.cp[gl.WM.ci].rule_use=[rule[0]]                   # record IM level rule used for reasoning
                    if gl.d==1: print ("KBUSE:",gl.WM.cp[gl.WM.ci].kb_use,"conclist",conclist)
                    self.set_Use(conclist[:],finalconcept)                  # remember used concepts
                    if gl.d==1: print ("KBUSE:",gl.WM.cp[gl.WM.ci].kb_use)
                    is_inhibited=False                                      # TO DO: move inhibition and same_reasoned to search_fullmatch!!
                    if finalconcept==1:
                        if gl.d==1: print ("KBUSE 2 before",gl.WM.cp[gl.WM.ci].kb_use,"input",kb_use,"we get",(set(gl.WM.cp[gl.WM.ci].kb_use) | set(kb_use)))
                        gl.WM.cp[gl.WM.ci].kb_use=list(set(gl.WM.cp[gl.WM.ci].kb_use) | set(kb_use))   # concepts used in KB, removing duplications   
                        if self.reason_Inhibit(relation,newparent,gl.WM)==1: is_inhibited=True
                        if r_known>-1:                                      # reasoned known value provided
                            gl.WM.cp[gl.WM.ci].known = r_known
                    gl.WM.populate_KBlink(gl.WM.ci)                         # populate the kblink field of newly added concept
                    if self.same_Reasoned(gl.WM.ci,samelist)==1 or is_inhibited:    # same concept reasoned as the input used, or inhibited
                        while gl.WM.ci>center: gl.WM.remove_concept()               # remove all concepts added in this round
                    else:
                        if finalconcept==1:
                            if gl.d==3 or gl.d==4 or gl.d==11: print ("FINALADD 8 -------- WM=",gl.WM.this,"concept added here=",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"parents",gl.WM.cp[gl.WM.ci].parent,"conclist",conclist,"wmuse",gl.WM.cp[gl.WM.ci].wmuse,"kb_use",gl.WM.cp[gl.WM.ci].kb_use,"rule:",rule,"reasonuse",gl.WM.cp[gl.WM.ci].reasonuse)
                            #gl.WM.printlog_WM(gl.WM)
                            #gl.WM.printlog_WM(gl.KB)
                            gl.args.success_reasoncount += 1                            # how many concepts have been reasoned
                            gl.log.add_log(("REASONED concept added! in WM:",gl.WM.this," on index:",gl.WM.ci," rule:",rule," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr," wmuse:",gl.WM.cp[gl.WM.ci].wmuse," kb_use:",gl.WM.cp[gl.WM.ci].kb_use, " p=",reasoned_p," known=",gl.WM.cp[gl.WM.ci].known," parents:",gl.WM.cp[gl.WM.ci].parent))
                            gl.WM.track_Concept(gl.WM.ci,"New REASONED.")               # concept and rule usage tracking
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

    def reason_Inhibit (self,reasoned_rel,reasoned_parents,pdb):     #check reasoned concept to stop stupid reasoning
        inhibit=0; visitand=[]
        parent1=reasoned_parents[0]
        allsame=1
        if pdb.name=="WM":                          # FIX3 TO DO make thsi work for KB
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
                self.imparents=[]; self.recordparents=[]; self.recordrel=[]; self.imcount=0; self.addedcount=0; self.repused=[]
                if gl.d==9: print ("GEN MULT 9 db=",gl.WM.this,"new=",new,"old=",old,"rule=",rule,"reasoned_P:",reasoned_p)
                klist=[]                                                 # concepts used in KB (TO DO)
                self.build_concept(gl.WM, implication, condimap, clist[:],klist[:], reasoned_p, rule)  # FIX ndb parameter=WM. call finaladd_Concept for several concepts
                
    def set_Reasonw(self,wmlist,kblist):                # set reasoned_with field
#        if gl.d==4: print ("SETRW wmlist",wmlist,"kblist",kblist)
        for kb1 in kblist:
            for kb2 in kblist:
                if kb1!=kb2:                    # not the same concepts
                    gl.KB.cp[kb1].reasoned_with.add(-kb2)
                    gl.KB.cp[kb2].reasoned_with.add(-kb1)
                    
    def yes_Reasoned_with(self,ndb,new,condic):     # check if IM and condition have been reasoned together 
        if ndb.name=="KB": newsig=-new              # minus shows the IM relation is in KB
        else: newsig=new
        reasoned=False
        if newsig in condic.reasoned_with:          # IM was reasoned with condic condition
            reasoned=True
        return reasoned

    def fix_clist(self,kbuse,clist):        # populate kbuse and clist
        for cluse in clist[:]:
            if cluse<0:                     # for a KB concept
                kbuse.append(-cluse)         # add to kbuse
                clist.remove(cluse)         # remove from clist

    def manage_Implic(self,ndb,new,clist,kbuse):            # manage the implication, set reasoned_concept
        reasoned_concept = ndb.cp[new].parent[1]            # the second parent of IM is the implication that we want to reason now.
        if ndb.name=="KB":                                  # the IM is in KB, so reasoned_concept is in KB
            reasoned_concept = gl.WM.copyto_WM(ndb,reasoned_concept,[])   # we copy it to WM and note the address
            if len(clist)>0:
                gl.WM.cp[reasoned_concept].wmuse=clist[:]
            else: gl.WM.cp[reasoned_concept].wmuse=[-3]
            gl.WM.cp[reasoned_concept].kb_use=kbuse[:]
        return reasoned_concept
 
    def generate_IMconcept(self,ndb,new,rule,implication,condition,wmcondi,wdb,condi_p=-1): # handle the rule IM(IM(%1,%2),%2) normal implication. 
        if len(gl.KB.cp[condition].parent)==2:          # IM() has a single condition and a single implication TO DO: multiple implications
            if "%" in gl.KB.cp[gl.KB.cp[condition].parent[0]].mentstr:      # % in IM(%1,%2)
                if gl.KB.cp[gl.KB.cp[condition].parent[1]].mentstr == gl.KB.cp[implication].mentstr:  # %2 in IM(IM(%1,%2),%2). The rule is now identified.
            #        if gl.d==4: print ("GENIM 1 ndb",ndb.name,"new",new,ndb.cp[new].mentstr,"wdb",wdb.name,"wmcondi",wmcondi,wdb.cp[wmcondi].mentstr)
                    added_inwm=0
                    if condi_p==-1:                     # called from generate_uniconcept: the IM rule is found in WM
                        index1 = int(ndb.cp[ndb.cp[new].parent[0]].p)   # parent of IM is the condition. Its p value was earlier matched to the
                                                                            # last occurance of this concept in WM, if present. So p is correctly taken.
                        clistsig = ndb.cp[new].parent[0]    # new is the IM relation, its parent is the condition used, its p value was overridden.
                        if ndb.name=="KB": clistsig=-clistsig  # parent is in KB (the condition)
                        clist = [clistsig]                  # FIX3
                        condiknow = ndb.cp[ndb.cp[new].parent[0]].known   # is condition known?
                        condic = ndb.cp[ndb.cp[new].parent[0]]  # FIX4 the condition
                    else:                                   # called from enter_RuleMatch: the condition was now found, the IM is older. Now "new" has the IM.
                        index1 = int(condi_p)               # the condition p value is explicitley submitted to this function.
                        if wdb.name=="WM": clist = [wmcondi]  # the comndition used for IM reasoning
                        else: clist = [-wmcondi]            # minus shows it is in KB
                        condiknow = wdb.cp[wdb.cp[wmcondi].parent[0]].known   # is condition known? 
                        condic = wdb.cp[wdb.cp[wmcondi].parent[0]]
                    if condiknow > 0 and self.yes_Reasoned_with(ndb,new,condic)==False:   # FIX3 condition known, not yet reasoned with
                        index2 = int(ndb.cp[new].p)             # p value of IM. That is always the secong index in the im reasoning table.
                        signew=new
                        if ndb.name=="KB": signew=-new          # minus shows that new is in KB
                        clist.append(signew)                    # FIX3 the IM relation added to the list of concepts used for this reasoning
                        for basec in clist:
                            gl.WM.track_Concept(basec,"IM reasoning attempted using:"+str(clist)+" ")    #FIX4 track usage           
                        try: reasoned_p = gl.args.im[index1][index2]    # the table name "im" is hardcoded here.
                        except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.im could not be accessed. Indices attempted:",index1,index2))
                        try: kp_known = gl.args.kp_im[index1][index2]   # known value based on p values.
                        except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.kp_im could not be accessed. Indices attempted:",index1,index2))
                        self.rtabname="im"
                        kbuse=[]
                        self.fix_clist(kbuse,clist)             # populate kbuse and clist
                        start=gl.WM.ci
                        reasoned_concept =  self.manage_Implic(ndb,new,clist[:],kbuse[:])    # reasoned concept is the implication. Add it to WM if needed.
                        added_inwm=gl.WM.ci-start           # how many concepts added in WM
                        matching=0
                        inhibit = self.reason_Inhibit(gl.KB.cp[implication].relation,gl.WM.cp[reasoned_concept].parent,gl.WM)      #inhibit if needed
                        if condi_p!=-1:                         # if we found the condition, we may not add the implication again
                            matching = gl.WM.search_fullmatch(reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule,[],clist[:])  #this is probably ok: we may not reason in case we would have a new p value!!
                        if 0==inhibit and 0==matching :         # in matching, reasoning got inhibited based on unknown concept
                            if added_inwm>0 and gl.WM.cp[gl.WM.ci].known>0: 
                                if gl.d==3 or gl.d==4: print ("REASONED  +------- IM in WM:",gl.WM.this," on index:",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr)
                                gl.log.add_log(("REASONED concept IM. in WM:",gl.WM.this," on index:",gl.WM.ci," rule:",rule," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr," wmuse:",gl.WM.cp[gl.WM.ci].wmuse," kb_use:",gl.WM.cp[gl.WM.ci].kb_use, " p=",reasoned_p," known=",gl.WM.cp[gl.WM.ci].known," parents:",gl.WM.cp[gl.WM.ci].parent))
                                self.set_Reasonw(clist[:],kbuse[:]) # set reasoned_with field
                                gl.args.success_reasoncount+=1
                            self.finaladd_Concept(clist[:],kbuse[:],reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule,kp_known)
                            if ndb.name=="WM" and condi_p==-1:                     # IM was the last concept we found
                                gl.WM.cp[gl.WM.cp[new].parent[1]].p = int(reasoned_p)   # set reasoned p value in IM parent occurance too. Consistency.
                                gl.log.add_log(("PVALUE OVERRIDE in generate_IMconcept: implication p=",reasoned_p," in WM concept:",gl.WM.cp[new].parent[1]," ",gl.WM.cp[gl.WM.cp[new].parent[1]].mentstr))                  
                        else:                                   # IM reasoning inhibited
                            for rem in range(0,added_inwm):     # remove concepts copied from KB
                                gl.WM.remove_concept()
                    else: 
                        a=1
                       # print ("GENIM 10 IM reasoning stopped. condiknow=0 clist",clist,"condiknow",condiknow,"new",new,"wmcondi",wmcondi)
 
    def visit_concept(self,db,curri,visitmap,nextp=0,relation_remember="0"):    # recursive walk over db from curri towards parents. Call without nextp.
        s=timer()
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.visit_concept(db,db.cp[curri].parent[nextp],visitmap,0,relation_remember+"."+str(db.cp[curri].relation))        # go down to parent
            nextp=nextp+1                                                       # next parent
        visitmap.append([curri, db.cp[curri].mentstr, relation_remember])       # visitmap is a flattened representation of teh concept
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

    def build_concept(self,ndb,curri,condimap,conclist,kb_use,reasoned_p,rule,nextp=0):     #recursive build of reasoned concept starting with parents
        db=gl.KB
        if nextp==0 and db.cp[curri].relation!=1: self.imparents.append([])     # curri is the index of the implication in KB
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.build_concept(ndb,db.cp[curri].parent[nextp],condimap,conclist,kb_use,reasoned_p,rule,0)
            nextp=nextp+1
        if db.cp[curri].relation==1:
            try: self.imparents[-1].append(condimap[db.cp[curri].mentstr])      # collect parents for a concept that has words as parents
            except: self.imparents[-1].append(db.cp[curri].mentstr)             # we assume that curri points to a specific word in the rule
        thispnum=len(db.cp[curri].parent)
        if thispnum == len(self.imparents[-1]):                                 # detect that all parents are in place
            plist=self.imparents.pop()                              #KBFIX
            if ndb.name=="KB":                                                   # KBFIX plist is in KB
                klist=plist[:]; plist=[]
                for kbpari in klist:
                    wmpari=self.visit_KBtowm(kbpari)                            # convert the parent valid in KB to one valid in WM
                    plist.append(wmpari)
            self.recordparents.append(plist)                     #KBFIX PLIST remove added fraction parents and record them
            self.recordrel.append(db.cp[curri].relation)                        # record the relation
            self.imcount+=1; self.addedcount+=1                                 # count the concepts added
            if len(self.imparents)>0:                                           # not yet complete
                self.imparents[-1].append(-1*self.imcount)                      # notify finaladd to use some previous concept as parent
            if len(self.imparents)==0:                                          # detect that last concept was added
                if gl.d==9: print ("BUILD CONC 8 db=",gl.WM.this,"conclist:",conclist,"p=",reasoned_p,"relation:",self.recordrel,"parents:",self.recordparents,"rule:",rule)
                self.finaladd_Concept(conclist[:],kb_use[:],reasoned_p,self.recordrel,self.recordparents,rule)
                

    def generate_UniConcept(self,db,new,rule):         #add reasoned concept to WM if condition is a single concept
        implication=gl.KB.cp[rule[0]].parent[1]
        condition=gl.KB.cp[rule[0]].parent[0]
        cpalist=gl.KB.cp[condition].parent[:]
        impalist=gl.KB.cp[implication].parent[:]
        try: rtable=gl.KB.cp[rule[0]].rulestr[0][:]         #first string on IM level is the table name
        except: print ("ERROR: RULES MUST HAVE TABLE!",gl.KB.cp[rule[0]].mentstr)
        reasoned_p=1
        newparent=[]                                                #this will hold the parents of the reasoned concept
        visitcond=[]; self.visit_concept(gl.KB,condition,visitcond)   # list of %1 %2 etc parents in KB rule condition part
        visitnew=[]; self.visit_concept(db,new,visitnew)            # list of parents in corresponding WM concept
        condimap = self.check_condition(visitnew,visitcond)         # check that %1 %2 etc in condition have the proper words in new
        #if gl.d==4: print ("GENUNI 1  db",db.name,"new",new,db.cp[new].mentstr,"rule",rule)
        #if gl.d==4: gl.WM.printlog_WM(gl.KB)
        if len(condimap)>0 and not (gl.KB.cp[implication].mentstr=="%2" and gl.KB.cp[rule[1]].relation == 13): # condition and new match, not the im rule
            if len(rtable)!=0:                              # reasoning table exist
                try:
                    reasoned_p=gl.args.pmap[rtable[(rtable.find("=")+1):]][int(db.cp[new].p)]   #index is p value of condition in WM
                    self.rtabname = rtable[(rtable.find("=")+1):]
                except:
                    gl.log.add_log(("ERROR generate_Uniconcept: could not read pmap reasoning table. Too few dimensions? Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable[(rtable.find("=")+1):]," index attempted:",int(gl.WM.cp[new].p)))
                if type(reasoned_p) is list:                # error message for too many dimensions
                    gl.log.add_log(("ERROR generate_Uniconcept: bad pmap reasoning table: Too many dimensions! Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable[(rtable.find("=")+1):]," index attempted:",int(gl.WM.cp[new].p)))
            self.imparents=[]; self.recordparents=[] ;self.repused=[]
            self.recordrel=[]; self.imcount=0; self.addedcount=0
            if gl.KB.cp[implication].mentstr!="%2" or gl.KB.cp[rule[1]].relation!=13:   # this is not the IM(IM(%1,%2),%2) rule
                clist=[]; klist=[]
                if db.name=="WM": clist=[new][:]            # new in WM
                else: 
                    klist=[new][:]                          # new in KB
                    clist=[-3]                              # shows that only KB concepts are used
                self.build_concept(db, implication, condimap,clist[:],klist[:],reasoned_p,rule)   # call finaladd_Concept for several concepts
        if gl.KB.cp[implication].mentstr=="%2" and gl.KB.cp[rule[1]].relation == 13:    # rule portion is IM, the implication in rule is just %2
    #        if gl.d==4: print ("GENUNI 9 call genIM. db",db.name,"new",new,db.cp[new].mentstr)
            self.generate_IMconcept(db,new,rule,implication,condition,0,db)     # wmcondi not known. this is hard-wired for rule: IM(IM(%1,%2),%2)

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
                        self.add_ReasonedConcept(gl.WM,new,orulei,old,wmpi)       #try add reasoned concept based on this exteded wm package
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
            self.add_ReasonedConcept(gl.WM,new,orulei,old,newpos-1)           #again try to add reasoned concept : 2-condition case
        gl.args.settimer("reason_012: append_Match", timer()-s)     # measure execution time

    def select_Rule(self,imlevel,rulelist):                 #find the last matching rule
        found=[]
        for rule in rulelist:
            if rule[0]==imlevel:
                found=rule[:]
        return found

    def isenabled_CDreplace(self,new,old,ndb,odb,fromc,toc):   # check that C od D reasoning is OK. new is the CD rel.
        isenabled=True
        self.noreplace={}
        for rel in gl.args.noreplace:                       #all relations
            if ndb.cp[new].relation==4:                     #new is C relation
                self.noreplace[rel]=gl.args.noreplace[rel][:]   #copy noreplace
            else:
                self.noreplace[rel]=[99]                    #dummy
        if ndb.cp[new].relation==4:                         # C rel
            if odb.cp[old].relation==3:                     # old is D rel
                isenabled=False                             # in a D rel, no replacement possible based on C
        if odb.cp[old].relation in gl.args.noxx and len(odb.cp[old].parent)>1:    #disable AND(x,x) D(x,x) and similar
            samecount=0
            for pari in odb.cp[old].parent:                 #all parents of target
                if pari==fromc: samecount+=1
                if pari==toc: samecount+=1
            if samecount==len(odb.cp[old].parent): isenabled=False
        #further cases based on gl.noreplace handled in visit_Replace
        return isenabled

    def count_Addedconc(self,repl,parentlist,odb):              # remember orig concepts being replaced and added concept count
        clist=[]
        for pari in odb.cp[repl].parent:                  # concepts potentially already replaced
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

    def manage_Replaced (self,rel,pari,repmap,pix,top,odb):     # calculate replacement disable or enable
        if (-1 not in self.replaced) and pari in repmap and pix in self.noreplace[rel]:   # now disable
            if pari not in self.kbreplace:                      # kbreplace would enable this replacement (it is just a WM index for a KB index)
                if rel in gl.args.enable_repl:                  # special enablement, override noreplace
                    if len(self.replaced)>0 and self.replaced[-1] in gl.args.enable_repl[rel]:  # replacement happened on special enablement pos
                        self.noreplace[rel]=[99]                # override noreplace, enable
                    else:
                        if len(self.replaced)>1 and self.replaced[-2] in gl.args.enable_repl[rel]:  # replacement happened on special enablement pos
                            self.noreplace[rel]=[99]            # override noreplace, enable
                        else:
                            self.replaced.append(-1)            #disable further replacements
                            if odb.cp[top].track==1:            # concept tracked
                                print ("TRACK concept in manage_Repl 1. db=",odb.name, "db index:",top,"CD reasoning has been disabled for relation:",rel,"parent",pix)
                else:
                    self.replaced.append(-1)            #disable further replacements
                    if odb.cp[top].track==1:          # concept tracked
                        print ("TRACK concept in manage_Repl 2. db=",odb.name, "db index:",top,"CD reasoning has been disabled for relation:",rel,"parent",pix)

    def get_KBtowm(self,curri):                          # curri is in KB, ghet the proper index valid in gl.WM
        for wmc in range(len(gl.WM.cp)):                    # all WM concepts
            if gl.KB.cp[curri].relation==gl.WM.cp[wmc].relation:   # match
                if wmc>1 and len(gl.WM.cp[wmc].kblink)>0:                                      
                    if gl.WM.cp[wmc].kblink[0] == curri:    # the same in KB
                        return wmc                          # this is the wm index
        return 0
        
    def visit_KBtowm(self,curri):                  # recursive walk - curri is valid in KB, needs to be assigned to a WM concept.
        nextp=0; db=gl.KB                                       # db is always KB
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            wmpari = self.visit_KBtowm(db.cp[curri].parent[nextp])      # go down to parent
            nextp=nextp+1                                                       # next parent
        # search for approproate WM concept and add needed concepts
        for wmc in range(len(gl.WM.cp)):                        # all WM concepts
            if db.cp[curri].relation==gl.WM.cp[wmc].relation:   # match
                if wmc>1 and len(gl.WM.cp[wmc].kblink)>0:                                      
                    if gl.WM.cp[wmc].kblink[0] == curri:        # the same in KB
                        self.buildparent.append(wmc)
                        return wmc                              # this is the replacement
        if db.cp[curri].relation==1:                # word
            addparents=[]
        else:                                                   # not word, it has the parents in buildparents
            addparents=self.buildparent[:]
            self.buildparent=[]
        gl.WM.add_concept(int(gl.args.pmax/2),db.cp[curri].relation,addparents,kbl=[curri],isinput=False)      # add the oonc in WM
        self.addedcount+=1           # FIX 09.26 count added concepts
        # self.adjust_Repmap() needed??
        if gl.d==3: print ("KBTOWM ADD CONC ci",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"addedc",self.addedcount)
        gl.WM.cp[gl.WM.ci].known=0                              # this is a parent, known=0
        gl.WM.cp[gl.WM.ci].wmuse=[-2]                           # this is a parent
        self.buildparent.append(gl.WM.ci)                       # the concept just added is a parent of the levbel above
        return gl.WM.ci

    def adjust_Repmap(self,db,repmap):          # a word was added in WM, so repmap indices and recordparents need to be increased 
        for ritem in repmap:                    # 
            #print ("ADJUST1 ritem",ritem,repmap[ritem],"ci",db.ci)
            if repmap[ritem]>=db.ci:            # only these WM items are impacted. for <ci the addition of the word happens after the item index.
                #print ("ADJUST2 ",repmap[ritem],"ci",db.ci)
                for useitem in self.repused:    # replacements used so far
                    if ritem==useitem[0]:       # this index that needs replacement was already used in recordparents 
                        if repmap[ritem]==useitem[1]:   # and oit was used to insert repmap[ritem] into recordparents, which needs a fix now
                            self.recordparents[useitem[2]][useitem[3]]+=1    # adjust the recordparents list because this repmap item was already used in it
                            #print ("ADJUST USED in recordparents! ritem:",ritem,"repmap:",repmap[ritem],"used here:",useitem[2],"on index:",useitem[3])
                repmap[ritem]+=1                # adjust the remap item, increase WM index by one
            #print ("ADJUST3",repmap[ritem],"ci",db.ci)
         
    def visit_Parlist(self,db,curri,repmap):                  # recursive walk - curri is valid in KB, needs to be assigned to a WM concept.
        nextp=0;wmpari=0
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            wmpari = self.visit_Parlist(db,db.cp[curri].parent[nextp],repmap)            # go down to parent
            nextp=nextp+1                                                       # next parent
        # parent replace action
        for wmc in range(len(gl.WM.cp)):                        # all WM concepts
            if db.cp[curri].relation==gl.WM.cp[wmc].relation:   # match
                if wmc>1 :                                      
                    if db.name=="KB":
                        if len(gl.WM.cp[wmc].kblink)>0 and gl.WM.cp[wmc].kblink[0] == curri:    # the same in KB
                            return wmc                          # this is the replacement
        if db.cp[curri].relation==1:                            # only word addition is needed, visit_replace makes sure others are added properly
            addparents=[]
            if gl.d==3: print ("PARLIST ADD WORD1 repmap",repmap,"ci",gl.WM.ci)
            gl.WM.add_concept(int(gl.args.pmax/2),db.cp[curri].relation,addparents,kbl=[curri],isinput=False)      # add the word in WM
            self.addedcount+=1                                  # FIX 09.26 count added concepts
            self.adjust_Repmap(gl.WM,repmap)                       # FIX 09.26 a word was added in WM. repmap and recordparents may be now incorrect because it does not know what words will be added in WM.    
            if gl.d==3: print ("PARLIST ADD WORD2 ci",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"addedc",self.addedcount,"adjusted repmap",repmap)            
            gl.WM.cp[gl.WM.ci].known=0                          # FIX bring under if !!!!! this is a parent, known=0
            gl.WM.cp[gl.WM.ci].wmuse=[-2]                           # this is a parent
            if gl.d==3: print ("PARLIST 3 repmap",repmap)
            repmap[curri]=gl.WM.ci
            if gl.d==3: print ("PARLIST 4 repmap",repmap)
            return gl.WM.ci
        else: return gl.WM.ci+1                                 #FIX compound concept that wioll be added to WM in visit_replace

    def convert_Parentlist(self,ndb,parentlist,repmap):   # parentlist comes from KB. parentlist should get values valid in WM
        for pari in parentlist:
            if pari not in repmap:                              # if pari in repmap, then it will be converted through repmap to a value in WM
                wmpari = self.visit_Parlist(gl.KB,pari,repmap)  # recursive visit of pari concept
                #if gl.d==3: print ("CONVP ndb",ndb.name,"pari in KB",pari,gl.KB.cp[pari].mentstr,"wmpari",wmpari,"WM ci",gl.WM.ci,"repmap",repmap)
                repmap[pari]=wmpari                             # note this as a replacement!! (in this way parentléist still holds indices in KB only)
                #if gl.d==3: print ("CONVP 2 ndb",ndb.name,"pari in KB",pari,gl.KB.cp[pari].mentstr,"wmpari",wmpari,"WM ci",gl.WM.ci,"repmap",repmap)
                if gl.KB.cp[pari].relation==1 and gl.WM.cp[wmpari].kblink[0]==pari:   # it is a word, just a KB-WM replacement, not an inference
                    self.kbreplace.add(pari)                    # remember that pari is an index valid in KB
        # FIX: seems this is not necessary because repmap has already the WM replacement!!!
            #elif ndb.name=="KB":                                # both odb and ndb == KB, repmap has KB replacements, needs to be handled
                #wmpari = self.visit_Parlist(gl.KB,repmap[pari],repmap)  # recursive visit of repmap[pari] concept

    def just_KBrep(self,pari,repmap):                  # find out if a replacement is only the wm copy of a KB concept
        if repmap[pari]<=gl.WM.ci:
            if gl.WM.cp[repmap[pari]].kblink[0]==pari:
                return True
            else:
                return False
                
    def visit_Replace (self,top,curri,odb,ndb,repmap):   #recursive visit of old and build of reasoned concept
        nextp=0
        if gl.d==3: print ("VREP -1 curri",curri)
        while (len(odb.cp[curri].parent)>0 and nextp<len(odb.cp[curri].parent)):
            self.visit_Replace(top,odb.cp[curri].parent[nextp],odb,ndb,repmap)    #go down to parent
            nextp+=1
        rel=odb.cp[curri].relation              # FIX repl changed to curri
        parentlist=odb.cp[curri].parent[:]      # FIX repl changed to curri
        if gl.d==3: print ("VREP 0 odb",odb.name,"curri",curri,odb.cp[curri].mentstr,"parents",odb.cp[curri].parent,"ndb",ndb.name,"repmap",repmap,"parentlist",parentlist,"recordparent",self.recordparents)
        if odb.name=="KB":                      # curri is in KB: parentlist is invalid in WM.
            self.convert_Parentlist(ndb,parentlist,repmap) # parentlist should get values valid in ndb (which is a WM). This adds missing words in WM.
        if gl.d==3: print ("VREP 1 odb",odb.name,"curri",curri,odb.cp[curri].mentstr,"parents",odb.cp[curri].parent,"ndb",ndb.name,"repmap",repmap,"parentlist",parentlist,"recordparent",self.recordparents)
        mentales=odb.cp[curri].mentstr[:]
        pix=0 ; repcount=0                      #zero parents needed replacement in concept curri
        inkb=[]                                 # which parent index is valid in KB!!
        for pari in odb.cp[curri].parent:       # parents may need to be replaced7  FIX: repl changhed to curri
            if odb.name=="KB": inkb.append(1)   # remember this position is still in KB
            else: inkb.append(0)
            self.manage_Replaced(rel,pari,repmap,pix,top,odb)           # enable or disable replacement
            if gl.d==3: print ("VREP 2 parentlist",parentlist,"pari",pari,"pix",pix,"curri",curri,"self.replaced",self.replaced,"recordrel",self.recordrel,"recordparent",self.recordparents,"repmap",repmap)
            #if gl.d==3: gl.WM.printlog_WM(gl.WM)
            #if gl.d==3: gl.WM.printlog_WM(gl.KB)
            if pari in repmap  and (-1 not in self.replaced) : #       parent need replace and is not disabled
                if (pix not in self.noreplace[rel]) or self.just_KBrep(pari,repmap):  # either replacement is OK, or replacement is just a KB index replacement with the WM index
                    parentlist[pix]=repmap[pari]        #replace parent
                    repusenow=[]
                    if gl.d==3: print ("VREP 3 repmap",repmap,"pari",pari,"curri",curri)
                    if repcount==0:                 # this is the first parent to be replaced
                        self.imcount+=1             # number of compound concepts to add
                        self.addedcount+=1           # word addition is counted in visit_Parlist
                        self.count_Addedconc(curri,parentlist,odb)  # remember how many concepts are added
                        self.recordrel.append(rel)  #remember the relation to be added
                        self.recordparents.append(parentlist)   #parentlist has both the unchanged parents and the replaced one
                        if gl.d==3: print ("VREP -4 repmap",repmap,"pari",pari,"ci",gl.WM.ci,"imcount",self.imcount,"curri",curri)
                        if 1==1 or odb.name=="WM":          # FIX - always needed!!!!  REPLACED PARENT PROCESSING
                            if curri not in repmap:         # FIX not yet replaced
                                repmap[curri]=gl.WM.ci+self.imcount  # FIX TO CURRI from repl! added in WM always. we know the index of the concept to be added. curri needs to be replaced because it has a replaced parent.
                        if gl.d==3: print ("VREP 4 repmap",repmap,"pari",pari)
                    else:                           #more than 1 parent to be replaced TO DO: test: C(dog,animal) F(animal,F(strong,animal))
                        self.recordparents[self.imcount-1][pix]=repmap[pari]   #replace more parents. imcount is good because we are in recordparents.
                        if gl.d==3: print ("VREP 41!!! more than 1 replacement. new recordparent:",self.recordparents,"repmap",repmap)
                    self.repused.append([pari,repmap[pari],self.imcount-1,pix])       # FIX 09.26 pari is in repmap, it was used to be replaced by repmap-value 
                    repcount+=1                     # count how many parents are replaced
                    self.replaced.append(rel)       # flag what is replaced
                    if curri==top:                  # we are on the level of the origoinal concept, not its parents
                        self.topparents.append(pari)   # remember parent needs replace
                    inkb[pix]=0                     # pix was replaced so it is now valid in WM
                    if gl.d==3: print ("VREP 5 parentlist",parentlist,"pari",pari,"pix",pix,"repcount",repcount,"self.replaced",self.replaced,"recordrel",self.recordrel,"recordparent",self.recordparents,"repmap",repmap,"inkb",inkb,"countadded",self.addedcount)
            self.fix_imcount(repmap,pari,pix,rel)  # decrese imcount if disabled replacement is occuring
            pix+=1                                  #index of next pari
        if 1 in inkb:                               # any parent value in recordparents is only valid in KB
            for pixinkb in range(len(inkb)):
                if inkb[pixinkb]==1:                # this parent position in recordparents is valid in KB, because it was not touched
                    wmval = self.get_KBtowm(self.recordparents[0][pixinkb])
                    if wmval>0: self.recordparents[0][pixinkb]=wmval   # set value valid in WM
                    #if gl.d==11: print ("VREP 9 FIX recordparent for KB. inkb",inkb,"pixinkb",pixinkb,"wmval",wmval,"recordparent",self.recordparents)


    def check_Replacedone(self,fromcfin,tocfin):            # check if KB-WM replacement occured only
        if fromcfin in self.kbreplace:                      # was valid in KB
            if len(gl.WM.cp[tocfin].kblink)>0:
                if gl.WM.cp[tocfin].kblink[0]==fromcfin:    # just KB-WM replacement
                    a=1                                     # leave fromcfin in self.kbreplace
                else: self.kbreplace.discard(fromcfin)      # remove fromcfin, it is not just KB-WM replacement 
            else: self.kbreplace.discard(fromcfin)                    

    def build_Repmap(self,fromc,toc,ndb,odb,repmap):            # fromc and same concepts to fromc need to be replaced by toc
        fromcfin=fromc; tocfin=toc                              # both ndb and odb  is WM
        if gl.d==3: print ("BUILD 1 ndb:",ndb.name,"odb",odb.name,"fromc",fromc,"toc",toc,"fromcfin tocfin",fromcfin,tocfin,"repmap",repmap)
        if ndb.name=="WM" and odb.name=="KB":                   # D() or C() is in WM, the concept in which we will replace is in KB
            if ndb.cp[fromc].kblink!=[]:
                fromcfin=ndb.cp[fromc].kblink[0]                # in repmap we will have the index of the parents valid in KB, and replace with index valid in WM (toc)
                self.kbreplace.add(fromcfin)                    # remember this is valid in KB
            else: 
                if gl.d==3: print ("BUILD 2 ndb:",ndb.name,"odb",odb.name,"fromc",fromc,ndb.cp[fromc].mentstr,"toc",toc,"fromcfin tocfin",fromcfin,tocfin,"repmap",repmap)
                return                                        # error
        if ndb.name=="KB" and odb.name=="WM":                   # D() or C() is in KB, the concept in which we will replace is in WM
            fromcfin = self.get_KBtowm(fromc)                   # fromc was in KB, fromcfin is valid in WM
            self.buildparent=[]
            tocfin = self.visit_KBtowm(toc)                  # toc was in KB, tocfin is valid in WM, and it is added to WM, if necessary, along with its parents
        if ndb.name=="KB" and odb.name=="KB":                   # D() or C() is in KB, the concept in which we will replace is in KB too
            self.kbreplace.add(fromc)                           # fromc is in KB
            tocfin = self.visit_KBtowm(toc)                     # tocfin is valid in WM and added in WM with parents if needed
        if fromcfin not in repmap: 
            repmap[fromcfin]=tocfin                             # repmap maps concept to replace to the concept by which it is replaced
            self.check_Replacedone(fromcfin,tocfin)             # check if KB-WM replacement occured only
        for samc in ndb.cp[fromc].same:                         # all concepts that are the same as fromc
            samcfin=samc                                        # default, both in WM
            if ndb.name=="WM" and odb.name=="KB":
                if ndb.cp[samc].kblink!=[]:
                    samcfin=ndb.cp[samc].kblink[0]
                    self.kbreplace.add(samcfin)                 # remember this is valid in KB
                else: 
                    if gl.d==3: print ("BUILD 7 ndb:",ndb.name,"odb",odb.name,"fromc",fromc,"toc",toc,"fromcfin tocfin",fromcfin,tocfin,"repmap",repmap)
                    return
            if ndb.name=="KB" and odb.name=="WM":    
                samcfin = self.get_KBtowm(samc) 
            if samcfin not in repmap: 
                repmap[samcfin]=tocfin                          # these also get replaced
                self.check_Replacedone(samcfin,tocfin)         # check if KB-WM replacement occured only
        if gl.d==3: print ("BUILD 9 ndb:",ndb.name,"odb",odb.name,"fromc",fromc,"toc",toc,"fromcfin tocfin",fromcfin,tocfin,"repmap",repmap)

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

    def build_Conclist(self,new,ndb,old,odb,conclist_use,kb_use):           # build the wmuse field content for finaladd function
        if ndb.name=="WM":
            conclist_use.append(new)                    # new in WM
        else: kb_use.append(new)                        # new in KB
        if odb.name=="WM":                             
            conclist_use.append(old)
        else: kb_use.append(old)

    def process_CDrel(self,new,old,ndb,odb):             # if new is C or D relation, reason on old
                                                # ndb is the db of new, odb is the db of old, any of these could be KB
        if len(ndb.cp[new].parent)==2:
            if ndb.name=="WM" and odb.name=="WM" and ndb.cp[new].relation==3 and odb.cp[old].relation==3 and len(odb.cp[old].parent)==2 and new>old:  
                                                            #D rels: reverse D(a,b) to D(b,a)  ONLY for WM currently.
                gl.WM.reverse_Drel(new,old)
            p0=ndb.cp[new].p                                # p value of C D rel
            p1=odb.cp[old].p                                # p of target concept
            pval=self.read_ptable("pclass",[int(p0),int(p1)])   # p value of reasoned concept based on C reasoning table
            kval=self.read_ptable("kp_pclass",[int(p0),int(p1)])   # known value of reasoned concept based on kp_pclass, index: p values   
            if gl.d==3: print ("CDREL 1 ndb",ndb.name,"new",new,ndb.cp[new].mentstr,"new parents",ndb.cp[new].parent,"odb",odb.name,"old",old,odb.cp[old].mentstr)            
            if kval>0:                                      # inhibit a result where known==0
                fromc=ndb.cp[new].parent[1]                 #class, this will be replaced
                toc=ndb.cp[new].parent[0]                   #member, this will be used
                isenab=self.isenabled_CDreplace(new,old,ndb,odb,fromc,toc)  #check that reasoning is OK
                if isenab and ndb.cp[fromc].mentstr in odb.cp[old].mentstr:  #enabled and fromc somewhere occurs in old:
                    repmap={}                               #map to hold pairs of concept replacements
                    if gl.d==3: print ("CDREL build_repmap")
                    self.build_Repmap(fromc,toc,ndb,odb,repmap)     # populate repmap
                    self.imcount=0; self.addedcount=0; self.recordrel=[];self.recordparents=[];self.topparents=[];self.repused=[]
                    self.addedconcfor = {}
                    if 1==1:
                        self.replaced=[]                                                # need to initialize
                        if gl.d==3: print ("CDREL startinggggggg 3 odb",odb.name,"old",old,odb.cp[old].mentstr,"old parents",odb.cp[old].parent,"repmap",repmap,"new",ndb.name,new,ndb.cp[new].mentstr)
                        self.visit_Replace(old,old,odb,ndb,repmap)                      # perform replacement and recursively add reasoned concept with parents
                        if len(self.topparents)>0 and (-1 not in self.replaced):        # we have something to reason and not disabled
                            conclist_use=[];kb_use=[]
                            self.build_Conclist(new,ndb,old,odb,conclist_use,kb_use)    # get wmuse field content
                            if conclist_use==[]: conclist_use=[-3]                      # -3 will show that no WM concept is used, only KB
                            if gl.d==3: print ("CDR pval",pval)
                            self.finaladd_Concept(conclist_use[:],kb_use[:],pval,self.recordrel,self.recordparents,[0])  # add the reasoned concepts
                    else:
                        gl.error+=1
                        gl.log.add_log(("ERROR in process_CDrel 1, reason.py. new:",ndb.cp[new].mentstr," old:",odb.cp[old].mentstr))
                if ndb.cp[new].relation==3:                       #D relation: replace parent 0 with 1  (or??)
                    fromc=ndb.cp[new].parent[0]                   # this will be replaced
                    toc=ndb.cp[new].parent[1]                     #member, this will be used
                    isenab=self.isenabled_CDreplace(new,old,ndb,odb,fromc,toc)  #check that reasoning is OK
                    if isenab and ndb.cp[fromc].mentstr in odb.cp[old].mentstr:  #enabled and fromc somewhere occurs in old:
                        repmap={}                                   #map to hold pairs of concept replacements
                        self.build_Repmap(fromc,toc,ndb,odb,repmap)     # populate repmap
                        self.imcount=0; self.addedcount=0; self.recordrel=[];self.recordparents=[];self.topparents=[];self.repused=[]
                        self.addedconcfor = {}
                        try:
                            self.replaced=[]                        # need to initialize
                            self.visit_Replace(old,old,odb,ndb,repmap)  #perform replacement and recursively add reasoned concept with parents
                            if len(self.topparents)>0 and (-1 not in self.replaced):    # we have something to reason and not disabled
                                conclist_use=[];kb_use=[]
                                self.build_Conclist(new,ndb,old,odb,conclist_use,kb_use)       # get wmuse field content
                                self.finaladd_Concept(conclist_use[:],kb_use[:],pval,self.recordrel,self.recordparents,[0])  # add the reasoned concepts
                        except:
                            gl.error+=1
                            gl.log.add_log(("ERROR in process_CDrel 2, reason.py. db of new:",ndb.name,ndb.this," new:",ndb.cp[new].mentstr," db of old:",odb.name,odb.this," old:",odb.cp[old].mentstr))
                    
    def process_Anyrel(self,new,old,ndb,odb):                   #if new is any relation, use earlier C or D in old to reason
        if (odb.cp[old].relation==3 or odb.cp[old].relation==4) and len(odb.cp[old].parent)==2:   #C or D rel with 2 parents
            isfirst=True                                    #old is the first occurence of this C or D rel
            if odb.name=="WM":                              # in WM, not in KB
                for samec in gl.WM.vs_samestring[gl.WM.cp[old].mentstr]:   #same concepts: check that this occurence of old is the first
                    if samec<old: isfirst=False             #TO DO check that this is enough just based on mentstr
            if isfirst: self.process_CDrel(old,new,odb,ndb)     #perform CD reasoning, old is teh CD rel
                                                       
                                                        
    def isnew_CDrel(self,new):                  #check that this C or D relation is its first occurence  (new is always WM)
        is_new=True
        for samec in gl.WM.cp[new].same:                    #same concepts
            if samec < new:                                 # VS there is some saem concept that occured earlier   
                if gl.WM.cp[new].p == gl.WM.cp[samec].p:    # p is same
                    if gl.WM.cp[new].known == gl.WM.cp[samec].known:    # known is same
                        is_new=False                    # this one ("new") is not new, no need to reason with it
                        if gl.WM.cp[new].track==1: print ("TRACK concept use:"+str(new)+" "+gl.WM.cp[new].mentstr+" Concept is not used for C,D reasoning because not new. Same conc:"+str(samec))
                                                #TO DO: add check for C/D relation in KB
        return is_new
                
    def enter_RuleMatch(self,new,old,odb,ndb,enable):         # VS:same_list deleted. enable: will cause reasoning be skipped if concept is argument of an IM() relation
        s=timer(); orulei=0   
        #hard wired reasoning follows for C and D relation
        if (ndb.cp[new].relation==3 or ndb.cp[new].relation==4) and odb.cp[old].relation!=1 and enable==1 and len(ndb.cp[new].parent)==2:
            if ndb.name=="KB" or self.isnew_CDrel(new) :        #see if this C or D rel is the first occurence, or it is in KB
                self.process_CDrel(new,old,ndb,odb)             #reason on old, using the C or D rel in new
        if ndb.cp[new].relation!=1 and enable==1:               #not a word
            self.process_Anyrel(new,old,ndb,odb)                    #check that old is C or D and reason on new
        gl.args.settimer("reason_013: enter_Rulematch process_CDrel", timer()-s)

        #reasoning follows based on rules
        #if gl.d==4: print ("ENTER 1 new:",ndb.name,new,"old:",odb.name,old)
        self.rtabname=""
        if odb.name=="WM":
            for ruleold in gl.WM.cp[old].kb_rules:              # all rules already added to old concept
                for rulenew in ndb.cp[new].kb_rules:            # all pairs with the latest concept
                    if ndb.name=="WM" and ruleold[0]==rulenew[0]:   # WM ONLY !! IM level rule is th same
                        if rulenew[1] not in ruleold:           # the new condition is not the same what we already had in old concept
                            finalmatch=self.final_RuleMatch(new,old,rulenew,ruleold)    #%1 %2 etc must mean the same thing in new and old
                            if enable==1 and finalmatch==1 and (new not in gl.WM.cp[old].rule_match[orulei]):     #not skipped, and new not in WM pack
                                self.append_Match(new,old,rulenew,ruleold,orulei)                   #add new to the current wm pack
                # this might be the condition of an earlier IM concept. This has nothing in kb_rules for this.
                if gl.KB.cp[ruleold[1]].relation==13:           # for old, the matching rule's condition is IM, as in IM(IM(%1,%2),%2)
                    if gl.WM.cp[old].relation==13:              # redundant for WM
                        if ndb.cp[new].relation==gl.WM.cp[gl.WM.cp[old].parent[0]].relation:  #condition in old IM() matches the new concept's relation
                            p2=gl.WM.cp[old].parent[0]
                            cast=0; newsigned=new
                            if ndb.name=="KB": cast=2                           #FIX2 in rec_match new is searched in KB, old in WM
                            if ndb.rec_match(ndb.cp[new],gl.WM.cp[p2],[new,p2],cast)==1:    #FIX2 ndb.  this is exactly the condition
                                if ndb.name=="KB": newsigned=-new                   # FIX3 remember thsi is in KB
                                gl.WM.cp[old].rule_match[orulei].append([newsigned])   #FIX3 for debugging and logging, remember the condition now found in "old"
                                implication=gl.KB.cp[ruleold[0]].parent[1]       # implication part of the rule for "old"
                                condition=gl.KB.cp[ruleold[0]].parent[0]         # condition part of the rule
                                condi_p = ndb.cp[new].p                          # p value of teh condition, which was found now
                                self.generate_IMconcept(odb,old,ruleold,implication,condition,new,ndb,condi_p)  # reason the implication now
            orulei+=1
        if odb.name=="KB":
            for ruleold in gl.KB.cp[old].kb_rules:              # all rules already added to old concept
                if gl.KB.cp[ruleold[1]].relation==13:           # for old, the matching rule's condition is IM, as in IM(IM(%1,%2),%2)
                    if gl.KB.cp[old].relation==13:             
                        if ndb.cp[new].relation==gl.KB.cp[gl.KB.cp[old].parent[0]].relation:  #condition in old IM() matches the new concept's relation
                            p2=gl.KB.cp[old].parent[0]
                            cast=0; newsigned=new
                            if ndb.name=="WM": cast=1                           #FIX2 in rec_match new is searched in KB, old in WM
                            if ndb.rec_match(ndb.cp[new],gl.KB.cp[p2],[new,p2],cast)==1:    #FIX2 ndb.  this is exactly the condition
                                if ndb.name=="KB": newsigned=-new                   # FIX3 remember thsi is in KB
                                gl.KB.cp[old].rule_match[orulei].append([newsigned])   #FIX3 for debugging and logging, remember the condition now found in "old"
                                implication=gl.KB.cp[ruleold[0]].parent[1]       # implication part of the rule for "old"
                                condition=gl.KB.cp[ruleold[0]].parent[0]         # condition part of the rule
                                condi_p = ndb.cp[new].p                          # p value of teh condition, which was found now
                                self.generate_IMconcept(odb,old,ruleold,implication,condition,new,ndb,condi_p)  # reason the implication now
            orulei+=1
        gl.args.settimer("reason_010: enter_RuleMatch", timer()-s)     # measure execution time
        
    
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
            gl.VS.kill_Branch(killwm,"Reason: low branch value.")  # kill this version
        gl.WM = gl.VS.wmliv[maxvs]                          # gl.WM gets reassigned to maxvs, because it might have been killed.
    
    def evaluate_Branch(self,db,wmpos):                     # update consistency of gl.WM
    #    allbr = self.select_Relbr(wmpos)                       #get all branches where we have wmpos
        consi = db.cp[wmpos].c                                  # consistency of this concept
        oldvalue = db.branchvalue                               # current consistency of branch
        db.branchvalue = gl.args.branchvalue[oldvalue][consi]   # new branchvalue = by old value and current consistency
        if gl.d==2: print ("EVALU db=",db.this,"wmpos=",wmpos,"consi oldvalue",consi,oldvalue,"new value:",db.branchvalue)
        if oldvalue != db.branchvalue:                          # branch value changed
            gl.log.add_log(("BRANCH VALUE CHANGE db=",db.this," WM value was:",oldvalue," new value:",db.branchvalue," based on concept:",wmpos," ",db.cp[wmpos].mentstr," consistency=",db.cp[wmpos].c))

    def call_Rulematch (self,newdb,wmkbpos,reason_due):      # call Rulematch for reasopn_due, wm_pos pairs. newdb may be either WM or KB.
        for mold in reason_due:                             # iterate over concepts active and not yet used with wm_pos, both in WM and KB
            old=mold ; odb=gl.WM                            # WM concepts                                  
            if mold<0:                                      # KB concept is shown by negative sign                                       
                odb = gl.KB
                old=-mold                                   # chnage sign to plus
            cnew=newdb.cp[wmkbpos]; cold=odb.cp[old]
            #if cold.kbrules_filled==1:                      # only for concepts that have kb_rules filled
            self.fill_Kbrules(odb,old,0)                     # fill kb_rules every time again (a new rule may have turned up). Disable reasoning.
            if cold.kb_rules!=[] or cnew.relation in [3,4] or cold.relation in [3,4]:  # old has the rule, or it is C, D relation
                #if newdb.name=="WM" or odb.name=="KB":      # this will exclude newdb=KB, odb=WM. this pair is not needed, it will come as newdb=WM, odb=KB.
                self.replaced=[]                            # initialize replacement flag
                gl.args.total_reasoncount+=1                # reasoning attempt
                reasondone=gl.args.success_reasoncount      # indicate whether reasoning is completed
                self.enter_RuleMatch(wmkbpos,old,odb,newdb,1)   # 1.completes rule_match list  2. runs reasoning.  ndb=gl.WM for wm_pos.
                if reasondone==gl.args.success_reasoncount-1:   # FIX3 enter_rulematch has successfully reasoned
                    cnew.reasoned_with.add(mold)                # remember this pair was reasoned about
                    if newdb.name=="WM": cold.reasoned_with.add(wmkbpos)      # remember this pair was reasoned about  
                    else: 
                        cold.reasoned_with.add(-wmkbpos)      # if it is KB, then -pos must be stored


    def fill_Kbrules(self,db,pos,enable):           # fill kb_rules by browsing through entire KB for matching rules       
        self.vs_createConceptRules(db,pos)          # collect matching rule fragments
        self.convert_KBrules(db,pos,enable)         # converts the rule fractions in kb_rules to [imlevel,condition] list
                                                    # also calls the addition of reasoned concept to WM if condition is not AND

                                 
    def vs_perform_Reason(self, qflag):                     # perform reasoning on all wm versions
        s=timer()                                           # qflag shows this is a question
        for liv in gl.VS.wmliv:                                     # all living WMs
            db = gl.VS.wmlist[liv]
            gl.WM = db                                              # set gl.WM to current db
            if gl.d==4 and gl.WM.ci>=4: print ("VS PERF 0 con=4:",gl.WM.cp[4].mentstr,"reasonedwith:",gl.WM.cp[4].reasoned_with)
            if qflag==1 and gl.act.act_qw==1:                       # this is a qquestion, and activation on question necessary
                gl.reasoning.vs_recent_Activation()                 # activate on question
            toprocess = db.activ_new.copy()                         # concepts to process in reasoning: those that have been newly activated
            for kbcon in db.kbactiv_new: toprocess.add(-kbcon)      # recently activated KB concepts added with minus sign
            # activ_new and kbactiv_new could be erased here.
            processed = set()                                       # from toprocess, these are processed in this round
            kbactminus=set()                                        # a minus sign will show that this is in KB
            for kbcon in db.kbactiv:
                kbactminus.add(-kbcon)                              # kbactminus has all kbactiv concepts with a minus sign
            if gl.d==4: print ("VS PERFORM 1 +++ toprocess",toprocess,"kbactminus",kbactminus,"kbactiv_new",db.kbactiv_new,"processed",processed,"kbactiv",db.kbactiv)
            while len(toprocess)>0:                                 # continue reasoning while there is any concept to process
                if gl.d==2: print ("VS PERFORM 2 toprocess",toprocess,"kbactminus",kbactminus)
                for wm_pos in sorted(toprocess):                    # this round, toprocess does not change
                    if wm_pos>0:                                    # this is in WM
                        #if db.cp[wm_pos].kbrules_filled == 0:           # not yet applied
                        self.fill_Kbrules(db,wm_pos,1)                # fill kb_rules every time again (a new rule may have turned up)
                        reason_due = ((db.activ|kbactminus)-set([wm_pos])) - db.cp[wm_pos].reasoned_with  # reasoning to be done with all activ, except itself, and those already done
                        #if gl.d==4: print ("VS PERFORM 4 wm_pos:",wm_pos,gl.WM.cp[wm_pos].mentstr,"db:",db.this,"reason_due",reason_due,"dbactiv",db.activ,"kbactminus",kbactminus,"reasonwith",db.cp[wm_pos].reasoned_with)
                        self.call_Rulematch(gl.WM,wm_pos,reason_due)    # wm_pos is in WM, perform pairing and call RuleMatch
                        self.evaluate_Branch(db,wm_pos)                 # update consistency for db - only relevant for new concepts that were reasoned into WM
                    elif wm_pos<0:                                  # wm_pos is in KB !
                        kb_pos=-wm_pos
                        self.fill_Kbrules(gl.KB,kb_pos,1)             # fill kb_rules every time again (a new rule may have turned up)
                        reason_due = ((db.activ|kbactminus)-set([wm_pos])) - gl.KB.cp[kb_pos].reasoned_with  # reasoning to be done with all activ, except itself, and those already done
                        #if gl.d==4: print ("VS PERFORM 41 kb_pos:",kb_pos,"db:",db.this,"reason_due:",reason_due)
                        self.call_Rulematch(gl.KB,kb_pos,reason_due)    # kb_pos is in KB, perform pairing and call RuleMatch 
                    processed.add(wm_pos)                           # remember this was processed
                processed = processed | toprocess                   # add concepts that were processed in this round (toprocess) to all processed
                toprocess = db.activ_new.copy()                     # concepts that have been activated while reasoning (reasoned concepts)
                for kbcon in db.kbactiv_new: toprocess.add(-kbcon)      # recently activated KB concepts added with minus sign
                toprocess = toprocess - processed                   # eliminate those already processed
            db.activ_new = set()                                    # resoning completed in this db, no activation is "new"
            db.kbactiv_new = set()
            db.activ = db.activ - db.activ_qu                   # remove from activated concepts those that were activated due to question      
            db.activ_qu = set()                                 # resoning completed in this db, clear activations based on question
            #gl.WM = storewm                                     # restore gl.WM
        self.compare_Branches()                                 # after reasoning complete, we try to kill some bad branches
        gl.args.settimer("reason_000: perform_reason", timer()-s)       # measure execution time

    def vs_recent_Activation(self):                   # we are at question, We activate additional concepts.
        s=timer()
        question = gl.WM.last_question                                  # locate the question
        wordlist = gl.WM.get_Wordinment(gl.WM.cp[question].mentstr)     # get words from question mentalese
        gl.act.vs_activate_Fromwords(wordlist,gl.WM,question)           # activation based on words of question
        gl.args.settimer("reason_001: recent_Activation",timer()-s)
       
        
