"""Synthetic experiment (CPU only): controlled study of the selection gap and of the reporting methods.
Model: K configs, true accuracies mu_c = base + spread * z_c (z_c equally spaced in [-1,1]; spread=0 means all identical),
per-question Bernoulli outcomes with a Gaussian-copula correlation rho between configs (rho=0: independent; rho>0: shared
question difficulty, as for real prompts of the same model).
Reports bias of naive = E[max_c mean_c - mu_{c*}] and coverage of the 90% intervals.
Usage: python code/exp_synth.py REPS OUT_CSV
"""
import sys, os, time
import numpy as np, pandas as pd, multiprocessing as mp
from scipy.stats import norm
sys.path.insert(0, "code")
from selinf import *

REPS = int(sys.argv[1]); OUT = sys.argv[2]
GRID = [dict(K=K, n=n, spread=sp, rho=rho) for K in (2, 8, 32, 128) for n in (100, 400) for sp in (0.0, 0.02, 0.08)
        for rho in (0.0, 0.5)]
FUN = {"naive": naive, "holdout50": lambda S, r, a: holdout(S, r, a, 0.5), "boot_opt": boot_optimism,
       "maxT": maxT, "cond": conditional}


def gen(rng, K, n, spread, rho, base=0.6):
    z = np.linspace(-1, 1, K) if K > 1 else np.zeros(1)
    mu = np.clip(base + spread * z, 0.02, 0.98)
    common = rng.randn(n, 1); eps = rng.randn(n, K)
    G = np.sqrt(rho) * common + np.sqrt(1 - rho) * eps
    S = (norm.cdf(G) < mu[None, :]).astype(np.float32)  # marginal P(S=1)=mu exactly, copula-correlated
    return S, mu


def one(args):
    gi, rep = args; g = GRID[gi]
    rng = np.random.RandomState(10_000 * gi + rep)
    S, mu = gen(rng, **g); rows = []
    for nm, f in FUN.items():
        e, lo, hi, c = f(S, rng, 0.1)
        rows.append(dict(**g, rep=rep, method=nm, est=e, lo=lo, hi=hi, mu_sel=mu[c], mu_best=mu.max(), sel=c))
    return rows


if __name__ == "__main__":
    t0 = time.time(); jobs = [(gi, r) for gi in range(len(GRID)) for r in range(REPS)]; out = []
    with mp.Pool(min(24, os.cpu_count())) as p:
        for rows in p.imap_unordered(one, jobs, chunksize=16): out.extend(rows)
    df = pd.DataFrame(out); df.to_csv(OUT, index=False); print("saved", OUT, df.shape, round(time.time() - t0))
