"""Statistical analysis of the minimum-investment results (claims C2, C4, C5 and the feasibility/censoring accounting).

Usage: python3 src/analyze.py [--B 1000] [--seed 0]      (reads results/*.csv, writes results/analysis/*.csv)

Conventions (also in results/MANIFEST.md)
* One row of an input file = one target model x cap x rule. L1 (score points), K (tasks touched), Linf (largest single jump).
  L1/K/Linf = +inf  <=>  PROVEN infeasible under the cap (feasible = 0);  NaN <=> solver time-out (censored = 1).
* Rank groups (= strata of the sampled ordinal runs) are by the target's rank under the plain mean: 2, 3-5, 6-10, 11-30, 31-100, 101-500, >500.
* design 'all'    : every model is a target (score rules).  design 'sample': ordinal rules on the rank-stratified sample
  (ranks 2..21 + 150 log-uniform in rank; seed 0).  design 'top500': the 500 best models.
* Median over a group treats infeasible targets as +inf (so it is inf when more than half are infeasible); `*_med_feas` is the median over
  feasible targets only.  All CIs are percentile bootstrap CIs over targets (resampling within the group), B and seed as given.
* Population-level rates from a stratified sample are stratum-weighted (weights = stratum size / sampled in stratum) and are flagged `weighted=1`.
"""
import sys, glob, pathlib, argparse
import numpy as np, pandas as pd
from scipy import stats

ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
R = pathlib.Path(__file__).resolve().parents[1] / "results"; OUT = R / "analysis"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(a.seed)
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 500), (501, 10**6)]
def lab(lo, hi): return f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
GROUPS = [lab(*b) for b in BINS]
def group_of(r): return next((lab(lo, hi) for lo, hi in BINS if lo <= r <= hi), "1")
NTASK = {"ollb": 6, "helm": 57, "ollb_raw": 6, "ollb_nomerge": 6, "ollb_top500": 6}
SCORE_RULES = {"mean", "geomean", "harmonic", "median", "min", "trimmed1", "pow-5", "winvstd"}


def load_main():
    parts = []
    def add(pattern, design):
        for f in sorted(glob.glob(str(R / pattern))):
            d = pd.read_csv(f); d["design"] = design; d["file"] = pathlib.Path(f).name; parts.append(d)
    add("ollb_score_*.csv", "all"); add("ollb_ordinal_*.csv", "sample"); add("ollb_plurality_sample.csv", "sample")
    add("ollb_plurality_top500.csv", "top500"); add("helm_main.csv", "all"); add("helm_trimmed.csv", "all")
    add("ollb_powmeans_weighted.csv", "all"); add("helm_powmeans_weighted.csv", "all")
    d = pd.concat(parts, ignore_index=True).drop_duplicates(["dataset", "design", "cap", "rule", "target"])
    d["group"] = [group_of(r) for r in d.rank_mean]
    for m in ("L1", "K", "Linf"):
        d[m] = pd.to_numeric(d[m], errors="coerce")
    return d[d.group != "1"]


def weighted_summary(w):
    """Weighted means: per (dataset, cap, group) the spread over the 20 Dirichlet(1) weight draws of the group-median L1 (and infeasible rate);
    `winvstd` (weights 1/std per task) is reported on its own row."""
    rows = []
    for (ds, cap, g), s in w.groupby(["dataset", "cap", "group"]):
        per = s[s.rule.str.startswith("wdir")].groupby("rule").agg(L1_med=("L1", "median"), K_med=("K", "median"), infeas=("feasible", lambda x: 1 - x.mean()))
        r = dict(dataset=ds, cap=cap, group=g, n_targets=int(s.target.nunique()), n_weight_draws=len(per))
        for m in ("L1_med", "K_med", "infeas"):
            r[f"{m}_min"], r[f"{m}_p50"], r[f"{m}_max"] = per[m].min(), per[m].median(), per[m].max()
        u = s[s.rule == "winvstd"]
        r.update(winvstd_L1_med=u.L1.median(), winvstd_K_med=u.K.median(), winvstd_infeas=1 - u.feasible.mean())
        rows.append(r)
    return pd.DataFrame(rows)


def boot(v, fn, B=None):
    """percentile bootstrap CI over targets; fn is np.median (vectorised over rows) or any callable on a 1-d array"""
    v = np.asarray(v, float); B = B or a.B
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    est = fn(v); idx = rng.integers(0, len(v), (B, len(v)))
    bs = np.median(v[idx], axis=1) if fn is np.median else np.array([fn(v[i]) for i in idx])
    ok = bs[~np.isnan(bs)]
    return est, *(np.percentile(ok, [2.5, 97.5], method='inverted_cdf') if len(ok) else (np.nan, np.nan))   # no interpolation: values may be +inf


