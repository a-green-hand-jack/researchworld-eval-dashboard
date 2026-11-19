"""Table C (Q2a, Q2b): bias, RMSE, coverage of the nominal-95% interval, median width and item cost of each reporting method, T0.
bias/RMSE are against the method's own target (theta_target); coverage carries its Wilson 95% interval over replicates.
Main grid (1000 replicates per cell; worst case tau=0, K=200, and tau=0.1; n in {100, 500}) -> tables/table_c_calibration.tex.
The extra '|m3' cells (300 replicates; the only cells with the M3 bootstrap methods; n=200, K=200) -> tables/table_c_m3.tex.
Compact main-text version (K=200, n=100, selected methods) -> tables/table_c_main.tex.
Every main-grid cell -> tables/table_c_all_cells.csv. Reads results/methods_t0.parquet."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

m_all = pd.read_parquet(common.path("methods_t0.parquet"))
is_main = ~m_all.cell_id.str.contains("|m3", regex=False)
keys = ["tau", "K", "n", "method"]
ORDER = ["M0", "M1_f0.2", "M1_f0.5", "M1_f0.8", "M2", "M3_opt", "M3_632", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder", "M5_ladder_se"]


def render(sel, path, methods=None):
    lines = [r"\begin{tabular}{llrrrrrr}", r"\toprule",
             r"$\tau$ & $n$ & method & bias (pts) & RMSE (pts) & coverage [Wilson 95\%] & width (pts) & items for report \\", r"\midrule"]
    for (tau, n), d in sel.groupby(["tau", "n"]):
        d = d.set_index("method").reindex([o for o in ORDER if o in set(d.method) and (methods is None or o in methods)])
        for meth, r in d.iterrows():
            cov = "--" if pd.isna(r.get("cov")) else rf"{r['cov']:.3f} [{r.cov_lo:.3f}, {r.cov_hi:.3f}]"
            w = "--" if pd.isna(r.get("width")) else f"{r.width:.1f}"
            lines.append(rf"{tau:g} & {n} & {meth.replace('_', chr(92) + '_')} & {r.bias:+.2f} $\pm$ {1.96 * r.bias_se:.2f} & {r.rmse:.2f} & {cov} & {w} & {r.items_report:.0f} \\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines.append(r"\end{tabular}")
    open(path, "w").write("\n".join(lines) + "\n")


t = common.method_stats(common.reference(m_all[is_main]), keys)
t.to_csv(f"{common.TOUT}/table_c_all_cells.csv", index=False)
render(t[(t.K == 200) & t.tau.isin([0.0, 0.1]) & t.n.isin([100, 500])], f"{common.TOUT}/table_c_calibration.tex")
MAIN = ["M0", "M1_f0.5", "M2", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder"]
render(t[(t.K == 200) & t.tau.isin([0.0, 0.1]) & (t.n == 100)], f"{common.TOUT}/table_c_main.tex", MAIN)
t3 = common.method_stats(m_all[~is_main], keys)
render(t3[(t3.K == 200) & t3.tau.isin([0.0, 0.1]) & (t3.n == 200)], f"{common.TOUT}/table_c_m3.tex")
print("replicates per cell: main", int(t.reps.min()), "-", int(t.reps.max()), "; m3", int(t3.reps.min()), "-", int(t3.reps.max()))
