"""Extra baselines and the temporal-shift diagnostics (review items 5 and 7).

For each dataset (dense-matrix runs, protocol B targets: random 25% of benchmarks never selected, same targets for all k) and each split
  kfold    : random K=7 folds (matched in size to the temporal test blocks)
  temporal : rolling origin, train on the earliest 55/65/75/85 % of dated models, test on the next 15 %
the script fits everything on the training models only and reports, per held-out model, the target error (nMSE, z-scale of the train sd) of

  mean        train column mean
  trend       column mean + per-benchmark linear release-date trend (no benchmark is run: the 'no-information, drift-aware' baseline)
  fa, krr     the main methods, after the selector (gv_fa / random) has revealed k benchmarks
  trend_fa    detrend every benchmark by its train date trend, FA on the residuals, predict residuals from the k detrended scores, add the trend back
  softimpute  soft-thresholded SVD completion (lambda by 10 % hold-out on the training matrix) + ridge fold-in of the new row
  pertarget   (kfold only) every target gets its OWN forward-selected benchmarks (k_t = 1,2,3; chosen by 5-fold CV error on the train matrix);
              the new model must run the UNION of them: its size is reported and gv_fa+fa / krr at that same size is evaluated on the same models

and, for every held-out model, the Mahalanobis distance d2/k of its k revealed scores to the train FA covariance (in-range check),
so that its rank correlation with the realised error and its shift between kfold and temporal blocks can be reported.

usage: python extra_baselines.py <name> [<name> ...]  ->  results/summary/extra_<name>_models.csv (per model), extra_<name>.csv (summaries)
"""
import os, sys, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import lib

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); SUM = os.path.join(HERE, '..', 'results', 'summary')
KS = [2, 4, 8, 16]


def softimpute_fit(Z, lams=(0.5, 1, 2, 4, 8), n_iter=60, seed=0):
    """soft-thresholded SVD completion of a matrix with NaN; lambda chosen by hold-out of 10 % of observed cells. returns (mean-free V, shrunk s, mu)."""
    mu = np.nanmean(Z, 0); mu = np.where(np.isnan(mu), 0, mu)
    X = Z - mu; obs = ~np.isnan(X); X0 = np.where(obs, X, 0.0)
    rng = np.random.default_rng(seed)
    hold = obs & (rng.random(X.shape) < 0.1)

    def fit(lam, mask):
        A = np.zeros_like(X0)
        for _ in range(n_iter):
            Xf = np.where(mask, X0, A)
            U, s, Vt = np.linalg.svd(Xf, full_matrices=False)
            s = np.maximum(s - lam, 0); A = (U * s) @ Vt
        return Vt, s

    best, bl = np.inf, lams[0]
    for lam in lams:
        Vt, s = fit(lam, obs & ~hold)
        Ahat = fit_rec(X0, obs & ~hold, Vt, s)
        e = ((Ahat - X0)[hold] ** 2).mean()
        if e < best:
            best, bl = e, lam
    Vt, s = fit(bl, obs)
    return Vt, s, mu, bl


def fit_rec(X0, mask, Vt, s):
    """reconstruction of the matrix from the (Vt, s) subspace by row-wise ridge fold-in on observed cells"""
    r = int((s > 0).sum())
    if r == 0:
        return np.zeros_like(X0)
    B = (Vt[:r].T * (s[:r] / np.sqrt(max(X0.shape[0], 1))))
    out = np.zeros_like(X0)
    for i in range(X0.shape[0]):
        m = mask[i]
        Bm = B[m]
        c = np.linalg.solve(Bm.T @ Bm + np.eye(r), Bm.T @ X0[i, m])
        out[i] = B @ c
    return out


def softimpute_predict(model, zS, S):
    Vt, s, mu, _, n = model
    r = int((s > 0).sum())
    if r == 0:
        return np.tile(mu, (zS.shape[0], 1))
    B = Vt[:r].T * (s[:r] / np.sqrt(max(n, 1)))
    BS = B[S]
    G = np.linalg.solve(BS.T @ BS + np.eye(r), BS.T)
    return mu + ((zS - mu[S]) @ G.T) @ B.T


def trend_fit(Z, t):
    """per-benchmark OLS of z on standardised date t (observed cells); returns intercept a, slope b (z-scale)"""
    N = Z.shape[1]; a = np.zeros(N); b = np.zeros(N)
    for j in range(N):
        m = ~np.isnan(Z[:, j])
        if m.sum() < 8:
            continue
        x = t[m]; y = Z[m, j]
        xc = x - x.mean()
        b[j] = (xc * (y - y.mean())).sum() / ((xc ** 2).sum() + 1e-9)
        a[j] = y.mean() - b[j] * x.mean()
    return a, b


