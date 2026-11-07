"""Usage: python scripts/run_e1.py --family dirichlet --D 5 --hetero 0 --pred linear --reps 100 --out results/e1/x.csv"""
import argparse, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cpc.data import World
from cpc.e1 import run_rep

ap = argparse.ArgumentParser()
ap.add_argument("--family"); ap.add_argument("--D", type=int); ap.add_argument("--hetero", type=int)
ap.add_argument("--pred"); ap.add_argument("--reps", type=int, default=100); ap.add_argument("--seed0", type=int, default=0)
ap.add_argument("--n_cal", type=int, default=500); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--out")
a = ap.parse_args()
world = World(a.family, a.D, a.hetero, seed=0)
rows = []
t0 = time.time()
for r in range(a.reps):
    out, meta = run_rep(world, a.pred, a.seed0 + r, n_cal=a.n_cal, eps=a.eps)
    for o in out:
        o.update(family=a.family, D=a.D, hetero=a.hetero, pred=a.pred, rep=a.seed0 + r, n_cal=a.n_cal, eps=a.eps, phi_hat=meta["phi_hat"])
        rows.append(o)
    print(f"rep {r} {time.time()-t0:.1f}s", flush=True)
os.makedirs(os.path.dirname(a.out), exist_ok=True)
pd.DataFrame(rows).to_csv(a.out, index=False)
