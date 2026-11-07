"""Number of distinct target-benchmark draws per primary run (the fixed 25 % / 34 % held-out targets are redrawn once per repetition; with N <= 10 several repetitions repeat a draw).
usage: python target_draws.py -> results/summary/target_draws.csv"""
import os, json, math, glob
import numpy as np, pandas as pd
from run_cv import make_folds
H = os.path.dirname(__file__); rows = []
for f in sorted(glob.glob(os.path.join(H, '..', 'results', 'raw', 'B_*.json'))):
    c = json.load(open(f)); Y = np.load(os.path.join(H, '..', 'data', 'matrices', c['data'] + '.npz'), allow_pickle=True)['Y']; M, N = Y.shape
    if not c.get('target_frac'):
        continue
    ntar = max(1, int(round(c['target_frac'] * N))); sets = []
    for rep in range(c['reps']):
        rng = np.random.default_rng(c['seed'] * 1000 + rep); make_folds(c['split'], M, c['K'], rng)
        sets.append(tuple(sorted(int(x) for x in rng.choice(N, ntar, replace=False))))
    rows.append(dict(run=os.path.basename(f)[:-5], N=N, n_targets=ntar, reps=c['reps'], distinct_target_draws=len(set(sets)), possible_draws=f'{math.comb(N, ntar):.3e}'))
pd.DataFrame(rows).to_csv(os.path.join(H, '..', 'results', 'summary', 'target_draws.csv'), index=False); print(pd.DataFrame(rows).to_string())
