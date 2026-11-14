"""E5: reliability of reporting methods in the synthetic interaction grid: bias of the report (pp), coverage of the nominal 95% interval for
the true score of the selected config, and mean interval width (pp), vs K.  Input: results/synth_plan_summary.csv (f_kind == 'inter').
Bias bars = 1.96*bias_se (y axis clipped at -4 pp; the conditional method lies below it and its range is printed in the panel); width on a log axis; coverage bars = 1.96*cover_se; grey band = binomial 95% MC band around 0.95 for `reps`.
simul reports the naive point value, so its bias is not drawn.  Usage: e5_reliability.py [rho] [n] [proc]"""
import sys
import matplotlib.ticker
from style import *
METHODS = ["naive", "split", "crossfit", "boot_opt", "boot_oob", "simul", "cond"]

def main(rho=0.5, n=200, proc="argmax"):
    setup(); d = load_plan()
    d = d[(d.f_kind == "inter") & (d.f_proc == proc) & (d.f_rho == rho) & (d.f_n == n) & (d.f_K > 1)]
    taus = sorted(d.f_tau.unique())
    fig, axs = plt.subplots(3, len(taus), figsize=(W, 5.0), sharex=True, sharey="row")
    for j, t in enumerate(taus):
        dt = d[d.f_tau == t]
        lo, hi = binom_band(0.95, int(dt.reps.min()))
        axs[1, j].axhspan(lo, hi, color="0.88", lw=0); axs[1, j].axhline(0.95, color="0.4", lw=0.6); axs[0, j].axhline(0, color="0.4", lw=0.6)
        for e in METHODS:
            g = dt[dt.est_name == e].sort_values("f_K")
            if g.empty: continue
            c, m, ls = EST_STYLE[e]; kw = dict(color=c, marker=m, ls=ls, capsize=1.5, elinewidth=0.7)
            if e != "simul": axs[0, j].errorbar(g.f_K, 100 * g.bias, yerr=100 * 1.96 * g.bias_se, label=EST_LABEL[e], **kw)
            axs[1, j].errorbar(g.f_K, g.cover, yerr=1.96 * g.cover_se, label=EST_LABEL[e], **kw)
            axs[2, j].plot(g.f_K, 100 * g.width, color=c, marker=m, ls=ls, label=EST_LABEL[e])
        c = dt[dt.est_name == "cond"]
        if not c.empty:  # conditional method is far off the bias scale: say so instead of hiding it
            axs[0, j].text(0.03, 0.05, "conditional (below axis):\n%.0f to %.0f pp" % (100 * c.bias.max(), 100 * c.bias.min()), transform=axs[0, j].transAxes, fontsize=6.5, va="bottom")
        axs[0, j].set_title(tau_title(t)); axs[2, j].set_xlabel("candidates searched, K")
        axs[2, j].set_xscale("log", base=2); axs[2, j].set_xticks([4, 16, 64]); axs[2, j].set_xticklabels(["4", "16", "64"])
    axs[0, 0].set_ylim(-4, 8); axs[2, 0].set_yscale("log"); axs[2, 0].set_yticks([10, 20, 40, 80]); axs[2, 0].set_yticklabels(["10", "20", "40", "80"]); axs[2, 0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs[0, 0].set_ylabel("bias of report (pp)"); axs[1, 0].set_ylabel("coverage of 95% interval"); axs[2, 0].set_ylabel("mean interval width (pp)")
    h, l = axs[1, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.02), columnspacing=1.2)
    save(fig, f"e5_reliability_{proc}_rho{rho:g}_n{n}.pdf")

if __name__ == "__main__":
    a = sys.argv[1:]
    main(float(a[0]) if a else 0.5, int(a[1]) if len(a) > 1 else 200, a[2] if len(a) > 2 else "argmax")
