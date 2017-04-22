from enum import Enum

class Relation(Enum):
    Word = 'W'
    Similar = 'S'
    Identical = 'D'
    Class = 'C'
    Feature = 'F'
    Determination = 'Q'
    Action = 'A'
    Impact = 'I'
    Relative = 'R'
    Time = 'T'
    Part = 'P'
    More = 'M'
    Implication = 'IM'
    NecessaryCondition = 'N'
    Relevance = 'V'
    And = 'AND'
    Or = 'OR'
    Not = 'NOT'
    MergeConcept = 'MC'
    def __init__(self, relation_id:str):
        self.id = relation_id

    def __repr__(self):
        return self.name

    @staticmethod
    def find(val:str) -> float:
        for name, member in Relation.__members__.items():
            if member.id == val:
                return member

        raise ValueError('Unknown relation type: '+val)

    def id(self) -> str:
        return self.id

if __name__ == "__main__":
    print("This is a module file, for tests run ml_test.py instead")