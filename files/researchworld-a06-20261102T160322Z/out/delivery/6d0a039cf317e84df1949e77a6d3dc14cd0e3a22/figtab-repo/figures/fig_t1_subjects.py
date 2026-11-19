"""Appendix figure (Q1a): where the optimism sits on the real MMLU-Pro matrix. Gap of the selected config per MMLU-Pro subject
(exhaustive search, n=500; K=24 and K=300), mean over 1000 replicates ± 1.96 x replicate-mean SE (mcse). A subject holds only 16-63 of the
n=500 search items, and replicates share items, so mcse understates the uncertainty: read the pattern, not single subjects.
Reads results/subject_breakdown.csv. Writes figures/fig_t1_subjects.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
s = pd.read_csv(common.path("subject_breakdown.csv"))
c = s.cell_id.str.extract(r"proc=(\w+)\|n=(\d+)\|K=(\d+)")
s["proc"], s["n"], s["K"] = c[0], c[1].astype(int), c[2].astype(int)
s = s[(s.proc == "exhaustive") & (s.n == 500)]
order = s[s.K == 300].sort_values("mean_gap").subject.tolist()
y = np.arange(len(order))
fig, ax = plt.subplots(figsize=(style.TEXT_WIDTH_IN, 3.0))
for K, col, off in [(24, style.OKABE_ITO[1], -0.15), (300, style.OKABE_ITO[5], 0.15)]:
    d = s[s.K == K].set_index("subject").loc[order]
    ax.errorbar(100 * d.mean_gap, y + off, xerr=196 * d.mcse, fmt="o", ms=3, lw=0.9, color=col, capsize=1.5, label=f"K={K}")
ax.axvline(0, color="0.5", lw=0.6)
ax.set_yticks(y); ax.set_yticklabels(order)
ax.set_xlabel("reported − fresh accuracy within subject (points)")
ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
fig.tight_layout(pad=0.4)
fig.savefig(f"{common.OUT}/fig_t1_subjects.pdf")
d = s[s.K == 300]
print("n_search_items per subject (n=500): %.1f-%.1f" % (d.n_search_items.min(), d.n_search_items.max()))
