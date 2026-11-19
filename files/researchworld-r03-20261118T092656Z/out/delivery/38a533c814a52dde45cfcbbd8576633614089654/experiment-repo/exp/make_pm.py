"""Compact per-model table (mean over repetitions per held-out model x k x selector x method) so that the analyses can be re-run without the
raw records (about 380 MB). python3 -I exp/make_pm.py DIR [DIR ...]   ->  DIR/per_model.parquet
Columns: model (row index in the setting's matrix), k, selector, method, mse, mae_raw, spear, pw_acc (MTEB and small LLM matrices);
mse only for OLMB6 / OLMB40 (size)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import pandas as pd
import analysis as A

for d in sys.argv[1:]:
    pm = A.per_model(A.load(d))
    cols = ['mse'] if os.path.basename(d.rstrip('/')) in ('OLMB6', 'OLMB40') else ['mse', 'mae_raw', 'spear', 'pw_acc']
    q = pm[['model', 'k', 'selector', 'method'] + cols].copy()
    for c in cols: q[c] = q[c].astype('float32')
    q['model'] = q.model.astype('int32'); q['k'] = q.k.astype('int16')
    for c in ('selector', 'method'): q[c] = q[c].astype('category')
    q.to_parquet(f'{d}/per_model.parquet', compression='zstd', compression_level=15)
    print(d, len(q), round(os.path.getsize(f'{d}/per_model.parquet') / 1e6, 2), 'MB')
