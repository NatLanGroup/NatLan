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

    def activate_KBconc(self,conc,db):          # activate a single concept in KB
        db.kbactiv.add(conc)           # add this KB concept to the list of KB-activated concepts with regard to this WM
        db.kbactiv_new.add(conc)       # add this KB concept to the list of KB-activated concepts with regard to this WM
        if gl.d==6: print ("ACT KB CONC NEW here:",conc)
        
    def activate_inKB(self,db,curr,around,isinput):         # FIX:isinput. activate concepts for curr in KB beyond relevance limit
        if db.cp[curr].kblink!=[] and isinput==True:    # FIX: input=False means thsi is a reasoned concept, do not activate currently.
            kbi = db.cp[curr].kblink[0]
            wmapto = -1
            for child in gl.KB.cp[kbi].child:
                if max(gl.KB.cp[child].relevance) >= gl.args.kbactiv_limit[around] and gl.KB.cp[child].known>0 and "%1" not in gl.KB.cp[child].mentstr: # relevance limit for the round met
                    db.kbactiv.add(child)           # add this KB concept to the list of KB-activated concepts with regard to this WM
                    db.kbactiv_new.add(child)       # add this KB concept to the list of KB-activated concepts with regard to this WM


    def pre_Activate(self,curri,wmdb,db):                      # for questions pre-activate concepts related to a C(x,y) concept
        level2=set()
        if db.cp[curri].relation==4 and len(db.cp[curri].parent)>1:     # C relation
            wmdb.kbactiv.add(db.cp[curri].parent[1])                    # second parent, the general concept, gets activated
            wmdb.kbactiv_new.add(db.cp[curri].parent[1])                # second parent, the general concept, gets activated
        #    wmdb.kbact_prestrong.update(db.cp[db.cp[curri].parent[1]].child)  # pre-activate children of "animal"
            for child in db.cp[db.cp[curri].parent[1]].child:           # concepts to pre-activate strongly
                if db.cp[child].known>=0 and "%" not in db.cp[child].mentstr:   #FIX >= 0 because we need just parents with known=0 to pre-activate!
                    if child not in wmdb.kbact_pre[2]:
                        wmdb.kbact_pre[2].add(child)                    # add level 2 pre-activation
                        #letiltas!!!!
                        if child>1 : wmdb.kbact_pre[child]=db.cp[curri].parent[1]  # remember that C(y,x) curri's x parent was used already. Should not be used twice.
                        level2.add(child)                               # remember
            if len(level2)>0:                                           # any level2 peractivation
                gl.test.track(db,curri,"   ACTIV (PRE) db new preactivation to level2="+str(level2),gl.args.tr_act,rule="")


                    
    def activKB_Allchild(self,db,start,curri,wmdb,around,isinput,nextch=0,isquestion=False):                 #nextp fixed recursive activation of curri and all children, used in KB
        #if gl.d==3: print ("ACTIVKB db",db.name,"curri",curri,"wmdb",wmdb.name)
        if isquestion: limit=gl.args.kbactiv_qlimit
        else: limit=gl.args.kbactiv_limit
    #    gl.test.track(db,curri,"   ACTIV (ATTEMPT) children of:",gl.args.tr_act)
        while (curri<len(db.cp) and len(db.cp[curri].child)>0 and nextch<len(db.cp[curri].child)):  # walk over children 
            if len(limit)>around+1: nextround=around+1
            else: nextround=around
            self.activKB_Allchild(db,curri,db.cp[curri].child[nextch],wmdb,nextround,isinput,0,isquestion)       # one level down. curri is the parent that was used to access child.
            nextch=nextch+1
        if  curri<len(db.cp) and db.cp[curri].known>0 and "%1" not in db.cp[curri].mentstr:    # FIX: isinput==True deleted. means thsi is not a reasoned concept
            if curri in wmdb.kbact_pre[3]: prelevel=1        # pre-activation level for the purpose of activation of children
            else: prelevel=0
            if gl.d==6: print ("ACTKB 3 TRY ACTIVATE curri",db.name,curri,db.cp[curri].mentstr,"limit",limit[around])
            if max(db.cp[curri].relevance)+prelevel >= limit[around] : # relevance limit for the round met
                thisact=True                        # do activate this curri
                if start==curri:                    # top level, not the children
                    wmdb.kbactiv.add(curri)         # add this KB concept to the list of KB-activated concepts with regard to this WM
                    wmdb.kbactiv_new.add(curri)     # add this KB concept to the list of KB-activated concepts with regard to this WM
                    if gl.d==6: print ("ACTKB 4 activate:",curri,gl.KB.cp[curri].mentstr)
                else:                               # we are at children
                    for pari in range(len(db.cp[curri].parent)):                            # look at relevance of each parent separately
                        if db.cp[curri].parent[pari]==start:
                            if db.cp[curri].relation in gl.args.kbactiv_addone:             # additional limit may apply for this relation
                                if pari in gl.args.kbactiv_addone[db.cp[curri].relation]:   # additional limit DOES apply for this parent position !! like for C(...,x)
                                    addlimit=gl.args.kbactiv_addone[db.cp[curri].relation][pari]
                                    if db.cp[curri].relevance[pari]+prelevel < limit[around]+addlimit:   # relevance of the specific parent is not high enough
                                        thisact=False                                        # do not activate this curri
                                        if gl.d==8: print ("ACTKB 5 inhibit activate:",curri,gl.KB.cp[curri].mentstr,"limit",limit[around]+addlimit)
                                        if gl.d==8 and (curri in wmdb.kbact_pre[1]): print ("ACTKB PRE 01 curri",curri)
                                        if gl.d==8 and (curri in wmdb.kbact_pre[2]): print ("ACTKB PRE 02 curri",curri)
                    if thisact:                         # if curri needs activation
                        wmdb.kbactiv.add(curri)         # add this KB concept to the list of KB-activated concepts with regard to this WM
                        wmdb.kbactiv_new.add(curri)     # add this KB concept to the list of KB-activated concepts with regard to this WM
                        if gl.d==6: print ("ACTKB 7 activate:",curri,gl.KB.cp[curri].mentstr)
                if thisact and isquestion:                        # curri has been activated now, and we started activation from a question
                    self.pre_Activate(curri,wmdb,db)              # for questions pre-activate concepts related to a C(x,y) concept
            else: 
                if gl.d==8 and (curri in wmdb.kbact_pre[1]): print ("ACTKB PRE 21 curri",curri)
                if gl.d==8 and (curri in wmdb.kbact_pre[2]): print ("ACTKB PRE 22 curri",curri)
                
                a=1
        #        if gl.d==6: print ("ACTKB 7 discarded",curri,gl.KB.cp[curri].mentstr,"limit:",limit[around])
                
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
                livewm.kbactiv_new = set()          # in KB, activated set empty
                livewm.kbact_pre = {3:set(),2:set(),1:set()}        # in KB, pre-activated dict empty
                livewm.kbact_prestrong = set()      # in KB, strong pre-activated set empty
                        

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
    #    if gl.d==6: print ("VS FROMWORDS 0 kblinklist:",kblinklist,"pos:",pos,gl.WM.cp[pos].mentstr)
        kbact_now=set(); oldprelen=len(gl.WM.kbact_pre[3])
        for kbcon in kblinklist:                                    # concepts in KB that occur in pos as a parent on any level
            kbact_this=set(gl.WM.kbactiv_new)
            if kbcon not in gl.WM.kbactiv_new:                         # activate itself too
                if  max(gl.KB.cp[kbcon].relevance) >=gl.args.kbactiv_qlimit[1]:   # relevance above questionb threshold  FIX gl.KB.cp[kbcon].known!=0 and
                    gl.WM.kbactiv.add(kbcon)                     # activate in KB
                    gl.WM.kbactiv_new.add(kbcon)                 # activate in KB
                 #   gl.WM.kbact_pre[kbcon]=2                     # activation level=3 : shows that children need be activated
            if len (gl.WM.kbactiv_new-kbact_this)>0:                # anything new activated based on this kbcon
                gl.test.track(gl.KB,kbcon,"   ACTIV (QUE1) KB new activated="+str(gl.WM.kbactiv_new-kbact_this),gl.args.tr_act,rule="")  
            if kbcon not in gl.WM.kbact_pre[3]:                     # not pre-activated on level 3
                gl.WM.kbact_pre[3].add(kbcon)                       # shows that children need be activated
    # ITT TARTOK regtest2 -ben 113-as KB concepttel reasonel, raadasul k=0 !!!, de ott van a WM-ben 11-en a concept.
        while len(gl.WM.kbactiv_new) > len(kbact_now) or len(gl.WM.kbact_pre[3])>oldprelen:  # spreading activation: while we have new (pre)activations in kbactiv_new
    #        if gl.d==6: print ("VS FROMWORDS 1  activation next round on pos",pos,db.cp[pos].mentstr)
            kbact_now = set(gl.WM.kbactiv_new); kbact_this=set(gl.WM.kbactiv_new)
            oldprelen=len(gl.WM.kbact_pre[3])
            for kbcon in kbact_now:                                     # spreading activation: activate children and do pre-activations
                if kbcon in gl.WM.kbact_pre[3]:                         # sufficiently high pre-activation level- either input, or category in C(...,x)
    #                if gl.d==6: print ("VS FROMWORDS 2  kbcon",kbcon,"KB act:",gl.WM.kbactiv_new,"preact",gl.WM.kbact_pre)
                    self.activKB_Allchild(gl.KB,kbcon,kbcon,gl.WM,1,True,0,True)   # activate children (again) in order to account for preactivation in kbact_prestrong
                    if gl.d==6: print ("VS FROMWORDS 3  KB act:",gl.WM.kbactiv_new,"preact",gl.WM.kbact_pre)
                if len (gl.WM.kbactiv_new-kbact_this)>0:                # anything new activated based on this kbcon
                    gl.test.track(gl.KB,kbcon,"   ACTIV (QUE2) KB new activated="+str(gl.WM.kbactiv_new-kbact_this),gl.args.tr_act,rule="")
                kbact_this=set(gl.WM.kbactiv_new)
        gl.args.settimer("activ_100: activate_Fromword",timer()-s)


        
                                