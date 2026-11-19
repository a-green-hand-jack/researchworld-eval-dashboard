"""Functional form of the rank dependence at cap `ceil` (external-review request #6.2).
Usage: python3 src/analyze_fits.py      (reads results/*.csv, writes results/analysis/rank_dependence_fits.csv and rank_monotonicity.csv)

For every (dataset, design, rule) at cap ceil, three forms are fitted to median L1 against rank, once on the 7 rank-group medians
(x = median rank_mean of the group's targets) and once on the target-level values (feasible targets with L1 > 0):
  power   log10 L1 = a + b log10 rank     (OLS in log space; investment ~ rank^b)
  linear  L1 = a + b rank                 (OLS)
  log     L1 = a + b ln rank              (OLS)
Fit quality is stated in a common currency: `rmse_log10` = root-mean-square of log10(L1) - log10(prediction) (predictions <= 0 count as
a failure: NaN), and `r2_L1` = R^2 on the L1 scale. `rmse_L1` = RMS error on the L1 scale. `preferred` = the form with the smallest rmse_log10 (a form that predicts L1 <= 0 somewhere has NaN and never wins);
`preferred_r2_L1` = the form with the largest R^2 on the L1 scale (dominated by the large-rank groups). The two criteria can disagree: both are written.
With 7 group points and 2 parameters per form, differences of a few hundredths in rmse_log10 are not decisive: see `margin` (second best / best).
Monotonicity: group medians (ranks 2, 3-5, 6-10, 11-30, 31-100, 101-500, >500) non-decreasing in rank?  A decrease is `within_ci` if the
bootstrap 95% intervals of the two groups' medians (summary_groups.csv) overlap.
"""
import glob, pathlib
import numpy as np, pandas as pd

