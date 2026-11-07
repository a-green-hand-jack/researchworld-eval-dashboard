"""Mechanism diagnostic: bias of p-IRT vs the share of target successes that fall on items solved by no source model."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from bplib import *
from run_main import split_models, REGIMES
from analyze_lib import load_rows, BENCH_LABEL
from scipy.stats import pearsonr, spearmanr

df, info = load_rows()
rows = []
for b in BENCHES:
    X, _ = load_bench(b)
    for reg in ['iid', 'up50', 'up75']:
        for rep in range(30):
            rng = np.random.default_rng(np.random.SeedSequence([20261102, BENCHES.index(b), list(REGIMES).index(reg), rep]))
            src, tgt = split_models(X, reg, rng)
            dead = X[src].max(0) == 0
            mass = (X[tgt][:, dead].sum(1) / X[tgt].sum(1).clip(1)).mean()      # share of target successes on dead items
            rows.append(dict(bench=b, regime=reg, rep=rep, dead_frac=dead.mean(), dead_mass=mass,
                             gap=(X[tgt].mean() - X[src].mean()) * 100))
d = pd.DataFrame(rows)
sub = df[(df.k == 100) & df.combo.isin(['rand/pirt', 'rand/mean', 'rand/cf'])].pivot_table(index=['bench', 'regime', 'rep'], columns='est', values='bias').reset_index()
sub2 = df[(df.k == 100) & df.combo.isin(['rand/pirt', 'rand/mean'])].pivot_table(index=['bench', 'regime', 'rep'], columns='est', values='rmse').reset_index().rename(columns={'mean': 'rmse_mean', 'pirt': 'rmse_pirt'})
m = d.merge(sub, on=['bench', 'regime', 'rep']).merge(sub2, on=['bench', 'regime', 'rep'])
g = m.groupby(['bench', 'regime'])[['dead_frac', 'dead_mass', 'gap', 'pirt', 'mean', 'cf', 'rmse_mean', 'rmse_pirt']].mean().reset_index()
g.to_csv('/work/results/diag.csv', index=False)
print(g.round(3).to_string())
for col in ['dead_mass', 'dead_frac', 'gap']:
    print(col, 'pearson', pearsonr(g[col], g.pirt), 'spearman', spearmanr(g[col], g.pirt))
fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.6))
col = {'iid': 'tab:blue', 'up50': 'tab:red', 'up75': 'tab:orange'}
for reg in col:
    q = g[g.regime == reg]
    ax.scatter(q.gap, q.pirt, c=col[reg], s=14, label={'iid': 'IID', 'up50': 'Extrap-50', 'up75': 'Extrap-25'}[reg])
ax.set_xlabel('target $-$ source mean accuracy (pts)', fontsize=8); ax.set_ylabel('p-IRT bias, $k{=}100$ (pts)', fontsize=8)
ax.legend(fontsize=7, frameon=False); ax.axhline(0, color='k', lw=0.6)
plt.tight_layout(); plt.savefig('/work/figs/fig_pirt_bias_mechanism.pdf')
