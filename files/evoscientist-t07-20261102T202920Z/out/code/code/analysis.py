"""Aggregate raw results into the tables / figures used in the paper.
Usage: python code/analysis.py results/main paper/gen
Outputs: CSV tables, LaTeX table fragments (paper/gen/*.tex) and PDF figures (paper/gen/*.pdf).
"""
import os, sys, itertools, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from metrics import tidy, coverage

RES = sys.argv[1] if len(sys.argv) > 1 else "results/main"
OUT = sys.argv[2] if len(sys.argv) > 2 else "paper/gen"
os.makedirs(OUT, exist_ok=True)
DEV = ["arc_challenge", "musr", "commonsense", "med_qa"]
BUDGETS = [10, 25, 50, 100, 200]
REF = "rand_ht"
rng = np.random.default_rng(12345)
NB = 4000

df = tidy(RES)
df.to_csv(os.path.join(OUT, "all_metrics.csv"), index=False)
benches_all = sorted(df.bench.unique())
TEST = [b for b in benches_all if b not in DEV]
beta_df = df[df.method.str.endswith("_beta")]
df = df[~df.method.str.endswith("_beta")]

NAMES = {
    "rand_ht": "Random subset, mean",
    "sort_ht": "Difficulty-stratified subset, mean",
    "pps_ht": "Residual-PPS subset, HT mean",
    "rand_plugin": "Random subset + latent-factor plug-in",
    "sort_plugin": "Stratified subset + plug-in",
    "pps_plugin": "PPS subset + plug-in",
    "info_plugin": "Max-information items + plug-in",
    "info_ht": "Max-information items, mean",
    "anchor_wmean": "Anchor points, weighted mean",
    "anchor_plugin": "Anchor points + plug-in",
    "ridge_rand": "Random subset + ridge assessor",
    "ridge_sort": "Stratified subset + ridge assessor",
    "rand_diff": "Random subset + cross-fit difference",
    "sort_diff": "Stratified subset + cross-fit difference",
    "pps_diff": "PPS subset + cross-fit difference",
    "rand_greg": "Random subset + cross-fit GREG",
    "sort_greg": "Stratified subset + cross-fit GREG",
    "pps_greg": "PPS subset + cross-fit GREG",
    "const_srcmean": "Constant: mean source accuracy",
}


# ------------------------------------------------------------------ helpers
def cell_array(d, method, scen, n, benches):
    """array [bench, rep] of a metric for one method."""
    x = d[(d.method == method) & (d.scen == scen) & (d.n == n) & d.bench.isin(benches)]
    return x.pivot(index="bench", columns="rep", values="mae").loc[benches].values


def boot_logratio(A, B, nb=NB):
    """Two-level bootstrap (benchmarks, then repetitions within benchmark; paired) of
    log( mean_b-geo of  mean_rep A / mean_rep B ). Returns point, lo, hi (as ratio)."""
    nbm, R = A.shape
    pt = np.mean(np.log(A.mean(1) / B.mean(1)))
    out = np.empty(nb)
    for i in range(nb):
        bi = rng.integers(0, nbm, nbm)
        ri = rng.integers(0, R, (nbm, R))
        a = np.take_along_axis(A[bi], ri, 1).mean(1); b = np.take_along_axis(B[bi], ri, 1).mean(1)
        out[i] = np.mean(np.log(a / b))
    return np.exp(pt), np.exp(np.percentile(out, 2.5)), np.exp(np.percentile(out, 97.5))


def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(run, 1.0)
    return adj


def fmt_ratio(t):
    return f"{t[0]:.2f} [{t[1]:.2f}, {t[2]:.2f}]"


# ------------------------------------------------------------------ main table: relative MAE vs random-subset mean
MAIN = ["rand_ht", "sort_ht", "info_ht", "anchor_wmean", "ridge_rand", "rand_plugin", "anchor_plugin", "info_plugin",
        "rand_diff", "rand_greg", "sort_greg", "pps_greg", "const_srcmean"]
