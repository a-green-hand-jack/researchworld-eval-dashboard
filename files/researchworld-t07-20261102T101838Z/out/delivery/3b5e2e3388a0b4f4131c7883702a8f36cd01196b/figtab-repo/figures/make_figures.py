"""Figures and summary table from the per-prediction results table.
Usage: python3 make_figures.py <results table (csv|parquet)> <out dir> [--baseline NAME] [--table-n N]
        [--methods A,B,...] [--scatter-n N]
Every figure's numbers come from the results table only; a CSV of the plotted values is written beside each figure."""
import argparse, pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import common
from common import style, label, TEXTWIDTH_IN
import metrics as M

ap = argparse.ArgumentParser()
ap.add_argument("results"); ap.add_argument("out")
ap.add_argument("--baseline", default="random")
ap.add_argument("--methods", default=None, help="ordered, comma separated; default: order of appearance")
ap.add_argument("--table-n", type=int, default=None)
ap.add_argument("--scatter-n", type=int, default=None)
a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

df = M.load(a.results)
methods = a.methods.split(",") if a.methods else list(dict.fromkeys(df.method))
df = df[df.method.isin(methods)]
common.register(methods)
runs = M.per_run(df)
runs.to_csv(out / "runs.csv", index=False)
splits = list(dict.fromkeys(df.split_type))
ns = sorted(df.n.unique())
benches = list(dict.fromkeys(df.benchmark))
LAB = dict(mae="MAE (accuracy points)", rmse="RMSE (accuracy points)", spearman="Spearman $\\rho$", kendall="Kendall $\\tau$")


def draw(ax, tab, extra=None, **kw):
    for m in methods:
        t = tab[tab.method == m].sort_values("n")
        if t.empty:
            continue
        s = style(m)
        ax.plot(t.n, t["mean"], color=s["color"], marker=s["marker"], ls=s["ls"], lw=s["lw"], label=label(m), **kw)
        ax.fill_between(t.n, t.lo, t.hi, color=s["color"], alpha=.15, lw=0)
    ax.set_xscale("log")
    tk = [n for n in ns if n in (10, 50, 200)]; ax.set_xticks(tk); ax.set_xticklabels([str(n) for n in tk]); ax.minorticks_off()
    ax.set_xlabel("items evaluated $n$")


def curve_fig(col, fname, split):
    """Per-benchmark grid (3 columns, appendix) of metric vs. n with 95% CIs over seeds."""
    r = runs[runs.split_type == split]
    nb = len(benches)
    ncol = 3
    nrow = int(np.ceil(nb / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(TEXTWIDTH_IN, 1.75 * nrow + .6), squeeze=False)
    allt = []
    for ax, b in zip(axs.ravel(), benches):
        t = M.boot_mean(r[r.benchmark == b], col, ["method", "n"])
        allt.append(t.assign(benchmark=b))
        draw(ax, t); ax.set_title(b)
        ax.tick_params(labelsize=7.5)
    for ax in axs.ravel()[nb:]:
        ax.axis("off")
    for ax in axs[:, 0]:
        ax.set_ylabel(LAB[col])
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(.5, -.07))
    fig.savefig(out / f"{fname}.pdf"); plt.close(fig)
    pd.concat(allt).to_csv(out / f"{fname}.csv", index=False)


def macro_fig():
    """Main-text figure: macro-average over benchmarks, MAE and Spearman vs. n, one column per split type."""
    cols = ["mae", "spearman"]
    fig, axs = plt.subplots(2, len(splits), figsize=(TEXTWIDTH_IN, 4.0), squeeze=False, sharex=True)
    allt = []
    for j, sp in enumerate(splits):
        r = runs[runs.split_type == sp]
        nb_at = r.groupby("n").benchmark.nunique()
        full_n = nb_at[nb_at == nb_at.max()].index   # macro-average only where every benchmark has the budget
        for i, col in enumerate(cols):
            agg = M.macro(r[r.n.isin(full_n)], col, ["method", "n"])
            allt.append(agg.assign(split_type=sp, metric=col))
            ax = axs[i, j]; draw(ax, agg)
            if i == 0: ax.set_title(f"{sp.replace('_', ' ')} split ({nb_at.max()} benchmarks)")
            if j == 0: ax.set_ylabel(LAB[col])
            ax.tick_params(labelsize=8)
            ax.set_xticks([n for n in full_n]); ax.set_xticklabels([str(n) for n in full_n])
            if i == 0: ax.set_xlabel("")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.5, 0.0))
    fig.savefig(out / "fig_macro_curves.pdf"); plt.close(fig)
    pd.concat(allt).to_csv(out / "fig_macro_curves.csv", index=False)


