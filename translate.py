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
        self.logf = open("logtr.txt", "w")

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

    def __init__(self, parse, rulesf):
        self.parse = None  # spacy output
        self.rules = dict()
        self.irreg_verb = {"is":"be", "has":"have"}                 # irregular verbs
        self.verbs_se = set(["causes","pauses","uses","abuses","browses","aches","releases"])   # verbs ending "se"
        self.verb_inge = set(["living","countershading","taking","moving"])  # verbs ending e, live -> living  
        self.nowildcard = 200                                   # bonus for a rule that has a [] expression with no wildcards
        self.punishwildcard = 2                                 # piunishment for % character
        self.enclosed = 100                                     # bonus if rule is encolsed in brackets like (xxx)
        self.priority = {                                       # on rule left side: assign bonuses to various rule fragments
            "[.:PUNCT,.,punct]":-200, "[and:CCONJ,CC,cc]":100, "[by:ADP,IN]":-100
        }
        self.right_priority = {                                 # on rule right side: assign bonuses
            "SENT+":-1 }
        try:
            self.rule_file = open(rulesf, "r")
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
            wcount = rule.count("%")
            rulenow = len(rule)+1000-wcount*self.punishwildcard     # current rule length with % punishment
            if wcount == 0: rulenow = rulenow+self.nowildcard       # add bonus for no wildcard
            if rule[0]=="(" and rule[-1]==")":                      # rule is enclosed in brackets ()
                rulenow = rulenow + self.enclosed                   # add bonus for ()
            for pritem in self.priority:                            # look for priortized items on left side
                if pritem in rule:                                  # a priority item found
                    rulenow = rulenow + self.priority[pritem]       # distort length of rule
            for pritem in self.right_priority:                      # look for priortized items on right side
                if pritem in self.rules[rule]:                       # a priority item found
                    rulenow = rulenow + self.right_priority[pritem]       # distort length of rule
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
#        print ("REPLACE in row=",i," rule left:",bestrule," rule right:",new_rule," new row:",self.evaluate[i])
        self.parse.logf.write("REPLACE in row="+str(i)+" rule left:"+bestrule+" rule right:"+new_rule+" new row:"+self.evaluate[i]+"\n")
        return

    def change_Capital(self,word,type,i):               # change capital letters in word
        new_word = word[:]
        if type !="PROPN":                                      # not proper noun
            new_word = word.lower()
            self.evaluate[i] = self.evaluate[i].replace(word+":"+type,new_word+":"+type)    # type added not to change every occurence
        return new_word[:]

    def change_Plural(self,word,type,i,j):              # convert plural npun to singular form
        singular = word[:]
        if type == "NOUN":
            subtype = ""
            row=self.evaluate[i]; j=j+1
            while row[j] != ",":
                subtype = subtype+row[j]                        # collect the nextz attribute in spacy
                j+=1
            if subtype=="NNS" and word[-1]=="s" and len(word)>2:  # NNS means plural noun
                if word[-2] != "e": singular = word[:-1]            # cut off ending s
                else:                                               # "e" before s
                    singular = word[:-1]                            # default: cut off s
                    if word[-3] in "sox":                           # -ses or -oes or -xes
                        singular = word[:-2]                        # cut off -es
                    if word[-3]=="h" and len(word)>3:
                        if word[-4] in "sc":                        # -shes or -ches
                            singular = word[:-2]
                    if word[-3]=="i" and len(word)>3:               # -ies
                        singular = word[:-3]+"y"                    # babies -> baby
                self.evaluate[i] = self.evaluate[i].replace(word+":"+type,singular+":"+type)
        return len(singular)-len(word)                          # how much shorter got the row

    def change_Ing(self,word,type):                 # convert -ing form of verb to normal form
        normal=word[:]
        if word[-3:]=="ing":
            normal=word[:-3]                                        # cut off -ing
            if word in self.verb_inge:                              # living -> live
                normal = normal+"e"
        return normal[:]

    def change_Third(self,word,type):               # convert verb third person to normal form
        singular = word[:]
        if word[-2]!="e" or word in self.verbs_se:                  # not an e before the s or normal form ends "se"
            singular = word[:-1]                                    # cut off s
        else:
            singular = word[:-1]                                    # default: cut off s
            if word[-3] in ["s","x","o"]:                           # ending ses, xes, oes
                singular = word[:-2]
            if word[-3]=="h" and len(word)>3:
                if word[-4] in ["s","c"]:                           # ending shes, ches
                    singular = word[:-2]
            if word[-3]=="i" and len(word)>3:                       # ending ies
                singular = word[:-3]+"y"
        if len(word)==4 and ord(word[0])==226 and word[3]=="s":     # 's instead of is
            singular="be"                                           # convert to be
        return singular[:]
    
    def change_Other(self,word,type,i,j):               # other changes
        singular = word[:]
        if type == "PART":
            if len(word)==4 and ord(word[0])==226 and word[3]=="s":   # ['s:PART,POS,case]  birtokos jel
                singular="ss"                                       # convert to ss
        if singular!=word:                                          # something changed
            self.evaluate[i] = self.evaluate[i].replace(word+":"+type,singular+":"+type)
        return len(singular)-len(word)

    def change_Verb(self,word,type,i,j):                # convert verbs to normal form
        singular=word[:]
        if type=="VERB":
            subtype=""
            row=self.evaluate[i]; j=j+1
            while row[j]!=",":                                      # get subtype before the ,
                subtype=subtype+row[j]                              # the next attribute in spacy
                j+=1
            if word in self.irreg_verb:                             # irregular verb
                singular=self.irreg_verb[word]                      # apply the specified form
            else:
                if subtype == "VBG":                                # -ing form of verb
                    singular=self.change_Ing(word[:],type[:])       # transform -ing
                if subtype == "VBZ" and word[-1]=="s" and len(word)>2:  # VBZ means third person form
                    singular=self.change_Third(word[:],type[:])     # transform third person
            if singular!=word:                                      # something changed, do replace
                self.evaluate[i] = self.evaluate[i].replace(word+":"+type,singular+":"+type)
        return len(singular)-len(word)

    def change_SomeLetters(self,i):                     # change some letters in teh i-th row. Capital letter, plurals, third person etc.
        inword=0; intype=0; j=0                                     # morphology processing can be done if independent from rules.
        while j < len(self.evaluate[i]):                            # characters of the row
            row = self.evaluate[i]
            char=row[j]
            if char=="[":                                           # word will follow, [xxx:NOUN,...]
                inword=1; word=""
            if char == ":":                                         # end of word
                inword=0; intype=1; type=""                         # type starts
            if intype==1 and char!=":":                             # we are in the type part
                if char!=",": type=type+char                        # collect type
                else:                                               # we are at ",", type is complete, we process this word now
                    intype=0
                    word = self.change_Capital(word[:],type[:],i)   # change capital letter
                    change=self.change_Plural(word[:],type[:],i,j)  # convert plural nouns to singular form
                    j=j+change                                      # set back j if word became shorter
                    change = self.change_Verb(word[:],type[:],i,j)  # convert verb to nominal form
                    j=j+change                                      # set back j if word became shorter
                    change=self.change_Other(word[:],type[:],i,j)   # other changes (not NOUN or VERB)
                    j=j+change                                      # set back j if word became shorter                    
            if inword==1 and char!="[":
                word=word+char                                      # collect word
            j=j+1

    def translate(self):                                # translate the spacy rows in the input to mentalese
        for i, roworig in enumerate(self.evaluate):                 # all rows in the input.
            self.change_SomeLetters(i)                              # change some letters in the spacy text before translating
            nochange=0                                              # nochange means nothing changed in this round
            while nochange!=1:                                      # checking every row many times until no change occurs
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
                    nochange=0
                else: nochange=1  
            if len(self.evaluate[i])>3: print (self.parse.eng[i],"   ",self.evaluate[i])

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
        
        transl.parse.logf.close()             # close log file

        print("The End")
    else:
        print(len(sys.argv))
        description()