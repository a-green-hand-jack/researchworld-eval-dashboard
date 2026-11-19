"""Ablation tables for the paper from results/ablate_*.csv (written by analyze_extra.py)."""
import os, pandas as pd, numpy as np
R = '/work/results'; T = f'{R}/tables'
NAMES = {'pirt': 'p-IRT', 'cf': 'CF', 'eb0': 'CF-EB0', 'eb1': 'CF-EB1', 'pirt_cal': 'p-IRT, recalibrated', 'cf_cal': 'CF, recalibrated predictor',
         'eb0_cal': 'CF-EB0, recalibrated', 'greg1': 'Regression est. (source difficulty)', 'greg_irt': 'Regression est. (IRT item features)',
         'strat_mean': 'Stratified + mean', 'strat_cf': 'Stratified + CF', 'strat_eb0': 'Stratified + CF-EB0',
         'strat_greg1': 'Stratified + regression (difficulty)', 'strat_greg_irt': 'Stratified + regression (IRT feat.)'}


def get(abl):
    return pd.read_csv(f'{R}/ablate_{abl}.csv')


def cell(d, reg, k, setting, est, col='rel_rmse', fmt='{:.2f}'):
    q = d[(d.regime == reg) & (d.k == k) & (d.setting.astype(str) == str(setting)) & (d.est == est)]
    return fmt.format(q[col].iloc[0]) if len(q) else '--'


def write(fn, rows):
    open(f'{T}/{fn}', 'w').write('\n'.join(rows).rstrip().rstrip('\\') .rstrip() + '\n')


# n source models
d = get('nsrc'); rows = []
for m in sorted(d.setting.unique()):
    cells = [cell(d, reg, 50, m, e) for reg in ['iid', 'up50'] for e in ['pirt', 'cf', 'eb0']]
    rows.append(f'{m} & ' + ' & '.join(cells) + ' \\\\')
write('abl_nsrc.tex', rows)
# latent dim / prior
d = get('dim'); rows = []
for st in sorted(d.setting.unique()):
    dd, lt = st.split('_lt')
    cells = [cell(d, reg, 50, st, e) for reg in ['iid', 'up50'] for e in ['pirt', 'cf', 'eb0']]
    rows.append(f'${dd[0]}={dd[1:]}$, $\\lambda_\\vartheta={lt}$ & ' + ' & '.join(cells) + ' \\\\')
write('abl_dim.tex', rows)
# folds
d = get('folds'); rows = []
for K in sorted(d.setting.unique()):
    cells = [cell(d, reg, 50, K, e) for reg in ['iid', 'up50'] for e in ['cf', 'eb0']]
    rows.append(f'$K={K}$ & ' + ' & '.join(cells) + ' \\\\')
write('abl_folds.tex', rows)
# calibrated predictor / regression / strat
d = get('cal'); rows = []
for e in ['pirt', 'pirt_cal', 'cf', 'cf_cal', 'eb0', 'eb0_cal', 'greg1', 'greg_irt', 'strat_mean', 'strat_cf', 'strat_eb0', 'strat_greg1', 'strat_greg_irt']:
    cells = []
    for reg in ['iid', 'up50']:
        cells += [cell(d, reg, 50, 'd4', e), cell(d, reg, 50, 'd4', e, 'spearman', '{:.3f}')]
    rows.append(f'{NAMES[e]} & ' + ' & '.join(cells) + ' \\\\')
write('abl_cal.tex', rows)
print('ok')
