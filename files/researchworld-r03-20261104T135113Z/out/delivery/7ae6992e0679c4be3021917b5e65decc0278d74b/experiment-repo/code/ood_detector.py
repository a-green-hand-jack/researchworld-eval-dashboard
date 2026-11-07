"""Out-of-range detector for the new model (review item #9.2).

For a run (same folds, targets, ranks and seeds; selector gv_fa, rules fa and krr) and each held-out model and k in {2,4,8,16}:
  d2 = Mahalanobis distance of its k revealed standardised scores from the training mean under the SHRUNK EMPIRICAL training covariance
       (FA-completed training matrix, shrinkage 0.1 to the diagonal; fitted on the training models only, restricted to the k revealed benchmarks)
  flag = d2 > chi2_{k, 0.95}
and reports per run and k: flag rate, Spearman(d2, own nMSE), AUC of d2 for the top error tercile, nMSE of flagged vs unflagged models (bootstrap 95% CI over models)
usage: python ood_detector.py <run> [<run>...]    -> results/summary/ood_<run>.csv        (runs: B_mteb_dense56 d56_group d56_famgroup d56_temporal B_mteb_dense d275_group d275_temporal ...)
"""
import os, sys, json
import numpy as np, pandas as pd
from scipy.stats import chi2, spearmanr
import lib
from run_cv import make_folds
from analysis_lib import per_model

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); MAT = os.path.join(HERE, '..', 'data', 'matrices'); OUT = os.path.join(HERE, '..', 'results', 'summary')
KS = [2, 4, 8, 16]


def run(name, n_boot=1000):
    cfg = json.load(open(os.path.join(RAW, name + '.json')))
    fo = pd.read_parquet(os.path.join(RAW, name + '_folds.parquet'))
    d = pd.read_parquet(os.path.join(RAW, name + '.parquet'))
    d = d[(d.selector == 'gv_fa') & d.method.isin(['fa', 'krr']) & d.k.isin(KS)]
    data = cfg['data']; Y = np.load(os.path.join(MAT, data + '.npz'), allow_pickle=True)['Y']; M, N = Y.shape
    meta = pd.read_csv(os.path.join(MAT, data + '_models.csv'), index_col=0)
    ntar = max(1, int(round(cfg['target_frac'] * N))); kmax = max(KS)
    rows = []
    for rep in range(cfg['reps']):
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
        T0 = np.zeros(N, bool); T0[rng.choice(N, ntar, replace=False)] = True; cand = ~T0
        for fi, (tr, te) in enumerate(folds):
            Ztr, mu, sd, okc = lib.standardise(Y[tr].copy()); Ztr[:, ~okc] = np.nan
            r = int(fo[(fo.rep == rep) & (fo.fold == fi)]['rank'].iloc[0])
            fa = lib.FA(r, seed=rep).fit(Ztr); Zc = fa.complete(Ztr)
            order = lib.greedy_cond_var(fa.cov(), kmax, cand=cand)
            C = np.cov(Zc.T); C = 0.9 * C + 0.1 * np.diag(np.diag(C)); m0 = Zc.mean(0)
            Zte = (Y[te] - mu) / sd; Zte[:, ~okc] = np.nan; obs = ~np.isnan(Zte)
            for ai, mi in enumerate(te):
                av = np.asarray(order)[obs[ai, order]]
                for k in KS:
                    if len(av) < k:
                        continue
                    S = list(av[:k]); dz = Zte[ai, S] - m0[S]
                    rows.append((rep, fi, int(mi), k, float(dz @ np.linalg.solve(C[np.ix_(S, S)], dz))))
    D = pd.DataFrame(rows, columns=['rep', 'fold', 'model', 'k', 'd2'])
    g = per_model(d)
    dm = D.groupby(['model', 'k']).d2.mean().reset_index()
    rng = np.random.default_rng(0); out = []
    for m in ('fa', 'krr'):
        gm = g[g.method == m].merge(dm, on=['model', 'k'])
        gm['nmse'] = gm.sse_z / gm.n_t
        for k, x in gm.groupby('k'):
            x = x.reset_index(drop=True); thr = chi2.ppf(0.95, k)
            fl = (x.d2 > thr).values
            top = x.nmse > x.nmse.quantile(2 / 3)
            pos, neg = x.d2[top].values, x.d2[~top].values
            auc = (pos[:, None] > neg[None]).mean() + 0.5 * (pos[:, None] == neg[None]).mean()
            def pooled(msk, idx=None):
                i = np.arange(len(x)) if idx is None else idx
                mk = msk[i]
                return (x.sse_z.values[i][mk].sum() / x.n_t.values[i][mk].sum()) if mk.any() else np.nan
            est_f, est_u = pooled(fl), pooled(~fl)
            bs = []
            for _ in range(n_boot):
                i = rng.integers(0, len(x), len(x)); bs.append((pooled(fl, i), pooled(~fl, i)))
            bs = np.array(bs, float)
            out.append(dict(run=name, split=cfg['split'] + ('/' + cfg['group_col'] if cfg['split'] == 'group' else ''), method=m, k=k, n_models=len(x), flag_rate=fl.mean(), mean_d2_over_k=(x.d2 / k).mean(),
                            spearman_d2_nmse=spearmanr(x.d2, x.nmse)[0], auc_top_tercile=auc, nmse_all=x.sse_z.sum() / x.n_t.sum(),
                            nmse_flagged=est_f, nmse_flagged_lo=np.nanpercentile(bs[:, 0], 2.5) if np.isfinite(bs[:, 0]).any() else np.nan, nmse_flagged_hi=np.nanpercentile(bs[:, 0], 97.5) if np.isfinite(bs[:, 0]).any() else np.nan,
                            nmse_unflagged=est_u, nmse_unflagged_lo=np.nanpercentile(bs[:, 1], 2.5), nmse_unflagged_hi=np.nanpercentile(bs[:, 1], 97.5), n_flagged=int(fl.sum())))
    o = pd.DataFrame(out); o.to_csv(os.path.join(OUT, f'ood_{name}.csv'), index=False)
    print(o[o.method == 'fa'].round(3).to_string(), flush=True)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n)
