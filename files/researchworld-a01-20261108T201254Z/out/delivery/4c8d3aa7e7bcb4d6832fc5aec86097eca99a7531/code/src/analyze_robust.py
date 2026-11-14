"""Robustness summaries (claim C6): evaluation noise, task bootstrap, task-subset size, data slices, tie margin / eps.
Usage: python3 src/analyze_robust.py [--seed 0] [--B 1000]       -> results/analysis/robust_*.csv
Replicate-based files carry the replicate interval itself (2.5-97.5 percentile over draws, R and seed are in the input files / MANIFEST);
paired comparisons (eps, ties) are bootstrapped over targets.
"""
import glob, pathlib, argparse
import numpy as np, pandas as pd
from scipy import stats
ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--seed", type=int, default=0); a = ap.parse_args()
R = pathlib.Path(__file__).resolve().parents[1] / "results"; OUT = R / "analysis"; OUT.mkdir(exist_ok=True); rng = np.random.default_rng(a.seed)
q = lambda v, p: float(np.percentile(v, p, method="inverted_cdf")) if len(v) else np.nan

def noise_boot():
    """per (dataset, mode, rule): L1/K over replicate draws, targets = the 10 best models after the first (fixed from the observed data).
    Per draw the cost of each target is evaluated on a perturbed matrix; `p_already_first` = share of draws where the target is already first under the rule."""
    rows, order_rows = [], []
    for f in sorted(glob.glob(str(R / "*_noise_*.csv")) + glob.glob(str(R / "*_taskboot_*.csv"))):
        ds, mode = pathlib.Path(f).name.split("_")[:2]; d = pd.read_csv(f)
        d["L1"] = pd.to_numeric(d.L1, errors="coerce")
        draws = d.draw.nunique()
        for (rule, tgt), s in d.groupby(["rule", "target"]):
            fin = s[np.isfinite(s.L1)]
            rows.append(dict(dataset=ds, mode=mode, rule=rule, target=tgt, rank_mean_obs=int(s.rank_mean_obs.iloc[0]), n_draws=len(s), p_already_first=float((s.L1 == 0).mean()),
                             p_infeasible=float(np.isinf(s.L1).mean()), L1_med=float(np.median(s.L1)), L1_lo=q(s.L1, 2.5), L1_hi=q(s.L1, 97.5),
                             K_med=float(np.median(s.K)), K_lo=q(s.K, 2.5), K_hi=q(s.K, 97.5)))
        # rule ordering per draw (median over targets of L1): how stable is the ordering of the rules?
        med = d.groupby(["draw", "rule"]).L1.median().unstack()
        rk = med.rank(axis=1, method="average"); base = med.median()
        for rule in med.columns:
            order_rows.append(dict(dataset=ds, mode=mode, rule=rule, rank_mean_over_draws=float(rk[rule].mean()), rank_lo=q(rk[rule], 2.5), rank_hi=q(rk[rule], 97.5),
                                   L1_med_of_target_medians=float(med[rule].median()), L1_lo=q(med[rule], 2.5), L1_hi=q(med[rule], 97.5)))
        top = med.median().sort_values().index
        if len(top) > 2:
            same = np.nanmean([stats.kendalltau(r.values, base.values).statistic for _, r in med.iterrows() if r.nunique() > 1])
            order_rows.append(dict(dataset=ds, mode=mode, rule="(mean Kendall tau of per-draw rule ordering vs median ordering)", rank_mean_over_draws=same))
    pd.DataFrame(rows).to_csv(OUT / "robust_noise_taskboot_targets.csv", index=False)
    pd.DataFrame(order_rows).to_csv(OUT / "robust_noise_taskboot_rule_order.csv", index=False)

def tasksub():
    rows = []
    for f in sorted(glob.glob(str(R / "*_tasksub_*.csv"))):
        ds = pathlib.Path(f).name.split("_")[0]; d = pd.read_csv(f); d["L1"] = pd.to_numeric(d.L1, errors="coerce")
        for (n, rule, rk), s in d.groupby(["n", "rule", "target_rank"]):
            rows.append(dict(dataset=ds, n=n, rule=rule, target_rank_in_subset=rk, n_draws=len(s), p_infeasible=float(np.isinf(s.L1).mean()),
                             L1_med=float(np.median(s.L1)), L1_lo=q(s.L1, 2.5), L1_hi=q(s.L1, 97.5), K_med=float(np.median(s.K)), K_lo=q(s.K, 2.5), K_hi=q(s.K, 97.5),
                             L1_per_task_med=float(np.median(s.L1 / n)), gap_own_med=float(np.median(s.gap_own))))
    T = pd.DataFrame(rows); T.to_csv(OUT / "robust_tasksub.csv", index=False)
    sl = []
    for (ds, rule, rk), s in T[np.isfinite(T.L1_med) & (T.L1_med > 0)].groupby(["dataset", "rule", "target_rank_in_subset"]):
        if s.n.nunique() >= 3:
            b = np.polyfit(np.log(s.n), np.log(s.L1_med), 1)[0]; sl.append(dict(dataset=ds, rule=rule, target_rank_in_subset=rk, loglog_slope_L1_vs_n=b, n_sizes=s.n.nunique()))
    pd.DataFrame(sl).to_csv(OUT / "robust_tasksub_slopes.csv", index=False)

