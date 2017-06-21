import gl, conc

class Rule:
    def __init__(self,actualconcept):       # an instance represents a single rule to apply for the actual concept
        self.actual = actualconcept         # index of concept in WM for which we found a rule
        self.rule = -1                      # index of rule in KB, an IM(g,k) concept
        self.condition = []                 # indices (in KB) of a,b,c in IM(Z(a,b),k)  . here c=Z(a,b)
        self.match=[]                       # indices of m,n,q in WM, where m matches a, n matches b etc
        self.matchrelation=-2               # if for example b=X(%2,%3) and n matches b, then we store the relation found in m
        self.matchvalue = []                # %1 %2 %3 matching concepts
        self.matchp = []                    # p1 p2 etc matching p values


class Reasoning:
    def __init__(self):
        self.actual=0

    #This method checks if the 2 indexes from WM and KB matches (in syntax, not in each word).
    def do_they_match_for_rule(self, wm_index, kb_index):
        if gl.WM.cp[wm_index].relation == 1 and gl.KB.cp[kb_index].relation == 1:
            wl_index = gl.KB.cp[kb_index].wordlink[0]
            if "%" in gl.WL.wcp[wl_index].word:
                return True
            else:
                return False
        elif gl.WM.cp[wm_index].relation == gl.KB.cp[kb_index].relation:
            if len(gl.WM.cp[wm_index].parent) != len(gl.KB.cp[kb_index].parent):
                return False
            for j in range(0, len(gl.WM.cp[wm_index].parent)):
                return self.do_they_match_for_rule(gl.WM.cp[wm_index].parent[j], gl.KB.cp[kb_index].parent[j])

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

        
    def convert_KBrules(self,new):              #converts the rule fractions in kb_rules to [imlevel,condition] list
        imcombined=[]                           #finds first arg of rule and records all potential matches
        for ruleindex in gl.WM.cp[new].kb_rules:    #low level condition fractions already in kb_rules
            im=[]
            for child in gl.KB.cp[ruleindex].child:
                if gl.KB.cp[child].relation==13:    #IM relation, single condition
                    if ruleindex==gl.KB.cp[child].parent[0]:    #this is the condition, not the implication
                        im.append(child)            #rule on IM level
                        im.append(ruleindex)        #rule condition
                        if im not in imcombined: imcombined.append(im)
                        im=[]
                if gl.KB.cp[child].relation==16:                #this is the AND-relation of the rule condition
                    for andchild in gl.KB.cp[child].child:      #at least 1 child of AND should be IM relation
                        if gl.KB.cp[andchild].relation==13:     #this is the IM relation
                            if child==gl.KB.cp[andchild].parent[0]:     #AND concept is the condition, not implication in IM
                                im.append(andchild)             #rule on IM level
                                im.append(ruleindex)            #rule condition
                                if im not in imcombined: imcombined.append(im)
                                im=[]                                
        gl.WM.cp[new].kb_rules=[]                               #delete old kb_rules content
        for rulei in range(len(imcombined)):                    #copy imcombined to kb_rules and add resoned concept (single condition)
            gl.WM.cp[new].kb_rules.append(imcombined[rulei])
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


    def generate_MultiConcept(self,new,old,rulei,wmpi):     #create reasoned concept if condition is AND()
        # rulei is the index to be used both in kb_rules and rule_match
        # wmpi is the index of wm pack in rule_match[rulei]
        rule=gl.WM.cp[old].kb_rules[rulei]
        implication=gl.KB.cp[rule[0]].parent[1]         #implication in KB
        condition=rule[1]                               #condition portion in KB that corresponds to "old" WM concept
        newparent=[]
        for cparenti in range(len(gl.KB.cp[condition].parent)):     #take condition portion of "old"
            for imparenti in range(len(gl.KB.cp[implication].parent)):  #walk on combinitaions of condition-implication parents
                if len(newparent)<imparenti+1: newparent.append(-1)     #newparent has elemets for implication parents
                cstr=gl.KB.cp[gl.KB.cp[condition].parent[cparenti]].mentstr
                imstr=gl.KB.cp[gl.KB.cp[implication].parent[imparenti]].mentstr
                if cstr==imstr:                                     #%1 == %1
                    newparent[imparenti]=gl.WM.cp[old].parent[cparenti]     #get the proper content of the conmdition
        for wmitem in gl.WM.cp[old].rule_match[rulei][wmpi]:        #take concepts of wm pack - these are conditions
            ruleset=gl.WM.cp[wmitem].kb_rules                       #next matching rule set
            for rule_wmitem in ruleset:                             #all matching rules
                if rule_wmitem[0]==rule[0]:                         #same as our current rule for reasoning (on IM level)
                    condition=rule_wmitem[1]
                    #last condition will be taken if the concept has multiple items for same IM level rule
            for cparenti in range(len(gl.KB.cp[condition].parent)):
                for imparenti in range(len(gl.KB.cp[implication].parent)):  #combinations of condition and impl parents
                    if len(newparent)<imparenti+1: newparent.append(-1)     #newparent elements must match implication parents
                    if gl.KB.cp[gl.KB.cp[condition].parent[cparenti]].mentstr==gl.KB.cp[gl.KB.cp[implication].parent[imparenti]].mentstr:
                        newparent[imparenti]=gl.WM.cp[wmitem].parent[cparenti]          #if %1=%1 get condition parent into implication
        condicount=len(gl.KB.cp[gl.KB.cp[rule[0]].parent[0]].parent)                     #how many conditions are there
        if len(gl.WM.cp[old].rule_match[rulei][wmpi])+1==condicount and (-1 not in newparent):   #we have the full concept
            if 0==gl.WM.search_fullmatch(1,gl.KB.cp[implication].relation,newparent):   #concept not yet in WM
                gl.WM.add_concept(1,gl.KB.cp[implication].relation,newparent)           #add vthe new concept to WM
                gl.log.add_log(("REASON MultiConcept - new input:",new,"old:",old," reasoned:",gl.WM.cp[gl.WM.ci].mentstr," parents:",gl.WM.cp[gl.WM.ci].parent))
                       

    def generate_UniConcept(self,new,rule):         #add reasoned concept to WM if condition is a single concept
        implication=gl.KB.cp[rule[0]].parent[1]
        condition=gl.KB.cp[rule[0]].parent[0]
        cpalist=gl.KB.cp[condition].parent[:]
        impalist=gl.KB.cp[implication].parent[:]
        newparent=[]                                        #this will hold the parents of the reasoned concept
        for cparenti in range(len(cpalist)):                #take %1 %2 etc arguments of the condition
            for imparenti in range(len(impalist)):          #all combinations with %1 %2 etc of implication
                if len(newparent)<imparenti+1: newparent.append(-1)     #implication parents placeholder
                if gl.KB.cp[cpalist[cparenti]].mentstr==gl.KB.cp[impalist[imparenti]].mentstr:      #we found %1==%1
                    newparent[imparenti]=gl.WM.cp[new].parent[cparenti]     #get the proper condition concept into the implication
        if len(newparent)==len(impalist):                   #we have the full implication
            matching=gl.WM.search_fullmatch(1,gl.KB.cp[implication].relation,newparent)
            #print ("ADD new",new,"rule",rule,"impli",implication,"newparent",newparent,"fullmatch?",matching,"origstart",gl.reasoning.actual)
            if 0==matching:   #this concept is not yet in WM
                gl.WM.add_concept(1,gl.KB.cp[implication].relation,newparent)           #add it to WM
                gl.log.add_log(("REASON UniConcept - new input:",new," reasoned:",gl.WM.cp[gl.WM.ci].mentstr," parents:",gl.WM.cp[gl.WM.ci].parent))


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
            newpos=len(gl.WM.cp[old].rule_match[orulei])
            self.add_ReasonedConcept(new,orulei,old,newpos-1)           #again try to add reasoned concept : 2-condition case

    def select_Rule(self,imlevel,rulelist):                 #find the last matching rule
        found=[]
        for rule in rulelist:
            if rule[0]==imlevel:
                found=rule[:]
        return found
            
                
    def enter_RuleMatch(self,new,old):
        orulei=0
        for ruleold in gl.WM.cp[old].kb_rules:              #all rules already added to old concept
            for rulenew in gl.WM.cp[new].kb_rules:          #all pairs with the latest concept
                if ruleold[0]==rulenew[0]:                  #IM level is teh same
                    if rulenew[1] not in ruleold:            #the new condition is not the same what we already had in old concept
                        finalmatch=self.final_RuleMatch(new,old,rulenew,ruleold)    #%1 %2 etc must mean the same thing in new and old
                        if finalmatch==1 and (new not in gl.WM.cp[old].rule_match[orulei]):     #new is not yet in the matching WM pack
                            self.append_Match(new,old,rulenew,ruleold,orulei)                   #add new to the current wm pack
                        if finalmatch==0:                   #nonmatching pair found, we must do a check
                            for checkwm in range(0,new):    #NOT OPTIMAL: entire older WM
                                for rmi in range(len(gl.WM.cp[checkwm].rule_match)):
                                    if old in gl.WM.cp[checkwm].rule_match[rmi]:    #older member of nonmatching pair included
                                        try: gl.WM.cp[checkwm].rule_match[rmi].remove(new)  #try remove new because of nonmatch
                                        except: y=0
            orulei+=1
                        

    def perform_Reason(self, starti, lasti):
        for wm_pos in range(starti,lasti):
            self.convert_KBrules(wm_pos)        #converts the rule fractions in kb_rules to [imlevel,condition] list
                                                #also calls the addition of reasoned concept to WM if condition is not AND
            for allwm in range(0,wm_pos):       #for all old concepts try to get a match for rules with multiple condition
                self.enter_RuleMatch(wm_pos,allwm)   #1.completes rule_match list  2.adds new reasoned concept to WM
            
