"""Asserts that numbers quoted in the paper text equal values recomputed from results/ (run from the repository root:
python3 paper/check_numbers.py). Every check lists the quoted value, the recomputed value and the rounding used."""
import sys
import numpy as np
import pandas as pd

R = "results/"
bad = []


def chk(name, value, quoted, nd=2):
    ok = bool(np.isclose(round(float(value), nd), quoted, atol=10 ** -nd / 2 + 1e-12))
    print(("ok   " if ok else "FAIL ") + f"{name}: quoted {quoted}, computed {float(value):.6g}")
    if not ok:
        bad.append(name)


e1, e2, e4, e5, e10 = [pd.read_csv(f"{R}summary/{e}.csv") for e in ("e1", "e2", "e4", "e5", "e10")]
t = lambda n: pd.read_csv(f"{R}tables/{n}.csv")

# --- H3: bias does not shrink with n (e10)
t4 = t("t4_bias_vs_n")
b = lambda n, p: t4[(t4.n_nom == n) & (t4.o_kind == "concave") & (t4.design == p) & (t4.est_name == "OLS_f")].bias.iloc[0]
chk("H3 bias n=1k p=0.1", b(1000, "bern:0.1"), 2.53)
chk("H3 bias n=20k p=0.1", b(20000, "bern:0.1"), 2.49)
chk("H3 bias n=1k p=0.5", b(1000, "bern:0.5"), -0.57)
chk("H3 bias n=20k p=0.5", b(20000, "bern:0.5"), -0.52)

# --- H4 exponents
t5 = t("t5_scaling_exponents").set_index("estimator")
chk("H4 exp n", t5.loc["OLS_f", "exp_n"], -0.501, 3)
chk("H4 se n", t5.loc["OLS_f", "se_n"], 0.005, 3)
chk("H4 exp d", t5.loc["OLS_f", "exp_d"], 0.495, 3)
chk("H4 se d", t5.loc["OLS_f", "se_d"], 0.006, 3)
chk("H4 OLS_big exp n", t5.loc["OLS_big", "exp_n"], -0.61)
chk("H4 OLS_big exp d", t5.loc["OLS_big", "exp_d"], 1.18)
pd5 = t("t5c_p_dependence")
r = pd5[(pd5.p == 0.05) & (pd5.est_name == "OLS_f")].set_index("gname")["sd_ratio_to_p0.5"]
chk("p-dep SBM", r["SBM"], 2.32); chk("p-dep Stanford3", r["Stanford3"], 2.21); chk("p-dep ego", r.iloc[-1] if "ego-FB" not in r else r["ego-FB"], 1.80)
chk("p-dep predicted", pd5[pd5.p == 0.05]["pred_ratio_to_p0.5"].iloc[0], 2.29)

# --- H2: closed form vs simulation (e9)
th = pd.read_csv(f"{R}summary/theory_vs_sim_e9.csv")
dev = (th.bias - th.pred_exact).abs()
chk("H2 corr", np.corrcoef(th.bias, th.pred_exact)[0, 1], 1.0, 4)
chk("H2 median dev", dev.median(), 0.0012, 4)
chk("H2 max dev", dev.max(), 0.041, 3)
chk("H2 all within 3SE", float((dev <= 3 * th.bias_se).all()), 1.0, 0)
chk("H2 bias min", th.bias.min(), -2.0, 0); chk("H2 bias max", th.bias.max(), 5.0, 0)
chk("H2 curvature max", th.o_curv.max(), 8, 0); chk("H2 curvature min", th.o_curv.min(), 0.5, 1)
ld = (th.bias - th.pred_largedeg).abs()
chk("H2 shortcut median dev", ld.median(), 0.09); chk("H2 shortcut max dev", ld.max(), 3.3, 1)
t2 = t("t2_noiseless_bias")
chk("H1 max|bias| ORACLE (1e-11)", t2[t2.est_name == "ORACLE"].bias.abs().max() * 1e11, 2.4, 1)

