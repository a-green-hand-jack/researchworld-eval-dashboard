"""Writes quoted_numbers.tex: LaTeX macros for every number quoted in the paper text, read from ../results/*.csv.
Usage: python3 quoted_numbers.py   (run from paper/; no randomness)"""
import math
import pathlib
import numpy as np
import pandas as pd

R = pathlib.Path(__file__).resolve().parent.parent / "results"
out = []


def mac(name, val, fmt="{}"):
    out.append("\\newcommand{\\%s}{%s}" % (name, fmt.format(val)))


def pct(x, d=2):
    return f"{100 * x:.{d}f}\\%"


a = pd.read_csv(R / "adv_budgets.csv")
a["ds"] = np.where(a.season.notna(), "nbaseason", a.dataset)
ok = a[a.verified & ~a.exact_tie]
mac("nVerified", int(a.verified.sum()), "{:,}".replace(",", "\\,") if False else "{}")
mac("nClaims", len(a))
mac("nExactTie", int(a.exact_tie.sum()))
mac("nSeasons", int(a[a.season.notna()].season.nunique()))
tag = dict(arena55k="Arena", mt_human="MTH", mt_gpt4="MTG", nba_all="NBA")
for d, t in tag.items():
    c1 = a[(a.dataset == d) & (a.claim_type == "C1")].iloc[0]
    mac(f"{t}ConeB", int(c1.budget)); mac(f"{t}ConeFrac", pct(c1.budget_frac_N)); mac(f"{t}ConeZ", f"{c1.z_gap:.1f}")
    mac(f"{t}ConeLev", f"{c1.budget_noise_units:.0f}"); mac(f"{t}N", int(c1.N))
    c2 = ok[(ok.dataset == d) & (ok.claim_type == "C2")]
    mac(f"{t}CtwoMed", f"{c2.budget.median():.0f}"); mac(f"{t}CtwoMin", int(c2.budget.min())); mac(f"{t}CtwoMax", int(c2.budget.max()))
    mac(f"{t}CtwoFracMed", pct(c2.budget_frac_N.median(), 3)); mac(f"{t}CtwoZMed", f"{c2.z_gap.median():.1f}")
    mac(f"{t}CtwoLowZ", int((c2.z_gap < 2).sum())); mac(f"{t}CtwoCount", len(c2))
    mac(f"{t}CtwoLowZBudMax", int(c2[c2.z_gap < 2].budget.max()) if (c2.z_gap < 2).any() else 0)
    mac(f"{t}Lev", f"{ok[(ok.dataset == d)].budget_noise_units.median():.0f}")
ns = ok[ok.season.notna()]
n1 = ns[ns.claim_type == "C1"]; n2 = ns[ns.claim_type == "C2"]
mac("NBAsConeMed", f"{n1.budget.median():.1f}"); mac("NBAsConeMax", int(n1.budget.max()))
mac("NBAsCtwoMed", f"{n2.budget.median():.0f}"); mac("NBAsCtwoQ", "{:.0f}--{:.0f}".format(*n2.budget.quantile([.25, .75])))
mac("NBAsCtwoMax", int(n2.budget.max())); mac("NBAsCtwoFracMed", pct(n2.budget_frac_N.median(), 2))
mac("NBAsCtwoZMed", f"{n2.z_gap.median():.2f}"); mac("NBAsLev", f"{ns.budget_noise_units.median():.1f}")
mac("NBAsNgames", f"{n2.N.median():.0f}")
mac("NBAsCtwoLowZ", pct((n2.z_gap < 1).mean(), 0))

