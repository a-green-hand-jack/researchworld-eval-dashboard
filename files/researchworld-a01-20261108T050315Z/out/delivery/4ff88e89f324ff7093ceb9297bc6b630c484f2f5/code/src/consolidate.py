"""Consolidate raw experiment CSVs into the tidy results schema (results/tidy/) and the summary tables (results/tables/).
Usage: python3 src/consolidate.py   (reads results/*.csv; run after the experiment jobs)
Tidy schema (one row per dataset x cap x rule x target; separate optima L1_star, K_star, Linf_star, NaN when infeasible):
  dataset, scale, cap, rule, target, target_idx, rank_mean, rank_rule, stratum, cohort, in_sample, weight, eps, gap, cap_headroom,
  feasible, L1_star, K_star, Linf_star, d_star (smallest uniform lift = Linf* at ceiling), min_front_margin, min_emp95_mult,
  L1_prop (headroom-proportional allocation cost), prop_ratio, tie_flag (K* or feasibility changes when ties count as wins, eps=0),
  x_checked / x_mismatch (independent feasibility check available for the row / disagrees with the solver)
"""
import sys, glob, json, hashlib, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt

R = pathlib.Path(__file__).resolve().parents[1] / "results"; T = R / "tidy"; TB = R / "tables"
T.mkdir(exist_ok=True); TB.mkdir(exist_ok=True)
import lzma, shutil
for _f in sorted((R / "raw").glob("*.csv.xz")) if (R / "raw").exists() else []:      # delivered package: unpack the raw CSVs next to where the drivers write them
    if not (R / _f.name[:-3]).exists():
        with lzma.open(_f, "rb") as a, open(R / _f.name[:-3], "wb") as b: shutil.copyfileobj(a, b)
rng = np.random.default_rng(0)
HEADLINE = ["mean", "geomean", "median", "min", "borda", "condorcet"]
KEY = ["dataset", "cap", "rule", "target_idx"]
SCORE = ["mean", "geomean", "harmonic", "median", "min", "trimmed1", "pow0.5", "pow-0.5", "pow-2", "pow-5"]