R = pathlib.Path(__file__).resolve().parents[1] / "results"; OUT = R / "analysis"
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 500), (501, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
GROUPS = [lab(*b) for b in BINS]
group_of = lambda r: next((lab(lo, hi) for lo, hi in BINS if lo <= r <= hi), "1")

parts = []
for pat, des in [("ollb_score_ceil.csv", "all"), ("helm_main.csv", "all"), ("helm_trimmed.csv", "all"), ("ollb_powmeans_weighted.csv", "all"),
                 ("helm_powmeans_weighted.csv", "all"), ("ollb_ordinal_*_ceil.csv", "sample"), ("ollb_plurality_sample.csv", "sample"),
                 ("ollb_plurality_top500.csv", "top500")]:
    for f in sorted(glob.glob(str(R / pat))):
        d = pd.read_csv(f); d["design"] = des; parts.append(d)
d = pd.concat(parts, ignore_index=True); d = d[d.cap == "ceil"].drop_duplicates(["dataset", "design", "rule", "target"])
d["group"] = [group_of(r) for r in d.rank_mean]; d = d[d.group != "1"]
for m in ("L1",): d[m] = pd.to_numeric(d[m], errors="coerce")
SG = pd.read_csv(OUT / "summary_groups.csv"); SG = SG[SG.cap == "ceil"].set_index(["dataset", "design", "rule", "group"])


def fit_forms(x, y):
    """returns {form: (a, b, rmse_log10, r2_L1)} ; x rank, y L1 (> 0)"""
    out = {}
    lx, ly = np.log10(x), np.log10(y)
    for form, X, Y, back in [("power", lx, ly, lambda a, b: 10 ** (a + b * lx)),
                             ("linear", x, y, lambda a, b: a + b * x),
                             ("log", np.log(x), y, lambda a, b: a + b * np.log(x))]:
        b, a = np.polyfit(X, Y, 1); pred = back(a, b)
        rm = float(np.sqrt(np.mean((ly - np.log10(pred)) ** 2))) if (pred > 0).all() else np.nan
        r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
        out[form] = (a, b, rm, r2, float(np.sqrt(np.mean((y - pred) ** 2))), bool((pred > 0).all()))
    return out


fits, mono = [], []
for (ds, des, rule), s in d.groupby(["dataset", "design", "rule"]):
    s = s[(s.censored.fillna(0) == 0)]
    nfeas = int(np.isfinite(s.L1).sum())
    ff = s[np.isfinite(s.L1) & (s.L1 > 0)]
    # group medians over feasible targets (all targets are feasible at ceil except where a rule cannot reach first at 100)
    gm = ff.groupby("group").agg(n=("L1", "size"), L1=("L1", "median"), rank=("rank_mean", "median")).reindex(GROUPS).dropna()
    for level, x, y in [("group_median", gm["rank"].values.astype(float), gm.L1.values), ("target", ff.rank_mean.values.astype(float), ff.L1.values)]:
        if len(x) < 5 or np.ptp(x) == 0: continue
        res = fit_forms(x, y)
        score = {f: (v[2] if np.isfinite(v[2]) else np.inf) for f, v in res.items()}
        order = sorted(score, key=score.get); best = order[0]
        best_r2 = max(res, key=lambda f: res[f][3])
        margin = score[order[1]] / score[best] if np.isfinite(score[best]) and score[best] > 0 and np.isfinite(score[order[1]]) else np.nan
        for f, (a_, b_, rm, r2, rl, pos) in res.items():
            fits.append(dict(dataset=ds, design=des, rule=rule, level=level, n_points=len(x), form=f, intercept=a_, slope=b_,
                             positive_everywhere=int(pos), rmse_log10=rm, rmse_L1=rl, r2_L1=r2,
                             preferred=int(f == best and np.isfinite(score[best])), margin_second_over_best=margin if f == best else np.nan,
                             preferred_r2_L1=int(f == best_r2)))
    if len(gm) >= 4:
        v = gm.L1.values; dv = np.diff(v); viol = np.where(dv < 0)[0]
        ci_overlap = []
        for i in viol:
            g1, g2 = gm.index[i], gm.index[i + 1]
            try:
                lo1, hi1 = SG.loc[(ds, des, rule, g1), ["L1_lo", "L1_hi"]]; lo2, hi2 = SG.loc[(ds, des, rule, g2), ["L1_lo", "L1_hi"]]
                ci_overlap.append(int(max(lo1, lo2) <= min(hi1, hi2)))
            except KeyError: ci_overlap.append(-1)
        row = dict(dataset=ds, design=des, rule=rule, n_groups=len(gm), monotone=int(len(viol) == 0), n_decreases=len(viol),
                   decreases_at="; ".join(f"{gm.index[i]}->{gm.index[i+1]}" for i in viol),
                   decreases_within_ci=int(all(c == 1 for c in ci_overlap)) if len(viol) else np.nan,
                   max_drop_ratio=float(max((v[i] - v[i + 1]) / v[i] for i in viol)) if len(viol) else 0.0,
                   n_targets_by_group="/".join(str(int(n)) for n in gm.n))
        for g in GROUPS: row[f"L1_med_{g}"] = float(gm.L1.get(g, np.nan))
        mono.append(row)
F = pd.DataFrame(fits); F.to_csv(OUT / "rank_dependence_fits.csv", index=False)
M = pd.DataFrame(mono); M.to_csv(OUT / "rank_monotonicity.csv", index=False)
P = F[(F.level == "group_median") & (F.preferred == 1)]
print("group-median level, preferred form counts by dataset:\n", P.groupby(["dataset", "form"]).size().unstack(fill_value=0))
P = F[(F.level == "group_median") & (F.preferred_r2_L1 == 1)]
print("group-median level, preferred by R2 on the L1 scale:\n", P.groupby(["dataset", "form"]).size().unstack(fill_value=0))
P = F[(F.level == "target") & (F.preferred == 1)]
print("target level, preferred form counts by dataset:\n", P.groupby(["dataset", "form"]).size().unstack(fill_value=0))
print("monotone group medians:", M.groupby(["dataset", "design"]).monotone.agg(["sum", "count"]))
