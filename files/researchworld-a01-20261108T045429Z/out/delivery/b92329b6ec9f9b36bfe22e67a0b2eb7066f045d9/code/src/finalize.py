"""Final, figure-ready result files -> results/final/ (written from results/*.csv only; nothing is recomputed except closed forms).
Usage: python3 src/finalize.py        (bootstrap: 1000 resamples over targets, seed 0)
(investment_main, investment_variants, theory_per_target are gzip-compressed CSV: pandas.read_csv reads them directly)

Encoding (all files):  an infeasible target (no allowed raise within the cap reaches first place; proven by the solver) has L1=K=Linf=inf
  (written 'inf'; pandas reads it as float inf) and status='infeasible'.  A target that is already first under the rule
  (rank_rule==1, or L1==0 for Condorcet which has no rank) has status='already_first'; its raw L1 (0, or a tie-break margin) is kept in
  L1/K/Linf but the *_net columns are NaN, so medians of 'investment needed' use *_net.  Otherwise status='ok'.
  Condorcet rank_rule is NaN for OLLB and a Copeland-proxy rank on HELM; do not rely on it.
files
  investment_main.csv.gz   : dataset,variant=main,cap,rule,target,target_idx,rank_mean,group,rank_rule,gap,L1,K,Linf,status,already_first,L1_net,K_net,Linf_net,sampled
  investment_variants.csv.gz: same for variants top500 / nomerge / raw (OLLB) and trimmed (OLLB sample)
  group_summary.csv        : per (dataset,variant,cap,rule,group): n targets, shares already_first / infeasible, medians (CIs) of L1/K/Linf
                             over all targets (inf if >50% infeasible) and over feasible needs-investment targets only, mean K
  k_distribution.csv       : OLLB K (number of raised tasks) distribution per (variant,cap,rule,group)
  variant_vs_main.csv      : ratio of group medians variant/main (ceil, gain10), OLLB
  theory_per_target.csv.gz : solver vs closed form for mean (all caps; L1,K,Linf,feasibility), min (all caps), median (HELM, n odd, all caps)
  robust_noise_by_target.csv, robust_noise_rule.csv, robust_taskboot_*.csv (HELM, OLLB noise when present), robust_tasksub.csv
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
ROOT = pathlib.Path(__file__).resolve().parents[1]; R = ROOT / "results"; F = R / "final"; F.mkdir(exist_ok=True)
rng = np.random.default_rng(0); EPS = 1e-3; B = 1000
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
def group_of(r): return "1" if r < 2 else next(lab(lo, hi) for lo, hi in BINS if lo <= r <= hi)
GORDER = ["2", "3-5", "6-10", "11-30", "31-100", ">100"]

# ------------------------------------------------------------------ tidy investment files
def tidy(files, variant, sampled_files=()):
    out = []
    for f in files:
        d = pd.read_csv(R / f"{f}.csv"); d["sampled"] = f in sampled_files
        for c in ("gap", "K", "Linf"):
            if c not in d: d[c] = np.nan      # trimmed-mean runs report L1 and Linf only (no K)
        out.append(d)
    d = pd.concat(out, ignore_index=True); d.insert(1, "variant", variant)
    fin = np.isfinite(d.L1)
    first = fin & ((d.rank_rule == 1) | (d.L1 == 0))
    d["status"] = np.where(~fin, "infeasible", np.where(first, "already_first", "ok"))
    d["already_first"] = d.status == "already_first"
    for m in ("L1", "K", "Linf"): d[m + "_net"] = np.where(d.status == "ok", d[m], np.nan)
    d["group"] = [group_of(r) for r in d.rank_mean]
    d["rule"] = d.rule.replace({"condorcet": "condorcet_winner"})     # Condorcet-WINNER requirement: sufficient (not necessary) for first under any Condorcet-consistent rule
    d.loc[d.rule == "condorcet_winner", "rank_rule"] = np.nan        # no ranking exists for the winner requirement (earlier Copeland proxy dropped)
    n = np.where(d.dataset == "helm", 57, 6)
    for m in ("L1", "L1_net"): d[m + "_per_task"] = d[m] / n          # per-task normalisation (n=57 HELM, n=6 OLLB)
    for m in ("K", "K_net"): d[m + "_frac"] = d[m] / n
    cols = ["dataset", "variant", "cap", "rule", "target", "target_idx", "rank_mean", "group", "rank_rule", "gap", "L1", "K", "Linf",
            "status", "already_first", "L1_net", "K_net", "Linf_net", "L1_per_task", "L1_net_per_task", "K_frac", "K_net_frac", "sampled"]
    return d[cols]

main = tidy(["helm_main", "ollb_closed", "ollb_score_caps", "ollb_score_emp", "ollb_ordinal_gain"], "main", ("ollb_ordinal_gain",))
var = pd.concat([tidy(["ollb_top500"], "top500"), tidy(["ollb_nomerge_score"], "nomerge"), tidy(["ollb_raw_score"], "raw"),
                 tidy(["ollb_trimmed"], "trimmed", ("ollb_trimmed",))], ignore_index=True)
main.to_csv(F / "investment_main.csv.gz", index=False); var.to_csv(F / "investment_variants.csv.gz", index=False)

# ------------------------------------------------------------------ group summary
def med_ci(v):
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan,) * 3
    if np.isfinite(v).mean() < 0.5: return (np.inf, np.nan, np.nan)
    idx = rng.integers(0, len(v), (B, len(v))); bs = np.median(v[idx], axis=1)
    bs = bs[np.isfinite(bs)]
    return (np.median(v), *np.percentile(bs, [2.5, 97.5])) if len(bs) else (np.median(v), np.nan, np.nan)

rows = []
allr = pd.concat([main, var], ignore_index=True)
allr = allr[allr.group != "1"]
for (ds, v, cap, rule, g), s in allr.groupby(["dataset", "variant", "cap", "rule", "group"]):
    r = dict(dataset=ds, variant=v, cap=cap, rule=rule, group=g, n_targets=len(s), sampled=bool(s.sampled.iloc[0]),
             share_already_first=float(s.already_first.mean()), share_infeasible=float((s.status == "infeasible").mean()))
    for m in ("L1", "K", "Linf"):
        r[f"{m}_med"], r[f"{m}_lo"], r[f"{m}_hi"] = med_ci(s[m].values)                      # over all targets (already-first count 0)
        nn = s[m + "_net"].dropna().values
        r[f"{m}_net_med"], r[f"{m}_net_lo"], r[f"{m}_net_hi"] = med_ci(nn) if len(nn) else (np.nan,) * 3   # needs-investment only
    kn = s.K_net.dropna(); r["K_net_mean"] = float(kn.mean()) if len(kn) else np.nan
    rows.append(r)
G = pd.DataFrame(rows); G["group"] = pd.Categorical(G.group, GORDER, ordered=True)
G.sort_values(["dataset", "variant", "cap", "rule", "group"]).to_csv(F / "group_summary.csv", index=False)

# K distribution (OLLB: 6 tasks -> K in 0..6)
rows = []
for (ds, v, cap, rule, g), s in allr[allr.dataset.str.startswith("ollb")].groupby(["dataset", "variant", "cap", "rule", "group"]):
    n = len(s)
    for k in range(0, 7):
        rows.append(dict(dataset=ds, variant=v, cap=cap, rule=rule, group=g, n_targets=n, K=k, share=float((s.K == k).mean()),
                         share_excl_already_first=float((s.K_net == k).sum() / max(1, (s.status != "already_first").sum()))))
    rows.append(dict(dataset=ds, variant=v, cap=cap, rule=rule, group=g, n_targets=n, K="infeasible", share=float((s.status == "infeasible").mean()),
                     share_excl_already_first=float((s.status == "infeasible").sum() / max(1, (s.status != "already_first").sum()))))
pd.DataFrame(rows).to_csv(F / "k_distribution.csv", index=False)

# variant vs main (OLLB), medians of L1_net, same cap / rule / group
a = G[(G.dataset.str.startswith("ollb")) & G.cap.isin(["ceil", "gain10"])]
mm = a[a.variant == "main"].set_index(["cap", "rule", "group"])
rows = []
for v in ("top500", "nomerge", "raw", "trimmed"):
    w = a[a.variant == v].set_index(["cap", "rule", "group"])
    j = w.join(mm, lsuffix="_var", rsuffix="_main", how="inner")
    for (cap, rule, g), r in j.iterrows():
        rows.append(dict(variant=v, cap=cap, rule=rule, group=g, n_var=r.n_targets_var, n_main=r.n_targets_main,
                         L1_net_med_var=r.L1_net_med_var, L1_net_med_main=r.L1_net_med_main,
                         ratio=r.L1_net_med_var / r.L1_net_med_main if r.L1_net_med_main not in (0,) and np.isfinite(r.L1_net_med_main) else np.nan,
                         infeasible_var=r.share_infeasible_var, infeasible_main=r.share_infeasible_main))
pd.DataFrame(rows).to_csv(F / "variant_vs_main.csv", index=False)

# ------------------------------------------------------------------ theory per target (closed form vs solver)
rows = []
for ds, csv in (("helm", "helm_main"), ("ollb", None)):
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    d = main[main.dataset == ds]
    v_mean = X.mean(axis=1); v_min = X.min(axis=1); v_med = np.median(X, axis=1)
    tau = lambda v, i: np.delete(v, i).max()
    for cap_name in sorted(d.cap.unique()):
        dc = d[d.cap == cap_name]
        for rule in ("mean", "min", "median"):
            if rule == "median" and n % 2 == 0: continue
            s = dc[dc.rule == rule].set_index("target_idx")
            for i in s.index:
                cap = np.maximum(dt.make_cap(cap_name, X, i), X[i]); h = cap - X[i]
                row = s.loc[i]
                if rule == "mean":
                    need = n * (tau(v_mean, i) - v_mean[i] + EPS)
                    if need <= n * EPS * 0 and row.status == "already_first": pass
                    first = v_mean[i] > tau(v_mean, i)
                    if first: pred = dict(feasible=True, L1=0.0, K=0.0, Linf=0.0)
                    elif h.sum() < need - 1e-9: pred = dict(feasible=False, L1=np.inf, K=np.inf, Linf=np.inf)
                    else:
                        hs = np.sort(h)[::-1]; k = int(np.searchsorted(np.cumsum(hs), need - 1e-9) + 1)
                        # water level: smallest d with sum(min(d,h_t)) >= need
                        hs2 = np.sort(h); cs = np.concatenate([[0], np.cumsum(hs2)]); lvl = None
                        for j in range(n):
                            dlev = (need - cs[j]) / (n - j)
                            if dlev <= hs2[j] + 1e-12: lvl = dlev; break
                        pred = dict(feasible=True, L1=need, K=float(k), Linf=lvl)
                elif rule == "min":
                    b = tau(v_min, i) + EPS
                    if v_min[i] > tau(v_min, i): pred = dict(feasible=True, L1=0.0, K=0.0, Linf=0.0)
                    else:
                        raise_ = np.maximum(0, b - X[i]); ok = (raise_ <= h + 1e-9).all()
                        pred = dict(feasible=bool(ok), L1=raise_.sum() if ok else np.inf, K=float((raise_ > 0).sum()) if ok else np.inf,
                                    Linf=raise_.max() if ok else np.inf)
                else:  # median, n odd
                    b = tau(v_med, i) + EPS; kk = (n + 1) // 2
                    if v_med[i] > tau(v_med, i): pred = dict(feasible=True, L1=0.0, K=0.0, Linf=0.0)
                    else:
                        have = int((X[i] >= b).sum()); k = max(0, kk - have)
                        cand = np.sort((b - X[i])[(X[i] < b) & (cap >= b - 1e-9)])
                        if len(cand) < k: pred = dict(feasible=False, L1=np.inf, K=np.inf, Linf=np.inf)
                        else: pred = dict(feasible=True, L1=cand[:k].sum(), K=float(k), Linf=cand[k - 1] if k else 0.0)
                for m in ("L1", "K", "Linf"):
                    sv, cf = float(row[m]), float(pred[m])
                    # a tie-break margin is not modelled for targets already first by tie (rank 1): compare only the status
                    err = 0.0 if (np.isinf(sv) and np.isinf(cf)) else (np.inf if np.isinf(sv) != np.isinf(cf) else abs(sv - cf))
                    tol = 1e-5 if m != "K" else 0.5
                    rows.append(dict(dataset=ds, cap=cap_name, rule=rule, target=names[i], target_idx=int(i), rank_mean=int(row.rank_mean),
                                     measure=m, solver=sv, closed_form=cf, abs_err=err, ok=bool(err <= tol),
                                     solver_status=row.status))
T = pd.DataFrame(rows); T.to_csv(F / "theory_per_target.csv.gz", index=False)
print(T.groupby(["dataset", "rule", "measure"]).agg(n=("ok", "size"), ok=("ok", "sum"), max_err=("abs_err", lambda x: x[np.isfinite(x)].max())).to_string())
print("mismatches:", int((~T.ok).sum()))

# ------------------------------------------------------------------ robustness
def mc_tables(f, tag):
    p = R / f"{f}.csv"
    if not p.exists(): return
    d = pd.read_csv(p); d["fin"] = np.isfinite(d.L1); d["rule"] = d.rule.replace({"condorcet": "condorcet_winner"})
    base = main[(main.dataset == ("helm" if "helm" in f else "ollb"))]
    cap = "gain10" if "gain10" in f else ("ceil" if "ceil" in f else None)
    obs = base[base.cap == cap].set_index(["rule", "target"]).L1
    rows = []
    for (rule, tg), s in d.groupby(["rule", "target"]):
        fin = s.L1[s.fin]
        rows.append(dict(rule=rule, target=tg, rank_mean_obs=int(s.rank_mean_obs.iloc[0]), draws=len(s), observed_L1=obs.get((rule, tg), np.nan),
                         mc_median=fin.median() if len(fin) else np.inf, q025=fin.quantile(.025) if len(fin) else np.nan,
                         q975=fin.quantile(.975) if len(fin) else np.nan, share_infeasible=float((~s.fin).mean()),
                         share_zero=float((s.L1 == 0).mean()), cv=float(fin.std() / fin.mean()) if len(fin) > 1 and fin.mean() > 0 else np.nan))
    bt = pd.DataFrame(rows); bt.to_csv(F / f"robust_{tag}_by_target.csv", index=False)
    wide = d.pivot_table(index=["draw", "target"], columns="rule", values="L1", aggfunc="first")
    targets = wide.index.get_level_values("target").unique(); rows = []
    for rule in wide.columns:
        b_ = bt[bt.rule == rule]
        r = dict(rule=rule, n_targets=len(b_), draws=int(d.draw.nunique()), share_infeasible=float((~np.isfinite(wide[rule])).mean()),
                 cv_median=float(b_.cv.median()), cv_lo=np.nan, cv_hi=np.nan)
        cv = b_.cv.values; cv = cv[np.isfinite(cv)]
        if len(cv) > 1:
            bs = np.median(cv[rng.integers(0, len(cv), (B, len(cv)))], axis=1); r["cv_lo"], r["cv_hi"] = np.percentile(bs, [2.5, 97.5])
        if rule != "mean" and "mean" in wide:
            # share of draws cheaper than the mean on the same target and draw; CI by bootstrap over targets
            cheaper = (wide[rule] < wide["mean"]).groupby("target").mean().values
            r["share_cheaper_than_mean"] = float(cheaper.mean())
            bs = cheaper[rng.integers(0, len(cheaper), (B, len(cheaper)))].mean(axis=1); r["share_cheaper_lo"], r["share_cheaper_hi"] = np.percentile(bs, [2.5, 97.5])
        rows.append(r)
    pd.DataFrame(rows).to_csv(F / f"robust_{tag}_rule.csv", index=False)

mc_tables("helm_noise_gain10", "helm_noise_gain10"); mc_tables("helm_taskboot_gain10", "helm_taskboot_gain10")
mc_tables("ollb_noise_ceil", "ollb_noise_ceil"); mc_tables("ollb_noise_gain10", "ollb_noise_gain10")
ts = [pd.read_csv(R / "tables" / f"tasksub_{c}.csv").assign(cap=c) for c in ("ceil", "gain10")]
pd.concat(ts).to_csv(F / "robust_tasksub.csv", index=False)
print("written:", sorted(p.name for p in F.glob("*.csv")))