def read(pattern):
    fs = sorted(glob.glob(str(R / pattern)))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def build(dataset, core_files, extra_files, eps_files=()):
    cf = [pd.read_csv(R / f) for f in core_files if (R / f).exists()]
    if not cf: return pd.DataFrame()
    core = pd.concat(cf, ignore_index=True)
    core = core[core.dataset == dataset].drop_duplicates(KEY, keep="last")
    if "eps" not in core: core["eps"] = 1e-3
    core["scale"] = dt.SCALE[dataset]
    exf = [pd.read_csv(R / f) for f in extra_files if (R / f).exists()]
    ex = pd.concat(exf, ignore_index=True) if exf else pd.DataFrame(columns=KEY + ["feasible", "d_star", "min_front_margin", "min_emp95_mult", "L1_prop"])
    ex = ex[ex.dataset == dataset].drop_duplicates(KEY, keep="last")
    d = core.merge(ex[KEY + ["feasible", "d_star", "min_front_margin", "min_emp95_mult", "L1_prop"]], on=KEY, how="left")
    d = d.rename(columns={"L1": "L1_star", "K": "K_star", "Linf": "Linf_star"})
    for c in ("L1_star", "K_star", "Linf_star"): d.loc[~np.isfinite(d[c]), c] = np.nan
    d["feasible_solver"] = d.L1_star.notna().astype(int)
    d["x_checked"] = d.feasible.notna().astype(int)                        # feasibility computed independently (feas.py) for this row
    d["x_mismatch"] = ((d.feasible.notna()) & (d.feasible != d.feasible_solver)).astype(int)   # solver said infeasible/finite against the independent check
    d["feasible"] = d.feasible.fillna(d.feasible_solver).astype(int)
    a_, b_ = pd.to_numeric(d.L1_prop, errors="coerce").to_numpy(float), pd.to_numeric(d.L1_star, errors="coerce").to_numpy(float)
    d["prop_ratio"] = np.divide(a_, b_, out=np.full(len(d), np.nan), where=b_ > 0)
    # cohort / strata
    X = dt.load(dataset)[0]
    ns = int(core.loc[core.get('nsample', pd.Series(0, index=core.index)) > 0, 'nsample'].max()) if 'nsample' in core and (core.nsample > 0).any() else 150
    tg, mr = dt.sample_targets(X, 0, ns)
    d["in_sample"] = d.target_idx.isin(tg).astype(int)
    d["stratum"] = [dt.rank_bin(r) for r in d.rank_mean]
    pop = pd.Series([dt.rank_bin(r) for r in mr]).value_counts(); samp = pd.Series([dt.rank_bin(mr[i]) for i in tg]).value_counts()
    nrows = d.groupby(["cap", "rule"]).target_idx.transform("size"); full = len(X)
    d["cohort"] = np.where(nrows >= 0.9 * full, "full", "sample")
    d["weight"] = np.where(d.cohort == "full", 1.0, d.stratum.map(lambda s: pop.get(s, 0) / max(samp.get(s, 1), 1)))
    # tie flag (score rules only): K* or feasibility changes when ties count as wins (eps = 0). For the ordinal rules eps = 0 is degenerate
    # (a strict pass of a rival needs eps > 0; ties get half credit), so no flag.
    d["tie_flag"] = np.nan
    ef = [pd.read_csv(R / f) for f in eps_files if (R / f).exists()]
    if ef:
        e0 = pd.concat(ef, ignore_index=True)
        e0 = e0[(e0.dataset == dataset) & (e0.eps == 0)].drop_duplicates(KEY)
        if len(e0):
            m = d.merge(e0[KEY + ["K"]].rename(columns={"K": "K0"}), on=KEY, how="left")
            has = m.K0.notna() | (m.K0.isna() & m.rule.isin(SCORE) & m.target_idx.isin(e0.target_idx))
            chg = (m.K0.fillna(-1) != m.K_star.fillna(-1)).astype(float)
            d["tie_flag"] = np.where(has & m.rule.isin(SCORE) & m.K0.notna(), chg, np.nan)
    cols = ["dataset", "scale", "cap", "rule", "target", "target_idx", "rank_mean", "rank_rule", "stratum", "cohort", "in_sample", "weight",
            "eps", "gap", "cap_headroom", "milp_status", "sec", "feasible", "L1_star", "K_star", "Linf_star", "d_star", "min_front_margin", "min_emp95_mult",
            "L1_prop", "prop_ratio", "tie_flag", "x_checked", "x_mismatch"]
    out = d[[c for c in cols if c in d]].copy()
    out.attrs.update(expected_full=len(X) - 1, expected_sample=len(tg))
    return out


def wmedian(v, w):
    o = np.argsort(v); v, w = np.asarray(v)[o], np.asarray(w)[o]; c = np.cumsum(w); return float(v[np.searchsorted(c, c[-1] / 2)])


def boot(v, w=None, B=1000):
    """bootstrap CI of the (weighted) median over targets; resamples targets within the given rows (sampling unit = targets)"""
    v = np.asarray(v, float); n = len(v)
    if n == 0: return np.nan, np.nan, np.nan
    w = np.ones(n) if w is None else np.asarray(w, float)
    med = wmedian(v, w)
    bs = []
    for _ in range(B):
        k = rng.integers(0, n, n); bs.append(wmedian(v[k], w[k]))
    return med, *np.percentile(bs, [2.5, 97.5])


