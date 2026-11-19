"""Figures for the paper (PDF, written to /work/paper/figures).

Palette: categorical hues from the validated default palette (light surface), distinct marker
shapes as secondary encoding, a legend for every multi-series panel.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/work/paper/figures"
os.makedirs(OUT, exist_ok=True)

COL = {"cf_spline": "#2a78d6", "cf_hgb": "#eb6834", "cf_linear": "#1baf7a",
       "sppi": "#eda100", "ppi": "#e87ba4", "cf_spline_X": "#6250d6", "ppi_linear_X": "#52514e"}
MK = {"cf_spline": "o", "cf_hgb": "s", "cf_linear": "^", "sppi": "D", "ppi": "v",
      "cf_spline_X": "o", "ppi_linear_X": "x"}
LABEL = {"cf_spline": "CF calibrator: spline (primary)", "cf_hgb": "CF calibrator: boosting",
         "cf_linear": "CF calibrator: linear", "sppi": "Stratified PPI",
         "ppi": "PPI (lambda=1)", "cf_spline_X": "CF spline, with covariates",
         "ppi_linear_X": "PPI++ linear, with covariates"}

plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
                     "legend.fontsize": 6.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e6e3", "grid.linewidth": 0.5,
                     "lines.linewidth": 1.0, "lines.markersize": 3.2,
                     "pdf.fonttype": 42})


def synth_fig():
    s = pd.read_csv("/work/results/synth_main_summary.csv")
    raw = pd.read_csv("/work/results/synth_main.csv")
    th = pd.read_csv("/work/results/theory_check.csv")
    scen_names = {"lin": "linear calibrator\n(no gain)", "nl": "nonlinear calibration",
                  "bin": "binary outcome", "xonly": "covariate beyond $f$",
                  "heavy": "heavy-tailed noise"}
    scens = ["lin", "nl", "bin", "xonly", "heavy"]
    fig, axes = plt.subplots(1, 5, figsize=(7.0, 1.9), sharey=False)
    ns = [50, 100, 200, 500, 1000]
    for ax, sc in zip(axes, scens):
        sub = s[(s.scenario == sc) & (s.ratio == 4)]
        methods = ["cf_spline", "cf_hgb", "cf_linear", "sppi", "ppi"]
        if sc == "xonly":
            methods = ["cf_spline", "cf_spline_X"]
        for m in methods:
            t = sub[sub["method"] == m].sort_values("n")
            if len(t) == 0:
                continue
            ax.plot(t.n, t.width_ratio_vs_ppi_pp, marker=MK[m], color=COL[m], label=LABEL[m],
                    markerfacecolor="white" if m == "sppi" else COL[m])
        # efficient bound (oracle calibrator), from theory_check at N/n = 4
        info = "X" if sc == "xonly" else "f"
        b = th[(th.scenario == sc) & (th["info"] == info) & (th["method"] == "oracle_s0.0") & (th.ratio == 4)]
        b = b.sort_values("n")
        ax.plot(b.n, b.width_ratio_pred, ls="--", color="#1d1d1b", lw=0.9,
                label="efficient bound (oracle)")
        ax.axhline(1.0, color="#52514e", lw=0.6)
        ax.set_xscale("log")
        ax.set_xticks([50, 200, 1000])
        ax.set_xticklabels(["50", "200", "1000"], rotation=0)
        ax.minorticks_off()
        ax.set_title(scen_names[sc])
        ax.set_xlabel("labeled $n$ ($N=4n$)")
    axes[0].set_ylabel("CI width / PPI++ width")
    handles, labels = [], []
    for ax in axes:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in labels:
                handles.append(hh); labels.append(ll)
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(f"{OUT}/fig_synth.pdf", bbox_inches="tight")
    fig.savefig(f"/work/results/preview_fig_synth.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def real_fig():
    raw = pd.read_csv("/work/results/real_main.csv")
    th = pd.read_csv("/work/results/theory_pool.csv")
    cfgs = [("galaxies", "f"), ("forest", "f"), ("gene_expression", "f"), ("alphafold", "f"),
            ("alphafold", "fX"), ("census_income", "f"), ("census_income", "fX"),
            ("census_healthcare", "f"), ("census_healthcare", "fX"),
            ("census_education", "f"), ("census_education", "fX")]
    n_, r_ = 200, 4
    rows = []
    for ds, rg in cfgs:
        sub = raw[(raw.dataset == ds) & (raw.regime == rg) & (raw.n == n_) & (raw.ratio == r_)]
        base_m = "ppi_linear_X" if rg == "fX" else "ppi_pp"
        b = sub[sub["method"] == base_m].groupby("rep").width.mean()
        methods = ["cf_spline", "cf_hgb", "cf_linear", "sppi", "ppi"] if rg == "f" else \
            ["cf_spline_X", "cf_hgb_X", "cf_linear_X", "sppi", "ppi"]
        rr = {}
        for m in methods:
            w = sub[sub["method"] == m].groupby("rep").width.mean()
            ratio = (w / b).dropna()
            rr[m] = (ratio.mean(), ratio.std(ddof=1) / np.sqrt(len(ratio)))
        tt = th[(th.dataset == ds) & (th.regime == rg) & (th.ratio == r_)].iloc[0]
        rows.append((f"{ds}\n({rg})", rr, float(np.sqrt(1 - (1 - tt.a) * tt.Delta / (tt.E_res_L + tt.a * tt.Var_L)))))
    fig, ax = plt.subplots(figsize=(3.4, 3.6))
    y = np.arange(len(rows))[::-1]
    offs = {"cf_spline": 0.22, "cf_hgb": 0.11, "cf_linear": 0.0, "sppi": -0.11, "ppi": -0.22,
            "cf_spline_X": 0.22, "cf_hgb_X": 0.11, "cf_linear_X": 0.0}
    for (lab, rr, bound), yy in zip(rows, y):
        for m, (mu, se) in rr.items():
            key = m
            c = COL.get(m, COL.get(m.replace("_X", ""), "#52514e"))
            c = COL.get(m, "#52514e")
            if m.endswith("_X"):
                c = {"cf_spline_X": COL["cf_spline"], "cf_hgb_X": COL["cf_hgb"], "cf_linear_X": COL["cf_linear"]}[m]
            mk = MK.get(m, "o")
            ax.errorbar(mu, yy + offs.get(m, 0), xerr=1.96 * se, fmt=mk, color=c, ms=3,
                        mfc="white" if m == "sppi" else c, elinewidth=0.6, capsize=0)
        ax.plot([bound, bound], [yy - 0.35, yy + 0.35], color="#1d1d1b", lw=1.0)
    ax.axvline(1.0, color="#52514e", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=6)
    ax.set_xlabel("CI width ratio vs PPI++ (same covariates); $n=200$, $N=4n$")
    ax.set_title("Real pools: flexible calibration vs. the efficient bound")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker=MK["cf_spline"], color=COL["cf_spline"], ls="", label="CF spline"),
               Line2D([], [], marker=MK["cf_hgb"], color=COL["cf_hgb"], ls="", label="CF boosting"),
               Line2D([], [], marker=MK["cf_linear"], color=COL["cf_linear"], ls="", label="CF linear"),
               Line2D([], [], marker="D", color="black", mfc="white", ls="", label="Stratified PPI"),
               Line2D([], [], marker="|", color="#1d1d1b", ls="", ms=7, label="efficient bound (pool)")]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=5.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_real.pdf", bbox_inches="tight")
    fig.savefig(f"/work/results/preview_fig_real.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def theory_fig():
    th = pd.read_csv("/work/results/theory_check.csv")
    t = th[th["method"] != "ppi_pp"]
    fig, ax = plt.subplots(figsize=(2.6, 2.6))
    cols = {"lin": "#1baf7a", "nl": "#2a78d6", "bin": "#e87ba4", "xonly": "#eb6834", "heavy": "#eda100"}
    for sc, c in cols.items():
        tt = t[t.scenario == sc]
        ax.scatter(tt.width_ratio_pred, tt.width_ratio_emp, s=7, color=c, label=sc, marker="o")
    lim = [0.7, 1.5]
    ax.plot(lim, lim, color="#1d1d1b", lw=0.6, ls="--")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("predicted width ratio")
    ax.set_ylabel("Monte Carlo width ratio")
    ax.legend(frameon=False, fontsize=5.5, loc="upper left", title="scenario", title_fontsize=5.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_theory.pdf", bbox_inches="tight")
    fig.savefig(f"/work/results/preview_fig_theory.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    which = sys.argv[1:] or ["synth", "real", "theory"]
    if "synth" in which: synth_fig()
    if "real" in which: real_fig()
    if "theory" in which: theory_fig()
    print("figures written to", OUT)
