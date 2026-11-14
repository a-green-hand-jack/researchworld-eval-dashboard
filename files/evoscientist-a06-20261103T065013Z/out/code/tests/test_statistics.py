"""Exhaustive and analytic correctness checks; no expensive endpoint calls."""
import itertools,json,pathlib,sys
import numpy as np
from scipy.stats import hypergeom,binom
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'code'))
from statistics import hg_table,cp_table,wilson,multiplier_radius,evaluate
from collect import parse_answer
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    tests={};worst=1.
    for M in range(2,19):
      for m in range(1,M+1):
       tab=hg_table(M,m)
       for T in range(M+1):
        x=np.arange(m+1);q=T/M
        coverage=np.sum(hypergeom.pmf(x,M,T,m)*((tab[:,0]<=q+1e-12)&(tab[:,1]>=q-1e-12)))
        worst=min(worst,coverage)
    assert worst>=.95-1e-12;tests['minimum_exhaustive_hypergeometric_coverage']=worst
    worstcp=1.
    for n in [1,2,8,16,32,128]:
      for p in np.linspace(0,1,201):
       t=cp_table(n);x=np.arange(n+1);cov=np.sum(binom.pmf(x,n,p)*((t[:,0]<=p)&(t[:,1]>=p)));worstcp=min(worstcp,cov)
    assert worstcp>=.95-1e-12;tests['minimum_CP_grid_coverage']=worstcp
    # Enumerate full selection->audit pipeline for a fixed small response table.
    Y=np.array([[1,0],[0,1],[1,1],[0,0],[1,0],[0,1],[1,1],[0,0]],dtype=float);N=len(Y);n=2;m=3;cnt=0;covered=0;paired=0
    for sel in itertools.combinations(range(N),n):
      rem=[i for i in range(N) if i not in sel];means=Y[list(sel)].mean(0);j=np.argmax(means);s=means[j]
      for a in itertools.combinations(rem,m):
        t=hg_table(N-n,m)[int(Y[list(a),j].sum())];ci=n/N*s+(N-n)/N*t;mu=Y[:,j].mean();covered+=ci[0]-1e-12<=mu<=ci[1]+1e-12
        plus=int(((Y[list(a),j]==1)&(Y[list(a),0]==0)).sum());minus=int(((Y[list(a),j]==0)&(Y[list(a),0]==1)).sum());t=hg_table(N-n,m,.025)
        dlo=n/N*(means[j]-means[0])+(N-n)/N*(t[plus,0]-t[minus,1]);dhi=n/N*(means[j]-means[0])+(N-n)/N*(t[plus,1]-t[minus,0]);delta=Y[:,j].mean()-Y[:,0].mean();paired+=dlo-1e-12<=delta<=dhi+1e-12;cnt+=1
    assert covered/cnt>=.95 and paired/cnt>=.95;tests['enumerated_selection_audit_cases']=cnt;tests['full_pipeline_coverage']=covered/cnt;tests['paired_pipeline_coverage']=paired/cnt
    rng=np.random.default_rng(11);S=rng.binomial(1,.7,(100,64,1));A=rng.binomial(1,.7,(100,128,1));r,_=evaluate(np.repeat(S,8,axis=2),np.repeat(A,8,axis=2),np.full(8,.7),np.random.default_rng(12),B=999)
    assert np.all(r['winner']==0);assert np.all(r['pair_width']==0);tests['duplicate_tie_and_self_comparison']='passed'
    for text,expected in [('ANSWER: A','A'),('Reason.\nANSWER: B','B'),('B',None),('ANSWER: A\nANSWER: B',None),('ANSWER: J',None),('ANSWER: A blah',None)]:assert parse_answer(text,['a','b'])==expected
    tests['parser_fixtures']='passed'
    # Gaussian covariance and explicit row multiplier distributions should match.
    X=rng.binomial(1,.6,(32,4));Xc=X-X.mean(0)
    explicit=np.max(np.abs(rng.normal(size=(100000,32))@Xc/np.sqrt(32*31)),axis=1)
    rad=multiplier_radius(X[None,:,:],np.random.default_rng(9),B=100000)[0];diff=abs(rad-np.quantile(explicit,.95));assert diff<.003;tests['multiplier_equivalence_quantile_difference']=float(diff)
    (ROOT/'artifacts/tests.json').write_text(json.dumps(tests,indent=2));print(json.dumps(tests,indent=2))
if __name__=='__main__':main()
