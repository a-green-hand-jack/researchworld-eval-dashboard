"""Population-level headroom of control-variate refinements over power-tuned PPI++ (claim C1).

For each pool, the control variate m is the L2 projection of Y on a class (affine in Yhat = PPI++; isotonic in
Yhat; GBM in Yhat; linear / GBM in (Yhat, X)), fitted with 2-fold cross-fitting on the FULL pool (no finite-n cost).
Asymptotic CI width^2 * n = Var(Y) - Cov(Y,m)^2 / ((1+rho) Var(m)),  rho = n/N;  rho -> 0 (N large) and rho = 1 reported.
Uncertainty: SD over 10 random 2-fold splits (split seeds 0..9).  Output: ../results/headroom_population.csv (long format).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np, pandas as pd
from run_real import load
from civ import LEARNERS, COLS

SEEDS = range(10)
DS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
rows = []
for name in DS:
    Y, F, X = load(name)
    Zfull = F[:, None] if X is None else np.column_stack([F, X])
    ls = ["lin_f", "iso_f", "gbm_f"] + (["lin_fX", "gbm_fX"] if X is not None else [])
    for seed in SEEDS:
        perm = np.random.default_rng(seed).permutation(len(Y)); half = [perm[::2], perm[1::2]]
        for L in ls:
            m = np.empty(len(Y))
            for a, b in [(0, 1), (1, 0)]:
                c = COLS[L]; Zc = Zfull if c is None else Zfull[:, c]
                mdl = LEARNERS[L]()
                if L.startswith("gbm"): mdl.kw.update(max_iter=200, min_samples_leaf=50)
                mdl.fit(Zc[half[a]], Y[half[a]]); m[half[b]] = mdl.predict(Zc[half[b]])
            for rho in [0.0, 1.0]:
                v = Y.var() - np.cov(Y, m)[0, 1] ** 2 / ((1 + rho) * m.var())
                rows.append(dict(dataset=name, split_seed=seed, method="cf_" + L, rho=rho, nvar=v))
        for rho in [0.0, 1.0]:   # reference: PPI++ with the exact full-pool affine fit (no cross-fitting)
            b = np.cov(Y, F)[0, 1] / F.var(); m = b * F
            rows.append(dict(dataset=name, split_seed=seed, method="ppi++", rho=rho, nvar=Y.var() - np.cov(Y, m)[0, 1] ** 2 / ((1 + rho) * m.var())))
        rows.append(dict(dataset=name, split_seed=seed, method="classical", rho=0.0, nvar=Y.var()))
        rows.append(dict(dataset=name, split_seed=seed, method="ppi", rho=0.0, nvar=(Y - F).var()))
df = pd.DataFrame(rows)
base = df[df.method == "ppi++"].set_index(["dataset", "split_seed", "rho"])["nvar"]
df["base"] = [base.get((d, s, r), base.get((d, s, 0.0))) for d, s, r in zip(df.dataset, df.split_seed, df.rho)]
df["width_ratio"] = np.sqrt(df.nvar / df.base)
out = df.groupby(["dataset", "method", "rho"]).agg(width_ratio=("width_ratio", "mean"), width_ratio_sd_splits=("width_ratio", "std")).reset_index()
out.to_csv("../results/headroom_population.csv", index=False)
pd.set_option("display.width", 200)
print(out.pivot_table(index="dataset", columns="method", values="width_ratio").loc[:, lambda d: d.columns.str.startswith("cf_")].round(4))
