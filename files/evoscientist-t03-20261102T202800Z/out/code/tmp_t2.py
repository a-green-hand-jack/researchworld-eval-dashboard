import sys,time; sys.path.insert(0,'src')
import run_main as R, config as C, numpy as np
for dn,k,est in [('german','rf','kernel'),('german','mlp','perm'),('acs','rf','kernel'),('gmsc','mlp','kernel'),('acs','xgb','perm')]:
    t=time.time(); out,ref,kind=R.e1_instance(dn,k,est,0,C.BUDGETS,C.R); print(dn,k,est,'%.1fs'%(time.time()-t),kind, out.shape)
