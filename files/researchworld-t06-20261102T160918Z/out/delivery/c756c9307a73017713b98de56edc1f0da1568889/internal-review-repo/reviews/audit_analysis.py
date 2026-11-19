"""Independent numerical checks of the analysis revision; raw inputs stay untracked.
Run with OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 reviews/audit_analysis.py.
Requires fetched inputs under /hutian/review-work, audited source /hutian/experiment-repo.
"""
import sys,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
sys.path.insert(0,'/hutian/review-work/scripts')
from datasets import primary,matched_mt
from bt import fit,influence
from run_study import refit
SRC=Path('/hutian/experiment-repo'); OUT=Path('/hutian/repo/reviews')
expected=json.loads((SRC/'results/provenance.json').read_text())
actual=json.loads(Path('/hutian/review-work/results/provenance.json').read_text())
assert [(x['sha256'],x['bytes']) for x in expected]==[(x['sha256'],x['bytes']) for x in actual]

def independent(a,b,y,m):
    # Independent explicit design-matrix likelihood and SciPy trust-region optimizer.
    pairs,rev=np.unique(np.column_stack((a,b)),axis=0,return_inverse=True)
    n=np.bincount(rev); s=np.bincount(rev,weights=y)
    X=np.zeros((len(pairs),m)); X[np.arange(len(pairs)),pairs[:,0]]=1;X[np.arange(len(pairs)),pairs[:,1]]=-1
    def fun(v):
        z=X@v
        return float(np.sum(n*np.logaddexp(0,z)-s*z)+v@v/2)
    def jac(v):return X.T@(n*expit(X@v)-s)+v
    def hes(v):
        p=expit(X@v)
        return X.T@((n*p*(1-p))[:,None]*X)+np.eye(m)
    opt=minimize(fun,np.zeros(m),jac=jac,hess=hes,method='trust-exact',options={'gtol':1e-9,'maxiter':100})
    # Trust-region termination can hit objective rounding at summed-loss scale.
    # Independently refine its stationary point using this explicit Hessian.
    v=opt.x.copy()
    for _ in range(3):v-=np.linalg.solve(hes(v),jac(v))
    opt.x=v
    assert np.max(np.abs(jac(opt.x)))<1e-6
    return opt.x,hes(opt.x),float(np.max(np.abs(jac(opt.x))))
rows=[]
for d in primary():
    a,b,y,names=d.arrays(); m=len(names)
    saved=json.loads((SRC/'results/primary'/d.name/'audit.json').read_text())
    t,H,grad=independent(a,b,y,m)
    st=pd.read_csv(SRC/'results/primary'/d.name/'scores.csv').theta.to_numpy()
    err=float(np.max(np.abs(t-st)));assert err<1e-7,(d.name,err)
    assert len(y)==saved['N'] and m==saved['m'] and sum(y==.5)==saved['ties']
    pair=[names.index(saved[k]) for k in ['leader','runner']]
    w=pd.read_csv(SRC/'results/witnesses'/f'{d.name}.csv'); ix=w.processed_row_index.to_numpy()
    assert len(set(ix))==saved['attack_k'] and np.all(y[ix]!=.5)
    assert d.frame.iloc[ix].a.tolist()==w.a.tolist() and d.frame.iloc[ix].b.tolist()==w.b.tolist()
    assert np.array_equal(y[ix],w.y) and np.array_equal(1-y[ix],w.new_y)
    z=y.copy();z[ix]=1-z[ix]; u,_,g2=independent(a,b,z,m)
    margin=float(u[pair[0]]-u[pair[1]]);assert margin<-1e-10 and abs(margin-saved['attack_margin_at_k'])<1e-7
    c=np.zeros(m);c[pair[0]]=1;c[pair[1]]=-1;v=np.linalg.solve(H,c)
    gain=-(1-2*y)*(v[a]-v[b]); assert np.max(abs(gain[ix]-w.influence_margin_reduction))<1e-8
    boot=pd.read_csv(SRC/'results/primary'/d.name/'bootstrap.csv');q=boot.margin.quantile([.025,.975]).to_numpy()
    unc=pd.read_csv(SRC/'results/summary/primary/uncertainty.csv').set_index('dataset').loc[d.name]
    assert np.allclose(q,[unc.gap_low,unc.gap_high],atol=1e-12)
    assert len(boot)==500 and boot.pair_reversed.mean()==unc.fixed_pair_reversal_rate
    rows.append(dict(dataset=d.name,N=len(y),score_max_difference=err,independent_gradient=grad,attack_k=len(ix),independent_attack_margin=margin,attack_gradient=g2))
    print('PASS original fit, raw count, witness, influence sign and bootstrap summary',d.name,flush=True)
pd.DataFrame(rows).to_csv(OUT/'independent_primary_checks.csv',index=False)
fixed=pd.read_csv(SRC/'results/summary/matched_fixedpair/replicates.csv')
checks=[]
for rep in [0,2,75,76,153,162,178,337,499]:
    h,j=matched_mt(20261102+rep); groups=h.frame.cluster.unique()
    assert len(h.frame)==1814 and h.frame[['cluster','a','b','turn']].equals(j.frame[['cluster','a','b','turn']])
    draw=np.random.default_rng(20261102+100000+rep).choice(groups,len(groups),replace=True)
    for d in [h,j]:
        d.frame=pd.concat([d.frame[d.frame.cluster==g] for g in draw],ignore_index=True)
        a,b,y,names=d.arrays(); t,_=fit(a,b,y,len(names));pair=(names.index('gpt-4'),names.index('claude-v1'))
        gap=float(t[pair[0]]-t[pair[1]])
        saved=fixed[(fixed.rep==rep)&(fixed.dataset==d.name)].iloc[0]
        assert len(y)==saved.N and abs(gap-saved.gap)<1e-8
        k=int(saved.attack_k)
        if gap<0:assert k==0
        else:
            ix,_,_=influence(a,b,y,t,pair=pair)
            u=refit(a,b,y,t,ix[:k],1.)
            assert u[pair[0]]-u[pair[1]]<-1e-10
            v=refit(a,b,y,t,ix[:k-1],1.)
            assert v[pair[0]]-v[pair[1]]>=-1e-10
        checks.append(dict(rep=rep,dataset=d.name,N=len(y),gap=gap,verified_attack_k=k))
    print('PASS matched schedule, fixed-pair gap and successful-prefix witness',rep,flush=True)
pd.DataFrame(checks).to_csv(OUT/'matched_spot_checks.csv',index=False)
piv=fixed.pivot(index='rep',columns='dataset',values='attack_fraction');diff=piv.matched_human-piv.matched_gpt4
summary=json.loads((SRC/'results/summary/matched_fixedpair/difference.json').read_text())
assert len(diff)==500 and diff.notna().all()
assert abs(diff.mean()-summary['mean_difference'])<1e-12
assert np.allclose(diff.quantile([.025,.975]),[summary['q025'],summary['q975']],atol=1e-12)
assert (diff<0).mean()==summary['human_lower_fraction']
print('PASS all raw hashes and full fixed-pair 500-replicate arithmetic',flush=True)