rows = []
for scen in ["random", "top", "bottom"]:
    for n in BUDGETS:
        for m in MAIN + [x for x in NAMES if x not in MAIN]:
            for grp, bl in [("test", TEST), ("dev", DEV)]:
                A = cell_array(df, m, scen, n, bl); B = cell_array(df, REF, scen, n, bl)
                pt, lo, hi = boot_logratio(A, B, nb=1000 if grp == "dev" else NB)
                rows.append(dict(scen=scen, n=n, method=m, group=grp, rel=pt, lo=lo, hi=hi,
                                 mae=A.mean(), mae_ref=B.mean()))
REL = pd.DataFrame(rows)
REL.to_csv(os.path.join(OUT, "relative_mae.csv"), index=False)

# absolute metrics pooled over test benchmarks (mean of benchmark means)
def pooled(metric, scen, n, m, benches=TEST):
    x = df[(df.method == m) & (df.scen == scen) & (df.n == n) & df.bench.isin(benches)]
    return x.groupby("bench")[metric].mean().mean()

# ---------------------------------------------------------------- Table 1 (LaTeX): n=50 and n=100, random & top
def table_main(ns=(50,), scens=("random", "top"), fn="tab_main.tex", methods=MAIN):
    lines = []
    hdr = "Method & " + " & ".join(f"{s} $n{{=}}{n}$" for s in scens for n in ns)
    for m in methods:
        cells = []
        for s in scens:
            for n in ns:
                r = REL[(REL.scen == s) & (REL.n == n) & (REL.method == m) & (REL.group == "test")].iloc[0]
                sp = pooled("spearman", s, n, m)
                cells.append(f"{r.rel:.2f} [{r.lo:.2f},{r.hi:.2f}] / {r.mae*100:.1f} / {sp:.2f}" if m != "const_srcmean"
                             else f"{r.rel:.2f} [{r.lo:.2f},{r.hi:.2f}] / {r.mae*100:.1f} / --")
        lines.append(NAMES[m].replace("&", "\\&") + " & " + " & ".join(cells) + " \\\\")
    open(os.path.join(OUT, fn), "w").write("\n".join(lines))

table_main((25, 50, 100), ("random",), "tab_main_random.tex")
table_main((25, 50, 100), ("top",), "tab_main_top.tex")
table_main((25, 50, 100), ("bottom",), "tab_main_bottom.tex")

# ---------------------------------------------------------------- ablation: sampler x estimator
abl = []
for scen in ["random", "top", "bottom"]:
    for n in [25, 50, 100]:
        for samp in ["rand", "sort", "pps"]:
            row = dict(scen=scen, n=n, sampler=samp)
            for est in ["ht", "plugin", "diff", "greg"]:
                r = REL[(REL.scen == scen) & (REL.n == n) & (REL.method == f"{samp}_{est}") & (REL.group == "test")].iloc[0]
                row[est] = f"{r.rel:.2f} [{r.lo:.2f},{r.hi:.2f}]"
                row[est + "_pt"] = r.rel
            abl.append(row)
ABL = pd.DataFrame(abl)
ABL.to_csv(os.path.join(OUT, "ablation.csv"), index=False)

# ---------------------------------------------------------------- paired significance tests (benchmark-level)
PAIRS = [("rand_greg", "rand_ht"), ("rand_greg", "rand_plugin"), ("sort_greg", "sort_ht"), ("pps_greg", "sort_greg"),
         ("rand_plugin", "rand_ht"), ("rand_greg", "anchor_wmean"), ("rand_greg", "anchor_plugin"), ("rand_greg", "ridge_rand"),
         ("rand_diff", "rand_greg"), ("sort_greg", "rand_plugin"), ("sort_greg", "sort_plugin")]
