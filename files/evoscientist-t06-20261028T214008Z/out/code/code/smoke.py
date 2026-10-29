import time, numpy as np
from lbrobust import data as D
from lbrobust.bt import fit_bt
from lbrobust.perturb import Searcher
import os; os.environ['LB_RAW']='../data/raw'
D.RAW='../data/raw'
for nm in ['arena140k']:
    t=time.time(); d=D.load(nm); tl=time.time()-t
    t=time.time(); S=Searcher(d); f=S.fit0; tf=time.time()-t
    r=f.ranking(d.K)
    print(nm, 'N',d.N,'K',d.K,'T',len(d.n),'load %.1fs fit %.3fs conv %s it %d'%(tl,tf,f.converged,f.iters))
    print('  top5', [(d.names[k], round(f.theta[k],3)) for k in r[:5]])
    hi,lo=r[0],r[1]
    print('  lev', {k:round(v,4) for k,v in S.leverage(hi,lo).items()})
    for fam in ['drop','flip','add']:
        t=time.time(); g=S.greedy(hi,lo,fam); a=S.amip(hi,lo,fam)
        print('  ',fam,'greedy',g['cost'],g['success'],g['refits'],'amip',a['pred'],a['cost'],a['refits'],'%.2fs'%(time.time()-t))
