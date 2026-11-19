"""Appendix figure (column, C5): what the unreliable instances of the shipped KernelSHAP default are made of. Per main-grid cell group (seeds pooled),
share of the instances with r_3 < 0.9 at x1 whose failure is truncation bias (the default's mean attribution has the wrong top-3, the paired
l1_reg=False mean the right one), other bias (wrong under both), or noise (the default's mean is right and the runs scatter), noise split at
z_true = gap/SD below / at or above 1. Input: results/c5_split_R20.csv (main-grid groups d = dfull; n_unreliable in the labels)."""
import os, json
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import figstyle as fs, common as C

a = C.args(__doc__)
fs.apply("column", 0.74)
path = os.path.join(C.RESULTS, "c5_split_R20.csv")
d = pd.read_csv(path)
d = d[d.group.str.match(r"(german|ACSEmployment)_dfull_(lr|mlp|gbdt)$")].copy()
d["ds"] = d.group.str.split("_").str[0]
d["model"] = d.group.str.split("_").str[-1]
d = d.sort_values(["ds", "model"], key=lambda s: s.map({"german": 0, "ACSEmployment": 1, "lr": 0, "mlp": 1, "gbdt": 2}))
d = d.iloc[::-1].reset_index(drop=True)   # German on top
segs = [("trunc_bias", "#D55E00", "truncation bias"),
        ("other_bias", "#000000", "bias under both"),
        ("noise_gap_lt_sd", "#56B4E9", r"noise, gap $<$ SD"),
        ("noise_gap_ge_sd", "#0072B2", r"noise, gap $\geq$ SD")]
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.43, right=0.97, top=0.98, bottom=0.40)
for i, r in d.iterrows():
    left = 0.0
    for c, colr, _ in segs:
        w = r[c]
        ax.barh(i, w, left=left, color=colr, height=0.62, linewidth=0)
        left += w
    lo, hi = r.trunc_bias_lo, r.trunc_bias_hi          # interval of the first segment
    ax.errorbar(r.trunc_bias, i, xerr=[[r.trunc_bias - lo], [hi - r.trunc_bias]], color="0.15", lw=0.8, capsize=1.5, capthick=0.8, zorder=4)
ax.set_yticks(range(len(d)))
ax.set_yticklabels([f"{C.DATA_LABEL[r.ds]} {C.MODEL_LABEL[r.model]} ($n$={int(r.n_unreliable)})" for _, r in d.iterrows()])
ax.set_xlim(0, 1); ax.set_xlabel("share of the unreliable instances")
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
fig.legend(handles=[Patch(color=c, label=l) for _, c, l in segs], frameon=False, loc="lower center", ncol=2, handlelength=1.2, columnspacing=1.0, labelspacing=0.3)
out = os.path.join(C.outdir(a), "figA_c5_split.pdf")
fig.savefig(out)
j = C.provenance([path]); j["shares"] = d[["group", "n_unreliable"] + [s[0] for s in segs]].round(4).to_dict("records")
json.dump(j, open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
