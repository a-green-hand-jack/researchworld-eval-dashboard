"""E2 on HELM MMLU: random odd-size subject subsets, sigma-unit budgets. usage: run_e2_helm.py OUT.csv shard n_shards [draws=60] [targets_per_draw=10: ranks 2,3,4,5,6,8,11,16,21,31 by subset mean] [ms=5,9,15,25,41,57]
Draw d of size m uses default_rng([seed, m, d]); the same subset and targets are used for every rule (paired)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.e2 import run_draw
out = sys.argv[1]; shard, ns = int(sys.argv[2]), int(sys.argv[3])
draws = int(sys.argv[4]) if len(sys.argv) > 4 else 60
ntar = int(sys.argv[5]) if len(sys.argv) > 5 else 10
SEED = 20260101
df = pd.read_csv("data_proc/helm_mmlu_em.csv", index_col=0); S0 = df.values * 100.0
MS = tuple(int(x) for x in sys.argv[6].split(",")) if len(sys.argv) > 6 else (5, 9, 15, 25, 41, 57)
jobs = [(m, d) for m in MS for d in range(1 if m == 57 else draws)]
rows = []; t0 = time.time()
for k, (m, d) in enumerate(jobs):
    if k % ns != shard: continue
    rng = np.random.default_rng([SEED, m, d])
    cols = np.sort(rng.choice(S0.shape[1], m, replace=False)) if m < 57 else np.arange(57)
    S = S0[:, cols]; sig = S.std(axis=0)
    order = np.argsort(-S.mean(axis=1), kind="stable"); targets = order[[1, 2, 3, 4, 5, 7, 10, 15, 20, 30]][:ntar]
    rows += run_draw(S, targets, sig, 100.0, tl=20.0, meta=dict(board="helm", draw=d, m_sub=m, cols=" ".join(map(str, cols))))
    print(f"m={m} d={d} rows={len(rows)} t={time.time()-t0:.0f}", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
