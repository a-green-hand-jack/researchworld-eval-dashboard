"""Table G (Q2a, Q2b): bias, RMSE, coverage of the nominal-95% interval, median width and item cost of each reporting method on the
real MMLU-Pro outcome matrix (T1; Qwen2.5-1.5B-Instruct, exhaustive search over K=300 candidates, n in {100, 500}, 1000 replicates per cell).
Replicates share items, so bias +- and the coverage interval are mean +- 1.96 x delete-a-block SE (10 blocks), not Wilson.
M3 rows come from the '|m3' cells (same design, M3 on). Reads results/methods_t1.parquet and runs_t1.parquet (block of each replicate).
Writes tables/table_g_t1_calibration.tex (all methods, n=100, 500), table_g_main.tex (compact: n=100, main methods), table_g_all_cells.csv."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

m = pd.read_parquet(common.path("methods_t1.parquet"))
blk = pd.read_parquet(common.path("runs_t1.parquet"), columns=["cell_id", "rep", "block"])
m = m.merge(blk, on=["cell_id", "rep"], validate="m:1")
m = m[m.procedure == "exhaustive"]
ORDER = ["M0", "M1_f0.2", "M1_f0.5", "M1_f0.8", "M2", "M3_opt", "M3_632", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder", "M5_ladder_se"]
is_m3 = m.cell_id.str.contains("|m3", regex=False)
t = common.method_stats(m[~is_m3], ["K", "n", "method"])
t3 = common.method_stats(m[is_m3], ["K", "n", "method"])
t3 = t3[t3.method.str.startswith("M3")]
t = pd.concat([t, t3])
t.to_csv(f"{common.TOUT}/table_g_all_cells.csv", index=False)

K = 300
MAIN = ["M0", "M1_f0.5", "M2", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder"]


def render(path, ns, methods):
    lines = [r"\begin{tabular}{rrlrrrrr}", r"\toprule",
             r"$K$ & $n$ & method & bias (pts) & RMSE (pts) & coverage & width (pts) & items \\", r"\midrule"]
    for n in ns:
        d = t[(t.K == K) & (t.n == n)].set_index("method").reindex([o for o in ORDER if o in methods and o in set(t[(t.K == K) & (t.n == n)].method)])
        for meth, r in d.iterrows():
            cov = "--" if pd.isna(r.get("cov")) else rf"{r['cov']:.3f} $\pm$ {(r.cov_hi - r.cov_lo) / 2:.3f}"
            w = "--" if pd.isna(r.get("width")) else f"{r.width:.1f}"
            lines.append(rf"{K} & {n} & {meth.replace('_', chr(92) + '_')} & {r.bias:+.2f} $\pm$ {1.96 * r.bias_se:.2f} & {r.rmse:.2f} & {cov} & {w} & {r.items_report:.0f} \\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines.append(r"\end{tabular}")
    open(path, "w").write("\n".join(lines) + "\n")


render(f"{common.TOUT}/table_g_t1_calibration.tex", [100, 500], ORDER)
render(f"{common.TOUT}/table_g_main.tex", [100], MAIN)
print("replicates per cell:", int(t.reps.min()), "-", int(t.reps.max()))
