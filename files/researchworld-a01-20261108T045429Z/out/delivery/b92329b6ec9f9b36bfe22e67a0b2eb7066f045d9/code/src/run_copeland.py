"""Exact Copeland-first minimum L1 (MILP) vs the Condorcet-winner cost, on a rank-stratified subset (the MILP takes 10-300 s per HELM target).
Usage: python3 src/run_copeland.py OUT [--procs 2]    targets: HELM ranks 2,3,4,5,6,8,10,15,20,30,50,70 (mean rank), caps ceil and gain10;
OLLB top-500 slice ranks 2,3,5,8,11 (mean rank within the slice), same caps.  Columns: dataset,cap,target,target_idx,rank_mean,copeland_L1,secs
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import ordinal as od, data as dt
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--procs", type=int, default=2); a = ap.parse_args()
JOBS = []
for ds, ranks in (("helm", [2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 70]), ("ollb_top500", [2, 3, 5, 8, 11])):
    X, names, _, _ = dt.load(ds); r = rankdata(-X.mean(axis=1), method="min"); order = np.argsort(r, kind="stable")
    for cap in ("ceil", "gain10"):
        for k in ranks: JOBS.append((ds, cap, int(order[k - 1]), int(r[order[k - 1]])))
def run(j):
    ds, cap, i, rk = j; X, names, _, _ = dt.load(ds); t = time.time()
    try: v = od.copeland_min_investment(X, i, dt.make_cap(cap, X, i), 1e-3, "L1")
    except RuntimeError as e: v = np.nan
    return dict(dataset=ds, cap=cap, target=names[i], target_idx=i, rank_mean=rk, copeland_L1=v, secs=time.time() - t)
if __name__ == "__main__":
    rows = []
    with Pool(a.procs) as p:
        for r in p.imap_unordered(run, sorted(JOBS, key=lambda j: j[0] != "ollb_top500")):
            rows.append(r); print(r, flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
