"""Paired per-target comparison of the rule/mean L1 ratio under normalised vs raw OLLB scores (cap ceil).
For each target: ratio_norm = L1_rule/L1_mean on the normalised scores, ratio_raw on raw accuracies, diff = ratio_raw - ratio_norm
(targets with L1_mean > 0 and both costs finite). Per group: medians of the two ratios, the median paired difference and the
share of targets with diff > 0, with 95% percentile bootstrap CIs over targets. Groups by the target's rank under the mean rule on the
NORMALISED scores (the leaderboard's own ordering, ex ante); 'top10' = ranks 2-11 as elsewhere, the others are disjoint bands. The same
table with groups by the raw-score mean rank is written with group_basis = raw.
Usage: python3 src/raw_vs_norm_paired.py NORM_CSV RAW_CSV OUT_PER_TARGET OUT_SUMMARY [CAP ceil]"""
import sys, numpy as np, pandas as pd
nf, rf, o1, o2 = sys.argv[1:5]; cap = sys.argv[5] if len(sys.argv) > 5 else "ceil"
rng = np.random.default_rng(0)
def wide(f):
    d = pd.read_csv(f); d = d[d.cap == cap]
    L = d.pivot_table(index="target", columns="rule", values="L1", aggfunc="first")
    return L, d[d.rule == "mean"].set_index("target").rank_mean
Ln, rn = wide(nf); Lr, rr = wide(rf)
rows = []
for rule in ["median", "min", "geomean", "harmonic"]:
    t = Ln.index.intersection(Lr.index)
    rows.append(pd.DataFrame(dict(target=t, rule=rule, rank_norm=rn[t].values, rank_raw=rr[t].values,
        L1_mean_norm=Ln.loc[t, "mean"].values, L1_mean_raw=Lr.loc[t, "mean"].values, L1_rule_norm=Ln.loc[t, rule].values, L1_rule_raw=Lr.loc[t, rule].values)))
P = pd.concat(rows, ignore_index=True)
with np.errstate(divide="ignore", invalid="ignore"):
    P["ratio_norm"] = P.L1_rule_norm / P.L1_mean_norm; P["ratio_raw"] = P.L1_rule_raw / P.L1_mean_raw
P["diff_raw_minus_norm"] = P.ratio_raw - P.ratio_norm
P.to_csv(o1, index=False)
def groups(rank):
    g = {"top10": (2, 11), "2-10": (2, 10), "11-30": (11, 30), "31-100": (31, 100), ">100": (101, 10**6)}
    return {k: (rank >= lo) & (rank <= hi) for k, (lo, hi) in g.items()}
def ci(v, f, B=2000):
    bs = [f(rng.choice(v, len(v))) for _ in range(B)]; return np.percentile(bs, [2.5, 97.5])
out = []
for basis, col in (("norm", "rank_norm"), ("raw", "rank_raw")):
    for rule, s in P.groupby("rule"):
        for gname, m in groups(s[col]).items():
            x = s[m.values]; x = x[np.isfinite(x.ratio_norm) & np.isfinite(x.ratio_raw)]
            if len(x) < 2: continue
            r = dict(group_basis=basis, rule=rule, group=gname, n_targets=len(x))
            for name, v, f in (("ratio_norm_med", x.ratio_norm.values, np.median), ("ratio_raw_med", x.ratio_raw.values, np.median),
                               ("diff_med", x.diff_raw_minus_norm.values, np.median), ("share_raw_higher", (x.diff_raw_minus_norm.values > 0).astype(float), np.mean)):
                r[name] = f(v); r[name + "_lo"], r[name + "_hi"] = ci(v, f)
            out.append(r)
S = pd.DataFrame(out); S.to_csv(o2, index=False)
print(S[S.group_basis == "norm"][["rule", "group", "n_targets", "ratio_norm_med", "ratio_raw_med", "diff_med", "diff_med_lo", "diff_med_hi", "share_raw_higher"]].round(3).to_string())
