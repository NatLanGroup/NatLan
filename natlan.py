import sys, gl, conc, wrd, testing, reason, branch, activ
from timeit import default_timer as timer

# VS MIGRACIOS JEGYZETEK
# 1. KESZ: finaladd_Concept-ben search_fullmatch hívása egyelőre ki van kommentelve. Javitani kell.
      # KESZ: eloszor .same mezot javiotani
#     # KESZ: search_fullmatch-ben check_Contradiction ki van kommentelve
# 2. KESZ: process_testinput-ban reasoning.recent_Activation hívása ki van kommentelve. Javítani, miután C-reasoning ellenőrizve lett.
# 3. KESZ: C-reasoning nincs letesztelve, átalakítva.
# 4. KESZ: AND() mint feltétel az új vs_perform_reason-ben kezelve. 
# 5. KESZ: IM reasoning nincs meg tesztelve
# 6. KESZ: manage_Consistency: athelyezve add_concept-be
# 7. KESZ: move_rule , move_relevant in process_testinput: athelyezni
# 8. KESZ: rossz es duplikalt version megszuntetese
# 9. KESZ: General rule 
# 10. KESZ: general feldolgozas - atrakni  rogton add_concept utan ugyanugy mint a same feldolgozast
# ITT TARTOK: copydata_KB -t egyberakni a transform_kb-val, és még törlés előtt, kezelni ha több bekeztdésből újra copizunk.
# törlés pedig csak utána. Közben elegendő lesz a remove-ra várókat összeszedni egy listában. Abban a listában lehet majd visszafele menni.
# az adatmásolást is rendezetten, visszafele kell csinálni !
# hatra van meg a bekezdes utan a branch-ek mindegyikenek törlése a legjobb kivételével.



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
    print ("WM list: "+str(gl.VS.wmlist)+" WM live: "+str(gl.VS.wmliv.keys()))
    for id,wmitem in enumerate(gl.VS.wmlist):           # all wms created
        print ("WM id:"+str(id)+" WM end:"+str(wmitem.ci)+" parent WM:"+str(wmitem.pawm)+" this wm id:"+str(wmitem.this)+" WMvalue="+str(wmitem.branchvalue)+" last conc used:"+str(wmitem.last)+" activated:"+str(wmitem.activ))
        for i,conc in enumerate(wmitem.cp): print (str(i)+ " "+conc.mentstr+" p="+str(conc.p)+" c="+str(conc.c)+" parents="+str(conc.parent)+" children="+str(conc.child)+" same="+str(conc.same)+" general="+str(conc.general)+" known="+str(conc.known)+" g="+str(conc.g)+" wmuse="+str(conc.wmuse)+" kblink:"+str(conc.kblink)+" kbrules:"+str(conc.kb_rules))

    i=0
    print ("KB list:")
    for wmi in gl.KB.cp:
        print (i,wmi.mentstr,"relation",wmi.relation,"parent",wmi.parent,"child",wmi.child,"p value",wmi.p,"known",wmi.known,"same",wmi.same,"general",wmi.general,"wmuse:",wmi.wmuse,"kb_rules:",wmi.kb_rules)
        i+=1

    gl.test.testf.close()
    gl.test.resultf.close()
    print ("branches:",gl.WM.branch," branchvalue:",gl.WM.branchvalue)
    
    print ("TIME USAGE REPORT IN BPS FOLLOWS.",end-s, " s total run time.")
    for t in sorted(gl.args.timecheck,reverse=False):
        print (t, int(gl.args.timecheck[t]*10000/(end-s)))
        
    gl.test.check_result()                  # compare _base to _result file
    print ("TOTAL reasoning attempts=",gl.args.total_reasoncount," REASONed concepts=",gl.args.success_reasoncount,"ERROR in process_CDrel. count =",gl.error)
    
else: print ("ERROR: too few arguments. An input file with mentalese text must be provided as argument!")

gl.log.logf.close()

