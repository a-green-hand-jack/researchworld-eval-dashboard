import sys, time; sys.path.insert(0,"code")
import datasets as D, btlib as bt, numpy as np
t=time.time()
ds=D.all_main()
print("load", time.time()-t)
for k,d in ds.items():
    tt=bt.build_table(d["a"],d["b"],d["y"],h=d["h"],use_home=d["use_home"])
    t=time.time(); f=bt.fit_bt(tt); dt=time.time()-t
    r=bt.ranking(f.theta, tt.m)
    print(f"{k:32s} N={int(tt.N):7d} m={tt.m:3d} T={len(tt.n):6d} ties={np.sum(tt.n[tt.y==0.5])/tt.N:.2f} fit={dt*1000:.0f}ms it={f.n_iter} top3={[tt.players[x] for x in r[:3]]} gaps={np.round(-np.diff(f.theta[r[:4]]),3)}")
