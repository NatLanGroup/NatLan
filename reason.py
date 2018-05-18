import gl, conc, branch
from timeit import default_timer as timer


# TO DO: X-relation
# TO DO: XOR(%1.p=p1,%2) this p value should work
# TO DO: NOT() relation  or Q(not,x)  just like Q(some,x) Q(maybe,x) Q(probably,x) etc
# TO DO: N() rule - necessary condition - not so important

class Reasoning:
    def __init__(self):
        self.actual=0
        self.reason_processed=0         # last indec in gl:WM.cp that was processed for reasoning
        self.brancho = []               # here we store the current branching object
        self.relevant_branch = []       # list of branches for current reasoning
        self.words_to_map = {}          # wmposition-word pairs to store the index of D(x) added in mapping_Insert
        self.question_specific_words=[] # words in a question that have g=0 and need mapping
        self.currentmapping = {}        # list of mappings of current input row
        self.recordrel = []             # collect relations of the compound concept to be reasoned
        self.imparents = []             # list to collect parents of a concept to be reasoned
        self.recordparents = []         # list to collect parents of a compound concept to be reasoned
        self.imcount=0                  # number of concepts added

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

    def createConceptRules(self, starti, endi):
        # print('starti: ' + str(starti) + '  endi: ' + str(endi) + '  wm size: ' + str(gl.WM.cp.__len__()))

        for wm_pos in range(starti+1, endi):                #starti+1 not to go back. 21.6.2017.
            matching_rules = []
            for kb_pos in range(0, gl.KB.cp.__len__()):
                if self.do_they_match_for_rule(wm_pos, kb_pos):
                    matching_rules.append(kb_pos)
            gl.WM.cp[wm_pos].kb_rules = matching_rules


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
            gl.WM.cp[new].kb_rules.append(imcombined[rulei])
            if enable==1:                                       #enable7==0 shows this "new" is parent of an IM concept so reasoning must be skipped
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
        thisbranch=self.brancho[0].get_previous_concepts(gl.WM.ci)
        ownleaf=-1
        for brd in gl.WM.cp[self.brancho[0].lastbrpos].next:        # run on the D concepts of branching
            if brd in thisbranch: ownleaf=brd
            if gl.WM.cp[brd].relation==3:                           #relation is D
                if sorted(newparent)==sorted(gl.WM.cp[brd].parent): #curent comncept parents are the same as in D()
                    self.brancho[0].kill_Branch(brd,"Reason: duplicate branch on:"+str(gl.WM.ci))  #kill this duplicated branch
                    print ("KILL DUPLICATE. Added:",gl.WM.ci,gl.WM.cp[gl.WM.ci].mentstr,"Killed:",brd)
                    

    def set_Use(self,conclist,finalconc=1):                   #set the concept.wmuse to record what input was used for reasoning
        gl.WM.cp[gl.WM.ci].reasonuse.extend(conclist)         # record concepts directly used for reasoning
        if finalconc!=1:
            gl.WM.cp[gl.WM.ci].wmuse=[-2]                       # this shows the concept is a parent of a reasoned concept
        else:
            if conclist!=[]:
                gl.WM.cp[gl.WM.ci].wmuse=[]
                for con in conclist:
                    gl.WM.cp[con].usedby.add(gl.WM.ci)        # record in old concept, in which new concept it was used
                    if gl.WM.cp[con].wmuse==[-1] or gl.WM.cp[con].wmuse==[] or gl.WM.cp[con].wmuse==[-2]:   #not a reasoned concept
                        gl.WM.cp[gl.WM.ci].wmuse.append(con)                #remember this concept in wmuse
                    else:
                        gl.WM.cp[gl.WM.ci].wmuse.extend(gl.WM.cp[con].wmuse)    #reasoned concept, transfer wmuse to current concept
                        gl.WM.cp[gl.WM.ci].wmuse = sorted(list(set(gl.WM.cp[gl.WM.ci].wmuse)))   # remove duplicates
                    
    def same_Reasoned(self,pos):                                # is this concept the same as one of the original inputs?
        for wmused in gl.WM.cp[pos].wmuse:                      # original conceptgs used for this reasoning
            if wmused>0:
                if gl.WM.rec_match(gl.WM.cp[pos],gl.WM.cp[wmused],[pos,wmused])==1:     #reasoned concept is the same
                    return 1
        return 0

    def finaladd_Concept(self,conclist,reasoned_p,rel_list,nplist,rule):     # single function to add a list of reasoned concepts to WM together with its parents
        s=timer(); new=conclist[0]                          #new concept of reasoning basis - the latest reason used
        finalconcept=0
        if type(nplist[0]) is not list: nplist=[nplist]     # old way to add a single concept
        if type(rel_list) is not list: rel_list=[rel_list]
        relevant = self.brancho[0].select_Relevant(new)     #collect branches on which new can be found
        for leaf in relevant:                               # on all leafs where the reasoned concept must be added
            addedconcept=[]                                 # will hold indices of concepts added now
            ccount=0
            for newparent in nplist:                        # parent list of next concept to add
                relation=rel_list[ccount]
                ccount+=1
                if newparent==nplist[-1]: finalconcept=1    # this is the main concept
                if finalconcept==1:                         # we are at the main concept
                    thisbranch = self.brancho[0].get_previous_concepts(leaf)    #next entire branch
                    found = gl.WM.search_fullmatch(reasoned_p, relation,newparent,rule,thisbranch,conclist[:])      #see whether the concept is already on the branch
                else: found=0                               # add the concept anyway
                if found == 0:
                    for i in range(len(newparent)):
                        if newparent[i]<0:                  # parent is a compound concept that was added now
                            newparent[i]=addedconcept[(-1)*newparent[i]-1]  # insert the index of this concept
                    if finalconcept==1: apply_p=reasoned_p                  # use reasoned_p in the final concept only
                    else: apply_p = gl.args.pmax/2                          # parents only get pmax/2
                    gl.WM.add_concept(apply_p, relation,newparent)          # add the reasoned concept
                    addedconcept.append(gl.WM.ci)                           # remember where we added a concept
                    gl.WM.cp[gl.WM.ci].reasonuse=[rule[0]]                  # record IM level rule used for reasoning
                    self.set_Use(conclist[:],finalconcept)                  # remember used concepts
                    is_inhibited=False                                      # TO DO: move inhibition and same_reasoned to search_fullmatch!!
                    if finalconcept==1:
                        if self.reason_Inhibit(relation,newparent)==1: is_inhibited=True
                    if self.same_Reasoned(gl.WM.ci)==1 or is_inhibited:     # same concept reasoned as the input used, or inhibited
                        gl.WM.remove_concept()
                    else:
                        gl.WM.cp[gl.WM.ci].previous = leaf
                        if leaf in gl.WM.branch:                            #we may need to update global leaf list
                            gl.WM.branch.remove(leaf)
                            gl.WM.branch.append(gl.WM.ci)                   #updated
                        if gl.WM.ci>0 and gl.WM.cp[gl.WM.ci-1].next == gl.WM.ci:    #earlier concept is also pointing here, ERROR
                            if gl.WM.cp[gl.WM.ci].previous != gl.WM.ci-1:           #next needs to be corrected
                                gl.WM.cp[gl.WM.ci-1].next = []                      #that needs to be a leaf
                        gl.WM.cp[leaf].next = [gl.WM.ci]                            #old leaf continued
                        if finalconcept==1:
                            gl.log.add_log(("REASONED concept added! input new,old:",conclist," on branch leaf:",leaf," on index:",gl.WM.ci," rule:",rule," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr, " p=",reasoned_p," parents:",gl.WM.cp[gl.WM.ci].parent))
                            if relation==3 and reasoned_p==gl.args.pmax:       #D(x,y) added with p=pmax: kill duplicate branch
                                if newparent in self.brancho[0].lastbr_list or list(reversed(newparent)) in self.brancho[0].lastbr_list:    #parents match
                                    self.kill_Duplicatebranch(newparent)        #try to kill a potentially duplicate branch
        gl.args.settimer("reason_002: finaladd_Concept", timer()-s)     # measure execution time
    

    def lookup_Rtable(self,new,old,rulei,wmpi,implication,newparent):   #read p value from reasoning table for multi condition
        rule=gl.WM.cp[old].kb_rules[rulei][:]
        try: rtable = gl.KB.cp[rule[0]].rulestr[0][:]                   # the first string is the table name
        except: print("ERROR! Rules must have table. ",gl.KB.cp[rule[0]].mentstr)
        indexrules = gl.KB.cp[rule[0]].rulestr[1:]
        reasoned_p=0
        indexlist=[]
        wmpack= gl.WM.cp[old].rule_match[rulei][wmpi]
        condition = gl.KB.cp[rule[0]].parent[0]
        for indexitem in indexrules:                        # take condition portions
            if len(indexitem)>3: indexlist.append(-1)       # placeholder
        for indexitem in indexrules:                        # take condition portions
            if len(indexitem)>3:
                indexnow=-2
                try:
                    if rule[1] == int(indexitem[:indexitem.find("p=")]):        #condition portion index is stored left to p=
                        indexnow = int(gl.WM.cp[old].p)                         #we have the condition portion that matches "old"
                    else:
                        for wmitem in wmpack:                                   #this condition must match something in wmpack
                            for rulei in range(len(gl.WM.cp[wmitem].kb_rules)): # we check all rules - this is general.
                                if [old] in gl.WM.cp[wmitem].rule_match[rulei]: # we remembered which rule matches "old"
                                    wmitemcondi=gl.WM.cp[wmitem].kb_rules[rulei][1]
                            if wmitemcondi == int(indexitem[:indexitem.find("p=")]):    # this is teh first match, left to p=
                                indexnow = int(gl.WM.cp[wmitem].p)
                    pep="p=p"
                    indexlist[int(indexitem[indexitem.find(pep)+3:])] = indexnow    #serial number of index is right to p=p
                except:
                    gl.log.add_log(("ERROR lookup_Rtable: could not get indices for reasoning table. Rule:",gl.KB.cp[rule[0]].mentstr," indices found:",indexlist))
        try:
            reasoned_p = gl.args.pmap[rtable[(rtable.find("=")+1):]]        #not yet p, but the entire table
            for index in indexlist:                                         #take indices one by one
                reasoned_p = reasoned_p[index]
        except:
            gl.log.add_log(("ERROR in lookup_Rtable: could not read p,map reasoning table. Table name not given or wrong, no =, too many indices, or too big index values. Rule:",gl.KB.cp[rule[0]].mentstr," Table name:",rtable," indexc attempted:",indexlist))
        return reasoned_p

    def reason_Inhibit (self,reasoned_rel,reasoned_parents):     #check reasoned concept to stop stupid reasoning
        inhibit=0
        parent1=reasoned_parents[0]
        allsame=1
        for pind in range(len(reasoned_parents)):
            if pind!=0:
                p2=reasoned_parents[pind]
                same = gl.WM.rec_match(gl.WM.cp[parent1],gl.WM.cp[p2], [parent1,p2])   # compare parents whether they are the same
                if same != 1: allsame=0                                 # a single difference is enough
        if allsame==1:                                                  # if concept parents are all the same      
            if reasoned_rel==2 or reasoned_rel==3 or reasoned_rel==4:   #S,D,C relation
                inhibit=1                                               #inhibit D(x,x) C(x,x) etc
        return inhibit

    def generate_MultiConcept(self,new,old,rulei,wmpi):     #create reasoned concept if condition is AND()
        # rulei is the index to be used both in kb_rules and rule_match
        # wmpi is the index of wm pack in rule_match[rulei]
        rule=gl.WM.cp[old].kb_rules[rulei]
        implication=gl.KB.cp[rule[0]].parent[1]         #implication in KB
        condition=rule[1]                               #condition portion in KB that corresponds to "old" WM concept
        newparent=[]
        celem = gl.KB.cp[condition].parent[:]           # words or subconcepts in this condition portion
        celem.append(condition)                         # add this entire condition portion as if it was a word
        for cparenti in range(len(celem)):              #take condition portion of "old"
            for imparenti in range(len(gl.KB.cp[implication].parent)):  #walk on combinitaions of condition-implication parents
                if len(newparent)<imparenti+1: newparent.append(-1)     #newparent has elemets for implication parents
                cstr=gl.KB.cp[celem[cparenti]].mentstr  # %1 or the entire condition portion
                imstr=gl.KB.cp[gl.KB.cp[implication].parent[imparenti]].mentstr
                if cstr==imstr:                                     #%1 == %1 or we have the same concept in the implication too
                    condiinstance = gl.WM.cp[old].parent[:]         # same in WM
                    condiinstance.append(old)
                    newparent[imparenti]=condiinstance[cparenti]     #get the proper content of the condition
        for wmitem in gl.WM.cp[old].rule_match[rulei][wmpi]:        #take concepts of wm pack - these are conditions
            ruleset=gl.WM.cp[wmitem].kb_rules                       #next matching rule set
            for rule_wmitem in ruleset:                             #all matching rules
                if rule_wmitem[0]==rule[0]:                         #same as our current rule for reasoning (on IM level)
                    condition=rule_wmitem[1]
                    celem=gl.KB.cp[condition].parent[:]
                    celem.append(condition)
                    #last condition will be taken if the concept has multiple items for same IM level rule
            for cparenti in range(len(celem)):
                for imparenti in range(len(gl.KB.cp[implication].parent)):  #combinations of condition and impl parents
                    if len(newparent)<imparenti+1: newparent.append(-1)     #newparent elements must match implication parents
                    if gl.KB.cp[celem[cparenti]].mentstr==gl.KB.cp[gl.KB.cp[implication].parent[imparenti]].mentstr:
                        condiinstance=gl.WM.cp[wmitem].parent[:]
                        condiinstance.append(wmitem)
                        newparent[imparenti]=condiinstance[cparenti]                            #if %1=%1 get condition parent into implication
        condicount=len(gl.KB.cp[gl.KB.cp[rule[0]].parent[0]].parent)                            #how many conditions are there
        if len(gl.WM.cp[old].rule_match[rulei][wmpi])+1==condicount and (-1 not in newparent):  #we have the full concept
            reasoned_p=self.lookup_Rtable(new,old,rulei,wmpi,implication,newparent[:])          #read p value from reasoning table
            inhibit = self.reason_Inhibit(gl.KB.cp[implication].relation,newparent)             # inhibit reasoning of D(x,x) etc
            if 0==inhibit:                                                                      #concept not inhibited (found is investigated in finaladd_Concept)
                clist=[new,old]                                             #create list of concepts used for this reasoning
                for olditem in gl.WM.cp[old].rule_match[rulei][wmpi]:       #further concepts used
                    if olditem not in clist: clist.append(olditem)
                self.finaladd_Concept(clist[:],reasoned_p,gl.KB.cp[implication].relation,newparent,rule)           #add the new concept to WM


    def generate_IMconcept(self,new,rule,implication,condition,condi_p=-1): # handle the rule IM(IM(%1,%2),%2) normal implication. TO DO: call finaladd.
        if len(gl.KB.cp[condition].parent)==2:          # IM() has a single condition and a single implication TO DO: multiple implications
            if "%" in gl.KB.cp[gl.KB.cp[condition].parent[0]].mentstr:      # % in IM(%1,%2)
                if gl.KB.cp[gl.KB.cp[condition].parent[1]].mentstr == gl.KB.cp[implication].mentstr:  # %2 in IM(IM(%1,%2),%2). The rule is now identified.
                    if condi_p==-1:                     # called from generate_uniconcept: the IM rule is found in WM
                        index1 = int(gl.WM.cp[gl.WM.cp[new].parent[0]].p)   # parent of IM is the condition. Its p value was earlier matched to the
                                                                            # last occurance of this concept in WM, if present. So p is correctly taken.
                        clist = [gl.WM.cp[new].parent[0]]
                    else:                               # called from enter_RuleMatch: the condition was now found, the IM is older. Now "new" has the IM.
                        index1 = int(condi_p)           # the condition p value is explicitley submitted to this function.
                        clist = [gl.WM.ci]
                    index2 = int(gl.WM.cp[new].p)       # p value of IM. That is always the secong index in the im reasoning table.
                    clist.append(new)                   # list of concepts used for this reasoning
                    try: reasoned_p = gl.args.im[index1][index2]     # the table name "im" is hardcoded here.
                    except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.im could not be accessed. Indices attempted:",index1,index2))
                    reasoned_concept = gl.WM.cp[new].parent[1]      # the second parent of IM is the implication that we want to reason now.
                    matching=0
                    inhibit = self.reason_Inhibit(gl.KB.cp[implication].relation,gl.WM.cp[reasoned_concept].parent)      #inhibit if needed
                    if condi_p!=-1:                     # if we found the condition, we may not add the implication again
                        matching = gl.WM.search_fullmatch(reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule)  #this is probably ok: we may not reason in case we would have a new p value!!
                    if 0==inhibit and 0==matching and reasoned_p!=gl.WM.convert_p(gl.args.pmax/2):     # we do not reason if p will be 0.5
                        self.finaladd_Concept(clist[:],reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent,rule)
                        if condi_p==-1:                 # IM was the last concept we found
                            gl.WM.cp[gl.WM.cp[new].parent[1]].p = gl.WM.convert_p(reasoned_p)   # set reasoned p value in IM parent occurance too. Consistency.
                            gl.log.add_log(("PVALUE set in generate_IMconcept: implication p=",reasoned_p," in WM concept:",gl.WM.cp[new].parent[1] ))
                     
    def visit_concept(self,db,curri,visitmap,nextp=0):      # recursive walk over db from curri towards parents. Call without nextp.
        s=timer()
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.visit_concept(db,db.cp[curri].parent[nextp],visitmap,0)        # go down to parent
            nextp=nextp+1                                                       # next parent
        visitmap.append([curri, db.cp[curri].mentstr])                          # visitmap is a flattened representation of teh context
        gl.args.settimer("reason_901: visit_concept",timer()-s)

    def check_condition(self, visitnew, visitcond):         # check that condition %1 %2 etc and words in WM (new) do match
        s=timer()
        if len(visitnew)!=len(visitcond): return {}         # length do not match, BAD
        condimap={}                                         # condition KB string mapped to index in WM
        for item in range(len(visitcond)):                  # walk in condition parents
            if gl.KB.cp[visitcond[item][0]].relation!=gl.WM.cp[visitnew[item][0]].relation:
                return {}                                   # relation do not match, BAD
            try:                                            # try read this condition %1
                if gl.WM.cp[condimap[visitcond[item][1]]].mentstr != visitnew[item][1]:    # will not run if this i sfirst occurence of %1
                    return {}                               # not first occurence and %1 does not match: BAD
            except:                                         # first occurence of %1 or %2 etc
                condimap[visitcond[item][1]] = visitnew[item][0]    # add it to the mapping, %1 etc string mapped to index in WM
        gl.args.settimer("reason_902: check_condition",timer()-s)
        return condimap

    def build_concept(self,db,curri,condimap,conclist,reasoned_p,rule,nextp=0):     #recursive build of reasoned concept starting with parents
        # TO DO: enable word in this implication. Not only %1 %2 etc.
        if nextp==0 and db.cp[curri].relation!=1: self.imparents.append([])     # curri is the index of the implication in KB
        while (len(db.cp[curri].parent)>0 and nextp<len(db.cp[curri].parent)):  # walk nto finished over parents on same level
            self.build_concept(db,db.cp[curri].parent[nextp],condimap,conclist,reasoned_p,rule,0)
            nextp=nextp+1
        if db.cp[curri].relation==1:
            self.imparents[-1].append(condimap[db.cp[curri].mentstr])           # collect parents for a concept that has words as parents
        thispnum=len(db.cp[curri].parent)
        if thispnum == len(self.imparents[-1]):                                 # detect that all parents are in place
            self.recordparents.append(self.imparents.pop())                     # remove added fraction parents and record them
            self.recordrel.append(db.cp[curri].relation)                        # record the relation
            self.imcount+=1                                                     # count the concepts added
            if len(self.imparents)>0:                                           # not yet complete
                self.imparents[-1].append(-1*self.imcount)                      # notify finaladd to use some previous concept as parent
            if len(self.imparents)==0:                                          # detect that last concept was added
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
        if len(condimap)>0:                                 # successful match of condition and new
            if len(rtable)!=0:                              # reasoning table exist
                try: reasoned_p=gl.args.pmap[rtable[(rtable.find("=")+1):]][int(gl.WM.cp[new].p)]   #index is p value of condition in WM
                except:
                    gl.log.add_log(("ERROR generate_Uniconcept: could not read pmap reasoning table. Too few dimensions? Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable," index attempted:",int(gl.WM.cp[new].p)))
                if type(reasoned_p) is list:                # error message for too many dimensions
                    gl.log.add_log(("ERROR generate_Uniconcept: bad pmap reasoning table: Too many dimensions! Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable," index attempted:",int(gl.WM.cp[new].p)))
            self.imparents=[]; self.recordparents=[]
            self.recordrel=[]; self.imcount=0
            self.build_concept(gl.KB, implication, condimap, [new][:], reasoned_p,rule)   # call finaladd_Concept for several concepts
        if len(newparent) == 0 and gl.KB.cp[rule[1]].relation == 13:    # rule portion is IM, the implication in rule is just %2
            self.generate_IMconcept(new,rule,implication,condition)     # this is hard-wired for rule: IM(IM(%1,%2),%2)

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
        gl.args.settimer("reason_011: finaladd_RuleMatch", timer()-s)     # measure execution time
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
            
                
    def enter_RuleMatch(self,new,old,enable):           # enable: will cause reasoning be skipped if concept is argument of an IM() relation
        s=timer(); orulei=0
        for ruleold in gl.WM.cp[old].kb_rules:              #all rules already added to old concept
            for rulenew in gl.WM.cp[new].kb_rules:          #all pairs with the latest concept
                if ruleold[0]==rulenew[0]:                  #IM level rule is th same
                    if rulenew[1] not in ruleold:            #the new condition is not the same what we already had in old concept
                        finalmatch=self.final_RuleMatch(new,old,rulenew,ruleold)    #%1 %2 etc must mean the same thing in new and old
                        if enable==1 and finalmatch==1 and (new not in gl.WM.cp[old].rule_match[orulei]):     #not skipped, and new not in WM pack
                            self.append_Match(new,old,rulenew,ruleold,orulei)                   #add new to the current wm pack
                                        
                # this might be the condition of an earlier IM concept. This has nothing in kb_rules for this.
            if gl.KB.cp[ruleold[1]].relation==13:       #for old, the matching rule's condition is IM, as in IM(IM(%1,%2),%2)
                if gl.WM.cp[old].relation==13:          #redundant for WM
                    if gl.WM.cp[new].relation==gl.WM.cp[gl.WM.cp[old].parent[0]].relation:  #condition in old IM() matches the new concept's relation
                        p2=gl.WM.cp[old].parent[0]
                        if gl.WM.rec_match(gl.WM.cp[new],gl.WM.cp[p2],[new,p2])==1:    # this is exactly the condition
                            gl.WM.cp[old].rule_match[orulei].append([new])   # for debugging and logging, remember the condition now found in "old"
                            implication=gl.KB.cp[ruleold[0]].parent[1]       # implication part of the rule for "old"
                            condition=gl.KB.cp[ruleold[0]].parent[0]         # condition part of the rule
                            condi_p = gl.WM.cp[new].p                        # p value of teh condition, which was found now
                            self.generate_IMconcept(old,ruleold,implication,condition,condi_p)  # reason the implication now
                                    
            orulei+=1
        gl.args.settimer("reason_010: enter_RuleMatch", timer()-s)     # measure execution time
    
 
    
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


    def reset_Currentmapping(self,oldment):                 # delete words from currentmapping that are not in the current row
        owords=self.get_Wordinment(oldment)                 # words of current row
        curmap = self.currentmapping.copy()
        owordlist=[]
        for ow in owords:
            owordlist.append(ow[0])                         # current words in sentence
        for mw in curmap:
            if mw not in owordlist:                         # keep only words of old sentence
                del self.currentmapping[mw]                 # delete words not in old sentence
        
    def create_Branchlist(self):
        if gl.WM.branch==[]:            #no branching happened so far
            br=[gl.WM.ci]               #last concept is the only leaf
        else:
            br=gl.WM.branch[:]          #stored branches copy
        return br

    def mapping_Insert(self,qmentalese):                    #insert some D(x) relations before question to force mapping
        #this is needed for any question if we want to do mapping for some words of the question
        #otherwise questions are skipped for reasoning and thereby for mapping too
        toinsert=""
        gl.reasoning.question_specific_words=[]
        wordlist=self.get_Wordinment(qmentalese[:])         #get all words of the question
        for word in wordlist:
            maprule=gl.WM.get_Maprules(-1,word[0])
            if maprule!=[]: toinsert="D(" + word[0]+word[1] + ")"      #assemble D(x) using g-value as well
            if toinsert!="":                                    #D(x) to be inserted
                gl.WM.branch_read_concept(0,[toinsert],0)       #insert on all living branches
                gl.log.add_log(("QUESTION WORD added for mapping on index:",gl.WM.ci," concept added:",gl.WM.cp[gl.WM.ci].mentstr))
                toinsert=""
                branches = self.create_Branchlist()             #add gl.WM.ci if needed
                for br in branches:                             #all living bfranches where D(x) has been added
                    gval=gl.WM.cp[br-1].g                       # g value of word
                    if gval == gl.args.gmin:                    # gvalue=0, specific
                        gl.reasoning.question_specific_words.append([word[0],br-1]) # record the index of g=0 word
            
    def insert_Drel(self,starti,qmentalese):                # insert a D(x) relation to force mapping, by calling mapping_Insert
        nqflag=False                                        # no D(x) insertion is default
        if qmentalese!="":                                  # means that next row is a question
            nqflag=True
            if starti==gl.WM.ci:                            # no other reasoning necessary
                self.mapping_Insert(qmentalese)             # insert D(x)
                nqflag=False                                # do not insert again
        return nqflag
            
    def perform_Reason(self, starti, lasti, nqflag, next_question):
        s=timer()
        try: nextrelation = gl.WM.cp[lasti-1].relation      # to test if this is an argument of an IM relation
        except: nextrelation=-2                             # because if YES we may want to disable reasoning
        for wm_pos in range(starti,lasti):
            enable=0; is_a_parent=0
            if nextrelation == 13:                          # next concept is IM()
                if gl.WM.cp[wm_pos].relation!=1:            # not a word
                    is_a_parent=1                           # this is a portion of the latestbrelation
            if nextrelation!=13 or is_a_parent==0:          # this is not the argument of an IM relation
                enable=1                                    # we enable reasoning now
            if wm_pos>gl.reasoning.reason_processed:        # not yet processed for reasoning
                gl.reasoning.reason_processed=wm_pos        # set as processed 
                self.brancho = [branch.Branch(wm_pos)]      # store the branch object
                self.relevant_branch = self.brancho[0].select_Relevant(wm_pos)   #collect branches on which wm_pos is present
                if self.relevant_branch!=[]:                # reason only if wm_pos is on a living branch
                    thisbranch = self.brancho[0].get_previous_concepts(wm_pos)   #all concepts in the branch 
                    self.brancho[0].perform_Branching(thisbranch)         # perform mapping
                    self.convert_KBrules(wm_pos,1)          # converts the rule fractions in kb_rules to [imlevel,condition] list
                                                            # also calls the addition of reasoned concept to WM if condition is not AND
                    cnum = len(thisbranch)-1                # counter backwards
                    while cnum>=0:                          # for all old concepts in branch try to get a match for rules with multiple condition
                        if gl.WM.cp[wm_pos].wmuse!=[-2]:    # do not reason if concept is parent of a reasoned concept
                            self.brancho[0].update_Consistency(wm_pos,thisbranch[cnum])     # update consistency of wm_pos
                            self.enter_RuleMatch(wm_pos,thisbranch[cnum],1)                 #1.completes rule_match list  2.adds new reasoned concept to WM
                        cnum-=1
                    self.brancho[0].evaluate_Branches(wm_pos)       # update consistency for branches thathave wm_pos included
        if nqflag: self.mapping_Insert(next_question)       # insert D(x) before questions on relevant branches
        self.brancho[0].compare_Branches()                  # after reasoning complete, we try to kill some bad branches
        gl.args.settimer("reason_000: perform_reason", timer()-s)     # measure execution time
        
            