# --- C2/H6: DM vs regression
t12 = t("t12_headline_numbers")
ra = t12[t12.claim == "C2"].value
chk("SD ratio min", ra.min(), 5.5, 1); chk("SD ratio max", ra.max(), 18.6, 1)
t1b = t("t1b_dm_vs_regression")
tb = t1b[t1b.design == "bern:0.5"]
chk("DM slope min", tb.dm_bias_slope_per_gamma.min(), -1.000, 3); chk("DM slope max", tb.dm_bias_slope_per_gamma.max(), -0.999, 3)

# --- default scenario table (e2: SBM, Bernoulli(0.5), concave)
x = e2[e2.graph.str.startswith("sbm") & (e2.design == "bern:0.5") & (e2.o_kind == "concave")].set_index("est_name")
chk("tab2 DM rmse", x.loc["DM", "rmse"], 2.00); chk("tab2 OLS_f rmse", x.loc["OLS_f", "rmse"], 0.72)
chk("tab2 ORACLE_D rmse", x.loc["ORACLE_D", "rmse"], 0.59); chk("tab2 HajekKappa rmse", x.loc["HajekKappa", "rmse"], 1.21)
chk("tab2 OLS_cnt bias", x.loc["OLS_cnt", "bias"], 1.0, 1); chk("tab2 OLS_cnt rmse", x.loc["OLS_cnt", "rmse"], 1.05)
chk("tab2 OLS_cubic bias", x.loc["OLS_cubic", "bias"], -0.05); chk("tab2 OLS_cubic rmse", x.loc["OLS_cubic", "rmse"], 1.33)
chk("tab2 OLS_big rmse", x.loc["OLS_big", "rmse"], 3.01); chk("tab2 OLS_big sd", x.loc["OLS_big", "sd"], 2.95); chk("tab2 OLS_f sd", x.loc["OLS_f", "sd"], 0.49)
chk("tab2 DM relative", x.loc["DM", "rmse"] / 3, 0.67); chk("tab2 OLS_f relative", x.loc["OLS_f", "rmse"] / 3, 0.24); chk("tab2 oracle relative", x.loc["ORACLE_D", "rmse"] / 3, 0.20)
y = e2[e2.graph.str.startswith("sbm") & (e2.design == "bern:0.1") & (e2.o_kind == "concave")].set_index("est_name")
chk("p=0.1 OLS_f rel rmse", y.loc["OLS_f", "rel_rmse"], 0.86); chk("p=0.1 quad rel rmse", y.loc["OLS_quad", "rel_rmse"], 3.8, 1); chk("p=0.1 big rel rmse", y.loc["OLS_big", "rel_rmse"], 27, 0)

# --- sigmoid sign flip
sg = e2[e2.graph.str.startswith("sbm") & (e2.o_kind == "sigmoid") & (e2.est_name == "OLS_f")].set_index("design")
chk("sigmoid bias p=.5", sg.loc["bern:0.5", "bias"], 2.0, 1); chk("sigmoid bias p=.1", sg.loc["bern:0.1", "bias"], -1.5, 1)

# --- shape ranking (OLS_f, e2)
o = e2[e2.est_name == "OLS_f"].copy()
o["rb"] = o.bias.abs() / o.gate; o["bshare"] = o.bias ** 2 / (o.bias ** 2 + o.sd ** 2)
for k, med, sh in (("linear", 0.01, 0), ("concave", 0.14, 33), ("convex", 0.14, 38), ("sigmoid", 0.34, 67)):
    g = o[o.o_kind == k]
    chk(f"median rel bias {k}", g.rb.median(), med); chk(f"bias share>0.5 {k} (%)", 100 * (g.bshare > 0.5).mean(), sh, 0)
# graph family, linear, Bernoulli(0.5)
g = o[(o.o_kind == "linear") & (o.design == "bern:0.5")].set_index("graph").rmse
for nm, key, v in (("BA", "ba:5000,10", 0.26), ("Stanford3", "stanford3", 0.26), ("ER", "er:5000,20", 0.27), ("ego", "ego", 0.92)):
    chk(f"H8 rmse {nm}", g[key], v)