# random perturbations
r = pd.read_csv(R / "random_survival.csv")
for d, t in tag.items():
    for pert, pn in [("remove", "Rem"), ("flip", "Flip")]:
        s = r[(r.dataset == d) & (r.perturbation == pert) & (r.claim_type == "C1") & (r.f == 0.5)]
        mac(f"{t}{pn}ConeHalf", f"{s.p_survive.iloc[0]:.2f}")
    s = r[(r.dataset == d) & (r.perturbation == "bootstrap") & (r.claim_type == "C1")]
    mac(f"{t}BootCone", f"{s.p_survive.iloc[0]:.2f}")
    s = r[(r.dataset == d) & (r.perturbation == "remove") & (r.claim_type == "C2") & (r.f == 0.1)]
    mac(f"{t}RemCtwoTen", f"{s.p_survive.mean():.2f}")
    s = r[(r.dataset == d) & (r.perturbation == "flip") & (r.claim_type == "C2") & (r.f == 0.1)]
    mac(f"{t}FlipCtwoTen", f"{s.p_survive.mean():.2f}")
    s = r[(r.dataset == d) & (r.perturbation == "bootstrap") & (r.claim_type == "C2")]
    mac(f"{t}BootCtwo", f"{s.p_survive.mean():.2f}")
mac("nSeeds", int(r[r.perturbation == "remove"].n_seeds.max()))

# adversarial vs random at the adversarial budget
for d, t in tag.items():
    s = a[(a.dataset == d)]
    mac(f"{t}RandFlipAtK", f"{s.rand_flip_prob_at_k.max():.2f}")

# regressions
g = pd.read_csv(R / "regression_coef.csv")
def coef(scope, model, term):
    x = g[(g.scope == scope) & (g.model == model) & (g.term == term)].iloc[0]
    return x
for scope, t in [("pooled", "Pool"), ("arena55k", "Arena"), ("nba_seasons", "NBAs")]:
    x = coef(scope, "M0 log z", "log_z")
    mac(f"slope{t}", f"{x.coef:.2f}"); mac(f"slope{t}CI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]"); mac(f"rsq{t}", f"{x.r2:.2f}"); mac(f"nreg{t}", int(x.n_claims))
x = coef("pooled", "M1 log z + log n_pair", "log_n_pair_involving"); mac("npairCoef", f"{x.coef:.2f}"); mac("npairCoefCI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")
x = coef("pooled", "M3 log z + log snr", "log_snr"); mac("snrCoef", f"{x.coef:.2f}"); mac("snrCoefCI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")
x = coef("pooled", "M3 log z + log snr", "log_z"); mac("zCoefMThree", f"{x.coef:.2f}"); mac("zCoefMThreeCI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")
for ds, t in [("dataset_mt_human", "MTH"), ("dataset_mt_gpt4", "MTG"), ("dataset_arena55k", "Arena")]:
    x = coef("pooled", "M0 log z", ds); mac(f"icpt{t}", f"{x.coef:.2f}"); mac(f"icpt{t}CI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")
x = coef("pooled", "M0 log z", "const"); mac("icptNBA", f"{x.coef:.2f}"); mac("icptNBACI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")

# method validity
m = pd.read_csv(R / "method_validity.csv")
for meth, t in [("influence_linearised_estimate", "Lin"), ("heuristic_own_wins_removal", "Own"), ("heuristic_direct_pair_removal", "Dir"),
                ("greedy_verified_unpolished", "Unpol"), ("one_shot_top_k_verified", "OneShot")]:
    for d, dt in tag.items():
        s = m[(m.dataset == d) & (m.method == meth)].ratio_to_best_verified
        mac(f"mv{t}{dt}Med", f"{s.median():.2f}" if len(s) else "--"); mac(f"mv{t}{dt}Max", f"{s.max():.2f}" if len(s) else "--")
nonba = m[m.dataset.isin(tag) & (m.method == "greedy_verified_unpolished")]
mac("mvUnpolImproved", int((nonba.ratio_to_best_verified > 1).sum())); mac("mvUnpolN", len(nonba))

# additions / relabel
ad = pd.read_csv(R / "additions.csv")
ad = ad[~ad.exact_tie]
for d, t in tag.items():
    s = ad[ad.dataset == d]
    mac(f"add{t}Med", f"{s.ratio_add_over_remove.median():.2f}"); mac(f"rel{t}Med", f"{s.ratio_relabel_over_remove.median():.2f}")
sn = ad[ad.dataset.str.match(r"nba\d{4}")]
mac("addNBAsMed", f"{sn.ratio_add_over_remove.median():.2f}"); mac("relNBAsMed", f"{sn.ratio_relabel_over_remove.median():.2f}")
mac("addAllFlipped", f"{ad.flipped_add.mean() * 100:.0f}\\%"); mac("relAllFlipped", f"{ad.flipped_relabel.mean() * 100:.0f}\\%")

