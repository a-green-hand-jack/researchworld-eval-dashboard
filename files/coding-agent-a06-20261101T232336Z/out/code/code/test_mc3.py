import sys; sys.path.insert(0,"/work/code")
import numpy as np, time
from synth import *; from mc import *
rng=np.random.default_rng(1)
for spread in (0.0,0.05,0.15):
    mu=make_mu(spread,rng); a=-0.4; acc=acc_from_mu(a,mu); Y=draw_items(mu,a,0.5,20000,rng)
    for algo,kw in [("rs",dict(B=72)),("rs",dict(B=8)),("sh",dict(B=72)),("ca",{}),("mipro",dict(B=40))]:
      for n in (100,400):
        res=[trial(Y,n,algo,kw,rng,truth_acc=acc,nboot=60) for _ in range(150)]
        s=f"spread {spread} {algo}{kw} n={n}: "
        for m in ("naive","boot_opt","boot_632","holdout","crossfit"):
            arr=np.array([r[m] for r in res]); s+=f"| {m} b{(arr[:,0]-arr[:,3]).mean():+.3f} c{((arr[:,1]<=arr[:,3])&(arr[:,3]<=arr[:,2])).mean():.2f} "
        print(s,flush=True)
