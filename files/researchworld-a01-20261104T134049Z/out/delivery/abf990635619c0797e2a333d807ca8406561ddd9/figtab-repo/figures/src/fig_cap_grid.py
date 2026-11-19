"""F3: how the modelling assumption (per-task cap on the achievable gain) changes feasibility and cost, per rule and rank stratum.
Usage: python3 figures/src/fig_cap_grid.py RESULTS_DIR DATASET OUT_STEM
Input: RESULTS_DIR/core_<dataset>.csv. Caps ordered from tight to loose by the mean-rule feasible share over all targets; rules with results at only some caps (ordinal rules on the OLLB
top-50) are drawn as unconnected markers. Left: fraction of targets feasible (Wilson 95% CI); right: median L1/n among feasible
targets (95% bootstrap CI over targets, B=1000, seed 0), omitted where fewer than 3 targets are feasible."""
import sys, argparse, pathlib, json
import numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import style
ap = argparse.ArgumentParser(); ap.add_argument("resdir"); ap.add_argument("dataset"); ap.add_argument("out"); a = ap.parse_args(); style.setup()
d, prov = style.load_core(a.resdir, a.dataset); d = d[d.rank_mean >= 2]
ORDER = ["gain5", "emp95", "emp95T", "gain10", "emp99", "emp99T", "gain20", "emp99P", "front0", "ceil"]
LAB = {"gain5": "+5", "gain10": "+10", "gain20": "+20", "emp95": "emp95", "emp95T": "emp95$^T$", "emp99": "emp99", "emp99T": "emp99$^T$",
       "emp99P": "pooled\nemp99", "front0": "front", "ceil": "100"}
caps = [c for c in ORDER if c in set(d.cap)]
_fm = d[d.rule == "mean"].groupby("cap").feas.mean(); caps = sorted(caps, key=lambda c: (_fm[c], ORDER.index(c)))   # tight -> loose by the mean-rule feasible share
rules = [r for r in style.MAIN_RULES if r in set(d.rule)]
STRATA = [("rank 2--5", 2, 5), ("rank 6--20", 6, 20), ("rank 21--100", 21, 100)] if a.dataset == "ollb" else [("rank 2--5", 2, 5), ("rank 6--20", 6, 20), ("rank 21--78", 21, 78)]
fig, axes = plt.subplots(len(STRATA), 2, figsize=(style.TEXTWIDTH_IN, 1.55 * len(STRATA) + 0.5), sharex=True, squeeze=False)
rng = np.random.default_rng(0); meta = {}
for r, (sl, lo, hi) in enumerate(STRATA):
    ds = d[d.rank_mean.between(lo, hi)]; nt = ds[ds.rule == "mean"].target.nunique()
    for rule in rules:
        xs, fr, flo, fhi, xm, med, mlo, mhi = [], [], [], [], [], [], [], []
        for i, cap in enumerate(caps):
            s = ds[(ds.cap == cap) & (ds.rule == rule) & ~ds.cens]
            if len(s) == 0: continue
            k = int(s.feas.sum()); l, h = style.wilson(k, len(s)); xs.append(i); fr.append(k / len(s)); flo.append(l); fhi.append(h)
            meta[f"{sl}/{rule}/{cap}"] = dict(n=int(len(s)), feasible=k)
            f = s[s.feas].L1n.to_numpy(float)
            if len(f) >= 3:
                bs = np.median(rng.choice(f, (1000, len(f))), axis=1); xm.append(i); med.append(np.median(f)); mlo.append(np.percentile(bs, 2.5)); mhi.append(np.percentile(bs, 97.5))
        partial = len(xs) < len(caps)
        kw = dict(color=style.RULE_COLOR[rule], marker=style.RULE_MARK[rule], ms=3.5, label=style.RULE_LABEL[rule], ls="none" if partial else "-")
        axes[r, 0].plot(xs, fr, **kw); axes[r, 1].plot(xm, med, **kw)
        if not partial:
            axes[r, 0].fill_between(xs, flo, fhi, color=kw["color"], alpha=0.12, lw=0); axes[r, 1].fill_between(xm, mlo, mhi, color=kw["color"], alpha=0.15, lw=0)
        else:
            axes[r, 0].vlines(xs, flo, fhi, color=kw["color"], lw=0.8); axes[r, 1].vlines(xm, mlo, mhi, color=kw["color"], lw=0.8)
    axes[r, 0].set_ylim(-0.03, 1.03); axes[r, 0].set_ylabel(f"{sl} ({nt} targets)\nfraction feasible", fontsize=7)
    axes[r, 1].set_yscale("symlog", linthresh=0.1); axes[r, 1].set_ylim(bottom=0); axes[r, 1].set_yticks([0, 0.1, 1, 10]); axes[r, 1].set_yticklabels(["0", "0.1", "1", "10"])
    axes[r, 1].set_ylabel("points per task, $L_1/n$", fontsize=7)
for ax in axes[-1]: ax.set_xticks(range(len(caps))); ax.set_xticklabels([LAB[c] for c in caps], fontsize=6, rotation=35, ha="right")
fig.supxlabel("per-task cap on the gain, ordered tight $\\rightarrow$ loose by the share of targets feasible under the mean rule\n(+h: at most h points; emp: empirical fine-tune gain percentile;$^T$: transferred from OLLB; front: best rival score; 100: score ceiling)", fontsize=6)
h, l = axes[0, 0].get_legend_handles_labels(); fig.legend(h, l, loc="upper center", ncol=len(l), frameon=False, fontsize=6.8, bbox_to_anchor=(0.5, 1.02))
fig.tight_layout(rect=(0, 0, 1, 0.95))
for ext in ("pdf", "png"): fig.savefig(f"{a.out}.{ext}", dpi=200)
json.dump(dict(script="figures/src/fig_cap_grid.py", args={k: v for k, v in vars(a).items() if k != "resdir"}, inputs=[dict(file=f, sha256=h) for f, h in prov], cells=meta),
          open(f"{a.out}.json", "w"), indent=1)
