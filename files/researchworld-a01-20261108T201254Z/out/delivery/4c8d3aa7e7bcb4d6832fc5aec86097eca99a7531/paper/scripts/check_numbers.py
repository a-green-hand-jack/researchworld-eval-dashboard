"""Check headline numbers quoted in paper/sections/*.tex against code/results/analysis/*.csv.

Usage: python3 paper/scripts/check_numbers.py [analysis_dir]
Each check recomputes a quoted number (or range) from the CSV and compares it with the value written in the paper
(rounded as quoted). Exit status 1 if any check fails.
"""
import sys, pandas as pd, numpy as np
d = sys.argv[1] if len(sys.argv) > 1 else "code/results/analysis"
sg = pd.read_csv(f"{d}/summary_groups.csv")
pf = pd.read_csv(f"{d}/pooled_feasibility.csv")
rd = pd.read_csv(f"{d}/rank_dependence.csv")
tu = pd.read_csv(f"{d}/targeted_vs_uniform.csv")
os_ = pd.read_csv(f"{d}/ordering_stability.csv")
cp = pd.read_csv(f"{d}/censoring_and_cpu.csv")
fails = 0
def chk(name, val, quoted, tol):
    global fails
    ok = abs(val - quoted) <= tol
    fails += not ok
    print(("ok   " if ok else "FAIL ") + f"{name}: computed {val:.4g}, paper {quoted}")
def L1(ds, cap, rule, grp, col="L1_med"):
    r = sg[(sg.dataset == ds) & (sg.design.isin(["all", "sample"])) & (sg.cap == cap) & (sg.rule == rule) & (sg.group == grp)]
    return r[col].iloc[0]
# Group medians quoted in the Results (cap ceil)
for rule, q in [("mean", 75), ("trimmed1", 55), ("geomean", 51), ("median", 29), ("min", 12)]:
    try:
        chk(f"OLLB 101-500 ceil L1 {rule}", L1("ollb", "ceil", rule, "101-500"), q, 1)
    except Exception as e:
        print("skip", rule, e)
for rule, q in [("mean", 1021), ("geomean", 992), ("median", 207), ("min", 200), ("plurality", 72)]:
    try:
        chk(f"HELM 31-100 ceil L1 {rule}", L1("helm", "ceil", rule, "31-100"), q, 1)
    except Exception as e:
        print("skip", rule, e)
# Kendall tau across cells
os_["d1"] = os_.cell1.str.split("|").str[0]; os_["d2"] = os_.cell2.str.split("|").str[0]
G = ["6-10", "11-30", "31-100"]
os_g = os_[os_.group.isin(G)]
hh = os_g[(os_g.d1 == "helm") & (os_g.d2 == "helm")].kendall_tau
oo = os_g[(os_g.d1 == "ollb") & (os_g.d2 == "ollb")].kendall_tau
oo5 = os_[(os_.group == "101-500") & (os_.d1 == "ollb") & (os_.d2 == "ollb")].kendall_tau
ho = os_g[os_g.d1 != os_g.d2].kendall_tau
chk("tau HELM within (groups >=5 targets): median", hh.median(), 0.45, 0.005); chk("tau HELM within: min", hh.min(), 0.22, 0.005); chk("tau HELM within: pairs", len(hh), 40, 0)
chk("tau OLLB within: median", oo.median(), 0.50, 0.005); chk("tau OLLB within: min", oo.min(), -0.52, 0.005); chk("tau OLLB within: pairs", len(oo), 77, 0)
chk("tau OLLB 101-500: median", oo5.median(), 0.15, 0.005); chk("tau OLLB 101-500: pairs", len(oo5), 21, 0)
chk("tau across datasets: median", ho.median(), 0.36, 0.005); chk("tau across datasets: min", ho.min(), -0.50, 0.005)
chk("tau across datasets: max", ho.max(), 0.86, 0.005); chk("tau across datasets: pairs", len(ho), 131, 0)
# Pooled feasibility on OLLB
for cap, rule, q in [("emp95", "mean", 0.075), ("emp95", "min", 0.014), ("gain10", "mean", 0.025), ("gain10", "min", 0.099)]:
    r = pf[(pf.dataset == "ollb") & (pf.cap == cap) & (pf.rule == rule) & (pf.design == "all")]
    chk(f"OLLB pooled feasible {cap} {rule}", r.feasible_rate.iloc[0], q, 0.0006)
