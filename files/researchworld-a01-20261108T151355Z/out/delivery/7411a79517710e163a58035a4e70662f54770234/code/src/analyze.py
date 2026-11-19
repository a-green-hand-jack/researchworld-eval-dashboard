"""Summary tables for the paper (claims C2-C8). Reads results/*.csv, writes results/summary/*.csv.
Conventions: rank bins by the target's rank under the MEAN (rank_mean) so all rules share the same target set;
CIs are 95% percentile bootstrap over targets within a bin (B=1000, seed 0) -- descriptive, targets are the population;
infeasible rows are never dropped: `feas` = share of targets that can reach first; K/L1 statistics are over feasible targets only.
Usage: python3 src/analyze.py
"""
import glob, pathlib, numpy as np, pandas as pd
from scipy.stats import spearmanr
R = pathlib.Path(__file__).resolve().parents[1] / "results"; OUT = R / "summary"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(0); B = 1000
def reseed():
    """every summary table starts from seed 0, so its intervals depend only on its own input files (not on how many draws earlier tables used)"""
    global rng; rng = np.random.default_rng(0)
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
def lab(r):
    for lo, hi in BINS:
        if lo <= r <= hi: return f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else ">100")
    return "1"
def ci(v, f):
    """point estimate and 95% percentile bootstrap CI of statistic f (np.mean / np.median) over v; vectorised over replicates"""
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    bs = f(v[rng.integers(0, len(v), (B, len(v)))], axis=1)
    return (float(f(v)), *np.percentile(bs, [2.5, 97.5]))

def load_main():
    parts = []
    for f in ["helm_main.csv", "ollb_score.csv"] + [pathlib.Path(g).name for g in sorted(glob.glob(str(R / "ollb_ord_*.csv")))]:
        if (R / f).exists():
            d = pd.read_csv(R / f)
            if "feasible" not in d: d["feasible"] = np.isfinite(d[["L1", "K", "Linf"]]).all(axis=1)
            parts.append(d)
    d = pd.concat(parts, ignore_index=True); d["group"] = [lab(r) for r in d.rank_mean]
    return d[d.group != "1"]

def table_groups(d):
    rows = []
    for (ds, cap, rule, g), s in d.groupby(["dataset", "cap", "rule", "group"]):
        feas = s[s.feasible]; r = dict(dataset=ds, cap=cap, rule=rule, group=g, n_targets=len(s), n_feasible=len(feas))
        r["feas"], r["feas_lo"], r["feas_hi"] = ci(s.feasible.astype(float).values, np.mean)
        for m, f, nm in (("K", np.mean, "Kmean"), ("K", np.median, "Kmed"), ("L1", np.median, "L1med"), ("L1", np.mean, "L1mean"), ("Linf", np.median, "Linfmed")):
            r[nm], r[nm + "_lo"], r[nm + "_hi"] = ci(feas[m].values, f)
        rows.append(r)
    return pd.DataFrame(rows)

def table_matched(d):
    """OLLB: rules on the SAME targets. The ordinal OLLB rows use a rank-stratified sample (20 targets ranked 2-21 + 100 log-uniform in rank), the score rules all
    targets, so pooled shares across rule families are only comparable on the ordinal sample: restrict every rule to it. Statistics are over the sample (not the population)."""
    o = d[(d.dataset == "ollb")]; samp = set(o[o.rule.isin(["borda", "condorcet", "plurality"])].target)
    m = o[o.target.isin(samp)].copy(); m["group"] = "sample"
    return table_groups(m)

def ordinal_gap(ds, rule, d):
    """gap in rule units for the ordinal rules (Borda points, plurality first-place count, Copeland score): best rival's value minus the target's (the solver leaves it NaN);
    needed for the C4 regression on rule units (the Condorcet gap is the Copeland-score proxy, see docs/SOLVERS.md)"""
    from mti import data as dt, ordinal as od
    X, names, tasks, meta = dt.load(ds); M, n = X.shape
    if rule == "borda": v = od.borda_points(X)
    elif rule == "plurality":
        ties = X == X.max(axis=0); v = (ties / ties.sum(axis=0)).sum(axis=1)
    else:
        v = np.zeros(M)
        for lo in range(0, M, 64):
            Xc = X[lo:lo + 64]; W = (Xc[:, None, :] > X[None, :, :]).sum(-1) + 0.5 * (Xc[:, None, :] == X[None, :, :]).sum(-1)
            v[lo:lo + 64] = ((W > n / 2) + 0.5 * (W == n / 2)).sum(1) - 0.5
    srt = np.sort(v)[::-1]; best_other = np.where(v == srt[0], srt[1], srt[0])          # best rival's value
    return d.target.map(dict(zip(names, best_other - v)))

