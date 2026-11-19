"""Extra selectors / inference rules evaluated on the SAME folds, targets, ranks and seeds as an existing run (review items #8, #9 of experiment-repo).

usage: python xrun.py <run> <name> --sel ... --meth ... [--ks 2 4 8 16] [--n_rand 5]
  <run>   an existing run in results/raw (its json gives data, split, K, reps, seed, target_frac, group_col; <run>_folds.parquet gives the rank)
  output  results/raw/X_<name>.parquet with the run_cv.py schema (rep, fold, model, selector, method, k, n_t, sse_z) -> analyze with x_table.py

selectors (all computed from the training models only; `adapt_loc` additionally uses the held-out model's revealed scores)
  random      n_rand random orders (as run_cv)
  gv_fa       static greedy conditional variance of the targets under the factor model (as run_cv)
  fwd_ridge   shared-set forward selection on the completed training matrix: next benchmark minimises the 5-fold CV ridge error summed over the held-out target benchmarks
  mtl         multi-task lasso path (training matrix, all target benchmarks jointly): benchmarks in order of entering the path
  adapt_loc   ADAPTIVE: after each revealed score the next benchmark is the greedy conditional-variance choice under a LOCAL Gaussian model, i.e. the
              covariance of the 40 training models nearest (on the benchmarks revealed so far) to the new model, shrunk 10 % to its diagonal.  Under the
              global Gaussian model the posterior variance does not depend on the observed values, so the adaptive and static greedy orders coincide; this
              variant lets the choice depend on the values.
methods: fa, krr, ridge, avgreg, knn, mean (lib.Predictor) and
  ols         unregularised least squares on the revealed benchmarks (completed train matrix, intercept) (k <= 8)
  fa_r1, fa_r2, fa_r3   factor model with the rank FIXED (r = 1 is the Gaussian one-dimensional ability / IRT-style model)
  softimpute  soft-thresholded SVD completion, lambda by hold-out, ridge fold-in of the new row
  trend_fa    per-benchmark linear release-date trend removed (fitted on the training models), FA on the residuals, predictions re-trended
  trend_ols   same detrending, then OLS on the detrended revealed scores
"""
import os, sys, json, argparse, time
import numpy as np, pandas as pd
import lib
from run_cv import make_folds
from extra_baselines import softimpute_fit, softimpute_predict, trend_fit

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); MAT = os.path.join(HERE, '..', 'data', 'matrices')


def fwd_ridge_order(Zc, T, cand, kmax, nf=5, lam=1.0, seed=0):
    n = Zc.shape[0]; fold = np.random.default_rng(seed).permutation(n) % nf
    S, ci = [], np.where(cand)[0]
    Yt = Zc[:, T]
    for _ in range(kmax):
        best, bj = np.inf, None
        for c in ci:
            if c in S:
                continue
            X = np.c_[Zc[:, S + [c]], np.ones(n)]; e = 0.0
            for f in range(nf):
                tr = fold != f
                A = X[tr].T @ X[tr] + lam * np.eye(X.shape[1])
                e += ((X[~tr] @ np.linalg.solve(A, X[tr].T @ Yt[tr]) - Yt[~tr]) ** 2).sum()
            if e < best:
                best, bj = e, c
        S.append(bj)
    return S


def mtl_order(Zc, T, cand, kmax):
    from sklearn.linear_model import MultiTaskLasso
    ci = np.where(cand)[0]
    X = Zc[:, ci]; Y = Zc[:, T]
    X = X - X.mean(0); Y = Y - Y.mean(0)
    amax = np.abs(X.T @ Y).max() if False else np.sqrt(((X.T @ Y) ** 2).sum(1)).max() / len(X)
    order = []
    m = MultiTaskLasso(alpha=amax, warm_start=True, max_iter=2000, tol=1e-3, fit_intercept=False)
    for a in amax * np.geomspace(1, 1e-3, 60):
        m.alpha = a; m.fit(X, Y)
        nz = np.where(np.sqrt((m.coef_ ** 2).sum(0)) > 1e-8)[0]
        for j in nz:
            if ci[j] not in order:
                order.append(int(ci[j]))
        if len(order) >= kmax:
            break
    rest = [int(c) for c in ci if c not in order]
    return (order + rest)[:kmax]


