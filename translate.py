import sys

def description():
    print("This module translates the spacy output to mentalese, with the help of rules.\n"
          "The parameters:\n"
          "\t\t [1]:  txt file which contains the spaCy output\n"
          "\t\t [2]:  txt file which contains rules")

def addspaces(ins,num):
    stt=""
    for i in range(num-len(ins)):
        stt=stt+" "
    return stt

class Parserinput:
    """class what reads and contain the input: the spacy output and the rules for the tranclation """

    def __init__(self, testfilename):
        self.eng = []  # english text
        self.mentalese = []  # mentalese version of english
        self.parse = []
        try:
            self.testf = open(testfilename, "r")
            self.read_test()  # reading the input
        except:
            print("ERROR: Test input: input file could not be opened:" + testfilename)

    def read_test(self):
        for line in self.testf:
            i = 0;
            epos = -1;
            mpos = -1;
            apos = -1;
            ppos = -1
            self.eng.append("");
            self.mentalese.append("")  # each list must have a new item
            self.parse.append("")
            rowi = len(self.eng) - 1  # index of the new item
            while i < len(line):
                if "e/" in line[i:i + 2]: epos = i  # order of e/ m/ // is fixed but all are optioonal
                if "m/" in line[i:i + 2]:
                    mpos = i
                    if epos > -1: self.eng[rowi] = line[epos + 2:mpos].strip()
                if "s/" in line[i:i + 2]:
                    ppos = i
                    self.parse[rowi] = line[ppos:].strip()
                    if epos > -1 and mpos == -1:
                        self.eng[rowi] = line[epos + 2:ppos].strip()
                    if mpos > -1 and apos == -1: self.mentalese[rowi] = line[mpos + 2:ppos].strip()
                i += 1
            if epos > -1 and mpos == -1 and apos == -1 and ppos == -1:
                self.eng[rowi] = line[epos + 2:i].strip()
            if mpos > -1 and apos == -1 and ppos == -1:
                self.mentalese[rowi] = line[mpos + 2:i].strip()
            self.parse[rowi] = self.parse[rowi].replace("s/", "")
            self.parse[rowi].replace(" ","")

class Translator():
    """this class translate the spacy parser output with the help of the rules"""

    def __init__(self, parse, rules):
        self.parse = None  # spacy output
        self.rules = dict()
        self.nowildcard = 200                                   # bonus for a rule that has a [] expression with no wildcards
        self.priority = {                                       # assign bonuses to various rule fragments
            "[.:PUNCT,.,punct]":-200, "SENT+":-100, "[and:CCONJ,CC,cc]":200
        }
        try:
            self.rule_file = open(rules, "r")
            self.read_rulefile()
        except:
            print("ERROR: input rule file cannot be found")
            raise
        try:
            self.parse = Parserinput(parse)
            self.evaluate = self.parse.parse[:]
        except:
            print("ERROR: spacy input cannot be found or processed")
            raise

    def read_rulefile(self):
        """saving the rules in a dictionary"""
        for i,line in enumerate(self.rule_file):
            line = line.replace(" ", "").replace("\n", "").split('>')
            try:
                self.rules[line[0]] = line[1]
            except:
                if len(line)<2: print("ERROR in rule file: no > character found in row:",i)
                else: print ("ERROR in read_rulefile")
                raise
            
    def in_Bracket(self,rule,ui,separator):                 # identify (%1) or [%1] , wildcard in brackets
        if ui-1>=0:                                         # character before exists in rule
            if separator == ")":                            # try detect ()
                if rule[ui-1] == "(":                       # () detected
                    return True                             # Yes, variable in brackets
            elif separator == "]":                          # try detect []
                if rule[ui-1] == "[":                       # [] detected
                    return True
        return False

    def match_it(self,rule,ui,row,rowstart,rowpos,vars):    # check that character or %1 wildcard match in rule and row
        mlen = [0,0]                                                # 0 means no match, otherwise the length of match in rule and row
        rowc = row[rowstart+rowpos]
        rulec = rule[ui]
        endofword = [";",":","]","+"]                               # characters where matching must end
        if rulec != "%":                                            # in rule, we are not at a wildcard
            if rowc == rulec:                                       # single character match
                mlen[0]=1
                mlen[1]=1                                           # length of match
        else:                                                   # we are at %, this will always match
            mlen[0]=1                                           # for the % character
            if ui+1 < len(rule):
                if rule[ui+1].isdigit()==True or rule[ui+1].isalpha()==True:   # %1 or %a
                    mlen[0]=2                                   # a single digit or alphanumeric can follow %
            if ui+mlen[0]<len(rule):                            # this is not the very end of the rule
                separator = rule[ui+mlen[0]]                    # the character after %1 serves as separator, here match must end
                endofword.append(separator)                     # this new separator also indicates end of matching
                if self.in_Bracket(rule,ui,separator):          # the separator is bracket and we have (%1) or [%1]:
                    endofword = [separator]                     # we do not separate anything else, just consider everything in the brackets
            rm=0; openc=0; closec=0
            while rowstart+rowpos+rm<len(row) and not closec>openc and (openc>closec or row[rowstart+rowpos+rm] not in endofword):
                # not too long              do not close too many brackets   do not end when brackets open or when end of word not reached
                rowc = row[rowstart+rowpos+rm]
                if rowc == "(": openc+=1                         # count of opening bracket
                if rowc == ")": closec+=1                        # count of closing bracket
                rm += 1                                         # move position in row while end of word not reached
            if closec>openc: rm=rm-1                            # do not include the additional closing bracket
            mlen[1]=rm                                          # matching length in row
            if mlen[0]==2:                                      # %1 %2 etc in rule: variable value assignment needed
                vars[rule[ui:][:2]] = row[rowstart+rowpos:][:rm]  # store actual values for %1 etc
        return mlen


    def locate_Rule(self,rule,row,vars):                # find rule string (left side) in row string
        rowstart=0; matchcount=0; rowpos=0                          # start of match in row, length of match in rule, and in row
        while matchcount<len(rule) and rowstart+rowpos<len(row):    # until total match, within the row
            matchcount=0                                            # match restart when we start at a new rowstart
            rowpos=0                                                # position in row, from rowstart
            ui=0                                                    # where are we in rule
            while ui<len(rule):                                     # within the rule
                if rowstart+rowpos<len(row):                        # within the row
                    mlen = self.match_it(rule,ui,row,rowstart,rowpos,vars)  # check: does this character match? and how long?
                    if mlen[0]>0:                                   # character does match (0 means no match)
                        ui+=mlen[0]                                 # how long is match in rule
                        rowpos+=mlen[1]                             # how long is match in row
                    else: break
                else: break
            matchcount=ui                                           # matching length
            rowstart+=1                                             # try from next psition in row
        if matchcount==len(rule):                                   # full match
