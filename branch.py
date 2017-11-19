import gl

class Branch:           #branching in WM

    def __init__(self,wmpos):
        self.wmpos=wmpos        #position in WM where branching is considered
        self.mapped=[]
        self.oldbranch=[]
        self.branchesnow=[]

    def get_previous_concepts(self,beforei):            # returns the id list of previous concepts (inclusive)
        previous_concepts = []
        curri = beforei
        while curri != -1:
            previous_concepts.append(curri)
            curri = gl.WM.cp[curri].previous
        return previous_concepts

    def search_previously(self,whati, beforei):        # returns True if the id (whati) appears previously on the branch (before beforei)
        curri = beforei
        while curri != -1:
            if curri == whati:
                return True
            curri = gl.WM.cp[curri].previous
        return False
    
    def search_on_branch(self,whati, branchi):
        # returns True if the id (whati) appears on the branch
        # in fact when whati and branchi are on the same branch, i.e. in the same 'domain'
        return search_previously(whati, branchi) or search_previously(branchi, whati)

    def rec_get_next_concepts(self,rooti):              # returns the id list of all next concepts (starting from rooti, inclusive)
        next_concepts = [rooti]
        for i in gl.WM.cp[rooti].next:
            next_concepts.extend(rec_get_next_concepts(i))
        return next_concepts
        
    def rec_get_leaves(self,rooti):                     # returns the id list of leaf concepts (starting from rooti, inclusive)
        leaf_concepts = []
        if gl.WM.cp[rooti].is_leaf():
            leaf_concepts.append(rooti)
        else:
            for i in gl.WM.cp[rooti].next:
                leaf_concepts.extend(rec_get_leaves(i))
        return leaf_concepts
    
    def rec_print_tree(self,rooti, printchildren = False, level = 0):          # prints the tree recursively (starting from rooti, inclusive) 
        print("." * (level * 3) + str(rooti) + 
            ((" (children: " + str(gl.WM.cp[rooti].child) + ")") if printchildren and len(gl.WM.cp[rooti].child)>0 else ""));
        for i in gl.WM.cp[rooti].next:
            rec_print_tree(i, printchildren, level + 1)
        
    def remove_branch(self,branchi):
        # removes branch starting from branchi
        # doesn't really remove concepts, only terminates connection in the tree
        # removes ids of next concepts from the child list of previous concepts
        if gl.WM.cp[branchi].previous != -1:
            gl.WM.cp[gl.WM.cp[branchi].previous].next.remove(branchi)
        
            next_concepts_list = rec_get_next_concepts(branchi)
            i = gl.WM.cp[branchi].previous
            while i != -1:
                children_list = gl.WM.cp[i].child[:]
                for childi in children_list:
                    if childi in next_concepts_list:
                        gl.WM.cp[i].child.remove(childi)
                i = gl.WM.cp[i].previous

    def get_previous_sentence_on_branch(self,beforei):       # finds the previous full sentence concept on the branch (before the given id)
        i = gl.WM.cp[beforei].previous                  # the previous sentence concept's id must be before the given id
        while i != -1:
            if len(gl.WM.cp[i].child) == 0:             # a concept is a full sentence concept, if it doesn't have children
                return i
            i = gl.WM.cp[i].previous
        return -1                                       # return -1 if no previous sentence concept available

    def select_Relevant(self,wmpos):        #select all branches in which we have wmpos
        relevant=[]
        for br in gl.WM.branch:
            thisbr=self.get_previous_concepts(br)
            if wmpos in thisbr: relevant.append(br)
        if gl.WM.branch==[]:
            relevant=[gl.WM.ci]
        return relevant

    def get_Maprules(self):                 # find mapping rules for the word on self.wmpos
        maplist=[]
        if gl.WM.cp[self.wmpos].relation==1:    #this is a word
            wpos=gl.WL.find_word(gl.WM.cp[self.wmpos].mentstr)
            word_kb = gl.WL.wcp[wpos].wchild[0]     #word meaning in KB
            rulecount=1
            for child in gl.KB.cp[word_kb].child:
                if gl.KB.cp[child].relation==3:     #D relation
                    #TO DO: further condition: D(he,Q(akn,person))
                    if gl.KB.cp[child].relevance==gl.args.rmax: #top relevant D relation
                        if gl.WM.cp[self.wmpos].mentstr==gl.KB.cp[gl.KB.cp[child].parent[0]].mentstr:  #wmpos word is x in D(x,y)
                            if rulecount==1:    #TO DO now we handle 1 rule only
                                maplist.append(child)
                                rulecount+=1
        return maplist


    def trymap_Single(self,maprule):        #mapping for a single rule
        currentwm=self.wmpos
        rulw=-1
        while currentwm>=0:                 #walk back on branch
            if gl.WM.cp[currentwm].previous>=0:     #we have a previous link
                previwm=gl.WM.cp[currentwm].previous
            else: previwm=currentwm-1
            if previwm<0: break
            currentwm = previwm
            #TO DO: if currentwm is a word, search for C relation in earlier WM and in KB !!
            if gl.WM.cp[currentwm].relation==4:     #C relation needed to try mapping
                ruleword=gl.KB.cp[maprule].parent[1]    # in the rule in KB, second parent is a new word to be added
                if gl.KB.cp[ruleword].relation==1:       #TO DO not only word but concept
                    if gl.KB.cp[ruleword].mentstr != gl.WM.cp[self.wmpos].mentstr:   #avoid D(x,x)?
                        if rulw==-1:        #add rule only once
                            rulw = gl.WM.add_concept(gl.args.pmax,1,[],[ruleword])      #add the word from the rule to WM
                            ruleinwm = gl.WM.add_concept(gl.KB.cp[maprule].p,gl.KB.cp[maprule].relation,[self.wmpos,rulw],[maprule])        #add rule D(x,y) relation to WM
                            gl.log.add_log(("MAPPING: add rule to WM:",gl.KB.cp[ruleword].mentstr," ",gl.KB.cp[maprule].mentstr))
                        self.add_Mapbranch(maprule, currentwm, ruleinwm)  #add branch now!

    def add_Mapbranch(self,maprule,currentwm, ruleinwm):    #add one more branch starting from ruleinwm and expressing D(wmpos,curretwm)
        currentword = gl.WM.cp[currentwm].parent[0]     #on currentwm we have C(x,y) and x is the current word for this mapping
        if currentword not in self.mapped:              #not yet mapped at this ruleinwm
            mapconcept = gl.WM.add_concept(gl.KB.cp[maprule].p, 3, [self.wmpos,currentword])        # mapping added to WM D()
            gl.WM.cp[mapconcept-1].next.remove(mapconcept)      #multiple mapping is not directly following ruleinwm
            gl.log.add_log(("MAPPING: add mapping to WM on index ",gl.WM.ci," concept:",gl.WM.cp[mapconcept].mentstr))
            self.mapped.append(currentword)             #remember this is mapped
            gl.WM.cp[ruleinwm].next.append(mapconcept)  #set next on ruleinwm, to list all branches
            gl.WM.cp[mapconcept].prevoius=ruleinwm      #branch shows back to rule
            gl.WM.branch.append(mapconcept)             #update list of branches
            self.branchesnow.append(mapconcept)
        print ("ADD BRANCH wmpos",self.wmpos,gl.WM.cp[self.wmpos].mentstr,"branches",gl.WM.branch)

    def evaluate_Branches(self):
        return self.oldbranch
    
    def perform_Branching(self):            #creation of new branches
        self.oldbranch = gl.WM.branch[:]    #remember blist of initial branches
        maplist = self.get_Maprules()       #mapping rules list
        for maprule in maplist:
            self.trymap_Single(maprule)
                  
        
                
if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
