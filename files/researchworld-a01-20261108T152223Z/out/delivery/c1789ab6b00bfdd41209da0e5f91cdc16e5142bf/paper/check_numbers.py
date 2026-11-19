"""Check that the numbers quoted in the text of the paper agree with the delivered result tables.

Usage: python3 -I paper/check_numbers.py [tables_dir]    (default: code/results/tables)
Every claim is (description, value computed from a table, value quoted in the paper, tolerance).
Exit status 1 if any claim disagrees.
"""
import sys
from pathlib import Path
import pandas as pd

T = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "code" / "results" / "tables")
mb = pd.read_csv(T / "main_by_rank.csv")
vm = pd.read_csv(T / "vs_mean.csv")
rs = pd.read_csv(T / "rank_scaling.csv")
ro = pd.read_csv(T / "rule_order_stability.csv")
cg = pd.read_csv(T / "cost_vs_gap.csv")
ts = pd.read_csv(T / "tasksub_summary.csv")
ns = pd.read_csv(T / "noise_summary_helm.csv")
no = pd.read_csv(T / "noise_summary_ollb_top500.csv")
rn = pd.read_csv(T / "raw_vs_norm.csv")
tb = pd.read_csv(T / "taskboot_summary_helm.csv")

claims = []
def add(desc, got, quoted, tol=None):
    claims.append((desc, float(got), float(quoted), tol if tol is not None else 0.5 * 10 ** -(len(str(quoted).split(".")[1]) if "." in str(quoted) else 0)))

def cell(ds, cap, rule, col, group="all", by="rank_mean"):
    r = mb[(mb.dataset == ds) & (mb.cap == cap) & (mb.rule == rule) & (mb.group_by == by) & (mb.group.astype(str) == group)]
    assert len(r) == 1, (ds, cap, rule, group)
    return r.iloc[0][col]

# --- headline (Section 4.2)
for rule, K, L1 in [("mean", 16, 696), ("plurality", 9, 47), ("min", 11.5, 98), ("median", 21, 112), ("copeland", 29, 213),
                    ("condorcet", 29, 213), ("borda", 47, 534)]:
    add(f"ceil {rule} K", cell("helm", "ceil", rule, "K_med_feas"), K, 0.05)
    add(f"ceil {rule} L1", cell("helm", "ceil", rule, "L1_med_feas"), L1, 0.5)
add("ceil mean K lo", cell("helm", "ceil", "mean", "K_lo_feas"), 13, .01); add("ceil mean K hi", cell("helm", "ceil", "mean", "K_hi_feas"), 18.5, .01)
add("ceil mean L1 lo", cell("helm", "ceil", "mean", "L1_lo_feas"), 556, .5); add("ceil mean L1 hi", cell("helm", "ceil", "mean", "L1_hi_feas"), 875, .5)
for rule, K in [("mean", 37), ("plurality", 18), ("borda", 48), ("copeland", 31)]:
    add(f"front0 {rule} K", cell("helm", "front0", rule, "K_med_feas"), K, .05)
add("front0 copeland L1", cell("helm", "front0", "copeland", "L1_med_feas"), 254, .5)
add("front0 condorcet L1", cell("helm", "front0", "condorcet", "L1_med_feas"), 259, .5)
add("ceil condorcet K ci", cell("helm", "ceil", "condorcet", "K_lo_feas"), 29, .01)
def ratio(cap, rule): return vm[(vm.dataset == "helm") & (vm.cap == cap) & (vm.rule == rule) & (vm.group.astype(str) == "all")].ratio_med.iloc[0]
for rule, q in [("plurality", .07), ("min", .15), ("median", .16), ("borda", .78)]:
    add(f"ceil ratio {rule}", ratio("ceil", rule), q, .005)
add("share cheaper borda", vm[(vm.dataset == "helm") & (vm.cap == "ceil") & (vm.rule == "borda") & (vm.group.astype(str) == "all")].share_cheaper_than_mean.iloc[0], .987, .0005)
for rule, q in [("geomean", .96), ("harmonic", .925), ("pow-2", .89), ("pow-5", .77)]:
    add(f"ceil ratio {rule}", ratio("ceil", rule), q, .006)
add("pow-5 K ceil", cell("helm", "ceil", "pow-5", "K_med_feas"), 15.5, .01)
wm = [cell("helm", "ceil", f"wmean{k}", "K_med_feas") for k in range(5)]
add("wmean K min", min(wm), 7, .01); add("wmean K max", max(wm), 9, .01)
wr = [ratio("ceil", f"wmean{k}") for k in range(5)]
add("wmean ratio min", min(wr), .36, .005); add("wmean ratio max", max(wr), .42, .005)

