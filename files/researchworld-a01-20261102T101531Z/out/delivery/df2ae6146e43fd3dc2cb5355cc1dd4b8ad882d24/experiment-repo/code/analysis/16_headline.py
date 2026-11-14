"""results/headline.csv: the one-place answer to 'what investment is needed'.
Rows: leaderboard/level x gain model x rule x rank stratum (rank under the mean rule, attackers = rank >= 2) -> feasible share (Wilson),
median k_min and median G_min over the feasible targets (percentile bootstrap over target models, B=2000, seed 20261104), IQR, n_targets.
Gain models: G2_0.5 (half of each task's headroom to the board best+1), G1_add10 (+10 points per task at most, cap best+1),
ceil_add10 (+10 points, cap 100) are the bounded ones that make feasibility non-trivial; G1 (unbounded, cap best+1) is added as the reference.
Cost: linear points for G_min (k_min does not depend on cost).   python 16_headline.py"""
from common import *
RES = f"{ROOT}/results"; B = 2000; SEED = 20261104
pt = pd.read_csv(f"{RES}/per_target.csv", low_memory=False)
pt = pt[(pt.cost == "linear") & (pt.normalisation == "normalised") & pt.gain_model.isin(["G2_0.5", "G1_add10", "ceil_add10", "G1"])]
KEY = ["leaderboard", "granularity", "population", "gain_model"]
if "rank_mean" not in pt:
    mr = pt[pt.rule == "mean"].groupby(KEY + ["target_id"]).init_rank.first().rename("rank_mean").reset_index()
    pt = pt.merge(mr, on=KEY + ["target_id"], how="left")
BANDS = {"2-10": (2, 10), "11-100": (11, 100), "101+": (101, 10**9), "all_attackers": (2, 10**9)}
def boot_med(x):
    x = np.asarray(x, float)
    if len(x) < 2: return (np.nan, np.nan)
    idx = np.random.default_rng(SEED).integers(0, len(x), (B, len(x)))
    return tuple(np.percentile(np.median(x[idx], axis=1), [2.5, 97.5]))
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
def rid(r, p): return r if pd.isna(p) else f"{r}:{p:g}"
pt["rule_id"] = [rid(r, p) for r, p in zip(pt.rule, pt.rule_param)]
rows = []
for keys, g in pt.groupby(KEY + ["rule_id"]):
    for band, (lo, hi) in BANDS.items():
        s = g[(g.rank_mean >= lo) & (g.rank_mean <= hi)]; n = len(s)
        if n == 0: continue
        f = s[s.feasible == 1]; wl, wh = wilson(len(f), n)
        r = dict(zip(KEY + ["rule_id"], keys), rank_stratum=band, n_targets=n, n_feasible=len(f), frac_feasible=len(f) / n, feas_ci_lo=wl, feas_ci_hi=wh)
        for m in ("k_min", "G_min"):
            x = f[m].dropna().values
            if m == "G_min" and len(x) < 0.9 * len(f): x = x[:0]   # point cost reported only where it is defined for >= 90% of the feasible targets
            if len(x):
                lo_, hi_ = boot_med(x); r.update({f"median_{m}": float(np.median(x)), f"{m}_ci_lo": lo_, f"{m}_ci_hi": hi_, f"{m}_q25": float(np.percentile(x, 25)), f"{m}_q75": float(np.percentile(x, 75)), f"n_{m}": len(x)})
        kinds = f[f.G_min.notna()].G_min_kind.dropna().unique(); r["G_min_kind"] = kinds[0] if len(kinds) == 1 else "|".join(sorted(kinds)) if len(kinds) else "na"
        if "median_G_min" not in r: r["G_min_kind"] = "na"
        r["k_min_exact"] = int(not (keys[-1].startswith("trimmed_mean") and s.n_tasks.iloc[0] > 10))   # only the trimmed mean at n > 10 is a heuristic upper bound
        r["ci_method"] = f"percentile bootstrap over target models, B={B}, seed={SEED}; feasibility Wilson 95%; medians over feasible targets"
        rows.append(r)
h = pd.DataFrame(rows); h.insert(0, "table", "headline")
h.to_csv(f"{RES}/headline.csv", index=False); print("headline", h.shape)
