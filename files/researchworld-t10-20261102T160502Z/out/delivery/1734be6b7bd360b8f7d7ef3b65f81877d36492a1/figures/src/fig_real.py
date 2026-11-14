"""Real-data figures (C1, C3): coverage and paired width ratio vs n, per dataset, N = 20 n.

Writes   real_main        coverage + width ratio of M1-M4 (primary datasets)             [main text]
         real_correction  coverage + width ratio of M3, M5(M3), M4, M5(M4)                [main text / appendix]
         real_appendix    same as real_main for census_healthcare / census_education     [appendix]
         real_nsweep      n/N sweep (galaxies, forest, gene_expression, census_income)   [appendix]
Input: summary_final_{real_primary,real_appendix,real_nsweep}.csv, theory_predicted_ratios.csv.
"""
import numpy as np
import matplotlib.pyplot as plt
from common import *
from panels import *

setup()
M3 = "ppipp_pkg"


def fig_grid(df, dsets, cov_m, wid_m, name, ncol=3, floor=True, wlim=WLIM, legend_extra=True, ph=0.93):
    """Row pairs (coverage, width ratio) per row of datasets."""
    nr = int(np.ceil(len(dsets) / ncol))
    fig, axes = plt.subplots(2 * nr, ncol, figsize=(TEXT_W, nr * 2 * ph + 0.85), sharex=True, squeeze=False)
    ns = sorted(df["n"].unique())
    lo_cov = np.floor((df[df["method"].isin(cov_m)]["cov_lo"].min() - 0.01) * 20) / 20
    lo_cov = max(lo_cov, 0.3)
    for i, ds in enumerate(dsets):
        r, c = divmod(i, ncol)
        d = df[df["dataset"] == ds]
        a, b = axes[2 * r, c], axes[2 * r + 1, c]
        cov_panel(a, d, cov_m)
        a.set_title(DATASET_LABEL[ds], pad=2)
        a.set_ylim(lo_cov, 1.0)
        fl = (*floor_curve(d, ds), METHODS[M4][1]) if floor else None
        wid_panel(b, d, wid_m, floor=fl, ylim=wlim)
    for j in range(len(dsets), nr * ncol):
        for rr in (0, 1):
            axes[2 * (j // ncol) + rr, j % ncol].set_visible(False)
    cat_ticks(axes, ns, rotation=0)
    for ax in axes[:, 1:].ravel():
        ax.tick_params(labelleft=False) if False else None
    for r in range(nr):
        axes[2 * r, 0].set_ylabel("coverage")
        axes[2 * r + 1, 0].set_ylabel("width / M3")
        for c in range(ncol):
            if axes[2 * r + 1, c].get_visible():
                axes[2 * r + 1, c].tick_params(labelbottom=(r == nr - 1 or not axes[2 * (r + 1), c].get_visible()))
    for c in range(ncol):
        vis = [k for k in range(2 * nr) if axes[k, c].get_visible()]
        axes[vis[-1], c].set_xlabel("labeled $n$ ($N=20n$)")
        axes[vis[-1], c].tick_params(labelbottom=True)
    seen = {}
    for ax in (axes[0, 0], axes[1, 0]):
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(ll, hh)
    if floor:
        seen[FLOOR_L] = FLOOR_H
    rows = int(np.ceil(len(seen) / 3))
    bottom = (0.19 * rows + 0.12) / fig.get_size_inches()[1]      # legend height in inches -> figure fraction
    fig.tight_layout(rect=(0, bottom, 1, 1), h_pad=0.5, w_pad=0.4)
    fig.legend(list(seen.values()), list(seen), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0),
               columnspacing=1.0, handletextpad=0.4)
    save(fig, name)
    plt.close(fig)


prim = summary("real_primary")
prim = prim[prim["N"] == 20 * prim["n"]]
P = [d for d in PRIMARY if d in set(prim["dataset"])]
fig_grid(prim, P, ["classical", "ppi", M3, M4], ["ppi", M4], "real_main", ph=0.66)
fig_grid(prim, P, [M3, "ppipp_jk", M4, M4 + "_t"], ["ppipp_jk", M4, M4 + "_t"], "real_correction", wlim=(0.85, 1.6))

app = summary("real_appendix")
app = app[app["N"] == 20 * app["n"]]
A = [d for d in ORDER if d in set(app["dataset"])]
fig_grid(app, A, ["classical", "ppi", M3, M4, M4 + "_t", "ppipp_jk"], ["ppi", M4, "ppipp_jk", M4 + "_t"], "real_appendix", ncol=2,
         wlim=(0.85, 1.6))

# n/N sweep: x = N (categorical), one column per dataset, rows = (n = 100 cov, width, n = 400 cov, width)
ns_ = summary("real_nsweep")
D4 = [d for d in ("galaxies", "forest", "gene_expression", "census_income") if d in set(ns_["dataset"])]
fig, axes = plt.subplots(4, len(D4), figsize=(TEXT_W, 4.4), sharex=True, squeeze=False)
labs = ["$N=n$", "$5n$", "$20n$", "20000"]
for j, ds in enumerate(D4):
    for r, n in enumerate((100, 400)):
        d = ns_[(ns_["dataset"] == ds) & (ns_["n"] == n)].copy()
        d["xi"] = d["N"].map({n: 0, 5 * n: 1, 20 * n: 2, 20000: 3})
        cov_panel(axes[2 * r, j], d, [M3, "ppi", M4], xcol="xi", log=False, jitter=0.06)
        wid_panel(axes[2 * r + 1, j], d, ["ppi", M4], xcol="xi", log=False, jitter=0.06, ylim=(0.9, 1.3))
        axes[2 * r, j].set_ylim(0.8, 1.0)
        if j == 0:
            axes[2 * r, 0].set_ylabel(f"coverage, $n={n}$")
            axes[2 * r + 1, 0].set_ylabel(f"width / M3, $n={n}$")
    axes[0, j].set_title(DATASET_LABEL[ds], pad=2)
    axes[3, j].set_xlabel("unlabeled $N$")
cat_ticks(axes, [0, 1, 2, 3], rotation=0, labels=labs)
for ax in axes.ravel():
    ax.set_xlim(-0.4, 3.4)
fig.tight_layout(rect=(0, 0.05, 1, 1), h_pad=0.4, w_pad=0.3)
seen = {}
for ax in (axes[0, 0], axes[1, 0]):
    for hh, ll in zip(*ax.get_legend_handles_labels()):
        seen.setdefault(ll, hh)
fig.legend(list(seen.values()), list(seen), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01))
save(fig, "real_nsweep")
plt.close(fig)
