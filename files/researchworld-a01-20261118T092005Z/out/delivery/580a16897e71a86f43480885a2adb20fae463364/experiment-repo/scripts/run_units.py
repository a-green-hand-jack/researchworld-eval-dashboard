"""R5 unit check: the price of first place under four cost units. usage: run_units.py BOARD(helm|m6raw|m39) OUT.csv [shard n_shards] [ntargets=30]
units (cost of a plan delta; per-task cap):  points: sum delta, cap 5 pts | sigma: sum delta/sigma_j, cap 1 sigma_j | headroom: sum delta/(ceil-S_tj), cap 20% of headroom |
convex2: sum (delta/sigma_j)^2, cap 1 sigma_j.  Each unit is also run with no cap (ceilings only).  Own-leader incumbents; targets = top-N by the official score."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import solvers as SV
from lbprice.e1 import RULE_LIST
from lbprice.boards import load_helm, load_ollb
name, out = sys.argv[1], sys.argv[2]
shard, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
ntar = int(sys.argv[5]) if len(sys.argv) > 5 else 30
b = load_helm() if name == "helm" else load_ollb(name)
S = b["S"]; sig = S.std(axis=0); m = S.shape[1]; ceil = np.full(m, 100.0); wh = b.get("w_h")
rules = RULE_LIST + (["meanh"] if wh is not None else [])
top = list(np.argsort(-b["official"], kind="stable")[:ntar]); rows = []; t0 = time.time()
for i, t in enumerate(top):
    if i % ns != shard: continue
    head = ceil - S[t]
    UNITS = {"points": (np.ones(m), 1, np.full(m, 5.0)), "sigma": (1 / sig, 1, sig), "headroom": (1 / np.maximum(head, 1e-9), 1, 0.2 * head), "convex2": (1 / sig, 2, sig)}
    for unit, (kappa, gamma, cap) in UNITS.items():
        for capname, B in (("cap", cap), ("inf", np.full(m, 1e4))):
            for rule in rules:
                rr, w = ("mean", wh) if rule == "meanh" else (rule, None)
                kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, sigma=sig, w=w, time_limit=30.0)
                for obj in ("depth", "breadth"):
                    p = SV.price(rr, S, t, B, objective=obj, **kw)
                    rows.append(dict(board=name, target=int(t), model=b["names"][t], rank_official=i + 1, m=m, unit=unit, capname=capname, rule=rule, objective=obj,
                                     feasible=p["feasible"], cost=p["cost"], depth_points=p["depth"], breadth=p["breadth"] if p["feasible"] else np.nan,
                                     mip_gap=p["mip_gap"], verified=p["verified"], approx=bool(unit == "convex2" and rule == "copeland")))
    print(name, t, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
