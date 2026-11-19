"""Unbiasedness / coverage / RMSE check of the sample mean vs the cross-fitted estimator (CF) with many independent
random subsets per (split). Usage: python -I run_cover.py [--workers 12]"""
import os, sys, time, pickle, argparse
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bplib import *
from run_main import split_models
from concurrent.futures import ProcessPoolExecutor, as_completed

M = 200; KS = [25, 100]


def task(args):
    bench, regime, rep, seed0 = args
    out = f'/work/results/raw_cover/{bench}_{regime}_{rep}.pkl'
    if os.path.exists(out):
        return out
    X, _ = load_bench(bench); n = X.shape[1]
    rng = np.random.default_rng(np.random.SeedSequence([seed0, 77, BENCHES.index(bench), ['iid', 'up50', 'up75'].index(regime), rep]))
    src, tgt = split_models(X, regime, rng)
    Xs, Xt = X[src], X[tgt]; true = Xt.mean(1)
    model = fit_irt(Xs, 4, maxiter=300)
    res = {}
    for k in KS:
        if k > n // 2:
            continue
        E = {e: np.zeros((M, len(tgt))) for e in ['mean', 'cf', 'plugin', 'pirt']}
        SE = {e: np.zeros((M, len(tgt))) for e in ['mean', 'cf']}
        for j in range(M):
            S, w = sel_random(Xs, k, rng); Y = Xt[:, S]
            b, c, v, R = cf_parts(Y, S, rng, n, model, return_resid=True)
            E['cf'][j] = b + c - true
            E['plugin'][j] = b - true
            E['pirt'][j] = est_pirt(Y, S, w, n, model) - true
            E['mean'][j] = Y.mean(1) - true
            SE['cf'][j] = np.sqrt((1 - k / n) * R.var(1, ddof=1) / k)
            SE['mean'][j] = np.sqrt((1 - k / n) * Y.var(1, ddof=1) / k)
        res[k] = dict(E=E, SE=SE)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pickle.dump(dict(res=res, true=true, n=n), open(out, 'wb'))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=12); ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--seed', type=int, default=20261102)
    a = ap.parse_args()
    tasks = [(b, r, rep, a.seed) for b in BENCHES for r in ['iid', 'up50'] for rep in range(a.reps)]
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(task, t) for t in tasks]):
            f.result()
    print('done')
