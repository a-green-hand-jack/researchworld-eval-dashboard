"""Compact paper-width version (7 estimators; Bernoulli 0.5/0.1 and Louvain clusters; propagation rho=0.9): include at \\linewidth.
Fig 7 (claims C3, C6; hypothesis H8): failure map. Relative RMSE (RMSE / |GATE|, colour on log scale, value printed)
of every estimator for each interference mechanism x design, one graph. Top: spillover shape (e2, gamma=2, 1-hop fraction);
bottom: other mechanisms (e7). Cells with no estimate (oracle undefined for equilibrium propagation, Hájek with no unit in the
full-neighbourhood exposure) are hatched. Usage: fig7_failure_map.py <graph> [relrmse|biasshare]"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from common import *

EST = ["DM", "HajekKappa", "OLS_f", "OLS_quad", "OLS_big", "GBM", "ORACLE_D"]   # compact: the paper-width layout; the rest is in results/summary/e2.csv, e7.csv
DSHORT = {"bern:0.5": "B.5", "bern:0.1": "B.1", "louv:1.0,0.5": "Lv"}


def matrix(d, cols, metric):
    M = np.full((len(EST), len(cols)), np.nan)
    for j, (sel, _) in enumerate(cols):
        s = d
        for k, v in sel.items():
            s = s[s[k] == v]
        for i, e in enumerate(EST):
            t = s[s.est_name == e]
            if len(t) and t.n_rep.iloc[0] >= 5:
                M[i, j] = t.rel_rmse.iloc[0] if metric == "relrmse" else (t.bias.iloc[0] ** 2 / t.rmse.iloc[0] ** 2)
    return M


def main(g="SBM", metric="relrmse"):
    style()
    e2, e7 = load("e2"), load("e7")
    d2, d7 = e2[e2.gname == g], e7[e7.gname == g]
    c2 = [({"o_kind": k, "design": ds}, f"{DSHORT[ds]}") for k in ["linear", "concave", "convex", "sigmoid"] for ds in DSHORT]
    mechs = [("count", {"o_mech": "count"}), ("2-hop", {"o_mech": "twohop"}), ("hetero", {"o_mech": "hetero"}),
             ("prop .9", {"o_mech": "prop", "o_rho": 0.9})]
    c7 = [({**sel, "design": ds}, DSHORT[ds]) for _, sel in mechs for ds in ["bern:0.5", "louv:1.0,0.5"]]
    norm = LogNorm(0.01, 10) if metric == "relrmse" else Normalize(0, 1)
    cmap = plt.cm.Blues if metric == "relrmse" else plt.cm.Oranges
    fig, axs = plt.subplots(2, 1, figsize=(TEXTW, 3.35), gridspec_kw={"width_ratios": [1], "hspace": 0.55})
    for ax, d, cols, groups, title in [(axs[0], d2, c2, [KLAB[k] + " spillover" for k in ["linear", "concave", "convex", "sigmoid"]], "1-hop spillover shape (e2)"),
                                       (axs[1], d7, c7, [m for m, _ in mechs], "other mechanisms (e7)")]:
        M = matrix(d, cols, metric)
        ax.set_facecolor("white")
        im = ax.imshow(np.ma.masked_invalid(M), cmap=cmap, norm=norm, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                if np.isnan(M[i, j]):
                    ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, hatch="////", edgecolor="#bbbbbb", lw=0))
                else:
                    v = M[i, j]
                    txt = (f"{v:.2g}" if v < 100 else f"{v:.0f}") if metric == "relrmse" else f"{v:.2f}"
                    dark = norm(v) > 0.55
                    ax.text(j, i, txt, ha="center", va="center", fontsize=5.5, color="white" if dark else "black")
        ax.set_yticks(range(len(EST))); ax.set_yticklabels([ELAB[e] for e in EST], fontsize=6.5)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels([c[1] for c in cols], fontsize=5.5)
        k = len(cols) // len(groups)
        for b in range(1, len(groups)):
            ax.axvline(b * k - 0.5, color="white", lw=2)
        for b, gl in enumerate(groups):
            ax.text(b * k + (k - 1) / 2, -0.9, gl, ha="center", va="bottom", fontsize=6.5)
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02)
    cb.set_label("relative RMSE (log)" if metric == "relrmse" else "bias$^2$ / MSE", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    fig.suptitle(f"{g}; B.5/B.1: Bernoulli(0.5/0.1), Lv: Louvain clusters", fontsize=6.5, y=1.0)
    save(fig, f"fig7_failure_map_{metric}_{g.lower().replace('-', '')}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
