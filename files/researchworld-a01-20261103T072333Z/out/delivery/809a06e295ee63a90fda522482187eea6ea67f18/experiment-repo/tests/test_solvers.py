"""Cross-check analytic/MILP optima against independent exhaustive evaluation."""
import sys,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from scipy.stats import rankdata
from analysis import solve,context,RULES

def evaluate(X,t,u,rule,z,strict):
    Y=X.copy();Y[t]=np.where(z,u,Y[t])
    if rule=='borda':scores=(rankdata(Y,axis=0,method='average')-1).sum(axis=1)
    elif rule=='mean':scores=Y.mean(axis=1)
    elif rule=='median':scores=np.median(Y,axis=1)
    elif rule=='minimum':scores=Y.min(axis=1)
    else:scores=Y.prod(axis=1)**(1/Y.shape[1])
    return scores[t]>=np.max(np.delete(scores,t))+(1e-10 if strict else -1e-10)

def main():
    rng=np.random.default_rng(47);cases=0
    P=np.array(list(itertools.product([False,True],repeat=11)))
    for repeat in range(6):
        X=rng.integers(0,11,size=(7,11))/10
        for alpha in [1.,.4]:
            t=repeat%7;u=X[t]+alpha*(1-X[t])
            for rule in RULES:
                for strict in [False,True]:
                    success=np.array([evaluate(X,t,u,rule,z,strict) for z in P])
                    expected=None if not success.any() else int(P[success].sum(axis=1).min())
                    z,status,detail=solve(X,t,u,rule,context(X,rule),strict)
                    actual=None if z is None else int(z.sum())
                    assert actual==expected,(repeat,alpha,rule,strict,actual,expected,status,detail)
                    cases+=1
    print(f'Passed {cases} analytic/MILP comparisons against independent exhaustive enumeration',flush=True)
if __name__=='__main__':main()
