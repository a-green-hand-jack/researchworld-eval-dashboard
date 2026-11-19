"""Strongest baseline per benchmark and protocol, chosen from SOURCE models only (no target scores used).
The source set of each protocol (rep 0 for `random`, the fixed split for `extrap`) is split again with the same protocol
(inner extrap: top 20% of the sources are pseudo-targets; inner random: 20% random; 5 inner reps); all non-proposed
methods are run at n = 50, 100 and ranked by mean RMSE.   usage: source_cv.py BENCH OUT.csv"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import data, protocol as P, methods as M, methods2, methods3, methods4

BASE = "random,strat_random,anchor,calib,ridge,irt_rand,irt_info,anchor_irt,aipw_rand,anchor_aipw,ppi,aipw_knn,aipw_ens,aipw_ridge_repo,aipw_ridge_cf".split(",")
bench, out = sys.argv[1], sys.argv[2]
X, models = P.dedup(*data.load(bench))
acc = X.mean(1)
rows = []
for proto in ["random", "extrap"]:
    src, _ = P.split(proto, acc, 0)
    Xs = X[src]
    accs = Xs.mean(1)
    for rep in range(5):
        s2, t2 = P.split(proto, accs, 100 + rep)
        ctx = {}
        for n in (50, 100):
            for name in BASE:
                m = M.ALL[name]()
                idx = m.fit(Xs[s2], n, 5000 * rep + n, ctx)
                pred = m.predict(Xs[t2][:, idx])
                rows.append((bench, proto, name, n, rep, float(np.sqrt(((pred - accs[t2]) ** 2).mean()))))
df = pd.DataFrame(rows, columns="bench protocol method n rep rmse".split())
g = df.groupby(["bench", "protocol", "method"], as_index=False).rmse.mean()
g["rank"] = g.groupby(["bench", "protocol"]).rmse.rank()
g.to_csv(out, index=False)
