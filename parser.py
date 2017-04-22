import sys,spacy
import time

def get_spacy_parser(language='en'):
    print("Loading text parsers for language '%s' (this may take a while...)" % language)
    start = time.time()
    result = spacy.load(language)
    end = time.time()
    print('Language loaded, took %r seconds' % (end-start))
    return result
    
if __name__ == "__main__":
    print("This is a module file, for tests run ml_test.py instead")