"""Shared feature construction for the price predictors (E4): rule-specific gap, target and incumbent dispersion, profile correlation, initial rank."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from lbprice.boards import load_helm, load_ollb
BM = {"helm_mmlu": load_helm, "ollb_bench": lambda: load_ollb("m6"), "ollb_sub": lambda: load_ollb("m39")}


def features(board, d):
    b = BM[board](); S = b["S"]; ix = {n: i for i, n in enumerate(b["names"])}
    t = np.array([int(x) for x in d.target]); l = np.array([ix[x] for x in d.incumbent_id])
    z = (S - S.mean(0)) / S.std(0)
    out = d.copy()
    out["tdisp"] = S[t].std(1); out["ldisp"] = S[l].std(1)
    out["corr"] = [np.corrcoef(z[a], z[c])[0, 1] for a, c in zip(t, l)]
    out["lgap"] = np.log(out.gap.clip(lower=1e-9)); out["lrank"] = np.log(out.init_rank)
    return out
