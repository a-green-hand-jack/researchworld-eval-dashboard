"""Exploratory: does calibration help for OLS coefficients? (large n, to see the asymptotic gap)"""
import numpy as np, sys
sys.path.insert(0, "code")
from ppi_py import ppi_ols_ci, classical_ols_ci
from ppi_lib import crossfit_calibrated
rng = np.random.default_rng(1)
for ds in ["census_income", "census_healthcare", "census_education"]:
    d = np.load(f"data/{ds}.npz"); Y, f, X = d["Y"].astype(float), d["Yhat"], d["X"].astype(float)
    keep = [j for j in range(X.shape[1]) if len(np.unique(X[:, j])) > 1]; X = X[:, keep]
    Xd = np.column_stack([np.ones(len(Y)), X])
    theta_true = np.linalg.lstsq(Xd, Y, rcond=None)[0]
    n, N = 3000, 30000
    res = {}
    for rep in range(3):
        idx = rng.choice(len(Y), n + N, replace=True); L, U = idx[:n], idx[n:]
        for name in ["classical", "ppi++", "cal_hgbX", "cal_lin"]:
            if name == "classical":
                lo, hi = classical_ols_ci(Xd[L], Y[L], alpha=0.05)
            elif name == "ppi++":
                lo, hi = ppi_ols_ci(Xd[L], Y[L], f[L], Xd[U], f[U], alpha=0.05)
            else:
                FL, FU = np.column_stack([f[L], X[L]]), np.column_stack([f[U], X[U]])
                if name == "cal_hgbX":
                    gL, gU = crossfit_calibrated("hgbX", Y[L], FL, FU, rng=rng)
                else:  # linear in (f,X) cross-fitted
                    from sklearn.linear_model import LinearRegression
                    gL = np.zeros(n); gU = np.zeros(len(U)); folds = np.array_split(rng.permutation(n), 5)
                    for k in folds:
                        tr = np.setdiff1d(np.arange(n), k); m = LinearRegression().fit(FL[tr], Y[L][tr])
                        gL[k] = m.predict(FL[k]); gU += m.predict(FU) / 5
                lo, hi = ppi_ols_ci(Xd[L], Y[L], gL, Xd[U], gU, alpha=0.05)
            res.setdefault(name, []).append(np.asarray(hi) - np.asarray(lo))
    print(ds, "kept X cols", keep)
    cl = np.mean(res["classical"], 0)
    for k, v in res.items():
        print(f"  {k:10s} width ratio vs classical per coef:", np.round(np.mean(v, 0) / cl, 3))
