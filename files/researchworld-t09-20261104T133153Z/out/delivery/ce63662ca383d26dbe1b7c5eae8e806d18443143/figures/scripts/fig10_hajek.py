"""Fig 10 (claim C2, C6; hypothesis H6, e12 post-freeze): bias of exposure-mapping (Hajek) estimators at low mean degree, relative to the
true GATE, by interference mechanism and design. One marker per graph (ER, WS, BA at mean degree 4 and 8, n=3000). Filled: the estimator's
exposure mapping is correct for the mechanism (HajekFull for the step mechanisms with kappa=1 and .75; HajekKappa(.75) for step kappa=.75);
open: mapping wrong. Cells with fewer than 100 estimable replicates (of 400) are not drawn; Hájek on Bernoulli(0.8) rests on 200-400 replicates
because control-exposed units are rare (wide bars). Bars +-1.96 MC SE (mostly smaller than the marker)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from common import *

EST = ["DM", "HajekFull", "HajekKappa", "OLS_f", "ORACLE_D"]
MECH = [("step_k1.0", "step\n$\\kappa$=1"), ("step_k0.75", "step\n$\\kappa$=.75"), ("shape_linear", "linear"), ("shape_sigmoid", "sigmoid"),
        ("twohop", "2-hop"), ("prop", "propag.\n$\\rho$=.6")]
CORRECT = {("HajekFull", "step_k1.0"), ("HajekFull", "step_k0.75"), ("HajekKappa", "step_k0.75")}
LC = dict(ECOL, HajekFull="#D55E00", HajekKappa="#CC79A7")  # the two Hájek variants need distinct colours here
GM = {"er": "s", "ws": "^", "ba": "D"}


def main():
    style()
    t = pd.read_csv(os.path.join(RES, "..", "tables", "t15_hajek.csv"))
    t["fam"] = t.tag.str[:2]; t["rel"] = t.bias / t.gate.abs(); t["rel_se"] = t.bias_se / t.gate.abs()
    fig, axs = plt.subplots(1, 3, figsize=(TEXTW, 2.5), sharey=True)
    for ax, (des, title) in zip(axs, [("bern:0.5", "Bernoulli(0.5)"), ("louv:1.0,0.5", "Louvain clusters"), ("bern:0.8", "Bernoulli(0.8)")]):
        for k, (m, _) in enumerate(MECH):
            for e_i, e in enumerate(EST):
                s = t[(t.design == des) & (t.mech == m) & (t.est_name == e) & (t.n_rep >= 100)]
                if s.empty:
                    continue
                x = k + (e_i - 2) * 0.14 + (s.tag.map({"er4": -1, "er8": -.5, "ws4": -.25, "ws8": 0, "ba2": .25, "ba4": .5}).values) * 0.02
                filled = (e, m) in CORRECT or e in ("ORACLE_D",) or (e == "OLS_f" and m == "shape_linear")
                for xi, r, se, f in zip(x, s.rel, s.rel_se, s.fam):
                    ax.errorbar([xi], [r], yerr=[1.96 * se], ls="none", marker=GM[f], ms=2.8, elinewidth=0.4,
                                color=LC[e], mfc=LC[e] if filled else "white", mew=0.6)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xticks(range(len(MECH))); ax.set_xticklabels([l for _, l in MECH], fontsize=5.5)
        ax.set_title(title)
        ax.set_xlim(-0.6, len(MECH) - 0.4)
    axs[0].set_ylabel("bias / GATE")
    h = [Line2D([], [], color=LC[e], marker="o", ls="none", ms=3.5, label=ELAB[e]) for e in EST]
    h += [Line2D([], [], color="gray", marker=m, ls="none", mfc="white", ms=3.5, label={"er": "ER", "ws": "WS", "ba": "BA"}[f]) for f, m in GM.items()]
    h += [Line2D([], [], color="gray", marker="o", ls="none", mfc="gray", ms=3.5, label="mapping/model correct"), Line2D([], [], color="gray", marker="o", ls="none", mfc="white", ms=3.5, label="wrong or misspecified")]
    fig.tight_layout(w_pad=0.5)
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=5, fontsize=6, columnspacing=0.8)
    save(fig, "fig10_hajek")


if __name__ == "__main__":
    main()
