"""Assemble the figtab-schema tables in results/ from the raw outputs of 09/10/12/13/14.
  per_target.csv, per_target_ablation.csv, paired_stats.csv, feasibility.csv, power_mean_curve.csv,
  subsample_curves.csv, baselines.csv, ablation.csv, noise_robust.csv   (verification.csv is written by 14)
Bootstrap: percentile, 2000 resamples of the TARGET MODELS (pairs resampled jointly), seed 20261104 per call.
Wilson 95% intervals for proportions.   python 11_collect.py"""
import glob, json
from common import *
from grid import RULE_META
RES = f"{ROOT}/results"; BOOT = 2000; SEED = 20261104
def fmt(x): return "" if pd.isna(x) else f"{float(x):g}"
def rid(df):
    p = df["rule_param"].map(fmt); return df["rule"] + np.where(p == "", "", ":" + p)
def load(specs):
    ds = []
    for s in specs:
        if not os.path.exists(f"{RES}/per_target_{s}.csv"): print("MISSING", s); continue
        d = pd.read_csv(f"{RES}/per_target_{s}.csv"); d["spec"] = s
        if "normalisation" not in d: d["normalisation"] = "normalised"
        d["normalisation"] = d["normalisation"].fillna("normalised"); ds.append(d)
    d = pd.concat(ds, ignore_index=True); d["rule_id"] = rid(d)
    d["tie_break"] = "strict"; d["spillover_rho"] = 0.0; d["noise_margin"] = 0.0; d["p_first_noise"] = np.nan
    return d
MAIN = ["helm", "olb_headline", "olb_headline_raw", "olb_subtask"]
ABL = [os.path.basename(f)[11:-4] for f in sorted(glob.glob(f"{RES}/per_target_ablation_*.csv"))]
pt = load(MAIN); pa = load(ABL)

# ordinal / trimmed-mean point cost: upper bound from the Delta*(k) frontier (G1 = cap best+1, linear cost)
fr = []
for f, spec in [("frontier_helm", "helm"), ("frontier_olb", "olb_headline"), ("frontier_olb_raw", "olb_headline_raw")]:
    d = pd.read_csv(f"{RES}/{f}.csv"); d = d[(d.cap == "sota+1") & np.isfinite(d.total_points)]
    d = d.groupby(["model", "rule"]).total_points.min().reset_index(); d["spec"] = spec
    d["rule"] = d["rule"].map(lambda r: RULE_META[r][0]); fr.append(d.rename(columns={"model": "target_id", "total_points": "ub"}))
fr = pd.concat(fr)
m = (pt.gain_model == "G1") & (pt.cost == "linear") & (pt.G_min_kind == "na") & pt.rule_param.isna() & pt.rule.isin(["borda", "plurality", "copeland", "condorcet_winner"]) | \
    ((pt.gain_model == "G1") & (pt.cost == "linear") & (pt.G_min_kind == "na") & (pt.rule == "trimmed_mean"))
j = pt[m].merge(fr, on=["spec", "target_id", "rule"], how="left")
pt.loc[m, "G_min"] = j["ub"].values; pt.loc[m & pt.G_min.notna(), "G_min_kind"] = "upper_bound_frontier"
pt.loc[m & pt.G_min.notna(), "exact"] = 0
# k_min exactness flag stays as the solver's (exact=1 -> k_min exact); the G_min kind says whether G_min is exact

# mean-rule rank of each target (key for strata)
KEY = ["leaderboard", "granularity", "population", "normalisation", "field", "gain_model"]
def add_mean_rank(d):
    mr = d[d.rule == "mean"].groupby(KEY + ["target_id"]).init_rank.first().rename("rank_mean").reset_index()
    return d.merge(mr, on=KEY + ["target_id"], how="left")
pt = add_mean_rank(pt); pa = add_mean_rank(pa)
pt.drop(columns=["spec"]).to_csv(f"{RES}/per_target.csv", index=False)   # carries rank_mean (rank under the mean rule, same cell)
pa.drop(columns=["spec"]).to_csv(f"{RES}/per_target_ablation.csv", index=False)
print("per_target", pt.shape, "ablation", pa.shape)
BANDS = {"all_attackers": (2, 10**9), "2-10": (2, 10), "11-100": (11, 100), "101+": (101, 10**9)}

