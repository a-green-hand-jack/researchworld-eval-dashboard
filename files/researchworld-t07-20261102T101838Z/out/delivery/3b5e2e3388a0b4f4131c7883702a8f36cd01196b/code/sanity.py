"""Data sanity table and estimator sanity checks. usage: python sanity.py OUTDIR"""
import sys, os, numpy as np, pandas as pd
from bpx import data, methods

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rows, chk = [], []
for b in data.BENCHMARKS:
    S0, names0, _ = data.load(b, dedup=False)
    S, names, info = data.load(b)
    N = S.shape[1]; sc = S.mean(1); q = S.mean(0)
    # near-duplicates: pairs of (deduplicated) models agreeing on >= 99% of items
    X = S.astype(np.float32); agree = (X @ X.T + (1 - X) @ (1 - X).T) / N
    np.fill_diagonal(agree, 0)
    near = int((agree >= 0.99).sum() // 2)
    rows.append(dict(benchmark=b, family="openllm" if b in data.OPENLLM else "helm", models_raw=info["M_raw"], models_dedup=info["M"],
                     exact_duplicate_rows=info["M_raw"] - info["M"], items=N, const_items=int(((q == 0) | (q == 1)).sum()),
                     mean_acc=sc.mean(), sd_acc=sc.std(), min_acc=sc.min(), max_acc=sc.max(), near_dup_pairs_ge99=near,
                     n_cap_quarter=N // 4))
    # checks: n = N exact; random-subset error vs analytic finite-population SE
    src = methods.Source(S[: S.shape[0] // 2], irt_d=1)
    T = S[S.shape[0] // 2:].astype(np.float32); true = T.mean(1)
    idx, wt = methods.sel_random(src, N, np.random.default_rng(0))
    err_full = np.abs(methods.est_mean(src, idx, wt, T[:, idx], None) - true).max()
    for n in (10, 50, 100):
        if n > N // 4: continue
        errs = []
        for s in range(300):
            idx, wt = methods.sel_random(src, n, np.random.default_rng(s))
            errs.append(T[:, idx].mean(1) - true)
        errs = np.array(errs)
        se_an = np.sqrt(true * (1 - true) / n * (N - n) / (N - 1))
        chk.append(dict(benchmark=b, n=n, empirical_rmse=np.sqrt((errs ** 2).mean()), analytic_rmse=np.sqrt((se_an ** 2).mean()),
                        mean_bias=errs.mean(), max_abs_err_at_n_equals_N=err_full))
pd.DataFrame(rows).to_csv(os.path.join(out, "data_summary.csv"), index=False)
pd.DataFrame(chk).to_csv(os.path.join(out, "sanity_random_subset.csv"), index=False)
print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(chk).round(4).to_string())
