import time,numpy as np
from ppi_py import ppi_mean_ci, ppi_mean_pointestimate
from ppi_py.datasets import load_dataset
rng=np.random.default_rng(0)
for name,n in [('galaxies',300),('forest',100),('gene_expression',300),('census_income',1000),('ballots',None)]:
    d=load_dataset('/hutian/scratch/dl/data/',name)
    Y,Yh=d['Y'],d['Yhat']
    if name=='ballots': Yu=d['Yhat_unlabeled']; n=len(Y)
    else:
        idx=rng.permutation(len(Y)); Yu=Yh[idx[n:]]; Y=Y[idx[:n]]; Yh=Yh[idx[:n]]
    t=time.time()
    for _ in range(100): ci=ppi_mean_ci(Y,Yh,Yu,alpha=0.05)
    print(name,len(Y),len(Yu),ci,'ms/ci',(time.time()-t)*10)
