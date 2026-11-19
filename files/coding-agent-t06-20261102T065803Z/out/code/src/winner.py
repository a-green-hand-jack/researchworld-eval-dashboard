"""Bounds for ANY original-leader loss, considering every other participant."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import json,time
import numpy as np
import pandas as pd
from bt import BT
from data import load_panels,ROOT


def main():
    start=time.time();details=[];summaries=[];witnesses={}
    for p in load_panels():
        b=BT(p);t=b.fit();rank=np.argsort(-t[:p.m]);leader=int(rank[0])
        best=p.n+1;bestattack=None;bestchallenger=None;lows=[]
        for rival in rank[1:]:
            c=b.contrast(leader,rival);bound=b.direct_bound(t,c)
            lows.append(bound['lower_k'])
            # No heuristic can improve the current feasible best if even the
            # relaxed optimal transfer needs more than that many flips.
            if bound['lower_k']<=best:
                a=b.attack(t,c,cap=min(best,p.n))
                if a['k'] is not None and a['k']<best:
                    best=a['k'];bestattack=a;bestchallenger=int(rival)
                upper=a['k']
            else:upper=None
            details.append(dict(panel=p.name,rival=p.models[rival],lower_k=bound['lower_k'],
                upper_k=upper,direct_capacity=bound['capacity']))
        assert bestattack is not None
        summary=dict(panel=p.name,lower_k=min(lows),upper_k=best,
            exact=bool(min(lows)==best),rival=p.models[bestchallenger],
            global_pct=100*best/p.n,leader_pct=100*best/np.sum((p.a==leader)|(p.b==leader)),
            fits=b.fit_count)
        summaries.append(summary);witnesses[p.name]=bestattack
        print(summary,flush=True)
    pd.DataFrame(summaries).to_csv(ROOT/'results/winner.csv',index=False)
    pd.DataFrame(details).to_csv(ROOT/'results/winner_rivals.csv',index=False)
    (ROOT/'results/winner_paths.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    (ROOT/'results/winner_run.json').write_text(json.dumps(dict(seconds=time.time()-start),indent=2)+'\n')


if __name__=='__main__':main()