def boot(x, stat, B=BOOT, seed=SEED):
    x = np.asarray(x); n = len(x)
    if n < 2: return (np.nan, np.nan)
    rng = np.random.default_rng(seed); idx = rng.integers(0, n, (B, n))
    v = stat(x[idx], axis=1); return tuple(np.nanpercentile(v, [2.5, 97.5]))
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)

# ---------------------------------------------------------------- paired stats (C2)
CM = "percentile bootstrap over target models, B=%d, seed=%d (re-seeded per row); Wilson n/a" % (BOOT, SEED)
def pair_rows(d, other, metric, spec_keys, band):
    a = d[d.rule_id == "mean"].set_index("target_id"); b = d[d.rule_id == other].set_index("target_id")
    idx = a.index.intersection(b.index); a, b = a.loc[idx], b.loc[idx]
    lo, hi = BANDS[band]; sel = (a.rank_mean >= lo) & (a.rank_mean <= hi); a, b = a[sel], b[sel]
    col = {"k_min": "k_min", "G_min": "G_min"}.get(metric, "feasible")
    out = []
    if metric == "feasible":
        diff = (b.feasible - a.feasible).values.astype(float)   # >0: other rule feasible where mean is not
        out.append(dict(estimate_type="mean_diff_feasible(other-mean)", estimate=diff.mean() if len(diff) else np.nan, n_pairs=len(diff),
                        n_counterexamples=int((diff > 0).sum()), n_ties=int((diff == 0).sum()), n_only_one_feasible=int((diff != 0).sum())))
        lo_, hi_ = boot(diff, np.mean) if len(diff) else (np.nan,) * 2; out[0].update(ci_lo=lo_, ci_hi=hi_); return out
    ok = a[col].notna() & b[col].notna()
    if metric == "G_min": ok &= (a.G_min_kind == "exact") & (b.G_min_kind == "exact")
    x, y = a[col][ok].values.astype(float), b[col][ok].values.astype(float); only = int(((a[col].notna() != b[col].notna())).sum())
    if len(x) == 0: return out
    d_ = y - x
    e = dict(estimate_type="median_diff(other-mean)", estimate=float(np.median(d_)), n_pairs=len(x), n_counterexamples=int((d_ < 0).sum()), n_ties=int((d_ == 0).sum()), n_only_one_feasible=only)
    e["ci_lo"], e["ci_hi"] = boot(d_, np.median); out.append(e)
    pos = x > 0
    if pos.sum() >= 2:
        r = y[pos] / x[pos]; e = dict(estimate_type="median_ratio(other/mean)", estimate=float(np.median(r)), n_pairs=int(pos.sum()), n_counterexamples=int((r < 1).sum()),
                                      n_ties=int((r == 1).sum()), n_only_one_feasible=only)
        e["ci_lo"], e["ci_hi"] = boot(r, np.median); out.append(e)
    return out
rows = []
for (lb, gr, pop, norm, fld, gm), g in pt.groupby(KEY):
    cores = [r for r in g.rule_id.unique() if r != "mean"]
    for cost in (["linear", "headroom"]):
        gc = g[g.cost == cost]
        for other in cores:
            for band in BANDS:
                for metric in (["k_min", "feasible"] if cost == "linear" else []) + ["G_min"]:
                    for e in pair_rows(gc, other, metric, KEY, band):
                        rows.append(dict(leaderboard=lb, granularity=gr, population=pop, normalisation=norm, field=fld, gain_model=gm, cost=cost,
                                         tie_break="strict", spillover_rho=0.0, noise_margin=0.0, rule_a="mean", rule_b=other,
                                         contrast=f"mean vs {other}", rank_stratum=band, metric=metric, ci_method=CM, **e))
ps = pd.DataFrame(rows); ps.to_csv(f"{RES}/paired_stats.csv", index=False); print("paired_stats", ps.shape)

