import sys, time, numpy as np
sys.path.insert(0, '/work/code')
from data import load
from irt import *
Y,_ = load(sys.argv[1]); rng=np.random.default_rng(0)
perm=rng.permutation(len(Y)); nt=int(.3*len(Y)); T=perm[:nt]; S=perm[nt:]
for d in [1,2,4,8]:
    t0=time.time(); M=fit_irt(Y[S],d); t=time.time()-t0
    # eval: random coreset 100 items
    for n in [25,100]:
        C=rng.choice(Y.shape[1],n,replace=False)
        th=infer_theta(M['A'][C],M['b'][C],Y[T][:,C]); P=predict_probs(th,M['A'],M['b'])
        est=P.mean(1); tru=Y[T].mean(1); rm=np.sqrt(np.mean((est-tru)**2)); rr=np.sqrt(np.mean((Y[T][:,C].mean(1)-tru)**2))
        print(sys.argv[1],'d',d,'n',n,'irt rmse %.4f random rmse %.4f fit %.1fs'%(rm,rr,t))
