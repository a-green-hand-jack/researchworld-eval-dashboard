"""E7 (Tier C, appendix): sensitivity of the price to the margin and to the board slice, on the OLLB benchmark board (m=6, `contents`).
usage: run_e7.py OUT.csv [shard n_shards] [ntargets=30]
Variants: margin in {1e-6, 0.1, 1.0} points (eps_task = eps: a boosted score must exceed a rival's by this; eps_agg = eps for the score aggregates, eps / mean(sigma_j) for zmean (z units); rank rules need a strict win only) on the main slice;
slice = all rows (merged and flagged models and models off the hub kept as rivals; the targets are the same models); budgets B in {5, 10, 100 (= uncapped)} points; objectives depth and breadth; own leader.
Targets: the top ntargets of the main slice under the official mean."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import solvers as SV, rules as R_
from lbprice.boards import load_ollb
out = sys.argv[1]; shard, ns = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
ntar = int(sys.argv[4]) if len(sys.argv) > 4 else 30
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]
bm, ba = load_ollb("m6", "main"), load_ollb("m6", "all")
top = list(np.argsort(-bm["official"], kind="stable")[:ntar]); idx_all = {n: i for i, n in enumerate(ba["names"])}
variants = [("main", bm, 1e-6), ("main", bm, 0.1), ("main", bm, 1.0), ("all_rows", ba, 1e-6)]
rows = []; t0 = time.time(); k = 0
for rank, t in enumerate(top):
    k += 1
    if (k - 1) % ns != shard: continue
    for slice_, b, eps in variants:
        S = b["S"]; sig = S.std(axis=0)
        tt = t if b is bm else idx_all[bm["names"][t]]
        for rule in RULES:
            A = R_.scores(S, rule, sigma=sig if rule == "zmean" else None, kw_cache=True).astype(float)
            for B in (5.0, 10.0, 100.0):
                for obj in ("depth", "breadth"):
                    p = SV.price(rule, S, tt, B, ceil=100.0, objective=obj, eps_agg=eps / (sig.mean() if rule == "zmean" else 1.0), eps_task=eps, sigma=sig if rule == "zmean" else None, time_limit=30.0)
                    rows.append(dict(board="m6", slice=slice_, eps=eps, target=int(t), model=bm["names"][t], rank_official=rank + 1, rule=rule, rank_rule=int((A > A[tt]).sum() + 1), B=B, objective=obj,
                                     feasible=bool(p["feasible"]), depth=p["depth"] if p["feasible"] else np.nan, breadth=p["breadth"] if p["feasible"] else np.nan, verified=p["verified"], status=p["status"], N=S.shape[0]))
    print(rank, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
