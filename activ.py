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

    def vs_activate_Conc(self,conc,db):         # activate a single concept in db (WM)
        if db.name=="WM":
            db.cp[conc].acts = gl.args.amax         # activation level set to maximum
            db.activ.add(conc)                      # add conc to the set of activated concepts
            db.activ_new.add(conc)                  # add conc to the set of newly activated concepts
        # for KB, we always need to do activation with regard to a specific WM, not just in general.

    def preact_Child(self,parent,wmdb,db,level):               # the pre-activation part
        act=[]; ret=""
        for child in db.cp[parent].child:           # concepts to pre-activate 
            if db.cp[child].known>=0 and "%" not in db.cp[child].mentstr:   #FIX >= 0 because we need just parents with known=0 to pre-activate!
                if child not in wmdb.kbact_pre[level] and child not in wmdb.kbact_pre[level+1]:            # not preactivated stronger
                    wmdb.kbact_pre[level].add(child)                # add level pre-activation
                    act.append(child)
                    if level==2 and child in wmdb.kbactiv_new:                  # child  preactivated on level 2 and also activated. 
                        new_act=self.preact_Child(child,wmdb,db,3)              # children of this double-activ child are pre-activated to level 3 !!
                        if len(new_act)>0:                                      # any level3 peractivation
                            gl.test.track(db,child,"   ACTIV (PRE4) double-preact. "+str(new_act),gl.args.tr_act,rule="")
                    if gl.d==88 and level==2 and child in wmdb.kbact_pre[2]:            
                        print ("PREACT CHILD 2 level=2 itt. child: :",child,"parent",parent)  #ITT TARTOK ennek gyerekeit aktivalni kell!!
                        if parent in wmdb.kbact_from: print ("parent from",wmdb.kbact_from[parent])
                        else: print ("parent from: not present in kbact_from.")
                        if child in wmdb.kbact_from: print ("child from:",wmdb.kbact_from[child])
                        else: print ("child from: not present in kbact_from.")
                    self.spread_From(wmdb,parent,child,level,[3])             # spread activation-from info from parent to the child
                    if level==2 and child in wmdb.kbact_pre[1]: 
                        wmdb.kbact_pre[1].remove(child)   # remove from lower preactivation
                        if self.con_lev(child,1) in wmdb.kbact_from:  wmdb.kbact_from[1].remove(self.con_lev(child,1))   # remove from content

        if len(act)>0:
            ret= "level:"+str(level)+" "+str(act)
        return ret

    def pre_Activate(self,curri,wmdb,db,isquestion):                      #  pre-activate concepts related to a C(x,y) concept or just the children
        level2=set()
        if isquestion: clevel=2                                         # level 2 activation
        else: clevel=1                                                  # level 1 activation
        if db.cp[curri].relation==4 and len(db.cp[curri].parent)>1:     # C relation, C(x,y) question
            wmdb.kbactiv.add(db.cp[curri].parent[1])                    # second parent, the general concept, gets activated
            wmdb.kbactiv_new.add(db.cp[curri].parent[1])                # second parent, the general concept, gets activated
            self.spread_From(wmdb,db.cp[curri].parent[1],curri,clevel,[3])         # spread activation-from info from curri to the parent
            new_act = self.preact_Child(db.cp[curri].parent[1],wmdb,db,clevel)    # children of y in C(x,y) to pre-activate strongly
            if len(new_act)>0:                                           # any level2 peractivation
                gl.test.track(db,curri,"   ACTIV (PRE1) C-preactivation. "+str(new_act),gl.args.tr_act,rule="")
        else:                                                           # not a C relation - perform level 1 preactivation   ???? not called for C relations!!
            new_act = self.preact_Child(curri,wmdb,db,1)                # children of parent
            if len(new_act)>0:                                          # any level2 peractivation
                gl.test.track(db,curri,"   ACTIV (PRE2) preact. "+str(new_act),gl.args.tr_act,rule="")
        if curri in wmdb.kbact_pre[2]:                              # now activated, earlier pre-activated on level 2
        #    if gl.d==8: print ("!!!!! PREACT 2, most aktivált és 2-es preaktivált:",curri,"from:",wmdb.kbact_from[curri])
            new_act=self.preact_Child(curri,wmdb,db,3)              # children of this double-activ curri are pre-activated to level 3 !!
            if len(new_act)>0:                                      # any level3 peractivation
                gl.test.track(db,curri,"   ACTIV (PRE3) double-preact. "+str(new_act),gl.args.tr_act,rule="")

    def double_Pre(self,wmdb,curri,lev1,lev2):                      # investigate source of lev1 and lev2 double (pre)activation
        lev1set=set()
        lev2set=set()
        act_this=False                                  # activate curri ?
        if curri in wmdb.kbact_from:
            for fromc in wmdb.kbact_from[curri]:        # sources of activations
                level = int(fromc.split("_")[1])
                if level==lev1: lev1set.add(int(fromc.split("_")[0]))   # first interesting level sources
                if level==lev2: lev2set.add(int(fromc.split("_")[0]))   # first interesting level sources
            for sourc in lev1set:
                if sourc not in lev2set:                # the source of lev1 is not the source of lev2
                    act_this=True                       # double activation condition is met !
        #    if gl.d==8: print ("DOUBLE curri",curri,"act this",act_this,"lev1set",lev1set,"lev2set",lev2set,"from",wmdb.kbact_from[curri])
        return act_this
                 
    def spread_Actpattern(self,db,coni,wmdb):           # spread activation based on p=question patterns
                                                        # in order to narrow, we check here, that this pattern matches the question at hand !!!!!!
        act=False
        if coni in wmdb.kbact_pre[1] or coni in wmdb.kbact_pre[2]:     # coni is pre-activated, close to something activated   amikor a 103-at pre=2-beteszem, akkor pre=1-bol kiveszem !!!!!!!
            if db.cp[coni].relation == 13 and len(db.cp[coni].parent)>1:   # IM(a,b) relation is coni, and pre-activated
                implic = db.cp[coni].parent[1]                  # implication - if this is the same structure as the question we need to proceed
                flatim = []
                db.pattern_Flat(db,flatim,implic)               # flattened implication
                for question in gl.WM.question_now:                     #  questions at hand
                    question_flat = []                                  # this will hold the flattened current question
                    gl.WM.pattern_Flat(gl.WM,question_flat,question)    # the current question gets flattened
                    match = gl.KB.pattern_flatmatch(question_flat,flatim) # check that a question matches the implication, b in IM(a,b)
                    if match: 
                        act=True                                # activate coni
                        gl.test.track(db,coni,"   ACTIV (SPREAD_1) triggered. IM concept implication matched question: "+str(question)+" ",gl.args.tr_act,rule="")
                        break
            flat=[]                             
            db.pattern_Flat(db,flat,coni)                       # store flat version of concept into flat
            spread_match=db.pattern_Spread(db,flat)             # compare flat (coni) to all stored patterns of spreading structures (based on questions)
            if act==False and spread_match[0]==True:                        # coni matches a p=question spreading pattern_Flat
                if gl.d==11: print ("SPREAD ACT 6 coni",db.name,coni,"matcvhing rules list",spread_match[1])
                for kb_que_rule in spread_match[1]:                         # the matching =question rule in KB. several matches possible.
                    toact = gl.KB.question_spread[kb_que_rule]              # the flattened b from the rule AND(a,b). This needs to be activated.
                    cmap={}                                                 # %1 %2 in rule mapped to the words in coni
                    gl.KB.pattern_flatmatch(flat,toact,cmap)                # we know that flat and toact match. But we call this again to fill cmap!!
                    related_question = gl.KB.question_observe[kb_que_rule]  # the first part of the rule, the related question to this match, flattened
                    for question in gl.WM.question_now:                     #  questions at hand
                        question_flat = []                                  # this will hold the flattened current question
                        gl.WM.pattern_Flat(gl.WM,question_flat,question)    # the current question gets flattened                
                        if len(related_question) == len(question_flat):     # these two need to match in order to spread the activation
                            qmap={}                                         # %1 %2 in rule mapped to the words in question
                            match = gl.KB.pattern_flatmatch(question_flat,related_question,qmap)   # if they match, this spreading is relevant and should be carried out
                                                                        # limitation (TO DO): we don't check yet if %1 %2 are the same in coni as in the current question.
                            if match:                                       # spread activation
                                if gl.d==11: print ("SPREAD ACT 9 coni",db.name,coni,"match",match,"question part in rule","none","current WM question",question,question_flat,"qmap",qmap,"cmap",cmap)
                                words_same=True
                                for wildcard in qmap:                       # %1 %2 etc we had in qmap, mapped to actual words in the question
                                    if wildcard in cmap:                    # the same %x wildcard occurs in coni conbcept to be activated according to the rule
                                        if qmap[wildcard]==cmap[wildcard]:  # the same word denoted in both question and coni by the same %x wildcard
                                            print ("SAME in SPREAD!!!! wildcard qm cm",wildcard,qmap[wildcard],cmap[wildcard])
                                        else:
                                            if cmap[wildcard] in gl.KB.cp[qmap[wildcard]].general:  # more general in coni, this is also fine, count as if it was the same  (KB because these are words)
                                                print ("GENREAL in SPREAD!!!! wildcard qm cm",wildcard,qmap[wildcard],"general",gl.KB.cp[qmap[wildcard]].general)
                                         #ITT TARTOK, működik, ezzel beáéllítható az act=True  .  még hozzá lehet tenni: gl.KB.cp[qmap[wildcard]].same SAME !!!!
                                act=True
                                gl.test.track(db,coni,"   ACTIV (SPREAD_2) triggered based on =question rule. matched question: "+str(question)+" ",gl.args.tr_act,rule=str(kb_que_rule))
                                break
                    if act: break                                           # first match enough for activation
        return act
                 
    def activKB_Allchild(self,db,start,curri,wmdb,around,isinput,nextch=0,isquestion=False):                 #nextp fixed recursive activation of curri and all children, used in KB
        s=timer()
        if isquestion: limit=gl.args.kbactiv_qlimit
        else: limit=gl.args.kbactiv_limit
    #    gl.test.track(db,curri,"   ACTIV (ATTEMPT) children of:",gl.args.tr_act)
        while (curri<len(db.cp) and len(db.cp[curri].child)>0 and nextch<len(db.cp[curri].child)):  # walk over children 
            if len(limit)>around+1: nextround=around+1
            else: nextround=around
            self.activKB_Allchild(db,curri,db.cp[curri].child[nextch],wmdb,nextround,isinput,0,isquestion)       # one level down. curri is the parent that was used to access child.
            nextch=nextch+1
        if  curri<len(db.cp) and "%1" not in db.cp[curri].mentstr:    # FIX: isinput==True deleted. >0 deleted. means thsi is not a reasoned concept
            if curri in wmdb.kbact_pre[2]: prelevel=1        # pre-activation level for the purpose of activation of self or children
            else: prelevel=0
        #    prelevel=0 #debug
        #    if gl.d==8: print ("ACTKB 3 TRY ACTIVATE curri",db.name,curri,db.cp[curri].mentstr,"limit",limit[around])
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
                    if thisact:                         # if curri 
                        wmdb.kbactiv.add(curri)         # add this KB concept to the list of KB-activated concepts with regard to this WM
                        wmdb.kbactiv_new.add(curri)     # add this KB concept to the list of KB-activated concepts with regard to this WM
                    #    if gl.d==8: print ("+++ ACTKB 7 activate:",curri,gl.KB.cp[curri].mentstr,"around",around,"limit",limit[around])
                if thisact :                                        # curri has been activated now
                    self.spread_From(wmdb,start,curri,0,[3])        # spread activation-from info level==0 means activation
                    self.pre_Activate(curri,wmdb,db,isquestion)     #  pre-activate concepts based on current activation
            #        if gl.d==8: print ("AFTER PRE_ACTIVATE kbact_pre:",wmdb.kbact_pre)
            else: 
                a=1
            if  curri not in wmdb.kbactiv_new:      # not activated, some other condition may activate it
                actnow=False                                    # condition met to activate??
                if curri in wmdb.kbact_pre[3]:                  # pre-act to level 3 shows this needs activation from double pre-activation
                    actnow = self.double_Pre(wmdb,curri,0,2)    # investigate the source of double pre-activation
                    if actnow: wmdb.kbact_pre[3].remove(curri)  # remove from level=3 pre-activation
                if actnow==False: actnow = self.spread_Actpattern(db,curri,wmdb)  # spread activation based on p=question patterns (but the question is not yet taken into acount!)               
                if actnow==True:                                # some activation condition is met
                    wmdb.kbactiv.add(curri)                     # add this KB concept to the list of KB-activated concepts with regard to this WM
                    wmdb.kbactiv_new.add(curri)                 # add this KB concept to the list of KB-activated concepts with regard to this WM
                    self.pre_Activate(curri,wmdb,db,False)      # pre-activate children of current activation
            #From is recorded in pre-activation but not recorded in structure spreading!        self.spread_From(wmdb,start,curri,0,[3])    # spread activation-from info level==0 means activation
                    if gl.d==8: print ("+++ ACTKB 9 activate:",curri,gl.KB.cp[curri].mentstr,"from",wmdb.kbact_from[curri])
                #ITT TARTOK: 105-öt kell aktiválni. IM(a,b) alapon, ahol b lett most a question.  
            #    if gl.d==8: print ("??? ACTKB 10 level 1 pre-activate:",curri,gl.KB.cp[curri].mentstr,"spread_act",actnow)
        gl.args.settimer("activ_200: activKB_Allchild",timer()-s)
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
                livewm.kbact_pre = {4:set(),3:set(),2:set(),1:set()}        # in KB, pre-activated dict empty
                livewm.kbact_from = {}       # empty the source data
                        

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

    def con_lev(self,con,level):
        return str(con)+"_"+str(level)
        
    def change_lev(self,fromst,level,nochange):          # change the level in fromst string to the level value provided.
        fromc=int(fromst.split("_")[0])
        oldlevel=int(fromst.split("_")[1])
    #    if gl.d==8:print ("CHANGE from:",fromst,"to",self.con_lev(fromc,level))
        if level in nochange:                           # we are on a level that from info should not change !!
            return self.con_lev(fromc,oldlevel)         # keep the old level info
        else:
            return self.con_lev(fromc,level)            # change to the new level info
 
    def activ_From(self,db,kbnow,fromc,level):                  # record which concept triggered the activation of kbnow
        if kbnow in db.kbact_from:
            db.kbact_from[kbnow].add(self.con_lev(fromc,level))     # fromc is one more source of activation
        else:
            db.kbact_from[kbnow] = set([self.con_lev(fromc,level)]) # start this set with fromc
 
    def spread_From(self,db,fromc,kbnow,level,nochange):        # record which concept triggered the activation by spreading from fromc
        if fromc in db.kbact_from:                                  # fromc has already a source
            if kbnow not in db.kbact_from:
                db.kbact_from[kbnow] = set()                        # initialize
            for fromst in db.kbact_from[fromc]:                     # sources of fromc
                newfrom=self.change_lev(fromst,level,nochange)      # change the level
                if fromc!=kbnow:
                    db.kbact_from[kbnow].add(newfrom)               # spread the from info to kbnow but with changed level
        else:                                                       # fromc has no source, nothing to spread
            self.activ_From(db,kbnow,fromc,level)                   # set fromc as source
 
    def vs_activate_Fromwords(self,wordlist,db,pos):                # activate concepts based on words (used for questions)
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
        gl.WM.question_now=[pos]                                    # clear current question inventory, fill with pos, the current question in WM
