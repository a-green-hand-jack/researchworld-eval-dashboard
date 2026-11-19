"""Fig 3 (figure*, C4): are in-run certificates calibrated, and what do they give up?
(a, b) calibration on fresh reruns, under the stopping rule: x = nominal level 1-delta, y = P(top-k of the delivered run is exact |
certified), pooled over instances and seeds, cluster-bootstrap 95% CI (results/certificate_coverage.csv), k=3 and k=5; colour = rule,
marker = dataset x model. On the diagonal = calibrated, above = conservative, below = over-claims.
(c) power against the oracle: share of runs certified at or before a coalition stage (x0.25, x1, x4 of the Covert-Lee schedule) against the share
of instances an oracle would certify at that stage (r_3(x;B) >= 0.9 from R~200 reruns, 30 stratified instances per s0 cell,
results/oracle_tightness.csv). Mean over the six cells; bars = range over cells. On the diagonal = oracle-tight, below = conservative.
`--appendix` writes figA_calibration_k135.pdf: the calibration panels for k=1, 3, 5."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import figstyle as fs, common as C

RULES = ["naive", "bonf", "maxt", "split", "shapk"]
RULE_LABEL = {"naive": "plug-in SE, no correction", "bonf": "SE + Bonferroni", "maxt": "SE + max-$t$",
              "split": "split-half", "shapk": "SHAP@k-style stopping"}
RULE_COLOR = {"naive": "#D55E00", "bonf": "#0072B2", "maxt": "#56B4E9", "split": "#009E73", "shapk": "#CC79A7"}
a = C.args(__doc__, extra=("--appendix",))
cov = pd.read_csv(os.path.join(C.RESULTS, "certificate_coverage.csv"))
orc = pd.read_csv(os.path.join(C.RESULTS, "oracle_tightness.csv"))
groups = sorted(cov.group.unique())
mk = dict(zip(groups, ["o", "s", "^", "D", "v", "P", "X"]))
glabel = {g: C.DATA_LABEL.get(g.split("_")[0], g.split("_")[0]) + " " + C.MODEL_LABEL.get(g.split("_")[2], g.split("_")[2]) for g in groups}
fs.apply("text", 0.46)
fig, axs = plt.subplots(1, 3, gridspec_kw={"wspace": 0.28})
fig.subplots_adjust(left=0.075, right=0.995, bottom=0.43, top=0.93)
nom = [0.8, 0.9, 0.95, 0.99]
ks = (1, 3, 5) if a.appendix else (3, 5)
for ax, k in zip(axs, ks):
    ax.plot([0.75, 1.0], [0.75, 1.0], color="0.4", lw=0.6, ls=":", zorder=1)
    ax.fill_between([0.75, 1.0], [0.75, 1.0], 0.70, color="0.9", lw=0, zorder=0)
    for ri, r in enumerate(RULES):
        for gi, g in enumerate(groups):
            s = cov[(cov.rule == r) & (cov.group == g) & (cov.k == k)].sort_values("delta", ascending=False)
            if s.empty:
                continue
            x = s.target.values + (ri - 2) * 0.0075 + (gi - 2) * 0.0012
            y = s.correct_given_certified.values
            ax.errorbar(x, y, yerr=[np.clip(y - s.ci_lo.values, 0, None), np.clip(s.ci_hi.values - y, 0, None)], fmt=mk[g], ms=3, color=RULE_COLOR[r],
                        lw=0.6, capsize=0, elinewidth=0.6, mfc=RULE_COLOR[r], zorder=3)
    ax.set_xlim(0.78, 1.0); ax.set_ylim(0.70, 1.02)
    ax.set_xticks(nom); ax.set_xticklabels(["0.80", "0.90", "0.95", "0.99"])
    ax.set_xlabel("nominal level $1-\\delta$")
    ax.text(0.03, 0.03, f"$k={k}$", transform=ax.transAxes, va="bottom", fontsize=fs.MIN_PT)
axs[0].set_ylabel("P(top-$k$ exact | certified)")
axs[0].text(0.985, 0.30, "over-claims", transform=axs[0].transAxes, ha="right", fontsize=fs.MIN_PT, color="0.35")
if not a.appendix:
    # (c) certified share vs the oracle's certifiable share at the same coalition stage (k=3, delta=0.1)
    ax = axs[2]
    o = orc[(orc.k == 3) & np.isclose(orc.delta, 0.1)]
    ax.plot([0, 0.8], [0, 0.8], color="0.4", lw=0.6, ls=":", zorder=1)
    ax.fill_between([0, 0.8], [0, 0.8], 0, color="0.9", lw=0, zorder=0)
    for r in RULES:
        g = o[o.rule == r].groupby("stage").agg(x=("oracle_share", "mean"), y=("cert_share", "mean"), lo=("cert_share", "min"), hi=("cert_share", "max"))
        g = g.loc[[st for st in ("x0.25", "x1", "x4") if st in g.index]]
        if r == "naive":
            for st, lab in (("x0.25", "$\\times0.25$"), ("x1", "$\\times1$"), ("x4", "$\\times4$")):
                if st in g.index:
                    ax.annotate(lab, (g.x[st], g.y[st]), xytext=(6, -3), textcoords="offset points", ha="left", va="center", fontsize=fs.MIN_PT, color=RULE_COLOR[r])
        ax.errorbar(g.x, g.y, yerr=[g.y - g.lo, g.hi - g.y], color=RULE_COLOR[r], marker="o", ms=3, lw=0.9, elinewidth=0.6, capsize=0, zorder=3)
    ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.8); ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8]); ax.set_xticklabels(["0", "0.2", "0.4", "0.6", ""])
    ax.set_xlabel("share an oracle certifies ($r_3\\geq 0.9$)")
    ax.set_ylabel("share certified")
    ax.text(0.97, 0.04, "conservative", transform=ax.transAxes, ha="right", fontsize=fs.MIN_PT, color="0.35")
    ax.text(0.03, 0.96, "$k=3$, $\\delta=0.1$", transform=ax.transAxes, va="top", fontsize=fs.MIN_PT)
for i, l in enumerate("abc"):
    axs[i].text(-0.02 if i else -0.08, 1.04, f"({l})", transform=axs[i].transAxes, fontweight="bold", va="bottom", ha="right")
h1 = [Line2D([], [], color=RULE_COLOR[r], lw=1.5, label=RULE_LABEL[r]) for r in RULES]
h2 = [Line2D([], [], color="0.3", marker=mk[g], ls="", ms=3.5, label=glabel[g]) for g in groups]
fig.legend(handles=h1, loc="lower left", bbox_to_anchor=(0.06, 0.0), ncol=1, frameon=False, handlelength=1.4, labelspacing=0.2, title="rule", title_fontsize=fs.MIN_PT, alignment="left")
fig.legend(handles=h2, loc="lower left", bbox_to_anchor=(0.40, 0.0), ncol=1, frameon=False, handlelength=1.0, labelspacing=0.2, title="dataset, model (a, b)", title_fontsize=fs.MIN_PT, alignment="left")
out = os.path.join(C.outdir(a), "figA_calibration_k135.pdf" if a.appendix else "fig3_certificates.pdf")
fig.savefig(out)
json.dump({"inputs": ["certificate_coverage.csv"] + ([] if a.appendix else ["oracle_tightness.csv"]), "groups": groups, "figtab_commit": C.provenance([])["figtab_commit"]},
          open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
