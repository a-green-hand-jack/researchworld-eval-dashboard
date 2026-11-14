"""Writes paper/numbers.tex: every number quoted in the paper text is a macro computed here from results/.
usage: python3 paper/scripts/make_numbers.py   (run from the repository root)"""
import os, numpy as np, pandas as pd
R = "results"; OUT = "paper/numbers.tex"
s = pd.read_csv(f"{R}/summary.csv")
rows = []
def put(name, val, fmt="{:.2f}"):
    rows.append("\\newcommand{\\%s}{%s}" % (name, fmt.format(val)))
def g(exp, tag, est, col):
    r = s[(s.experiment == exp) & (s.tag == tag) & (s.est_name == est)]
    assert len(r) == 1, (exp, tag, est, len(r))
    return float(r[col].iloc[0])
# E1 size
for n in (500, 2000, 8000):
    put(f"EoneOLS{ {500:'A',2000:'B',8000:'C'}[n] }", g("E1_size", f"n={n}", "ols_f", "rel_rmse"))
    put(f"EoneDM{ {500:'A',2000:'B',8000:'C'}[n] }", g("E1_size", f"n={n}", "dm", "rel_rmse"))
ns = np.array([500, 1000, 2000, 4000, 8000]); sd = np.array([g("E1_size", f"n={n}", "ols_f", "sd") for n in ns])
put("EoneSlope", np.polyfit(np.log(ns), np.log(sd), 1)[0])
put("EoneBiasMax", max(abs(g("E1_size", f"n={n}", "ols_f", "rel_bias")) for n in ns), "{:.3f}")
put("EoneDMbias", g("E1_size", "n=8000", "dm", "rel_bias"))
put("EoneTwohopA", g("E1_size", "n=8000", "ols_f2", "rel_rmse"))
# E3 gamma
for lab, t in (("Z", "gamma=0"), ("H", "gamma=0.5"), ("O", "gamma=1"), ("F", "gamma=4")):
    put(f"EthreeOLS{lab}", g("E3_gamma", t, "ols_f", "rel_rmse")); put(f"EthreeDM{lab}", g("E3_gamma", t, "dm", "rel_rmse"))
put("EthreeCntZ", g("E3_gamma", "gamma=0", "ols_cnt", "rel_bias"))
# E2 degree
for t, lab in (("sbm_d=5", "SbmLo"), ("sbm_d=160", "SbmHi"), ("er_d=5", "ErLo"), ("er_d=160", "ErHi")):
    put(f"Etwo{lab}", g("E2_degree", t, "ols_f", "rel_rmse"))
# E9 noise
put("EnineCzero", g("E9_noise", "sigE1_sigC0", "ols_f", "rel_rmse")); put("EnineCthree", g("E9_noise", "sigE1_sigC3", "ols_f", "rel_rmse"))
# E10 coverage
c = s[(s.experiment == "E10_coverage") & (s.est_name == "ols_f")]
cl = c[c.tag.str.endswith("_cl")]; hc = c[c.tag.str.endswith("_hc")]
put("CovClMin", cl.cover.min()); put("CovClMax", cl.cover.max()); put("CovHcMin", hc.cover.min())
put("CovClSbmN", g("E10_coverage", "sbm0.05_n4000_cl", "ols_f", "cover")); put("CovClSbmSmall", g("E10_coverage", "sbm0.05_n1000_cl", "ols_f", "cover"))
put("CovHcSbmMix", g("E10_coverage", "sbm0.3_n1000_hc", "ols_f", "cover"))
# E7 model class
for t, lab in (("lin_frac_d10", "LinA"), ("lin_frac_d40", "LinB"), ("thresh_d10", "ThrA"), ("thresh_d40", "ThrB")):
    for e, el in (("ols_f", "Ols"), ("gbm", "Gbm"), ("ridge_rich", "Ridge"), ("ols_poly3", "Cub")):
        put(f"Eseven{lab}{el}", g("E7_model", t, e, "rel_rmse"))
    for e, el in (("ols_f", "Ols"), ("gbm", "Gbm")):
        put(f"EsevenBias{lab}{el}", g("E7_model", t, e, "rel_bias"), "{:+.2f}")
