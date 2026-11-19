"""Breadth-depth frontiers. usage: run_frontier.py BOARD(helm|m6|m6raw|m39) OUT.csv [ntargets=30] [time_limit=30]
One row per (target, rule, incumbent mode, B, k): least cost (points, linear) of a plan touching at most k tasks."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import solvers as SV, rules as R
from lbprice.e1 import incumbents
from lbprice.boards import load_ollb
board, out = sys.argv[1], sys.argv[2]
ntar = int(sys.argv[3]) if len(sys.argv) > 3 else 30; tl = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
if board == "helm":
    df = pd.read_csv("data_proc/helm_mmlu_em.csv", index_col=0); S = df.values * 100.0; names = list(df.index); Aoff = S.mean(1)
else:
    b = load_ollb(board, slice_="main"); S = b["S"]; names = b["names"]; Aoff = b["official"] if "official" in b else S.mean(1)
sig = S.std(0); m = S.shape[1]
order = np.argsort(-Aoff, kind="stable"); targets = list(order[:ntar])
rows = []; t0 = time.time()
for ti, t in enumerate(targets):
    for mode in ("own", "common"):
        rivals = None if mode == "own" else incumbents(Aoff, t, 5)
        for rule in ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]:
            for B in (5.0, 10.0, 100.0):
                kw = dict(ceil=100.0, rivals=rivals, sigma=sig if rule == "zmean" else None, time_limit=tl)
                if rule == "median" and m % 2 == 0 and m > 12: continue
                fr = SV.frontier(rule, S, int(t), B, **kw)
                for k, cost, depth, feas in fr:
                    rows.append(dict(board=board, target=int(t), model=names[t], rank_official=ti + 1, rule=rule, incumbent=mode, B=B, k=k, depth=depth if feas else np.nan, feasible=feas))
    print(f"target {ti+1}/{len(targets)} t={time.time()-t0:.0f}", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows))
