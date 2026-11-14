"""Merge the shards of code/ordinal_sample.py and summarise (issue #11).
Usage: python3 code/summarize_ordinal_sample.py   -> results/ordinal_sample/sample_all.csv, summary_status.csv, summary_costs.csv, paired_vs_mean.csv
The `all` rows pool four equal-size strata: their share and interval describe those targets only, not the board's models (no exchangeability assumption); use per-stratum counts. Status counts keep censored / feasible / infeasible apart; feasible shares use the targets that were decided (not censored) and are shown with the exact
(Clopper-Pearson) 95% interval. Cost medians are over feasible targets and are read with the feasible share; bootstrap 95% CIs (1000 draws, seed 0) over
targets. paired_vs_mean: ratio of the rule's L1 (K) to the mean rule's, same targets and cap, targets feasible under both (mean costs from results/core_ollb.csv);
the mean rule's feasibility on the same targets is reported beside it, because the pairs are selected."""
import glob, pathlib
import numpy as np, pandas as pd
from scipy.stats import beta
root = pathlib.Path(__file__).resolve().parents[1]; d = root / "results" / "ordinal_sample"
s = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(d / "shards" / "sample_*.csv")))], ignore_index=True)
s = s.sort_values(["cap", "rule", "rank_mean"]).reset_index(drop=True); s.to_csv(d / "sample_all.csv", index=False)
rng = np.random.default_rng(0)
def cp(k, n):
    return (np.nan, np.nan) if n == 0 else (beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0, beta.ppf(0.975, k + 1, n - k) if k < n else 1.0)
def bci(x):
    x = np.asarray(x, float); return np.percentile(np.median(x[rng.integers(0, len(x), (1000, len(x)))], axis=1), [2.5, 97.5]) if len(x) else (np.nan, np.nan)
rows = []
for (cap, rule), g in s.groupby(["cap", "rule"]):
    for st, h in [("all", g)] + list(g.groupby("stratum", sort=False)):
        c = h.status.value_counts(); n = len(h); cens = int(c.get("censored", 0) + c.get("censored_K", 0)); dec = n - cens
        feas = int(c.get("ok", 0) + c.get("already_first", 0)); lo, hi = cp(feas, dec)
        rows.append(dict(cap=cap, rule=rule, stratum=st, n=n, n_feasible=feas, n_infeasible_screen=int(c.get("infeasible_screen", 0)), n_infeasible_milp=int(c.get("infeasible_milp", 0)),
                         n_censored=cens, n_already_first=int(c.get("already_first", 0)), feasible_share_of_decided=feas / dec if dec else np.nan, share_lo=lo, share_hi=hi,
                         rank_min=int(h.rank_mean.min()), rank_max=int(h.rank_mean.max())))
pd.DataFrame(rows).to_csv(d / "summary_status.csv", index=False)
rows = []
for (cap, rule), g in s.groupby(["cap", "rule"]):
    for st, h in [("all", g)] + list(g.groupby("stratum", sort=False)):
        f = h[h.status == "ok"]
        for m in ("L1", "K", "Linf"):
            if len(f):
                lo, hi = bci(f[m]); rows.append(dict(cap=cap, rule=rule, stratum=st, measure=m, n_feasible=len(f), median=f[m].median(), ci_lo=lo, ci_hi=hi, min=f[m].min(), max=f[m].max()))
pd.DataFrame(rows).to_csv(d / "summary_costs.csv", index=False)
core = pd.read_csv(root / "results" / "core_ollb.csv"); core = core[core.rule == "mean"][["cap", "target", "L1", "K", "status"]].rename(columns={"L1": "L1_mean", "K": "K_mean", "status": "status_mean"})
m = s[s.status == "ok"].merge(core, on=["cap", "target"], how="left")
rows = []
for (cap, rule), g in s.groupby(["cap", "rule"]):
    mm = m[(m.cap == cap) & (m.rule == rule)]; both = mm[np.isfinite(mm.L1_mean) & (mm.L1_mean > 0)]
    allg = g.merge(core, on=["cap", "target"], how="left")
    r = dict(cap=cap, rule=rule, n_sample=len(g), n_rule_feasible=len(mm), n_mean_feasible_on_sample=int(np.isfinite(allg.L1_mean).sum()), n_both=len(both))
    for ms, lab in (("L1", "L1"), ("K", "K")):
        if len(both):
            x = (both[ms] / both[ms + "_mean"]).values; lo, hi = bci(x)
            r.update({f"{lab}_ratio_median": np.median(x), f"{lab}_ratio_lo": lo, f"{lab}_ratio_hi": hi, f"{lab}_rule_cheaper_share": float((x < 1).mean()), f"{lab}_rule_mean_median": both[ms].median(), f"{lab}_mean_rule_median": both[ms + "_mean"].median()})
    rows.append(r)
pd.DataFrame(rows).to_csv(d / "paired_vs_mean.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(pd.read_csv(d / "summary_status.csv").query("stratum=='all'").round(3).to_string()); print(pd.read_csv(d / "paired_vs_mean.csv").round(3).to_string())
