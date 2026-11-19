"""F5: stability of the minimum investment under evaluation noise and task resampling, for a handful of targets.
Usage: python3 figures/src/fig_robust.py RESULTS_DIR OUT_STEM
Inputs: RESULTS_DIR/summary/summary_rob_{ollb_noise_closed_emp99, ollb_taskboot_closed_emp99, helm_taskboot_emp99T}.csv and the matching
core tables (point estimate on the observed data). Bars = 2.5-97.5 percentile of L1 over feasible Monte Carlo draws (not a CI of the median);
dot = median of the draws; open diamond = value on the observed data (core table). The share of draws in which first place is
unreachable within the cap is written above each bar when > 5%. Bars absent where every draw is infeasible."""
import sys, pathlib, json, hashlib
import numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import style
res, out = pathlib.Path(sys.argv[1]), sys.argv[2]; style.setup()
PANELS = [("ollb", ["ollb_noise_closed_emp99", "ollb_noise_ord_emp99"], "OLLB, evaluation noise"),
          ("ollb", ["ollb_taskboot_closed_emp99", "ollb_taskboot_ord_emp99"], "OLLB, task bootstrap"),
          ("helm", ["helm_noise_emp99T"], "HELM, evaluation noise"), ("helm", ["helm_taskboot_emp99T"], "HELM, task bootstrap")]
fig, AX = plt.subplots(4, 2, figsize=(style.TEXTWIDTH_IN, 6.8), gridspec_kw=dict(height_ratios=[3, 1.1, 3, 1.1])); prov = []
for (ax, bx), (ds, names, title) in zip([(AX[0, 0], AX[1, 0]), (AX[0, 1], AX[1, 1]), (AX[2, 0], AX[3, 0]), (AX[2, 1], AX[3, 1])], PANELS):
    ps = [res / "summary" / f"summary_rob_{nm}.csv" for nm in names]; s = pd.concat([pd.read_csv(p) for p in ps])
    prov += [dict(file="summary/" + p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in ps]
    core, pc = style.load_core(res, ds); capn = style.PRIMARY_CAP[ds]; core = core[core.cap == capn]
    prov.append(dict(file=pc[0][0], sha256=pc[0][1]))
    rules = [r for r in ("mean", "median", "min", "borda", "condorcet") if r in set(s.rule)]
    tg = s.drop_duplicates("target").sort_values("rank_mean_obs"); order = list(tg.target); ranks = list(tg.rank_mean_obs)
    top = 1.0; DX = 0.045   # median dot left of the bar, observed diamond right of it, so the two never overlap
    for ri, rule in enumerate(rules):
        for ti, t in enumerate(order):
            x = ti + (ri - (len(rules) - 1) / 2) * 0.17; r = s[(s.rule == rule) & (s.target == t)]
            if r.empty: continue
            r = r.iloc[0]; c = style.RULE_COLOR[rule]
            if np.isfinite(r["L1_p50"]):
                ax.vlines(x, r["L1_p2.5"], r["L1_p97.5"], color=c, lw=1.4); ax.plot(x - DX, r["L1_p50"], "o", color=c, ms=3, clip_on=False); top = max(top, r["L1_p97.5"])
            o = core[(core.rule == rule) & (core.target == t)]
            if len(o) and np.isfinite(o.L1.iloc[0]): (ax.plot(x + DX, o.L1.iloc[0], "D", mfc="none", mec=c, ms=3.5, mew=0.9, clip_on=False), top := max(top, o.L1.iloc[0]))
            bx.plot(x, 100 * r["L1_infeasible"], "s", color=c, ms=3)
    for a_ in (ax, bx): a_.set_xlim(-0.6, len(order) - 0.4)
    ax.set_xticks(range(len(order))); ax.set_xticklabels([])
    bx.set_xticks(range(len(order))); bx.set_xticklabels([str(int(k)) for k in ranks], fontsize=7); bx.set_ylim(-5, 105); bx.set_yticks([0, 50, 100])
    ax.set_yscale("symlog", linthresh=0.5); ax.set_ylim(0, top * 1.8)   # headroom: no marker sits on or beyond the frame
    tk = [t_ for t_ in (0, 1, 10, 100, 1000) if t_ <= top * 1.8]; ax.set_yticks(tk); ax.set_yticklabels([str(t_) for t_ in tk])
    ax.set_title(title, fontsize=7.5, loc="left"); bx.set_xlabel("target's rank under the mean", fontsize=7)
for r in (0, 2): AX[r, 0].set_ylabel("minimum $L_1$ (points)", fontsize=7); AX[r + 1, 0].set_ylabel("% draws\ninfeasible", fontsize=7)
from matplotlib.lines import Line2D
hs = [Line2D([], [], color=style.RULE_COLOR[r], lw=1.6, label=style.RULE_LABEL[r]) for r in ("mean", "median", "min", "borda", "condorcet")]
hs += [Line2D([], [], ls="none", marker="o", color="0.3", ms=3, label="median of draws"), Line2D([], [], ls="none", marker="D", mfc="none", mec="0.3", ms=3.5, label="observed data")]
fig.legend(handles=hs, loc="upper center", ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.5, 1.02)); fig.tight_layout(rect=(0, 0, 1, 0.955))
for ext in ("pdf", "png"): fig.savefig(f"{out}.{ext}", dpi=200)
json.dump(dict(script="figures/src/fig_robust.py", inputs=prov), open(f"{out}.json", "w"), indent=1)