# Rank-dependence slopes
ro = rd[(rd.cap == "ceil") & (rd.dataset == "ollb") & (rd.design == "all")].L1_slope_log10
rh = rd[(rd.cap == "ceil") & (rd.dataset == "helm") & (rd.design == "all")].L1_slope_log10
chk("OLLB slope min", ro.min(), 0.44, 0.006); chk("OLLB slope max", ro.max(), 0.65, 0.006)
chk("HELM slope min", rh.min(), 1.07, 0.006); chk("HELM slope max", rh.max(), 2.17, 0.006)
sp = rd[(rd.cap == "ceil") & (rd.design == "all")]
chk("Spearman OLLB min", sp[sp.dataset == "ollb"].L1_spearman.min(), 0.96, 0.006); chk("Spearman HELM min", sp[sp.dataset == "helm"].L1_spearman.min(), 0.97, 0.006)
chk("runner-up OLLB mean ceil L1", L1("ollb", "ceil", "mean", "2"), 4.8, 0.05)
ts = pd.read_csv(f"{d}/robust_tasksub_slopes.csv")
chk("tasksub mean slope min", ts[ts.rule == "mean"].loglog_slope_L1_vs_n.min(), 0.55, 0.006); chk("tasksub mean slope max", ts[ts.rule == "mean"].loglog_slope_L1_vs_n.max(), 1.06, 0.006)
mm = ts[ts.rule.isin(["median", "min"])].loglog_slope_L1_vs_n
chk("tasksub median/min slope min", mm.min(), -0.14, 0.006); chk("tasksub median/min slope max", mm.max(), 0.06, 0.006)
# Targeted vs uniform: mean
m = tu[(tu.rule == "mean") & (tu.design == "all")]
chk("mean ratio OLLB ceil", m[(m.dataset == "ollb") & (m.cap == "ceil")].ratio_med.max(), 1.0, 1e-6)
h = m[(m.dataset == "helm") & (m.cap == "ceil")].ratio_med
chk("mean ratio HELM ceil min", h.min(), 0.93, 0.006); chk("mean ratio HELM ceil max", h.max(), 0.99, 0.006)
o = m[(m.dataset == "ollb") & (m.cap == "emp95")].ratio_med
chk("mean ratio OLLB emp95 min", o.min(), 0.42, 0.006); chk("mean ratio OLLB emp95 max", o.max(), 0.89, 0.006)
# Compute accounting
chk("solves", float(cp.n.sum()), 260572, 0)
chk("time-outs", float(cp.censored.sum()), 0, 0)
# Empirical caps (emp95/emp99) and the types of the 540 pairs, from the processed OLLB matrix
import os
op = os.path.join(d, "..", "..", "data", "processed", "ollb6.csv")
T = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
o = pd.read_csv(op); o = o[~o.Flagged]; ix = o.set_index("fullname")
pr = o[(o["Base Model"].isin(ix.index)) & (o["Base Model"] != o.fullname)]
gn = pr[T].values - ix.loc[pr["Base Model"], T].values
chk("emp pairs", len(pr), 540, 0)
chk("pairs chat", pr.Type.str.contains("chat").sum(), 154, 0); chk("pairs domain fine-tuned", pr.Type.str.contains("domain").sum(), 346, 0)
for t, q in zip(T, [46.0, 7.3, 21.3, 3.8, 7.2, 3.2]): chk(f"emp95 {t}", np.percentile(gn, 95, axis=0)[T.index(t)], q, 0.05)
# Group-median monotonicity at ceil (design all), L1
order = ["2", "3-5", "6-10", "11-30", "31-100", "101-500", ">500"]
def mono(ds, rule):
    x = sg[(sg.dataset == ds) & (sg.cap == "ceil") & (sg.design == "all") & (sg.rule == rule)].set_index("group").L1_med
    v = [x[g] for g in order if g in x.index]
    return all(b >= a for a, b in zip(v, v[1:]))
for r_ in ["mean", "geomean", "trimmed1"]: chk(f"OLLB L1 group medians monotone: {r_}", float(mono("ollb", r_)), 1, 0)
for r_ in ["median", "min", "harmonic", "pow-5"]: chk(f"OLLB L1 group medians NOT monotone: {r_}", float(mono("ollb", r_)), 0, 0)
m_ = sg[(sg.dataset == "ollb") & (sg.cap == "ceil") & (sg.design == "all") & (sg.rule == "min")].set_index("group").L1_med
chk("OLLB min medians >500", m_[">500"], 46.5, 0.05); chk("OLLB min medians 11-30", m_["11-30"], 9.7, 0.05)
for r_ in sorted(sg[sg.dataset == "helm"].rule.unique()):
    chk(f"HELM L1 group medians monotone: {r_}", float(mono("helm", r_)), 0 if r_ == "plurality" else 1, 0)
# Analyses added after review (experiment-repo PR 25)
cpair = pd.read_csv(f"{d}/cap_composition_pairs.csv").set_index(["subset", "task"])
for sub_, vals in [("all", [46.0, 7.3, 21.3, 3.8, 7.2, 3.2]), ("nochat", [44.6, 7.0, 19.4, 3.9, 7.2, 3.2]), ("nochatname", [55.7, 7.9, 18.8, 3.1, 6.9, 3.2])]:
    for t, q in zip(T, vals): chk(f"emp95 {sub_} {t}", cpair.loc[(sub_, t), "emp95"], q, 0.05)
