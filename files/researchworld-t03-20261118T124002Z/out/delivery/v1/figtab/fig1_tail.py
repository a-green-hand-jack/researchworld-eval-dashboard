"""Fig 1 (figure*, C1 + d): the mean hides a tail.
(a) ECDF of per-instance r_3 at the shipped default budget (x1), exact top-3 (solid) and eps=0.10-tolerant top-3 (dotted), one curve
per dataset/model, exact mean marked (the x16 version of the exact ECDF is figA_ecdf_x16.pdf);
(b) reliable fraction F_3(delta=0.1) vs dimension d at x1, cluster-bootstrap CI;
(c) observed r_3 against z = gap/SE (true z, and plug-in z from a single run), binned.
Input: results/tidy_*.csv (+ plugz_*.npz for the plug-in curve)."""
import os, glob, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import figstyle as fs, common as C

K, DELTA = 3, 0.10
a = C.args(__doc__)
fs.apply("text", 0.40)
df, files = C.load_tidy(a.pilot)
sub, sub_files = C.load_tidy(a.pilot, subsets=True)   # d-curve cells (feature subsets of German / ACS), preliminary
main_files, files = files, files + sub_files
sub = sub[sub.dataset.isin(["german", "ACSEmployment"])]   # probability-scale cells only; Arrhythmia is on the margin scale
d3 = df[(df.arm == C.DEFAULT_ARM) & (df.k == K)].copy()
# players that vary between x and the background (`nvar`) are the d of the Shapley game (protocol §1)
d3["d"] = d3["nvar"]
d3["group"] = d3.dataset.map(lambda s: C.DATA_LABEL.get(s, s)) + " " + d3.model.map(lambda s: C.MODEL_LABEL.get(s, s.upper()))
groups = sorted(d3.group.unique())
pal = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442"]
col = {g: pal[i % len(pal)] for i, g in enumerate(groups)}

fig, ax = plt.subplots(1, 3, gridspec_kw={"width_ratios": [1.15, 1, 1.05], "wspace": 0.38})
fig.subplots_adjust(left=0.07, right=0.99, bottom=0.36, top=0.92)

# (a) ECDF per instance
for g in groups:
    for rc, ls in (("r", "-"), ("r_eps10", (0, (1, 1.2)))):
        v = d3[(d3.group == g) & (d3.budget == "x1")].groupby(["cell", "inst"])[rc].mean().values
        if len(v) == 0:
            continue
        x, y = C.ecdf(v)
        ax[0].step(x, y, where="post", color=col[g], ls=ls, lw=1.0 if rc == "r" else 1.3)
        if rc == "r":
            ax[0].plot([v.mean()], [0], marker="v", ms=4, color=col[g], clip_on=False, zorder=5)
ax[0].axvline(1 - DELTA, color="0.5", lw=0.6, ls=":")
ax[0].set_xlabel(r"per-instance $r_3$ (P[top-3 correct])")
ax[0].set_ylabel("cumulative fraction of instances")
ax[0].set_xlim(0, 1.02); ax[0].set_ylim(0, 0.5)   # the lower tail is the content; the ECDF is 1 at r=1 for every curve
from matplotlib.lines import Line2D
h = [Line2D([], [], color=col[g], lw=1.2, label=g) for g in groups]
h += [Line2D([], [], color="0.3", lw=1.0, label="exact top-3"), Line2D([], [], color="0.3", lw=1.3, ls=(0, (1, 1.2)), label="$\\epsilon=0.1$-tolerant top-3"),
      Line2D([], [], color="0.3", marker="v", ls="", ms=4, label="mean (exact)")]
fig.legend(handles=h, frameon=False, loc="lower center", ncol=5, handlelength=1.6, columnspacing=1.2, labelspacing=0.3, bbox_to_anchor=(0.5, -0.01))