# --- order stability across caps (HELM-HELM pairs)
h = ro[ro.setting_a.str.startswith("helm") & ro.setting_b.str.startswith("helm")]
for m, med, lo, hi in [("L1", .85, .63, .93), ("K", .63, .19, .87)]:
    x = h[h.measure == m].kendall_tau
    add(f"tau {m} median", x.median(), med, .005); add(f"tau {m} min", x.min(), lo, .005); add(f"tau {m} max", x.max(), hi, .006)

# --- rank (4.3)
def slope(rule, col="slope_logL1_logrank"): return rs[(rs.dataset == "helm") & (rs.cap == "ceil") & (rs.rule == rule)].iloc[0][col]
for rule, s, lo, hi in [("mean", 1.13, .92, 1.34), ("median", 1.91, 1.71, 2.07), ("plurality", 3.29, 2.21, 4.11)]:
    add(f"slope {rule}", slope(rule), s, .005); add(f"slope {rule} lo", slope(rule, "lo"), lo, .005); add(f"slope {rule} hi", slope(rule, "hi"), hi, .005)
add("slope min", slope("min"), 1.59, .005)
sp = rs[(rs.dataset == "helm") & (rs.cap == "ceil")].set_index("rule").spearman
add("spearman plurality", sp["plurality"], .61, .005); add("spearman min", sp["min"], .88, .005); add("spearman median", sp["median"], .99, .005)
mt = sp[["mean", "geomean", "harmonic", "pow-0.5", "pow-2", "pow-5", "pow0.5"]]
add("spearman mean-type min", mt.min(), .93, .005); add("spearman mean-type max", mt.max(), 1.00, .005)
g = cg[(cg.dataset == "helm") & (cg.cap == "ceil")].spearman_L1_gap
add("gap spearman median", g.median(), .998, .0005); add("gap spearman min", g.min(), .88, .005); add("n rules gap", len(g), 14, .01)
add("rank2 mean K", cell("helm", "ceil", "mean", "K_med_feas", "2"), 1, .01); add("rank2 mean L1", cell("helm", "ceil", "mean", "L1_med_feas", "2"), 4.0, .05)
add("rank3-5 mean L1", cell("helm", "ceil", "mean", "L1_med_feas", "3-5"), 42, .5)
add("rank6-10 mean L1", cell("helm", "ceil", "mean", "L1_med_feas", "6-10"), 177, .5); add("rank6-10 mean K", cell("helm", "ceil", "mean", "K_med_feas", "6-10"), 5, .01)
add("rank11-30 mean K", cell("helm", "ceil", "mean", "K_med_feas", "11-30"), 10, .01); add("rank11-30 mean L1", cell("helm", "ceil", "mean", "L1_med_feas", "11-30"), 435, .5)
add("n targets rank 31+", cell("helm", "ceil", "mean", "n_targets", "31-100"), 49, .01)

# --- feasibility (4.4): infeasible share
for cap, vals in {"gain5": dict(mean=.86, median=.79, copeland=.79, borda=.86, min=.91, plurality=.63),
                  "gain10": dict(mean=.63, median=.49, plurality=.27, copeland=.51, borda=.68, min=.82),
                  "gain20": dict(mean=.28, median=.15, plurality=.05, copeland=.17, borda=.37, min=.56)}.items():
    for rule, q in vals.items(): add(f"infeasible {cap} {rule}", cell("helm", cap, rule, "infeasible"), q, .006)
add("gain10 mean feasible n", cell("helm", "gain10", "mean", "n_feasible"), 29, .01)
add("gain10 plurality feasible n", cell("helm", "gain10", "plurality", "n_feasible"), 57, .01)
add("gain10 min feasible n", cell("helm", "gain10", "min", "n_feasible"), 14, .01)
add("gain10 min K", cell("helm", "gain10", "min", "K_med_feas"), 3, .01); add("gain10 min L1", cell("helm", "gain10", "min", "L1_med_feas"), 9, .05)
add("gain10 mean rank31+ feasible", cell("helm", "gain10", "mean", "n_feasible", "31-100"), 0, .01)
add("gain10 mean rank11-30 feasible", cell("helm", "gain10", "mean", "n_feasible", "11-30"), 20, .01)
add("gain10 mean rank11-30 K", cell("helm", "gain10", "mean", "K_med_feas", "11-30"), 44.5, .01)

# --- K vs n (4.5), targets at rank 5, n = 48
def tsK(cap, rule, n, rank=5, col="K_med_feas"):
    r = ts[(ts.cap == cap) & (ts.rule == rule) & (ts.n == n) & (ts.target_rank == rank)]; return r.iloc[0][col]