# ---------------------------------------------------------------- feasibility (C4)
def rbin(r): return np.where(r <= 2, "1-2", np.where(r <= 10, "3-10", np.where(r <= 100, "11-100", "rest")))
rows = []
for basis in ["rule", "mean"]:
    for ds, tag in [(pt, "main"), (pa, "ablation")]:
        d = ds[ds.cost == "linear"].copy(); d["rank_bin"] = rbin(d.init_rank if basis == "rule" else d.rank_mean)
        for keys, g in d.groupby(KEY + ["rule_id", "rank_bin"]):
            n_ = len(g); k_ = int(g.feasible.sum()); lo, hi = wilson(k_, n_)
            rows.append(dict(zip(KEY + ["rule_id", "rank_bin"], keys), rank_basis=basis, n_targets=n_, frac_feasible=k_ / n_, ci_lo=lo, ci_hi=hi, ci_method="Wilson 95%", table=tag))
fe = pd.DataFrame(rows); fe[["rule", "rule_param"]] = fe.rule_id.str.split(":", n=1, expand=True).reindex(columns=[0, 1]).fillna("").values
fe["tie_break"] = "strict"; fe["spillover_rho"] = 0.0; fe["noise_margin"] = 0.0
fe.to_csv(f"{RES}/feasibility.csv", index=False); print("feasibility", fe.shape)

# ---------------------------------------------------------------- power-mean curve (C3)
PGRID = [("min", -np.inf), ("power_mean:-2", -2), ("power_mean:-1", -1), ("geomean:0", 0), ("power_mean:0.5", 0.5), ("mean", 1), ("power_mean:2", 2), ("power_mean:4", 4), ("power_mean:8", 8)]
OTH = ["median", "borda", "copeland", "trimmed_mean:0.2", "plurality", "condorcet_winner"]
ridmap = {"geomean:0": "geomean:0", "min": "min"}
rows = []; mono = []
for (lb, gr, pop, norm, fld, gm), g in pt[pt.cost == "linear"].groupby(KEY):
    if gm not in ("G1", "G2_0.25", "G2_0.5", "G2_1", "G1_add10", "ceil"): continue
    W = g.pivot_table(index="target_id", columns="rule_id", values="k_min", aggfunc="first", dropna=False)
    F = g.pivot_table(index="target_id", columns="rule_id", values="feasible", aggfunc="first", dropna=False)
    rk = g[g.rule_id == "mean"].set_index("target_id").rank_mean
    if not all(r in W for r, _ in PGRID): continue
    for band, (lo, hi) in BANDS.items():
        T = rk.index[(rk >= lo) & (rk <= hi)]
        if len(T) < 2: continue
        for r, p in PGRID + [(o, np.nan) for o in OTH]:
            if r not in W: continue
            k = W.loc[T, r]; f = F.loc[T, r]; kk = k.dropna().values
            lo_, hi_ = boot(kk, np.median) if len(kk) >= 2 else (np.nan, np.nan)
            nm = r.split(":")[0]; pr = r.split(":")[1] if ":" in r else ""
            rows.append(dict(leaderboard=lb, granularity=gr, population=pop, normalisation=norm, field=fld, gain_model=gm, cost="linear", rank_stratum=band,
                             rule=("power_mean" if r in dict(PGRID) and nm not in ("min", "mean", "geomean") else nm), rule_param=pr, p=p, family=int(r in dict(PGRID)),
                             median_k_min=float(np.median(kk)) if len(kk) else np.nan, ci_lo=lo_, ci_hi=hi_, frac_feasible=float(f.mean()), n_targets=len(T),
                             ci_method="percentile bootstrap over targets, B=%d" % BOOT))
        # monotonicity along p for targets feasible at every p
        K = W.loc[T, [r for r, _ in PGRID]].dropna()
        if len(K) >= 2:
            d_ = np.diff(K.values, axis=1); nd = (d_ >= 0).all(1); ni = (d_ <= 0).all(1); const = ni & nd
            from scipy.stats import kendalltau
            taus = [kendalltau(np.arange(K.shape[1]), v)[0] for v in K.values if np.ptp(v) > 0]
            mono.append(dict(leaderboard=lb, granularity=gr, population=pop, normalisation=norm, field=fld, gain_model=gm, rank_stratum=band, n_targets=len(K),
                             frac_nondecreasing_in_p=float(nd.mean()), frac_nonincreasing_in_p=float(ni.mean()), frac_monotone_either=float((nd | ni).mean()),
                             frac_constant=float(const.mean()), mean_kendall_tau=float(np.mean(taus)) if taus else np.nan, n_nonconstant=len(taus)))