def pertarget_sets(Zc, T, cand, kt=3, nf=5, seed=0):
    """forward selection per target (CV OLS error on the train matrix); returns {j: [S after 1, 2, ..kt]}"""
    rng = np.random.default_rng(seed)
    n = Zc.shape[0]; fold = rng.permutation(n) % nf
    ci = np.where(cand)[0]; out = {}
    for j in T:
        S = []
        for _ in range(kt):
            best, bj = np.inf, None
            for c in ci:
                if c in S:
                    continue
                X = np.c_[Zc[:, S + [c]], np.ones(n)]; e = 0.0
                for f in range(nf):
                    tr = fold != f
                    beta = np.linalg.lstsq(X[tr].T @ X[tr] + 1e-2 * np.eye(X.shape[1]), X[tr].T @ Zc[tr, j], rcond=None)[0]
                    e += ((X[~tr] @ beta - Zc[~tr, j]) ** 2).sum()
                if e < best:
                    best, bj = e, c
            S.append(bj)
        out[j] = list(S)
    return out


def folds_for(split, M, dates, rng, K=7):
    idx = np.arange(M)
    if split == 'kfold':
        p = rng.permutation(M)
        return [(np.setdiff1d(idx, f), np.sort(f)) for f in np.array_split(p, K)]
    ok = ~pd.isna(dates)
    o = idx[ok][np.argsort(np.asarray(dates)[ok])]
    out = []
    for f in (0.55, 0.65, 0.75, 0.85):
        a, b = int(len(o) * f), int(len(o) * (f + 0.15))
        out.append((np.concatenate([o[:a], idx[~ok]]), o[a:b]))
    return out


