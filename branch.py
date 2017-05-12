import gl, copy

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
    if rooti == -1:
        return []
    next_concepts = [rooti]
    for i in gl.WM.cp[rooti].next:
        next_concepts.extend(rec_get_next_concepts(i))
    return next_concepts
        
def rec_get_leaves(rooti):                     # returns the id list of leaf concepts (starting from rooti, inclusive)
    if rooti > gl.WM.ci or rooti == -1:
        return []
    leaf_concepts = []
    if gl.WM.cp[rooti].is_leaf():
        leaf_concepts.append(rooti)
    else:
        if -1 in gl.WM.cp[rooti].next:
            leaf_concepts.append(rooti)
        for i in gl.WM.cp[rooti].next:
            leaf_concepts.extend(rec_get_leaves(i))
    return leaf_concepts
    
def rec_print_tree(rooti, print_details = False, level = 0):          # prints the tree recursively (starting from rooti, inclusive) 
    if rooti == -1: return
    text = "." * (level * 3) + str(rooti)
    if print_details:
        text += " " + gl.WM.cp[rooti].mentstr
        if len(gl.WM.cp[rooti].child) > 0:
            text += " (children: " + str(gl.WM.cp[rooti].child) + ")"
        if len(gl.WM.cp[rooti].parent) > 0:
            text += " (parents: " + str(gl.WM.cp[rooti].parent) + ")"
    print(text)
    for i in gl.WM.cp[rooti].next:
        rec_print_tree(i, print_details, level + 1)
        
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
                
def search_concept_on_branch(what, branchi):
    found = []
    possibleids = []
    possibleids.extend(get_previous_concepts(branchi)[::-1])
    possibleids.extend(rec_get_next_concepts(branchi)[1:])
    
    for conitemi in possibleids:
        if gl.WM.rec_match(what, gl.WM.cp[conitemi]) == 1:
            found.append(conitemi)  # add to found list
            
    return found
    
def add_concept_to_all_branches(original_concept):
    added_concepts = []
    leaves = rec_get_leaves(0)
    if len(leaves) == 0:
        added_concepts.append(gl.WM.add_concept_to_cp(original_concept))
    else:
        for leafi in leaves:
            concept = copy.deepcopy(original_concept)
            concept.previous = leafi
            concept.parent[:] = [x for x in concept.parent if search_previously(x, leafi)]
            added_i = gl.WM.add_concept_to_cp(concept)
            added_concepts.append(added_i)
            gl.WM.cp[leafi].next.append(added_i)
            if -1 in gl.WM.cp[leafi].next:
                gl.WM.cp[leafi].next.remove(-1)
    return added_concepts
    
                
if __name__ == "__main__":
    print("This is a module file, run natlan.py instead")
