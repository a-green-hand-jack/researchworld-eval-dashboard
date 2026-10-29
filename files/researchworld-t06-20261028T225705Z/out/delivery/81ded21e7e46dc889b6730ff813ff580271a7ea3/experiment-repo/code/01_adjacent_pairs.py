"""Worst-case (min drop / min flip, plus head-to-head-only baselines) budget of every adjacent rank pair.
Usage: 01_adjacent_pairs.py DATASET  ->  results/adjacent_pairs_<DATASET>.csv"""
import sys, time, numpy as np, pandas as pd, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
ds = sys.argv[1]
c = rsens.load(ds); th = rsens.fit(c); r = rsens.ranking(th, c.p)
H_inv = np.linalg.inv(rsens.hess(c, th)); rows = []; t0 = time.time()
for pos in range(len(r) - 1):
    a, b = r[pos], r[pos + 1]; q = rsens.qvec(c, a, b)
    se = float(np.sqrt(q @ H_inv @ q))
    ab = ((c.I == a) & (c.J == b)) | ((c.I == b) & (c.J == a))
    inv = (c.I == a) | (c.J == a) | (c.I == b) | (c.J == b)
    row = dict(dataset=ds, pos=pos + 1, a=c.names[a], b=c.names[b], phi=th[a] - th[b], se_phi=se, z=(th[a] - th[b]) / se,
               n_ab=int(ab.sum()), n_a=int(((c.I == a) | (c.J == a)).sum()), n_b=int(((c.I == b) | (c.J == b)).sum()), N=c.n, p=c.p)
    for mode in ("drop", "flip"):
        res = rsens.worst_case(c, a, b, mode, th0=th)
        row[f"k_{mode}"], row[f"k1_{mode}"] = res["k"], res["k_first_order"]
        row[f"k_direct_{mode}"] = rsens.worst_case(c, a, b, mode, allowed=ab, th0=th)["k"]
        row[f"k_involving_{mode}"] = rsens.worst_case(c, a, b, mode, allowed=inv, th0=th)["k"]
    rows.append(row)
print(ds, "done", round(time.time() - t0, 1), flush=True)
pd.DataFrame(rows).to_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../results/adjacent_pairs_{ds.replace(':', '_')}.csv", index=False)