pm = pd.DataFrame(rows); pm.to_csv(f"{RES}/power_mean_curve.csv", index=False)
mo = pd.DataFrame(mono); mo.to_csv(f"{RES}/power_mean_monotonicity.csv", index=False); print("power_mean", pm.shape, mo.shape)

# ---------------------------------------------------------------- subsample curves (C5)
sub = []
for b in ["helm", "olb_subtask"]:
    f = f"{RES}/subsample_raw_{b}.csv"
    if os.path.exists(f): sub.append(pd.read_csv(f))
if sub:
    sd = pd.concat(sub, ignore_index=True); sd["rule_id"] = rid(sd)
    sd["k_frac"] = sd.k_min / sd.n_tasks
    rows = []
    for keys, g in sd.groupby(["leaderboard", "granularity", "population", "gain_model", "rule", "rule_param", "n_tasks", "rep", "seed"], dropna=False):
        for rk_, gg in list(g.groupby("target_rank")) + [("2-20 (median of 4)", g)]:
            rows.append(dict(zip(["leaderboard", "granularity", "population", "gain_model", "rule", "rule_param", "n_tasks", "rep", "seed"], keys), cost="linear", field="all",
                             tie_break="strict", spillover_rho=0.0, noise_margin=0.0, target_rank=rk_, median_k_min=gg.k_min.median(), median_k_min_frac=gg.k_frac.median(),
                             median_G_min=gg.G_min.median() if (gg.G_min_kind == "exact").all() else np.nan, frac_feasible=gg.feasible.mean(), n_targets=len(gg)))
    sc = pd.DataFrame(rows); sc.to_csv(f"{RES}/subsample_curves.csv", index=False)
    kc = ["leaderboard", "granularity", "gain_model", "rule", "rule_param", "n_tasks", "target_rank"]
    sm = sc.groupby(kc, dropna=False).agg(n_reps=("rep", "nunique"), k_frac_mean=("median_k_min_frac", "mean"), k_frac_lo=("median_k_min_frac", lambda x: np.nanpercentile(x, 2.5)),
                                          k_frac_hi=("median_k_min_frac", lambda x: np.nanpercentile(x, 97.5)), k_mean=("median_k_min", "mean"), G_mean=("median_G_min", "mean"),
                                          frac_feasible=("frac_feasible", "mean")).reset_index()
    sm.to_csv(f"{RES}/subsample_curves_summary.csv", index=False); print("subsample", sc.shape, sm.shape)

# ---------------------------------------------------------------- baselines
bl = []
for b in ["helm", "olb"]:
    f = f"{RES}/baselines_raw_{b}.csv"
    if os.path.exists(f): bl.append(pd.read_csv(f))