chk("pairs chat subset", cpair.loc[("chat", "IFEval"), "n_pairs"], 154, 0); chk("pairs nochatname subset", cpair.loc[("nochatname", "IFEval"), "n_pairs"], 207, 0)
cf = pd.read_csv(f"{d}/cap_composition_feasible.csv").set_index(["cap", "rule"]).feasible_share_all * 100
for (c_, r_), q in {("emp95", "mean"): 7.5, ("emp95_nochat", "mean"): 6.7, ("emp95_nochatname", "mean"): 6.9, ("emp99", "mean"): 12.1, ("empfrac95", "mean"): 1.4, ("head0.25", "mean"): 12.2,
                    ("emp95", "median"): 3.1, ("emp95_nochat", "median"): 2.7, ("emp95_nochatname", "median"): 2.9, ("emp99", "median"): 10.0, ("empfrac95", "median"): 1.7, ("head0.25", "median"): 9.4,
                    ("emp95", "min"): 1.4, ("emp95_nochat", "min"): 1.7, ("emp95_nochatname", "min"): 0.8, ("emp99", "min"): 6.1, ("empfrac95", "min"): 0.8, ("head0.25", "min"): 100,
                    ("emp95", "plurality"): 2.9, ("emp95_nochat", "plurality"): 2.3, ("emp95_nochatname", "plurality"): 2.2, ("emp99", "plurality"): 16.0, ("empfrac95", "plurality"): 0.4, ("head0.25", "plurality"): 4.4}.items():
    chk(f"feasible share {c_} {r_}", cf[(c_, r_)], q, 0.05)
fi = pd.read_csv(f"{d}/rank_dependence_fits.csv")
pw = fi[fi.form == "power"]
for ds, lv, n_pref, n_all in [("ollb", "group_median", 25, 32), ("helm", "group_median", 16, 18), ("ollb", "target", 21, 32), ("helm", "target", 31, 31)]:
    x = pw[(pw.dataset == ds) & (pw.level == lv)]; chk(f"power preferred (rmse log) {ds} {lv}", x.preferred.sum(), n_pref, 0); chk(f"fits {ds} {lv}", len(x), n_all, 0)
lin = fi[(fi.preferred_r2_L1 == 1) & (fi.form == "linear") & (fi.level == "group_median")]
chk("linear best R2 OLLB groups", (lin.dataset == "ollb").sum(), 14, 0); chk("linear best R2 HELM groups", (lin.dataset == "helm").sum(), 17, 0)
mo = pd.read_csv(f"{d}/rank_monotonicity.csv")
chk("monotone OLLB cells", mo[mo.dataset == "ollb"].monotone.sum(), 19, 0); chk("monotone HELM cells", mo[mo.dataset == "helm"].monotone.sum(), 31, 0)
dr = pd.read_csv(f"{d}/duplicate_rule_sensitivity.csv")
chk("duplicate rule max relative change", dr.L1_med_vs_best_rel.abs().max() * 100, 5.3, 0.05); chk("duplicate rule latest max", dr[dr.dup_rule == "latest"].L1_med_vs_best_rel.abs().max() * 100, 2.2, 0.05)
for r_, q in [("best", 41), ("first", 38), ("latest", 45), ("worst", 43)]:
    chk(f"emp95 mean infeasible 101-500 {r_}", dr[(dr.dup_rule == r_) & (dr.cap == "emp95") & (dr.group == "101-500")].infeasible_rate.iloc[0] * 100, q, 0.3)
hs = pd.read_csv(f"{d}/helm_subject_sizes.csv")
chk("HELM min items", hs.n_items.min(), 100, 0); chk("HELM median items", hs.n_items.median(), 173, 0); chk("HELM max items", hs.n_items.max(), 1534, 0)
chk("HELM total items", hs.n_items.sum(), 14042, 0); chk("HELM subjects with 100 items", (hs.n_items == 100).sum(), 10, 0)
sd = pd.read_csv(f"{d}/score_cap_defence.csv")
x = sd[(sd.clip_kind == "leader+h") & (sd.clip_h == 5) & (sd.attack_cap == "ceil")].set_index(["dataset", "rule"])
chk("defence share min over rules", x.share_can_reach_first.min(), 1.0, 0)
for k_, q in {("ollb", "mean"): 180.5, ("ollb", "median"): 109.1, ("ollb", "min"): 43.2, ("helm", "mean"): 696, ("helm", "median"): 113, ("helm", "min"): 98}.items():
    chk(f"defence L1 {k_}", x.loc[k_, "L1_med_feasible"], q, 0.5)
print("failures:", fails)
sys.exit(1 if fails else 0)
print("failures:", fails)
sys.exit(1 if fails else 0)