# E6 spec
put("EsixCntEr", g("E6_spec", "er_d60_lin_count", "ols_cnt", "rel_rmse")); put("EsixCntErFrac", g("E6_spec", "er_d60_lin_frac", "ols_cnt", "rel_rmse"))
put("EsixCntAdjEr", g("E6_spec", "er_d60_lin_count", "ols_cnt_adj", "rel_rmse")); put("EsixCntAdjErFrac", g("E6_spec", "er_d60_lin_frac", "ols_cnt_adj", "rel_rmse"))
put("EsixTwohopBias", g("E6_spec", "sbm_d20_lin_2hop", "ols_f", "rel_bias"), "{:+.2f}")
put("EsixCntAdjBaBias", g("E6_spec", "ba_d20_lin_frac", "ols_cnt_adj", "rel_bias"), "{:+.2f}")
# MAIN
m = s[s.experiment == "MAIN"].copy(); m[["graph", "mech", "design"]] = m.tag.str.split("|", expand=True)
def med(mech, design, est, col): return float(m[(m.mech == mech) & (m.design == design) & (m.est_name == est)][col].median())
put("MainOneOls", med("M1", "bern0.5", "ols_f", "rel_rmse")); put("MainDM", med("M1", "bern0.5", "dm", "rel_rmse"))
put("MainThreeBernLow", med("M3", "bern0.1", "ols_f", "rel_rmse")); put("MainThreeBernLowBias", med("M3", "bern0.1", "ols_f", "rel_bias"), "{:+.2f}")
put("MainFourBias", med("M4", "bern0.5", "ols_f", "rel_bias"), "{:+.2f}"); put("MainFourTwohopBias", med("M4", "bern0.5", "ols_f2", "rel_bias"), "{:+.2f}")
put("MainEgoOls", g("MAIN", "fb_ego|M1|bern0.5", "ols_f", "rel_rmse")); put("MainStanOls", g("MAIN", "fb_stanford|M1|bern0.5", "ols_f", "rel_rmse"))
h = m[(m.est_name == "hajek")]
put("HajekUndefBernHalf", h[h.design == "bern0.5"].frac_undefined.median(), "{:.2f}"); put("HajekUndefBernLow", h[h.design == "bern0.1"].frac_undefined.median(), "{:.2f}")
put("NMainCells", m.tag.nunique(), "{:d}") if False else rows.append("\\newcommand{\\NMainCells}{%d}" % m.tag.nunique())
# H7
h7 = pd.read_csv(f"{R}/h7.csv"); q = h7[h7.stat == "ext"].set_index(["mech", "design"])
put("HsevenSat", q.loc[("sat", "bernoulli"), "r2"]); put("HsevenPooled", q.loc[("ALL_misspecified", "all"), "r2"])
put("HsevenThresh", q.loc[("thresh", "bernoulli"), "r2"]); put("HsevenPow", q.loc[("pow", "bernoulli"), "r2"]); put("HsevenHet", q.loc[("het", "bernoulli"), "r2"])
# theory
tv = pd.read_csv(f"{R}/theory_check_var.csv"); tb = pd.read_csv(f"{R}/theory_check_bias.csv")
put("TheoryVarMed", tv.ratio.median(), "{:.3f}"); put("TheoryVarLo", tv.ratio.quantile(.25), "{:.3f}"); put("TheoryVarHi", tv.ratio.quantile(.75), "{:.3f}")
rows.append("\\newcommand{\\TheoryVarN}{%d}" % len(tv)); rows.append("\\newcommand{\\TheoryBiasN}{%d}" % len(tb))
put("TheoryBiasCorr", np.corrcoef(tb.emp_pop_bias, tb.th_pop_bias)[0, 1], "{:.5f}"); put("TheoryBiasMaxDiff", (tb.emp_pop_bias - tb.th_pop_bias).abs().max(), "{:.3f}")
# E11 graph error
put("EelevenSbmBias", g("E11_grapherr", "err0.5|sbm|gamma1.0", "ols_f", "rel_bias"), "{:+.2f}"); put("EelevenSbmGOne", g("E11_grapherr", "err0.5|sbm|gamma1.0", "ols_f", "rel_rmse"))
put("EelevenWeakOls", g("E11_grapherr", "err0.0|sbm|gamma0.25", "ols_f", "rel_rmse")); put("EelevenWeakDM", g("E11_grapherr", "err0.0|sbm|gamma0.25", "dm", "rel_rmse"))
# E4 population bias
d4 = pd.read_csv(f"{R}/diagnostics.csv"); d4 = d4[(d4.experiment == "E4_curv") & (d4.estimator == "ols_f")]

