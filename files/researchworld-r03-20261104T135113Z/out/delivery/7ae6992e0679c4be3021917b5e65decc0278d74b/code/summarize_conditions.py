"""One long table over all analysed runs for the data-condition figure / table (C5, C6, C8):
run, group, selector, method, k, nmse (+CI), paired difference to random (+CI), error of the column-mean baseline.
usage: python summarize_conditions.py   -> results/summary/conditions.csv
group: main (B_* real), small-N-A (A_* protocol), synthetic (B_syn_*), ablation (d56_*, d275_*, olb_*), cost (C_*)
"""
import os, glob
import pandas as pd

S = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')
KS = [1, 2, 4, 8, 16]
rows = []
for f in sorted(glob.glob(os.path.join(S, 'curves_*.csv'))):
    run = os.path.basename(f)[7:-4]
    if run.startswith('main_'):
        continue
    c = pd.read_csv(f)
    pf = os.path.join(S, f'paired_{run}.csv')
    p = pd.read_csv(pf) if os.path.exists(pf) else None
    c = c[c.k.isin(KS) & c.selector.isin(['random', 'gv_fa', 'gv_emp', 'dopt', 'kcenter', 'popular', 'oracle'])]
    base = c[(c.method == 'mean')].groupby('k').nmse.mean()
    if p is not None:
        c = c.merge(p.rename(columns={'diff': 'diff_vs_random', 'lo': 'diff_lo', 'hi': 'diff_hi'}), on=['selector', 'method', 'k'], how='left')
    c['nmse_mean_baseline'] = c.k.map(base)
    grp = ('synthetic' if '_syn_' in run else 'main' if run.startswith('B_') else 'small-N-A' if run.startswith('A_') else 'cost' if run.startswith('C_') else 'ablation')
    c.insert(0, 'run', run); c.insert(1, 'group', grp)
    rows.append(c)
out = pd.concat(rows)
out.to_csv(os.path.join(S, 'conditions.csv'), index=False)
print(out.groupby(['group', 'run']).size())
