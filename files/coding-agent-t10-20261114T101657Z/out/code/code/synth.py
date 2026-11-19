import numpy as np, json
from multiprocessing import Pool
from run import ppi_family, crossfit, ci
from scipy.stats import t as tdist
def gen(kind,m,rng):
    z=rng.normal(size=m)
    if kind=='linear': y=z+rng.normal(size=m)        # Yhat already calibrated
    elif kind=='nonmono': y=z**2+0.5*rng.normal(size=m)   # corr(Y,Yhat)=0, E[Y|Yhat]=Yhat^2
    else: y=np.tanh(2*z)+0.5*rng.normal(size=m)      # monotone nonlinear
    return y,z
def one(a):
    kind,n,seed=a; rng=np.random.default_rng(seed); N=20000
    truth={'linear':0,'nonmono':1,'monotone':0}[kind]
    Y,F=gen(kind,n,rng); _,Fu=gen(kind,N,rng); out={}
    out['classical']=ci(Y.mean(),Y.std(ddof=1)/n**.5)
    out['PPI++']=ci(*ppi_family(Y,F,Fu))
    fl,fu=crossfit(Y,F[:,None],Fu[:,None],'gbm',rng=rng); out['recal-gbm']=ci(*ppi_family(Y,fl,fu))
    return kind,n,{k:(float(v[0]<=truth<=v[1]),v[1]-v[0]) for k,v in out.items()}
if __name__=='__main__':
    jobs=[(k,n,r+1000*n) for k in ('linear','nonmono','monotone') for n in (100,500,2000) for r in range(1000)]
    res={}
    with Pool(36) as p:
        for k,n,o in p.imap_unordered(one,jobs,chunksize=8):
            for m,v in o.items(): res.setdefault(f'{k}|{n}|{m}',[]).append(v)
    json.dump(res,open('/work/code/synth.json','w'))
    with open('/work/paper/synth.tex','w') as f:
        f.write('\\begin{tabular}{llrrrrrr}\\toprule\n & & \\multicolumn{2}{c}{classical} & \\multicolumn{2}{c}{PPI++} & \\multicolumn{2}{c}{recal-gbm}\\\\\nsetting & $n$ & cov & width & cov & width & cov & width\\\\\\midrule\n')
        for k in ('linear','nonmono','monotone'):
            for n in (100,500,2000):
                l=[k,str(n)]
                for m in ('classical','PPI++','recal-gbm'):
                    a=np.array(res[f'{k}|{n}|{m}']); l+= [f'{100*a[:,0].mean():.1f}',f'{a[:,1].mean():.3f}']
                f.write(' & '.join(l)+'\\\\\n'); print(l)
        f.write('\\bottomrule\\end{tabular}\n')
