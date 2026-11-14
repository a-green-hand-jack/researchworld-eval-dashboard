"""Generate paper/gen/numbers.tex (macros) from code/results (final grids of the analysis position).
Usage: python3 -I make_numbers.py   (run from paper/; reads ../code/results/summary/*.csv and ../code/results/theory_checks.csv)
Every number quoted in the paper text through a macro comes from here; nothing is typed by hand."""
import pathlib
import numpy as np, pandas as pd

R = pathlib.Path(__file__).resolve().parent.parent / "code" / "results"
S = R / "summary"
OUT = pathlib.Path(__file__).resolve().parent / "gen"; OUT.mkdir(exist_ok=True)
mac = {}
def put(name, val, f="{:.2f}"):
    mac[name] = f.format(val) if not isinstance(val, str) else val
def pct(x): return f"{100*x:.0f}"

# ---- theory checks (C1-C3)
t = pd.read_csv(R / "theory_checks.csv")
put("thRows", len(t), "{:d}")
def sci(x):
    e = int(np.floor(np.log10(x))); m = np.ceil(x / 10**e * 10) / 10
    if m >= 10: m, e = 1.0, e + 1
    return f"{m:.1f}\\times10^{{{e}}}"
mac["thMaxLone"] = sci(np.nanmax(np.abs(t.dL1))); put("thMaxK", np.nanmax(np.abs(t.dK)), "{:.0f}")
mac["thMaxLinf"] = sci(np.nanmax(np.abs(t.dLinf)))

# ---- C2: min vs mean (ceiling cap; statistic = CV of the target's task scores, secondary = mean minus min)
c2 = pd.read_csv(S / "c2_min_vs_mean.csv"); c2 = c2[c2.cap == "ceil"]
def neg(x, nd=2): return "{:+.{}f}".format(x, nd).replace("-", "$-$")
for d, D in (("helm", "Helm"), ("ollb", "Ollb")):
    x = c2[(c2.dataset == d) & (c2.statistic == "cv")].set_index("tercile")
    put(f"ctwo{D}Ratio", x.loc["all", "ratio_med"], "{:.2f}"); put(f"ctwo{D}RatioLo", x.loc["all", "ratio_lo"]); put(f"ctwo{D}RatioHi", x.loc["all", "ratio_hi"])
    put(f"ctwo{D}Rho", neg(x.loc["all", "spearman"])); put(f"ctwo{D}Share", pct(x.loc["all", "share_min_cheaper"])); put(f"ctwo{D}N", x.loc["all", "n"], "{:.0f}")
    for t, T in (("low", "Low"), ("mid", "Mid"), ("high", "High")):
        put(f"ctwo{D}T{T}", x.loc[t, "ratio_med"], "{:.2f}"); put(f"ctwo{D}T{T}Lo", x.loc[t, "ratio_lo"], "{:.2f}"); put(f"ctwo{D}T{T}Hi", x.loc[t, "ratio_hi"], "{:.2f}")
    y = c2[(c2.dataset == d) & (c2.statistic == "mean_minus_min") & (c2.tercile == "all")].iloc[0]
    put(f"ctwo{D}RhoMM", neg(y.spearman))

# ---- C3: K/n over task subsets (targets of rank 2 and 5, averaged)
c3 = pd.read_csv(S / "c3_tasksub.csv")
for n, N in ((5, "Five"), (57, "Full")):
    for r, Rn in (("mean", "Mean"), ("median", "Median"), ("min", "Min"), ("borda", "Borda"), ("plurality", "Plur")):
        put(f"cthree{N}{Rn}", c3[(c3.n == n) & (c3.rule == r)].K_over_n_med.mean(), "{:.2f}")
mf = c3[(c3.rule == "min") & (c3.n == 5) & (c3.target_rank == 5)].feas.iloc[0]
put("cthreeMinFeasFive", 1 - mf, "{:.2f}")

# ---- C4: R2 of log L1 on log rank vs on log gap; support = CI of the R2 difference excludes 0 in favour of the gap
c4 = pd.read_csv(S / "c4_rank_vs_gap.csv")
for _, r in c4.iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Ru = r.rule.capitalize()
    put(f"cfour{D}{Ru}Rank", r.R2_rank, "{:.2f}"); put(f"cfour{D}{Ru}Gap", r.R2_gap, "{:.2f}")
    put(f"cfour{D}{Ru}Diff", neg(r.R2_diff, 3)); put(f"cfour{D}{Ru}DiffLo", neg(r.R2_diff_lo, 3)); put(f"cfour{D}{Ru}DiffHi", neg(r.R2_diff_hi, 3))
