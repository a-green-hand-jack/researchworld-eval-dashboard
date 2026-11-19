"""Fig. 3: multi-hop (linear-in-means) interference -- from E3.csv (tag multihop)."""
import numpy as np, pandas as pd
from ac import *
from matplotlib.ticker import NullFormatter

df = load("E3")
df = df[df.tag == "multihop"].copy()
df["gl"] = gkey(df)
df["fam"] = df.gl + "/" + df.design_type.map({"bern": "Bernoulli", "cluster": "cluster"})
fams = [("ER/Bernoulli", C["blue"], "o", "-"), ("SBM/Bernoulli", C["orange"], "s", "-"), ("Stanford3/Bernoulli", C["red"], "P", "-"), ("ego-Facebook/Bernoulli", C["yellow"], "X", "-"),
        ("SBM/cluster", C["orange"], "s", "--"), ("Stanford3/cluster", C["red"], "P", "--"), ("ego-Facebook/cluster", C["yellow"], "X", "--")]
import json
PSI = json.load(open(f"{RES}/psi.json"))
def b_exact(lam, name):
    p = {int(k): v for k, v in PSI[name]["psi"].items()}
    K = max(p)
    tot = -sum(lam ** k * (1 - p[k]) for k in range(2, K + 1))
    tot -= lam ** (K + 1) / (1 - lam) * (1 - p[K])   # tail: psi_k := psi_K for k > K
    return tot
lam = np.linspace(0, 0.8, 50)
fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.15))
for k, (est, ttl) in enumerate([("ols_s", "(a) 1-hop regression: bias"), ("ols_s2", "(b) + 2-hop covariate: bias")]):
    a = ax[k]
    for f, col, mk, ls in fams:
        s = df[(df.fam == f) & (df.estimator == est)]
        g = agg_worlds(s, ["mech_lam"]).sort_values("mech_lam")
        a.errorbar(g.mech_lam, g.bias, yerr=[g.bias - g.bias_min, g.bias_max - g.bias], color=col, marker=mk, ls=ls, mfc=col if ls == "-" else "white", capsize=1.2, elinewidth=.5, ms=3.8, label=f)
    if est == "ols_s":
        a.plot(lam, -lam ** 2 / (1 - lam), color=INK, lw=0.9, ls=":", label=r"$-\lambda^2/(1-\lambda)$")
        for nm, col in [("egofb", C["yellow"]), ("stanford3", C["red"])]:
            a.plot(lam, [b_exact(l, nm) for l in lam], color=col, lw=0.8, ls="-.", alpha=0.9)
    a.set_xlabel(r"spillover strength $\lambda$"); a.set_title(ttl)
    a.axhline(0, color=INK2, lw=0.5)
ax[0].set_ylabel("bias of GATE estimate")
ax[0].legend(frameon=False, fontsize=5.6, loc="lower left", handlelength=1.8)
a = ax[2]
for f, col, mk, ls, lab in [("Stanford3/Bernoulli", C["red"], "P", "-", "Stanford3 Bern."), ("Stanford3/cluster", C["red"], "P", "--", "Stanford3 cluster")]:
    for est, a_s, lw in [("ols_s", 1, 1.4), ("ols_s2", 0.55, 1.4), ("dm", 0.25, 1.4)]:
        s = df[(df.fam == f) & (df.estimator == est)]
        g = agg_worlds(s, ["mech_lam"]).sort_values("mech_lam")
        a.plot(g.mech_lam, g.rmse, color=col, alpha=a_s, ls=ls, marker=mk, ms=3.5, mfc=col if ls == "-" else "white")
a.set_yscale("log"); a.set_xlabel(r"spillover strength $\lambda$"); a.set_ylabel("RMSE"); a.set_title("(c) Stanford3 RMSE")
pass
a.set_ylim(0.01, 6)
fig.tight_layout(w_pad=0.8)
save(fig, "fig_multihop")

# table: bias at lambda=0.6 and predicted
t = df[(df.mech_lam.isin([0.4, 0.6])) & (df.estimator.isin(["ols_s", "ols_s2", "dm"]))]
t = agg_worlds(t, ["fam", "mech_lam", "estimator"])
t["pred_ols_s_bias"] = -t.mech_lam ** 2 / (1 - t.mech_lam)
print(t[["fam", "mech_lam", "estimator", "truth", "bias", "bias_sem", "pred_ols_s_bias", "rmse"]].to_string())
t.to_csv(f"{TAB}/multihop.csv", index=False)

# exact-formula table (Bernoulli designs)
rows = []
for nm, gl in [("er", "ER"), ("egofb", "ego-Facebook"), ("stanford3", "Stanford3")]:
    for l in [0.2, 0.4, 0.6, 0.8]:
        s_ = df[(df.fam == gl + "/Bernoulli") & (df.estimator == "ols_s") & (df.mech_lam == l)]
        rows.append(dict(graph=gl, lam=l, sim_bias=s_.bias.mean(), sim_sem=s_.bias.std(ddof=1) / np.sqrt(len(s_)), exact=b_exact(l, nm), tree=-l ** 2 / (1 - l)))
T = pd.DataFrame(rows); print(T.round(3).to_string()); T.to_csv(f"{TAB}/multihop_exact.csv", index=False)
