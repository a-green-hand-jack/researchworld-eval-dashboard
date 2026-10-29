import sys,time; sys.path.insert(0,"code")
from common import *
d=D.arena55k()[0]; tt=table(d); f=bt.fit_bt(tt); r=bt.ranking(f.theta,tt.m)
for kind in ["drop","flip"]:
    t=time.time(); res=bt.min_perturbation(tt,int(r[0]),int(r[1]),kind,fit0=f); print(kind,res["k"],res["k_oneshot"],res["k_pred"],res["n_iter"],time.time()-t)
    t=time.time(); res=bt.min_perturbation(tt,int(r[1]),int(r[2]),kind,fit0=f); print(kind,res["k"],res["k_oneshot"],res["k_pred"],res["n_iter"],time.time()-t)
tta=table(d,all_pairs=True); f=bt.fit_bt(tta)
t=time.time(); res=bt.min_perturbation(tta,int(r[1]),int(r[2]),"add",fit0=f); print("add",res["k"],res["k_oneshot"],res["k_pred"],res["n_iter"],time.time()-t, res["moves"][:3], [tta.players[x] for x in (tta.a[res["moves"][0][1]], tta.b[res["moves"][0][1]])])