def tables(d, tag):
    d = d[d.rank_mean >= 2]
    rows = []
    for (cap, rule, stratum), s in d.groupby(["cap", "rule", "stratum"]):
        f = s[s.feasible == 1]; r = dict(dataset=s.dataset.iloc[0], scale=s.scale.iloc[0], cap=cap, rule=rule, stratum=stratum,
                                         cohort=s.cohort.iloc[0], n_targets=len(s), n_feasible=len(f), frac_feasible=len(f) / len(s),
                                         ci_unit="targets within stratum (spread across models, not measurement uncertainty)")
        for m in ("L1_star", "K_star", "Linf_star"):
            med, lo, hi = boot(f[m].values); r[m + "_med"], r[m + "_lo"], r[m + "_hi"] = med, lo, hi
        r["d_star_med"] = float(np.nanmedian(s.d_star)) if s.d_star.notna().any() else np.nan
        r["prop_ratio_med"] = float(np.nanmedian(f.prop_ratio)) if len(f) and f.prop_ratio.notna().any() else np.nan
        rows.append(r)
    pd.DataFrame(rows).to_csv(TB / f"cost_by_stratum_{tag}.csv", index=False)
    # pooled over rank >= 2: weighted median over feasible targets (stratum weights if sampled), feasibility fraction weighted
    rows = []
    for (cap, rule), s in d.groupby(["cap", "rule"]):
        f = s[s.feasible == 1]; med = boot(f.L1_star.values, f.weight.values) if len(f) else (np.nan,) * 3
        medK = boot(f.K_star.values, f.weight.values) if len(f) else (np.nan,) * 3
        rows.append(dict(dataset=s.dataset.iloc[0], scale=s.scale.iloc[0], cap=cap, rule=rule, cohort=s.cohort.iloc[0], n_targets=len(s),
                         n_feasible=len(f), frac_feasible_w=float(np.average(s.feasible, weights=s.weight)),
                         L1_med_w=med[0], L1_lo=med[1], L1_hi=med[2], K_med_w=medK[0], K_lo=medK[1], K_hi=medK[2]))
    pd.DataFrame(rows).to_csv(TB / f"cost_pooled_{tag}.csv", index=False)
    # relative cost vs mean on the common feasible cohort of the compared rules, denominator reported
    rows = []
    for cap, s in d.groupby("cap"):
        rules = [r for r in s.rule.unique() if r != "mean"]
        for r in rules:
            for coh_rules in ([r], ):                                 # pairwise vs mean: cohort = targets feasible under both
                a_ = s[s.rule == "mean"].set_index("target_idx"); b_ = s[s.rule == r].set_index("target_idx")
                idx = a_.index.intersection(b_.index)
                a_, b_ = a_.loc[idx], b_.loc[idx]; ok = (a_.feasible == 1) & (b_.feasible == 1) & (a_.L1_star > 0)
                if ok.sum() == 0: rows.append(dict(dataset=s.dataset.iloc[0], scale=s.scale.iloc[0], cap=cap, rule=r, n_common=0, n_targets=len(idx))); continue
                rel = (b_.L1_star[ok] / a_.L1_star[ok]).values; w = b_.weight[ok].values
                med = boot(rel, w)
                rows.append(dict(dataset=s.dataset.iloc[0], scale=s.scale.iloc[0], cap=cap, rule=r, n_targets=len(idx), n_common=int(ok.sum()),
                                 frac_common=float(ok.sum() / len(idx)), rel_L1_vs_mean_med_w=med[0], lo=med[1], hi=med[2],
                                 note="common cohort = targets feasible under both rules, mean L1 > 0; weighted by stratum weights"))
    pd.DataFrame(rows).to_csv(TB / f"rel_L1_vs_mean_{tag}.csv", index=False)
    # minimal feasible cap per rule: smallest uniform lift d*, smallest best-rival margin m (cap = best rival + m), smallest empirical-gain
    # multiplier (cap = m x the 95th-percentile gain); weighted quantiles over targets of rank >= 2 (stratum weights where sampled)
    rows = []
    for rule, s in d.groupby("rule"):
        w = np.where(s.cohort == "full", 1.0, s.weight)
        for col in ("d_star", "min_front_margin", "min_emp95_mult"):
            v = s[col].to_numpy(float); ok = np.isfinite(v)
            if ok.sum() == 0: continue
            o = np.argsort(v[ok]); vv, ww = v[ok][o], w[ok][o]; c = np.cumsum(ww) / ww.sum()
            q = lambda p: float(vv[min(np.searchsorted(c, p), len(vv) - 1)])
            rows.append(dict(dataset=s.dataset.iloc[0], scale=s.scale.iloc[0], rule=rule, quantity=col, n_targets=len(s), n_finite=int(ok.sum()),
                             frac_finite_w=float(ww.sum() / w.sum()), q25=q(.25), median=q(.5), q75=q(.75), max=float(vv[-1])))
    pd.DataFrame(rows).to_csv(TB / f"min_feasible_cap_{tag}.csv", index=False)
    # common feasible cohort across the headline rule set, per cap: the same targets for every rule (denominators n_common / n_targets)
    rows = []; hr = [r for r in HEADLINE if r in set(d.rule)]
    for cap, s in d.groupby("cap"):
        s = s[s.rule.isin(hr)]
        if len(hr) < 2 or s.rule.nunique() < len(hr): continue
        ok = s.assign(f=(s.feasible == 1)).groupby("target_idx").f.agg(["all", "size"])
        common = ok.index[(ok["all"]) & (ok["size"] == len(hr))]; allt = ok.index[ok["size"] == len(hr)]
        s = s[s.target_idx.isin(common)]
        wt = s[s.cohort == "sample"].groupby("stratum").weight.first() if (s.cohort == "sample").any() else pd.Series(dtype=float)
        for rule, g in s.groupby("rule"):
            w = g.stratum.map(wt).fillna(1.0).to_numpy() if len(wt) else np.ones(len(g))
            mL = boot(g.L1_star.values, w); mK = boot(g.K_star.values, w)
            rows.append(dict(dataset=g.dataset.iloc[0], scale=g.scale.iloc[0], cap=cap, rule=rule, rule_set="+".join(hr), n_common=len(common), n_targets=len(allt),
                             frac_common=len(common) / max(len(allt), 1), L1_med_w=mL[0], L1_lo=mL[1], L1_hi=mL[2], K_med_w=mK[0], K_lo=mK[1], K_hi=mK[2],
                             note="targets of rank >= 2 feasible under every rule of the set, in the stratified sample when ordinal rules are included; stratum weights"))
    pd.DataFrame(rows).to_csv(TB / f"common_cohort_{tag}.csv", index=False)


