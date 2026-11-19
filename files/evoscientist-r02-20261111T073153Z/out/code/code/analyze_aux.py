"""Tables for predictor-quality ablation, cross-conformal comparison, and CIFAR-10H. Usage: python code/analyze_aux.py"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_common import *

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "pdf.fonttype": 42})
S = {}

# ---------------------------------------------------------------- predictor quality (K=5, n_cal=200)
if os.path.exists("results/synth_predq.csv"):
    d = pd.read_csv("results/synth_predq.csv")
    A = agg(d, ["dgp", "n_train", "method"], ["cov", "size_pool"])
    A.to_csv("results/summary_predq.csv", index=False)
    meths = ["l2", "hell", "kl", "ait", "l2n", "l2_mond"]
    lines = [r"\begin{tabular}{ll" + "r" * 4 + "}", r"\toprule", r"DGP & Score & " + " & ".join(f"$n_{{train}}$={n}" for n in [30, 100, 300, 3000]) + r" \\", r"\midrule"]
    for dg in DGPN:
        for m in meths:
            cells = []
            for n in [30, 100, 300, 3000]:
                r = A[(A.dgp == dg) & (A.n_train == n) & (A.method == m)].iloc[0]
                best = A[(A.dgp == dg) & (A.n_train == n) & A.method.isin(meths)].size_pool.min()
                s = f"{r.size_pool:.3f}"
                cells.append(r"\textbf{" + s + "}" if r.size_pool <= best * 1.0000001 else s)
            lines.append((DGPN[dg] if m == meths[0] else "") + f" & {NAMES[m]} & " + " & ".join(cells) + r" \\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
    open("tables/tab_predq.tex", "w").write("\n".join(lines))
    # best method per cell
    best = A[A.method.isin(meths)].loc[lambda x: x.groupby(["dgp", "n_train"]).size_pool.idxmin()][["dgp", "n_train", "method", "size_pool"]]
    print(best.to_string()); best.to_csv("results/summary_predq_best.csv", index=False)
    S["predq_cov_range"] = [float(A["cov"].min()), float(A["cov"].max())]

# ---------------------------------------------------------------- cross conformal
if os.path.exists("results/synth_cv.csv"):
    d = pd.read_csv("results/synth_cv.csv")
    A = agg(d, ["dgp", "N", "scheme", "method"], ["cov", "size_pool", "size_unif"])
    A.to_csv("results/summary_cv.csv", index=False)
    rows = []
    for (dg, N, m), g in d.groupby(["dgp", "N", "method"]):
        a = g[g.scheme == "cross"].set_index("rep"); b = g[g.scheme == "split"].set_index("rep")
        for col in ["size_pool", "size_unif", "cov"]:
            x = (a[col] - b[col]).to_numpy()
            rows.append(dict(dgp=dg, N=N, method=m, col=col, diff=x.mean(), hw=1.96 * x.std(ddof=1) / np.sqrt(len(x)),
                             rel=x.mean() / b[col].mean()))
    D = pd.DataFrame(rows); D.to_csv("results/summary_cv_paired.csv", index=False)
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule", r"DGP & Score & $N$ & cov. split & cov. cross & rel.\ size change \\", r"\midrule"]
    for dg in DGPN:
        for m in ["l2", "hell", "ait"]:
            for N in [60, 150, 400]:
                cs = A[(A.dgp == dg) & (A.N == N) & (A.method == m) & (A.scheme == "split")].iloc[0]
                cc = A[(A.dgp == dg) & (A.N == N) & (A.method == m) & (A.scheme == "cross")].iloc[0]
                r = D[(D.dgp == dg) & (D.N == N) & (D.method == m) & (D["col"] == "size_pool")].iloc[0]
                lines.append((DGPN[dg] if (m == "l2" and N == 60) else "") + f" & {NAMES[m] if N == 60 else ''} & {N} & {cs['cov']:.3f} & {cc['cov']:.3f} & {100 * r.rel:+.0f}\\% $\\pm$ {100 * r.hw / A[(A.dgp == dg) & (A.N == N) & (A.method == m) & (A.scheme == 'split')].iloc[0].size_pool:.0f} \\\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
    open("tables/tab_cv.tex", "w").write("\n".join(lines))
    S["cv_cov_min"] = float(A[A.scheme == "cross"]["cov"].min()); S["cv_cov_max"] = float(A[A.scheme == "cross"]["cov"].max())
    S["cv_rel_size_range"] = [float(D[D["col"] == "size_pool"].rel.min()), float(D[D["col"] == "size_pool"].rel.max())]
    S["cv_rel_size_mean_by_N"] = {int(k): float(v) for k, v in D[D["col"] == "size_pool"].groupby("N").rel.mean().items()}

# ---------------------------------------------------------------- CIFAR-10H
if os.path.exists("results/cifar10h.csv"):
    d = pd.read_csv("results/cifar10h.csv")
    A = agg(d, ["variant", "n_cal", "method"], ["cov", "size_pool", "q"])
    gaps = []
    for (v, n, m), g in d.groupby(["variant", "n_cal", "method"]):
        e, lo, hi, cov = group_gap(g, "ent", 3)
        ea, loa, hia, cova = group_gap(g, "arg", 10, min_n=1)
        z0 = g["g_zero0_c"].sum() / g["g_zero0_n"].sum(); z1 = g["g_zero1_c"].sum() / g["g_zero1_n"].sum()
        gaps.append(dict(variant=v, n_cal=n, method=m, ent_gap=e, ent_lo=lo, ent_hi=hi, arg_gap=ea, arg_lo=loa, arg_hi=hia,
                         cov_zero0=z0, cov_zero1=z1, ent_c0=cov[0], ent_c1=cov[1], ent_c2=cov[2],
                         zero_n0=g["g_zero0_n"].sum() / len(g), zero_n1=g["g_zero1_n"].sum() / len(g)))
    A = A.merge(pd.DataFrame(gaps), on=["variant", "n_cal", "method"])
    A.to_csv("results/summary_cifar10h.csv", index=False)
    meths = ORDER
    for n in [500]:
        lines = [r"\begin{tabular}{l" + "rrrr" * 2 + "}", r"\toprule",
                 r" & \multicolumn{4}{c}{raw softmax} & \multicolumn{4}{c}{temperature-scaled} \\",
                 r"Score & cov. & size & ent.-gap & arg-gap & cov. & size & ent.-gap & arg-gap \\", r"\midrule"]
        for m in meths:
            cells = []
            for v in ["raw", "ts"]:
                r = A[(A.variant == v) & (A.n_cal == n) & (A.method == m)].iloc[0]
                best = A[(A.variant == v) & (A.n_cal == n) & A.method.isin(meths)].size_pool.min()
                s = f"{r.size_pool:.3f}"
                cells += [f"{r['cov']:.3f}", r"\textbf{" + s + "}" if r.size_pool <= best * 1.0000001 else s, f"{r.ent_gap:.3f}", f"{r.arg_gap:.3f}"]
            lines.append(NAMES[m] + " & " + " & ".join(cells) + r" \\")
        lines += [r"\bottomrule", r"\end{tabular}"]
        open(f"tables/tab_cifar_{n}.tex", "w").write("\n".join(lines))
    # n_cal dependence table (size) for raw
    lines = [r"\begin{tabular}{l" + "rrr" * 2 + "}", r"\toprule", r" & \multicolumn{3}{c}{raw softmax} & \multicolumn{3}{c}{temperature-scaled} \\",
             r"Score & 100 & 500 & 2000 & 100 & 500 & 2000 \\", r"\midrule"]
    for m in meths:
        cells = []
        for v in ["raw", "ts"]:
            for n in [100, 500, 2000]:
                r = A[(A.variant == v) & (A.n_cal == n) & (A.method == m)].iloc[0]
                cells.append(f"{r.size_pool:.3f}")
        lines.append(NAMES[m] + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open("tables/tab_cifar_ncal.tex", "w").write("\n".join(lines))
    # eps sweep table
    lines = [r"\begin{tabular}{lrrrr}", r"\toprule", r"Score ($\varepsilon$) & cov. & size & $\hat q$ & ent.-gap \\", r"\midrule"]
    for m, lab in [("ait_eps1e-08", r"Aitchison ($10^{-8}$)"), ("ait_eps1e-06", r"Aitchison ($10^{-6}$)"), ("ait_eps0.0001", r"Aitchison ($10^{-4}$)"), ("ait_eps0.001", r"Aitchison ($10^{-3}$)"), ("ait", r"Aitchison ($10^{-2}$)"),
                   ("ait_eps0.1", r"Aitchison ($10^{-1}$)"), ("l2", r"$\ell_2$"), ("hell", "Hellinger")]:
        r = A[(A.variant == "raw") & (A.n_cal == 500) & (A.method == m)].iloc[0]
        lines.append(f"{lab} & {r['cov']:.3f} & {r.size_pool:.3f} & {r.q:.2f} & {r.ent_gap:.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open("tables/tab_cifar_eps.tex", "w").write("\n".join(lines))
    # figure: conditional coverage by entropy tercile & zero-in-Y for key methods (raw, n_cal=500)
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.0))
    for ax, v in zip(axs[:2], ["raw", "ts"]):
        for m in ["l2", "hell", "kl", "ait", "l2n", "l2_mond", "ait_mond"]:
            r = A[(A.variant == v) & (A.n_cal == 500) & (A.method == m)].iloc[0]
            ax.plot([0, 1, 2], [r.ent_c0, r.ent_c1, r.ent_c2], marker="o", ms=3, lw=0.9, label=PLAIN[m])
        ax.axhline(0.9, color="k", ls=":", lw=0.6); ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["low", "mid", "high"])
        ax.set_xlabel("entropy of $f(x)$"); ax.set_title(f"({'a' if v == 'raw' else 'b'}) CIFAR-10H, {v} softmax")
    axs[0].set_ylabel("coverage")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=7, frameon=False, fontsize=6)
    ax = axs[2]
    for m in ["l2", "hell", "ait"]:
        sub = A[(A.variant == "raw") & (A.method == m)].sort_values("n_cal")
        ax.errorbar(sub.n_cal, sub.size_pool, sub.size_pool_hw, marker="o", ms=3, lw=0.9, label=PLAIN[m])
    ax.set_xscale("log"); ax.set_xlabel("$n_{cal}$"); ax.set_ylabel("pool size"); ax.set_title("(c) size vs $n_{cal}$"); ax.legend(frameon=False)
    plt.tight_layout(rect=[0, 0.09, 1, 1]); plt.savefig("figures/fig_cifar.pdf"); plt.close()
    S["cifar_cov_range"] = [float(A["cov"].min()), float(A["cov"].max())]
    print(A[(A.n_cal == 500)][["variant", "method", "cov", "size_pool", "ent_gap", "arg_gap", "cov_zero0", "cov_zero1"]].round(3).to_string())
json.dump(S, open("results/summary_aux_misc.json", "w"), indent=1)
print(json.dumps(S, indent=1))
