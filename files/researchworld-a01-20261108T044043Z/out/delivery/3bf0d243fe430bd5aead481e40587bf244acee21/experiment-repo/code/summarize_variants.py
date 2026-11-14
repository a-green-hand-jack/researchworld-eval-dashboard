"""Summaries of the sensitivity variants against the primary runs.
Usage: python3 code/summarize_variants.py RESULTS_DIR OUT_CSV
One long table, columns: variant, dataset, cap, rule (or weighting scheme), group (rank stratum under the mean), n (targets), feas_frac
(share of targets with a finite L1 cost; a target whose L1 solve is censored counts as not feasible here even where its K and Linf solves, or a
cap-saturated check, show it feasible, so feas_frac is a lower bound under censoring: see results/variants/copeland_top500_feasibility.csv), L1_med_feas / K_med_feas (median among feasible targets), and for variants that have a baseline
in the core tables the paired comparison on targets feasible in both: n_both, L1_ratio_med (variant / baseline, median of per-target
ratios, positive costs only), n_base (targets of the group that have a baseline value) and feas_frac_base (baseline feasible share among those
targets only; NaN when none has one: the OLLB ordinal baselines exist for the 50 best targets under the mean, so for the top-500 slice
the ordinal comparators cover ranks <= 50 only).
Variants: margin1/margin2 (eps = 1 or 2 points instead of 1e-3; baseline = core table), var_ollb_nomerge / var_ollb_top500 / var_ollb_raw
(OLLB slices or raw scores; baseline = core OLLB, same cap and rule, same target name where it exists), weights (Dirichlet(1) weights,
baseline = the uniform-weight cost of the same target in the same file), zcost (cost in units of the across-model standard deviation of
each task, ddof = 1: L1z only, no baseline).
"""
import sys, pathlib, numpy as np, pandas as pd

R = pathlib.Path(sys.argv[1]); out = sys.argv[2]
core = {"ollb": pd.read_csv(R / "core_ollb.csv"), "helm": pd.read_csv(R / "core_helm.csv")}
BINS = {"ollb": [(2, 5), (6, 10), (11, 30), (31, 100), (101, 300), (301, 10**6)], "helm": [(2, 3), (4, 5), (6, 10), (11, 20), (21, 40), (41, 10**6)]}
lab = lambda lo, hi: f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}"
rows = []

def add(variant, ds, cap, rule, s, base=None, cost="L1"):
    """s: rows of the variant (columns rank_mean, target, cost); base: baseline rows with the same targets (column `b`) or None."""
    for lo, hi in [(2, 10**6)] + BINS[ds]:
        t = s[(s.rank_mean >= lo) & (s.rank_mean <= hi)]
        if not len(t): continue
        v = t[cost].values.astype(float); f = np.isfinite(v)
        r = dict(variant=variant, dataset=ds, cap=cap, rule=rule, group="all" if lo == 2 and hi == 10**6 else lab(lo, hi), n=len(t),
                 feas_frac=f.mean(), n_censored=int(np.isnan(v).sum() + (np.isnan(t.K.values[f]).sum() if "K" in t else 0)), L1_med_feas=np.median(v[f]) if f.any() else np.nan)
        if "K" in t: r["K_med_feas"] = np.nanmedian(t.K.values[f]) if f.any() else np.nan
        if base is not None:
            b = t["b"].values.astype(float); both = f & np.isfinite(b) & (v > 0) & (b > 0)
            have = ~np.isnan(b)      # baseline exists (OLLB ordinal baselines cover only the 50 best targets; a missing one is not "infeasible")
            r["n_base"] = int(have.sum()); r["feas_frac_base"] = float(np.isfinite(b[have]).mean()) if have.any() else np.nan; r["n_both"] = int(both.sum())
            r["L1_ratio_med"] = float(np.median(v[both] / b[both])) if both.sum() else np.nan
        rows.append(r)

for f in sorted((R / "variants").glob("margin*_*.csv")):
    e, ds = f.stem.split("_"); d = pd.read_csv(f)
    for (cap, rule), s in d[d.rank_mean >= 2].groupby(["cap", "rule"]):
        b = core[ds][(core[ds].cap == cap) & (core[ds].rule == rule)].set_index("target").L1
        s = s.assign(b=s.target.map(b)); add(e + "_eps", ds, cap, rule, s, True)
for f in sorted((R / "variants").glob("var_ollb_*.csv")):
    d = pd.read_csv(f); d = d[d.rank_mean >= 2]
    for (cap, rule), s in d.groupby(["cap", "rule"]):
        b = core["ollb"][(core["ollb"].cap == cap) & (core["ollb"].rule == rule)].set_index("target").L1
        add(f.stem, "ollb", cap, rule, s.assign(b=s.target.map(b)), True)
for f in sorted((R / "variants").glob("weights_*.csv")):
    d = pd.read_csv(f); ds = d.dataset.iloc[0]
    u = d[d.scheme == "uniform"].set_index("target").L1
    for (cap, sch), s in d[(d.scheme != "uniform") & (d.rank_mean >= 2)].groupby(["cap", "scheme"]):
        add("weights", ds, cap, sch, s.assign(b=s.target.map(u)), True)
for f in sorted((R / "variants").glob("zcost_*.csv")):
    d = pd.read_csv(f); ds = d.dataset.iloc[0]
    for (cap, rule), s in d[d.rank_mean >= 2].groupby(["cap", "rule"]): add("zcost", ds, cap, rule, s, cost="L1z")
pd.DataFrame(rows).to_csv(out, index=False)
