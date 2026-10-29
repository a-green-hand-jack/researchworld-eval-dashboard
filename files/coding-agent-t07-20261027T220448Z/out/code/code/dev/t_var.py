import sys, os; sys.path.insert(0,'/work/code')
os.environ['OMP_NUM_THREADS']='1'
import numpy as np, pandas as pd, irt as I, bp
from data import load
from run_exp import make_split
from joblib import Parallel, delayed
def run(bench, prot, seed, n):
    Y,o=load(bench); S,T=make_split(Y,o,prot,seed); YS,YT=Y[S],Y[T]; N=Y.shape[1]
    rng=np.random.default_rng(seed); accT=YT.mean(1); pS=YS.mean(0)
    out=[]
    for ra in [1.0,0.2]:
        fit=I.fit_irt(YS,4,reg_a=ra,seed=seed); P=I.predict_probs(fit['theta'],fit['A'],fit['b']); v=((YS-P)**2).mean(0)
        C,W=bp.d_pps(N,n,rng,pS=pS,vS=v,lam=0.5); Yc=YT[:,C]
        for pv in [4.0,25.0,1000.0]:
            th=I.infer_theta(fit['A'][C],fit['b'][C],Yc,pv); Z=th@fit['A'].T+fit['b'][None]
            pure=I._sig(Z).mean(1); greg=pure+((Yc-I._sig(Z[:,C]))*W).sum(1)
            s,c=I.platt(Z[:,C],Yc); Pc=I._sig(s[:,None]*Z+c[:,None]); cal=Pc.mean(1); calg=cal+((Yc-Pc[:,C])*W).sum(1)
            for nm,e in [('pure',pure),('greg',greg),('cal',cal),('calgreg',calg)]:
                m=bp.metrics(e,accT); out.append(dict(bench=bench,prot=prot,seed=seed,n=n,ra=ra,pv=pv,est=nm,rmse=m['rmse'],bias=m['bias']))
        # random mean ref
    C=rng.choice(N,n,replace=False); m=bp.metrics(YT[:,C].mean(1),accT); out.append(dict(bench=bench,prot=prot,seed=seed,n=n,ra=0,pv=0,est='rand',rmse=m['rmse'],bias=m['bias']))
    return out
jobs=[(b,'top',s,n) for b in ['ifeval','gpqa','musr','arc_challenge','openllm_math','gsm','mmlu','legalbench','med_qa'] for s in range(2000,2008) for n in [25,100]]
res=sum(Parallel(n_jobs=38)(delayed(run)(*j) for j in jobs),[])
df=pd.DataFrame(res); ref=df[df.est=='rand'].set_index(['bench','seed','n']).rmse
df=df[df.est!='rand']; df['rel']=[r.rmse/ref[(r.bench,r.seed,r.n)] for r in df.itertuples()]
print(df.pivot_table(index=['est','ra','pv'],columns='n',values='rel',aggfunc=lambda x: np.exp(np.log(x).mean())).round(3))
print(df.pivot_table(index=['est','ra','pv'],columns='n',values='bias',aggfunc='mean').round(4))
