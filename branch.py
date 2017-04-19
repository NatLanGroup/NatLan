import gl

def get_previous_concepts(beforei):            # returns the id list of previous concepts (inclusive)
    previous_concepts = []
    curri = beforei
    while curri != -1:
        previous_concepts.append(curri)
        curri = gl.WM.cp[curri].previous
    return previous_concepts

def search_previously(whati, beforei):        # returns True if the id (whati) appears previously on the branch (before beforei)
    curri = beforei
    while curri != -1:
        if curri == whati:
            return True
        curri = gl.WM.cp[curri].previous
    return False
    
def search_on_branch(whati, branchi):
    # returns True if the id (whati) appears on the branch
    # in fact when whati and branchi are on the same branch, i.e. in the same 'domain'
    return search_previously(whati, branchi) or search_previously(branchi, whati)

def rec_get_next_concepts(rooti):              # returns the id list of all next concepts (starting from rooti, inclusive)
    next_concepts = [rooti]
    for i in gl.WM.cp[rooti].next:
        next_concepts.extend(rec_get_next_concepts(i))
    return next_concepts
        
def rec_get_leaves(rooti):                     # returns the id list of leaf concepts (starting from rooti, inclusive)
    leaf_concepts = []
    if gl.WM.cp[rooti].is_leaf():
        leaf_concepts.append(rooti)
    else:
        for i in gl.WM.cp[rooti].next:
            leaf_concepts.extend(rec_get_leaves(i))
    return leaf_concepts
    
def rec_print_tree(rooti, printchildren = False, level = 0):          # prints the tree recursively (starting from rooti, inclusive) 
    print("." * (level * 3) + str(rooti) + 
        ((" (children: " + str(gl.WM.cp[rooti].child) + ")") if printchildren and len(gl.WM.cp[rooti].child)>0 else ""));
    for i in gl.WM.cp[rooti].next:
        rec_print_tree(i, printchildren, level + 1)
        
def remove_branch(branchi):
    # removes branch starting from branchi
    # doesn't really remove concepts, only terminates connection in the tree
    # removes ids of next concepts from the child list of previous concepts
    if gl.WM.cp[branchi].previous != -1:
        gl.WM.cp[gl.WM.cp[branchi].previous].next.remove(branchi)
        
        next_concepts_list = rec_get_next_concepts(branchi)
        i = gl.WM.cp[branchi].previous
        while i != -1:
            children_list = gl.WM.cp[i].child[:]
            for childi in children_list:
                if childi in next_concepts_list:
                    gl.WM.cp[i].child.remove(childi)
            i = gl.WM.cp[i].previous

def get_previous_sentence_on_branch(beforei):       # finds the previous full sentence concept on the branch (before the given id)
    i = gl.WM.cp[beforei].previous                  # the previous sentence concept's id must be before the given id
    while i != -1:
        if len(gl.WM.cp[i].child) == 0:             # a concept is a full sentence concept, if it doesn't have children
            return i
        i = gl.WM.cp[i].previous
    return -1                                       # return -1 if no previous sentence concept available
                
                
if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
