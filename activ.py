import gl
from timeit import default_timer as timer

class Activate:
    def __init__(self):
        self.allwmactive=1                      # 1 means we activate the entire WM

    def activate_Conc(self,conc,leaflist):      # activate a single concept on several leafs
        for leaf in leaflist:
            gl.WM.branchactiv[leaf].add(conc)   # add conc to the set of activated concepts per branch

    def get_Thisactiv(self,wmpos):              # collect all activated concepts from relevant branches
        thisact=set()
        for leaf in gl.WM.brelevant:            # brelevant has leafs where wmpos occurs
            thisact.update(set(gl.WM.branchactiv[leaf]))  # add the activated elemets of this branch
        return thisact

    def update_Para(self):                      # update paragraph information when new paragraph starts
        if len(gl.WM.thispara)>0:               # nonempty
            gl.WM.prevpara[:]=[]                # make list of previous paragraph empty
            for con in gl.WM.thispara:          # current paragraph
                gl.WM.thispara.remove(con)      # remove from current paragraph
                gl.WM.prevpara.append(con)      # append to previous paragraph list