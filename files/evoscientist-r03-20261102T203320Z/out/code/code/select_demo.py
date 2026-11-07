"""Descriptive: which benchmarks does each selection rule pick when fitted on ALL rows (in-sample, for illustration only,
not part of any accuracy claim).  Usage: PYTHONPATH=code python code/select_demo.py -> results/summary_selected.json"""
import json
import numpy as np, pandas as pd
import bsp

out = {}
for data, kmax, rc in [("olb", 3, 3), ("helm", 4, 3), ("livebench", 4, 3), ("mteb_mid", 6, 8), ("mteb_dense", 6, 8)]:
    D = pd.read_csv(f"data/processed/{data}.csv", index_col=0)
    Y = D.values.astype(float)
    mu, sd = bsp.fit_std(Y); Z = (Y - mu) / sd
    V, psi = bsp.fa_em(Z, rc)
    Sg = bsp.shrink_cov(bsp.pairwise_corr(Z), 0.05)
    C = np.arange(D.shape[1])
    out[data] = dict(r=rc, greedy_iopt=[D.columns[i] for i in bsp.sel_greedy_iopt(C, kmax, V, psi)],
                     cov_greedy=[D.columns[i] for i in bsp.sel_cov_greedy(C, kmax, Sg)],
                     top_communality=[D.columns[i] for i in bsp.sel_top_load(C, kmax, V, psi)])
json.dump(out, open("results/summary_selected.json", "w"), indent=1)
print(json.dumps(out, indent=1))
