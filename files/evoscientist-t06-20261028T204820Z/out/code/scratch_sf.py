import os
os.environ['OMP_NUM_THREADS']='1'
import sys; sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import load
import bt
df=pd.read_csv('results/pairs_core.csv')
D=load('arena55k_human'); th=bt.fit_data(D); rank=np.argsort(-th[:D.M])
g=df[(df.board=='arena55k_human')&(df.z>1)&(df.z<3)].sort_values('z')
for r in g.itertuples():
    i,j=rank[r.rank_i],rank[r.rank_j]
    ks=[bt.min_perturbation(D,th,i,j,'drop',step_frac=s)['k'] for s in (0.5,0.2,0.05)]
    print(r.rank_i,r.rank_j,round(r.z,2),r.n_inv,ks, 'klin',r.klin_drop)
