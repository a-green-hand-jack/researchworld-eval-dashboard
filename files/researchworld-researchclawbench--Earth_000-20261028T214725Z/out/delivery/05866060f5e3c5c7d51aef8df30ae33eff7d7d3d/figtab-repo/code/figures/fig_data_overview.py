"""Figure 1 (inventory heatmap), Figure 2 (temporal coverage), Table T1 (inventory) from raw glambie/input."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from common import *

inv = inventory()
os.makedirs(TAB, exist_ok=True)
inv.to_csv(os.path.join(TAB, "input_inventory_files.csv"), index=False)

cnt = inv.pivot_table(index="region_id", columns="method", values="file", aggfunc="count", fill_value=0)[METHODS]
cnt["total"] = cnt.sum(axis=1)
cnt.insert(0, "region", [REGIONS[i] for i in cnt.index])
cnt.loc["all"] = ["All regions"] + cnt[METHODS + ["total"]].sum().tolist()
cnt.to_csv(os.path.join(TAB, "T1_inventory_region_by_method.csv"))
with open(os.path.join(TAB, "T1_inventory_region_by_method.md"), "w") as fh:
    fh.write("| # | Region | " + " | ".join(METHOD_LABEL[m] for m in METHODS) + " | Total |\n")
    fh.write("|--:|:--|" + "--:|" * (len(METHODS) + 1) + "\n")
    for i, r in cnt.iterrows():
        fh.write(f"| {i if i != 'all' else ''} | {r['region']} | " + " | ".join(str(int(r[m])) for m in METHODS) + f" | {int(r['total'])} |\n")

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# Fig 1: heatmap of counts
M = cnt.drop("all")[METHODS].values.astype(int)
fig, ax = plt.subplots(figsize=(6.6, 6.2))
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=M.max() + 1, aspect="auto")
ax.set_xticks(range(len(METHODS)), [METHOD_LABEL[m] for m in METHODS], rotation=25, ha="right")
ax.set_yticks(range(19), [f"{i}  {REGIONS[i]}" for i in range(1, 20)])
for (i, j), v in np.ndenumerate(M):
    ax.text(j, i, v, ha="center", va="center", color="white" if v > M.max() * 0.6 else "black")
ax.set_xlabel("Observation method of the submitted estimate")
ax.set_title(f"Submitted regional estimates per method (n = {M.sum()} input files)", fontsize=10)
for s in ax.spines.values():
    s.set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig01_input_inventory.png"), dpi=200)
plt.close(fig)

# Fig 2: temporal coverage; one thin bar per file, grouped by region, coloured by method
fig, axes = plt.subplots(5, 4, figsize=(11, 10.5), sharex=True)
axes = axes.ravel()
for k, rid in enumerate(range(1, 20)):
    ax = axes[k]
    sub = inv[inv.region_id == rid].copy()
    sub["mo"] = sub.method.map({m: i for i, m in enumerate(METHODS)})
    sub = sub.sort_values(["mo", "start"]).reset_index(drop=True)
    for y, r in sub.iterrows():
        ax.hlines(y, max(r.start, 1960), r.end, color=METHOD_COLOR[r.method], lw=2.2)
    ax.axvspan(2000, 2024, color="0.9", zorder=0)
    ax.set_title(f"{rid} {REGIONS[rid]}", fontsize=8.5, loc="left")
    ax.set_yticks([])
    ax.set_xlim(1960, 2026)
axes[19].axis("off")
axes[19].legend(handles=[Line2D([0], [0], color=METHOD_COLOR[m], lw=3, label=METHOD_LABEL[m]) for m in METHODS]
                + [plt.Rectangle((0, 0), 1, 1, color="0.9", label="GlaMBIE period 2000–2023")],
                loc="center", frameon=False)
for ax in axes[15:19]:
    ax.set_xlabel("Year")
fig.suptitle("Temporal coverage of each submitted estimate (one line per file; start clipped at 1960)", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig02_input_coverage.png"), dpi=170)
plt.close(fig)
print(cnt.loc["all"].to_dict())
print(inv.unit.value_counts().to_dict(), inv.method.value_counts().to_dict())
