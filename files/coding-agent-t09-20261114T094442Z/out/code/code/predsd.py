# plug-in prediction of sd(GATE_hat) for ols_frac / ols_rich from the realised design matrix alone
import sys; sys.path.insert(0,'/work/code')
from sim import *; from run_all import exp
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from look import load
rows=[]
for e in ['E1','E2','E3','E4','E5']:
    dd=load(e); dd=dd[dd.est.isin(['ols_frac','ols_rich'])]
    for cfg in exp[e]:
        A,lab=graph(cfg['graph'],1); n=A.shape[0]; deg=np.asarray(A.sum(1)).ravel(); dbar=deg.mean()
        ld=np.log(deg); ld=(ld-ld.mean())/ld.std(); cl=lab if cfg['design']=='cluster' else np.arange(n); K=cl.max()+1
        rng=np.random.default_rng(0); one=np.ones(n); zero=np.zeros(n)
        for m in ['ols_frac','ols_rich']:
            c=(phi(m,one,one,deg/dbar,ld)-phi(m,zero,zero,zero,ld)).mean(0); v=[]
            for _ in range(5):
                z=(rng.random(K)<cfg['p']).astype(float)[cl]; x=A@z/deg; X=phi(m,z,x,A@z/dbar,ld)
                v.append(c@np.linalg.pinv(X.T@X)@c)
            s2=1.25 if m=='ols_frac' else 1.0   # ols_frac leaves 0.5*logdeg (var .25) in residual
            s2*=cfg.get('sigma',1.)**2
            obs=dd[(dd.est==m)&(dd.seed==cfg['seed'])]
            if len(obs): rows.append(dict(exp=e,est=m,model=cfg['model'],design=cfg['design'],pred=np.sqrt(s2*np.mean(v)),obs=obs.sd.iloc[0],g=cfg['graph']['kind']))
import pandas as pd; r=pd.DataFrame(rows); r['ratio']=r.obs/r.pred
r.to_csv('/work/results/predsd.csv',index=False)
print(len(r)); print(r.groupby('est').ratio.describe().round(3)); print(r.groupby(['est','g']).ratio.median().round(3))
print('corr log',np.corrcoef(np.log(r.pred),np.log(r.obs))[0,1])
plt.rcParams.update({'font.size':8}); fig,ax=plt.subplots(figsize=(3.3,2.8))
for g,mk in zip(r.g.unique(),'osv^D'):
    q=r[r.g==g]; ax.scatter(q.pred,q.obs,s=9,marker=mk,label=g,alpha=.7)
ax.plot([.02,3],[.02,3],'k--',lw=.7); ax.set_xscale('log');ax.set_yscale('log');ax.set_xlabel('plug-in predicted SD');ax.set_ylabel('simulated SD');ax.legend(fontsize=6)
plt.tight_layout(); plt.savefig('/work/paper/fig_predsd.pdf')
