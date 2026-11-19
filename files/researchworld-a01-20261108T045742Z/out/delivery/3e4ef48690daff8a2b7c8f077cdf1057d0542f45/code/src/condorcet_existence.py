"""Does the ORIGINAL leaderboard have a Condorcet winner (a model beating every other on a strict majority of tasks)?
Also the Copeland-first model and whether it equals the mean-first model. Usage: python3 src/condorcet_existence.py OUT_CSV"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
rows = []
for ds in ["helm", "ollb", "ollb_raw", "ollb_nomerge", "ollb_top500"]:
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    # W[j,k] = #tasks where j beats k (ties half); majority margin matrix, vectorised over k
    wins = np.zeros((M, M), dtype=np.float32)
    for t in range(n):
        x = X[:, t]; wins += (x[:, None] > x[None, :]) + 0.5 * (x[:, None] == x[None, :])
    maj = wins > n / 2; np.fill_diagonal(maj, True)
    cw = np.where(maj.all(axis=1))[0]
    cop = (maj & ~np.eye(M, dtype=bool)).sum(axis=1) + 0.5 * ((wins == n / 2) & ~np.eye(M, dtype=bool)).sum(axis=1)
    mean_first = int(np.argmax(X.mean(axis=1)))
    rows.append(dict(dataset=ds, M=M, n=n, has_condorcet_winner=len(cw) > 0, condorcet_winner=names[cw[0]] if len(cw) else "",
                     mean_first=names[mean_first], mean_first_is_condorcet_winner=bool(mean_first in cw),
                     copeland_first=names[int(np.argmax(cop))], copeland_first_equals_mean_first=bool(int(np.argmax(cop)) == mean_first)))
pd.DataFrame(rows).to_csv(sys.argv[1], index=False); print(pd.DataFrame(rows).T.to_string())
