"""Summaries of the main experiment CSVs: per rank-group medians with bootstrap CIs over targets.
Usage: python3 src/summarize.py IN_CSV OUT_PREFIX [--seed 0]
Rank groups are by the target's rank under the MEAN (rank_mean) so that all rules are compared on the same set of targets.
"""
import sys, numpy as np, pandas as pd
inp, outp = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(0)
d = pd.read_csv(inp)
bins = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
d["group"] = pd.Series([next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi) if r >= 2 else "1" for r in d.rank_mean], index=d.index)

def boot_median(v, B=1000):
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    fin = np.isfinite(v)
    if fin.mean() < 0.5: return (np.inf, np.nan, np.nan)      # more than half infeasible
    med = np.median(v)
    bs = [np.median(rng.choice(v, len(v))) for _ in range(B)]
    return med, *np.percentile(bs, [2.5, 97.5])

rows = []
for (cap, rule, g), s in d[d.group != "1"].groupby(["cap", "rule", "group"]):
    r = dict(cap=cap, rule=rule, group=g, n_targets=len(s))
    for m in ("L1", "K", "Linf"):
        if m not in s: continue
        med, lo, hi = boot_median(s[m].values); r[m + "_med"], r[m + "_lo"], r[m + "_hi"] = med, lo, hi
        r[m + "_infeasible"] = float(np.mean(~np.isfinite(s[m].values)))
    rows.append(r)
S = pd.DataFrame(rows); S.to_csv(outp + "_groups.csv", index=False)

# relative cost vs the mean rule on the same target (finite in both)
w = d.pivot_table(index=["cap", "target", "rank_mean"], columns="rule", values="L1", aggfunc="first")
if "mean" in w:
    rel = w.div(w["mean"], axis=0).replace([np.inf, -np.inf], np.nan).drop(columns="mean")
    rel = rel.reset_index(); rel["group"] = [next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi) if r >= 2 else "1" for r in rel.rank_mean]
    rel = rel[rel.group != "1"].drop(columns="rank_mean")
    rel.groupby(["cap", "group"]).median(numeric_only=True).to_csv(outp + "_relL1_vs_mean.csv")
print(S[S.cap == S.cap.iloc[0]].round(2).head(60).to_string())