if bl:
    bd = pd.concat(bl, ignore_index=True)
    mr = pt[(pt.rule == "mean") & (pt.gain_model == "G1") & (pt.cost == "linear") & (pt.granularity == "headline") & (pt.normalisation == "normalised")][["leaderboard", "target_id", "init_rank"]].rename(columns={"init_rank": "rank_mean"})
    bd = bd.drop(columns="rank_mean").merge(mr, on=["leaderboard", "target_id"], how="left")
    rows = []
    for keys, g in bd.groupby(["leaderboard", "granularity", "population", "rule", "budget_type", "budget", "strategy"]):
        for band, (lo, hi) in BANDS.items():
            gg = g[(g.rank_mean >= lo) & (g.rank_mean <= hi)]
            if len(gg) == 0: continue
            s = gg.success.values; lo_, hi_ = boot(s, np.mean, B=500) if len(s) > 1 else (np.nan,) * 2
            rows.append(dict(zip(["leaderboard", "granularity", "population", "rule", "budget_type", "budget", "strategy"], keys), gain_model="G1", cost="linear", field="all",
                             tie_break="strict", spillover_rho=0.0, noise_margin=0.0, rank_stratum=band, n_targets=len(gg), frac_first=s.mean(), ci_lo=lo_, ci_hi=hi_,
                             ci_method="percentile bootstrap over targets, B=500; random strategy: success is the mean over 100 random draws per target"))
    bs = pd.DataFrame(rows)
    # median budget needed (smallest budget on the grid with success >= 0.5 for the target)
    need = []
    for keys, g in bd.groupby(["leaderboard", "granularity", "population", "rule", "budget_type", "strategy", "target_id"]):
        ok = g[g.success >= 0.5].budget; need.append(dict(zip(["leaderboard", "granularity", "population", "rule", "budget_type", "strategy", "target_id"], keys), need=ok.min() if len(ok) else np.inf))
    nd = pd.DataFrame(need).merge(mr, on=["leaderboard", "target_id"], how="left")
    nd = nd[nd.rank_mean >= 2].groupby(["leaderboard", "granularity", "population", "rule", "budget_type", "strategy"]).need.agg(median_budget_needed="median", frac_reached=lambda x: np.isfinite(x).mean()).reset_index()
    nd.to_csv(f"{RES}/baselines_budget_needed.csv", index=False); bs.to_csv(f"{RES}/baselines.csv", index=False); print("baselines", bs.shape, nd.shape)

# ---------------------------------------------------------------- noise-robust k (HELM, OLB)
nr = []
for b, lb in [("helm", "helm_mmlu"), ("olb", "openllm_v2")]:
    f = f"{RES}/noise_robust_{b}.csv"
    if os.path.exists(f):
        d = pd.read_csv(f); d["leaderboard"] = lb; nr.append(d)
if nr:
    nd = pd.concat(nr, ignore_index=True)
    rows = []
    for (lb, tid, rule), g in nd.groupby(["leaderboard", "target_id", "rule"]):
        g = g.sort_values("k"); r = dict(leaderboard=lb, target_id=tid, rule=rule, init_rank_mean=g.init_rank_mean.iloc[0], k_det=g.k_det.iloc[0], p_first_at_k_det=g.p_first_noise.iloc[0], n_draws=g.n_draws.iloc[0])
        for q in [0.5, 0.9]:
            ok = g[g.p_first_noise >= q].k; r[f"k_noise_q{int(q*100)}"] = ok.min() if len(ok) else np.nan
        rows.append(r)
    nrs = pd.DataFrame(rows); nrs.to_csv(f"{RES}/noise_robust.csv", index=False); print("noise_robust", nrs.shape)

# ---------------------------------------------------------------- noise rows in the per-target schema
if nr:
    rows = []
    for _, r in nrs.iterrows():
        base = dict(leaderboard=r.leaderboard, granularity="headline", population="all" if r.leaderboard == "helm_mmlu" else "no_flagged", normalisation="normalised" if r.leaderboard == "openllm_v2" else "points",
                    field="all", gain_model="G1", cost="linear", tie_break="strict", spillover_rho=0.0, target_id=r.target_id, rank_mean=r.init_rank_mean,
                    rule=RULE_META[{"trim": "trim"}.get(r.rule, r.rule)][0], rule_param=RULE_META[{"trim": "trim"}.get(r.rule, r.rule)][1], n_draws=r.n_draws)
        rows.append(dict(base, noise_margin=0.0, k_min=r.k_det, p_first_noise=r.p_first_at_k_det, feasible=1))
        for q in [0.5, 0.9]:
            k = r[f"k_noise_q{int(q*100)}"]
            rows.append(dict(base, noise_margin=q, k_min=k, p_first_noise=np.nan, feasible=int(pd.notna(k))))
    pd.DataFrame(rows).to_csv(f"{RES}/per_target_noise.csv", index=False)
    print("noise margin column = required probability of ranking first (0 = none, p_first_noise is then the probability at the noise-free k_min)")

