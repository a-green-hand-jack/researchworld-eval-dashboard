"""C4 (H1'): does one coordinate Z organise the normalised error across graph families?  python scripts/analyze_c4.py
Reads results/summary/e4.csv (REG-L rows); writes results/summary/c4_variance.csv, c4_bias_loo.csv, c4_bias_pred.csv (the held-out prediction of every cell).
Nothing is fitted per graph:
 (A) variance: sd(tau_hat) sqrt(n) / sigma_tot  against  Z0 + Z1 = 1 / s_g  (identity line, no parameters), s_g^2 = p(1-p)/d,
     for three degree summaries d (mean, harmonic mean, d_eff = mean for Bernoulli); linear response (correctly specified), sigma_tot > 0.
 (B) bias: bias/scale against (log Z1, log Z0) (or one of them, or (log d, p) as baselines) with a cubic polynomial fitted on all families but one, predicted for the held-out family
     (leave-one-family-out); the same predictor built from (log d, p) is the baseline; held-out R^2 pooled over families and Spearman."""
import itertools
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline

d = pd.read_csv("results/summary/e4.csv")
d = d[d.est == "REG-L"].copy()
d["family"] = d["graph.kind"]
d["p"] = d["design.p"]
d["sig_tot"] = np.sqrt(d["out.sigma"].fillna(0) ** 2 + d["out.sigma_alpha"].fillna(0) ** 2)
d["resp"] = np.where(d["out.kappa"] == 0, "linear", np.where(d["out.shape"] == "thresh", "thresh", "concave"))
STAT = {"mean": "d_mean", "harmonic": "d_hm"}
for k, c in STAT.items():
    s = np.sqrt(d.p * (1 - d.p) / d[c])
    d[f"Z1_{k}"], d[f"Z0_{k}"] = (1 - d.p) / s, d.p / s

# ---- (A) variance
rows = []
lin = d[(d.resp == "linear")].copy()
y = np.log(lin.sd * np.sqrt(lin.n_eff) / lin.sig_tot)
for k in STAT:
    x = np.log(lin[f"Z1_{k}"] + lin[f"Z0_{k}"])
    for fam, idx in [("all", lin.index)] + [(f, lin.index[lin.family == f]) for f in sorted(lin.family.unique())]:
        e = y[idx] - x[idx]
        sst = ((y[idx] - y[idx].mean()) ** 2).sum()
        rows.append(dict(stat=k, family=fam, n_cells=len(idx), mean_log_ratio=e.mean(), median_abs_log_ratio=np.abs(e).median(),
                         max_abs_log_ratio=np.abs(e).max(), r2_identity=1 - (e ** 2).sum() / sst if sst > 0 else np.nan,
                         spearman=spearmanr(y[idx], x[idx])[0] if len(idx) > 2 else np.nan))
va = pd.DataFrame(rows)
va.to_csv("results/summary/c4_variance.csv", index=False)
print(va.round(3).to_string())

# ---- (B) bias, leave-one-family-out
def feats(df, how):
    if how == "d,p":
        return np.c_[np.log(df.d_mean), df.p]
    if how == "dhm,p":
        return np.c_[np.log(df.d_hm), df.p]
    if how in ("Z1:harmonic", "Z0:harmonic"):
        return np.c_[np.log(df[f"{how[:2]}_harmonic"])]
    k = how.split(":")[1]
    return np.c_[np.log(df[f"Z1_{k}"]), np.log(df[f"Z0_{k}"])]

def model():
    return make_pipeline(StandardScaler(), PolynomialFeatures(3), Ridge(alpha=1e-3))

rows = []
cells = []
CELL = ["graph.kind", "graph.n", "graph.d", "graph.q", "design.p", "out.kappa", "out.shape", "out.sigma", "out.sigma_alpha"]
fams = sorted(d.family.unique())
for resp in ["thresh", "concave"]:
    r = d[d.resp == resp]
    for how in ["Z:mean", "Z:harmonic", "Z1:harmonic", "Z0:harmonic", "d,p", "dhm,p"]:
        pred = pd.Series(np.nan, index=r.index)
        for f in fams:
            tr, te = r[r.family != f], r[r.family == f]
            m = model().fit(feats(tr, how), tr.bias_norm)
            pred[te.index] = m.predict(feats(te, how))
        res = r.bias_norm - pred
        cells.append(r[CELL + ["bias_norm", "bias_norm_se", "d_hm", "d_mean"]].assign(resp=resp, predictor=how, pred=pred))
        sst = ((r.bias_norm - r.bias_norm.mean()) ** 2).sum()
        row = dict(resp=resp, predictor=how, r2_heldout=1 - (res ** 2).sum() / sst, spearman=spearmanr(r.bias_norm, pred)[0],
                   rmse_pred=float(np.sqrt((res ** 2).mean())), sd_bias_norm=float(r.bias_norm.std()))
        for f in fams:
            rr = res[r.family == f]
            row[f"rmse_{f}"] = float(np.sqrt((rr ** 2).mean()))
        rows.append(row)
bi = pd.DataFrame(rows)
bi.to_csv("results/summary/c4_bias_loo.csv", index=False)
print(bi.round(3).to_string())
pd.concat(cells)[["resp", "predictor"] + CELL + ["bias_norm", "bias_norm_se", "pred", "d_hm", "d_mean"]].to_csv("results/summary/c4_bias_pred.csv", index=False)
