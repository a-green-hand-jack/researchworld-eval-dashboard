"""F1 (OLLB) / F2 (HELM): feasibility and conditional investment vs. the target's current rank, per rule, primary and oracle caps.
Usage: python3 figures/src/fig_rank_rules.py RESULTS_DIR DATASET(ollb|helm) OUT_STEM [--rules mean,median,...] [--caps primary,ceil]
Input: RESULTS_DIR/core_<dataset>.csv. Columns used: cap, rule, target, rank_mean, K, L1, status.
Panels per cap row: fraction of targets for which first place is reachable within the cap (Wilson 95% CI; bins with <3 targets omitted), and median K/n and L1/n *among feasible targets* (95% bootstrap CI of the bin median over targets, B=1000, seed 0).
Targets already first under the rule cost 0 and count as feasible. Writes OUT_STEM.{pdf,png,json}."""
import sys, argparse, pathlib, json
import numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import style
ap = argparse.ArgumentParser(); ap.add_argument("resdir"); ap.add_argument("dataset"); ap.add_argument("out")
ap.add_argument("--rules", default=",".join(style.MAIN_RULES)); ap.add_argument("--caps", default="primary,ceil")
a = ap.parse_args(); style.setup()
d, prov = style.load_core(a.resdir, a.dataset)
caps = [style.PRIMARY_CAP[a.dataset] if c == "primary" else c for c in a.caps.split(",")]
rules = [r for r in a.rules.split(",") if r in set(d.rule)]
d = d[(d.rank_mean >= 2) & d.cap.isin(caps) & d.rule.isin(rules)]
fig, axes = plt.subplots(len(caps), 3, figsize=(style.TEXTWIDTH_IN, 2.0 * len(caps) + 0.45), squeeze=False)
meta = {}
for r, cap in enumerate(caps):
    dc = d[d.cap == cap]
    for rule in rules:
        s = dc[dc.rule == rule]
        if s.empty: continue
        kw = dict(color=style.RULE_COLOR[rule], marker=style.RULE_MARK[rule], ms=3, label=style.RULE_LABEL[rule])
        f = style.feas_binned(s)
        axes[r, 0].plot(f.x, f.frac, **kw); axes[r, 0].fill_between(f.x, f.lo, f.hi, color=kw["color"], alpha=0.12, lw=0)
        for ax, col in zip(axes[r, 1:], ("Kn", "L1n")):
            b = style.rank_binned(s[s.feas], col, min_n=3)
            if len(b): ax.plot(b.x, b.med, **kw); ax.fill_between(b.x, b.lo, b.hi, color=kw["color"], alpha=0.15, lw=0)
        meta[f"{cap}/{rule}"] = dict(n_targets=int(len(s)), feasible_fraction=float(s.feas.mean()),
                                    n_censored=int(s.cens.sum()), max_rank=int(s.rank_mean.max()))
    axes[r, 0].set_ylim(-0.03, 1.03); axes[r, 0].set_ylabel("fraction feasible")
    axes[r, 1].set_ylabel("tasks touched, $K/n$"); axes[r, 2].set_ylabel("points per task, $L_1/n$")
    axes[r, 1].set_ylim(bottom=0); axes[r, 2].set_yscale("symlog", linthresh=0.1); axes[r, 2].set_ylim(bottom=0)
    axes[r, 2].set_yticks([0, 0.1, 1, 10]); axes[r, 2].set_yticklabels(["0", "0.1", "1", "10"])
    axes[r, 0].set_title(f"{style.DATASET_LABEL[a.dataset]}: {style.CAP_LABEL[cap]}", loc="left", fontsize=6.5)
    for ax in axes[r]:
        style.log_axis(ax); ax.set_xticks([x for x in (2, 10, 100, 1000) if x <= d.rank_mean.max()])
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=len(l), frameon=False, fontsize=6.8, bbox_to_anchor=(0.5, 1.02))
fig.supxlabel("target's current rank under the mean rule (log scale)", fontsize=8)
fig.tight_layout(rect=(0, 0, 1, 0.94))
for ext in ("pdf", "png"): fig.savefig(f"{a.out}.{ext}", dpi=200)
args = {k: v for k, v in vars(a).items() if k != "resdir"}
json.dump(dict(script="figures/src/fig_rank_rules.py", args=args, inputs=[dict(file=f, sha256=h) for f, h in prov], summary=meta),
          open(f"{a.out}.json", "w"), indent=1)
