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

    def delete_activate_Conc(self,conc,leaflist):      # activate a single concept on several leafs
        gl.WM.cp[conc].acts = gl.args.amax      # activation level set to maximum
        for leaf in leaflist:
            gl.WM.branchactiv[leaf].add(conc)   # add conc to the set of activated concepts per branch

    def vs_activate_Conc(self,conc,db):         # activate a single concept in db (WM)
        if db.name=="WM":
            db.cp[conc].acts = gl.args.amax         # activation level set to maximum
            db.activ.add(conc)                      # add conc to the set of activated concepts
            db.activ_new.add(conc)                  # add conc to the set of newly activated concepts
        # for KB, we always need to do activation with regard to a specific WM, not just in general.
        
    def activate_inKB(self,db,curr,around,isinput):         # FIX:isinput. activate concepts for curr in KB beyond relevance limit
        if db.cp[curr].kblink!=[] and isinput==True:    # FIX: input=False means thsi is a reasoned concept, do not activate currently.
            kbi = db.cp[curr].kblink[0]
            wmapto = -1
            for child in gl.KB.cp[kbi].child:
                if max(gl.KB.cp[child].relevance) >= gl.args.kbactiv_limit[around] and gl.KB.cp[child].known>0 and "%1" not in gl.KB.cp[child].mentstr: # relevance limit for the round met
                    db.kbactiv.add(child)           # add this KB concept to the list of KB-activated concepts with regard to this WM
                    db.kbactiv_new.add(child)       # add this KB concept to the list of KB-activated concepts with regard to this WM
                    
    def activKB_Allchild(self,db,start,curri,wmdb,around,isinput,nextch=0):                 #nextp fixed recursive activation of curri and all children, used in KB
        #if gl.d==3: print ("ACTIVKB db",db.name,"curri",curri,"wmdb",wmdb.name)
        while (curri<len(db.cp) and len(db.cp[curri].child)>0 and nextch<len(db.cp[curri].child)):  # walk over children 
            if len(gl.args.kbactiv_limit)>around+1: nextround=around+1
            else: nextround=around
            self.activKB_Allchild(db,curri,db.cp[curri].child[nextch],wmdb,nextround,isinput,0)       # one level down. curri is the parent that was used to access child.
            nextch=nextch+1
        if isinput==True and curri<len(db.cp):    # FIX: input=False means thsi is a reasoned concept, do not activate currently in KB.
            if max(db.cp[curri].relevance) >= gl.args.kbactiv_limit[around] and db.cp[curri].known>0 and "%1" not in db.cp[curri].mentstr: # relevance limit for the round met
                if start==curri:                    # top level, not the children
                    wmdb.kbactiv.add(curri)         # add this KB concept to the list of KB-activated concepts with regard to this WM
                    wmdb.kbactiv_new.add(curri)     # add this KB concept to the list of KB-activated concepts with regard to this WM
                else:                               # we are at children
                    wmdb.kbactiv.add(curri)         # add this KB concept to the list of KB-activated concepts with regard to this WM
                    wmdb.kbactiv_new.add(curri)     # add this KB concept to the list of KB-activated concepts with regard to this WM
                    for pari in range(len(db.cp[curri].parent)):                            # look at relevance of each parent separately
                        if db.cp[curri].parent[pari]==start:
                            if db.cp[curri].relation in gl.args.kbactiv_addone:             # additional limit may apply for this relation
                                if pari in gl.args.kbactiv_addone[db.cp[curri].relation]:   # additional limit DOES apply for this parent position !! like for C(...,x)
                                    addlimit=gl.args.kbactiv_addone[db.cp[curri].relation][pari]
                                    if db.cp[curri].relevance[pari] < gl.args.kbactiv_limit[around]+addlimit:   # relevance of the specific parent is not high enough
                                        wmdb.kbactiv.discard(curri)                         # remove it from activation set
                                        wmdb.kbactiv_new.discard(curri)
