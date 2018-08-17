import sys, gl, conc, wrd, testing, reason, branch
from timeit import default_timer as timer

def process_testinput (tf):                  # input is the Testinput object
    nqflag=False                            # flag to show next row is question and not processed
    for ri in range(len(tf.mentalese)):     # take mentalese items (rows in test input file)
        counter=0; tfment=[]
        tfment.append(tf.mentalese[ri])
        starti=gl.WM.ci                             # start position in WM
        if len(tfment[0])<2:                        # if this is an empty row, remember paragraph border
            gl.WM.paragraph = list(set(gl.WM.branch).union(set([gl.WM.ci])))  # record the last concept of the paragraph
        while (len(tfment[0])>3 and counter<20):    # counter protects against endless loop
            gl.WM.branch_read_concept(starti,tfment,tf.question[ri])              # store concepts in WM
            counter=counter+1
        gl.WM.move_rule(tf,ri,starti)               # if this is a rule, move to KB
        if gl.WM.ci>=0: gl.WM.move_relevant(starti) # if this is top relevant, r=4, move it to KB
        endi = gl.WM.ci                             # end position in WM
        gl.reasoning.actual=starti+1
        if (tf.question[ri]==1):                    # if yes, then on endi we assume a question
            tf.systemanswer[ri][:] = gl.WM.answer_question(starti,endi)[:]    # answer question and record concept indices
            starti = gl.WM.ci                       # do not reason on questions
            gl.reasoning.actual = gl.WM.ci
        gl.test.write_result(ri)                    # write result file
        nqflag = gl.reasoning.insert_Drel(starti,tf.next_question[ri])   # insert D(x) relation if next row is question
        gl.WM.set_General(starti)                   # compare new concepts with entire WM to find more general or special concept pairs
        while starti > 0 and starti!=gl.WM.ci:      # reason on new concept and on all reasoned concepts
            startiremember=gl.WM.ci                 # TO DO: limitation: if r=4 relation, reasoning is skipped, nqflag goes lost.
            gl.reasoning.createConceptRules(starti, gl.WM.cp.__len__())     #add initial kb_rules content
            gl.reasoning.perform_Reason(starti+1, len(gl.WM.cp), nqflag, tf.next_question[ri])  #convert kb_rules, add rule_match, add reasoned concepts
            nqflag=False                            # reset flag in order to insert D(x) only once
            starti=startiremember
        gl.reasoning.reset_Currentmapping(tf.mentalese[ri])     # keep only words in currentmapping that are in current sentence

gl.d=0                      # debugging
gl.error = 0                # error counter
gl.args = gl.Arguments()    # initialize
gl.WM = conc.Kbase("WM")    # WORKING MEMORY
gl.KB = conc.Kbase("KB")    # KNOWLEDGE BASE
gl.WL = wrd.Wlist("WL")     # WORD LIST
gl.log = gl.Logging()
gl.reasoning = reason.Reasoning() #class instance for reasoning

test1 = conc.Concept()
test1.add_parents([-1, 17])
result = gl.WM.search_inlist(test1)
gl.unittest=testing.Temptest()              # initialize temporary tests

if gl.args.argnum == 2:
    #gl.unittest.test_implication()
    gl.test = testing.Testinput(sys.argv[1])
    gl.test.readtest()
    s=timer()
    process_testinput (gl.test)
    end=timer()
    i=0
    for wmi in gl.WM.cp:
        print (i,wmi.mentstr,wmi.p,wmi.parent,"g=",wmi.g," consist=",wmi.c," wmuse:",wmi.wmuse," reasonuse:",wmi.reasonuse," used by:",wmi.usedby," general:",wmi.general," same:",wmi.same," prev",wmi.previous," next:",wmi.next)
        i+=1
    i=0
    for wmi in gl.KB.cp:
        print (i,wmi.mentstr,wmi.parent," general:",wmi.general)
        i+=1
#    for br in gl.WM.branch:
 #       bro=branch.Branch(0)
  #      thisbr=bro.get_previous_concepts(br)
   #     for wmi in reversed(thisbr):
    #        print (wmi,gl.WM.cp[wmi].mentstr,gl.WM.cp[wmi].parent," p=",gl.WM.cp[wmi].p," g=",gl.WM.cp[wmi].g," wmuse:",gl.WM.cp[wmi].wmuse," next:",gl.WM.cp[wmi].next," consistency=",gl.WM.cp[wmi].c)
     #   print ("BRANCH:",br,thisbr)
    gl.test.testf.close()
    gl.test.resultf.close()
    print ("branches:",gl.WM.branch," branchvalue:",gl.WM.branchvalue)
    print ("TIME USAGE REPORT IN BPS FOLLOWS.",end-s, " s total run time.")
    for t in sorted(gl.args.timecheck,reverse=False):
        print (t, int(gl.args.timecheck[t]*10000/(end-s)))
    gl.test.check_result()                  # compare _base to _result file
    if gl.error>0: print ("ERROR in process_CDrel. count =",gl.error)

#gl.KB.walk_db(24)                        # walk through parents of a concept, print them
#gl.unittest.utest_read_concept()            # run read_concept unit test
#gl.unittest.test_branch_functions()         # tests branch handling functions

gl.log.logf.close()

