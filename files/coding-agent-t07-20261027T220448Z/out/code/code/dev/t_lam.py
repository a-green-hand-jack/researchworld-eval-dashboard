import sys, os; sys.path.insert(0,'/work/code')
os.environ['OMP_NUM_THREADS']='1'
import numpy as np, pandas as pd, irt as I, bp, data
from data import load
from run_exp import make_split
from joblib import Parallel, delayed
GRID=[(1,1),(5,1),(20,1),(1e4,1),(1e4,0.1),(1e4,1e4)]
def run(bench, prot, seed):
    Y,o=load(bench); S,T=make_split(Y,o,prot,seed); YS,YT=Y[S],Y[T]; N=Y.shape[1]
    rng=np.random.default_rng(seed); accT=YT.mean(1); pS=YS.mean(0)
    fit=I.fit_irt(YS,4,seed=seed); P=I.predict_probs(fit['theta'],fit['A'],fit['b']); v=((YS-P)**2).mean(0)
    out=[]
    for n in [25,100]:
        C,W=bp.d_pps(N,n,rng,pS=pS,vS=v,lam=1.0); Yc=YT[:,C]
        th=I.infer_theta(fit['A'][C],fit['b'][C],Yc,4.0); Z=th@fit['A'].T+fit['b'][None]
        for ls,lc in GRID:
            s,c=I.platt(Z[:,C],Yc,lam=ls,lam_c=lc); e=I._sig(s[:,None]*Z+c[:,None]).mean(1)
            m=bp.metrics(e,accT); out.append(dict(bench=bench,prot=prot,seed=seed,n=n,g=f'{ls:g}/{lc:g}',rmse=m['rmse'],bias=m['bias']))
        Cr=rng.choice(N,n,replace=False); m=bp.metrics(YT[:,Cr].mean(1),accT); out.append(dict(bench=bench,prot=prot,seed=seed,n=n,g='rand',rmse=m['rmse'],bias=m['bias']))
    return out
jobs=[(b,p,s) for b in ['ifeval','gpqa','musr','arc_challenge','openllm_math','gsm','mmlu','legalbench','med_qa'] for p in ['random','top','org'] if not(p=='org' and b not in data.OPENLLM) for s in range(2000,2008)]
df=pd.DataFrame(sum(Parallel(n_jobs=38)(delayed(run)(*j) for j in jobs),[]))
ref=df[df.g=='rand'].set_index(['bench','prot','seed','n']).rmse; df=df[df.g!='rand']; df['rel']=[r.rmse/ref[(r.bench,r.prot,r.seed,r.n)] for r in df.itertuples()]
print(df.pivot_table(index='g',columns=['prot','n'],values='rel',aggfunc=lambda x: np.exp(np.log(x).mean())).round(3))
