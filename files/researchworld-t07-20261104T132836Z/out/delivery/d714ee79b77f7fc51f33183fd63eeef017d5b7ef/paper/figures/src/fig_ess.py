"""C3: effective-sample-size gain vs budget.  Output: ess_gain.pdf

gain = (RMSE_random-mean / RMSE_method)^2 at the same n (ess_gain.csv, committed by experiment-repo): the factor by which the
random-subset mean would need more items to match the method's MSE.  Thin lines: one per benchmark; thick: median over benchmarks.
"""
import numpy as np
import matplotlib.pyplot as plt
import common as C

METHODS = ["ridge", "anchor_irt", "aipw_rand", "mass", "mass_ens"]


def main():
    C.style()
    e = C.load("ess_gain.csv")
    protos = [p for p in ["random", "extrap"] if p in set(e.protocol)]
    ms = [m for m in METHODS if m in set(e.method)]
    fig, axes = plt.subplots(1, len(protos), figsize=(C.TEXTWIDTH, 2.3), sharey=True, squeeze=False)
    for ax, p in zip(axes[0], protos):
        for m in ms:
            g = e[(e.protocol == p) & (e.method == m)]
            piv = g.pivot(index="n", columns="bench", values="ess_gain")
            ax.plot(piv.index, piv.values, color=C.color(m), lw=0.4, alpha=0.3)
            ax.plot(piv.index, piv.median(axis=1), color=C.color(m), lw=1.8, marker=C.MARKER.get(m, "o"), label=C.ml(m))
        ax.axhline(1, color="k", lw=0.8)
        ax.set_xscale("log"); ax.set_yscale("log")
        ns = sorted(e.n.unique()); ax.set_xticks(ns); ax.set_xticklabels(map(str, ns)); ax.xaxis.set_minor_locator(plt.NullLocator())
        ax.set_xlabel("items evaluated, $n$"); ax.set_title(C.PROTO_LABEL[p], fontsize=7.5)
    axes[0, 0].set_ylabel("effective-sample-size gain\n(MSE$_{\\rm random}$ / MSE$_{\\rm method}$)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(l), frameon=False, bbox_to_anchor=(0.5, -0.2))
    C.save(fig, "ess_gain.pdf")


if __name__ == "__main__":
    main()