def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def summarize_groups(d, pop_sizes):
    rows = []
    for (ds, des, cap, rule, g), s in d.groupby(["dataset", "design", "cap", "rule", "group"]):
        cens = s.censored.fillna(0).astype(int).values == 1
        ok = s[~cens]; feas = ok.feasible == 1
        r = dict(dataset=ds, design=des, cap=cap, rule=rule, group=g, n_targets=len(s), n_censored=int(cens.sum()),
                 n_infeasible=int((ok.feasible == 0).sum()), n_stratum_pop=pop_sizes.get((ds, g), np.nan))
        r["infeasible_rate"] = float((ok.feasible == 0).mean()) if len(ok) else np.nan
        r["infeasible_lo"], r["infeasible_hi"] = wilson(int((ok.feasible == 0).sum()), len(ok))
        for m in ("L1", "K", "Linf"):
            if m not in ok or ok[m].isna().all(): continue
            v = ok[m].values.astype(float)
            med, lo, hi = boot(v, np.median); r[f"{m}_med"], r[f"{m}_lo"], r[f"{m}_hi"] = med, lo, hi     # inf counts as +inf
            vf = v[np.isfinite(v)]
            r[f"{m}_med_feas"], r[f"{m}_feas_lo"], r[f"{m}_feas_hi"] = boot(vf, np.median) if len(vf) else (np.nan,) * 3
        rows.append(r)
    return pd.DataFrame(rows)


def pooled_rates(d, pop_sizes):
    """stratum-weighted population infeasible / feasible rates (sample designs) or plain rates (design 'all'), bootstrap within strata."""
    rows = []
    for (ds, des, cap, rule), s in d.groupby(["dataset", "design", "cap", "rule"]):
        s = s[s.censored.fillna(0) == 0]
        if des == "top500": continue
        strata = {g: x.feasible.values.astype(float) for g, x in s.groupby("group")}
        def est(sv):
            num = den = 0.0
            for g, v in sv.items():
                N = pop_sizes.get((ds, g), len(v)) if des == "sample" else len(v); num += N * v.mean(); den += N
            return num / den
        e = est(strata); bs = [est({g: v[rng.integers(0, len(v), len(v))] for g, v in strata.items()}) for _ in range(a.B)]
        rows.append(dict(dataset=ds, design=des, cap=cap, rule=rule, feasible_rate=e, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                         weighted=int(des == "sample"), n_targets=len(s)))
    return pd.DataFrame(rows)


def rank_dependence(d):
    """C4: slope of log10(L1) (and of K) on log10(rank_mean) among feasible targets, bootstrap over targets; Spearman rho."""
    rows = []
    for (ds, des, cap, rule), s in d.groupby(["dataset", "design", "cap", "rule"]):
        s = s[(s.censored.fillna(0) == 0) & (s.feasible == 1) & (s.L1 > 0) & np.isfinite(s.L1)]
        if len(s) < 8: continue
        lr = np.log10(s.rank_mean.values.astype(float))
        r = dict(dataset=ds, design=des, cap=cap, rule=rule, n_feasible=len(s), rank_min=int(s.rank_mean.min()), rank_max=int(s.rank_mean.max()))
        for m in ("L1", "K"):
            if m not in s or s[m].isna().all(): continue
            y = np.log10(s[m].values.astype(float)); ok = np.isfinite(y) & (s[m].values > 0)
            if ok.sum() < 8 or np.ptp(lr[ok]) == 0: continue
            sl = lambda idx: np.polyfit(lr[ok][idx], y[ok][idx], 1)[0]
            n = ok.sum(); est = sl(np.arange(n)); bs = [sl(rng.integers(0, n, n)) for _ in range(a.B)]
            r[f"{m}_slope_log10"], r[f"{m}_slope_lo"], r[f"{m}_slope_hi"] = est, *np.percentile(bs, [2.5, 97.5])
            rho = stats.spearmanr(lr[ok], y[ok]); r[f"{m}_spearman"] = rho.statistic; r[f"{m}_spearman_p"] = rho.pvalue
        rows.append(r)
    return pd.DataFrame(rows)


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); adj[i] = min(1, run)
    return adj


