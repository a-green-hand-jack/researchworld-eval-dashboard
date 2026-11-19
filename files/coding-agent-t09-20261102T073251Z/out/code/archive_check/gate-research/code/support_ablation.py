"""Exploratory follow-up: remove low-degree outcome observations, keep graph fixed."""
import time,json
import numpy as np,pandas as pd
from study import ROOT,SEED,load_graphs,setup_graph,weights

start=time.time();g=load_graphs()['Facebook']
P,deg,groups,x,_=setup_graph(g,'Facebook',5);n=len(g)
rng=np.random.default_rng(np.random.SeedSequence([SEED,5,0,0,0]));out=[]
for r in range(400):
    z=rng.binomial(1,.5,n).astype(float);s=P@z;t=P@s
    eps=.5*rng.normal(size=n);rng.normal(size=groups.max()+1)
    y=1+.5*x+z+2*s**3+eps
    control_rng=np.random.default_rng(np.random.SeedSequence([SEED,777,r]))
    control_order=control_rng.permutation(n)
    for cutoff in [1,5,10,20,50,100]:
        keep=deg>=cutoff;nk=int(keep.sum())
        control=np.zeros(n,dtype=bool);control[control_order[:nk]]=True
        for selection,mask in [('degree',keep),('random',control)]:
            ans=weights(z[mask],s[mask],t[mask],x[mask],'OLS-C')
            if ans is None:
                out.append(dict(rep=r,cutoff=cutoff,selection=selection,n_kept=nk,valid=False));continue
            w,_,_,_=ans
            out.append(dict(rep=r,cutoff=cutoff,selection=selection,n_kept=nk,valid=True,
                            error=float(w@y[mask]-3),noise_var=.25*float(w@w)))
pd.DataFrame(out).to_csv(ROOT/'results/support_raw.csv.gz',index=False)
(ROOT/'results/support_run.json').write_text(json.dumps(dict(reps=400,seconds=time.time()-start),indent=2))
print('support ablation seconds',time.time()-start)
