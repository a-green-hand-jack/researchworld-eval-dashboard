"""Stage 2 (POST HOC, exploratory): model-level regressions shrunk toward the design-unbiased mean.

Motivated by the stage-1 result (results/main.csv): RS-Learn (ridge from coreset outcomes to full accuracy,
trained over source models) is best under interpolation but breaks under extrapolation because ridge shrinks
toward the *source* mean accuracy.  Variants written down before running this script:
  rsres_<design> : y_hat = b_t + ridge(y_{t,C}),   ridge trained on source models to predict (ybar_full - b),
                   where b is the (Hajek) coreset mean => shrinkage toward the design-unbiased estimate b.
  rslearn_<design>: RS-Learn (shrink toward source mean) on the same coreset, for a like-for-like comparison.
  cal1d_<design> : y_hat = alpha + beta * b_t, (alpha, beta) fit by OLS across source models (1-D calibration).
Designs: uniform, strat (same coresets as stage 1 through the shared RNG recipe).  The Neyman design is not
used here because it needs the (expensive) MIRT fit.
"""
import os, sys, zlib, argparse
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from methods import design_uniform, design_strat, hajek_mean
from sklearn.linear_model import RidgeCV, LinearRegression


def rng_for(seed, n, tag):
    return np.random.default_rng([seed, n, zlib.crc32(tag.encode()) & 0xFFFFFF])


def run_task(args):
    name, kind, seed, budgets = args
    S = load_scores(name)
    src, tgt = make_split(name, S, kind, seed)
    Ssrc, Stgt = S[src], S[tgt]; true = Stgt.mean(1); full_src = Ssrc.mean(1); N = S.shape[1]
    rows = []
    def rec(method, n, pred):
        rows.append(dict(dataset=name, split=kind, seed=seed, n=n, method=method, n_src=len(src), n_tgt=len(tgt), N=N,
                         **metrics(pred, true)))
    for n in budgets:
        if n >= N: continue
        for dname, fn in (("uniform", design_uniform), ("strat", design_strat)):
            idx, pi = fn(Ssrc, n, rng_for(seed, n, f"{dname}-0.3-2")); pis = pi[idx]
            Xs, Yt = Ssrc[:, idx], Stgt[:, idx]
            b_src, b_tgt = hajek_mean(Xs, pis), hajek_mean(Yt, pis)
            if dname == "uniform":
                rec("chk_random", n, b_tgt)
                rec("chk_rs_learn", n, RidgeCV().fit(Xs, full_src).predict(Yt))
            else:
                rec("rslearn_strat", n, RidgeCV().fit(Xs, full_src).predict(Yt))
            rg = RidgeCV().fit(Xs, full_src - b_src)
            rec(f"rsres_{dname}", n, b_tgt + rg.predict(Yt))
            # guard (added after the first stage-2 pass showed rsres/cal1d still degrade under extrapolation):
            # use rsres only if the target's coreset mean lies within the range of the source models' coreset means,
            # otherwise fall back to the design-unbiased mean b_t.  The rule has no tuned constant.
            inr = (b_tgt >= b_src.min()) & (b_tgt <= b_src.max())
            rec(f"guard_{dname}", n, np.where(inr, b_tgt + rg.predict(Yt), b_tgt))
            lr = LinearRegression().fit(b_src[:, None], full_src)
            rec(f"cal1d_{dname}", n, lr.predict(b_tgt[:, None]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30); ap.add_argument("--procs", type=int, default=12)
    ap.add_argument("--out", default="results/stage2.csv")
    a = ap.parse_args()
    tasks = [(d, k, s, [10, 25, 50, 100]) for d in ALL for k in ("interp", "extrap", "org") if not (k == "org" and d not in OPENLLM)
             for s in range(a.seeds)]
    with Pool(a.procs) as p:
        parts = p.map(run_task, tasks, chunksize=4)
    pd.concat(parts, ignore_index=True).to_csv(a.out, index=False)
    print("done", len(tasks))
