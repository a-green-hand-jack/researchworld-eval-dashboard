"""E4a: decision impact for one tuned system. False-claim rate = P(method licenses 'tuned beats the untuned baseline (config 0)'
(one-sided, 5% level) | the selected config is truly not better than the baseline), vs K.
Input: results/synth_plan_summary.csv (f_kind == 'inter', columns fp_rate, n_nonpos = replications in the denominator).
Error bars 1.96*sqrt(p(1-p)/n_nonpos); grey band = binomial 95% band around the nominal 0.05 for the smallest denominator in the panel.
Usage: e4_false_claims.py [rho] [n] [proc]"""
import sys
from style import *
METHODS = ["naive", "split", "crossfit", "boot_oob", "simul", "cond"]

def main(rho=0.5, n=200, proc="argmax"):
    setup(); d = load_plan()
    d = d[(d.f_kind == "inter") & (d.f_proc == proc) & (d.f_rho == rho) & (d.f_n == n) & (d.f_K > 1)]
    taus = sorted(d.f_tau.unique())
    fig, axs = plt.subplots(1, len(taus), figsize=(W, 2.0), sharey=True)
    for ax, t in zip(axs, taus):
        dt = d[d.f_tau == t]
        lo, hi = binom_band(0.05, dt.n_nonpos.min())
        ax.axhspan(max(lo, 0), hi, color="0.88", lw=0); ax.axhline(0.05, color="0.4", lw=0.6)
        for e in METHODS:
            g = dt[dt.est_name == e].sort_values("f_K")
            if g.empty: continue
            p = g.fp_rate; se = np.sqrt(p * (1 - p) / g.n_nonpos); c, m, ls = EST_STYLE[e]
            ax.errorbar(g.f_K, p, yerr=1.96 * se, color=c, marker=m, ls=ls, capsize=1.5, elinewidth=0.7, label=EST_LABEL[e])
        ax.set_xscale("log", base=2); ax.set_xticks([4, 16, 64]); ax.set_xticklabels(["4", "16", "64"])
        ax.set_title(tau_title(t)); ax.set_xlabel("candidates searched, K")
    axs[0].set_ylabel("false-claim rate"); axs[0].set_ylim(bottom=0)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.02), columnspacing=1.2)
    save(fig, f"e4_false_claims_{proc}_rho{rho:g}_n{n}.pdf")

if __name__ == "__main__":
    a = sys.argv[1:]
    main(float(a[0]) if a else 0.5, int(a[1]) if len(a) > 1 else 200, a[2] if len(a) > 2 else "argmax")
