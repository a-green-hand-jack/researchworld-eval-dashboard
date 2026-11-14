"""k*(G_own CI lower bound >= 0.8 / 0.9) per selector and rule for the extra-selector / extra-rule runs, on the xrun k grid.
usage: python x_kstar.py -> results/summary/x_kstar.csv   (NaN = not reached on the grid; model bootstrap)"""
import os, glob
import pandas as pd
S = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')
rows = []
for f in sorted(glob.glob(os.path.join(S, 'xcurves_*.csv'))):
    run = os.path.basename(f)[8:-4]
    c = pd.read_csv(f)
    for (sel, meth), g in c.groupby(['selector', 'method']):
        r = dict(run=run, selector=sel, method=meth)
        for q in (0.8, 0.9):
            ok = g[g.G_own_lo >= q]
            r[f'kstar_G>={q}'] = ok.k.min() if len(ok) else float('nan')
        rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(S, 'x_kstar.csv'), index=False)