# ---------------------------------------------------------------- ablation grid (C6)
from scipy.stats import spearmanr
CORE_IDS = ["median", "borda", "copeland", "condorcet_winner", "plurality", "min", "trimmed_mean:0.2"]
PLAN_C2 = {"median", "borda", "copeland", "condorcet_winner"}
allc = pd.concat([pt.assign(table="main"), pa.assign(table="ablation")], ignore_index=True)
allc = allc[allc.cost == "linear"]
DEF = dict(field="all", normalisation="normalised")
def default_pop(lb): return "all" if lb == "helm_mmlu" else "no_flagged"
def cell_rows(g, key):
    out = []
    a = g[g.rule_id == "mean"].set_index("target_id")
    for r in CORE_IDS:
        b = g[g.rule_id == r].set_index("target_id")
        idx = a.index.intersection(b.index); aa, bb = a.loc[idx], b.loc[idx]; sel = aa.rank_mean >= 2; aa, bb = aa[sel], bb[sel]
        ok = aa.k_min.notna() & bb.k_min.notna()
        if ok.sum() >= 5:
            d = (bb.k_min[ok] - aa.k_min[ok]).values; lo, hi = boot(d, np.median)
            out.append(dict(key, rule=r, metric="C2_median_diff_k(other-mean)", estimate=float(np.median(d)), ci_lo=lo, ci_hi=hi, n_targets=int(ok.sum()),
                            claim_holds=int(lo > 0), claim_in_plan=int(r in PLAN_C2), note=f"share of pairs reversed: {(d < 0).mean():.2f}"))
        bt = b[b.rank_mean >= 2] if "rank_mean" in b else b
        if len(bt) >= 5:
            fe = bt.feasible.values.astype(float); rkm = bt.rank_mean.values
            if np.ptp(fe) > 0:
                rho = spearmanr(rkm, fe)[0]; rng = np.random.default_rng(SEED); bs = []
                for _ in range(500):
                    i = rng.integers(0, len(fe), len(fe))
                    if np.ptp(fe[i]) > 0: bs.append(spearmanr(rkm[i], fe[i])[0])
                lo, hi = np.percentile(bs, [2.5, 97.5])
                out.append(dict(key, rule=r, metric="C4_spearman(rank_mean,feasible)", estimate=float(rho), ci_lo=lo, ci_hi=hi, n_targets=len(fe), claim_holds=int(hi < 0), claim_in_plan=1, note=""))
            else:
                out.append(dict(key, rule=r, metric="C4_spearman(rank_mean,feasible)", estimate=np.nan, ci_lo=np.nan, ci_hi=np.nan, n_targets=len(fe), claim_holds=0, claim_in_plan=1,
                                note="degenerate: feasibility constant (%s)" % ("all feasible" if fe.all() else "none feasible")))
    return out
cells = {}
for keys, g in allc.groupby(KEY):
    cells[keys] = cell_rows(g, dict(zip(KEY, keys)))
mo_i = mo.set_index(KEY + ["rank_stratum"]) if len(mo) else None
ab = []
def add(factor, level, keys, extra=None):
    for r in cells.get(keys, []):
        ab.append(dict(r, factor=factor, level=level, **(extra or {})))
    # C3
    if mo_i is not None and keys + ("all_attackers",) in mo_i.index:
        m_ = mo_i.loc[keys + ("all_attackers",)]
        ab.append(dict(zip(KEY, keys), rule="power_mean_family", metric="C3_frac_monotone_in_p(either direction)", estimate=float(m_.frac_monotone_either), ci_lo=np.nan, ci_hi=np.nan,
                       n_targets=int(m_.n_targets), claim_holds=int(m_.frac_monotone_either >= 0.9), claim_in_plan=1, note=f"nondecreasing {m_.frac_nondecreasing_in_p:.2f}, nonincreasing {m_.frac_nonincreasing_in_p:.2f}, mean tau {m_.mean_kendall_tau:.2f}",
                       factor=factor, level=level))
