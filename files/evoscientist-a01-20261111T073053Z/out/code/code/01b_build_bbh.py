"""Build the OLLB-BBH24 matrix from open-llm-leaderboard/results (latest results file per model directory):
24 BBH sub-tasks, metric acc_norm (x100). Keeps non-flagged models listed in the `contents` snapshot with all 24 sub-tasks."""
import os, json, glob
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = os.path.join(ROOT, 'data', 'ollb_results'); P = os.path.join(ROOT, 'data', 'processed')
cont = pd.read_csv(os.path.join(P, 'ollb_contents_full.csv'))
ok = set(cont[cont['Flagged'] == False]['fullname'])
rows = {}; files = sorted(glob.glob(os.path.join(R, '**', 'results_*.json'), recursive=True))
bad = 0
for f in files:
    model = os.path.relpath(os.path.dirname(f), R)
    if model not in ok: continue
    try: res = json.load(open(f))['results']
    except Exception: bad += 1; continue
    d = {k[len('leaderboard_bbh_'):]: v['acc_norm,none'] * 100 for k, v in res.items() if k.startswith('leaderboard_bbh_') and 'acc_norm,none' in v}
    if len(d) == 24: rows[model] = d
X = pd.DataFrame(rows).T.sort_index()
print('result files', len(files), 'unreadable', bad, '| models kept with all 24 subtasks:', len(X), '| subtasks:', X.shape[1])
X.to_csv(os.path.join(P, 'ollb_bbh24.csv'))
# sanity check: mean of the 24 sub-task scores vs `BBH Raw` in the contents snapshot
c = cont.drop_duplicates('fullname').set_index('fullname').loc[X.index]
print('corr(mean subtask acc_norm, contents BBH Raw*100) =', np.corrcoef(X.mean(axis=1), c['BBH Raw'] * 100)[0, 1],
      '; median abs diff =', float(np.median(np.abs(X.mean(axis=1) - c['BBH Raw'] * 100))))
