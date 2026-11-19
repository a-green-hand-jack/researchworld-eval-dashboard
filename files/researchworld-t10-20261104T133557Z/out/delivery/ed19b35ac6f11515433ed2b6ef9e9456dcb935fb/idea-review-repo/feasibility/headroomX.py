import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor as H
from ppi_py.datasets import load_dataset
D='/hutian/scratch/dl/data/'
for name in ['census_income','census_healthcare','census_education']:
    d=load_dataset(D,name); Y,F,X=d['Y'].astype(float),d['Yhat'].astype(float),d['X'].astype(float)
    Z=np.column_stack([F,X]); idx=np.random.default_rng(0).permutation(len(Y)); h=len(Y)//2; r=np.empty(len(Y)); rf=np.empty(len(Y))
    for a,b in [(idx[:h],idx[h:]),(idx[h:],idx[:h])]:
        r[b]=Y[b]-H(max_iter=100).fit(Z[a],Y[a]).predict(Z[b])
        rf[b]=Y[b]-H(max_iter=100).fit(F[a,None],Y[a]).predict(F[b,None])
    bb=np.cov(Y,F)[0,1]/F.var(); vl=(Y-Y.mean()-bb*(F-F.mean())).var()
    print(name,'V(f,X)/V_lin',r.var()/vl,'width',np.sqrt(r.var()/vl),'| V(g(f) GBM)/V_lin',rf.var()/vl)
