import sys,time; sys.path.insert(0,'code')
import numpy as np
from lb import agg, boards
for name in boards.BOARDS:
    B=boards.load(name); S=B.S
    print(name,S.shape, 'min',S.min(), [ (S[:,j]).max().round(1) for j in range(min(6,B.m))])
    mr = np.argsort(-S.mean(1)); 
    u=np.full(B.m,100.0)
    for rule in agg.ALL_RULES:
        if rule=='gmean' and S.min()<=0: continue
        t0=time.time(); res=[agg.target_costs(rule,S,int(t),u) for t in mr[[1,4,9]]]
        print(' ',rule, round(time.time()-t0,2),'s', [(round(r['l1'],2), r['br']) for r in res])
