#!/usr/bin/env python3
"""Independent witness, bound, monotonicity, pairwise-score and tolerance audit."""
from pathlib import Path
import json,glob,time
import numpy as np
import pandas as pd
import optimize
ROOT=Path(__file__).resolve().parents[1]

def independent_borda(a):
    out=np.zeros(len(a),dtype=int)
    for col in a.T:
        s=np.sort(col);left=np.searchsorted(s,col,'left');right=np.searchsorted(s,col,'right');out+=left+right-1
    return out

def main():
    start=time.perf_counter();total=0;bounds=0;near=[];data={};checks={};sensitivity=[]
    for p in sorted((ROOT/'artifacts').glob('results_*.csv')):
        name=p.stem[8:];source='open_raw' if name in ['open_dedup','open_available','open_median_convention'] else name
        df=pd.read_csv(ROOT/f'data/processed/{source}.csv',index_col=0)
        if name=='open_dedup':df=df.drop_duplicates()
        if name=='open_available':
            meta=pd.read_csv(ROOT/'data/processed/open_metadata.csv').set_index('row_id');df=df.loc[meta.loc[df.index,'Available on the hub'].astype(bool)&~meta.loc[df.index,'Flagged'].astype(bool)]
        a=df.to_numpy();base=independent_borda(a);assert np.array_equal(base,optimize.scores(a,'borda'))
        rows=pd.read_csv(p);byrule={};count=0
        for r in rows.itertuples():
            i=r.i;x=a[i];c=x+r.rho*(1-x);z=np.zeros(a.shape[1],dtype=bool)
            if pd.notna(r.mask):z[[int(t) for t in str(r.mask).split(';')]]=True
            if pd.notna(r.K):assert int(z.sum())==int(r.K) and np.all(c[z]>x[z])
            # Infeasibility must hold even with every permitted coordinate at ceiling.
            y=np.where(z,c,x) if pd.notna(r.K) else c
            if r.rule=='borda':
                other=np.delete(a,i,axis=0);own=int(np.sum(2*(other<y)+(other==y)))
                # Independent expression: a rival's doubled pair points are 1+sign(rival-target).
                loss=np.sum(np.sign(other-x)-np.sign(other-y),axis=1).astype(int)
                rival=np.delete(base,i)-loss;margin=own-int(rival.max());good=margin>=int(r.strict)
                if r.dataset=='helm' and pd.notna(r.K) and r.K>0:
                    assert r.gap==0 and abs(r.dual-r.K)<1e-7;bounds+=1
            else:
                if r.rule=='mean':f=lambda aa:np.mean(aa,axis=-1)
                elif r.rule=='median':f=lambda aa:np.median(aa,axis=-1)
                elif r.rule=='lower_median':f=lambda aa:np.sort(aa,axis=-1)[...,(a.shape[1]-1)//2]
                else:f=lambda aa:np.sort(aa,axis=-1)[...,a.shape[1]//2]
                rival=np.delete(f(a),i);margin=float(f(y)-rival.max());good=margin>1e-12 if r.strict else margin>=-1e-12
                if abs(margin)<1e-9:near.append(dict(dataset=name,i=i,rho=r.rho,strict=r.strict,rule=r.rule,K=None if pd.isna(r.K) else r.K,margin=margin))
            assert good==pd.notna(r.K),(name,i,r.rho,r.rule,r.strict,margin,r.K)
            if pd.notna(r.K):assert abs(r.witness_L1-np.mean(y-x))<1e-14
            assert r.status in ['optimal','infeasible'];count+=1
        # Monotonicity with infinity treated only internally, never as a reported finite cost.
        for _,g in rows.groupby(['i','rule','strict']):
            ks=g.sort_values('rho').K.fillna(np.inf).to_numpy();assert np.all(np.diff(ks[np.isfinite(ks)])<=0)
            feasible=g.sort_values('rho').K.notna().to_numpy();assert np.all(np.diff(feasible.astype(int))>=0)
        if rows.strict.nunique()==2:
            w=rows.pivot(index=['i','rule','rho'],columns='strict',values='K').fillna(np.inf);assert np.all(w[True]>=w[False])
        checks[name]={'rows':count,'near_boundary_rows':sum(q['dataset']==name for q in near)};total+=count
        # Full primary cardinal support rerun at zero and larger tolerance, not only returned margins.
        if name in ['helm','open_raw']:
          for tol in [0.,1e-10]:
            optimize.TOL=tol;changed=0
            for rho in [.25,.5,1.]:
             for rule in ['mean','median']:
              b=optimize.scores(a,rule)
              for strict in [False,True]:
               original=rows[(rows.rho==rho)&(rows.rule==rule)&(rows.strict==strict)].set_index('i')
               masks=optimize.subsets(a.shape[1]) if a.shape[1]<=10 else None
               for i in range(len(a)):
                out=optimize.solve(a,i,rho,rule,strict,b,masks);old=original.at[i,'K'];changed+= int((out['K'] is None)!=pd.isna(old) or (out['K'] is not None and out['K']!=old))
            sensitivity.append(dict(dataset=name,tolerance=tol,changed_K=changed))
          optimize.TOL=1e-12
    pd.DataFrame(near).to_csv(ROOT/'artifacts/boundary_cases.csv',index=False)
    out={'total_rows_checked':total,'checks':checks,'helm_borda_nonzero_optima_with_zero_gap_and_matching_bound':bounds,'tolerance_sensitivity':sensitivity,'all_checks_passed':True,'elapsed_s':time.perf_counter()-start,'note':'Numerical MILP lower bounds are not formal rational-arithmetic certificates.'}
    (ROOT/'artifacts/validation_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