def table_rank_vs_gap(d):
    """C4: R^2 of log L1 on log rank vs on log gap (gap = best rival's value - target's value under the same rule, in rule units; for the ordinal rules computed here by
    ordinal_gap, in rule units: Borda points, first-place count, Copeland score), ceil cap, targets with gap>0 and L1>0. The mean is an identity (L1 = n*gap) and is listed only as a check."""
    rows = []
    for (ds, cap, rule), s in d[(d.cap == "ceil")].groupby(["dataset", "cap", "rule"]):
        if rule in ("borda", "plurality", "condorcet"): s = s.assign(gap=ordinal_gap(ds, rule, s))
        s = s[s.feasible & (s.L1 > 0) & (s.gap > 0)] if "gap" in s and s.gap.notna().any() else s.iloc[0:0]
        if len(s) < 10 or s.rank_rule.nunique() < 5: continue      # e.g. OLLB plurality: ~all targets tie at rank 8 (no first-place wins), the rank has no variance
        y = np.log(s.L1.values); xr = np.log(s.rank_rule.values.astype(float)); xg = np.log(s.gap.values)
        def r2(x, y): return np.corrcoef(x, y)[0, 1] ** 2
        idx = np.arange(len(s)); bs = np.array([(lambda b: (r2(xr[b], y[b]), r2(xg[b], y[b])))(rng.choice(idx, len(idx))) for _ in range(B)])
        bs_d = bs[:, 1] - bs[:, 0]
        rows.append(dict(dataset=ds, cap=cap, rule=rule, n=len(s), R2_rank=r2(xr, y), R2_rank_lo=np.percentile(bs[:, 0], 2.5), R2_rank_hi=np.percentile(bs[:, 0], 97.5),
                         R2_gap=r2(xg, y), R2_gap_lo=np.percentile(bs[:, 1], 2.5), R2_gap_hi=np.percentile(bs[:, 1], 97.5),
                         R2_diff=r2(xg, y) - r2(xr, y), R2_diff_lo=np.percentile(bs_d, 2.5), R2_diff_hi=np.percentile(bs_d, 97.5)))
    return pd.DataFrame(rows)

def table_min_vs_mean(d):
    """C2: ratio L1(min)/L1(mean) by tercile of the target's score dispersion, fixed in the analysis plan before the final grids: CV = sd/mean of the target's task scores (population sd);
    secondary statistic mean - min of its scores. Terciles are over the targets in the table (rank >= 2, mean L1 > 0, both rules feasible); rows `all` give the Spearman
    correlation of the ratio with the statistic. Caps ceil and emp95 (per-task empirical caps; feasible targets only, so the emp95 rows are conditional on feasibility)."""
    from mti import data as dt
    rows = []
    for ds in ("helm", "ollb"):
        X, names, tasks, meta = dt.load(ds)
        stats = {"cv": dict(zip(names, X.std(axis=1) / X.mean(axis=1))), "mean_minus_min": dict(zip(names, X.mean(axis=1) - X.min(axis=1)))}
        for cap in ("ceil", "emp95"):
            s = d[(d.dataset == ds) & (d.cap == cap) & d.rule.isin(["mean", "min"]) & d.feasible]
            w = s.pivot_table(index=["target", "rank_mean"], columns="rule", values="L1", aggfunc="first").dropna().reset_index()
            w = w[(w["mean"] > 0)]; w["ratio"] = w["min"] / w["mean"]
            for st, mp in stats.items():
                w["x"] = w.target.map(mp); rho, p = spearmanr(w.x, w.ratio)
                w["terc"] = pd.qcut(w.x.rank(method="first"), 3, labels=["low", "mid", "high"])
                for terc, g in [("all", w)] + list(w.groupby("terc", observed=True)):
                    med = ci(g.ratio.values, np.median)
                    rows.append(dict(dataset=ds, cap=cap, statistic=st, tercile=terc, n=len(g), stat_min=g.x.min(), stat_max=g.x.max(), ratio_med=med[0], ratio_lo=med[1], ratio_hi=med[2],
                                     share_min_cheaper=float((g.ratio < 1).mean()), spearman=rho if terc == "all" else np.nan, p=p if terc == "all" else np.nan))
    return pd.DataFrame(rows)

