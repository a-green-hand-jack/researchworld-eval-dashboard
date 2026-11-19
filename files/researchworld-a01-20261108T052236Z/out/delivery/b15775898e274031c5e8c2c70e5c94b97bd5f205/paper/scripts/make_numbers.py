#!/usr/bin/env python3
"""Write paper/numbers.tex: every number quoted in the paper text that comes from analysis/results.

Usage: python3 paper/scripts/make_numbers.py   (run from the delivery root)
Text uses \\num{key}; keys are listed in numbers.tex. Nothing is typed by hand.
"""
import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
R = ROOT / "analysis" / "results"
CL = R / "claims"
out = {}


def f(x, nd=0):
    if pd.isna(x):
        return "n/a"
    if x == float("inf"):
        return "inf"
    return f"{x:.{nd}f}"


def pct(x, nd=0):
    return f"{100 * x:.{nd}f}"


# --- cap map (cap_rule_summary): medians over feasible targets, feasible share
cs = pd.read_csv(CL / "cap_rule_summary.csv")
for r in cs.itertuples():
    k = f"{r.dataset}.{r.cap}.{r.rule}"
    out[k + ".K"] = f(r.K_q50, 1 if r.K_q50 % 1 else 0)
    out[k + ".L1"] = f(r.L1_q50)
    out[k + ".Linf"] = f(r.Linf_q50, 1)
    out[k + ".feas"] = pct(r.share_feasible)
    out[k + ".nfeas"] = str(int(r.n_feasible))
    out[k + ".ntar"] = str(int(r.n_targets))
    out[k + ".feaslo"] = pct(r.feas_wilson_lo, 1)
    out[k + ".feashi"] = pct(r.feas_wilson_hi, 1)

# --- C2
c2 = pd.read_csv(CL / "c2_order_statistics.csv")
for r in c2.itertuples():
    pair = r.pair.replace("K(", "").replace(")", "").replace(" <= ", "<").replace(" ", "")
    out[f"c2.{r.dataset}.{r.cap}.{pair}"] = pct(r.share_holds)
    out[f"c2n.{r.dataset}.{r.cap}.{pair}"] = str(int(r.n_both_feasible))

# --- C4
c4 = pd.read_csv(CL / "c4_ordinal_vs_mean.csv")
for r in c4.itertuples():
    k = f"c4.{r.dataset}.{r.cap}.{r.ordinal_rule}"
    out[k + ".cheaper"] = pct(r.share_ordinal_cheaper)
    out[k + ".ratio"] = f(r.ratio_med, 2)
    out[k + ".nboth"] = str(int(r.n_both_feasible))
    out[k + ".ntar"] = str(int(r.n_targets))
    out[k + ".ordonly"] = str(int(r.n_ordinal_feasible_mean_infeasible))
    out[k + ".meanonly"] = str(int(r.n_mean_feasible_ordinal_infeasible))

# --- pairwise rule comparison
pw = pd.read_csv(CL / "pairwise_rule_comparison.csv")
for r in pw.itertuples():
    k = f"pw.{r.dataset}.{r.measure}.{r.cap}.{r.rule_a}.{r.rule_b}"
    out[k + ".cheaper"] = pct(r.share_a_cheaper, 1)
    out[k + ".equal"] = pct(r.share_equal, 1)

# --- C3 rule ranks by cap
c3 = pd.read_csv(CL / "c3_rule_ordering_by_cap.csv")
for r in c3.itertuples():
    for col in c3.columns:
        if col.startswith("rank_") and not pd.isna(getattr(r, col)):
            out[f"c3.{r.dataset}.{r.measure}.{r.cap}.{col[5:]}"] = f(getattr(r, col))

