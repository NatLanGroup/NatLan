import sys,spacy
from concept import Concept


def get_concept(token):
    return token.doc.user_token_hooks[token]

def init(token): #initialisation: mentalese is the base form of the words
    for child in token.children:
        init(child)
    token.doc.user_token_hooks[token] = Concept(token.lemma_,'W')
    if token.tag_ == (u'WP' or u'WP$' or u'WRB' or u'WDT'): #what, who replace with '?'
        get_concept(token).set_mentalese('?','W')
    if token.pos_ == u'PROPN':
        get_concept(token).set_mentalese(token.orth_,'W') # instead joe -> Joe      
    
def lvl_1_rule_1(token): # advmod, advmod -> advmod
    if token.head.dep_ == token.dep_ == u'advmod':
        get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(token.head).mentalese,'MC')
        get_concept(token).set_is_processed(True)
        
def lvl_1_rule_2(token): #Q(NOUN,DET)
    if token.head.pos_ == u'NOUN' and token.pos_ == u'DET':
        get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(token.head).mentalese,'Q')
        get_concept(token).set_is_processed(True)                   
def lvl_2_rule_1(token): # NOUN, NOUN -> NOUN
    if token == token.head:
        return
    if token.head.pos_ == token.pos_ == u'NOUN':
        get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(token.head).mentalese,'MC')
        get_concept(token).set_is_processed(True)
            
def lvl_3_rule_1(token): #ADJ, ADJ -> ADJ
    if token.dep_ == u'amod':
        for child in token.head.children:
            if child == token:
                return
            if child.dep_ == token.dep_:
                get_concept(child).set_mentalese(get_concept(child).mentalese,get_concept(token).mentalese,'MC')
                get_concept(token).set_is_processed(True)
            
def lvl_3_rule_2(token): #R(prep,pobj)
    if token.head.dep_ == u'prep' and token.dep_ == u'pobj':
        get_concept(token.head).set_mentalese(get_concept(token.head).mentalese,get_concept(token).mentalese,'R')
        get_concept(token).set_is_processed(True)

def lvl_3_rule_3(token): #R(prep,pobj)
    if (token.head).head.lemma_ == u'same' and token.head.dep_ == u'prep':
        get_concept((token.head).head).set_mentalese(get_concept(token).mentalese,'W')
        get_concept(token).set_is_processed(True)
        get_concept(token.head).set_is_processed(True)
        
def lvl_4_rule_1(token): #F(NOUN,ADJ)
    if token.head.pos_ == u'NOUN' and token.dep_== u'amod':
        get_concept(token.head).set_mentalese(get_concept(token.head).mentalese,get_concept(token).mentalese,'F')
        get_concept(token).set_is_processed(True)
            
def lvl_4_rule_2(token): #same relation -> one group e.g. R(%1,%2), R(%3,%4)
    for child in token.head.children:
        if get_concept(child).is_processed == True:
            return
        if child == token:
            return
        if child.dep_ == token.dep_ == u'prep':
            get_concept(child).set_mentalese(get_concept(child).mentalese,get_concept(token).mentalese,'MC')
            get_concept(token).set_is_processed(True)

def lvl_4_rule_3(token): #ADV, ADJ -> Q(ADV,ADJ)
    if token.pos_ == u'ADJ':
        for child in token.head.children:
            if child == token:
                return
            if child.pos_ == u'ADV':
                get_concept(token).set_mentalese(get_concept(child).mentalese,get_concept(token).mentalese,'Q')
                get_concept(child).set_is_processed(True)
                
def lvl_4_rule_4(token): #ADV, NOUN -> Q(ADV,NOUN)
    if token.pos_ == u'NOUN':
        for child in token.head.children:
            if child == token:
                return
            if child.pos_ == u'ADV':
                get_concept(token).set_mentalese(get_concept(child).mentalese,get_concept(token).mentalese,'Q')
                get_concept(child).set_is_processed(True)
                
def lvl_5_rule_1(token): #A(nsubj, ROOT) or I(nsubj,dobj) with question handling
    if token.head.dep_ == u'ROOT' and token.dep_== u'nsubj':
        if token.head.lemma_ != u'be':
            for child in token.head.children:
                if child.dep_ == u'dobj':
                    if child.lemma_ == (u"what" or u"who"): str = 'A'
                    else: str = 'I'
                    get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(child).mentalese,str)
                    get_concept(child).set_is_processed(True)
                    get_concept(token).set_is_processed(True)
                    return
            get_concept(token.head).set_mentalese(get_concept(token).mentalese,token.head.lemma_,'A')
            get_concept(token).set_is_processed(True)