# --- clusters (e4)
e4 = e4[e4.tag.str.contains("_res")]
c = e4[(e4.est_name == "OLS_f")].set_index(["graph", "design", "o_kind"]).rmse
S = "sbm:5000,50,20,0.8"
chk("cl SBM concave louv", c[(S, "louv:1.0,0.5", "concave")], 0.37); chk("cl SBM concave rand", c[(S, "rand:1.0,0.5", "concave")], 0.76)
chk("cl Stanford3 linear louv", c[("stanford3", "louv:1.0,0.5", "linear")], 0.54); chk("cl Stanford3 linear rand", c[("stanford3", "rand:1.0,0.5", "linear")], 0.26)
chk("cl ego linear louv", c[("ego", "louv:1.0,0.5", "linear")], 0.43); chk("cl ego linear rand", c[("ego", "rand:1.0,0.5", "linear")], 0.98)
bb = e4[(e4.est_name == "OLS_f")].set_index(["graph", "design", "o_kind"]).bias
chk("cl SBM concave bias louv", bb[(S, "louv:1.0,0.5", "concave")], -0.07); chk("cl SBM concave bias rand", bb[(S, "rand:1.0,0.5", "concave")], -0.48)

# --- planted blocks (t6b, concave)
pb = t("t6b_planted_blocks"); pb = pb[pb.o_kind == "concave"].set_index(["tag", "design", "est_name"])
chk("planted DM block bias f=.5", pb.loc[("sbm_f0.5", "block:0.5", "DM"), "bias"], -1.21); chk("planted DM block bias f=.97", pb.loc[("sbm_f0.97", "block:0.5", "DM"), "bias"], -0.07)
chk("planted OLS_f block rmse f=.5", pb.loc[("sbm_f0.5", "block:0.5", "OLS_f"), "rmse"], 0.50); chk("planted OLS_f block rmse f=.97", pb.loc[("sbm_f0.97", "block:0.5", "OLS_f"), "rmse"], 0.29)
chk("planted OLS_f bern rmse f=.5", pb.loc[("sbm_f0.5", "bern:0.5", "OLS_f"), "rmse"], 0.60); chk("planted OLS_f bern rmse f=.97", pb.loc[("sbm_f0.97", "bern:0.5", "OLS_f"), "rmse"], 0.82)

# --- noise / baseline (t10)
n10 = t("t10_noise_baseline")
n10 = n10[(n10.gname == "SBM") & (n10.design == "bern:0.5") & (n10.est_name == "OLS_f") & (n10.o_sigma == 1.0)].set_index("o_alpha_graph").sd
chk("smooth baseline SD a=0", n10[0.0], 0.16); chk("a=1", n10[1.0], 0.49); chk("a=3", n10[3.0], 1.37)

# --- coverage (t8; Bernoulli(0.5), analysis resolution 1.0, mean over graphs with a value)
cv = t("t8_coverage"); cv = cv[(cv.design == "bern:0.5") & cv.tag.str.endswith("acl1.0")]
m = lambda kind, est: cv[(cv.o_kind == kind) & (cv.est_name == est)][["cov_hc", "cov_cl", "cov_hac1", "cov_hac2"]].mean()
for (kind, est), vals in {("linear", "OLS_f"): (0.66, 0.86, 0.79, 0.91), ("concave", "OLS_f"): (0.43, 0.65, 0.56, 0.70), ("concave", "ORACLE_D"): (0.68, 0.86, 0.81, 0.92)}.items():
    for col, v in zip(("cov_hc", "cov_cl", "cov_hac1", "cov_hac2"), vals):
        chk(f"coverage {kind} {est} {col}", m(kind, est)[col], v)
lin = cv[(cv.o_kind == "linear") & (cv.est_name == "OLS_f")].set_index("gname")
chk("HC0 linear min", lin.cov_hc.min(), 0.32); chk("HC0 linear max", lin.cov_hc.max(), 0.89)
chk("CL linear BA", lin.loc["BA", "cov_cl"], 0.75); chk("HAC2 SBM", lin.loc["SBM", "cov_hac2"], 0.93); chk("HAC2 ER", lin.loc["ER", "cov_hac2"], 0.95)