GM = ["G1", "G1_add10", "G1_add20", "G2_0.25", "G2_0.5", "G2_1", "ceil", "ceil_add10", "ceil_add20"]; CHEAP = ["G1", "G2_0.5", "G1_add10", "ceil"]
for lb in ["helm_mmlu", "openllm_v2"]:
    for gm in GM: add("gain_model", gm, (lb, "headline", default_pop(lb), "normalised", "all", gm))
    for f in ["top50", "top10"]:
        for gm in CHEAP: add("field", f, (lb, "headline", default_pop(lb), "normalised", f, gm))
    for gm in CHEAP: add("field", "all", (lb, "headline", default_pop(lb), "normalised", "all", gm))
for pop in ["all", "no_flagged", "no_merges", "official_providers"]:
    for gm in CHEAP: add("population", pop, ("openllm_v2", "headline", pop, "normalised", "all", gm))
for gm in CHEAP:
    add("normalisation", "raw", ("openllm_v2", "headline", "no_flagged", "raw", "all", gm)); add("normalisation", "normalised", ("openllm_v2", "headline", "no_flagged", "normalised", "all", gm))
    add("granularity", "headline(n=6)", ("openllm_v2", "headline", "no_flagged", "normalised", "all", gm)); add("granularity", "subtask(n=39)", ("openllm_v2", "subtask", "subtask_pool_699", "normalised", "all", gm))
# noise: C2 on the k needed for P(first)>=0.9 (item-level evaluation noise) versus the noise-free k on the same targets
if nr:
    for lb in nrs.leaderboard.unique():
        g = nrs[(nrs.leaderboard == lb) & (nrs.init_rank_mean >= 2)]
        for lvl, col in [("none", "k_det"), ("P(first)>=0.5", "k_noise_q50"), ("P(first)>=0.9", "k_noise_q90")]:
            W = g.pivot(index="target_id", columns="rule", values=col)
            for r in ["median", "borda", "trim", "plurality", "min"]:
                if r in W and "mean" in W:
                    ok = W[r].notna() & W["mean"].notna()
                    if ok.sum() >= 5:
                        d = (W[r][ok] - W["mean"][ok]).values; lo, hi = boot(d, np.median)
                        ab.append(dict(leaderboard=lb, granularity="headline", population=default_pop(lb), normalisation="normalised", field="all", gain_model="G1", factor="noise", level=lvl,
                                       rule={"trim": "trimmed_mean:0.2"}.get(r, r), metric="C2_median_diff_k(other-mean)", estimate=float(np.median(d)), ci_lo=lo, ci_hi=hi, n_targets=int(ok.sum()),
                                       claim_holds=int(lo > 0), claim_in_plan=int(r in PLAN_C2), note=f"share of pairs reversed: {(d < 0).mean():.2f}; targets reaching the level for both rules only"))
abl = pd.DataFrame(ab); abl["cost"] = "linear"; abl["tie_break"] = "strict"; abl["spillover_rho"] = 0.0
abl["noise_margin"] = np.where(abl.factor == "noise", abl.level.map({"none": 0.0, "P(first)>=0.5": 0.5, "P(first)>=0.9": 0.9}), 0.0)
abl["ci_method"] = "percentile bootstrap over target models (B=%d; C4 B=500), seed=%d" % (BOOT, SEED)
abl["claim_criterion"] = abl.metric.map({"C2_median_diff_k(other-mean)": "1 if the bootstrap CI of the median paired difference k_other-k_mean lies strictly above 0 (targets with mean-rank>=2, feasible under both rules)",
                                         "C4_spearman(rank_mean,feasible)": "1 if the bootstrap CI of the Spearman correlation between mean-rank and feasibility lies strictly below 0 (feasibility falls with initial rank); 0 and empty estimate if feasibility is constant",
                                         "C3_frac_monotone_in_p(either direction)": "1 if >=90% of targets feasible at every p have k_min monotone (either direction) along p = -inf,-2,-1,0,0.5,1,2,4,8"})
abl.to_csv(f"{RES}/ablation.csv", index=False); print("ablation", abl.shape)
