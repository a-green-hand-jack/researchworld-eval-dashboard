"""Independent numerical checks for the exact target and feature grouping."""
import itertools, math
import numpy as np
from shap_reliability.estimators import Game,kernel_shap

class PolynomialModel:
    def predict_proba(self,x):
        p=.1+.1*x[:,0]+.2*x[:,1]+.3*x[:,0]*x[:,1]+.1*x[:,2]
        return np.column_stack([1-p,p])

class GroupedModel:
    def predict_proba(self,x):
        p=.1+.2*x[:,0]+.3*x[:,1]+.1*x[:,2]+.1*x[:,1]*x[:,2]
        return np.column_stack([1-p,p])

def brute_permutations(game):
    result=np.zeros(game.d)
    for p in itertools.permutations(range(game.d)):
        code=0; prev=game.values([0])[0]
        for j in p:
            code|=1<<j; new=game.values([code])[0]
            result[j]+=new-prev; prev=new
    return result/math.factorial(game.d)

def test():
    bg=np.zeros((3,3)); x=np.ones(3)
    game=Game(PolynomialModel(),bg,x,[np.array([i]) for i in range(3)],batch_rows=6)
    target=np.array([.25,.35,.1])
    np.testing.assert_allclose(game.exact(),target,atol=1e-12)
    np.testing.assert_allclose(brute_permutations(game),target,atol=1e-12)
    np.testing.assert_allclose(game.permutation(100,19),target,atol=1e-12)
    assert abs(game.exact().sum()-(game.values([7])[0]-game.values([0])[0]))<1e-12
    # Grouping the first two encoded columns into one raw feature must retain
    # their full joint effect, and exact Kernel SHAP must solve the same game.
    grouped=Game(GroupedModel(),np.array([[1,0,0],[0,1,0]]),np.array([0,1,1]),[np.array([0,1]),np.array([2])])
    ref=grouped.exact()
    np.testing.assert_allclose(brute_permutations(grouped),ref,atol=1e-12)
    kg=Game(GroupedModel(),grouped.background,grouped.x,grouped.groups)
    phi,details=kernel_shap(kg,100,18)
    np.testing.assert_allclose(phi,ref,atol=1e-12)
    assert details['exhaustive']
    # Null feature and efficiency on a nondegenerate empirical background.
    bg=np.array([[.2,.5,0],[.7,.1,1]])
    game=Game(PolynomialModel(),bg,np.array([.4,.8,.7]),[np.array([i]) for i in range(3)])
    ref=game.exact(); np.testing.assert_allclose(ref,brute_permutations(game),atol=1e-12)
    for seed in range(3):
        phi=game.permutation(100,seed)
        assert abs(phi.sum()-ref.sum())<1e-12
    print('PASS: analytic interaction, exhaustive permutations, grouping, exact Kernel SHAP, efficiency')
if __name__=='__main__': test()
