import gl, conc, branch

# TO DO: X-relation
# TO DO: XOR((%1)p=p1,%2) this p value should work
# TO DO: NOT() relation
# TO DO: N() rule - necessary condition
#TO DO: make uniconcept work for compound concepts

class Reasoning:
    def __init__(self):
        self.actual=0
        self.reason_processed=0         # last indec in gl:WM.cp that was processed for reasoning
        self.brancho = []               # here we store the current branching object
        self.relevant_branch = []       # list of branches for current reasoning
        self.mapping_processed=0

    #This method checks if the 2 indexes from WM and KB matches (in syntax, not in each word).
    def do_they_match_for_rule(self, wm_index, kb_index):
        if gl.KB.cp[kb_index].relation == 1 and "%" in gl.KB.cp[kb_index].mentstr:  #also finds rules where %1 refers to an entire concept
            return True
        rule_relation=gl.KB.cp[kb_index].relation
        if rule_relation==-1 or rule_relation==gl.WM.cp[wm_index].relation:         #handles X concept - X must be the last concept in rule condition
            if len(gl.WM.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(gl.WM.cp[wm_index].parent)):
                return self.do_they_match_for_rule(gl.WM.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j])
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

    def finaladd_Concept(self,conclist,reasoned_p,relation,newparent,rule):     # single function to add reasoned concept to WM
        #TO DO: generate_IMconcept should call this too
        new=conclist[0]         #new concept of reasoning basis - the latest reason used
        self.relevant_branch = self.brancho[0].select_Relevant(new)     #collect branches on which new can be found
        for leaf in self.relevant_branch:       # on all leafs where the reasoned concept must be added
            thisbranch = self.brancho[0].get_previous_concepts(leaf)    #next entire branch
            found = gl.WM.search_fullmatch(reasoned_p, relation,newparent, thisbranch)      #see whether the concept is already on the branch
            if found == 0:
                gl.WM.add_concept(reasoned_p, relation,newparent)       #add the reasoned concept
                gl.WM.cp[gl.WM.ci].previous = leaf
                if leaf in gl.WM.branch:                #we may need to update global leaf list
                    gl.WM.branch.remove(leaf)
                    gl.WM.branch.append(gl.WM.ci)       #upadted
                if gl.WM.ci>0 and gl.WM.cp[gl.WM.ci-1].next == gl.WM.ci:    #earlier concept is also pointing here, ERROR
                    if gl.WM.cp[gl.WM.ci].previous != gl.WM.ci-1:           #next needs to be corrected
                        gl.WM.cp[gl.WM.ci-1].next = []  #that needs to be a leaf
                gl.log.add_log(("REASONED concept added! input new,old:",conclist," on branch leaf:",leaf," on index:",gl.WM.ci," rule:",rule," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr, " p=",reasoned_p," parents:",gl.WM.cp[gl.WM.ci].parent))
                gl.WM.cp[leaf].next = [gl.WM.ci]        #old leaf continued
                
    

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

    def reason_Inhibit (self,reasoned_p,reasoned_rel,reasoned_parents):     #check reasoned concept to stop stupid reasoning
        inhibit=0
        parent1=reasoned_parents[0]
        allsame=1
        for parent in reasoned_parents:
            if parent != parent1: allsame=0            #if not very same concept then not same
        if allsame==1:
            if reasoned_rel==2 or reasoned_rel==3 or reasoned_rel==4:   #S,D,C relation
                inhibit=1
        if reasoned_rel==4:                             #C relation, even if parents are different
            inhibit=1
            for parent in reasoned_parents:
                if gl.WM.cp[parent1].relation==1 and gl.WM.cp[parent].relation==1:      #C parents are words
                    if gl.WM.cp[parent1].kblink[0] != gl.WM.cp[parent].kblink[0]:       #not same words
                        inhibit=0
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
            inhibit = self.reason_Inhibit(reasoned_p, gl.KB.cp[implication].relation,newparent) # inhibit reasoning of D(x,x) etc
            if 0==inhibit:                                                                      #concept not inhibited (found is investigated in finaladd_Concept)
                self.finaladd_Concept([new,old],reasoned_p,gl.KB.cp[implication].relation,newparent,rule)           #add the new concept to WM


    def generate_IMconcept(self,new,rule,implication,condition,condi_p=-1): # handle the rule IM(IM(%1,%2),%2) normal implication. TO DO: call finaladd.
        if len(gl.KB.cp[condition].parent)==2:          # IM() has a single condition and a single implication TO DO: multiple implications
            if "%" in gl.KB.cp[gl.KB.cp[condition].parent[0]].mentstr:      # % in IM(%1,%2)
                if gl.KB.cp[gl.KB.cp[condition].parent[1]].mentstr == gl.KB.cp[implication].mentstr:  # %2 in IM(IM(%1,%2),%2). The rule is now identified.
                    if condi_p==-1:                     # called from generate_uniconcept: the IM rule is found in WM
                        index1 = int(gl.WM.cp[gl.WM.cp[new].parent[0]].p)   # parent of IM is the condition. Its p value was earlier matched to the
                                                                            # last occurance of this concept in WM, if present. So p is correctly taken.
                    else:                               # called from enter_RuleMatch: the condition was now found, the IM is older. Now "new" has the IM.
                        index1 = int(condi_p)           # the condition p value is explicitley submitted to this function.
                    index2 = int(gl.WM.cp[new].p)       # p value of IM. That is always the secong index in the im reasoning table.
                    try: reasoned_p = gl.args.im[index1][index2]     # the table name "im" is hardcoded here.
                    except: gl.log.add_log(("ERROR in generate_IMconcept: reasoning table gl.args.im could not be accessed. Indices attempted:",index1,index2))
                    reasoned_concept = gl.WM.cp[new].parent[1]      # the second parent of IM is the implication that we want to reason now.
                    matching=0
                    inhibit = self.reason_Inhibit(reasoned_p,gl.KB.cp[implication].relation,gl.WM.cp[reasoned_concept].parent)      #inhibit if needed
                    if condi_p!=-1:                     # if we found the condition, we may not add the implication again
                        matching = gl.WM.search_fullmatch(reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent)  #this is probably ok: we may not reason in case we would have a new p value!!
                    if 0==inhibit and 0==matching and reasoned_p!=gl.WM.convert_p(gl.args.pmax/2):     # we do not reason if p will be 0.5
                        gl.WM.add_concept(reasoned_p, gl.WM.cp[reasoned_concept].relation, gl.WM.cp[reasoned_concept].parent)
                        gl.log.add_log(("REASON generate_IMconcept. IM:",new," WM pos:",gl.WM.ci," condition p=",condi_p," im table indices:",index1,index2," reasoned concept:",gl.WM.cp[gl.WM.ci].mentstr," p=",reasoned_p))
                        if condi_p==-1:                 # IM was the last concept we found
                            gl.WM.cp[gl.WM.cp[new].parent[1]].p = gl.WM.convert_p(reasoned_p)   # set reasoned p value in IM parent occurance too. Consistency.
                            gl.log.add_log(("PVALUE set in generate_IMconcept: implication p=",reasoned_p," in WM concept:",gl.WM.cp[new].parent[1] ))
                     
            

    def generate_UniConcept(self,new,rule):         #add reasoned concept to WM if condition is a single concept
        implication=gl.KB.cp[rule[0]].parent[1]
        condition=gl.KB.cp[rule[0]].parent[0]
        cpalist=gl.KB.cp[condition].parent[:]
        impalist=gl.KB.cp[implication].parent[:]
        try: rtable=gl.KB.cp[rule[0]].rulestr[0][:]         #first string on IM level is the table name
        except: print ("ERROR: RULES MUST HAVE TABLE!",gl.KB.cp[rule[0]].mentstr)
        reasoned_p=1
        newparent=[]                                        #this will hold the parents of the reasoned concept
        for cparenti in range(len(cpalist)):                #TO DO: make work for compound concepts. take %1 %2 etc arguments of the condition
            for imparenti in range(len(impalist)):          #all combinations with %1 %2 etc of implication
                if len(newparent)<imparenti+1: newparent.append(-1)     #implication parents placeholder
                if gl.KB.cp[cpalist[cparenti]].mentstr==gl.KB.cp[impalist[imparenti]].mentstr:      #we found %1==%1
                    try:newparent[imparenti]=gl.WM.cp[new].parent[cparenti]     #DEBUG get the proper condition concept into the implication
                    except:gl.log.add_log(("ERROR Uniconcept newparent index error"))
        if len(newparent)>0 and (-1 not in newparent):              #we have the full implication, it must have parent(s)
            if len(rtable)!=0:                                      #reasoning table exists
                try: reasoned_p=gl.args.pmap[rtable[(rtable.find("=")+1):]][int(gl.WM.cp[new].p)]   #index is p value of condition in WM
                except:
                    gl.log.add_log(("ERROR generate_Uniconcept: could not read pmap reasoning table. Rule:",gl.KB.cp[rule[0]].mentstr," table name:",rtable," index attempted:",int(gl.WM.cp[new].p)))
            inhibit = self.reason_Inhibit(reasoned_p, gl.KB.cp[implication].relation,newparent)
            if 0==inhibit:   #this concept is not inhibited
                self.finaladd_Concept([new],reasoned_p,gl.KB.cp[implication].relation,newparent,rule)           #add it to WM
        if len(newparent) == 0 and gl.KB.cp[rule[1]].relation == 13:    # rule portion is IM, the implication in rule is just %2
            self.generate_IMconcept(new,rule,implication,condition)     # this is hard-wired for rule: IM(IM(%1,%2),%2)


    def final_RuleMatch(self,new,old,rulenew,ruleold):      #%1 %2 etc must mean the same thing in new and old
        finalmatch=1; oparenti=0
        for oparent in gl.KB.cp[ruleold[1]].parent:        #%1 %2 etc level in the condition of old concept
            nparenti=0
            for nparent in gl.KB.cp[rulenew[1]].parent:
                ostring=gl.KB.cp[oparent].mentstr          #%1 string in old
                nstring=gl.KB.cp[nparent].mentstr          #%1 string in new
                if ostring[0]=="%":                         #currently works for % only
                    if ostring==nstring:                    #we found a pair that should match, now let us see whether it matches
                        thismatch=gl.WM.rec_match(gl.WM.cp[gl.WM.cp[new].parent[nparenti]],gl.WM.cp[gl.WM.cp[old].parent[oparenti]])
                        if thismatch==0: finalmatch=0       #a single non-match causes comparison to fail
                nparenti+=1
            oparenti+=1
        return finalmatch

    def append_Match(self,new,old,rulenew,ruleold,orulei):  #append "new" to old's rule_match wm pack on orulei
        wmpi=0; stored=[]
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

    def select_Rule(self,imlevel,rulelist):                 #find the last matching rule
        found=[]
        for rule in rulelist:
            if rule[0]==imlevel:
                found=rule[:]
        return found
            
                
    def enter_RuleMatch(self,new,old,enable):           # enable: will cause reasoning be skipped if concept is argument of an IM() relation
        orulei=0
        for ruleold in gl.WM.cp[old].kb_rules:              #all rules already added to old concept
            for rulenew in gl.WM.cp[new].kb_rules:          #all pairs with the latest concept
                if ruleold[0]==rulenew[0]:                  #IM level rule is th same
                    if rulenew[1] not in ruleold:            #the new condition is not the same what we already had in old concept
                        finalmatch=self.final_RuleMatch(new,old,rulenew,ruleold)    #%1 %2 etc must mean the same thing in new and old
                        if enable==1 and finalmatch==1 and (new not in gl.WM.cp[old].rule_match[orulei]):     #not skipped, and new not in WM pack
                            self.append_Match(new,old,rulenew,ruleold,orulei)                   #add new to the current wm pack
                        if finalmatch==0:                   #nonmatching pair found, we must do a check
                            for checkwm in range(0,new):    #NOT OPTIMAL: entire older WM
                                for rmi in range(len(gl.WM.cp[checkwm].rule_match)):
                                    if old in gl.WM.cp[checkwm].rule_match[rmi]:    #older member of nonmatching pair included
                                        try: gl.WM.cp[checkwm].rule_match[rmi].remove(new)  #try remove new because of nonmatch
                                        except: y=0
                                        
                # this might be the condition of an earlier IM concept. This has nothing in kb_rules for this.
            if gl.KB.cp[ruleold[1]].relation==13:       #for old, the matching rule's condition is IM, as in IM(IM(%1,%2),%2)
                if gl.WM.cp[old].relation==13:          #redundant for WM
                    if gl.WM.cp[new].relation==gl.WM.cp[gl.WM.cp[old].parent[0]].relation:  #condition in old IM() matches the new concept's relation
                        if gl.WM.rec_match(gl.WM.cp[new],gl.WM.cp[gl.WM.cp[old].parent[0]]):    # this is exactly the condition
                            gl.WM.cp[old].rule_match[orulei].append([new])   # for debugging and logging, remember the condition now found in "old"
                            implication=gl.KB.cp[ruleold[0]].parent[1]       # implication part of the rule for "old"
                            condition=gl.KB.cp[ruleold[0]].parent[0]         # condition part of the rule
                            condi_p = gl.WM.cp[new].p                        # p value of teh condition, which was found now
                            self.generate_IMconcept(old,ruleold,implication,condition,condi_p)  # reason the implication now
                                    
            orulei+=1
                        

    def perform_Reason(self, starti, lasti):
        try: nextrelation = gl.WM.cp[lasti-1].relation      # to test if this is an argument of an IM relation
        except: nextrelation=-2                             # because if YES we may want to disable reasoning
        for wm_pos in range(starti,lasti):
            enable=0; is_a_parent=0
            if nextrelation == 13:                          # next concept is IM()
                if gl.WM.cp[wm_pos].relation!=1:            # not a word
                    is_a_parent=1                           # this is a portion of the latestbrelation
            if nextrelation!=13 or is_a_parent==0:          # this is not the argument of an IM relation
                enable=1                                    # we enable reasoning now
            if wm_pos>gl.reasoning.reason_processed:       # not yet processed for reasoning
                gl.reasoning.reason_processed=wm_pos        # set as processed 
                self.brancho = [branch.Branch(wm_pos)]      # store the branch object
                self.brancho[0].perform_Branching()         # perform mapping
                thisbranch = self.brancho[0].get_previous_concepts(wm_pos)   #all concepts in the branch
                self.convert_KBrules(wm_pos,1)              #converts the rule fractions in kb_rules to [imlevel,condition] list
                                                            #also calls the addition of reasoned concept to WM if condition is not AND
                cnum = len(thisbranch)-1                    # counter backwards
                while cnum>=0:                   #for all old concepts in branch try to get a match for rules with multiple condition
                    self.enter_RuleMatch(wm_pos,thisbranch[cnum],1)        #1.completes rule_match list  2.adds new reasoned concept to WM
                    cnum-=1
                self.brancho[0].evaluate_Branches()         # calculate consistency for branches
            
