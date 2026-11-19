"""H5 table from E1 shards: per grid cell (spectrum x SNR-level h x M x k) the relative RMSE gap between each forecast and the measured error
(rep-averaged), the pass fraction at the pre-declared 10% tolerance, failing cells, rank_eff vs selected rank.  python exp/analyze_e1.py"""
import sys, glob, json
import numpy as np, pandas as pd
D = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob('results/E1/e1_shard*.parquet'))], ignore_index=True)
FC = ['oracle', 'naive', 'fm_noinfl', 'fm']
cell = ['kind', 'h', 'M', 'k', 'plug']
G = D.groupby(cell)[FC + ['measured', 'floor', 'mean_pred']].mean().reset_index()
nrep = D.groupby(cell).rep.nunique().rename('n_rep').reset_index()
G = G.merge(nrep)
for f in FC:
    G['gap_' + f] = (np.sqrt(G[f]) - np.sqrt(G.measured)).abs() / np.sqrt(G.measured)
    G['sgap_' + f] = (np.sqrt(G[f]) - np.sqrt(G.measured)) / np.sqrt(G.measured)
G['gain_vs_mean'] = 1 - G.measured / G.mean_pred
G.to_csv('results/E1/h5_cells.csv', index=False)
summ = {}
for plug in ('cv', 'true_r'):
    g = G[G.plug == plug]
    summ[plug] = {f: dict(pass10=float((g['gap_' + f] <= 0.10).mean()), pass20=float((g['gap_' + f] <= 0.20).mean()),
                          median_gap=float(g['gap_' + f].median()), n_cells=len(g),
                          by_kind={kk: float((x['gap_' + f] <= 0.10).mean()) for kk, x in g.groupby('kind')},
                          by_M={int(m): float((x['gap_' + f] <= 0.10).mean()) for m, x in g.groupby('M')}) for f in FC}
R = D.drop_duplicates(['kind', 'h', 'M', 'rep', 'plug']).query("plug=='cv'")
R = R.assign(d_sel=R.r_cv - R.rank_eff, d_true=R.r_cv - R.r_true)
rk = R.groupby(['kind', 'h', 'M'])[['r_cv', 'rank_eff', 'r_true', 'd_sel']].mean().reset_index()
rk['within2'] = R.assign(w=(R.d_sel.abs() <= 2)).groupby(['kind', 'h', 'M']).w.mean().values
rk.to_csv('results/E1/rank_eff_cells.csv', index=False)
summ['rank'] = dict(frac_cells_mean_within2=float((rk.d_sel.abs() <= 2).mean()), frac_reps_within2=float((R.d_sel.abs() <= 2).mean()),
                    corr_rcv_rankeff=float(np.corrcoef(R.r_cv, R.rank_eff)[0, 1]))
json.dump(summ, open('results/E1/h5_summary.json', 'w'), indent=1)
print(json.dumps(summ, indent=1)); print(len(D), 'rows; reps per cell', nrep.n_rep.min(), nrep.n_rep.max())
