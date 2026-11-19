"""k needed + theory check summaries. usage: summarize.py RESULTS_DIR"""
import sys, os, numpy as np, pandas as pd
out = sys.argv[1]; c = pd.read_csv(os.path.join(out, "curves.csv"))
rows = []
for (data, sel, inf), g in c[c.inf.isin(["ridge", "fa", "knn"])].groupby(["data", "sel", "inf"]):
    g = g.sort_values("k"); s0, smax = 0.0, g.skill.iloc[-1]
    for frac in (0.8, 0.9):
        ok = g[g.skill >= frac * smax]; rows.append((data, sel, inf, frac, int(ok.k.iloc[0]) if len(ok) else None, float(smax), int(g.k.iloc[-1])))
pd.DataFrame(rows, columns="data sel inf frac_of_max_skill k_needed skill_at_kmax kmax".split()).to_csv(os.path.join(out, "k_needed.csv"), index=False)
t = pd.read_csv(os.path.join(out, "theory_synth.csv"))
t["rel_gap_emp_vs_oracle"] = t.emp_fa_est / t.theory_oracle - 1
g = t.groupby(["r", "rho", "M", "sel", "k"])[["theory_oracle", "approx_psi_1_plus_r_over_k", "emp_fa_est", "floor"]].mean().reset_index()
g.to_csv(os.path.join(out, "theory_summary.csv"), index=False)
x = g[(g.sel == "random") & (g.r == 5) & (g.rho == 0.6)]
print(x.pivot_table(index=["M"], columns="k", values=["theory_oracle", "emp_fa_est"]).round(2).T.to_string())
print(pd.read_csv(os.path.join(out, "k_needed.csv")).query("sel in ['greedy_ridge','random'] and inf=='ridge' and frac_of_max_skill==0.9").to_string())
