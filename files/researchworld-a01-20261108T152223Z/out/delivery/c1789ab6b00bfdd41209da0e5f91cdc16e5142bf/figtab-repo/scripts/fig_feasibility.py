"""Feasibility of first place by cap and rule (HELM): (a) share of the 79 targets for which first place is reachable at all,
(b) the same share by the target's current rank under the mean rule, for cap = base+20 (10 targets per bin, so no interval is drawn: a share of 0.9 is 9/10).
Usage: python3 scripts/fig_feasibility.py RESDIR OUT_STEM. Input: helm_main.csv (infeasible cells have K = inf)."""
import sys, argparse, pathlib
import numpy as np, matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import style, common
ap = argparse.ArgumentParser(); ap.add_argument("resdir"); ap.add_argument("out"); ap.add_argument("--cap_b", default="gain20")
a = ap.parse_args(); style.setup()
d = common.load_main(a.resdir, "helm_main.csv"); rules = common.RULE_ORDER; caps = common.CAP_ORDER
fig, (ax, bx) = plt.subplots(1, 2, figsize=(style.TEXTWIDTH_IN, 2.9), gridspec_kw=dict(width_ratios=[1.05, 1]))
share = np.array([[d[(d.cap == c) & (d.rule == r)].feasible.mean() for c in caps] for r in rules])
cnt = np.array([[int(d[(d.cap == c) & (d.rule == r)].feasible.sum()) for c in caps] for r in rules])
im = ax.imshow(share, vmin=0, vmax=1, cmap="viridis", aspect="auto")
for i in range(len(rules)):
    for j in range(len(caps)):
        ax.text(j, i, cnt[i, j], ha="center", va="center", fontsize=6.5, color="k" if share[i, j] > .6 else "w")
ax.set_xticks(range(len(caps))); ax.set_xticklabels(["100", "best\n+2", "best\n+0", "base\n+20", "base\n+10", "base\n+5"])
ax.set_yticks(range(len(rules))); ax.set_yticklabels([style.RULE_LABEL[r] + ("*" if r == "condorcet" else "") for r in rules])
ax.spines[:].set_visible(False); ax.tick_params(length=0); ax.set_xlabel("cap on each task's score"); ax.set_title("(a) feasible targets (of 79)", fontsize=7.5)
cb = fig.colorbar(im, ax=ax, fraction=.05, pad=.02); cb.set_label("share feasible", fontsize=6.5); cb.ax.tick_params(labelsize=6)
BINS = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50), (51, 60), (61, 70), (71, 79)]
for r in rules:
    s = d[(d.cap == a.cap_b) & (d.rule == r)]; xs, ps, lo, hi = [], [], [], []
    for l, h in BINS:
        t = s[(s.rank_mean >= l) & (s.rank_mean <= h)]; k = int(t.feasible.sum()); w = common.wilson(k, len(t))
        xs.append((l + h) / 2); ps.append(k / len(t)); lo.append(w[0]); hi.append(w[1])
    bx.plot(xs, ps, color=style.RULE_COLOR[r], marker=style.RULE_MARK[r], ms=3, lw=.9, label=style.RULE_LABEL[r] + ("*" if r == "condorcet" else ""))
bx.set_ylabel("share of targets feasible"); bx.set_ylim(-.02, 1.02)
bx.set_title(f"(b) {common.CAP_LABEL[a.cap_b]}", fontsize=7.5); bx.set_xticks([5, 15, 25, 35, 45, 55, 65, 75]); bx.set_xticklabels(["1-10", "", "21-30", "", "41-50", "", "61-70", ""])
bx.set_xlabel("target's rank under the mean rule")
fig.tight_layout(rect=(0, .1, 1, 1)); h, l = bx.get_legend_handles_labels(); fig.legend(h, l, frameon=False, loc="lower center", ncol=5, fontsize=6)
for ext in ("pdf", "png"): fig.savefig(f"{a.out}.{ext}", dpi=300)
common.write_provenance(a.out, "scripts/fig_feasibility.py", a.resdir, ["helm_main.csv"], {"cap_b": a.cap_b})