def table_c8(d):
    """C8: per dataset x rule x rank bin: share of targets for which first is INFEASIBLE under the per-task emp95 / emp99 caps (main grids), and h* against the empirical
    fine-tune-minus-base gain: ratio h*/q (median over targets with finite h*) and share of targets with h* > q, q = pooled q95 / q99 gain over the six OLLB tasks 
    and, for HELM, the transferred MMLU-PRO per-task emp95 gain (the cap that emp95 actually applies to every HELM subject). Caps: see src/mti/data.py make_cap."""
    from mti import data as dt
    hp = [pd.read_csv(R / f) for f in ("helm_hstar.csv", "ollb_hstar.csv", "ollb_hstar_ord.csv") if (R / f).exists()]
    h = pd.concat(hp, ignore_index=True); h["group"] = [lab(r) for r in h.rank_mean]; h = h[h.group != "1"]; h = pd.concat([h, h.assign(group="all")], ignore_index=True)
    m = d[d.cap.isin(["emp95", "emp99"])]; m = pd.concat([m, m.assign(group="all")], ignore_index=True)
    pooled = {q: float(dt.empirical_gain_caps(q, pooled=True)[0]) for q in (95, 99)}
    mp = {q: float(dt.empirical_gain_caps(q)[0][dt.OLLB_TASKS.index("MMLU-PRO")]) for q in (95, 99)}
    rows = []
    for (ds, rule, g), s in h.groupby(["dataset", "rule", "group"]):
        fin = s[np.isfinite(s.hstar)]; r = dict(dataset=ds, rule=rule, group=g, n_hstar_targets=len(s), n_not_solved=int((s.status == "censored").sum()))
        for q in (95, 99):
            mm = m[(m.dataset == ds) & (m.rule == rule) & (m.cap == f"emp{q}") & (m.group == g)]
            r[f"n_targets_emp{q}"] = len(mm); r[f"share_infeasible_emp{q}"] = float((mm.status == "infeasible").mean()) if len(mm) else np.nan
            r[f"n_censored_emp{q}"] = int((mm.status == "censored").sum())
            lo, hi = ci((mm.status == "infeasible").astype(float).values, np.mean)[1:] if len(mm) else (np.nan, np.nan); r[f"share_infeasible_emp{q}_lo"] = lo; r[f"share_infeasible_emp{q}_hi"] = hi
            for nm, e in (("pooled", pooled[q]),) + ((("mmlupro", mp[q]),) if ds == "helm" else ()):
                r[f"gain_emp{q}_{nm}"] = e; r[f"hstar_over_emp{q}_{nm}_med"] = float((fin.hstar / e).median()) if len(fin) else np.nan
                r[f"share_hstar_gt_emp{q}_{nm}"] = float((s.hstar > e).mean())       # h* = inf counts as exceeding
        rows.append(r)
    return pd.DataFrame(rows)

def table_tasksub():
    f = R / "helm_tasksub_gain10.csv"
    if not f.exists(): return None
    d = pd.read_csv(f); d["feas"] = np.isfinite(d.K)
    out = []
    for (rule, rk, n), s in d.groupby(["rule", "target_rank", "n"]):
        fin = s[s.feas]; kn = (fin.K / n).values
        out.append(dict(rule=rule, target_rank=rk, n=n, feas=s.feas.mean(), K_over_n_mean=kn.mean() if len(kn) else np.nan,
                        **dict(zip(("K_over_n_med", "K_over_n_lo", "K_over_n_hi"), ci(kn, np.median) if len(kn) else (np.nan,) * 3)),
                        L1_over_n_med=(fin.L1 / n).median() if len(fin) else np.nan))
    return pd.DataFrame(out)

