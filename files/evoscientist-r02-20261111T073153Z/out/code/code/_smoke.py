import numpy as np, time
from compconf import *
rng=np.random.default_rng(0)
K=5
for dgp in ["ln","ln_het","dir","mult"]:
    W=make_world(rng,K)
    X,Y,m=gen_data(rng,W,3000,dgp,K)
    print(dgp,"maxm mean",m.max(1).mean().round(2),"zeros frac",(Y<=0).any(1).mean().round(3),"minY",Y.min().round(10))
    f=fit_softmax_reg(X[:1000],Y[:1000]); F=f(X)
    Ftr,Ytr=F[1000:1500],Y[1000:1500]
    t=time.time()
    for eps in [1e-3]:
        aux=fit_aux(Ytr,Ftr,eps)
        for s in ["l2","l1","linf","hell","kl","ait","mah","l2n"]:
            sc=Score(s,K,eps,aux)
            # check pair vs paired consistency
            a=sc.pair(F[:3],Y[:4]); b=np.array([[sc.paired(Y[j:j+1],F[i:i+1])[0] for j in range(4)] for i in range(3)])
            assert np.allclose(a,b,atol=1e-6),(s,a,b)
            cs=sc.paired(Y[1500:2500],F[1500:2500]); q=conf_quantile(cs,0.1)
            cov,sp,su=evaluate(sc,F[2500:],Y[2500:],np.full(500,q),Y[:500],None)
            print(" ",s,round(cov.mean(),3),round(sp.mean(),4))
    print("time",time.time()-t)
