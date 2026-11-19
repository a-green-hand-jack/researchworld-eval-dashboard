"""Reporting-method comparison figure: bias / RMSE / coverage vs n for each search algorithm.  Usage: python fig_methods.py synth|real"""
import sys; sys.path.insert(0, "/work/code")
import pandas as pd, numpy as np
from figstyle import *
from summ import summarize
METHODS = [("naive", "naive (status quo)", OI[1], "o"), ("holdout", "hold-out 30%", OI[0], "s"), ("crossfit", "5-fold cross-fit", OI[2], "^"),
           ("boot_opt", "replay-bootstrap", OI[3], "D")]
ALG = [("rs72", "random search B=72"), ("sh72", "succ. halving B=72"), ("ca", "coordinate ascent"), ("mipro40", "surrogate (MIPRO-like) T=40")]

def prep(d):
    d = d.copy()
    d["alg"] = np.where(d.algo == "mipro", "mipro40", np.where(d.algo == "ca", "ca", d.algo + d.kw_B.fillna(0).astype(int).astype(str)))
    return d

def fig(d, fname, title):
    s = summarize(prep(d), ["alg", "n", "method"])
    fig, ax = plt.subplots(3, 4, figsize=(7.0, 4.6), sharex=True)
    for j, (a, an) in enumerate(ALG):
        for m, ml, c, mk in METHODS:
            h = s[(s.alg == a) & (s.method == m)].sort_values("n")
            if len(h) == 0: continue
            ax[0, j].errorbar(h.n, 100 * h.bias, yerr=100 * 1.96 * h.bias_se, color=c, marker=mk, label=ml, capsize=0)
            ax[1, j].plot(h.n, 100 * h.rmse, color=c, marker=mk)
            ax[2, j].errorbar(h.n, h.cover, yerr=1.96 * h.cover_se, color=c, marker=mk, capsize=0)
        ax[0, j].set_title(an); ax[0, j].axhline(0, color="k", lw=0.6)
        ax[2, j].axhline(0.95, color="k", lw=0.6, ls="--"); ax[2, j].set_ylim(0.6, 1.02)
        ax[2, j].set_xscale("log"); ax[2, j].set_xticks([50, 100, 200, 400, 800]); ax[2, j].set_xticklabels(["50", "100", "200", "400", "800"]); ax[2, j].minorticks_off()
        ax[2, j].set_xlabel("n")
    ax[0, 0].set_ylabel("bias: report $-$ truth [pts]"); ax[1, 0].set_ylabel("RMSE [pts]"); ax[2, 0].set_ylabel("95% CI coverage")
    ax[0, 0].legend(frameon=False, fontsize=6)
    if title: fig.suptitle(title, fontsize=8, y=0.995)
    plt.tight_layout(); plt.savefig(fname)

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "synth":
        d = pd.read_parquet("/work/results/synth_main.parquet")
        for tau in (0.0, 0.1):
            fig(d[(d.w_tau == tau) & (d.w_rho == 0.8)], f"/work/paper/figs/fig_methods_synth_tau{int(tau*100):02d}.pdf", f"synthetic world, config spread tau={tau} probit units, rho=0.8")

    if which == "real":
        d = pd.read_parquet("/work/results/real_main.parquet"); d = d[d.method_set == "main"]
        fig(d, "/work/paper/figs/fig_methods_real.pdf", None)