def _read(f):
    d = pd.read_csv(R / f)
    if "feasible" not in d: d["feasible"] = np.isfinite(d[[c for c in ("L1", "K") if c in d]]).all(axis=1)
    return d

def table_noise(kind, dataset, mainfile, cap="gain10", suffix=""):
    """noise / taskboot replicates vs the same target and rule on the observed data (`cap`). Per-draw median of L1_draw/L1_obs over targets, then
    mean and 2.5/97.5 percentiles across draws; feasible share per rule; mean |rank_rule(draw) - rank_rule(obs)|."""
    f = f"{dataset}_{kind}_{cap}{suffix}.csv"
    if not (R / f).exists(): return None
    d = _read(f); base = _read(mainfile); base = base[base.cap == cap].set_index(["rule", "target"])
    d = d.join(base[["L1", "K", "rank_rule"]].rename(columns=lambda c: c + "_obs"), on=["rule", "target"])
    rows = []
    # `_t30` files hold rank-stratified targets: report all targets and by observed mean-rank group (2-10 | 11-30 | >30)
    groups = [("all", lambda r: r > 0)] + ([("2-10", lambda r: r <= 10), ("11-30", lambda r: (r > 10) & (r <= 30)), (">30", lambda r: r > 30)] if suffix else [])
    for rule, s0 in d.groupby("rule"):
        for gname, sel in groups:
            s = s0[sel(s0.rank_mean_obs)]
            if not len(s): continue
            fin = s[s.feasible & np.isfinite(s.L1_obs) & (s.L1_obs > 0)]
            pr = fin.assign(r=fin.L1 / fin.L1_obs, dk=fin.K - fin.K_obs).groupby("draw").agg(r=("r", "median"), dk=("dk", "median"))
            rows.append(dict(kind=kind, dataset=dataset, cap=cap, rule=rule, group=gname, n_draws=s.draw.nunique(), n_targets=s.target.nunique(), n_targets_obs_feasible_positive=fin.target.nunique(),
                             feas_noisy=s.feasible.mean(), feas_obs=float(np.isfinite(base.L1.xs(rule, level="rule").reindex(s.target.unique())).mean()),
                             L1_ratio_mean=pr.r.mean(), L1_ratio_lo=pr.r.quantile(.025), L1_ratio_hi=pr.r.quantile(.975),
                             dK_med_mean=pr.dk.mean(), dK_lo=pr.dk.quantile(.025), dK_hi=pr.dk.quantile(.975),
                             abs_rank_change=float((s.rank_rule - s.rank_rule_obs).abs().mean())))
    return pd.DataFrame(rows)

def table_flip():
    out = []
    for ds in ("helm", "ollb"):
        f = f"{ds}_flip_ceil.csv"
        if not (R / f).exists(): continue
        d = pd.read_csv(R / f); d["group"] = [lab(r) for r in d.rank_mean]; d["extra"] = d.d95 - d.d_eps
        for (rule, g), s in d.groupby(["rule", "group"]):
            r = dict(dataset=ds, rule=rule, group=g, n=len(s), feas=s.feasible.mean())
            s = s[s.feasible & np.isfinite(s.d95)]
            for nm, v, fn in (("p_eps", s.p_eps, np.mean), ("d_eps", s.d_eps, np.median), ("d95", s.d95, np.median), ("extra", s.extra, np.median)):
                r[nm], r[nm + "_lo"], r[nm + "_hi"] = ci(v.values, fn)
            out.append(r)
    return pd.DataFrame(out)

def table_spill():
    out = []
    for ds in ("helm", "ollb"):
        f = f"{ds}_spillover.csv"
        if not (R / f).exists(): continue
        d = pd.read_csv(R / f); d["group"] = [lab(r) for r in d.rank_mean]
        b0 = d[d.lam == 0].set_index(["cap", "rule", "target"])[["L1", "K"]]
        for (cap, rule, lam, g), s in d.groupby(["cap", "rule", "lam", "group"]):
            j = s.join(b0, on=["cap", "rule", "target"], rsuffix="0")
            ok = j[np.isfinite(j.L1) & np.isfinite(j.L10) & (j.L10 > 0)]
            r = dict(dataset=ds, cap=cap, rule=rule, lam=lam, group=g, n=len(s), feas=s.feasible.mean(), feas_lam0=float(np.isfinite(j.L10).mean()))
            r["L1_ratio"], r["L1_ratio_lo"], r["L1_ratio_hi"] = ci((ok.L1 / ok.L10).values, np.median)
            r["dK"], r["dK_lo"], r["dK_hi"] = ci((ok.K - ok.K0).values, np.median)
            out.append(r)
    return pd.DataFrame(out)

