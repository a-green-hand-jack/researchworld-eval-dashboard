"""Real-II figure: model x prompt pool.  (a) accuracy of each of the pool's configurations (population accuracy) ; (b) optimism vs B for several n."""
import sys; sys.path.insert(0, "/work/code")
import pandas as pd, numpy as np
from figstyle import *
from realdata import load_pool2
Y, names = load_pool2(return_names=True); N, K = Y.shape
p = Y.mean(0)
fig, ax = plt.subplots(1, 2, figsize=(5.6, 2.3))
models = []
for nm in names:
    m = nm.split(":")[0]
    if m not in models: models.append(m)
lab = {"qwen25_15b": "Qwen2.5-1.5B", "m_qwen2_15b": "Qwen2-1.5B", "m_qwen3_17b": "Qwen3-1.7B", "m_qwen3_06b": "Qwen3-0.6B", "m_qwen25_05b": "Qwen2.5-0.5B"}
for i, m in enumerate(models):
    idx = [j for j, nm in enumerate(names) if nm.startswith(m + ":")]
    ax[0].scatter([i] * len(idx), 100 * p[idx], color=OI[i % 7], s=14)
ax[0].set_xticks(range(len(models))); ax[0].set_xticklabels([lab[m] for m in models], rotation=25, ha="right"); ax[0].set_ylabel("accuracy of each configuration [%]")
ax[0].set_title(f"(a) pool: {K} configs, {N} items")
sw = pd.read_parquet("/work/results/real2_sweep.parquet"); sw = sw[sw.method == "naive"].copy(); sw["opt"] = sw.est - sw.truth
for i, n in enumerate((50, 100, 200)):
    g = sw[sw.n == n].groupby("kw_B").opt.agg(["mean", "std", "count"]).reset_index(); g["se"] = g["std"] / np.sqrt(g["count"])
    ax[1].errorbar(g.kw_B, 100 * g["mean"], yerr=100 * 1.96 * g.se, color=OI[i], marker="o", capsize=0, label=f"n={n}")
ax[1].set_xscale("log", base=2); ax[1].set_xticks([1, 2, 4, 8, 16, 32]); ax[1].set_xticklabels(["1", "2", "4", "8", "16", "32"]); ax[1].minorticks_off()
ax[1].set_xlabel("search budget B"); ax[1].set_ylabel("optimism [pts]"); ax[1].legend(frameon=False); ax[1].set_title("(b) optimism, model x prompt pool")
plt.tight_layout(); plt.savefig("/work/paper/figs/fig_real2.pdf"); print("ok")