#            print ("LOCATE full match for rule:",rule," rowstart",rowstart," rowpos", rowpos)
            return [rowstart,rowpos]
#        print ("LOCATE no match. rule:",rule,"rowstart",rowstart)
        return None
    
    def get_Bestrule(self,rulefound):                   # select the best rule for which total match was found
        rulelen=0                                                   # best rule length
        ruleselect = ""
        for rule in rulefound:
            rulenow = len(rule)+1000                                # current rule length
            for pritem in self.priority:                            # look for priortized items
                if pritem in rule:                                  # a priority item found
                    rulenow = rulenow + self.priority[pritem]       # distort length of rule
            if rulenow > rulelen:                                   # longest rule so far
                rulelen=rulenow
                ruleselect = rule[:]                                # best rule selected based on length and bonuses
        return ruleselect

    def replace_Rule(self,i,row,bestrule,rulefound,rulevars):       # replace the left rule part with the right part in row
        findpos = rulefound[bestrule]                               # where is the best rule in row
        vars = rulevars[bestrule]                                   # map of variables for best rule
        new_rule = self.rules[bestrule]                             # right side of the rule, the new string to be inserted
        for wildcard in vars:
            new_rule = new_rule.replace(wildcard,vars[wildcard])    # replace rule wildcard with actual values
        self.evaluate[i] = row[:findpos[0]-1] + new_rule + row[findpos[0]+findpos[1]-1:]   # perform replacement in row
        self.evaluate[i] = self.evaluate[i].replace("\r","")        # remove \r newline chgaracters
        print ("REPLACE in row=",i," rule left:",bestrule," rule right:",new_rule," new row:",self.evaluate[i])
        return

    def translate(self):                                # translate the spacy rows in the input to mentalese
        for i, roworig in enumerate(self.evaluate):                 # all rows in the input.
            for count in range(0,30):                               # checking every row many times
                bestrule=""                                         # the best of all matching rules
                rulefound={}                                        # map to hold rules for which we have full match
                rulevars={}                                         # dictionary to map wildcards %1 %2 to actual values
                for rule in self.rules:                             # try all rules on this row
                    row = self.evaluate[i]                          # pointer to the current row. Rows keep changing.
                    vars = {}                                       # dictionary for the actual values of %1 %2 etc
                    findpos = self.locate_Rule(rule[:],row[:],vars) # find the rule string in the row string
                    if findpos is not None:
                        rulefound[rule]=findpos[:]                  # remember the location of this match for this rule
                        rulevars[rule] = dict(vars)                 # copy to remember the vars mapping we found
                                                                    # if the rule has several matches, the last one is remembered
                if rulefound != {}:                                 # we do have some full match
                    bestrule = self.get_Bestrule(rulefound)         # after all rules checked, select the best one to apply now
                if bestrule != "":                                  # a rule to be applied is selected
                    self.replace_Rule(i,row,bestrule[:],rulefound,rulevars)   # replace the left rule part with the right part
                    

    def write_result(self):  # write output file
        with open('output.txt', 'w+') as output:
            for row,x in enumerate(self.parse.eng):
                output.write(" e/ ")
                output.write(self.parse.eng[row])
                output.write(addspaces(self.parse.eng[row],45))
                output.write(" m/ ")
                output.write(self.evaluate[row])
                output.write(addspaces(self.evaluate[row], 125))
                output.write(" n/ ")

                output.write(self.parse.mentalese[row])
                output.write(addspaces(self.parse.mentalese[row], 100))
                output.write(" s/ ")
                output.write(self.parse.parse[row])

                output.write("\n")


if __name__ == '__main__':
    if len(sys.argv) == 3:
        parse = sys.argv[1]
        rules = sys.argv[2]

        transl = Translator(parse, rules)
        transl.translate()
        transl.write_result()

        print("The End")
    else:
        print(len(sys.argv))
        description()