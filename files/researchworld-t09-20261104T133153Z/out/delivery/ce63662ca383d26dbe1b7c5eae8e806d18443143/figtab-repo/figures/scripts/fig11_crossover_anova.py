"""Fig 11 (claims C3/C4, new analyses): how the crossover and the variance price depend on (n, d, sigma), and what drives the RMSE of OLS (z,f).
(a) crossover strength gamma* (OLS_f overtakes the difference in means in RMSE; model-based, t21_crossover.csv) against mean degree, one grey line per n
    (through the sigma=1 cells), marker per sigma; open markers: gamma* above the largest simulated gamma (2), i.e. extrapolated from the fitted DM bias slope.
(b) SD(OLS_f)/SD(DM) at gamma=0 on the same grid and styling, plus the six default graphs (coloured, t20c_headline_intervals.csv, 95% hierarchical bootstrap)
    at their mean degree. Fitted exponents of both panels: t21b_crossover_scaling.csv.
(c) first-order (dark) and total-effect (light) shares of the variance of log RMSE(OLS_f), SBM factorial e20 (t22_factor_anova.csv), sorted by total effect.
Reads <FIGTAB_RESULTS>/../tables/{t21_crossover,t21b_crossover_scaling,t20c_headline_intervals,t17_variance_law,t22_factor_anova}.csv."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

TAB = os.path.join(RES, "..", "tables")
NCOL = {1000: "#9a9a9a", 5000: "#5a5a5a", 20000: "#000000"}
NLS = {1000: ":", 5000: "--", 20000: "-"}
SMARK = {0.5: "^", 1.0: "o", 2.0: "s"}
GMAX = 2.0  # largest simulated interference strength in e17


def expo(sc, q, keys):
    r = sc[sc.quantity == q].iloc[0]
    return r"$\propto$ " + " ".join(f"${k}^{{{r['exp_' + c]:+.2f}\\pm{r['se_' + c]:.2f}}}$".replace("+", "") if r['exp_' + c] > 0 else f"${k}^{{{r['exp_' + c]:.2f}\\pm{r['se_' + c]:.2f}}}$".replace("-", "−") for k, c in keys)


def ticks(ax, xt, yt):
    """Explicit plain decimal ticks on both log axes, no minor labels."""
    from matplotlib.ticker import FuncFormatter, NullLocator
    f = FuncFormatter(lambda v, _: f"{v:g}")
    for a, t in ((ax.xaxis, xt), (ax.yaxis, yt)):
        a.set_major_locator(plt.FixedLocator(t)); a.set_major_formatter(f); a.set_minor_locator(NullLocator())


def grid_panel(ax, T, col, ylabel):
    for n in sorted(T.n.round(-3).unique()):
        t = T[T.n.round(-3) == n]
        s1 = t[t.sigma == 1.0].sort_values("mean_deg")
        ax.plot(s1.mean_deg, s1[col], color=NCOL[n], ls=NLS[n], lw=0.9, zorder=2)
        for sg, m in SMARK.items():
            u = t[t.sigma == sg]
            ex = (u[col] > GMAX) if col == "gamma_star_model" else pd.Series(False, index=u.index)
            for e, fc in ((False, NCOL[n]), (True, "white")):
                v = u[ex == e]
                if len(v):
                    ax.plot(v.mean_deg, v[col], ls="", marker=m, ms=3.2, mfc=fc, mec=NCOL[n], mew=0.7, zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("mean degree $d$"); ax.set_ylabel(ylabel)


def main():
    style()
    plt.rcParams.update({"font.size": 6.5, "axes.labelsize": 6.5, "xtick.labelsize": 6, "ytick.labelsize": 6, "legend.fontsize": 5.5,
                         "axes.titlesize": 6.5})
    T = pd.read_csv(os.path.join(TAB, "t21_crossover.csv"))
    sc = pd.read_csv(os.path.join(TAB, "t21b_crossover_scaling.csv"))
    hl = pd.read_csv(os.path.join(TAB, "t20c_headline_intervals.csv"))
    vl = pd.read_csv(os.path.join(TAB, "t17_variance_law.csv")).set_index("graph")
    an = pd.read_csv(os.path.join(TAB, "t22_factor_anova.csv"))
    an = an[(an.est_name == "OLS_f") & (an.response == "rmse")].sort_values("total")
    fig, axs = plt.subplots(1, 3, figsize=(TEXTW, 1.95), gridspec_kw={"width_ratios": [1, 1, 1.05], "wspace": 0.62, "top": 0.82, "bottom": 0.2, "left": 0.07, "right": 0.995})
    ax = axs[0]
    grid_panel(ax, T, "gamma_star_model", r"crossover $\gamma^*$")
    ax.axhline(GMAX, color="#888888", lw=0.5, ls=(0, (1, 1.5)))
    ax.text(10.2, GMAX * 1.06, "largest simulated $\\gamma$", fontsize=5, color="#666666", va="bottom")
    ax.set_xlim(8, 52); ax.set_ylim(0.08, 4.5); ticks(ax, [10, 20, 40], [0.1, 0.2, 0.5, 1, 2])
    ax.text(0.03, 0.97, r"$\gamma^*$ " + expo(sc, "gamma* (model)", [("n", "n"), ("d", "d"), (r"\sigma", "sigma")]), transform=ax.transAxes, va="top", fontsize=5.3)
    panel_label(ax, "a")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=NCOL[n], ls=NLS[n], lw=0.9, label=f"$n$={n // 1000}k") for n in NCOL]
    h += [Line2D([], [], color="#444444", ls="", marker=m, ms=3, mfc="#444444", label=f"$\\sigma$={sg:g}") for sg, m in SMARK.items()]
    h += [Line2D([], [], color="#444444", ls="", marker="o", ms=3, mfc="white", label="$\\gamma^*>2$ (extrapolated)")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.06, 1.0), ncol=7, handletextpad=0.3, columnspacing=0.8, fontsize=5.8)

    ax = axs[1]
    grid_panel(ax, T, "sd_ratio_g0", r"SD(OLS$_f$)/SD(DM) at $\gamma$=0")
    ax.set_xlim(8, 130); ax.set_ylim(1.9, 55); ticks(ax, [10, 20, 40, 100], [4, 8, 16, 32])
    for _, r in hl[hl.graph.isin(GNAME)].iterrows():
        g = GNAME[r.graph]; d = vl.loc[r.graph, "mean_deg"]
        ax.errorbar(d, r.value, yerr=[[r.value - r.lo], [r.hi - r.value]], color=GCOL[g], marker=GMARK[g], ms=3.6, mec="black", mew=0.4,
                    lw=0.8, capsize=1.2, capthick=0.6, ls="", zorder=4, label=g)
    ax.text(0.03, 0.97, "ratio " + expo(sc, "SD(OLS_f)/SD(DM) at gamma=0", [("n", "n"), ("d", "d"), (r"\sigma", "sigma")]), transform=ax.transAxes, va="top", fontsize=5.3)
    hh, ll = ax.get_legend_handles_labels()
    ax.legend(hh, ll, loc="lower right", ncol=2, handletextpad=0.1, labelspacing=0.2, columnspacing=0.4, markerscale=0.8, fontsize=5.2, borderaxespad=0.1)
    panel_label(ax, "b")

    ax = axs[2]
    LAB = {"n": "units $n$", "mean degree": "mean degree $d$", "treated share p": "treated share $p$", "noise sigma": "noise $\\sigma$",
           "graph-smooth baseline": "smooth baseline", "spillover shape": "spillover shape"}
    y = np.arange(len(an))
    ax.barh(y + 0.19, an.total, height=0.34, color="#d0d0d0", edgecolor="#555555", lw=0.4, hatch="////", label="total effect", zorder=2)
    ax.barh(y - 0.19, an.first_order, height=0.34, color="#404040", edgecolor="#404040", lw=0.4, label="first-order", zorder=2)
    for yy, lo, hi in zip(y + 0.19, an.total_lo, an.total_hi): ax.plot([lo, hi], [yy, yy], color="black", lw=0.7, zorder=3)
    for yy, lo, hi in zip(y - 0.19, an.first_lo, an.first_hi): ax.plot([lo, hi], [yy, yy], color="black", lw=0.7, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([LAB[f] for f in an.factor]); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 0.4); ax.set_ylim(-0.6, len(an) - 0.4)
    ax.set_xlabel("share of variance of log RMSE")
    ax.legend(loc="lower right", handlelength=1.3, labelspacing=0.25)
    ax.text(0.99, 0.30, "SBM factorial\n144 cells (e20)", transform=ax.transAxes, ha="right", va="bottom", fontsize=5.3, color="#444444")
    panel_label(ax, "c")
    save(fig, "fig11_crossover_anova")


if __name__ == "__main__":
    main()
