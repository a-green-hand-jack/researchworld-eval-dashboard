"""Aggregate analyses of the experiment CSVs -> results/tables/*.csv  (all bootstrap CIs: 1000 resamples, seed 0).
Usage: python3 src/analyze.py
Tables
  cheapest_rule_<ds>.csv  : per cap, share of targets (rank>=2 under the mean) for which each rule is (weakly) cheapest in L1 / K
  elasticity_<ds>.csv     : log-log OLS slope of the minimum L1 against the target's gap to the leader under the SAME rule (bootstrap over targets)
  rankslope_<ds>.csv      : log-log slope of L1 against the target's mean-rank (rank-1 offset), per rule
  spearman_<ds>.csv       : Spearman correlation between rules of L1 over common targets (do rules agree on who is cheap to push to first?)
  robust_<mode>.csv       : MC robustness (noise, task bootstrap): per rule, median of per-target medians, 2.5/97.5% of pooled draws, share of draws in which
                            each rule is cheaper than the mean rule, share infeasible
  tasksub_<cap>.csv       : median cost vs number of tasks n (task subsets), CI over draws, per rule, target rank
"""
import sys, pathlib, numpy as np, pandas as pd
from scipy.stats import spearmanr
R = pathlib.Path(__file__).resolve().parents[1] / "results"; T = R / "tables"; T.mkdir(exist_ok=True)
rng = np.random.default_rng(0)

def boot_ci(f, n, B=1000):
    s = [f(rng.integers(0, n, n)) for _ in range(B)]; return np.nanpercentile(s, [2.5, 97.5])

def load(*names):
    fs = [pd.read_csv(R / f"{n}.csv") for n in names if (R / f"{n}.csv").exists()]
    return pd.concat(fs, ignore_index=True) if fs else None

def per_dataset(tag, d):
    d = d[d.rank_mean >= 2].copy()
    # cheapest rule
    rows = []
    for (cap, ds), s in d.groupby(["cap", "dataset"]):
        for meas in ("L1", "K"):
            w = s.pivot_table(index="target_idx", columns="rule", values=meas, aggfunc="first").dropna()
            if w.empty: continue
            best = w.min(axis=1)
            for r in w.columns:
                rows.append(dict(cap=cap, dataset=ds, measure=meas, rule=r, n_targets=len(w),
                                 share_cheapest=float((w[r] <= best + 1e-9).mean()), infeasible=float((~np.isfinite(w[r])).mean())))
    pd.DataFrame(rows).to_csv(T / f"cheapest_rule_{tag}.csv", index=False)
    # medians by rank group on the targets common to all rules of that cap (the target sets of sampled runs are rank-stratified,
    # so pooled medians over a sample are not population medians; always read these by group)
    bins = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
    lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
    gm = []
    for (cap, ds), s in d.groupby(["cap", "dataset"]):
        for meas in ("L1", "K"):
            w = s.pivot_table(index=["target_idx", "rank_mean"], columns="rule", values=meas, aggfunc="first").dropna().reset_index()
            for lo, hi in bins:
                sub = w[(w.rank_mean >= lo) & (w.rank_mean <= hi)]
                if sub.empty: continue
                for r in [c for c in w.columns if c not in ("target_idx", "rank_mean")]:
                    v = sub[r].values; fin = np.isfinite(v)
                    gm.append(dict(cap=cap, dataset=ds, measure=meas, group=lab(lo, hi), rule=r, n_targets=len(sub),
                                   median=float(np.median(v)) if fin.mean() >= 0.5 else np.inf, infeasible=float((~fin).mean())))
    pd.DataFrame(gm).to_csv(T / f"group_medians_{tag}.csv", index=False)
    # elasticity & rank slope & spearman
    el, rs, sp = [], [], []
    for (cap, rule), s in d.groupby(["cap", "rule"]):
        s = s[np.isfinite(s.L1) & (s.L1 > 0) & (s.gap > 0)]
        if len(s) >= 20:
            x, y = np.log(s.gap.values), np.log(s.L1.values)
            sl = lambda i: np.polyfit(x[i], y[i], 1)[0]; lo, hi = boot_ci(sl, len(s))
            el.append(dict(cap=cap, rule=rule, n=len(s), slope=sl(np.arange(len(s))), lo=lo, hi=hi))
            x2 = np.log(s.rank_mean.values - 1 + 1); sl2 = lambda i: np.polyfit(x2[i], y[i], 1)[0]; lo, hi = boot_ci(sl2, len(s))
            rs.append(dict(cap=cap, rule=rule, n=len(s), slope=sl2(np.arange(len(s))), lo=lo, hi=hi))
    pd.DataFrame(el).to_csv(T / f"elasticity_{tag}.csv", index=False); pd.DataFrame(rs).to_csv(T / f"rankslope_{tag}.csv", index=False)
    for cap, s in d.groupby("cap"):
        w = s.pivot_table(index="target_idx", columns="rule", values="L1", aggfunc="first")
        w = w.replace([np.inf, -np.inf], np.nan)
        c = w.corr(method="spearman"); c.insert(0, "cap", cap); sp.append(c.reset_index())
    pd.concat(sp).to_csv(T / f"spearman_{tag}.csv", index=False)

for tag, names in (("helm", ["helm_main"]), ("ollb", ["ollb_closed", "ollb_score_caps", "ollb_score_emp", "ollb_ordinal_gain", "ollb_trimmed"]),
                   ("ollb_top500", ["ollb_top500"])):
    d = load(*names)
    if d is not None: per_dataset(tag, d)

# ---- Monte-Carlo robustness
for mode, f in (("noise", "helm_noise_gain10"), ("taskboot", "helm_taskboot_gain10")):
    d = load(f)
    if d is None: continue
    rows = []
    wide = d.pivot_table(index=["draw", "target"], columns="rule", values="L1", aggfunc="first")
    for rule in wide.columns:
        v = wide[rule].values; fin = np.isfinite(v)
        tm = wide[rule].groupby("target").median()
        r = dict(rule=rule, draws=int(d.draw.nunique()), median_L1=float(np.median(v[fin])) if fin.any() else np.inf,
                 q025=float(np.percentile(v[fin], 2.5)) if fin.any() else np.nan, q975=float(np.percentile(v[fin], 97.5)) if fin.any() else np.nan,
                 infeasible=float((~fin).mean()), cv_within_target=float((wide[rule].groupby("target").std() / wide[rule].groupby("target").mean()).median()))
        if rule != "mean": r["share_cheaper_than_mean"] = float((wide[rule].values < wide["mean"].values).mean())
        rows.append(r)
    pd.DataFrame(rows).to_csv(T / f"robust_{mode}.csv", index=False)

# ---- task-subset scaling
for cap in ("ceil", "gain10"):
    d = load(f"helm_tasksub_{cap}")
    if d is None: continue
    rows = []
    for (rule, n, rk), s in d.groupby(["rule", "n", "target_rank"]):
        for m in ("L1", "K"):
            v = s[m].values; fin = np.isfinite(v)
            if not fin.any(): rows.append(dict(rule=rule, n=n, target_rank=rk, measure=m, median=np.inf, lo=np.nan, hi=np.nan, infeasible=1.0)); continue
            lo, hi = boot_ci(lambda i: np.median(v[i]), len(v), 400)
            rows.append(dict(rule=rule, n=n, target_rank=rk, measure=m, median=float(np.median(v)), lo=lo, hi=hi, infeasible=float((~fin).mean())))
    pd.DataFrame(rows).to_csv(T / f"tasksub_{cap}.csv", index=False)
print("tables written:", sorted(p.name for p in T.glob("*.csv")))
