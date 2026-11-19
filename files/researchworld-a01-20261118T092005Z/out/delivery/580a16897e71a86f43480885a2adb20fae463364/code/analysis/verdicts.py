"""Verdicts on the pre-registered tests R1-R5 (thresholds of the Brief, rev 3) and headline.json.
usage: verdicts.py TABLES_DIR RAWDIR   reads TABLES_DIR/{price,m_effect_fit,units,units_tau,predictors}.csv and RAWDIR/r1_*.csv; writes TABLES_DIR/verdicts.csv, r1_detail.csv and headline.json.
R1 supported: p >= 80% of targets need strictly more breadth fraction k/m than the mean family at b = median B* of the mean family (sigma units of the board's granularity) AND the paired-difference CI
(cluster bootstrap by target family and by incumbent) excludes 0; partial: 60% <= p < 80% with CI excluding 0; failed otherwise.  An infeasible plan counts as breadth fraction 1 (lower bound).
R2 failed-to-find-dominance ('supported' = no dominance) iff no rule has the lowest depth for >= 90% of targets on every board.
R3 (gap sufficiency): per rule, held-out R^2 of the gap-only model; 'supported' iff the CI lower bound >= 0.9 (gap alone explains >= 90% held out, predictors empty) on both transfer directions;
  here that is the *refutation* threshold, so verdict 'failed' means the predictors are not empty.
R4 (m effect): HELM subset slope CI over ln m excludes 0 and is positive at the primary budget b=2 sigma (supported if also positive at 1 and 4 sigma, partial otherwise), failed if the primary CI includes 0 or is negative.
R5: direction of the median-type vs mean-type price identical in all four units and min Kendall tau >= 0.5: supported; identical direction, tau < 0.5: partial; direction flips: failed (unit-dependent)."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import numpy as np, pandas as pd
from stats import cluster_mean_ci
from lbprice.boards import load_helm, load_ollb, ollb_family
T, RAW = sys.argv[1], sys.argv[2]
NB = int(os.environ.get("NBOOT", 2000))
MEDT = ["median", "plurality", "copeland"]
BOARD = {"helm": "helm_mmlu", "m6raw": "ollb_bench_raw", "m39": "ollb_sub"}
rows = []


from families import fam_map


def verdict_r1(p, d):
    if p >= 0.8 and d[1] > 0: return "supported"
    if p >= 0.6 and d[1] > 0: return "partial"
    return "failed"


# ---- R1 (sigma units, b = c * median B* of the mean family)
detail = []
r1all = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RAW}/r1_*.csv"))]) if glob.glob(f"{RAW}/r1_*.csv") else pd.DataFrame(columns=["board"])
for name, r in r1all.groupby("board"):
    b, fam = fam_map(name)
    ref = "meanh" if name == "m39" else "mean"
    for c, g in r[r.objective == "breadth"].groupby("c"):
        g = g.copy(); g["kf"] = np.where(g.feasible, g.k / g.m, 1.0)
        K = g.pivot_table(index=["target", "model"], columns="rule", values="kf"); G = g.pivot_table(index=["target", "model"], columns="rule", values="gap0")
        for rule in MEDT + ["zmean"] + (["mean"] if name == "m39" else []):
            use = (G[[ref, rule]] > 0).all(axis=1)
            k = K[use]; diff = (k[rule] - k[ref]).values
            fams = [fam[i[1]] for i in k.index]
            off = np.argsort(-b["official"], kind="stable"); lead = [b["names"][off[0]] if b["names"].index(i[1]) != off[0] else b["names"][off[1]] for i in k.index]
            est = cluster_mean_ci(diff, [fams, lead], nboot=NB, seed=21)
            share = float((diff > 1e-12).mean()) if len(diff) else np.nan
            detail.append(dict(R="R1", board=BOARD[name], rule=rule, reference=ref, c=c, b_sigma=float(g.b_sigma.iloc[0]), n_targets=len(diff), share_more_breadth=share,
                               mean_diff_kfrac=est[0], ci_lo=est[1], ci_hi=est[2], n_clusters=est[3], infeasible_counted_as_1=True))
d1 = pd.DataFrame(detail)
if len(d1):
    d1.to_csv(f"{T}/r1_detail.csv", index=False)
    for (board, rule), g in d1[(d1.c == 1.0)].groupby(["board", "rule"]):
        g = g.iloc[0]
        if rule not in MEDT: continue
        rows.append(dict(R="R1", board=board, rule=f"{rule} vs {g.reference}", statistic="share of targets needing more breadth fraction (b = median B* of mean family); paired diff in k/m",
                         value=g.share_more_breadth, ci_lo=g.ci_lo, ci_hi=g.ci_hi, threshold=">=0.8 and CI>0 (supported); 0.6-0.8 (partial)", verdict=verdict_r1(g.share_more_breadth, (g.ci_lo, g.ci_lo)), detail=f"mean diff {g.mean_diff_kfrac:.3f}, n={g.n_targets}, clusters={g.n_clusters}"))

# ---- R2 no dominance (E1 prices in points)
pr = pd.read_csv(f"{T}/price.csv") if os.path.exists(f"{T}/price.csv") else None
if pr is not None:
    for (board, inc, B), g in pr[(pr.init_rank <= 30)].groupby(["board", "incumbent", "B"]):
        W = g.pivot_table(index="target", columns="rule", values="depth_star", aggfunc="first").replace(np.nan, np.inf)
        W = W[(W > 0).any(axis=1)]
        mn = W.min(axis=1); share = {r: float(((W[r] <= mn + 1e-9) & (W[r] < np.inf)).mean()) for r in W}
        top = max(share, key=share.get)
        rows.append(dict(R="R2", board=board, rule=f"lowest-depth rule: {top}", statistic=f"largest share of targets at which one rule has the lowest depth ({inc}, B={B:g} points)", value=share[top], ci_lo=np.nan, ci_hi=np.nan,
                         threshold=">=0.9 on every board (dominance)", verdict="failed" if share[top] >= 0.9 else "supported", detail="verdict 'supported' = no dominance; ties count for every tied rule"))

# ---- R3 / E4
if os.path.exists(f"{T}/predictors.csv"):
    q = pd.read_csv(f"{T}/predictors.csv"); q = q[(q.B == 100.0) & (q.model == "gap")]
    for rule, g in q.groupby("rule"):
        lo = g.ci_lo.min(); v = g.r2_heldout.min()
        rows.append(dict(R="R3", board="; ".join(f"{a}->{b}" for a, b in zip(g.fit_board, g.test_board)), rule=rule, statistic="held-out R^2 of log price on log gap (B=ceilings)", value=v, ci_lo=lo, ci_hi=g.ci_hi.max(),
                         threshold="R^2>=0.9 (gap sufficient)", verdict="failed" if lo >= 0.9 else "supported", detail="verdict 'failed' = gap alone explains >=90% (predictor contribution empty); 'supported' = gap not sufficient"))

# ---- R4
if os.path.exists(f"{T}/m_effect_fit.csv"):
    f = pd.read_csv(f"{T}/m_effect_fit.csv"); f = f[f.rule_pair.str.startswith("median-type") & (f.variant == "inf1")]
    h = f[(f.regime == "helm_subset") & (f.statistic == "slope_ratio_vs_ln_m")].set_index("B_sigma")
    if len(h):
        prim = h.loc[2.0]; pos = [bool(h.loc[b].ci_lo > 0) for b in h.index]
        v = "failed" if not prim.ci_lo > 0 else ("supported" if all(pos) else "partial")
        rows.append(dict(R="R4", board="helm_mmlu (random subsets)", rule="median-type / mean-type", statistic="slope of breadth-fraction ratio vs ln m, primary b=2 sigma", value=prim.slope, ci_lo=prim.ci_lo, ci_hi=prim.ci_hi,
                         threshold="CI excludes 0 and >0", verdict=v, detail="b=1,2,4 sigma slopes: " + ", ".join(f"{b:g}:{h.loc[b].slope:.3f} [{h.loc[b].ci_lo:.3f},{h.loc[b].ci_hi:.3f}]" for b in h.index)))
    o = f[(f.regime == "ollb_free_vs_bundled") & (f.statistic == "ratio_m39_minus_m6") & (f.rule_pair.str.contains("meanh"))].set_index("B_sigma")
    if len(o):
        prim = o.loc[2.0]
        rows.append(dict(R="R4", board="ollb (m=39 free vs m=6 bundled)", rule="median-type / mean-type", statistic="ratio at m=39 minus ratio at m=6, b=2 sigma", value=prim.slope, ci_lo=prim.ci_lo, ci_hi=prim.ci_hi,
                         threshold="CI excludes 0 and >0", verdict="supported" if prim.ci_lo > 0 else "failed", detail="two granularities only; b=1,2,4: " + ", ".join(f"{b:g}:{o.loc[b].slope:.3f} [{o.loc[b].ci_lo:.3f},{o.loc[b].ci_hi:.3f}]" for b in o.index)))

# ---- R5
if os.path.exists(f"{T}/units.csv"):
    u = pd.read_csv(f"{T}/units.csv"); tau = pd.read_csv(f"{T}/units_tau.csv")
    for (board, cap), g in u.groupby(["board", "cap"]):
        dirs = {}
        for unit, gu in g.groupby("unit"):
            med = gu[gu.rule.isin(MEDT)].median_cost.median(); mn = gu[gu.rule.isin(["mean", "zmean"])].median_cost.median(); dirs[unit] = bool(med < mn)
        t = tau[(tau.board == board) & (tau.cap == cap) & (tau.metric == "rank_by_cost")].kendall_tau.min()
        v = "failed" if len(set(dirs.values())) > 1 else ("supported" if t >= 0.5 else "partial")
        rows.append(dict(R="R5", board=board, rule=f"median-type cheaper than mean-type in each unit ({cap})", statistic="min Kendall tau of rule orderings across unit pairs", value=t, ci_lo=np.nan, ci_hi=np.nan, threshold="same direction in all units, tau>=0.5",
                         verdict=v, detail="median-type cheaper by unit: " + str(dirs)))
V = pd.DataFrame(rows); V.to_csv(f"{T}/verdicts.csv", index=False)
print(V[["R", "board", "rule", "value", "ci_lo", "ci_hi", "verdict"]].round(3).to_string())
