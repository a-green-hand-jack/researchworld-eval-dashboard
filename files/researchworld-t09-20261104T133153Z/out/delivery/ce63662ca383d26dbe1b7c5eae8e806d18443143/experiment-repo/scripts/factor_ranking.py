#!/usr/bin/env python3
"""C3: one-factor sweeps around a default, same scale: RMSE of OLS_f (neighbour-fraction regression) at the extremes of each factor.
Default: SBM n=5000 mean degree 20, Bernoulli(0.5), concave spillover gamma=2 (e2) unless the factor needs another grid. -> results/tables/t11_factor_ranking.csv"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os
import numpy as np, pandas as pd

R = results_dir(); S = lambda e: pd.read_csv(os.path.join(R, "summary", f"{e}.csv"))
SBM = "sbm:5000,50,20,0.8"
e1, e2, e3, e5 = S("e1"), S("e2"), S("e3"), S("e5")
f = lambda d: d[d.est_name == "OLS_f"]
rows = []


def add(factor, grid, levels, d, key):
    d = f(d).set_index(key).sort_index(); r = d.rmse; b = d.bias
    rows.append(dict(factor=factor, grid=grid, levels=f"{r.index.min()} .. {r.index.max()}" if not isinstance(r.index.min(), str) else ", ".join(map(str, r.index)),
                     n_levels=len(r), rmse_min=r.min(), rmse_max=r.max(), ratio_max_min=r.max() / r.min(), lowest_level=str(r.idxmin()), highest_level=str(r.idxmax()),
                     bias_share_at_highest=float(b[r.idxmax()] ** 2 / r.max() ** 2), note=levels))


base = e2[(e2.graph == SBM) & (e2.o_kind == "concave")]
add("spillover shape (4)", "e2 SBM bern0.5", "linear/concave/convex/sigmoid, gamma=2", e2[(e2.graph == SBM) & (e2.design == "bern:0.5")], "o_kind")
add("treatment prob p (0.1, 0.5)", "e2 SBM concave", "Bernoulli", base[base.design.isin(["bern:0.5", "bern:0.1"])], "design")
add("design (Bernoulli / Louvain / random clusters)", "e2 SBM concave", "bern0.5, louv res1, rand res1", base[base.design.isin(["bern:0.5", "louv:1.0,0.5", "rand:1.0,0.5"])], "design")
add("graph family (6)", "e2 bern0.5 concave", "n,d differ by graph", e2[(e2.design == "bern:0.5") & (e2.o_kind == "concave")].assign(g=lambda d: d.graph), "g")
add("interference strength gamma (0..4)", "e1 SBM bern0.5 linear", "bias of OLS_f is ~0 here; RMSE is variance", e1[(e1.graph == SBM) & (e1.design == "bern:0.5")], "o_gamma")
a = e3[e3.graph.str.startswith("er:") & (e3.graph.str.contains(",20$"))].copy(); a["n"] = a.graph.str.extract(r"er:(\d+),")[0].astype(int)
add("sample size n (1k..20k)", "e3 ER d=20 bern0.5 linear", "variance only", a, "n")
a = e3[e3.graph.str.startswith("er:5000,")].copy(); a["d"] = a.graph.str.extract(r",(\d+)$")[0].astype(int)
add("mean degree d (5..80)", "e3 ER n=5000 bern0.5 linear", "variance only", a, "d")
a = e5[(e5.graph == SBM) & (e5.design == "bern:0.5") & (e5.o_alpha_graph == 1.0)]
add("noise sigma (0.25..4)", "e5 SBM bern0.5 alpha_graph=1", "linear", a, "o_sigma")
T = pd.DataFrame(rows).sort_values("ratio_max_min", ascending=False)
T.to_csv(os.path.join(R, "tables", "t11_factor_ranking.csv"), index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 60)
print(T.round(3).to_string(index=False))
