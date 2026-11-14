"""Conditional vs hybrid (AKM) intervals for the argmax winner, synthetic pool. usage: run_hybrid.py OUT_CSV"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from run_grid import run, summarize
rows = []
for tau in (0.0, 0.01, 0.03):
    Y = make_pool(128, 20000, m=0.3, tau=tau, rho=0.5, seed=300 + int(tau * 1000))
    df = run(Y, 0, ["argmax"], [100, 200, 500], [4, 16, 64], ["naive", "cond", "hybrid", "simul"], M=500, seed=11, grid=None, est_kw=dict(simul=dict(B=200)), tag=f"hyb_tau{tau}")
    s = summarize(df).reset_index(); s["tau"] = tau; rows.append(s)
pd.concat(rows).to_csv(sys.argv[1], index=False)
