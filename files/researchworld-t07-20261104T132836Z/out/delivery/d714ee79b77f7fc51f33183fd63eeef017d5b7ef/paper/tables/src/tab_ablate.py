"""C5: selection x predictor decomposition and latent-rank ablation (Q2).  Outputs: tables/ablate_design_n<n>.tex, tables/ablate_rank_n<n>.tex

Cells: RMSE relative to the random mean at the same n and protocol (geometric mean over the benchmarks that have the method;
95% benchmark-level bootstrap CI, the benchmark is the unit; HELM benchmarks share models).  The design x predictor grid uses the
experiment-repo ablation arms; `--` = arm not run.  Design: random items; difficulty-stratified systematic sampling (strat.);
PPS inclusion probabilities without stratification; both (the MASS design).  Predictor: sample mean; latent model + difference
correction (AIPW); latent+kNN ensemble + correction; ensemble without correction.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures", "src"))
import common as C

GRID = [  # (design label, [methods per predictor column])
    ("Random items", ["random", "aipw_rand", "aipw_ens", "ens_rand_nocorr"]),
    ("Stratified", ["strat_random", "aipw_strat", None, None]),
    ("PPS only", [None, "aipw_pps", None, None]),
    ("Stratified + PPS (MASS design)", ["mass_sel", "mass", "mass_ens", "mass_ens_nocorr"]),
]
COLS = ["sample mean", "latent + corr.", "ensemble + corr.", "ensemble, no corr."]
RANK = [("Random items + AIPW", ["aipw_k1", "aipw_rand", "aipw_k4"]), ("MASS (latent)", ["mass_k1", "mass", "mass_k4"])]
PROTOS = [("extrap", "Extrapolation"), ("random", "Interpolation")]


def cellval(c, proto, m):
    if m is None:
        return "--"
    piv = c[c.protocol == proto].pivot_table(index="bench", columns="method", values="mean")
    if m not in piv:
        return "--"
    r = (piv[m] / piv["random"]).dropna()
    if len(r) < 3:
        return "--"
    g = C.geomean_ci(r.values)
    return f"{g[0]:.2f} [{g[1]:.2f}, {g[2]:.2f}]"


def main(N=100):
    cells = C.load("cells.csv"); c = cells[(cells.metric == "rmse") & (cells.n == N)]
    os.makedirs(C.OUT_TAB, exist_ok=True)
    L = ["\\begin{tabular}{ll" + "c" * len(COLS) + "}", "\\toprule", "Protocol & Design & " + " & ".join(COLS) + " \\\\", "\\midrule"]
    for pi, (proto, pl) in enumerate(PROTOS):
        for di, (dl, ms) in enumerate(GRID):
            L.append((pl if di == 0 else "") + " & " + dl + " & " + " & ".join(cellval(c, proto, m) for m in ms) + " \\\\")
        if pi < len(PROTOS) - 1:
            L.append("\\midrule")
    L += ["\\bottomrule", "\\end{tabular}"]
    p = os.path.join(C.OUT_TAB, f"ablate_design_n{N}.tex"); open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)
    L = ["\\begin{tabular}{llccc}", "\\toprule", "Protocol & Method & rank $k=1$ & $k=2$ (default) & $k=4$ \\\\", "\\midrule"]
    for pi, (proto, pl) in enumerate(PROTOS):
        for ri, (rl, ms) in enumerate(RANK):
            L.append((pl if ri == 0 else "") + " & " + rl + " & " + " & ".join(cellval(c, proto, m) for m in ms) + " \\\\")
        if pi < len(PROTOS) - 1:
            L.append("\\midrule")
    L += ["\\bottomrule", "\\end{tabular}"]
    p = os.path.join(C.OUT_TAB, f"ablate_rank_n{N}.tex"); open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)


if __name__ == "__main__":
    main()