macro_fig()
for sp in splits:
    curve_fig("mae", f"fig_mae_vs_n_{sp}", sp)
    curve_fig("spearman", f"fig_spearman_vs_n_{sp}", sp)

# --- paired differences to the baseline, macro-averaged, per split type -------------------------------
if a.baseline in methods:
    rows = []
    for col in ["mae", "spearman"]:
        d = M.paired_diff(runs, col, a.baseline).rename(columns={"diff": col + "_diff"})
        rows.append(M.macro(d, col + "_diff", ["split_type", "method", "n"]).assign(metric=col))
    pdf = pd.concat(rows)
    pdf = pdf[pdf.method != "const"]   # B0 ignores the target's outcomes and is off-scale; see the curve figures
    pdf.to_csv(out / "fig_paired_diff.csv", index=False)
    fig, axs = plt.subplots(2, len(splits), figsize=(TEXTWIDTH_IN, 3.3), squeeze=False, sharex=True, sharey="row")
    for j, sp in enumerate(splits):
        for i, col in enumerate(["mae", "spearman"]):
            ax = axs[i, j]
            t = pdf[(pdf.split_type == sp) & (pdf.metric == col)]
            draw(ax, t)
            ax.axhline(0, color="k", lw=.8)
            if i == 0: ax.set_title(sp.replace("_", " "))
            if j == 0:
                ax.set_ylabel(("$\\Delta$ MAE (points)" if col == "mae" else "$\\Delta$ Spearman") + f"\nvs. {label(a.baseline)}"
                              + ("\n(<0 better)" if col == "mae" else "\n(>0 better)"))
    h, l = axs[0, 0].get_legend_handles_labels()
    h2, l2 = h, l
    fig.legend(h2, l2, loc="lower center", ncol=min(len(l2), 5), frameon=False, bbox_to_anchor=(.5, -.06))
    fig.tight_layout(); fig.savefig(out / "fig_paired_diff.pdf"); plt.close(fig)

