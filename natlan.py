import sys, gl, conc, wrd, testing

gl.args = gl.Arguments()  # initialize
gl.WM = conc.Kbase("WM")  # WORKING MEMORY
gl.KB = conc.Kbase("KB")  # KNOWLEDGE BASE
gl.WL = wrd.Wlist("WL")  # WORD LIST
gl.log = gl.Logging()

#gl.KB.add_concept(3, 3, [9, 5])
#gl.WL.add_word("pista")
#gl.WM.add_concept(3, 1, [19])
#gl.WM.add_concept(4, 2, [12, 17])
#gl.WL.add_word("joska")

test1 = conc.Concept()
test1.add_parents([-1, 17])
result = gl.WM.search_inlist(test1)

if gl.args.argnum == 2:
    gl.test = testing.Testinput(sys.argv[1])
    gl.test.readtest()
    print("input file read test - row 3 eng:", gl.test.eng[2], "row 5 mentalese:", gl.test.mentalese[4], "goodanswer:",
          gl.test.goodanswer[4])
    gl.test.testf.close()

gl.WM.read_mentalese("mentalese_test_input.txt")

gl.log.logf.close()
#print(gl.KB.cp[0].parent, "word with index 1=", gl.WL.wcp[1].word, "search:", result)
