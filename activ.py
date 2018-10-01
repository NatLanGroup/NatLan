import gl
from timeit import default_timer as timer

class Activate:
    def __init__(self):
        self.allwmactive=1                      # 1 means we activate any new concept in WM
        self.deactiv_prevpara = 1               # 1 means deactivate concepts of previous paragraph when crossing paragraph border
        self.act_qw = 1                         # 1 means activate concepts based on words in question
        # 1,0,0 is the old way of activating everything
        self.act_secondround=0                  # working but explodes. 1 means second round of activation based on words of 1st round.
        self.secondround_set = set()            # remember concepts in second round activation

    def activate_Conc(self,conc,leaflist):      # activate a single concept on several leafs
        gl.WM.cp[conc].acts = gl.args.amax      # activation level set to maximum
        for leaf in leaflist:
            gl.WM.branchactiv[leaf].add(conc)   # add conc to the set of activated concepts per branch

    def get_Thisactiv(self,wmpos):              # collect all activated concepts from relevant branches
        thisact=set()
        for leaf in gl.WM.brelevant:            # brelevant has leafs where wmpos occurs
            thisact.update(set(gl.WM.branchactiv[leaf]))  # add the activated elemets of this branch
        return thisact

    def update_Para(self):                      # update paragraph information when new paragraph starts
        if len(gl.WM.thispara)>0:               # nonempty
            gl.WM.prevpara = gl.WM.thispara[:]  # copy previous paragraph
            gl.WM.thispara[:]=[]                # this para empty
        if self.deactiv_prevpara==1:            # previous paragraph deactivation needed
            for leaf in gl.WM.branchactiv:
                for con in gl.WM.branchactiv[leaf]:
                    if gl.WM.ci>0: gl.WM.cp[con].acts=0  # activation to zero
                    gl.WM.branchactiv[leaf]=set([1]) #fully deactivate, just keep the key in the dictionary with concept=1 dummy

    def second_Collect (self,con,second_parents):   # collect concepts for spreading activation
        visitcon=[]
        gl.WM.visit_db(gl.WM,con,visitcon)          # get all parents
        for item in visitcon:
            if item[0]!=con:
                second_parents.add(item[0])         # add parent of con to second round activation collection
                second_parents.update(gl.WM.cp[item[0]].same)   # also add concepts being the same as item0

    def activate_Second(self,leaf,second_parents):  # perform spreading activation
        curri=leaf
        while curri>0:
            if gl.WM.cp[curri].acts < gl.args.amax:
                for parent in gl.WM.cp[curri].parent:
                    if not((len(gl.WM.cp[curri].wmuse)>0 and gl.WM.cp[curri].wmuse[0]<0) and gl.WM.cp[curri].p==gl.args.pmax/2):  # not a parent with p=2
                        gl.WM.cp[curri].acts+=gl.args.asec   # increase activation
                        self.secondround_set.add(curri)      # remember this pre-activation
                        if gl.WM.cp[curri].acts>=gl.args.amax:
                            gl.WM.cp[curri].acts=gl.args.amax
                            self.activate_Conc(curri,[leaf])  # activate this concept, do not spread activation deeper
                            gl.WM.new_activ[leaf].add(curri)  # add activation to invetory of recent activations
                            self.secondround_set.discard(curri)  # remove
            curri=gl.WM.cp[curri].previous                    # up in the branch
            
    def activate_Fromwords(self,wordlist):                  # activate concepts based on words (used for questions)
        # only the top level needs activation where p!=2. Parents dont.
        s=timer()
        for branch in gl.WM.brelevant:
            current=branch
            second_parents=set()
            while current>1:                                # walk up on branch
                for actword in wordlist:                    # check eachg word
                    if gl.WM.cp[current].p!=2 and gl.WM.cp[current].relation!=1:   # makes sense, not a word
                        if actword[0] in gl.WM.cp[current].mentstr:     # actword present in mentalese
                            if branch not in gl.WM.branchactiv:
                                gl.WM.branchactiv[branch]=set()         # initialize branchactiv for this branch
                            if branch not in gl.WM.new_activ:
                                gl.WM.new_activ[branch]=set()            # initialize new_activ for this branch
                            if current not in gl.WM.branchactiv[branch]: # not yet activated
                                gl.WM.branchactiv[branch].add(current)   # add to inventory of activated concepts
                                gl.WM.new_activ[branch].add(current)     # add to inventory of recently activated concepts
                                if self.act_secondround==1:              # spreading activation
                                    self.second_Collect(current,second_parents)  # collect for activation spreading
                current = gl.WM.cp[current].previous                     # walk up on branch
            if self.act_secondround==1:                                  # spreading activation
                self.activate_Second(branch,second_parents)              # perform spreading activation
            if gl.d==1: print ("ACTIVATE FROMWORD 3 wordlist",wordlist," branch",branch," now activated",gl.WM.branchactiv[branch])
        gl.args.settimer("activ_100: activate_Fromword",timer()-s)

    def clean_Recentact(self):                          # clear recent activation
        for leaf in gl.WM.new_activ:
            for con in gl.WM.new_activ[leaf]:
                brele = gl.WM.select_Relevant(con)      # branches where con is present
                for br in brele:
                    try: gl.WM.branchactiv[br].discard(con)   # deactivate
                    except: a=1
                gl.WM.cp[con].acts=0                    # deactivate
        for leaf in list(gl.WM.new_activ.keys())[:] :         # key will be removed this is why we do it with keys()
            del gl.WM.new_activ[leaf]                   # remove leaf key
        for con in self.secondround_set:                # pre-actiavted concepts in spreading activation
            gl.WM.cp[con].acts=0                        # deactivate
        self.secondround_set.clear()                    # empty the set
        
                                