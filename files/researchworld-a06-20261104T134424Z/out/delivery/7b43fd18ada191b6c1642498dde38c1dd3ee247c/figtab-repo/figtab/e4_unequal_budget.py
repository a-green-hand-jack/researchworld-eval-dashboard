"""E4b: comparing two tuned systems that searched different numbers of configurations (K_A for A, K_B for B).
False-claim rate = P(claim 'A beats B' (one-sided, 5% level) and A is truly not better).  Input: results/synth_compare_summary.csv.
Top: error bars 1.96*sqrt(p(1-p)/reps) (binomial s.e. of the rate). Bottom: bias of the reported difference (reported A-B minus true A-B), bars 1.96*bias_diff_se.  Usage: e4_unequal_budget.py [n]"""
import sys
from style import *
METHODS = ["naive", "boot_opt", "split"]

def main(n=200):
    setup(); d = pd.read_csv(os.path.join(RESULTS, "synth_compare_summary.csv")); d = d[d.n == n]
    pairs = [(16, 16), (16, 4), (64, 4), (64, 1)]; taus = sorted(d.tau.unique())
    fig, axs2 = plt.subplots(2, len(taus), figsize=(W, 3.6), sharex=True, sharey="row"); axs = axs2[0]
    for ax, t in zip(axs, taus):
        for j, e in enumerate(METHODS):
            ys, es = [], []
            for a, b in pairs:
                r = d[(d.tau == t) & (d.KA == a) & (d.KB == b) & (d.est_name == e)].iloc[0]
                ys.append(r.false_claim); es.append(1.96 * np.sqrt(r.false_claim * (1 - r.false_claim) / r.reps))
            x = np.arange(len(pairs)) + (j - 1) * 0.18; c, m, _ = EST_STYLE[e]
            ax.errorbar(x, ys, yerr=es, color=c, marker=m, ls="none", capsize=1.5, elinewidth=0.7, label=EST_LABEL[e])
        ax.axhline(0.05, color="0.4", lw=0.6)
        ax.set_title(tau_title(t))
        bx = axs2[1, list(taus).index(t)]; bx.axhline(0, color="0.4", lw=0.6)
        for j, e in enumerate(METHODS):
            rr = [d[(d.tau == t) & (d.KA == a) & (d.KB == b) & (d.est_name == e)].iloc[0] for a, b in pairs]
            c, m, _ = EST_STYLE[e]
            bx.errorbar(np.arange(len(pairs)) + (j - 1) * 0.18, [100 * r.bias_diff for r in rr], yerr=[196 * r.bias_diff_se for r in rr], color=c, marker=m, ls="none", capsize=1.5, elinewidth=0.7)
        bx.set_xticks(range(len(pairs))); bx.set_xticklabels([f"{a}/{b}" for a, b in pairs]); bx.set_xlabel(r"configs searched, $K_A$/$K_B$")
    axs[0].set_ylabel("false-claim rate, A beats B"); axs[0].set_ylim(bottom=0); axs2[1, 0].set_ylabel("bias of reported A$-$B (pp)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.02), columnspacing=1.2)
    save(fig, f"e4_unequal_budget_n{n}.pdf")

if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:2]))
