#!/usr/bin/env python3
"""Post-freeze analysis for experiment-repo#10(b): does a good cluster design leave little exposure variation (so that z and the
neighbour-treated fraction f cannot be separated)? For Bernoulli(0.5), Louvain-cluster and size-matched random-cluster designs at the resolutions of e4
on Stanford3, ego-Facebook and the SBM (world-0 graph of the first e4 SBM cell), over 200 assignments per design: Var(f) across units, the
pooled within-arm variance of f (Var(f | z): what identifies the coefficient on f once z is in the model), corr(z, f), and the share of units with f >= 0.9 or <= 0.1.
Joined with the OLS_f SD / RMSE of e4 (linear truth). -> results/tables/t18_exposure_variation.csv"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os
import numpy as np, pandas as pd
from netgate import designs
from netgate.experiments import EXPERIMENTS
from netgate.runner import get_graph, make_design

R = results_dir(); N_DRAWS = 200


def main():
    e4 = pd.read_csv(os.path.join(R, "summary", "e4.csv"))
    cells = EXPERIMENTS["e4"]()
    rows = []
    for gs in ["stanford3", "ego", "sbm:5000,50,20,0.8"]:
        seed = [c["seed"] for c in cells if c["graph"] == gs][0] * 1000
        g = get_graph(gs, seed)
        rng = np.random.default_rng(12345)
        for kd in ["bern", "louv", "rand"]:
            for res in ([None] if kd == "bern" else [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]):
                des = make_design("bern:0.5" if kd == "bern" else f"{kd}:{res},0.5", g, rng)
                acc = []
                for _ in range(N_DRAWS):
                    z = des.draw(g, rng)
                    if z.min() == z.max():
                        continue
                    f = g.W @ z
                    w = np.where(z == 1, f - f[z == 1].mean(), f - f[z == 0].mean())
                    acc.append((f.var(), (w ** 2).mean(), np.corrcoef(z, f)[0, 1], ((f >= 0.9) | (f <= 0.1)).mean()))
                a = np.mean(acc, axis=0)
                spec = "bern:0.5" if kd == "bern" else f"{kd}:{res},0.5"
                m = e4[(e4.graph == gs) & (e4.design == spec) & (e4.o_kind == "linear") & (e4.est_name == "OLS_f")]
                sd = rmse = np.nan
                if len(m):
                    sd, rmse = m.sd.iloc[0], m.rmse.iloc[0]
                rows.append(dict(graph=gs, design=kd, resolution=res if res else np.nan, n_clusters=len(np.unique(des.labels)) if kd != "bern" else g.n,
                                 var_f=a[0], var_f_within_arm=a[1], corr_z_f=a[2], share_f_extreme=a[3], ols_f_sd_e4=sd, ols_f_rmse_e4=rmse))
    T = pd.DataFrame(rows)
    T["within_arm_share_of_var_f"] = T.var_f_within_arm / T.var_f
    T.to_csv(os.path.join(R, "tables", "t18_exposure_variation.csv"), index=False)
    pd.set_option("display.width", 250)
    print(T.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
