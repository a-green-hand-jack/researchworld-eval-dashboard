"""How often is the KernelSHAP normal-equation matrix (near-)singular at small budgets? Writes results/kernel_conditioning.csv"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import numpy as np, pandas as pd
from data import RESULTS
from shapsim import _kernel_plan

rng = np.random.default_rng(0)
rows = []
for d in (8, 10, 20):
    for mult in (2, 3, 4, 8, 16):
        m = mult * d
        conds = []
        for _ in range(300):
            masks, w = _kernel_plan(d, m, rng)
            Mf = masks.astype(float)
            et = Mf[:, :-1] - Mf[:, -1:]
            A = et.T @ (et * w[:, None])
            conds.append(np.linalg.cond(A))
        conds = np.array(conds)
        rows.append(dict(d=d, mult=mult, budget=m, frac_cond_gt_1e8=float((conds > 1e8).mean()), median_cond=float(np.median(conds))))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(RESULTS, "kernel_conditioning.csv"), index=False)
print(df.to_string())