_g0 = g[g.model == "M0 log z"].groupby("scope").n_claims.first()
mac("nregMTfit", int(_g0["pooled"] - _g0["nba_seasons"] - _g0["arena55k"]))

# kendall tau
t = pd.read_csv(R / "random_tau.csv")
for d, dt in tag.items():
    s = t[(t.dataset == d) & (t.perturbation == "remove") & (t.f == 0.1)]
    mac(f"tau{dt}Ten", f"{s.tau_mean.iloc[0]:.2f}")

# matched labeller (MT-Bench human vs GPT-4 on the same keys)
from scipy.stats import spearmanr
mp = pd.read_csv(R / "matched_pairs.csv")
for cmp_, t in [("mt_human_matched_all_vs_gpt4", "MA"), ("mt_human_ordmatched_vs_gpt4_ordmatched_1232keys", "MO")]:
    s = mp[mp.comparison == cmp_]
    mac(f"mt{t}SpB", f"{spearmanr(s.ref_budget, s.alt_budget_median)[0]:.2f}")
    mac(f"mt{t}SpZ", f"{spearmanr(s.ref_z, s.alt_z_median)[0]:.2f}")
    rr = s.alt_budget_median / s.ref_budget
    mac(f"mt{t}RatioMed", f"{rr.median():.2f}"); mac(f"mt{t}RatioMin", f"{rr.min():.2f}"); mac(f"mt{t}RatioMax", f"{rr.max():.2f}")
    mac(f"mt{t}Npairs", len(s)); mac(f"mt{t}Keys", "1232" if t == "MO" else "1814")
    mac(f"mt{t}BudZ", f"{(s.ref_budget / s.ref_z).median():.0f}/{(s.alt_budget_median / s.alt_z_median).median():.0f}")
ag = pd.read_csv(R / "s2_matched_agreement.csv").iloc[0]
mac("mtAgreeAll", f"{100 * ag.agree_all:.0f}\\%"); mac("mtAgreeNonTie", f"{100 * ag.agree_nontie:.0f}\\%")
mo = pd.read_csv(R / "matched_labeller.csv")
for v, t in [("mt_human_ordmatched", "H"), ("mt_gpt4_ordmatched", "G")]:
    s = mo[(mo.variant == v) & (mo.claim == "c1")].iloc[0]
    mac(f"mtOrd{t}ConeB", int(s.budget)); mac(f"mtOrd{t}ConeZ", f"{s.z:.1f}"); mac(f"mtOrd{t}N", int(s.N))


# exhaustive validation of the search (small MT-Bench human subsamples)
ex = pd.read_csv(R / "method_validity_exhaustive.csv")
xe = ex[ex.exact.notna()]; xc = ex[ex.exact.isna()]
mac("exInst", ex.groupby("m").instance.nunique().sum()); mac("exClaims", len(ex)); mac("exMs", "{}, {} and {}".format(*sorted(ex.m.unique())))
mac("exKmax", int(ex.exact_censored_above.dropna().iloc[0])); mac("exExactN", len(xe)); mac("exCensN", len(xc))
mac("exPolishEq", int((xe.greedy_polish == xe.exact).sum())); mac("exPolishBelow", int((xe.greedy_polish < xe.exact).sum()))
mac("exGreedyEqPct", f"{100 * (xe.greedy == xe.exact).mean():.1f}\\%"); mac("exOneshotEqPct", f"{100 * (xe.oneshot == xe.exact).mean():.1f}\\%")
mac("exCensMinPolish", int(xc.greedy_polish.min())); mac("exCensConsistent", int((xc.greedy_polish > xc.exact_censored_above).sum()))
mac("exLinMed", f"{(xe.lin_est / xe.exact).median():.2f}")

# controls: synthetic BT data, N-matched subsamples, Arena restricted to six models
cc = pd.read_csv(R / "control_comparison.csv").set_index("label")
def cf(lbl, col="median_frac_N"):
    return cc.loc[lbl, col]
