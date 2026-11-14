import sys,time,pickle,os
sys.path.insert(0,'code')
import numpy as np
from common import *
for ds,m in [("gmsc","rf"),("arrhythmia","xgb"),("arrhythmia","mlp")]:
    Xtr,Xte,ytr,yte,names,cat=split(ds)
    o=pickle.load(open(f"results/model_{ds}_{m}.pkl","rb")); mod,meta=o["model"],o["meta"]
    fn=Fn(mod); bg=Xtr[meta["bg_idx"]]; x=Xte[meta["inst"][0]]
    for k in ["kernel","kernel_l1","perm"]:
        t=time.time(); fn.rows=0; v=explain_once(k,fn,bg,x,3000,0); dt=time.time()-t
        print(ds,m,k,"B=1000 sec=%.2f rows=%d"%(dt,fn.rows),flush=True)