# (b) reliable fraction vs d
d3b = pd.concat([d3, sub[(sub.arm == C.DEFAULT_ARM) & (sub.k == K)]], ignore_index=True)
d3b["d"] = d3b["nvar"]
d3b["group"] = d3b.dataset.map(lambda s: C.DATA_LABEL.get(s, s)) + " " + d3b.model.map(lambda s: C.MODEL_LABEL.get(s, s.upper()))
x1 = d3b[d3b.budget == "x1"].groupby(["cell", "inst"], as_index=False).agg(r=("r", "mean"), d=("d", "first"), seed=("seed", "first"),
                                                                        group=("group", "first"))
x1["rel"] = (x1.r >= 1 - DELTA).astype(float)
for g in groups:
    sg = x1[x1.group == g]
    pts = []
    for dd, s in sg.groupby("d"):
        m, lo, hi = C.cluster_boot(s, lambda f: f.rel.mean(), B=500)
        pts.append((dd, m, lo, hi))
    if not pts:
        continue
    p = np.array(pts)
    ax[1].errorbar(p[:, 0], p[:, 1], yerr=[p[:, 1] - p[:, 2], p[:, 3] - p[:, 1]], color=col[g], marker="o", ms=3.5, lw=1, capsize=1.5)
dvals = sorted(x1.d.unique())
ax[1].set_xticks(dvals); ax[1].set_xlim(min(dvals) - 1.5, max(dvals) + 1.5); ax[1].set_ylim(0, 1.02)
ax[1].set_xlabel("number of attributes $d$")
ax[1].set_ylabel(r"fraction with $r_3\geq 0.9$")

# (c) r vs z (true and plug-in), binned by quantile
def binned(z, ok, nb=6):
    q = np.unique(np.quantile(z, np.linspace(0, 1, nb + 1)))
    idx = np.clip(np.digitize(z, q[1:-1]), 0, len(q) - 2)
    return np.array([(np.median(z[idx == i]), ok[idx == i].mean()) for i in range(len(q) - 1) if (idx == i).sum() >= 5])
# the plug-in z exists for the Covert-Lee arm only (its own SE), so both curves use that arm's runs at x1
t = df[(df.arm == "covert_lee") & (df.k == K) & (df.budget == "x1")]
bt = binned(t.z_true.clip(upper=1e3).values, t.r.values)
if len(bt):
    ax[2].plot(bt[:, 0], bt[:, 1], "o-", color="#0072B2", ms=3.5, label="true $z$ (needs $\\phi^*$)")
zs, oks = [], []
for f in main_files:
    pz = f.replace("tidy_", "plugz_").replace(".csv", ".npz")
    if os.path.exists(pz):
        w = np.load(pz)
        if f"zplug/x1/k{K}" in w.files:
            zs.append(w[f"zplug/x1/k{K}"].ravel()); oks.append(w[f"ok/x1/k{K}"].ravel().astype(float))
if zs:
    bp = binned(np.concatenate(zs), np.concatenate(oks))
    if len(bp):
        ax[2].plot(bp[:, 0], bp[:, 1], "s--", color="#D55E00", ms=3.5, label="plug-in $z$ (one run)")
ax[2].set_xscale("log"); ax[2].set_ylim(0, 1.02)
ax[2].set_xticks([0.1, 1]); ax[2].set_xticklabels(["0.1", "1"]); ax[2].minorticks_off()
ax[2].set_xlabel("$z=$ gap / SE of gap")
ax[2].set_ylabel("observed $r_3$")
if ax[2].get_legend_handles_labels()[0]:
    ax[2].legend(frameon=False, loc="lower right")

for i, l in enumerate("abc"):
    ax[i].text(-0.02, 1.04, f"({l})", transform=ax[i].transAxes, fontweight="bold", va="bottom", ha="right")
out = os.path.join(C.outdir(a), "fig1_tail.pdf")
fig.savefig(out)
json.dump(C.provenance(files), open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
