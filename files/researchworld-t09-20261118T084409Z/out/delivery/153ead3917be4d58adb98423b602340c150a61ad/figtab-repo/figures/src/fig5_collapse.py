"""Fig. 5 (C4): the error is a function of the corner distances built from the harmonic-mean degree; evaluated out of sample.
(a) sd(tau_hat) sqrt(n)/sigma vs Z0+Z1 = 1/s, no fitted parameter, correct linear response; degree summary = harmonic vs arithmetic mean
    [results/summary/e4.csv, REG-L rows]
(b) leave-one-family-out prediction of the normalised bias from (Z1, Z0) vs measured  [results/summary/c4_bias_pred.csv, written by analyze_c4.py]
(c) held-out R^2 by predictor                                                        [results/summary/c4_bias_loo.csv]"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SUMM = os.path.join(ROOT, "results", "summary")
OUT = os.path.join(ROOT, "figures", "fig5_collapse.pdf")
e4 = pd.read_csv(os.path.join(SUMM, "e4.csv")); e4 = e4[e4.est == "REG-L"].copy()
loo = pd.read_csv(os.path.join(SUMM, "c4_bias_loo.csv"))
pred = pd.read_csv(os.environ.get("C4_PRED", os.path.join(SUMM, "c4_bias_pred.csv")))
e4["fam"] = e4["graph.kind"].map(S.FAMILY_KEYS)
e4["sig_tot"] = np.sqrt(e4["out.sigma"].fillna(0) ** 2 + e4["out.sigma_alpha"].fillna(0) ** 2)
lin = e4[e4["out.kappa"] == 0].copy()
lin["y"] = lin.sd * np.sqrt(lin.n_eff) / lin.sig_tot
FAMS = list(S.FAMILY_COLORS)

S.apply()
fig, axs = S.fig("text", aspect=0.36, ncols=3, gridspec_kw={"width_ratios": [1, 1, 0.85]})
import matplotlib.pyplot as plt

# (a) variance identity
ax = axs[0]
lim = (2.5, 80)
ax.plot(lim, lim, color="0.4", lw=0.7, zorder=0)
for col, filled in [("d_mean", False), ("d_hm", True)]:
    s = np.sqrt(lin["design.p"] * (1 - lin["design.p"]) / lin[col]); x = 1 / s
    for f in FAMS:
        m = lin.fam == f
        kw = dict(mfc=S.FAMILY_COLORS[f], mec=S.FAMILY_COLORS[f]) if filled else dict(mfc="none", mec="0.55")
        ax.plot(x[m], lin.y[m], ls="none", marker=S.FAMILY_MARKERS[f], ms=2.6 if filled else 2.8, mew=0.5, alpha=0.9 if filled else 0.8,
                zorder=3 if filled else 2, **kw)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim); ax.set_box_aspect(1)
ticks = [3, 5, 10, 20, 40, 80]; ax.set_xticks(ticks); ax.set_xticklabels(map(str, ticks)); ax.set_yticks(ticks); ax.set_yticklabels(map(str, ticks))
ax.minorticks_off()
ax.set_xlabel("$Z_0+Z_1=\\sqrt{d/(p(1-p))}$"); ax.set_ylabel("$\\mathrm{sd}(\\hat\\tau)\\sqrt{n}\\,/\\,\\sigma$")
ax.set_title("(a) variance", fontsize=8)
ax.legend([plt.Line2D([], [], ls="none", marker="o", mfc="0.3", mec="0.3", ms=3), plt.Line2D([], [], ls="none", marker="o", mfc="none", mec="0.55", ms=3)],
          ["harmonic $d$", "mean $d$"], loc="upper left", handletextpad=0.1, borderaxespad=0.1, labelspacing=0.2)

# (b) bias, held-out prediction
ax = axs[1]
pp = pred[pred.predictor == "Z:harmonic"].copy()
pp["fam"] = pp["graph.kind"].map(S.FAMILY_KEYS)
lo, hi = -0.02, 0.62
ax.plot([lo, hi], [lo, hi], color="0.4", lw=0.7, zorder=0)
for resp, filled in [("thresh", True), ("concave", False)]:
    for f in FAMS:
        m = pp[(pp.resp == resp) & (pp.fam == f)]
        mk = S.FAMILY_MARKERS[f]; c = S.FAMILY_COLORS[f]
        ax.errorbar(m.pred.abs() * np.sign(m.pred), m.bias_norm.abs() * 0 + m.bias_norm, yerr=1.96 * m.bias_norm_se, fmt=mk, ms=2.6,
                    mfc=c if filled else "none", mec=c, ecolor=c, elinewidth=0.4, mew=0.5, alpha=0.9)
ax.set_box_aspect(1)
ax.set_xlabel("predicted (family held out)"); ax.set_ylabel("measured bias / scale")
ax.set_title("(b) bias, out of sample", fontsize=8)

# (c) held-out R^2 by predictor
ax = axs[2]
PRED = [("Z:harmonic", "$Z_1,Z_0$ (hm)"), ("dhm,p", "$d_{hm},p$"), ("Z:mean", "$Z_1,Z_0$ (mean)"),
        ("Z1:harmonic", "$Z_1$ only"), ("Z0:harmonic", "$Z_0$ only")]
for j, (resp, mk, c, lab) in enumerate([("thresh", "o", "#D55E00", "threshold"), ("concave", "s", "#0072B2", "concave")]):
    r = loo[loo.resp == resp].set_index("predictor")
    ys = np.arange(len(PRED))[::-1] + (0.12 if j == 0 else -0.12)
    ax.plot([r.loc[k, "r2_heldout"] for k, _ in PRED], ys, ls="none", marker=mk, ms=4, color=c, label=lab)
ax.set_yticks(np.arange(len(PRED))[::-1]); ax.set_yticklabels([l for _, l in PRED])
ax.set_xlim(-0.05, 1.02); ax.axvline(0, color="0.7", lw=0.5, zorder=0)
ax.set_xlabel("held-out $R^2$"); ax.set_title("(c) out-of-sample fit", fontsize=8)
ax.set_box_aspect(1)
ax.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.1, labelspacing=0.2)

h = [plt.Line2D([], [], ls="none", marker=S.FAMILY_MARKERS[f], mfc=S.FAMILY_COLORS[f], mec=S.FAMILY_COLORS[f], ms=3.5) for f in FAMS]
fig.legend(h, FAMS, loc="outside lower center", ncols=6, fontsize=8, handletextpad=0.2, columnspacing=1.0)
S.save(fig, OUT)
