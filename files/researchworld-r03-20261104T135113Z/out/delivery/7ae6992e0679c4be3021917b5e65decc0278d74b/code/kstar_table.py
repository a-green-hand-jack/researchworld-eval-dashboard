"""Table 2 source: k* per dataset for the pre-fixed gap-closed criterion and the absolute tolerances, selectors random / gv_fa / dopt x rules fa / ridge / krr.
usage: python kstar_table.py -> results/summary/kstar_table.csv   (rows: run, selector, method, k*G_own>=0.8, ..., nmse<=..., floor, mean baseline)
Runs with an F_ partner (`gapclosed_*`) only; NaN = not reached on the k grid (k grid per run in curves_*.csv).
"""
import os, glob
import pandas as pd

S = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')
rows = []
for f in sorted(glob.glob(os.path.join(S, 'kstar_gap_*.csv'))):
    run = os.path.basename(f)[10:-4]
    g = pd.read_csv(f)
    a = pd.read_csv(os.path.join(S, f'kstar_{run}.csv'))
    fl = pd.read_csv(os.path.join(S, f'floor_{run}.csv')).set_index('method')
    d = g.merge(a, on=['selector', 'method'])
    d = d[d.selector.isin(['random', 'gv_fa', 'dopt', 'gv_emp', 'kcenter', 'popular']) & d.method.isin(['fa', 'ridge', 'krr', 'knn'])]
    d.insert(0, 'run', run)
    d['nmse_floor_own'] = d.method.map(fl.nmse_floor)
    d['nmse_mean_k0'] = fl.loc['mean_k0', 'nmse_floor']
    rows.append(d)
out = pd.concat(rows)
out.to_csv(os.path.join(S, 'kstar_table.csv'), index=False)
print(out[out.selector.isin(['random', 'gv_fa']) & (out.method == 'krr')][['run', 'selector', 'k*G_own>=0.8', 'k*G_own>=0.9', 'nmse<=0.25']].to_string(index=False))