def table_eps():
    out = []
    for ds, base in (("helm", "helm_main.csv"), ("ollb", "ollb_score.csv")):
        b = _read(base); b = b[b.cap.isin(["ceil", "gain10"])].set_index(["cap", "rule", "target"])
        for e in ("1e-6", "1e-1"):
            f = f"{ds}_eps{e}.csv"
            if not (R / f).exists(): continue
            d = _read(f).join(b[["L1", "K", "feasible"]], on=["cap", "rule", "target"], rsuffix="_base")
            d["group"] = [lab(r) for r in d.rank_mean]; d = d[d.group != "1"]
            for (cap, rule), s in d.groupby(["cap", "rule"]):
                ok = s[np.isfinite(s.L1) & np.isfinite(s.L1_base) & (s.L1_base > 0)]
                out.append(dict(dataset=ds, eps=e, cap=cap, rule=rule, n=len(s), feas_change=int((s.feasible != s.feasible_base).sum()),
                                L1_ratio_med=float((ok.L1 / ok.L1_base).median()), L1_ratio_max=float((ok.L1 / ok.L1_base).max()), K_diff_max=float((ok.K - ok.K_base).abs().max())))
    return pd.DataFrame(out)

def table_slices():
    parts = []
    for f in ("ollb_nomerge_sample.csv", "ollb_top500.csv", "ollb_raw_sample.csv"):
        if (R / f).exists(): parts.append(_read(f))
    if not parts: return None
    d = pd.concat(parts, ignore_index=True); d["group"] = [lab(r) for r in d.rank_mean]
    return table_groups(d[d.group != "1"])

def table_trim():
    parts = [_read(pathlib.Path(g).name) for g in sorted(glob.glob(str(R / "*trim*.csv")))]
    if not parts: return None
    d = pd.concat(parts, ignore_index=True)
    if "status" not in d: d["status"] = np.where(d.feasible, "ok", "infeasible")
    d["group"] = [lab(r) for r in d.rank_mean]; d = d[d.group != "1"]
    g = table_groups(d); cens = d.groupby(["dataset", "cap"]).status.apply(lambda s: int((s == "censored").sum())).rename("n_censored").reset_index()
    return g.merge(cens, on=["dataset", "cap"])

HGRID = [0, 0.5, 1, 2, 3, 5, 7.5, 10, 15, 20, 30, 50, 100]
def table_hstar():
    """C5/C8: distribution of the minimum uniform gain cap h* by rule and rank bin, feasible share as a function of h (derived from h*: share(h) = mean(h* <= h)),
    and comparison with the OLLB empirical fine-tune gain quantiles (pooled scalar q95/q99; per-task values are in data.empirical_gain_caps)."""
    from mti import data as dt
    parts = [pd.read_csv(R / f) for f in ("helm_hstar.csv", "ollb_hstar.csv", "ollb_hstar_ord.csv") if (R / f).exists()]
    if not parts: return None, None
    d = pd.concat(parts, ignore_index=True); d["group"] = [lab(r) for r in d.rank_mean]; d = d[d.group != "1"]
    emp = {q: float(dt.empirical_gain_caps(q, pooled=True)[0]) for q in (95, 99)}
    rows, curve = [], []
    d = pd.concat([d, d.assign(group="all")], ignore_index=True)        # "all" = every target except the current leader
    for (ds, rule, g), s in d.groupby(["dataset", "rule", "group"]):
        fin = s[np.isfinite(s.hstar)]
        r = dict(dataset=ds, rule=rule, group=g, n_targets=len(s), n_censored=int((s.status == "censored").sum()), share_inf_at_100=float((s.hstar == np.inf).mean()))
        r["hstar_med"], r["hstar_lo"], r["hstar_hi"] = ci(fin.hstar.values, np.median)
        r["hstar_q90"] = float(fin.hstar.quantile(.9)) if len(fin) else np.nan
        for q, e in emp.items():
            r[f"share_hstar_gt_emp{q}"] = float((s.hstar > e).mean()); r[f"ratio_med_emp{q}"] = float((fin.hstar / e).median()) if len(fin) else np.nan
        rows.append(r)
    for (ds, rule), s in d[d.group != "all"].groupby(["dataset", "rule"]):
        for h in HGRID:
            f = s.hstar.le(h) if len(s) else s.hstar
            curve.append(dict(dataset=ds, rule=rule, h=h, n=len(s), feas=float(f.mean()), **dict(zip(("feas_lo", "feas_hi"), ci(f.astype(float).values, np.mean)[1:]))))
    return pd.DataFrame(rows), pd.DataFrame(curve).assign(emp95_pooled=emp[95], emp99_pooled=emp[99])

