import gl
from timeit import default_timer as timer

class Branch:           #branching in WM

    def __init__(self,wmpos):
        self.wmpos=wmpos        #position in WM where branching is considered
        self.mapped=[]
        self.oldbranch=[]
        self.branchesnow=[]
        self.lastbrpos=-1       #last position where branching happened
        self.lastbr_list=[]     #list of concepts of mapping at this last position
        self.map_potential=set()    # words for potential mapping within this paragraph
        self.wordinpara = {}    # kblink-wmpos pairs to show latest occurance of words in the paragraph

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
        return relevant                     #this is empty list if branch of wmpos was killed earlier

    def word_Tomapto(self, thispara, currentwm):            # returns word from the same paragraph that has C(word,...) in WM, before or after
        wmapto=-1
        cmapto=gl.WM.cp[currentwm].parent[0]                # we know this is C relation. take the word in the C relation.
        mapwmuse=gl.WM.cp[cmapto].wmuse                     # for original input wmuse=-1
        if gl.WM.cp[currentwm].relation==4 and mapwmuse==[-1] and int(gl.args.pmax/2)!=gl.WM.cp[currentwm].p:  # C rel orig inp p!=2
            if thispara==1 and gl.WM.cp[cmapto].kblink[0] not in self.map_potential:  # first the C() is found
                if gl.WM.cp[cmapto].relation==1:            # this is a word
                    wmapto=gl.WM.cp[cmapto].mapto           # in .mapto we have either cmapto or the override_parent mapping value
            if gl.WM.cp[cmapto].kblink[0] in self.map_potential:    # the word x in C(x,..) has not crossed paragraph border
                wordpos=self.wordinpara[gl.WM.cp[cmapto].kblink[0]]  # get the latest occurance of the word in paragraph
                wmapto=gl.WM.cp[wordpos].mapto              # in .mapto
        return wmapto                                       # if this is -1 then no word to map to

    def collect_Potential(self,thispara,currentwm):         # if we are still within paragraph, add word to list of potential mapping
        if currentwm in gl.WM.paragraph: thispara=0         # remember if we cross paragraph border
        if gl.WM.cp[currentwm].relation==1 and thispara==1: # we are on a word in the same paragraph
            if gl.WM.cp[currentwm].wmuse==[-1]:             # original input
                if gl.WM.cp[currentwm].kblink[0] not in self.map_potential:     # add wm position only once. TO DO: enable multiple positions.
                    self.wordinpara[gl.WM.cp[currentwm].kblink[0]]=currentwm    # remember latest occurence in paragraph
                self.map_potential.add(gl.WM.cp[currentwm].kblink[0])           # remember kblink as potential word to map to
        return thispara

    def trymap_Single(self,maprule):        #mapping for a single rule
        relevant = self.select_Relevant(self.wmpos)     #all branches where we have wmpos
        currentwm=self.wmpos
        rulw=-1 ; thispara=1                            # flag to show we did not cross paragraph border yet
        while currentwm>=0:                             #walk back on branch
            if gl.WM.cp[currentwm].previous>=0:         #we have a previous link
                previwm=gl.WM.cp[currentwm].previous
            else: previwm=currentwm-1
            if previwm<0: break
            currentwm = previwm
            thispara = self.collect_Potential(thispara,currentwm)       # add currentwm to potential words to map, if so.   
            #TO DO: if currentwm is a word, search for C relation  in KB  (done in earlier WM) !!
            if gl.WM.cp[currentwm].relation==4:                             #C relation needed to try mapping
                wmapto=self.word_Tomapto(thispara,currentwm)                # find out if this C relation has a word to map to
                if wmapto!=-1:      
                    ruleword=gl.KB.cp[maprule].parent[1]                    # in the rule in KB, second parent is a new word to be added
                    if gl.KB.cp[ruleword].relation==1:                      #TO DO not only word but concept
                        if gl.KB.cp[ruleword].mentstr != gl.WM.cp[self.wmpos].mentstr:   #TO DO: avoid D(x,x)?
                            if rulw==-1:                                    #add rule only once
                                rulw = gl.WM.add_concept(gl.args.pmax,1,[],[ruleword])      #add the word from the rule to WM
                                ruleinwm = gl.WM.add_concept(gl.KB.cp[maprule].p,gl.KB.cp[maprule].relation,[self.wmpos,rulw],[maprule])        #add rule D(x,y) relation to WM
                                gl.WM.cp[relevant[0]].next = [rulw]         #continue branch leaf with rulw
                                gl.WM.cp[rulw].previous = relevant[0]
                                gl.WM.cp[rulw].wmuse=[]
                                gl.WM.cp[ruleinwm].wmuse=[]
                                gl.log.add_log(("MAPPING: add rule to WM:",gl.KB.cp[ruleword].mentstr," ",gl.KB.cp[maprule].mentstr))
                            self.add_Mapbranch(maprule, currentwm, ruleinwm, wmapto)  #add branch now!
                            if relevant[0] in gl.WM.branch:                     #we do have some branch already
                                gl.WM.branch.remove(relevant[0])                #remove obsolate branch leaf
                                                                       #TO DO: try update branchvalue too


    def add_Mapbranch(self,maprule,currentwm, ruleinwm,currentword):    #add one more branch starting from ruleinwm and expressing D(wmpos,curretwm)
        if currentword not in self.mapped:              #not yet mapped at this ruleinwm
            mapconcept = gl.WM.add_concept(gl.KB.cp[maprule].p, 3, [self.wmpos,currentword])        # mapping added to WM D()
            gl.reasoning.currentmapping[gl.WM.cp[self.wmpos].mentstr]=self.wmpos    # remembefr mapping happening in this row
            gl.WM.cp[mapconcept].wmuse=[]               #wmuse for a mapping is not -1 but empty
            gl.WM.cp[mapconcept-1].next.remove(mapconcept)      #multiple mapping is not directly following ruleinwm
            gl.log.add_log(("MAPPING: add mapping to WM on index ",gl.WM.ci," concept:",gl.WM.cp[mapconcept].mentstr))
            self.mapped.append(currentword)             #remember this is mapped
            gl.WM.cp[ruleinwm].next.append(mapconcept)  #set next on ruleinwm, to list all branches
            gl.WM.cp[mapconcept].previous=ruleinwm      #branch shows back to rule
            gl.WM.branch.append(mapconcept)             #update list of branches
            self.branchesnow.append(mapconcept)
            gl.log.add_log(("BRANCH ADDED on WM index:",ruleinwm," added branch index:",mapconcept," all branches here:",gl.WM.cp[ruleinwm].next," All branches:",gl.WM.branch))
            print ("ADD BRANCH wmpos",self.wmpos,gl.WM.cp[self.wmpos].mentstr,"branches",gl.WM.branch)

    def kill_Branch(self,leaf,reason):                             # kill this branch
       if leaf in gl.WM.branch:
           gl.WM.branch.remove(leaf)
           try:
               val=gl.WM.branchvalue[leaf]
               del gl.WM.branchvalue[leaf]
               gl.log.add_log(("BRANCH KILLED on leaf index:",leaf," Branch value was:",val," All branches now:",gl.WM.branch,reason))
           except:
               gl.log.add_log(("BRANCH KILLED on leaf index:",leaf," Branch value was: NO VALUE YET"," All branches now:",gl.WM.branch,reason))
       else:                                                       # kill all relevant branches if this is not a leaf
            relbr=self.select_Relevant(leaf)
            leaf=-1
            if len(relbr)==1:                                       # kill only if this is a single branch
                for leaf1 in relbr:
                    if leaf1 in gl.WM.branch:
                        gl.WM.branch.remove(leaf1)
                        try:
                            val=gl.WM.branchvalue[leaf1]
                            del gl.WM.branchvalue[leaf1]            # also delete the branch value entry
                            gl.log.add_log(("BRANCH KILLED. Leaf index killed:",leaf1," branch value was:",val," all branches:",gl.WM.branch," ",reason))
                        except:
                            gl.log.add_log(("BRANCH KILLED. Leaf index killed:",leaf1," branch value was:","NO VALUE"," all branches:",gl.WM.branch," ",reason))
                            

    def compare_Branches(self):                             # find bad branches to be killed
        brmax = 0
        for leaf in gl.WM.branch:                           # get best branch
            if gl.WM.branchvalue[leaf] > brmax:
                brmax = gl.WM.branchvalue[leaf]
        kill_limit = gl.args.branch_kill[brmax]             # limit set in branch_kill parameter table
        for leaf in gl.WM.branch:                           # kill branches below limit
            if gl.WM.branchvalue[leaf] < kill_limit:
                self.kill_Branch(leaf,"Reason: low branch value.")

    def create_Branchlist(self):
        if gl.WM.branch==[]:            #no branching happened so far
            br=[gl.WM.ci]               #last concept is the only leaf
        else:
            br=gl.WM.branch[:]          #stored branches copy
        return br


    def evaluate_Branches(self,wmpos):                          # update consistency of entire branches
        allbr = self.select_Relevant(wmpos)                     #get all branches where we have wmpos
        consi = gl.WM.cp[wmpos].c                               #consistency of this concept
        for leaf in allbr:                                      #for all branches with wmpos
            addc = leaf
            if leaf not in self.oldbranch:                      #leaf has changed, new addition happened in branch
                while addc>-1 and addc not in self.oldbranch:   #walk back until arrive at old branch leaf
                    addc = gl.WM.cp[addc].previous
            try:
                oldvalue=gl.WM.branchvalue[addc]                #previous branchvalue
                del gl.WM.branchvalue[addc]
            except: oldvalue = gl.args.cmax                     #no previous branch value
            if gl.WM.branch!=[]:                                #should be the case
                gl.WM.branchvalue[leaf] = gl.args.branchvalue[oldvalue][consi]  #read branchvalue table by old value and current consistency
        

    def update_Consistency(self,new,old):   # update consistency value for wm item new
        s=timer()
        if new!=old:
            if gl.WM.rec_match(gl.WM.cp[new],gl.WM.cp[old])==1:     #concepts match
                index1 = int(gl.WM.cp[new].p)
                index2 = int(gl.WM.cp[old].p)
                cons = gl.args.consist[index1][index2]              #read the consist table
                if cons<gl.WM.cp[new].c:                            #consistency is worse than stored
                    gl.WM.cp[new].c=cons                            #currently we just store the top inconsistency per concept
        gl.args.settimer("branch_02: update_consistency",timer()-s)

    def get_Lastmulti(self,thisbranch):                 #get position of last branching
        self.lastbrpos=-1
        for pos in thisbranch:                          #this is a reverese list, we go from top to origin
            if len(gl.WM.cp[pos].next)>1 and pos!=self.wmpos:
                if self.lastbrpos==-1: self.lastbrpos=pos
        if self.lastbrpos>-1:                           #create list of what was mapped
            for ni in gl.WM.cp[self.lastbrpos].next:    #next items
                if ni not in thisbranch:                #D(), and not the own branch!
                    self.lastbr_list.append(gl.WM.cp[ni].parent)    #list of D(x,y) mappinf relation parents: (x,y)
    
    def perform_Branching(self,thisbranch):             #creation of new branches
        s=timer()
        self.get_Lastmulti(thisbranch)                  #get the latest psition where branching happened
        self.oldbranch = gl.WM.branch[:]                #remember blist of initial branches
        maplist = gl.WM.get_Maprules(self.wmpos)         #mapping rules list
        for maprule in maplist:
            self.trymap_Single(maprule)
        gl.args.settimer("branch_01: perform_branching",timer()-s)

                
if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