def lvl_5_rule_2(token): # C(nsubj, attr)
    if token.head.lemma_== u'be' and token.dep_ == u'nsubj':
        for child in token.head.children:
            if child.dep_ == u'attr': #nsubj exist always
                if child.lemma_ == u"same": str = 'D'
                else: str = 'C'
                get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(child).mentalese,str)
                get_concept(token).set_is_processed(True)
                get_concept(child).set_is_processed(True)
                
def lvl_5_rule_3(token): # C(pobj, nsubj)
    if token.head.lemma_== u'be' and token.dep_ == u'pobj':
        for child in token.head.children:
            if child.dep_ == u'nsubj': #nsubj exist always
                get_concept(token.head).set_mentalese(get_concept(child).mentalese,get_concept(token).mentalese,'C')
                get_concept(token).set_is_processed(True)
                get_concept(child).set_is_processed(True)
                
def lvl_5_rule_4(token): # F(nsubj, acomp)
    if token.head.lemma_== u'be' and token.dep_ == u'nsubj':
        for child in token.head.children:
            if get_concept(child).is_processed == True:
                continue
            if child.dep_ == u'acomp': 
                if child.lemma_ == u"same": str = 'D'
                else: str = 'F'
                get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(child).mentalese,str)
                get_concept(token).set_is_processed(True)
                get_concept(child).set_is_processed(True)

def lvl_5_rule_5(token): # F(nsubj, R(prep, %1))
    if token.head.lemma_== u'be' and token.dep_ == u'nsubj':
        for child in token.head.children:
            if get_concept(child).is_processed == True:
                continue
            if child.dep_ == u'prep': 
                get_concept(token.head).set_mentalese(get_concept(token).mentalese,get_concept(child).mentalese,'F')
                get_concept(token).set_is_processed(True)
                get_concept(child).set_is_processed(True)
                
def lvl_6_rule_1(token): # F(A(nsubj, %1), advmod)
    if token.head.dep_ == u'ROOT' and token.head.lemma_ != u'be'and token.dep_== u'advmod':
            get_concept(token.head).set_mentalese(get_concept(token.head).mentalese,get_concept(token).mentalese,'F')
            get_concept(token).set_is_processed(True)

def lvl_6_rule_2(token): #F(be, R(prep, %1))
    if token.head.dep_ == u'ROOT' and token.head.lemma_ != u'be' and token.dep_== u'prep':
            get_concept(token.head).set_mentalese(get_concept(token.head).mentalese,get_concept(token).mentalese,'F')
            get_concept(token).set_is_processed(True)

def lvl_7_rule_1(token):
    if token.lemma_ == u'?':
        if token.head.lemma_ == u"be":
            get_concept(token.head).set_mentalese(get_concept(token.head).mentalese+'?')
        else:    
            for child in token.head.children:
                if child.dep_ == u"aux":
                    get_concept(token.head).set_mentalese(get_concept(token.head).mentalese+'?')
                    get_concept(child).set_is_processed(True)
        get_concept(token).set_is_processed(True)
        
def lvl__1(token):
    for child in token.children:
        lvl__1(child)
    if get_concept(token).is_processed == True:
        return
    lvl_1_rule_1(token)
    lvl_1_rule_2(token)
    
def lvl__2(token):
    for child in token.children:
        lvl__2(child)
    if get_concept(token).is_processed == True:
        return
    lvl_2_rule_1(token)

def lvl__3(token):
    for child in token.children:
        lvl__3(child)
    if get_concept(token).is_processed == True:
        return
    lvl_3_rule_1(token)
    lvl_3_rule_2(token)
    lvl_3_rule_3(token)
    
def lvl__4(token):
    for child in token.children:
        lvl__4(child)
    if get_concept(token).is_processed == True:
        return
    lvl_4_rule_1(token)
    lvl_4_rule_2(token)
    lvl_4_rule_3(token)
    lvl_4_rule_4(token)

def lvl__5(token):
    for child in token.children:
        lvl__5(child)
    if get_concept(token).is_processed == True:
        return
    lvl_5_rule_1(token)
    lvl_5_rule_2(token)
    lvl_5_rule_3(token)
    lvl_5_rule_4(token)
    lvl_5_rule_5(token)

def lvl__6(token):
    for child in token.children:
        lvl__6(child)
    if get_concept(token).is_processed == True:
        return
    lvl_6_rule_1(token)
    lvl_6_rule_2(token)

def lvl__7(token):
    for child in token.children:
        lvl__7(child)
    lvl_7_rule_1(token)

def mentalese_trans(token):
    init(token)
    lvl__1(token)
    lvl__2(token)
    lvl__3(token)
    lvl__4(token)
    lvl__5(token)
    lvl__6(token)
    lvl__7(token)
    
if __name__ == "__main__":
    print("This is a module file, for tests run ml_test.py instead")