# --- eps and offset sensitivity (L1 at ceil, relative to eps=1e-3 / offset 1)
eps = pd.read_csv(CL / "robust_eps.csv")
base = cs[cs.cap == "ceil"][["dataset", "rule", "L1_q50"]]
x = eps[(eps.cap == "ceil") & (eps.measure == "L1")].merge(base, on=["dataset", "rule"])
x["rel"] = (x.median_feasible / x.L1_q50 - 1).abs()
out["eps.maxrel.1e-4"] = pct(x[x.eps == 1e-4].rel.max(), 2)
out["eps.maxrel.1e-2"] = pct(x[x.eps == 1e-2].rel.max(), 2)
out["eps.maxrel.1e-1"] = pct(x[x.eps == 0.1].rel.max(), 1)
of = pd.read_csv(CL / "robust_offsets.csv")
of = of[(of.cap == "ceil") & (of.measure == "L1")]
ref = of[of.offset_s == 1.0].set_index(["dataset", "family"]).median_feasible
of = of.assign(rel=lambda d: (d.median_feasible / d.set_index(["dataset", "family"]).index.map(ref) - 1).abs())
out["offs.maxrel"] = pct(of.rel.max(), 1)

# --- near-top costs (mean rule, ceil): OLLB and HELM targets of mean rank 2..5
for ds, fn in [("ollb", "ollb_closed.csv"), ("helm", "helm_main.csv")]:
    d = pd.read_csv(R / fn)
    d = d[(d.cap == "ceil") & (d.rule == "mean") & (d.rank_mean.between(2, 5))]
    out[f"near.{ds}.L1.min"] = f(d.L1.min(), 1)
    out[f"near.{ds}.L1.max"] = f(d.L1.max(), 1)
    out[f"near.{ds}.n"] = str(len(d))

# --- robustness slices (L1 order at ceil)
sl = pd.read_csv(CL / "robust_slices.csv")
for r in sl[sl.cap == "ceil"].itertuples():
    out[f"slice.{r.slice}.{r.rule}.L1"] = f(r.L1_med)
    out[f"slice.{r.slice}.ntar"] = str(int(r.n_targets))
orders = {}
for s, g in sl[sl.cap == "ceil"].groupby("slice"):
    orders[s] = list(g.sort_values("L1_med").rule)
out["slice.n_same_order"] = str(sum(o == orders["ollb"] for o in orders.values()))
out["slice.n_slices"] = str(len(orders))

# --- fixed-strategy replay (F4); targets with rank_mean > 1 only
rp = pd.read_csv(CL / "robust_replay_summary.csv")
u = rp[(rp.strategy == "uniform") & (rp.rank_mean > 1)]
for (ds, cap, rule), g in u.groupby(["dataset", "cap", "rule"]):
    out[f"replay.{ds}.{cap}.{rule}.pnom"] = f(g.p_first_at_nominal_Linf.median(), 2)
uc = u[u.cap == "ceil"].assign(extra=lambda d: d.budget_p90 - d.nominal_Linf_min)
med = uc.groupby(["dataset", "rule"]).p_first_at_nominal_Linf.median()
out["replay.pnom.min"] = f(med.min(), 2)
out["replay.pnom.max"] = f(med.max(), 2)
out["replay.pnom.rangelo"] = f(uc.p_first_at_nominal_Linf.min(), 2)
out["replay.pnom.rangehi"] = f(uc.p_first_at_nominal_Linf.max(), 2)
ex = uc.groupby(["dataset", "rule"]).extra.median()
out["replay.extra.min"] = f(ex.min(), 1)
out["replay.extra.max"] = f(ex.max(), 1)
out["replay.extra.minrule"] = f(ex.drop("min", level="rule").max(), 1)
out["replay.ntargets"] = str(uc.groupby("dataset").target.nunique().max())
out["replay.R"] = str(int(uc.R.max()))

# --- n-sweep
ns = pd.read_csv(CL / "robust_nsweep.csv")
for r in ns[(ns.cap == "ceil") & (ns.target_rank == 5)].itertuples():
    k = f"nsweep.{'shuf' if r.shuffled else 'obs'}.{r.rule}.{r.n}"
    out[k + ".KoverN"] = f(r.K_over_n_med, 3)
    out[k + ".K"] = f(r.K_med, 1)
    out[k + ".L1"] = f(r.L1_med, 1)

# --- Condorcet existence
ce = pd.read_csv(R / "condorcet_existence.csv")
for ds, g in ce.groupby("dataset"):
    obs = g[g["draw"] == -1].iloc[0]
    d = g[g["draw"] >= 0]
    out[f"cond.{ds}.obs"] = "yes" if obs.has_winner else "no"
    out[f"cond.{ds}.draws"] = str(len(d))
    out[f"cond.{ds}.share"] = pct(d.has_winner.mean())
    out[f"cond.{ds}.share_mean_leader"] = pct(d.winner_is_mean_leader.mean())

