import sys, gl, conc, wrd, testing, reason

def process_testinput (tf):                  # input is the Testinput object
    for ri in range(len(tf.mentalese)):     # take mentalese items (rows in test input file)
        counter=0; tfment=[]
        tfment.append(tf.mentalese[ri])
        starti=gl.WM.ci                             # start position in WM
        while (len(tfment[0])>3 and counter<20):    # counter protects against endless loop
            gl.WM.read_concept(tfment)              # store concepts in WM
            counter=counter+1
        gl.WM.move_rule(tf,ri,starti)               # if this is a rule, move to KB
        endi = gl.WM.ci                             # end position in WM
        if (tf.question[ri]==1):                    # if yes, then on endi we assume a question
            tf.systemanswer[ri][:] = gl.WM.answer_question(starti,endi)[:]    # answer question and record concept indices
        gl.test.write_result(ri)                    # write result file
        gl.reasoning.actual=starti+1
        while starti > 0 and starti!=gl.WM.ci:      # reason on new concept and on all reasoned concepts
            startiremember=gl.WM.ci
            gl.reasoning.createConceptRules(starti, gl.WM.cp.__len__())     #add initial kb_rules content
            gl.reasoning.perform_Reason(starti+1, gl.WM.cp.__len__())         #convert kb_rules, add rule_match, add reasoned concepts
            starti=startiremember

gl.args = gl.Arguments()  # initialize
gl.WM = conc.Kbase("WM")  # WORKING MEMORY
gl.KB = conc.Kbase("KB")  # KNOWLEDGE BASE
gl.WL = wrd.Wlist("WL")  # WORD LIST
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
    process_testinput (gl.test)
    i=0
    for wmi in gl.WM.cp:
        print (i,wmi.mentstr,wmi.p,wmi.parent,"kb_rules:",wmi.kb_rules,"rule_match",wmi.rule_match)
        i+=1
    i=0
    for wmi in gl.KB.cp:
        print (i,wmi.mentstr,wmi.parent)
        i+=1
    gl.test.testf.close()
    gl.test.resultf.close()

#gl.KB.walk_db(24)                        # walk through parents of a concept, print them
#gl.unittest.utest_read_concept()            # run read_concept unit test
#gl.unittest.test_branch_functions()         # tests branch handling functions

gl.log.logf.close()

