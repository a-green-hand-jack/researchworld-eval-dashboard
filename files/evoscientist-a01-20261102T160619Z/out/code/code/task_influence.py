#!/usr/bin/env python3
"""Bounded task-influence diagnostic; freeze protocol before examining outputs."""
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from optimize import solve,scores,subsets
ROOT=Path(__file__).resolve().parents[1]

def main():
    protocol={'selection':'12 equally spaced order statistics of baseline mean rank, ascending mean then stable row order; all competitors retained','rhos':[.5,1.],'rules':['mean','median','borda'],'strict':False,'note':'Open deletes each task; HELM deletes six preselected pairs of alphabetically ordered subjects to preserve odd median. Planned HELM leave-one-out not run: n=56 conventional median unsupported by analytic solver. Diagnostic only, not random sampling or statistical uncertainty.','panels':{}}
    frames={}
    for name in ['helm','open_raw']:
        df=pd.read_csv(ROOT/f'data/processed/{name}.csv',index_col=0);frames[name]=df;a=df.to_numpy();order=np.argsort(a.mean(axis=1),kind='stable');ids=order[np.linspace(0,len(a)-1,12,dtype=int)]
        drops=[[i] for i in range(6)] if name=='open_raw' else [[i,i+1] for i in [0,9,18,27,36,45]]
        protocol['panels'][name]={'target_indices':ids.tolist(),'targets':df.index[ids].tolist(),'drop_indices':drops,'drop_tasks':[[df.columns[i] for i in ds] for ds in drops]}
    (ROOT/'artifacts/task_influence_protocol.json').write_text(json.dumps(protocol,indent=2))
    out=[];start=time.perf_counter()
    for name,df in frames.items():
      a=df.to_numpy();p=protocol['panels'][name]
      for ix,drop in enumerate(p['drop_indices']):
        b=np.delete(a,drop,axis=1);allsets=subsets(b.shape[1]) if b.shape[1]<10 else None
        for rule in protocol['rules']:
          baseline=scores(b,rule)
          for rho in protocol['rhos']:
            for i in p['target_indices']:
              v=solve(b,i,rho,rule,False,baseline,allsets);out.append(dict(dataset=name,panel=ix,drop_tasks=';'.join(df.columns[drop]),i=i,model=df.index[i],n=b.shape[1],rho=rho,rule=rule,K=v['K'],K_fraction=None if v['K'] is None else v['K']/b.shape[1],initial_winner=bool(baseline[i]>=baseline.max()-1e-12),status=v['status']))
    pd.DataFrame(out).to_csv(ROOT/'artifacts/task_influence_results.csv',index=False)
    summary=[]
    for (name,rho,panel),g in pd.DataFrame(out).groupby(['dataset','rho','panel']):
        p=g.pivot(index='i',columns='rule',values='K_fraction');w=g.pivot(index='i',columns='rule',values='initial_winner');ids=p.dropna().index.intersection(w[~w.any(axis=1)].index)
        summary.append(dict(dataset=name,rho=rho,panel=panel,common_nonwinners=len(ids),median_minus_mean=float((p.loc[ids,'median']-p.loc[ids,'mean']).mean()),**{r+'_feasible':int(p[r].notna().sum()) for r in protocol['rules']}))
    pd.DataFrame(summary).to_csv(ROOT/'artifacts/task_influence_summary.csv',index=False);print('task-influence rows',len(out),'elapsed_s',time.perf_counter()-start)
if __name__=='__main__':main()
