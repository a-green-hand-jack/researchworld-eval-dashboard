"""Composition sensitivity: bootstrap HELM subjects; delete each Open LLM task."""
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from analysis import ROOT,RULES,context,solve

def measure(X,dataset,kind,rep,description):
    rows=[];costs={}
    for rule in RULES:
        base=context(X,rule);ks=[]
        for t in range(len(X)):
            z,status,_=solve(X,t,np.ones(X.shape[1]),rule,base)
            assert status not in ['solver_failure','bounded'],status
            ks.append(np.nan if z is None else z.sum())
        a=np.asarray(ks);costs[rule]=a
        rows.append(dict(dataset=dataset,kind=kind,rep=rep,description=description,rule=rule,n_targets=len(X),n_tasks=X.shape[1],reachable=int(np.isfinite(a).sum()),median_k=float(np.nanmedian(a)),mean_k=float(np.nanmean(a)),fraction_at_10pct=float(np.mean(a<=.1*X.shape[1])),fraction_at_25pct=float(np.mean(a<=.25*X.shape[1])),fraction_at_50pct=float(np.mean(a<=.5*X.shape[1]))))
    paired=[]
    for i,a in enumerate(RULES):
        for b in RULES[i+1:]:
            d=costs[a]-costs[b]
            paired.append(dict(dataset=dataset,kind=kind,rep=rep,description=description,rule_a=a,rule_b=b,median_difference=float(np.nanmedian(d)),a_lower=int((d<0).sum()),a_higher=int((d>0).sum()),same=int((d==0).sum())))
    return rows,paired

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',required=True);ap.add_argument('--reps',type=int,default=200);a=ap.parse_args()
    frame=pd.read_csv(ROOT/f'data/processed/{a.dataset}.csv',index_col=0);X=frame.to_numpy();rng=np.random.default_rng(20261103)
    rows=[];pairs=[];start=time.perf_counter()
    if a.dataset=='helm':
        designs=[('task_bootstrap',r,rng.integers(0,X.shape[1],size=X.shape[1]),'57 tasks sampled with replacement') for r in range(a.reps)]
    else:
        designs=[('leave_one_task_out',r,np.delete(np.arange(X.shape[1]),r),str(frame.columns[r])) for r in range(X.shape[1])]
    for kind,rep,indices,description in designs:
        r,p=measure(X[:,indices],a.dataset,kind,rep,description);rows.extend(r);pairs.extend(p)
        if (rep+1)%10==0:print(f'{a.dataset} robustness {rep+1}/{len(designs)}',flush=True)
    pd.DataFrame(rows).to_csv(ROOT/f'results/composition_{a.dataset}.csv',index=False)
    pd.DataFrame(pairs).to_csv(ROOT/f'results/composition_pairs_{a.dataset}.csv',index=False)
    print(f'HUTIAN_WAKE: {a.dataset} composition completed {len(designs)} designs in {time.perf_counter()-start:.2f}s',flush=True)
if __name__=='__main__':main()
