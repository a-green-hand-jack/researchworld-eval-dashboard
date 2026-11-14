"""Synthetic study. usage: run_synth.py TAU OUT [M]"""
import sys, numpy as np, pandas as pd, itertools, time
from synth import make_pool; from run_grid import run
tau = float(sys.argv[1]); out = sys.argv[2]; M = int(sys.argv[3]) if len(sys.argv) > 3 else 500
ests = ["naive", "split", "crossfit", "boot_opt", "simul"]; dfs = []; t0 = time.time()
for rho in (0.0, 0.5, 0.9):
    Y = make_pool(64, 20000, m=0.3, tau=tau, rho=rho, seed=7)
    d = run(Y, 0, ["argmax", "sh", "greedy"], [100, 200, 400, 800], [1, 4, 16, 64], ests, M, seed=11, grid=(4, 4, 4),
            est_kw=dict(boot_opt=dict(B=100), simul=dict(B=200)), tag=f"tau={tau},rho={rho}")
    d["tau"] = tau; d["rho"] = rho; dfs.append(d); print("done rho", rho, time.time() - t0, flush=True)
    pd.concat(dfs).to_parquet(out)
