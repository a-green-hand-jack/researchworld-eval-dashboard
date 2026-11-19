"""Write numbers.tex: every number quoted in the paper text, read from experiment/results/tables.

usage: python3 make_numbers.py TABLES_DIR OUT.tex
"""
import sys
import numpy as np
import pandas as pd

tab, out = sys.argv[1], sys.argv[2]
b = pd.read_csv(f"{tab}/budget_curve.csv")
sl = pd.read_csv(f"{tab}/slopes.csv")
st = pd.read_csv(f"{tab}/standards.csv")
ad = pd.read_csv(f"{tab}/adequacy.csv")
cm = pd.read_csv(f"{tab}/compute_matched.csv")
dg = pd.read_csv(f"{tab}/diagnostic.csv")
cells = pd.read_csv(f"{tab}/cells.csv")

M = {}
def rng(name, x, f="{:.2f}"):
    M[name + "Lo"] = f.format(x.min()); M[name + "Hi"] = f.format(x.max())

M["nCells"] = str(len(cells))
M["acsEmpModels"] = ", ".join(sorted(cells[cells.dataset == "acs_emp"].model)); M["nAcsEmp"] = str((cells.dataset == "acs_emp").sum())
M["nDatasets"] = str(cells.dataset.nunique())
sl = sl[sl.scope == "global"]
rng("slopeKernel", sl[sl.explainer == "kernel"].slope)
rng("slopePerm", sl[sl.explainer == "perm"].slope)
for e, tag in (("kernel", "K"), ("perm", "P")):
    x = b[b.explainer == e]
    first = x[x.budget_idx == 0]
    last = x.loc[x.groupby(["dataset", "model"]).budget_idx.idxmax()]
    rng(f"matchSmall{tag}", first.match_ref_k3)
    rng(f"signflipSmall{tag}", first.signflip_k3, "{:.3f}")
    rng(f"matchLarge{tag}", last.match_ref_k3)
    rng(f"matchOneSmall{tag}", first.match_ref_k1)
    rng(f"matchFiveSmall{tag}", first.match_ref_k5)
    rng(f"matchFiveLarge{tag}", last.match_ref_k5)
    a = ad[(ad.explainer == e) & (ad.k == 3) & (ad.tau == 0.9)]
    rng(f"adeqSmall{tag}", a[a.budget_idx == 0].frac_adequate)
    rng(f"adeqLarge{tag}", a.loc[a.groupby(["dataset", "model"]).budget_idx.idxmax()].frac_adequate)
s3 = st[st.k == 3]
for name, key in (("retrain", "retrain"), ("bgFifty", "bg_B50"), ("bgTwoHundred", "bg_B200"), ("nullInst", "null_other_instance"), ("nullSub", "null_random_subsets")):
    rng("std" + name, s3[s3.standard == key].pair_match)
M["nCfourAll"] = str(int((cm.c == 4).sum()))
m = cm[(cm.compute_ratio > 0.9) & (cm.compute_ratio < 1.1) & (cm.c == 4)]
M["cfiveN"] = str(len(m))
for e, tag in (("kernel", "K"), ("perm", "P")):
    z = m[m.explainer == e]
    M[f"cfiveN{tag}"] = str(len(z))
    M[f"cfiveWorse{tag}"] = str(int((z.match_diff_k3_hi < 0).sum()))
    M[f"cfiveBetter{tag}"] = str(int((z.match_diff_k3_lo > 0).sum()))
    M[f"cfiveMean{tag}"] = "{:+.3f}".format(z.match_diff_k3.mean())
for d, tag in (("own_margin", "Margin"), ("repeat_z", "RepeatZ"), ("repeat_pmatch", "RepeatP")):
    z = dg[dg.diagnostic == d].auc
    M[f"auc{tag}Med"] = "{:.2f}".format(z.median())
    M[f"auc{tag}N"] = str(len(z))

