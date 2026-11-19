"""Selection upper bound: oracle selection (O_* runs; uses the held-out model's own target scores, optimistic) next to random / gv_fa / dopt from the
matching B_* run restricted to the same repetitions (same folds and targets).
usage: python oracle_table.py <dataset> ...   (dataset = suffix of B_<dataset>/O_<dataset>, e.g. mteb_dense56)  -> results/summary/oracle_<dataset>.csv
"""
import os, sys
import pandas as pd
from analysis_lib import per_model, boot_metric

RAW = os.path.join(os.path.dirname(__file__), '..', 'results', 'raw'); OUT = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')

for ds in sys.argv[1:]:
    o = pd.read_parquet(os.path.join(RAW, f'O_{ds}.parquet'))
    b = pd.read_parquet(os.path.join(RAW, f'B_{ds}.parquet'))
    b = b[b.rep <= o.rep.max()]
    b = b[b.selector.isin(['random', 'gv_fa', 'dopt']) & b.method.isin(['mean', 'fa', 'ridge', 'krr']) & b.k.isin(o.k.unique())]
    d = pd.concat([b, o])
    g = per_model(d)
    c = boot_metric(g, ['selector', 'method', 'k'], 500, metric='nmse')
    c.to_csv(os.path.join(OUT, f'oracle_{ds}.csv'), index=False)
    print(ds, c[(c.method == 'krr') & c.k.isin([1, 2, 4, 8])].pivot(index='k', columns='selector', values='est').round(3).to_string())