# --- theory validation
tv = json.load(open(R / "theory_validation_summary.json"))
out["theory.cells"] = str(len(tv))
out["theory.mismatch"] = str(sum(v["n_mismatch"] for v in tv.values() if isinstance(v, dict) and "n_mismatch" in v))
out["theory.maxerr"] = f"{max(v['max_abs_err'] for v in tv.values() if isinstance(v, dict) and 'max_abs_err' in v):.1e}"

# --- g*: smallest uniform gain cap that makes first place feasible (gstar_summary)
gs = pd.read_csv(CL / "gstar_summary.csv")
GSET = {"HELM (all targets)": "helm", "OLLB census": "ollb", "OLLB 136-sample": "sample"}
for r in gs.itertuples():
    k = f"gs.{GSET[r.set]}.{r.rule}"
    out[k + ".cross"] = f(r.crossing_cap_50, 1)
    out[k + ".lo"] = f(r.crossing_lo, 1)
    out[k + ".hi"] = f(r.crossing_hi, 1)
    out[k + ".le5"] = pct(r.share_le_5)
    out[k + ".le10"] = pct(r.share_le_10)
    out[k + ".le20"] = pct(r.share_le_20)
    out[k + ".q90"] = f(r.q90, 1)
for ds in ("helm", "ollb", "sample"):
    sub = gs[gs.set.map(GSET) == ds]
    out[f"gs.{ds}.crossmin"] = f(sub.crossing_cap_50.min(), 0)
    out[f"gs.{ds}.crossmax"] = f(sub.crossing_cap_50.max(), 0)
    out[f"gs.{ds}.nrules"] = str(len(sub))
gv = pd.read_csv(CL / "gstar_validation.csv")
out["gs.valid.cells"] = f"{int(gv.n.sum()):,}".replace(",", "{,}")
out["gs.valid.dis"] = str(int(gv.disagree.sum()))
an = pd.read_csv(CL / "gstar_anchor_finetune_gains.csv")
out["gs.anchor.pairs"] = str(int(an.n_pairs.max()))
q99 = an[an["quantile"] == 99.0].iloc[0]
out["gs.anchor.q99.ifeval"] = f(q99["IFEval"], 0)
out["gs.anchor.q99.max5"] = f(max(q99[t] for t in ("BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO")), 0)
out["gs.anchor.q99.n"] = str(sum(q99[t] < gs[(gs.set == "OLLB census") & (gs.rule == "mean")].crossing_cap_50.iloc[0]
                                 for t in ("IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO")))

# --- replay on 36 targets per dataset (replay2_summary)
r2 = pd.read_csv(CL / "replay2_summary.csv")
r2 = r2[r2.band == "all"]
RUN = {"obs_s1.0": "obs1", "obs_s1.5": "obs15", "obs_s2.0": "obs2", "shrunk_s1.0": "shr", "obs_s1.0_seed1": "seed1",
       "randtargets_seed1": "rt1", "randtargets_seed2": "rt2", "randtargets_seed20261108": "rts"}
for r in r2.itertuples():
    ds, run = r.run.split("_", 1)
    k = f"r2.{ds}.{RUN[run]}.{r.rule}"
    out[k + ".p0"] = f(r.p0_median, 2)
    out[k + ".p0lo"] = f(r.p0_lo, 2)
    out[k + ".p0hi"] = f(r.p0_hi, 2)
    out[k + ".x90"] = f(r.x90_median, 1)
    out[k + ".x90lo"] = f(r.x90_lo, 1)
    out[k + ".x90hi"] = f(r.x90_hi, 1)
    out[k + ".cens"] = str(int(r.x90_censored))
