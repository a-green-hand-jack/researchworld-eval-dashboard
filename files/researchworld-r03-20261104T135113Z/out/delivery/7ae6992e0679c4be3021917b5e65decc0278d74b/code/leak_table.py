"""Leakage ablation: selection-FA fitted on the held-out rows (leak) vs train-only (B_*), same reps/folds/targets.
usage: python leak_table.py <leak_run> <B_run> <out_name>  -> results/summary/leak_<out_name>.csv (nMSE, 95% CI, by selector x method x k)"""
import os, sys
import pandas as pd
from analysis_lib import per_model, boot_metric
RAW = os.path.join(os.path.dirname(__file__), '..', 'results', 'raw'); OUT = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')
leak, base, name = sys.argv[1:4]
l = pd.read_parquet(os.path.join(RAW, leak + '.parquet')); b = pd.read_parquet(os.path.join(RAW, base + '.parquet'))
b = b[b.rep <= l.rep.max()]
b = b[b.selector.isin(l.selector.unique()) & b.method.isin(l.method.unique()) & b.k.isin(l.k.unique())]
cs = []
for run, d in (('leak', l), ('train_only', b)):
    cs.append(boot_metric(per_model(d), ['selector', 'method', 'k'], 500, metric='nmse').assign(run=run))
c = pd.concat(cs)
c.to_csv(os.path.join(OUT, f'leak_{name}.csv'), index=False)
p = c[(c.method == 'krr') & c.selector.isin(['gv_fa', 'dopt', 'random']) & c.k.isin([2, 4, 8, 16])].pivot_table(index=['selector', 'k'], columns='run', values='est')
p['leak_gain'] = p.train_only - p.leak
print(name); print(p.round(3).to_string())
