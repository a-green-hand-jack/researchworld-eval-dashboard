"""Fig 3 (claim C3): marginal validity vs conditional coverage on E1.  Rows: configurations; columns: coverage on predicted-dominant-part strata (lowest/highest
quintile) and boundary / interior y, for plain, locally-normalised and Mondrian variants of each score.  95% CI over replicates.
Usage: python figtab/fig3_cond.py [family D hetero pred ...]  -- configs given as file stems, default: all main_*.csv present (capped at 6).
"""
import sys
import matplotlib.pyplot as plt
from common import *

style()
d = load_e1()
if "ymax_min" in d:
    d["ymax_gap"] = d.ymax_max - d.ymax_min
files = sys.argv[1:] or [f for f in dict.fromkeys(d.file) if "_D5_h1_linear" in f]
files = [f if f.endswith(".csv") else f + ".csv" for f in files]
d = d[d.file.isin(files)]
d = d.assign(_o=d.file.map(files.index)).sort_values("_o", kind="stable")
panels = [("or_gap", "oracle gap"), ("ymax_gap", "top-prob. bin gap"), ("wsc", "worst-slab cov."), ("bnd_cov", "cov. | $y$ near bdry")]
panels = [p for p in panels if p[0] in d.columns and d[p[0]].notna().any()]
scores = ["l2", "hell", "kl", "ait", "nll"]
fig, ax = plt.subplots(d.file.nunique(), len(panels), figsize=(TEXT_W, 1.3 * d.file.nunique() + 0.6), sharex="col", squeeze=False)
null = load_null()
NULL = {"or_gap", "ymax_gap", "wsc"}  # grey band: 5-95% of the metric when conditional coverage is exact (Fig 5), at the config's n_cal
off = {"plain": -0.2, "n": 0.0, "m": 0.2}
for i, (f, g) in enumerate(d.groupby("file", sort=False)):
    for j, (col, ttl) in enumerate(panels):
        a = ax[i, j]
        A = agg(g, col)
        for _, r in A.iterrows():
            if r.score not in scores or r.variant not in off:
                continue
            y = scores.index(r.score) + off[r.variant]
            c = SCORE_COL[r.score]
            a.errorbar(r["mean"], y, xerr=[[r["mean"] - r.lo], [r.hi - r["mean"]]], fmt=VARIANT_MK[r.variant], color=c,
                       mfc="white" if r.variant == "plain" else c, ms=3.2, elinewidth=0.7, capsize=1)
        if col in NULL:
            nn = null[null.n_cal == g.n_cal.iloc[0]][col]
            a.axvspan(nn.quantile(0.05), nn.quantile(0.95), color="0.88", lw=0, zorder=0)
        if col in ("wsc", "bnd_cov"):
            a.axvline(0.9, color="0.3", lw=0.6, ls="--")
        a.set_yticks(range(len(scores)))
        a.set_yticklabels([SCORE_LAB[s] for s in scores] if j == 0 else [])
        a.set_ylim(len(scores) - 0.4, -0.6)
        a.grid(axis="x", lw=0.3, color="0.88")
        if i == 0:
            a.set_title(ttl, fontsize=7)
        if j == 0:
            r = g.iloc[0]; a.set_ylabel(f"{r['family']}\nD={int(r['D'])}, {'het.' if r['hetero'] else 'hom.'}, {r['pred']}", fontsize=6)
        if i == d.file.nunique() - 1:
            a.set_xlabel({"or_gap": r"mean $|c(x)-0.9|$", "ymax_gap": "max $-$ min cov.", "wsc": "coverage", "bnd_cov": "coverage"}[col], fontsize=7)
from matplotlib.lines import Line2D
h = [Line2D([], [], marker=VARIANT_MK[k], ls="", color="0.3", mfc="white" if k == "plain" else "0.3", ms=4, label=VARIANT_LAB[k]) for k in off]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.55 / fig.get_figheight()))
save(fig, "fig3_conditional.pdf")
