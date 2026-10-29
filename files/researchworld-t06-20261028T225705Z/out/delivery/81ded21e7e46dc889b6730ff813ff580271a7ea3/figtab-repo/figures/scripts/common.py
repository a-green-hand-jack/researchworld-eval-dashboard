"""Readers for experiment-repo result files (results/SCHEMA.md). NaN budget = no attack found within 50% of N -> treated as +inf."""
import os, glob, numpy as np, pandas as pd
ORDER = ["arena55k", "mtbench_human", "mtbench_gpt4", "nba"]
def load(res, prefix):
    out = {}
    for k in ORDER:
        f = f"{res}/{prefix}_{k}.csv"
        if os.path.exists(f): out[k] = pd.read_csv(f)
    return out
def attack_budget(dec, decision, method, ptype):
    """Original-data budget_frac (replicate -1) and bootstrap 2.5/97.5 percentiles over replicates >= 0 (NaN counted as inf)."""
    d = dec[(dec.decision == decision) & (dec.method == method) & (dec.perturbation_type == ptype)]
    o = d[d.replicate < 0].budget_frac
    b = d[d.replicate >= 0].budget_frac.fillna(np.inf).to_numpy()
    est = float(o.iloc[0]) if len(o) else np.nan
    lo, hi = (np.percentile(b, [2.5, 97.5]) if len(b) else (np.nan, np.nan))
    return est, lo, hi, len(b)

SHORT = {"arena55k": "Arena 55k", "mtbench_human": "MT-Bench expert", "mtbench_gpt4": "MT-Bench GPT-4", "nba": "NBA"}
def th(n): return f"{int(n):,}".replace(",", "\\,")
def wrap(tabular, small="footnotesize"):
    """Self-contained fragment: \\footnotesize, tight column separation, so it fits the 5.5 in text width."""
    return "{\\" + small + "\\setlength{\\tabcolsep}{3pt}" + tabular.rstrip() + "}\n"
