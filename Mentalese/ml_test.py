import time
from mentalese import *
from nltk.tree import Tree

def to_nltk_tree(node): #visual reepresentation of spacy hierarchy
    if node.n_lefts + node.n_rights > 0:
        return Tree(node.lemma_+node.pos_+node.dep_, [to_nltk_tree(child) for child in node.children])
    else:
        return node.lemma_+node.pos_+node.dep_
        
def addspaces(ins,num):
    stt=""
    for i in range(num-len(ins)):
        stt=stt+" "
    return stt
        
def get_spacy_parser(language='en'):
    print("Loading text parsers for language '%s' (this may take a while...)" % language)
    start = time.time()
    result = spacy.load(language)
    end = time.time()
    print('Language loaded, took %d seconds' % (end-start))
    return result
    
class Testinput:
    def __init__(self, testfilename):
        self.name = testfilename
        self.eng = []           # english text
        self.mentalese = []     # mentalese version of english
        self.systemanswer = []  # output of the system
        self.evaluation = []    # evaluation of system output including mentalese translation
        self.comment = []       # comment
        try:
            self.testf = open(testfilename, "r")
            pos=testfilename.find(".")
            self.resultf = open(testfilename[:pos]+"_result"+testfilename[pos:],"w")    #output file
        except:
            print("ERROR: Testinput: input or output file could not be opened:"+self.name)

    def readtest(self):
        print("Test file started:"+ self.name)
        for line in self.testf:
            i = 0;
            epos = -1;
            mpos = -1;
            apos = -1;
            comment = -1
            self.eng.append("");
            self.mentalese.append("")  # each list must have a new item
            self.systemanswer.append([]);
            self.evaluation.append("")
            self.comment.append("")
            rowi = len(self.eng) - 1  # index of the new item
            while i < len(line):
                if "e/" in line[i:i + 2]: epos = i  # order of e/ m/ // is fixed but all are optioonal
                if "m/" in line[i:i + 2]:
                    mpos = i
                    if epos > -1: self.eng[rowi] = line[epos + 2:mpos].strip()
                if "//" in line[i:i + 2]:
                    comment = i
                    self.comment[rowi]=line[comment:].strip()
                    if epos > -1 and mpos == -1:
                        self.eng[rowi] = line[epos + 2:comment].strip()
                    if mpos > -1 and apos == -1: self.mentalese[rowi] = line[mpos + 2:comment].strip()
                i += 1
            if epos > -1 and mpos == -1 and apos == -1 and comment == -1:
                self.eng[rowi] = line[epos + 2:i].strip()
            if mpos > -1 and apos == -1 and comment == -1:
                self.mentalese[rowi] = line[mpos + 2:i].strip()

    def eval_test(self,rowindex):                       # evaluation string of a row of the input file
        finalanswers=[]
        eval="BAD    "
        if (self.mentalese[rowindex]==self.systemanswer[rowindex]):                # *** Translation successful ***
            eval=" OK    "
        return eval

 
    def write_result(self,rowindex):                    # write output file
        if (len(self.eng[rowindex])==0 and len(self.mentalese[rowindex])==0 and len(self.comment[rowindex])>0):
            self.resultf.write(self.comment[rowindex])
        else:
            self.resultf.write(" /e ")
            self.resultf.write(self.eng[rowindex])
            self.resultf.write(addspaces(self.eng[rowindex],45))               # fill spaces up to 45 characters
            self.resultf.write(" /m ")
            self.resultf.write(self.mentalese[rowindex])
            self.resultf.write(addspaces(self.mentalese[rowindex],56))
            self.resultf.write(" /s ")
            self.resultf.write(str(self.systemanswer[rowindex]))
            self.resultf.write(addspaces(self.systemanswer[rowindex],56))
            evals=self.eval_test(rowindex)
            self.resultf.write(evals)                       # write OK, BAD
            self.resultf.write(self.comment[rowindex])
        self.resultf.write("\n")
        
print("Importing spaCy")
nlp = get_spacy_parser()
try:
    t = Testinput(sys.argv[1])
    t.readtest()
    for rowi in range(len(t.eng)):
        doc=nlp(t.eng[rowi])
        for sent in doc.sents:
            mentalese_trans(sent.root)
            t.systemanswer[rowi] = get_concept(sent.root).mentalese
        t.write_result(rowi)
    print('Testoutput file generated')
except:
    print("ERROR: Testfile not founded")
    
#################### FOR OTHER TEST ####################
#print('Input file loaded')  
#f_doc = f.read()
#doc=nlp(f_doc)
#doc=nlp(u"Is the garden a place?")
#f.close()
#f = open("ml_test_out.txt",'w') 
#for sent in doc.sents:
    #mentalese_trans(sent.root)
    #print(get_concept(sent.root).mentalese, file=f)
    #to_nltk_tree(sent.root).pretty_print()
#f.close()    
#print('Output file generated')