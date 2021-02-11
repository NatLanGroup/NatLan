import gl,conc
from timeit import default_timer as timer

class Version:                  # inventory of WM versions (formerly branches)

    def __init__(self):
        self.wmlist = []        # list of all WM versions ever created. WM objects are in this list.
        self.wmliv = {}         # living wm id mapped to wm object
        self.killed = []        # list of WMs killed or abandoned

    def copy_Set(self,oldwm,newwm,oldset,newset):       # copy a set from oldwm to newwm
        for elem in oldset:                             # take old set elements
            if elem <= gl.VS.wmlist[oldwm].last:        # copy only relevant concepts
                newset.add(elem)                        # copy  concepts to new set

    def copy_List(self,oldwm,newwm,oldlist,newlist):    # copy a list from oldwm to newwm
        for elem in oldlist:                            # take old list elements
            if elem <= gl.VS.wmlist[oldwm].last:        # copy only relevant concepts
                newlist.append(elem)                    # copy  concepts to new list

    def copy_WMfields(self,oldwm,newwm):                # copy the fields from oldwm to newwm
        gl.VS.wmlist[newwm].last_question = gl.VS.wmlist[oldwm].last_question                   # copy last question index
        self.copy_Set(oldwm,newwm,gl.VS.wmlist[oldwm].activ,gl.VS.wmlist[newwm].activ)          # copy activ concept set
        gl.VS.wmlist[newwm].kbactiv = gl.VS.wmlist[oldwm].kbactiv.copy()     # copy kbactiv concept set - these are KB indices!
        self.copy_Set(oldwm,newwm,gl.VS.wmlist[oldwm].activ_new,gl.VS.wmlist[newwm].activ_new)  # copy newly activ concept set
        self.copy_Set(oldwm,newwm,gl.VS.wmlist[oldwm].activ_qu,gl.VS.wmlist[newwm].activ_qu)    # copy  activated based on question concept set
    #    self.copy_Set(oldwm,newwm,gl.VS.wmlist[oldwm].reasoned,gl.VS.wmlist[newwm].reasoned)    # copy resoning complete concept set
        for ment in gl.VS.wmlist[oldwm].vs_samestring:                      # copy vs_samestring dictionary
            for samecon in gl.VS.wmlist[oldwm].vs_samestring[ment]:         # all concepts that share this menatlese
                if samecon <= gl.VS.wmlist[oldwm].last:                     # copy only relevant concepts
                    if ment not in gl.VS.wmlist[newwm].vs_samestring:
                        gl.VS.wmlist[newwm].vs_samestring[ment] = set()     # initialize
                    gl.VS.wmlist[newwm].vs_samestring[ment].add(samecon)    # copy this concept id
        for ment in gl.VS.wmlist[oldwm].mapped_Inpara:                      # copy mapped_Inpara dictionary
            con=gl.VS.wmlist[oldwm].mapped_Inpara[ment]                     # all concepts that share this menatlese
            if con <= gl.VS.wmlist[oldwm].last:                             # copy only relevant concepts
                gl.VS.wmlist[newwm].mapped_Inpara[ment] = con               # copy
        self.copy_List(oldwm,newwm,gl.VS.wmlist[oldwm].thispara,gl.VS.wmlist[newwm].thispara)    # copy thispara concept list
        self.copy_List(oldwm,newwm,gl.VS.wmlist[oldwm].prevpara,gl.VS.wmlist[newwm].prevpara)    # copy prevpara concept list
        gl.VS.wmlist[newwm].branchvalue = gl.VS.wmlist[oldwm].branchvalue   # copy branch value

    def add_WM(self,pwmid=-1,copymax=0):        # create a new WM. pwmid=-1 means no parent exists.
        nwm = conc.Kbase("WM")                  # create new wm instance
        self.wmlist.append(nwm)
        nwm.pawm = pwmid                        # parent WM id added
        id = len(self.wmlist)-1                 # id of the new wm
        nwm.this = id                           # self-id stored
        self.wmliv[id] = nwm                    # adding to the directory of living wms
        if pwmid != -1:                         # not the root wm
            for concid in range(0,copymax):     # copy concepts stored in parent
                gl.WM.copy_Conc(gl.VS.wmlist[pwmid],nwm,concid)    # copy concept
        if pwmid>-1: self.copy_WMfields(pwmid,id)   # copy fields of old wm into new
        return nwm
     
    def kill_Branch(self,wmi,reason):           # kill the WM version wmi (given by index)
        gl.log.add_log(("BRANCH KILLED db=",wmi," WM value was:",gl.VS.wmlist[wmi].branchvalue," ",reason," All living versions:",gl.VS.wmliv.keys()))
        print ("BRANCH KILLED db=",wmi," WM value was:",gl.VS.wmlist[wmi].branchvalue,reason," All living versions:",gl.VS.wmliv.keys())
        if "low branch value" in reason: gl.VS.wmlist[wmi].printlog_WM(gl.VS.wmlist[wmi])     # print WM on screen
         #gl.WM.printlog_WM(gl.VS.wmliv[wmi])
        del gl.VS.wmliv[wmi]                    # kill the WM version 

