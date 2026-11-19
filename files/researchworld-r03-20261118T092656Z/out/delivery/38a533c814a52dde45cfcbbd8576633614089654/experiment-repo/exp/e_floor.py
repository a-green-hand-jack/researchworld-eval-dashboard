"""Empirical floor: leave-one-benchmark-out prediction of each held-out model's scores from ALL its other observed
benchmarks (ridge-shrunk Gaussian conditional, shrinkage chosen on a held-out slice of the history). A model-agnostic
reference for what the full row can achieve; no k-benchmark design can beat it in expectation by more than estimation noise.
python exp/e_floor.py SETTING [--reps 3] -> results/SETTING/floor.csv (rows: rep, fold, model, mse, lam)"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
from settings import mteb_setting, llm_setting
from infer import Ctx, precision_floor_predict

ap = argparse.ArgumentParser(); ap.add_argument('setting'); ap.add_argument('--reps', type=int, default=3)
ap.add_argument('--nmin', type=int, default=0); ap.add_argument('--max_models', type=int, default=0); a = ap.parse_args()
LLM = a.setting in ('OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH')
s = llm_setting(a.setting) if LLM else mteb_setting(a.setting)
X, obs = s['X'], s['obs']; M, N = X.shape; dense = obs.all()
elig = np.where(obs.sum(1) >= (a.nmin or (3 if dense else 40)))[0]
rows = []
for rep in range(a.reps):
    rng = np.random.default_rng([rep, 4242])
    perm = rng.permutation(elig)
    if a.max_models: perm = perm[:a.max_models]
    for fi, te in enumerate(np.array_split(perm, 5)):
        tr = np.setdiff1d(np.arange(M), te)
        keep = np.where(obs[tr].sum(0) >= min(15, max(3, len(tr) // 4)))[0]
        h = rng.permutation(tr); nv = max(len(h) // 5, 5); va, pt = h[:nv], h[nv:]
        ctx = Ctx(X[np.ix_(pt, keep)], obs[np.ix_(pt, keep)], r=1)
        Zv = (X[np.ix_(va, keep)] - ctx.m) / ctx.sd
        best = None
        for lam in (0.02, 0.05, 0.1, 0.2, 0.5, 1.0):
            P = precision_floor_predict(ctx, lam, Zv, obs[np.ix_(va, keep)])
            e = np.nanmean((P - Zv) ** 2) if False else np.nanmean(np.where(obs[np.ix_(va, keep)], (P - Zv) ** 2, np.nan))
            if best is None or e < best[0]: best = (e, lam)
        lam = best[1]
        ctx = Ctx(X[np.ix_(tr, keep)], obs[np.ix_(tr, keep)], r=1)      # refit on the whole history
        Zt = (X[np.ix_(te, keep)] - ctx.m) / ctx.sd; Ot = obs[np.ix_(te, keep)]
        P = precision_floor_predict(ctx, lam, Zt, Ot)
        E2 = np.where(Ot, (P - Zt) ** 2, np.nan)
        for j, i in enumerate(te):
            if Ot[j].sum() > 1:
                rows.append(dict(rep=rep, fold=fi, model=int(i), mse=float(np.nanmean(E2[j])), lam=lam))
        print(a.setting, rep, fi, 'lam', lam, 'rmse', round(float(np.sqrt(np.nanmean(E2))), 3), flush=True)
os.makedirs(f"results/{a.setting}", exist_ok=True)
pd.DataFrame(rows).to_csv(f"results/{a.setting}/floor.csv", index=False)