# --- additions: inference trends, graph error, H7 by design, main-grid per-graph, E5, E4 ---
for k, tg in (("HcSbmLoA", "sbm0.05_n1000_hc"), ("HcSbmLoB", "sbm0.05_n4000_hc"), ("HcSbmMixB", "sbm0.3_n4000_hc"), ("ClBaA", "ba_n1000_cl"), ("ClBaB", "ba_n4000_cl"), ("ClSbmMixA", "sbm0.3_n1000_cl"), ("ClSbmMixB", "sbm0.3_n4000_cl")):
    put("Cov" + k, g("E10_coverage", tg, "ols_f", "cover"))
put("EelevenSbmZero", g("E11_grapherr", "err0.0|sbm|gamma1.0", "ols_f", "rel_rmse")); put("EelevenSbmGOneDM", g("E11_grapherr", "err0.5|sbm|gamma1.0", "dm", "rel_rmse"))
put("EelevenEgoBias", g("E11_grapherr", "err0.5|fb_ego|gamma1.0", "ols_f", "rel_bias"), "{:+.2f}")
put("EelevenEgoGOne", g("E11_grapherr", "err0.5|fb_ego|gamma1.0", "ols_f", "rel_rmse")); put("EelevenEgoZero", g("E11_grapherr", "err0.0|fb_ego|gamma1.0", "ols_f", "rel_rmse"))
for mech, nm in (("sat", "Sat"), ("lin_2hop", "Twohop"), ("het", "Het")):
    put(f"HsevenCl{nm}", q.loc[(mech, "cluster"), "r2"]); 
put("HsevenBernTwohop", q.loc[("lin_2hop", "bernoulli"), "r2"])
for gr, nm in (("er", "Er"), ("ba", "Ba"), ("sbm", "Sbm"), ("ws", "Ws")):
    put(f"MainOls{nm}", g("MAIN", f"{gr}|M1|bern0.5", "ols_f", "rel_rmse"))
for gr, nm in (("sbm", "Sbm"), ("fb_ego", "Ego"), ("fb_stanford", "Stan")):
    put(f"MainTwohopOne{nm}", g("MAIN", f"{gr}|M1|bern0.5", "ols_f2", "rel_rmse"))
for d, nm in (("bern0.5", "BernHalf"), ("cluster0.5", "Cluster")):
    put(f"MainDMmed{nm}", med("M1", d, "dm", "rel_rmse"))
for mech, nm in (("M1", "One"), ("M3", "Three"), ("M4", "Four"), ("M5", "Five")):
    put(f"MainDMCl{nm}", med(mech, "cluster0.5", "dm", "rel_rmse")); put(f"MainOlsCl{nm}", med(mech, "cluster0.5", "ols_f", "rel_rmse"))
