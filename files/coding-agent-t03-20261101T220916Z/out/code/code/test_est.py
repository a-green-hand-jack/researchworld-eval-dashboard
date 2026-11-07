import numpy as np, time
from estimators import *
d=int(__import__('sys').argv[1]); rng=np.random.default_rng(0)
# random game: additive + pairwise interactions + a nonlinearity
w=rng.normal(size=d); Wp=rng.normal(size=(d,d))*0.4
ids_all=np.arange(1<<d); B=((ids_all[:,None]>>np.arange(d))&1).astype(float)
v=np.tanh(B@w*0.5 + 0.5*np.einsum('ni,ij,nj->n',B,Wp,B)*0.3)
v=v-v[0]
vf=lambda ids: v[np.asarray(ids)]
pc=popcount_table(d); phi=exact_shapley(v,d,pc); print("exact",np.round(phi,3), "resid",additivity_residual(v,d,phi,pc))
for m in [64,128,256,512,1024,2048,4096]:
    if m>(1<<d)-2: continue
    for est in ["kernel","leverage","perm"]:
        t=time.time(); R=[]; SE=[]
        for r in range(200):
            p,se=run_estimator(est,vf,d,m,r,want_se=True,pc=pc); R.append(p); SE.append(se)
        R=np.array(R); SE=np.array(SE)
        err=np.sqrt(((R-phi)**2).sum(1).mean())/np.linalg.norm(phi); bias=np.linalg.norm(R.mean(0)-phi)/np.linalg.norm(phi)
        ratio=np.nanmean(SE.mean(0)/R.std(0)) if SE.max()>0 else float('nan')
        print(f"m={m} {est:8s} relRMSE={err:.4f} relBias={bias:.4f} SE/SD={ratio:.2f} time/run={(time.time()-t)/200*1e3:.2f}ms")