def rule_comparison(d, ref="mean"):
    """C2: paired-by-target log10 ratio of L1 (and K) of each rule to the reference rule, within rank group; Wilcoxon signed-rank, Holm per cell."""
    rows = []
    for (ds, cap, g), s in d.groupby(["dataset", "cap", "group"]):
        w = s[s.censored.fillna(0) == 0].pivot_table(index=["target", "design"], columns="rule", values="L1", aggfunc="first")
        if ref not in w: continue
        cell = []
        for rule in w.columns:
            if rule == ref: continue
            both = w[[ref, rule]].dropna(); both = both[np.isfinite(both).all(axis=1) & (both > 0).all(axis=1)]
            nb = len(both); tot = int(w[rule].notna().sum())
            r = dict(dataset=ds, cap=cap, group=g, rule=rule, ref=ref, n_targets=tot, n_both_feasible=nb)
            if nb >= 5:
                lr = np.log10(both[rule].values / both[ref].values)
                med, lo, hi = boot(lr, np.median); r.update(log10ratio_med=med, lo=lo, hi=hi, ratio_med=10 ** med)
                r["wilcoxon_p"] = stats.wilcoxon(lr).pvalue if np.any(lr != 0) else 1.0
            cell.append(r)
        if cell:
            ps = [c.get("wilcoxon_p", np.nan) for c in cell]; good = [i for i, p in enumerate(ps) if not np.isnan(p)]
            if good:
                adj = holm([ps[i] for i in good])
                for i, ap_ in zip(good, adj): cell[i]["wilcoxon_p_holm"] = ap_
            rows += cell
    return pd.DataFrame(rows)


def ordering_stability(G):
    """C2 ordering: per (dataset, cap, group) the rules sorted by median L1 (inf = more than half infeasible); Kendall tau between caps/datasets
    on the common rules; reported as one row per pair of cells with the same group."""
    rows = []
    G = G[(G.design != "top500")]
    cells = {}
    for (ds, cap, g), s in G.groupby(["dataset", "cap", "group"]):
        s = s.drop_duplicates("rule").set_index("rule"); cells[(ds, cap, g)] = s["L1_med"]
    keys = list(cells)
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            if k1[2] != k2[2]: continue
            common = cells[k1].index.intersection(cells[k2].index)
            if len(common) < 4: continue
            x, y = cells[k1][common].replace(np.inf, 1e12).values, cells[k2][common].replace(np.inf, 1e12).values
            if np.ptp(x) == 0 or np.ptp(y) == 0: continue
            t = stats.kendalltau(x, y); rows.append(dict(group=k1[2], cell1="|".join(k1[:2]), cell2="|".join(k2[:2]), n_rules=len(common), kendall_tau=t.statistic, p=t.pvalue))
    return pd.DataFrame(rows)


def targeted_vs_uniform(d):
    """C5: L1 / (n * Linf): cost of the optimal targeted raise relative to the uniform raise by Linf on all n tasks (<= 1 by construction)."""
    rows = []
    for (ds, des, cap, rule, g), s in d.groupby(["dataset", "design", "cap", "rule", "group"]):
        s = s[(s.censored.fillna(0) == 0) & (s.feasible == 1) & (s.L1 > 0) & (s.Linf > 0) & np.isfinite(s.L1) & np.isfinite(s.Linf)]
        if len(s) < 5: continue
        ratio = (s.L1 / (NTASK[ds] * s.Linf)).values
        med, lo, hi = boot(ratio, np.median)
        rows.append(dict(dataset=ds, design=des, cap=cap, rule=rule, group=g, n=len(s), ratio_med=med, lo=lo, hi=hi, ratio_max=ratio.max(), n_tasks=NTASK[ds]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = load_main()
    WD = d[d.rule.str.startswith("wdir") | (d.rule == "winvstd")]; d = d[~d.rule.str.startswith("wdir") & (d.rule != "winvstd")]
    weighted_summary(WD).to_csv(OUT / "weighted_means.csv", index=False)
    pop = {}
    for ds in ("ollb", "helm"):
        full = d[(d.dataset == ds) & (d.design == "all")].drop_duplicates("target")
        pop.update({(ds, g): int((full.group == g).sum()) for g in GROUPS})
    print("rows", len(d), d.groupby(["dataset", "design"]).size().to_dict(), flush=True)
    G = summarize_groups(d, pop); G.to_csv(OUT / "summary_groups.csv", index=False); print("groups", len(G), flush=True)
    P = pooled_rates(d, pop); P.to_csv(OUT / "pooled_feasibility.csv", index=False)
    rd = rank_dependence(d); rd.to_csv(OUT / "rank_dependence.csv", index=False)
    rc = rule_comparison(d); rc.to_csv(OUT / "rule_comparison_vs_mean.csv", index=False)
    os_ = ordering_stability(G); os_.to_csv(OUT / "ordering_stability.csv", index=False)
    tv = targeted_vs_uniform(d); tv.to_csv(OUT / "targeted_vs_uniform.csv", index=False)
    cen = d.groupby(["dataset", "design", "cap", "rule"]).agg(n=("censored", "size"), censored=("censored", "sum"), cpu_s=("cpu_s", "sum")).reset_index()
    cen["censored_share"] = cen.censored / cen.n; cen.to_csv(OUT / "censoring_and_cpu.csv", index=False)
    print("written", sorted(p.name for p in OUT.glob("*.csv")))