def table_c7_slices():
    """C7 (i, ii): rule comparison on OLLB targets with mean-rank 2-100 under caps ceil/gain10 in four settings: `main_sample` (the ordinal sample, normalised scores),
    `nomerge` (merged models removed), `raw` (un-normalised scores), `top500` (top-500 models only, all of them). Per slice, cap, rule: n targets, feasible share,
    median L1 and mean K over feasible targets. Slice samples differ in size (main_sample/nomerge/raw: the same ~54 sampled ranks 2-100; top500: all 99), so compare orderings, not levels."""
    spec = {"main_sample": None, "nomerge": "ollb_nomerge_sample.csv", "raw": "ollb_raw_sample.csv", "top500": "ollb_top500.csv"}
    rows = []
    for k, f in spec.items():
        if f is None:
            d = pd.concat([pd.read_csv(R / g) for g in ("ollb_ord_ceil.csv", "ollb_ord_gain10.csv")] + [pd.read_csv(R / "ollb_score.csv")])
            d = d[d.cap.isin(["ceil", "gain10"])]
            samp = set(d[d.rule == "borda"].target); d = d[d.target.isin(samp)]
        else: d = pd.read_csv(R / f)
        d = d[(d.rank_mean >= 2) & (d.rank_mean <= 100) & d.cap.isin(["ceil", "gain10"])]
        for (cap, rule), g in d.groupby(["cap", "rule"]):
            fin = g[g.feasible]
            rows.append(dict(slice=k, cap=cap, rule=rule, n_targets=g.target.nunique(), n_censored=int((g.status == "censored").sum()), feas=float(g.feasible.mean()),
                             L1med=float(fin.L1.median()) if len(fin) else np.nan, Kmean=float(fin.K.mean()) if len(fin) else np.nan))
    return pd.DataFrame(rows)

def table_ord100():
    """OLLB ordinal rules (Borda, Condorcet, plurality) on EVERY target of ranks 2-100 (results/ollb_ord100_<rule>.csv; caps ceil and gain10, margin 1e-3), next to the score rules
    on the same 99 targets (ollb_score.csv): feasible share, median L1, mean K per rank bin and for all 99. No sampling, so no weights; compare with the sampled main grids
    (summary/main_groups.csv, ollb_matched_sample.csv)."""
    fs = [R / f"ollb_ord100_{r}.csv" for r in ("borda", "condorcet", "plurality")]
    if not all(f.exists() for f in fs): return None
    o = pd.concat([_read(f.name) for f in fs], ignore_index=True)
    o = o[(o.rank_mean >= 2) & (o.rank_mean <= 100)]
    sc = _read("ollb_score.csv"); sc = sc[sc.cap.isin(["ceil", "gain10"]) & sc.target.isin(set(o.target))]
    d = pd.concat([o, sc], ignore_index=True); d["group"] = [lab(r) for r in d.rank_mean]
    return table_groups(pd.concat([d, d.assign(group="2-100")], ignore_index=True))

