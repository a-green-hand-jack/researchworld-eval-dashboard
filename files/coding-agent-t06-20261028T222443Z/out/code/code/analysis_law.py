"""Figure 1 (fragility law) and Table 3 (law regressions with board-clustered bootstrap CIs).

Usage: python code/analysis_law.py
Outputs: figs/fig_law.pdf, paper/tables/law.tex, results/law_summary.json
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_common import DESIGN_LABEL, DESIGN_ORDER, FIG, RES, TAB, load_pairs

COL = {"crowd": "#2a78d6", "expert": "#eb6834", "llm_judge": "#1baf7a", "sports": "#6250d6"}
MK = {"crowd": "o", "expert": "s", "llm_judge": "^", "sports": "D"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "legend.frameon": False})


def ols(X, y):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    r = y - X @ b
    return b, 1 - r.var() / y.var()


def cluster_boot(df, fn, B=1000, seed=0):
    rng = np.random.default_rng(seed)
    boards = df.board.unique()
    groups = {b: g for b, g in df.groupby("board")}
    out = []
    for _ in range(B):
        pick = rng.choice(boards, len(boards), replace=True)
        out.append(fn(pd.concat([groups[b] for b in pick])))
    return np.array(out)


def main():
    os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
    d = load_pairs()
    base = d[~d.noties & (d.z_ij > 0) & (d.kb >= 1)].copy()
    summ = {}
    rows = []
    for mode in ["drop", "flip", "add"]:
        x = base[base["mode"] == mode].copy()
        x3 = x[x.kb >= 3]

        def f_law(g):
            b, r2 = ols(np.c_[np.ones(len(g)), np.log(g.z_ij), np.log(g.Rm)], np.log(g.kb))
            b2, r22 = ols(np.c_[np.ones(len(g)), np.log(g.z_ij), np.log(g.n_loc)], np.log(g.kb))
            return np.r_[b, r2, b2, r22, np.median(g.ratio)]
        est = f_law(x3)
        bt = cluster_boot(x3, f_law, B=int(os.environ.get("NBOOT", 500)), seed=1)
        lo, hi = np.percentile(bt, [2.5, 97.5], axis=0)
        names = ["a", "b_z", "b_R", "R2", "a_n", "bz_n", "b_n", "R2_n", "med_ratio"]
        summ[mode] = {n: [float(e), float(l), float(h)] for n, e, l, h in zip(names, est, lo, hi)}
        summ[mode]["n_pairs"] = int(len(x3)); summ[mode]["n_boards"] = int(x3.board.nunique())
        # per design ratio medians with cluster CI
        for des in DESIGN_ORDER:
            g = x3[x3.design == des]
            if len(g) == 0:
                continue
            bt2 = cluster_boot(g, lambda h: np.median(h.ratio), B=int(os.environ.get("NBOOT", 500)), seed=2) if g.board.nunique() > 1 else np.array([np.median(g.ratio)])
            summ[mode]["ratio_" + des] = [float(np.median(g.ratio)), float(np.percentile(bt2, 2.5)),
                                          float(np.percentile(bt2, 97.5)), int(len(g)), int(g.board.nunique())]
            summ[mode]["Rn_" + des] = float(np.median(g.Rm / np.sqrt(g.n_loc)))
        # design dummies on top of log z, log R
        X = np.c_[np.ones(len(x3)), np.log(x3.z_ij), np.log(x3.Rm)]
        D = np.c_[[(x3.design == des).astype(float) for des in ["expert", "llm_judge", "sports"]]].T
        b_full, r2_full = ols(np.c_[X, D], np.log(x3.kb))
        summ[mode]["R2_with_design"] = float(r2_full)
        summ[mode]["design_coef"] = dict(zip(["expert", "llm_judge", "sports"], map(float, b_full[3:])))
        # share of pairs (all k>=1) within factor 1.5 of the prediction
        summ[mode]["within1.5_all"] = float(((x.ratio > 1 / 1.5) & (x.ratio < 1.5)).mean())
        summ[mode]["n_pairs_all"] = int(len(x))
        s = summ[mode]
        rows.append((mode, s))
    json.dump(summ, open(os.path.join(RES, "law_summary.json"), "w"), indent=1)

    # ---- LaTeX table
    def ci(v, fmt="{:.2f}"):
        return (fmt + " [" + fmt + ", " + fmt + "]").format(*v[:3])
    lines = [r"\begin{tabular}{lccc}", r"\toprule",
             r" & drop & flip & inject \\", r"\midrule"]
    def row(lbl, key, fmt="{:.2f}"):
        return lbl + " & " + " & ".join(ci(summ[m][key], fmt) for m in ["drop", "flip", "add"]) + r" \\"
    lines.append(row(r"slope on $\log z$", "b_z"))
    lines.append(row(r"slope on $\log R$", "b_R"))
    lines.append(row(r"$R^2$ ($\log z$, $\log R$)", "R2", "{:.3f}"))
    lines.append(row(r"slope on $\log n_{\mathrm{loc}}$ (with $\log z$)", "b_n"))
    lines.append(row(r"$R^2$ ($\log z$, $\log n_{\mathrm{loc}}$)", "R2_n", "{:.3f}"))
    lines.append(r"$R^2$ adding design indicators & " + " & ".join("{:.3f}".format(summ[m]["R2_with_design"]) for m in ["drop", "flip", "add"]) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\multicolumn{4}{l}{median $k^\star/(z R)$ [board-cluster 95\% CI]} \\")
    for des in DESIGN_ORDER:
        cells = []
        for m in ["drop", "flip", "add"]:
            v = summ[m].get("ratio_" + des)
            cells.append("{:.2f} [{:.2f}, {:.2f}]".format(*v[:3]) if v else "--")
        nb = summ["drop"]["ratio_" + des]
        lines.append(r"\quad {} ({} pairs, {} boards) & ".format(DESIGN_LABEL[des], nb[3], nb[4]) + " & ".join(cells) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"pairs within $\times1.5$ of $zR$ (all $k^\star\ge1$) & " + " & ".join("{:.0f}\\%".format(100 * summ[m]["within1.5_all"]) for m in ["drop", "flip", "add"]) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "law.tex"), "w").write("\n".join(lines) + "\n")

    # ---- Figure 1
    x = base[base["mode"] == "drop"]
    fig, ax = plt.subplots(1, 2, figsize=(6.75, 2.6))
    for des in ["sports", "crowd", "llm_judge", "expert"]:
        g = x[x.design == des]
        kw = dict(s=9 if des != "expert" else 18, marker=MK[des], color=COL[des], alpha=0.55 if des == "sports" else 0.8,
                  linewidths=0.3, edgecolors="white", label=DESIGN_LABEL[des], rasterized=True)
        ax[0].scatter(g.z_ij, 100 * g.alpha, **kw)
        ax[1].scatter(g.pred, g.kb, **kw)
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel(r"statistical evidence $z = \hat\Delta/\mathrm{SE}$")
    ax[0].set_ylabel(r"worst-case drop, % of all data ($100\,k^\star/N$)")
    ax[0].set_title("(a) global fraction: designs separate", fontsize=8, loc="left")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    lim = [0.3, 5e3]
    ax[1].plot(lim, lim, color="#52514e", lw=1, ls="--")
    ax[1].text(900, 330, r"$k^\star = zR$", color="#52514e", fontsize=7, ha="left")
    ax[1].set_xlim(lim); ax[1].set_ylim(0.7, 5e3)
    ax[1].set_xlabel(r"prediction $z\cdot R$ (from one BT fit)")
    ax[1].set_ylabel(r"verified worst-case drop count $k^\star$")
    ax[1].set_title("(b) count vs. $zR$: designs collapse", fontsize=8, loc="left")
    ax[1].legend(loc="upper left", fontsize=7, handletextpad=0.2, markerscale=1.3)
    for a in ax:
        a.grid(True, which="major", color="#e6e5e0", lw=0.5)
        a.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_law.pdf"), dpi=300)
    fig.savefig(os.path.join(FIG, "fig_law.png"), dpi=150)
    print(json.dumps({m: {k: summ[m][k] for k in ["b_z", "b_R", "R2", "b_n", "R2_n", "R2_with_design", "med_ratio", "within1.5_all"]} for m in summ}, indent=1))
    print({m: {des: summ[m].get("ratio_" + des) for des in DESIGN_ORDER} for m in summ})
    print({m: {des: summ[m].get("Rn_" + des) for des in DESIGN_ORDER} for m in summ})


if __name__ == "__main__":
    main()
