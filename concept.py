from relation import Relation


def merge_probability(p1:float, p2:float) -> float:
    d1 = abs(p1 - .5)
    d2 = abs(p2 - .5)
    if d1 > d2:
        return p1
    return p2


class Concept:

    def __init__(self, mentalese: str, relation: str, probability: float=1.0, is_processed: bool=False):

        self.mentalese = mentalese
        self.relation = relation
        self.probability = probability
        self.is_processed = is_processed

    def __str__(self):     #print
        return "Concept(mentalese=%r,relation=%r,p=%r,proc_state=%r)" % \
               (self.mentalese, self.relation, self.probability, self.is_processed)
               
    def update_mentalese(self):
            if self.probability < 1.0:
                self.mentalese += 'p='+str(self.probability)    
            
    def set_mentalese(self, m1: str, m2: str= None, rel_type: str = 'W'):
        if rel_type == 'W':
            self.mentalese = m1
            return
        self.relation = rel_type
        if rel_type == 'MC':
            self.mentalese = m1+','+m2
            return
        self.mentalese = self.relation + '(' + m1 + ',' + m2 + ')'
        self.update_mentalese()
            
    def set_probability(self, value:float) -> None:
        if self.probability != value:
            self.probability = value
            self.update_mentalese()

    def set_is_processed(self, value:bool) -> None:
        if self.is_processed != value:
            self.is_processed = value
    
    @staticmethod
    def word(label: str) -> 'Concept':
        return Concept(label, Relation.Word, [])

    def is_question(self) -> bool:
        if self.mentalese == '?':
            return True
        return False

if __name__ == "__main__":
    print("This is a module file, for tests run ml_test.py instead")