add("n48 median K", tsK("ceil", "median", 48), 3, .01); add("n48 median bound", tsK("ceil", "median", 48, col="K_bound"), 25, .01)
add("n48 mean K ceil", tsK("ceil", "mean", 48), 4, .01); add("n48 mean K gain10", tsK("gain10", "mean", 48), 14, .01)
add("n48 plurality K", tsK("ceil", "plurality", 48), 4, .01); add("n48 min K", tsK("ceil", "min", 48), 1, .01)
add("n48 borda K ceil", tsK("ceil", "borda", 48), 14, .01); add("n48 borda K gain10", tsK("gain10", "borda", 48), 17, .01)
for n, q in zip([3, 6, 12, 24, 48], [1, 2, 4, 7, 14]): add(f"gain10 mean K n={n}", tsK("gain10", "mean", n), q, .01)
for n, q in zip([3, 6, 12, 24, 48], [2, 3, 4.5, 7.5, 17]): add(f"gain10 borda K n={n}", tsK("gain10", "borda", n), q, .01)
add("n48 gain10 median K", tsK("gain10", "median", 48), 3, .01); add("n48 gain10 plurality K", tsK("gain10", "plurality", 48), 4, .01)

# --- robustness (4.6): relative 5-95% width of L1 (median over the ten targets) and infeasible share
def relw(t, rule):
    x = t[t.rule == rule]; return ((x.L1_q95 - x.L1_q05) / x.L1_med).median()
for rule, a, b in [("mean", .51, .76), ("median", 2.33, 1.90), ("min", 1.90, 2.56), ("plurality", 1.49, 1.51), ("borda", 1.13, 1.10), ("condorcet", 1.08, 1.01)]:
    add(f"noise relw {rule}", relw(ns, rule), a, .006); add(f"taskboot relw {rule}", relw(tb, rule), b, .006)
add("noise min infeasible", ns[ns.rule == "min"].infeasible.mean(), .44, .006); add("taskboot min infeasible", tb[tb.rule == "min"].infeasible.mean(), .30, .006)

# --- second leaderboard (Section 4.7)
def vr(ds, cap, rule, col="ratio_med"): 
    r = vm[(vm.dataset == ds) & (vm.cap == cap) & (vm.rule == rule) & (vm.group.astype(str) == "all")]; assert len(r) == 1, (ds, cap, rule); return r.iloc[0][col]
for rule, K, L1 in [("mean", 2, 180.52), ("median", 3, 105.90), ("min", 3, 43.20), ("geomean", None, 153.19), ("harmonic", None, 124.81), ("pow-5", None, 67.50), ("borda", 2, 12.70), ("plurality", 2, 22.79), ("condorcet", 3, 23.33)]:
    if K is not None: add(f"ollb ceil {rule} K", cell("ollb", "ceil", rule, "K_med_feas"), K, .05)
    add(f"ollb ceil {rule} L1", cell("ollb", "ceil", rule, "L1_med_feas"), L1, .005)
add("ollb mean L1 lo", cell("ollb", "ceil", "mean", "L1_lo_feas"), 177.95, .005); add("ollb mean L1 hi", cell("ollb", "ceil", "mean", "L1_hi_feas"), 182.31, .005)
add("ollb n targets", cell("ollb", "ceil", "mean", "n_targets"), 4495, .01); add("ollb borda n", cell("ollb", "ceil", "borda", "n_targets"), 57, .01)
for rk, K, L1 in [("2", 1, 4.77), ("3-5", 1, 7.90), ("6-10", 1, 27.71), ("11-30", 1, 32.16), ("31-100", 1, 52.58), (">100", 2, 181.9)]:
    add(f"ollb rank {rk} L1", cell("ollb", "ceil", "mean", "L1_med_feas", rk), L1, .05)
add("ollb rank>100 n", cell("ollb", "ceil", "mean", "n_targets", ">100"), 4396, .01)
for rule, q in [("min", .25), ("median", .60), ("harmonic", .70), ("geomean", .85), ("borda", .37), ("plurality", .50), ("condorcet", .64)]:
    add(f"ollb ratio {rule}", vr("ollb", "ceil", rule), q, .005)
for rule, q in [("min", .23), ("copeland", .27), ("median", .34), ("plurality", .38), ("borda", .39), ("condorcet", .64), ("trimmed1", .82)]:
    add(f"top500 ratio {rule}", vr("ollb_top500", "ceil", rule), q, .005)
add("top500 copeland matched", vr("ollb_top500", "ceil", "copeland", "n_both_feasible"), 27, .01)
add("top500 n targets", cell("ollb_top500", "gain10", "mean", "n_targets"), 116, .01)
for rule, q in [("min", .24), ("median", .60), ("geomean", .85), ("borda", .38), ("condorcet", .59), ("plurality", .42)]:
    add(f"nomerge ratio {rule}", vr("ollb_nomerge", "ceil", rule), q, .005)
