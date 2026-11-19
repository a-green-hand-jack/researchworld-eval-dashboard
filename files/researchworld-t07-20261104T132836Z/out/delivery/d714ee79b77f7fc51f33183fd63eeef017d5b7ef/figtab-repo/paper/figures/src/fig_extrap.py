"""C4: extrapolation failure view and interval coverage.
Outputs: extrap_scatter.pdf (true vs predicted full score, protocol `extrap`, n=50; `Sources only` omitted: constant prediction by construction), coverage.pdf.

Scatter: one point per held-out target model; prediction = mean over item-selection seeds (predictions_headline.csv);
orange = target scored above every source model, grey = within the source range.
Points are seed-averaged, so they show the systematic part of the error (bias), not the error of one run.  `bias` = mean of
(seed-averaged prediction - truth) over the plotted targets; `RMSE (one run)` = the per-draw RMSE of cells.csv (as in the tables),
which also contains the item-selection variance that averaging over 20 seeds removes.  coverage: share of target-model
predictions whose true score lies within +-1.96 SE of the method's reported standard error (coverage.csv), per benchmark.
"""
import numpy as np
import matplotlib.pyplot as plt
import common as C

SCAT_BENCH = ["mmlu_pro", "bbh", "musr"]
SCAT_METHODS = ["random", "ridge", "mass", "mass_ens"]


def scatter(pr, cells, n=50, benches=SCAT_BENCH, methods=SCAT_METHODS):
    d = pr[(pr.protocol == "extrap") & (pr.n == n)]
    benches = [b for b in benches if b in set(d.bench)]
    methods = [m for m in methods if m in set(d.method)]
    fig, axes = plt.subplots(len(benches), len(methods), figsize=(C.TEXTWIDTH, 1.35 * len(benches) + 0.5), squeeze=False)
    for i, b in enumerate(benches):
        for j, m in enumerate(methods):
            ax = axes[i, j]
            g = d[(d.bench == b) & (d.method == m)]
            if g.empty:
                ax.axis("off"); continue
            above = g.above_all_sources.astype(str).str.lower().isin(["true", "1", "1.0"])
            ax.scatter(g.true[~above], g.pred[~above], s=6, c=C.OI["grey"], lw=0, alpha=0.8)
            ax.scatter(g.true[above], g.pred[above], s=7, c=C.OI["verm"], lw=0, alpha=0.9)
            lo, hi = min(g.true.min(), g.pred.min()), max(g.true.max(), g.pred.max())
            pad = 0.05 * (hi - lo); lo, hi = lo - pad, hi + pad
            ax.plot([lo, hi], [lo, hi], color="k", lw=0.6)
            ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
            ax.xaxis.set_major_locator(plt.MaxNLocator(3)); ax.yaxis.set_major_locator(plt.MaxNLocator(3))
            bias = (g.pred - g.true).mean()
            r = cells[(cells.protocol == "extrap") & (cells.n == n) & (cells.bench == b) & (cells.method == m) & (cells.metric == "rmse")]
            txt = f"bias {bias:+.3f}" + (f"\nRMSE (one run) {r['mean'].iloc[0]:.3f}" if len(r) else "")
            ax.text(0.04, 0.95, txt, transform=ax.transAxes, va="top", fontsize=5, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.8))
            if i == 0:
                ax.set_title(C.ml(m), fontsize=7, color="k")
            if j == 0:
                ax.set_ylabel(f"{C.bl(b)}\npredicted", fontsize=7)
            if i == len(benches) - 1:
                ax.set_xlabel("true full-benchmark score", fontsize=6.5)
    h = [plt.Line2D([], [], marker="o", ls="", color=c, ms=3, label=l) for c, l in
         [(C.OI["grey"], "within source range"), (C.OI["verm"], "above all sources")]]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    C.save(fig, "extrap_scatter.pdf")


def coverage(cv):
    """Coverage of the nominal 95% interval vs n; thin lines: benchmarks, thick: mean over benchmarks."""
    ms = [m for m in ["mass_ens"] if m in set(cv.method)]
    protos = [p for p in ["random", "extrap"] if p in set(cv.protocol)]
    fig, axes = plt.subplots(1, len(protos), figsize=(C.TEXTWIDTH, 2.2), sharey=True, squeeze=False)
    for ax, p in zip(axes[0], protos):
        for m in ms:
            piv = cv[(cv.protocol == p) & (cv.method == m)].pivot(index="n", columns="bench", values="cover95")
            ax.plot(piv.index, piv.values, color=C.color(m), lw=0.5, alpha=0.4)
            ax.plot(piv.index, piv.mean(axis=1), color=C.color(m), lw=1.8, marker="o", label=f"{C.ml(m)} (mean over benchmarks)")
        ax.axhline(0.95, color="k", ls="--", lw=0.7)
        ax.set_xscale("log"); ns = sorted(cv.n.unique()); ax.set_xticks(ns); ax.set_xticklabels(map(str, ns))
        ax.xaxis.set_minor_locator(plt.NullLocator()); ax.set_xlabel("items evaluated, $n$")
        ax.set_title(C.PROTO_LABEL[p], fontsize=7.5); ax.set_ylim(0, 1.02)
    axes[0, 0].set_ylabel("coverage of nominal 95% interval")
    axes[0, 0].legend(frameon=False, fontsize=6.5, loc="lower right")
    C.save(fig, "coverage.pdf")


if __name__ == "__main__":
    C.style()
    scatter(C.load("predictions_headline.csv"), C.load("cells.csv"))
    cv = C.load("coverage.csv", required=False)
    if cv is not None:
        coverage(cv)
