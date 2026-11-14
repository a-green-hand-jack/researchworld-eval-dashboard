"""Main comparisons at noise-robust margins -> results/summary/margin_robust.csv (long format: claim, dataset, cap, scenario, statistic, group, n, value, lo, hi).
Why a margin: the main grids demand that the target beat the best rival by eps = 1e-3 rule units, which a re-draw of the evaluation noise undoes with probability 0.5-0.9 (summary/flip.csv, p_eps).
Margins used (from summary/flip.csv, uniform-strategy raise d on all tasks; extra = d95 - d_eps, median over targets of ranks 2-100): mean 1.5-1.8, geomean 1.6-2.4, median 1.6-2.5 (HELM) / 1.6-1.9 (OLLB),
Borda 0.5-1.1, min 6.0-10.6 points. Scenarios:
  eps1e-3        main grids (reference)
  eps0.1, eps1   the same margin for every rule (grids results/*_eps1e-1.csv, *_eps1e0.csv)
  rule_specific  mean and median at 2.0, min at 8.0 (roughly the extra d95 of that rule rounded up; grids *_eps2e0.csv, *_eps8e0.csv); only those three rules
The 95%-stay margin d95 itself is defined in run_flip.py only for the uniform strategy on ~40 targets per dataset, so it is not applied to every target of the grid; it is used here to choose eps.
OLLB targets: ranks 2-100 (all scenarios on the same targets). HELM: all 78 non-leaders. CIs: 95% percentile bootstrap over targets (descriptive).
Statistics: C2 median of L1(min)/L1(mean) and share of targets with min cheaper, overall and by CV tercile (cap ceil); C3 task-subset K/n by rule at n=5..57 (gain10; median K/n over feasible subsets, feasible share;
HELM, R=50 subsets per n and ranks as in c3_tasksub.csv; scenarios eps1e-3, eps0.1, eps1 only); C5 feasible share by rule at gain10 (and ceil), with the rule order.
Usage: python3 src/margin_robust.py"""
import sys, pathlib, numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyze as an
from mti import data as dt
R = an.R; OUT = an.OUT
GRIDS = {"eps1e-3": {"helm": ["helm_main.csv"], "ollb": ["ollb_score.csv"]}, "eps0.1": {"helm": ["helm_eps1e-1.csv"], "ollb": ["ollb_eps1e-1.csv"]},
         "eps1": {"helm": ["helm_eps1e0.csv"], "ollb": ["ollb_eps1e0.csv"]}}
RULE_SPEC = {"mean": "eps2e0", "median": "eps2e0", "min": "eps8e0"}
def read(f):
    d = pd.read_csv(R / f)
    if "feasible" not in d: d["feasible"] = np.isfinite(d[["L1", "K"]]).all(axis=1)
    return d
def grid(ds, scen):
    if scen == "rule_specific":
        parts = []
        for rule, suf in RULE_SPEC.items():
            f = R / f"{ds}_{suf}.csv"
            if not f.exists(): return None
            d = read(f.name); parts.append(d[d.rule == rule])
        d = pd.concat(parts)
    else:
        d = pd.concat([read(f) for f in GRIDS[scen][ds]], ignore_index=True)
    d = d[d.cap.isin(["ceil", "gain10"]) & (d.rank_mean >= 2) & (d.rank_mean <= (100 if ds == "ollb" else 10**6))]
    return d