for lbl, t in [("syn arena55k N=57477", "SynArena"), ("syn mt_human N=3355", "SynMTH"), ("syn mt_gpt4 N=2400", "SynMTG"), ("syn nba_all N=59124", "SynNBA"),
               ("real arena55k", "RealArena"), ("real mt_human", "RealMTH"), ("real mt_gpt4", "RealMTG"), ("real nba_all", "RealNBA"),
               ("sub arena55k N=3355", "SubArenaMTHN"), ("sub arena55k N=1367", "SubArenaSmall"), ("sub arena55k N=20000", "SubArenaBig"),
               ("sub mt_human N=1367", "SubMTHSmall"), ("sub nba_all N=3355", "SubNBAMTHN"),
               ("arena6 arena55k N=1367", "ArenaSixN"), ("arena6 arena55k N=683", "ArenaSixHalf")]:
    mac(f"ctl{t}B", f"{cf(lbl, 'median_budget'):g}"); mac(f"ctl{t}Frac", pct(cf(lbl), 2)); mac(f"ctl{t}Z", f"{cf(lbl, 'median_z'):.1f}")
mac("ctlSynSeasonsMed", f"{cc[cc.index.str.match(r'syn nba19|syn nba20')].median_budget.median():.0f}")
mac("ctlSynSeasonsFracMed", pct(cc[cc.index.str.match(r'syn nba19|syn nba20')].median_frac_N.median(), 2))

# ablations
ab = pd.read_csv(R / "ablations_summary.csv").set_index(["variant", "dataset"])
def av(v, d, col="median_budget"):
    return ab.loc[(v, d), col]
for v, vt in [("baseline", "Base"), ("drop_ties", "NoTie"), ("lam=0.01", "LamLo"), ("lam=100.0", "LamHi")]:
    for d, t in [("arena55k", "Arena"), ("mt_human", "MTH"), ("mt_gpt4", "MTG"), ("nba_all", "NBA")]:
        if (v, d) in ab.index:
            mac(f"ab{vt}{t}B", f"{av(v, d):.0f}")
            mac(f"ab{vt}{t}CI", "{:.2f}\\%--{:.2f}\\%".format(100 * av(v, d, 'ci_lo'), 100 * av(v, d, 'ci_hi')))
mac("abAllSixtyfourB", f"{av('elig=all64', 'arena55k'):.0f}"); mac("abAllSixtyfourN", int(av('elig=all64', 'arena55k', 'n_claims')))
mac("abEligThousandB", f"{av('elig=n>=1000', 'arena55k'):.0f}"); mac("abEligThousandN", int(av('elig=n>=1000', 'arena55k', 'n_claims')))
mac("abHomeNBAB", f"{av('home_param', 'nba_all_home'):.0f}")
hs = ab.loc["home_param"].drop("nba_all_home"); hb = ab.loc["baseline"].loc["nba_seasons"]
mac("abHomeSeasonsMed", f"{ab.loc['home_param'].drop('nba_all_home').median_budget.median():.1f}")
mac("abPlayoffsSeasonsMed", f"{av('playoffs_incl', 'nba_seasons'):.0f}"); mac("abBaseSeasonsMed", f"{av('baseline', 'nba_seasons'):.0f}")


# ---- second round (s5_*): intervals, cluster z, noise-equivalent and constrained budgets, published-output claims, estimators, first-order prediction, windows
tag4 = dict(arena55k="Arena", mt_human="MTH", mt_gpt4="MTG", nba_all="NBA")
bi = pd.read_csv(R / "s5_budget_intervals.csv").set_index(["dataset", "statistic"])
for d, t in tag4.items():
    for st, sn in [("c1", "Cone"), ("median_c2", "Ctwo")]:
        x = bi.loc[(d, st)]
        mac(f"bi{t}{sn}Lo", f"{math.floor(x.lo95)}"); mac(f"bi{t}{sn}Hi", f"{math.ceil(x.hi95)}"); mac(f"bi{t}{sn}Base", f"{x.base_budget:.0f}")
        mac(f"bi{t}{sn}Range", f"{math.floor(x.lo95)}--{math.ceil(x.hi95)}")
