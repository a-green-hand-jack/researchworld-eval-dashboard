"""Main experiment: selection x estimator factorial over benchmarks, shift regimes and replicates.
Usage: python -I run_main.py [--reps 30] [--workers 36] [--benches a,b] [--regimes iid,up50,up75] [--tag main]
Each (bench, regime, rep) task writes results/raw_<tag>/<bench>_<regime>_<rep>.pkl (resumable)."""
import os, sys, time, pickle, argparse
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bplib import *
from concurrent.futures import ProcessPoolExecutor, as_completed

KS = [10, 25, 50, 100, 200]
REGIMES = {'iid': None, 'up50': 0.5, 'up75': 0.75, 'fam': None}  # 'fam': hold out whole organisations (Open LLM Leaderboard only)
DETAIL_EST = {'mean', 'pirt', 'cf', 'eb0', 'eb1', 'ridge', 'gpirt', 'pirt_cal', 'eb0_cal'}


def split_models(X, regime, rng, models=None):
    m = X.shape[0]
    if regime == 'fam':
        orgs = np.array([str(n).split('/')[0].split('__')[0] for n in models])
        uo = rng.permutation(np.unique(orgs)); tgt = np.zeros(m, bool)
        for o in uo:
            tgt |= orgs == o
            if tgt.sum() >= 0.3 * m:
                break
        return np.where(~tgt)[0], np.where(tgt)[0]
    if regime == 'iid':
        perm = rng.permutation(m); ns = int(round(m / 2))
        return np.sort(perm[:ns]), np.sort(perm[ns:])
    q = REGIMES[regime]
    order = np.argsort(X.mean(1), kind='stable'); ns = int(round(q * m))
    pool, tgt = order[:ns], order[ns:]
    src = rng.choice(pool, int(round(0.8 * len(pool))), replace=False)
    return np.sort(src), np.sort(tgt)


def run_task(args):
    bench, regime, rep, tag, seed0 = args
    out = f'/work/results/raw_{tag}/{bench}_{regime}_{rep}.pkl'
    if os.path.exists(out):
        return out
    t0 = time.time()
    X, models = load_bench(bench); n = X.shape[1]
    rng = np.random.default_rng(np.random.SeedSequence([seed0, BENCHES.index(bench), list(REGIMES).index(regime), rep]))
    src, tgt = split_models(X, regime, rng, models)
    Xs, Xt = X[src], X[tgt]; true = Xt.mean(1)
    d, b2, sig2, cvs = cv_select(Xs, rng)
    model = fit_irt(Xs, d, maxiter=300)
    rows, detail = [], {}
    info = dict(bench=bench, regime=regime, rep=rep, d=d, b2=b2, sig2=sig2, n=n, n_src=len(src), n_tgt=len(tgt),
                src_max=float(Xs.mean(1).max()), tgt_min=float(true.min()), tgt_max=float(true.max()))
    for k in KS:
        if k > n // 2:
            continue
        for sel, fn in SELECTORS.items():
            S, w = fn(Xs, k, rng, model)
            Y = Xt[:, S]
            preds = {'mean': est_mean(Y, S, w, n),
                     'pirt': est_pirt(Y, S, w, n, model),
                     'ridge': est_ridge(Xs, S, Y),
                     'knn': est_knn(Xs, S, Y)}
            preds['pirt_cal'] = est_pirt_cal(Y, S, w, n, model)
            s2 = sig2 / (4.0 if sel.startswith('anchor') else 1.0)
            lam = b2 / (s2 / len(S) + b2)
            preds['gpirt'] = lam * preds['mean'] + (1 - lam) * preds['pirt']
            if sel in ('rand', 'strat'):
                b, c, v = cf_parts(Y, S, rng, n, model)
                preds['cf'] = b + c
                preds['eb0'] = eb_shrink(b, c, v, False)
                preds['eb1'] = eb_shrink(b, c, v, True)
                preds['plugin_cf'] = b
                bc, cc, vc = cf_parts_cal(Y, S, np.random.default_rng([seed0, rep, k, len(S)]), n, model)   # separate rng: main draws unchanged
                preds['cf_cal'] = bc + cc
                preds['eb0_cal'] = eb_shrink(bc, cc, vc, False)
            for est, p in preds.items():
                r = dict(bench=bench, regime=regime, rep=rep, k=k, sel=sel, est=est, **metrics(p, true))
                rows.append(r)
                if sel == 'rand' and est in DETAIL_EST:
                    detail[(k, est)] = p.astype(np.float32)
    detail['true'] = true.astype(np.float32)
    info['time'] = time.time() - t0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + '.tmp', 'wb') as f:
        pickle.dump(dict(rows=rows, detail=detail, info=info), f)
    os.rename(out + '.tmp', out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=30); ap.add_argument('--workers', type=int, default=36)
    ap.add_argument('--benches', default=','.join(BENCHES)); ap.add_argument('--regimes', default='iid,up50,up75')
    ap.add_argument('--tag', default='main'); ap.add_argument('--seed', type=int, default=20261102)
    a = ap.parse_args()
    cost = {b: load_bench(b)[0].size for b in a.benches.split(',')}
    tasks = [(b, r, rep, a.tag, a.seed) for rep in range(a.reps) for b in sorted(cost, key=lambda b: -cost[b])
             for r in a.regimes.split(',')]  # rep-major so that partial runs stay balanced
    print(len(tasks), 'tasks', flush=True)
    t0 = time.time(); done = 0
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_task, t) for t in tasks]
        for f in as_completed(futs):
            f.result(); done += 1
            if done % 20 == 0:
                print(done, 'done', round(time.time() - t0), 's', flush=True)
    print('finished', round(time.time() - t0), 's')
