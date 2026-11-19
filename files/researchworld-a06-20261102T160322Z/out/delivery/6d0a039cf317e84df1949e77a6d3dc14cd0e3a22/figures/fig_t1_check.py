"""Appendix figure (Q1a/Q1b): how well do the closed form and the synthetic world predict the real-matrix optimism?
(a) T1 exhaustive-search gap vs the closed form fed with the matrix's own sigma, r, tau (`gap_theory_from_matrix`), all main cells (K=2..300, n=50..500);
(b) T1 gap vs the T0 synthetic cells with the same (n, K) at tau=0.1, rho=0.6, base accuracy 0.3 (T0 not calibrated to the matrix).
Axes in points; bars 1.96 x delete-a-block SE (T1) and 1.96 x mcse (T0); dashed y=x. Reads results/summary_gap_t1.csv, t0_vs_t1_gap.csv. Writes figures/fig_t1_check.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
s = pd.read_csv(common.path("summary_gap_t1.csv"))
s = s[(s.procedure == "exhaustive") & ~s.cell_id.str.contains("|m3", regex=False)]
t = pd.read_csv(common.path("t0_vs_t1_gap.csv"))
t = t[(t.t0_tau == 0.1) & (t.t0_rho == 0.6)]
fig, axs = plt.subplots(1, 2, figsize=(style.TEXT_WIDTH_IN, 2.5))
ns = sorted(s.n.unique()); cm = dict(zip(ns, plt.cm.viridis(np.linspace(0.05, 0.9, len(ns)))))
ax = axs[0]
for n, d in s.groupby("n"):
    ax.errorbar(100 * d.gap_theory_from_matrix, 100 * d.gap_mean, yerr=196 * d.gap_block_se, fmt="o", ms=3, lw=0.8, color=cm[n], capsize=1, label=f"n={n}")
ax.set_xlabel("closed form from the matrix (points)"); ax.set_ylabel("observed T1 gap (points)"); ax.set_title("(a) closed form", fontsize=8)
ax = axs[1]
for n, d in t.groupby("n"):
    ax.errorbar(100 * d.t1_gap_mean, 100 * d.t0_gap_mean, xerr=196 * d.t1_gap_block_se, yerr=196 * d.t0_gap_mcse, fmt="o", ms=3, lw=0.8, color=cm[n], capsize=1)
ax.set_xlabel("observed T1 gap (points)"); ax.set_ylabel("T0 gap, $\\tau$=0.1, $\\rho$=0.6 (points)"); ax.set_title("(b) synthetic world", fontsize=8)
for ax in axs:
    lim = max(ax.get_xlim()[1], ax.get_ylim()[1]); ax.plot([0, lim], [0, lim], "--", color="0.5", lw=0.7); ax.set_xlim(-0.3, lim); ax.set_ylim(-0.3, lim)
axs[0].legend(frameon=False, loc="upper left", fontsize=6.5)
fig.tight_layout(pad=0.4)
fig.savefig(f"{common.OUT}/fig_t1_check.pdf")
x = s.gap_mean * 100 - 100 * s.gap_theory_from_matrix
print("closed form vs observed: mean diff %.2f pts, max |diff| %.2f pts, cells %d; T0-T1 mean diff %.2f pts" % (x.mean(), x.abs().max(), len(x), (100 * (t.t0_gap_mean - t.t1_gap_mean)).mean()))