prow = []
for scen in ["random", "top", "bottom"]:
    for n in [25, 50, 100]:
        ps = []
        for a, b in PAIRS:
            A = cell_array(df, a, scen, n, TEST); B = cell_array(df, b, scen, n, TEST)
            lr = np.log(A.mean(1) / B.mean(1))
            p = wilcoxon(lr).pvalue if np.any(lr != 0) else 1.0
            pt, lo, hi = boot_logratio(A, B)
            ps.append(p)
            prow.append(dict(scen=scen, n=n, A=a, B=b, ratio=pt, lo=lo, hi=hi, wins=int((lr < 0).sum()), nb=len(lr), p=p))
        adj = holm(ps)
        for i, a in enumerate(adj):
            prow[len(prow) - len(ps) + i]["p_holm"] = a
PT = pd.DataFrame(prow)
PT.to_csv(os.path.join(OUT, "pairwise_tests.csv"), index=False)

# ---------------------------------------------------------------- per-benchmark tables (MAE, %-points) n=50
def per_bench(scen, n, metric="mae", scale=100):
    x = df[(df.scen == scen) & (df.n == n)]
    t = x.pivot_table(index="method", columns="bench", values=metric, aggfunc="mean") * scale
    return t
for scen in ["random", "top"]:
    for n in [50]:
        t = per_bench(scen, n)
        t.to_csv(os.path.join(OUT, f"perbench_mae_{scen}_{n}.csv"))

# ---------------------------------------------------------------- bias (signed error) and other metrics
bias_rows = []
for scen in ["random", "top", "bottom"]:
    for n in BUDGETS:
        for m in NAMES:
            bias_rows.append(dict(scen=scen, n=n, method=m, bias=pooled("bias", scen, n, m) * 100,
                                  rmse=pooled("rmse", scen, n, m) * 100, mae=pooled("mae", scen, n, m) * 100,
                                  spearman=pooled("spearman", scen, n, m), kendall=pooled("kendall", scen, n, m)))
BI = pd.DataFrame(bias_rows)
BI.to_csv(os.path.join(OUT, "pooled_metrics.csv"), index=False)

# ---------------------------------------------------------------- coverage
cov = coverage(RES)
cov = cov[cov.bench.isin(TEST)]
cov.to_csv(os.path.join(OUT, "coverage_all.csv"), index=False)
covs = cov.groupby(["scen", "n", "method"]).agg(cover=("cover", "mean"), width=("width", "mean")).reset_index()
covs.to_csv(os.path.join(OUT, "coverage.csv"), index=False)
# coverage bootstrap over benchmarks of benchmark-mean coverage
cb = cov.groupby(["scen", "n", "method", "bench"]).cover.mean().reset_index()
cov_ci = []
for (s, n, m), g in cb.groupby(["scen", "n", "method"]):
    v = g.cover.values
    bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(2000)]
    cov_ci.append(dict(scen=s, n=n, method=m, cover=v.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                       min_bench=v.min()))
pd.DataFrame(cov_ci).to_csv(os.path.join(OUT, "coverage_ci.csv"), index=False)

# ---------------------------------------------------------------- betas
bd = beta_df[beta_df.bench.isin(TEST)].groupby(["scen", "method", "n"]).beta.mean().reset_index()
bd.to_csv(os.path.join(OUT, "beta_mean.csv"), index=False)

# ================================================================== FIGURES
plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False})
STY = {
    "rand_ht": ("Random mean", "k", "-", "o"),
    "sort_ht": ("Stratified mean", "0.45", "-", "s"),
    "anchor_wmean": ("Anchor points", "tab:brown", "--", "v"),
    "ridge_rand": ("Ridge assessor", "tab:purple", "--", "^"),
    "rand_plugin": ("Random + plug-in", "tab:orange", "-", "D"),
    "anchor_plugin": ("Anchor + plug-in", "tab:olive", ":", "P"),
    "info_plugin": ("Max-info + plug-in", "tab:pink", ":", "X"),
    "rand_greg": ("Random + GREG (ours)", "tab:blue", "-", "o"),
    "sort_greg": ("Stratified + GREG (ours)", "tab:cyan", "-", "s"),
    "pps_greg": ("PPS + GREG (ours)", "tab:green", "-", "^"),
}
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.5), sharey=False)
for ax, scen, ttl in zip(axs, ["random", "top", "bottom"], ["random model split", "targets = strongest 20%", "targets = weakest 20%"]):
    for m, (lab, c, ls, mk) in STY.items():
        r = REL[(REL.scen == scen) & (REL.method == m) & (REL.group == "test")].sort_values("n")
        ax.plot(r.n, r.rel, color=c, ls=ls, marker=mk, ms=3, lw=1.1, label=lab)
        if m in ("rand_greg", "rand_plugin", "rand_ht"):
            ax.fill_between(r.n, r.lo, r.hi, color=c, alpha=0.12, lw=0)
    ax.axhline(1, color="gray", lw=0.5)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels(BUDGETS)
    ax.set_title(ttl); ax.set_xlabel("evaluated items $n$")
