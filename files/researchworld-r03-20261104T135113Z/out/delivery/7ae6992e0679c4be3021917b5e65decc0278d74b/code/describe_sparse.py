"""What the density filters do to the raw MTEB matrix (review item #10.1): raw size / observed fraction, and for each analysis matrix its size, share of the raw
observed cells it retains, task-type mix (share of tasks) vs raw, and the characteristics of the models kept vs dropped (release year, parameter count).
usage: python describe_sparse.py [DATA=/hutian/data]  -> results/summary/sparse_population.csv, sparse_population_types.csv
"""
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__); MAT = os.path.join(HERE, '..', 'data', 'matrices'); OUT = os.path.join(HERE, '..', 'results', 'summary')
DATA = sys.argv[1] if len(sys.argv) > 1 else '/hutian/data'
d = pd.read_parquet(os.path.join(DATA, 'processed', 'mteb_long.parquet'))
d = d[~d.task.isin(['CPUSpeedTask', 'GPUSpeedTask'])]; d = d[(d.score >= -1) & (d.score <= 1)]
M = d.groupby(['model_dir', 'task']).score.first().unstack()
tm = json.load(open(os.path.join(HERE, '..', 'data', 'mteb_task_meta.json')))
typ = pd.Series({t: tm.get(t, {}).get('type', 'unknown') for t in M.columns})
mm = pd.read_csv(os.path.join(MAT, 'mteb_dense_models.csv'), index_col=0)
rows, trows = [], []
nobs = int(M.notna().sum().sum())
rows.append(dict(matrix='raw', n_models=M.shape[0], n_tasks=M.shape[1], observed_cells=nobs, observed_frac=nobs / M.size, share_raw_cells=1.0,
                 median_tasks_per_model=float(M.notna().sum(1).median()), median_models_per_task=float(M.notna().sum(0).median())))
trows.append(pd.Series(typ.value_counts(normalize=True), name='raw'))
for n in ('mteb_dense56', 'mteb_dense', 'mteb_mid', 'mteb_sparse'):
    z = np.load(os.path.join(MAT, n + '.npz'), allow_pickle=True)
    Y = z['Y']; o = int((~np.isnan(Y)).sum())
    ms = pd.read_csv(os.path.join(MAT, n + '_models.csv'), index_col=0)
    rd = pd.to_datetime(ms['release_date'], errors='coerce')
    rows.append(dict(matrix=n, n_models=Y.shape[0], n_tasks=Y.shape[1], observed_cells=o, observed_frac=o / Y.size, share_raw_cells=o / nobs,
                     median_tasks_per_model=float(np.median((~np.isnan(Y)).sum(1))), median_models_per_task=float(np.median((~np.isnan(Y)).sum(0))),
                     median_release_year=float(rd.dt.year.median()), median_n_params_M=float(pd.to_numeric(ms['n_parameters'], errors='coerce').median() / 1e6),
                     share_models_of_raw=Y.shape[0] / M.shape[0], share_tasks_of_raw=Y.shape[1] / M.shape[1]))
    trows.append(pd.Series(typ.reindex(z['benches'].astype(str)).value_counts(normalize=True), name=n))
allm = pd.read_csv(os.path.join(MAT, 'mteb_sparse_models.csv'), index_col=0)
rd = pd.to_datetime(allm['release_date'], errors='coerce')
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sparse_population.csv'), index=False)
pd.concat(trows, axis=1).fillna(0).round(4).to_csv(os.path.join(OUT, 'sparse_population_types.csv'))
print(pd.DataFrame(rows).round(3).to_string()); print(pd.concat(trows, axis=1).fillna(0).round(3))
