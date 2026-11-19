"""Why do leverage-score and pivoted-QR selection do worse than random here? (review item #8.4)  Descriptive diagnostic on the full completed MTEB-56 matrix:
for each rank r: share of the total leverage mass in the 5 highest-leverage tasks, their task types, and the mean absolute pairwise correlation (completed matrix)
among the first 8 benchmarks picked by lev / qr / gv_fa / dopt (a redundant set has a high value) and the number of distinct task types among them.
usage: python lev_diag.py [dataset=mteb_dense56]  -> results/summary/lev_diag_<dataset>.csv
"""
import os, sys
import numpy as np, pandas as pd
import lib

HERE = os.path.dirname(__file__); MAT = os.path.join(HERE, '..', 'data', 'matrices'); OUT = os.path.join(HERE, '..', 'results', 'summary')
data = sys.argv[1] if len(sys.argv) > 1 else 'mteb_dense56'
Y = np.load(os.path.join(MAT, data + '.npz'), allow_pickle=True)['Y']
b = pd.read_csv(os.path.join(MAT, data + '_benches.csv'))
Z, mu, sd, ok = lib.standardise(Y.copy()); Z[:, ~ok] = np.nan
fa = lib.FA(12, seed=0).fit(Z); Zc = fa.complete(Z)
R = np.corrcoef(Zc.T)
_, _, Vt = np.linalg.svd(Zc - Zc.mean(0), full_matrices=False)
rows = []
for r in (1, 2, 3, 4, 8, 12, 16):
    lev = (Vt[:r] ** 2).sum(0); top = np.argsort(-lev)[:5]
    orders = {'lev': lib.leverage_order(Zc, r), 'qr': lib.qr_pivot_order(Zc, r)[:8]}
    if r == 12:
        orders['gv_fa'] = lib.greedy_cond_var(fa.cov(), 8); orders['dopt'] = lib.greedy_dopt(fa.W, fa.psi, 8)
    for s, o in orders.items():
        o = list(o)[:8]; sub = np.abs(R[np.ix_(o, o)])[np.triu_indices(8, 1)]
        rows.append(dict(rank=r, selector=s, top5_leverage_share=lev[top].sum() / lev.sum(), top5_types='; '.join(b.type.values[top]),
                         mean_abs_corr_first8=sub.mean(), mean_abs_corr_with_all=np.abs(R[o]).mean(), mean_uniqueness_psi=fa.psi[o].mean(), n_types_first8=len(set(b.type.values[o])), first8_types=','.join(t[:4] for t in b.type.values[o])))
rnd = np.random.default_rng(0); sub = []
for _ in range(200):
    o = rnd.permutation(Y.shape[1])[:8]; sub.append(np.abs(R[np.ix_(o, o)])[np.triu_indices(8, 1)].mean())
rows.append(dict(rank=0, selector='random(mean of 200)', mean_abs_corr_first8=float(np.mean(sub)), mean_abs_corr_with_all=float(np.abs(R).mean()), mean_uniqueness_psi=float(fa.psi.mean())))
pd.DataFrame(rows).to_csv(os.path.join(OUT, f'lev_diag_{data}.csv'), index=False)
print(pd.DataFrame(rows).round(3).to_string())
print(b.type.value_counts().to_dict())