mac("biResamplesArena", int(bi.loc[("arena55k", "c1")].resamples)); mac("biResamplesMT", int(bi.loc[("mt_human", "c1")].resamples))
zs = pd.read_csv(R / "s5_z_shares.csv").set_index("dataset")
for d, t in tag4.items():
    x = zs.loc[d]
    mac(f"zsh{t}Iid", pct(x.share_z_lt1_iid, 0)); mac(f"zsh{t}Clu", pct(x.share_z_lt1_cluster, 0))
    mac(f"zsh{t}MedIid", f"{x.median_z_iid:.1f}"); mac(f"zsh{t}MedClu", f"{x.median_z_cluster:.1f}"); mac(f"zsh{t}SeRatio", f"{x.median_se_ratio:.2f}")
x = zs.loc["nba_seasons"]
mac("zshNBAsIid", pct(x.share_z_lt1_iid, 0)); mac("zshNBAsClu", pct(x.share_z_lt1_cluster, 0)); mac("zshNBAsMedClu", f"{x.median_z_cluster:.2f}")
mac("zshArenaTwoIid", pct(zs.loc["arena55k"].share_z_lt2_iid, 0))
for scope, t in [("pooled", "Pool"), ("arena55k", "Arena"), ("nba_seasons", "NBAs")]:
    x = coef(scope, "M0c log z_cluster", "log_zc")
    mac(f"slopeClu{t}", f"{x.coef:.2f}"); mac(f"slopeClu{t}CI", f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]")

# noise-equivalent budget and constrained adversary (medians over adjacent-pair claims)
nz = pd.read_csv(R / "s5_noise.csv"); cn = pd.read_csv(R / "s5_constrained.csv")
rm = pd.read_csv(R / "budgets_remove.csv")[["unit", "claim", "budget"]].rename(columns={"budget": "b_rem"})
adq = pd.read_csv(R / "additions.csv")
def grp_of(u):
    return "nba_seasons" if (len(u) == 7 and u.startswith("nba") and u[3:].isdigit()) else u
for df in (nz, cn, rm):
    df["g"] = df.unit.map(grp_of)
m2 = rm.merge(nz[["unit", "claim", "k_noise_05", "k_noise_50", "flip_freq_at_1pct_N"]], on=["unit", "claim"]).merge(cn[["unit", "claim", "budget_con_add", "budget_con_relabel"]], on=["unit", "claim"], how="left")
m2 = m2[m2.claim.str.startswith("c2") & (m2.b_rem > 0)]
for d, t in {**tag4, "nba_seasons": "NBAs"}.items():
    x = m2[m2.g == d]
    mac(f"nz{t}Med", f"{x.k_noise_05.median():.0f}"); mac(f"nz{t}Ratio", f"{(x.k_noise_05 / x.b_rem).median():.0f}")
    mac(f"nz{t}RatioMin", f"{(x.k_noise_05 / x.b_rem).min():.0f}"); mac(f"nz{t}Never", pct(x.k_noise_05.isna().mean(), 0))
    mac(f"nz{t}Half", pct(x.k_noise_50.isna().mean(), 0))
    mac(f"con{t}Add", f"{x.budget_con_add.median():.0f}"); mac(f"con{t}Rel", f"{x.budget_con_relabel.median():.0f}")
    mac(f"con{t}RatioAdd", f"{(x.budget_con_add / x.b_rem).median():.2f}"); mac(f"con{t}RatioRel", f"{(x.budget_con_relabel / x.b_rem).median():.2f}")
c1n = nz[(nz.claim == "c1") & nz.unit.isin(list(tag4))].set_index("unit")
for d, t in tag4.items():
    mac(f"nz{t}Cone", "never" if np.isnan(c1n.loc[d].k_noise_05) else f"{c1n.loc[d].k_noise_05:.0f}")
    mac(f"nz{t}ConeFreq", f"{c1n.loc[d].flip_freq_at_1pct_N:.2f}")

