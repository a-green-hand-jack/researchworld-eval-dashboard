"""Paired rule comparisons on the same targets, restricted to targets feasible under both rules.
Usage: python3 code/paired.py CORE_CSV OUT_CSV
For every dataset x cap x ordered pair of rules (A, B) and every rank stratum (by rank under the mean, plus `all`):
  n_both = targets feasible under both rules with positive investment under both (already-first and censored targets excluded),
  n_either = targets feasible under at least one of the two (so n_both / n_either says how selective the comparison is),
  for L1 and K: the median of the per-target ratio A/B, its 95% bootstrap CI over targets (1000 draws, seed 0), and the share of
  targets where A costs strictly less than B (ties count as not cheaper).
Ratios are cost(A)/cost(B): below 1 means A is cheaper. Only pairs among the rules in RULES are reported.
"""
import sys, itertools, numpy as np, pandas as pd

inp, outp = sys.argv[1], sys.argv[2]
RULES = ["mean", "median", "min", "borda", "condorcet", "plurality", "copeland"]
rng = np.random.default_rng(0)
d = pd.read_csv(inp)
BINS = {"ollb": [(2, 5), (6, 10), (11, 30), (31, 100)], "helm": [(2, 3), (4, 5), (6, 10), (11, 20), (21, 79)]}
B = 1000

rows = []
for (ds, cap), s in d[d.rule.isin(RULES) & (d.rank_mean >= 2)].groupby(["dataset", "cap"]):
    L = s.pivot_table(index=["target", "rank_mean"], columns="rule", values="L1", aggfunc="first")
    K = s.pivot_table(index=["target", "rank_mean"], columns="rule", values="K", aggfunc="first")
    rk = L.index.get_level_values("rank_mean").values
    for a, b in itertools.permutations([r for r in RULES if r in L], 2):
        la, lb, ka, kb = (x[r].values for x in (L, K) for r in (a, b))
        ok_a, ok_b = np.isfinite(la), np.isfinite(lb)
        for g, (lo, hi) in [("all", (2, 10**6))] + [(f"{lo}-{hi}", (lo, hi)) for lo, hi in BINS[ds]]:
            m = (rk >= lo) & (rk <= hi)
            both = m & ok_a & ok_b & (la > 0) & (lb > 0)
            r = dict(dataset=ds, cap=cap, rule_a=a, rule_b=b, group=g, n_both=int(both.sum()), n_either=int((m & (ok_a | ok_b)).sum()))
            if both.sum() >= 3:
                for name, x, y in (("L1", la, lb), ("K", ka, kb)):
                    q = x[both] / y[both]
                    bs = np.median(q[rng.integers(0, len(q), (B, len(q)))], axis=1)
                    r[name + "_ratio_med"] = float(np.median(q)); r[name + "_ratio_lo"], r[name + "_ratio_hi"] = np.percentile(bs, [2.5, 97.5])
                    r[name + "_a_cheaper"] = float(np.mean(x[both] < y[both]))
            rows.append(r)
pd.DataFrame(rows).to_csv(outp, index=False)