def run(name, reps=6, n_rand=5):
    z = np.load(os.path.join(HERE, '..', 'data', 'matrices', name + '.npz'), allow_pickle=True)
    Y = z['Y']; M, N = Y.shape
    meta = pd.read_csv(os.path.join(HERE, '..', 'data', 'matrices', name + '_models.csv'), index_col=0)
    dates = pd.to_datetime(meta['release_date'], errors='coerce').values
    tnum = pd.Series(dates).astype('int64').where(~pd.isna(dates)).values.astype(float) / 8.64e13    # days
    ranks = pd.read_parquet(os.path.join(RAW, f'B_{name}_folds.parquet'))['rank']
    r = int(np.median(ranks))
    ntar = max(1, int(round(0.25 * N)))
    rows = []
    for split in ('kfold', 'temporal'):
        for rep in range(reps):
            rng = np.random.default_rng(777 + rep)
            T0 = np.zeros(N, bool); T0[rng.choice(N, ntar, replace=False)] = True
            cand = ~T0; T = np.where(T0)[0]
            for fi, (tr, te) in enumerate(folds_for(split, M, dates, rng)):
                Ztr, mu, sd, okc = lib.standardise(Y[tr].copy()); Ztr[:, ~okc] = np.nan
                Zte = (Y[te] - mu) / sd; Zte[:, ~okc] = np.nan
                obs = ~np.isnan(Zte)
                trd = tnum[tr]; ted = tnum[te]
                tm, ts = np.nanmean(trd), np.nanstd(trd) + 1e-9
                t_tr = np.where(np.isnan(trd), tm, trd); t_tr = (t_tr - tm) / ts
                t_te = (np.where(np.isnan(ted), tm, ted) - tm) / ts
                fa = lib.FA(r, seed=rep).fit(Ztr); pred = lib.Predictor(Ztr, fa)
                a, b = trend_fit(Ztr, t_tr)
                Zdt = Ztr - (a + np.outer(t_tr, b))
                fad = lib.FA(r, seed=rep).fit(Zdt)
                sim = softimpute_fit(Ztr, seed=rep); sim = sim + (Ztr.shape[0],)
                C = fa.cov()
                orders = {'gv_fa': [lib.greedy_cond_var(C, max(KS), cand=cand)],
                          'random': [[j for j in rng.permutation(N) if cand[j]] for _ in range(n_rand)]}
                # per-model target error accumulator
                def err(P, a_):
                    m = obs[a_] & T0
                    return ((P[m] - Zte[a_][m]) ** 2).sum(), m.sum()
                res = {}
                for ai in range(len(te)):
                    ntk = (obs[ai] & T0).sum()
                    if ntk == 0:
                        continue
                    base = dict(split=split, rep=rep, fold=fi, model=int(te[ai]), n_t=int(ntk))
                    for nm, P in (('mean', np.zeros(N)), ('trend', a + b * t_te[ai])):
                        rows.append({**base, 'sel': 'none', 'k': 0, 'method': nm, 'sse': err(P, ai)[0], 'd2k': np.nan})
                    for sel, ol in orders.items():
                        for k in KS:
                            for method in ('fa', 'krr', 'trend_fa', 'softimpute'):
                                sse = 0.0; d2 = 0.0; cnt = 0
                                for order in ol:
                                    av = np.asarray(order)[obs[ai, np.asarray(order)]][:k]
                                    if len(av) < k:
                                        continue
                                    S = list(av); zS = Zte[ai, S][None]
                                    if method in ('fa', 'krr'):
                                        P = pred.predict(method, S, zS)[0]
                                    elif method == 'trend_fa':
                                        zdt = zS - (a[S] + b[S] * t_te[ai])
                                        P = fad.predict_from(zdt, S)[0] + a + b * t_te[ai]
                                    else:
                                        P = softimpute_predict(sim, zS, S)[0]
                                    sse += err(P, ai)[0]; cnt += 1
                                    if method == 'fa':
                                        dz = zS[0] - fa.mu[S]
                                        d2 += dz @ np.linalg.solve(C[np.ix_(S, S)], dz) / k
                                if cnt:
                                    rows.append({**base, 'sel': sel, 'k': k, 'method': method, 'sse': sse / cnt, 'd2k': d2 / cnt if method == 'fa' else np.nan})
                if split == 'kfold' and rep < 3:
                    Zc = fa.complete(Ztr); ps = pertarget_sets(Zc, T, cand, 3, seed=rep)
                    for kt in (1, 2, 3):
                        U = sorted({c for j in T for c in ps[j][:kt]}); u = len(U)
                        ok_models = [ai for ai in range(len(te)) if obs[ai, U].all() and (obs[ai] & T0).any()]
                        ridge = {j: lib.ridge_gcv_fit(Zc[:, ps[j][:kt]], Zc[:, [j]]) for j in T}
                        order = lib.greedy_cond_var(C, max(KS + [u]), cand=cand)
                        for ai in ok_models:
                            P = np.zeros(N)
                            for j in T:
                                B_, b0 = ridge[j]; P[j] = (Zte[ai, ps[j][:kt]] @ B_ + b0)[0]
                            base = dict(split=split, rep=rep, fold=fi, model=int(te[ai]), n_t=int((obs[ai] & T0).sum()), kt=kt, u=u)
                            rows.append({**base, 'sel': 'pertarget', 'k': u, 'method': 'pertarget', 'sse': err(P, ai)[0], 'd2k': np.nan})
                            S = order[:u]
                            for method in ('fa', 'krr'):
                                P2 = pred.predict(method, S, Zte[ai, S][None])[0]
                                rows.append({**base, 'sel': 'gv_fa', 'k': u, 'method': method + '@union', 'sse': err(P2, ai)[0], 'd2k': np.nan})
        print(name, split, 'done', len(rows), flush=True)
    d = pd.DataFrame(rows); d['nmse'] = d.sse / d.n_t
    d.insert(0, 'dataset', name)
    d.to_csv(os.path.join(SUM, f'extra_{name}_models.csv'), index=False)
    # --- summaries with bootstrap over held-out models
    rng = np.random.default_rng(0); out = []
    for (split, sel, method, k), g in d.groupby(['split', 'sel', 'method', 'k']):
        pm = g.groupby('model').agg(sse=('sse', 'sum'), n=('n_t', 'sum'))
        v = pm.sse.values / pm.n.values
        bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(300)]
        out.append(dict(dataset=name, split=split, sel=sel, method=method, k=k, n_models=len(v), nmse=v.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
    pd.DataFrame(out).to_csv(os.path.join(SUM, f'extra_{name}.csv'), index=False)
    # --- Mahalanobis in-range check: does d2/k order the realised error ?
    mr = []
    dd = d[(d.method == 'fa') & d.d2k.notna()]
    for (split, sel, k), g in dd.groupby(['split', 'sel', 'k']):
        pm = g.groupby(['rep', 'fold', 'model']).agg(d2k=('d2k', 'mean'), nmse=('nmse', 'mean')).reset_index()
        rho = spearmanr(pm.d2k, pm.nmse)[0]
        top = pm.nmse > pm.nmse.quantile(2 / 3)
        pos, neg = pm.d2k[top].values, pm.d2k[~top].values
        auc = (pos[:, None] > neg[None]).mean() + 0.5 * (pos[:, None] == neg[None]).mean()
        mr.append(dict(dataset=name, split=split, sel=sel, k=k, n=len(pm), mean_d2k=pm.d2k.mean(), median_d2k=pm.d2k.median(), spearman_d2k_nmse=rho, auc_top_tercile=auc))
    pd.DataFrame(mr).to_csv(os.path.join(SUM, f'extra_mahalanobis_{name}.csv'), index=False)
    print(pd.DataFrame(mr).round(3).to_string(), flush=True)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n, reps=int(os.environ.get('REPS', 4)))
