"""E1: optimism gap (naive report - true score of the selected config) vs number of candidates K, per tuning-set size n,
with the Gaussian-max prediction (analysis/theory.py) overlaid.  Input: results/synth_theory_prediction.csv
(columns pred_gap, pred_gap_mc_se, emp_gap, emp_gap_mc_se, emp_reps).  rho = 0.5, best-of-K search.
Lines = prediction; markers = empirical mean over emp_reps whole-pipeline repetitions with 1.96 * MC s.e.
(the interaction cells have 500 repetitions, the reference cell 2000)."""
import sys
from style import *

NS = [100, 200, 500, 1000]

def main(rho=0.5):
    setup(); d = pd.read_csv(os.path.join(RESULTS, "synth_theory_prediction.csv"))
    d = d[(d.rho == rho)]
    taus = [t for t in (0.0, 0.01, 0.03) if t in set(d.tau)]
    fig, axs = plt.subplots(1, len(taus), figsize=(W, 2.0), sharey=True)
    for ax, t in zip(axs, taus):
        for i, n in enumerate(NS):
            g = d[(d.tau == t) & (d.n == n)].sort_values("K")
            ax.plot(g.K, 100 * g.pred_gap, color=OI[i], ls="-", lw=1.0, alpha=0.8)
            e = g.dropna(subset=["emp_gap"])
            ax.errorbar(e.K, 100 * e.emp_gap, yerr=100 * 1.96 * e.emp_gap_mc_se, color=OI[i], marker=MARK[i], ls="none", capsize=1.5, elinewidth=0.7, label=f"n = {n}")
        ax.axhline(0, color="0.4", lw=0.6)
        ax.set_xscale("log", base=2); ax.set_xticks([1, 4, 16, 64]); ax.set_xticklabels(["1", "4", "16", "64"])
        ax.set_title(tau_title(t)); ax.set_xlabel("candidates searched, K")
    axs[0].set_ylabel("optimism gap (pp)")
    h, l = axs[0].get_legend_handles_labels()
    h.append(plt.Line2D([], [], color="0.3", ls="-")); l.append("Gaussian-max prediction")
    fig.legend(h, l, loc="upper center", ncol=5, bbox_to_anchor=(0.5, -0.02), columnspacing=1.2, handletextpad=0.4)
    save(fig, f"e1_gap_vs_K_rho{rho:g}.pdf")

if __name__ == "__main__":
    main(*(float(a) for a in sys.argv[1:2]))
