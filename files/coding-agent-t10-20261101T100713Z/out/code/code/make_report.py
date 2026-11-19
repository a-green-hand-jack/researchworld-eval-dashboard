"""Figures (../figs/*.pdf) and LaTeX table fragments (../paper/tables/*.tex) from ../results/*.csv.
usage: python make_report.py   (run analysis.py first)"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R, FG, TB = "../results/", "../figs/", "../paper/tables/"
os.makedirs(TB, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
REAL = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education", "plankton", "ballots"]
SYN = ["S0_calibrated", "S1_nonlinear_link", "S2_omitted_linear", "S3_omitted_nonlinear", "S4_noise_predictor", "S5_all_noise", "S6_heavy_tail", "S7_binary_miscal"]
NICE = lambda s: s.replace("_", r"\_")
sr, ss = pd.read_csv(R + "summary_real.csv"), pd.read_csv(R + "summary_synth.csv")
th = pd.read_csv(R + "theory_pop.csv").set_index("dataset")
th["mse_opt"] = th[[c for c in th.columns if c.startswith("mse_")]].min(axis=1)
th["mse_lin_ins"] = th.varY - th["cov"] ** 2 / th.varF
th["kappa"] = np.clip((th.mse_lin_ins - th.mse_opt) / th.mse_lin_ins, 0, 1)
th["bound"] = np.sqrt(1 - th.kappa)
th["b"] = th["cov"] / th.varF
pal = plt.cm.tab10(np.arange(10))
bp = R + "boot_summary.csv"


def cell(s, ds, n, N, m, col):
    return s[(s.dataset == ds) & (s.n == n) & (s.N == N) & (s.method == m)].iloc[0][col]


# ------------------------------------------------------------------ Table 1/2: main comparison
def main_table(s, names, fname, n=200, N=5000):
    ms = ["classical", "ppi", "ppi++", "aipw-lin", "aipw-auto"]
    lines = []
    for ds in names:
        cov = " & ".join("%.1f" % (100 * cell(s, ds, n, N, m, "cov_z")) for m in ms)
        rat = " & ".join("%.3f" % cell(s, ds, n, N, m, "ratio") for m in ["classical", "ppi", "aipw-lin", "aipw-auto"])
        lines.append(f"{NICE(ds)} & {th.loc[ds,'b']:.2f} & {th.loc[ds,'kappa']:.3f} & {th.loc[ds,'bound']:.3f} & {cov} & {rat} \\\\")
    open(TB + fname, "w").write(("\n".join(lines)).rstrip("\\") + "\n")


main_table(sr, REAL, "main_real.tex"); main_table(ss, SYN, "main_synth.tex")
main_table(sr, REAL, "main_real_n1000.tex", n=1000); main_table(ss, SYN, "main_synth_n1000.tex", n=1000)
main_table(sr, REAL, "main_real_n50.tex", n=50); main_table(ss, SYN, "main_synth_n50.tex", n=50)

# ------------------------------------------------------------------ Fig 1: width ratio vs n  and vs N
def ratio_panel(ax, s, names, xcol, fixed, method="aipw-auto", title=""):
    for i, ds in enumerate(names):
        g = s[(s.dataset == ds) & (s.method == method) & (s[fixed[0]] == fixed[1])].sort_values(xcol)
        ax.plot(g[xcol], g.ratio, "-o", ms=2.5, lw=1.1, color=pal[i % 10], label=ds.replace("_", " "))
        ax.fill_between(g[xcol], g.ratio_lo, g.ratio_hi, color=pal[i % 10], alpha=.15, lw=0)
    ax.axhline(1, color="k", lw=.6, ls=":"); ax.set_xscale("log"); ax.set_title(title, fontsize=8)


fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.2), sharey=False); axs = axs.ravel()
ratio_panel(axs[0], sr, REAL, "n", ("N", 5000), title="real data, N=5000"); axs[0].set_ylim(0.9, 1.2)
ratio_panel(axs[1], ss, SYN, "n", ("N", 5000), title="synthetic, N=5000"); axs[1].set_ylim(0.3, 1.25)
ratio_panel(axs[2], sr, REAL, "N", ("n", 200), title="real data, n=200"); axs[2].set_ylim(0.9, 1.2)
ratio_panel(axs[3], ss, SYN, "N", ("n", 200), title="synthetic, n=200"); axs[3].set_ylim(0.3, 1.25)
axs[0].set_ylabel("width AIPW-auto / width PPI++"); axs[2].set_ylabel("width AIPW-auto / width PPI++")
for a, x in zip(axs, ["labeled n", "labeled n", "unlabeled N", "unlabeled N"]): a.set_xlabel(x)
h1, l1 = axs[0].get_legend_handles_labels(); h2, l2 = axs[1].get_legend_handles_labels()
fig.legend(h1 + h2, l1 + l2, ncol=4, loc="lower center", fontsize=6, frameon=False, bbox_to_anchor=(.5, -.08))
fig.tight_layout(); fig.savefig(FG + "fig_ratio.pdf", bbox_inches="tight"); plt.close()

# ------------------------------------------------------------------ Fig 3: predicted vs observed ratio
pv = pd.read_csv(R + "pred_vs_obs.csv"); pv = pv[pv.method == "aipw-auto"]
fig, ax = plt.subplots(figsize=(3.4, 3.2))
for (suite, mk), lab in zip([("real", "o"), ("synth", "s")], ["real", "synthetic"]):
    for n, a in [(50, .35), (200, .6), (1000, 1.0)]:
        g = pv[(pv.suite == suite) & (pv.n == n) & (pv.N == 5000)]
        ax.scatter(g.pred_ratio, g.obs_ratio, marker=mk, s=14, alpha=a, color=pal[0] if suite == "real" else pal[3], label=f"{lab}, n={n}")
ax.plot([.3, 1.25], [.3, 1.25], "k:", lw=.7); ax.set_xlabel("asymptotic prediction  sqrt(V_eff / V_PPI++)"); ax.set_ylabel("observed width ratio")
ax.legend(fontsize=6, frameon=False); fig.tight_layout(); fig.savefig(FG + "fig_pred_obs.pdf"); plt.close()

# ------------------------------------------------------------------ Bootstrap-t table + summary file
if os.path.exists(R + "boot.csv.gz"):
    b = pd.read_csv(R + "boot.csv.gz")
    b["cov_bt"] = (b.lo_bt <= b.truth) & (b.truth <= b.hi_bt); b["cov_z"] = (b.lo_z <= b.truth) & (b.truth <= b.hi_z)
    b["w_bt"] = b.hi_bt - b.lo_bt; b["w_z"] = b.hi_z - b.lo_z
    rows = []
    for (ds, n), g in b.groupby(["dataset", "n"]):
        P = g.pivot(index="rep", columns="method", values="w_bt")
        for m in P.columns:
            gm = g[g.method == m]
            rows.append(dict(dataset=ds, n=n, method=m, cov_bt=gm.cov_bt.mean(), cov_bt_se=np.sqrt(gm.cov_bt.mean() * (1 - gm.cov_bt.mean()) / len(gm)),
                             cov_z=gm.cov_z.mean(), w_bt=gm.w_bt.mean(), w_z=gm.w_z.mean(), ratio_bt=(P[m] / P["ppi++"]).mean(),
                             ratio_bt_of_means=P[m].mean() / P["ppi++"].mean(), med_ratio=np.median(P[m] / P["ppi++"]), reps=len(gm)))
    bs = pd.DataFrame(rows); bs.to_csv(bp, index=False)
    for n in [50, 200]:
        L = []
        for ds in REAL:
            x = {m: bs[(bs.dataset == ds) & (bs.n == n) & (bs.method == m)].iloc[0] for m in ["classical", "ppi++", "aipw-lin"]}
            L.append(f"{NICE(ds)} & " + " & ".join("%.1f" % (100 * x[m].cov_bt) for m in x) + " & " + " & ".join("%.3f" % x[m].ratio_bt_of_means for m in ["classical", "aipw-lin"]) + " \\\\")
        open(TB + f"boot_n{n}.tex", "w").write(("\n".join(L)).rstrip("\\") + "\n")

# ------------------------------------------------------------------ Fig 2: coverage vs n (real), with bootstrap-t if available

fig, axs = plt.subplots(3, 3, figsize=(7.5, 6), sharex=True)
sty = {"classical": ("0.5", "--"), "ppi++": (pal[0], "-"), "aipw-lin": (pal[3], "-")}
bs = pd.read_csv(bp) if os.path.exists(bp) else None
for ax, ds in zip(axs.ravel(), REAL):
    for m, (c, ls) in sty.items():
        g = sr[(sr.dataset == ds) & (sr.method == m) & (sr.N == 5000)].sort_values("n")
        ax.errorbar(g.n, 100 * g.cov_z, yerr=100 * 1.96 * g.cov_z_se, color=c, ls=ls, lw=1, ms=2, marker="o", capsize=0, label=m + " (Wald)")
        if bs is not None and m != "classical":
            h = bs[(bs.dataset == ds) & (bs.method == m)].sort_values("n")
            ax.plot(h.n, 100 * h.cov_bt, color=c, ls=":", marker="s", ms=2, lw=1, label=m + " (boot-t)")
    ax.axhline(95, color="k", lw=.6); ax.set_xscale("log"); ax.set_title(ds.replace("_", " "), fontsize=8); ax.set_ylim(70, 100)
for ax in axs[:, 0]: ax.set_ylabel("coverage (%)")
for ax in axs[-1]: ax.set_xlabel("labeled n")
h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=5, loc="lower center", fontsize=6.5, frameon=False, bbox_to_anchor=(.5, -.03))
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FG + "fig_coverage.pdf", bbox_inches="tight"); plt.close()

# ------------------------------------------------------------------ shift & noclip tables
if os.path.exists(R + "shift.csv.gz"):
    d = pd.read_csv(R + "shift.csv.gz"); d["w"] = 2 * 1.959964 * d.se; d["cov"] = abs(d.est - d.truth) <= 1.959964 * d.se
    s = d.groupby(["n", "method"]).agg(cov=("cov", "mean"), w=("w", "mean"), bias=("est", lambda x: x.mean() - d.truth.iloc[0])).reset_index()
    s.to_csv(R + "shift_summary.csv", index=False)
    L = []
    for n in [100, 500, 5000]:
        r = " & ".join("%.1f" % (100 * s[(s.n == n) & (s.method == m)]["cov"].iloc[0]) for m in ["classical", "ppi", "ppi++", "aipw-lin", "aipw-auto"])
        L.append(f"{n} & {r} \\\\")
    open(TB + "shift.tex", "w").write(("\n".join(L)).rstrip("\\") + "\n")
if os.path.exists(R + "noclip.csv"):
    s = pd.read_csv(R + "noclip.csv")
    L = []
    for ds in s.dataset.unique():
        for n in [200, 1000]:
            a = s[(s.dataset == ds) & (s.n == n) & (s.method == "ppi++clipped")].iloc[0]; c = s[(s.dataset == ds) & (s.n == n) & (s.method == "ppi++unclipped")].iloc[0]
            L.append(f"{NICE(ds)} & {n} & {100*a['cov']:.1f} & {100*c['cov']:.1f} & {c.width/a.width:.3f} \\\\")
    open(TB + "noclip.tex", "w").write(("\n".join(L)).rstrip("\\") + "\n")
print("report done")
