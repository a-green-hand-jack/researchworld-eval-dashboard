"""Fig 2 (column, C3 yardstick): is the rerun noise of the shipped estimator below variation practitioners already accept?
Per instance, the rerun disagreement d_rerun of the shipped estimator (mean pairwise 1 - top-3 Jaccard between its R reruns) is
compared with the disagreement of the exact phi* across background resamples (`background`), across retrains of the model that
differ in the seed only (`retrain, seed`) and across bootstrap retrains of the training set (`retrain, bootstrap`), the retrains
filtered to |AUC - AUC of the audited model| <= 0.01. One bar per (dataset x model, reference): the share of instances where the
rerun disagreement is smaller than, equal to, or larger than the reference (strict, as registered; ties are mostly 0 = 0).
Seed-only retraining of LR is deterministic, so that row is absent for LR (protocol note of 2026-11-18).
Input: results/yardstick_R20.csv. `--perm` draws the same for the Permutation explainer (appendix)."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import figstyle as fs, common as C

a = C.args(__doc__, extra=("--perm",))
arm = "perm" if a.perm else "kshap_default"
f = os.path.join(C.RESULTS, "yardstick_R20.csv")
y = pd.read_csv(f)
y["group"] = y.cell.str.replace(r"_s\d+$", "", regex=True)
p = y.group.map(lambda c: C.parse_cell(c + "_s0"))
y["dataset"] = p.map(lambda m: m["data"]); y["model"] = p.map(lambda m: m["model"])
col = f"d_rerun_{arm}"
REF = [("d_bg", "background"), ("d_retrain_seed", "retrain, seed"), ("d_retrain_boot", "retrain, bootstrap")]
order = [(d, m) for d in ("german", "ACSEmployment") for m in ("lr", "mlp", "gbdt")]
rows, rec = [], []   # rows: ("head", label) | ("bar", label, lt, tie, gt)
for d, m in order:
    g = y[(y.dataset == d) & (y.model == m)]
    if g.empty:
        continue
    rows.append(("head", f"{C.DATA_LABEL[d]} {C.MODEL_LABEL[m]} ($n={len(g)}$)"))
    for ref, lab in REF:
        if ref == "d_retrain_seed" and m == "lr":
            continue
        diff = g[ref].values - g[col].values
        lt, tie, gt = (diff > 1e-9).mean(), (np.abs(diff) <= 1e-9).mean(), (diff < -1e-9).mean()
        rows.append(("bar", lab, lt, tie, gt))
        rec.append({"dataset": d, "model": m, "reference": ref, "n": len(g), "share_rerun_lt_ref": lt, "share_tie": tie, "share_rerun_gt_ref": gt,
                    "mean_d_rerun": float(g[col].mean()), "mean_d_ref": float(g[ref].mean())})
n = len(rows)
fs.apply("column", (0.145 * n + 0.75) / 3.25)
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.36, right=0.95, top=1 - 0.05 / (0.145 * n + 0.75) * 3, bottom=0.62 / (0.145 * n + 0.75) * 1)
C_LT, C_TIE, C_GT = "#0072B2", "#BBBBBB", "#D55E00"
for i, r in enumerate(rows):
    yy = n - 1 - i
    if r[0] == "head":
        ax.text(-0.56, yy, r[1], transform=ax.get_yaxis_transform(), ha="left", va="center", fontweight="bold")
        continue
    _, lab, lt, tie, gt = r
    ax.barh(yy, lt, color=C_LT, height=0.72, lw=0)
    ax.barh(yy, tie, left=lt, color=C_TIE, height=0.72, lw=0)
    ax.barh(yy, gt, left=lt + tie, color=C_GT, height=0.72, lw=0)
    ax.text(-0.03, yy, lab, transform=ax.get_yaxis_transform(), ha="right", va="center")
ax.set_yticks([]); ax.set_ylim(-0.6, n - 0.4); ax.set_xlim(0, 1)
ax.spines["left"].set_visible(False)
ax.set_xlabel("share of instances")
ax.legend(handles=[Patch(color=C_LT, label="rerun $<$ reference"), Patch(color=C_TIE, label="equal"), Patch(color=C_GT, label="rerun $>$ reference")],
          loc="upper center", bbox_to_anchor=(0.35, -0.2), ncol=3, frameon=False, handlelength=1.0, columnspacing=1.0, handletextpad=0.4)
suffix = "" if arm == "kshap_default" else "_perm"
out = os.path.join(C.outdir(a), f"fig2_yardstick{suffix}.pdf")
fig.savefig(out)
pv = C.provenance([f]); pv["arm"] = arm; pv["rows"] = rec
json.dump(pv, open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