put("MainFourBiasCl", med("M4", "cluster0.5", "ols_f", "rel_bias"), "{:+.2f}")
e5 = s[(s.experiment == "E5_graphs") & (s.est_name == "ols_f")]; e5d = s[(s.experiment == "E5_graphs") & (s.est_name == "dm")]
bet = e5[e5.rel_rmse < 0.5]
put("EfiveBetterN", len(bet), "{:d}"); put("EfiveLo", bet.rel_rmse.min()); put("EfiveHi", bet.rel_rmse.max()); put("EfiveEgo", g("E5_graphs", "fb_ego", "ols_f", "rel_rmse"))
put("EfiveEr", g("E5_graphs", "er_", "ols_f", "rel_rmse")); put("EfiveSbmLo", g("E5_graphs", "sbm_0.02", "ols_f", "rel_rmse")); put("EfiveSbmMid", g("E5_graphs", "sbm_0.4", "ols_f", "rel_rmse"))
sat = s[(s.experiment == "E3_gamma") & (s.est_name == "ols_f")]
put("EthreeSdLo", sat.sd.min()); put("EthreeSdHi", sat.sd.max())

for k, tg in (("PowLo", "powq0.5_d10_p0.1"), ("PowHi", "powq0.5_d10_p0.9"), ("QuadLo", "powq2.0_d10_p0.1"), ("QuadMid", "powq2.0_d10_p0.5"), ("QuadHi", "powq2.0_d10_p0.9"),
              ("ThrLoDten", "threshsteep10.0_thr0.5_d10_p0.1"), ("ThrMidDten", "threshsteep10.0_thr0.5_d10_p0.5"), ("ThrHiDten", "threshsteep10.0_thr0.5_d10_p0.9"), ("ThrMidDhund", "threshsteep10.0_thr0.5_d160_p0.5")):
    v = g("E4_curv", tg, "ols_f", "rel_bias"); put("Efour" + k, 0.0 if abs(v) < 0.005 else v, "{:+.2f}" if abs(v) >= 0.005 else "{:.2f}")
# real graphs over 8 independent baseline draws (MAIN_realdraws)
rd = pd.read_csv(f"{R}/realdraws_summary.csv")
def rdv(gr, mech, des, pp, est, col):
    r = rd[(rd.graph == gr) & (rd.mechanism == mech) & (rd.design == des) & (rd.p == pp) & (rd.estimator == est)]
    assert len(r) == 1, (gr, mech, des, pp, est)
    return float(r[col].iloc[0])
for gr, nm in (("fb_ego", "Ego"), ("fb_stanford", "Stan")):
    put(f"Rd{nm}OneMean", rdv(gr, "M1", "bernoulli", 0.5, "ols_f", "mean")); put(f"Rd{nm}OneLo", rdv(gr, "M1", "bernoulli", 0.5, "ols_f", "min"))
    put(f"Rd{nm}OneHi", rdv(gr, "M1", "bernoulli", 0.5, "ols_f", "max")); put(f"Rd{nm}OneSd", rdv(gr, "M1", "bernoulli", 0.5, "ols_f", "sd"))
    put(f"Rd{nm}OneDM", rdv(gr, "M1", "bernoulli", 0.5, "dm", "mean"))
    for pp, lab in ((0.5, "Half"), (0.1, "Tenth")):
        w = rd[(rd.graph == gr) & (rd.design == "bernoulli") & (rd.p == pp) & (rd.estimator == "ols_f")].ols_beats_dm.sum()
        put(f"Rd{nm}Wins{lab}", w, "{:.0f}")
    put(f"Rd{nm}WinsCl", rd[(rd.graph == gr) & (rd.design == "cluster") & (rd.estimator == "ols_f")].ols_beats_dm.sum(), "{:.0f}")
    for mech, ml in (("M3", "Three"), ("M5", "Five")):
        put(f"Rd{nm}{ml}Half", rdv(gr, mech, "bernoulli", 0.5, "ols_f", "ols_beats_dm"), "{:.0f}")
open(OUT, "w").write("% generated by paper/scripts/make_numbers.py from results/; do not edit\n" + "\n".join(rows) + "\n")
print(len(rows), "macros")
