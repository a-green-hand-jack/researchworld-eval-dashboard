"""Replication on a second, later crowd snapshot (Arena-140k, Apr-Jul 2025; 135,634 votes, 53 models).
 (a) all pairs, same protocol as exp_main  -> results/pairs_arena140k.csv
 (b) session-level deletion (unit = evaluation session) vs vote-level deletion for 300 random pairs
     -> results/cluster_arena140k.csv
(temporal split: see exp_temporal.py)"""
import time, numpy as np, pandas as pd
from multiprocessing import Pool
import exp_main as M
import datasets as ds
from bt import *
from cluster import min_clusters, votes_index

SESS = {}

def clus_task(a):
    i, j = a
    b = M.BOARDS["arena140k"]; v_cfg, v_lab, v_cl = SESS["v"]
    th = M.get_fit("arena140k"); z = (th[i] - th[j]) / b.ij_se(th, i, j)
    ks = min_clusters(b, v_cfg, v_lab, v_cl, i, j)
    kv = min_edits(b, i, j, "drop", int(0.3 * b.n), th0=th)["k"]
    return dict(i=i, j=j, z=z, n=b.n, nsess=int(v_cl.max()) + 1, k_sessions=ks, k_votes=kv)

def kendall(a, b):
    da = np.sign(a[:, None] - a[None, :]); db = np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(len(a), 1)
    return float(np.mean(da[iu] * db[iu]))

if __name__ == "__main__":
    d = ds.arena140k_votes()
    b = ds.arena140k(); M.BOARDS["arena140k"] = b
    th = b.fit(); s = th[: b.m]
    tasks = [("arena140k", i, j) for i in range(b.m) for j in range(b.m) if s[i] > s[j]]
    t0 = time.time()
    with Pool(38) as p:
        out = sum(p.map(M.task, tasks, chunksize=4), [])
    pd.DataFrame(out).to_csv("/work/results/pairs_arena140k.csv", index=False)
    print("pairs done", time.time() - t0, flush=True)

    # (b) sessions
    idx = {n: k for k, n in enumerate(b.names)}
    ia = d.model_a.map(idx).values; ib = d.model_b.map(idx).values; sw = ia > ib
    lo, hi = np.where(sw, ib, ia), np.where(sw, ia, ib); yy = np.where(sw, 1 - d.y.values, d.y.values)
    v_cfg, v_lab = votes_index(b, lo, hi, np.rint(yy * 2).astype(int))
    v_cl = pd.factorize(d.evaluation_session_id.values)[0]
    SESS["v"] = (v_cfg, v_lab, v_cl)
    rng = np.random.default_rng(3)
    sel = []
    for (i, j) in [(t[1], t[2]) for t in tasks]:
        z = (s[i] - s[j]) / b.ij_se(th, i, j)
        if z > 2: sel.append((i, j))
    sel = [sel[k] for k in rng.choice(len(sel), min(300, len(sel)), replace=False)]
    with Pool(38) as p:
        res = p.map(clus_task, sel, chunksize=2)
    pd.DataFrame(res).to_csv("/work/results/cluster_arena140k.csv", index=False)
    print("cluster done", time.time() - t0, flush=True)
