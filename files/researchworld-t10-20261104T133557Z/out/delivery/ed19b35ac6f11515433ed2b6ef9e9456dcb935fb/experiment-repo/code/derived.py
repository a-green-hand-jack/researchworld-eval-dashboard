"""Derived tables from summary CSVs (output of summarize.py).

usage: derived.py SUMMARY_SYNTH.csv THEORY.csv OUT_THEORY_VS_MEASURED.csv
  theory_vs_measured: measured paired width ratio (Wald, vs ppi++) per scenario/n/rho next to the asymptotic prediction
  (theory_synth.csv), and the finite-n excess measured/predicted.
       derived.py --breakeven SUMMARY.csv OUT.csv [KEY]
  breakeven: for each (KEY = dataset or scenario, rho, method) the smallest n in the grid at which the like-for-like ratio's
  95% CI lies entirely below 1 (a significant gain) and the n at which it lies entirely above 1 (a significant loss);
  empty = never within the grid. Only adjusters (cf_*) are listed.
"""
import sys, numpy as np, pandas as pd

if sys.argv[1] == "--breakeven":
    s = pd.read_csv(sys.argv[2]); out = sys.argv[3]
    key = sys.argv[4] if len(sys.argv) > 4 else ("dataset" if "dataset" in s else "scenario")
    s = s[s.method.str.startswith("cf_")]
    grp = [key] + (["rho"] if "rho" in s else []) + ["method"]
    rows = []
    for g, d in s.groupby(grp):
        d = d.sort_values("n")
        win = d[d.ratio_lfl_hi < 1].n; loss = d[d.ratio_lfl_lo > 1].n
        rows.append({**dict(zip(grp, g)), "grid_n": " ".join(map(str, d.n)),
                     "ratio_lfl_by_n": " ".join(f"{r:.3f}" for r in d.ratio_lfl),
                     "first_n_significant_gain": win.min() if len(win) else np.nan,
                     "first_n_significant_loss": loss.min() if len(loss) else np.nan,
                     "n_gain_cells": len(win), "n_loss_cells": len(loss)})
    pd.DataFrame(rows).to_csv(out, index=False); print(len(rows), "rows ->", out)
else:
    s = pd.read_csv(sys.argv[1]); t = pd.read_csv(sys.argv[2]); out = sys.argv[3]
    t = t.rename(columns={"asym_width_ratio_vs_ppi++": "predicted_ratio"})
    t["rho"] = t.rho.round(4)
    s = s.copy(); s["rho"] = s.rho.round(4)
    m = s.merge(t, on=["scenario", "rho", "method"], how="inner")
    m["excess_over_prediction"] = m.ratio / m.predicted_ratio
    m = m[["scenario", "n", "N", "rho", "method", "reps", "ratio", "ratio_lo", "ratio_hi", "predicted_ratio", "excess_over_prediction"]]
    m.to_csv(out, index=False); print(len(m), "rows ->", out)
