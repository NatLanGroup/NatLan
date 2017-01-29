import sys, gl, conc, wrd, testing

def process_testinput (tf):                  # input is the Testinput object
    for ri in range(len(tf.mentalese)):     # take mentalese items (rows in test input file)
        counter=0; tfment=[]
        tfment.append(tf.mentalese[ri])
        starti=gl.WM.ci                             # start position in WM
        while (len(tfment[0])>3 and counter<20):    # counter protects against endless loop
            gl.WM.read_concept(tfment)              # store concepts in WM
            counter=counter+1
        endi = gl.WM.ci                             # end position in WM
        if (tf.question[ri]==1):                    # if yes, then on endi we assume a question
            pix=0
            for pit in gl.WM.cp[endi].parent:       # replace "?" words with parent=-1
                for wi in gl.WM.cp[pit].wordlink:
                    if (gl.WL.wcp[wi].word=="?"):
                        gl.WM.cp[endi].parent[pix]=-1
                pix=pix+1
            tf.systemanswer[ri][:] = gl.WM.answer_question(endi)[:]    # answer question and record concept indices
        if (tf.question[ri]==1):
            if len(tf.systemanswer[ri])==0:                         # no answer
                if -1 not in gl.WM.cp[endi].parent:                 # question not for parent
                    starti=endi                                     # keep question
                    tf.systemanswer[ri].append(endi)                # the question is the answer
                    gl.WM.cp[endi].p=0.5                            # set p for unknown
            for i in range(endi-starti): gl.WM.remove_concept()        # remove question from WM
            endi=gl.WM.ci
        gl.test.write_result(ri)                    # write reult file
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

if gl.args.argnum == 2:
    gl.test = testing.Testinput(sys.argv[1])
    gl.test.readtest()
    process_testinput (gl.test)
    gl.test.testf.close()
    gl.test.resultf.close()

#gl.unittest.utest_read_concept()            # run read_concept unit test

gl.log.logf.close()
