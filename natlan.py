import sys, gl, conc, wrd, testing, reason, branch, activ
from timeit import default_timer as timer

# VS MIGRACIO, VERSIONS BEVEZETESE
# 10. KESZ: general feldolgozas - atrakni  rogton add_concept utan ugyanugy mint a same feldolgozast
# PARAGRAPH mozgatasa KB-be:
# 12. KESZ: a bekezdes vegenel a branch-ek mindegyikenek törlése a legjobb kivételével.
# MAPPING:
# 13. KESZ: utolso conceptre mappeles +1 pontot kapjon
# 14. KESZ: a C(he,person) rule-lal valo konzisztencia nincs elegge juztalmazva?   wmuse-ba betenni a D(he,ploceman) conceptet !!!!
# REASONING WITH KB:
# 16. KESZ: KB-ben levo aktivalt concepttel reasoneljen. 
# 21. KESZ: new: KB  old: KB  (CDrel feldolgozas). CRRel-ben a parenteket KB-rol WM-re kell alakitani. Meg tzesztelni !
# 22. KESZ a KB-ben most mar van kerdes alapu aktivalas.
# 23. KESZ: process_Anyrel esetben meg nem jo.
# KESZ: probléma: kbrules_filled és reasoned_with érvényét veszti ha jön egy új rule!
# 24. KESZ: megoldás:  Minden aktivált conceptre,  ujra kell fusson a createconceptrules és a convert_kbrules. 
# 25. KESZ: kb_rules töltése a vs_perform_reasonben minding megtörténik KB-ben is. A reasoning (UniConcept) KB esetben is megy.
# IM reasonminggel meg nem foglalkoztam KB esetre. 
# a rule alapu reasoningggel meg nem foglalkoztam KB esetre.
# reverse_Drel KB eseten nincs meghivva.
# lehetne a KB-ben spreading activation, es lehetne több activation round, lsd gl.py: self.kbactiv_limit


def process_testinput (tf):                     # run mentalese comprehension, input is the Testinput object
    for ri in range(len(tf.mentalese)):         # take mentalese items (rows in test input file)
        tfment = []
        tfment.append(tf.mentalese[ri])             # store mentalese
        starti=gl.WM.ci; counter=0                  # start position in WM
        if ri>0 and len(tf.mentalese[ri-1])>3 and len(tfment[0])<4:   # if this is an empty row, and the previous was not, then process paragraph
            gl.WM.process_Para(tf.mentalese[ri-1])  # process paragraph
        while len(tfment[0])>3 and counter<100:     # counter protects against endless loop
            gl.WM.branch_read_concept(starti,tfment,tf,ri) # store concepts in all WMs
            counter+=1
        if counter == 100: 
            gl.log.add_log(("Invalid input row provided, endless loop stopped. row=",ri," ",tf.mentalese[ri]))
            break
        if starti > 0 and starti!=gl.WM.ci:         # if something read: reason on new concept, but vs_perform_reason will reason on reasoned concepts
            gl.reasoning.vs_perform_Reason(tf.question[ri])  # convert kb_rules, add rule_match, add reasoned concepts
        if (tf.question[ri]==1):                    # the row is a question
            if gl.args.loglevel>0: gl.log.add_log(("Question answering started. input row:",ri," ",tf.mentalese[ri]))
            tf.systemanswer[ri][:] = gl.WM.answer_question(starti)[:]    # answer question and record concept indices
        gl.test.write_result(ri)                    # write result file

# GLOBAL VARIABLES

gl.d=1                      # debugging
gl.vstest=1                 # testing Versions class funtcionality
gl.error = 0                # error counter
gl.args = gl.Arguments()    # initialize global parameters
gl.KB = conc.Kbase("KB")    # KNOWLEDGE BASE
gl.WL = wrd.Wlist("WL")     # WORD LIST
gl.VS = branch.Version()    # versions instance that keeps track of versions of WM
gl.WM = gl.VS.add_WM()      # create the root Working Memory. (other instances of WM will be created as necessary.)
gl.log = gl.Logging()       # log file
gl.reasoning = reason.Reasoning() # instance for reasoning
gl.act = activ.Activate()   # activation instance

# START THE PROGRAM

if gl.args.argnum == 2:
    gl.test = testing.Testinput(sys.argv[1])    # the instance that holds the input file
    gl.test.readtest()                          # read the input file into gl.test
    s=timer()                                   # measure total execution time
    process_testinput (gl.test)                 # run the mentalese comprehension program
    end=timer()
    
    # OUTPUTS AFTER PROCESSING HAS FINISHED
    
    i=0
    print ("WM list count: "+str(len(gl.VS.wmlist))+" WM live: "+str(gl.VS.wmliv.keys()))
    for id,wmitem in enumerate(gl.VS.wmlist):           # all wms created
        if id in gl.VS.wmliv:                   # for living wm only
            print ("WM id:"+str(id)+" WM end:"+str(wmitem.ci)+" parent WM:"+str(wmitem.pawm)+" this wm id:"+str(wmitem.this)+" WMvalue="+str(wmitem.branchvalue)+" last conc used:"+str(wmitem.last)+" activated:"+str(wmitem.activ))
            for i,conc in enumerate(wmitem.cp): print (str(i)+ " "+conc.mentstr+" p="+str(conc.p)+" c="+str(conc.c)+" parents="+str(conc.parent)+" children="+str(conc.child)+" same="+str(conc.same)+" general="+str(conc.general)+" known="+str(conc.known)+" g="+str(conc.g)+" wmuse="+str(conc.wmuse)+" kblink:"+str(conc.kblink)+" kbrules:"+str(conc.kb_rules)+" rule_match:"+str(conc.rule_match))

    i=0
    print ("KB list:")
    for wmi in gl.KB.cp:
        print (i,wmi.mentstr,"parent",wmi.parent,"p=",wmi.p,"r=",wmi.relevance,"known",wmi.known,"same",wmi.same,"general",wmi.general,"wmuse:",wmi.wmuse,"kb_use:",wmi.kb_use,"kb_rules:",wmi.kb_rules," rule_match:",wmi.rule_match,"kbrules_upto:",wmi.kbrules_upto)
        i+=1

    gl.test.testf.close()
    gl.test.resultf.close()
    print ("branches:",gl.VS.wmliv.keys(),"this WM:",gl.WM.this," branchvalue:",gl.WM.branchvalue)
    
    print ("TIME USAGE REPORT IN BPS FOLLOWS.",end-s, " s total run time.")
    for t in sorted(gl.args.timecheck,reverse=False):
        print (t, int(gl.args.timecheck[t]*10000/(end-s)))
        
    gl.test.check_result()                  # compare _base to _result file
    print ("TOTAL reasoning attempts=",gl.args.total_reasoncount," REASONed concepts=",gl.args.success_reasoncount,"ERROR in process_CDrel. count =",gl.error)
    
else: print ("ERROR: too few or too many arguments. An input file with mentalese text must be provided as argument!")

gl.log.logf.close()