#                                        if gl.d==6: print ("ACTKB 6 discarded",curri)
        return


    def get_Thisactiv(self,wmpos):              # collect all activated concepts from relevant branches
        thisact=set()
        for leaf in gl.WM.brelevant:            # brelevant has leafs where wmpos occurs
            thisact.update(set(gl.WM.branchactiv[leaf]))  # add the activated elemets of this branch
        return thisact

    def update_Para(self):                      # update paragraph information when new paragraph starts
        for livewmind in gl.VS.wmliv:               # all live WMs
            livewm = gl.VS.wmliv[livewmind]         # get live WM object
            if len(livewm.thispara)>0:              # nonempty
                livewm.prevpara = livewm.thispara[:]  # copy previous paragraph
                livewm.thispara[:]=[]               # this para empty
            livewm.mapped_Inpara.clear()            # clear dictionary of mapped words
            if self.deactiv_prevpara==1:            # previous paragraph deactivation needed
                for con in livewm.activ:            # activated concepts
                    if livewm.ci>con: livewm.cp[con].acts=0   # deactivate
                livewm.activ = set()                # activated set empty
                livewm.activ_new = set()            # activated set empty
                livewm.kbactiv = set()              # in KB, activated set empty
            if gl.d==6:print ("UPD PARA now wm= "+str(livewm.this)+" now activ="+str(livewm.activ)," prevpara",livewm.prevpara)
                        

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

    def enable_Word(self,db,current,word):                     # check that this word position is enabled for activation
        act_ok=1
        rel=db.cp[current].relation
        if rel in gl.args.noactivate_fromword:              # some positions for this relation are disabled
            act_ok=0; pari=0                                # default is disbale
            for par in db.cp[current].parent:               # check all parents
                if pari not in gl.args.noactivate_fromword[rel]:   # this position is not disabled
                    if word in db.cp[par].mentstr:       # this enabled parent has the word of activation
                        act_ok=1                            # ebable
                pari+=1
        return act_ok
        
    def vs_activate_Fromwords(self,wordlist,db,pos):                  # activate concepts based on words (used for questions)
        # ?? only the top level needs activation where p!=2. Parents dont.
        s=timer()
        current = gl.WM.ci
        while current>1:                                            # all concepts in this wm, backwards                          
            if gl.WM.cp[current].p!=2 and gl.WM.cp[current].known!=0 and gl.WM.cp[current].relation!=1:   # makes sense, not a word
                for actword in wordlist:                            # check eachg word
                    if actword[0] in gl.WM.cp[current].mentstr:     # actword present in mentalese
                        activation_ok = self.enable_Word(gl.WM,current,actword[0])   # check if this is enabled
                        if activation_ok == 1:                      # this activation is enabled
                            if current not in gl.WM.activ:          # not activated so far
                                gl.WM.activ_qu.add(current)         # remember this was activated due question
                            gl.WM.activ_new.add(current)            # activate concept current
                            gl.WM.activ.add(current)
            current=current-1                                       # upwards in this WM
        kblinklist=[]
        gl.WM.visit_KBlinks(gl.WM,pos,kblinklist)                   # collect the kblinks: these parents are in KB
        #print ("ACTFROMW kblinklist:",kblinklist,"pos:",pos,gl.WM.cp[pos].mentstr)
        for kbcon in kblinklist:                                    # concepts in KB that occur in pos as a parent on any level
            for kbch in gl.KB.cp[kbcon].child:                  # direct children only (limitation)
                if gl.KB.cp[kbch].known!=0 and max(gl.KB.cp[kbch].relevance) >=gl.args.kbactiv_qlimit[1]:   # relevance above questionb threshold
                    gl.WM.kbactiv.add(kbch)                     # activate in KB
                    gl.WM.kbactiv_new.add(kbch)                 # activate in KB
            if gl.KB.cp[kbcon].relation!=1:                         # not a word: activate itself too
                if gl.KB.cp[kbcon].known!=0 and max(gl.KB.cp[kbcon].relevance) >=gl.args.kbactiv_qlimit[1]:   # relevance above questionb threshold
                    gl.WM.kbactiv.add(kbcon)                     # activate in KB
                    gl.WM.kbactiv_new.add(kbcon)                 # activate in KB
        gl.args.settimer("activ_100: activate_Fromword",timer()-s)


        
                                