axs[0].set_ylabel("MAE relative to random-subset mean")
axs[2].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_rel_mae.pdf"), bbox_inches="tight"); plt.close()

# bias figure
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.2), sharey=False)
for ax, scen, ttl in zip(axs, ["random", "top", "bottom"], ["random split", "strongest 20% targets", "weakest 20% targets"]):
    for m in ["rand_ht", "rand_plugin", "anchor_plugin", "ridge_rand", "rand_greg", "pps_greg", "const_srcmean"]:
        lab, c, ls, mk = STY.get(m, ("Constant source mean", "tab:red", ":", "x"))
        r = BI[(BI.scen == scen) & (BI.method == m)].sort_values("n")
        ax.plot(r.n, r.bias, color=c, ls=ls, marker=mk, ms=3, lw=1.1, label=lab)
    ax.axhline(0, color="gray", lw=0.5); ax.set_xscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels(BUDGETS)
    ax.set_title(ttl); ax.set_xlabel("evaluated items $n$")
axs[0].set_ylabel("mean signed error (pp)")
axs[2].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_bias.pdf"), bbox_inches="tight"); plt.close()

# spearman figure
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.2))
for ax, scen, ttl in zip(axs, ["random", "top", "bottom"], ["random split", "strongest 20% targets", "weakest 20% targets"]):
    for m, (lab, c, ls, mk) in STY.items():
        r = BI[(BI.scen == scen) & (BI.method == m)].sort_values("n")
        ax.plot(r.n, r.spearman, color=c, ls=ls, marker=mk, ms=3, lw=1.1, label=lab)
    ax.set_xscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels(BUDGETS); ax.set_title(ttl); ax.set_xlabel("evaluated items $n$")
axs[0].set_ylabel("Spearman $\\rho$ among targets")
axs[2].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_spearman.pdf"), bbox_inches="tight"); plt.close()

# coverage figure
ci = pd.read_csv(os.path.join(OUT, "coverage_ci.csv"))
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.0), sharey=True)
for ax, scen, ttl in zip(axs, ["random", "top", "bottom"], ["random split", "strongest 20%", "weakest 20%"]):
    for m, c, ls in [("rand_ht", "k", "-"), ("rand_diff", "tab:blue", "--"), ("rand_greg", "tab:blue", "-"), ("sort_greg", "tab:cyan", "-"),
                     ("pps_greg", "tab:green", "-")]:
        r = ci[(ci.scen == scen) & (ci.method == m)].sort_values("n")
        ax.plot(r.n, r.cover, color=c, ls=ls, marker="o", ms=2.5, lw=1, label=NAMES[m].replace("Random subset", "Rand.").replace("Difficulty-stratified subset", "Strat.").replace("PPS subset", "PPS"))
    ax.axhline(0.95, color="r", lw=0.6, ls=":"); ax.set_xscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels(BUDGETS)
    ax.set_title(ttl); ax.set_xlabel("evaluated items $n$"); ax.set_ylim(0.8, 1.0)
axs[0].set_ylabel("coverage of nominal 95\\% CI")
axs[2].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_coverage.pdf"), bbox_inches="tight"); plt.close()

# summary json for the text
summ = dict(test_benchmarks=TEST, dev_benchmarks=DEV, n_files=len([f for f in os.listdir(RES) if f.endswith(".npz")]))
json.dump(summ, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
print("done", summ)
