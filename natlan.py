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

            #generate from every rule:
            for concept_index in range(0, endi):
                reasoning = reason.Reasoning()
                rules_list = reasoning.getRulesFor(concept_index)

                strToPrint = ""
                for k in range(0, len(rules_list)):
                    strToPrint += gl.KB.cp[rules_list[k]].mentstr
                    strToPrint += " , "
                print("{} matches {}".format(gl.WM.cp[concept_index].mentstr, strToPrint))

            tf.systemanswer[ri][:] = gl.WM.answer_question(starti,endi)[:]    # answer question and record concept indices
        gl.test.write_result(ri)                    # write result file
        ri=ri+1
               
    
gl.args = gl.Arguments()  # initialize
gl.WM = conc.Kbase("WM")  # WORKING MEMORY
gl.KB = conc.Kbase("KB")  # KNOWLEDGE BASE
gl.WL = wrd.Wlist("WL")  # WORD LIST
gl.log = gl.Logging()

test1 = conc.Concept()
test1.add_parents([-1, 17])
result = gl.WM.search_inlist(test1)
gl.unittest=testing.Temptest()              # initialize temporary tests

thisrule=reason.Rule(2)

if gl.args.argnum == 2:
    gl.unittest.test_implication()
    gl.test = testing.Testinput(sys.argv[1])
    gl.test.readtest()
    process_testinput (gl.test)
    gl.test.testf.close()
    gl.test.resultf.close()

gl.KB.walk_db(24)                        # walk through parents of a concept, print them
#gl.unittest.utest_read_concept()            # run read_concept unit test
#gl.unittest.test_branch_functions()         # tests branch handling functions

gl.log.logf.close()

