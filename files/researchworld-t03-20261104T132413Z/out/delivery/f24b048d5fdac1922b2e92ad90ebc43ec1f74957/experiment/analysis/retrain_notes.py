"""Retrain standard: number of pairs behind each number and the estimator error of the d>16 (German) retrain explanations.

usage: python3 analysis/retrain_notes.py [raw_dir] [out_dir]
For every cell with a retrain stage: K retrains, N instances, K(K-1)/2 retrain pairs per instance (N*K(K-1)/2 pairs, which are
NOT independent: they share retrains, so the instance is the independent unit, K=5 retrains is the effective sample of models).
Retrain explanations are exact for d <= 16 and a single Kernel run at 10000 coalitions for German (d = 20).  For those the
estimator error is an ESTIMATE, not a measurement: the run-to-run variance of the Kernel runs of the same cell
(R runs, relative to ||phi*||^2) is fitted as a power law in the budget over the three largest budgets and extrapolated to 10000.
A retrain pair difference then contains 2*s^2(10000) of estimator variance, so
  rms_pair_obs^2 = rms_pair_true^2 + 2*s^2   =>   rms_pair_true = sqrt(max(rms_pair_obs^2 - 2*s^2, 0)).
All "rms" are root-mean-squares over instances of ||phi_k - phi_k'|| / ||phi*||.
Writes tables/retrain_notes.csv.
"""
import glob, os, sys
import numpy as np, pandas as pd

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rows = []
for fr in sorted(glob.glob(f"{raw}/*__retrain.npz")):
    cell = os.path.basename(fr).rsplit("__", 1)[0]; ds, model = cell.split("__")
    P = np.load(fr)["phi"]; K, N, d = P.shape
    fref = f"{raw}/{cell}__ref.npz"
    if not os.path.exists(fref):
        continue
    ref = np.load(fref)["ref"]; nr2 = (ref ** 2).sum(1)
    D2 = np.array([((P[a] - P[b]) ** 2).sum(1) / nr2 for a in range(K) for b in range(a + 1, K)])   # (pairs, N)
    r = dict(dataset=ds, model=model, d=d, K=K, n_inst=N, pairs_per_inst=K * (K - 1) // 2, n_pairs_total=D2.size,
             rms_pair_obs=float(np.sqrt(D2.mean())), retrain_explanations="exact (d<=16)" if d <= 16 else "single Kernel run, 10000 coalitions")
    if d > 16 and os.path.exists(f"{raw}/{cell}__kernel.npz"):
        z = np.load(f"{raw}/{cell}__kernel.npz"); phi = z["phi"]; bud = z["budgets"].astype(float); R = phi.shape[2]
        s2 = np.array([(R / (R - 1)) * (((phi[:, b] - phi[:, b].mean(1, keepdims=True)) ** 2).sum(2).mean(1) / nr2).mean() for b in range(len(bud))])
        sl, ic = np.polyfit(np.log(bud[-3:]), np.log(s2[-3:]), 1)
        s2_10k = float(np.exp(ic + sl * np.log(10000.0)))
        r.update(est_var_exponent=sl, est_rms_err_single_run_10000=float(np.sqrt(s2_10k)),
                 rms_pair_obs_minus_noise=float(np.sqrt(max(D2.mean() - 2 * s2_10k, 0))),
                 noise_share_of_pair_variance=float(min(2 * s2_10k / D2.mean(), 1)))
    rows.append(r)
pd.DataFrame(rows).to_csv(f"{out}/retrain_notes.csv", index=False)
print(len(rows), "cells")