for ds in ("helm", "ollb"):
    g = r2[(r2.dataset == ds) & (r2.run == f"{ds}_obs_s1.0")]
    out[f"r2.{ds}.obs1.ntar"] = str(int(g.n_targets.max()))
    out[f"r2.{ds}.obs1.R"] = str(int(g.R.max()))
    out[f"r2.{ds}.obs1.p0min"] = f(g.p0_median.min(), 2)
    out[f"r2.{ds}.obs1.p0max"] = f(g.p0_median.max(), 2)
    nm = g[g.rule != "min"]
    out[f"r2.{ds}.obs1.x90max_nomin"] = f(nm.x90_median.max(), 1)
    out[f"r2.{ds}.obs1.x90min_nomin"] = f(nm.x90_median.min(), 1)
    # sensitivity to the noise seed and to the redrawn target samples: largest change of the median p0 / x90
    base = r2[(r2.dataset == ds) & (r2.run == f"{ds}_obs_s1.0")].set_index("rule")
    alt = r2[(r2.dataset == ds) & r2.run.str.contains("seed")]
    d_p0 = alt.apply(lambda r: abs(r.p0_median - base.loc[r.rule, "p0_median"]), axis=1)
    out[f"r2.{ds}.seed.dp0max"] = f(d_p0.max(), 2)
    nb = alt[~alt.rule.isin(["min", "borda"])]
    dx = nb.apply(lambda r: abs(r.x90_median - base.loc[r.rule, "x90_median"]), axis=1)
    out[f"r2.{ds}.seed.dx90max"] = f(dx.max(), 1)
    sh = r2[(r2.dataset == ds) & (r2.run == f"{ds}_shrunk_s1.0")]
    out[f"r2.{ds}.shr.p0min"] = f(sh.p0_median.min(), 2)
    out[f"r2.{ds}.shr.p0max"] = f(sh.p0_median.max(), 2)

# --- cluster bootstrap on the OLLB census (cluster_boot)
cb = pd.read_csv(CL / "cluster_boot.csv")
ca = cb[cb.kind == "a_all"].copy()
ca = ca[(ca.naive_hi - ca.naive_lo) > 1e-9]
w = (ca.cluster_hi - ca.cluster_lo) / (ca.naive_hi - ca.naive_lo)
out["cb.width.med"] = f(w.median(), 1)
out["cb.width.min"] = f(w.min(), 1)
out["cb.width.max"] = f(w.max(), 1)
out["cb.nclusters"] = str(int(cb[cb.kind == "a_all"].n_clusters.max()))
for r in cb[cb.kind == "a_all"].itertuples():
    k = f"cb.{r.rule}.{r.statistic.replace('@', '_')}"
    out[k] = f(r.estimate, 3 if r.estimate < 2 else 1)
    out[k + ".clo"] = f(r.cluster_lo, 3 if r.estimate < 2 else 1)
    out[k + ".chi"] = f(r.cluster_hi, 3 if r.estimate < 2 else 1)
    out[k + ".nlo"] = f(r.naive_lo, 3 if r.estimate < 2 else 1)
    out[k + ".nhi"] = f(r.naive_hi, 3 if r.estimate < 2 else 1)
dr = cb[cb.kind == "b_drop_large"]
dr = dr[dr.subset.isin(["families<=10", "families<=20", "families<=50"])]
base = cb[cb.kind == "a_all"].set_index(["rule", "statistic"]).estimate
rel = dr[dr.statistic == "median_L1@ceil"].apply(lambda r: abs(r.estimate / base[(r.rule, r.statistic)] - 1), axis=1)
out["cb.drop.maxrelL1"] = f(100 * rel.max(), 1)
shr = dr[dr.statistic.str.startswith("share_feasible")].apply(lambda r: abs(r.estimate - base[(r.rule, r.statistic)]), axis=1)
out["cb.drop.maxshare"] = f(shr.max(), 2)
rat = dr[dr.statistic.str.startswith("ratio_")].apply(lambda r: abs(r.estimate - base[(r.rule, r.statistic)]), axis=1)
out["cb.drop.maxratio"] = f(rat.max(), 3)
cz = pd.read_csv(CL / "cluster_sizes.csv")
out["cb.singletons"] = str(int(cz.set_index("statistic").value["singleton clusters"]))

# --- rule-normalised and rank-matched costs (abstract_ratio_check)
ar = pd.read_csv(CL / "abstract_ratio_check.csv")
ASET = {"HELM (78 targets)": "helm", "OLLB 136-sample": "sample", "OLLB census (4495)": "ollb"}
AVIEW = {"raw L1": "raw", "L1 / rule gap": "gap", "L1 per task / rule IQR": "iqr", "raw Linf": "rawinf",
         "L1 rank-matched (target-weighted geometric mean of bin ratios)": "rm"}
