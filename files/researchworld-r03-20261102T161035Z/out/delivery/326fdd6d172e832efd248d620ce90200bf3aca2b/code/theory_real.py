"""Real-data tie-in of the factor-model theory. For each dataset fit the factor model on ALL models (descriptive, in-sample; rank/noise floor by
held-out-cell CV on a wide grid), report spectrum / effective rank / noise floor, and the theory curve
  MSE_z(k) = mean_{S random of size k, j not in S} [ psi_j + l_j' (I + L_S' Psi_S^-1 L_S)^-1 l_j ]   (and psi_bar (1 + r/k))
in the units of the z-RMSE of curves.csv (sd of the fitted data).  usage: theory_real.py OUT_DIR"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from bench import *
D = "/hutian/repo/data/"; out = sys.argv[1]
sets = {"mteb": (dense_core(pd.read_csv(D + "mteb_matrix.csv", index_col=0), 0.95), (2, 4, 8, 12, 16, 24), (0.15, 0.3, 0.5, 0.8), [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128]),
        "olb": (pd.read_csv(D + "olb_matrix.csv", index_col=0), (1, 2, 3), (0.05, 0.15, 0.3), [1, 2, 3, 4, 5]),
        "helm": (pd.read_csv(D + "helm_lite_matrix.csv", index_col=0), (1, 2, 3, 4), (0.05, 0.15, 0.3), [1, 2, 3, 4, 5, 6, 7, 8, 9])}
spec, par, curve = [], [], []
rng = np.random.default_rng(0)
for name, (X, ranks, psis, ks) in sets.items():
    V = X.values; N = V.shape[1]
    r, pm = fa_cv_rank(V, ranks=ranks, psis=psis, seed=0, iters=60)
    fa = FA(r, iters=100, seed=0, psi_min=pm).fit(V); Z = fa.impute(V); Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-9)
    ev = np.sort(np.linalg.eigvalsh(np.corrcoef(Z.T)))[::-1]; p = ev / ev.sum()
    comm = (fa.L ** 2).sum(1); psi = fa.psi
    par.append((name, V.shape[0], N, r, pm, float(np.mean(psi)), float(np.median(psi)), float(comm.mean()), float(1 / (p ** 2).sum()), float(p[:r].sum()),
                float(ev[0] / ev.sum()), float(p[:3].sum())))
    for i, e in enumerate(p[:min(len(p), 30)]): spec.append((name, i + 1, float(e)))
    for k in ks:
        if k >= N - 1: continue
        vals = []
        for _ in range(100):
            S = rng.choice(N, k, replace=False); t = np.setdiff1d(np.arange(N), S)
            P = np.linalg.inv(np.eye(r) + (fa.L[S].T / psi[S]) @ fa.L[S])
            vals.append(np.mean(psi[t] + np.einsum("jr,rs,js->j", fa.L[t], P, fa.L[t])))
        curve.append((name, k, float(np.sqrt(np.mean(vals))), float(np.sqrt(np.mean(psi) * (1 + r / k)))))
    print(name, "r", r, "psi_min", pm, "mean psi", psi.mean().round(3), "eff rank", round(1 / (p ** 2).sum(), 2), flush=True)
pd.DataFrame(par, columns="data n_models n_bench fa_rank psi_min psi_mean psi_median communality_mean eff_rank_participation var_top_r var_top1 var_top3".split()).to_csv(os.path.join(out, "theory_real_params.csv"), index=False)
pd.DataFrame(spec, columns="data component frac_variance".split()).to_csv(os.path.join(out, "spectrum.csv"), index=False)
pd.DataFrame(curve, columns="data k theory_zrmse_fitted_FA_random_S approx_sqrt_psi_1_plus_r_over_k".split()).to_csv(os.path.join(out, "theory_real_curve.csv"), index=False)
