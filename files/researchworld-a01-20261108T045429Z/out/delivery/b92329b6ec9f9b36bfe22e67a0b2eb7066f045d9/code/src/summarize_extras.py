"""Summaries of the controls and the leaf-task board -> results/final/{random_control_summary,leaf_vs_six_groups,leaf_top500_groups,leaf_tasksub}.csv
(bootstrap CIs: 1000 resamples, seed 0).  Inputs: results/random_control_*.csv, results/leaf_*.csv, results/leaf6_score.csv.
Units: per-task L1 = L1/n (n = 39 leaf tasks or 6 benchmark aggregates), K/n = share of tasks raised.  Rank groups: rank of the model under the mean on the board concerned
(for leaf_top500: within the 500-model slice).  'inf' = no feasible allocation under the cap (median over targets is inf when >= 50% are infeasible; 'infeasible' gives the share).
"""
import pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1] / "results"; F = R / "final"; F.mkdir(exist_ok=True)
rng = np.random.default_rng(0); B = 1000
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
def med_ci(v):
    v = np.asarray(v, float)
    if len(v) == 0: return (np.nan,) * 3
    if np.isfinite(v).mean() < 0.5: return (np.inf, np.nan, np.nan)
    bs = np.median(v[rng.integers(0, len(v), (B, len(v)))], axis=1); bs = bs[np.isfinite(bs)]
    return (np.median(v), *np.percentile(bs, [2.5, 97.5])) if len(bs) else (np.median(v), np.nan, np.nan)

# ---- random-allocation control (HELM, ranks 2..20)
d = pd.concat([pd.read_csv(p) for p in sorted(R.glob("random_control_*.csv"))])
q = lambda v, p: float(np.sort(v)[int(round(p * (len(v) - 1)))])
rows = []
for (cap, rule, scheme), s in d.groupby(["cap", "rule", "scheme"], sort=False):
    f = s.factor_med.values
    rows.append(dict(cap=cap, rule=rule, scheme=scheme, n_targets=len(s), draws=int(s.draws.iloc[0]),
                     factor_median_over_targets=q(f, .5), factor_q25=q(f, .25), factor_q75=q(f, .75),
                     share_targets_inf=float((~np.isfinite(f)).mean()), success_at_opt_median=float(s.success_at_opt.median()),
                     success_at_opt_mean=float(s.success_at_opt.mean()), share_draws_inf_mean=float(s.share_inf.mean())))
pd.DataFrame(rows).to_csv(F / "random_control_summary.csv", index=False)

# ---- leaf board vs the same models aggregated to 6 benchmarks, and the top-500 slice
def groups(df, board, n_tasks):
    out = []
    df = df[df.rank_mean >= 2]
    for (cap, rule), s in df.groupby(["cap", "rule"], sort=False):
        for lo, hi in BINS:
            g = s[(s.rank_mean >= lo) & (s.rank_mean <= hi)]
            if g.empty: continue
            l1 = med_ci(g.L1.values / n_tasks); k = med_ci(g.K.values / n_tasks); kc = med_ci(g.K.values)
            out.append(dict(board=board, n_tasks=n_tasks, cap=cap, rule=rule, group=lab(lo, hi), n_targets=len(g),
                            L1_per_task_median=l1[0], L1_per_task_lo=l1[1], L1_per_task_hi=l1[2],
                            K_median=kc[0], K_share_median=k[0], K_share_lo=k[1], K_share_hi=k[2],
                            infeasible=float((~np.isfinite(g.L1)).mean())))
    return out
parts = []
leaf = [R / "leaf_closed.csv", R / "leaf_score_caps.csv"]
parts += groups(pd.concat([pd.read_csv(p) for p in leaf if p.exists()]), "leaf39", 39)
if (R / "leaf6_score.csv").exists(): parts += groups(pd.read_csv(R / "leaf6_score.csv"), "leaf6_same_models", 6)
pd.DataFrame(parts).to_csv(F / "leaf_vs_six_groups.csv", index=False)
if (R / "leaf_top500.csv").exists():
    pd.DataFrame(groups(pd.read_csv(R / "leaf_top500.csv"), "leaf39_top500", 39)).to_csv(F / "leaf_top500_groups.csv", index=False)

# ---- task-subset scaling on the leaf board (random subsets of n leaves)
rows = []
for tag, board, f in (("ceil", "leaf39", "leaf_tasksub_ceil"), ("gain10", "leaf39", "leaf_tasksub_gain10"), ("ceil", "leaf39_top500", "leaf_top500_tasksub_ceil")):
    p = R / f"{f}.csv"
    if not p.exists(): continue
    t = pd.read_csv(p)
    for (rule, n, rk), s in t.groupby(["rule", "n", "target_rank"]):
        l1 = med_ci(s.L1.values / n); kk = med_ci(s.K.values / n); kc = med_ci(s.K.values)
        rows.append(dict(board=board, cap=tag, rule=rule, n=n, target_rank=rk, draws=len(s), L1_per_task_median=l1[0], L1_per_task_lo=l1[1], L1_per_task_hi=l1[2],
                         L1_median=float(np.median(s.L1.values)), K_median=kc[0], K_share_median=kk[0], K_share_lo=kk[1], K_share_hi=kk[2],
                         infeasible=float((~np.isfinite(s.L1)).mean())))
pd.DataFrame(rows).to_csv(F / "leaf_tasksub.csv", index=False)
print("written", sorted(p.name for p in F.glob("*") if p.name.startswith(("random_control", "leaf"))))
