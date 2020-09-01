import gl
from timeit import default_timer as timer

class Word:
    def __init__(self, wordstring):
        self.word = str(wordstring)  # a Word object has the word string itself
        self.wchild = []  # a Word object has the meanings, indices in KB


class Wlist:
    def __init__(self, instancename):
        self.wcp = []
        self.wci = -1
        self.wname = instancename

    def add_word(self, new_word, g_value=-1):           # add new word to the word list WL
        if g_value==-1: g_value=gl.args.gmax
        self.wcp.append(Word(new_word))                 # add the object
        self.wci = len(self.wcp) - 1                    # current index in WL
        kbi=gl.KB.add_concept(gl.args.pmax, 1, [], [], g_value)    # create the concept for the word meaning. Parent is empty.
        gl.KB.cp[kbi].wordlink.append(self.wci)         # set word link in KB
        gl.KB.cp[kbi].mentstr = new_word[:]
        self.wcp[self.wci].wchild.append(gl.KB.ci)      # add the meaning concept as child in the word object.
        gl.log.add_log(
            (self.wname, " add_word ", self.wcp[self.wci].word, " wordindex=", self.wci, " KB index=", gl.KB.ci))
        return gl.KB.ci

    def find(self,new_word):
        s=timer()
        for index in range(len(self.wcp)):
            if self.wcp[index].word == new_word:
                return self.wcp[index].wchild[0]
        gl.args.settimer("word_01: find_word",timer()-s)
        return -1

    def find_word(self,new_word):
        s=timer()
        for index in range(len(self.wcp)):
            if self.wcp[index].word==new_word:
                return index
        gl.args.settimer("word_01: find_word",timer()-s)
        return -1
    

if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
