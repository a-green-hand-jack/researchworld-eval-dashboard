"""E4c: ranking five tuned systems on the same tuning items. Design 'unequal_K4_64': systems searched K = 4, 8, 16, 32, 64 configs (best-of-K).
Top row: how often the largest-budget system (K=64) is ranked first by the reported score (coloured, per method) vs how often it is truly best
(black dashed). Bottom row: mean Kendall tau between reported and true ranking of the five systems; bars 1.96*tau_sd/sqrt(reps).
Input: results/synth_ranking_summary.csv, 500 repetitions per point; bars on proportions 1.96*sqrt(p(1-p)/reps).  Usage: e4c_ranking.py"""
import matplotlib.ticker
from style import *
METHODS = ["naive", "split", "boot_opt", "boot_oob"]

def main(design="unequal_K4_64"):
    setup(); d = pd.read_csv(os.path.join(RESULTS, "synth_ranking_summary.csv")); d = d[d.design == design]
    taus = sorted(d.tau_gen.unique())
    fig, axs = plt.subplots(2, len(taus), figsize=(W, 3.4), sharex=True, sharey="row")
    for j, t in enumerate(taus):
        dt = d[d.tau_gen == t]
        tr = dt[dt.est_name == "naive"].sort_values("n")  # the truth does not depend on the method
        axs[0, j].errorbar(tr.n, tr.big_truly_best, yerr=1.96 * np.sqrt(tr.big_truly_best * (1 - tr.big_truly_best) / tr.reps), color="k", ls="--", marker="x", capsize=1.5, elinewidth=0.7, label="truly best")
        for e in METHODS:
            g = dt[dt.est_name == e].sort_values("n"); c, m, ls = EST_STYLE[e]; p = g.big_reported_best
            axs[0, j].errorbar(g.n, p, yerr=1.96 * np.sqrt(p * (1 - p) / g.reps), color=c, marker=m, ls=ls, capsize=1.5, elinewidth=0.7, label=EST_LABEL[e] + ", ranked first")
            axs[1, j].errorbar(g.n, g.tau_mean, yerr=1.96 * g.tau_sd / np.sqrt(g.reps), color=c, marker=m, ls=ls, capsize=1.5, elinewidth=0.7)
        axs[0, j].set_title(tau_title(t)); axs[1, j].set_xlabel("tuning questions, n")
        axs[1, j].set_xscale("log"); axs[1, j].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); axs[1, j].set_xticks([100, 200, 500]); axs[1, j].set_xticklabels(["100", "200", "500"])
    axs[0, 0].set_ylabel("P(K=64 ranked first)"); axs[1, 0].set_ylabel("Kendall tau")
    axs[0, 0].set_ylim(bottom=0); axs[1, 0].axhline(0, color="0.4", lw=0.6)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.02), columnspacing=1.2)
    save(fig, "e4c_ranking.pdf")

if __name__ == "__main__":
    main()