rows = []
def add(**k): rows.append({**dict(group="all", n=np.nan, value=np.nan, lo=np.nan, hi=np.nan), **k})
SCEN = ["eps1e-3", "eps0.1", "eps1", "rule_specific"]
for ds in ("helm", "ollb"):
    X, names, tasks, meta = dt.load(ds); cv = dict(zip(names, X.std(axis=1) / X.mean(axis=1)))
    for scen in SCEN:
        d = grid(ds, scen)
        if d is None: print("missing grid", ds, scen); continue
        # C2
        s = d[(d.cap == "ceil") & d.rule.isin(["mean", "min"]) & d.feasible].pivot_table(index="target", columns="rule", values="L1", aggfunc="first").dropna()
        s = s[s["mean"] > 0].copy(); s["ratio"] = s["min"] / s["mean"]; s["cv"] = s.index.map(cv)
        s["terc"] = pd.qcut(s.cv.rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str)
        rho, p = spearmanr(s.cv, s.ratio)
        for g, t in [("all", s)] + [(f"CV {k}", s[s.terc == k]) for k in ("low", "mid", "high")]:
            v, lo, hi = an.ci(t.ratio.values, np.median); add(claim="C2", dataset=ds, cap="ceil", scenario=scen, statistic="median L1(min)/L1(mean)", group=g, n=len(t), value=v, lo=lo, hi=hi)
            v, lo, hi = an.ci((t.ratio < 1).astype(float).values, np.mean); add(claim="C2", dataset=ds, cap="ceil", scenario=scen, statistic="share min cheaper than mean", group=g, n=len(t), value=v, lo=lo, hi=hi)
        add(claim="C2", dataset=ds, cap="ceil", scenario=scen, statistic="Spearman(ratio, CV)", n=len(s), value=rho)
        # C5
        for cap in ("ceil", "gain10"):
            f = d[d.cap == cap].groupby("rule").feasible.agg(["mean", "size"])
            for rule, r in f.iterrows():
                v, lo, hi = an.ci(d[(d.cap == cap) & (d.rule == rule)].feasible.astype(float).values, np.mean)
                add(claim="C5", dataset=ds, cap=cap, scenario=scen, statistic=f"feasible share ({rule})", n=int(r["size"]), value=v, lo=lo, hi=hi)
            rules3 = [r for r in ("mean", "median", "min") if r in f.index]
            srt = sorted(rules3, key=lambda r: -f.loc[r, "mean"]); order = srt[0]
            for a_, b_ in zip(srt, srt[1:]): order += (" = " if abs(f.loc[a_, "mean"] - f.loc[b_, "mean"]) < 1e-9 else " > ") + b_
            add(claim="C5", dataset=ds, cap=cap, scenario=scen, statistic="order of mean/median/min by feasible share (= tie)", group=order)
# C3 (HELM task subsets)
for scen, f in (("eps1e-3", "helm_tasksub_gain10.csv"), ("eps0.1", "helm_tasksub_gain10_eps1e-1.csv"), ("eps1", "helm_tasksub_gain10_eps1e0.csv")):
    if not (R / f).exists(): print("missing", f); continue
    t = pd.read_csv(R / f); t["feas"] = np.isfinite(t.K)
    for n, g in t.groupby("n"):
        km = {}
        for rule, s in g.groupby("rule"):
            fin = s[s.feas]; kn = (fin.K / n).values; v, lo, hi = an.ci(kn, np.median) if len(kn) else (np.nan,) * 3; km[rule] = v
            add(claim="C3", dataset="helm", cap="gain10", scenario=scen, statistic=f"median K/n ({rule})", group=f"n={n}", n=len(s), value=v, lo=lo, hi=hi)
            add(claim="C3", dataset="helm", cap="gain10", scenario=scen, statistic=f"feasible share ({rule})", group=f"n={n}", n=len(s), value=float(s.feas.mean()))
        if "median" in km and "min" in km: add(claim="C3", dataset="helm", cap="gain10", scenario=scen, statistic="median K/n: median rule minus min rule (negative = median cheaper)", group=f"n={n}", value=km["median"] - km["min"])
out = pd.DataFrame(rows)[["claim", "dataset", "cap", "scenario", "statistic", "group", "n", "value", "lo", "hi"]]
out.to_csv(OUT / "margin_robust.csv", index=False); print(out[out.claim == "C2"].query("group=='all'").round(3).to_string()); print(out[out.statistic.str.startswith("order")].to_string())
