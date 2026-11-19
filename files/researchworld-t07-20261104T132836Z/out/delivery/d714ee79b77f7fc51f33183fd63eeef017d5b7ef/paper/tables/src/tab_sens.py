"""C5: robustness table.  Output: tables/robustness_n100.tex

RMSE relative to the random mean at the same n=100 (geometric mean over benchmarks, 95% benchmark-level bootstrap CI) for the
main protocols and the dedup / family-out variants: `*_nodedup` keeps exact duplicate model rows (main runs remove them);
`family` holds out whole organisations (Open LLM Leaderboard benchmarks only, hence 7 benchmarks).  Rows: methods present in all
variants.  Each cell uses only the benchmarks run in that protocol (n_bench in the header).
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures", "src"))
import common as C

PROTOS = [("random", "Random"), ("random_nodedup", "Random, dups kept"), ("family", "Family-out"),
          ("extrap", "Extrap."), ("extrap_nodedup", "Extrap., dups kept")]
METHODS = ["sources_only", "ridge", "anchor_irt", "aipw_rand", "aipw_ens", "mass", "mass_ens"]
N = 100

if __name__ == "__main__":
    cells = C.load("cells.csv"); c = cells[(cells.metric == "rmse") & (cells.n == N)]
    L = ["\\begin{tabular}{l" + "c" * len(PROTOS) + "}", "\\toprule",
         "Method & " + " & ".join(f"{t} ({c[c.protocol == p].bench.nunique()})" for p, t in PROTOS) + " \\\\", "\\midrule"]
    for m in METHODS:
        row = []
        for p, _ in PROTOS:
            piv = c[c.protocol == p].pivot_table(index="bench", columns="method", values="mean")
            if m not in piv:
                row.append("--"); continue
            g = C.geomean_ci((piv[m] / piv["random"]).dropna().values)
            row.append(f"{g[0]:.2f} [{g[1]:.2f}, {g[2]:.2f}]")
        L.append(C.ml(m) + " & " + " & ".join(row) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    os.makedirs(C.OUT_TAB, exist_ok=True)
    p = os.path.join(C.OUT_TAB, f"robustness_n{N}.tex"); open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)
