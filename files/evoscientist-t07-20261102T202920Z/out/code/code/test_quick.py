import time, numpy as np
from bp import *
for name in ["ifeval","gpqa","mmlu_pro","mmlu"]:
    Y=load(name); M,N=Y.shape
    rng=np.random.default_rng(0)
    perm=rng.permutation(M); nt=int(.3*M); tg=perm[:nt]; sr=perm[nt:]
    for d in [1,3]:
        t=time.time(); mod,res=fit_latent(Y[sr],d); t1=time.time()-t
        truth=Y[tg].mean(1)
        rows=[]
        for n in [20,100]:
            S,pi=sample_random(N,n,rng)
            pl=est_plugin(mod,S,Y[tg][:,S]); df,gr,be=est_crossfit(mod,S,pi[S],Y[tg][:,S],rng)
            mean=Y[tg][:,S].mean(1)
            rows.append((n,[round(np.abs(x-truth).mean(),4) for x in (mean,pl,df,gr)],round(be.mean(),2)))
        print(name,Y.shape,d,"fit %.1fs"%t1,res.nit,rows,flush=True)
