"""Aggregate the raw experiment CSVs in results/ into the tables handed to figtab/paper (results/tables/*.csv).
Usage: python3 src/analyze.py            (skips inputs that do not exist)  Seeds fixed (0). Bootstrap = resampling targets, B=1000.
Tables
  main_by_rank.csv     dataset,cap,rule,group_by,group: n_targets, n_feasible, infeasible share, share with K<=1; median K / L1 / Linf (...) with 95% bootstrap CI
                       `X_med/X_lo/X_hi`: over ALL targets, infeasible entered as +inf (inf if more than half infeasible); `X_med_feas/X_lo_feas/X_hi_feas`: over the feasible targets only (use these as costs)
  rank_scaling.csv     slope of log L1 on log(rank) over feasible targets (rank = rank under the rule itself), bootstrap CI, Spearman rho
  vs_mean.csv          paired ratio L1_rule / L1_mean per target (median, CI) by rank group
  noise_summary.csv    evaluation-noise Monte-Carlo: per target and rule, median / 5-95% of L1 over draws; share of draws infeasible; rank flips
  tasksub_summary.csv  task-subset-size scaling: median K, L1 (and K/n) by n, rule, target rank
  taskboot_summary.csv task bootstrap: same as noise
"""
import pathlib, numpy as np, pandas as pd
from scipy.stats import spearmanr
R = pathlib.Path(__file__).resolve().parents[1] / "results"; T = R / "tables"; T.mkdir(exist_ok=True)
rng = np.random.default_rng(0); B = 1000
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
def grp(r):
    if not np.isfinite(r): return "NA"
    for lo, hi in BINS:
        if lo <= r <= hi: return f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
    return "1"
ORDER = ["2", "3-5", "6-10", "11-30", "31-100", ">100"]

def bmed(v, B=B):
    v = np.asarray(v, float); v = v[~np.isnan(v)]            # NaN = solver failure (time limit), excluded and reported in `failed`
    if len(v) == 0: return (np.nan,) * 3
    if np.isfinite(v).mean() <= 0.5: return (np.inf, np.nan, np.nan)    # median infeasible
    m = np.median(v); idx = rng.integers(0, len(v), (B, len(v)))
    bs = np.median(v[idx], axis=1); return m, *np.percentile(bs, [2.5, 97.5])

def load_core():
    fs = {"ollb": ["ollb_score", "ollb_wmean", "ollb_ord_ceil", "ollb_ord_front0", "ollb_ord_gain10", "ollb_ord_emp95"],
          "ollb_top500": ["ollb_top500_a", "ollb_top500_b", "ollb_top500_c", "ollb_top500_cope_ceil"], "ollb_nomerge": ["ollb_nomerge_score", "ollb_nomerge_ord"],
          "ollb_raw": ["ollb_raw_score", "ollb_raw_score_front0", "ollb_raw_score_gain10", "ollb_raw_score_gain20", "ollb_raw_ord"], "helm": ["helm_main", "helm_pow"]}
    out = []
    for ds, names in fs.items():
        for n in names:
            p = R / f"{n}.csv"
            if not p.exists(): p = R / f"{n}.csv.gz"   # the large OLLB grids are committed gzipped
            if p.exists(): out.append(pd.read_csv(p).assign(source=n))
    d = pd.concat(out, ignore_index=True).drop_duplicates(subset=["dataset", "cap", "rule", "target"])   # overlapping partial runs: first file wins
    d = d[d.rank_mean > 1].copy()                      # targets that are not already first under the mean
    return d

d = load_core()
# L1 relative to the median across-model task SD of the dataset (cross-dataset comparability, plan decision #1)
import sys; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
SD = {ds: float(np.median(dt.load(ds)[0].std(axis=0, ddof=1))) for ds in d.dataset.unique()}
d["L1_over_sd"] = d.L1 / d.dataset.map(SD)
pd.Series(SD, name="median_task_sd").to_csv(T / "task_sd.csv")
rows = []
for (ds, cap, rule), s in d.groupby(["dataset", "cap", "rule"]):
    for gb in ("rank_mean", "rank_rule"):
        g = s[gb].map(grp)
        for gname in ORDER + ["all"]:
            t = s if gname == "all" else s[g == gname]
            if gb == "rank_rule": t = t[t[gb] > 1] if gname == "all" else t
            if len(t) == 0: continue
            r = dict(dataset=ds, cap=cap, rule=rule, group_by=gb, group=gname, n_targets=len(t))
            for m in ("K", "L1", "Linf", "L1_over_sd", "K_at_L1", "L1_lexK"):
                if m not in t or t[m].isna().all(): continue
                med, lo, hi = bmed(t[m].values); r.update({f"{m}_med": med, f"{m}_lo": lo, f"{m}_hi": hi})   # over all targets, infeasible entered as +inf
                v = t[m].values.astype(float); v = v[np.isfinite(v)]                                          # feasible-only median and CI over feasible targets
                fm, flo, fhi = bmed(v) if len(v) else (np.nan,) * 3; r.update({f"{m}_med_feas": fm, f"{m}_lo_feas": flo, f"{m}_hi_feas": fhi})
                if m == "K": r["K_q25"], r["K_q75"] = np.nanpercentile(t.K.values[np.isfinite(t.K.values)], [25, 75]) if np.isfinite(t.K.values).any() else (np.nan, np.nan)
                if m == "L1": r["L1_q25"], r["L1_q75"] = np.nanpercentile(t.L1.values[np.isfinite(t.L1.values)], [25, 75]) if np.isfinite(t.L1.values).any() else (np.nan, np.nan)
            r["note"] = "upper bound for any Condorcet-consistent rule (sufficient, not necessary)" if rule == "condorcet" else ""
            ok = t.L1.notna().values; r["failed"] = float(np.mean(~ok)); r["infeasible"] = float(np.mean(np.isinf(t.L1.values[ok]))) if ok.any() else np.nan
            r["n_feasible"] = int(np.isfinite(t.L1.values).sum())
            r["K_le1"] = float(np.mean(t.K.values[ok] <= 1)) if ok.any() else np.nan
            rows.append(r)