class Branch:           #branching in WM

    def __init__(self,wmpos):
        self.wmpos=wmpos            #position in WM where branching is considered
        self.mapped=[]
        self.map_potential=set()    # words for potential mapping within this paragraph
        self.wordinpara = {}        # kblink-wmpos pairs to show latest occurance of words in the paragraph
        
    def remove_branch(self,branchi):
        # removes branch starting from branchi
        # doesn't really remove concepts, only terminates connection in the tree
        # removes ids of next concepts from the child list of previous concepts
        if gl.d==4: print ("REMOV BR 1 branch:",branch)
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
        if currentwm in gl.WM.prevpara: thispara=0         # remember if we cross paragraph border
        if gl.WM.cp[currentwm].relation==1 and thispara==1: # we are on a word in the same paragraph
            if gl.WM.cp[currentwm].wmuse==[-1]:             # original input
                if gl.WM.cp[currentwm].kblink[0] not in self.map_potential:     # add wm position only once. TO DO: enable multiple positions.
                    self.wordinpara[gl.WM.cp[currentwm].kblink[0]]=currentwm    # remember latest occurence in paragraph
                self.map_potential.add(gl.WM.cp[currentwm].kblink[0])           # remember kblink as potential word to map to
        return thispara

    def trymap_Single(self,maprule):        #mapping for a single rule
        currentwm=self.wmpos-1
        rulw=-1 ; thispara=1                            # flag to show we did not cross paragraph border yet
        ruleinwm = -1
        bonus = 1
        while currentwm>0:                             
            thispara = self.collect_Potential(thispara,currentwm)       # add currentwm to potential words to map, if so.   
            #TO DO: if currentwm is a word, search for C relation  in KB  (done in earlier WM) !!
            wmapto=-1                                                   # this will be the word we can try to map to
            if gl.WM.cp[currentwm].relation==4 and gl.WM.cp[currentwm].wmuse==[-1]:   #C relation needed to try mapping. only input is valid, no reasoning.
                wmapto=self.word_Tomapto(thispara,currentwm)            # find out if this C relation has a word to map to
            if gl.WM.cp[currentwm].relation==1 and gl.WM.cp[currentwm].wmuse==[-1] and thispara==1 :        # FIX:wmuse==-1 means this was input!! not reasoned!! this is a word in this paragraph
                if (self.wmpos not in gl.WM.mapped_Already) or (currentwm not in gl.WM.mapped_Already[self.wmpos]):
                    wmapto=gl.WM.check_Crel(currentwm,maprule)          # check if there is a C-relation for currentwm in KB or in this WM
            if wmapto!=-1:  
                if gl.d==1: print ("TRYMAP 2 wmapto=",wmapto,gl.WM.cp[wmapto].mentstr)
                ruleword=gl.KB.cp[maprule].parent[1]                    # in the rule in KB, second parent is a new word to be added
                if gl.KB.cp[ruleword].relation==1:                      #TO DO not only word but concept
                    if gl.KB.cp[ruleword].mentstr != gl.WM.cp[self.wmpos].mentstr:   #TO DO: avoid D(x,x)?
                        if rulw==-1:                                    #add rule only once
                            rulw = gl.WM.add_concept(gl.args.pmax,1,[],[ruleword])      #add the word from the rule to WM
                            ruleinwm = gl.WM.add_concept(gl.KB.cp[maprule].p,gl.KB.cp[maprule].relation,[self.wmpos,rulw],[maprule]) #add rule D(x,y) relation to WM
                            gl.act.vs_activate_Conc(ruleinwm,gl.WM)      # VS activate rule
                            gl.WM.cp[rulw].wmuse=[]
                            gl.WM.cp[ruleinwm].wmuse=[]
                            gl.WM.cp[ruleinwm].relevance = gl.KB.cp[maprule].relevance   # set relevance in rule
                            gl.log.add_log(("MAPPING: add rule to WM:",gl.KB.cp[ruleword].mentstr," ",gl.KB.cp[maprule].mentstr))
                        self.add_Mapbranch(maprule,ruleinwm,wmapto,bonus)  # add a new WM instance, as branch
                        bonus = 0                                       # the first mapping was closest to wmpos, it gets a bonus, others dont get it
            currentwm=currentwm-1                       #walk back on branch
        return ruleinwm

    def add_Mapbranch(self,maprule,ruleinwm,currentword,bonus):        #add one more branch starting from ruleinwm and expressing D(wmpos,curretwm)
        mapped_earlier=set()
        if self.wmpos in gl.WM.mapped_Already:                      # this wmpos was already mapped
            mapped_earlier.update(gl.WM.mapped_Already[self.wmpos]) # collect
            for mcon in gl.WM.mapped_Already[self.wmpos]:
                mapped_earlier.update(gl.WM.cp[mcon].same)          # add the concepts that are the same as those mapped to earlier
        if currentword not in mapped_earlier:                       # this will be a new mapping
            self.mapped.append(currentword)                             #remember this is mapped
        #    gl.reasoning.currentmapping[gl.WM.cp[self.wmpos].mentstr]=self.wmpos    # VS? kell?  remember mapping happening in this row
            gl.WM.last = ruleinwm                                       # last concept used in this wm
            oldwm = gl.WM
            gl.WM = gl.VS.add_WM(gl.WM.this,ruleinwm+1)                 # add new WM version. we copy the parent wm up to ruleinwm, inclusive.
            if self.wmpos not in oldwm.mapped_Already:                  # the first mapping of wmpos
                oldwm.mapped_Already[self.wmpos] = set()                # initialize
            oldwm.mapped_Already[self.wmpos].add(currentword)           # note that wmpos is mapped to currentword
            gl.WM.branchvalue += bonus                                  # increased the value of this branch if bonus was provided
            if gl.WM.branchvalue > gl.args.bmax:                        # max branchvalue exceeded
                gl.WM.branchvalue -= 1
            print ("ADD_BRANCH MAPPING: new wm: "+str(gl.WM.this)+" WM value:"+str(gl.WM.branchvalue)+" old wm: "+str(oldwm.this)+" oldwm last concept: "+str(oldwm.last)+" mapped concept="+str(self.wmpos)+" mapped to:"+str(currentword)+" "+str(oldwm.cp[currentword].mentstr)+" bonus="+str(bonus)+" mapped to list="+str(oldwm.mapped_Already[self.wmpos]))
            mapconcept = gl.WM.add_concept(gl.KB.cp[maprule].p, 3, [self.wmpos,currentword])        # mapping added to WM D()
            gl.WM.mapped_Inpara[gl.WM.cp[self.wmpos].mentstr]=currentword   # note that the concept on wmpos was mapped to currentword within paragraph
            gl.WM.cp[mapconcept].wmuse=[-1]                             #wmuse for a mapping is  -1 like for concepts that were in the input
            gl.act.activate_inKB(gl.WM,currentword,1,True)              # activate KB based on the word mapped to. activation round=1.
            if gl.d==1: print ("ADD MAPPING currentw:",currentword,gl.WM.cp[currentword].mentstr,"KB activ:",gl.WM.kbactiv)
            gl.log.add_log(("ADD BRANCH: MAPPING: old wm:",oldwm.this," old wm concept:",ruleinwm," mentalese:",oldwm.cp[ruleinwm].mentstr," new WM:",gl.WM.this," WM value=",gl.WM.branchvalue," mapped concept:",self.wmpos," ",gl.WM.cp[self.wmpos].mentstr," bonus=",bonus," mapped to:",gl.WM.cp[mapconcept].mentstr))
            gl.WM = oldwm                                               #COMP compatibility, set back original wm
                                             
    def vs_perform_Branching(self,db):                  #creation of new branches according to the VS object
        s=timer()
        if gl.WM.cp[self.wmpos].mentstr in gl.WM.mapped_Inpara:    # this mentalese was mapped in this paragraph
            mapconcept = gl.WM.add_concept(gl.args.pmax, 3, [self.wmpos,gl.WM.mapped_Inpara[gl.WM.cp[self.wmpos].mentstr]])   # mapping to the same concept as before
            gl.WM.cp[mapconcept].wmuse=[]                          #wmuse for a mapping is not -1 but empty
            gl.log.add_log(("MAPPING SAME as earlier in paragraph. WM:",gl.WM.this," mapped what:",self.wmpos," ",gl.WM.cp[self.wmpos].mentstr," mapped to:",gl.WM.cp[mapconcept].mentstr))
        else:
            maplist = db.get_Maprules(self.wmpos)           #mapping rules list
            lastconc=-1
            for maprule in maplist:
                lastconc = self.trymap_Single(maprule)      # perform mapping, lastconc is the last concept used in old wm
            if lastconc>-1:
                gl.VS.wmliv.pop(gl.WM.this,None)            # in case of branching, old wm is not live anymore      
            gl.args.settimer("branch_710: perform_branching",timer()-s)
                
if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
