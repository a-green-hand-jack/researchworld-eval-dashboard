"""Summaries of the main experiment CSVs: per rank-group medians with bootstrap CIs over targets.
Columns per measure m in L1, K, Linf, L2: m_med/m_lo/m_hi (median over ALL targets of the group, inf when more than half are
infeasible, bootstrap 95% CI over targets), m_infeasible (share proven infeasible under the cap), m_censored (share NaN = solver
time limit), m_feas_med (median among feasible targets only: conditional on feasibility, so read with m_infeasible).
K_frac = K/n (share of tasks touched); L1_per_task = L1/n (average points per task).
Usage: python3 code/summarize.py IN_CSV OUT_PREFIX [--seed 0]
Rank groups are by the target's rank under the MEAN (rank_mean) so that all rules are compared on the same set of targets.
"""
import sys, numpy as np, pandas as pd
inp, outp = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(0)
d = pd.read_csv(inp)
NT = {"ollb": 6, "helm": 57, "ollb_leaf": 39, "ollb6_leafslice": 6}
bins = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
BY = sys.argv[3] if len(sys.argv) > 3 else "rank_mean"      # rank_mean: same targets for every rule; rank_rule: target's rank under the rule itself
d["group"] = pd.Series([next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi) if r >= 2 else "1" for r in d[BY].fillna(0)], index=d.index)
if BY == "rank_rule": outp = outp + "_own"

def boot_median(v, B=1000):
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    v = v[~np.isnan(v)]                                       # censored (time limit) targets are not costs
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    fin = np.isfinite(v)
    if fin.mean() < 0.5: return (np.inf, np.nan, np.nan)      # more than half infeasible
    med = np.median(v)
    bs = [np.median(rng.choice(v, len(v))) for _ in range(B)]
    return med, *np.percentile(bs, [2.5, 97.5])

rows = []
for (ds, cap, rule, g), s in d[d.group != "1"].groupby(["dataset", "cap", "rule", "group"]):
    r = dict(dataset=ds, cap=cap, rule=rule, group=g, n_targets=len(s))
    for m in ("L1", "K", "Linf", "L2"):
        if m not in s or s[m].isna().all(): continue
        med, lo, hi = boot_median(s[m].values); r[m + "_med"], r[m + "_lo"], r[m + "_hi"] = med, lo, hi
        v = s[m].values.astype(float)
        r[m + "_infeasible"] = float(np.mean(np.isinf(v))); r[m + "_censored"] = float(np.mean(np.isnan(v)))
        r[m + "_feas_med"] = float(np.median(v[np.isfinite(v)])) if np.isfinite(v).any() else np.nan
    if "K_med" in r: r["K_frac"] = r["K_med"] / NT[ds]
    if "L1_med" in r: r["L1_per_task"] = r["L1_med"] / NT[ds]
    rows.append(r)
S = pd.DataFrame(rows); S.to_csv(outp + "_groups.csv", index=False)

# relative cost vs the mean rule on the same target (finite in both)
if BY == "rank_mean": w = d.pivot_table(index=["dataset", "cap", "target", "rank_mean"], columns="rule", values="L1", aggfunc="first")
if BY == "rank_mean" and "mean" in w:
    rel = w.div(w["mean"], axis=0).replace([np.inf, -np.inf], np.nan).drop(columns="mean")
    rel = rel.reset_index(); rel["group"] = [next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi) if r >= 2 else "1" for r in rel.rank_mean]
    rel = rel[rel.group != "1"].drop(columns="rank_mean")
    rel.groupby(["dataset", "cap", "group"]).median(numeric_only=True).to_csv(outp + "_relL1_vs_mean.csv")
print(S[(S.cap == S.cap.iloc[0]) & (S.dataset == S.dataset.iloc[0])].round(2).head(60).to_string())