for r in ar.itertuples():
    if r.view not in AVIEW:
        continue
    k = f"nr.{ASET[r.set]}.{r.rule}.{AVIEW[r.view]}"
    out[k] = f(r.ratio_to_mean, 2)
    if pd.notna(r.lo):
        out[k + ".lo"] = f(r.lo, 2)
        out[k + ".hi"] = f(r.hi, 2)

# --- seed stability of the OLLB sample (seed_stability, noise_seed_check)
ss = pd.read_csv(CL / "seed_stability.csv")
SS = {"grid (delivered)": "grid", "20261108": "s0", "1": "s1", "2": "s2"}
for r in ss.itertuples():
    k = f"ss.{SS[str(r.sample)]}.{r.rule}"
    out[k + ".ratio"] = f(r.median_ratio_L1_to_mean, 2)
    out[k + ".cheaper"] = pct(r.share_cheaper_than_mean, 1)
    out[k + ".ordonly"] = str(int(r.ord_infeasible_mean_feasible))
    out[k + ".n"] = f(r.n_targets_ceil)
    out[k + ".n10"] = str(int(r.n_targets_gain10))
for rule, g in ss.groupby("rule"):
    out[f"ss.{rule}.ratiolo"] = f(g.median_ratio_L1_to_mean.min(), 2)
    out[f"ss.{rule}.ratiohi"] = f(g.median_ratio_L1_to_mean.max(), 2)
    out[f"ss.{rule}.ordlo"] = str(int(g.ord_infeasible_mean_feasible.min()))
    out[f"ss.{rule}.ordhi"] = str(int(g.ord_infeasible_mean_feasible.max()))
    out[f"ss.{rule}.nlo"] = str(int(g.n_targets_gain10.min()))
    out[f"ss.{rule}.nhi"] = str(int(g.n_targets_gain10.max()))
    out[f"ss.{rule}.cheaperlo"] = pct(g.share_cheaper_than_mean.min(), 1)
nsc = pd.read_csv(CL / "noise_seed_check.csv")
piv = nsc.pivot_table(index=["experiment", "dataset", "rule"], columns="run", values="median_of_target_L1_median")
if piv.shape[1] == 2:
    a, b = piv.columns[0], piv.columns[1]
    dd = (piv[a] - piv[b]).abs().reset_index(name="d")
    for ds in ("helm", "ollb"):
        out[f"nsc.maxabs.{ds}"] = f(dd[dd.dataset == ds].d.max(), 1)

# --- the minimum rule and models with a zero score (min_zero_diagnostic, min_zero_bars)
mz = pd.read_csv(CL / "min_zero_diagnostic.csv")
mz = mz[(mz.rule == "min") & (mz.cap == "ceil")].set_index("view")
out["nozero.ratio_full"] = f(mz.loc["full board, all targets", "ratio_L1_to_mean"], 3)
out["nozero.ratio_removed"] = f(mz.loc["no-zero board, all targets", "ratio_L1_to_mean"], 3)
mb = pd.read_csv(CL / "min_zero_bars.csv").set_index("board")
out["nozero.share"] = pct(1 - mb.loc["no-zero board", "n_models"] / mb.loc["full board", "n_models"], 1)

# --- manifest
mf = pd.read_csv(R / "MANIFEST.csv")
out["manifest.nfiles"] = str(len(mf))
out["manifest.nunresolved"] = str(int(mf.n_unresolved_nan.fillna(0).sum()))
out["manifest.ncomplete"] = str(int((mf.status == "complete").sum()))

lines = ["% generated by paper/scripts/make_numbers.py from analysis/results; do not edit",
         "\\newcommand{\\num}[1]{\\expandafter\\ifx\\csname num@#1\\endcsname\\relax\\textbf{??}\\else\\csname num@#1\\endcsname\\fi}"]
for k, v in sorted(out.items()):
    lines.append(f"\\expandafter\\def\\csname num@{k}\\endcsname{{{v}}}")
(ROOT / "paper" / "numbers.tex").write_text("\n".join(lines) + "\n")
print(len(out), "numbers written")