with open(OUT / "tab_c4.tex", "w") as f:
    f.write("\\begin{tabular}{@{}llrccc@{}}\n\\toprule\ndataset & rule & targets & $R^2$ (log rank) & $R^2$ (log gap) & difference [95\\% CI] \\\\\n\\midrule\n")
    for _, r in c4.iterrows():
        f.write(f"{'HELM' if r.dataset=='helm' else 'OLLB'} & {r.rule} & {r.n} & {r.R2_rank:.2f} & {r.R2_gap:.2f} & {neg(r.R2_diff,3)} [{neg(r.R2_diff_lo,3)}, {neg(r.R2_diff_hi,3)}] \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---- C5: feasible share vs h ; h* ; emp95
fh = pd.read_csv(S / "c5_feasible_vs_h.csv")
def feas(d, rule, h): return fh[(fh.dataset == d) & (fh.rule == rule) & (fh.h == h)].feas.iloc[0]
for d, D in (("helm", "Helm"), ("ollb", "Ollb")):
    for rule in sorted(fh[fh.dataset == d].rule.unique()):
        for h in (10, 20): put(f"cfive{D}{rule.capitalize()}H{'ten' if h==10 else 'twenty'}", pct(feas(d, rule, h)))
mg = pd.read_csv(S / "main_groups.csv")
g = mg[mg.cap == "emp95"].groupby(["dataset", "rule"])[["n_feasible", "n_targets"]].sum()
for (d, rule), r in g.iterrows():
    put(f"ceightEmp{'Helm' if d=='helm' else 'Ollb'}{rule.capitalize()}", pct(r.n_feasible / r.n_targets))
for (d, rule), r in g.iterrows():
    put(f"ceightInf{'Helm' if d=='helm' else 'Ollb'}{rule.capitalize()}", pct(1 - r.n_feasible / r.n_targets))
hs = pd.read_csv(S / "c5_c8_hstar.csv"); hs = hs[hs.group == "all"]
for _, r in hs.iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Ru = r.rule.capitalize()
    put(f"hstar{D}{Ru}", r.hstar_med, "{:.1f}"); put(f"hstar{D}{Ru}Lo", r.hstar_lo, "{:.1f}"); put(f"hstar{D}{Ru}Hi", r.hstar_hi, "{:.1f}")
    put(f"hstarShare{D}{Ru}", pct(r.share_hstar_gt_emp95))
# h* by rank bin (the all-target median is dominated by low-ranked targets)
BINS = {"2": "Two", "3-5": "ThreeFive", "6-10": "SixTen", "11-30": "ElevenThirty", "31-100": "ThirtyOneHundred", ">100": "OverHundred"}
hb = pd.read_csv(S / "c5_c8_hstar.csv")
for _, r in hb[hb.group.isin(BINS)].iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Ru = r.rule.capitalize(); B = BINS[r.group]
    put(f"hstarBin{D}{Ru}{B}", r.hstar_med, "{:.1f}"); put(f"hstarBinShare{D}{Ru}{B}", pct(r.share_hstar_gt_emp95))
    if Ru == "Mean": put(f"hstarBinN{D}{B}", r.n_targets, "{:.0f}")
ho = hb[(hb.dataset == "ollb") & (hb.rule == "mean")].set_index("group").n_targets
put("ollbShareOverHundred", pct(ho[">100"] / ho["all"]))
put("empPooled", fh.emp95_pooled.iloc[0], "{:.1f}")
c8 = pd.read_csv(S / "c8_cap_realism.csv"); put("empMmluQ", c8.gain_emp95_mmlupro.dropna().iloc[0], "{:.1f}")
for _, r in c8[(c8.group == "all") & (c8.dataset == "helm")].iterrows():
    put(f"hstarMmluShareHelm{r.rule.capitalize()}", pct(r.share_hstar_gt_emp95_mmlupro))

# ---- C7: noise / flip
nh = pd.read_csv(S / "noise_helm_t30.csv"); no = pd.read_csv(S / "noise_ollb_t30.csv"); tbh = pd.read_csv(S / "taskboot_helm_t30.csv")
for D, df in (("Helm", nh), ("Ollb", no)):
    put(f"noiseN{D}", df[df.group == "all"].n_targets.iloc[0], "{:.0f}"); put(f"noiseDraws{D}", df[df.group == "all"].n_draws.max(), "{:.0f}")
put("tbootNHelm", tbh[tbh.group == "all"].n_targets.iloc[0], "{:.0f}"); put("tbootDrawsHelm", tbh[tbh.group == "all"].n_draws.max(), "{:.0f}")
for _, r in tbh[tbh.group == "all"].iterrows(): put(f"tbootRatioHelm{r.rule.capitalize()}", r.L1_ratio_mean, "{:.2f}"); put(f"tbootFeasHelm{r.rule.capitalize()}", pct(r.feas_noisy))
nh = nh[nh.group == "all"].set_index("rule"); no = no[no.group == "all"].set_index("rule")
for D, df in (("Helm", nh), ("Ollb", no)):
    for rule in df.index:
        put(f"noiseRatio{D}{rule.capitalize()}", df.loc[rule, "L1_ratio_mean"], "{:.2f}")
        put(f"noiseFeas{D}{rule.capitalize()}", pct(df.loc[rule, "feas_noisy"])); put(f"noiseFeasObs{D}{rule.capitalize()}", pct(df.loc[rule, "feas_obs"]))
fl = pd.read_csv(S / "flip.csv")
fl = fl[fl.group == "11-30"]
for d, D in (("helm", "Helm"), ("ollb", "Ollb")):
    for rule in ("mean", "median", "min", "geomean"):
        x = fl[(fl.dataset == d) & (fl.rule == rule)]
        if len(x): put(f"flipP{D}{rule.capitalize()}", x.p_eps.median(), "{:.2f}"); put(f"flipX{D}{rule.capitalize()}", x.extra.median(), "{:.1f}")


# ---- bin 11-30 medians at the ceiling (HELM), and pooled emp95pool feasibility
b = mg[(mg.cap == "ceil") & (mg.group == "11-30")]
for _, r in b.iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Ru = r.rule.capitalize()
    put(f"binK{D}{Ru}", r.Kmed, "{:.0f}"); put(f"binL{D}{Ru}", r.L1med, "{:.0f}")
ep = mg[(mg.cap == "emp95pool")].groupby(["dataset", "rule"])[["n_feasible", "n_targets"]].sum()
sh = (ep.n_feasible / ep.n_targets).xs("helm")
put("empPoolHelmMin", pct(sh.min())); put("empPoolHelmMax", pct(sh.max()))
e95 = pd.Series({k: v.n_feasible / v.n_targets for k, v in g.iterrows()})
put("empHelmMin", pct(e95.xs("helm").min())); put("empHelmMax", pct(e95.xs("helm").max()))
put("empOllbScoreMin", pct(e95.xs("ollb")[["mean", "median", "min", "geomean", "harmonic"]].min())); put("empOllbScoreMax", pct(e95.xs("ollb")[["mean", "median", "min", "geomean", "harmonic"]].max()))

# ---- feasible shares under additive caps (all targets; OLLB ordinal rules only on the rank-stratified sample)
om = pd.read_csv(S / "ollb_matched_sample.csv")
for cap, Cn in (("gain10", "Ten"), ("gain20", "Twenty")):
    t = mg[(mg.cap == cap)].groupby(["dataset", "rule"])[["n_feasible", "n_targets"]].sum()
    for (d, rule), r in t.iterrows():
        if d == "ollb" and rule in ("borda", "condorcet", "plurality"): continue
        put(f"gf{Cn}{'Helm' if d == 'helm' else 'Ollb'}{rule.capitalize()}", pct(r.n_feasible / r.n_targets))
    t = om[om.cap == cap].groupby("rule")[["n_feasible", "n_targets"]].sum()
    for rule, r in t.iterrows(): put(f"gf{Cn}Samp{rule.capitalize()}", pct(r.n_feasible / r.n_targets))

# ---- appendix: eps sensitivity, spillover, slices
e = pd.read_csv(S / "eps.csv"); e1 = e[e.eps == 0.1]; e6 = e[e.eps < 1e-3]
for d, D in (("helm", "Helm"), ("ollb", "Ollb")):
    x = e1[e1.dataset == d]
    put(f"epsRatioLo{D}", x.L1_ratio_med.min() , "{:.3f}"); put(f"epsRatioHi{D}", x.L1_ratio_med.max(), "{:.3f}")
    put(f"epsFeasChange{D}", x.feas_change.abs().max(), "{:.0f}")
    put(f"epsSmallMaxRatio{D}", e6[e6.dataset == d].L1_ratio_max.max(), "{:.3f}")
sp = pd.read_csv(S / "spillover.csv"); sp = sp[sp.lam > 0]
t = sp.groupby(["dataset", "rule", "lam"]).L1_ratio.median()
for (d, rule, lam), v in t.items():
    put(f"spill{'Helm' if d == 'helm' else 'Ollb'}{rule.capitalize()}Lam{'A' if lam < 0.2 else 'B'}", v, "{:.2f}")

# ---- C7 slices (ceiling, OLLB ranks 2-100, rank-stratified sample): median L1 per rule and slice
c7 = pd.read_csv(S / "c7_slices_compact.csv"); c7 = c7[c7.cap == "ceil"]
for sl_, Sl in (("main_sample", "Main"), ("nomerge", "Nomerge"), ("raw", "Raw"), ("top500", "Top")):
    x = c7[c7.slice == sl_].set_index("rule")
    put(f"sliceN{Sl}", x.n_targets.iloc[0], "{:.0f}")
    for rule in ("mean", "median", "min"): put(f"sliceL{Sl}{rule.capitalize()}", x.loc[rule, "L1med"], "{:.1f}")

# ---- run times (jobs whose log printed a final wall time; running jobs excluded from the total)
rt = pd.read_csv(S / "runtimes.csv")
done = rt[rt.log_last_done_wall_s.notna() & (rt.state.fillna("") != "running")]
put("rtJobs", len(done), "{:.0f}"); put("rtHours", done.log_last_done_wall_s.sum() / 3600, "{:.1f}")
put("rtMaxJob", done.log_last_done_wall_s.max() / 3600, "{:.1f}")

# ---- sensitivity analyses delivered after the first version (convex cost, margins, clusters, pairs, ordinal ranks 2-100, resources)
cv = pd.read_csv(S / "convex_cost.csv")
for _, r in cv[(cv.comparison == "min / mean") & (cv.cv_tercile == "all")].iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; C = r.cost.capitalize()
    put(f"cvx{D}{C}Ratio", r.ratio_median, "{:.2f}"); put(f"cvx{D}{C}Share", pct(r.share_min_cheaper)); put(f"cvx{D}{C}Rho", r.spearman_ratio_cv, "{:.2f}")
    put(f"cvx{D}{C}N", r.n, "{:.0f}")
q = cv[(cv.comparison == "min / mean") & (cv.cost == "quadratic") & (cv.dataset == "ollb") & (cv.cv_tercile == "high")].iloc[0]
put("cvxOllbQuadHighMeanCheaper", pct(1 - q.share_min_cheaper)); put("cvxOllbQuadHighRatio", q.ratio_median, "{:.2f}")
mr = pd.read_csv(S / "margin_robust.csv"); mr = mr[mr.group == "all"]
SC = {"eps1e-3": "Base", "eps0.1": "Tenth", "eps1": "One", "rule_specific": "Rule"}
for _, r in mr[mr.claim == "C2"].iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Sc = SC[r.scenario]
    if r.statistic.startswith("median"): put(f"mr{D}{Sc}Ratio", r.value, "{:.2f}")
    if r.statistic.startswith("Spearman"): put(f"mr{D}{Sc}Rho", r.value, "{:.2f}")
for _, r in mr[(mr.claim == "C5") & (mr.cap == "gain10")].iterrows():
    D = "Helm" if r.dataset == "helm" else "Ollb"; Sc = SC[r.scenario]; ru = r.statistic.split("(")[1].rstrip(")").capitalize()
    put(f"mrFeas{D}{Sc}{ru}", pct(r.value))
cb = pd.read_csv(S / "cluster_bootstrap_ollb.csv")
def cbp(name, stat, sub):
    r = cb[(cb.statistic == stat) & (cb.subset == sub)].iloc[0]
    put(f"cb{name}", r.estimate, "{:.3f}"); put(f"cb{name}IidLo", r.iid_lo, "{:.3f}"); put(f"cb{name}IidHi", r.iid_hi, "{:.3f}")
    put(f"cb{name}Lo", r.cluster_lo, "{:.3f}"); put(f"cb{name}Hi", r.cluster_hi, "{:.3f}")
cbp("Ratio", "C2 median L1(min)/L1(mean)", "CV tercile all"); cbp("RatioHigh", "C2 median L1(min)/L1(mean)", "CV tercile high")
for rule in ("geomean", "harmonic", "median", "min", "borda", "condorcet"):
    x = cb[cb.statistic == f"C4 R2 gap - R2 rank ({rule})"]
    if len(x): cbp(f"Diff{rule.capitalize()}", f"C4 R2 gap - R2 rank ({rule})", x.subset.iloc[0])
put("cbClusters", cb.n_clusters.iloc[0], "{:.0f}"); put("cbTargets", cb.n_targets.iloc[0], "{:.0f}")
pc = pd.read_csv(R / "pairs_composition.csv")
for key, nm in (("fine-tuned on domain-specific datasets", "Domain"), ("chat models (RLHF, DPO, IFT)", "Chat")):
    r = pc[(pc.grouping == "Type of the fine-tune") & (pc.cls == key)].iloc[0]; put(f"pair{nm}", r.n_pairs, "{:.0f}"); put(f"pair{nm}Share", pct(r.share))
ec = pd.read_csv(R / "emp_caps_restricted.csv")
ec = ec[(ec["quantile"] == 95) & (ec.task == "pooled scalar")].set_index("subset")
put("pairRestrictedN", ec.loc["restricted", "n_pairs"], "{:.0f}"); put("empPooledRestricted", ec.loc["restricted", "cap_gain"], "{:.1f}")
bm = pd.read_csv(R / "base_model_metadata.csv").set_index("item")["count"]
put("bmPlaceholder", bm["... of which 'Removed' / '(Merge)' / starts with '[' placeholder strings"], "{:.0f}"); put("bmSuspect", bm["pairs whose fine-tune scores below its base on all six tasks (suspect base entry)"], "{:.0f}")
rp = pd.read_csv(S / "c8_restricted_pairs.csv")
for _, r in rp[(rp.cap == "emp95") | (rp.cap == "emp95r")].iterrows():
    if (r.dataset, r.ranks) in (("ollb", "2-30"), ("helm", "11-30")):
        D = "Helm" if r.dataset == "helm" else "Ollb"; V = "R" if r.cap.endswith("r") else "A"
        put(f"rp{D}{r.rule.capitalize()}{V}", pct(r.share_infeasible))
og = pd.read_csv(S / "ollb_ord100_groups.csv")
for _, r in og[og.group == "2-100"].iterrows():
    Ru = r.rule.capitalize(); C = "Ceil" if r.cap == "ceil" else "Ten"
    put(f"ordHundred{C}{Ru}Feas", pct(r.feas)); put(f"ordHundred{C}{Ru}K", r.Kmed, "{:.0f}"); put(f"ordHundred{C}{Ru}L", r.L1med, "{:.1f}")
cpu = pd.read_csv(S / "cpu_total.csv").iloc[0]; put("cpuHours", cpu.total_cpu_h, "{:.0f}")
ho = pd.read_csv(S / "ollb_hstar_ord100_groups.csv")
for _, r in ho.iterrows():
    B = {"2-10": "TwoTen", "11-30": "ElevenThirty", "31-100": "ThirtyOneHundred", "2-100": "All"}[r.group]
    put(f"hstarOrd{r.rule.capitalize()}{B}", r["median"], "{:.1f}")
    if B == "All": put(f"hstarOrd{r.rule.capitalize()}Max", r["max"], "{:.1f}"); put("hstarOrdN", r.n, "{:.0f}")
pm = pd.read_csv(S / "peak_memory.csv"); put("peakMemMB", pm.peak_rss_mb.max(), "{:.0f}")


with open(OUT / "numbers.tex", "w") as f:
    f.write("% generated by paper/make_numbers.py from code/results; do not edit\n")
    for k, v in sorted(mac.items()): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(mac), "macros")
