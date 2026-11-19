"""E8: history size and missingness sweeps.  python exp/analyze_e8.py -> results/E8/{gap_cells,rank_cells,summary}.csv/json
For each (setting, M, mask): relative RMSE gap of every forecast vs measured at k in the H1 grid; pass fraction at 20%;
rank: likelihood-selected r (r_cv) vs the BBP count rank_eff(M) from the reference spectrum, within 2?"""
import glob, json
import numpy as np, pandas as pd
D = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob('results/E8/sweep_*.parquet'))], ignore_index=True)
D = D.drop_duplicates(['setting', 'rep', 'M', 'mask', 'k'])
FC = ['naive', 'fm_noinfl', 'fm']
G = D.groupby(['setting', 'M', 'mask', 'k'])[FC + ['measured', 'random', 'mean_pred', 'floor']].mean().reset_index()
n = D.groupby(['setting', 'M', 'mask', 'k']).rep.nunique().rename('n_rep').reset_index(); G = G.merge(n)
for f in FC:
    G['sgap_' + f] = (np.sqrt(G[f]) - np.sqrt(G.measured)) / np.sqrt(G.measured)
G['gain_vs_random'] = 1 - np.sqrt(G.measured) / np.sqrt(G.random)
G['rmse_measured'] = np.sqrt(G.measured); G['rmse_random'] = np.sqrt(G.random); G['rmse_meanpred'] = np.sqrt(G.mean_pred)
G.to_csv('results/E8/gap_cells.csv', index=False)
R = D.drop_duplicates(['setting', 'rep', 'M', 'mask'])
R = R.assign(d=R.r_cv - R.rank_eff, dref=R.r_cv - R.r_ref)
rk = R.groupby(['setting', 'M', 'mask']).agg(r_cv=('r_cv', 'mean'), rank_eff=('rank_eff', 'mean'), r_ref=('r_ref', 'mean'), thr=('thr', 'first'),
                                              within2=('d', lambda x: float((x.abs() <= 2).mean())), n_rep=('rep', 'nunique')).reset_index()
rk.to_csv('results/E8/rank_cells.csv', index=False)
summ = {}
for (s, mk), g in G.groupby(['setting', 'mask']):
    for f in FC:
        a = g['sgap_' + f].abs()
        summ[f'{s}|mask={mk}|{f}'] = dict(median_gap=float(a.median()), pass20=float((a <= 0.2).mean()), n_cells=len(g),
                                          by_M={int(m): float(x['sgap_' + f].abs().median()) for m, x in g.groupby('M')})
json.dump(summ, open('results/E8/summary.json', 'w'), indent=1)
pd.set_option('display.width', 200)
print(rk.round(2).to_string())
t = G[(G.k.isin([3, 8, 20])) & (G['mask'] == 0)].pivot_table(index=['setting', 'M'], columns='k', values=['rmse_measured', 'sgap_fm'])
print(t.round(3).to_string())
