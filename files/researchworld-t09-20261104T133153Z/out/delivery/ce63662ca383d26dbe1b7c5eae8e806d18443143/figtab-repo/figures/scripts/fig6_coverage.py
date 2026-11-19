"""Fig 6 (claim C5; hypothesis H7): empirical coverage of nominal 95% intervals (e6, gamma=2). Filled: regression OLS (z,f);
hollow: correctly-specified regression (oracle). x: variance estimator (HC0 = independent units; CL-r = cluster-robust on
Louvain clusters at analysis resolution r, for the cluster design the design clusters; HAC-k = graph-distance-k kernel).
Cluster-robust points whose mean SE is ~0 (a single analysis cluster) are omitted. Bars are +-1.96 binomial SE over replicates. Rows: spillover shape; columns: design."""
import numpy as np
import matplotlib.pyplot as plt
from common import *


def main():
    style()
    e6 = load("e6"); e6["acl"] = pd.to_numeric(e6.tag.str.extract(r"acl([\d.]+)")[0])
    fig, axs = plt.subplots(2, 2, figsize=(TEXTW, 3.5), sharey=True, sharex="col")
    cols = [("bern", "Bernoulli(0.5)", ["HC0", "CL-0.5", "CL-1", "CL-2", "CL-5", "HAC-1", "HAC-2"]),
            ("louv", "Louvain-cluster design", ["HC0", "CL (design)", "HAC-1", "HAC-2"])]
    for i, kind in enumerate(["linear", "concave"]):
        for j, (dk, title, xl) in enumerate(cols):
            ax = axs[i, j]; d = e6[(e6.o_kind == kind) & (e6.dkind == dk)]
            for g in present(GORDER, d.gname):
                for est, filled in [("OLS_f", True), ("ORACLE_D", False)]:
                    s = d[(d.gname == g) & (d.est_name == est)]
                    if s.empty:
                        continue
                    pts = []
                    if dk == "bern":
                        s1 = s[s.acl == 1.0]
                        pts.append((0, s1.cov_hc, s1.n_rep))
                        for k, r in enumerate([0.5, 1.0, 2.0, 5.0]):
                            t = s[(s.acl == r) & (s.mean_se_cl > 1e-6)]; pts.append((1 + k, t.cov_cl, t.n_rep))  # one analysis cluster => SE ~ 0: omitted
                        pts += [(5, s1.cov_hac1, s1.n_rep), (6, s1.cov_hac2, s1.n_rep)]
                    else:
                        pts = [(0, s.cov_hc, s.n_rep), (1, s.cov_cl, s.n_rep), (2, s.cov_hac1, s.n_rep), (3, s.cov_hac2, s.n_rep)]
                    xs = np.array([p[0] for p in pts if len(p[1])]) + {"OLS_f": -0.08, "ORACLE_D": 0.08}[est] + 0.025 * (GORDER.index(g) - 2.5)
                    c = np.array([p[1].iloc[0] for p in pts if len(p[1])]); n = np.array([p[2].iloc[0] for p in pts if len(p[1])])
                    ax.errorbar(xs, c, yerr=1.96 * cov_se(c, n), ls="none", marker=GMARK[g], ms=3.5, color=GCOL[g], elinewidth=0.5,
                                mfc=GCOL[g] if filled else "white", mew=0.8, label=g if (est == "OLS_f" and i == 0 and j == 0) else None)
            ax.axhline(0.95, color="k", lw=0.6, ls="--")
            ax.set_xticks(range(len(xl))); ax.set_xticklabels(xl, rotation=30, ha="right")
            ax.set_ylim(-0.03, 1.03)
            if i == 0:
                ax.set_title(title)
        axs[i, 0].set_ylabel(f"coverage, {kind} spillover")
    axs[0, 0].legend(fontsize=6, ncol=2, loc="lower left")
    fig.tight_layout(w_pad=0.6, h_pad=0.6)
    save(fig, "fig6_coverage")


if __name__ == "__main__":
    main()