def table_hstar_ord100():
    """h* (smallest uniform gain cap that makes the target first; points) of the ordinal rules on every OLLB target of ranks 2-100 (results/ollb_hstar_ord100_<rule>.csv):
    median, quartiles, max and number of infeasible targets per rank bin and for all 99."""
    fs = [R / f"ollb_hstar_ord100_{r}.csv" for r in ("borda", "condorcet", "plurality")]
    if not all(f.exists() for f in fs): return None
    rows = []
    for f in fs:
        d = pd.read_csv(f); d = d[(d.rank_mean >= 2) & (d.rank_mean <= 100)]
        for g, (a, b) in {"2-10": (2, 10), "11-30": (11, 30), "31-100": (31, 100), "2-100": (2, 100)}.items():
            x = d[(d.rank_mean >= a) & (d.rank_mean <= b)]; h = x.hstar.replace([np.inf], np.nan)
            rows.append(dict(rule=d.rule.iloc[0], group=g, n=len(x), n_censored=int((x.status == "censored").sum()), n_inf=int(np.isinf(x.hstar).sum()),
                             median=h.median(), q25=h.quantile(.25), q75=h.quantile(.75), max=h.max()))
    return pd.DataFrame(rows)

def table_status():
    """rows per status for every per-target result file (censored = solver time limit; reported, never counted infeasible)"""
    out = []
    for f in sorted(R.glob("*.csv")):
        d = pd.read_csv(f)
        if "status" in d and f.stem != "MANIFEST": out.append(dict(file=f.name, rows=len(d), **{k: int((d.status == k).sum()) for k in ("ok", "infeasible", "censored")}))
    return pd.DataFrame(out)

if __name__ == "__main__":
    import sys; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    d = load_main(); print(d.groupby(["dataset", "cap"]).size().unstack())
    reseed(); g = table_groups(d); g.to_csv(OUT / "main_groups.csv", index=False)
    reseed(); table_matched(d).to_csv(OUT / "ollb_matched_sample.csv", index=False)
    reseed(); t = table_rank_vs_gap(d); t.to_csv(OUT / "c4_rank_vs_gap.csv", index=False)
    reseed(); m = table_min_vs_mean(d); m.to_csv(OUT / "c2_min_vs_mean.csv", index=False)
    reseed(); table_c8(d).to_csv(OUT / "c8_cap_realism.csv", index=False)
    reseed(); ts = table_tasksub()
    if ts is not None: ts.to_csv(OUT / "c3_tasksub.csv", index=False)
    def _t(f):
        reseed(); return f()
    for nm, tb in (("noise_helm", _t(lambda: table_noise("noise", "helm", "helm_main.csv"))), ("noise_ollb", _t(lambda: table_noise("noise", "ollb", "ollb_score.csv"))),
                   ("taskboot_helm", _t(lambda: table_noise("taskboot", "helm", "helm_main.csv"))),
                   ("noise_helm_t30", _t(lambda: table_noise("noise", "helm", "helm_main.csv", suffix="_t30"))), ("noise_ollb_t30", _t(lambda: table_noise("noise", "ollb", "ollb_score.csv", suffix="_t30"))), ("taskboot_helm_t30", _t(lambda: table_noise("taskboot", "helm", "helm_main.csv", suffix="_t30"))), ("flip", _t(lambda: table_flip())), ("spillover", _t(lambda: table_spill())),
                   ("eps", _t(lambda: table_eps())), ("slices", _t(lambda: table_slices())), ("trimmed", _t(lambda: table_trim()))):
        if tb is not None and len(tb): tb.to_csv(OUT / f"{nm}.csv", index=False); print(nm, len(tb))
    reseed(); table_c7_slices().to_csv(OUT / "c7_slices_compact.csv", index=False)
    reseed(); o100 = table_ord100()
    if o100 is not None: o100.to_csv(OUT / "ollb_ord100_groups.csv", index=False); print("ord100", len(o100))
    reseed(); h100 = table_hstar_ord100()
    if h100 is not None: h100.to_csv(OUT / "ollb_hstar_ord100_groups.csv", index=False)
    st = table_status(); st.to_csv(OUT / "status_counts.csv", index=False); print("censored rows:", st.set_index("file").censored[lambda x: x > 0].to_dict())
    reseed(); hs, hc = table_hstar()
    if hs is not None: hs.to_csv(OUT / "c5_c8_hstar.csv", index=False); hc.to_csv(OUT / "c5_feasible_vs_h.csv", index=False); print("hstar", len(hs))
    print(m.round(3).to_string()); print(t.round(3).to_string())
