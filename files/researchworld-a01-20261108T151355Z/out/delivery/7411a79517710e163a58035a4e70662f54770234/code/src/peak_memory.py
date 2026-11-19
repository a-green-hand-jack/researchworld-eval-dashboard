"""Peak resident memory (ru_maxrss of a fresh process) of the ordinal MILP solvers at full OLLB size (M=4496 models) for a mid-table and a tail target, ceil and gain10 caps.
Writes results/summary/peak_memory.csv.  Usage: python3 src/peak_memory.py"""
import sys, subprocess, resource, json, pathlib, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1] / "results"
CODE = """
import sys, time, resource; sys.path.insert(0, 'src')
import numpy as np
from scipy.stats import rankdata
from mti import data as dt, ordinal as od
X, names, tasks, meta = dt.load('ollb'); rk = rankdata(-X.mean(axis=1), method='min'); i = int(np.where(rk == int(sys.argv[2]))[0][0])
t0 = time.time(); out = od.min_investment_ordinal(sys.argv[1], X, i, dt.make_cap(sys.argv[3], X, i), 1e-3)
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, time.time() - t0)
"""
rows = []
for rule in ("borda", "condorcet", "plurality"):
    for rank in (20, 1000):
        for cap in ("ceil", "gain10"):
            r = subprocess.run([sys.executable, "-c", CODE, rule, str(rank), cap], capture_output=True, text=True, cwd=R.parent)
            mb, s = map(float, r.stdout.split()) if r.returncode == 0 else (float("nan"),) * 2
            rows.append(dict(rule=rule, target_rank_mean=rank, cap=cap, peak_rss_mb=round(mb), wall_s=round(s, 1), M=4496)); print(rows[-1], flush=True)
base = subprocess.run([sys.executable, "-c", "import sys,resource; sys.path.insert(0,'src')\nfrom mti import data as dt, ordinal as od\nX=dt.load('ollb')[0]\nprint(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)"], capture_output=True, text=True, cwd=R.parent)
rows.append(dict(rule="(load data only)", target_rank_mean=0, cap="-", peak_rss_mb=round(float(base.stdout)), wall_s=0.0, M=4496))
pd.DataFrame(rows).to_csv(R / "summary" / "peak_memory.csv", index=False)