# claims on the published output
ps = pd.read_csv(R / "s5_published_summary.csv").set_index("dataset")
for d, t in {"arena55k": "Arena", "mt_human": "MTH", "mt_gpt4": "MTG", "nba_all": "NBA", "nba_seasons_sample": "NBAs"}.items():
    x = ps.loc[d]
    mac(f"pub{t}Sep", int(x.ci_separated_at_base)); mac(f"pub{t}Pairs", int(x.adjacent_pairs)); mac(f"pub{t}SepShare", pct(x.share_ci_separated, 0))
    mac(f"pub{t}Bud", f"{x.median_budget_ci_separated:.0f}"); mac(f"pub{t}Point", f"{x.median_budget_point_same_pairs:.0f}")
    mac(f"pub{t}Ratio", f"{x.median_ratio_ci_to_point:.2f}"); mac(f"pub{t}Pone", f"{x.median_p_rank1:.2f}")
    mac(f"pub{t}Cprime", f"{int(x.c1prime_holds_at_base)} of {int(x.c1prime_units)}")
mac("pubMTHCprimeBud", f"{ps.loc['mt_human'].median_c1prime_budget_holding:.0f}"); mac("pubMTGCprimeBud", f"{ps.loc['mt_gpt4'].median_c1prime_budget_holding:.0f}")

# estimator sensitivity
es = pd.read_csv(R / "s5_estimator.csv"); esr = pd.read_csv(R / "s5_estimator_rank.csv")
vtag = dict(base="Base", lam_1e_6="Unreg", drop_ties="DropTies", tie_wl="TieWL")
for d, t in tag4.items():
    for v, vt in [("base", "Base"), ("lam_1e-6", "Unreg"), ("drop_ties", "DropTies"), ("tie_wl", "TieWL")]:
        x = es[(es.dataset == d) & (es.variant == v)]
        if len(x):
            mac(f"est{t}{vt}Cone", f"{x[x.claim == 'c1'].budget.iloc[0]:.0f}"); mac(f"est{t}{vt}Ctwo", f"{x[x.claim.str.startswith('c2')].budget.median():.0f}")
        y = esr[(esr.dataset == d) & (esr.variant == v)]
        if len(y):
            mac(f"est{t}{vt}Tau", f"{y.tau_vs_base_window.iloc[0]:.2f}"); mac(f"est{t}{vt}Same", "same" if bool(y.top1_same.iloc[0]) else "different")
mac("estArenaDropTiesTop", str(esr[(esr.dataset == "arena55k") & (esr.variant == "drop_ties")].top1.iloc[0]))

# first-order prediction and out-of-sample test
oo = pd.read_csv(R / "s5_oos_summary.csv").set_index("dataset")
for d, t in {**tag4, "nba_seasons": "NBAs"}.items():
    x = oo.loc[d]
    mac(f"oos{t}Bias", f"{x.bias_logk_z:.1f}"); mac(f"oos{t}Fold", f"{np.exp(x.bias_logk_z):.0f}"); mac(f"oos{t}KhatBias", f"{x.bias_logk_khat:.2f}")
    mac(f"oos{t}KhatRmse", f"{x.rmse_logk_khat:.2f}"); mac(f"oos{t}ZRmse", f"{x.rmse_logk_z:.2f}")
    mac(f"oos{t}KhatMed", f"{x.median_khat_over_k:.2f}"); mac(f"oos{t}KhatTwo", pct(x.share_khat_within_2x, 0))
mac("oosSlope", f"{oo.loc['nba_seasons'].b:.2f}"); mac("oosSlopeCI", f"[{oo.loc['nba_seasons'].slope_boot_lo:.2f}, {oo.loc['nba_seasons'].slope_boot_hi:.2f}]")
col = pd.read_csv(R / "s5_collinearity.csv").set_index("dataset")
mac("collArena", f"{col.loc['arena55k'].r_logz_logsnr:.3f}"); mac("collNBAs", f"{col.loc['nba_seasons'].r_logz_logsnr:.2f}"); mac("collPool", f"{col.loc['pooled'].r_logz_logsnr:.2f}")

