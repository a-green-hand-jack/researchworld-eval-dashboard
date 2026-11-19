"""Recomputes the numbers quoted in the paper's text (Section 6, Discussion, Appendix) from results/*.csv and prints them
with the claim labels used in paper/sec_results_*.tex.  Compare against the text."""
import json, numpy as np, pandas as pd
from ac import *
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
def P(k, v): print(f"[{k}] {v}")

E1 = load("E1"); E1["gl"] = gkey(E1)
E2 = load("E2"); E2["gl"] = gkey(E2)
E3 = load("E3"); E3["gl"] = gkey(E3)
E4 = load("E4"); E4["gl"] = gkey(E4)
E5 = load("E5"); E5["gl"] = gkey(E5)
E7 = load("E7"); E7["gl"] = gkey(E7)
m = lambda d, **kw: d[np.logical_and.reduce([d[k] == v for k, v in kw.items()])]

# ---- 6.1
h = E1[(E1.estimator == "hajek") & (E1.tag == "er_n")]
P("hajek er_n fail by n", h.groupby("graph_n").fail.mean().round(3).to_dict())
P("hajek er_n rmse by n (fail<.5)", h[h.fail < .5].groupby("graph_n").rmse.mean().round(3).to_dict())
P("hajek er_d fail by d", E1[(E1.estimator == "hajek") & (E1.tag == "er_d")].groupby("graph_d").fail.mean().round(3).to_dict())
P("DiM rmse er_n", E1[(E1.estimator == "dm") & (E1.tag == "er_n")].groupby("graph_n").rmse.mean().round(3).to_dict())
for tag, key in [("ws_d", "graph_d"), ("sbm_d", "graph_d"), ("ba_m", "graph_m")]:
    s = E1[(E1.estimator == "ols_s") & (E1.tag == tag)]
    b = s[s.design_type == "bern"].groupby(key).rmse.mean(); c = s[s.design_type == "cluster"].groupby(key).rmse.mean()
    P(f"{tag} bern/cluster rmse ratio", (b / c).round(2).to_dict())
    P(f"{tag} cut", s[s.design_type == "cluster"].groupby(key).cut_frac.mean().round(2).to_dict())
    P(f"{tag} bern rmse", b.round(3).to_dict()); P(f"{tag} cluster rmse", c.round(3).to_dict())
# ---- 6.2 (E2)
E2["shape"] = E2.apply(lambda r: f"k={r.mech_k:g}" if r.mech_shape == "pow" else "thr", axis=1)
for gl in ["ER", "ego-Facebook", "Stanford3"]:
    for des in ["bern", "cluster"]:
        s = E2[(E2.tag == "shape") & (E2.gl == gl) & (E2.design_type == des)]
        t = s.pivot_table(index="shape", columns="estimator", values=["bias", "rmse"], aggfunc="mean")
        P(f"E2 {gl} {des}", "\n" + t[[("bias", "ols_s"), ("rmse", "ols_s"), ("bias", "ols_s_quad"), ("bias", "ols_s_cub"), ("rmse", "ols_s_cub")]].round(3).to_string())
# ---- 6.3 multi-hop
mh = E3[E3.tag == "multihop"].copy(); mh["fam"] = mh.gl + "/" + mh.design_type
sd = mh[mh.mech_lam == 0.4].pivot_table(index="fam", columns="estimator", values="sd", aggfunc="mean")
P("multihop sd ratio s2/s (lam=.4)", (sd.ols_s2 / sd.ols_s).round(2).to_dict())
lev = mh[(mh.mech_lam == 0.4)].pivot_table(index="fam", columns="estimator", values="lev", aggfunc="mean")
P("multihop lev s, s2 (lam=.4)", lev[["ols_s", "ols_s2"]].round(1).to_dict())
for lam in [0.4, 0.6]:
    r = mh[mh.mech_lam == lam].pivot_table(index="fam", columns="estimator", values="rmse", aggfunc="mean")
    P(f"multihop lam={lam}: s2 better than s in", f"{(r.ols_s2 < r.ols_s).sum()} of {len(r)}: {list(r.index[(r.ols_s2 < r.ols_s)])}")
b6 = mh[(mh.mech_lam == 0.6) & (mh.estimator == "ols_s")].groupby("fam").bias.mean().round(3)
P("multihop lam=.6 ols_s bias", b6.to_dict())
P("multihop lam=.8 ER bias/truth", (mh[(mh.fam == "ER/bern") & (mh.mech_lam == .8) & (mh.estimator == "ols_s")].bias.mean() / mh[(mh.fam == "ER/bern") & (mh.mech_lam == .8) & (mh.estimator == "ols_s")].truth.mean()))
# heterogeneity / count
gh = E3[E3.tag == "gamhet"].copy(); gh["gh"] = gh.mech_gam_het
t = gh.pivot_table(index=["gl", "graph_m", "design_type", "gh"], columns="estimator", values=["bias", "rmse"], aggfunc="mean")
P("gamhet", "\n" + t.round(3).to_string())
ct = E3[E3.tag == "count"]
t = ct.pivot_table(index=["gl", "graph_m", "design_type"], columns="estimator", values=["bias", "rmse"], aggfunc="mean")
P("count mech", "\n" + t.round(3).to_string())
# ---- 6.4 design
q = E5[(E5.estimator == "ols_s")]
for tg in ["K_pow4", "K_mh06"]:
    s = q[q.tag == tg]; print(tg); print(agg_worlds(s, ["gl", "design_K"])[["gl", "design_K", "n_clusters", "bias", "rmse"]].round(3).to_string())
s = q[(q.tag == "p_pow05") & (q.design_type == "bern")]
P("p_pow05 bern bias SBM p=.05", s[(s.gl == "SBM") & (s.design_p == .05)].bias.mean())
dmk = E5[(E5.tag == "K_lin") & (E5.estimator == "dm") & (E5.design_K == 30)]
P("dm cluster K=30?", agg_worlds(dmk, ["gl"])[["gl", "bias", "truth", "n_clusters"]])
E1r = E1[(E1.tag == "real") & (E1.estimator == "dm") & (E1.design_type == "cluster") & (E1.design_K == 30)]
P("E1 dm cluster K=30", E1r.groupby("gl")[["bias", "truth"]].mean())
# ---- 6.5
c4 = E4[E4.tag == "cross"]
g0 = c4[(c4.mech_gamma == 0)].pivot_table(index=["graph_d", "graph_n"], columns="estimator", values="rmse", aggfunc="mean")
P("gamma=0 rmse dm/ols", g0.round(3).to_string())
r4 = E4[E4.tag == "cross_real"]
for gl in ["ego-Facebook", "Stanford3"]:
    for des in ["bern", "cluster"]:
        s = r4[(r4.gl == gl) & (r4.design_type == des)].pivot_table(index="mech_gamma", columns="estimator", values="rmse", aggfunc="mean")
        P(f"cross_real {gl} {des} (gamma, rmse)", "\n" + s.round(3).T.to_string())
# ---- E7
o = E7[(E7.estimator == "ols_s")]
t = agg_worlds(o.assign(st=o.gl + "/" + o.design_type), ["st", "obs_noise_drop"])[["st", "obs_noise_drop", "bias", "rmse"]]
P("E7 ols_s", "\n" + t.round(3).to_string())
