"""Fig. 3 (C2): (a) smallest verified attack that changes the top-1 model/team, % of N, per dataset and perturbation
(dot = original data, bar = 2.5-97.5 percentile over bootstrap resamples of the comparisons, drawn only with >= 20 resamples); (b) benign random drop/flip
probability that top-1 changes vs. the same budget, Wilson 95% bands, with the adversarial budget marked.
Reads results/decisions_*.csv, results/benign_*.csv. Usage: fig3_top1_adv_vs_benign.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter
sys.path.insert(0, os.path.dirname(__file__)); import style, common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "figures"
style.apply(); os.makedirs(out, exist_ok=True)
dec = common.load(res, "decisions"); ben = common.load(res, "benign")
fig, (a, b) = plt.subplots(1, 2, figsize=(style.TEXTW, 2.4), gridspec_kw=dict(width_ratios=[1, 1.05]))
PT = [("drop", "remove"), ("flip", "flip"), ("add_a_wins", "inject")]
n = len(dec); w = 0.8 / max(n, 1)
for i, (k, d) in enumerate(dec.items()):
    lab, col, mk, ls = style.DATASETS[k]
    for j, (pt, _) in enumerate(PT):
        est, lo, hi, nb = common.attack_budget(d, "top1", "influence_exact", pt)
        if np.isnan(est): continue
        x = j + (i - (n - 1) / 2) * w
        if nb < 20: lo = hi = est   # no bootstrap bar unless >= 20 resamples
        a.errorbar(x, est * 100, yerr=[[max(est - lo, 0) * 100], [(min(hi, 0.5) - est) * 100]], color=col, marker=mk, ms=4, lw=0.9, capsize=1.5, label=lab if j == 0 else None)
a.set_yscale("log"); a.set_xticks(range(len(PT))); a.set_xticklabels([p[1] for p in PT]); a.set_ylabel("smallest top-1 change found, % of $N$")
a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); a.yaxis.set_minor_formatter(NullFormatter()); a.set_yticks([0.001, 0.01, 0.1, 1, 10]); a.set_ylim(0.0008, 20); a.grid(axis="y", alpha=0.25, lw=0.4); a.legend(loc="lower center", bbox_to_anchor=(0.5, -0.5), ncol=2, fontsize=6.5, columnspacing=0.8, handletextpad=0.3)
a.set_title("(a) adversarial", loc="left")
for k, d in ben.items():
    lab, col, mk, ls = style.DATASETS[k]
    for pt, st in (("random_drop", "-"), ("random_flip", "--")):
        s = d[(d.perturbation_type == pt) & (d.metric == "p_top1")].sort_values("budget_frac")
        b.plot(s.budget_frac * 100, s.value, color=col, ls=st, marker=mk, ms=2.5, lw=1)
        if pt == "random_drop": b.fill_between(s.budget_frac * 100, s.ci_lo, s.ci_hi, color=col, alpha=0.12, lw=0)
    if k in dec:
        for pt, st in (("drop", "-"), ("flip", "--")):
            est = common.attack_budget(dec[k], "top1", "influence_exact", pt)[0]
            if not np.isnan(est): b.axvline(est * 100, color=col, ls=st, lw=0.6, alpha=0.6)
b.set_xscale("log"); b.set_xlabel("random perturbation size, % of $N$"); b.set_ylabel("P(top-1 changes)"); b.set_ylim(-0.02, 1.02)
b.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); b.grid(alpha=0.25, lw=0.4)
b.set_title("(b) random (solid: remove, dashed: flip)", loc="left")
fig.tight_layout(w_pad=1.0); fig.savefig(f"{out}/fig3_top1_adv_vs_benign.pdf"); fig.savefig(f"{out}/fig3_top1_adv_vs_benign.png", dpi=200)
