"""Compact summary of extra_baselines outputs (review items #8/#9):
(1) per-target forward selection vs the shared gv_fa set + fa / krr, matched on union size (models pooled over the union sizes in each bin);
(2) rolling-origin temporal: nMSE of mean / trend / fa / krr / softimpute / trend_fa for random and gv_fa sets.
usage: python extra_summary.py -> results/summary/extra_pertarget_summary.csv, extra_temporal_summary.csv
"""
import os
import numpy as np, pandas as pd
S = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')
pt, tm = [], []
for n in ['mteb_dense56', 'mteb_dense', 'mteb_mid']:
    d = pd.read_csv(os.path.join(S, f'extra_{n}.csv'))
    u = d[d.split == 'kfold']
    u = u[u.method.isin(['pertarget', 'fa@union', 'krr@union'])]
    sizes = np.array(sorted(u.k.unique()))
    bins = np.array_split(sizes, 3)
    for b in bins:
        for m in ['pertarget', 'fa@union', 'krr@union']:
            x = u[(u.method == m) & u.k.isin(b)]
            w = x.n_models.to_numpy()
            pt.append(dict(dataset=n, union_lo=b.min(), union_hi=b.max(), method=m, n_models=int(w.sum()), nmse=float((x.nmse * w).sum() / w.sum()) if w.sum() else np.nan))
    t = d[(d.method.isin(['mean', 'trend', 'fa', 'krr', 'softimpute', 'trend_fa']))]
    t = t.assign(dataset=n)
    tm.append(t[['dataset', 'split', 'sel', 'method', 'k', 'n_models', 'nmse', 'lo', 'hi']])
pd.DataFrame(pt).to_csv(os.path.join(S, 'extra_pertarget_summary.csv'), index=False)
pd.concat(tm).to_csv(os.path.join(S, 'extra_temporal_summary.csv'), index=False)
print(pd.DataFrame(pt).pivot_table(index=['dataset', 'union_lo', 'union_hi'], columns='method', values='nmse').round(3))
