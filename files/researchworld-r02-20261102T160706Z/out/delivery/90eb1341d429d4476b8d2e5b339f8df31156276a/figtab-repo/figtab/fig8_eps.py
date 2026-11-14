"""Fig 8 (claim C5, E1 sensitivity): effect of the Aitchison zero-replacement eps on region mass and worst-slab coverage, D=5, het., linear predictor, n_cal=500, 100 replicates.
eps in {1e-4,1e-3,1e-2,1e-1}; eps=1e-3 is the main grid file, the others are `sens_eps<eps>_<family>.csv`.  Marginal coverage is reported in the caption (all within the table check below).
Reference lines: plain L2 and locally normalised L2 (independent of eps).  Error bars: 95% t-CI over replicates.
"""
import glob
import matplotlib.pyplot as plt
from common import *

style()
fams = ["dirichlet", "multinomial", "rounded"]
rows = []
for fam in fams:
    for f in [f"{EXP}/results/e1/main_{fam}_D5_h1_linear.csv"] + sorted(glob.glob(f"{EXP}/results/e1/sens_eps*_{fam}.csv")):
        x = pd.read_csv(f)
        rows.append(x[x.method.isin(["l2", "l2_n", "ait", "ait_n", "ait_m"])].assign(fam=fam))
d = pd.concat(rows)
d["score"] = d.method.str.split("_").str[0]
d["variant"] = d.method.str.split("_").str[1].fillna("plain")
print("marginal coverage range (means over reps) of l2/ait variants:", d.groupby(["fam", "eps", "method"]).cov10.mean().agg(["min", "max"]).round(3).tolist())
fig, ax = plt.subplots(2, 3, figsize=(TEXT_W, 3.1), sharex=True, sharey="row")
for j, fam in enumerate(fams):
    for i, (col, lab) in enumerate([("pool_frac", "region mass"), ("wsc", "worst-slab coverage")]):
        a = ax[i, j]
        g = d[d.fam == fam]
        for m, ls in (("l2", "-"), ("l2_n", "--")):
            a.axhline(g[g.method == m][col].mean(), color=SCORE_COL["l2"], lw=0.8, ls=ls, label={"l2": r"plain $L_2$", "l2_n": r"normalised $L_2$"}[m])
        for v in ("plain", "n", "m"):
            m = "ait" if v == "plain" else f"ait_{v}"
            A = agg(g[g.method == m], col, by=("eps",))
            a.errorbar(A.eps, A["mean"], yerr=[A["mean"] - A.lo, A.hi - A["mean"]], fmt="-" + VARIANT_MK[v], color=SCORE_COL["ait"], mfc="white" if v == "plain" else SCORE_COL["ait"],
                       ms=3.5, lw=0.7, elinewidth=0.7, capsize=1.5, label="Aitchison, " + VARIANT_LAB[v])
        a.set_xscale("log")
        a.set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
        a.grid(lw=0.3, color="0.88")
        if i == 0:
            a.set_title(fam, fontsize=7)
        if j == 0:
            a.set_ylabel(lab)
        if i == 1:
            a.set_xlabel(r"zero-replacement $\varepsilon$")
h, l = ax[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.27, wspace=0.08)
save(fig, "fig8_eps_sensitivity.pdf")
