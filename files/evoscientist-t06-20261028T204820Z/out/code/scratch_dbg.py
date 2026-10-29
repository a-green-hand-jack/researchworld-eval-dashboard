import os
os.environ['OMP_NUM_THREADS']='1'
import sys; sys.path.insert(0,'code')
import numpy as np
from common import load
import bt
from exp_main import GROUPS, pair_list
for nm in GROUPS['core']:
    D=load(nm); th=bt.fit_data(D)
    rank,pairs=pair_list(th,D.M); r=np.argsort(-th[:D.M])
    bad=[(x,y) for x,y in pairs if not (th[r[x]]-th[r[y]]>0)]
    if bad or np.isnan(th).any(): print(nm,bad[:5],np.isnan(th).sum(), np.sort(th[:D.M])[:3])
