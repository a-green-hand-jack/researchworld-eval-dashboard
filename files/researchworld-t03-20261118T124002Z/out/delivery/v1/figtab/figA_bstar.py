"""Appendix figure (column, C2): required budget B*(x) per instance, predicted against empirical.
Covert-Lee arm, k=3, delta=0.1 (results/instances_R20.csv): x = c * sigma^2 / gap^2 with c fitted per cell (Bstar_mult_pred), y = the smallest
grid budget (multiple of the shipped default) at which r_3 >= 1-delta (Bstar_mult_emp). Instances not reliable by x16 are censored at
x16 and drawn hollow. Colour = dataset; Spearman rank correlation over uncensored points in the legend (computed here, from the same file)."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import figstyle as fs, common as C

a = C.args(__doc__)
f = os.path.join(C.RESULTS, "instances_R20.csv")
i = pd.read_csv(f)
i = i[(i.arm == "covert_lee") & (i.k == 3) & np.isclose(i.delta, 0.1)]
i = i[i.group.str.contains("_dfull_")]
i["data"] = i.group.str.split("_").str[0]
i = i.assign(y=i.Bstar_mult_emp * np.exp(np.random.default_rng(0).uniform(-0.08, 0.08, len(i))))
fs.apply("column", 0.9)
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.17, right=0.98, bottom=0.17, top=0.98)
col = {"german": "#0072B2", "ACSEmployment": "#D55E00"}
rec = {}
for d, g in i.groupby("data"):
    cens = g.censored.astype(bool)
    rho = spearmanr(g.Bstar_mult_pred[~cens], g.Bstar_mult_emp[~cens])[0]
    rec[d] = {"n": int(len(g)), "n_censored": int(cens.sum()), "spearman_uncensored": float(rho)}
    ax.scatter(g.Bstar_mult_pred[~cens], g.y[~cens], s=4, color=col[d], alpha=0.35, lw=0, label=f"{C.DATA_LABEL[d]} ($\\rho={rho:.2f}$)")
    ax.scatter(g.Bstar_mult_pred[cens], g.y[cens], s=5, facecolors="none", edgecolors=col[d], alpha=0.5, lw=0.4)
lo, hi = 0.03, 512.0   # points outside are counted in the .json and said in the caption
rec_off = int(((i.Bstar_mult_pred < lo) | (i.Bstar_mult_pred > hi)).sum())
lim = [lo, hi]
ax.plot(lim, lim, color="0.4", lw=0.6, ls=":")
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.set_xlim(*lim); ax.set_ylim(0.2, 24)   # the grid is {1/4, 1/2, 1, 2, 4, 16}; empirical values are jittered by +-8% for visibility
tk = [t for t in (0.25, 1, 4, 16, 64, 256) if lo <= t <= hi]; ax.set_xticks(tk); ax.set_xticklabels(["0.25" if t == 0.25 else f"{t:g}" for t in tk]); ax.set_yticks([0.25, 1, 4, 16]); ax.set_yticklabels(["0.25", "1", "4", "16"])
ax.minorticks_off()
ax.set_xlabel("predicted $B^*(x)$ ($\\times$ shipped default)")
ax.set_ylabel("empirical $B^*(x)$")
ax.legend(frameon=False, loc="lower right", handletextpad=0.2, markerscale=2.5)
out = os.path.join(C.outdir(a), "figA_bstar.pdf")
fig.savefig(out)
pv = C.provenance([f]); pv["by_dataset"] = rec; pv["n_points_outside_axes"] = rec_off
json.dump(pv, open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