# library-default budget, sampled regime (d > 10): min(2d+2048, 2^d-2) coalitions
dflt = b[(b.explainer == "kernel") & (b.d > 10) & (b.budget == (2 * b.d + 2048).clip(upper=2 ** b.d - 2))]
M["nDefaultCells"] = str(len(dflt))
for k, w in ((1, "One"), (3, "Three"), (5, "Five")):
    rng(f"dfltMatch{w}", dflt[f"match_ref_k{k}"])
ad_d = ad[(ad.explainer == "kernel") & (ad.k == 3) & (ad.tau == 0.9)].merge(dflt[["dataset", "model", "budget"]], on=["dataset", "model", "budget"])
rng("dfltAdeq", ad_d.frac_adequate)
rng("dfltAdeqLoCI", ad_d.lo); rng("dfltAdeqHiCI", ad_d.hi)
rng("dfltSignFlip", dflt.signflip_k3); rng("dfltNogueira", dflt.nogueira_k3)
M["dfltBudget"] = ",".join(str(int(v)) for v in sorted(dflt.budget.unique()))
sd = st[(st.k == 3) & (st.standard == "retrain") & (st.dataset.isin(cells[cells.d > 10].dataset))]
rng("stdretrainSampled", sd.pair_match)
se = st[(st.k == 3) & (st.standard == "retrain") & (st.dataset.isin(cells[cells.d <= 10].dataset))]
rng("stdretrainExact", se.pair_match)
# retrain agreement vs run-to-run agreement at the default budget (sampled regime), per cell
pm = b[(b.explainer == "kernel") & (b.d > 10) & (b.budget == (2 * b.d + 2048))][["dataset", "model", "pair_match_k3"]].merge(
    st[(st.k == 3) & (st.standard == "retrain")][["dataset", "model", "pair_match"]], on=["dataset", "model"])
M["nRetrainBelowRun"] = str(int((pm.pair_match < pm.pair_match_k3).sum())); M["nRetrainCmp"] = str(len(pm))
rng("pairDefault", pm.pair_match_k3)
try:
    l1 = pd.read_csv(f"{tab}/l1_default.csv")
    top = l1[l1.variant == "top3_changed_by_default_l1"]
    at = top[top.budget == 2088]
    rng("lOneChangedAtDefault", at.match_ref_k3)
    a0 = l1[(l1.variant == "l1_false") & (l1.budget == 2088)]; a1 = l1[(l1.variant == "l1_default") & (l1.budget == 2088)]
    rng("lOneFalseMatch", a0.match_ref_k3); rng("lOneDefaultMatch", a1.match_ref_k3)
    rng("lOneFalseErr", a0.relerr_med); rng("lOneDefaultErr", a1.relerr_med)
    big = l1[(l1.variant == "l1_default") & (l1.budget == l1.budget.max()) & (l1.dataset == "german")]
    rng("lOneDefaultErrMax", big.relerr_med)
    ae = l1[(l1.dataset == "acs_emp") & (l1.budget == l1.budget.max())]
    M["lOneEmpDefaultErr"] = f"{ae[ae.variant == 'l1_default'].relerr_med.iloc[0]:.2f}"
    M["lOneEmpFalseErr"] = f"{ae[ae.variant == 'l1_false'].relerr_med.iloc[0]:.3f}"
    M["lOneEmpChanged"] = f"{l1[(l1.dataset == 'acs_emp') & (l1.variant == 'top3_changed_by_default_l1') & (l1.budget == 2080)].match_ref_k3.iloc[0]:.3f}"
except Exception as e:
    print("l1_default.csv skipped:", e)
try:
    lg = pd.read_csv(f"{tab}/logit_reference_agreement.csv")
    rng("logitSameThree", lg[lg.k == 3].topk_same_prob_vs_logit)
    ls = pd.read_csv(f"{tab}/logit_sensitivity.csv")
    pv = ls.pivot_table(index=["dataset", "model", "explainer", "budget"], columns="output", values="match_ref_k3")
    pv["dm"] = pv["logit"] - pv["prob"]
    rng("logitMatchDiff", pv.groupby(["dataset", "model", "explainer"]).dm.mean())
    M["nLogitCells"] = str(len(lg[lg.k == 3]))
