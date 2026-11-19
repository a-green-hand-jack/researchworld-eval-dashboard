"""Parameter-free first-order budget and out-of-sample test of the budget-vs-z fit (paper-repo request #11).

(a) k_hat = ceil(lin_est): the smallest k whose k largest per-comparison first-order effects on theta_a - theta_b (cells taken in decreasing gain with their exact
    multiplicities, at the base fit) sum to the gap -- no parameter, no refit. Reported with k_hat / k_verified per claim and its distribution per dataset.
(b) Out-of-sample: log k = a + b log z is fitted on the NBA seasons ONLY (c2 claims, verified budget >= 1, z > 0; seasons are the bootstrap clusters) and used to
    predict the log budgets of Arena (new claim set), MT-Bench human / GPT-4 and NBA pooled with NO dataset intercept; the error log k - log k_pred has bias
    (mean), RMSE and a season-cluster bootstrap interval; the same errors for k_hat (log k - log k_hat).
(c) Collinearity of the regressors of M4: correlations of log z, log snr, log n_pair (pairs of the claim sample, per dataset and pooled) and variance inflation factors.
Writes results/s5_khat.csv (claim level), results/s5_oos_summary.csv, results/s5_collinearity.csv.   Usage: python code/s5_oos.py [--B 2000]"""
import argparse
import os

import numpy as np
import pandas as pd

from btlib import prov
from s3_models import prep

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
TARGETS = ["arena55k", "mt_human", "mt_gpt4", "nba_all"]


def claims():
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    d = d[d.claim.str.startswith("c2") & (d.gap > 1e-9) & (d.budget >= 1) & (d.z > 0) & d.flipped].copy()
    d["dataset"] = np.where(d.season.notna(), "nba_seasons", d.unit)
    d = d[d.dataset.isin(TARGETS + ["nba_seasons"])]
    d["k_hat"] = np.ceil(d.lin_est.clip(lower=1))
    d["log_k"], d["log_z"], d["log_khat"] = np.log(d.budget), np.log(d.z), np.log(d.k_hat)
    d["cluster"] = np.where(d.season.notna(), d.season.fillna(0).astype(int).astype(str), d.unit + ":" + d.claim)
    return d.reset_index(drop=True)


def fit_line(x, y):
    X = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(X, y, rcond=None)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=2000)
    a = ap.parse_args()
    d = claims()
    d["khat_over_k"] = d.k_hat / d.budget
    d[["unit", "dataset", "claim", "a", "b", "gap", "z", "lin_est", "k_hat", "budget", "khat_over_k", "season"]].to_csv(
        f"{OUT}/s5_khat.csv", index=False, float_format="%.6g")
    nba = d[d.dataset == "nba_seasons"]
    b0 = fit_line(nba.log_z.values, nba.log_k.values)
    groups = [np.asarray(v) for v in nba.groupby("cluster").indices.values()]
    rng = np.random.default_rng(31)
    boots = []
    for _ in range(a.B):
        idx = np.concatenate([groups[k] for k in rng.integers(0, len(groups), len(groups))])
        boots.append(fit_line(nba.log_z.values[idx], nba.log_k.values[idx]))
    boots = np.array(boots)
    rows = []
    for ds in ["nba_seasons"] + TARGETS:
        s = d[d.dataset == ds]
        if not len(s):
            continue
        pred = b0[0] + b0[1] * s.log_z.values
        e_z = s.log_k.values - pred
        e_h = s.log_k.values - s.log_khat.values
        # target claims resampled (single claims; NBA seasons: whole seasons); the NBA-season fit is resampled by season
        if ds == "nba_seasons":
            tg = groups
        else:
            tg = [np.array([i]) for i in range(len(s))]
        be_z, be_h = [], []
        for bi in range(min(a.B, len(boots))):
            idx = np.concatenate([tg[k] for k in rng.integers(0, len(tg), len(tg))])
            pz = boots[bi, 0] + boots[bi, 1] * s.log_z.values[idx]
            be_z.append(np.mean(s.log_k.values[idx] - pz))
            be_h.append(np.mean(e_h[idx]))
        rows.append(dict(dataset=ds, n_claims=len(s), fit="NBA-seasons log k = a + b log z", a=b0[0], b=b0[1],
                         bias_logk_z=e_z.mean(), bias_z_lo=np.percentile(be_z, 2.5), bias_z_hi=np.percentile(be_z, 97.5), rmse_logk_z=np.sqrt(np.mean(e_z ** 2)),
                         sd_logk_z=e_z.std(ddof=1) if len(s) > 1 else np.nan, bias_logk_khat=e_h.mean(),
                         bias_khat_lo=np.percentile(be_h, 2.5), bias_khat_hi=np.percentile(be_h, 97.5), rmse_logk_khat=np.sqrt(np.mean(e_h ** 2)),
                         sd_logk_khat=e_h.std(ddof=1) if len(s) > 1 else np.nan, median_khat_over_k=np.median(s.khat_over_k),
                         share_khat_within_2x=float(np.mean((s.khat_over_k >= 0.5) & (s.khat_over_k <= 2))),
                         slope_boot_lo=np.percentile(boots[:, 1], 2.5), slope_boot_hi=np.percentile(boots[:, 1], 97.5)))
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_oos_summary.csv", index=False, float_format="%.5g")
    # (c) collinearity within the M4 sample
    m = prep()
    cols = ["log_z", "log_snr", "log_n_pair_involving"]
    cr = []
    for ds, s in list(m.groupby("dataset")) + [("pooled", m)]:
        if len(s) < 8:
            continue
        C = s[cols].corr()
        X = s[cols].values
        vif = {}
        for j, cname in enumerate(cols):
            others = np.delete(X, j, 1)
            Z = np.column_stack([np.ones(len(s)), others])
            res = X[:, j] - Z @ np.linalg.lstsq(Z, X[:, j], rcond=None)[0]
            vif[cname] = 1.0 / max(res.var() / X[:, j].var(), 1e-12)
        cr.append(dict(dataset=ds, n_claims=len(s), r_logz_logsnr=C.loc["log_z", "log_snr"], r_logz_lognpair=C.loc["log_z", "log_n_pair_involving"],
                       r_logsnr_lognpair=C.loc["log_snr", "log_n_pair_involving"], vif_logz=vif["log_z"], vif_logsnr=vif["log_snr"],
                       vif_lognpair=vif["log_n_pair_involving"]))
    pd.DataFrame(cr).to_csv(f"{OUT}/s5_collinearity.csv", index=False, float_format="%.4g")
    prov.write_meta(f"{OUT}/s5_oos.meta.json", script="code/s5_oos.py", B=a.B)
    print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(cr).round(3).to_string())


if __name__ == "__main__":
    main()
