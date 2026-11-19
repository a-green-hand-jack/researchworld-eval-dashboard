"""F6 (claim E4, controls): do synthetic data and N-matched subsamples reproduce the budgets?

Reads controls.csv (one row per control run x claim; `synthetic` flag, `kind` real/sub/arena6/syn, 10-20 runs per control) and
adv_budgets.csv. Only adjacent-pair claims (C2) with a verified budget and no exact tie are used, as in F3/F4.
Left: median budget as a share of N of synthetic data (BT model fitted to the real data, real pair counts; y, per-run medians as
bars min-max) against the real data (x); the NBA seasons shown are the seven synthetic seasons. Right: median budget share of N
against the number of comparisons N for random subsamples of each real data set (line, bars = min-max of the per-run medians),
the real data set at its full N (large marker) and Arena restricted to the six MT-Bench models (open triangles). Writes fig6_controls.pdf.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import common as C

A = C.args(__doc__)
C.set_style()
c = C.read(A.results, "controls.csv")
c = c[(c.claim_type == "C2") & (c["mode"] == "remove") & c.budget.notna() & (c.budget > 0)].copy()
c["frac"] = c.budget / c.N
real = C.adv_c2(A.results)


def per_run(d):
    g = d.groupby("unit").frac.median()
    return g.median(), g.min(), g.max()


fig, (a, b) = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.3))
# (a) synthetic vs real
pts = []
for base, lab in [("arena55k", "Arena"), ("mt_human", "MT human"), ("mt_gpt4", "MT GPT-4"), ("nba_all", "NBA all")]:
    d = c[(c.kind == "syn") & (c.base == base)]
    pts.append((lab, (real[real.dataset == base].budget / real[real.dataset == base].N).median(), per_run(d), C.design_of(base)))
for s in sorted(c[(c.kind == "syn") & c.base.str.startswith("nba19") | (c.kind == "syn") & c.base.str.startswith("nba20")].base.unique()):
    r = real[real.dataset == s]
    pts.append((s[3:], (r.budget / r.N).median(), per_run(c[(c.kind == "syn") & (c.base == s)]), "sports"))
for lab, x, (m, lo, hi), des in pts:
    big = lab in ("Arena", "MT human", "MT GPT-4", "NBA all")
    a.errorbar([x], [m], yerr=[[m - lo], [hi - m]], fmt=C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=4.8 if big else 3.5,
               elinewidth=0.6, mec="white" if big else C.DESIGN_COLOR[des], mew=0.4, fillstyle="full" if big else "none")
    if big:
        a.annotate(lab, (x, m), xytext={"MT GPT-4": (-30, 5), "Arena": (3, 7), "NBA all": (4, -10)}.get(lab, (4, -9)), textcoords="offset points", fontsize=6)
lim = [3e-5, 0.1]
a.plot(lim, lim, "-", color=C.MUTED, lw=0.7, zorder=0)
a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(lim); a.set_ylim(lim)
a.set_xlabel("real data: median budget / $N$"); a.set_ylabel("synthetic data: median budget / $N$")
a.set_title("synthetic control", loc="left", fontsize=8)
a.plot([], [], C.DESIGN_MARKER["sports"], color=C.DESIGN_COLOR["sports"], fillstyle="none", ms=3.5, label="synthetic NBA seasons")
a.legend(loc="upper left", frameon=False, fontsize=6, handletextpad=0.2)
# (b) N-matched
for base in ["arena55k", "mt_human", "nba_all"]:
    des = C.design_of(base)
    d = c[(c.kind == "sub") & (c.base == base)]
    xs, ms, los, his = [], [], [], []
    for n in sorted(d.N_target.unique()):
        m, lo, hi = per_run(d[d.N_target == n]); xs.append(n); ms.append(m); los.append(lo); his.append(hi)
    r = real[real.dataset == base]
    xs.append(r.N.iloc[0]); ms.append((r.budget / r.N).median()); los.append(ms[-1]); his.append(ms[-1])
    xs, ms, los, his = map(np.array, (xs, ms, los, his))
    b.errorbar(xs, ms, yerr=[ms - los, his - ms], fmt="-" + C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=3.5, lw=0.9, elinewidth=0.6,
               mec="white", mew=0.3, label=C.SHORT_LABEL[base])
    b.plot(xs[-1], ms[-1], C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=7, mec=C.INK, mew=0.8)
d = c[(c.kind == "arena6") & (c.N_target < 1000)]  # the one-run N=1367 case is replaced by the 40-draw summary below
xs = sorted(d.N_target.unique()); st = [per_run(d[d.N_target == n]) for n in xs]
b.errorbar(xs, [s[0] for s in st], yerr=[[s[0] - s[1] for s in st], [s[2] - s[0] for s in st]], fmt="^", color=C.DESIGN_COLOR["crowd"],
           fillstyle="none", ms=4.5, mew=0.9, elinewidth=0.6, label="Arena, six MT-Bench models")
# 40 independent draws at N=1367: Arena restricted to the six MT-Bench models vs MT-Bench human, median share and 95% interval
cs = C.read(A.results, "s5_control_summary.csv", secondary=True)
cs = cs[cs.statistic == "median of 5 adjacent-pair claims"].set_index("side")
for side, des, mk, dx in [("arena6", "crowd", "^", 0.94), ("mt_human", "expert", "s", 1.06)]:
    r = cs.loc[side]
    b.errorbar([r.N * dx], [r.median_share], yerr=[[r.median_share - r.lo95], [r.hi95 - r.median_share]], fmt=mk, color=C.DESIGN_COLOR[des],
               fillstyle="none", ms=4.5, mew=0.9, elinewidth=0.9, capsize=1.5)
b.set_xscale("log"); b.set_yscale("log"); b.set_xlabel("comparisons $N$ (outlined: full data)")
b.set_ylabel("median budget / $N$"); b.set_title("size-matched control", loc="left", fontsize=8)
b.legend(loc="center left", bbox_to_anchor=(0.0, 0.62), frameon=False, fontsize=6, handletextpad=0.2, borderaxespad=0.1)
C.panel_letter(a, "a"); C.panel_letter(b, "b")
fig.subplots_adjust(left=0.1, right=0.985, bottom=0.2, top=0.88, wspace=0.34)
fig.savefig(os.path.join(A.out, "fig6_controls.pdf"))
C.record_inputs(A.out, "fig6_controls.pdf", [os.path.join(A.results, f) for f in ["controls.csv", "adv_budgets.csv", "s5_control_summary.csv"]])