except Exception as e:
    print("logit skipped:", e)

# repeat versus enlarge at c = 2 and 8 (matched pairs, ratio within [0.9, 1.1]); pairs of core cells only
cmc = cm[~cm.dataset.str.endswith("_logit")]
for cc, w in ((2, "Two"), (4, "Four"), (8, "Eight")):
    for e, tag in (("kernel", "K"), ("perm", "P")):
        z = cmc[(cmc.c == cc) & (cmc.explainer == e) & (cmc.compute_ratio >= 0.9) & (cmc.compute_ratio <= 1.1)]
        M[f"cm{w}N{tag}"] = str(len(z))
        M[f"cm{w}Mean{tag}"] = "{:+.3f}".format(z.match_diff_k3.mean()) if len(z) else "n/a"

# single-run margin as a deployment flag, Kernel SHAP at the default budget, d > 10, pooled over cells (k = 3)
try:
    oc = pd.read_csv(f"{tab}/operating_curve.csv")
    x = oc[(oc.k == 3) & (oc.explainer == "kernel") & (oc.d > 10) & (oc.budget == 2 * oc.d + 2048) & (oc.diagnostic == "own_margin")].copy()
    for thr, w in ((0.02, "Low"), (0.05, "Mid")):
        y = x[np.isclose(x.threshold, thr)]
        n = int(y.n_inst.sum()); unrel = int(round((y.frac_unreliable_overall * y.n_inst).sum()))
        flag = int(round((y.frac_flagged * y.n_inst).sum())); acc = int(y.n_accepted.sum()); fa = int(round((y.false_adequate * y.n_accepted).sum()))
        M[f"opN{w}"] = str(n); M[f"opUnrel{w}"] = str(unrel); M[f"opFlagPct{w}"] = "{:.0f}".format(100 * flag / n)
        M[f"opAccepted{w}"] = str(acc); M[f"opFalseAdeq{w}"] = str(fa)
    M["opUnrelPct"] = "{:.1f}".format(100 * unrel / n)
except Exception as e:
    print("operating_curve skipped:", e)

# seed streams shared across cells of one dataset (Spearman correlation of run noise between two models)
try:
    sc = pd.read_csv(f"{tab}/seed_correlation.csv")
    for e, tag in (("kernel", "K"), ("perm", "P")):
        s = sc[sc.explainer == e]
        M[f"seedCorrMean{tag}"] = "{:.2f}".format(s.spearman.mean()); M[f"seedCorrMax{tag}"] = "{:.2f}".format(s.spearman.max())
        M[f"seedCorrNull{tag}"] = "{:.2f}".format(s.spearman_null.abs().max())
except Exception as e:
    print("seed_correlation skipped:", e)

# estimator share of the retrain disagreement for German (single Kernel run at 10 000 coalitions; an extrapolated estimate)
try:
    rn = pd.read_csv(f"{tab}/retrain_notes.csv")
    rn = rn[rn.noise_share_of_pair_variance.notna() & ~rn.dataset.str.endswith("_logit")]
    M["retrainNoiseSharePct"] = "{:.3f}".format(100 * rn.noise_share_of_pair_variance.max())
except Exception as e:
    print("retrain_notes skipped:", e)

# hierarchical estimates for repeat versus enlarge on the compute-matched pairs (c5_hier.csv, subset "matched")
try:
    hh = pd.read_csv(f"{tab}/c5_hier.csv")
    hh = hh[(hh.subset == "matched") & (hh.metric == "match_diff_k3")]
    for cc, w in ((2, "Two"), (4, "Four"), (8, "Eight")):
        for e, tag in (("kernel", "K"), ("perm", "P")):
            r = hh[(hh.c == cc) & (hh.explainer == e)]
            if len(r):
                r = r.iloc[0]
                M[f"hm{w}{tag}"] = "{:+.3f}".format(r.estimate); M[f"hm{w}Lo{tag}"] = "{:+.3f}".format(r.lo); M[f"hm{w}Hi{tag}"] = "{:+.3f}".format(r.hi)
                M[f"hm{w}DLo{tag}"] = "{:+.3f}".format(r.lo_dataset_cluster); M[f"hm{w}DHi{tag}"] = "{:+.3f}".format(r.hi_dataset_cluster)
                M[f"hm{w}Pairs{tag}"] = str(int(r.n_pairs)); M[f"hm{w}Cells{tag}"] = str(int(r.n_cells))
                M[f"hm{w}Fav{tag}"] = str(int(r.cells_favouring_repeat))
            else:
                M[f"hm{w}{tag}"] = "n/a"
