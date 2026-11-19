"""E5: mechanism mismatch (count channel, two-hop spillover, corrupted graph)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_lib import *

reps, gr, cf = load("E5")
m = metrics(reps, cf, boot=True)
m.to_csv(os.path.join(TAB, "E5_metrics.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)

# ---- count channel: predicted limit for frac-regression = delta + beta d_H/dbar
c = m[m.tag == "count"].copy()
pred = []
for _, r in c[c.est == "lin_frac"].iterrows():
    g = gr[gr.cid == r.cid]
    pred.append(dict(cid=r.cid, bias_pred=np.mean([-(1 - st.harm_deg / st.mean_deg) for _, st in g.iterrows()]),
                     harm=g.harm_deg.mean(), mean=g.mean_deg.mean()))
pred = pd.DataFrame(pred)
c = c.merge(pred, on="cid", how="left")
c["graph"] = c.gkind + c.d_spec.fillna(0).astype(int).astype(str)
t = c.pivot_table(index="graph", columns="est", values="rel_rmse")
t2 = c[c.est == "lin_frac"].set_index("graph")[["bias", "bias_pred", "harm", "mean"]]
print(t.round(3)); print(t2.round(3))
c.to_csv(os.path.join(TAB, "E5_count.csv"), index=False)
cb = c.pivot_table(index="graph", columns="est", values="rel_bias")
print(cb.round(3))

# ---- two-hop
th = m[m.tag == "twohop"].copy()
t = th.pivot_table(index=["gkind", "dkind", "omega"], columns="est", values=["rel_bias", "rel_rmse"])
print(t.round(3))
th.to_csv(os.path.join(TAB, "E5_twohop.csv"), index=False)

# ---- edge drop
ed = m[m.tag == "edgedrop"].copy()
t = ed.pivot_table(index=["gkind", "s", "edge_drop"], columns="est", values=["rel_bias", "rel_rmse"])
print(t.round(3))
ed.to_csv(os.path.join(TAB, "E5_edgedrop.csv"), index=False)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
w = 0.2
gl = list(c.graph.unique())
for j, (e, col) in enumerate((("dm", "0.6"), ("lin_frac", "C3"), ("lin_count", "C0"), ("lin_both", "C2"))):
    g = c[c.est == e].set_index("graph").loc[gl]
    ax[0].bar(np.arange(len(gl)) + j * w, g.rel_bias, width=w, color=col, label=e)
ax[0].plot(np.arange(len(gl)) + 1.5 * w - 0.1, (c[c.est == "lin_frac"].set_index("graph").loc[gl].bias_pred * 0.5), "k_", ms=12, label="pred. (lin_frac)")
ax[0].set_xticks(np.arange(len(gl)) + 1.5 * w); ax[0].set_xticklabels(gl, rotation=60, fontsize=6)
ax[0].set_ylabel("relative bias (count channel)"); ax[0].legend(fontsize=6)
for gk, col in (("er", "C0"), ("sbm", "C1"), ("ws", "C2")):
    for dk, ls in (("bernoulli", "-"), ("cluster", "--")):
        for e, mk in (("lin_frac", "o"), ("two_hop", "s")):
            g = th[(th.gkind == gk) & (th.dkind == dk) & (th.est == e)].sort_values("omega")
            if e == "two_hop" and dk == "cluster":
                continue
            ax[1].plot(g.omega, g.rel_bias, ls, c=col, marker=mk, ms=3, lw=1, label=f"{gk}/{dk[:4]}/{e}" if gk == "er" else None)
ax[1].set_xlabel("two-hop weight $\\omega$"); ax[1].set_ylabel("relative bias"); ax[1].legend(fontsize=5)
for gk, col in (("er", "C0"), ("ba", "C1"), ("sbm", "C2")):
    for s, ls in ((0, "-"), (4, "--")):
        g = ed[(ed.gkind == gk) & (ed.s == s) & (ed.est == "lin_frac")].sort_values("edge_drop")
        ax[2].plot(g.edge_drop, g.rel_bias, ls, c=col, marker="o", ms=3, lw=1, label=f"{gk}, s={s}")
ax[2].set_xlabel("fraction $q$ of true edges missing"); ax[2].set_ylabel("relative bias (lin_frac)"); ax[2].legend(fontsize=6)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_mismatch.pdf"))
