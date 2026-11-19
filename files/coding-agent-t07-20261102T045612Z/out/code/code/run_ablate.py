"""Ablations: number of source models, latent dimension, ability-prior strength, number of cross-fitting folds.
Usage: python -I run_ablate.py [--reps 10 --workers 4]; results in results/raw_ablate/"""
import os, sys, time, pickle, argparse
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bplib import *
from run_main import split_models
from concurrent.futures import ProcessPoolExecutor, as_completed

KS = [50, 100]
NSRC = [8, 16, 32, 64, 128]
DIMS = [1, 2, 4, 8]


def evaluate(rows, meta, model, Xt, true, S, w, n, rng, K=5, lam_theta=1.0):
    Y = Xt[:, S]
    b, c, v = cf_parts(Y, S, rng, n, model, K=K, lam_theta=lam_theta)
    preds = {'mean': Y @ w, 'pirt': est_pirt(Y, S, w, n, model, lam_theta), 'cf': b + c,
             'eb0': eb_shrink(b, c, v, False), 'eb1': eb_shrink(b, c, v, True)}
    for est, p in preds.items():
        rows.append(dict(**meta, est=est, **metrics(p, true)))


def task(args):
    bench, regime, rep, seed0 = args
    out = f'/work/results/raw_ablate/{bench}_{regime}_{rep}.pkl'
    if os.path.exists(out):
        return out
    X, _ = load_bench(bench); n = X.shape[1]
    rng = np.random.default_rng(np.random.SeedSequence([seed0, 99, BENCHES.index(bench), ['iid', 'up50', 'up75'].index(regime), rep]))
    src, tgt = split_models(X, regime, rng)
    Xt = X[tgt]; true = Xt.mean(1)
    rows = []
    base = dict(bench=bench, regime=regime, rep=rep)
    draws = {}
    for k in KS:
        if k <= n // 2:
            draws[k] = sel_random(X[src], k, rng)
    # A: number of source models (d=2)
    for ms in NSRC:
        if ms > len(src):
            continue
        sub = rng.choice(src, ms, replace=False)
        model = fit_irt(X[sub], 2, maxiter=300)
        for k, (S, w) in draws.items():
            evaluate(rows, dict(base, abl='nsrc', setting=ms, k=k), model, Xt, true, S, w, n, np.random.default_rng(rep), 5, 1.0)
    # B: latent dim and ability prior
    for d in DIMS:
        model = fit_irt(X[src], d, maxiter=300)
        for lt in [1.0, 0.1]:
            for k, (S, w) in draws.items():
                evaluate(rows, dict(base, abl='dim', setting=f'd{d}_lt{lt}', k=k), model, Xt, true, S, w, n, np.random.default_rng(rep), 5, lt)
        if d == 2:   # C: number of folds
            for K in [2, 5, 10]:
                for k, (S, w) in draws.items():
                    evaluate(rows, dict(base, abl='folds', setting=K, k=k), model, Xt, true, S, w, n, np.random.default_rng(rep), K, 1.0)
    # E: recalibrated per-target predictor (supplementary stronger model-based baseline)
    model = fit_irt(X[src], 4, maxiter=300)
    Xs_mean = X[src].mean(0)
    for k, (S, w) in draws.items():
        Y = Xt[:, S]
        b, c, v = cf_parts_cal(Y, S, np.random.default_rng(rep), n, model)
        b0, c0, v0 = cf_parts(Y, S, np.random.default_rng(rep), n, model)
        preds = {'mean': Y @ w, 'pirt': est_pirt(Y, S, w, n, model), 'pirt_cal': est_pirt_cal(Y, S, w, n, model),
                 'cf': b0 + c0, 'cf_cal': b + c, 'eb0': eb_shrink(b0, c0, v0), 'eb0_cal': eb_shrink(b, c, v)}
        Z1 = Xs_mean[:, None]; Zirt = np.concatenate([model['b'][:, None], model['A']], 1)
        preds['greg1'] = est_greg(Y, S, Z1); preds['greg_irt'] = est_greg(Y, S, Zirt)
        S2, w2 = sel_strat(X[src], k, rng); Y2 = Xt[:, S2]
        b2_, c2_, v2_ = cf_parts(Y2, S2, np.random.default_rng(rep), n, model)
        preds['strat_mean'] = Y2 @ w2; preds['strat_cf'] = b2_ + c2_; preds['strat_eb0'] = eb_shrink(b2_, c2_, v2_)
        preds['strat_greg1'] = est_greg(Y2, S2, Z1); preds['strat_greg_irt'] = est_greg(Y2, S2, Zirt)
        for est, p in preds.items():
            rows.append(dict(**base, abl='cal', setting='d4', k=k, est=est, **metrics(p, true)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pickle.dump(rows, open(out, 'wb'))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=4); ap.add_argument('--reps', type=int, default=10)
    ap.add_argument('--seed', type=int, default=20261102)
    a = ap.parse_args()
    tasks = [(b, r, rep, a.seed) for rep in range(a.reps) for b in BENCHES for r in ['iid', 'up50']]
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(task, t) for t in tasks]):
            f.result(); n += 1
            if n % 20 == 0:
                print(n, 'done', round(time.time() - t0), 's', flush=True)
    print('done')
