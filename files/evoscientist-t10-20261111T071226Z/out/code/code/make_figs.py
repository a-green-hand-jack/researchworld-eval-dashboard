"""Builds all figures (figs/*.pdf) and LaTeX table fragments (paper/tables/*.tex) from results/*.csv."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES, FIG, TAB = [os.path.join(HERE, "..", p) for p in ("results", "figs", "paper/tables")]
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 7, "figure.dpi": 150})

NAMES = {"classical": "Classical", "classical_t": "Classical-t", "ppi++_own_t": "PPI++ unclipped-t", "spline4_t": "NC-spline (k=4)-t", "ppi": "PPI", "ppi++": "PPI++ (ppi_py)", "ppi++_own": "PPI++ (unclipped)",
         "strat_ppi5": "Post-strat PPI (K=5)", "spline3": "NC-spline (k=3)", "spline4": "NC-spline (k=4)",
         "spline6": "NC-spline (k=6)", "cf_iso": "CF-isotonic", "cf_gbm_fX": "CF-GBM on (f,X)"}
COL = {"classical": "gray", "classical_t": "silver", "ppi++_own_t": "gold", "spline4_t": "navy", "ppi": "tab:brown", "ppi++": "k", "ppi++_own": "tab:olive", "strat_ppi5": "tab:purple",
       "spline3": "tab:cyan", "spline4": "tab:blue", "spline6": "tab:green", "cf_iso": "tab:red", "cf_gbm_fX": "tab:orange"}
SCN = {"herm0": "Hermite 0°", "herm30": "Hermite 30°", "herm60": "Hermite 60°", "herm90": "Hermite 90°",
       "lognorm1": "Lognormal β=1", "lognorm1.5": "Lognormal β=1.5", "logistic1": "Logistic b=1", "logistic3": "Logistic b=3",
       "binaryf": "Binary f", "herm0_scale0.25": "Linear, f scaled 0.25", "herm30_scale0.25": "Hermite 30°, f scaled 0.25"}
DS = {"galaxies": "Galaxies", "forest": "Forest", "alphafold": "AlphaFold", "gene_expression": "Gene expr.",
      "census_income": "Census income", "census_healthcare": "Census health", "census_education": "Census educ.",
      "plankton": "Plankton", "ballots": "Ballots"}


def pm(x, se, d=3):
    return f"{x:.{d}f}$\\pm${se:.{d}f}"


def fig_synth(df):
    d = df[(df.N == 10000)]
    sel = ["herm0", "herm30", "herm60", "herm90", "lognorm1", "lognorm1.5", "logistic1", "logistic3", "binaryf",
           "herm0_scale0.25", "herm30_scale0.25"]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
    d2 = d[d.n == 200]
    y = np.arange(len(sel))
    for off, m in zip((-0.2, 0.0, 0.2), ("spline4", "cf_iso", "ppi++_own")):
        r = d2[d2.method == m].set_index("scenario").loc[sel]
        ax[0].errorbar(r.ratio_vs_ppipp, y + off, xerr=1.96 * r.ratio_se, fmt="o", ms=3, color=COL[m], label=NAMES[m], lw=0.8)
    r = d2[d2.method == "spline4"].set_index("scenario").loc[sel]
    ax[0].plot(r.theory_ratio_eff, y, "k|", ms=9, label="efficiency bound (theory)")
    ax[0].axvline(1, color="gray", lw=0.6, ls=":")
    ax[0].set_yticks(y)
    ax[0].set_yticklabels([SCN[s] for s in sel])
    ax[0].invert_yaxis()
    ax[0].set_xlabel("mean CI width / PPI++ (ppi_py) width,  n=200, N=10^4")
    h0, l0 = ax[0].get_legend_handles_labels()
    ax[0].set_title("(a) width ratio by scenario (±1.96 SE of paired ratio)")
    for s, c in zip(("herm0", "herm60", "lognorm1", "logistic3"), ("gray", "tab:blue", "tab:green", "tab:red")):
        r = d[(d.scenario == s) & (d.method == "spline4")].sort_values("n")
        ax[1].errorbar(r.n, r.ratio_vs_ppipp, yerr=1.96 * r.ratio_se, fmt="-o", ms=3, color=c, label=SCN[s], lw=0.8)
        ax[1].plot(r.n, r.theory_ratio, ls="--", color=c, lw=0.8)
    ax[1].set_xscale("log")
    ax[1].axhline(1, color="gray", lw=0.6, ls=":")
    ax[1].set_xlabel("labeled sample size n")
    ax[1].set_ylabel("NC-spline (k=4) / PPI++ width")
    ax[1].set_title("(b) vs n (dashed: asymptotic theory)")
    ax[1].legend(frameon=False)
    fig.legend(h0, l0, loc="lower center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_synth_width.pdf"))
    plt.close(fig)


def fig_real(df):
    fig, axes = plt.subplots(3, 3, figsize=(7.2, 5.6), sharex=False)
    for ax, ds in zip(axes.ravel(), DS):
        d = df[df.dataset == ds]
        for m in ("spline4", "spline4_t", "cf_iso", "strat_ppi5", "ppi++_own"):
            r = d[d.method == m].sort_values("n")
            ax.errorbar(r.n, r.ratio_vs_ppipp, yerr=1.96 * r.ratio_se, fmt="-o", ms=2.5, lw=0.8, color=COL[m], label=NAMES[m])
        eff = d.theory_ratio_eff.iloc[0]
        ax.axhline(eff, color="k", ls="--", lw=0.8, label="efficiency bound (n=200)")
        ax.axhline(1, color="gray", lw=0.5, ls=":")
        ax.set_xscale("log")
        ax.set_xticks([50, 100, 200, 500, 1000, 2000][: len(d.n.unique())])
        ax.set_xticklabels(["50", "100", "200", "500", "1k", "2k"][: len(d.n.unique())])
        ax.minorticks_off()
        ax.set_title(DS[ds])
    axes[1, 0].set_ylabel("CI width / PPI++ (ppi_py) width")
    axes[2, 1].set_xlabel("labeled sample size n (N=10^4)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_real_width.pdf"))
    plt.close(fig)


def fig_cover(real, synth):
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    for a, df, t in ((ax[0], real, "real-data resampling (9 datasets)"), (ax[1], synth[synth.N == 10000], "synthetic (11 scenarios)")):
        for m in ("classical", "ppi", "ppi++", "ppi++_own", "strat_ppi5", "spline4", "cf_iso"):
            g = df[df.method == m].groupby("n").cover.agg(["mean", "min"])
            a.plot(g.index, g["mean"], "-o", ms=3, lw=0.9, color=COL[m], label=NAMES[m])
            a.plot(g.index, g["min"], ":", lw=0.7, color=COL[m])
        a.axhline(0.95, color="k", lw=0.6)
        a.set_xscale("log")
        a.set_xlabel("n")
        a.set_title(t)
    ax[0].set_ylabel("empirical coverage (solid: mean over\nconfigs; dotted: worst config)")
    ax[1].legend(frameon=False, loc="lower right", ncol=1)
    ax[0].set_ylim(0.88, 0.97)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_coverage.pdf"))
    plt.close(fig)


def fig_theory(real, synth):
    fig, ax = plt.subplots(1, 1, figsize=(3.2, 3.0))
    both = pd.concat([real.assign(src="real"), synth.assign(src="synthetic")])
    both = both[(both.n >= 500) & both.method.isin(["spline4"]) & (both.N == 10000)]
    for s, mk in (("real", "o"), ("synthetic", "s")):
        r = both[both.src == s]
        ax.errorbar(r.theory_ratio, r.ratio_vs_ppipp, yerr=1.96 * r.ratio_se, fmt=mk, ms=3, lw=0.6, label=s, alpha=0.8)
    ax.plot([0.6, 1.1], [0.6, 1.1], "k--", lw=0.6)
    ax.set_xlabel("asymptotic theory: width ratio")
    ax.set_ylabel("empirical width ratio")
    ax.set_title("NC-spline (k=4) vs PPI++, n≥500")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_theory_vs_emp.pdf"))
    plt.close(fig)


def write(name, s):
    for a, b in (("ppi_py", "\\texttt{ppi\\_py}"), ("°", "$^\\circ$"), ("β", "$\\beta$"), ("->", "$\\to$")):
        s = s.replace(a, b)
    with open(os.path.join(TAB, name), "w") as f:
        f.write(s)


def table_real(real):
    """Width ratio vs PPI++ and coverage for n=200 and n=1000 (n=500 for small pools)."""
    meths = ["classical", "ppi", "ppi++_own", "strat_ppi5", "spline4", "cf_iso"]
    out = ["\\begin{tabular}{llrrrrrrr}", "\\toprule",
           "Dataset & $n$ & Classical & PPI & PPI++ unclip. & Post-strat & NC-spline & CF-iso & Bound \\\\", "\\midrule"]
    for ds in DS:
        for n in (200, 1000 if ds not in ("forest", "ballots") else 500):
            d = real[(real.dataset == ds) & (real.n == n)].set_index("method")
            cells = []
            for m in meths:
                r = d.loc[m]
                cells.append(f"{r.ratio_vs_ppipp:.3f}")
            out.append(f"{DS[ds]} & {n} & " + " & ".join(cells) + f" & {d.theory_ratio_eff.iloc[0]:.3f} \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_real_width.tex", "\n".join(out))


def table_cover(real, synth):
    meths = ["classical", "classical_t", "ppi", "ppi++", "ppi++_own", "ppi++_own_t", "strat_ppi5", "spline4", "spline4_t", "cf_iso"]
    out = ["\\begin{tabular}{lrrrrrrr}", "\\toprule",
           "Method & \\multicolumn{3}{c}{mean coverage, $n\\in\\{50,100,200\\}$ / $\\{500,1000,2000\\}$} & & \\multicolumn{3}{c}{min coverage (any config)} \\\\"]
    out = ["\\begin{tabular}{lrrrrrrrr}", "\\toprule",
           " & \\multicolumn{4}{c}{Real-data resampling} & \\multicolumn{4}{c}{Synthetic ($N{=}10^4$)} \\\\",
           "Method & $n{\\le}100$ & $n{\\ge}500$ & min & \\#$<$.93 & $n{\\le}100$ & $n{\\ge}500$ & min & \\#$<$.93 \\\\", "\\midrule"]
    for m in meths:
        cells = []
        for df in (real, synth[synth.N == 10000]):
            d = df[df.method == m]
            cells += [f"{d[d.n <= 100].cover.mean():.3f}", f"{d[d.n >= 500].cover.mean():.3f}", f"{d.cover.min():.3f}",
                      f"{(d.cover < 0.93).sum()}/{len(d)}"]
        out.append(NAMES[m] + " & " + " & ".join(cells) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_coverage.tex", "\n".join(out))


def table_synth(synth):
    d = synth[(synth.N == 10000) & (synth.n == 200)]
    sel = list(SCN)
    out = ["\\begin{tabular}{lrrrrrrr}", "\\toprule",
           "Scenario & PPI & PPI++ unclip. & NC-spline & CF-iso & Bound & cov. PPI++ & cov. NC-spline \\\\", "\\midrule"]
    for s in sel:
        r = d[d.scenario == s].set_index("method")
        out.append(f"{SCN[s]} & {r.loc['ppi','ratio_vs_ppipp']:.3f} & {r.loc['ppi++_own','ratio_vs_ppipp']:.3f} & "
                   f"{r.loc['spline4','ratio_vs_ppipp']:.3f} & {r.loc['cf_iso','ratio_vs_ppipp']:.3f} & "
                   f"{r.loc['spline4','theory_ratio_eff']:.3f} & {r.loc['ppi++','cover']:.3f} & {r.loc['spline4','cover']:.3f} \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_synth.tex", "\n".join(out))


def table_shift():
    p = os.path.join(RES, "shift_summary.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    out = ["\\begin{tabular}{llrrrrr}", "\\toprule", "Setting & $n$ & Method & Coverage & 95\\% CI of cov. & Width & Bias \\\\", "\\midrule"]
    for (st, n), g in d.groupby(["setting", "n"], sort=False):
        for m in ("classical", "ppi", "ppi++", "spline4"):
            r = g[g.method == m].iloc[0]
            out.append(f"{st} & {n} & {NAMES[m]} & {r.cover:.3f} & [{r.cover_lo:.3f}, {r.cover_hi:.3f}] & {r.width:.4f} & {r.bias:+.4f} \\\\")
        out.append("\\midrule")
    out[-1] = "\\bottomrule"
    out.append("\\end{tabular}")
    write("tab_shift.tex", "\n".join(out))


def table_ext_x():
    p = os.path.join(RES, "ext_x_summary.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    o = pd.read_csv(os.path.join(RES, "ext_x_oracle.csv")).set_index("dataset")
    out = ["\\begin{tabular}{lrrrrrr}", "\\toprule",
           "Dataset & $n$ & NC-spline & CF-iso & CF-GBM$(f,X)$ & cov. PPI++ & cov. CF-GBM \\\\", "\\midrule"]
    for (ds, n), g in d.groupby(["dataset", "n"], sort=False):
        g = g.set_index("method")
        out.append(f"{DS[ds]} & {n} & {g.loc['spline4','ratio_vs_ppipp']:.3f} & {g.loc['cf_iso','ratio_vs_ppipp']:.3f} & "
                   f"{g.loc['cf_gbm_fX','ratio_vs_ppipp']:.3f}$\\pm${g.loc['cf_gbm_fX','ratio_se']:.3f} & {g.loc['ppi++','cover']:.3f} & {g.loc['cf_gbm_fX','cover']:.3f} \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_ext_x.tex", "\n".join(out))


def table_ballots():
    p = os.path.join(RES, "ballots_deploy.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p).set_index("method")
    out = ["\\begin{tabular}{lrrrr}", "\\toprule", "Method & Estimate & Lower & Upper & Width \\\\", "\\midrule"]
    for m in ("classical", "ppi", "ppi++", "ppi++_own", "strat_ppi5", "spline4", "cf_iso"):
        r = d.loc[m]
        out.append(f"{NAMES[m]} & {r.estimate:.4f} & {r.lo:.4f} & {r.hi:.4f} & {r.width:.4f} \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_ballots.tex", "\n".join(out))


def table_distort():
    p = os.path.join(RES, "distort_summary.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    d = d[d.n == 200]
    out = ["\\begin{tabular}{l" + "rrrr" * 2 + "}", "\\toprule",
           " & \\multicolumn{4}{c}{rank-uniformised score} & \\multicolumn{4}{c}{exponential score scale} \\\\",
           "Dataset & PPI++ unclip. & NC-spline & Bound & cov. NC-s. & PPI++ unclip. & NC-spline & Bound & cov. NC-s. \\\\", "\\midrule"]
    for ds in ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]:
        cells = []
        for k in ("rank", "expz"):
            g = d[(d.dataset == ds) & (d["transform"] == k)].set_index("method")
            cells += [f"{g.loc['ppi++_own','ratio_vs_ppipp']:.3f}", f"{g.loc['spline4','ratio_vs_ppipp']:.3f}",
                      f"{g.loc['spline4','theory_ratio_eff']:.3f}", f"{g.loc['spline4','cover']:.3f}"]
        out.append(DS[ds] + " & " + " & ".join(cells) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_distort.tex", "\n".join(out))


def table_sens(real, synth):
    """Sensitivity to the number of spline knots k in {3,4,6}: width ratio vs PPI++ (ppi_py) at n=200, coverage at n=100."""
    out = ["\\begin{tabular}{lrrrrrrr}", "\\toprule",
           " & \\multicolumn{3}{c}{width ratio, $n{=}200$} & \\multicolumn{3}{c}{coverage, $n{=}100$} & \\\\",
           "Setting & $k{=}3$ & $k{=}4$ & $k{=}6$ & $k{=}3$ & $k{=}4$ & $k{=}6$ & Bound \\\\", "\\midrule"]
    d = synth[synth.N == 10000]
    for sc in ("herm0", "herm30", "herm60", "herm90", "lognorm1", "lognorm1.5", "logistic3", "binaryf"):
        a = d[(d.scenario == sc) & (d.n == 200)].set_index("method")
        b = d[(d.scenario == sc) & (d.n == 100)].set_index("method")
        out.append(f"{SCN[sc]} & " + " & ".join(f"{a.loc[m,'ratio_vs_ppipp']:.3f}" for m in ("spline3", "spline4", "spline6")) + " & "
                   + " & ".join(f"{b.loc[m,'cover']:.3f}" for m in ("spline3", "spline4", "spline6")) + f" & {a.loc['spline4','theory_ratio_eff']:.3f} \\\\")
    out.append("\\midrule")
    cont = [x for x in DS if x not in ("plankton", "ballots")]
    r = real[real.dataset.isin(cont)]
    a, b = r[r.n == 200].groupby("method"), r[r.n == 100].groupby("method")
    wr = r[r.n == 200].groupby("method").ratio_vs_ppipp.mean()
    cv = r[r.n == 100].groupby("method").cover.mean()
    out.append("Real, 7 continuous-score datasets (mean) & " + " & ".join(f"{wr[m]:.3f}" for m in ("spline3", "spline4", "spline6")) + " & "
               + " & ".join(f"{cv[m]:.3f}" for m in ("spline3", "spline4", "spline6")) + " & -- \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    write("tab_sens.tex", "\n".join(out))


if __name__ == "__main__":
    real = pd.read_csv(os.path.join(RES, "real_summary.csv"))
    synth = pd.read_csv(os.path.join(RES, "synth_summary.csv"))
    fig_synth(synth)
    fig_real(real)
    fig_cover(real, synth)
    fig_theory(real, synth)
    table_real(real)
    table_cover(real, synth)
    table_synth(synth)
    table_shift()
    table_ext_x()
    table_ballots()
    table_distort()
    table_sens(real, synth)
    import shutil
    shutil.copytree(FIG, os.path.join(HERE, '..', 'paper', 'figs'), dirs_exist_ok=True)
    print("figures and tables written")