add("nomerge n targets", cell("ollb_nomerge", "ceil", "mean", "n_targets"), 3788, .01)
add("helm plurality ratio", ratio("ceil", "plurality"), .07, .005); add("helm borda ratio", ratio("ceil", "borda"), .78, .005)
def osl(ds, rule, col="slope_logL1_logrank"): return rs[(rs.dataset == ds) & (rs.cap == "ceil") & (rs.rule == rule)].iloc[0][col]
add("ollb slope mean", osl("ollb", "mean"), .44, .005); add("ollb slope mean lo", osl("ollb", "mean", "lo"), .43, .005); add("ollb slope mean hi", osl("ollb", "mean", "hi"), .44, .005)
for ds, cap, vals in [("ollb", "gain10", dict(mean=.97, median=.95, min=.90)), ("ollb", "emp95", dict(mean=.93, median=.97, min=.99)),
                      ("ollb_top500", "gain10", dict(mean=.34, median=.31, min=.25, borda=.10, copeland=.29, condorcet=.59, plurality=.65))]:
    for rule, q in vals.items(): add(f"{ds} infeasible {cap} {rule}", cell(ds, cap, rule, "infeasible"), q, .006)
add("ollb gain10 mean feasible n", cell("ollb", "gain10", "mean", "n_feasible"), 113, .01)
def rnv(rule, col, cap="ceil"):
    r = rn[(rn.cap == cap) & (rn.rule == rule)]; assert len(r) == 1, (cap, rule); return r.iloc[0][col]
for rule, q in [("mean", .85), ("median", .86), ("geomean", .91), ("harmonic", .99), ("pow-5", 1.38), ("min", 1.61)]:
    add(f"raw/norm L1 {rule}", rnv(rule, "L1_ratio_raw_over_norm_med"), q, .006)
add("raw/norm K equal mean", rnv("mean", "K_equal_share"), .94, .006); add("raw/norm K equal min", rnv("min", "K_equal_share"), .29, .006)
add("raw/norm rank equal mean", rnv("mean", "rank_rule_equal_share"), .01, .006)
add("raw/norm spread", rnv("min", "L1_ratio_raw_over_norm_med") / rnv("mean", "L1_ratio_raw_over_norm_med"), 1.9, .05)
def orelw(rule):
    x = no[no.rule == rule]; return ((x.L1_q95 - x.L1_q05) / x.L1_med).median()
for rule, q in [("mean", .52), ("geomean", .86), ("condorcet", .65), ("median", 1.83), ("borda", 1.59), ("plurality", .76)]:
    add(f"ollb noise relw {rule}", orelw(rule), q, .006)
add("ollb noise min infeasible", no[no.rule == "min"].infeasible.mean(), .52, .006); add("ollb noise plurality infeasible", no[no.rule == "plurality"].infeasible.mean(), .30, .006)
add("ollb noise min rank under rule", no[no.rule == "min"].rank_rule_med.median(), 248, 1)
for m, q in [("L1", .63), ("K", .46)]:
    r = ro[(ro.measure == m) & (ro.setting_a == "helm|ceil") & (ro.setting_b == "ollb|ceil")]; add(f"tau helm-ollb {m}", r.kendall_tau.iloc[0], q, .005)
o = ro[ro.setting_a.str.startswith("ollb|") & ro.setting_b.str.startswith("ollb|")]
for m, q in [("L1", .68), ("K", .58)]:
    add(f"tau within ollb {m} median", o[o.measure == m].kendall_tau.median(), q, .005)

# --- example plan (4.2)
ep = pd.read_csv(T.parent / "example_plan_summary.csv").set_index("rule")
for rule, K, L1 in [("mean", 16, 154), ("median", 5, 6.2), ("plurality", 10, 5.0), ("borda", 46, 43.7), ("condorcet", 27, 24.5)]:
    add(f"example plan {rule} K", ep.loc[rule, "K"], K, .01); add(f"example plan {rule} L1", ep.loc[rule, "L1"], L1, .05)
add("example mean plan rank median", ep.loc["mean", "rank_after_median"], 1, .01); add("example mean plan rank plurality", ep.loc["mean", "rank_after_plurality"], 1, .01)
add("example mean plan rank borda", ep.loc["mean", "rank_after_borda"], 4, .01)
add("example median plan rank mean", ep.loc["median", "rank_after_mean"], 5, .01); add("example plurality plan rank mean", ep.loc["plurality", "rank_after_mean"], 5, .01)

add("helm plurality ratio 3 digits", ratio("ceil", "plurality"), .068, .0005)
add("helm median ratio", ratio("ceil", "median"), .16, .005)
bad = 0
for d, got, q, tol in claims:
    ok = abs(got - q) <= tol
    bad += not ok
    if not ok: print(f"MISMATCH {d}: table {got:.4f} vs paper {q} (tol {tol})")
print(f"{len(claims)} claims checked, {bad} mismatches")
sys.exit(1 if bad else 0)
