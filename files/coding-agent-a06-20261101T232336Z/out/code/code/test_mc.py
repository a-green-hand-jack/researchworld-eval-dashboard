import sys; sys.path.insert(0,"/work/code")
import numpy as np, time
from synth import *; from mc import *
rng=np.random.default_rng(0)
mu=make_mu(0.15,rng); a=-0.4
acc=acc_from_mu(a,mu); print("acc range",acc.min(),acc.max(),acc.mean())
Y=draw_items(mu,a,0.5,20000,rng)
t=time.time(); res=[]
for r in range(200):
    res.append(trial(Y,200,"rs",dict(B=72),rng,truth_acc=acc,nboot=50))
print("time/trial",(time.time()-t)/200)
for m in res[0]:
    arr=np.array([r[m] for r in res]); print(m, "bias",(arr[:,0]-arr[:,3]).mean().round(4),"cover",((arr[:,1]<=arr[:,3])&(arr[:,3]<=arr[:,2])).mean().round(3),"width",(arr[:,2]-arr[:,1]).mean().round(3),"truth",arr[:,3].mean().round(3))