# --- predicted vs. true scatter ---------------------------------------------------------------------
sn = a.scatter_n or ns[len(ns) // 2]
SC = [m_ for m_ in ["random+mean", "random+cal", "anchor+irt", "omp+ridge", "strat+lowrank_dr", "strat+lowrank_eb"] if m_ in methods]
for sp in splits:
    d = df[(df.n == sn) & (df.split_type == sp) & df.method.isin(SC)].copy()
    if d.empty: continue
    # strong targets: top quartile of the true score within the benchmark (among the targets present)
    q = d.groupby("benchmark").true.transform(lambda x: x.quantile(.75))
    d["strong"] = d.true >= q
    nr = int(np.ceil(len(SC) / 3))
    fig, axs = plt.subplots(nr, 3, figsize=(TEXTWIDTH_IN, 1.8 * nr), squeeze=False, sharex=True, sharey=True)
    for ax, m_ in zip(axs.ravel(), SC):
        g = d[d.method == m_]
        for strong, col, z in [(False, "#999999", 1), (True, "#D55E00", 2)]:
            h = g[g.strong == strong]
            ax.scatter(h.true * 100, h.pred * 100, s=1.5, alpha=.2, color=col, rasterized=True, zorder=z, lw=0)
        ax.plot([0, 100], [0, 100], "k-", lw=.7); ax.set_title(label(m_))
        ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    for ax in axs[-1]: ax.set_xlabel("true accuracy (%)")
    for ax in axs[:, 0]: ax.set_ylabel("predicted accuracy (%)")
    for ax in axs.ravel()[len(SC):]: ax.axis("off")
    fig.text(.5, -.01, f"{sp} split, $n$={sn}, all benchmarks pooled; orange = top quartile of true score within benchmark",
             ha="center", fontsize=6.5)
    fig.tight_layout(); fig.savefig(out / f"fig_scatter_{sp}.pdf"); plt.close(fig)
    d.groupby(["method", "strong"]).apply(lambda g: pd.Series(dict(
        mean_signed_err_pts=100 * (g.pred - g.true).mean(), n_points=len(g))), include_groups=False).to_csv(out / f"fig_scatter_{sp}_bias.csv")

# --- summary table ----------------------------------------------------------------------------------
tn = a.table_n or ns[len(ns) // 2]
TM = [m_ for m_ in methods if m_ != "const"]   # B0 does not use the target's outcomes: shown in the curves, not the table
for sp, mcol in [(s_, c_) for s_ in splits for c_ in ("mae", "rmse", "kendall")]:
    r = runs[(runs.n == tn) & (runs.split_type == sp)]
    lines = [r"{\scriptsize\setlength{\tabcolsep}{2.5pt}", r"\begin{tabular}{l" + "r" * len(TM) + "}", r"\toprule",
             "Benchmark & " + " & ".join(label(m_).replace("random+cal.", "rand.+cal.") for m_ in TM) + r" \\", r"\midrule"]
    dd = M.paired_diff(r, mcol, a.baseline) if a.baseline in methods else None
    csv = []
    for b_ in benches + ["macro"]:
        cells = []
        for m_ in TM:
            sel = r[r.method == m_] if b_ == "macro" else r[(r.benchmark == b_) & (r.method == m_)]
            t = M.macro(sel, mcol, ["method"]) if b_ == "macro" else M.boot_mean(sel, mcol, ["method"])
            if t.empty: cells.append("--"); continue
            x = t.iloc[0]
            cell = f"{x['mean']:.3f}" if mcol == "kendall" else f"{x['mean']:.2f}"
            if m_ != a.baseline and dd is not None:
                dm = dd[dd.method == m_]
                dm = dm if b_ == "macro" else dm[dm.benchmark == b_]
                if len(dm):
                    q = (M.macro(dm, "diff", ["method"]) if b_ == "macro" else M.boot_mean(dm, "diff", ["method"])).iloc[0]
                    cell += r"$^{\downarrow}$" if q.hi < 0 else (r"$^{\uparrow}$" if q.lo > 0 else "")
                    csv.append(dict(metric=mcol, split_type=sp, n=tn, benchmark=b_, method=m_, mean=x["mean"], lo=x.lo, hi=x.hi,
                                    d_mean=q["mean"], d_lo=q.lo, d_hi=q.hi))
            else:
                csv.append(dict(metric=mcol, split_type=sp, n=tn, benchmark=b_, method=m_, mean=x["mean"], lo=x.lo, hi=x.hi))
            cells.append(cell)
        if b_ == "macro": lines.append(r"\midrule")
        lines.append(b_.replace("_", r"\_") + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}}"]
    (out / f"tab_{mcol}_{sp}_n{tn}.tex").write_text("\n".join(lines) + "\n")
    pd.DataFrame(csv).to_csv(out / f"tab_{mcol}_{sp}_n{tn}.csv", index=False)

# --- pairwise ranking accuracy vs. true score gap -----------------------------------------------------
bins = np.array([0, 1, 2, 5, 10, 20, 100.1])
pw = M.pairwise_by_gap(df[df.n == sn], bins)
if len(pw):
    fig, axs = plt.subplots(1, len(splits), figsize=(TEXTWIDTH_IN, 1.9), squeeze=False, sharey=True)
    xl = [f"{bins[i]:g}-{bins[i+1]:g}" if i < len(bins) - 2 else f">{bins[i]:g}" for i in range(len(bins) - 1)]
    tabs = []
    for ax, sp in zip(axs[0], splits):
        p = pw[pw.split_type == sp]
        t = M.macro(p, "acc", ["method", "bin"]).rename(columns={"bin": "n"}) if len(p) else pd.DataFrame()
        for m in methods:
            q = t[t.method == m].sort_values("n") if len(t) else t
            if len(q):
                s = style(m); x = q.n.to_numpy()
                ax.plot(x, q["mean"], color=s["color"], marker=s["marker"], ls=s["ls"], lw=s["lw"], label=label(m))
                ax.fill_between(x, q.lo, q.hi, color=s["color"], alpha=.15, lw=0)
        ax.axhline(.5, color="k", lw=.8); ax.set_xticks(range(len(xl))); ax.set_xticklabels(xl, rotation=30)
        ax.set_xlabel("true accuracy gap (points)"); ax.set_title(sp.replace("_", " ")); tabs.append(t.assign(split_type=sp))
    axs[0, 0].set_ylabel("pairwise ranking accuracy")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=min(len(l), 5), frameon=False, bbox_to_anchor=(.5, -.12))
    fig.tight_layout(); fig.savefig(out / "fig_pairwise_vs_gap.pdf"); plt.close(fig)
    pd.concat(tabs).to_csv(out / "fig_pairwise_vs_gap.csv", index=False)
print("done", sorted(p.name for p in out.iterdir()))
