#!/usr/bin/env python3
"""Run frozen primary and sensitivity analyses; checkpoint each matrix."""
from pathlib import Path
import argparse,json,time,sys,os
import numpy as np
import pandas as pd
from optimize import scores,solve,subsets,borda_problem,heuristic
ROOT=Path(__file__).resolve().parents[1]
SEEDS=[17,29,43]

def run_frame(name,a,ids,rhos,conventions,rules):
    n=a.shape[1];allsets=subsets(n) if n<=10 else None;results=[];t0=time.perf_counter()
    baselines={rule:scores(a,rule) for rule in rules}
    ranks={rule:np.sum(b[None,:]>b[:,None]+(0 if rule=='borda' else 1e-12),axis=1)+1 for rule,b in baselines.items()}
    for rho in rhos:
      for strict in conventions:
       for rule in rules:
        start=time.perf_counter();base=baselines[rule]
        for i in range(len(a)):
            out=solve(a,i,rho,rule,strict,base,allsets)
            z=out.pop('mask');k=out['K'];d=rho*(1-a[i]);out.update(dataset=name,i=i,model=ids[i],rho=rho,strict=strict,rule=rule,n=n,m=len(a),rank=int(ranks[rule][i]),base_score=float(base[i]),K_fraction=k/n if k is not None else None,witness_L1=float(z@d/n) if k is not None else None,mask=';'.join(map(str,np.flatnonzero(z))))
            if rule=='borda':
                _,G,rhs,_=borda_problem(a,i,rho,base);rhs+=int(strict)
                out['headroom_K']=heuristic(G,rhs,np.argsort(-d,kind='stable'))
                for seed in SEEDS:
                    rng=np.random.default_rng(seed+1000*i)
                    out[f'random_K_{seed}']=heuristic(G,rhs,rng.permutation(n))
            results.append(out)
        print(name,rho,strict,rule,'seconds',round(time.perf_counter()-start,3),flush=True)
    frame=pd.DataFrame(results);frame.to_csv(ROOT/f'artifacts/results_{name}.csv',index=False,float_format='%.17g')
    return {'dataset':name,'models':len(a),'tasks':n,'rows':len(frame),'elapsed_s':time.perf_counter()-t0,'status_counts':frame.status.value_counts().to_dict()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--only',default='all');args=p.parse_args();logs=[];cpu=time.process_time();wall=time.perf_counter()
    for name in ['helm','open_raw','open_norm','open_dedup','open_available']:
        if args.only!='all' and name!=args.only:continue
        source='open_raw' if name in ['open_dedup','open_available'] else name
        df=pd.read_csv(ROOT/f'data/processed/{source}.csv',index_col=0)
        if name=='open_dedup':df=df.drop_duplicates()
        if name=='open_available':
            meta=pd.read_csv(ROOT/'data/processed/open_metadata.csv').set_index('row_id');df=df.loc[meta.loc[df.index,'Available on the hub'].astype(bool)&~meta.loc[df.index,'Flagged'].astype(bool)]
        if args.pilot:
            # Pilot preserves all competitors, limits targets through a separate quick direct path.
            a=df.to_numpy();b=scores(a,'borda');selected=np.argsort(b)[np.linspace(0,len(a)-1,12,dtype=int)];t=time.perf_counter()
            details=[]
            for i in selected:
                r=solve(a,i,.5,'borda',False,b);details.append({k:v for k,v in r.items() if k!='mask'})
            print(name,'pilot',time.perf_counter()-t,details);continue
        logs.append(run_frame(name,df.to_numpy(),df.index.tolist(),[.25,.5,1.] if name in ['helm','open_raw'] else [.5],[False,True] if name in ['helm','open_raw'] else [False],['mean','median','borda']))
        if name=='open_raw':logs.append(run_frame('open_median_convention',df.to_numpy(),df.index.tolist(),[.5],[False],['lower_median','upper_median']))
    if not args.pilot:
        (ROOT/f'artifacts/timing_{args.only}.json').write_text(json.dumps({'runs':logs,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'seeds':SEEDS,'blas_threads':os.environ.get('OPENBLAS_NUM_THREADS')},indent=2))
if __name__=='__main__':main()
