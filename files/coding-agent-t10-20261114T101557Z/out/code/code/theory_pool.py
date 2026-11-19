"""Pool-level theoretical quantities for each real-data configuration.

For a pool (Y, Z) with Z = f(X) or (f(X), X), define
    m(Z) = E[Y|Z]            (estimated by 5-fold cross-fitted gradient boosting on the full pool)
    L(Z) = best linear predictor of Y from Z (OLS on the full pool)
    a    = n / (n + N)
and the asymptotic variances (times n) of the estimators in the paper:
    n V_eff   = E(Y - m)^2 + a Var(m)          (efficient bound for information Z)
    n V_PPI++ = E(Y - L)^2 + a Var(L)          (PPI++ with linear calibrator)
    n V_class = Var(Y)                          (labeled-only)
    Delta     = E(m - L)^2 = Var(m - L)        (linear misfit; the gain in n-variance is (1-a) Delta)
Predicted CI-width ratios (flexible / PPI++) at the efficient bound: sqrt(V_eff / V_PPI++).

Output: /work/results/theory_pool.csv
"""
import os
import sys
os.environ.setdefault("OMP_NUM_THREADS", "8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold

import ppi_flex as P
from run_real import CONFIGS, get_pool


def pool_m(Z, Y, seed=0):
    m = np.empty(len(Y))
    for tr, te in KFold(5, shuffle=True, random_state=seed).split(Z):
        g = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.1, max_iter=400,
                                          min_samples_leaf=100, random_state=seed)
        g.fit(Z[tr], Y[tr])
        m[te] = g.predict(Z[te])
    return m


def main():
    rows = []
    for name, regime in CONFIGS:
        Y, f, X = get_pool(name, regime)
        Z = f.reshape(len(f), -1) if X is None else np.column_stack([f, X])
        m = pool_m(Z, Y)
        L = LinearRegression().fit(Z, Y).predict(Z)
        Delta = np.mean((m - L) ** 2)
        VarY = Y.var()
        for ratio in [1, 4, 16]:
            a = 1.0 / (1.0 + ratio)
            nVeff = np.mean((Y - m) ** 2) + a * m.var()
            nVpp = np.mean((Y - L) ** 2) + a * L.var()
            rows.append(dict(
                dataset=name, regime=regime, ratio=ratio, a=a, M=len(Y),
                VarY=VarY, E_res_m=np.mean((Y - m) ** 2), E_res_L=np.mean((Y - L) ** 2),
                Var_m=m.var(), Var_L=L.var(), Delta=Delta,
                nV_class=VarY, nV_ppipp=nVpp, nV_eff=nVeff,
                width_ratio_ppipp_vs_class=np.sqrt(nVpp / VarY),
                width_ratio_eff_vs_ppipp=np.sqrt(nVeff / nVpp),
                gain_fraction_var=1 - nVeff / nVpp,
                R2_linear=1 - np.mean((Y - L) ** 2) / VarY,
                R2_nonlinear=1 - np.mean((Y - m) ** 2) / VarY,
            ))
        print(name, regime, f"Delta={Delta:.4g}", f"R2lin={rows[-1]['R2_linear']:.3f}",
              f"R2nl={rows[-1]['R2_nonlinear']:.3f}", flush=True)
    df = pd.DataFrame(rows)
    out = "/work/results/theory_pool.csv"
    df.to_csv(out, index=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