# --- mechanisms (t9, Bernoulli(0.5))
t9 = t("t9_mechanisms"); t9 = t9[t9.design == "bern:0.5"]
rb = t9[t9.est_name == "OLS_f"].assign(rb=lambda d: d.bias / d.gate).groupby("mech").rb.mean()
chk("count rel bias", rb["count"], -0.22); chk("hetero rel bias", rb["hetero"], 0.0); chk("twohop rel bias", rb["twohop"], -0.29); chk("rho .9 rel bias", rb["prop(rho=0.9)"], -0.74)
pr = t9[t9.mech == "prop(rho=0.9)"].groupby("est_name").rmse.mean()
for k, v in (("OLS_f", 7.8), ("DM", 8.9), ("GBM", 8.7), ("OLS_big", 9.8)):
    chk("rho .9 rmse " + k, pr[k], v, 1)
pr3 = t9[t9.mech == "prop(rho=0.3)"].groupby("est_name").rmse.mean(); chk("rho .3 rmse OLS_f", pr3["OLS_f"], 0.56); chk("rho .3 rmse DM", pr3["DM"], 0.43)
tw = t9[t9.mech == "twohop"].pivot_table(index="gname", columns="est_name", values=["bias", "rmse"])
chk("twohop SBM rmse OLS_f", tw.loc["SBM", ("rmse", "OLS_f")], 1.04); chk("twohop SBM rmse ORACLE_D", tw.loc["SBM", ("rmse", "ORACLE_D")], 2.75)
chk("twohop oracle worse on all", float((tw["rmse"]["ORACLE_D"] > tw["rmse"]["OLS_f"]).all()), 1.0, 0)
chk("twohop bias WS", tw.loc["WS", ("bias", "OLS_f")], -0.4, 1); chk("twohop bias max", tw["bias"]["OLS_f"].min(), -1.0, 1)

# --- factor ranking (t11)
t11 = t("t11_factor_ranking").set_index("factor").ratio_max_min
for k, v in zip(t11.index, (4.6, 4.5, 3.9, 3.6, 3.2, 2.0, 1.5, 1.1)):
    chk("t11 " + k, t11[k], v, 1)

# --- post-freeze e11 (H3g) and e12 (H6)
t14 = t("t14_gamma_dependence"); o = t14[t14.est_name == "OLS_f"]
chk("e11 slope min", o.slope_per_gamma.min(), -0.71); chk("e11 slope max", o.slope_per_gamma.max(), 1.26)
sb = o[o.graph.str.startswith("sbm")].set_index(["kind", "design"]).slope_per_gamma
chk("e11 SBM concave p.5", sb[("concave", "bern:0.5")], -0.25); chk("e11 SBM concave p.1", sb[("concave", "bern:0.1")], 1.26)
chk("e11 slope se min", o.slope_se.min(), 0.005, 3); chk("e11 slope se max", o.slope_se.max(), 0.037, 3)
d = t14[t14.est_name == "DM"].slope_per_gamma; chk("e11 DM slope", d.mean(), -1.00)
chk("e11 ORACLE_D max |bias4|", t14[t14.est_name == "ORACLE_D"].bias_g4.abs().max(), 0.17)
q = t14[(t14.est_name == "OLS_quad") & (t14.design == "bern:0.1")]
chk("e11 quad intercept min", q.intercept.min(), -9.86); chk("e11 quad stanford", q[q.graph == "stanford3"].intercept.mean(), -1.9, 1)
hp = pd.read_csv(f"{R}hypotheses_postfreeze.csv").set_index("hypothesis")
for k, v in (("H3g", "14/16"), ("H6c", "31/43"), ("H6d", "44/65")):
    ok = hp.loc[k, "statistic"].startswith(v); print(("ok   " if ok else "FAIL ") + f"{k} statistic {hp.loc[k, 'statistic']}"); ok or bad.append(k)
