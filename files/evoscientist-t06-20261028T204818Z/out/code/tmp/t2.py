import sys,time; sys.path.insert(0,"code"); sys.path.insert(0,"code/tests")
import numpy as np
from test_btlib import synth
import btlib as bt
tt=synth(m=5,N=120,seed=5)
t=time.time()
for _ in range(100): f=bt.fit_bt(tt)
print("fit ms",(time.time()-t)*10, f.n_iter)
r=bt.ranking(f.theta,tt.m)
t=time.time(); res=bt.min_perturbation(tt,r[0],r[1],"drop",fit0=f); print(res["k"], time.time()-t)
t=time.time(); print(bt.exact_min_drop(tt,r[0],r[1],kmax=2,fit0=f), time.time()-t)
