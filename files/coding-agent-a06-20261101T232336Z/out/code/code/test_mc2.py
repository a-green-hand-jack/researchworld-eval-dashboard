import sys; sys.path.insert(0,"/work/code")
import numpy as np, time
from synth import *; from mc import *
rng=np.random.default_rng(0)
for spread in (0.0,0.05,0.15):
    mu=make_mu(spread,rng); a=-0.4
    acc=acc_from_mu(a,mu)
    Y=draw_items(mu,a,0.5,20000,rng)
    t=time.time(); res=[]
    for r in range(300):
        res.append(trial_rs_extras(Y,200,72,rng,truth_acc=acc))
    print("spread",spread,"time/trial",(time.time()-t)/300, "acc sd",acc.std())
    for m in res[0]:
        arr=np.array([r[m] for r in res]); ok=np.isfinite(arr[:,1])&np.isfinite(arr[:,2])
        print(f"{m:14s} bias {np.nanmean(arr[:,0]-arr[:,3]):+.4f} cover {((arr[:,1]<=arr[:,3])&(arr[:,3]<=arr[:,2]))[ok].mean():.3f} width {np.nanmean((arr[:,2]-arr[:,1])[ok]):.3f} finite {ok.mean():.2f}")
