"""Population-level (full-data) quantities for the mean-estimation problem.
For each dataset with full (Y, Yhat) pairs: Var(Y), best-linear residual variance, nonparametric residual variance
E[Var(Y|f)] (isotonic fit, and K-bin fit), and implied asymptotic variance ratios."""
import numpy as np, json, sys
from sklearn.isotonic import IsotonicRegression
D='/work/data/'
names=['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare','census_education']
out={}
for nm in names:
    d=np.load(D+nm+'.npz'); y=d['Y'].astype(float); f=d['Yhat'].astype(float)
    V=y.var(); b=np.cov(y,f)[0,1]/f.var(); a=y.mean()-b*f.mean()
    r_lin=((y-a-b*f)**2).mean()
    iso=IsotonicRegression(out_of_bounds='clip').fit(f,y); r_iso=((y-iso.predict(f))**2).mean()
    # K-bin (quantile) fit with K=50 (for big sets) to compare
    K=min(50,len(y)//40); q=np.quantile(f,np.linspace(0,1,K+1)); idx=np.clip(np.searchsorted(q,f,side='right')-1,0,K-1)
    gb=np.array([y[idx==k].mean() for k in range(K)]); r_bin=((y-gb[idx])**2).mean()
    # also identity predictor (PPI lambda=1) residual
    r_id=((y-f)**2).mean()
    out[nm]=dict(pop=len(y),mean=y.mean(),var=V,corr=float(np.corrcoef(y,f)[0,1]),slope=b,r_id=r_id,r_lin=r_lin,r_iso=r_iso,r_bin=r_bin,
        nonlin_share_iso=1-r_iso/r_lin,nonlin_share_bin=1-r_bin/r_lin,var_g_iso=float(iso.predict(f).var()),var_f=f.var())
    print(nm,{k:(round(v,5) if isinstance(v,float) else v) for k,v in out[nm].items()})
json.dump(out,open('/work/results/pop_stats.json','w'),indent=1)