t15 = t("t15_hajek"); b5 = t15[(t15.design == "bern:0.5") & (t15.n_rep >= 200)]
m = lambda e, k: b5[(b5.est_name == e) & (b5.mech == k)].bias.mean()
chk("e12 full twohop", m("HajekFull", "twohop"), -0.88); chk("e12 full prop", m("HajekFull", "prop"), -0.65)
chk("e12 kappa linear", m("HajekKappa", "shape_linear"), -0.57); chk("e12 kappa step1", m("HajekKappa", "step_k1.0"), -1.38)
chk("e12 kappa sigmoid", m("HajekKappa", "shape_sigmoid"), -0.13); chk("e12 full linear", m("HajekFull", "shape_linear"), 0.03)
chk("e12 full sigmoid", m("HajekFull", "shape_sigmoid"), -0.01)

# --- second freeze: e13-e21 (Sec. 4 and Appendix on post-freeze analyses)
t16 = t("t16_second_seed"); h5 = t16[t16.check == "H5"].set_index(["graph", "seed"]).louvain_rmse_greater_than_random
chk("e13 H5 stanford3 seed1", h5[("stanford3", "seed1")], 10, 0); chk("e13 H5 stanford3 seed2", h5[("stanford3", "seed2")], 11, 0)
chk("e13 H5 ego seed2", h5[("ego", "seed2")], 0, 0)
t16b = t16.set_index(["check", "graph", "seed"]); chk("e13 H4 exp n", t16b.loc[("H4", "er", "seed2"), "mean_rmse_louvain"], -0.506, 3)
chk("e13 H2 max dev", t16b.loc[("H2", "sbm/ba/stanford3", "seed2"), "mean_rmse_random"], 0.058, 3)
sc = t("t21b_crossover_scaling").set_index("quantity")
g = sc.loc["gamma* (model)"]; r_ = sc.loc["SD(OLS_f)/SD(DM) at gamma=0"]
chk("gamma* exp n", g.exp_n, -0.49); chk("gamma* exp d", g.exp_d, 1.01); chk("gamma* exp sigma", g.exp_sigma, 0.09); chk("gamma* R2", g.r2, 0.997, 3)
chk("gamma* min", g["min"], 0.11); chk("gamma* max", g["max"], 2.2, 1)
chk("ratio exp n", r_.exp_n, 0.01); chk("ratio exp d", r_.exp_d, 1.0, 1); chk("ratio exp sigma", r_.exp_sigma, -0.31); chk("ratio R2", r_.r2, 0.99)
chk("ratio min", r_["min"], 4.0, 1); chk("ratio max", r_["max"], 26.5, 1); chk("ratio median", r_["median"], 11.1, 1)
hi = t("t20c_headline_intervals").set_index("graph")
for gname, (v, lo, hi_) in {"ba:5000,10": (5.5, 4.8, 6.3), "egofacebook": (18.6, 16.9, 20.7)}.items():
    k = [i for i in hi.index if i.startswith(gname[:3]) and gname[:3] != "ego" or i.startswith("ego")] if False else [i for i in hi.index if i.startswith(gname[:3])]
    r = hi.loc[k[0]]; chk("t20c " + gname + " value", r.value, v, 1); chk("t20c " + gname + " lo", r.lo, lo, 1); chk("t20c " + gname + " hi", r.hi, hi_, 1)
