"""C5: sensitivity to the number of source models and to the extrapolation fraction.  Output: sensitivity.pdf

Each point: RMSE relative to the random mean at the same n (n=100) in the same protocol, geometric mean over the 13 benchmarks
(all benchmarks were run in the sensitivity grids); band: 95% benchmark-level bootstrap.  Protocols `*_s025/_s05` keep 25%/50% of the
source models (1.0 = the main protocol, 20 repetitions; sensitivity runs use 10); `extrap_f01/_f03` hold out the strongest 10%/30% of
models (main = 20%).  Only the methods run in the sensitivity grids appear.
"""
import numpy as np
import matplotlib.pyplot as plt
import common as C

METHODS = ["ridge", "anchor_irt", "aipw_rand", "mass", "mass_ens"]
N = 100
PANELS = [
    ("(a) extrapolation", [("extrap", 1.0), ("extrap_s05", 0.5), ("extrap_s025", 0.25)], "source fraction kept"),
    ("(b) interpolation", [("random", 1.0), ("random_s05", 0.5), ("random_s025", 0.25)], "source fraction kept"),
    ("(c) extrapolation", [("extrap_f01", 0.1), ("extrap", 0.2), ("extrap_f03", 0.3)], "held-out fraction"),
]


def rel(cells, proto, m, n=N):
    d = cells[(cells.metric == "rmse") & (cells.protocol == proto) & (cells.n == n)]
    piv = d.pivot_table(index="bench", columns="method", values="mean")
    if m not in piv or "random" not in piv:
        return None
    r = (piv[m] / piv["random"]).dropna()
    return (C.geomean_ci(r.values) + (len(r),)) if len(r) >= 3 else None


def main():
    C.style()
    cells = C.load("cells.csv")
    fig, axes = plt.subplots(1, 3, figsize=(C.TEXTWIDTH, 2.3), sharey=True)
    for ax, (title, pts, xl) in zip(axes, PANELS):
        for m in METHODS:
            v = [(x, rel(cells, pr, m)) for pr, x in pts]
            v = sorted([(x, r) for x, r in v if r is not None])
            if len(v) < 2:
                continue
            x = [p[0] for p in v]; y = np.array([p[1] for p in v])
            ax.plot(x, y[:, 0], color=C.color(m), marker=C.MARKER.get(m, "o"), lw=1.6 if m.startswith("mass") else 1.0, label=C.ml(m))
            ax.fill_between(x, y[:, 1], y[:, 2], color=C.color(m), alpha=0.12, lw=0)
        ax.axhline(1, color="k", lw=0.8); ax.set_xlabel(xl, fontsize=7); ax.set_xticks([p[1] for p in pts])
        ax.set_title(title, fontsize=7)
        ax.set_yscale("log"); ax.set_ylim(0.45, 3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}" if v in (0.5, 0.7, 1.5, 2) else ""))
    axes[0].set_ylabel(f"RMSE rel. to random mean ($n={N}$)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(l), frameon=False, bbox_to_anchor=(0.5, -0.12))
    C.save(fig, "sensitivity.pdf")


if __name__ == "__main__":
    main()