except Exception as e:
    print("c5_hier skipped:", e)

# operating curve (summary table of the experiment delivery); single-run margin, k = 3
try:
    os_ = pd.read_csv(f"{tab}/operating_curve_summary.csv")
    os_ = os_[(os_.k == 3) & (os_["diagnostic"] == "own_margin")]
    for grp, g in (("D", "d>10 default"), ("S", "d<=10 sub-default")):
        for e, tag in (("kernel", "K"), ("perm", "P")):
            for thr, w in ((0.02, "Low"), (0.05, "Mid")):
                r = os_[os_.group.str.startswith(g) & (os_.explainer == e) & np.isclose(os_.threshold, thr)].iloc[0]
                q = f"os{grp}{tag}{w}"
                M[q + "N"] = str(int(r.n_inst)); M[q + "Flag"] = "{:.0f}".format(100 * r.frac_flagged)
                M[q + "FA"] = "{:.1f}".format(100 * r.false_adequate); M[q + "FALo"] = "{:.1f}".format(100 * r.false_adequate_lo); M[q + "FAHi"] = "{:.1f}".format(100 * r.false_adequate_hi)
                M[q + "Unrel"] = "{:.1f}".format(100 * r.frac_unreliable_overall)
except Exception as e:
    print("operating_curve_summary skipped:", e)

# German reference against enumeration
try:
    rc = pd.read_csv(f"{tab}/ref_check.csv")
    M["refN"] = str(len(rc)); M["refNModels"] = str(rc.model.nunique())
    M["refMaxRel"] = "{:.1f}".format(100 * rc.ref_vs_exact_rel.max())
    M["refTopThree"] = str(int(rc.top3_equal.sum())); M["refTopFive"] = str(int(rc.top5_equal.sum()))
except Exception as e:
    print("ref_check skipped:", e)

# retrain-subsample sensitivity on the d > 10 cells (k = 3)
try:
    rs = pd.read_csv(f"{tab}/retrain_sensitivity.csv")
    rs = rs[(rs.k == 3) & (rs.d > 10) & rs.subsample.isin(["50%", "80%", "95%"])]
    for sub, w in (("50%", "Fifty"), ("80%", "Eighty"), ("95%", "NinetyFive")):
        y = rs[rs.subsample == sub]
        M[f"rsLo{w}"] = "{:.2f}".format(y.pair_match.min()); M[f"rsHi{w}"] = "{:.2f}".format(y.pair_match.max()); M[f"rsN{w}"] = str(len(y))
except Exception as e:
    print("retrain_sensitivity skipped:", e)

# background redraws on the d > 10 cells (reduced: 3 redraws, 30 instances), k = 3
try:
    sd = pd.read_csv(f"{tab}/standards.csv")
    y = sd[(sd.standard == "bg_B50") & (sd.k == 3) & (sd.d > 10)]
    M["bgRedLo"] = "{:.2f}".format(y.pair_match.min()); M["bgRedHi"] = "{:.2f}".format(y.pair_match.max()); M["bgRedN"] = str(len(y))
    M["bgRedInst"] = str(int(y.n_inst.min()))
except Exception as e:
    print("standards skipped:", e)

with open(out, "w") as f:
    f.write("% generated by make_numbers.py from experiment/results/tables; do not edit\n")
    for k, v in M.items():
        f.write(f"\\newcommand{{\\num{k}}}{{{v}}}\n")
