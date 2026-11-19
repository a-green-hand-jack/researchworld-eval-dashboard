"""Ladder-type thresholded reporting vs naive, synthetic, n x K x tau (rho=.5, base acc .3). usage: run_synth_ladder.py OUT"""
import sys, pandas as pd, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from run_grid import run
dfs = []
for tau in (0.0, 0.01, 0.03):
    Y = make_pool(128, 20000, m=0.3, tau=tau, rho=0.5, seed=7)
    d = run(Y, 0, ["argmax"], [100, 200, 500, 1000], [4, 16, 64, 128], ["naive", "ladder"], 1000, seed=77, tag=f"tau={tau}"); d["tau"] = tau; dfs.append(d)
    pd.concat(dfs).to_parquet(sys.argv[1]); print("done", tau, flush=True)