def main_ref():
    parts = [pd.read_csv(f) for f in glob.glob(str(R / "ollb_score_*.csv")) + glob.glob(str(R / "ollb_ordinal_*.csv")) + [str(R / "ollb_plurality_sample.csv")]]
    parts += [pd.read_csv(R / "helm_main.csv"), pd.read_csv(R / "helm_trimmed.csv")]
    return pd.concat(parts, ignore_index=True).drop_duplicates(["dataset", "cap", "rule", "target"])

def paired(var_file, label, ref):
    v = pd.read_csv(R / var_file); out = []
    m = v.merge(ref, on=["dataset", "cap", "rule", "target"], suffixes=("", "_ref"))
    for (ds, cap, rule), s in m.groupby(["dataset", "cap", "rule"]):
        s = s[(s.censored.fillna(0) == 0) & (s.censored_ref.fillna(0) == 0)]
        both = s[np.isfinite(s.L1) & np.isfinite(s.L1_ref) & (s.L1_ref > 0)]
        ratio = (both.L1 / both.L1_ref).values
        r = dict(variant=label, dataset=ds, cap=cap, rule=rule, n_targets=len(s), eps_variant=float(s.eps.iloc[0]) if len(s) else np.nan, eps_ref=float(s.eps_ref.iloc[0]) if len(s) else np.nan,
                 n_feasibility_changed=int((s.feasible != s.feasible_ref).sum()), n_L1_equal=int(np.isclose(s.L1, s.L1_ref, equal_nan=False).sum()),
                 n_K_changed=int((both.K != both.K_ref).sum()), n_both_feasible_positive=len(both))
        if len(ratio):
            idx = rng.integers(0, len(ratio), (a.B, len(ratio))); bs = np.median(ratio[idx], axis=1)
            r.update(L1_ratio_med=float(np.median(ratio)), L1_ratio_lo=float(np.percentile(bs, 2.5)), L1_ratio_hi=float(np.percentile(bs, 97.5)), L1_ratio_max=float(ratio.max()), L1_ratio_min=float(ratio.min()))
        out.append(r)
    return out

def eps_ties():
    ref = main_ref(); rows = []
    for f, lab in (("ollb_eps0.1.csv", "eps=0.1"), ("ollb_notie.csv", "ties_as_loss"), ("helm_eps0.1.csv", "eps=0.1"), ("helm_notie.csv", "ties_as_loss")):
        if (R / f).exists(): rows += paired(f, lab, ref.rename(columns=lambda c: c + "_ref" if c in ("eps", "feasible", "censored", "L1", "K") else c))
    pd.DataFrame(rows).to_csv(OUT / "robust_eps_ties.csv", index=False)

def variants():
    """data slices vs the main OLLB matrix: per variant/cap/rule median L1 and K (feasible targets, bootstrap CI over targets), feasible rate (unweighted sample share),
    and the Kendall tau between the rule ordering (median L1 over feasible targets) of the variant and the main matrix on its rank sample (descriptive)."""
    ref = main_ref(); ref = ref[ref.dataset == "ollb"]
    samp = set(pd.read_csv(R / "ollb_plurality_sample.csv").target)
    refs = ref[ref.target.isin(samp) & (ref.censored.fillna(0) == 0)]
    rows, tau = [], []
    for f in sorted(glob.glob(str(R / "ollb_*_variants.csv"))):
        d = pd.read_csv(f); d = d[d.censored.fillna(0) == 0]
        for (ds, cap, rule), s in d.groupby(["dataset", "cap", "rule"]):
            fe = s[np.isfinite(s.L1)]; idx = rng.integers(0, max(len(fe), 1), (a.B, max(len(fe), 1)))
            bs = np.median(fe.L1.values[idx], axis=1) if len(fe) else np.array([np.nan])
            rows.append(dict(dataset=ds, cap=cap, rule=rule, n_targets=len(s), feasible_rate_unweighted=float((s.feasible == 1).mean()), L1_med_feas=float(fe.L1.median()) if len(fe) else np.nan,
                             L1_lo=float(np.percentile(bs, 2.5)), L1_hi=float(np.percentile(bs, 97.5)), K_med_feas=float(fe.K.median()) if len(fe) else np.nan))
        V = pd.DataFrame(rows)
        for (ds, cap), g in V[V.dataset == pathlib.Path(f).name.replace("_variants.csv", "")].groupby(["dataset", "cap"]):
            rr = refs[refs.cap == cap]; rm = rr[np.isfinite(rr.L1)].groupby("rule").L1.median()
            com = g.set_index("rule").L1_med_feas.dropna().index.intersection(rm.index)
            if len(com) >= 4:
                t = stats.kendalltau(g.set_index("rule").loc[com].L1_med_feas, rm[com]); tau.append(dict(dataset=ds, cap=cap, n_rules=len(com), kendall_tau_vs_main=t.statistic, p=t.pvalue))
    pd.DataFrame(rows).drop_duplicates().to_csv(OUT / "robust_variants.csv", index=False); pd.DataFrame(tau).drop_duplicates().to_csv(OUT / "robust_variants_ordering.csv", index=False)

if __name__ == "__main__":
    for fn in (noise_boot, tasksub, eps_ties, variants):
        try: fn(); print("ok", fn.__name__, flush=True)
        except Exception as e: print("FAILED", fn.__name__, repr(e), flush=True); raise