wn = t("t20b_worlds_needed").set_index("W")
chk("worlds W4 rule cover", wn.loc[4, "cover_1.96_rule"], 0.97); chk("worlds W4 world cover", wn.loc[4, "cover_1.96_world"], 0.85)
chk("worlds W4 rep cover", wn.loc[4, "cover_1.96_rep"], 0.96); chk("worlds W4 t world", wn.loc[4, "cover_t_world"], 0.94)
vc = t("t20_variance_components"); o_ = vc[vc.est_name == "OLS_f"]
chk("ICC OLS_f max", o_.icc.max(), 0.035, 3); chk("ICC OLS_f e2 max", o_[o_.exp == "e2"].icc.max(), 0.016, 3)
chk("ICC ORACLE_D max", vc[vc.est_name == "ORACLE_D"].icc.max(), 0.165, 3)
cv = t("t19b_coverage_by_se_type"); cv = cv[cv.exp == "e15"].set_index(["design", "interval", "quantity"]).mean_coverage
for des, iv, g_, e_ in [("Bernoulli(0.5)", "HC0", .54, .66), ("Bernoulli(0.5)", "HAC1", .66, .78), ("Bernoulli(0.5)", "cluster", .75, .86),
                        ("Bernoulli(0.5)", "boot_sd", .76, .87), ("Bernoulli(0.5)", "HAC2", .82, .92), ("Louvain clusters", "HC0", .36, .37),
                        ("Louvain clusters", "HAC1", .56, .57), ("Louvain clusters", "cluster", .80, .82), ("Louvain clusters", "boot_sd", .83, .85),
                        ("Louvain clusters", "HAC2", .73, .74)]:
    chk(f"e15 {des} {iv} gate", cv[(des, iv, "cov_gate")], g_); chk(f"e15 {des} {iv} exp", cv[(des, iv, "cov_exp")], e_)
ht = t("t23_heavy_tail"); h_ = ht[(ht.est_name == "OLS_f") & (ht.kind == "linear") & (ht.gamma == 2)].set_index("graph").sd
for k, v in {"ba": 0.255, "cmba": 0.248, "er": 0.276, "reg": 0.240, "pl2.2": 0.144, "pl2.5": 0.164, "pl3.0": 0.175}.items(): chk("e14 SD " + k, h_[k], v, 3)
hc = ht[(ht.est_name == "OLS_f") & (ht.kind == "concave") & (ht.gamma == 2)].set_index("graph").bias
chk("e14 concave bias ba", hc["ba"], -0.452, 3); chk("e14 concave bias cmba", hc["cmba"], -0.487, 3)
chk("e14 concave bias pl max", hc[["pl2.2", "pl2.5", "pl3.0"]].max(), -0.12, 2); chk("e14 concave bias pl min", hc[["pl2.2", "pl2.5", "pl3.0"]].min(), -0.14, 2)
sp = t("t25_estimator_scope"); sa = sp[(sp.p == "all") & (sp.truth == "all")].set_index("est_name")
chk("e16 zf median", sa.loc["OLS_zf", "median_rmse_ratio"], 1.03); chk("e16 zf better", sa.loc["OLS_zf", "share_better_than_OLS_f"], 0.19)
chk("e16 ridge", sa.loc["RIDGE_big", "median_rmse_ratio"], 6.3, 1); chk("e16 lasso", sa.loc["LASSO_big", "median_rmse_ratio"], 6.5, 1)
chk("e16 big", sa.loc["OLS_big", "median_rmse_ratio"], 6.6, 1)
chk("e16 gbm untuned", sa.loc["GBM", "median_rmse_ratio"], 1.71)
t17b_ = t("t17c_variance_law_components"); ni = t17b_[t17b_.variant == "noise_only"].ratio_dh
chk("e21 d_h ratio min", ni.min(), 0.93, 2); chk("e21 d_h ratio max", ni.max(), 1.04, 2)
tv = t("t17_variance_law").set_index("graph").ratio_obs_over_pred_dh
chk("t17 ER ratio", tv[[i for i in tv.index if i.startswith("er")][0]], 1.29); chk("t17 max ratio", tv.max(), 5.1, 1)
rt = pd.read_csv(f"{R}RUNTIME.csv").set_index("exp").cpu_hours_excl_stalled
chk("runtime e1-e10", rt[[f"e{i}" for i in range(1, 11)]].sum(), 58.5, 1); chk("runtime e11-e21", rt[[f"e{i}" for i in range(11, 22)]].sum(), 8.2, 1)
cells = pd.read_csv(f"{R}COMPLETENESS.csv"); print("completeness columns", list(cells.columns))
print("FAILED:" if bad else "all checks passed", bad)
sys.exit(1 if bad else 0)
