"""Wald s.e. (ties = half wins, from kstar_full) vs bootstrap s.e. of the same gap (boot_flip, frac = 1).
-> results/se_check.csv.  No new fits; pure join of two existing outputs."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as pv

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
k = pd.read_csv(os.path.join(RES, "kstar_full.csv"))
k = k[(k.claim == "C2") & (k.pert == "P1")][["board", "claim_id", "se", "z", "gap", "tie_rate"]]
b = pd.read_csv(os.path.join(RES, "boot_flip.csv"))
b = b[(b.claim == "C2") & (b.frac == 1.0)][["board", "claim_id", "gap_se_boot", "n_rep", "n_changed"]]
j = k.merge(b, on=["board", "claim_id"])
j["se_ratio_wald_over_boot"] = j.se / j.gap_se_boot
j["z_boot"] = j.gap / j.gap_se_boot
pv.save(j, "se_check.csv", "run_secheck.py", 0, [os.path.join(RES, "kstar_full.csv"), os.path.join(RES, "boot_flip.csv")])
print(j.groupby("board").se_ratio_wald_over_boot.agg(["count", "median", "min", "max"]).round(2))