pd.DataFrame(rows).to_csv(T / "main_by_rank.csv", index=False)

rows = []
for (ds, cap, rule), s in d.groupby(["dataset", "cap", "rule"]):
    s = s[(s.rank_rule > 1) & np.isfinite(s.L1) & (s.L1 > 0)]   # NaN/inf dropped
    if len(s) < 20: continue
    lr, ll = np.log(s.rank_rule.values), np.log(s.L1.values)
    sl = np.polyfit(lr, ll, 1)[0]
    idx = rng.integers(0, len(s), (B, len(s))); bs = [np.polyfit(lr[i], ll[i], 1)[0] for i in idx]
    rho = spearmanr(s.rank_rule, s.L1)[0]
    rows.append(dict(dataset=ds, cap=cap, rule=rule, n=len(s), slope_logL1_logrank=sl, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), spearman=rho))
pd.DataFrame(rows).to_csv(T / "rank_scaling.csv", index=False)

rows = []
for (ds, cap), s in d.groupby(["dataset", "cap"]):
    w = s.pivot_table(index=["target", "rank_mean"], columns="rule", values="L1", aggfunc="first")
    if "mean" not in w: continue
    rkall = w.index.get_level_values("rank_mean").map(grp)
    for rule in w.columns:
        if rule == "mean": continue
        # paired ratio only where BOTH rules are feasible (finite L1, mean L1 > 0); x/inf must not enter as 0
        both = np.isfinite(w[rule]) & np.isfinite(w["mean"]) & (w["mean"] > 0)
        ratio = (w[rule] / w["mean"])[both]; rk = rkall[both.values]
        only_rule = np.isfinite(w[rule]) & ~np.isfinite(w["mean"]) & w["mean"].notna() & w[rule].notna()
        only_mean = np.isfinite(w["mean"]) & ~np.isfinite(w[rule]) & w[rule].notna() & w["mean"].notna()
        for gname in ORDER + ["all"]:
            sel = np.ones(len(w), bool) if gname == "all" else (rkall == gname)
            v = ratio.values if gname == "all" else ratio[rk == gname].values
            nr, nm = int((only_rule.values & sel).sum()), int((only_mean.values & sel).sum())
            if len(v) < 5 and nr + nm == 0: continue
            med, lo, hi = bmed(v) if len(v) else (np.nan,) * 3
            rows.append(dict(dataset=ds, cap=cap, rule=rule, group=gname, n=len(v), n_both_feasible=len(v), n_only_rule_feasible=nr, n_only_mean_feasible=nm,
                             ratio_med=med, lo=lo, hi=hi, share_cheaper_than_mean=float(np.mean(v < 1)) if len(v) else np.nan))
pd.DataFrame(rows).to_csv(T / "vs_mean.csv", index=False)

def draws_summary(path, out):
    if not path.exists(): return
    n = pd.read_csv(path); rows = []
    for (rule, tg), s in n.groupby(["rule", "target"]):
        L = s.L1.values; K = s.K.values
        rows.append(dict(rule=rule, target=tg, rank_mean_obs=s.rank_mean_obs.iloc[0], draws=len(s), infeasible=float(np.mean(np.isinf(L[~np.isnan(L)]))),
                         L1_med=np.median(L), L1_q05=np.nanpercentile(np.where(np.isfinite(L), L, np.nan), 5) if np.isfinite(L).any() else np.nan,
                         L1_q95=np.nanpercentile(np.where(np.isfinite(L), L, np.nan), 95) if np.isfinite(L).any() else np.nan,
                         K_med=np.median(K), n_feasible=int(np.isfinite(L).sum()), L1_med_feas=np.median(L[np.isfinite(L)]) if np.isfinite(L).any() else np.nan,
                         K_med_feas=np.median(K[np.isfinite(K)]) if np.isfinite(K).any() else np.nan, already_first=float(np.mean(L == 0)), rank_rule_med=np.median(s.rank_rule)))
    pd.DataFrame(rows).to_csv(T / out, index=False)
