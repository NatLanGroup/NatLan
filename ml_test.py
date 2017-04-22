import time
from mentalese import *
from nltk.tree import Tree

def to_nltk_tree(node):
    if node.n_lefts + node.n_rights > 0:
        return Tree(node.lemma_+node.pos_+node.dep_, [to_nltk_tree(child) for child in node.children])
    else:
        return node.lemma_+node.pos_+node.dep_

def get_spacy_parser(language='en'):
    print("Loading text parsers for language '%s' (this may take a while...)" % language)
    start = time.time()
    result = spacy.load(language)
    end = time.time()
    print('Language loaded, took %d seconds' % (end-start))
    return result
    
nlp = get_spacy_parser()
f = open("ml_test_in.txt",'r')
print('Input file loaded')  
f_doc = f.read()
doc=nlp(f_doc)
f.close()
f = open("ml_test_out.txt",'w') 
for sent in doc.sents:
    mentalese_trans(sent.root)
    print(get_concept(sent.root).mentalese, file=f)
    #to_nltk_tree(sent.root).pretty_print()
f.close()    
print('Output file generated')