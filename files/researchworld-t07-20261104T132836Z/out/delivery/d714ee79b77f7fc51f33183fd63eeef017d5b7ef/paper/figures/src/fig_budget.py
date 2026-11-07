"""C3: error vs budget.  Outputs: budget_relrmse.pdf (main text), budget_grid_<protocol>.pdf (appendix).

relrmse: per benchmark ratio RMSE(method, n) / RMSE(random mean, n) from the committed cells.csv point estimates;
line = geometric mean over benchmarks, band = 95% percentile bootstrap over benchmarks (benchmarks, not models, are the
resampling unit; HELM benchmarks share models, so the band is optimistic for them).
grid: per-benchmark RMSE (accuracy units, 0-1 scale) with the committed model-level 95% bootstrap CI.
"""
import sys, numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import common as C

MAIN = ["sources_only", "random", "ridge", "anchor_irt", "aipw_rand", "best_cv", "mass", "mass_ens"]


def methods_present(cells, want):
    have = set(cells.method)
    return [m for m in want if m in have]


def add_best_cv(d, best):
    """Pseudo-method `best_cv`: per benchmark and protocol, the baseline with the lowest source-CV RMSE (best_baseline.csv)."""
    rows = []
    for r in best.itertuples():
        g = d[(d.bench == r.bench) & (d.protocol == r.protocol) & (d.method == r.method)].copy()
        g["method"] = "best_cv"
        rows.append(g)
    return __import__("pandas").concat([d] + rows)


def relrmse(cells, protocols=("random", "extrap"), want=MAIN, best=None):
    d = cells[(cells.metric == "rmse") & cells.protocol.isin(protocols)]
    if best is not None:
        d = add_best_cv(d, best)
    fig, axes = plt.subplots(1, len(protocols), figsize=(C.TEXTWIDTH, 2.5), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, p in zip(axes, protocols):
        dp = d[d.protocol == p]
        piv = dp.pivot_table(index=["bench", "n"], columns="method", values="mean")
        ns = sorted(dp.n.unique())
        for m in methods_present(dp, want):
            if m == "random":
                continue
            g = []
            for n in ns:
                r = (piv.xs(n, level="n")[m] / piv.xs(n, level="n")["random"]).dropna()
                g.append(C.geomean_ci(r.values) + (len(r),))
            g = np.array(g)
            ax.plot(ns, g[:, 0], color=C.color(m), marker=C.MARKER.get(m, "o"), ls=C.LS.get(m, "-"),
                    label=C.ml(m), zorder=3 if m == "mass_ens" else 2, lw=1.8 if m in ("mass_ens", "mass") else 1.1)
            ax.fill_between(ns, g[:, 1], g[:, 2], color=C.color(m), alpha=0.15, lw=0)
        ax.axhline(1, color="k", lw=0.8)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(0.45, 2.2)
        ax.set_xticks(ns); ax.set_xticklabels([str(n) for n in ns])
        ax.set_xlabel("target-model items evaluated, $n$")
        ax.set_title(C.PROTO_LABEL[p], fontsize=7.5)
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:g}" if v in (0.5, 0.7, 1.5, 2) else ""))
    axes[0].set_ylabel("RMSE relative to random mean\n(geo. mean over benchmarks)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.24), columnspacing=1.0, handlelength=1.6)
    C.save(fig, "budget_relrmse.pdf")


def grid(cells, protocol, want=MAIN, best=None):
    d = cells[(cells.metric == "rmse") & (cells.protocol == protocol)]
    if best is not None:
        d = add_best_cv(d, best)
    bs = C.benches(d)
    nc = 4; nr = int(np.ceil(len(bs) / nc))
    fig, axes = plt.subplots(nr, nc, figsize=(C.TEXTWIDTH, 1.25 * nr + 0.9), sharex=True)
    axes = axes.ravel()
    for ax, b in zip(axes, bs):
        for m in methods_present(d, want):
            g = d[(d.bench == b) & (d.method == m)].sort_values("n")
            ax.plot(g.n, g["mean"], color=C.color(m), ls=C.LS.get(m, "-"), lw=1.5 if m in ("mass_ens", "mass") else 0.9, label=C.ml(m))
            ax.fill_between(g.n, g.ci_lo, g.ci_hi, color=C.color(m), alpha=0.15, lw=0)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(C.bl(b), fontsize=7)
        ax.set_xticks([10, 50, 200]); ax.set_xticklabels(["10", "50", "200"]); ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:g}" if f"{v:.0e}"[0] in "25" else ""))
        ax.tick_params(axis="y", which="minor", labelsize=5.5)
    for ax in axes[len(bs):]:
        ax.axis("off")
    h, l = axes[0].get_legend_handles_labels()
    fig.supxlabel("items evaluated, $n$", fontsize=8, y=0.095); fig.supylabel("RMSE (accuracy, 0--1)", fontsize=8, x=0.0)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.01), handlelength=2.2, fontsize=6.5)
    C.save(fig, f"budget_grid_{protocol}.pdf")


if __name__ == "__main__":
    C.style()
    cells = C.load("cells.csv")
    relrmse(cells, best=C.load("best_baseline.csv"))
    for p in ("random", "extrap"):
        grid(cells, p, best=C.load("best_baseline.csv"))
