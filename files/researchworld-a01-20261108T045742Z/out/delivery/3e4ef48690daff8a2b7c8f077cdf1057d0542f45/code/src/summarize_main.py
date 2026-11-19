"""Headline summaries of the main experiments (feasibility-aware, scale-free units, bootstrap CIs over targets).
Usage: python3 src/summarize_main.py OUT_PREFIX IN_CSV [IN_CSV ...]
Units: K/n = fraction of tasks touched; L1/n = mean score-points raised per task (scores are on 0-100 per task);
Linf = largest single-task jump. Targets are grouped by their rank under the MEAN rule (the ex-ante initial rank), so every
rule is compared on the same targets. Medians are over targets for which the cap scenario makes the rule feasible; the
feasible share is reported next to them (a median is never pooled across caps). Infeasible = no raise within the cap makes the
target strictly first. NaN = solver time limit (excluded from both numerator and denominator of the feasible share).
Also writes paired ratios L1(rule)/L1(mean) (targets feasible under both) with bootstrap CI.
"""
import sys, numpy as np, pandas as pd
outp = sys.argv[1]; d = pd.concat([pd.read_csv(f) for f in sys.argv[2:]], ignore_index=True)
rng = np.random.default_rng(0)
dsets = d.dataset.unique()
n_tasks = {"helm": 57, "ollb": 6, "ollb_raw": 6, "ollb_nomerge": 6, "ollb_top500": 6}
d["n"] = d.dataset.map(n_tasks)
d["K_n"] = d.K / d.n; d["L1_n"] = d.L1 / d.n
bins = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
d["group"] = [next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi) if r >= 2 else "1" for r in d.rank_mean]
d = d[d.group != "1"]
top10 = d[(d.rank_mean >= 2) & (d.rank_mean <= 11)].copy(); top10["group"] = "top10"   # primary ex-ante target set (plan sec. 2)
d = pd.concat([d, top10], ignore_index=True)

def bmed(v, B=2000):
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan,) * 3
    med = np.median(v); bs = np.median(rng.choice(v, (B, len(v))), axis=1)
    return (med, *np.percentile(bs, [2.5, 97.5]))

rows = []
for (ds, cap, rule, g), s in d.groupby(["dataset", "cap", "rule", "group"]):
    s = s[s.L1.notna()]
    fin = np.isfinite(s.L1.values)
    r = dict(dataset=ds, cap=cap, rule=rule, group=g, n_targets=len(s), feasible=float(fin.mean()) if len(s) else np.nan)
    f = s[fin]
    for m in ("K_n", "L1_n", "Linf"):
        r[m + "_med"], r[m + "_lo"], r[m + "_hi"] = bmed(f[m].values) if len(f) else (np.nan,) * 3
    rows.append(r)
S = pd.DataFrame(rows); S.to_csv(outp + "_by_rule_group.csv", index=False)

pv = d.pivot_table(index=["dataset", "cap", "target", "group"], columns="rule", values="L1", aggfunc="first").reset_index()
rows = []
if "mean" in pv:
    for (ds, cap, g), s in pv.groupby(["dataset", "cap", "group"]):
        for rule in [c for c in pv.columns if c not in ("dataset", "cap", "target", "group", "mean")]:
            ok = s[["mean", rule]].dropna(); ok = ok[np.isfinite(ok["mean"]) & np.isfinite(ok[rule]) & (ok["mean"] > 0)]
            if len(ok) < 3: continue
            med, lo, hi = bmed((ok[rule] / ok["mean"]).values)
            rows.append(dict(dataset=ds, cap=cap, group=g, rule=rule, n_pairs=len(ok), ratio_med=med, ratio_lo=lo, ratio_hi=hi))
pd.DataFrame(rows).to_csv(outp + "_ratio_to_mean.csv", index=False)
print(S[(S.group.isin(["2", "6-10", ">100"]))].round(3).to_string())
