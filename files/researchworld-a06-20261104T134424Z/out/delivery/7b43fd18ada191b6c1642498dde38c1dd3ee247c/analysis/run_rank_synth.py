"""Ranking flips among tuned systems, synthetic pool. usage: run_rank_synth.py OUT_CSV"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from run_grid import run_rank
rows = []
for tau in (0.0, 0.01, 0.03):
    Y = make_pool(128, 20000, m=0.3, tau=tau, rho=0.5, seed=400 + int(tau * 1000))
    for name, Ks in (("equal_K16", [16] * 5), ("unequal_K4_64", [4, 8, 16, 32, 64])):
        df = run_rank(Y, Ks, ["argmax"] * 5, [100, 200, 500], 500, 21, tag=f"rank_{name}_tau{tau}")
        g = df.groupby(["n", "est_name"]).agg(tau_mean=("tau", "mean"), top1=("top1", "mean"), wrong_order_1pp=("wrong_order_1pp", "mean"),
              big_reported_best=("big_reported_best", "mean"), big_truly_best=("big_truly_best", "mean"), range_true=("range_true", "mean"), reps=("tau", "size")).reset_index()
        g["tau_sd"] = df.groupby(["n", "est_name"]).tau.std().values; g["tau_gen"] = tau; g["design"] = name; g["Ks"] = str(Ks); rows.append(g)
pd.concat(rows).to_csv(sys.argv[1], index=False)