draws_summary(R / "helm_noise_gain10.csv", "noise_summary_helm.csv")
draws_summary(R / "ollb_noise_gain10.csv", "noise_summary_ollb_top500.csv")
draws_summary(R / "helm_taskboot_gain10.csv", "taskboot_summary_helm.csv")

rows = []
for cap in ("gain10", "ceil"):
    p = R / f"helm_tasksub_{cap}.csv"
    if not p.exists(): continue
    s = pd.read_csv(p)
    for (n, rule, rk), t in s.groupby(["n", "rule", "target_rank"]):
        L, K = t.L1.values, t.K.values
        r = dict(cap=cap, n=n, rule=rule, target_rank=rk, draws=len(t), infeasible=float(np.mean(np.isinf(L[~np.isnan(L)]))), gap_med=float(np.median(t.gap_own)))
        for nm, v in (("L1", L), ("K", K)): med, lo, hi = bmed(v); r.update({f"{nm}_med": med, f"{nm}_lo": lo, f"{nm}_hi": hi})
        fin = np.isfinite(L) & np.isfinite(K); r["n_feasible"] = int(fin.sum())      # feasible-only medians (infeasible draws excluded)
        for nm, v in (("L1", L), ("K", K)): med, lo, hi = bmed(v[fin]) if fin.any() else (np.nan,) * 3; r.update({f"{nm}_med_feas": med, f"{nm}_lo_feas": lo, f"{nm}_hi_feas": hi})
        r["K_over_n"] = r["K_med"] / n; r["K_over_n_feas"] = r["K_med_feas"] / n
        # closed-form upper bounds on K for a feasible plan: median needs a strict majority of tasks above the rival median (floor(n/2)+1);
        # min needs every task above the rival min (n); mean/geomean can need as few as one task.
        r["K_bound"] = n // 2 + 1 if rule == "median" else (n if rule == "min" else np.nan)
        rows.append(r)
if rows: pd.DataFrame(rows).to_csv(T / "tasksub_summary.csv", index=False)
print("wrote", sorted(p.name for p in T.glob("*.csv")))


# ---- C1: stability of the order of rules (Kendall tau between settings, on the feasible-only median cost over targets with rank_mean > 1)
from scipy.stats import kendalltau
M = pd.read_csv(T / "main_by_rank.csv"); M = M[(M.group == "all") & (M.group_by == "rank_mean")]
rows = []
for meas in ("L1", "K"):
    P = M.pivot_table(index="rule", columns=["dataset", "cap"], values=f"{meas}_med_feas", aggfunc="first")
    cols = list(P.columns)
    for a_ in range(len(cols)):
        for b_ in range(a_ + 1, len(cols)):
            both = P[[cols[a_], cols[b_]]].replace([np.inf], np.nan).dropna()
            if len(both) < 4: continue
            tau, pv = kendalltau(both.iloc[:, 0], both.iloc[:, 1]); rows.append(dict(measure=meas, setting_a=f"{cols[a_][0]}|{cols[a_][1]}", setting_b=f"{cols[b_][0]}|{cols[b_][1]}", n_rules=len(both), kendall_tau=tau, p=pv))
pd.DataFrame(rows).to_csv(T / "rule_order_stability.csv", index=False)

# ---- C5: cost vs the score gap to the leader (score rules; spearman) and cost vs rank
rows = []
for (ds, cap, rule), s_ in d.groupby(["dataset", "cap", "rule"]):
    s_ = s_[np.isfinite(s_.L1) & s_.gap.notna() & (s_.gap > 0)]
    if len(s_) >= 20: rows.append(dict(dataset=ds, cap=cap, rule=rule, n=len(s_), spearman_L1_gap=spearmanr(s_.L1, s_.gap)[0]))
pd.DataFrame(rows).to_csv(T / "cost_vs_gap.csv", index=False)

# ---- C6: raw vs normalised OLLB, matched targets
rows = []
a_, b_ = d[d.dataset == "ollb"], d[d.dataset == "ollb_raw"]
if len(b_):
    m = a_.merge(b_, on=["target", "cap", "rule"], suffixes=("_norm", "_raw"))
    for (cap, rule), s_ in m.groupby(["cap", "rule"]):
        ok = np.isfinite(s_.L1_norm) & np.isfinite(s_.L1_raw) & (s_.L1_norm > 0)
        if ok.sum() < 5: continue
        ratio = (s_.L1_raw[ok] / s_.L1_norm[ok]).values; med, lo, hi = bmed(ratio)
        rows.append(dict(cap=cap, rule=rule, n_matched=int(ok.sum()), L1_ratio_raw_over_norm_med=med, lo=lo, hi=hi,
                         K_equal_share=float(np.mean(s_.K_norm[ok] == s_.K_raw[ok])), rank_rule_equal_share=float(np.mean(s_.rank_rule_norm[ok] == s_.rank_rule_raw[ok]))))
pd.DataFrame(rows).to_csv(T / "raw_vs_norm.csv", index=False)
print("wrote", sorted(p.name for p in T.glob("*.csv")))
