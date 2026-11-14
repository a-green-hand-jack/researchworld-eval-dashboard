"""Wall-clock of the exact ordinal MILPs at full OLLB size (M=4496), a few rank-stratified targets, per cap.
Usage: python3 src/time_milp.py OUT.csv   (records per-call seconds; justifies the sampled-target design for rank rules)"""
import sys, time, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import ordinal as od, data as dt
X, names, tasks, meta = dt.load("ollb"); M, n = X.shape
order = np.argsort(rankdata(-X.mean(axis=1), method="min"), kind="stable")
targets = [order[r] for r in (1, 9, 99, 999, 4000)]       # mean-rank 2, 10, 100, 1000, 4001
rows = []
t0 = time.time(); od.copeland_scores(X); tc = time.time() - t0
print(f"copeland_scores M={M}: {tc:.2f}s", flush=True)
for cap_name in ("ceil", "front0", "gain10"):
    for rule in ("borda", "condorcet", "plurality"):
        for i in targets:
            cap = dt.make_cap(cap_name, X, i, "ollb"); t0 = time.time()
            L1 = od.MIN_INV[rule](X, i, cap, 1e-3, "L1"); t1 = time.time() - t0; t0 = time.time()
            K = od.MIN_INV[rule](X, i, cap, 1e-3, "K"); t2 = time.time() - t0
            rows.append(dict(cap=cap_name, rule=rule, target_idx=int(i), rank_mean=int(rankdata(-X.mean(axis=1), method="min")[i]),
                             L1=L1, K=K, sec_L1_milp=t1, sec_K_milp=t2))
            print(rows[-1], flush=True); pd.DataFrame(rows).to_csv(sys.argv[1], index=False)