def adaptive_local(Zc, zte_row, obs_row, T, cand, kmax, nb=40, shrink=0.1, first=None):
    """returns the adaptive order for one held-out model (only benchmarks it has scores for are candidates)"""
    av = np.where(cand & obs_row)[0]
    S = []
    for step in range(kmax):
        if step == 0 and first is not None:
            S.append(first); continue
        if S:
            d = ((Zc[:, S] - zte_row[S]) ** 2).sum(1)
            idx = np.argsort(d)[:nb]
        else:
            idx = np.arange(len(Zc))
        L = Zc[idx]; C = np.cov(L.T); C = (1 - shrink) * C + shrink * np.diag(np.diag(C))
        if S:
            Css = C[np.ix_(S, S)] + 1e-6 * np.eye(len(S))
            Cs = np.linalg.solve(Css, C[S, :])
            R = C - C[:, S] @ Cs
        else:
            R = C
        num = (R[:, T] ** 2).sum(1); den = np.diag(R) + 1e-9
        gain = num / den
        gain[S] = -np.inf; mask = np.full(len(gain), True); mask[av] = False; gain[mask] = -np.inf
        if not np.isfinite(gain).any():
            break
        S.append(int(np.argmax(gain)))
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('name')
    ap.add_argument('--sel', nargs='+', default=['random', 'gv_fa'])
    ap.add_argument('--meth', nargs='+', default=['fa'])
    ap.add_argument('--ks', type=int, nargs='+', default=[2, 4, 8, 16])
    ap.add_argument('--n_rand', type=int, default=5)
    ap.add_argument('--reps', type=int, default=0)
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(RAW, a.run + '.json')))
    fo = pd.read_parquet(os.path.join(RAW, a.run + '_folds.parquet'))
    data = cfg['data']
    Y = np.load(os.path.join(MAT, data + '.npz'), allow_pickle=True)['Y']; M, N = Y.shape
    mp = os.path.join(MAT, data + '_models.csv')
    meta = pd.read_csv(mp, index_col=0) if os.path.exists(mp) else None
    ntar = max(1, int(round(cfg['target_frac'] * N)))
    kmax = max(a.ks)
    tnum = None
    if any(m.startswith('trend') for m in a.meth):
        dts = pd.to_datetime(meta['release_date'], errors='coerce')
        tnum = (dts.astype('int64').where(~dts.isna()).values.astype(float)) / 8.64e13
    rows = []; t0 = time.time()
    for rep in range(a.reps or cfg['reps']):
        rng = np.random.default_rng(cfg['seed'] * 1000 + rep)
        groups = dates = None
        if cfg['split'] == 'group':
            if cfg['group_col'] == 'family':
                groups = lib.family_labels(meta['org'].fillna('NA').astype(str).values, meta['adapted_from'].values, meta['name'].values)
            else:
                groups = meta[cfg['group_col']].fillna('NA').astype(str).values
            groups = np.array([f'single_{i}' if g in ('NA', 'Removed', '', 'nan') else g for i, g in enumerate(groups)])
        if cfg['split'] == 'temporal':
            dates = pd.to_datetime(meta['release_date'], errors='coerce').values
        folds = make_folds(cfg['split'], M, cfg['K'], rng, groups, dates)
        T0 = np.zeros(N, bool); T0[rng.choice(N, ntar, replace=False)] = True
        cand = ~T0; T = np.where(T0)[0]
        for fi, (tr, te) in enumerate(folds):
            Ztr, mu, sd, okc = lib.standardise(Y[tr].copy()); Ztr[:, ~okc] = np.nan
            r = int(fo[(fo.rep == rep) & (fo.fold == fi)]['rank'].iloc[0])
            fa = lib.FA(r, seed=rep).fit(Ztr); pred = lib.Predictor(Ztr, fa); Zc = pred.Zc
            Zte = (Y[te] - mu) / sd; Zte[:, ~okc] = np.nan; obs = ~np.isnan(Zte)
            extra = {}
            for m in a.meth:
                if m.startswith('fa_r'):
                    extra[m] = lib.FA(int(m[4:]), seed=rep).fit(Ztr)
            if 'softimpute' in a.meth:
                sim = softimpute_fit(Ztr, seed=rep) + (Ztr.shape[0],)
            if any(m.startswith('trend') for m in a.meth):
                trd = tnum[tr]; tm_, ts_ = np.nanmean(trd), np.nanstd(trd) + 1e-9
                tt = lambda x: (np.where(np.isnan(x), tm_, x) - tm_) / ts_
                ta, tb = trend_fit(Ztr, tt(trd))
                Zdt = Ztr - (ta + np.outer(tt(trd), tb))
                fad = lib.FA(r, seed=rep).fit(Zdt); Zdc = fad.complete(Zdt)
                t_te = tt(tnum[te])
            orders = {}
            for s in a.sel:
                if s == 'random':
                    orders[s] = [[j for j in rng.permutation(N) if cand[j]] for _ in range(a.n_rand)]
                elif s == 'gv_fa':
                    orders[s] = [lib.greedy_cond_var(fa.cov(), kmax, cand=cand)]
                elif s == 'dopt':
                    orders[s] = [lib.greedy_dopt(fa.W, fa.psi, kmax, cand)]
                elif s == 'fwd_ridge':
                    orders[s] = [fwd_ridge_order(Zc, T, cand, kmax, seed=rep)]
                elif s == 'mtl':
                    orders[s] = [mtl_order(Zc, T, cand, kmax)]
                elif s == 'adapt_loc':
                    orders[s] = None
            gv = lib.greedy_cond_var(fa.cov(), kmax, cand=cand)
            for ai in range(len(te)):
                tm = obs[ai] & T0
                if tm.sum() == 0:
                    continue
                for s in a.sel:
                    ol = orders[s] if orders[s] is not None else [adaptive_local(Zc, Zte[ai], obs[ai], T, cand, kmax, first=None)]
                    for k in a.ks:
                        for m in a.meth:
                            sse = 0.0; cnt = 0
                            for o in ol:
                                av = np.asarray(o)[obs[ai, np.asarray(o)]][:k]
                                if len(av) < k:
                                    continue
                                S = list(av); zS = Zte[ai, S][None]
                                if m in ('fa', 'krr', 'ridge', 'avgreg', 'knn', 'mean', 'pcals'):
                                    P = pred.predict(m, S, zS)[0]
                                elif m == 'ols':
                                    X = np.c_[Zc[:, S], np.ones(len(Zc))]
                                    B = np.linalg.lstsq(X, Zc, rcond=None)[0]
                                    P = (np.r_[zS[0], 1.0] @ B)
                                elif m.startswith('fa_r'):
                                    P = extra[m].predict_from(zS, S)[0]
                                elif m == 'softimpute':
                                    P = softimpute_predict(sim, zS, S)[0]
                                elif m == 'trend_fa':
                                    P = fad.predict_from(zS - (ta[S] + tb[S] * t_te[ai]), S)[0] + ta + tb * t_te[ai]
                                elif m == 'trend_ols':
                                    X = np.c_[Zdc[:, S], np.ones(len(Zdc))]
                                    B = np.linalg.lstsq(X, Zdc, rcond=None)[0]
                                    P = np.r_[zS[0] - (ta[S] + tb[S] * t_te[ai]), 1.0] @ B + ta + tb * t_te[ai]
                                else:
                                    raise ValueError(m)
                                sse += ((P - Zte[ai])[tm] ** 2).sum(); cnt += 1
                            if cnt:
                                rows.append((rep, fi, int(te[ai]), s, m, k, int(tm.sum()), sse / cnt))
            print(a.name, 'rep', rep, 'fold', fi, len(rows), f'{time.time()-t0:.0f}s', flush=True)
    d = pd.DataFrame(rows, columns=['rep', 'fold', 'model', 'selector', 'method', 'k', 'n_t', 'sse_z'])
    d['sse_pts'] = np.nan; d['sae_pts'] = np.nan; d['size'] = d.k
    d.to_parquet(os.path.join(RAW, f'X_{a.name}.parquet'))
    json.dump({**vars(a), 'base_run': a.run}, open(os.path.join(RAW, f'X_{a.name}.json'), 'w'))
    print('done', len(d), time.time() - t0)


if __name__ == '__main__':
    main()