# restarts
rs = pd.read_csv(R / "s5_restarts_summary.csv")
mac("rsClaims", int(rs.claims.sum())); mac("rsPer", int(rs.restarts_per_claim.iloc[0])); mac("rsBeat", int(rs.claims_where_a_restart_beat_det.sum()))
mac("rsMaxRatio", f"{rs.max_restart_over_det.max():.2f}"); mac("rsAllEq", int(rs.claims_where_all_restarts_equal_det.sum()))

# Arena six-model control with intervals
cs = pd.read_csv(R / "s5_control_summary.csv")
x = cs[cs.statistic.str.startswith("median of 5") & (cs.side == "arena6")].iloc[0]; y = cs[cs.statistic.str.startswith("median of 5") & (cs.side == "mt_human")].iloc[0]
rt = cs[cs.statistic.str.startswith("median of 5") & cs.side.str.startswith("ratio")].iloc[0]
mac("ctlSixShare", pct(x.median_share, 2)); mac("ctlSixLo", pct(x.lo95, 1)); mac("ctlSixHi", pct(x.hi95, 1))
mac("ctlMTHSixShare", pct(y.median_share, 2)); mac("ctlMTHSixLo", pct(y.lo95, 1)); mac("ctlMTHSixHi", pct(y.hi95, 1))
mac("ctlSixRatio", f"{rt.median_share:.2f}"); mac("ctlSixRatioCI", f"[{rt.lo95:.2f}, {rt.hi95:.2f}]"); mac("ctlSixMinDet", f"{rt.min_detectable_ratio:.2f}"); mac("ctlSixDraws", int(x.draws))
rc = cs[cs.statistic.str.startswith("claim level") & cs.side.str.startswith("ratio")].iloc[0]; mac("ctlSixMinDetClaim", f"{rc.min_detectable_ratio:.2f}")

# window sweep
ws = pd.read_csv(R / "s5_window_sweep.csv")
for d, t in [("arena55k", "Arena"), ("nba_all", "NBA")]:
    for rule, rt_ in [("score", "S"), ("count", "C")]:
        for sz in sorted(ws[(ws.dataset == d) & (ws.rule == rule)]["size"]):
            x = ws[(ws.dataset == d) & (ws.rule == rule) & (ws["size"] == sz)].iloc[0]
            mac(f"win{t}{rt_}{ {10:'Ten',20:'Twenty',30:'Thirty',40:'Forty',64:'All',53:'All'}[sz]}Cone", int(x.c1)); mac(f"win{t}{rt_}{ {10:'Ten',20:'Twenty',30:'Thirty',40:'Forty',64:'All',53:'All'}[sz]}Ctwo", f"{x.median_c2:.0f}")
wp = pd.read_csv(R / "s5_window_support.csv")
x = wp[(wp.dataset == "arena55k") & (wp.rule == "score") & (wp["size"] == 20)].iloc[0]
mac("winArenaInside", pct(x.share_comparisons_both_inside, 0)); mac("winArenaTouch", pct(x.share_comparisons_touching, 0)); mac("winArenaGeDirect", int(x.adjacent_pairs_ge100_direct))

# Arena top-1 claim: margin in Elo and the runner-up
_ar = pd.read_csv(R / "s5_constrained.csv"); _c1 = _ar[(_ar.unit == "arena55k") & (_ar.claim == "c1")].iloc[0]
mac("ArenaGapElo", f"{_c1.gap_first_pair * 400 / np.log(10):.1f}")
_bs = pd.read_csv(R / "base_scores.csv"); _b = _bs[_bs.dataset == "arena55k"].sort_values("rank")
mac("ArenaLeaderN", f"{int(_b.iloc[0].n_comparisons):,}".replace(",", "{,}")); mac("ArenaRunnerN", f"{int(_b.iloc[1].n_comparisons):,}".replace(",", "{,}"))
mac("ArenaRunnerSE", f"{_b.iloc[1].se:.1f}"); mac("ArenaLeaderSE", f"{_b.iloc[0].se:.1f}")

pathlib.Path(__file__).with_name("quoted_numbers.tex").write_text("% generated by quoted_numbers.py from ../results; do not edit\n" + "\n".join(out) + "\n")
print(len(out), "macros")