def eps_table():
    """effect of the strictness margin eps on L1*, K*, feasibility, relative to eps = 1e-3 on the common targets"""
    rows = []
    for tag, files in (("helm", ["eps_helm_*.csv"]), ("ollb", ["eps_ollb_score_*.csv", "eps_ollb_ord_*.csv"])):
        e = pd.concat([read(f) for f in files], ignore_index=True)
        if e.empty or not (T / f"{tag}.csv.gz").exists(): continue
        base = pd.read_csv(T / f"{tag}.csv.gz"); base = base[base.rank_mean >= 2]
        e = e[e.rank_mean >= 2]
        for (rule, cap, eps), s in e.groupby(["rule", "cap", "eps"]):
            if eps == 0 and rule not in SCORE: continue          # eps = 0 is degenerate for the ordinal solvers
            b = base[(base.rule == rule) & (base.cap == cap)].set_index("target_idx"); s = s.drop_duplicates("target_idx").set_index("target_idx")
            idx = s.index.intersection(b.index)
            if len(idx) == 0: continue
            L1e = s.loc[idx, "L1"].replace(np.inf, np.nan); L1b = b.loc[idx, "L1_star"]; Ke = s.loc[idx, "K"].replace(np.inf, np.nan); Kb = b.loc[idx, "K_star"]
            both = L1e.notna() & L1b.notna() & (L1b > 0)
            rows.append(dict(dataset=tag, rule=rule, cap=cap, eps=eps, n_targets=len(idx), frac_feasible_eps=float(L1e.notna().mean()),
                             frac_feasible_base=float(L1b.notna().mean()), n_both=int(both.sum()),
                             L1_ratio_med=float(np.median(L1e[both] / L1b[both])) if both.any() else np.nan,
                             K_changed_frac=float((Ke[both] != Kb[both]).mean()) if both.any() else np.nan,
                             L1_med_eps=float(L1e.median()), L1_med_base=float(L1b.median())))
    pd.DataFrame(rows).to_csv(TB / "eps_sensitivity.csv", index=False)


ROBUST = {   # raw file -> (dataset, cap, kind)
    "helm_tasksub_gain10.csv": ("helm", "gain10", "tasksub"), "helm_tasksub_ceil.csv": ("helm", "ceil", "tasksub"),
    "helm_noise_gain10.csv": ("helm", "gain10", "noise"), "ollb_noise_gain10.csv": ("ollb", "gain10", "noise"),
    "ollb_taskboot_gain10.csv": ("ollb", "gain10", "taskboot"), "helm_taskboot_gain10.csv": ("helm", "gain10", "taskboot"),
}


