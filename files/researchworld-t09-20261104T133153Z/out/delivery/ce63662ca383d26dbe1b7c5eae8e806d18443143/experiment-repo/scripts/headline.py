#!/usr/bin/env python3
"""Headline numbers with Monte-Carlo SEs, each with the file and rows it comes from -> results/tables/t12_headline_numbers.csv.
bias_se is the larger of the replicate-level and the between-world SE; coverage SE = sqrt(c(1-c)/n_rep)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os
import numpy as np, pandas as pd

R = results_dir(); S = lambda e: pd.read_csv(os.path.join(R, "summary", f"{e}.csv"))
SBM = "sbm:5000,50,20,0.8"; rows = []


def add(claim, f, sel, quantity, v, se, regime):
    rows.append(dict(claim=claim, source=f"results/summary/{f}.csv", rows=sel, quantity=quantity, value=v, mc_se=se, regime=regime))


e10 = S("e10")
for des in ["bern:0.1", "bern:0.5"]:
    for n in [1000, 20000]:
        r = e10[(e10.graph.str.startswith(f"sbm:{n},")) & (e10.o_kind == "concave") & (e10.design == des) & (e10.est_name == "OLS_f")].iloc[0]
        add("H3", "e10", f"graph=sbm n={n}, concave, {des}, OLS_f", "bias", r.bias, r.bias_se, "SBM d=20, gamma=2, GATE=3, 4 worlds x 100")
e1 = S("e1")
for g in ["sbm:5000,50,20,0.8", "ba:5000,10", "stanford3", "ego"]:
    r = e1[(e1.graph == g) & (e1.design == "bern:0.5") & (e1.o_gamma == 4.0) & (e1.est_name == "DM")].iloc[0]
    add("H6", "e1", f"graph={g}, bern:0.5, gamma=4, DM", "bias (GATE=5)", r.bias, r.bias_se, "linear truth")
    r = e1[(e1.graph == g) & (e1.design == "bern:0.5") & (e1.o_gamma == 0.0)]
    a, b = r[r.est_name == "OLS_f"].iloc[0], r[r.est_name == "DM"].iloc[0]
    add("C2", "e1", f"graph={g}, bern:0.5, gamma=0", "SD(OLS_f)/SD(DM)", a.sd / b.sd, np.nan, "SD has no MC SE reported; ratio of two SDs of ~400 draws (relative SE ~ 5% each)")
e2 = S("e2")
for g in ["sbm:5000,50,20,0.8", "stanford3", "ego"]:
    for des in ["bern:0.5", "bern:0.1", "louv:1.0,0.5"]:
        r = e2[(e2.graph == g) & (e2.design == des) & (e2.o_kind == "sigmoid") & (e2.est_name == "OLS_f")].iloc[0]
        add("C6", "e2", f"graph={g}, {des}, sigmoid, OLS_f", "bias (GATE=3)", r.bias, r.bias_se, "gamma=2")
e4 = S("e4")
for g in ["stanford3", "ego", "sbm:5000,50,20,0.8"]:
    for des in ["louv:1.0,0.5", "rand:1.0,0.5"]:
        r = e4[(e4.graph == g) & (e4.design == des) & (e4.o_kind == "linear") & (e4.est_name == "OLS_f")].iloc[0]
        add("H5", "e4", f"graph={g}, {des}, linear, OLS_f", "RMSE", r.rmse, np.nan, "bias_se=%.3f, bias=%+.3f" % (r.bias_se, r.bias))
e6 = S("e6"); e6 = e6[(e6.est_name == "OLS_f") & (e6.design == "bern:0.5") & (e6.tag.str.endswith("acl1.0"))]
for kind in ["linear", "concave"]:
    for g in ["sbm:5000,50,20,0.8", "stanford3", "ego"]:
        r = e6[(e6.o_kind == kind) & (e6.graph == g)].iloc[0]
        for c in ["cov_hc", "cov_cl", "cov_hac2"]:
            if pd.notna(r[c]):
                add("H7", "e6", f"graph={g}, bern:0.5, analysis res 1.0, {kind}, OLS_f", c, r[c], np.sqrt(r[c] * (1 - r[c]) / r.n_rep), "95% CI; SE is binomial over replicates (worlds correlated: treat as lower bound)")
T = pd.read_csv(os.path.join(R, "summary", "theory_vs_sim_e9.csv"))
add("H2", "theory_vs_sim_e9", "all 144 cells", "max |bias - exact prediction|", (T.bias - T.pred_exact).abs().max(), np.nan, "median bias_se of those cells = %.4f" % T.bias_se.median())
D = pd.DataFrame(rows); D.to_csv(os.path.join(R, "tables", "t12_headline_numbers.csv"), index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 70); print(D.round(4).to_string(index=False))
