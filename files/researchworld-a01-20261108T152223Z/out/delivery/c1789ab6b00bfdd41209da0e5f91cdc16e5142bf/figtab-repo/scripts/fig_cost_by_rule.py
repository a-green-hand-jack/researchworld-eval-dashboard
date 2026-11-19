"""Cost of reaching first place by rule: K (tasks touched) and L1 (score points), distribution across targets, per cap.
Usage: python3 scripts/fig_cost_by_rule.py RESDIR OUT_STEM [--caps ceil,front0,gain20] [--height 4.6]
Input: helm_main.csv. Every target model (79) is one point; feasible cells only are drawn, the feasible count is printed per row."""
import sys, argparse, pathlib
import numpy as np, matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import style, common
ap = argparse.ArgumentParser(); ap.add_argument("resdir"); ap.add_argument("out")
ap.add_argument("--caps", default="ceil,front0,gain20"); ap.add_argument("--height", type=float, default=4.6)
ap.add_argument("--rules", default=",".join(common.RULE_ORDER)); ap.add_argument("--extra", default="", help="second result file with more rules, e.g. helm_pow.csv"); ap.add_argument("--transpose", action="store_true", help="one row per cap (K | L1), for many caps")
a = ap.parse_args(); style.setup()
d = common.load_main(a.resdir, "helm_main.csv"); caps = a.caps.split(","); rules = a.rules.split(",")
if a.extra: import pandas as pd; d = pd.concat([d, common.load_main(a.resdir, a.extra)], ignore_index=True)
rng = np.random.default_rng(0)
if a.transpose: fig, axes = plt.subplots(len(caps), 2, figsize=(style.TEXTWIDTH_IN, a.height), sharey=True, sharex="col")
else: fig, axes = plt.subplots(2, len(caps), figsize=(style.TEXTWIDTH_IN, a.height), sharey="row", sharex="row")
AX = (lambda i, j: axes[j, i]) if a.transpose else (lambda i, j: axes[i, j])
for j, cap in enumerate(caps):
    for i, (col, xl) in enumerate([("K", "tasks touched $K$ (of 57)"), ("L1", "total score points $L_1$")]):
        ax = AX(i, j)
        for r, rule in enumerate(rules):
            s = d[(d.cap == cap) & (d.rule == rule)]; v = s.loc[s.feasible, col].to_numpy(float)
            c = style.RULE_COLOR[rule]
            ax.scatter(v, r + rng.uniform(-.28, .28, len(v)), s=3, color=c, alpha=.35, lw=0, rasterized=True)
            if len(v):
                q1, md, q3 = np.percentile(v, [25, 50, 75])
                ax.plot([q1, q3], [r, r], color="k", lw=1.6, solid_capstyle="butt")
                ax.plot([md], [r], marker="o", mfc="w", mec="k", ms=3.2, mew=.8, zorder=5)
            ax.text(1.01, r, f"{len(v)}/{len(s)}", transform=ax.get_yaxis_transform(), fontsize=5.5, va="center", ha="left", color="0.3")
        ax.set_ylim(len(rules) - .4, -.6)
        if col == "L1": ax.set_xscale("symlog", linthresh=1); ax.set_xlim(left=0); ax.set_xticks([0, 10, 100, 1000]); ax.set_xticklabels(["0", "10", "100", "1000"])
        else: ax.set_xlim(-1, 58)
        ax.set_xlabel(xl); ax.set_yticks(range(len(rules)))
        ax.tick_params(axis="y", length=0, labelleft=(i == 0 if a.transpose else j == 0))
        if a.transpose and i == 0: ax.set_title(common.CAP_LABEL[cap], fontsize=7.5, loc="left")
        elif not a.transpose and i == 0: ax.set_title(common.CAP_LABEL[cap], fontsize=7.5)
        if a.transpose and j < len(caps) - 1: ax.set_xlabel("")
YL = [style.RULE_LABEL[r] + ("*" if r == "condorcet" else "") for r in rules]
for k in range(len(caps) if a.transpose else 2): (axes[k, 0] if a.transpose else axes[k, 0]).set_yticklabels(YL)
fig.tight_layout(w_pad=2.2, h_pad=.6)
for ext in ("pdf", "png"): fig.savefig(f"{a.out}.{ext}", dpi=300)
common.write_provenance(a.out, "scripts/fig_cost_by_rule.py", a.resdir, ["helm_main.csv"] + ([a.extra] if a.extra else []), {"caps": caps, "rules": rules})