def robust_tables():
    """tidy robustness files, one row per draw: dataset, kind, cap, rule, draw, [n], target, stratum, feasible, L1_star, K_star
    (Linf* is not computed in the robustness runs)"""
    allr = []
    for f, (ds, cap, kind) in ROBUST.items():
        if not (R / f).exists(): continue
        r = pd.read_csv(R / f); r["dataset"] = ds; r["cap"] = cap; r["kind"] = kind; r["scale"] = dt.SCALE[ds]
        r = r.rename(columns={"L1": "L1_star", "K": "K_star"})
        for c in ("L1_star", "K_star"): r.loc[~np.isfinite(r[c]), c] = np.nan
        r["feasible"] = r.L1_star.notna().astype(int); r["Linf_star"] = np.nan
        if "rank_mean_obs" in r: r["stratum"] = [dt.rank_bin(x) for x in r.rank_mean_obs]
        r["first_already"] = (r.L1_star == 0).astype(int)
        allr.append(r)
        r.to_csv(T / f"robust_{kind}_{ds}_{cap}.csv.gz", index=False)
    return allr


SETS = {
    "helm": dict(dataset="helm", core=["helm_main.csv", "helm_pow.csv", "helm_empm.csv"], extra=["extra_helm.csv"],
                 eps=["eps_helm_0.csv", "eps_helm_0.01.csv", "eps_helm_0.1.csv"]),
    "ollb": dict(dataset="ollb", core=["ollb_closed.csv", "ollb_closed_emp.csv", "ollb_ord_a.csv", "ollb_ord_front2_borda.csv", "ollb_ord_front2_condorcet.csv", "ollb_ord_front2_plurality_trimmed1.csv", "ollb_ord_b.csv", "ollb_ord_c.csv", "ollb_ord_resolve_front0_borda.csv"],   # last: re-solve of the one cell whose L1 solve returned no incumbent in the 120 s run
                
                 extra=["extra_ollb_score.csv", "extra_ollb_ord.csv"], eps=["eps_ollb_score_0.csv"]),
    "ollb_z": dict(dataset="ollb_z", core=["ollbz_closed.csv", "ollbz_ord.csv"], extra=["extra_ollbz_score.csv", "extra_ollbz_ord.csv"], eps=[]),
    "ollb_pct": dict(dataset="ollb_pct", core=["ollbpct_closed.csv"], extra=["extra_ollbpct_score.csv", "extra_ollbpct_ord.csv"], eps=[]),
    "ollb_nomerge": dict(dataset="ollb_nomerge", core=["slice_ollb_nomerge_closed.csv", "slice_ollb_nomerge_ord.csv"], extra=[], eps=[]),
    "ollb_top500": dict(dataset="ollb_top500", core=["slice_ollb_top500_closed.csv", "slice_ollb_top500_ord.csv"], extra=[], eps=[]),
    "ollb_raw": dict(dataset="ollb_raw", core=["slice_ollb_raw_closed.csv", "slice_ollb_raw_ord.csv"], extra=[], eps=[]),
}
if __name__ == "__main__":
    which = sys.argv[1:] or list(SETS); comp = []
    for tag in which:
        s = SETS[tag]; d = build(s["dataset"], s["core"], s["extra"], s["eps"])
        if d.empty: print(tag, "no data"); continue
        d.to_csv(T / f"{tag}.csv.gz", index=False); tables(d, tag)
        c = d.groupby(["dataset", "cap", "rule", "cohort"]).agg(n_rows=("target_idx", "nunique"), n_xchecked=("x_checked", "sum"), n_xmismatch=("x_mismatch", "sum"), n_timelimit=("milp_status", lambda v: int((v == "time_limit").sum())) if "milp_status" in d else ("target_idx", lambda v: 0)).reset_index()
        c["n_expected"] = np.where(c.cohort == "full", d.attrs["expected_full"], d.attrs["expected_sample"])
        c["complete"] = (c.n_rows >= c.n_expected).astype(int); comp.append(c)
        print(tag, len(d), "rows;", d.groupby("rule").size().to_dict(), flush=True)
    if comp: pd.concat(comp).to_csv(TB / "completeness.csv", index=False)   # rows per (dataset, cap, rule) against the expected cohort size
    eps_table(); robust_tables()
    man = {str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(R.rglob("*")) if p.is_file() and p.name != "MANIFEST.sha256.json"}
    json.dump(man, open(R / "MANIFEST.sha256.json", "w"), indent=1)
