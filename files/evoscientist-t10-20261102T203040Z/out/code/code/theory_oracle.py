"""Population-level (large-sample) quantities per dataset, treating each pool as the population.

For n labeled, N unlabeled, rho = n/(n+N), the asymptotic variance (times n) of the best estimator in a
class that corrects with a function g of the available inputs is
    V(g) = sigma_Y^2 - (1 - rho) * Var(m_g),       m_g = L2-projection of Y onto the class.
  classical : Var(m) = 0
  PPI++     : Var(m) = R2_affine * sigma_Y^2          (best affine function of f)
  calibrated: Var(m) = Var(E[Y|f])                    (any function of f)
  with X    : Var(m) = Var(E[Y|f,X])
R2 of nonparametric classes are estimated out-of-sample (5-fold CV on the pool), so they are not inflated by
in-sample fitting.  Output: results/oracle.csv
"""
import numpy as np, pandas as pd, os
from sklearn.model_selection import KFold
from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingRegressor

os.makedirs("results", exist_ok=True)
rng = np.random.default_rng(0)
DS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]


def cv_R2(kind, F, y, K=5, seed=0):
    pred = np.zeros(len(y))
    for tr, te in KFold(K, shuffle=True, random_state=seed).split(F):
        if kind == "iso":
            m = IsotonicRegression(out_of_bounds="clip", increasing="auto").fit(F[tr, 0], y[tr]); pred[te] = m.predict(F[te, 0])
        elif kind == "hgb":
            m = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=16).fit(F[tr][:, [0]], y[tr]); pred[te] = m.predict(F[te][:, [0]])
        elif kind == "hgbX":
            m = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=16).fit(F[tr], y[tr]); pred[te] = m.predict(F[te])
        elif kind == "affine":
            A = np.column_stack([np.ones(len(tr)), F[tr, 0]]); b = np.linalg.lstsq(A, y[tr], rcond=None)[0]
            pred[te] = b[0] + b[1] * F[te, 0]
    return 1 - np.mean((y - pred) ** 2) / np.var(y)


rows = []
for ds in DS:
    d = np.load(f"data/{ds}.npz"); Y, f = d["Y"].astype(float), d["Yhat"].astype(float)
    F = f[:, None] if "X" not in d.files else np.column_stack([f, d["X"][:, [j for j in range(d["X"].shape[1]) if len(np.unique(d["X"][:, j])) > 1]]])
    if len(Y) > 100000:  # subsample for speed
        ii = rng.choice(len(Y), 100000, replace=False); Y, F = Y[ii], F[ii]
    r2 = {k: cv_R2(k, F, Y) for k in ["affine", "iso", "hgb"] + (["hgbX"] if F.shape[1] > 1 else [])}
    r2["pearson_sq"] = np.corrcoef(F[:, 0], Y)[0, 1] ** 2
    rows.append(dict(dataset=ds, pool=len(Y), n_unique_f=len(np.unique(F[:, 0])), **{f"R2_{k}": v for k, v in r2.items()}))
    print(rows[-1], flush=True)
df = pd.DataFrame(rows)
# implied asymptotic width ratio calibrated/PPI++ and PPI++/classical for several N/n
out = []
for _, r in df.iterrows():
    for ratio in [1, 5, 25, 1e6]:  # N/n
        rho = 1 / (1 + ratio)
        best = max(r.R2_iso, r.R2_hgb, r.R2_affine)
        for name, R2 in [("affine", r.R2_affine), ("best_f_only", best)] + ([("with_X", max(best, r.R2_hgbX))] if "R2_hgbX" in r and not np.isnan(r.R2_hgbX) else []):
            out.append(dict(dataset=r.dataset, N_over_n=ratio, cls=name, width_ratio_vs_classical=np.sqrt(1 - (1 - rho) * R2)))
o = pd.DataFrame(out).pivot_table(index=["dataset", "N_over_n"], columns="cls", values="width_ratio_vs_classical").reset_index()
o["cal_vs_ppi++"] = o["best_f_only"] / o["affine"]
o["withX_vs_ppi++"] = o["with_X"] / o["affine"] if "with_X" in o else np.nan
df.to_csv("results/oracle_R2.csv", index=False); o.to_csv("results/oracle_width_ratios.csv", index=False)
print(df.round(4).to_string()); print(o.round(4).to_string())
