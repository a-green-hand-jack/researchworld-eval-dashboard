"""E5b: coverage and mean width of intervals for the argmax winner's true score: naive, simultaneous bound, conditional, hybrid (AKM-type), vs K.
Input: results/synth_hybrid_summary.csv (M = reps per cell, rho = .5, mean accuracy .3, best-of-K).  Usage: e5b_hybrid.py [n]
Coverage bars 1.96*cover_se; grey band = binomial 95% MC band around 0.95 for the number of repetitions; width in pp, log axis."""
import sys
import matplotlib.ticker
from style import *
METHODS = ["naive", "simul", "cond", "hybrid"]
STY = dict(EST_STYLE, hybrid=(OI[3], "D", (0, (5, 1))))
LAB = dict(EST_LABEL, hybrid="hybrid (conditional + projection)")

def main(n=200):
    setup(); d = pd.read_csv(os.path.join(RESULTS, "synth_hybrid_summary.csv")); d = d[d.n == n]
    taus = sorted(d.tau.unique())
    fig, axs = plt.subplots(2, len(taus), figsize=(W, 3.4), sharex=True, sharey="row")
    for j, t in enumerate(taus):
        dt = d[d.tau == t]; lo, hi = binom_band(0.95, int(dt.reps.min()))
        axs[0, j].axhspan(lo, hi, color="0.88", lw=0); axs[0, j].axhline(0.95, color="0.4", lw=0.6)
        for e in METHODS:
            g = dt[dt.est_name == e].sort_values("K"); c, m, ls = STY[e]
            axs[0, j].errorbar(g.K, g.cover, yerr=1.96 * g.cover_se, color=c, marker=m, ls=ls, capsize=1.5, elinewidth=0.7, label=LAB[e])
            axs[1, j].plot(g.K, 100 * g.width, color=c, marker=m, ls=ls)
        axs[0, j].set_title(tau_title(t)); axs[1, j].set_xlabel("candidates searched, K")
        axs[1, j].set_xscale("log", base=2); axs[1, j].set_xticks([4, 16, 64]); axs[1, j].set_xticklabels(["4", "16", "64"])
    axs[1, 0].set_yscale("log"); axs[1, 0].set_yticks([10, 20, 40, 80]); axs[1, 0].set_yticklabels(["10", "20", "40", "80"])
    axs[1, 0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs[0, 0].set_ylabel("coverage of 95% interval"); axs[1, 0].set_ylabel("mean width (pp)")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.02), columnspacing=1.2)
    save(fig, f"e5b_hybrid_n{n}.pdf")

if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:2]))