#        gl.WM.current_Question(pos)                                 # record the current question, on pos, in WM, flattened, in question_now
        if gl.d==8: gl.test.track(gl.WM,pos,"   ACTIV (POS CURRENT QUESTION). "+str(gl.WM.question_now),gl.args.tr_act,rule="") #debug
        kbact_now=set(); oldprelen=len(gl.WM.kbact_pre[3])
        for kbcon in kblinklist:                                    # concepts in KB that occur in pos as a parent on any level
            kbact_this=set(gl.WM.kbactiv_new)
            if kbcon not in gl.WM.kbactiv_new:                         # activate itself too
                if  max(gl.KB.cp[kbcon].relevance) >=gl.args.kbactiv_qlimit[1]:   # relevance above questionb threshold  FIX gl.KB.cp[kbcon].known!=0 and
                    gl.WM.kbactiv.add(kbcon)                      # activate in KB
                    gl.WM.kbactiv_new.add(kbcon)                  # activate in KB
                    self.activ_From(gl.WM,kbcon,kbcon,0)          # record which concept triggered the activation
            if len (gl.WM.kbactiv_new-kbact_this)>0:                # anything new activated based on this kbcon
                gl.test.track(gl.KB,kbcon,"   ACTIV (QUE1) KB new activated="+str(gl.WM.kbactiv_new-kbact_this),gl.args.tr_act,rule="")  
            if kbcon not in gl.WM.kbact_pre[3]:                     # not pre-activated on level 3
                gl.WM.kbact_pre[3].add(kbcon)                       # shows that children need be activated
        while len(gl.WM.kbactiv_new) > len(kbact_now) or len(gl.WM.kbact_pre[3])>oldprelen:  # spreading activation: while we have new (pre)activations in kbactiv_new
            kbact_now = set(gl.WM.kbactiv_new); kbact_this=set(gl.WM.kbactiv_new)
            oldprelen=len(gl.WM.kbact_pre[3])
            for kbcon in kbact_now:                                     # spreading activation: activate children and do pre-activations
                if kbcon in gl.WM.kbact_pre[3]:                         # sufficiently high pre-activation level- either input, or category in C(...,x)
                    self.activKB_Allchild(gl.KB,kbcon,kbcon,gl.WM,1,True,0,True)   # activate children (again) in order to account for preactivation in kbact_prestrong
    #                if gl.d==8: print ("VS FROMWORDS 3  KB act:",gl.WM.kbactiv_new,"old act",kbact_this)
                if len (gl.WM.kbactiv_new-kbact_this)>0:                # anything new activated based on this kbcon
                    gl.test.track(gl.KB,kbcon,"   ACTIV (QUE2) KB new activated="+str(gl.WM.kbactiv_new-kbact_this),gl.args.tr_act,rule="")
                kbact_this=set(gl.WM.kbactiv_new)
        gl.WM.question_now=[]                                       # clear current question inventory
        gl.args.settimer("activ_100: activate_Fromword",timer()-s)


        
                                