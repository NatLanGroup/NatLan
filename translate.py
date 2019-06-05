import sys, re


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

class Translator():
    """this class translate the spacy parser output with the help of the rules"""

    def __init__(self, parse, rules):
        self.parse = None  # spacy output
        self.rules = dict()
        try:
            self.rule_file = open(rules, "r")
            self.read_files()
            self.parse = Parserinput(parse)
            self.evaluate = self.parse.parse.copy()
        except:
            print("ERROR: input can not found")
            raise

    def read_files(self):
        """saving the rules in a dictionary"""
        for line in self.rule_file:
            line = line.replace(" ", "").replace("\n", "").split('>')
            self.rules[line[0]] = line[1]

    def translate(self):
        """This is where the translation happens"""
        """NOT FINISHED YET"""

        # iterating through the rules and replacing the % with regular expression
        for rule in self.rules:
            magic_str = "([A-Za-z\),\(]*)"
            searched_expr = rule.replace("[", "\[").replace("]", "\]") \
                .replace("+", "\+").replace("(", "\(").replace(")", "\)")
            print(searched_expr, ">", self.rules[rule])
            searched_expr = re.sub("%[0-9]|%", magic_str, searched_expr)

            for count in range(0, 5):                                       # checking every row 5 times
                for i, row in enumerate(self.evaluate):
                    found = re.search(searched_expr, row)                   # searching for the rule in the spacy output
                    length_changed = 0

                    # TODO: Refine the translation to work for every rule
                    if found is not None:
                        # if the expression is found than we split the rule and the text component too by ';'
                        # so we can translate the parsed text component by component

                        new_rule = self.rules[rule]
                        original_text = row[found.start():found.end()]
                        rule_components = rule.split(';')
                        text_components = original_text.split(';')

                        for it, r in enumerate(rule_components):          # iterating through the components of the rule

                            var = ""
                            txt = text_components[it]
                            l_t = 0                                        # iterator for the text letters
                            l_r = 0                                        # iterator for the rule letters
                            p = 1
                            while l_r < (len(r)):                          # reading the rule component letter by letter
                                if r[l_r] == txt[l_t]:                     # if the letters are the same in the rule and
                                    l_t += 1                               # in the text then we see the next

                                else:
                                    start_p = l_t
                                    bracket1 = bracket2 = 0

                                    if r[l_r] == '%':                      # if it  is the escape character ('%')...
                                        l_r += 1
                                        if re.match("[0-9]", r[l_r]) \
                                                and l_r != len(r) - 1:     # ...then we search the next non-special
                                            l_r += 1                       # character in the text

                                        while r[l_r] != txt[l_t]:         # we read the text what is in the place of '%'
                                            l_t += 1
                                            if l_t == len(txt):
                                                break
                                            if txt[l_t] == "(":
                                                bracket1 += 1
                                            if txt[l_t] == ")":
                                                bracket1 -= 1
                                                if bracket1 == 0:
                                                    l_t += 1
                                            if l_t == len(txt):
                                                break

                                        var = txt[start_p:l_t + bracket2]
                                    if l_t == len(txt):
                                        p = 0

                                    if re.match("[0-9]", r[l_r - p]):                           # then we paste it...
                                        new_rule = new_rule.replace("%" + r[l_r - p], var)      # ...in the given rule
                                        l_t += 1

                                l_r += 1

                            length_changed += l_t

                        new_rule = new_rule + original_text[length_changed + 2:]
                        self.evaluate[i] = row[:found.start()] + new_rule + row[(found.end()):]
                        print(row)                                  # print for debug purpose
                        print(self.evaluate[i])

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
    #if len(sys.argv) == 3:
        parse = r'spacy.txt' # sys.argv[1]
        rules = r'rules.txt' #sys.argv[2]

        transl = Translator(parse, rules)
        transl.translate()
        transl.write_result()

        print("The End")
    # else:
    #     print(len(sys.argv))
    #     description()