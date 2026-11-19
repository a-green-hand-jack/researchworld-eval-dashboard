"""Figures for the paper. Reads /work/results/summary_E*.csv, writes /work/paper/figures/*.pdf.

Palette: validated light-mode categorical slots from the dataviz reference palette
(blue #2a78d6, orange #eb6834, aqua #1baf7a); text #0b0b0b / #52514e; grid #e6e5e1.
At most three series per panel (the first three slots are validated for all-pairs use).
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "/work/code")
from gate import dgp  # noqa: E402

RES = "/work/results"
FIG = "/work/paper/figures"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
GRAPH_LABEL = {"stanford3": "Stanford3 (n=11,586)", "egofb": "ego-Facebook (n=4,039)",
               "ba_n5000_m3": "BA (n=5,000, m=3)"}
MECH_SHORT = {"M0": "M0 null", "M1": "M1 linear", "M2": "M2 cubic", "M3": "M3 saturating",
              "M4": "M4 2-hop", "M5": "M5 threshold", "M6": "M6 shocks"}


def style(ax):
    ax.set_facecolor(SURF)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_bias_by_mechanism(s1):
    """Bias of DiM, 1-hop OLS and GBM by mechanism, Bernoulli p=0.5, one panel per graph."""
    graphs = ["stanford3", "egofb", "ba_n5000_m3"]
    mechs = ["M1", "M2", "M3", "M4", "M5", "M6"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), sharey=True)
    series = [("dim", "difference in means", ORANGE, "o"),
              ("r2", "OLS, 1-hop exposure", BLUE, "s"),
              ("r5", "gradient boosting", AQUA, "^")]
    x = np.arange(len(mechs))
    for ax, g in zip(axes, graphs):
        style(ax)
        d = s1[(s1.graph == g) & (s1.design == "bern") & (s1.p == 0.5)]
        for k, (est, lab, col, mk) in enumerate(series):
            vals = [d[(d.mech == m) & (d.estimator == est)]["bias"].values[0] for m in mechs]
            ax.scatter(x + (k - 1) * 0.18, vals, color=col, marker=mk, s=16, label=lab, zorder=3)
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(mechs, fontsize=8)
        ax.set_title(GRAPH_LABEL[g], fontsize=8.5, color=INK)
    axes[0].set_ylabel("bias of GATE estimate", fontsize=8.5, color=INK)
    axes[1].set_xlabel("mechanism (Bernoulli p = 0.5)", fontsize=8.5, color=INK)
    axes[0].legend(frameon=False, fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(f"{FIG}/fig_bias_by_mechanism.pdf")
    plt.close(fig)


def fig_coverage(s1):
    """Coverage of nominal 95% intervals for the 1-hop OLS: HC1 vs cluster-robust CR1."""
    rows = []
    for g in ["stanford3", "egofb", "ba_n5000_m3"]:
        for design, p in [("bern", 0.5), ("gcr", 0.5)]:
            d = s1[(s1.graph == g) & (s1.design == design) & (s1.p == p) & (s1.estimator == "r2")]
            for _, r in d.iterrows():
                rows.append(dict(graph=g, design=design, mech=r.mech, hc1=r.cov_hc1, cr1=r.cov_cr1))
    c = pd.DataFrame(rows)
    mechs = ["M1", "M2", "M3", "M4", "M5", "M6"]
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.0), sharey=True)
    for i, design in enumerate(["bern", "gcr"]):
        for j, g in enumerate(["stanford3", "egofb", "ba_n5000_m3"]):
            ax = axes[i, j]
            style(ax)
            d = c[(c.graph == g) & (c.design == design)].set_index("mech").reindex(mechs)
            x = np.arange(len(mechs))
            ax.scatter(x - 0.13, d.hc1, color=ORANGE, marker="o", s=16, label="HC1 (iid sandwich)", zorder=3)
            ax.scatter(x + 0.13, d.cr1, color=BLUE, marker="s", s=16, label="CR1 (Louvain clusters)", zorder=3)
            ax.axhline(0.95, color=INK2, linewidth=0.8, linestyle="--")
            ax.set_ylim(-0.02, 1.02)
            ax.set_xticks(x)
            ax.set_xticklabels(mechs, fontsize=7.5)
            if i == 0:
                ax.set_title(GRAPH_LABEL[g], fontsize=8.5, color=INK)
            if j == 0:
                ax.set_ylabel(("Bernoulli" if design == "bern" else "graph-cluster") + "\ncoverage", fontsize=8, color=INK)
    axes[0, 0].legend(frameon=False, fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(f"{FIG}/fig_coverage.pdf")
    plt.close(fig)


def fig_degree(s2):
    """E2: precision, bias and extrapolation as mean degree grows (ER graphs, n about 5000)."""
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
    d = s2.mean_deg.unique()
    d = np.sort(d)
    # Panel A: SD of the 1-hop estimator, linear mechanism, with sqrt(d) reference
    ax = axes[0]
    style(ax)
    m1 = s2[(s2.mech == "M1") & (s2.estimator == "r2")].sort_values("mean_deg")
    m5 = s2[(s2.mech == "M5") & (s2.estimator == "r2")].sort_values("mean_deg")
    ax.loglog(m1.mean_deg, m1.sd, "o-", color=BLUE, ms=3.5, lw=1.2, label="M1 linear")
    ax.loglog(m5.mean_deg, m5.sd, "s-", color=ORANGE, ms=3.5, lw=1.2, label="M5 threshold")
    c = np.exp(np.mean(np.log(m1.sd / np.sqrt(m1.mean_deg))))
    xx = np.logspace(np.log10(d.min()), np.log10(d.max()), 50)
    ax.loglog(xx, c * np.sqrt(xx), "--", color=INK2, lw=0.9)
    ax.text(xx[-1], c * np.sqrt(xx[-1]) * 0.7, r"$\propto\sqrt{d}$", fontsize=7, color=INK2, ha="right", va="top")
    ax.set_xlabel("mean degree", fontsize=8, color=INK)
    ax.set_ylabel("SD of 1-hop OLS estimate", fontsize=8, color=INK)
    ax.set_title("A. precision", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    # Panel B: bias of the 1-hop estimator, cubic and threshold mechanisms (symlog)
    ax = axes[1]
    style(ax)
    m2 = s2[(s2.mech == "M2") & (s2.estimator == "r2")].sort_values("mean_deg")
    ax.plot(m2.mean_deg, m2.bias, "o-", color=ORANGE, ms=3.5, lw=1.2, label="M2 cubic")
    ax.plot(m5.mean_deg, m5.bias, "s-", color=BLUE, ms=3.5, lw=1.2, label="M5 threshold")
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("mean degree", fontsize=8, color=INK)
    ax.set_ylabel("bias of 1-hop OLS (symlog)", fontsize=8, color=INK)
    ax.set_title("B. misspecification bias", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    # Panel C: gradient boosting bias under the linear mechanism
    ax = axes[2]
    style(ax)
    g1 = s2[(s2.mech == "M1") & (s2.estimator == "r5")].sort_values("mean_deg")
    r2 = s2[(s2.mech == "M1") & (s2.estimator == "r2")].sort_values("mean_deg")
    ax.plot(g1.mean_deg, g1.bias, "^-", color=AQUA, ms=4, lw=1.2, label="gradient boosting")
    ax.plot(r2.mean_deg, r2.bias, "o-", color=BLUE, ms=3.5, lw=1.2, label="1-hop OLS")
    ax.set_xscale("log")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("mean degree", fontsize=8, color=INK)
    ax.set_ylabel("bias, M1 (truth = 3)", fontsize=8, color=INK)
    ax.set_title("C. learner extrapolation", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    for a in axes:
        a.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/fig_degree.pdf")
    plt.close(fig)


def fig_sample_size(s3):
    """E3: misspecification bias is stable in n while the SD shrinks like 1/sqrt(n)."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    ns = np.sort(s3.n.unique())
    ax = axes[0]
    style(ax)
    spec = [("M2", ORANGE, "o", "M2 cubic"), ("M5", BLUE, "s", "M5 threshold"), ("M1", AQUA, "^", "M1 linear")]
    for m, col, mk, lab in spec:
        d = s3[(s3.mech == m) & (s3.estimator == "r2")].sort_values("n")
        ax.plot(d.n, d.bias, marker=mk, color=col, ms=3.5, lw=1.2, label=lab)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("sample size n (ER, mean degree 20)", fontsize=8, color=INK)
    ax.set_ylabel("bias of 1-hop OLS (symlog)", fontsize=8, color=INK)
    ax.set_title("A. bias does not vanish", fontsize=8.5, color=INK)
    ax.set_ylim(-3, 12)
    ax.legend(frameon=False, fontsize=7, loc="center left")
    ax = axes[1]
    style(ax)
    d = s3[(s3.mech == "M1") & (s3.estimator == "r2")].sort_values("n")
    ax.loglog(d.n, d.sd, "o-", color=BLUE, ms=3.5, lw=1.2, label="M1 linear, empirical SD")
    c = np.exp(np.mean(np.log(d.sd * np.sqrt(d.n))))
    xx = np.logspace(np.log10(ns.min()), np.log10(ns.max()), 50)
    ax.loglog(xx, c / np.sqrt(xx), "--", color=INK2, lw=0.9, label=r"$\propto n^{-1/2}$")
    ax.set_xlabel("sample size n", fontsize=8, color=INK)
    ax.set_ylabel("SD of 1-hop OLS estimate", fontsize=8, color=INK)
    ax.set_title("B. precision", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    for a in axes:
        a.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/fig_sample_size.pdf")
    plt.close(fig)


def fig_p_sweep(s4):
    """E4: bias of the 1-hop OLS and of gradient boosting as the treatment probability varies."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    ax = axes[0]
    style(ax)
    spec = [("M2", ORANGE, "o", "M2 cubic"), ("M3", AQUA, "^", "M3 saturating"), ("M5", BLUE, "s", "M5 threshold")]
    for m, col, mk, lab in spec:
        d = s4[(s4.mech == m) & (s4.estimator == "r2")].sort_values("p")
        ax.plot(d.p, d.bias, marker=mk, color=col, ms=3.5, lw=1.2, label=lab)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel("treatment probability p (Bernoulli)", fontsize=8, color=INK)
    ax.set_ylabel("bias of 1-hop OLS (symlog)", fontsize=8, color=INK)
    ax.set_title("A. 1-hop OLS", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    ax = axes[1]
    style(ax)
    spec = [("M1", BLUE, "o", "M1 linear"), ("M2", ORANGE, "s", "M2 cubic"), ("M5", AQUA, "^", "M5 threshold")]
    for m, col, mk, lab in spec:
        d = s4[(s4.mech == m) & (s4.estimator == "r5")].sort_values("p")
        ax.plot(d.p, d.bias, marker=mk, color=col, ms=3.5, lw=1.2, label=lab)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("treatment probability p (Bernoulli)", fontsize=8, color=INK)
    ax.set_ylabel("bias of gradient boosting", fontsize=8, color=INK)
    ax.set_title("B. gradient boosting", fontsize=8.5, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    for a in axes:
        a.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/fig_p_sweep.pdf")
    plt.close(fig)


if __name__ == "__main__":
    s1 = pd.read_csv(f"{RES}/summary_E1.csv")
    fig_bias_by_mechanism(s1)
    fig_coverage(s1)
    import os
    if os.path.exists(f"{RES}/summary_E2.csv"):
        fig_degree(pd.read_csv(f"{RES}/summary_E2.csv"))
    if os.path.exists(f"{RES}/summary_E3.csv"):
        fig_sample_size(pd.read_csv(f"{RES}/summary_E3.csv"))
    if os.path.exists(f"{RES}/summary_E4.csv"):
        fig_p_sweep(pd.read_csv(f"{RES}/summary_E4.csv"))
    print("figures written")
