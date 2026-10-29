import os
os.environ['OMP_NUM_THREADS']='1'; os.environ['OPENBLAS_NUM_THREADS']='1'
import sys,time; sys.path.insert(0,'code')
import numpy as np
from common import load
import bt
for nm in ['mtbench_human','arena55k_human','nba_2010','nba_alltime']:
    D=load(nm); t=time.time(); th=bt.fit_data(D); print(nm,'fit',time.time()-t)
    order=np.argsort(-th[:D.M]);
    i,j=order[0],order[1]
    print('gap',th[i]-th[j],'se',bt.se_gap_sandwich(D,th,i,j))
    i,j=order[0],order[3]
    print('gap',th[i]-th[j],'se',bt.se_gap_sandwich(D,th,i,j))
    for mode in ['drop','flip','add']:
        t=time.time(); r=bt.min_perturbation(D,th,i,j,mode); print(mode,r,'N',D.N,round(time.time()-t,2),'s')
